#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-16T02:43:35Z
#   last-change: 2026-07-16T02:43:35Z
#   contributors: 9a17b6b9/main
# <<< PROVENANCE-STAMP <<<

"""workflow_check — the v0 validator for declared pipeline workflows under design/workflows/*.toml
(ledger work item pipeline-dsl-v0; governing exploration doc
vestigial_documentation/design/FABLE-PIPELINE-DSL-EXPLORATION.md, uncommitted in the maintainer's main checkout, read
verbatim from its absolute path during this build).

WHAT THIS CHECKS. The exploration doc names exactly four fields a v0 workflow declaration may
carry -- phases, roles, convergence, landing_zones -- and nothing else ("Not a workflow engine.
No conditionals, no loops, no expressions."). This tool refuses, with a teach-text explaining
why, any file that:

  1. has a dependency CYCLE among phases (the `depends_on` graph must be a DAG -- the same
     acyclicity discipline this project's own ledger already carries on its dependency edges,
     cited by the exploration doc itself);
  2. declares a phase with NO ROLE (no `authors`, `reviews`, or `implements` entry under
     `[roles.<phase>]` -- a phase nobody is assigned to cannot be dispatched);
  3. declares a phase with NO LANDING ZONE for its deliverable (every phase in this grammar
     produces a deliverable by definition -- "named stages" per the exploration doc's field 1 --
     so every phase name must have a non-empty `[landing_zones]` entry; this mechanically
     discharges the lesson of ledger item `dispatch-deliverable-landing-zone`, where a deployment
     lost a full audit cycle's evidence to an ephemeral scratchpad because no dispatch surface
     asked the question);
  4. carries an UNKNOWN top-level key (v0's grammar is exactly `phases`, `roles`, `convergence`,
     `landing_zones` -- an unrecognized key is refused rather than silently ignored, the same
     lesson this project's own `led.tmpl` unknown-flag handling teaches: an unenforced typo or
     speculative field is a silent scope leak, not a convenience).

It also refuses a handful of narrower shape defects in the same four fields (a phase with no
`name`, a duplicate phase name, a `depends_on`/`roles`/`convergence`/`landing_zones` entry naming
a phase that does not exist, a `convergence` entry missing `done` or `escalation_event`) -- these
are not separately called out in the work item's four mandatory refusals, but they are the same
"refuse loudly, never silently accept a malformed plan" discipline ADR-0000 names for a declared
workflow, so they are checked here rather than left for a later, harder-to-diagnose failure.

WHAT THIS DELIBERATELY DOES NOT CHECK. It never evaluates whether a `done`/`escalation_event`
string is a GOOD description, whether a role assignment is wise, or whether a landing zone is the
RIGHT place -- those are judgment calls for the human or agent authoring the declaration, per the
exploration doc's "Not speculative" section: this tool is structural well-formedness only, the
same J-boundary this project's kernel already draws (design/ORCH-SPEC-RESOURCE-REGISTRY.md sec 7:
"no machine can detect that a judgment-triggered entry SHOULD have been made").

Usage:
    python3 tools/workflow_check.py <path-to.toml> [<path-to.toml> ...]

Exit 0 with a one-line summary per valid file. Exit 1 listing every refusal across ALL given files
before exiting non-zero, so a batch run does not require N separate invocations to see everything
wrong at once.
"""
from __future__ import annotations

import sys
import tomllib
from pathlib import Path

ALLOWED_TOP_LEVEL_KEYS = {"phases", "roles", "convergence", "landing_zones"}
ROLE_KEYS = {"authors", "reviews", "implements"}


class Refusal(Exception):
    """Raised with a teach-text explaining exactly why the declaration was refused."""


def _refuse(path: Path, teach_text: str) -> None:
    raise Refusal(f"{path}: REFUSED -- {teach_text}")


def _check_unknown_top_level_keys(path: Path, doc: dict) -> None:
    unknown = sorted(set(doc.keys()) - ALLOWED_TOP_LEVEL_KEYS)
    if unknown:
        _refuse(
            path,
            f"unknown top-level key(s): {', '.join(unknown)}. v0's grammar is exactly four "
            f"fields -- phases, roles, convergence, landing_zones -- nothing else "
            f"(vestigial_documentation/design/FABLE-PIPELINE-DSL-EXPLORATION.md, \"What the DSL would be\"). An "
            f"unrecognized key is refused rather than silently ignored, the same lesson this "
            f"project's own led.tmpl unknown-flag handling teaches: a typo'd or speculative "
            f"field must not silently vanish. Remove it, or if it names a real recurring need, "
            f"bring it to the maintainer as a grammar-growth question -- the vocabulary grows "
            f"only from harvested specimens, never speculatively."
        )


