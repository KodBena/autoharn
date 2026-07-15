# The spy method — observability-driven development of autoharn itself

<!-- doc-attest-exempt: ADR-0017's A:B:C fresh-context loop (law/adr/0017-the-zero-context-reader.md,
"The fresh-context audit loop") requires spawning a genuinely separate Agent invocation as B; the
subagent authoring this document has no agent-forking tool in its toolset (verified: its available
tools carry no Agent/Task dispatch capability, only Bash/Read/Edit/Write/Artifact/Skill/ToolSearch/
ReportFindings) and cannot invoke it. This is the same blocker already recorded in ledger row 785 for
panel/manifests/SCHEMA.md ("no agent-forking tool available to this subagent for the ADR-0017 A:B:C
loop"). REMOVAL CONDITION: strike this marker and run the loop for real (record the attestation per
gates/doc_attestation_presence.py) the first time this document is touched by a session that does
carry a fork tool -- do not carry this marker forward as a permanent excuse. -->

This document answers one question: **what is the "spy method," and how does an orchestrator run
it correctly?** The spy method is how autoharn studies deployments it does not own or control --
the `~/ent` picom-hardening deployment, the `~/w/omega` frontend codebase -- as evidence for
autoharn's own design, without ever writing into the thing being studied. It is
observability-driven development applied reflexively: autoharn improves itself by watching
what happens when its own machinery (hooks, gates, the ledger, the A:B:C loop) runs inside someone
else's session, rather than by reasoning about that machinery in the abstract. If you are about to
dispatch an agent to go look at another deployment, a sibling codebase, or any subject this project
does not own, and report back what it finds -- this is the recipe, and the rest of this document is
the *how* and the *why*, distilled from five witnessed cycles against `~/ent`
(`observatory/ent/cycle-001.md` through `cycle-005.md` plus two same-day `2026-07-14-cycle-00{4,5}.md`
reports, a memo, and an independence audit) and four same-day scout sheets against `~/w/omega`
(`observatory/omega/2026-07-15-frontend-*.md`).

## 1. What a "spy" is, concretely

A spy is a single dispatched agent (Sonnet-executed, per this project's standing delegation
contract) sent to read a subject it does not own -- another live deployment's ledger and hook
journals (`~/ent`), or a sibling codebase's documented history and current architecture
(`~/w/omega`) -- and report back a **written sheet** answering a **named question**, using only
the subject's own read verbs and files. It never runs a multi-agent workflow of its own; it is one
session, one read pass, one report. Five witnessed ent cycles and four witnessed omega sheets are
all single-spy dispatches. Section 6 below names when a spy stops being the right shape and a
workflow sweep (multiple agents, a decomposition, a fan-out) takes over instead.

## 2. Commission shape

Every witnessed spy commission in this corpus shares four properties. An orchestrator writing a
new spy commission should keep all four; a commission missing one of them is the corpus's own
evidence of a gap, not a discovered exception.

### 2a. The verbatim-seed rule

The commission carries the maintainer's own question **verbatim or near-verbatim**, not a
paraphrase, and the report quotes it back. Cycle-001: "Question answered here (maintainer's,
verbatim in substance): what can autoharn AS SUCH learn from what is happening in ent's first
audit cycle." The `2026-07-15-frontend-architecture-reap.md` sheet opens: "Commission (maintainer,
2026-07-15, near-verbatim): omega/frontend has 'somewhat rigorous architectural discipline (or at
least, as of late -- after refactoring)... which also might be worth doing for [the new SPA]... I
like the general shape of what we have there.'" and quotes the maintainer's own words rather than
restating them in the scout's voice. This is the same discipline this project's own
commissions-verbatim-never-paraphrased ruling names for commissions generally (a paraphrased brief
was censured for narrowing scope) -- the spy method is one instance of that standing rule, not a
separate one. Practically: when writing a spy commission, paste the maintainer's actual sentence
into the prompt; when writing the report, quote it back at the top so a reader checking the report
against the ask can see the two side by side.

### 2b. The single-focus rule

