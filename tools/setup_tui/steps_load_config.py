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

COMPLETENESS (cycle-2 fix round, AUDIT.md MAJOR #2): seeding runs through `config_seam.
build_live_field_overrides` -- the ONE implementation this action and `tools.setup_tui.app`'s own
`--initial-config` CLI handling BOTH call (P1), so a completeness fix reaches both paths at once.
That function's own docstring has the full account: every scalar/list field AND the
principals-authority repeatable rows (register/competences/relations) are seeded; the one
genuinely unseedable fact (a role charter's own file path -- host-specific, excluded BY TYPE
from the config schema) is DISCLOSED BY NAME in this action's own info line, never silently
dropped."""
from __future__ import annotations

from pathlib import Path

from tools.configtree import ActionSpec, ChoiceField, SectionResult, TextField
from tools.setup_tui import config_file, config_seam

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = REPO_ROOT / "bootstrap" / "templates"

_NO_TEMPLATE = ""


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
    overrides, seeded, unseedable = config_seam.build_live_field_overrides(doc)
    live.update(overrides)

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
    if unseedable:
        lines.append("not seeded (by design, not an omission): " + "; ".join(unseedable))
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
