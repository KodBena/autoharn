# The A:B:C fresh-context audit loop — an operator/orchestrator recipe

<!-- doc-attest-exempt: doc-tree relocation mechanical edit (work item doc-tree-reorg-user-guide, ledger row 1620, 2026-07-18) -- relative link path(s) repointed to a sibling file's new location after a git-mv relocation elsewhere in the tree; no prose rewrite, same disposition as the v1.1.2 release-cut's own markers (commit 543a389). Removal condition: strike this marker and run the real A:B:C loop next time this file is touched for content, not just link repair. -->


Audience: orchestrator (the title's "operator/orchestrator" names the same reader — a human operator or an orchestrating agent running this recipe)

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

   Before you conclude, walk the NAMED DEFECT CATALOGUE below (a growing, dated list of defect
   shapes two independent fresh Bs missed on a live document) and dispose of each entry
   explicitly against this document — either "not present" or a finding in the required shape.
   Print your verdict as your FINAL MESSAGE — do not use SendMessage to report it.

   === NAMED DEFECT CATALOGUE (see this recipe's own "Named defect catalogue" section) ===
   <catalogue text — see below>

   === ADR-0017 ===
   <full text>

   === DOCUMENT UNDER REVIEW (path: <repo-relative path>) ===
   <full text>
   ```

   **B-briefing clauses added 2026-07-13, from the attestation-incident diagnosis** (ledger
   decision row 293, "INCIDENT + DIAGNOSIS: attested-CLEAN doc carried maintainer-visible
   legibility defects" — a document attested CLEAN twice, by two independent fresh Bs, still
   carried six defects the maintainer caught by eye). These three clauses belong in every B
   prompt from this date forward, alongside the four-clause test above, not as a replacement
   for it:

   - **(a) Table row/column labels are referents under clause 1(b), walked individually.** The
     incident's root cause #1 (ledger row 293) is that Rule 1's clause partition leaks at
     structured content: clause 1(c) owns a table's *frame* (is it captioned, is it grounded),
     and 1(b)'s referent-resolution walk is easy to read as a prose-only obligation, so nobody
     owned "does each individual cell resolve." B must walk every table's row labels *and*
     column headers one at a time, exactly as it would walk a paragraph's referents — a label is
     a referent like any other, not a decoration on the frame clause already checks.
   - **(b) The BROADCAST / INHABITATION TEST, stated in its general form.** A table's
     label-column header is a **type former**; every row label must be an **inhabitant** of the
     type the header declares
     ([design/ORCH-COMPOUND-NOMINAL-DETECTION.md](../vestigial_documentation/design/ORCH-COMPOUND-NOMINAL-DETECTION.md) Part 1,
     "the type-theoretic name"). For each row label `Li` under header `H`, distribute the header over
     the label (`H : Li`, or in prose, "does `Li` read as a well-formed instance of what `H`
     names?") and require the result well-formed. This is the general rule; "does the row answer
     the header's question" is **one worked example of it**, not the definition — per the
     maintainer's own type-theoretic clarification (ledger row 299): a `Directory` column whose
     rows must all be directories, or a `Lens` column whose rows must all be lenses, are
     instances of the identical test, and neither is phrased as a question. A column that fails
     the test for even one row (the incident's "capability … : cost to stand up" — a cost is not
     a capability) is a finding.
   - **(c) Compound relation-recoverability.** A coined noun-noun (or noun-noun-noun) compound
     is legible if and only if the reader can recover the implicit relation between its parts —
     Levi's deleted predicate
     ([design/ORCH-COMPOUND-NOMINAL-DETECTION.md](../vestigial_documentation/design/ORCH-COMPOUND-NOMINAL-DETECTION.md) Part 1:
     CAUSE, HAVE, MAKE, USE, BE, IN, FOR, FROM, ABOUT) — **from the document's own definition surfaces**
     (an inline gloss, a GLOSSARY.md link, or a single obvious relation apparent on the page).
     "Row hash" and "birth chain" recover via a single obvious relation or a linked definition;
     "trust story" (the incident's own specimen) does not — a reader cannot tell whether it
     names a story about trust, a property of being trustworthy, or a capability to trust, and
     the document says nothing that picks one. Flag any compound that does not resolve this way,
     citing the candidate relations you considered and why none is recoverable from the text.

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

   **B VERDICT ROUTING (rule added 2026-07-13): B prints its verdict as its FINAL MESSAGE and
   never uses `SendMessage` to report it.** This is the same misrouting the background-spawn
   paragraph above documents, restated as a standing rule because it recurred beyond that one
   pair of incidents: a B that tries to route its verdict via `SendMessage` — to an agent
   *type* rather than a specific address, or to whichever session it guesses is listening — has
   been witnessed failing to deliver it, repeatedly, across independent loop runs. The
   `run_in_background: false` requirement above closes the *background-completion* half of the
   failure; this rule closes the other half by removing the failure-prone transport
   altogether: whoever spawned B (per the B-briefing prompt skeleton above, which now
   instructs this explicitly) reads B's own final output as the verdict, full stop — B is never
   asked to actively route its own report anywhere. The workaround the two BACKLOG-recorded
   incidents stumbled into by accident (both recovered only because B also happened to print
   its verdict in its final message) is now the rule, not a lucky fallback.

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

   **ROUND-2 DISCIPLINE (two rules added 2026-07-13, both from the attestation incident, ledger
   decision row 293):**

   - **Round-2 B is always a FRESH FORK, never a resumed agent.** A round-2 B that is a
     `SendMessage`-resumed continuation of round 1's own agent was witnessed repeating its
     round-1 verdict *verbatim* against on-disk bytes that directly contradicted it — the
     resumed agent's prior turn had already committed to a verdict in its own context and did
     not genuinely re-read the repaired file. This is the same faculty-that-corrupts admission
     ADR-0017 Rule 1 already makes about A ("the author cannot unknow their own context"),
     applied to B across rounds: a B that remembers round 1 is no longer the zero-context
     reader round 2 needs, for the identical structural reason A never was one. Round 2 spawns
     a genuinely new `Agent` invocation, exactly like round 1 did — no `SendMessage` resume,
     ever, at either round.
   - **Round-2-after-repairs is the WEAKER verdict — it must re-sweep fresh, never only verify
     the finding list.** A round-2 pass that merely checks "were C's specific repairs applied"
     measures finding-list convergence, not defect-population exhaustion, and the incident is
     the witnessed proof this gap is real: a round-2 CLEAN verdict on
     [design/ORCH-KR-TITRATION-EXPLORATION.md](../vestigial_documentation/design/ORCH-KR-TITRATION-EXPLORATION.md) ("KR" =
     Knowledge Representation; a knowledge-representation titration exploration, the document
     the attestation incident's own specimens came from) was immediately followed by a
     maintainer catch (the "trust story" specimen, missed by *two* independent fresh Bs across
     two rounds), and a subsequent adversarial fresh sweep over the same document found
     **7 more findings** the convergence-focused rounds never surfaced.
     Round 2 therefore repeats the FULL four-clause test (plus the B-briefing clauses and the
     Named Defect Catalogue below) over the entire document as it now stands, from zero context
     — the same instruction as round 1, not a narrower "confirm these lines changed" pass. A
     round 2 that only re-checks the round-1 finding list is not a valid round 2 under this
     recipe; it is a rubber stamp wearing round 2's clothes.

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
  dated entries), [`judgment/**`](ORCH-OPERATING-CARD.md) (declared history — a predecessor era's
  archive, kept for the record but not binding unless a current spec cites it), or a document
  carrying an inline `doc-attest-exempt: <reason>` marker for a case the other two exclusions do
  not cover.

## Merging: the integrator's checklist (design/ORCH-WORKTREE-LEDGERING.md, "3c. The typed merge event" and "3d. The attestation merge-seam rule")

Everything above covers ONE document changed in ONE session. This section answers a different
question: **when a worktree's branch merges into mainline, what does the person or agent doing that
merge (the "integrator") owe the ledger and this A:B:C loop, specifically because it was a merge and
not an ordinary edit?** [design/ORCH-WORKTREE-LEDGERING.md](../vestigial_documentation/design/ORCH-WORKTREE-LEDGERING.md) designed both
answers; this section is where that design's own "3c. The typed merge event (convention first)" and
"3d. The attestation merge-seam rule (codify the precedent)" bullets asked to be written down, so the
next integrator inherits the rule instead of rediscovering it.

### The merge convention row ("3c. The typed merge event")

This project keeps a general append-only decision ledger in Postgres — a record of ledgered acts
(decisions, reviews, work-item state, and more), written and read through the `./led` command-line
verb — which is a SEPARATE record from the `attestations/doc-legibility-attestations.jsonl` ledger
this recipe's own step 6/7 write to; the two are both "ledgers" in the ordinary-English sense but are
different files serving different purposes. At each worktree merge, the integrator writes ONE row to
the `./led` decision ledger: `decision` kind, a statement that starts with the literal prefix `merge:`,
naming the branch that was merged, the resulting merge commit, and the work-item slug(s) whose work
rode that merge. Concretely:

```
./led decision "merge: <branch-name> -> <merge-commit-sha> (work items: <slug-1>, <slug-2>)"
```

This is a plain `decision` row — no new ledger kind, no kernel change (a first-class typed merge-event
kind is deferred until a real need for one is witnessed, the same mechanize-on-recurrence discipline
[ADR-0011](../law/adr/0011-mechanization-discipline.md) states generally: a new mechanism earns its
place by a witnessed recurrence, not by anticipation). The `merge:` prefix is a naming CONVENTION, not
a constraint the kernel enforces; it exists so the row is findable later (a text search for `merge:` in
the ledger, or the branch-attribution reader
[`tools/branch_attribution.py`](../tools/branch_attribution.py) —
[design/ORCH-WORKTREE-LEDGERING.md](../vestigial_documentation/design/ORCH-WORKTREE-LEDGERING.md)'s "3b. Branch attribution as
derivation, not schema" bullet — surfaced alongside it) and so a later deductive query can join "this
line of work landed" to "at this commit, carrying these slugs" without inventing a second place that
fact lives.

### The merge-seam attestation rule ("3d. The attestation merge-seam rule")

A git merge can produce a document byte-state that no fresh-context reviewer ever actually read: side
A's B-reviewed edit and side B's B-reviewed edit each passed their own loop independently, but the
MERGED text — the two edits interleaved, plus whatever surrounds the seam where they meet — is a new
sequence of bytes neither review covered.
[`gates/doc_attestation_presence.py`](../gates/doc_attestation_presence.py) already refuses exactly
this: it checks a document's CURRENT content hash against the attestation ledger, so a merged state
with no matching record is caught the same way an un-reviewed fresh edit would be — witnessed when a
merged state of [`ORCH-CAPABILITIES.md`](../ORCH-CAPABILITIES.md) was refused until reviewed
([BACKLOG.md](../BACKLOG.md), entry "First live enforcement of ADR-0017's loop — on the orchestrator's
own merge").

The remedy is the loop this whole recipe already describes, run once more at the merge, scoped
narrower than a full-document pass: after the merge lands (or in the merge commit itself, before it is
pushed), run this recipe's steps 2-6 with B reading the MERGED document, scoped to the changed sections
from both sides PLUS the seam between them — the paragraphs immediately before and after wherever the
two sides' independent edits now sit adjacent to each other, since that adjacency is the one thing
neither side's own B ever saw. If B comes back CLEAN on that scope, record the attestation exactly as
step 6 describes; if B finds a seam defect (a heading that no longer introduces what follows it, a
cross-reference broken by the interleaving, a repeated point now sitting twice), C repairs it before
the merge is considered done. This is not a new mechanism — it is this recipe's own loop, invoked once
more, at one more trigger (a merge landing) than "an edit finished."

## Named defect catalogue (added 2026-07-13)

This section answers a question the attestation incident (ledger decision row 293) raised
directly: two independent fresh Bs each attested a document CLEAN, twice, while it carried
defects the maintainer caught by eye — so B's briefing needed something more concrete than the
four general Rule-1 clauses. This catalogue is that concrete supplement: a standing, named list
of defect shapes handed to **every** B alongside the four-clause test and the briefing clauses
above (the B-prompt skeleton in step 2 now references it by name). B disposes of every entry
explicitly — "not present in this document" or a finding in the required shape — rather than
re-deriving these blind spots from scratch each time.

**Entry 1 — unrecoverable coined compounds.** A coined noun-noun (or noun-noun-noun) compound
whose implicit relation the reader cannot recover from the document's own definition surfaces
(see B-briefing clause (c) above). The measured evidence:
[design/ORCH-COMPOUND-NOMINAL-DETECTION.md](../vestigial_documentation/design/ORCH-COMPOUND-NOMINAL-DETECTION.md) and its sequel
[design/ORCH-COMPOUND-NOMINAL-DETECTION-2.md](../vestigial_documentation/design/ORCH-COMPOUND-NOMINAL-DETECTION-2.md) measured this
defect class on the live corpus: a deterministic *blocking* gate is not buildable at this
project's precision bar (the semantic judgment of relation-recoverability is not a static
property, per Downing 1977's non-enumerability result — the second note's own Verdict section
confirms this holds even for its stronger instrument), but a **ranked, report-only detector**
(`tools/experiments/compound_nominal_scan2.py`) exists and is measured useful as a reviewer aid:
top-10 100% / top-25 92% / top-50 78% precision on the actionable band (the "unrecoverable
coinages + undefined Claude-idiom metaphor compounds" slice of the scan's ranked output — the
band the second detection note names as the population these numbers describe), and it catches the
incident's own "trust story" specimen at global rank 1 of 13,855 candidates. This entry's
standing is therefore: B judges the compound directly (this is the semantic part no tool
performs), and the scan2 tool's ranked output is available as a **report-only net** to consult
when a document's compound-nominal load is large enough that manual review risks missing one —
it does not replace B's own judgment and is not itself a gate.

**Entry 2 — table label-type incoherence.** A table whose label-column header declares a type
that one or more row labels do not inhabit (see B-briefing clause (b), the broadcast test,
above) — the incident's own "capability for a Haiku-tier consumer" table, two of five rows
silently switching type to "property of the option." Named in the linguistics/logic literature
as faulty parallelism, the cross-division fallacy (mixing more than one *fundamentum
divisionis*), and Ryle's category mistake, and in this project's own law as the
[ADR-0008](../law/adr/0008-classification-discipline.md) MECE (Mutually Exclusive, Collectively
Exhaustive) requirement violated on the label axis
([design/ORCH-COMPOUND-NOMINAL-DETECTION.md](../vestigial_documentation/design/ORCH-COMPOUND-NOMINAL-DETECTION.md) Part 1). B
applies the broadcast test to every table in the document under review, not only ones that look
suspicious — the incident's tables looked ordinary to two independent Bs until the maintainer
ran the test by eye.

**Entry 3 — the empty-label-column-header lint.** The one sound, zero-judgment mechanical check
either detection note identified: a label column with **no header at all** cannot be broadcast
against any declared type (there is no genus to check inhabitance against), which is a
structural fact a reader can spot without any semantic judgment
([design/ORCH-COMPOUND-NOMINAL-DETECTION.md](../vestigial_documentation/design/ORCH-COMPOUND-NOMINAL-DETECTION.md) Part 2 and Part
3's "edge case" row; [design/ORCH-COMPOUND-NOMINAL-DETECTION-2.md](../vestigial_documentation/design/ORCH-COMPOUND-NOMINAL-DETECTION-2.md)
"Angle F"). B flags any table whose label column carries no header, independent of whether any
row's type is otherwise judged coherent.

**This catalogue GROWS by maintainer-caught incidents.** Every defect the maintainer catches
that B's four-clause test and current catalogue entries missed is a **candidate entry** — filed
here, dated, with the specimen and the general shape it represents (not just the one document it
was caught in), the same way entries 1–3 above were filed from the 2026-07-13 incident. Adding an
entry to this catalogue is a recipe edit like any other (binds on touch, per ADR-0017 Rule 4) and
does not require re-ratifying the recipe or ADR-0017 itself — the catalogue is this recipe's own
standing text, amended by addition, never by silently deleting or rewriting a prior entry's
account of what was caught and why.

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
- [design/ORCH-COMPOUND-NOMINAL-DETECTION.md](../vestigial_documentation/design/ORCH-COMPOUND-NOMINAL-DETECTION.md) and
  [design/ORCH-COMPOUND-NOMINAL-DETECTION-2.md](../vestigial_documentation/design/ORCH-COMPOUND-NOMINAL-DETECTION-2.md) — the
  measured evidence behind the B-briefing clauses and the "Named defect catalogue" section
  above: the compound-relation-recoverability defect, the broadcast/inhabitation test, and the
  ranked report-only detector and empty-header lint the catalogue cites.
- [design/ORCH-WORKTREE-LEDGERING.md](../vestigial_documentation/design/ORCH-WORKTREE-LEDGERING.md) — the memo whose §3c/§3d this
  page's "Merging: the integrator's checklist" section carries out, and the home of the merge
  drivers ([`tools/merge_jsonl.py`](../tools/merge_jsonl.py),
  [`tools/merge_backlog_sections.py`](../tools/merge_backlog_sections.py)) and the branch-
  attribution reader ([`tools/branch_attribution.py`](../tools/branch_attribution.py)) the
  merge convention row's `merge:` prefix is findable alongside.
