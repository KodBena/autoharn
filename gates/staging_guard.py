#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-07T03:28:16Z
#   last-change: 2026-07-15T12:48:20Z
#   contributors: 37017f46/main, a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""staging_guard — the explicit-paths commit guard (forecloses finding 33, the commit-scope-sweep /
git-add-sweep class: `git commit` commits the whole INDEX, not just the paths the committer added this
turn, so a path staged earlier, concurrently, or by a broad `git add` rides along — attribution muddling
(commit 420e5bf swept a concurrently-authored BACKLOG.md entry; c3d7b00 swept consult-21 + a deletion)
and inclusion of unrelated/unready material). ADR-0000 never-again for the class.

STAGING-SCOPE-SUBSET-ENFORCEMENT (ledger item `staging-scope-subset-enforcement`, motivating class
c4923ae): c4923ae's declared CLAUDE_COMMIT_PATHS was a narrow "commission-680 decomposition manifest"
scope, but its staged index carried 46 files — deletions of live seen-red fixtures, a reverted
deployment.json .gitignore rule (a privacy hazard), reverted kernel/lineage detect.sql fixes — none of
it declared. The set-equality check below already existed at that time and still REFUSED the class in
the ordinary case; the debacle happened because the declared manifest itself was generated FROM the
already-broadly-staged index (a self-certifying declaration — "declare whatever is staged" defeats any
set check by construction). This module cannot see a scope any more independent than what
CLAUDE_COMMIT_PATHS asserts — closing THAT gap is `item-bracketed-work-discipline`'s job (the claim-time
scope becomes the one independently-authored source the guard would check against, ADR-0012 P1). What
this hardening DOES own: make "staged not subset-of-declared" unrepresentable as a passing commit under
every real commit flow this repo uses, with no silent bypass.

CLOSURE STATEMENT (ADR-0000 Rule 2a):
  - INVARIANT: the staged index set of any commit is a SUBSET of the committing actor's declared scope;
    no path rides along undeclared. (The guard additionally checks the converse — every declared exact
    file IS staged — as a typo/failed-add tripwire; that check is a stricter *addition*, never a
    relaxation of the subset invariant.)
  - QUANTIFICATION UNIVERSE — axes of the ingress (how an undeclared path reaches the index): (1) a broad
    `git add -A`/`.`/`<dir>` sweep; (2) a path staged earlier in the session and never unstaged, that a
    later bare `git commit` sweeps (420e5bf's BACKLOG.md); (3) a concurrently-authored change to a shared
    file staged wholesale; (4) a self-certifying declaration that enumerates the sweep instead of the
    actor's true intent (c4923ae — undetectable by this module alone, named above, not silently ignored).
    Sibling surfaces: BOTH repos committed by the agent (claude_harness + epistemic-operator) — the guard
    is invoked from each repo's pre-commit hook, reads that repo's index. AXIS NAMED-NOT-FULLY-MECHANIZED:
    attribution-muddle WITHIN a declared shared file (a hunk by another actor inside a file the committer
    legitimately declares) is not caught by the set match — a staged shared-surface file is FLAGGED for
    hunk inspection (ADR-0013 Rule 5), the rest is the brief's `git add -p` discipline (review-only,
    declared here, not silently omitted).
  - DENOMINATION: the guard is denominated in "staged index paths the committer did not declare" — the
    exact resource of the class — never a proxy (not file count, not a junk-name denylist).
  - THREE NAMED ESCAPE HATCHES, none silent (every one prints what it is doing, to stderr, every time):
      1. TEMP-INDEX COMMITS (the house pattern: CLAUDE_COMMIT_PATHS + GIT_INDEX_FILE read-tree HEAD).
         No special-case needed — `git diff --cached` below reads whichever index GIT_INDEX_FILE names
         (subprocess inherits the caller's environment unmodified), so the declared-vs-staged check
         already operates on the temp index transparently.
      2. MERGE COMMITS legitimately sweep the whole merged diff against HEAD by construction — that is
         not the finding-33 class (nobody's `git add -A` chose those paths; git's own merge machinery
         did). Detected via `MERGE_HEAD` (git rev-parse -q --verify MERGE_HEAD in the invoking repo);
         when present the check is skipped, loudly, unconditionally (no manifest needed).
      3. THE MAINTAINER'S OWN HANDS: `CLAUDE_COMMIT_ALL=maintainer` (exact value, not merely truthy —
         this is a deliberate, visible acknowledgment, never an accidental blanket bypass) sweeps the
         whole staged index as approved. This is distinct from `STAGING_GUARD_SKIP=1` (below): SKIP only
         ever applied to the "no manifest declared at all" branch; ALL applies even with a declared-but-
         insufficient manifest, and unlike SKIP it is loud about exactly what rode along.

