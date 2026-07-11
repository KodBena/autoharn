# The A:B:C fresh-context audit loop — an operator/orchestrator recipe

This document answers one question: **when someone finishes writing or editing a
maintainer-facing markdown document in this repository, what do they actually type to run the
fresh-context audit loop that [ADR-0017](../law/adr/0017-the-zero-context-reader.md) requires,
and how do they record that it happened?** It is a recipe, not a restatement of the law — read
[ADR-0017's "The fresh-context audit loop" section](../law/adr/0017-the-zero-context-reader.md#the-fresh-context-audit-loop--the-maintainer-proposed-wiring-2026-07-11)
for the *why*; this document is only the *how*. It is written for whoever is about to run the
loop — a maintainer at a terminal, or an orchestrating agent driving a Sonnet-executor session —
and assumes only that they can already read and write files and invoke Claude Code's `Agent`
tool (or, for a human operator, open a second Claude Code session).

## What A, B, and C are

The loop has three roles, each a distinct invocation, never the same context twice:

- **A** is whoever authored or edited the document. A's session has full context: the task that
  motivated the edit, the conversation that shaped the wording, everything. That context is
  exactly what makes A unable to judge the document's legibility — A cannot "unknow" what A
  already knows, so A's own re-read is not the test (ADR-0017 Rule 1, "the author cannot
  self-certify this test").
- **B** is a fresh-context reviewer: an invocation that has seen **only the document's current
  text and ADR-0017 itself** — never A's conversation, never the task, never the repository's
  other open threads. B applies ADR-0017 Rule 1's test literally: can a reader with none of A's
  context parse every sentence, resolve every reference, understand every table's purpose, and
  learn from the opening what the document is and why it exists?
- **C** repairs whatever B found. C can be A again (the author fixing their own flagged
  passages) or a separate agent; C's context does not need to be fresh, because C is not the one
  passing judgment — C is discharging findings B already made concrete.

## Step by step

1. **A finishes a draft or edit** of a maintainer-facing `.md` file (the scope ADR-0017's own
   "Scope" section names: READMEs, design notes, rulings, briefs, capability and operating
   documents, BACKLOG entries, ADRs — everything except code comments, commit messages, table
   cells, and other telegraphic registers it explicitly exempts).

2. **Spawn B as a genuinely separate invocation.** In this harness, that means the `Agent` tool
   with a prompt that is **self-contained**: paste in the full text of ADR-0017 (or point B at
   `law/adr/0017-the-zero-context-reader.md` and instruct it to read only that file plus the
   document under review — nothing else in the repository, no conversation history) and the full
   text of the document under review. A worked prompt skeleton:

   ```
   You are B in ADR-0017's fresh-context audit loop. You have been given exactly two things:
   the text of ADR-0017 below, and the text of one document under review below. You have no
   other context — not the conversation that produced this document, not the rest of this
   repository, nothing else. Apply Rule 1's test to the document: (a) is every sentence a
   sentence — subjects and verbs present, no bare noun-phrase paragraphs; (b) does every
   referent resolve — a term, artifact, or "the X" either is plain English, is defined here,
   or links to its definition; (c) is every table/list/code block grounded by prose saying what
   it is and why it's here; (d) does the opening state in plain words what the document is, who
   it's for, and what question it answers, before any jargon. Report EITHER a list of findings,
   each with the exact file:line, a verbatim quote, and a one-sentence suggested repair, OR an
   explicit CLEAN verdict naming all four clauses (1a/1b/1c/1d) you checked. A bare "looks fine"
   is not a valid verdict.

   === ADR-0017 ===
   <full text>

   === DOCUMENT UNDER REVIEW (path: <repo-relative path>) ===
   <full text>
   ```

   Running B as a fresh `Agent` invocation (rather than a follow-up turn in A's own session) is
   what makes "provably distinct from A" true by construction here, not merely asserted: a new
   `Agent` call starts with no memory of the conversation that produced the document
   (`Agent` tool's own description: "A new Agent call starts a fresh agent with no memory of
   prior runs, so the prompt must be self-contained").

   **Spawn B synchronously (`run_in_background: false`), always.** This is a hard requirement,
   not a preference: whoever is *running the loop* (A, in the ordinary case) needs B's verdict
   back in the same turn to act on it in step 3 — a background-spawned B completes into a
   message addressed to the ORCHESTRATOR session, not to the subagent that spawned it, because
   completion routing in this harness follows the spawn's own top-level session, not the
   spawning subagent. That routing is sound only when the loop-runner IS the top-level
   (main/orchestrator) session; the moment the A:B:C loop itself runs *inside* a dispatched
   subagent (a common shape — the orchestrator delegates a documentation task to a Sonnet
   executor, and that executor runs its own A:B:C loop before reporting back), a background B's
   completion never reaches the subagent that is waiting on it. Two live instances of exactly
   this ([BACKLOG.md](../BACKLOG.md), entry "A:B:C recipe friction, twice-witnessed",
   2026-07-11): a subagent-run loop's
   background-spawned B tried to `SendMessage` back to `"general-purpose"` — an agent *type*,
   not an address — and failed; both B's recovered only because they happened to also report
   their verdict in their own final output, which the orchestrator (not the spawning subagent)
   picked up and relayed. That recovery is not a mechanism to depend on. The fix is procedural,
   not architectural: run B with `run_in_background: false` so its verdict returns in-band as
   the `Agent` tool's own synchronous result, every time, regardless of which session is
   running the loop.



3. **B returns a verdict.** If CLEAN across all four clauses, skip to step 6. If B lists
   findings, each finding must carry a file:line specimen, a verbatim quote, and a suggested
   repair — ADR-0017's own words: "B's attestation carries per-finding file:line specimens
   with quoted text and a suggested repair, or an explicit clean verdict enumerated against
   the four clauses of Rule 1." A finding with no specimen is not a finding — send it back to
   B, don't record it.

4. **C repairs every finding**, editing the document directly. C does not need to be
   fresh-context — C is executing concrete, already-specified fixes, not making the legibility
   judgment.

5. **B re-reviews the repaired document — this is round 2, the last one.** ADR-0017 caps the
   loop at two B→C rounds: "Two B→C rounds; if B still finds, the document routes upward as a
   non-converging-review-loop — the escalation event the orchestration contract already types —
   rather than grinding a third round." If round 2 comes back CLEAN, go to step 6. If round 2
   still finds defects, **stop** — do not run a third round. Escalate as a
   [non-converging-review-loop](../CLAUDE.md#orchestration--the-standing-delegation-contract-2026-07-09),
   the same typed event this project's orchestration contract already names for other
   non-converging review cycles, and hand the document to a human or a higher-authority
   reviewer. The document still gets its attestation record at step 6 — recording a DEFECT
   verdict with `escalated: true` is not a failure to record, it is the honest record of what
   happened.

6. **Record the attestation.** Write a JSON body (see
   [`gates/doc_attestation_presence.py`](../gates/doc_attestation_presence.py)'s module
   docstring for the exact schema) naming the document, a `b_id` string identifying this round's
   B invocation, one object per round with its verdict and (for DEFECT) findings or (for CLEAN)
   the four checked clauses, and whether the loop escalated. Then run:

   ```
   python3 gates/doc_attestation_presence.py --record <path-to-the-json-body>
   ```

   The tool computes the document's content hash itself from its current on-disk bytes (never
   trusting a caller-supplied hash) and refuses to append anything structurally invalid — a
   malformed record never enters the ledger, so a later commit-time check never has to discover
   the defect itself.

7. **Commit.** `attestations/doc-legibility-attestations.jsonl` (the ledger the record was
   appended to) and the document both go into the same commit. Once
   `gates/doc_attestation_presence.py` is wired into `hooks/pre-commit` (`gates/
   doc_attestation_presence.py`'s own module docstring carries the exact stanza to insert,
   prepared but not yet applied — see that file's "ARMING MODE" section for why), a commit
   touching an in-scope `.md` file with no matching attestation record is refused there; until
   then, running the gate by hand
   (`python3 gates/doc_attestation_presence.py <the changed files>`) before committing is the
   manual form of the same check.

## What this loop costs, stated up front

ADR-0017 names the price rather than letting it arrive as a surprise, in its "Consequences"
section: "roughly two to three times the tokens per documentation change, on session billing."
B's fresh-context read and, when needed, a second B round are real, billed invocations
— the same class of cost as any other `Agent` dispatch, not a hidden background job. There is no
`.claude/apparatus.json` mode switch (each scaffolded world's per-mechanism on/off/observe/enforce
config file, [templated here](../bootstrap/templates/apparatus.json)) for this cost the way there
is for the headless critic (`hooks/doc_legibility_critic.py`): the A:B:C loop is a **workflow** run
by choice each time a document changes, not a hook that fires automatically and could silently
bill an operator who forgot it was on.

## What the loop does not do

- It does not replace [`gates/doc_shapes.py`](../gates/doc_shapes.py) or
  [`gates/link_integrity.py`](../gates/link_integrity.py) — those are
  deterministic, narrow, and free; they run on every commit regardless of whether A:B:C ran.
- It does not make any LLM verdict block a commit. `gates/doc_attestation_presence.py` checks
  only that a structurally valid record exists for the document's exact current content — never
  whether B's content judgment was CLEAN or DEFECT ([BACKLOG.md](../BACKLOG.md), entry "Two
  ratifications (maintainer, 2026-07-11 evening)", ratification 1's sub-question 2: "may any LLM
  verdict ever sit in a BLOCKING path for this discipline? ... NO").
- It is not required for excluded documents: point-in-time records ([BACKLOG.md](../BACKLOG.md)'s
  dated entries), [`judgment/**`](../OPERATING-CARD.md) (declared history — a predecessor era's
  archive, kept for the record but not binding unless a current spec cites it), or a document
  carrying an inline `doc-attest-exempt: <reason>` marker for a case the other two exclusions do
  not cover.

## Related

- [ADR-0017](../law/adr/0017-the-zero-context-reader.md) — the law this recipe operationalizes,
  especially Rule 1 (the test B applies) and "The fresh-context audit loop" section (the design
  this recipe follows step for step).
- [`gates/doc_attestation_presence.py`](../gates/doc_attestation_presence.py) — the record
  schema and the commit-time presence check, in its own module docstring.
- [`hooks/doc_legibility_critic.py`](../hooks/doc_legibility_critic.py) — the lightweight,
  costed, headless alternative transport for the same Rule 1 test; its own module docstring
  states the two transports "want the same briefing, so `CRITIC_PROMPT_TEMPLATE` below is the
  ONE home of it" — this recipe's step 2 prompt skeleton is adapted from that same template.
