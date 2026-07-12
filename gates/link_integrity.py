#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T14:37:38Z
#   last-change: 2026-07-12T01:25:43Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""link_integrity — the class-not-instance fix for the maintainer's 2026-07-11 legibility
indictment ("you shouldn't have to navigate the doc graph like a squirrel"). Three dangling/
mis-cited paths were found and hand-fixed the same morning (commit 48dce0c); this gate is the
CLASS: every relative markdown link `[text](target)` in every tracked `*.md` file must resolve
to a file (or directory) that actually exists on disk. A doc that tells a reader to click
somewhere that 404s is the exact hazard the indictment named.

CLOSURE STATEMENT (ADR-0000 Rule 2a):
  - INVARIANT: every relative-path markdown link target in scope, once its `#anchor` suffix is
    stripped, resolves (via `os.path.exists`) relative to the linking file's own directory.
  - QUANTIFICATION UNIVERSE: every `[text](target)` occurrence (link syntax only — this repo's
    corpus carries no `![image]`, no reference-style `[text]: url` definitions, checked at
    authoring time; a corpus that grows either shape should extend TOKEN accordingly, named
    here rather than silently uncovered) in every git-TRACKED `*.md` file, minus the two
    principled exclusions below.
  - DENOMINATION: the resource is "a link target path", not a proxy (not link count, not doc
    count) — one violation per unresolvable target, every occurrence reported.

