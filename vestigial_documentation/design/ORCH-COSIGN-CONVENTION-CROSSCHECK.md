# ORCH-COSIGN-CONVENTION-CROSSCHECK — adjudicating ent cycle-003's METHOD CANDIDATE 2

Audience: maintainer (and the orchestrator relaying to him)

**Status: point-in-time adjudication record, dated 2026-07-13. Never retro-edited; a later
cross-check of the same or a related candidate supersedes it by a new numbered document.**
Commissioned as tracker work item `cosign-convention-crosscheck` (ledger row 486): cross-check
ent observatory cycle-003's METHOD CANDIDATE 2 — an "iterate-to-approval co-sign convention"
surfaced in `/home/bork/ent`'s own tracker (that project's row 54, not this project's `./led`
— this repository's own append-only work-item tracker, the command-line verb this project
uses to read and write its decision ledger) — against this repository's existing corpus, and
adjudicate one of three outcomes:
already-covered (name the home), genuinely-new (serve it), or divergent (surface the gap for
the maintainer, never silently harmonize). This document is that adjudication. It does not
serve a new recipe, because the verdict below is **already-covered**.

## The candidate, as described in its own source

[observatory/ent/cycle-003.md](../../observatory/ent/cycle-003.md) §7, item 2, quotes ent's
fix-stage redesign (ent tracker row 54) as stating "a clean, generalizable review rule: a
co-sign gate loops until the reviewer actually APPROVES (capped, here at 3 rounds); short of
that, the work is IN FLIGHT, never treated as done; and a task that exhausts the cap without
approval is emitted UNRESOLVED and held, never silently applied." The observer who filed it
explicitly flagged it as "not yet adjudicated" and "did not cross-check the full existing
corpus for overlap (time-boxed)" — this document is that deferred cross-check.

The candidate restates as three clauses, to line up against the corpus below:

1. **Convergence criterion** — the loop terminates when the reviewer's response constitutes
   agreement (here: "APPROVES"), not on a verbal or subjective sense of quality.
2. **Hard round cap** — a fixed ceiling on iterations (here: 3).
3. **Cap-exhaustion semantics** — hitting the cap without convergence does NOT silently apply
   the unresolved work; it is held, marked unresolved, visible as such.

## Cross-check against the corpus

### law/adr/0014-executor-second-opinion.md (read in full)

ADR-0014 is the root: it licenses fetching **one** independent second opinion when an
executor's own line of reasoning has demonstrably stalled (Rule 2's observable-recurrence
trigger — "≥2 attempts that each turned out to address the wrong target," or a diagnosis that
keeps proving partial), and requires that opinion be briefed for independence, never pre-led
(Rule 3 — the same "brief the artifact, not your verdict" discipline the ent redesign's
maintainer-relayed correction enforced when it un-fused ent's rounds 2-3 reviewer: rounds 2-3
had used the same single reviewer instance for both a front-loaded findings briefing and what
was meant to be a fresh sweep, and the correction split those two into genuinely separate,
independent reviewer instances. That correction is ent's own tracker row 71, cited in
[observatory/ent/cycle-003.md](../../observatory/ent/cycle-003.md)'s "DIFF-VS-PRIOR" section — the
section, near the top of that report, that compares this cycle's ledger state against the prior
cycle's snapshot — and again in that report's §3, "Harness Friction"). ADR-0014 does not itself
specify a round cap or a
convergence-loop structure — its scope is explicitly "fetching an independent opinion," not
"iterating a review to a fixed point." Its own "Related" section is explicit about this
boundary: it names
[design/ORCH-review-fixpoint-protocol.md](../../design/ORCH-review-fixpoint-protocol.md) nowhere directly,
but that document's own text states the lineage plainly (quoted next): ADR-0014 is the
single-opinion root that a later design generalized into a convergence loop. ADR-0014 is
therefore a necessary but not sufficient home for the candidate — it is the ancestor of the
convention, not the convention itself.

### design/ORCH-review-fixpoint-protocol.md (read in full)

This is the match. Its own closing line states the lineage explicitly: "ADR-0014 (executor
second opinion) generalized from one opinion to convergence." Line up its three structural
pieces against the candidate's three clauses above:

1. **Convergence criterion.** The review-fixpoint protocol's criterion is "structural, never
   verbal": not the word "flawless" (or, in ent's language, "APPROVES") but **a fresh review of
   the final artifact producing ZERO findings that survive disposition** — precisely the
   behavioral content of "the reviewer actually approves," restated to avoid the exact
   verbal-inflation trap the protocol's own opening section names two failure directions for
   (history-anchoring and nit-manufacturing). Ent's "APPROVES" and the protocol's "zero
   undisposed findings" are the same convergence event, described at two different vocabularies
   — a design-review co-sign gate reporting a verdict word versus a findings-count criterion —
   not two different conventions.
2. **Hard round cap.** The protocol's **round-ceiling** parameter is exactly this: "a hard cap
   on TOTAL rounds, dirty ones included." It is explicitly a **per-unit calibration knob**, not
   a fixed constant — the document's own worked example (labeled "e18," one dated case in this
   project's e-series of numbered review-convergence exercises) used round-ceiling=1; the ABC
   audit loop (below) instantiates it at 2; ent's redesign instantiated it at 3. Three different
   numbers for the same parameter is calibration variance, the exact thing the vocabulary
   section designed the knob to carry — not a divergence in the convention's shape.
