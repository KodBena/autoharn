#!/usr/bin/env python3
"""tools/setup_tui/feature_facts_data.py -- the DATA half of the feature-facts registry, split
out of tools/setup_tui/feature_facts.py under law/adr/0012's 2026-07-22 Amendment (P10 -- "data
is not code"), phase 1 of design/FABLE-SETUP-TUI-FIELD-STRATEGY.md Track 2.2. This module is the
declared data artifact P10 calls for: typed literals, ZERO functions, ZERO logic -- a writing/
content edit to a fact's `aspiration`/`external` prose lands here and ONLY here, never mixed with
a review of `feature_facts.py`'s comparator logic.

Content, not structure: `RAW_ENTRIES` carries every field feature_facts.FeatureFact needs
(key/label/aspiration/external), keyed by the same `key` the dataclass instance itself carries
(duplicated on purpose -- the original REGISTRY dict already carried both a dict key and a
`FeatureFact.key` field, kept unchanged here). `feature_facts.py` constructs the typed
`REGISTRY: dict[str, FeatureFact]` from this dict at import time (one line, pure wiring -- never
a parse, never a runtime file read); the FeatureFact dataclass DEFINITION stays in feature_facts.py
per this build's own commission (dataclass definitions are logic-side contracts, not data).

Chosen form (P10's own "choose deliberately" instruction): a data-only Python module, not JSON/
TOML. Every field here is a plain string with no cross-references a non-engineer edits blind --
each entry cites ledger rows, spec paths, and code paths BY NAME, and those citations are exactly
the kind of content a structured-file editor (JSON/TOML) would make easier to mistype (no
schema/type check on a JSON edit) and harder to keep consistent with feature_facts.py's own
FeatureFact field names (a JSON key typo is a silent no-op at parse time; a dict-literal key typo
here is a TypeError at import time -- P8's fail-loud-signature bar, kept). Zero-copy: this module
has zero imports and zero functions, so there is nothing here for a parser to fail on and nothing
here mypy --strict cannot check as plain `dict[str, dict[str, str]]` literals.

This module has NO dependency on feature_facts.py (avoiding any import-order fragility): it is
pure literal data, importable standalone. feature_facts.py is this module's only intended
importer; nothing else should import RAW_ENTRIES directly (the REGISTRY it builds is the stable
consumer-facing name -- see feature_facts.py's own module docstring for the drift-backstop
machinery this content backs).

Content is UNCHANGED from feature_facts.py's prior REGISTRY literal -- this is a pure relocation
(program-text moved, not rewritten); see the commit message for how this was verified (an AST-
level extraction of each field's original source segment, not hand-retyped).

Lazy imports are banned (CLAUDE.md, 2026-07-02) -- moot here (zero imports), stated for the
convention's sake.
"""
from __future__ import annotations

