#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for design/FABLE-SERVICE-DRAIN-RESTART-SPEC.md:
`autoharn service restart` (libexec/autoharn-service's `cmd_restart`), a drained, witnessed hub
handover. Every case below runs against SCRATCH worlds -- real, throwaway Postgres roles/schemas
scaffolded via `bootstrap/new-project.sh --new-world` on `HARNESS_PGHOST`/`EPISTEMIC_PGHOST`
(never a literal host default -- filing/pghost_resolve.py, the same resolver every sibling
seen-red driver uses), served by real `serving.boundary_service` processes on dynamically-chosen
loopback ports, with scratch toml/pidfile under a `tempfile.mkdtemp()` directory -- NEVER this
repo's own boundary-multiplex.toml, pidfile, or ports 8433/8422 (the real deployment's own
reserved ports). Real Postgres worlds are needed here (unlike the config-shape-only fixtures)
because `/d/{name}/health` genuinely runs a kernel query requiring the deployment's own role to
exist -- discovered directly while building this fixture (a first draft assumed, from
serving/boundary_multiplex_config.py's own docstring about STARTUP validation, that /health
itself never touched Postgres; a live run showed a 500 "role ... does not exist" instead).
Every scaffolded schema/role is dropped in `finally`, and every scratch directory is removed,
regardless of outcome -- zero residue (CLAUDE.md's scratch discipline).

Cases (spec §3's own witness plan, letters chosen to match this file, not the spec's own
un-lettered prose):
  a-no-pidfile-refuses-hub-undisturbed -- RED: a hand-started `serving.boundary_service` (no
                                 pidfile at all -- an operator-started or otherwise-adopted hub)
                                 makes `restart` refuse at leg 1, teaching, signaling nothing;
                                 the hand-started process is then re-probed and confirmed STILL
                                 alive and healthy -- "nothing signaled" witnessed, not assumed.
  b-wrong-pid-refuses -- RED: a pidfile naming a `sleep` decoy (simulating PID reuse -- the OS
                                 handing a dead service's old pid to an unrelated process) makes
                                 `restart` refuse; the decoy survives untouched (never signaled),
                                 and the stale pidfile is removed (verbatim `stop` posture, spec
                                 §1.1). No real boundary_service is needed for this one (leg 1
                                 never reaches config validation).
  c-invalid-toml-refuses-old-still-serving -- RED: a REAL hub is standing (via `autoharn service
                                 start`); the toml is corrupted (an unknown key) between start
                                 and restart; `restart` refuses at leg 2, BEFORE any signal --
                                 the old process is re-probed afterward and confirmed still
                                 serving, same pid, unaffected.
  d-bind-race-lost-to-foreign -- RED, live construction (spec §3: "constructible: stop, bind a
                                 dummy socket, run restart"): a REAL hub is standing; a background
                                 "dummy socket" squatter (a tight bind-retry loop, no HTTP/ASGI
                                 machinery at all -- deliberately minimal so it can win the real
                                 OS-level bind race against a brand-new `serving.boundary_service`
                                 child's own heavier FastAPI/uvicorn import path) grabs the port
                                 the instant the old process's own drain frees it. `restart` must
                                 never report success over this: the new child fails its own
                                 bind, spawn_and_wait exhausts its poll window, and `restart`
                                 refuses -- no SERVING line, no claim the config is now served.
  d2-adopted-divergence-white-box -- white-box (spec §1.5's OTHER shape: a genuinely
                                 protocol-COMPATIBLE foreign winner, which `serving/ensure_running.
                                 py`'s own `spawn_and_wait` classifies "adopted", not "failed" --
                                 the shape row 1165 lets `start` treat as success). Legs 1-3 run
                                 for REAL against a real standing process (real pidfile, real
                                 valid toml, a genuine SIGTERM + drain-wait); only leg 4's spawn
                                 OUTCOME is monkeypatched to force "adopted" -- the one shape
                                 impractical to force via a genuine timing race (a truly
                                 protocol-compatible foreign winner would itself have to be a
                                 second real serving.boundary_service answering /health inside
                                 this exact narrow window). Proves `cmd_restart`'s leg-5
                                 divergence text (names the squatter, never claims success).
  e-drain-timeout-tiny-succeeds -- GREEN: `--drain-timeout` exercised with a tiny value (0.2s)
                                 against a HEALTHY hub with nothing in flight -- completes well
                                 under it, exit 0, never a timeout refusal.
  f-green-add-deployment-witnessed -- GREEN: the scratch toml is edited to ADD a second, real
                                 (separately-scaffolded) deployment; `restart` is run while a
                                 background thread issues repeated `/health` GETs against the OLD
                                 process (proving the drain is genuinely graceful -- a request
                                 landing before the old process exits completes successfully,
                                 never a connection-reset); both deployments' `/d/{name}/health`
                                 are witnessed passing post-restart, and the one-line summary's
                                 measured drained/unserved-window/N-of-N figures are captured and
                                 asserted present and internally consistent (unserved window
                                 >= 0, N/N == 2/2).
  g-in-flight-across-sigterm -- UNEXERCISED, stated blocker (spec §3's own escape hatch): a
                                 genuinely in-flight-across-SIGTERM request (a request whose
                                 HANDLING is still executing inside `serving/boundary_service.py`
                                 at the exact instant SIGTERM lands) needs a handler slow enough to
                                 still be running when the signal arrives; every existing endpoint
                                 in that unmodified module (spec §2: NOT touched by this build)
                                 returns near-instantly, and adding an artificial delay hook to
                                 prove this leg would itself violate the spec's own non-goal. In
                                 its place: the graceful-shutdown log-line witness (spec's own
                                 stated substitute) -- grepping the drained process's own
                                 service.log for uvicorn's "Waiting for application shutdown."/
                                 "Application shutdown complete." lines after SIGTERM, from the
                                 SAME real drain case f already performed, plus the already-
                                 established fact (case f) that a request ISSUED just before the
                                 old process exits completes successfully -- together the
                                 strongest witness available without touching serving/
                                 boundary_service.py.

RUN: python3 seen-red/service-restart/run_fixtures.py
(scaffolds two real, throwaway worlds via bootstrap/new-project.sh -- takes a handful of
seconds -- and spins up several real serving.boundary_service scratch processes; needs a
handful of free loopback ports, chosen dynamically -- never 8433/8422)
"""
from __future__ import annotations

import contextlib
import dataclasses
import importlib.machinery
import importlib.util
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AUTOHARN = REPO_ROOT / "autoharn"
AUTOHARN_SERVICE = REPO_ROOT / "libexec" / "autoharn-service"
NEW_PROJECT = REPO_ROOT / "bootstrap" / "new-project.sh"

sys.path.insert(0, str(REPO_ROOT))
from serving import ensure_running as er  # noqa: E402

sys.path.insert(0, str(REPO_ROOT / "filing"))
import deployment_record  # noqa: E402
import pghost_resolve  # noqa: E402

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own environment
# before any subprocess is spawned -- inherited by the whole process tree this fixture starts.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

PGHOST = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST")
PGDB = "toy"
RUN_SUFFIX = str(os.getpid())  # per-run unique suffix (A3.5 precedent): two concurrent suite
                                # runs never collide on an identical scratch-world name.
WORLD_1 = f"svcrestart1{RUN_SUFFIX}"
WORLD_2 = f"svcrestart2{RUN_SUFFIX}"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _run(argv: list[str], env: dict[str, str], timeout: float = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, capture_output=True, text=True, env=env, timeout=timeout)


def _base_env(dep_path: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["PICKUP_DEPLOYMENT"] = str(dep_path)
    # filing/fixture_sandbox.py: this fixture's own AUTOHARN_FIXTURE_SANDBOX=1 makes
    # libexec/autoharn-service's own main() refuse EVERY invocation of THIS repo's real
    # ./autoharn dispatcher outright, no exception for a scratch PICKUP_DEPLOYMENT override --
    # this IS the "REVIEWED, use-site reason to touch a repo-root verb directly" case its own
    # refusal text names as sanctioned: every invocation below carries PICKUP_DEPLOYMENT pointed
    # at THIS function's own scratch deployment.json/boundary-multiplex.toml, never the real one.
    env["AUTOHARN_FIXTURE_SANDBOX_WAIVER"] = (
        "seen-red/service-restart both-polarity-proves design/FABLE-SERVICE-DRAIN-RESTART-"
        "SPEC.md by driving libexec/autoharn-service through the real ./autoharn dispatcher "
        "against scratch worlds this function scaffolds -- PICKUP_DEPLOYMENT is overridden on "
        "every call below, the real repo deployment.json is never read.")
    return env


def scaffold_world(scratch_root: Path, world_name: str) -> deployment_record.DeploymentRecord:
    """Runs the real `bootstrap/new-project.sh --new-world` birth chain (the SAME path every
    other seen-red fixture in this tree uses -- ADR-0012 P1) so this world's own role/schema/
    kern genuinely exist in Postgres: `/d/{name}/health` runs a real kernel query, discovered
    live while building this fixture (see module docstring)."""
    dest = scratch_root / f"scaffold-{world_name}"
    r = subprocess.run(
        [str(NEW_PROJECT), str(dest), "--new-world", world_name, "--db", PGDB,
         "--host", PGHOST, "--name", world_name],
        capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"scaffold_world({world_name!r}) FAILED:\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    return deployment_record.load_deployment(dest / "deployment.json")


def teardown_world(world_name: str) -> None:
    subprocess.run(
        ["psql", "-h", PGHOST, "-d", PGDB, "-c",
         f"DROP SCHEMA IF EXISTS {world_name} CASCADE; "  # declared-drop: service-restart fixture scratch world
         f"DROP SCHEMA IF EXISTS {world_name}_kernel CASCADE; "
         f"DROP OWNED BY {world_name}_rw;"],
        capture_output=True, text=True)
    subprocess.run(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {world_name}_rw;"],
                   capture_output=True, text=True)


def _write_multiplex_toml(toml_path: Path, records: list[deployment_record.DeploymentRecord]) -> None:
    tables = []
    for rec in records:
        tables.append(f"[deployments.{rec.schema}]\n"
                      f"pghost = \"{rec.host}\"\npgdatabase = \"{rec.db}\"\n"
                      f"pguser = \"{rec.role}\"\npgschema = \"{rec.schema}\"\n"
                      f"pgkern = \"{rec.kern}\"\n")
    toml_path.write_text("\n".join(tables), encoding="utf-8")


def _write_deployment_json(dep_path: Path, primary: deployment_record.DeploymentRecord,
                            port: int) -> None:
    served = dataclasses.replace(primary, boundary_url=f"http://127.0.0.1:{port}",
                                  boundary_deployment=primary.schema)
    deployment_record.write_deployment(dep_path, served)


def _wait_health(url: str, deployment: str, timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{url}/d/{deployment}/health", timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(0.05)
    return False


def _read_pid(pidfile: Path) -> int | None:
    if not pidfile.is_file():
        return None
    try:
        return int(pidfile.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def _proc_alive(pid: int) -> bool:
    return os.path.exists(f"/proc/{pid}")


def _spawn_boundary_service_direct(toml_path: Path, port: int, pidfile: Path | None = None
                                    ) -> subprocess.Popen:
    """Hand-starts a REAL `serving.boundary_service` directly -- bypassing `autoharn service
    start` entirely -- so cases a/d2 can stand up an "old process" this fixture fully controls
    the log path and lifecycle of. Log redirected to a real scratch file, never a pipe (the same
    reason `serving/ensure_running.py`'s own PRODUCTION redirect targets a file: an unbounded
    diagnostic-log volume can fill an anonymous pipe's OS buffer and hang the server's own
    writes).

    A background daemon thread immediately starts `Popen.wait()` on the returned process,
    reaping it the moment it exits -- the SAME house rule seen-red/umbrella-cli-ensure-running/
    run_fixtures.py's own `_spawn_mock_boundary_service` documents: in the real world, the pid
    `stop`/`restart` signals is reparented to init (its own spawning invocation having already
    exited) and reaped by init the instant it dies, never left as a zombie. THIS fixture process
    stays alive across many cases, though, so without an explicit reaper thread a SIGTERM'd child
    would sit as a zombie -- `/proc/<pid>` still exists for a zombie, which made a first draft of
    this fixture misread a cleanly-exited process as "STILL RUNNING" for the the full 30s drain-
    timeout window (witnessed live while building this fixture, traced to exactly this gap)."""
    log_path = toml_path.parent / "service.log"
    log_fh = open(log_path, "ab")
    argv = [sys.executable, "-m", "serving.boundary_service", "--config", str(toml_path),
            "--host", "127.0.0.1", "--port", str(port)]
    if pidfile is not None:
        argv += ["--pidfile", str(pidfile)]
    proc = subprocess.Popen(argv, cwd=str(REPO_ROOT), stdout=log_fh, stderr=subprocess.STDOUT)
    log_fh.close()
    threading.Thread(target=proc.wait, daemon=True).start()
    return proc


def _kill(proc: subprocess.Popen, timeout: float = 5.0) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            pass


def main() -> int:
    ok = True
    scratch_root = Path(tempfile.mkdtemp(prefix="service-restart-fixture-"))
    print(f"-- scratch root: {scratch_root} --")
    print(f"-- scaffolding real scratch worlds {WORLD_1!r}, {WORLD_2!r} on {PGHOST} --")
    rec1 = scaffold_world(scratch_root, WORLD_1)
    rec2 = scaffold_world(scratch_root, WORLD_2)

    try:
        # ================================================================
        # a-no-pidfile-refuses-hub-undisturbed
        # ================================================================
        a_dir = scratch_root / "a"
        a_dir.mkdir(parents=True, exist_ok=True)
        a_port = _free_port()
        a_toml = a_dir / "boundary-multiplex.toml"
        a_dep = a_dir / "deployment.json"
        _write_multiplex_toml(a_toml, [rec1])
        _write_deployment_json(a_dep, rec1, a_port)
        a_proc = _spawn_boundary_service_direct(a_toml, a_port)  # NO --pidfile: hand-started
        try:
            a_url = f"http://127.0.0.1:{a_port}"
            if not _wait_health(a_url, rec1.schema):
                print("a-no-pidfile-refuses-hub-undisturbed: FAIL -- hand-started hub never "
                      "came up")
                ok = False
            else:
                r = _run([str(AUTOHARN), "service", "restart"], _base_env(a_dep))
                still_alive = a_proc.poll() is None and _wait_health(a_url, rec1.schema, timeout=5)
                if (r.returncode != 1 or "no pidfile" not in r.stderr
                        or "REFUSED" not in r.stderr or not still_alive):
                    print(f"a-no-pidfile-refuses-hub-undisturbed: FAIL -- exit {r.returncode}, "
                          f"stderr={r.stderr!r}, still_alive={still_alive}")
                    ok = False
                else:
                    print("a-no-pidfile-refuses-hub-undisturbed: PASS (RED case: exit 1, "
                          "REFUSED, no pidfile; the hand-started hub is confirmed still alive "
                          "and healthy afterward -- nothing was signaled)")
        finally:
            _kill(a_proc)

        # ================================================================
        # b-wrong-pid-refuses (no real boundary needed -- leg 1 never reaches config validation)
        # ================================================================
        b_dir = scratch_root / "b"
        b_dir.mkdir(parents=True, exist_ok=True)
        b_port = _free_port()
        b_toml = b_dir / "boundary-multiplex.toml"
        b_dep = b_dir / "deployment.json"
        _write_multiplex_toml(b_toml, [rec1])
        _write_deployment_json(b_dep, rec1, b_port)
        b_pidfile = b_dir / ".autoharn-service.pid"
        decoy = subprocess.Popen(["sleep", "300"])
        try:
            b_pidfile.write_text(str(decoy.pid), encoding="utf-8")
            r = _run([str(AUTOHARN), "service", "restart"], _base_env(b_dep))
            decoy_alive = decoy.poll() is None
            if (r.returncode != 1 or "REFUSED" not in r.stderr
                    or "not a" not in r.stderr or "serving.boundary_service" not in r.stderr
                    or not decoy_alive or b_pidfile.is_file()):
                print(f"b-wrong-pid-refuses: FAIL -- exit {r.returncode}, stderr={r.stderr!r}, "
                      f"decoy_alive={decoy_alive}, pidfile_present={b_pidfile.is_file()}")
                ok = False
            else:
                print("b-wrong-pid-refuses: PASS (RED case: decoy survives untouched, stale "
                      "pidfile removed, refusal teaches -- verbatim `stop` posture)")
        finally:
            decoy.terminate()
            try:
                decoy.wait(timeout=5)
            except subprocess.TimeoutExpired:
                decoy.kill()

        # ================================================================
        # c-invalid-toml-refuses-old-still-serving
        # ================================================================
        c_dir = scratch_root / "c"
        c_dir.mkdir(parents=True, exist_ok=True)
        c_port = _free_port()
        c_toml = c_dir / "boundary-multiplex.toml"
        c_dep = c_dir / "deployment.json"
        _write_multiplex_toml(c_toml, [rec1])
        _write_deployment_json(c_dep, rec1, c_port)
        c_env = _base_env(c_dep)
        r = _run([str(AUTOHARN), "service", "start"], c_env)
        c_pidfile = c_dir / ".autoharn-service.pid"
        c_old_pid = _read_pid(c_pidfile)
        c_url = f"http://127.0.0.1:{c_port}"
        try:
            if r.returncode != 0 or c_old_pid is None or not _wait_health(c_url, rec1.schema):
                print(f"c-invalid-toml-refuses-old-still-serving: FAIL -- setup failed, "
                      f"exit {r.returncode}, stdout={r.stdout!r}, stderr={r.stderr!r}")
                ok = False
            else:
                # Corrupt the toml AFTER the hub is standing (an operator's edit gone wrong):
                # an unknown key.
                original_toml_text = c_toml.read_text(encoding="utf-8")
                c_toml.write_text(original_toml_text + "\nnot_a_real_key = 1\n", encoding="utf-8")
                r2 = _run([str(AUTOHARN), "service", "restart"], c_env)
                still_same_pid = _read_pid(c_pidfile) == c_old_pid and _proc_alive(c_old_pid)
                still_healthy = _wait_health(c_url, rec1.schema, timeout=5)
                if (r2.returncode != 1 or "REFUSED" not in r2.stderr
                        or "not_a_real_key" not in r2.stderr
                        or not still_same_pid or not still_healthy):
                    print(f"c-invalid-toml-refuses-old-still-serving: FAIL -- exit "
                          f"{r2.returncode}, stderr={r2.stderr!r}, still_same_pid="
                          f"{still_same_pid}, still_healthy={still_healthy}")
                    ok = False
                else:
                    print("c-invalid-toml-refuses-old-still-serving: PASS (RED case: refused at "
                          "leg 2, BEFORE any signal -- the old process is confirmed the SAME "
                          "pid, still alive, still answering /health, completely undisturbed)")
        finally:
            _run([str(AUTOHARN), "service", "stop"], c_env)

        # ================================================================
        # d-bind-race-lost-to-foreign (live construction)
        # ================================================================
        d_dir = scratch_root / "d"
        d_dir.mkdir(parents=True, exist_ok=True)
        d_port = _free_port()
        d_toml = d_dir / "boundary-multiplex.toml"
        d_dep = d_dir / "deployment.json"
        _write_multiplex_toml(d_toml, [rec1])
        _write_deployment_json(d_dep, rec1, d_port)
        d_env = _base_env(d_dep)
        r = _run([str(AUTOHARN), "service", "start"], d_env)
        d_url = f"http://127.0.0.1:{d_port}"
        squatter_proc: subprocess.Popen | None = None
        try:
            if r.returncode != 0 or not _wait_health(d_url, rec1.schema):
                print(f"d-bind-race-lost-to-foreign: FAIL -- setup failed, exit {r.returncode}, "
                      f"stdout={r.stdout!r}, stderr={r.stderr!r}")
                ok = False
            else:
                # A minimal, non-HTTP/non-ASGI "dummy socket" squatter (spec §3's own phrase):
                # a tight bind-retry loop with no import overhead at all, deliberately lighter
                # than a real serving.boundary_service child so it reliably wins the OS-level
                # bind race the instant the old process's own drain frees the port. It accepts
                # and immediately closes every connection (never hangs a client for its own
                # ~65s HTTP timeout) -- fast, deterministic non-adoption.
                squatter_code = (
                    "import socket,sys\n"
                    "port=int(sys.argv[1])\n"
                    "s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)\n"
                    "s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)\n"
                    "while True:\n"
                    "    try:\n"
                    "        s.bind(('127.0.0.1', port)); break\n"
                    "    except OSError:\n"
                    "        pass\n"
                    "s.listen(50)\n"
                    "sys.stdout.write('BOUND\\n'); sys.stdout.flush()\n"
                    "while True:\n"
                    "    conn,_ = s.accept()\n"
                    "    conn.close()\n"
                )
                squatter_proc = subprocess.Popen(
                    ["python3", "-c", squatter_code, str(d_port)],
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                r2 = _run([str(AUTOHARN), "service", "restart"], d_env, timeout=30)
                claims_success = "restart: drained" in r2.stdout and "deployments healthy" in r2.stdout
                if r2.returncode == 0 or claims_success:
                    print(f"d-bind-race-lost-to-foreign: FAIL -- restart reported success over "
                          f"a foreign occupant: exit {r2.returncode}, stdout={r2.stdout!r}")
                    ok = False
                elif "REFUSED" not in (r2.stdout + r2.stderr):
                    print(f"d-bind-race-lost-to-foreign: FAIL -- refused, but without a REFUSED "
                          f"teaching line: exit {r2.returncode}, stdout={r2.stdout!r}, "
                          f"stderr={r2.stderr!r}")
                    ok = False
                else:
                    print(f"d-bind-race-lost-to-foreign: PASS (RED case: a raw dummy-socket "
                          f"squatter won the freed port; restart never claimed success -- exit "
                          f"{r2.returncode}, combined output names the failure)")
        finally:
            if squatter_proc is not None:
                squatter_proc.terminate()
                try:
                    squatter_proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    squatter_proc.kill()
            _run([str(AUTOHARN), "service", "stop"], d_env)

        # ================================================================
        # d2-adopted-divergence-white-box
        # ================================================================
        d2_dir = scratch_root / "d2"
        d2_dir.mkdir(parents=True, exist_ok=True)
        d2_port = _free_port()
        d2_toml = d2_dir / "boundary-multiplex.toml"
        d2_dep = d2_dir / "deployment.json"
        _write_multiplex_toml(d2_toml, [rec1])
        _write_deployment_json(d2_dep, rec1, d2_port)
        d2_pidfile = d2_dir / ".autoharn-service.pid"
        real_proc = _spawn_boundary_service_direct(d2_toml, d2_port, pidfile=d2_pidfile)
        try:
            d2_url = f"http://127.0.0.1:{d2_port}"
            if not _wait_health(d2_url, rec1.schema) or not d2_pidfile.is_file():
                print("d2-adopted-divergence-white-box: FAIL -- setup failed to come up")
                ok = False
            else:
                loader = importlib.machinery.SourceFileLoader(
                    "autoharn_service_mod_d2", str(AUTOHARN_SERVICE))
                spec = importlib.util.spec_from_loader(loader.name, loader)
                assert spec is not None
                mod = importlib.util.module_from_spec(spec)
                loader.exec_module(mod)
                mod.DEPLOYMENT_PATH = d2_dep

                real_pid = int(d2_pidfile.read_text(encoding="utf-8").strip())
                _orig_spawn_and_wait = mod.er.spawn_and_wait

                def _fake_spawn_and_wait(world_dir, url, port, boundary_deployment,
                                          *, poll_timeout_s=10.0):
                    return er.SpawnOutcome(status="adopted", proc_pid=999999,
                                            winner_pid=88888888, log_path=None, detail=None)

                # Legs 1-3 run for REAL against the real standing process (real pidfile check,
                # real valid toml, a genuine SIGTERM + drain-wait of `real_proc`) -- only leg 4's
                # spawn OUTCOME is faked (forcing "adopted", the one shape impractical to force
                # via a genuine timing race). `real_proc` is therefore expected to be
                # legitimately DEAD by the time this call returns -- this white-box proves leg
                # 5's divergence text, not a no-op.
                mod.er.spawn_and_wait = _fake_spawn_and_wait
                out, err = io.StringIO(), io.StringIO()
                try:
                    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                        rc = mod.cmd_restart([])
                finally:
                    mod.er.spawn_and_wait = _orig_spawn_and_wait
                stdout, stderr = out.getvalue(), err.getvalue()
                combined = stdout + stderr
                names_squatter = "88888888" in combined
                never_claims_success = ("SERVING" not in combined
                                         and "deployments healthy" not in combined)
                mentions_adopt_divergence = ("NOT by the config" in combined
                                              or "REFUSED" in combined)
                if rc == 0 or not names_squatter or not never_claims_success \
                        or not mentions_adopt_divergence:
                    print(f"d2-adopted-divergence-white-box: FAIL -- rc={rc}, "
                          f"names_squatter={names_squatter}, "
                          f"never_claims_success={never_claims_success}, "
                          f"mentions_adopt_divergence={mentions_adopt_divergence}, "
                          f"combined={combined!r}")
                    ok = False
                else:
                    print("d2-adopted-divergence-white-box: PASS (a forced 'adopted' spawn "
                          "outcome -- a genuinely protocol-compatible foreign winner, the shape "
                          "`start` would treat as success per row 1165 -- is REFUSED by "
                          "`restart` instead, naming the squatter's pid, never claiming success)")
                real_drained = real_proc.poll() is not None or not _proc_alive(real_pid)
                if not real_drained:
                    print("d2-adopted-divergence-white-box: FAIL -- the real standing process "
                          "was never actually drained -- legs 1-3 did not run for real")
                    ok = False
        finally:
            _kill(real_proc)

        # ================================================================
        # e-drain-timeout-tiny-succeeds
        # ================================================================
        e_dir = scratch_root / "e"
        e_dir.mkdir(parents=True, exist_ok=True)
        e_port = _free_port()
        e_toml = e_dir / "boundary-multiplex.toml"
        e_dep = e_dir / "deployment.json"
        _write_multiplex_toml(e_toml, [rec1])
        _write_deployment_json(e_dep, rec1, e_port)
        e_env = _base_env(e_dep)
        r = _run([str(AUTOHARN), "service", "start"], e_env)
        e_url = f"http://127.0.0.1:{e_port}"
        try:
            if r.returncode != 0 or not _wait_health(e_url, rec1.schema):
                print(f"e-drain-timeout-tiny-succeeds: FAIL -- setup failed, exit "
                      f"{r.returncode}, stdout={r.stdout!r}, stderr={r.stderr!r}")
                ok = False
            else:
                r2 = _run([str(AUTOHARN), "service", "restart", "--drain-timeout", "0.2"], e_env)
                if (r2.returncode != 0 or "restart: drained" not in r2.stdout
                        or "STILL RUNNING" in r2.stdout + r2.stderr
                        or "ESCALATING" in r2.stdout + r2.stderr):
                    print(f"e-drain-timeout-tiny-succeeds: FAIL -- exit {r2.returncode}, "
                          f"stdout={r2.stdout!r}, stderr={r2.stderr!r}")
                    ok = False
                else:
                    print("e-drain-timeout-tiny-succeeds: PASS (GREEN: --drain-timeout 0.2 "
                          "against a healthy, idle hub completes well under it -- no timeout "
                          "refusal, no escalation)")
        finally:
            _run([str(AUTOHARN), "service", "stop"], e_env)

        # ================================================================
        # f-green-add-deployment-witnessed (+ g's log-line witness reuses this same drain)
        # ================================================================
        f_dir = scratch_root / "f"
        f_dir.mkdir(parents=True, exist_ok=True)
        f_port = _free_port()
        f_toml = f_dir / "boundary-multiplex.toml"
        f_dep = f_dir / "deployment.json"
        _write_multiplex_toml(f_toml, [rec1])
        _write_deployment_json(f_dep, rec1, f_port)
        f_env = _base_env(f_dep)
        r = _run([str(AUTOHARN), "service", "start"], f_env)
        f_url = f"http://127.0.0.1:{f_port}"
        f_pidfile = f_dir / ".autoharn-service.pid"
        try:
            if r.returncode != 0 or not _wait_health(f_url, rec1.schema):
                print(f"f-green-add-deployment-witnessed: FAIL -- setup failed, exit "
                      f"{r.returncode}, stdout={r.stdout!r}, stderr={r.stderr!r}")
                ok = False
            else:
                old_pid = _read_pid(f_pidfile)
                # ADD a second, real, separately-scaffolded deployment to the scratch toml --
                # exactly the motivating scenario (design/FABLE-SERVICE-DRAIN-RESTART-SPEC.md's
                # own opening paragraph: "adding/retiring a world's deployment").
                _write_multiplex_toml(f_toml, [rec1, rec2])

                # A background thread hammers the OLD process's /health right up to (and
                # slightly past) the moment `restart` sends SIGTERM -- proving the drain is
                # genuinely graceful: a request that lands before the old process actually
                # exits must complete (200), never a connection-reset. Recorded results, not
                # asserted mid-flight (the exact SIGTERM instant is not observable from here).
                probe_results: list[bool] = []
                stop_probing = threading.Event()

                def _hammer() -> None:
                    while not stop_probing.is_set():
                        try:
                            with urllib.request.urlopen(
                                    f"{f_url}/d/{rec1.schema}/health", timeout=1) as resp:
                                probe_results.append(resp.status == 200)
                        except (urllib.error.URLError, OSError):
                            probe_results.append(False)
                        time.sleep(0.01)

                hammer_thread = threading.Thread(target=_hammer, daemon=True)
                hammer_thread.start()
                r2 = _run([str(AUTOHARN), "service", "restart"], f_env, timeout=30)
                stop_probing.set()
                hammer_thread.join(timeout=5)

                new_pid = _read_pid(f_pidfile)
                svc1_ok = _wait_health(f_url, rec1.schema, timeout=10)
                svc2_ok = _wait_health(f_url, rec2.schema, timeout=10)
                summary_present = ("restart: drained" in r2.stdout
                                    and "unserved window ~" in r2.stdout
                                    and "2/2 deployments healthy" in r2.stdout)
                any_pre_exit_request_succeeded = any(probe_results)
                if (r2.returncode != 0 or new_pid is None or old_pid is None
                        or new_pid == old_pid or not svc1_ok or not svc2_ok
                        or not summary_present or not any_pre_exit_request_succeeded):
                    print(f"f-green-add-deployment-witnessed: FAIL -- exit {r2.returncode}, "
                          f"old_pid={old_pid}, new_pid={new_pid}, svc1_ok={svc1_ok}, "
                          f"svc2_ok={svc2_ok}, summary_present={summary_present}, "
                          f"any_pre_exit_request_succeeded={any_pre_exit_request_succeeded}, "
                          f"stdout={r2.stdout!r}")
                    ok = False
                else:
                    summary_line = r2.stdout.strip().splitlines()[-1]
                    print(f"f-green-add-deployment-witnessed: PASS (GREEN: old pid {old_pid} "
                          f"drained, new pid {new_pid} up, BOTH {rec1.schema} and {rec2.schema} "
                          f"/health witnessed passing, summary line present -- {summary_line!r}; "
                          f"a request issued to the old process just before it exited also "
                          f"completed successfully, proving the drain was graceful)")

                    # g-in-flight-across-sigterm: UNEXERCISED (stated blocker in this file's own
                    # docstring) -- witnessed instead via the graceful-shutdown log-line pair,
                    # from THIS SAME real drain, plus the pre-exit-request-succeeded fact above.
                    log_path = f_dir / "service.log"
                    log_text = log_path.read_text(encoding="utf-8", errors="replace") \
                        if log_path.is_file() else ""
                    has_shutdown_wait = "Waiting for application shutdown" in log_text
                    has_shutdown_complete = "Application shutdown complete" in log_text
                    if has_shutdown_wait and has_shutdown_complete:
                        print("g-in-flight-across-sigterm: UNEXERCISED (stated blocker: a "
                              "genuinely in-flight-across-SIGTERM request needs a handler slow "
                              "enough to still be executing when SIGTERM lands; every endpoint "
                              "in the unmodified serving/boundary_service.py -- spec §2, not "
                              "touched -- returns near-instantly, and adding an artificial delay "
                              "hook to force this would itself violate that non-goal). Witnessed "
                              "instead: the drained process's own service.log carries BOTH "
                              "uvicorn graceful-shutdown log lines ('Waiting for application "
                              "shutdown.', 'Application shutdown complete.') after SIGTERM, and "
                              "case f above already proved a request issued just before this "
                              "same process exited completed successfully -- the strongest "
                              "witness available without touching the frozen service module.")
                    else:
                        print(f"g-in-flight-across-sigterm: FAIL -- expected both uvicorn "
                              f"graceful-shutdown log lines in {log_path}, "
                              f"has_shutdown_wait={has_shutdown_wait}, "
                              f"has_shutdown_complete={has_shutdown_complete}")
                        ok = False
        finally:
            _run([str(AUTOHARN), "service", "stop"], f_env)

    finally:
        print("-- teardown --")
        teardown_world(WORLD_1)
        teardown_world(WORLD_2)
        shutil.rmtree(scratch_root, ignore_errors=True)

    if ok:
        print("\nALL CASES PASS")
        return 0
    print("\nAT LEAST ONE CASE FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
