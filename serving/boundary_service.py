#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T07:44:41Z
#   last-change: 2026-07-18T08:37:24Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""boundary_service -- the FastAPI outer boundary Port into an autoharn-managed ledger
(design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md, the RATIFIED build basis; ledger rows 1471,
1481, 1518; orchlog.d/panel-single-boundary-direction.md; kernel/lineage/
s43-typed-verdict-write-boundary.sql; law/adr/0002, 0012 P2, 0016).

WHAT THIS SERVICE IS (spec §0). The kernel's OWN inner boundary -- s43's four SECURITY
DEFINER write functions plus the derived views -- remains the sole authority. This service is
the OUTER declared boundary: it translates and validates, refuses what it cannot honor, and
adds NO truth of its own (ADR-0012 P2, verbatim). Every byte it serves originates in a kernel
view; every byte it writes passes through an s43 boundary function (spec §9's closure
invariant). It never issues a raw INSERT/UPDATE/DELETE against any kernel-governed table --
grep this file for 'INSERT INTO'/'UPDATE '/'DELETE FROM' targeting a table (not a boundary
FUNCTION CALL) and find nothing; W3's witness proves it live on a pre-s43 world too.

TRANSPORT (a choice this spec left open -- FLAGGED as a spec defect in the build report; the
smallest honest resolution taken here): this repository's own filing/ modules (see
filing/record_reading.py's own docstring, point 1) deliberately use a `psql` SUBPROCESS
transport with `-v name=value` / `:'var'` injection-safe substitution, NOT a Python DB driver,
because "this repo has no psycopg dependency" and "the house style" is already established.
This service follows that same house convention rather than introducing a second transport
the project does not otherwise use for its ledger connections -- `led`/`judge`/every filing/
module all connect this same way. Every value interpolated into a SQL string below is either
(a) an integer FastAPI itself already type-validated (a non-integer path/query value is a
422 before this module sees it -- never hand-parsed here), or (b) a deployment-config
identifier (schema/kern/role) validated ONCE at process start against a strict identifier
regex (`_IDENT_RE` below) and refused loudly if it fails -- so no HTTP-controlled string ever
reaches a SQL string via concatenation. Payload BODIES cross as psql `-v payload=...` bind
values (`:'payload'::jsonb`), never spliced as text -- the same idiom kernel_write() in
bootstrap/templates/led.tmpl already uses.

