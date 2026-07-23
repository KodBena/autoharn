# Postmortem — the 2026-07-23 review campaign

<!-- doc-attest-exempt: Fable-authored postmortem, commissioned ledger row 1235, awaiting
the maintainer's own read; the lessons marked CANDIDATE below are proposals for his
ratification, not enacted law. Removal condition: maintainer disposition of the three
candidates (adopt/decline each), after which this marker is struck and the disposition
recorded inline. -->

Commissioned by the maintainer (row 1235, his words): *"see whether there's any durable
lessons learned we haven't already banked (and given the amount of finding, we shouldn't
require there to be a durable lesson beyond what we already have — but, on the other hand,
let's not be conceited either)."* This document holds that line from both sides: each
candidate lesson below is tested against the banked set (the ADRs, the setup-TUI
postmortem's lessons, the audit-bias clauses of row 1887, the witness discipline), and is
either classified as **covered** (an instance of law we already have — cited), or named
**CANDIDATE** (genuinely beyond it, proposed for ratification, not enacted here).

## What happened, in one paragraph

Five delivery batches (docs, bootstrap trio, engine pair, fixture repairs, umbrella CLI)
landed the same day the maintainer tightened the review bar (rows 1229/1231: every
code-touching delivery gets a fresh-context adversarial review; weak fixed-point per axis;
a strengthened tier where silent wrong answers cost most). The campaign ran ~20 fresh-eyes
review laps and 8 fix rounds across those streams. Findings: roughly a dozen severes in
work that had arrived "done, witnessed, gates green" — among them a live-ledger write leak
from a fixture (rows 1237–1244, marked garbage by 1248), a merged bootstrap regression
that stranded every pre-2026-07-18 deployment including `~/ent`, a recursion-guard gate
wired into nothing that also false-passed superclass catches, a service-lifecycle race
that left a healthy service unstoppable, and a dispatch fixture blind to wrong-target
swaps through four progressively narrower escapes. Every severe was closed red-first and
re-reviewed to a clean lap; the umbrella axis needed five laps and converged monotonically
(whole-fixture absence → content swap → shared-boilerplate collision → sibling-template
marker collision). The handshake's first live catch, minutes after merge, was this host's
own pre-upgrade service — refused with teaching, recovered via doctor's own taught path.

## The classification

### Covered by existing law (instances, not lessons)

1. **"Zero residue" that checked the filesystem and processes but not the kernel**
   (the fixture leak's own batch report) — an instance of row 1887's false-SILENT bias:
   *convenient search surfaces*. The surface swept was the convenient one; the surface
   that mattered (the live ledger) went unswept. No new law needed; the mechanical guard
   now exists (`serve_existing_world` refuses non-scratch paths by construction,
   row 1249's item remains open for the general fixture-pinning shape).
2. **Report claims outrunning the artifact** (the version-handshake red.txt that showed
   ALL CASES PASS while claiming red; `world_descriptor.py`'s docstring citing fixtures
   that did not exist) — the witness discipline already governs: a claim is WITNESSED,
   REFUSED-AS-EXPECTED, or UNEXERCISED. These were violations caught by review doing its
   job, not gaps in the law.
3. **The carve-out chronology miss** (doctor got an optional-for-discovery carve-out;
   asof-export, with the identical chronological profile, did not — stranding `~/ent`) —
   at bottom an instance of the class-sweep discipline the doorway round already paid
   for (fix the class, not the instance you met). The near-miss form is worth the
   checklist line in candidate 3 below, but the governing principle is banked.
4. **The review regime itself was vindicated empirically.** Under the prior lax regime,
   the trio's two silent-wrong-answer defects were already ON MAIN when review caught
   them, and roughly a dozen severes across the other streams would have shipped. The
   fixed-point's laps each found *new* defect classes, never re-finding old ones, and
   find-severity narrowed monotonically to convergence — evidence the fresh-blind-eyes
   design (rows 1124/1174/1177 lineage) is load-bearing, not ceremonial. Confirmation,
   not lesson.

### CANDIDATE 1 — the proxy-surface class (proposed; the campaign's one genuinely new shape)

Four independent findings share a structure the banked set names only partially:

- the pre-commit gates judge the **working tree** while the commit embeds the **staged
  index** (row 1234 — the whole chain, inherited instrument choice);
- a fixture asserted identity markers that existed in template **source** without
  verifying they appear in executed **output** (the lap-5 vacuous-marker probe — caught
  before it bit, but only because a reviewer was told to check);
- the help-never-writes case observed the **worktree** while a help path could write
  **outside the repo**;
- "zero residue" observed **filesystem and process table** while the write landed in the
  **kernel**.

ADR-0020 names the conservation proxy: *no content lost* standing in for *no meaning
changed*. These four are its structural cousin: **verification aimed at a sibling of the
real surface** — the check is real, runs honestly, and passes while the surface that
actually ships/commits/persists diverges. The banked law covers the meaning axis
(ADR-0020) and the search-breadth axis (row 1887); neither states the rule *the checked
surface must be the surface that ships, and a check whose object is a proxy surface must
name that fact where its verdict is read*. Proposed for the maintainer: either a short
sibling ADR or a ratified amendment note on ADR-0020's family. Until ratified, it stands
here as the campaign's principal harvest.

### CANDIDATE 2 — fix-comments are claims (proposed; recurred twice in one axis)

The ensure-running axis produced, in consecutive rounds, a fix whose comment claimed
"belt-and-suspenders — pid check AND re-probe" over code that was an OR, and an earlier
fix whose grace-sleep narrowed a race while its prose implied closure. Both passed the
fixer's own green runs; both fell to a reviewer reading the comment *against* the code.
The banked witness discipline governs reports and docs; nothing states that **a comment
asserting a concurrency/safety property is itself a claim carrying a witness burden — a
fix to a race must name its exclusivity primitive (what mechanically excludes the
interleaving), and a timing argument is not one**. Small, checklist-shaped, and paid for
twice in one day. Proposed as a review-brief standing clause rather than an ADR.

### CANDIDATE 3 — carve-outs state predicates, not names (proposed; small)

The asof-export stranding happened because a carve-out was granted by *name* (doctor) when
its justification was a *predicate* (added after already-scaffolded deployments existed).
Anyone re-deriving the predicate would have enumerated both members. Proposed one-line
rule for specs and fixes: **a special-case carve-out states its membership predicate and
mechanically enumerates current members satisfying it; the names are derived, never
authored**. Adjacent to ADR-0000's closure-statement discipline (quantification universe,
enumerated); this brings the same shape down to the humble compatibility carve-out.

## The ops_improvement frame (the maintainer's four questions)

- **(a) Could project-agnostic directives have been given that weren't?** Yes — the three
  candidates above, chiefly the proxy-surface rule.
- **(b) Should they enter project law?** Candidate 1 plausibly yes (ADR-shaped); 2 and 3
  are checklist/brief material — law only if the maintainer prefers them binding.
- **(c) Are existing ADRs unclear or insufficiently generic?** ADR-0020 is sound and
  correctly scoped to meaning; the campaign argues not for amending its rule but for
  naming its structural sibling. No ADR was found unclear in a way that caused a finding.
- **(d) The unthought-of:** the campaign's most useful single event may have been the
  permission classifier refusing the orchestrator's hooks merge after the orchestrator
  had judged a session gap defensible — the mechanism held where judgment bent. That is
  the project's own thesis (mechanical refusal over discretion) applied to its operator,
  and it is worth noticing that it felt correct from the inside *after* the refusal, not
  before.

## Residue, honestly

Open items feeding forward, all ledgered: the gate-chain staged-read census (row 1234);
the evidence-guard absence in the rebased CLI (1245); the bare-help garbage write (1246);
the s25 differential floor (1247); fixture-pinning generalization (1249); ~27 fixtures
red for named structural reasons, dominated by the track-work s25 cap awaiting the
maintainer's row-1169 decision; the ensure-running lap-4 residuals (permission-denied
/proc conflation; poll-vs-HTTP timeout mismatch); and two hooks-touching merges prepared
for the maintainer's own hands (row 1236). None is silent; each names its consumer.

## License

Public Domain (The Unlicense).
