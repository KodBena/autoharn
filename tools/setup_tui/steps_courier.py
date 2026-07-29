#!/usr/bin/env python3
"""tools/setup_tui/steps_courier.py -- the Courier step's UI-free core (work item
setup-tui-config-extension, ledger row 685's audit / row 693: gap 6, "a courier section/screen").

`courier.toml` (design/FABLE-MISSIVES-KERNEL-SPEC.md §5, `libexec/autoharn/courier`'s own
`load_courier_config`) carries four facts: `authn` (a NAMED EMPTY SLOT, row 1162 -- the only
ratified v1 value is `"single-operator"`, any other value refused at load), `self`/`self_base`
(this world's own name and boundary base URL), and `[courier.counterparts]` (world name -> base
URL, at least one entry required by `load_courier_config` itself).

`self`/`self_base` are DERIVED facts, not editable fields (ADR-0019 C2, "no editable control on a
derived value" -- this library carries NO read-only-reference field kind at all, `tools.
configtree.spec`'s own `DuplicatedSharedFieldError` docstring: a derived value renders via
`info_lines`, never a second field mirroring a fact Birth/Boundary already own). `authn` is not a
field either -- it is a fixed fact (the named empty slot), surfaced as static text, never a
choice this screen offers. The ONE real field is `counterparts`.

WHY THIS SECTION MAY WRITE NO FILE AT ALL: `load_courier_config` refuses to run against BOTH a
missing file AND an empty `[courier.counterparts]` table (`not counterparts` in that function's
own guard) -- so a `courier.toml` with zero counterparts would never actually load; writing one
anyway would be dead weight an operator discovers only when `./autoharn courier` refuses it. This
step's own honest choice (disclosed here, not silently decided): when the operator leaves
`counterparts` empty, `courier.toml` is NOT queued for writing at all -- "nothing to courier with,
yet" is represented by the file's absence, exactly the shape `load_courier_config`'s own missing-
file refusal already teaches an operator to expect and fix later (add a counterpart, re-run this
screen, or hand-author the file per its own module docstring's worked example).

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import here is top of file."""
from __future__ import annotations

import os

from tools.configtree import ListField, SectionResult, SectionSpec, TextField
from tools.setup_tui import checklist as ck
from tools.setup_tui.idtypes import WorldName, WorldNameError
from tools.setup_tui.plan import PlanEntry, WriteAct

_SLUG = "courier"

# The single ratified v1 value (row 1162's own named empty slot) -- never a choice this screen
# offers; `libexec/autoharn/courier`'s own `load_courier_config` refuses any other value loudly.
_AUTHN = "single-operator"


def _validate_counterpart_world(raw: str) -> "str | None":
    try:
        WorldName.parse(raw)
    except WorldNameError as exc:
        return str(exc)
    return None


def _validate_counterpart_base_url(raw: str) -> "str | None":
    if not (raw.startswith("http://") or raw.startswith("https://")):
        return "must start with http:// or https://"
    return None


def _counterparts_field() -> ListField:
    return ListField(
        name="counterparts", label="Counterpart world to courier missives with",
        item_fields=(
            TextField(name="world", label="Counterpart world name",
                      validator=_validate_counterpart_world),
            TextField(name="base_url", label="Counterpart boundary base URL "
                      "(e.g. http://127.0.0.1:8400)", validator=_validate_counterpart_base_url),
        ),
        summarize=lambda r: f"{r['world']} -> {r['base_url']}",
        help=("courier.toml's own [courier.counterparts] table -- one entry per world this "
              "world exchanges missives with (design/FABLE-MISSIVES-KERNEL-SPEC.md §5). authn "
              "is fixed at 'single-operator' (the only ratified v1 value, row 1162's named "
              "empty slot) -- not a choice here. self/self_base are DERIVED from this world's "
              "own name (Birth) and picked boundary URL (Boundary above), never editable here "
              "(ADR-0019 C2). Leave this list empty if this world couriers with no one yet -- "
              "courier.toml is then not written at all this run (load_courier_config's own "
              "contract already refuses to run against an empty counterparts table, so a stub "
              "file would never be a working config)."))


