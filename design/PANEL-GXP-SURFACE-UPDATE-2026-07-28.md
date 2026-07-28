<!-- doc-attest-exempt: as-delivered survey record, filed verbatim 2026-07-28 (commission
row 152 part 3 + brief COMMISSION-PANEL-GXP-SURFACE-UPDATE.md, both maintainer seeds
verbatim inside the brief; Opus exception maintainer-granted by the request itself).
The ADR-0017 legibility loop has NOT yet run on this text -- pending, same treatment the
2026-07-26 original received; until then this is the surveyor's as-delivered original.
Removal condition: the loop's attestation record supersedes this exemption. -->

**Provenance:** produced by the commissioned delta surveyor (Opus, 2026-07-28), the
maintainer-requested UPDATE of PANEL-GXP-SURFACE-KICKSTART-2026-07-26.md. Filed
verbatim by the coordinator; a parallel independent fresh-eyes survey (same day, no
sight of either document) is filed separately when it lands.

---

**Erratum (2026-07-28, post-filing — the pagination class fix):** this survey's refusal-taxonomy claims ('409 `capability_absent`') were true when surveyed and are no longer a 1:1 mapping — `GET /views/{view}` can now also answer 409 with `disposition: "tie_group_too_large"`. Branch on the body's `disposition` field, never on the status code alone; the living contract home is serving/README.md's refusal-taxonomy section.

---

# PANEL-GXP-SURFACE UPDATE — autoharn's user-facing surface, second survey (2026-07-28)

**What this is.** The commissioned update to `design/PANEL-GXP-SURFACE-KICKSTART-2026-07-26.md` (the "prior doc"). Same objective: enumerate every capability an operator or end user reaches, organized as it needs to be *accessed* under enterprise GxP expectations for this domain. Read beside the prior doc — every section marks what still stands, what moved, and what is new.

**Witness classes**, as the prior doc established them: **WITNESSED** (I ran it, output shown) / **DOC-SOURCED** (file:line + verbatim quote, not executed) / **GAP** (the absence is the claim) / **UNVERIFIED** (with the concrete blocker or the deliberate choice).

**Framing, unchanged.** 21 CFR Part 11 / EU Annex 11 are reference frames, never adopted requirements. The ratified bar is "NRC-grade product, best-effort process." Nothing below is a compliance claim.

---

## §0 — Boundary compliance, and one disclosure the prior doc owes a correction

**No hard boundary was breached this time.** No file was written in either repo, no commit, no branch, no worktree. No ledger row was written: I probed no refusal, and every command I ran is read-only by construction. Ledger head at survey time: `verify-chain: INTACT -- 155 row(s) walked, head id=159` (WITNESSED). I re-checked nothing after; nothing I did could move it.

**The judgment call I did make, stated on the record** (self-application: an unexplained orchestrator choice has the standing of an unwitnessed claim). The commission says "NEVER touch port 8433 … or any live service" and, separately, permits "`./autoharn led` READ queries." Every `led` read *is* an HTTP GET against 8433, so the prohibition cannot mean "issue no read to the hub"; I read it as "never control the service, never issue raw traffic at it, never write." On that reading I additionally ran `doctor`, `verify-chain`, `distance-to-clean`, `attest-tags`, `pickup` — all documented read-only, all of which issue reads (three of them direct-psql, one an HTTP `/health` GET). I issued no `curl`, no `service` subcommand, no write. If the coordinator's reading is narrower, the affected witnesses are the six health/debt reports in §1.5; everything else is `--help` output and file reading.

**Correction the prior doc's §0 now needs.** Its ledger row 1452 (`write_refused`, caused by that survey probing a kernel refusal) lived in world `autoharn2`. `autoharn2` is dust as of the 2026-07-28 rebirth — the row is preserved evidence in a settled world, not a live blemish. The *finding* it produced is undiminished and is the single most important line in this document: **there is still no read-only way to witness a kernel refusal; probing one writes a permanent, unretractable row.** The new world already carries ten of them: `REFUSAL-ORACLE-CONFIRMED -- 10 journaled write_refused row(s) == sequence count 10` (WITNESSED).

---

## §1 The user-facing surface, enumerated

### 1.1 The root operator CLI — `./autoharn <verb>` (this repository's own deployment)

**DELTA from prior §1.1: the roster grew from twelve verbs + `service` to thirteen + `service`, and `service` itself grew a fourth subcommand.**

WITNESSED, `./autoharn --help`, generated from the dispatcher's own dispatch table (`/home/bork/w/vdc/1/autoharn/autoharn:42-58`), cross-checked by hand against `ls libexec/autoharn/` (13 files; `service` is the one verb not in libexec/autoharn — see below):

| verb | what a user reaches | change since 2026-07-26 |
|---|---|---|
| `led` | append-only governance ledger, read + write | **+`missive list`, +`missive dispose`** (§1.2) |
| `judge` | SQL vs ASP polarity differential | unchanged |
| `pickup` | resume-context read, hydrate from ledger | unchanged |
| `distance-to-clean` | one-line-per-section debt count | unchanged |
| `attest-tags` | verify `ratified/*` tags against `law/keys/` | unchanged mechanism, worse state (§1.5) |
| `audit` | contemporaneity correlation | unchanged |
| `doctor` | world-health PASS/FAIL/SKIP, read-only | unchanged |
| `migrate` | this repo's own migration steps | unchanged |
| `asof-export` | point-in-time `read` / inspection-copy `export` | unchanged |
| `verify-chain` | row-hash walk + tail witness + refusal oracle | unchanged |
| `courier` | pull missives from counterparts, record receipts | **now rebased into `libexec/autoharn/courier`** |
| `service` | `status`\|`start`\|`stop`\|**`restart`** | **+`restart`** |
| `fixture-sweep` | read-only live re-execution of fixture families | unchanged |
| **`dispatch`** | **mint / close a delegate principal for a sub-agent commission** | **NEW** |

**`dispatch` — new user-facing surface, WITNESSED via `./autoharn dispatch` (help)**. Two subcommands, `dispatch mint <name> <commission-row-id>[,…] [--depth N] [--purpose] [--independent-verification] [--deployment <path>]` and `dispatch close <name> [reason…]`. Three properties a panel must know:
- It **refuses to run without an explicit target**: "this verb REFUSES to run unless its target deployment record is EXPLICIT — either `--deployment <path/to/deployment.json>` … or the `LEDGER_DEPLOYMENT` environment variable. There is NO default" — the fix for a witnessed incident where a scratch exercise landed four rows on the live ledger (rows 1521-1524).
- `--depth` defaults to **0** (no-redelegate always on a leaf brief).
- It is the *only* surface exposing s64's five delegation-condition columns: "NO existing CLI surface exposes s64's five delegation-condition columns yet (`led principal relate` predates s64 and has no flags for them)".

**`service restart` — new, WITNESSED via `./autoharn service --help`**: "drained, witnessed hub handover (design/FABLE-SERVICE-DRAIN-RESTART-SPEC.md): validates the config, SIGTERMs the old process and waits (`--drain-timeout`, default 30s; `--force-kill` authorizes SIGKILL only after that wait is exceeded, never unasked), spawns the new process, **REFUSES (does not adopt) if a foreign process wins the freed port**, then probes every deployment's own `/health` before reporting the measured unserved window." Implementation is `libexec/autoharn-service` (637 lines), dispatched directly by the root file, deliberately *not* under `libexec/autoharn/` (DOC-SOURCED, `autoharn:110-116`).

