<!-- doc-attest-exempt: freshly authored alongside the serving/ build this same commit, under
     the Fable freeze plan's Sonnet-executes posture (design/FABLE-LEDGER-BOUNDARY-SERVICE-
     SPEC.md's own header carries the identical deferral for the same reason). A fresh-context
     ADR-0017 A:B:C attestation is deferred until the content stabilizes against a maintainer/
     Fable review pass of the build it documents, the same deferral this spec's own build-basis
     document states for itself. -->

# serving/ — the FastAPI outer boundary into an autoharn-managed ledger

**Build basis:** [design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md](../design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md)
(RATIFIED — ledger rows 1471, 1481, 1518), **hardened per Amendment A2** (seven post-build
independent-review findings, adjudicated), **Amendment A3** (the time axis and the parse
closure — two more adjacent axes of the same write ingress A2's size closure did not reach),
**and Amendment A4** (value closure on non-finite numbers and Postgres-text-representability,
the read-side id domain, and exit-code fidelity in the psql layer — `PsqlInfraFailure` narrows
to genuinely connection-level psql failures only, exit 3 and other residue now get their own
typed `unclassified_failure`), **and Amendment A5** (the representability scan re-denominated
onto ACTUAL codepoints, fixing a regression A4's own fix introduced; write-payload integer
fields bounded to the id domain; the body-read phase's own time bound; pagination propagated to
`/standing/principals` and `/work/items`; the framework-owned coercion sub-axis named).
Read the spec in full, including A2, A3, A4, and A5, before touching this directory; this
README is an operator's pointer into it, not a restatement.

## What this is, in one paragraph

One FastAPI service is the **outer declared boundary** (ADR-0012 P2 Port) into an
autoharn-managed ledger, for every UI-class and programmatic consumer — the autoharn-panel
Vue SPA first. The kernel's own **inner** boundary — s43's four `SECURITY DEFINER` write
functions (`kernel.ledger_write`/`review_write`/`registration_write`/`obligation_write`) plus
the derived views (`ledger_current`, `principal_standing_current`, `work_item_current`, …) —
remains the sole authority. This service adds **no truth of its own**: it translates and
validates, refuses what it cannot honor, and never coerces. Every byte it serves originates in
a kernel view; every byte it writes passes through an s43 boundary function.

## What this is NOT

- **Not a second validator.** Write payloads are checked for JSON well-formedness and
  top-level shape only; the kernel is the one authority on ledger semantics.
- **Not a replacement for the operator verbs.** `led`, `judge`, `pickup`,
  `distance-to-clean`, `attest-tags`, `audit` are **declared here, explicitly, as the
  remaining sanctioned non-service surface** (spec §1) — v1 does not deprecate them; routing
  them through this service is a reserved, maintainer-sequenced v2 question.
- **Not a cache.** Every request re-detects capabilities and re-reads/re-writes through the
  kernel fresh — no caching anywhere in this module (spec §5).

## Running it

```sh
$HOME/w/vdc/venvs/generic/bin/python -m serving.boundary_service --deployment /path/to/deployment.json
```

Binds `127.0.0.1:8420` by default. Any other host requires an explicit
`--i-understand-this-exposes-the-ledger` flag — the ledger carries operator-real content, the
same posture as the OTel collector's localhost-only rule. Run from the repo root (`-m
serving.boundary_service`, matching the spec's own launch command).

**Dependencies:** FastAPI + uvicorn, installed into this host's existing generic venv
(`$HOME/w/vdc/venvs/generic`) — the project has no `venv setup` script of its own for this
service; a fresh host needs `$HOME/w/vdc/venvs/generic/bin/pip install fastapi uvicorn`
once (pydantic already ships in that venv for other consumers).

## Endpoint table (spec §3, §4 — fixed; the route table itself IS the enumeration, spec §9/A2.1)

This service carries **exactly eleven routes** — the seven GETs and four POSTs below — and
**nothing else**. FastAPI's own self-documentation surface is **disabled, not merely
unenumerated**: `docs_url=None, redoc_url=None, openapi_url=None` (A2.1), so `/docs`, `/redoc`,
`/openapi.json`, and `/docs/oauth2-redirect` do not exist on this service at all — there is no
running-schema self-report to ask, honest or otherwise. The witness suite's W12 asserts this
table against `app.routes` **directly, in-process** (never a schema endpoint).

| Method | Path | Serves | Capability gate |
| --- | --- | --- | --- |
| GET | `/health` | world name, capability manifest, this service's registered principal name | none |
| GET | `/rows/current` | `ledger_current`, id-paginated (`?after_id=&limit=`, bounds below) | none |
| GET | `/rows/{id}` | one row, any status | none |
| GET | `/rows/{id}/history` | the row's full supersession chain (both directions), each hop carrying its own `superseded_by` | none |
| GET | `/credited` | the credited view, when the world carries one | `s44-credited-view` — no world in this repository's kernel lineage carries this view yet (spec §7); always `capability_absent` today |
| GET | `/standing/principals` | `principal_standing_current`, id-paginated (`?after_id=&limit=`, bounds below, A5.4) | `s41-identity` |
| GET | `/work/items` | `work_item_current`, ORDINAL-paginated (`?after_id=&limit=`, same bounds; the view has no id column, A5.4's fallback below) | `s22-work` |
| POST | `/write/ledger` | `kernel.ledger_write` | `s43-boundary` |
| POST | `/write/review` | `kernel.review_write` | `s43-boundary` |
| POST | `/write/registration` | `kernel.registration_write` | `s43-boundary` |
| POST | `/write/obligation` | `kernel.obligation_write` | `s43-boundary` |

**Capability detection is object existence** (`to_regclass`/`pg_proc`), never a version
literal — the same migrate-detect-drift discipline `bootstrap/templates/led.tmpl`'s own s43/s45
probes use, so a world need not match this service's authoring commit exactly.

**The router-level 404/405 boundary (A3.3, named-not-mechanized).** A request to an unmapped
`(method, path)` pair — a typo'd path, a `PUT` on a `GET`-only route, anything outside the
table above — is rejected by FastAPI's/Starlette's own router, before this service's code ever
runs, as an ordinary untyped `{"detail": "Not Found"}` (404) or `{"detail": "Method Not
Allowed"}` (405). This is **outside §9's enumerated ingress universe by construction**: the
closure statement's axes (size, time, parse, capability-absence) are properties of a REQUEST
THIS SERVICE ACCEPTS FOR DISPATCH; a request the router itself never dispatches never reaches
any of this service's own refusal machinery to hold to that discipline. Revisit only if a real
consumer demonstrates harm from the untyped shape (spec A3.3's own carve-out) — not pre-emptively
typed, per ADR-0004 (no work ahead of a demonstrated need).

## Bounds (A2.2, A2.6, A2.7, A3.1, A4.1, A4.2, A5.1–A5.4 — one disclosed discipline, every ingress)

- **Pagination — ALL FOUR read routes** (`/rows/current`, `/credited`, `/standing/principals`,
  `/work/items` — A5.4 propagated this from two routes to all four): `?after_id=&limit=`,
  **`1 ≤ limit ≤ 1000`**, **`after_id ≥ 0`** — both violations are a typed HTTP 422 naming the
  bound. Ratified spec text as of A2.7; A2.6 added the `after_id ≥ 0` half (it previously
  accepted negatives while `limit` was already range-checked — an asymmetry with no reason).
  `/rows/current`, `/credited`, and `/standing/principals` page on the view's own `id` column
  (`WHERE id > after_id ORDER BY id LIMIT limit`, identical shape on all three). `/work/items`
  serves `work_item_current`, which carries **no id-shaped key at all** (one row per `slug`, no
  bigint column) — its fallback, named per the spec's own "flag it if a view lacks one" clause:
  a `row_number() OVER (ORDER BY slug)` ordinal, computed ONLY inside the service's own wrapper
  query (never stored, never claimed to be a kernel id, since `slug` is unique per the view's
  own invariant — one opening act per slug), stands in for `id` as the `after_id`/`limit`
  cursor. The synthetic ordinal is stripped back out of each row's JSON before it is returned,
  so the served row shape stays byte-identical to the view's own columns; only the cursoring
  mechanics differ from the id-keyed routes.
- **The read-side id domain** (A4.2, symmetric with A2.6): every id-typed path/query parameter
  — `/rows/{id}`, `/rows/{id}/history`'s `id`, and every route's `after_id` — is bounded
  **`0 ≤ id ≤ 9223372036854775807`** (a Postgres `bigint`'s own ceiling, `MAX_ID`), typed HTTP
  422 outside it. Before this bound existed, an over-range id reached `psql`'s bigint cast
  unchecked and wore a 503 it did not earn.
- **The write-ingress value closure** (A4.1, at the parse boundary, after structure/encoding/
  magnitude, before `psql`): (a) **non-finite numbers** — the payload is re-serialized with
  `json.dumps(..., allow_nan=False)`, so `Infinity`, `NaN`, and any numeric literal that
  overflows to one of them (e.g. `1e400`) refuse on the **value axis**, since jsonb has no
  representation for them; (b) **Postgres-text-representability** — the payload refuses if it
  carries a literal `U+0000` (NUL) or an unpaired UTF-16 surrogate character on the
  **representability axis**, neither of which jsonb text storage can store. Both are typed
  HTTP 422 naming the axis, never echoing the payload back. **A5.1 fixed a regression in (b):**
  the pre-A5 scan inspected the *escaped serialization*'s text, so a payload whose string
  content was the literal six characters "a backslash, then u0000" (documenting an escape in
  prose — no real NUL codepoint present) re-escaped its own backslash and false-positived on
  the same six-character substring the old scan matched. The fix walks the ACTUAL codepoints of
  the PARSED value (every string and object key, recursively) — a real `U+0000` or a real
  unpaired surrogate still refuses; the literal-escape-text case is now correctly accepted
  through to the kernel.
- **The write-ingress id-domain closure on the BODY (A5.2, new):** every integer-typed field
  the payload contract declares — `serving/boundary_models.py`'s per-surface `*WriteIntFields`
  models are the enumeration authority (e.g. `actor`/`supersedes`/`regards`/`enacts` on
  `/write/ledger`; `assigned_by`/`obliges_actor` on `/write/obligation`) — is bounded
  **`0 ≤ v ≤ MAX_ID`** if the caller supplied it, typed HTTP 422 naming the field and the
  bound. This is A4.2's id-domain class completed from path/query onto the write body; no
  other semantic validation is added (a non-integer value under one of these field names is
  left for the kernel's own rowtype cast to judge — a type question, not a domain-bound one).
  **A8 label consistency:** the check tests **finiteness first** — a non-finite numeric value
  (`Infinity`/`-Infinity`/`NaN`, including `1e400`-parsed-to-`inf`) under a declared int field
  is routed to the value-axis refusal above (A4.1(a)'s own message), never the id-domain
  shape; pre-A8, `Infinity` in `actor` wore the id-domain label ("got inf") while `NaN` in
  the same field wore the value axis — one condition, two labels, split by IEEE-754
  comparison accident. Finite out-of-range values keep the id-domain shape; in-range values
  (including in-range floats like `5.0`) pass to the kernel unchanged.
- **Write body size** (`/write/*`, re-denominated per A8): **TWO named bounds, one per
  checkpoint, because the two checkpoints guard two different walls.** (a) The **raw request
  body**, before any JSON parsing, is bounded by `MAX_WRITE_BODY_BYTES = 1_048_576` (1 MiB) —
  its rationale is **buffering**: never hold an unbounded body in memory (Content-Length
  checked first when the client declared one — refused without ever reading the body; the
  actual byte count otherwise, refused mid-stream, never buffered whole). (b) The
  **re-serialized payload**, before the `psql` subprocess, is bounded by
  `MAX_PSQL_ARG_BYTES = 100_000` — its rationale is **transport**: the payload crosses to
  postgres as ONE `psql -v` argument, and Linux's *per-argument* limit is `MAX_ARG_STRLEN`
  (32 pages = 131 072 bytes), not the 2 MiB total-argv `ARG_MAX` the pre-A8 bound was sized
  against — a payload between ~131 KiB and 1 MiB passed both pre-A8 checkpoints and
  detonated in the subprocess launch as an uncaught `E2BIG` (a bare untyped 500). 100 KB
  remains generous for a ledger payload (prose), and the A1-ratified `psql` transport is not
  reopened: the bound moved to the transport's true capacity, not the transport to the bound.
  A payload can pass (a) and still fail (b) — any raw body between the two bounds, or
  non-ASCII content whose `json.dumps`-default `\uXXXX` escaping expands past its raw UTF-8
  size. Either checkpoint returns HTTP 413:
  `{"disposition": "payload_too_large", "limit_bytes": <the bound that fired: 1048576 for (a), 100000 for (b)>, "observed_bytes": <n>, "message": "<teach-text>"}`
  — `limit_bytes` is honest about which bound refused. Defense in depth behind (b): `_psql`
  also catches `OSError` from the subprocess launch itself and routes it to the typed 500
  `unclassified_failure` path, so no present or future transport wall can wear a bare shape.
- **The time axis, BOTH legs (A3.1 psql phase; A5.3 body-read phase, new):** every `psql` call
  this service makes is bounded twice — `PSQL_CONNECT_TIMEOUT_S = 5` (passed as
  `PGCONNECT_TIMEOUT` in the subprocess's own environment, so libpq itself refuses a stalled TCP
  handshake/auth round trip) and `PSQL_EXEC_TIMEOUT_S = 60` (`subprocess.run(timeout=...)`,
  catching a peer that accepts the connection and then goes silent — a blackhole/accept-and-
  stall, the class no libpq connect-timeout option reaches). A `subprocess.TimeoutExpired` on
  either bound is treated as infra failure (HTTP 503, below) — "a stall IS infra." The write
  handlers are plain `def` (see "Write path shape" below), so a stalled write cannot starve
  `/health` or any other route. **Separately, `BODY_READ_TIMEOUT_S = 30`** bounds the RAW BODY
  READ phase itself — before A5.3, a trickled body (a client sending a declared-length body a
  few bytes at a time) held the request open indefinitely, since the psql-phase bounds above
  only start their clock once the body is already fully in hand. Expiry returns a typed HTTP
  408: `{"disposition": "body_read_timeout", "timeout_s": 30, "message": "<teach-text>"}`.
- **The admission axis (A9, new): concurrent kernel-call admission is bounded, never queued.**
  Per-request time was bounded (above); *how many requests can be inside a kernel call at once*
  was not — witnessed with measurements, N concurrent stalled requests exhaust the shared ASGI
  threadpool (anyio's default 40 tokens on the review host) and wall-clock on EVERY route,
  `/health` included, grew unboundedly with N (80 → 5.3 s, 200 → 27.7 s, 600 → no answer in
  180 s). Fix: `MAX_INFLIGHT_KERNEL_CALLS = 24` (deliberately under the threadpool's 40 tokens)
  — every kernel call (reads, writes, and `/health`'s own kernel probes alike) acquires a
  non-blocking slot from one shared semaphore immediately before the `psql` subprocess runs, and
  releases it the instant that call returns. On saturation the caller is refused IMMEDIATELY,
  never queued: HTTP 503,
  `{"disposition": "server_saturated", "inflight_limit": 24, "message": "<teach-text naming the
  bound, the cause, and that retry-after-backoff is the correct response>"}`. `/health` shares
  this same gate — bounded admission is what guarantees it never waits behind other requests'
  occupancy, even under a burst that would otherwise starve it.
- **Framework-owned parameter coercion (A5.5, ACCEPTED AS-IS, named — the A3.3 precedent):** a
  non-integer value for an int-typed path/query parameter (e.g. a non-numeric `after_id`)
  returns FastAPI's/pydantic's own untyped coercion-failure 422 shape, not one of this service's
  typed shapes above. This sits at the framework's transport layer, predates every amendment,
  and carries no false cause statement (it is not claiming to be a kernel or service verdict);
  revisit only if a consumer demonstrates harm, per the same named-not-mechanized carve-out
  A3.3 already applies to router-level 404/405s below.

## Infrastructure failure (A2.4, extended per A3.1, NARROWED per A4.3)

A `psql` failure that is genuinely **connection-level** — an unreachable world, a connection
refusal (`psql` exit 2), OR a `PSQL_EXEC_TIMEOUT_S` stall — is typed, not a bare 500: HTTP 503,
`{"disposition": "infra_failure", "message": "<generic — no SQL, role, schema, or stack>"}`. As
of A3.2 this is raised ONLY by the service's own dedicated `PsqlInfraFailure` exception (never a
bare `RuntimeError`, which a foreign failure such as `RecursionError` — a `RuntimeError`
subclass — could also raise and thereby wear this shape by accident); one exception handler on
the FastAPI app, registered on that dedicated class, is the single home for this translation
(ADR-0012 P1) — every route inherits it, not a per-route try/except. The full `psql` stderr is
logged server-side (stderr) for operator diagnosis; it never reaches the client.

**Unclassified failure (A4.3, the sibling narrowing).** `psql` exit 3 (a script/data-level
failure under `ON_ERROR_STOP=1`) or any other unrecognized nonzero residue is **NOT**
connection-level and no longer wears `infra_failure` — before A4.1/A4.2 closed the
value-closure and id-domain classes above, this path was reachable by a handful of cheap
malformed-but-not-invalid-JSON payloads, which then counterfeited outage signal in the infra
logs (an actively false "not a problem with your request" claim, the lying-signature class
ADR-0002 rung 3 exists to forbid). It now returns a DEDICATED typed shape, HTTP 500:
`{"disposition": "unclassified_failure", "message": "<honest: the storage layer refused for a
reason this boundary did not anticipate — may be the deployment or the request; the boundary
declines to guess>"}`. Raised ONLY by the service's own dedicated `PsqlUnclassifiedFailure`
exception, on its own exception handler (ADR-0012 P1, matching `PsqlInfraFailure`'s own
discipline) — never `infra_failure`, and never a bare 500. After A4.1/A4.2, this path is
unreachable via an ordinary caller-supplied request; its occurrence names a boundary or
deployment defect. Full `psql` stderr logged server-side only, exactly like `infra_failure`'s
own logging discipline.

**Capability-absent responses** are HTTP 409 with body
`{"disposition": "capability_absent", "capability": "<name>", "message": "<teach-text>"}` — a
third, service-level disposition, deliberately shaped to sit beside the kernel's own
`write_verdict.disposition` vocabulary (`accepted`/`refused`) without ever claiming to be a
kernel verdict itself. **This is a spec defect resolution, not a specified shape** — the spec
names the refusal's meaning ("typed", "never a silent fallback") but not its HTTP status or
JSON envelope; 409 + this shape is the smallest honest choice made here. Flagged for the
Fable/maintainer orchestrator to confirm or override.

**Write verdicts** (`/write/*`) cross **byte-verbatim** as the kernel's own
`write_verdict` JSON, HTTP 200 whether `accepted` or `refused` — a kernel refusal is a
first-class domain result carrying kernel-authored teach-text, never a transport error.
Transport-level failures (malformed JSON, a non-object body) are a typed 422, loud — checked
by the write route itself (it reads and bounds the raw body manually, per the size checkpoints
above, rather than via an automatic pydantic body parameter).

**The parse closure (A3.2).** The explicit `json.loads` call over the (already size-bounded)
raw body is wrapped in `except (ValueError, RecursionError)` — the closure over every way that
call can fail short of well-formed, in-bound JSON: invalid UTF-8 (`UnicodeDecodeError`, a
`ValueError` subclass — the **encoding** axis), an integer literal past CPython's int-string
conversion guard (`ValueError` — the **value magnitude** axis), malformed JSON
(`json.JSONDecodeError`, also `ValueError`) or nesting too deep for the recursive-descent
parser to complete (`RecursionError`, which subclasses `RuntimeError` — both the **structure**
axis; the `RecursionError` case is exactly why the infra handler above is narrowed to
`PsqlInfraFailure` rather than a bare `RuntimeError`, so it cannot be mistaken for one). Every
leg is a typed HTTP 422 naming the failed axis, never echoing the raw body bytes back (the body
is untrusted and, in the encoding-axis case, may not even be valid UTF-8 to echo).

**Write path shape (A3.1).** The write handlers are plain `def`, matching the read routes —
FastAPI/Starlette dispatches a plain `def` path operation function to its threadpool, off the
event loop, so a write blocked on `PSQL_EXEC_TIMEOUT_S` cannot starve `/health` or any other
route. The one piece of genuinely ASGI-bound I/O — reading the raw request body — is factored
out to an `async def` FastAPI **dependency** (`_bounded_raw_body`), which the framework awaits
on the event loop before dispatching the synchronous handler to the threadpool; this is
FastAPI's own supported async-dependency/sync-handler split, not a hand-rolled bridge.

## The write path — attribution, honestly limited

Per-end-user attribution through this service is **RESERVED** (v1 is a single-operator
localhost tool, spec §4) — the service passes a write payload's `actor` key through unchanged
if the caller supplied one; if omitted, the kernel's own `set_actor` default-resolution
applies, exactly as it does for a `led` write with no `LED_ACTOR` set (session_user's declared
standing). **This service does NOT itself inject an actor.** A deployment that wants every
service-originated write attributed to a dedicated `boundary-service` principal (rather than
whatever principal the connecting role's standing declaration already resolves to) must:

1. Register the principal once (any already-registered `tool`-class principal can do this, or
   use the boundary directly): a `registration_write` payload
   `{"name": "boundary-service", "agent_class": "tool", "purpose": "the FastAPI outer boundary Port's own registered principal"}`.
2. Either supply `actor: <boundary-service-id>` on every write this service issues (the
   caller's responsibility — a UI/panel client would set this), OR give the service's own
   connecting login role a **dedicated** standing declaration to `boundary-service` (a
   `principal_standing_declared` payload naming that role) — which requires the service to
   connect as a role distinct from whatever role `led` already declares standing for, or the
   two would collide on one declaration per role (this repo's kernel does not appear to
   support more than one standing declaration in force per `db_role` — **this is a spec
   defect** worth the maintainer's attention: the exact mechanism by which THIS service's
   writes get attributed to its OWN registered principal, as opposed to riding the operator's
   existing declared-default, is not specified. Flagged loudly here rather than silently
   assumed.).

`GET /health`'s `service_principal` field reports whether a principal named `boundary-service`
of class `tool` **exists** in this world — a fact independently checkable from the attribution
question above (a registered-but-not-yet-declared-standing principal is a legitimate,
in-between state, and `/health` says so honestly rather than conflating "registered" with
"is the writing identity").

## Transport (a choice the spec left open — flagged)

This service connects to Postgres via a `psql` **subprocess**, `-v name=value` /
`:'var'` injection-safe substitution — the same house convention every `filing/` module and
`bootstrap/templates/led.tmpl`'s own `kernel_write()` helper already use (see
`filing/record_reading.py`'s own docstring point 1: "this repo has no psycopg dependency
... this module follows the house style rather than importing a transport the project does
not otherwise use"). A Python DB driver (`psycopg`) happens to already be present in this
host's `venvs/generic`, but introducing it here would be a **second** transport for the same
project — flagged as the smallest honest choice, not a spec mandate.

## `audit_served.py` — the served-vs-kernel spot differential

Ships WITH the service (spec §5, sentry-class treatment):

```sh
$HOME/w/vdc/venvs/generic/bin/python serving/audit_served.py \
    --base-url http://127.0.0.1:8420 --deployment /path/to/deployment.json \
    [--endpoint /rows/current] [--view ledger_current]
```

Fetches a served page over HTTP, reads the same view directly via a read-only psql, and
structurally compares the row sets by id (`compare_row_sets`, the one comparator both a live
audit and the witness suite's negative control exercise). Exit 0 = AGREE; exit 1 = a real
row-set disagreement (printed by row id and mismatched field); exit 2 = a transport/
infrastructure failure (the fetch or the direct read itself failed — not a disagreement
verdict, and not conflated with one).

## Witness suite

`seen-red/boundary-service/run_fixtures.py` (fixture-census registered) — both-polarity, real
infra (scratch Postgres schemas on the TOY db, real uvicorn subprocesses on loopback), no
mocks. Run:

```sh
HARNESS_PGHOST=<toy-db-host> $HOME/w/vdc/venvs/generic/bin/python seen-red/boundary-service/run_fixtures.py
```

Covers spec §8's W1–W7 plus A2's W9–W12 plus A3's W13–W14 plus A4's W15–W19 plus A5's W20–W23,
all live; **W8 (the panel-side deprecation-mark emission) is UNEXERCISED by construction** — that legacy path
lives in the separate autoharn-panel repository, which this build never touches, per the spec's
own §10.4 ("panel-side is a separate session's item citing this spec"). A2's additions: **W9**
an oversized write body at both A2.2 checkpoints (typed 413 both times, server stays alive,
`/health` still answers afterward); **W10** `/health` on a pre-s40 chain (200, null
`service_principal`, no 500); **W11** the s41/s22 capability gates' PRESENT leg (a chain
carrying both views) and ABSENT leg (a chain carrying neither — `WORLD NOCAP`, truncated
before s22); **W12** the route-table closure assertion, now against `app.routes` in-process
(A2.1 disabled the OpenAPI self-report the pre-hardening witness relied on). A3's additions:
**W13** the parse-closure legs — invalid UTF-8, a >4300-digit integer literal, a 60,000-level
deeply-nested body — each a typed 422 naming its axis, `/health` still answering after all
three; **W14** the hang leg — the service pointed at a deliberately non-routable address
(`10.255.255.1`) returns a typed 503 within `PSQL_CONNECT_TIMEOUT_S` plus a generous margin
(observed: ~5s against a 30s budget), nowhere near an ordinary OS TCP connect timeout (60–130s
on Linux) — proving the bound is this service's own, not the kernel's. **The W9 streaming-abort
leg is UNEXERCISED** (named per A3.4's own carve-out): driving it needs a client that half-closes
a POST mid-body, which this fixture's `urllib`-only transport cannot do without introducing a
second, parallel HTTP client layer. A4's additions: **W15** the non-finite legs — `Infinity`,
`NaN`, `1e400` — each a typed 422 on the value axis, `/health` still answering after all three;
**W16** the representability legs — a U+0000-bearing string, an unpaired UTF-16 surrogate —
each a typed 422 on the representability axis; **W17** an over-range id on the read side, both
a path parameter (`/rows/{id}`) and a query parameter (`/rows/current?after_id=`), each a typed
422; **W18** exit-code fidelity, both polarities — **(a)** a fresh server instance whose
`PGPORT` points at a closed local port (a genuine `psql` exit 2, connection refusal, distinct
from W14's blackhole/stall) returns typed 503 `infra_failure`; **(b)** `ledger_current` forced-
dropped on `WORLD B` (a genuine `psql` exit 3, script/data-level, run LAST and destructively —
after every other `WORLD B` check) returns typed 500 `unclassified_failure`, message honest;
**W19** `audit_served.py`'s exit-2 "transport/infrastructure failure" contract, re-witnessed
against the same closed-port lever applied to the audit tool's OWN direct-read leg (the
served-fetch leg still targets `WORLD B`'s live server) — proves A4.4's regression fix (catching
the dedicated `PsqlInfraFailure`/`PsqlUnclassifiedFailure` exceptions instead of the stale bare
`RuntimeError`) restores the contract rather than letting the failure escape uncaught.
A5's additions: **W20** the representability-scan regression, both polarities — a payload
carrying the literal escape TEXT (double-backslash wire encoding, no real NUL codepoint) is now
ACCEPTED through to the kernel, while a real NUL and a real unpaired surrogate (single-backslash
wire encoding) still refuse on the representability axis; **W21** a write-payload integer field
above bigint range (e.g. `actor`) returns a typed 422 naming the field and the bound, never
reaching `psql`'s bigint cast; **W22** the body-read-phase time bound — a raw-socket client (the
same lever the W9 streaming-abort leg's own docstring names as needed and does not otherwise
carry) trickles a declared-length body one byte at a time, slow enough that completing it would
take well over `BODY_READ_TIMEOUT_S=30s`; the server returns a typed 408 within the bound plus a
generous margin, never waiting for the trickle to finish; **W23** pagination on
`/standing/principals` and `/work/items`, both polarities — `limit=1` genuinely truncates a
multi-row result on both routes (proving the pre-A5 silent-no-op is closed), an out-of-range
`limit`/`after_id` is a typed 422 on both, and `/work/items`' id-less synthetic-ordinal fallback
(`row_number() OVER (ORDER BY slug)`) is exercised directly by opening two fixture work items
through the boundary first.

**Concurrent-runner safety (A3.5).** Every scratch world/schema name carries a per-run unique,
pid-derived suffix (`RUN_SUFFIX`); teardown is scoped to the exact suffixed name a run created.
Two independent suite runs against the same toy db no longer collide on an identical scratch
name — witnessed live by running two full suite invocations concurrently against the same host
(both exited 0, no leftover `svcfx%` schemas or roles after either).

## The deprecation duty (spec §6) — autoharn-side finding

Searched this repo for any AUTOHARN-SIDE standing service or documented direct-psql consumer
path a UI-class client would reach for instead of this service. **None exists.** The only
HTTP/ASGI server anywhere in this repository is `serving/boundary_service.py` itself; the
repo-root operator verbs are explicitly NOT the deprecated class (spec §1); the deprecated
class the spec names concretely — "the autoharn-panel FastAPI-side SQL, plus any panel doc
describing direct access" — lives entirely in the separate autoharn-panel repository, which
per the maintainer's own standing rule and this spec's §10.4 is **never touched by this
build**. The deprecation marks themselves (loud-at-invocation, naming the replacement
endpoint, pointing at
[design/FABLE-WORLD-CONTEXT-MIGRATION-CONSULT-2026-07-19.md](../design/FABLE-WORLD-CONTEXT-MIGRATION-CONSULT-2026-07-19.md))
are a separate panel-repo session's item, citing this spec — not a gap in this build.

## License

Public Domain (The Unlicense).
