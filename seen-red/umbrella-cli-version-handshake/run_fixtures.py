#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for design/FABLE-AUTOHARN-UMBRELLA-CLI-SPEC.md §3/§7:
the wire-protocol version handshake (serving/boundary_cli_client.py's `check_protocol_version`).
Spins up a real `serving.boundary_service` process against a scratch config (a genuinely
unreachable Postgres host is fine -- /health never touches the database, see
serving/boundary_service.py's own `health()` handler) and drives the client against it directly,
in-process (no need to go through a full `led`/`pickup` invocation to exercise this one function).

Cases:
  a-server-carries-protocol-version -- a live boundary's own GET /health response actually
                                 carries `protocol_version`/`authn_mode` (not just the client's
                                 own belief about the shape).
  b-skewed-client-refuses -- RED case: a client whose own `_CLIENT_WIRE_PROTOCOL_VERSION` does
                                 not match the server's raises `ProtocolVersionMismatch`, naming
                                 BOTH versions; `report_protocol_mismatch` maps it to exit 4.
  c-matching-client-proceeds -- GREEN case: a client whose version matches proceeds silently, and
                                 caches the check per base URL (a second call is a cache hit, no
                                 second HTTP round trip -- verified by an unreachable base URL
                                 that would otherwise raise BoundaryUnreachable on a real call).

RUN: python3 seen-red/umbrella-cli-version-handshake/run_fixtures.py
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "serving"))
sys.path.insert(0, str(REPO_ROOT / "filing"))
import boundary_cli_client as bcc  # noqa: E402  (path set immediately above -- top-of-file, not lazy: CLAUDE.md's 2026-07-02 ban is on RUNTIME-deferred imports, and this sys.path setup + import both execute unconditionally at module load, the same pattern serving/boundary_service.py's own module docstring documents for its sibling imports)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> int:
    port = _free_port()
    scratch = Path("/tmp") / f"umbrella-cli-version-handshake-fixture-{os.getpid()}"
    scratch.mkdir(parents=True, exist_ok=True)
    toml_path = scratch / "boundary-multiplex.toml"
    toml_path.write_text(
        "[deployments.svctest]\n"
        "pghost = \"192.168.122.1\"\npgdatabase = \"toy\"\npguser = \"toy_rw\"\n"
        "pgschema = \"toy\"\npgkern = \"toy_kernel\"\n", encoding="utf-8")
    base = f"http://127.0.0.1:{port}"
    # Same interpreter-resolution convention bootstrap/new-project.sh's own PY variable uses
    # (this project's fastapi/uvicorn live in the generic venv, not necessarily on sys.executable
    # when this fixture is invoked from a bare python3 -- fall back to sys.executable only if
    # that venv is absent, e.g. a different machine's checkout).
    py = str(Path.home() / "w/vdc/venvs/generic/bin/python")
    if not Path(py).is_file():
        py = sys.executable
    proc = subprocess.Popen(
        [py, "-m", "serving.boundary_service", "--config", str(toml_path),
         "--port", str(port)],
        cwd=str(REPO_ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    ok = True
    try:
        deadline = time.monotonic() + 10.0
        up = False
        while time.monotonic() < deadline:
            try:
                urllib.request.urlopen(base, timeout=1.0)
                up = True
                break
            except urllib.error.HTTPError:
                up = True  # any HTTP response (even the bare-root 404) means uvicorn is up
                break
            except Exception:
                time.sleep(0.25)
        if not up:
            print("SETUP FAILED -- boundary_service never became reachable")
            return 1

        health = json.loads(urllib.request.urlopen(f"{base}/d/svctest/health", timeout=3.0).read())
        if "protocol_version" not in health or "authn_mode" not in health:
            print(f"a-server-carries-protocol-version: FAIL -- /health shape missing keys: {health}")
            ok = False
        else:
            print(f"a-server-carries-protocol-version: PASS ({health['protocol_version']!r}, "
                  f"{health['authn_mode']!r})")

        bcc._HANDSHAKE_CHECKED.clear()
        old = bcc._CLIENT_WIRE_PROTOCOL_VERSION
        bcc._CLIENT_WIRE_PROTOCOL_VERSION = "999-skewed"
        try:
            bcc.check_protocol_version(f"{base}/d/svctest", base)
            print("b-skewed-client-refuses: FAIL -- no ProtocolVersionMismatch raised")
            ok = False
        except bcc.ProtocolVersionMismatch as e:
            exit_code = bcc.report_protocol_mismatch("fixture", e)
            if exit_code == 4 and "999-skewed" in str(e) and health["protocol_version"] in str(e):
                print(f"b-skewed-client-refuses: PASS (RED case: exit {exit_code}, names both versions)")
            else:
                print(f"b-skewed-client-refuses: FAIL -- exit {exit_code}, message={e}")
                ok = False
        finally:
            bcc._CLIENT_WIRE_PROTOCOL_VERSION = old
            bcc._HANDSHAKE_CHECKED.clear()

        bcc.check_protocol_version(f"{base}/d/svctest", base)
        if f"{base}/d/svctest" not in bcc._HANDSHAKE_CHECKED:
            print("c-matching-client-proceeds: FAIL -- matching call did not populate the cache")
            ok = False
        else:
            # Cache hit: kill the server, then confirm a second check_protocol_version call
            # against the SAME base does NOT raise BoundaryUnreachable (it never makes the HTTP
            # call at all -- proving "cached thereafter" is real, not just documented).
            proc.terminate()
            proc.wait(timeout=10)
            try:
                bcc.check_protocol_version(f"{base}/d/svctest", base)
                print("c-matching-client-proceeds: PASS (GREEN case: cached, no second HTTP call)")
            except Exception as e:
                print(f"c-matching-client-proceeds: FAIL -- cache did not prevent a second call: {e}")
                ok = False
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        shutil.rmtree(scratch, ignore_errors=True)

    if ok:
        print("\nALL CASES PASS")
        return 0
    print("\nAT LEAST ONE CASE FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
