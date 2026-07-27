# FABLE-JUDGE-LAYER-CAPABILITY-CLOSURE-SPEC — a registered layer without a declared capability rule becomes unrepresentable

<!-- doc-attest-exempt: Fable-authored spec 2026-07-26, awaiting maintainer ratification;
the A:B:C loop runs when this spec is ratified and its build begins, not on the proposal
text. A-side pre-review (attestations/COMMON-DEFECT-CLASSES.md contract) was applied
during authoring. Removal condition: superseded by the build's completion record. -->

This spec repairs the defect that makes every bare `./judge` invocation crash, and
forecloses the class it belongs to. It is Fable-authored because the fix touches
`engine/` differential semantics, which CLAUDE.md's orchestration contract gates behind a
Fable-authored, maintainer-ratified spec. Sonnet builds it once ratified.

- **Status:** RATIFIED by the maintainer 2026-07-27 ("Let's start with 1(yes)"); build
  dispatched the same day.
- **Basis:** ledger row 1459 (the fixture-sweep triage that witnessed the crash — six
  families RED on this one cause), and the code as read at head: the capability-detection
  path in [`engine/ledger_differential.py`](../engine/ledger_differential.py) (the
  `layer_capability` function, ~line 302, and the bare-invocation auto-detect loop,
  ~line 474) and the layer registry in [`engine/lp_registry.py`](../engine/lp_registry.py)
  (`LAYERS`, ~line 216).

## 1. The defect, and the class behind it (ADR-0000 Rule 2's two questions)

**The instance.** `layer_capability(name, layer)` — the detection function the bare
(no `--layer` flag) `judge`/`ledger_differential.py` path calls for every registered
layer on every target — carries explicit branches for `tnow`, `work`, `defeat`, and
`belief`, then `raise NotImplementedError` for anything else. The registry's `LAYERS`
already contains `entitlement` (registered when the s60-family entitlement programs
landed). The auto-detect loop iterates `list(lp_registry.LAYERS)` unconditionally, so
every bare invocation, on any world, on any schema, crashes before producing a single
verdict. Witnessed across six fixture families (row 1459 cluster 2). A crash is not a
refusal: it teaches nothing, names no capability, and takes the four healthy layers down
with it — the opposite of the closed-verdict discipline (`AGREE | DIVERGE_BY_DESIGN |
DIVERGE_DEFECT | QUARANTINED`) the differential is built on.

**Question (a) — what shape makes the class unrepresentable?** The class, named at full
width per the 2026-07-02 closure-statement amendment to
[ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md): *a layer can
be registered without declaring how to detect its substrate or how to floor-compare it,
and the omission detonates at run time in whichever consumer switches on layer names.*
There are TWO such consumer switches today, not one: `layer_capability`'s if-chain, and
the `_LAYER_FLOOR_PREDS` dict that `run_layer_differential` consults (a layer absent
from it raises its own `NotImplementedError`). Both are enumerations that fail open at
the next registered layer. The foreclosing shape: **the registry entry itself carries
the capability rule and the floor disposition.** A `LAYERS` entry becomes a typed record
— program stack (as today), plus a capability probe, plus a floor disposition that is
explicitly one of floor-preds or declared-no-floor-with-reason — validated at module
import time (a plain module-scope check over the completed registry; the lazy-import ban
is untouched). Registering a layer without all three parts then fails at import, in
every test and every commit, not at the next operator's bare `judge`.

**Question (b) — what operational lapse let it recur?** The enumeration-consumer gap had
no net: nothing quantified `LAYERS` against the switches that consume it, so the
`entitlement` registration was one edit away from this crash from the day it landed —
and the same gap would fire again on the next layer. The net is the import-time closure
check above (the strongest feasible surface — construction-time, per ADR-0002's
hierarchy), plus the witness legs in §4 that pin the bare path's no-crash contract.

## 2. Design

1. **Typed registry entries.** Each `LAYERS` entry in `engine/lp_registry.py` carries:
   the program stack (unchanged); a `capability` probe returning `(bool, reason)` in
   exactly the shape `layer_capability` returns today; and a `floor` disposition —
   either the layer's floor predicate set (what `_LAYER_FLOOR_PREDS` holds today) or an
   explicit no-floor marker with a one-line reason. The existing four layers' probes and
   reason strings move VERBATIM (byte-diffed, not retyped) from `layer_capability`'s
   branches into their entries — the reuse-the-same-checks-verbatim discipline that
   function's own docstring mandates is preserved, just relocated to the single home the
   registry already is. `tnow`'s always-capable rule moves with the same fidelity.
