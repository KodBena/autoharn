# Deployment-session methods — checking a blessed tool's output, and not writing outside a grant

<!-- doc-attest-exempt: doc-tree relocation mechanical edit (work item doc-tree-reorg-user-guide, ledger row 1620, 2026-07-18) -- relative link path(s) repointed to a sibling file's new location after a git-mv relocation elsewhere in the tree; no prose rewrite, same disposition as the v1.1.2 release-cut's own markers (commit 543a389). Removal condition: strike this marker and run the real A:B:C loop next time this file is touched for content, not just link repair. -->


Audience: anyone dispatching or reviewing agent work in this project — an orchestrator deciding
whether to trust a newly-blessed tool's output, or an agent (or the human reviewing one) who hit
a permission boundary mid-task and has to decide what to do next. This page answers two separate
questions with two separate methods, harvested from the same source session and filed together
because both are about **what an agent owes the record when its own authority or its own tool's
authority is in question**: (1) when a tool freshly blessed for use hands back a labeled-good
result, what do you do before you act on that label; and (2) when an agent cannot write the
finding its own investigation produced, what do you do instead of making it write anyway. Read
this before trusting a scheduler's, linter's, or solver's "optimal"/"valid"/"green" label on a
consequential decision, or before deciding whether a read-only agent may write down what it
found.

**Provenance, stated honestly up front.** Both methods below are witnessed in the
**experience-world deployment session**, a separate downstream deployment this repository's own
harness scaffolds and observes — not this repository, and not independently witnessed by the
author of this page. The two rows cited (experience-world ledger row 89 for Method 1, row 54 for
Method 2) were relayed by the maintainer as a description of what happened; this page did not
read that ledger, that session's transcript, or any file under that deployment's own tree. Every
factual claim below about "what the session did" is marked **relayed-by-spy** for exactly this
reason: it is evidence of the same evidentiary status as a dated citation this author could not
independently confirm, following [ADR-0017 Rule 1](../law/adr/0017-the-zero-context-reader.md)'s
own honest-disclosure standard (recording an unconfirmed source plainly rather than dressing it
up as a witnessed one). What follows is the **general method** each episode illustrates, written
so it stands on its own regardless of whether a reader can chase the source row.

## Method 1 — a blessed tool's output is a claim, not a witness; check it against ground truth before you trust it

**The general method.** A tool a project has newly approved for use — "blessed" in this
project's own vocabulary, meaning reviewed and accepted as fit to guide real decisions — still
only reports what its own model told it. A label like `optimal`, `valid`, or `green` is the
tool's claim about its own internal computation, not an independent confirmation that the
computation's inputs matched the real world it was meant to describe. Where the world already
contains an independent source of ground truth relevant to that computation — a typed dependency
edge in a ledger, a kernel constraint, a banked fixture, any fact recorded by a mechanism other
than the tool being checked — the discipline is a three-step chain: **label, then check the
label's claim against that ground truth, then ledger any divergence as a finding** — never hide a
caught mismatch by quietly hand-correcting it and moving on, and never skip the check because the
label already says the answer.

**The episode this generalizes from (relayed-by-spy, experience-world ledger row 89).** A session
ran a newly-blessed scheduling tool — `tools/makespan-scheduler/` in this repository's own
vocabulary, described further in
[design/ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md](../design/ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md) — and
received a schedule labeled `optimal`. Before trusting that schedule, the session checked it
against the real dependency edges recorded for the work items being scheduled (a typed
`work_depends_on` edge, the kind
[kernel/lineage/s30-typed-dependency-edges.sql](../kernel/lineage/s30-typed-dependency-edges.sql)
adds a typed `edge_type` column to) — and caught that the schedule would start a dependent work
item before its prerequisite had finished. The session corrected the schedule by hand and
recorded the discrepancy as a ledger finding, rather than silently fixing it and reporting the
run as clean.

