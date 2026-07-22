#!/usr/bin/env python3
"""seen-red/setup-tui-background-proc-hygiene/run_fixtures.py -- both-polarity proof of
tools/setup_tui/runner.py's `start_background` stdin/stdout hygiene fix (commission: maintainer
field observation f, "after finally answering all questions, seems that PTY control is not
released to the user"; fresh-context investigator's mechanism finding: `start_background` did
not set `stdin` at all, so the long-lived boundary-service daemon it starts inherited fd 0 --
normally the operator's controlling PTY, which Textual has put in raw mode -- and also Popen'd
`stdout=PIPE` with nothing anywhere draining it, so a chatty daemon eventually blocks forever on
its own next write once the 64KiB OS pipe buffer fills).

NOT registered in gates/fixture_census.py: this builder's file scope is `tools/setup_tui/
runner.py` plus this fixture's own directory ONLY -- `gates/` is out of the exclusive scope
another concurrent builder owns. Residue, reported rather than silently left (filed for whoever
next touches gates/fixture_census.py to add the "setup-tui-background-proc-hygiene" row pointing
at this file, the same registry shape every sibling setup-tui-* fixture already uses).

METHOD (real infra, no mocks, mirrors seen-red/setup-tui-write-file-atomicity/run_fixtures.py's
own idiom for this exact module): loads the OLD, pre-fix `start_background` straight from git
history (`git show <PRE_FIX_COMMIT>:tools/setup_tui/runner.py`, executed in an isolated
namespace -- never `sys.modules`-registered, so this fixture holds the old and the new
implementation live at once without one shadowing the other) and proves it reproduces both
halves of the hazard; then proves the REAL, current, fixed `runner.start_background` closes both.

  CASE RED-1 (stdin leak): with this fixture process's own fd 0 temporarily redirected (via
  `os.dup2`) to point at a scratch marker file (standing in for "the operator's controlling
  PTY" -- whatever concrete file fd 0 points at is the thing that must NOT leak to a background
  daemon), the OLD `start_background` starts a child that reads `/proc/self/fd/0` via `readlink`
  and writes what it finds to a result file (a file, not stdout, so this case's own proof does
  not depend on the very pipe-drain hazard CASE RED-2 exists to demonstrate). The child's fd 0
  resolves to the SAME marker file as this fixture process's own fd 0 -- inherited verbatim,
  proving the leak is real, not hypothetical.

  CASE RED-2 (stdout pipe deadlock): the OLD `start_background` starts a child that writes
  300,000 bytes (comfortably past Linux's 64KiB default pipe buffer) to stdout and then exits.
  Nothing drains `proc.stdout` (exactly the shape verified against every real consumer of the
  returned `Popen` -- `commit_executor.py`, `screens.py` -- neither ever reads it). `proc.
  wait(timeout=...)` raises `TimeoutExpired`: the child is still alive, blocked forever on its
  own `write()` call once the pipe buffer filled -- the silent hang the commission names.

  CASE GREEN-1 (stdin fixed): same marker-file fd-0 redirection, but against the REAL, current
  `runner.start_background`. The child's fd 0 resolves to `/dev/null` (realpath-compared),
  regardless of what this fixture process's own fd 0 pointed at -- proving the fix is
  unconditional, not merely "does not happen to leak in this particular test's fd-0 shape".

  CASE GREEN-2 (stdout fixed, non-blocking): the SAME 300,000-byte child script, against the
  REAL `runner.start_background`. `proc.wait(timeout=...)` returns cleanly with returncode 0 --
  the child was never blocked -- and the file at the returned `BackgroundResult.log_path`
  contains all 300,000 bytes, proving output is captured (not silently dropped to `/dev/null`)
  as well as non-blocking.

  CASE GREEN-3 (regression guards, unbroken by the fix): `dry_run=True` still returns
  `proc=None`, `log_path=None`, and starts nothing; an explicit `log_path=` is honored verbatim
  and appended to rather than truncated.

Zero residue: every scratch dir removed in `finally`; every spawned child explicitly killed
(belt-and-braces, whether or not the fix's own non-blocking behavior already let it finish) in
`finally` regardless of assertion outcome. Lazy imports banned.

Usage: python3 seen-red/setup-tui-background-proc-hygiene/run_fixtures.py
Exit 0 if every case matches; 1 otherwise."""
from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO))

