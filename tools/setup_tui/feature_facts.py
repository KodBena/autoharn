#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T23:35:54Z
#   last-change: 2026-07-19T01:43:11Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""tools/setup_tui/feature_facts.py -- the feature-facts registry
(design/FABLE-SETUP-TUI-FEATURE-FACTS-SPEC.md §2, commission ledger row 1714). ONE home
(ADR-0012 P1) for the standards-conformance aspiration and external-cost/dependency facts the
setup wizard shows AT THE POINT OF SELECTION, before the operator commits an act. Screens
render FROM this module (`fact(key).line()`); no screen carries a facts string of its own.

Each entry's `aspiration` names the standards-conformance aim it serves, with a citation, or
says so honestly ("none named; house discipline only") rather than inventing one. Each entry's
`external` enumerates concrete external costs/dependencies (binaries, Python packages beyond
stdlib, network ports, cluster-host operator acts, recurring operator processes) or states
`none` explicitly -- absence of the fact and absence of the entry are kept distinguishable by
this dataclass always having both fields populated, never omitted.

Drift backstop (this module's own instance of the FAQ's five-move method,
user-guide/USER-RECIPES-FAQ.md "Drift backstops" -- this spec is that section's first
deliberate consumer, per design/FABLE-SETUP-TUI-FEATURE-FACTS-SPEC.md §1):

  1. Name the pair: REGISTRY (the dependent) vs. the live authorities anchored in screens.py's
     module-level constants -- `PREFLIGHT_BINARIES` (screen 1's probed-binary tuple) and
     `SUBSTRATE_CHOICES` (screen 2's `ask_choice` option keys) -- plus
     `durable_decisions.CATALOG`'s slugs (the hydration submenu's own registry).
  2. Both sides derived mechanically at check time (`derive_live_keys`), never a hand-typed
     second list -- the same filenames/live-catalog-derivation discipline the FAQ names.
  3. `check_registry` is the comparator, and it quantifies over the whole class: any FUTURE
     preflight binary, substrate choice, or catalog slug is in scope by construction (adding one
     without a matching registry key, or vice versa, is caught the next time this runs).
  4. The comparator refuses loud -- it returns every orphaned/missing key as a message, never
     silently drops one.
  5. Backstopped by seen-red/setup-tui-feature-facts-drift/run_fixtures.py, census-registered in
     gates/fixture_census.py (WF2's red leg: a synthetic registry with an extra or a missing key
     reads red there).

Import-cycle note: screens.py imports THIS module (to render facts); this module must therefore
never import screens.py back. `derive_live_keys` below gets its screens.py-anchored half of the
comparison from the caller (the drift fixture imports screens.py directly, a one-way leaf
import) rather than from this module reaching back into screens.py.

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import here is top of file.
"""
from __future__ import annotations

from dataclasses import dataclass

from tools.setup_tui import durable_decisions


@dataclass(frozen=True)
class FeatureFact:
    key: str
    label: str
    aspiration: str
    external: str

    def line(self) -> str:
        return f"  facts [{self.label}] -- aspiration: {self.aspiration} | external: {self.external}"


# ---------------------------------------------------------------------------------------------
# Registry -- every selectable act the flow offers (§2's enumeration): the substrate paths, the
# boundary service, observability (otelcol + watchdog), each hydration item, and the
# preflight-probed toolchains (idris2, clingo/ASP, python3, psql, textual/urwid if present).
# ---------------------------------------------------------------------------------------------

REGISTRY: dict[str, FeatureFact] = {
    "preflight_idris2": FeatureFact(
        key="preflight_idris2", label="idris2 toolchain",
        aspiration="none named; house discipline only -- backs the categorical-kernel-model "
                    "freshness cross-check (gates/idris_model_freshness.py), not a named "
                    "external standards-conformance aim.",
        external="external binary: idris2 (github.com/idris-lang/Idris2#installation); not on "
                 "PATH reads RED with an install pointer (tools/setup_tui/screens.py "
                 "screen_preflight).",
    ),
    "preflight_clingo": FeatureFact(
        key="preflight_clingo", label="clingo (ASP solver)",
        aspiration="none named; house discipline only -- the deductive engine (clingo/ASP over "
                    "engine/lp/*, driving ./judge's differential) is this project's own "
                    "raison d'etre, not a named external standard.",
        external="external binary: clingo -- the engine differential proofs and ./judge need "
                 "it; NON-FATAL if absent, matching bootstrap/bootstrap.sh's own posture "
                 "('not fatal to bootstrap').",
    ),
    "preflight_psql": FeatureFact(
        key="preflight_psql", label="psql client",
        aspiration="none named; house discipline only.",
        external="external binary: the postgresql-client package's psql; not on PATH reads RED "
                 "(tools/setup_tui/screens.py screen_preflight).",
    ),
    "preflight_python3": FeatureFact(
        key="preflight_python3", label="python3 interpreter",
        aspiration="none named; house discipline only.",
        external="none beyond the baseline interpreter this tool and every driven verb already "
                 "run under -- checked for presence/PATH correctness, not an ADDED dependency "
                 "beyond running the tool at all.",
    ),
    "ui_backend_textual": FeatureFact(
        key="ui_backend_textual", label="textual (optional TUI backend)",
        aspiration="none named.",
        external="optional external Python package beyond stdlib -- this build found it NOT "
                 "installed at build time (tools/setup_tui/__init__.py), so the zero-dependency "
                 "numbered-menu fallback is used (design/FABLE-SETUP-TUI-SPEC.md 'v1 "
                 "boundaries'). Adopting it later is in-boundary, not automatic.",
    ),
    "ui_backend_urwid": FeatureFact(
        key="ui_backend_urwid", label="urwid (optional TUI backend)",
        aspiration="none named.",
        external="optional external Python package beyond stdlib -- this build found it NOT "
                 "installed at build time (tools/setup_tui/__init__.py); same posture as "
                 "textual above.",
    ),
    "substrate_existing": FeatureFact(
        key="substrate_existing", label="existing-db substrate path",
        aspiration="none named.",
        external="none -- zero manual steps, reuses an already-reachable database "
                 "(design/FABLE-SETUP-TUI-SPEC.md screen 2, 'the omega-lab shape').",
    ),
    "substrate_dedicated": FeatureFact(
        key="substrate_dedicated", label="dedicated-db substrate path",
        aspiration="none named; house config-fragment discipline only (memory: "
                    "config-fragments-need-the-real-file -- pg_hba lines are never authored "
                    "without reading the live target file first).",
        external="cluster-host operator acts: pg_hba install + reload + createdb "
                 "(tools/setup_tui/pghba.py, tools/setup_tui/screens.py screen_substrate's "
                 "PREPARED blocks); requires a live, network-reachable Postgres cluster the "
                 "operator administers.",
    ),
    "signed_genesis": FeatureFact(
        key="signed_genesis", label="Signed genesis ceremony",
        aspiration="the SIGNED commission mode, design/MAINT-GPG-TRUST-LAYER.md §3 -- the "
                    "NIST-lineage authenticity aspiration that spec names for a GPG signature "
                    "(non-repudiation, forgery resistance against the apparatus itself, "
                    "outside-verifiability, §1); design/FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md "
                    "is this screen's own build basis (commission ledger rows 1724/1725).",
        external="external binary: gpg (GnuPG), must be on PATH; a real, ONGOING key-custody "
                 "burden for the operator (the private key and its revocation certificate, "
                 "user-guide/USER-GPG-TRUST-LAYER-FAQ.md §1-§2) -- stated plainly, this is the "
                 "one screen in this flow with a genuine standing operator responsibility "
                 "attached, though the SIGNING act itself is one-time (spec §1 item 5: no "
                 "ongoing signing burden, no signature gates added anywhere).",
    ),
    "boundary_service": FeatureFact(
        key="boundary_service", label="boundary service",
        aspiration="none named directly; law/adr/0016-the-service-contract-is-an-enforcement-"
                    "surface.md governs its shape as house discipline, not an external "
                    "standard -- its request stream is the same OTel channel the sentry's NIST "
                    "AU-family aspiration below reads (design/FABLE-OTEL-SENTRY-SPEC.md §0).",
        external="Python packages beyond stdlib: fastapi + uvicorn (serving/boundary_service.py "
                 "own top-of-file imports); a network port (tools/setup_tui/probes.py "
                 "free_port); optionally a recurring operator process to keep alive "
                 "(tools/setup_tui/screens.py screen_boundary's systemd-unit PREPARED block, "
                 "taken when this process does not start the service itself).",
    ),
    "observability_otelcol": FeatureFact(
        key="observability_otelcol", label="OTel collector (otelcol)",
        aspiration="NIST AU-family audit-supporting evidence at diagnostics tier "
                    "(design/FABLE-OTEL-SENTRY-SPEC.md §0: 'Watchdog alerts and attestations "
                    "alike are AU-family audit-supporting evidence, never IA-2 "
                    "authentication').",
        external="external binary: otelcol-contrib; a recurring operator process to keep alive "
                 "(tools/setup_tui/screens.py screen_observability's PREPARED start line).",
    ),
    "observability_watchdog": FeatureFact(
        key="observability_watchdog", label="OTel model-provenance watchdog (otel-watch)",
        aspiration="NIST AU-family audit-supporting evidence at diagnostics tier, same "
                    "citation as otelcol above (design/FABLE-OTEL-SENTRY-SPEC.md §0, §3's v0 "
                    "watchdog: 'no principal, no ledger write, no kernel anything').",
        external="depends on the otelcol collector's JSONL export already running "
                 "(design/FABLE-OTEL-SENTRY-SPEC.md §3); a recurring operator daemon process "
                 "(the repo-root `./otel-watch --daemon` verb).",
    ),
    "hydration_fork_provenance": FeatureFact(
        key="hydration_fork_provenance", label="fork provenance",
        aspiration="none named; a per-world fact, not a standards-conformance aim.",
        external="none.",
    ),
    "hydration_role_charters": FeatureFact(
        key="hydration_role_charters", label="role charters",
        aspiration="adjacent to the principal-surface's NIST SP 800-63 aspiration "
                    "(design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md header) but NOT that "
                    "delta itself -- tools/role_charter.py predates s40/s41 and registers a "
                    "charter, not an event-sourced identity.",
        external="none beyond this repo's own tools/role_charter.py (no new binary/package).",
    ),
    "hydration_makespan_scheduling_by_mandate": FeatureFact(
        key="hydration_makespan_scheduling_by_mandate",
        label="makespan-scheduling-by-mandate (durable decision)",
        aspiration="none named as an external standard; operating-rhythm house mandate "
                    "(user-guide/USER-RECIPES-FAQ.md 'Workflow patterns', maintainer directive "
                    "2026-07-14).",
        external="external Python package: ortools>=9.0 "
                 "(tools/makespan-scheduler/pyproject.toml), vendored as a git submodule.",
    ),
    "hydration_drift_backstops": FeatureFact(
        key="hydration_drift_backstops", label="drift-backstops (durable decision)",
        aspiration="the project-wide NRC-grade-product posture (house discipline; memory: "
                    "quality-bar-nrc-grade-best-effort), not a named external standard.",
        external="none.",
    ),
    "hydration_adr_adoption": FeatureFact(
        key="hydration_adr_adoption", label="ADR adoption (submenu)",
        aspiration="the ADRs under law/adr/ ARE this project's own standards-conformance law; "
                    "adopting one is adopting a named house standard, not an external one.",
        external="none.",
    ),
    "hydration_single_branch_authoring": FeatureFact(
        key="hydration_single_branch_authoring", label="single-branch-authoring (durable "
        "decision)",
        aspiration="house version-control discipline (ledger row 1033), not a named external "
                    "standard.",
        external="none.",
    ),
    "hydration_tags_are_serious_business": FeatureFact(
        key="hydration_tags_are_serious_business", label="tags-are-serious-business (durable "
        "decision)",
        aspiration="house release-discipline (ledger row 1027), not a named external standard.",
        external="none.",
    ),
    "hydration_obligate_amplification_caution": FeatureFact(
        key="hydration_obligate_amplification_caution", label="obligate-amplification-caution "
        "(durable decision)",
        aspiration="house kernel-write discipline (ledger row 1640), not a named external "
                    "standard.",
        external="none.",
    ),
    "hydration_doc_currency_at_the_seam": FeatureFact(
        key="hydration_doc_currency_at_the_seam", label="doc-currency-at-the-seam (durable "
        "decision)",
        aspiration="the project-wide NRC-grade-product posture (ledger row 1699), not a named "
                    "external standard.",
        external="none.",
    ),
    "hydration_concurrent_builders_need_isolation": FeatureFact(
        key="hydration_concurrent_builders_need_isolation",
        label="concurrent-builders-need-isolation (durable decision)",
        aspiration="house concurrency discipline (ledger row 1502), not a named external "
                    "standard.",
        external="none.",
    ),
    "hydration_runs_are_strictly_linear": FeatureFact(
        key="hydration_runs_are_strictly_linear", label="runs-are-strictly-linear (durable "
        "decision)",
        aspiration="house world-lifecycle discipline (maintainer ruling 2026-07-11), not a "
                    "named external standard.",
        external="none.",
    ),
    "hydration_decomposition_to_unit_of_independent_resumption": FeatureFact(
        key="hydration_decomposition_to_unit_of_independent_resumption",
        label="decomposition-to-unit-of-independent-resumption (durable decision)",
        aspiration="house decomposition discipline, mined from the autoharn-panel live "
                    "deployment's own prior art, not a named external standard.",
        external="none.",
    ),
    "hydration_claims_carry_witnesses": FeatureFact(
        key="hydration_claims_carry_witnesses", label="claims-carry-witnesses (durable "
        "decision)",
        aspiration="an evidentiary-discipline house standard (this repo's own CLAUDE.md "
                    "ORCHESTRATION section), not a named external standard.",
        external="none.",
    ),
    "hydration_unanchored_review_briefs": FeatureFact(
        key="hydration_unanchored_review_briefs", label="unanchored-review-briefs (durable "
        "decision)",
        aspiration="house anti-anchoring-bias review discipline (ledger row 1278), not a named "
                    "external standard.",
        external="none.",
    ),
    "hydration_fresh_context_review_for_delegated_work": FeatureFact(
        key="hydration_fresh_context_review_for_delegated_work",
        label="fresh-context-review-for-delegated-work (durable decision)",
        aspiration="house independent-review discipline (ledger row 1492), not a named "
                    "external standard.",
        external="none.",
    ),
}


def fact(key: str) -> FeatureFact:
    """Looks up one registry entry. Raises KeyError (loud, never a silent default) if `key` is
    not registered -- a screen asking for a fact that does not exist is exactly the drift this
    module's backstop exists to catch before it ships."""
    return REGISTRY[key]


def facts_block(keys: list[str]) -> str:
    """Renders every named key's fact line, one per line -- the shape screens.py calls at a
    point of selection (§2: 'a facts line under each item')."""
    return "\n".join(fact(k).line() for k in keys)


# ---------------------------------------------------------------------------------------------
# Drift backstop: derive the live key set mechanically, compare against REGISTRY.
# ---------------------------------------------------------------------------------------------

def derive_live_keys() -> set[str]:
    """The live authority side, derived mechanically (never hand-typed): the fixed UI-backend/
    boundary/observability singleton keys (aspirational, non-enumerable facts -- the
    banked-manifest variant, existence-checked rather than re-derived, per this module's own
    docstring move 1), the preflight binary names, the substrate choice keys, and
    durable_decisions.CATALOG's own slugs plus its fixed non-catalog hydration items. This is
    the SAME live set screens.py's PREFLIGHT_BINARIES/SUBSTRATE_CHOICES constants are built
    from -- kept as one literal list here (not re-imported from screens.py, to avoid the import
    cycle noted in the module docstring); the drift fixture cross-checks this function's output
    against screens.py's own constants directly, which is the independent-derivation half of
    the backstop."""
    live: set[str] = {
        "ui_backend_textual", "ui_backend_urwid",
        "signed_genesis",
        "boundary_service", "observability_otelcol", "observability_watchdog",
        "hydration_fork_provenance", "hydration_role_charters",
        "hydration_adr_adoption",
    }
    for name in ("idris2", "clingo", "python3", "psql"):
        live.add(f"preflight_{name}")
    for choice_key in ("existing", "dedicated"):
        live.add(f"substrate_{choice_key}")
    for decision in durable_decisions.CATALOG:
        live.add(f"hydration_{decision.slug.replace('-', '_')}")
    return live


def check_registry(registry: dict[str, FeatureFact] | None = None,
                    live_keys: set[str] | None = None) -> list[str]:
    """The comparator (move 3): every registry key with no live counterpart, and every live key
    with no registry entry, is a drift message. Both `registry` and `live_keys` are injectable
    so a fixture can feed a SYNTHETIC registry/live-set and observe the red leg without mutating
    this module's own globals (WF2's own bar)."""
    reg = registry if registry is not None else REGISTRY
    live = live_keys if live_keys is not None else derive_live_keys()
    messages: list[str] = []
    for key in sorted(reg):
        if key not in live:
            messages.append(f"ORPHANED registry key: '{key}' has no live counterpart")
    for key in sorted(live):
        if key not in reg:
            messages.append(f"UNREGISTERED live feature: '{key}' has no feature_facts entry")
    return messages


if __name__ == "__main__":
    import sys

    problems = check_registry()
    if problems:
        print("feature_facts drift:")
        for p in problems:
            print(f"  {p}")
        sys.exit(1)
    print("feature_facts: registry and live derivation agree, no drift.")
    sys.exit(0)
