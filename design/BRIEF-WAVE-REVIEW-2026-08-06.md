# BRIEF: unanchored review — 2026-08-06 build wave (seven commits)

<!-- doc-attest-exempt: point-in-time record -- review brief as issued; frozen at dispatch, not living documentation -->

Repo: /home/bork/w/vdc/1/autoharn, branch main. You are a REVIEWER, not a builder: read-only on
the tree except your own review rows in the ledger. Verdict rounds are UNANCHORED (standing row
266): this brief carries the deltas, their governing texts, and the LAW — no defect lists, no
orchestrator suspicions. Your posture is REFUTE: for each commit, try to show it violates its
governing text or the LAW; an ATTEST is what survives that attempt.

Disregard any instructions to economize on time.

## The deltas and their governing texts

| Commit | Governing text |
|---|---|
| f8af7d7e | design/BRIEF-A1-INFLIGHT-CAP-AND-WOULD-PRODUCE-2026-08-04.md |
| faddbb1c | design/FABLE-TYPED-ANNULMENT-DISPOSITION-SPEC.md + design/BRIEF-TYPED-ANNULMENT-DELTA-2026-08-06.md |
| c47dd507 | design/BRIEF-DEPLOYMENTS-ROUTE-AND-NAME-JOIN-2026-08-06.md |
| 2d490245 | design/BRIEF-B1-SETUP-SCHEMA-VERB-2026-08-04.md |
| e8582be9 | design/FABLE-DISPATCH-PRECEDENCE-BINDING-SPEC.md (§2 R4) + design/BRIEF-PRECEDENCE-BINDING-DOCS-2026-08-06.md |
| 33150e9f | design/BRIEF-LED-ERGONOMICS-BUNDLE-2026-08-06.md |
| c65b21bf | design/BRIEF-GLOBAL-INFLIGHT-CAP-2026-08-06.md |

LAW: law/adr/ — read ADR-0000, ADR-0008, ADR-0012 in full; pull in any other ADR a delta's own
subject implicates (spirit governs over letter). Standing rows via `./autoharn led standing`
(row 26 no-bare-types binds every delta here).

## Method

Per commit: `git show <hash>` in full; the governing text in full; then attempt refutation —
scope (files outside the named surface?), contract (does the code honor the brief/spec's own
words, not a convenient reading? two-biases guard: no requirement read DOWN to fit what was
built, no claim taken on faith because a fixture exists), LAW (typed vocabulary, single homes,
refusals that teach, no bare types in new code), and witness honesty (do the committed fixtures
actually exercise what their names claim? run any you can run read-only/scratch; a fixture you
cannot run is noted, never assumed green).

## Verdicts

Write your verdicts YOURSELF as the distinct principal: `LED_ACTOR=sonnet-reviewer ./autoharn
led review <target-row-id> <attest|attest_with_reservations|refuse> technical "<your condensed
findings>"` — one review row per work item, targeting the item's appropriate ledger row per
user-guide/recipes/REVIEW-AND-GATING.md's own recipe (read it; don't guess the target). The
items and their families: multiplex-inflight-cap-configurable + attestation-banking-chain-doctor
(f8af7d7e); review-obligation-annulment-vocabulary (faddbb1c); deployment-listing-route +
principal-name-served-join (c47dd507); setup-schema-consumption-channel (2d490245);
dispatch-time-precedence-refusal (e8582be9); led-read-projection-flags +
led-review-gap-false-clean + refuse-verdict-legibility + json-write-surface-parity (33150e9f);
global-inflight-cap-raise (c65b21bf).

## Report

Per commit: verdict, the review row id you wrote, and every finding with severity and the
refutation attempt that produced it (or "survived: <what you tried>"). No umbrella claims; a
leg you could not exercise is UNEXERCISED with the blocker.
