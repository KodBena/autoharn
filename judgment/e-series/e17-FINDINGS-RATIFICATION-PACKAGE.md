# e17 FINDINGS ratification package — RATIFIED (maintainer paste, Increment 11)

Assembles the e17 analysis's proposed findings, their dispositions, and the conformance-map diff, for the
record. The maintainer RATIFIED the dispositions by the Increment-11 paste; this package records the
ratified state (assembly, not grading — grading was the odd link's, consult 35).

**Primary source (verbatim, do not paraphrase):** `consults/e17-analysis-consult-35.md`, commit `e691b04`,
anchored `acts.ruling id 37`. Its §1 (primary measurement), §2 (ride-alongs), §3 (synthesis, incl. the
five proposed findings and the e18 recommendation) are authoritative; summaries below are pointers.

## The five findings — RATIFIED dispositions

| # | finding (id) | disposition | foreclosure / basis |
|---|---|---|---|
| (a) | 38 partial-review-stub-seam | **filed** | kernel fix candidate (atomic review+detail / extend refuse-and-teach to a foreign-principal review row); whether it enters s18 is decided at e18 elevation |
| (b) | 39 binder-batch-insert-artifact | **fixed** | fc21 `binder-bind-many` — row_performed_by binds one act to many rows (key-occurrence counting); both-polarity fixture + seen-red |
| (c) | 40 compose-live-file-at-delivery | **fixed** | fc23 **waived-discipline** — standing line in the delivery protocol (file_resolution header); a ruled discipline, not a mechanical gate (an unfiled delivery isn't detectable without a close-line join not commissioned); backstop = delivery_freight_integrity |
| (d) | 41 ambiguity-pre-test-gap | **filed** | rides the next clean-spec authoring: an ambiguity pre-test (e16 adversarial-pre-test machinery retargeted to ambiguity-finding) |
| (e) | 42 gate-journal-registration-gap | **fixed** | fc22 `gate-journal-registered` — arm-time check refuses arming a target absent from contemporaneity SESSIONS+GATE_JOURNALS; seen-red = e17, the unregistered specimen |

Foreclosure state after: `foreclosure_debt` GREEN (no fixed finding owes a foreclosure).

## §0 erratum (consult 35, recorded — a trailer correction, not a finding)

My Increment-10 trailer mis-mapped ledger id 15. Correct (consult 35 §0): the refused-DETAIL review INSERT
landed as row 12 (per-statement autocommit; only `review_detail` was refused, consuming no ledger id). Id
15 was consumed by act 498 — a re-verification insert whose `enacts=ARRAY[15]` referenced a nonexistent
row (typo for 14), refused, retried correctly at act 504 → row 16. TWO refused-insert events, different
causes; both id-is-order-clean.

## Conformance-map diff through e17 (commit `1ef0afa`)

- **I2** subject rows: self-declared → **mechanized** (interception stamps bind the true invocation).
- **I6** independence: built-unexercised → **mechanized + EXERCISED live** (F53 refuse-and-teach; rows 12/17/18).
- **G7** independent check on subject work: open → **exercised once** (real author-missed defect caught) +
  the `review_fixpoint` criterion built.
- **I3/I4/I5**: append_only_integrity live line, delivery_freight_integrity, delivers-FK, organic
  answers/amends/supersedes exercised.
- **I7**: subject now authors assumptions; validity BOUNDS still unexercised subject-side (said so).
- **I12**: finding-36 substrate resolution + gate-journal-registered arm check.
- Every remaining item is a declared exclusion with a reason or J-boundary — no silently-open row.

## e18 (consult 35 §5) — GO once this pass lands

Three candidate levers, odd-link preference order: **(i) the review-fixpoint CRITERION measurement**
(fresh first-contact reviewer vs directed re-review — e17 banked round one; the `review_fixpoint` line
built this increment mechanizes the criterion, gates nothing yet); (ii) discharge/obligation provoked
(the fence consult 33 deferred); (iii) stamp-enforcement widening beyond `review`. One lever, whichever
is chosen.

## What the maintainer's pass has done / what remains

Dispositions ratified (this paste). Remaining for e18 elevation: the (a) kernel-fix s18 decision; the
e18 lever choice; the review_fixpoint attachment via the policy-authoring-seam. Finding 34
(banked-report-ephemera, ratified-open backlog) stays open by design — it is the GLOBAL findings-gate RED
on any close until its referential-integrity gate is built (a future increment), not an e17 defect.
