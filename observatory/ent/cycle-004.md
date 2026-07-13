# ent observatory — cycle 004

<!-- doc-attest-exempt: point-in-time observatory evidence record, cycle-scoped -->

Commission: autoharn tracker row 372 (work_opened `ent-observatory`, standing series). This
cycle's specific estimate row was not surfaced to this agent (report-only dispatch, no tracker
write access per its own mandate — see the closing note below); citing row 372 and the two
directly-relevant corrections on record since cycle-003 instead: row 566 (maintainer,
2026-07-14) clarifies that action-stream-is-evidentiary-basis bounds what autoharn-as-product
promises a downstream operator, and does NOT bar the autoharn team's own transcript reads of its
own dogfood deployments — superseding row 372's original "never the session transcript" clause,
which had overread its own cited source. This is the FIRST cycle in the series with transcript
access; cycles 001-003 read only ent's tracker (`./pickup`, `./led show <id>`, `./led --recent`),
its `.claude/logs/*.journal.jsonl`, and `git -C /home/bork/ent/picom`. Row 571 (maintainer,
2026-07-14) separately records that a report-only dispatch of this same standing series had
already once overstepped — attempting to adjudicate ADR-0013 itself and draft into `design/` —
and was killed on the spot the instant it reached for a write tool. This cycle's mandate is
explicit about the same boundary and this report holds it: no ADR-0013/0011/0012 adjudication
below, no recipe/policy/design drafting, no autoharn tracker writes, nothing written under
`~/ent`. Subject (`/home/bork/ent`) was read-only for this report — never Written/Edited/
bash-mutated. New this cycle: the actual Claude Code session transcript(s) for `~/ent` were
read directly from `/home/bork/.claude/projects/-home-bork-ent/*.jsonl` (four files; the
terminal/current session is `948fb06c-0ffc-4d92-8892-fa2613e649bc`, which stamped every ledger
row from 164 onward and contains the exchange this cycle was specifically asked to document —
see §3a), cross-checked against `.claude/logs/delegation_observer.journal.jsonl` (a
dispatch/return log this deployment has run in `observe` mode since at least 17:15Z on
2026-07-13, not enumerated in cycles 001-003's gate tables though already populated during their
windows).

## DIFF-VS-PRIOR (baseline: cycle-003 at row 90 / 2026-07-13T20:20Z; cycles 001-002 lineage noted
where relevant)

- **Ledger**: 90 rows → 265 rows (+175, rows 91-265), by far the largest single-cycle growth in
  this series. The session is still live as of this snapshot (row 265, ts `2026-07-14
  01:44:47+02` / `2026-07-13T23:44:47Z`, mid-fix on a round-3 review finding — see below); per
  the runs-are-linear doctrine this is a point-in-time read of an in-progress world, not a
  completed one.
- **The fix stage finally reached the gate.** All 7 of the original 93-finding backlog's P0
  memory-safety findings are now SHIPPED as 4 real commits on the `hardening` branch:
  `6582334` (narrowing/assert-elided, P0 idx46), `4db9df5` (unclamped-value, P0 idx26+idx45),
  `9ef2d6f` (size-bound overflow, P0 idx27+idx55), `905db9f` (GLSL conversion, 2 P0s). `git log
  2dc21884..HEAD` on `hardening` (still the sole worktree) now returns these 4 commits where all
  three prior cycles returned nothing. This closes — partially — the single largest,
  longest-standing evidence gap this series has carried since cycle-002's LOAD-BEARING ANSWER
  section: `change_gate` has real allow/deny/boundary activity to report for the first time (see
  §2). The 17 `harden-*` umbrella work items from cycle-001's original decomposition remain OPEN,
  none closed — the 23-task fix taxonomy that is actually landing commits is a SEPARATE,
  finer-grained decomposition layered on top of cycle-1a's findings, not a 1:1 rename of the 17
  surfaces; closing the umbrella items is evidently deferred until (if) the taxonomy fully
  clears.
- **Of the 23-task taxonomy: 4 shipped (above), 16 further tasks approved but not yet applied —
  then explicitly SHELVED by the maintainer — plus 2 corrected-but-not-yet-re-reviewed (strtol,
  sqrt) and 1 fully-errored task awaiting a fresh restart (unchecked-index-offset-arithmetic).**
  See §3a for exactly why the 16 got shelved instead of continuing — this is the cycle's
  headline finding, asked for by name in this cycle's commission.
- **A new tool exists as a direct byproduct: `/home/bork/w/vdc/1/makespan-scheduler/`,** a
  standalone, project-agnostic minimum-makespan CP-SAT scheduler for bulk file-editing
  operations, commissioned specifically to replace the ad hoc serial task-queue the 16 shelved
  picom tasks were about to be run through. Built, then hardened through 3 full rounds of the
  split-review (targeted verifier + genuinely blind reviewer) protocol; round 2 caught the same
  defect CLASS recurring after round 1's instance-patch, escalating to a class-level fix; round
  3 (in flight as of row 265) found one more narrow issue. See §7.