SCOPE. Every tracked `*.md` (`git ls-files '*.md'`), same universe doc-legibility.py settled on
(maintainer ruling 2026-07-07, finding 48) — "the gate ought to apply to any documentation a
human might read." Two EXCLUSIONS, both principled and both printed in every run's output
(never silent, per the commission):

  1. judgment/**  — ORCH-OPERATING-CARD.md's own words: "predecessor era — history unless a current
     spec cites it." A declared-history archive is not held to a live-link bar; if a current
     spec ever cites into it, that citing document (not the archived one) carries the live link.
  2. design/ORCH-ARCHITECTURE.md (renamed from design/ARCHITECTURE.md by the doc-audience-taxonomy
     sweep, 2026-07-12 — the exclusion follows the file) — carries its own `⚠ STALE (2026-06-27;
     migrated 2026-07-07, not rewritten)` banner: "Its internal path citations ... point at the OLD
     `claude_harness` layout, not autoharn's tree ... carried as a design witness, not authority; a
     full rewrite ... is owed and filed in BACKLOG.md." Patching its paths piecemeal without the
     rewrite the banner itself calls for would manufacture false current-ness — worse than leaving
     the banner's own honest disclaimer standing. Excluded until that filed rewrite lands.

ANCHORS (`#fragment` after a resolving path): v1 does not verify the fragment resolves to a real
heading/anchor in the target — flagged in a separate, NON-BLOCKING report section, never failing
the gate on a bad anchor alone (declared residue, not a silent gap).

Exit 0 clean (broken-path violations only); exit 1 listing every one. Run from repo root:
  python3 gates/link_integrity.py
Lazy imports banned.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Exclusion 1: a whole directory, declared history (ORCH-OPERATING-CARD.md, "The deep history" section).
EXCLUDE_DIR_PREFIXES = ("judgment/",)
# Exclusion 2: a single file, self-declared STALE with its rewrite filed separately (BACKLOG.md).
# Renamed design/ARCHITECTURE.md -> design/ORCH-ARCHITECTURE.md by the doc-audience-taxonomy
# sweep (tracker item doc-audience-taxonomy, 2026-07-12); the exclusion follows the file, not
# the old name -- the STALE banner and its still-owed rewrite are unaffected by the rename.
EXCLUDE_FILES = {"design/ORCH-ARCHITECTURE.md"}

LINK = re.compile(r'(?<!!)\[[^\]]*\]\(([^)]+)\)')
_SCHEMES = {"http", "https", "mailto", "ftp", "ftps", "tel"}


def tracked_md() -> list[str]:
    """Every git-tracked *.md, repo-relative — the same universe doc-legibility.py settled on."""
    r = subprocess.run(["git", "-C", ROOT, "ls-files", "*.md"],
                        capture_output=True, text=True, check=True)
    return [ln for ln in r.stdout.splitlines() if ln.strip()]


def in_scope(rel: str) -> bool:
    if rel in EXCLUDE_FILES:
        return False
    return not any(rel.startswith(p) for p in EXCLUDE_DIR_PREFIXES)


def strip_fences(text: str) -> str:
    """Blank out fenced code-block bodies (``` or ~~~) so a link-shaped code example is never
    mistaken for a real link — same device doc-legibility.py uses."""
    out = []
    fence = False
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith('```') or line.lstrip().startswith('~~~'):
            fence = not fence
            out.append(line)
            continue
        out.append('\n' if fence else line)
    return ''.join(out)


def strip_inline_code(line: str) -> str:
    """Drop the contents of inline `code` spans (a link-shaped example inside backticks is
    prose, not a real link) while keeping the rest of the line intact for the LINK regex."""
    parts = line.split('`')
    return ''.join(p if i % 2 == 0 else '' for i, p in enumerate(parts))


def classify_target(raw: str) -> tuple[str, str] | None:
    """Split a raw link target into (path_part, anchor) after dropping a markdown title
    (`target "title"`) and `<...>` wrapping. Returns None for out-of-scope targets: external
    URLs/mailto, and pure same-file `#anchor` links (no path to resolve)."""
    target = raw.strip().split(' ', 1)[0].strip('<>')
    if not target:
        return None
    if urlsplit(target).scheme in _SCHEMES:
        return None
    if target.startswith('#'):
        return None  # same-file anchor — no path component to resolve
    path_part, _, anchor = target.partition('#')
    path_part = unquote(path_part)
    if not path_part:
        return None
    return path_part, anchor


def resolve(doc_path: str, path_part: str) -> str:
    """Resolve a link's path part relative to its own file's directory (root-relative if it
    starts with '/' — none in the corpus today, but a link authored that way means the repo
    root, not the filesystem root)."""
    if path_part.startswith('/'):
        return os.path.normpath(os.path.join(ROOT, path_part.lstrip('/')))
    return os.path.normpath(os.path.join(os.path.dirname(doc_path), path_part))


def iter_raw_line_links(text: str):
    """Yield (line_no, match) for every LINK-regex match in `text`, one parser shared by this
    gate and any other consumer that needs to find/rewrite real markdown links (tools/rename_doc.py
    is the second consumer this was extracted for — CLAUDE.md ADR-0012 P1, one home for the link
    grammar). Scans fence-stripped lines (a link-shaped example inside a code fence is never a
    real link — same exclusion the gate applies) but, unlike the gate's own scan-line construction
    (`strip_inline_code`, which DELETES backtick-wrapped content and so shifts offsets), this
    function skips an inline-code match by a parity check on the UNMODIFIED line instead of
    deleting anything — so a caller gets match objects whose `.start()`/`.end()` are valid offsets
    into the exact line text it can slice and rewrite. This is purely an ADDITIVE helper: the gate's
    own `main()` below is untouched byte-for-byte, so its output stays byte-equivalent."""
    stripped_text = strip_fences(text)
    for ln, line in enumerate(stripped_text.splitlines(), 1):
        for m in LINK.finditer(line):
            prefix = line[:m.start()]
            if prefix.count('`') % 2 == 1:
                continue  # match starts inside an inline `code` span — a quoted example, not a link
            yield ln, m


def main() -> int:
    all_tracked = tracked_md()
    scope = [f for f in all_tracked if in_scope(f)]
    excluded = [f for f in all_tracked if not in_scope(f)]

    broken: list[tuple[str, int, str]] = []      # (rel, line, target)
    anchor_flags: list[tuple[str, int, str]] = []  # (rel, line, target) — informational only
    total_links = 0

    for rel in scope:
        path = os.path.join(ROOT, rel)
        text = strip_fences(open(path, encoding='utf-8').read())
        for ln, line in enumerate(text.splitlines(), 1):
            scan = strip_inline_code(line)
            for m in LINK.finditer(scan):
                classified = classify_target(m.group(1))
                if classified is None:
                    continue
                total_links += 1
                path_part, anchor = classified
                resolved = resolve(path, path_part)
                if not os.path.exists(resolved):
                    broken.append((rel, ln, m.group(1)))
                elif anchor and os.path.isfile(resolved) and resolved.endswith('.md'):
                    anchor_flags.append((rel, ln, m.group(1)))

    print(f"link-integrity: {len(scope)} docs in scope ({len(all_tracked)} tracked *.md, "
          f"{len(excluded)} excluded), {total_links} relative link(s) checked.")
    print(f"  excluded (principled, see gates/link_integrity.py docstring):")
    print(f"    judgment/**            — declared history (ORCH-OPERATING-CARD.md)")
    print(f"    design/ORCH-ARCHITECTURE.md — self-declared STALE; rewrite filed in BACKLOG.md")

    if anchor_flags:
        print(f"\n  {len(anchor_flags)} link(s) with an unchecked #anchor (v1 does not verify "
              f"fragments — NOT a failure):")
        for rel, ln, target in anchor_flags[:10]:
            print(f"    {rel}:{ln}  {target}")
        if len(anchor_flags) > 10:
            print(f"    ... +{len(anchor_flags) - 10} more")

    if broken:
        print(f"\nlink-integrity: {len(broken)} broken link(s) — target does not exist on disk:\n")
        for rel, ln, target in broken:
            print(f"  !! {rel}:{ln}  {target}")
        return 1

    print(f"\nlink-integrity: clean ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