**Why this is the tool's own documented limitation, not a fluke.**
[design/ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md](../design/ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md) §3 names
this exact failure mode in this repository's own law, independent of the relayed episode: the
scheduler solves an **independent-tasks** model — its only notion of relationship between two
jobs is "must not run concurrently," never "B consumes A's output" — so a batch containing a true
data dependency, fed to the scheduler as if it were a mere resource conflict, "can be actively
wrong... it may schedule B to start before A's output exists, because the solver has no
representation of 'before' in the data-flow sense." §2 of the same document states the
scheduler's own guarantee is conditional on its input being "a complete and accurate account of
every real conflict," and that "the scheduler cannot audit its own input's fidelity to the real
world; nothing in this tool tries to." The relayed episode is that named gap made concrete: a
`work_depends_on` edge is exactly the fact the scheduler's own model has no notion of, and a
session that checked the schedule against that edge caught precisely the failure mode the
scheduler's own documentation already disclaims.

**The incidental validation, worth naming on its own.** The check was only possible because the
ground truth existed and was reachable: the s30 typed dependency edges were exactly the
independent fact that made "check the blessed tool's output" a concrete, executable step rather
than a vague exhortation to "be careful." A blessed tool's output is checkable against ground
truth only where a project has bothered to keep ground truth in a form a checker (human or agent)
can actually query — an unmodeled dependency, kept only in someone's head or a stale comment,
would have left the same check with nothing to check against. The general lesson generalizes
past this one scheduler: before trusting any newly-blessed tool's label on a consequential
decision, ask what independent, queryable ground truth exists for the claim the label is making,
and if none exists, that absence is itself worth naming rather than trusting the label anyway.

