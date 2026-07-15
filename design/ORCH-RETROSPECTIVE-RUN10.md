# Retrospective: run10 — a process-improvement read of one governed run

Audience: orchestrator

## What this document is

This is a standing retrospective of **run10**, one governed Claude Code session that built a
small web app under this project's ledger governance. A [run](../GLOSSARY.md#run) is one such
session executing a task inside one isolated [world](../GLOSSARY.md#world); run10's world lives
at `/home/bork/w/vdc/1/run10` and is now settled read-only evidence (runs are strictly linear —
a later run makes an earlier one dust). The document was commissioned as an **experiment with
two halves**: (1) what the governed record teaches about improving how these runs are operated,
and (2) what the record turns out to be *unable* to answer — because every unanswerable
retrospective question is itself a finding about the harness, not a gap to paper over.

It is written for the maintainer and for whoever plans **run11**. Each finding below ends in a
concrete, costed recommendation, and every claim carries an evidence pointer: a **ledger row id**
(a numbered row in run10's append-only claim ledger — the `run10.ledger` table), an **invocation
timestamp** (from the world's `.claude/logs/invocations.jsonl`, which logs every Bash call the
session made), a **git commit hash** in run10's own repository, or a **delegation-journal**
timestamp (`.claude/logs/delegation_observer.journal.jsonl`, which records every subagent
dispatch). All times are shown in UTC as the invocation log records them; the ledger's own
`ts` column is two hours ahead (local time), a fact stated once here so the two never look
inconsistent later.

One scope note. A separate concurrent forensic pass is classifying run10's *closure* struggles
in detail — the three refused ledger writes (the gaps at ids 67, 112, 113), the repeated stop
gate, and the countersign rounds at the end. Where this retrospective touches closure it does so
only at the flow-and-delegation level and defers the fingerprint-level mechanics to that pass.

## The run in one paragraph

run10's commission was to build a browser app that tunes a terminal's 16 ANSI colors by
preference-based optimization against a backend service called QEUBO (a preference-Bayesian
optimizer running at `192.168.122.68:8764`): a terminal-transcript preview, an editable
16-swatch palette the user can pin individual colors in, and an A/B preference loop wired to
the backend, plus a single-homed interface doc and a deterministic smoke test. The agent
decomposed the commission into ten ledgered work items up front, had a stamp-distinct reviewer
principal countersign the decomposition, built the artifacts, and shipped them. Wall-clock ran
from `15:33:46Z` to `16:31:07Z` (57 minutes), across 299 Bash invocations and 162 landed ledger
rows. All ten tasks shipped with git or ledger witnesses; the reviewer found one documentation
defect and two real behavioral defects in the delivered app, all three of which were fixed
before the run stopped. The build itself took roughly 22 minutes; the governed closure tail took
roughly 25 — the single most visible fact about the run's shape.

## Finding 1 — Flow: closure cost as much wall-clock as the build

**Phase structure, reconstructed from invocation and ledger timestamps.** The run divides into
four phases:

| Phase | Span (UTC) | Duration | Ledger rows | What happened |
|---|---|---|---|---|
| Intake + decomposition | `15:33:46`–`15:36:41` | ~3 min | 1–21 | ~2.5 min of un-ledgered API discovery (self-flagged in row 1), then the ten-task decomposition burst (rows 2–11) and the matching work-open burst (rows 12–21) |
| Decomposition countersign | `15:37:51`–~`15:44` | ~7 min | 22–62 | reviewer subagent #1 countersigns all ten tasks and runs the antecedent audit |
| Build | ~`15:44`–`16:06:25` | ~22 min | 63–86 | the actual implementation; commits `dd0b99e`, `12e4808`, `a77786c`, `51f3adc` |
| Closure | `16:06`–`16:31:07` | ~25 min | 87–165 | countersign of the closures, first stop (row 143), defect discovery and fix (commit `ee44487`), revised stop (row 156), final countersign passes |

The table's rows are the run's four phases in order; the "Ledger rows" column names the
`run10.ledger` id range each phase produced, so any claim here can be checked against the row
dump. Two measurements make the shape concrete. First, of the 299 invocations, 190 fall in the
second half of the run (minutes 30–60), so the closure tail generated the majority of the
session's tool activity for a minority of its deliverable. Second, **47 of the 299 invocations
(about 16%) simply polled the stop-gate debt view** `./led review-gap`, with the first such poll
at `15:36:47Z` — before any build had started; `question-status` was polled 21 times and
`work violations` 7. The stop gate refuses a "dirty" stop, so the agent repeatedly checked
whether it was clean enough to stop.

**Rework loops** (a subject touched repeatedly with an intervening failure) are all in the
closure phase and all traceable through the ledger's `refs`/`supersedes` edges:

- the `num_init_queries` seed-count decision — decided at row 80, reviewed-and-accepted at row
  102, re-flagged as a defect at rows 136/139/147/150, fixed at row 151 / commit `ee44487`;
- the page-reload-wipes-progress behavior — shipped in commit `a77786c`, flagged at rows
  139/141/142/150, fixed at row 151/154 / commit `ee44487`;
- the dangling forward reference in the interface doc — shipped at row 65 / commit `dd0b99e`,
  flagged at row 122, fixed at row 145 / commit `a60d993`;
- the first stopping statement — written at row 143, judged incomplete at rows 146/147/150,
  rewritten at row 156.

**Recommendation for run11.** The closure tail is where the wall-clock and the frustration went,
and the 47 review-gap polls are its signature: the agent could not cheaply tell, from where it
stood, how far it was from a clean stop. A considered fix is a single "distance-to-clean" verb
(one command that prints the outstanding review-gap / question-status / work-violations counts
and the ids behind them, so one call answers what 47 answered piecemeal) — this holds
auditability constant (it only reads existing debt views) and shortens the compliant path, which
is exactly the ergonomics-without-weakening-audit posture the maintainer's 2026-07-11 priority
ruling permits. The cost is a small verb to build and keep in step with the debt-view schema.
The deeper flow lesson is that **review-triggered rework, not the build, dominated this run's
tail** — see Findings 2 and 4 for why that rework was worth its cost here.

## Finding 2 — Decision quality: the decomposition held; two design decisions did not

**Decisions that held up.** The ten task-declaration rows (2–11) all closed shipped, each with a
witness (rows 64, 65, 69, 73, 76, 81, 82, 83, 86, 117; commits `a3568c9`, `dd0b99e`, `12e4808`,
`a77786c`, `51f3adc`, `a255590`). The pre-registered smoke-test acceptance criterion (row 68)
drove the implementation and was verified passing against its own terms (row 72, distance 0.0085
vs tolerance 0.12). The color parameterization design (row 75) was implemented verbatim, which
the reviewer confirmed by reading the shipped code against the row's own table (row 97).

**Decisions that were amended or reversed.**

- *Over-specification in the decomposition, caught before it cost code.* Two of the ten
  task-decomposition rows (5 and 9) pre-committed design facts that belonged to other tasks
  chartered to own them — row 5 fixed the smoke-test oracle's shape, which was task 3's job to
  pin down; row 9 fixed the color-fixing exclusion mechanism, which was task 5's. The reviewer's
  antecedent audit caught both and filed them as assumption rows 43 and 44; the author amended
  the decomposition at rows 50 and 51 (the first attempt, rows 48/49, malformed the amendment
  flags and had to be superseded — a tooling-usage slip, self-corrected, cost only ledger
  churn). No code was written against the over-specified reading, so the cost was four amendment
  rows and two re-reviews, not rework.

- *A decision that passed its first review and was later reversed.* Row 80 set the backend's
  initial random-query count to a flat 20. It passed its first reviewer pass (row 102 accepted
  it as an honest judgment call). Three later independent passes (rows 136, 139, 147, 150)
  established that a flat 20 actually *regresses* the low-dimensionality case — once the user
  pins enough colors, the vendor default would have been smaller and better — and it was
  superseded by a scaled formula in the fix at row 151 / commit `ee44487`. This is the clearest
  "decision that did not survive contact with scrutiny," and notably it survived the *first*
  review and fell only to later ones.

**Did the ten-task intake survive contact with the work?** Structurally, yes: all ten items
closed one-to-one, none split or merged in the ledger, and two emergent work items were added as
the work revealed them — `reviewer-dispatch` (the eleventh, when delegation itself needed
ledgering) and `fix-reload-and-init-scaling` (the twelfth, for the two defects review found).
Neither emergent item was foreseeable at intake, and the work-item mechanism absorbed both
cleanly. One granularity signal is worth carrying to run11, though: tasks 6, 7, and 8
(terminal-renderer, swatch-list-ui, backend-integration) were claimed in the same second (rows
77–79), closed in the same second (rows 81–83), and all resolve to **one file** (`app/index.html`)
and **one commit** (`a77786c`). They were decomposed finer than the unit in which they were
actually delivered.

**Recommendation for run11.** Two lessons. First, **a decomposition statement should name what a
task delivers, not pre-decide the how that a later task owns** — rows 5 and 9 leaked design
downstream, and only the reviewer's antecedent audit caught it. Consider a one-line intake
convention: a task's decomposition text states its deliverable and its acceptance handle, and
defers any mechanism choice to the task chartered for it. Second, **decompose to the unit of
independent resumption, not below it** — three work items that collapse to one file and one
commit add ledger ceremony without adding resumability, since no successor can pick up
"swatch-list-ui" without also holding "terminal-renderer." Both are policy nudges, not
mechanisms; their cost is only that intake takes slightly more thought, and the first is
partly self-enforcing because the antecedent audit already catches its violations after the
fact.

## Finding 3 — Assumptions: discharged or standing, none violated into rework

run10's assumption rows were all filed by the reviewer principal during the antecedent audit
that the world's preamble mandates (the audit enumerates design facts the artifacts encode with
no antecedent in the task text or the ledger, and files each as its own assumption row). Three
assumptions were filed:

- Rows 43 and 44 flagged the two over-specifications discussed under Finding 2. Both were
  **discharged** by the amendments at rows 50 and 51 before any code depended on them.
- Row 144 recorded that the app's device-local pseudo-identity login (a random username/password
  generated client-side and stored in the browser) was implemented with no antecedent decision.
  This assumption was **left standing** — it was surfaced by name in the final stopping statement
  (row 156) as a reasonable minimal-viable choice, not converted into a decision or a code
  change.

