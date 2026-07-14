#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T21:26:05Z
#   last-change: 2026-07-14T21:27:53Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures -- both-polarity live proof for tracker item `deployment-live-exec-coupling`
(design/ORCH-DEPLOYMENT-PINNING.md; maintainer commission 2026-07-14 late, "git submodule
DEPLOYMENT must be IDIOT-PROOF"): the three scripts that convert a deployment's operator verbs
+ hook wiring from "live-exec out of a shared checkout" to "pinned at a git submodule commit,
upgraded only by an explicit act":

  - bootstrap/new-project.sh --pin submodule   (the NEW-deployment path)
  - bootstrap/convert-to-submodule.sh          (the CONVERSION path for an EXISTING deployment)
  - bootstrap/upgrade-submodule.sh             (the UPGRADE verb -- bump the pin deliberately)
  - bootstrap/live_session_check.py            (the shared "never run against a live session" gate)

REAL GIT, REAL SUBMODULE, NO MOCKS (per this build's own commission): every case below runs the
actual scripts against actual `git` (submodule add/checkout/commit/fetch), an actual scratch
throwaway deployment directory, and the REAL toy postgres (192.168.122.1/toy) for the smoke-test
step -- never a stub or a monkeypatched subprocess.

WHY A CLEAN WORKTREE, NOT `REPO` DIRECTLY: `--pin submodule` (and the conversion/upgrade scripts'
own dirty-checkout refusal) require the autoharn checkout being pinned to be CLEAN (a dirty
checkout cannot be reproduced from its SHA alone) -- but THIS checkout, mid-session, routinely has
uncommitted work in flight (other agents' staged changes, this build's own edits). So this fixture
stands up a throwaway `git worktree` at REPO's current HEAD, copies the CURRENT on-disk bytes of
the four scripts above into it (so the fixture always exercises what is actually on disk right
now, not a stale HEAD), commits them there (a scratch commit, never touching REPO's own history),
and uses THAT worktree as the "autoharn checkout" every case pins against. The worktree, every
scaffolded deployment dir, and every DB schema/role this run creates are dropped at the end
(left standing only on failure, matching this project's standing-probe convention).

Cases (RED = the refusal is the point; GREEN = the mechanism must work end to end):
  RED   1. --pin <bogus>                          refused, exit 2, teaches the one valid value
  RED   2. --pin submodule + --new-world           refused, exit 2, teaches the scope split
  RED   3. --pin submodule against a DIRTY source  refused, exit 1, teaches commit-or-stash
  GREEN 4. --pin submodule, clean source            .autoharn added+pinned, 8 shims resolve into
                                                     it, settings.json hooks repointed, real
                                                     ./led decision + --recent round-trip through
                                                     the pin against real postgres
  GREEN 5. convert-to-submodule.sh on a classic
           (live-exec) deployment                   converts correctly, 0 leftover references to
                                                     the old root, real ./led round-trip
  RED   6. convert-to-submodule.sh, already pinned  refused, exit 1, nothing touched
  RED   7. convert-to-submodule.sh, LIVE SESSION    refused (real background process, cwd inside
                                                     the target dir), .autoharn never created
  GREEN 8. upgrade-submodule.sh, real new commit    fetch + checkout + commit succeed, real
                                                     ./led round-trip on the new pin
  RED   9. upgrade-submodule.sh, bogus SHA           refused after a real fetch, nothing touched
  RED  10. upgrade-submodule.sh, LIVE SESSION        refused, pin unchanged
  RED  11. upgrade-submodule.sh, not yet pinned      refused, teaches to convert first

Usage: python3 seen-red/deployment-pinning/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
CONVERT = REPO / "bootstrap" / "convert-to-submodule.sh"
UPGRADE = REPO / "bootstrap" / "upgrade-submodule.sh"
LIVE_CHECK = REPO / "bootstrap" / "live_session_check.py"
PINNING_SCRIPTS = [
    ("bootstrap/new-project.sh", NEW_PROJECT),
    ("bootstrap/convert-to-submodule.sh", CONVERT),
    ("bootstrap/upgrade-submodule.sh", UPGRADE),
    ("bootstrap/live_session_check.py", LIVE_CHECK),
]

DB = "toy"
HOST = "192.168.122.1"
STAMP = str(int(time.time()))[-6:]  # short, run-unique DB name suffix -- avoids collisions
                                     # between concurrent fixture runs without a coordination
                                     # mechanism (ADR-0012 P1: one cheap fix, not a lock server)


def _sh(cmd: list[str], cwd: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd), env=full_env)


def _git(worktree: Path, *args: str) -> subprocess.CompletedProcess:
    return _sh(["git", *args], cwd=worktree)


def _commit_in_worktree(worktree: Path, paths: list[str], message: str) -> subprocess.CompletedProcess:
    _git(worktree, "add", *paths)
    return _sh(["git", "commit", "--quiet", "-m", message], cwd=worktree,
               env={"CLAUDE_COMMIT_PATHS": " ".join(paths),
                    "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "fixture@local",
                    "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "fixture@local"})


def _psql(sql: str) -> subprocess.CompletedProcess:
    return subprocess.run(["psql", "-h", HOST, "-d", DB, "-v", "ON_ERROR_STOP=1", "-c", sql],
                          capture_output=True, text=True)


def _apply_light_kernel(worktree: Path, schema: str, kern: str, role: str) -> subprocess.CompletedProcess:
    """The minimum kernel lineage (high_watermark_1 + s20 + s21) needed for `led decision` /
    `led --recent` to round-trip against real postgres -- classic (non --new-world) scaffold mode
    never applies a kernel itself, and this fixture wants a REAL smoke test, not just a path check."""
    _psql(f'DROP ROLE IF EXISTS {role};')
    _psql(f'CREATE ROLE {role} LOGIN;')
    return subprocess.run(
        ["psql", "-h", HOST, "-d", DB, "-v", "ON_ERROR_STOP=1",
         "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}",
         "-f", str(worktree / "kernel" / "lineage" / "high_watermark_1.sql"),
         "-f", str(worktree / "kernel" / "lineage" / "s20-obligation-grants-and-view-refresh.sql"),
         "-f", str(worktree / "kernel" / "lineage" / "s21-session-aware-distinctness.sql")],
        capture_output=True, text=True)


def _drop_schema_role(schema: str, kern: str, role: str) -> None:
    _psql(f'DROP SCHEMA IF EXISTS {schema} CASCADE;')
    _psql(f'DROP SCHEMA IF EXISTS {kern} CASCADE;')
    _psql(f'DROP ROLE IF EXISTS {role};')


def main() -> int:
    failures: list[str] = []
    tmproot = Path(tempfile.mkdtemp(prefix="deployment-pinning-fixture-"))
    worktree = tmproot / "autoharn-src"
    ok_overall = True
    schemas_to_drop: list[tuple[str, str, str]] = []

    def check(label: str, cond: bool, detail: str = "") -> None:
        nonlocal ok_overall
        status = "PASS" if cond else "FAIL"
        print(f"{label}: {status}" + (f"\n{detail}" if detail and not cond else ""))
        if not cond:
            failures.append(f"{label}\n{detail}")
            ok_overall = False

    try:
        # ------------------------------------------------------------ scratch worktree setup
        r = _git(REPO, "worktree", "add", "--detach", str(worktree), "HEAD")
        if r.returncode != 0:
            check("SETUP: git worktree add", False, r.stderr)
            return 1
        rel_paths = []
        for rel, src in PINNING_SCRIPTS:
            dst = worktree / rel
            dst.write_bytes(src.read_bytes())
            dst.chmod(0o755)
            rel_paths.append(rel)
        cm = _commit_in_worktree(worktree, rel_paths,
                                 "fixture: current pinning scripts (deployment-pinning run_fixtures.py, scratch worktree)")
        if cm.returncode != 0:
            check("SETUP: commit current scripts into scratch worktree", False, cm.stdout + cm.stderr)
            return 1
        base_sha = _git(worktree, "rev-parse", "HEAD").stdout.strip()
        print(f"-- scratch worktree {worktree} at {base_sha} (current pinning scripts committed) --")

        # ============================================================ RED 1: --pin <bogus>
        dest = tmproot / "red1"
        r = _sh(["bash", str(worktree / "bootstrap" / "new-project.sh"), str(dest),
                "--db", DB, "--host", HOST, "--schema", f"dpf{STAMP}r1",
                "--kern", f"dpf{STAMP}r1_kernel", "--role", f"dpf{STAMP}r1_rw",
                "--pin", "copy"], cwd=worktree)
        check("RED 1 (--pin copy is refused, only 'submodule' supported)",
              r.returncode == 2 and "not a recognized value" in r.stderr, r.stdout + r.stderr)

        # ============================================================ RED 2: --pin + --new-world
        dest = tmproot / "red2"
        r = _sh(["bash", str(worktree / "bootstrap" / "new-project.sh"), str(dest),
                "--new-world", f"dpf{STAMP}r2", "--db", DB, "--host", HOST,
                "--pin", "submodule"], cwd=worktree)
        check("RED 2 (--pin submodule + --new-world is refused)",
              r.returncode == 2 and "cannot be combined with --new-world" in r.stderr, r.stdout + r.stderr)

        # ============================================================ RED 3: dirty source
        # The dirty check is `git diff --quiet && git diff --cached --quiet` (tracked-file
        # modifications) -- an UNTRACKED new file does not trip it, so this must modify a file
        # already tracked in the worktree (one of the four scripts just committed there).
        dirty_target = worktree / "bootstrap" / "new-project.sh"
        original = dirty_target.read_bytes()
        dirty_target.write_bytes(original + b"\n# fixture dirty marker\n")
        dest = tmproot / "red3"
        r = _sh(["bash", str(worktree / "bootstrap" / "new-project.sh"), str(dest),
                "--db", DB, "--host", HOST, "--schema", f"dpf{STAMP}r3",
                "--kern", f"dpf{STAMP}r3_kernel", "--role", f"dpf{STAMP}r3_rw",
                "--pin", "submodule"], cwd=worktree)
        dirty_target.write_bytes(original)
        check("RED 3 (--pin submodule refuses a DIRTY autoharn source)",
              r.returncode == 1 and "DIRTY" in r.stderr and not dest.exists(), r.stdout + r.stderr)

        # ============================================================ GREEN 4: --pin submodule
        dest4 = tmproot / "green4-newdeploy"
        schema4, kern4, role4 = f"dpf{STAMP}g4", f"dpf{STAMP}g4_kernel", f"dpf{STAMP}g4_rw"
        r = _sh(["bash", str(worktree / "bootstrap" / "new-project.sh"), str(dest4),
                "--db", DB, "--host", HOST, "--schema", schema4, "--kern", kern4, "--role", role4,
                "--name", f"dpf{STAMP}g4", "--governed", "*.py", "--pin", "submodule"], cwd=worktree)
        autoharn_dir = dest4 / ".autoharn"
        led_shim = dest4 / "led"
        shim_ok = led_shim.exists() and str(autoharn_dir) in led_shim.read_text()
        settings_ok = (dest4 / ".claude" / "settings.json").exists() and \
            str(worktree) not in (dest4 / ".claude" / "settings.json").read_text() and \
            str(autoharn_dir / "hooks") in (dest4 / ".claude" / "settings.json").read_text()
        pin_sha = _git(autoharn_dir, "rev-parse", "HEAD").stdout.strip() if autoharn_dir.is_dir() else ""
        check("GREEN 4a (--pin submodule: scaffold succeeds, .autoharn pinned to the source HEAD)",
              r.returncode == 0 and autoharn_dir.is_dir() and pin_sha == base_sha,
              f"exit={r.returncode} pin_sha={pin_sha} base_sha={base_sha}\n{r.stdout}\n{r.stderr}")
        check("GREEN 4b (all shims + hook wiring resolve into the pin, none of the source path leaks)",
              shim_ok and settings_ok, f"shim_ok={shim_ok} settings_ok={settings_ok}")
        akr = _apply_light_kernel(worktree, schema4, kern4, role4)
        schemas_to_drop.append((schema4, kern4, role4))
        if akr.returncode != 0:
            check("GREEN 4c: kernel apply for smoke test", False, akr.stdout + akr.stderr)
        else:
            smoke = _sh([str(dest4 / "led"), "decision", "pinning-fixture smoke test (new-deployment path)"], cwd=dest4)
            recent = _sh([str(dest4 / "led"), "--recent", "1"], cwd=dest4)
            check("GREEN 4c (real ./led decision + --recent round-trip through the pin, real postgres)",
                  smoke.returncode == 0 and recent.returncode == 0 and "pinning-fixture smoke test" in recent.stdout,
                  f"smoke: {smoke.stdout}{smoke.stderr}\nrecent: {recent.stdout}{recent.stderr}")

        # ============================================================ GREEN 5 / RED 6,7: conversion
        dest5 = tmproot / "green5-classic"
        schema5, kern5, role5 = f"dpf{STAMP}g5", f"dpf{STAMP}g5_kernel", f"dpf{STAMP}g5_rw"
        r = _sh(["bash", str(worktree / "bootstrap" / "new-project.sh"), str(dest5),
                "--db", DB, "--host", HOST, "--schema", schema5, "--kern", kern5, "--role", role5,
                "--name", f"dpf{STAMP}g5", "--governed", "*.py"], cwd=worktree)
        classic_led = (dest5 / "led").read_text() if (dest5 / "led").exists() else ""
        check("SETUP: classic (live-exec) deployment scaffolded for the conversion cases",
              r.returncode == 0 and str(worktree) in classic_led, r.stdout + r.stderr)

        rc = _sh(["bash", str(CONVERT), str(dest5), "--yes"], cwd=REPO)
        settings_text = (dest5 / ".claude" / "settings.json").read_text() if (dest5 / ".claude" / "settings.json").exists() else ""
        led_text = (dest5 / "led").read_text() if (dest5 / "led").exists() else ""
        pin_sha5 = _git(dest5 / ".autoharn", "rev-parse", "HEAD").stdout.strip() if (dest5 / ".autoharn").is_dir() else ""
        no_leftover = str(worktree) not in settings_text and str(worktree) not in led_text
        check("GREEN 5a (convert-to-submodule.sh: classic deployment converts, pinned to the commit it was actually running)",
              rc.returncode == 0 and pin_sha5 == base_sha and no_leftover,
              f"exit={rc.returncode} pin_sha5={pin_sha5} base_sha={base_sha} no_leftover={no_leftover}\n{rc.stdout}\n{rc.stderr}")
        akr5 = _apply_light_kernel(worktree, schema5, kern5, role5)
        schemas_to_drop.append((schema5, kern5, role5))
        if akr5.returncode != 0:
            check("GREEN 5b: kernel apply for smoke test", False, akr5.stdout + akr5.stderr)
        else:
            smoke5 = _sh([str(dest5 / "led"), "decision", "pinning-fixture smoke test (conversion path)"], cwd=dest5)
            recent5 = _sh([str(dest5 / "led"), "--recent", "1"], cwd=dest5)
            check("GREEN 5b (real ./led round-trip through the converted pin, real postgres)",
                  smoke5.returncode == 0 and recent5.returncode == 0 and "conversion path" in recent5.stdout,
                  f"smoke: {smoke5.stdout}{smoke5.stderr}\nrecent: {recent5.stdout}{recent5.stderr}")

        # RED 6: re-convert an already-pinned deployment
        rc6 = _sh(["bash", str(CONVERT), str(dest5), "--yes"], cwd=REPO)
        check("RED 6 (convert-to-submodule.sh refuses an already-pinned deployment)",
              rc6.returncode == 1 and "ALREADY" in rc6.stderr and "PINNED" in rc6.stderr,
              rc6.stdout + rc6.stderr)

        # RED 7: convert against a BUSY deployment (a real background process sitting inside it)
        dest7 = tmproot / "red7-busy"
        schema7, kern7, role7 = f"dpf{STAMP}r7", f"dpf{STAMP}r7_kernel", f"dpf{STAMP}r7_rw"
        r7s = _sh(["bash", str(worktree / "bootstrap" / "new-project.sh"), str(dest7),
                  "--db", DB, "--host", HOST, "--schema", schema7, "--kern", kern7, "--role", role7,
                  "--governed", "*.py"], cwd=worktree)
        proc = subprocess.Popen(["sleep", "30"], cwd=str(dest7))
        time.sleep(0.5)
        try:
            rc7 = _sh(["bash", str(CONVERT), str(dest7), "--yes"], cwd=REPO)
            check("RED 7 (convert-to-submodule.sh refuses a deployment with a live process sitting in it)",
                  r7s.returncode == 0 and rc7.returncode == 1 and
                  f"pid={proc.pid}" in rc7.stderr and not (dest7 / ".autoharn").exists(),
                  f"setup_exit={r7s.returncode} convert_exit={rc7.returncode}\n{rc7.stdout}\n{rc7.stderr}")
        finally:
            proc.terminate()
            proc.wait(timeout=5)

        # ============================================================ GREEN 8 / RED 9,10,11: upgrade
        # A real second commit, ON A BRANCH (not detached -- `git fetch` only follows refs), so
        # upgrade-submodule.sh's own `git fetch` genuinely has something new to retrieve.
        bump_file = worktree / ".fixture-upgrade-bump.txt"
        bump_file.write_text(f"bump {STAMP}\n")
        _git(worktree, "branch", "-f", "fixture-pinning-bump", "HEAD")
        cm2 = _commit_in_worktree(worktree, [".fixture-upgrade-bump.txt"],
                                  "fixture: trivial bump for upgrade-submodule.sh GREEN case")
        new_sha = _git(worktree, "rev-parse", "HEAD").stdout.strip()
        _git(worktree, "branch", "-f", "fixture-pinning-bump", "HEAD")
        check("SETUP: second commit for the upgrade GREEN case", cm2.returncode == 0 and new_sha != base_sha,
              cm2.stdout + cm2.stderr)

        # RED 11: upgrade a NOT-YET-PINNED deployment (dest7, still live-exec -- red7 never converted)
        r11 = _sh(["bash", str(UPGRADE), str(dest7), new_sha, "--yes"], cwd=REPO)
        check("RED 11 (upgrade-submodule.sh refuses a deployment that is not pinned yet)",
              r11.returncode == 1 and "not pinned" in r11.stderr, r11.stdout + r11.stderr)

        # RED 9: bogus SHA
        r9 = _sh(["bash", str(UPGRADE), str(dest5), "0" * 40, "--yes"], cwd=REPO)
        check("RED 9 (upgrade-submodule.sh refuses a SHA that does not resolve after fetch)",
              r9.returncode == 1 and "does not resolve to a commit" in r9.stderr, r9.stdout + r9.stderr)

        # RED 10: live session present
        proc2 = subprocess.Popen(["sleep", "30"], cwd=str(dest5))
        time.sleep(0.5)
        try:
            r10 = _sh(["bash", str(UPGRADE), str(dest5), new_sha, "--yes"], cwd=REPO)
            pin_unchanged = _git(dest5 / ".autoharn", "rev-parse", "HEAD").stdout.strip() == base_sha
            check("RED 10 (upgrade-submodule.sh refuses with a live process sitting in the deployment)",
                  r10.returncode == 1 and f"pid={proc2.pid}" in r10.stderr and pin_unchanged,
                  r10.stdout + r10.stderr)
        finally:
            proc2.terminate()
            proc2.wait(timeout=5)

        # GREEN 8: the real upgrade
        r8 = _sh(["bash", str(UPGRADE), str(dest5), new_sha, "--yes"], cwd=REPO)
        pin_sha8 = _git(dest5 / ".autoharn", "rev-parse", "HEAD").stdout.strip() if (dest5 / ".autoharn").is_dir() else ""
        check("GREEN 8a (upgrade-submodule.sh: real fetch + checkout + commit, pin bumped to the new sha)",
              r8.returncode == 0 and pin_sha8 == new_sha, f"exit={r8.returncode} pin_sha8={pin_sha8} new_sha={new_sha}\n{r8.stdout}\n{r8.stderr}")
        smoke8 = _sh([str(dest5 / "led"), "--recent", "1"], cwd=dest5)
        check("GREEN 8b (real ./led round-trip through the UPGRADED pin, real postgres)",
              smoke8.returncode == 0 and "conversion path" in smoke8.stdout,
              smoke8.stdout + smoke8.stderr)

    finally:
        for schema, kern, role in schemas_to_drop:
            _drop_schema_role(schema, kern, role)
        _sh(["git", "worktree", "remove", "--force", str(worktree)], cwd=REPO)
        if ok_overall:
            shutil.rmtree(tmproot, ignore_errors=True)
        else:
            print(f"\n(left standing for inspection on failure: {tmproot})")

    if failures:
        print(f"\n{len(failures)} failure(s):")
        for f in failures:
            print(f"  !! {f}")
        return 1
    print("\ndeployment-pinning: all cases PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
