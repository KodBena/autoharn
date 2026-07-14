# Maintainer decision brief — the open review queue, 2026-07-14

Audience: maintainer

This is a new, separate brief — it does not replace
[MAINT-MAINTAINER-DECISION-BRIEF.md](MAINT-MAINTAINER-DECISION-BRIEF.md) (2026-07-12, still
live for its own five items: your signing key, the research-ledger script, the trust-domain
question, the Opus-readiness follow-ups, and publishing). This document instead answers a
different ask: everything sitting in the project's own review queue — surfaced by `./pickup`,
the command that prints a status summary of everything the project is tracking, one section of
which lists items specifically waiting on you — and everything else waiting on your go-ahead
alone, as of tonight. "The ledger" throughout this document means the project's append-only
decision log, a database table read via the `./led` command; every "tick" instruction below is
a `./led decision "..."` line that writes your answer into that log. Every item below was
re-checked against its source document or tracker row this session — nothing here is carried
over from memory or an older report.

This document is written the same way as the other one: for someone running this project who
does not write code and does not want to read source files to answer a question. Each item
states what the question actually is in plain words, why it exists, what saying yes or no
changes in practice, a recommendation clearly marked as this session's orchestrator judgment
(not a neutral fact), and the exact command to type to record your answer. Where a decision has
a genuinely fine "no" or "not yet," that is stated plainly.