No assumption in run10 was *violated* in a way that cost rework. The two behavioral defects that
did cost rework (Finding 2) were not assumption violations — they were a decision-quality miss
(row 80) and an undisclosed runtime behavior (the reload wipe), both caught by review rather than
by an assumption coming untrue.

**Recommendation for run11.** The antecedent audit earned its place here: it is the mechanism
that turned two silent design leaks (rows 5, 9) and one silent implementation choice (row 144)
into visible, findable rows. Keep it. The one gap it exposes is that a *standing* assumption like
row 144 has no lifecycle — it is filed and then only informally "surfaced" in a stopping row.
If run11 accumulates more standing assumptions, consider whether a stop should be required to
enumerate the still-open ones explicitly, rather than leaving that to the author's judgment
(which failed once here — row 143's first stop omitted several live items and had to be
rewritten). The cost is a modest tightening of the stop discipline, which touches the
closure mechanics the separate forensic pass is already examining.

## Finding 4 — Delegation: review was load-bearing, and it changed the shipped product

The delegation journal records **five** subagent dispatches, all via the `Agent` tool, all to
the `reviewer` [principal](../GLOSSARY.md#principal) (a registered identity distinct from the
author, so its rows are stamp-distinct — attributable to a provably different invocation): at
`15:37:51`, `16:08:07`, `16:15:35`, `16:22:40`, and `16:28:14Z`. Their journal descriptions,
read in order, tell the run's story: "Reviewer principal countersigns decomposition" → "Fast
reviewer countersign to clear stop gate" → "Countersign final ledger row 143" → "Truly final
countersign pass" → "Countersign the last row, 164."

