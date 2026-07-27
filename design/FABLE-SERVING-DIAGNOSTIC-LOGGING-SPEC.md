# FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC — a jq-queryable structured log for the boundary service

<!-- doc-attest-exempt: Fable-authored spec awaiting maintainer ratification 2026-07-27;
the A:B:C loop runs on the build, not the proposal text. Removal condition: superseded by
the build's merge record, or rejection. -->
<!-- design-currency: status=discharged discharged-by=f5d4934ace5cf4d980e50772c1a1360874579f60 -->

(Header corrected 2026-07-28, autoharn3 design-drift-triage sweep, ledger row 90: the
doc-attest-exempt marker's free prose above ("awaiting maintainer ratification") stood
stale against the machine-readable `design-currency` header immediately below it, which
already correctly reads `status=discharged` — `git merge-base --is-ancestor
f5d4934a... HEAD` confirms that sha is an ancestor, and its own commit message reads
"Merge serving diagnostic logging (f450019 + fix round b45eef0): all four ratified
layers; review CLEARS." The status line below is likewise already correct
("RATIFIED IN FULL"). Historical prose kept verbatim.)

- **Status:** RATIFIED IN FULL 2026-07-27 (maintainer, same day as proposal: "As per
  your recommendation, then" — all four layers; ledger row records it). The L3 floor was
  ratified separately and earlier (the maintainer, verbatim on ledger row 1496: *"I'll
  at least want the json debug log so that we can do structured resolution with jq (so
  this is the minimum floor, not a ceiling or scope)"*). The layer shapes resolve
  [design/LOGGING-DIRECTION-SURVEY-2026-07-27.md](LOGGING-DIRECTION-SURVEY-2026-07-27.md)
  §3, sharpened by the two witnesses below.
- **Basis:** ledger rows 1484/1486 (the survey commission and its due-diligence framing),
  1495 (the spec track), 1496 (the floor), 1498 (the two prerequisite witnesses, both
  WITNESSED on scratch 2026-07-27).
- **Standing line, restated because everything under it depends on it:** this layer is
  DIAGNOSTIC-grade, never evidentiary. No fact may live only in this log; anything a
  guarantee rests on goes through the kernel (the s43 refusal journal and its successors)
  into the ledger. The action stream and the ledger remain the evidentiary basis
  (maintainer principle 2026-07-11). This spec adds provenance breadcrumbs, not evidence.

## 1. What the witnesses settled (row 1498)

1. **The digest join is NOT byte-sound, by mechanism.** The kernel computes
   `refusal_payload_digest` over jsonb's canonical text (`p_payload::text` after the
   `::jsonb` cast — key order normalized), while the service serializes with
   `json.dumps(payload, allow_nan=False)` (`serving/boundary_service.py:1436`, insertion
   order, no `sort_keys`). All three witness cases UNEQUAL; the kernel's own s43 LIMIT
   comment (lines ~317-320) predicted exactly this. **Therefore: the log-to-ledger join
   anchors on `refusal_id` / verdict row id — values the kernel already returns to the
   service — never on digest equality.** The log MAY additionally record a
   `payload_sha256` over the service's own sent bytes, labeled as service-side and
   approximate; it is a grep handle, not a join key.
2. **contextvars propagate to plain-`def` handlers through `run_in_threadpool` — but
   only from async context.** Witnessed 20/20 correct under concurrency on the installed
   stack (Python 3.13.13, fastapi 0.139.2, starlette 1.3.1, uvicorn 0.51.0,
   anyio 4.14.1). The trap, witnessed as the negative control: a plain-`def`
   DEPENDENCY's contextvar writes are silently lost (each threadpool dispatch copies the
   context; mutations never flow back). **Therefore: L1 is ASYNC middleware (or an
   `async def` dependency, the pattern `_bounded_raw_body` already uses); a plain-`def`
   dependency for context-setting is refused at review, and the build's fixture
   witnesses the propagation live on the real app.**

