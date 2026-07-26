#!/usr/bin/env python3
"""Seen-red specimen for night-build-defect-repair DEFECT 1 (gates/staging_guard.py merge bypass).

RCA: `_merge_in_progress()` used to return True on bare MERGE_HEAD *presence* and the guard
exempted the WHOLE staged set unconditionally. A fresh-context verifier reproduced this live: a
real `git merge --no-ff --no-commit`, then `git add`ed an unrelated file (`law-edit.txt`, no
relation to either side of the merge) that rode through the guard unchecked because the guard
never looked at what the merge actually touched.

RED: reproduces the exact smuggle against a REAL scratch git repo — a real `git merge --no-ff
--no-commit` (no conflicts) leaves MERGE_HEAD staged, then an unrelated file untouched by either
side of the merge is `git add`ed on top. The guard must now REFUSE, naming the smuggled path.

GREEN: a genuine conflict-resolution merge (both branches touch the same file, git leaves it
conflicted, the operator resolves and re-`git add`s it) must still PASS — the resolved path is
inside the merge diff by construction (a conflict can only happen on a path touched by both
sides).

RED 3 / GREEN 3 (merge-deletion blind spot, ledger row 1375, staging-guard-merge-deletion-
blindspot): `_merge_diff_paths` computed the touched-side's expected blob via `_blob_hash`, which
returns None when the path does not exist at that rev -- exactly what happens when the touched
side DELETED the path. The old check (`expected is not None and staged == expected`) then always
skipped a one-sided deletion, so a completely honest merge-inherited deletion never made it into
`permitted` and was flagged SMUGGLED, forcing the operator to declare it via CLAUDE_COMMIT_PATHS
just to land an ordinary merge (witnessed live 2026-07-26 at the pruning merge, ten deleted files).
GREEN 3 reproduces the honest shape (one side deletes a file the other side never touched) and
must PASS with no manifest declared. RED 3 is the negative control: a deletion smuggled onto a
path NEITHER side of the merge touched at all must still REFUSE -- the fix must not go blind to
deletions generally, only recognize the ones git's own merge machinery actually produced.

RED 2 (content-swap smuggle, found while adversarially re-probing this very fix): path-set
confinement alone has a residual hole — a path already touched on ONE side since divergence (say,
the mainline committed an unrelated edit to config.yml before this merge started) is a legitimate
member of the merge diff by PATH, but its staged CONTENT during the merge window can still be
silently swapped for something with no relation to either side's actual version, since a pure
path-set check never compares content. Reproduced here: mainline edits config.yml after
divergence (unrelated to the merge), the merge starts (no conflict on config.yml, since feature
never touched it), then config.yml's staged blob is swapped for arbitrary content different from
mainline's own committed version. MUST REFUSE. GREEN 2 is the negative control: the same shape
with config.yml staged at exactly the content git's own merge machinery would have produced
(untouched-by-incoming, so identical to the one side that DID touch it) — MUST PASS.

Every case runs the guard's REAL functions against a REAL git repo (subprocess, not stubbed) —
this is exactly the kind of state (MERGE_HEAD, merge-base, real diffs, real blob content) an
in-memory stub cannot honestly represent.
"""
from __future__ import annotations

import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "gates"))
import staging_guard as g  # noqa: E402

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own
# environment before any subprocess is spawned -- inherited by the whole process tree
# this fixture starts, so every repo-root verb invocation anywhere downstream carries it.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

FAILURES: list[str] = []


def _check(label: str, cond: bool) -> None:
    print(f"  [{'ok' if cond else 'FAIL'}] {label}")
    if not cond:
        FAILURES.append(label)


def _reset_env() -> None:
    for k in ("CLAUDE_COMMIT_PATHS", "CLAUDE_COMMIT_ALL", "STAGING_GUARD_SKIP"):
        os.environ.pop(k, None)


def _run(*a, cwd=None, **kw):
    return subprocess.run(a, cwd=cwd, check=True, capture_output=True, text=True, **kw)