RAW_ENTRIES: dict[str, dict[str, str]] = {
    "preflight_idris2": {
        "key": "preflight_idris2",
        "label": "idris2 toolchain",
        "aspiration": "none named; house discipline only -- backs the categorical-kernel-model "
                    "freshness cross-check (gates/idris_model_freshness.py), not a named "
                    "external standards-conformance aim.",
        "external": "external binary: idris2 (github.com/idris-lang/Idris2#installation); not on "
                 "PATH reads RED with an install pointer (tools/setup_tui/screens.py "
                 "screen_preflight).",
    },
    "preflight_clingo": {
        "key": "preflight_clingo",
        "label": "clingo (ASP solver)",
        "aspiration": "none named; house discipline only -- the deductive engine (clingo/ASP over "
                    "engine/lp/*, driving ./judge's differential) is this project's own "
                    "raison d'etre, not a named external standard.",
        "external": "external binary: clingo -- the engine differential proofs and ./judge need "
                 "it; NON-FATAL if absent, matching bootstrap/bootstrap.sh's own posture "
                 "('not fatal to bootstrap').",
    },
    "preflight_psql": {
        "key": "preflight_psql",
        "label": "psql client",
        "aspiration": "none named; house discipline only.",
        "external": "external binary: the postgresql-client package's psql; not on PATH reads RED "
                 "(tools/setup_tui/screens.py screen_preflight).",
    },
    "preflight_python3": {
        "key": "preflight_python3",
        "label": "python3 interpreter",
        "aspiration": "none named; house discipline only.",
        "external": "none beyond the baseline interpreter this tool and every driven verb already "
                 "run under -- checked for presence/PATH correctness, not an ADDED dependency "
                 "beyond running the tool at all.",
    },
    "ui_backend_textual": {
        "key": "ui_backend_textual",
        "label": "textual (optional TUI backend)",
        "aspiration": "none named.",
        "external": "optional external Python package beyond stdlib -- IN USE as of "
                 "design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md (commission ledger row 1818): a real "
                 "Textual application (tools/setup_tui/ui_textual.py's TextualUi/"
                 "SetupWizardApp) is the interactive face when this library is importable; "
                 "version 8.2.8 witnessed against this build (a scratch venv, since the build "
                 "interpreter itself did not have it installed -- see the FAQ getting-started "
                 "entry). Absent, the numbered-menu fallback is used automatically (one "
                 "teaching line naming the exact venv/pip command) -- --plain forces that "
                 "fallback explicitly, --scripted never touches textual at all.",
    },
    "ui_backend_urwid": {
        "key": "ui_backend_urwid",
        "label": "urwid (optional TUI backend)",
        "aspiration": "none named.",
        "external": "optional external Python package beyond stdlib -- this build found it NOT "
                 "installed at build time (tools/setup_tui/__init__.py); same posture as "
                 "textual above.",
    },
    "substrate_existing": {
        "key": "substrate_existing",
        "label": "existing-db substrate path",
        "aspiration": "none named.",
        "external": "none -- zero manual steps, reuses an already-reachable database "
                 "(design/FABLE-SETUP-TUI-SPEC.md screen 2, 'the omega-lab shape').",
    },
    "substrate_dedicated": {
        "key": "substrate_dedicated",
        "label": "dedicated-db substrate path",
        "aspiration": "none named; house config-fragment discipline only (memory: "
                    "config-fragments-need-the-real-file -- pg_hba lines are never authored "
                    "without reading the live target file first).",
        "external": "cluster-host operator acts: pg_hba install + reload + createdb "
                 "(tools/setup_tui/pghba.py, tools/setup_tui/screens.py screen_substrate's "
                 "PREPARED blocks); requires a live, network-reachable Postgres cluster the "
                 "operator administers.",
    },
    "fork_target_governed_files": {
        "key": "fork_target_governed_files",
        "label": "governed-files pattern exposure",
        "aspiration": "F33 (governance keyed to WHAT THE THING IS, not an enumerated file list) -- "
                    "house discipline, not an external standard "
                    "(hooks/pretooluse_change_gate.py's own _load_governed_patterns).",
        "external": "none -- writes one JSON file inside the target directory "
                 "(<dest>/.claude/governed_files.json), no new binary or package. Commission "
                 "row 1730: the autoharn-panel deployment started .py-only and needed "
                 ".ts/.vue/.html added by hand after the fact.",
    },
    "principals_authority": {
        "key": "principals_authority",
        "label": "Principals & authority screen",
        "aspiration": "NIST SP 800-63's identity/lifecycle/binding decomposition, via the s40/s41 "
                    "family (kernel/lineage/s40-principal-identity-events.sql, kernel/lineage/"
                    "s41-principal-bindings-and-relations.sql), cited to "
                    "design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md.",
        "external": "none -- drives this world's own <dest>/legacy/led and tools/role_charter.py, "
                 "no new binary or package.",
    },
    "signed_genesis": {
        "key": "signed_genesis",
        "label": "Signed genesis ceremony",
        "aspiration": "the SIGNED commission mode, design/MAINT-GPG-TRUST-LAYER.md §3 -- the "
                    "NIST-lineage authenticity aspiration that spec names for a GPG signature "
                    "(non-repudiation, forgery resistance against the apparatus itself, "
                    "outside-verifiability, §1); design/FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md "
                    "is this screen's own build basis (commission ledger rows 1724/1725).",
        "external": "external binary: gpg (GnuPG), must be on PATH; a real, ONGOING key-custody "
                 "burden for the operator (the private key and its revocation certificate, "
                 "user-guide/USER-GPG-TRUST-LAYER-FAQ.md §1-§2) -- stated plainly, this is the "
                 "one screen in this flow with a genuine standing operator responsibility "
                 "attached, though the SIGNING act itself is one-time (spec §1 item 5: no "
                 "ongoing signing burden, no signature gates added anywhere).",
    },
    "boundary_service": {
        "key": "boundary_service",
        "label": "boundary service",
        "aspiration": "none named directly; law/adr/0016-the-service-contract-is-an-enforcement-"
                    "surface.md governs its shape as house discipline, not an external "
                    "standard -- its request stream is the same OTel channel the sentry's NIST "
                    "AU-family aspiration below reads (design/FABLE-OTEL-SENTRY-SPEC.md §0).",
        "external": "Python packages beyond stdlib: fastapi + uvicorn (serving/boundary_service.py "
                 "own top-of-file imports); a network port (tools/setup_tui/probes.py "
                 "free_port); optionally a recurring operator process to keep alive "
                 "(tools/setup_tui/screens.py screen_boundary's systemd-unit PREPARED block, "
                 "taken when this process does not start the service itself).",
    },
    "observability_otelcol": {
        "key": "observability_otelcol",
        "label": "OTel collector (otelcol)",
        "aspiration": "NIST AU-family audit-supporting evidence at diagnostics tier "
                    "(design/FABLE-OTEL-SENTRY-SPEC.md §0: 'Watchdog alerts and attestations "
                    "alike are AU-family audit-supporting evidence, never IA-2 "
                    "authentication').",
        "external": "external binary: otelcol-contrib; a recurring operator process to keep alive "
                 "(tools/setup_tui/screens.py screen_observability's PREPARED start line).",
    },
    "observability_watchdog": {
        "key": "observability_watchdog",
        "label": "OTel model-provenance watchdog (otel-watch)",
        "aspiration": "NIST AU-family audit-supporting evidence at diagnostics tier, same "
                    "citation as otelcol above (design/FABLE-OTEL-SENTRY-SPEC.md §0, §3's v0 "
                    "watchdog: 'no principal, no ledger write, no kernel anything').",
        "external": "depends on the otelcol collector's JSONL export already running "
                 "(design/FABLE-OTEL-SENTRY-SPEC.md §3); a recurring operator daemon process "
                 "(the repo-root `./otel-watch --daemon` verb).",
    },
    "hydration_fork_provenance": {
        "key": "hydration_fork_provenance",
        "label": "fork provenance",
        "aspiration": "none named; a per-world fact, not a standards-conformance aim.",
        "external": "none.",
    },
    "hydration_role_charters": {
        "key": "hydration_role_charters",
        "label": "role charters",
        "aspiration": "adjacent to the principal-surface's NIST SP 800-63 aspiration "
                    "(design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md header) but NOT that "
                    "delta itself -- tools/role_charter.py predates s40/s41 and registers a "
                    "charter, not an event-sourced identity.",
        "external": "none beyond this repo's own tools/role_charter.py (no new binary/package).",
    },
    "hydration_makespan_scheduling_by_mandate": {
        "key": "hydration_makespan_scheduling_by_mandate",
        "label": "makespan-scheduling-by-mandate (durable decision)",
        "aspiration": "none named as an external standard; operating-rhythm house mandate "
                    "(user-guide/USER-RECIPES-FAQ.md 'Workflow patterns', maintainer directive "
                    "2026-07-14).",
        "external": "external Python package: ortools>=9.0 "
                 "(tools/makespan-scheduler/pyproject.toml), vendored as a git submodule.",
    },
    "hydration_drift_backstops": {
        "key": "hydration_drift_backstops",
        "label": "drift-backstops (durable decision)",
        "aspiration": "the project-wide NRC-grade-product posture (house discipline; memory: "
                    "quality-bar-nrc-grade-best-effort), not a named external standard.",
        "external": "none.",
    },
    "hydration_adr_adoption": {
        "key": "hydration_adr_adoption",
        "label": "ADR adoption (submenu)",
        "aspiration": "the ADRs under law/adr/ ARE this project's own standards-conformance law; "
                    "adopting one is adopting a named house standard, not an external one.",
        "external": "none.",
    },
    "hydration_single_branch_authoring": {
        "key": "hydration_single_branch_authoring",
        "label": "single-branch-authoring (durable "
        "decision)",
        "aspiration": "house version-control discipline (ledger row 1033), not a named external "
                    "standard.",
        "external": "none.",
    },
    "hydration_tags_are_serious_business": {
        "key": "hydration_tags_are_serious_business",
        "label": "tags-are-serious-business (durable "
        "decision)",
        "aspiration": "house release-discipline (ledger row 1027), not a named external standard.",
        "external": "none.",
    },
    "hydration_obligate_amplification_caution": {
        "key": "hydration_obligate_amplification_caution",
        "label": "obligate-amplification-caution "
        "(durable decision)",
        "aspiration": "house kernel-write discipline (ledger row 1640), not a named external "
                    "standard.",
        "external": "none.",
    },
    "hydration_doc_currency_at_the_seam": {
        "key": "hydration_doc_currency_at_the_seam",
        "label": "doc-currency-at-the-seam (durable "
        "decision)",
        "aspiration": "the project-wide NRC-grade-product posture (ledger row 1699), not a named "
                    "external standard.",
        "external": "none.",
    },
    "hydration_concurrent_builders_need_isolation": {
        "key": "hydration_concurrent_builders_need_isolation",
        "label": "concurrent-builders-need-isolation (durable decision)",
        "aspiration": "house concurrency discipline (ledger row 1502), not a named external "
                    "standard.",
        "external": "none.",
    },
    "hydration_runs_are_strictly_linear": {
        "key": "hydration_runs_are_strictly_linear",
        "label": "runs-are-strictly-linear (durable "
        "decision)",
        "aspiration": "house world-lifecycle discipline (maintainer ruling 2026-07-11), not a "
                    "named external standard.",
        "external": "none.",
    },
    "hydration_decomposition_to_unit_of_independent_resumption": {
        "key": "hydration_decomposition_to_unit_of_independent_resumption",
        "label": "decomposition-to-unit-of-independent-resumption (durable decision)",
        "aspiration": "house decomposition discipline, mined from the autoharn-panel live "
                    "deployment's own prior art, not a named external standard.",
        "external": "none.",
    },
    "hydration_claims_carry_witnesses": {
        "key": "hydration_claims_carry_witnesses",
        "label": "claims-carry-witnesses (durable "
        "decision)",
        "aspiration": "an evidentiary-discipline house standard (this repo's own CLAUDE.md "
                    "ORCHESTRATION section), not a named external standard.",
        "external": "none.",
    },
    "hydration_unanchored_review_briefs": {
        "key": "hydration_unanchored_review_briefs",
        "label": "unanchored-review-briefs (durable "
        "decision)",
        "aspiration": "house anti-anchoring-bias review discipline (ledger row 1278), not a named "
                    "external standard.",
        "external": "none.",
    },
    "hydration_fresh_context_review_for_delegated_work": {
        "key": "hydration_fresh_context_review_for_delegated_work",
        "label": "fresh-context-review-for-delegated-work (durable decision)",
        "aspiration": "house independent-review discipline (ledger row 1492), not a named "
                    "external standard.",
        "external": "none.",
    },
    "hydration_polychotomy_option_space_justification": {
        "key": "hydration_polychotomy_option_space_justification",
        "label": "polychotomy-option-space-justification (durable decision, SHOULD-grade)",
        "aspiration": "house anti-false-polychotomy discipline (ledger row 1915), not a named "
                    "external standard -- universal suggestion, not a mandatory rule.",
        "external": "none.",
    },
}
