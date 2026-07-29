**Provenance:** produced by the commissioned fresh-eyes surveyor (Opus, 2026-07-28), the
anchoring-free second variant the maintainer requested alongside the delta survey
([PANEL-GXP-SURFACE-UPDATE-2026-07-28.md](PANEL-GXP-SURFACE-UPDATE-2026-07-28.md)). The two are designed to be read against each
other: this one derives the surface from primary sources alone. The text below now
carries LEGIBILITY REPAIRS from an [ADR-0017](../law/adr/0017-the-zero-context-reader.md) +A:B:C loop (2026-07-28: pre-review pass,
then blind-round-1 repairs) — a "Vocabulary and citation conventions" block, resolving
links, and bracketed editorial notes; no factual claim, verdict, or table value was
altered, with two disclosed exceptions from blind round 1: an authoring-residue line
("I have what I need. Composing the report."), the COORDINATOR'S OWN extraction
artifact and never the surveyor's prose, was deleted; and the witness-class list
gained a bracketed editorial note naming the UNEXERCISED class §5 uses but the
original list omitted, following the same-day
[PANEL-GXP-SURFACE-KICKSTART-2026-07-26.md](PANEL-GXP-SURFACE-KICKSTART-2026-07-26.md)
precedent.

**Vocabulary and citation conventions (added for the zero-context reader):**
- **GxP** — the family of "Good x Practice" life-science regulations (GMP manufacturing,
  GLP laboratory, GCP clinical, …) whose computerized-systems expectations frame §2. Used
  as a reference frame only, never a compliance claim (stated explicitly in this
  document's own framing note above).
- **ALCOA+** — the data-integrity acronym behind §2's expectation column: attributable,
  legible, contemporaneous, original, accurate, plus complete, consistent, enduring,
  available.
- **sNN** (s43, s58, s60, …) — the Nth numbered kernel migration delta, one file each
  under `kernel/lineage/`; a world's Postgres schema is built by applying them in order
  at birth (its **birth chain**).
- **SoD** — segregation of duties (one actor may not both author and countersign the
  same record). **HMAC** — the keyed hash the kernel attaches to a write to bind it to
  the session/agent pair that made it; a tamper-evidence stamp, not an authentication
  credential. **CORS** — cross-origin resource sharing, the browser policy that blocks a
  page from one origin fetching another origin's API without an explicit response
  header. **SSE** — server-sent events, a server-push protocol; this system has none.
  **SSOT** — single source of truth. **TUI** — text user interface (`tools/setup_tui`,
  the scaffolding wizard). **GUC** — a PostgreSQL "Grand Unified Configuration" session
  variable, the mechanism the boundary service uses to carry a resolved identity into a
  request's DB session. **NRC** — the U.S. Nuclear Regulatory Commission; "NRC-grade"
  names an assurance register this project's own ratified bar borrows as a comparison,
  not an NRC compliance claim.
- **clingo** — the Answer Set Programming solver `judge` runs alongside a direct SQL read
  of the same ledger data, to independently re-derive the same views and check the two
  agree; `judge`'s closed verdict vocabulary is `AGREE` / `DIVERGE_BY_DESIGN` /
  `DIVERGE_DEFECT` / `QUARANTINED` (only the first two appear in this document's prose).
- **`SPEC.md` / `BACKLOG.md` / `AUTOHARN_BACKFLOW.md`** — files of the LIVE
  panel checkout (§3.2, `/home/bork/w/vdc/2/autoharn-panel`), not the §3.1
  submodule; `FABLE-MISSIVES-KERNEL-SPEC.md` and `JUDGE-READING.md` and
  `s-history.md` live in THIS repository (design/ and root respectively).
  **`LED_ACTOR`** — the environment variable `led` reads for its acting
  identity. **"Served" vs "legacy"** templates (§1.1's table) — a served
  template talks to the HTTP boundary; a legacy template talks direct psql.
- **The coordinator** — the orchestrating session that commissioned this survey and
  filed it; the surveyor is a separate, context-free instance. **Missive** — a message
  one world sends another through the kernel's typed substrate (sent/received/disposed
  states; §1.4's views read them). **seen-red/** — this repository's bank of
  red-first fixtures (each family witnesses the failing state before the fix, kept
  runnable). **P0/P1** — the panel SPEC.md's own priority tiers (P0 highest).
  **`LED_BIN`** — the retired panel backend's subprocess path to the `led` CLI,
  explained where §3.1 describes that backend. **"Commission row 168 part b"** — the
  second lettered part of the commission recorded at ledger row 168.
  **`COMMISSION-PANEL-GXP-SURFACE-FRESH.md`** — the commissioning prompt, an
  untracked session file per this project's ephemera rule, not in this tree.
- **A `C<N>` COLLISION WARNING (added at round 3):** this document uses `C<N>`
  for TWO unrelated numbering axes — the ADR-0019-appendix clauses below
  (C1–C29, cited in §2.0–§2.2) and this document's OWN gap-table row ids in §4.C
  (C1–C15, alongside §4.A's A-rows and §4.B's B-rows). The numbers overlap;
  resolve by section: a bare C-cite inside §2 is an ADR clause, inside §4/§5 it
  is a gap-table row.
- **C1–C29** — the numbered clauses of [ADR-0019's appendix](../law/adr/0019-appendix-ui-proscriptions.md)
  (UI proscriptions); the clauses this document actually cites carry a parenthetical
  gloss at first use (most in §2.0/§2.1; C29's is in §2.2); the rest of C1-C28 are
  cited only as the range and are not individually glossed here.
- **ADR-NNNN** — an Architecture Decision Record under `law/adr/`; specific numbered ADRs
  named in prose below are linked at their first occurrence, with one exception: bare
  "ADR-0019" is left unlinked throughout, because this document's own finding C14 (§4.C)
  reports that two files in this repository currently share that number and which one a
  bare citation means is an open, unresolved ambiguity — resolving it here would assert a
  fact this pre-review did not verify.
- **GLOSSARY.md**, **README.md**, **ORCH-CAPABILITIES.md** — this repository's root-level
  term dictionary, top-level readme, and operator capability ledger, resolving to
  [GLOSSARY.md](../GLOSSARY.md), [README.md](../README.md), and
  [ORCH-CAPABILITIES.md](../ORCH-CAPABILITIES.md) respectively, wherever named bare below.
- Plain code-formatted paths (`serving/boundary_service.py:2242-2244`) resolve from this
  repository's root, matching the sibling kickstart document's own convention.
- **Kernel** — this project's append-only decision-ledger engine (the Postgres schema,
  functions, and refusal logic built from `kernel/lineage/`), NOT an operating-system
  kernel; **the boundary service** — the one HTTP layer over it (`serving/`, one
  process, port 8433 here), fully described in §1.3 below; **psql** — PostgreSQL's
  command-line client, so "direct psql" means a verb talks to the database itself,
  bypassing the boundary; **actor / principal** — the same entity (the ledger's unit
  of acting identity); "principal" is the noun the identity views use, "actor" the
  ledger column; **world / deployment** — one world (a born ledger instance) is served
  as one deployment under the boundary's `/d/{name}/` multiplex.
- Citations of the form "panel `BACKLOG.md`, entry N" are POSITIONAL into a mutable
  file in the sibling repository — specifically the LIVE panel checkout of §3.2
  (`/home/bork/w/vdc/2/autoharn-panel`, git remote `autoharn-gui`), NOT the §3.1
  `tools/autoharn-panel` submodule; both answer to the name "autoharn-panel" (the
  collision §4.C C15 reports) — they index that file as it stood at survey time
  (2026-07-28) and may dangle after it is reordered; retained verbatim as surveyed.

---

**Erratum (2026-07-28, post-filing — the pagination class fix):** this survey's refusal-taxonomy claims ('409 `capability_absent`') were true when surveyed and are no longer a 1:1 mapping — `GET /views/{view}` can now also answer 409 with `disposition: "tie_group_too_large"`. Branch on the body's `disposition` field, never on the status code alone; the living contract home is [serving/README.md](../serving/README.md)'s refusal-taxonomy section.

---

# autoharn's user-facing surface — a complete enumeration, organized for GxP access

**Independent second-Opus survey, 2026-07-28.** Commission: `COMMISSION-PANEL-GXP-SURFACE-FRESH.md`. Sources: primary only — the two repos' files, `--help` output, and read-only `./autoharn led` queries. **Independence clause honored:** no file whose name contains `PANEL-GXP` or `KICKSTART` was opened; `design/PANEL-GXP-SURFACE-KICKSTART-2026-07-26.md` and `design/PANEL-GXP-SURFACE-UPDATE-2026-07-28.md` appeared in a directory listing and were not read.

**Boundaries respected:** no writes to either repo; no ledger row written; the boundary service on 8433 was never started, stopped, restarted, or reconfigured; no refusal was probed and no verb was fed deliberately bad input — every refusal text below is read from source or from `--help`. `judge`, `audit --retain`, and `doctor` were **not run**: `judge` banks a DerivationRecord pair *into the repo tree* (a write), and `doctor`/`audit` were held back as outside the explicitly enumerated permission. Their surfaces below are DOC-SOURCED.

**Witness classes:** WITNESSED (observed output shown) · DOC-SOURCED (file:line or command-output + quote) · GAP (the absence itself is the claim) · UNVERIFIED (with blocker) *[editorial addition, repair pass: the closure statement in §5 also uses UNEXERCISED (a surface deliberately not invoked, with the blocker stated) — a fifth class the original list omitted]*.

One framing note the whole document is built on: **21 CFR Part 11 and EU Annex 11 are reference frames here, never adopted requirements.** The project's own ratified bar is "NRC-grade product, best-effort process." Where §2 says "an enterprise GxP user needs to reach X," that is a statement about what a user needs to *see*, not a compliance claim. Autoharn's own prior Part 11 mapping (`vestigial_documentation/design/FABLE-21CFR11-STANDING-ASSESSMENT.md`, 453 lines, verdicts `WITNESSED-BY-DESIGN`/`PARTIAL`/`ABSENT`/`BUREAUCRACY-CLASS`) exists and is *vestigial*, i.e. history — I cite it as a frame, not as current standing.

---

## §1 The user-facing surface, enumerated

### 1.1 The CLI roster — 13 verbs plus `service`

WITNESSED, `./autoharn --help`:

> ```
> usage: autoharn <verb> [args...]
> verbs:
>   led  judge  pickup  distance-to-clean  attest-tags  audit  doctor
>   migrate  asof-export  verify-chain  courier  service  fixture-sweep  dispatch
> ...
> The thirteen-verb-plus-service roster above is generated from this dispatcher's own dispatch
> table -- it cannot drift from what actually runs (design/FABLE-AUTOHARN-UMBRELLA-CLI-SPEC.md §1).
> ```

Cross-checked (DOC-SOURCED, `autoharn:41-59` dispatch table vs `ls libexec/autoharn/`): 13 table entries have a `libexec/autoharn/<verb>` file; `service` is handled inside the dispatcher. Parity is mechanically gated (`seen-red/umbrella-cli-dispatch-parity`, cited at `autoharn:38-40`).

**Which data path each verb uses** — this is the single most load-bearing structural fact for a panel, and it is not stated in any one place today (DOC-SOURCED, per-verb `libexec/` and `.tmpl` reads):

| Verb | Reaches data via | Panel-reachable? |
|---|---|---|
| `led` | HTTP boundary (`bootstrap/templates/led.tmpl`, served) | yes |
| `courier` | HTTP boundary (`libexec/autoharn/courier:1-100`) | yes |
| `dispatch` | HTTP boundary (`tools/dispatch_mechanics.py:76` imports `boundary_cli_client`) | yes |
| `pickup` | **direct psql** — root uses `legacy-pickup.tmpl` (`libexec/autoharn/pickup:20`) | no |
| `distance-to-clean` | **direct psql** — root uses `legacy-distance-to-clean.tmpl` | no |
| `asof-export` | **direct psql** — root uses `legacy-asof-export.tmpl` | no |
| `doctor` | **direct psql** (`doctor.tmpl:107` `_psql`) | no |
| `verify-chain` | **direct psql** (`verify-chain.tmpl:219` `_psql_json_rows`) | no |
| `judge` | **direct psql + clingo** (`engine/ledger_differential.py:121`) | no |
| `audit` | **direct psql** (`engine/contemp_audit.py`) | no |
| `migrate` | direct psql (schema migration) | no |
| `attest-tags` | git + gpg only, no DB | n/a |
| `fixture-sweep` | subprocess sweep over `gates/fixture_census.py` | n/a |
| `service` | process control (`serving/ensure_running.py`) | n/a |

**Three of thirteen verbs are served; eight read Postgres directly.** Everything in the psql column is structurally invisible to any HTTP client.

Autoharn's own root roster ≠ the roster a scaffolded world gets. Worlds get **ten** verbs (DOC-SOURCED, `bootstrap/new-project.sh:1964-1965`): *"the ten verbs (led, judge, pickup, audit, distance-to-clean, verify-commission, verify-chain, asof-export, attest-doc, doctor)."* So `verify-commission` and `attest-doc` exist **only in worlds**, and `migrate`/`fixture-sweep`/`dispatch`/`attest-tags`/`courier`/`service` exist **only in autoharn's own repo**.

### 1.2 `led` — the full grammar (the surface a panel must mirror or route through)

DOC-SOURCED, `bootstrap/templates/led.tmpl:3-41` (the `--help` text) and `:3014-3254` (`main()`'s dispatch), read in full.

**Reads:** `--recent [N]` · `current [N]` · `show <id>` · `question-status` · `review-gap` · `stamp-distinctness` · `standing` · `work list [--all]` · `work violations` · `work asof <ts>` · `work review-gap` · `work startable` · `missive list` · `artifact get|stat` · `decomposition-review-status` · `briefing` · `principal` (usage).

**Writes:** the generic `led <kind> <statement...>` path · `register-principal` · `obligate` / `obligate revoke` · `review <entry-id> <verdict> <independence>` · `work open|claim|depends|close|resolve-violation|supersede-cascade` · `artifact put` · `missive dispose` · the 14 `led principal *` sub-verbs · `--json <ledger|review|registration|obligation> <file|->`.

`led principal`'s 14 sub-verbs, verbatim from `led.tmpl:434-455`:
`declare-standing` · `undeclare-standing` · `suspend` · `lift-suspension` · `revoke` · `relate <subject> <acts-for|dispatched-by|same-natural-person|succeeds> <object>` · `unrelate` · `bind-role` · `release-role` · `attest-possession <fingerprint> --asc <sig>` · `bind-key --fingerprint --possession-ref` · `revoke-key` · `grant-competence --activity --band --basis` · `withdraw-competence`.

**Twelve shared flags**, front-anchored only (`led.tmpl:2965-2973`): `-f` `-e` `--supersedes` `--amends` `--amends-scope` `--answers` `--refs` `--concern` `--evidence` `--confidence` `--event-time` `--signature-witness`. **`--signature-witness` (s61) is absent from `led --help`'s usage block** — a small but real documentation gap (GAP).

The flag-side asymmetry is itself a witnessed usability hazard the system already teaches about. WITNESSED, `./autoharn led briefing`:

> ```
> 2. Flag-order asymmetry. Generic ledger flags go BEFORE the kind word: `./led --refs row:N
>    decision "..."`. `led work <sub>` flags go AFTER the slug/title/verdict instead...
>    A flag placed on the wrong side of that boundary is REFUSED, never silently swallowed
> ```

Same output carries the segregation-of-duties rule an operator otherwise discovers by tripping it:

> ```
> 3. Same-actor countersign (segregation of duties). `led review <id> attest ...` is refused
>    when the countersigning actor authored the row it regards -- keyed on actor/principal
>    identity alone, unconditionally, regardless of the independence value chosen...
> ```

**A material read-surface limit, WITNESSED on the first line of `./autoharn led --recent 3`:**

> ```
> led --recent: NOTE -- this rebase's --recent reads /rows/current (in-force rows only, no
> raw-ledger route exists on the boundary, and no legacy recovery path survives legacy-led.tmpl's
> own retirement) -- the superseded-inclusive raw read is not available from any CLI in this
> repository anymore.
> ```

This is the audit-trail-review gap in one sentence: **no CLI in this repository can list superseded rows.** They remain reachable per-row (`led show <id>` → `GET /rows/{id}`, any status) but there is no listing.

### 1.3 The HTTP boundary — 21 route shapes

DOC-SOURCED, `serving/README.md:120-166` (the endpoint table) plus counts verified directly against `serving/boundary_service.py`.

**Reads (15):** `GET /health` · `/rows/current` · `/rows/{id}` (*"one row, any status"*) · `/rows/{id}/history` (*"the row's full supersession chain (both directions), each hop carrying its own `superseded_by`"*) · `/credited` · `/standing/principals` · `/work/items` · `/views/{view}` · `/rows/asof/{ts}` · `/meta` · `/kinds` · `/artifacts/{hash}` · `/artifacts/{hash}/stat`.

**Writes (6 + 1):** `POST /write/ledger` `.../review` `.../registration` `.../obligation` `.../obligation_revoke` `.../missive_dispose` (verified: exactly six entries in `WRITE_SURFACES`), plus `POST /artifacts` on its own route.

**`VIEW_REGISTRY` — exactly 25 views** (verified by direct count):
`question_status` `review_gap` `review_stamp_distinctness` `standing_decisions` `countersign_obligation` `work_item_violations` `work_review_gap` `model_attestations` `model_defeated_rows` `credited_current` `work_item_current` `reservations_outstanding` `review_verdicts` `work_edge_parent` `work_startable` `principal_relations` `principal_role_bindings` `principal_keys` `principal_competences` `missive_outbound` `missive_receipts` `missive_undisposed` `missive_stale` `missive_delivery_audit` `missive_open_threads`.

**The refusal taxonomy a client can meet** (DOC-SOURCED, `serving/README.md:165-346`), all typed, all JSON, none a bare 500:

| Disposition | HTTP | Where |
|---|---|---|
| `write_verdict` `accepted`/`refused` (kernel teach-text, byte-verbatim) | **200** | `README.md:344-346` — *"a kernel refusal is a first-class domain result carrying kernel-authored teach-text, never a transport error"* |
| `unknown_view` (names the known set) | 404 | `/views/{view}` |
| `unknown_deployment` (body carries `known`) | 404 | `/d/{x}/...` |
| `capability_absent` + `capability` name | 409 | `README.md:335-342` — flagged as *"a spec defect resolution, not a specified shape"* |
| pagination/value/id-domain violations | 422 | bounds section |
| `payload_too_large` + `limit_bytes` + `observed_bytes` | 413 | `README.md:268` |
| `body_read_timeout` (30s) | 408 | `:284` |
| `server_saturated` + `inflight_limit: 24` | 503 | `:295` |
| `infra_failure` | 503 | `:310` |
| `unclassified_failure` | 500 | `:320-333` |
| untyped `{"detail":"Not Found"}` / `405` | 404/405 | `:165-176`, explicitly outside the typed universe by construction |

**Multiplexing:** every route is prefixed `/d/{deployment}/`. One process on `127.0.0.1:8433` currently serves four deployments — `autoharn2`, `autoharn3`, `experience3`, `experience4` (DOC-SOURCED, `boundary-multiplex.toml`, and cross-confirmed by the panel's own live check note at `frontend/src/core/state/deployment.ts:20-27`).

### 1.4 Artifact classes a user reads

1. **Ledger rows.** WITNESSED, `./autoharn led show 168` — 14 populated columns rendered as `key : value`:
   ```
   id : 168 · ts : 2026-07-28T19:36:03.844139+02:00 · kind : commission · actor : 1
   status : open · session : main · row_hash : 9e1b003d… · stamp_ts : 1785260163
   statement : Maintainer commission 2026-07-28 (second batch)…
   stamp_hmac : a0593864… · stamp_agent : main · stamp_session : 332dda3a-…
   stamp_verified : True · stamp_invocation : ec976229-… · principal_actor_resolution : declared-default
   ```
   Note `actor : 1` — a raw integer with no name resolution at this surface.

2. **View rows**, rendered as one JSON object per line. WITNESSED, `./autoharn led work list`:
   ```
   {"claimant": null, "effective_state": "open", "parent_slug": null, "resolution": null,
    "review_disposition": null, "review_ref": null, "slug": "belief-doubt-tier", "state": "open",
    "title": "re-asserted from autoharn2: re-asserted from autoharn1: opt-in dou…
   ```

3. **The `pickup` resume brief.** WITNESSED, `./autoharn pickup -n 2` — ten `### SECTION:` blocks (`STANDING-DECISIONS`, `IN-FORCE-DECISIONS`, `OPEN-QUESTIONS`, `REVIEW-DEBT`, `RECENT-CHANGES`, `GIT-STATE`, `RESOURCES`, `ESTIMATES`, `TAXONOMIES`, …), most rendered as **raw psql ASCII tables including the `SET` role echo**, truncated at terminal width:
   ```
   ### SECTION: IN-FORCE-DECISIONS
   SET
    id  |    kind     |
   -----+-------------+---------------------------------------------------------------
    170 | work_opened | work_opened: work-role-doctrine-faq -- Careful FAQ treatment of…
   (2 rows)
   ```
   Also witnessed, the one imperative line in the whole surface: `ACTION REQUIRED: 5 more standing decision(s) omitted -- run './led standing' NOW to read them before proceeding.`

4. **Missives.** WITNESSED, `./autoharn led missive list` → `led missive list: no undisposed missives.`

5. **DerivationRecords** — banked per `judge` run under `engine/docs/ledger-marriage/derivations/<world>/<ts>_<hash>/` as four files (`derivation.json`, `edb.lp`, `asp_atoms.txt`, `sql_atoms.txt`). WITNESSED content of one `derivation.json`: `verdict: "AGREE"`, `only_asp: []`, `only_sql: []`, and two engine records each carrying `engine`/`version`/`input_basis`/`input_hash`/`program_hash`/`output_hash`. The two `output_hash` values are identical — that identity *is* the verdict.

6. **Attestations** — `attestations/doc-legibility-attestations.jsonl` (A:B:C fresh-context doc reviews), plus `code-review-findings.jsonl`, `pre-review-log.jsonl`. WITNESSED current state, `attestations/README.md:16-18`: *"## Current state: empty — No attestation has been recorded here yet. This is the honest starting state, not an error."*

7. **AS-OF inspection copies** — `asof-export export` writes a three-file set (txt + json + sha256 manifest). Its own docstring names its provenance in Part 11 vocabulary (`legacy-asof-export.tmpl:3`): *"the ledger-wide AS-OF read plus the §11.10(b) inspection-copy export verb."*

8. **World configuration.** WITNESSED: `deployment.json` (6 keys: `db host schema kern role name` + `boundary_url`/`boundary_deployment`), `.autoharn-world.json` (`world`, `run`, `born`, `autoharn_commit`, `schema`), `features.json` (6 feature switches), `courier.toml`, `boundary-multiplex.toml`.

9. **The apparatus switchboard** — `.claude/apparatus.json`: **15 mechanisms**, each `off`/`observe`/`enforce` (WITNESSED file contents): `change_gate` `permit_to_work` `decomposition_review` `stamp_intercept` `clean_exit` `demurral_detect` `mutation_observer` `delegation_observer` `doc_shapes_gate` `read_observer` `bash_completion` `error_recurrence` `doc_legibility_critic` `doc_attestation` `sql_block`, plus a `standing_decisions` policy block. Two carry a `cost_note` **in the config next to the switch** because they spend real money — the standing mandate is *"no world silently bills its operator"* (DOC-SOURCED, `user-guide/USER-CONFIGURATION.md:177-179`).

10. **Refusal messages**, of three kinds: kernel teach-text (recorded permanently — the s43 refusal journal), boundary typed dispositions (§1.3), and CLI-local refusals (~40 in `led.tmpl` alone). One representative, `led.tmpl:3089-3091`: *"led obligate revoke: REFUSED -- --reason is MANDATORY (kernel/lineage/s57-obligation-revocation-event.sql: a revocation is a maintainer act, and its stated ground is part of the record)."*

11. **`governed_files.json`** — the change-gate's pattern list; **`roles/`**, **`keys/`**, **`legacy/`** (four teaching-refusal or recovery stubs).

### 1.5 The other user-facing surfaces (not CLI, not HTTP)

- **The setup wizard** — `python3 -m tools.setup_tui`. DOC-SOURCED, `tools/setup_tui/app.py:2-8`: *"Interactive mode is Textual, full stop -- `tools/configtree`'s hierarchical configuration editor (a sidebar `Tree` of the ENTIRE configuration, a form pane per section, dependency-as-data blocking, a commit node)… If `textual` is not importable, this REFUSES with the install command -- there is no fallback UI to maintain."* Closed exit vocabulary: 0 clean · 1 pre-flight refusal · 2 commit boundary halted · 3 `--from-config` answers rejected · 130 interrupted. `--dry-run` keeps read probes live: *"a rehearsal that fakes its reads is a lie, not a rehearsal."* **This is already the ADR-0019 genre shape** (tree + form pane + one commit).
- **The hook layer** — 18 scripts in `hooks/`, the surface where a refusal actually meets a user mid-edit.
- **`orchlog`** (commit-ordered landing notes), **`otel-attest`**, **`otel-watch`**, **`extract-context`** — four root executables outside the umbrella.
- **The documentation corpus** — 27 files in `user-guide/` with an audience-prefix convention (`USER-` adopter · `ORCH-` orchestrator · `MAINT-` maintainer), `GLOSSARY.md` (62 defined terms), `README.md` (564 lines), `ORCH-CAPABILITIES.md` (1542 lines, 42 numbered witnessed capabilities).

---

## §2 The GxP access map

For each surface item: which expectation it serves, how a user-friendly panel should expose it, and what CLI-only access costs a non-expert.

### 2.0 Four laws that bind the panel before any screen is drawn

These are not background — they are constraints on the deliverable, and three of them are typed refusals, not review items.

- **ADR-0019 Rule 1/2 — genre convention is the spec.** *"A spec or build for a UI in such a genre inherits the dominant idiom as its default in full… any UI structure the genre's reference exemplars do not exhibit is presumptively wrong."* And: *"A UI spec that names no genre and no reference exemplars is incomplete and may not be frozen."*
- **ADR-0019 Rule 3 — one home per fact on screen**, enforced as a **type error at UI start**: *"a duplicated projection of one fact is a TYPE ERROR, refused loudly at UI start, naming the fact and every section claiming it."*
- **ADR-0019 Rule 4 — data topology is the default information architecture.** *"an entity gets one home surface; a dependent (foreign-keyed) entity is created and edited within its parent's context, master-detail, never as a sibling flat list; an association renders as a selection over the entities it joins, never as free text; a derived projection gets a read surface and no editor; storage artifacts (junction mechanics, hash chains, lineage columns) are owed no surface at all."*
- **ADR-0019-appendix C1–C29**, four enforcement tiers, Synopsis = required reading. The ones that bite a ledger panel hardest: **C6** (loading/error/empty/genuine-zero/no-data never collapsed — *"A dashboard showing `0` when it means 'feed down' is a defect at the severity of showing wrong data"*), **C7** (as-of time + distinct stale state), **C5** (success only from a durable ack), **C10** (irreversible action guarded), **C27** (auto-refresh yields to interaction), **C13** (typed semantic elements, never layout inside a string), **C18** (no colour-only meaning).

And one more, which governs whether the panel is allowed to *reformat* a ledger row at all — **[ADR-0020](../law/adr/0020-meaning-preservation-witness.md)**: *"Any operation that migrates, schematizes, summarizes, or re-renders authored content carries a cold-read meaning-preservation witness… **re-rendering content into a new presentation vocabulary**"* is explicitly in scope. A panel that renders a statement truncated, badged, or summarized is performing a transformation under this ADR.

### 2.1 The map

| Surface item | GxP expectation served | How a panel should expose it | What CLI-only costs a non-expert |
|---|---|---|---|
| Ledger rows (`/rows/current`, `/rows/{id}`) | ALCOA+ **attributable, original, legible, enduring**; audit trail (§11.10(e) frame) | Board list + item view; statement never elided; `actor` resolved to principal name; `stamp_verified` as glyph+label (C18), not colour | `led --recent` prints one JSON line per row, terminal-truncated; `actor: 1` is an unresolved integer; no filtering grammar exists client- or server-side |
| `/rows/{id}/history` — the supersession chain | **Audit-trail REVIEW** — the panel's whole reason to exist; "changes shall not obscure previously recorded information" | The chain rendered *as a chain*, both directions, each hop's `superseded_by` shown; superseded state a first-class rendering, never a hidden row | **No CLI verb reads this route at all** (verified across `led.tmpl`, `legacy-pickup.tmpl`, `libexec/*`). An operator cannot see a supersession chain from the command line, full stop |
| `led --recent` in-force projection | ALCOA+ **complete** | Read `/rows/current` for the working set, `/rows/{id}` + `/history` for the record | The witnessed NOTE: *"the superseded-inclusive raw read is not available from any CLI in this repository anymore"* |
| `/rows/asof/{ts}`, `asof-export` | **Inspection copy** (§11.10(b) frame); ALCOA+ **available** | An as-of picker on any view; export button producing the same txt+json+sha256 triple | Requires ISO-8601 exactly; the looser grammar is only in `./legacy/asof-export`. The root verb bypasses the boundary entirely, so a panel cannot reproduce it without its own psql path |
| `review` / `review_gap` / `countersign_obligation` / `review_stamp_distinctness` | **Segregation of duties**; electronic-signature *meaning* | A review queue with the owing actor and age; a co-sign panel that renders the kernel's refusal verbatim | The same-actor refusal is only discoverable via `led briefing` or by tripping it — and tripping it writes a permanent refusal row |
| `reservations_outstanding` | Honest concern-tracking (an `attest_with_reservations` discharges the gate but the concern persists) | A standing worklist; the point of the view is that it *survives* discharge | **No surface reads it** — CLI or panel. Its own glossary entry says the pre-s34 alternative *"rewarded fabricating a clean `attest` to satisfy the gate rather than recording an honest concern"* |
| `led principal *` (14 sub-verbs), `/standing/principals`, `principal_relations` / `_role_bindings` / `_keys` / `_competences` | **Access control, authority checks, identity uniqueness** (§11.10(d)(g), §11.100 frames) | Master-detail under ADR-0019 Rule 4: principal is the entity; competences, role bindings, key bindings, relations are dependents edited *in its context* — never four sibling flat lists (this exact mistake is Rule 4's own minting specimen) | Four separate flag-heavy verbs with no read-back verb at all; the four dependent views are unreachable from any surface |
| s61 signature machinery (`attest-possession`, `bind-key`, `--signature-witness`, `signed_commissions`) | **Electronic signatures**; signature/record linking (§11.50/§11.70 frames) | Manifestation: signer + time + meaning, rendered together; verification status computed, never asserted | `attest-possession` requires hand-producing a detached GPG signature over a canonical statement string (`led.tmpl:342-355`). `signed_commissions` is **not in `VIEW_REGISTRY`** — no HTTP client can read it |
| `row_hash` chain, `verify-chain`, `chain_high_water`, s43 refusal-completeness oracle | **Tamper evidence** — "discern invalid or altered records" | A verification *badge* whose state is computed on demand, with the six-value exit vocabulary preserved (`INTACT`/`BROKEN`/`TAIL-DELETION-SUSPECT`/`WITNESS-BEHIND-LEDGER`/`CANNOT-VERIFY`/`REFUSAL-ORACLE-FORGERY-SUSPECT`) | `verify-chain` is direct-psql. A panel cannot run it. **And ADR-0019 Rule 4 says hash chains are "storage artifacts… owed no surface at all"** — so the honest exposure is the *verdict*, never the hashes. Also note [ADR-0015](../law/adr/0015-verification-substrate-discipline.md) Rule 4: a degraded run *"says so in its verdict"* — `CANNOT-VERIFY` must never render as green |
| Missives (`missive list`/`dispose`, 6 views, `courier`) | **Inter-world correspondence**; contemporaneous receipt and disposition | An inbox: undisposed / stale / open threads / delivery audit, with the four-value disposition vocabulary as the only write | **There is no `led missive send` verb.** The generic write path carries no `missive_*` flags (verified against `cmd_generic`'s payload keys). Authoring a `missive_sent` requires hand-writing a 10-key JSON envelope and `led --json ledger <file>`. Four of six missive views are read by nothing |
| `judge` verdicts + DerivationRecords | Independent verification; ALCOA+ **accurate** | The four-verdict vocabulary rendered as-is, with the two `output_hash` values shown as the evidence of AGREE | `judge` is psql+clingo and **banks files into the repo**, so a read-only panel cannot invoke it. `JUDGE-READING.md:37-45` also marks `DIVERGE_BY_DESIGN` **UNWITNESSED as a live outcome** — a panel that renders four equal chips implies more than is true |
| `audit` contemporaneity verdicts | ALCOA+ **contemporaneous** — the weakest link, admitted | The four verdicts (`CONTEMPORANEOUS`/`BATCHED_DECLARED`/`LATE_DECLARED`/`BACKFILL_SUSPECT`) | `ORCH-CAPABILITIES.md:1502-1514`: *"A permit gates whether you may write; nothing yet records WHEN the recorded act actually happened relative to the row… **treat every ledger `ts` as INSERT time, not event time.**"* A panel that renders `ts` as an event time is asserting something the system disclaims |
| `apparatus.json` — 15 mechanisms × 3 modes | **Configuration control**; documented, reviewable system settings | Exactly the ADR-0019 configuration genre: tree of the whole space + form pane + one whole-model transactional commit (C3/C4). Cost notes render *beside* their switch | Hand-editing JSON with an 800-word `cost_note` embedded as a string value. No surface shows current mode at a glance |
| `governed_files.json`, `deployment.json`, `features.json`, `courier.toml`, `boundary-multiplex.toml` | Configuration control; system inventory | One configuration surface; **`boundary-multiplex.toml` is already known stale** (panel `BACKLOG.md`, entry 1) | Five files, three formats, two repos |
| `work_item_current` / `_violations` / `_startable` / `work_review_gap` / `work_edge_parent` | **Operational sequencing** (§11.10(f) frame) — permit-to-work refuses edits without an open+claimed item | Work item as entity, dependencies as edges, violations named individually by kind and slug | WITNESSED: `led work list` prints raw JSON lines; `led work violations` prints nothing when clean — indistinguishable from a failed query at a glance (exactly C6's collapse) |
| Refusal messages (kernel, boundary, CLI) | **Refuse-and-teach** — *"the refusal itself is the instruction"* | Rendered verbatim as first-class outcomes. **But see below** | **Probing a refusal writes a permanent ledger row** (s43). Discovery-by-trial is not free here — which is precisely why the panel must *advertise* limits rather than let users find them |
| `pickup` | Resumption; ALCOA+ **available** | Ten sections as ten typed views, live | WITNESSED: raw psql ASCII tables with `SET` echoes, viewport-width lines — a direct C12/C13 violation in the operator's primary daily surface |
| `attestations/` A:B:C loop | Documentation control (§11.10(k) frame) | Per-document attestation state | Off by default (`doc_attestation: "off"`), file is empty, `attest-doc` isn't in autoharn's own roster |

### 2.2 Write paths — the one rule

Every write must go through autoharn's own refusal-enforcing surface. Concretely: **`POST /d/{deployment}/write/<surface>`**, the same six surfaces `led` uses, with the kernel's `write_verdict` returned byte-verbatim at HTTP 200 whether accepted or refused. There is no second write path, and the alternative — the retired panel's `LED_BIN` subprocess conduit — is a *different* mechanism with a different failure surface.

Three constraints on how a write is offered:

1. **Advertise the ceiling before the request, from the gate's own SSOT.** [ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md) P2-extended and [ADR-0016](../law/adr/0016-the-service-contract-is-an-enforcement-surface.md) Rule 3 are unambiguous: *"Refusal is the sanctioned failure only when it is a refusal the client could predict."* The provenance is a maintainer ruling that a correct typed refusal against an unadvertised limit is *"a SYSTEM-level failure."* For this panel that means: same-actor-countersign, the flag-order asymmetry, the four-value disposition vocabulary, `limit ≤ 1000`, and the payload bound must all be visible *before* submit — sourced from `/kinds`, `/meta`, and the kernel constraints, never hand-copied.
2. **Attribution is never a free-text field.** `USER-WALKTHROUGH.md:12-15`: entries are *"attributed to the connecting role… **never a self-declared name**."* An "acting as" control selects a *registered principal* (`LED_ACTOR`), and the panel must show which one is live (C29: a mode that changes what the same input does carries a persistent indicator).
3. **C5 + C10 + C4 compose here.** No optimistic success (the ledger confirms, then the view shows it); an irreversible act — supersession, revocation, `missive dispose`, `principal revoke` — is confirmed or undoable; and a configuration commit validates the whole document and writes atomically.

### 2.3 The cost of CLI-only access, stated as the project states it

The strongest brief the panel has is on the record in the maintainer's own words.

The **standing release bar** (`user-guide/ORCH-POST-FABLE-OPERATING-BRIEF.md:41-45`):
> *"pushes (standing bar: **NO PUSH until a non-expert can use this without a frontier model** — his words, his test)"*

The **interface mandate** (same file, `:97-103`):
> *"He is executive-level and **self-describes as a non-expert operator; build the interface for that deliberately.** Briefs are plain-language option sets with ONE recommendation and the cost of each — **never a wall of mechanism, never a leading question with the conclusion pre-loaded.** Every step he performs names the exact command in order, with what success and failure look like… **Cost is a hard constraint; surface it in every option set.**"*

The **legibility indictment** (`law/adr/0017:22-34`), which is what "audit-trail review" actually means here:
> *"you shouldn't have to navigate the doc graph like a squirrel just to figure out what the insane staccato — a consistent malady of our documentation — is supposed to mean… The documentation has a life-time of about 2 hours"*

And the **anti-ceremony ruling** (`ORCH-CAPABILITIES.md:310-315`) — the failure mode a panel most easily reproduces:
> *"the ceremony this script guarded (typed confirmation, provenance line) was witnessed producing exactly the **cargo-cult paperwork a high-assurance project must not impose on a non-expert operator** ("I was told to run a delta ... until I realized it does nothing at all")."*

Plus one procedural rule that a panel will trigger, and should be built expecting: **[ADR-0014](../law/adr/0014-executor-second-opinion.md)'s external recurrence trigger** (`:485-492`) — *"A second defect report from an operator or ratifier against a surface already reported done fires a mandatory fresh-context adversarial review of that surface's architecture — mechanically, on the count, never by anyone's judgment that the reports 'feel' related."*

---

## §3 What's already there

**There are two different repositories both called "autoharn-panel," and they are different products.** This is worth stating first because the name collides.

### 3.1 `tools/autoharn-panel` — the submodule, and the *documented* panel

- Git remote `KodBena/autoharn-panel.git`, pinned at `6bd657b`, **4 commits** (WITNESSED, `git log --oneline`).
- Architecture: `backend/` (FastAPI, `/api/*` routes, `backend/config.py`, `backend/core`, `backend/extensions`) + `frontend/` (Vue 3 + Vite + TS). Reads **Postgres directly**; writes via a `LED_BIN` subprocess conduit (`POST /api/cosign`). Default bind `127.0.0.1:8420`.
- **This is the panel autoharn's own documentation describes and its scaffolder wires.** `README.md:137-148` presents it as *"enabled by default as an autoharn extension"*; `user-guide/USER-CONFIGURATION.md:380-400` gives the full adopter-facing env-var table (`LEDGER_PG_URI`, `LED_BIN`, `PANEL_BIND`/`PANEL_PORT` default `8420`, `PANEL_EXTENSIONS`); `tools/setup_tui/steps_features.py:49-53` offers `panel_extension` as a scaffold checkbox that does a *local* `git clone` of this submodule into `<dest>/panel`.
- Autoharn's own world has it **off**: `features.json` → `"panel_extension": false` (WITNESSED).

### 3.2 `/home/bork/w/vdc/2/autoharn-panel` — the live panel, world `experience4`

- Git remote **`KodBena/autoharn-gui.git`** — a *different* repo — **182 commits**, branch `master`, most recent `87e66ed` today (WITNESSED).
- **The Python backend has been deleted.** DOC-SOURCED, `frontend/vite.config.ts:8-13`: *"this app's own Python `backend/` is gone -- every read/write now crosses autoharn's FastAPI **boundary service** (upstream `serving/boundary_service.py`, multiplexed by `/d/{deployment}/...`)."* The repo is frontend-only (plus `docs/`, `scripts/`, `seed/`, `scratch/`, `attic/`).
- Stack: Vue 3.5 + Vite 8 + TS 5.9, `vue-router`, `@tanstack/vue-virtual`, `openapi-fetch`/`openapi-typescript`. A custom `scripts/lint-boundaries.mjs` enforces the core↔extension layer rule at build time.
- **17 tabs**, single-sourced in `frontend/src/tabs.ts` (2 core, 15 autoharn-extension): Recent ledger · Profiles · Commission decomposition · Work items · Obligation tree · Discharge records · Review gap · Questions · Violations · Findings & snags · Standing decisions · Countersign obligations · Review stamp distinctness · Work review gap · Model attestations · Model defeated rows · Credited current. Plus `/item/<id>` (`ItemView.vue`) and a `NotFoundView`.
- **Boundary routes actually reached** (verified by grep over `frontend/src`): `/health`, `/rows/current?after_id=&limit=`, `/rows/{id}`, `/rows/{id}/history`, `/work/items`, and **11 of the 25 registered views** — `question_status` `review_gap` `review_stamp_distinctness` `standing_decisions` `countersign_obligation` `work_item_violations` `work_review_gap` `model_attestations` `model_defeated_rows` `credited_current` `review_verdicts`.
- **Exactly one write path**, and it goes through the boundary correctly. `frontend/src/extensions/autoharn/services/cosign.ts:21-28` — `boundaryPost('/write/review', {regards, verdict, independence, basis})`, with a header naming its field mapping as verified against `serving/boundary_models.py`'s `ReviewWriteIntFields`, and deliberately not supplying `actor`/`antecedent`/`statement`.
- **World selection is runtime, not build-time** (`core/state/deployment.ts`) — a `KNOWN_DEPLOYMENTS` list of `autoharn2`/`autoharn3`/`experience3`/`experience4`, hand-maintained with a disclosed reason: *"the boundary service has no 'list known deployments' endpoint; its only self-description of the known set is the `unknown_deployment` 404 error body's `known` field… which is a side channel, not a real listing endpoint."*
- **CORS is a live blocker**, disclosed and worked around rather than hidden (`vite.config.ts:14-21`): *"the boundary service, as of this writing, sends no `Access-Control-Allow-Origin` header at all (confirmed live, filed in AUTOHARN_BACKFLOW.md), so a direct cross-origin browser fetch… is silently blocked by CORS even though the identical request succeeds from curl."* The Vite dev proxy is the only reason the dev build works.
- **Live updates are polling, not SSE.** SSE went away with the backend; `panel-live-updates-poll` (commit `7db0d18`) added a polling fallback over `/rows/current`. A boundary-side SSE route is an *open autoharn work item*, not built — WITNESSED, `./autoharn led --recent`, row 169: `work_opened: boundary-sse-events -- SSE live-updates route on the boundary service, strictly additive… Rationale-visible state: blocked-on view-registry-decomposition-views/rows-bulk-superseded-read merge`.

### 3.3 Where the panel has drifted from autoharn HEAD — named specifics

1. **`SPEC.md` describes a product that no longer exists.** §1 specifies `LED_BIN` as the write conduit, `PANEL_BIND`/`PANEL_PORT`, `PANEL_POLL_INTERVAL` for "SSE watermark poll cadence"; §4 specifies *"backend + frontend together… submoduled into autoharn under `tools/`"* and an OpenAPI-typed client generated from *the backend's* `openapi.json`. All four are now false: no backend, no `LED_BIN`, no SSE, and this repo is `autoharn-gui`, not the `tools/` submodule. `SPEC.md` carries a `doc-attest-exempt` marker calling itself *"frozen as of its date."* The panel is executing against a superseded spec.
2. **`SPEC.md` §2.6 promises a timeline view with *"s26 row-hash chain verification status as a badge (verified locally by the backend, never asserted without checking)."*** With the backend deleted, nothing can verify the chain — `verify-chain` is direct-psql and the boundary exposes no chain-verification route. That badge is currently unbuildable.
3. **`SPEC.md` §2.1 promises *"Superseded rows hidden by default, one visible toggle (maintainer verdict)."*** `/rows/current` serves in-force rows only; there is no listing route for superseded rows. The toggle is unbuildable from the current boundary — the per-row `/rows/{id}/history` is the only reach, and the panel does use it in `ItemDetail.vue`.
4. **`actor_name` is a wire/type mismatch shipped into the UI.** The panel's own `BACKLOG.md` states it precisely: *"`LedgerRow.actor_name`… renders silently blank -- ground truth: `kernel/lineage/s15-schema.sql`'s `ledger`/`ledger_current` carry no `actor_name` column, and `boundary_service.py`'s `rows_current`/`row_by_id` do no join to add one."* `ReviewGapTab` discloses it with a raw-id fallback; **the Board view and Questions tab do not** — a silently blank attributability field, which is the ALCOA+ "attributable" axis rendered as nothing.
5. **`boundary-multiplex.toml` in the panel repo is stale** relative to the live known-deployment set (its own `BACKLOG.md`, entry 1).
6. **Known silent-truncation defect in the supersession chain renderer**, filed rather than fixed (`BACKLOG.md`, entry 2): `ItemDetail.vue`'s `buildChain()` *"silently absorbs a hop whose `superseded_by` points to an id NOT present in the fetched `/rows/{id}/history` response… as if it were a normal chain terminus, indistinguishable in the rendered UI from a genuinely closed chain."* For an audit-trail-review surface this is the highest-severity class in the file — it is C6's collapse applied to the record's own completeness.
7. **Empty-state flash before load settles** in `QuestionsTab`/`FindingsSnagsTab` (`BACKLOG.md`, entry 5) — "No findings." rendered while the fetch is in flight. A textbook C6 violation, filed by the panel's own review.
8. **Nothing in autoharn's documentation mentions this panel.** `README.md`, `USER-CONFIGURATION.md`, and the setup wizard all describe the submodule at port 8420.

### 3.4 The maintainer's own fresh punch-list

`/home/bork/w/vdc/2/autoharn-panel/first_observations`, dated today (file mtime 2026-07-28 19:14), WITNESSED in full — quoted here because it is the most current statement of what the panel is missing:

> 1. The one long horizontal list (the nav tabs) probably should be vertical, since right now you have to scroll to see it all
> 2. No apparent attempt at responsive design -- playwright is available and should be used
> 3. Partially incorrect conclusion about graph rendering — a) the graph can be obtained locally b) ECharts should be used for rendering
> 4. No safe mode/observer mode
> 5. Similarly, no unsafe type operations (i.e. those that write to the ledger)
> 6. No missives view
> 7. Timer based refresh annoying (especially while scrolling); may need backend extension to allow SSE
> 8. No capabilites view (what, among the many options selected, does this given deployment use?)
> 9. Similarly, no way to create a configuration for a new world (in other words, like the autoharn setup TUI but which merely exports the necessary configuration and instructions for deploying it); should be usable without even connecting to a deployment
> 10. No roles view
> 11. Not ADR-0017 compliant

Item 1 is ADR-0019 Rule 4 (17 sibling flat tabs is not the data's topology). Item 7 is C27 verbatim. Items 6, 8, 9, 10 each name surface enumerated as a gap in §4 below, independently.

---

## §4 Gap table

Gaps are stated as gaps. Shape hints are one line, no more.

### 4.A Surface that exists but is panel-inaccessible

| # | Gap | Witness | Shape hint |
|---|---|---|---|
| A1 | **8 of 13 root verbs bypass the boundary entirely** (`pickup`, `distance-to-clean`, `asof-export`, `doctor`, `verify-chain`, `judge`, `audit`, `migrate`). Their outputs are structurally unreachable to any HTTP client. | §1.1 table, per-verb source reads | Served rebases exist for four of them (`pickup.tmpl`, `distance-to-clean.tmpl`, `asof-export.tmpl`, `doctor.tmpl`) but autoharn's own root deliberately keeps the legacy originals |
| A2 | **15 kernel views have no `VIEW_REGISTRY` entry**, so no HTTP client can read them: `belief_current` `contested_beliefs` `corroboration` `credited_beliefs` `shared_premise` (the whole belief substrate), `entitlement_class_roles`, `signed_commissions`, `countersigned_in_force`, `discharging_attest`, `work_edge_blocks_close` `work_edge_blocks_start` `work_edge_obligation` `work_item_descendants` `work_violation_history` `work_bookkeeping_closes`. | Verified by set-diff of `CREATE VIEW` names in `kernel/lineage/*.sql` against `VIEW_REGISTRY` | `VIEW_REGISTRY` is a closed allowlist whose own comment names it *"the closed-allowlist growth mechanism"* — additions need no new route and no version bump |
| A3 | **8 registered views are read by no surface at all** — `reservations_outstanding`, `principal_relations`, `principal_role_bindings`, `principal_keys`, `principal_competences`, `missive_stale`, `missive_delivery_audit`, `missive_open_threads`. | Grep across `led.tmpl`, `libexec/*`, panel `frontend/src` | The four `principal_*` views are exactly the access-control surface item 10 of the punch-list asks for |
| A4 | **`/rows/{id}/history` is read by no CLI verb.** The supersession chain — the audit trail's actual shape — is command-line-invisible. | Grep across all templates and `libexec/` | The panel already reads it; the CLI does not |
| A5 | **`/credited`, `/meta` are called by nothing.** `/kinds` is called only from `boundary_cli_client.py`'s refusal-teach path. `/rows/asof/{ts}` is called only by the *served* `asof-export.tmpl`, which autoharn's root does not use. | Grep | `/meta` carries the served view allowlist + lineage head + service version — exactly the "capabilities view" of punch-list item 8 |
| A6 | **Obligation tree data is behind unregistered views.** `SPEC.md` §2.3 marks the tree P0 "maintainer-demanded"; `work_edge_obligation`, `work_edge_blocks_close`, `work_edge_blocks_start`, `work_item_descendants` are all unregistered. Only `work_edge_parent` is reachable. | A2 + `VIEW_REGISTRY` | This is why the tree tab can only render parentage |
| A7 | **`apparatus.json`'s 15 mechanisms have no read or write surface** on the boundary. The switchboard is file-only. | `.claude/apparatus.json`; no route in `serving/README.md`'s table | Punch-list item 8 ("what does this deployment use?") lands here |
| A8 | **No CORS on the boundary.** A browser client cannot talk to it cross-origin at all. | `vite.config.ts:14-21`, confirmed live by the panel build | Currently papered over by a dev proxy; a production panel needs the header or a reverse proxy |
| A9 | **No live-update route.** Polling `/rows/current` is the only mechanism. | `boundary-sse-events` is an *open work item* (WITNESSED, ledger row 169), blocked on a concurrent merge | Named, specced at spec-time, unbuilt |

### 4.B Surface the panel assumes but autoharn does not provide

| # | Gap | Witness |
|---|---|---|
| B1 | **`ledger.actor_name` does not exist.** The panel's row type carries it; the kernel has no such column and the boundary does no join. Renders blank in the Board and Questions views. | Panel `BACKLOG.md` entry 3, grounded in `kernel/lineage/s15-schema.sql` |
| B2 | **No superseded-row listing route.** `SPEC.md` §2.1's P0 "superseded toggle" cannot be built. | §1.2 witnessed NOTE; `serving/README.md:120-166` |
| B3 | **No chain-verification route.** `SPEC.md` §2.6's P1 verification badge cannot be built. `verify-chain` is psql-only. | §1.1 table |
| B4 | **No deployment-listing route.** The panel's world selector is a hand-maintained constant. | `core/state/deployment.ts:17-27` |
| B5 | **`SPEC.md` §1 specifies `LED_BIN`, `PANEL_BIND`/`PANEL_PORT`, SSE** — all four now false for this repo. The spec is frozen and superseded in fact but not in form. | §3.3 item 1 |
| B6 | **`SPEC.md` §4 specifies an OpenAPI-generated client** against a backend that no longer exists; `boundary-client.ts:10-13` documents falling back to hand-typed `fetch`. | `boundary-client.ts` header |

### 4.C Expectations no surface serves yet

| # | Gap | Witness |
|---|---|---|
| C1 | **No missive authoring verb.** `missive_sent` is writable only by hand-composing a 10-key JSON envelope through `led --json ledger`. Inter-world correspondence — an explicitly named GxP concern for this domain — has a read verb, a dispose verb, and no send verb. | `led.tmpl` `cmd_generic` payload keys; `FABLE-MISSIVES-KERNEL-SPEC.md:115-137` |
| C2 | **Missives are absent from autoharn's own resume brief.** The missives spec names `./autoharn pickup` as the consumer of `missive_undisposed` and `missive_stale`; the *served* `pickup.tmpl` has a MAIL section, but autoharn's root runs `legacy-pickup.tmpl`, which does not. | `FABLE-MISSIVES-KERNEL-SPEC.md:398-410` vs WITNESSED `./autoharn pickup -n 2` output (ten sections, no MAIL) |
| C3 | **`./autoharn attest-doc` does not exist in autoharn's own repo**, yet `attestations/README.md:22-24` instructs the reader to run it. Same for `verify-commission`. Both are world-only verbs; autoharn's rebirth copied the world-shaped README into a repo whose dispatcher lacks the verbs. | `grep -c attest-doc autoharn` → `0`; `attestations/README.md` |
| C4 | **The apparatus switchboard has no reviewable presentation.** Fifteen mechanisms × three modes, with 800-word cost notes as JSON string values, is a configuration-control surface with no configuration-control UI. | §1.4 item 9 |
| C5 | **No world-creation/config-export surface outside the Textual wizard.** Punch-list item 9 asks for exactly this, usable without connecting to any deployment. | `first_observations` item 9 |
| C6 | **`ts` is INSERT time, not event time** — and no surface says so at the point of rendering. Any timeline view asserts contemporaneity the system explicitly disclaims. | `ORCH-CAPABILITIES.md:1502-1514` |
| C7 | **The stamp is a tripwire, not authentication**, and `stamp_verified: True` renders as a plain boolean with no such qualification. | `GLOSSARY.md:345-349`; WITNESSED `led show 168` |
| C8 | **`DIVERGE_BY_DESIGN` is unreachable in current code.** Any four-chip verdict legend over-claims. | `JUDGE-READING.md:37-45` |
| C9 | **Access control is admitted deeply flawed on autoharn's own front page**, and nothing surfaces that caveat to a user of a panel built over it. `README.md:18-22`: *"**access control is deeply flawed and rudimentary** due to Fable→Opus demotion when planning making it impossible to produce any decently robust and flexible specification (maintainer's own words, 2026-07-26)."* A panel is the most likely place for that disclaimer to be quietly dropped — which is the exact drift ADR-0020 exists to catch. | `README.md:9-22` |
| C10 | **No panel-side observer/safe-mode distinction.** Punch-list items 4 and 5 name both halves: no observer mode, and no exposure of write-type operations. Today the panel has exactly one write (co-sign) and no mode indicator (C29). | `first_observations` items 4–5 |
| C11 | **`s-history.md` documents s15–s67; the lineage head is s68.** The per-delta synopsis a reader would consult is one delta stale. | `ls kernel/lineage/` → `s68-typed-absence-dispositions.sql`; `s-history.md:273` heading reads "`s60` – `s67`" |
| C12 | **The `ORCH-CAPABILITIES.md` items have no stable anchors**, so the 42 capabilities can only be cited by number — already filed as a known gap in `GLOSSARY.md:494-496`. A panel surfacing them would deepen it. | `GLOSSARY.md:494-496` |
| C13 | **"missive" has no `GLOSSARY.md` entry** despite being a coined term in live use across the kernel, a verb, and a spec — against the file's own Stand-Alone Principle (*"Any coined term… is defined in this file"*). | `GLOSSARY.md:8-15`; no `### missive` heading exists |
| C14 | **Two files both claim "ADR-0019."** `law/adr/README.md:44-48` flags it: *"which one a bare citation means is ambiguous — flagged here, not fixed."* Any panel rendering law citations inherits the ambiguity. | `law/adr/README.md:44-48` |
| C15 | **Two different git repos are both called `autoharn-panel`** (`KodBena/autoharn-panel.git` as the submodule, `KodBena/autoharn-gui.git` as the live checkout directory-named `autoharn-panel`). | §3.1/§3.2, `git remote -v` in both |

---

## §5 Closure statement

**What I enumerated.** The `./autoharn` verb roster (13 + `service`) and every verb's `--help`; `led`'s complete grammar — 16 read forms, 20+ write forms, 14 `principal` sub-verbs, 12 shared flags — read from `bootstrap/templates/led.tmpl` in the regions that carry it; the boundary's 21 route shapes, 25-entry `VIEW_REGISTRY`, 6 `WRITE_SURFACES`, and 11-class refusal taxonomy; eleven artifact classes a user reads; the setup TUI, hook layer, and four non-umbrella root executables; the 22 ADRs and 27 user-guide documents with the rules that bind a user surface; and the panel repo's 17 tabs, single write path, reached routes, spec drift, and filed backlog.

**How I know the enumeration is closed on its main axis.** Three independent sources were cross-checked and agree:

1. `./autoharn --help`'s roster is generated from the dispatcher's own dispatch table and is gated against `ls libexec/autoharn/` by the `umbrella-cli-dispatch-parity` fixture — so the roster cannot drift from what runs. WITNESSED roster = 13 table entries + `service`; `ls libexec/autoharn/` = 13 files. **Match.**
2. `VIEW_REGISTRY` was counted directly out of `serving/boundary_service.py` (25) and set-differenced against every `CREATE VIEW` in `kernel/lineage/*.sql`, producing gap A2's 15 names mechanically rather than by inspection.
3. `serving/README.md`'s endpoint table was checked against the routes the CLI client and the panel actually call; the residue is gap A5.

**Axes deliberately not covered, named per [ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)'s closure form:**

- **Kernel closed vocabularies are under-enumerated.** I have the entry-kind count (30 members as of s58), the four missive dispositions, the four `judge` verdicts, the four `audit` verdicts, the two `write_verdict` dispositions, the four principal relation kinds, and the eleven `work` sub-verbs — but I did **not** exhaustively enumerate every CHECK-constrained vocabulary across s15–s68, nor every kernel `RAISE` teach-text. A background survey of exactly this was commissioned and had not returned when this report closed. **UNVERIFIED**, blocker: incomplete parallel survey; the source of record is `kernel/lineage/*.sql`.
- **s61 signature machinery is documented at the surface level only** — the verbs, the `--signature-witness` flag, the `signed_commissions` view's non-registration. The record shape a signature produces and the exact verification predicate are **UNVERIFIED**; source of record is `kernel/lineage/s61-signature-symmetry-and-key-binding.sql`.
- **`doctor`, `judge`, `audit`, `verify-chain`, `fixture-sweep`, `migrate`, `attest-tags`, `dispatch`, `service`, `courier` were not executed.** `judge` writes files into the repo; the rest were held back as outside the commission's explicitly enumerated permission (`--help` and `led` reads). Their surfaces are DOC-SOURCED from `--help` and source, never observed. **UNEXERCISED**, blocker: the read-only/no-live-service boundary.
- **No refusal was provoked.** Every refusal text is read from source or `--help`. Blocker: probing a kernel refusal writes a permanent s43 row.
- **The panel's rendered output was never seen.** No dev server was started, no build run, no screenshot taken. Everything in §3 is source-read. **UNEXERCISED**, blocker: read-only. This matters for §4.B/§4.C, where several gaps are the *absence* of a rendering — I can show the code path is absent; I cannot show the screen.
- **`ORCH-CAPABILITIES.md` (1542 lines) and `README.md` (564 lines) were read structurally**, not line by line — headings, the 42-item capability roster, the honest-limits and not-yet-enforced sections in full.
- **`design/` (102 files) was not swept.** Specs were read where a surface pointed at one (missives, boundary read-surface, umbrella CLI, setup TUI, UI inoculation). Two files were excluded by the independence clause and never opened.

**What remains open, ranked by how load-bearing it is for the panel's stated purpose.**

1. **Audit-trail review has no listing surface for superseded rows.** This is the panel's reason to exist and the boundary does not currently serve it. Per-row history exists; the working set does not. (B2, A4)
2. **The panel's supersession-chain renderer has a known silent-truncation path**, filed not fixed, that makes a broken chain indistinguishable from a complete one. For an audit-review surface this outranks every feature gap. (§3.3 item 6)
3. **`actor_name` renders blank in two views.** Attributability rendered as nothing, disclosed in one view and not the other two. (B1)
4. **Fifteen kernel views — including the entire belief substrate, `signed_commissions`, `entitlement_class_roles`, and the obligation-edge family — are unreachable over HTTP.** The P0 obligation tree is blocked on this. (A2, A6)
5. **Inter-world correspondence has no authoring verb and no panel view**, and is missing from autoharn's own resume brief. (C1, C2, punch-list 6)
6. **`SPEC.md` is superseded in fact.** The panel is building against a frozen spec whose §1 and §4 no longer describe the product, and two of whose P0/P1 promises are unbuildable against the current boundary. Reconciling that is a coordinator/maintainer act, not a build task.
7. **CORS and live-updates are boundary-side prerequisites** for anything a browser is meant to use in production. The SSE work item is open and blocked on an unrelated merge. (A8, A9)
8. **The name collision between two repos** should be resolved before either is documented for an adopter. (C15)

**One thing I would flag beyond the commission's frame,** because it is a hazard in reach: `attestations/README.md` in autoharn's own repo instructs the reader to run `./autoharn attest-doc check`, and that verb does not exist in autoharn's dispatcher (`grep -c attest-doc autoharn` → `0`). It is a world template written into a repo whose roster differs. A reader following it gets a bare dispatch failure, not a teaching refusal — which is the one failure mode this project's `refuse-and-teach` principle exists to prevent.