def _run_capturing_stderr():
    buf = io.StringIO()
    old_stderr = sys.stderr
    sys.stderr = buf
    try:
        rc = g.main()
    finally:
        sys.stderr = old_stderr
    return rc, buf.getvalue()


def _init_repo(repo: Path) -> None:
    _run("git", "init", "-q", cwd=repo)
    _run("git", "config", "user.email", "x@example.com", cwd=repo)
    _run("git", "config", "user.name", "x", cwd=repo)


def _current_branch(repo: Path) -> str:
    cp = subprocess.run(["git", "branch", "--show-current"], cwd=repo,
                        capture_output=True, text=True)
    return cp.stdout.strip()


def red_smuggled_file_rides_the_merge() -> None:
    print("# RED — a real merge (no conflicts) + an unrelated `git add` smuggle: MUST REFUSE")
    _reset_env()
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        (repo / "base.txt").write_text("base\n")
        _run("git", "add", "base.txt", cwd=repo)
        _run("git", "commit", "-q", "-m", "base", cwd=repo)
        main_branch = _current_branch(repo)
        _run("git", "checkout", "-q", "-b", "feature", cwd=repo)
        (repo / "feature.txt").write_text("feature content\n")
        _run("git", "add", "feature.txt", cwd=repo)
        _run("git", "commit", "-q", "-m", "feature", cwd=repo)
        _run("git", "checkout", "-q", main_branch, cwd=repo)
        merge = subprocess.run(["git", "merge", "-q", "--no-ff", "--no-commit", "feature"],
                               cwd=repo, capture_output=True, text=True)
        _check("scratch merge left MERGE_HEAD staged (no conflicts)",
               (repo / ".git" / "MERGE_HEAD").exists() and merge.returncode == 0)
        # THE SMUGGLE: an unrelated file, part of neither side of the merge, `git add`ed on top —
        # the verifier's `law-edit.txt` shape, reproduced here as `law-edit.txt` itself.
        (repo / "law-edit.txt").write_text("an unrelated smuggled edit\n")
        _run("git", "add", "law-edit.txt", cwd=repo)
        cwd = os.getcwd()
        try:
            os.chdir(repo)
            rc, text = _run_capturing_stderr()
        finally:
            os.chdir(cwd)
        _check("guard REFUSES the smuggle (nonzero exit)", rc != 0)
        _check("teach-text names the smuggled path", "law-edit.txt" in text)
        _check("teach-text cites night-build-defect-repair", "night-build-defect-repair" in text)
        _check("teach-text cites the reopened class (staging-scope-subset-enforcement/c4923ae)",
               "staging-scope-subset-enforcement" in text and "c4923ae" in text)


def green_genuine_conflict_resolution() -> None:
    print("# GREEN — a genuine conflict-resolution merge still PASSES (resolved file is in-diff)")
    _reset_env()
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        (repo / "shared.txt").write_text("base\n")
        _run("git", "add", "shared.txt", cwd=repo)
        _run("git", "commit", "-q", "-m", "base", cwd=repo)
        main_branch = _current_branch(repo)
        _run("git", "checkout", "-q", "-b", "feature", cwd=repo)
        (repo / "shared.txt").write_text("feature edit\n")
        _run("git", "add", "shared.txt", cwd=repo)
        _run("git", "commit", "-q", "-m", "feature edits shared.txt", cwd=repo)
        _run("git", "checkout", "-q", main_branch, cwd=repo)
        (repo / "shared.txt").write_text("mainline edit\n")
        _run("git", "add", "shared.txt", cwd=repo)
        _run("git", "commit", "-q", "-m", "mainline edits shared.txt", cwd=repo)
        merge = subprocess.run(["git", "merge", "-q", "--no-ff", "feature"],
                               cwd=repo, capture_output=True, text=True)
        _check("merge produced a real conflict on shared.txt",
               merge.returncode != 0 and (repo / ".git" / "MERGE_HEAD").exists())
        # resolve it and re-stage — the ordinary conflict-resolution flow
        (repo / "shared.txt").write_text("resolved content\n")
        _run("git", "add", "shared.txt", cwd=repo)
        cwd = os.getcwd()
        try:
            os.chdir(repo)
            rc = g.main()
        finally:
            os.chdir(cwd)
        _check("genuine conflict-resolution merge PASSES", rc == 0)


