# Boundary read surface — closing the §5 route gap

<!-- doc-attest-exempt: build-basis spec; attestation rides witnessed delivery -->

**Status: Fable-authored 2026-07-18, amendment to
[design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md](FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md)
(ratified, ledger row 1631). AWAITING MAINTAINER RATIFICATION — this spec changes the
boundary service's ratified closed route enumeration ("exactly eleven routes and
nothing else"), which is precisely the kind of change the closure discipline exists
to make loud. The §5 CLI-rebase build is HELD until this is ratified or declined.**

## The witnessed gap (why §5 cannot build as written)

The §5 builder's seam stop (2026-07-18): §5 says read verbs become "pure clients of
the read routes," but the boundary's eleven routes cannot serve most of the CLI's
actual read surface. Unservable today, enumerated: `question_status`, `review_gap`,
`review_stamp_distinctness`, `standing_decisions`, `countersign_obligation` (+ its
`review_gap` join), `work_item_violations`, `work_review_gap`, the `asof-export`
as-of reconstruction query, `pickup`'s sectioned scans, and the capability probes the
verbs run before deciding behavior. Only ledger-row CRUD and the four writes map onto
the existing table. The alternatives to this spec are both rejected: extending routes
ad hoc violates the closure discipline; a partial rebase makes §5's "originals retire
to ./legacy/" claim false and silently strands most verbs on psql.

## Mechanism — three route shapes, not ten bespoke routes

The route table grows from eleven to FOURTEEN, and the closure statement is
re-ratified at fourteen ("and nothing else" stands, at the new count):

1. **`GET /d/{deployment}/views/{view}`** — the derived-read carrier. `{view}` is
   validated against a CLOSED, spec-enumerated allowlist (below), exactly the
   ADR-0012 interpreter-boundary shape: the view name is data checked against a
   closed alphabet, never spliced; an unknown name is a typed 404 `unknown_view`
   naming the known set (refuses, never guesses). Read-only, the existing pagination
   discipline, per-deployment admission gate unchanged. The v1 allowlist:
   `question_status`, `review_gap`, `review_stamp_distinctness`,
   `standing_decisions`, `countersign_obligation`, `work_item_violations`,
   `work_review_gap`, `model_attestations`, `model_defeated_rows`,
   `credited_current`, `work_item_current`. No server-side filter parameters in v1:
   shims filter client-side over paginated output (the views are the kernel's own
   derived reads; the boundary adds transport, not query language — a filter grammar
   would be a second query surface to close, deliberately not opened here).
2. **`GET /d/{deployment}/rows/asof/{ts}`** — the as-of reconstruction, `{ts}` a
   typed ISO-8601 timestamp (422 on malformed input, refused before any kernel
   call), serving `asof-export`'s reconstruction with the same pagination.
3. **`GET /d/{deployment}/meta`** — the capability surface: the served view
   allowlist, the deployment's kernel lineage head, and the boundary's own version.
   This replaces the shims' direct `pg_proc`/`information_schema` probes — a verb
   decides behavior from the boundary's declared capabilities, not from database
   introspection it no longer has credentials for.

Everything else in ratified §5 stands unchanged: same argv surfaces, byte-faithful
verdicts, boundary-vs-kernel refusals distinguishably typed, `./legacy/` holds the
direct-psql originals whole, `judge` and bootstrap scaffolding do not rebase.

## Witnesses (rides §5's build; both polarities)

- **WR1** every allowlisted view served: output row-set equal to the direct view
  query on the same scratch world (per view, not umbrella).
- **WR2** unknown view name → typed 404 naming the known set; nothing queried.
- **WR3** as-of at a mid-history timestamp: served reconstruction equals
  `asof-export read`'s direct output on the same world; malformed ts → 422 pre-kernel.
- **WR4** `/meta` matches reality: its view list equals the allowlist, its lineage
  head equals the scratch world's actual head.
- **WR5** admission discipline unchanged: the new routes saturate per-deployment
  exactly like the old ones (the WM4 method, one probe on a `/views/` route).

## The question for ratification, prepared

**Ratify fourteen routes as specified (recommended), or decline** — declining means
either §5 builds as a partial rebase with `./legacy/`'s meaning restated (the CRUD
slice rebases, the rest stays psql), or the CLI rebase is dropped and the boundary
stays a served-read/write surface only. A yes/no suffices; the allowlist's exact
membership is the only sub-question open to line-item edits.
