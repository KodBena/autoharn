# CAPABILITIES — what the harness can already do, in plain words

Audience: orchestrator (the opening paragraph below calls this same reader "a maintainer or operator" — the practical reader deciding what the apparatus can be trusted to do)

The harness is autoharn's governance apparatus: the append-only Postgres decision ledger,
the refuse-and-teach Claude Code hooks, and the operator verbs this repository builds so
that AI-collaborator work leaves an auditable trail. This document is for a maintainer or
operator deciding what the apparatus can already be trusted to do versus what is still
aspiration, and it lists what that apparatus verifiably does today.

Each item: what you get, how it is enforced, and how we know it works — **witnessed** means it
has fired for real at least once (the evidence is banked); **built, unexercised** means the
mechanism exists but has never fired in anger. Nothing here is aspiration; the aspirational
layer lives in `law/briefs/`. Source of record: `law/briefs/BRIEF-CONFORMANCE-MAP.md`.

This pass (2026-07-10) refreshes the doc past s20 (obligation grants + view refresh), s21
(pair-keyed session-aware distinctness), s22 (work-item ledger), the operator verbs' shape as
of that date (four then: `led`/`judge`/`pickup`/the scaffold; `audit` and `distance-to-clean`
joined later — item 25 below carries the current, canonical list), `bootstrap/apply-delta.sh`, the
self-documenting `--new-world` scaffold, the conformance checker instrument, the fail-closed
hook changes, and the class-ratification + self-application rules in CLAUDE.md ORCHESTRATION.
Method: re-read the source files below, then re-witnessed the operator-facing round trip on a
throwaway probe world (`bootstrap/new-project.sh /home/bork/w/vdc/1/.capsprobe --new-world
capsprobe --db toy --host 192.168.122.1`, torn down after — `DROP SCHEMA ... CASCADE` both
schemas + `DROP OWNED BY`/`DROP ROLE`, zero residue verified by an empty
`information_schema.schemata` query and directory removal). Items marked *(this pass)* carry
that probe's own captured output; older items keep their original citation and were re-verified
against the current source rather than re-run.

A FOLLOW-UP consolidation pass (same date, 2026-07-10) added the per-world `apparatus.json`
mechanism switchboard (items 18–23 below) — every hook now reads its own `mode` live — and the
new `mutation_observer` hook (item 22). Method: re-read the four just-landed/changed hooks in
full, wire the config layer, add `seen-red/mutation-observer/` + `seen-red/apparatus-config/`
(registered in `gates/fixture_census.py`), then re-witness the operator-facing round trip on a
SECOND throwaway probe world (`bootstrap/new-project.sh /home/bork/w/vdc/1/.consolprobe
--new-world consolprobe --db toy --host 192.168.122.1`): the birth `apparatus.json` carried every
default (confirmed byte-for-byte); `change_gate`'s full three-way (`off` let a previously-denied
edit through untouched, `observe` produced a warning instead of a denial, `enforce` denied) and a
`stamp_intercept` spot-check (`enforce` injected, `off` produced no output at all) were driven
against the real wired hooks in this world; the mutation observer's two legs, driven against a
real python-driven write, warned when no work item was open+claimed and fell silent once one was
— torn down after with the identical zero-residue verification. Items marked *(this pass, config
layer)* carry this second probe's own captured output.

## Witnessed

**1. Decisions that cannot be quietly rewritten.**
Every decision/assumption/finding is an append-only row. UPDATE, DELETE, TRUNCATE are refused by
database trigger — not by convention. Changing your mind is a *new* row linked to the old one
(`supersedes` for replacement, `amends` for one clause), so the record shows what was believed and
when, forever. *Witnessed: e17 (increment 17 of this project's predecessor build sequence)
exercised both correction tracks organically; refused mutations are banked in `seen-red/06` (this
repository's own convention: a directory under `seen-red/` holds the runnable proof that a refusal
actually fired, per item 6 below).*

**2. Authorship you didn't type, so it can't be faked by typing.**
Every row is attributed. The `actor` is resolved from the database connection; on top of that, rows
written through the intercepted path carry an HMAC **stamp** binding them to the actual Claude
session/agent that wrote them — injected by a hook, unforgeable without a secret the writer's role
cannot read. A forged or stale stamp is refused at write time; a bypass write is recorded as
unstamped, visibly. *Witnessed: e17 live; forgery/staleness refusal proven by
`kernel/fixtures/s17_stamp_fixture.py`.*

**3. A second pair of eyes that has to be real — and now session-aware, not just agent-aware.**
A review claiming independence is refused unless it was written by a *provably different
invocation* than the work it reviews. Through s17 alone this meant "a different `stamp_agent`,"
which falsely refused an honest cross-session reviewer whose main thread also stamps
`agent='main'` (BACKLOG 2026-07-09, "Independence investigation verdict"). **s21** fixes this:
`validate_independence` and the `review_stamp_distinctness` view now decide distinctness from the
**(stamp_session, stamp_agent) pair**, never `stamp_agent` alone — strictly more permissive
cross-session, byte-identical same-session (a NULL half on either side is still treated as NOT
distinct, fail-safe never fail-open). *Witnessed: at e17 an inflated independence claim was
refused live and the genuinely independent reviewer then caught a real defect the author's own
verification had passed (pre-s21, still valid — same-session distinctness is unchanged by s21).
s21 itself fired in anger for the first time during run 5 (2026-07-10, mid-run forensics): a
reviewer's `technical` claim was REFUSED by `validate_independence` ("SAME invocation wrote
both"), the reviewer then honestly downgraded to `self-review` citing the NULL-half fail-safe
rule verbatim — kernel fail-safe held with the hook layer dark. Applied live to `toycolors` (an
existing, pre-s20 project deployment this document cites repeatedly as a real-world test
substrate, distinct from the throwaway `--new-world` probes named elsewhere here) (confirmed
*this pass*: `review_stamp_distinctness` there carries `review_stamp_session`/
`regards_stamp_session`) and to every `--new-world` scaffold's birth chain since.*

**4. Edits gated on declared intent (refuse-and-teach).**
With the change-gate hook wired, an edit to a governed source file is *refused* unless a current
ledger entry declares that file — and the refusal message teaches the exact honest path (file the
entry, re-issue). Comply and it unlocks; both the refusal and the unlock land in a journal. The
hook now also **fails closed** rather than silently governing nothing: if an explicitly-configured
`SUBJECT_ROOT`/`GATE_SUBJECT_ROOT` does not exist on disk, the gate DENIES loudly with teach-text
instead of matching zero files (the run-2 integrity finding, 2026-07-09 — a moved/renamed project
directory used to defeat the gate silently). *Witnessed: the §6 acceptance run drove refusal →
teach → comply → allow from a fresh clone (`runs/acceptance-20260707T222452/`); the dangling-
`SUBJECT_ROOT` fail-closed path has its own seen-red proof, both polarities
(`seen-red/change-gate-subject-root/`, 5 cases, commit `296ce6d`).*

**5. "Done" that can't be claimed while checks are missing.**
A close (the end-of-increment verdict) runs a registry of mandatory checks. A check that did not
run is loudly QUARANTINED — provably distinct from "passed" and from "nothing to check" — and any
OPEN finding turns the close RED: an increment cannot report complete with undischarged defects.
*Witnessed: the acceptance close came out RED-honest on 6 open findings, which is the machinery
working, not failing.*

**6. Commits gated mechanically, and every gate proven able to fail.**
Pre-commit runs the refusal chain, currently (per `hooks/pre-commit`, 2026-07-09 ruling):
staging_guard → no_lazy_imports → fixture_census → doc-legibility (report-only). `layout_census`
is deliberately **not** wired here — a maintainer ruling (BACKLOG 2026-07-09) named it a guarantee
for *downstream* template consumers, not a self-guarantee this research repo needs; the script
itself is untouched and still shipped. Every wired gate has banked **seen-red** evidence — a
recorded run where it actually refused. *Witnessed: an undeclared commit was refused from a fresh
clone; each migrated gate re-proved red (`seen-red/`, now 20+ dated fixture directories including
`change-gate-subject-root/`, `stamp-intercept-secret/`, `conformance_check/`).*

**7. Obligation debt is actually reachable — grants gap and stale views closed (s20).**
Before s20, the kernel's own `review_gap` view named an obligation-tracking capability the
subject role could not reach: `countersign_obligation` (the table backing an assignment) was
never GRANTed to the subject role (a lineage-wide gap since s13/s14), and `ledger_current`/
`countersigned_in_force` were `SELECT l.*` views frozen at s15's column set, so s17's five
`stamp_*` columns never appeared in either — a consumer wanting `stamp_verified` had to bypass
the view. s20 grants `SELECT, INSERT` on `countersign_obligation` to the role (mirroring the
ledger's own grant posture) and re-issues both views with explicit, s17-complete column lists.
*Witnessed: applied to `toycolors` (2026-07-09) — `review_gap` readable with no permission error,
both views carry all five `stamp_*` columns, a full obligate → review-gap-shows-debt →
countersign → debt-cleared round trip landed (ledger rows 71-73). Re-witnessed *this pass* on the
`capsprobe` throwaway world: `led obligate cap-scope author reviewer` succeeded, `led review-gap`
reflected it, and `led obligate revoke cap-scope` was correctly REFUSED (see item 9 below).*

**8. A queryable notion of "what work is in flight" — the work-item ledger (s22).**
Five new ledger columns (`work_slug`/`work_title`/`work_depends_on`/`work_resolution`/
`work_witness`) and four new `kind` values (`work_opened`/`work_claimed`/`work_depends_on`/
`work_closed`) — no new base table, per the spec's SSOT invariant. A duplicate opening act for
the same slug is REFUSED at insert (`validate_work_item`), as is a claim/dependency/close row
naming a slug with no opening act. `resolution='shipped'` REQUIRES a non-empty `work_witness` —
enforced as a table CHECK (`work_shipped_requires_witness`), the strongest available surface (an
illegal row cannot exist even transiently) — the "omega shipped-without-ship-ref" lesson from
run 1's uncommitted-deliverable finding. Two derived views: `work_item_current` (one row per
slug: state/title/resolution/witness/claimant) and `work_item_violations` (four members:
`duplicate_open`/`shipped_without_witness` — both provably vacuous under normal operation, listed
as defense in depth — and the genuinely reachable, deliberately-unrefused
`depends_on_unknown_slug`/`dependency_cycle`). *Witnessed this pass on `capsprobe`*: `led work
open cap-probe-1 "..."` → `led work claim cap-probe-1` → `led work close cap-probe-1 shipped
--witness "capsprobe witness commit"` → `led work list` showed the closed row with its
witness/claimant; `led work violations` returned 0 rows (clean); a second item
(`cap-probe-2`) opened+claimed but left open showed up correctly in `led work list` and in
`pickup`'s IN-FLIGHT section (below). **Not yet applied to `toycolors`** (confirmed live this
pass: `validate_work_item` does not exist in that schema) — s22 ships in every fresh
`--new-world` birth chain but is not yet an operator-applied delta on the pre-existing live
deployment.

