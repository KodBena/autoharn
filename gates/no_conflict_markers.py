#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T22:42:37Z
#   last-change: 2026-07-11T22:42:37Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""no_conflict_markers — refuse a commit whose STAGED ADDITIONS contain raw git conflict
markers (the `<<<<<<< ` / `>>>>>>> ` pair-halves git writes into a file during a failed
merge and a human is supposed to remove during resolution).

WHY THIS GATE EXISTS (witnessed defect, 2026-07-12, ledgered as an orchestrator
self-report): merge commit b25272f landed with unresolved conflict markers baked into
BACKLOG.md — the orchestrator's keep-both resolution ran inside a compound shell command
whose sequencing failed silently, and nothing in the pre-commit chain looked. A downstream
agent caught it by accident while appending its own entry (fix: commit 1eb0750). Third
witnessed specimen of the ad-hoc worktree-merge ritual failing (the design memo is the
tracker item `worktree-ledgering-design`); this gate is the cheap deterministic guard that
does not wait for the memo.

CLASS, NOT INSTANCE: the check keys on the marker SHAPE git itself emits — a line
BEGINNING with exactly seven `<` or seven `>` followed by a space (git always writes
`<<<<<<< <ref>` / `>>>>>>> <ref>`). Deliberately NOT flagged: bare `=======` lines — they
are legitimate markdown (setext headings, rules) and cannot land alone; the `<`/`>`
pair-halves are each individually damning, and no unresolved merge can land without at
least one of them. Only ADDED lines in the staged diff are scanned (`git diff --cached
-U0`), so historical text that already carries a quoted marker never blocks an unrelated
edit, and a file can still QUOTE a marker deliberately by indenting or fencing it so the
line does not BEGIN with the marker (the teach-text says so).

Exit 0 clean; exit 1 with file:line teach-text on any hit. Runs in the pre-commit chain
after staging_guard (see hooks/pre-commit). Seen-red: seen-red/no-conflict-markers/.
"""
from __future__ import annotations

import re
import subprocess
import sys

_MARKER = re.compile(r"^\+(<{7}|>{7})( |$)")


def staged_added_marker_lines() -> list[tuple[str, str]]:
    """(file, offending added line) pairs from the staged diff, added lines only."""
    diff = subprocess.run(
        ["git", "diff", "--cached", "-U0", "--no-color"],
        capture_output=True, text=True, check=True,
    ).stdout
    hits: list[tuple[str, str]] = []
    current = "?"
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
        elif _MARKER.match(line):
            hits.append((current, line[1:]))
    return hits


def main() -> int:
    hits = staged_added_marker_lines()
    if not hits:
        print("no-conflict-markers: clean ✓  (no raw git conflict markers in staged additions)")
        return 0
    print("no-conflict-markers: REFUSED — staged additions contain raw git conflict "
          "markers (an unresolved merge is about to be committed):", file=sys.stderr)
    for fname, text in hits:
        print(f"  {fname}: {text[:80]}", file=sys.stderr)
    print("Resolve the merge fully (remove every `<<<<<<< `/`=======`/`>>>>>>> ` block, "
          "keeping the intended content), re-stage, and commit again. If you are QUOTING "
          "a marker deliberately, indent or fence it so the line does not begin with the "
          "marker.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
