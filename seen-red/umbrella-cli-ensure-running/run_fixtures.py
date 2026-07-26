#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for design/FABLE-AUTOHARN-UMBRELLA-CLI-SPEC.md §2/§7:
ensure-running (`autoharn service status|start|stop`, `libexec/autoharn-service`). Runs entirely
against a SCRATCH deployment.json pointing at an unused loopback port -- NEVER against this
host's own standing boundary services (the ones this build's own report explicitly declines to
touch, see design/FABLE-AUTOHARN-UMBRELLA-CLI-SPEC.md §4's hub-consolidation item).

Cases:
  a-status-unreachable -- a scratch world with no service running: `status` reports UNREACHABLE,
                                 exit 1, writes nothing.
  b-cold-spawn -- `start` against the same down service: spawns a detached child, prints ONE
                                 stderr line saying so, polls until reachable, writes a pidfile
                                 naming its own spawn's pid, exits 0.
  c-warm-adopt-silent -- a second `start` against the now-reachable service: "already running",
                                 no new spawn, exit 0.
  d-race-two-invocations -- kill the service, then launch TWO `start` invocations concurrently
                                 against the same down port: exactly one wins the bind (spawns,
                                 pidfile records it), the other ADOPTS (loses the race, its own
                                 child exits, no pidfile write, still exits 0) -- both succeed,
                                 exactly one service process survives.
  e-explicit-stop -- `stop` against the winner: SIGTERM sent, pidfile removed, exit 0.
  f-stop-without-pidfile-refuses -- `stop` again (no pidfile left): REFUSED, exit 1, teaches why,
                                 never guesses a pid.
  g-race-structural-winner -- round-1 review SEVERE-2 extension: after the race (case d), a
                                 STRUCTURAL census (never a timing assumption) that exactly one
                                 `serving.boundary_service` process is alive for this scratch
                                 port, that `ss` independently reports THAT SAME pid as the one
                                 actually holding the port, and that the pidfile names that exact
                                 pid too -- three independent sources of truth (the process
                                 table, the kernel's own socket table via `ss`, and this tool's
                                 own pidfile) agreeing is the structural proof the old grace-sleep
                                 TOCTOU (this family's own red.txt) could not have given: a stale,
                                 losing-but-still-alive child could make `ss`/pidfile disagree
                                 with the process census, which case g would catch.
  h-stop-refuses-decoy-pid -- round-1 review SEVERE-3: a pidfile naming a DECOY process (a plain
                                 `sleep`, not a `serving.boundary_service` at all -- simulating PID
                                 REUSE, where the OS hands a dead service's old pid to an unrelated
                                 process) makes `stop` REFUSE rather than signal it: the decoy
                                 process survives, the stale pidfile is removed, and stderr teaches
                                 why.
  i-squatter-refused-not-adopted -- round-1 review SEVERE-4: a trivial, non-autoharn HTTP server
                                 (200 response, plain-text body -- not this project's own /health
                                 JSON shape) bound to the scratch port makes BOTH `status` and
                                 `start` REFUSE (naming the port and that something non-autoharn
                                 answered there) rather than treating any HTTP response as
                                 "reachable" -- the squatter is neither adopted nor spawned over.
                                 The 200-with-non-JSON-body response also exercises `serving/
                                 boundary_cli_client.py`'s own `_http` fix (the 200 path's
                                 `json.loads` used to be unguarded and would have raised a bare
                                 traceback instead of this typed refusal).
  j-verb-auto-spawns-through-shim -- round-1 review DIRECTED WORK (spec §2 wired into a served
                                 shim, not just the explicit `autoharn service` control-plane
                                 verb): a scratch `led` copy (from bootstrap/templates/led.tmpl)
                                 invoked with `--recent 1` against a DOWN scratch boundary prints
                                 the ONE-LINE ensure-running notice to stderr, spawns the boundary
                                 itself (no separate `autoharn service start` involved), and
                                 proceeds to actually issue its real HTTP call -- proven by the
                                 boundary answering (even a kernel/DB-level failure past that
                                 point is fine and expected against this scratch, DB-less config;
                                 what matters is the call is no longer `BoundaryUnreachable`).

  k-hot-service-late-straggler -- round-2 review AXIS 2 SEVERE: a winner's own live pidfile must
                                 never be destroyed by a later straggler's own spawn_and_wait call
                                 against the same world.
  k2-adopted-requires-probe -- round-4 review SEVERE-A (red-first against pre-fix code): a decoy
                                 process named like serving.boundary_service for this exact toml
                                 (passes the pid identity check) but bound to nothing at all (no
                                 listener on the URL) must NEVER be adopted -- the pid check alone
                                 must never suffice; only a successful probe() may.
  k3-stale-squat-reclamation -- round-4 review SEVERE-B item 1 (red-first against pre-fix code): a
                                 pidfile pre-seeded with a dead pid, present when serving/
                                 boundary_service.py's own O_CREAT|O_EXCL pidfile write loses to
                                 that stale file, must be RECLAIMED (rewritten to the real winner's
                                 own pid) rather than merely warned about and left stale forever --
                                 and 'autoharn service stop' must then work against it.

  l-stop-waits-for-delayed-exit -- ledger rows 1332/1354 (service-stop-no-wait-orphans): a slow-
                                 shutdown witness. A mock process (a plain Python child whose own
                                 /proc/<pid>/cmdline is made to match pid_is_boundary_service's
                                 text check, never a real boundary -- house rule) traps SIGTERM
                                 and only actually exits ~1.5s later. Pre-fix, `stop` removed the
                                 pidfile the instant SIGTERM was sent -- the mock was still alive
                                 for that whole 1.5s, an ORPHAN with the pidfile already gone and
                                 the world looking stopped. Post-fix, `stop` must poll and WAIT
                                 for the real exit before touching the pidfile, and report
                                 "confirmed dead after SIGTERM" (never "ESCALATING", since the
                                 mock died on its own well inside the grace window).
  m-stop-escalates-to-sigkill-loud -- a mock that IGNORES SIGTERM outright (SIG_IGN) and only
                                 dies to SIGKILL. `stop` must wait out the full SIGTERM grace
                                 window, print a LOUD stderr line disclosing the escalation, send
                                 SIGKILL, confirm the exit, and only then remove the pidfile.
  n-stop-refuses-pidfile-removal-while-alive -- white-box case (imports libexec/autoharn-service
                                 directly and fakes ONLY its `os.kill` to a recording no-op,
                                 leaving `os.path.exists`/`/proc` real): simulates a pid that
                                 outlives BOTH SIGTERM and SIGKILL (the uninterruptible-kernel-
                                 sleep case the reference _kill_boundary posture cannot rule out
                                 either). `stop` must REFUSE, exit 1, and leave the pidfile in
                                 place -- removing it here would orphan a demonstrably-live
                                 process while reporting success, exactly the defect this whole
                                 item exists to close.

