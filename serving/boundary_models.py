#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T07:43:25Z
#   last-change: 2026-07-18T07:43:25Z
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

  - Write payloads (`WritePayload`) are `dict[str, Any]` -- FastAPI/pydantic reject anything
    that is not a JSON object before the kernel is ever called (a transport-level 422,
    ADR-0002 loud), and nothing past that is interpreted here.
  - Read/verdict RESPONSES are mostly NOT modeled at all -- they are the kernel's own JSON
    (row records, `write_verdict`), returned via `fastapi.responses.JSONResponse` so no second
    encoding pass can silently reshape or drop a field the kernel actually returned. The few
    models below (`HealthResponse`, `CapabilityAbsent`) describe SERVICE-OWNED facts (what the
    service itself detected, what it itself refused) -- never kernel-row content.

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import is top-of-file.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# A write payload is any JSON object -- the kernel boundary functions (kernel.ledger_write et
# al.) are the ONLY validators of its keys/values (s43 §4.2). FastAPI's own body-decode already
# refuses non-JSON and non-object bodies as a 422 before this type is even consulted; this
# alias exists so every write route names its contract the same way (ADR-0012 P1), not so it
# can grow a second check later without a very deliberate reason.
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