**Was review load-bearing or ceremonial? Load-bearing, demonstrably** — it changed the shipped
artifacts three separate times:

- the antecedent audit (rows 43, 44) forced the two decomposition amendments;
- reviewer row 122 caught the dangling doc reference, producing the fix at commit `a60d993`;
- reviewer rows 136/139/147/150 caught the two app defects, producing the fix at commit
  `ee44487`;
- reviewer rows 146/147 judged the first stopping statement incomplete, producing the rewrite at
  row 156.

The content of those review rows is substantive, not rubber-stamp: row 139, for instance,
traces the exact line in `app/index.html` where `connect()` unconditionally destroys and
recreates the experiment on every page load, and explains why an ordinary tab refresh silently
discards a user's accumulated preferences — a defect no acceptance criterion named, found by
reading the runtime behavior rather than the spec.

The five dispatches also expose the closure regress: each countersign pass wrote review rows,
and each stopping decision created a new row that itself then needed countersigning, so "final"
had to be declared four times. That regress is the closure-mechanics territory the concurrent
forensic pass owns; the delegation-level fact this retrospective records is only that the
*number* of dispatches was driven by the tail, not by the build.

**Recommendation for run11.** The reviewer principal paid for itself here — three product
changes came from it, and the two app defects in particular would have shipped without it. That
is the strongest single argument in this record for keeping the stamp-distinct reviewer in the
loop even when it slows closure. The cost is real and visible (the closure tail), and the honest
framing for run11 is that **review load-bearingness and closure friction are the same phenomenon
seen from two sides** — the reviewer found real defects *because* it kept looking, and it kept
looking *because* the stop gate would not let a dirty state stop. The lever to pull is Finding
1's "distance-to-clean" verb (cheaper polling), not less review.