**A note on timing.** You answered four of the review-queue items live, in conversation, while
this brief was still being written — those are recorded below as already decided, not presented
as open questions. Two more (pgAudit, the knowledge-representation titration idea) you said to
pass on for now; they are written up in full below so they are ready to read whenever you come
back to them, not because they need an answer tonight. What is genuinely live: the NIST
security-checklist follow-ups (the fullest write-up in this document, below, because you said
the first pass wasn't plain enough), and the six go-ahead-only items in Part B.

---

## Already decided today

You answered these four live; each is recorded on the project's decision log (the "ledger")
already. Listed here only so this brief's own count of what's still open is honest — no action
needed on any of these four.

- **The stale "four verbs" sentence in the project's house rules (`claude-md-four-verbs`)** —
  approved and already fixed (ledger row 657). Your own words, paraphrased: this was too small
  and obvious a thing to have been queued for you at all — a fixable small error gets fixed on
  sight, not routed to you for permission.
- **The compound-word documentation-defect detector (`detector-adoption-decision`)** — adopted
  (ledger row 658); the follow-up tracking work (recording every time it flags something, so a
  future reader can check whether it's biased) is now unblocked and moving.
- **The two notes behind that detector (`compound-nominal-detection-pair`)** — accepted, same
  motion as the adoption decision above (ledger row 659).
- **The table-building tool that forces an author to double-check every row (`typed-table-adoption`)**
  — adopted (ledger row 660) — you called it the other way from this brief's own original
  recommendation to hold off, and a follow-up item (`typed-table-ssot-integration`, ledger row
  663) is now filed to close the one real gap the experiment note itself named: making sure the
  table's true source stays in one place instead of two once it's wired into real documents.

---

## Part A — the two items you said to pass on for now

Written up in full so they are ready to read whenever you return to them — not because either
needs an answer tonight.

### A1. Knowledge-representation "titration" — should the project start turning some prose facts into small structured database rows?

*Source, read in full this session:
[ORCH-KR-TITRATION-EXPLORATION.md](ORCH-KR-TITRATION-EXPLORATION.md). Tracker slug
`kr-titration-design-exploration`.*

**The question, in plain words.** Right now, when the project records a fact — "is feature X
actually built or just planned?" — it gets written as a sentence inside a longer document. The
same fact sometimes gets written down twice, in two documents, and if the two sentences ever
say slightly different things, a reader can be misled without anyone noticing (this actually
happened once, tracked in detail in the document). You floated the idea of also storing some
facts as small, rigid, one-line database records — like a form with fixed blanks — so a cheap,
fast reader (not a full model) can check them without understanding paragraphs of prose.

**What was investigated.** The document looked at five different ways to build this (including
heavier, more "official" formats used elsewhere in the software world) and rejected four of them
as overkill or a poor fit for this project's own logic engine. The one that fits: extend the
project's *existing* mechanism — it already has four "fill-in-the-blank" record types (for
declaring available data sources, cost estimates, and two kinds of catalog entries), each with a
strict format that refuses to save if filled in wrong. The proposal is a fifth kind, for "facts
about how the system itself behaves," built the same way.

**Your idea about *when* to write these records, tested against a real incident.** You proposed
that the best moment to write one of these structured records is right after a mix-up is
discovered — because at that moment, someone has already had to pin down exactly what the fact
actually is, so writing it down formally costs almost nothing extra. The document tested this
against a real recorded mix-up and found it holds up, with one important addition: writing the
record only helps if, in the very same edit, every place that used to state the fact in prose is
changed to point at the new record instead. If you write the record but leave the old sentences
in place, you have not fixed the problem, you have added a third place a reader might look and
get a stale answer from.

- **If you approve:** nothing gets built tonight. What happens is a standing habit change — the
  next time a documented mix-up gets resolved, whoever resolves it writes a short structured
  record of the correct fact and updates every place that used to state it in prose, instead of
  only fixing the prose. Later (a separate, smaller decision, not asked now) the project would
  add the formal fifth record type so this can be done more rigorously.
- **If you decline:** the project keeps recording facts only as prose, and reconciles mix-ups
  the way it always has.

**Recommendation (orchestrator's): approve the habit change now (the document's "Stage 0"), and
leave the bigger formal record-type work for a later, separate decision.** The habit change
costs nothing to adopt — it is just discipline, not new software — and the document's own
evidence (an existing incident, tested honestly rather than assumed) supports it. The bigger
formal-record-type step can wait until it is actually needed.

**The act.**
```
./led decision "review-done: kr-titration-design-exploration | approve Stage 0 (resolved-collision facts get deposited as a structured row and every prose teller repointed in the same edit); Stage 1 (the formal fifth record type) deferred, not commissioned"
```

---

### A2. pgAudit — should the database start logging who reads the project's own decision record?

*Source, read in full this session:
[ORCH-PGAUDIT-EXPLORATION.md](ORCH-PGAUDIT-EXPLORATION.md). Tracker slug
`pgaudit-exploration`. Strengthened by last night's finding, read in full this session:
[observatory/ent/2026-07-14-cycle-004.md](../observatory/ent/2026-07-14-cycle-004.md) §2.*

**The question, in plain words.** The project's decision record (the "ledger," the database
table everything important gets written into) is very well protected against someone secretly
*editing or deleting* an entry — there is a tamper-evident chain and a tripwire for exactly
that. But nothing today records who merely *reads* it. pgAudit is a free, well-established
add-on for the database software (Postgres) that would start writing "who ran what query, when"
into a plain log file on your machine. Installing it costs: a software package install, a
database restart (a few seconds of downtime), and log file growth on your disk. Nothing is
installed yet — this document only investigated what it would mean.

**Why it matters more as of last night.** A separate investigator (the "ent observatory," a
recurring check-in on a sibling deployment of this same software) found a real, live example of
exactly the gap pgAudit would close: an automated helper on that other deployment ran a
privileged database command to fix its own mistake, and *nothing in the standard action log
recorded whether that command actually succeeded* — only that it was attempted. The tooling
meant to capture "what actually ran" turned out to be recording the wrong text due to an
unrelated bug, so the record of the attempt existed but the record of the outcome did not. A
database-level log like pgAudit would have captured both, directly, regardless of any bug in
the surrounding tooling. This is not a hypothetical anymore; it happened.

