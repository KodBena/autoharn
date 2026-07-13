#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-13T17:42:09Z
#   last-change: 2026-07-13T17:42:09Z
#   contributors: 3c50e030/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures -- both-polarity live proof for bootstrap/new-project.sh's two fixes landed
under tracker items `scaffold-governed-set-language-default` (ent testbed finding 4, 2026-07-13)
and `scaffold-log-churn-in-subject-repo` (ent-observatory cycle-001, NEW lesson 1):

  1. governed_files.json used to be written as `["*.py"]` UNCONDITIONALLY, silently ungoverning
     any non-Python deployment's real work surface. Fix: `--governed <csv-patterns>` argument;
     absent it, the *.py default is kept but a LOUD post-scaffold notice is printed.
  2. the scaffold never gitignored its own runtime-churn paths (`.claude/logs/`) inside the
     subject repo it stamps, so the invocation log landed git-tracked and churned every session
     (witnessed: picom/.claude/logs against a pristine baseline). Fix: append-if-missing
     `.gitignore` block, written even when the dest dir is not (yet) a git repo.

BOTH POLARITIES, LIVE, NO MOCKS:

  RED  -- the SAME script AT THE MERGE-BASE COMMIT (7097533, before this session's fix) run
          against a throwaway dest dir: no `--governed` flag exists (rejected as an unrecognized
          argument), `.claude/governed_files.json` is written unconditionally as `*.py` with NO
          notice of any kind, and no `.gitignore` is written at all. Extracted via `git show
          <base>:bootstrap/new-project.sh` into a sibling file inside THIS checkout's own
          `bootstrap/` dir (so its relative AUTOHARN_ROOT/TEMPLATES resolution is correct),
          executed, then deleted -- never committed.
  GREEN -- the CURRENT script (this checkout's working tree) run three ways: (a) with
          `--governed`, patterns land verbatim and no notice prints; (b) without `--governed`,
          the *.py default lands AND the loud notice prints; (c) a re-run (`--force`) is
          idempotent on the `.gitignore` block (exactly one marked block, never duplicated).
          Also checks the non-git-dest-dir NOTE branch and the real-git-repo silent branch.

Scratch-only: throwaway tempdirs under the OS temp dir, removed after a clean run (left standing
on any failure, matching this project's standing-probe convention). No live database schemas are
touched at any point -- classic (non `--new-world`) scaffold mode never opens a DB connection at
all, so this fixture needs no scratch schema and no teardown beyond removing directories.

Usage: python3 seen-red/scaffold-governed-and-gitignore/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
BASE_COMMIT = "7097533"  # the merge base this session's fix landed on top of (pre-fix state)
BASE_ARGS = ["--db", "toy", "--host", "192.168.122.1"]


def _run(script: Path, dest: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(script), str(dest), *BASE_ARGS, *extra],
                          capture_output=True, text=True, cwd=str(REPO))


def main() -> int:
    failures: list[str] = []
    tmpdir = Path(tempfile.mkdtemp(prefix="scaffold-governed-fixture-"))

    # ---------------------------------------------------------------- RED: pre-fix script
    old_script = REPO / "bootstrap" / ".scaffold-governed-fixture-old-new-project.sh"
    show = subprocess.run(["git", "show", f"{BASE_COMMIT}:bootstrap/new-project.sh"],
                          capture_output=True, text=True, cwd=str(REPO))
    if show.returncode != 0:
        failures.append(f"RED setup: `git show {BASE_COMMIT}:bootstrap/new-project.sh` failed: "
                        f"{show.stderr}")
        old_script = None
    else:
        old_script.write_text(show.stdout)
        old_script.chmod(0o755)

    try:
        if old_script is not None:
            red_dest = tmpdir / "red-project"
            r = _run(old_script, red_dest, "--schema", "sggfixturered",
                    "--kern", "sggfixturered_kernel", "--role", "sggfixturered_rw",
                    "--governed", "*.sql")
            # pre-fix script has no --governed flag at all -- it must reject this as an
            # unrecognized argument (exit 2), never silently accept it.
            if r.returncode != 2:
                failures.append(f"RED --governed: expected exit 2 (unrecognized argument) on the "
                                f"pre-fix script, got {r.returncode}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
            print(f"RED --governed (pre-fix script rejects the flag): exit={r.returncode} "
                  f"(expect 2) -- {'PASS' if r.returncode == 2 else 'FAIL'}")

            red_dest2 = tmpdir / "red-project-plain"
            r2 = _run(old_script, red_dest2, "--schema", "sggfixturered2",
                     "--kern", "sggfixturered2_kernel", "--role", "sggfixturered2_rw")
            gf = red_dest2 / ".claude" / "governed_files.json"
            gi = red_dest2 / ".gitignore"
            governed_default_only = gf.exists() and gf.read_text().strip() == '{\n  "patterns": ["*.py"]\n}'
            no_notice = "NOTICE" not in r2.stdout and "!!" not in r2.stdout
            no_gitignore = not gi.exists()
            if r2.returncode != 0 or not governed_default_only or not no_notice or not no_gitignore:
                failures.append(
                    f"RED plain run: exit={r2.returncode} governed_default_only={governed_default_only} "
                    f"no_notice={no_notice} no_gitignore={no_gitignore}\nSTDOUT:\n{r2.stdout}")
            print(f"RED plain run (pre-fix: unconditional *.py, no notice, no .gitignore): "
                  f"exit={r2.returncode} default_only={governed_default_only} silent={no_notice} "
                  f"no_gitignore={no_gitignore} -- "
                  f"{'PASS' if r2.returncode == 0 and governed_default_only and no_notice and no_gitignore else 'FAIL'}")
    finally:
        if old_script is not None and old_script.exists():
            old_script.unlink()

    # ---------------------------------------------------------------- GREEN: --governed honored
    green_dest = tmpdir / "green-governed"
    (green_dest).parent.mkdir(parents=True, exist_ok=True)
    green_dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=str(green_dest))  # a real repo -> silent branch
    r = _run(NEW_PROJECT, green_dest, "--schema", "sggfixturegreen",
             "--kern", "sggfixturegreen_kernel", "--role", "sggfixturegreen_rw",
             "--governed", "*.sql,*.tf,Makefile")
    gf = green_dest / ".claude" / "governed_files.json"
    gi = green_dest / ".gitignore"
    patterns_ok = gf.exists() and '"*.sql"' in gf.read_text() and '"*.tf"' in gf.read_text()
    no_notice = "GOVERNED-SET DEFAULT NOTICE" not in r.stdout
    gitignore_ok = gi.exists() and ".claude/logs/" in gi.read_text()
    no_repo_note = "not (yet) a git repo" not in r.stdout
    ok = r.returncode == 0 and patterns_ok and no_notice and gitignore_ok and no_repo_note
    if not ok:
        failures.append(f"GREEN --governed: exit={r.returncode} patterns_ok={patterns_ok} "
                        f"no_notice={no_notice} gitignore_ok={gitignore_ok} no_repo_note={no_repo_note}\n"
                        f"STDOUT:\n{r.stdout}")
    print(f"GREEN --governed (custom patterns, real git repo dest): exit={r.returncode} "
          f"patterns_landed={patterns_ok} notice_suppressed={no_notice} gitignore_landed={gitignore_ok} "
          f"repo_note_suppressed={no_repo_note} -- {'PASS' if ok else 'FAIL'}")

    # ---------------------------------------------------------------- GREEN: default + loud notice
    green_default = tmpdir / "green-default"  # NOT a git repo -- exercises the NOTE branch too
    r = _run(NEW_PROJECT, green_default, "--schema", "sggfixturedef",
             "--kern", "sggfixturedef_kernel", "--role", "sggfixturedef_rw")
    gf = green_default / ".claude" / "governed_files.json"
    gi = green_default / ".gitignore"
    default_only = gf.exists() and gf.read_text().strip() == '{\n  "patterns": ["*.py"]\n}'
    notice_present = "GOVERNED-SET DEFAULT NOTICE" in r.stdout and "*.py files ONLY" in r.stdout
    gitignore_ok = gi.exists() and ".claude/logs/" in gi.read_text()
    repo_note_present = "not (yet) a git repo" in r.stdout
    ok = r.returncode == 0 and default_only and notice_present and gitignore_ok and repo_note_present
    if not ok:
        failures.append(f"GREEN default: exit={r.returncode} default_only={default_only} "
                        f"notice_present={notice_present} gitignore_ok={gitignore_ok} "
                        f"repo_note_present={repo_note_present}\nSTDOUT:\n{r.stdout}")
    print(f"GREEN default (no --governed, non-git dest): exit={r.returncode} default_only={default_only} "
          f"loud_notice_present={notice_present} gitignore_landed={gitignore_ok} "
          f"non_repo_note_present={repo_note_present} -- {'PASS' if ok else 'FAIL'}")

    # ---------------------------------------------------------------- GREEN: idempotent re-run
    gi_before = (green_default / ".gitignore").read_text()
    r = _run(NEW_PROJECT, green_default, "--schema", "sggfixturedef",
             "--kern", "sggfixturedef_kernel", "--role", "sggfixturedef_rw", "--force")
    gi_after = (green_default / ".gitignore").read_text()
    marker_count = gi_after.count("autoharn scaffold-owned churn")
    idempotent = (r.returncode == 0 and gi_before == gi_after and marker_count == 2
                 and "already carries the scaffold-owned churn block" in r.stdout)
    if not idempotent:
        failures.append(f"GREEN idempotent re-run: exit={r.returncode} unchanged={gi_before == gi_after} "
                        f"marker_count={marker_count}\nSTDOUT:\n{r.stdout}")
    print(f"GREEN idempotent re-run (--force): exit={r.returncode} gitignore_unchanged={gi_before == gi_after} "
          f"marker_pairs=1 (count={marker_count}) -- {'PASS' if idempotent else 'FAIL'}")

    if failures:
        print("\n=== FAILURES ===")
        for f in failures:
            print(f"- {f}")
        print(f"\nScratch dirs left standing for inspection: {tmpdir}")
        return 1

    shutil.rmtree(tmpdir, ignore_errors=True)
    print("\nAll cases PASS; scratch dirs removed (zero residue).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
