#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-07T03:29:13Z
#   last-change: 2026-07-14T22:20:21Z
#   contributors: 37017f46/main, a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""Seen-red specimen for the staging-guard gate (forecloses finding 33, commit-scope-sweep). Reproduces
the 420e5bf defect: the committer declares the paths THIS commit owns, but the staged index also holds a
concurrently-authored BACKLOG.md that was staged earlier and never unstaged — a bare `git commit` would
sweep it. The guard compares the declared manifest to the staged index and REFUSES, naming the swept
path. Pure in-memory probe (the staged-set reader is stubbed to the defect state); no real index touched."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "gates"))
import staging_guard as g  # noqa: E402


def main() -> int:
    # the committer's honest intent for THIS commit (what it git-add-ed):
    os.environ["CLAUDE_COMMIT_PATHS"] = "db/harness/006_foreclosure_debt.sql tools/file_foreclosure.py"
    # the index as it actually was at 420e5bf: the declared paths PLUS a swept concurrent BACKLOG.md
    g._staged_paths = lambda: {
        "db/harness/006_foreclosure_debt.sql", "tools/file_foreclosure.py", "BACKLOG.md"}
    rc = g.main()
    if rc == 0:
        print("SPECIMEN INERT — the guard passed a commit with an undeclared swept path (guard broken).")
        return 1
    print(f"# staging-guard REFUSED (exit {rc}) — a concurrently-authored BACKLOG.md staged but not "
          f"declared would have ridden along in the commit; the guard names it and blocks (finding 33).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
