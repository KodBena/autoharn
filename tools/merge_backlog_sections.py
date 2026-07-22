#!/usr/bin/env python3
"""merge_backlog_sections — a git MERGE DRIVER for BACKLOG.md's dated `## ` sections (design/
ORCH-WORKTREE-LEDGERING.md 3a: "`BACKLOG.md` ... gets the same treatment one level up: a
section-union driver keyed on the dated heading line -- sections are append-only point-in-time
records by the journal's own charter, so union is semantically exact."). Registered via
`.gitattributes` (`BACKLOG.md merge=backlog-section-union`) plus a one-time `git config` line (this
file's own docstring below).

THE UNIT OF MERGE is a SECTION: a `## `-prefixed heading line (NOT `### ` or deeper -- those are
subsections INSIDE one dated entry, not top-level journal entries) plus every line up to the next
`## ` heading or end of file. The file's PREAMBLE (everything before the first `## ` heading) is
merged as one more section under this same rule. A section's KEY is its exact heading-line text,
disambiguated by OCCURRENCE INDEX if the same heading text appears more than once in one side (the
Nth occurrence of heading text H keys as (H, N) -- so a real duplicate heading is never silently
aliased to one slot).

THE 3-WAY RULE PER SECTION KEY (ancestor `O`, current `A`, other `B`; a body absent on a side --
key not present there at all -- reads as `None`, "this side does not have this section"):

    A == B                    -> take it (both sides agree, trivially -- covers the common
                                  no-op-on-one-side-touched-on-neither case and identical edits)
    O is None (brand-new key) -> if exactly one of A/B has it, take that one (an ordinary append on
                                  one side); if BOTH have it and they differ, CONFLICT (two sides
                                  independently authored a DIFFERENT section under an identical
                                  heading -- a genuine collision, not an append)
    A == O                    -> B's side changed (or removed) it since the ancestor -- take B
    B == O                    -> A's side changed (or removed) it since the ancestor -- take A
    else                      -> BOTH sides changed it, differently, since the ancestor -- CONFLICT
                                  (this is the "same section edited on both sides" case the memo
                                  requires to FAIL LOUDLY, never silently union)

This is the exact append-only-vs-edited distinction the jsonl driver's algorithm does not need to
draw (a jsonl line is immutable once written; a BACKLOG section is prose that COULD legitimately be
edited in place after it lands, so unioning two divergent edits blindly would silently interleave
two different narratives of the same entry -- the sound thing is to refuse and let a human resolve
it, exactly as an ordinary git conflict would, but WITHOUT breaking on the common, safe case: two
sides that only ever APPENDED new dated sections after the ancestor, which resolves automatically).

ORDERING: the merged file is A's own section order, verbatim, for every key A has (with a resolved
body -- possibly B's, per the rule above); then any section whose key exists ONLY in B (never in A),
in B's own relative order, appended at the end -- the same "current's order first, other's novelties
appended" convention `tools/merge_jsonl.py` uses, apt here too because BACKLOG's own charter is
append-at-the-end (the tail of the file is always the newest dated entries).

CONFLICT RENDERING: a CLASS, real git-shaped conflict block --

    <<<<<<< A (current)
    <A's version of the section, or "(section absent on this side)">
    =======
    <B's version of the section, or "(section absent on this side)">
    >>>>>>> B (other)

-- markers matching EXACTLY the shape `gates/no_conflict_markers.py` keys on (a line beginning with
seven `<` or seven `>` then a space), so an unresolved instance of this driver's own loud failure is
independently catchable by that gate if it is ever committed unresolved (belt-and-braces: this
driver's own exit code already refuses the merge; the gate is the second, independent net if a human
force-commits over the markers anyway).

GIT MERGE DRIVER CONTRACT (gitattributes(5)): `%O`/`%A`/`%B` are ancestor/current/other temp file
paths; the driver overwrites `%A` with its result and exits 0 (clean) or non-zero (conflict -- git
still stages whatever the driver left in `%A`, which is why the conflict-marker rendering above
matters: it is what a human sees and resolves).

INDEPENDENTLY INVOCABLE (ADR-0012 P1/P2): `merge_sections()`/`parse()` are plain functions; the CLI
form takes the exact three positional paths a merge driver would receive.

USAGE:
  python3 tools/merge_backlog_sections.py <ancestor-path> <current-path> <other-path>
      Merges current-path and other-path against ancestor-path's baseline and OVERWRITES
      current-path. Exit 0 if every section resolved cleanly; exit 1 (conflict markers left in
      current-path) if one or more sections needed human resolution; exit 2 on a usage error.

ONE-TIME INSTALL (per clone; `.git/config` is unversioned, mirroring `hooks/pre-commit`'s own
"Install (once per clone...)" line):

    git config merge.backlog-section-union.name "dated-section union merge driver for BACKLOG.md"
    git config merge.backlog-section-union.driver "python3 tools/merge_backlog_sections.py %O %A %B"

`bootstrap/bootstrap.sh` installs this automatically on a fresh clone; the line above is the
manual/documented fallback for an already-cloned checkout.

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

_HEADING_RE = re.compile(r"^## (?!#)")  # a top-level dated `## ` heading; NOT `### ` (a subsection)

SectionKey = tuple[str, int]  # (heading text, occurrence index within this side's document)


def parse(text: str) -> tuple[list[str], list[tuple[str, list[str]]], bool]:
    """Split `text` into (preamble_lines, [(heading_line, body_lines), ...], had_trailing_newline).
    A `body_lines` run is every line up to (not including) the next `## ` heading or EOF."""
    had_trailing_newline = text.endswith("\n")
    lines = text.splitlines()
    preamble: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    current: list[str] | None = None
    for line in lines:
        if _HEADING_RE.match(line):
            current = []
            sections.append((line, current))
        elif current is None:
            preamble.append(line)
        else:
            current.append(line)
    return preamble, sections, had_trailing_newline


def keyed(sections: list[tuple[str, list[str]]]) -> tuple[dict[SectionKey, list[str]], list[SectionKey]]:
    """(key -> body, ordered key list) for one side's section list, keys disambiguated by
    occurrence index (module docstring, "THE UNIT OF MERGE")."""
    counts: Counter[str] = Counter()
    by_key: dict[SectionKey, list[str]] = {}
    order: list[SectionKey] = []
    for heading, body in sections:
        idx = counts[heading]
        counts[heading] += 1
        key = (heading, idx)
        by_key[key] = body
        order.append(key)
    return by_key, order


def _conflict_block(label: str, a_body: list[str] | None, b_body: list[str] | None) -> list[str]:
    """Real git-shaped conflict markers (module docstring, "CONFLICT RENDERING") -- each half
    individually matches `gates/no_conflict_markers.py`'s marker regex."""
    a_text = a_body if a_body is not None else ["(section absent on this side)"]
    b_text = b_body if b_body is not None else ["(section absent on this side)"]
    return ([f"<<<<<<< A (current) {label}"] + a_text +
            ["======="] + b_text +
            [f">>>>>>> B (other) {label}"])


