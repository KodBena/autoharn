#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T07:45:52Z
#   last-change: 2026-07-18T07:45:52Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""audit_served -- the served-vs-kernel spot differential (design/
FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md §5: "the service's audit is a scripted spot
differential ... fetch a served page, read the same view directly (read-only psql), byte-
compare the row sets, exit nonzero on any difference. Sentry-class treatment per row 1471:
this audit verb ships WITH the service, not after it.").

WHAT THIS PROVES, AND WHAT IT DOES NOT (named per ADR-0000 §9's closure-statement discipline,
carried into every witness-bearing script in this project): it proves that what
`serving/boundary_service.py` handed an HTTP client for one page of one view, at one instant,
is BYTE-IDENTICAL (after JSON canonicalization -- key order is not semantic) to what a direct
read-only psql SELECT against the SAME view returns. It does NOT prove the service correct
against every endpoint, every page, or every concurrent interleaving -- it is a SPOT check
(the spec's own word), run ad hoc or wired into a monitoring cadence, not a total proof. It
also does not re-validate kernel semantics (P2: the service adds no truth of its own, and
neither does its auditor).

COMPARISON IS STRUCTURAL, NOT TEXTUAL: both sides are parsed JSON, id-sorted, and compared as
Python values (`compare_row_sets` below) -- so re-ordering or JSON whitespace differences that
carry no semantic content are not false positives; any ACTUAL row content or row SET
difference is reported by row id, single home for the diff logic (ADR-0012 P1) so both the
witness suite's negative control and a real operator invocation exercise the identical
comparator.

Usage:
    python3 serving/audit_served.py --base-url http://127.0.0.1:8420 \\
        --deployment /path/to/deployment.json [--endpoint /rows/current] [--view ledger_current]

Exit 0 on agreement; 1 on any row-set difference; 2 on a transport/infrastructure failure
(the served fetch or the psql read itself failed -- ADR-0002: an infrastructure failure is
not a "disagreement," and conflating the two would poison the audit's own meaning, the same
distinction s43's journaler draws between a policy refusal and a re-raised infrastructure
class).

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import is top-of-file.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "filing"))
import deployment_record  # noqa: E402
from boundary_service import BoundaryConfig, _query_json  # noqa: E402  (the ONE query helper, reused -- not a second reader, P1)


class AuditTransportError(Exception):
    """The served fetch or the kernel read itself failed -- not a row-set disagreement."""


def fetch_served(base_url: str, endpoint: str) -> list[dict[str, Any]]:
    url = base_url.rstrip("/") + endpoint
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            body = resp.read()
    except (urllib.error.URLError, OSError) as e:
        raise AuditTransportError(f"fetching {url} failed: {e.__class__.__name__}: {e}") from e
    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        raise AuditTransportError(f"served page at {url} was not valid JSON: {e}") from e
    if not isinstance(data, list):
        raise AuditTransportError(f"served page at {url} was not a JSON array (got {type(data).__name__})")
    return data


def fetch_kernel(cfg: BoundaryConfig, view: str, after_id: int, limit: int) -> list[dict[str, Any]]:
    try:
        rows = _query_json(
            cfg,
            f"SELECT coalesce(jsonb_agg(t ORDER BY t.id), '[]'::jsonb) FROM "
            f"(SELECT * FROM {cfg.schema}.{view} WHERE id > {after_id} "
            f"ORDER BY id LIMIT {limit}) t;",
        )
    except RuntimeError as e:
        raise AuditTransportError(f"reading {cfg.schema}.{view} directly failed: {e}") from e
    if not isinstance(rows, list):
        raise AuditTransportError(f"direct read of {cfg.schema}.{view} was not a JSON array")
    return rows


def compare_row_sets(served: list[dict[str, Any]], kernel: list[dict[str, Any]]) -> list[str]:
    """Structural row-set comparison, denominated in row id (ADR-0000 §9's denomination
    discipline: compare by the immutable id, never by list position). Returns a list of
    human-readable diff descriptions; an empty list means AGREE. Pure function -- no IO, so
    both a live audit run and the witness suite's negative control exercise this exact code."""
    served_by_id = {r["id"]: r for r in served}
    kernel_by_id = {r["id"]: r for r in kernel}
    diffs: list[str] = []
    only_served = sorted(set(served_by_id) - set(kernel_by_id))
    only_kernel = sorted(set(kernel_by_id) - set(served_by_id))
    if only_served:
        diffs.append(f"row id(s) present in the SERVED page but absent from the direct kernel read: {only_served}")
    if only_kernel:
        diffs.append(f"row id(s) present in the direct kernel read but absent from the SERVED page: {only_kernel}")
    for rid in sorted(set(served_by_id) & set(kernel_by_id)):
        s, k = served_by_id[rid], kernel_by_id[rid]
        if s != k:
            mismatched_keys = sorted({key for key in set(s) | set(k) if s.get(key) != k.get(key)})
            diffs.append(f"row id {rid}: served vs kernel disagree on field(s) {mismatched_keys} "
                         f"(served={ {k2: s.get(k2) for k2 in mismatched_keys} !r}, "
                         f"kernel={ {k2: k.get(k2) for k2 in mismatched_keys} !r})")
    return diffs


def run_audit(base_url: str, cfg: BoundaryConfig, endpoint: str, view: str,
              after_id: int = 0, limit: int = 1000) -> list[str]:
    served = fetch_served(base_url, f"{endpoint}?after_id={after_id}&limit={limit}")
    kernel = fetch_kernel(cfg, view, after_id, limit)
    return compare_row_sets(served, kernel)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--base-url", required=True, help="the running service's base URL, e.g. http://127.0.0.1:8420")
    p.add_argument("--deployment", required=True, help="path to this project's deployment.json")
    p.add_argument("--endpoint", default="/rows/current")
    p.add_argument("--view", default="ledger_current")
    p.add_argument("--after-id", type=int, default=0)
    p.add_argument("--limit", type=int, default=1000)
    args = p.parse_args(sys.argv[1:] if argv is None else argv)

    record = deployment_record.load_deployment(args.deployment)
    cfg = BoundaryConfig(record)
    try:
        diffs = run_audit(args.base_url, cfg, args.endpoint, args.view, args.after_id, args.limit)
    except AuditTransportError as e:
        sys.stderr.write(f"audit_served: TRANSPORT FAILURE (not a disagreement verdict): {e}\n")
        return 2

    if diffs:
        sys.stderr.write(f"audit_served: DISAGREE -- {args.endpoint} vs {args.view}:\n")
        for d in diffs:
            sys.stderr.write(f"  - {d}\n")
        return 1
    print(f"audit_served: AGREE -- {args.endpoint} matches {cfg.schema}.{args.view} "
          f"byte-for-byte over the compared page.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
