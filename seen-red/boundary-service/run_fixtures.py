#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T07:49:10Z
#   last-change: 2026-07-18T12:16:13Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity witness for design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md's
§8 witness plan (W1-W12, A2's amendment; W13-W14, A3's amendment; W15-W19, A4's amendment;
W20-W23, A5's amendment; W21's float legs, A6's amendment; W24, A7's amendment; W25-W26,
A8's amendment; W27, A9's amendment). Real infra, no mocks:
CLASSIC scaffolds + manual chain applies in the TOY db (the exact pattern seen-red/
s43-typed-verdict-write-boundary/run_fixtures.py already banks, and this fixture imports
nothing new for scaffolding -- same helpers, re-derived here because the two fixtures scaffold
DIFFERENT chains for different reasons, not because the pattern needed a second home), plus a
REAL `serving.boundary_service` uvicorn subprocess bound to loopback, torn down before AND
after every world.

A3.5 (concurrent-runner safety): every scratch world/schema name below carries a PER-RUN
UNIQUE suffix (`RUN_SUFFIX`, this process's own pid) -- two independent suite runs against the
same toy db no longer collide on an identical scratch-world name (the root cause of a
transient fixture collision witnessed once during A3's review). Teardown (`teardown()`) is
scoped to the exact suffixed name it is called with, so a run only ever drops schemas/roles it
itself created.

WORLDS:
  WORLD PRE  -- chain ends at s42 (no s43): W3, every write endpoint capability_absent.
  WORLD B    -- chain ends at s43, full birth via the boundary (author, write-boundary,
                boundary-service): W1 (accepted write + read-back), W2 (refused write,
                journaled, verdict verbatim), W4 (/credited capability_absent, never a
                fallback), W5 (history-with-cause + credited-only-style exclusion from
                /rows/current), W6 (audit_served.py AGREE leg + a tampered negative control
                caught nonzero), the s22/s41 gate PRESENT legs (W11), W9 (oversized write body
                at both A2.2 checkpoints, typed 413, server alive, /health still answering),
                W13 (parse-closure legs: invalid UTF-8, an oversized integer literal, deeply
                nested body -- each a typed 422, server alive after each), W15 (non-finite
                legs: Infinity/NaN/1e400, typed 422 value axis), W16 (representability legs: a
                U+0000-bearing string, an unpaired UTF-16 surrogate, typed 422 representability
                axis), W17 (an over-range read-side id, path and query, typed 422), W18a (a
                FRESH server instance against a closed local port -- genuine psql exit 2 -> 503
                infra_failure), W19 (audit_served.py's exit-2 contract, using the same
                closed-port lever against ITS OWN direct-read leg while the served-fetch leg
                still targets world_b's live server), W20 (the representability-scan
                regression fixed: literal escape TEXT accepted through to the kernel; a real
                NUL and a real unpaired surrogate still refuse), W21 (an over-bigint write-
                payload field, typed 422 naming the field and bound -- plain-int form AND A6's
                float/exponent-form legs, `1e20` over-bound refused the same way, in-range
                `5.0` NOT newly refused by the boundary), W22 (a raw-socket
                trickled body, typed 408 within BODY_READ_TIMEOUT_S plus margin), W23
                (pagination on /standing/principals and /work/items, both polarities, including
                /work/items' id-less synthetic-ordinal fallback), W24 (a ~3000-level-nested,
                under-bound, otherwise-valid write body -- overflows the representability
                scan's OWN post-parse traversal, typed 422 structure axis, server alive; W13's
                deep-nesting leg, which overflows AT PARSE TIME instead, stays green), W25
                (A8's argv-wall legs: a ~200 KiB payload -- under checkpoint (a)'s 1 MiB
                raw-body bound, over checkpoint (b)'s re-denominated MAX_PSQL_ARG_BYTES --
                typed 413 naming the per-argument transport wall; a ~90 KiB payload passes
                BOTH checkpoints through to the kernel and gets a verdict, not a 413 --
                pre-A8, NO payload over ~131 KiB could ever have succeeded, the argv wall
                E2BIG'd it into a bare 500), W26 (A8's label consistency: Infinity/-Infinity/
                NaN under the int-declared `actor` field each refuse on the VALUE axis --
                same message family, never the id-domain "got inf" label the pre-A8 code
                gave Infinity by IEEE-754 comparison accident), the
                §9/A2.1/W12 in-process route-table closure assertion, and FINALLY (destructive,
                run last) W18b
                (ledger_current dropped on world_b -- genuine psql exit 3 -> 500
                unclassified_failure).
  WORLD NOCAP -- chain truncated BEFORE s22/s40/s41/s42/s43 (ends at s21): W10 (/health on a
                pre-s40 chain -> 200, null service_principal, no 500) and the s22/s41 gate
                ABSENT legs (W11) -- this world carries neither view, so both capability gates
                refuse.
  (no DB)    -- W7 bind guard, both legs (refusal leg + explicit-flag-allowed leg), standalone
                subprocess invocations of `python3 -m serving.boundary_service`; W14 (the hang
                leg -- a deployment pointed at a non-routable address, no toy-db world needed at
                all, since the connection never reaches auth); W27 (A9's admission bound -- the
                SAME non-routable-address lever as W14, a burst of 40 concurrent writes against
                it: the excess beyond MAX_INFLIGHT_KERNEL_CALLS=24 answers typed 503
                server_saturated promptly, /health fired concurrently during the burst answers
                within its own W14-proven margin -- never queued behind the burst's occupancy --
                and a single fresh write after the burst completes drains back to the ordinary
                W14 infra_failure shape, never server_saturated).
  (static)   -- W3's grep half (no DML string in serving/); W8 is UNEXERCISED BY CONSTRUCTION
                (panel-side; this repo never touches the panel repo) and is NAMED, not faked.
                W9's streaming-abort leg is likewise UNEXERCISED here -- see the W9 section
                below for why.

Usage: python3 seen-red/boundary-service/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import json
import os
import re
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

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
LINEAGE = REPO / "kernel" / "lineage"
SERVING = REPO / "serving"
PYVENV = Path.home() / "w" / "vdc" / "venvs" / "generic" / "bin" / "python"

# A3.5: a per-run unique suffix, pid-derived -- every scratch world name below is built from
# this, so two concurrent suite runs against the same toy db never collide on an identical
# scratch-world name (the root cause of a transient collision witnessed once during A3's
# review; see this file's own module docstring).
RUN_SUFFIX = str(os.getpid())

# A3.4/W14: an address deliberately NOT routable from this host -- the connection attempt is
# never refused (which would be fast and ordinary) and never routed (which would eventually
# ICMP-unreachable); it is simply never answered, exactly the "blackhole, accept-then-stall"
# class A3.1 names. No toy-db world is scaffolded for this leg: the connection never reaches
# postgres auth, so no real schema/kern/role need exist.
UNROUTABLE_HOST = "10.255.255.1"

sys.path.insert(0, str(REPO / "filing"))
sys.path.insert(0, str(SERVING))
import deployment_record  # noqa: E402
import pghost_resolve  # noqa: E402
import audit_served  # noqa: E402  (compare_row_sets -- the negative-control comparator, reused not re-derived)
import boundary_service  # noqa: E402  (W12 -- the in-process app.routes closure witness, and MAX_WRITE_BODY_BYTES/PSQL_CONNECT_TIMEOUT_S -- W9/W14 reuse the module's OWN bounds, never a second literal)

PGHOST, PGDB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_COMMON = [
    "s15-schema.sql", "s17-stamp-mechanism.sql", "s17-independence-vocabulary.sql",
    "s19-trigger-search-path.sql", "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
    "s25-commission-kind.sql", "s26-row-hash-chain.sql", "s27-chain-high-water.sql",
    "s28-work-parent-edge.sql", "s29-obligation-item-key-and-typed-close.sql",
    "s30-typed-dependency-edges.sql", "s31-supersession-uniform-retraction.sql",
    "s32-edge-views-single-home.sql", "s33-composite-discharge.sql",
    "s34-computed-grade-refusal.sql", "s35-validation-decomposition.sql",
    "s36-decision-grade.sql", "s37-violation-disposition.sql",
    "s38-bookkeeping-close.sql", "s39-blocks-start.sql",
    "s40-principal-identity-events.sql", "s41-principal-bindings-and-relations.sql",
    "s42-row-hash-full-coverage.sql",
]
CHAIN_PRE = CHAIN_COMMON  # s42 head -- no s43 (WORLD PRE)
CHAIN_B = CHAIN_COMMON + ["s43-typed-verdict-write-boundary.sql"]  # s43 head (WORLD B)
# A2's W10/W11: truncated BEFORE s22 (work-item views) and s40/s41 (identity events/views) --
# this chain carries NEITHER capability, so both gates' ABSENT leg is live here, and the chain
# is pre-s40 by construction (W10). Stops at s21 (session-aware-distinctness), the last common
# delta before s22.
CHAIN_NOCAP = CHAIN_COMMON[: CHAIN_COMMON.index("s22-work-item-ledger.sql")]

EXPECTED_ROUTES = {
    ("GET", "/health"), ("GET", "/rows/current"), ("GET", "/rows/{row_id}"),
    ("GET", "/rows/{row_id}/history"), ("GET", "/credited"),
    ("GET", "/standing/principals"), ("GET", "/work/items"),
    ("POST", "/write/ledger"), ("POST", "/write/review"),
    ("POST", "/write/registration"), ("POST", "/write/obligation"),
}


def actual_route_table(deployment_path: Path) -> set[tuple[str, str]]:
    """W12 (A2.1): asserts against `app.routes` DIRECTLY, in-process -- never the OpenAPI
    schema's self-report (§9's route claim was found false exactly because that self-report
    structurally cannot list a disabled/undeclared meta-route; A2.1 disabled them outright, so
    there is no schema endpoint left to ask). `create_app` only builds the ASGI route table; it
    opens no socket and issues no query, so calling it here needs no live server and no live DB
    -- any syntactically valid deployment record does (the identifiers need never resolve)."""
    rec = deployment_record.load_deployment(deployment_path)
    cfg = boundary_service.BoundaryConfig(rec)
    app = boundary_service.create_app(cfg)
    routes: set[tuple[str, str]] = set()
    for route in app.routes:
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", None)
        if methods and path:
            for m in methods:
                routes.add((m, path))
    return routes


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def teardown(world: str) -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {world} CASCADE; DROP SCHEMA IF EXISTS {world}_kernel CASCADE; "
        f"DROP OWNED BY {world}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {world}_rw;"])


