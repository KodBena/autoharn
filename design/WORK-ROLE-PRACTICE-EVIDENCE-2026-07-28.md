<!-- doc-attest-exempt: as-delivered evidence record, filed verbatim 2026-07-28
(commission row 168 part c, brief BRIEF-WORK-ROLE-EVIDENCE.md; read-only Sonnet survey,
evidence only, no recommendations by its own mandate). This file is the evidence base
the work-role doctrine treatment (work item work-role-doctrine-faq, row 170) cites.
Removal condition: superseded by a later census. -->

**Provenance:** produced by the commissioned read-only evidence surveyor (Sonnet,
2026-07-28) across the autoharn2 (dust, read-only), autoharn3, and experience4 ledgers.
Filed verbatim by the coordinator.

---

# Evidence Report: Work-Item Role Assignment as Practiced (autoharn2 / autoharn3 / experience4)

Scope note: read-only throughout. All psql via `env -u PGOPTIONS psql -h 192.168.122.1 -U bork -d toy`. No ledger/DB writes. No file writes performed. This is evidence only — no doctrine or recommendation is offered.

## 1. The lifecycle census

Query pattern (WITNESSED): for each world, joined `work_opened` / latest `work_claimed` / latest `work_closed` per `work_slug`, resolved `actor` via `<world>_kernel.principal`.

**Headline finding, all three worlds, no exceptions: every work-item lifecycle act (open, claim, close) is performed by the single principal named `author`, in the single session named `main`.**

| World | items opened | opener==claimer==closer (of the closed subset) | distinct actors ever used for open/claim/close |
|---|---|---|---|
| autoharn2 | 102 | 61/61 (100%) | `author` only |
| autoharn3 | 53 | 5/5 (100%) | `author` only |
| experience4 | 47 | 29/29 (100%) | `author` only |

WITNESSED — full actor distribution per world (query: `select p.name, count(*) from <w>.ledger l join <w>_kernel.principal p on p.id=l.actor group by 1`):
- autoharn2: `author` 1567, `write-boundary` 7 (the latter only on `write_refused` rows, never on work-lifecycle kinds)
- autoharn3: `author` 147, `write-boundary` 11, `courier` 7
- experience4: `author` 262, `write-boundary` 89, `reviewer` 31, `commissioner` 7, `courier` 5

WITNESSED — session distribution: **all rows in all three worlds carry `session='main'`** (`select session, count(*) from <w>.ledger group by 1` returns exactly one row, `main`, in every schema). There is no second session anywhere in these three worlds' ledgers, so "same-session open-and-close" is true by construction, not by any deliberate act — there is no other session to differ from.

Consequence: the four "does X==Y" questions in the brief (opener==claimer, claimer==closer, opener==closer, same-session open-close) are **all true, 100%, in every world, with zero counterexamples on the work-lifecycle acts themselves.** Role separation in these three worlds does not show up on work_opened/claimed/closed at all — it shows up only on the *review* surface (see §2), where a second principal (`reviewer`) and, in experience4, further principals (`commissioner`, `courier`) appear.

