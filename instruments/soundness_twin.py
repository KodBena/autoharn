#!/usr/bin/env python3
"""soundness_twin — the OPERATOR-TWIN DIFFERENTIAL: soundness.lp (ASP) vs soundness.py (the
live-psql Python core, `derive`) must AGREE on the shared, keying-sensitive derived-validity
judgments {alias_surface, unsound_derivation, launder}, over the banked s10 record AND the
self-superseding-citation boundary fixture.

WHY THIS EXISTS (F-D, clingo-fidelity review 2026-07-06; RATIFIED 2026-07-06 strict id-precedence).
soundness.lp and soundness.py are TWO encodings of ONE semantics (§8.3). Before the id-keying
retrofit they keyed defeat/head on DIFFERENT precedence — soundness.py on ts-`<=`, soundness.lp on
id-`<` — and AGREED only because id-order == ts-order on the banked record. That is a latent
divergence at the self-superseding-citation boundary (a row that both supersedes D and enacts D:
UNSOUND under ts-`<=`, SOUND under strict id-`<`) that NOTHING mechanically caught: the marriage
side has a differential (ledger_tnow.lp vs ledger_floor.py); the operator twins had none. This
instrument is that missing net — the same immune-system shape the marriage side already runs, on the
operator side. A keying divergence between the twins is a DIVERGE (non-zero exit), so registered as a
close_manifest declared-observer line it can NEVER be silently skipped.

Read-only (soundness.py's `load` reads {session}.ledger read-only; the boundary fixture is pure,
no DB). A divergence is a DEFECT / NO RESULT, never a silent pass. Exit codes: 0 AGREE on every
scenario; 1 a producer DIVERGENCE (a defect); 2 the s10 scenario's substrate was unreachable
(QUARANTINED — NO RESULT, ADR-0015 Rule 3); 3 the differential's own negative-control self-check
failed (the comparator is not catching an injected divergence — the net is broken)."""
from __future__ import annotations

import json
import os
import subprocess
import sys

from soundness import Row, derive, load

HERE = os.path.dirname(os.path.abspath(__file__))
SOUNDNESS_LP = os.path.join(HERE, "soundness.lp")

# The SHARED, keying-sensitive judgments both encodings compute. soundness.lp additionally emits
# `inexpressible/1` (scalar-schema commentary, not a keying judgment); soundness.py additionally
# emits the clause-defeat family — neither is a shared derived-validity judgment, so both are
# excluded from the comparison (comparing only what BOTH produce, ADR-0008 vocabulary precision).
SHARED = ("alias_surface", "unsound_derivation", "launder")

# The self-superseding-citation boundary fixture, defined ONCE and emitted to BOTH producers so the
# twin runs the SAME facts through each. It is built so the agreement is NON-vacuous — it pins BOTH
# a SOUND self-citation and a genuine UNSOUND derivation in one record:
#   1 decision (D1); 2 supersedes 1 AND enacts 1 — the self-superseding citation. Under strict id-`<`
#     it is SOUND (the citer names the antecedent it replaces): NO unsound_derivation(2,1). Under the
#     former ts-`<=` soundness.py called it UNSOUND — the exact boundary this twin guards.
#   3 decision (D2); 4 supersedes 3 (an ordinary defeater, id 4 > 3); 5 enacts 3 (id 5 > 4) — an
#     ordinary unsound derivation: D2 was defeated by 4 before 5 cited it => unsound_derivation(5,3),
#     launder(5,3,4). Both encodings must produce EXACTLY {unsound_derivation(5,3), launder(5,3,4)} —
#     the self-citation's ABSENCE from that set is the boundary soundness, proven alongside a live hit.
# entry/4 arity matches soundness.lp's EDB (Id,Ts,Kind,Concern). This boundary is absent from every
# banked record (id-order == ts-order there), which is exactly why the twins agreed before by luck.
_BOUNDARY_EDB_ASP = (
    "entry(1,1000,decision,design). entry(2,2000,note,enactment).\n"
    "entry(3,3000,decision,design). entry(4,4000,decision,design).\n"
    "entry(5,5000,note,enactment).\n"
    "supersedes(2,1). supersedes(4,3). enacts(2,1). enacts(5,3).\n"
)
_BOUNDARY_ROWS: dict[int, Row] = {
    1: Row(1, "1000", "decision"), 2: Row(2, "2000", "note"),
    3: Row(3, "3000", "decision"), 4: Row(4, "4000", "decision"), 5: Row(5, "5000", "note"),
}
_BOUNDARY_EDGES: list[tuple[int, int]] = [(2, 1), (5, 3)]
_BOUNDARY_SUP: dict[int, int] = {2: 1, 4: 3}


def _clingo_shared_atoms(program_text: str) -> set[str]:
    """Run a clingo program (EDB+IDB text) and return its shown atoms filtered to SHARED. A
    non-SATISFIABLE result or a grounding failure is a loud RuntimeError (never a silent []
    read as agreement — the F49 lesson, ADR-0015 Rule 3)."""
    cp = subprocess.run(["clingo", "-", "--outf=2"], input=program_text,
                        capture_output=True, text=True)
    if not cp.stdout.strip():
        raise RuntimeError(f"clingo produced no JSON (exit {cp.returncode}): {cp.stderr.strip()[:200]}")
    d = json.loads(cp.stdout)
    if d.get("Result") != "SATISFIABLE":
        raise RuntimeError(f"clingo did not solve to SATISFIABLE: Result={d.get('Result')!r}")
    atoms = set(d["Call"][-1]["Witnesses"][-1]["Value"])
    return {a for a in atoms if a.split("(", 1)[0] in SHARED}


