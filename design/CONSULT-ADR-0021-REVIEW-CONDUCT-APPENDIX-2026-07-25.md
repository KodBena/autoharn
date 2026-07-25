# Proposed appendix to ADR-0021 — review-conduct points (ADR-0018 consult edition)

<!-- doc-attest-exempt: ADR-0018 consult deliverable, authored 2026-07-25 by a fresh-context
Fable instance commissioned under law/adr/0018-consults-are-not-front-loaded.md (the consult
received the witnessed problem, the campaign evidence, and the governing law — deliberately
not the commissioning orchestrator's postmortem or the parallel candidate appendix). It is a
proposal menu awaiting the maintainer's cherry-pick into ADR-0021 before that ADR is
ratified. Removal condition: strike this marker when the maintainer's cherry-pick disposition
is recorded — points merged into ADR-0021 live there under its own attestation; this file
then stands as the dated consult record. -->

This document proposes review-conduct points for the appendix the maintainer commissioned
against the ADR-0021 draft (`law/adr/0021-the-checked-surface-is-the-shipped-surface.md`):
generic guidance for a working reviewer — things easy to miss or forget under load — drawn
from the 2026-07-23 review campaign (ledger rows 1228–1260: five delivery batches, ~20
fresh-context adversarial review laps, 8 fix rounds, repeated severe findings in work that
arrived "done, witnessed, gates green") and from named review craft. Per the commission it
deliberately does NOT restate ADR-0021's Rule A (checked surface = shipped surface), Rule B
(comments asserting safety properties are claims), or the subsidiary carve-out-predicate
clause; it generalizes around them.

Format, for cherry-picking: each point is numbered, self-contained, and independently
mergeable — an imperative a reviewer can execute, a one-line reason, and its grounding
(campaign evidence with the ledger row, or named craft, stated per point). No point depends
on another; order is presentational only.

---

**1. Before crediting any check's green, break the thing it guards and watch it go red.**
A check that cannot be made to fail is not evidence, whatever it prints.
*Reason:* the only proof a check observes anything is a witnessed failure.
*Grounding:* campaign — the umbrella dispatch-parity fixture stayed green after the reviewer
deliberately broke the dispatcher's exec line (row 1230); craft — mutation testing ("kill the
mutant"), the seen-red/ convention generalized to review time.

**2. Accept a "red-first" witness only if the red was observed against the actual defective
code.** A red produced by a contrived stand-in, or reconstructed after the fix, witnesses
nothing about the defect.
*Reason:* the value of a pre-fix red is that the defect itself, not a simulation of it,
tripped the check.
*Grounding:* campaign — the handshake red.txt was found to be "not a genuine pre-fix red"
(row 1230).

**3. Review a check's false-accept space: ask what else its acceptance predicate would
pass.** Feed it an imposter — a plausible wrong artifact, a sibling, a wrong-but-shaped
output — before trusting what it accepts.
*Reason:* a predicate is defined as much by what it fails to reject as by what it accepts.
*Grounding:* campaign, three independent instances — a health probe adopted ANY HTTP
responder including a 404 (row 1230); a verb file carrying another verb's implementation
passed every fixture case with plausible output and exit 0 (row 1250); sibling templates
printed identical usage markers, so a served-for-legacy swap passed the suite (row 1255).
Craft: discriminating power of assertions — an assertion that cannot tell the target from
its nearest plausible neighbor asserts nothing.

**4. Review a rewrite, rebase, or port from the predecessor's capability inventory, not from
the new code.** Enumerate what the old surface did; check each item present or deliberately
retired — absence never appears in a review of what is present.
*Reason:* diff-shaped review can only see what exists; feature loss is invisible in it.
*Grounding:* campaign — the rebased led CLI silently lost two whole guards (evidence
dereference, path-shaped-statement warning); the fixture reported "SPECIMEN INERT: the
behaviors it exists to witness no longer exist to exercise" (row 1245). Composes with
ADR-0020's meaning-preservation posture, applied to code capability rather than prose
meaning.

**5. Review every fix as new code under a full fresh pass, never as the discharge of the
finding it answers.** Checking that the named defect is gone is the smallest part; the fix
is the diff most likely to have been authored under pressure, in code just proven hazardous.
*Reason:* the campaign's fix rounds repeatedly introduced new severe defects the prior lap's
findings did not name.
*Grounding:* campaign — "the lap-2 finds are new defect instances, not round-1 residue"
(row 1250); a round-1 fix itself unlinked the winner's live pidfile (row 1250). Law:
ADR-0012's 2026-07-02 amendment, "a corrective diff IS new structure."

**6. Grade findings by silence, not by size.** A moderate whose failure mode is a silent
wrong answer (silent misparse, wrong-target action, false success) outranks a severe-looking
defect that fails loudly and honestly; calibrate iteration effort accordingly.
*Reason:* a loud defect costs a diagnosis; a silent one costs whatever was built on the
wrong answer before anyone noticed.
*Grounding:* campaign — the ratified strengthened tier holds an axis open on
silent-wrong-answer moderates and lets loud-and-honest moderates through (row 1231);
composes with ADR-0002's hierarchy read from the reviewer's side.

**7. Treat a severe finding as a claim: execute it before it blocks a merge or ships a fix.**
Reproduce the failure against the real habitat where permitted, or by simulation named as
such; a finding that cannot be exercised is reported as suspected, not confirmed.
*Reason:* reviews are subject to the same witness discipline as the work they judge, and a
false severe spends fix-round capacity the true ones need.
*Grounding:* campaign — the trio severe was "CONFIRMED AGAINST THE REAL ~/ent" and the
gitignore false-idempotence "confirmed by simulation" before dispositions were made
(row 1230).

**8. Report the negative space with the findings: axes that cleared, refutations attempted
that held, and surfaces left unexercised with the concrete blocker.** A review reporting
only hits cannot be told apart from one that looked at nothing else.
*Reason:* the consumer of a review needs its coverage, not just its catches, to know what
the green means.
*Grounding:* campaign — cleared axes and held refutations were recorded per lap
("Sourcing/quoting/fixture-weakening refutations all held", row 1230; docs axis clears and
drops out, row 1250); house law — the WITNESSED / REFUSED-AS-EXPECTED / UNEXERCISED
reporting rule (CLAUDE.md, claims carry witnesses).

**9. Review the delivery against the commission before reviewing the diff against the
delivery — and convert the builder's own PARTIAL list into tracked items, not goodwill.**
Undelivered scope hides in the gap between what was asked and what the report answers.
*Reason:* a diff review can be flawless while the commission is half-done; an honest
stop-and-name only helps if someone files it.
*Grounding:* campaign — the umbrella delivery's self-declared partials (a)–(e) each became
review axes or follow-on work items rather than dissolving at merge (rows 1228, 1257).
Craft: requirements traceability.

**10. Review tests and fixtures as actors with a blast radius: their isolation from
production must hold by construction, not by circumstance.** Ask where a test CAN write —
under a wrong cwd, an inherited environment, a stale resolution path — not where it is
observed to write on the happy path.
*Reason:* a fixture that reaches a real store only by accident today reaches it again on
every future accidental alignment.
*Grounding:* campaign — a seen-red fixture wrote eight probe rows into the live kernel
because its deployment resolution reached the real boundary; its own docstring showed it
was designed to (rows 1237–1244, 1248, 1251); the repair was structural refusal (tempdir +
repo-containment), not care (row 1253).

**11. Flag every hand-maintained enumeration of facts owned elsewhere — a roster, a count, a
list of verbs or files — even when it is currently accurate.** Ask where the authoritative
set lives and whether this copy is derived or re-typed.
*Reason:* a correct hand copy is a drift seam armed for the next change to the authority.
*Grounding:* campaign — a hand-typed ten-verb roster reopened a count-drift seam the project
had already paid for once (row 1230); law — ADR-0012 P1 (derive, don't duplicate), read at
review time.

**12. Quantify every descriptive sentence shipped in the change: for which targets, worlds,
and times is it true, and do its referents exist?** Docstrings, doc edits, and help text are
part of the diff; check named artifacts on disk and check universally-phrased sentences
against every member of their quantification universe, not the instance in front of the
author.
*Reason:* an unscoped true-here sentence is a false sentence everywhere else, and a
reference to a nonexistent artifact fails the first reader who chases it.
*Grounding:* campaign — a CLAUDE.md sentence unscoped and false for every newborn world; a
docstring claiming fixtures that exist nowhere; another claiming a git-absent fallback that
does not exist (rows 1230, 1236). Law: ADR-0000's quantification-universe discipline,
brought to prose.

**13. When a mechanical guard refuses your own act mid-review or mid-merge, treat the
refusal as the system working: route the act to its proper principal, never work around.**
Record the refusal as evidence the guard is live.
*Reason:* the reviewer who bypasses a guard "just this once" deletes the guard for everyone,
and the moment of an inconvenient refusal is exactly the moment guards exist for.
*Grounding:* campaign — the harness refused a hooks-touching merge to the orchestrator; the
refusal was "accepted as the correct mechanical enforcement of the standing hooks rule, not
worked around," and the merge became a prepared operator act (row 1236).

**14. Audit the review's own report before delivering it: every attribution, commit range,
and claimed retirement in it is checked the way the report checked the code.** A wrong
statement in a review is a defect of the review.
*Reason:* the report is the artifact downstream decisions consume; an inaccurate record
misdirects the fix round it commissions.
*Grounding:* campaign — a batch report claimed case retirements "not found in the commit
range"; the fix round included an attribution correction with the note "record must end
accurate" (row 1251).

**15. Do not let "merged" stand in for "reviewed": review debt survives merge, and a severe
found post-merge becomes a fix-forward on the record, not a quiet patch.** When the bar
tightens, apply it retroactively to recently merged work.
*Reason:* the defect does not know it was merged; suppressing a post-merge finding to
protect a clean history converts one defect into two.
*Grounding:* campaign — post-merge blind review was dispatched for already-merged commits
under the tightened bar and confirmed a real severe against a real deployment, dispositioned
as a reviewed fix-forward (rows 1229, 1230, 1233).

**16. Exercise the merged artifact in its live habitat promptly, and treat the first live
run as review evidence.** Watch the first real invocation; a refusal, a skew catch, or a
recovery path firing there is data no pre-merge lap can produce.
*Reason:* the live habitat holds state — running services, old versions, real
deployments — that no worktree reproduces.
*Grounding:* campaign — minutes after merge, the new CLI's version handshake correctly
refused the still-running old service, and doctor's new consistency line named it; the
taught recovery was followed and witnessed (row 1257). Craft: post-deployment verification
as part of the change, not operations' problem.

**17. When a fix makes code a correct outlier among similar-looking neighbors, require an
adjacent marker naming the deliberate divergence and warning against harmonization.** Review
the fix for what a future tidier will see: N-1 files doing X and one doing Y.
*Reason:* an unmarked correct outlier is one well-meaning cleanup away from reverting to the
defect it fixed.
*Grounding:* campaign — the staged-read gate's deliberate divergence from its tree-reading
neighbors got an explicit do-not-harmonize comment precisely to "guard against a future
editor reintroducing the silent false-success" (row 1236).

**18. Converge on a clean lap, never on a lap count: a lap that finds proves the class is
present in the process, not that it caught the last instance.** After fixes, a fresh
reviewer — blind to the prior lap's findings — reads again, until a lap finds none at the
declared severity.
*Reason:* finding-sets across laps were pairwise disjoint; stopping after N laps because N
felt sufficient would have shipped whichever classes lap N+1 was going to catch.
*Grounding:* campaign — the umbrella parity axis needed five laps, each finding strictly
narrower (whole-fixture absence → content swap → shared boilerplate → sibling marker
collision) (rows 1250, 1255); the same iterate-to-clean shape ADR-0020's second subsidiary
clause ratified for meaning witnesses, applied to code review.

---

*End of proposed points. Eighteen, independently mergeable; the maintainer cherry-picks.*