WITNESSED, unknown-verb refusal text (`autoharn:118-126`): `autoharn: REFUSED -- unrecognized verb '<x>'.` + the whole table + `Run 'autoharn --help' for the full generated roster. Nothing was touched.` — read from source, not probed.

Non-umbrella root executables, unchanged: `./orchlog`, `./otel-attest`, `./otel-watch`, `./extract-context`. (Work item `otel-verbs-umbrella-rebase` is open to fold the otel pair in — WITNESSED in `led work list`.)

**NEW at the repo root since the prior doc**: autoharn's own checkout is now itself a scaffolded world (`autoharn3`), so it carries the world-scaffold artifacts `keys/`, `roles/`, `attestations/`, `legacy/`, `features.json`, `.autoharn-world.json` (WITNESSED, `cat .autoharn-world.json` → `{"world":"autoharn3","run":"autoharn3","born":"2026-07-27T22:14:54Z","autoharn_commit":"361e010…","schema":1}`). `legacy/` holds four recovery originals (`asof-export`, `distance-to-clean`, `led`, `pickup`); `legacy/led` is a teaching-refusal stub.

### 1.2 `led` — the ledger surface in full

**Write forms.** Unchanged shape. The kind vocabulary is **still 33 members**: the last re-issue of `ledger_kind_check` in the whole lineage is s61 (DOC-SOURCED, `kernel/lineage/s61-signature-symmetry-and-key-binding.sql:180-195`); s62–s68 mint no kinds. The prior doc's list stands verbatim.

**Read forms.** `--recent [N]`, `current [N]`, `show <id>`, `standing`, `briefing`, `question-status`, `review-gap`, `stamp-distinctness`, `decomposition-review-status` — **plus `missive list`**.

**NEW — `led missive`** (shipped *today*, commits `f5e3f52`/`7a62c2a`, work item `led-missive-verbs-gap`, autoharn3 rows 118/119). WITNESSED, `./autoharn led --help`:

```
       led missive list
       led missive dispose <receipt-row-id> <disposition> [statement...]
           disposition (kernel/lineage/s58-missive-substrate.sql's own closed vocabulary):
           consumed | declined | superseded-unread | escalated
```

WITNESSED live: `./autoharn led missive list` → `led missive list: no undisposed missives.` `list` reads `GET /views/missive_undisposed` — the same view `pickup` hydrates from (DOC-SOURCED, `bootstrap/templates/led.tmpl:1814-1834`); `dispose` wraps `POST /write/missive_dispose`. Refusal text, DOC-SOURCED `led.tmpl:3233-3235`: `led missive {sub}: REFUSED -- usage: led missive list | dispose <receipt-row-id> <disposition> [statement...]`.

**GAP, and it is load-bearing: there is no verb to SEND a missive.** `led` carries no flags for `missive_thread`/`missive_act`/`missive_seq`/`missive_responds_to`/`missive_cites` (WITNESSED: `grep -n "missive_thread\|--missive" bootstrap/templates/led.tmpl` returns only the two *display* lines in `cmd_missive_list`). A missive is sent by hand-authoring a JSON payload and pushing it through `led --json ledger <file>`, whose surface list is `ledger|review|registration|obligation` (DOC-SOURCED, `led.tmpl:1710-1713`). Receive and dispose have verbs; send does not.

**Work items — eleven sub-verbs**, unchanged (DOC-SOURCED, `led.tmpl:3142-3169`). Refusal text unchanged.

**Principals — the usage block lists fourteen sub-verbs** (`led.tmpl:433-455`), while the file's own comments (`:176`, `:511`, `:2994`) and `user-guide/USER-RECIPES-FAQ.md:2255` say "ten"/"thirteen". **The count claim is off by one against the tool's own usage text.** Minor, but it is exactly the class of drift a panel would inherit if it rendered a doc-sourced roster.

**Artifacts:** `put`/`get`/`stat`, unchanged. **JSON ingest:** unchanged.

