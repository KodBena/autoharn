#!/usr/bin/env python3
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

EACH LAYERS ENTRY IS A TYPED LayerSpec, NOT A BARE PROGRAM-NAME TUPLE (design/
FABLE-JUDGE-LAYER-CAPABILITY-CLOSURE-SPEC.md, RATIFIED 2026-07-27; the fix for ledger row 1459's
"bare `./judge` crashes on `entitlement`" defect). Before this build, "what does a layer need to
detect its own substrate" and "what does a layer's SQL floor compare" lived as two separate
if-chains in engine/ledger_differential.py (`layer_capability`, `_LAYER_FLOOR_PREDS`) that fell
open the moment a new layer was registered here without an entry there -- exactly what happened
when `entitlement` landed. This registry is the single home the spec's Rule-2(a) answer names: a
`LayerSpec` carries the program stack (unchanged), a `capability` probe (name -> (bool, reason),
the SAME shape and SAME reason strings `layer_capability`'s deleted if-chain used, moved here
verbatim), and a `floor` disposition -- the frozenset of predicate names the SQL floor compares,
or an honest `NoFloor(reason)`/`FloorElsewhere()` marker when no such comparison exists (see
their own docstrings). `_validate_layer_registry` runs at IMPORT TIME (module scope, below) and
refuses loudly if any entry is missing a part -- so registering a layer without all three, from
now on, fails at import in every test and every commit, never at the next operator's bare
`judge`.

Lazy imports banned (CLAUDE.md)."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from belief_floor import BELIEF_PREDS, belief_capable
from ledger_edb import resolve
from ledger_floor import DEFEAT_PREDS, WORK_ITEM_PREDS, WORK_REVIEW_PREDS


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
    "ledger_belief.lp": ModuleSpec(
        provides=("contested_belief/2", "contest_resolved/2", "credited_belief/1",
                  "corroboration_grade/2", "shared_ancestor/3", "belief_doubt/1",
                  "belief_wellfounded/1", "belief_grounded/1"),
        requires=("ledger_tnow.lp", "ledger_support.lp", "ledger_defeat.lp"),
        stands_alone=True,
        note="design/FABLE-BELIEF-SUBSTRATE-SPEC.md §2.2/§3.4 (ratified ledger rows 1914/1919): "
             "credited_belief's well-foundedness composes model_defeated_row/1 (ledger_defeat.lp) "
             "to un-found a belief resting on a defeated premise/source -- the SAME 'meaningful, "
             "not merely groundable' shape ledger_defeat.lp's own note describes for "
             "support_star/affirmed; the 'belief' LAYER entry below is what a differential "
             "runner actually enforces."),
    "ledger_entitlement.lp": ModuleSpec(
        provides=("reaches_genesis/1",),
        requires=("ledger_tnow.lp",),
        stands_alone=True,
        note="design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §1 item 2: the chain closure in the "
             "ledger_defeat.lp stratification shape, beside in_force/1, never into it -- reads "
             "principal/1, acts_for_edge/2, genesis/1, principal_active/1 off "
             "engine/ledger_edb.py's export_entitlement(), the independent second derivation of "
             "kernel/lineage/s60-entitlement-enforcement.sql's "
             "principal_authority_chain_reaches_genesis(). Does not itself consume in_force/1/"
             "superseded/1 by name (acts_for_edge/2 arrives already in-force-filtered from the "
             "exporter, mirroring ledger_defeat.lp's own trust_grant/3) -- the 'entitlement' "
             "LAYER entry below is what a differential runner actually enforces."),
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
# 8(ii)/(iii); typed per LayerSpec, closure spec §2 item 1). A layer's `programs` tuple is the
# COMPLETE required member set, in load order; a runner that wants to ground a layer calls
# `require_layer_stack(layer, loaded)` with the program-NAME list it is about to hand to clingo --
# a subset refuses loudly (RegistryError, teach-text naming the missing member and why), a
# superset (extra modules alongside the layer) is accepted.

WORK_LAYER_PREDS = frozenset(WORK_ITEM_PREDS) | frozenset(WORK_REVIEW_PREDS)


class RegistryError(RuntimeError):
    """Raised when a caller's program-name list does not satisfy a named layer's required member
    set (ADR-0002 fail-loudly; the F7 mis-stacked-invocation hazard this registry forecloses), OR
    (closure spec §2 items 2/4) when the import-time registry validation finds an incomplete
    LayerSpec, OR when an explicit `--layer <x>` request lands on a layer whose floor disposition
    is `NoFloor` -- the typed refusal design item 4 calls for, sourced from the registry entry's
    own declared reason rather than a bare `NotImplementedError`."""


