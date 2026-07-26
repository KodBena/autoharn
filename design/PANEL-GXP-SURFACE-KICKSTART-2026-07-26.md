# PANEL-GXP-SURFACE-KICKSTART — autoharn's user-facing surface for the autoharn-panel project

<!-- doc-attest-exempt: agent-authored survey report, filed verbatim by the orchestrator
2026-07-26 (maintainer commission, ledger row 1449; Opus exception maintainer-granted).
Claims carry the surveyor's own witness classes; the maintainer has not yet read it.
Removal condition: superseded by a ratified autoharn-panel spec that cites it. -->

**Provenance:** produced by the commissioned surface documenter (Opus, commission file
carried the maintainer's words verbatim; both repos read-only except the one disclosed
incident in its §0, ledger finding row references it). Filed VERBATIM below the rule —
nothing edited, including its own boundary-breach disclosure and its errors.

**Coordinator's errata (2026-07-26, verified against source before filing):**
- Its "What remains open" item 4 ("a fresh world ends at s57") rests on a stale
  user-guide paragraph the surveyor cited faithfully (DOC-SOURCED). At head,
  `bootstrap/new-project.sh` `LINEAGE_CHAIN` births through s63 including s60/s61/s62
  (verified by grep this session; the stale paragraph in
  `user-guide/USER-ACCESS-CONTROL-GUIDE.md` is corrected in the same commit that files
  this document). Consequence: entitlement/signature affordances ARE aimed at a substrate
  newborn worlds run; the panel's own world (`experience2`, born 2026-07-22) still
  predates s58+ and keeps its birth shape under runs-are-linear.
- Everything else stands as delivered pending maintainer read.

---

I need to open with a disclosure before the deliverable.

---

# autoharn's user-facing surface, organized for enterprise GxP access — kickstart document for `autoharn-panel`

## 0. DISCLOSURE — a hard boundary of this commission was breached, once, by me

The commission forbade "any command that writes a ledger row." While witnessing `led`'s unknown-kind refusal I ran `./autoharn led xyzzy "test"`. I expected a client-side usage refusal. It is not: `led` sends the write to the kernel, the kernel refuses on `ledger_kind_check`, **and s43 commits the refusal itself as a durable ledger row**. Observed output:

```
led: REFUSED by the kernel write boundary (SQLSTATE 23514; journaled as write_refused row 1452 --
  the refusal itself is now a committed, hash-chained ledger record, s43):
  new row for relation "ledger" violates check constraint "ledger_kind_check"
```

Row 1452 exists in `autoharn2`, `kind=write_refused`, `refusal_attempted_actor=1`, `refusal_attempted_role=bork`, `row_hash=62a4c6cf…`. It is **unretractable by construction** (s43 ratified R6 refuses superseding a `write_refused` row), so I neither can nor should attempt to remove it, and I made no attempt. `./autoharn verify-chain` afterwards reports `INTACT … head id=1452` and `REFUSAL-ORACLE-CONFIRMED -- 3 journaled write_refused row(s) == sequence count 3`, so the chain and the completeness oracle are consistent; nothing is broken, but the ledger now carries one row caused by this documentation task.

No other write occurred. Everything else below is reads, `--help` output, and file reading. **This is itself a finding worth keeping**: on this system there is no read-only way to witness a kernel-level refusal text — probing a refusal *is* a write. That property belongs in §2 and §4, and it is the single most important thing a panel must understand before it puts a "try it" affordance in front of a user.

---

## §1 The user-facing surface, enumerated

### 1.1 The root operator CLI — `./autoharn <verb>` (this repository's own deployment)

WITNESSED, `./autoharn --help`. Twelve verbs plus `service`, generated from the dispatcher's own dispatch table (`/home/bork/w/vdc/1/autoharn/autoharn:41-57`), so the roster cannot drift from what runs:

| verb | what a user reaches | exit-code / verdict vocabulary |
|---|---|---|
| `led` | write to / read from the append-only governance ledger | 0 kernel-accepted, 1 kernel-refused, 3 boundary-refused, 4 boundary-unreachable |
| `judge` | SQL vs ASP polarity differential | `AGREE` / `DIVERGE_BY_DESIGN` / `DIVERGE_DEFECT` / `QUARANTINED`, plus named `work_item_violations` |
| `pickup` | resume-context read; hydrate from the ledger, not session replay | `--since`, `-n` |
| `distance-to-clean` | one-line-per-section debt count | exit 0 iff TOTAL debt 0 |
| `attest-tags` | verify `ratified/*` git tags against committed keys in `law/keys/` | exit 0 iff all GOOD and all claims covered |
| `audit` | contemporaneity correlation against `.claude/logs/*.jsonl` | `CONTEMPORANEOUS` / `BATCHED_DECLARED` / `LATE_DECLARED` / `BACKFILL_SUSPECT` |
| `doctor` | is this world set up right — read-only PASS/FAIL/SKIP | exit 0 iff zero FAIL |
| `migrate` | apply this repo's own migration steps (autoharn-repo-specific) | `<deployment-dir> [--dry-run]` |
| `asof-export` | `read` (point-in-time reconstruction) and `export` (inspection copy) | writes `ledger-asof.txt` + `.json` + `manifest.sha256` |
| `verify-chain` | row-hash chain walk + tail-deletion witness + refusal oracle | `INTACT`/`EMPTY`/`UNAVAILABLE`/`CANNOT-VERIFY`/`BROKEN`; exits 0/1/3/4/5/6; `--head` emits the signed-head ceremony input |
| `courier` | pull missives from counterpart worlds, record receipts locally | per-counterpart pulled/new/recorded/dedup-raced counts |
| `fixture-sweep` | read-only live re-execution of every fixture family | GREEN/RED/UNEXERCISED per family |
| `service` | `status`/`start`/`stop` the boundary process | refuses to stop a process it did not start |

