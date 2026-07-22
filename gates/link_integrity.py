#!/usr/bin/env python3
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

  1. judgment/**  — user-guide/ORCH-OPERATING-CARD.md's own words: "predecessor era — history unless a current
     spec cites it." A declared-history archive is not held to a live-link bar; if a current
     spec ever cites into it, that citing document (not the archived one) carries the live link.
  2. vestigial_documentation/design/ORCH-ARCHITECTURE.md (renamed from design/ARCHITECTURE.md by
     the doc-audience-taxonomy sweep, 2026-07-12; moved again to vestigial_documentation/design/
     by the vestigial-doc-sweep, 2026-07-12 — the exclusion follows the file through both moves)
     — carries its own `⚠ STALE (2026-06-27; migrated 2026-07-07, not rewritten)` banner: "Its
     internal path citations ... point at the OLD `claude_harness` layout, not autoharn's tree
     ... carried as a design witness, not authority; a full rewrite ... is owed and filed in
     BACKLOG.md." Patching its paths piecemeal without the rewrite the banner itself calls for
     would manufacture false current-ness — worse than leaving the banner's own honest disclaimer
     standing. Excluded until that filed rewrite lands (see VESTIGIAL-INDEX.md for the file's
     current entry and provenance).

ANCHORS (`#fragment` after a resolving path): v1 does not verify the fragment resolves to a real
heading/anchor in the target — flagged in a separate, NON-BLOCKING report section, never failing
the gate on a bad anchor alone (declared residue, not a silent gap).

GITIGNORED-LOCAL TARGETS (found authoring kernel/lineage/s44-model-identity-attestation.sql,
2026-07-18): a link resolving under `/local/` (`.gitignore`'s own words: "operator-local notes
... never tracked") is unverifiable from `os.path.exists` on ANY checkout that has not locally
installed whatever `local/` records (e.g. `local/OTEL-COLLECTOR.md`, cited by
ORCH-CAPABILITIES.md, exists only on a host that has actually installed the OTel collector) --
this is NOT the class this gate exists to catch (a doc pointing somewhere that can never exist,
the maintainer's 2026-07-11 indictment), it is a doc pointing at *evidence the operator's own
convention deliberately keeps out of git*. Flagged in the SAME NON-BLOCKING report section as
anchors (never counted toward `broken`, never silently dropped either) -- a target under
`local/` that happens to ALSO be missing on a host that HAS installed the referenced tooling
would still need a human's eyes (this gate cannot distinguish "not installed yet" from "typo'd
the filename" for an untracked path), so the honest move is informational, not silent
exclusion.

UNINITIALIZED SUBMODULES (found reproducing work_opened `worktree-submodule-link-integrity`,
2026-07-19): a fresh `git worktree add` does NOT populate this repo's gitlink submodules
(`tools/makespan-scheduler`, `tools/autoharn-panel`) -- the directory exists (git creates the
placeholder) but is empty, a VALID git state, not a defect in the branch. A link resolving to a
path *inside* an unpopulated submodule (e.g. `tools/makespan-scheduler/README.md`) genuinely
cannot be verified in that state -- this gate's contract (does the target resolve on disk) has
no way to distinguish "not populated yet" from "typo'd the filename" for content the checkout
does not have. Per law/adr/0012 P1 (derive a fact from its one authoritative source, never a
disk-shape heuristic): submodule-populated-or-not is authoritatively `git submodule status`
(a `-`-prefixed line names an uninitialized path), queried once via `uninitialized_submodules()`
below -- NOT inferred from directory emptiness. Unlike `/local/` (permanently, deliberately
untracked by convention -- informational forever), a submodule is SUPPOSED to be populated in a
normal working checkout; this is a fixable, transient gap, so the honest move is to REFUSE with
one teaching line (how to populate), not to silently downgrade to informational-only and let a
real future typo inside the submodule slip past unverified. A link into an uninitialized
submodule is therefore reported in its OWN section (never merged into the `broken` wall, never
silently dropped) and, if any such link exists, the gate exits 1 with ONE teaching block --
never a per-link wall of false errors. Once the submodule is populated, `git submodule status`
drops the `-` prefix and a genuinely broken link inside it is caught by the normal `broken` path
exactly as before.

Exit 0 clean (broken-path violations only, none into an uninitialized submodule); exit 1 listing
every broken link and/or the single uninitialized-submodule teaching block. Default target is THIS
checkout (autoharn) regardless of caller's cwd -- ROOT is derived from this file's own location,
not os.getcwd(), so running the script from inside a different repo does NOT check that repo's
docs (a real, dated gap: an adopting project running this script unmodified got a false "clean"
verdict for autoharn's own docs while its own docs went unchecked -- AUTOHARN_BACKFLOW.md,
autoharn-panel deployment, 2026-07-16). Pass --repo to check a different tree instead:
  python3 gates/link_integrity.py                    # scans THIS checkout (autoharn)
  python3 gates/link_integrity.py --repo /path/to/other/project   # scans that tree instead
Lazy imports banned.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

DEFAULT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _resolve_root(argv: list[str]) -> str:
    """--repo PATH overrides the default self-check root; omitting it preserves the exact prior
    behavior (scan this checkout) for every existing caller."""
    if "--repo" in argv:
        i = argv.index("--repo")
        if i + 1 >= len(argv):
            print("link-integrity: --repo requires a PATH argument", file=sys.stderr)
            sys.exit(2)
        return os.path.abspath(argv[i + 1])
    return DEFAULT_ROOT


ROOT = _resolve_root(sys.argv[1:])

# Exclusion 1: a whole directory, declared history (user-guide/ORCH-OPERATING-CARD.md, "The deep history" section).
EXCLUDE_DIR_PREFIXES = ("judgment/",)
# Exclusion 2: a single file, self-declared STALE with its rewrite filed separately (BACKLOG.md).
# Renamed design/ARCHITECTURE.md -> design/ORCH-ARCHITECTURE.md by the doc-audience-taxonomy
# sweep (tracker item doc-audience-taxonomy, 2026-07-12), then moved again to
# vestigial_documentation/design/ORCH-ARCHITECTURE.md by the vestigial-doc-sweep (2026-07-12,
# work_slug vestigial-doc-sweep) -- the exclusion follows the file, not the path, through both
# moves -- the STALE banner and its still-owed rewrite are unaffected by either rename.
EXCLUDE_FILES = {"vestigial_documentation/design/ORCH-ARCHITECTURE.md"}

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


def uninitialized_submodules() -> set[str]:
    """Repo-relative paths of every registered submodule not yet populated. `git submodule
    status` is the ONE authoritative source for this fact (ADR-0012 P1: derive-don't-duplicate
    — never infer "populated?" from directory emptiness, a disk-shape heuristic with no
    connection to git's own bookkeeping): a `-`-prefixed status line names an uninitialized
    submodule; ` `/`+` mean populated (clean/dirty). Returns an empty set (nothing to flag) for
    a repo with no `.gitmodules` at all — `git submodule status` then exits nonzero or prints
    nothing, either way there is no gitlink to reason about."""
    r = subprocess.run(["git", "-C", ROOT, "submodule", "status"],
                        capture_output=True, text=True)
    if r.returncode != 0:
        return set()
    paths = set()
    for line in r.stdout.splitlines():
        if line.startswith('-'):
            parts = line[1:].split()
            if len(parts) >= 2:
                paths.add(parts[1])
    return paths


def under_submodule(rel_to_root: str, submodule_paths: set[str]) -> str | None:
    """Return the submodule path that `rel_to_root` resolves inside (itself or a descendant),
    or None. `os.path.relpath`-normalized paths only (no trailing slash), so the containment
    check is a prefix-plus-separator match."""
    for sm in submodule_paths:
        if rel_to_root == sm or rel_to_root.startswith(sm + os.sep):
            return sm
    return None


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
    uninit_submodules = uninitialized_submodules()

    broken: list[tuple[str, int, str]] = []      # (rel, line, target)
    anchor_flags: list[tuple[str, int, str]] = []  # (rel, line, target) — informational only
    local_flags: list[tuple[str, int, str]] = []   # (rel, line, target) — gitignored /local/, informational only
    submodule_flags: list[tuple[str, int, str, str]] = []  # (rel, line, target, submodule_path) — refuses, teaches
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
                    rel_to_root = os.path.relpath(resolved, ROOT)
                    sm = under_submodule(rel_to_root, uninit_submodules)
                    if rel_to_root == "local" or rel_to_root.startswith("local" + os.sep):
                        local_flags.append((rel, ln, m.group(1)))
                    elif sm is not None:
                        submodule_flags.append((rel, ln, m.group(1), sm))
                    else:
                        broken.append((rel, ln, m.group(1)))
                elif anchor and os.path.isfile(resolved) and resolved.endswith('.md'):
                    anchor_flags.append((rel, ln, m.group(1)))

    print(f"link-integrity: {len(scope)} docs in scope ({len(all_tracked)} tracked *.md, "
          f"{len(excluded)} excluded), {total_links} relative link(s) checked.")
    print(f"  excluded (principled, see gates/link_integrity.py docstring):")
    print(f"    judgment/**            — declared history (user-guide/ORCH-OPERATING-CARD.md)")
    print(f"    vestigial_documentation/design/ORCH-ARCHITECTURE.md — self-declared STALE; "
          f"rewrite filed in BACKLOG.md")

    if anchor_flags:
        print(f"\n  {len(anchor_flags)} link(s) with an unchecked #anchor (v1 does not verify "
              f"fragments — NOT a failure):")
        for rel, ln, target in anchor_flags[:10]:
            print(f"    {rel}:{ln}  {target}")
        if len(anchor_flags) > 10:
            print(f"    ... +{len(anchor_flags) - 10} more")

    if local_flags:
        print(f"\n  {len(local_flags)} link(s) into /local/ (gitignored operator evidence, "
              f"never tracked -- NOT a failure; a host that has not locally installed the "
              f"referenced tooling will not have the target, by the project's own convention):")
        for rel, ln, target in local_flags[:10]:
            print(f"    {rel}:{ln}  {target}")
        if len(local_flags) > 10:
            print(f"    ... +{len(local_flags) - 10} more")

    if submodule_flags:
        submods = sorted({sm for _, _, _, sm in submodule_flags})
        print(f"\nlink-integrity: {len(submodule_flags)} link(s) point into uninitialized "
              f"submodule(s) {', '.join(submods)} -- this checkout has the gitlink but not its "
              f"content (a fresh `git worktree add` does not populate submodules), so these "
              f"targets cannot be verified. Populate and re-run:\n"
              f"    git submodule update --init --recursive")

    if broken:
        print(f"\nlink-integrity: {len(broken)} broken link(s) — target does not exist on disk:\n")
        for rel, ln, target in broken:
            print(f"  !! {rel}:{ln}  {target}")
        return 1

    if submodule_flags:
        return 1

    print(f"\nlink-integrity: clean ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
