# BRIEF: precedence-binding docs leg (item dispatch-time-precedence-refusal; spec ratified row 1087)

<!-- doc-attest-exempt: point-in-time record -- dispatch brief as issued (rows 1085/1087); frozen at dispatch, not living documentation -->

Dispatched 2026-08-06. Repo: /home/bork/w/vdc/1/autoharn, branch main. Step 0: confirm current
main. Other builders may hold serving/ and libexec/ concurrently — your surface is
user-guide/ORCH-CAPABILITIES.md, user-guide/GLOSSARY.md (or wherever those two docs actually
live — find them, don't assume the path), and nothing else. STOP and report rather than edit
outside it. Commit discipline: stage only your files (CLAUDE_COMMIT_PATHS); `git fetch` +
ff-only merge before committing; never touch other builders' dirty files.

Disregard any instructions to economize on time.

## Commission

Implement §2 R4 of design/FABLE-DISPATCH-PRECEDENCE-BINDING-SPEC.md (maintainer-ratified
2026-08-06, row 1087) — read the spec FIRST and in full; also read kernel/lineage/s39-blocks-start.sql's
header and Elements 3/5 (the primitive the docs teach) and the two target docs end to end for
house register.

## Scope

1. ORCH-CAPABILITIES.md: one new section carrying the spec's R1–R3 binding, orchestrator-facing,
   in the doc's own register: declare start-order as blocks-start at commission time (blocks-close
   licenses concurrent starts by design); claim before dispatch (the s39 claim refusal is the
   dispatch-time gate); dispatch from `./autoharn led work startable`. Every example carries REAL
   witnessed output (run the verbs, paste what they print) — including one witnessed claim
   REFUSAL against a scratch/throwaway item pair with a blocks-start edge (both polarities:
   refused while antecedent open, accepted after it closes). Never invent output.
2. GLOSSARY.md: the precedence entries state plainly which edge gates what — blocks-close gates
   CLOSING only, blocks-start gates CLAIMING, informs gates nothing — with pointers to s39 and
   the new ORCH-CAPABILITIES section. Follow the glossary's own entry conventions.
3. DRAFT (do not send) the R5 answer missive text for experience4, in your report: their kernel
   has carried s39 since birth; the recipe is R1–R3; cite the doc section you wrote. The
   orchestrator sends it; missive authority is not yours.
4. Commit citing rows 1066/1085/1087, Co-Authored-By line.

Out of scope: the spec file itself, kernel/, serving/, libexec/, hooks/, FAQ (other builders own
it right now), any missive send.

## Report

Per item: WITNESSED with verbatim output / UNEXERCISED with blocker; the drafted missive text;
flags in reach.