def fields(state: dict) -> tuple:
    # NO "self"/"self_base" fields here -- both are Birth's/Boundary's own facts (`state["world"]`/
    # `state["boundary_url"]`), rendered read-only via `submit`'s own info_lines below, never a
    # second field declaration (ADR-0019 C2 + `tools.configtree.spec.validate_shared_ownership`'s
    # single-editable-home discipline, the SAME reasoning `steps_boundary.py`'s own `fields()`
    # docstring gives for dropping its "dest"/"world" fields).
    return (_counterparts_field(),)


def _blocked_needs_boundary(state: dict) -> "str | None":
    """courier.toml's self/self_base come from Birth's world name and Boundary's picked port --
    nothing to derive until both have run."""
    missing = []
    if not state.get("dest"):
        missing.append("Fork/target (a destination directory)")
    if not state.get("world"):
        missing.append("Birth (a world name)")
    if not state.get("boundary_url"):
        missing.append("Boundary (a picked boundary URL)")
    if not missing:
        return None
    return f"requires: {' and '.join(missing)} to be set first"


def submit(state: dict, answers: dict) -> SectionResult:
    cl = state["_checklist"]
    self_name = state.get("world", "")
    self_base = state.get("boundary_url", "")
    lines = [
        f"self (derived from Birth's own world name): {self_name}",
        f"self_base (derived from Boundary's own picked port): {self_base}",
        f"authn: {_AUTHN} (fixed -- row 1162's named empty slot, not a choice)",
    ]

    rows = answers["counterparts"]
    if not rows:
        cl.add(_SLUG, "courier.toml", ck.INSTRUCTED,
                "no counterparts entered -- NOT written (load_courier_config refuses an empty "
                "[courier.counterparts] table just as loudly as a missing file, so a stub would "
                "never be a working config; add a counterpart and revisit this screen, or "
                "hand-author courier.toml later)")
        lines.append("no counterparts entered -- courier.toml will NOT be written this run.")
        return SectionResult(ok=True, state_updates={"courier_counterparts": []},
                              info_lines=tuple(lines))

    seen_worlds: set[str] = set()
    for row in rows:
        world = (row.get("world") or "").strip()
        base_url = (row.get("base_url") or "").strip()
        if not world:
            return SectionResult(ok=False, errors={"counterparts": "every counterpart needs a "
                                                     "world name"})
        try:
            WorldName.parse(world)
        except WorldNameError as exc:
            return SectionResult(ok=False, errors={"counterparts": f"'{world}': {exc}"})
        if world == self_name:
            return SectionResult(ok=False, errors={"counterparts": f"'{world}' is this world's "
                                                     "own name -- a counterpart must be a "
                                                     "DIFFERENT world"})
        if world in seen_worlds:
            return SectionResult(ok=False, errors={"counterparts": f"'{world}' is declared more "
                                                     "than once"})
        seen_worlds.add(world)
        if not base_url:
            return SectionResult(ok=False, errors={"counterparts": f"'{world}' needs a base URL"})

    dest = state.get("dest", "")
    resolved_rows = [{"world": (r.get("world") or "").strip(),
                       "base_url": (r.get("base_url") or "").strip()} for r in rows]
    counterparts_toml = "\n".join(f'{r["world"]} = "{r["base_url"]}"' for r in resolved_rows)
    toml_text = ("[courier]\n"
                 f'authn = "{_AUTHN}"\n'
                 f'self = "{self_name}"\n'
                 f'self_base = "{self_base}"\n'
                 "\n"
                 "[courier.counterparts]\n"
                 f"{counterparts_toml}\n")
    toml_path = os.path.join(dest, "courier.toml")
    lines.append(f"--- queuing write: {toml_path} ---\n{toml_text}")
    state["_plan"].append(PlanEntry(screen=_SLUG, item="courier.toml written",
                                     lesson="the courier verb's own config file",
                                     act=WriteAct(path=toml_path, content=toml_text)))
    return SectionResult(ok=True, state_updates={"courier_counterparts": resolved_rows},
                          info_lines=tuple(lines))


STEP = SectionSpec(
    slug=_SLUG, title="Courier", group="Runtime", fields=fields, submit=submit,
    blocked=_blocked_needs_boundary,
    description=("courier.toml -- this world's own missive-courier config. self/self_base are "
                  "derived from Birth's world name and Boundary's picked URL (never editable "
                  "here); authn is fixed at single-operator; add zero or more counterpart "
                  "worlds below. Zero counterparts means courier.toml is not written this run."))
