#!/usr/bin/env python3
"""Seen-red specimen for the bash-write-classification gate (forecloses finding 18). Reproduces the
pre-fix classifier — the deriver recognized a fenced WRITE only when it was a Write tool, so a Bash
redirection/tee wrote a file with NO write act. The naive classifier below returns None for every Bash
command (its whole defect); the gate's oracle table then diverges on the four redirection/tee writes.
The captured divergence is banked as red.txt. Run from the harness repo root."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path("/home/bork/w/vdc/1/epistemic-operator/tools/act_stream")))
from verify_bash_write import check  # noqa: E402


def _naive_write_only(command: str) -> None:
    """The finding-18 defect: only a Write TOOL is a fenced write; a Bash command is never one."""
    return None


def main() -> int:
    bad = check(classify=_naive_write_only)
    if not bad:
        print("SPECIMEN INERT — the naive Write-only classifier did not diverge (unexpected).")
        return 1
    for b in bad:
        print(f"BASH-WRITE MISCLASSIFIED: {b}")
    print(f"# bash-write-classification FAIL — {len(bad)} command(s) diverge from the oracle "
          f"(a fenced Bash-redirection write is not being accounted).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