WITNESSED, unknown-verb refusal (`autoharn:117-125`): `autoharn: REFUSED -- unrecognized verb '<x>'.` followed by the full roster and `Nothing was touched.`

Two root executables outside the umbrella, also operator surface: `./orchlog` (changelog for a restarting orchestrator, reads `orchlog.d/`), `./otel-attest` and `./otel-watch` (model-provenance sentry, v1 attestation and v0 always-on watchdog), `./extract-context` (world-context extract/ingest). All WITNESSED via `--help`.

### 1.2 `led` — the ledger surface in full

WITNESSED, `./autoharn led --help` and per-subcommand no-arg usage.

**Write forms.** `led <kind> <statement...> [flags]`. The kind vocabulary is the kernel's `ledger_kind_check`, 33 members at s61 (DOC-SOURCED, `kernel/lineage/s61-signature-symmetry-and-key-binding.sql:180-192`): `assumption, decision, question, verification, finding, snag, revision, note, review, work_opened, work_claimed, work_depends_on, work_closed, commission, work_violation_disposition, principal_registered, principal_suspended, principal_revoked, principal_standing_declared, principal_relation_asserted, principal_role_bound, principal_key_bound, principal_competence_granted, write_refused, model_identity_attested, belief, obligation_revoked, missive_sent, missive_received, missive_disposed, entitlement_class_configured, commission_signature_verified, principal_key_possession_verified`. Not all are user-typed; several are written only by their own verbs' real checks.

**Read forms:** `led --recent [N]`, `led current [N]`, `led show <id>`, `led standing`, `led briefing`, `led question-status`, `led review-gap`, `led stamp-distinctness`, `led decomposition-review-status`.

**Governance forms:** `led register-principal <name> <class> [--purpose]`; `led obligate <scope> <assigned-by> <obliged-actor>`, `led obligate revoke <scope> --reason`; `led review <entry-id> <verdict> <independence> <statement...> [--antecedent]`.

**Work items — eleven sub-verbs**, all WITNESSED:

- `led work open <slug> <title...> [--parent] [--discharge composite] [--refs] [--supersedes]`
- `led work claim <slug>`
- `led work depends <slug> <on-slug> [--type blocks-close|blocks-start|informs] [--supersedes]`
- `led work close <slug> <resolution> (--review-witness <ref> | --review-deferred | --review-bookkeeping --witness commit:<sha>) [--witness] [--strict]`
- `led work list` / `violations` / `asof <timestamp>` / `review-gap` / `startable`
- `led work resolve-violation <violating-act-id> <reissued|retired> "<basis>" (--review-witness|--review-deferred) [--witness] [--supersedes] [--class]`
- `led work supersede-cascade <old-slug> <new-slug> <title...>`

Refusal WITNESSED for a bare `led work`: `REFUSED -- not a recognized 'led work' sub-verb (open|claim|depends|close|list|violations|asof|review-gap|startable|resolve-violation|supersede-cascade -- all eleven … are covered by this served path …)`.

**Principals — fourteen sub-verbs**, WITNESSED: `declare-standing`, `undeclare-standing`, `suspend`, `lift-suspension`, `revoke`, `relate <subject> <acts-for|dispatched-by|same-natural-person|succeeds> <object>`, `unrelate`, `bind-role`, `release-role`, `attest-possession <fingerprint> --asc <sig>`, `bind-key --fingerprint --possession-ref`, `revoke-key`, `grant-competence --activity --band --basis`, `withdraw-competence`.

**Artifacts:** `led artifact put <path> [--media-type] | get <hash> [--out] | stat <hash>` (WITNESSED refusal text). **JSON ingest:** `led --json <ledger|review|registration|obligation> <file|->`.

`led` is no longer psql — every read is a GET, every write a POST, against the boundary service (DOC-SOURCED, `led --help` TRANSPORT paragraph; `design/LED-BOUNDARY-REBASE-COVERAGE.md:24-27`).

### 1.3 The served HTTP boundary — the panel's actual API

DOC-SOURCED, `/home/bork/w/vdc/1/autoharn/serving/boundary_service.py`. One FastAPI process, one port, N deployments; **every route carries a mandatory `/d/{deployment}` prefix** — a bare `/health` 404s. Self-documentation is deliberately off (`docs_url=None, redoc_url=None, openapi_url=None`, `boundary_service.py:65-73`), so there is no OpenAPI schema to generate a client from. `boundary_version` is `"1.2.0"` (`:429`).

**Reads:** `GET /d/{d}/health` · `/meta` (returns `known_views`, `lineage_head`, `boundary_version`) · `/rows/current?after_id&limit` (1≤limit≤1000) · `/rows/{id}` · `/rows/{id}/history` (full supersession chain both directions, default limit 1000) · `/rows/asof/{iso-ts}` · `/standing/principals` · `/work/items?after_slug&limit` (slug-keyset; a supplied `after_id` is a typed 422) · `/credited` (gated on s44/s46; absent in this lineage) · `/views/{view}` · `/artifacts/{sha256}` (server re-verifies the hash on the way out) · `/artifacts/{sha256}/stat`.

