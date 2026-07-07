# Review fixed-point protocol — iterate to zero undisposed findings (maintainer proposal + Fable design, 2026-07-07, post-e17)

Maintainer proposal, verbatim core: "a fixed-point protocol where the agent is required to
run an independent review -> fix until the review comes back essentially with the verdict
'flawless' ... care would have to be taken that the reviewer be mindless about prior fixes
so it's not biased into thinking 'oh, they already fixed so much so it must be flawless at
this point'." Motivating specimen: e17, where one genuinely independent review (entry 17,
stamp-distinct) caught a real defect (28-digit Decimal ceiling) that the author's own
verification (entry 11) had passed.

## The criterion is structural, never verbal

The fixed point is NOT the verdict "flawless" (subjective; inflatable; presses the
reviewer toward one of two opposite biases — history-anchoring ["so much fixed already"]
or nit-manufacturing ["a clean verdict looks lazy"]). The fixed point is: **a fresh
review of the final artifact version produces ZERO findings that survive disposition.**
- Review findings carry a reproducible basis (review_detail.basis) — the check on
  manufactured nits.
- Dispositions are actor-attributed acts (the findings idiom, per-unit) — author waves-off
  are visible, not silent; a waive needs a ruling ref as everywhere else.

## Two review species, only one terminates the loop

- **delta-review** — same reviewer, briefed on the fix, verifies it landed. Cheap,
  directed, ANCHORED BY CONSTRUCTION. Allowed as a gate on the fix itself; never
  terminates the loop. (e17's terminating attest, entry 18, was this species: same
  reviewer, author-supplied checklist. Under this protocol e17 would still owe one
  criterion-review — the maintainer's bias instinct, validated by the run that
  motivated him.)
- **criterion-review** — FRESH FIRST-CONTACT invocation: its stamp has never appeared in
  the unit's history (checkable mechanically from stamps + acts stream, no new
  machinery); brief = artifact + spec + fixtures ONLY — no fix narrative, no prior
  verdicts, no round number. Perfect brief-blindness is not enforceable (the reviewer
  could read the ledger); the brief is a recorded act and divergence is acts-visible —
  the standing tripwire-not-authentication posture.

## Elevation — three layers (the two-tier posture ruling, applied)

1. **Kernel, write-time (EXISTS):** stamps make each review's independence claim true or
   refused (F53). Nothing loop-shaped belongs in triggers.
2. **Close manifest, enforcement (BUILD):** `review_fixpoint` line — a completion claim
   for a unit under this policy is RED unless the FINAL artifact version carries an
   attesting review that is (i) stamp-distinct from the author, (ii) first-contact
   (stamp unseen earlier in the unit), (iii) zero undisposed review-findings. Three
   derivable joins.
3. **Orchestration, the loop (POLICY/WORKFLOW):** while-loop spawning fresh reviewers
   until the criterion holds, calibrated per-unit by the three parameters below —
   a hard round-ceiling is mandatory because cost is a real constraint and an unbounded
   polish loop is a budget hazard, not a virtue.

## Calibration vocabulary (maintainer ruling, 2026-07-07 — e18 ratification forward)

Three knobs, named apart, **full words only** — the one-letter "K" spelling is RETIRED
as same-spelling-drift (the semantics-refutation class: "K" meant consecutive clean
rounds in this note's first draft and reviewers-per-round in consults 37/39 — one
spelling, two quantities). No single-letter or abbreviated spellings anywhere,
including in code. All three are per-unit calibration parameters in the future policy
library ([[policy-authoring-seam]]).

- **confirmation-depth** — consecutive clean rounds required to terminate the loop.
  Default 1 (first-clean-round semantics: a clean round from honest reviewers predicts
  the next; e18's noise-tail-zero specimen is the first calibration datum).
- **panel-width** — fresh first-contact reviewers per round. Default 1 at e-series
  grain; widen for thin in-run review depth or high stakes.
- **round-ceiling** — hard cap on TOTAL rounds, dirty ones included. Hitting it closes
  the unit RED-honest with its open findings, never auto-attested.

e18's criterion phase is recorded retroactively in this vocabulary:
confirmation-depth=1, panel-width=2, round-ceiling=1 (one round, two lens reviewers,
both attest — clean at the first round, terminated).

Attachment is per-unit via the policy-instance idiom — `review_fixpoint` should be among
the FIRST ratified patterns in the policy-authoring-seam library
([[policy-authoring-seam]]: instantiation as data rows, both-polarity control fixtures).
ADR-0014 (executor second opinion) generalized from one opinion to convergence.

## Open empirical question (do not assume; measure)

Whether fresh first-contact reviewers keep finding REAL flaws round over round — or the
tail is noise — is unmeasured. Natural future e-lever: fresh-blind vs directed re-review,
convergence depth distribution. e17 banked round one (one fresh review, one real defect).
N=1 discipline applies: e17 is a specimen, not a rate.