RUN: python3 seen-red/umbrella-cli-ensure-running/run_fixtures.py
(needs a free loopback port; picks one dynamically to avoid colliding with any of this host's
many concurrent boundary_service test fixtures)
"""
from __future__ import annotations

import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AUTOHARN = REPO_ROOT / "autoharn"

# case k calls serving/ensure_running.py's own spawn_and_wait directly (not through a subprocess)
# so it can drive the exact hot-service-plus-late-straggler shape deterministically -- top-level
# import, per CLAUDE.md's lazy-import ban.
sys.path.insert(0, str(REPO_ROOT))
from serving import ensure_running as er  # noqa: E402

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own
# environment before any subprocess is spawned -- inherited by the whole process tree
# this fixture starts, so every repo-root verb invocation anywhere downstream carries it.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _run(argv: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, capture_output=True, text=True, env=env, timeout=30)


def _live_boundary_service_pids(port: int) -> list[int]:
    """Every process whose own /proc/<pid>/cmdline names BOTH serving.boundary_service and this
    exact --port -- a structural census independent of ss/HTTP, read straight off the process
    table (case g's first of three independent sources of truth)."""
    pids = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            cmdline = entry.joinpath("cmdline").read_bytes()
        except OSError:
            continue
        text = cmdline.replace(b"\x00", b" ").decode("utf-8", errors="replace")
        if "serving.boundary_service" in text and f"--port {port} " in text + " ":
            pids.append(int(entry.name))
    return pids


def _ss_pid_for_port(port: int) -> int | None:
    """The pid `ss` (the kernel's own socket table, case g's second independent source of truth)
    reports as holding the LISTEN socket at 127.0.0.1:<port>, or None if nothing is listening."""
    try:
        r = subprocess.run(["ss", "-H", "-ltnp"], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return None
    for line in r.stdout.splitlines():
        if re.search(rf"[:.]{port}\s", line) is None:
            continue
        m = re.search(r"pid=(\d+)", line)
        if m:
            return int(m.group(1))
    return None


def _spawn_mock_boundary_service(toml_path: Path, py_code: str) -> subprocess.Popen:
    """Cases l/m/n's shared spawn: a plain `python3 -c <py_code>` child, never a real
    serving.boundary_service (house rule: test processes are the fixture's own children, plain
    sleeps or trivial mocks, never a real boundary) -- but its /proc/<pid>/cmdline is made to
    satisfy pid_is_boundary_service's own text check (mentions `serving.boundary_service` and
    this exact scratch world's `boundary-multiplex.toml` path) by passing them as trailing,
    otherwise-unused positional argv after the `-c` script, exactly like case h's existing decoy
    convention passes a recognizable marker on the process's own command line.
    A background daemon thread immediately starts `Popen.wait()` on it, reaping it the moment it
    exits -- mirroring the real world, where the pid `stop` signals is reparented to init (its
    own spawning invocation already having exited) and reaped by init the instant it dies, never
    left as a zombie a later poll would misread as 'still alive'."""
    proc = subprocess.Popen(
        ["python3", "-c", py_code, "serving.boundary_service", "--config", str(toml_path)])
    threading.Thread(target=proc.wait, daemon=True).start()
    return proc


def main() -> int:
    port = _free_port()
    scratch = Path("/tmp") / f"umbrella-cli-ensure-running-fixture-{os.getpid()}"
    scratch.mkdir(parents=True, exist_ok=True)
    dep_path = scratch / "deployment.json"
    dep_path.write_text(json.dumps({
        "db": "toy", "host": "192.168.122.1", "kern": "toy_kernel", "name": "svctest",
        "role": "toy_rw", "schema": "toy",
        "boundary_url": f"http://127.0.0.1:{port}", "boundary_deployment": "svctest",
    }), encoding="utf-8")
    (scratch / "boundary-multiplex.toml").write_text(
        "[deployments.svctest]\n"
        "pghost = \"192.168.122.1\"\npgdatabase = \"toy\"\npguser = \"toy_rw\"\n"
        "pgschema = \"toy\"\npgkern = \"toy_kernel\"\n", encoding="utf-8")
    env = dict(os.environ)
    env["PICKUP_DEPLOYMENT"] = str(dep_path)
    # filing/fixture_sandbox.py: this fixture's own AUTOHARN_FIXTURE_SANDBOX=1 (set above, at
    # import time) makes libexec/autoharn-service's own main() refuse EVERY invocation of THIS
    # repo's real ./autoharn dispatcher outright, with no exception for a scratch
    # PICKUP_DEPLOYMENT override -- that refusal is unconditional by design (the module's own
    # docstring: "does not depend on recognizing a fixture's call shape"). This IS exactly the
    # "REVIEWED, use-site reason to touch a repo-root verb directly" case its own refusal text
    # names as sanctioned exit 2: every invocation below is driven with PICKUP_DEPLOYMENT pointed
    # at this function's own scratch deployment.json/boundary-multiplex.toml, never the real one.
    env["AUTOHARN_FIXTURE_SANDBOX_WAIVER"] = (
        "seen-red/umbrella-cli-ensure-running both-polarity-proves design/"
        "FABLE-AUTOHARN-UMBRELLA-CLI-SPEC.md sec2/sec7 (ensure-running) by driving "
        "libexec/autoharn-service through the real ./autoharn dispatcher against a scratch "
        "deployment.json this function writes -- PICKUP_DEPLOYMENT is overridden on every call "
        "below, the real repo deployment.json is never read.")

    ok = True

    r = _run([str(AUTOHARN), "service", "status"], env)
    if r.returncode != 1 or "UNREACHABLE" not in r.stderr:
        print(f"a-status-unreachable: FAIL -- exit {r.returncode}, stderr={r.stderr!r}")
        ok = False
    else:
        print("a-status-unreachable: PASS (RED case: exit 1, UNREACHABLE)")

    r = _run([str(AUTOHARN), "service", "start"], env)
    if r.returncode != 0 or "spawning it" not in r.stderr or "this invocation's own spawn" not in r.stdout:
        print(f"b-cold-spawn: FAIL -- exit {r.returncode}, stdout={r.stdout!r} stderr={r.stderr!r}")
        ok = False
    else:
        print("b-cold-spawn: PASS (one stderr notice, reachable after spawn, pidfile written)")
    if not (scratch / ".autoharn-service.pid").is_file():
        print("b-cold-spawn: FAIL -- no pidfile written after a winning spawn")
        ok = False

    r = _run([str(AUTOHARN), "service", "start"], env)
    if r.returncode != 0 or "already running" not in r.stdout:
        print(f"c-warm-adopt-silent: FAIL -- exit {r.returncode}, stdout={r.stdout!r}")
        ok = False
    else:
        print("c-warm-adopt-silent: PASS (no new spawn, exit 0)")

    _run([str(AUTOHARN), "service", "stop"], env)
    time.sleep(0.3)

    p_a = subprocess.Popen([str(AUTOHARN), "service", "start"], env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    p_b = subprocess.Popen([str(AUTOHARN), "service", "start"], env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out_a, err_a = p_a.communicate(timeout=30)
    out_b, err_b = p_b.communicate(timeout=30)
    both_zero = p_a.returncode == 0 and p_b.returncode == 0
    one_adopted = ("lost the bind race" in out_a) or ("lost the bind race" in out_b)
    one_spawned = ("this invocation's own spawn, pid" in out_a) or ("this invocation's own spawn, pid" in out_b)
    if not (both_zero and one_adopted and one_spawned):
        print(f"d-race-two-invocations: FAIL -- a(exit={p_a.returncode}, out={out_a!r}) "
              f"b(exit={p_b.returncode}, out={out_b!r})")
        ok = False
    else:
        print("d-race-two-invocations: PASS (one spawned+won, one adopted, both exit 0)")

    # g-race-structural-winner: three independent sources of truth about "who actually holds the
    # port right now" -- the process table, the kernel's own socket table (ss), and this tool's
    # own pidfile -- must all agree on exactly one pid. A LOSING child is spawned but may still be
    # importing fastapi/pydantic (has not yet even attempted its own bind()) for up to ~1s after
    # its own `autoharn service start` invocation already returned "ADOPTING" -- that straggler is
    # harmless (it will reach its own bind(), lose, and exit on its own) but means the process
    # CENSUS can transiently show more than one `serving.boundary_service` entry right after the
    # race resolves. This polls (bounded) for the census to settle rather than asserting on the
    # instant right after case d -- the actual invariant this case exists to prove is that `ss`
    # (the kernel's own socket table -- the ONE source that can only ever name a genuine bind
    # winner) and the pidfile agree, and that the process census converges to that same single
    # pid rather than staying stuck at more than one (which WOULD be the split-brain defect the
    # old grace-sleep TOCTOU risked: two processes both genuinely bound, or a pidfile naming a pid
    # that never held the port at all).
    deadline = time.monotonic() + 5.0
    live_pids: list[int] = []
    ss_pid: int | None = None
    pidfile_path = scratch / ".autoharn-service.pid"
    pidfile_pid: int | None = None
    while time.monotonic() < deadline:
        live_pids = _live_boundary_service_pids(port)
        ss_pid = _ss_pid_for_port(port)
        pidfile_pid = (int(pidfile_path.read_text(encoding="utf-8").strip())
                       if pidfile_path.is_file() else None)
        if len(live_pids) == 1 and ss_pid == live_pids[0] and pidfile_pid == live_pids[0]:
            break
        time.sleep(0.1)
    if len(live_pids) != 1:
        print(f"g-race-structural-winner: FAIL -- process census never converged to exactly one "
              f"live serving.boundary_service process for port {port} (last seen: {live_pids})")
        ok = False
    elif ss_pid != live_pids[0]:
        print(f"g-race-structural-winner: FAIL -- ss reports port {port} held by pid {ss_pid}, "
              f"but the (converged) process census says {live_pids}")
        ok = False
    elif pidfile_pid != live_pids[0]:
        print(f"g-race-structural-winner: FAIL -- pidfile names pid {pidfile_pid}, but the "
              f"live/port-holding process is {live_pids[0]}")
        ok = False
    else:
        print(f"g-race-structural-winner: PASS (converged to exactly one live process, pid "
              f"{live_pids[0]}, agreeing with ss's port-holder AND the pidfile)")

    r = _run([str(AUTOHARN), "service", "stop"], env)
    # ROW 1332 FIX: stop's happy-path wording changed from "sent SIGTERM ... pidfile removed"
    # (which only proved a signal was SENT, not that the process actually died) to "confirmed
    # dead after SIGTERM ... pidfile removed" -- stop now waits for and confirms exit before
    # touching the pidfile. This is the ONLY output-wording delta on the fast-dying/no-marker
    # path; exit code and pidfile-removed behavior are unchanged.
    if r.returncode != 0 or "confirmed dead after SIGTERM" not in r.stdout:
        print(f"e-explicit-stop: FAIL -- exit {r.returncode}, stdout={r.stdout!r}")
        ok = False
    else:
        print("e-explicit-stop: PASS (confirmed-dead wording, not merely sent-signal)")

    r = _run([str(AUTOHARN), "service", "stop"], env)
    if r.returncode != 1 or "REFUSED" not in r.stderr or "no pidfile" not in r.stderr:
        print(f"f-stop-without-pidfile-refuses: FAIL -- exit {r.returncode}, stderr={r.stderr!r}")
        ok = False
    else:
        print("f-stop-without-pidfile-refuses: PASS (RED case: exit 1, teaches, never guesses)")

    # h-stop-refuses-decoy-pid (round-1 review SEVERE-3): a pidfile naming a process that is NOT
    # a serving.boundary_service at all -- simulating PID REUSE, where the OS hands a dead
    # service's old pid to an unrelated process later. `stop` must refuse rather than signal it.
    decoy = subprocess.Popen(["sleep", "300"])
    try:
        pidfile_path.write_text(str(decoy.pid), encoding="utf-8")
        r = _run([str(AUTOHARN), "service", "stop"], env)
        decoy_alive = decoy.poll() is None
        if (r.returncode != 1 or "REFUSED" not in r.stderr or "not a" not in r.stderr
                or "serving.boundary_service" not in r.stderr or not decoy_alive
                or pidfile_path.is_file()):
            print(f"h-stop-refuses-decoy-pid: FAIL -- exit {r.returncode}, stderr={r.stderr!r}, "
                  f"decoy_alive={decoy_alive}, pidfile_still_present={pidfile_path.is_file()}")
            ok = False
        else:
            print("h-stop-refuses-decoy-pid: PASS (RED case: decoy survives, stale pidfile "
                  "removed, refusal teaches)")
    finally:
        decoy.terminate()
        try:
            decoy.wait(timeout=5)
        except subprocess.TimeoutExpired:
            decoy.kill()

    # i-squatter-refused-not-adopted (round-1 review SEVERE-4): a trivial, non-autoharn HTTP
    # responder on the scratch port -- 200 status, plain-text body, no protocol_version key at
    # all -- must make `status`/`start` REFUSE, never "REACHABLE"/adopted. The plain-text 200
    # body also exercises serving/boundary_cli_client.py's own `_http` fix (previously an
    # unguarded `json.loads` on the 200 path would raise a bare traceback here instead of this
    # typed refusal).
    squatter_port = _free_port()
    squatter_dep = scratch / "deployment-squatter.json"
    squatter_dep.write_text(json.dumps({
        "db": "toy", "host": "192.168.122.1", "kern": "toy_kernel", "name": "svctest",
        "role": "toy_rw", "schema": "toy",
        "boundary_url": f"http://127.0.0.1:{squatter_port}", "boundary_deployment": "svctest",
    }), encoding="utf-8")
    squatter_env = dict(env)
    squatter_env["PICKUP_DEPLOYMENT"] = str(squatter_dep)
    squatter = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(squatter_port), "--bind", "127.0.0.1"],
        cwd=str(scratch), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline = time.monotonic() + 5.0
        squatter_up = False
        while time.monotonic() < deadline:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{squatter_port}/", timeout=1.0)
                squatter_up = True
                break
            except urllib.error.HTTPError:
                squatter_up = True
                break
            except Exception:
                time.sleep(0.1)
        if not squatter_up:
            print("i-squatter-refused-not-adopted: FAIL -- SETUP FAILED, python -m http.server "
                  "never came up")
            ok = False
        else:
            r_status = _run([str(AUTOHARN), "service", "status"], squatter_env)
            r_start = _run([str(AUTOHARN), "service", "start"], squatter_env)
            status_refuses = (r_status.returncode == 1 and "REFUSED" in r_status.stderr
                               and "REACHABLE" not in r_status.stdout)
            start_refuses = (r_start.returncode == 1 and "REFUSED" in r_start.stderr
                              and "already running" not in r_start.stdout
                              and "this invocation's own spawn" not in r_start.stdout)
            if not (status_refuses and start_refuses):
                print(f"i-squatter-refused-not-adopted: FAIL -- status(exit={r_status.returncode}, "
                      f"stdout={r_status.stdout!r}, stderr={r_status.stderr!r}) "
                      f"start(exit={r_start.returncode}, stdout={r_start.stdout!r}, "
                      f"stderr={r_start.stderr!r})")
                ok = False
            else:
                print("i-squatter-refused-not-adopted: PASS (RED case: both status and start "
                      "refuse a non-autoharn HTTP responder, name the port, never adopt)")
    finally:
        squatter.terminate()
        try:
            squatter.wait(timeout=5)
        except subprocess.TimeoutExpired:
            squatter.kill()

    # j-verb-auto-spawns-through-shim (round-1 review DIRECTED WORK): a served shim's OWN
    # `_load_config()` -- not `autoharn service start` -- ensure-runs the boundary when it is
    # unreachable. A fresh scratch `led` copy (from the REAL bootstrap/templates/led.tmpl, not a
    # stand-in) is invoked directly against a DOWN scratch boundary.
    j_scratch = Path("/tmp") / f"umbrella-cli-ensure-running-shim-fixture-{os.getpid()}"
    j_scratch.mkdir(parents=True, exist_ok=True)
    j_port = _free_port()
    j_dep_path = j_scratch / "deployment.json"
    j_dep_path.write_text(json.dumps({
        "db": "toy", "host": "192.168.122.1", "kern": "toy_kernel", "name": "svctest",
        "role": "toy_rw", "schema": "toy",
        "boundary_url": f"http://127.0.0.1:{j_port}", "boundary_deployment": "svctest",
    }), encoding="utf-8")
    (j_scratch / "boundary-multiplex.toml").write_text(
        "[deployments.svctest]\n"
        "pghost = \"192.168.122.1\"\npgdatabase = \"toy\"\npguser = \"toy_rw\"\n"
        "pgschema = \"toy\"\npgkern = \"toy_kernel\"\n", encoding="utf-8")
    led_copy = j_scratch / "led"
    led_copy.write_text((REPO_ROOT / "bootstrap" / "templates" / "led.tmpl").read_text(encoding="utf-8"),
                         encoding="utf-8")
    led_copy.chmod(0o755)
    j_env = dict(os.environ)
    j_env["PICKUP_DEPLOYMENT"] = str(j_dep_path)
    j_env["AUTOHARN"] = str(REPO_ROOT)
    j_pidfile = j_scratch / ".autoharn-service.pid"
    try:
        r = subprocess.run([str(led_copy), "--recent", "1"], env=j_env, capture_output=True,
                            text=True, timeout=30)
        spawned_notice = "was unreachable -- spawned it" in r.stderr
        no_longer_unreachable = "boundary service itself could not be reached" not in r.stderr
        pidfile_now_present = j_pidfile.is_file()
        if not (spawned_notice and no_longer_unreachable and pidfile_now_present):
            print(f"j-verb-auto-spawns-through-shim: FAIL -- exit {r.returncode}, "
                  f"stdout={r.stdout!r}, stderr={r.stderr!r}, pidfile_present={pidfile_now_present}")
            ok = False
        else:
            print("j-verb-auto-spawns-through-shim: PASS (led auto-spawned the down boundary "
                  "itself, one stderr notice, then proceeded to a real HTTP call)")
    finally:
        if j_pidfile.is_file():
            try:
                pid = int(j_pidfile.read_text(encoding="utf-8").strip())
                os.kill(pid, 15)
            except (OSError, ValueError):
                pass
        shutil.rmtree(j_scratch, ignore_errors=True)

    # k-hot-service-late-straggler (round-2 review AXIS 2 SEVERE): a "winner" spawn_and_wait call
    # already has the boundary up and its own pidfile written; a SECOND, later spawn_and_wait call
    # against the SAME world (simulating a straggler invocation whose own earlier `probe()` call --
    # made moments before, in a real concurrent-process race -- legitimately observed UNREACHABLE
    # before the winner's bind completed) must ADOPT without ever deleting, replacing, or
    # corrupting the winner's pidfile: the pre-fix code unconditionally did
    # `pidfile.unlink(missing_ok=True)` here, so the straggler's own spawn attempt would delete the
    # LIVE winner's pidfile, its own child would then fail to bind (the winner still holds the
    # port) and exit without writing a new one, leaving the winner running but with NO pidfile at
    # all -- unstoppable via `autoharn service stop` ("no pidfile" refusal) even though the service
    # is healthy.
    k_scratch = Path("/tmp") / f"umbrella-cli-ensure-running-straggler-fixture-{os.getpid()}"
    k_scratch.mkdir(parents=True, exist_ok=True)
    k_port = _free_port()
    (k_scratch / "boundary-multiplex.toml").write_text(
        "[deployments.svctest]\n"
        "pghost = \"192.168.122.1\"\npgdatabase = \"toy\"\npguser = \"toy_rw\"\n"
        "pgschema = \"toy\"\npgkern = \"toy_kernel\"\n", encoding="utf-8")
    k_url = f"http://127.0.0.1:{k_port}"
    k_pidfile = k_scratch / ".autoharn-service.pid"
    try:
        winner = er.spawn_and_wait(k_scratch, k_url, k_port, "svctest")
        if winner.status != "own" or not k_pidfile.is_file():
            print(f"k-hot-service-late-straggler: FAIL -- SETUP could not establish a winner "
                  f"(status={winner.status!r}, pidfile_present={k_pidfile.is_file()})")
            ok = False
        else:
            before_bytes = k_pidfile.read_bytes()
            straggler = er.spawn_and_wait(k_scratch, k_url, k_port, "svctest")
            after_bytes = k_pidfile.read_bytes() if k_pidfile.is_file() else None
            winner_still_answers = er.probe(k_url, "svctest")[0] == er.OK
            stop_still_works = False
            if k_pidfile.is_file():
                try:
                    stop_pid = int(k_pidfile.read_text(encoding="utf-8").strip())
                    stop_still_works = (stop_pid == winner.proc_pid)
                except (OSError, ValueError):
                    stop_still_works = False
            if (straggler.status != "adopted" or after_bytes != before_bytes or
                    not winner_still_answers or not stop_still_works):
                print(f"k-hot-service-late-straggler: FAIL -- straggler status={straggler.status!r}, "
                      f"pidfile_before={before_bytes!r} pidfile_after={after_bytes!r}, "
                      f"winner_still_answers={winner_still_answers}, "
                      f"stop_still_works={stop_still_works}")
                ok = False
            else:
                print("k-hot-service-late-straggler: PASS (straggler adopted, winner's pidfile "
                      "byte-identical, winner still reachable, stop still targets the real winner)")
    finally:
        if k_pidfile.is_file():
            try:
                pid = int(k_pidfile.read_text(encoding="utf-8").strip())
                os.kill(pid, 15)
            except (OSError, ValueError):
                pass
        shutil.rmtree(k_scratch, ignore_errors=True)

    shutil.rmtree(scratch, ignore_errors=True)

    # k2-adopted-requires-probe (round-4 review SEVERE-A, red-first against the pre-fix code): a
    # DECOY process whose own cmdline matches serving.boundary_service AND this exact toml path
    # (so pid_is_boundary_service's identity check says "yes") but which is bound to NOTHING at
    # all -- no listener anywhere on k2_url -- must NEVER be adopted. Pre-fix code returned
    # "adopted" straight off the pid check, without ever calling probe(); the fix requires a
    # successful probe() before any "adopted" verdict, so this decoy is refused-over-and-spawned-
    # past, never adopted.
    k2_scratch = Path("/tmp") / f"umbrella-cli-ensure-running-decoy-fixture-{os.getpid()}"
    k2_scratch.mkdir(parents=True, exist_ok=True)
    k2_port = _free_port()
    k2_toml = k2_scratch / "boundary-multiplex.toml"
    k2_toml.write_text(
        "[deployments.svctest]\n"
        "pghost = \"192.168.122.1\"\npgdatabase = \"toy\"\npguser = \"toy_rw\"\n"
        "pgschema = \"toy\"\npgkern = \"toy_kernel\"\n", encoding="utf-8")
    k2_url = f"http://127.0.0.1:{k2_port}"
    k2_pidfile = k2_scratch / ".autoharn-service.pid"
    decoy2 = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(300)",
         "serving.boundary_service", str(k2_toml)])
    try:
        k2_pidfile.write_text(str(decoy2.pid), encoding="utf-8")
        outcome = er.spawn_and_wait(k2_scratch, k2_url, k2_port, "svctest")
        if outcome.status == "adopted":
            print(f"k2-adopted-requires-probe: FAIL -- adopted a decoy (pid {decoy2.pid}) that "
                  f"was named like serving.boundary_service for this toml but bound to nothing "
                  f"(outcome={outcome!r})")
            ok = False
        else:
            print(f"k2-adopted-requires-probe: PASS (status={outcome.status!r}, never adopted "
                  f"the bound-to-nothing decoy; the pid check alone never suffices)")
    finally:
        decoy2.terminate()
        try:
            decoy2.wait(timeout=5)
        except subprocess.TimeoutExpired:
            decoy2.kill()
        if k2_pidfile.is_file():
            try:
                real_pid = int(k2_pidfile.read_text(encoding="utf-8").strip())
                if real_pid != decoy2.pid:
                    os.kill(real_pid, 15)
            except (OSError, ValueError):
                pass
        shutil.rmtree(k2_scratch, ignore_errors=True)

    # k3-stale-squat-reclamation (round-4 review SEVERE-B item 1, red-first against the pre-fix
    # code): a pidfile pre-seeded with a genuinely DEAD pid sits at the exact path
    # serving/boundary_service.py's own --pidfile targets. Invoking that module DIRECTLY (bypassing
    # ensure_running.py's own pre-clear, which would otherwise unlink an obviously-stale file
    # before the child ever runs -- this fixture exists specifically to prove boundary_service.py's
    # OWN O_CREAT|O_EXCL-lost-to-a-stale-file branch reclaims rather than merely warns) must
    # rewrite the pidfile to name the real winner, and `autoharn service stop` must then work
    # against it. Pre-fix, that branch only ever warned and left the dead pid in place forever --
    # unstoppable via the tracked path even though the real service is healthy.
    k3_scratch = Path("/tmp") / f"umbrella-cli-ensure-running-stale-squat-fixture-{os.getpid()}"
    k3_scratch.mkdir(parents=True, exist_ok=True)
    k3_port = _free_port()
    k3_toml = k3_scratch / "boundary-multiplex.toml"
    k3_toml.write_text(
        "[deployments.svctest]\n"
        "pghost = \"192.168.122.1\"\npgdatabase = \"toy\"\npguser = \"toy_rw\"\n"
        "pgschema = \"toy\"\npgkern = \"toy_kernel\"\n", encoding="utf-8")
    k3_url = f"http://127.0.0.1:{k3_port}"
    k3_dep_path = k3_scratch / "deployment.json"
    k3_dep_path.write_text(json.dumps({
        "db": "toy", "host": "192.168.122.1", "kern": "toy_kernel", "name": "svctest",
        "role": "toy_rw", "schema": "toy",
        "boundary_url": k3_url, "boundary_deployment": "svctest",
    }), encoding="utf-8")
    k3_env = dict(os.environ)
    k3_env["PICKUP_DEPLOYMENT"] = str(k3_dep_path)
    k3_env["AUTOHARN_FIXTURE_SANDBOX_WAIVER"] = env["AUTOHARN_FIXTURE_SANDBOX_WAIVER"]
    k3_pidfile = k3_scratch / ".autoharn-service.pid"
    _dead = subprocess.Popen([sys.executable, "-c", "pass"])
    _dead.wait(timeout=5)
    dead_pid = _dead.pid
    k3_pidfile.write_text(str(dead_pid), encoding="utf-8")
    service_proc = subprocess.Popen(
        [sys.executable, "-m", "serving.boundary_service", "--config", str(k3_toml),
         "--port", str(k3_port), "--pidfile", str(k3_pidfile)],
        cwd=str(REPO_ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        start_new_session=True)
    # ROW 1332 FIX SIDE EFFECT: this fixture's own main process is service_proc's REAL parent
    # and stays alive for the rest of this run -- without a prompt reaper, a dead service_proc
    # sits as a ZOMBIE (its own /proc/<pid> entry persisting) until this function eventually
    # calls .wait() on it, which `cmd_stop`'s own NEW liveness poll below (row 1332's fix) would
    # misread as "still alive" even after a genuine SIGKILL death -- exactly the same reason
    # _spawn_mock_boundary_service (cases l/m) starts a background reaper thread the instant it
    # spawns its own mock. In the REAL world this never bites: the `start` invocation that
    # originally spawned a service has already exited by the time a separate `stop` invocation
    # runs, so init (pid 1) has already reparented and will reap it the instant it dies. This
    # thread reproduces that same prompt-reap behavior for this fixture's own long-lived process.
    threading.Thread(target=service_proc.wait, daemon=True).start()
    try:
        deadline = time.monotonic() + 10.0
        up = False
        while time.monotonic() < deadline:
            if er.probe(k3_url, "svctest")[0] == er.OK:
                up = True
                break
            time.sleep(0.1)
        if not up:
            _out, _err = service_proc.communicate(timeout=2) if service_proc.poll() is not None else ("", "")
            print(f"k3-stale-squat-reclamation: FAIL -- SETUP, service never came up "
                  f"(stdout={_out!r} stderr={_err!r})")
            ok = False
        else:
            reclaimed_pid: int | None = None
            if k3_pidfile.is_file():
                try:
                    reclaimed_pid = int(k3_pidfile.read_text(encoding="utf-8").strip())
                except (OSError, ValueError):
                    reclaimed_pid = None
            if reclaimed_pid != service_proc.pid:
                print(f"k3-stale-squat-reclamation: FAIL -- pidfile still names {reclaimed_pid} "
                      f"(pre-seeded dead pid was {dead_pid}), not the real winner "
                      f"{service_proc.pid}")
                ok = False
            else:
                r = _run([str(AUTOHARN), "service", "stop"], k3_env)
                if r.returncode != 0 or "confirmed dead after SIGTERM" not in r.stdout:
                    print(f"k3-stale-squat-reclamation: FAIL -- stop after reclamation: exit "
                          f"{r.returncode}, stdout={r.stdout!r}, stderr={r.stderr!r}")
                    ok = False
                else:
                    print("k3-stale-squat-reclamation: PASS (dead-pid stale pidfile reclaimed to "
                          "name the real winner; stop worked against it)")
    finally:
        if k3_pidfile.is_file():
            try:
                pid = int(k3_pidfile.read_text(encoding="utf-8").strip())
                os.kill(pid, 15)
            except (OSError, ValueError):
                pass
        else:
            try:
                os.kill(service_proc.pid, 15)
            except OSError:
                pass
        try:
            service_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            service_proc.kill()
        shutil.rmtree(k3_scratch, ignore_errors=True)

    # l-stop-waits-for-delayed-exit / m-stop-escalates-to-sigkill-loud (rows 1332/1354): a fresh
    # scratch world of their own, separate from every prior case's, so nothing above's teardown
    # ordering matters here.
    lm_scratch = Path("/tmp") / f"umbrella-cli-ensure-running-fixture-lm-{os.getpid()}"
    lm_scratch.mkdir(parents=True, exist_ok=True)
    lm_dep_path = lm_scratch / "deployment.json"
    lm_dep_path.write_text(json.dumps({
        "db": "toy", "host": "192.168.122.1", "kern": "toy_kernel", "name": "svctest",
        "role": "toy_rw", "schema": "toy",
        "boundary_url": f"http://127.0.0.1:{_free_port()}", "boundary_deployment": "svctest",
    }), encoding="utf-8")
    lm_toml_path = lm_scratch / "boundary-multiplex.toml"
    lm_toml_path.write_text(
        "[deployments.svctest]\npghost = \"192.168.122.1\"\npgdatabase = \"toy\"\n"
        "pguser = \"toy_rw\"\npgschema = \"toy\"\npgkern = \"toy_kernel\"\n", encoding="utf-8")
    lm_env = dict(os.environ)
    lm_env["PICKUP_DEPLOYMENT"] = str(lm_dep_path)
    lm_env["AUTOHARN_FIXTURE_SANDBOX_WAIVER"] = env["AUTOHARN_FIXTURE_SANDBOX_WAIVER"]
    lm_pidfile = lm_scratch / ".autoharn-service.pid"

    # l: traps SIGTERM, exits ~1.5s later of its own accord -- well inside the production
    # SIGTERM grace window (5.0s, libexec/autoharn-service's own _STOP_SIGTERM_TIMEOUT_S).
    l_code = (
        "import signal, sys, time\n"
        "deadline = [None]\n"
        "def _h(signum, frame):\n"
        "    deadline[0] = time.monotonic() + 1.5\n"
        "signal.signal(signal.SIGTERM, _h)\n"
        "while True:\n"
        "    if deadline[0] is not None and time.monotonic() >= deadline[0]:\n"
        "        sys.exit(0)\n"
        "    time.sleep(0.02)\n"
    )
    l_proc = _spawn_mock_boundary_service(lm_toml_path, l_code)
    lm_pidfile.write_text(str(l_proc.pid), encoding="utf-8")
    t0 = time.monotonic()
    r = _run([str(AUTOHARN), "service", "stop"], lm_env)
    elapsed = time.monotonic() - t0
    if (r.returncode != 0 or "confirmed dead after SIGTERM" not in r.stdout
            or "ESCALATING" in r.stderr or lm_pidfile.is_file() or l_proc.poll() is None
            or elapsed < 1.4):
        print(f"l-stop-waits-for-delayed-exit: FAIL -- exit {r.returncode}, elapsed={elapsed:.2f}s, "
              f"stdout={r.stdout!r}, stderr={r.stderr!r}, pidfile_present={lm_pidfile.is_file()}, "
              f"proc_alive={l_proc.poll() is None}")
        ok = False
    else:
        print(f"l-stop-waits-for-delayed-exit: PASS (waited {elapsed:.2f}s for the real exit "
              f"before touching the pidfile -- RED against pre-fix code, which would have "
              f"removed the pidfile instantly while this mock was still alive for another "
              f"~1.5s, the exact orphan this item closes)")

    # m: ignores SIGTERM outright (SIG_IGN) -- only SIGKILL can end it. Must wait out the full
    # grace window, disclose the escalation LOUDLY, then confirm the SIGKILL death.
    m_code = (
        "import signal, time\n"
        "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
        "time.sleep(9999)\n"
    )
    m_proc = _spawn_mock_boundary_service(lm_toml_path, m_code)
    lm_pidfile.write_text(str(m_proc.pid), encoding="utf-8")
    t0 = time.monotonic()
    r = _run([str(AUTOHARN), "service", "stop"], lm_env)
    elapsed = time.monotonic() - t0
    if (r.returncode != 0 or "ESCALATING" not in r.stderr or "SIGKILL" not in r.stderr
            or "confirmed dead after SIGKILL" not in r.stdout or lm_pidfile.is_file()
            or m_proc.poll() is None or elapsed < 4.9):
        print(f"m-stop-escalates-to-sigkill-loud: FAIL -- exit {r.returncode}, "
              f"elapsed={elapsed:.2f}s, stdout={r.stdout!r}, stderr={r.stderr!r}, "
              f"pidfile_present={lm_pidfile.is_file()}, proc_alive={m_proc.poll() is None}")
        ok = False
    else:
        print(f"m-stop-escalates-to-sigkill-loud: PASS (waited out the {elapsed:.2f}s grace "
              f"window, LOUDLY disclosed the SIGKILL escalation in stderr, confirmed the kill, "
              f"pidfile removed only after death)")
    # Belt-and-braces cleanup, independent of whether `stop` (real or pre-fix) actually killed
    # them: l_proc dies on its own; m_proc (SIGTERM-immune) relies on `stop`'s own SIGKILL
    # escalation, which a RED run against pre-fix code never sends -- SIGKILL it here for real so
    # a RED run never leaves an orphaned mock process behind on this host.
    for _p in (l_proc, m_proc):
        try:
            _p.kill()
        except OSError:
            pass
    shutil.rmtree(lm_scratch, ignore_errors=True)

    # n-stop-refuses-pidfile-removal-while-alive: white-box -- imports libexec/autoharn-service
    # directly and fakes ONLY its own `os.kill` (a no-op recorder; `os.path`/`/proc` stay real,
    # delegated through __getattr__ below) so a REAL, genuinely-alive process's signals have no
    # effect, simulating the uninterruptible-kernel-sleep case SIGKILL cannot rule out either.
    n_scratch = Path("/tmp") / f"umbrella-cli-ensure-running-fixture-n-{os.getpid()}"
    n_scratch.mkdir(parents=True, exist_ok=True)
    n_dep_path = n_scratch / "deployment.json"
    n_toml_path = n_scratch / "boundary-multiplex.toml"
    n_toml_path.write_text("[deployments.svctest]\n", encoding="utf-8")
    n_dep_path.write_text(json.dumps({
        "db": "toy", "host": "192.168.122.1", "kern": "toy_kernel", "name": "svctest",
        "role": "toy_rw", "schema": "toy",
        "boundary_url": f"http://127.0.0.1:{_free_port()}", "boundary_deployment": "svctest",
    }), encoding="utf-8")
    n_pidfile = n_scratch / ".autoharn-service.pid"
    n_proc = subprocess.Popen(
        ["python3", "-c", "import time; time.sleep(30)",
         "serving.boundary_service", "--config", str(n_toml_path)])
    n_pidfile.write_text(str(n_proc.pid), encoding="utf-8")

    class _FakeOS:
        def __init__(self, real: object) -> None:
            self._real = real
            self.kill_calls: list[int] = []

        def kill(self, pid: int, sig: int) -> None:
            self.kill_calls.append(sig)  # recorded, never actually delivered

        def __getattr__(self, name: str) -> object:
            return getattr(self._real, name)

    _n_loader = importlib.machinery.SourceFileLoader(
        "autoharn_service_mod_n", str(REPO_ROOT / "libexec" / "autoharn-service"))
    _spec = importlib.util.spec_from_loader(_n_loader.name, _n_loader)
    assert _spec is not None
    autoharn_service_mod = importlib.util.module_from_spec(_spec)
    _n_loader.exec_module(autoharn_service_mod)
    fake_os = _FakeOS(os)
    autoharn_service_mod.os = fake_os
    autoharn_service_mod.DEPLOYMENT_PATH = n_dep_path
    autoharn_service_mod._STOP_SIGTERM_TIMEOUT_S = 0.3
    autoharn_service_mod._STOP_SIGKILL_TIMEOUT_S = 0.2
    autoharn_service_mod._STOP_POLL_INTERVAL_S = 0.05
    try:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            n_rc = autoharn_service_mod.cmd_stop(["stop"])
        n_stdout, n_stderr = out.getvalue(), err.getvalue()
        if (n_rc != 1 or "STILL ALIVE" not in n_stderr or not n_pidfile.is_file()
                or fake_os.kill_calls != [signal.SIGTERM, signal.SIGKILL]
                or int(n_pidfile.read_text(encoding="utf-8").strip()) != n_proc.pid):
            print(f"n-stop-refuses-pidfile-removal-while-alive: FAIL -- exit {n_rc}, "
                  f"stdout={n_stdout!r}, stderr={n_stderr!r}, "
                  f"pidfile_present={n_pidfile.is_file()}, kill_calls={fake_os.kill_calls}")
            ok = False
        else:
            print("n-stop-refuses-pidfile-removal-while-alive: PASS (SIGTERM and SIGKILL both "
                  "sent and both had no effect on this genuinely-alive process; stop REFUSED, "
                  "exit 1, and left the pidfile in place rather than orphan a live process while "
                  "reporting success)")
    finally:
        try:
            os.kill(n_proc.pid, signal.SIGKILL)
        except OSError:
            pass
        try:
            n_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        shutil.rmtree(n_scratch, ignore_errors=True)

    if ok:
        print("\nALL CASES PASS")
        return 0
    print("\nAT LEAST ONE CASE FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
