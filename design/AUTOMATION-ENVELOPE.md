# AUTOMATION ENVELOPE — how far the patterns + harness actually reach (2026-07-09)

Status: DESIGN/assessment, Fable-authored (session be693afb), companion to AGENTIC-PATTERNS.md.
The question answered: can "fuzzy task in → hierarchically decomposed → formally accountable
engineering → polished software out" run robustly and economically on this harness, with
Sonnet doing the work, hotshots called in on typed triggers (ADR-0014-style), leaves-first
re-engineering, opportunistic refactoring? Answer: a large, precisely-boundable YES, with five
boundaries that are properties of the problem, not of today's tooling — plus a gap list of
what the harness still needs for the yes-part.

## The core asymmetry that defines the envelope

Automation is robust exactly where VERIFICATION IS CHEAP RELATIVE TO GENERATION and a checker
can be written: types, tests, gates, differentials, view-emptiness (question_status,
review_gap), equivalence bars. There, fix-points terminate on a mechanism's verdict and Sonnet
executes safely at depth — today's evidence: a naive agent completed the deny→teach→retry loop
unaided; the 9-item exercise ran hours of witnessed work and surfaced two real kernel defects;
the registry job survived three enumeration failures BECAUSE the refusals were loud. Where no
checker exists (taste, architecture quality, UX), fix-points don't terminate meaningfully —
judge panels drift and Goodhart. The envelope's edge is not "how smart is the model"; it is
"can this property be checked."

## The five boundaries (each names its evidence)

1. **Seams, not leaves.** Decomposed leaves verify locally; systems fail at composition —
   ADR-0012's 2026-07-02 amendment (OBS-2: every port individually correct, the composed
   system wrong) is the recorded proof. Hierarchical decomposition is safe when every SEAM is
   itself an artifact: an interface spec + a differential/parity check across it. Corollary:
   decomposition depth ~2-3 levels is the practical ceiling — each level multiplies seams, and
   seams are where the automation is weakest. Leaves-first re-engineering is the right
   instinct for exactly this reason (smallest blast radius, checkable in isolation), and the
   kernel anticipated it: the engine's DTO layer (decompose-then-overrule, fragment standing,
   SoD-gated decomposition attestation) IS hierarchical-decomposition adjudication — dark
   today, built for this.

2. **Fuzzy→spec keeps the operator; spec→software doesn't.** Interrogation-to-spec (pattern 1)
   makes elicitation efficient and its termination mechanical, but the operator remains the
   oracle for what they actually want — and real requirements are partly discovered against
   the running artifact, not extracted up front. The pipeline is autonomous downstream of a
   ratified spec; upstream it is operator-paced by nature. Budget the operator's role there,
   not in code review.

3. **Verification terminates at the deployed effect — and that step often needs a human or an
   instrumented deployment.** The recidivism study's OBS-1 (three passes of mechanism-level
   clears; the originating complaint still observable live) is the recorded proof, now law
   (ADR-0013 amendment 2026-07-02). Fully-automated pipelines clear mechanisms; the
   effect-level acceptance run is a designed step with an owner, or the "supremely polished"
   claim is exactly the umbrella claim the law forbids.

4. **The law's spirit and constitutional acts stay out.** Kernel lineage deltas (s20),
   ADR interpretation, assurance-level assignment, condemnations (refgraph) — these are
   ratifier acts. The harness's job is to make them RARE and WELL-PREPARED (the delta
   authored, the evidence attached, the apply command one line), not to absorb them.

5. **Economics scale with consequence, by design.** Adversarial verification multiplies
   tokens roughly with panel size × fix-point iterations (3-10× naive generation). That is
   affordable precisely because the assurance-level dial (OPUS-READINESS move 2) prices rigor
   per artifact: leaf code at low DAL gets tests+gates; the kernel-adjacent path gets panels
   and countersigns. A pipeline that runs everything at max assurance is not "robust", it is
   unaffordable — the dial IS the economic model. Today's operating data: major Sonnet tasks
   ran 40-370k tokens each; orchestration overhead ~10-20%; Fable needed only for specs,
   rulings-preparation, and one relay failure (which a mechanism now prevents).

## Escalation, made typed (the ADR-0014 generalization)

Hotshot call-in works iff the trigger is an EVENT, not self-assessment (the corrupted-faculty
problem, ADR-0013 R3). The triggers, all typed and available: N consecutive gate refusals on
one item; differential DIVERGE_DEFECT/QUARANTINED; a review-objection loop not converging in K
rounds; demurral-detector fire; watchdog timeout (see gaps); commission/conformance diff
non-empty. Escalation path: Sonnet → second Sonnet with fresh context (pattern 10 — cheaper
than a tier jump and catches context contamination) → Opus ONLY under the two-condition rule →
the QUESTION (not the task) to the maintainer/Fable. Every escalation is a ledger row; "what
needed a hotshot" becomes measurable, which is what lets the thresholds be tuned instead of
guessed.

## What the harness still needs (the gap list, priority order)

1. **s20 delta applied** — unlocks obligations/review_gap: the review fix-point as emptiness
   of a view (the load-bearing termination criterion for pattern 2 at scale). Filed.
2. **A work-item layer** — tasks/decomposition edges/state as first-class rows (the
   omega work-status shape, married to the existing enacts vocabulary). Without it,
   decomposition tracking rides in prose statements — the exact prose-vs-schema gap the
   capability audit flagged in the toy ledger.
3. **Commission/conformance instrument** (OPUS-READINESS move 4) — the mechanical "did the
   delivery match the ratified scope" diff; ADR-0013 R1's named conversion trigger.
4. **Agent liveness watchdog** — today an agent parked on a timer and never woke; the fix
   (resume-from-transcript with a status demand) worked but was manual. A parked-agent
   timeout with automatic prod is trivial and closes a real robustness hole.
5. **judge --bootstrap** (pattern 6) — T_now as the session handoff, so deep pipelines don't
   accumulate prose-drift between stages.
6. **Seam differentials as a first-class instrument** (boundary 1) — the marriage
   differential's shape, parameterized for arbitrary interface contracts.
7. **Cost accounting per node** — tokens/tier per ledger-tracked work item, so boundary 5's
   dial is tuned on data.

## Verdict

Robust and economical TODAY for: spec-first, leaf-sized (hours-of-Sonnet) tasks in a gated
repo, two-level decomposition with countersigned splits, refactors under the P6 equivalence
bar, and audits/exercises of the enumerated-universe kind. Robust AFTER the gap list for:
deep hierarchical builds with typed escalation and mechanical conformance. Permanently
outside, by nature not by tooling: requirements discovery against reality, taste, effect-level
acceptance in the world, and constitutional acts — the operator's residue, deliberately small
and well-prepared. "Supremely polished" is reachable in the verified-to-spec sense; polish
beyond spec is a spec defect to fix upstream, not an automation gap.
