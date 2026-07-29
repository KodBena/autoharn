<!-- doc-attest-exempt: as-delivered survey record, filed verbatim 2026-07-29 (the maintainer's
third-run commission "send out again an Opus, same prompt (blind to previous ones) with another GxP
run", brief COMMISSION-PANEL-GXP-SURFACE-FRESH-2.md; independence clause forbade all three prior
PANEL-GXP survey documents, compliance stated in the report's own preamble. Opus exception to the
Sonnet-default authoring policy maintainer-granted by the request itself). ADR-0017 legibility loop
NOT yet run; pending, same as its siblings at filing time. Removal condition: the loop's attestation
record supersedes this exemption. -->

**Provenance:** produced by the commissioned fresh-eyes surveyor (Opus, 2026-07-29), the third
independent run. Filed verbatim by the coordinator; the only transform is reversing the harness's
control-tag neutralization (escaped angle brackets restored). Its four in-passing hazards (H1 SSE
subscriber-slot leak, H2 migrate-manifest glob drift, H3 root-roster missing world verbs, H4 grace
posture) were converted to work items (ledger rows 429/430/431; H4 is the known v1 posture, routed
to the maintainer) with fixes for H1/H2 dispatched the same hour.

I have completed the survey. Here is the report.

---

# autoharn's user-facing surface — a GxP access map for the autoharn-panel project

**Independent third survey, 2026-07-29.** No prior survey of this surface was read (three exist by filename: `design/PANEL-GXP-SURFACE-KICKSTART-2026-07-26.md`, `design/PANEL-GXP-SURFACE-UPDATE-2026-07-28.md`, `design/PANEL-GXP-SURFACE-FRESH-2026-07-28.md`, plus `/home/bork/w/vdc/2/autoharn-panel/docs/consults/2026-07-29-gxp-gap-closure-audit/`). Two grep results incidentally echoed three lines from one of them; those facts are independently re-witnessed below from primary sources and cited to the primary source only.

**Witness classes:** WITNESSED (observed output shown) · DOC-SOURCED (file:line + quote) · GAP · UNVERIFIED (with blocker).

**Read-only compliance:** no file was written, no commit, no branch, no state-changing command, no refusal probed. Live traffic was plain GETs against 127.0.0.1:8433 only.

---

## §0 — Four hazards found in passing, stated first because they are live

Per CLAUDE.md's engineering-responsibility clause, these are surfaced loudly rather than filed at the bottom.

### H1 (CRITICAL, live now) — the SSE live-signal surface is hard-down on both worlds; subscriber slots leak permanently

WITNESSED — the boundary refuses every new `/events` subscriber on both deployments:

```
$ curl -sSN --max-time 5 http://127.0.0.1:8433/d/autoharn3/events
{"disposition":"sse_saturated","max_clients":16,"message":"this hub already has
MAX_SSE_CLIENTS=16 concurrent SSE connections open ... Retry after a short backoff."}
$ curl -sSN --max-time 5 http://127.0.0.1:8433/d/experience4/events
{"disposition":"sse_saturated","max_clients":16, ...}
```

WITNESSED — there are **no live SSE clients**. The service is a single process with no children, holding **three socket file descriptors** in total (the listener plus two), and the kernel shows zero ESTABLISHED connections to 8433 (only `LISTEN` plus TIME-WAIT residue from my own probes):

```
$ ss -tan | grep 8433 | awk '{print $1}' | sort | uniq -c
      1 LISTEN
     25 TIME-WAIT
$ ps -o pid,ppid,etime,cmd -p 3508295
3508295  1  05:13:16  /usr/bin/python3 -m serving.boundary_service --config .../boundary-multiplex.toml --port 8433 ...
$ pgrep -P 3508295 -a          # (no children)
$ ls -l /proc/3508295/fd | grep -c socket
3
```

So `sum(len(h.subscribers) for h in sse_hubs.values()) >= 16` while the process holds three sockets. Sixteen subscriber slots are held by connections that no longer exist, and they are held for the life of the process.

DOC-SOURCED — the mechanism, `/home/bork/w/vdc/1/autoharn/serving/boundary_service.py:3792-3814`:

```python
async def _stream():
    queue: asyncio.Queue[int] = asyncio.Queue()
    known_head = await hub.connect(queue)      # registers the subscriber, OUTSIDE the try
    last_sent = resume_from
    try:
        ...
    finally:
        await hub.disconnect(queue)            # never reached if connect() raised/was cancelled
```

`_SseHub.connect()` (`serving/boundary_service.py:2864-2885`) adds the queue to `self.subscribers` under the lock and *then* awaits a synchronous DB head-poll on a worker thread (`await asyncio.to_thread(_sse_query_head, self.cfg)`, `:2880`). If the client disconnects — or the request task is cancelled, or `to_thread` raises anything outside `_SSE_POLL_EXCEPTIONS` — during that await, the exception propagates out of `connect()` *after* registration, the generator's `try` block was never entered, and `disconnect()` (`:2887-2894`) never runs. The queue stays in `subscribers` forever, which also pins `watcher_task` alive forever (`subscribers` never empties). Classic acquire-outside-try; the leak window is exactly the duration of one psql head query, which widens under load.

Consequences for the panel specifically: `useLiveUpdates.ts` is SSE-primary with a poll fallback and already branches on `disposition === 'sse_saturated'`, so the panel degrades honestly rather than lying — but the live-update path the maintainer asked for (`first_observations` item 7, "timer-refresh annoying, may need SSE") is currently not functioning, and the refusal's own advice ("Retry after a short backoff") can never succeed. Only `autoharn service restart` clears it, and it will re-accumulate.

Secondary, same route: the 16-client bound is **hub-wide across all deployments** (`:3782-3783`, deliberately per `serving/boundary_service.py:3746-3753`). One world's viewers can starve another's; there is no per-deployment fairness. For a multi-viewer GxP panel, 16 total is a low ceiling even without the leak.

### H2 (HIGH) — `/meta.lineage_head` reports a 50-generation-stale value, and `./autoharn migrate` would report a world at s69 as "already at the lineage head"

WITNESSED — against a world whose real chain runs to s69:

```
$ curl -sS http://127.0.0.1:8433/d/autoharn3/meta | python3 -m json.tool | grep lineage_head
    "lineage_head": "high_watermark_1",
```

WITNESSED — the cause, read-only:

```
$ python3 -c "import sys; sys.path.insert(0,'bootstrap'); import migrate_core as m; mf=m._manifest(); print(len(mf), mf)"
1 ['high_watermark_1.sql']
```

DOC-SOURCED — `bootstrap/migrate_core.py:145-171` derives the birth-chain manifest by regex over `new-project.sh`'s `psql -f` list: `re.findall(r'kernel/lineage/([A-Za-z0-9_.\-]+\.sql)"', text)`. That `-f` list **no longer exists**: `bootstrap/new-project.sh:1183-1222` now *generates* the apply list with a glob loop (`for _lf in "$AUTOHARN_ROOT"/kernel/lineage/s[0-9]*-*.sql`) and builds the `-f` arguments with `set --`. Only the single literal `-f "$AUTOHARN_ROOT/kernel/lineage/high_watermark_1.sql"` at `:1221` still matches the regex.

