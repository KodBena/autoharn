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

RUN: python3 seen-red/umbrella-cli-ensure-running/run_fixtures.py
(needs a free loopback port; picks one dynamically to avoid colliding with any of this host's
many concurrent boundary_service test fixtures)
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AUTOHARN = REPO_ROOT / "autoharn"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _run(argv: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, capture_output=True, text=True, env=env, timeout=30)


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

    r = _run([str(AUTOHARN), "service", "stop"], env)
    if r.returncode != 0 or "sent SIGTERM" not in r.stdout:
        print(f"e-explicit-stop: FAIL -- exit {r.returncode}, stdout={r.stdout!r}")
        ok = False
    else:
        print("e-explicit-stop: PASS")

    r = _run([str(AUTOHARN), "service", "stop"], env)
    if r.returncode != 1 or "REFUSED" not in r.stderr or "no pidfile" not in r.stderr:
        print(f"f-stop-without-pidfile-refuses: FAIL -- exit {r.returncode}, stderr={r.stderr!r}")
        ok = False
    else:
        print("f-stop-without-pidfile-refuses: PASS (RED case: exit 1, teaches, never guesses)")

    shutil.rmtree(scratch, ignore_errors=True)

    if ok:
        print("\nALL CASES PASS")
        return 0
    print("\nAT LEAST ONE CASE FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
