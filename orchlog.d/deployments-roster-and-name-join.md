subject: c47dd507
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

`GET /deployments` — the hub's own deployment roster (`declared`/`reachable`/`serving`,
[ADR-0008](../law/adr/0008-classification-discipline.md) honest: never an umbrella "healthy"),
live-probed per request. Deliberately the one route on
this service with no `/d/{deployment}` prefix, since it answers the prior question ("which
deployments exist") a per-deployment route cannot. WITNESSED live on this checkout:
`{"deployments":[{"name":"autoharn2","declared":true,"reachable":true,"serving":true}, ...],
"boundary_version":"1.8.0","protocol_version":"1"}` (4/4 configured deployments healthy).

An additive, opt-in `?annotate_names=true` flag on `/rows/current`, `/rows/{id}`,
`/rows/{id}/history`, `/rows/asof/{ts}`, `/work/items`, and `/views/{review_gap,
work_item_current}` adds a `{column}_name` sibling field resolved against `kernel.principal` —
typed absence (`null`, never an invented or empty-string name) for an unregistered/unclaimed
actor, default response byte-identical on every route. Any OTHER view given the flag is refused,
never silently ignored — WITNESSED: `GET /views/work_violation_history?annotate_names=true` ->
HTTP 422 `"annotate_names is not accepted on GET /views/work_violation_history -- only
['review_gap', 'work_item_current'] carry an actor-shaped column this route knows how to
annotate"`.

**What a restarting orchestrator needs to know — the
[ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md) exception, ratified and
closed.** This annotation join is the service's first SELF-AUTHORED SQL join — §5 of
[design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md](../design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md)
(the boundary spec) otherwise claims unconditionally that the service mints no truth of its own.
Adjudicated (spec amendment A14, 2026-08-06): RATIFIED as built (the join reads `kernel.principal.name`, truth the
service already serves elsewhere, joined beside an id it already serves — disclosure, not
fabrication), and CLOSED, not a precedent — any future self-authored join needs its own dated
amendment, adjudicated the same way. The A14-named checkability gap (no independent differential
covered the annotation path) is dispatched, not waived: `serving/audit_served.py` gained an
opt-in `--annotate-names-column` differential against a direct `kernel.principal` read.