2. **The switches become lookups.** `layer_capability` and the `_LAYER_FLOOR_PREDS`
   consultation reduce to registry lookups. Both `NotImplementedError` sites are
   DELETED — not kept as defensive tails — because the import-time closure check makes
   the state they guarded unrepresentable; a defensive branch for an unconstructable
   state would be dead code lying about reachability.
3. **The entitlement entry specifically.** Capability probe: presence of the s60
   entitlement substrate on the target schema, detected in the same `has_col` idiom the
   `work`/`defeat` probes use (the `entitlement_act_class` column is the s60-family
   marker; the builder confirms the exact minimal column set against
   `kernel/lineage/s60-entitlement-enforcement.sql` and, post-s64, states whether the
   s64 columns change the probe — they should not, since s64 adds columns to an
   s41-era kind, but the builder verifies rather than assumes). Reason string on
   absence: same teaching shape as the `defeat` probe's ("capability absent, not
   record-empty"). Floor disposition: the builder reconciles against what exists at
   build time — if the s64 work left a servable entitlement floor
   (`engine/ledger_edb.py` gained entitlement EDB families; `engine/lp/
   ledger_entitlement.lp` carries the ASP side), wire it as floor-preds and the layer
   differentials like any other; if no complete floor exists yet, the entry declares
   no-floor with the reason, honestly, and the gap is FILED (BACKLOG or ledger row),
   never silently widened into scope.
4. **Bare-path behavior for a capability-present, no-floor layer.** The auto-detect
   loop prints a disclosed one-line skip naming the layer and the declared reason
   (mirroring the existing declared-incapable line's shape) and contributes nothing to
   the red count. An explicit `--layer <name>` request for a no-floor layer gets the
   typed refusal naming the gap — the current `run_layer_differential` behavior,
   preserved, now sourced from the registry entry's own declared reason. The explicit
   path's semantics for capable layers are byte-identical to today (the pre-existing
   contract that `--layer` never runs detection is untouched).

## 3. What this spec does NOT change

No kernel object, no `engine/lp/*.lp` program content, no verdict vocabulary member, no
derivation-record shape, and no behavior of any explicitly-requested capable layer. The
change is confined to `engine/lp_registry.py`'s entry shape, the two consumer switches
in `engine/ledger_differential.py`, and (if the builder's floor reconciliation lands
floor-preds) the wiring of already-existing floor machinery. `judge` itself
(`libexec/autoharn/judge`) passes flags through unchanged and is untouched.

## 4. Witness plan (scratch, both polarities, red first)

RED — at head, before the fix: bare `ledger_differential.py` against any scratch world
crashes with the NotImplementedError naming `entitlement` (the row-1459 symptom,
re-witnessed as the baseline). After the fix, the negative-control leg: a synthetic
registry entry missing its capability probe (constructed in a test, never committed)
fails the import-time closure check loudly.
GREEN — after the fix: bare `judge` on a pre-s60 scratch world runs to completion, four
layers verdicted, `entitlement` reported declared-incapable with the teaching reason,
exit code unchanged from the healthy-layers result; bare `judge` on a post-s64 scratch
world either differentials the entitlement layer (floor wired) or prints the disclosed
no-floor skip (floor filed) — whichever the §2 item 3 reconciliation produced, witnessed
as built; explicit `--layer entitlement` on an incapable target QUARANTINEs with the
same reason string the bare path prints (the two-paths-agree discipline); explicit
`--layer work`/`defeat`/`belief`/`tnow` byte-identical output against a pre-fix capture
on the same scratch world. The six row-1459 cluster-2 fixture families go GREEN.
SQL/ASP differential in AGREE wherever a layer actually runs.

## 5. Closure statement

Quantification universe, per ADR-0000 Rule 2(a)'s amendment: all members of
`lp_registry.LAYERS` at head (`tnow`, `work`, `defeat`, `belief`, `entitlement`) × both
invocation paths (bare auto-detect, explicit `--layer`) × capability present/absent ×
floor present/declared-absent. The invariant: no combination raises; every combination
lands in the closed verdict vocabulary, a declared-incapable line, a declared-no-floor
line, or a typed explicit-request refusal. The closure is held by the import-time
registry validation (construction surface), quantifying over every FUTURE layer as well
— which is the point. Not covered, named honestly: consumers of layer names outside the
two switches this spec rewires (none are known at authoring time; the builder greps for
`lp_registry.LAYERS` consumers and either confirms the enumeration or extends it, with
the grep output in the build report).

## License

Public Domain (The Unlicense).