def psql_tuples(sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"psql failed: {cp.stdout[-500:]} {cp.stderr[-500:]}")
    return cp.stdout.strip()


def psql_raw(script: str) -> subprocess.CompletedProcess[str]:
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-f", "/dev/stdin"], input=script)


def scaffold_classic(world: str, chain: list[str]) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix=f"{world}-seenred-"))
    world_dir = tmp / world
    schema, kern, role = world, f"{world}_kernel", f"{world}_rw"
    r = sh(["bash", str(NEW_PROJECT), str(world_dir),
            "--db", PGDB, "--host", PGHOST,
            "--schema", schema, "--kern", kern, "--role", role])
    if r.returncode != 0:
        raise RuntimeError(f"CLASSIC SCAFFOLD FAILED ({world}): {r.stdout[-1500:]} {r.stderr[-1500:]}")
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}"]
    for name in chain:
        args += ["-f", str(LINEAGE / name)]
    ra = sh(args)
    if ra.returncode != 0:
        raise RuntimeError(f"CLASSIC apply FAILED ({world}): {ra.stdout[-1500:]} {ra.stderr[-1500:]}")
    hexsecret = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    rs = sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
             "-c", f"TRUNCATE {kern}.stamp_secret;",
             "-c", f"INSERT INTO {kern}.stamp_secret (secret) VALUES (decode('{hexsecret}','hex'));"])
    if rs.returncode != 0:
        raise RuntimeError(f"stamp_secret seed FAILED ({world}): {rs.stdout[-800:]} {rs.stderr[-800:]}")
    # kern.chain_genesis is an s26-row-hash-chain.sql object -- a chain truncated BEFORE s26
    # (A2.5's WORLD NOCAP, which stops at s21) never creates it. Gate on chain membership
    # rather than firing the INSERT unconditionally and letting a real "relation does not
    # exist" error pass unchecked (the two prior lines' own fail-loud discipline, applied
    # here too -- ADR-0002: a silently-swallowed nonzero exit is exactly the failure this
    # tenet forbids, and it was a live gap in this function before this chain existed).
    if "s26-row-hash-chain.sql" in chain:
        genesis_hex = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
        rg = sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
                 "-c", f"INSERT INTO {kern}.chain_genesis (seed) VALUES ('{genesis_hex}') "
                       f"ON CONFLICT (only_one) DO NOTHING;"])
        if rg.returncode != 0:
            raise RuntimeError(f"chain_genesis seed FAILED ({world}): {rg.stdout[-800:]} {rg.stderr[-800:]}")
    return world_dir


def birth_pre_s43(world: str) -> None:
    """WORLD PRE has no boundary functions yet -- birth acts are the ordinary direct INSERT,
    exactly as bootstrap/new-project.sh's own pre-s43 scaffold path writes them."""
    S, K, R = world, f"{world}_kernel", f"{world}_rw"
    script = (
        f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
        f"INSERT INTO ledger (kind, statement, actor, principal_subject, principal_purpose)\n"
        f"VALUES ('principal_registered', 'author registered (fixture genesis exception)',\n"
        f"        (SELECT id FROM principal WHERE name='author'),\n"
        f"        (SELECT id FROM principal WHERE name='author'), 'fixture connection principal');\n"
        f"INSERT INTO ledger (kind, statement, actor, principal_subject, principal_db_role)\n"
        f"VALUES ('principal_standing_declared', 'role {R} -> author',\n"
        f"        (SELECT id FROM principal WHERE name='author'),\n"
        f"        (SELECT id FROM principal WHERE name='author'), '{R}');\n")
    r = psql_raw(script)
    if r.returncode != 0:
        raise RuntimeError(f"birth acts failed ({world}): {r.stderr[-600:]}")


def bw_call(world: str, fn: str, payload: dict) -> dict:
    S, K, R = world, f"{world}_kernel", f"{world}_rw"
    pj = json.dumps(payload).replace("'", "''")
    r = psql_raw(
        f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
        f"SELECT to_jsonb(v) FROM {K}.{fn}('{pj}'::jsonb) v;\n")
    if r.returncode != 0:
        raise RuntimeError(f"NON-VERDICT: {r.stderr.strip()[-500:]}")
    line = [ln for ln in r.stdout.splitlines() if ln.strip().startswith("{")][-1]
    return json.loads(line)