**The honest limits, stated plainly (both documents are emphatic about this).** pgAudit only
logs *statements* (what was asked), not *results* (what came back). It cannot reliably watch a
database superuser — the same powerful account the tamper-evident chain is designed to defend
against — because a superuser can simply turn the logging off. And the log file itself sits on
disk with no tamper protection of its own; it is strictly a diagnostic aid, never a replacement
for the ledger's own protections. Both documents recommend explicitly labeling it that way if
adopted, so nobody mistakes it for stronger evidence than it is.

- **If you say yes (even just the cheapest version):** a much smaller step exists first —
  turning on a module (`pg_stat_statements`) that already ships with your database software, no
  new install needed, just one settings line and a restart. It answers "which kinds of queries
  keep getting run" (useful for noticing when someone bypasses the project's proper commands and
  writes raw database queries by hand instead) but does not give you who-read-what tracking.
  Full pgAudit is the second, bigger step, if you want actual read-tracking.
- **If you say no:** nothing changes; the gap stays exactly as it is today, on both this
  deployment and any deployment like it.

**Recommendation (orchestrator's): turn on `pg_stat_statements` now (cheap, no new package,
answers a real and current question about stray hand-typed database commands); hold full pgAudit
as a "yes when you're ready" rather than urgent, but read the outcome-invisibility finding above
as the strongest argument yet for eventually saying yes to it.** The gap it would close is no
longer theoretical.

**The act.**
```
./led decision "review-done: pgaudit-exploration | adopt Stage 1 (pg_stat_statements: preload + CREATE EXTENSION, no new package); Stage 2 (pgaudit proper) approved-in-principle, scheduled at maintainer's convenience, config authored against the live host file when installed"
```
(or, to decline everything for now: `./led decision "review-done: pgaudit-exploration | decline for now, revisit if the read-tracking gap becomes load-bearing"`)

---

## Part A2 — the NIST security-checklist follow-ups (the fullest write-up in this brief)

*Source, read in full this session:
[ORCH-REGISTRY-COMPLETENESS-AUDIT-001.md](ORCH-REGISTRY-COMPLETENESS-AUDIT-001.md). Tracker
slug `registry-audit-p1-p7`. You said the first pass at explaining this wasn't plain enough, so
this section starts from the concepts instead of assuming them.*

### What this audit actually measured, in plain words

At some point you asked the project to measure itself against NIST SP 800-53 — a standard
security-and-privacy checklist published by the U.S. government's National Institute of
Standards and Technology, the same body that sets a lot of the technical standards American
government agencies and contractors are required to follow. It is not a law and nothing forces
you to follow it; you adopted it voluntarily, as an outside yardstick, so the project's own
sense of "is this well-governed" isn't just self-graded. This checklist itself is what a
"control-family registry" means, where that phrase appears elsewhere in the project's own
records — a published list of security topic areas ("control families") to be measured against,
not a piece of software or a database this project built.

The checklist is organized into **20 topic areas**, called "families" — things like Access
Control (who can do what), Incident Response (what happens when something goes wrong), Audit
and Accountability (does the system keep a record of what happened), Contingency Planning
(what happens if the hardware dies), and so on. Each family contains a further list of specific
numbered items (e.g., "AU-2, Event Logging") — but for most of this audit, the family level is
the resolution that matters: does this project have *anything* addressing this whole topic area,
yes or no, and if not, has anyone said whether that's on purpose.

This first audit walked all 20 families and, for each one, asked: does the project have a real
mechanism here (**PARTIAL** or, if it were ever complete, **IMPLEMENTED**), or is there nothing
at all? And if there's nothing, is that a decision or an accident?

### "Silently absent" vs. "explicitly excluded" — what this actually means for this project

This is the heart of the finding, made concrete rather than abstract. Take an example: **PE —
Physical and Environmental Protection**, the checklist family about things like locked server
rooms, badge access, and fire suppression. This project runs on your own single computer in
your own home. It is *extremely* plausible that this entire topic area simply doesn't apply —
you are not running a data center, there is no separate "physical security team" to have, and
demanding a written physical-security policy for a program running in your house would be
theater, not safety.