def _one_sided_touch_repo(td: Path) -> tuple[Path, Path]:
    """Shared setup for RED 2 / GREEN 2: base commits config.yml, feature branches off and never
    touches it, mainline edits config.yml AFTER divergence (unrelated to the merge), then the
    merge starts — config.yml is untouched by the incoming side, so it can never conflict. Returns
    (repo, config_path)."""
    repo = Path(td)
    _init_repo(repo)
    (repo / "config.yml").write_text("base\n")
    _run("git", "add", "config.yml", cwd=repo)
    _run("git", "commit", "-q", "-m", "base", cwd=repo)
    main_branch = _current_branch(repo)
    _run("git", "checkout", "-q", "-b", "feature", cwd=repo)
    (repo / "feature.txt").write_text("feature content\n")
    _run("git", "add", "feature.txt", cwd=repo)
    _run("git", "commit", "-q", "-m", "feature", cwd=repo)
    _run("git", "checkout", "-q", main_branch, cwd=repo)
    (repo / "config.yml").write_text("mainline edit after divergence, unrelated to the merge\n")
    _run("git", "add", "config.yml", cwd=repo)
    _run("git", "commit", "-q", "-m", "mainline touches config.yml (unrelated to any merge)", cwd=repo)
    merge = subprocess.run(["git", "merge", "-q", "--no-ff", "--no-commit", "feature"],
                           cwd=repo, capture_output=True, text=True)
    _check("one-sided-touch merge left MERGE_HEAD staged (no conflict on config.yml)",
           (repo / ".git" / "MERGE_HEAD").exists() and merge.returncode == 0)
    return repo, repo / "config.yml"


def red_content_swap_on_one_sided_path() -> None:
    print("# RED 2 — content swapped on a path touched by only ONE side: MUST REFUSE")
    _reset_env()
    with tempfile.TemporaryDirectory() as td:
        repo, config_path = _one_sided_touch_repo(td)
        # THE SMUGGLE: config.yml is a legitimate merge-diff PATH (mainline touched it), but the
        # staged CONTENT is swapped for something that is neither mainline's nor feature's version.
        config_path.write_text("SMUGGLED GARBAGE, unrelated to mainline's own edit\n")
        _run("git", "add", "config.yml", cwd=repo)
        cwd = os.getcwd()
        try:
            os.chdir(repo)
            rc, text = _run_capturing_stderr()
        finally:
            os.chdir(cwd)
        _check("guard REFUSES the content-swap smuggle (nonzero exit)", rc != 0)
        _check("teach-text names the swapped path", "config.yml" in text)


def green_one_sided_path_unmodified() -> None:
    print("# GREEN 2 — a one-sided-touched path staged EXACTLY as that side committed it: PASSES")
    _reset_env()
    with tempfile.TemporaryDirectory() as td:
        repo, _config_path = _one_sided_touch_repo(td)
        # config.yml is already staged by git's own merge machinery at exactly mainline's content
        # (untouched by the incoming side) — no further edit, this IS the legitimate flow.
        cwd = os.getcwd()
        try:
            os.chdir(repo)
            rc = g.main()
        finally:
            os.chdir(cwd)
        _check("unmodified one-sided-touched path PASSES", rc == 0)


