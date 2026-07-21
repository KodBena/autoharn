#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-21T21:50:25Z
#   last-change: 2026-07-21T21:51:16Z
#   contributors: 43f77bff/main
# <<< PROVENANCE-STAMP <<<

"""seen-red/setup-tui-destination-foreign-refusal/run_fixtures.py -- spec §5's third witness-set
item, second closed defect: "new-project.sh merging into FOREIGN content (red leg in a scratch
dir)". Census-registered in gates/fixture_census.py.

design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md §1(a): `bootstrap/new-project.sh` `mkdir -p`s
and merges into ANY occupied directory that lacks `deployment.json`, silently. This fixture pins
`bootstrap/new-project.sh` AS IT STOOD at commit a9d779f (this build's own base commit -- the
same PRE_FIX_COMMIT seen-red/setup-tui-destination-birth-guard/run_fixtures.py pins, both being
"the last commit before this build touched the relevant file"), runs it against a REAL, on-disk,
non-empty scratch directory carrying no autoharn birth evidence (FOREIGN), and shows it writes
deployment.json into it anyway (RED, exit 0, silent merge); the current script refuses (exit
nonzero, nothing written) unless `--accept-existing-content` is given, in which case it merges
explicitly (GREEN, both polarities of the new flag).

CLASSIC (`--schema/--kern/--role`) mode is used deliberately, NOT `--new-world`: classic mode
invokes no `psql` at all (grep the script -- every `psql` call is inside `if [ -n "$NEW_WORLD"
]`), so this fixture needs no live Postgres and runs in well under a second. The FOREIGN-content
refusal gate sits BEFORE any DB-touching code path either way (right before `mkdir -p "$DEST"`),
so classic mode exercises the identical gate `--new-world` mode would.

Zero mocks (the real scripts, real subprocess, real filesystem), zero residue (tmpdir rmtree in
`finally`). Lazy imports banned."""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PRE_FIX_COMMIT = "a9d779f"  # see seen-red/setup-tui-destination-birth-guard's own note: this
# build's base commit, the last one before the FOREIGN-refusal gate was added.

ARGS = ["--db", "toy", "--host", "192.0.2.1", "--schema", "scratchschema",
        "--kern", "scratchschema_kernel", "--role", "scratchschema_rw"]


