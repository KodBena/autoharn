#!/usr/bin/env python3
"""enacts_chain — walk the design→enactment edge the e9/e10 vocabulary adds (consult 9 §4/§5.4.2,
consult 11 §7.4.2). Reads BOTH edge shapes: e9's scalar `enacts bigint` and e10's multi-target
`enacts bigint[]` (consult 11 §7.1.1 — historical comparability), auto-detected per session.

Four readouts:

  1. THE CHAIN — every enactment row and the design row(s) it enacts, walked via the FK/array.
     What a prose "enacts the jax fusion-functor decision" could never resolve mechanically, this
     resolves in one join. (Sampling the RIGHT antecedent is still a human/J check — the edge
     proves existence + precedence, not that the pointer is the correct design row; F20.)
  2. NEVER-ENACTED design rows — the id-22 pattern (a real design decision no enactment row
     points at) as a one-line SELECT.
  3. NULL/EMPTY enacts on enactment rows — in e9 the §4.4-denied shape; in e10 the DOCUMENTED
     honest-empty ("no single design row applies", consult 11 §7.1). Listed, not condemned.
  4. ALIAS SURFACE (consult 11 §4.2/§7.4.2) — enacts elements whose target is NOT a `decision`
     (a question/note/verification row in a design-antecedent slot: the 10/25/27→4 shape). All
     three of e9's wrong pointers land here; a target-kind flag catches them without touching the
     honest rows. Mechanically shrinkable reference-domain hygiene; reference TRUTH stays with
     review (F20).

Read-only. Consumes {session}.ledger (per-session). Nothing is written.
"""
import subprocess
import sys

PGHOST = "192.168.122.1"
PGDB = "epistemic"


def _psql(sql: str) -> str:
    out = subprocess.run(
        ["psql", "-h", PGHOST, "-d", PGDB, "-tA", "-F", "\x1f", "-R", "\x1e", "-c", sql],
        capture_output=True, text=True, check=True,
    )
    return out.stdout


def _rows(sql: str) -> list[list[str]]:
    # rstrip the single trailing newline psql appends to the whole result before splitting on
    # the record separator, so the last field of the last row carries no stray '\n'.
    return [r.split("\x1f") for r in _psql(sql).rstrip("\n").split("\x1e") if r.strip()]


def _enacts_is_array(session: str) -> bool:
    got = _psql(
        f"SELECT data_type FROM information_schema.columns "
        f"WHERE table_schema='{session}' AND table_name='ledger' AND column_name='enacts';"
    ).strip()
    return got == "ARRAY"


def report(session: str) -> None:
    rel = f"{session}.ledger"
    is_array = _enacts_is_array(session)
    print(f"# enacts-chain report — {rel}\n")

    print("== 1. design -> enactment chain (walked via the enacts FK) ==")
    if not is_array:
        # e9 scalar path — preserved verbatim for series comparability (byte-identical output).
        chain = _rows(
            f"SELECT e.id, e.concern, left(e.statement,60), d.id, coalesce(left(d.statement,60),'(none)') "
            f"FROM {rel} e LEFT JOIN {rel} d ON d.id = e.enacts "
            f"WHERE e.concern = 'enactment' ORDER BY e.id;")
        if not chain:
            print("  (no enactment rows)")
        for eid, concern, estmt, did, dstmt in chain:
            print(f"  enact #{eid}: {estmt.strip()}\n      -> design #{did}: {dstmt.strip()}")
    else:
        # e10 array path — each enactment row lists all its targets (one, several, or none).
        eids = _rows(
            f"SELECT e.id, left(e.statement,60) FROM {rel} e "
            f"WHERE e.concern = 'enactment' ORDER BY e.id;")
        if not eids:
            print("  (no enactment rows)")
        for eid, estmt in eids:
            targets = _rows(
                f"SELECT t.id, left(t.statement,60), t.kind FROM {rel} e "
                f"CROSS JOIN LATERAL unnest(e.enacts) AS u(tid) JOIN {rel} t ON t.id = u.tid "
                f"WHERE e.id = {int(eid)} ORDER BY t.id;")
            print(f"  enact #{eid}: {estmt.strip()}")
            if not targets:
                print(f"      -> (empty: no single design row applies)")
            for tid, tstmt, tkind in targets:
                print(f"      -> #{tid} [{tkind}]: {tstmt.strip()}")

    print("\n== 2. design rows never enacted (the id-22 wasted-ticket pattern) ==")
    if not is_array:
        never = _rows(
            f"SELECT d.id, left(d.statement,72) FROM {rel} d "
            f"WHERE d.concern = 'design' "
            f"AND NOT EXISTS (SELECT 1 FROM {rel} e WHERE e.enacts = d.id) ORDER BY d.id;")
    else:
        never = _rows(
            f"SELECT d.id, left(d.statement,72) FROM {rel} d "
            f"WHERE d.concern = 'design' "
            f"AND NOT EXISTS (SELECT 1 FROM {rel} e WHERE d.id = ANY(e.enacts)) ORDER BY d.id;")
    if not never:
        print("  (every design row has an enactment pointing at it — none wasted)")
    for did, dstmt in never:
        print(f"  design #{did} (never enacted): {dstmt.strip()}")

    if not is_array:
        print("\n== 3. unresolved / malformed enactment rows (gate should have blocked these) ==")
        bad = _rows(
            f"SELECT e.id, left(e.statement,60), coalesce(e.enacts::text,'NULL') FROM {rel} e "
            f"WHERE e.concern = 'enactment' AND (e.enacts IS NULL OR NOT EXISTS "
            f"(SELECT 1 FROM {rel} d WHERE d.id = e.enacts AND d.ts < e.ts)) ORDER BY e.id;")
        if not bad:
            print("  (none — every enactment row resolves to an earlier row, as the gate requires)")
        for eid, estmt, enacts in bad:
            print(f"  enact #{eid} (enacts={enacts}): {estmt.strip()}")
    else:
        print("\n== 3. NULL/empty enacts on enactment rows (the documented honest-empty, §7.1) ==")
        empty = _rows(
            f"SELECT e.id, left(e.statement,60) FROM {rel} e "
            f"WHERE e.concern = 'enactment' AND (e.enacts IS NULL OR cardinality(e.enacts) = 0) "
            f"ORDER BY e.id;")
        if not empty:
            print("  (every enactment row carries at least one resolving enacts element)")
        for eid, estmt in empty:
            print(f"  enact #{eid} (enacts empty — 'no single design row applies'): {estmt.strip()}")

    print("\n== 4. alias surface — enacts elements whose target is NOT a decision (§4.2) ==")
    if not is_array:
        alias = _rows(
            f"SELECT e.id, e.enacts, t.kind, left(t.statement,50) FROM {rel} e "
            f"JOIN {rel} t ON t.id = e.enacts "
            f"WHERE e.enacts IS NOT NULL AND t.kind <> 'decision' ORDER BY e.id;")
    else:
        alias = _rows(
            f"SELECT e.id, u.tid, t.kind, left(t.statement,50) FROM {rel} e "
            f"CROSS JOIN LATERAL unnest(e.enacts) AS u(tid) JOIN {rel} t ON t.id = u.tid "
            f"WHERE t.kind <> 'decision' ORDER BY e.id, u.tid;")
    if not alias:
        print("  (none — every enacts target is a decision row)")
    for eid, tid, tkind, tstmt in alias:
        print(f"  enact #{eid} -> #{tid} [{tkind}] (non-decision target): {tstmt.strip()}")


if __name__ == "__main__":
    for s in (sys.argv[1:] or ["s11"]):
        report(s)
