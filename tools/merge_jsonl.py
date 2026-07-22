#!/usr/bin/env python3
"""merge_jsonl — a git MERGE DRIVER for append-only JSONL ledgers (vestigial_documentation/design/ORCH-WORKTREE-LEDGERING.md
3a: "The jsonl merge driver (mechanize the ritual)"). Registered via `.gitattributes`
(`attestations/*.jsonl merge=jsonl-union`) plus a one-time `git config` line (this file's own
docstring below, and user-guide/USER-CONFIGURATION.md / bootstrap/bootstrap.sh carry the same line -- .git/config
is unversioned, so every clone installs it once, mirroring `hooks/pre-commit`'s own
`git config core.hooksPath hooks` precedent).

THE ALGORITHM (sound because the file is APPEND-ONLY, per the memo's own words): union of lines,
order preserved per side, identity being the line's own BYTES. `current`'s lines come first in
`current`'s own order; then every line from `other` that does not already appear (byte-identical) in
`current` is appended, in `other`'s own order. No ancestor comparison is needed or used -- an
append-only file's lines are immutable once written, so a line present on either side belongs in the
union, full stop; a duplicate is only possible for a byte-identical record, and byte-identical union
collapses it harmlessly (a record cannot "conflict" with itself). This NEVER produces a conflict --
jsonl-union's exit code is always 0 (see the memo's honest-limits §4: this makes FILE merges
mechanical, not a general concurrent-SEMANTIC-edit tool; the BACKLOG section-union driver
(tools/merge_backlog_sections.py) is the sibling that DOES conflict-check, because prose sections are
not immutable-once-written the way one jsonl line is).

GIT MERGE DRIVER CONTRACT (gitattributes(5), "Defining a custom merge driver"): git substitutes `%O`
(the common ancestor's temp file), `%A` (the current/"ours" temp file -- ALSO where the driver must
leave its result), `%B` (the other/"theirs" temp file), invokes `driver %O %A %B` from the top of the
working tree, and expects the driver to overwrite `%A` with the merged content, exiting 0 on a clean
merge or non-zero on a conflict (git then stages `%A`'s content either way). This driver never
conflicts, so it always writes the union to `%A` and exits 0. The ancestor path (`%O`) is accepted
for contract-compliance (git always passes it) but deliberately UNUSED (see "THE ALGORITHM" above).

INDEPENDENTLY INVOCABLE (ADR-0012 P1/P2, composability): `union_lines()` is a plain function callable
from any Python caller (tests, another tool), and the CLI form below takes the exact three positional
paths a merge driver would receive -- so this file works BOTH as `git`'s own configured driver AND as
a standalone `python3 tools/merge_jsonl.py <ancestor> <current> <other>` for scripting/testing.

USAGE:
  python3 tools/merge_jsonl.py <ancestor-path> <current-path> <other-path>
      Merges current-path and other-path's lines (ancestor-path is read for contract-compliance but
      not used in the algorithm) and OVERWRITES current-path with the union. Exit 0 always (see
      above); a non-existent path is the one usage error (exit 2).

ONE-TIME INSTALL (per clone; `.git/config` is unversioned, mirroring `hooks/pre-commit`'s own
"Install (once per clone...)" line):

    git config merge.jsonl-union.name "union merge driver for append-only jsonl ledgers"
    git config merge.jsonl-union.driver "python3 tools/merge_jsonl.py %O %A %B"

`bootstrap/bootstrap.sh` installs this automatically on a fresh clone (mirrors its existing
`git config core.hooksPath hooks` step); the line above is the manual/documented fallback for an
already-cloned checkout that predates this commission, or a worktree whose shared `.git/config`
was never re-run through bootstrap.sh.

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import sys
from pathlib import Path


def union_lines(current_lines: list[str], other_lines: list[str]) -> list[str]:
    """Union of two line lists: `current_lines` first, in their own order; then every line from
    `other_lines` not already present (byte-identical) in `current_lines`, in `other_lines`' own
    order. Pure, side-effect-free -- the one home of the algorithm (ADR-0012 P1)."""
    seen = set(current_lines)
    merged = list(current_lines)
    for line in other_lines:
        if line not in seen:
            merged.append(line)
            seen.add(line)
    return merged


def _read_lines(path: Path) -> list[str]:
    """Read a text file as a list of lines with NO trailing-newline noise (each element is one
    line's content, newline-stripped) -- `\\n`-delimited, matching jsonl's own line convention.
    An empty file yields `[]`, never `['']`."""
    text = path.read_text(encoding="utf-8")
    if text == "":
        return []
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()  # a trailing newline produces one empty trailing split element; drop it
    return lines


def merge_files(ancestor_path: Path, current_path: Path, other_path: Path) -> None:
    """Read current/other, union them, overwrite current_path in place -- the git merge-driver
    contract (writes to %A). `ancestor_path` is accepted (git always passes %O) but unused (see
    module docstring, "THE ALGORITHM")."""
    del ancestor_path  # unused by design; named so the signature documents the contract honestly
    current_lines = _read_lines(current_path)
    other_lines = _read_lines(other_path)
    merged = union_lines(current_lines, other_lines)
    body = "\n".join(merged) + ("\n" if merged else "")
    current_path.write_text(body, encoding="utf-8")


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("usage: merge_jsonl.py <ancestor> <current> <other>  (git merge-driver %O %A %B)",
              file=sys.stderr)
        return 2
    ancestor, current, other = Path(argv[0]), Path(argv[1]), Path(argv[2])
    for p in (current, other):
        if not p.is_file():
            print(f"merge_jsonl: not a file: {p}", file=sys.stderr)
            return 2
    merge_files(ancestor, current, other)
    return 0  # always clean (see module docstring, "THE ALGORITHM")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