def birth_via_boundary(world: str) -> tuple[int, int]:
    """The s40/s43 birth acts through the boundary (WORLD B), PLUS this service's own s40
    registration ceremony (spec §4: "the service is registered at deployment as a principal
    (class tool, the s40 ceremony)") -- `boundary-service`, alongside `write-boundary`.
    Returns (author_id, boundary_service_principal_id)."""
    S, K = world, f"{world}_kernel"
    author = int(psql_tuples(f"SELECT id FROM {K}.principal WHERE name='author';"))
    login_role = psql_tuples("SELECT session_user;")
    for fn, payload in [
        ("ledger_write", {"kind": "principal_registered",
                          "statement": "author registered (fixture genesis exception)",
                          "actor": author, "principal_subject": author,
                          "principal_purpose": "fixture connection principal"}),
        ("ledger_write", {"kind": "principal_standing_declared",
                          "statement": f"role {world}_rw -> author", "actor": author,
                          "principal_subject": author, "principal_db_role": f"{world}_rw"}),
        ("ledger_write", {"kind": "principal_standing_declared",
                          "statement": f"login role {login_role} -> author (dual declaration)",
                          "actor": author, "principal_subject": author,
                          "principal_db_role": login_role}),
        ("registration_write", {"name": "write-boundary", "agent_class": "tool",
                                "actor": author,
                                "purpose": "the kernel write boundary's own recording "
                                           "identity (s43 fixture birth)"}),
        ("registration_write", {"name": "boundary-service", "agent_class": "tool",
                                "actor": author,
                                "purpose": "the FastAPI outer boundary Port's own registered "
                                           "principal (design/FABLE-LEDGER-BOUNDARY-SERVICE-"
                                           "SPEC.md §4 -- fixture-birth ceremony)"}),
    ]:
        v = bw_call(world, fn, payload)
        if v["disposition"] != "accepted":
            raise RuntimeError(f"birth act refused: {v}")
    boundary_service_id = int(psql_tuples(f"SELECT id FROM {K}.principal WHERE name='boundary-service';"))
    return author, boundary_service_id


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def free_closed_port() -> int:
    """A4/W18a: identical mechanics to `free_port` above -- bind then immediately close -- but
    named separately because the INTENT differs: `free_port` hands the port to a server this
    fixture is about to bind; this one hands a port that stays closed, so a subsequent connect
    attempt against it gets a fast ECONNREFUSED (genuine connection-level failure, psql exit 2)
    rather than a stall (W14's already-covered blackhole/accept-then-silent class)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def write_scratch_deployment(tmpdir: Path, world: str) -> Path:
    rec = deployment_record.DeploymentRecord(
        db=PGDB, host=PGHOST, schema=world, kern=f"{world}_kernel", role=f"{world}_rw", name=world)
    path = tmpdir / f"{world}-deployment.json"
    deployment_record.write_deployment(path, rec)
    return path


def start_server(deployment_path: Path, host: str = "127.0.0.1", port: int | None = None,
                  extra_flag: bool = False, env_overrides: dict[str, str] | None = None
                  ) -> tuple[subprocess.Popen, int]:
    """`env_overrides` (A4/W18a): merged over this process's own environment before launch --
    used to force a genuine connection-refusal leg (PGPORT pointed at a closed local port) that
    is distinct from W14's already-covered blackhole/stall leg, without needing a second
    deployment-record shape (deployment.json carries no port field of its own; PGPORT is the
    one lever psql itself already understands, the same lever _psql's own PGCONNECT_TIMEOUT
    override in boundary_service.py uses for the time axis)."""
    if port is None:
        port = free_port()
    args = [str(PYVENV), "-m", "serving.boundary_service",
            "--deployment", str(deployment_path), "--host", host, "--port", str(port)]
    if extra_flag:
        args.append("--i-understand-this-exposes-the-ledger")
    env = dict(os.environ)
    if env_overrides:
        env.update(env_overrides)
    proc = subprocess.Popen(args, cwd=str(REPO), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, env=env)
    return proc, port


def wait_health(base_url: str, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(base_url + "/health", timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(0.3)
    return False


def http_get(url: str) -> tuple[int, object]:
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def http_post(url: str, payload: dict) -> tuple[int, object]:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _post_trickled(host: str, port: int, path: str, declared_len: int, total_wall_s: float,
                    chunk_size: int = 1) -> tuple[int, dict | None, float]:
    """W22 (A5.3): drives the body-read-phase time bound the same way W9's own module docstring
    named as UNEXERCISED there -- a raw `socket` client, because `urllib`/`http.client` (every
    other HTTP call this fixture makes) offer no supported way to hold a POST body open
    mid-stream; this is a SEPARATE, minimal transport used ONLY for this one leg, not a general
    replacement for `urllib` elsewhere in this file. Sends the HTTP/1.1 request line + headers
    (a real `Content-Length: declared_len`) immediately, then trickles exactly ONE byte of body
    every `total_wall_s / declared_len` seconds -- so the connection stays open, genuinely
    sending real bytes throughout, and never completes the declared length within
    `BODY_READ_TIMEOUT_S`. A background thread does the trickling so the main thread can block
    on `recv` for the server's own response (which, on the read-timeout leg, arrives BEFORE the
    trickle finishes -- the point of the witness). Returns (status, parsed-json-body-or-None,
    wall-clock elapsed until a response was read or the socket closed)."""
    start = time.time()
    body = b"x" * declared_len
    header = (
        f"POST {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Content-Type: application/json\r\n"
        f"Content-Length: {declared_len}\r\n"
        f"Connection: close\r\n\r\n"
    ).encode()
    per_chunk_delay = total_wall_s / max(1, declared_len // chunk_size)
    sock = socket.create_connection((host, port), timeout=total_wall_s + 20)

    def _trickle() -> None:
        sent = 0
        try:
            while sent < len(body):
                chunk = body[sent:sent + chunk_size]
                sock.sendall(chunk)
                sent += len(chunk)
                time.sleep(per_chunk_delay)
        except OSError:
            pass  # the server closed its read side once it gave up -- expected on the timeout leg

    sock.sendall(header)
    t = threading.Thread(target=_trickle, daemon=True)
    t.start()
    # `Connection: close` above asks the server to close its side once it has written a
    # response -- so reading until `recv` returns empty (peer closed) is the ordinary, robust
    # way to collect a small response, no header-parsing heuristic needed. Bounded by the same
    # generous settimeout as the connect above (never the OS default).
    resp = b""
    try:
        sock.settimeout(total_wall_s + 20)
        while True:
            data = sock.recv(4096)
            if not data:
                break
            resp += data
    except OSError:
        pass
    elapsed = time.time() - start
    sock.close()
    t.join(timeout=5)
    status = None
    parsed: dict | None = None
    if resp:
        try:
            status_line = resp.split(b"\r\n", 1)[0].decode()
            status = int(status_line.split(" ", 2)[1])
            body_text = resp.split(b"\r\n\r\n", 1)[1]
            parsed = json.loads(body_text)
        except (IndexError, ValueError, UnicodeDecodeError):
            pass
    return status, parsed, elapsed


def stop_server(proc: subprocess.Popen) -> str:
    proc.terminate()
    try:
        out, _ = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _ = proc.communicate(timeout=5)
    return out or ""


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    procs: list[subprocess.Popen] = []
    # A3.5: every scratch world name carries RUN_SUFFIX (this process's pid) -- see the module
    # docstring's "concurrent-runner safety" note.
    world_pre = f"svcfxpre{RUN_SUFFIX}"
    world_b = f"svcfxb{RUN_SUFFIX}"
    world_nocap = f"svcfxnocap{RUN_SUFFIX}"
    for w in (world_pre, world_b, world_nocap):
        teardown(w)
    try:
        # ============================= W3: WORLD PRE (no s43) =============================
        print(f"== scaffolding classic world {world_pre} (chain ends {CHAIN_PRE[-1]}) ==")
        wpre = scaffold_classic(world_pre, CHAIN_PRE)
        tmps.append(wpre.parent)
        birth_pre_s43(world_pre)
        dep_pre = write_scratch_deployment(wpre.parent, world_pre)
        proc_pre, port_pre = start_server(dep_pre)
        procs.append(proc_pre)
        up = wait_health(f"http://127.0.0.1:{port_pre}")
        results = {}
        if up:
            for surface in ("ledger", "review", "registration", "obligation"):
                status, body = http_post(f"http://127.0.0.1:{port_pre}/write/{surface}", {"x": "y"})
                results[surface] = (status, body)
        out_pre = stop_server(proc_pre)
        grep_dml = subprocess.run(
            ["grep", "-nE", "INSERT INTO [A-Za-z_.]+ *\\(|UPDATE [A-Za-z_.]+ SET|DELETE FROM [A-Za-z_.]+ ",
             str(SERVING / "boundary_service.py"), str(SERVING / "audit_served.py"),
             str(SERVING / "boundary_models.py")],
            capture_output=True, text=True)
        check("w3-pre-s43-capability-absent-and-no-dml-string",
              up and all(status == 409 and body.get("disposition") == "capability_absent"
                         and body.get("capability") == "s43-boundary"
                         for status, body in results.values())
              and grep_dml.returncode == 1,  # grep exit 1 = no match found anywhere
              f"server up={up}; per-surface (status, disposition, capability)="
              f"{ {k: (v[0], v[1].get('disposition'), v[1].get('capability')) for k, v in results.items()} }; "
              f"grep for INSERT/UPDATE/DELETE DML strings in serving/*.py: "
              f"{'NONE FOUND (exit 1)' if grep_dml.returncode == 1 else grep_dml.stdout}; "
              f"server tail: {out_pre[-300:] if not up else '(server came up cleanly)'}",
              failures)

        # ============================= WORLD B (s43 head) =============================
        print(f"== scaffolding classic world {world_b} (chain ends {CHAIN_B[-1]}) ==")
        wb = scaffold_classic(world_b, CHAIN_B)
        tmps.append(wb.parent)
        author_id, svc_id = birth_via_boundary(world_b)
        dep_b = write_scratch_deployment(wb.parent, world_b)
        proc_b, port_b = start_server(dep_b)
        procs.append(proc_b)
        base = f"http://127.0.0.1:{port_b}"
        up_b = wait_health(base)

        # -- /health: route count (§9 closure), capability manifest, service_principal named.
        st_h, body_h = http_get(base + "/health") if up_b else (0, {})
        check("closure-health-and-route-count",
              up_b and st_h == 200 and body_h.get("capabilities", {}).get("s43_boundary") is True
              and body_h.get("service_principal") == "boundary-service",
              f"health status={st_h} body={body_h}", failures)

        # -- W1: accepted write, read back verbatim.
        st1, v1 = http_post(base + "/write/ledger",
                            {"kind": "note", "statement": "boundary-service W1 accepted write",
                             "actor": author_id}) if up_b else (0, {})
        st1r, row1 = http_get(f"{base}/rows/{v1.get('row_id')}") if up_b and v1.get("disposition") == "accepted" else (0, {})
        check("w1-accepted-write-and-readback",
              up_b and st1 == 200 and v1.get("disposition") == "accepted" and v1.get("row_id")
              and st1r == 200 and row1.get("statement") == "boundary-service W1 accepted write"
              and row1.get("id") == v1.get("row_id"),
              f"POST /write/ledger status={st1} verdict={v1}; GET /rows/{{id}} status={st1r} "
              f"row.statement={row1.get('statement')!r}", failures)

        # -- W2: refused write (illegal kind -> kernel CHECK, journaled, verdict verbatim).
        st2, v2 = http_post(base + "/write/ledger",
                            {"kind": "bogus_kind_not_in_vocabulary",
                             "statement": "boundary-service W2 refused write"}) if up_b else (0, {})
        wr_row = None
        if up_b and v2.get("disposition") == "refused" and v2.get("refusal_id"):
            _, wr_row = http_get(f"{base}/rows/{v2['refusal_id']}")
        check("w2-refused-write-journaled-verdict-verbatim",
              up_b and st2 == 200 and v2.get("disposition") == "refused" and v2.get("sqlstate") == "23514"
              and v2.get("refusal_id") and v2.get("message")
              and wr_row is not None and wr_row.get("kind") == "write_refused"
              and wr_row.get("refusal_sqlstate") == "23514" and wr_row.get("refusal_surface") == "ledger",
              f"POST /write/ledger status={st2} verdict={v2}; committed write_refused row: "
              f"kind={wr_row.get('kind') if wr_row else '?'} "
              f"sqlstate={wr_row.get('refusal_sqlstate') if wr_row else '?'}", failures)

        # -- W4: /credited capability_absent (no fallback -- this world has no s44 view).
        st4, v4 = http_get(base + "/credited") if up_b else (0, {})
        check("w4-credited-capability-absent-never-fallback",
              up_b and st4 == 409 and v4.get("disposition") == "capability_absent"
              and v4.get("capability") == "s44-credited-view",
              f"GET /credited status={st4} body={v4}", failures)

        # -- W5: history-with-cause + credited-only-style exclusion from /rows/current.
        st5a, orig = http_post(base + "/write/ledger",
                               {"kind": "decision", "statement": "W5 original decision",
                                "actor": author_id}) if up_b else (0, {})
        st5b, sup = http_post(base + "/write/ledger",
                              {"kind": "decision", "statement": "W5 superseding decision",
                               "actor": author_id, "supersedes": orig.get("row_id")}) if up_b else (0, {})
        st5h, hist = http_get(f"{base}/rows/{sup.get('row_id')}/history") if up_b else (0, [])
        hist_ids = {r["id"] for r in hist} if isinstance(hist, list) else set()
        st5c, current_page = http_get(f"{base}/rows/current?after_id=0&limit=1000") if up_b else (0, [])
        current_ids = {r["id"] for r in current_page} if isinstance(current_page, list) else set()
        check("w5-history-with-cause-and-current-exclusion",
              up_b and st5a == 200 and st5b == 200 and orig.get("disposition") == "accepted"
              and sup.get("disposition") == "accepted"
              and orig["row_id"] in hist_ids and sup["row_id"] in hist_ids
              and orig["row_id"] not in current_ids and sup["row_id"] in current_ids,
              f"original row {orig.get('row_id')} + superseding row {sup.get('row_id')} both "
              f"reachable via /rows/{{id}}/history ({sorted(hist_ids)}); original ABSENT from "
              f"/rows/current ({orig.get('row_id') in current_ids}), superseding row present "
              f"({sup.get('row_id') in current_ids})", failures)

        # -- W6: audit_served.py AGREE leg + a tampered negative control caught nonzero.
        audit_cp = sh([str(PYVENV), str(SERVING / "audit_served.py"),
                      "--base-url", base, "--deployment", str(dep_b)]) if up_b else None
        served_ok, served_rows = http_get(f"{base}/rows/current?after_id=0&limit=1000") if up_b else (0, [])
        tampered = [dict(r, statement="TAMPERED-FOR-NEGATIVE-CONTROL") for r in served_rows[:1]] + served_rows[1:]
        neg_diffs = audit_served.compare_row_sets(tampered, served_rows) if served_rows else ["no rows to tamper"]
        check("w6-audit-served-agree-and-negative-control",
              up_b and audit_cp is not None and audit_cp.returncode == 0 and "AGREE" in audit_cp.stdout
              and len(neg_diffs) > 0,
              f"audit_served.py exit={audit_cp.returncode if audit_cp else '?'} "
              f"stdout={(audit_cp.stdout.strip() if audit_cp else '?')!r}; tampered-vs-real "
              f"negative control diffs={neg_diffs} (nonzero expected -- the comparator catches "
              f"the deliberate perturbation)", failures)

        # -- W11 PRESENT legs: this world carries both s22 and s41 views -- both gates serve.
        st_sp, standing = http_get(base + "/standing/principals") if up_b else (0, None)
        st_wi, witems = http_get(base + "/work/items") if up_b else (0, None)
        check("w11-present-legs-s41-and-s22-serve",
              up_b and st_sp == 200 and isinstance(standing, list)
              and st_wi == 200 and isinstance(witems, list),
              f"GET /standing/principals status={st_sp} type={type(standing).__name__}; "
              f"GET /work/items status={st_wi} type={type(witems).__name__} -- both views "
              f"present on this chain, so neither gate refuses", failures)

        # -- W9 (A2.2): oversized write body at BOTH checkpoints, typed 413, server stays alive.
        # Checkpoint (a): raw body over the bound, plain ASCII -- refused before JSON parsing.
        oversized_raw = json.dumps({
            "kind": "note", "statement": "x" * (boundary_service.MAX_WRITE_BODY_BYTES + 2000),
            "actor": author_id}).encode()
        req9a = urllib.request.Request(
            base + "/write/ledger", data=oversized_raw,
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req9a, timeout=15) as resp:
                st9a, body9a = resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            st9a, body9a = e.code, json.loads(e.read())
        # Checkpoint (b): a raw body UNDER checkpoint (a)'s raw-body bound (non-ASCII, compact
        # UTF-8) whose re-serialization (json.dumps's default ensure_ascii=True, \uXXXX-escaping
        # every multi-byte character) lands OVER checkpoint (b)'s bound -- proves checkpoint (b)
        # is a REAL second gate, not a duplicate of (a): CJK char = 3 raw UTF-8 bytes, 6 escaped
        # bytes. A8 re-denominated (b) at MAX_PSQL_ARG_BYTES (the per-argument transport wall's
        # margin), so the refusal's limit_bytes must now name THAT bound, not (a)'s -- the
        # 413 shape's numbers stay honest about which bound fired.
        cjk_count = (boundary_service.MAX_WRITE_BODY_BYTES // 3) - 20000  # raw ~<(a)'s bound, escaped ~2x>(a)'s bound, and far >(b)'s
        oversized_b_payload = {"kind": "note", "statement": "中" * cjk_count, "actor": author_id}
        oversized_b_raw = json.dumps(oversized_b_payload, ensure_ascii=False).encode("utf-8")
        raw_len_b = len(oversized_b_raw)
        reserialized_len_b = len(json.dumps(oversized_b_payload).encode("utf-8"))
        req9b = urllib.request.Request(
            base + "/write/ledger", data=oversized_b_raw,
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req9b, timeout=15) as resp:
                st9b, body9b = resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            st9b, body9b = e.code, json.loads(e.read())
        st9h, body9h = http_get(base + "/health") if up_b else (0, {})
        check("w9-oversized-write-body-both-checkpoints-server-alive",
              up_b
              and st9a == 413 and body9a.get("disposition") == "payload_too_large"
              and body9a.get("limit_bytes") == boundary_service.MAX_WRITE_BODY_BYTES
              and raw_len_b < boundary_service.MAX_WRITE_BODY_BYTES
              and reserialized_len_b > boundary_service.MAX_PSQL_ARG_BYTES
              and st9b == 413 and body9b.get("disposition") == "payload_too_large"
              and body9b.get("limit_bytes") == boundary_service.MAX_PSQL_ARG_BYTES
              and st9h == 200 and body9h.get("world") == world_b,
              f"checkpoint (a, raw body over MAX_WRITE_BODY_BYTES, limit_bytes must name it): "
              f"status={st9a} body={body9a}; "
              f"checkpoint (b, raw={raw_len_b} bytes UNDER (a)'s bound, reserialized="
              f"{reserialized_len_b} bytes OVER (b)'s MAX_PSQL_ARG_BYTES="
              f"{boundary_service.MAX_PSQL_ARG_BYTES}, limit_bytes must name THAT bound, A8): "
              f"status={st9b} body={body9b}; "
              f"/health after both: status={st9h} world={body9h.get('world')} (server alive)",
              failures)

        # -- W13 (A3.2): parse-closure legs -- invalid UTF-8, an oversized integer literal, a
        # deeply nested body -- each a typed 422 naming the failed axis, server alive after
        # each (never a bare 500, never the wrong axis via a foreign RecursionError wearing the
        # infra shape -- see boundary_service.py's PsqlInfraFailure narrowing).
        def _post_raw(path: str, raw: bytes) -> tuple[int, dict]:
            req = urllib.request.Request(
                base + path, data=raw, headers={"Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    return resp.status, json.loads(resp.read())
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read())

        # Leg (a) encoding: invalid UTF-8 inside an otherwise JSON-shaped body.
        invalid_utf8_body = b'{"kind": "note", "statement": "bad utf8 \xff\xfe here", "actor": 1}'
        st13a, body13a = _post_raw("/write/ledger", invalid_utf8_body)

        # Leg (b) value magnitude: an integer literal past CPython's int-string conversion
        # guard (default 4300 digits) -- built as raw TEXT, never as a Python int object (
        # constructing the int itself would hit the identical guard on THIS side of the wire,
        # not exercise the server's).
        huge_digits = 4301
        huge_int_body = ('{"kind": "note", "actor": 1, "n": ' + ("9" * huge_digits) + '}').encode()
        st13b, body13b = _post_raw("/write/ledger", huge_int_body)

        # Leg (c) structure: deeply nested brackets -- overruns the recursive-descent JSON
        # parser's own stack budget (RecursionError, confirmed above the default recursion
        # limit of 1000 in the SAME venv this server runs under).
        deep_nest = 60000
        deep_nest_body = (b"[" * deep_nest) + (b"]" * deep_nest)
        st13c, body13c = _post_raw("/write/ledger", deep_nest_body)

        st13h, body13h = http_get(base + "/health") if up_b else (0, {})
        check("w13-parse-closure-legs-typed-422-server-alive",
              up_b
              and st13a == 422 and "encoding" in body13a.get("detail", "")
              and st13b == 422 and "value magnitude" in body13b.get("detail", "")
              and st13c == 422 and "structure" in body13c.get("detail", "")
              and st13h == 200 and body13h.get("world") == world_b,
              f"leg (a) invalid UTF-8: status={st13a} body={body13a}; "
              f"leg (b) oversized integer literal ({len(huge_int_body)}-byte body, "
              f"{huge_digits}-digit n): status={st13b} body={body13b}; "
              f"leg (c) deeply nested ({deep_nest} levels, {len(deep_nest_body)}-byte body): "
              f"status={st13c} body={body13c}; /health after all three: status={st13h} "
              f"world={body13h.get('world')} (server alive)",
              failures)

        # -- W15 (A4.1a): non-finite legs -- Infinity, NaN, 1e400 -- each a typed 422 on the
        # value axis, server alive after. Hand-built raw bytes (never json.dumps, which would
        # need a Python float('inf')/('nan') input and so would pre-filter client-side rather
        # than driving the SERVER's own classification): `json.loads` accepts all three
        # non-standard literals by default (confirmed above -- `1e400` silently parses to
        # `inf`, exceeding float's exponent range), the same lenience A4.1(a)'s
        # `allow_nan=False` re-serialization exists to close downstream of.
        infinity_body = b'{"kind": "note", "actor": 1, "statement": "W15 Infinity leg", "n": Infinity}'
        nan_body = b'{"kind": "note", "actor": 1, "statement": "W15 NaN leg", "n": NaN}'
        huge_exp_body = b'{"kind": "note", "actor": 1, "statement": "W15 1e400 leg", "n": 1e400}'
        st15a, body15a = _post_raw("/write/ledger", infinity_body)
        st15b, body15b = _post_raw("/write/ledger", nan_body)
        st15c, body15c = _post_raw("/write/ledger", huge_exp_body)
        st15h, body15h = http_get(base + "/health") if up_b else (0, {})
        check("w15-non-finite-legs-typed-422-value-axis-server-alive",
              up_b
              and st15a == 422 and "value axis" in body15a.get("detail", "")
              and st15b == 422 and "value axis" in body15b.get("detail", "")
              and st15c == 422 and "value axis" in body15c.get("detail", "")
              and st15h == 200 and body15h.get("world") == world_b,
              f"Infinity: status={st15a} body={body15a}; NaN: status={st15b} body={body15b}; "
              f"1e400 (overflows to inf): status={st15c} body={body15c}; /health after all "
              f"three: status={st15h} world={body15h.get('world')} (server alive)",
              failures)

        # -- W16 (A4.1b): representability legs -- a U+0000-bearing string, an unpaired UTF-16
        # surrogate -- each a typed 422 on the representability axis, server alive after. Both
        # crafted as raw JSON escape sequences in the request bytes (a NUL escape, a lone `\ud800` escape
        # with no low surrogate pairing it) -- `json.loads` accepts both by default (confirmed
        # above) and hands the server a real NUL character / a real lone-surrogate Python str
        # character, exactly what A4.1(b) exists to catch before jsonb ever sees it.
        nul_body = b'{"kind": "note", "actor": 1, "statement": "before\\u0000after"}'
        surrogate_body = b'{"kind": "note", "actor": 1, "statement": "before\\ud800after"}'
        st16a, body16a = _post_raw("/write/ledger", nul_body)
        st16b, body16b = _post_raw("/write/ledger", surrogate_body)
        st16h, body16h = http_get(base + "/health") if up_b else (0, {})
        check("w16-representability-legs-typed-422-server-alive",
              up_b
              and st16a == 422 and "representability axis" in body16a.get("detail", "")
              and st16b == 422 and "representability axis" in body16b.get("detail", "")
              and st16h == 200 and body16h.get("world") == world_b,
              f"NUL-bearing string: status={st16a} body={body16a}; unpaired surrogate: "
              f"status={st16b} body={body16b}; /health after both: status={st16h} "
              f"world={body16h.get('world')} (server alive)",
              failures)

        # -- W17 (A4.2): over-range id on the read side -- a path-param id past MAX_ID
        # (2**63 - 1) and an over-range after_id query param -- each a typed 422, never
        # reaching psql's bigint cast (which previously wore a 503 it did not earn).
        over_range_id = 2**63  # one past MAX_ID
        st17a, body17a = http_get(f"{base}/rows/{over_range_id}") if up_b else (0, {})
        st17b, body17b = http_get(f"{base}/rows/current?after_id={over_range_id}&limit=10") if up_b else (0, {})
        check("w17-over-range-id-read-side-typed-422",
              up_b
              and st17a == 422 and "row_id" in body17a.get("detail", "")
              and st17b == 422 and "after_id" in body17b.get("detail", ""),
              f"GET /rows/{{id}} with id={over_range_id} (MAX_ID+1): status={st17a} "
              f"body={body17a}; GET /rows/current?after_id={over_range_id}: status={st17b} "
              f"body={body17b}",
              failures)

        # -- W18a (A4.3), connection-refusal polarity: PsqlInfraFailure (typed 503
        # infra_failure) for a genuine psql exit 2. A FRESH server instance, pointed at world_b's
        # OWN deployment file but with PGPORT overridden to a closed local port (nothing
        # listens there), so every psql call this instance makes gets a fast ECONNREFUSED
        # (exit 2) -- distinct from W14's already-covered blackhole/stall leg (a TimeoutExpired,
        # also infra per A3.1, but not this specific exit-2 path A4.3 draws the line at).
        closed_port = free_closed_port()
        proc18a, port18a = start_server(dep_b, env_overrides={"PGPORT": str(closed_port)})
        asgi_up_18a = False
        deadline18a = time.time() + 10
        while time.time() < deadline18a:
            try:
                with socket.create_connection(("127.0.0.1", port18a), timeout=1):
                    asgi_up_18a = True
                    break
            except OSError:
                time.sleep(0.2)
        st18a, body18a = http_get(f"http://127.0.0.1:{port18a}/health") if asgi_up_18a else (0, {})
        out18a = stop_server(proc18a)
        check("w18a-exit2-connection-refusal-503-infra-failure",
              asgi_up_18a and st18a == 503 and body18a.get("disposition") == "infra_failure",
              f"ASGI socket accepting={asgi_up_18a}; GET /health against a server whose PGPORT "
              f"points at a closed local port ({closed_port}, nothing listening -- genuine "
              f"ECONNREFUSED, psql exit 2): status={st18a} body={body18a}; "
              f"server tail: {out18a[-300:] if not asgi_up_18a else '(n/a, came up)'}",
              failures)

        # -- W19 (A4.4): audit_served.py's exit-2 "transport/infrastructure failure" contract,
        # restored -- against an unreachable world (the SAME closed-port lever W18a uses,
        # applied to the audit tool's OWN direct-psql leg, not the service under audit). The
        # served-page fetch (--base-url) still targets world_b's live, healthy server, so ONLY
        # the audit's direct-read leg fails -- proving A4.4's fix (catching the dedicated
        # PsqlInfraFailure/PsqlUnclassifiedFailure exceptions instead of the stale bare
        # RuntimeError) restores the exit-2 contract rather than letting the failure escape as
        # an uncaught exception (a crash) or silently miscount as exit 0/1.
        env19 = dict(os.environ)
        env19["PGPORT"] = str(closed_port)
        audit19_cp = sh([str(PYVENV), str(SERVING / "audit_served.py"),
                        "--base-url", base, "--deployment", str(dep_b)], env=env19) if up_b else None
        check("w19-audit-served-exit2-contract-unreachable-world",
              up_b and audit19_cp is not None and audit19_cp.returncode == 2
              and "TRANSPORT FAILURE" in audit19_cp.stderr,
              f"audit_served.py --deployment pointed at an unreachable world (PGPORT="
              f"{closed_port}, closed -- direct-read leg only, served-fetch leg still targets "
              f"the live world_b server): exit={audit19_cp.returncode if audit19_cp else '?'} "
              f"stderr={(audit19_cp.stderr.strip() if audit19_cp else '?')!r}",
              failures)

        # -- W20 (A5.1): the representability-scan regression, both polarities. Leg (a): a
        # payload whose STRING VALUE is the literal six characters "a backslash, then u0000"
        # (documenting an escape in prose -- carrying NO real NUL codepoint) -- built via a
        # DOUBLE-backslash JSON escape on the wire, which `json.loads` resolves to ONE literal
        # backslash character followed by literal text "u0000" -- must now be ACCEPTED through
        # to the kernel (the pre-A5.1 scan false-refused this exact shape). Legs (b)/(c): a real
        # NUL and a real unpaired surrogate (the SAME true-positive bodies W16 already covers,
        # re-witnessed here under W20's own name per the spec's numbering) must STILL refuse on
        # the representability axis -- the fix closes the false positive without opening the
        # true positives back up.
        w20a_raw = (
            '{"kind": "note", "actor": ' + str(author_id) + ', '
            '"statement": "W20 leg a -- documents an escape sequence: before\\\\u0000after"}'
        ).encode()
        w20b_raw = (
            '{"kind": "note", "actor": ' + str(author_id) + ', '
            '"statement": "W20 leg b -- real NUL: before\\u0000after"}'
        ).encode()
        w20c_raw = (
            '{"kind": "note", "actor": ' + str(author_id) + ', '
            '"statement": "W20 leg c -- real unpaired surrogate: before\\ud800after"}'
        ).encode()
        st20a, body20a = _post_raw("/write/ledger", w20a_raw)
        st20b, body20b = _post_raw("/write/ledger", w20b_raw)
        st20c, body20c = _post_raw("/write/ledger", w20c_raw)
        st20h, body20h = http_get(base + "/health") if up_b else (0, {})
        check("w20-representability-scan-regression-fixed-both-polarities",
              up_b
              and st20a == 200 and body20a.get("disposition") == "accepted"
              and st20b == 422 and "representability axis" in body20b.get("detail", "")
              and st20c == 422 and "representability axis" in body20c.get("detail", "")
              and st20h == 200 and body20h.get("world") == world_b,
              f"leg (a) literal escape TEXT (double-backslash wire encoding, no real NUL): "
              f"status={st20a} verdict={body20a}; "
              f"leg (b) real NUL (single-backslash wire encoding): status={st20b} body={body20b}; "
              f"leg (c) real unpaired surrogate: status={st20c} body={body20c}; "
              f"/health after all three: status={st20h} world={body20h.get('world')} "
              f"(server alive)",
              failures)

        # -- W21 (A5.2): a write-payload integer field above bigint range -> typed 422 naming
        # the field and the bound, BEFORE it ever reaches psql's bigint cast (which previously
        # wore a 500 unclassified_failure it did not earn, per A5's own §8 note on the sibling
        # kernel defect this boundary fix stands beside without fixing).
        over_bigint = 2**63
        w21_raw = json.dumps({"kind": "note", "actor": over_bigint,
                              "statement": "W21 over-bigint actor field"}).encode()
        st21, body21 = _post_raw("/write/ledger", w21_raw)
        st21h, body21h = http_get(base + "/health") if up_b else (0, {})
        check("w21-write-payload-int-field-over-bigint-typed-422",
              up_b and st21 == 422 and "actor" in body21.get("detail", "")
              and str(boundary_service.MAX_ID) in body21.get("detail", "")
              and st21h == 200 and body21h.get("world") == world_b,
              f"POST /write/ledger with actor={over_bigint} (MAX_ID+1): status={st21} "
              f"body={body21}; /health after: status={st21h} world={body21h.get('world')} "
              f"(server alive)",
              failures)

        # -- W21 float legs (A6): A5.2's own residue -- the bound was denominated on the
        # Python TYPE (`isinstance(v, int)`), so a JSON number in float/exponent form skipped
        # the check entirely. Leg (a): an over-bound value spelled as a float/exponent literal
        # (`1e20`, well past MAX_ID) must be refused with the SAME typed 422 shape as the plain-
        # int leg above -- proving the fix is denominated on magnitude, not on `type(v) is int`.
        over_bigint_float = 1e20
        w21f_over_raw = json.dumps({"kind": "note", "actor": over_bigint_float,
                                    "statement": "W21 float over-bigint actor field"}).encode()
        st21fo, body21fo = _post_raw("/write/ledger", w21f_over_raw)
        st21foh, body21foh = http_get(base + "/health") if up_b else (0, {})
        check("w21-write-payload-int-field-over-bigint-float-form-typed-422",
              up_b and st21fo == 422 and "actor" in body21fo.get("detail", "")
              and str(boundary_service.MAX_ID) in body21fo.get("detail", "")
              and st21foh == 200 and body21foh.get("world") == world_b,
              f"POST /write/ledger with actor={over_bigint_float!r} (float form, well past "
              f"MAX_ID): status={st21fo} body={body21fo}; /health after: status={st21foh} "
              f"world={body21foh.get('world')} (server alive)",
              failures)

        # Leg (b): an IN-RANGE float-valued id (`5.0`) is deliberately NOT newly refused by
        # this bound -- A6's own words, "it passes to the kernel exactly as before". The
        # assertion is negative-and-precise: this is NOT the boundary's int-field-out-of-range
        # 422 shape (the new check did not trip), and the server stays alive after -- whatever
        # the kernel/psql layer itself does with a decimal-form bigint text cast is that layer's
        # own pre-existing business, not this boundary fix's to adjudicate.
        w21f_inrange_raw = json.dumps({"kind": "note", "actor": 5.0,
                                       "statement": "W21 float in-range actor field"}).encode()
        st21fi, body21fi = _post_raw("/write/ledger", w21f_inrange_raw)
        st21fih, body21fih = http_get(base + "/health") if up_b else (0, {})
        w21fi_is_boundary_oor_422 = (
            st21fi == 422 and "actor" in body21fi.get("detail", "")
            and str(boundary_service.MAX_ID) in body21fi.get("detail", ""))
        check("w21-write-payload-int-field-in-range-float-not-boundary-422",
              up_b and not w21fi_is_boundary_oor_422
              and st21fih == 200 and body21fih.get("world") == world_b,
              f"POST /write/ledger with actor=5.0 (in-range float, spec A6's own example): "
              f"status={st21fi} body={body21fi} (must NOT be the boundary's int-field-oor 422 "
              f"shape -- reaches the kernel/psql layer exactly as before); /health after: "
              f"status={st21fih} world={body21fih.get('world')} (server alive)",
              failures)

        # -- W22 (A5.3): the body-READ-phase time bound. A raw-socket client (see
        # `_post_trickled`'s own docstring for why urllib cannot drive this leg) sends real
        # request headers with a genuine Content-Length, then trickles ONE byte at a time,
        # slowly enough that the FULL declared body would take well over
        # BODY_READ_TIMEOUT_S=30s to arrive -- the server must respond with a typed 408 WITHIN
        # that bound plus a generous margin, never waiting for the trickle to finish (which it
        # never does; the client stops as soon as a response arrives).
        w22_declared_len = 40
        w22_total_wall_s = 40.0  # 40 one-byte sends, ~1s apart -- exceeds BODY_READ_TIMEOUT_S=30
        st22, body22, elapsed22 = _post_trickled(
            "127.0.0.1", port_b, "/write/ledger", w22_declared_len, w22_total_wall_s
        ) if up_b else (None, None, 0.0)
        st22h, body22h = http_get(base + "/health") if up_b else (0, {})
        margin22 = boundary_service.BODY_READ_TIMEOUT_S + 20
        check("w22-body-read-timeout-trickled-body-typed-408-within-bound-plus-margin",
              up_b and st22 == 408 and body22 is not None
              and body22.get("disposition") == "body_read_timeout"
              and body22.get("timeout_s") == boundary_service.BODY_READ_TIMEOUT_S
              and elapsed22 < margin22
              and st22h == 200 and body22h.get("world") == world_b,
              f"trickled body (declared Content-Length={w22_declared_len}, 1 byte/~1s -- would "
              f"take ~{w22_total_wall_s:.0f}s to complete, well past "
              f"BODY_READ_TIMEOUT_S={boundary_service.BODY_READ_TIMEOUT_S}s): status={st22} "
              f"body={body22} elapsed={elapsed22:.1f}s (bound: "
              f"{boundary_service.BODY_READ_TIMEOUT_S}s, margin={margin22}s); /health after: "
              f"status={st22h} world={body22h.get('world')} (server alive)",
              failures)

        # -- W23 (A5.4): pagination on /standing/principals and /work/items, both polarities.
        # `/standing/principals`: WORLD B already carries >=3 principals (author, write-boundary,
        # boundary-service) by this point, so `limit=1` genuinely tests enforcement (pre-A5 this
        # route ignored the param and always returned the whole view). `/work/items` carries NO
        # rows yet on WORLD B (no work_opened act in its birth sequence) -- two are opened here,
        # through the boundary, so `limit=1` has something real to truncate; this also exercises
        # the view's own id-less fallback ordering (ORDER BY slug via a synthetic row_number()
        # cursor, spec A5.4's own "fixer flags a view lacking an id-shaped key" clause).
        w23_slug_a, w23_slug_b = f"w23-item-a-{RUN_SUFFIX}", f"w23-item-b-{RUN_SUFFIX}"
        for slug in (w23_slug_a, w23_slug_b):
            v = http_post(base + "/write/ledger", {
                "kind": "work_opened", "statement": f"W23 fixture item {slug}",
                "actor": author_id, "work_slug": slug, "work_title": f"W23 fixture {slug}",
            })[1] if up_b else {}
            if v.get("disposition") != "accepted":
                raise RuntimeError(f"W23 fixture work_opened write refused: {v}")

        st23sp_honored, page23sp_honored = http_get(
            f"{base}/standing/principals?after_id=0&limit=1") if up_b else (0, [])
        st23sp_oor, body23sp_oor = http_get(
            f"{base}/standing/principals?after_id=0&limit=0") if up_b else (0, {})
        st23wi_honored, page23wi_honored = http_get(
            f"{base}/work/items?after_id=0&limit=1") if up_b else (0, [])
        st23wi_all, page23wi_all = http_get(
            f"{base}/work/items?after_id=0&limit=1000") if up_b else (0, [])
        st23wi_oor, body23wi_oor = http_get(
            f"{base}/work/items?after_id=-1&limit=10") if up_b else (0, {})
        check("w23-pagination-both-routes-both-polarities",
              up_b
              and st23sp_honored == 200 and isinstance(page23sp_honored, list)
              and len(page23sp_honored) == 1
              and st23sp_oor == 422
              and st23wi_honored == 200 and isinstance(page23wi_honored, list)
              and len(page23wi_honored) == 1
              and st23wi_all == 200 and isinstance(page23wi_all, list)
              and len(page23wi_all) >= 2
              and {r["slug"] for r in page23wi_all} >= {w23_slug_a, w23_slug_b}
              and st23wi_oor == 422,
              f"/standing/principals?limit=1: status={st23sp_honored} "
              f"n={len(page23sp_honored) if isinstance(page23sp_honored, list) else '?'} "
              f"(honored leg); /standing/principals?limit=0: status={st23sp_oor} "
              f"body={body23sp_oor} (out-of-range leg); "
              f"/work/items?limit=1: status={st23wi_honored} "
              f"n={len(page23wi_honored) if isinstance(page23wi_honored, list) else '?'} "
              f"(honored leg, id-less fallback ordering); "
              f"/work/items?limit=1000: status={st23wi_all} "
              f"slugs={sorted(r.get('slug') for r in page23wi_all) if isinstance(page23wi_all, list) else '?'} "
              f"(both fixture items present); "
              f"/work/items?after_id=-1: status={st23wi_oor} body={body23wi_oor} "
              f"(out-of-range leg)",
              failures)

        # -- W24 (A7): the representability scan's OWN traversal (_iter_strings) is recursive
        # and inherits none of A3.2's parse-time recursion-depth protection -- a well-formed
        # body nested deeply enough overflows AFTER parse, inside the scan, rather than inside
        # json.loads. Depth 3000 is chosen deliberately: confirmed above the pure-Python
        # recursion limit (default 1000, so _iter_strings overflows well before 3000) and
        # confirmed UNDER json.loads/json.dumps's own much higher C-accelerated threshold (both
        # survive 6000+ levels), so this body parses fine, passes the id-domain and non-finite
        # checks, and overflows ONLY the representability scan -- the exact adjacency A7 closes.
        # Also under MAX_WRITE_BODY_BYTES (a few KB), so no size checkpoint fires first.
        w24_depth = 3000
        w24_nested = ("[" * w24_depth) + ("]" * w24_depth)
        w24_body = (
            '{"kind": "note", "actor": 1, "statement": "W24 deep nest", "n": ' + w24_nested + "}"
        ).encode()
        st24, body24 = _post_raw("/write/ledger", w24_body)
        st24h, body24h = http_get(base + "/health") if up_b else (0, {})
        check("w24-post-parse-recursion-guard-typed-422-structure-axis-server-alive",
              up_b
              and st24 == 422 and "structure" in body24.get("detail", "")
              and st24h == 200 and body24h.get("world") == world_b,
              f"~{w24_depth}-level-nested, under-bound, otherwise-valid write body "
              f"({len(w24_body)} bytes): status={st24} body={body24}; /health after: "
              f"status={st24h} world={body24h.get('world')} (server alive); W13's own "
              f"deep-nesting leg (parse-time, {deep_nest} levels) stays green above",
              failures)

        # -- W25 (A8 item 1): the argv-wall legs. Pre-A8, checkpoint (b) was denominated at
        # 1 MiB against the TOTAL-argv ARG_MAX (2 MiB) -- but the re-serialized payload
        # travels as ONE psql `-v` argument, and Linux's PER-ARGUMENT wall is MAX_ARG_STRLEN
        # (32 pages = 131072 bytes). A payload between ~131 KiB and 1 MiB passed BOTH pre-A8
        # checkpoints and detonated in subprocess.run as an uncaught E2BIG OSError -> bare
        # text/plain 500 (the untyped shape the spec has banned since A2.4) -- so checkpoint
        # (b)'s stated bound was unreachable-honest (no payload over ~131 KiB could ever have
        # succeeded). Leg (a): a ~200 KiB payload -- under checkpoint (a)'s 1 MiB raw-body
        # bound, over A8's re-denominated MAX_PSQL_ARG_BYTES=100000 -- must refuse as a typed
        # 413 whose limit_bytes names the NEW bound and whose teach-text names the
        # per-argument transport wall (MAX_ARG_STRLEN). Leg (b): a ~90 KiB payload -- under
        # BOTH bounds -- must pass all the way through to the kernel and get a verdict, not a
        # 413 (proving the re-denominated bound is real headroom, not a wall painted on).
        w25_over_raw = json.dumps({
            "kind": "note", "actor": author_id,
            "statement": "W25 over-transport-bound leg " + ("x" * 200_000)}).encode()
        st25a, body25a = _post_raw("/write/ledger", w25_over_raw)
        w25_under_raw = json.dumps({
            "kind": "note", "actor": author_id,
            "statement": "W25 under-both-bounds leg " + ("x" * 90_000)}).encode()
        st25b, body25b = _post_raw("/write/ledger", w25_under_raw)
        st25h, body25h = http_get(base + "/health") if up_b else (0, {})
        check("w25-argv-wall-legs-typed-413-naming-transport-wall-and-under-bound-verdict",
              up_b
              and len(w25_over_raw) < boundary_service.MAX_WRITE_BODY_BYTES
              and len(w25_over_raw) > boundary_service.MAX_PSQL_ARG_BYTES
              and st25a == 413 and body25a.get("disposition") == "payload_too_large"
              and body25a.get("limit_bytes") == boundary_service.MAX_PSQL_ARG_BYTES
              and "MAX_ARG_STRLEN" in body25a.get("message", "")
              and len(w25_under_raw) < boundary_service.MAX_PSQL_ARG_BYTES
              and st25b == 200 and body25b.get("disposition") in ("accepted", "refused")
              and st25h == 200 and body25h.get("world") == world_b,
              f"leg (a) ~200 KiB payload ({len(w25_over_raw)} raw bytes -- under checkpoint "
              f"(a)'s {boundary_service.MAX_WRITE_BODY_BYTES}, over checkpoint (b)'s "
              f"{boundary_service.MAX_PSQL_ARG_BYTES}): status={st25a} body={body25a}; "
              f"leg (b) ~90 KiB payload ({len(w25_under_raw)} raw bytes, under both bounds -- "
              f"pre-A8 this size could NEVER succeed, E2BIG'd at the argv wall): "
              f"status={st25b} verdict disposition={body25b.get('disposition')} "
              f"row_id={body25b.get('row_id')}; /health after both: status={st25h} "
              f"world={body25h.get('world')} (server alive)",
              failures)

        # -- W26 (A8 item 2): non-finite label consistency. Pre-A8, `Infinity` under the
        # int-declared `actor` field tripped the id-domain comparison (`inf > MAX_ID` is
        # True) and wore the id-domain label ("must satisfy 0 <= actor <= ...; got inf"),
        # while `NaN` in the SAME field compared False everywhere, fell through, and wore
        # A4.1(a)'s value-axis label -- one condition, two labels, split by IEEE-754
        # comparison accident. A8: the int-field domain check tests finiteness FIRST and
        # routes every non-finite numeric to A4.1(a)'s value-axis message. All three
        # non-finite spellings under `actor` must now refuse as typed 422 on the VALUE axis
        # (same message family), and NONE may wear the id-domain shape (asserted by MAX_ID's
        # digits being absent from the detail -- the id-domain message always prints the
        # bound). W15 (non-finite under a NON-declared field) and W21 (finite out-of-range
        # under `actor` keeps the id-domain shape; in-range 5.0 passes) stay green above.
        w26_inf_raw = b'{"kind": "note", "actor": Infinity, "statement": "W26 Infinity under int-declared field"}'
        w26_neginf_raw = b'{"kind": "note", "actor": -Infinity, "statement": "W26 -Infinity under int-declared field"}'
        w26_nan_raw = b'{"kind": "note", "actor": NaN, "statement": "W26 NaN under int-declared field"}'
        st26a, body26a = _post_raw("/write/ledger", w26_inf_raw)
        st26b, body26b = _post_raw("/write/ledger", w26_neginf_raw)
        st26c, body26c = _post_raw("/write/ledger", w26_nan_raw)
        st26h, body26h = http_get(base + "/health") if up_b else (0, {})
        max_id_digits = str(boundary_service.MAX_ID)
        check("w26-non-finite-under-int-declared-field-value-axis-not-id-domain",
              up_b
              and st26a == 422 and "value axis" in body26a.get("detail", "")
              and max_id_digits not in body26a.get("detail", "")
              and st26b == 422 and "value axis" in body26b.get("detail", "")
              and max_id_digits not in body26b.get("detail", "")
              and st26c == 422 and "value axis" in body26c.get("detail", "")
              and max_id_digits not in body26c.get("detail", "")
              and st26h == 200 and body26h.get("world") == world_b,
              f"Infinity under actor: status={st26a} body={body26a}; "
              f"-Infinity under actor: status={st26b} body={body26b}; "
              f"NaN under actor: status={st26c} body={body26c} "
              f"(all three: value axis, id-domain bound {max_id_digits} absent from detail); "
              f"/health after all three: status={st26h} world={body26h.get('world')} "
              f"(server alive)",
              failures)

        # -- W9 streaming-abort leg: UNEXERCISED, named (spec A3.4's own carve-out, "exercised
        # if cheaply drivable, else UNEXERCISED with why"). Driving it needs a client that opens
        # the write connection, sends a Content-Length promise, then closes the socket mid-body
        # BEFORE finishing the declared byte count -- `urllib`/`http.client` (this fixture's
        # only HTTP client) offer no supported way to half-close a POST mid-stream (the library
        # always either sends the buffer it was given in full or raises before sending
        # anything); reaching for a raw `socket` client to hand-craft a truncated HTTP/1.1
        # request is possible but is exactly the kind of second, parallel transport layer this
        # fixture file otherwise avoids (it reuses `urllib` uniformly, W1-W13 above). Named here
        # rather than silently absent from the witness plan or faked with a shortcut that
        # doesn't actually abort mid-stream.
        print("=== w9-streaming-abort-leg ===")
        print("  [UNEXERCISED] no supported urllib/http.client path half-closes a POST body "
              "mid-stream; driving this leg needs a raw-socket client, which this fixture does "
              "not otherwise carry. Named per spec A3.4's own carve-out.")
        print()

        # -- §9/A2.1 closure (W12): the route table IS the enumeration -- asserted against
        # app.routes DIRECTLY (in-process), never the (now-disabled) OpenAPI schema.
        actual_routes = actual_route_table(dep_b)
        check("w12-route-table-is-the-enumeration-in-process",
              actual_routes == EXPECTED_ROUTES,
              f"app.routes == spec's fixed §3+§4 table: {actual_routes == EXPECTED_ROUTES}; "
              f"actual={sorted(actual_routes)}; meta-routes (docs/redoc/openapi) present: "
              f"{bool({p for _, p in actual_routes if 'doc' in p or 'openapi' in p})}",
              failures)

        # -- W18b (A4.3), script/data-level polarity: PsqlUnclassifiedFailure (typed 500
        # unclassified_failure) for a genuine psql exit 3. DELIBERATELY corrupts world_b by
        # dropping ledger_current (a forced boundary/deployment defect -- exactly what A4.3
        # says this path means: after A4.1/A4.2 close the value-closure and id-domain classes,
        # an ordinary caller-supplied request cannot reach exit 3 on its own). CASCADE is
        # required and harmless here: s41's principal_relations/principal_role_bindings/
        # principal_keys/principal_competences all depend on ledger_current, and this is the
        # LAST check in WORLD B's block -- run after every other check that depends on any of
        # them, immediately before this world is torn down entirely. Uses the same admin psql
        # connection `teardown()` already uses on this world.
        r18b = sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP VIEW {world_b}.ledger_current CASCADE;"])
        if r18b.returncode != 0:
            check("w18b-exit3-script-failure-500-unclassified-failure", False,
                  f"could not force the fixture (DROP VIEW {world_b}.ledger_current CASCADE "
                  f"failed): {r18b.stdout[-400:]} {r18b.stderr[-400:]}",
                  failures)
        else:
            st18b, body18b = http_get(base + "/rows/current?after_id=0&limit=10") if up_b else (0, {})
            check("w18b-exit3-script-failure-500-unclassified-failure",
                  up_b and st18b == 500 and body18b.get("disposition") == "unclassified_failure",
                  f"GET /rows/current against world_b with ledger_current DROPPED (forces a "
                  f"genuine psql exit 3 -- relation does not exist, under ON_ERROR_STOP=1): "
                  f"status={st18b} body={body18b}",
                  failures)

        out_b = stop_server(proc_b)
        if not up_b:
            print(f"  (WORLD B server tail on failure-to-come-up: {out_b[-1000:]})")

        # ============================= WORLD NOCAP (pre-s22/s40/s41) =============
        print(f"== scaffolding classic world {world_nocap} (chain ends {CHAIN_NOCAP[-1]}) ==")
        wnc = scaffold_classic(world_nocap, CHAIN_NOCAP)
        tmps.append(wnc.parent)
        dep_nc = write_scratch_deployment(wnc.parent, world_nocap)
        proc_nc, port_nc = start_server(dep_nc)
        procs.append(proc_nc)
        base_nc = f"http://127.0.0.1:{port_nc}"
        up_nc = wait_health(base_nc)

        # -- W10: /health on a pre-s40 chain -> 200, null service_principal, no 500.
        st_h_nc, body_h_nc = http_get(base_nc + "/health") if up_nc else (0, {})
        check("w10-health-pre-s40-chain-null-principal-no-500",
              up_nc and st_h_nc == 200 and body_h_nc.get("service_principal") is None
              and body_h_nc.get("capabilities", {}).get("s22_work") is False
              and body_h_nc.get("capabilities", {}).get("s41_identity") is False
              and body_h_nc.get("capabilities", {}).get("s43_boundary") is False,
              f"GET /health on WORLD NOCAP (chain ends {CHAIN_NOCAP[-1]}, no s40/s41/s43): "
              f"status={st_h_nc} body={body_h_nc}", failures)

        # -- W11 ABSENT legs: this world carries NEITHER s22 nor s41 -- both gates refuse.
        st_sp_nc, v_sp_nc = http_get(base_nc + "/standing/principals") if up_nc else (0, {})
        st_wi_nc, v_wi_nc = http_get(base_nc + "/work/items") if up_nc else (0, {})
        check("w11-absent-legs-s41-and-s22-refuse",
              up_nc and st_sp_nc == 409 and v_sp_nc.get("disposition") == "capability_absent"
              and v_sp_nc.get("capability") == "s41-identity"
              and st_wi_nc == 409 and v_wi_nc.get("disposition") == "capability_absent"
              and v_wi_nc.get("capability") == "s22-work",
              f"GET /standing/principals status={st_sp_nc} body={v_sp_nc}; "
              f"GET /work/items status={st_wi_nc} body={v_wi_nc}", failures)

        out_nc = stop_server(proc_nc)
        if not up_nc:
            print(f"  (WORLD NOCAP server tail on failure-to-come-up: {out_nc[-1000:]})")

    finally:
        for p in procs:
            if p.poll() is None:
                stop_server(p)
        for w in (world_pre, world_b, world_nocap):
            teardown(w)
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    # ============================= W7: bind guard, both legs (no DB) =============================
    tmp7 = Path(tempfile.mkdtemp(prefix="svcfxw7-"))
    try:
        fake_dep = tmp7 / "fake-deployment.json"
        deployment_record.write_deployment(
            fake_dep, deployment_record.DeploymentRecord(
                db="toy", host=PGHOST, schema="doesnotmatterw7", kern="doesnotmatterw7_kernel",
                role="doesnotmatterw7_rw"))
        port7 = free_port()
        r_refused = sh([str(PYVENV), "-m", "serving.boundary_service", "--deployment", str(fake_dep),
                       "--host", "8.8.8.8", "--port", str(port7)], cwd=str(REPO))
        check("w7-bind-guard-refusal-leg",
              r_refused.returncode == 2 and "REFUSED" in r_refused.stderr
              and "--i-understand-this-exposes-the-ledger" in r_refused.stderr,
              f"non-loopback host without the flag: exit={r_refused.returncode}, "
              f"stderr={r_refused.stderr.strip()[-400:]!r} -- refused BEFORE any socket bind "
              f"(construction-time, ADR-0002 rung 1)", failures)

        # WORLD PRE (a throwaway, born just for W7's allowed leg -- torn down immediately after;
        # only /health needs to answer, so a pre-s43 world is deliberately reused rather than a
        # second full s43 scaffold).
        w7world = f"svcfxw7ok{RUN_SUFFIX}"
        teardown(w7world)
        w7dir = scaffold_classic(w7world, CHAIN_PRE)
        tmps2 = [w7dir.parent]
        birth_pre_s43(w7world)
        dep7ok = write_scratch_deployment(w7dir.parent, w7world)
        port7b = free_port()
        proc7, _ = start_server(dep7ok, host="0.0.0.0", port=port7b, extra_flag=True)
        up7 = wait_health(f"http://127.0.0.1:{port7b}")
        out7 = stop_server(proc7)
        teardown(w7world)
        for t in tmps2:
            shutil.rmtree(t, ignore_errors=True)
        check("w7-bind-guard-allowed-leg",
              up7,
              f"0.0.0.0 WITH --i-understand-this-exposes-the-ledger: server came up and "
              f"answered /health over loopback (up={up7}); tail={out7[-300:] if not up7 else '(clean)'}",
              failures)
    finally:
        shutil.rmtree(tmp7, ignore_errors=True)

    # ============================= W14: the hang leg (no DB) =============================
    # A deployment pointed at UNROUTABLE_HOST -- the connection attempt is neither refused
    # (fast, ordinary) nor eventually ICMP-unreachable; it is simply never answered. No toy-db
    # world is scaffolded (or needed): the connection never reaches postgres auth.
    tmp14 = Path(tempfile.mkdtemp(prefix="svcfxw14-"))
    try:
        dep14 = tmp14 / "w14-deployment.json"
        deployment_record.write_deployment(
            dep14, deployment_record.DeploymentRecord(
                db="toy", host=UNROUTABLE_HOST, schema="doesnotmatterw14",
                kern="doesnotmatterw14_kernel", role="doesnotmatterw14_rw"))
        port14 = free_port()
        proc14 = subprocess.Popen(
            [str(PYVENV), "-m", "serving.boundary_service", "--deployment", str(dep14),
             "--host", "127.0.0.1", "--port", str(port14)],
            cwd=str(REPO), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        # The ASGI server itself binds instantly (it never touches postgres to do so) -- wait
        # for the bare TCP socket to accept, NOT for /health to answer (which is exactly the
        # call under timing below, and would hang for as long as the bound allows).
        asgi_up = False
        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                with socket.create_connection(("127.0.0.1", port14), timeout=1):
                    asgi_up = True
                    break
            except OSError:
                time.sleep(0.2)
        start14 = time.time()
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port14}/health", timeout=40) as resp:
                st14, body14 = resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            st14, body14 = e.code, json.loads(e.read())
        except (urllib.error.URLError, OSError) as e:
            st14, body14 = 0, {"client_side_error": str(e)}
        elapsed14 = time.time() - start14
        out14 = stop_server(proc14)
        # Margin over the bound: generous enough to absorb process/subprocess overhead, tight
        # enough that it could never be mistaken for the OS's own TCP connect timeout (Linux's
        # default SYN-retry schedule is roughly 60-130s on an unrouted destination -- an order
        # of magnitude past this margin).
        margin14 = boundary_service.PSQL_CONNECT_TIMEOUT_S + 25
        check("w14-hang-leg-typed-503-within-connect-timeout-plus-margin",
              asgi_up and st14 == 503 and body14.get("disposition") == "infra_failure"
              and elapsed14 < margin14,
              f"ASGI socket accepting={asgi_up}; GET /health against unroutable host "
              f"{UNROUTABLE_HOST}: status={st14} body={body14} elapsed={elapsed14:.1f}s "
              f"(bound: PSQL_CONNECT_TIMEOUT_S={boundary_service.PSQL_CONNECT_TIMEOUT_S}s, "
              f"margin={margin14}s -- an ordinary OS TCP connect timeout on an unrouted host "
              f"is 60-130s, well past this margin); server tail if not up: "
              f"{out14[-300:] if not asgi_up else '(n/a, came up)'}",
              failures)
    finally:
        shutil.rmtree(tmp14, ignore_errors=True)

    # ============================= W27: admission bound under a stalled burst (no DB) =========
    # A9: MAX_INFLIGHT_KERNEL_CALLS=24 bounds concurrent in-flight kernel calls; a burst beyond
    # it must answer typed 503 server_saturated PROMPTLY (never queue), /health must never wait
    # behind other requests' occupancy, and the server must drain to normal service once the
    # burst completes. Reuses W14's UNROUTABLE_HOST lever: every kernel call this burst makes
    # stalls for up to PSQL_CONNECT_TIMEOUT_S before it could ever resolve, so an ADMITTED
    # call's own latency is bounded exactly like W14's own -- the only new behavior under test
    # here is what happens to the calls that never get admitted at all.
    tmp27 = Path(tempfile.mkdtemp(prefix="svcfxw27-"))
    try:
        dep27 = tmp27 / "w27-deployment.json"
        deployment_record.write_deployment(
            dep27, deployment_record.DeploymentRecord(
                db="toy", host=UNROUTABLE_HOST, schema="doesnotmatterw27",
                kern="doesnotmatterw27_kernel", role="doesnotmatterw27_rw"))
        port27 = free_port()
        proc27 = subprocess.Popen(
            [str(PYVENV), "-m", "serving.boundary_service", "--deployment", str(dep27),
             "--host", "127.0.0.1", "--port", str(port27)],
            cwd=str(REPO), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        asgi_up27 = False
        deadline27 = time.time() + 10
        while time.time() < deadline27:
            try:
                with socket.create_connection(("127.0.0.1", port27), timeout=1):
                    asgi_up27 = True
                    break
            except OSError:
                time.sleep(0.2)
        base27 = f"http://127.0.0.1:{port27}"

        # > MAX_INFLIGHT_KERNEL_CALLS (24); matches anyio's own default threadpool size named in
        # A9's own trigger measurements, so this burst is provably not bottlenecked by ANY OTHER
        # concurrency limit before it ever reaches the semaphore under test.
        BURST_N = 40
        # "Promptly, not after a timeout" (A9's own W27 sentence): well under
        # PSQL_CONNECT_TIMEOUT_S=5s -- a saturated call is refused before subprocess.run is ever
        # invoked, so it should be near-instant; this margin is generous for scheduling jitter
        # under 40-thread contention while remaining an order of magnitude under the connect
        # bound admitted calls are subject to.
        PROMPT_BOUND_S = 2.0
        # /health's OWN bound: reuses W14's margin14 formula verbatim (PSQL_CONNECT_TIMEOUT_S +
        # 25 = 30s) -- W14 already proved this margin covers /health's own multi-probe sequence
        # (capability_manifest's several regclass checks plus service_principal_name) against
        # this exact UNROUTABLE_HOST lever with NO contention at all. Bounded admission can only
        # ever make an individual probe FASTER under contention (an immediate 503 reject instead
        # of a full connect-timeout stall), never slower -- so the unburstened W14 margin is a
        # valid, non-arbitrary bound to reuse here, and it is exactly what "never wait behind
        # other requests' occupancy" (A9) means made checkable.
        HEALTH_MARGIN_S = boundary_service.PSQL_CONNECT_TIMEOUT_S + 25

        results: list[tuple[int, int | None, dict | None, float]] = []
        results_lock = threading.Lock()

        def _burst_one(idx: int) -> None:
            t0 = time.time()
            try:
                req = urllib.request.Request(
                    f"{base27}/write/ledger",
                    data=json.dumps({"statement": f"w27-burst-{idx}"}).encode(),
                    headers={"Content-Type": "application/json"}, method="POST")
                try:
                    with urllib.request.urlopen(req, timeout=40) as resp:
                        status, body = resp.status, json.loads(resp.read())
                except urllib.error.HTTPError as e:
                    status, body = e.code, json.loads(e.read())
            except (urllib.error.URLError, OSError, ValueError) as e:
                status, body = None, {"client_side_error": str(e)}
            elapsed = time.time() - t0
            with results_lock:
                results.append((idx, status, body, elapsed))

        # /health fired from its OWN thread, concurrently with the burst, so its wall-clock is
        # measured DURING contention, not before or after it.
        health_result: list[tuple[int | None, dict | None, float]] = []

        def _health_during_burst() -> None:
            t0 = time.time()
            try:
                status, body = http_get(f"{base27}/health")
            except (urllib.error.URLError, OSError, ValueError) as e:
                status, body = None, {"client_side_error": str(e)}
            health_result.append((status, body, time.time() - t0))

        burst_threads = [threading.Thread(target=_burst_one, args=(i,)) for i in range(BURST_N)]
        health_thread = threading.Thread(target=_health_during_burst)
        for t in burst_threads:
            t.start()
        time.sleep(0.05)  # let the burst threads actually dispatch before /health races them
        health_thread.start()
        for t in burst_threads:
            t.join(timeout=60)
        health_thread.join(timeout=60)

        saturated = [r for r in results if r[1] == 503 and isinstance(r[2], dict)
                     and r[2].get("disposition") == "server_saturated"]
        prompt_saturated = [r for r in saturated if r[3] < PROMPT_BOUND_S]
        expected_excess = BURST_N - boundary_service.MAX_INFLIGHT_KERNEL_CALLS
        check("w27-saturation-typed-503-prompt",
              asgi_up27 and len(results) == BURST_N and len(saturated) >= expected_excess
              and len(prompt_saturated) == len(saturated)
              and all(r[2].get("inflight_limit") == boundary_service.MAX_INFLIGHT_KERNEL_CALLS for r in saturated)
              and all("retry" in (r[2].get("message") or "").lower() for r in saturated),
              f"asgi_up={asgi_up27}; burst_n={BURST_N}, responses={len(results)}, "
              f"saturated={len(saturated)} (expected >= {expected_excess}), all prompt"
              f"(<{PROMPT_BOUND_S}s)={len(prompt_saturated) == len(saturated)}; sample statuses="
              f"{sorted({r[1] for r in results})}; elapsed range="
              f"{min((r[3] for r in results), default=-1):.2f}s..{max((r[3] for r in results), default=-1):.2f}s",
              failures)

        health_status, health_body, health_elapsed = health_result[0] if health_result else (None, None, -1.0)
        check("w27-health-unstarved-during-burst",
              health_status is not None and health_elapsed < HEALTH_MARGIN_S,
              f"/health DURING the burst: status={health_status} elapsed={health_elapsed:.1f}s "
              f"(bound: {HEALTH_MARGIN_S}s -- must never wait behind other requests' occupancy, "
              f"A9) body={health_body}",
              failures)

        # Drain check: once the burst has fully completed and every semaphore slot it held is
        # released, a single FRESH write must behave exactly like an ordinary (non-saturated)
        # request against this same unroutable host -- typed infra_failure once its own connect
        # attempt exhausts PSQL_CONNECT_TIMEOUT_S, and specifically NOT server_saturated --
        # proving no slot leaked or stayed stuck held.
        t0drain = time.time()
        try:
            drain_status, drain_body = http_post(f"{base27}/write/ledger", {"statement": "w27-drain-check"})
        except (urllib.error.URLError, OSError, ValueError) as e:
            drain_status, drain_body = None, {"client_side_error": str(e)}
        drain_elapsed = time.time() - t0drain
        drain_margin = boundary_service.PSQL_CONNECT_TIMEOUT_S + 25
        check("w27-drains-after-burst",
              drain_status == 503 and isinstance(drain_body, dict)
              and drain_body.get("disposition") == "infra_failure" and drain_elapsed < drain_margin,
              f"post-burst POST /write/ledger: status={drain_status} body={drain_body} "
              f"elapsed={drain_elapsed:.1f}s (bound {drain_margin}s) -- must be the ORDINARY "
              f"infra_failure a single call against this unroutable host always wears (W14), "
              f"never server_saturated (every semaphore slot the burst held must have been "
              f"released)",
              failures)
        out27 = stop_server(proc27)
        if not asgi_up27:
            print(f"  (W27 server tail on failure-to-come-up: {out27[-1000:]})")
    finally:
        shutil.rmtree(tmp27, ignore_errors=True)

    # ============================= W8: panel-side, UNEXERCISED BY CONSTRUCTION =============
    print("=== w8-deprecation-mark-panel-side ===")
    print("  [UNEXERCISED] the marked legacy path lives in the autoharn-panel repository, which "
          "this build never touches (spec §6, §10.4 'panel-side is a separate session's item "
          "citing this spec'). No live check is possible from this repo; recorded here so the "
          "gap is named, not silently absent from the witness plan.")
    print()

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- boundary-service both-polarity proof (W1-W7, W9-W27 live; "
          "W8 and the W9 streaming-abort leg UNEXERCISED, named).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