Each spy answers **one** named question, and the corpus's own scoping decisions show this being
enforced actively, not accidentally. Cycle-004 records a mid-cycle maintainer instruction that
*narrowed* an already-dispatched cycle: "findings below are confined to autoharn/harness-mechanism
behavior only... No picom-side fix content... is described." The four omega sheets are one focus
each by construction, not by coincidence: `2026-07-15-frontend-architecture-reap.md` (current
structure only, "no git archaeology; a sibling scout covers history"), `2026-07-15-frontend-history.md`
(the sequence that produced the structure -- commits, ADR dates, postmortems), `2026-07-15-frontend-speed-reap.md`
(don't-do's and nice patterns from RCAs/postmortems), and `2026-07-15-structural-reap.md` (ten
capped, deliberately curated structural transfer candidates -- "capped deliberately... most of
what's there is domain-specific and not relevant"). A spy that tries to answer two unrelated
questions in one pass produces a report a later reader cannot cite precisely -- the omega scouts'
own cross-references to each other ("a sibling scout covers history") exist because the split was
made at commission time, not stitched together afterward.

### 2c. Read-only guarantees

Every report in this corpus states, near its top, in plain words: the subject was read-only
throughout, nothing was Written/Edited/or bash-mutated against it, and the report's claims come
only from the subject's own read verbs and log files -- never the subject's session transcript.
Cycle-001: "Subject (`/home/bork/ent`) was read-only for this report -- never Written/Edited/
bash-mutated; all claims below come from its tracker... and its `.claude/logs/*.journal.jsonl`...
Session transcripts were never read (action-stream-is-evidentiary-basis ruling)." The
reviewer2-independence audit adds a concrete instance of the guarantee holding under pressure: "One
`psql` attempt under the read-only `ent_ro` role during this cycle was refused by the database
(permission denied) and was not retried under a stronger role -- this cycle worked entirely through
ent's own verbs." That is the guarantee in practice: a spy that hits a wall inside the read-only
boundary reports the wall, it does not climb over it. This composes with, and does not restate,
this project's own action-stream-is-evidentiary-basis principle (guarantees rest on hooks/journals,
not on session transcripts or self-report) -- the spy method is that principle applied to a
*second* deployment's action stream, one the spy does not control.

### 2d. Output-sheet conventions

Two conventions recur across every sheet in this corpus and should be treated as the standing
shape, not a per-report choice:

- **A `doc-attest-exempt` marker with a stated reason**, because these are point-in-time
  observatory evidence records (per ADR-0017's own Exceptions: "point-in-time records... are
  cited as evidence, never retro-edited into compliance"), not living prose that the zero-context
  reader test binds to going forward. Every `observatory/ent/*.md` file in this corpus carries
  `<!-- doc-attest-exempt: point-in-time observatory evidence record, cycle-scoped -->` at its top.
- **VERIFIED / INFERRED marks on every substantive claim.** The omega sheets state the convention
  explicitly and then hold to it: "VERIFIED means the artifact was read; INFERRED means
  reconstructed from commit shapes, dates, or cross-references without reading the underlying
  source directly" (`2026-07-15-frontend-history.md`); "Every entry below is either VERIFIED (I
  read the actual RCA/postmortem/commit worklog text cited) or INFERRED (reasonable extrapolation,
  no direct textual confirmation). No entry here is unverified-and-unmarked"
  (`2026-07-15-frontend-speed-reap.md`). The architecture sheet extends this to a **partial-read
  disclosure**: which documents were read end-to-end, which were skimmed by heading, and which
  were never opened at all and are cited only INFERRED-from-citation -- disclosed rather than
  bluffed ("omega's own house rule... is noted, not fully honored, for the docs skimmed --
  disclosed rather than bluffed"). A spy report with an unmarked claim is not following this
  convention; a spy report that discloses its own reading gaps is the corpus's actual practice, not
  an aspiration.

## 3. The artifact-claim dereference rule

A specific, cheap, and load-bearing check surfaced same-day (2026-07-15) as a finding, not from
the ent/omega cycles themselves but from the immediately adjacent scout work these cycles fed
(ledger rows 896-899): a scout's `Write` call to `observatory/omega/2026-07-15-frontend-architecture-reap.md`
silently landed at the wrong path (`/home/bork/w/autoharn/observatory/omega/...`, dropping the
`vdc/1` path segment -- `Write` creates missing parent directories, so the mistyped path succeeded
without complaint) and the ledger row recording the artifact as written was filed *before* anyone
ran `ls` on the claimed path. Row 898 names the class and the fix in one sentence: "'Write returned
success' witnesses A path, not THE path... Cheap universal check: any report claiming an artifact
at a path must include the ls/wc of that exact path." Row 897 is the correction once the maintainer
caught the mismatch by eye: the file was intact (30217 bytes) at the wrong location and was `mv`'d
(bit-identical, not re-typed) to the commissioned path.

**Recipe line for every delegation prompt that asks an agent to write a file and report on it:**
the report must include the `ls -la`/`wc -c` (or equivalent) output of the *exact claimed path*,
run *after* the write, not the write tool's own success signal. This is now this project's own
practice, not just advice: this task's own report (below) follows it for every path it claims. Row
899 opened a candidate harness-level mechanization (`artifact-claim-dereference-guard`, not
scheduled) for the same check at the PostToolUse/Stop-hook or `led`-evidence-flag layer -- a join
against data the action stream already carries (the Write's real path vs. the claimed path), not
new instrumentation -- and a read-side form (the panel's planned hover-synopsis dereferencing
cited artifacts). Until one of those ships, the recipe line above is the only guard; it is cheap
enough that omitting it from a delegation prompt is itself a gap worth flagging on sight.

## 4. The sync-reviewers/never-wait recipe line

Four witnessed instances on 2026-07-14 (ledger row 719, `builder-stop-and-wait-stall-class`) of
builder agents stopping mid-commission to "wait for" a reviewer or background notification that
never arrives in their context: a doc-ABC builder whose APPARATUS verdict was delivered to the
orchestrator instead of the waiting builder; a gates-trio workflow stage; the gates-trio FINISHER
(a free agent, stopped twice); and workflow subagents lacking fork tools discovering the pattern
late. Each cost an orchestrator wakeup and a manual resume with the identical nudge.

This project already has the fix, shipped and load-bearing, for the one instance of this class it
has fully worked out: `design/ORCH-ABC-AUDIT-LOOP-RECIPE.md`'s A:B:C loop states, as a **hard
requirement, not a preference**, "Spawn B synchronously (`run_in_background: false`), always,"
and explains why in the same breath -- a background-spawned child's completion routes to the
*top-level orchestrator session*, not to the subagent that spawned it, because completion routing
in this harness follows the spawn's own top-level session. That routing is sound only when the
loop-runner IS the top-level session; the moment a reviewer loop runs *inside* a dispatched
subagent -- the common shape, an orchestrator delegating documentation work to a Sonnet
executor that then runs its own A:B:C loop before reporting back -- a background reviewer's
completion never reaches the waiting subagent. Two live BACKLOG-recorded incidents are the direct
ancestors of row 719's four: a subagent-run loop's background-spawned B tried to `SendMessage`
back to `"general-purpose"` (an agent *type*, not an address) and failed; both recovered only
because the child happened to also print its verdict in its own final output, which the
orchestrator -- not the waiting subagent -- picked up and relayed. **That recovery is not a
mechanism to depend on.**

**The recipe line, generalized beyond the A:B:C loop to every reviewer/child dispatch a builder
or workflow stage makes:** run every reviewer, B-round, or child subagent **synchronously**
(`run_in_background: false`), always, without exception, regardless of whether the dispatching
session is the top-level orchestrator or a subagent itself. Never end a turn to "wait" for a
background result addressed to a session you are not. If a result must be recovered after the
fact, recover it from the child's own output file or transcript, or simply re-run the same
dispatch synchronously -- do not architect a workflow stage around waiting for a notification that
this harness's own routing rules make structurally unreachable from inside a subagent.

**Disposition of `builder-stop-and-wait-stall-class`:** this section is the fold-in its own
mechanism-candidate list named as option (2) ("fold into the spy-method-formalization item's
recipe section (composes)"). The generalized rule above -- synchronous dispatch, always, no
background-wait, recover from output rather than notification -- is the standing recipe line this
document commits to, applicable to every builder preamble and workflow stage in this project, not
only the A:B:C loop that first forced it into the open. Per row 719's own text this is
"Sonnet-executable (recipe/doc edit)," and this document is that edit; the corresponding ledger
work item is closed at the end of this task (Section 7) with this document cited as its witness.

## 5. When one spy vs. a workflow sweep

The corpus draws this line by demonstration, not by explicit rule, so it is worth stating plainly
here. A **single spy** is the right shape when:

- the question is a single, answerable "what happened" or "what is here" ask against a subject
  the dispatcher does not own (an ent cycle's headline question; one omega scout's single focus,
  section 2b);
- the read surface is bounded and enumerable ahead of time -- a ledger, a fixed set of journal
  files, a git log, a fixed document list;
- the answer does not require the subject itself to be modified, decomposed, or acted on -- only
  observed and reported.

A **workflow sweep** (a decomposition into multiple parallel or staged agents, the shape ent's own
cycle-1a FIND+VERIFY 16-surface audit or the gates-trio finisher workflow use) is the right shape
when:

- the work being *observed or performed* is itself naturally decomposable into many independent
  units of resumption (ent's 16-surface `harden-*` decomposition; the FIND/VERIFY split; the
  split/architect/implement fix-stage design) -- note this is a property of the **subject's own
  work**, not of the spy watching it: the ent cycles remained single spies throughout, even while
  the *subject* they watched ran a 16-agent workflow of its own;
- multiple independent reviewer countersigns or out-of-frame checks are required before a result
  is accepted (the fix-stage's own "MANDATORY out-of-frame co-signed review" design, or this
  project's own A:B:C loop for a document);
- the task requires *writing* into the subject or into this project's own tree in more than one
  place at once, which a single read-only spy is constitutionally unable to do (a spy that starts
  mutating anything is no longer a spy under section 2c's guarantee).

The corpus's own cleanest illustration: cycle-002's "LOAD-BEARING ANSWER" section reports the
distinct-actor-countersign question as **UNEXERCISED, not failed**, precisely because the *spy*
correctly refused to synthesize an answer about a workflow (the fix-stage's countersigning) that
had not yet produced any evidence in the subject's own action stream -- a spy reports what the
action stream shows, including "not yet," rather than reaching for a workflow-sized conclusion a
single read pass cannot support.

## 6. The opt-in provisioning key question

This item's own text speculated that "an opt-in provisioning key for this service class may
already exist" in the harness's project-scaffolding verb. **Verified, this task: no such key
exists.** `bootstrap/new-project.sh` accepts `--governed <patterns>` (widens the governed-file set
at birth -- unrelated to observability) and no other opt-in flag; grepping the script and
`bootstrap/provision-db.sh` for `spy`, `observatory`, `opt-in`, `provisioning key`, or a read-only
(`_ro`-suffixed) database role turns up nothing -- `provision-db.sh` provisions exactly one role
per world, `<name>_rw`, with no read-only counterpart created at birth. The `ent_ro` role the
reviewer2-independence audit found refused (permission denied) on one `psql` attempt is therefore
evidence of a role that exists in `~/ent`'s own deployment specifically, not a standing autoharn
scaffold feature every new world gets. Filed honestly rather than silently: **no provisioning key
for the spy-method's read-only posture is wired into `bootstrap/new-project.sh` today.** Building
one (e.g. a `--spy-role` flag that provisions a companion read-only login alongside `<name>_rw`,
mirroring the `_ro` shape witnessed ad hoc in `~/ent`) is a candidate for a future commission but
is explicitly out of this task's scope -- this is design+recipe work, not a kernel/provisioning
change, and CLAUDE.md's ORCHESTRATION contract reserves provisioning-script edits for their own
licensed commission. Recorded here so the next reader does not have to re-derive the "does it
exist" answer from scratch.

## Related

- [ADR-0017](../law/adr/0017-the-zero-context-reader.md) -- the zero-context reader discipline
  this document's own output-sheet conventions (section 2d) instantiate, and whose A:B:C loop
  this document is itself subject to (see the exemption marker at the top of this file for why
  that loop is UNEXERCISED, not run, this pass).
- [design/ORCH-ABC-AUDIT-LOOP-RECIPE.md](ORCH-ABC-AUDIT-LOOP-RECIPE.md) -- the synchronous-dispatch
  rule section 4 generalizes, worked out first for the A:B:C loop specifically.
- `observatory/ent/cycle-001.md` through `cycle-005.md`, `2026-07-14-cycle-004.md`,
  `2026-07-14-cycle-005.md`, `2026-07-14-MEMO-to-ent-orchestrator.md`, and
  `2026-07-14-reviewer2-independence-audit.md` -- the ent-side corpus this document distills.
- `observatory/omega/2026-07-15-frontend-architecture-reap.md`,
  `2026-07-15-frontend-history.md`, `2026-07-15-frontend-speed-reap.md`, and
  `2026-07-15-structural-reap.md` -- the omega-side corpus this document distills.
- [design/MAINT-COUNTERSIGN-CLOSE-SEMANTICS-SPEC.md](MAINT-COUNTERSIGN-CLOSE-SEMANTICS-SPEC.md)
  section 5 ("Element C") -- the independence-grade vocabulary
  (`same-principal`/`same-session`/`distinct-session`/`distinct-deployment`) the
  reviewer2-independence audit classifies against, cited in section 2c above by name only; read
  that spec directly for the grades' full definitions.
- CLAUDE.md's "Auditability -- the ledger is the trail" section and the
  action-stream-is-evidentiary-basis memory ruling -- the standing principle section 2c's
  read-only guarantee instantiates for a *second*, non-owned deployment.

## Revisit when...

1. A spy is dispatched against a third kind of subject (not a live harness deployment like `~/ent`,
   not a sibling static codebase like `~/w/omega`) -- confirm sections 2-6 still hold or need a
   third worked shape.
2. The `artifact-claim-dereference-guard` work item (row 899) is built -- update section 3 to cite
   the mechanized check rather than only the manual recipe line.
3. A spy-role provisioning flag is actually commissioned and built -- update section 6 from "does
   not exist" to the flag's name and shape.
4. This document itself is next touched by a session carrying an agent-forking tool -- strike the
   top-of-file exemption marker and run the real A:B:C loop (see that marker's own removal
   condition).