The generator change was a deliberate drift fix (`gates/lineage_chain_coverage.py:13` was rewritten for it, and `new-project.sh:1179-1181` says so in terms: *"it does not, and structurally cannot, regex-scan a `-f` list that no longer exists here"*). The gate was updated; **`migrate_core._manifest()` was not**. It is the second consumer, and it fails silently rather than loudly.

Two consequences, both decidable from source:

- `serving/boundary_service.py:1793-1811` (`_lineage_head`) walks that one-entry manifest, runs `high_watermark_1.detect.sql`, gets `t`, and returns `"high_watermark_1"` — for every deployment, forever. A panel that renders `/meta.lineage_head` as "this world's kernel generation" displays a value ~50 generations stale. Under GxP this is a mislabelled system-version field on the record-keeping system itself.
- `bootstrap/migrate_core.py:936-947`: `manifest` has one entry, `_current_head_and_missing` finds it applied, `missing` is empty, and `main()` prints `"migrate: '<name>' is already at the lineage head. Nothing to migrate."` and returns 0. A migration verb that reports clean while fifty deltas are unapplied is fail-dangerous. (Not exercised — `migrate` writes; read from source only. Mitigated in practice by runs-are-linear, which makes `migrate` rare, and by `migrate` being autoharn-repo-specific and never scaffolded into worlds.)

Panel-facing shape hint: `/meta` currently offers no trustworthy "which kernel generation is this world at" field, which is precisely the field a panel needs to warn that `experience4` (s68) and `autoharn3` (s69) enforce different rules.

### H3 (MODERATE) — the electronic-signature verification verb is unreachable from autoharn's own operator surface

WITNESSED — autoharn's own root roster is thirteen verbs plus `service` (`./autoharn --help`): `led judge pickup distance-to-clean attest-tags audit doctor migrate asof-export verify-chain courier service fixture-sweep dispatch`, from the dispatch table at `/home/bork/w/vdc/1/autoharn/autoharn:42-58`.

WITNESSED — a scaffolded world's roster is eleven verbs (`/home/bork/w/vdc/2/autoharn-panel/autoharn:21-31`): `asof-export attest-doc audit courier distance-to-clean doctor judge led pickup verify-chain verify-commission`.

The asymmetry: **`verify-commission` and `attest-doc` exist only in worlds, never in autoharn's own repo.** `verify-commission` is Rung 2 of the GPG trust layer — the verb that returns `VERIFIED | UNSIGNED | FORGED-OR-CORRUPT` on a signed commission (`bootstrap/templates/verify-commission.tmpl:1-40`). It is the single most GxP-load-bearing verb in the corpus (an e-signature verification act), and an operator standing in the autoharn checkout cannot run it through `./autoharn`. The world roster is glob-derived from `bootstrap/templates/*.tmpl` (`bootstrap/new-project.sh:216-254`, forgetting a verb is "unrepresentable"); the root roster is a hand-maintained heredoc that can and did drift from it.

### H4 (MODERATE) — attributability is off by default on both live worlds

WITNESSED — both deployments report `"identity_enforcement": "grace"` from `GET /health`. DOC-SOURCED — `serving/boundary_models.py:277-290`: grace *"accepts an anonymous write unchanged — byte-identical"*; only `"enforce"` refuses an authority-bearing write carrying neither vendor stamp nor minted-principal header. The live hub config `/home/bork/w/vdc/1/autoharn/boundary-multiplex.toml` sets no `identity_enforcement` key at all, so the default applies.

The panel sends **no identity headers on any request** (`frontend/src/core/services/boundary-client.ts:115` for GETs, `:133` for POSTs — `Content-Type` only). Both of its write paths therefore resolve to the `"anonymous"` case (`serving/boundary_service.py:1327`) and currently succeed. This is the ALCOA **attributable** leg, and it is the one leg that is presently unenforced end-to-end. It is also a latent break: flipping the config to `"enforce"` refuses both panel writes with a 403, and the panel has no code to mint or attach an identity header — it reads `identity_enforcement` into its health type (`frontend/src/core/services/types.ts:122`) but nothing branches on it.

---

## §1 The user-facing surface, enumerated

### 1.1 The CLI — `./autoharn <verb>` (thirteen verbs + `service`)

The dispatch table is the single roster (`/home/bork/w/vdc/1/autoharn/autoharn:42-58`); the parity fixture `seen-red/umbrella-cli-dispatch-parity` greps it against `ls libexec/autoharn/`. All fourteen `--help` outputs were captured (WITNESSED).

| Verb | Trust root | What it is |
|---|---|---|
| `led` | boundary (HTTP) | the ledger read/write CLI — see 1.2 |
| `judge` | **direct/independent** | SQL-vs-ASP differential: `AGREE \| DIVERGE_BY_DESIGN \| DIVERGE_DEFECT \| QUARANTINED`, plus the four `work_item_violations` classes named individually; banks a DerivationRecord pair |
| `pickup` | boundary | resume-context hydration — six sections, see 1.4 |
| `distance-to-clean` | boundary | one-line-per-section debt count; exit 0 iff TOTAL is 0 |
| `attest-tags` | direct (git+gpg) | verifies `ratified/*` tags against `law/keys/*.asc`; `--json` available |
| `audit` | **direct/independent** | contemporaneity correlation vs `.claude/logs/*.jsonl`: `CONTEMPORANEOUS \| BATCHED_DECLARED \| LATE_DECLARED \| BACKFILL_SUSPECT` |
| `doctor` | **direct/independent** | nine-fact PASS/FAIL/SKIP world health; read-only, writes no file |
| `migrate` | direct (admin DDL) | autoharn-repo-only; rehearsal + history-byte-identity + per-delta detect/verify (see H2) |
| `asof-export` | boundary | `read` (as-of reconstruction) and `export` (txt+json+`manifest.sha256`, unsigned by design) |
| `verify-chain` | **direct/independent** | row-hash chain walk; `INTACT/EMPTY/UNAVAILABLE/CANNOT-VERIFY/BROKEN` + tail-deletion witness + refusal-oracle; `--head` emits the signed-genesis input |
| `courier` | boundary | receiver-pull missive transport; never writes to a foreign boundary, never transforms |
| `service` | process control | `status\|start\|stop\|restart` with drained handover, `--drain-timeout`, `--force-kill` |
| `fixture-sweep` | mixed | autoharn-repo-only; read-only re-execution of every `gates/fixture_census.py` family |
| `dispatch` | boundary | `mint`/`close` a delegate principal; refuses without an explicit `--deployment`/`LEDGER_DEPLOYMENT` |

WITNESSED, three read-only diagnostics run live:

