#!/usr/bin/env python3
"""stale_enactment_debt — hole (c) of the stale-design guardrails (consult 11 §5.4), an audit
query buildable today with no schema change: the journal × supersedes join.

Distinct from `soundness.unsound_derivation` (which is present-tense: an enactment ticket whose
antecedent was ALREADY defeated when it was logged). Stale-enactment DEBT is the temporal case:
a file was unlocked under a design antecedent D, then D was later SUPERSEDED, and governed work
continued on the file afterward — the file now carries edits justified by a retired design. For
each file: its last unlocking entry E → E's enacts antecedents → any antecedent defeated AFTER
E's unlock → list (file, antecedent, defeater, governed acts on the file since the defeat).

Zero hits expected on s10 (consult 11 §5.4: the one supersession's file-work all post-dates it);
the instrument earns its keep at e11 scale where revision-then-reuse actually overflows.

Read-only. Consumes the gate journal (which entry unlocked which file) and {session}.ledger
(the supersedes edges). Nothing is written.
"""
from __future__ import annotations

import json
import os
import sys

from soundness import load, load_amends  # DRY: same both-shapes ledger loader + the e13 amends edges

DEPLOYED_JOURNAL = os.path.expanduser(
    "~/w/vdc/1/epistemic-audit/logs/change_gate.journal.jsonl")


def _fresh_allows(journal_path: str) -> list[dict]:
    out = []
    try:
        for line in open(journal_path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("outcome") == "allowed" and not r.get("reused_ticket"):
                out.append(r)
    except FileNotFoundError:
        pass
    return out


def report(session: str, journal_path: str = DEPLOYED_JOURNAL) -> None:
    rows, edges, sup = load(session)
    ant: dict[int, list[int]] = {}
    for e, d in edges:
        ant.setdefault(e, []).append(d)
    # inverse supersedes: parent D -> superseders X (X replaces D)
    inv: dict[int, list[int]] = {}
    for child, parent in sup.items():
        inv.setdefault(parent, []).append(child)
    # e13 amends: parent D -> clause-defeaters (A, scope) that amend a clause of D (A.ts the defeat).
    amends_of: dict[int, list[tuple[int, str]]] = {}
    for a, d, scope in load_amends(session):
        amends_of.setdefault(d, []).append((a, scope))

    allows = _fresh_allows(journal_path)
    # last unlocking entry per file (max entry_ts)
    last: dict[str, dict] = {}
    for r in allows:
        f = r.get("file")
        if f and (f not in last or (r.get("entry_ts") or "") > (last[f].get("entry_ts") or "")):
            last[f] = r

    print(f"# stale-enactment-debt — {session}.ledger × {os.path.basename(journal_path)} "
          f"({len(allows)} fresh unlocks over {len(last)} files)\n")
    hits = 0
    unreachable = []  # F45/consult 17 item 5: no-antecedent tickets are unreachable-by-debt, not
    #                   silently vacuous — name them so the reader knows the vacuity is by
    #                   construction (an empty-enacts ticket has nothing to defeat), not by clean.
    for f, r in sorted(last.items()):
        eid = r.get("unlocked_by_entry")
        e_ts = r.get("entry_ts") or ""
        antD = ant.get(eid, [])
        if not antD:
            unreachable.append((f, eid))
        for d in antD:
            for x in inv.get(d, []):  # X supersedes D (whole-row)
                if x in rows and rows[x].ts > e_ts:   # defeated AFTER this file's unlock
                    hits += 1
                    since = [a for a in allows if a.get("file") == f
                             and (a.get("entry_ts") or "") >= rows[x].ts]
                    print(f"  DEBT {f}: unlocked by #{eid} (enacts #{d}); "
                          f"#{d} superseded by #{x} at {rows[x].ts} (after unlock {e_ts}); "
                          f"{len(since)} governed act(s) on the file since the defeat")
            for a, scope in amends_of.get(d, []):  # A clause-defeats D (e13; F44)
                if a in rows and rows[a].ts > e_ts:  # clause amended AFTER this file's unlock
                    hits += 1
                    since = [z for z in allows if z.get("file") == f
                             and (z.get("entry_ts") or "") >= rows[a].ts]
                    print(f"  CLAUSE-STALE {f}: unlocked by #{eid} (enacts #{d}); a clause of #{d} "
                          f"defeated by #{a} at {rows[a].ts} (after unlock {e_ts}) — scope: {scope}; "
                          f"{len(since)} governed act(s) on the file since the clause defeat")
    if hits == 0:
        print("  (no stale-enactment debt — every file's unlocking antecedent is still in force,"
              " or was defeated before the file was unlocked)")
    if unreachable:
        print("\n  UNREACHABLE-BY-DEBT (F45): these files' last unlocking ticket carries no design "
              "antecedent (empty enacts) — there is nothing for stale-debt to defeat, so their "
              "silence here is structural, not a clean bill:")
        for f, eid in unreachable:
            print(f"    {f}: last unlock #{eid} has no enacts antecedent")


if __name__ == "__main__":
    jp = DEPLOYED_JOURNAL
    args = sys.argv[1:]
    if args and args[0].startswith("--journal="):
        jp = os.path.expanduser(args[0].split("=", 1)[1]); args = args[1:]
    for s in (args or ["s11"]):
        report(s, jp)