**9. `led`'s own guardrails around obligations and work — refusal, not silent widening.**
`led obligate revoke <scope>` checks the connecting role's **live** grant via
`has_table_privilege` before attempting the delete — never a hardcoded assumption — and under
the current (s20) kernel this refuses every time with teach-text naming the maintainer-run
one-liner that does revoke it (an obligation is standing operator-owned policy config, not a
role self-service capability). `led work close` additionally gates client-side on a prior
`work_claimed` row before allowing a close (the s22 trigger only requires the item be *opened*,
not claimed — run-5 forensics found two work items closed with no claim ever landing,
unflagged). *Witnessed this pass on `capsprobe`*: `led obligate cap-scope author reviewer`
succeeded, then `led obligate revoke cap-scope` printed the exact REFUSED message above verbatim
(role `capsprobe_rw` has no DELETE grant, checked live) and named the maintainer's schema-owner
one-liner. The claim-before-close gate is built and documented in `led`'s own usage text; not
separately re-exercised this pass beyond the ordinary claim→close path above.

**10. `--refs row:<id>` — a sanctioned bare cross-reference on any kind.**
The kernel's typed `regards` edge is reserved for `kind=review` (s15 `validate_review`,
unchanged through s21). For any other kind that needs to cite an earlier row (e.g. a
verification citing the pre-registered criteria it checks against), the free-text `refs` column
carries the convention `row:<id>` — s15's own `enacts` column comment names this channel
outright ("a bare reference uses refs"). *Witnessed this pass*: `led --refs row:1 verification
"capsprobe witness: citing antecedent row:1 via refs convention"` landed as ledger row 5 with
`refs='row:1'`, retrievable via `led --recent`/`led current`.