## Finding 5 — Deliverable versus commission: one disclosed narrowing, no gold-plating

Measured against the ten task statements (rows 2–11), **every task shipped with a witness and
nothing was silently dropped** (closure rows 64, 65, 69, 73, 76, 81, 82, 83, 86, 117). One
deliberate narrowing is on the record: the smoke test (row 68) uses a two-parameter toy
experiment "deliberately decoupled from the product's 16-color parameterization ... so the smoke
test verifies the QEUBO loop's convergence machinery in isolation." This is defensible and was
disclosed and reviewed (row 91), but it means the shipped smoke test does not exercise the actual
16-color experiment — a reader who expects "the smoke test covers the product" should know it
covers the *machinery*, not the product's parameterization.

No gold-plating is visible. The two closure fixes (commit `ee44487`) were repairs to
already-committed code, not new features, and the device-local identity (row 144) is an
implementation choice inside task 8's "register/auth," not scope beyond the commission.

There is, however, a limit on how far this comparison can be trusted, and it is a harness
finding rather than a run10 finding: **the commission itself is not in the governed record.**
The original user brief survives only as paraphrase inside reviewer rows (rows 24, 26, 27, 28,
29, 30 each quote a fragment of it). The comparison above is therefore a diff of the shipped
artifacts against the agent's own *decomposition* of the ask, not against the ask. This is
carried into the could-not-answer list below because it is the most consequential gap the
experiment surfaced.

**Recommendation for the harness.** Capture the commission at intake as a frozen ledger row (or a
committed artifact the decomposition rows reference), so that "deliverable versus commission" can
be checked mechanically against the source, not only against the agent's restatement of it. The
cost is one required row at session start and a small preamble line; the benefit is that the
intake mechanism would ledger the *thing being decomposed*, which today it never does.

