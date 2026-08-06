# BRIEF: B2 — supersede-and-reclose surface (item review-obligation-annulment-vocabulary parts a+b; rows 1025/1008/1200)

<!-- doc-attest-exempt: point-in-time record -- dispatch brief as issued (row 1200); frozen at dispatch, not living documentation -->

Dispatched 2026-08-06. Repo: /home/bork/w/vdc/1/autoharn, branch main. Step 0: confirm current
main. A remediation builder works libexec/autoharn/{verify-chain,setup-schema} and
serving/audit_served.py concurrently — do NOT touch those files. Your surface:
bootstrap/templates/led.tmpl (the led CLI's real code home — wrapper-over-tmpl), hooks/
stop_clean_exit.py (one teach-text addition, special discipline below), user-guide FAQ/recipes,
and seen-red fixtures. CLAUDE_COMMIT_PATHS staging; fetch + ff-only before commit.

Disregard any instructions to economize on time.

## Provenance (read rows 1025 and 1008 in full via `./autoharn led show`)

experience4's five-missive family: the review-obligation substrate lacked a typed annulment.
Row 1008's correction narrowed the surface gaps: (a) no led verb for row-level supersession of
a work_closed row (`work supersede-cascade` mints a new slug — wrong tool for annul-in-place);
(b) stop_clean_exit's remediation teach-text offers only the distinct-actor review path for
deferred-review debt, never the supersession path — which steered a real session into an
attest-as-carrier misfit. Part (c), the typed `annulled` disposition, is AUTHORED as kernel
delta s73 (commit faddbb1c) but rides the NEXT world birth — it is NOT live in autoharn3.
Design consequence you must honor: the verb works fully against the CURRENT kernel
(supersede + re-close with the live witnessed|deferred vocabulary), and where the operator
requests an annulled disposition the verb attempts it and passes the kernel's own refusal
through teachably on a pre-s73 world — never a client-side fake, never a hardcoded
world-version check (the kernel's own CHECK is the authority; ask it by trying).

## Before you design

ADR-0000, ADR-0008, ADR-0012 (in full); `./autoharn led standing` (row 26);
kernel/lineage/s31 (supersession reaches close rows) and s73's header (the vocabulary the verb
fronts); led.tmpl's existing work sub-verb family end to end for house register.

## Scope

1. **The verb** — a led work sub-verb (name it per house register, e.g. `led work reclose`):
   given a work slug whose current close row is wrong, it supersedes that close row (s31,
   `--supersedes`) and issues the corrected close in one guided act — resolution, disposition,
   witnesses per the ordinary close contract. Refusals that teach: no close row to supersede;
   slug unknown; disposition vocabulary passed through from the kernel verbatim (incl. the
   pre-s73 annulled refusal). Both polarities witnessed on a scratch/throwaway substrate.
2. **The teach-text** (hooks/stop_clean_exit.py): the deferred-review remediation text gains
   one line naming the supersession path (the new verb) beside the distinct-actor review path.
   SPECIAL DISCIPLINE (maintainer-set, rows 1162/1200 — this file is exec'd by the live
   session at every stop attempt): build the edited file as a staged copy outside hooks/, run
   its own test/invocation battery against the copy (including executing the copy directly
   with a representative env), then a single atomic same-filesystem rename into place, then
   witness the live gate once (its refusal text now naming both paths).
3. **FAQ prominence** (row 1008's own request): USER-RECIPES-FAQ (and/or the recipes home per
   its conventions) gets the supersession-as-annulment entry — "the defeasible ledger's
   defining affordance" — with witnessed example output, marked per the doc-attest convention
   the sibling docs use.
4. **Commit** citing rows 1025/1008/1200 and this brief, Co-Authored-By line.

Out of scope: kernel/ (s73 is authored and committed — do not touch), serving/, libexec/
(the remediation builder's surface), any other hook.

## Report

Per item: design choices defended, WITNESSED verbatim both polarities / UNEXERCISED with
blocker (the pre-s73 annulled refusal pass-through is a REQUIRED witness), flags in reach.
