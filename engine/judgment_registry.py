#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-07T17:13:48Z
#   last-change: 2026-07-09T14:32:28Z
#   contributors: 37017f46/main, be693afb/main
# <<< PROVENANCE-STAMP <<<

"""judgment_registry — THE one authority module for engine judgments (engine INC 1; ruling 110 D1/D2).

One home (ADR-0012 P1) for the JudgmentSpec record kind: one row per judgment CLASS the apparatus
runs today — every close-manifest line, every instrument, every `.lp` #shown judgment atom, the e17
kernel triggers. The Expectation record kind (instances on substrates) is INC 2's; nothing here
pretends to carry it. From this module the parity checker (`verify_registry_parity.py`) pins the
LIVE surface against the registry both ways (D2/F49): an implementation with no row FAILS; a row
with no implementation is RED-undischarged unless it carries a declared exclusion.

Field union per ruling 110 §1 (D1), with INC-1 honesty markers where a later increment owns the
mechanism: `complexity_class` is HAND-ASSERTED here and says so in `class_provenance` (the
mechanical checker is INC 3 — after which a hand-asserted class is unconstructible);
`verdict_enum` members are DECLARED here (the generator with injected per-family NOT_RUN members is
INC 2, D4). Law citations are NAMESPACED keys only (D15): RULING:/FIND:/BRIEF:/INV:/ADR: — a bare
"F11" is unconstructible (checked at import, ADR-0000 Rule 1).

Registry ledger discipline (D2), live from day one: rows are APPEND-ONLY and supersedes-chained —
`registry_baseline.json` banks (judgment_id, content-hash) for every row ever registered; the
parity checker REFUSES a changed hash unless a new row supersedes the old (the old row stays in
SPECS, superseded, citable). A regold is an F9-shaped CONTEST record (`ContestRecord`): the red it
answers, the authorizing law citation, mover and approver — approver is never the mover
(constructibility-checked).

Families (the eight-family taxonomy, design-semantics §2 as ratified through D1–D5):
  A record integrity · B currency/contemporaneity · C derived validity (T_now) ·
  D consumption soundness/flags · E obligation & independence · F claims-vs-acts differential ·
  G apparatus self-judgment · H review-residue routing (router only, never a content verdict).

CLI:
  judgment_registry.py                # print the registry summary (one line per spec)
  judgment_registry.py --family-map   # JSON: flag/atom/close-line name -> family (for the
                                      #   review-queue-debt close line, cross-repo, subprocess —
                                      #   the marriage-differential idiom, never a hand-sync)
  judgment_registry.py --impl-keys    # JSON: every implementation key -> judgment_id

Lazy imports banned. Read-only; no DB access.
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field, fields

_NAMESPACES = ("RULING:", "FIND:", "BRIEF:", "INV:", "ADR:")
_FAMILIES = frozenset("ABCDEFGH")
_STAGES = ("P0", "P1", "P2", "P3", "P4", "P5")


@dataclass(frozen=True)
class JudgmentSpec:
    """One judgment class. Frozen: a change is a NEW row that supersedes this one (D2)."""

    judgment_id: str
    family: str
    title: str
    # Declared members (INC 1). The generated per-family enum with the injected NOT_RUN member is
    # INC 2 (D4); until then this field is the declaration the generator will consume, not the enum.
    verdict_enum: tuple[str, ...]
    subject_ref_type: str  # row | row-set | edge | clause-fragment | span | stream-pair | meta
    law_citations: tuple[str, ...]  # namespaced (D15)
    engine: str  # SQL | ASP | SMT | FDE-lens | shell | python | none-router
    # Every implementation key this spec owns (D11: producers are registered encodings):
    #   close:<line> | instrument:<file> | lp:<file>#<atom>/<arity> | trigger:<name> | tool:<path>
    implementations: tuple[str, ...]
    # The differential is per-judgment declared, never assumed: a producer OR a reason (I12).
    second_producer: str | None = None
    second_producer_none_reason: str | None = None
    complexity_class: str | None = None  # A | B | C | C_t | D
    class_provenance: str = "hand-asserted (INC 1; mechanical checker lands INC 3, after which this is unconstructible)"
    tier_placement: str = "T2"
    promotion_stage: str = "P0"
    ruling42_ratification: str | None = None  # non-NULL REQUIRED at P4/P5 (ruling 42 / D21)
    goodhart_surface: str | None = None
    fixtures: tuple[str, ...] = ()
    mutations: tuple[str, ...] = ()  # each names the verdict it flips
    red_history: str | None = None
    teach_text_ref: str | None = None
    assumptions: tuple[str, ...] = ()
    adjudication_slot: bool = False
    adjudication_routing: str | None = None
    exclusion: str | None = None  # reason, where deliberately unimplemented/undischargeable
    spec_version: int = 1
    supersedes: str | None = None

    def __post_init__(self) -> None:
        # Constructibility (ADR-0000 Rule 1: illegal states unrepresentable at construction).
        if self.family not in _FAMILIES:
            raise ValueError(f"{self.judgment_id}: family {self.family!r} not in A-H")
        if self.promotion_stage not in _STAGES:
            raise ValueError(f"{self.judgment_id}: promotion_stage {self.promotion_stage!r}")
        if not self.law_citations:
            raise ValueError(f"{self.judgment_id}: a judgment with no law citation is apocryphal "
                             "(INC 1: loud; the constructor refusal itself is INC 3)")
        for c in self.law_citations:
            if not c.startswith(_NAMESPACES):
                raise ValueError(f"{self.judgment_id}: bare law key {c!r} — namespaced keys only (D15)")
        if not self.implementations and self.exclusion is None:
            raise ValueError(f"{self.judgment_id}: no implementation and no declared exclusion")
        if self.promotion_stage in ("P4", "P5") and not self.ruling42_ratification:
            raise ValueError(f"{self.judgment_id}: stage {self.promotion_stage} with NULL "
                             "ruling42_ratification is unconstructible (ruling 42 / D21)")
        if self.second_producer is None and self.second_producer_none_reason is None:
            raise ValueError(f"{self.judgment_id}: second_producer is a declared none-with-reason "
                             "(I12 row), never a silence")

    def content_hash(self) -> str:
        """The D2 append-only identity of this row's content."""
        payload = {f.name: getattr(self, f.name) for f in fields(self)}
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


