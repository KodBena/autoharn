"""tools/setup_tui/probes.py -- the live-connection/liveness probes honesty rule 2 requires
("a 'press enter when done' gate that VERIFIES the effect... rather than trusting the
keypress"). Every probe here re-checks reality; none of them trust an operator's say-so.

No new dependency: Postgres reachability goes through the `psql`/`pg_isready` binaries this
repo's own scripts already require (bootstrap/new-project.sh, bootstrap/teardown-world.sh);
HTTP probes use `urllib.request` (stdlib)."""
from __future__ import annotations

import ipaddress
import json
import re
import shutil
import socket
import subprocess
import urllib.error
import urllib.request

# Interpreter-boundary allowlist (law/adr/0012's 2026-07-18 amendment, "The interpreter
# boundary -- a value never crosses as program text": "where no carrier exists, a strict
# validation to a closed alphabet at the Port, which refuses what it cannot honor" -- the same
# check bootstrap/teardown-world.sh already carries for its schema/kern/role names). ONE home
# for the regex (ADR-0012 P1): both this module's own `pg_connect` (schema spliced into SQL
# text below) and `screens.py`'s dedicated-db path (db/role spliced into pg_hba/SQL text)
# import and call this, rather than each carrying its own copy of the pattern.
_IDENT_RE = re.compile(r"^[A-Za-z0-9_]+$")
# A real Postgres host is a hostname or IP literal -- never a bare [A-Za-z0-9_]+ identifier
# (dots, hyphens are ordinary in both DNS names and dotted-quad/v6-ish forms this codebase
# actually sees, e.g. "192.168.122.1"). Wider than _IDENT_RE by design, still closed: no
# quote/space/shell-metacharacter/TOML-control-character can pass.
_HOSTNAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
# The pg_hba `subnets` field (screens.py's dedicated-db path) is a CIDR/host token spliced
# unvalidated into the PREPARED pg_hba block until this fix -- digits, dots (IPv4), hex digits
# and colons (IPv6), and exactly one slash + prefix length is the closed alphabet a real CIDR
# ever needs. Character-class-closed FIRST (this regex), then parsed for real (`valid_subnet`
# below, via the stdlib `ipaddress` module) -- neither check alone is the Port; both together are
# (ADR-0012 P2: translate-and-validate, never a hand-rolled parse standing in for the real one).
_SUBNET_CHARS_RE = re.compile(r"^[0-9A-Fa-f.:/]+$")


def valid_identifier(name: str) -> bool:
    """True iff `name` is composed ONLY of letters, digits, underscore -- the only shape ever
    safe to splice into SQL/shell/config text this module or its callers construct by
    concatenation (no bind-variable carrier exists at those sites; this is the closed-alphabet
    refusal ADR-0012's interpreter-boundary amendment requires in that case)."""
    return bool(name) and bool(_IDENT_RE.fullmatch(name))


def valid_hostname(name: str) -> bool:
    """True iff `name` is composed ONLY of letters, digits, dot, hyphen, underscore -- the
    hostname/IP-literal-safe variant of `valid_identifier` for values that are a Postgres HOST
    (a DNS name or dotted-quad, never a bare SQL/shell identifier) but still get spliced into
    program text (a TOML config file, a shell copy-paste line) with no bind-variable carrier."""
    return bool(name) and bool(_HOSTNAME_RE.fullmatch(name))


def valid_subnet(token: str) -> bool:
    """True iff `token` is a syntactically closed-alphabet CIDR (digits, dots, IPv6 hex/colons,
    exactly one slash + prefix length) AND parses as a real network via the stdlib `ipaddress`
    module -- never a hand-rolled parse standing in for the real one. Used at the pg_hba-block
    splice site (screens.py's dedicated-db path, `pghba.generate_block`'s `subnets` argument),
    the same interpreter-boundary discipline `valid_identifier`/`valid_hostname` already carry
    for the other fields spliced into that same PREPARED block."""
    if not token or not _SUBNET_CHARS_RE.fullmatch(token) or token.count("/") != 1:
        return False
    try:
        ipaddress.ip_network(token, strict=False)
    except ValueError:
        return False
    return True


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
        if not valid_identifier(schema):
            return False, (
                f"REFUSED: schema '{schema}' contains characters outside [A-Za-z0-9_] -- "
                f"refusing to splice it into SQL text (law/adr/0012's interpreter-boundary "
                f"rule). Nothing probed."
            )
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