@dataclass(frozen=True)
class NoFloor:
    """A layer's floor disposition: capability detection may exist, but NO complete SQL-floor
    differential is wired for this layer yet on this build -- an honest, filed gap (closure spec
    §2 item 3's fallback), never silently widened into a passing (AGREE) comparison. `reason` is
    the one-line teaching text a bare-path skip line or an explicit-request refusal prints."""
    reason: str


@dataclass(frozen=True)
class FloorElsewhere:
    """A layer's floor disposition: the floor comparison EXISTS and runs, but through a mechanism
    OTHER than run_layer_differential's `preds`-restricted lookup -- today, only 'tnow', whose
    floor is the ORIGINAL, unrestricted run_differential/floor_atoms comparison that
    ledger_differential.main() special-cases before ever reaching run_layer_differential (that
    special-casing predates this build and is untouched by it). Deliberately a DIFFERENT type
    than `NoFloor`: 'tnow' unambiguously HAS a floor, just not one this field's consumers should
    ever read as a predicate-restriction set or a stated absence -- collapsing the two into one
    representation would let a future refactor that unifies the two code paths misread 'runs
    elsewhere' as 'doesn't exist', exactly the representable-but-wrong state ADR-0000 Rule 2(a)
    asks a fix to foreclose, not merely avoid today."""


@dataclass(frozen=True)
class LayerSpec:
    """One judge LAYER entry (closure spec §2 item 1): the program stack (unchanged, load order),
    a capability probe (`name -> (bool, reason)`, the exact shape `layer_capability` returns --
    the SAME checks and SAME reason strings the four pre-existing layers' branches used, moved
    here byte-verbatim, not retyped; see each `_*_capability` function below), and a floor
    disposition: `frozenset[str]` (the predicate names the SQL floor compares -- what
    `_LAYER_FLOOR_PREDS` held pre-this-build), `NoFloor(reason)` (no such comparison exists yet,
    honestly declared), or `FloorElsewhere()` ('tnow' only -- see that class's own docstring)."""
    programs: tuple[str, ...]
    capability: Callable[[str], tuple[bool, str]]
    floor: frozenset[str] | NoFloor | FloorElsewhere


# ---- capability probes -------------------------------------------------------------------------
# Moved VERBATIM (byte-diffed in the build report, not retyped) from
# engine/ledger_differential.py's now-deleted `layer_capability` if-chain -- the single home this
# registry already was for load order becomes the single home for capability detection too, per
# the closure spec's Rule 2(a) answer. Each probe takes the target NAME (matching
# `layer_capability`'s own signature) and returns (bool, reason), same as before.

def _tnow_capability(name: str) -> tuple[bool, str]:
    """'tnow' is always capable: every ledger (even the pre-kernel/empty case) has the entry rows
    both T_now and the SQL floor read; there is no schema precondition to detect, so it is never
    auto-declared incapable."""
    return True, ""


def _work_capability(name: str) -> tuple[bool, str]:
    t = resolve(name)
    if not t.has_col("work_slug"):
        return False, ("target has no `work_slug` column (pre-s22 lineage) -- "
                       "the 'work' layer has no substrate here, capability absent")
    return True, ""


def _defeat_capability(name: str) -> tuple[bool, str]:
    t = resolve(name)
    if not (t.has_col("principal_binding_active") and t.has_col("principal_competence_activity")):
        return False, ("target has no principal_binding_active/"
                       "principal_competence_activity columns (pre-s41 lineage) "
                       "-- the 'defeat' layer has no grant substrate here, "
                       "capability absent, not record-empty")
    return True, ""


def _belief_capability(name: str) -> tuple[bool, str]:
    """Moved verbatim from belief_differential.belief_layer_capability (whose one caller was
    ledger_differential.layer_capability's now-deleted if-chain); belief_layer_capability itself
    is deleted from belief_differential.py by this same delta (this was its only caller) rather
    than kept as an orphaned wrapper. Same belief_floor.belief_capable has_col-idiom check, same
    reason string."""
    t = resolve(name)
    if not belief_capable(t):
        return False, ("target has no `statement` column, or `actor` is not integer-typed -- "
                       "the 'belief' layer has no substrate here, capability absent, "
                       "not record-empty")
    return True, ""


