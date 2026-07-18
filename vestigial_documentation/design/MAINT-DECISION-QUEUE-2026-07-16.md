# Maintainer decision queue — 2026-07-16

Written for a zero-context reader
([ADR-0017](../../law/adr/0017-the-zero-context-reader.md)): each question below is self-contained —
what it is, why it reached you, the evidence, the options, and a recommendation with
its reasoning. Everything NOT here is already dispatched autonomously per the
decision-queue bar (only load-bearing judgment questions reach you). Answering can be
as short as "1: keep, 2: yes, 3: park, 4: park".

Two recurring terms, glossed once: **the panel** is the `autoharn-panel` deployment
at `~/w/vdc/1/experience/autoharn-panel`, a downstream adoption of this harness run
by a non-Fable orchestrator; a **spy** is a report-only investigation agent sent
into a deployment's session transcripts and ledger to harvest findings (the
"generic spy" cited below is the 2026-07-16 instance of that pattern).

---

## Q1 — Stop-gate circuit breaker: is "fail open after 3 identical debt fingerprints" the posture you want?

**What it is.** `hooks/stop_clean_exit.py` blocks a session from stopping while
governance debt is open, but deliberately allows the stop (loudly) the third time the
*identical* debt fingerprint is seen — an escape valve so a structurally-unclosable
debt (e.g. a review owed to a different principal) cannot trap a session forever.

**Why it reached you.** The panel orchestrator's backflow file
(`/home/bork/w/vdc/1/experience/autoharn-panel/AUTOHARN_BACKFLOW.md`, its
stop-gate circuit-breaker finding — "Finding 5" in that frozen point-in-time
record) flags, correctly, that nothing distinguishes "three good-faith remediation attempts" from
"three bare repeated stop attempts" — the protection can be worn down by repetition
alone. That is a policy property, not a bug: the trade-off is stated honestly in the
hook's own docstring.

**Evidence both ways.** Concern: the bypass is reachable by mere repetition, with no
harder-to-forge signal (elapsed time, distinct-actor attestation, maintainer
override). Reassurance, witnessed by the generic spy: across the panel's sampled
sessions the gate blocked 25+ times under a weaker model and the fail-open was never
reached once — operators resolved genuine debt every time, so normal-path friction
does not push toward gaming.

**Options.**
- (a) Keep as-is; add one docstring sentence naming the posture as deliberate and
  the condition that would reopen the question (a witnessed gaming specimen).
- (b) Harden the third strike: require a distinct signal (e.g. a maintainer-supplied
  override token, or a minimum wall-clock elapsed between identical attempts).

**Recommendation: (a).** No gaming specimen exists; (b) adds ceremony to a path
never yet exercised, and the runs-are-linear ruling's own principle
([CLAUDE.md](../../CLAUDE.md), maintainer-ratified 2026-07-11) applies —
paperwork that is ritual rather than load-bearing gets deleted, not added.

---

## Q2 — Authorize a close-time REFUSAL for consult/audit items without a filed artifact?

**What it is.** Ledger item `consult-close-artifact-gate`: after the panel filing
incident (a commissioned audit closed "shipped" with its only artifact in an
ephemeral /tmp scratchpad, violating the deployment's own standing decision), the
enforcement-side fix is a typed close that REFUSES when a work item declared as a
consult/audit closes without a `--witness` dereferencing to a file under the
deployment's declared filing home.

**Why it reached you.** Everything else dispatched today only adds vocabulary,
views, or teach-text. This one adds a refusal — new friction on the close path —
which is exactly the class your ratification bandwidth is reserved for. It was
deliberately kept out of the ratified
[FABLE-GRADED-DECISIONS-SPEC](../../design/FABLE-GRADED-DECISIONS-SPEC.md) so each could be
judged alone.

**Options.**
- (a) Yes: Fable authors a small spec (declared filing-home obligation on the item,
  close-time dereference check, teach-text), you ratify, Sonnet builds.
- (b) No / not yet: rely on the graded-decisions hook re-injecting the standing
  decision, plus the delegation-observer teach-text improvements already dispatched.

**Recommendation: (a).** The witnessed incident shows prose obligations fail even
when present in context; this is the same lesson that produced the stop-gate. The
scope is one refusal with a narrow, declared trigger — small spec, small build.

---

## Q3 — Reusable orchestration-pipeline primitive: pursue or park?

**What it is.** The generic spy observed you authoring orchestration policy as
per-turn prose (topologically-ordered phases, Opus-drafts/Sonnet-reviews pipelines,
re-scheduling on refactor), and the panel orchestrator hand-building its own
`scripts/cycle-workflow-template.mjs` because no harness primitive exists for
"define a reusable review-then-implement workflow".

**Why it reached you.** Real scope: a first-class primitive is a new operator
surface, not a fix. Wrong to open autonomously.

**Options.** (a) Pursue: Fable authors an exploration spec (what the primitive
would be, what it deliberately is not). (b) Park: record as a known pattern;
deployments keep hand-building, we harvest their shapes via spies until the design
is obvious.

**Recommendation: (b) park for now.** One deployment's specimen is thin evidence
for a primitive's shape; the method-harvesting posture says collect more specimens
first. Reopens automatically the next time a spy finds another hand-built one.

---

## Q4 — Makespan-scheduler/ledger dependency seam: whose problem?

**What it is.** The panel repeatedly hand-corrects makespan-scheduler output using
the ledger's own `work_depends_on` edges, because the external tool reasons about
resource conflicts, not directed precedence. The recurring burden sits at the
boundary; the panel's own fix was a backflow file to the scheduler repo.

**Why it reached you.** Cross-repo ownership is yours to assign; also adjacent to
the earlier faceplant (a panel-session failure of 2026-07-15; the quote is your own wording from the
message in which you commissioned that day's spy, in the orchestrator session of
2026-07-15/16 whose ledgered spy-dispatch decision rows in THIS repo's ledger —
find them via `./led --recent` around rows 1190–1195 — carry the dispatch record)
that you attributed to "guardrails regarding task scheduling with constraints".

**Options.** (a) autoharn absorbs: an export verb emitting precedence edges in the
scheduler's input format. (b) scheduler absorbs: it learns to read precedence
(its repo's concern). (c) Park until the scheduler backflow is triaged.

**Recommendation: (c), leaning (a) later.** An export verb is cheap and keeps each
tool's model honest, but deciding before reading the panel's
`MAKESPAN_SCHEDULER_BACKFLOW.md` (in the panel repo, sibling of the backflow file
Q1 cites) would be authoring blind.