def pg_schema_exists(host: str, db: str, schema: str, timeout: float = 5.0) -> tuple[bool, str]:
    """`SELECT to_regnamespace('<schema>') IS NOT NULL` -- a read-only existence probe
    (design/FABLE-SETUP-TUI-CONFIG-FILE-SPEC.md §3's world-exists rejection leg: "REFUSED if the
    schema (or `<name>_kernel`) already exists on the target Postgres"). Never raises; an
    unreachable host or a validation refusal both report `(False, detail)` -- a probe that
    cannot reach the server has not PROVEN the schema exists, and must never be misread as
    "safe to proceed" (ADR-0002: a probe that cannot answer says so, it does not guess)."""
    if not valid_identifier(schema):
        return False, f"REFUSED: schema '{schema}' contains characters outside [A-Za-z0-9_]"
    psql = which("psql")
    if not psql:
        return False, "psql not found on PATH -- cannot probe"
    sql = f"SELECT to_regnamespace('{schema}') IS NOT NULL"
    argv = [psql, "-h", host, "-d", db, "-tA", "-c", sql]
    try:
        cp = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"psql schema-exists probe failed to run: {exc}"
    out = cp.stdout.strip()
    return (cp.returncode == 0 and out == "t"), (out or (cp.stdout + cp.stderr).strip())


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


def process_running(pattern: str) -> tuple[bool, str]:
    """Whether a process matching `pattern` (an argv substring, `pgrep -f`'s own semantics) is
    currently alive -- the liveness half of `checklist.py`'s new daemon-verification vocabulary
    (design/FABLE-SETUP-TUI-CHECKLIST-SPLIT-SPEC.md \xa73 point 3), used for a daemon that
    exposes no HTTP health endpoint of its own (otel-watch). `pattern` reaches `pgrep` as ONE
    argv element (`subprocess.run([..., "-f", pattern], ...)`, never shell text) -- the
    interpreter-boundary rule (ADR-0000's 2026-07-18 amendment) applies even to a read-only
    probe: a value never crosses as program text, regardless of whether the call it feeds is a
    write or a read. Never raises: `pgrep` absent from PATH, or any other OSError, reports
    `(False, "<reason>")` rather than crashing the probe (ADR-0002: fail loud in the RETURN
    value, since a probe's whole contract is 'report, never explode the caller')."""
    try:
        r = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True, timeout=5)
    except OSError as exc:
        return False, f"pgrep unavailable: {exc}"
    if r.returncode == 0 and r.stdout.strip():
        pids = r.stdout.strip().splitlines()
        return True, f"pgrep -f {pattern!r}: pid(s) {', '.join(pids)}"
    return False, f"pgrep -f {pattern!r}: no matching process"


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


def git_head_commit(repo_root: str) -> tuple[bool, str]:
    """`git -C <repo_root> rev-parse HEAD` -- a read-only preflight probe (PHASE-2 ADDITION: moved
    off `runner.run_command` so `screen_preflight` carries no plan-boundary act at all, per
    design/FABLE-SETUP-TUI-PURE-CORE-SPEC.md §2.8's purity gate -- this repo's own commit is a
    read, not a world-effect, exactly like every other probe in this module)."""
    cp = subprocess.run(["git", "-C", repo_root, "rev-parse", "HEAD"],
                         capture_output=True, text=True)
    return cp.returncode == 0, (cp.stdout + cp.stderr).strip()


def git_submodule_status(repo_root: str) -> tuple[bool, str]:
    """`git -C <repo_root> submodule status` -- same reasoning as `git_head_commit` above."""
    cp = subprocess.run(["git", "-C", repo_root, "submodule", "status"],
                         capture_output=True, text=True)
    return cp.returncode == 0, (cp.stdout + cp.stderr).strip()