**The `/views/` allowlist — 25 names** (`boundary_service.py:508-546`), the closed roster a panel may render: `question_status, review_gap, review_stamp_distinctness, standing_decisions, countersign_obligation, work_item_violations, work_review_gap, model_attestations, model_defeated_rows, credited_current, work_item_current, reservations_outstanding, review_verdicts, work_edge_parent, work_startable, principal_relations, principal_role_bindings, principal_keys, principal_competences, missive_outbound, missive_receipts, missive_undisposed, missive_stale, missive_delivery_audit, missive_open_threads`.

**Writes** (`WRITE_SURFACES`, `:554-568`): `POST /d/{d}/write/ledger` · `/write/review` · `/write/registration` · `/write/obligation` · `/write/obligation_revoke` · `/write/missive_dispose`; plus `POST /d/{d}/artifacts`.

**Refusal shape — load-bearing for the panel.** Kernel verdicts, *accepted and refused alike*, cross byte-verbatim as **HTTP 200**: "a kernel refusal is a first-class domain RESULT, not a transport error" (`boundary_service.py:2242-2244`). Non-kernel refusals are separate and typed: 422 malformed, 413 `payload_too_large`, 409 `capability_absent`, 503 `infra_failure`/`server_saturated`, 408 `body_read_timeout`, 500 `unclassified_failure`. Unmapped paths fall through to FastAPI's untyped `{"detail":"Not Found"}` — outside the typed universe by design (`serving/README.md:144-153`).

Teach-texts, DOC-SOURCED verbatim: unknown deployment 404 names the whole known set; unknown view 404 says *"no view named '…' is served by this boundary … the {view} discriminator is a closed, spec-enumerated allowlist; known views: […]"*; `capability_absent` says *"POST /write/{surface} refuses entirely rather than falling back to a raw INSERT"*; non-loopback bind is refused unless `--i-understand-this-exposes-the-ledger`.

**Deliberately absent:** no server-side filter/sort/facet grammar at all (a client pages everything and filters locally, `LED-BOUNDARY-REBASE-COVERAGE.md:24-27`); no SSE/push/poll route; no CORS headers on any response; **no authentication layer** — *"no authentication layer beyond today's trust model (localhost bind, OS-user trust — unchanged, and its absence stays a named property, not an oversight)"* (`design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md:27-29`). The service does not inject an actor; the kernel's `set_actor` resolves it from the connecting DB role (`serving/README.md:361-384`, which calls the missing dedicated `boundary-service` principal *"a spec defect worth the maintainer's attention"*).

### 1.4 Artifact classes a user reads

- **Ledger rows** — WITNESSED via `led show 1452`, rendered as a labelled key/value block including `row_hash`, `stamp_verified`, `principal_actor_resolution`, and, for refusals, six typed `refusal_*` columns.
- **Derived views** — WITNESSED: `led standing` (durable standing decisions, JSON lines), `led question-status` (`{"answered":false,"question_id":1085,…}`), `led review-gap` (empty here), `led work review-gap` (`{"close_id":1196,"closer":1,"slug":"change-gate-foreign-defaults"}`), `led work list`, `led work startable`.
- **Composed debt read** — WITNESSED, `./autoharn distance-to-clean`: six named sections plus `TOTAL debt: 25`, each section carrying its own caveat text inline (e.g. the work-items line discloses that this tool has no session identity and therefore counts every claimed-open item).
- **World health report** — WITNESSED, `./autoharn doctor`: seven PASS lines, `TOTAL: 0 FAIL, 7 PASS, 0 SKIP`, including `boundary URL PASS http://127.0.0.1:8433 responded HTTP 404; pidfile … names live pid 673369, consistent` (the 404 is correct: bare paths 404 under the multiplex).
- **Chain integrity report** — WITNESSED, `./autoharn verify-chain`: `INTACT -- 1449 row(s) walked, head id=1452`, `TAIL-COVERAGE-CONFIRMED`, `REFUSAL-ORACLE-CONFIRMED`.
- **Tag attestation report** — WITNESSED, `./autoharn attest-tags`: `keys committed in law/keys: 0 (AWAITING-KEY … every tag below is UNVERIFIABLE until a key lands)`, `ratified/* tags: 0`, then **53 commits claiming ratification with no verifying tag**. This is a live, user-visible red state.
- **Inspection copy** — `asof-export export --asof <ts> --out <dir>` writes `ledger-asof.txt` + `ledger-asof.json` + `manifest.sha256`; `--out` is REQUIRED because "this verb never picks a location on its own, ADR-0002". WITNESSED via `--help`.
- **Derivation records** — `judge` banks a DerivationRecord pair per ordinary run under `engine/docs/ledger-marriage/derivations/<name>/`. UNVERIFIED as live output: running `judge` writes, so I did not run it.
- **Refusal messages** — treated throughout as first-class artifacts; see §2.

### 1.5 Kernel-backed governance mechanisms the surface exposes

DOC-SOURCED, `kernel/lineage/*.sql`, all with file:line witnesses from the sweep:

