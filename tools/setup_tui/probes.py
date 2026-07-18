# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T21:32:16Z
#   last-change: 2026-07-18T21:32:21Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""tools/setup_tui/probes.py -- the live-connection/liveness probes honesty rule 2 requires
("a 'press enter when done' gate that VERIFIES the effect... rather than trusting the
keypress"). Every probe here re-checks reality; none of them trust an operator's say-so.

No new dependency: Postgres reachability goes through the `psql`/`pg_isready` binaries this
repo's own scripts already require (bootstrap/new-project.sh, bootstrap/teardown-world.sh);
HTTP probes use `urllib.request` (stdlib)."""
from __future__ import annotations

import json
import shutil
import socket
import subprocess
import urllib.error
import urllib.request


def which(name: str) -> str | None:
    return shutil.which(name)


def pg_reachable(host: str, timeout: float = 5.0) -> tuple[bool, str]:
    """TCP/server-liveness only (no auth, no db needed) -- pg_isready if present, else a bare
    connect via psql to postgres db which will fail on auth but succeeds at 'reachable' as long
    as the failure is an auth/db failure, not a connection failure."""
    pg_isready = which("pg_isready")
    if pg_isready:
        try:
            cp = subprocess.run([pg_isready, "-h", host], capture_output=True, text=True,
                                 timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, f"pg_isready -h {host} failed to run: {exc}"
        ok = cp.returncode == 0
        return ok, (cp.stdout + cp.stderr).strip()
    # No pg_isready on this host -- fall back to psql's own connection attempt distinguishing
    # "could not connect" (server truly unreachable) from any later-stage error (server is up).
    psql = which("psql")
    if not psql:
        return False, "neither pg_isready nor psql found on PATH -- cannot probe reachability"
    try:
        cp = subprocess.run(
            [psql, "-h", host, "-d", "postgres", "-tA", "-c", "SELECT 1"],
            capture_output=True, text=True, timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"psql probe failed to run: {exc}"
    text = (cp.stdout + cp.stderr)
    if "could not connect" in text or "could not translate" in text or "timeout expired" in text:
        return False, text.strip()
    return True, text.strip()


def pg_connect(host: str, db: str, role: str | None = None, schema: str | None = None,
               timeout: float = 5.0) -> tuple[bool, str]:
    """A real, authenticated connection probe: SELECT current_user (and current schema's
    to_regnamespace, if given) against <host>/<db> as <role>. This is the post-keypress
    verification honesty rule 2 requires for a prepared cluster-host act -- it is never
    satisfied merely because the operator pressed enter."""
    psql = which("psql")
    if not psql:
        return False, "psql not found on PATH -- cannot probe"
    sql = "SELECT current_user"
    if schema:
        sql += f", to_regnamespace('{schema}') IS NOT NULL AS schema_exists"
    argv = [psql, "-h", host, "-d", db]
    if role:
        argv += ["-U", role]
    argv += ["-tA", "-c", sql]
    try:
        cp = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"psql connect probe failed to run: {exc}"
    ok = cp.returncode == 0 and bool(cp.stdout.strip())
    return ok, (cp.stdout + cp.stderr).strip()


def http_get_json(url: str, timeout: float = 5.0) -> tuple[bool, int, object]:
    """GET `url`, returning (ok, status_code, parsed_json_or_raw_text). Never raises on a
    connection failure -- returns (False, 0, str(error)) so a probe screen can render it."""
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        status = exc.code
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        return False, 0, str(exc)
    try:
        parsed = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        parsed = body
    return (200 <= status < 300), status, parsed


def free_port(host: str = "127.0.0.1", start: int = 8420, span: int = 200) -> int:
    """Finds a free TCP port near `start` by actually binding and releasing it (never a guess
    that a port is free from a static table)."""
    for port in range(start, start + span):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"no free port found in [{start}, {start + span}) on {host}")
