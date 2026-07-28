#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity live proof for work item birth-standing-steps-scaffold
(ledger row 270; design/PHOENIX-SURVIVAL-UNIVERSE-2026-07-28.md §3/§7).

WHAT THIS CLOSES: two operator-remembered birth steps that used to require a by-hand fix after
the fact (autoharn3 row 122's courier-registration fix; the autoharn3 cutover's by-hand
`world_identity` INSERT) are now real birth acts inside `bootstrap/new-project.sh`'s own
--new-world sequence:

  1. the `courier` principal is registered through the s40/s43 `registration_write` boundary
     ceremony (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.6), same shape as reviewer/commissioner/
     write-boundary, printed in the birth transcript.
  2. `kernel.world_identity` is seeded (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.1) with an
     owner-direct INSERT -- NOT through a boundary function, since the table's own grants give
     the world's granted role SELECT only (the spec's own witness plan seeds it "as owner,
     exactly as genesis is seeded") -- also printed in the birth transcript.

`bootstrap/templates/doctor.tmpl` gained two matching checks ("courier principal registered",
"world_identity populated"): PASS when the birth act ran, FAIL with a teach-text naming the
concrete fix command when it didn't, SKIP on a kernel lineage that predates s58.

CASES (real infra throughout -- a real `bootstrap/new-project.sh --new-world` birth against the
toy Postgres db, a real `./autoharn doctor` run, a real `serving.boundary_service` instance, and
a real `libexec/autoharn/courier` pull -- nothing stubbed at the Python-object level):

  RED   -- `bootstrap/new-project.sh` extracted at the merge-base commit (BASE_COMMIT, the tree
            immediately before this work item's fix) births a scratch world the SAME OLD way
            (courier/world_identity both skipped, exactly as the tree stood before this fix).
            The CURRENT `doctor.tmpl` (this world's birth still copies templates off THIS
            checkout's disk, since only new-project.sh's own body is swapped -- the same
            extraction trick seen-red/scaffold-governed-and-gitignore/run_fixtures.py already
            uses) is run against it: both new checks FAIL, each with its teach-text.
  GREEN -- the CURRENT `bootstrap/new-project.sh` births a second scratch world: the birth
            transcript itself contains both new acts' own lines, and doctor PASSes both checks.
  GREEN -- a real courier pull: the GREEN world's schema is served by a real
            `serving.boundary_service` instance, `libexec/autoharn/courier` is pointed at it
            plus a real (mock, but a real HTTP server, not stubbed) counterpart outbound feed,
            and a `missive_received` row lands authored by the birth-registered `courier`
            principal -- the row-122 class, closed end to end, not merely "the principal exists".

Scratch-only: two throwaway schema/kern/role triples in the toy db (never this repo's own
autoharn3 deployment), one throwaway `serving.boundary_service` subprocess on a dynamically
chosen loopback port, one throwaway HTTP mock counterpart -- all torn down on a clean run,
left standing (named) on any failure.

Usage: python3 seen-red/birth-standing-steps-scaffold/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own environment
# before any subprocess is spawned -- inherited by the whole process tree this fixture starts.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

# hooks/stamp_intercept.py stamps THIS SESSION'S OWN psql-touching Bash commands with
# app.vendor_* GUCs (via PGOPTIONS), HMAC'd against the CALLING deployment's (this repo's own
# autoharn3) kernel.stamp_secret -- kernel/lineage/s17-stamp-mechanism.sql's set_stamp trigger
# HARD REFUSES (never silently downgrades) any write that carries those GUCs but fails to
# validate against the TARGET schema's own secret, which a freshly-birthed scratch kernel's own
# fresh secret never will. The trigger's own leniency path is "no GUCs set at all" (stamp_verified
# = false, recorded not refused) -- so every psql/new-project.sh subprocess this fixture spawns
# runs with PGOPTIONS stripped from its environment, never inherited from this process's own.
FIXTURE_ENV = {k: v for k, v in os.environ.items() if k != "PGOPTIONS"}

REPO = Path(__file__).resolve().parents[2]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
SERVING = REPO / "serving"
COURIER = REPO / "libexec" / "autoharn" / "courier"
PGHOST = fixture_pghost()
PGDB = "toy"
BASE_COMMIT = "74d8b2d"  # the merge base this work item's fix landed on top of (pre-fix state)

WORLD_RED = "bshredw"
WORLD_GREEN = "bshgrnw"
COUNTERPART_WORLD = "bshcpartw"

FAILURES: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    print(f"  [{'ok' if cond else 'FAIL'}] {label}" + (f" -- {detail}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(f"{label}" + (f" -- {detail}" if detail else ""))


def sh(args: list[str], **kw) -> subprocess.CompletedProcess:
    env = kw.pop("env", FIXTURE_ENV)
    return subprocess.run(args, capture_output=True, text=True, env=env, **kw)


def psql(sql: str, **binds: str) -> subprocess.CompletedProcess:
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-tA"]
    for k, v in binds.items():
        args += ["-v", f"{k}={v}"]
    return subprocess.run(args, input=sql, capture_output=True, text=True, env=FIXTURE_ENV)


def teardown_world(world: str) -> None:
    schema, kern, role = world, f"{world}_kernel", f"{world}_rw"
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {schema} CASCADE; DROP SCHEMA IF EXISTS {kern} CASCADE;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {role};"])


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def wait_up(port: int, path: str, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=1) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(0.2)
    return False


def birth_world(script: Path, world: str, dest_root: Path) -> subprocess.CompletedProcess:
    dest = dest_root / world
    return sh(["bash", str(script), str(dest), "--new-world", world,
               "--db", PGDB, "--host", PGHOST], cwd=str(REPO))


def run_doctor(dest_root: Path, world: str) -> subprocess.CompletedProcess:
    dispatcher = dest_root / world / "autoharn"
    return sh([str(dispatcher), "doctor"], cwd=str(dest_root / world))


class _CounterpartHandler(BaseHTTPRequestHandler):
    """A real (stdlib http.server) counterpart -- one well-formed outbound missive addressed to
    WORLD_GREEN, serving the same `/d/<world>/health` and `/d/<world>/views/missive_outbound`
    shapes `libexec/autoharn/courier` actually reads (mirrors seen-red/missives-kernel-family/
    courier_witness_fixtures.py's own mock handlers, same field set)."""
    ROW = {"id": 1, "ts": "2026-07-28T00:00:00+00:00", "statement": "birth-standing-steps-scaffold witness",
           "missive_act": "assertion", "missive_seq": 1, "missive_cites": None,
           "missive_thread": f"{COUNTERPART_WORLD}/witness-1", "missive_protocol": 1,
           "missive_provenance": f"xrow:{COUNTERPART_WORLD}:1:" + "f" * 64,
           "missive_disposition": None, "missive_responds_to": None,
           "missive_author_world": COUNTERPART_WORLD, "missive_addressee_world": WORLD_GREEN}

    def log_message(self, fmt, *a):
        pass

    def do_GET(self):
        if self.path.startswith(f"/d/{COUNTERPART_WORLD}/health"):
            body = json.dumps({"world": COUNTERPART_WORLD, "service_principal": None,
                                "capabilities": {}, "protocol_version": "1",
                                "authn_mode": "single-operator"}).encode()
        elif self.path.startswith(f"/d/{COUNTERPART_WORLD}/views/missive_outbound"):
            body = (json.dumps([self.ROW]).encode()
                    if "after_id=0" in self.path or "after_id=" not in self.path
                    else json.dumps([]).encode())
        else:
            self.send_response(404); self.end_headers(); self.wfile.write(b'{"detail":"nf"}')
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)


def red_case(tmpdir: Path) -> None:
    print("### RED -- pre-fix new-project.sh births a world with both birth acts skipped")
    old_script = REPO / "bootstrap" / ".birth-standing-steps-fixture-old-new-project.sh"
    show = sh(["git", "show", f"{BASE_COMMIT}:bootstrap/new-project.sh"], cwd=str(REPO))
    check(f"RED setup: git show {BASE_COMMIT}:bootstrap/new-project.sh", show.returncode == 0, show.stderr)
    if show.returncode != 0:
        return
    old_script.write_text(show.stdout)
    old_script.chmod(0o755)
    try:
        teardown_world(WORLD_RED)
        r = birth_world(old_script, WORLD_RED, tmpdir)
        check("RED birth: pre-fix new-project.sh --new-world exits 0", r.returncode == 0,
              (r.stdout + r.stderr)[-1500:])
        if r.returncode != 0:
            return
        check("RED birth transcript: no courier registration line (confirms this really is the "
              "pre-fix shape, not an accidental no-op)",
              "'courier' registered" not in r.stdout and "(courier) registered" not in r.stdout)
        check("RED birth transcript: world_identity NOT seeded (confirms pre-fix shape)",
              "world_identity seeded" not in r.stdout)

        dr = run_doctor(tmpdir, WORLD_RED)
        print("  doctor stdout:\n" + "\n".join(f"    {l}" for l in dr.stdout.splitlines()))
        check("RED doctor: overall exit 1 (at least one FAIL)", dr.returncode == 1, dr.stderr)
        m_courier = re.search(r"^courier principal registered\s+FAIL\s+(.*)$", dr.stdout, re.MULTILINE)
        check("RED doctor: 'courier principal registered' FAILs", m_courier is not None, dr.stdout)
        if m_courier:
            check("RED doctor: courier FAIL teach-text names the fix command",
                  "register-principal courier tool" in m_courier.group(1), m_courier.group(1))
        m_wi = re.search(r"^world_identity populated\s+FAIL\s+(.*)$", dr.stdout, re.MULTILINE)
        check("RED doctor: 'world_identity populated' FAILs", m_wi is not None, dr.stdout)
        if m_wi:
            check("RED doctor: world_identity FAIL teach-text names the owner-INSERT fix",
                  "INSERT INTO" in m_wi.group(1) and "world_identity" in m_wi.group(1), m_wi.group(1))
    finally:
        if old_script.exists():
            old_script.unlink()
        teardown_world(WORLD_RED)


def green_case(tmpdir: Path) -> Path:
    print("\n### GREEN -- current new-project.sh births both acts")
    teardown_world(WORLD_GREEN)
    r = birth_world(NEW_PROJECT, WORLD_GREEN, tmpdir)
    check("GREEN birth: current new-project.sh --new-world exits 0", r.returncode == 0,
          (r.stdout + r.stderr)[-1500:])
    check("GREEN birth transcript: courier registration line present",
          "(courier) registered through the boundary ceremony" in r.stdout, r.stdout[-2000:])
    check("GREEN birth transcript: world_identity seed line present",
          f"world_identity seeded: world_name = '{WORLD_GREEN}'" in r.stdout, r.stdout[-2000:])

    dr = run_doctor(tmpdir, WORLD_GREEN)
    print("  doctor stdout:\n" + "\n".join(f"    {l}" for l in dr.stdout.splitlines()))
    # NOT asserted: overall doctor exit 0 -- this --new-world birth passes no --boundary-url/
    # --boundary-deployment, so "./autoharn led answers a read query" and (independently)
    # "boundary URL" correctly FAIL/SKIP on an unconfigured boundary (doctor.tmpl's own
    # pre-existing, unrelated behavior, not a claim this work item's fix touches) -- only the
    # two checks this work item ADDED are this case's concern.
    check("GREEN doctor: 'courier principal registered' PASSes",
          re.search(r"^courier principal registered\s+PASS", dr.stdout, re.MULTILINE) is not None,
          dr.stdout)
    check("GREEN doctor: 'world_identity populated' PASSes",
          re.search(r"^world_identity populated\s+PASS", dr.stdout, re.MULTILINE) is not None,
          dr.stdout)
    return tmpdir / WORLD_GREEN


def courier_pull_case(world_dir: Path) -> None:
    print("\n### GREEN -- a real courier pull against the birth-registered courier principal "
          "(the row-122 class, witnessed closed)")
    schema, kern, role = WORLD_GREEN, f"{WORLD_GREEN}_kernel", f"{WORLD_GREEN}_rw"

    toml_path = world_dir / "birth-standing-steps-fixture-multiplex.toml"
    self_port = free_port()
    toml_path.write_text(
        f'[deployments.{WORLD_GREEN}]\n'
        f'pghost = "{PGHOST}"\n'
        f'pgdatabase = "{PGDB}"\n'
        f'pguser = "{role}"\n'
        f'pgschema = "{schema}"\n'
        f'pgkern = "{kern}"\n')

    boundary_proc = subprocess.Popen(
        ["python3", "boundary_service.py", "--config", str(toml_path), "--port", str(self_port)],
        cwd=str(SERVING), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        env=FIXTURE_ENV)  # libpq (psycopg's own backend) honors PGOPTIONS too -- same strip as sh()/psql()
    counterpart_srv = HTTPServer(("127.0.0.1", 0), _CounterpartHandler)
    counterpart_port = counterpart_srv.server_address[1]
    counterpart_thread = Thread(target=counterpart_srv.serve_forever, daemon=True)
    counterpart_thread.start()
    try:
        up = wait_up(self_port, f"/d/{WORLD_GREEN}/health")
        check("courier pull setup: real boundary_service comes up for the birthed world", up)
        cp_up = wait_up(counterpart_port, f"/d/{COUNTERPART_WORLD}/health")
        check("courier pull setup: mock counterpart HTTP server comes up", cp_up)
        if not (up and cp_up):
            return

        courier_toml = world_dir / "birth-standing-steps-fixture-courier.toml"
        courier_toml.write_text(
            "[courier]\n"
            'authn = "single-operator"\n'
            f'self = "{WORLD_GREEN}"\n'
            f'self_base = "http://127.0.0.1:{self_port}"\n'
            "\n[courier.counterparts]\n"
            f'{COUNTERPART_WORLD} = "http://127.0.0.1:{counterpart_port}"\n')

        env = dict(FIXTURE_ENV)
        env["AUTOHARN_FIXTURE_SANDBOX_WAIVER"] = (
            "birth-standing-steps-scaffold run_fixtures.py: courier-toml points only at a "
            "scratch 127.0.0.1 boundary_service (this world's own birthed schema) and a "
            "127.0.0.1 mock counterpart this same fixture spawns and tears down, never this "
            "repo's real deployment.json")
        cr = sh(
            # fixture-scratch-pinning-guard-waiver: courier_toml (written just above, in this
            # same tmpdir) names only scratch 127.0.0.1 endpoints -- a boundary_service instance
            # over the freshly-birthed scratch schema and a mock counterpart HTTP server this
            # same fixture spawns and tears down -- never this checkout's own deployment.json
            # (gates/fixture_deployment_pin_guard.py, ledger row 1249).
            ["python3", str(COURIER), "--courier-toml", str(courier_toml)], cwd=str(REPO), env=env,
        )
        print("  courier stdout+stderr:\n" +
              "\n".join(f"    {l}" for l in (cr.stdout + cr.stderr).splitlines()))
        check("courier pull: exits 0", cr.returncode == 0, cr.stdout + cr.stderr)

        received = psql(
            'SELECT count(*) FROM :"schema".ledger l JOIN :"kern".principal p ON p.id = l.actor '
            "WHERE l.kind = 'missive_received' AND p.name = 'courier' "
            f"AND l.missive_author_world = '{COUNTERPART_WORLD}';",
            schema=schema, kern=kern).stdout.strip()
        check("courier pull: a missive_received row landed, authored by the birth-registered "
              "'courier' principal -- the row-122 class (courier missing at first pull) is gone",
              received == "1", f"count={received!r}")
    finally:
        boundary_proc.terminate()
        try:
            boundary_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            boundary_proc.kill()
        counterpart_srv.shutdown()


def main() -> int:
    tmpdir = Path(tempfile.mkdtemp(prefix="birth-standing-steps-fixture-"))
    ok = True
    try:
        red_case(tmpdir)
        world_dir = green_case(tmpdir)
        courier_pull_case(world_dir)
    except Exception as e:
        FAILURES.append(f"unhandled exception: {e.__class__.__name__}: {e}")
        ok = False
    finally:
        if not FAILURES:
            teardown_world(WORLD_RED)
            teardown_world(WORLD_GREEN)
            shutil.rmtree(tmpdir, ignore_errors=True)
        else:
            print(f"\n(leaving {tmpdir} and its scratch schemas standing as evidence -- at "
                  f"least one case failed)")

    if FAILURES:
        print(f"\nbirth-standing-steps-scaffold: {len(FAILURES)} FAILURE(S):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("\nbirth-standing-steps-scaffold: all cases behaved as expected. ✓")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
