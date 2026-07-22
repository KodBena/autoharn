#!/usr/bin/env python3
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
     module-level constants -- `PREFLIGHT_BINARIES` (the preflight screen's probed-binary
     tuple) and `SUBSTRATE_CHOICES` (the substrate screen's `ask_choice` option keys) -- plus
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

CONTENT SPLIT (law/adr/0012's 2026-07-22 Amendment, P10 -- "data is not code", design/
FABLE-SETUP-TUI-FIELD-STRATEGY.md Track 2.2, phase 1): the REGISTRY entries' authored prose
(`aspiration`/`external`) used to live as literal FeatureFact(...) constructor calls in THIS
file -- 62% of it by volume, a writing edit indistinguishable from a logic edit in every diff.
That content now lives in tools/setup_tui/feature_facts_data.py's `RAW_ENTRIES` (a data-only
module: typed literals, zero functions, zero logic) and is assembled into the typed `REGISTRY`
below by one line of pure wiring. The FeatureFact dataclass DEFINITION stays here -- it is the
logic-side contract P10 leaves with logic, not content. `fact()`/`facts_block()`/
`derive_live_keys()`/`check_registry()` and every consumer's import path (`feature_facts.REGISTRY`,
`feature_facts.FeatureFact`, `feature_facts.fact`, `feature_facts.check_registry`) are UNCHANGED.

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import here is top of file.
"""
from __future__ import annotations

from dataclasses import dataclass

from tools.configtree import DescriptionElement, PROVENANCE_LABEL
from tools.setup_tui import content, durable_decisions


@dataclass(frozen=True)
class FeatureFact:
    """SCHEMA (round 7, ledger row 1119 -- following the Fable RCA consult,
    design/CONSULT-FABLE-ELUCIDATION-RCA-2026-07-22.md; supersedes round 6's aspiration/
    standards/mechanism/external four-slot vocabulary, which the consult diagnosed as: D1
    CRITICAL, a `standards` slot silently PROMOTED an aspiration -- "aspires to this standard's
    decomposition" -- into an unqualified conformance claim, a truth-value change no mechanical
    check could catch (every token survived; the qualifying edge between them did not); D4, a
    `mechanism` slot held design docs and citations, never actual mechanism; D5, `external` meant
    three different things across sections; D9, four labeled lines per fact read as
    "serialization masquerading as layout.").

    `lead` -- REQUIRED-if-anything-is-said, decision-guidance prose (D7: what choosing/having
    this costs, requires, or changes for the operator -- written as a sentence, D8, never
    slot:value telegraphy). A standard this feature ASPIRES to (never CONFORMS to, D1) is named
    INSIDE this sentence, with its qualifying hedge kept intact ("aspires to X's decomposition",
    never "Standards: X") -- there is no separate standards slot to promote it into. Empty string
    = nothing to say (D6: an empty slot is not rendered at all, never "none named").
    `external` -- ONE meaning only (D5): a concrete EXTERNAL PREREQUISITE OR STANDING
    OBLIGATION the operator must supply or keep -- a binary on PATH, a live cluster, a recurring
    process to keep alive. Never a description of what the feature does internally. Empty = none.
    `provenance` -- OPTIONAL list of citations a FOUNDING OPERATOR could actually open and read
    (this repo's own `user-guide/*` docs, or `law/adr/` itself) -- rendered demoted, LAST, one
    `PROVENANCE_LABEL` element per path (D2: "where a citation is genuinely operator-relevant it
    renders as provenance, demoted and last").
    `maintainer_refs` -- OPTIONAL list of internal-only citations (ledger rows, `design/FABLE-*`/
    `design/MAINT-*` build-basis docs, kernel lineage SQL files, AI-memory notes) -- NEVER
    rendered by any widget (D2: "most are maintainer-relevant only: move those OUT of the
    operator surface entirely"). Kept here only so the maintainer's own audit trail names where
    each fact's claim comes from; `elements()`/`line()` never read this field.

    `line()` stays the tabular/log-line renderer (`facts_block`'s own checklist/info-line use, an
    EXEMPT class this codebase already established -- `.ct-info-line`/`.ct-precheck-line` are
    deliberately never capped/wrapped, and this project's own "claims carry witnesses" register
    is at home there); `elements()` is the typed accessor for the INTERACTIVE elucidation area --
    the two are deliberately different shapes for deliberately different registers (D7/D8), never
    one reused where the other belongs (the round-5 mistake round 6 answered on the WIDTH axis
    only; round 7 answers it on the TRUTH/AUDIENCE/ALTITUDE axes)."""
    key: str
    label: str
    lead: str = ""
    external: str = ""
    provenance: tuple[str, ...] = ()
    maintainer_refs: tuple[str, ...] = ()

    def line(self) -> str:
        parts = [p for p in (self.lead, f"external: {self.external}" if self.external else "") if p]
        body = "; ".join(parts) if parts else "(no operator-facing content)"
        return f"  facts [{self.label}] -- {body}"

    def elements(self, *, prefix: "str | None" = None) -> "ElucidationValue | None":
        """The section-description/elucidation rendering of this fact (round 7): `lead` renders
        FIRST as unlabeled connective prose (D7/D8); `external`, if present, follows as a SHORT
        labeled "Requires" line (a genuinely separate, standing prerequisite -- never folded into
        `lead` when it is a distinct, ongoing fact rather than the sentence's own main point);
        `provenance`, if any, renders LAST, demoted, one `PROVENANCE_LABEL` element per path.
        Blank components are simply absent (D6) -- a fact with nothing to say renders NOTHING.
        `prefix`, if given (a section combining MORE THAN ONE fact under one description, e.g.
        substrate's existing/dedicated paths), disambiguates the External/Full-basis lines only
        -- `lead`'s own prose does not need it (a real `ElucidationHeading`, built by the caller,
        names the group instead, D9)."""
        out: list = []
        if self.lead:
            out.append(self.lead)
        if self.external:
            label = f"{prefix} Requires" if prefix else "Requires"
            out.append(DescriptionElement(label, self.external))
        for path in self.provenance:
            label = f"{prefix} {PROVENANCE_LABEL}" if prefix else PROVENANCE_LABEL
            out.append(DescriptionElement(label, path))
        if not out:
            return None
        if len(out) == 1 and isinstance(out[0], str):
            return out[0]
        return tuple(out)


# ---------------------------------------------------------------------------------------------
# Registry -- every selectable act the flow offers (§2's enumeration): the substrate paths, the
# boundary service, observability (otelcol + watchdog), each hydration item, and the
# preflight-probed toolchains (idris2, clingo/ASP, python3, psql, textual/urwid if present).
# Built straight from feature_facts.toml (content.py's own validated FEATURE_FACTS) -- one line
# of construction, never a parse, never a runtime file read.
# ---------------------------------------------------------------------------------------------

REGISTRY: dict[str, FeatureFact] = {
    row["key"]: FeatureFact(key=row["key"], label=row["label"], lead=row.get("lead", ""),
                             external=row.get("external", ""),
                             provenance=tuple(row.get("provenance", ())),
                             maintainer_refs=tuple(row.get("maintainer_refs", ())))
    for row in content.FEATURE_FACTS
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
        "fork_target_governed_files",
        "principals_authority",
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