@dataclass(frozen=True)
class ContestRecord:
    """An F9-shaped regold record (D2): any change to a banked golden/fixture expectation."""

    contest_id: str
    answers_red: str  # the red this regold answers (artifact ref)
    law_citation: str  # namespaced authorization
    mover: str
    approver: str

    def __post_init__(self) -> None:
        if not self.law_citation.startswith(_NAMESPACES):
            raise ValueError(f"{self.contest_id}: bare law key {self.law_citation!r} (D15)")
        if self.approver == self.mover:
            raise ValueError(f"{self.contest_id}: approver == mover ({self.mover!r}) — "
                             "a self-ratified regold is unconstructible (D2)")


_T2 = "T2 (close-time authority; no lower-tier shadow registered in INC 1)"
_NO2ND_SINGLE = "single producer today; a second encoding is beyond-INC-5 work (D11), declared not assumed"

SPECS: tuple[JudgmentSpec, ...] = (
    # ---- Family C — derived validity (T_now) --------------------------------------------------
    JudgmentSpec(
        judgment_id="tnow-derived-validity",
        family="C",
        title="In-force / head / answered / clause-defeat closure over the append-only ledger",
        verdict_enum=("IN-FORCE", "DEFEATED(by)", "CLAUSE-DEFEATED(by)", "ANSWERED(by)"),
        subject_ref_type="row",
        law_citations=("ADR:0000", "FIND:F28", "INV:I3"),
        engine="ASP",
        implementations=(
            "lp:ledger_tnow.lp#in_force/1", "lp:ledger_tnow.lp#head/2",
            "lp:ledger_tnow.lp#question_open/1", "lp:ledger_tnow.lp#question_answered/1",
            "lp:ledger_tnow.lp#clause_defeat/2", "lp:ledger_tnow.lp#clause_defeat_moot/2",
            "lp:ledger_tnow.lp#clause_defeat_withdrawn/2",
        ),
        second_producer="SQL floor (ledger_floor, reconciled by close:marriage_differential)",
        complexity_class="C",
        fixtures=("marriage banked targets s10-s13/nla (bit-identical reproduction)",),
        promotion_stage="P2",
    ),
    JudgmentSpec(
        judgment_id="dto-decomposition-validity",
        family="C",
        title="DTO decomposition status: decomposed / attested(authentic) / pending / SoD violation",
        verdict_enum=("DECOMPOSED", "ATTESTED-AUTHENTIC", "PENDING-ATTESTATION", "SOD-VIOLATION"),
        subject_ref_type="row",
        law_citations=("FIND:F44", "ADR:0000"),
        engine="ASP",
        implementations=(
            "lp:ledger_dto.lp#decomposed/1", "lp:ledger_dto.lp#decomp_attested/1",
            "lp:ledger_dto.lp#decomp_attested_authentic/1",
            "lp:ledger_dto.lp#decomp_pending_attestation/1",
            "lp:ledger_dto.lp#decomp_sod_violation/1", "lp:ledger_dto.lp#fragment_in_force/1",
            "lp:ledger_dto.lp#fragment_in_force_authentic/1", "lp:ledger_dto.lp#fragment_pending/1",
            "lp:ledger_dto.lp#clause_defeat_moot_dto/2", "lp:ledger_dto.lp#decomp_evicts_referent/1",
            "lp:ledger_dto.lp#premature_eviction/2", "lp:ledger_dto.lp#referent_in_current/1",
            "lp:ledger_dto.lp#rekey_debt/3", "lp:ledger_dto.lp#synthetic_standing/1",
        ),
        second_producer=None,
        second_producer_none_reason=_NO2ND_SINGLE,
        complexity_class="C",
        promotion_stage="P1",
    ),
    # ---- Family D — consumption soundness / flags ---------------------------------------------
    JudgmentSpec(
        judgment_id="consumption-soundness",
        family="D",
        title="unsound_derivation / launder(negative control) / alias_surface / stale_enactment_row / cond-2",
        verdict_enum=("SOUND", "UNSOUND(D)", "FLAG(kind)"),
        subject_ref_type="edge",
        law_citations=("FIND:F28", "FIND:F51", "ADR:0002"),
        engine="ASP",
        implementations=(
            "lp:ledger_tnow.lp#unsound_derivation/2", "lp:ledger_tnow.lp#launder/3",
            "lp:ledger_tnow.lp#alias_surface/2", "lp:ledger_tnow.lp#stale_enactment_row/2",
            "lp:ledger_tnow.lp#condition2_individuation/1",
            "instrument:soundness.py", "close:soundness",
        ),
        second_producer="soundness.lp ASP twin (reconciled by close:soundness_twin)",
        complexity_class="C",
        adjudication_slot=True,
        adjudication_routing="review queue (alias_surface has proven false positives — FIND:F51)",
        fixtures=("e12 miscite 31->27 caught live (alias_surface)",),
        promotion_stage="P2",
    ),
    JudgmentSpec(
        judgment_id="stale-enactment-debt",
        family="D",
        title="Files carrying work under a later-retired antecedent (journal x ledger join)",
        verdict_enum=("NO-DEBT", "STALE-DEBT(rows)"),
        subject_ref_type="span",
        law_citations=("FIND:F49", "ADR:0013"),
        engine="python",
        implementations=("instrument:stale_enactment_debt.py", "close:stale_enactment_debt"),
        second_producer=None,
        second_producer_none_reason=_NO2ND_SINGLE,
        complexity_class="B",
        promotion_stage="P1",
    ),
    JudgmentSpec(
        judgment_id="findings-disposition-gate",
        family="D",
        title="OPEN findings block a close (prose never disposes — F28)",
        verdict_enum=("GREEN", "RED(open-findings)", "QUARANTINED"),
        subject_ref_type="row-set",
        law_citations=("FIND:F28", "ADR:0013"),
        engine="SQL",
        implementations=("close:findings_gate", "tool:claude_harness/tools/findings_gate.py"),
        second_producer=None,
        second_producer_none_reason="the gate reads one view (harness.finding_open); its negative "
                                    "control is the seen-red fixture, not a second encoding",
        complexity_class="A",
        fixtures=("finding 6a TRUNCATE-CASCADE hole seen RED before disposal",),
        promotion_stage="P2",
    ),
    JudgmentSpec(
        judgment_id="why-orphan-flag",
        family="D",
        title="WHY-ledger orphan flag (rationale row whose subject vanished)",
        verdict_enum=("BOUND", "ORPHANED"),
        subject_ref_type="row",
        law_citations=("FIND:F28",),
        engine="ASP",
        implementations=("lp:why_layer.lp#why_orphaned/1",),
        second_producer=None,
        second_producer_none_reason=_NO2ND_SINGLE,
        complexity_class="C",
        promotion_stage="P0",
    ),
    JudgmentSpec(
        judgment_id="assumption-expiry",
        family="B",
        title="Assumption validity bounds: in-force / expired (temporal + horizon) and what rests on them",
        verdict_enum=("IN-BOUND", "EXPIRED", "UNBOUNDED-DECLARED"),
        subject_ref_type="row",
        law_citations=("INV:I7",),
        engine="ASP",
        implementations=(
            "lp:ledger_assumes.lp#assumption_in_force/1", "lp:ledger_assumes.lp#assumption_not_in_force/1",
            "lp:ledger_assumes.lp#expired_temporal/1", "lp:ledger_assumes.lp#expired_horizon/1",
            "lp:ledger_assumes.lp#resting_on_expired/2", "lp:ledger_assumes.lp#resting_on_superseded/2",
        ),
        second_producer=None,
        second_producer_none_reason=_NO2ND_SINGLE,
        complexity_class="C_t",
        assumptions=("identity for expiry findings keys on the crossed bound, never the raw clock (D7) — "
                     "the retrofit is INC 2 work",),
        promotion_stage="P1",
    ),
    JudgmentSpec(
        judgment_id="support-exposure-closure",
        family="E",
        title="Affirms/support closure: exposure discharge, affirm-SoD, support cycles/stars",
        verdict_enum=("DISCHARGED(by)", "UNDISCHARGED", "EXPOSURE-EXPIRED", "SOD-VIOLATION"),
        subject_ref_type="edge",
        law_citations=("BRIEF:G7", "FIND:F28"),
        engine="ASP",
        implementations=(
            "lp:ledger_support.lp#affirmed/2", "lp:ledger_support.lp#affirm_sod_violation/1",
            "lp:ledger_support.lp#exposure/2", "lp:ledger_support.lp#exposure_expired/2",
            "lp:ledger_support.lp#exposure_undischarged/2", "lp:ledger_support.lp#support_cycle/1",
            "lp:ledger_support.lp#support_edge/3", "lp:ledger_support.lp#support_star/2",
        ),
        second_producer=None,
        second_producer_none_reason=_NO2ND_SINGLE,
        complexity_class="C",
        promotion_stage="P1",
    ),
    # ---- Family B — currency & contemporaneity ------------------------------------------------
    JudgmentSpec(
        judgment_id="contemporaneity",
        family="B",
        title="Ledger-write contemporaneity (bursts/batching) + act-gate journal summary",
        verdict_enum=("CONTEMPORANEOUS", "BATCHED", "GAP(span)"),
        subject_ref_type="stream-pair",
        law_citations=("INV:I1", "FIND:F49"),
        engine="python",
        implementations=("instrument:contemporaneity.py", "close:contemporaneity"),
        second_producer=None,
        second_producer_none_reason=_NO2ND_SINGLE,
        complexity_class="B",
        assumptions=("ts comparisons are against an external clock only (no in-record ordering)",),
        promotion_stage="P2",
    ),
    JudgmentSpec(
        judgment_id="observed-currency",
        family="B",
        title="Citation currency: record-observed at citation time (F42/F46) — flag, never a gate",
        verdict_enum=("OBSERVED-CURRENT", "UNOBSERVED-AT-CITATION", "STALE-OBSERVED"),
        subject_ref_type="row",
        law_citations=("FIND:F42", "FIND:F46"),
        engine="python",
        implementations=("instrument:observed_currency.py", "close:observed_currency",
                         "instrument:read_currency.py"),
        second_producer=None,
        second_producer_none_reason=_NO2ND_SINGLE,
        complexity_class="B",
        assumptions=("warning polarity is LAW (D14): currency never denies a write",),
        promotion_stage="P2",
    ),
    # ---- Family A — record integrity ----------------------------------------------------------
    JudgmentSpec(
        judgment_id="kernel-write-validation",
        family="A",
        title="Write-time record integrity: actor resolution, edge target-shape, review shape, one-row batches",
        verdict_enum=("ACCEPTED", "REFUSED(reason)"),
        subject_ref_type="row",
        law_citations=("ADR:0000", "ADR:0002", "FIND:F26"),
        engine="SQL",
        implementations=("trigger:set_actor", "trigger:validate_enacts", "trigger:validate_amends",
                         "trigger:validate_answers", "trigger:validate_review",
                         "trigger:one_row_per_insert"),
        second_producer=None,
        second_producer_none_reason="write-time refusals re-derive at close via the T2 consumers "
                                    "(the D11 verdict-equivalence duty formalizes at INC 4)",
        complexity_class="A",
        fixtures=("e17 enacts=[15] typo refused live (earlier-target FK)",),
        promotion_stage="P3",
        goodhart_surface="subject-controlled inserts; refusal text is the teach surface (F26: an "
                         "illegible deny converts to label evasion)",
    ),
    JudgmentSpec(
        judgment_id="kernel-append-only",
        family="A",
        title="Append-only integrity of the unit ledger + review_detail (UPDATE/DELETE/TRUNCATE refused)",
        verdict_enum=("HELD", "REFUSED(mutation)"),
        subject_ref_type="row-set",
        law_citations=("ADR:0000", "BRIEF:G1"),
        engine="SQL",
        implementations=("trigger:append_only_row", "trigger:append_only_truncate",
                         "trigger:review_detail_append_only", "trigger:review_detail_append_only_trunc"),
        second_producer="close:append_only_integrity (the audit-spine close line re-checks trigger presence)",
        complexity_class="A",
        promotion_stage="P3",
    ),
    # -- census-ratification amendment (c) supersessions (D2 chain; the F9 contest record is in
    # CONTESTS below): the two pre-engine kernel rows gain the DECLARED substrate-MAC scope. The
    # v1 rows above stay byte-identical as citable history; these rows are the live chain heads.
    JudgmentSpec(
        judgment_id="kernel-write-validation-2",
        family="A",
        title="Write-time record integrity: actor resolution, edge target-shape, review shape, one-row batches",
        verdict_enum=("ACCEPTED", "REFUSED(reason)"),
        subject_ref_type="row",
        law_citations=("ADR:0000", "ADR:0002", "FIND:F26"),
        engine="SQL",
        implementations=("trigger:set_actor", "trigger:validate_enacts", "trigger:validate_amends",
                         "trigger:validate_answers", "trigger:validate_review",
                         "trigger:one_row_per_insert"),
        second_producer=None,
        second_producer_none_reason="write-time refusals re-derive at close via the T2 consumers "
                                    "(the D11 verdict-equivalence duty formalizes at INC 4)",
        complexity_class="A",
        fixtures=("e17 enacts=[15] typo refused live (earlier-target FK)",),
        promotion_stage="P3",
        goodhart_surface="subject-controlled inserts; refusal text is the teach surface (F26: an "
                         "illegible deny converts to label evasion)",
        assumptions=("deny surface is pre-engine substrate MAC (FIND:F15 / INV:I3), grandfathered "
                     "with the e17 kernel, OUTSIDE ruling 42's engine-promotion ladder; close-time "
                     "verdict-equivalence owed at INC 4 (D11)",),
        spec_version=2,
        supersedes="kernel-write-validation",
    ),
    JudgmentSpec(
        judgment_id="kernel-append-only-2",
        family="A",
        title="Append-only integrity of the unit ledger + review_detail (UPDATE/DELETE/TRUNCATE refused)",
        verdict_enum=("HELD", "REFUSED(mutation)"),
        subject_ref_type="row-set",
        law_citations=("ADR:0000", "BRIEF:G1"),
        engine="SQL",
        implementations=("trigger:append_only_row", "trigger:append_only_truncate",
                         "trigger:review_detail_append_only", "trigger:review_detail_append_only_trunc"),
        second_producer="close:append_only_integrity (the audit-spine close line re-checks trigger presence)",
        complexity_class="A",
        assumptions=("deny surface is pre-engine substrate MAC (FIND:F15 / INV:I3), grandfathered "
                     "with the e17 kernel, OUTSIDE ruling 42's engine-promotion ladder; close-time "
                     "verdict-equivalence owed at INC 4 (D11)",),
        promotion_stage="P3",
        spec_version=2,
        supersedes="kernel-append-only",
    ),
    JudgmentSpec(
        judgment_id="audit-spine-append-only",
        family="A",
        title="acts.ruling / audit-spine append-only + hash-matches trigger presence, checked at close",
        verdict_enum=("OK", "RED(spine-mutable)"),
        subject_ref_type="meta",
        law_citations=("ADR:0011", "BRIEF:G1"),
        engine="SQL",
        implementations=("close:append_only_integrity",),
        second_producer=None,
        second_producer_none_reason="the line IS the second witness over the kernel triggers above",
        complexity_class="A",
        fixtures=("both-way fixture-proven at the foreclosure back-fill (2026-07-07)",),
        promotion_stage="P2",
    ),
    JudgmentSpec(
        judgment_id="delivery-freight-integrity",
        family="A",
        title="acts.ruling delivery rows byte-key their freight (delivers-FK + sha match)",
        verdict_enum=("OK", "RED(unkeyed-or-mismatched)"),
        subject_ref_type="edge",
        law_citations=("FIND:F22", "ADR:0002"),
        engine="SQL",
        implementations=("close:delivery_freight_integrity",),
        second_producer="trigger:ruling-delivers-integrity (db-side, write-time half; kernel-owned)",
        complexity_class="A",
        red_history="finding 35 (ruling-delivery-unkeyed, 'air raid siren') — fixed fc19",
        promotion_stage="P2",
    ),
    JudgmentSpec(
        judgment_id="foreclosure-debt",
        family="G",
        title="Every fixed finding is foreclosed on a registered line with banked red evidence",
        verdict_enum=("GREEN", "RED(debt)"),
        subject_ref_type="row-set",
        law_citations=("ADR:0000", "ADR:0011"),
        engine="SQL",
        implementations=("close:foreclosure_debt",),
        second_producer="close:foreclosure_integrity (referential half)",
        complexity_class="A",
        promotion_stage="P2",
    ),
    JudgmentSpec(
        judgment_id="foreclosure-integrity",
        family="G",
        title="class_foreclosure rows reference registered lines + existing red artifacts (sha-checked)",
        verdict_enum=("GREEN", "RED(dangling)"),
        subject_ref_type="row-set",
        law_citations=("ADR:0011", "ADR:0005"),
        engine="SQL",
        implementations=("close:foreclosure_integrity",),
        second_producer=None,
        second_producer_none_reason="paired with close:foreclosure_debt; the pair is the differential",
        complexity_class="A",
        promotion_stage="P2",
    ),
    # ---- Family E — obligation & independence -------------------------------------------------
    JudgmentSpec(
        judgment_id="stamp-independence-gate",
        family="E",
        title="Interception-stamp independence: technical/independent require stamp-distinct "
              "invocations; refuse-and-teach at the write (the e17 gate — ruling 42's template; "
              "recorded P4, P5-pending)",
        verdict_enum=("ACCEPTED", "REFUSED-AND-TAUGHT"),
        subject_ref_type="row",
        law_citations=("RULING:29", "RULING:42", "RULING:107"),
        engine="SQL",
        implementations=("trigger:set_stamp", "trigger:validate_independence"),
        second_producer="review_fixpoint close criterion re-derives stamp-distinctness at close",
        complexity_class="A",
        promotion_stage="P4",
        ruling42_ratification="RULING:42",
        teach_text_ref="s17-independence-vocabulary.sql (frozen refusal text; e17/e18 specimen-tested)",
        fixtures=("e17 TEACH-ACCEPT->HONEST-DISTINCT (rows 12/17/18)",
                  "e18 self-ledgered snag (entries 6/7/8/9)",
                  "e18 finding 45 four refusals, id gaps 10-13, zero orphans"),
        mutations=("stamp-secret mismatch flips ACCEPTED->stamp_verified=false (arm-witness negative controls)",),
        goodhart_surface="subject-controlled claim over subject-uncontrolled stamp facts (HMAC); "
                         "the invariant witness is kernel.stamp_valid (SECURITY DEFINER)",
    ),
    JudgmentSpec(
        judgment_id="review-fixpoint",
        family="E",
        title="Fresh first-contact attesting review of the final artifact; zero undisposed findings "
              "(calibration: confirmation-depth/panel-width/round-ceiling — ruling 108)",
        verdict_enum=("GREEN", "RED(joins-failed)"),
        subject_ref_type="row",
        law_citations=("RULING:107", "RULING:108", "ADR:0014"),
        engine="python",
        implementations=("instrument:review_fixpoint_close.py", "instrument:review_fixpoint.py",
                         "instrument:verify_review_fixpoint.py"),
        second_producer=None,
        second_producer_none_reason="three derivable joins over stamped rows; the stamps themselves "
                                    "carry the kernel second witness",
        complexity_class="C",
        fixtures=("verify_review_fixpoint.py both-polarity (GREEN fresh attest; RED delta-review/"
                  "undisposed/self-attest)",),
        promotion_stage="P2",
    ),
    JudgmentSpec(
        judgment_id="review-without-detail",
        family="E",
        title="Orphaned review stub: a kind='review' row with no review_detail (the e17 partial-stub seam)",
        verdict_enum=("COMPLETE", "ORPHANED(id)"),
        subject_ref_type="row",
        law_citations=("FIND:F53", "RULING:29"),
        engine="SQL",
        implementations=("instrument:review_without_detail.py", "instrument:verify_review_without_detail.py"),
        second_producer=None,
        second_producer_none_reason=_NO2ND_SINGLE,
        complexity_class="A",
        red_history="first live positive: e18 close-1, review_without_detail(6)",
        promotion_stage="P2",
    ),
    JudgmentSpec(
        judgment_id="core-a-dischargeability-probe",
        family="E",
        title="Core-A k-phase SoD/financial dischargeability probes (modal: about dischargeability, not fact)",
        verdict_enum=("DISCHARGEABLE(k,orgs)", "UNDISCHARGEABLE(core)"),
        subject_ref_type="meta",
        law_citations=("BRIEF:G5", "BRIEF:G7"),
        engine="ASP",
        implementations=("lp:instruments/core_a.lp", "tool:instruments/run-core-a.sh"),
        second_producer=None,
        second_producer_none_reason="generate-and-test probe kept apart from the strict closure "
                                    "(design-semantics §3.1); no fact lane to reconcile against",
        complexity_class="D",
        fixtures=("k-phase table = the s13 waiver rows' pinned evidence; broken-program fixture "
                  "(fixtures/core-a-broken.lp) proves the runner fails LOUDLY",),
        red_history="run-core-a.sh pre-INC-1 silenced stderr and grep-matched UNSATISFIABLE as "
                    "SATISFIABLE (refute-evaluation flaw 1(b)) — the ruling-110 nail, fixed here",
        promotion_stage="P1",
    ),
    # ---- Family F — claims-vs-acts differential -----------------------------------------------
    JudgmentSpec(
        judgment_id="acts-claims-differential",
        family="F",
        title="Ledger claims vs acts stream: unledgered spans, claims without acts, stale attestations",
        verdict_enum=("CORROBORATED", "SUBJECT-OMISSION", "INSTRUMENT-ARTIFACT", "UNRESOLVED-POINTER"),
        subject_ref_type="stream-pair",
        law_citations=("BRIEF:F11", "FIND:F49"),
        engine="SQL",
        implementations=(
            "lp:ledger_acts.lp#act_ledgered/1", "lp:ledger_acts.lp#unledgered_lr/1",
            "lp:ledger_acts.lp#claim_matched/1", "lp:ledger_acts.lp#stale_attestation/2",
            "lp:ledger_acts.lp#stale_attest/2", "lp:ledger_acts.lp#stale_nonattest/2",
            "lp:ledger_acts.lp#claimed_without_act/1", "lp:ledger_acts.lp#unledgered_span/2",
            "close:stale_attestation", "close:claimed_without_act", "close:unledgered_span",
        ),
        second_producer="acts_join.py SQL deriver vs the ledger_acts.lp ASP encoding (QUARANTINE on divergence)",
        complexity_class="B",
        adjudication_slot=True,
        adjudication_routing="attribution is defeasible (e17 unbound_row batch artifact) — human ruling appended",
        assumptions=("close-time only until acts_live ordering is ratified (D13)",),
        promotion_stage="P2",
    ),
    JudgmentSpec(
        judgment_id="row-performed-by",
        family="F",
        title="Claimed-vs-performed over the subject session's ledger-INSERT acts (proxy/self/unbound)",
        verdict_enum=("BOUND", "PROXY-WRITTEN", "SELF-PERFORMED", "UNBOUND"),
        subject_ref_type="row",
        law_citations=("FIND:F53", "BRIEF:G7"),
        engine="python",
        implementations=("close:proxy_written", "close:self_performed", "close:unbound_row",
                         "tool:claude_harness/experiments/fact-mining/row_performed_by.py"),
        second_producer="Python parse vs SQL join (in-deriver differential; DIVERGE quarantines)",
        complexity_class="B",
        adjudication_slot=True,
        adjudication_routing="unbound_row has a proven instrument-artifact class (e17 binder batch)",
        red_history="first live positive: e16 proxy_written(7) = row-7 claim inflation (finding 31)",
        promotion_stage="P2",
    ),
    JudgmentSpec(
        judgment_id="narration-cite-check",
        family="F",
        title="Narrated citations resolve against the record (F22)",
        verdict_enum=("RESOLVES", "UNRESOLVED-POINTER"),
        subject_ref_type="span",
        law_citations=("FIND:F22",),
        engine="python",
        implementations=("instrument:cite_check.py",),
        second_producer=None,
        second_producer_none_reason=_NO2ND_SINGLE,
        complexity_class="B",
        promotion_stage="P1",
    ),
    # ---- Family G — apparatus self-judgment ---------------------------------------------------
    JudgmentSpec(
        judgment_id="close-manifest-aggregation",
        family="G",
        title="THE one cross-family aggregation point (D5): every line's color, no silent non-run",
        verdict_enum=("OK", "RED", "QUARANTINED", "REQUIRED-ABSENT", "DECLARED-EXCLUSION(reason)"),
        subject_ref_type="meta",
        law_citations=("FIND:F49", "ADR:0002", "RULING:110"),
        engine="python",
        implementations=("instrument:close_manifest.py",),
        second_producer=None,
        second_producer_none_reason="it IS the aggregation authority; views of it are generated, "
                                    "never independent aggregators (D5)",
        complexity_class="A",
        promotion_stage="P2",
    ),
    JudgmentSpec(
        judgment_id="close-sweep",
        family="G",
        title="Close-window sweep: session log vs ledger tail (nothing after the close claim)",
        verdict_enum=("CLEAN", "POST-CLOSE-ACTIVITY"),
        subject_ref_type="span",
        law_citations=("ADR:0013", "FIND:F49"),
        engine="python",
        implementations=("instrument:close_sweep.py", "close:close_sweep"),
        second_producer=None,
        second_producer_none_reason=_NO2ND_SINGLE,
        complexity_class="B",
        promotion_stage="P2",
    ),
    JudgmentSpec(
        judgment_id="soundness-twin-differential",
        family="G",
        title="soundness.lp ASP vs soundness.py live-psql core (the operator immune-system differential)",
        verdict_enum=("AGREE", "DIVERGE_DEFECT", "QUARANTINED"),
        subject_ref_type="meta",
        law_citations=("ADR:0011", "FIND:F49"),
        engine="python",
        implementations=("instrument:soundness_twin.py", "close:soundness_twin",
                         "lp:instruments/soundness.lp#unsound_derivation/2"),
        second_producer=None,
        second_producer_none_reason="it IS a reconciliation line (S3 layer); its subjects are the two producers",
        complexity_class="A",
        promotion_stage="P1",
    ),
    JudgmentSpec(
        judgment_id="marriage-differential",
        family="G",
        title="ASP T_now vs independent SQL floor over banked targets (cross-repo, never hand-synced)",
        verdict_enum=("AGREE", "DIVERGE_DEFECT", "QUARANTINED"),
        subject_ref_type="meta",
        law_citations=("ADR:0011", "ADR:0009"),
        engine="python",
        implementations=("close:marriage_differential",
                         "tool:claude_harness/experiments/fact-mining/ledger_differential.py"),
        second_producer=None,
        second_producer_none_reason="it IS a reconciliation line (S3 layer)",
        complexity_class="A",
        promotion_stage="P1",
    ),
    JudgmentSpec(
        judgment_id="gate-journal-registered",
        family="G",
        title="A target is registered for contemporaneity (SESSIONS + GATE_JOURNALS) before arming (fc22)",
        verdict_enum=("REGISTERED", "REFUSED(missing)"),
        subject_ref_type="meta",
        law_citations=("FIND:F49",),
        engine="python",
        implementations=("instrument:verify_gate_journal_registered.py",),
        second_producer=None,
        second_producer_none_reason=_NO2ND_SINGLE,
        complexity_class="A",
        red_history="finding 42: the e17 gate-journal was never registered; contemporaneity read N/A silently",
        promotion_stage="P2",
    ),
    JudgmentSpec(
        judgment_id="meta-toolchain-negative-controls",
        family="G",
        title="The verify_* meta-checks: each proves a line's both-polarity behavior (qualification "
              "perimeter; the D2 systematic negative-control corpus lands INC 2)",
        verdict_enum=("PASS", "FAIL"),
        subject_ref_type="meta",
        law_citations=("ADR:0011", "FIND:F49"),
        engine="python",
        implementations=("instrument:verify_consumer_no_vacuous.py",
                         "instrument:verify_contemporaneity_degrade.py",
                         "instrument:verify_delivery_freight.py",
                         "instrument:verify_substrate_required.py"),
        second_producer=None,
        second_producer_none_reason="these ARE negative controls; their own controls are INC 2 (D2)",
        complexity_class="A",
        promotion_stage="P1",
    ),
    JudgmentSpec(
        judgment_id="review-queue-debt",
        family="G",
        title="Open/aging unadjudicated flags counted per family on the face of every close "
              "(visibility mandatory; the RED threshold is a future maintainer ruling)",
        verdict_enum=("OK(counts-shown)", "QUARANTINED"),
        subject_ref_type="meta",
        law_citations=("RULING:110", "FIND:F28"),
        engine="python",
        implementations=("close:review_queue_debt",),
        second_producer=None,
        second_producer_none_reason="a counting view over already-differential-checked producers",
        complexity_class="B",
        assumptions=("flag AGE is NOT-AVAILABLE until an adjudication store lands (OQ9) — declared, "
                     "not silently omitted",),
        promotion_stage="P1",
    ),
    JudgmentSpec(
        judgment_id="diagnostic-derivers",
        family="G",
        title="Diagnostic (non-gating) derivers: derive_trail, enacts_chain, coverage_audit",
        verdict_enum=("REPORT",),
        subject_ref_type="meta",
        law_citations=("ADR:0005",),
        engine="python",
        implementations=("instrument:derive_trail.py", "instrument:enacts_chain.py",
                         "instrument:coverage_audit.py"),
        second_producer=None,
        second_producer_none_reason="diagnostic report artifacts; no verdict to reconcile",
        complexity_class="B",
        promotion_stage="P0",
    ),
    JudgmentSpec(
        judgment_id="kb-logic-layer",
        family="D",
        title="Fact-mining KB logic layer (PoC substrate): typed truth, functional-conflict findings, "
              "supersession; logic_repair's retract/1 is blame-explanation output ONLY",
        verdict_enum=("TRUTH(v)", "CONFLICT(kind)", "SUPERSEDED"),
        subject_ref_type="row-set",
        law_citations=("ADR:0000", "ADR:0008"),
        engine="ASP",
        implementations=(
            "lp:logic_layer.lp#truth/4", "lp:logic_layer.lp#finding/3",
            "lp:logic_layer.lp#conflict_func/2", "lp:logic_layer.lp#supersedes/2",
            "lp:logic_repair.lp#retract/1",
        ),
        second_producer=None,
        second_producer_none_reason=_NO2ND_SINGLE,
        complexity_class="C",
        assumptions=("minimal-repair output is a REPORT artifact, never applied to the record "
                     "(the launder proof is the standing negative control)",),
        promotion_stage="P0",
    ),
    # ---- Family H — review-residue routing ----------------------------------------------------
    JudgmentSpec(
        judgment_id="review-queue-router",
        family="H",
        title="The materialized review queue: routes flags to human adjudication (NEVER a content verdict)",
        verdict_enum=("ROUTED(queue-ref)",),
        subject_ref_type="meta",
        law_citations=("FIND:F20", "FIND:F27", "FIND:F28"),
        engine="none-router",
        implementations=("instrument:review_queue.py",),
        second_producer=None,
        second_producer_none_reason="a router emits no verdict to reconcile (family H by law)",
        complexity_class="B",
        promotion_stage="P1",
    ),
    # ---- s22 work-item ledger (design/ORCH-S22-WORK-ITEM-LEDGER.md, session be693afb, 2026-07-09) ---
    JudgmentSpec(
        judgment_id="work-item-violations",
        family="D",
        title="Work-item ledger violations: duplicate-open / shipped-without-witness (both "
              "defense-in-depth, refused at construction by s22's DDL) / dangling depends_on / "
              "dependency cycles (the omega port)",
        verdict_enum=("CLEAN", "VIOLATION(kind)"),
        subject_ref_type="edge",
        law_citations=("ADR:0000",),
        engine="ASP",
        implementations=(
            "lp:work_items.lp#work_dep_edge/2", "lp:work_items.lp#work_dep_star/2",
            "lp:work_items.lp#work_duplicate_open/1",
            "lp:work_items.lp#work_shipped_without_witness/2",
            "lp:work_items.lp#work_depends_on_unknown/2",
            "lp:work_items.lp#work_dependency_cycle/1",
        ),
        second_producer="SQL floor (work_item_floor_atoms, engine/ledger_floor.py; reconciled by "
                        "kernel/fixtures/s22_work_item_fixture.py item 5)",
        complexity_class="C",
        fixtures=("kernel/fixtures/s22_work_item_fixture.py (toy db, schema s22probe): open/claim/"
                  "close round trip, shipped-without-witness refusal, duplicate-open refusal, "
                  "acyclic-vs-cyclic deps, dangling depends_on, SQL/ASP AGREE",),
        promotion_stage="P1",
    ),
)

