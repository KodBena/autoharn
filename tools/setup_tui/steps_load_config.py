#!/usr/bin/env python3
"""tools/setup_tui/steps_load_config.py -- the "Load a configuration" tree node, an
`ActionSpec` (`tools.configtree.spec.ActionSpec`'s own docstring: immediate, not deferred to the
commit sweep). Maintainer round 5, ledger row 1115, defect C(i): "an in-UI affordance to load a
configuration file (the tree's root or a dedicated node offering bootstrap/templates/*.toml and
a path entry -- genre: preset/profile pickers), equivalent to --initial-config, usable at start."

Genre: a settings dialog's own "import/load defaults" picker (Qt/SAP, ADR-0019 Rule 1) -- picks a
known-good template (`bootstrap/templates/*.toml`) or a typed path, loads+validates it as a
PARTIAL config (`config_file.validate(doc, require_complete=False)`, the SAME partial-safe
contract `--initial-config` already has), and seeds every OTHER section's own live field
defaults straight into the shared model -- reachable and usable the INSTANT the app starts,
before any other section is ever visited, unlike a value that would only take effect after the
whole tree was already filled in and committed.

Named, honest limitation (mirrors `config_seam.build_initial_state_overrides`'s own documented
gap): only the scalar/list fields named in `_SCOPED_OVERRIDE_KEYS` below are seeded this way --
the principals-authority repeatable rows (register/competences/relations/charters) and a role
charter's own file path have no single scalar field to seed and are NOT seeded here, exactly the
same gap `--initial-config` already carries and names."""
from __future__ import annotations

from pathlib import Path

from tools.configtree import (ActionSpec, ChoiceField, FieldName, NodeId, ScopedFieldKey,
                               SectionResult, TextField)
from tools.setup_tui import config_file, config_seam

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = REPO_ROOT / "bootstrap" / "templates"

_NO_TEMPLATE = ""

# dotted config key -> (owning section slug, that section's OWN field name) -- every entry here
# is a SCALAR or LIST value with exactly one live-field home (never `substrate.db`, handled
# specially in `apply` below since its OWN target field name depends on `substrate.path`).
_SCOPED_OVERRIDE_KEYS: dict[str, tuple[str, str]] = {
    "substrate.run": ("substrate", "run"),
    "substrate.path": ("substrate", "path"),
    "substrate.host": ("substrate", "host"),
    "fork_target.governed_extend": ("fork-target", "governed_extend"),
    "fork_target.governed_extensions": ("fork-target", "governed_extensions"),
    "rehearsal.run": ("rehearsal", "run"),
    "birth.run": ("birth", "run"),
    "signed_genesis.run": ("signed-genesis", "run"),
    "signed_genesis.commission_statement": ("signed-genesis", "statement"),
    "boundary.configure": ("boundary", "run"),
    "boundary.start_now": ("boundary", "start_now"),
    "observability.run": ("observability", "run"),
    "observability.otelcol": ("observability", "otelcol"),
    "observability.otel_watch": ("observability", "otel_watch"),
    "hydration.run": ("hydration", "run"),
    "hydration.fork_provenance": ("hydration", "fork_provenance"),
    "hydration.fork_provenance_statement": ("hydration", "fork_provenance_statement"),
    "hydration.role_charters": ("hydration", "role_charters"),
    "hydration.durable_decisions": ("hydration", "durable_decisions"),
    "hydration.adopt_adrs": ("hydration", "adopt_adrs"),
}


def _discover_templates() -> tuple[tuple[str, str], ...]:
    """`bootstrap/templates/*.toml`, read fresh every call (the mechanical-derivation discipline
    every other closed-vocabulary source in this package already follows, e.g.
    `durable_decisions.list_adrs`) -- never a hand list that can drift from what is actually on
    disk."""
    opts = [(_NO_TEMPLATE, "(none -- type a custom path below instead)")]
    if TEMPLATES_DIR.is_dir():
        for path in sorted(TEMPLATES_DIR.glob("*.toml")):
            opts.append((str(path), path.stem))
    return tuple(opts)


def fields(state: dict) -> tuple:
    return (
        ChoiceField(name="template", label="Known-good template", options=_discover_templates(),
                    default=_NO_TEMPLATE,
                    help="Pre-fills every OTHER section's own defaults from a known-good config "
                    "file -- equivalent to --initial-config, applied right now instead of only "
                    "at launch. Partial-safe: a missing/incomplete key simply keeps that field's "
                    "own ordinary default, never a refusal."),
        TextField(name="path", label="...or a custom config file path", required=False,
                  help="Non-empty overrides the template choice above."),
    )


def apply(state: dict, answers: dict) -> SectionResult:
    template = answers.get("template", "") or ""
    custom_path = (answers.get("path", "") or "").strip()
    path = custom_path or template
    if not path:
        return SectionResult(ok=False, errors={"": "choose a template above, or type a custom "
                                             "path, first"})
    try:
        doc = config_file.load_config_file(path)
        config_file.validate(doc, require_complete=False)
    except config_file.ConfigError as exc:
        return SectionResult(ok=False, errors={"": str(exc)})

    live = state.setdefault("_live_fields", {})
    seeded: list[str] = []
    for dotted, (section, field_name) in _SCOPED_OVERRIDE_KEYS.items():
        val = config_file.get(doc, dotted)
        if val is None:
            continue
        key = ScopedFieldKey(section=NodeId(section), field=FieldName(field_name))
        live[key] = val
        seeded.append(dotted)

    db_val = config_file.get(doc, "substrate.db")
    if db_val is not None:
        target = "db_dedicated" if config_file.get(doc, "substrate.path") == "dedicated" else "db_existing"
        live[ScopedFieldKey(section=NodeId("substrate"), field=FieldName(target))] = db_val
        seeded.append(f"substrate.db -> substrate.{target}")

    bare_updates = config_seam.build_initial_state_overrides(doc)
    state.update(bare_updates)

    lines = [f"loaded: {path}"]
    if seeded:
        lines.append(f"seeded {len(seeded)} field default(s): {', '.join(sorted(seeded))}")
    else:
        lines.append("this config named none of the fields this loader knows how to seed -- "
                      "every section keeps its own ordinary default")
    if bare_updates:
        lines.append(f"seeded shared default(s): {', '.join(sorted(bare_updates))}")
    lines.append("visit any section to see its now-updated default -- nothing here is queued "
                  "or committed; every section's own submit still runs at commit time as usual.")
    return SectionResult(ok=True, info_lines=tuple(lines))


STEP = ActionSpec(
    slug="load-config", title="Load a configuration", group="Setup", fields=fields, apply=apply,
    apply_label="Load",
    description="Pick one of this repo's own known-good templates (bootstrap/templates/*.toml) "
    "or type a path, then press Load -- every OTHER section's own field defaults update "
    "immediately, reflecting the loaded config (the SAME contract --initial-config has at "
    "process launch, just usable from inside the running editor).")
