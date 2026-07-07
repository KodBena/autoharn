#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-07T03:28:16Z
#   last-change: 2026-07-07T10:11:17Z
#   contributors: 37017f46/main
# <<< PROVENANCE-STAMP <<<

"""staging_guard — the explicit-paths commit guard (forecloses finding 33, the commit-scope-sweep /
git-add-sweep class: `git commit` commits the whole INDEX, not just the paths the committer added this
turn, so a path staged earlier, concurrently, or by a broad `git add` rides along — attribution muddling
(commit 420e5bf swept a concurrently-authored BACKLOG.md entry; c3d7b00 swept consult-21 + a deletion)
and inclusion of unrelated/unready material). ADR-0000 never-again for the class.

CLOSURE STATEMENT (ADR-0000 Rule 2a):
  - INVARIANT: every path in a commit's staged index is one the committing actor DECLARED it intends
    this commit; no path rides along undeclared.
  - QUANTIFICATION UNIVERSE — axes of the ingress (how an undeclared path reaches the index): (1) a broad
    `git add -A`/`.`/`<dir>` sweep; (2) a path staged earlier in the session and never unstaged, that a
    later bare `git commit` sweeps (420e5bf's BACKLOG.md); (3) a concurrently-authored change to a shared
    file staged wholesale. Sibling surfaces: BOTH repos committed by the agent (claude_harness +
    epistemic-operator) — the guard is invoked from each repo's pre-commit hook, reads that repo's index.
    AXIS NAMED-NOT-FULLY-MECHANIZED: attribution-muddle WITHIN a declared shared file (a hunk by another
    actor inside a file the committer legitimately declares) is not caught by the set match — a staged
    shared-surface file is FLAGGED for hunk inspection (ADR-0013 Rule 5), the rest is the brief's
    `git add -p` discipline (review-only, declared here, not silently omitted).
  - DENOMINATION: the guard is denominated in "staged index paths the committer did not declare" — the
    exact resource of the class — never a proxy (not file count, not a junk-name denylist).

MECHANISM. The committer DECLARES its intended paths via `CLAUDE_COMMIT_PATHS` (whitespace/newline
separated, repo-relative — exactly the paths passed to `git add`). The guard asserts the staged index
set == the declared set; any undeclared staged path REFUSES the commit (listed), any declared-but-unstaged
path REFUSES (listed — an add that silently failed or a typo). Fail-safe strict: a commit with NO declared
manifest is REFUSED unless `STAGING_GUARD_SKIP=1` (the documented human-interactive opt-out) is set.

A declared entry ending in `/` is a DIRECTORY PREFIX (maintainer rider 2026-07-07): it covers any staged
path beneath it — a legitimate bulk case (a whole-dir ephemera/packet snapshot) declared INDEPENDENTLY
(the prefix is chosen before staging), never generated from the index. A prefix need not match anything;
exact-file entries still must be staged. A path outside every declared prefix and exact entry is still a
swept path and still REFUSED.

Registered close/lint line id: `staging-guard`. Lazy imports banned.
"""
from __future__ import annotations

import os
import subprocess
import sys

# shared surfaces where a concurrent-actor hunk is most likely to ride inside a legitimately-declared
# file (the named-not-fully-mechanized axis) — flagged loud for hunk inspection, never silently passed.
_SHARED_SURFACES = ("BACKLOG.md", "MEMORY.md", "consults/", "docs/adr/", "docs/work-units/")


def _staged_paths() -> set[str]:
    """The repo-relative paths in the staged index (added/copied/modified/renamed/deleted)."""
    cp = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRD"],
                        capture_output=True, text=True)
    return {ln.strip() for ln in cp.stdout.splitlines() if ln.strip()}


def _declared_paths(raw: str) -> set[str]:
    """The committer's declared intent, normalized: split on whitespace/newlines, repo-relative."""
    return {tok.strip() for tok in raw.replace("\n", " ").split(" ") if tok.strip()}


def main(argv: list[str] | None = None) -> int:
    staged = _staged_paths()
    if not staged:
        return 0  # nothing staged — an empty commit is git's own problem, not the sweep class
    raw = os.environ.get("CLAUDE_COMMIT_PATHS", "").strip()
    if not raw:
        if os.environ.get("STAGING_GUARD_SKIP") == "1":
            return 0  # documented human-interactive opt-out
        print("STAGING GUARD: commit REFUSED — no CLAUDE_COMMIT_PATHS manifest declared (finding 33).", file=sys.stderr)
        print("  A bare `git commit` commits the whole index; declare exactly what THIS commit owns.", file=sys.stderr)
        print(f"  Staged now ({len(staged)}): {sorted(staged)}", file=sys.stderr)
        print("  Agents: export CLAUDE_COMMIT_PATHS='<the paths you git add-ed>' before committing.", file=sys.stderr)
        print("  Humans committing interactively: export STAGING_GUARD_SKIP=1 (once, in your shell rc).", file=sys.stderr)
        return 1
    declared = _declared_paths(raw)
    # A declared entry ending in '/' is a DIRECTORY PREFIX (maintainer rider 2026-07-07): it covers any
    # staged path beneath it — a legitimate bulk case (a whole-dir ephemera/packet snapshot) declared
    # INDEPENDENTLY (the prefix is chosen before staging), never generated from the index (which would
    # make the manifest rubber-stamp whatever is staged). A prefix need not match anything (declaring a
    # dir that turns out empty is not an error); exact-file entries still must be staged.
    prefixes = {d for d in declared if d.endswith("/")}
    exact = declared - prefixes
    undeclared = sorted(p for p in staged
                        if p not in exact and not any(p.startswith(pre) for pre in prefixes))
    unstaged = sorted(exact - staged)        # a declared FILE that is absent — a failed add or a typo
    if undeclared or unstaged:
        print("STAGING GUARD: commit REFUSED — staged index does not match the declared manifest "
              "(finding 33: a swept path would ride along).", file=sys.stderr)
        if undeclared:
            print(f"  SWEPT (staged, NOT declared — unstage or declare): {undeclared}", file=sys.stderr)
        if unstaged:
            print(f"  MISSING (declared, NOT staged — a failed `git add` or a typo): {unstaged}", file=sys.stderr)
        return 1
    shared = sorted(p for p in staged if any(p == s or p.startswith(s) for s in _SHARED_SURFACES))
    if shared:
        print(f"STAGING GUARD: OK — staged set matches the manifest. NOTE shared-surface file(s) staged; "
              f"confirm every hunk is yours (ADR-0013 Rule 5): {shared}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
