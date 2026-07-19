#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-19T03:50:06Z
#   last-change: 2026-07-19T03:50:30Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""seen-red/setup-tui-boundary-proc-cleanup/run_fixtures.py -- live, red-before-green proof of
tools/setup_tui/app.py's `_terminate_boundary_proc` cleanup guarantee (ledger row 1799 finding
6): every exit path from the screen-driving loop -- including an ORDINARY uncaught exception
from a screen function, not just the two typed exits (`ScriptExhausted`/`KeyboardInterrupt`) --
must terminate a boundary service THIS process started before the process actually dies.

METHOD (real infra, no mocks): births a real scratch world, then drives
`python3 -m tools.setup_tui.app --scripted <answers> --start-at boundary` through a small,
UNCOMMITTED driver script this fixture writes into its own scratch tempdir at run time (never
committed as product behavior, per the commission's own instruction).

PHASE-2 CONTRACT CHANGE (design/FABLE-SETUP-TUI-PURE-CORE-SPEC.md, commission ledger rows 1823
point 2 / 1825 / 1835): under the pre-Phase-2 progressive-execution model, screen_boundary started
the real boundary_service DIRECTLY, at decision time, so a crash injected into the NEXT screen
(observability) genuinely fired "after the boundary service is already a live, running child
process." Under the pure-core rewrite NOTHING executes -- including the boundary service start --
until the terminal Checklist screen's ONE commit boundary; a crash at observability now fires
BEFORE boundary has done anything at all, proving nothing about cleanup. The driver's injection
technique moves accordingly: it loads the named app.py via `importlib.util.spec_from_file_location`
(unchanged) and MONKEYPATCHES `tools.setup_tui.screens._dispatch_result` (the per-entry checklist-
decision function `commit_executor.execute`'s `on_result` callback calls) to call through to the
REAL dispatch first (so the boundary entry's own real success handling -- setting
`state["boundary_proc"]`, running the real post-start /health probe -- happens exactly as it would
in product use) and THEN raise an ordinary `RuntimeError`, but ONLY once it observes the
"boundary"/"service started" entry succeed -- simulating an unanticipated defect discovered right
after the boundary service is confirmed live, mid-commit, the genuine Phase-2-shaped equivalent of
the pre-Phase-2 scenario. Since `tools.setup_tui.screens` is imported ONCE (Python's own module
cache) regardless of which app.py copy is driving it, this monkeypatch reaches the SAME module
object either pre-fix or post-fix app.py loads -- only app.py's own cleanup-on-abnormal-exit
differs between the two legs, exactly as the fixture's original design intended.

Two driver runs prove the two polarities of the SAME fix, both against the CURRENT, live
`tools/setup_tui/screens.py`/boundary-starting mechanics -- only `app.py` itself differs:

  * RED (pre-fix): the driver loads `git show 82e8a81:tools/setup_tui/app.py` (PRE_FIX_COMMIT
    below -- an EXPLICIT, pinned commit, not "HEAD": a moving HEAD reference drifted stale the
    moment a later, unrelated commit touched app.py again, caught live in this build's own repair
    pass -- 82e8a81 is app.py's own direct parent immediately BEFORE 5349251 introduced the
    try/finally this fixture proves, verified to carry zero "finally:" occurrences) into a scratch
    file and runs it. The injected exception propagates uncaught past `main()` with NO cleanup
    call -- the real boundary_service subprocess is observed STILL RUNNING via `ps` after the
    driver process has exited.
  * GREEN (post-fix): the driver loads the CURRENT, on-disk `tools/setup_tui/app.py` (this
    fixture's own fix). The SAME injected exception propagates the SAME way, but
    `_terminate_boundary_proc` runs from the `finally` block first -- the boundary_service
    subprocess is observed REAPED (gone) via `ps` after the driver exits.

Needs HARNESS_PGHOST (or EPHEMERIC_PGHOST, or deployment.json) for a real Postgres host, AND
~/w/vdc/venvs/generic/bin/python (screen_boundary's own hardcoded venv for starting a real
boundary_service) -- absent either, UNEXERCISED, exit 0.

Zero residue: every scratch world torn down, every stray boundary_service process (from either
leg) explicitly killed in `finally` regardless of the fix's own cleanup, every scratch dir
removed. Lazy imports banned."""
from __future__ import annotations

import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "filing"))

from pghost_resolve import resolve_pghost  # noqa: E402

sys.path.insert(0, str(REPO))
from tools.setup_tui import commit_executor as _CE  # noqa: E402


def _clear_journal(dest: str) -> None:
    """Removes a leftover commit journal from the RED leg's own (uncleaned, by design) crash
    against this SAME scratch `dest`, before the GREEN leg's independent driver run reuses it --
    see module docstring's own note on why RED/GREEN share one physical destination."""
    path = _CE.journal_path(dest)
    if os.path.isfile(path):
        os.remove(path)


PGDB = "toy"
# app.py's own direct parent commit, immediately BEFORE 5349251 introduced the
# try/finally this fixture proves (verified: git show 82e8a81:tools/setup_tui/app.py
# contains zero "finally:" occurrences) -- an EXPLICIT, pinned reference, never "HEAD"
# (a moving target that drifts stale the moment any later commit touches app.py again,
# caught live in this build's own repair pass).
PRE_FIX_COMMIT = "82e8a81"
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
TEARDOWN = REPO / "bootstrap" / "teardown-world.sh"
VENV_PYTHON = os.path.expanduser("~/w/vdc/venvs/generic/bin/python")

DRIVER_SOURCE = '''\
import importlib.util
import sys

sys.path.insert(0, {repo!r})

import tools.setup_tui.screens as _screens_mod

_orig_dispatch_result = _screens_mod._dispatch_result


def _boom_after_boundary_start(ui, cl, state, index, entry, result, proc=None):
    # Real dispatch FIRST -- the boundary entry's own success handling (state["boundary_proc"],
    # the real post-start /health probe) must actually happen, exactly as it would in product use;
    # this is what proves the injected crash fires GENUINELY after the service is live, not before.
    _orig_dispatch_result(ui, cl, state, index, entry, result, proc)
    if entry.screen == "boundary" and entry.item == "service started" and result.ok:
        print("FIXTURE: injecting a simulated ordinary exception right after the boundary "
              "service is confirmed started, mid-commit (seen-red/setup-tui-boundary-proc-"
              "cleanup)", file=sys.stderr)
        raise RuntimeError(
            "FIXTURE-INJECTED-CRASH: simulated defect right after boundary service start, "
            "mid-commit -- never a committed product behavior, this driver is scratch-only"
        )


_screens_mod._dispatch_result = _boom_after_boundary_start

spec = importlib.util.spec_from_file_location("setup_tui_app_under_test", {app_path!r})
app_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_mod)

sys.exit(app_mod.main())
'''


def sh(argv: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, **kw)


def birth(host: str, world: str, dest: str) -> None:
    r = sh(["bash", str(NEW_PROJECT), dest, "--new-world", world, "--db", PGDB, "--host", host],
           timeout=180)
    assert r.returncode == 0, f"birth of {world} failed: {(r.stdout + r.stderr)[-2000:]}"
    for verb in ("led", "verify-commission"):
        os.chmod(os.path.join(dest, verb), 0o755)


def teardown(host: str, world: str, dest: str) -> None:
    sh([str(TEARDOWN), world, "--db", PGDB, "--host", host, "--dir", dest],
       input=f"{world}\n", timeout=60)


def boundary_pids(needle: str) -> list[int]:
    """Every live PID whose command line mentions `serving.boundary_service` AND `needle` (the
    scratch destination path -- unique per run, so this never matches an unrelated boundary
    service, including a maintainer's own live deployment)."""
    r = sh(["ps", "-eo", "pid,args"])
    pids = []
    for line in r.stdout.splitlines():
        if "serving.boundary_service" in line and needle in line:
            m = re.match(r"\s*(\d+)\s", line)
            if m:
                pids.append(int(m.group(1)))
    return pids


def kill_pids(pids: list[int]) -> None:
    for pid in pids:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass


def run_driver(app_path: str, scratch: str, tag: str, dest: str, world: str, host: str,
               ) -> tuple[str, list[int]]:
    """Writes the driver script (scratch-only, never committed) pointed at `app_path`, runs it
    against a fresh `--start-at boundary` flow, and returns (combined_output,
    boundary_pids_observed_shortly_after_exit)."""
    driver_path = os.path.join(scratch, f"driver-{tag}.py")
    with open(driver_path, "w", encoding="utf-8") as f:
        f.write(DRIVER_SOURCE.format(repo=str(REPO), app_path=app_path))

    answers = "\n".join([
        "y",         # override birth_ok gate (out-of-sequence --start-at boundary)
        "y",         # configure the boundary service now
        dest,        # destination directory
        world,       # world/deployment name
        host,        # Postgres host
        PGDB,        # database
        "y",         # start the boundary service now (this process)
        # PHASE 2: --start-at boundary continues into observability/hydration/checklist (nothing
        # executes until the terminal commit boundary) -- decline both, then confirm the commit so
        # the queued boundary-start entry actually runs; the injected crash fires mid-commit, right
        # after that entry succeeds, so no further scripted answer is ever consumed past "y" here.
        "n",         # show observability blocks? no
        "n",         # run hydration now? no
        "y",         # commit this plan now? yes -- this is where the real boundary start happens
    ]) + "\n"
    ans_path = os.path.join(scratch, f"answers-{tag}.txt")
    with open(ans_path, "w", encoding="utf-8") as f:
        f.write(answers)

    cp = sh([sys.executable, driver_path, "--scripted", ans_path, "--start-at", "boundary"],
            cwd=str(REPO), timeout=120)
    out = cp.stdout + cp.stderr
    assert "/health probe: GREEN" in out, (
        f"{tag}: boundary service does not appear to have started for real (no GREEN /health "
        f"probe observed) -- nothing to prove cleanup against: {out[-2000:]}"
    )
    assert cp.returncode != 0, (
        f"{tag}: expected the injected RuntimeError to propagate as a nonzero exit -- "
        f"got 0: {out[-2000:]}"
    )
    assert "FIXTURE-INJECTED-CRASH" in out, f"{tag}: injected crash marker missing: {out[-2000:]}"

    time.sleep(1.0)  # let SIGTERM/wait() in the finally block (post-fix) actually complete
    return out, boundary_pids(dest)


def main() -> int:
    try:
        pghost = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST")
    except SystemExit as exc:
        print(f"UNEXERCISED: {exc}\nThis fixture needs a live, reachable Postgres host -- set "
              f"HARNESS_PGHOST to run it for real.")
        return 0
    if not os.path.isfile(VENV_PYTHON):
        print(f"UNEXERCISED: {VENV_PYTHON} not found -- this fixture needs a REAL "
              f"boundary_service process (screen_boundary's own hardcoded venv) to prove "
              f"anything about cleaning one up.")
        return 0

    base = int(time.time())
    scratch = tempfile.mkdtemp(prefix="setup-tui-boundary-proc-cleanup-")
    world = f"probeworld{base}bpc"
    dest = os.path.join(scratch, "dest")
    world_born = False
    stray_pids: list[int] = []
    try:
        birth(pghost, world, dest)
        world_born = True

        # ================================ RED: pre-fix app.py ================================
        prefix_app = os.path.join(scratch, "app_prefix.py")
        r = sh(["git", "-C", str(REPO), "show", f"{PRE_FIX_COMMIT}:tools/setup_tui/app.py"])
        assert r.returncode == 0 and r.stdout.strip(), (
            f"could not read {PRE_FIX_COMMIT}:tools/setup_tui/app.py -- {r.stderr}"
        )
        assert "finally:" not in r.stdout, (
            f"fixture assumption stale: {PRE_FIX_COMMIT}:tools/setup_tui/app.py ALREADY carries "
            f"a try/finally -- PRE_FIX_COMMIT needs repinning to a genuinely earlier commit "
            f"(one before whichever commit introduced it)"
        )
        with open(prefix_app, "w", encoding="utf-8") as f:
            f.write(r.stdout)

        out_red, pids_red = run_driver(prefix_app, scratch, "red", dest, world, pghost)
        stray_pids = pids_red
        assert pids_red, (
            f"RED leg: expected the boundary_service child process to still be alive (orphaned) "
            f"after the pre-fix driver's uncaught exception -- found none. Either the defect "
            f"does not reproduce against {PRE_FIX_COMMIT}, or ps matching is broken: "
            f"{out_red[-2000:]}"
        )
        print(f"RED ok (pre-fix, {PRE_FIX_COMMIT}:tools/setup_tui/app.py, no try/finally): "
              f"boundary_service ORPHANED after the injected exception -- live pid(s) {pids_red} "
              f"observed via ps")
        kill_pids(pids_red)
        stray_pids = []
        time.sleep(0.5)
        assert not boundary_pids(dest), "RED leg cleanup: orphan still alive after SIGKILL"

        # =============================== GREEN: post-fix app.py ==============================
        _clear_journal(dest)
        current_app = str(REPO / "tools" / "setup_tui" / "app.py")
        current_text = Path(current_app).read_text(encoding="utf-8")
        assert "finally:" in current_text and "_terminate_boundary_proc(state_holder[0])" in \
            current_text, (
                "fixture assumption stale: the current tools/setup_tui/app.py no longer carries "
                "the try/finally this fixture's GREEN leg expects -- update this fixture"
            )

        out_green, pids_green = run_driver(current_app, scratch, "green", dest, world, pghost)
        stray_pids = pids_green
        assert not pids_green, (
            f"GREEN leg: expected the boundary_service child process to be REAPED (gone) after "
            f"the post-fix driver's uncaught exception -- found live pid(s) {pids_green} "
            f"instead: {out_green[-2000:]}"
        )
        assert ("terminating the boundary service this process started" in out_green), (
            f"GREEN leg: expected app.py's own cleanup message on stderr: {out_green[-2000:]}"
        )
        print("GREEN ok (post-fix, current tools/setup_tui/app.py, try/finally): "
              "boundary_service REAPED -- zero live pid after the SAME injected exception, "
              "app.py's own cleanup message observed")

        print("ALL CASES OK -- app.py boundary_proc cleanup guaranteed on an ordinary uncaught "
              "exception, red before green, live infra, zero residue")
        return 0
    finally:
        if stray_pids:
            kill_pids(stray_pids)
        # belt-and-braces: anything else this run's dest may have started, by any name match.
        kill_pids(boundary_pids(dest))
        if world_born:
            teardown(pghost, world, dest)
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