Counts of never-claimed opens (all closed items in all three worlds were claimed first — see §4 for why that's a CLI-level fact, not a kernel-level one):

| World | opened, never claimed | closed, never claimed |
|---|---|---|
| autoharn2 | 41 of 102 | 0 |
| autoharn3 | 45 of 53 | 0 |
| experience4 | 18 of 47 | 0 |

## 2. Review interaction

**autoharn2 and autoharn3 have zero `kind='review'` rows** (WITNESSED: `select kind,count(*) from <w>.ledger group by kind` lists no `review` row for either world), and **`review_detail` is empty (0 rows) in autoharn2** (checked directly). Review evidence in those two worlds lives entirely in `work_closed.work_review_disposition` (`witnessed`/`deferred`/`bookkeeping`) plus a `work_review_ref` pointing at either a `finding`-kind ledger row or a `commit:<sha>`. In every one of these cases the referenced `finding` row's `actor` is also `author` — i.e., in autoharn2/autoharn3 the "witness" is a same-principal, same-session note the closer wrote about their own work, not a second party's countersignature. Disposition counts, autoharn2 (61 closes): witnessed 32, deferred 18, bookkeeping 11 — **zero self-review flags exist because the mechanism that records independence (`review_detail`) was never populated in this world**, a GAP between the schema (which supports `independence`/`discharge_grade`) and this world's actual practice.

**experience4 is the rich specimen for this question.** It has 31 `kind='review'` rows, all authored by principal `reviewer` (actor id 2, distinct from `author`, id 1), joined against `review_detail`:

- **Every one of the 31 rows carries `independence='self-review'`** (WITNESSED, full table pulled). Not one row in experience4 uses `technical`, `managerial`, `financial`, or `disclosed-isolated-dispatch` — despite those being legal, closed-vocabulary values (`review_detail_independence_check`).
- `discharge_grade` (kernel-computed, not writer-asserted — see §4) splits `same-principal` (18), `same-session` (12), `distinct-session` (2, both regarding row 256). Because `session` is uniformly `main` across the whole world, "distinct-session" here must be riding on `stamp_agent`/`stamp_session` (finer-grained sub-session identity), not the coarse `session` column — worth flagging as a distinct axis from the one used in §1's census.
- Verdicts: `attest` 15, `attest_with_reservations` 15, `refuse` 1 (row 419).

**The one fix-gate case (row 419, verdict `refuse`), traced in full:**
- Row 413 `work_closed` (`panel-board-view`, resolution `shipped`, disposition `deferred`, actor=`author`).
- Row 419 `review` (actor=`reviewer`, regards=413, independence=`self-review`, verdict=`refuse`): statement reads *"Adversarial review of 3b9f3cc (panel-board-view), self-review disclosed (no independent second reviewer genuinely available this session). REFUSE…"*
- Row 421 `decision` (actor=`author`): *"Out-of-frame review row:419 REFUSED panel-board-view … the show-superseded toggle is dead code…"* — fix work is dispatched by the same `author` actor.
- Row 427 `work_closed` (actor=`author`, `supersedes=413`, resolution `shipped`, disposition still `deferred`) — the re-close after the fix.
- Row 431 `review` (actor=`reviewer`, verdict `attest`) **mis-cites `regards=413`** (the now-superseded close) instead of 427.
- Row 435 `review` (actor=`reviewer`): *"Correcting a citation error: this attest properly regards row:427 (the actual current close…)"* — a self-caught correction, re-filed with the right `regards`.
- Row 436 `decision` (actor=`author`): *"Process defect, caught by the stop-gate itself: when dispatching a re-review after a superseding close, I twice … cited the superseded row instead of its successor."*

So: the same operator identity (session `main`, whether wearing the `author` or `reviewer` principal hat) opened, claimed, closed, fixed, superseded, reviewed, mis-cited, and self-corrected the same item end to end. Nothing here is enforced against; it is all disclosed in the prose, and the mis-citation was self-caught rather than kernel-caught.

**A genuine, kernel-enforced refusal exists for independence claims that outrun the identity evidence** (experience4 row 339, `write_refused`, `refusal_surface='review'`): *"this review claims independence (technical) but the SAME invocation (session=…, agent=main) wrote both it and the row it regards … Record independence='self-review' … or have a genuinely distinct invocation … write the review."* — see §4 for the mechanism.

## 3. Haphazard specimens (no editorializing, shapes only)

1. **Witness-ref existence check does not check witness-ref shape** (autoharn2, close row 1265, slug `experience-secret-gitignore-hazard`): `work_review_ref='row:1232'`, and row 1232 is `kind='work_claimed'` for the same slug — not a review, finding, or any evidentiary row. Cross-checked: this is the *only* such mismatch across all `row:` witness references in all three worlds (7 other autoharn2 refs point to `finding` rows; all 4 experience4 refs point to `review` rows; autoharn3 has zero `row:`-style refs). Root cause traced to §4: the enforcing trigger (`validate_review_witness_existence`, s48) checks only that the cited id **exists**, never that it is review-shaped.
2. **Same-actor, cross-hat review with a mis-cited antecedent, self-corrected** — the `panel-board-view` sequence in §2 (rows 413/419/421/427/431/435/436). The correction was authored by the same identity that made the error, in the same session, with no independent party catching it — the "catch" is a decision-row narrative (row 436), not a distinct reviewer.
3. **All independence claims in the one world that uses the vocabulary are `self-review`** — 31/31 in experience4, 0/0 elsewhere (the field is simply unpopulated in autoharn2/autoharn3). No specimen anywhere in the three worlds of `technical`/`managerial`/`financial`/`disclosed-isolated-dispatch` independence being successfully recorded (one *attempt* at `technical` was refused — row 339, §2/§4).
4. **`review_detail` is a schema mechanism with essentially no adoption in two of three worlds.** autoharn2: 0 rows against 61 closes, 32 of them flagged `witnessed`. autoharn3: 0 `kind='review'` rows at all — its five closes are all `bookkeeping` disposition (commit-ref only, no reviewer-of-record).
5. **A named work item exists in autoharn3 for exactly this question and is itself unclaimed/unclosed**: slug `work-role-doctrine-faq` (opened by `author`, session `main`; no claim, no close as of the query time) — i.e., the ledger already contains an open item asking the question this brief was commissioned to gather evidence for.

## 4. What the mechanism actually constrains vs. pure convention

Enforcement traced by reading `pg_get_functiondef` for the live trigger functions in `toy.autoharn2` (representative; same trigger family exists in all three worlds) and cross-checked against `kernel/lineage/*.sql` comments, plus `bootstrap/templates/led.tmpl` for CLI-side gates.

**Kernel-enforced (DB trigger level):**
- An item must have a `work_opened` row before any `work_claimed`/`work_depends_on`/`work_closed` act — `autoharn2.validate_work_item()`, dispatches into `validate_work_item_claim`, invariant cited as "invariant 2, item identity" (s22).
- Claiming an already-closed item is refused — `validate_work_item_claim`, explicit s47 check against `ledger_current`.
- Claim-time blockers (`blocks-start` edges) must be resolved — same function, s39.
- A close past the world's migration epoch must carry a non-NULL `work_review_disposition` — `validate_work_item_close`, s29 Element B.
- A **strict** close requires `witnessed` disposition (not `deferred`/`bookkeeping`) and a resolved obligation tree via `work_item_strict_blockers` — s29 Element C, s39.
- `work_review_ref`'s `row:<id>` citations must reference an **existing** ledger row — `validate_review_witness_existence()`, s48 — but, per specimen 1 in §3, existence only; **not that the row is review-shaped**. GAP, evidenced concretely.
- A row's own author may not countersign it as a `kind='review'` row (`target_actor = NEW.actor` refusal, "segregation of duties") — `validate_review()`. This applies only where `kind='review'` rows are used at all (experience4); autoharn2/autoharn3's disposition-only review path is untouched by this check because it never inserts a `kind='review'` row.
- Independence claims of `technical`/`managerial`/`financial` require a **verified stamp** and a **distinct (stamp_session, stamp_agent) pair** between the review and the row it regards — `validate_independence()`, s21/s34/s41; `managerial`/`financial` further require the reviewing actor's `agent_class='human'` (s41 D-6). `discharge_grade` itself is kernel-computed and a writer-supplied value is refused outright (s34, "ledger finding 1157" cited in the trigger's own exception text).