def _entitlement_capability(name: str) -> tuple[bool, str]:
    """NEW (closure spec §2 item 3): the s60 marker column `entitlement_act_class`, same has_col
    idiom the work/defeat probes use. Builder-verified (build report) against
    kernel/lineage/s60-entitlement-enforcement.sql: that migration adds
    `entitlement_act_class` ALONGSIDE the principal_relation/principal_binding_active/
    principal_object substrate engine/ledger_edb.py's export_entitlement() also gates on, in the
    SAME file -- so a target carrying the marker column always carries the rest, making a single
    has_col check a sound proxy for the whole capability gate (exactly as 'work's single
    work_slug check, and 'defeat's two-column check, are proxies for their own richer
    substrates). Builder-verified against kernel/lineage/s64-principal-stamps-delegation-
    conditions.sql too: s64 adds delegation_expiry/delegation_scope_classes to the SAME s41-era
    ledger kind but never touches entitlement_act_class -- this probe is unchanged by s64,
    verified, not assumed."""
    t = resolve(name)
    if not t.has_col("entitlement_act_class"):
        return False, ("target has no `entitlement_act_class` column (pre-s60 lineage) -- "
                       "the 'entitlement' layer has no substrate here, capability absent, "
                       "not record-empty")
    return True, ""


LAYERS: dict[str, LayerSpec] = {
    "tnow": LayerSpec(("ledger_tnow.lp",), _tnow_capability, FloorElsewhere()),
    "work": LayerSpec(("ledger_tnow.lp", "work_items.lp", "work_review.lp"),
                      _work_capability, WORK_LAYER_PREDS),
    "defeat": LayerSpec(("ledger_tnow.lp", "ledger_support.lp", "ledger_defeat.lp"),
                        _defeat_capability, frozenset(DEFEAT_PREDS)),
    "belief": LayerSpec(("ledger_tnow.lp", "ledger_support.lp", "ledger_defeat.lp",
                         "ledger_belief.lp"), _belief_capability, frozenset(BELIEF_PREDS)),
    "entitlement": LayerSpec(
        ("ledger_tnow.lp", "ledger_entitlement.lp"), _entitlement_capability,
        NoFloor("no SQL-floor differential is wired for the 'entitlement' layer yet "
                "(engine/ledger_floor.py has no entitlement floor function) -- capability "
                "detection only; the floor-wiring gap is FILED (design/FABLE-JUDGE-LAYER-"
                "CAPABILITY-CLOSURE-SPEC.md §2 item 3's honest-no-floor fallback; a ledger row "
                "for the floor-wiring follow-on is the orchestrator's to file, this build has no "
                "ledger-write access) -- never silently widened into an AGREE")),
}


def _validate_layer_registry(layers: dict[str, LayerSpec], modules: dict[str, ModuleSpec]) -> None:
    """THE IMPORT-TIME CLOSURE CHECK (closure spec §2 item 1's mandate): a plain module-scope
    check over the completed registry (no lazy import -- CLAUDE.md's ban is about
    runtime-deferred IMPORTS, not ordinary code executing at module scope over already-imported
    names). Refuses LOUDLY if any LAYERS entry is missing a part of its required triple: a
    non-empty program stack whose every member is a real MODULES entry, a callable capability
    probe, and a typed floor disposition. Takes the two dicts as PARAMETERS (not the module
    globals) precisely so a test can construct a synthetic, deliberately-incomplete registry and
    witness this refusal directly (the closure spec §4 negative-control leg) without
    monkeypatching this module's own LAYERS/MODULES."""
    for lname, spec in layers.items():
        if not spec.programs:
            raise RegistryError(
                f"LAYERS[{lname!r}] declares an empty program stack -- a layer with no members "
                f"is a missing declaration, not a stack.")
        missing_modules = [p for p in spec.programs if p not in modules]
        if missing_modules:
            raise RegistryError(
                f"LAYERS[{lname!r}] references undeclared MODULES entries {missing_modules} -- "
                f"every program a layer stacks must have its own MODULES declaration.")
        if not callable(spec.capability):
            raise RegistryError(
                f"LAYERS[{lname!r}] has no capability probe (got {spec.capability!r}) -- every "
                f"layer must declare how to detect its own substrate (closure spec §2 item 1).")
        if not isinstance(spec.floor, (frozenset, NoFloor, FloorElsewhere)):
            raise RegistryError(
                f"LAYERS[{lname!r}]'s floor disposition {spec.floor!r} is none of frozenset "
                f"(floor-preds), NoFloor(reason), or FloorElsewhere() -- every layer must declare "
                f"a floor disposition, honestly (closure spec §2 item 1).")


_validate_layer_registry(LAYERS, MODULES)


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
    required = LAYERS[layer].programs
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
    return [d / name for name in LAYERS[layer].programs]


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
    for name, spec in sorted(LAYERS.items()):
        floor_desc = (f"preds={sorted(spec.floor)}" if isinstance(spec.floor, frozenset)
                     else repr(spec.floor))
        print(f"  {name}: programs={list(spec.programs)} floor={floor_desc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