MECHANISM. The committer DECLARES its intended paths via `CLAUDE_COMMIT_PATHS` (whitespace/newline
separated, repo-relative — exactly the paths passed to `git add`). The guard asserts the staged index
set is a SUBSET of the declared set (any undeclared staged path REFUSES the commit, listed, naming this
item + c4923ae) and, as an added tripwire, that every declared exact file IS staged (any declared-but-
unstaged path REFUSES, listed — an add that silently failed or a typo). Fail-safe strict: a commit with
NO declared manifest is REFUSED unless `STAGING_GUARD_SKIP=1` (the documented human-interactive opt-out)
is set.

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


def _merge_in_progress() -> bool:
    """True iff a `git merge` is mid-flight in the invoking repo (MERGE_HEAD exists) — a merge commit
    legitimately sweeps the whole merged diff against HEAD; that is git's own machinery, not a
    finding-33 `git add -A` sweep, so it is exempted (escape hatch 2, see module docstring)."""
    cp = subprocess.run(["git", "rev-parse", "-q", "--verify", "MERGE_HEAD"],
                        capture_output=True, text=True)
    return cp.returncode == 0


def _blob_hash(rev: str | None, path: str) -> str | None:
    """git's own object hash for `path` as of `rev` (e.g. "HEAD", "MERGE_HEAD"), or, when `rev` is
    None, the STAGED (index) blob for `path` (git's own `:path` index-stage-0 syntax) — None if the
    path does not exist there."""
    spec = f"{rev}:{path}" if rev is not None else f":{path}"
    cp = subprocess.run(["git", "rev-parse", "-q", "--verify", spec],
                        capture_output=True, text=True)
    return cp.stdout.strip() if cp.returncode == 0 else None