CAPABILITY DETECTION (spec §3 GET /health note: "capability facts are DETECTED per request
start-up, never assumed"). Detection is OBJECT EXISTENCE (`to_regclass`), never a version
literal -- the same migrate-detect-drift discipline led.tmpl's own s43/s45 probes already use
(a world need not match this service's authoring commit exactly). No caching anywhere in this
module (spec §5): every request re-detects, re-reads, re-writes through the kernel fresh.

BIND GUARD (spec §2): refuse to bind any non-loopback address without
--i-understand-this-exposes-the-ledger, construction-time (before uvicorn ever binds a
socket) -- ADR-0002 rung 1, the strongest rung, because the anomaly never reaches a running
server. The spec's own words name '0.0.0.0'; this build refuses EVERY non-loopback host under
the same flag (127.0.0.1/localhost/::1 are the only unguarded binds) -- a specific LAN IP is
exactly as exposing as the wildcard address, and gating on the literal string '0.0.0.0' only
would leave that hazard in reach of the same work untouched (CLAUDE.md's engineering-
responsibility rule). FLAGGED as a deliberate broadening of the spec's literal text, in its
spirit.

NO META-ROUTES (spec A2.1): `docs_url`/`redoc_url`/`openapi_url` are all `None` below --
FastAPI's default `/docs`, `/redoc`, `/openapi.json`, `/docs/oauth2-redirect` are DISABLED, not
merely unenumerated. §9's closure statement's route claim was found false against the running
service (A2.1's HIGH finding: those meta-routes were live, unenumerated, and `/docs`/`/redoc`
pulled a third-party CDN asset) -- a ledger boundary needs no self-documentation surface with
an external dependency; §3/§4 + this file's own docstring + serving/README.md are the
documentation. The route witness (seen-red/boundary-service/run_fixtures.py's W12) asserts
against `app.routes` directly, in-process, never the OpenAPI schema's self-report (which is
now absent entirely and structurally could never have enumerated a meta-route anyway).

SIZE AXIS (spec A2.2): `MAX_WRITE_BODY_BYTES = 1_048_576` (1 MiB) is enforced at BOTH named
checkpoints on every `/write/*` route -- (a) the raw request body, before any JSON parsing
(`_read_bounded_body`: Content-Length when the client declared one, refused without ever
reading the body; the actual byte count otherwise, refused mid-stream, never buffered whole);
(b) the re-serialized payload, before the psql subprocess (a payload can pass checkpoint (a)
and still fail (b) -- e.g. non-ASCII content that `json.dumps`'s default `ensure_ascii=True`
escaping expands well past its raw UTF-8 byte count; the witness suite's W9 exercises exactly
this). Both checkpoints return the same typed `payload_too_large` shape (413).

INFRA FAILURE (spec A2.4): a psql infrastructure failure (unreachable world, connection
refusal, a nonzero exit that is not a kernel verdict) is the ONE thing `_query_json` raises
`RuntimeError` for (module docstring, `_query_json`) -- so a single `RuntimeError` exception
handler on the FastAPI app, not a per-route try/except, is the ONE home (ADR-0012 P1) for the
infra-failure -> HTTP 503 `infra_failure` translation. The full psql stderr stays server-side
(`_log_infra_failure`, stderr -- this project's own house channel for a loud, non-silent,
non-exposed diagnostic); the client sees a generic message only, never SQL/role/schema/stack.

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import is top-of-file.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

# Path setup, NOT lazy imports (both `sys.path.insert` calls execute at module import time,
# unconditionally, before either import below runs -- the gate that actually arbitrates this,
# gates/no_lazy_imports.py, passes on this file). Both inserts are needed regardless of HOW
# this module is invoked: `python3 -m serving.boundary_service` (spec §2's launch command)
# puts the REPO ROOT on sys.path[0], not serving/ itself, so the sibling import below
# (`boundary_models`, a top-level import for house-convention consistency with every other
# filing/ consumer, not a package-relative one) needs its own directory added explicitly.
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "filing"))
import deployment_record  # filing/deployment_record.py -- the ONE home for the deployment.json shape  # noqa: E402

from boundary_models import (  # noqa: E402
    CapabilityAbsent,
    CapabilityManifest,
    HealthResponse,
    InfraFailure,
    PayloadTooLarge,
)

# The four s43 boundary functions, named ONCE (ADR-0012 P1) -- the write-route table (spec §4)
# is built from this dict, never re-typed per route.
WRITE_SURFACES: dict[str, str] = {
    "ledger": "ledger_write",
    "review": "review_write",
    "registration": "registration_write",
    "obligation": "obligation_write",
}

# A deployment.json identifier (schema/kern/role) must look like a plain SQL identifier --
# refused at construction time otherwise (ADR-0002 rung 1); this is the one guard that lets
# every query below interpolate schema/kern/role as bare text safely.
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}

# A2.2's one named write-ingress bound (ADR-0012 P1: one home, not one literal per checkpoint),
# 1 MiB -- generous for any ledger payload, safely under the psql-argv wall (ARG_MAX) that the
# pre-hardening build crashed into on a ~3 MB payload. Enforced at BOTH `_read_bounded_body`
# (checkpoint a, raw body) and `make_write_route`'s handler (checkpoint b, re-serialized
# payload) -- see this module's docstring, "SIZE AXIS".
MAX_WRITE_BODY_BYTES = 1_048_576


