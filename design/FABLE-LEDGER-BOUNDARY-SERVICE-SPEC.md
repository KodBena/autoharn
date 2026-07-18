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
| `GET /rows/current` | `ledger_current`, id-paginated (`?after_id=&limit=`, ORDER BY id) | the in-force reading |
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
endpoint table of §3 + the four write endpoints of §4 — no other route exists (FastAPI's own
route table IS the enumeration; the witness plan asserts the route count). Axes: read
(views only), write (functions only), refuse (typed, verbatim), capability-absence (typed
refusal, never fallback). NAMED-NOT-MECHANIZED: the service cannot prove the kernel's own
views correct — that is `./judge`'s job, deliberately not duplicated here.

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

## License

Public Domain (The Unlicense).