def _merge_diff_paths() -> set[str] | None:
    """The honest changed-file set of the in-progress merge (night-build-defect-repair, verifier
    finding: the prior escape hatch trusted bare MERGE_HEAD *presence* and exempted the ENTIRE
    staged set unconditionally — a file `git add`ed during the merge but not actually part of the
    merge diff (the verifier's `law-edit.txt` smuggle) rode through unchecked, reopening the exact
    c4923ae class this guard exists to close).

    Returns the set of paths a staged edit is permitted to touch during this merge. Two disjoint
    sub-cases, both computed against the merge-base:
      - paths touched by BOTH sides (in the incoming diff AND the ours diff) are real conflict
        candidates — git's own machinery can only conflict on a path touched by both, so ANY
        staged content there is legitimate conflict-resolution output, unrestricted.
      - paths touched by only ONE side are never conflicted — a plain three-way merge leaves such
        a path exactly as that one side already has it, so the staged blob must equal that side's
        blob content, or it is not a merge-resolution edit at all, just a same-named smuggle riding
        an incidentally-touched path (a real gap this guard would otherwise miss: a path legitimately
        touched on one side since divergence, with its staged content silently swapped for something
        else during the merge window — content-blind path-set confinement alone cannot see this).
    Returns None if MERGE_HEAD or the merge base cannot be resolved (caller must then refuse to
    exempt anything — fail-safe, never a silent full-sweep pass)."""
    head = subprocess.run(["git", "rev-parse", "-q", "--verify", "HEAD"],
                          capture_output=True, text=True)
    merge_head = subprocess.run(["git", "rev-parse", "-q", "--verify", "MERGE_HEAD"],
                                capture_output=True, text=True)
    if head.returncode != 0 or merge_head.returncode != 0:
        return None
    base = subprocess.run(["git", "merge-base", "HEAD", "MERGE_HEAD"],
                          capture_output=True, text=True)
    if base.returncode != 0:
        return None
    base_sha = base.stdout.strip()
    incoming_cp = subprocess.run(["git", "diff", "--name-only", base_sha, "MERGE_HEAD"],
                                 capture_output=True, text=True)
    ours_cp = subprocess.run(["git", "diff", "--name-only", base_sha, "HEAD"],
                             capture_output=True, text=True)
    if incoming_cp.returncode != 0 or ours_cp.returncode != 0:
        return None
    incoming = {ln.strip() for ln in incoming_cp.stdout.splitlines() if ln.strip()}
    ours = {ln.strip() for ln in ours_cp.stdout.splitlines() if ln.strip()}
    both = incoming & ours              # real conflict candidates -- unrestricted
    one_sided = incoming ^ ours         # touched by exactly one side -- content-pinned below
    permitted = set(both)
    for path in one_sided:
        rev = "MERGE_HEAD" if path in incoming else "HEAD"
        expected = _blob_hash(rev, path)
        staged = _blob_hash(None, path)
        if expected is not None and staged == expected:
            permitted.add(path)
        # else: staged content deviates from the untouched side's own version -- NOT part of git's
        # own merge machinery, left OUT of `permitted` deliberately (caught by the caller's smuggle
        # check below, unless separately declared via CLAUDE_COMMIT_PATHS)
    return permitted


