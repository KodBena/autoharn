#!/usr/bin/env python3
"""strip_provenance_banners.py — one-shot, idempotent removal of the retired PROVENANCE-STAMP
banner (ledger row 1903: the in-file provenance banner is retired; provenance migrates to a
database schema, design pending — this tool performs the mechanical half of that retirement,
"can be bulk-stripped and adjudicated e.g. by a Sonnet agent, because the format is fairly
machine-readable" per the maintainer's commission, row 1904).

SCOPE, per the commission's amendment: this is STRIP-ONLY. An earlier draft of this task also
harvested every banner into a JSON artifact before stripping; the maintainer withdrew that
requirement (no auditor is owed the record — git history already preserves every banner at
every pre-strip commit immutably, and the banner ledger is lossy-by-construction so it should
not seed the future provenance schema). What remains load-bearing is the CONSERVATION half:
this script must never eat file CONTENT that merely resembles a banner (a fixture testing the
stamping hook, a doc quoting the format, a captured log). That's why the recognizer below is
deliberately the same structural, no-false-positive shape as the hook's own `_find_banner`
(hooks/stamp_provenance.py) — a candidate is stripped only if it reproduces the hook's exact
5-line fixed shape, at the hook's own comment-lead for that file's extension, near the very top
of the file (within FIRST_LINE_BUDGET lines — a real banner is only ever inserted right after an
optional shebang / coding-cookie; content mentions found deeper than that, or with the wrong
shape, are left untouched and reported for manual adjudication instead of being silently eaten).

Deliberately does NOT import hooks/stamp_provenance.py: CLAUDE.md's standing rule ("never modify
hooks/ ... while a live session runs") is read here as "don't couple a committed tool's behavior
to a directory this same commission is not touching" too, and hooks/ is scheduled for its own
retirement commit (the hook unwiring) at a later session boundary — this file re-derives the
tiny format spec (BEGIN/END marker text, per-extension comment lead) independently instead of
importing a module about to be deleted out from under it. The two are kept in sync by eyeball;
if they drift, `git log -p -- hooks/stamp_provenance.py` is the source of truth for the format
this script targets.

USAGE (from repo root):
    python3 tools/strip_provenance_banners.py            # do the strip, print a summary
    python3 tools/strip_provenance_banners.py --dry-run   # report only, touch nothing
    python3 tools/strip_provenance_banners.py --report    # like --dry-run but also lists every
                                                            # tracked file that CONTAINS banner-
                                                            # like text and was NOT auto-stripped
                                                            # (the manual-adjudication worklist)

Idempotent: a second run over an already-stripped tree finds zero banners and exits clean with
zero files touched — this is exercised by seen-red/strip-provenance-banners/run_fixtures.py.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Assembled from split literals ON PURPOSE, same idiom as hooks/stamp_provenance.py and
# seen-red/stamp-provenance-marker-corruption/run_fixtures.py: the contiguous marker string
# must not appear in this file's own source, or a live stamp/strip pass over THIS file could
# mistake its own definition for a banner.
_SENTINEL = "PROV" "ENANCE-STAMP"
BEGIN_MARK = f">>> {_SENTINEL} >>>"
END_MARK = f"<<< {_SENTINEL} <<<"

# Verbatim copy of hooks/stamp_provenance.py's COMMENT map (see module docstring for why this
# is a copy, not an import). A file whose extension is not here was never a stamp target, so
# banner-shaped text found in it is by construction content, not a real banner — left alone
# unconditionally, never even considered for stripping.
COMMENT = {
    ".py": "#", ".sh": "#", ".bash": "#", ".zsh": "#", ".toml": "#", ".cfg": "#",
    ".yaml": "#", ".yml": "#", ".ini": "#", ".rb": "#", ".pl": "#",
    ".js": "//", ".ts": "//", ".jsx": "//", ".tsx": "//", ".c": "//", ".h": "//",
    ".cc": "//", ".cpp": "//", ".hpp": "//", ".go": "//", ".rs": "//", ".java": "//",
}

# A real banner is inserted right after an optional shebang line and an optional coding-cookie
# line (hooks/stamp_provenance.py's `stamp()`: ins starts at 0, +1 for a shebang, +1 more for a
# coding cookie) — so index 0, 1, or 2 in the common case. A live scan of every tracked non-
# text/doc file in this repo (2026-07-22) found the begin-marker line at index <= 1 in every
# real case; this budget is set generously above that observed maximum to tolerate an odd
# leading blank line without opening the door to matching content deep in a file body — the
# structural 5-line-exact-shape requirement below is the real gate, this is just a cheap
# early-out that also serves as an explicit, checked assumption rather than an unstated one.
FIRST_LINE_BUDGET = 4

# Paths this script refuses to touch outright, independent of banner shape — see module
# docstring: hooks/ is under a standing "don't modify during a live session" rule, and its
# stamping banners are scheduled for removal in the same later commit that unwires the hook
# itself (stripping them here while the hook stays wired would just cause instant regrowth on
# next touch). This is a manual-adjudication KEEP, not a bug in the recognizer.
# 2026-07-22, session-boundary batch: the refusal above is retired -- the stamp hook was
# unwired from .claude/settings.json in this same batch and no live session runs in this
# checkout, so the regrowth rationale no longer holds; hooks/ strips like everything else.
REFUSE_PATHS_PREFIXES = ()


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True,
                          text=True, check=True)
    return [l for l in out.stdout.splitlines() if l.strip()]


def _find_banner(lines: list[str], lead: str) -> tuple[int, int] | None:
    """Structural match, identical in spirit to hooks/stamp_provenance.py's `_find_banner`:
    a candidate is a real banner only if the begin-marker line starts at column 0 (not
    embedded mid-line) AND the following three lines and the end-marker line reproduce the
    exact fixed 5-line shape at their exact relative offsets. Bounded to the first
    FIRST_LINE_BUDGET lines by the caller. Returns (begin_line, end_line) inclusive, or None.
    """
    begin_prefix = f"{lead} {BEGIN_MARK}"
    end_line = f"{lead} {END_MARK}"
    fs_prefix = f"{lead}   first-seen :"
    lc_prefix = f"{lead}   last-change:"
    co_prefix = f"{lead}   contributors:"
    for i, ln in enumerate(lines):
        if i > FIRST_LINE_BUDGET:
            break
        if not ln.startswith(begin_prefix):
            continue
        if (i + 4 < len(lines)
                and lines[i + 1].startswith(fs_prefix)
                and lines[i + 2].startswith(lc_prefix)
                and lines[i + 3].startswith(co_prefix)
                and lines[i + 4] == end_line):
            return i, i + 4
    return None


def _looks_like_damaged_banner(lines: list[str], lead: str) -> int | None:
    """A begin-marker line at column 0, within budget, immediately followed by a first-seen-
    shaped line, but that does not complete to the full valid shape `_find_banner` requires --
    plausibly a real banner damaged by hand-editing. Flagged for manual adjudication, never
    auto-stripped (mirrors the hook's own damaged-banner safety net)."""
    begin_prefix = f"{lead} {BEGIN_MARK}"
    fs_prefix = f"{lead}   first-seen :"
    for i, ln in enumerate(lines):
        if i > FIRST_LINE_BUDGET:
            break
        if ln.startswith(begin_prefix) and i + 1 < len(lines) and lines[i + 1].startswith(fs_prefix):
            return i
    return None


def _mentions_marker(text: str) -> bool:
    return _SENTINEL in text


def plan_file(rel_path: str) -> dict:
    """Classify one tracked file. Returns a dict with at least a 'status' key:
      'no-mention'      — doesn't contain the marker text at all, nothing to do.
      'stripped'        — a real banner found and (unless dry-run) removed.
      'refused-path'    — under a REFUSE_PATHS_PREFIXES root; never auto-stripped.
      'damaged'         — plausible hand-damaged real banner; manual adjudication.
      'unrecognized-ext'— contains marker text but extension has no known comment lead.
      'content'         — extension is known but no structural match within budget; almost
                           certainly a content mention (fixture/doc/log), not a real banner.
    """
    abs_path = ROOT / rel_path
    try:
        text = abs_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return {"status": "no-mention", "path": rel_path}
    if not _mentions_marker(text):
        return {"status": "no-mention", "path": rel_path}

    if rel_path.startswith(REFUSE_PATHS_PREFIXES):
        return {"status": "refused-path", "path": rel_path}

    ext = abs_path.suffix.lower()
    lead = COMMENT.get(ext)
    if lead is None:
        return {"status": "unrecognized-ext", "path": rel_path}

    lines = text.split("\n")
    found = _find_banner(lines, lead)
    if found is None:
        dmg = _looks_like_damaged_banner(lines, lead)
        if dmg is not None:
            return {"status": "damaged", "path": rel_path, "line": dmg}
        return {"status": "content", "path": rel_path}

    b0, b1 = found
    new_lines = lines[:b0] + lines[b1 + 1:]
    # At most one following blank line, only if it immediately follows the banner (the hook's
    # own insert-time pad: `stamp()` adds a single blank separator line iff the line right
    # after the insertion point was non-blank; that pad, if present, is now the first line of
    # `new_lines` at index b0). Named residual (this is a heuristic, not a certainty; see
    # module docstring / task report): if a file's ORIGINAL content (pre-stamp) happened to
    # start with its own blank line, the hook would have added no pad, and this heuristic
    # would remove that pre-existing blank instead of a hook-added one. Structurally
    # indistinguishable after the fact from tracked file content alone -- flagged here rather
    # than silently assumed away.
    removed_blank = False
    if b0 < len(new_lines) and new_lines[b0] == "":
        new_lines = new_lines[:b0] + new_lines[b0 + 1:]
        removed_blank = True

    new_text = "\n".join(new_lines)
    return {"status": "stripped", "path": rel_path, "new_text": new_text,
            "removed_blank": removed_blank}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    ap.add_argument("--report", action="store_true",
                     help="like --dry-run, plus list every non-stripped file that mentions "
                          "the marker text (the manual-adjudication worklist)")
    args = ap.parse_args()
    dry = args.dry_run or args.report

    plans = [plan_file(f) for f in tracked_files()]
    by_status: dict[str, list[dict]] = {}
    for p in plans:
        by_status.setdefault(p["status"], []).append(p)

    stripped = by_status.get("stripped", [])
    if not dry:
        for p in stripped:
            (ROOT / p["path"]).write_text(p["new_text"], encoding="utf-8")

    verb = "would strip" if dry else "stripped"
    print(f"strip_provenance_banners: {verb} {len(stripped)} real banner(s).")
    blanks = sum(1 for p in stripped if p["removed_blank"])
    print(f"  ({blanks} of those also had one following blank line removed, heuristic pad-detection)")

    for status in ("refused-path", "damaged", "unrecognized-ext"):
        items = by_status.get(status, [])
        if items:
            print(f"  {status}: {len(items)} file(s) -> manual adjudication required")
            if args.report:
                for p in items:
                    extra = f" (line {p['line']})" if "line" in p else ""
                    print(f"    - {p['path']}{extra}")

    content_items = by_status.get("content", [])
    if content_items:
        print(f"  content (mentions marker, no structural match): {len(content_items)} file(s)")
        if args.report:
            for p in content_items:
                print(f"    - {p['path']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
