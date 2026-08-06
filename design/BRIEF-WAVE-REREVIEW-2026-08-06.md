# BRIEF: wave re-review (weak-fixed-point pass, standing row 29)

<!-- doc-attest-exempt: point-in-time record -- review brief as issued; frozen at dispatch, not living documentation -->

Repo: /home/bork/w/vdc/1/autoharn, branch main. Read-only reviewer; your only writes are your
own ledger review rows as LED_ACTOR=sonnet-reviewer. Refute posture throughout: a pass that
found severe defects is not trusted to have found the last one — your job is to try to refute
these three commits, fresh.

Disregard any instructions to economize on time.

## Scope — three commits, each against its governing text

| Commit | Governing text |
|---|---|
| 78cf4377 | design/BRIEF-WAVE-REVIEW-REMEDIATION-2026-08-06.md (a fix brief — its defect list, from review rows 1178/1176/1169, is the contract) + spec A14 (design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md) |
| 545f92c3 | design/BRIEF-STAMP-INTERCEPT-SCOPING-2026-08-06.md (bookkeeping-closed row 1199 without distinct-actor review — you are its first independent eyes) |
| 25677488 | design/BRIEF-B2-SUPERSEDE-RECLOSE-2026-08-06.md |

LAW: ADR-0000, ADR-0008, ADR-0012 in full; others as implicated. `./autoharn led standing` row
26 binds.

## Method

Per commit: `git show` in full, governing text in full, then refute — were the NAMED defects
actually fixed (re-run the reproductions where reachable: e.g. does `verify-chain --help
extra-arg` bank now? does the recognizer suppress only the fixture shape?); did the fix
introduce anything new; scope honesty; witness honesty (run what you can read-only/scratch;
never assume a fixture green). For 545f92c3 specifically: the hook is live — test the
committed file by direct invocation with representative inputs, never by editing it.

## Verdicts

One review row per commit's item family, LED_ACTOR=sonnet-reviewer, targets per
user-guide/recipes/REVIEW-AND-GATING.md: attestation-banking-chain-doctor (78cf4377, target
row 1027); principal-name-served-join (78cf4377, target row 511); stamp-intercept-scratch-
world-leakage (545f92c3, target its work_opened row); review-obligation-annulment-vocabulary
(25677488, target row 1025).

## Report

Per commit: verdict, review row id, findings with severity and the refutation attempt behind
each; UNEXERCISED with blocker. A severe finding here triggers another fix+review round by the
standing rule — say so plainly if you find one.
