# ent observatory — cycle 003

<!-- doc-attest-exempt: point-in-time observatory evidence record, cycle-scoped -->

Commission: autoharn tracker row 372 (work_opened `ent-observatory`, standing series), this
cycle's estimate row 480. STANDING POSTURE amendment on record at row 479 (maintainer,
2026-07-13): from this cycle onward, observers also harvest **METHOD CANDIDATES** — durably-
shaped workflows or plain methods surfaced in ent's record that belong in the served recipes
corpus — including odd-but-recurring shapes that cannot yet be classified ("we may not actually
know what we are looking for" — unclassifiable-but-durable beats classified-and-forgotten). That
is this cycle's new §7. Subject (`/home/bork/ent`) was read-only for this report — never
Written/Edited/bash-mutated; all claims below come from its tracker (`./pickup`, `./led show
<id>`, `./led --recent`), its `.claude/logs/*.journal.jsonl`, and `git -C /home/bork/ent/picom`
read commands. Session transcripts were never read (action-stream-is-evidentiary-basis ruling).

## DIFF-VS-PRIOR (baseline: cycle-002 at row 53 / 18:35Z; cycle-001 lineage noted where relevant)

- **Ledger**: 53 rows → 90 rows (+37, rows 54-90). Zero new `work_opened`/`work_closed` events
  this cycle (`upstream-anchoring`'s open/close at rows 45/51 both predate cycle-002's own
  snapshot — cycle-002 already reported them; nothing new closed since). The 17 `harden-*` items
  remain OPEN, untouched, exactly as in both prior cycles.
- **Gate journals — still zero new `change_gate` activity.** `change_gate.journal.jsonl` is
  unchanged at 1 entry (the cycle-001 probe deny). Zero fix-edits have reached the gate across
  three consecutive cycles now, because — as detailed below — the cycle-1b fix stage has spent
  this entire window on **orchestration-substrate failures**, not on landing patches.
  `stop_clean_exit` 14 → 28 entries (+14: 5 more `breaker_fail_open` on the unchanged 17-item set,
  then the debt-signature reset cycle-002 flagged recurred exactly as predicted — `blocked`
  count 1→2 when `upstream-anchoring` reappeared/disappeared from the entries list around its
  18:00-18:23 open/close window — then a NEW, larger data point: the counter climbed
  uninterrupted from `blocked count:1` (16:31:30) to `breaker_fail_open count:14` (18:10:35) over
  ~1h39m on the unchanged 17-item `harden-*` set, with no further Stop attempts recorded since).
  `mutation_observer`, `verify_commission`, `apparatus_flip`, `read_observer` all unchanged in
  kind from cycle-002 (no new entries in the first three; `read_observer` grew to 350, pure
  volume, not mined).
- **picom git — still zero fix commits.** `hardening` branch, sole worktree, `git status` clean,
  `git log 2dc21884..HEAD` returns nothing: the branch is still exactly the upstream anchor point
  cycle-002 reported. No code has changed under `/home/bork/ent/picom/src` since cycle-001's
  pristine baseline.
- **What actually happened in this +37-row window (the headline):** cycle-1b's fix-execution
  substrate went through a second full redesign cycle. The `wsz8hpjx6` workflow cycle-002 reported
  as "running" turned out to have **stopped at Phase 1 with ~0 sunk** (row 54) — a load-bearing
  correction to cycle-002's own framing, which took the fix workflow's presence at face value.
  From there: (1) a design upgrade making both co-sign gates iterate-to-approval (row 54); (2) a
  Phase-1 stall traced to one Opus agent over-loading a single-shot 189KB-backlog classification
  (row 55), fixed by adding integer indices + a compact view + splitting Phase 1 into two stages;
  (3) two more Opus stalls on the (now much smaller) taxonomy step, diagnosed as a genuine
  reliability pattern — "one clean completed tool call, then total silence... for 5+ minutes" —
  leading to a STANDING RULE retiring the Workflow tool for orchestration in favor of
  in-session emulated Agent calls (row 57); (4) a SCOPED REFINEMENT of that same rule one row
  later in substance (row 73), restoring the real Workflow tool specifically for Phase 2/3's
  large parallel fan-out, on the maintainer's hypothesis that the stall was a lone-heavy-agent
  failure mode, not a Workflow-tool-wide one; (5) the maintainer-relayed METHODOLOGY CORRECTION
  (row 71) — a third-party critique caught that rounds 2-3's co-sign reviewers had been FUSED
  (front-loaded findings + fresh sweep in one prompt), the exact anti-pattern ADR-0014 Rule 3
  warns against — corrected into a two-agent split (targeted verifier + genuinely blind
  reviewer), which converged CLEAN at round 6 (row 87, 23-task taxonomy, 93/93 finding coverage);
  (6) the real (non-emulated) Phase 2/3 Workflow was then launched (row 89) and its first attempt
  crashed in 31ms on an args-parsing bug, caught and fixed defensively (row 90, the last row
  observed) — "this, not any silent hang, is the actual answer... I had not checked for a failure
  notification before reporting it as running," an honest self-correction on the record. As of
  row 90 the fix workflow is being relaunched; zero patches have yet reached `change_gate`.

## 1. SNAPSHOT

- Observed at: 2026-07-13T20:20Z (autoharn worktree base: `e02871d`, fast-forwarded from `next`
  at the start of this task — see STEP 0 in the assigning commission).
- ent ledger: 90 rows total (max id observed = 90; `led show 91` REFUSED with "no ledger row with
  id=91" — confirms 90 is current). 0 rows in `review-gap`, 0 rows in `question-status` at
  observation time — same clean state as both prior cycles.
- picom git: `master` still pristine at `40fac30`. `hardening` branch (sole worktree, checked
  out) still rooted at real upstream `2dc21884` with `git status` clean and zero commits past
  the anchor point — unchanged from cycle-002.
- Audit-cycle phase: cycle-1a (FIND) remains complete (93 findings, unchanged since cycle-002).
  Cycle-1b (FIX) has NOT progressed past taxonomy/split design in three cycles of wall-clock
  time: the fix-execution substrate itself (Workflow tool reliability, co-sign reviewer
  briefing design) has been the entire subject of this window's ledger activity. The
  ADR-0000-driven taxonomy that will drive Phase 2 (architect) + Phase 3 (implement↔review) is
  now finalized and co-signed CLEAN (row 87: `taxonomy_consolidated_v6.json`, 23 tasks, 93/93
  finding coverage, converged over 6 verify rounds). The real Phase-2/3 Workflow was dispatched
  once (row 89, task `wcgh4i0gp`), crashed instantly on an argument-shape bug, was fixed, and is
  being relaunched (row 90) — no architect or implement output exists yet. 17 `harden-*` work
  items remain OPEN; none CLAIMED.

## 2. GATE BEHAVIOR

Mechanism firing counts (full contents of each journal, cumulative across all three cycles; new
activity called out):

| journal | entries (c1→c2→c3) | new this cycle |
|---|---|---|
| `change_gate.journal.jsonl` | 1 → 1 → 1 | none |
| `stop_clean_exit.journal.jsonl` | 7 → 14 → 28 | +14: 5 more `breaker_fail_open` on the unchanged 17-item set (counts 5-9), a `blocked`/reset pair bracketing `upstream-anchoring`'s brief reappearance (counts 1-2, then `breaker_fail_open` 3-4 on the 18-item set), then — after `upstream-anchoring` closed and the set returned to 17 items — ANOTHER full reset-and-climb: `blocked` counts 1-2 (16:31:30-16:31:48) then `breaker_fail_open` counts 3-14 running uninterrupted from 16:31:57 to 18:10:35 (~1h39m), the longest unbroken fail-open run observed this series |
| `verify_commission.jsonl` | 2 → 2 → 2 | none |
| `apparatus_flip.journal.jsonl` | 1 → 1 → 1 | none |
| `mutation_observer.journal.jsonl` | 1 → 3 → 3 | none |
| `read_observer.journal.jsonl` | 89 → 256 → 350 | +94, pure telemetry, no denials |
| `bash_completions.jsonl` / `invocations.jsonl` | 158/107 → 442/368 → 535/465 | +93/+97, no outcome field surfaced, not further mined (time-boxed, as before) |

**Still zero new DENYs of any kind.** The single `change_gate` DENY remains the cycle-001 probe,
never repeated. This is now a 3-cycle-long, ~5h-wall-clock-long stretch with the fix stage never
once reaching the gate — not because the gate is untested, but because the orchestration
substrate feeding it (Workflow-tool stalls, a fused-briefing reviewer defect, a crashing
workflow launch) has consumed the entire window. That is itself the most important gate-behavior
fact this cycle: **the mechanism has nothing new to report because the fix stage has not yet
produced anything for it to gate.**

**A second, larger reset-and-climb of `stop_clean_exit`, confirming cycle-002's mechanism note.**
Cycle-002 discovered the breaker resets on any change to the open-work-item SET, not just on
debt clearing. This cycle shows the same mechanism firing again around `upstream-anchoring`'s
open/close (though that event itself predates this cycle's row window — see DIFF-VS-PRIOR), and
then, on the stable 17-item set, an unbroken climb to `count: 14` — the highest count observed in
this series (prior high was 9). The mechanism still behaves exactly as designed: fails open every
time, journals every instance, teach-text unchanged. What is new is the *scale*: a single
sustained session window pushed the counter three times higher than any prior cycle's high-water
mark, simply because more real wall-clock time passed with the same wide decomposition still
open. See §5 item 2 for why an operator should expect this number to keep climbing, not read it
as escalating danger.

**Non-deny gate events, for completeness:** `verify_commission` fired no new calls (still
2×UNSIGNED, expected-configuration, unchanged). `apparatus_flip` fired no new flips.
`mutation_observer` fired no new flags this cycle (still the 3 entries from cycles 001-002: one
tracked-log-churn hit, two git-plumbing hits).

## 3. HARNESS FRICTION

- **Stop-hook / wide-decomposition tension: same class, new magnitude (KNOWN, reconfirmed at
  larger scale).** See §2 above — count reached 14, the highest yet. No new mechanism detail;
  this is the same structural tension cycles 001-002 named, now with a bigger number attached.
  Not re-filed as new.
- **Workflow-tool substrate: THREE separate reliability incidents this cycle, of at least two
  distinct shapes, which is new and worth its own line.** (a) Two silent hangs on lone,
  heavy-single-shot generation tasks (row 56: the original splitter and a first taxonomy
  redesign, both Opus, both "one clean tool call then total silence, 5+ min, zero error") — a
  genuine stall shape, mechanized per ADR-0011 Rule 2 (2 instances). (b) One near-instant crash
  on the Phase 2/3 launch (row 90) that was *initially going to be reported as another stall* —
  the orchestrator caught itself before doing so: "I had not checked for a failure notification
  before reporting it as running." (a) and (b) present identically from the outside ("the
  workflow isn't producing output") but have opposite causes (a tool genuinely wedged vs. a
  script bug that failed before doing any work) and opposite fixes (retire/reshape the workload
  vs. fix the argument-passing code). This is exactly the kind of durable-but-not-yet-fully-
  classified shape the STANDING POSTURE decision asks observers to flag — see §7.
- **Fused-briefing reviewer defect: caught, corrected, and reconverged inside this ledger window
  — and already served to deployments same-day.** Rounds 2-3's co-sign reviewers were fused
  (front-loaded findings + fresh sweep, one prompt) — the precise anti-pattern ADR-0014 Rule 3
  warns against. A maintainer-relayed third-party critique caught it (row 71); the corrected
  two-agent split (targeted verifier + genuinely blind reviewer) then ran rounds 4-6 to a CLEAN
  convergence (row 87). This is the worked example the STANDING POSTURE decision names verbatim,
  and it is already WITNESSED as served: `git show 83bb2cd` (this repo, 2026-07-13 20:02:35)
  lands a "Briefing your reviewer" section in `design/USER-DOC-AUDIT-LOOP.md` plus a pointer in
  `design/USER-RECIPES-FAQ.md`, citing this exact ent incident by name. See §7 item 1.
- **Fix-stage gate exercise: still unobserved, now across three cycles.** `change_gate` and
  `decomposition_review`'s FIX-stage behavior (claim → `-f` → commit, serialized per row 48's
  design) remains entirely untested by evidence, because zero patches have been applied. This is
  the single largest, longest-standing gap in this series' evidence.

## 4. STRUGGLE CLASSIFICATION

(per the 2026-07-11 auditability ruling: struggling agents are acceptable; classify, and only
"refuses-without-teaching" is a defect class to fix.)

| moment | class | defect? |
|---|---|---|
| `stop_clean_exit` climbs to count 14 on unchanged debt | STRUCTURAL-TENSION, same class as cycles 001-002, larger magnitude only | no |
| Cycle-002's "fix workflow running" framing corrected at row 54 to "stopped at Phase 1, ~0 sunk" | GOOD-PRACTICE — self-correction against its own prior optimistic framing, on the record, before building further on a false premise | no |
| Two Opus stalls on lone heavy-generation tasks (row 56) | RECURRING-RELIABILITY-PATTERN — mechanized per ADR-0011 Rule 2 as 2 instances of one shape; not agent confusion, a tool-load-shape finding | not a harness defect (autoharn side); flagged for the Workflow-tool substrate, see §7 |
| Standing rule retiring Workflow (row 57), then scoped back for large fan-outs one row-window later (row 73) | GOOD-PRACTICE / SELF-CORRECTING-POLICY — a rule was tightened on 3 data points, then correctly narrowed once the maintainer supplied a load-shape hypothesis distinguishing the failure class, rather than over-generalizing from a small sample | no |
| Fused-briefing reviewer anti-pattern (rounds 2-3) | TAUGHT-LATE-BUT-CORRECTED — the defect was not self-caught; an external (maintainer-relayed) critique caught it, and the correction was then executed cleanly and reconverged (rounds 4-6) | no (not a refuses-without-teaching case; the gap was in independent self-review, not in any harness mechanism) |
| Workflow crash misread as "hadn't started" until row 90's explicit check | GOOD-PRACTICE-ON-SECOND-LOOK — the orchestrator initially seems to have been about to report a stall, caught itself, and named the false inference explicitly rather than letting it stand | no |
| `mutation_observer`/`verify_commission`/`apparatus_flip` | unchanged, no new instances | no |

No refuses-without-teaching instances found in this cycle's evidence. No new `change_gate` DENY
of any kind was observed.

## 5. LESSONS FOR AUTOHARN

1. **KNOWN, reconfirmed at larger scale — false-positive-generator class (cycles 001-002).** No
   new `mutation_observer` triggers this cycle; the two known trigger classes (tracked
   governance logs, git's own plumbing) stand unchanged. Not re-filed.
2. **KNOWN, reconfirmed at larger scale — `stop_clean_exit`'s signature-keyed, non-monotonic
   3-strike breaker (cycle-002).** This cycle's count-14 run is the same mechanism cycle-002
   described, just observed for longer. Worth stating plainly for a future reader: **there is no
   upper bound on this counter within a session** — it will keep incrementing for as long as Stop
   keeps firing against unchanged debt, and a large number here is not evidence of anything
   getting worse, only evidence that a wide decomposition has stayed open a long time. An
   operator should not read "count: 14" as 14x more broken than "count: 4." Not re-filed as new,
   but the "worth a doc line" recommendation from cycles 001-002 gets stronger with each cycle
   that reconfirms it — three consecutive independent observations of the same undocumented
   gap is itself a signal this is due for that doc line, not just noted again.
3. **KNOWN-adjacent, reinforcing evidence — verify-chain "cannot verify" family.** No new
   `verify_commission` calls this cycle; unchanged.
4. **NEW — orchestration-substrate failures can fully consume a cycle without ever reaching the
   mechanism the FIND/FIX cycle exists to exercise.** Three cycles and ~5 hours of wall-clock ent
   activity have now passed without a single fix-edit reaching `change_gate`. That is not a
   defect in the gate (it has nothing to gate yet) — but it is a real observability gap for
   *this observatory*: the SoD/countersign question this series exists partly to answer remains
   structurally unanswerable until the fix stage's substrate (Workflow tool reliability, reviewer
   briefing design) stabilizes enough to actually apply a patch. Worth naming so a future cycle
   doesn't quietly treat "still unexercised" as a steady-state fact rather than a a symptom of a
   slower-than-expected ramp.
5. **NEW (process observation, not a harness defect) — "is the fix workflow running" needs the
   same sub-phase-qualifier discipline cycle-002 flagged for "is the audit cycle done."** Cycle-002
   itself, reporting in good faith from the ledger's last row, described the fix workflow as
   "running" (row 53's own words) when in fact — per row 54's later correction — it had already
   stopped at Phase 1 with near-zero work done. This observatory's own report inherited an
   optimistic premise from the subject's self-report once already. Future cycles should treat a
   "workflow running" disposition as unconfirmed until the NEXT row either advances the phase or
   explicitly reports a stall/crash — exactly the caveat cycle-002 raised about "audit complete,"
   now shown to generalize to "workflow running" too.

## 6. CYCLE NARRATIVE

Between the cycle-002 snapshot (2026-07-13T18:35Z) and this one (2026-07-13T20:20Z), the ent
session spent the entire window on the fix stage's execution substrate rather than on landing
any actual hardening fix. The `wsz8hpjx6` fix workflow cycle-002 had reported as "running" turned
out to have stalled at Phase 1 with essentially nothing sunk; the orchestrator corrected that
framing explicitly (row 54) rather than letting cycle-002's optimistic read stand uncorrected.

A redesign made both co-sign gates iterate-to-approval (co-signature is agreement; absent it,
work stays in-flight, capped at 3 rounds, unresolved tasks held rather than applied) and traced
the Phase-1 stall to one Opus agent choking on a 189KB single-shot classification job — the same
overload shape as an earlier audit-agent failure. The fix: integer indices, a compact view, and a
two-stage split so no agent ever classifies all 93 findings in one blob again. Two more silent
Opus stalls on the (now much smaller) taxonomy step followed, leading to a standing rule retiring
the Workflow tool for orchestration in favor of in-session emulated Agent calls — then, one
ledger-row-window later, a scoped refinement restoring the real Workflow tool specifically for
Phase 2/3's large parallel fan-out, on the hypothesis that the failure mode is specific to
lone-heavy-agent loads rather than the tool as a whole.

Separately, a maintainer-relayed third-party critique caught that the taxonomy's co-sign review
rounds 2-3 had fused a front-loaded verifier briefing with a supposedly-fresh independent sweep —
exactly the anti-pattern ADR-0014 Rule 3 warns against. The corrected design (a targeted verifier
plus a genuinely blind second reviewer, run separately) converged cleanly over rounds 4-6, ending
with a co-signed, 93/93-coverage, 23-task taxonomy. That correction has already been served to
deployments same-day, in this very repository (commit `83bb2cd`), as a "Briefing your reviewer"
section citing this incident by name.

With the taxonomy final, the real (non-emulated) Phase 2/3 Workflow was launched — and crashed in
31 milliseconds on an argument-shape bug (the tool passed `args` as a JSON string rather than a
live array, compounded by a script-side field-name mismatch). The orchestrator caught its own
near-miss explicitly: it had been about to report the workflow as silently stalled again, and
instead checked for a failure notification first, found the crash, fixed both bugs defensively,
and relaunched. As of the last row observed (90), no architect or implement output exists yet,
and `change_gate` has recorded no new activity across all three cycles of this series.

## 7. METHOD CANDIDATES (new section per the 2026-07-13 STANDING POSTURE decision, row 479)

1. **Reviewer-briefing two-agent split — already codified, WITNESSED as served.** ent's fused
   verifier/blind-reviewer defect (rounds 2-3, row 71) is the exact worked example the STANDING
   POSTURE decision names. It is not merely a candidate this cycle — it is already landed:
   `design/USER-DOC-AUDIT-LOOP.md` gained a "Briefing your reviewer" section and
   `design/USER-RECIPES-FAQ.md` a pointer entry, both in commit `83bb2cd` (2026-07-13 20:02:35,
   same day as the incident), both A:B:C-attested per that commit's own message. Recorded here
   as the calibration example for what "durably shaped and worth serving" looks like, and to
   confirm the loop this observatory feeds into is actually working: an ent incident became a
   served rule within hours, not a future cycle's backlog item.
2. **Candidate, not yet served — "co-signature is agreement" / iterate-to-approval / held-not-
   applied convention (row 54).** The fix-stage redesign states a clean, generalizable review
   rule: a co-sign gate loops until the reviewer actually APPROVES (capped, here at 3 rounds);
   short of that, the work is IN FLIGHT, never treated as done; and a task that exhausts the cap
   without approval is emitted UNRESOLVED and held, never silently applied. This reads as a
   durably-shaped SoD/review convention independent of this specific fix workflow — worth
   checking against ORCH-CAPABILITIES / the recipes corpus to see whether it is already implied
   elsewhere or is a genuinely new, servable rule. Flagged, not adjudicated: this observer did
   not cross-check the full existing corpus for overlap (time-boxed).
3. **Odd-but-recurring, NOT yet classified — "is it a stall or is it dead" as a distinct
   diagnostic shape from "is it stalled" per se.** This cycle surfaced two Workflow-tool failure
   incidents that present identically from the outside (no output, no error visible) but have
   opposite root causes and opposite correct responses: a genuine multi-minute silent hang on a
   lone heavy-generation agent (row 56, real stall, fixed by reshaping the workload) versus a
   near-instant crash before any work started (row 90, fixed by checking for a failure
   notification the orchestrator hadn't checked for). The STANDING POSTURE decision explicitly
   asks for shapes like this to be flagged even unclassified: the durable lesson may be
   "explicitly distinguish and check-for both hypotheses before reporting either" — a discipline
   an orchestrator invoking any background/async tool (not just Workflow) plausibly needs — but
   this observer does not have enough evidence yet to say whether it's a Workflow-tool-specific
   gotcha, a general async-tool-usage recipe, or a one-off. Recording it now, unclassified,
   rather than letting it pass as "just another stall" alongside the two genuine stalls it
   superficially resembles.

## Confidence note on action-stream observability

Same caveat as cycles 001-002: `bash_completions.jsonl` and `invocations.jsonl` carry no
`outcome` field and were not mined line-by-line (time-boxed, as before); their growth (+93/+97
lines) is reported as raw volume only. The completeness claim in DIFF-VS-PRIOR and §2 above (no
new `change_gate` activity, no new `harden-*` closes) is a claim about `led --recent`/`led show`
and the named journal files, not an independent audit of a side channel this observatory does
not query. §7's METHOD CANDIDATES section is this observer's judgment call, made explicitly on
the evidence cited per item, per the STANDING POSTURE decision's own framing that "what has
lasting shape is a judgment call" — none of the three items above carries a stronger warrant
than what is quoted from the ledger. No session transcripts were read in producing this report.