**Enforcement surface, named honestly per
[ADR-0011 Rule 1](../law/adr/0011-mechanization-discipline.md).** This method is **review-only**:
no mechanism in this repository currently forces a session to check a blessed tool's label
against available ground truth before acting on it, and the makespan scheduler's own §6
counter-signature step
([design/ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md](../design/ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md), "designed
discipline, not a built or wired mechanism" per its §7) is itself unwired. Per
[ADR-0011 Rule 2](../law/adr/0011-mechanization-discipline.md), a second independently-witnessed
recurrence of this exact class — a blessed tool's label trusted without a ground-truth check,
where ground truth existed and could have caught the same failure — is this method's own trigger
to convert from review-only prose into a check named at the strongest feasible surface, not a
standing invitation to keep citing this one relayed episode indefinitely.

## Method 2 — a permission boundary is part of the record's integrity; dispatch a second, correctly-granted agent rather than route around it

**The general method.** An agent's permission envelope — what it was granted the tools to do —
is not only an access-control fact about that one invocation; it is part of the provenance of
anything that agent produces. A finding written by an agent operating outside its own grant (a
read-only investigation agent that somehow writes its own conclusion to disk) carries a corrupted
provenance even when the finding's content is correct, because the record now asserts an act the
agent was never authorized to perform. The honest move when a read-only agent's investigation
needs to be written down is **a second dispatch**: a separate, write-capable agent records the
first agent's finding. The cost of that second dispatch — a fresh agent invocation, briefed with
the first agent's output — is the price of a trustworthy trail, not overhead to be economized
away by forcing or working around the original grant.

**The episode this generalizes from (relayed-by-spy, experience-world ledger row 54).** A
read-only investigation agent in the experience-world deployment session could not write its own
finding to the record, because its grant did not include write access. Rather than force the
write or work around the grant, the session dispatched a second, write-capable agent whose job
was to record the finding the first agent had already produced.

**Why this is not merely a permissions technicality.** This project's own orchestration contract
already treats witnessed claims and unwitnessed ones as different in kind — "claims carry
witnesses" ([CLAUDE.md](../CLAUDE.md), ORCHESTRATION section) — and a permission grant is one of
the facts a later reader relies on to know what kind of witness a given record is. A finding that
an agent was not authorized to write is, structurally, the same defect class as a resumed agent
reporting a stale verdict across an A:B:C round
([design/ORCH-ABC-AUDIT-LOOP-RECIPE.md](ORCH-ABC-AUDIT-LOOP-RECIPE.md)'s round-2 discipline: "a
B that remembers round 1 is no longer the zero-context reader round 2 needs") — in both cases the
record's trustworthiness depends on a structural property of who or what produced it, not merely
on whether the content happens to be right. Working around a permission boundary to save a
dispatch is the same shortcut as resuming a stale B to save a fresh fork: cheaper in the moment,
and it corrupts exactly the property the extra step existed to protect.

**What this method does not claim.** It is not a claim that every read-only agent's output must
always be re-written by a second agent — a read-only investigation whose findings are relayed
verbatim by the orchestrator itself (a human or agent already holding a legitimate write grant,
summarizing rather than impersonating the investigator) is a different, unproblematic case; the
defect this method names is specifically an agent writing *as itself* outside its own grant, not
any downstream use of a read-only agent's output.

**Enforcement surface, named honestly per
[ADR-0011 Rule 1](../law/adr/0011-mechanization-discipline.md).** This method is **review-only**
in general — recognizing that a task calls for a second, correctly-granted dispatch rather than a
workaround is a judgment call at dispatch time, not something a static check can catch ahead of
time. Where it composes with a mechanized surface already in this project: an agent's tool grant
is enforced at the harness level (the agent literally cannot invoke a write tool it was not given
access to), so the *hazard* this method is really naming is not "the agent wrote when it
shouldn't have" — the harness already forecloses that — but "the orchestrator, faced with that
refusal, chose to route around it" (asking the same agent again with escalated tools mid-task, or
hand-copying the finding into the record itself in a way that loses the second witness). That
choice point is not currently gated by any mechanism in this repository; per
[ADR-0011 Rule 2](../law/adr/0011-mechanization-discipline.md), a witnessed recurrence of an
orchestrator routing around a permission refusal instead of dispatching a second agent is this
method's own trigger to name a sharper mechanism.

## Related

- [design/ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md](../design/ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md) — the
  scheduler's own documented independent-tasks limitation (§3) and its unbuilt counter-signature
  discipline (§6–7), the law-corpus grounding Method 1's relayed episode is a concrete instance
  of.
- [kernel/lineage/s30-typed-dependency-edges.sql](../kernel/lineage/s30-typed-dependency-edges.sql) —
  the typed `edge_type` column on `work_depends_on` that made Method 1's ground-truth check
  possible in principle; ratified 2026-07-15 per this file's own header.
- [design/ORCH-ABC-AUDIT-LOOP-RECIPE.md](ORCH-ABC-AUDIT-LOOP-RECIPE.md) — the fresh-fork
  discipline (never resume an agent across rounds) that Method 2's second-dispatch rule is a
  sibling case of: both refuse to let a record's trustworthiness depend on stretching one
  invocation past what its own standing (fresh context; a write grant) actually supports.
- [law/adr/0011-mechanization-discipline.md](../law/adr/0011-mechanization-discipline.md) — Rule 1
  (declare the enforcement surface honestly) and Rule 2 (a recurrence converts review-only prose
  to a mechanism), the vocabulary both methods' "Enforcement surface" paragraphs use.
- [CLAUDE.md](../CLAUDE.md), ORCHESTRATION section — "Claims carry witnesses," the standing rule
  Method 2's provenance argument is one instance of, and the source of this page's own
  relayed-by-spy disclosure convention.

## What this recipe does NOT claim

- **Not independently witnessed.** Every factual claim about the experience-world session's own
  conduct is relayed by the maintainer, not read or confirmed by this page's author from that
  deployment's own records — marked relayed-by-spy throughout rather than presented as a
  first-hand audit finding.
- **Not a claim that either method is currently mechanized.** Both "Enforcement surface"
  paragraphs above say review-only plainly, per
  [ADR-0011 Rule 1](../law/adr/0011-mechanization-discipline.md)'s own honesty requirement; this
  page names the trigger that would convert each to a mechanism, and does not claim one exists
  today.
- **Not a critique of the makespan scheduler.** Method 1's episode is the scheduler's own
  documented limitation working as designed — the tool never claimed to model data dependencies,
  and the check that caught the mismatch is exactly the counter-signature discipline
  [design/ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md](../design/ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md) already
  recommends. The finding is evidence the recommended check works when applied, not evidence the
  tool is unsound.
