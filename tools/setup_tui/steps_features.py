#!/usr/bin/env python3
"""tools/setup_tui/steps_features.py -- the DECLARATIVE FEATURE MANIFEST step (work item
deploy-feature-manifest, ledger row 1274's "as recommended" reframe of the two now-superseded
items deploy-time-feature-selection / deployment-makespan-offering).

WHAT THIS SCREEN IS: checkboxes for the five deploy-time features the maintainer named --
portable ADRs, vendored skills, panel extension, principal set, makespan-scheduler tier (the
tier expressed via the EXISTING blessed/mandated/forbidden RESOURCES granularity,
design/ORCH-SPEC-RESOURCE-ACCOUNTING.md §3) -- resolved into ONE JSON manifest file,
`features.json`, that `bootstrap/new-project.sh` itself reads (`--features-file`) and applies.
THE MANIFEST FILE IS THE DURABLE RECORD (hand-editable, hand-authorable without ever running
this screen); this screen is sugar over it, nothing more -- it writes exactly the file an
operator could have typed by hand, through the SAME `runner.write_file` choke point every other
screen's real-effect writes go through.

WHY A NEW FILE, NOT `.claude/apparatus.json` (the commission's own explicit question):
`user-guide/USER-CONFIGURATION.md`'s own words are unambiguous about what apparatus.json IS --
"your project's one switchboard: a `deny_hint` string plus a `mechanisms` object, one entry per
SAFETY MECHANISM this project ships, each independently set to off/observe/enforce". Every hook
that reads it (`filing/apparatus_registry.py`'s known-mechanism set) and the gate that polices it
(`gates/apparatus_unknown_keys.py`) are scoped to that ONE closed vocabulary of hook-enforcement
modes -- a scaffold-time inclusion decision ("did this world get the panel extension vendored
in") is a semantically different fact (WHAT got born, not HOW HARD an already-born mechanism
polices itself) that does not belong in that closed vocabulary, and adding it there would widen
apparatus.json's own unknown-key sweep to swallow a class of key its own gate was never written
to reason about. A SEPARATE file keeps each switchboard's closed vocabulary honest.

WHY NOT `world-config.toml` (`config_seam.save_world_config`) EITHER: that file is this WIZARD's
own after-the-fact self-application record (config_seam.py's own module docstring, job 4) --
written ONCE, AFTER every screen (including a live birth) has already run, purely so a LATER
`--from-config` replay can reproduce the same wizard session. `features.json` is the opposite
direction: an INPUT the scaffold (`new-project.sh`) consumes DURING birth, decided BEFORE the
kernel exists, hand-editable by an operator who never opens this TUI at all. The two files
coexist without overlap: this screen's OWN resolved decisions are ALSO folded into
`world-config.toml`'s `features.*` keys (`config_seam.py`'s `_SCOPED_OVERRIDE_KEYS`/
`capture_resolved_config`) purely for --from-config replay parity with every other section --
`features.json` itself remains the one file `new-project.sh` actually reads.

FIVE FIELDS, mapped straight onto `bootstrap/new-project.sh`'s five feature effects (see that
script's own `apply_features_file`-adjacent block for the per-effect WITNESSED/DECLARATIVE-ONLY
disposition):
  - `portable_adrs` (bool, default True) -- mirrors the EXISTING `--no-law` flag (tracker item
    portable-adr-delivery, already wired, already witnessed since 2026-07-15); this manifest
    just gives the same decision a checkbox and a durable, hand-editable home instead of a
    flag an operator has to remember to type.
  - `vendored_skills` (bool, default True) -- NEW opt-out; the scaffold vendors every skill
    under bootstrap/templates/claude-skills/ unconditionally today (no flag existed before this
    build), the manifest's first genuinely new lever.
  - `panel_extension` (bool, default False) -- NEW: a local (never network) `git clone` of this
    checkout's own `tools/autoharn-panel` submodule into `<dest>/panel`, whose own `backend/
    config.py` auto-discovers `<dest>/deployment.json` by the nested-repo convention its own
    README already documents ("the latter finds an autoharn checkout's own record when this repo
    is nested under it").
  - `makespan_tier` (choice: off/available/blessed/mandated/forbidden, default off) -- the
    carried-forward deployment-makespan-offering instance (sibling checkout + editable venv
    install, ledger's own design/workflows/panel-msched-resource-provisioning.toml specimen).
    DECLARATIVE-ONLY in this build (see new-project.sh's own block comment for the named
    blocker: an operator-designated venv path and a pip install are not knowable/performable at
    scaffold time without a network call this scaffold does not make) -- writes a ready-to-paste
    `resource:` declaration template, never fakes the install.
  - `principal_set` (repeatable rows: name/agent_class/purpose) -- reuses the IDENTICAL
    `register-principal` shape `steps_principals_authority.py`'s own "register" field already
    uses (content.PA_CLASS_CHOICES); a row here is applied by `new-project.sh` itself, through
    the just-written `led` shim, for `--new-world` mode only (a classic-mode scaffold has no
    kernel/ledger to register into yet -- a nonempty `principal_set` there is refused loudly,
    never silently dropped).

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import here is top of file."""
from __future__ import annotations

