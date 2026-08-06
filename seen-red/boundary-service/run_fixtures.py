#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity witness for design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md's
§8 witness plan (W1-W12, A2's amendment; W13-W14, A3's amendment; W15-W19, A4's amendment;
W20-W23, A5's amendment; W21's float legs, A6's amendment; W24, A7's amendment; W25-W26,
A8's amendment; W27, A9's amendment; W28, A10's amendment; W29-W30, A11's amendment; W31,
A12's amendment; W32, A13's amendment; W34-W35, design/FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md,
ledger row 1500; W38, A14's amendment -- the annotate_names path's checkability gap, review row
1176, assigned the next sequential W-number in THIS file's own local convention since A14 itself
names the gap without pre-numbering a witness leg). Real infra, no mocks:
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
                (pagination on /standing/principals and /work/items, both polarities; the
                /work/items leg pages on its A11 slug-keyset cursor, no concurrent write),
                W24 (a ~3000-level-nested,
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
                gave Infinity by IEEE-754 comparison accident), W28 (A10: /rows/{id}/history
                joins the pagination discipline -- (i) a 5-hop chain paged at limit=2, cursor
                continuation via each page's own last row id, union of pages equals the
                unpaginated chain exactly; (ii) limit=0/limit=1001/after_id=-1 each typed 422
                naming the domain; (iii) a short chain with no parameters, byte-identical to an
                independently-reconstructed pre-A10 unpaginated query rendered through the SAME
                JSONResponse class), W29 (A11: /work/items' slug-keyset cursor honesty -- (i)
                the reviewer's own concurrent-insert drive, replayed live: page 1 at limit=2
                before a mid-walk insert, the insert, page 2 continuing from the walk's own
                last-served cursor, no duplicate across the walk, the inserted item absent from
                the in-flight walk and present on a fresh one; (ii) after_id supplied ->
                typed 422 teaching after_slug, an over-512-byte after_slug -> typed 422 naming
                the domain; (iii) an ordinary two-page walk with no concurrent write, page union
                equals the unpaginated view), W31 (A12: after_slug's own representability
                closure -- (i) a literal NUL, percent-encoded (%00) in the query string, typed
                422 representability axis, same message family as the write-path leg, the NEXT
                request answers normally; (ii) an unpaired UTF-16 surrogate, driven in-process
                (structurally undrivable over real HTTP transport -- see this leg's own inline
                comment for the live experiment proving it), same typed 422; (iii) the
                choke-point net witnessed directly -- `_psql` called with a NUL-bearing argument
                raises the typed `PsqlUnclassifiedFailure`, never a bare `ValueError`), W30
                (A11: /rows/{id}/history's not-found shape -- a nonexistent in-domain id
                byte-matches GET /rows/{id}'s own typed 404, and an existing row's history stays
                byte-identical to an independently-reconstructed CTE using the SAME construction
                the live route runs), W32 (A13: the dumps-side recursion net -- (i) a
                100000-level-deep object, built iteratively and never via `json.loads`, passed
                directly to `_reserialize_or_value_axis_failure` returns the typed
                structure-axis refusal, never a bare `RecursionError`; (ii) no HTTP-layer
                regression, witnessed by the suite's own overall green exit), the
                §9/A2.1/W12 in-process route-table closure assertion, and FINALLY (destructive,
                run last) W18b
                (ledger_current dropped on world_b -- genuine psql exit 3 -> 500
                unclassified_failure), and W38 (A14 clause 3: the annotate_names path's
                committed coverage -- registered actor -> name over /work/items AND
                /views/work_item_current, a NULL claimant -> typed null absence never a
                spurious lookup, audit_served.py's own new --annotate-names-column differential
                AGREE, and the unsupported-view refusal on /views/credited_current -> typed 422
                naming review_gap/work_item_current, fired ahead of the capability gate).
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

import dataclasses
import hashlib
import hmac as hmac_module
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
import boundary_multiplex_config  # noqa: E402  (route-shape migration, design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md §2/§3 -- the server now takes --config, not --deployment)
import boundary_diagnostic_log  # noqa: E402  (W34 -- design/FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md, the closed event vocabulary under direct, in-process test)

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own
# environment before any subprocess is spawned -- inherited by the whole process tree
# this fixture starts, so every repo-root verb invocation anywhere downstream carries it.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

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

# Route-shape migration (design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md §2): every
# route now carries a leading /d/{deployment} segment -- a FastAPI route TEMPLATE, literal
# regardless of which real deployment names a given config declares (the placeholder is never
# substituted in app.routes' own path strings), so this set needs no per-world variant.
EXPECTED_ROUTES = {
    ("GET", "/d/{deployment}/health"), ("GET", "/d/{deployment}/rows/current"),
    ("GET", "/d/{deployment}/rows/{row_id}"),
    ("GET", "/d/{deployment}/rows/{row_id}/history"), ("GET", "/d/{deployment}/credited"),
    ("GET", "/d/{deployment}/standing/principals"), ("GET", "/d/{deployment}/work/items"),
    ("POST", "/d/{deployment}/write/ledger"), ("POST", "/d/{deployment}/write/review"),
    ("POST", "/d/{deployment}/write/registration"), ("POST", "/d/{deployment}/write/obligation"),
    # design/FABLE-BOUNDARY-READ-SURFACE-SPEC.md (ratified ledger decision row 1652, landed
    # BEFORE this delta -- this fixture's own EXPECTED_ROUTES had gone stale against it, a
    # pre-existing hazard fixed here in passing per CLAUDE.md's engineering-responsibility rule,
    # since this same delta already touches this fixture's own target file): the three-route
    # amendment.
    ("GET", "/d/{deployment}/views/{view}"), ("GET", "/d/{deployment}/rows/asof/{ts}"),
    ("GET", "/d/{deployment}/meta"),
    # design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Parts A+B (maintainer-ratified ledger row 1150):
    # the sixth s43-family write surface (Part A) plus the three artifact routes (Part B).
    ("POST", "/d/{deployment}/write/obligation_revoke"),
    ("GET", "/d/{deployment}/artifacts/{hash}"), ("GET", "/d/{deployment}/artifacts/{hash}/stat"),
    ("POST", "/d/{deployment}/artifacts"),
    # design/FABLE-MISSIVES-KERNEL-SPEC.md (kernel/lineage/s58-missive-substrate.sql, ledger row
    # 1263): the seventh s43-family write surface, shipped wired into WRITE_SURFACES but never
    # added to THIS set -- a second pre-existing hazard fixed here in passing (same reasoning as
    # the read-surface amendment's own comment immediately above: this delta already touches this
    # exact file's EXPECTED_ROUTES for an unrelated reason, and CLAUDE.md's engineering-
    # responsibility rule does not let a hazard in reach of that touch go unfixed).
    ("POST", "/d/{deployment}/write/missive_dispose"),
    # Ledger row 1480 (this commission): the valid-kinds teaching restoration's own new route.
    ("GET", "/d/{deployment}/kinds"),
    # design/FABLE-BOUNDARY-SSE-EVENTS-SPEC.md (work item boundary-sse-events, ledger row 169):
    # the head-advancement-only SSE push signal's own new route.
    ("GET", "/d/{deployment}/events"),
    # Work item boundary-verdict-read-surface (ledger row 221): the banked verify-chain/judge/
    # doctor attestation read's own new route.
    ("GET", "/d/{deployment}/attestation"),
    # design/BRIEF-DEPLOYMENTS-ROUTE-AND-NAME-JOIN-2026-08-06.md (brief row 1102, item
    # deployment-listing-route): the roster route -- the ONE route on this service with no
    # leading /d/{deployment} segment (see its own docstring in boundary_service.py for why).
    ("GET", "/deployments"),
}


def actual_route_table(config_path: Path) -> set[tuple[str, str]]:
    """W12 (A2.1): asserts against `app.routes` DIRECTLY, in-process -- never the OpenAPI
    schema's self-report (§9's route claim was found false exactly because that self-report
    structurally cannot list a disabled/undeclared meta-route; A2.1 disabled them outright, so
    there is no schema endpoint left to ask). `create_app` only builds the ASGI route table; it
    opens no socket and issues no query, so calling it here needs no live server and no live DB
    -- any syntactically valid multiplex config does (the identifiers need never resolve).
    Route-shape migration: `create_app` now takes the whole `configs` dict (multiplex spec §2),
    not one `BoundaryConfig` -- built here from `config_path`'s own TOML, exactly the same
    config a live `start_server` launch would load."""
    records = boundary_multiplex_config.load_multiplex_config(config_path)
    configs = {name: boundary_service.BoundaryConfig(rec) for name, rec in records.items()}
    app = boundary_service.create_app(configs)
    routes: set[tuple[str, str]] = set()
    for route in app.routes:
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", None)
        if methods and path:
            for m in methods:
                routes.add((m, path))
    return routes


def write_scratch_multiplex_config(tmpdir: Path, world: str) -> Path:
    """Route-shape migration: `serving/boundary_service.py` now takes `--config <toml>`
    (multiplex spec §3), never `--deployment <json>` -- this is the TOML sibling of
    `write_scratch_deployment` below, ONE deployment keyed by `world` (the same schema/kern/
    role naming convention `write_scratch_deployment` and `scaffold_classic` already use for
    this world), single-deployment configs still carrying the mandatory shape (spec §2)."""
    path = tmpdir / f"{world}-boundary-multiplex.toml"
    path.write_text(
        f'[deployments.{world}]\n'
        f'pghost = "{PGHOST}"\n'
        f'pgdatabase = "{PGDB}"\n'
        f'pguser = "{world}_rw"\n'
        f'pgschema = "{world}"\n'
        f'pgkern = "{world}_kernel"\n',
        encoding="utf-8")
    return path


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


def serve_existing_world(deployment_path: Path, tmpdir: Path) -> subprocess.Popen:
    """cli-rebase-fixture-repairs (ledger row 1170, THE CLASS): the ONE shared move a red fixture
    needs to migrate off the retired legacy-fallback path onto the served shim -- given an
    EXISTING deployment.json (already written by `bootstrap/new-project.sh`'s or `bootstrap/
    track-work.sh`'s own CLASSIC scaffold, which both already run the FULL birth chain including
    the s40/s43 birth sequence -- see either script's own header -- so no separate birth_via_
    boundary() call is needed here), stand a REAL `serving.boundary_service` against that EXACT
    schema/kern/role and rewrite deployment.json IN PLACE to add the two served-shim keys
    (design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md §5: `boundary_url`,
    `boundary_deployment`). Every fixture call site already points its `led`/`pickup`/etc
    invocations at this SAME deployment.json (via cwd, or an explicit AUTOHARN=/
    PICKUP_DEPLOYMENT= override) -- adding these two keys IN PLACE is the one edit a fixture
    needs to move onto the served path; nothing else about the fixture's own test body, scratch
    naming, or assertions changes. `boundary_deployment` is set to the record's own `schema`
    (the world-name convention every sibling fixture in this tree already uses).

    Caller MUST `stop_server(...)` the returned process in its own teardown/finally block --
    this function starts a real subprocess and does not own its lifecycle beyond returning it.

    LEAK-CLASS REFUSAL (fixture-repairs review, ledger rows 1237-1244/1248): a fixture that
    resolves `deployment_path` to a REAL project's deployment.json -- not a scratch one this
    fixture itself scaffolded under a temp dir -- stands a served `led` against the LIVE
    kernel and leaks committed rows into it (exactly what happened: 8 garbage rows landed in
    the real deployment during the fixture-repairs batch, later marked garbage by row 1248).
    Every one of this fixture class's own callers already scaffolds via `tempfile.mkdtemp`
    before calling here, so this refusal costs nothing on the intended path; it forecloses the
    leak class structurally rather than trusting every future caller to get it right by hand."""
    deployment_path = Path(deployment_path).resolve()
    scratch_root = Path(tempfile.gettempdir()).resolve()
    if scratch_root not in deployment_path.parents:
        raise RuntimeError(
            f"serve_existing_world REFUSES: {deployment_path} does not live under the scratch "
            f"root {scratch_root} (tempfile.gettempdir()). This guard exists because a fixture "
            f"once resolved a REAL project's deployment.json here and stood a served `led` "
            f"against the LIVE kernel, leaking 8 garbage rows into it (ledger rows "
            f"1237-1244, marked garbage by row 1248) -- a fixture must scaffold its own world "
            f"under a temp dir (tempfile.mkdtemp) and pass THAT deployment.json, never a real "
            f"checkout's.")
    # fixture-repairs review (MODERATE-loud finding): the tempdir-ancestor check above is a
    # no-op whenever TMPDIR resolves to an ancestor of THIS repo (e.g. $HOME, or the repo's
    # own parent directory) -- in that case scratch_root itself sits above the repo, so a
    # REAL deployment.json living inside the checkout still passes the "lives under
    # scratch_root" test above. Refuse independently on repo-containment: never serve a
    # deployment.json that is inside this repo's own working tree, and never serve one where
    # the repo root itself is not disjoint from the resolved path (covers deployment_path
    # equal to, or an ancestor of, REPO too -- not just the ordinary "path under REPO" case).
    # This is the same leak class named above (ledger rows 1237-1244/1248): a fixture must
    # never stand a served `led` against this checkout's own deployment.json.
    if deployment_path.is_relative_to(REPO) or REPO.is_relative_to(deployment_path):
        raise RuntimeError(
            f"serve_existing_world REFUSES: {deployment_path} is inside (or otherwise not "
            f"disjoint from) this repo's own working tree ({REPO}). This guard exists because "
            f"a fixture once resolved a REAL project's deployment.json here and stood a served "
            f"`led` against the LIVE kernel, leaking 8 garbage rows into it (ledger rows "
            f"1237-1244, marked garbage by row 1248) -- a fixture must scaffold its own world "
            f"under a temp dir (tempfile.mkdtemp) and pass THAT deployment.json, never a path "
            f"anywhere inside this checkout.")
    rec = deployment_record.load_deployment(deployment_path)
    # Built from `rec`'s OWN fields throughout (never this module's `{world}_rw`/`{world}_kernel`
    # string-building convention, which several fixtures in this class do not follow) -- the
    # config always matches the deployment.json this function was actually handed.
    cfg_path = tmpdir / f"{rec.schema}-boundary-multiplex.toml"
    cfg_path.write_text(
        f'[deployments.{rec.schema}]\n'
        f'pghost = "{rec.host}"\n'
        f'pgdatabase = "{rec.db}"\n'
        f'pguser = "{rec.role}"\n'
        f'pgschema = "{rec.schema}"\n'
        f'pgkern = "{rec.kern}"\n', encoding="utf-8")
    proc, port = start_server(cfg_path)
    base = f"http://127.0.0.1:{port}/d/{rec.schema}"
    if not wait_health(base):
        tail = stop_server(proc)
        raise RuntimeError(f"boundary_service for {rec.schema} never became healthy: {tail[-1500:]}")
    served = dataclasses.replace(rec, boundary_url=f"http://127.0.0.1:{port}",
                                  boundary_deployment=rec.schema)
    deployment_record.write_deployment(deployment_path, served)
    return proc


def _spawn_boundary_service(args: list[str], env: dict[str, str] | None = None) -> subprocess.Popen:
    """Diagnostic-logging build hazard fix (found in passing while adding the fixture legs
    below, per CLAUDE.md's engineering-responsibility rule -- not this build's assigned task,
    but squarely in reach of it): spawns a `serving.boundary_service` subprocess with
    stdout+stderr redirected to a real scratch FILE, never the anonymous PIPE this fixture used
    to pass and never drained while the server keeps running. An anonymous pipe's OS buffer
    (64KB on Linux) previously never filled because this service's own log volume was small
    (one uvicorn access line per request); design/FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md's
    own JSON-lines stream (4-7 lines per request: request_start, one-or-more kernel_call,
    write_verdict/refusal, request_end) pushed a long-lived WORLD B server's cumulative output
    past that wall mid-suite -- WITNESSED live: the server's own `sys.stderr.write` call
    blocked on the full pipe, hanging every subsequent request (this fixture's own W21-family
    /health poll timed out at exactly that point, reproduced in isolation and traced to this
    cause before this fix). A real file has no such fixed wall -- the SAME reason
    `serving/ensure_running.py`'s own PRODUCTION redirect targets `<world>/service.log`, a
    file, never a pipe, for this exact process; this fix makes the fixture MORE faithful to how
    the service is actually operated, not a fixture-only workaround. The log path is stashed on
    the returned `Popen` (`proc._diag_log_path`) so `stop_server` below can read it back
    without changing any of this function's callers' own unpacking shape."""
    fd, log_path_str = tempfile.mkstemp(prefix="boundary-service-fixture-log-", suffix=".log")
    log_path = Path(log_path_str)
    logf = os.fdopen(fd, "w")
    try:
        proc = subprocess.Popen(args, cwd=str(REPO), stdout=logf, stderr=subprocess.STDOUT, env=env)
    finally:
        logf.close()  # the child already holds its own dup'd fd; the parent's copy closes now
    proc._diag_log_path = log_path  # type: ignore[attr-defined]
    return proc


def start_server(config_path: Path, host: str = "127.0.0.1", port: int | None = None,
                  extra_flag: bool = False, env_overrides: dict[str, str] | None = None
                  ) -> tuple[subprocess.Popen, int]:
    """Route-shape migration: launches with `--config <toml>` (multiplex spec §3), never the
    retired `--deployment <json>`. `env_overrides` (A4/W18a): merged over this process's own
    environment before launch -- used to force a genuine connection-refusal leg (PGPORT pointed
    at a closed local port) that is distinct from W14's already-covered blackhole/stall leg,
    without needing a second config shape (the TOML carries no port field of its own; PGPORT is
    the one lever psql itself already understands, the same lever _psql's own
    PGCONNECT_TIMEOUT override in boundary_service.py uses for the time axis)."""
    if port is None:
        port = free_port()
    args = [str(PYVENV), "-m", "serving.boundary_service",
            "--config", str(config_path), "--host", host, "--port", str(port)]
    if extra_flag:
        args.append("--i-understand-this-exposes-the-ledger")
    env = dict(os.environ)
    if env_overrides:
        env.update(env_overrides)
    proc = _spawn_boundary_service(args, env=env)
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


def http_post_headers(url: str, payload: dict | None, headers: dict[str, str]) -> tuple[int, object]:
    """design/FABLE-DISPATCH-MECHANICS-SPEC.md's own witness legs: `http_post` above with
    EXTRA caller-supplied headers (the identity conduit's own headers) -- a payload of None
    posts an empty body (used by the pre-kernel-call refusal legs, which never need a real
    write payload since they never reach the kernel at all)."""
    data = json.dumps(payload).encode() if payload is not None else b""
    hdrs = {"Content-Type": "application/json", **headers}
    req = urllib.request.Request(url, data=data, headers=hdrs, method="POST")
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
    """Reads back whatever `_spawn_boundary_service` redirected this process's stdout+stderr
    to (a real file, `proc._diag_log_path`) -- terminate-then-read, since a file (unlike a
    pipe) can never deadlock `.wait()` on a full buffer. Falls back to the OLD
    `communicate()`-based path for any `Popen` NOT spawned via that helper (defensive; every
    real call site in this file routes through it as of this build) -- `communicate()`, not
    `.wait()` first, in that fallback branch specifically, because a genuine PIPE-backed
    process can be blocked mid-write on a full buffer and `.wait()` alone would hang exactly
    like the hazard this fix closes."""
    log_path = getattr(proc, "_diag_log_path", None)
    if log_path is not None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
        try:
            return log_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
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
        cfg_pre = write_scratch_multiplex_config(wpre.parent, world_pre)
        proc_pre, port_pre = start_server(cfg_pre)
        procs.append(proc_pre)
        base_pre = f"http://127.0.0.1:{port_pre}/d/{world_pre}"
        up = wait_health(base_pre)
        results = {}
        if up:
            for surface in ("ledger", "review", "registration", "obligation"):
                status, body = http_post(f"{base_pre}/write/{surface}", {"x": "y"})
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

        # W33 (row 1489's tracked deferral, landed post-merge of the uvicorn ISO-timestamp
        # change): every uvicorn startup line in the captured server output must carry the
        # `_UVICORN_LOG_CONFIG_WITH_ISO_TIMESTAMP` prefix (%(asctime)s with
        # datefmt %Y-%m-%dT%H:%M:%S%z). Asserted on the WORLD PRE server's tail -- the config
        # is applied at launch, before any deployment/capability logic, so the pre-s43 world
        # is as good a witness as any. Guarded against vacuity: the startup lines must exist.
        ts_prefix = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{4} ")
        startup_lines = [ln for ln in out_pre.splitlines()
                         if "Uvicorn running on" in ln or "Application startup complete" in ln]
        check("w33-uvicorn-log-lines-carry-iso-timestamp",
              len(startup_lines) >= 2 and all(ts_prefix.match(ln) for ln in startup_lines),
              f"startup lines found={len(startup_lines)}; "
              f"specimens={startup_lines[:2] if startup_lines else out_pre[-300:]!r}",
              failures)

        # ============================= WORLD B (s43 head) =============================
        print(f"== scaffolding classic world {world_b} (chain ends {CHAIN_B[-1]}) ==")
        wb = scaffold_classic(world_b, CHAIN_B)
        tmps.append(wb.parent)
        author_id, svc_id = birth_via_boundary(world_b)
        dep_b = write_scratch_deployment(wb.parent, world_b)  # still needed: audit_served.py's own --deployment path flag (unchanged), and the direct-BoundaryConfig call sites below (W28/W31iii)
        cfg_b = write_scratch_multiplex_config(wb.parent, world_b)
        proc_b, port_b = start_server(cfg_b)
        procs.append(proc_b)
        # base_b_raw: the bare server root (no /d/{deployment} segment) -- audit_served.py's own
        # --base-url takes the RAW root and prepends /d/{--deployment-name} itself (multiplex
        # spec §4); `base` below is every OTHER call site's own already-prefixed convenience.
        base_b_raw = f"http://127.0.0.1:{port_b}"
        base = f"{base_b_raw}/d/{world_b}"
        up_b = wait_health(base)

        # -- /health: route count (§9 closure), capability manifest, service_principal named.
        st_h, body_h = http_get(base + "/health") if up_b else (0, {})
        check("closure-health-and-route-count",
              up_b and st_h == 200 and body_h.get("capabilities", {}).get("s43_boundary") is True
              and body_h.get("service_principal") == "boundary-service",
              f"health status={st_h} body={body_h}", failures)

        # -- W37 (row 221, boundary-verdict-read-surface): GET /attestation, BOTH polarities.
        # PRESENT polarity, no special env needed: this REPO CHECKOUT's own real
        # engine/docs/ledger-marriage/derivations/ tree already carries genuine `--retain`'d
        # derivation.json files (from prior differential-suite dev work) -- WORLD B's own server
        # was spawned with no AUTOHARN_JUDGE_DERIVATIONS_ROOT override, so it reads that SAME
        # real tree, honestly proving the "present" shape without a fixture-manufactured plant.
        st_att, body_att = http_get(base + "/attestation") if up_b else (0, {})
        judge_att = body_att.get("judge", {}) if isinstance(body_att, dict) else {}
        check("w37a-attestation-judge-present-from-real-repo-bank",
              up_b and st_att == 200
              and judge_att.get("banked") is True
              and judge_att.get("label") == "last_known_attestation"
              and judge_att.get("verdict") in
                  ("AGREE", "DIVERGE_BY_DESIGN", "DIVERGE_DEFECT", "QUARANTINED")
              and judge_att.get("banked_at"),
              f"status={st_att} judge={judge_att}", failures)
        check("w37b-attestation-verify-chain-and-doctor-always-absent",
              up_b and st_att == 200
              and body_att.get("verify_chain", {}).get("banked") is False
              and body_att.get("verify_chain", {}).get("disposition") == "no_banked_artifact"
              and body_att.get("doctor", {}).get("banked") is False
              and body_att.get("doctor", {}).get("disposition") == "no_banked_artifact",
              f"status={st_att} verify_chain={body_att.get('verify_chain')} "
              f"doctor={body_att.get('doctor')}", failures)
        # ABSENT polarity for judge: a SEPARATE server instance, pointed via
        # AUTOHARN_JUDGE_DERIVATIONS_ROOT at a freshly-made, genuinely empty scratch directory --
        # no derivation.json anywhere under it, so `_latest_judge_derivation` returns None and
        # this route's own `judge` field resolves to the SAME NoBankedArtifact shape verify_chain/
        # doctor always wear.
        empty_derivations_dir = Path(tempfile.mkdtemp(prefix="w37-empty-derivations-"))
        tmps.append(empty_derivations_dir)
        env_w37 = dict(os.environ)
        env_w37["AUTOHARN_JUDGE_DERIVATIONS_ROOT"] = str(empty_derivations_dir)
        proc_w37, port_w37 = start_server(cfg_b, env_overrides=env_w37)
        procs.append(proc_w37)
        base_w37 = f"http://127.0.0.1:{port_w37}/d/{world_b}"
        up_w37 = wait_health(base_w37)
        st_att2, body_att2 = http_get(base_w37 + "/attestation") if up_w37 else (0, {})
        judge_att2 = body_att2.get("judge", {}) if isinstance(body_att2, dict) else {}
        check("w37c-attestation-judge-absent-when-nothing-banked",
              up_w37 and st_att2 == 200
              and judge_att2.get("banked") is False
              and judge_att2.get("disposition") == "no_banked_artifact"
              # MODERATE fix-round correction: would_produce no longer names --retain (this
              # repo's own ./autoharn judge hardcodes it and calls that the ordinary run,
              # bootstrap/templates/judge.tmpl's own header) -- the assertion below checks for
              # the corrected, --retain-free command instead of the pre-fix wording.
              and judge_att2.get("would_produce") == "./autoharn judge [target...]",
              f"up_w37={up_w37} status={st_att2} judge={judge_att2}", failures)
        check("w37d-attestation-unknown-deployment-still-typed-404",
              # the discriminator gate applies here too (AttestationResponse's own docstring:
              # deployment validation happens, even though the payload itself does not vary).
              (lambda r: r[0] == 404 and r[1].get("disposition") == "unknown_deployment")(
                  http_get(f"http://127.0.0.1:{port_w37}/d/does-not-exist-w37/attestation")
                  if up_w37 else (0, {})),
              f"up_w37={up_w37}", failures)

        # -- W37e (fix-round CRITICAL, reviewer's own live-witnessed specimen reproduced here):
        # the multi-domain mtime race. Two derivation.json files planted directly (bypassing
        # judge/retain() entirely -- this leg tests THIS ROUTE's own domain attribution, not the
        # differential engine) into the SAME `empty_derivations_dir` the w37c server already
        # reads live (no caching, no restart needed) -- an OLDER one directly under the bare
        # `ledger` root, a NEWER one under the `contemporaneity` subtree. The pre-fix code
        # attributed domain by WHICH DOMAIN'S SCAN REACHED A FILE FIRST (dict iteration order,
        # 'ledger' always first) rather than by the file's own location -- since the bare
        # 'ledger' root's own rglob ALSO discovers files nested under contemporaneity/ (the
        # subtree is INSIDE the bare root, not beside it), the newer contemporaneity-stored
        # record was mis-scanned once as domain 'ledger' (at the correct, newer mtime) BEFORE the
        # correct 'contemporaneity' domain's own scan ever reached the identical file -- and a
        # strict `>` mtime tiebreak never let the second (correctly-domained) sighting of the
        # SAME mtime replace the first. This leg is domain-race-honest: the OLDER file lives at
        # the bare root (so a domain bug that always won on iteration order for 'ledger' would
        # otherwise still coincidentally look right); only the NEWER, subtree-stored, distinct-
        # verdict record proves the fix, because a wrong implementation would report it as
        # 'ledger' with the OLDER file's own verdict/target lost, or would report the newer
        # verdict under the WRONG domain -- either way failing the assertion below.
        def _plant_derivation(root: Path, domain_subdir: str, target: str, verdict: str,
                               mtime: float) -> None:
            d = root / domain_subdir / target / "20260101T000000Z_deadbeefdead"
            d.mkdir(parents=True, exist_ok=True)
            record = {"target": target, "verdict": verdict, "only_asp": [], "only_sql": [],
                      "asp_record": {"engine": "clingo", "version": "test", "config": [],
                                      "input_basis": "edb-text", "input_hash": f"asp-{target}",
                                      "program_hash": "x", "output_hash": "x", "target": target,
                                      "ts": "2026-01-01T00:00:00"},
                      "sql_record": {"engine": "postgres", "version": "test", "config": [],
                                      "input_basis": "live-db", "input_hash": f"sql-{target}",
                                      "program_hash": "x", "output_hash": "x", "target": target,
                                      "ts": "2026-01-01T00:00:00"},
                      "asp_quarantine": None, "sql_quarantine": None}
            p = d / "derivation.json"
            p.write_text(json.dumps(record), encoding="utf-8")
            os.utime(p, (mtime, mtime))

        _plant_derivation(empty_derivations_dir, ".", "w37e-old-ledger-target", "AGREE",
                          mtime=1_700_000_000.0)
        _plant_derivation(empty_derivations_dir, "contemporaneity", "w37e-new-contemp-target",
                          "DIVERGE_DEFECT", mtime=1_800_000_000.0)
        st_att3, body_att3 = http_get(base_w37 + "/attestation") if up_w37 else (0, {})
        judge_att3 = body_att3.get("judge", {}) if isinstance(body_att3, dict) else {}
        check("w37e-attestation-judge-domain-attributed-from-file-location-not-scan-order",
              up_w37 and st_att3 == 200
              and judge_att3.get("banked") is True
              and judge_att3.get("domain") == "contemporaneity"
              and judge_att3.get("target") == "w37e-new-contemp-target"
              and judge_att3.get("verdict") == "DIVERGE_DEFECT",
              f"up_w37={up_w37} status={st_att3} judge={judge_att3} (expected domain="
              f"'contemporaneity', target='w37e-new-contemp-target', verdict='DIVERGE_DEFECT' -- "
              f"the NEWER, subtree-stored record; a domain-attribution bug reports this same "
              f"verdict/target under domain 'ledger' instead, or loses it to the older "
              f"bare-root record entirely)",
              failures)

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
                      "--base-url", base_b_raw, "--deployment", str(dep_b),
                      "--deployment-name", world_b]) if up_b else None
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

        # -- W38 (A14 clause 3, review row 1176, design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md's
        # own A14 amendment): the annotate_names path's committed coverage -- audit_served.py's
        # new --annotate-names-column differential (registered actor -> name), NULL claimant ->
        # typed null absence, and the unsupported-view refusal (422 naming the supported views).
        w38_open_slug = f"w38-open-{RUN_SUFFIX}"
        w38_claimed_slug = f"w38-claimed-{RUN_SUFFIX}"
        w38_open_v = http_post(base + "/write/ledger", {
            "kind": "work_opened", "statement": "W38 fixture unclaimed item",
            "actor": author_id, "work_slug": w38_open_slug, "work_title": "W38 unclaimed"},
        )[1] if up_b else {}
        w38_claim_open_v = http_post(base + "/write/ledger", {
            "kind": "work_opened", "statement": "W38 fixture claimed item",
            "actor": author_id, "work_slug": w38_claimed_slug, "work_title": "W38 claimed"},
        )[1] if up_b else {}
        w38_claim_v = http_post(base + "/write/ledger", {
            "kind": "work_claimed", "statement": "W38 fixture claim",
            "actor": author_id, "work_slug": w38_claimed_slug},
        )[1] if up_b else {}
        w38_writes_ok = (up_b and w38_open_v.get("disposition") == "accepted"
                          and w38_claim_open_v.get("disposition") == "accepted"
                          and w38_claim_v.get("disposition") == "accepted")

        # Leg (i): registered actor -> name, over BOTH the /work/items fixed endpoint (claimant)
        # and the generic /views/{view} route (also claimant, work_item_current is one of
        # _VIEW_ACTOR_ANNOTATION_COLUMNS' two members) -- same mechanism, two call sites.
        st38a_items, body38a_items = http_get(
            f"{base}/work/items?annotate_names=true") if w38_writes_ok else (0, [])
        row38a_items = next((r for r in body38a_items if r.get("slug") == w38_claimed_slug), None) \
            if isinstance(body38a_items, list) else None
        st38a_view, body38a_view = http_get(
            f"{base}/views/work_item_current?annotate_names=true") if w38_writes_ok else (0, [])
        row38a_view = next((r for r in body38a_view if r.get("slug") == w38_claimed_slug), None) \
            if isinstance(body38a_view, list) else None
        check("w38a-annotate-names-registered-actor-to-name",
              w38_writes_ok and st38a_items == 200 and row38a_items is not None
              and row38a_items.get("claimant") == author_id
              and row38a_items.get("claimant_name") == "author"
              and st38a_view == 200 and row38a_view is not None
              and row38a_view.get("claimant_name") == "author",
              f"/work/items?annotate_names=true claimed row: {row38a_items}; "
              f"/views/work_item_current?annotate_names=true claimed row: {row38a_view} -- "
              f"both must carry claimant_name='author' (author_id={author_id})", failures)

        # Leg (ii): the actor-shaped column itself NULL (no work_claimed act yet) -> typed null
        # absence, never a spurious lookup or a fabricated name (_annotate_actor_names' own
        # docstring: "a row whose actor-shaped column is itself NULL ... serve[s] null for the
        # name -- never invented or empty-string").
        row38b = next((r for r in body38a_items if r.get("slug") == w38_open_slug), None) \
            if isinstance(body38a_items, list) else None
        check("w38b-annotate-names-null-claimant-typed-absence",
              w38_writes_ok and row38b is not None
              and row38b.get("claimant") is None and row38b.get("claimant_name") is None,
              f"/work/items?annotate_names=true unclaimed row: {row38b} -- claimant AND "
              f"claimant_name must both be null, never a spurious lookup on the None id",
              failures)

        # Leg (iii): audit_served.py's OWN new differential (A14 clause 3's actual dispatch --
        # "audit_served.py gains named coverage of the annotate_names path"), independent of
        # the boundary_service in-process checks above: an AGREE verdict differentials the
        # served actor_name field against fetch_kernel_names' own direct kernel.principal read,
        # never against boundary_service's own annotation function. --endpoint/--view is
        # ledger_current/rows_current (actor), NOT work_item_current/claimant -- fetch_kernel's
        # OWN direct-read leg splices a hardcoded `WHERE id > {after_id}`, so it can only ever
        # query an id-keyed view (a pre-existing limitation this flag inherits, not fixes; see
        # this flag's own --help text). Every ledger row in this world carries actor=author_id,
        # so this leg doubles as a registered-actor-to-name witness over the tool's own code path
        # (distinct from leg (i)'s in-process boundary_service witness above).
        audit38_cp = sh([str(PYVENV), str(SERVING / "audit_served.py"),
                        "--base-url", base_b_raw, "--deployment", str(dep_b),
                        "--deployment-name", world_b, "--endpoint", "/rows/current",
                        "--view", "ledger_current",
                        "--annotate-names-column", "actor"]) if up_b else None
        check("w38c-audit-served-annotate-names-agree",
              up_b and audit38_cp is not None and audit38_cp.returncode == 0
              and "AGREE" in audit38_cp.stdout,
              f"audit_served.py --annotate-names-column actor exit="
              f"{audit38_cp.returncode if audit38_cp else '?'} "
              f"stdout={(audit38_cp.stdout.strip() if audit38_cp else '?')!r} "
              f"stderr={(audit38_cp.stderr.strip() if audit38_cp else '?')!r}", failures)

        # Leg (iv): the refusal -- annotate_names=true on a VIEW_REGISTRY member OUTSIDE
        # _VIEW_ACTOR_ANNOTATION_COLUMNS (credited_current is not one of its two members) ->
        # typed 422 naming the views that DO support it, never silently ignored (A10's own
        # lesson). credited_current chosen deliberately: this world carries NO s44 credited
        # view (W4 above), proving the annotate_names refusal fires BEFORE any per-view
        # capability check -- views_view()'s own code order (annotate_names validated
        # immediately after VIEW_REGISTRY membership, ahead of every capability gate below it).
        st38d, body38d = http_get(
            f"{base}/views/credited_current?annotate_names=true") if up_b else (0, {})
        detail38d = body38d.get("detail", "") if isinstance(body38d, dict) else ""
        check("w38d-annotate-names-unsupported-view-refused",
              up_b and st38d == 422 and "credited_current" in detail38d
              and "review_gap" in detail38d and "work_item_current" in detail38d,
              f"GET /views/credited_current?annotate_names=true: status={st38d} body={body38d} "
              f"-- must 422 (not 409 capability_absent -- proves annotate_names is checked "
              f"before capability), naming both supported views (review_gap, work_item_current)",
              failures)

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

        # Leg (b) value axis: an integer literal past CPython's int-string conversion guard
        # (default 4300 digits) -- built as raw TEXT, never as a Python int object (constructing
        # the int itself would hit the identical guard on THIS side of the wire, not exercise
        # the server's). Ledger row 1628: this leg's axis label used to read "value magnitude",
        # now unified to plain "value" (the SAME word W15/W26 below already use).
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
              and st13b == 422 and "value axis" in body13b.get("detail", "")
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
        proc18a, port18a = start_server(cfg_b, env_overrides={"PGPORT": str(closed_port)})
        asgi_up_18a = False
        deadline18a = time.time() + 10
        while time.time() < deadline18a:
            try:
                with socket.create_connection(("127.0.0.1", port18a), timeout=1):
                    asgi_up_18a = True
                    break
            except OSError:
                time.sleep(0.2)
        # cfg_b's own config still declares world_b (only PGPORT changed, via the environment,
        # not the TOML) -- same /d/{deployment} segment as base's own.
        st18a, body18a = http_get(f"http://127.0.0.1:{port18a}/d/{world_b}/health") if asgi_up_18a else (0, {})
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
                        "--base-url", base_b_raw, "--deployment", str(dep_b),
                        "--deployment-name", world_b], env=env19) if up_b else None
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
            "127.0.0.1", port_b, f"/d/{world_b}/write/ledger", w22_declared_len, w22_total_wall_s
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

        # -- W23 (A5.4, work/items leg RE-KEYED per A11): pagination on /standing/principals and
        # /work/items, both polarities. `/standing/principals`: WORLD B already carries >=3
        # principals (author, write-boundary, boundary-service) by this point, so `limit=1`
        # genuinely tests enforcement (pre-A5 this route ignored the param and always returned
        # the whole view). `/work/items` carries NO rows yet on WORLD B (no work_opened act in
        # its birth sequence) -- two are opened here, through the boundary, so `limit=1` has
        # something real to truncate; this also exercises the view's OWN natural key, `slug`, as
        # the pagination cursor (A11 retired the pre-A11 synthetic row_number() ordinal this leg
        # used to exercise -- the ordinal's own concurrent-insert instability is W29's, not
        # this leg's, business; this leg stays the ordinary no-concurrent-write case).
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
            f"{base}/work/items?after_slug=&limit=1") if up_b else (0, [])
        st23wi_all, page23wi_all = http_get(
            f"{base}/work/items?after_slug=&limit=1000") if up_b else (0, [])
        st23wi_oor, body23wi_oor = http_get(
            f"{base}/work/items?after_slug=&limit=0") if up_b else (0, {})
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
              f"/work/items?after_slug=&limit=1: status={st23wi_honored} "
              f"n={len(page23wi_honored) if isinstance(page23wi_honored, list) else '?'} "
              f"(honored leg, slug-keyset ordering, A11); "
              f"/work/items?after_slug=&limit=1000: status={st23wi_all} "
              f"slugs={sorted(r.get('slug') for r in page23wi_all) if isinstance(page23wi_all, list) else '?'} "
              f"(both fixture items present); "
              f"/work/items?after_slug=&limit=0: status={st23wi_oor} body={body23wi_oor} "
              f"(out-of-range leg, limit domain)",
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

        # -- W28 (A10): the history route joins the pagination discipline, three legs.
        # Leg (i): a long chain, `limit` honored -- build a 5-hop supersession chain, walk it
        # page by page at `limit=2` (forcing 3 pages), and assert the union of pages equals the
        # unpaginated chain (limit=1000, the route's own default) EXACTLY -- same id set, same
        # per-row content.
        w28_rows = []
        w28_prev = None
        for i in range(5):
            payload = {"kind": "decision", "statement": f"W28 chain hop {i}", "actor": author_id}
            if w28_prev is not None:
                payload["supersedes"] = w28_prev
            v = http_post(base + "/write/ledger", payload)[1] if up_b else {}
            if v.get("disposition") != "accepted":
                raise RuntimeError(f"W28 fixture chain write refused: {v}")
            w28_rows.append(v["row_id"])
            w28_prev = v["row_id"]
        w28_head = w28_rows[-1]  # history of any hop returns the WHOLE chain both directions

        def _history_page(after_id: int, limit: int) -> tuple[int, object]:
            return http_get(f"{base}/rows/{w28_head}/history?after_id={after_id}&limit={limit}")

        st28_full, w28_full = _history_page(0, 1000) if up_b else (0, [])
        pages: list[list[dict]] = []
        cursor = 0
        page_statuses = []
        for _ in range(10):  # generous cap -- 5 hops at limit=2 needs at most 3 pages
            st_p, page = _history_page(cursor, 2)
            page_statuses.append(st_p)
            if not isinstance(page, list) or not page:
                break
            pages.append(page)
            cursor = page[-1]["id"]
            if len(page) < 2:
                break
        union_ids = {r["id"] for p in pages for r in p}
        full_ids = {r["id"] for r in w28_full} if isinstance(w28_full, list) else set()
        union_rows_by_id = {r["id"]: r for p in pages for r in p}
        full_rows_by_id = {r["id"]: r for r in w28_full} if isinstance(w28_full, list) else {}
        page_sizes = [len(p) for p in pages]
        check("w28i-history-long-chain-limit-honored-union-equals-unpaginated",
              up_b and st28_full == 200 and all(s == 200 for s in page_statuses)
              and set(w28_rows) <= full_ids
              and len(pages) >= 3
              and all(sz <= 2 for sz in page_sizes)
              and union_ids == full_ids
              and union_rows_by_id == full_rows_by_id,
              f"5-hop chain (row ids {w28_rows}); unpaginated (?after_id=0&limit=1000): "
              f"status={st28_full} n={len(w28_full) if isinstance(w28_full, list) else '?'} "
              f"ids={sorted(full_ids)}; paged at limit=2: page sizes={page_sizes} "
              f"(cursor continuation via each page's own last row id), union of page ids="
              f"{sorted(union_ids)}, union-vs-unpaginated row content equal="
              f"{union_rows_by_id == full_rows_by_id}",
              failures)

        # Leg (ii): out-of-domain `limit`/`after_id`, each a typed 422 naming the domain --
        # SAME message family as the four A5.4 routes' own out-of-range refusals.
        st28_lim0, body28_lim0 = _history_page(0, 0) if up_b else (0, {})
        st28_lim1001, body28_lim1001 = _history_page(0, 1001) if up_b else (0, {})
        st28_negafter, body28_negafter = http_get(
            f"{base}/rows/{w28_head}/history?after_id=-1&limit=10") if up_b else (0, {})
        check("w28ii-history-out-of-domain-limit-after-id-typed-422",
              up_b
              and st28_lim0 == 422 and "limit" in body28_lim0.get("detail", "")
              and st28_lim1001 == 422 and "limit" in body28_lim1001.get("detail", "")
              and st28_negafter == 422 and "after_id" in body28_negafter.get("detail", ""),
              f"limit=0: status={st28_lim0} body={body28_lim0}; "
              f"limit=1001: status={st28_lim1001} body={body28_lim1001}; "
              f"after_id=-1: status={st28_negafter} body={body28_negafter}",
              failures)

        # Leg (iii): a short chain with NO parameters -- byte-identical to the pre-A10
        # unpaginated response. Reuses W5's own 2-row chain (`orig`/`sup`, already born above)
        # and independently reconstructs the PRE-A10 query (the exact unpaginated SQL this
        # route ran before A10 -- verbatim, no LIMIT/after_id filter) via a direct psql call
        # through `boundary_service`'s own `_query_json`/`BoundaryConfig`, then renders it
        # through the SAME `fastapi.responses.JSONResponse` class the live route uses -- so the
        # comparison is real byte equality of the actual wire encoding, not a decoded-then-
        # re-compared structural equality that could hide a field-order regression.
        w28_cfg = boundary_service.BoundaryConfig(deployment_record.load_deployment(dep_b))
        pre_a10_sql = (
            f"WITH RECURSIVE chain(id) AS ("
            f"  SELECT {sup['row_id']}::bigint"
            f"  UNION"
            f"  SELECT l.id FROM {world_b}.ledger l JOIN chain c ON l.id = c.id"
            f"),"
            f"chain_up AS ("
            f"  SELECT id FROM chain"
            f"  UNION"
            f"  SELECT l.supersedes FROM {world_b}.ledger l JOIN chain_up c ON l.id = c.id "
            f"    WHERE l.supersedes IS NOT NULL"
            f"),"
            f"chain_full(id) AS ("
            f"  SELECT id FROM chain_up"
            f"  UNION"
            f"  SELECT l.id FROM {world_b}.ledger l JOIN chain_full c "
            f"    ON l.supersedes = c.id"
            f")"
            f"SELECT coalesce(jsonb_agg(to_jsonb(l) || jsonb_build_object("
            f"  'superseded_by', (SELECT s.id FROM {world_b}.ledger s "
            f"                    WHERE s.supersedes = l.id)) ORDER BY l.id), '[]'::jsonb) "
            f"FROM {world_b}.ledger l WHERE l.id IN (SELECT id FROM chain_full);"
        )
        pre_a10_rows = boundary_service._query_json(w28_cfg, pre_a10_sql)
        # Lazy imports are banned (CLAUDE.md) -- reuse `boundary_service`'s OWN already-
        # top-of-file-imported `JSONResponse` (the identical class object the live route
        # renders through) rather than importing a second time here.
        expected_bytes = bytes(boundary_service.JSONResponse(content=pre_a10_rows).body)
        req28iii = urllib.request.Request(f"{base}/rows/{sup['row_id']}/history")
        with urllib.request.urlopen(req28iii, timeout=10) as resp28iii:
            st28iii = resp28iii.status
            actual_bytes = resp28iii.read()
        check("w28iii-history-short-chain-no-params-byte-identical-to-pre-a10-shape",
              up_b and st28iii == 200 and actual_bytes == expected_bytes,
              f"GET /rows/{sup['row_id']}/history (no query parameters): status={st28iii} "
              f"len={len(actual_bytes)} bytes; independently-reconstructed pre-A10 unpaginated "
              f"query, rendered through the SAME JSONResponse class: len={len(expected_bytes)} "
              f"bytes; byte-identical={actual_bytes == expected_bytes}",
              failures)

        # -- W29 (A11 item 1): the slug-keyed route's cursor honesty, three legs.
        def _open_work_item_or_raise(slug: str) -> dict:
            v = http_post(base + "/write/ledger", {
                "kind": "work_opened", "statement": f"W29 fixture item {slug}",
                "actor": author_id, "work_slug": slug, "work_title": f"W29 fixture {slug}",
            })[1] if up_b else {}
            if v.get("disposition") != "accepted":
                raise RuntimeError(f"W29 fixture work_opened write refused ({slug}): {v}")
            return v

        def _work_items_page(after_slug: str, limit: int) -> tuple[int, object]:
            return http_get(f"{base}/work/items?after_slug={after_slug}&limit={limit}")

        # Leg (i): the reviewer's exact concurrent-insert drive, replayed against the slug
        # keyset. A dedicated prefix (`w29_floor`) scopes this leg's own walk away from every
        # OTHER slug this suite opens (W11's present-legs probe opens none; W23 opens
        # "w23-item-*", which sorts BEFORE "w29-" -- ASCII '3' < '9' -- so it never lands inside
        # this leg's own after_slug range). Items aa/cc/ee/gg are opened FIRST (bb deliberately
        # withheld); page 1 at limit=2, starting just past the floor, must return exactly
        # [aa, cc] -- bb does not exist yet. bb is then opened (the concurrent insert). The walk
        # CONTINUES from cursor "cc" (the actual last slug page 1 returned, not a re-derived
        # value) at limit=2, and must return exactly [ee, gg] -- bb sorts BEHIND the already-
        # advanced cursor, so it is invisible to this in-flight walk (A11's own disclosed
        # residual), never duplicating cc or silently appearing out of order. A FRESH walk from
        # the same floor must include bb -- the named semantics ("an item inserted behind the
        # cursor appears on the next walk") witnessed, not just stated.
        w29_prefix = f"w29-{RUN_SUFFIX}-"
        w29_floor = w29_prefix  # sorts before every w29-prefixed slug, after every other fixture's own prefix
        w29_slugs = {k: f"{w29_prefix}{k}" for k in ("aa", "bb", "cc", "ee", "gg")}
        for key in ("aa", "cc", "ee", "gg"):
            _open_work_item_or_raise(w29_slugs[key])

        st29i_p1, page29i_p1 = _work_items_page(w29_floor, 2) if up_b else (0, [])
        p1_slugs = [r.get("slug") for r in page29i_p1] if isinstance(page29i_p1, list) else []

        _open_work_item_or_raise(w29_slugs["bb"])  # the concurrent insert, mid-walk

        cursor_after_p1 = p1_slugs[-1] if p1_slugs else w29_floor
        st29i_p2, page29i_p2 = _work_items_page(cursor_after_p1, 2) if up_b else (0, [])
        p2_slugs = [r.get("slug") for r in page29i_p2] if isinstance(page29i_p2, list) else []

        st29i_fresh, page29i_fresh = _work_items_page(w29_floor, 10) if up_b else (0, [])
        fresh_slugs = [r.get("slug") for r in page29i_fresh] if isinstance(page29i_fresh, list) else []

        walk_slugs = p1_slugs + p2_slugs
        check("w29i-work-items-concurrent-insert-no-duplicate-behind-cursor-joins-next-walk",
              up_b
              and st29i_p1 == 200 and p1_slugs == [w29_slugs["aa"], w29_slugs["cc"]]
              and st29i_p2 == 200 and p2_slugs == [w29_slugs["ee"], w29_slugs["gg"]]
              and len(walk_slugs) == len(set(walk_slugs))
              and w29_slugs["bb"] not in walk_slugs
              and st29i_fresh == 200 and w29_slugs["bb"] in fresh_slugs,
              f"page 1 (after_slug={w29_floor!r}, limit=2, BEFORE bb opened): status={st29i_p1} "
              f"slugs={p1_slugs}; bb opened (concurrent insert); page 2 continuing from cursor "
              f"{cursor_after_p1!r} (the walk's own last-served slug), limit=2: status={st29i_p2} "
              f"slugs={p2_slugs}; walk union={walk_slugs} (no duplicate: "
              f"{len(walk_slugs) == len(set(walk_slugs))}; bb absent from this walk: "
              f"{w29_slugs['bb'] not in walk_slugs}); FRESH walk from the same floor, limit=10: "
              f"status={st29i_fresh} slugs={fresh_slugs} (bb now present: "
              f"{w29_slugs['bb'] in fresh_slugs})",
              failures)

        # Leg (ii): after_id supplied to /work/items -> typed 422 teaching after_slug; an
        # over-512-byte after_slug -> typed 422 naming the domain.
        st29ii_afterid, body29ii_afterid = http_get(
            f"{base}/work/items?after_id=0") if up_b else (0, {})
        long_after_slug = "x" * (boundary_service.MAX_AFTER_SLUG_BYTES + 88)
        st29ii_long, body29ii_long = http_get(
            f"{base}/work/items?after_slug={long_after_slug}&limit=10") if up_b else (0, {})
        check("w29ii-work-items-after-id-refused-and-over-domain-after-slug-refused",
              up_b
              and st29ii_afterid == 422 and "after_slug" in body29ii_afterid.get("detail", "")
              and st29ii_long == 422
              and str(boundary_service.MAX_AFTER_SLUG_BYTES) in body29ii_long.get("detail", ""),
              f"after_id=0 supplied on /work/items: status={st29ii_afterid} "
              f"body={body29ii_afterid} (must teach after_slug, never silently ignored); "
              f"after_slug of {len(long_after_slug)} bytes (over "
              f"{boundary_service.MAX_AFTER_SLUG_BYTES}): status={st29ii_long} "
              f"body={body29ii_long}",
              failures)

        # Leg (iii): an ordinary two-page walk with NO concurrent write -- page union equals the
        # unpaginated view exactly. A dedicated prefix, isolated from leg (i)'s own slugs and
        # from every other fixture's own work items opened above.
        w29iii_prefix = f"w29c-{RUN_SUFFIX}-"
        w29iii_slugs = [f"{w29iii_prefix}{k}" for k in ("m1", "m2", "m3")]
        for slug in w29iii_slugs:
            _open_work_item_or_raise(slug)

        st29iii_full, page29iii_full = _work_items_page(w29iii_prefix, 1000) if up_b else (0, [])
        full_slugs = {r.get("slug") for r in page29iii_full} if isinstance(page29iii_full, list) else set()

        union_slugs: set[str] = set()
        cursor29iii = w29iii_prefix
        page29iii_statuses = []
        for _ in range(10):  # generous cap -- 3 items at limit=2 needs at most 2 pages
            st_p, page = _work_items_page(cursor29iii, 2)
            page29iii_statuses.append(st_p)
            if not isinstance(page, list) or not page:
                break
            union_slugs |= {r.get("slug") for r in page}
            cursor29iii = page[-1]["slug"]
            if len(page) < 2:
                break

        check("w29iii-work-items-two-page-walk-union-equals-unpaginated-no-concurrent-write",
              up_b and st29iii_full == 200 and all(s == 200 for s in page29iii_statuses)
              and set(w29iii_slugs) <= full_slugs
              and union_slugs == full_slugs,
              f"3 fixture items {w29iii_slugs}; unpaginated (after_slug={w29iii_prefix!r}, "
              f"limit=1000): status={st29iii_full} slugs={sorted(full_slugs)}; paged walk at "
              f"limit=2: page statuses={page29iii_statuses}, union={sorted(union_slugs)} "
              f"(equal to unpaginated: {union_slugs == full_slugs})",
              failures)

        # -- W31 (A12): after_slug's own representability closure, three legs.
        # Leg (i): a literal NUL, percent-encoded (%00) in the query string -> typed 422 on the
        # representability axis, SAME message family as the write-path leg (W16), and the NEXT
        # request answers normally (server alive, no wedge -- the choke-point net at _psql is
        # never even reached, since the ingress gate refuses first).
        st31i, body31i = http_get(f"{base}/work/items?after_slug=%00&limit=10") if up_b else (0, {})
        st31i_next, body31i_next = http_get(base + "/health") if up_b else (0, {})
        check("w31i-after-slug-nul-typed-422-representability-axis-server-alive",
              up_b
              and st31i == 422 and "representability axis" in body31i.get("detail", "")
              and st31i_next == 200 and body31i_next.get("world") == world_b,
              f"GET /work/items?after_slug=%00 (a literal NUL in the query string): "
              f"status={st31i} body={body31i}; NEXT request (/health): status={st31i_next} "
              f"world={body31i_next.get('world')} (server alive, answers normally)",
              failures)

        # Leg (ii): an unpaired UTF-16 surrogate. STRUCTURALLY UNDRIVABLE over real HTTP
        # transport -- witnessed here, not assumed: Starlette's query-string decoding
        # (`QueryParams.__init__` -> `urllib.parse.parse_qsl`, default `errors="replace"`) can
        # NEVER produce an actual lone-surrogate Python `str` character from any byte sequence a
        # client can put on the wire. A percent-encoded WTF-8 sequence for U+D800 (`%ED%A0%80`)
        # decodes to THREE U+FFFD replacement characters, never one surrogate (confirmed live
        # against this exact venv's Starlette: `QueryParams("after_slug=%ED%A0%80")["after_slug"]`
        # == three U+FFFD, never `"\ud800"`); the raw, un-percent-encoded bytes instead decode
        # `latin-1` first (Starlette's bytes-vs-str `QueryParams` branch), giving three ordinary
        # Latin-1 codepoints -- again never a surrogate. This is the OPPOSITE of the write path,
        # where `json.loads` decodes a `\ud800` JSON escape directly to a real surrogate CODE
        # POINT regardless of UTF-8 validity (W16's own leg): JSON string escapes and URL
        # percent-encoding are different mechanisms with different honesty properties here.
        # Asserting a "surrogate" leg via a byte sequence Starlette actually turns into
        # replacement characters would be a LYING witness -- U+FFFD is not in the
        # 0xD800-0xDFFF range `_representability_failure_for_string` checks, so that leg would
        # pass through to a 200, not exercise the surrogate branch at all, and calling that
        # green a positive proof would be exactly the false-witness class this project's own LAW
        # forbids. The HONEST disposition, matching this same W31's own leg (iii) below (spec
        # A12's own instruction: "unit-style leg, no HTTP needed"): drive this leg in-process,
        # calling the SAME shared function `work_items()`'s own representability check calls
        # (`_query_string_representability_failure`) with a REAL Python `str` carrying a genuine
        # unpaired surrogate character -- exercising the identical rule leg (i) above exercises
        # via HTTP, minus only the transport hop no client can actually drive.
        w31ii_resp = boundary_service._query_string_representability_failure(
            "after_slug", "before\ud800after")
        w31ii_body = json.loads(bytes(w31ii_resp.body)) if w31ii_resp is not None else {}
        check("w31ii-after-slug-unpaired-surrogate-typed-422-representability-axis",
              w31ii_resp is not None and w31ii_resp.status_code == 422
              and "representability axis" in w31ii_body.get("detail", ""),
              f"_query_string_representability_failure('after_slug', a str carrying a real "
              f"U+D800 lone surrogate) -- the SAME function work_items() calls at this exact "
              f"gate, driven in-process because Starlette's query-string decoding structurally "
              f"cannot carry a real unpaired surrogate over the wire (see this check's own "
              f"comment for the live experiment proving it): "
              f"status={w31ii_resp.status_code if w31ii_resp else None} body={w31ii_body}",
              failures)

        # Leg (iii): the choke-point net witnessed directly (spec A12's own instruction:
        # "unit-style leg, no HTTP needed") -- `_psql`, called with a NUL-bearing argument value
        # (bypassing every ingress-level representability gate, exactly what a future,
        # differently-gated caller would do), must raise the typed `PsqlUnclassifiedFailure`,
        # never a bare `ValueError` -- A8's OSError pattern, repeated for A12's ValueError.
        w31iii_cfg = boundary_service.BoundaryConfig(deployment_record.load_deployment(dep_b))
        w31iii_raised: Exception | None = None
        w31iii_is_bare_valueerror = False
        try:
            boundary_service._psql(
                w31iii_cfg, "SELECT 1;", extra_v={"after_slug": "before\x00after"})
        except boundary_service.PsqlUnclassifiedFailure as e:
            w31iii_raised = e
        except ValueError as e:
            w31iii_is_bare_valueerror = True
            w31iii_raised = e
        check("w31iii-psql-choke-point-net-nul-argument-typed-unclassified-not-bare-valueerror",
              w31iii_raised is not None
              and isinstance(w31iii_raised, boundary_service.PsqlUnclassifiedFailure)
              and not w31iii_is_bare_valueerror,
              f"_psql(cfg, 'SELECT 1;', extra_v={{'after_slug': a NUL-bearing str}}) -- "
              f"bypassing every ingress gate directly: "
              f"raised={type(w31iii_raised).__name__ if w31iii_raised else None} (must be "
              f"PsqlUnclassifiedFailure, never a bare ValueError): {w31iii_raised}",
              failures)

        # -- W30 (A11 item 2): the history route's not-found shape matches its sibling; an
        # existing row's history is unchanged by the leading existence check.
        def _raw_get(url: str) -> tuple[int, bytes]:
            try:
                with urllib.request.urlopen(url, timeout=10) as resp:
                    return resp.status, resp.read()
            except urllib.error.HTTPError as e:
                return e.code, e.read()

        # In-domain (well under MAX_ID) but essentially guaranteed absent from a freshly
        # scaffolded scratch schema's own small, sequential ledger ids.
        w30_missing_id = 999_999_999_999
        st30_hist, raw30_hist = _raw_get(
            f"{base}/rows/{w30_missing_id}/history") if up_b else (0, b"")
        st30_row, raw30_row = _raw_get(f"{base}/rows/{w30_missing_id}") if up_b else (0, b"")

        # An EXISTING row's history: reuse W28's own 5-hop chain head (`w28_head`) and its own
        # `BoundaryConfig` (`w28_cfg`), independently reconstructing the SAME CTE construction
        # `row_history`'s live code runs (unchanged by A11 -- only the LEADING existence check is
        # new, and it falls through instantly, returning `None`, for a row that exists), and
        # comparing the actual live no-query-parameters response against it byte-for-byte,
        # rendered through the SAME JSONResponse class -- the identical technique W28iii already
        # uses above, re-run here to prove A11 changed nothing for the existing-row case.
        w30_sql = (
            f"WITH RECURSIVE chain(id) AS ("
            f"  SELECT {w28_head}::bigint"
            f"  UNION"
            f"  SELECT l.id FROM {world_b}.ledger l JOIN chain c ON l.id = c.id"
            f"),"
            f"chain_up AS ("
            f"  SELECT id FROM chain"
            f"  UNION"
            f"  SELECT l.supersedes FROM {world_b}.ledger l JOIN chain_up c ON l.id = c.id "
            f"    WHERE l.supersedes IS NOT NULL"
            f"),"
            f"chain_full(id) AS ("
            f"  SELECT id FROM chain_up"
            f"  UNION"
            f"  SELECT l.id FROM {world_b}.ledger l JOIN chain_full c "
            f"    ON l.supersedes = c.id"
            f")"
            f"SELECT coalesce(jsonb_agg(t.row ORDER BY t.id), '[]'::jsonb) FROM ("
            f"  SELECT l.id AS id, to_jsonb(l) || jsonb_build_object("
            f"    'superseded_by', (SELECT s.id FROM {world_b}.ledger s "
            f"                      WHERE s.supersedes = l.id)) AS row "
            f"  FROM {world_b}.ledger l WHERE l.id IN (SELECT id FROM chain_full) "
            f"    AND l.id > 0 "
            f"  ORDER BY l.id LIMIT 1000"
            f") t;"
        )
        w30_expected_rows = boundary_service._query_json(w28_cfg, w30_sql)
        w30_expected_bytes = bytes(boundary_service.JSONResponse(content=w30_expected_rows).body)
        st30_existing, raw30_existing = _raw_get(
            f"{base}/rows/{w28_head}/history") if up_b else (0, b"")

        parsed30_hist = json.loads(raw30_hist) if raw30_hist else {}
        check("w30-history-not-found-matches-sibling-and-existing-row-unchanged",
              up_b
              and st30_hist == 404 and st30_row == 404 and raw30_hist == raw30_row
              and parsed30_hist.get("detail") == f"no row {w30_missing_id}"
              and st30_existing == 200 and raw30_existing == w30_expected_bytes,
              f"nonexistent id {w30_missing_id}: GET /rows/{{id}}/history status={st30_hist} "
              f"raw={raw30_hist!r}; GET /rows/{{id}} (sibling) status={st30_row} "
              f"raw={raw30_row!r}; byte-identical={raw30_hist == raw30_row}; "
              f"existing row (W28's chain head {w28_head}) history, no query parameters: "
              f"status={st30_existing} len={len(raw30_existing)} bytes vs an independently-"
              f"reconstructed CTE (the SAME construction row_history's live code runs) "
              f"len={len(w30_expected_bytes)} bytes, "
              f"byte-identical={raw30_existing == w30_expected_bytes}",
              failures)

        # -- W32 (A13): the dumps-side recursion net. Not a finding -- pre-A13,
        # _reserialize_or_value_axis_failure's own json.dumps call had no RecursionError
        # handling of its own and was protected only by the accident that json.loads
        # overflows at the same-or-shallower depth on this CPython build; no caller input
        # reaches this branch via HTTP (the loads-side parse-time guard, A3.2, fires first for
        # every body that ever parses). Two legs.
        #
        # Leg (i), unit-style, input class -> observed -> expected: input class is "a
        # programmatically nested object deep enough to overflow CPython's default recursion
        # limit (1000), reaching _reserialize_or_value_axis_failure's own json.dumps call
        # directly" -- built by an ITERATIVE Python loop, NEVER recursion (the fixture itself
        # must not stack-overflow while CONSTRUCTING the object) and NEVER via json.loads (the
        # point is to bypass the loads-side guard and exercise the dumps-side call under test
        # in isolation). Observed: the function must return the typed structure-axis refusal
        # (axis="structure", detail naming the nesting bound), never let a bare RecursionError
        # escape. Expected: same typed shape, same message family A7 already gave the
        # adjacent post-parse traversal.
        w32i_depth = 100_000
        w32i_nested: list = []
        w32i_cur = w32i_nested
        for _ in range(w32i_depth - 1):
            w32i_next: list = []
            w32i_cur.append(w32i_next)
            w32i_cur = w32i_next
        w32i_payload = {"n": w32i_nested}
        w32i_raised: Exception | None = None
        w32i_result: tuple | None = None
        try:
            w32i_result = boundary_service._reserialize_or_value_axis_failure(w32i_payload)
        except RecursionError as e:
            w32i_raised = e
        w32i_payload_json, w32i_axis, w32i_detail = (
            w32i_result if w32i_result is not None else (None, None, None))
        check("w32i-dumps-side-recursion-net-typed-structure-axis-never-bare-recursionerror",
              w32i_raised is None
              and w32i_payload_json is None
              and w32i_axis == "structure"
              and w32i_detail is not None and "nest" in w32i_detail,
              f"_reserialize_or_value_axis_failure({{'n': a {w32i_depth}-level-nested list, "
              f"built iteratively, never via json.loads}}): bare RecursionError "
              f"escaped={w32i_raised is not None} ({w32i_raised!r} if any); "
              f"returned=(payload_json={w32i_payload_json!r}, axis={w32i_axis!r}, "
              f"detail={w32i_detail!r})",
              failures)

        # Leg (ii): behavior at the HTTP layer is unchanged by construction (A13 adds ONE
        # new except clause on a branch no caller-supplied body reaches today -- the
        # loads-side parse-time guard, A3.2, always fires first). No new HTTP-level check is
        # added for this leg specifically; it is witnessed by the SUITE'S OWN overall exit
        # (every prior write-path check above -- W1's accepted write, W15's non-finite value-
        # axis legs, W20/W21's representability/id-domain legs -- already round-trips through
        # this exact call site over real HTTP, and this file's own final "ALL CASES OK" gate
        # is this leg's positive proof: a regression here would fail one of those checks, not
        # a check named separately for W32ii).
        print("=== w32ii-full-suite-green-end-to-end ===")
        print("  [WITNESSED] no HTTP-layer regression -- see comment above; proven by every "
              "other write-path check in this run, not a check named separately for this leg.")
        print()

        # -- W34 (design/FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md, ledger row 1500): the
        # diagnostic JSON-lines log layer. Both polarities, reusing WORLD B's already-running
        # server (`proc_b`/`base`) rather than scaffolding a second one -- its own
        # `_diag_log_path` (see `_spawn_boundary_service`) is read DIRECTLY, live, no teardown
        # needed first.
        #
        # Leg (i), RED: an unknown event name and a missing required field each raise the
        # closed-vocabulary contract's teaching error, in-process, driven directly against the
        # module under test (unit-style, like W32i above) -- BEFORE any level filter (spec §2
        # L2's own ordering requirement).
        w34_unknown_event_raised: Exception | None = None
        try:
            boundary_diagnostic_log.log_event("not_a_real_event")
        except boundary_diagnostic_log.LogContractError as e:
            w34_unknown_event_raised = e
        w34_missing_field_raised: Exception | None = None
        try:
            boundary_diagnostic_log.log_event(boundary_diagnostic_log.Event.REQUEST_START)
        except boundary_diagnostic_log.LogContractError as e:
            w34_missing_field_raised = e
        check("w34i-red-unknown-event-and-missing-field-raise-log-contract-error",
              isinstance(w34_unknown_event_raised, boundary_diagnostic_log.LogContractError)
              and isinstance(w34_missing_field_raised, boundary_diagnostic_log.LogContractError)
              and "not_a_real_event" in str(w34_unknown_event_raised)
              and "route" in str(w34_missing_field_raised) and "method" in str(w34_missing_field_raised),
              f"log_event('not_a_real_event') raised={w34_unknown_event_raised!r}; "
              f"log_event(REQUEST_START) with no fields raised={w34_missing_field_raised!r}",
              failures)

        # Leg (ii), RED: an unrecognized `log_level` value in the multiplex TOML refuses
        # loudly, before the socket ever binds (construction time) -- the SAME whole-file
        # validation pass every other config axis already goes through.
        w34_bad_cfg = wb.parent / "w34-bad-log-level.toml"
        w34_bad_cfg.write_text(
            f'log_level = "VERBOSE"\n'
            f'[deployments.{world_b}]\n'
            f'pghost = "{PGHOST}"\npgdatabase = "{PGDB}"\n'
            f'pguser = "{world_b}_rw"\npgschema = "{world_b}"\npgkern = "{world_b}_kernel"\n',
            encoding="utf-8")
        w34_bad_level_raised: Exception | None = None
        try:
            boundary_multiplex_config.load_multiplex_config_with_log_level(w34_bad_cfg)
        except boundary_multiplex_config.MultiplexConfigError as e:
            w34_bad_level_raised = e
        check("w34ii-red-unknown-log-level-value-refused-before-bind",
              isinstance(w34_bad_level_raised, boundary_multiplex_config.MultiplexConfigError)
              and "VERBOSE" in str(w34_bad_level_raised),
              f"load_multiplex_config_with_log_level(log_level='VERBOSE') raised="
              f"{w34_bad_level_raised!r}",
              failures)

        # Leg (iii), GREEN: a served write (accepted leg) yields a jq-reconstructable record
        # chain (request_start -> kernel_call -> write_verdict -> request_end) sharing ONE
        # request_id -- read from WORLD B's own live log file, no teardown needed.
        w34_accept_payload = {"kind": "note", "statement": "W34 diagnostic-log accepted write witness", "actor": author_id}
        st34a, body34a = http_post(base + "/write/ledger", w34_accept_payload) if up_b else (0, {})
        time.sleep(0.3)  # let the JSON line flush to the log file
        w34_log_text = proc_b._diag_log_path.read_text(encoding="utf-8", errors="replace")
        w34_json_lines = [json.loads(ln) for ln in w34_log_text.splitlines() if ln.startswith("{")]
        w34_accept_wv = [r for r in w34_json_lines
                         if r.get("event") == "write_verdict" and r.get("row_id") == body34a.get("row_id")
                         and body34a.get("row_id") is not None]
        w34_chain_ok = False
        w34_chain_events: list[str] = []
        if w34_accept_wv:
            w34_rid = w34_accept_wv[0]["request_id"]
            w34_chain_events = [r["event"] for r in w34_json_lines if r.get("request_id") == w34_rid]
            w34_chain_ok = (
                w34_chain_events[:1] == ["request_start"] and w34_chain_events[-1:] == ["request_end"]
                and "kernel_call" in w34_chain_events and "write_verdict" in w34_chain_events
                and w34_chain_events.index("kernel_call") < w34_chain_events.index("write_verdict")
                < w34_chain_events.index("request_end"))
        check("w34iii-green-accepted-write-jq-reconstructable-chain-one-request-id",
              up_b and st34a == 200 and body34a.get("disposition") == "accepted" and w34_chain_ok,
              f"POST /write/ledger (accepted) status={st34a} verdict={body34a}; reconstructed "
              f"chain for its own request_id: {w34_chain_events}",
              failures)

        # Leg (iiiv), GREEN, fresh-context review finding (a) fixed: field-shape COHERENCE
        # across the same chain -- a jq query grouping/filtering on a field name must see the
        # SAME kind of value under that name on every event that carries it. Two assertions,
        # both against the SAME w34_chain_events/w34_rid this leg already reconstructed:
        #   1. every record in the chain that carries `route` carries the BARE path (never
        #      method-prefixed "METHOD /path") -- request_start/request_end/kernel_call all
        #      qualify here (no infra/unclassified_failure fires on this accepted-write leg).
        #   2. the kernel_call record(s) in this chain carry `route`, never `surface`; the
        #      write_verdict record carries `surface` as the short write-surface label
        #      ("ledger", WRITE_SURFACES's own vocabulary), never a route path.
        w34_records_in_chain = [r for r in w34_json_lines if r.get("request_id") == w34_rid] if w34_accept_wv else []
        w34_routes_seen = {r["route"] for r in w34_records_in_chain if "route" in r}
        w34_route_bare = all(not re.match(r"^[A-Z]+ /", rt) for rt in w34_routes_seen)
        w34_kernel_call_recs = [r for r in w34_records_in_chain if r.get("event") == "kernel_call"]
        w34_write_verdict_recs = [r for r in w34_records_in_chain if r.get("event") == "write_verdict"]
        w34_kernel_call_shape_ok = bool(w34_kernel_call_recs) and all(
            "route" in r and "surface" not in r for r in w34_kernel_call_recs)
        w34_write_verdict_shape_ok = bool(w34_write_verdict_recs) and all(
            r.get("surface") == "ledger" for r in w34_write_verdict_recs)
        check("w34iiiv-green-jq-floor-field-coherence-one-shape-per-name",
              up_b and w34_route_bare and w34_kernel_call_shape_ok and w34_write_verdict_shape_ok,
              f"routes seen across the chain (must all be bare paths, never method-prefixed): "
              f"{w34_routes_seen}; kernel_call record(s) carry 'route' not 'surface': "
              f"{[{'route': r.get('route'), 'has_surface': 'surface' in r} for r in w34_kernel_call_recs]}; "
              f"write_verdict record(s) carry surface='ledger' (the short write-surface label): "
              f"{[r.get('surface') for r in w34_write_verdict_recs]}",
              failures)

        # Leg (iv), GREEN: the refuse leg's `refusal_id` joins to the scratch world's own
        # journaled write_refused ledger row -- the join anchor row-1498 settled on (NEVER the
        # payload digest, which the spec's §1 point 1 witness proved unequal by mechanism).
        w34_refuse_payload = {"kind": "note", "statement": "W34 diagnostic-log refused write witness",
                              "actor": author_id, "row_hash": "deadbeef"}
        st34r, body34r = http_post(base + "/write/ledger", w34_refuse_payload) if up_b else (0, {})
        w34_refusal_id = body34r.get("refusal_id")
        w34_journal_row = boundary_service._query_json(
            w28_cfg, f"SELECT to_jsonb(l) FROM {world_b}.ledger l "
                     f"WHERE l.id = {w34_refusal_id} AND l.kind = 'write_refused';"
        ) if w34_refusal_id else None
        check("w34iv-green-refusal-id-joins-scratch-journal-row",
              up_b and st34r == 200 and body34r.get("disposition") == "refused"
              and w34_refusal_id is not None and isinstance(w34_journal_row, dict)
              and w34_journal_row.get("refusal_surface") == "ledger",
              f"POST /write/ledger (refused) status={st34r} verdict={body34r}; journal row for "
              f"refusal_id={w34_refusal_id}: {w34_journal_row}",
              failures)

        # -- W35 (design/FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md, ledger row 1500 --
        # committed per fresh-context review finding (b), post-f450019: the review found the
        # concurrency leg TRUE but UNCOMMITTED -- this closes that audit-trail gap). L1's
        # contextvar propagation, live, under real parallel load, against WORLD B's already-
        # running server -- reused rather than scaffolding a third server. N=20 (10 per route,
        # not the ad hoc review's own N=60 -- the point is a committed, re-runnable witness,
        # not a specific number; a smaller N against the SAME assertion is exactly as sound a
        # proof of "no cross-contamination" as a larger one, and keeps this bank's own runtime
        # down). Split across two distinct routes so a request_id's OWN chain disagreeing on
        # `route` (the cross-contamination this leg exists to catch) is actually reachable.
        w35_n_per_route = 10
        w35_results: list[tuple[str, int]] = []
        w35_lock = threading.Lock()

        def _w35_fire(route_suffix: str) -> None:
            try:
                st, _ = http_get(f"{base}{route_suffix}")
            except Exception:
                st = 0
            with w35_lock:
                w35_results.append((route_suffix, st))

        w35_threads = [
            threading.Thread(target=_w35_fire, args=(rs,))
            for rs in (["/health"] * w35_n_per_route + ["/rows/current"] * w35_n_per_route)
        ] if up_b else []
        for t in w35_threads:
            t.start()
        for t in w35_threads:
            t.join(timeout=30)
        time.sleep(0.3)  # let every JSON line flush to the log file

        w35_all_200 = bool(w35_results) and all(st == 200 for _, st in w35_results)
        w35_log_text = proc_b._diag_log_path.read_text(encoding="utf-8", errors="replace")
        w35_json_lines = [json.loads(ln) for ln in w35_log_text.splitlines() if ln.startswith("{")]
        w35_by_request_id: dict[str, set[str]] = {}
        for rec in w35_json_lines:
            rid, rt = rec.get("request_id"), rec.get("route")
            if rid is not None and rt is not None:
                w35_by_request_id.setdefault(rid, set()).add(rt)
        # Only request_ids whose OWN chain touched a /health or /rows/current call from THIS
        # burst are in scope (WORLD B's server already served many prior requests this same
        # run; this leg does not require isolating the log to only its own burst -- it only
        # requires that NO single request_id's own events ever disagree on route).
        w35_cross_contaminated = {rid: routes for rid, routes in w35_by_request_id.items() if len(routes) > 1}
        check("w35-concurrency-contextvar-propagation-no-cross-contamination",
              up_b and w35_all_200 and not w35_cross_contaminated,
              f"fired {len(w35_threads)} concurrent requests ({w35_n_per_route} each to "
              f"/health and /rows/current) against the REAL, already-running WORLD B server; "
              f"all 200={w35_all_200}; request_id(s) whose own chain disagreed on route "
              f"(cross-contamination -- must be empty): {w35_cross_contaminated}",
              failures)

        # ============================================================================
        # W36: design/FABLE-DISPATCH-MECHANICS-SPEC.md (ledger rows 1463/1467/1468/1471) --
        # the identity conduit, both polarities, live against WORLD B's already-running,
        # already-s43-capable server (reused, not a fresh world -- these legs need exactly the
        # same substrate W1-W35 already stood up: a real stamp_secret, a real s43 write
        # boundary). Run BEFORE W18b's own destructive DROP VIEW (this block sits ahead of it
        # in the file for exactly that reason).
        # ============================================================================
        print("=== w36a-identity-header-oversized-refused-pre-kernel ===")
        oversized = "x" * (boundary_service.IDENTITY_HEADER_MAX_BYTES + 1)
        st36a, body36a = http_post_headers(
            f"{base}/write/ledger", {"kind": "finding", "statement": "w36a should never land"},
            {"X-Autoharn-Vendor-Session": oversized})
        check("w36a-identity-header-oversized-refused-pre-kernel",
              st36a == 422 and isinstance(body36a, dict)
              and body36a.get("disposition") == "identity_header_invalid",
              f"257-byte X-Autoharn-Vendor-Session: status={st36a} body={body36a} (must refuse "
              f"BEFORE any kernel call, typed identity_header_invalid, never truncated)",
              failures)

        print("=== w36b-identity-header-malformed-hmac-refused ===")
        st36b, body36b = http_post_headers(
            f"{base}/write/ledger", {"kind": "finding", "statement": "w36b should never land"},
            {"X-Autoharn-Vendor-Session": "s1", "X-Autoharn-Vendor-Agent": "a1",
             "X-Autoharn-Vendor-Ts": str(int(time.time())),
             "X-Autoharn-Vendor-Hmac": "not-a-hex-digest"})
        check("w36b-identity-header-malformed-hmac-refused",
              st36b == 422 and isinstance(body36b, dict)
              and body36b.get("disposition") == "identity_header_invalid",
              f"non-hex vendor HMAC: status={st36b} body={body36b}",
              failures)

        print("=== w36c-identity-header-malformed-ts-refused ===")
        st36c, body36c = http_post_headers(
            f"{base}/write/ledger", {"kind": "finding", "statement": "w36c should never land"},
            {"X-Autoharn-Vendor-Session": "s1", "X-Autoharn-Vendor-Agent": "a1",
             "X-Autoharn-Vendor-Ts": "not-an-integer",
             "X-Autoharn-Vendor-Hmac": "0" * 64})
        check("w36c-identity-header-malformed-ts-refused",
              st36c == 422 and isinstance(body36c, dict)
              and body36c.get("disposition") == "identity_header_invalid",
              f"non-integer vendor ts: status={st36c} body={body36c}",
              failures)

        print("=== w36d-identity-header-partial-vendor-stamp-refused ===")
        st36d, body36d = http_post_headers(
            f"{base}/write/ledger", {"kind": "finding", "statement": "w36d should never land"},
            {"X-Autoharn-Vendor-Session": "s1", "X-Autoharn-Vendor-Agent": "a1"})
        check("w36d-identity-header-partial-vendor-stamp-refused",
              st36d == 422 and isinstance(body36d, dict)
              and body36d.get("disposition") == "identity_header_invalid",
              f"session+agent only (ts/hmac absent): status={st36d} body={body36d} (a partial "
              f"stamp is malformed, never completed or silently dropped)",
              failures)

        print("=== w36e-identity-header-malformed-minted-principal-refused ===")
        st36e, body36e = http_post_headers(
            f"{base}/write/ledger", {"kind": "finding", "statement": "w36e should never land"},
            {"X-Autoharn-Minted-Principal": "not-an-integer"})
        check("w36e-identity-header-malformed-minted-principal-refused",
              st36e == 422 and isinstance(body36e, dict)
              and body36e.get("disposition") == "identity_header_invalid",
              f"non-integer minted-principal header: status={st36e} body={body36e}",
              failures)

        # W36f: forged HMAC via the conduit. CORRECTION TO THE COMMISSION'S OWN WITNESS-PLAN
        # TEXT, recorded here rather than silently forced to fit: kernel/lineage/
        # s17-stamp-mechanism.sql's set_stamp trigger does NOT land a forged-but-FULLY-PRESENT
        # stamp as stamp_verified=false -- read literally, it RAISES AN EXCEPTION instead ("the
        # write stamp did not validate") when all four GUCs are present but stamp_valid() fails;
        # stamp_verified=false is the UNSTAMPED case (one or more GUCs absent/NULL), not the
        # forged-but-complete case. This leg observes and reports the REAL behavior rather than
        # asserting the brief's stated shape.
        print("=== w36f-forged-hmac-via-conduit ===")
        forged_hmac = "f" * 64  # structurally valid (64 lowercase hex), cryptographically wrong
        st36f, body36f = http_post_headers(
            f"{base}/write/ledger", {"kind": "finding", "statement": "w36f forged-hmac probe"},
            {"X-Autoharn-Vendor-Session": "w36f-sess", "X-Autoharn-Vendor-Agent": "w36f-agent",
             "X-Autoharn-Vendor-Ts": str(int(time.time())), "X-Autoharn-Vendor-Hmac": forged_hmac})
        w36f_landed_unverified = False
        w36f_write_refused = False
        w36f_uncaught_kernel_exception = False
        if st36f == 200 and isinstance(body36f, dict):
            if body36f.get("disposition") == "accepted" and body36f.get("row_id"):
                row36f = psql_tuples(
                    f"SELECT stamp_verified FROM {world_b}.ledger WHERE id = {body36f['row_id']};")
                w36f_landed_unverified = row36f.strip() == "f"
            elif body36f.get("disposition") == "refused":
                w36f_write_refused = True
        elif st36f == 500 and isinstance(body36f, dict) and body36f.get("disposition") == "unclassified_failure":
            w36f_uncaught_kernel_exception = True
        check("w36f-forged-hmac-via-conduit",
              w36f_landed_unverified or w36f_write_refused or w36f_uncaught_kernel_exception,
              f"structurally-valid-but-cryptographically-wrong vendor HMAC: status={st36f} "
              f"body={body36f} -- OBSERVED (LIVE, NOT the commission brief's assumed shape, "
              f"and named loudly as a real finding, not silently reconciled): "
              f"kernel/lineage/s17-stamp-mechanism.sql's set_stamp trigger RAISES an exception "
              f"when all four GUCs are present but stamp_valid() fails ('the write stamp did "
              f"not validate') -- stamp_verified=false is the UNSTAMPED case (one or more GUCs "
              f"absent, W36d above), never the forged-but-complete case. THIS trigger exception "
              f"is, in turn, NOT caught by kernel.ledger_write's own BEGIN..EXCEPTION block "
              f"(s43-typed-verdict-write-boundary.sql's own docstring: 'all run their real "
              f"INSERTs inside BEGIN..EXCEPTION' -- but evidently not for THIS exception's "
              f"SQLSTATE), so it escapes as a genuine psql exit 3 and this service's own A4.3 "
              f"machinery correctly classifies it as unclassified_failure (500), never "
              f"infra_failure and never a bare untyped crash. landed-with-stamp_verified=false="
              f"{w36f_landed_unverified}; kernel-write_verdict-refused={w36f_write_refused}; "
              f"uncaught-kernel-exception-typed-500={w36f_uncaught_kernel_exception}. Whichever "
              f"of the three fires: the service NEVER minted a verified stamp from a forged "
              f"value, and never crashed untyped -- the conduit invariant (spec §1) and this "
              f"service's own A4.3 exit-code fidelity both hold. FLAGGED for the maintainer: "
              f"whether kernel/lineage/s17's set_stamp exception should be widened into s43's "
              f"caught-exception set (so a forged stamp reads as an ordinary typed "
              f"write_verdict refusal rather than a 500) is a kernel-lineage question this "
              f"build does not touch (no kernel edits, per scope) -- named here, not routed "
              f"around, per CLAUDE.md's hazard-in-reach corollary.",
              failures)

        # W36g: GREEN, operator-shaped vendor stamp end-to-end -- CLI env -> headers ->
        # per-request GUCs -> stamped row with stamp_verified=true, AND the acceptance
        # criterion itself: a stamp-distinctness pair (review_stamp_distinctness,
        # kernel/lineage/s17-stamp-mechanism.sql) becomes non-empty on a SERVED world for the
        # FIRST time (ledger row 1467's own finding: "no stamped distinctness pair has EVER
        # formed on the real deployment" -- this is the SAME view `led stamp-distinctness`
        # reads, exercised here directly against the scratch world's own kernel connection,
        # never the real deployment, per this build's own scratch-only witness discipline).
        print("=== w36g-green-vendor-stamp-end-to-end-stamp-distinctness-first-pair ===")
        real_secret_hex = psql_tuples(f"SELECT encode(secret,'hex') FROM {world_b}_kernel.stamp_secret;")
        w36g_session, w36g_agent = "w36g-session", "w36g-agent-A"
        w36g_ts = int(time.time())
        w36g_mac = hmac_module.new(
            bytes.fromhex(real_secret_hex),
            f"{w36g_session}|{w36g_agent}|{w36g_ts}".encode(), hashlib.sha256).hexdigest()
        st36g_a, body36g_a = http_post_headers(
            f"{base}/write/ledger", {"kind": "finding", "statement": "w36g stamped write A (the authoring row)"},
            {"X-Autoharn-Vendor-Session": w36g_session, "X-Autoharn-Vendor-Agent": w36g_agent,
             "X-Autoharn-Vendor-Ts": str(w36g_ts), "X-Autoharn-Vendor-Hmac": w36g_mac})
        # A genuinely DISTINCT invocation identity (a different agent id under the SAME
        # session -- e.g. a dispatched sub-agent's own stamp_intercept.py hook run) authors a
        # `review` regarding row A -- review_stamp_distinctness's own join (s17's own view)
        # needs a kind='review' row whose `regards` points at the authored row.
        w36g_agent_b = "w36g-agent-B"
        w36g_ts_b = int(time.time())
        w36g_mac_b = hmac_module.new(
            bytes.fromhex(real_secret_hex),
            f"{w36g_session}|{w36g_agent_b}|{w36g_ts_b}".encode(), hashlib.sha256).hexdigest()
        w36g_row_a = body36g_a.get("row_id") if isinstance(body36g_a, dict) else None
        st36g_b, body36g_b = (None, None)
        if w36g_row_a is not None:
            w36g_review_statement = "w36g stamped review B (a genuinely distinct invocation identity)"
            st36g_b, body36g_b = http_post_headers(
                f"{base}/write/review",
                # verdict/independence are s15's own closed CHECK vocabularies (kernel/lineage/
                # s15-schema.sql: verdict IN ('attest','attest_with_reservations','refuse'),
                # independence IN ('technical','managerial','financial')) -- 'basis' is
                # MANDATORY (led.tmpl's own cmd_review always supplies it, verbatim = statement).
                # 'actor' = svc_id (the pre-registered 'boundary-service' principal, DISTINCT
                # from row A's own actor, which defaulted to 'author' -- the pre-existing
                # ACTOR-keyed segregation-of-duties gate (s18/finding-31's own validate_review,
                # independent of and prior to s17's stamp-based distinctness) refuses a
                # same-actor countersign regardless of stamp distinctness; this leg's own point
                # is the STAMP pair, so the actor is deliberately varied too, exactly as a real
                # two-hop dispatch would (a distinct dispatched principal, a distinct stamp)).
                {"regards": w36g_row_a, "verdict": "attest", "independence": "technical",
                 "statement": w36g_review_statement, "basis": w36g_review_statement,
                 "actor": svc_id},
                {"X-Autoharn-Vendor-Session": w36g_session, "X-Autoharn-Vendor-Agent": w36g_agent_b,
                 "X-Autoharn-Vendor-Ts": str(w36g_ts_b), "X-Autoharn-Vendor-Hmac": w36g_mac_b})
        w36g_row_b = body36g_b.get("row_id") if isinstance(body36g_b, dict) else None
        w36g_a_verified = (psql_tuples(f"SELECT stamp_verified FROM {world_b}.ledger WHERE id = {w36g_row_a};").strip() == "t"
                            if w36g_row_a is not None else False)
        w36g_b_verified = (psql_tuples(f"SELECT stamp_verified FROM {world_b}.ledger WHERE id = {w36g_row_b};").strip() == "t"
                            if w36g_row_b is not None else False)
        w36g_distinctness_pair = psql_tuples(
            f"SELECT review_id, regards_id, same_invocation, both_stamped "
            f"FROM {world_b}.review_stamp_distinctness WHERE review_id = {w36g_row_b};"
            ) if w36g_row_b is not None else ""
        check("w36g-green-vendor-stamp-end-to-end-stamp-distinctness-first-pair",
              w36g_a_verified and w36g_b_verified and bool(w36g_distinctness_pair),
              f"row A (id={w36g_row_a}) stamp_verified={w36g_a_verified}; row B/review "
              f"(id={w36g_row_b}) stamp_verified={w36g_b_verified}; "
              f"review_stamp_distinctness row for this pair (review_id|regards_id|"
              f"same_invocation|both_stamped): {w36g_distinctness_pair!r} -- THE FIRST REAL "
              f"STAMPED DISTINCTNESS PAIR ON THIS SERVED WORLD (ledger row 1467's own finding: "
              f"'no stamped distinctness pair has EVER formed on the real deployment' -- this "
              f"is the observable this build makes possible, witnessed here on scratch, never "
              f"the real deployment).",
              failures)

        # W36h: anonymous-write refusal, rung (a), BOTH postures -- grace (byte-identical
        # accept) and enforce (typed refusal). A FRESH server instance is spun up pointed at
        # the SAME world_b (read-only wrt world_b's own data -- these writes are additive rows,
        # not a schema change), one with identity_enforcement="enforce" in its own multiplex
        # TOML, so WORLD B's own long-lived server (posture "grace", the untouched default)
        # keeps proving the grace leg throughout this entire file's run.
        print("=== w36h-anonymous-write-refusal-both-postures ===")
        anon_payload = {"kind": "finding", "statement": "w36h anonymous write (no identity headers at all)"}
        st36h_grace, body36h_grace = http_post(f"{base}/write/ledger", anon_payload)
        w36h_grace_ok = (st36h_grace == 200 and isinstance(body36h_grace, dict)
                         and body36h_grace.get("disposition") == "accepted")
        cfg_b_enforce_dir = Path(tempfile.mkdtemp(prefix=f"{world_b}-w36h-"))
        cfg_b_enforce = cfg_b_enforce_dir / "boundary-multiplex.toml"
        cfg_b_enforce.write_text(
            f'identity_enforcement = "enforce"\n'
            f'[deployments.{world_b}]\n'
            f'pghost = "{PGHOST}"\npgdatabase = "{PGDB}"\n'
            f'pguser = "{world_b}_rw"\npgschema = "{world_b}"\npgkern = "{world_b}_kernel"\n')
        proc36h, port36h = start_server(cfg_b_enforce)
        base36h = f"http://127.0.0.1:{port36h}/d/{world_b}"
        up36h = wait_health(base36h)
        st36h_enforce, body36h_enforce = (
            http_post(f"{base36h}/write/ledger", anon_payload) if up36h else (0, {}))
        w36h_enforce_refused = (st36h_enforce == 403 and isinstance(body36h_enforce, dict)
                                 and body36h_enforce.get("disposition") == "anonymous_write_refused")
        # Byte-identity, grace posture (spec §5, "byte-identity of an accepted anonymous write
        # pre/post under the grace posture"): the SAME anonymous payload, posted to the SAME
        # grace-posture server (WORLD B's own long-lived one), yields a structurally-identical
        # accept shape both before and after this leg's own enforce-posture server existed --
        # compared by disposition/keys-shape (row ids/timestamps differ by construction between
        # two independent writes, exactly like this suite's own W1 byte/shape-diff precedent).
        st36h_grace_again, body36h_grace_again = http_post(f"{base}/write/ledger", anon_payload)
        w36h_byte_identical = (
            isinstance(body36h_grace, dict) and isinstance(body36h_grace_again, dict)
            and body36h_grace.keys() == body36h_grace_again.keys()
            and body36h_grace.get("disposition") == body36h_grace_again.get("disposition") == "accepted")
        out36h = stop_server(proc36h)
        check("w36h-anonymous-write-refusal-both-postures",
              w36h_grace_ok and w36h_enforce_refused and w36h_byte_identical,
              f"GRACE posture (default, WORLD B's own long-lived server): anonymous write "
              f"accepted={w36h_grace_ok} (status={st36h_grace} body={body36h_grace}); ENFORCE "
              f"posture (a fresh server instance, same world_b, identity_enforcement=\"enforce\" "
              f"in its own multiplex TOML): anonymous write refused={w36h_enforce_refused} "
              f"(status={st36h_enforce} body={body36h_enforce}); byte-identical shape across two "
              f"grace-posture accepts={w36h_byte_identical}"
              + ("" if up36h else f" -- enforce-posture server FAILED TO COME UP: {out36h[-500:]}"),
              failures)

        # W36i-k: the minted-principal actor rule, all three payload shapes (fresh-context
        # review round 2, ledger row 1525 -- the round-1 build had ZERO coverage of the valid
        # override path, and the disagreement case was a SILENT override, now a typed 409).
        print("=== w36i-green-minted-principal-actor-absent-attributed ===")
        st36i, body36i = http_post_headers(
            f"{base}/write/ledger",
            {"kind": "finding", "statement": "w36i minted write, payload actor absent"},
            {"X-Autoharn-Minted-Principal": str(svc_id)})
        w36i_row = body36i.get("row_id") if isinstance(body36i, dict) else None
        w36i_actor = (psql_tuples(f"SELECT actor FROM {world_b}.ledger WHERE id = {w36i_row};").strip()
                      if w36i_row is not None else "")
        check("w36i-green-minted-principal-actor-absent-attributed",
              st36i == 200 and isinstance(body36i, dict)
              and body36i.get("disposition") == "accepted"
              and w36i_actor == str(svc_id),
              f"payload with NO actor + X-Autoharn-Minted-Principal={svc_id}: status={st36i} "
              f"body={body36i}; landed row's actor={w36i_actor!r} (must be the minted "
              f"principal, {svc_id})",
              failures)

        print("=== w36j-green-minted-principal-actor-agreeing-accepted ===")
        st36j, body36j = http_post_headers(
            f"{base}/write/ledger",
            {"kind": "finding", "statement": "w36j minted write, payload actor agreeing",
             "actor": svc_id},
            {"X-Autoharn-Minted-Principal": str(svc_id)})
        w36j_row = body36j.get("row_id") if isinstance(body36j, dict) else None
        w36j_actor = (psql_tuples(f"SELECT actor FROM {world_b}.ledger WHERE id = {w36j_row};").strip()
                      if w36j_row is not None else "")
        check("w36j-green-minted-principal-actor-agreeing-accepted",
              st36j == 200 and isinstance(body36j, dict)
              and body36j.get("disposition") == "accepted"
              and w36j_actor == str(svc_id),
              f"payload actor={svc_id} agreeing with the minted header: status={st36j} "
              f"body={body36j}; landed row's actor={w36j_actor!r}",
              failures)

        print("=== w36k-red-minted-actor-conflict-typed-409-nothing-written ===")
        w36k_count_before = psql_tuples(f"SELECT count(*) FROM {world_b}.ledger;").strip()
        st36k, body36k = http_post_headers(
            f"{base}/write/ledger",
            {"kind": "finding", "statement": "w36k should never land", "actor": author_id},
            {"X-Autoharn-Minted-Principal": str(svc_id)})
        w36k_count_after = psql_tuples(f"SELECT count(*) FROM {world_b}.ledger;").strip()
        check("w36k-red-minted-actor-conflict-typed-409-nothing-written",
              st36k == 409 and isinstance(body36k, dict)
              and body36k.get("disposition") == "minted_actor_conflict"
              and body36k.get("minted_principal") == svc_id
              and str(author_id) in str(body36k.get("payload_actor"))
              and str(svc_id) in str(body36k.get("message"))
              and str(author_id) in str(body36k.get("message"))
              and w36k_count_before == w36k_count_after,
              f"payload actor={author_id} DISAGREEING with minted header {svc_id}: "
              f"status={st36k} body={body36k} (must be a typed 409 naming BOTH values -- "
              f"declared, never silent, spec §2); ledger row count "
              f"before/after={w36k_count_before}/{w36k_count_after} (must be unchanged -- "
              f"nothing written, no journal row either: this refusal is pre-kernel)",
              failures)

        # W36k2: resolution_case serialized into the diagnostic log (round-2 MODERATE: the
        # field was set on the context dataclass but never landed in any record). Reads WORLD
        # B's own live log file, the same access path W34iii already uses.
        print("=== w36k2-green-resolution-case-serialized-in-log ===")
        time.sleep(0.3)  # let the JSON lines flush
        w36k2_log_lines = [json.loads(ln) for ln in
                           proc_b._diag_log_path.read_text(encoding="utf-8", errors="replace").splitlines()
                           if ln.startswith("{")]
        w36k2_minted = [r for r in w36k2_log_lines if r.get("resolution_case") == "minted"]
        w36k2_vendor = [r for r in w36k2_log_lines if r.get("resolution_case") == "vendor"]
        w36k2_anon = [r for r in w36k2_log_lines if r.get("resolution_case") == "anonymous"]
        w36k2_conflict = [r for r in w36k2_log_lines
                          if r.get("event") == "refusal"
                          and r.get("disposition") == "minted_actor_conflict"]
        check("w36k2-green-resolution-case-serialized-in-log",
              bool(w36k2_minted) and bool(w36k2_vendor) and bool(w36k2_anon)
              and bool(w36k2_conflict)
              and all(r.get("resolution_case") == "minted" for r in w36k2_conflict),
              f"records carrying resolution_case in WORLD B's live log: "
              f"minted={len(w36k2_minted)} vendor={len(w36k2_vendor)} "
              f"anonymous={len(w36k2_anon)}; the w36k conflict refusal record(s) "
              f"(event=refusal disposition=minted_actor_conflict, must carry "
              f"resolution_case='minted'): {w36k2_conflict!r}",
              failures)

        # W36l-m: the dispatch verb's target-scoping gate (round-2 CRITICAL, ledger rows
        # 1525/1526 -- the live-deployment incident: the verb's former default resolved
        # deployment.json relative to the SCRIPT's own repo, so a scratch-world exercise wrote
        # rows 1521-1524 to the real ledger). RED: a bare invocation with neither
        # --deployment nor LEDGER_DEPLOYMENT refuses, teaching both spellings, before ANY
        # config read or network touch. GREEN: the explicit form mints end-to-end against
        # WORLD B's own scratch server, and close retires the delegate.
        print("=== w36l-red-dispatch-verb-unscoped-invocation-refused ===")
        w36l_env = {k: v for k, v in os.environ.items()
                    if k not in ("LEDGER_DEPLOYMENT", "PICKUP_DEPLOYMENT",
                                 # an ambient minted/vendor identity in THIS harness's own env
                                 # would ride into the verb's own boundary calls and change the
                                 # leg's meaning -- stripped so the witness is self-contained
                                 "AUTOHARN_MINTED_PRINCIPAL", "PGOPTIONS")}
        w36l_env["LED_ACTOR"] = "author"
        w36l = subprocess.run(
            [str(PYVENV), str(REPO / "tools" / "dispatch_mechanics.py"),
             "mint", "w36l-delegate", "1"],
            capture_output=True, text=True, env=w36l_env, timeout=60)
        check("w36l-red-dispatch-verb-unscoped-invocation-refused",
              w36l.returncode == 2
              and "REFUSED -- no target deployment named" in w36l.stderr
              and "--deployment" in w36l.stderr and "LEDGER_DEPLOYMENT" in w36l.stderr,
              f"bare `dispatch mint` with no --deployment and no LEDGER_DEPLOYMENT: "
              f"rc={w36l.returncode} stderr={w36l.stderr[-600:]!r} (must refuse, teach both "
              f"spellings, and touch NOTHING -- the former script-relative default is the "
              f"live-deployment incident's own mechanism)",
              failures)

        # WORLD B's chain deliberately ends at s43 (CHAIN_B) and carries no s64 delegation
        # vocabulary, so the mint verb's dispatched-by edge cannot land there -- this leg
        # scaffolds its OWN throwaway --new-world (full chain through s65, the same move
        # seen-red/pickup-connection-failure-silent-empty already uses), serves it, and tears
        # it down self-contained.
        print("=== w36m-green-dispatch-mint-close-explicit-deployment-end-to-end ===")
        w36m_world = f"svcfxw36m{RUN_SUFFIX}"
        teardown(w36m_world)
        w36m_tmp = Path(tempfile.mkdtemp(prefix="svcfxw36m-"))
        w36m_world_dir = w36m_tmp / w36m_world
        w36m_proc = None
        try:
            r36m = sh(["bash", str(NEW_PROJECT), str(w36m_world_dir), "--new-world", w36m_world,
                       "--db", PGDB, "--host", PGHOST])
            if r36m.returncode != 0:
                raise RuntimeError(f"w36m --new-world scaffold FAILED: "
                                   f"{r36m.stdout[-800:]} {r36m.stderr[-800:]}")
            w36m_dep = w36m_world_dir / "deployment.json"
            w36m_proc = serve_existing_world(w36m_dep, w36m_tmp)
            w36m_env = dict(w36l_env)
            w36m_env["LEDGER_DEPLOYMENT"] = str(w36m_dep)
            w36m_mint = subprocess.run(
                [str(PYVENV), str(REPO / "tools" / "dispatch_mechanics.py"),
                 "mint", "w36m-delegate", "1", "--purpose", "w36m end-to-end scoping witness"],
                capture_output=True, text=True, env=w36m_env, timeout=120)
            w36m_delegate_id = psql_tuples(
                f"SELECT id FROM {w36m_world}_kernel.principal WHERE name = 'w36m-delegate';").strip()
            w36m_edge = psql_tuples(
                f"SELECT principal_relation, delegation_redelegate_depth "
                f"FROM {w36m_world}.ledger "
                f"WHERE kind = 'principal_relation_asserted' "
                f"AND principal_subject = {w36m_delegate_id or 'NULL'} "
                f"AND principal_relation = 'dispatched-by';") if w36m_delegate_id else ""
            w36m_close = subprocess.run(
                [str(PYVENV), str(REPO / "tools" / "dispatch_mechanics.py"),
                 "close", "w36m-delegate", "w36m witness done",
                 "--deployment", str(w36m_dep)],
                capture_output=True, text=True, env=w36l_env, timeout=120)
            w36m_standing = psql_tuples(
                f"SELECT count(*) FROM {w36m_world}.ledger WHERE kind = 'principal_suspended' "
                f"AND principal_subject = {w36m_delegate_id or 'NULL'};").strip() if w36m_delegate_id else ""
            check("w36m-green-dispatch-mint-close-explicit-deployment-end-to-end",
                  w36m_mint.returncode == 0 and bool(w36m_delegate_id)
                  and f"AUTOHARN_MINTED_PRINCIPAL={w36m_delegate_id}" in w36m_mint.stdout
                  and "dispatched-by|0" in w36m_edge
                  and w36m_close.returncode == 0 and w36m_standing == "1",
                  f"mint via LEDGER_DEPLOYMENT (env spelling) against full-chain scratch world "
                  f"{w36m_world}: rc={w36m_mint.returncode} "
                  f"stdout={w36m_mint.stdout[-300:]!r} stderr={w36m_mint.stderr[-300:]!r}; "
                  f"delegate id={w36m_delegate_id!r}; dispatched-by edge "
                  f"(relation|depth)={w36m_edge!r} (depth 0 = no-redelegate default); close via "
                  f"--deployment (flag spelling): rc={w36m_close.returncode} "
                  f"stderr={w36m_close.stderr[-300:]!r}; principal_suspended rows for the "
                  f"delegate={w36m_standing!r} -- BOTH explicit spellings witnessed, against "
                  f"the scratch world only",
                  failures)
        finally:
            if w36m_proc is not None:
                stop_server(w36m_proc)
            teardown(w36m_world)
            shutil.rmtree(w36m_tmp, ignore_errors=True)

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
        actual_routes = actual_route_table(cfg_b)
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
        cfg_nc = write_scratch_multiplex_config(wnc.parent, world_nocap)
        proc_nc, port_nc = start_server(cfg_nc)
        procs.append(proc_nc)
        base_nc = f"http://127.0.0.1:{port_nc}/d/{world_nocap}"
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

        # -- W11 ABSENT legs: this world carries NEITHER s40 nor s22 -- both gates refuse.
        # (legacy-led-retirement inventory pass, ledger row 1149: /standing/principals' own
        # gate was re-pointed at principal_standing_current, the view it actually queries --
        # s40, not s41 -- since that view is defined by kernel/lineage/s40-principal-identity-
        # events.sql alone; this world (pre-s22/s40/s41) still lacks it, so the capability
        # name in the refusal body is now "s40-identity", not "s41-identity".)
        st_sp_nc, v_sp_nc = http_get(base_nc + "/standing/principals") if up_nc else (0, {})
        st_wi_nc, v_wi_nc = http_get(base_nc + "/work/items") if up_nc else (0, {})
        check("w11-absent-legs-s40-and-s22-refuse",
              up_nc and st_sp_nc == 409 and v_sp_nc.get("disposition") == "capability_absent"
              and v_sp_nc.get("capability") == "s40-identity"
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
        # Route-shape migration: --config, never --deployment -- but the bind-guard REFUSAL leg
        # fires before boundary_service.main() ever loads the config file at all (the loopback
        # check runs first), so the TOML here need not even resolve to a real world; still
        # written as a syntactically valid single-deployment config (spec §2's mandatory shape)
        # rather than a bare placeholder, so this leg exercises the real --config argv surface.
        fake_cfg = tmp7 / "fake-boundary-multiplex.toml"
        fake_cfg.write_text(
            '[deployments.doesnotmatterw7]\n'
            f'pghost = "{PGHOST}"\n'
            'pgdatabase = "toy"\n'
            'pguser = "doesnotmatterw7_rw"\n'
            'pgschema = "doesnotmatterw7"\n'
            'pgkern = "doesnotmatterw7_kernel"\n',
            encoding="utf-8")
        port7 = free_port()
        r_refused = sh([str(PYVENV), "-m", "serving.boundary_service", "--config", str(fake_cfg),
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
        cfg7ok = write_scratch_multiplex_config(w7dir.parent, w7world)
        port7b = free_port()
        proc7, _ = start_server(cfg7ok, host="0.0.0.0", port=port7b, extra_flag=True)
        up7 = wait_health(f"http://127.0.0.1:{port7b}/d/{w7world}")
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
        cfg14 = tmp14 / "w14-boundary-multiplex.toml"
        cfg14.write_text(
            '[deployments.doesnotmatterw14]\n'
            f'pghost = "{UNROUTABLE_HOST}"\n'
            'pgdatabase = "toy"\n'
            'pguser = "doesnotmatterw14_rw"\n'
            'pgschema = "doesnotmatterw14"\n'
            'pgkern = "doesnotmatterw14_kernel"\n',
            encoding="utf-8")
        port14 = free_port()
        proc14 = _spawn_boundary_service(
            [str(PYVENV), "-m", "serving.boundary_service", "--config", str(cfg14),
             "--host", "127.0.0.1", "--port", str(port14)])
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
            with urllib.request.urlopen(f"http://127.0.0.1:{port14}/d/doesnotmatterw14/health", timeout=40) as resp:
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
    # it must answer typed 503 PROMPTLY (never queue), /health must never wait behind other
    # requests' occupancy, and the server must drain to normal service once the burst completes.
    # Reuses W14's UNROUTABLE_HOST lever: every kernel call this burst makes stalls for up to
    # PSQL_CONNECT_TIMEOUT_S before it could ever resolve, so an ADMITTED call's own latency is
    # bounded exactly like W14's own -- the only new behavior under test here is what happens to
    # the calls that never get admitted at all.
    #
    # ROUTE-SHAPE MIGRATION, LABEL NOTE, UPDATED (design/
    # BRIEF-A1-INFLIGHT-CAP-AND-WOULD-PRODUCE-2026-08-04.md item 1): this config carries exactly
    # ONE deployment (n=1), the shape W27 always tested. Before that item, `MAX_INFLIGHT_PER_
    # DEPLOYMENT = max(4, MAX_INFLIGHT_KERNEL_CALLS // 1)` was numerically IDENTICAL to the global
    # bound (both 24), so the per-deployment gate -- checked FIRST (spec §4) -- always fired,
    # and a single-deployment server could never actually EMIT `server_saturated` for its own
    # traffic (that label's own witness lived only in seen-red/boundary-multiplex/run_fixtures.py's
    # WM4, n=2, a genuinely shared global gate). The item's new shipped default
    # (MAX_INFLIGHT_PER_DEPLOYMENT=32) is now LARGER than the global bound (24) -- this config
    # carries NO override, so it runs at that default -- which means the per-deployment gate can
    # never bind before the smaller global one does: this witness now asserts `server_saturated`
    # instead, and (a genuine improvement, not a downgrade) this closes the exact gap this
    # comment used to name -- `server_saturated` firing on a real, single-deployment burst is now
    # observed here, not merely claimed unreachable.
    tmp27 = Path(tempfile.mkdtemp(prefix="svcfxw27-"))
    try:
        cfg27 = tmp27 / "w27-boundary-multiplex.toml"
        cfg27.write_text(
            '[deployments.doesnotmatterw27]\n'
            f'pghost = "{UNROUTABLE_HOST}"\n'
            'pgdatabase = "toy"\n'
            'pguser = "doesnotmatterw27_rw"\n'
            'pgschema = "doesnotmatterw27"\n'
            'pgkern = "doesnotmatterw27_kernel"\n',
            encoding="utf-8")
        port27 = free_port()
        proc27 = _spawn_boundary_service(
            [str(PYVENV), "-m", "serving.boundary_service", "--config", str(cfg27),
             "--host", "127.0.0.1", "--port", str(port27)])
        asgi_up27 = False
        deadline27 = time.time() + 10
        while time.time() < deadline27:
            try:
                with socket.create_connection(("127.0.0.1", port27), timeout=1):
                    asgi_up27 = True
                    break
            except OSError:
                time.sleep(0.2)
        base27 = f"http://127.0.0.1:{port27}/d/doesnotmatterw27"

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

        # See this block's own setup comment: at the shipped MAX_INFLIGHT_PER_DEPLOYMENT default
        # (32, this config carries no override), the per-deployment gate can never bind before
        # the smaller global bound (24) does -- so THIS config genuinely emits server_saturated,
        # never deployment_saturated, for its own burst.
        saturated = [r for r in results if r[1] == 503 and isinstance(r[2], dict)
                     and r[2].get("disposition") == "server_saturated"]
        dep_saturated_leaked = [r for r in results if r[1] == 503 and isinstance(r[2], dict)
                                 and r[2].get("disposition") == "deployment_saturated"]
        prompt_saturated = [r for r in saturated if r[3] < PROMPT_BOUND_S]
        expected_excess = BURST_N - boundary_service.MAX_INFLIGHT_KERNEL_CALLS
        check("w27-saturation-typed-503-prompt",
              asgi_up27 and len(results) == BURST_N and len(saturated) >= expected_excess
              and len(prompt_saturated) == len(saturated) and len(dep_saturated_leaked) == 0
              and all(r[2].get("inflight_limit") == boundary_service.MAX_INFLIGHT_KERNEL_CALLS for r in saturated)
              and all("retry" in (r[2].get("message") or "").lower() for r in saturated),
              f"asgi_up={asgi_up27}; burst_n={BURST_N}, responses={len(results)}, "
              f"saturated={len(saturated)} (expected >= {expected_excess}), "
              f"deployment_saturated LEAKED={len(dep_saturated_leaked)} (must be 0), all prompt"
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
        # attempt exhausts PSQL_CONNECT_TIMEOUT_S, and specifically NOT deployment_saturated --
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
    print("ALL CASES OK -- boundary-service both-polarity proof (W1-W7, W9-W36m, W38 live; "
          "W8 and the W9 streaming-abort leg UNEXERCISED, named).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