class BoundaryConfig:
    """This deployment's resolved (db, host, schema, kern, role) plus the psql connection
    host -- kept distinct from the LEDGER's own `host` field on purpose: `deployment.json`'s
    `host` is the POSTGRES host (what `led`/`judge` already call `--host`), never this HTTP
    service's own bind address (spec §2's separate `--host`/`--port` argv)."""

    def __init__(self, record: deployment_record.DeploymentRecord) -> None:
        for field_name in ("schema", "kern", "role"):
            value = getattr(record, field_name)
            if not _IDENT_RE.match(value):
                raise SystemExit(
                    f"boundary_service: REFUSED at start-up -- deployment.json field "
                    f"'{field_name}'={value!r} is not a plain SQL identifier "
                    f"(pattern {_IDENT_RE.pattern}). A deployment record is operator-authored "
                    f"config, not HTTP input, but this service still refuses to interpolate an "
                    f"unvalidated identifier into SQL text (ADR-0002 rung 1, construction-time)."
                )
        self.record = record

    @property
    def pg_host(self) -> str:
        return self.record.host

    @property
    def db(self) -> str:
        return self.record.db

    @property
    def schema(self) -> str:
        return self.record.schema

    @property
    def kern(self) -> str:
        return self.record.kern

    @property
    def role(self) -> str:
        return self.record.role