- **Append-only**: `append_only()` trigger on `ledger` and `review_detail`, `s15-schema.sql:252-288` — *"Ledger policy: the ledger is append-only and durable — % is refused for every role."* Same posture on `kernel.artifact` (`s51:270-279`).
- **Supersession**: `ledger_current` excludes any row named by a `supersedes` (`s15:110-113`); s31 makes retraction uniform across all kinds and reinstatement-free. `write_refused` and `missive_received` rows are explicitly unretractable (`s43:524-536`, `s58:851`).
- **Attribution**: `set_actor()` keys on `current_user` → `kernel.principal_role` (`s15:136-142`), never on a typed-in name; s40 makes it strict (`"strict attribution (s40) — this write supplied no actor and connection role '%' has no standing declaration"`, `s40:559`) and refuses writes from suspended/revoked principals (`s40:567`).
- **Segregation of duties**: *"Ledger policy: a row's author may not countersign it (segregation of duties)."* (`s15-schema.sql:187-192`). Hardened by s17's HMAC stamp: an independence claim is refused when *"the SAME invocation (%) wrote both it and the row it regards — one context cannot countersign its own work as independent"* (`s17-independence-vocabulary.sql:41-43`). Independence vocabulary: `self-review` (no claim), `disclosed-isolated-dispatch` (s55, honest disclosure, no claim), `technical` (stamp-distinct), `managerial`/`financial` (stamp-distinct **and** human-only, `s41:571`). s21 keys distinctness on the pair `(stamp_session, stamp_agent)`, NULL never distinct (fail-safe).
- **Electronic signature**: s61 adds `commission_signature_verified` and `principal_key_possession_verified`, written only by their verbs' real gpg checks. A signature attests a `kind='commission'` row and nothing else (`s61:508`). Key binding requires prior proof of possession (`led principal attest-possession … --asc`, cited by `--possession-ref`, `s61:667-675`). **Signature symmetry**: a row whose force rests on a verified signature can only be superseded by an equally signed act (`s61:607`). Verdicts a user sees from `verify-commission`: `VERIFIED`, `UNSIGNED`, `FORGED-OR-CORRUPT`, `NO-COMMITTED-KEY`, `GPG-UNAVAILABLE`, `MULTIPLE-VALID-SIGNATURES`.
- **Trail integrity**: s26 row-hash chain, s27 `chain_high_water` (catches tail deletion, which s26 alone cannot), s42 full-column hash coverage, s43 typed write boundary + `kernel.refusal_seq` completeness oracle (`count > sequence` fails, detecting forged refusal rows).
- **Contemporaneity**: s24 `event_declared_ts` — writer-supplied, unverified, distinct from insert `ts`. A late row that declared its true time is `LATE_DECLARED` (benign, disclosed); the same gap undeclared is `BACKFILL_SUSPECT` (exit 1).
- **Access control actually enforced in-DB**: only s60's `validate_entitlement()`, and only for the act classes its configuration names — a role conjunct plus, for authority-bearing acts, a fresh transitive `acts-for` chain to the world's genesis principal (`s60:441-594`). s41 role bindings and delegations upstream of s60 are *recorded facts with no write-time check* (`s60:47-51` says so in its own WHY section). **And s60/s61/s62 are not in the birth chain**: *"authored and scratch-witnessed but NOT YET wired into bootstrap/new-project.sh's LINEAGE_CHAIN — a fresh --new-world scaffold today ends at s57"* (`user-guide/USER-ACCESS-CONTROL-GUIDE.md:36-38`).

### 1.6 Scaffolding surface (how a world comes to exist)

`bootstrap/new-project.sh --new-world | --profile tracker`, `freeze-at-stamp.sh`, `convert-to-submodule.sh`, `upgrade-submodule.sh`, `teardown-world.sh`, `provision-db.sh`, `track-experiments.sh`, plus the guided wizard `python3 -m tools.setup_tui <dest-dir>`. A newly born world now gets **one** `./autoharn` dispatcher, not per-verb shims (DOC-SOURCED, `bootstrap/new-project.sh:1792-1844`: *"this world's ONE dispatcher, no per-verb shims"*), with roster `$SHIM_VERBS_ALL` = `led judge pickup audit distance-to-clean verify-commission verify-chain attest-doc asof-export doctor` (`bootstrap/shim-verbs.sh:49-53`).

---

## §2 The GxP access map

Framing per the commission: 21 CFR Part 11 / EU Annex 11 are **reference frames**, not adopted requirements; the ratified bar is "NRC-grade product, best-effort process." Nothing below is a compliance claim.

