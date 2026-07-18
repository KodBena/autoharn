# RETROSPECTIVE-RECIPE — running a process-improvement retrospective on your own project

<!-- doc-attest-exempt: doc-tree relocation mechanical edit (work item doc-tree-reorg-user-guide, ledger row 1620, 2026-07-18) -- relative link path(s) repointed to a sibling file's new location after a git-mv relocation elsewhere in the tree; no prose rewrite, same disposition as the v1.1.2 release-cut's own markers (commit 543a389). Removal condition: strike this marker and run the real A:B:C loop next time this file is touched for content, not just link repair. -->


Audience: adopter

This document answers one question: **how does a project using this harness's ledger
governance learn from its own finished work, in a way the record can back up rather than a
vibe?** It codifies a method exercised twice already inside this repository — two full
retrospectives over two governed builds — into something you can run on a deployment of your
own. It is written for whoever runs, or commissions, a retrospective: a maintainer at a
terminal, or an orchestrating agent handing the job to a fresh executor. It assumes you already
have a ledger-governed [world](../GLOSSARY.md#world) — an append-only decision ledger recording
every act a session took — or a [standing work tracker](USER-WORK-STATUS-OFFERING.md) to
retrospect, and that you can read a git log and a JSONL journal.

The method is not invented here; it is **distilled** from two live exercises —
[design/ORCH-RETROSPECTIVE-RUN10.md](../vestigial_documentation/design/ORCH-RETROSPECTIVE-RUN10.md) and
[design/ORCH-RETROSPECTIVE-RUN11.md](../vestigial_documentation/design/ORCH-RETROSPECTIVE-RUN11.md), retrospectives of two real
governed builds (`run10`, `run11`) — into a reusable recipe, the same relationship
[design/ORCH-ABC-AUDIT-LOOP-RECIPE.md](ORCH-ABC-AUDIT-LOOP-RECIPE.md) has to
[ADR-0017](../law/adr/0017-the-zero-context-reader.md). Every claim below that describes what
those two runs found cites the finding by name in the source document, not by paraphrase alone,
so you can check it.

## 1. What a retrospective is here, and when to run one

A retrospective, in this project, is a **read-only** pass over a governed run's own record —
never a rewrite of the record, never a live intervention in a run still underway — that asks
what the record teaches about doing the *next* run better. There are two tiers, distinguished by
weight and by trigger, both named in the maintainer's own framing of the need: real deployments
have subprojects, and on a fresh project nobody yet knows what they are doing right, so learning
has to attach to the smallest unit that closes, not only to a whole project's end.

### Tier (a) — per-feature-close: a self-reported lessons note

Every time a [work item](../GLOSSARY.md#permit-to-work) closes (a `work_closed` ledger row lands),
the closing agent is exhorted — never gated — to write one more row: a `note` naming what it
learned, in seconds, before moving on. This is a **preamble exhortation, not a gate**: nothing
refuses a close that skips it, and nothing checks the note's content. It exists because most
learning happens at the grain of one feature, and a full retrospective (tier b) is too heavy to
run after every close.

The exact command shape — a `work close` immediately followed by a `note` that cross-references
it by slug (the ledger's free-text `--refs` field already carries mixed conventions such as
`row:<id>` and a bare doc path side by side, per
[`bootstrap/templates/led.tmpl`](../bootstrap/templates/led.tmpl)'s own header comment;
`work:<slug>` extends that same convention to the one antecedent a closing agent always has on
hand without an extra lookup):

```sh
./led work close <slug> shipped --witness <ref>
./led --refs work:<slug> note "LESSON: <what worked, keep> / <what you'd change next time>"
```

A worked example, illustrative rather than a quoted ledger row (no such note is on record for
this item; the shape is what matters):

```sh
./led work close research-ledger-offering shipped --witness commit:9ebb7b8
./led --refs work:research-ledger-offering note "LESSON: bounding the offering (no DDL apply, that stays the maintainer's own act) kept scope honest; would pre-register the scratch-schema naming convention up front instead of improvising it per build."
```

### Tier (b) — per-phase: the full agent pass

Periodically — per phase of work, or after some maintainer-chosen number of closures — a
separate agent runs the **full method** (Section 2) over one settled world's or one project's
whole governed record, producing a standing document like the two this recipe distills from.
This is heavier (a genuine dispatch of a separate agent — Claude Code's own `Agent` tool,
forking a fresh session with no memory of the one that dispatched it — plus evidence gathering
across several journals, and a document that itself goes through the [A:B:C legibility
loop](ORCH-ABC-AUDIT-LOOP-RECIPE.md)) and answers questions tier (a)'s one-line notes cannot: was
the *flow* healthy, did *decisions* hold up, did the *delegation* pay for itself, did the
*deliverable* match the *commission*.

The two tiers are not competitors. Tier (a) is a cheap, continuous trickle of self-reported
signal; tier (b) is the periodic, evidence-backed synthesis — and, per Section 3, tier (b) is
also where tier (a)'s notes and everything else the record shows get read together.

## 2. The full-pass method

### Evidence sources — read-only, all of it

A retrospective never writes to the world or project it is retrospecting; it treats the record
exactly as the project's own [runs-are-strictly-linear
rule](../CLAUDE.md#orchestration--the-standing-delegation-contract-2026-07-09) already treats a
settled world — evidence, not a thing to be patched. The record run10 and run11 both drew from:

- the append-only **ledger** itself (a numbered row per act — decision, assumption, question,
  finding, review, `work_*` — the table every `led` verb reads or writes, attributed to a
  registered [principal](../GLOSSARY.md#principal));
- the **invocation log** (`.claude/logs/invocations.jsonl`), which timestamps every Bash call —
  Bash only; run10's own retrospective named this gap explicitly and it is still not fully
  closed (Section 3);
- the **delegation-observer journal** (`.claude/logs/delegation_observer.journal.jsonl`), which
  timestamps every subagent dispatch;
- the **read-observer journal** (`.claude/logs/read_observer.journal.jsonl`), which timestamps
  every Read-tool call — added between run10 and run11 specifically because run10 could not see
  non-Bash tool use at all;
- the world's own **git log** — commit hashes are a first-class evidence pointer, exactly like a
  row id;
- the **operator verbs**, re-run live during the retrospective itself rather than trusted from
  a prior claim (`./judge`, `./distance-to-clean`, `./audit`, `./pickup` — a retrospective
  re-confirms the end state is what the record says it is, the same discipline this project's
  own "Run-11 first-shift forensics" pass used, a dated BACKLOG.md entry: "independently
  re-confirmed live during this pass").

### The five lenses

Both live retrospectives organize their findings under the same five questions, and this recipe
names them as the standing lens list:

1. **Flow / cycle-time** — how did wall-clock split across phases (intake, decomposition,
   build, closure), and where did rework loops cluster?
2. **Decision quality** — which decisions held up under later scrutiny, which were amended or
   reversed, and did the task decomposition survive contact with the actual work?
3. **Assumptions** — what did the record file as an assumption, and was each one discharged,
   left standing and disclosed, or silently violated into rework?
4. **Delegation** — was a dispatched subagent (a reviewer, most often) load-bearing — did its
   output change the shipped artifact — or ceremonial?
5. **Deliverable versus commission** — does what shipped match what was asked, checked against
   the actual signed ask where one exists (run11's row 1, a `commission`-kind row the
   maintainer signs himself before any agent runs — detailed in Section 3's re-scored-question
   table below, where it closes what run10 called its single most consequential finding: it
   could diff a deliverable only against the agent's own restatement of the ask, never the ask
   itself).

### The evidence-pointer rule

**Every lesson cites a row id, an invocation timestamp, a journal line, or a commit hash, or it
is not a lesson.** Both source retrospectives state this as their own operating rule in their
opening sections, and it is what makes a retrospective checkable rather than a summary a reader
must take on faith: a finding that cannot be traced back to a specific piece of the record does
not go in the document.

### UNDECIDABLE discipline

Where the record genuinely cannot settle a question, the retrospective says so in those terms —
**UNDECIDABLE** — rather than picking the more flattering of two readings. Run10 marked whether
its two shipped defects were oversight or a considered-but-wrong call UNDECIDABLE, and whether
its ten-task granularity matched the user's own mental model UNDECIDABLE; run11's DELEGATION
lens marked whether its clean-shipping review pass reasoned hard or merely opened the files
UNDECIDABLE, calling both readings "live." An UNDECIDABLE verdict is not a shrug — Section 3
shows it is exactly what feeds the ratchet's second output: it is always paired with the kind of
record that would settle it.

### The boundary this recipe does NOT cross: retrospective versus closure forensics

A retrospective is **process-improvement**, not a defect audit of one run's struggle. This
project runs a separate, complementary pass — closure forensics — that classifies each observed
struggle in a run's closure against a three-class rubric, filed as a dated entry titled
"Maintainer priority ruling: auditability outranks agent ergonomics" in this project's own
BACKLOG.md (BACKLOG.md is an append-only journal with no per-entry anchors — find any entry
cited below the same way: search the file for its quoted heading text): **(a) AGENT DEFECT**, **(b)
MECHANISM-REFUSES-WITHOUT-TEACHING**, **(c) LEGITIMATE-REQUIREMENT-BEING-FELT** — only class (b)
produces a change proposal, because the ruling behind the rubric holds that auditability
outranks agent ergonomics: a struggling agent is not by itself evidence a mechanism is wrong.
Both live retrospectives drew this line explicitly and kept to it, in near-identical words: run10
states "a separate concurrent forensic pass is classifying run10's closure struggles in
detail... Where this retrospective touches closure it does so only at the flow-and-delegation
level and defers the fingerprint-level mechanics to that pass"; run11 states the same for its own
companion pass (BACKLOG.md, "Run-11 first-shift forensics"). **A retrospective may notice a
struggle and note its flow-level cost; classifying WHY the struggle happened against the
a/b/c rubric belongs to forensics, not here.** Keeping the two separate is what let each pass
answer its own question cleanly instead of producing one document that did both jobs poorly.

## 3. The ratchet

This is the load-bearing section — the mechanism that makes a *second* retrospective worth more
than the first, rather than a fresh restart. Every retrospective ends with two typed outputs:

- **lessons → mechanisms/conventions.** A finding that generalizes becomes a proposed fix: a new
  verb, a preamble convention, a kernel column — the same shape run10's five findings each
  closed with ("Recommendation for run11").
- **could-not-answer → record-kind candidates.** Every question the record could not settle is
  listed by name, paired with the *record-kind* that would settle it — never left as a bare
  "we don't know."

**The next retrospective's first duty is to re-ask the predecessor's could-not-answer list**
against the newer, richer record — before it opens any of its own five lenses fresh. This is
what makes the second pass a genuine test of the first pass's proposals rather than an unrelated
report.

### The live specimen: run10's six, re-scored by run11

Run10 closed with six could-not-answer questions. Run11 opened its own body with "Part I — The
six re-asked questions," restating each verbatim from run10 and giving it a fresh verdict. The
tally, quoted from run11 (design/ORCH-RETROSPECTIVE-RUN11.md, Part I headings):

| # | Run10's question | Run11's verdict |
|---|---|---|
| Q1 | Why the two app defects arose — oversight or a considered-but-wrong call | **NOW ANSWERABLE** (for the defects that occurred), one named limit |
| Q2 | How wall-clock split between model deliberation and tool execution | **STILL BLOCKED** (narrowed, not answered) |
| Q3 | Whether reviewer subagents read independently or paraphrased confidently | **PARTIALLY** (moved furthest; attribution rests on an inference, not a stamp) |
| Q4 | The verbatim commission, and a true deliverable-versus-ask diff | **NOW ANSWERABLE** |
| Q5 | Whether the run was efficient in cost terms | **STILL BLOCKED** |
| Q6 | Whether the decomposition granularity matched the user's own mental model | **NOW ANSWERABLE** |

Three now answerable, one partial, two still blocked — the table's own tally is the concrete
shape of "the ratchet worked, in part." What separates the three that moved from the two that
did not is exactly what got built in the interval, each addition named at the point in run11
where it closed the gap:

- **the verbatim signed commission** — a `commission`-kind ledger row (`row 1` of run11's
  ledger), written by the `commissioner` [principal](../GLOSSARY.md#principal) — the maintainer's
  own words, signed before any agent existed — closed Q4 outright and, as a side effect, gave
  Q6 something to check the decomposition's grain against;
- **the read-observer journal** (`.claude/logs/read_observer.journal.jsonl`) moved Q3 from
  "trusted, not witnessed" to "PARTIALLY witnessed" — it proved a reviewer's Read calls landed
  inside its own dispatch window, but could not attribute a read to a specific subagent by
  identity, only by timing;
- **declared event times** (`event_declared_ts`, so a ledgered act written after it happened is
  dated honestly rather than narrated as live) closed the honesty gap run10's own self-flagging
  discipline had exposed, feeding the FLOW lens's trustworthiness generally rather than one
  numbered question directly;
- **a decision-alternatives convention** — point 11 of the world's governance preamble
  (`bootstrap/templates/CLAUDE.md.tmpl`, the file every governed world auto-loads at session
  start): a load-bearing decision names what was rejected and why, in the statement — closed
  most of Q1. Run11's decision rows carry explicit rejected-alternatives clauses, and the
  convention visibly governed conduct even under a live operator instruction to rely on it;
- **decomposition-granularity guidance** — the same preamble's point 1, citing run10's own
  Finding 2 by name: decompose to "the unit of independent resumption" — is what run11's Q6
  verdict is actually attributing the improved grain to. Four work items, each mapping to a
  distinct commit, where run10 had three that collapsed into one file and one commit.

Q2 (the deliberation/execution split) and Q5 (cost efficiency) stayed blocked because **nothing
was built to move them** — run11 says so plainly: "The two questions no new record-kind
targeted... are exactly the two that stayed STILL BLOCKED, which is the experiment behaving as
designed rather than a disappointment." That is the ratchet's own honesty check: a question a
retrospective names but nobody builds toward should still be blocked next time, and if it isn't,
something else moved it by accident, worth asking about on its own.

Run11 closes with its own fresh could-not-answer list of six items (its Part III) — the next
retrospective's own first duty, unresolved as of this document.

## 4. Commission-prompt TEMPLATE

The fenced block below is the reusable prompt an orchestrator hands a fresh executor agent to
run the full-pass method (Section 2) against any deployment. It is distilled from what actually
worked across run10 and run11's own commissions — the evidence-pointer rule, the five-lens
frame, the ratchet's re-asking duty, and the doc-attestation obligation the produced document
itself owes under [ADR-0017](../law/adr/0017-the-zero-context-reader.md). Replace every
`{PLACEHOLDER}`.

```
You are running a process-improvement retrospective per design/USER-RETROSPECTIVE-RECIPE.md.
Read that document in full first, and read the predecessor retrospective named below in full
before writing anything — its could-not-answer list is your first duty, not an afterthought.

DEPLOYMENT UNDER REVIEW: {DEPLOYMENT_PATH}
  (e.g. /home/bork/w/vdc/1/run12, or a standing bootstrap/track-work.sh deployment)
LEDGER: {LEDGER_SCHEMA} / {LEDGER_KERNEL_SCHEMA} on {DB_HOST}
PREDECESSOR RETROSPECTIVE (re-ask its could-not-answer list first): {PREDECESSOR_DOC_PATH}
  (omit this line and state so explicitly if this is the first retrospective for this
  deployment — there is then no predecessor list to re-ask)

READ-ONLY BOUNDARY (hard requirement, not a preference): you may run any read-only verb
(./led, ./judge, ./audit, ./distance-to-clean, ./pickup, git log/show/diff, psql SELECT) against
{DEPLOYMENT_PATH}'s own ledger and repository. You may NEVER write a ledger row, edit a file, or
run any mutating command inside {DEPLOYMENT_PATH} itself -- this pass is evidence-gathering, not
intervention. If {DEPLOYMENT_PATH} is a settled/superseded world (a later run exists), treat it
as read-only history by the project's own runs-are-linear rule regardless of this instruction.

METHOD:
1. Re-ask every item on {PREDECESSOR_DOC_PATH}'s could-not-answer list first. For each, give a
   verdict of NOW ANSWERABLE, PARTIALLY, or STILL BLOCKED, quoting the predecessor's question
   verbatim and citing the record-kind (if any) that moved it.
2. Apply the five lenses to the deployment under review: FLOW/cycle-time, DECISION QUALITY,
   ASSUMPTIONS, DELEGATION, DELIVERABLE VERSUS COMMISSION (against the signed commission row
   if one exists; against the agent's own decomposition, disclosed as a weaker comparison, if
   it does not).
3. Every claim you write carries an evidence pointer: a ledger row id, an invocation-log
   timestamp, a journal line, or a git commit hash. A claim with no pointer does not go in the
   document.
4. Where the record cannot settle a question, write UNDECIDABLE and name the record-kind that
   would settle it -- never guess toward the more flattering reading.
5. Do NOT classify closure struggles against the (a) AGENT DEFECT / (b)
   MECHANISM-REFUSES-WITHOUT-TEACHING / (c) LEGITIMATE-REQUIREMENT-BEING-FELT rubric -- that is
   closure forensics, a separate pass, out of scope here. You may note a struggle's flow-level
   cost; you may not adjudicate its cause.
6. Close with two typed outputs: LESSONS -> proposed mechanisms/conventions for the next run,
   and a fresh COULD-NOT-ANSWER list, each item paired with the record-kind that would settle
   it -- this is what the NEXT retrospective re-asks first.

OUTPUT: write the document to {OUTPUT_DOC_PATH} (convention: design/ORCH-RETROSPECTIVE-{RUN_ID}.md,
"Audience: orchestrator" as the second line under the title). Before considering the document
done, run it through the ADR-0017 A:B:C fresh-context audit loop
(design/ORCH-ABC-AUDIT-LOOP-RECIPE.md -- spawn B synchronously, run_in_background: false,
always) and record its attestation via gates/doc_attestation_presence.py per that recipe's
step 6. A retrospective that is itself illegible to a zero-context reader has failed on its own
terms.
```

## 5. Honest limits

A retrospective reads the record; it does not invent what the record lacks. Where a question is
UNDECIDABLE, the document says so and names the missing record-kind — it never fills the gap
with a plausible-sounding guess, and it never edits a settled world to make the record say more
than it does (runs are linear; the world under review is dust the moment a newer run supersedes
it, and evidence is never patched to fit a conclusion).

The tier-(a) self-reported lessons note (Section 1) is deliberately the weakest trust class this
project names: it is the **LAZY-commission trust class** — an attributable claim, carrying the
writing agent's own identity, but no independent witness and no harness guarantee that the
lesson is accurate or even honestly self-critical. This is the same trust class as a LAZY-mode
commission transcription (`bootstrap/templates/CLAUDE.md.tmpl` point 10: an implementer
transcribing an ask vicariously "carries no commissioner guarantee") and the same trust class as
a subagent's self-reported token usage (BACKLOG.md, "Follow-ups commission scope extended":
"no harness guarantee, just a 'hope it's being honest' sort of thing"). A tier-(a) note is worth
exactly what an unverified self-report is worth — a cheap, honestly-labeled signal, not evidence
a tier-(b) retrospective may cite as if it were a witnessed finding. Tier (b)'s full pass is the
instrument that actually checks a claim against the ledger, the journals, and git; tier (a) is
what makes sure there is something on record to check in the first place.

One more limit, drawn directly from this method's own commissioning decision: a lesson's *home*
depends on what it is a lesson about. A finding about the harness itself — this project's
ledger, hooks, and verbs — becomes a proposed **mechanism** (Section 3's ratchet, upstream in
this repository). A finding about the *deployment being retrospected* — a decision this specific
project made, a convention this specific team should adopt — becomes a **convention** recorded
in that deployment's own preamble or documentation, not a change to the harness. A retrospective
that blurs the two either bloats the harness with one project's local habit or leaves a genuine
harness gap undiscovered because it was filed as "just this project's convention."

## 6. Estimate versus actual — cost-estimation retrospectives, never cost policing

This section answers a narrower question than Sections 1–5: given a task carries a pre-execution
cost *estimate* (an `estimate:`-prefixed ledger row, grammar below), what does a retrospective do
with it? The answer is stated up front because it is easy to read this section backward: an
estimate exists so a team can learn whether its own prediction habits are calibrated. It is
**never** a cost-policing mechanism — the maintainer's own invariant, stated twice at
commissioning, on the record in this repository's tracker ledger as work item
`cost-estimation-retro` (run `./led show <id>` or `./led --recent` at the repository root to
read it, the same live-lookup convention [design/ORCH-SPEC-RESOURCE-ACCOUNTING.md](../design/ORCH-SPEC-RESOURCE-ACCOUNTING.md)
and [design/ORCH-SPEC-DECOMPOSITION-POLICY.md](../design/ORCH-SPEC-DECOMPOSITION-POLICY.md) use for their
own commissioning work items) — and nothing below proposes a gate, an audit family, or an exit
code that fails a build over a missed prediction. A missed estimate is retrospective data,
exactly like an UNDECIDABLE finding (Section 2's discipline): the honest disposition, not a
violation to punish.

### The `estimate:` statement grammar

The `estimate:` grammar below is the same sibling-grammar convention as the
[Pillar 1](../GLOSSARY.md#pillar-1) capability registry's `resource:` statement
([design/USER-BLESSED-TABLE-TEMPLATE.md](USER-BLESSED-TABLE-TEMPLATE.md)'s "statement grammars"
section): a `decision`-kind ledger row whose statement carries a prefix, validated at write time
by [`bootstrap/templates/led.tmpl`](../bootstrap/templates/led.tmpl) (its own refusal teach-text
cites this section by name) and read at pickup time by the `ESTIMATES` section of
[`bootstrap/templates/pickup.tmpl`](../bootstrap/templates/pickup.tmpl). This is the ONE
documented home of the grammar — both parsers point back here rather than restating it a second
time, per the single-source-of-truth-per-fact rule Principle 1 states in
[ADR-0012 (compositional and structural hygiene)](../law/adr/0012-compositional-and-structural-hygiene.md).

```
estimate: <TASK-SLUG> | <TOOL-CALLS> | <SUBAGENT-SPAWNS> | <WALL-CLOCK> | <TOKEN-OOM> | <BASIS>
```

The six fields, in order, separated by ` | ` (space-pipe-space):

- **TASK-SLUG** — the task this estimate covers, matching `^[a-z0-9][a-z0-9-]*$` (ideally the
  same slug a later `led work open <slug>` row will use, though the ledger does not enforce that
  link — a statement-prefix convention, not a foreign key).
- **TOOL-CALLS** — predicted tool-call count: a bare non-negative integer (`40`) or an inclusive
  range (`40-60`).
- **SUBAGENT-SPAWNS** — predicted subagent-spawn count, the same integer-or-range grammar as
  TOOL-CALLS (`0`, `1`, `2-4`).
- **WALL-CLOCK** — predicted wall-clock duration: a bare duration (`20m`, `2h`, `1d`) or a range
  (`10m-30m`).
- **TOKEN-OOM** — predicted token order-of-magnitude, one of the closed vocabulary
  `1K | 10K | 100K | 1M | 10M+` — deliberately coarse (an order of magnitude, not a figure)
  because, per the grade boundary below, a token count never earns a precise evidentiary reading
  in this harness, so a precise-looking prediction would promise more than the actuals side can
  ever confirm.
- **BASIS** — free text naming what the prediction is grounded in (a comparable past task, a file
  count times an average, or a plain guess named as one) — never left blank; an estimate with no
  stated basis teaches a retrospective nothing about whether the *reasoning* was sound, only
  whether the *number* happened to land.

Copy-paste example:

```sh
./led decision "estimate: cost-estimation-retro | 40-60 | 0 | 3h-5h | 100K | scoped from resource-accounting-spec stage A, a similarly-sized led.tmpl/pickup.tmpl validator pair plus one doc section and one seen-red fixture"
```

`./pickup` prints every on-record `estimate:` row under its own `### SECTION: ESTIMATES` header,
sorted by TASK-SLUG then ledger row id — the same malformed-flagged, never-silently-dropped
posture the RESOURCES section
([bootstrap/templates/pickup.tmpl](../bootstrap/templates/pickup.tmpl)'s `resources()`)
already keeps for `resource:` rows. Reading that section is where a
retrospective (or anyone) sees what was predicted; it is not itself a comparison against what
happened — that comparison is this section's remaining job.

### The `actual:` statement grammar (added 2026-07-13, tracker item `actual-intake-grammar`)

The `estimate:` grammar above predicts a task's cost *before* execution; `actual:` is its
measured-afterward twin — the same polymorphic six-field shape, the same sibling-grammar
convention as `resource:`/`estimate:` themselves
([design/USER-BLESSED-TABLE-TEMPLATE.md](USER-BLESSED-TABLE-TEMPLATE.md)'s "statement
grammars" section), validated at write time by
[`bootstrap/templates/led.tmpl`](../bootstrap/templates/led.tmpl) and read at pickup time by
the `ESTIMATES` section of [`bootstrap/templates/pickup.tmpl`](../bootstrap/templates/pickup.tmpl)
(which pairs an `actual:` row beside its matching `estimate:` row by shared TASK-SLUG, where
both exist). This is the ONE documented home of the `actual:` grammar — both parsers cite this
subsection by name rather than restating it a second time (ADR-0012 P1).

```
actual: <TASK-SLUG> | <TOOL-CALLS> | <SUBAGENT-SPAWNS> | <WALL-CLOCK> | <TOKENS> | <SOURCE>
```

The six fields, in order, separated by ` | ` (space-pipe-space):

- **TASK-SLUG** — matching `^[a-z0-9][a-z0-9-]*$`, the same rule `estimate:`'s own TASK-SLUG
  uses. A deliberate granularity convention rides this one field: a slug may name a *whole*
  work item, or a *single spawn within it* — e.g. `kr-titration-design-exploration-b-round-2`
  for round 2's B-fork alone. Same grammar, finer instance. This is what makes a per-phase
  question queryable later — for instance, a `question`-kind ledger row filed for later
  answering (a "parking row": a question the ledger records now, with no answer yet, so it is
  not lost before the record that would settle it exists), tracked under the slug
  `abc-wallclock-dominance-maintainer-callback`, asks what share of a task's wall-clock the
  A:B:C attestation loop consumed — answerable only if the loop's own spawns can be
  `actual:`-recorded at their own granularity, not folded into the whole item's one number.
- **TOOL-CALLS** / **SUBAGENT-SPAWNS** — a bare non-negative integer, **never a range**. This
  is the one deliberate divergence from `estimate:`'s matching fields (which accept an N-M
  range, because a prediction is honestly a spread): a measurement is a point, not a range —
  by the time a task has finished, the tool-call and subagent-spawn counts are exact numbers,
  and a range here would launder an actual count back into prediction-shaped uncertainty. This
  field REFUSES an N-M range where `estimate:` accepts one.
- **WALL-CLOCK** — a duration, matching the identical parser `estimate:`'s own WALL-CLOCK field
  uses (`20m`, `2h`, `1d`, and `90s` — the parser already accepts seconds, so this field does
  too, at no extra cost). Kept as the same parser deliberately (including its range form),
  per the "match its parser" instruction this addition was commissioned under, rather than
  introducing a second, subtly-different duration grammar for what is otherwise the same unit.
- **TOKENS** — an exact-ish count with a `K`/`M` suffix (`204K`, `1.2M`) **or** one of the same
  closed OOM-bucket vocabulary `estimate:`'s TOKEN-OOM field uses (`1K | 10K | 100K | 1M | 10M+`)
  — both forms accepted, because a measured actual is sometimes read off a precise-looking
  harness figure and sometimes only an order-of-magnitude self-report. A **bare unsuffixed
  number above 999 is refused** (e.g. `12000`): without a `K`/`M` suffix a number that large is
  ambiguous between "twelve thousand" and a typo, and refusing it is cheaper than guessing. A
  bare unsuffixed number of 999 or below is accepted as-is (an actual token count that small
  needs no suffix to be unambiguous).
- **SOURCE** — non-empty free text stating where the measurement came from (e.g. `"harness
  task-notification duration_ms+subagent_tokens"`, `"orchestrator wall clock"`,
  `"transcript token count"`). **The standing grade, stated here so it cannot be misread, and
  scoped exactly as the "Actuals" subsection immediately below scopes it**: an `actual:` row's
  WALL-CLOCK and TOKENS fields are **harness-sourced and diagnostic-grade, permanently, with no
  sunset clause** — per the action-stream ruling (ledgered 2026-07-13: the harness's guarantees
  rest on the hook-observed action stream only, and no per-invocation token or duration figure
  ever graduates past diagnostic-grade). TOOL-CALLS/SUBAGENT-SPAWNS are the one exception the
  next subsection names: they become genuinely evidentiary once the witnessed-counting
  machinery (Stage B/D) ships, because those two are hook-observed event counts, not token or
  duration figures. Regardless of grade, an `actual:` row is **never for cost policing** — the
  exact same never-police invariant the `estimate:` grammar states above (the maintainer's own
  invariant, stated twice at commissioning) applies to `actual:` **verbatim**: this grammar
  exists so a team can learn whether its own estimation habits are calibrated against what the
  harness later reports, never to audit or penalize a task over its measured cost. `led.tmpl`'s
  intake validator restates the never-policing rule in its own refusal teach-text, exactly as
  `estimate:`'s does.

Copy-paste examples (whole-item and spawn-granularity):

```sh
./led decision "actual: actual-intake-grammar | 47 | 2 | 42m | 210K | harness task-notification duration_ms+subagent_tokens"
./led decision "actual: kr-titration-design-exploration-b-round-2 | 6 | 1 | 8m | 1.2M | orchestrator wall clock plus subagent's own self-reported token usage"
```

`./pickup`'s `ESTIMATES` section pairs an accepted `actual:` row beside the `estimate:` row
sharing its TASK-SLUG (printed directly beneath the matching estimate block); an `actual:` row
whose TASK-SLUG matches no on-record `estimate:` is listed afterward, under its own
unmatched-actuals listing — the same never-silently-dropped, MALFORMED-flagged posture
`resources()`/`estimates()` already keep.

### Actuals — what the harness can honestly witness, and what it cannot yet

Comparing a `TOOL-CALLS`/`SUBAGENT-SPAWNS` estimate to what actually happened is only as sound as
the actuals it is compared against, and the honest state of those actuals — per
[design/ORCH-SPEC-RESOURCE-ACCOUNTING.md](../design/ORCH-SPEC-RESOURCE-ACCOUNTING.md) §5 ("Usage evidence
and the accounting audit") — is a split grade:

- **Witnessed event counts are evidentiary, once the counting machinery exists.** The accounting
  spec routes tool-invocation and subagent-spawn counting through its §8 Stage B (the SQL
  counting floor over the invocation journal and the ledger) and Stage D (a costless
  subagent-spawn observer, mirroring the read/bash-completion observers already in the
  apparatus). **Both are spec'd, not built, as of this writing** — the honest precondition
  stated plainly rather than implied: an estimate can be *ledgered* today (the grammar above),
  but the actuals half of a TOOL-CALLS/SUBAGENT-SPAWNS comparison lands only once those two
  stages ship. Until then, a retrospective comparing such an estimate to reality is doing the
  same manual evidence-pointer work Section 2 already describes for every other lens — walking
  the invocation log and the delegation-observer journal by hand — not reading a built
  comparison surface.
- **Token figures are diagnostic-grade, permanently.** The maintainer's ruling of 2026-07-11
  (restated in the accounting spec §6 as its own hard edge) holds with no sunset clause:
  hook-witnessed *event counts* are evidentiary, but token and money figures never graduate past
  diagnostic-grade — nothing in this harness will ever emit a monetary or precisely-metered-token
  claim with evidentiary standing. A TOKEN-OOM estimate is therefore compared, honestly, only
  against another diagnostic-grade figure (a subagent's self-reported usage, or a session's own
  billing display) — never against a witnessed count, because no such count exists for tokens and
  none is coming. Wall-clock likewise has no dedicated witnessed observer named in the accounting
  spec; a retrospective reads WALL-CLOCK the same informal, timestamp-reading way Section 2's FLOW
  lens already reads cycle-time generally.
- **The comparison inherits its inputs' grade, honestly.** An estimate-vs-actual finding is only
  as strong as its weaker side: a TOOL-CALLS/SUBAGENT-SPAWNS estimate checked against a witnessed
  Stage-B/D count (once built) is a genuinely evidentiary comparison; a TOKEN-OOM or WALL-CLOCK
  estimate checked against anything is, and stays, diagnostic-grade. State which grade a given
  comparison is before drawing a conclusion from it — the same UNDECIDABLE discipline (Section 2)
  applies where the actuals side cannot be produced at all yet.

### The consumption surface — this section, and nowhere else

Per the maintainer's design (tracker item `cost-estimation-retro`), the estimate-vs-actual
comparison lives **here**, in a retrospective, and deliberately nowhere else: there is no audit
family, no gate, and no exit code anywhere in this tree that reads an `estimate:` row and fails a
build, refuses a commit, or flags a work item over a missed prediction. `led.tmpl`'s own validator
(above) refuses only a malformed *shape* — it has no opinion on whether a well-formed prediction
turned out to be right. A retrospective folds the comparison into its existing FLOW and DELEGATION
lenses (Section 2) as an additional evidence pointer, cites the estimate's ledger row id alongside
the actuals' own pointer (an invocation-log line, a journal entry, or — honestly — "no witnessed
count exists yet, Stage B/D unbuilt"), and writes the finding as **retrospective data**: what the
gap teaches about this team's estimation habits, never a verdict on the task that missed its
number. A deployment that wants harder discipline than this — a standing habit of estimating
*before* execution — declares it itself via the `task-policy:` convention's
`estimate-before-execution` SHOULD criterion
([design/ORCH-SPEC-DECOMPOSITION-POLICY.md](../design/ORCH-SPEC-DECOMPOSITION-POLICY.md) §3), the same
escape valve every [blessed](../GLOSSARY.md#blessed)-tier convention in this harness offers: `should`, reviewer-judgment,
declared on the deployment's own ledger — never a `must` this recipe invents on a deployment's
behalf.

## 7. Model attribution — the `outcome:` statement grammar, and reading outcomes by model

This section answers a narrower question than Section 6's cost retrospective: given a dispatched
task closes at a seam, **which model executed it, and what did the seam review find?** — the
maintainer's own framing, verbatim in substance (2026-07-12 ~noon): "track which MODEL executed
each dispatched task and what misses it produced, to answer 'what are the observed capabilities
of the models, across tasks?'". Like `estimate:`/`actual:` above, this is
**RETROSPECTIVE-ONLY**, per the standing never-police invariant restated at Section 6's own
opening — nothing below proposes a gate, an audit family, or an exit code that ranks or penalizes
a model over an observed miss. It is hazard-detection instrumentation, not economizing, per the
maintainer's same-day reiteration of that invariant.

### Two upstream sources this section reads together

An `outcome:` row (grammar below) is only half the picture. The other half is the
**delegation-observer journal** (`.claude/logs/delegation_observer.journal.jsonl`,
`hooks/pretooluse_delegation_observer.py`), which — since work item
`model-attribution-tracking` (`./led work list` shows its row) — journals `tool_input.model` and `tool_input.subagent_type`
verbatim on every subagent dispatch, alongside the session id and prompt fingerprint the module
docstring's CORRELATION FIELD section already documents. **Both fields are
DECLARED-BY-DISPATCHER grade, named honestly**: neither the journal nor an `outcome:` row is
witnessed proof of which model actually served a call — the action stream cannot verify that, only
record what the calling agent's own tool_input said would be used. This is the identical grade
boundary Section 6's "Actuals" subsection already draws for token/duration figures, per the
2026-07-11 evidentiary-basis ruling: diagnostic-grade, permanently, with no sunset clause.

### The `outcome:` statement grammar

A `decision`-kind ledger row whose statement carries the `outcome:` prefix, validated at write
time by [`bootstrap/templates/led.tmpl`](../bootstrap/templates/led.tmpl) (its own refusal
teach-text cites this section by name) — the same sibling-grammar convention as `resource:`/
`estimate:`/`actual:` above and `taxon:`
([design/USER-TAXONOMY-DECLARATION.md](USER-TAXONOMY-DECLARATION.md), that grammar's own home —
this document does not restate it). This is the ONE documented home of the grammar; the
validator transcribes it, never restates it as a second, driftable definition (ADR-0012 P1). An
`outcome:` row is written by the **ORCHESTRATOR**, at each seam close — never by the executing
agent describing its own work, the same posture `review:`/`review-done:`
([design/USER-RECIPES-FAQ.md](USER-RECIPES-FAQ.md)) already keep for the maintainer's own queue.

```
outcome: <TASK-SLUG> | <MODEL> | <SEAM-VERDICT> | <DEFECTS-FOUND-AT-SEAM> | <NOTES>
```

The five fields, in order, separated by ` | ` (space-pipe-space):

- **TASK-SLUG** — matching `^[a-z0-9][a-z0-9-]*$`, the same rule `estimate:`'s own TASK-SLUG
  uses — ideally the same slug a `led work open <slug>` and/or `estimate:` row for the task
  already carries, so a retrospective can join all three on one key (see "Joining the record"
  below). A statement-prefix convention, not a foreign key — the ledger does not enforce the
  link.
- **MODEL** — matching `^[a-zA-Z0-9][a-zA-Z0-9._-]*$` (a bare identifier, e.g. `sonnet`, `opus`,
  `claude-sonnet-4-5`) — no spaces, deliberately, so grouping rows by exact string equality (the
  read surface below) is honest rather than approximate. DECLARED-BY-DISPATCHER grade (see
  above): the orchestrator states which model it dispatched or observed, typically read off the
  delegation-observer journal's own `model` field for the same task's dispatch line.
- **SEAM-VERDICT** — free text, non-empty, stating what the seam review concluded, in the
  orchestrator's own words. No closed vocabulary is imposed here deliberately: this project's own
  seam-progress decisions already use varied phrasing ("DELIVERED", "merge HELD", "QUARANTINED")
  depending on what actually happened, and inventing a taxonomy this grammar would then have to
  police is exactly the over-reach Section 6 warns against for `estimate:`/`actual:`.
- **DEFECTS-FOUND-AT-SEAM** — free text, non-empty — what the seam review found, or an honest `0`
  / `none` when it found nothing. Never left blank: a clean seam is itself a fact worth recording
  (a model with a long run of clean seams is exactly the "observed capability" signal the
  maintainer's ask names), not an absence to omit.
- **NOTES** — free text, non-empty (state `none` if there is nothing to add) — anything else worth
  keeping: a link to the seam-review decision row, a named limitation, a flagged hazard.

Copy-paste example:

```sh
./led decision "outcome: model-attribution-tracking | sonnet | DELIVERED, merge HELD (ent gap) | 0 | all sec-6 items witnessed; hooks/led.tmpl/pickup.tmpl legs built, hooks leg fixture-verified against the toy db"
```

### The read surface — grouping seam outcomes by model

`led.tmpl`'s validator refuses only the intake *shape*; grouping and reading `outcome:` rows by
MODEL is a retrospective's own job (Section 2's evidence-gathering method), deliberately kept off
the live `./pickup` surface the same way the estimate-vs-actual *comparison* (Section 6, "The
consumption surface") is: there is no standing display section, gate, or audit family anywhere in
this tree that ranks models against each other. A tier-(b) full-pass retrospective (Section 1)
reads `outcome:` rows the same way it reads every other prefix convention in this file: pull every
unsuperseded `kind=decision` row matching `statement ~ '^[[:space:]]*outcome:'` from
`ledger_current` (the same view `resources()`/`estimates()`/`taxonomies()` in
[`bootstrap/templates/pickup.tmpl`](../bootstrap/templates/pickup.tmpl) already query), apply the
identical `regexp_replace(statement, '[\n\r]+[ \t]*', ' ', 'g')` newline-normalization every reader
in that file already applies (a paste-reflowed embedded newline must never shred one row into
several), split the five `|`-delimited fields apart **in Python, not in SQL** — parsing a
pipe-delimited free-text field is exactly the fragile work `led.tmpl`'s own validators exist to do
once, correctly, rather than have every reader re-derive its own regex — then group the parsed
rows by the MODEL field in memory: one bucket per distinct model string, each bucket holding its
TASK-SLUG/SEAM-VERDICT/DEFECTS-FOUND-AT-SEAM/NOTES tuples in ledger-row-id order. A malformed
`outcome:` row (wrong field count) is reported, never silently dropped — the same
never-silently-dropped, MALFORMED-flagged posture every prefix-convention reader in this project
already keeps.

**Joining the record**, the two joins the commissioning work item's design (work item
`model-attribution-tracking` — `./led work list` shows its row, whose title carries the full
design captured at asking) names explicitly:

- **join on the s28 parent edge** (`kernel/lineage/s28-work-parent-edge.sql`'s `work_parent`
  column / the `work_item_descendants` view) — an `outcome:` row's TASK-SLUG against
  `work_item_current.slug`, to fold a subagent-round outcome (e.g.
  `kr-titration-design-exploration-b-round-2`, the same finer-granularity convention `actual:`'s
  own TASK-SLUG field documents in Section 6) up into its parent item's own outcome tally;
- **join on `estimate:`/`actual:` by TASK-SLUG** (Section 6) — pairing what was predicted and
  measured for a task beside what model executed it and what the seam found, so a retrospective
  can ask questions Section 6 alone cannot: did a particular model's tasks run over their own
  estimate more often than another's, did a model's clean-seam tasks also land inside their
  wall-clock prediction.

A retrospective states which grade a given cross-tabulation is (DECLARED-BY-DISPATCHER for MODEL,
diagnostic-grade for any WALL-CLOCK/TOKENS it pulls in from a joined `actual:` row — Section 6's
own grade boundary applies unchanged) — the same UNDECIDABLE discipline (Section 2) governs where
the record cannot settle a question about a model's capability, rather than guessing toward the
more flattering reading.

### The consumption surface — retrospective only, same posture as Section 6

Exactly like the estimate-vs-actual comparison, the model-outcome grouping above lives **in a
retrospective**, and deliberately nowhere else: no gate, no audit family, no exit code anywhere in
this tree reads an `outcome:` row and fails a build, blocks a dispatch, or ranks a model. This is
the maintainer's own standing invariant (Section 6, restated here verbatim for the same reason):
an outcome is retrospective data about this team's own observed experience with a model on this
project's tasks — never a verdict this harness enforces on a future dispatch decision.

## Related

- [design/ORCH-SPEC-RESOURCE-ACCOUNTING.md](../design/ORCH-SPEC-RESOURCE-ACCOUNTING.md) — Section 6's
  actuals-grade boundary (witnessed event counts evidentiary once Stages B/D ship; token figures
  diagnostic-grade permanently) is that spec's §5/§6, cited rather than restated.
- [design/ORCH-SPEC-DECOMPOSITION-POLICY.md](../design/ORCH-SPEC-DECOMPOSITION-POLICY.md) — §3's starter
  criteria table carries the `estimate-before-execution` SHOULD criterion Section 6 points a
  deployment at for harder-than-default estimation discipline.
- [design/USER-BLESSED-TABLE-TEMPLATE.md](USER-BLESSED-TABLE-TEMPLATE.md) — the `resource:`
  statement grammar Section 6's `estimate:` grammar is styled as a sibling of.
- [design/ORCH-RETROSPECTIVE-RUN10.md](../vestigial_documentation/design/ORCH-RETROSPECTIVE-RUN10.md) and
  [design/ORCH-RETROSPECTIVE-RUN11.md](../vestigial_documentation/design/ORCH-RETROSPECTIVE-RUN11.md) — the two live exercises
  this recipe distills; every specimen quoted above traces to one of the two.
- [design/ORCH-ABC-AUDIT-LOOP-RECIPE.md](ORCH-ABC-AUDIT-LOOP-RECIPE.md) — the fresh-context
  legibility loop this recipe's own output document, and any retrospective document, must pass
  before it is done.
- [law/adr/0017-the-zero-context-reader.md](../law/adr/0017-the-zero-context-reader.md) — the
  law the A:B:C loop operationalizes.
- BACKLOG.md, **"Maintainer priority ruling: auditability outranks agent ergonomics"** — the
  three-class struggle rubric that closure forensics uses and this recipe deliberately does not.
- BACKLOG.md, **"Run-10 closure audit"** and **"Run-11 first-shift forensics"** — the
  complementary forensics passes, cited above only to draw the boundary this recipe stays
  inside of.
- This project's own decision ledger, row 74 — **"Continuous-improvement input (maintainer,
  2026-07-12, informal)"** — the commissioning decision this recipe discharges: per-feature
  learning tiered by weight, the ratchet named explicitly ("every retrospective ends with
  lessons->mechanisms and could-not-answer->record-kind-candidates"), and the cross-project
  split this document's Section 5 keeps (harness lessons become mechanisms upstream; project
  lessons become conventions in the deployment). Run `./led show 74` to read it verbatim.
- [USER-WORK-STATUS-OFFERING.md](USER-WORK-STATUS-OFFERING.md) — the sibling consumer-facing
  offering this document follows in shape and in its `USER-` naming convention.
- [GLOSSARY.md](../GLOSSARY.md) — `world`, `run`, `principal`, and every other coined term this
  document links on first use.
- [`hooks/pretooluse_delegation_observer.py`](../hooks/pretooluse_delegation_observer.py) —
  Section 7's other upstream source: the dispatch-time journal that carries `tool_input.model` +
  `tool_input.subagent_type` verbatim, DECLARED-BY-DISPATCHER grade, per work item
  `model-attribution-tracking`.
- [`kernel/lineage/s28-work-parent-edge.sql`](../kernel/lineage/s28-work-parent-edge.sql) —
  Section 7's "Joining the record" folds a subagent-round `outcome:` row up to its parent work
  item via this edge.