def main(argv: list[str] | None = None) -> int:
    staged = _staged_paths()
    if not staged:
        return 0  # nothing staged — an empty commit is git's own problem, not the sweep class

    if _merge_in_progress():
        merge_diff = _merge_diff_paths()
        # a committer MAY also explicitly declare additional paths via CLAUDE_COMMIT_PATHS during a
        # merge (e.g. a genuinely new file introduced as part of resolving the merge) — that is an
        # explicit, visible declaration, never a silent widening; anything staged that is neither in
        # the merge diff NOR explicitly declared is the smuggle this fix closes.
        declared_extra = _declared_paths(os.environ.get("CLAUDE_COMMIT_PATHS", ""))
        if merge_diff is None:
            print("STAGING GUARD: commit REFUSED — MERGE_HEAD is present but the merge diff could "
                  "not be computed (merge-base/diff failed); the merge escape hatch cannot honestly "
                  "exempt an unknown set, so nothing is exempted (staging-scope-subset-enforcement, "
                  "night-build-defect-repair).", file=sys.stderr)
            return 1
        smuggled = sorted(p for p in staged if p not in merge_diff and p not in declared_extra)
        if smuggled:
            print("STAGING GUARD: commit REFUSED — MERGE_HEAD is present, but the staged set is NOT "
                  "confined to the merge's own changed-file set (night-build-defect-repair: bare "
                  "MERGE_HEAD *presence* used to exempt the entire staged index unconditionally, "
                  "letting a file `git add`ed during the merge but not part of the merge diff ride "
                  "through unchecked — the exact class staging-scope-subset-enforcement/c4923ae "
                  "exists to close, reopened through this hatch).", file=sys.stderr)
            print(f"  SMUGGLED — staged, not in the merge diff, not declared via "
                  f"CLAUDE_COMMIT_PATHS: {smuggled}", file=sys.stderr)
            print("  A genuine conflict-resolution edit is always inside the merge diff (it can only "
                  "conflict on a path touched by both sides). If this path is legitimately part of "
                  "this merge, declare it explicitly via CLAUDE_COMMIT_PATHS; if it is unrelated, "
                  "unstage it and commit it separately.", file=sys.stderr)
            return 1
        print("STAGING GUARD: OK — merge commit in progress (MERGE_HEAD present); staged set is "
              "confined to the merge's own changed-file set (escape hatch 2, "
              "staging-scope-subset-enforcement).", file=sys.stderr)
        return 0

    if os.environ.get("CLAUDE_COMMIT_ALL") == "maintainer":
        print("STAGING GUARD: OK — CLAUDE_COMMIT_ALL=maintainer acknowledged (escape hatch 3, "
              "staging-scope-subset-enforcement): the maintainer's own hands approve the FULL staged "
              "set below, declared-scope check skipped. Never silent — review this list:", file=sys.stderr)
        print(f"  Staged and approved ({len(staged)}): {sorted(staged)}", file=sys.stderr)
        return 0

    raw = os.environ.get("CLAUDE_COMMIT_PATHS", "").strip()
    if not raw:
        if os.environ.get("STAGING_GUARD_SKIP") == "1":
            return 0  # documented human-interactive opt-out
        print("STAGING GUARD: commit REFUSED — no CLAUDE_COMMIT_PATHS manifest declared (finding 33).", file=sys.stderr)
        print("  A bare `git commit` commits the whole index; declare exactly what THIS commit owns.", file=sys.stderr)
        print(f"  Staged now ({len(staged)}): {sorted(staged)}", file=sys.stderr)
        print("  Agents: export CLAUDE_COMMIT_PATHS='<the paths you git add-ed>' before committing.", file=sys.stderr)
        print("  Humans committing interactively: export STAGING_GUARD_SKIP=1 (once, in your shell rc),", file=sys.stderr)
        print("  or CLAUDE_COMMIT_ALL=maintainer to sweep the full staged set as a deliberate, logged act.", file=sys.stderr)
        return 1
    declared = _declared_paths(raw)
    # A declared entry ending in '/' is a DIRECTORY PREFIX (maintainer rider 2026-07-07): it covers any
    # staged path beneath it — a legitimate bulk case (a whole-dir ephemera/packet snapshot) declared
    # INDEPENDENTLY (the prefix is chosen before staging), never generated from the index (which would
    # make the manifest rubber-stamp whatever is staged). A prefix need not match anything (declaring a
    # dir that turns out empty is not an error); exact-file entries still must be staged.
    prefixes = {d for d in declared if d.endswith("/")}
    exact = declared - prefixes
    # SUBSET INVARIANT (staging-scope-subset-enforcement): every staged path must fall under a declared
    # exact entry or prefix — this is the class c4923ae broke (46 files staged, a handful declared).
    undeclared = sorted(p for p in staged
                        if p not in exact and not any(p.startswith(pre) for pre in prefixes))
    unstaged = sorted(exact - staged)        # a declared FILE that is absent — a failed add or a typo
    if undeclared or unstaged:
        print("STAGING GUARD: commit REFUSED — staged index is not a subset of the declared manifest "
              "(finding 33 / staging-scope-subset-enforcement, motivating class c4923ae: a broad add "
              "with a narrow declared scope rides unrelated paths along).", file=sys.stderr)
        if undeclared:
            print(f"  EXCESS — staged but NOT declared (unstage them or widen the declared scope): "
                  f"{undeclared}", file=sys.stderr)
        if unstaged:
            print(f"  MISSING (declared, NOT staged — a failed `git add` or a typo): {unstaged}", file=sys.stderr)
        print("  This is discipline, not friction: a scope you cannot state precisely is a scope you "
              "have not finished deciding. Narrow CLAUDE_COMMIT_PATHS to match, or split this into "
              "separate commits.", file=sys.stderr)
        return 1
    shared = sorted(p for p in staged if any(p == s or p.startswith(s) for s in _SHARED_SURFACES))
    if shared:
        print(f"STAGING GUARD: OK — staged set matches the manifest. NOTE shared-surface file(s) staged; "
              f"confirm every hunk is yours (ADR-0013 Rule 5): {shared}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