def _extract_phase_names(path: Path, doc: dict) -> list[str]:
    phases = doc.get("phases")
    if phases is None:
        _refuse(path, "no [[phases]] declared -- a workflow with zero phases has nothing to do.")
    if not isinstance(phases, list):
        _refuse(path, "'phases' must be an array of tables ([[phases]] entries), got "
                      f"{type(phases).__name__}.")

    names: list[str] = []
    seen: set[str] = set()
    for i, phase in enumerate(phases):
        if not isinstance(phase, dict) or "name" not in phase or not phase["name"]:
            _refuse(path, f"phases[{i}] has no 'name' -- every phase must be named so roles, "
                          f"convergence, and landing_zones can refer to it.")
        name = phase["name"]
        if name in seen:
            _refuse(path, f"phase name '{name}' is declared more than once -- phase names must "
                          f"be unique.")
        seen.add(name)
        names.append(name)
    return names


def _check_cycle(path: Path, doc: dict, phase_names: list[str]) -> None:
    edges: dict[str, list[str]] = {name: [] for name in phase_names}
    for phase in doc["phases"]:
        name = phase["name"]
        depends_on = phase.get("depends_on", [])
        if not isinstance(depends_on, list):
            _refuse(path, f"phase '{name}': 'depends_on' must be an array of phase names, got "
                          f"{type(depends_on).__name__}.")
        for dep in depends_on:
            if dep not in edges:
                _refuse(path, f"phase '{name}' depends_on unknown phase '{dep}' -- every "
                              f"depends_on entry must name a phase declared in [[phases]].")
        edges[name] = list(depends_on)

    # DFS cycle detection over the depends_on graph (edge name -> its dependencies).
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {name: WHITE for name in phase_names}
    path_stack: list[str] = []

    def visit(node: str) -> None:
        color[node] = GRAY
        path_stack.append(node)
        for dep in edges[node]:
            if color[dep] == GRAY:
                cycle = path_stack[path_stack.index(dep):] + [dep]
                _refuse(
                    path,
                    f"dependency cycle among phases: {' -> '.join(cycle)}. Phases must form a "
                    f"DAG with a valid topological order (vestigial_documentation/design/FABLE-PIPELINE-DSL-EXPLORATION.md "
                    f"field 1, 'Phases' -- 'the harness can check for cycles, the same acyclicity "
                    f"discipline this project's own ledger already carries on its dependency "
                    f"edges'). Break the cycle by removing or redirecting one of the depends_on "
                    f"edges above; the DSL is not a workflow engine and has no notion of a loop "
                    f"that could give a cycle a valid execution order."
                )
            elif color[dep] == WHITE:
                visit(dep)
        path_stack.pop()
        color[node] = BLACK

    for name in phase_names:
        if color[name] == WHITE:
            visit(name)


def _check_roles(path: Path, doc: dict, phase_names: list[str]) -> None:
    roles = doc.get("roles", {})
    if not isinstance(roles, dict):
        _refuse(path, f"'roles' must be a table keyed by phase name, got {type(roles).__name__}.")

    for key in roles:
        if key not in phase_names:
            _refuse(path, f"[roles.{key}] names a phase that is not declared in [[phases]].")

    for name in phase_names:
        entry = roles.get(name)
        if not isinstance(entry, dict):
            _refuse(
                path,
                f"phase '{name}' has no role declared (no [roles.{name}] table at all). Every "
                f"phase must name at least one role -- field 2 of "
                f"vestigial_documentation/design/FABLE-PIPELINE-DSL-EXPLORATION.md ('Roles -- which model tier authors, "
                f"which reviews, which implements, per phase'). A phase nobody is assigned to "
                f"cannot be dispatched; add [roles.{name}] with at least one of authors / "
                f"reviews / implements."
            )
        present = {k: v for k, v in entry.items() if k in ROLE_KEYS and v}
        unknown_role_keys = sorted(set(entry.keys()) - ROLE_KEYS)
        if unknown_role_keys:
            _refuse(
                path,
                f"[roles.{name}] carries unknown key(s): {', '.join(unknown_role_keys)}. The "
                f"only role verbs v0 declares are authors, reviews, implements -- the exploration "
                f"doc's own three verbs ('which model tier authors, which reviews, which "
                f"implements')."
            )
        if not present:
            _refuse(
                path,
                f"phase '{name}' has no role declared: [roles.{name}] exists but every one of "
                f"authors / reviews / implements is empty or absent. Every phase must name at "
                f"least one role (vestigial_documentation/design/FABLE-PIPELINE-DSL-EXPLORATION.md field 2) -- a phase "
                f"nobody is assigned to cannot be dispatched."
            )