def green_one_sided_deletion_inherited_from_merge() -> None:
    print("# GREEN 3 — a one-sided deletion inherited from the merge (row 1375): MUST PASS, no manifest")
    _reset_env()
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        (repo / "keep.txt").write_text("base\n")
        (repo / "gone.txt").write_text("base\n")
        _run("git", "add", "keep.txt", "gone.txt", cwd=repo)
        _run("git", "commit", "-q", "-m", "base", cwd=repo)
        main_branch = _current_branch(repo)
        _run("git", "checkout", "-q", "-b", "feature", cwd=repo)
        _run("git", "rm", "-q", "gone.txt", cwd=repo)
        _run("git", "commit", "-q", "-m", "feature deletes gone.txt", cwd=repo)
        _run("git", "checkout", "-q", main_branch, cwd=repo)
        (repo / "keep.txt").write_text("base\nmainline edit (unrelated to the merge)\n")
        _run("git", "add", "keep.txt", cwd=repo)
        _run("git", "commit", "-q", "-m", "mainline touches keep.txt (unrelated to the merge)", cwd=repo)
        merge = subprocess.run(["git", "merge", "-q", "--no-ff", "--no-commit", "feature"],
                               cwd=repo, capture_output=True, text=True)
        _check("merge inherited the one-sided deletion, no conflict",
               (repo / ".git" / "MERGE_HEAD").exists() and merge.returncode == 0
               and not (repo / "gone.txt").exists())
        cwd = os.getcwd()
        try:
            os.chdir(repo)
            rc, text = _run_capturing_stderr()
        finally:
            os.chdir(cwd)
        _check("merge-inherited deletion PASSES with no manifest (not flagged SMUGGLED)", rc == 0)
        _check("guard did not misname gone.txt as smuggled", "gone.txt" not in text)


def red_deletion_smuggled_onto_an_untouched_path() -> None:
    print("# RED 3 — a deletion smuggled onto a path NEITHER side of the merge touched: MUST REFUSE")
    _reset_env()
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        (repo / "untouched.txt").write_text("base\n")
        _run("git", "add", "untouched.txt", cwd=repo)
        _run("git", "commit", "-q", "-m", "base", cwd=repo)
        main_branch = _current_branch(repo)
        _run("git", "checkout", "-q", "-b", "feature", cwd=repo)
        (repo / "feature.txt").write_text("feature\n")
        _run("git", "add", "feature.txt", cwd=repo)
        _run("git", "commit", "-q", "-m", "feature adds feature.txt", cwd=repo)
        _run("git", "checkout", "-q", main_branch, cwd=repo)
        (repo / "mainline.txt").write_text("mainline\n")
        _run("git", "add", "mainline.txt", cwd=repo)
        _run("git", "commit", "-q", "-m", "mainline adds mainline.txt", cwd=repo)
        merge = subprocess.run(["git", "merge", "-q", "--no-ff", "--no-commit", "feature"],
                               cwd=repo, capture_output=True, text=True)
        _check("merge left MERGE_HEAD staged, no conflict",
               (repo / ".git" / "MERGE_HEAD").exists() and merge.returncode == 0)
        # THE SMUGGLE: delete a path neither side of the merge ever touched.
        _run("git", "rm", "-q", "untouched.txt", cwd=repo)
        cwd = os.getcwd()
        try:
            os.chdir(repo)
            rc, text = _run_capturing_stderr()
        finally:
            os.chdir(cwd)
        _check("guard REFUSES the smuggled deletion (nonzero exit)", rc != 0)
        _check("teach-text names the smuggled path", "untouched.txt" in text)


def main() -> int:
    red_smuggled_file_rides_the_merge()
    green_genuine_conflict_resolution()
    red_content_swap_on_one_sided_path()
    green_one_sided_path_unmodified()
    green_one_sided_deletion_inherited_from_merge()
    red_deletion_smuggled_onto_an_untouched_path()
    _reset_env()
    if FAILURES:
        print(f"\nSPECIMEN INERT — {len(FAILURES)} check(s) failed: {FAILURES}")
        return 1
    print("\n# merge-diff-confinement: RED reproduces the verifier's smuggle and is refused; "
          "GREEN's genuine conflict-resolution merge still passes; RED 2 reproduces the "
          "content-swap-on-a-one-sided-path residual found while adversarially re-probing this "
          "fix, also refused; GREEN 2's unmodified one-sided path still passes; GREEN 3 (row 1375) "
          "a merge-inherited one-sided deletion passes with no manifest; RED 3 confirms a deletion "
          "smuggled onto a path neither side touched is still refused.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
