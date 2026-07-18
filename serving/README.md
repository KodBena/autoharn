<!-- doc-attest-exempt: freshly authored alongside the serving/ build this same commit, under
     the Fable freeze plan's Sonnet-executes posture (design/FABLE-LEDGER-BOUNDARY-SERVICE-
     SPEC.md's own header carries the identical deferral for the same reason). A fresh-context
     ADR-0017 A:B:C attestation is deferred until the content stabilizes against a maintainer/
     Fable review pass of the build it documents, the same deferral this spec's own build-basis
     document states for itself. -->

# serving/ — the FastAPI outer boundary into an autoharn-managed ledger

**Build basis:** [design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md](../design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md)
(RATIFIED — ledger rows 1471, 1481, 1518). Read it in full before touching this directory;
this README is an operator's pointer into it, not a restatement.

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

## Endpoint table (spec §3, §4 — fixed; the route table itself IS the enumeration, spec §9)

| Method | Path | Serves | Capability gate |
| --- | --- | --- | --- |
| GET | `/health` | world name, capability manifest, this service's registered principal name | none |
| GET | `/rows/current` | `ledger_current`, id-paginated (`?after_id=&limit=`) | none |
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
Transport-level failures (malformed JSON, a non-object body) are FastAPI's own 422, loud.

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

Covers spec §8's W1–W7 live; **W8 (the panel-side deprecation-mark emission) is UNEXERCISED
by construction** — that legacy path lives in the separate autoharn-panel repository, which
this build never touches, per the spec's own §10.4 ("panel-side is a separate session's item
citing this spec").

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
