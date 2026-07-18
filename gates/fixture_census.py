#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-09T13:36:11Z
#   last-change: 2026-07-18T09:22:45Z
#   contributors: be693afb/main, e4410ef6/main, 3c50e030/main, 3c942a60/main, a857c93d/main, ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""fixture_census — mechanizes mandate §6's "every migrated gate's seen-red still proves it
can fail" (manifest [C20]). A gate never seen red is a claim (ADR-0011); this gate makes the
SEEN-RED corpus a checked property so a gate cannot be added, or a seen-red silently orphaned,
without its both-polarity proof.

It holds a REGISTRY mapping every seen-red/<dir> to its runnable fixture (the live artifact that
both-polarity-proves the gate/close-line). It goes RED on:

  1. a seen-red/<dir> with NO banked red evidence (no red-shaped .txt) — a gate not seen red;
  2. an ORPHANED seen-red/<dir> not in the registry — evidence with no owning gate;
  3. a registry entry whose FIXTURE file does not exist — a claim whose proof cannot be run.

SCOPE (declared, ADR-0011 Rule 1): this gate checks red-evidence PRESENCE + fixture EXISTENCE
statically — cheap enough for every commit. Actually RE-EXECUTING each fixture to a live red is
the ACCEPTANCE-time re-verification (mandate §6 / BUILD-BRIEF Step 10e), not run on every commit
(many fixtures touch the DB; a 3s-per-fixture commit tax is its own hazard). The static census is
the standing net; the live red-re-execution is the acceptance gate.

Exit 0 clean; exit 1 listing every breach. Run from repo root: python3 gates/fixture_census.py
Lazy imports banned.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEN_RED = os.path.join(ROOT, "seen-red")

