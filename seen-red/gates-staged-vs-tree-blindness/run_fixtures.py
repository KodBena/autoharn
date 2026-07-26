#!/usr/bin/env python3
"""Both-polarity fixture for gates-staged-vs-tree-blindness (ledger row 1234): one shared
throwaway-git-repo family exercising the SAME staged-vs-tree class across every gate the census
converted (gates/deep_walk_recursion_guard.py's own "Finding A, 2026-07-23" fixture, in
seen-red/deep-walk-recursion-guard/run_fixtures.py, is that class's ORIGINAL specimen and stays
the pattern exemplar; this fixture is the shared family for its five newly-converted siblings,
per the builder brief's own "a single shared seen-red family exercising the class across
converted gates is acceptable" allowance).

THE CLASS, restated once here rather than per-gate: `git commit` embeds the STAGED (index)
bytes, not whatever the working tree happens to hold when a gate runs. A tree-reading
content-checking gate can be defeated by staging a violation, then restoring the previous
(clean) bytes in the working tree WITHOUT re-staging: the gate reads the clean tree, passes,
and the commit still embeds the staged violation. Every case below: build a throwaway git repo,
`git add` a violating file, restore a clean version of the SAME path in the working tree without
touching the index, then assert the gate's default (no `--tree`/no root-override-to-tree-only)
invocation still catches the violation via the staged bytes -- and, where the gate exposes a
`--tree` (or equivalent working-tree-forcing) mode, that mode instead sees the restored CLEAN
tree and passes, proving the two reads genuinely differ.

FIVE GATES, FIVE SUB-FIXTURES:
  1. gates/no_lazy_imports.py       -- CLI takes [root] [--tree]; subprocess-driven.
  2. gates/max_lines.py             -- CLI takes [root] [--tree]; subprocess-driven.
  3. gates/link_integrity.py        -- CLI takes --repo PATH [--tree]; subprocess-driven.
  4. gates/doc_shapes.py            -- gate mode takes FILE args directly (no root to fake);
                                        driven via `check_file(path, use_tree=)` in-process,
                                        same device seen-red/setup-tui-purity-gate/run_fixtures.py
                                        already uses for THAT gate's non-staged-vs-tree cases.
  5. gates/doc_attestation_presence.py -- CLI takes --doc-root/--ledger [--tree]; subprocess-driven.
  6. gates/setup_tui_purity_gate.py -- `scan_file`/`scan_configtree_file` take a bare path (no
                                        root to fake, PACKAGE_DIR/CONFIGTREE_DIR are only used by
                                        main()'s own directory walk); driven in-process the same
                                        way, over a throwaway git repo.

gates/_staged_read.py itself (the shared primitive all six now import) is exercised implicitly
by every case below -- there is no separate unit fixture for it alone for the STAGED-vs-TREE
question; its only two callers' worth of behavior (staged-present -> staged bytes; staged-absent
-> tree fallback) is exactly what "staged read wins, tree fallback for untracked" proves case by
case here.

CASE 7 -- THE GIT_DIR MECHANISM, NAMED BUT NOT PREVIOUSLY EXERCISED (added 2026-07-26, closing a
MODERATE/SILENT finding from a fresh-context strengthened-tier review of this fixture's own first
cut): cases 1-6 above all stage-then-restore inside a plain, non-worktree throwaway repo -- they
prove the STAGED-vs-TREE read is right, but none of them ever drives the actual REAL BUG the
_staged_read.py module docstring is named for and was fixed against ("REAL BUG FOUND VALIDATING
THIS CENSUS" there): a `git commit` running as a hook INSIDE A GIT WORKTREE (this repo's own
`.claude/worktrees/*` pattern) sets `GIT_DIR` in the process environment, and an unstripped
`git -C <subdir> rev-parse --show-toplevel` inherits it and silently misresolves the toplevel to
`<subdir>` itself instead of the worktree's real root. `case_git_dir_worktree_regression` below
drives an ACTUAL `git commit` through a capturing `core.hooksPath` hook inside a real linked
worktree to harvest the REAL `GIT_*` env vars git sets for that context (not a guessed/hand-typed
approximation), replays them over the current process env, and on that exact env: (a) reproduces
the raw pre-fix defect on an unstripped `-C` call (proving the trigger is real, not narrative),
then (b) proves `_staged_read.read_staged_bytes` and (c) one of the six converted gates, run as a
live subprocess, both get it right under the identical polluted env.

Runs entirely against throwaway git repos in a TemporaryDirectory; zero residue in this repo.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..", "..")
GATES = os.path.join(REPO, "gates")

sys.path.insert(0, GATES)
import doc_shapes as doc_shapes_gate  # noqa: E402
import setup_tui_purity_gate as purity_gate  # noqa: E402
import _staged_read as staged_read  # noqa: E402  (case 7's own subject: the shared primitive)
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"  # FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1 (merge-completion of the dc91755 sweep: this family postdates its base)


def _init_repo(repo_dir: str) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "fixture"], cwd=repo_dir, check=True)


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _stage_violation_then_restore_clean(repo_dir: str, rel_path: str, clean: str, violating: str) -> None:
    """Commit `clean` as a baseline, then `git add` the `violating` bytes, then overwrite the
    working-tree file back to `clean` WITHOUT re-staging -- the index still holds `violating`."""
    abs_path = os.path.join(repo_dir, rel_path)
    _write(abs_path, clean)
    subprocess.run(["git", "add", rel_path], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "baseline"], cwd=repo_dir, check=True)
    _write(abs_path, violating)
    subprocess.run(["git", "add", rel_path], cwd=repo_dir, check=True)
    _write(abs_path, clean)  # restore clean tree, index still carries `violating`


# ---------------------------------------------------------------------------------------
# 1. no_lazy_imports.py
# ---------------------------------------------------------------------------------------

def case_no_lazy_imports() -> None:
    gate = os.path.join(GATES, "no_lazy_imports.py")
    clean = "from __future__ import annotations\nimport os\n\ndef f():\n    return os.getcwd()\n"
    violating = ("from __future__ import annotations\nimport os\n\n"
                 "def f():\n    import json\n    return json.dumps(os.getcwd())\n")
    with tempfile.TemporaryDirectory(prefix="no-lazy-imports-staged-vs-tree-") as repo_dir:
        _init_repo(repo_dir)
        rel = "probe.py"
        _stage_violation_then_restore_clean(repo_dir, rel, clean, violating)
        staged = subprocess.run([sys.executable, gate, repo_dir], capture_output=True, text=True)
        assert staged.returncode == 1, f"expected exit 1 (staged lazy import), got {staged.returncode}: {staged.stdout}"
        assert "import json" in staged.stdout, staged.stdout
        tree_mode = subprocess.run([sys.executable, gate, repo_dir, "--tree"], capture_output=True, text=True)
        assert tree_mode.returncode == 0, f"--tree should read the restored clean tree, got {tree_mode.returncode}: {tree_mode.stdout}"
    print("case 1 (no_lazy_imports) ok: staged lazy import refused despite restored clean tree; --tree reads the clean tree")


# ---------------------------------------------------------------------------------------
# 2. max_lines.py
# ---------------------------------------------------------------------------------------

def case_max_lines() -> None:
    gate = os.path.join(GATES, "max_lines.py")
    clean = "\n".join(f"# line {i}" for i in range(10)) + "\n"
    violating = "\n".join(f"# line {i}" for i in range(450)) + "\n"  # new file, over the 400 ceiling
    with tempfile.TemporaryDirectory(prefix="max-lines-staged-vs-tree-") as repo_dir:
        _init_repo(repo_dir)
        rel = "gates/synthetic_probe_for_fixture.py"
        _stage_violation_then_restore_clean(repo_dir, rel, clean, violating)
        staged = subprocess.run([sys.executable, gate, repo_dir], capture_output=True, text=True)
        assert staged.returncode == 1, f"expected exit 1 (staged over-ceiling new file), got {staged.returncode}: {staged.stdout}"
        assert f"{rel}: 450 lines -- NEW file over the 400-line ceiling" in staged.stdout, staged.stdout
        # NOTE: this gate's BASELINE table is hardcoded to THIS repository's own real files (see
        # its module docstring) -- pointed at a throwaway repo, every baseline row reads as
        # "STALE" (not present there) regardless of read mode, so overall exit code is always 1
        # against a foreign root. The staged-vs-tree assertion this fixture cares about is
        # therefore keyed on the PROBE FILE'S OWN finding, not the overall exit code: it must
        # appear in the staged read (above) and must NOT appear in the --tree read (below).
        tree_mode = subprocess.run([sys.executable, gate, repo_dir, "--tree"], capture_output=True, text=True)
        assert rel not in tree_mode.stdout, (
            f"--tree should read the restored short tree file (10 lines, clean) for {rel}, but "
            f"it still appears in the findings: {tree_mode.stdout}")
    print("case 2 (max_lines) ok: staged over-ceiling file refused despite restored short tree; --tree reads the short tree")


# ---------------------------------------------------------------------------------------
# 3. link_integrity.py
# ---------------------------------------------------------------------------------------

def case_link_integrity() -> None:
    gate = os.path.join(GATES, "link_integrity.py")
    clean = "# Doc\n\n[real](real.md)\n"
    violating = "# Doc\n\n[broken](does-not-exist.md)\n"
    with tempfile.TemporaryDirectory(prefix="link-integrity-staged-vs-tree-") as repo_dir:
        _init_repo(repo_dir)
        _write(os.path.join(repo_dir, "real.md"), "# Real target\n")
        subprocess.run(["git", "add", "real.md"], cwd=repo_dir, check=True)
        rel = "probe.md"
        _stage_violation_then_restore_clean(repo_dir, rel, clean, violating)
        staged = subprocess.run([sys.executable, gate, "--repo", repo_dir], capture_output=True, text=True)
        assert staged.returncode == 1, f"expected exit 1 (staged broken link), got {staged.returncode}: {staged.stdout}"
        assert "does-not-exist.md" in staged.stdout, staged.stdout
        tree_mode = subprocess.run([sys.executable, gate, "--repo", repo_dir, "--tree"], capture_output=True, text=True)
        assert tree_mode.returncode == 0, f"--tree should read the restored clean tree, got {tree_mode.returncode}: {tree_mode.stdout}"
    print("case 3 (link_integrity) ok: staged broken link refused despite restored clean tree; --tree reads the clean tree")


# ---------------------------------------------------------------------------------------
# 4. doc_shapes.py -- driven in-process (gate mode takes bare file paths, no root to fake)
# ---------------------------------------------------------------------------------------

def case_doc_shapes() -> None:
    clean = "# Doc\n\nA real sentence explaining the point in full.\n"
    violating = "# Doc\n\nThe core deliverable.\n"  # the FRAGMENT shape
    with tempfile.TemporaryDirectory(prefix="doc-shapes-staged-vs-tree-") as repo_dir:
        _init_repo(repo_dir)
        rel = "probe.md"
        _stage_violation_then_restore_clean(repo_dir, rel, clean, violating)
        abs_path = Path(repo_dir) / rel
        staged = doc_shapes_gate.check_file(abs_path)
        assert staged, "expected a FRAGMENT finding from the STAGED bytes"
        assert any("FRAGMENT" in v for v in staged), staged
        tree_mode = doc_shapes_gate.check_file(abs_path, use_tree=True)
        assert tree_mode == [], f"--tree should read the restored clean tree, got {tree_mode}"
    print("case 4 (doc_shapes) ok: staged FRAGMENT refused despite restored clean tree; use_tree=True reads the clean tree")


# ---------------------------------------------------------------------------------------
# 5. doc_attestation_presence.py
# ---------------------------------------------------------------------------------------

def case_doc_attestation_presence() -> None:
    gate = os.path.join(GATES, "doc_attestation_presence.py")
    with tempfile.TemporaryDirectory(prefix="doc-attestation-staged-vs-tree-") as repo_dir:
        _init_repo(repo_dir)
        rel = "probe.md"
        attested_content = "# Attested doc\n\nThis exact text was attested.\n"
        edited_content = "# Attested doc\n\nThis text was edited AFTER attestation, unreviewed.\n"
        # Commit the attested content, record its attestation, then stage the edit and restore
        # the ATTESTED (old, already-reviewed) bytes in the tree without re-staging -- the tree
        # now looks clean/attested, but the STAGED bytes are the unreviewed edit.
        abs_path = os.path.join(repo_dir, rel)
        _write(abs_path, attested_content)
        subprocess.run(["git", "add", rel], cwd=repo_dir, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "baseline"], cwd=repo_dir, check=True)
        ledger_path = os.path.join(repo_dir, "attestations", "doc-legibility-attestations.jsonl")
        record_body = os.path.join(repo_dir, "record.json")
        with open(record_body, "w", encoding="utf-8") as f:
            json.dump({
                "doc": rel, "b_id": "fixture-b", "escalated": False,
                "rounds": [{"round": 1, "verdict": "CLEAN", "findings": [],
                            "clauses_checked": ["1a", "1b", "1c", "1d"]}],
            }, f)
        rec = subprocess.run(
            [sys.executable, gate, "--doc-root", repo_dir, "--ledger", ledger_path, "--record", record_body],
            capture_output=True, text=True)
        assert rec.returncode == 0, f"expected --record to succeed, got {rec.returncode}: {rec.stdout} {rec.stderr}"
        # Now stage the edit, restore the ATTESTED bytes in the tree.
        _write(abs_path, edited_content)
        subprocess.run(["git", "add", rel], cwd=repo_dir, check=True)
        _write(abs_path, attested_content)
        staged = subprocess.run(
            [sys.executable, gate, "--doc-root", repo_dir, "--ledger", ledger_path, rel],
            capture_output=True, text=True)
        assert staged.returncode == 1, (
            f"expected exit 1 (staged edit has no attestation, despite the restored tree matching "
            f"an attested hash), got {staged.returncode}: {staged.stdout}")
        assert "NO-ATTESTATION" in staged.stdout, staged.stdout
        tree_mode = subprocess.run(
            [sys.executable, gate, "--doc-root", repo_dir, "--ledger", ledger_path, "--tree", rel],
            capture_output=True, text=True)
        assert tree_mode.returncode == 0, (
            f"--tree should hash the restored (already-attested) tree file and pass, got "
            f"{tree_mode.returncode}: {tree_mode.stdout}")
    print("case 5 (doc_attestation_presence) ok: staged unreviewed edit refused (hash mismatch) "
          "despite a restored tree that hashes to an already-attested record; --tree hashes the "
          "restored tree and passes")


# ---------------------------------------------------------------------------------------
# 6. setup_tui_purity_gate.py -- driven in-process (scan_file takes a bare path)
# ---------------------------------------------------------------------------------------

def case_setup_tui_purity_gate() -> None:
    clean = "def f(x):\n    return x + 1\n"
    violating = "def f(x):\n    print('debug', x)\n    return x + 1\n"
    with tempfile.TemporaryDirectory(prefix="setup-tui-purity-staged-vs-tree-") as repo_dir:
        _init_repo(repo_dir)
        rel = "probe.py"
        _stage_violation_then_restore_clean(repo_dir, rel, clean, violating)
        abs_path = Path(repo_dir) / rel
        staged = purity_gate.scan_file(str(abs_path))
        assert staged, "expected a print(...) finding from the STAGED bytes"
        assert any("print(" in v for v in staged), staged
        tree_mode = purity_gate.scan_file(str(abs_path), use_tree=True)
        assert tree_mode == [], f"use_tree=True should read the restored clean tree, got {tree_mode}"
    print("case 6 (setup_tui_purity_gate) ok: staged print(...) refused despite restored clean "
          "tree; use_tree=True reads the clean tree")


# ---------------------------------------------------------------------------------------
# 7. THE GIT_DIR MECHANISM -- a real `git commit` inside a real linked worktree, driven through
#    a capturing hook so the reproduction's env is HARVESTED, not hand-typed (see module
#    docstring's CASE 7 section).
# ---------------------------------------------------------------------------------------

def case_git_dir_worktree_regression() -> None:
    clean = "from __future__ import annotations\nimport os\n\ndef f():\n    return os.getcwd()\n"
    violating = ("from __future__ import annotations\nimport os\n\n"
                 "def f():\n    import json\n    return json.dumps(os.getcwd())\n")
    main_repo = tempfile.mkdtemp(prefix="gitdir-worktree-main-")
    worktree_dir = tempfile.mkdtemp(prefix="gitdir-worktree-linked-")
    hooks_dir = tempfile.mkdtemp(prefix="gitdir-worktree-hooks-")
    os.rmdir(worktree_dir)  # `git worktree add` requires the target path not already exist
    try:
        _init_repo(main_repo)
        sub_rel = "sub/probe.py"
        _write(os.path.join(main_repo, sub_rel), clean)
        subprocess.run(["git", "add", sub_rel], cwd=main_repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "baseline"], cwd=main_repo, check=True)

        subprocess.run(["git", "worktree", "add", "-q", worktree_dir, "-b", "gitdir-probe-branch"],
                        cwd=main_repo, check=True)

        # Harvest the REAL GIT_* env a pre-commit hook sees when git commits INSIDE this linked
        # worktree -- not a guessed approximation, the actual values git itself sets.
        captured_path = os.path.join(hooks_dir, "captured_env.txt")
        hook_path = os.path.join(hooks_dir, "pre-commit")
        with open(hook_path, "w", encoding="utf-8") as f:
            f.write(f"#!/bin/sh\nenv | grep '^GIT_' > {captured_path}\nexit 0\n")
        os.chmod(hook_path, 0o755)
        subprocess.run(
            ["git", "-c", f"core.hooksPath={hooks_dir}", "commit", "-q", "--allow-empty",
             "-m", "capture env"],
            cwd=worktree_dir, check=True)
        captured = {}
        with open(captured_path, encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, _, v = line.rstrip("\n").partition("=")
                    captured[k] = v
        assert "GIT_DIR" in captured, f"hook did not capture GIT_DIR -- reproduction stale: {captured}"

        # Stage a violation in the WORKTREE's own copy of the file, restore clean bytes in the
        # tree without re-staging -- same staged-vs-tree class, now inside a linked worktree.
        # Inlined rather than `_stage_violation_then_restore_clean` (which re-commits `clean` as
        # its own baseline first): the worktree already checked out `main_repo`'s `clean` commit
        # verbatim, so a redundant `git commit` of identical bytes here would fail with "nothing
        # to commit" -- only the stage-violation/restore-clean half is needed.
        abs_sub_path = os.path.join(worktree_dir, sub_rel)
        _write(abs_sub_path, violating)
        subprocess.run(["git", "add", sub_rel], cwd=worktree_dir, check=True)
        _write(abs_sub_path, clean)  # restore clean tree, index still carries `violating`

        saved_env = {k: os.environ.get(k) for k in captured}
        try:
            os.environ.update(captured)
            sub_dir_abs = os.path.join(worktree_dir, "sub")

            # (a) RAW PRE-FIX REPRODUCTION: an unstripped `-C` call inherits the captured GIT_DIR
            # and misresolves --show-toplevel to `sub_dir_abs` itself -- the exact defect
            # gates/_staged_read.py's module docstring names.
            raw = subprocess.run(["git", "-C", sub_dir_abs, "rev-parse", "--show-toplevel"],
                                  capture_output=True, text=True)
            assert raw.returncode == 0, raw.stderr
            raw_top = os.path.realpath(raw.stdout.strip())
            assert raw_top == os.path.realpath(sub_dir_abs), (
                f"expected the RAW pre-fix defect (toplevel misresolved to the subdir itself, "
                f"{sub_dir_abs!r}), got {raw_top!r} instead -- this reproduction's harvested env "
                f"no longer triggers the live defect; re-diagnose before trusting the fix below")
            print(f"  (a) RED  raw unstripped `-C {os.path.basename(sub_dir_abs)} rev-parse "
                  f"--show-toplevel` under a live worktree hook's captured env misresolves "
                  f"toplevel to the subdir itself: {raw_top}")

            # (b) POST-FIX: the shared primitive, called under the SAME polluted env, strips
            # GIT_DIR/GIT_WORK_TREE/GIT_PREFIX/GIT_COMMON_DIR and correctly reads the STAGED
            # (violating) bytes, not the restored clean tree.
            staged_bytes = staged_read.read_staged_bytes(Path(sub_dir_abs) / "probe.py")
            assert staged_bytes is not None, "expected staged bytes, primitive returned None"
            assert b"import json" in staged_bytes, staged_bytes
            print("  (b) GREEN read_staged_bytes, same polluted env, correctly returns the "
                  "STAGED (violating) bytes")

            # (c) END TO END: one of the six converted gates, run as a REAL subprocess
            # (inheriting this same polluted env exactly as a live pre-commit hook invocation
            # would), still catches the staged violation despite the restored clean tree.
            gate = os.path.join(GATES, "no_lazy_imports.py")
            result = subprocess.run([sys.executable, gate, worktree_dir],
                                     capture_output=True, text=True)
            assert result.returncode == 1, (
                f"expected exit 1 (staged lazy import, live worktree GIT_DIR env), got "
                f"{result.returncode}: {result.stdout}")
            assert "import json" in result.stdout, result.stdout
            print("  (c) GREEN no_lazy_imports.py, run as a live subprocess under the identical "
                  "polluted env, exit 1 -- staged violation caught despite the restored clean tree")
        finally:
            for k, v in saved_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", worktree_dir],
                        cwd=main_repo, check=False)
        shutil.rmtree(main_repo, ignore_errors=True)
        shutil.rmtree(worktree_dir, ignore_errors=True)
        shutil.rmtree(hooks_dir, ignore_errors=True)
    print("case 7 (GIT_DIR worktree regression) ok: raw -C call misresolves toplevel under a "
          "live worktree hook's harvested env (pre-fix reproduction); _staged_read.read_staged_bytes "
          "and no_lazy_imports.py both correctly read staged bytes under the identical env "
          "(post-fix)")


def main() -> int:
    case_no_lazy_imports()
    case_max_lines()
    case_link_integrity()
    case_doc_shapes()
    case_doc_attestation_presence()
    case_setup_tui_purity_gate()
    case_git_dir_worktree_regression()
    print("ALL CASES OK -- gates-staged-vs-tree-blindness (ledger row 1234), six converted gates "
          "plus the GIT_DIR-worktree mechanism case, zero residue")
    return 0


if __name__ == "__main__":
    sys.exit(main())
