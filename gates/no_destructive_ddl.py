#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-07T01:32:54Z
#   last-change: 2026-07-07T02:05:02Z
#   contributors: 37017f46/main
# <<< PROVENANCE-STAMP <<<

"""no_destructive_ddl — the destructive-DDL guard (foreclosure specimen 5; forecloses findings 24 + 30,
the acts-schema-reset class: an ad-hoc `DROP SCHEMA acts CASCADE` that took out acts.ruling/act/stream
as UNDECLARED collateral). ADR-0000 never-again for the "blast radius wider than declared" class.

THE RULE. A `DROP SCHEMA <x> CASCADE` (or `DROP ... CASCADE`) is banned outside a designated migration
path UNLESS the destructive statement DECLARES its target on the same or the preceding line with a
`declared-drop: <name>` marker — so a CASCADE can never silently take out more than the author named.
An undeclared CASCADE is the finding-24/30 shape; the guard refuses it loudly (exit 1), never silent.

Designated migration path (allowed without a marker): `db/harness/*.sql` / `db/**/*.sql` (the DDLs whose
whole job is (re)building a schema — their `DROP SCHEMA ... CASCADE` rewind is the declared intent).

Enforced mechanically: this guard is a registered close/lint line (`destructive-ddl-guard`); its
foreclosure row pins a banked SEEN-RED artifact. Lazy imports banned.

  no_destructive_ddl.py <path> [<path> ...]     # scan files/dirs; exit 1 on any undeclared CASCADE
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_CASCADE = re.compile(r"\bDROP\s+(?:SCHEMA|TABLE|DATABASE)\b[^;]*\bCASCADE\b", re.IGNORECASE)
_DECLARED = re.compile(r"declared-drop\s*:", re.IGNORECASE)
# an EXECUTION marker: the CASCADE is actually run (not merely documented in a comment/docstring/REWIND
# note). A DROP CASCADE that co-occurs with a psql/execute/subprocess call is a real destructive act.
_EXEC = re.compile(r"\b(?:_?psql|execute|\.run\(|cursor|ON_ERROR_STOP)\b", re.IGNORECASE)
_COMMENT = re.compile(r"^\s*(?:#|--|\*|\"\"\"|''')")
_ALLOWED_DIRS = ("db/",)  # migration DDLs: their DROP ... CASCADE rewind is the declared intent
# seen-red evidence specimens (ADR-0011) are RED BY DESIGN: their whole job is to carry the hazard
# pattern the gate catches (e.g. finding-24's own undeclared CASCADE). Scanning them would make the
# gate fail on its own banked proof — the evidence tree is documentation of a caught hazard, not a live
# code path. Exempt it, same spirit as the migration-path exemption.
_EVIDENCE_DIRS = ("docs/adr-evidence/seen-red/",)
_SCAN_EXT = (".py", ".sql", ".sh")


def _is_migration(path: str) -> bool:
    p = path.replace(os.sep, "/")
    return (any(f"/{d}" in p or p.startswith(d) for d in _ALLOWED_DIRS)
            or any(f"/{d}" in p or p.startswith(d) for d in _EVIDENCE_DIRS))


def scan_text(text: str, path: str) -> list[tuple[int, str]]:
    """Undeclared EXECUTABLE CASCADE hits: [(line_no, line)]. A hit is a DROP ... CASCADE that is actually
    RUN — an execution marker (psql/execute/subprocess) on the line for .py/.sh, or a non-comment SQL
    statement for .sql. EXEMPT: a migration DDL (db/), a comment/docstring/REWIND note (documentation, not
    an act), or a `declared-drop:` marker on/above the line (the author named the blast radius)."""
    if _is_migration(path):
        return []
    is_sql = path.endswith(".sql")
    hits: list[tuple[int, str]] = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not _CASCADE.search(line):
            continue
        if _COMMENT.search(line):                       # a comment / docstring line — documentation, not an act
            continue
        if not is_sql and not _EXEC.search(line):       # .py/.sh: only flag when actually executed
            continue
        prev = lines[i - 1] if i > 0 else ""
        if _DECLARED.search(line) or _DECLARED.search(prev):   # blast radius declared by the author
            continue
        hits.append((i + 1, line.strip()))
    return hits


def _iter_files(paths: list[str]):
    for p in paths:
        pp = Path(p)
        if pp.is_dir():
            for ext in _SCAN_EXT:
                yield from pp.rglob(f"*{ext}")
        elif pp.is_file():
            yield pp


def main(argv: list[str] | None = None) -> int:
    paths = argv if argv is not None else sys.argv[1:]
    if not paths:
        print("usage: no_destructive_ddl.py <path> [<path> ...]", file=sys.stderr)
        return 2
    total = 0
    for f in _iter_files(list(paths)):
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for ln, src in scan_text(text, str(f)):
            total += 1
            print(f"UNDECLARED CASCADE: {f}:{ln}: {src}")
    if total:
        print(f"# destructive-ddl-guard FAIL — {total} undeclared DROP ... CASCADE. Add a "
              f"`declared-drop: <name>` marker on/above the line, or move it into a db/ migration.")
        return 1
    print("# destructive-ddl-guard PASS — no undeclared DROP ... CASCADE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