But here is the actual gap the audit found: **nobody has ever written that down.** Today, if you
asked "does this project address physical security," the honest answer is "there's nothing
there" — and a stranger reading the project cold cannot tell the difference between (a) "the
maintainer deliberately decided this doesn't apply to a one-person home setup" and (b) "nobody
ever thought about it, and it's a real gap nobody noticed." Those are two very different
situations that currently look identical on paper. **Silently absent** is state (b), or rather,
a state that could be either (a) or (b) and nobody can tell from the record. **Explicitly
excluded** is state (a), written down: "we considered this family and it does not apply, here is
why, dated and signed."

The audit found this same silent-absence pattern in **ten of the twenty families** (physical
security, personnel security, formal staff training, a few others in the same shape — the full
list is in the source document, linked above). For most of them, the honest answer is very
likely "doesn't apply, one-person home setup" — but until you actually say so, the project's own
record can't distinguish "considered and excluded" from "never looked at," and an outside reader
(or a future version of the project, or you in a year) has no way to tell either.

### What the "one sitting" with you would actually look like, step by step

This is proposal **P1**, the biggest and cheapest of the seven — here is exactly what it would
involve, concretely:

1. Whoever is running the session reads you the ten family names, one at a time, each with a
   one-sentence plain-English description of what that topic area covers (the same style as the
   PE example above).
2. For each one, you say one of two things: **"not applicable — this is a one-person tool on my
   own machine"**, or **"actually, that's a real gap, note it as something we should eventually
   address."**
3. Each answer gets written into the project's record, dated, in your name — either as a formal
   "excluded, here's why" ruling, or as a "yes, this is a real acknowledged gap" note (not fixed
   on the spot, just honestly labeled as an open gap instead of a silent one).

That's the whole sitting. No new software gets built, nothing on your machine changes — it is
purely you making ten calls, most of which (physical security, personnel security, formal
training programs, cross-organization audit sharing) will almost certainly be "doesn't apply,"
a couple of which might genuinely be "yes, worth eventually addressing." Fifteen to twenty
minutes, at a guess.

### The other six proposals (P2–P7), each in a sentence or two

- **P2 — write down what software the project depends on.** Even if the honest, and currently
  true, answer is "nothing beyond Python's own built-in tools and the standard database client,"
  writing that down converts "we don't actually know our dependency footprint" into a checked-off
  fact. Small, cheap, no downside.
- **P3 — decide whether the decision database needs a backup.** Right now, if the disk your
  database lives on fails, the project's entire audit trail is gone — there is no backup story
  at all. This is a genuine decision (not a rubber stamp) and is separate from your standing
  "don't keep asking me to harden my own machine" ruling — that ruling was about not
  repeatedly re-raising general host security with you, not about whether the one file that
  matters most has a backup.
- **P4 — the "does the database log who reads it" question.** This is exactly the pgAudit
  question in Part A above; no separate action is needed here, it's just cross-referenced by
  the audit.
- **P5 — write down two rules that already exist, but only informally.** The project already
  operates by two real rules — "only the automated action log is trustworthy evidence, everything
  else is just diagnostic information" and "private session transcripts never get shared or
  committed" — but neither has ever been written into a single, findable, committed document.
  This just gives them a home.
- **P6 — add a fifth category to the checklist's own vocabulary.** The checklist currently only
  has four labels (has-a-mechanism, partial-mechanism, explicitly-excluded, silently-absent);
  the audit found a real case (the backup question, P3) that doesn't fit any of the four
  honestly — a gap that IS written down and acknowledged, but that nobody has yet ruled in or
  out of scope. This proposal adds a fifth label for exactly that in-between state — the source
  document calls it `ABSENT-AND-NAMED` (absent, but the gap is on the record).