```
$ ./autoharn doctor
deployment.json  PASS ... database reachable PASS ... schema + kern schema exist PASS
lineage high-water/epoch PASS chain_high_water.max_id=418, migration_epoch.epoch=0
principals registered PASS 11 row(s)   courier principal registered PASS
world_identity populated PASS world_name='autoharn3'
./autoharn led answers a read query PASS   boundary URL PASS ... HTTP 404; pidfile ... consistent
TOTAL: 0 FAIL, 9 PASS, 0 SKIP  (0 FAIL = healthy)

$ ./autoharn distance-to-clean
review-gap: 0 | question-status: 0 open of 2 | work-violations: 0
work-items: 5 open+claimed | work-review-gap: 1 | doc-attestation: off
TOTAL debt: 6

$ ./autoharn verify-chain
verify-chain: INTACT -- 409 row(s) walked, head id=418 hash=53fa11dc...
verify-chain: TAIL-COVERAGE-CONFIRMED -- witness max_id=418 agrees with walked max_id=418
verify-chain: REFUSAL-ORACLE-CONFIRMED -- 15 journaled write_refused row(s) == sequence count 15
```

**World-only verbs** (in every scaffolded world, absent from autoharn's own root — see H3): `verify-commission` (`VERIFIED | UNSIGNED | FORGED-OR-CORRUPT` + two typed refusals for gpg-missing / no-committed-key, `bootstrap/templates/verify-commission.tmpl:1-40`); `attest-doc record|check` (ADR-0017 A:B:C attestations; `ATTESTED | STALE | NO-ATTESTATION`, `bootstrap/templates/attest-doc.tmpl:1-40`).

**Operator surfaces outside the umbrella entirely** (DOC-SOURCED):
- `python3 -m tools.setup_tui <dest-dir>` — the **primary onboarding UI**, a Textual wizard with a sidebar section tree and one commit step (`README.md:31`, `tools/setup_tui/` — 38 modules). This is the largest user-facing surface in the project and it is not a `./autoharn` verb.
- `./orchlog` — the restarting-orchestrator changelog over `orchlog.d/`.
- `./otel-attest`, `./otel-watch` — model-provenance sentry (post-hoc attestation and always-on watchdog). Rebasing them into the umbrella is an open work item, `otel-verbs-umbrella-rebase` (WITNESSED in `led work list`).
- `./extract-context` — world-context extract/ingest, `--deployment`-scoped.
- `hooks/` — eighteen Claude Code hooks the operator experiences as refusals: the change gate, `stamp_intercept.py` (vendor stamps), `pretooluse_sql_block.py` (raw-SQL ban), `stop_clean_exit.py` (the governance-debt stop gate), and others (WITNESSED via `.claude/settings.json`).

### 1.2 `led` — the full subcommand tree

Implementation `bootstrap/templates/led.tmpl` (3,272 lines) via `libexec/autoharn/led`. Every read is a paginated GET walked to completion client-side; every write is a `POST /write/<surface>` whose kernel `write_verdict` is passed through byte-verbatim.

**Write kinds.** The CLI imposes **no vocabulary of its own** — `cmd_generic` (`led.tmpl:2891-2951`) forwards `kind` verbatim. The closed vocabulary is the kernel's `ledger_kind_check`, WITNESSED live at `GET /kinds` — **33 kinds**: `assumption decision question verification finding snag revision note review work_opened work_claimed work_depends_on work_closed commission work_violation_disposition principal_registered principal_suspended principal_revoked principal_standing_declared principal_relation_asserted principal_role_bound principal_key_bound principal_competence_granted write_refused model_identity_attested belief obligation_revoked missive_sent missive_received missive_disposed entitlement_class_configured commission_signature_verified principal_key_possession_verified`.

**Twelve shared flags, front-anchored before the kind word** (`led.tmpl:2965-2988`): `-f -e --supersedes --amends --amends-scope --answers --refs --concern --evidence --confidence --event-time --signature-witness`. The flag-order asymmetry is load-bearing enough to be rule 2 of `led briefing`.

**Eight statement grammars, refused at construction** (`led.tmpl:1462-1487`): `resource:` (class ∈ solver|service|backend|binary|library; tier ∈ available|blessed|mandated|forbidden), `estimate:`, `actual:` (token-OOM ∈ 1K|10K|100K|1M|10M+), `taxon:`, `interface:`, `outcome:`, `review-done:`, `review:`. Plus a garbage-statement guard (`:1512-1542`) that refuses captured CLI/help text, an `--evidence` dereference guard (`:1576-1620`), and a warn-only path-shape scan.

**Reads:** `--recent [N]`, `current [N]`, `show <id>`, `question-status`, `review-gap`, `stamp-distinctness`, `standing`, `decomposition-review-status` (prints `mode:` / `countersign_obligation:` / `verdict: OFF|VACUOUS|ARMED-ENFORCING|ARMED-OBSERVING`), `briefing` (no DB access; the three fresh-agent rules).

**`led work` — eleven sub-verbs:** `open` (`--parent`, `--discharge composite`, `--supersedes` with slug-burn warning) · `claim` · `depends` (`--type blocks-close|blocks-start|informs`, `--supersedes` with three-step validation) · `close` (resolutions `shipped|superseded|dropped|deferred`; exactly one of `--review-witness` / `--review-deferred` / `--review-bookkeeping`; claim-before-close gate; `--review-bookkeeping` requires `commit:<7-40 hex>` verified against a real git object) · `list [--all]` · `violations` · `asof <ts>` · `review-gap` · `startable` · `resolve-violation` (`reissued|retired`; class re-derived, never parsed from text) · `supersede-cascade`.

**`led principal` — fourteen sub-verbs:** `declare-standing`, `undeclare-standing`, `suspend`, `lift-suspension`, `revoke`, `relate`/`unrelate` (relations `acts-for|dispatched-by|same-natural-person|succeeds`), `bind-role`/`release-role`, `bind-key`/`revoke-key`, `attest-possession`, `grant-competence`/`withdraw-competence`. Only `--event-time` is honoured from the shared flags; every other is refused by name.

**`led review <entry-id> <verdict> <independence> <statement...>`** — verdicts `attest | attest_with_reservations | refuse`; independence, widened to five at `kernel/lineage/s55-dispatch-grain-independence.sql:115-117`: `self-review, technical, managerial, financial, disclosed-isolated-dispatch`.

**`led obligate <scope> <assigned-by> <obliged-actor>`** and **`led obligate revoke <scope> --reason "<text>"`** (reason mandatory — a revocation's stated ground is part of the record, s57).

**`led missive list | dispose <receipt> <consumed|declined|superseded-unread|escalated>`** — **there is no `send`**, see §4/G1.

**`led artifact put|get|stat`** — content-addressed store with client-side re-hash on `get` and a `CORRUPT STORE` teach-text on mismatch.

**`led --json <ledger|review|registration|obligation> <file|->`** — note `obligation_revoke` and `missive_dispose` are *not* reachable through `--json` though they exist as write surfaces; and the eight grammars and the garbage guard are disclosed as **not running** on this path (`led.tmpl:1141`).

**Exit codes** (`serving/boundary_cli_client.py:23-60`): 0 kernel-accepted · 1 kernel-refused (journaled `write_refused`) or a merits-based CLI refusal · 3 boundary-refused · 4 unreachable/client/usage · 2 deliberately never used.

**Environment identity:** `LED_ACTOR` (name→id; unregistered refuses loudly, never a silent fallback), `AUTOHARN_MINTED_PRINCIPAL` → `X-Autoharn-Minted-Principal`, and the vendor stamp scraped out of `PGOPTIONS` (written by `hooks/stamp_intercept.py`) → five `X-Autoharn-Vendor-*` headers.

### 1.3 The boundary service — 21 routes

One process, port 8433, multiplexing `autoharn2`, `autoharn3`, `experience3`, `experience4` (`boundary-multiplex.toml`). Every route carries a mandatory `/d/{deployment}` prefix; FastAPI's `/docs`, `/redoc`, `/openapi.json` are disabled outright (`serving/boundary_service.py:2951-2953`).

**14 GET:** `/health` · `/rows/current` (`?after_id&limit&include_superseded`) · `/rows/{id}` · `/rows/{id}/history` (full supersession chain both directions) · `/rows/asof/{ts}` · `/credited` · `/standing/principals` · `/work/items` (slug-keyset) · `/views/{view}` · `/meta` · `/kinds` · `/attestation` · `/artifacts/{hash}` + `/artifacts/{hash}/stat` · `/events` (SSE).

**7 POST:** `/write/ledger`, `/write/review`, `/write/registration`, `/write/obligation`, `/write/obligation_revoke`, `/write/missive_dispose` (all six generated from `WRITE_SURFACES`, `:1031-1045`, each mapping to an s43 SECURITY DEFINER kernel function), plus `/artifacts` (separate because a base64 payload can approach 1.4 MiB and would blow `MAX_PSQL_ARG_BYTES`).

**VIEW_REGISTRY — 31 views**, WITNESSED live from `GET /meta`: `countersign_obligation, countersigned_in_force, credited_current, discharging_attest, missive_delivery_audit, missive_open_threads, missive_outbound, missive_receipts, missive_stale, missive_undisposed, model_attestations, model_defeated_rows, principal_competences, principal_keys, principal_relations, principal_role_bindings, question_status, reservations_outstanding, review_gap, review_stamp_distinctness, review_verdicts, standing_decisions, work_bookkeeping_closes, work_edge_blocks_close, work_edge_parent, work_item_current, work_item_violations, work_review_gap, work_role_census, work_startable, work_violation_history`. Two views are **deliberately excluded and named** rather than silently omitted: `work_edge_obligation` and `work_item_descendants`, both because no row-identifying column survives keyset pagination (`serving/boundary_service.py:747-770`).

`work_role_census` (s69-era, ledger row 203) is unusual and worth a panel author's attention: it names **no stored relation** — its SELECT lives in Python at `_role_census_sql()` (`:931-1012`) over `ledger` + `review_detail`, wrapped as a subquery by the one seam at `:1015-1023`. Its capability gate is therefore special-cased onto `work_item_current` (`view:work_role_census:s22_work`). It yields per-slug `opener, opened_id/ts, claimants[] (with `is_reclaim_by_distinct_actor`), claimant_of_record, closer, closed_id/ts, reviewers[] (with kernel-computed `discharge_grade`)`.

**Refusal taxonomy — 14 typed dispositions.** The contract is *branch on `disposition`, never on status alone* (`serving/README.md:436-444`): `capability_absent` (409), `payload_too_large` (413), `infra_failure` (503), `unclassified_failure` (500), `server_saturated` (503), `deployment_saturated` (503), `unknown_deployment` (404), `unknown_view` (404), `tie_group_too_large` (409), `body_read_timeout` (408), `identity_header_invalid` (422), `anonymous_write_refused` (403), `minted_actor_conflict` (409), `sse_saturated` (503). Beneath them sit ~20 untyped `{"detail": ...}` 422s (limit bounds, cursor-shape mismatches, write-payload parse axes `encoding|value|structure|representability`), and router-level 404/405 which is untyped by construction (`serving/README.md:212-221`).

**Capability manifest**, WITNESSED live and identical on both worlds:

```json
{"world":"autoharn3","service_principal":null,
 "capabilities":{"s22_work":true,"s41_identity":true,"s43_boundary":true,"credited_view":true,
                 "s45_standing_lifecycle":true,"s58_missives":true,"s60_entitlement":true,
                 "s61_signatures":true,"s64_delegation":true},
 "protocol_version":"1","authn_mode":"single-operator","identity_enforcement":"grace"}
```

Detection is object-existence, never a version literal (`:2032-2070`). Nine flags; note they stop at s64 — s65–s69 are internal refusal-journaling and role-coherence hardening with no externally actionable flag (`serving/boundary_models.py:77-83`).

**`/attestation`**, WITNESSED live: three independent sub-objects, each either a `Banked*` shape or the typed-absence `NoBankedArtifact`. Today `judge` is banked (`{"banked":true,"label":"last_known_attestation","domain":"ledger","target":"autoharn3","verdict":"AGREE","asp_input_hash":"a07dbbc5…","sql_input_hash":"1a6a2ab1…","computed_at":"2026-07-28T00:56:01","banked_at":"2026-07-27T22:56:01Z"}`), while `verify_chain` and `doctor` always resolve to absence because neither template writes its result to disk. The route **never runs the instruments server-side**.

**Pagination:** two shapes only — id-keyset (stable under concurrent insert) and slug-keyset (no duplication, but a row inserted behind an in-flight cursor joins the next walk — disclosed, `:262-273`). `1 <= limit <= 1000` everywhere. Non-unique-key views use an atomic tie-group keyset with a per-row `_page_tie` the client resupplies. **No server-side filter/sort/facet grammar in v1** (`design/FABLE-BOUNDARY-READ-SURFACE-SPEC.md:46-48`; client half at `serving/boundary_cli_client.py:366-374`). Unbound query parameters are silently dropped by FastAPI routing — named as a hazard, not fixed (`:604-610`).

**Two trust roots** — DOC-SOURCED verbatim, `serving/README.md:62-102`, maintainer-ratified 2026-07-28:

> The one-sanctioned-interface ruling governs CLIENTS: any program — a panel, a courier counterpart, `led`, a future GUI — that reads or writes the ledger goes through this service, because refusal enforcement must have exactly one home. It was never meant to route the system's OWN second opinions about itself through the thing they check.
> … **Independent instruments** (direct psql or no DB at all, DELIBERATELY outside this service): `verify-chain` … `judge` … `audit` … `doctor` — must be able to diagnose "the boundary is down" from outside the boundary; `migrate` …
> What a panel needs from the second group is not the instruments but their RESULTS: work item `boundary-verdict-read-surface` (row 221) serves the latest banked verdicts … labeled as this service's own last-known attestation with freshness visible — never a substitute for running the independent instrument, and never conflated with it.

**This paragraph is the panel's charter for §2.** It also disposes of the obvious "just add a Run Judge button" idea in advance: moving a group-two verb into the boundary is a maintainer decision against the trust-root argument, not a consistency cleanup.

### 1.4 Artifact classes a user reads

| Class | Where it lives | Shape |
|---|---|---|
| **Ledger row** | `/rows/*`, `led show` | **102 columns** (WITNESSED by counting a live row). `actor` is an **integer principal id**, not a name |
| **Derived view row** | `/views/{view}` | 31 registries, shapes per view |
| **Missive** | `/views/missive_*`, `led missive list` | ten `missive_*` columns; author/addressee world, thread, seq, act, provenance, cites, disposition |
| **Derivation record** | `engine/docs/ledger-marriage/derivations/<domain>/<target>/<ts>_<hash>/derivation.json` | `{target, verdict, only_asp[], only_sql[], asp_record{engine,version,config,input_basis,input_hash,program_hash,output_hash,ts}, sql_record{...}, asp_quarantine, sql_quarantine}` (WITNESSED) |
| **Doc attestation** | `attestations/doc-legibility-attestations.jsonl` | `attest-doc record` schema; classification `ATTESTED/STALE/NO-ATTESTATION` |
| **Tag attestation** | `attest-tags --json` | per-tag GOOD/BAD + uncovered RATIFIED commits |
| **Signed commission** | `.claude/commission-<id>.asc` + `verify-commission` | detached GPG sig over the row's *current* bytes, checked against the deployment's own `keys/` |
| **Inspection copy** | `asof-export export --out <dir>` | `ledger-asof.txt` + `.json` + `manifest.sha256`; **unsigned by design**, and the verb says so out loud rather than offering an inert `--sign` |
| **Refusal message** | `write_refused` rows, CLI teach-text, boundary dispositions | s43 journal; s65 records the attempted kind; s66/s67 journal totality + digest binding; s68 typed-absence dispositions |
| **Signed head** | `verify-chain --head` | `{world, max_id, head_hash, utc, apparatus_hash}` — refuses unless chain and both witnesses are clean |

---

## §2 The GxP access map

Framing per the commission: 21 CFR Part 11 / EU Annex 11 are **reference frames**, not adopted requirements; the ratified bar is *"NRC-grade product, best-effort process"*. Nothing below is a compliance claim.

### 2.1 ALCOA+ leg by leg

| Leg | Served by | Reachable how today | What CLI-only costs a non-expert |
|---|---|---|---|
| **Attributable** | s40/s41 principals, `LED_ACTOR`, vendor stamps, minted principals, `work_role_census`, `principal_*` views | `/standing/principals`, `/views/principal_*`, `/views/work_role_census` | Rows expose `actor` as a bare integer; the id→name join is manual. And see **H4**: enforcement is `grace`, so an anonymous write is accepted |
| **Legible** | `led show` (`{k:28s}: {v}` per non-null column), teach-text refusals | CLI only | 102 columns as a flat key:value dump. There is no rendering that distinguishes the ~8 columns that matter for a given `kind` from the ~94 nulls |
| **Contemporaneous** | row `ts` (system insert, never writer-supplied), `event_declared_ts` (s24, declared), `./autoharn audit` | `audit` is a **direct-psql instrument**, not served | The one verdict that answers "was this recorded when it happened" is not on the boundary at all, and is not banked to disk, so `/attestation` reports it absent by construction |
| **Original** | append-only ledger; supersession never edits (`--supersedes`); `/rows/{id}/history` walks the chain both ways | served, complete | The strongest leg. `/rows/{id}/history` is the single best panel primitive in the whole surface |
| **Accurate** | ASP/SQL differential (`judge`), row-hash chain (`verify-chain`), refusal-completeness oracle | **both are group-two instruments** | Their *results* are reachable only insofar as they are banked; today only `judge` banks |
| **Complete** | `refusal_seq` oracle (s43), `chain_high_water` tail witness (s27), s66/s67 journal totality | `verify-chain` (direct) | WITNESSED clean today: 409 rows walked, 15 journaled refusals == sequence count 15 |
| **Consistent** | `ledger_current` in-force semantics; `credited_current` (s46); `/rows/asof/{ts}` | served | Good |
| **Enduring** | Postgres + `asof-export export` + `sha256` manifest | served + CLI | Manifest is unsigned and says so |
| **Available** | boundary GETs, `asof-export read` | served | **Currently degraded**: `/events` is hard-down (H1) |

### 2.2 Audit-trail REVIEW — the panel's actual reason to exist

A trail nobody can usably review fails its purpose. Concretely, what the CLI makes hard:

- **No server-side filter grammar.** Every filter is client-side over paginated walks. This is not theoretical: an open work item, `led-read-projection-flags`, records it in the maintainer's own terms (WITNESSED in `led work list`): *"Two independent orchestrators (the panel's wave-2 session: 25 ad-hoc `| python3 -c` filters; this session: sam…)"*. Twenty-five hand-rolled filter pipelines is the measured cost.
- **102-column rows with no kind-aware projection.** `led show` prints every non-null column in schema order. A reviewer asking "who countersigned this and on what basis" reads a wall.
- **Integer identity everywhere.** `actor`, `regards`, `supersedes`, `answers`, `antecedent`, `work_violation_target_id` are ids. Following a review chain by hand is `led show` recursion.
- **Obligation/discharge is spread across five surfaces** — `countersign_obligation`, `review_gap`, `work_review_gap`, `discharging_attest`, `countersigned_in_force`, `reservations_outstanding` — with no single "what is outstanding against whom" view.
- **`review_gap` is actor-keyed; `work review-gap` is item-keyed.** Two different questions with confusingly adjacent names.

**Read paths a panel should expose first**, in the order a reviewer actually asks:
1. `/rows/{id}` + `/rows/{id}/history` — the record and its supersession chain, with `actor` resolved to a name. (This is the atom; everything else is an index into it.)
2. `/views/work_role_census` — who opened, claimed, closed, reviewed, and whether a claim was a handoff. This is the segregation-of-duties view.
3. `/views/review_gap` ∪ `/views/work_review_gap` ∪ `/views/reservations_outstanding` — the outstanding-obligation surface, presented as one queue with its three provenances labelled.
4. `/views/countersigned_in_force` + `/views/discharging_attest` — what is discharged and by what.
5. `/rows/asof/{ts}` — time travel, as a **modality** over the whole app rather than one tab (`second_observations` item 5).
6. `/attestation` — the last-known verdicts of the independent instruments, **labelled as last-known with freshness visible** (`serving/README.md:95-102`), never as "the system is verified".
7. `/health` + `/meta` — capability and posture, including `identity_enforcement`, which today nothing renders as a *consequence*.

### 2.3 Write paths — the one rule

Every write must go through autoharn's own refusal-enforcing surface, never around it. That is already how the panel does it (`POST /write/review`, `POST /write/missive_dispose`), and the kernel `write_verdict` is passed back byte-verbatim so a refusal renders as information, not as an error. Two design constraints follow from the corpus and should not be relaxed:

- A refusal is a **first-class domain result**. The panel already branches on `result.disposition === 'accepted'` rather than on HTTP status (`frontend/src/core/services/boundary-client.ts:123-140`) — correct, and the pattern to keep.
- **Probing a refusal writes a permanent ledger row** (the s43 journal). A panel must never offer a "try it and see" affordance, and must never retry a refused write automatically.

### 2.4 Electronic signatures, and where the panel cannot follow

The s61 machinery — `led principal attest-possession` (canonical statement `autoharn key-binding proof-of-possession: fingerprint=<FP>`, single-signer required, verified against the deployment's own committed `keys/`), then `bind-key --possession-ref <row>` — is **CLI + local GPG only**. It cannot be moved to the boundary without moving private-key operations to a service, which is exactly what proof-of-possession exists to avoid. The same is true of `verify-commission`. Correct as designed; a panel's honest role is to **display** signature state (`signed_commissions`, `commission_signature_verified`, `principal_key_possession_verified`, `signature_grade`, `signature_symmetry_witness`) and to *refuse to imply* it can produce one.

### 2.5 ADR-0019 binds any panel built here

`law/adr/0019-appendix-ui-proscriptions.md` is 29 rules, and its Synopsis is **required reading for UI implementers** (`:14-18`). The ones this domain will trip on, named because they are load-bearing here specifically:

- **C6** — loading / error / empty / genuine-zero / no-data must never collapse. A capability-gated view returning `capability_absent` is *not* "zero rows".
- **C7** — an aging datum needs a non-optional `asOf` and a visibly distinct stale state. **H1 makes this acute**: with SSE down, everything the panel shows is poll-aged and the staleness must be legible.
- **C2** — no editable control on a derived value. Nearly everything the boundary serves is derived; only the six write surfaces carry source fields.
- **C5** — success only from a durable ack. The kernel `write_verdict` *is* the ack; nothing may render "co-signed" before `disposition === 'accepted'`.
- **C8** — errors located, remediable, no dead end. The boundary's teach-texts already carry remediation; the panel must surface them, not replace them with a banner.
- **C28** — alarms severity-prioritized and flood-capped. A governance-debt dashboard is an alarm surface.
- **C13/C12** — typed semantic elements, bounded measure. Statements and refusal texts are load-bearing and must never be ellipsised (the maintainer's own PoC verdict, restated at `tools/autoharn-panel/SPEC.md:24-27`).

---

## §3 What's already there

### 3.1 There are TWO panel codebases, and only one is live

- **`tools/autoharn-panel/`** — a git submodule of `github.com/KodBena/autoharn-panel`, pinned at `6bd657b` (WITNESSED via `git submodule status` and `.gitmodules`). This is the older Flask backend + SPA: `backend/config.py`, `LED_BIN` conduit writes, `PANEL_BIND`/`PANEL_PORT` default 8420, `PANEL_EXTENSIONS`, direct-psql `LEDGER_PG_URI`. It carries `SPEC.md` (Fable-authored 2026-07-15) and a `README.md`. Autoharn's own world has it **off**: `features.json` → `"panel_extension": false` (WITNESSED).
- **`/home/bork/w/vdc/2/autoharn-panel/`** — remote `github.com/KodBena/**autoharn-gui**.git` (WITNESSED via `git remote -v`). This is the live project, world `experience4`. Different repo, different name, boundary-only architecture.

The directory name collision is a trap for a reader: the path says `autoharn-panel`, the remote says `autoharn-gui`. Worth naming before anyone wires the wrong one.

### 3.2 The live panel (autoharn-gui) — current state

**Stack:** Vue 3.5 + Vite 8 + TypeScript, `vue-router`, `@tanstack/vue-virtual`, `echarts`, Vitest + Playwright. Build runs `lint:boundaries && vue-tsc -b && vite build` — `frontend/scripts/lint-boundaries.mjs` is the only *mechanically enforced* architecture spec (4 rules, including RULE 4 which bans reintroducing the deleted backend's ports/routes).

**26 registered tabs** in the single registry `frontend/src/tabs.ts:60-87`. By coverage:

- **Fully implemented (23):** ledger, commissions, work-items, obligation-tree (ECharts DAG), discharge-records (4 parallel reads, 496 lines — the largest component), review-gap, questions, work-violations, findings-snags, standing-decisions, countersign-obligation, review-stamp-distinctness, work-review-gap, model-attestations, model-defeated-rows, credited-current, capabilities (renders **all 9** manifest flags, verified 1:1 against `serving/boundary_models.py:72-87`), artifacts (hash lookup + raw download), principals (4 s41 views, each independently best-effort), work-role-census (slug-keyset walk), mail (6 missive views + the dispose write), glossary, reservations-outstanding.
- **Re-scoped (1):** `profiles` — now a world `<select>`, not the `panel.toml` profile editor its name implies (44 lines).
- **Partial (2):** `asof-inspection` — the read works; the maintainer's two asks (time-travel-as-modality, CSV/JSON export) are not built. `setup-configuration` — five sections, zero boundary calls by design, exports via clipboard/Blob; but `setupPlan.ts:276-277` emits literal `<fill in at scaffold time: …>` placeholders into the exported `.autoharn-world.json`, so the export is not directly usable, and `second_observations` item 1 ("does not come close to the autoharn setup TUI") is only partly answered.

**One `PendingUpstream` stub remains** — `ItemObligationsPanel.vue:144-146`: *"No boundary route serves this row's witness-edge resolution or resource-field parsing yet."* Every other historical stub has been un-stubbed.

**Write paths — exactly two,** both through the boundary, both behind a safe-mode gate that is honestly labelled a UX gate and not a security boundary (`core/state/safe-mode.ts:13-20`): `POST /write/review` (co-sign) and `POST /write/missive_dispose`. Nothing else writes.

**Data layer:** hand-typed `fetch` in `core/services/boundary-client.ts` (141 lines); the generated `openapi-fetch` client was abandoned because its schema targeted the deleted Python backend — leaving `openapi-fetch` and `openapi-typescript` as **two dependencies with zero importers**. Same-origin relative base by default because the boundary sends no CORS headers. Three pagination shapes handled correctly, including per-view cursor dispatch (the boundary 422s on the wrong cursor param). Refusal handling is split deliberately: kernel verdicts by `disposition`, transport/absence by status, with `404`/`409` treated as honest "not available on this deployment".

### 3.3 Drift, named

| Drift | Witness |
|---|---|
| **`SPEC.md` does not exist** — yet is cited **119 times across 45 files**, including `README.md:15`, `router.ts:1`, `App.vue:19`, `lint-boundaries.mjs:19`, and dozens of component headers ("SPEC.md sec 4"). The largest documentation defect in the repo | file absent; citations live |
| **A frozen letter is doing load-bearing spec work.** `DIRECTIVE_FROM_AUTOHARN.md` carries `> **FROZEN 2026-07-28**` yet its §5 is cited by name in `boundary-client.ts:2-4`, `cosign.ts:11`, `PendingUpstream.vue:32`, `README.md:5` | banner at `:1-5`, citations live |
| **UI copy points into a retired channel.** `ReviewGapTab.vue:52` and `PendingUpstream.vue:34` tell the operator to consult `AUTOHARN_BACKFLOW.md` — frozen history. 26 live source-comment citations to the two frozen files remain | file:line above |
| **UI copy uses pre-umbrella spellings.** `StandingDecisionsTab.vue:10-11,40` renders "`./led standing` and `./pickup`" — the correct spelling is `./autoharn led standing` / `./autoharn pickup` | `/home/bork/w/vdc/2/autoharn-panel/autoharn:28-29` |
| **`README.md` §1 documents a backend deleted seven days ago** — ~75 lines on `backend/config.py`, `PANEL_PROFILE`, port 8420, `LED_BIN`, `/api/health`. §2 is marked historical; §1 is not. `core/services/types.ts:147-183` still declares `BackendSurfaceRelation` for the removed `GET /api/backend-surface` | file:line above |
| **Six in-source comments actively contradict the code.** `vite.config.ts:27-29` says "no client-side SSE/live-update code exists anymore" (`useLiveUpdates.ts` is 288 lines and SSE-primary); `App.vue:102-105` says "no SSE exists on the boundary" (it does, `boundary_service.py:3731`); `safe-mode.ts:6-7` says "exactly ONE write path" (there are two); `DischargeRecordsTab.vue:29` says `GenericViewTab.vue` doesn't exist (it does, 215 lines); `DataRow.vue:11` references a deleted component; `tabs.ts:52-54`/`App.vue:59-61` narrate "7 gated tabs / never all 9" when 20 of 26 are gated | file:line above |
| **`extensions_enabled` is hardcoded** to `['autoharn']` at `core/state/health.ts:24`, and that single literal gates 20 of 26 tabs. The "is this extension enabled?" question is never actually asked of the deployment | file:line above |
| **`panel.toml` names world `autoharn1`** — a schema not served by the hub. Harmless (nothing reads it) but stale | `panel.toml`, vs `boundary-multiplex.toml` |
| **`MAKESPAN_SCHEDULER_BACKFLOW.md` is dead** — 25 lines whose "Open entries" section reads *"(none yet — this file is a stub)"*, tracking an `off` feature in a dust-world path | `:23-25`, `features.json:3` |
| **Dispatcher is CURRENT, not stale** — panel roster (11 verbs) matches upstream `bootstrap/templates/*.tmpl` minus `NON_VERB_TEMPLATES` exactly, regenerated after the courier gap fix (autoharn3 row 101) | rosters compared, WITNESSED |

**Lineage drift is semantic and invisible.** `experience4` stops at s68; `autoharn3` has s69. s69 adds no view, no column, no kind — only new refusal branches on re-issued triggers — so nothing in `VIEW_REGISTRY` or the capability manifest changes, and the panel's world selector gives an operator **no signal that the two worlds enforce different rules**. `/meta.lineage_head` is the field that would show it, and it is broken (H2).

---

## §4 Gap table

### A. Surface that exists but is panel-inaccessible

| # | Gap | Witness | Shape hint (one line) |
|---|---|---|---|
| A1 | **`GET /kinds` unconsumed.** The panel ships a *static* `core/vocabulary.ts` (145 lines) + `glossaryTerms.ts` (179 lines); a kind added upstream is invisible until someone hand-edits them. This is exactly the "derive, don't duplicate" defect the PoC's critique loop spent two rounds killing (`tools/autoharn-panel/SPEC.md:26-28`) | zero hits for `/kinds` in `frontend/src/` | fetch at boot, fall back to the static list |
| A2 | **`GET /attestation` unconsumed.** The one route that carries the independent instruments' verdicts — the whole point of `boundary-verdict-read-surface` (row 221) — is never called | zero hits | a header strip: chain / judge / doctor, each with freshness or typed absence |
| A3 | **`/views/work_startable` unconsumed.** No "what can I pick up next?" surface, despite work-items and obligation-tree both existing | zero hits | column on the work-items tab |
| A4 | **`/views/work_violation_history` unconsumed.** Only current violations are shown; no resolved/historical view | zero hits | history drawer on a violation row |
| A5 | **`after_tie` never sent.** Seven non-unique-key views emit a `_page_tie` the panel never reads or resupplies. Masked today by one-shot large-`limit` fetches; a walk past a page boundary on a repeated key is unprotected | `VIEW_REGISTRY` at `boundary_service.py:853-912` vs no `after_tie` in `frontend/src/` | thread `_page_tie` through the pager |
| A6 | **4 of 8 `/meta` fields unread** (`max_tie_group_extra_rows`, `max_sse_clients`, `sse_poll_interval_secs`, `authn_mode`) — and `useLiveUpdates.ts:21-25` *narrates* using two of them without ever fetching `/meta` | `types.ts:127-140` | — |
| A7 | **`identity_enforcement` read but never acted on.** The co-sign button's enabled state depends only on safe mode, never on the deployment's posture (H4) | `types.ts:122`, `CosignPanel.vue:124` | gate the write affordance on posture, not just safe mode |
| A8 | **The setup TUI has no panel analogue.** `python3 -m tools.setup_tui` is 38 modules; the Setup tab is 5 sections that emit placeholder-bearing exports | `second_observations` item 1 | — |
| A9 | **The independent instruments are unreachable by design** (`judge`, `verify-chain`, `doctor`, `audit`, `migrate`). Correct per the two-trust-roots doctrine — listed so it is a **stated** gap, not an oversight | `serving/README.md:62-102` | expose banked results only, labelled `last_known_attestation` |

### B. Surface the panel assumes but autoharn does not provide

| # | Gap | Witness |
|---|---|---|
| B1 | **No missive-send surface at all.** `led missive` has only `list` and `dispose`; `missive_sent` appears **nowhere in `user-guide/`**; sending requires hand-authoring a ten-key `missive_*` envelope through `led --json ledger`. Tracked as open work item `led-missive-send` (WITNESSED). `second_observations` item 6 ("no way to create/submit missives") is the panel-side face of the same gap |
| B2 | **No deployment-listing route.** `KNOWN_DEPLOYMENTS` is hand-maintained in `deployment.ts:34-39` and explicitly disowns `boundary-multiplex.toml` as ground truth |
| B3 | **No artifact-listing route.** Hash-only lookup is all the boundary offers, so the Artifacts tab can only be a lookup box (merged under a `refuse` verdict, row 678) |
| B4 | **No `trust_level` on rows.** `CommissionTab.vue:20-26` has a `v-if="detail.trust_level"` that can never render |
| B5 | **No witness-edge / resource-field resolution route** — the last `PendingUpstream` stub |
| B6 | **No server-side filter/sort/facet grammar.** Every projection is a client-side walk (open item `led-read-projection-flags`) |
| B7 | **`--json` cannot reach `obligation_revoke` or `missive_dispose`**, though both are write surfaces |

### C. Expectations no surface serves yet

| # | Gap | Witness |
|---|---|---|
| C1 | **Trustworthy kernel-generation reporting.** `/meta.lineage_head` is wrong for every deployment (H2); nothing else answers "which lineage is this world at" over HTTP. Consequence: no cross-world rule-difference warning |
| C2 | **A working live-signal channel.** `/events` is hard-down and self-refilling (H1) |
| C3 | **Enforced attributability.** `identity_enforcement=grace` on both worlds; the panel sends no identity headers; anonymous authority-bearing writes succeed (H4). This is the ALCOA leg most load-bearing under a GxP frame and the one presently unenforced end-to-end |
| C4 | **Contemporaneity as a served fact.** `audit`'s verdict is neither served nor banked; `/attestation` cannot report it because the template writes nothing to disk |
| C5 | **A signed inspection copy.** `asof-export`'s manifest is an unsigned content hash and says so — honest, but it proves neither who exported nor that a regenerated copy wasn't substituted |
| C6 | **`verify-commission` / `attest-doc` from the root operator surface** (H3) |
| C7 | **A unified obligation/discharge queue.** Five surfaces, no single "outstanding against whom" view |
| C8 | **Principal-id → name resolution as a served join.** Every consumer does it client-side; `ReviewGapTab.vue:52` discloses the gap in its own UI copy |
| C9 | **`work_role_census` reviewer resolution is one hop only** — a review regarding a *superseded* close still surfaces. Correct for post-hoc RCA, wrong for "who owns this now"; the caller must filter for currency itself (`boundary_service.py:952-959`) |
| C10 | **Per-deployment SSE fairness.** The 16-client bound is hub-wide; one world's viewers can starve another's |
| C11 | **Unbound query parameters are silently dropped service-wide** — a mistyped filter returns a plausible full page rather than a refusal (`boundary_service.py:604-610`, named as a hazard, not fixed) |

---

## §5 Closure statement

**What I enumerated.** (a) Every verb on autoharn's own operator surface — the thirteen-plus-`service` roster and the eleven-verb world roster, each with its `--help` captured; (b) the full `led` subcommand tree: 33 write kinds, 12 shared flags, 8 statement grammars, 9 top-level reads, 11 `work` sub-verbs, 14 `principal` sub-verbs, `missive`/`artifact`/`review`/`obligate`/`register-principal`/`--json`, and the 5-value exit-code convention; (c) all 21 boundary routes, the 31-member `VIEW_REGISTRY`, the 7 write surfaces, the 14-disposition refusal taxonomy, the 9-flag capability manifest, the SSE contract and the `/attestation` shape; (d) every artifact class an operator reads, with its on-disk or on-wire shape; (e) the operator surfaces outside the umbrella (setup TUI, orchlog, otel-*, extract-context, hooks); (f) the panel's 26 tabs, 12 consumed routes, 21 consumed views, 2 write paths, and its drift from autoharn HEAD.

**How I know the enumeration is complete.** Three independent cross-checks, each of which would have caught an omission in the others:

1. **Roster ↔ implementation.** `./autoharn --help` is generated from the dispatch table at `autoharn:42-58`; `ls libexec/autoharn/` returns exactly those 13 names (the `seen-red/umbrella-cli-dispatch-parity` fixture greps this same pair). The world roster is glob-derived from `bootstrap/templates/*.tmpl` minus the enumerated `NON_VERB_TEMPLATES` (`new-project.sh:186`) — I ran that set difference by hand and got the 11 in the panel's dispatcher. The **delta between the two rosters is H3**, found by this cross-check and by nothing else.
2. **Code ↔ live service.** `VIEW_REGISTRY` as declared at `boundary_service.py:853-912` was checked against `GET /meta.known_views` (31, matching), and the capability manifest as declared at `boundary_models.py:72-87` against live `GET /health` (9, matching). `GET /kinds` returned 33, matching `s61-signature-symmetry-and-key-binding.sql:180`. **H2 was found by this cross-check** — `/meta.lineage_head` was the one field that did *not* match the code's evident intent, which sent me to `migrate_core._manifest()`.
3. **Docs ↔ both.** `user-guide/` (28 files) and `user-guide/recipes/` (8 files) were outlined section by section and their claimed verbs reconciled against the rosters. **B1 was found here**: `missive_sent` appears in zero user-guide files, which is what made me check for a `send` verb and find none.

**Live GET witnesses taken:** `/health` (both worlds), `/meta`, `/kinds`, `/attestation`, `/rows/current?limit=1` (102 columns counted), `/views/work_role_census?limit=1`, `/events` (three attempts, both worlds). **Read-only commands run:** `./autoharn --help`, 14 verb `--help`s, `doctor`, `distance-to-clean`, `verify-chain`, `led work list`, `led --recent`. **No refusal was probed; no ledger row was written by this survey.**

**What remains open (UNVERIFIED, with blockers).**

- **The SSE leak's exact trigger.** The acquire-outside-try in `_stream()` is decidable from source and is sufficient to explain it, but I did not reproduce the leak — doing so means opening and abandoning SSE connections against the live hub, which exceeds "plain GETs". Blocker: read-only mandate. The witnessed *state* (16 slots, 3 sockets) is not in doubt.
- **`./autoharn migrate`'s actual behaviour under the one-entry manifest.** Read from source only; `migrate` writes. Blocker: read-only mandate.
- **Whether `experience4`'s kernel truly stops at s68.** Taken from the commission's ground-truth statement plus the fact that s69 adds no capability flag. `/meta.lineage_head` cannot confirm it (H2), and I did not query the schema directly. Blocker: H2 plus read-only.
- **The panel's runtime behaviour.** Everything in §3 is read from source and git history; I did not run the SPA. Blocker: read-only, and the maintainer's own responsive audits already cover rendered behaviour.
- **Two stray `boundary_service` processes** were observed alongside the sanctioned hub (port 8420 from a `/tmp` deploy fixture, port 8421 from a scratch run under this session's scratchpad). Noted as an observation only — neither is the autoharn3/experience4 hub, and disposing of them is a state change I did not take. It sits adjacent to the maintainer's own "there needs to be only one running at any one time" ruling recorded in `boundary-multiplex.toml`.
- **Which of the three prior surveys already found H1–H4** is unknown to me by construction. The independence clause was honoured; de-duplication against them is the coordinator's step, not mine.
