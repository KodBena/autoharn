#!/usr/bin/env python3
"""dto_authentic_verify — DERIVE-ONLY re-run of the DTO scratch standing derivation.

Reads the CURRENT `marriage_dto_scratch` state and runs the T_now/DTO/assumes closures WITHOUT
rebuilding the scratch (so it never wipes an attestation). This is the re-run for the maintainer's
authentic-attestation touchpoint: run it BEFORE the attestation to see `synthetic_standing`, and
AFTER to see `fragment_in_force_authentic` fire and `synthetic_standing` retire.

NOT `ledger_dto_scratch.py` — that one calls setup_scratch() and DROPS+REBUILDS the tables (resetting
the authentic slot to reserved), which would erase the maintainer's genuine attestation. This script
only derives.

DISPLAY-CONTRACT DISCIPLINE (Increment 3 item 3; the F49-class fix). A verifier may only DISPLAY a
predicate the program's `#show` contract actually EXPORTS. A queried predicate absent from that
contract does not derive to nothing — clingo never emits it at all, so printing "(none)" for it
silently conflates NOT-SHOWN with FALSE (the exact defect that hid `decomp_attested_authentic` while
the atom HELD internally). So `_display` FAILS LOUDLY (ADR-0002) on any queried-but-unshown predicate
rather than reporting a fabricated absence. The contract is derived from the loaded `.lp` files' own
`#show` directives — one home (ADR-0012 P1), never a hand-maintained second list.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import ledger_dto_scratch as m

# The programs whose composed derivation this verifier reads — the SAME stack run_closures loads,
# so the display contract is exactly the contract of the run that produced the atoms (no drift).
PROGRAMS: list[Path] = [m.TNOW_LP, m.DTO_LP, m.ASSUMES_LP]

_SHOW_RE = re.compile(r"^\s*#show\s+([A-Za-z_][A-Za-z0-9_]*)\s*/\s*\d+\s*\.", re.MULTILINE)


def shown_predicates(programs: list[Path]) -> frozenset[str]:
    """The predicate NAMES the loaded programs export via `#show` — the display contract, read from
    the programs themselves (ADR-0012 P1: one home). A name here is a predicate clingo will emit;
    a name NOT here is a predicate the run never prints, so a "(none)" for it would be a lie.

    Guard: a loaded program carrying NO `#show` at all means clingo shows EVERYTHING it grounds, so
    the contract is not the union of `#show` names — it is "all". Detecting that honestly (rather than
    silently returning a too-small set) is itself the F49 posture, so we refuse loudly if any loaded
    program has zero `#show` directives (none of this stack does today; the guard keeps it true)."""
    names: set[str] = set()
    for prog in programs:
        text = prog.read_text(encoding="utf-8")
        hits = _SHOW_RE.findall(text)
        if not hits:
            raise RuntimeError(
                f"display-contract undefined: {prog.name} carries NO #show directive, so clingo emits "
                f"EVERY grounded predicate and the exported set is not the union of #show names. "
                f"Refusing to claim a partial contract (F49: a silent wrong contract is the defect).")
        names.update(hits)
    return frozenset(names)


def make_display(atoms: set[str], shown: frozenset[str]):
    """Return a `display(pred)` that renders the atoms of `pred` — but ONLY for a predicate the
    program `#show` contract emits. A queried-but-unshown predicate raises (never "(none)")."""
    def display(pred: str) -> str:
        if pred not in shown:
            raise RuntimeError(
                f"display-contract violation: {pred!r} is NOT in the program #show contract "
                f"({sorted(shown)}). The verifier refuses to print '(none)' for a predicate the "
                f"program does not EXPORT — NOT-SHOWN is not FALSE (F49). Add `#show {pred}/N.` to "
                f"the program that owns it, or stop querying it.")
        hits = sorted(a for a in atoms if a.startswith(pred + "("))
        return "  ".join(hits) if hits else "(none)"
    return display


def main() -> int:
    atoms = m.run_closures(m.dto_edb() + m.assumes_edb(), PROGRAMS)
    shown = shown_predicates(PROGRAMS)
    show = make_display(atoms, shown)

    print(f"# DTO scratch standing — derive-only over the CURRENT {m.DB}.{m.SCHEMA} state (no rebuild)")
    print(f"  fragment_in_force:           {show('fragment_in_force')}")
    print(f"  fragment_in_force_authentic: {show('fragment_in_force_authentic')}")
    print(f"  synthetic_standing:          {show('synthetic_standing')}")
    print(f"  referent_in_current:         {show('referent_in_current')}")
    print(f"  decomp_attested_authentic:   {show('decomp_attested_authentic')}")
    authentic = show("fragment_in_force_authentic") != "(none)"
    synthetic = show("synthetic_standing") != "(none)"
    if authentic and not synthetic:
        print("\n# AUTHENTIC standing established — synthetic_standing retired. The attestation is a "
              "genuine human act (authentic:maintainer).")
    elif synthetic and not authentic:
        print("\n# PRE-TAP: standing rests only on the SYNTHETIC acceptance. The authentic:maintainer "
              "slot is RESERVED (unattested). Awaiting the maintainer's own attestation act.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