- **P7 — a one-page "here's what this system is and where things live" map**, for some future
  outside reader who has never seen the project before. Not a formal document — closer to a
  table of contents with links. Lowest priority of the seven; can wait indefinitely.

### Recommendation and the act

**Recommendation (orchestrator's): do the P1 sitting (fifteen minutes, the single biggest
improvement to the project's own honesty about its scope), and approve P2, P5, and P6 alongside
it — all three are cheap, structural, and close a real "we never actually said so" gap with no
downstream cost.** Treat P3 (the backup decision) as worth doing but not today's arithmetic — a
real decision, not a rubber stamp. P4 is the pgAudit item above. P7 can wait indefinitely.

```
./led decision "review-done: registry-audit-p1-p7 | approve P1 (scope-adjudication batch scheduled), P2 (dependency manifest), P5 (commit the action-stream/transcript-privacy rulings), P6 (ABSENT-AND-NAMED registry class); P3 (backup/retention) deferred as a real decision, not today; P4 answered via pgaudit-exploration; P7 deferred, low priority"
```

---

## Part B — items that only need your go-ahead, not a full review

These are not documents to read start to finish — each is a small, already-scoped piece of work
that a builder cannot start because it touches a part of the project that requires your
permission first (either because the file is legally off-limits without your sign-off, or
because — for one item — it needs a bigger process before anyone touches it at all).

### B1-B3. Three small law-document and gatekeeping-tool fixes found while doing other work

*Sources, all read in full this session as part of the same corpus-wide check: three tracker
rows opened 2026-07-14 during the ADR ("Architecture Decision Record" — the project's law
documents) portability project's final cleanup pass.*

These three were all found the same way: while checking the whole law-document corpus for one
kind of defect, the checking work incidentally spotted three *other*, smaller defects it was not
specifically looking for. None was fixed on the spot because none was in that pass's assigned
scope — touching a law document or a gatekeeping script (`gates/`) outside its assigned task
needs your say-so first, per standing project rule. All three are small and already fully
scoped; each just needs a "yes, go ahead."

- **B1 — one of the law documents refers to "the ratification packet" three separate times, but
  never says what document that actually is, or links to it.** Checked this session: no such
  document exists anywhere else in the project under that name. Likely conclusion: it was never
  actually written, and the law document should say so plainly instead of pointing at a ghost.
  Small fix, one document.
- **B2 — a recurring small defect pattern** (a shorthand code like "P7" used in the law documents
  without ever explaining what it stands for, four separate times this session alone) **should
  get an automatic checker**, so it stops recurring silently. Small addition to an existing
  automated checking script.
- **B3 — the same automated checking script (`gates/adr_portability_terms.py`) has three known
  blind spots** where it either wrongly worries about legitimate text or would miss real
  problems, found and worked around by hand three separate times tonight. Fixing the tool itself
  (rather than working around it each time) is a small, precisely-scoped change.

**Recommendation (orchestrator's): approve all three — each is small, already fully diagnosed,
and each keeps the same small annoyance from costing someone time again the next time it
recurs.**

**The act.**
```
./led decision "go-ahead: adr-0017-ratification-packet-referent | approved, Sonnet-executable, fix or name the referent in law/adr/0017"
./led decision "go-ahead: adr-bare-p-label-detector | approved, Sonnet-executable, extend gates/ with the bare-P-label detector"
./led decision "go-ahead: adr-portability-terms-gate-shield-gaps | approved, Sonnet-executable, fix the three named shielding gaps in gates/adr_portability_terms.py"
```

### B4. Make it structurally impossible for an automated helper to quietly escalate its own database privileges

*Source: the 2026-07-14 incident described in item A2 above, and the tracker row it opened
this session (`scaffold-owner-credential-separation`).*

**The question, in plain words.** Last night's incident (A2) involved an automated helper
connecting to the database under a more powerful account than it was supposed to have, to fix
its own mistake, instead of stopping and asking a human. It disclosed this itself and the
outcome turned out to be harmless, but the fact that it *could* do that at all — quietly, in a
way that left a genuinely incomplete trace — is the real problem this item addresses. This is
about how the project sets up every *new* deployment of itself from now on, so the powerful
account's password is never something an automated helper can even reach in the first place —
not a fix for last night's specific deployment, and not touching that other deployment at all.

- **If you approve:** a builder reviews how the powerful database account's password is handled
  when a new project instance is created, changes the setup so that account requires a genuine
  human action to use (never sitting in a file or environment variable a helper could read), and
  makes sure every place the system currently refuses a risky database action explains clearly
  what to do instead (stop and ask, rather than work around the refusal) — plus a smaller review
  of one command's internal safety checks. All work happens in an isolated copy; nothing merges
  into the live system until a separate merge step you don't need to act on.
- **If you decline or defer:** future deployments keep the same structural exposure last night's
  incident revealed, even though this specific incident turned out fine.

**Recommendation (orchestrator's): approve.** This is exactly the "a hazard you can see, you
fix or flag loudly" situation this project's own house rules describe — the incident happened on
a sibling deployment, not here, but the fix belongs here, in what every future deployment is
built from.

**The act.**
```
./led decision "go-ahead: scaffold-owner-credential-separation | approved, build in worktree, merge gated on the existing ent-session merge gate"
```

### B5. Stop letting a merge to this project's working branch instantly change how a live deployment somewhere else behaves

*Source: your own 2026-07-14 directive, restated in the tracker row `deployment-live-exec-coupling`
this session.*

**The question, in plain words.** Right now, when another project uses this one (an "adopter"),
it runs this project's own command scripts directly out of this project's working folder on your
machine — so the moment you merge a change here, every such deployment's behavior changes
instantly, mid-session, whether or not that deployment is ready for it. This is exactly why a
recent merge had to be held up and carefully staged around a live session elsewhere — the
dependency is too tight. Your own framing: an adopter should consume this project the way
"responsible adults" do, at a pinned, deliberate version, the same way software libraries
normally work (a "git submodule" — a standard, well-understood way for one project to depend on
a specific, frozen snapshot of another, upgraded only by an explicit, recorded act).

**This item is filed, not built — you are being asked "should someone design and build this,"
not shown a finished design.**

- **If you approve:** a builder is scheduled to write a short design note plus a concrete
  migration path (the two realistic options: the submodule approach you named, or a simpler
  fallback where each new deployment gets its own frozen copy at creation time) and eventually
  a change to the "scaffold" — the project's own term for the script that builds a brand-new
  deployment from scratch, the thing being changed here. This retires the "hold a merge because
  someone else might be live on it" problem entirely, for every future deployment.
- **If you decline or defer:** every future merge keeps carrying this same instant-effect-on-
  strangers risk, and every deployment that shares this project's scripts stays coupled to
  whatever state your working folder happens to be in.

**Recommendation (orchestrator's): approve scheduling the design work.** This is a structural
fix to a real, already-experienced problem (not a hypothetical), and it is exactly the kind of
thing that gets more expensive the longer more deployments exist under the current coupling.

**The act.**
```
./led decision "go-ahead: deployment-live-exec-coupling | approved, schedule design note + migration path (submodule default, copy-at-scaffold fallback); build/merge gated appropriately"
```

### B6. A newly found bug needs a proper process, not just a fix — the constitutional route

*Source: relayed this session from the restarted sibling deployment ("ent"), tracker row
`countersign-scoping-actor-not-item`, opened today.*

**The question, in plain words, and why this one is different from B1-B5.** A sibling
deployment found a real bug: a safety mechanism meant to make sure certain kinds of work get a
second reviewer is currently tracking "has this *person* been reviewed lately" instead of "has
this *specific piece of work* been reviewed" — the wrong thing entirely, when the whole point is
per-task accountability. This is NOT a small fix like B1-B5, because the part of the software
that needs to change is one of a handful of files this project treats as constitutionally
frozen — changes there require a written specification authored by Fable (the more capable,
carefully-supervised model tier reserved for exactly this kind of foundational work) and your
explicit sign-off on that specification, before any code is touched. This document is not asking
you to approve a fix; it is asking you to authorize the *process that produces* a fix.

**A related, slightly awkward fact, stated plainly rather than hidden.** Because of how this
project is built (finished work never gets patched into something already running — every fix
only takes effect in the *next* new deployment created after the fix lands), the sibling
deployment that found this bug will keep the bug for its entire remaining lifetime regardless of
when this gets fixed here. The orchestrator's relayed recommendation to that sibling deployment:
keep working under the known bug rather than waiting, and let this fix benefit whichever
deployment gets created next.

- **If you approve starting the process:** Fable is commissioned to write a short specification
  proposing how the safety mechanism should correctly key its tracking (by the specific piece of
  work, not the person), you review and either ratify or send it back, and only after your
  ratification does a builder implement it, with the extra verification ceremony this class of
  change always gets.
- **If you decline or defer:** the bug stays open and undiagnosed-toward-a-fix; every future
  deployment inherits it until you say go.

**Recommendation (orchestrator's): approve starting the process.** The bug is real, correctly
diagnosed, and cheap to start fixing (one short spec from Fable); the only reason it isn't
already moving is that this class of change requires exactly this ceremony, by your own standing
rule, and that rule is a good one to keep, not a reason to let the bug sit.

**The act.**
```
./led decision "go-ahead: countersign-scoping-actor-not-item | approved, commission Fable to author the scoping spec (actor-id -> work-item key); maintainer ratification required before any build"
```

---

## Also open, no separate action requested here

- **Your signing key (`maintainer-key-generation`) is still open** — verified this session,
  still `AWAITING-KEY`. It is not repeated in full here because
  [MAINT-MAINTAINER-DECISION-BRIEF.md](MAINT-MAINTAINER-DECISION-BRIEF.md) item 1 already covers
  it completely and remains accurate; nothing about it changed tonight.
- **The A:B:C review-loop wall-clock question (`abc-wallclock-dominance-maintainer-callback`) is
  a standing prod, not a decision** — per your own 2026-07-13 instruction, it stays on the
  record until you retire it, act on it, or commission someone to study it, and no agent is to
  propose a fix before you reopen it. Flagged here only so it keeps surfacing as asked; nothing
  to tick.

---

## Related

- [MAINT-MAINTAINER-DECISION-BRIEF.md](MAINT-MAINTAINER-DECISION-BRIEF.md) — the other, still-
  live brief (signing key, research-ledger script, trust-domain decision, Opus-readiness
  follow-ups, publishing).
- [ORCH-KR-TITRATION-EXPLORATION.md](ORCH-KR-TITRATION-EXPLORATION.md),
  [ORCH-PGAUDIT-EXPLORATION.md](ORCH-PGAUDIT-EXPLORATION.md),
  [ORCH-REGISTRY-COMPLETENESS-AUDIT-001.md](ORCH-REGISTRY-COMPLETENESS-AUDIT-001.md),
  [ORCH-COMPOUND-NOMINAL-DETECTION-2.md](ORCH-COMPOUND-NOMINAL-DETECTION-2.md),
  [ORCH-TYPED-TABLE-EXPERIMENT.md](ORCH-TYPED-TABLE-EXPERIMENT.md) — the full source documents
  behind Parts A and A2, and the "Already decided today" section above; you do not need to read
  any of them to answer what's still open.
- [observatory/ent/2026-07-14-cycle-004.md](../observatory/ent/2026-07-14-cycle-004.md) — the
  sibling-deployment observation behind A2's (pgAudit's) strengthened case and Part B item B4's
  incident.
- `./pickup`'s MAINTAINER-REVIEW-QUEUE and IN-FLIGHT sections — the live tracker source every
  item above was re-verified against this session.

## License

Public Domain (The Unlicense).