# Implementation keys that are deliberately NOT judgments — each with its reason (I12: a declared
# absence is a row, never a silence). The parity checker treats these as covered.
DECLARED_EXCLUSIONS: dict[str, str] = {
    "instrument:ledger_target.py": "substrate registry (SSOT of target->db/schema/dirs); carries no verdict",
    "instrument:run-core-a.sh": "alias of tool:instruments/run-core-a.sh (registered on core-a-dischargeability-probe)",
}

# The F9-shaped regold records (D2): every ratified change to banked registry rows, mover never
# the approver. Contest 1 documents the census-ratification amendment (c) supersessions above.
CONTESTS: tuple[ContestRecord, ...] = (
    ContestRecord(
        contest_id="census-ratification-amendment-c",
        answers_red="consults/engine-census-ratification-RECOMMENDED.md §2.3 (two armed deny "
                    "surfaces below the D16 stage check, scope in tribal memory)",
        law_citation="RULING:120",
        mover="vicar:37017f46",
        approver="human:maintainer",
    ),
)


def superseded_ids() -> frozenset[str]:
    """judgment_ids superseded by a later row (D2 chain). A superseded row stays in SPECS as
    citable history but is NOT a live owner — parity, the family map, and the census behavior
    checks all read the chain head."""
    return frozenset(s.supersedes for s in SPECS if s.supersedes)


