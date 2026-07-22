#!/usr/bin/env python3
"""run_fixtures.py — both-polarity proof for vestigial_documentation/design/ORCH-WORKTREE-LEDGERING.md 3a's two merge
drivers (`tools/merge_jsonl.py`, `tools/merge_backlog_sections.py`), driven through REAL `git merge`
in a throwaway git repo (never this repo's own history; scrubbed in `finally`).

THREE CASES:

  case_jsonl_union (GREEN): two branches, diverging from one base `attestations/*.jsonl` file, each
    APPEND a different new line. `git merge` (using the real, installed `jsonl-union` driver) resolves
    with NO conflict, exit 0, and the merged file is the exact union of base+A's line+B's line, in
    the order the memo specifies (current's lines, then other's novel lines). This is the append-
    append conflict a bare/default git merge normally CANNOT resolve without a custom driver (both
    sides changed the same neighborhood -- end of file -- with no common anchor); the driver is what
    makes it mechanical.

  case_backlog_union (GREEN): the identical append-append shape one level up, on BACKLOG.md's dated
    `## ` sections: two branches each add a DIFFERENT new dated section (no overlap with each other
    or with any existing section). `git merge` (using the real `backlog-section-union` driver)
    resolves with NO conflict, exit 0, and the merged file carries every original section plus both
    new ones.

  case_backlog_conflict (RED): two branches both EDIT the SAME pre-existing dated section's body,
    differently. `git merge` REFUSES (non-zero exit), leaves real git-shaped conflict markers
    (`<<<<<<< `/`=======`/`>>>>>>> `) in BACKLOG.md, and -- proven here, not merely asserted --
    `gates/no_conflict_markers.py` independently catches those markers in the staged diff, exactly
    as it would for a human who force-committed over them (BELT-AND-BRACES: this driver's own exit
    code already refuses the merge before it reaches that point; the gate is the second net).

THE JSONL DRIVER HAS NO RED CASE, BY DESIGN, NAMED HERE RATHER THAN LEFT IMPLICIT: an append-only
line-set union cannot conflict (tools/merge_jsonl.py's own docstring, "THE ALGORITHM") -- there is no
"NON-appendable" shape for one immutable jsonl line the way there is for a prose section that can
legitimately be edited in place. Manufacturing a fake red case for it would be asserting a hazard the
driver's own design forecloses, the acronym-gate mistake ADR-0017's Context warns against (a
mechanism that "cries wolf"); the honest-limits section vestigial_documentation/design/ORCH-WORKTREE-LEDGERING.md §4 already
states this boundary, and this fixture matches it rather than papering over it with a contrived case.

Run: python3 seen-red/worktree-ledgering/run_fixtures.py
Exit 0 iff every case matches its expected polarity; 1 otherwise. Zero residue: every throwaway repo
lives under a `tempfile.TemporaryDirectory`, scrubbed on the way out regardless of outcome.
Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MERGE_JSONL = REPO / "tools" / "merge_jsonl.py"
MERGE_BACKLOG = REPO / "tools" / "merge_backlog_sections.py"
NO_CONFLICT_MARKERS_GATE = REPO / "gates" / "no_conflict_markers.py"
_MARKER_RE = re.compile(r"^(<{7}|>{7})( |$)", re.MULTILINE)


def run(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), cwd=str(cwd), capture_output=True, text=True)


def init_repo(tmp: Path) -> Path:
    repo = tmp / "repo"
    repo.mkdir()
    run(repo, "git", "init", "-q")
    run(repo, "git", "config", "user.email", "fixture@example.invalid")
    run(repo, "git", "config", "user.name", "fixture")
    (repo / ".gitattributes").write_text(
        "attestations/*.jsonl merge=jsonl-union\n"
        "BACKLOG.md merge=backlog-section-union\n")
    run(repo, "git", "config", "merge.jsonl-union.name", "union merge driver for append-only jsonl")
    run(repo, "git", "config", "merge.jsonl-union.driver",
        f"{sys.executable} {MERGE_JSONL} %O %A %B")
    run(repo, "git", "config", "merge.backlog-section-union.name",
        "dated-section union merge driver for BACKLOG.md")
    run(repo, "git", "config", "merge.backlog-section-union.driver",
        f"{sys.executable} {MERGE_BACKLOG} %O %A %B")
    return repo


def commit_all(repo: Path, message: str) -> None:
    run(repo, "git", "add", "-A")
    run(repo, "git", "commit", "-q", "-m", message)


def case_jsonl_union() -> list[str]:
    errs: list[str] = []
    with tempfile.TemporaryDirectory(prefix="wtl-jsonl-") as tmpdir:
        tmp = Path(tmpdir)
        repo = init_repo(tmp)
        attestations = repo / "attestations"
        attestations.mkdir()
        (attestations / "sample.jsonl").write_text(
            '{"n": "base-1"}\n{"n": "base-2"}\n')
        commit_all(repo, "base: two jsonl lines")

        run(repo, "git", "checkout", "-q", "-b", "worktree-a")
        with open(attestations / "sample.jsonl", "a") as f:
            f.write('{"n": "a-appended"}\n')
        commit_all(repo, "worktree-a: append one line")

        run(repo, "git", "checkout", "-q", "master")
        run(repo, "git", "checkout", "-q", "-b", "worktree-b")
        with open(attestations / "sample.jsonl", "a") as f:
            f.write('{"n": "b-appended"}\n')
        commit_all(repo, "worktree-b: append a DIFFERENT line")

        run(repo, "git", "checkout", "-q", "worktree-a")
        merge = run(repo, "git", "merge", "--no-edit", "worktree-b")
        if merge.returncode != 0:
            errs.append(f"jsonl-union merge FAILED (expected clean): {merge.stdout} {merge.stderr}")
            return errs
        merged = (attestations / "sample.jsonl").read_text()
        expected_lines = ['{"n": "base-1"}', '{"n": "base-2"}',
                           '{"n": "a-appended"}', '{"n": "b-appended"}']
        actual_lines = merged.splitlines()
        if actual_lines != expected_lines:
            errs.append(f"jsonl union content mismatch: expected {expected_lines}, "
                        f"got {actual_lines}")
        status = run(repo, "git", "status", "--porcelain")
        if status.stdout.strip():
            errs.append(f"merge left an unclean working tree: {status.stdout}")
        print(f"  case_jsonl_union: merge exit={merge.returncode}, lines={actual_lines}")
    return errs


def case_backlog_union() -> list[str]:
    errs: list[str] = []
    with tempfile.TemporaryDirectory(prefix="wtl-backlog-union-") as tmpdir:
        tmp = Path(tmpdir)
        repo = init_repo(tmp)
        base_backlog = (
            "# fixture backlog\n\n"
            "preamble text.\n\n"
            "## 2026-01-01: Existing entry A\n\n"
            "Original body of A.\n\n"
            "## 2026-01-02: Existing entry B\n\n"
            "Original body of B.\n")
        (repo / "BACKLOG.md").write_text(base_backlog)
        commit_all(repo, "base: two dated sections")

        run(repo, "git", "checkout", "-q", "-b", "worktree-a")
        with open(repo / "BACKLOG.md", "a") as f:
            f.write("\n## 2026-01-03: A's new entry\n\nBody added by worktree-a.\n")
        commit_all(repo, "worktree-a: append a new dated section")

        run(repo, "git", "checkout", "-q", "master")
        run(repo, "git", "checkout", "-q", "-b", "worktree-b")
        with open(repo / "BACKLOG.md", "a") as f:
            f.write("\n## 2026-01-04: B's new entry\n\nBody added by worktree-b.\n")
        commit_all(repo, "worktree-b: append a DIFFERENT new dated section")

        run(repo, "git", "checkout", "-q", "worktree-a")
        merge = run(repo, "git", "merge", "--no-edit", "worktree-b")
        if merge.returncode != 0:
            errs.append(f"backlog-section-union merge FAILED (expected clean): "
                        f"{merge.stdout} {merge.stderr}")
            return errs
        merged = (repo / "BACKLOG.md").read_text()
        for needle in ("## 2026-01-01: Existing entry A", "## 2026-01-02: Existing entry B",
                       "## 2026-01-03: A's new entry", "## 2026-01-04: B's new entry",
                       "Body added by worktree-a.", "Body added by worktree-b."):
            if needle not in merged:
                errs.append(f"backlog union missing expected content: {needle!r}")
        if _MARKER_RE.search(merged):
            errs.append("backlog union left conflict markers on a supposedly-clean merge")
        status = run(repo, "git", "status", "--porcelain")
        if status.stdout.strip():
            errs.append(f"merge left an unclean working tree: {status.stdout}")
        print(f"  case_backlog_union: merge exit={merge.returncode}, "
             f"sections present: 4/4, no markers")
    return errs


def case_backlog_conflict() -> tuple[list[str], str]:
    """Returns (errors, captured-red-output) -- the red output is banked to red.txt by main()."""
    errs: list[str] = []
    captured = []
    with tempfile.TemporaryDirectory(prefix="wtl-backlog-conflict-") as tmpdir:
        tmp = Path(tmpdir)
        repo = init_repo(tmp)
        base_backlog = (
            "# fixture backlog\n\n"
            "preamble text.\n\n"
            "## 2026-02-01: Shared entry\n\n"
            "Original body line 1.\n")
        (repo / "BACKLOG.md").write_text(base_backlog)
        commit_all(repo, "base: one shared dated section")

        run(repo, "git", "checkout", "-q", "-b", "edit-a")
        (repo / "BACKLOG.md").write_text(
            "# fixture backlog\n\npreamble text.\n\n"
            "## 2026-02-01: Shared entry\n\nA's edited body line 1.\n")
        commit_all(repo, "edit-a: reword the shared section")

        run(repo, "git", "checkout", "-q", "master")
        run(repo, "git", "checkout", "-q", "-b", "edit-b")
        (repo / "BACKLOG.md").write_text(
            "# fixture backlog\n\npreamble text.\n\n"
            "## 2026-02-01: Shared entry\n\nB's DIFFERENTLY edited body line 1.\n")
        commit_all(repo, "edit-b: reword the SAME shared section, differently")

        run(repo, "git", "checkout", "-q", "edit-a")
        merge = run(repo, "git", "merge", "--no-edit", "edit-b")
        captured.append(f"$ git merge --no-edit edit-b\n{merge.stdout}{merge.stderr}"
                        f"\n(exit {merge.returncode})")
        if merge.returncode == 0:
            errs.append("backlog-section-union merge SUCCEEDED on a same-section double-edit "
                       "(expected a loud failure)")
            return errs, "\n".join(captured)
        merged = (repo / "BACKLOG.md").read_text()
        if not _MARKER_RE.search(merged):
            errs.append(f"expected conflict markers in BACKLOG.md, found none: {merged!r}")
        for needle in ("A's edited body line 1.", "B's DIFFERENTLY edited body line 1."):
            if needle not in merged:
                errs.append(f"conflict block missing one side's content: {needle!r}")
        captured.append(f"--- BACKLOG.md after the refused merge ---\n{merged}")

        # BELT-AND-BRACES: the same conflicted state is independently catchable by
        # gates/no_conflict_markers.py, run against THIS throwaway repo's own staged diff (never
        # this project's own repo -- run() executes with cwd=repo throughout).
        run(repo, "git", "add", "-A")  # stage the conflicted file, as a human about to force-commit would
        gate = run(repo, sys.executable, str(NO_CONFLICT_MARKERS_GATE))
        captured.append(f"$ python3 gates/no_conflict_markers.py (run against the conflicted "
                        f"staged state)\n{gate.stdout}{gate.stderr}\n(exit {gate.returncode})")
        if gate.returncode == 0:
            errs.append("gates/no_conflict_markers.py did NOT catch the unresolved conflict "
                       "markers left by the refused merge")
        print(f"  case_backlog_conflict: merge exit={merge.returncode} (refused, as expected), "
             f"markers present, gates/no_conflict_markers.py exit={gate.returncode} (refused, "
             f"as expected)")
    return errs, "\n".join(captured)


def main() -> int:
    failures: list[str] = []

    print("=== case_jsonl_union (GREEN) ===")
    failures += [f"jsonl_union: {e}" for e in case_jsonl_union()]

    print("=== case_backlog_union (GREEN) ===")
    failures += [f"backlog_union: {e}" for e in case_backlog_union()]

    print("=== case_backlog_conflict (RED) ===")
    conflict_errs, red_output = case_backlog_conflict()
    failures += [f"backlog_conflict: {e}" for e in conflict_errs]

    # The captured output below legitimately QUOTES real git conflict markers (this fixture's own
    # RED evidence) -- indented four spaces so no line BEGINS with the marker shape
    # gates/no_conflict_markers.py's own regex keys on (`^\+(<{7}|>{7})( |$)` on the staged diff),
    # exactly the deliberate-quoting escape that gate's own docstring/teach-text names. Un-indented,
    # this file would refuse ITS OWN commit -- verified live: the first version of this file, before
    # this indent, was caught by that exact gate when staged.
    indented_red_output = "\n".join("    " + line for line in red_output.splitlines())
    here = Path(__file__).resolve().parent
    (here / "red.txt").write_text(
        "# Banked red evidence: seen-red/worktree-ledgering/run_fixtures.py::case_backlog_conflict\n"
        "# A same-section double-edit across two branches; the backlog-section-union driver\n"
        "# refuses the merge (non-zero exit), leaves real git conflict markers in BACKLOG.md, and\n"
        "# gates/no_conflict_markers.py independently catches them in the staged diff.\n"
        "# (Every line below is indented 4 spaces -- a deliberate quote of the markers, per\n"
        "# gates/no_conflict_markers.py's own documented escape for quoting rather than committing\n"
        "# a marker; see that gate's module docstring.)\n\n"
        + indented_red_output + "\n")

    if failures:
        print(f"\n{len(failures)} FAILURE(S):")
        for f in failures:
            print(f"  !! {f}")
        return 1
    print("\nALL CASES OK -- worktree-ledgering 3a: both drivers proven (jsonl-union always-clean "
         "union; backlog-section-union clean-union on non-overlapping appends, loud refusal + "
         "gate-catchable markers on a same-section double-edit). Zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
