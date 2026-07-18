#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T20:48:39Z
#   last-change: 2026-07-18T05:37:23Z
#   contributors: a857c93d/main, ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""lp_registry -- the declared provides/requires/stands_alone registry for engine/lp/*.lp
(vestigial_documentation/design/ORCH-CATEGORICAL-REFACTOR-CONSULT-2026-07-15.md F7 / plan step 8(i)).

THE GAP THIS CLOSES (F7). Load order for engine/lp/*.lp has lived only in per-file comment
prose ("loaded ON TOP OF ledger_tnow.lp", "stacks ON TOP of engine/lp/contemporaneity.lp") --
readable by a human, unenforceable by a machine. A mis-stacked invocation grounds SILENTLY:
every consumed predicate in this corpus's own idiom is `#defined`, so an absent producer degrades
to an empty extension rather than a clingo grounding error -- correct and deliberate for the
single-program case (a fixture that never needed the composed reading), but a HAZARD the moment a
runner composes several programs and gets the stack wrong: nothing raises, the differential just
reads a real defect (an unfiltered retraction, an unclosed closure) as "nothing to report" (the
F49 vacuous-pass class this corpus refuses everywhere else). This module is the single, checkable
home of "what does each program provide, what does it need, and which named STACKS this codebase's
own runners actually compose" -- so a runner can ask ONE function whether its stack is complete
BEFORE grounding, and refuse loudly (ADR-0002) rather than let the .lp file's own fail-safe
`#defined` guards silently swallow the gap.

DERIVED FROM THE REAL HEADERS, NOT ASSERTED (ADR-0011 Rule 1 / ADR-0012 P1): every `provides` /
`requires` entry below was read off each file's own docstring-comment block (the #show list for
`provides`; the "loaded ON TOP OF" / "stacks ON TOP of" / "CONSUMED" prose for `requires`) at the
time this registry was authored. Each .lp file's header is updated (this same delta) to CITE this
registry as the one home of that declaration rather than duplicating the prose forward -- a header
still explains the WHY (the semantics), this registry is the sole place a runner reads the WHAT
(the checkable provides/requires/stands_alone triple).

`stands_alone=True` for every module currently in this corpus (every file uses the `#defined`
fail-safe-degrade idiom) -- declared explicitly per module, not assumed globally, since a future
module MAY legitimately need a hard EDB precondition with no safe empty reading.

LAYERS is the second half of this registry: the NAMED, checkable program stacks this codebase's
own runners actually compose (the differential harness, `judge`, the seen-red fixtures) -- e.g.
"work" = [ledger_tnow.lp, work_items.lp, work_review.lp], the exact stack the s31 both-polarity
fixture (seen-red/s31-supersession-uniform-retraction/run_fixtures.py) hand-assembled and the
standing `./judge` differential never wired up (the second F7 gap this build closes -- see
ledger_differential.py's new `run_layer_differential`). `require_layer_stack` is the one function
a runner calls before grounding a named layer: given the program-name list it is ABOUT to load, it
either returns cleanly or raises `RegistryError` with teach-text naming exactly which module is
missing and why the layer needs it -- never a silent empty grounding.

Lazy imports banned (CLAUDE.md)."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModuleSpec:
    """One engine/lp/*.lp module's declared contract. `provides` and `requires` are informational
    (the checkable restatement of the file's own header -- a reader or a future tool can diff this
    registry against the real #show/#defined lines to catch drift, the F2-shaped mechanization this
    corpus applies elsewhere); `stands_alone` is the one field `require_layer_stack` below actually
    enforces at runtime, via LAYERS."""
    provides: tuple[str, ...]
    requires: tuple[str, ...]
    stands_alone: bool
    note: str = ""


# ==== MODULES ================================================================================
# One entry per engine/lp/*.lp file. `requires` names OTHER registry keys whose EDB families this
# module's header says it CONSUMES (the "CONSUMED" / "#defined" list) -- not necessarily a load-
# order requirement (this corpus's #defined idiom makes every listed consumption OPTIONAL, see
# `stands_alone`); LAYERS below is where a HARD, checkable stack is declared.
MODULES: dict[str, ModuleSpec] = {
    "ledger_tnow.lp": ModuleSpec(
        provides=("in_force/1", "head/2", "unsound_derivation/2", "launder/3", "alias_surface/2",
                  "stale_enactment_row/2", "question_open/1", "question_answered/1",
                  "clause_defeat/2", "clause_defeat_moot/2", "clause_defeat_withdrawn/2",
                  "condition2_individuation/1"),
        requires=(),
        stands_alone=True,
        note="the root program of the T_now stack; reads entry/6, supersedes/2, enacts/2, "
             "answers/2, amends/2 off ledger_edb.py's export -- every family #defined."),
    "closure.lp": ModuleSpec(
        provides=("star/3",),
        requires=(),
        stands_alone=True,
        note="the generic kind-indexed transitive-closure module (plan step 4); reads edge/3, "
             "which any consumer contributes -- work_items.lp (kind work_dep), work_review.lp "
             "(kind work_succ) today."),
    "work_items.lp": ModuleSpec(
        provides=("work_dep_edge/2", "work_dep_star/2", "work_dep_star_via_closure/2",
                  "work_duplicate_open/1", "work_shipped_without_witness/2",
                  "work_depends_on_unknown/2", "work_dependency_cycle/1",
                  "work_orphaned_by_retraction/2", "edge/3"),
        requires=("ledger_tnow.lp",),
        stands_alone=True,
        note="work_orphaned_by_retraction's in-force reading needs ledger_tnow.lp's superseded/1 "
             "to be MEANINGFUL (not merely groundable -- see closure.lp's own note: absent, the "
             "predicate silently reads 'nothing retracted' rather than refusing); the LAYERS "
             "entry below is what a differential runner actually enforces. "
             "work_dep_star_via_closure/2 additionally needs closure.lp's star/3 (soft -- absent, "
             "it is simply empty; the historical work_dep_star/2 is unaffected)."),
    "work_review.lp": ModuleSpec(
        provides=("w_tree_member/2", "w_own_leaf_unresolved/1", "w_tree_unresolved/1",
                  "work_succ_star_via_closure/2", "edge/3"),
        requires=("ledger_tnow.lp",),
        stands_alone=True,
        note="the s31 in-force projections (w_opened/w_parent/w_dep derived from w_open/"
             "w_parent_e/w_dep_e) need ledger_tnow.lp's superseded/1 to be MEANINGFUL, same "
             "shape as work_items.lp above. work_succ_star_via_closure/2 additionally needs "
             "closure.lp's star/3 (soft)."),
    "ledger_support.lp": ModuleSpec(
        provides=("support_edge/3", "support_star/2", "support_cycle/1", "exposure/2",
                  "exposure_expired/2", "affirmed/2", "exposure_undischarged/2",
                  "affirm_sod_violation/1"),
        requires=("ledger_tnow.lp",),
        stands_alone=True,
        note="header's own words: 'loaded ON TOP OF ledger_tnow.lp -- it consumes in_force/1, "
             "superseded/1, enacts/2, answers/2 from that program'; composes with "
             "ledger_assumes.lp when present (soft, #defined)."),
    "ledger_dto.lp": ModuleSpec(
        provides=("decomposed/1", "decomp_attested/1", "decomp_attested_authentic/1",
                  "decomp_pending_attestation/1", "decomp_sod_violation/1", "fragment_in_force/1",
                  "fragment_in_force_authentic/1", "synthetic_standing/1", "fragment_pending/1",
                  "clause_defeat_moot_dto/2", "rekey_debt/3", "premature_eviction/2",
                  "referent_in_current/1", "decomp_evicts_referent/1"),
        requires=("ledger_tnow.lp",),
        stands_alone=True,
        note="header's own words: 'loaded ON TOP OF ledger_tnow.lp (which supplies superseded/1, "
             "amends/2, enacts/2, answers/2)'; exercised on a scratch lineage only."),
    "ledger_assumes.lp": ModuleSpec(
        provides=("assumption_in_force/1", "assumption_not_in_force/1", "expired_temporal/1",
                  "expired_horizon/1", "resting_on_expired/2", "resting_on_superseded/2"),
        requires=("ledger_tnow.lp",),
        stands_alone=True,
        note="header's own words: 'MUST be loaded ON TOP OF ledger_tnow.lp -- it consumes "
             "superseded/1 from that program's supersession closure'."),
    "ledger_acts.lp": ModuleSpec(
        provides=("act_ledgered/1", "unledgered_lr/1", "claim_matched/1", "stale_attestation/2",
                  "stale_attest/2", "stale_nonattest/2", "claimed_without_act/1",
                  "unledgered_span/2"),
        requires=("ledger_tnow.lp",),
        stands_alone=True,
        note="header's own words: 'Loaded ON TOP OF ledger_tnow.lp (consumes in_force/1, "
             "superseded/1, supersedes/2, amends/2 from it)'."),
    "contemporaneity.lp": ModuleSpec(
        provides=("refusal_fingerprint/1", "token_burst/1", "intake_shape/1", "ts_cluster/2",
                  "silence/2", "backfill_suspect/1", "late_declared/1", "verdict/1"),
        requires=(),
        stands_alone=True,
        note="the sole producer of the contemporaneity verdict; reads its own EDB "
             "(engine/contemp_edb.py) directly, no other .lp module."),
    "preamble_ordering.lp": ModuleSpec(
        provides=("ob_discharged/2", "ob_violated/2", "ob_undecidable/3", "preamble_verdict/2"),
        requires=("contemporaneity.lp",),
        stands_alone=True,
        note="header's own words: 'this file stacks ON TOP of engine/lp/contemporaneity.lp "
             "(F12's imports: token/1, backfill_suspect/1, late_declared/1)'; work_items.lp is "
             "named OPTIONAL there (F11's s22-violations arm, #defined-guarded)."),
    "ordering_violations.lp": ModuleSpec(
        provides=("close_before_dependency_violated/3", "conditional_precedence_violated/3",
                  "dependency_cycle/1", "ordering_verdict/2"),
        requires=(),
        stands_alone=True,
        note="reads work_opened/work_closed/work_depends + constraint_precedes directly off "
             "engine/ordering_edb.py; does not compose with work_items.lp or closure.lp (its own "
             "ordering_edge_star is a deliberate union-of-two-edge-families closure, a different "
             "composition than closure.lp's kind-indexed one -- see closure.lp's own scope note)."),
    "review_gap_audit.lp": ModuleSpec(
        provides=("discharges/2", "flagged/1"),
        requires=("ledger_tnow.lp",),
        stands_alone=True,
        note="single-hop superseded reading is DELIBERATE (mirrors s13.review_gap's own SQL "
             "semantics, not ledger_tnow.lp's transitive sup_star) -- composes with ledger_tnow.lp "
             "only in the loose sense of sharing the superseded/1 NAME, not its closure."),
    "ledger_defeat.lp": ModuleSpec(
        provides=("model_defeated/3", "credited/1", "exposure_model/2",
                  "exposure_model_undischarged/2", "model_defeated_row/1", "defeat_input/1"),
        requires=("ledger_tnow.lp", "ledger_support.lp"),
        stands_alone=True,
        note="design/FABLE-DEFEAT-PIPELINE-SPEC.md §7: model_defeated's in-force tests read "
             "superseded/1 (ledger_tnow.lp) to be MEANINGFUL, same shape as work_items.lp's own "
             "note; the CASCADE half additionally needs support_star/2 + affirmed/2 "
             "(ledger_support.lp) to be MEANINGFUL -- absent, exposure_model/2 silently reads "
             "'nothing supports anything' rather than refusing. Meaningfulness, not "
             "groundability, is what the 'defeat' LAYER entry below protects."),
    "verification_stats.lp": ModuleSpec(
        provides=("count_workflow_verdict/3", "count_role_verdict/3", "count_round_verdict/3",
                  "count_verdict/2", "count_unparseable/1"),
        requires=(),
        stands_alone=True,
        note="reads engine/verification_stats_edb.py directly; no composition with any other "
             "engine/lp module."),
}


# ==== LAYERS ==================================================================================
# The named, checkable program stacks this codebase's own runners actually compose (plan step
# 8(ii)/(iii)). A layer's tuple is the COMPLETE required member set, in load order; a runner that
# wants to ground a layer calls `require_layer_stack(layer, loaded)` with the program-NAME list it
# is about to hand to clingo -- a subset refuses loudly (RegistryError, teach-text naming the
# missing member and why), a superset (extra modules alongside the layer) is accepted.
LAYERS: dict[str, tuple[str, ...]] = {
    "tnow": ("ledger_tnow.lp",),
    "work": ("ledger_tnow.lp", "work_items.lp", "work_review.lp"),
    "defeat": ("ledger_tnow.lp", "ledger_support.lp", "ledger_defeat.lp"),
}


class RegistryError(RuntimeError):
    """Raised when a caller's program-name list does not satisfy a named layer's required member
    set (ADR-0002 fail-loudly; the F7 mis-stacked-invocation hazard this registry forecloses)."""


def require_layer_stack(layer: str, loaded: list[str]) -> None:
    """Refuse LOUDLY if `loaded` (the program-NAME list, e.g. ['ledger_tnow.lp', 'work_items.lp'],
    a caller is about to hand to clingo) does not carry every module LAYERS[layer] declares
    required. Never lets a mis-stacked invocation silently ground an empty/wrong closure the way
    the .lp files' own `#defined` guards would (that idiom is right for the single-program case;
    this is the composed-runner net the corpus's own consult F7 finding named as missing)."""
    if layer not in LAYERS:
        raise RegistryError(
            f"unknown layer {layer!r} -- known layers: {sorted(LAYERS)}. A layer is registered "
            f"in engine/lp_registry.py's LAYERS dict, not invented ad hoc at the call site.")
    required = LAYERS[layer]
    loaded_set = set(loaded)
    missing = [m for m in required if m not in loaded_set]
    if missing:
        raise RegistryError(
            f"REFUSED: layer {layer!r} requires {list(required)} but the invocation only loaded "
            f"{loaded!r} -- missing {missing}. Grounding this stack anyway would NOT raise (every "
            f"engine/lp/*.lp module's own `#defined` guards degrade a missing producer to an empty "
            f"extension, never a clingo error) -- it would silently ground a WRONG closure instead "
            f"of the intended one (e.g. work_items.lp/work_review.lp's in-force filtering reading "
            f"'nothing retracted' rather than refusing when ledger_tnow.lp is absent from the "
            f"'{layer}' stack) -- the exact F49 vacuous-pass class this corpus refuses elsewhere. "
            f"Add the missing module(s) to the invocation, or use engine/lp_registry.MODULES to "
            f"check what each one provides/requires before composing a stack by hand.")


def layer_paths(layer: str, lp_dir) -> list:
    """Resolve LAYERS[layer]'s module names to Path objects under `lp_dir` (typically
    engine/lp/), in the layer's declared load order -- the convenience a runner calls once it has
    already passed `require_layer_stack` (or is calling this BEFORE building its `loaded` list;
    both orders are legitimate, this function does not itself check membership)."""
    d = Path(lp_dir)
    return [d / name for name in LAYERS[layer]]


def main(argv: list[str] | None = None) -> int:
    """Print the registry (module -> provides/requires/stands_alone; layer -> member stack) --
    a human-readable dump of the same data `require_layer_stack` enforces mechanically."""
    print("# engine/lp_registry -- MODULES")
    for name, spec in sorted(MODULES.items()):
        print(f"  {name}")
        print(f"    provides: {list(spec.provides)}")
        print(f"    requires: {list(spec.requires)}")
        print(f"    stands_alone: {spec.stands_alone}")
        if spec.note:
            print(f"    note: {spec.note}")
    print("\n# engine/lp_registry -- LAYERS")
    for name, members in sorted(LAYERS.items()):
        print(f"  {name}: {list(members)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