**11. `pickup` — a live-derived resume brief, work-item-aware.**
Five sections (`IN-FORCE-DECISIONS`, `OPEN-QUESTIONS`, `REVIEW-DEBT`, `RECENT-CHANGES`,
`GIT-STATE`) plus a sixth, **`IN-FLIGHT`**, added for s22: open work items (slug/title/claimant)
from `work_item_current`, plus a `work_item_violations` count that is explicitly "violations:
none" when clean (never a silently-absent line) — and an honest `UNAVAILABLE (no work-item
layer ...)` fallback, not a crash, when the target world's kernel predates s22. Nothing here is
cached; every section is a live SELECT re-run at pickup time. *Witnessed this pass on
`capsprobe`*: `IN-FLIGHT` correctly showed `(0 rows)` / `violations: none` right after
`cap-probe-1` was closed, then showed `cap-probe-2 | ... | author` once that second item was
opened+claimed and left open — both the empty and non-empty shapes exercised in one session.
`REVIEW-DEBT` returned real (empty) rows rather than `BLOCKED: pre-s20 grants` (that fallback
text exists for a pre-s20 world; `capsprobe`, freshly scaffolded, is post-s20 by construction).

**12. `judge` — the ASP/SQL marriage differential, wired per-project.**
`./judge` invokes autoharn's `engine/ledger_differential.py --retain` against the project's own
`deployment.json`, banking a `DerivationRecord` pair under autoharn's
`engine/docs/ledger-marriage/derivations/<name>/` on every run, and prints the closed verdict
vocabulary (`AGREE | DIVERGE_BY_DESIGN | DIVERGE_DEFECT | QUARANTINED`), exiting non-zero iff any
family is `DIVERGE_DEFECT`/`QUARANTINED`. Deliberately observer-first: not wired into any gate.
*Witnessed this pass on `capsprobe`*: `AGREE`, `asp=10 sql=10 atoms`, `Δasp=[] Δsql=[]`, exit 0
("DIFFERENTIAL GREEN — every target bit-identical to the SQL floor"). The derivation record this
run banked was deliberately removed after the probe teardown (out of this pass's touch-only-
CAPABILITIES.md scope, and specific to the torn-down `capsprobe` world).

**13. `bootstrap/new-project.sh --new-world` — opening an isolated world is one scripted command.**
Per the "one world per run" ruling (maintainer, 2026-07-09: a run's subject must not see a
sibling run's ledger history), `--new-world <name>` derives `--schema`/`--kern`/`--role` from one
name, applies the FULL current birth chain in order — `high_watermark_1.sql` → s20 → s21 → s22 →
s23 — with every `-v` var spelled out, seeds the stamp secret idempotently (never rotates an existing
one), registers the `reviewer` principal (`author` is auto-seeded by `s15-schema.sql`), writes
`deployment.json`, and (new-world only) writes the world-root `CLAUDE.md` governance preamble —
so opening a run is one scaffold command, one `cd`, one `claude`, no hand-paste (the ratifier's
own acceptance bar). The script also self-documents: it captures its real argv + UTC timestamp
*before* argument parsing consumes it, and writes a PROVENANCE header into the scaffolded
`.claude/HOOKS.md` naming the exact command, the lineage chain applied, and mode-aware status
lines for the stamp secret / s21 / reviewer registration (closing the "how was run3 created?"
gap — a prior world had to have its birth reconstructed from template residue and SELinux
context because nothing recorded it). *Witnessed this pass*: `capsprobe` scaffolded clean
end-to-end (kernel+s20+s21+s22 applied with only cosmetic `NOTICE: ... does not exist, skipping`
lines from idempotent `DROP CONSTRAINT IF EXISTS`/`DROP TRIGGER IF EXISTS` — no errors; secret
provisioned; `reviewer` principal registered; `deployment.json` + `CLAUDE.md` + the three verbs
written), followed by the full `led`/`judge`/`pickup` round trip above, then torn down with zero
residue (`DROP SCHEMA ... CASCADE` both schemas, `DROP OWNED BY`/`DROP ROLE`, confirmed by an
empty post-drop `information_schema.schemata` query and directory removal). *Re-witnessed
2026-07-11 (s23 fold, BACKLOG dated entry) on `batchprobe`*: birth chain now reaches s23 —
`information_schema.columns` confirmed `stamp_invocation` present on `ledger`/`ledger_current`/
`countersigned_in_force` post-scaffold, no errors beyond the same cosmetic idempotent-DROP
NOTICEs; torn down zero-residue the same way.

**14. `bootstrap/apply-delta.sh` — DEMOTED TO HISTORY (maintainer ruling 2026-07-11), file
DELETED same day.** The ruling's own vocabulary was "deleted, not documented"; the file's
continued presence was flagged as a live hazard (an executable script whose every
legitimate scenario the law had abolished) by the s24 commission's adversarial review
(the s24 commission: the delegated build that produced kernel-lineage delta
`s24-declared-event-time.sql`, item 24a below), and it was
`git rm`'d executing the already-ratified instruction. The witness record below stays as
history of what the script was.
Runs are strictly linear: run M > N settles run N's world as dust — there is no operator
scenario for applying a delta to an existing world, and the ceremony this script guarded
(typed confirmation, provenance line) was witnessed producing exactly the cargo-cult
paperwork a high-assurance project must not impose on a non-expert operator ("I was told
to run a delta ... until I realized it does nothing at all"). Deltas reach reality via
the birth chain at the next scaffold. The script and its witness record below stay as
history; it is no longer part of the operator surface. Original entry, retained:
Resolves db/host/schema/kern/role from `<world-dir>/deployment.json` alone (refuses loudly on a
missing/malformed file, never guesses), prints the fully-resolved `psql -v ...` command before
doing anything, requires the operator to **type the schema name back** (a mismatch aborts, no
`--yes`), and on success appends a dated `APPLIED` line to the world's `.claude/HOOKS.md`
PROVENANCE section. States plainly on failure that lineage deltas are NOT transaction-wrapped (a
mid-file error can leave a partial apply) and not to re-run blind. *Witnessed (2026-07-09) on a
throwaway `deltaprobe`/`deltaprobe_kernel`/`deltaprobe_rw` world (pre-s21): wrong-confirmation
abort (no db change), missing-`deployment.json` refusal, a deliberately-broken delta's
psql-failure path, and a real positive apply (s21's CREATE FUNCTION/TRIGGER/VIEW, no ERROR; the
HOOKS.md PROVENANCE line landed). Not re-exercised this pass — read-only re-verification of the
script's logic only (UNWITNESSED this session, cited from the prior session's record).*

**15. Class-ratified fail-safe deltas — some kernel deltas no longer need a per-delta maintainer
question.**
CLAUDE.md ORCHESTRATION (2026-07-09 ruling): a kernel lineage delta that only ADDS refusals,
vocabulary, or derived views — strictly fail-safe, nothing existing relaxed — and that arrives
scratch-witnessed on both polarities with the SQL/ASP differential in AGREE, is pre-ratified as a
**class**: it enters the birth chain without individual sign-off. *(Clause corrected
2026-07-11: this entry originally kept apply-to-existing as "the scripted, typed-confirmation
operator act" — the runs-are-linear ruling later abolished apply-to-existing entirely; a
class-ratified delta reaches reality only via the birth chain at the next scaffold, and the
apply script is deleted, see item 14.)* This class was named retroactively as the shape
s21 and s22 both already satisfied. *UNWITNESSED as its own
mechanism this pass*: no delta has yet been authored and landed *citing* this class explicitly
(it is a standing rule, not (yet) an exercised gate) — the honest state is "ratified rule, no
instance run under it yet."

**16. Self-application — the harness's own operational acts meet its own bar.**
CLAUDE.md ORCHESTRATION (2026-07-09 ruling, issued after run 2's world was found broken at birth
by an unscripted scaffold-to-`/tmp` + hand-`mv`): no operator procedure ships as prose steps +
hand-pasted SQL/bash where a scripted, witnessed verb is possible ("why is this not a verb?" is
the first question every walkthrough must answer), and every orchestrator choice or judgment is
explained on the record at the moment it is made — an unexplained decision has the same standing
as an unwitnessed claim. Items 13/14 above are this ruling's own concrete discharges (the
run-starting ceremony and the delta-apply ceremony were each, per the ruling's own honest
self-assessment, commissioned *reactively* — after the manual version had already caused a real
incident — rather than proactively; the ruling makes proactive scripting the standing default,
not a post-incident remedy).

**17. The commission/conformance checker — mechanizing "does the report match the ask" (observer only).**
`instruments/conformance_check.py` diffs a structured commission (scope items, each with a
`witness_type`) against a report's verdicts, closing on `CONFORMANT` /
`CONFORMANT_WITH_DEFERRALS` / `NONCONFORMANT`. Of the five witness types, only `commit` and
`file` are mechanically checked here; `ledger_row`/`db_state`/`gate_output`/`doc_excerpt` each
print a loud `OPERATOR-CHECK:` line naming the exact command to run, rather than silently
passing — the explicit boundary: this instrument verifies claim/artifact *correspondence*, never
artifact *quality* or effect-level acceptance. **STATUS: observer only** — not wired into any
hook, gate, or pre-commit chain; promotion to an enforcing gate is a maintainer act. *Witnessed:
`seen-red/conformance_check/` carries its own both-polarity proof (built, per BACKLOG/commit
history); not re-exercised this pass.*

**18. Permit-to-work — a ledger entry is not a permit; an open+claimed work item is (s22).**
`hooks/pretooluse_change_gate.py` composes a SECOND, PRIOR gate in front of the existing ticket/
window logic: when the gate is WIRED and the world's ledger carries the s22 work-item layer, a
Write/Edit/NotebookEdit on a governed file (and the already-denied bash-mutation-into-governed-
file class) is DENIED unless `work_item_current` shows at least one row with `state='open'` AND a
non-NULL claimant, teaching the exact `./led work open`/`./led work claim` commands. Landed commit
`495e088` (BACKLOG "Run-5 forensics", 2026-07-10). *Witnessed: `seen-red/change-gate-subject-root/`
cases `f-permit-to-work-no-open-claimed` (DENY, no open item), `g-permit-to-work-open-claimed-
allowed` (ALLOW, a claimed item exists), and `h-permit-to-work-pre-s22` (skipped entirely — a
pre-s22 world has no work-item layer to check) — all three against a real scratch schema in the
toy db, both-polarity, run via `seen-red/change-gate-subject-root/run_fixtures.py`.*

**19. Matcherless stamping — the command-shape matcher is DELETED, not grown a fourth shape.**
`hooks/stamp_intercept.py` no longer tests whether a Bash command LOOKS like a psql call; when
the hook is wired (a deployment record located, or `STAMP_SECRET` explicitly set), every Bash
command is rewritten unconditionally to export the HMAC stamp as `PGOPTIONS`, inherited by any
descendant process — a generated script, a `cd`-prefixed chain, an evasion shape nobody has
thought of yet — because the export happens before any of the subject's own command text runs,
never conditional on recognizing it. Landed commit `495e088` alongside item 18 (same pass, same
BACKLOG). *Witnessed: `seen-red/stamp-intercept-secret/` cases `f-evasion-cd-prefix-injected` and
`g-evasion-generated-script-injected` (the exact two evasion shapes run 5's forensics found) both
now get stamped, plus `h-preexisting-pgoptions-overridden`/`i-preexisting-pgoptions-no-space-
metachar` (the subject's own competing `PGOPTIONS` assignment is neutralized so this hook's export
wins) — all via `seen-red/stamp-intercept-secret/run_fixtures.py`.*

**20. Clean-exit gate — "done means clean" mechanized as a Stop hook, not left as CLAUDE.md
advice.** `hooks/stop_clean_exit.py` reads the world's own ledger (read-only) on every Stop event
and refuses to let the turn end while `review_gap`/`question_status`/`work_item_current`
(state=open)/`work_item_violations` show anything outstanding — enumerating each item by id/slug
with the exact closing command. A circuit breaker allows the stop (with a loud warning) after the
IDENTICAL debt set has blocked three consecutive attempts, so unclosable debt (obligated to a
different principal, a dependency cycle) cannot wedge a session forever. Landed commit `58ce4e4`.
*Witnessed: `seen-red/stop-clean-exit/run_fixtures.py` drives a real, freshly-scaffolded throwaway
world (`.stopprobe`, toy db) through the full stateful sequence — unwired passthrough, a clean
world (silent allow), a dirty world (BLOCK, debt named), the circuit breaker firing on the third
identical block (ALLOW-with-warning), then cleanup back to a clean, silent allow with the state
file cleared. **LIVE-WITNESSED 2026-07-10 (run 7, partial)**: fired on a genuine session's Stop
event (transcript `stop_hook_summary` 21:26:59Z, 200ms, silent-allow — the world's debt views
were already empty). The BLOCK path and circuit breaker remain fixture-witnessed only: run 7's
agent closed its debt before stopping, so the gate never had to refuse. See the run-7
verification entry in BACKLOG.md (2026-07-10).*

**21. Demurral detector — the ADR-0013 Rule 3 out-of-frame backstop (observer, classifier OFF by
default).** `hooks/demurral_detect.py` sends a candidate text (a drafted `AskUserQuestion`, or a
Stop-event completion claim) to a SEPARATE, context-free classifier and asks Rule 3's own three
discriminators (mandated? pre-drawn conclusion? who decides?) — never the executor's own
self-assessment. Observer mode only: it never blocks, denies, or asks; a positive verdict injects
an `additionalContext` warning plus a journal record. Landed commit `460c90e`. *Witnessed:
`seen-red/demurral-detector/red-specimen.py` fires the detector on ADR-0013's own canonical
Specimen 2 (a drafted question with the skip pre-recommended) on both attachment points, and
stays silent on a genuine hard negative (a neutral scope question) — a LIVE fixture, real
`claude -p --model claude-haiku-4-5-20251001` classifier calls, `seen-red/demurral-detector/
eval-witness.txt` banks the corpus-level precision/recall numbers. **The classifier defaults to
OFF** (this pass's apparatus.json switchboard, item 23) — no world pays for a classifier call it
did not opt into.*

**22. Mutation observer — detecting an evasive bash mutation after the fact, since predicting
every write-shape is impossible (this pass, 2026-07-10).** `hooks/posttooluse_mutation_observer.py`
closes the epistemic half of the bash-evasion gap `bash_mutates_governed()`'s own command-shape
enumeration cannot close (a `python3`-driven write, or any descendant process that writes bytes
without spelling a recognized shell redirection, evades that matcher — the same "enumeration
fails open" class matcherless stamping (item 19) retired for psql-stamping, structurally
unfixable here too since PreToolUse only ever sees command TEXT). Two legs: `PreToolUse(Bash)`
touches a marker file under the world's `.claude/`; `PostToolUse(Bash)` runs `find SUBJECT_ROOT
-newer <marker> -type f` (excluding `.claude/logs/`, a short list of named hook state files, and
`.git/`) and, reusing permit-to-work's own `has_work_item_layer()`/`has_open_claimed_work_item()`
query shape, journals + injects a non-blocking warning naming the mutated files and the
`./led work open`/`claim` teach-text whenever a mutation lands with no live open+claimed work
item — silent when one exists. **OBSERVER ONLY, by construction, not by degree**: `mode:
"enforce"` is not merely unimplemented, it is IMPOSSIBLE for this attachment point (the mutation
has already happened by the time PostToolUse fires) — apparatus.json naming it anyway is warned
and downgraded to `observe`. **Named residues, stated honestly**: deletions are invisible to
`find -newer` (a removed file never "changed"); mtime-preserving writes (`touch -r`,
`cp --preserve=timestamps`) defeat the whole detection method; the marker is one shared file per
world, not per invocation, so two genuinely concurrent Bash calls in the same session could
cross-attribute a mutation to the wrong command. *Witnessed: a direct stdin-harness run against a
real scratch schema in the toy db (this pass) — a python-driven write with no open work item
produced the warning naming the file and command; the identical write with an open+claimed item
was silent — plus `seen-red/mutation-observer/run_fixtures.py`'s own banked both-polarity proof.
**UNWITNESSED-LIVE**: this hook has fired only via a direct stdin harness, never yet during a
genuine live Claude Code session's own PreToolUse/PostToolUse Bash events — see "Built,
unexercised" below.*

**23. The apparatus.json mechanism switchboard — per-world configurability for all six mechanisms
(maintainer mandate, 2026-07-10).** Every mechanism above (`change_gate`, `permit_to_work`,
`stamp_intercept`, `clean_exit`, `demurral_detect`, `mutation_observer`) now reads its OWN mode —
`"off"` / `"observe"` / `"enforce"` — from `<world>/.claude/apparatus.json`'s `mechanisms.<name>
.mode`, LIVE, at every invocation (no re-scaffold needed to change behavior). `"off"` skips the
mechanism entirely (no journal, no state); `"observe"` runs the same checks but turns a
would-have-denied outcome into an ALLOW carrying a loud `additionalContext` warning plus a journal
record, never a block; `"enforce"` is byte-identical to each hook's behavior before this pass. An
unrecognized mode string never widens permissions — every hook falls back to its own default
(named per-mechanism in `bootstrap/templates/APPARATUS.md`) with a loud stderr warning. The one
mechanism that spends real money per invocation (`demurral_detect`'s classifier) defaults to
**OFF**, inverting the "free mechanisms default to their current strength" rule on purpose — "no
world may silently bill its operator" (maintainer mandate, verbatim); its `cost_note` field sits
next to the switch. *Witnessed (this pass)*: a throwaway probe world
(`bootstrap/new-project.sh --new-world consolprobe --db toy --host 192.168.122.1` into
`/home/bork/w/vdc/1/.consolprobe`) confirmed the birth `apparatus.json` carries every default
(demurral_detect OFF) with no hand-editing; on `change_gate`, `mode=off` let a previously-denied
edit through untouched, `mode=observe` produced a warning instead of a denial, and `mode=enforce`
denied — the same three-way spot-checked on `stamp_intercept` (off = no injection; observe =
inject-but-warn-on-broken-secret instead of deny; enforce = deny). Torn down after, zero residue.
`seen-red/apparatus-config/run_fixtures.py` banks the same three-way both-polarity proof
permanently (`change_gate` full three-way, `stamp_intercept` spot-check), registered in
`gates/fixture_census.py`.

**24. The contemporaneity correlation verb (`./audit`) — Part 2 of
design/CONTEMPORANEITY-AUDIT.md (BACKLOG "Contemporaneity indictment", 2026-07-11).** A fifth
operator verb (`bootstrap/templates/audit.tmpl`, scaffolded alongside `led`/`judge`/`pickup` by
`bootstrap/new-project.sh --new-world`) that joins a world's ledger rows against its
`.claude/logs/invocations.jsonl` token journal (s23) and the three existing hook-journaled
tool-activity logs, and reports the closed verdict vocabulary
`CONTEMPORANEOUS | BATCHED_DECLARED | LATE_DECLARED | BACKFILL_SUSPECT` (LATE_DECLARED added
2026-07-11 evening, see the dated addendum below) — ASP-FIRST per the maintainer's
directive: the verdict logic lives in `engine/lp/contemporaneity.lp` (batch/silence/
backfill_suspect derived from an EDB — extensional database, the fact set an ASP program
reasons over — of `invocation/2`, `row_tokened/4`/`row_untokened/3`,
`tool_event/2`, with `burst_threshold_ms`/`silence_threshold_ms` entering as FACTS in
`engine/contemp_thresholds.lp`, never hardcoded in a rule), run via the shared `clingo_run.py`.
Thresholds are MEASURED, not guessed: derived from the runs 5-8 corpus (db `toy`,
192.168.122.1) — see `engine/contemp_thresholds.lp`'s own derivation comments for the exact
query and numbers (burst_threshold_ms=1000, from a measured gap of [21ms,40ms] for genuine
same-command bursts vs. 1141ms for the smallest genuine distinct-moment gap; silence_
threshold_ms=180000, reasoned below the two hand-forensic true positives on record, 503s and
312s). HONEST HISTORICAL LIMIT, ENFORCED: runs 5-8 (and any pre-s23 world) get an EXPLICIT
typed refusal (`NO_VERDICT`, exit 3) naming the missing capability, never a guessed verdict —
*Witnessed live* against run7's own real, unmodified schema (read-only): `s23_capable=False`
named as the refusal's reason, exit 3, plus a degraded ts-cluster burst table (explicitly marked
INFERRED, never conflated with a STATED token burst) that reproduces the exact burst shape
BACKLOG's own hand forensics found (rows 5-8, 13-16, 17-20, ...) and the exact burned-id
refusal fingerprint (id 62) BACKLOG's forensic pass found by hand. **CAPABILITY IS WIREDNESS,
NOT CORPUS NON-EMPTINESS (run9 amendment, same day, 2026-07-11)**: the first landing keyed
capability on whether any events had been journaled yet, so run9 — the first s23-capable world,
fully and correctly wired, fresh enough that only orientation commands had run — was falsely
refused (`NO_VERDICT` exit 3, "Missing/excluded: ['tool_event']") and the maintainer stopped
the run over it. Fixed same day: `engine/contemp_edb.py` now reads each journal family's
capability from the world's OWN wiring (settings.json hook references + apparatus.json
off-switches — the `produced`-vs-`capable` two-axis split `engine/ledger_edb.py` already
carries), and a fully-capable world with ZERO ledger rows gets an explicit `VACUOUSLY_CLEAN`
(exit 0: "0 ledger rows, nothing to audit yet — NOT evidence of conduct"), never a refusal.
*Witnessed live* against run9's real world, read-only, post-fix: capability-present
(`tool_event` reported "EMPTY (capable, zero events yet)", not EXCLUDED), `VACUOUSLY_CLEAN`,
exit 0 — banked verbatim as `seen-red/contemporaneity-audit/run9-vacuous-clean-witness.txt`.
*Witnessed on a scratch world (full s23+journal capability, apparatus-authored, both
polarities)*: `seen-red/contemporaneity-audit/run_fixtures.py` — a clean multi-row token burst
with dense tool activity verdicts `BATCHED_DECLARED` (exit 0, zero backfill_suspect tokens); a
manufactured >300s tool-activity silence with zero ledger rows immediately followed by a 2-row
burst verdicts `BACKFILL_SUSPECT` (exit 1), naming the offending token; an UNWIRED empty world
verdicts N/A (exit 3, no wiring evidence at all); a WIRED-but-empty world (the run9 shape,
reproduced synthetically) verdicts `VACUOUSLY_CLEAN` (exit 0) — never a guessed
CONTEMPORANEOUS, never a false refusal. *Witness-record correction (the auditprobe claim)*: the
first landing's record here read "produced the correct N/A refusal" for a freshly-scaffolded
empty world — accurate as an observation (auditprobe DID exit 3, exactly as run9 later did; the
witness reproduced), but the behavior it blessed as "correct" was the design defect the run9
specimen exposed. Under the fix a scaffolded fresh world is vacuously clean, not refused. **Second-producer status, declared
honestly**: this ships ONE producer (the ASP derivation) — the marriage discipline's SQL-floor
differential (this domain's sibling to `engine/ledger_floor.py`) is FILED in BACKLOG.md, not
built, this pass (a maintainer critical-path resequencing scoped the first landing to the
ASP-derived core); a verdict here is not yet cross-validated AGREE-style. **Named hazard, fixed
in-pass, not deferred**: clingo/clasp's integer terms are 32-bit signed C ints and silently wrap
on an absolute 2026-era epoch-millisecond value (found live, in this module's own first test
against real run7 data, before an anchor-relative encoding closed it — every T this module
emits is now relative to a per-export minimum-timestamp anchor, never absolute). **Named hazard,
flagged then FIXED (same day, separate pass)**: the hook journals `contemp_edb.py` reads
originally disagreed on a timestamp convention (UTC-Z vs naive-local `datetime.now()`); flagged
in BACKLOG.md by this build, then unified to UTC-Z at the hooks themselves in the pre-run-9
window (commit 19c9159). `contemp_edb.py::_parse_ts_ms` deliberately keeps both parse branches
so journal lines written before that fix stay readable (same-host reading remains the correct
assumption for exactly those historical lines).

**24a. Late-entry discipline (2026-07-11 evening addendum) — design/LATE-ENTRY-AND-INTAKE-
SEMANTICS.md, all three ratified proposals, implemented same evening.** Item 24's own vocabulary
gains one member and one annotation, both additive; nothing above this addendum is relaxed.
**Proposal 1 (intake-shape annotation, engine-side only, no vocabulary change):** a
`token_burst` whose every row precedes this world's own first `tool_event` is now annotated
`intake-shape (precedes all tool activity)` on the burst-table line
(`engine/lp/contemporaneity.lp`'s `intake_shape/1`) — the run-10 first-audit specimen's own
shape (BACKLOG "Run-10 first audit verdict adjudicated": rows 2-11, one invocation token,
present-tense task declarations written before any tool activity existed). *Witnessed on a
scratch world reproducing that shape* (case h, `seen-red/contemporaneity-audit/run_fixtures.py`):
`VERDICT: BATCHED_DECLARED`, exit 0, the burst line carrying the annotation — never touching the
live run-10 world itself (runs are linear; a settled world is read-only evidence, never a fixture
substrate). **Proposal 2 (declared late entries — kernel/lineage/s24-declared-event-time.sql +
one new verdict):** `led` gains an optional `--event-time <iso-ts>` flag
(`bootstrap/templates/led.tmpl`) writing a nullable `event_declared_ts` column, distinct from
`ts` (write time) and from s23's `stamp_invocation` (a capture-only, trigger-derived stamp;
`event_declared_ts` is the OPPOSITE shape — a plain writer-supplied, unauthenticated declaration,
disclosed as such in the kernel delta's own header). Omitting the flag is byte-identical to
today's semantics. The audit gains **LATE_DECLARED**: the silence-breaking row of a burst that
would otherwise verdict BACKFILL_SUSPECT instead verdicts LATE_DECLARED (exit 0) when that row
carries a declared event time whose gap from its own write time exceeds `late_threshold_ms`
(60000ms, `engine/contemp_thresholds.lp` — reasoned below the one real specimen on record,
run-10 row 1's self-reported ~120s gap, the same below-the-smallest-true-positive method
`silence_threshold_ms`'s own derivation uses). BACKFILL_SUSPECT now means precisely the
UNDECLARED case — sharpened, not relaxed. **s24 SCRATCH-WITNESSED, both polarities, differential
AGREE**: applied clean on a throwaway schema (`s24val`/`s24val_kernel`/`s24val_rw`, TOY db) atop
the full s15…s23 chain; a row written with no `event_declared_ts` reads NULL (today's semantics
unchanged) and a row written WITH one round-trips correctly; the existing HMAC/stamp machinery
(forged stamp refused, valid stamp verifies true, event_declared_ts coexisting with a valid
stamp) is byte-identical before and after — no trigger touched, grep-verified; `engine/
ledger_differential.py s24val` (via `LEDGER_DEPLOYMENT`) reports **AGREE** (`asp=10 sql=10
atoms; Δasp=[] Δsql=[]`) both on the raw scratch schema and after real `led --event-time` writes
through the shim. `led.tmpl`'s own backward-compatibility hazard — this template executes LIVE
for every already-scaffolded world, old and new alike (the "live verbs" ruling) — is closed by a
LIVE `information_schema.columns` capability check, paid only when `--event-time` is actually
passed: an s24-capable world writes the column; a pre-s24 world REFUSES loudly (never a silent
drop of a value the operator explicitly asked to be recorded), naming the fix (omit the flag, or
note the late entry in prose as run-10 row 1 did). **COVERAGE GUARD (added after an out-of-frame
hack-rationalization audit of this same commission found the gap, same session):** `--event-time`
is parsed by `led.tmpl`'s ONE shared top-level flag loop but only the generic `<kind>
<statement...>` path's INSERT carries `event_declared_ts` — `led review`/`led work *` each have
their own INSERT that does not. Rather than silently no-op on those verbs (the audit's finding),
`led.tmpl` now REFUSES loudly, exit 1, naming the reason, when `--event-time` is passed to
`--recent`/`current`/`question-status`/`review-gap`/`stamp-distinctness`/`register-principal`/
`obligate`/`review`/`work` — widening the flag to those verbs is a named future increment, not a
silent gap. **Witnessed, SCRIPTED (not merely prose)**: `seen-red/contemporaneity-audit/
run_fixtures.py` cases (i)/(j)/(k) invoke a REAL `led` shim (the same exec-wrapper `bootstrap/
new-project.sh` writes) as a subprocess against two real schemas — case (i): generic-path
`--event-time` succeeds and round-trips (exit 0, read back via SELECT); case (j): the coverage
guard refuses on `work open` (exit 1, teach-text visible); case (k): a SECOND scratch schema
(`contempprobe_pre24`, applied through s23 only) proves the missing-column refusal against a real
pre-s24 schema, not merely the s24val schema case (i)/(j) share. Both schemas torn down to zero
residue after a clean run. `bootstrap/new-project.sh --new-world`'s birth chain now applies s24
automatically (never applied to any *existing* world — runs are linear). **Proposal 3 (preamble
line):** `bootstrap/templates/CLAUDE.md.tmpl` gains point 9, verbatim from the ratified memo:
"Record as you go — one row at the moment of the act. Batching declarations you are making right
now (an intake decomposition) is fine; the token declares it. If you must record an act after
the fact, declare its event time — never narrate the past as if live." **Seen-red, both
polarities, banked**: `seen-red/contemporaneity-audit/run_fixtures.py` cases (f)/(g) — the
IDENTICAL silence-then-burst gap shape, declared verdicts LATE_DECLARED/exit 0
(`late-declared-green.txt`), undeclared verdicts BACKFILL_SUSPECT/exit 1
(`late-declared-red.txt`), the latter re-asserting case (b)'s own pre-extension behavior is
unaffected. **Honest limit, named:** `late_threshold_ms` is a REASONED lower bound from the one
real declared-late specimen on record (run-10 row 1, itself an improvised prose disclosure that
predates s24), not a full corpus measurement — re-measure once a run born after s24 produces
real `--event-time` data (the same disclosure `silence_threshold_ms`'s own header already
carries for its axis). **Hazard found and flagged, not fixed this pass (same audit):**
`kernel/lineage/s24-declared-event-time.sql`'s own header originally asserted "bootstrap/
apply-delta.sh is retired" as settled fact; the script is in fact still present, executable, and
functionally capable of applying a delta to an existing world — corrected in the SQL file's own
prose and flagged loudly in BACKLOG.md's dated entry (deleting/neutering the script is a
separate, larger decision, not taken here).

**24b. SQL-floor marriage differential — item 24's own deferral CLOSED (2026-07-12, Sonnet,
commissioned build).** `engine/contemp_floor.py` (the SQL floor) + `engine/contemp_differential.py`
(the differential runner, matching `engine/ledger_differential.py`'s AGREE/DIVERGE_BY_DESIGN/
DIVERGE_DEFECT/QUARANTINED vocabulary + DerivationRecord banking by import, never re-derived) give
this verb the same marriage-grade cross-validated pair the ledger's `T_now` judgments already have
(`T_now` is this project's name for the record-time facts `engine/lp/ledger_tnow.lp` derives — see
item 30 below for its own full gloss; it is cited here only to say this verb now gets the SAME
two-producer treatment). `./audit --differential` (opt-in, default OFF — reasoned in `audit.tmpl`'s
own header) runs both producers and prints AGREE/DIVERGE beneath the normal report; a new exit code
4 marks "audit was clean but the differential disagreed," never silently folded into exit 0.
**Witnessed live**: seen-red case (p) — AGREE, `asp=63 sql=63 atoms`, DerivationRecord pair
retained; case (q) — a manufactured DIVERGE_DEFECT (a forged atom substituted into the SQL floor's
own output, never touching either real producer's source), correctly caught and named. **A second,
previously-latent 32-bit clingo-wraparound hazard was found live authoring this pass's own
fixture** (a window spanning ~7 years, ~100x past the documented safe bound) — flagged, and
guarded against with a loud QUARANTINE refusal in `contemp_differential.py` (in-scope: this module
owns the anchor normalization step), rather than fixed at `contemp_edb.py`'s own source (out of
this commission's touch-list). The full account, the denomination-normalization design, and the
fixture reordering this hazard required all live in `design/CONTEMPORANEITY-AUDIT.md`'s Status
section and in BACKLOG.md's dated entry. Deferrals stay unchanged: `engine/contemp_audit.py` (item
24's own single-producer report script, the one `./audit` execs) still defaults its own `--retain`
flag OFF, the verdict is still computed over the whole ledger window rather than per-session, and
Part 3 stays filed.

**24c. Preamble-ordering audit (`./audit --preamble`) — Part 3 of design/
ORCH-CONTEMPORANEITY-PART3-SPEC.md LANDED (2026-07-12, Sonnet, commissioned build; closes the
Part-3-implementation half of the audit-verb-completions tracker item; item 24/24a/24b's own
memo left standing, "Part 3 (untouched, as scoped above)").** Turns the governance preamble's
twelve numbered points (`bootstrap/templates/CLAUDE.md.tmpl`, the points every scaffolded world
receives at birth) from prose into F1-F12 verdicts a program derives from the world's own event
record. It reasons inside the SAME settled deontic position item 20 below (obligation grants)
already instantiates once (`countersign_obligation` -> `review_gap`): the **Anderson reduction**
— an obligation is a recorded, other-assigned fact rather than a modal claim (no O/P/F operator
exists in this project's logic layer), and a violation is simply a derived flag computed from
whether the discharging record is present. Here that fact family is `preamble_obligation/2`, one
per family, recorded in `engine/preamble_obligations.lp`. `engine/lp/preamble_ordering.lp` stacks
on `engine/lp/contemporaneity.lp` (F12 imports Part 2's own backfill_suspect/late_declared
wholesale) and reads SIX new EDB extensions folded into `engine/contemp_edb.py`'s own
`export()`: E1 (work-item shapes + `work_claimed`), E2 (`refs`/`regards`), E3 (the stop-hook
journal), E4 (a fine delegation-dispatch/return read), E5 (Bash-completion tokens), E7
(actor/countersign) — plus E8, the `preamble_obligation/2` catalogue itself (a facts file, not
an EDB read), and a template-side addition, E6 (one journaled line in
`bootstrap/templates/verify-commission.tmpl`). The spec's own §3 TWO-CLOCK BRIDGE requires that
a tokened ledger row occupy the interval `[invocation(Tok,Lo), invocation_completed(Tok,Hi)]`;
this interval governs every cross-seam "before"/"after" comparison between a ledger row and a
journal event, refusing with a typed reason (`untokened_row`/`open_window`/`window_overlap`)
rather than ever guessing from a raw `ts` comparison. Each family gets a closed-vocabulary
verdict — DISCHARGED | VIOLATED | UNDECIDABLE(reason) | VACUOUS — and the family stratum
(`preamble_verdict/2`) emits all TWELVE always (E8's own catalogue grounds every family even on
an empty world), so a missing verdict is itself a loud defect, never silence. Ships with its OWN
SQL-floor marriage pair from day one (`engine/preamble_floor.py` + `engine/preamble_differential.py`,
importing `engine/ledger_differential.py`'s conventions exactly) — unlike item 24's own first
landing, which shipped single-producer and closed the gap one delta later (24b) — fulfilling the
spec's own mandate ("no exemption is invoked... ships as a pair, or its report says why"). **Witnessed
live**: `seen-red/preamble-ordering/run_fixtures.py`, ALL GREEN — two consolidated scratch worlds
(GREEN: F1-F10/F12 DISCHARGED, F11 UNDECIDABLE by this build's own named scope reduction; RED:
F1/F2/F3/F4/F8/F9/F10/F11 VIOLATED, F7 UNDECIDABLE(untokened_row)), both differentials AGREE
(`asp=36 sql=36` / `asp=33 sql=33`, zero delta), and a manufactured negative control was caught
and correctly labeled DIVERGE_DEFECT (this project's name, in its closed differential-verdict
vocabulary, for "the two independent producers disagree" — see item 24b above for the full
vocabulary). The REAL historical corpus (runs 4/5/6/7/9/10/11, read-only, dust) all differential
AGREE too, and its own 84-instance (7 worlds x 12 families) distribution is UNDECIDABLE-heavy as
the spec itself predicted (39 vacuous, 25 undecidable, 17 discharged, 3 real, previously-unknown
VIOLATED findings — run4's F7, run5's F6, run11's F3). Exit-code composition: `--preamble` never
overrides a non-zero base `./audit` exit; a clean base (0) may rise to a NEW code 5 iff >=1
family is VIOLATED, mirroring `--differential`'s own exit-4 rule exactly. **Deferred, named
honestly (not silently narrowed):** F11's `question_open`/full review-gap arms need a
second, separate EDB composition (`engine/ledger_edb.py`'s own `entry`/`supersedes` export, a
different denomination, no consumer yet) that this pass does not build — those arms report
UNDECIDABLE(capability_absent) categorically rather than a guessed clean; F7's `regards`-edge
refined form (E2, already EMITTED but not yet consumed by any rule) ships coarse only. Full
disposition: `design/ORCH-CONTEMPORANEITY-PART3-SPEC.md`'s own dated Status section and
BACKLOG.md's dated entry beside it.

**25. `distance-to-clean` — the composed closure-debt verb (BACKLOG "Five-item batch,
maintainer-approved 2026-07-11 evening", item 1; design/RETROSPECTIVE-RUN10.md Finding 1).** A
sixth operator verb (`bootstrap/templates/distance-to-clean.tmpl`, scaffolded alongside
`led`/`judge`/`pickup`/the scaffold verb/`audit` by `bootstrap/new-project.sh --new-world`) that reads the SAME
three existing debt views `led review-gap`/`question-status`/`work violations` already expose
and prints their counts and ids in one pass — computing nothing new, no new join, no derived
predicate. The three disaggregated commands remain the documented default, unchanged (the
maintainer's own condition on this item). Built to kill the run10 pattern the retrospective
named: 47 of run10's 299 invocations (about 16%) were bare polls of `./led review-gap` alone,
because one call could not answer "how far am I from a clean stop." *Witnessed live* on a
throwaway `--new-world` probe (`batch5probe`, torn down after): a clean world reports `TOTAL
debt: 0`, exit 0; after registering a real obligation, writing an unreviewed row, an open
question, and a work item with a dangling dependency, the SAME probe reports `review-gap: 6
row(s) -- ids: [2, 3, 4, 5, 6, 7]`, `question-status: 1 open of 1 total -- open ids: [6]`,
`work-violations: 1 violation(s) -- slugs: [widget-x]`, `TOTAL debt: 8`, exit 1 — cross-checked
id-for-id against the disaggregated `led review-gap`/`question-status`/`work violations` output
on the same probe (identical rows, identical counts), proving this verb reads the same views
rather than a second, driftable copy of their logic.

**26. `commission` ledger kind, two signing modes — capturing the ask itself
(`kernel/lineage/s25-commission-kind.sql`; BACKLOG "Five-item batch, maintainer-approved
2026-07-11 evening", item 2; design/RETROSPECTIVE-RUN10.md Finding 5 and could-not-answer item
4).** The retrospective's harness recommendation, closed: "capture the commission at intake as
a frozen ledger row ... so that 'deliverable versus commission' can be checked mechanically
against the source, not only against the agent's restatement of it." `commission` joins the
`ledger_kind_check` vocabulary — a pure set union (every prior kind stays legal, unchanged),
class-ratified per the kernel-delta decision tree (OPERATING-CARD.md's "Kernel deltas" section,
sourced from CLAUDE.md ORCHESTRATION). Two signing modes, mechanically distinguishable by
actor identity + stamp state, never prose claims alone: **FULL mode** — the maintainer signs the
ask himself, in his own terminal, via the exact line `bootstrap/new-project.sh --new-world`
prints at scaffold time: `LED_ACTOR=commissioner ./led commission "<the ask verbatim>"` (the
`commissioner` principal, class `human`, is registered automatically at scaffold time alongside
`author`/`reviewer` — no separate registration step). **LAZY mode** — the implementer's own
FIRST ledger act on receiving a commission (`bootstrap/templates/CLAUDE.md.tmpl` point 10),
transcribing the ask verbatim under their own `author` actor, statement prefixed "(vicarious
transcription by the implementer; carries no commissioner guarantee)" — the agent's own stamped
invocation already proves the transcription vicarious by construction; the prose marker is
required IN ADDITION, per the maintainer's own words. Decomposition rows cite the commission via
the pre-existing `--refs row:<id>` channel, no new edge type. **Pre-s25 worlds refuse
`commission` loudly**, and the refusal's teach-text (the run-10 closure-audit fix,
`_led_kind_refusal_teach()`) correctly names that world's OWN live (shorter) valid-kind list,
never a stale or hardcoded one — verified, not assumed: `led.tmpl` requires zero code change for
this interaction to work, because the teach-text already re-queries `pg_get_constraintdef` live
per invocation. *Witnessed live*, two ways: (1) a real `--new-world` scaffold (`batch5probe`) —
`LED_ACTOR=commissioner ./led commission "..."` landed `actor='commissioner'`, unstamped
(typed from a bare shell, no live Claude session to inject a stamp — the honest "unstamped-but-
attributed" case the design names); a second, default-actor `./led commission "(vicarious
transcription ...) ..."` landed `actor='author'`; a `--refs row:2` decision row round-tripped
correctly; a separate pre-s25 schema (`s15`..`s24` only, no s25) refused `commission` with the
live teach-text naming its own 13-member list (no `commission`), exit 3. (2) scratch-witnessed
both polarities plus the SQL/ASP differential, `seen-red/s25-commission-kind/run_fixtures.py`
(7 cases — legality, `--refs`, existing-kinds-unchanged as a union not a replacement,
invalid-kind-still-refused, actor-distinguishes-the-two-modes, prior s23/s24 columns untouched,
pre-s25 refusal-with-teach — all green) plus `engine/ledger_differential.py` reporting **AGREE**
(`asp=10 sql=10 atoms; Δasp=[] Δsql=[]`), zero schema/role residue after teardown, re-verified.
**Named limit:** no new ASP/SQL derived view consumes `commission` rows yet (e.g. "every
`work_opened` traceable to a commission via `--refs`") — a plausible follow-on, filed as a
possibility in the delta's own header, not built or claimed built this pass.

**27. Read observer — closing the "did the reviewer actually read it" gap
(`hooks/pretooluse_read_observer.py`; BACKLOG "Five-item batch, maintainer-approved 2026-07-11
evening", item 3; design/RETROSPECTIVE-RUN10.md could-not-answer item 3).** The retrospective
named this UNDECIDABLE from the existing record: "the invocation log captures only Bash ... a
reviewer that inspects files via the Read tool leaves no trace ... review rows that claim
'independently read app/index.html' are trusted, not witnessed." A new `PreToolUse(Read)` hook,
wired into every freshly scaffolded world's `.claude/settings.json` and switched by
`mechanisms.read_observer` in `.claude/apparatus.json` (default `"observe"`, mirroring
`mutation_observer`/`delegation_observer` (item 22's after-the-fact bash-mutation watcher and
the subagent-dispatch watcher on `hooks/pretooluse_delegation_observer.py`, respectively) —
their own house convention that a costless observer defaults ON), journals every `Read` call's
UTC-Z timestamp, session id, and file path to
`.claude/logs/read_observer.journal.jsonl` — nothing else (no content, no excerpt). No warning,
no deny path: reading a file is never itself a policy violation under this project's law, so
`"enforce"` in config is a NAMED-NOT-YET-SANCTIONED case (warns loudly, behaves as `"observe"`),
distinct from `mutation_observer`'s genuine PostToolUse impossibility. *Witnessed*, both
polarities, `seen-red/read-observer/run_fixtures.py` (six cases, pure filesystem, no database):
a real `Read` call against a wired, `"observe"`-mode (and missing-key-default) probe lands
exactly one journal line with the right ts/session/path; `"off"` writes nothing at all even
though a real `Read` just happened; `"enforce"` warns on stderr and downgrades to `"observe"`
behavior; a non-`Read` tool call (`Write`) produces no output and no journal line; an unwired
invocation (no `GATE_SUBJECT_ROOT`, no real cwd) is silent; two further real reads against the
same wired probe append two more lines, in order — proving accumulation, not overwrite. All six
green, zero probe-directory residue after the fixture's own teardown.

**28. `attest-tags` — signed ratification tags, verified against a committed key
(`attest-tags`, repo root; `filing/gpg_trust.py`; design/GPG-TRUST-LAYER.md §2, Rung 1 of 3 —
design/GPG-TRUST-LAYER.md's own name for each of the three signing mechanisms it specifies, in
build order; items 28/29/30 here are Rungs 1/2/3 respectively).**
Enumerates every `ratified/*` git tag, verifies each against `law/keys/*.asc` using a throwaway
GNUPGHOME built per invocation (never the operator's ambient keyring), and reports any commit
whose message claims ratification with no verifying tag. Three verdicts, all loud except the
first: `GOOD` (a tag's signature verifies against a committed key), `BAD` (a tag exists but does
not verify — unsigned, tampered, or signed by a key never committed), and `UNVERIFIABLE` (no
public key is committed at all — `law/keys/` is empty — so no tag's signature can be checked
against anything; a distinct label from `BAD`, never a relabeled worst case, because "cannot
check" and "checked and failed" are different facts). *Witnessed*, both polarities,
`seen-red/attest-tags/run_fixtures.py` (real GPG, a scratch git repo, a fresh Ed25519 test key
generated per run, all torn down after): a tag signed with a committed key verifies `GOOD`, exit
0; an unsigned (lightweight) tag is refused `BAD` with git's own "cannot verify a non-tag object"
detail, exit 1; a tag signed by a key deliberately never committed to the scratch `law/keys/`
(the forger case) is refused `BAD` identically, exit 1; a commit whose message contains "RATIFIED"
with no covering tag is listed as an uncovered claim. Run against THIS repository's own real
history (no `ratified/*` tags exist yet, `law/keys/` is genuinely AWAITING-KEY — see
`law/keys/README.md`): reports "0 keys committed (AWAITING-KEY)", "0 `ratified/*` tags", and
every RATIFIED-marked commit as uncovered — the honest, expected report for a keyless,
unratified-by-tag repo, never a false clean. (`UNVERIFIABLE` itself fires per-TAG, so it prints
only once at least one `ratified/*` tag exists to check — witnessed in the seen-red fixture's own
scratch repo, which has tags; this repository's own real history currently has none.)

**29. `verify-commission` — SIGNED-mode commissions, the third of three commission-signing
strengths (LAZY < FULL < SIGNED — `design/GPG-TRUST-LAYER-FAQ.md` §5 walks all three;
`bootstrap/templates/verify-commission.tmpl`; design/GPG-TRUST-LAYER.md §3, Rung 2 of 3).**
Implements the closed vocabulary `VERIFIED | UNSIGNED | FORGED-OR-CORRUPT` (exit non-zero only on
the third) PLUS two typed refusals distinct from all three verdicts (`GPG-UNAVAILABLE`, exit 2;
`NO-COMMITTED-KEY`, exit 3 — neither precondition leaves any of the three verdicts decidable),
reading a commission row's CURRENT statement bytes and any banked `.claude/commission-<id>.asc`,
checked against THIS DEPLOYMENT's own `keys/*.asc` (a sibling of its `deployment.json`, never
autoharn's `law/keys/` — see the key-residence note below) via the same shared scratch-keyring
mechanism as item 28 (`filing/gpg_trust.py` — `law/adr/0012-compositional-and-structural-hygiene.md`'s
Principle 1, "single source of truth / derive-don't-duplicate": one home, two callers now
pointed at two different directories by design). **Key-residence revision (2026-07-11/12, "key-residence refactor" commission):** this
verb originally resolved `AUTOHARN / "law" / "keys"` — a maintainer finding the same evening
("THIS repository should not have anything to do with end user's keys... any end-user would find
[it] counter-intuitive") named this as a conflation of autoharn's own law-signing with every
deployment's commission-signing. Fixed by resolving the deployment's own `keys/` instead (see
`bootstrap/templates/keys-README.md.tmpl`, `bootstrap/track-work.sh`, and
design/GPG-TRUST-LAYER.md §7 / design/GPG-TRUST-LAYER-FAQ.md §3 for the full split); wired into
`bootstrap/track-work.sh`'s standing-deployment scaffold same-commission. `bootstrap/new-project.sh`'s
matching `keys/` scaffolding for WORLDS is the one piece FROZEN this pass (a live session was
running in the shared checkout when this landed — CLAUDE.md's liveness rule); the mechanism does
not depend on it (`filing/gpg_trust.py`'s `committed_keys()` degrades an absent directory to
"zero keys," the same honest AWAITING-KEY shape either way), only the friendly `keys/README.md`
stub a `--new-world` scaffold does not yet write. Closed, and fixed in the course of building it,
TWO real defects, neither merely flagged: (a) a byte-fidelity hazard in the ceremony's own naive
form (`gpg --detach-sign --armor ~/aa` signs a trailing newline that `$(cat ~/aa)` strips before
insertion — an honest commission would otherwise verify as forged; the fix, `printf '%s'
"$STATEMENT" | gpg --detach-sign`, ships in both the scaffold's printed ceremony and
`design/GPG-TRUST-LAYER-FAQ.md` §5); (b) an out-of-frame hack-rationalization audit, run before
this shipped as "done" (CLAUDE.md's own standing rubric), caught an earlier version folding the
"no committed key exists to check a claimed signature against" case into `FORGED-OR-CORRUPT`,
reasoning the spec's vocabulary was "closed to three members" — a reason the SAME file's own
missing-gpg handling already contradicted, and the wrong structural choice relative to item 28's
own `attest-tags` precedent (which uses a distinct `UNVERIFIABLE` label, never a relabeled
`BAD`). Fixed by giving that precondition its own verdict string and exit code
(`NO-COMMITTED-KEY`, 3), so a fresh, keyless repository's commissions (this repository's own real
state today) are never indistinguishable, by verdict string alone, from an actual forgery.
Wired into `bootstrap/new-project.sh`'s six-verb shim loop (item 25's `distance-to-clean`
precedent for adding a verb without touching a live-executed template) and one sentence in
`bootstrap/templates/CLAUDE.md.tmpl`'s governance-preamble point about commission verification
(run it at intake, carry the verdict into the first row of the session's own task breakdown —
its ledgered decomposition of the commission into work items, per that same preamble's own
first point). *Witnessed*, all five outcomes, `seen-red/verify-commission/
run_fixtures.py` (a real throwaway `--new-world` scaffold, a real FULL-mode commission via `led`,
a fresh Ed25519 test key): no `.asc` banked yields `UNSIGNED`, exit 0; signing with the
byte-fidelity-fixed ceremony against a committed test key yields `VERIFIED`, exit 0; the same
`.asc` path re-signed over different bytes, checked against a committed key, yields a genuine
cryptographic mismatch, `FORGED-OR-CORRUPT`, exit 1; a good signature checked against the
DEPLOYMENT's own `keys/` with the committed test key TEMPORARILY moved out (the honest
AWAITING-KEY state a fresh scaffold starts in — never autoharn's `law/keys/`, per the
key-residence revision above) yields the distinct refusal `NO-COMMITTED-KEY`, exit 3; `gpg`
absent from `PATH` yields the other distinct refusal, `GPG-UNAVAILABLE`, exit 2.

**30. `row_hash` chain + `verify-chain` — the anchored ledger, kernel delta s26 + the signed head
(`kernel/lineage/s26-row-hash-chain.sql`; `bootstrap/templates/verify-chain.tmpl`;
design/GPG-TRUST-LAYER.md §4, Rung 3 of 3).** Every ledger row gains a SHA-256 `row_hash` (hex text)
of a canonical, INJECTIVE, timezone-safe serialization of every OTHER column, concatenated
with the predecessor row's `row_hash` (or a per-world genesis seed, `kernel.chain_genesis`,
auto-provisioned by `bootstrap/new-project.sh --new-world`, not a secret — its only job is making
two worlds' row-1 hashes differ). Computed by ONE shared SQL function
(`compute_row_hash()`, called identically by the insert trigger and by `./verify-chain`'s
read-only walk — ADR-0012's Principle 1 (see item 29 above), no second re-derivation of "what a
row means" to drift). TWO real
defects were found and closed, neither merely flagged: (a) a concurrency race (two concurrent
inserts could interleave their predecessor reads and fork the chain, given how `bigserial`
allocates before a `BEFORE INSERT` trigger runs), closed with a per-schema
`pg_advisory_xact_lock`; (b) an out-of-frame hack-rationalization audit, run before this shipped
as "done," found that an EARLIER version of `compute_row_hash()` coalesced `NULL` and `''` to the
IDENTICAL serialized token — a genuine hash COLLISION (not merely an adversarial-hardening gap:
`rationale IS NULL` and `rationale = ''` are different, SQL-observable facts), which would have
let a schema-owner tamper (`rationale IS NULL` → `''`, bypassing `append_only_row`, the trigger
that otherwise enforces the ledger's append-only invariant) produce ZERO
change to the stored hash anywhere in the chain — defeating not just the chain walk but the
signed-head backstop below, for free. Closed by replacing the delimiter-join with a
length-prefixed, presence-tagged encoding (`hashfield()`: `'N:'` for NULL, `'V<len>:<value>'` for
present, self-delimiting so no two column-value tuples can serialize identically) — see
`compute_row_hash()`'s own header for the full account. Class-ratified (strictly
additive: one column, one genesis table, two functions, one trigger that fires last and writes
only the new column — nothing existing relaxed) and entered `bootstrap/new-project.sh`'s
`LINEAGE_CHAIN` (that script's record of which kernel deltas a freshly `--new-world`-scaffolded
world is born with, applied automatically). *Witnessed*, both polarities plus the differential plus the collision closure,
`seen-red/s26-row-hash-chain/run_fixtures.py` (a real throwaway `--new-world` scaffold): an
INSERT attempted before the genesis seed exists is refused loudly; three real rows via `led`
build a chain `./verify-chain` reports `INTACT`; `--head` emits exactly `{world, max_id,
head_hash, utc}` and nothing else; the EXISTING SQL/ASP marriage differential
(`engine/ledger_differential.py`) still verdicts `AGREE` on an s26 world, proving the delta does
not perturb existing `T_now` facts (the record-time atoms `engine/lp/ledger_tnow.lp` derives
from the ledger — this project's "what the record says now" half of its two-clock temporal
split); tampering `rationale` from `NULL` to `''` (the specific
collision found by the audit) now IS detected (a direct recomputation shows the stored hash no
longer matches, `stored_hash_now_matches_altered_content=f`); a historical row's content
surgically altered (trigger bypassed, mirroring a schema-owner-level tamper) while its own
`row_hash` is left stale breaks the chain AT the altered row (the spec's own words, verified
literally); the sophisticated variant — the tamperer also rewrites that row's own hash to match
its new content — moves the detected break to the very next row instead, never later; `--head`
against a broken chain refuses with EMPTY stdout, exit 1 (never signs a head it has not
verified). The full signed-head ceremony (§6 of `design/
GPG-TRUST-LAYER-FAQ.md`) was additionally exercised end to end on a real scaffolded world with a
throwaway test key: `gpg --verify` reports `Good signature` on the banked `.claude/head.json` +
`.claude/head.json.asc` pair. Key rotation (revoke → generate → commit → re-sign) was also
exercised on the same test key, witnessed in `design/GPG-TRUST-LAYER-FAQ.md` §8, including the
genuine finding that a revoked key becomes immediately unusable for new signing (`gpg` refuses
outright, "Unusable secret key" — stronger than a mere warning). **Note on key residence
(2026-07-11/12 audit, filed alongside item 29's revision):** `verify-chain.tmpl` reads NO
committed-keys directory at all, in either domain — the signed-head ceremony above is a direct
`gpg --detach-sign` / `gpg --verify` pair run by the operator against their own ambient
`~/.gnupg` keyring, never `filing/gpg_trust.py`'s scratch-keyring mechanism items 28/29 share.
An earlier draft of `filing/gpg_trust.py`'s own module docstring and of
design/GPG-TRUST-LAYER-FAQ.md §3 claimed otherwise (listing this verb as a third caller of that
mechanism); corrected in both places this same pass — a documentation inaccuracy caught and
fixed in passing, not a code change, since there was no committed-key resolution here to
relocate.

**31. Small follow-ups batch — a read-only ledger verb, two timing journals, and a gate liveness
counter (BACKLOG "Follow-ups commission scope extended (maintainer, 2026-07-11)" and the
run-11-forensics change proposals it queues; the small-follow-ups commission executed the same
day).** Four small, additive mechanisms are bundled into one entry because each is small on its
own:

- **`led show <id>` is a real, read-only subcommand** (`bootstrap/templates/led.tmpl`): it
  prints one ledger row, every column, in full (`psql -x` expanded display, statement never
  truncated). Before this it silently fell through to the generic write path with kind="show",
  refused by the kernel's `ledger_kind_check`, burning a sequence id on every attempt — the
  run-11 first-shift-forensics pass's own finding (BACKLOG "Run-11 first-shift forensics
  (2026-07-11)", item 7: `led show <id>` was reached as an intuitive read-only verb but absorbed
  into the write path instead). It now refuses loudly, with teach-text, on a missing id, and
  never reaches the write path at all — proven by the ledger id sequence's own `last_value`
  staying unchanged across a missing-id `show`. *Witnessed*, both polarities,
  `seen-red/contemporaneity-audit/run_fixtures.py` cases n/o (a real `led` shim against a real
  scaffolded schema).
- **The doc-shapes gate now counts its own liveness.** `gates/doc_shapes.py`'s two checks
  (standalone-fragment paragraphs; positional references into `HANDOFF.md`, the wholesale-
  rewritten status document, where a bare position like "item 2" can dangle after a rewrite —
  ADR-0017's deterministic core) run at write time in a scaffolded world via
  `hooks/pretooluse_doc_shapes_gate.py`. That
  hook now also writes a second, separate journal, `doc_shapes_gate.exercised.jsonl`: it gets
  one line per COMPLETED evaluation (clean, denied, or observed-would-deny alike), written only
  after the check actually runs to completion. A gap between a world's `.md` Write/Edit count
  and its exercised-line count is therefore itself the signal that the gate is silently
  fail-opening — closing the exact epistemic limit the run-11 forensics pass named: "a clean
  pass and a silently-broken gate are byte-identical from the DENY-only journal alone"
  (BACKLOG "Run-11 first-shift forensics (2026-07-11)", item 2). *Witnessed*, both polarities,
  `seen-red/doc-shapes-gate-world/run_fixtures.py`'s EXERCISED-LIVENESS case: five real
  evaluations produce five lines in order; the sixth call (mode="off", which returns before the
  check runs) produces none.
- **PostToolUse Bash completion timestamps land in a new sibling journal.**
  `hooks/posttooluse_bash_completion.py` (new) writes `bash_completions.jsonl`, banking each Bash
  call's completion time (UTC-Z) beside `hooks/stamp_intercept.py`'s existing PreToolUse dispatch
  token. It FIFO-pairs each completion against that dispatch by a shared `command_sha256` where a
  match exists (`pairing: "token"`, `duration_ms` included) and honestly marks
  `pairing: "ts-only"` when none does — the maintainer's own design, named verbatim in the
  commission as "invocation token if recoverable, else ts-pairing," stated here as a disclosed
  heuristic: a named residual gap is that two truly concurrent Bash calls with byte-identical
  command text can pair to the wrong dispatch. It is a sibling file, not a new line shape inside
  `invocations.jsonl` itself, so the existing contemporaneity EDB (`engine/contemp_edb.py`) is
  untouched. *Witnessed*, both polarities plus the FIFO-double-dispatch case,
  `seen-red/bash-completion/run_fixtures.py`.
- **The delegation observer gained a return leg.** `hooks/pretooluse_delegation_observer.py`
  (extended) now also attaches at PostToolUse on `Task|Agent`. It journals a `kind: "return"`
  line FIFO-paired against its own dispatch line (the hook's existing per-dispatch journaling
  contract is unchanged; the return leg is a strictly additive new line kind in the SAME
  journal), giving dispatch-to-return duration per subagent — the reviewer-execution-window
  inference gap the run-11 retrospective named as still blocked (BACKLOG "RETROSPECTIVE-RUN11
  ... second iteration of the record-sufficiency experiment (2026-07-11)": "with the product
  shipping clean, the record can witness that review HAPPENED and READ the files but not that it
  REASONED HARD"). A match carries `dispatch_ts` and `duration_ms`; no match is honestly
  `pairing: "unresolved"`. *Witnessed*, both polarities plus the FIFO-double-dispatch case,
  `seen-red/delegation-observer/run_fixtures.py`'s three new return-leg cases (g/h/i), extending
  the file's existing dispatch-leg cases (a-f) unbroken.

Two convention-only additions add no new mechanism (`bootstrap/templates/CLAUDE.md.tmpl`): a
preamble sentence on point 5 names `./distance-to-clean` as available for a one-command closure
check (the disaggregated `review-gap`/`question-status`/`work violations` views remain the
documented default); and a new preamble point 12 exhorts the orchestrating agent to ledger a
returning subagent's self-reported token/usage numbers, if ledgered at all, explicitly marked as
an unverified self-report ("no harness guarantee") — the same trust class as a LAZY commission
transcription, diagnostic-grade by design (BACKLOG "Maintainer principle: the action stream is
the evidentiary basis; session internals are diagnostics (2026-07-11)").

## Built, unexercised (exists; has not yet fired in anger)

- **Assumption validity bounds** — an assumption can carry "valid until / valid within" and an
  expiry closure exists, but no real task has posed a bounded assumption yet.
- **Review fix-point** — a close line requiring review rounds to continue until a stamp-distinct
  review finds nothing undisposed (the "iterate until clean" loop). Built for e18; gates nothing
  yet. **Known residue, named not fixed**: `instruments/review_fixpoint.py`'s `FpRow` still
  carries `stamp_agent` alone (no `stamp_session` field) — the identical session-blind
  distinctness defect s21 fixed at the kernel layer, one register up, in a Python instrument.
  Filed (BACKLOG 2026-07-09), fix shape named (thread `stamp_session` through `FpRow` and both
  joins, mirroring s21's pair rule), not yet built.
- **Class-ratified fail-safe deltas (item 15 above)** — the rule stands; no delta has yet been
  authored and landed under it by name.
- **The Stop-hook wiring (`clean_exit`, item 20; `demurral_detect`'s Stop leg, item 21) and the
  mutation observer (item 22)** — every one of these has been driven, both-polarity, through a
  scripted stdin harness that hand-assembles the exact JSON Claude Code's hook contract
  documents and feeds it to the hook script directly (this project's standing seen-red
  convention, the same method `kernel/fixtures/s17_stamp_fixture.py` and every other DB-touching
  fixture here already uses). NONE of the three have yet fired during a genuine LIVE Claude Code
  session's own Stop/PreToolUse/PostToolUse event — that first real firing is still owed, named
  here rather than left for a reader to assume "seen-red" means "seen live."

## Honest limits (so the guarantees aren't oversold)

- **Machine-observable events only.** The gap-detection works where a trigger is mechanical (a
  write, a commit, a close line). *Noticing* a hazard, *recognizing* an assumption — judgment
  events — have no oracle; nothing can prove one silently didn't happen. Backstop: the independent
  review (item 3) and the engineering-responsibility clause in `CLAUDE.md`.
- **The stamp is a tripwire, not authentication.** Same OS user; the secret is huntable by a
  determined local attacker. It catches drift and self-review, not a malicious admin.
- **N=1 where it says N=1.** One witnessed firing proves the mechanism exists, not how often it
  catches things.
- **Tool provenance covers the apparatus's own solvers** (engine runs bank a pinned
  engine+version+hashes record), **not yet the subject's build tools.**
- **The ledger WAS a diary the writer controls the timing of, not a permit log — run-5 forensics
  (2026-07-10). HALF FIXED, and this entry previously overclaimed "NOW FIXED" (corrected
  2026-07-11 after the maintainer caught the slide).** The finding had two halves. The PERMIT
  half — writes with no open work item — is fixed by permit-to-work (item 18) for the two
  `PreToolUse` hooks it covers (Write/Edit/NotebookEdit + the already-denied bash-mutation
  class); the evasive-bash residue is `mutation_observer`'s after-the-fact territory (item 22).
  The CONTEMPORANEITY half — rows landing in retroactive bursts long after the acts they
  describe — was never fixed and never re-measured until 2026-07-11, when a read of run7's own
  timestamps showed the same burst signature in run 7's celebrated clean loop (four work_closed
  in 0.11s; reviews 0.02s apart) and in run 8. A permit gates whether you may write; nothing yet
  records WHEN the recorded act actually happened relative to the row. Design filed:
  design/CONTEMPORANEITY-AUDIT.md (per-invocation stamp token + a first-class correlation verb);
  until it lands, treat every ledger `ts` as INSERT time, not event time.
- **The stamp interceptor WAS a command-shape matcher, and matchers get evaded — NOW FIXED (item
  19 below).** Run 5 found a third distinct evasion shape (`cd run5 && ./led ...`; `cat >
  script.sh; bash script.sh`) — every one of 38 writes that session landed unstamped despite the
  hook firing correctly on two unrelated read-only commands. The matcher is deleted; every Bash
  command in a wired world is now stamped unconditionally (item 19).
- **Bash-driven mutation is still only OBSERVED, never denied (`mutation_observer`, item 22
  below).** Detecting a mutation after the fact via `find -newer` is not the same guarantee as a
  PreToolUse deny — deletions and mtime-preserving writes are invisible to this detector (named
  residues, item 22), and there is no enforce mode for this mechanism at all: a PostToolUse
  observation fires after the mutation already happened, so "deny" is not a state this attachment
  point can ever reach.

## Not yet enforced — designed but unbuilt, or scheduled but not scheduled (load-bearing honesty)

- **`pg_hba` superuser hardening.** A maintainer act, unscheduled — the host's `pg_hba.conf`
  currently governs auth by admitting only registered databases from the operator's host; no
  further hardening (e.g. narrowing superuser reach, per-role `pg_hba` entries) has a committed
  design or a queued date. Referenced in passing across `HANDOFF.md`,
  `POST-FABLE-OPERATING-BRIEF.md`, `WALKTHROUGH.md`, and `design/human-side-fragility.md` (the
  "pg_hba ordering slip" fragility mode), never as a scheduled increment.
- **s22 (work-item ledger) is not applied to the `toycolors` deployment — DEAD, not pending
  (2026-07-11).** Under the runs-are-linear ruling `toycolors` is settled evidence; there is
  nothing to apply anything to, ever. Retained here only so the earlier "not yet taken" framing
  is visibly superseded rather than silently deleted.
- **`instruments/conformance_check.py` is observer-only** (item 17 above) — no gate consumes its
  verdict yet.
- **Review-fixpoint's session-blind residue** (see "Built, unexercised" above) — filed, fix shape
  named, not built.
