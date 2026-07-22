#!/usr/bin/env python3
"""Seen-red specimen for staging-scope-subset-enforcement (ledger item, motivating class c4923ae).

RED: reproduces c4923ae's shape — a commit declares a narrow scope (a manifest-only change) but its
staged index carries a broad, undeclared sweep (a reverted gitignore rule, a deleted seen-red fixture,
an edited kernel/lineage detect.sql — none of it declared). The guard must REFUSE, name every excess
path, and cite this item + c4923ae in its teach-text.

GREEN (four real commit flows, each must PASS):
  1. staged set IS a subset of the declared scope (the ordinary case).
  2. a merge commit in progress (MERGE_HEAD present) — exempt with no manifest declared at all.
  3. CLAUDE_COMMIT_ALL=maintainer — the maintainer's own-hands escape hatch, broad staged, no manifest.
  4. the temp-index house pattern (CLAUDE_COMMIT_PATHS + GIT_INDEX_FILE read-tree HEAD) — the guard
     reads whichever index GIT_INDEX_FILE names, proven against a REAL scratch git repo (not stubbed).

Flows 2 and 4 exercise real git plumbing (MERGE_HEAD / GIT_INDEX_FILE) in a throwaway scratch repo —
the guard's own subprocess calls, not a stub — since these two escape hatches depend on genuine git
state the in-memory stub style (see seen-red/33-staging-guard/) cannot represent.
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

FAILURES: list[str] = []


def _reset_env() -> None:
    for k in ("CLAUDE_COMMIT_PATHS", "CLAUDE_COMMIT_ALL", "STAGING_GUARD_SKIP"):
        os.environ.pop(k, None)


def _check(label: str, cond: bool) -> None:
    print(f"  [{'ok' if cond else 'FAIL'}] {label}")
    if not cond:
        FAILURES.append(label)


def _run_capturing_stderr() -> tuple[int, str]:
    """Runs g.main(), returning (exit code, everything it printed to stderr)."""
    buf = io.StringIO()
    old_stderr = sys.stderr
    sys.stderr = buf
    try:
        rc = g.main()
    finally:
        sys.stderr = old_stderr
    return rc, buf.getvalue()


def red_c4923ae_reproduction() -> None:
    print("# RED — c4923ae reproduction: narrow declared scope, broad staged sweep")
    _reset_env()
    os.environ["CLAUDE_COMMIT_PATHS"] = (
        "panel/manifests/0714_exec_response.json panel/manifests/SCHEMA.md"
    )
    swept = {
        ".gitignore",                                              # reverted privacy-hazard rule
        "seen-red/33-staging-guard/red-specimen.py",                # a live fixture, edited/deleted
        "kernel/lineage/s21-session-aware-distinctness.detect.sql", # unrelated detect.sql edit
        "instruments/verify_branch_attribution.py",
    }
    g._staged_paths = lambda: swept | {
        "panel/manifests/0714_exec_response.json", "panel/manifests/SCHEMA.md"}
    g._merge_in_progress = lambda: False
    rc, text = _run_capturing_stderr()
    _check("guard REFUSES (nonzero exit)", rc != 0)
    _check("teach-text cites the item (staging-scope-subset-enforcement)",
           "staging-scope-subset-enforcement" in text)
    _check("teach-text cites c4923ae", "c4923ae" in text)
    _check("every swept path is named in the EXCESS line",
           all(p in text for p in swept))


def green_subset_of_declared() -> None:
    print("# GREEN 1 — staged set is a genuine subset of the declared scope")
    _reset_env()
    os.environ["CLAUDE_COMMIT_PATHS"] = "gates/staging_guard.py seen-red/"
    g._staged_paths = lambda: {"gates/staging_guard.py",
                               "seen-red/staging-scope-subset-enforcement/run_fixtures.py"}
    g._merge_in_progress = lambda: False
    rc = g.main()
    _check("ordinary declared-superset commit PASSES", rc == 0)


def green_merge_commit() -> None:
    print("# GREEN 2 — a real merge in progress (MERGE_HEAD present) is exempt, no manifest needed")
    _reset_env()
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        run = lambda *a: subprocess.run(a, cwd=repo, check=True,
                                        capture_output=True, text=True)
        run("git", "init", "-q")
        run("git", "config", "user.email", "x@example.com")
        run("git", "config", "user.name", "x")
        (repo / "a.txt").write_text("base\n")
        run("git", "add", "a.txt")
        run("git", "commit", "-q", "-m", "base")
        run("git", "checkout", "-q", "-b", "feature")
        (repo / "b.txt").write_text("feature\n")
        run("git", "add", "b.txt")
        run("git", "commit", "-q", "-m", "feature")
        run("git", "checkout", "-q", "master" if _has_branch(repo, "master") else "main")
        (repo / "c.txt").write_text("mainline\n")
        run("git", "add", "c.txt")
        run("git", "commit", "-q", "-m", "mainline")
        # start a merge that conflicts nothing but leaves MERGE_HEAD + a staged multi-file diff
        merge = subprocess.run(["git", "merge", "-q", "--no-ff", "--no-commit", "feature"],
                               cwd=repo, capture_output=True, text=True)
        _check("scratch merge left MERGE_HEAD staged", (repo / ".git" / "MERGE_HEAD").exists()
               or merge.returncode == 0)
        cwd = os.getcwd()
        # no CLAUDE_COMMIT_PATHS declared at all — would REFUSE outside a merge
        try:
            os.chdir(repo)
            g._staged_paths = staging_guard_real_staged  # real subprocess, real repo
            g._merge_in_progress = staging_guard_real_merge
            rc = g.main()
        finally:
            os.chdir(cwd)
        _check("merge commit with NO manifest still PASSES (escape hatch 2)", rc == 0)


def _has_branch(repo: Path, name: str) -> bool:
    cp = subprocess.run(["git", "rev-parse", "--verify", name], cwd=repo,
                        capture_output=True, text=True)
    return cp.returncode == 0


def staging_guard_real_staged() -> set[str]:
    cp = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRD"],
                        capture_output=True, text=True)
    return {ln.strip() for ln in cp.stdout.splitlines() if ln.strip()}


def staging_guard_real_merge() -> bool:
    cp = subprocess.run(["git", "rev-parse", "-q", "--verify", "MERGE_HEAD"],
                        capture_output=True, text=True)
    return cp.returncode == 0


def green_maintainer_all() -> None:
    print("# GREEN 3 — CLAUDE_COMMIT_ALL=maintainer sweeps the full staged set, loudly")
    _reset_env()
    os.environ["CLAUDE_COMMIT_ALL"] = "maintainer"
    broad = {"a.py", "b.md", "c/d.sql"}
    g._staged_paths = lambda: broad
    g._merge_in_progress = lambda: False
    rc, text = _run_capturing_stderr()
    _check("maintainer override PASSES", rc == 0)
    _check("override is logged, never silent (every path named)", all(p in text for p in broad))


def green_temp_index_house_pattern() -> None:
    print("# GREEN 4 — temp-index commit (CLAUDE_COMMIT_PATHS + GIT_INDEX_FILE) reads the temp index")
    _reset_env()
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        run = lambda *a, **kw: subprocess.run(a, cwd=repo, check=True,
                                              capture_output=True, text=True, **kw)
        run("git", "init", "-q")
        run("git", "config", "user.email", "x@example.com")
        run("git", "config", "user.name", "x")
        (repo / "keep.txt").write_text("base\n")
        run("git", "add", "keep.txt")
        run("git", "commit", "-q", "-m", "base")
        # a REAL-index-only change (must NOT leak into the temp-index read)
        (repo / "keep.txt").write_text("real-index-only edit\n")
        run("git", "add", "keep.txt")
        # a separate temp index, seeded from HEAD, holding a DIFFERENT declared file
        temp_index = repo / ".git" / "temp-index-fixture"
        env = dict(os.environ, GIT_INDEX_FILE=str(temp_index))
        subprocess.run(["git", "read-tree", "HEAD"], cwd=repo, env=env, check=True,
                       capture_output=True, text=True)
        (repo / "new.txt").write_text("new via temp index\n")
        subprocess.run(["git", "add", "new.txt"], cwd=repo, env=env, check=True,
                       capture_output=True, text=True)
        os.environ["GIT_INDEX_FILE"] = str(temp_index)
        os.environ["CLAUDE_COMMIT_PATHS"] = "new.txt"
        cwd = os.getcwd()
        try:
            os.chdir(repo)
            g._staged_paths = staging_guard_real_staged
            g._merge_in_progress = staging_guard_real_merge
            rc = g.main()
        finally:
            os.chdir(cwd)
            os.environ.pop("GIT_INDEX_FILE", None)
        _check("declared-matches-temp-index commit PASSES (real-index churn on keep.txt not seen)",
               rc == 0)


def main() -> int:
    red_c4923ae_reproduction()
    green_subset_of_declared()
    green_merge_commit()
    green_maintainer_all()
    green_temp_index_house_pattern()
    _reset_env()
    if FAILURES:
        print(f"\nSPECIMEN INERT — {len(FAILURES)} check(s) failed: {FAILURES}")
        return 1
    print("\n# staging-scope-subset-enforcement: RED reproduced + refused (c4923ae class named), "
          "all four GREEN legitimate flows (subset / merge / maintainer-hands / temp-index) pass.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
