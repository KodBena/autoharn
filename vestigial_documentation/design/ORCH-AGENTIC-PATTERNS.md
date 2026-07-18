# AGENTIC PATTERNS — algorithmic applications of LLMs, and what the harness does for each

Audience: orchestrator (+secondary: maintainer)

(2026-07-09, Fable-authored, session be693afb. Status: DESIGN, for maintainer curation.)

*Editorial note, appended 2026-07-18 (maintainer catch, this file otherwise stands as
declared history): every "today"/"Today" below is deictic to the authoring date above,
2026-07-09 — the zero-context-reader defect ADR-0017 names, anchored here by dated
append rather than retro-edit. Status drift since authoring, recorded not rewritten:
§11's "kernel-anticipated" half has since been BUILT — s40/s41 (principal identity,
bindings, role edges, competence grants) and s45 (standing lifecycle) landed the
durable-role/ephemeral-instance substrate, witnessed to the point of a suspension
structurally halting a workflow wave (ledger row 1661, WC7, 2026-07-18). §11's
assembly wiring — charter, derived per-role brief, inbox view, percolation-by-query —
remains unbuilt as of this note.*

The organizing test for admission: a pattern is *algorithmic* when its termination or verdict
is decided by a mechanism, not by an agent's (or the operator's) sense that it's done. The
harness's role in every entry is the same move: take the part of the pattern that runs on
trust and give it a typed, refusable, queryable home. Several entries are transplants from
the formal-methods/QA lineage (Fagan re-inspection, CEGAR, differential testing,
pre-registration) — the grayhairs' output, operationalized.

Legend: WITNESSED (ran on toy today) · READY (kernel supports it; needs prompt/tooling only)
· BLOCKED (names its blocker) · DESIGN (needs a build).

## 1. Interrogation-to-spec — WITNESSED (mechanism), READY (pattern)
Start fuzzy; the agent interrogates the operator until the task is a spec. The harness makes
the loop's termination *mechanical*: every open unknown is a `question`-kind ledger row; every
operator answer lands as a row with a typed `answers` edge (validated); **the spec is done when
`led question-status` shows zero open questions** — the checker decides termination, not the
agent's eagerness to start coding. Exercised today: ask/answer/status transition all witnessed.
Bonus: the question rows ARE the requirements-elicitation record, permanently.

## 2. Decomposition countersign — WITNESSED (principal path); obligation form BLOCKED on s20
Split the task; an independent agent reviews the split against the original ask and
countersigns each part. Kernel: `review` rows with `regards`, SoD trigger refuses self-signing
(witnessed), distinct principal via `led register-principal` + `LED_ACTOR` (witnessed),
stamp-verified independence in a real toy session (expected, first session is the test). The
stronger form — the reviewer is *obliged* up front (`countersign_obligation`), and
**"decomposition approved" = `review_gap` returns empty** — is the review fix-point made
structural; blocked today by the s15 grants gap (BACKLOG, proposed s20).

## 3. Spec-polish fix-point (two-role) — READY
Author-agent drafts; adversary-agent hunts ambiguity/contradiction; loop until the adversary
returns nothing. Harness upgrades: each objection is a row `regards` the spec entry; each
revision must be a typed `amends` whose `amends_scope` is a VERBATIM quote of the clause it
defeats — the kernel refuses paraphrase (witnessed today), so revisions are forced to name
exactly what they kill. Supersession keeps every draft in the record; `led current` shows the
head. Termination: adversary files zero new rows for K consecutive rounds — the loop-until-dry
criterion, in the ledger rather than in anyone's judgment.

## 4. Blind differential construction — DESIGN (the engine's own idiom, generalized)
The marriage differential's move (two independent producers, exact-agreement verdict) applied
to authoring: two agents, isolated contexts, both derive FROM THE SPEC ONLY — one writes the
implementation, the other writes the tests (or both write implementations). Divergence is not
a bug count, it is an *ambiguity detector aimed at the spec* — each divergence feeds pattern 3
as an objection row. This is CEGAR's counterexample loop with the spec as the abstraction.
Harness: verdict vocabulary exists (AGREE/DIVERGE_*); needs a small driver instrument.

