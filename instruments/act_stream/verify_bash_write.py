#!/usr/bin/env python3
"""verify_bash_write — the standing fixture for the adapter's Bash-write classification (forecloses
finding 18: the acts<->ledger deriver classified a fenced WRITE only when it was a Write TOOL, so a file
written via a Bash redirection (`> path`, `>> path`) or `tee` produced NO write act and slipped the
fenced-write accounting). _bash_write_target closed that; this pins the behavior against a pre-registered
expectation table so a regression (a redirection stops being recognized) flips RED.

The expectation table is authored HERE and committed with the fix; it is the oracle. Registered
close/lint line id: `bash-write-classification`. Lazy imports banned.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from claude_code_adapter import _bash_write_target

# pre-registered (command -> the file the command WRITES, or None for a read / no-write):
EXPECT = [
    ("echo hi > /fenced/out.txt", "/fenced/out.txt"),
    ("echo hi >> /fenced/log.txt", "/fenced/log.txt"),
    ("tee /fenced/t.txt", "/fenced/t.txt"),
    ("tee -a /fenced/t.txt", "/fenced/t.txt"),
    ("cat /fenced/in.txt", None),           # a READ sets no target
    ("grep foo /fenced/in.txt", None),
    ("sed 's/a/b/' /fenced/in.txt", None),  # sed WITHOUT redirect writes nothing
    ("ls -la", None),
]


def check(classify=_bash_write_target) -> list[str]:
    """Divergences between the classifier and the pre-registered oracle (empty = agree)."""
    bad: list[str] = []
    for cmd, want in EXPECT:
        got = classify(cmd)
        if got != want:
            bad.append(f"{cmd!r}: classified {got!r}, oracle {want!r}")
    return bad


def main() -> int:
    bad = check()
    for b in bad:
        print(f"BASH-WRITE MISCLASSIFIED: {b}")
    if bad:
        print(f"# bash-write-classification FAIL — {len(bad)} command(s) diverge from the oracle "
              f"(a fenced Bash-redirection write is not being accounted).")
        return 1
    print(f"# bash-write-classification PASS — all {len(EXPECT)} commands classified per the oracle "
          f"(redirection/tee writes recognized; reads set no target).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