import json
import os
import tempfile

from tools.configtree import (ChoiceField, ConfirmField, ListField, SectionResult, SectionSpec,
                               TextField)
from tools.setup_tui import checklist as ck
from tools.setup_tui import content
from tools.setup_tui.runner import write_file

_SLUG = "features"

MAKESPAN_TIER_CHOICES = (
    ("off", "off -- no makespan-scheduler resource declaration written"),
    ("available", "available -- MAY reach for it (weakest deontic register)"),
    ("blessed", "blessed -- SHOULD reach for it for a matching task shape"),
    ("mandated", "mandated -- MUST reach for it for a matching task shape, countersigned"),
    ("forbidden", "forbidden -- MUST NOT reach for it for a matching task shape"),
)
_MAKESPAN_TIER_VALUES = {v for v, _ in MAKESPAN_TIER_CHOICES}

# Reserved principal names: the three every --new-world birth already registers through its own
# s40 ceremony (bootstrap/new-project.sh), plus the write-boundary tool principal s43 registers.
# A `principal_set` row naming one of these would either silently collide with, or (s40's own
# double-registration refusal) loudly duplicate, an identity the birth sequence itself already
# owns -- refused HERE, at the manifest's own boundary, with a message that names the reason,
# rather than surfacing as a bare `led register-principal` exit-1 the operator has to decode.
RESERVED_PRINCIPAL_NAMES = frozenset({"author", "reviewer", "commissioner", "write-boundary"})

FEATURES_FORMAT = 1


def _principal_set_field() -> ListField:
    class_opts = tuple((v, v) for v, _ in content.PA_CLASS_CHOICES)
    class_help = {v: full for v, full in content.PA_CLASS_CHOICES}
    return ListField(
        name="principal_set", label="Principal to pre-register at scaffold time",
        item_fields=(TextField(name="name", label="Principal name"),
                     ChoiceField(name="agent_class", label="Class", options=class_opts,
                                 option_help=class_help),
                     TextField(name="purpose", label="Stated purpose")),
        summarize=lambda r: f"{r['name']} ({r['agent_class']}): {r['purpose']}",
        help=("Registered by new-project.sh itself, through the just-written 'led' shim, "
              "immediately after birth -- --new-world mode only. The interactive "
              "'Principals & authority' screen remains available afterward for anything not "
              "declared here (competences, relations, charters)."))


def fields(state: dict) -> tuple:
    return (
        ConfirmField(name="portable_adrs", label="Include the portable ADR subset (LAW section, "
                     "design/MAINT-ADR-PORTABILITY-SPEC.md)?", default=True),
        ConfirmField(name="vendored_skills", label="Vendor bootstrap/templates/claude-skills/ "
                     "into .claude/skills/?", default=True),
        ConfirmField(name="panel_extension", label="Wire the ledger-panel SPA in (local git "
                     "clone of tools/autoharn-panel into <dest>/panel)?", default=False),
        ChoiceField(name="makespan_tier", label="makespan-scheduler RESOURCES tier",
                    options=MAKESPAN_TIER_CHOICES, default="off"),
        _principal_set_field(),
    )


def _validate_principal_set(rows: list) -> "str | None":
    seen: set[str] = set()
    for row in rows:
        name = (row.get("name") or "").strip()
        if not name:
            return "principal_set: every row needs a non-empty name"
        if name in RESERVED_PRINCIPAL_NAMES:
            return (f"principal_set: '{name}' is reserved -- registered automatically by every "
                     f"--new-world birth's own s40/s43 ceremony; do not re-declare it here")
        if name in seen:
            return f"principal_set: '{name}' is declared more than once"
        seen.add(name)
        if row.get("agent_class") not in {v for v, _ in content.PA_CLASS_CHOICES}:
            return f"principal_set: '{name}' has an unrecognized agent_class {row.get('agent_class')!r}"
    return None


def _resolved_manifest(answers: dict) -> dict:
    """The dict this manifest's own bytes are (schema keys, JSON-ready) -- ONE HOME (ADR-0012
    P1) for the shape both `submit` (staging-file write) and `config_seam.capture_resolved_config`
    (world-config.toml self-save) need, so the two never drift into two independently-typed
    renderings of the same five decisions."""
    return {
        "features_format": FEATURES_FORMAT,
        "portable_adrs": bool(answers["portable_adrs"]),
        "vendored_skills": bool(answers["vendored_skills"]),
        "panel_extension": bool(answers["panel_extension"]),
        "makespan_scheduler_tier": answers["makespan_tier"],
        "principal_set": [dict(r) for r in answers["principal_set"]],
    }


