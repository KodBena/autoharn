#!/usr/bin/env python3
"""Both-polarity fixture for gates/bounds_kernel_drift.py (ledger row 1514 item 2: the
bounds-vocabulary single-home build). That gate reads kernel/lineage/*.sql TEXT directly (Python
cannot import SQL) and asserts serving/bounds.py's named constants still agree with their
kernel-side CHECK twins; this fixture proves BOTH failure shapes the gate is built to catch,
plus the ordinary green case, without touching any real kernel/lineage file (frozen; this build
does not edit kernel SQL at all).

RED 1 (drift): a temp SQL file carrying the SAME anchor shape as the real s65 CHECK but a
DIFFERENT numeric literal (999 instead of 256) is fed to the gate's own `extract_int` +
compared against `bounds.IDENTITY_HEADER_MAX_BYTES` -- the mismatch must be reported as a
problem, not silently accepted.

RED 2 (false-SILENT refusal -- the failure mode the brief specifically names): a temp SQL file
with NO matching anchor text at all (the constraint renamed/reshaped, simulating a future kernel
edit this gate's regex no longer matches) must make `extract_int` FAIL LOUDLY (raise
RuntimeError), never silently return nothing / report agreement it never checked.

GREEN: the gate run for real, against the actual repo, exits 0 -- serving/bounds.py agrees with
both live kernel CHECK twins today.

Zero residue: all doctored SQL lives under a TemporaryDirectory."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own environment
# before any subprocess is spawned -- inherited by the whole process tree this fixture starts.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
_GATES_DIR = os.path.join(_REPO_ROOT, "gates")
_GATE_SCRIPT = os.path.join(_GATES_DIR, "bounds_kernel_drift.py")

sys.path.insert(0, _GATES_DIR)
import bounds_kernel_drift as gate  # noqa: E402  (the module under test: gates/bounds_kernel_drift.py)


def _real_anchor_text(literal: int) -> str:
    """A minimal SQL fragment carrying the SAME anchor shape gates/bounds_kernel_drift.py's
    `_S65_ANCHOR` regex matches (verified byte-for-byte against the real s65 constraint's own
    clause shape), parameterized only in the numeric literal -- so RED 1 below tests a REAL
    anchor match on DIFFERENT data, never a fabricated shape the gate would never actually see."""
    return (
        "ALTER TABLE :\"schema\".ledger ADD CONSTRAINT refusal_attempted_kind_length CHECK (\n"
        f"    refusal_attempted_kind IS NULL OR octet_length(refusal_attempted_kind) <= {literal});\n"
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="bounds-drift-fixture-") as tmp:
        # ---- RED 1: drift (same anchor shape, mismatched literal) -----------------------------
        mismatched_path = os.path.join(tmp, "s65-mismatched.sql")
        with open(mismatched_path, "w") as f:
            f.write(_real_anchor_text(999))  # kernel says 999; service (real bounds.py) says 256
        extracted = gate.extract_int(mismatched_path, gate._S65_ANCHOR, gate._S65_ANCHOR_DESC)
        assert extracted == 999, f"expected the doctored anchor to extract 999, got {extracted}"
        assert gate.bounds.IDENTITY_HEADER_MAX_BYTES == 256, (
            "fixture assumption broken: serving/bounds.py's IDENTITY_HEADER_MAX_BYTES is no "
            "longer 256 -- this fixture's RED-1 case needs re-deriving, not silently adjusting.")
        assert extracted != gate.bounds.IDENTITY_HEADER_MAX_BYTES, (
            "RED 1 fixture setup error: doctored literal accidentally matches the real constant")
        print(f"RED  ok (drift): doctored kernel literal {extracted} != service constant "
              f"{gate.bounds.IDENTITY_HEADER_MAX_BYTES} -- the mismatch the gate must catch is "
              f"real, not vacuous")

        # ---- RED 2: false-SILENT refusal -- anchor not found must FAIL LOUD, never silently ---
        reshaped_path = os.path.join(tmp, "s65-reshaped.sql")
        with open(reshaped_path, "w") as f:
            # A constraint that still mentions the same column/table but under a RENAMED
            # constraint and a DIFFERENT clause shape -- simulates a future kernel edit this
            # gate's anchor regex no longer matches (the false-SILENT scenario the brief names).
            f.write(
                "ALTER TABLE :\"schema\".ledger ADD CONSTRAINT refusal_attempted_kind_shape "
                "CHECK (\n    octet_length(refusal_attempted_kind) < 300);\n"
            )
        raised = False
        try:
            gate.extract_int(reshaped_path, gate._S65_ANCHOR, gate._S65_ANCHOR_DESC)
        except RuntimeError as e:
            raised = True
            assert "anchor NOT FOUND" in str(e), f"wrong RuntimeError shape: {e}"
        assert raised, (
            "RED 2 FAILED: extract_int returned silently instead of raising -- this IS the "
            "false-SILENT failure mode the gate exists to refuse (a stale anchor must crash "
            "loud, never report an agreement it never actually checked)")
        print("RED  ok (false-SILENT refused): a reshaped/renamed constraint makes extract_int "
              "raise RuntimeError, not silently pass")

        # ---- GREEN: the real gate, run for real, against the real repo ------------------------
        green = subprocess.run(
            [sys.executable, _GATE_SCRIPT], cwd=_REPO_ROOT, capture_output=True, text=True)
        assert green.returncode == 0, (
            f"GREEN expected exit 0, got {green.returncode}: stdout={green.stdout!r} "
            f"stderr={green.stderr!r}")
        assert "OK" in green.stdout, green.stdout
        print("GREEN ok: gates/bounds_kernel_drift.py exits 0 against the real repo -- "
              "serving/bounds.py agrees with both live kernel CHECK twins")

    print("ALL CASES OK -- bounds-vocabulary-drift both polarities (+false-SILENT refusal), "
          "zero residue")
    return 0


if __name__ == "__main__":
    sys.exit(main())