from tools.setup_tui import runner  # noqa: E402 -- the REAL, fixed implementation under test

# runner.py's own HEAD immediately before this dated fix -- pinned by SHA (never "HEAD", which
# drifts stale the moment a later commit touches runner.py again, per this corpus's own
# sibling fixtures' documented lesson).
PRE_FIX_COMMIT = "1de2553699c908489f7f6981e9fd690a51adaadc"

STDIN_CHECK_SCRIPT = """\
import os, sys
out_path = sys.argv[1]
try:
    target = os.readlink('/proc/self/fd/0')
except OSError as exc:
    target = f'ERROR:{exc}'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(target)
"""

BIG_WRITE_SCRIPT = """\
import sys
sys.stdout.write('A' * 300000)
sys.stdout.flush()
sys.exit(0)
"""

BIG_WRITE_BYTES = 300000


def load_old_start_background():
    """Fetches `start_background` exactly as it stood in `PRE_FIX_COMMIT` -- no `stdin=`, plain
    `stdout=subprocess.PIPE` -- via `git show`, executed in an ISOLATED namespace (never
    imported as a module), so this fixture can hold both the old and the new implementation
    live at once without one shadowing the other in `sys.modules`."""
    src = subprocess.run(
        ["git", "show", f"{PRE_FIX_COMMIT}:tools/setup_tui/runner.py"],
        cwd=str(REPO), capture_output=True, text=True, check=True,
    ).stdout
    ns: dict = {}
    exec(compile(src, f"<{PRE_FIX_COMMIT}:tools/setup_tui/runner.py>", "exec"), ns)
    assert "start_background" in ns, (
        f"case RED setup: {PRE_FIX_COMMIT}:tools/setup_tui/runner.py has no start_background -- "
        f"wrong commit pinned?")
    return ns["start_background"]


def kill_quietly(proc: "subprocess.Popen | None") -> None:
    if proc is None:
        return
    try:
        proc.kill()
        proc.wait(timeout=5)
    except Exception:
        pass


