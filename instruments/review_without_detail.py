#!/usr/bin/env python3
"""review_without_detail — a DESCRIPTIVE close-line consumer (consult 37 Addendum A; finding 38). Same
tier as proxy_written: it surfaces every `kind='review'` ledger row that carries NO `review_detail`, and
adjudication disposes it — it does NOT gate the close.

WHY A CONSUMER, NOT A WRITE-TIME FIX. The atomic review+detail write-time fix was DECLARED NOT SHIPPED
(Addendum A): the deferred-constraint form refuses an honest self-review recorded via the heredoc /
per-statement-autocommit idiom the e17 subject actually used — a refusal predicate must never capture a
shape honest work takes (F34-lineage scoping discipline). A close-line consumer covers the class WITHOUT
touching write-time semantics: it names the detail-less review at close, covering BOTH the dishonest-path
stub (finding 38's e17 specimen, row 12) AND the honest-path crash-between-inserts the atomic form was
never scoped to anyway. Reading, not refusing.

Registered close/lint line id: `review-without-detail`. Lazy imports banned.
"""
from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "filing"))
from ledger_target import resolve  # noqa: E402
import pghost_resolve  # noqa: E402 (filing/pghost_resolve.py -- never a literal host default)

PGHOST = pghost_resolve.resolve_pghost("EPISTEMIC_PGHOST")


@dataclass(frozen=True)
class ReviewRow:
    id: int
    has_detail: bool


def derive(rows: list[ReviewRow]) -> list[int]:
    """PURE: the ids of `kind='review'` rows (each ReviewRow here IS a review row) with no review_detail."""
    return sorted(r.id for r in rows if not r.has_detail)


def _query(db: str, schema: str) -> list[ReviewRow]:
    sql = (f'SELECT l.id, EXISTS(SELECT 1 FROM "{schema}".review_detail d WHERE d.ledger_id=l.id) '
           f'FROM "{schema}".ledger l WHERE l.kind = \'review\' ORDER BY l.id;')
    cp = subprocess.run(["psql", "-h", PGHOST, "-d", db, "-tA", "-F", "|", "-c", sql],
                        capture_output=True, text=True, timeout=30)
    if cp.returncode != 0:
        raise RuntimeError(cp.stderr.strip()[-160:])
    rows = []
    for ln in cp.stdout.splitlines():
        if ln.strip():
            rid, has = ln.split("|")
            rows.append(ReviewRow(int(rid), has == "t"))
    return rows


def atoms_for(target: str) -> tuple[str, str]:
    """(status, detail) — DESCRIPTIVE, never gating. QUARANTINED if the ledger cannot be read."""
    t = resolve(target)
    try:
        rows = _query(t.db, t.schema)
    except RuntimeError as e:
        return ("QUARANTINED", f"cannot read {t.db}.{t.schema}.ledger: {e}")
    stubs = derive(rows)
    if not stubs:
        return ("OK", f"0 finding(s): (none) [DESCRIPTIVE — adjudication disposes; does not gate]")
    return ("OK", f"{len(stubs)} finding(s): {[f'review_without_detail({i})' for i in stubs]} "
            f"[DESCRIPTIVE — adjudication disposes; does not gate]")


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("usage: review_without_detail.py <target>", file=sys.stderr)
        return 2
    st, detail = atoms_for(args[0])
    print(f"review_without_detail: {st} {detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