# The registry: seen-red dir -> the runnable fixture that both-polarity-proves it. The fixture is the
# LIVE artifact (a verify_*.py / *_fixture.py / a gate / the arm script / the banked reproduction) — the
# thing the acceptance re-executes to a live red. Every seen-red dir MUST appear here (orphan check).
REGISTRY: dict[str, str] = {
    "change-gate-subject-root":       "seen-red/change-gate-subject-root/run_fixtures.py",
    "stamp-intercept-secret":         "seen-red/stamp-intercept-secret/run_fixtures.py",
    "stamp-intercept-invocation-token": "seen-red/stamp-intercept-invocation-token/run_fixtures.py",
    "contemporaneity-audit":           "seen-red/contemporaneity-audit/run_fixtures.py",
    "04-consumer-no-vacuous-pass":    "instruments/verify_consumer_no_vacuous.py",
    "05-verify-adapter":              "instruments/act_stream/verify_adapter.py",
    "06-append-only-integrity":       "seen-red/06-append-only-integrity/red-specimen.py",
    "09-relevant-act-classification": "instruments/verify_relevant_act.py",
    "12-contemporaneity-degrade":     "instruments/verify_contemporaneity_degrade.py",
    "18-bash-write-classification":   "instruments/act_stream/verify_bash_write.py",
    "24-destructive-ddl-guard":       "seen-red/24-destructive-ddl-guard/red-specimen.py",
    "25-operator-turn-extraction":    "instruments/verify_operator_turns.py",
    "31-interception-stamp":          "kernel/fixtures/s17_stamp_fixture.py",
    "33-staging-guard":               "seen-red/33-staging-guard/red-specimen.py",
    "staging-scope-subset-enforcement": "seen-red/staging-scope-subset-enforcement/run_fixtures.py",
    "merge-diff-confinement":         "seen-red/merge-diff-confinement/run_fixtures.py",
    "artifact-claim-dereference-guard": "seen-red/artifact-claim-dereference-guard/run_fixtures.py",
    "rehearse-clone-jail-confinement": "seen-red/rehearse-clone-jail-confinement/run_fixtures.py",
    "35-delivery-freight-integrity":  "instruments/verify_delivery_freight.py",
    "36-consumer-substrate-required": "instruments/verify_substrate_required.py",
    "38-review-without-detail":       "instruments/verify_review_without_detail.py",
    "39-binder-bind-many":            "instruments/verify_binder.py",
    "42-gate-journal-registered":     "instruments/verify_gate_journal_registered.py",
    "43-arming-delivery-set":         "drive/arm.sh",
    "45-criterion-reviewer-grants":   "drive/arm.sh",
    "engine-inc1-controls":           "engine/tests",
    "review-fixpoint":                "instruments/verify_review_fixpoint.py",
    "s19-trigger-search-path":        "kernel/fixtures/s19_search_path_fixture.py",
    "conformance_check":              "seen-red/conformance_check/run_fixtures.py",
    "stop-clean-exit":                "seen-red/stop-clean-exit/run_fixtures.py",
    "demurral-detector":              "seen-red/demurral-detector/red-specimen.py",
    "mutation-observer":              "seen-red/mutation-observer/run_fixtures.py",
    "delegation-observer":            "seen-red/delegation-observer/run_fixtures.py",
    "apparatus-config":               "seen-red/apparatus-config/run_fixtures.py",
    "doc-shapes":                     "seen-red/doc-shapes/red-specimen.py",
    "doc-legibility-critic":          "seen-red/doc-legibility-critic/red-specimen.py",
    "doc-attestation-presence":       "seen-red/doc-attestation-presence/red-specimen.py",
    "doc-shapes-gate-world":          "seen-red/doc-shapes-gate-world/run_fixtures.py",
    "read-observer":                  "seen-red/read-observer/run_fixtures.py",
    "bash-completion":                "seen-red/bash-completion/run_fixtures.py",
    "hook-payload-contract":          "seen-red/hook-payload-contract/check_contract.py",
    "model-sql-block":                "seen-red/model-sql-block/run_fixtures.py",
    "s25-commission-kind":            "seen-red/s25-commission-kind/run_fixtures.py",
    "track-work":                     "seen-red/track-work/run_fixtures.py",
    "resource-registry":              "seen-red/resource-registry/run_fixtures.py",
    "track-experiments":              "seen-red/track-experiments/run_fixtures.py",
    "attest-tags":                    "seen-red/attest-tags/run_fixtures.py",
    "verify-commission":              "seen-red/verify-commission/run_fixtures.py",
    "s26-row-hash-chain":             "seen-red/s26-row-hash-chain/run_fixtures.py",
    "s26-row-hash-chain-deletion":    "seen-red/s26-row-hash-chain-deletion/run_fixtures.py",
    "s26-accommodate":                "seen-red/s26-accommodate/run_fixtures.py",
    "s27-chain-high-water":           "seen-red/s27-chain-high-water/run_fixtures.py",
    "no-conflict-markers":            "seen-red/no-conflict-markers/run_fixtures.py",
    "rename-doc":                     "seen-red/rename-doc/red-specimen.py",
    "scaffold-governed-and-gitignore": "seen-red/scaffold-governed-and-gitignore/run_fixtures.py",
    # the two census gates minted in this build carry their own seen-red (a census gate never seen
    # red is the joke that writes itself); their fixture is the gate itself, red-specimen mutates its
    # registry in memory to force the breach.
    "layout-census":                  "gates/layout_census.py",
    "fixture-census":                 "gates/fixture_census.py",
    "link-integrity":                 "seen-red/link-integrity/run_fixtures.py",
    "apparatus-unknown-keys":         "seen-red/apparatus-unknown-keys/run_fixtures.py",
    "worktree-ledgering":             "seen-red/worktree-ledgering/run_fixtures.py",
    "led-refs-flag-order-parser-bug": "seen-red/led-refs-flag-order-parser-bug/run_fixtures.py",
    "led-work-depends-default-type-advisory": "seen-red/led-work-depends-default-type-advisory/run_fixtures.py",
    "preamble-ordering":              "seen-red/preamble-ordering/run_fixtures.py",
    "resource-intake-validation":     "seen-red/resource-intake-validation/run_fixtures.py",
    "content-free-review-audit":      "seen-red/content-free-review-audit/run_fixtures.py",
    "decomposition-review-blocker":   "seen-red/decomposition-review-blocker/run_fixtures.py",
    "registry-ordering":              "seen-red/registry-ordering/run_fixtures.py",
    "estimate-intake-validation":     "seen-red/estimate-intake-validation/run_fixtures.py",
    "apparatus-flip":                 "seen-red/apparatus-flip/run_fixtures.py",
    "taxonomy-intake-validation":     "seen-red/taxonomy-intake-validation/run_fixtures.py",
    "accounting-forbidden-tier":      "seen-red/accounting-forbidden-tier/run_fixtures.py",
    "s28-work-parent-edge":           "seen-red/s28-work-parent-edge/run_fixtures.py",
    "s29-obligation-item-key-and-typed-close": "seen-red/s29-obligation-item-key-and-typed-close/run_fixtures.py",
    "s29-migration-epoch":            "seen-red/s29-migration-epoch/run_fixtures.py",
    "s30-typed-dependency-edges":      "seen-red/s30-typed-dependency-edges/run_fixtures.py",
    "s31-supersession-uniform-retraction": "seen-red/s31-supersession-uniform-retraction/run_fixtures.py",
    "lp-module-registry":             "seen-red/lp-module-registry/run_fixtures.py",
    "s32-edge-views-single-home":     "seen-red/s32-edge-views-single-home/run_fixtures.py",
    "s33-composite-discharge":        "seen-red/s33-composite-discharge/run_fixtures.py",
    "s34-computed-grade-refusal":     "seen-red/s34-computed-grade-refusal/run_fixtures.py",
    "s35-validation-decomposition":   "seen-red/s35-validation-decomposition/run_fixtures.py",
    "s40-principal-identity-events":  "seen-red/s40-principal-identity-events/run_fixtures.py",
    "s41-principal-bindings-and-relations": "seen-red/s41-principal-bindings-and-relations/run_fixtures.py",
    "s42-row-hash-full-coverage":     "seen-red/s42-row-hash-full-coverage/run_fixtures.py",
    "s43-typed-verdict-write-boundary": "seen-red/s43-typed-verdict-write-boundary/run_fixtures.py",
    "s45-standing-lifecycle":          "seen-red/s45-standing-lifecycle/run_fixtures.py",
    "s44-model-identity-attestation":  "seen-red/s44-model-identity-attestation/run_fixtures.py",
    "s46-credited-views":              "seen-red/s46-credited-views/run_fixtures.py",
    "defeat-pipeline":                 "seen-red/defeat-pipeline/run_fixtures.py",
    "judge-all-capable-layers":       "seen-red/judge-all-capable-layers/run_fixtures.py",
    "boundary-service":                "seen-red/boundary-service/run_fixtures.py",
    "otel-attest":                     "seen-red/otel-attest/run_fixtures.py",
    "column-complete-gate":           "seen-red/column-complete-gate/run_fixtures.py",
    "freeze-at-stamp":                "seen-red/freeze-at-stamp/run_fixtures.py",
    "verify-chain-error-conflation":  "seen-red/verify-chain-error-conflation/run_fixtures.py",
    "actual-intake-validation":       "seen-red/actual-intake-validation/run_fixtures.py",
    "outcome-intake-validation":      "seen-red/outcome-intake-validation/run_fixtures.py",
    "review-queue-intake":            "seen-red/review-queue-intake/run_fixtures.py",
    "adr-portability-terms":          "seen-red/adr-portability-terms/run_fixtures.py",
    "adr-bare-p-label":               "seen-red/adr-bare-p-label/run_fixtures.py",
    "doc-tables":                     "seen-red/doc-tables/red-specimen.py",
    "stamp-provenance-marker-corruption": "seen-red/stamp-provenance-marker-corruption/run_fixtures.py",
    "pickup-connection-failure-silent-empty": "seen-red/pickup-connection-failure-silent-empty/run_fixtures.py",
    "scan2-firing-telemetry":       "seen-red/scan2-firing-telemetry/run_fixtures.py",
    "deployment-pinning":           "seen-red/deployment-pinning/run_fixtures.py",
    "orchlog-since-filter":         "seen-red/orchlog-since-filter/run_fixtures.py",
    "kind-shape-manifest-gate":     "seen-red/kind-shape-manifest-gate/run_fixtures.py",
    "idris-model-freshness":        "seen-red/idris-model-freshness/run_fixtures.py",
    # panel-disposition / panel-cosign DEREGISTERED (2026-07-15, TASK C, commission item 3):
    # both suites ported to the standalone SPA repo's own tests/ (test_disposition.py,
    # test_cosign_live.py in KodBena/autoharn-panel) when the PoC moved out of panel/ into its
    # own repo, adopted back as a git submodule at tools/autoharn-panel — both-polarity
    # discipline continues to hold there, just no longer under this repo's seen-red/ registry.
}


