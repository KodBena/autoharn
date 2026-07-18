<!-- doc-attest-exempt: RATIFIED build basis authored 2026-07-18 under the Fable freeze plan (ledger row 1455 posture); the ADR-0017 fresh-context attestation is deferred until the Sonnet build lands and the content stabilizes against built reality (the same deferral, for the same reason, as the defeat-pipeline and standing-lifecycle bases). -->

# FABLE-LEDGER-BOUNDARY-SERVICE-SPEC — the FastAPI outer boundary: the one declared Port into an autoharn ledger

**Status:** RATIFIED BUILD BASIS — authorized by the maintainer's serving-boundary direction
(ledger row 1471, batch-ratified at row 1481) and his 2026-07-18 commission (ledger row 1518,
verbatim: *"implementation of the FastAPI as the only remaining sanctioned surface into the
ledger (expect for backwards-compatibility, \*deprecation-marked\* ADR-0002 compliant, with a
pointer to the Fable-commissioned context migration doc"*). Fable-authored under the freeze
plan; a **Sonnet builder** executes this document post-freeze. Nothing is applied by this
document's authoring.

**Primary inputs, read in full at authoring:** ledger rows 1471, 1481, 1518;
[orchlog.d/panel-single-boundary-direction.md](../orchlog.d/panel-single-boundary-direction.md);
[kernel/lineage/s43-typed-verdict-write-boundary.sql](../kernel/lineage/s43-typed-verdict-write-boundary.sql)
(the four boundary functions and `write_verdict`);
[design/FABLE-DEFEASIBILITY-ENVELOPE-2026-07-18.md](FABLE-DEFEASIBILITY-ENVELOPE-2026-07-18.md) §9;
[design/FABLE-DEFEAT-PIPELINE-SPEC.md](FABLE-DEFEAT-PIPELINE-SPEC.md) §9 (the SPA display
contract); [design/FABLE-WORLD-CONTEXT-MIGRATION-CONSULT-2026-07-19.md](FABLE-WORLD-CONTEXT-MIGRATION-CONSULT-2026-07-19.md)
(the deprecation-pointer target; its filename date is a recorded drift, correction row 1517);
[law/adr/0002-fail-loudly.md](../law/adr/0002-fail-loudly.md),
[law/adr/0012-compositional-and-structural-hygiene.md](../law/adr/0012-compositional-and-structural-hygiene.md) (P2),
[law/adr/0016-the-service-contract-is-an-enforcement-surface.md](../law/adr/0016-the-service-contract-is-an-enforcement-surface.md),
plus ADR-0000/0011/0013/0017 as standing law.

## 0. Executive summary

One FastAPI service — repo home `serving/` — becomes the **outer declared boundary** (ADR-0012
P2 Port) into an autoharn-managed ledger for every UI-class and programmatic consumer, the Vue
panel first. The kernel's **inner** boundary (s43's four SECURITY DEFINER write functions plus
the derived views) remains the sole authority; the service adds no truth of its own —
translate-and-validate, refuse what it cannot honor, never coerce. Writes pass through the
boundary functions and return the kernel's own typed `write_verdict` verbatim; refusals reach
the UI as first-class teach-text, never stack traces. Reads serve the kernel's derived views;
where a world carries a credited view, credited-only is the default and history-mode shows
defeated/superseded rows WITH CAUSE (the auditability wall — binding, not preference). Legacy
direct-psql consumer paths survive only deprecation-marked per ADR-0002: loud at invocation,
naming the replacement endpoint, pointing at the context-migration consult.

## 1. Scope — and the one commission sentence interpreted on the record

The commission's "only remaining sanctioned surface into the ledger" is fixed here, v1, as:
**all UI-class and new programmatic consumers**. The repo-root operator verbs (`led`, `judge`,
`pickup`, ...) are NOT deprecated by v1: they are the operator surface the standing contract
names, and marking them deprecated before the service can replace their function would be
ritual ahead of substance (the 2026-07-11 ruling's own test). Instead v1 DECLARES them, in the
service's own README section, as the remaining sanctioned non-service surface, with their
eventual routing-through-the-service reserved as a maintainer-sequenced v2 question. If the
maintainer intended the stronger reading, that word reverses this paragraph, not the build.
The panel's direct-psql access, by contrast, is exactly the deprecated class: §6.

## 2. Residence and shape

- `serving/boundary_service.py` — the FastAPI app; plus `serving/boundary_models.py`
  (pydantic request/response models) and `serving/README.md`. Top-of-file imports only (the
  lazy-import ban is absolute). FastAPI + uvicorn come from the host's existing venv
  conventions; no new system packages.
- Per-deployment wiring: the service reads the SAME `deployment.json` the verbs read (db,
  host, schema, kern, role) — one config home, zero second copies. Launch:
  `python3 -m serving.boundary_service --deployment <path>` (or the scaffold writes a thin
  `serve` shim later; not v1).
- **Bind 127.0.0.1 by default, refuse `--host 0.0.0.0` without an explicit
  `--i-understand-this-exposes-the-ledger` flag** (the ledger carries operator-real content;
  same posture as the OTel collector's localhost-only rule).

## 3. The read surface (v1 endpoints, fixed)

| Endpoint | Serves | Notes |
| --- | --- | --- |
| `GET /health` | world name, lineage capability manifest (which of: s22 work, s41 identity, s43 boundary, credited view), service principal id | capability facts are DETECTED per request start-up, never assumed |
| `GET /rows/current` | `ledger_current`, id-paginated (`?after_id=&limit=`, `1 ≤ limit ≤ 1000`, `after_id ≥ 0`, ORDER BY id; bounds per A2.6/A2.7) | the in-force reading |
| `GET /rows/{id}` | one row, any status | includes status and supersession pointers |
| `GET /rows/{id}/history` | the row's supersession chain, each hop WITH its superseding row id | history-mode leg 1 |
| `GET /credited` | the credited view, when the world carries one | **capability-gated**: on a world without it, a typed `capability_absent` JSON refusal naming the missing lineage — never a silent fallback to `ledger_current` (that would be the F49 vacuous-pass at the serving layer) |
| `GET /standing/principals` | `principal_standing_current` (s41+ worlds; capability-gated as above) | |
| `GET /work/items` | the work-item views (s22+; capability-gated) | |

Display contract, carried from the defeat-pipeline spec §9 verbatim in substance: credited-only
is the DEFAULT reading wherever a credited view exists; defeated and superseded rows remain
reachable through the explicit history endpoints, shown with cause (which attestation, which
grant, what grade — the fields the credited view exposes), never merely absent.

## 4. The write surface

Four endpoints, one per s43 boundary function: `POST /write/ledger`, `/write/review`,
`/write/registration`, `/write/obligation`. Each accepts the function's jsonb payload
(pydantic-validated for JSON well-formedness and top-level shape only — the KERNEL validates
semantics; the service must not grow a second validator that could disagree with the
authority), calls the function through the granted role's connection, and returns the
`write_verdict` composite **verbatim as JSON**: `{disposition, row_id, refusal_id, sqlstate,
message}`.

- **A kernel refusal is HTTP 200 with `disposition: "refused"`** — a refusal is a first-class
  domain result carrying kernel-authored teach-text, not a transport error. Transport-level
  failures (malformed JSON, unknown fields, missing payload) are 422 and loud (ADR-0002).
- **On a pre-s43 world the write endpoints refuse entirely** (`capability_absent`, naming
  s43): the service NEVER falls back to raw INSERT. There is no code path that writes SQL
  DML; grep-provable, and the witness plan checks it (§8).
- Attribution: the service is registered at deployment as a principal (class `tool`, the s40
  ceremony), and its writes carry that principal via the same actor mechanism `led` uses.
  Per-end-user attribution through the service is RESERVED (v1 is a single-operator localhost
  tool); the honest limit is stated in `/health` and the README.

## 5. No truth of its own (the P2 discipline, made checkable)

No caching (v1 reads pass through to the views on every request); no default-filling beyond
JSON parsing; no reordering that changes meaning (`ORDER BY id` everywhere, matching the
engine's own convention); no error translation that paraphrases kernel teach-text (the
`message` field crosses byte-verbatim). The service's audit is a scripted spot differential —
`serving/audit_served.py`: fetch a served page, read the same view directly (read-only psql),
byte-compare the row sets, exit nonzero on any difference. Sentry-class treatment per row
1471: this audit verb ships WITH the service, not after it.

## 6. The deprecation duty (commission's letter, ADR-0002's spirit)

Every legacy direct-psql consumer path — v1 concretely: the autoharn-panel FastAPI-side SQL,
plus any panel doc describing direct access — gets a deprecation mark that is LOUD AT
INVOCATION (a runtime warning naming the replacement endpoint on every use, plus a marker
comment at the code site), states the replacement (`serving/` endpoint), and points at
[design/FABLE-WORLD-CONTEXT-MIGRATION-CONSULT-2026-07-19.md](FABLE-WORLD-CONTEXT-MIGRATION-CONSULT-2026-07-19.md)
for the crossing method. Deprecation-marked means still functional (backwards compatibility,
the commission's own carve-out) — but never silent: a silently-tolerated legacy path is the
fail-quietly shape ADR-0002 exists to forbid. Panel-side edits happen in the panel's own repo
by its own Sonnet session against this spec — never while a live session runs there.

## 7. What this supersedes and what it does not

- Row 1516 (`judge-all-capable-layers`) is NOT superseded: `judge` is differential tooling,
  not a serving surface; the commission's guess is answered here on the record.
- The envelope §9 read-architecture choice stands at option (c) (plain view) per its own
  recommendation; nothing here escalates to a daemon.
- The credited view remains s44-gated and unbuilt; §3's capability gate is how the service
  stays honest about that until a world carries it.

## 8. Witness plan (both polarities; WITNESSED / REFUSED-AS-EXPECTED / UNEXERCISED)

W1 accepted write through `/write/ledger` on a scratch s43 world — verdict `accepted`,
row readable back via `/rows/{id}`. W2 refused write (a payload the kernel refuses) — verdict
`refused` with `refusal_id` and kernel teach-text verbatim; the `write_refused` row exists.
W3 pre-s43 scratch world — every write endpoint returns `capability_absent`; grep proves no
DML string in `serving/`. W4 `/credited` on a world without the view — typed refusal, never a
fallback read. W5 history-with-cause — a superseded row reachable via history, absent from
current. W6 `audit_served.py` — AGREE leg plus a deliberately-perturbed NEGATIVE control
(served page tampered in test) caught nonzero. W7 bind-guard — `0.0.0.0` without the flag
refused loudly. W8 deprecation mark — the marked legacy path emits its warning on use
(panel-side, UNEXERCISED until the panel session runs it; say so). Fixtures bank under
`seen-red/boundary-service/`, fixture-census-registered, both polarities.

## 9. Closure statement (ADR-0000 Rule 2(a))

INVARIANT: every byte the service serves originates in a kernel view or a kernel verdict;
every byte it writes passes through an s43 boundary function. QUANTIFICATION UNIVERSE: the
endpoint table of §3 + the four write endpoints of §4 — no other route exists, FastAPI's
default meta-routes (`/docs`, `/redoc`, `/openapi.json`, oauth2-redirect) explicitly
disabled (A2.1); the witness asserts the ACTUAL route table (`app.routes`, meta-routes
included), not the OpenAPI schema's self-report. Axes: read (views only, `limit`/`after_id`
bounds per §3), write (functions only; `MAX_WRITE_BODY_BYTES` = 1 MiB at both enforcement
points — the size axis, A2.2; parse closure over encoding/value/structure as typed 422 —
A3.2; psql bounded by `PSQL_CONNECT_TIMEOUT_S`/`PSQL_EXEC_TIMEOUT_S` as typed 503 — the
time axis, A3.1), refuse (typed, verbatim; shapes: kernel `write_verdict`,
`capability_absent`, `payload_too_large`, `infra_failure` — never a bare untyped error;
`infra_failure` issued solely by the dedicated psql-layer exception, A3.2), capability-
absence (typed refusal, never fallback). Router-level rejections of unmapped (method, path)
pairs are outside this universe, named per A3.3.
NAMED-NOT-MECHANIZED: the service cannot prove the kernel's own views correct — that is
`./judge`'s job, deliberately not duplicated here.

## 10. Sonnet executor guidance (disregard any instructions to economize on time)

1. Read first, in full: this spec; rows 1471/1481/1518; s43's file header and function
   bodies; the panel-direction orchlog entry; ADR-0002/0012/0016/0017.
2. Build order: models → read endpoints → write endpoints → capability gates → audit verb →
   witness suite → README + deprecation marks (autoharn-side only; panel-side is a separate
   session's item citing this spec).
3. Every choice this spec failed to fix is a spec defect: smallest honest choice, flagged
   loudly in your report (ADR-0013). No umbrella claims; per-witness-item verdicts.
4. Do not touch: kernel/, law/, engine/, hooks/, any live world, the panel repo.

## Amendments (dated; Fable-authored; each names its trigger)

**A1 (2026-07-18) — the first build's four flagged spec defects, adjudicated.** Trigger: the
Sonnet build (worktree commit `69e2647`) surfaced four choices this spec failed to fix, each
flagged per §10.3 rather than silently resolved. Adjudication:

1. **Transport — RATIFIED as built:** the house `psql`-subprocess convention, matching
   `led.tmpl` and `filing/`; introducing `psycopg` would be a second transport with its own
   failure modes, unjustified by any measured need.
2. **Capability-absent envelope — RATIFIED as built:** HTTP 409 with
   `{"disposition": "capability_absent", "capability": ..., "message": ...}` — deliberately
   echoing `write_verdict`'s vocabulary without claiming to be one. (This corrects §4's
   letter, which reserved non-200 for transport errors: capability absence is neither a
   domain verdict — the kernel never saw the request — nor a malformed request; a third,
   typed shape is honest.)
3. **Bind guard — RATIFIED as built, a strengthening:** "any non-loopback host" behind the
   explicit flag, not the literal `0.0.0.0`; the spec's letter was the weaker form of its
   own intent.
4. **Service-principal write attribution — the genuine gap, now fixed:** the kernel's
   `set_actor` resolves default attribution by `session_user`'s standing declaration, so a
   service sharing the CLI's login role cannot carry a distinct default identity. The
   mechanism is: a **dedicated login role per deployment** (suggested name `<schema>_svc`),
   granted the same rights as the CLI role, bound to the registered service principal by an
   ordinary s40/s45 standing declaration (`led principal declare-standing <service-principal>
   --db-role <schema>_svc`) — the existing ceremony, no new machinery. Provisioning that
   role is a per-world operator act (documented in `serving/README.md`); until a world
   provisions it, the AS-BUILT disclosed pass-through (writes attributed exactly as an
   unset `LED_ACTOR`) stands as the honest interim. The service NEVER injects an `actor`
   field on a caller's behalf — a boundary asserting someone else's identity is the
   substitution class this project exists to make representable, not commit.

**A2 (2026-07-18) — post-build independent review findings, adjudicated; hardening basis.**
Trigger: independent fresh-context review of the merged build (base `9f483a9`) surfaced seven
findings beyond A1's settled set — none architectural, all repair-shaped, several witnessed
live. Each is adjudicated here; this amendment is the ratified basis for the hardening pass.

1. **§9's route claim was FALSE against the running service (HIGH, witnessed):** FastAPI's
   default `/docs`, `/redoc`, `/openapi.json`, `/docs/oauth2-redirect` were live and
   unenumerated, `/docs`/`/redoc` pulling assets from a third-party CDN; the witness suite's
   route check diffed the OpenAPI schema's self-report, which structurally cannot list those
   meta-routes — the claim verified itself (ADR-0013 Rule 5 failure). **Adjudication: disable,
   don't enumerate** — `FastAPI(docs_url=None, redoc_url=None, openapi_url=None)`. A ledger
   boundary needs no self-documentation surface with an external dependency; §3/§4 + the
   README are the documentation. The route witness is REPLACED: it must assert against the
   ACTUAL route table (`app.routes`), counting every route object including meta-routes, and
   §9's parenthetical now reads "the witness asserts the actual route table, not the schema's
   self-report."
2. **The ADR-0016 size axis was unhandled on the write ingress (HIGH class, witnessed two
   ways):** a ~3 MB payload crashed into a bare plain-text 500 at the psql-argv wall
   (`ARG_MAX` = 2 MiB), and a 100 MB body was buffered and JSON-parsed whole before any
   handler logic (an availability hazard on a host with documented OOM history).
   **Adjudication: one named bound, enforced twice.** `MAX_WRITE_BODY_BYTES = 1_048_576`
   (1 MiB — generous for any ledger payload, safely under the argv wall): (a) the raw request
   body is length-checked BEFORE JSON parsing (Content-Length when present, actual read
   otherwise); (b) the re-serialized payload is length-checked before the subprocess. Both
   refuse with HTTP 413, typed: `{"disposition": "payload_too_large", "limit_bytes": ...,
   "observed_bytes": ..., "message": <teach-text naming the bound and why>}`. The bound and
   both enforcement points are named in §9's axes (size joins the closure statement) and in
   the README.
3. **`/health`'s `service_principal_name()` was the one unguarded kernel query (MEDIUM,
   analytic):** on a pre-s40 world it 500s instead of degrading. **Adjudication:** guard with
   the same existence check every other capability fact uses; absent table → `service_principal:
   null` plus the capability manifest already saying why. Witnessed on a pre-s40 chain (§8 W10).
4. **Infra/DB failure returned a bare untyped 500 (LOW, witnessed):** everything else in the
   service is typed. **Adjudication:** psql infra failure (unreachable world, connection
   refusal, nonzero exit that is not a kernel verdict) returns HTTP 503, typed:
   `{"disposition": "infra_failure", "message": <generic, no SQL/role/schema/stack>}`; the
   full detail stays server-side in the log (ADR-0002 rung 3 loudness retained, exposure
   posture unchanged).
5. **The s41/s22 capability-refuse legs were unwitnessed (LOW):** both fixture worlds carried
   those views. **Adjudication:** the suite adds a chain that lacks them; both legs of both
   gates get a polarity each (§8 W11).
6. **`after_id` accepted negatives while `limit` was range-checked (INFO):**
   **Adjudication:** `after_id ≥ 0`, typed 422 below it — symmetry, not necessity.
7. **The read-side `limit` bound (1..1000) was an invented, undisclosed policy (LOW):**
   **Adjudication: RATIFIED and now spec text** — §3's pagination reads
   `?after_id=&limit=, 1 ≤ limit ≤ 1000, after_id ≥ 0`; the A1-style lesson (both ingresses
   held to ONE disclosed discipline) is the point of this whole amendment.

§8 gains: **W9** oversized write body (both enforcement points) → typed 413, server alive,
`/health` still answering. **W10** `/health` on a pre-s40 chain → 200 with null principal,
no 500. **W11** s41/s22 capability-refuse legs, both polarities. **W12** route-table witness
against `app.routes` — count AND membership, meta-routes included (expected: exactly the
§3/§4 routes plus nothing). §9's closure statement is amended in place per items 1, 2, 4
(new typed shapes `payload_too_large`, `infra_failure` join the refuse axis).

**A3 (2026-07-18) — iteration-1 independent re-review findings, adjudicated.** Trigger:
independent fresh-context re-review of the hardened build (`cac001e`). Every A2 fix held under
live attack (route closure true against the running service, both size checkpoints proven,
/health guard, capability legs, bind guard, injection — all re-witnessed clean). The new
findings are adjacent axes of the same write ingress that A2's size closure did not reach —
the second consecutive demonstration of ADR-0000's "the class as first named is presumed too
narrow." Adjudication:

1. **The time axis (witnessed):** `_psql` runs with no timeout of any kind — a database that
   HANGS rather than exits (blackhole, accept-then-stall) leaves the request unbounded, and
   A2.4's own words ("unreachable world") promised a typed 503 for exactly this. Amplifier:
   the write handlers are `async def` calling the blocking subprocess directly on the event
   loop, so one stalled write starves every route including `/health` (the ADR-0016 wedge
   class). **Fix:** two named constants — `PSQL_CONNECT_TIMEOUT_S = 5` (passed as
   `PGCONNECT_TIMEOUT` in the subprocess environment) and `PSQL_EXEC_TIMEOUT_S = 60`
   (`subprocess.run(timeout=...)`); `TimeoutExpired` maps to the typed 503 infra path (a
   stall IS infra). The write handlers become plain `def` so FastAPI's threadpool runs them
   off the event loop (the smallest honest offload, matching the read routes). §9's axes
   gain time.
2. **The parse closure (witnessed, three ways):** the A2.2 raw-body path lost FastAPI's
   default exception coverage — `json.loads` raises `UnicodeDecodeError` on invalid UTF-8
   (bare untyped 500), `ValueError` on a >4300-digit integer literal (bare 500), and
   `RecursionError` on deep nesting, which subclasses `RuntimeError` and therefore lands in
   the infra handler, telling the client "this is an infrastructure problem, not a problem
   with your request" — an actively false cause statement (the lying-signature class).
   **Fix:** the body is explicitly decoded and parsed under `except (ValueError,
   RecursionError)` (`ValueError` covers `JSONDecodeError` and `UnicodeDecodeError`) → typed
   422 transport refusal naming the failed axis (encoding / value magnitude / structure),
   never echoing raw body bytes. **And the infra handler is narrowed to a dedicated
   exception class** (`PsqlInfraFailure`, raised only by the psql layer) so no foreign
   exception can ever wear the `infra_failure` signature by accident again — that narrowing
   is the load-bearing part of this item, not the catch list.
3. **Router-level 404/405 untyped shapes — ACCEPTED AS-IS, named:** rejections of an
   unmapped (method, path) by the router sit outside §9's enumerated ingress universe; the
   README names this boundary explicitly (named-not-mechanized). Revisit only if a consumer
   demonstrates harm.
4. **Witness gaps close:** **W13** parse-closure legs on an s43 world (invalid UTF-8,
   oversized integer literal, deep nesting → typed 422 each, server alive after); **W14**
   the hang leg (service pointed at a non-routable address → typed 503 within
   `PSQL_CONNECT_TIMEOUT_S` + margin, not the OS TCP timeout); the W9 streaming-abort leg
   is exercised if cheaply drivable, else carries an explicit UNEXERCISED mark naming why.
5. **Transient fixture collision (witnessed once, not reproduced) — not a service defect:**
   root-caused to concurrent suite runs on the shared toy DB using IDENTICAL scratch-world
   names (two independent reviewers ran the suite simultaneously). **Fix:** scratch world
   names gain a per-run unique suffix (pid-derived), teardown scoped to that run's suffix —
   concurrent-runner safety, auditability unchanged.

§9's closure statement is amended in place: the write axis now reads "functions only,
`MAX_WRITE_BODY_BYTES` = 1 MiB both enforcement points, parse closure over encoding/value/
structure (typed 422), psql bounded by `PSQL_CONNECT_TIMEOUT_S`/`PSQL_EXEC_TIMEOUT_S`
(typed 503)"; the refuse axis's typed-shape list is unchanged, with `infra_failure` now
issued solely by the dedicated psql-layer exception.

**A4 (2026-07-18) — iteration-2 independent re-review findings, adjudicated.** Trigger:
independent fresh-context re-review of the hardened build (`cb639b0`). Every A3 fix held
under live exercise (both timeout bounds proven, parse closure over the three named axes,
off-loop handlers, route/size/capability/injection legs all re-witnessed clean). Both
reviewers independently converged on ONE new root class, the third consecutive instance of
ADR-0000 2(a) on this ingress: **`PsqlInfraFailure` names a narrower class than the code
assigns to it.** `_query_json` maps EVERY nonzero psql exit to it, but psql under
`ON_ERROR_STOP=1` reliably distinguishes (witnessed live): **exit 2** = connection-level
failure (genuinely infra) vs **exit 3** = script/data-level failure — which the write path
reaches with caller-supplied values that are valid JSON yet not Postgres-representable. Those
callers currently receive 503 `infra_failure` with a message asserting "not a problem with
your request" — false for their case (the lying-signature class, ADR-0002 rung 3), and it
lets a handful of cheap malformed payloads counterfeit outage signal in the logs. Adjudication:

1. **Value closure at the parse boundary (writes) — the class closed as a class, not per
   specimen.** After parse, before psql, two named checks, each a typed 422 naming its axis,
   never echoing body bytes: (a) **non-finite numbers** — re-serialization uses
   `json.dumps(..., allow_nan=False)`, so `Infinity`, `NaN`, and any literal parsing to an
   infinite float (`1e400`) refuse on the value axis; (b) **Postgres-text-representability**
   — the serialized payload refuses if it carries `\u0000` or an unpaired UTF-16 surrogate
   (the two classes jsonb cannot store; checked mechanically, e.g. a strict UTF-8 encode of
   the serialized text plus a NUL-escape scan). §9's parse-closure axis list grows to
   encoding / value magnitude / structure / non-finite / representability.
2. **Read-side id domain closes symmetrically:** every id-typed path/query parameter is
   bounded to `0 ≤ id ≤ 2^63 − 1` → typed 422 above it (the A2.6 `after_id ≥ 0` precedent,
   completed upward; today an over-range id reaches psql's bigint cast and wears 503).
3. **Exit-code fidelity in `_psql`:** `PsqlInfraFailure` (→ typed 503, message unchanged —
   now true) is raised ONLY for connection-level failure: exit 2 and `TimeoutExpired`.
   Exit 3 and any other residue — unreachable via the request after items 1–2, so its
   occurrence means a boundary or deployment defect — raises a second dedicated exception →
   typed 500 `{"disposition": "unclassified_failure", "message": <honest: the storage layer
   refused for a reason this boundary did not anticipate; logged server-side; may be the
   deployment or the request — the boundary declines to guess>}`, logged loudly with full
   detail server-side. No signature claims a cause it cannot witness.
4. **`audit_served.py` regression (mandatory):** its `except RuntimeError` predates A3.2's
   dedicated exception — `PsqlInfraFailure` is NOT a `RuntimeError`, so a direct-read infra
   failure now escapes both handlers and breaks that tool's exit-2 contract. The handler
   catches the dedicated exception(s); the exit-2 contract is re-witnessed. (A3 introduced
   this by narrowing the exception without sweeping its second consumer — the narrowing was
   right, the sweep was owed; noted as the lesson of this item.)
5. **Witness gaps close:** **W15** non-finite legs (`Infinity`, `NaN`, `1e400` → typed 422,
   value axis, server alive); **W16** representability legs (`\u0000`-bearing string,
   unpaired surrogate → typed 422); **W17** over-range id on the read side → typed 422;
   **W18** exit-code fidelity both polarities (connection refusal → 503 `infra_failure`;
   a forced script-level failure on a scratch world → 500 `unclassified_failure`, message
   honest); **W19** `audit_served.py` exit-2 contract on an unreachable world.

§9 is amended in place per items 1–3: the write axis's parse closure gains the two new
axes; the refuse axis's typed-shape list gains `unclassified_failure`; `infra_failure`'s
issuing condition narrows to connection-level (exit 2 / timeout) only.

**A5 (2026-07-18) — iteration-3 independent re-review findings, adjudicated.** Trigger:
independent fresh-context re-review of the hardened build (merge `7016a24`), two blind
reviewers on distinct angles. Every A2/A3/A4 behavior held under live re-exercise (full
suite green, all nineteen witnesses); no crash/wedge/leak class remains. Five findings —
including the loop's first fix-introduced regression, which is why re-review exists.
Adjudication:

1. **A4.1's representability scan is denominated on the wrong text (REGRESSION, mandatory,
   witnessed both ways):** the scan inspects the *escaped* serialization, so a payload
   containing the literal six characters `\u0000` (a backslash, then `u0000` — documenting
   an escape, a regex, a code snippet; NO NUL codepoint present) is falsely refused with a
   message asserting a NUL that is not there — the exact lying-signature class A4 exists to
   close, produced by A4's own fix. jsonb stores that payload fine. **Fix:** the scan runs
   over the ACTUAL codepoints of the parsed value (walk the parsed object's strings and
   keys, or equivalently scan a non-escaping `ensure_ascii=False` serialization), refusing
   only a real U+0000 or a real unpaired surrogate. The false-positive input becomes a
   GREEN witness leg; the true-positive legs stay red.
2. **Write-payload integer fields lack the id-domain bound (witnessed):** a finite integer
   above bigint range in an id-referencing payload field passes every A4 axis, reaches
   psql, and dies at exit 3 → 500 `unclassified_failure` whose message is false for this
   ordinary caller value. Worse, the witnessed failure point is *inside
   `kernel.journal_write_refusal`* — a genuine s43 kernel defect (the refusal-journaling
   path itself overflows; sibling field `supersedes` gets a clean typed `refused`), filed
   as constitutional intake at work item `s43-refusal-journal-bigint-overflow` (row 1581),
   NOT fixed by this service. **Boundary fix:** every integer-typed field the payload
   contract declares (the pydantic models are the enumeration authority) is bounded to
   `0 ≤ v ≤ 2^63 − 1` at the parse boundary → typed 422 naming the field and bound —
   A4.2's discipline propagated from path/query to body, completing the id-domain class.
   No semantic validation beyond the domain bound (the kernel stays the authority).
3. **The time axis was half-closed (witnessed):** A3.1 bounded the psql phase; the raw-body
   READ phase has no bound — a trickled body holds its request open indefinitely (48 s
   witnessed; /health unaffected, so per-request only). **Fix:** one named constant
   `BODY_READ_TIMEOUT_S = 30` enforced around the body stream read; expiry → typed 408
   `{"disposition": "body_read_timeout", "timeout_s": ..., "message": <teach-text>}`.
   §9's time axis now names both legs (read phase, psql phase), symmetric with A2.2's
   two size checkpoints.
4. **Pagination discipline applied to two of four read routes (both reviewers, witnessed):**
   `/standing/principals` and `/work/items` silently accept-and-discard `limit`/`after_id`
   and return the whole view — the ADR-0012 applied-once-not-propagated shape, and a
   silently no-op'd parameter is the ADR-0002 rule-4 class. **Fix:** both routes gain the
   SAME declared `limit`/`after_id` discipline as `/rows/current` and `/credited`
   (1..1000, ≥ 0, typed 422 outside, honored in SQL with stable id-ordered pagination —
   using each view's id-shaped key; the fixer flags if a view lacks one and falls back to
   a documented deterministic ordering). §3's table now names the bounds on all four.
5. **Framework-owned parameter-coercion 422 on matched read routes — ACCEPTED AS-IS,
   named (the A3.3 precedent):** a non-integer value for an int-typed path/query param
   returns FastAPI's own untyped-list 422 shape. This sits at the framework's transport
   layer, predates every amendment, and carries no false cause statement; §9 names it as
   the delegated-to-framework coercion sub-axis. Revisit only if a consumer demonstrates
   harm.

§8 gains: **W20** literal-`\u0000`-text accepted (green) while real-NUL and unpaired
surrogate stay refused (red); **W21** over-bigint integer payload field → typed 422 naming
field and bound; **W22** trickled body → typed 408 within `BODY_READ_TIMEOUT_S` + margin;
**W23** pagination on `/standing/principals` and `/work/items`, both polarities (honored
`limit=1`; out-of-range → typed 422). §9 is amended in place per items 1–4; the refuse
axis's typed-shape list gains `body_read_timeout`.

**A6 (2026-07-18) — iteration-4 re-review: one residue inside A5.2's own class,
adjudicated.** Trigger: fourth blind pair on `2a1f235`. One reviewer CLEAN across every
amended axis (including its own adjacent-axis probes: element-wise `enacts` bounds,
60-way concurrent writes, framework coercion). The other confirmed everything held and
found A5.2's bound denominated on the *Python type* (`isinstance(v, int)`) rather than on
the *value*: a JSON number in float/exponent form (`1e20` for `actor`) skips the check,
reaches psql, and lands on the row-1581 kernel defect → 500 `unclassified_failure`
instead of W21's typed 422. **Adjudication — A5.2's denomination corrected in place:**
the bound applies to any *numeric* value of a declared integer field whose magnitude lies
outside `0 ≤ v ≤ 2^63 − 1` (typed 422, same shape as W21). Preserved deliberately, per
the finding's own terms: a genuine type mismatch (string/bool/object under an int field)
stays the kernel's rowtype-cast business, and an in-range float-valued id (`5.0`) is not
newly refused — it passes to the kernel exactly as before. **W21 gains the float legs**
(`1e20` → 422; `5.0` → kernel verdict, not a 422). No other change.

**A7 (2026-07-18) — iteration-5 confirmation pass: one new adjacency from A5.1's own
mechanism, adjudicated.** Trigger: single-reviewer confirmation on `0866a11`. Every
A2–A6 behavior held (re-driven live, including the id-field enumeration independently
checked complete against the kernel's own column authority). The finding: A5.1's
representability scan walks the parsed value with a *recursive* traversal that inherits
none of A3.2's recursion-depth protection — a well-formed body nested ~1000–9999 levels
(under the size bound, under `json.loads`'s own ~5000+ RecursionError threshold) raises
an uncaught `RecursionError` *after* parse, inside the traversal, and escapes every
registered handler → bare text/plain 500, the untyped shape this spec has banned since
A2.4. Server survives; the class is caller-observable identical to A3.2's structure axis
("a too-deeply-nested body"), split only by which Python frame overflows first.
**Adjudication:** the post-parse traversal joins A3.2's own catch — the value-closure
call sites (the representability scan, and any future post-parse walk of the payload)
run under the same `except RecursionError` → typed 422 naming the structure axis that
A3.2 already owns (or, equivalently, `_iter_strings` becomes an explicit-stack iterative
walk — the fixer picks the smaller honest diff and says which). Preserved: A3.2's
parse-time catch stays (load-bearing at its own depths); every A5.1 green/red leg
unchanged. **W24:** a ~3000-level-nested, under-bound, otherwise-valid write body →
typed 422 structure axis, server alive; the existing W13 deep-nesting leg stays green.
§9's structure axis now reads "at parse AND at every post-parse traversal."

**A8 (2026-07-18) — iteration-6 confirmation pass: the size axis's real wall, and one
label consistency, adjudicated.** Trigger: single-reviewer confirmation on `4976e0d`.
Every A2–A7 behavior held under live re-exercise and independent adjacent probes. Two
findings:

1. **A2.2 sized its bound against the wrong limit (witnessed, latent since A2):** the
   1 MiB bound was justified as "safely under the argv wall (`ARG_MAX` = 2 MiB)" — but
   `ARG_MAX` bounds the *total* argv+env, while Linux's per-argument limit is
   `MAX_ARG_STRLEN` (32 pages ≈ 131 072 bytes), and the re-serialized payload travels as
   ONE psql `-v` argument. A payload between ~131 KiB and 1 MiB passes both A2.2
   checkpoints and detonates in `subprocess.run` as an uncaught `OSError` (E2BIG) →
   bare text/plain 500 — the untyped shape §9 forbids, and it makes checkpoint (b)'s
   stated bound unreachable-honest (no payload over ~131 KiB could ever have succeeded).
   **Fix, three parts:** (i) checkpoint (b)'s bound becomes a second named constant
   `MAX_PSQL_ARG_BYTES = 100_000` (under `MAX_ARG_STRLEN` with margin), typed 413 whose
   teach-text names the per-argument transport wall; checkpoint (a)'s raw-body 1 MiB
   pre-parse bound STAYS as the cheap early reject (its rationale — bounded buffering —
   is unchanged). (ii) `_psql` catches `OSError` and raises the unclassified-failure
   path (typed 500) so no future transport wall can ever wear the bare shape — defense
   in depth, not the primary mechanism. (iii) §9 and the README state both size bounds
   and why they differ (buffering vs transport). The A1-ratified psql transport is NOT
   reopened: the bound moves to the transport's true capacity rather than the transport
   moving to the bound (a ledger payload is prose; 100 KB remains generous, and A2.2's
   own "generous" claim is re-made honestly at the smaller number).
2. **Non-finite values under an int-declared field wear the id-domain label (witnessed,
   label consistency):** `Infinity` in `actor` refuses via the id-domain comparison
   ("got inf") while `NaN` in the same field refuses on the value axis — one condition,
   two labels, split by IEEE-754 comparison accidents. **Fix:** the int-field domain
   check tests finiteness FIRST and routes non-finite values to A4.1's value-axis
   message; finite out-of-range keeps the id-domain shape, `NaN` keeps its current
   correct label. Both stay typed 422.

§8 gains: **W25** the argv-wall legs — a ~200 KiB payload → typed 413 naming
`MAX_PSQL_ARG_BYTES`; a ~90 KiB payload → passes to the kernel (verdict, not 413);
**W26** `Infinity` under an int-declared field → typed 422 on the value axis (same
message family as `NaN`). §9's size axis now reads "raw body ≤ `MAX_WRITE_BODY_BYTES`
(buffering), re-serialized payload ≤ `MAX_PSQL_ARG_BYTES` (transport)."

## License

Public Domain (The Unlicense).
