#!/usr/bin/env python3
"""gates/_staged_read.py — the ONE shared staged-bytes-vs-working-tree read primitive for every
content-checking gate in hooks/pre-commit's chain (gates-staged-vs-tree-blindness, ledger row
1234). Extracted from gates/deep_walk_recursion_guard.py's own `_read_staged_bytes`/
`_read_source` (that gate's own module docstring, "READ MODE", first closed this exact class for
ONE gate on 2026-07-23) — this module is the ADR-0012 P1 "one home" for the same primitive, so
every other content-checking gate gets the same fix without N independently-authored copies.

THE DEFECT THIS CLOSES (generic across the whole chain, not particular to any one gate): a
tree-reading gate judges whatever bytes happen to sit in the working tree at gate-run time, not
the bytes the commit will actually embed (the staged/index bytes). `git commit` embeds the
INDEX, not the working tree — so `git add` a violation, then restore the clean file in the tree
WITHOUT re-staging, and a tree-reading gate passes on the clean bytes while the staged (about to
be committed) bytes still carry the violation. gates/deep_walk_recursion_guard.py's own module
docstring names this "Finding A, 2026-07-23"; the census this module answers (gates-staged-vs-
tree-blindness) found the same shape latent in every OTHER content-checking gate in the chain.

MECHANISM: `git -C <toplevel> show :<repo-relative-path>` reads the STAGED (index, stage 0) blob
for a path -- `<toplevel>` resolved fresh per call via `git -C <path.parent> rev-parse
--show-toplevel` (so this finds whichever git work tree the target actually lives in --
load-bearing for a fixture that stages its reproduction in a throwaway repo, not this one), then
the pathspec is spelled `:<path-relative-to-toplevel>` -- NOT the `:./<name>` cwd-relative
shorthand this module's own first draft used (and gates/deep_walk_recursion_guard.py's original,
pre-extraction code used before it too). Returns None (never raises) when `path`'s directory is
not inside a git work tree at all, or the path is not tracked/staged there (untracked, or a
fixture's tempfile in /tmp). `use_tree=True` forces the working-tree read unconditionally,
bypassing git entirely -- the mode manual/fixture use wants when pointing a gate at a synthetic
file that was never staged.

REAL BUG FOUND VALIDATING THIS CENSUS (a `git commit` invocation misbehaved where a direct
`python3 gates/link_integrity.py` or `sh hooks/pre-commit` run did not -- caught by actually
running `git commit` against this fix, not merely the gates' own scripts standalone; see
`GLOSSARY.md`-style note below since this is exactly the kind of hazard CLAUDE.md's engineering-
responsibility clause means): a git hook's own invocation sets `GIT_DIR` (and `GIT_INDEX_FILE`,
`GIT_PREFIX`) in the environment. A child `git -C <subdir> ...` subprocess inherits `GIT_DIR`
unless told otherwise -- and with `GIT_DIR` present in the environment, git does NOT re-discover
the repository from `-C`'s new working directory the way a freshly-invoked `git -C <subdir> ...`
does on its own: `git -C <subdir> rev-parse --show-toplevel` returned `<subdir>` ITSELF as the
toplevel (silently wrong, no error) instead of the actual worktree root, and the original
`:./<name>` cwd-relative pathspec form resolved against the wrong base the same way -- so every
subdirectory file's "staged" read silently returned a DIFFERENT file's blob (the repo root's
same-named file, in the reproduction that caught this) whenever this ran as a live pre-commit
hook, though it read correctly from a direct script invocation with no inherited `GIT_DIR`.

THE FIX: `_subprocess_env()` below strips `GIT_DIR`/`GIT_WORK_TREE`/`GIT_PREFIX`/
`GIT_COMMON_DIR` from the environment passed to every subprocess this module spawns, forcing
fresh, correct repository autodiscovery from `-C`'s own directory every time -- the exact
standalone behavior already verified correct. `GIT_INDEX_FILE` is deliberately LEFT to inherit
unmolested (never stripped): a temp-index commit (staging_guard.py's own documented house
pattern) needs this primitive to read the SAME temp index that will become HEAD, exactly as
`git diff --cached` already does for that workflow, and `GIT_INDEX_FILE` is independent of the
`GIT_DIR`-vs-`-C` confusion above -- git honors it regardless of how the repository itself was
discovered. The pathspec itself is ALSO spelled `:<repo-relative-path>` (no leading `./`), a
belt-and-suspenders choice: unambiguous even if some other git build's environment-stripping
edge case reintroduces prefix sensitivity this fixture's own reproduction did not happen to
exercise.

Every function here is a pure I/O primitive — no gate-specific policy, no violation logic. Each
gate keeps its own AST/regex/JSON checks; only WHERE THE BYTES COME FROM moves here.

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

# Stripped from every subprocess env this module spawns (see module docstring's REAL BUG FOUND
# VALIDATING THIS CENSUS): these four make `-C <dir>` stop re-discovering the repository from
# `<dir>` when inherited from an enclosing git process (a live pre-commit hook). GIT_INDEX_FILE
# is deliberately NOT in this set -- a temp-index commit needs it honored, see the docstring.
_STRIP_GIT_ENV = ("GIT_DIR", "GIT_WORK_TREE", "GIT_PREFIX", "GIT_COMMON_DIR")


def _subprocess_env() -> dict[str, str]:
    """A copy of the current environment with `_STRIP_GIT_ENV` removed -- passed to every git
    subprocess this module spawns so `-C` governs repository discovery unambiguously, regardless
    of what an enclosing git hook invocation left in the environment."""
    return {k: v for k, v in os.environ.items() if k not in _STRIP_GIT_ENV}


def read_staged_bytes(path: Path) -> bytes | None:
    """The STAGED content of `path` (git's index, stage 0) as raw bytes — the bytes the next
    commit will actually embed, regardless of whatever the working tree currently holds. Returns
    None (never raises) when `path`'s directory is not inside a git work tree, the path is not
    tracked/staged there, or (defensively) its resolved path is not actually beneath the
    worktree's own reported top-level — callers fall back to the working-tree file in those
    cases. (If `git` itself is absent from PATH, subprocess.run raises FileNotFoundError and the
    caller crashes loudly — unreachable in the pre-commit context, which only ever runs under
    git.)

    See the module docstring's WHY NOT `:./<name>` section: this resolves the worktree's own
    top-level fresh (via `-C path.parent`, so it finds whichever repo the target actually lives
    in) and spells the pathspec relative to THAT root (`:<rel>`, no leading `./`) rather than the
    cwd/GIT_PREFIX-sensitive `:./<name>` shorthand — a real, git-build-specific misresolution
    only observable when this runs as an actual git hook (GIT_PREFIX inherited from the
    invoking `git commit`), not from a direct script run."""
    env = _subprocess_env()
    top = subprocess.run(
        ["git", "-C", str(path.parent), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, env=env,
    )
    if top.returncode != 0:
        return None
    try:
        toplevel = Path(top.stdout.strip()).resolve()
        rel = path.resolve().relative_to(toplevel)
    except (ValueError, OSError):
        return None
    result = subprocess.run(
        ["git", "-C", str(toplevel), "show", f":{rel.as_posix()}"],
        capture_output=True, env=env,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def read_staged_text(path: Path, encoding: str = "utf-8") -> str | None:
    """`read_staged_bytes` decoded as text, or None under the same conditions (not staged, not
    in a git work tree, OR the staged blob is not valid `encoding` — a malformed-encoding staged
    blob is not this primitive's problem to solve; the caller's own tree-fallback handles it the
    same as "not staged")."""
    raw = read_staged_bytes(path)
    if raw is None:
        return None
    try:
        return raw.decode(encoding)
    except UnicodeDecodeError:
        return None


def read_source_text(path: Path, use_tree: bool = False, encoding: str = "utf-8") -> str:
    """The source text a gate should judge. By default, the STAGED bytes (falling back to the
    working-tree file only when the path is not staged at all). `use_tree=True` forces the
    working-tree read unconditionally, bypassing git entirely."""
    if not use_tree:
        staged = read_staged_text(path, encoding=encoding)
        if staged is not None:
            return staged
    return path.read_text(encoding=encoding)


def read_source_bytes(path: Path, use_tree: bool = False) -> bytes:
    """`read_source_text`'s raw-bytes twin — for a gate that needs to hash or otherwise judge
    exact bytes (gates/doc_attestation_presence.py's content_sha256) rather than decoded text."""
    if not use_tree:
        staged = read_staged_bytes(path)
        if staged is not None:
            return staged
    return path.read_bytes()