def _has_red_evidence(d: str) -> bool:
    """A seen-red dir proves failure iff it banks a red-shaped artifact (red.txt, *-red.txt,
    red-specimen.py) — the captured or reproducible red the gate produced."""
    for name in os.listdir(d):
        low = name.lower()
        if low == "red.txt" or low.endswith("-red.txt") or low.startswith("red-specimen"):
            return True
    return False


def main() -> int:
    breaches: list[str] = []
    present = sorted(e for e in os.listdir(SEEN_RED)
                     if os.path.isdir(os.path.join(SEEN_RED, e)))

    # (2) orphan check — every seen-red dir must be registered
    for d in present:
        if d not in REGISTRY:
            breaches.append(f"ORPHANED seen-red dir: seen-red/{d}/ has no registry entry "
                            f"(a gate's proof with no owning gate — register it or remove it)")
    # registry entries for dirs that vanished
    for d in REGISTRY:
        if d not in present:
            breaches.append(f"MISSING seen-red dir: registry names seen-red/{d}/ but it does not exist")

    for d in present:
        path = os.path.join(SEEN_RED, d)
        # (1) red evidence present
        if not _has_red_evidence(path):
            breaches.append(f"NO RED EVIDENCE: seen-red/{d}/ banks no red-shaped artifact "
                            f"(a gate never seen red is a claim, ADR-0011)")
        # (3) fixture exists
        fx = REGISTRY.get(d)
        if fx and not os.path.exists(os.path.join(ROOT, fx)):
            breaches.append(f"FIXTURE MISSING: seen-red/{d}/ -> {fx} does not exist "
                            f"(a proof whose fixture cannot run)")

    if breaches:
        print(f"fixture-census: {len(breaches)} breach(es) — the seen-red corpus is not intact:\n")
        for b in breaches:
            print(f"  !! {b}")
        return 1
    print(f"fixture-census: clean ✓  ({len(present)} seen-red gates, each with banked red evidence and a "
          f"registered runnable fixture). Live red-re-execution is the acceptance gate (§6).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