## 2. The deliverable, by layer (survey §3.3, resolved)

**L1 — one per-request context object.** Async middleware mints `request_id` (short
random token), records route, method, deployment (once resolved), client address, and —
when row 1471's identity plumbing lands — the declared principal/session. Held in one
`contextvars.ContextVar`. This is deliberately the same object the identity work needs;
it is defined here ONCE and that build extends it rather than minting its own.

**L2 — a closed event vocabulary with per-event required fields.** Events (target ~8,
the build states the final set): `request_start`, `request_end` (status, duration_ms),
`kernel_call` (surface, psql exit class, duration_ms), `write_verdict`
(accepted|refused, ledger row id or `refusal_id`), `refusal` (the typed disposition),
`infra_failure`, `unclassified_failure`, `startup`. The refusal events are DERIVED from
the disposition enumeration the service already computes — one enumeration, so a future
disposition gets its event by construction. Emitting an unknown event or omitting a
required field raises a dedicated error whose message teaches (event, required set,
missing, provided — the proxy's `LogContractError` shape; ADR-0002 applied to the log's
own contract). Validation runs BEFORE any level filter (the proxy's witnessed
latent-crash lesson: validation whose result depends on the level filter is a trap).

**L3 — one rendering: JSON lines (THE RATIFIED FLOOR).** One object per line to the
service's existing captured output (ensure_running.py already redirects to
`<world>/service.log`; destination unchanged). Stable field names, ISO-8601 timestamps,
`request_id` on every record so `jq 'select(.request_id=="…")'` reconstructs a request.
The existing human stderr lines stay as-is beside it. No console/logfmt renderers — one
machine rendering, added-later is cheap, kept-honest-now is not.

**L4 — migrate the existing sites.** `_log_infra_failure`, `_log_unclassified_failure`,
and the startup banner become the first typed call sites, not a parallel stream. Their
server-side-only discipline (nothing client-visible, psql stderr capped) is unchanged.

**Config:** level (and nothing else initially) in the existing multiplex TOML, validated
whole-file before the socket binds, refusing unknown values loudly. No parallel env
namespace. Payload content never logged above the existing capped psql-stderr excerpts;
INFO carries structure, not bodies.

## 3. Class routing and non-scope

serving/ only — no kernel delta, no law/, no engine/lp. Strengthened-tier review
(serving/). Explicitly NOT closing the rows-1474/1476 attribution gap: that is row
1471's evidentiary identity plumbing, which this must not become an excuse to defer
(survey §3.1's two-work-items rule). Rotation, metrics, tracing: out of scope, as in
the survey.

## 4. Witness plan (scratch, both polarities)

RED: unknown event name raises the teaching error (witnessed text); missing required
field likewise; unknown level value in TOML refused before bind. GREEN: a served write
(accept and refuse legs) yields a jq-reconstructable record chain
(`request_start → kernel_call → write_verdict → request_end`) sharing one `request_id`,
with the refuse leg's `refusal_id` joining to the scratch world's journal row (the
witness performs the actual jq query and the actual join, output shown); contextvar
propagation witnessed on the real app under concurrent load; existing fixture bank
(seen-red/boundary-service) stays green including W33; no client-visible response byte
changes on any existing route (diff witnessed).

## 5. Closure statement

Quantification universe, per ADR-0000 Rule 2(a): the emission sites are exactly (a) the
L1 middleware (request_start/request_end), (b) `_psql`'s single chokepoint
(kernel_call), (c) the verdict/refusal classification paths already enumerated by the
disposition set in `boundary_service.py`, (d) the three existing L4 sites. The builder
enumerates them by grep in the build report and states any site found outside this set.
Not covered, stated honestly: anything that never reaches the service (CLI-local
failures, hook stderr) logs nothing here, before and after.

## License

Public Domain (The Unlicense).