## What this record could not answer

Each item below is a retrospective question this record cannot settle, paired with the record-kind
that would settle it. This list is the experiment's second deliverable — a direct harness-improvement
input.

1. **Why the two app defects were introduced — genuine oversight or considered-but-wrong call.**
   The ledger records the decision and its stated rationale (row 80 explains the flat-20 choice)
   but not the cases the author weighed at decision time. UNDECIDABLE whether the low-dimensionality
   regression was overlooked or considered and misjudged. *Needed:* a decision-row field
   enumerating alternatives-considered / cases-checked, so a retrospective can tell an oversight
   from a bad bet.

2. **How the 57 minutes split between model deliberation and tool execution.** The invocation log
   timestamps Bash calls only; the reasoning time between calls is invisible, and non-Bash tool
   calls (Read, Grep, Edit) are not logged at all. The phase durations in Finding 1 are wall-clock
   envelopes, not work-time attributions. *Needed:* turn-level timing (assistant-turn start/end)
   and/or per-phase token accounting.

3. **Whether the reviewer subagents genuinely read independently or paraphrased confidently.**
   The delegation journal records each dispatch (timestamp, prompt hash, prompt excerpt) but not
   the subagent's own process. Because the invocation log captures only Bash, a reviewer that
   inspects files via the Read tool leaves no trace — so review rows that claim "independently
   read app/index.html" (rows 137, 139, 141, 150) are trusted, not witnessed. The *outputs* of
   review are load-bearing (Finding 4), which is strong circumstantial evidence the reads were
   real, but the process is not on the record. *Needed:* per-subagent tool-call attribution — the
   reviewer's own Read/Grep calls tagged to its stamp.

4. **The verbatim commission.** As Finding 5 states, the original brief is absent from the ledger,
   git, and the journals; it survives only as reviewer paraphrase. A true deliverable-versus-ask
   diff cannot be run. *Needed:* the commission captured as a frozen row or artifact at intake
   (the Finding 5 recommendation).

5. **Whether the run was efficient in cost terms.** There is no token or dollar accounting
   anywhere in the record, so "was the 25-minute, 190-invocation closure tail worth it" is
   unanswerable as an efficiency question — only as a correctness one (it found real defects).
   *Needed:* cost/token ledgering per run.

6. **Whether the ten-task granularity matched the user's own mental model.** The record shows the
   decomposition survived contact with the work (Finding 2), but not whether the user would have
   carved the commission the same way. UNDECIDABLE from this record. *Needed:* the user's own task
   breakdown or post-hoc feedback — neither of which the harness currently captures.

## An honest note on the experiment itself

The maintainer's actual question was whether the governed record is sufficient for a
retrospective. For a *process* retrospective, largely yes. The append-only ledger with its
`refs` / `supersedes` / `amends` edges, plus the invocation log and the delegation journal,
reconstruct the run's spine at row-level resolution: the phase structure, the rework loops, the
decisions that held and the ones that fell, the assumptions and their disposition, and the
load-bearingness of review were all answerable from the record alone, with concrete pointers.
The run's own self-flagging discipline helped — rows 1, 45, and 164 each put a process gap on
the record rather than hiding it, which means even some of the run's failures audit cleanly.

Where the record is insufficient, the insufficiency clusters in one place: **the causal,
counterfactual, cost, and subagent-process questions** (the could-not-answer list). None of those
is a fact lost to time; each is a record-kind the harness does not currently produce. The single
most consequential is that the harness ledgers the *decomposition* but never the *source it
decomposes* — so the system can check an agent against its own restatement of the ask, but not
against the ask. For a project whose entire premise is extreme auditability, that the commission
itself goes un-ledgered is the finding this experiment most wants run11's intake to fix.
