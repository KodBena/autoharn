# CAPABILITIES — what the harness can already do, in plain words

Each item: what you get, how it is enforced, and how we know it works — **witnessed** means it
has fired for real at least once (the evidence is banked); **built, unexercised** means the
mechanism exists but has never fired in anger. Nothing here is aspiration; the aspirational
layer lives in `law/briefs/`. Source of record: `law/briefs/BRIEF-CONFORMANCE-MAP.md`.

This pass (2026-07-10) refreshes the doc past s20 (obligation grants + view refresh), s21
(pair-keyed session-aware distinctness), s22 (work-item ledger), the four operator verbs'
current shape (`led`/`judge`/`pickup`/the scaffold), `bootstrap/apply-delta.sh`, the
self-documenting `--new-world` scaffold, the conformance checker instrument, the fail-closed
hook changes, and the class-ratification + self-application rules in CLAUDE.md ORCHESTRATION.
Method: re-read the source files below, then re-witnessed the operator-facing round trip on a
throwaway probe world (`bootstrap/new-project.sh /home/bork/w/vdc/1/.capsprobe --new-world
capsprobe --db toy --host 192.168.122.1`, torn down after — `DROP SCHEMA ... CASCADE` both
schemas + `DROP OWNED BY`/`DROP ROLE`, zero residue verified by an empty
`information_schema.schemata` query and directory removal). Items marked *(this pass)* carry
that probe's own captured output; older items keep their original citation and were re-verified
against the current source rather than re-run.

## Witnessed

**1. Decisions that cannot be quietly rewritten.**
Every decision/assumption/finding is an append-only row. UPDATE, DELETE, TRUNCATE are refused by
database trigger — not by convention. Changing your mind is a *new* row linked to the old one
(`supersedes` for replacement, `amends` for one clause), so the record shows what was believed and
when, forever. *Witnessed: e17 exercised both correction tracks organically; refused mutations are
banked in `seen-red/06`.*

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
rule verbatim — kernel fail-safe held with the hook layer dark. Applied live to `toycolors`
(confirmed *this pass*: `review_stamp_distinctness` there carries `review_stamp_session`/
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
name, applies the FULL current birth chain in order — `high_watermark_1.sql` → s20 → s21 → s22 —
with every `-v` var spelled out, seeds the stamp secret idempotently (never rotates an existing
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
empty post-drop `information_schema.schemata` query and directory removal).

**14. `bootstrap/apply-delta.sh` — applying one kernel delta to an existing world is one scripted
command, not "pages of SQL."**
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
**class**: it enters the birth chain without individual sign-off. *Applying* such a delta to an
EXISTING live deployment remains the scripted, typed-confirmation operator act
(`bootstrap/apply-delta.sh`) — the ruling removes the authoring question, never the apply act.
Named retroactively as the shape s21 and s22 both already satisfied. *UNWITNESSED as its own
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
- **The ledger is a diary the writer controls the timing of, not a permit log — run-5 forensics
  (2026-07-10).** A live, hook-wired session recorded 8+ minutes of real tool-driven work with
  zero ledger rows, then backfilled 19+ rows in under 90 seconds once the session decided to
  write. Nothing here refuses *late* writes; the fix (permit-to-work, below) is designed, not
  built.
- **The stamp interceptor is a command-shape matcher, and matchers get evaded.** Run 5 found a
  third distinct evasion shape (`cd run5 && ./led ...`; `cat > script.sh; bash script.sh`) —
  every one of 38 writes that session landed unstamped despite the hook firing correctly on two
  unrelated read-only commands. The enumeration approach (raw-psql shape, `led`-wrapper shape,
  and whatever shape comes next) is structurally a cat-and-mouse game; the fix (below) removes
  the game rather than adding a fourth shape.

## Not yet enforced — designed but unbuilt, or scheduled but not scheduled (load-bearing honesty)

- **Permit-to-work gate.** Queued (BACKLOG, run-5 forensics, 2026-07-10; hooks/ frozen while any
  wired session is live, so this cannot land until every such session exits): the change gate
  would DENY substantive tool calls (Write/Edit anywhere in the world, mutating Bash) unless an
  open+claimed work item exists in that world's ledger (s22 supplies the queryable state),
  teaching `./led work open`/`claim`. Confirmed *this pass*: `hooks/pretooluse_change_gate.py`
  carries no such check today — read, not present.
- **Matcherless stamping.** Queued alongside the above, same freeze condition: delete the
  command-shape matcher entirely and have `stamp_intercept.py` inject its `PGOPTIONS` unconditionally
  into every Bash call in a wired world (harmless to non-psql descendants, inherited by any
  generated script), so the enumeration-and-evasion class ceases to exist rather than growing a
  fourth recognized shape. Confirmed *this pass*: `stamp_intercept.py` still matches on command
  shape (`_is_led_invocation` and the raw-psql-with-ledger-db check) — the matcher has not yet
  been deleted.
- **`pg_hba` superuser hardening.** A maintainer act, unscheduled — the host's `pg_hba.conf`
  currently governs auth by admitting only registered databases from the operator's host; no
  further hardening (e.g. narrowing superuser reach, per-role `pg_hba` entries) has a committed
  design or a queued date. Referenced in passing across `HANDOFF.md`,
  `POST-FABLE-OPERATING-BRIEF.md`, `WALKTHROUGH.md`, and `design/human-side-fragility.md` (the
  "pg_hba ordering slip" fragility mode), never as a scheduled increment.
- **s22 (work-item ledger) is not applied to the live `toycolors` deployment.** Confirmed live
  this pass (`validate_work_item` absent from `toycolors`'s functions). It ships in every fresh
  `--new-world` birth chain; applying it to a pre-existing world is the scripted, explicit
  `bootstrap/apply-delta.sh` act, not yet taken there.
- **`instruments/conformance_check.py` is observer-only** (item 17 above) — no gate consumes its
  verdict yet.
- **Review-fixpoint's session-blind residue** (see "Built, unexercised" above) — filed, fix shape
  named, not built.
