# Shaped recipes — exploration spec (the DSL's first public exposure)

<!-- doc-attest-exempt: exploration spec under the maintainer's unfreeze decision (row
     1617); attestation rides the factored doc it governs, not this basis -->

**Status: Fable-authored 2026-07-18 under the maintainer's unfreeze of
`pipeline-dsl-exploration` (decision row 1617, his words verbatim there; rider row
1616 carries the dual-representation framing). This is Q3 ruling (a)'s exploration
spec, deliberately scoped to the maintainer's named first step: factor the mechanical
recipes out of `design/USER-RECIPES-FAQ.md` into a sibling doc where each carries a
validated formal specimen. Executor: the default implementer, work item
`shaped-recipes-factoring` (row 1618). Not a language-design exercise: v0 of the
formal layer already exists (`design/workflows/*.toml`, validated by
`tools/workflow_check.py`) and this spec treats its schema as AUTHORITATIVE — schema
gaps found during factoring are FILED against `pipeline-dsl-exploration`, never
invented ad hoc by the builder.**

## 1. The new document

`design/USER-SHAPED-RECIPES-FAQ.md` (the maintainer's suggested name, adopted). One
section per factored recipe, each in this fixed order:

1. **Plain-words orientation** — what the recipe does and when you'd reach for it,
   before any citation or formalism (the FAQ house rule).
2. **The shape** — the recipe's TOML, embedded verbatim from a REAL file in
   `design/workflows/<recipe-name>.toml`. The file is the specimen; the doc quotes
   it. Never a code fence with no backing file — public exposure means a validated
   artifact, not markdown that looks like one.
3. **The prose recipe** — moved from `USER-RECIPES-FAQ.md`, content-preserving
   (edits limited to what the new home requires: section lead, cross-references).
   Witnessed transcripts move with it and stay witnessed.
4. **The contrast note** — 2-5 sentences on what the TOML captures that the prose
   obscures, and what the prose carries that the TOML cannot (the maintainer's
   stated purpose: the contrast itself is the teaching instrument). Honest in both
   directions; a recipe whose contrast note would be empty on either side is
   mis-selected (see §2).

`USER-RECIPES-FAQ.md` keeps a stub at each old location: one sentence naming where
the recipe went and why ("this recipe has a formal shape; both live in ..."). No
silent disappearance from a document operators have already read.

## 2. Selection criteria — "mechanical, gainfully shaped"

Factor a recipe iff ALL hold:

- **(a) Algorithmic shape:** it has enumerable steps/phases with a defined order
  (sequence, fan-out, or loop), typed participant roles, and a stated termination or
  convergence condition. The A:B:C loop (phases, fresh-context forks, two-round cap,
  escalation edge) is the canonical member and MUST be the first factored specimen.
- **(b) Gainful:** `workflow_check.py`'s v0 schema can express the control flow
  without dropping a constraint the prose states as load-bearing. If a load-bearing
  constraint has no schema home, the recipe is NOT factored; the gap is filed
  against `pipeline-dsl-exploration` with the constraint quoted verbatim. Partial
  factoring (TOML for the flow, prose carrying the rest) is acceptable ONLY if the
  contrast note names exactly which constraints stayed prose-only.
- **(c) Not judgment-shaped:** recipes whose essence is human/orchestrator judgment
  (recusal-RCA's fact-finding mandate, the pairing convention's "when a close
  necessarily mutates the tree") stay prose. A TOML that reduces judgment to a
  boolean field is a lying formalization — the failure mode this spec exists to
  refuse.

The builder's report ENUMERATES every recipe/section in `USER-RECIPES-FAQ.md` with a
per-recipe verdict (factored / kept-prose with the failed criterion named / filed as
schema gap). Closure statement over that enumeration, per ADR-0000 2(a): the
universe is the FAQ's section list at the base commit, stated explicitly in the
report.

## 3. Validation as witness

Every `design/workflows/<recipe>.toml` passes `tools/workflow_check.py` — the run is
a witnessed transcript in the new doc's own preamble (real output, exit code). If
`workflow_check.py` has no repo gate wiring yet (the 2026-07-18 sweep flagged its
missing fixture leg), the builder does NOT build gate wiring in this task — that is
the already-filed fixture-coverage item's scope; the witnessed manual run suffices
here.

## 4. Review

ADR-0017 A:B:C on the new doc AND on the FAQ's stubs, two-round cap, escalation to
the orchestrator on non-convergence (the standing path). B reviewers additionally
verify content-preservation: each moved recipe diffed against its FAQ original,
divergences beyond §1.3's allowance are findings.

## 5. Explicitly out of scope

Executing TOML shapes (the DSL stays declarative-and-validated only, this pass);
schema evolution (filed, not built); factoring anything from documents other than
`USER-RECIPES-FAQ.md`; the maintainer's own reading of the formal layer — §1's
format is designed so he can "peek" at a specimen beside prose he already knows,
which is the whole point of the exposure.
