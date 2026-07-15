#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T19:30:37Z
#   last-change: 2026-07-15T19:30:37Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for ../../orchlog (ledger item
orchlog-changelog-verb). Real infra, no mocks: a throwaway scratch git repository under this
process's own temp dir, torn down before AND after this file runs so re-running it never
leaves residue. Uses orchlog's own `--repo PATH` flag (added for exactly this purpose) to
point the real verb at the scratch repo instead of this one.

Cases (matching the brief's own both-polarity spec):
  green-since-shows-and-hides -- a note lands in commit N (orchlog.d/some-note.md, tracked
                                  via `git ls-files`). `orchlog --repo SCRATCH since <N-1>`
                                  lists it (it landed after N-1); `orchlog --repo SCRATCH
                                  since <N>` does NOT list it (N is not strictly after
                                  itself -- the note's adding commit IS N, ancestor-or-equal
                                  of N, so it is excluded by the since filter's own stated
                                  rule).
  red-invalid-commit-ish       -- an unresolvable commit-ish is REFUSED loudly with
                                  teach-text on stderr, exit nonzero (never a silent empty
                                  list, and never exit 0).

Usage: python3 seen-red/orchlog-since-filter/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ORCHLOG = REPO / "orchlog"


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return sh(["git", "-C", str(repo)] + list(args))


def orchlog(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return sh([sys.executable, str(ORCHLOG), "--repo", str(repo), *args])


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="orchlog-seenred-"))
    scratch_repo = tmp / "scratch-repo"
    scratch_repo.mkdir()
    failures: list[str] = []

    try:
        git(scratch_repo, "init", "-q")
        git(scratch_repo, "config", "user.email", "seenred@example.invalid")
        git(scratch_repo, "config", "user.name", "seen-red fixture")

        # commit N-1: an unrelated commit, no note.
        (scratch_repo / "README.md").write_text("scratch fixture repo\n", encoding="utf-8")
        git(scratch_repo, "add", "README.md")
        git(scratch_repo, "commit", "-q", "-m", "initial commit, no orchlog note")
        n_minus_1 = git(scratch_repo, "rev-parse", "HEAD").stdout.strip()

        # commit N: adds the one orchlog.d note this fixture proves both polarities on.
        (scratch_repo / "orchlog.d").mkdir()
        (scratch_repo / "orchlog.d" / "fixture-note.md").write_text(
            "subject: deadbeef\n\nfixture note body, first line.\n", encoding="utf-8"
        )
        git(scratch_repo, "add", "orchlog.d/fixture-note.md")
        git(scratch_repo, "commit", "-q", "-m", "orchlog.d: add fixture-note")
        n = git(scratch_repo, "rev-parse", "HEAD").stdout.strip()

        # --- green: since N-1 shows the note ------------------------------------------------
        r_before = orchlog(scratch_repo, "since", n_minus_1)
        shows_it = ("fixture-note.md" in r_before.stdout) and (n[:12] in r_before.stdout)
        ok_before = r_before.returncode == 0 and shows_it
        check("green-since-n-minus-1-shows-note", ok_before,
              f"exit={r_before.returncode} shown={shows_it}", failures)

        # --- green: since N (the note's own adding commit) hides it (ancestor-or-equal) -----
        r_at = orchlog(scratch_repo, "since", n)
        hides_it = "fixture-note.md" not in r_at.stdout
        ok_at = r_at.returncode == 0 and hides_it
        check("green-since-n-hides-note", ok_at,
              f"exit={r_at.returncode} hidden={hides_it} stdout={r_at.stdout.strip()!r}",
              failures)

        # --- red: an unresolvable commit-ish is refused loudly, never a silent empty list ---
        r_bad = orchlog(scratch_repo, "since", "totally-not-a-real-commit-ish-xyz")
        refused = (
            r_bad.returncode != 0
            and "REFUSED" in r_bad.stderr
            and "usage:" in r_bad.stderr
        )
        check("red-invalid-commit-ish-refused", refused,
              f"exit={r_bad.returncode} stderr={r_bad.stderr.strip()!r}", failures)

        # --- listing with no args shows the note too, newest-first --------------------------
        r_list = orchlog(scratch_repo)
        ok_list = r_list.returncode == 0 and "fixture-note.md" in r_list.stdout
        check("plain-list-shows-note", ok_list, f"exit={r_list.returncode}", failures)

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print(f"FAILURES: {failures}")
        return 1
    print("ALL CASES OK -- orchlog both-polarity proof (since-filter green/green, "
          "invalid-commit-ish red), zero residue (tmp dir removed).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
