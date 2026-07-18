#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T07:43:25Z
#   last-change: 2026-07-18T10:03:32Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

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
    """A2.2's one named write-ingress bound (`MAX_WRITE_BODY_BYTES = 1_048_576`), enforced at
    BOTH checkpoints named in the spec: (a) the raw request body, before any JSON parsing; (b)
    the re-serialized payload, before the psql subprocess. Either checkpoint returns this same
    shape -- one bound, one refusal shape, not one per checkpoint (ADR-0012 P1)."""

    disposition: str = "payload_too_large"
    limit_bytes: int = Field(description="MAX_WRITE_BODY_BYTES -- the one named bound")
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
