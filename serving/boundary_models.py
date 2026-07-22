#!/usr/bin/env python3
"""boundary_models -- pydantic request/response shapes for serving/boundary_service.py
(design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md §2, §4).

DELIBERATELY THIN (the spec's §5 "no truth of its own" discipline, applied to typing too): a
model here validates JSON WELL-FORMEDNESS and top-level SHAPE only -- never ledger semantics.
The kernel is the one validator of semantics (jsonb_populate_record against the real rowtype,
inside the s43 boundary functions); a second, richer model here that tried to pre-validate
column names or value types would be exactly the "second validator that could disagree with
the authority" the spec's §4 forbids. So:

  - Write payloads (`WritePayload`) are `dict[str, Any]` -- a non-JSON or non-object body is
    refused as a transport-level 422 (ADR-0002 loud), and nothing past that is interpreted
    here. As of A2.2 the write routes read and bound the raw body THEMSELVES (via the
    `_bounded_raw_body` FastAPI dependency, an async wrapper around `_read_bounded_body` -- not
    an automatic pydantic body parameter) so the 1 MiB size checkpoint runs before the JSON
    decode ever sees an oversized body; as of A3.2 the decode+parse itself is also explicit
    (`json.loads`, wrapped in `except (ValueError, RecursionError)`) so invalid UTF-8, an
    oversized integer literal, and deep nesting are each a typed 422 naming the failed axis,
    never a bare 500 -- see `serving/boundary_service.py`'s `_classify_parse_failure`.
    `WritePayload` still names the post-decode shape every write handler works with; it is just
    no longer wired in as a route parameter annotation.
  - Read/verdict RESPONSES are mostly NOT modeled at all -- they are the kernel's own JSON
    (row records, `write_verdict`), returned via `fastapi.responses.JSONResponse` so no second
    encoding pass can silently reshape or drop a field the kernel actually returned. The models
    below (`HealthResponse`, `CapabilityAbsent`, `PayloadTooLarge`, `InfraFailure`) describe
    SERVICE-OWNED facts (what the service itself detected, what it itself refused) -- never
    kernel-row content.

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import is top-of-file.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# A write payload is any JSON object -- the kernel boundary functions (kernel.ledger_write et
# al.) are the ONLY validators of its keys/values (s43 §4.2). The write route's own explicit
# decode+parse (serving/boundary_service.py's `_classify_parse_failure`, A3.2) refuses a
# non-JSON or non-object body as a typed 422 before this type is even consulted; this alias
# exists so every write route names its contract the same way (ADR-0012 P1), not so it can grow
# a second check later without a very deliberate reason.
WritePayload = dict[str, Any]


class CapabilityManifest(BaseModel):
    """Which lineage capabilities THIS world was detected to carry, at THIS request (spec §3
    GET /health: "capability facts are DETECTED per request start-up, never assumed" -- no
    caching, matching §5's no-caching discipline applied to capability facts too). Detection is
    OBJECT EXISTENCE (to_regclass), never a version-number literal -- the same
    migrate-detect-drift discipline `bootstrap/templates/led.tmpl`'s own s43/s45 capability
    probes already use, so a world need not match this service's authoring commit exactly."""

    s22_work: bool = Field(description="work-item views present (kernel/lineage/s22-work-item-ledger.sql): work_item_current")
    s41_identity: bool = Field(description="principal identity/relation views present (kernel/lineage/s41-principal-bindings-and-relations.sql): principal_relations")
    s43_boundary: bool = Field(description="the four SECURITY DEFINER write-verdict functions present (kernel/lineage/s43-typed-verdict-write-boundary.sql): kernel.ledger_write")
    credited_view: bool = Field(description="the s44 credited-reading view present (unbuilt as of this service's authoring -- spec §7): credited_current")


class HealthResponse(BaseModel):
    world: str = Field(description="this deployment's world/schema name")
    service_principal: str | None = Field(description="the registered `tool`-class principal this service writes as, when the operator has completed the s40 registration step (README); null if not yet registered -- named, not hidden")
    capabilities: CapabilityManifest


class CapabilityAbsent(BaseModel):
    """The one typed shape EVERY capability-gated refusal in this service returns (spec §3's
    `/credited` refusal, generalized to every other capability gate the service holds,
    including the write surface on a pre-s43 world -- ADR-0012 P1, one refusal shape, not one
    per gate). Mirrors the kernel's own `write_verdict.disposition` vocabulary on purpose --
    'capability_absent' sits beside 'accepted'/'refused' as a third, SERVICE-level disposition
    that never claims to be a kernel verdict (there was no kernel call to verdict)."""

    disposition: str = "capability_absent"
    capability: str = Field(description="the missing lineage capability's name, e.g. 's43-boundary', 's44-credited-view'")
    message: str = Field(description="teach-text: what is missing and why the service refuses to fall back")


class PayloadTooLarge(BaseModel):
    """A2.2's write-ingress size refusal, RE-DENOMINATED per A8: TWO named bounds, one per
    checkpoint, because the checkpoints guard two different walls -- (a) the raw request body,
    before any JSON parsing, bounded by `MAX_WRITE_BODY_BYTES = 1_048_576` (rationale:
    BUFFERING -- never hold an unbounded body in memory); (b) the re-serialized payload,
    before the psql subprocess, bounded by `MAX_PSQL_ARG_BYTES = 100_000` (rationale:
    TRANSPORT -- the payload crosses as ONE psql `-v` argument, and Linux's per-argument
    wall is `MAX_ARG_STRLEN` = 131 072 bytes, not the total-argv `ARG_MAX` the pre-A8 bound
    was sized against). Either checkpoint returns this SAME shape (one refusal shape, not one
    per checkpoint -- ADR-0012 P1), with `limit_bytes` honest about which bound fired."""

    disposition: str = "payload_too_large"
    limit_bytes: int = Field(description="the bound the refusing checkpoint enforces -- MAX_WRITE_BODY_BYTES (checkpoint a, raw body/buffering) or MAX_PSQL_ARG_BYTES (checkpoint b, re-serialized payload/transport), per A8")
    observed_bytes: int = Field(description="the size actually observed at the checkpoint that refused")
    message: str = Field(description="teach-text: which checkpoint refused, the bound, and why")


class InfraFailure(BaseModel):
    """A2.4, extended per A3.1/A3.2, NARROWED per A4.3: a psql infra failure -- unreachable
    world, connection refusal (psql exit 2), OR a `PSQL_EXEC_TIMEOUT_S` stall (a peer that
    accepts the connection and then goes silent; A3.1's "a stall IS infra") -- is typed rather
    than a bare 500. As of A3.2 this shape is raised ONLY by the service's dedicated
    `PsqlInfraFailure` exception (never a bare `RuntimeError`, which a foreign failure like
    `RecursionError` could also raise), so no unrelated exception can wear this signature by
    accident. As of A4.3, `PsqlInfraFailure` itself is narrowed further: a psql exit 3 (or any
    other nonzero residue) is NOT connection-level and is no longer classified here -- see
    `UnclassifiedFailure` below. The message here is DELIBERATELY generic (no SQL, role, schema,
    or stack); the full loud detail stays server-side in the log (ADR-0002 rung 3 loudness
    retained, exposure posture unchanged)."""

    disposition: str = "infra_failure"
    message: str = Field(description="generic teach-text; see the server's own log for the full detail")


class UnclassifiedFailure(BaseModel):
    """A4.3: a psql exit that is NEITHER exit 2 (connection-level, `InfraFailure` above) NOR a
    kernel verdict -- concretely, psql exit 3 (a script/data-level failure under
    `ON_ERROR_STOP=1`) or any other unrecognized nonzero residue. After A4.1/A4.2 close the
    value-closure and id-domain classes, this path is unreachable via an ordinary caller-
    supplied request; its occurrence names a boundary or deployment defect, not a request
    defect -- so the message says exactly that, honestly, rather than asserting a cause (SQL/
    role/schema/stack) this boundary did not witness. Raised ONLY by the service's dedicated
    `PsqlUnclassifiedFailure` exception -- the A4.3 sibling of `PsqlInfraFailure`'s own
    narrowing, so neither typed shape can claim a cause it cannot witness."""

    disposition: str = "unclassified_failure"
    message: str = Field(description="honest teach-text: the storage layer refused for a reason "
                                      "this boundary did not anticipate; full detail is logged "
                                      "server-side only; see the server's own log")


class BodyReadTimeout(BaseModel):
    """A5.3: the raw-body READ phase's own bound -- `BODY_READ_TIMEOUT_S = 30`, distinct from
    A3.1's psql-phase bounds (`PSQL_CONNECT_TIMEOUT_S`/`PSQL_EXEC_TIMEOUT_S`). Before this
    existed, a trickled body (a client sending a declared-length body a few bytes at a time)
    held the request open indefinitely -- 48s witnessed in A5's own review, `/health` on other
    connections unaffected (per-request only, not a server-wide wedge). Symmetric with A2.2's
    two named size checkpoints: the time axis now names both legs (read phase, psql phase)."""

    disposition: str = "body_read_timeout"
    timeout_s: float = Field(description="BODY_READ_TIMEOUT_S -- the one named bound")
    message: str = Field(description="teach-text: the body-read phase stalled past this bound")


class ServerSaturated(BaseModel):
    """A9: `MAX_INFLIGHT_KERNEL_CALLS` concurrent kernel calls are already in flight -- this
    service's own named admission bound, deliberately under the ASGI threadpool's own default
    concurrency so `/health` and every other route are never starved by kernel-call occupancy
    alone (the concurrency axis A3.1's own single-stalled-call test never reached: N concurrent
    stalled requests, unbounded, made wall-clock on EVERY route grow without limit). Every
    kernel-call site -- reads, writes, and `/health`'s own kernel probes alike -- shares ONE
    admission gate (`serving/boundary_service.py`'s `_KERNEL_CALL_SEMAPHORE`, tested inside
    `_psql`, the one choke point every kernel call already passes through); saturation refuses
    IMMEDIATELY, never queues -- this shape is the caller-visible result, distinct from
    `InfraFailure` (this is ordinary load, not a connection-level anomaly)."""

    disposition: str = "server_saturated"
    inflight_limit: int = Field(description="MAX_INFLIGHT_KERNEL_CALLS -- the named admission bound this call was refused against")
    message: str = Field(description="teach-text: names the bound, the cause (concurrent kernel calls at capacity), and that retry-with-backoff is the correct caller response")


class UnknownDeployment(BaseModel):
    """design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md §2: the `{deployment}` path
    segment on every route is valid iff it is a key of the loaded multiplex config -- a closed
    enumeration fixed at startup (ledger decision row 1631: TOML config, mandatory `/d/{name}`
    discriminator even for one deployment). Anything else refuses this ONE typed 404 shape,
    naming the full known set so the caller can self-correct without a second round trip."""

    disposition: str = "unknown_deployment"
    known: list[str] = Field(description="every deployment name this service is configured to serve")
    message: str = Field(description="teach-text naming the unknown segment and the known set")


class DeploymentSaturated(BaseModel):
    """spec §4: `MAX_INFLIGHT_KERNEL_CALLS` stays the GLOBAL admission bound (it protects the
    shared threadpool, process-wide) and gains a per-deployment sub-bound,
    `MAX_INFLIGHT_PER_DEPLOYMENT`, so one deployment's stalled kernel cannot occupy the whole
    global bound and starve its siblings. This shape is DISTINCT from `ServerSaturated` above
    (spec §4/A6/A8's label-honesty ruling: one condition, one label -- a caller refused because
    ITS OWN deployment's sub-bound is exhausted must never see the same label a caller refused
    because the WHOLE SERVER's global bound is exhausted would see, and vice versa)."""

    disposition: str = "deployment_saturated"
    deployment: str = Field(description="the deployment name this call was refused against")
    inflight_limit: int = Field(description="MAX_INFLIGHT_PER_DEPLOYMENT -- this deployment's own sub-bound")
    message: str = Field(description="teach-text: names the bound, the deployment, the cause, and that retry-with-backoff is the correct caller response")


class UnknownView(BaseModel):
    """design/FABLE-BOUNDARY-READ-SURFACE-SPEC.md (amendment to the multiplex/CLI-rebase spec,
    ratified ledger decision row 1652): `GET /d/{deployment}/views/{view}`'s `{view}` path
    segment is valid iff it is a key of `boundary_service.py`'s closed, spec-enumerated
    `VIEW_REGISTRY` -- a second closed enumeration, mirroring `UnknownDeployment` above exactly
    (ADR-0012 P1: the SAME shape, applied to a second discriminator). Anything else refuses this
    typed 404, naming the full known set so a caller can self-correct without a second round
    trip; nothing is queried for an unknown view name."""

    disposition: str = "unknown_view"
    known: list[str] = Field(description="every view name this service's VIEW_REGISTRY serves")
    message: str = Field(description="teach-text naming the unknown view and the known set")


class MetaResponse(BaseModel):
    """design/FABLE-BOUNDARY-READ-SURFACE-SPEC.md's third new route, `GET /d/{deployment}/meta`
    -- the capability surface a rebased CLI shim decides its own behavior from, replacing the
    shims' former direct `pg_proc`/`information_schema` probes (the amendment's own words: "a
    verb decides behavior from the boundary's declared capabilities, not from database
    introspection it no longer has credentials for"). Three facts, no more (v1 scope, per the
    amendment's own three-item mechanism list) -- this is deliberately NOT a superset of
    `HealthResponse`'s `CapabilityManifest` (that shape stays `/health`'s own; `/meta` answers a
    different question, "what can a served-read verb ask for", not "is this world alive")."""

    known_views: list[str] = Field(description="VIEW_REGISTRY's full key set, sorted -- identical to what a GET /views/{view} 404 would report")
    lineage_head: str | None = Field(description="the highest kernel/lineage/*.sql manifest entry (basename, minus .sql) this deployment's own .detect.sql siblings confirm applied, walked in the SAME order bootstrap/migrate_core.py's own `_current_head_and_missing` uses -- null if even the first manifest entry's detect fails (a pre-birth-chain world, or a manifest/detect defect)")
    boundary_version: str = Field(description="this boundary_service.py build's own declared version string -- a service-owned fact, never a kernel fact")


class LedgerWriteIntFields(BaseModel):
    """A5.2's enumeration authority for `POST /write/ledger` (`kernel.ledger_write`): the
    bigint-typed `ledger` columns a payload MAY name (kernel/lineage/s15-schema.sql's
    `supersedes`/`actor`/`regards`/`amends`/`answers`/`enacts`, plus the bigint columns later
    lineage deltas append -- s37's `work_violation_target_id`/`work_violation_witness`, s40's
    `principal_subject`, s41's `principal_object`, s44's `attest_row_id`). NOT a second
    validator of payload KEY MEMBERSHIP (`kernel.ledger_write` itself is the sole authority on
    which keys a payload may carry, spec §4/§5) -- this model exists ONLY so
    `serving/boundary_service.py` has one declared home to enumerate "every integer-typed
    field the payload contract declares" and bound each one's VALUE, per field, if the caller
    supplied it. `enacts` is `bigint[]` (multi-target), so it is bounded element-wise."""

    supersedes: int | None = None
    actor: int | None = None
    regards: int | None = None
    amends: int | None = None
    answers: int | None = None
    enacts: list[int] | None = None
    principal_subject: int | None = None
    principal_object: int | None = None
    work_violation_target_id: int | None = None
    work_violation_witness: int | None = None
    attest_row_id: int | None = None


class ReviewWriteIntFields(BaseModel):
    """A5.2's enumeration authority for `POST /write/review` (`kernel.review_write`): its
    closed contract's bigint-typed keys (kernel/lineage/s43-typed-verdict-write-boundary.sql
    Element 3 -- `regards`, `actor`, `antecedent`; `statement`/`verdict`/`independence`/`basis`
    are text, out of this model's scope)."""

    regards: int | None = None
    actor: int | None = None
    antecedent: int | None = None


class RegistrationWriteIntFields(BaseModel):
    """A5.2's enumeration authority for `POST /write/registration`
    (`kernel.registration_write`): its closed contract's one bigint-typed key (`actor`);
    `name`/`agent_class`/`purpose`/`statement` are text, `event_declared_ts` is a timestamptz
    literal (text on the wire), out of this model's scope."""

    actor: int | None = None


class ObligationWriteIntFields(BaseModel):
    """A5.2's enumeration authority for `POST /write/obligation` (`kernel.obligation_write`):
    its closed contract's two bigint-typed keys (`assigned_by`, `obliges_actor`); `scope` is
    text, out of this model's scope."""

    assigned_by: int | None = None
    obliges_actor: int | None = None