**CLI-enforced, not kernel-enforced (documented explicitly in the source as such):**
- **Claim-before-close** — `bootstrap/templates/led.tmpl`, `cmd_work_close`, ~line 2312: *"claim-before-close gate (led-side; the kernel's own trigger checks only that <slug> was OPENED, not that anyone claimed it) — run-5 forensics: two work items were closed with no claim ever landing, unflagged."* The check (`_slug_claimant`) only verifies **some** claimant exists on `work_item_current` — it does **not** check that the claimant is the same actor as the one closing.

**Explicitly NOT enforced anywhere (pure convention, per the source's own comments), confirmed by the census in §1 having zero counterexamples to check against:**
- Nothing requires the closer to be the claimant, or the opener to be the claimer/closer.
- Multiple claims on one item are explicitly legal by design — `kernel/lineage/s47-claim-on-closed-refusal.sql` line 184: *"Claiming an ALREADY-CLAIMED item remains legal — multiple claimants are representable…"* — with no mechanism to prevent a second actor from claiming an item someone else already holds ("claim-stealing" is representable, not refused). `work_item_current`'s `claimant` field resolves to the **latest** claim row (`DISTINCT ON (work_slug) … ORDER BY id DESC`) — last-claim-wins is a view convention, not an identity binding.
- Nothing ties a `work_closed` row's `actor` to the item's `work_opened` or `work_claimed` actor.

**`work_item_violations` view**: checked directly in all three worlds — **0 rows in every world** (`select * from <w>.work_item_violations` returns empty everywhere queried). Its catchable classes were not exercised further because no populated instance exists to inspect in these three worlds' data (see "what I could not determine" below).

## 5. Vocabulary inventory (sourced)

| Category | Values observed / defined | Source |
|---|---|---|
| `principal.agent_class` | `human`, `model`, `subagent`, `tool` | CHECK constraint `principal_agent_class_check`, `autoharn2_kernel.principal` |
| Principal names actually seen | `author`(model), `reviewer`(subagent), `commissioner`(human), `write-boundary`(tool), `maintainer`(human), `bork`(human), `countersign-reviewer-01`(subagent), `otel-sentry`(tool), `delegate-1`/`delegate-2`(subagent) — autoharn2's registry; `courier` also seen active (autoharn3/experience4) | `select id,name,agent_class from <w>_kernel.principal` |
| `principal_actor_resolution` | `explicit`, `declared-default` | CHECK `principal_actor_resolution_check`; autoharn2: 1064 explicit / 510 declared-default |
| `principal_relation` | `acts-for`, `dispatched-by`, `same-natural-person`, `succeeds` | CHECK `principal_relation_check` |
| `principal_role_name` bindings observed | `authority` (autoharn3, experience4; 1 row each) | `select principal_role_name,count(*) from <w>.ledger where kind='principal_role_bound'` |
| `review_detail.independence` | `self-review`, `technical`, `managerial`, `financial`, `disclosed-isolated-dispatch` (only `self-review` actually recorded in the data) | CHECK `review_detail_independence_check`; experience4 data |
| `review_detail.verdict` | `attest`, `attest_with_reservations`, `refuse` | CHECK `review_detail_verdict_check` |
| `review_detail.discharge_grade` | `same-principal`, `same-session`, `distinct-session`, `distinct-deployment` (kernel-computed; `distinct-deployment` documented as "closed vocabulary but UNREACHABLE here today") | CHECK + trigger comment, `validate_independence()` |
| `work_review_disposition` | `witnessed`, `deferred`, `bookkeeping` | CHECK `work_review_disposition_check` |
| `work_resolution` (close) | `shipped`, `superseded`, `dropped`, `deferred` | CHECK `work_resolution_check` |
| stamp identity fields | `stamp_session`, `stamp_agent`, `stamp_ts`, `stamp_hmac`, `stamp_verified`, `stamp_invocation` — a second, finer identity axis beneath the ledger's own coarse `session` column, used specifically by the independence-distinctness check | `autoharn2.ledger` columns; `validate_independence()` reads `stamp_session`/`stamp_agent`, not `session` |
| `refusal_surface` | `ledger`, `review`, `registration`, `obligation`, `artifact` | CHECK `refusal_surface_check`; all five values found live except `obligation`/`artifact` not observed among the ≤107 `write_refused` rows sampled |
| `edge_type` (work_depends_on) | `blocks-close`, `blocks-start`, `informs` | CHECK `edge_type_check`; `informs` explicitly documented as "advisory only — never enforced at close or claim" |

## What I could not determine, and why

- **No populated example of `work_item_violations`** exists in any of the three worlds queried — I could describe the view's *shape* (from its column list: `violation, slug, detail, target_id`) but not confirm what it fires on in practice, since it returned 0 rows in autoharn2/autoharn3/experience4 alike. Confirming its actual trigger conditions would require reading the view's defining SQL in `kernel/lineage/s37-violation-disposition.sql` or similar (I read function/trigger bodies but did not read every view definition end-to-end for this one) — flagged rather than guessed at.
- **`review_detail`'s complete non-adoption in autoharn2/autoharn3** is reported as a fact (0 rows) but I could not determine *why* it went unused there — whether the mechanism postdates most of those worlds' actual close activity (a schema-vs-practice timing question I did not chase against migration/epoch metadata) or was simply not exercised by convention. Both are consistent with the data; I did not have grounds to pick one.
- **The `main`-only session finding across all three worlds** means the brief's "same-session open-and-close" question is vacuously true everywhere queried — I have no counter-example world available in the three schemas granted (autoharn2/autoharn3/experience4) to show what a cross-session case looks like. `autoharn2_kernel`/etc. contain no second session to compare against; I did not query other schemas in the `toy` database (many exist — `foo1`, `cyc7w7528`, etc.) since the brief scoped access to these three only, so I cannot say whether cross-session role separation exists anywhere else in the broader `toy` database.
- **The panel repo** (`/home/bork/w/vdc/2/autoharn-panel`) and the Grafana-style read endpoints (`127.0.0.1:8433/d/autoharn3/...`, `/d/experience4/...`) named in the brief's access grant were **not exercised** — the psql access alone was sufficient to answer every numbered question, and I did not find a further question that required them. Flagged as UNEXERCISED rather than claimed covered.