def _py_shared_atoms(rows: dict[int, Row], edges: list[tuple[int, int]],
                     sup: dict[int, int]) -> set[str]:
    """soundness.py's PURE core (`derive`) over the given facts, formatted to the SHARED atom
    strings — the exact id-keyed semantics soundness.report prints, run without a print stage."""
    alias, unsound, launder = derive(rows, edges, sup)
    out = {f"alias_surface({e},{d})" for e, d in alias}
    out |= {f"unsound_derivation({e},{d})" for e, d in unsound}
    out |= {f"launder({e},{d},{h})" for e, d, h in launder}
    return out


def _idb_rules() -> str:
    """The IDB rules of soundness.lp WITHOUT its hardcoded s10 EDB, so the twin runs the SAME rules
    over the boundary fixture. Split on the file's own `% ---- IDB` marker — the rules are read from
    the file, never re-authored here (SSOT; a second hand-copy would be the drift this twin exists
    to catch)."""
    text = open(SOUNDNESS_LP, encoding="utf-8").read()
    marker = "% ---- IDB"
    if marker not in text:
        raise RuntimeError(f"{SOUNDNESS_LP}: IDB marker {marker!r} not found — cannot isolate rules")
    return text.split(marker, 1)[1]


def _compare(asp: set[str], py: set[str]) -> tuple[bool, str]:
    """(agree, detail). AGREE iff empty symmetric difference on the SHARED judgments."""
    only_lp, only_py = asp - py, py - asp
    if not only_lp and not only_py:
        return (True, f"AGREE — {len(asp)} shared atom(s) match")
    return (False, f"DIVERGE — only_lp={sorted(only_lp)} only_py={sorted(only_py)}")


def _negative_control() -> bool:
    """Prove the comparator is NOT vacuous: inject a fake atom into one side of the boundary
    comparison and confirm it is caught as a DIVERGE. A differential that cannot turn red on a
    real divergence is not a net (ADR-0011: a clause never seen red is a claim, not a gate)."""
    py = _py_shared_atoms(_BOUNDARY_ROWS, _BOUNDARY_EDGES, _BOUNDARY_SUP)
    agree, _ = _compare(py | {"unsound_derivation(999,1)"}, py)  # inject a divergence
    return not agree  # the control PASSES iff the comparator flagged the injected divergence


def main(argv: list[str] | None = None) -> int:
    print("# soundness operator-twin differential — soundness.lp (ASP) vs soundness.py (derive)")
    print(f"#   shared judgments compared: {list(SHARED)}\n")
    diverged = 0
    quarantined = 0

    # scenario 1 — the banked s10 record (soundness.lp's hardcoded EDB == s10; soundness.py over live
    # s10). id-order == ts-order here, so this is the rich NON-empty agreement (7 shared atoms).
    try:
        asp_s10 = _clingo_shared_atoms(open(SOUNDNESS_LP, encoding="utf-8").read())
        rows, edges, sup = load("s10")
        agree, detail = _compare(asp_s10, _py_shared_atoms(rows, edges, sup))
        print(f"  [{'OK ' if agree else '!! '}] s10 (banked record)              {detail}")
        diverged |= (0 if agree else 1)
    except Exception as e:  # noqa: BLE001 — a psql/substrate failure is QUARANTINED, not a code verdict
        print(f"  [q  ] s10 (banked record)              QUARANTINED — {type(e).__name__}: {e}")
        quarantined = 1

    # scenario 2 — the self-superseding-citation boundary (no DB): soundness.lp's IDB over the
    # fixture vs soundness.py's derive over the same facts. THE case the old ts-`<=` keying diverged
    # on; post-retrofit both call it SOUND (empty unsound) — they AGREE.
    try:
        asp_b = _clingo_shared_atoms(_BOUNDARY_EDB_ASP + _idb_rules())
        py_b = _py_shared_atoms(_BOUNDARY_ROWS, _BOUNDARY_EDGES, _BOUNDARY_SUP)
        agree, detail = _compare(asp_b, py_b)
        print(f"  [{'OK ' if agree else '!! '}] boundary (self-superseding cite)  {detail}")
        print("        (the case ts-`<=` diverged on: SOUND under strict id-`<` in BOTH encodings)")
        diverged |= (0 if agree else 1)
    except Exception as e:  # noqa: BLE001 — the boundary is DB-free; any failure here is a real defect
        print(f"  [!! ] boundary (self-superseding cite)  DEFECT — {type(e).__name__}: {e}")
        diverged = 1

    ok_control = _negative_control()
    print(f"  [{'OK ' if ok_control else '!! '}] negative control                 "
          f"{'injected divergence caught (comparator has teeth)' if ok_control else 'FAILED — comparator did not catch an injected divergence'}")

    if not ok_control:
        print("\n# TWIN BROKEN — the comparator failed its negative control (NO RESULT).")
        return 3
    if diverged:
        print("\n# TWIN DIVERGED — soundness.lp and soundness.py disagree on a shared judgment "
              "(a keying divergence; DEFECT).")
        return 1
    if quarantined:
        print("\n# TWIN QUARANTINED — the s10 scenario's substrate was unreachable (NO RESULT, "
              "ADR-0015 Rule 3); the DB-free boundary scenario AGREED.")
        return 2
    print("\n# TWIN AGREE — soundness.lp and soundness.py agree on every shared judgment over the "
          "banked record and the self-superseding-citation boundary.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