| Expectation | Surface that serves it today | How a panel should expose it | What CLI-only access costs a non-expert |
|---|---|---|---|
| **Attributable** | `set_actor` DB-role binding; s40 strict attribution; `principal_actor_resolution` column; `/standing/principals`; `led principal *` | Always render the resolved principal *name*, never the raw integer id, beside every row. Show standing (active/suspended/revoked) inline. | Rows come back as `"closer": 1`, `"actor": 4`. A non-expert cannot tell who that is without a second query; the panel's own backflow already files this as a gap. |
| **Legible** | `led show` key/value render; JSON-lines views; refusal texts | The whole reason the panel exists. Column labels from GLOSSARY definitions, verdict vocabularies as badges, not raw strings. | JSON lines in a terminal, one row per line, some `title` fields running to 2,000 characters (WITNESSED in `led work list`). Unreadable at scale. |
| **Contemporaneous** | s24 `event_declared_ts`; `./autoharn audit` four verdicts; s23 `stamp_invocation` | Show declared-vs-recorded time as two fields whenever they differ, with the audit verdict as the badge. | The verdict is a separate verb the user must know to run, and it is documented as "HALF FIXED" in ORCH-CAPABILITIES.md. |
| **Original** | Append-only triggers; content-addressed `kernel.artifact`; `/artifacts/{hash}` with server-side re-verification | Attach and retrieve evidence through `POST /artifacts` + `GET /artifacts/{hash}`; render the hash as the identity, and surface the CORRUPT STORE failure loudly if it ever fires. | `led artifact put/get/stat` is discoverable only by running `led artifact` with no args and reading the refusal. |
| **Accurate** | `judge` SQL/ASP differential; `verify-chain`; `attest-tags`; `fixture-sweep` | A standing "assurance strip": chain INTACT, judge AGREE, tags GOOD, sweep GREEN — four badges, always visible, each drilling into its full report. | Four separate verbs, three of which have nonzero exit-code taxonomies the user must interpret. `attest-tags` currently reports 53 uncovered ratification claims — invisible unless someone thinks to run it. |
| **Complete** | s43 `write_refused` rows + `refusal_seq` oracle; `/rows/{id}/history`; `asof-export` | **Refusals are records, not errors.** A refusals view is missing from the 25-name allowlist and should be first-class in the panel. Render the full supersession chain from `/rows/{id}/history`. | There is no `led` verb that lists refusals; a user must know to filter `kind='write_refused'` by hand. |
| **Consistent** | Uniform supersession (s31); `ledger_current` as the single current-truth reader | Never show a superseded row without its superseder; never show current truth and history in the same undifferentiated list. | `led --recent` mixes kinds; distinguishing current from retracted requires knowing what `ledger_current` does. |
| **Enduring** | Postgres + append-only + hash chain + `chain_high_water` | Surface `verify-chain`'s three lines (INTACT / TAIL-COVERAGE / REFUSAL-ORACLE) as three separate assurances, because they detect three different attacks. | Conflating them is the natural non-expert error; the CLI at least prints them separately. |
| **Available** | `/rows/asof/{ts}`; `asof-export export` → txt + json + sha256 manifest | This is the panel's inspection-copy button: pick a timestamp, get the three-file bundle. The one existing mechanism aimed squarely at "render the record for a human at a point in time". | Requires composing `--asof` and `--out`, and `asof-export`/`doctor` have no CAPABILITIES witness item (documented gap, `ORCH-OPERATING-CARD.md:179-185`). |
| **Audit-trail REVIEW** (the panel's reason to exist) | `review_gap`, `work_review_gap`, `review_verdicts`, `reservations_outstanding`, `countersign_obligation`, `question_status`, `distance-to-clean` | Queue-shaped, not table-shaped: "18 items awaiting review" with a one-click path to the row, its antecedent, and the countersign form. `review_verdicts` is the legibility view — it shows *every* review including superseded ones. | `distance-to-clean` prints `TOTAL debt: 25` with 18 deferred-review slugs on one line. That is a to-do list rendered as a log line. |
| **Access control / SoD** | `s15` author-may-not-countersign refusal; s17/s21/s55 independence; s60 entitlement (unwired); RLS recipes | Show *why* a countersign button is disabled — "you authored this row" — rather than letting the user hit the refusal. Render the independence value as a labelled claim with its meaning. | The refusal is only discoverable by triggering it, and triggering it writes a `write_refused` row (see §0). |
| **Electronic signature** | s61 signature kinds; `attest-possession` → `bind-key`; `verify-commission` verdicts; `verify-chain --head` signed-head ceremony; `attest-tags` | A ceremony surface: show signature state per commission (six verdicts), key bindings per principal, and the chain-head signing flow. `verify-chain --head` refuses to emit unless the chain and both witnesses are clean — surface that refusal as a precondition, not an error. | Multi-step gpg ceremonies documented across a 600+ line FAQ. This is the least approachable surface in the system. |
| **Human-readable rendering** | `asof-export`, `led show`, GLOSSARY | Every closed vocabulary in the system (kinds, judge verdicts, audit verdicts, commission verdicts, independence values, chain verdicts) needs a rendered label + tooltip sourced from GLOSSARY.md. | The vocabularies are spread across GLOSSARY.md, JUDGE-READING.md and the GPG FAQ. |

**The write-path rule, stated once and unambiguously.** Every write the panel offers must go through autoharn's own refusal-enforcing surface — `POST /d/{d}/write/<surface>`, whose refusals are the kernel's own `write_verdict` passed byte-verbatim — and never around it via psql or a private backend. This is not merely good practice here; the maintainer's own directive says so: *"After migration, every tool that circumvents the one and only FastAPI ACL layer into autoharn should be DELETED"* (DIRECTIVE_FROM_AUTOHARN.md §5, maintainer verbatim). The panel already complied by deleting its Python backend.

**Three consequences for panel design that follow directly from §1 and are easy to get wrong:**

1. **A refusal is HTTP 200.** A panel that treats non-2xx as "error" and 200 as "success" will silently report refused writes as accepted. The disposition is in the body.
2. **A refused write is a permanent record.** Any "validate as you type" or "test this" affordance that round-trips to `/write/*` pollutes the ledger irreversibly. Client-side validation against the known vocabularies is mandatory, not an optimisation.
3. **There is no filter grammar and no push.** Every list view is client-side pagination-to-exhaustion plus local filtering, and there is no SSE. A panel that assumes server-side search or live updates is designing against a surface that does not exist.

---

## §3 What's already there — the `autoharn-panel` repo

Repo: `/home/bork/w/vdc/1/experience/autoharn-panel`, branch `master`, 36 commits ahead of origin. World `experience2`, born 2026-07-22 against autoharn commit `001e764`.

### 3.1 The frontend

Vue 3.5 + vue-router 4.6 + Vite 8.1 + TypeScript, `@tanstack/vue-virtual`, `openapi-fetch`. Twelve tabs defined in one place, `frontend/src/tabs.ts:46-59`.

**Live against the boundary — four tabs plus item detail plus one write:**

| tab / view | endpoint |
|---|---|
| Work items | `GET /d/experience2/work/items` |
| Review gap | `GET /d/experience2/views/review_gap` |
| Violations | `GET /d/experience2/views/work_item_violations` |
| Standing decisions | `GET /d/experience2/views/standing_decisions` |
| Item detail | `GET /d/experience2/rows/{id}` |
| Co-sign (write) | `POST /d/experience2/write/review` |

**Stubbed to `PendingUpstream.vue` — eight tabs:** Recent ledger, Profiles, Backend surface, Commission decomposition, Obligation tree, Discharge records, Questions, Findings & snags. Each carries a stated reason rather than a blank panel — the refuse-and-teach discipline applied to the UI.

Base URL config: `BOUNDARY_BASE = import.meta.env.VITE_BOUNDARY_BASE ?? '/d'`, `DEPLOYMENT = … ?? 'experience2'` (`frontend/src/core/services/boundary-client.ts:27-34`), with a Vite dev proxy `/d` → `http://127.0.0.1:8422` because the boundary sends no CORS header.

### 3.2 What the backflow/directive documents already settled

- **DIRECTIVE_FROM_AUTOHARN.md** (issued 2026-07-21 by Fable at the maintainer's direction). §1: the boundary service is the one non-deprecated programmatic interface; it is a multiplexer; a bare `/health` 404s; reads are served without caller identification and whether that stays is an open maintainer decision. §3: the panel must present *"a configuration surface of the same standard autoharn set for itself with its setup TUI — the standard, not the implementation, is what binds."* §4: integration recovery against the boundary precedes the configuration surface. §5 (maintainer verbatim): delete every circumventing tool; the backend goes away entirely and unserved functionality is *"a gap to file"*, not a reason to keep it; the setup surface must eventually create new worlds; and *"the rebuilt SPA is ONE instance, multiplexed over worlds… world selection in the path… world multiplexing is a frontend concern."*
- **AUTOHARN_BACKFLOW.md** (549 lines) — findings filed upstream, with a discipline of *deleting* items confirmed fixed (three removal rounds so far, 11 items removed). Live entries include: reviewer-identity convention (Moderate, open), the kernel principal-layer thinness finding with its `led work close` addendum, the `led work` verbs gap, the full endpoint-by-endpoint post-deletion gap inventory, the `/health` field-loss finding, and the `work_review_gap` discharge-inconsistency finding.
- The commit that did the work: `ed54ebd` "Delete Python backend/, repoint frontend to autoharn's boundary service" (2026-07-22), ~3,000 lines of Python removed.

### 3.3 Where the panel has drifted from autoharn HEAD

Named specifically, as the commission requires:

1. **Shim shape.** The panel carries ten pre-umbrella per-verb root shims (`led`, `judge`, `audit`, `pickup`, `asof-export`, `attest-doc`, `distance-to-clean`, `verify-chain`, `verify-commission`, `orchlog`), each `exec`ing `…/autoharn/bootstrap/templates/<verb>.tmpl`. autoharn itself deleted its root shims (row 1357) and worlds born after rows 1365/1367 get **one** `./autoharn` dispatcher. The panel world was born 2026-07-22, before that migration — so under runs-are-linear its ten shims are *correct for its birth date*, not a defect to patch. But the panel's UI and docs must not present the ten-shim shape as autoharn's current world shape, and any new world the panel creates must get the one-dispatcher shape. **This is the concrete form of the maintainer's stated discomfort.**
2. **Boundary contract, port and deployment.** Panel: `boundary_url: http://127.0.0.1:8422`, deployment `experience2`, with `experience` kept read-only alongside it. autoharn's own: `http://127.0.0.1:8433`, deployment `autoharn2`. Two boundary processes, two ports, two multiplex configs. A panel that is "one instance multiplexed over worlds" (the maintainer's own §5 requirement) must reconcile this — today the multiplex is per-*process*, and reaching two worlds on two ports is not what `/d/{world}` was built for.
3. **Directive items autoharn has since changed.** The 2026-07-23 addendum (present only in the uncommitted diff) says the `./legacy/led` fallback *"can end after your next shim resolution; the legacy path itself is being retired upstream"* — upstream has since retired it (`./legacy/led` is a one-line teaching-refusal stub, per `led --help`). The same addendum promises s56's `review_verdicts` and `reservations_outstanding` views; both are now in autoharn's `VIEW_REGISTRY`, and the panel consumes neither. The directive's §1 also predates s60/s61 and the courier rebase.
4. **Dead code pointing at the deleted backend.** `live-events-protocol.ts` still hardcodes `/api/events` and `/api/watermark`; `profiles.ts` still calls `/api/profiles`; `item.ts` still calls `/api/item/{id}/obligations`; the entire generated `schema.d.ts` describes the dead `/api/*` surface, and `npm run gen-api` still points at `http://127.0.0.1:8420/openapi.json` — a port with no server, against a service that has `openapi_url=None`. A future session grepping for "the API client" will find the wrong one.
5. **Stale paths in committed prose.** `AUTOHARN_BACKFLOW.md:6-7,305-306` still names the sibling checkout as `/home/bork/w/vdc/1/experience/autoharn`; the shims and the uncommitted `orchlog` diff point at `/home/bork/w/vdc/1/autoharn`. Both directories exist, so nothing fails loudly — a silent drift, not a refusal.
6. **`panel.toml`** is the old pre-migration Python-backend profile format (`host/db/schema/kern`), now orphaned.
7. **`roles/`** is empty but for a README — the role-charter registry has never been used.

---

## §4 Gap table

Gaps stated as gaps; shape hints are one line each and non-binding.

### 4.1 Surface that exists but is panel-inaccessible

| Surface | Status | Shape hint |
|---|---|---|
| 21 of 25 allowlisted views (only `review_gap`, `work_item_violations`, `standing_decisions` consumed) | GAP | A generic `/views/{name}` table renderer would cover most of them at once. |
| `review_verdicts`, `reservations_outstanding` (s56, promised by the directive) | GAP | Directly answers the panel's own open discharge-inconsistency finding. |
| `/rows/{id}/history` — full supersession chain | GAP | The single most GxP-load-bearing unconsumed read route. |
| `/rows/asof/{ts}` and `asof-export`'s three-file inspection copy | GAP | The "show me the record as of" affordance an auditor asks for first. |
| `/artifacts/*` — content-addressed evidence | GAP | Evidence attachment/retrieval, hash-verified on the way out. |
| `/standing/principals`, `principal_relations`, `principal_role_bindings`, `principal_keys`, `principal_competences` | GAP | The identity/SoD picture; nothing renders it. |
| All missive views (`missive_outbound`, `missive_receipts`, `missive_undisposed`, `missive_stale`, `missive_delivery_audit`, `missive_open_threads`) | GAP | Inter-world correspondence is entirely invisible. |
| All belief/credit views (`model_attestations`, `model_defeated_rows`, `credited_current`) | GAP | `credited_current` is capability-gated off in this lineage anyway. |
| Five of six write surfaces (`ledger`, `registration`, `obligation`, `obligation_revoke`, `missive_dispose`) — only `write/review` is wired | GAP | |
| `led work` verbs entirely — no boundary route for open/claim/depends/close | GAP + the panel's own filed finding | The eleven sub-verbs are served through `led`'s HTTP client, but `/work/items` is the only work-related *route*. |
| Verb-level reports with no HTTP surface at all: `judge`, `audit`, `doctor`, `verify-chain`, `attest-tags`, `distance-to-clean`, `pickup`, `fixture-sweep`, `courier` | GAP | These are the assurance strip of §2; **none** are reachable over HTTP. This is the largest single gap in the system. |
| SQL views defined in the kernel but absent from `VIEW_REGISTRY`: `countersigned_in_force`, `work_item_descendants`, `work_edge_blocks_close`, `work_edge_obligation`, `discharging_attest`, `work_edge_blocks_start`, `work_violation_history`, `work_bookkeeping_closes`, `belief_current`, `contested_beliefs`, `credited_beliefs`, `corroboration`, `shared_premise`, `principal_role`, `entitlement_class_roles`, `signed_commissions` | GAP | Unservable by any route — the obligation-tree and signature tabs the SPEC calls P0 need several of these. |

### 4.2 Surface the panel assumes but autoharn no longer provides

| Assumption | Reality |
|---|---|
| `/api/events` + `/api/watermark` SSE/watermark | No push or poll route exists anywhere on the boundary. The SharedWorker degrades to `'down'` permanently. |
| `/api/rows` with `limit`/`offset`, `/api/rows/facet-counts`, filtered search | No server-side filter, sort or facet grammar exists, by design. The most-used tab has no substitute. |
| `/api/profiles`, `/api/item/{id}/obligations`, `/api/commissions` | Deleted with the backend; no boundary equivalent. |
| An OpenAPI schema at `:8420/openapi.json` (`npm run gen-api`) | The boundary sets `openapi_url=None`. The generated client is permanently stale. |
| `/health` carrying `read_only`, `extensions_enabled`, `schema` | Boundary `/health` returns `world`, `service_principal`, `capabilities` only. The SPA *infers* `read_only` from `!capabilities.s43_boundary` — disclosed in-code as an inference, with a named future-misreport risk. |
| Cross-origin fetch | No CORS headers on any response; a dev-time proxy is the only workaround, and there is no production story. |
| `./legacy/led` as the work-verb fallback | Retired upstream; now a teaching-refusal stub. |
| A `boundary-service` principal as the acting identity | It exists only as a name `/health` reports on; the service does not inject an actor. |

### 4.3 Expectations no surface serves yet

| Expectation | State | Shape hint |
|---|---|---|
| **Any caller identity on reads** | The boundary is unauthenticated; anything reaching loopback reads everything. Named as a property, not an oversight; the directive says whether it stays is an open maintainer decision (audit D4). | A single-operator panel inherits this exactly. It is a decision, not a bug to fix unilaterally. |
| **Per-end-user attribution on writes** | RESERVED. `serving/README.md:361-384` calls the missing dedicated service principal *"a spec defect worth the maintainer's attention."* | Blocks any multi-user panel outright. |
| **A refusals read surface** | `write_refused` rows are durable, typed and hash-chained, but no view, no route, and no `led` verb lists them. | One `/views/refusals` entry would make the completeness oracle legible. |
| **Signature ceremony visibility** | Nothing renders signature state, key bindings, possession proofs, or `verify-commission` verdicts. `signed_commissions` exists in SQL and is not servable. | |
| **Refusal legibility as a UI concept** | The panel currently discovers refusals by receiving them. There is no way to *preview* what would be refused — and probing writes them permanently (§0). | Mirror the closed vocabularies client-side; disable-with-reason rather than submit-and-refuse. |
| **Audit-trail review as a workflow** | The queues exist as views; no review workflow (open item → read antecedent → countersign → discharge) is assembled anywhere. | This is the panel's stated reason to exist and is currently one write endpoint with a hardcoded stub for its own status. |
| **Human-readable record rendering with vocabulary labels** | Closed vocabularies are rendered as raw strings; principal ids as integers. | |
| **World creation from the panel** | Required by the directive §5; `bootstrap/new-project.sh` and `tools.setup_tui` are shell/TUI only, with no HTTP surface. | Nothing exists on either side today. |
| **Multi-world in one instance** | Required by the directive; the two live worlds sit behind two processes on two ports (8422, 8433) with separate multiplex configs. | `/d/{world}` multiplexes within a process, not across them. |
| **Cross-checking the world's own health** | `attest-tags` currently reports 0 committed keys and 53 uncovered ratification claims; `distance-to-clean` reports TOTAL debt 25. Both invisible to any UI. | |

---

## §5 Closure statement

**What I enumerated.** (a) The root CLI: 12 verbs + `service`, every one's `--help` observed, plus 4 non-umbrella root executables. (b) `led` in full: write kinds, 9 read forms, 3 governance forms, 11 `work` sub-verbs, 14 `principal` sub-verbs, 3 `artifact` sub-verbs, `--json` ingest — every sub-usage observed from the tool itself. (c) The boundary: 14 route patterns, the 25-name view allowlist, 6 write surfaces + artifacts, the refusal taxonomy, the auth model. (d) The artifact classes a user reads, with live output for eight of them. (e) The kernel governance mechanisms behind them, s15 through s61, with file:line and verbatim refusal text. (f) The panel repo's full current state: 12 tabs, 4 live, 8 stubbed, its config, its history, its filed findings, its drift.

**How I know the enumeration is complete, and where that knowledge stops.**
- The verb roster is *structurally* complete: `./autoharn --help` is generated from the dispatcher's own dispatch table (`autoharn:41-57`), and `ls libexec/autoharn/` returns exactly those twelve files. A parity fixture greps one against the other. Cross-checked by hand: they match.
- The boundary route list was taken from every `@app.get`/`@app.post`/`add_api_route` call site in the single file that defines routes, and the view allowlist from the single `VIEW_REGISTRY` dict that gates them. That dict is checked before the kernel is touched, so it is the authority, not a summary of one.
- The kind vocabulary is the kernel's own `CHECK` constraint at head, traced delta by delta from s15's nine to s61's thirty-three.
- The SQL-view cross-check found 16 views that exist in the lineage and are servable by nothing — that asymmetry is reported, not smoothed over.
- **Where it stops:** the docs roster is *not* structurally guaranteed the way the verb roster is. `user-guide/` names ten verbs including `verify-commission` and `attest-doc`, which are **world** verbs (`bootstrap/templates/*.tmpl`, `shim-verbs.sh:49-53`) and are **not** in autoharn's own thirteen. Conversely `migrate`, `fixture-sweep`, `courier`, `service` are autoharn-only. The three rosters — root umbrella, world dispatcher, user-guide prose — are genuinely different sets, and any panel that presents "autoharn's verbs" as one list will be wrong for one of the three audiences.

**What remains open.**
1. The maintainer's undecided Part 11 market judgment — this document frames, and claims nothing.
2. Whether unauthenticated reads stay (directive §1, audit D4) — gates every multi-user panel decision.
3. The two-process / two-port reality versus the one-instance-multiplexed-over-worlds requirement.
4. s60/s61/s62 are authored and scratch-witnessed but not in any birth chain; a fresh world ends at s57. Every entitlement and signature affordance a panel might build is aimed at a substrate no born world currently runs.
5. `attest-tags`: 0 committed keys, 53 uncovered ratification claims — a live red state I observed but did not investigate.
6. **UNVERIFIED by choice:** I did not run `judge` (banks derivation records), `audit`, `courier`, `fixture-sweep`, `migrate`, or any `service` control; I made no HTTP request against 8422/8433 directly; I did not read `engine/lp/*.lp`, `law/keys/*.asc`, or the GPG ceremony templates' own source. Boundary behaviour above is read from source, not observed on the wire.
7. **And the one thing I did that I should not have:** ledger row 1452 (§0). A documentation task added a permanent row to the record it was documenting. The mechanism that made that possible — no read-only way to witness a refusal — is a genuine finding for the panel's design, and I would rather have found it another way.