- **Two more ent-sourced findings were independently harvested into served autoharn artifacts,
  same-day, since cycle-003:** `design/ORCH-FINDING-ATOMIZATION-RECIPE.md` (commit `54f30bd`,
  2026-07-13 23:15:29+02) serves ent's atomize-before-classify method (ledger row 91 +
  `FINDING-ATOMIZATION.md`); `engine/verification_stats_edb.py` /
  `engine/verification_stats_audit.py` / `engine/lp/verification_stats.lp` (commit `d13ad29`,
  2026-07-13 22:24:27+02) serve ent's structured verification-verdict evidence convention
  (ledger row 102). Neither harvest was done by this observatory cycle — both landed on `next`
  before this report was drafted, found here by inspecting the worktree's own base. See §7.
- **Gate journals**: `change_gate` 1 → 89 entries (was completely dormant for 3 cycles; now 74
  allowed, 11 denied, 4 `boundary` test-run/commit events — see §2 for the new `bash_write` deny
  kind). `stop_clean_exit` 28 → 42 entries (breaker climbed uninterrupted from `count:14`
  (cycle-003's high, 18:10:35Z) straight through to `count:28` at 22:08:47Z on the SAME unchanged
  17-item debt set — no reset, even though 4 fix-class work items opened and closed inside this
  same window; see §2 for why that's a mechanistic refinement, not a contradiction, of cycle-002's
  signature-keyed-reset finding). `mutation_observer` 3 → 5 (+2, a third distinct trigger class:
  build-system configuration artifacts). `verify_commission` 2 → 6 (+4, still all UNSIGNED,
  expected-configuration, unchanged verdict). `apparatus_flip` unchanged (1). `read_observer` 350
  → 963 (+613). `bash_completions`/`invocations` 535/465 → 1960/1920 (+1425/+1455) — still
  time-boxed, not mined line-by-line. **Two mechanisms this cycle examined for the first time
  though present in earlier windows too:** `delegation_observer.journal.jsonl` (`observe` mode,
  logs every Agent/Workflow dispatch+return with a prompt hash and duration — populated since at
  least 17:15Z on 2026-07-13, i.e. within cycle-002/003's own windows, but never enumerated in
  their gate tables) and `doc_shapes_gate.exercised.jsonl` (`observe` mode, 19 entries, all
  `clean` — memory-file and README writes, harmless). `delegation_observer` is the mechanism that
  made §3a's quantitative claim possible; it is worth a permanent line in this table going
  forward.
- **Config/provisioning**: `governed_files.json` and `.claude/apparatus.json` mode settings
  byte-identical to cycles 001-003 (`change_gate`/`permit_to_work`/`decomposition_review`/
  `stamp_intercept`/`clean_exit` all `enforce`; `mutation_observer`/`delegation_observer`/
  `doc_shapes_gate`/`read_observer`/`bash_completion` all `observe`; `demurral_detect`/
  `doc_legibility_critic`/`doc_attestation` all `off`) — no drift.
- **`distance-to-clean`**: TOTAL debt 0 (review-gap 0, question-status 0/0, work-violations 0) —
  clean, same as all prior cycles.

## 1. SNAPSHOT

- Observed at: 2026-07-13T23:45Z / 2026-07-14 01:45 local (autoharn worktree base: `54f30bd` on
  local `next`, which is itself ahead of `origin/next` at `91a06b9` — confirmed via `git
  rev-parse next origin/next`; this cycle's worktree branches from the local, more current ref).
- ent ledger: 265 rows total (max id observed = 265; `led show 266` REFUSED with "no ledger row
  with id=266"). 0 rows in `review-gap`, 0 in `question-status`, 0 `work violations` —
  `distance-to-clean` reads TOTAL debt 0, same clean state as all three prior cycles.
- picom git: `master` still pristine at `40fac30`. `hardening` branch (sole worktree, checked
  out, `git status` clean modulo one untracked build artifact `subprojects/.wraplock`) now has 4
  real commits past the `2dc21884` upstream anchor: `905db9f` / `9ef2d6f` / `4db9df5` /
  `6582334`. All 7 of the original 93-finding backlog's P0 findings are shipped.
- Audit-cycle phase: cycle-1a (FIND) remains complete and unchanged (93 findings). Cycle-1b's
  Phase 2/3 Workflow (task `wkbwg3cz8`, launched row 89, relaunched after the row-90 crash-fix)
  ran to completion this cycle: ~2.8 hours wall-clock, 100 agents, ~4.76M subagent tokens (row
  132). Result: 19/23 tasks approved (reviewed patches, not yet applied), 3 unresolved at the
  3-round iteration cap, 1 fully errored (StructuredOutput retry cap exceeded, zero result:
  `unchecked-index-offset-arithmetic`). Of the 19 approved (later 20, after a redo — see below):
  4 P0-bearing tasks were applied and shipped this cycle (commits above); the remaining 16
  approved P1-P3 tasks were queued for the same one-task-at-a-time apply pipeline, then
  explicitly SHELVED by the maintainer mid-queue (§3a) in favor of building a general scheduler
  tool. 2 further tasks (strtol-strtoul-erange-unchecked, redundant-hot-path-sqrt) were corrected
  after failing their first iteration cap but not yet re-reviewed. The 17 `harden-*` umbrella
  work items from cycle-001 remain OPEN; none CLAIMED or CLOSED — the 23-task taxonomy is a
  distinct, finer decomposition that does not itself close the 17 surface-level items.

## 2. GATE BEHAVIOR

Mechanism firing counts (full contents of each journal, cumulative across all four cycles; new
activity called out):

| journal | entries (c1→c2→c3→c4) | new this cycle |
|---|---|---|
| `change_gate.journal.jsonl` | 1 → 1 → 1 → 89 | **+88: the fix stage's first real gate exercise.** 74 `allowed` (real Edit tool calls against picom source, each citing an `unlocked_by_entry` ledger row), 4 `boundary` (`test-run/commit` — one per shipped task, closing 11/9/13/2 files respectively), 11 `denied`. Deny kinds: 4× `no_open_claimed_work_item` (one repeat of the cycle-001 probe shape, at 21:40:50Z), 1× `needs_entry` (a claimed-but-not-yet-entered file, taught and cleared one attempt later), and **6× a NEW deny kind, `bash_write`**, all clustered 23:01-23:39Z around repeated attempts to write a `commission`-kind ledger row via bash workarounds (a heredoc, a python script, a shell variable) — every attempt denied, no silent workaround succeeded; the eventual successful path used the disclosed `"(vicarious transcription by the implementer; carries no commissioner guarantee)"` convention already visible in every `commission`-kind row this cycle (rows 179, 210, 236). Worth naming for a future cycle: this looks like a working SoD guard against an implementer session impersonating a commissioning principal, not a bug — but this observer did not verify the enforcing hook's source, only the journal's outcome. |
| `stop_clean_exit.journal.jsonl` | 7 → 14 → 28 → 42 | +14: `breaker_fail_open` climbed uninterrupted from `count:14` (18:10:35Z, cycle-003's high) to `count:28` (22:08:47Z) on the unchanged 17-item `harden-*` set — no reset, the highest count observed in this series (2× cycle-003's high-water mark). Notably, 4 fix-class work items opened and closed inside this same window without resetting the counter — see the mechanistic note below. |
| `verify_commission.jsonl` | 2 → 2 → 2 → 6 | +4, all UNSIGNED (23:00:58Z, 23:14:00Z, 23:25:14Z, 23:30:21Z) — same expected-configuration verdict as every prior call this series. |
| `apparatus_flip.journal.jsonl` | 1 → 1 → 1 → 1 | none |
| `mutation_observer.journal.jsonl` | 1 → 3 → 3 → 5 | +2, a **third distinct trigger class**: `meson setup` (build-configure attempt, 19:46:15Z, touching `subprojects/.wraplock`) and a full `meson setup build -Dunittest=true` (20:32:21Z, touching dozens of `build/meson-private/*` and `build/meson-logs/*` artifacts). Both `observe` mode, non-blocking — same lesson as cycles 001-002 (log-churn, git-plumbing), now with a third confirmed incidental-write class (build-system tooling) that any future "diff purity" enforcement would also need to tolerate. |
| `read_observer.journal.jsonl` | 89 → 256 → 350 → 963 | +613, pure telemetry, no denials |
| `bash_completions.jsonl` / `invocations.jsonl` | 158/107 → 442/368 → 535/465 → 1960/1920 | +1425/+1455, still time-boxed, not mined |
| `delegation_observer.journal.jsonl` | *(not tabulated c1-c3)* → 77 lines / 40 dispatch+39 return pairs | Examined for the first time this cycle — see §3a; already `observe`-mode active since ≥17:15Z on 2026-07-13, inside cycle-002/003's own windows. |
| `doc_shapes_gate.exercised.jsonl` | *(not tabulated c1-c3)* → 19 lines, all `clean` | Examined for the first time this cycle — memory-file writes and 2 README writes against the new makespan-scheduler tool, all `observe` mode, harmless. |

**Mechanistic refinement to cycle-002's signature-keyed-reset finding.** Cycle-002 established
that `stop_clean_exit`'s 3-strike counter resets whenever the open-work-item SET changes, not on
a monotonic session clock. This cycle's uninterrupted 14→28 climb, despite 4 fix-class work
items (`fix-narrowing-or-bound-check-elided` etc.) opening and closing inside the same window,
shows the mechanism only re-evaluates the debt signature at the moment a Stop attempt actually
fires — it does not poll the ledger between attempts. Because each fix-task's full open-claim-
apply-close cycle completed faster than the next Stop attempt landed, no Stop hook ever fired
while the temporary 18th item was open, so the breaker never saw the changed signature and never
reset. This refines, not contradicts, cycle-002's finding: the reset is real but requires a Stop
attempt to land inside the narrow window when the signature differs, which is not guaranteed and
apparently did not happen even once across 4 separate work-item lifecycles this cycle.

**Non-deny gate events, for completeness:** `apparatus_flip` fired no new flips. `mutation_observer`
covered above.

## 3. HARNESS FRICTION

- **Stop-hook / wide-decomposition tension: same class, now at 2× the prior high-water mark
  (KNOWN, reconfirmed).** See §2. Not re-filed as new; the "worth a doc line" recommendation
  from cycles 001-003 gets stronger with a fourth independent reconfirmation at a larger scale.
- **New `change_gate` deny kind, `bash_write` — first appearance this series.** 6 occurrences,
  all in a ~38-minute window (23:01-23:39Z) attempting to write a `commission`-kind ledger entry
  through bash workarounds rather than through a genuine second principal. Every attempt was
  denied loudly; no workaround silently succeeded, and the session recovered by using the
  already-established disclosed-vicarious-transcription convention. TAUGHT, not
  refuses-without-teaching. See §2's table entry for detail.
- **A third `mutation_observer` trigger class: build-system tooling (meson configure/setup).**
  Same family as cycles 001-002's already-banked false-positive-generator lesson (tracked
  governance logs, git's own plumbing); now confirmed to also fire on ordinary build-system
  bookkeeping. Still `observe` mode, still harmless. See §2.
- **Fix-stage gate exercise: partially closed after 3 cycles of being the single largest gap.**
  `change_gate` now has 89 real entries where cycles 001-003 combined had 1. This is a genuine,
  positive evidentiary development for the SoD/countersign question cycle-002's LOAD-BEARING
  ANSWER section left UNEXERCISED — but only partially: only the 4 P0-bearing tasks were
  actually applied; 16 further approved tasks were shelved before reaching the gate (§3a), and
  the disclosed-self-review fallback (a registered second-principal id countersigning in a
  genuinely solo session) remains the pattern in use throughout, not a distinct-human/distinct-
  model countersign. This observer does not adjudicate whether that satisfies the SoD
  convention's spirit — flagging the evidence as now existing where before it did not, for
  whoever does that adjudication next.
- **Mid-flight commission augmentation and pivot, absorbed with real friction this time (contrast
  with cycles 001-002's frictionless augmentations).** The maintainer's commission pivot at row
  178 — stop applying the 16 remaining approved fix tasks, build a scheduler tool instead — did
  NOT land as cleanly as cycle-001's backdoor-sweep addition or cycle-002's upstream-anchoring
  requirement. It required the maintainer to interrupt an in-progress checklist twice (rows
  1919-1930 in the transcript), and the orchestrator's own commission-kind ledger writes for the
  new tool needed 6 `bash_write` denials before landing correctly (see above). Recorded as
  friction, not failure: the pivot did land, correctly, inside the same session.

## 3a. SERIAL-DISPATCH OBSERVATION (this cycle's specifically-commissioned question)

**What was asked:** whether the ent session dispatched roughly 16 independent tasks one after
another rather than concurrently, and why — with transcript evidence, classified per the
auditability ruling, flagged as a recommendation candidate for the orchestrator's separate
ADR-0013 crosscheck. Not adjudicated here.

**What the transcript shows, in order, with timestamps (session
`948fb06c-0ffc-4d92-8892-fa2613e649bc`, which stamped every ledger row from 164 onward):**

1. **22:46:28Z-22:48:13Z** — the session builds a 22-item checklist via the built-in
   `TaskCreate`/`TaskUpdate` tool (not a subagent dispatch mechanism; a plan/tracking list).
   Items #1-4 are marked `completed` retroactively, one per already-shipped P0 task. Items
   **#5 through #20 — exactly 16 items** — are each phrased "Ship fix-`<slug>`... Delegate full
   pipeline to subagent," one per remaining approved P1-P3 task. Items #21-22 cover the two
   corrected-but-unreviewed tasks (strtol redo, sqrt retry).
2. **22:48:17.831Z** — `[Request interrupted by user]`, immediately after item #22 is created and
   before any of items #5-22 are actually dispatched to a subagent.
3. **22:49:01.450Z, maintainer, verbatim:** *"Hold on a minute, have you topologically sorted
   (tsort) the tasks? Are you absolutely sure they need to be sequenced, or could possibly some
   be run concurrently? Let's not violate ADR-0013"*
4. **22:58:44.093Z, maintainer, verbatim (a fuller resend of a 22:57:33Z message):** *"Ok, this
   is silly. Leave the fix task set as is for now, and instead build a minimum-makespan scheduler
   for this type of bulk-editing operation; we have ~/w/vdc/venvs/generic which contains
   OR-tools. The goal is to create a minimum makespan schedule given a collection of sets, each
   set of which contains touched files, so that you don't need to sequence 16 approved tasks and
   can instead batch where appropriate (here batch can mean a parallel workflow, which is the
   default for anything that can be parallelized)."*
5. **22:59:48.449Z, assistant:** *"Good call — stepping back from manual task bookkeeping to
   build the actual tool."*

**What the ledger's own prior reasoning says (row 164, ts `2026-07-13T22:38:40Z`, written by a
dispatched subagent BEFORE the maintainer's question, ~10 minutes earlier):** *"CONCURRENCY
NOTE: remaining subagent dispatches are SEQUENTIAL, not parallel -- all share one working
tree/git index/ledger; true parallel apply+commit would race on git state (worktree isolation
was already ruled out earlier for escaping SUBJECT_ROOT governance)."*

**Quantitative corroboration from `delegation_observer.journal.jsonl`** (this deployment's own
Agent/Workflow dispatch+return log, `observe` mode): across the entire session, 40 tracked
dispatches / 39 matched returns. Only ONE pair genuinely overlapped in wall-clock time — the
picom taxonomy's round-3 co-sign pair (verifier 17:42:27Z-17:43:18Z overlapping a "full coverage
cross-check" dispatch at 17:43:09Z), predating this stretch. Every other dispatch — including
all four apply-pipeline tasks that actually ran, AND all three rounds of the makespan-scheduler's
own targeted-verifier + genuinely-blind-reviewer pairs (independent by design; a front-loaded
verifier and a reviewer with zero mention of prior claims do not depend on each other's output)
— ran strictly dispatch-then-wait-for-return before the next dispatch began. The serial pattern
was not confined to the 16 shelved picom tasks; it was the session's general default for
independent work this cycle, with one apparent exception.

**Classification (per the 2026-07-11 auditability ruling — struggling agents are acceptable;
classify, don't editorialize about fixes):** row 164's CONCURRENCY NOTE is a correctly-reasoned
constraint for one specific step — the final apply-and-commit against a single shared git working
tree genuinely cannot be parallelized without either racing git state or reopening the
worktree-isolation-escapes-governance problem cycles 001-002 already closed. But the default that
followed from it — queuing every remaining task, and even independent review pairs with no data
dependency between them, as one-at-a-time full-pipeline dispatches — was adopted without a
visible check of the tasks' actual file-touch-set overlap first. That gap is what the
maintainer's tsort question targets. Classified as **UNEXAMINED-DEFAULT**, maintainer-caught (not
self-caught): the correct narrow constraint (serialize the commit) was silently generalized to
cover strictly more (serialize everything), and nothing in the transcript shows that
generalization being examined before ~16 further dispatches were about to be queued the same
way. Not classified as refuses-without-teaching — nothing here is a refusal, and the correction,
once raised, was accepted and acted on immediately ("Good call"). **Flagged here as a
recommendation candidate for the orchestrator's separate ADR-0013 crosscheck — this observer
takes no position on whether it constitutes a violation, only reports what happened and why, per
this cycle's mandate.**

One further descriptive note, not a verdict either way: the maintainer's own follow-through was
not "go tsort it by hand right now" but "build a reusable tool for this class of problem" — i.e.
the human in the loop also judged live manual dependency analysis not worth doing in the moment,
investing instead in general capability. Worth recording as a data point on how the gap was
actually closed in practice, alongside the classification above.

## 4. STRUGGLE CLASSIFICATION

(per the 2026-07-11 auditability ruling: struggling agents are acceptable; classify, and only
"refuses-without-teaching" is a defect class to fix.)

| moment | class | defect? |
|---|---|---|
| Cycle-1b Phase 2/3 Workflow completes (task `wkbwg3cz8`, 100 agents, ~2.8h, ~4.76M tokens): 19/23 approved, 3 unresolved at cap, 1 fully errored | RECOVERED-FROM-PARTIAL-FAILURE / GOOD-PRACTICE — every outcome traced to its cause (P0 status, blocking defects named exactly) rather than accepted as an opaque summary | no |
| Two interruptions mid-authorized-apply-batch to compose a full status report (fix-narrowing task) | RECURRING-PATTERN, self-caught on the 2nd occurrence, converted into a standing rule (row 158: one-line inline answers during an authorized apply, full reports reserved for completion/genuine blockers) | no |
| Hand-applying dozens of Edit calls directly in the main loop instead of delegating (fix-narrowing, start of fix-unclamped) | MAINTAINER-CAUGHT, corrected via direct question ("is delegating literally impossible?") rather than self-caught; role clarified (row 160) and self-correction landed (row 161: "every subsequent task from here on, no partial-completion exceptions") | no (execution-shape gap, not a harness mechanism defect) |
| Process error: a correction dispatch presupposed prior edits were already applied to the working tree, when cycle-1b's workflow only ever emits reviewed patches, never live edits | TAUGHT — caught by the DISPATCHED SUBAGENT itself, which verified real git state and refused to fabricate a fix against a false precondition (row 136, explicitly ADR-0002-aligned conduct) rather than guessing | no |
| Scoping correction: the Opus-tiering policy's "cycle-2 forward" framing was misapplied by the orchestrator as excluding cycle-1's own tail work | MAINTAINER-CAUGHT-MISREAD, corrected same-session once the maintainer pointed at task SHAPE (not cycle number) as the actual test | no |
| ADR-0012 degraded to a 6-word paraphrase in the fix-stage LAW block; a real sibling defect (x.c NULL-deref) found by a supplementary agent was about to be filed "out-of-scope, not blocking" rather than escalated; the orchestrator's own first answer to the maintainer's question was, by its own later admission, "a much narrower, near-irrelevant substitute question" | MAINTAINER-CAUGHT-MISREAD, twice in the same stretch (rows 139, 142) — a real completeness gap in what the 93-finding backlog covers, closed going forward by a charter fix (row 144: future FIND charters must instruct agents to hunt ADR-0000/0008/0012/0013 violations as first-class findings, not filter post-hoc) | not a harness mechanism defect; a charter/process gap, self-corrected once surfaced |
| Serial full-pipeline dispatch of the 16 remaining approved fix-tasks (and, per delegation_observer, independent review pairs generally) without an examined check of task-touch-set overlap first | **UNEXAMINED-DEFAULT, maintainer-caught — see §3a for full detail and classification** | not adjudicated here; recommendation candidate for the orchestrator's ADR-0013 crosscheck |
| New `change_gate` deny kind `bash_write` fires 6× on bash-workaround attempts to write a `commission`-kind row | TAUGHT — every attempt denied loudly, no silent bypass, correct disclosed-convention path used instead | no |
| makespan-scheduler round-1/2/3 review loop: split-review protocol used correctly throughout; round 2 catches the SAME defect class recurring after round 1's instance-patch and escalates to a class-level fix, self-diagnosed as "ADR-0000 2(a) applied to my own delegation, not more instance-patching" | GOOD-PRACTICE — the exact instance-vs-class discipline the ADR corpus asks for, applied to a brand-new, unrelated codebase without prompting | no |
| makespan-scheduler had no git repo at all despite a pre-existing `.gitignore` and the "files committed to git" house convention; treated as a hazard within reach and fixed (git init + commit) rather than routed around as out-of-scope (row 220) | GOOD-PRACTICE — a small, unprompted instance of exactly the hazard-fix reflex this observatory's own governing instructions ask for, observed operating inside a tangential sub-task | no |
| `stop_clean_exit` climbs from count 14 to count 28 on unchanged debt, uninterrupted despite 4 fix-item open/close cycles inside the window | STRUCTURAL-TENSION, same class as cycles 001-003, now with a mechanistic refinement (see §2) | no |
| `mutation_observer`'s 2 new hits (meson configure/setup) | NOISE-CLASS, same family, third confirmed trigger | not yet — watch if promoted |
| `verify_commission` UNSIGNED ×4 more | EXPECTED-CONFIGURATION, unchanged | no |

No refuses-without-teaching instances found in this cycle's evidence.

## 5. LESSONS FOR AUTOHARN

1. **KNOWN, reconfirmed at 2× the prior scale — the stop-hook/wide-decomposition breaker.** Count
   climbed from 14 to 28 with no reset, refining (not contradicting) cycle-002's signature-keyed-
   reset finding: the breaker only re-checks the debt signature when a Stop attempt actually
   fires, so brief work-item churn between attempts can pass entirely unnoticed. A fourth
   consecutive independent cycle reconfirms the same undocumented gap; the doc-line
   recommendation from cycles 001-003 is now overdue rather than merely "worth it."
2. **NEW — a new `change_gate` deny kind, `bash_write`, appeared for the first time this series.**
   6 occurrences, all denied, all around bash-workaround attempts to write a `commission`-kind
   ledger row. Worth naming so a future cycle recognizes this as an existing, working mechanism
   rather than a fresh anomaly. This observer did not verify the enforcing hook's source, only
   the journal's outcome — the mechanism appears to be a SoD guard against an implementer session
   impersonating a commissioning principal, consistent with the disclosed-vicarious-transcription
   convention already visible in this deployment's `commission`-kind rows.
3. **NEW — a third `mutation_observer` false-positive trigger class: build-system tooling.**
   Cycles 001-002 established tracked-log-churn and git-plumbing as incidental-write classes any
   future "diff purity" enforcement must tolerate. This cycle adds meson configure/setup
   artifacts as a third. Still `observe` mode, still harmless; the accumulating lesson is that
   this class keeps growing new members rather than converging on a fixed enumerable set.
4. **NEW — the fix-stage gate-exercise gap flagged as this series' single largest evidence gap is
   now partially, not fully, closed.** `change_gate` has real activity for the first time (89
   entries, 4 shipped tasks). The SoD/countersign question cycle-002's LOAD-BEARING ANSWER
   section left UNEXERCISED can now draw on real evidence — though only for 4 of 23 tasks, all
   solo-session disclosed-self-review, not a distinct-principal countersign. Whether that
   satisfies the standing convention's spirit is exactly the kind of question this observer is
   asked not to adjudicate; flagged for whoever does.
5. **NEW — the same-day ent-to-recipe harvesting loop cycle-003 first confirmed working (the
   reviewer-briefing split) is now independently reconfirmed twice more.** Two more ent findings
   (atomize-before-classify, structured verification-verdict evidence) became served autoharn
   artifacts the same day they were generated in ent, found already-landed on `next` by this
   cycle rather than needing this cycle to propose them. Three-for-three same-day harvests across
   two cycles is a real signal this loop is working repeatably, not a one-off.
6. **NEW (process observation, transcript-sourced) — the serial-dispatch pattern this cycle was
   specifically asked to investigate.** See §3a in full. Summary for this section only: a
   correctly-reasoned narrow constraint (git-tree commit serialization) was generalized, without
   an examined check, into serializing all independent work — confirmed both by the transcript's
   explicit exchange and by a full-session count of dispatch/return pairs (1 genuine overlap out
   of 40 dispatches). Recommendation candidate for the orchestrator's ADR-0013 crosscheck; not
   adjudicated here.
7. **KNOWN-adjacent, reinforcing evidence — verify-chain "cannot verify" family.** 4 more
   UNSIGNED verdicts this cycle, same expected-configuration reading as every prior cycle. Not
   re-filed as new.

## 6. CYCLE NARRATIVE

Between the cycle-003 snapshot (2026-07-13T20:20Z) and this one (2026-07-13T23:45Z, session
still live), the ent deployment finished cycle-1b's real Phase 2/3 Workflow — 100 agents over
roughly 2.8 hours, ~4.76M subagent tokens — landing 19 of 23 taxonomy tasks in reviewed-but-
unapplied state, 3 unresolved at the iteration cap, and 1 fully errored. A forward-design decision
(atomize findings into 1..N atomic units with provenance edges before taxonomy construction, so
coverage/exclusivity becomes a mechanical set check instead of a recurring adversarial sweep) was
banked for the next cycle and, separately from this observatory, already harvested into
`design/ORCH-FINDING-ATOMIZATION-RECIPE.md` the same day. A new structured-evidence convention
for tracking review verdicts (`verdict=...;role=...;workflow=...;round=...;task=...` inside the
existing `--evidence` field, no schema change) was adopted and likewise already harvested into
the engine's ASP layer the same day.

The apply phase then began: the first task (`fix-narrowing-or-bound-check-elided`, 22 edits, the
P0 xrender heap-overflow among them) was hand-applied directly by the orchestrating session,
interrupted twice mid-batch to compose status reports the maintainer hadn't actually asked for —
a recurrence converted into a standing rule (one-line answers during an authorized apply, full
reports reserved for real stopping points). Landing it produced this cycle's first real commit
(`6582334`) after three cycles of everything sitting as reviewed JSON. Partway through the second
task, the maintainer asked directly whether hand-applying dozens of edits was actually necessary
or just inertia; it wasn't, and every task from there on was delegated whole to a subagent. The
delegated tail of that second task explained, on the record, why the remaining dispatches would
be serial rather than parallel: everything shares one git working tree, index, and ledger, and
running fix-agents in isolated worktrees had already been ruled out in an earlier cycle
specifically because it let them escape governance. Two more tasks shipped the same way
(`4db9df5`, `9ef2d6f`), and a fourth (`905db9f`) closed out all 7 of the original backlog's P0
findings.

Separately, a maintainer Socratic question caught that ADR-0012 — the largest ADR in the corpus —
had quietly degraded to a six-word paraphrase in the fix-stage's LAW block, and that a real
sibling defect a supplementary review agent had incidentally found was about to be filed as
out-of-scope rather than escalated; the orchestrator's own first answer to the actual question
asked was, by its own later admission, a near-irrelevant substitute. Both were corrected on the
record, closing with a charter fix requiring every future FIND-stage dispatch to hunt ADR-0000/
0008/0012/0013 violations as first-class findings rather than filtering for them after the fact.

With all 7 P0s shipped and 16 approved P1-P3 tasks left to apply the same way, the orchestrating
session built a 22-item checklist enumerating every remaining task for one-at-a-time subagent
dispatch. The maintainer interrupted immediately after the checklist was complete to ask whether
the tasks had actually been checked for independence before being queued sequentially, invoking
ADR-0013; rather than resolve that by hand, the maintainer redirected entirely — shelve the 16
tasks as they stand, and build a standalone, project-agnostic minimum-makespan scheduler using
OR-tools CP-SAT that takes each task's touched-file set and computes an optimal batching, so this
class of problem doesn't need re-litigating by hand each time it recurs. See §3a for the full
transcript evidence and classification.

The rest of this cycle's window built and hardened that tool at
`/home/bork/w/vdc/1/makespan-scheduler/`: an initial implementation (11/11 tests), a round-1
review finding 3 concrete instance bugs (fixed, along with an unprompted git-repo hazard fix), a
round-2 review finding the SAME defect class recurring and escalating to a class-level fix (36/36
tests, including a deliberately-unenumerated malformed-input case routed only through the
defense-in-depth net, proving the class genuinely closed rather than just its enumerated
instances), and a round-3 review — in flight as of the last row observed — finding one further
narrow issue (duration values unbounded against CP-SAT's actual representable domain). Throughout,
the tool-building work used the corrected split-review protocol (targeted verifier, then a
genuinely blind reviewer with zero mention of prior claims) that cycle-003 first flagged as a
served method — a second, independent, successful reuse of that exact convention in an unrelated
codebase.

## 7. METHOD CANDIDATES

1. **Reviewer-briefing two-agent split — reused successfully a second time, in an unrelated
   codebase.** Cycle-003 flagged this as already-served (commit `83bb2cd`). This cycle's
   makespan-scheduler review rounds 1-3 apply the identical targeted-verifier + genuinely-blind-
   reviewer split, cleanly, without prompting — evidence the served rule generalizes beyond the
   picom context it was extracted from. No new artifact needed; recorded as reinforcing
   confirmation the harvesting loop targets a genuinely durable shape.
2. **Atomize-before-classify — already served, found landed, not proposed by this cycle.**
   `design/ORCH-FINDING-ATOMIZATION-RECIPE.md`, commit `54f30bd` (2026-07-13 23:15:29+02),
   serving ent ledger row 91 + `FINDING-ATOMIZATION.md`'s two-grain atoms/blocks pipeline
   (atomic units for mechanical coverage/exclusivity checking; blocks, clustered by shared
   invariant, as the actual unit of fix-authorship). Recorded here because this is the evidence
   trail this observatory feeds; the harvest itself happened outside this cycle.
3. **Structured verification-verdict evidence convention — already served, found landed.**
   `engine/verification_stats_edb.py` / `engine/verification_stats_audit.py` /
   `engine/lp/verification_stats.lp`, commit `d13ad29` (2026-07-13 22:24:27+02), serving ent
   ledger row 102's `verdict=...;role=...;workflow=...;round=...;task=...` `--evidence`-field
   convention (no ledger schema change, queryable directly). Same note as above — recorded, not
   proposed.
4. **NEW, not yet served — the minimum-makespan bulk-edit scheduler itself
   (`/home/bork/w/vdc/1/makespan-scheduler/`).** A standalone, project-agnostic CP-SAT tool
   (OR-tools, NoOverlap-per-resource + optional cumulative max_parallel + minimize-makespan
   objective) built specifically to answer the "must these independent fix-tasks really be
   applied one at a time" question §3a documents. Now 3 rounds of class-level adversarial
   hardening deep (round 3 in flight). This looks like a durably-shaped, reusable capability for
   exactly the kind of situation an audit-fix cycle with many independent approved patches keeps
   re-encountering — flagged as a strong candidate for the recipes/tooling corpus. Whether and
   how autoharn's own delegation conventions should actually consume it is a design question for
   later, not adjudicated here.
5. **Candidate, carried forward unchanged from cycle-003 — "co-signature is agreement" /
   iterate-to-approval convention (row 54).** No new evidence either way this cycle; still
   flagged, still not cross-checked against the existing corpus for overlap (time-boxed).
6. **Odd-but-recurring, carried forward unchanged from cycle-003 — the "stall vs. dead" diagnostic
   shape.** No new evidence either way this cycle.

## Confidence note on action-stream and transcript observability

`bash_completions.jsonl` and `invocations.jsonl` remain un-mined line-by-line (time-boxed, as all
three prior cycles); their growth (+1425/+1455 lines) is reported as raw volume only. This
cycle's transcript reads covered all four JSONL files under
`/home/bork/.claude/projects/-home-bork-ent/` — two short early sessions
(`91b52890-...`, 64 lines; `d9835b3f-...`, 71 lines) and two long sessions
(`615b5d05-...`, 2048 lines; `948fb06c-...`, 2052 lines) that share overlapping early content
before diverging — this observer did not establish the exact mechanism linking the two long
sessions (e.g. a resume/compaction event) and does not assert one; only `948fb06c` was used as
the source for §3a's quoted passages and timestamps, cross-checked against ledger `stamp_session`
values (rows 164, 178, 265 all stamp to `948fb06c`, confirming it as the terminal session for
every claim made in that section). §7's METHOD CANDIDATES section is this observer's judgment
call per the STANDING POSTURE decision's own framing; items 2-3 report an already-landed harvest
rather than propose one, and item 4 is flagged, not adjudicated, per this cycle's explicit
mandate not to draft or propose recipes. No ADR-0013/0011/0012 compliance verdict is rendered
anywhere in this report — §3a and §5 item 6 are deliberately confined to fact plus classification,
per this cycle's mandate and per ledger row 571's on-the-record account of what happens when a
report-only dispatch oversteps that line.