def config_seam_answers(g) -> dict:
    """--from-config's own per-section answers dict (`config_seam.answers_for_from_config` calls
    this rather than re-deriving the same {key: default} shape a second time, ADR-0012 P1)."""
    return {
        "portable_adrs": bool(g("features.portable_adrs", True)),
        "vendored_skills": bool(g("features.vendored_skills", True)),
        "panel_extension": bool(g("features.panel_extension", False)),
        "makespan_tier": str(g("features.makespan_tier", "off")),
        "principal_set": list(g("features.principal_set", []) or []),
    }


def config_seam_capture(manifest: "dict | None") -> dict:
    """world-config.toml's own dotted-key capture of a resolved manifest (`config_seam.
    capture_resolved_config` calls this rather than re-deriving `_resolved_manifest`'s field
    mapping a second time) -- `{}` if this section was never reached this run."""
    if manifest is None:
        return {}
    return {
        "features.portable_adrs": bool(manifest.get("portable_adrs", True)),
        "features.vendored_skills": bool(manifest.get("vendored_skills", True)),
        "features.panel_extension": bool(manifest.get("panel_extension", False)),
        "features.makespan_tier": str(manifest.get("makespan_scheduler_tier", "off")),
        "features.principal_set": list(manifest.get("principal_set", [])),
    }


def submit(state: dict, answers: dict) -> SectionResult:
    cl = state["_checklist"]
    if answers["makespan_tier"] not in _MAKESPAN_TIER_VALUES:
        return SectionResult(ok=False, errors={
            "makespan_tier": f"must be one of {sorted(_MAKESPAN_TIER_VALUES)}"})
    problem = _validate_principal_set(answers["principal_set"])
    if problem:
        return SectionResult(ok=False, errors={"principal_set": problem})

    manifest = _resolved_manifest(answers)
    dry_run = state.get("dry_run", False)
    # Staged BEFORE birth ever runs (this section sits ahead of Fork/target + Birth in
    # tools/setup_tui/steps.py's SECTIONS registry order -- the same registry order the commit
    # sweep executes in, steps.py's own module docstring): a destination directory need not
    # exist yet, so this writes to a per-run TEMP path (system temp dir, never the autoharn
    # checkout root -- `runner.start_background`'s own module docstring names exactly this
    # litter hazard for a first draft that defaulted to `cwd`), never `<dest>/features.json`
    # directly (that path is `new-project.sh`'s OWN write, at birth, of the canonical durable
    # record -- writing it here first would be a second, premature copy of a file birth has not
    # run yet to justify). A path already staged earlier THIS session (an operator revisiting
    # this screen before commit) is reused rather than re-minted, so re-visiting the screen
    # does not litter a fresh temp file per visit.
    staging_path = state.get("features_manifest_path")
    if not staging_path:
        if dry_run:
            # No real file under --dry-run (mirrors `runner.start_background`'s own dry-run
            # discipline: nothing is actually created) -- a symbolic path name is enough for the
            # WOULD-DO line and for `birth_submit`'s own argv rendering.
            staging_path = os.path.join(tempfile.gettempdir(),
                                         ".setup-tui-features.<dry-run>.json")
        else:
            fd, staging_path = tempfile.mkstemp(prefix=".setup-tui-features.", suffix=".json")
            os.close(fd)
    content_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    wrote = write_file(staging_path, content_text, dry_run=dry_run)
    lines = [f"{'would stage' if dry_run else 'staged'}: {staging_path}",
             content_text.rstrip()]
    cl.add(_SLUG, "feature manifest staged", ck.WOULD_DO if dry_run else
           (ck.WITNESSED if wrote else ck.REFUSED), staging_path)

    if manifest["makespan_scheduler_tier"] != "off":
        lines.append("makespan-scheduler: DECLARATIVE-ONLY in this build -- new-project.sh "
                      "writes a ready-to-paste 'resource:' declaration template; the sibling-"
                      "checkout + editable venv install itself is NOT automated (named blocker: "
                      "the operator's own venv path is not known at scaffold time, and this "
                      "scaffold makes no network/pip calls).")
    return SectionResult(ok=True, state_updates={
        "features_manifest": manifest,
        "features_manifest_path": staging_path,
    }, info_lines=tuple(lines))


STEP = SectionSpec(
    slug=_SLUG, title="Feature manifest", group="Substrate & target", fields=fields, submit=submit,
    description=("Declarative, hand-editable checkboxes for what this scaffold includes -- "
                  "portable ADRs, vendored skills, the panel extension, a principal set to "
                  "pre-register, and the makespan-scheduler RESOURCES tier. Written to "
                  "features.json (the durable record new-project.sh itself reads); this screen "
                  "is sugar over that file, never a second source of truth for it."))