## 5. Pre-registered acceptance — READY (discipline exists in chocofarm; ledger carries it)
Before implementation starts, the acceptance criterion is registered as a ledger row (what
will be measured, what bins count as pass/fail — chocofarm's `tlab_prereg` discipline). The
completion claim later must be a row that `enacts`/`regards` the pre-registration, carrying
`evidence`. Forecloses the moved goalpost: "done" is evaluated against a criterion that
predates the work, and the timestamp order is kernel-enforced (answers/enacts must resolve to
EARLIER rows — witnessed today). The QEUBO smoke test's "record command/seed/optimum/reached"
instruction was this pattern by hand.

## 6. Ledger-bootstrapped sessions (T_now as the handoff) — DESIGN, high value
Replace prose HANDOFF.md with a query: a fresh session (or post-compaction context) bootstraps
by asking the engine what is IN FORCE now — `ledger_tnow`'s supersession/defeat closure is
literally "what should a fresh agent believe," computed defeasibly, not narrated. Prose
handoffs decay and lie (today's HANDOFF said "wire the hooks"; the ledger knows what was
decided, amended, defeated, and still open). Needs: `judge --bootstrap` emitting in-force
decisions + open questions + open obligations as the session preamble. This is the deductive
layer earning its keep on pure ergonomics — and it makes the Opus-readiness story stronger:
the orchestrator's context is *derived*, not curated.

## 7. Staged escalation on gate refusal — READY (quota-native)
Cheapest model first (Haiku executor); a gate refusal or review objection escalates one tier
(Sonnet), a second consecutive failure escalates the *question* (not the task) to the
maintainer/Fable. The harness makes this honest: escalation triggers are typed events (deny
journal lines, review rows with objecting verdicts), so "this needed a bigger model" is a
measurable, auditable fact — and quota flows to exactly the steps that demonstrated need.
Directly serves the 40%-quota constraint.

## 8. Out-of-frame justification audit — READY (skill exists; hook DESIGN filed)
Never let a justification self-certify: run the hack-rationalization-detector (or the
BACKLOG-filed Rule-3 demurral hook) on the *justification text*, in a fresh context, with the
mandate as the only shared input. ADR-0013's insight mechanized: the corner-cutter's judgment
is corrupted at exactly the moment it self-assesses, so the assessor must not share its frame.
Ledger tie-in: the audit verdict is a `review` row regards the completion claim — refusals
and passes both banked.

## 9. Enumerated-universe audit — WITNESSED today, name it and keep it
Never audit by sampling; enumerate the universe from the SSOT (all kernel objects, all
resolve() consumers, all close paths), then force a verdict per item: exposed/exercised/dark,
witnessed/refused/UNEXERCISED-with-blocker. Today's capability audit and 9-item exercise both
ran this shape and each found a real kernel defect that sampling would have missed. The
closure-statement amendment (ADR-0000) is the law-side form; the audit table with one verdict
per enumerated row is the practice-side form.

## 10. Fresh-eyes re-read (context-contamination control) — READY
The reviewer who shares the author's context shares the author's blind spots. For any
document/spec/claim: spawn the reviewer WITHOUT the working context (fresh subagent, spec-only
diet), and let the stamp layer prove it — `review_stamp_distinctness` distinguishes
same-invocation from distinct-invocation review mechanically (view witnessed today). "Fresh
eyes" stops being a figure of speech and becomes a checkable property of the review row.

## 11. Ephemeral principals (durable roles, disposable instances) — DESIGN, kernel-anticipated
The org-shaped idea (maintainer, 2026-07-09): per-subtask-orchestrator "CLAUDE.md"s — standing
roles with responsibilities and recommendations — under the constraint that agents restart
rather than run (kv-cache reality). The kernel already draws the load-bearing distinction:
**the principal is durable, the invocation is ephemeral.** `kernel.principal` carries the role
(registered once, witnessed today); stamps carry the instance (session/agent per invocation);
`actor` on every row binds work to the ROLE, not the process. So a role survives restarts as a
QUERY, not a memory: everything this actor decided, what of it is in force, what it is obliged
to review, what questions address its concerns.

Assembly (the pieces exist; the wiring doesn't):
- **Charter** = a static per-role preamble (responsibilities, scope, constraints) — versioned
  as a ledger-referenced artifact (supersession applies; charters get amended with verbatim
  quotes like anything else), never a drifting loose file.
- **Brief** = the dynamic half, DERIVED per instantiation: `judge --bootstrap` (pattern 6)
  filtered to the role — its in-force decisions, its open obligations (`review_gap` WHERE
  obliged_actor = role), open questions in its concerns. The instance context is charter +
  brief, nothing else.
- **Responsibilities** = `countersign_obligation` rows literally assign review duty to a
  principal, self-assignment refused by CHECK; a role's "inbox" is a view (blocked on s20 —
  a third consumer for that delta).
- **Percolation** = no mailboxes. A role communicates by writing typed rows (recommendation =
  a `note`/`decision` naming its concern; objection = a `review` regards the target); the
  receiving role's next bootstrap query picks it up. Information flow is a derived view over
  shared history — the epistemic layer as the org's nervous system, exactly the leverage the
  maintainer suspected.
- **Economics**: restart-not-resume becomes an advantage — every instantiation is fresh-eyes
  (pattern 10) with a minimal derived context, and the stable charter prefix is kv-cache
  friendly ACROSS instantiations of the same role (same preamble → warm cache).

Honest risks: role proliferation (each principal is charter+audit surface — keep the org
small, grow it on demonstrated need); the `concern` vocabulary is coarse for addressing
(design/enactment/process/other) — the work-item layer (AUTOMATION-ENVELOPE gap 2) is the
natural fix; conflicting in-force decisions between roles need an adjudicator — which is
precisely the engine's defeat/T_now machinery, giving the deductive layer a THIRD operational
job (after judge and bootstrap).

## What the harness adds, summarized
Across all ten: (a) **termination decided by views, not vibes** (question_status, review_gap,
loop-until-dry over regards-rows); (b) **identity and independence as data** (principals, SoD
trigger, stamps, distinctness view); (c) **revision forced to name its target** (amends +
verbatim quote); (d) **time-order enforced** (edges resolve to earlier rows only — prereg is
trustworthy); (e) **everything is one queryable history** (append-only, supersession-aware),
so any pattern's transcript is reconstructible and auditable after the fact.

## Suggested first adoptions (cheapest, highest yield)
1. Pattern 1 on the toy restart (costs one paragraph of prompt).
2. Pattern 5 on the QEUBO smoke test (already half-done by hand).
3. Pattern 6 as the next engine increment after the judge wiring lands — it converts the
   deductive layer from "intellectually central" to "operationally indispensable," which is
   the strongest possible answer to any future "is the engine worth its complexity" question.
