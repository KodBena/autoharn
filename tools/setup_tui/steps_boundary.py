#!/usr/bin/env python3
"""tools/setup_tui/steps_boundary.py -- the Boundary step's UI-free core, ported from
`screen_boundary`.

CONFIG-EXTENSION ADDENDUM (work item setup-tui-config-extension, ledger row 685's audit / row 693):
`log_level`, `identity_enforcement` (hub-wide default and its per-deployment override), and the two
SSE tunables (`sse_poll_interval_secs`/`max_sse_clients`) are `boundary-multiplex.toml`'s own
OPTIONAL top-level/per-deployment keys (`serving/boundary_multiplex_config.py`'s own module
docstring names each) -- this step's fields are sugar over the SAME closed vocabulary/bounds that
module already enforces at load time, imported here rather than copied (ADR-0012 P1): the
vocabulary for `log_level` comes from `serving/boundary_diagnostic_log.LEVELS` (ADR-0012 P1,
ledger row 685's audit names this explicitly), the vocabulary/bounds for the rest from
`serving/boundary_multiplex_config.py` itself. Every one of these five fields is written to
`boundary-multiplex.toml` ONLY when the operator's resolved value differs from that module's own
default (`submit`'s own logic below) -- the parser's own absent-means-default contract, preserved
byte-for-byte when every field is left at default (a regression leg checks this)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from tools.configtree import ChoiceField, ConfirmField, SectionResult, SectionSpec, TextField
from tools.setup_tui import boundary_config_values as bcv
from tools.setup_tui import checklist as ck
from tools.setup_tui import destination, feature_facts, governed_files, probes
from tools.setup_tui.idtypes import DestPath, DestPathError, WorldName, WorldNameError
from tools.setup_tui.plan import (BackgroundAct, CallableAct, CommandAct, DaemonSelection,
                                   PlanEntry, WriteAct)

# `serving/` modules import each other by BARE name (`serving/boundary_service.py`'s own module
# docstring names this convention) -- inserting `serving/` itself onto sys.path, once, at import
# time (not a lazy/function-body import; CLAUDE.md's ban is about deferred-to-call-time imports,
# this executes at module load exactly like every other top-of-file import here). Guarded
# (if-not-in-sys.path) to match this file's own cited precedent, `tools/setup_tui/destination.py`'s
# `_FILING` insert -- an unguarded insert would grow sys.path by one duplicate entry per re-import
# of this module (fix round, review row 776, finding 3).
_SERVING = str(Path(__file__).resolve().parents[2] / "serving")
if _SERVING not in sys.path:
    sys.path.insert(0, _SERVING)
import boundary_diagnostic_log  # noqa: E402  (serving/boundary_diagnostic_log.py -- the ONE home for LEVELS/DEFAULT_LEVEL)
import boundary_multiplex_config  # noqa: E402  (serving/boundary_multiplex_config.py -- the ONE home for the identity_enforcement/SSE vocabulary+bounds)

BOUNDARY_PROC_PRODUCES = "boundary-proc"
_SLUG = "boundary"

# ChoiceField vocabularies -- built ONCE from the imported homes above, never a hand-copied literal
# set (ADR-0012 P1; this is the audit's own P1 finding for log_level, extended on principle to the
# sibling identity_enforcement/SSE keys sharing the same "import, don't duplicate" relationship).
_LOG_LEVEL_CHOICES = tuple(
    (lvl, lvl) for lvl in sorted(boundary_diagnostic_log.LEVELS, key=boundary_diagnostic_log.LEVELS.get))
_IDENTITY_ENFORCEMENT_CHOICES = tuple(
    (p, p) for p in sorted(boundary_multiplex_config.IDENTITY_ENFORCEMENT_POSTURES))
# fix round (review row 776, finding 2): the sentinel is now DEFINED at
# `boundary_config_values.IDENTITY_ENFORCEMENT_OVERRIDE_INHERIT` (the one shared public home both
# this module and `config_seam.py` import) -- this module keeps its own short private alias
# (unchanged by name, only by source) since it is used as a field default/choice-tuple member
# below, private to this file's own field declarations.
_IDENTITY_ENFORCEMENT_OVERRIDE_INHERIT = bcv.IDENTITY_ENFORCEMENT_OVERRIDE_INHERIT
_IDENTITY_ENFORCEMENT_OVERRIDE_CHOICES = (
    (_IDENTITY_ENFORCEMENT_OVERRIDE_INHERIT, "inherit -- no override, use the hub-wide default above"),
) + _IDENTITY_ENFORCEMENT_CHOICES


def _validate_sse_poll_interval_secs(raw: str) -> "str | None":
    """Delegates to `boundary_config_values.SsePollIntervalSecs` -- the SAME constructing home
    `submit` below uses to resolve the final value (fix round finding 1: one SSOT, not two
    parallel implementations of the same bound check). This adapter only translates the typed
    home's `ValueError` into the plain string-or-None a `TextField` validator returns for live
    widget feedback."""
    try:
        bcv.SsePollIntervalSecs.parse(raw)
    except ValueError as exc:
        return str(exc)
    return None


def _validate_max_sse_clients(raw: str) -> "str | None":
    """Delegates to `boundary_config_values.MaxSseClients` -- see `_validate_sse_poll_interval_secs`
    above for why this is a thin adapter, not a second implementation."""
    try:
        bcv.MaxSseClients.parse(raw)
    except ValueError as exc:
        return str(exc)
    return None


def fields(state: dict) -> tuple:
    # NO "dest"/"world" fields here (maintainer ruling 2026-07-22, ADR-0019 single-editable-
    # home): the destination directory is owned by Fork/target, the world name by Birth --
    # boundary reads both shared facts straight out of state in `submit` below, never via a
    # second field declaration (a duplicated projection is refused at App construction,
    # `tools.configtree.spec.validate_shared_ownership`).
    #
    # legacy-led-retirement inventory pass (ledger row 1149/1150): the "Configure the boundary
    # service now?" decline gate that stood here is REMOVED -- the boundary is MANDATORY at
    # every birth per the ratified coupling (row 1150) now that legacy-led.tmpl is retired:
    # declining used to fall back to `legacy/led`, now a one-line teaching-refusal stub, never a
    # working CLI -- "decline" would brick the rest of this run's commit. Configuration CHOICES
    # (host/db/port/auto-start-now-vs-later) are unchanged; only the existence gate is gone.
    # BASIS (corrected, retirement review round 1, ledger row 1173): the decision rests on the
    # ratified boundary coupling alone -- ledger row 1150 ("the boundary becomes every world's
    # standing service per the spec's stated coupling") -- plus the plain operational fact stated
    # above: post-retirement, declining now falls through to a one-line refusal stub (legacy/led
    # is no longer a working CLI at all), which bricks the rest of this run's commit. ERRATUM:
    # this comment previously cited "row 1942 (autoharn1's own ledger)" as a DEFECT-FIX WITNESS
    # for Case 14 (runner.resolve_led) supporting this removal. That citation was independently
    # verified FALSE -- autoharn1 row 1942 is autoharn1's OWN succession commission (the
    # maintainer-commissioned rebirth to autoharn2), not a witness of any decline-mode fallback
    # defect. The removal decision above does not need, and never needed, that citation; it
    # stands on row 1150 and the operational fact alone.
    return (
        ConfirmField(name="override", label="Override and proceed WITHOUT a confirmed successful "
                     "birth? (only used if birth was not confirmed)"),
        TextField(name="host", label="Postgres host", default=state.get("pghost", "192.168.122.1"),
                  required=False),
        TextField(name="db", label="Database", default=state.get("db", "toy"), required=False),
        ConfirmField(name="start_now", label="Start the boundary service now (this process)?",
                     default=True),
        ChoiceField(name="log_level", label="Boundary service log level",
                    options=_LOG_LEVEL_CHOICES, default=boundary_diagnostic_log.DEFAULT_LEVEL,
                    help="serving/boundary_diagnostic_log.LEVELS is the ONE home for this "
                         "vocabulary (ADR-0012 P1) -- omitted from boundary-multiplex.toml "
                         "entirely when left at the default."),
        ChoiceField(name="identity_enforcement", label="identity_enforcement (hub-wide default)",
                    options=_IDENTITY_ENFORCEMENT_CHOICES,
                    default=boundary_multiplex_config.DEFAULT_IDENTITY_ENFORCEMENT,
                    help="The anonymous-authority-bearing-write refusal's posture, applied to "
                         "every deployment that does not override it below. Omitted from "
                         "boundary-multiplex.toml entirely when left at the default (grace)."),
        ChoiceField(name="identity_enforcement_override",
                    label="identity_enforcement override for THIS deployment only",
                    options=_IDENTITY_ENFORCEMENT_OVERRIDE_CHOICES,
                    default=_IDENTITY_ENFORCEMENT_OVERRIDE_INHERIT,
                    help="Written into [deployments.{world}] only when set to something other "
                         "than 'inherit' -- absent means this deployment follows the hub-wide "
                         "default above, exactly like every other deployment that carries no "
                         "override of its own."),
        TextField(name="sse_poll_interval_secs", label="SSE poll interval, seconds",
                  default=str(boundary_multiplex_config.DEFAULT_SSE_POLL_INTERVAL_SECS),
                  required=False, validator=_validate_sse_poll_interval_secs,
                  help=f"How often the shared per-deployment head-watcher polls max(id); "
                       f"(0, {boundary_multiplex_config.MAX_SSE_POLL_INTERVAL_SECS}]. Omitted "
                       f"from boundary-multiplex.toml entirely when left at the default."),
        TextField(name="max_sse_clients", label="Max concurrently open SSE clients (hub-wide)",
                  default=str(boundary_multiplex_config.DEFAULT_MAX_SSE_CLIENTS),
                  required=False, validator=_validate_max_sse_clients,
                  help=f"The separate, hub-wide bound on concurrently open GET "
                       f"/d/{{deployment}}/events connections -- NEVER the 24-slot inflight gate; "
                       f"[1, {boundary_multiplex_config.MAX_SSE_CLIENTS_CEILING}]. Omitted from "
                       f"boundary-multiplex.toml entirely when left at the default."),
    )


def submit(state: dict, answers: dict) -> SectionResult:
    cl = state["_checklist"]
    lines = [feature_facts.facts_block(["boundary_service"])]
    if not state.get("birth_ok") and not answers["override"]:
        return SectionResult(ok=False, errors={"override": "birth was not confirmed successful -- "
                                             "check this box to proceed anyway"})
    if not state.get("birth_ok") and answers["override"]:
        cl.add("boundary", "birth gate", ck.WITNESSED, "OVERRIDDEN by operator")

    # "dest"/"world" are Fork/target's and Birth's own owned fields respectively -- read the
    # shared facts directly, never via a field of boundary's own (dropped, see `fields`'s own
    # docstring above).
    try:
        dest_path = DestPath.parse(state.get("dest", ""))
    except DestPathError as exc:
        return SectionResult(ok=False, errors={"": f"destination (set in Fork/target): {exc}"})
    dest = str(dest_path)
    if destination.classify_destination(dest).kind == destination.DestKind.FRESH:
        if not state.get("dest_would_exist"):
            cl.add("boundary", "destination exists", ck.REFUSED, f"'{dest}' not a directory")
            return SectionResult(ok=False, errors={"": "destination (set in Fork/target) does not "
                                                 "exist -- run a birth first"})
        cl.add("boundary", "destination exists", ck.DRY_SKIPPED, f"'{dest}' queued earlier")

    try:
        world_name = WorldName.parse(state.get("world", ""))
    except WorldNameError as exc:
        return SectionResult(ok=False, errors={"": f"world name (set in Birth): {exc}"})
    # `WorldName.__post_init__` (tools/setup_tui/idtypes.py, work item
    # setup-tui-worldname-boundary-allowlist) now enforces the INTERSECTION of the shell/SQL
    # identifier allowlist AND the boundary service's own deployment-slug allowlist -- so `world`
    # below is already safe to splice into `[deployments.{world}]` (this step's own TOML table
    # key) by construction, not by convention. Birth's own entry gate re-parses through this SAME
    # constructor, so a bad name never even reaches this step; the re-parse here is this step's
    # own defense against being driven with a state dict that skipped Birth (e.g. a test harness),
    # not a second copy of the allowlist.
    world = str(world_name)
    host = answers["host"].strip() or state.get("pghost", "192.168.122.1")
    db = answers["db"].strip() or state.get("db", "toy")

    port = probes.free_port()
    boundary_url = f"http://127.0.0.1:{port}"
    lines.append(f"picked free port: {port} ({boundary_url})")

    dep_json_path = os.path.join(dest, "deployment.json")
    dep = {}
    if os.path.isfile(dep_json_path):
        with open(dep_json_path) as f:
            dep = json.load(f)
    schema, kern, role = dep.get("schema", world), dep.get("kern", f"{world}_kernel"), dep.get("role", f"{world}_rw")

    for label, val, checker in (("host", host, probes.valid_hostname), ("database", db, probes.valid_identifier),
                                 ("role", role, probes.valid_identifier), ("schema", schema, probes.valid_identifier),
                                 ("kern", kern, probes.valid_identifier), ("world", world, probes.valid_identifier)):
        if not checker(val):
            cl.add("boundary", "multiplex TOML values validated", ck.REFUSED, f"'{val}' ({label}) invalid")
            return SectionResult(ok=False, errors={"": f"{label} '{val}' fails the interpreter-boundary "
                                                 "allowlist"})

    # CONFIG-EXTENSION ADDENDUM (row 693/685), TYPED CONSTRUCTION (fix round, review row 776,
    # finding 1 -- CLAUDE.md/ledger row 26: "every value construction goes through one SSOT that
    # checks a contract; no bare ints, no bare strs"). Each of the five values is constructed
    # through `boundary_config_values` -- the ONE typed home per value, hit whether or not the
    # answer already passed its own field's inline validator (a blank/whitespace answer skips
    # that validator entirely, `fields.validate_value`'s own "only when non-blank" rule, and must
    # still fall back to the default rather than crash) -- never a second, ad hoc re-derivation
    # of the same contract. `.value`/`.raw` is unwrapped back to a plain scalar only once each
    # value has passed its own gate -- what state/config_seam/the TOML writer below need next.
    # `_typed` is the ONE adapter from a typed home's own ValueError/MultiplexConfigError to this
    # function's own REFUSED-checklist-row + SectionResult shape, instead of five near-identical
    # try/excepts (kept to one line per call so this addendum stays inside ADR-0007's ceiling).
    toml_path = os.path.join(dest, "boundary-multiplex.toml")

    def _typed(field: str, parse_call):
        try:
            return parse_call(), None
        except (ValueError, boundary_multiplex_config.MultiplexConfigError) as exc:
            cl.add("boundary", "multiplex TOML values validated", ck.REFUSED, f"{field}: {exc}")
            return None, SectionResult(ok=False, errors={field: str(exc)})

    log_level_t, refusal = _typed("log_level", lambda: bcv.LogLevel.parse(answers["log_level"]))
    if refusal: return refusal  # noqa: E701 (one-liner, see `_typed`'s own docstring comment above)
    identity_enforcement_t, refusal = _typed("identity_enforcement", lambda: bcv.IdentityEnforcementPosture.parse(
        answers["identity_enforcement"], where="identity_enforcement (hub-wide default)", path=Path(toml_path)))
    if refusal: return refusal  # noqa: E701
    identity_enforcement_override_t, refusal = _typed(
        "identity_enforcement_override",
        lambda: bcv.IdentityEnforcementOverride.parse(answers["identity_enforcement_override"]))
    if refusal: return refusal  # noqa: E701
    sse_raw = answers["sse_poll_interval_secs"].strip() or str(bcv.SsePollIntervalSecs.default().value)
    sse_poll_interval_secs_t, refusal = _typed("sse_poll_interval_secs", lambda: bcv.SsePollIntervalSecs.parse(sse_raw))
    if refusal: return refusal  # noqa: E701
    clients_raw = answers["max_sse_clients"].strip() or str(bcv.MaxSseClients.default().value)
    max_sse_clients_t, refusal = _typed("max_sse_clients", lambda: bcv.MaxSseClients.parse(clients_raw))
    if refusal: return refusal  # noqa: E701

    log_level = log_level_t.value
    identity_enforcement = identity_enforcement_t.value
    identity_enforcement_override = identity_enforcement_override_t.raw
    sse_poll_interval_secs = sse_poll_interval_secs_t.value
    max_sse_clients = max_sse_clients_t.value

    # Absent-means-default (the parser's own contract, `serving/boundary_multiplex_config.py`):
    # a top-level/per-deployment key is written ONLY when it differs from that module's own
    # default -- an all-defaults run emits BYTE-IDENTICAL TOML to before these fields existed.
    # Compared as TYPED VALUES (their generated `__eq__`), not the unwrapped scalar, so a future
    # typed home that adds fields to its contract still compares correctly by construction.
    top_level_lines: list[str] = []
    if log_level_t != bcv.LogLevel.default():
        top_level_lines.append(f'log_level = "{log_level}"')
    if identity_enforcement_t != bcv.IdentityEnforcementPosture.default():
        top_level_lines.append(f'identity_enforcement = "{identity_enforcement}"')
    if sse_poll_interval_secs_t != bcv.SsePollIntervalSecs.default():
        top_level_lines.append(f"sse_poll_interval_secs = {sse_poll_interval_secs}")
    if max_sse_clients_t != bcv.MaxSseClients.default():
        top_level_lines.append(f"max_sse_clients = {max_sse_clients}")

    deployment_lines = [f'pghost = "{host}"', f'pgdatabase = "{db}"', f'pguser = "{role}"',
                         f'pgschema = "{schema}"', f'pgkern = "{kern}"']
    if not identity_enforcement_override_t.inherits:
        deployment_lines.append(f'identity_enforcement = "{identity_enforcement_override}"')

    toml_text = "".join(f"{line}\n" for line in top_level_lines)
    toml_text += f"[deployments.{world}]\n" + "".join(f"{line}\n" for line in deployment_lines)
    lines.append(f"--- queuing write: {toml_path} ---\n{toml_text}")
    plan = state["_plan"]
    plan.append(PlanEntry(screen="boundary", item="multiplex TOML written",
                           lesson="the boundary service's own config file",
                           act=WriteAct(path=toml_path, content=toml_text)))

    argv = [str(state["_repo_root"] / "bootstrap" / "new-project.sh"), dest, "--db", db, "--host", host,
            "--schema", schema, "--kern", kern, "--role", role, "--name", dep.get("name", world),
            "--force", "--boundary-url", boundary_url, "--boundary-deployment", world]
    if state.get("governed_patterns"):
        argv += ["--governed", governed_files.governed_flag_value(state["governed_patterns"])]
    lines.append(f"$ {' '.join(argv)}")
    plan.append(PlanEntry(screen="boundary", item="deployment.json boundary keys written",
                           lesson="classic-mode re-scaffold", act=CommandAct(argv=tuple(argv))))

    preferred_python = os.path.expanduser("~/w/vdc/venvs/generic/bin/python")
    fallback_python = probes.which("python3")
    if os.access(preferred_python, os.X_OK):
        venv_python, interp_reason = preferred_python, f"venv interpreter: {preferred_python}"
    elif fallback_python:
        venv_python, interp_reason = fallback_python, f"venv absent -- using python3 on PATH: {fallback_python}"
    else:
        venv_python, interp_reason = None, f"NEITHER {preferred_python} NOR python3 is on PATH"

    updates = {
        "boundary_url": boundary_url, "boundary_port": port,
        # CONFIG-EXTENSION ADDENDUM (row 693/685): the resolved values, for world-config.toml's
        # own self-save (config_seam.capture_resolved_config) -- ADR-0012 P1, no second
        # re-derivation of what was actually decided this run.
        "boundary_log_level": log_level, "boundary_identity_enforcement": identity_enforcement,
        "boundary_identity_enforcement_override": identity_enforcement_override,
        "boundary_sse_poll_interval_secs": sse_poll_interval_secs,
        "boundary_max_sse_clients": max_sse_clients,
    }
    if answers["start_now"] and venv_python:
        argv2 = [venv_python, "-m", "serving.boundary_service", "--config", toml_path, "--port", str(port)]
        lines.append(f"interpreter: {interp_reason}")
        lines.append(f"$ {' '.join(argv2)}   (background)")
        plan.append(PlanEntry(screen="boundary", item="service started",
                               lesson="starts the boundary service, this process's own child",
                               act=BackgroundAct(argv=tuple(argv2), cwd=str(state["_repo_root"])),
                               produces=BOUNDARY_PROC_PRODUCES))

        # design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part C completion (row 1158/1159, item 2 --
        # FAILURE HONESTY): the BackgroundAct above reports ok=True the instant Popen() succeeds
        # (commit_executor.py's own `_run_entry` -- forking/exec'ing is not the same fact as "the
        # service actually came up"), so a genuinely failed start (the concrete case this closes:
        # the picked port is ALREADY occupied -- uvicorn's own bind refuses and the child exits
        # within milliseconds) would otherwise sail through as a false accept, and every act
        # queued AFTER it -- principals-authority, signed-genesis, hydration -- would then run
        # against a boundary that is not there: a half-born world, no different from the
        # silent-fallback class this whole re-sequencing exists to foreclose. This CallableAct
        # (the one generic commit-time-effect escape hatch, `plan.py`'s own docstring) polls the
        # SAME health URL for up to 10s (`probes.wait_for_health`) and is the ACT that actually
        # fails the commit -- REFUSED, with the last probe's own detail as teaching -- when the
        # service never answers; per-act atomicity means NOTHING queued after this entry ever
        # runs (`commit_executor.execute`'s own "stops at the FIRST entry whose act does not
        # succeed"). No silent fallback to legacy/led exists to reach for either way -- the
        # operator's only lawful next step is fixing the port/env and re-running the commit
        # (which resumes exactly here, the journal's own resume-from-PENDING contract).
        def _boundary_health_gate() -> tuple[bool, str]:
            ok, last = probes.wait_for_health(f"{boundary_url}/d/{world}/health", timeout_s=10.0)
            if ok:
                return True, f"boundary healthy: {last}"
            return False, (
                f"REFUSED -- the boundary service never answered {boundary_url}/d/{world}/health "
                f"within 10s (last probe: {last}). The most likely cause is the port ({port}) "
                f"already being occupied by another process -- check with `ss -ltnp | grep "
                f"{port}` (or lsof -i :{port}), free the port or re-run this section to pick a "
                f"different one, then retry the commit. NOTHING after this act ran (per-act "
                f"atomicity); principals-authority/signed-genesis/hydration never touched a "
                f"half-born world.")
        plan.append(PlanEntry(screen="boundary", item="service health gate",
                               lesson="confirms the boundary actually came up before any "
                                      "ledger-writing act trusts it",
                               act=CallableAct(fn=_boundary_health_gate,
                                                label=f"poll {boundary_url}/d/{world}/health")))
        updates["boundary_will_start"] = True
        updates["boundary_world"] = world
    else:
        if answers["start_now"] and not venv_python:
            cl.add("boundary", "service auto-start", ck.REFUSED, interp_reason)
        unit_text = (f"[Unit]\nDescription=autoharn boundary service ({world})\n\n[Service]\n"
                     f"ExecStart={venv_python or preferred_python} -m serving.boundary_service "
                     f"--config {toml_path}\nWorkingDirectory={state['_repo_root']}\n"
                     f"Restart=on-failure\n\n[Install]\nWantedBy=multi-user.target\n")
        lines.append(f"--- PREPARED: systemd unit text (operator installs/starts) ---\n{unit_text}")
        plan.add_daemon(DaemonSelection(
            name="boundary", argv=(venv_python or preferred_python, "-m", "serving.boundary_service",
                                    "--config", toml_path, "--port", str(port)),
            cwd=str(state["_repo_root"]), env_notes="boundary-multiplex.toml's own deployment section",
            health_probe=f"http:{boundary_url}/d/{world}/health", prerequisite=(venv_python or preferred_python)))
        cl.add("boundary", "service unit text", ck.INSTRUCTED, "systemd unit, not started")

    # NOTE: no `updates["dest"] = dest` here -- "dest" is Fork/target's own owned fact, already
    # in state; re-writing the same value here would be a second writer of one truth (ADR-0012
    # P1), even though harmless today (same value) -- removed on principle.
    return SectionResult(ok=True, state_updates=updates, info_lines=tuple(lines))


def _blocked_needs_dest(state: dict) -> "str | None":
    """The boundary service is started FROM the born world's own destination, under its own
    world name -- nothing to start until Fork/target has recorded a destination AND Birth has
    recorded a world name (both are now read directly from shared state, boundary's own "dest"/
    "world" fields having been dropped in favor of their single owning section)."""
    missing = []
    if not state.get("dest"):
        missing.append("Fork/target (a destination directory)")
    if not state.get("world"):
        missing.append("Birth (a world name)")
    if not missing:
        return None
    return f"requires: {' and '.join(missing)} to be set first"


STEP = SectionSpec(slug="boundary", title="Boundary", group="Runtime", fields=fields,
                    submit=submit, blocked=_blocked_needs_dest,
                    description=feature_facts.fact("boundary_service").elements())