def main() -> int:
    scratch = tempfile.mkdtemp(prefix="setup-tui-background-proc-hygiene-")
    spawned: list["subprocess.Popen | None"] = []
    saved_stdin_fd: int | None = None
    # CASE GREEN-2's whole point is proving the default log lands OUTSIDE `scratch` (in the
    # system temp dir, never beside `cwd`), so `shutil.rmtree(scratch, ...)` in `finally` cannot
    # remove it -- tracked here explicitly so this fixture's own "zero residue" claim holds.
    extra_paths_to_clean: list[str] = []
    try:
        old_start_background = load_old_start_background()

        marker_path = os.path.join(scratch, "stdin_marker.txt")
        with open(marker_path, "w", encoding="utf-8") as f:
            f.write("MARKER-STANDING-IN-FOR-THE-OPERATOR-PTY\n")
        stdin_script = os.path.join(scratch, "stdin_check.py")
        with open(stdin_script, "w", encoding="utf-8") as f:
            f.write(STDIN_CHECK_SCRIPT)
        big_write_script = os.path.join(scratch, "big_write.py")
        with open(big_write_script, "w", encoding="utf-8") as f:
            f.write(BIG_WRITE_SCRIPT)

        def with_stdin_redirected_to_marker(fn):
            """Temporarily points THIS process's own fd 0 at `marker_path` (standing in for
            'the operator's controlling PTY' -- whatever concrete thing fd 0 points at is the
            thing a background daemon must never inherit) for the duration of `fn()`, then
            restores the original fd 0 unconditionally."""
            nonlocal saved_stdin_fd
            saved_stdin_fd = os.dup(0)
            marker_fd = os.open(marker_path, os.O_RDONLY)
            try:
                os.dup2(marker_fd, 0)
            finally:
                os.close(marker_fd)
            try:
                return fn()
            finally:
                os.dup2(saved_stdin_fd, 0)
                os.close(saved_stdin_fd)
                saved_stdin_fd = None

        # ============================ CASE RED-1: stdin leak ============================
        red1_result = os.path.join(scratch, "red1_result.txt")

        def run_red1():
            bg = old_start_background(
                [sys.executable, stdin_script, red1_result], cwd=scratch, echo=False)
            spawned.append(bg.proc)
            bg.proc.wait(timeout=15)
            return bg

        with_stdin_redirected_to_marker(run_red1)
        with open(red1_result, encoding="utf-8") as f:
            red1_target = f.read().strip()
        assert os.path.realpath(red1_target) == os.path.realpath(marker_path), (
            f"case RED-1: expected the OLD start_background's child to inherit this fixture "
            f"process's own fd 0 (the marker file, standing in for the operator's controlling "
            f"PTY) -- got {red1_target!r} instead of {marker_path!r}. (If this now differs, the "
            f"pinned pre-fix commit no longer reproduces the stdin-inheritance hazard.)")
        print(f"case RED-1 ok: the OLD start_background ({PRE_FIX_COMMIT[:12]}) let its child "
              f"inherit this process's own fd 0 ({red1_target!r}) -- the PTY-leak hazard the "
              f"commission names is real, not hypothetical")

        # ======================= CASE RED-2: stdout pipe deadlock =======================
        red2_bg = old_start_background(
            [sys.executable, big_write_script], cwd=scratch, echo=False)
        spawned.append(red2_bg.proc)
        try:
            red2_bg.proc.wait(timeout=5)
            raise AssertionError(
                "case RED-2: expected the OLD start_background's child (writing "
                f"{BIG_WRITE_BYTES} bytes to an undrained PIPE) to still be blocked after 5s -- "
                "it exited instead, so this pinned commit no longer reproduces the pipe-"
                "deadlock hazard")
        except subprocess.TimeoutExpired:
            pass
        assert red2_bg.proc.poll() is None, (
            "case RED-2: expected the child to still be ALIVE (blocked on its own write()), "
            "found it already exited")
        print(f"case RED-2 ok: the OLD start_background ({PRE_FIX_COMMIT[:12]})'s child, "
              f"writing {BIG_WRITE_BYTES} bytes to an undrained stdout PIPE, is still alive and "
              f"blocked after 5s -- the silent-hang hazard the commission names is real")
        kill_quietly(red2_bg.proc)

        # =========================== CASE GREEN-1: stdin fixed ===========================
        green1_bg_holder: dict = {}

        def run_green1():
            bg = runner.start_background(
                [sys.executable, stdin_script,
                 os.path.join(scratch, "green1_result.txt")],
                cwd=scratch, echo=False)
            green1_bg_holder["bg"] = bg
            spawned.append(bg.proc)
            if bg.log_path is not None:
                extra_paths_to_clean.append(bg.log_path)
            bg.proc.wait(timeout=15)

        with_stdin_redirected_to_marker(run_green1)
        with open(os.path.join(scratch, "green1_result.txt"), encoding="utf-8") as f:
            green1_target = f.read().strip()
        assert os.path.realpath(green1_target) == os.path.realpath(os.devnull), (
            f"case GREEN-1: expected the FIXED start_background's child to see /dev/null on "
            f"fd 0 regardless of this fixture process's own fd 0 (the marker file) -- got "
            f"{green1_target!r}")
        print("case GREEN-1 ok: the FIXED start_background's child sees /dev/null on fd 0 even "
              "though this fixture process's own fd 0 pointed at a real file -- the PTY-leak "
              "hazard is closed unconditionally")

        # ==================== CASE GREEN-2: stdout fixed, non-blocking ====================
        green2_bg = runner.start_background(
            [sys.executable, big_write_script], cwd=scratch, echo=False)
        spawned.append(green2_bg.proc)
        if green2_bg.log_path is not None:
            extra_paths_to_clean.append(green2_bg.log_path)
        green2_bg.proc.wait(timeout=15)  # must NOT raise TimeoutExpired
        assert green2_bg.proc.returncode == 0, (
            f"case GREEN-2: expected the child to exit 0, got {green2_bg.proc.returncode}")
        assert green2_bg.log_path is not None and os.path.isfile(green2_bg.log_path), (
            f"case GREEN-2: expected BackgroundResult.log_path to name a real file, got "
            f"{green2_bg.log_path!r}")
        with open(green2_bg.log_path, encoding="utf-8") as f:
            logged = f.read()
        assert logged == "A" * BIG_WRITE_BYTES, (
            f"case GREEN-2: expected the log file to hold all {BIG_WRITE_BYTES} bytes the child "
            f"wrote, got {len(logged)} bytes")
        log_dir = os.path.dirname(os.path.abspath(green2_bg.log_path))
        assert log_dir != os.path.abspath(scratch), (
            f"case GREEN-2: the default log location must NOT sit beside `cwd` ({scratch!r}) -- "
            f"a real caller's cwd may be a git checkout root (live-witnessed against this fix's "
            f"own seen-red/setup-tui-boundary-proc-cleanup regression run, which passes "
            f"cwd=REPO_ROOT) and dropping an untracked log there is litter, not a feature -- got "
            f"{green2_bg.log_path!r}")
        assert log_dir == os.path.abspath(tempfile.gettempdir()), (
            f"case GREEN-2: expected the default log location to be the system temp directory "
            f"({tempfile.gettempdir()!r}) -- got {green2_bg.log_path!r}")
        print(f"case GREEN-2 ok: the FIXED start_background's child wrote all "
              f"{BIG_WRITE_BYTES} bytes and exited cleanly within 15s (never blocked); the full "
              f"output landed in the named log file {green2_bg.log_path!r} in the system temp "
              f"directory, never beside `cwd`")

        # ================ CASE GREEN-3: dry_run + explicit log_path unbroken ================
        dry_bg = runner.start_background(["true"], dry_run=True, echo=False)
        assert dry_bg.proc is None and dry_bg.log_path is None, (
            f"case GREEN-3a: expected dry_run=True to start nothing and name no log -- got "
            f"proc={dry_bg.proc!r} log_path={dry_bg.log_path!r}")
        print("case GREEN-3a ok: dry_run=True still starts nothing and names no log_path -- "
              "the pre-existing dry-run contract is unbroken")

        explicit_log = os.path.join(scratch, "explicit.log")
        with open(explicit_log, "w", encoding="utf-8") as f:
            f.write("PRE-EXISTING-LINE\n")
        explicit_bg = runner.start_background(
            [sys.executable, "-c", "print('hello')"], cwd=scratch, echo=False,
            log_path=explicit_log)
        spawned.append(explicit_bg.proc)
        explicit_bg.proc.wait(timeout=15)
        assert explicit_bg.log_path == explicit_log, (
            f"case GREEN-3b: expected an explicit log_path to be honored verbatim, got "
            f"{explicit_bg.log_path!r}")
        with open(explicit_log, encoding="utf-8") as f:
            explicit_contents = f.read()
        assert explicit_contents.startswith("PRE-EXISTING-LINE\n"), (
            f"case GREEN-3b: expected an explicit log_path to be APPENDED to, not truncated -- "
            f"pre-existing content missing: {explicit_contents!r}")
        assert "hello" in explicit_contents, (
            f"case GREEN-3b: expected the child's own output appended after the pre-existing "
            f"line, got {explicit_contents!r}")
        print("case GREEN-3b ok: an explicit log_path is honored verbatim and appended to, "
              "never truncated")

        print("ALL CASES OK -- tools/setup_tui/runner.py start_background: pre-fix stdin-leak "
              "and stdout-pipe-deadlock hazards both demonstrated red, then the fixed "
              "stdin=DEVNULL + log-file-redirected implementation proven to close both, plus "
              "dry-run and explicit-log-path contracts unbroken")
        return 0
    finally:
        for proc in spawned:
            kill_quietly(proc)
        if saved_stdin_fd is not None:
            try:
                os.dup2(saved_stdin_fd, 0)
                os.close(saved_stdin_fd)
            except OSError:
                pass
        for extra_path in extra_paths_to_clean:
            try:
                os.remove(extra_path)
            except OSError:
                pass
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