def merge_sections(ancestor_text: str, current_text: str, other_text: str) -> tuple[str, list[str]]:
    """Returns (merged_text, conflict_labels). `conflict_labels` is empty iff the merge was clean;
    a non-empty list names every section key that needed human resolution (module docstring, "THE
    3-WAY RULE PER SECTION KEY")."""
    o_pre, o_sections, _ = parse(ancestor_text)
    a_pre, a_sections, a_trailing_nl = parse(current_text)
    b_pre, b_sections, _ = parse(other_text)
    o_by, _ = keyed(o_sections)
    a_by, a_order = keyed(a_sections)
    b_by, b_order = keyed(b_sections)

    all_keys: list[SectionKey] = list(a_order)
    seen_keys = set(a_order)
    for k in b_order:
        if k not in seen_keys:
            all_keys.append(k)
            seen_keys.add(k)

    conflicts: list[str] = []
    resolved: dict[SectionKey, list[str] | None] = {}
    conflicted_keys: set[SectionKey] = set()
    for key in all_keys:
        o_body, a_body, b_body = o_by.get(key), a_by.get(key), b_by.get(key)
        if a_body == b_body:
            resolved[key] = a_body
            continue
        if o_body is None:
            if a_body is not None and b_body is not None:
                conflicts.append(f"{key[0]!r} (occurrence {key[1]}): both sides independently "
                                  f"introduced this heading with different content")
                conflicted_keys.add(key)
                resolved[key] = None  # placeholder; rendered from a_by/b_by directly below
            else:
                resolved[key] = a_body if a_body is not None else b_body
            continue
        if a_body == o_body:
            resolved[key] = b_body  # only B changed (including removal) since the ancestor
        elif b_body == o_body:
            resolved[key] = a_body  # only A changed (including removal) since the ancestor
        else:
            conflicts.append(f"{key[0]!r} (occurrence {key[1]}): edited on both sides since the "
                              f"common ancestor")
            conflicted_keys.add(key)
            resolved[key] = None  # placeholder; rendered from a_by/b_by directly below

    # Preamble gets the identical 3-way rule, as its own pseudo-section.
    preamble_conflict = False
    if a_pre == b_pre:
        merged_pre = a_pre
    elif a_pre == o_pre:
        merged_pre = b_pre
    elif b_pre == o_pre:
        merged_pre = a_pre
    else:
        conflicts.append("(preamble): edited on both sides since the common ancestor")
        preamble_conflict = True
        merged_pre = []  # rendered from a_pre/b_pre directly below

    out_lines: list[str] = []
    if preamble_conflict:
        out_lines += _conflict_block("(preamble)", a_pre, b_pre)
    else:
        out_lines += merged_pre
    for key in all_keys:
        heading = key[0]
        if key in conflicted_keys:
            out_lines.append(heading)
            out_lines += _conflict_block(heading, a_by.get(key), b_by.get(key))
        else:
            body = resolved[key]
            if body is None:
                continue  # a section legitimately removed on the winning side -- drop it, not blank
            out_lines.append(heading)
            out_lines += body

    merged_text = "\n".join(out_lines) + ("\n" if a_trailing_nl else "")
    return merged_text, conflicts


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("usage: merge_backlog_sections.py <ancestor> <current> <other>  "
              "(git merge-driver %O %A %B)", file=sys.stderr)
        return 2
    ancestor, current, other = Path(argv[0]), Path(argv[1]), Path(argv[2])
    for p in (ancestor, current, other):
        if not p.is_file():
            print(f"merge_backlog_sections: not a file: {p}", file=sys.stderr)
            return 2
    merged_text, conflicts = merge_sections(
        ancestor.read_text(encoding="utf-8"),
        current.read_text(encoding="utf-8"),
        other.read_text(encoding="utf-8"))
    current.write_text(merged_text, encoding="utf-8")
    if conflicts:
        print("merge_backlog_sections: CONFLICT -- the following section(s) need human "
              "resolution (conflict markers left in place):", file=sys.stderr)
        for c in conflicts:
            print(f"  !! {c}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