def _index() -> dict[str, str]:
    """implementation key -> LIVE judgment_id; refuses duplicates at import (one live owner per
    key). Superseded rows are skipped: their keys belong to the superseding row (D2)."""
    dead = superseded_ids()
    idx: dict[str, str] = {}
    for s in SPECS:
        if s.judgment_id in dead:
            continue
        for k in s.implementations:
            if k in idx:
                raise ValueError(f"implementation key {k!r} owned by both {idx[k]!r} and {s.judgment_id!r}")
            idx[k] = s.judgment_id
    return idx


IMPL_INDEX: dict[str, str] = _index()

# Flag-name -> family map for the review-queue-debt line (consumed cross-repo via --family-map).
# Derived from SPECS (one home): a flag's family is its owning judgment's family.
_FLAG_SOURCES: dict[str, str] = {
    "unsound_derivation": "consumption-soundness",
    "alias_surface": "consumption-soundness",
    "launder": "consumption-soundness",
    "condition2_individuation": "consumption-soundness",
    "stale_enactment_row": "stale-enactment-debt",
    "ticket_flags": "contemporaneity",
    "stale_attestation": "acts-claims-differential",
    "claimed_without_act": "acts-claims-differential",
    "unledgered_span": "acts-claims-differential",
    "proxy_written": "row-performed-by",
    "self_performed": "row-performed-by",
    "unbound_row": "row-performed-by",
    "review_without_detail": "review-without-detail",
    "open_finding": "findings-disposition-gate",
    "why_orphaned": "why-orphan-flag",
}


def family_map() -> dict[str, str]:
    by_id = {s.judgment_id: s.family for s in SPECS}
    return {flag: by_id[jid] for flag, jid in _FLAG_SOURCES.items()}


def main(argv: list[str]) -> int:
    if "--family-map" in argv:
        print(json.dumps(family_map(), sort_keys=True))
        return 0
    if "--impl-keys" in argv:
        print(json.dumps(IMPL_INDEX, sort_keys=True))
        return 0
    print(f"# judgment_registry — {len(SPECS)} specs, {len(IMPL_INDEX)} implementation keys, "
          f"{len(DECLARED_EXCLUSIONS)} declared exclusions")
    for s in SPECS:
        second = s.second_producer or f"none: {s.second_producer_none_reason}"
        print(f"  [{s.family}] {s.judgment_id}  stage={s.promotion_stage}"
              f"{' ruling42=' + s.ruling42_ratification if s.ruling42_ratification else ''}"
              f"  laws={','.join(s.law_citations)}  impls={len(s.implementations)}  2nd={second[:60]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
