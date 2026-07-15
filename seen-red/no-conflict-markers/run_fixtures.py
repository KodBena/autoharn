#!/usr/bin/env python3
"""Both-polarity fixture for gates/no_conflict_markers.py (witnessed defect: merge b25272f
landed raw conflict markers in BACKLOG.md; this gate refuses that class at commit time).

RED: a staged addition whose line begins with a raw `<<<<<<< HEAD` marker is REFUSED.
GREEN: a staged addition that merely QUOTES a marker (indented) passes, as does clean text.
Runs in a throwaway git repo under /tmp; zero residue."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

GATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "gates", "no_conflict_markers.py")


def run(cwd: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), cwd=cwd, capture_output=True, text=True)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="ncm-fixture-") as tmp:
        run(tmp, "git", "init", "-q")
        run(tmp, "git", "config", "user.email", "fixture@example.invalid")
        run(tmp, "git", "config", "user.name", "fixture")

        # RED: raw marker at line start in a staged addition
        with open(os.path.join(tmp, "bad.md"), "w") as f:
            f.write("some text\n<<<<<<< HEAD\ntheir side\n>>>>>>> branch\n")
        run(tmp, "git", "add", "bad.md")
        red = run(tmp, sys.executable, GATE)
        assert red.returncode == 1, f"RED expected exit 1, got {red.returncode}: {red.stderr}"
        assert "REFUSED" in red.stderr and "bad.md" in red.stderr, red.stderr
        print("RED  ok: raw marker in staged addition refused, file named")
        run(tmp, "git", "reset", "-q")

        # GREEN: quoted (indented) marker + bare ======= (legit markdown) pass
        with open(os.path.join(tmp, "good.md"), "w") as f:
            f.write("Heading\n=======\nquoting a marker:\n    <<<<<<< HEAD\nis fine indented\n")
        run(tmp, "git", "add", "good.md")
        green = run(tmp, sys.executable, GATE)
        assert green.returncode == 0, f"GREEN expected exit 0, got {green.returncode}: {green.stderr}"
        print("GREEN ok: indented quote + bare ======= pass clean")
    print("ALL CASES OK -- no-conflict-markers both polarities, zero residue")
    return 0


if __name__ == "__main__":
    sys.exit(main())
