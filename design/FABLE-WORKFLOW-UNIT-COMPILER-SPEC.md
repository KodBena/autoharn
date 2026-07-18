# Workflow-unit compiler — fixed-shape TOML to kernel-coupled units

<!-- doc-attest-exempt: build-basis spec; attestation rides witnessed delivery -->

**Status: Fable-authored 2026-07-18, build basis. Commission: ledger row 1658
(maintainer, verbatim: "a compiler that takes our 'fixed-shape' toml's and produces
workflow units of them ... I'll want to exercise 'in real time' role constraints and
true obligation blockers in the new world"). Compile target maintainer-ratified same
date via the decision queue: KERNEL-COUPLED UNITS — the kernel is the truth, the
workflow obeys it. Exercise world: omega-lab (born this date, chain head s50).
Sonnet builds; no kernel/lineage or law/ edits are licensed by this spec.**

## The one design commitment (everything follows from it)

The compiler adds NO enforcement machinery of its own, because the kernel already
owns every blocking mechanism the commission names:

- a **dependency blocker** is an s39 `blocks-start` edge — `led work claim` REFUSES
  while an in-force antecedent is open (claim-time precondition foreclosure);
- a **completion blocker** is s47 — a closed slug is not claimable;
- an **obligation blocker** is a countersign obligation — debt visible in
  `review_gap`/`work_review_gap`, discharged by an independent review row;
- a **role constraint** is a principal fact — s40/s41 registration, class, binding.

"True obligation blockers, in real time" therefore means: the driver ATTEMPTS the
kernel act and obeys the typed refusal. It never pre-computes "is this blocked" from
its own state; the refusal (or acceptance) IS the gate. A unit is runnable exactly
when the kernel accepts its claim — the same fact `work_startable` derives.

## Inputs

The fixed-shape TOMLs of `design/workflows/*.toml` (the pipeline-dsl-v0 grammar per
`design/FABLE-SHAPED-RECIPES-EXPLORATION-SPEC.md`): `[[phases]]` with `name` +
`depends_on`, and `[roles.<phase>]` with `authors`/`implements`/`reviews` prose.
v0's "no conditionals, no loops, no expressions" discipline stands: loop mechanics
(dry-counts, round caps) stay driver-side code, never TOML — the compiler compiles
the SHAPE, exactly as the specimens' own headers already document for their misfits.

## Outputs, two artifacts per TOML

1. **A hydration script** — a deterministic sequence of `led` invocations (never raw
   SQL; the led verbs are the write surface): one `led work open` per phase (slug
   `<toml-stem>-<phase>`, the TOML's provenance in the statement), one
   `led work depends <dep> <ant> blocks-start` per `depends_on` edge, and — where a
   phase's `reviews` clause names an independent countersign — the obligation act
   for it. Obligation scoping MUST follow the row-1640 teaching (the obligate
   footgun): oblige the narrowest implementer principal, never a principal whose
   prior rows would become retroactive debt; the hydration script prints the
   projected debt-surface delta and requires explicit confirmation before writing an
   obligation row. Re-running hydration is idempotent by refusal: already-open slugs
   refuse loudly (s22/s29 semantics) and the script treats that as "already
   hydrated", never as an error to work around.
2. **A driver script** — executes the wave by kernel conversation, per phase:
   claim (`led work claim` as the implementing principal; a refusal is a BLOCKED
   unit — the driver reports the kernel's own teach-text and moves on or waits,
   never overrides), dispatch (the `implements` role names the agent class to run;
   the driver hands the phase's prose brief to that agent), close (`led work close`
   with the `reviews` clause's discipline: `--review-witness` when witnessed,
   `--review-deferred` when the TOML defers it, per the specimen idiom). The driver
   polls runnability by re-attempting claims, not by shadow bookkeeping —
   `work_startable` may be CONSULTED for display, but the claim's verdict decides.

## Transport honesty (omega-lab today)

The served `led` does not yet cover `led work *` (Block D's named seam). The
compiler emits plain `./led` invocations and the driver takes a `--led <path>` knob;
in omega-lab that is `./legacy/led` until served coverage extends. Extending the
served shim to the work family is a SEPARATE, already-named pass — this spec does
not smuggle it in, and the compiler must not depend on it.

## Witnesses (both polarities, on omega-lab or a scratch world)

- **WC1** compile a two-phase specimen (e.g. `autoharn-builder-wave.toml`'s
  claim→build spine): hydration opens the slugs and edges; `work_startable` shows
  only the root; driver claims the root phase green.
- **WC2** the dependency blocker is REAL: driver attempts the dependent phase's
  claim while the antecedent is open → the s39 refusal, verbatim in the driver's
  output; after the antecedent closes, the same claim is accepted (s39/s47 both
  polarities).
- **WC3** the obligation blocker is REAL: with a countersign obligation hydrated,
  the closed-but-unreviewed phase shows in `work_review_gap`; an independent review
  row discharges it; the projected-debt confirmation printed before the obligation
  was written (the row-1640 guard) is in the transcript.
- **WC4** a role constraint is REAL: a phase whose `implements` names a class the
  claiming principal does not have → the claim (or the act the kernel gates on
  class, e.g. a key binding) refuses with the kernel's teaching, not the driver's.
- **WC5** idempotent re-hydration: running hydration twice adds zero rows beyond
  the first run's, with the refusals visible and treated as already-done.
- **WC6** the misfit discipline holds: a TOML with loop-shaped prose compiles to
  shape only; the compiler's output contains no loop bookkeeping (inspect, and the
  README "Known misfits" entries stay accurate).

## Build conditions

Compiler + driver live under `tools/` (Python, top-of-file imports only, gates
apply); no edits to kernel/lineage, law/, engine/lp, bootstrap/new-project.sh's
LINEAGE_CHAIN, or the boundary's route table; the TOML grammar is v0 as it stands —
grammar extensions route back to the exploration spec's own process, not here.