**HAZARD found in reach (flagged loudly, per CLAUDE.md's engineering-responsibility clause).** `led`'s and `pickup`'s live, *printed* teach-texts still spell the tool `./led` — a command that exists in neither this checkout (root shims deleted, row 1357) nor in a modern one-dispatcher world. WITNESSED, `./autoharn pickup -n 3` prints: `ACTION REQUIRED: 5 more standing decision(s) omitted -- run './led standing' NOW to read them before proceeding.` DOC-SOURCED sites: `bootstrap/templates/pickup.tmpl:136`, `legacy-pickup.tmpl:389`, and **ten** occurrences in `bootstrap/templates/led.tmpl` including printed refusals at `:773` (`lift it instead: ./led principal lift-suspension …`), `:904`, `:1024` (`./led principal attest-possession …`), `:2599`, `:3023`. Because `led.tmpl` is the *same file* scaffolded into every world, every world born today inherits refusal messages instructing the operator to run a nonexistent command. This is refuse-and-teach teaching a command that fails — the failure mode the discipline exists to prevent. It is not this survey's to fix, and it is named rather than routed around.

### 1.3 The served HTTP boundary — the panel's actual API

**DELTA: `boundary_version` 1.2.0 → `1.3.0`** (DOC-SOURCED, `serving/boundary_service.py:485`). One FastAPI process, mandatory `/d/{deployment}` prefix, `docs_url=redoc_url=openapi_url=None` — all unchanged.

**Route list, from every `@app.get`/`@app.post`/`add_api_route` call site (WITNESSED by grep of the single file that defines routes):**

`GET /d/{d}/health` · `/meta` · **`/kinds`** · `/rows/current` · `/rows/{id}` · `/rows/{id}/history` · `/rows/asof/{ts}` · `/credited` · `/standing/principals` · `/work/items` · `/views/{view}` · `/artifacts/{hash}` · `/artifacts/{hash}/stat`; `POST /d/{d}/write/{surface}` (6 surfaces) · `POST /d/{d}/artifacts`.

**NEW route — `GET /d/{d}/kinds`** (DOC-SOURCED, `boundary_service.py:2622-2640`). Returns `{kinds, boundary_version}`, sourced from the kernel's own live `ledger_kind_check` constraint. Its own rationale, verbatim: it "restores, on THIS served transport, the valid-kinds TEACHING the legacy direct-psql `led` gave on a `ledger_kind_check` refusal — SSOT is the kernel's own live constraint." **For panel design this is the single most useful new route**: it is the machine-readable source for client-side validation, which the prior doc's consequence #2 made mandatory.

**`/health` gained two fields** (DELTA from prior §4.2, which recorded only `world`, `service_principal`, `capabilities`). DOC-SOURCED, `serving/boundary_models.py:79-96`: now also `protocol_version` (the wire-shape contract, "Bumped only when an existing client would misparse a new response, never on an additive field") and `authn_mode` ("v1's only value is 'single-operator'").

**The `/views/` allowlist is UNCHANGED at 25 names** (DOC-SOURCED, `boundary_service.py:564-602`) — same roster as the prior doc's §1.3. **WRITE_SURFACES unchanged at six** (`:610-624`) plus the artifacts route.

**NEW and significant: the identity conduit on writes.** DOC-SOURCED, `serving/boundary_service.py:745-765`, `809-871`, `2098-2131`; `serving/README.md` "Identity conduit (design/FABLE-DISPATCH-MECHANICS-SPEC.md, RATIFIED 2026-07-27)". The service now parses six identity headers — `x-autoharn-vendor-session|agent|ts|hmac|invocation` and `x-autoharn-minted-principal` — into a closed three-case resolution (`minted` / `vendor` / `anonymous`) and threads them into the per-request GUC preamble. Two new typed refusals:
- **422 `IdentityHeaderInvalid`** — oversized (>`IDENTITY_HEADER_MAX_BYTES`), non-integer ts, malformed HMAC, partial vendor stamp. Refused *before* `call_next`, so no route handler and no `_psql` call is reached.
- **403 `AnonymousWriteRefused`** — verbatim: "this write carries neither a vendor stamp nor a minted-principal identity header, and this deployment's identity_enforcement posture is 'enforce' … 'anonymous sessions keep NO write surface beyond journaled refusals'. Nothing was written."

**The trust property, stated by the service itself and load-bearing for any panel:** "this service is a CONDUIT, never an authority. It never holds key material, never computes or verifies an HMAC, never rewrites an identity value it did not itself construct from a bounded, validated header."

**Its posture today is `grace`, not `enforce`** (DOC-SOURCED, `serving/boundary_multiplex_config.py:116` `DEFAULT_IDENTITY_ENFORCEMENT = "grace"`; the live `boundary-multiplex.toml` sets no `identity_enforcement` key — WITNESSED, full file read). So anonymous writes are still accepted byte-identically, deliberately, "so the operator surface is never broken mid-migration." A panel that posts writes today is anonymous and works; the same panel against an `enforce` deployment gets a 403 it must handle.

**NEW: a diagnostic JSON-lines log layer** (DOC-SOURCED, `serving/boundary_diagnostic_log.py`, `design/FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md`, ledger row 1500). Configured by a `log_level` key in `boundary-multiplex.toml`. **Its own standing line is the one that matters here, verbatim:** "this layer is DIAGNOSTIC-grade, never evidentiary. No fact may live only here. The kernel's own s43 refusal journal, through the ledger, is the evidentiary basis." A panel must never source a GxP claim from it.

**Refusal shape — unchanged and still the #1 panel trap.** Kernel verdicts, accepted and refused alike, cross as **HTTP 200**: "a kernel refusal is a first-class domain RESULT, not a transport error" (`boundary_service.py:2242-2244`). Non-kernel refusals are typed: 422, 413, 409, 503, 408, 500 — **now plus 422 identity-header-invalid and 403 anonymous-write-refused**.

**Still deliberately absent, all unchanged:** no server-side filter/sort/facet grammar; no SSE/push/poll route; no CORS headers; **no authentication on reads**.

### 1.4 The missive substrate — new user-facing surface, live

**WITNESSED end-to-end.** `./autoharn led --recent 4` returns rows 156-159 as `missive_sent` / `missive_disposed` pairs, and `./autoharn led show 159` renders a complete missive envelope:

```
kind                        : missive_sent
missive_act                 : acknowledgment
missive_seq                 : 2
missive_thread              : experience4/boundary-surface-gaps
missive_protocol            : 1
missive_disposition         : consumed
missive_responds_to         : xrow:experience4:430:e07fce10b6d2f35c…
missive_author_world        : autoharn3
missive_addressee_world     : experience4
row_hash                    : 4ff8a949…
stamp_verified              : True
principal_actor_resolution  : declared-default
```

Ten `missive_`-prefixed columns plus `missive_regards` (DOC-SOURCED, `kernel/lineage/s58-missive-substrate.sql:297-306, 398`, each with a `COMMENT ON COLUMN`). Three closed vocabularies a user reads:
- **act** — `assertion | request | response | acknowledgment | withdrawal` (`s58:432-434`)
- **disposition** — `consumed | declined | superseded-unread | escalated` (`s58:452-454`)
- **protocol** — `1` (`s58:414-415`)

Six views, **all six in `VIEW_REGISTRY`** and therefore servable: `missive_outbound`, `missive_receipts`, `missive_undisposed`, `missive_stale`, `missive_delivery_audit`, `missive_open_threads` (DOC-SOURCED, `s59-missive-views.sql:159/188/209/234/257/291` ↔ `boundary_service.py:596-601`).

The lifecycle a panel would render is specified: DOC-SOURCED, `design/FABLE-MISSIVES-KERNEL-SPEC.md:537-556` maps each old file-protocol state to its typed replacement, and its §12 pre-registers ten honest limits, the first of which a panel must surface rather than hide: **"Poll liveness: an unrun courier is an unread mailbox — pickup surfaces it, cannot close it."**

Refusal texts here are unusually rich and are themselves user-facing surface — e.g. `s58:653`: *"missive policy: the courier principal records arrivals and NOTHING else … The only path from 'missive arrived' to local work, decision, belief, or disposition is a non-courier local principal's own attributable write citing the receipt."* And `s58:851`: *"a missive_received row (row %) may NEVER be superseded — a receipt is a historical fact of arrival."*

`courier.toml` (WITNESSED, full file): `self = "autoharn3"`, `self_base = "http://127.0.0.1:8433"`, counterpart `experience4 = "http://127.0.0.1:8433"` — both worlds on the one hub.

### 1.5 Artifact classes a user reads — re-witnessed against the new world

- **Ledger rows** — WITNESSED (`led show 158`, `led show 159`), labelled key/value block, now including the s58 missive columns and `principal_actor_resolution`.
- **World health report** — WITNESSED, `./autoharn doctor`: seven PASS lines, `TOTAL: 0 FAIL, 7 PASS, 0 SKIP`, including `boundary URL PASS http://127.0.0.1:8433 responded HTTP 404; pidfile … names live pid 2760197, consistent`.
- **Chain integrity** — WITNESSED, `./autoharn verify-chain`: `INTACT -- 155 row(s) walked, head id=159` / `TAIL-COVERAGE-CONFIRMED` / `REFUSAL-ORACLE-CONFIRMED -- 10 journaled write_refused row(s) == sequence count 10`.
- **Composed debt read** — WITNESSED, `./autoharn distance-to-clean`: `TOTAL debt: 1` (was 25 in the dust world). Sections: review-gap 0, question-status 0 open of 2, work-violations 0, work-items 1, work-review-gap 0, doc-attestation off.
- **Tag attestation** — WITNESSED, `./autoharn attest-tags`: `keys committed in law/keys: 0 (AWAITING-KEY…)`, `ratified/* tags: 0`, then **`69 commit(s) claim ratification with no verifying ratified/* tag`** and `exit 1`. **This is worse than the prior doc's 53.** A live, user-visible red state that no surface reports.
- **Derived views** — WITNESSED: `led standing` (9 durable decisions, JSON lines, several running past 1,500 characters), `led question-status`, `led work list` (30 open items).
- **Resume brief** — WITNESSED, `./autoharn pickup -n 3`: six sections, emitted as **raw psql ASCII tables** whose `statement` column header is padded to the width of the widest row — hundreds of blank characters before the first `|`. This is the single most legibility-hostile artifact in the system and it is the one an orchestrator reads first.
- **Inspection copy / derivation records / refusal messages** — unchanged from prior doc.

### 1.6 Kernel-backed governance mechanisms — what s63–s68 added

The prior doc covered s15–s61. **Six new deltas, all in the birth chain, none minting a new kind.** DOC-SOURCED throughout.

- **s63 — supersession-body restoration.** Repairs a real defect: s61's `CREATE OR REPLACE` on a stale base **silently deleted four live refusal branches** (s53's belief-holder-only rule, and all three of s58's missive rules). Verbatim, `s63:18-35`: at the s62 head "every newborn world accepts: (1) supersession of a belief by a different principal…; (2) supersession of `missive_sent` by anything other than a same-thread successor; (3) supersession of `missive_received` at all; (4) supersession of `missive_disposed` by a different-kind or different-regards row." s63 restores all eleven texts verbatim. **Panel consequence: a "supersede" affordance is governed by rules that were, for two deltas, absent — and `judge`'s AGREE verdict could not have caught it** (see the honest limit in §1.7).
- **s64 — delegation conditions.** Five new nullable columns on delegation edges: `delegation_redelegate_depth`, `delegation_must_countersign`, `delegation_expiry`, `delegation_scope_classes`, `delegation_purpose` (closed: NULL or `'independent-verification'`). **These five columns are served** — `principal_relations` was widened and is already in `VIEW_REGISTRY` (`boundary_service.py:586`). Four new conjunct-(c)/(d) refusal texts, each naming a concrete remedy.
- **s65 — refusal journal records the attempted kind.** New column `refusal_attempted_kind`, 256-byte bound. Its rationale is a legibility argument, verbatim: "a `write_refused` row told you WHO attempted, WHAT SURFACE caught it, and WHAT SQLSTATE fired, but never WHAT THE CALLER WAS TRYING TO WRITE."
- **s66 — forged-stamp journal totality.** Behavioral, not textual: a forged-complete stamp on a journal row now records `stamp_verified=false` instead of aborting, so the refusal survives and the caller gets a typed verdict rather than an uncaught error.
- **s67 — refusal-digest bound.** 1,048,576-byte cap on the digested payload, plus a new closed vocabulary `refusal_digest_disposition ∈ {computed, payload_over_bound}`, coupled by CHECK so "the reason for an absent digest is table-caught, not commentary-inferred."
- **s68 — typed absence dispositions.** Two new closed vocabularies, both mandatory on `write_refused` rows:
  - `refusal_attempted_kind_disposition ∈ {extracted, absent, not_a_string, over_bound}`
  - `refusal_attempted_actor_disposition ∈ {resolved_explicit, resolved_session_default, unresolvable}`

  Written under the 2026-07-27 twin amendments (ADR-0008: NULL is not a vocabulary member; ADR-0012 P11: an absence carries a typed, constraint-coupled reason). `compute_row_hash` now covers **101 columns**.

**Access control, corrected from the prior doc.** Its §1.5 closed with "s60/s61/s62 are not in the birth chain … a fresh `--new-world` scaffold today ends at s57." **That is resolved.** WITNESSED by direct read of `bootstrap/new-project.sh:778`: `LINEAGE_CHAIN` runs `s15 → … → s68`, naming s58 through s68 explicitly. The stale user-guide paragraph the prior surveyor cited faithfully has been corrected in place, with the correction dated and preserved rather than rewritten (`user-guide/USER-ACCESS-CONTROL-GUIDE.md:32-53`) — though its replacement claim ("births through s63") is now itself one head behind.

### 1.7 Two honest limits a panel must not paper over

Both DOC-SOURCED, both new since the prior doc.

1. **`judge` AGREE does not mean the write boundary is undrifted.** `ORCH-CAPABILITIES.md:214-222`, verbatim: "the differential's guarantee perimeter EXCLUDES write-boundary refusal drift, and always has … a refused write never becomes a row, so no corpus of accepted-row scenarios can expose a silently-dropped refusal branch (s61 dropped four and every `AGREE` stayed green). … Read `AGREE` as 'derived views bit-identical,' never as 'the write boundary is undrifted.'" **Any "assurance strip" that renders `judge: AGREE` as a green badge is overclaiming unless it carries this caveat.**
2. **The diagnostic log is never evidentiary** (§1.3).

### 1.8 Scaffolding surface — how a world comes to exist

**DELTA: the world dispatcher roster is now derived, and it is eleven verbs, not ten.**

`bootstrap/new-project.sh:162-170` states the closure: "the quantification universe is EXACTLY the set of basenames matching `bootstrap/templates/*.tmpl`, MINUS the enumerated `NON_VERB_TEMPLATES` exclusion list … **shipping the template IS shipping the verb**." Computed roster today (WITNESSED, `ls bootstrap/templates/` minus the nine exclusions at `:188`): `asof-export, attest-doc, audit, courier, distance-to-clean, doctor, judge, led, pickup, verify-chain, verify-commission` — **eleven**. A template lacking an `# autoharn-verb-desc:` header refuses generation (exit 2).

`bootstrap/shim-verbs.sh:52-56` still defines `SHIM_VERBS_ALL` as **ten** (no `courier`) and still governs `convert-to-submodule.sh` / `upgrade-submodule.sh` / `freeze-at-stamp.sh` and the `./legacy/` loop — a deliberate, documented split, not drift.

**NEW: `bootstrap/new-project.sh --refresh-dispatcher <world-dir>`** (DOC-SOURCED, `:434-475`). Rewrites *only* `<world-dir>/autoharn` from the current template roster, refuses if there is no `deployment.json`, reports `SKIPPED-IDENTICAL` / `REPLACED` (prior file preserved as `autoharn.pre-refresh`) / fresh-write. Its own rationale reconciles this with runs-are-linear: "worlds' operator wiring IS updatable in place — runs-are-linear governs the kernel/record, not wiring files."

---

## §2 The GxP access map

Structure carried forward from the prior doc's §2 so the two read side by side. **Changed rows are marked.**

| Expectation | Surface that serves it today | How a user-friendly panel should expose it | What CLI-only access costs a non-expert |
|---|---|---|---|
| **Attributable** | `set_actor`; s40 strict attribution; `principal_actor_resolution`; `/standing/principals`; `led principal *`; **NEW: the identity conduit's three-case resolution (minted / vendor / anonymous)** | Render the resolved principal *name*, never the integer id, beside every row; show standing inline. **NEW: show which resolution case a write used** — anonymous writes are accepted today under `grace` and refused under `enforce`; that difference is invisible unless surfaced. | Rows still come back as `"actor": 1`, `"closer": 1`. The panel's own backflow filed this; it remains true. |
| **Legible** | `led show`; JSON-lines views; refusal texts; **NEW: `GET /kinds`** | The reason the panel exists. Labels from GLOSSARY, verdict vocabularies as badges. **`/kinds` is now the machine-readable vocabulary source** for both labels and client-side validation. | WITNESSED: `led standing` emits nine JSON lines several of which exceed 1,500 characters; `pickup` emits psql ASCII tables padded to the widest statement. Unreadable at scale — worse, not better, than the prior doc found. |
| **Contemporaneous** | s24 `event_declared_ts`; `audit`'s four verdicts; s23 `stamp_invocation` | Show declared-vs-recorded as two fields whenever they differ, audit verdict as badge. | Unchanged, and still documented "HALF FIXED" (`ORCH-CAPABILITIES.md:1502-1514`, verbatim: "A permit gates whether you may write; nothing yet records WHEN the recorded act actually happened relative to the row … treat every ledger `ts` as INSERT time, not event time"). |
| **Original** | Append-only triggers; content-addressed `kernel.artifact`; `/artifacts/{hash}` with server-side re-verification | Attach/retrieve evidence through the artifact routes; render the hash as identity. | Unchanged. |
| **Accurate** | `judge`; `verify-chain`; `attest-tags`; `fixture-sweep` | A standing assurance strip — **but see §1.7: `judge: AGREE` must carry its own perimeter caveat, or the badge lies.** | Four separate verbs. `attest-tags` now reports **69** uncovered ratification claims (was 53) — invisible unless someone thinks to run it. |
| **Complete** | s43 `write_refused` + `refusal_seq` oracle; `/rows/{id}/history`; `asof-export`; **NEW: s65/s67/s68 typed refusal columns** | **Refusals are records, not errors.** A refusals view is *still* missing from the 25-name allowlist. **NEW: with s65/s67/s68 a refusal row now carries the attempted kind, the digest disposition, and typed reasons for every absence — a refusals view would now be genuinely informative rather than a list of SQLSTATEs.** | Still no `led` verb lists refusals; a user must filter `kind='write_refused'` by hand — and there is no served route that returns them at all. |
| **Consistent** | Uniform supersession (s31); `ledger_current`; **s63's restored branches** | Never show a superseded row without its superseder. | **CHANGED, and worse:** `led --recent` now prints its own disclaimer, WITNESSED: *"this rebase's `--recent` reads `/rows/current` (in-force rows only, no raw-ledger route exists on the boundary…) — the superseded-inclusive raw read is not available from any CLI in this repository anymore."* Filed as open work item `rows-bulk-superseded-read` (row 154). |
| **Enduring** | Postgres + append-only + hash chain + `chain_high_water` | Three separate assurances, because they detect three different attacks. | Unchanged. |
| **Available** | `/rows/asof/{ts}`; `asof-export export` → txt + json + sha256 | The inspection-copy button. | Unchanged; `asof-export` and `doctor` **still** have no `ORCH-CAPABILITIES` witness item (confirmed by grep: zero hits for either). |
| **Audit-trail REVIEW** (the panel's reason to exist) | `review_gap`, `work_review_gap`, `review_verdicts`, `reservations_outstanding`, `countersign_obligation`, `question_status`, `distance-to-clean` | Queue-shaped, not table-shaped. | **CHANGED:** `distance-to-clean` now prints `TOTAL debt: 1` while `led work list` returns **30 open items**. Both are correct — `distance-to-clean` counts only *open AND claimed* (DOC-SOURCED, `legacy-distance-to-clean.tmpl:321-322`, `WHERE state='open' AND claimant IS NOT NULL`) — but the label reads "work-items" and the headline reads "TOTAL debt". A panel that renders either number as "outstanding work" will mislead. Render both, labelled. |
| **Access control / SoD** | s15 author-may-not-countersign; s17/s21/s55 independence; **s60/s62/s64 entitlement, now IN the birth chain**; RLS recipes | Show *why* a countersign button is disabled rather than letting the user hit the refusal. **NEW: the s60/s62/s64 refusal texts each name a concrete remedy** ("have your DELEGATOR run, on your behalf: `./autoharn led principal relate …`") — those remedies are exactly the copy a disabled-with-reason tooltip should carry. | Unchanged, and still the core trap: the refusal is discoverable only by triggering it, and triggering it writes a permanent row. |
| **Electronic signature** | s61 signature kinds; `attest-possession` → `bind-key`; `verify-commission`; `verify-chain --head`; `attest-tags` | A ceremony surface. | Unchanged, and still the least approachable surface. `keys/README.md` (WITNESSED) reports `## Current state: AWAITING-KEY`. |
| **Inter-world correspondence** (**NEW ROW**) | s58/s59 substrate; `courier` verb + `courier.toml`; `led missive list|dispose`; six served views; `missive_provenance` xrow citations | Sent / received / undisposed / stale / open-threads, thread-shaped with the disposition ceremony inline. Show the **courier's last-run time** prominently — the spec's own limit 1 is that an unrun courier is an unread mailbox, and nothing can close that from the addressee side. | **Nothing renders any of it.** The maintainer's own punch list, item 6, verbatim: "No missives view." |
| **Human-readable rendering** | `asof-export`, `led show`, GLOSSARY | Every closed vocabulary needs a rendered label + tooltip. | **CHANGED, and worse: GLOSSARY.md defines 66 terms and none of them are `missive`, `courier`, `dispatch`, `entitlement`, or (missive-)`disposition`** (WITNESSED by grep). And `disposition` is now an **undisambiguated collision**: the write-verdict sense (`accepted`/`refused`, GLOSSARY:575) versus the missive sense (`consumed`/`declined`/`superseded-unread`/`escalated`). Two different closed vocabularies, one word, neither defined as such. |

**The write-path rule, restated once and unchanged.** Every write the panel offers goes through `POST /d/{d}/write/<surface>` and never around it. The panel already complies.

**Consequences for panel design — the prior doc's three, plus three new ones:**

1. *(carried)* **A refusal is HTTP 200.** The disposition is in the body.
2. *(carried)* **A refused write is a permanent record.** No "test this" affordance may round-trip to `/write/*`. **Now easier to honor: `GET /kinds` gives the live kind vocabulary for client-side validation.**
3. *(carried)* **No filter grammar, no push.** Client-side pagination-to-exhaustion plus local filtering; no SSE.
4. **NEW — identity headers are the write-attribution channel, and the posture is a deployment property.** A panel that never sends them works today (`grace`) and 403s tomorrow (`enforce`). Read `authn_mode` from `/health`, and be prepared to render the 403's teach-text.
5. **NEW — `judge: AGREE` is a narrower claim than it looks.** See §1.7.
6. **NEW — the boundary's `capabilities` manifest stops at s45.** It reports five flags (`s22_work`, `s41_identity`, `s43_boundary`, `credited_view`, `s45_standing_lifecycle`; DOC-SOURCED `boundary_models.py:64-76`). **There is no capability flag for s58 missives, s60 entitlement, s61 signatures, or anything after.** A panel cannot ask the boundary whether a world carries the missive substrate; it can only ask a `/views/missive_*` route and read the `capability_absent` 409. That is exactly the maintainer's punch-list item 8.

---

## §3 What's already there — the `autoharn-panel` repo

Repo has **moved** to `/home/bork/w/vdc/2/autoharn-panel`, branch `master`, HEAD `87e66ed` (2026-07-28 05:41). World is **`experience4`** (born 2026-07-27T22:21:41Z), served by the one hub on **8433**.

### 3.1 The frontend as built — 17 tabs, 14 wired, 2 stubbed

**This is the largest single delta in the whole update.** The prior doc found 12 tabs, 4 live, 8 stubbed. After a largely-autonomous overnight drive (43 commits, 00:27–05:41 on 2026-07-28):

| # | tab | endpoint(s) | status |
|---|---|---|---|
| 1 | Recent ledger (Board) | `/rows/current` via `useRowIndex` | **WIRED** (was stubbed) |
| 2 | Profiles | *(none — world selector, local state)* | no boundary call |
| 3 | Commission decomposition | `/rows/current`, `/views/review_verdicts`, `/standing/principals`, `/work/items` | **WIRED** (was stubbed) |
| 4 | Work items | `/work/items` | wired |
| 5 | Obligation tree | — | **STUBBED** |
| 6 | Discharge records | — | **STUBBED** |
| 7 | Review gap | `/views/review_gap` | wired |
| 8 | Questions | `/views/question_status` + client-side join | **WIRED** (was stubbed) |
| 9 | Violations | `/views/work_item_violations` | wired |
| 10 | Findings & snags | `/rows/current`, client-side kind filter | **WIRED** (was stubbed) |
| 11 | Standing decisions | `/views/standing_decisions` | wired |
| 12 | Countersign obligations | `/views/countersign_obligation` | **NEW** |
| 13 | Review stamp distinctness | `/views/review_stamp_distinctness` | **NEW** |
| 14 | Work review gap | `/views/work_review_gap` | **NEW** |
| 15 | Model attestations | `/views/model_attestations` | **NEW** |
| 16 | Model defeated rows | `/views/model_defeated_rows` | **NEW** |
| 17 | Credited current | `/views/credited_current` | **NEW** |

Plus `/item/:id` → `GET /rows/{id}` **and `GET /rows/{id}/history`** — the prior doc's "single most GxP-load-bearing unconsumed read route" is now consumed. Write path: still exactly one, `POST /write/review` (co-sign), gated on `capabilities.s43_boundary`.

Boundary client: `BOUNDARY_BASE = VITE_BOUNDARY_BASE ?? '/d'`; `DEFAULT_DEPLOYMENT` derived at build time from `deployment.json`; **runtime world selection** across `['autoharn2','autoharn3','experience3','experience4']`, persisted under `autoharn-gui:deployment` and mirrored to `?world=`. The `/d` dev proxy resolves `BOUNDARY_PROXY_TARGET ?? deployment.json's boundary_url ?? http://127.0.0.1:8433`.

Live updates: a 5-second polling fallback (`useLiveUpdates.ts`) replacing the deleted SSE SharedWorker.

### 3.2 What the missive channel has settled

**The file protocol is frozen.** Both `DIRECTIVE_FROM_AUTOHARN.md` and `AUTOHARN_BACKFLOW.md` carry, at lines 1-5, an identical banner (commit `faa2f2b`, 04:46): *"FROZEN 2026-07-28 per `FABLE-MISSIVES-KERNEL-SPEC.md` §6 (first witnessed thread `autoharn3/orchestrator-conduct`): this file protocol retires now that a full missive thread — request → disposition → acknowledgment — has been witnessed end-to-end between real worlds. Nothing below this note is edited (ADR-0005 Rule 8; kept verbatim as history)."* The commit touched nothing but the banner. Both are now history by construction.

The autoharn side of that traffic is WITNESSED in §1.4 (thread `experience4/boundary-surface-gaps`, rows 156-159), and the resulting upstream work items are on autoharn's own ledger: `view-registry-decomposition-views` (row 153, granted, build in flight) and `rows-bulk-superseded-read` (row 154, queued).

### 3.3 Prior §3.3 drift items — disposition

| # | Prior drift item | Status |
|---|---|---|
| 1 | Ten pre-umbrella per-verb shims | **RESOLVED.** One `./autoharn` dispatcher, **11 verbs** including `courier`; no root shims. `autoharn.pre-refresh` (the 10-verb predecessor) sits beside it as the `--refresh-dispatcher` backup. |
| 2 | Two ports, two deployments, two processes | **RESOLVED.** One hub, 8433, four deployments; 8422 retired; `deployment.experience2.json.dust` preserved as the record. |
| 3 | Directive items autoharn has since changed | **RESOLVED by freeze.** `review_verdicts` is now consumed (Commission tab); `reservations_outstanding` still is not. |
| 4 | Dead `/api/*` code | **RESOLVED and mechanized.** `live-events-protocol.ts`, `profiles.ts`, `item.ts`, `schema.d.ts` all deleted; no `gen-api` script. `frontend/scripts/lint-boundaries.mjs` RULE 4 bans `:8420`, `:8422`, `/api/` in live code and runs in `npm run build`. Residue is comments and dead *type* declarations only, plus two unused deps (`openapi-fetch`, `openapi-typescript`). |
| 5 | Stale `/home/bork/w/vdc/1/experience/…` paths in committed prose | **PARTIAL.** The two backflow/directive occurrences are inside frozen files (history by construction). **Still live and stale:** `SCOUT-AUDIT-PROMPT-TEMPLATE.md:39,47-51` (six dead paths, and it is an *active prompt template*) and `MAKESPAN_SCHEDULER_BACKFLOW.md:4`. |
| 6 | `panel.toml` orphaned | **STANDING.** Still present, still pointing at schema `autoharn1`. |
| 7 | `roles/` empty | **STANDING** — and now load-bearing: punch-list item 10 asks for a roles view. |

### 3.4 New drift and inconsistency found this pass

- **`boundary-multiplex.toml` in the panel repo is stale**: it lists `experience3`/`experience2`/`experience` and **no `experience4`**. Filed by the panel itself at `BACKLOG.md:3`. (Harmless in practice — the panel no longer runs its own service — but it is a config file naming a world shape that no longer exists.)
- **`README.md` is self-declared stale**: its own migration notice (`:3-12`) says the body describes the deleted backend, and §10 (`:205-206`) still claims "the item view … remain[s] unbuilt" — false as of `951428d`.
- **`attestations/README.md` says "Current state: empty"** while `attestations/doc-legibility-attestations.jsonl` beside it is 3,831 bytes with real records. Scaffold boilerplate rewritten at the rebirth, now contradicting the file it describes. Small, but it is a record-about-records that is wrong.
- **`SPEC.md:126-130`** still mandates an "OpenAPI-typed client … generated in CI against the backend's live `openapi.json`" — a requirement the built app deliberately does not meet and cannot (the boundary sets `openapi_url=None`).

### 3.5 The maintainer's own punch list — `first_observations`

**This is the newest artifact in either repo** (WITNESSED: `/home/bork/w/vdc/2/autoharn-panel/first_observations`, mtime 2026-07-28 19:14, untracked). It is the maintainer's own first sighted reading of the built SPA, and it should be read before any design work. Verbatim:

1. The one long horizontal list (the nav tabs) probably should be vertical, since right now you have to scroll to see it all
2. No apparent attempt at responsive design — playwright is available and should be used
3. Partially incorrect conclusion about graph rendering: (a) the graph can be obtained locally; (b) ECharts should be used for rendering, see e.g. `/home/bork/w/omega/frontend/src/components/charts/CardTreeWidget.vue`
4. No safe mode/observer mode
5. Similarly, no unsafe type operations (i.e. those that write to the ledger)
6. No missives view
7. Timer based refresh annoying (especially while scrolling); may need backend extension to allow SSE
8. No capabilites view (what, among the many options selected, does this given deployment use?)
9. Similarly, no way to create a configuration for a new world (in other words, like the autoharn setup TUI but which merely exports the necessary configuration and instructions for deploying it); should be usable without even connecting to a deployment
10. No roles view
11. Not ADR-0017 compliant

Six of these eleven (4, 5, 6, 8, 9, 10) are surface-access questions and are carried into §4 as rows. Items 1, 2, 3, 11 are UI-craft matters outside this document's remit. **Item 7 is notable because it names a required upstream change** ("may need backend extension to allow SSE") — the boundary has no push route by design, so this is a decision for autoharn, not a panel workaround.

---

## §4 Gap table

Prior rows carried forward with a status column; new rows appended. Gaps are stated as gaps; shape hints are one line and non-binding.

### 4.1 Surface that exists but is panel-inaccessible

| Surface | Prior status | Status now | Note / shape hint |
|---|---|---|---|
| 21 of 25 allowlisted views unconsumed | GAP | **CHANGED — 11 of 25 now consumed** | `GenericViewTab.vue` is the generic renderer the prior doc's shape hint asked for; it exists and works. |
| `review_verdicts` | GAP | **RESOLVED** | Consumed by the Commission tab. |
| `reservations_outstanding` | GAP | **STANDING** | Still unconsumed. |
| `/rows/{id}/history` | GAP | **RESOLVED** | `ItemDetail.vue:134-135`. |
| `/rows/asof/{ts}` + `asof-export` bundle | GAP | **STANDING** | The auditor's first ask. |
| `/artifacts/*` | GAP | **STANDING** | |
| `/standing/principals` | GAP | **CHANGED — consumed** by `commissions.ts:110` | But `principal_relations`, `principal_role_bindings`, `principal_keys`, `principal_competences` remain unconsumed — the SoD picture is still unrendered. |
| All six missive views | GAP | **STANDING** — now with the maintainer's own item 6 behind it | Inter-world correspondence is still entirely invisible. |
| `model_attestations`, `model_defeated_rows`, `credited_current` | GAP | **RESOLVED** | All three wired via `GenericViewTab`. |
| Five of six write surfaces | GAP | **STANDING** | Only `write/review`. |
| `led work` verbs — no boundary route | GAP | **STANDING** | `/work/items` remains the only work-related route. |
| Verb-level reports with no HTTP surface (`judge`, `audit`, `doctor`, `verify-chain`, `attest-tags`, `distance-to-clean`, `pickup`, `fixture-sweep`, `courier`, **`dispatch`**, **`service`**) | GAP — "largest single gap" | **STANDING and larger by two** | Still the largest single gap. Two of them (`attest-tags` at 69 uncovered claims; `distance-to-clean`) are the ones carrying live red state. |
| Kernel SQL views absent from `VIEW_REGISTRY` | GAP (16 named) | **STANDING, now 18** | s60's `entitlement_class_roles` and s61's `signed_commissions` both joined the unservable set. Both are precisely what a signature/entitlement tab would need. |
| **`GET /kinds`** (NEW) | — | **NEW GAP** | Shipped, unconsumed. It is the client-side-validation source consequence #2 requires. |
| **s64's five delegation-condition columns on `principal_relations`** (NEW) | — | **NEW GAP** | Served today; nothing renders them. |
| **`/health`'s `protocol_version` / `authn_mode`** (NEW) | — | **NEW GAP** | The panel reads `/health` but for `capabilities` only. |

### 4.2 Surface the panel assumes but autoharn does not provide

| Assumption | Prior status | Status now |
|---|---|---|
| `/api/events` + `/api/watermark` SSE | GAP | **RESOLVED as an assumption** — code deleted, replaced by 5s polling. **But the underlying need is now the maintainer's item 7**: polling is "annoying (especially while scrolling)". No push route exists; adding one is an autoharn decision. |
| `/api/rows` with limit/offset/facets, server-side search | GAP | **STANDING as a design constraint.** Board fetches to exhaustion and filters locally. |
| `/api/profiles`, `/api/item/{id}/obligations`, `/api/commissions` | GAP | **RESOLVED** — deleted; Commission tab rebuilt from served primitives. |
| OpenAPI schema at `:8420/openapi.json` | GAP | **RESOLVED** — script deleted; only `SPEC.md:126-130` still asserts it. |
| `/health` carrying `read_only`, `extensions_enabled`, `schema` | GAP | **STANDING.** The SPA still infers read-only from `!capabilities.s43_boundary`. |
| Cross-origin fetch | GAP | **STANDING** — dev proxy only; no production story. |
| `./legacy/led` as work-verb fallback | GAP | **RESOLVED** — retired both sides. |
| A `boundary-service` principal as acting identity | GAP | **STANDING.** `serving/README.md:395-406` still calls it "**a spec defect** worth the maintainer's attention." The new identity conduit addresses *caller* identity, not the service's own. |
| **A raw/superseded-inclusive ledger read** (NEW) | — | **NEW GAP, filed both sides** — autoharn work item `rows-bulk-superseded-read` (row 154); the panel removed its dead superseded toggle rather than fake it. |

### 4.3 Expectations no surface serves yet

| Expectation | Prior status | Status now | Note |
|---|---|---|---|
| Any caller identity on reads | open decision | **STANDING** | Unchanged; `authn_mode: single-operator`. |
| Per-end-user attribution on writes | RESERVED | **CHANGED — partially built.** The identity conduit exists (minted-principal + vendor-stamp headers, `enforce` posture available). Still blocks multi-user: the service's *own* principal problem is unfixed. |
| A refusals read surface | GAP | **STANDING — and now more valuable.** s65/s67/s68 make a refusal row genuinely informative (attempted kind, typed absence reasons). One `/views/refusals` entry would make the completeness oracle legible. |
| Signature ceremony visibility | GAP | **STANDING.** `signed_commissions` (s61) exists in SQL and is not servable. |
| Refusal legibility as a UI concept | GAP | **STANDING** — but `GET /kinds` plus the s60/s62/s64 remedy-bearing refusal texts now supply the raw material for disable-with-reason. |
| Audit-trail review as a workflow | GAP | **PARTIAL.** Queues render; the assembled open-item → antecedent → countersign → discharge flow still does not. `ItemObligationsPanel.vue:35` still ships a hardcoded stub co-sign status. |
| Human-readable rendering with vocabulary labels | GAP | **STANDING and worse** — GLOSSARY covers none of the new vocabulary; `disposition` is an unresolved collision (§2). |
| World creation from the panel | GAP | **STANDING — now an explicit maintainer ask** (punch-list item 9), with a sharper shape than the directive gave: export the configuration and instructions, "usable without even connecting to a deployment." |
| Multi-world in one instance | GAP | **RESOLVED.** One SPA, one hub, runtime world selection across four deployments. |
| Cross-checking the world's own health | GAP | **STANDING and worse** — `attest-tags` now 69 uncovered claims (was 53); both it and `distance-to-clean` remain invisible to any UI. |
| **Safe / observer mode** (NEW, punch-list 4+5) | — | **NEW GAP** | The panel has exactly one write path today, so "safe mode" is currently a UI affordance over a near-read-only client — but the maintainer is naming it as a required, explicit mode with writes visibly typed as unsafe. |
| **A capabilities view** (NEW, punch-list 8) | — | **NEW GAP with an upstream blocker** | `/health`'s manifest stops at s45 and knows nothing of s58–s68. The panel cannot build an honest capabilities view against the current manifest; the manifest itself needs extending. |
| **A roles view** (NEW, punch-list 10) | — | **NEW GAP** | `principal_role_bindings` and `entitlement_class_roles` are the data; the first is served and unconsumed, the second is unservable. |
| **Missives view** (NEW, punch-list 6) | — | **NEW GAP** | All six views served; nothing renders them. |

### 4.4 Documentation gaps that are themselves user-facing surface

Refusals-that-teach and operator docs are surface; these are stated as gaps, not fixed here.

| Gap | Witness |
|---|---|
| **Missives and `courier` have zero user-facing documentation.** Shipped today; the only prose homes are `design/FABLE-MISSIVES-KERNEL-SPEC.md`, source docstrings, and the `led --help` usage block. | grep across `user-guide/*.md` + `CLAUDE.md`: five hits, none explanatory. |
| **`ORCH-CAPABILITIES.md` — the "what can be trusted" document — has no item for `doctor`, `asof-export`, or `courier`/missives.** Its sweep record stops 2026-07-18. | Zero grep hits for each. |
| **`./autoharn service` appears in no user-facing doc** except one line of `WORLD-REBIRTH-RUNBOOK.md:62-74`, which prescribes `stop && start` — not the purpose-built `restart` that shipped the day before. | DOC-SOURCED. |
| **Three-way verb-roster split, now wider.** Dispatcher 13+service; user-guide/README 10; world dispatcher 11. `attest-tags`, `courier`, `service` are in the dispatcher, are *not* marked repo-specific, and appear in no user-facing roster. | `autoharn:42-58` vs `USER-GUIDE.md:236-246` vs the templates glob. |
| **GLOSSARY covers none of** missive, courier, dispatch, entitlement, missive-disposition; and `disposition` collides across two closed vocabularies. | 66 `###` terms, WITNESSED by grep. |
| **The 2026-07-28 rebirth and the one-hub consolidation live only in config-file comments,** `.claude/HOOKS.md`, `roles/README.md`, and design headers. Zero mentions in README, GLOSSARY, ORCH-CAPABILITIES, or any user-guide page. | grep. |
| **The prior doc itself is now stale on exactly one point:** its §3.3 item 2 and §4.3 still describe the two-process/two-port shape as an open problem. | `PANEL-GXP-SURFACE-KICKSTART-2026-07-26.md:240,295`. |
| **HAZARD: live refusal/instruction texts spell `./led`,** a command that exists nowhere. Fourteen sites across `led.tmpl`, `pickup.tmpl`, `legacy-pickup.tmpl`. | §1.2, WITNESSED via `pickup`. |

---

## §5 Closure statement

**What I enumerated.** (a) The root CLI: 13 verbs + `service`, every one's `--help` observed, plus the four non-umbrella root executables; the new `dispatch` verb and `service restart` in full. (b) `led`: write kinds, ten read forms, three governance forms, eleven `work` sub-verbs, fourteen `principal` usage lines, three `artifact` sub-verbs, **two new `missive` sub-verbs**, `--json` ingest. (c) The boundary: 15 route patterns (one new), the 25-name view allowlist (unchanged), six write surfaces + artifacts (unchanged), the refusal taxonomy plus **two new typed refusals**, the **identity conduit**, the **diagnostic log layer**, `/health`'s widened shape. (d) The artifact classes a user reads, with live output for nine of them against the new world. (e) The kernel mechanisms, s15–s61 as the prior doc left them **plus s63–s68 in full**, with file:line and verbatim refusal text. (f) The scaffolding surface, including the derived 11-verb world roster and `--refresh-dispatcher`. (g) The panel repo's current state: 17 tabs, 14 wired, 2 stubbed, one write path, its config, its freeze, its drift, and the maintainer's own eleven-item punch list.

**How I know the enumeration is complete, and where that knowledge stops.**
- **The verb roster is structurally complete.** `./autoharn --help` is generated from the dispatcher's own dispatch table (`autoharn:42-58`), which the `seen-red/umbrella-cli-dispatch-parity` fixture greps directly against `ls libexec/autoharn/`. Cross-checked by hand: 13 table rows, 13 libexec files, plus `service` handled in-dispatcher at `autoharn:110-116`. They match.
- **The world roster is now structurally complete too, and by a stronger mechanism than before.** `bootstrap/new-project.sh:162-170` states its own ADR-0000 Rule 2(a) closure: the universe is exactly `bootstrap/templates/*.tmpl` minus the nine enumerated exclusions, and a template without an `# autoharn-verb-desc:` header refuses generation. Computed: 11. "Shipping the template IS shipping the verb."
- **The boundary route list** came from every `@app.get`/`@app.post`/`add_api_route` call site in the single file that defines routes; the view allowlist from the single `VIEW_REGISTRY` dict that gates them, checked before the kernel is touched.
- **The kind vocabulary** is the kernel's own CHECK at head. I traced the *last* re-issue rather than assuming the last delta: `grep -l ledger_kind_check kernel/lineage/*.sql` returns s57, s58, s60, s61, s65 only, and only s61 carries an `ADD CONSTRAINT`. 33 members, unchanged since the prior doc.
- **The birth chain** was read directly from `LINEAGE_CHAIN` (`bootstrap/new-project.sh:778`) rather than from any doc that describes it — which is how the prior doc's open item 4 got its (faithful but stale) answer.
- **The unservable-view cross-check** was re-run from scratch: 18 current-era kernel views have no `/views/` route, up from the prior doc's 16 by exactly `entitlement_class_roles` (s60) and `signed_commissions` (s61).
- **Where it stops.** The *docs* roster is still not structurally guaranteed the way the verb rosters are, and the gap has widened rather than closed: three rosters, three counts (13+service / 11 / 10), and three verbs (`attest-tags`, `courier`, `service`) that belong to a world or to this checkout and appear in no user-facing list at all. Any panel presenting "autoharn's verbs" as one list will be wrong for at least one audience.

**Prior doc's open items — disposition.**

1. **Part 11 market judgment** — **STANDING.** This document frames and claims nothing.
2. **Whether unauthenticated reads stay** — **STANDING.** Reads remain unauthenticated; `authn_mode: single-operator`. *Writes* gained an identity conduit, so the read side is now the sole remaining anonymous surface — the question is sharper, not answered.
3. **Two processes, two ports vs one-instance-multiplexed** — **RESOLVED.** One hub on 8433 serving four deployments; one SPA with runtime world selection; 8422 retired.
4. **s60/s61/s62 not in any birth chain** — **RESOLVED.** `LINEAGE_CHAIN` births s15→s68. Every entitlement and signature affordance a panel might build now aims at a substrate both live worlds actually run.
5. **`attest-tags`: 0 keys, 53 uncovered claims** — **CHANGED, worse: 0 keys, 69 uncovered claims.** Work item `maintainer-key-generation` is open and is the maintainer's own act.
6. **UNVERIFIED by choice** — carried forward and slightly widened. I did not run `judge`, `audit`, `courier`, `fixture-sweep`, `migrate`, `dispatch`, or any `service` subcommand; I issued no direct HTTP request to 8433; I did not read `engine/lp/*.lp` or the GPG ceremony templates' source. Boundary behavior above is read from source, not observed on the wire. I did run the read-only health/debt verbs — see §0 for that judgment call.
7. **The row-1452 incident** — the row is settled evidence in the dust world `autoharn2`. **No equivalent occurred this pass.** The mechanism it revealed is unchanged and remains the most important constraint on panel design.

**What remains open, newly.**

1. **The maintainer's punch list is unanswered** (§3.5). Six of its eleven items are surface-access questions carried into §4; item 7 (SSE) names a change the boundary would have to make.
2. **The capability manifest stops at s45**, so no honest capabilities view is buildable today — an upstream blocker, not a panel omission.
3. **No verb sends a missive.** Receive and dispose have verbs; send is hand-authored JSON through `led --json ledger`.
4. **No superseded-inclusive ledger read exists on any surface.** Filed as work item `rows-bulk-superseded-read` (row 154).
5. **`judge: AGREE` has a narrower perimeter than any badge would suggest** — and the s61→s63 incident is the worked proof that the gap is real, not theoretical.
6. **Two hazards found in reach and flagged, not fixed:** the `./led` spelling in live refusal and instruction text (fourteen sites, inherited by every world born today), and the panel's `attestations/README.md` asserting an empty state over a non-empty file.
7. **Documentation is the widest gap in this update.** Missives, courier, `dispatch`, `service`, and the whole s58–s68 vocabulary shipped between the two surveys with no user-guide page, no GLOSSARY entry, and no `ORCH-CAPABILITIES` item. A panel that renders vocabulary labels sourced from GLOSSARY today will render blanks for the newest and most GxP-relevant half of the record.