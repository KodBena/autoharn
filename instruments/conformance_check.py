#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-09T13:33:34Z
#   last-change: 2026-07-09T13:33:34Z
#   contributors: be693afb/main
# <<< PROVENANCE-STAMP <<<

"""conformance_check.py — the commission/conformance instrument's mechanical differ.

Mechanizes design/CONFORMANCE-INSTRUMENT.md (Fable-authored schema, ratified
2026-07-09) — itself the mechanism ADR-0013 Rule 1 names as missing: "a
structured commission/result-conformance record — a checklist the result is
mechanically diffed against." It converts executor narrowing (a scope item
with no verdict) and claim-without-artifact (a WITNESSED verdict whose witness
does not actually exist) from maintainer discoveries into a loud, named
refusal.

STATUS: OBSERVER ONLY. This script is not wired into any hook, gate, or
pre-commit chain — it is invoked by hand (or by a future `judge`-style verb).
Promotion to an enforcing gate is a maintainer act (design/CONFORMANCE-
INSTRUMENT.md, "Acceptance criteria").

Usage:
    python3 instruments/conformance_check.py <commission.json> <report.json> [--repo PATH]

`--repo PATH` sets the repository `commit`/`file` witnesses are resolved
against (default: current working directory). Exit code is the checker's
closed verdict vocabulary:

    0  CONFORMANT                 — every item WITNESSED or REFUSED_AS_EXPECTED,
                                     all mechanically-checkable witnesses verified.
    1  CONFORMANT_WITH_DEFERRALS  — as above, plus one or more honestly filed
                                     UNEXERCISED items (blocker + filing pointer).
    2  NONCONFORMANT              — coverage gap, a failed/missing witness, a
                                     dishonest UNEXERCISED, an unratified
                                     renegotiation, or a malformed input. Every
                                     reason names the failing item_id and states
                                     the fix (deny -> teach).

Boundaries (design/CONFORMANCE-INSTRUMENT.md, "Boundaries, honestly named"):
this checker verifies claim/artifact CORRESPONDENCE, not artifact QUALITY, and
not effect-level acceptance (ADR-0013 2026-07-02 amendment part 1) — those stay
review/ratifier acts. Of the five witness_types, only `commit` and `file` are
mechanically reachable here; `ledger_row`, `db_state`, `gate_output`, and
`doc_excerpt` each print a loud `OPERATOR-CHECK:` line naming the exact command
to run instead of silently passing (the F49 lesson: "(none)" must be provably
distinct from "did not run").
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

VERDICT_VALUES = {"WITNESSED", "REFUSED_AS_EXPECTED", "UNEXERCISED"}
WITNESS_TYPES = {"commit", "file", "ledger_row", "gate_output", "db_state", "doc_excerpt"}
MECHANICAL_WITNESS_TYPES = {"commit", "file"}

# ADR-0013 Rule 4's two named deferred-work homes. An UNEXERCISED blocker must
# point at one of these (or a path plainly naming one) to count as *filed*
# rather than *narrated and left*. Spec is silent on exact syntax; this is the
# smallest mechanical check consistent with "a blocker AND a filing pointer".
FILING_MARKERS = ("BACKLOG", "FINDINGS")

# Spec is silent on the exact syntax a renegotiation names its ratifier with.
# Smallest mechanical check: the string must contain "ratified by" (the form
# the spec's own example renegotiation field implies: "WHO ratified each").
RATIFIER_MARKER = "ratified by"

REQUIRED_COMMISSION_KEYS = ("commission_id", "scope")
REQUIRED_SCOPE_ITEM_KEYS = ("item_id", "mandate", "witness_type", "witness_hint")
REQUIRED_REPORT_KEYS = ("commission_id", "verdicts")
REQUIRED_VERDICT_KEYS = ("item_id", "verdict")


class Reason:
    """One NONCONFORMANT reason: a failing item (or the commission/report as a
    whole, item_id=None) plus the teaching fix (deny -> teach house style)."""

    def __init__(self, item_id: str | None, problem: str, fix: str) -> None:
        self.item_id = item_id
        self.problem = problem
        self.fix = fix

    def render(self) -> str:
        where = f"item_id={self.item_id}" if self.item_id else "commission/report"
        return f"  !! {where}: {self.problem}\n     fix: {self.fix}"


def load_json(path: Path, kind: str) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"REFUSE: {kind} not found at {path} — fix: check the path and re-run")
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"REFUSE: {kind} at {path} is not valid JSON ({e}) — fix: repair the JSON and re-run")
        return None
    if not isinstance(data, dict):
        print(f"REFUSE: {kind} at {path} is not a JSON object at the top level — fix: wrap it as one")
        return None
    return data


def verify_commit(repo: Path, commit_hash: str) -> bool:
    """True iff `commit_hash` resolves to a real commit in `repo`."""
    r = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"{commit_hash}^{{commit}}"],
        capture_output=True,
    )
    return r.returncode == 0


def verify_file(repo: Path, rel_or_abs: str) -> bool:
    """True iff the path exists, resolved against `repo` when relative."""
    p = Path(rel_or_abs)
    if not p.is_absolute():
        p = repo / rel_or_abs
    return p.exists()


def operator_check_line(witness_type: str, item_id: str, witness: str, witness_hint: str) -> str:
    """The exact command an operator runs to verify a witness_type this checker
    cannot reach mechanically. Never a silent pass (design doc, "Boundaries")."""
    if witness_type == "ledger_row":
        cmd = f'psql -c "SELECT 1 FROM {witness_hint} WHERE id = \'{witness}\';"'
    elif witness_type == "db_state":
        cmd = f'inspect {witness_hint} and confirm it matches: "{witness}"'
    elif witness_type == "gate_output":
        cmd = f're-run the gate at {witness_hint} and confirm its output contains: "{witness}"'
    elif witness_type == "doc_excerpt":
        cmd = f'open {witness_hint} and confirm it contains verbatim: "{witness}"'
    else:
        cmd = f"inspect {witness_hint} for witness: \"{witness}\""
    return f"  OPERATOR-CHECK: item_id={item_id} ({witness_type}) — {cmd}"


def check(commission: dict, report: dict, repo: Path) -> tuple[list[Reason], list[str], bool]:
    """Returns (reasons, operator_check_lines, any_honest_deferral)."""
    reasons: list[Reason] = []
    operator_lines: list[str] = []
    any_deferral = False

    for key in REQUIRED_COMMISSION_KEYS:
        if key not in commission:
            reasons.append(Reason(None, f"commission is missing required key {key!r}",
                                   f"add {key!r} to the commission and re-run"))
    for key in REQUIRED_REPORT_KEYS:
        if key not in report:
            reasons.append(Reason(None, f"report is missing required key {key!r}",
                                   f"add {key!r} to the report and re-run"))
    if reasons:
        return reasons, operator_lines, any_deferral

    if report.get("commission_id") != commission.get("commission_id"):
        reasons.append(Reason(
            None,
            f"report commission_id {report.get('commission_id')!r} does not match "
            f"commission commission_id {commission.get('commission_id')!r}",
            "point the report at the commission it actually claims to satisfy",
        ))

    scope = commission.get("scope") or []
    scope_by_id: dict[str, dict] = {}
    for item in scope:
        missing = [k for k in REQUIRED_SCOPE_ITEM_KEYS if k not in item]
        if missing:
            reasons.append(Reason(item.get("item_id"),
                                   f"commission scope item is missing {missing}",
                                   "fill in every required scope-item field before commissioning"))
            continue
        iid = item["item_id"]
        if iid in scope_by_id:
            reasons.append(Reason(iid, "duplicate item_id in commission scope",
                                   "give each scope item a distinct item_id"))
            continue
        if item["witness_type"] not in WITNESS_TYPES:
            reasons.append(Reason(iid, f"unknown witness_type {item['witness_type']!r}",
                                   f"use one of {sorted(WITNESS_TYPES)}"))
            continue
        scope_by_id[iid] = item

    verdicts = report.get("verdicts") or []
    verdicts_by_id: dict[str, list[dict]] = {}
    for v in verdicts:
        missing = [k for k in REQUIRED_VERDICT_KEYS if k not in v]
        if missing:
            reasons.append(Reason(v.get("item_id"), f"verdict is missing {missing}",
                                   "every verdict needs item_id and verdict fields"))
            continue
        iid = v["item_id"]
        if not isinstance(iid, str):
            # Rule 1: "An umbrella verdict over N items is N unverifiable claims —
            # the item_id join makes it unrepresentable." A list/umbrella id is
            # exactly that shape, caught here rather than silently accepted.
            reasons.append(Reason(None,
                                   f"verdict item_id {iid!r} is not a single string — looks like an "
                                   f"umbrella verdict over multiple items",
                                   "split into one verdict per item_id, one claim each"))
            continue
        verdicts_by_id.setdefault(iid, []).append(v)

    # Rule 1 — coverage: unknown item_id (verdict for something not in scope).
    for iid in verdicts_by_id:
        if iid not in scope_by_id:
            reasons.append(Reason(iid, "verdict references an item_id not in the commission scope",
                                   "match the verdict's item_id to a real scope item, or remove it"))

    # Rule 1 — coverage: every scope item has exactly one verdict.
    for iid, item in scope_by_id.items():
        vlist = verdicts_by_id.get(iid, [])
        if not vlist:
            reasons.append(Reason(iid, "no verdict filed for this commissioned item — the narrowing tell",
                                   "file a WITNESSED / REFUSED_AS_EXPECTED / UNEXERCISED verdict for it"))
            continue
        if len(vlist) > 1:
            reasons.append(Reason(iid, f"{len(vlist)} verdicts filed for one item_id (ambiguous claim)",
                                   "file exactly one verdict per item_id"))
            continue
        v = vlist[0]
        verdict = v.get("verdict")
        if verdict not in VERDICT_VALUES:
            reasons.append(Reason(iid, f"verdict value {verdict!r} is not one of {sorted(VERDICT_VALUES)}",
                                   "use WITNESSED, REFUSED_AS_EXPECTED, or UNEXERCISED"))
            continue

        if verdict in ("WITNESSED", "REFUSED_AS_EXPECTED"):
            witness = v.get("witness")
            if not witness:
                reasons.append(Reason(iid, f"verdict claims {verdict} but carries no witness",
                                       f"cite the {item['witness_type']} witness named in the commission"))
                continue
            wtype = item["witness_type"]
            if wtype == "commit":
                if not verify_commit(repo, str(witness)):
                    # Rule 2 / ADR-0013 2026-07-02 amendment: a witness that fails
                    # verification is treated as no claim at all.
                    reasons.append(Reason(
                        iid,
                        f"witness commit {witness!r} does not exist in {repo} — "
                        f"a verdict whose witness fails verification is treated as no claim",
                        "commit the deliverable and cite the real commit hash, or file the honest gap",
                    ))
            elif wtype == "file":
                if not verify_file(repo, str(witness)):
                    reasons.append(Reason(
                        iid,
                        f"witness path {witness!r} does not exist under {repo} — "
                        f"a verdict whose witness fails verification is treated as no claim",
                        "write the file at the committed path, or file the honest gap",
                    ))
            else:
                operator_lines.append(operator_check_line(wtype, iid, str(witness), item["witness_hint"]))

        elif verdict == "UNEXERCISED":
            blocker = v.get("blocker")
            if not blocker:
                reasons.append(Reason(iid, "UNEXERCISED with no blocker stated — a silent gap",
                                       "state the concrete blocker and where it is filed (BACKLOG/FINDINGS)"))
            elif not any(marker.lower() in str(blocker).lower() for marker in FILING_MARKERS):
                reasons.append(Reason(
                    iid,
                    "UNEXERCISED blocker names no filing pointer (BACKLOG/FINDINGS)",
                    "file the deferral in BACKLOG.md (or FINDINGS.md) and reference it in the blocker text",
                ))
            else:
                any_deferral = True

    # Rule 4 — renegotiations must each name their ratifier.
    for i, reneg in enumerate(report.get("renegotiations") or []):
        if RATIFIER_MARKER not in str(reneg).lower():
            reasons.append(Reason(
                None,
                f"renegotiation[{i}] does not name who ratified it: {reneg!r}",
                f'state who authorized the change, e.g. "...{RATIFIER_MARKER} <name>"',
            ))

    return reasons, operator_lines, any_deferral


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("commission", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("--repo", type=Path, default=Path("."),
                         help="repo root commit/file witnesses resolve against (default: cwd)")
    args = parser.parse_args(argv)

    commission = load_json(args.commission, "commission")
    report = load_json(args.report, "report")
    if commission is None or report is None:
        print("NONCONFORMANT (input could not be read)")
        return 2

    repo = args.repo.resolve()
    reasons, operator_lines, any_deferral = check(commission, report, repo)

    # Extras: Rule 4's mirror failure (over-scope). Flagged for the ratifier,
    # never itself a NONCONFORMANT reason — the spec names it as symmetric
    # visibility, not a violation.
    extras = report.get("extras") or []
    if extras:
        print(f"EXTRAS flagged for the ratifier ({len(extras)}, self-declared over-scope):")
        for e in extras:
            print(f"  - {e}")

    if operator_lines:
        print(f"OPERATOR-CHECK required ({len(operator_lines)} witness(es) this checker cannot reach):")
        for line in operator_lines:
            print(line)

    if reasons:
        print(f"NONCONFORMANT ({len(reasons)} reason(s)):")
        for r in reasons:
            print(r.render())
        return 2

    if any_deferral:
        print("CONFORMANT_WITH_DEFERRALS: every item WITNESSED/REFUSED_AS_EXPECTED or honestly "
              "UNEXERCISED-and-filed.")
        return 1

    print("CONFORMANT: every item WITNESSED or REFUSED_AS_EXPECTED, every reachable witness verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