3. **Cap-exhaustion semantics.** The protocol states this outcome in so many words: "Hitting it
   closes the unit RED-honest with its open findings, never auto-attested." That is the
   identical semantics to ent's "emitted UNRESOLVED and held, never silently applied" — same
   refusal (no silent pass), same visibility requirement (the unresolved state is on the
   record), same non-negotiable floor (a round-ceiling breach is not covered up by treating the
   work as done).

The protocol document further generalizes the *scope* of "unit" beyond a single fix-review pair
to any artifact under this policy, which is exactly the shape ent's redesign applied it to (a
taxonomy-consolidation co-sign, not a code-review co-sign) — the generalization was already
designed for a broader "unit" than "one patch," so ent's application to a different artifact
type is an instance of the existing design, not an extension of it.

### design/ORCH-ABC-AUDIT-LOOP-RECIPE.md (read in full)

The A:B:C loop is a **concrete, operationalized instance** of the same fixed-point shape,
calibrated for maintainer-facing documents specifically: confirmation-depth=1 (one clean round
suffices), round-ceiling=2 ("ADR-0017 caps the loop at two B→C rounds"), and — on cap exhaustion
— "the document routes upward as a non-converging-review-loop... rather than grinding a third
round," with the record explicitly kept as "a DEFECT verdict with `escalated: true`... the
honest record of what happened," never a silent pass. This is the same three-clause shape again
(convergence = zero surviving findings across a fresh round; hard cap = 2; exhaustion = held/
escalated, not silently applied), calibrated differently (round-ceiling=2, escalate-to-human
rather than review-fixpoint's escalate-to-RED-and-open) for its specific artifact class
(documents, not code fixes or design taxonomies). It corroborates, rather than complicates, the
already-covered verdict: two live instances of the identical convention already exist in the
corpus at two different calibrations, exactly as the review-fixpoint protocol's calibration
vocabulary anticipates.

## Verdict: ALREADY-COVERED

**Home: [design/ORCH-review-fixpoint-protocol.md](../../design/ORCH-review-fixpoint-protocol.md)**, itself
grounded in **[law/adr/0014-executor-second-opinion.md](../../law/adr/0014-executor-second-opinion.md)**
and already carrying a live, differently-calibrated instance in
**[design/ORCH-ABC-AUDIT-LOOP-RECIPE.md](../../user-guide/ORCH-ABC-AUDIT-LOOP-RECIPE.md)**.

Ent cycle-003's METHOD CANDIDATE 2 — "co-signature is agreement, capped at N rounds,
unresolved-held-not-applied" — is the review-fixpoint protocol's confirmation-depth/
round-ceiling/RED-honest-on-exhaustion shape, described in a different vocabulary (ent's
"co-sign gate... APPROVES... UNRESOLVED and held" versus the protocol's "criterion-review...
zero undisposed findings... RED-honest, never auto-attested") and instantiated at a third
calibration point (round-ceiling=3, alongside the corpus's existing e18 example at 1 and the
ABC recipe at 2). No divergence was found on any of the three structural clauses checked above:
the convergence criterion, the round cap, and the cap-exhaustion semantics all match. This is
not a genuinely-new servable rule — it is the same rule, correctly re-derived by a different
project (ent) from the same root ADR-0014, landing at the same design the review-fixpoint
protocol already generalized to. No new document is served; this adjudication note itself is
the deliverable, per the commission's own framing of the already-covered outcome ("point at the
home").

**What this adjudication does NOT claim.** It does not claim ent's redesign was *derived from*
this repository's protocol (ent is a separate project under `/home/bork/ent`, read-only, and
this cross-check has no evidence either way about ent's own design provenance) — only that the
resulting convention, whatever its origin, is structurally identical to one already codified
here, so re-serving it under a new name would duplicate an existing home rather than add
information. Nor does it claim the three calibration points observed (1, 2, 3) exhaust the
useful range — the review-fixpoint protocol's own "Open empirical question" section already
names round-count calibration as unmeasured, and a fourth data point (ent's, at 3) is consistent
with, not disruptive to, that open question.

## Related

- [observatory/ent/cycle-003.md](../../observatory/ent/cycle-003.md) §7 item 2 — the candidate this
  document adjudicates, and the observer's own explicit flag that the cross-check was deferred.
- [law/adr/0014-executor-second-opinion.md](../../law/adr/0014-executor-second-opinion.md) — the
  root tenet (single independent opinion, briefed for independence, Rule 3) that the
  review-fixpoint protocol generalized into a convergence loop.
- [design/ORCH-review-fixpoint-protocol.md](../../design/ORCH-review-fixpoint-protocol.md) — the home this
  adjudication names: the structural (not verbal) convergence criterion, the three-knob
  calibration vocabulary (confirmation-depth and round-ceiling, both discussed above, plus a
  third knob that document defines as panel-width — how many fresh first-contact reviewers sit
  on a single round, not touched by this document's own cross-check), and the RED-honest,
  never-auto-attested cap-exhaustion rule.
- [design/ORCH-ABC-AUDIT-LOOP-RECIPE.md](../../user-guide/ORCH-ABC-AUDIT-LOOP-RECIPE.md) — a second, differently
  calibrated live instance of the same convention (round-ceiling=2, escalate-to-human), cited
  here as corroborating evidence that the convention already recurs in this corpus at more than
  one calibration.
