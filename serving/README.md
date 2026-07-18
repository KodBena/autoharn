<!-- doc-attest-exempt: freshly authored alongside the serving/ build this same commit, under
     the Fable freeze plan's Sonnet-executes posture (design/FABLE-LEDGER-BOUNDARY-SERVICE-
     SPEC.md's own header carries the identical deferral for the same reason). A fresh-context
     ADR-0017 A:B:C attestation is deferred until the content stabilizes against a maintainer/
     Fable review pass of the build it documents, the same deferral this spec's own build-basis
     document states for itself. -->

# serving/ — the FastAPI outer boundary into an autoharn-managed ledger

**Build basis:** [design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md](../design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md)
(RATIFIED — ledger rows 1471, 1481, 1518), **hardened per Amendment A2** (seven post-build
independent-review findings, adjudicated). Read the spec in full, including A2, before
touching this directory; this README is an operator's pointer into it, not a restatement.

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
| GET | `/standing/principals` | `principal_standing_current` | `s41-identity` |
| GET | `/work/items` | `work_item_current` | `s22-work` |
| POST | `/write/ledger` | `kernel.ledger_write` | `s43-boundary` |
| POST | `/write/review` | `kernel.review_write` | `s43-boundary` |
| POST | `/write/registration` | `kernel.registration_write` | `s43-boundary` |
| POST | `/write/obligation` | `kernel.obligation_write` | `s43-boundary` |

**Capability detection is object existence** (`to_regclass`/`pg_proc`), never a version
literal — the same migrate-detect-drift discipline `bootstrap/templates/led.tmpl`'s own s43/s45
probes use, so a world need not match this service's authoring commit exactly.

## Bounds (A2.2, A2.6, A2.7 — one disclosed discipline, both ingresses)

- **Pagination** (`/rows/current`, `/credited`): `?after_id=&limit=`, **`1 ≤ limit ≤ 1000`**,
  **`after_id ≥ 0`** — both violations are a typed HTTP 422 naming the bound. Ratified spec
  text as of A2.7; A2.6 added the `after_id ≥ 0` half (it previously accepted negatives while
  `limit` was already range-checked — an asymmetry with no reason).
- **Write body size** (`/write/*`): `MAX_WRITE_BODY_BYTES = 1_048_576` (1 MiB), the ONE named
  bound (ADR-0012 P1), enforced at BOTH checkpoints A2.2 names: (a) the **raw request body**,
  before any JSON parsing (Content-Length checked first when the client declared one — refused
  without ever reading the body; the actual byte count otherwise, refused mid-stream, never
  buffered whole); (b) the **re-serialized payload**, before the `psql` subprocess (a payload
  can pass (a) and still fail (b) — e.g. non-ASCII content whose `json.dumps`-default
  `\uXXXX` escaping expands past its raw UTF-8 size). Either checkpoint returns HTTP 413:
  `{"disposition": "payload_too_large", "limit_bytes": 1048576, "observed_bytes": <n>, "message": "<teach-text>"}`.
  1 MiB is generous for any ledger payload and comfortably under the `psql`-argv wall
  (`ARG_MAX`) the pre-hardening build crashed into on a ~3 MB payload.

## Infrastructure failure (A2.4)

A `psql` infrastructure failure (an unreachable world, a connection refusal, a nonzero exit
that is not a kernel verdict) is typed, not a bare 500: HTTP 503,
`{"disposition": "infra_failure", "message": "<generic — no SQL, role, schema, or stack>"}`.
One `RuntimeError` exception handler on the FastAPI app is the single home for this
translation (ADR-0012 P1) — every route inherits it, not a per-route try/except. The full
`psql` stderr is logged server-side (stderr) for operator diagnosis; it never reaches the
client.

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

Covers spec §8's W1–W7 plus A2's W9–W12 live; **W8 (the panel-side deprecation-mark
emission) is UNEXERCISED by construction** — that legacy path lives in the separate
autoharn-panel repository, which this build never touches, per the spec's own §10.4
("panel-side is a separate session's item citing this spec"). A2's additions: **W9** an
oversized write body at both A2.2 checkpoints (typed 413 both times, server stays alive,
`/health` still answers afterward); **W10** `/health` on a pre-s40 chain (200, null
`service_principal`, no 500); **W11** the s41/s22 capability gates' PRESENT leg (a chain
carrying both views) and ABSENT leg (a chain carrying neither — `WORLD NOCAP`, truncated
before s22); **W12** the route-table closure assertion, now against `app.routes` in-process
(A2.1 disabled the OpenAPI self-report the pre-hardening witness relied on).

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