def _psql(cfg: BoundaryConfig, script: str, extra_v: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run `script` against this deployment's postgres, as the granted role, with search_path
    set to (schema, kern) -- the ONE connection idiom every query/call in this module uses (the
    same pattern bootstrap/templates/led.tmpl's own kernel_write()/psql_tuples() helpers use).
    `extra_v` values cross as psql `-v` bind vars (never string-spliced)."""
    args = ["psql", "-h", cfg.pg_host, "-d", cfg.db, "-tAq", "-v", "ON_ERROR_STOP=1"]
    for k, v in (extra_v or {}).items():
        args += ["-v", f"{k}={v}"]
    args += ["-f", "/dev/stdin"]
    preamble = f"SET ROLE {cfg.role};\nSET search_path = {cfg.schema}, {cfg.kern};\n"
    return subprocess.run(args, input=preamble + script, capture_output=True, text=True)


def _query_json(cfg: BoundaryConfig, sql: str, extra_v: dict[str, str] | None = None) -> Any:
    """Run a SELECT of exactly one scalar column; parse and return it as a Python value.
    Raises RuntimeError (never silently returns None/empty for a REAL failure) on a nonzero
    psql exit -- an infrastructure failure at the DB layer is not this service's to interpret,
    only to surface loudly (ADR-0002). A ZERO-ROW or SQL-NULL result is NOT that failure: `psql
    -tAq` prints the empty string for a NULL scalar (never the text "null"), and a single-row
    subquery over a WHERE that matches nothing legitimately returns zero output rows -- both
    are the honest "no value" case every caller here already handles (row_by_id's 404;
    service_principal_name's absent-registration None), so both map to Python None rather than
    an error. Distinguishing "no value" from "the query itself broke" is exactly the
    returncode check above, not output-emptiness -- conflating them would turn a legitimate
    NULL into a manufactured 500 on every one of this service's read routes."""
    cp = _psql(cfg, sql, extra_v)
    if cp.returncode != 0:
        raise RuntimeError(f"psql query failed (exit {cp.returncode}): {cp.stderr.strip()[-2000:]}")
    lines = [ln for ln in cp.stdout.splitlines() if ln.strip()]
    if not lines:
        return None
    return json.loads(lines[-1])


def _regclass_exists(cfg: BoundaryConfig, qualified_name: str) -> bool:
    out = _query_json(cfg, f"SELECT to_jsonb(to_regclass('{qualified_name}') IS NOT NULL);")
    return bool(out)


def capability_manifest(cfg: BoundaryConfig) -> CapabilityManifest:
    """Live per-request detection (no caching, spec §5) -- object existence only, never a
    version literal (module docstring)."""
    s22 = _regclass_exists(cfg, f"{cfg.schema}.work_item_current")
    s41 = _regclass_exists(cfg, f"{cfg.schema}.principal_relations")
    credited = _regclass_exists(cfg, f"{cfg.schema}.credited_current")
    s43 = bool(_query_json(
        cfg,
        f"SELECT to_jsonb(EXISTS (SELECT 1 FROM pg_proc p JOIN pg_namespace n "
        f"ON n.oid = p.pronamespace WHERE n.nspname = '{cfg.kern}' "
        f"AND p.proname = 'ledger_write' AND p.prosecdef));",
    ))
    return CapabilityManifest(s22_work=s22, s41_identity=s41, s43_boundary=s43, credited_view=credited)


def service_principal_name(cfg: BoundaryConfig) -> str | None:
    """A2.3: guarded with the SAME existence check every other capability fact uses
    (`_regclass_exists`, object existence never a version literal) -- on a world whose
    `kernel.principal` table itself is absent, this degrades to `None` exactly like every
    other capability-absent case, rather than reaching the query at all. `_query_json` already
    maps a legitimate zero-row/NULL result to `None` (see its own docstring); this guard covers
    the STRUCTURALLY absent case that same mapping cannot reach (a query against a table that
    does not exist is a psql error, not a NULL scalar)."""
    if not _regclass_exists(cfg, f"{cfg.kern}.principal"):
        return None
    out = _query_json(
        cfg,
        f"SELECT to_jsonb((SELECT name FROM {cfg.kern}.principal "
        f"WHERE name = 'boundary-service' AND agent_class = 'tool'));",
    )
    return out


def capability_absent(capability: str, message: str) -> JSONResponse:
    body = CapabilityAbsent(capability=capability, message=message)
    return JSONResponse(status_code=409, content=body.model_dump())


def payload_too_large(observed_bytes: int, message: str) -> JSONResponse:
    """A2.2: the one typed shape both write-ingress size checkpoints return (ADR-0012 P1)."""
    body = PayloadTooLarge(limit_bytes=MAX_WRITE_BODY_BYTES, observed_bytes=observed_bytes, message=message)
    return JSONResponse(status_code=413, content=body.model_dump())


def infra_failure(message: str) -> JSONResponse:
    """A2.4: the one typed shape a psql infrastructure failure returns."""
    body = InfraFailure(message=message)
    return JSONResponse(status_code=503, content=body.model_dump())


def _log_infra_failure(context: str, exc: Exception) -> None:
    """The full, loud, un-redacted detail stays server-side (stderr -- this project's own house
    channel for a loud diagnostic every other construction-time refusal in this file already
    uses) -- never in the HTTP response (A2.4's exposure posture)."""
    sys.stderr.write(f"boundary_service: INFRA FAILURE ({context}): {exc}\n")


class _BodyTooLarge(Exception):
    """Raised by `_read_bounded_body` (checkpoint a) -- caught once, at each write route, and
    turned into the typed `payload_too_large` response."""

    def __init__(self, observed_bytes: int, message: str) -> None:
        super().__init__(message)
        self.observed_bytes = observed_bytes
        self.message = message


async def _read_bounded_body(request: Request) -> bytes:
    """A2.2 checkpoint (a): MAX_WRITE_BODY_BYTES enforced on the RAW request body, BEFORE any
    JSON parsing. Two sub-cases, both named in the spec: a Content-Length header, when the
    client sent one, is checked FIRST and refuses without ever reading the body (the 100 MB
    whole-body-buffered-then-parsed hazard A2.2 names, foreclosed before a single byte is
    read); a body with no (or a lying) Content-Length is bounded by reading it incrementally
    and aborting the instant the running total exceeds the bound -- never buffered whole first
    and measured after."""
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            declared = int(content_length)
        except ValueError:
            declared = None
        if declared is not None and declared > MAX_WRITE_BODY_BYTES:
            raise _BodyTooLarge(
                declared,
                f"the request's Content-Length ({declared} bytes) exceeds the "
                f"{MAX_WRITE_BODY_BYTES}-byte write bound (checkpoint a, before JSON parsing) "
                f"-- refused before reading the body.")
    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > MAX_WRITE_BODY_BYTES:
            raise _BodyTooLarge(
                total,
                f"the request body exceeds the {MAX_WRITE_BODY_BYTES}-byte write bound "
                f"(checkpoint a, before JSON parsing) -- refused mid-read, never buffered "
                f"whole first.")
        chunks.append(chunk)
    return b"".join(chunks)


def create_app(cfg: BoundaryConfig) -> FastAPI:
    app = FastAPI(
        title="autoharn ledger boundary service",
        description="The outer declared Port into an autoharn-managed ledger "
                     "(design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md). Reads serve kernel "
                     "views verbatim; writes pass through the s43 boundary functions and "
                     "return the kernel's own write_verdict verbatim.",
        # A2.1: no self-documentation surface, disabled not merely unenumerated -- see this
        # module's docstring, "NO META-ROUTES". §9's route table is EXACTLY §3+§4's endpoints.
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    @app.exception_handler(RuntimeError)
    async def _infra_failure_handler(request: Request, exc: RuntimeError) -> JSONResponse:
        # A2.4: the ONE place a psql infrastructure failure (unreachable world, connection
        # refusal, a nonzero exit that is not a kernel verdict -- the ONLY thing _query_json
        # raises RuntimeError for) becomes a typed 503, for every route uniformly (ADR-0012
        # P1: one handler, not a try/except duplicated per route).
        _log_infra_failure(f"{request.method} {request.url.path}", exc)
        return infra_failure(
            "the ledger's underlying database connection failed -- this is an infrastructure "
            "problem, not a problem with your request; see the server's own log for full detail.")

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            world=cfg.schema,
            service_principal=service_principal_name(cfg),
            capabilities=capability_manifest(cfg),
        )

    @app.get("/rows/current")
    def rows_current(after_id: int = 0, limit: int = 100) -> Response:
        if limit < 1 or limit > 1000:
            return JSONResponse(status_code=422, content={
                "detail": "limit must be between 1 and 1000 (transport-level bound, ADR-0002)"})
        if after_id < 0:
            return JSONResponse(status_code=422, content={
                "detail": "after_id must be >= 0 (transport-level bound, spec §3/A2.6)"})
        rows = _query_json(
            cfg,
            f"SELECT coalesce(jsonb_agg(t ORDER BY t.id), '[]'::jsonb) FROM "
            f"(SELECT * FROM {cfg.schema}.ledger_current WHERE id > {after_id} "
            f"ORDER BY id LIMIT {limit}) t;",
        )
        return JSONResponse(content=rows)

    @app.get("/rows/{row_id}")
    def row_by_id(row_id: int) -> Response:
        row = _query_json(
            cfg, f"SELECT to_jsonb(t) FROM (SELECT * FROM {cfg.schema}.ledger WHERE id = {row_id}) t;")
        if row is None:
            return JSONResponse(status_code=404, content={"detail": f"no row {row_id}"})
        return JSONResponse(content=row)

    @app.get("/rows/{row_id}/history")
    def row_history(row_id: int) -> Response:
        # The full supersession chain both directions (predecessors this row's lineage
        # superseded, and any successor that superseded it), each hop annotated with its own
        # superseding row id -- spec §3's "each hop WITH its superseding row id".
        rows = _query_json(
            cfg,
            f"WITH RECURSIVE chain(id) AS ("
            f"  SELECT {row_id}::bigint"
            f"  UNION"
            f"  SELECT l.id FROM {cfg.schema}.ledger l JOIN chain c ON l.id = c.id"
            f"),"
            f"chain_up AS ("
            f"  SELECT id FROM chain"
            f"  UNION"
            f"  SELECT l.supersedes FROM {cfg.schema}.ledger l JOIN chain_up c ON l.id = c.id "
            f"    WHERE l.supersedes IS NOT NULL"
            f"),"
            f"chain_full(id) AS ("
            f"  SELECT id FROM chain_up"
            f"  UNION"
            f"  SELECT l.id FROM {cfg.schema}.ledger l JOIN chain_full c "
            f"    ON l.supersedes = c.id"
            f")"
            f"SELECT coalesce(jsonb_agg(to_jsonb(l) || jsonb_build_object("
            f"  'superseded_by', (SELECT s.id FROM {cfg.schema}.ledger s "
            f"                    WHERE s.supersedes = l.id)) ORDER BY l.id), '[]'::jsonb) "
            f"FROM {cfg.schema}.ledger l WHERE l.id IN (SELECT id FROM chain_full);",
        )
        return JSONResponse(content=rows)

    @app.get("/credited")
    def credited(after_id: int = 0, limit: int = 100) -> Response:
        if not _regclass_exists(cfg, f"{cfg.schema}.credited_current"):
            return capability_absent(
                "s44-credited-view",
                "This world carries no credited_current view (kernel/lineage/s44, unbuilt as "
                "of this service's authoring -- design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md "
                "§7). The service refuses to fall back to ledger_current for this endpoint "
                "(that would be the vacuous-pass F49 class, silently serving a weaker "
                "reading under the credited-only contract's name); use GET /rows/current "
                "until this world's kernel gains the view.")
        if limit < 1 or limit > 1000:
            return JSONResponse(status_code=422, content={"detail": "limit must be between 1 and 1000"})
        if after_id < 0:
            return JSONResponse(status_code=422, content={
                "detail": "after_id must be >= 0 (transport-level bound, spec §3/A2.6)"})
        rows = _query_json(
            cfg,
            f"SELECT coalesce(jsonb_agg(t ORDER BY t.id), '[]'::jsonb) FROM "
            f"(SELECT * FROM {cfg.schema}.credited_current WHERE id > {after_id} "
            f"ORDER BY id LIMIT {limit}) t;",
        )
        return JSONResponse(content=rows)

    @app.get("/standing/principals")
    def standing_principals() -> Response:
        if not _regclass_exists(cfg, f"{cfg.schema}.principal_relations"):
            return capability_absent(
                "s41-identity",
                "This world carries no principal-identity/relation views "
                "(kernel/lineage/s41-principal-bindings-and-relations.sql) -- "
                "GET /standing/principals is refused rather than served from a view this "
                "world's kernel does not have.")
        rows = _query_json(
            cfg,
            f"SELECT coalesce(jsonb_agg(t), '[]'::jsonb) FROM "
            f"(SELECT * FROM {cfg.schema}.principal_standing_current) t;",
        )
        return JSONResponse(content=rows)

    @app.get("/work/items")
    def work_items() -> Response:
        if not _regclass_exists(cfg, f"{cfg.schema}.work_item_current"):
            return capability_absent(
                "s22-work",
                "This world carries no work-item views (kernel/lineage/s22-work-item-ledger"
                ".sql) -- GET /work/items is refused rather than served from a view this "
                "world's kernel does not have.")
        rows = _query_json(
            cfg,
            f"SELECT coalesce(jsonb_agg(t), '[]'::jsonb) FROM "
            f"(SELECT * FROM {cfg.schema}.work_item_current) t;",
        )
        return JSONResponse(content=rows)

    def make_write_route(surface: str, fn: str):
        async def handler(request: Request) -> Response:
            if not bool(_query_json(
                cfg,
                f"SELECT to_jsonb(EXISTS (SELECT 1 FROM pg_proc p JOIN pg_namespace n "
                f"ON n.oid = p.pronamespace WHERE n.nspname = '{cfg.kern}' "
                f"AND p.proname = '{fn}' AND p.prosecdef));",
            )):
                return capability_absent(
                    "s43-boundary",
                    f"This world carries no s43 write boundary (kernel.{fn} absent) -- "
                    f"POST /write/{surface} refuses entirely rather than falling back to a "
                    f"raw INSERT (design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md §4: 'the "
                    f"service NEVER falls back to raw INSERT; there is no code path that "
                    f"writes SQL DML').")

            # A2.2 checkpoint (a): the raw body, bounded BEFORE any JSON parsing.
            try:
                raw_body = await _read_bounded_body(request)
            except _BodyTooLarge as e:
                return payload_too_large(e.observed_bytes, e.message)

            try:
                payload = json.loads(raw_body) if raw_body else None
            except json.JSONDecodeError as e:
                return JSONResponse(status_code=422, content={"detail": f"malformed JSON body: {e}"})
            if not isinstance(payload, dict):
                return JSONResponse(status_code=422, content={
                    "detail": "write payload must be a JSON object (transport-level shape check, spec §4)"})

            # A2.2 checkpoint (b): the re-serialized payload, bounded BEFORE the psql
            # subprocess -- a payload can pass checkpoint (a) and still fail here (non-ASCII
            # content that json.dumps's default ensure_ascii=True escaping expands past its
            # raw UTF-8 byte count; W9 exercises exactly this).
            payload_json = json.dumps(payload)
            observed = len(payload_json.encode("utf-8"))
            if observed > MAX_WRITE_BODY_BYTES:
                return payload_too_large(
                    observed,
                    f"the JSON payload, re-serialized, is {observed} bytes -- exceeds the "
                    f"{MAX_WRITE_BODY_BYTES}-byte write bound (checkpoint b, before the psql "
                    f"subprocess).")

            verdict = _query_json(
                cfg,
                f"SELECT to_jsonb(v) FROM {cfg.kern}.{fn}(:'payload'::jsonb) v;",
                extra_v={"payload": payload_json},
            )
            # Kernel verdicts (accepted AND refused) cross byte-verbatim as HTTP 200 -- a
            # kernel refusal is a first-class domain RESULT, not a transport error (spec §4).
            return JSONResponse(status_code=200, content=verdict)
        handler.__name__ = f"write_{surface}"
        return handler

    for surface, fn in WRITE_SURFACES.items():
        app.add_api_route(f"/write/{surface}", make_write_route(surface, fn), methods=["POST"])

    return app


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python3 -m serving.boundary_service",
        description="The FastAPI outer boundary into an autoharn-managed ledger "
                     "(design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md).")
    p.add_argument("--deployment", required=True,
                    help="path to this project's deployment.json (the SAME record led/judge read)")
    p.add_argument("--host", default="127.0.0.1",
                    help="bind address for THIS HTTP service (default 127.0.0.1, loopback-only)")
    p.add_argument("--port", type=int, default=8420)
    p.add_argument("--i-understand-this-exposes-the-ledger", action="store_true",
                    help="required to bind any non-loopback address -- the ledger carries "
                         "operator-real content (spec §2, the OTel-collector localhost-only posture)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    if args.host not in _LOOPBACK_HOSTS and not args.i_understand_this_exposes_the_ledger:
        sys.stderr.write(
            f"boundary_service: REFUSED -- --host {args.host!r} is not a loopback address "
            f"({sorted(_LOOPBACK_HOSTS)}). The ledger carries operator-real content; binding "
            f"it to a non-loopback interface is refused unless you pass "
            f"--i-understand-this-exposes-the-ledger explicitly (design/"
            f"FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md §2; construction-time refusal, ADR-0002 "
            f"rung 1 -- the anomaly never reaches a bound socket).\n")
        return 2
    record = deployment_record.load_deployment(args.deployment)
    cfg = BoundaryConfig(record)
    app = create_app(cfg)
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