def _pinned_new_project_sh() -> str:
    """Written INSIDE bootstrap/ (not a scratch tmpdir) -- the pinned script's own
    `AUTOHARN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"` line resolves relative to $0's own
    location, so a copy living outside bootstrap/ would compute the WRONG root (a tmpdir, not
    this checkout) and fail before ever reaching the classification gate under test. Untracked,
    dot-prefixed, removed in `finally` -- never committed, never mistaken for a real script by
    any other gate that scans bootstrap/ (name does not match new-project*.sh)."""
    r = subprocess.run(
        ["git", "-C", REPO, "show", f"{PRE_FIX_COMMIT}:bootstrap/new-project.sh"],
        capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip(), (
        f"could not read {PRE_FIX_COMMIT}:bootstrap/new-project.sh -- {r.stderr}")
    assert "--accept-existing-content" not in r.stdout, (
        f"fixture assumption stale: {PRE_FIX_COMMIT}:bootstrap/new-project.sh ALREADY carries "
        f"--accept-existing-content -- PRE_FIX_COMMIT needs repinning to a genuinely earlier "
        f"commit")
    path = os.path.join(REPO, "bootstrap", ".new-project-prefix-scratch.sh")
    with open(path, "w", encoding="utf-8") as f:
        f.write(r.stdout)
    os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
    return path


def _mk_foreign(tmp: str, name: str) -> str:
    d = os.path.join(tmp, name)
    os.makedirs(d)
    with open(os.path.join(d, "README.md"), "w", encoding="utf-8") as f:
        f.write("some pre-existing project, not autoharn's\n")
    return d


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="setup-tui-destination-foreign-refusal-")
    prefix_sh = None
    ok = True
    try:
        # --- RED: the pinned pre-fix script merges into FOREIGN content silently ---
        prefix_sh = _pinned_new_project_sh()
        red_dest = _mk_foreign(tmp, "red_dest")
        r = subprocess.run([prefix_sh, red_dest] + ARGS, capture_output=True, text=True)
        deployment_written_red = os.path.isfile(os.path.join(red_dest, "deployment.json"))
        assert r.returncode == 0, (
            f"RED setup failed: pre-fix new-project.sh was expected to SUCCEED (silent merge) "
            f"against FOREIGN content -- exit {r.returncode}, stderr: {r.stderr[-2000:]}")
        assert deployment_written_red, (
            "RED setup failed: pre-fix new-project.sh exited 0 but did not write "
            "deployment.json -- fixture assumption stale?")
        print("case RED ok: pre-fix new-project.sh merges into FOREIGN content silently "
              "(exit 0, deployment.json written into pre-existing, unrelated content) -- "
              "reproducing the closed defect")

        # --- GREEN leg 1: the current script refuses, without --accept-existing-content ---
        current_sh = os.path.join(REPO, "bootstrap", "new-project.sh")
        green_dest_refused = _mk_foreign(tmp, "green_dest_refused")
        r = subprocess.run([current_sh, green_dest_refused] + ARGS, capture_output=True, text=True)
        deployment_written_refused = os.path.isfile(
            os.path.join(green_dest_refused, "deployment.json"))
        assert r.returncode != 0, (
            f"GREEN leg 1: current new-project.sh must REFUSE (nonzero exit) against "
            f"unacknowledged FOREIGN content -- got exit 0")
        assert not deployment_written_refused, (
            "GREEN leg 1: current new-project.sh must write NOTHING when it refuses -- "
            "deployment.json was written anyway")
        assert "FOREIGN" in r.stderr or "accept-existing-content" in r.stderr, (
            f"GREEN leg 1: refusal must teach the flag name -- stderr: {r.stderr}")
        print("case GREEN leg 1 ok: current new-project.sh refuses FOREIGN content "
              "(nonzero exit, nothing written, refusal names --accept-existing-content)")

        # --- GREEN leg 2: --accept-existing-content scaffolds explicitly ---
        green_dest_accepted = _mk_foreign(tmp, "green_dest_accepted")
        r = subprocess.run(
            [current_sh, green_dest_accepted] + ARGS + ["--accept-existing-content"],
            capture_output=True, text=True)
        deployment_written_accepted = os.path.isfile(
            os.path.join(green_dest_accepted, "deployment.json"))
        sentinel_written_accepted = os.path.isfile(
            os.path.join(green_dest_accepted, ".autoharn-world.json"))
        assert r.returncode == 0, (
            f"GREEN leg 2: current new-project.sh with --accept-existing-content must succeed -- "
            f"exit {r.returncode}, stderr: {r.stderr[-2000:]}")
        assert deployment_written_accepted, (
            "GREEN leg 2: --accept-existing-content must actually scaffold -- "
            "deployment.json missing")
        assert sentinel_written_accepted, (
            "GREEN leg 2: the .autoharn-world.json sentinel (spec §2) must be written "
            "alongside deployment.json")
        # the README.md that made this dir FOREIGN in the first place must survive the merge
        # (an explicit accept merges INTO existing content, it does not wipe it).
        assert os.path.isfile(os.path.join(green_dest_accepted, "README.md")), (
            "GREEN leg 2: the pre-existing FOREIGN content must survive an accepted merge")
        print("case GREEN leg 2 ok: --accept-existing-content scaffolds explicitly -- "
              "deployment.json + sentinel written, pre-existing content survives")

        print("ALL CASES OK -- new-project.sh's FOREIGN-content refusal, red before green, "
              "pinned pre-fix script vs current, classic mode (no live Postgres needed), "
              "zero mocks")
    except AssertionError as exc:
        print(f"FAILED: {exc}")
        ok = False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        if prefix_sh and os.path.isfile(prefix_sh):
            os.remove(prefix_sh)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