def _check_convergence(path: Path, doc: dict, phase_names: list[str]) -> None:
    convergence = doc.get("convergence", {})
    if not isinstance(convergence, dict):
        _refuse(path, f"'convergence' must be a table keyed by phase name, got "
                      f"{type(convergence).__name__}.")

    for key in convergence:
        if key not in phase_names:
            _refuse(path, f"[convergence.{key}] names a phase that is not declared in "
                          f"[[phases]].")

    for name in phase_names:
        entry = convergence.get(name)
        if not isinstance(entry, dict):
            _refuse(
                path,
                f"phase '{name}' has no [convergence.{name}] table. Field 3 of "
                f"vestigial_documentation/design/FABLE-PIPELINE-DSL-EXPLORATION.md requires 'what \"done\" means per "
                f"phase, and the typed escalation event ... that routes to the maintainer when "
                f"it is not reached' -- add [convergence.{name}] with 'done' and "
                f"'escalation_event'."
            )
        if not entry.get("done"):
            _refuse(
                path,
                f"[convergence.{name}] has no 'done' -- what \"done\" means for this phase must "
                f"be stated (vestigial_documentation/design/FABLE-PIPELINE-DSL-EXPLORATION.md field 3)."
            )
        if not entry.get("escalation_event"):
            _refuse(
                path,
                f"[convergence.{name}] has no 'escalation_event' -- the typed event that routes "
                f"to the maintainer when this phase does not converge must be named, even if it "
                f"never fires in practice (vestigial_documentation/design/FABLE-PIPELINE-DSL-EXPLORATION.md field 3: "
                f"'Escalation on typed events only, never on self-assessment'). A bare 'done' "
                f"with no named escalation leaves non-convergence with nowhere defined to go."
            )


def _check_landing_zones(path: Path, doc: dict, phase_names: list[str]) -> None:
    landing_zones = doc.get("landing_zones", {})
    if not isinstance(landing_zones, dict):
        _refuse(path, f"'landing_zones' must be a table keyed by phase name, got "
                      f"{type(landing_zones).__name__}.")

    for key in landing_zones:
        if key not in phase_names:
            _refuse(path, f"[landing_zones.{key}] names a phase that is not declared in "
                          f"[[phases]].")

    for name in phase_names:
        value = landing_zones.get(name)
        empty = value is None or (isinstance(value, str) and not value.strip())
        if isinstance(value, dict):
            empty = not value.get("zone")
        if empty:
            _refuse(
                path,
                f"phase '{name}' has no landing_zones.{name} entry -- its deliverable has "
                f"nowhere declared to land. Field 4 of vestigial_documentation/design/FABLE-PIPELINE-DSL-EXPLORATION.md "
                f"requires this for every phase ('where each phase's deliverable lands so it "
                f"outlives the session'), and mechanically discharges the lesson of ledger item "
                f"dispatch-deliverable-landing-zone: a deployment lost a full audit cycle's "
                f"evidence to an ephemeral scratchpad because no dispatch surface asked the "
                f"question. Add a landing_zones.{name} entry naming where this phase's output "
                f"lives after the session ends."
            )


def check_file(path: Path) -> str:
    """Validate one workflow declaration. Returns a one-line summary on success; raises
    Refusal (with a teach-text) on the first structural defect found."""
    try:
        raw = path.read_bytes()
    except OSError as exc:
        _refuse(path, f"could not read file: {exc}")
    try:
        doc = tomllib.loads(raw.decode("utf-8"))
    except tomllib.TOMLDecodeError as exc:
        _refuse(path, f"not valid TOML: {exc}")

    _check_unknown_top_level_keys(path, doc)
    phase_names = _extract_phase_names(path, doc)
    _check_cycle(path, doc, phase_names)
    _check_roles(path, doc, phase_names)
    _check_convergence(path, doc, phase_names)
    _check_landing_zones(path, doc, phase_names)

    return f"{path}: OK -- {len(phase_names)} phase(s), well-formed v0 workflow declaration."


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: python3 tools/workflow_check.py <path-to.toml> [<path-to.toml> ...]",
              file=sys.stderr)
        return 2

    refusals: list[str] = []
    oks: list[str] = []
    for arg in argv:
        path = Path(arg)
        try:
            oks.append(check_file(path))
        except Refusal as refusal:
            refusals.append(str(refusal))

    for line in oks:
        print(line)
    for line in refusals:
        print(line, file=sys.stderr)

    return 1 if refusals else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
