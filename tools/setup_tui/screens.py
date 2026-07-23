#!/usr/bin/env python3
"""tools/setup_tui/screens.py -- the eleven screens, PHASE 2 (design/FABLE-SETUP-TUI-PURE-CORE-
SPEC.md, commission ledger rows 1823 point 2 / 1825 / 1835): every screen is now a PURE DECIDER.
It computes, displays, and collects decisions into THE PLAN (`tools.setup_tui.plan.Plan`) -- it
performs no world-effect. The only inter-screen state is the append-only plan
(`state["plan"]`), read-only probe evidence, and the operator's answers; no screen observes an
effect of a prior screen, because until the ONE commit boundary (the final screen, below) there
are none.

Each screen function still takes `(ui, cl, state)` and returns the same `state` dict, mutated --
`state["plan"]` is the one new, load-bearing entry (`_plan(state)` below is the single accessor).
`cl` (the `Checklist`) is still used for DECISION-TIME facts that are not effects: a REFUSED
validation, an operator SKIP, a live read-only display -- never for a WITNESSED effect row, which
now only exists once the commit boundary has actually run the corresponding plan entry (the final
screen's `_execute_commit` drives that).

DECLARED EXCEPTIONS (spec §2.5, the honest envelope -- named at their sites, not hidden):
  - Every read-only probe (preflight, connection checks, the pg_hba read, `list_principals`/
    `list_commissions` against an ALREADY-EXISTING world, `durable_decisions.list_adrs`) stays
    live -- a rehearsal that fakes its reads is a lie.
  - `screen_rehearsal` is the wizard's P9-rule-4-shaped Workspace: a declared, explicitly-scoped
    effect on a SCRATCH target, performed mid-flow because its evidence informs decisions, with
    witnessed zero-residue teardown. It is the ONE screen function (besides
    `tools/setup_tui/commit_executor.py`) the §2.8 AST purity gate permits to call
    `runner.run_command`/`start_background`/`write_file` directly.
  - The scratch GNUPGHOME `--scripted` witnessing needs (`signed_genesis.
    prepare_scratch_gnupghome_act`) is NOT a decision-time exception any more (FINDING-2 fix,
    fresh-context review of b565db1): it is its own plan entry (a `plan.CallableAct`, the one act
    type that is neither of the three runner choke points), executed only at commit time, exactly
    like every other effect in this flow -- the decision phase stays genuinely effect-free.

THE THREE RE-DERIVED DISPLAYS (spec §2.7): `screen_principals_authority` shows the scaffold's
static contractual base (`principals_authority.SCAFFOLD_BASE_PRINCIPALS`) rather than a live
world's views, UNLESS `dest` already exists on disk (an out-of-sequence entry against an
already-born world, where the live read is a genuine read of something real); the genesis-row
designation in `screen_signed_genesis` is a symbolic `Hole` until commit when a NEW commission is
written; the boundary health probe in `_execute_commit` runs at commit, post-start.

`--dry-run`: a dry run is the decision phase WITHOUT the commit act (spec §2.4) -- every screen
below builds the SAME plan entries it would under a live run; `_execute_commit` (the final screen)
renders the plan and, under `--dry-run`, stops there (WOULD-DO rows only, no
`commit_executor.execute` call at all) rather than committing. The choke-point `dry_run` plumbing
in `runner.py` remains as defense-in-depth (unreachable in the normal pure-core path, since no
screen but `screen_rehearsal` calls a choke point directly any more) -- `screen_rehearsal` itself
still threads `dry_run` through its own direct calls exactly as before, per its declared-exception
status.
"""
from __future__ import annotations

import importlib.util
import json
import os
import time
from pathlib import Path

from tools.setup_tui import checklist as ck
from tools.setup_tui import commit_executor as CE
from tools.setup_tui import config_seam
from tools.setup_tui import daemon_scaffold
from tools.setup_tui import destination
from tools.setup_tui import durable_decisions, feature_facts, governed_files, pghba, probes
from tools.setup_tui import principals_authority, signed_genesis
from tools.setup_tui.content import screens_data as SD
from tools.setup_tui.elements import Heading, Note, Paragraph, Rule, Table
from tools.setup_tui.plan import (BackgroundAct, CallableAct, CommandAct, DaemonSelection, Plan,
                                   PlanEntry, WriteAct)
from tools.setup_tui.runner import legacy_led_path, resolve_led, run_command, served_led_path
from tools.setup_tui.ui import ScriptedUi

REPO_ROOT = Path(__file__).resolve().parents[2]

PREFLIGHT_BINARIES = ("idris2", "clingo", "python3", "psql")

SUBSTRATE_CHOICES = [
    ("existing", "existing-db path (zero manual steps, the omega-lab shape)"),
    ("dedicated", "dedicated-db path (generates a confined pg_hba block)"),
]


def _plan(state: dict) -> Plan:
    """THE PLAN's one accessor (ADR-0012 P1) -- `state.setdefault` so any screen, entered first
    via `--start-at`, gets the same empty `Plan` rather than each screen re-deriving its own."""
    return state.setdefault("plan", Plan())


def _show_facts(ui, *keys: str) -> None:
    ui.emit(Paragraph(feature_facts.facts_block(list(keys))))


def _dry_skip_or(ui, cl, state, screen: str, item: str, verify) -> None:
    """A PREPARED block's post-keypress verification gate -- unchanged from Phase 1: under
    `state["dry_run"]`, `verify` is never called (there is no live act behind a PREPARED block to
    verify, dry run or not -- a PREPARED block was never a plan entry, it stays an operator
    copy-paste act in both modes) and a single `ck.DRY_SKIPPED` row is recorded instead."""
    if state.get("dry_run"):
        cl.add(screen, item, ck.DRY_SKIPPED, "dry-run: prepared act not taken, not verified")
        return
    verify()


# ---------------------------------------------------------------------------------------------
# Preflight -- entirely read-only; builds no plan entries.
# ---------------------------------------------------------------------------------------------

def screen_preflight(ui, cl, state):
    ui.emit(Heading(screen_banner("preflight")))
    if ui.confirm("Run preflight checks?", default=True) is False:
        cl.add("preflight", "all checks", ck.SKIPPED, skip_detail("preflight"))
        return state

    # repo commit / submodules populated -- read-only (probes.py, PHASE-2: moved off
    # runner.run_command so this screen holds no direct choke-point call at all).
    ui.emit(Paragraph(f"$ git -C {REPO_ROOT} rev-parse HEAD"))
    ok, out = probes.git_head_commit(str(REPO_ROOT))
    if ok:
        ui.emit(Paragraph(f"  repo commit: GREEN ({out})"))
        cl.add("preflight", "repo commit", ck.WITNESSED, out)
    else:
        ui.emit(Paragraph("  repo commit: RED -- not a git checkout?"))
        cl.add("preflight", "repo commit", ck.WITNESSED, "RED: git rev-parse HEAD failed")

    ui.emit(Paragraph(f"$ git -C {REPO_ROOT} submodule status"))
    sub_ok, sub_out = probes.git_submodule_status(str(REPO_ROOT))
    dash_lines = [ln for ln in sub_out.splitlines() if ln.strip().startswith("-")]
    if sub_ok and not dash_lines:
        ui.emit(Paragraph("  submodules populated: GREEN"))
        cl.add("preflight", "submodules populated", ck.WITNESSED, "no '-' prefixed entries")
    else:
        ui.emit(Paragraph("  submodules populated: RED"))
        ui.emit(Paragraph("    fix: git -C <repo> submodule update --init --recursive"))
        cl.add("preflight", "submodules populated", ck.WITNESSED,
               f"RED: {len(dash_lines)} uninitialized submodule(s)")

    for name in PREFLIGHT_BINARIES:
        _show_facts(ui, f"preflight_{name}")
        path = probes.which(name)
        if path:
            ui.emit(Paragraph(f"  {name}: GREEN ({path})"))
            cl.add("preflight", f"{name} found", ck.WITNESSED, path)
        elif name == "clingo":
            ui.emit(Paragraph(f"  {name}: not found on PATH (non-fatal -- the engine differential proofs "
                   f"and ./judge need it, but this does not block setup)"))
            cl.add("preflight", f"{name} found", ck.WITNESSED,
                   "not on PATH (non-fatal, matches bootstrap/bootstrap.sh's own posture)")
        elif name == "idris2":
            ui.emit(Paragraph(f"  {name}: not found on PATH (non-fatal -- it backs autoharn's own "
                   f"categorical-kernel-model freshness gate, gates/idris_model_freshness.py; "
                   f"a downstream project built from this scaffold does not need it, and this "
                   f"does not block setup)"))
            cl.add("preflight", f"{name} found", ck.WITNESSED,
                   "not on PATH (non-fatal -- house discipline for autoharn's own repo only, "
                   "not required by a scaffolded downstream project)")
        else:
            ui.emit(Paragraph(f"  {name}: RED -- not found on PATH"))
            fix = {
                "python3": "install Python 3 and ensure it is on PATH",
                "psql": "install the postgresql-client package and ensure `psql` is on PATH",
            }[name]
            ui.emit(Paragraph(f"    fix: {fix}"))
            cl.add("preflight", f"{name} found", ck.WITNESSED, f"RED: not on PATH -- {fix}")

    host = os.environ.get("HARNESS_PGHOST") or os.environ.get("EPISTEMIC_PGHOST")
    if not host:
        ui.emit(Paragraph("  HARNESS_PGHOST: RED -- not set"))
        ui.emit(Paragraph("    fix: export HARNESS_PGHOST=<your postgres host> (or EPISTEMIC_PGHOST)"))
        cl.add("preflight", "HARNESS_PGHOST reachable", ck.WITNESSED,
               "RED: HARNESS_PGHOST/EPISTEMIC_PGHOST unset")
    else:
        ok2, detail = probes.pg_reachable(host)
        if ok2:
            ui.emit(Paragraph(f"  HARNESS_PGHOST ({host}): GREEN -- {detail or 'reachable'}"))
            cl.add("preflight", "HARNESS_PGHOST reachable", ck.WITNESSED, f"{host}: {detail}")
        else:
            ui.emit(Paragraph(f"  HARNESS_PGHOST ({host}): RED -- {detail}"))
            ui.emit(Paragraph(f"    fix: confirm postgres is running and reachable at {host}, or set "
                   f"HARNESS_PGHOST to the correct host"))
            cl.add("preflight", "HARNESS_PGHOST reachable", ck.WITNESSED, f"RED: {detail}")
        state["pghost"] = host

    for name in ("textual", "urwid"):
        _show_facts(ui, f"ui_backend_{name}")
        available = importlib.util.find_spec(name) is not None
        if name == "textual":
            note = ("this run's interactive face" if available else
                    "not this run's face -- the numbered-menu fallback is used, with the "
                    "one-line teaching this build's own startup already gave (or --plain, if "
                    "the operator chose it explicitly)")
        else:
            note = "informational only -- this package never adopted urwid as a backend"
        ui.emit(Paragraph(f"  {name}: {'available' if available else 'not installed'} ({note})"))
        cl.add("preflight", f"{name} available", ck.WITNESSED,
               "available" if available else "not installed")
    return state


# ---------------------------------------------------------------------------------------------
# Substrate -- no runner-choke-point call sites (unchanged from Phase 1: the dedicated-db path
# only ever DISPLAYS PREPARED blocks for the operator to apply by hand on the cluster host; it
# never itself calls run_command/write_file/start_background). Builds no plan entries.
# ---------------------------------------------------------------------------------------------

def screen_substrate(ui, cl, state):
    ui.emit(Heading(screen_banner("substrate")))
    if not ui.confirm("Configure substrate now?", default=True):
        cl.add("substrate", "path chosen", ck.SKIPPED, skip_detail("substrate"))
        return state

    _show_facts(ui, "substrate_existing", "substrate_dedicated")
    path = ui.ask_choice("Which substrate path?", SUBSTRATE_CHOICES)
    state["substrate_path"] = path
    host = state.get("pghost") or ui.ask_text("Postgres host", default="192.168.122.1")
    state["pghost"] = host

    if path == "existing":
        db = ui.ask_text("Existing database name", default="toy")
        state["db"] = db
        ok, detail = probes.pg_reachable(host)
        status = ck.WITNESSED if ok else ck.REFUSED
        ui.emit(Paragraph(f"  reachability probe: {'GREEN' if ok else 'RED'} -- {detail}"))
        cl.add("substrate", f"existing-db {db}@{host} reachable", status,
               f"{'GREEN' if ok else 'RED'}: {detail}")
        return state

    db = ui.ask_text("New (dedicated) database name")
    role = ui.ask_text("New (dedicated) role name")
    for _label, _val in (("database name", db), ("role name", role)):
        if not probes.valid_identifier(_val):
            ui.emit(Note(f"  REFUSED: {_label} '{_val}' contains characters outside [A-Za-z0-9_] -- "
                   f"refusing to splice it into pg_hba/SQL text (law/adr/0012's interpreter-"
                   f"boundary rule). Nothing generated.", tone="refusal"))
            cl.add("substrate", "dedicated db/role name validated", ck.REFUSED,
                   f"'{_val}' ({_label}) not in [A-Za-z0-9_]+")
            return state
    subnets = ui.ask_text("Subnets to trust (comma-separated CIDR)",
                           default="192.168.122.68/32,192.168.122.1/32")
    subnet_list = [s.strip() for s in subnets.split(",") if s.strip()]

    for _subnet in subnet_list:
        if not probes.valid_subnet(_subnet):
            ui.emit(Note(f"  REFUSED: subnet '{_subnet}' is not a valid CIDR/host token -- refusing "
                   f"to splice it into the pg_hba block (law/adr/0012's interpreter-boundary "
                   f"rule). Nothing generated.", tone="refusal"))
            cl.add("substrate", "dedicated subnets validated", ck.REFUSED,
                   f"'{_subnet}' not a valid CIDR (digits/dots/IPv6 hex+colons, one slash + "
                   f"prefix length, parsed by ipaddress.ip_network)")
            return state

    state["db"] = db
    state["dedicated_role"] = role

    try:
        block, disclosure = pghba.build_prepared_block(host, db, role, subnet_list,
                                                         probe_db="toy")
    except pghba.PgHbaReadError as exc:
        ui.emit(Paragraph(f"  could not read the live pg_hba.conf: {exc}"))
        cl.add("substrate", "pg_hba block (dedicated)", ck.WITNESSED, f"REFUSED-READ: {exc}")
        return state
    except pghba.PgHbaValidationError as exc:
        ui.emit(Note(f"  REFUSED: {exc}", tone="refusal"))
        cl.add("substrate", "pg_hba block (dedicated)", ck.REFUSED, f"REFUSED: {exc}")
        return state

    ui.emit(Paragraph("  " + disclosure.replace("\n", "\n  ")))
    ui.emit(Rule())
    ui.emit(Paragraph("  --- PREPARED: pg_hba.conf block (operator applies, on the cluster host) ---"))
    for line in block.splitlines():
        ui.emit(Paragraph(f"  {line}"))
    ui.emit(Paragraph("  --- end block ---"))
    ui.emit(Rule())
    createdb_cmd = f"CREATE ROLE {role} LOGIN; CREATE DATABASE {db} OWNER {role};"
    ui.emit(Paragraph("  --- PREPARED: createdb/reload block (operator applies, on the cluster host) ---"))
    ui.emit(Paragraph(f"  psql -h {host} -c \"{createdb_cmd}\""))
    ui.emit(Paragraph(f"  # insert the pg_hba block above into pg_hba.conf, then:"))
    ui.emit(Paragraph(f"  psql -h {host} -c \"SELECT pg_reload_conf();\""))
    ui.emit(Paragraph("  what you should see: CREATE ROLE / CREATE DATABASE / one-row 't' from reload"))
    ui.emit(Paragraph("  --- end block ---"))
    # STATUS-SPLIT (design/FABLE-SETUP-TUI-CHECKLIST-SPLIT-SPEC.md §2): ck.INSTRUCTED, not
    # ck.PREPARED -- these two blocks are generated TEXT the operator is shown to run by hand on
    # the cluster host; nothing about the WORLD's state (a file present, a role/db already
    # existing) is confirmed here, so the narrowed PREPARED (which requires exactly that, named
    # in its own detail) does not apply. This is the ORIGINAL PREPARED's honest meaning.
    cl.add("substrate", "pg_hba block generated", ck.INSTRUCTED,
           f"db={db} role={role} subnets={subnet_list}")
    cl.add("substrate", "createdb/reload block", ck.INSTRUCTED, f"db={db} host={host}")

    def _verify_dedicated() -> None:
        ui.pause(f"Apply the two blocks above on {host}, then press enter to verify: ")
        ok, detail = probes.pg_connect(host, db, role=role)
        if ok:
            ui.emit(Paragraph(f"  post-keypress verification probe: GREEN -- {detail}"))
            cl.add("substrate", "dedicated-db connection verified", ck.WITNESSED, detail)
            state["dedicated_verified"] = True
        else:
            ui.emit(Paragraph(f"  post-keypress verification probe: RED -- {detail}"))
            ui.emit(Note("  REFUSED to advance: the connection probe did not succeed. This is the "
                   "honesty-rule-2 gate -- pressing enter is not enough, the effect must be "
                   "real.", tone="refusal"))
            cl.add("substrate", "dedicated-db connection verified", ck.WITNESSED,
                   f"RED (refused to advance): {detail}")
            state["dedicated_verified"] = False

    _dry_skip_or(ui, cl, state, "substrate", "dedicated-db connection verified", _verify_dedicated)
    return state


# ---------------------------------------------------------------------------------------------
# Fork/target -- PHASE 2: the fork-copy (`cp -a`) and the CLAUDE.md-preservation rename (`mv`)
# used to run directly (`shutil.copytree`/`Path.rename`) at what the printed `$ cp -a`/`$ mv`
# lines CLAIMED was the exact command -- a real gap between the printed argv and the actual
# Python call (`shutil.copytree` is not `cp -a`), closed here as a byproduct of moving these to
# plan entries: the plan literally IS `cp -a`/`mv`, so the printed line and the executed argv are
# now the same text by construction, never merely claimed to be.
# ---------------------------------------------------------------------------------------------

def _governed_files_step(ui, cl, state, dest: str) -> None:
    _show_facts(ui, "fork_target_governed_files")
    ui.emit(Paragraph("  " + governed_files.TEACHING_LINE))
    ui.emit(Paragraph(f"  default pattern set: {governed_files.DEFAULT_PATTERNS}"))
    extend = ui.confirm(SD.CONFIRM_GOVERNED_FILES_EXTEND, default=False)
    if not extend:
        patterns, hostile = governed_files.DEFAULT_PATTERNS, []
        cl.add("fork-target", "governed-files pattern set chosen", ck.WITNESSED,
               f"kept default (operator declined to extend): {patterns}")
    else:
        raw = ui.ask_text("Extensions to add, comma-separated (e.g. .ts,.vue,.html)")
        patterns, hostile = governed_files.build_pattern_set(raw)
        if hostile:
            ui.emit(Note(f"  REFUSED: extension token(s) {hostile} contain characters outside "
                   f"'.' + [A-Za-z0-9] -- refusing to splice into the --governed argv (law/"
                   f"adr/0012's interpreter-boundary rule). Falling back to the default set; "
                   f"nothing recorded beyond it.", tone="refusal"))
            cl.add("fork-target", "governed-files pattern set chosen", ck.REFUSED,
                   f"hostile token(s) {hostile}; reverted to default {patterns}")
        else:
            cl.add("fork-target", "governed-files pattern set chosen", ck.WITNESSED,
                   f"extended: {patterns}")
    state["governed_patterns"] = patterns

    path = governed_files.governed_files_path(dest)
    preview = json.dumps({"patterns": patterns}, indent=2) + "\n"
    ui.emit(Paragraph(f"  --- PREVIEW: {path} (written by new-project.sh --governed at birth, and again "
           f"at any later scaffold re-run this flow performs -- never by this screen directly) "
           f"---"))
    ui.emit(Paragraph("  " + preview.replace("\n", "\n  ")))


def screen_fork_target(ui, cl, state):
    ui.emit(Heading(screen_banner("fork-target")))
    if not ui.confirm("Choose destination now?", default=True):
        cl.add("fork-target", "destination", ck.SKIPPED, skip_detail("fork-target"))
        return state

    mode = ui.ask_choice("Destination kind?", [
        ("fresh", "fresh directory"),
        ("fork", "fork-copy of an existing project"),
    ])
    if mode == "fresh":
        dest = ui.ask_text("Fresh destination directory (will be created)")
        dest_state = destination.classify_destination(dest)
        if dest_state.kind == destination.DestKind.FRESH:
            state["dest"] = dest
            cl.add("fork-target", "destination", ck.WITNESSED, f"fresh dir: {dest}")
            _governed_files_step(ui, cl, state, dest)
            return state
        if dest_state.kind == destination.DestKind.AUTOHARN_COMPLETE:
            ui.emit(Note(f"  REFUSED: '{dest}' is already a complete autoharn world "
                   f"({'; '.join(dest_state.evidence)}) -- re-entry (`--start-at`) reaches an "
                   f"existing world without touching it; a genuine re-birth needs teardown "
                   f"first (bootstrap/teardown-world.sh). Nothing done.", tone="refusal"))
            cl.add("fork-target", "destination", ck.REFUSED,
                   f"REFUSED: '{dest}' is AUTOHARN_COMPLETE")
            return state
        if dest_state.kind == destination.DestKind.AUTOHARN_PARTIAL:
            ui.emit(Note(f"  REFUSED: '{dest}' looks like an INTERRUPTED prior birth "
                   f"({'; '.join(dest_state.evidence)}) -- see the birth screen's own "
                   f"partial-birth teaching (teardown-world.sh, never a bare re-birth) once you "
                   f"reach it. Nothing done here.", tone="refusal"))
            cl.add("fork-target", "destination", ck.REFUSED,
                   f"REFUSED: '{dest}' is AUTOHARN_PARTIAL")
            return state
        # FOREIGN -- the new third mode (spec §3): evidence + an explicit ack, never a flat
        # refusal or a silent merge (the blank world proved the use case real).
        ui.emit(Paragraph(f"  '{dest}' is non-empty and carries no autoharn birth evidence "
               f"({'; '.join(dest_state.evidence)})."))
        if not ui.confirm(SD.CONFIRM_FOREIGN_SCAFFOLD, default=False):
            cl.add("fork-target", "destination", ck.REFUSED,
                   f"REFUSED: '{dest}' is FOREIGN content, not acknowledged")
            return state
        state["dest"] = dest
        state["dest_accept_foreign"] = True
        cl.add("fork-target", "destination", ck.WITNESSED,
               f"FOREIGN content acknowledged: {dest}")
        _governed_files_step(ui, cl, state, dest)
        return state

    src = ui.ask_text("Existing project directory to fork-copy")
    dest = ui.ask_text("Destination directory for the fork-copy")
    src_path = Path(src)
    dest_path = Path(dest)
    if not src_path.is_dir():
        ui.emit(Note(f"  REFUSED: source '{src}' is not a directory -- nothing copied.", tone="refusal"))
        cl.add("fork-target", "fork-copy", ck.REFUSED, f"REFUSED: '{src}' not a directory")
        return state
    dest_state = destination.classify_destination(dest)
    if dest_state.kind != destination.DestKind.FRESH:
        ui.emit(Note(f"  REFUSED: destination '{dest}' already exists ({dest_state.kind.value}: "
               f"{'; '.join(dest_state.evidence)}) -- `cp -a` into an occupied directory nests "
               f"the copy rather than creating it, so this mode stays fresh-only. Nothing copied.", tone="refusal"))
        cl.add("fork-target", "fork-copy", ck.REFUSED,
               f"REFUSED: '{dest}' is {dest_state.kind.value}")
        return state

    ui.emit(Paragraph(f"  $ cp -a {src} {dest}"))
    _plan(state).append(PlanEntry(
        screen="fork-target", item="fork-copy", lesson="directory tree copy (cp -a)",
        act=CommandAct(argv=("cp", "-a", src, dest)),
    ))
    # `dest_would_exist` -- read by screen_boundary/screen_hydration/etc.'s out-of-sequence
    # precondition checks: under the pure-core flow this fork-copy is now ALWAYS a deferred act
    # (never real by decision time), so this flag means "queued in THIS session's plan", the same
    # meaning the pre-Phase-2 code gave it under --dry-run specifically.
    state["dest_would_exist"] = True

    would_preserve = (src_path / "CLAUDE.md").is_file()
    dest_claude = dest_path / "CLAUDE.md"
    dest_project_claude = dest_path / "CLAUDE.project.md"
    if would_preserve:
        ui.emit(Paragraph(f"  $ mv {dest_claude} {dest_project_claude}"))
        _plan(state).append(PlanEntry(
            screen="fork-target", item="CLAUDE.md preserved",
            lesson="rename to CLAUDE.project.md before the scaffold write (the omega-lab move)",
            act=CommandAct(argv=("mv", str(dest_claude), str(dest_project_claude))),
        ))
    else:
        cl.add("fork-target", "CLAUDE.md preserved", ck.SKIPPED,
               "fork source had no CLAUDE.md to preserve")

    state["dest"] = str(dest_path)
    _governed_files_step(ui, cl, state, str(dest_path))
    return state


# ---------------------------------------------------------------------------------------------
# Rehearsal -- THE DECLARED EXCEPTION (spec §2.5/§3): a live effect on a SCRATCH target, mid-flow,
# with witnessed zero-residue teardown. Unchanged from Phase 1 -- this is the one screen function
# the §2.8 AST purity gate permits to call runner.run_command directly.
# ---------------------------------------------------------------------------------------------

def _new_project_argv(dest, world, db, host, extra=None):
    argv = [str(REPO_ROOT / "bootstrap" / "new-project.sh"), dest,
            "--new-world", world, "--db", db, "--host", host]
    if extra:
        argv += extra
    return argv


def _teardown_argv(world, db, host, extra=None):
    argv = [str(REPO_ROOT / "bootstrap" / "teardown-world.sh"), world,
            "--db", db, "--host", host]
    if extra:
        argv += extra
    return argv


_ALREADY_EXISTS_REFUSAL = "deployment.json already exists -- refusing to overwrite"


def _render_partial_birth_teaching(ui, cl, world, host, db, dest) -> None:
    """Ledger row 1790 finding 4/5. PHASE 2: birth's own new-project.sh call is now a deferred
    plan entry, so this teaching block can only fire once that entry has actually run -- called
    from `_execute_commit`'s on_result dispatch (below), never from `screen_birth` itself, which
    no longer sees a real result to inspect at decision time."""
    teardown_argv = _teardown_argv(world, db, host, extra=["--dir", dest])
    fmt = {"dest": dest, "world": world, "teardown_argv": " ".join(teardown_argv)}
    for kind, template in SD.PARTIAL_BIRTH_TEACHING:
        text = template.format(**fmt)
        if kind == "rule":
            ui.emit(Rule())
        elif kind == "refusal":
            ui.emit(Note(text, tone="refusal"))
        else:
            ui.emit(Paragraph(text))
    cl.add("birth", "world birth", ck.REFUSED,
           f"REFUSED (new-project.sh's own gate): deployment.json exists at '{dest}' -- likely "
           f"a partial prior birth. Taught: {' '.join(teardown_argv)} (destructive, "
           f"UNEXERCISED against a partial chain -- ledger row 1792), --force re-birth is a "
           f"known kernel-s15-non-idempotency dead end, NOT attempted.")


def screen_rehearsal(ui, cl, state):
    ui.emit(Heading(screen_banner("rehearsal")))
    if not ui.confirm("Run rehearsal (scratch birth + teardown + zero-residue check)?",
                       default=True):
        cl.add("rehearsal", "rehearsal", ck.SKIPPED, skip_detail("rehearsal"))
        state["rehearsal_green"] = False
        return state

    host = state.get("pghost") or ui.ask_text("Postgres host", default="192.168.122.1")
    db = state.get("db") or ui.ask_text("Database", default="toy")
    scratch_world = ui.ask_text("Scratch world name (must match teardown's scratch-safe "
                                 "pattern, e.g. probeworldNNNN)",
                                 default=f"probeworld{int(time.time())}")
    scratch_dir = ui.ask_text("Scratch scaffold directory (throwaway)",
                               default=f"/tmp/setup_tui_rehearsal_{scratch_world}")

    dry_run = state.get("dry_run", False)

    argv = _new_project_argv(scratch_dir, scratch_world, db, host, extra=["--force"])
    res = run_command(argv, dry_run=dry_run)
    birth_ok = res.ok
    cl.add("rehearsal", "scratch birth", ck.status_for(res),
           f"{'exit 0' if birth_ok else f'exit {res.returncode}'}")

    argv = _teardown_argv(scratch_world, db, host, extra=["--dir", scratch_dir])
    res = run_command(argv, stdin_text=f"{scratch_world}\n", dry_run=dry_run)
    teardown_ok = res.ok
    cl.add("rehearsal", "scratch teardown", ck.status_for(res),
           f"{'exit 0' if teardown_ok else f'exit {res.returncode}'}")

    if dry_run:
        cl.add("rehearsal", "scratch scaffold dir removed", ck.WOULD_DO,
               f"{scratch_dir} (would be created by birth, then removed by teardown)")
    else:
        dir_removed = not os.path.isdir(scratch_dir)
        cl.add("rehearsal", "scratch scaffold dir removed",
               ck.WITNESSED if dir_removed else ck.REFUSED,
               scratch_dir if dir_removed else f"STILL PRESENT: {scratch_dir}")

    green = birth_ok and teardown_ok
    ui.emit(Paragraph(f"  rehearsal: {'GREEN' if green else 'RED'}{' (simulated, --dry-run)' if dry_run else ''}"))
    cl.add("rehearsal", "rehearsal overall", ck.WOULD_DO if dry_run else ck.WITNESSED,
           "GREEN" if green else "RED")
    state["rehearsal_green"] = green
    return state


# ---------------------------------------------------------------------------------------------
# Birth -- PHASE 2: the new-project.sh call becomes ONE plan entry, `produces="birth-ran"` (the
# ordering signal `durable_decisions.hydration_claude_md_write_act` and every later screen's
# out-of-sequence dest-exists check depend on). The partial-birth-refusal teaching (module-level
# `_render_partial_birth_teaching`) can no longer fire here -- there is no real result to inspect
# until commit; `_execute_commit`'s dispatch table renders it once the real entry actually runs.
# ---------------------------------------------------------------------------------------------

BIRTH_PRODUCES = "birth-ran"


def screen_birth(ui, cl, state):
    ui.emit(Heading(screen_banner("birth")))
    if not state.get("rehearsal_green"):
        ui.emit(Note("  REFUSED: rehearsal did not report GREEN (or was skipped) -- the real birth "
               "is gated on rehearsal green (spec screen 4: 'the real birth is gated on "
               "rehearsal green, the ratified discipline'). Go back and run a green rehearsal "
               "first, or explicitly override below.", tone="refusal"))
        if not ui.confirm("Override and proceed WITHOUT a green rehearsal? (not recommended)",
                           default=False):
            cl.add("birth", "world birth", ck.SKIPPED, "refused: rehearsal not green")
            return state
        cl.add("birth", "rehearsal gate", ck.WITNESSED, "OVERRIDDEN by operator")

    if not ui.confirm("Run the real birth now?", default=True):
        cl.add("birth", "world birth", ck.SKIPPED, skip_detail("birth"))
        return state

    host = state.get("pghost") or ui.ask_text("Postgres host", default="192.168.122.1")
    db = state.get("db") or ui.ask_text("Database", default="toy")
    world = ui.ask_text("World name")
    dest = state.get("dest") or ui.ask_text("Destination directory")
    name = ui.ask_text("Project name (deployment.json 'name')", default=world)

    # The previously-missing check (spec §3): `state["dest"]` used to be trusted unchecked here.
    # FOREIGN is sanctioned only by fork-target's ack (`dest_accept_foreign`) or a same-session
    # queue (`dest_would_exist`); AUTOHARN_COMPLETE/PARTIAL stay new-project.sh's own gate.
    dest_state = destination.classify_destination(dest)
    if (dest_state.kind == destination.DestKind.FOREIGN
            and not state.get("dest_accept_foreign") and not state.get("dest_would_exist")):
        ui.emit(Note(f"  REFUSED: '{dest}' classifies as FOREIGN content "
               f"({'; '.join(dest_state.evidence)}) -- birth into non-autoharn content needs "
               f"the explicit acknowledgment from fork-target's FOREIGN mode, never queued "
               f"silently. Go back to fork-target, or pick a different destination.", tone="refusal"))
        cl.add("birth", "destination classification", ck.REFUSED,
               f"REFUSED: '{dest}' is FOREIGN, not acknowledged")
        return state

    extra = ["--name", name]
    if state.get("governed_patterns"):
        extra += ["--governed", governed_files.governed_flag_value(state["governed_patterns"])]
    if state.get("dest_accept_foreign"):
        extra += ["--accept-existing-content"]
    argv = _new_project_argv(dest, world, db, host, extra=extra)
    ui.emit(Paragraph(f"  $ {' '.join(argv)}"))
    _plan(state).append(PlanEntry(
        screen="birth", item="world birth",
        lesson="the world's founding scaffold + kernel lineage chain",
        act=CommandAct(argv=tuple(argv)), produces=BIRTH_PRODUCES,
    ))
    state["world"] = world
    state["dest"] = dest
    state["dest_would_exist"] = True
    state["birth_ok"] = True  # decision-time optimism: the commit boundary is the real verdict
    state["birth_produces"] = BIRTH_PRODUCES
    state["birth_world"] = world
    state["birth_host"] = host
    state["birth_db"] = db
    ui.emit(Paragraph("  (the real birth output, and the maintainer's own copy-paste signing line, stream "
           "at commit time -- this screen only queues the act.)"))
    return state


# ---------------------------------------------------------------------------------------------
# Principals & authority -- PHASE 2: every led act queues a plan entry via
# principals_authority.py's `*_act` builders instead of executing. The existing-principals
# display re-derives per spec §2.7: the STATIC scaffold base
# (principals_authority.SCAFFOLD_BASE_PRINCIPALS) when `dest` does not exist yet (the normal
# sequence -- birth has not committed), the real live read when it does (an out-of-sequence
# `--start-at` against an already-born world). The charter trap-resolution (spec WP3) now checks
# BOTH the live read (if any) and a session-local set of names THIS run has already queued a
# registration for -- a principal this same run is about to register would not show up in a live
# read yet.
# ---------------------------------------------------------------------------------------------

def screen_principals_authority(ui, cl, state):
    ui.emit(Heading(screen_banner("principals-authority")))
    _show_facts(ui, "principals_authority")
    if not ui.confirm(SD.CONFIRM_PRINCIPALS_AUTHORITY, default=True):
        cl.add("principals-authority", "screen", ck.SKIPPED,
               "operator skipped (declared-not-silent default=yes) -- legitimate and legible")
        return state

    dest = state.get("dest") or ui.ask_text("Destination directory (the born world)")
    state["dest"] = dest
    plan = _plan(state)
    queued_names: set[str] = state.setdefault("planned_principal_names", set())
    # "boundary" runs BEFORE this screen (Part C, row 1158/1159). legacy-led-retirement
    # inventory pass (row 1149/1150): the decline fallback is RETIRED -- always the served path.
    led = served_led_path(dest)

    dest_state = destination.classify_destination(dest)
    # Out-of-sequence-entry amendment (design/FABLE-SETUP-TUI-SPEC.md 2026-07-19): a not-yet-born
    # `dest` (classifier FRESH) is legitimate ONLY when THIS session already queued a birth for it
    # (`state["dest_would_exist"]`, set by screen_birth/screen_fork_target) -- a genuinely
    # out-of-sequence entry (no birth in this run at all, e.g. `--start-at principals-authority`
    # against a path nobody ever discussed) must refuse legibly here, the same precondition check
    # every other screen in this module already carries. PRODUCT FIX (not a fixture issue): an
    # earlier pass of this rewrite let ANY nonexistent `dest` fall through to the spec §2.7
    # scaffold-base display below, silently treating a true out-of-sequence entry as "not yet
    # born, normal sequence" -- caught live against real Postgres (seen-red/setup-tui-principals-
    # authority WP6a).
    if dest_state.kind == destination.DestKind.FRESH and not state.get("dest_would_exist"):
        ui.emit(Note(f"  REFUSED: destination directory '{dest}' does not exist -- nothing to "
               f"constitute against. Run a birth first (or check the path), then retry this "
               f"screen.", tone="refusal"))
        cl.add("principals-authority", "destination exists", ck.REFUSED, f"'{dest}' not a directory")
        return state
    dest_exists = dest_state.kind != destination.DestKind.FRESH
    if dest_exists:
        if dest_state.kind != destination.DestKind.AUTOHARN_COMPLETE:
            ui.emit(Note(f"  REFUSED: '{dest}' classifies as {dest_state.kind.value} "
                   f"({'; '.join(dest_state.evidence)}) -- this does not look like a complete "
                   f"world this project's own scaffold produced. Nothing done.", tone="refusal"))
            cl.add("principals-authority", "legacy/led present", ck.REFUSED,
                   f"{dest_state.kind.value}: {'; '.join(dest_state.evidence)}")
            return state
        # AUTOHARN_COMPLETE guarantees legacy/led (classifier rule, spec §2) -- the private
        # isfile probe folds into the classification rather than being re-derived (spec §3).
        cl.add("principals-authority", "legacy/led present", ck.WITNESSED,
               legacy_led_path(dest))
        try:
            existing = principals_authority.list_principals(dest)
        except Exception as exc:  # noqa: BLE001 -- a read-only probe; report, never crash the flow
            ui.emit(Note(f"  REFUSED: could not read this world's own principal_standing_current view "
                   f"({exc}) -- lineage-head readability check failed. Nothing offered.", tone="refusal"))
            cl.add("principals-authority", "world readable (lineage-head check)", ck.REFUSED, str(exc))
            return state
        cl.add("principals-authority", "world readable (lineage-head check)", ck.WITNESSED,
               f"{len(existing)} principal(s) found")
        ui.emit(Paragraph(f"  existing principals ({len(existing)}), from {dest}'s own principal_standing_"
               f"current view:"))
        for p in existing:
            ui.emit(Paragraph(f"    id={p['id']:<4} name={p['name']:<14} class={p['agent_class']:<9} "
                   f"standing={p['standing']:<9} purpose={p.get('purpose') or '(none recorded)'}"))
        cl.add("principals-authority", "existing principals shown", ck.WITNESSED,
               ", ".join(f"{p['name']}({p['agent_class']})" for p in existing) or "(none)")
        existing_names = {p["name"] for p in existing}
        s41_available, s41_reason = principals_authority.s41_status(dest)
    else:
        # Spec §2.7: shows the SCAFFOLD's contractual base, not a born world's views (which do
        # not exist yet -- birth is a still-PENDING plan entry in the normal sequence).
        cl.add("principals-authority", "destination exists", ck.DRY_SKIPPED if state.get("dry_run")
               else ck.WITNESSED, f"'{dest}' does not exist yet -- queued for this commit")
        ui.emit(Paragraph(f"  {dest} does not exist yet -- showing the SCAFFOLD's contractual base (every "
               f"world this package births carries exactly these three, unconditionally):"))
        for slug, agent_class, purpose in principals_authority.SCAFFOLD_BASE_PRINCIPALS:
            ui.emit(Paragraph(f"    name={slug:<14} class={agent_class:<9} purpose={purpose}"))
        cl.add("principals-authority", "existing principals shown (scaffold base)", ck.WITNESSED,
               ", ".join(f"{n}({c})" for n, c, _ in principals_authority.SCAFFOLD_BASE_PRINCIPALS))
        existing_names = {n for n, _, _ in principals_authority.SCAFFOLD_BASE_PRINCIPALS}
        # s41 is present at this repo's current lineage head (verified against
        # gates/idris_model_freshness.py's own AS-OF check at build time) -- every world this
        # package births is at that head or later, so a NORMAL-sequence (not-yet-born) world can
        # honestly assume s41 is available, unlike a live check it cannot yet perform.
        s41_available, s41_reason = True, (
            "assumed available -- this repo's current lineage head carries s41 "
            "(kernel/lineage/s41-principal-bindings-and-relations.sql); dest does not exist "
            "yet to check live"
        )

    def _is_known(name: str) -> bool:
        return name in existing_names or name in queued_names

    # --- item 1: register principals ---------------------------------------------------------
    while ui.confirm("Register a principal now?", default=False):
        ui.emit(Paragraph("  " + principals_authority.LESSON_REGISTER))
        name = ui.ask_text("Principal name")
        agent_class = ui.ask_choice("Class (kernel/lineage/s40-schema.sql agent_class CHECK)",
                                     principals_authority.CLASS_CHOICES)
        purpose = ui.ask_text("Stated purpose (mandatory -- AC-2's 'account with a stated "
                               "purpose')")
        act, produces = principals_authority.register_principal_act(dest, name, agent_class, purpose, led=led)
        plan.append(PlanEntry(screen="principals-authority", item=f"register principal '{name}'",
                               lesson=principals_authority.LESSON_REGISTER, act=act,
                               produces=produces))
        queued_names.add(name)
        ui.emit(Paragraph(f"  queued: {act.render()}"))

    # --- item 2: authority bindings (s41 vocabulary, worlds at s41+) -------------------------
    if not s41_available:
        ui.emit(Paragraph(f"  authority bindings section UNAVAILABLE: {s41_reason}"))
        cl.add("principals-authority", "authority bindings (s41)", ck.SKIPPED, s41_reason)
    else:
        cl.add("principals-authority", "authority bindings (s41) available", ck.WITNESSED, s41_reason)
        while ui.confirm("Grant a competence now?", default=False):
            ui.emit(Paragraph("  " + principals_authority.LESSON_COMPETENCE))
            name = ui.ask_text("Principal name (must already be registered)")
            activity = ui.ask_text("Activity")
            band = ui.ask_text("Band")
            basis = ui.ask_text("Basis")
            # `led principal grant-competence` is now a served led.tmpl verb (row 1149) -- same
            # `led` as every other act this screen queues.
            act, produces = principals_authority.grant_competence_act(dest, name, activity, band,
                                                                       basis, led=led)
            plan.append(PlanEntry(screen="principals-authority",
                                   item=f"grant competence '{activity}' to '{name}'",
                                   lesson=principals_authority.LESSON_COMPETENCE, act=act,
                                   produces=produces))
            ui.emit(Paragraph(f"  queued: {act.render()}"))

        while ui.confirm("Add a typed relation now?", default=False):
            ui.emit(Paragraph("  " + principals_authority.LESSON_RELATION))
            subj = ui.ask_text("Subject principal name")
            rel = ui.ask_choice("Relation (kernel/lineage/s41 principal_relation_check CHECK)",
                                 principals_authority.RELATION_CHOICES)
            obj = ui.ask_text("Object principal name")
            # `led principal relate` too (row 1149) -- see grant_competence_act's call above.
            act, produces = principals_authority.relate_act(dest, subj, rel, obj, led=led)
            plan.append(PlanEntry(screen="principals-authority", item=f"relate '{subj}' {rel} '{obj}'",
                                   lesson=principals_authority.LESSON_RELATION, act=act,
                                   produces=produces))
            ui.emit(Paragraph(f"  queued: {act.render()}"))

    # --- item 3: role charters, trap resolved -------------------------------------------------
    while ui.confirm("Register a role charter now?", default=False):
        ui.emit(Paragraph("  " + principals_authority.LESSON_CHARTER))
        role = ui.ask_text("Role name (must be a registered principal)")
        path = ui.ask_text("Charter file path")
        if not _is_known(role):
            ui.emit(Paragraph(f"  '{role}' is not yet a registered principal -- the charter "
                   f"pre-registration trap (spec WP3)."))
            if not ui.confirm(f"Register '{role}' now, in-flow, so the charter can proceed?",
                               default=True):
                manual = (f"{led} register-principal {role} "
                          f"<class> --purpose \"<why>\", then retry this charter")
                ui.emit(Note(f"  REFUSED: charter left unregistered -- manual command: {manual}", tone="refusal"))
                cl.add("principals-authority", f"charter '{role}' (unregistered, declined)",
                       ck.REFUSED, manual)
                continue
            agent_class = ui.ask_choice(f"Class for '{role}'",
                                         principals_authority.CLASS_CHOICES)
            purpose = ui.ask_text(f"Stated purpose for '{role}'")
            reg_act, reg_produces = principals_authority.register_principal_act(
                dest, role, agent_class, purpose, led=led)
            plan.append(PlanEntry(screen="principals-authority",
                                   item=f"register principal '{role}' (in-flow, from charter)",
                                   lesson=principals_authority.LESSON_REGISTER, act=reg_act,
                                   produces=reg_produces))
            queued_names.add(role)
            ui.emit(Paragraph(f"  queued: {reg_act.render()}"))
        act, produces = principals_authority.charter_register_act(dest, role, path, led=led)
        plan.append(PlanEntry(screen="principals-authority", item=f"charter '{role}' <- {path}",
                               lesson=principals_authority.LESSON_CHARTER, act=act,
                               produces=produces))
        ui.emit(Paragraph(f"  queued: {act.render()}"))

    # --- item 4: the workflow on-ramp (pointer, not machinery) --------------------------------
    ui.emit(Paragraph("  " + principals_authority.LESSON_WORKFLOW_POINTER))
    cl.add("principals-authority", "workflow on-ramp pointer", ck.WITNESSED,
           "spec §1 item 4 -- checklist-only note, no mechanism added")
    return state


# ---------------------------------------------------------------------------------------------
# Signed genesis -- PHASE 2: keygen/export/discharge/sign/verify all become plan entries, chained
# through Holes (fingerprint -> export -> keys/ write; fingerprint -> README discharge; a
# just-written commission's row id -> asc-path -> sign -> verify). The genesis-row designation is
# a symbolic Hole until commit when the operator chooses to write a NEW commission (spec §2.7).
# ---------------------------------------------------------------------------------------------

def screen_signed_genesis(ui, cl, state):
    ui.emit(Heading(screen_banner("signed-genesis")))
    _show_facts(ui, "signed_genesis")
    if not ui.confirm(SD.CONFIRM_SIGNED_GENESIS_CEREMONY, default=True):
        cl.add("signed-genesis", "ceremony", ck.SKIPPED,
               "operator skipped (declared-not-silent default=yes, ledger row 1725) -- "
               "legitimate and legible, never nagged again this run")
        return state

    dry_run = state.get("dry_run", False)
    dest = state.get("dest") or ui.ask_text("Destination directory (the born world)")
    state["dest"] = dest
    plan = _plan(state)
    # "boundary" runs BEFORE this screen (Part C, row 1158/1159), so `state["boundary_url"]` is
    # already set. legacy-led-retirement inventory pass (row 1149/1150): the decline fallback is
    # RETIRED (boundary mandatory, legacy-led.tmpl gone) -- always the served path.
    led = served_led_path(dest)

    # spec §3: the private isdir probe replaced by the one Port -- FRESH (absent or empty) reads
    # as "not there yet", exactly what the bare isdir check meant here.
    dest_exists = destination.classify_destination(dest).kind != destination.DestKind.FRESH
    if not dest_exists:
        if state.get("dest_would_exist"):
            cl.add("signed-genesis", "destination exists", ck.DRY_SKIPPED,
                   f"'{dest}' queued earlier in this run -- not independently checkable "
                   f"read-only, recorded honestly rather than faked")
            cl.add("signed-genesis", "world has keys/+verify-commission+legacy/led", ck.DRY_SKIPPED,
                   "trusted along with the destination above -- always scaffolded by birth")
        else:
            ui.emit(Note(f"  REFUSED: destination directory '{dest}' does not exist -- nothing to "
                   f"run the ceremony against. Run a birth first (or check the path), then "
                   f"retry this screen.", tone="refusal"))
            cl.add("signed-genesis", "destination exists", ck.REFUSED, f"'{dest}' not a directory")
            return state
    else:
        keys_dir = os.path.join(dest, "keys")
        verify_bin = os.path.join(dest, "verify-commission")
        legacy_led = legacy_led_path(dest)
        checks = (("keys/", os.path.isdir(keys_dir)), ("verify-commission", os.path.isfile(verify_bin)),
                  ("legacy/led", os.path.isfile(legacy_led)))
        missing = [name for name, ok in checks if not ok]
        if missing:
            ui.emit(Note(f"  REFUSED: {dest} is missing {', '.join(missing)} -- this does not look "
                   f"like a world this project's own scaffold produced. Nothing done.", tone="refusal"))
            cl.add("signed-genesis", "world has keys/+verify-commission+legacy/led", ck.REFUSED,
                   f"missing: {missing}")
            return state
        cl.add("signed-genesis", "world has keys/+verify-commission+legacy/led", ck.WITNESSED, dest)

    gpg_path = probes.which("gpg")
    if not gpg_path:
        ui.emit(Note("  REFUSED: 'gpg' is not on PATH -- the Signed genesis ceremony needs GnuPG "
               "installed (user-guide/USER-GPG-TRUST-LAYER-FAQ.md). Nothing done.", tone="refusal"))
        cl.add("signed-genesis", "gpg present", ck.REFUSED, "gpg not on PATH")
        return state
    cl.add("signed-genesis", "gpg present", ck.WITNESSED, gpg_path)

    # --- designate the genesis commission (spec step 3) --------------------------------------
    # A live read against an EXISTING world only (the declared-exception reads stay live); against
    # a NOT-YET-BORN one (normal sequence) there is nothing to list, and the operator's only real
    # option is to write a new one now -- its row id is a symbolic Hole until commit (spec §2.7).
    commission_id_arg = None  # Arg (str for an existing row, Hole for a just-written one)
    statement = None
    existing = []
    if dest_exists:
        try:
            existing = signed_genesis.list_commissions(dest)
        except Exception as exc:  # noqa: BLE001 -- a read-only probe; report, never crash the flow
            ui.emit(Paragraph(f"  could not list existing commissions ({exc}) -- proceeding as if none exist"))
            existing = []

    if existing:
        latest = existing[-1]
        preview = latest["statement"][:100] + ("..." if len(latest["statement"]) > 100 else "")
        if ui.confirm(f"Use commission {latest['id']} (\"{preview}\") as the genesis "
                      f"commission?", default=True):
            commission_id_arg = str(latest["id"])
            statement = signed_genesis.fetch_commission_statement(dest, latest["id"])
            cl.add("signed-genesis", "genesis commission designated", ck.WITNESSED,
                   f"row {latest['id']} (existing)")

    if commission_id_arg is None:
        ui.emit(Paragraph("  no existing commission designated -- a NEW founding commission will be "
               "written at commit time (FULL mode, via legacy/led) -- its row id is a symbolic "
               "hole until then."))
        statement = ui.ask_text("Founding commission statement (the ask this world exists to "
                                 "carry out)")
        act, produces = signed_genesis.write_commission_act(dest, statement, led=led)
        plan.append(PlanEntry(screen="signed-genesis", item="genesis commission written",
                               lesson="the world's founding commission row", act=act,
                               produces=produces))
        commission_id_arg = signed_genesis.commission_id_hole()
        ui.emit(Paragraph(f"  queued: {act.render()}"))
        cl.add("signed-genesis", "genesis commission designated", ck.WITNESSED,
               f"<row-id of the just-queued write> (symbolic until commit)")

    # --- keygen, ONE fixed shape (HAZARD FIX 2026-07-22 runbook Step 4: unwrap NavigableUi) --
    is_scripted = isinstance(getattr(ui, "_inner", ui), ScriptedUi)
    scratch_setup_produces = None
    if is_scripted:
        ui.emit(Paragraph("  --scripted witnessing: a scratch GNUPGHOME + fixture passphrase is used "
               "(never the operator's own ~/.gnupg) -- prepared as its own plan entry, at "
               "commit time (FINDING-2 fix: this used to be a real filesystem effect at "
               "decision time)."))
        name = ui.ask_text("Key Name-Real (scripted/fixture keygen)",
                            default="AUTOHARN SETUP-TUI FIXTURE KEY -- THROWAWAY")
        email = ui.ask_text("Key Name-Email (scripted/fixture keygen)",
                             default="setup-tui-fixture@example.invalid")
        setup_act, scratch_setup_produces = signed_genesis.prepare_scratch_gnupghome_act(name, email)
        plan.append(PlanEntry(screen="signed-genesis", item="scratch GNUPGHOME prepared",
                               lesson="a throwaway keyring + fixture passphrase for "
                                      "--scripted witnessing, never the operator's own",
                               act=setup_act, produces=scratch_setup_produces))
        ui.emit(Paragraph(f"  queued: {setup_act.render()}"))
        act, produces = signed_genesis.keygen_scripted_act(
            signed_genesis.gnupghome_hole(), signed_genesis.batch_path_hole())
        gnupghome = signed_genesis.gnupghome_hole()
    else:
        name = ui.ask_text("Key Name-Real (your name)")
        email = ui.ask_text("Key Name-Email")
        gnupghome_in = ui.ask_text("GNUPGHOME to use for this key (blank = your default "
                                    "~/.gnupg)", default="")
        gnupghome = gnupghome_in or None
        ui.emit(Paragraph("  gpg will now prompt YOU, interactively, for a passphrase (its own pinentry "
               "prompt -- never captured or scripted by this tool) -- AT COMMIT TIME."))
        act, produces = signed_genesis.keygen_operator_act(name, email, gnupghome)

    plan.append(PlanEntry(screen="signed-genesis", item="keypair generated",
                           lesson="ONE fixed shape (ed25519, sign-only, no expiry), no quiz",
                           act=act, produces=produces))
    ui.emit(Paragraph(f"  queued: {act.render()}"))

    gnupghome_display = ("<scratch GNUPGHOME -- path known only at commit>" if is_scripted
                          else (gnupghome or "your default ~/.gnupg"))
    ui.emit(Paragraph(f"  private key custody: {gnupghome_display} -- this tool never reads, copies, or "
           f"moves it (user-guide/USER-GPG-TRUST-LAYER-FAQ.md §2: print the revocation "
           f"certificate and store it offline)."))
    cl.add("signed-genesis", "private key custody (facts line, not a file)", ck.WITNESSED,
           gnupghome_display)

    # list-secret-keys (fingerprint) -- queued immediately after keygen, same commit.
    list_act, list_produces = signed_genesis.list_secret_key_act(gnupghome)
    plan.append(PlanEntry(screen="signed-genesis", item="fingerprint listed",
                           lesson="the real fingerprint keygen just produced", act=list_act,
                           produces=list_produces))
    ui.emit(Paragraph(f"  queued: {list_act.render()}"))

    # --- key lands where the record expects it (spec step 2) -------------------------------
    filename = signed_genesis.key_filename(name)
    keys_path = os.path.join(dest, "keys", filename)
    export_act, export_produces = signed_genesis.export_public_key_act(gnupghome)
    plan.append(PlanEntry(screen="signed-genesis", item="public key exported",
                           lesson="exports the real key to armored text", act=export_act,
                           produces=export_produces))
    ui.emit(Paragraph(f"  queued: {export_act.render()}"))

    keys_write = signed_genesis.keys_write_act(dest, filename)
    plan.append(PlanEntry(screen="signed-genesis", item="public key written to keys/",
                           lesson=f"discharges keys/{filename}", act=keys_write))
    ui.emit(Paragraph(f"  queued: write {keys_path}"))

    discharge = signed_genesis.discharge_write_act(dest, filename, name, email)
    plan.append(PlanEntry(screen="signed-genesis", item="keys/README.md AWAITING-KEY discharged",
                           lesson="rewrites keys/README.md's AWAITING-KEY section", act=discharge))
    ui.emit(Paragraph(f"  queued: write {os.path.join(dest, 'keys', 'README.md')}"))

    # --- sign the genesis act (spec step 3) -------------------------------------------------
    asc_path = signed_genesis.asc_path_arg(dest, commission_id_arg)
    sign_act, sign_produces = signed_genesis.sign_statement_act(
        gnupghome, statement or "", asc_path, scripted=is_scripted)
    plan.append(PlanEntry(screen="signed-genesis", item="genesis commission signed",
                           lesson="detached signature over the designated commission's statement",
                           act=sign_act, produces=sign_produces))
    ui.emit(Paragraph(f"  queued: {sign_act.render()}"))

    # --- the gate verifies, not the keypress (spec step 4) ----------------------------------
    if dry_run:
        cl.add("signed-genesis", "ceremony gate (verify-commission)", ck.DRY_SKIPPED,
               "cannot verify a signature that was never made (spec §3) -- never a faked "
               "VERIFIED; this entry is never even queued under --dry-run")
    else:
        # GENESIS-GATE HARD-STOP (ledger row 1918): the override is decided HERE, before commit
        # (this act is built at plan time -- there is no "ask after it fails" in a pure-decider
        # flow) -- `state["accept_unverified_genesis"]` is set once, from `--accept-unverified-
        # genesis`, by app.py's own argument parsing, applying uniformly to every backend
        # (`--scripted` included: the flag rides the process argv, not an answers-file line, so
        # a scripted/fixture invocation exercises it by passing the flag alongside `--scripted`).
        accept_unverified = bool(state.get("accept_unverified_genesis", False))
        verify_act, verify_produces = signed_genesis.verify_commission_act(
            dest, commission_id_arg, accept_unverified=accept_unverified)
        plan.append(PlanEntry(screen="signed-genesis", item="ceremony gate (verify-commission)",
                               lesson="requires the VERIFIED verdict before recording WITNESSED "
                                      "(or an explicit --accept-unverified-genesis override)",
                               act=verify_act, produces=verify_produces))
        ui.emit(Paragraph(f"  queued: {verify_act.render()}"))
        if accept_unverified:
            ui.emit(Paragraph("  --accept-unverified-genesis is set for this run: if the gate below does "
                   "not confirm VERIFIED, the ceremony will continue anyway -- eyes open, "
                   "recorded on its own checklist row, never silent."))

    ui.emit(Paragraph("  Signed genesis complete for this run: nothing further in this flow, or in the "
           "world's ongoing operation, demands another signature (spec §1 item 5) -- "
           "subsequent acts ride the ledger's own append-only record; SIGNED remains available "
           "for later commissions as a deliberate act (user-guide/USER-GPG-TRUST-LAYER-FAQ.md "
           "§5), never a nag."))
    cl.add("signed-genesis", "no ongoing signing burden after this screen", ck.WITNESSED,
           "spec §1 item 5 -- checklist-only note, no mechanism added")
    if scratch_setup_produces:
        # FINDING-2: only the PRODUCES KEY is known at decision time -- the real scratch
        # GNUPGHOME path does not exist until the plan entry above actually runs, at commit.
        # _execute_commit resolves this key against the commit's own real bindings/journal
        # AFTER execute() runs (or halts), then tears down whatever was actually created.
        state.setdefault("scratch_gnupghome_produces_keys", []).append(scratch_setup_produces)
    return state


# ---------------------------------------------------------------------------------------------
# Boundary -- PHASE 2: the multiplex TOML write, the deployment.json boundary-keys rewrite, and
# the service start all become plan entries. The health/meta probes are live reads that can only
# happen AFTER the service has actually started -- spec §2.7's "boundary health probe runs at
# commit, post-start" -- so they are not plan entries at all; `_execute_commit`'s dispatch runs
# them right after the "service started" entry's on_result fires.
# ---------------------------------------------------------------------------------------------

BOUNDARY_PROC_PRODUCES = "boundary-proc"


def screen_boundary(ui, cl, state):
    ui.emit(Heading(screen_banner("boundary")))
    _show_facts(ui, "boundary_service")
    if not state.get("birth_ok"):
        ui.emit(Note("  REFUSED: birth did not report success (state['birth_ok'] is not truthy) -- "
               "configuring the boundary service for a world that may not exist would be "
               "building on nothing. Go back and get a successful birth first, or explicitly "
               "override below.", tone="refusal"))
        if not ui.confirm("Override and proceed WITHOUT a confirmed successful birth? "
                           "(not recommended)", default=False):
            cl.add("boundary", "boundary", ck.REFUSED, "refused: birth_ok not truthy")
            return state
        cl.add("boundary", "birth gate", ck.WITNESSED, "OVERRIDDEN by operator")

    # legacy-led-retirement inventory pass, part 3 (ledger row 1149/1150): the "Configure the
    # boundary service now?" decline gate that stood here is REMOVED -- the boundary is
    # MANDATORY at every birth per the ratified coupling (row 1150) now that legacy-led.tmpl is
    # retired: declining used to fall back to `legacy/led`, now a one-line teaching-refusal stub,
    # never a working CLI -- "decline" would brick the rest of this run's commit. Configuration
    # CHOICES (host/db/port/auto-start-now-vs-later) are unchanged; only the existence gate is
    # gone. BASIS (corrected, retirement review round 1, ledger row 1173): the decision rests on
    # the ratified boundary coupling alone -- ledger row 1150 ("the boundary becomes every
    # world's standing service per the spec's stated coupling") -- plus the plain operational
    # fact stated above: post-retirement, declining now falls through to a one-line refusal stub
    # (legacy/led is no longer a working CLI at all), which bricks the rest of this run's commit.
    # ERRATUM: this comment previously cited "row 1942 (autoharn1's own ledger)" as a DEFECT-FIX
    # WITNESS for Case 14 (runner.resolve_led) supporting this removal. That citation was
    # independently verified FALSE -- autoharn1 row 1942 is autoharn1's OWN succession commission
    # (the maintainer-commissioned rebirth to autoharn2), not a witness of any decline-mode
    # fallback defect. The removal decision above does not need, and never needed, that citation;
    # it stands on row 1150 and the operational fact alone. See seen-red/setup-tui-scripted-
    # smoke/run_fixtures.py's own Case 14 docstring for the matching correction.
    dest = state.get("dest") or ui.ask_text("Destination directory")
    state["dest"] = dest
    # spec §3: the private isdir probe replaced by the one Port (same FRESH-means-"not there
    # yet" reading as signed-genesis's own site above).
    if destination.classify_destination(dest).kind == destination.DestKind.FRESH:
        if state.get("dest_would_exist"):
            cl.add("boundary", "destination exists", ck.DRY_SKIPPED,
                   f"'{dest}' queued earlier in this run -- not independently checkable "
                   f"read-only, recorded honestly rather than faked")
        else:
            ui.emit(Note(f"  REFUSED: destination directory '{dest}' does not exist -- nothing to "
                   f"write the multiplex TOML or deployment.json keys into. Run a birth first "
                   f"(or check the path), then retry this screen.", tone="refusal"))
            cl.add("boundary", "destination exists", ck.REFUSED, f"'{dest}' not a directory")
            return state
    world = state.get("world") or ui.ask_text("World/deployment name")
    host = state.get("pghost") or ui.ask_text("Postgres host", default="192.168.122.1")
    db = state.get("db") or ui.ask_text("Database", default="toy")

    port = probes.free_port()
    boundary_url = f"http://127.0.0.1:{port}"
    ui.emit(Paragraph(f"  picked free port: {port} ({boundary_url})"))

    toml_path = os.path.join(dest, "boundary-multiplex.toml")
    dep_json_path = os.path.join(dest, "deployment.json")
    dep = {}
    if os.path.isfile(dep_json_path):
        with open(dep_json_path) as f:
            dep = json.load(f)
    schema = dep.get("schema", world)
    kern = dep.get("kern", f"{world}_kernel")
    role = dep.get("role", f"{world}_rw")

    for _label, _val, _checker in (
        ("host", host, probes.valid_hostname),
        ("database", db, probes.valid_identifier),
        ("role", role, probes.valid_identifier),
        ("schema", schema, probes.valid_identifier),
        ("kern", kern, probes.valid_identifier),
        ("world", world, probes.valid_identifier),
    ):
        if not _checker(_val):
            ui.emit(Note(f"  REFUSED: {_label} '{_val}' fails the interpreter-boundary allowlist -- "
                   f"refusing to splice it into boundary-multiplex.toml (law/adr/0012's "
                   f"interpreter-boundary rule). Nothing written.", tone="refusal"))
            cl.add("boundary", "multiplex TOML values validated", ck.REFUSED,
                   f"'{_val}' ({_label}) failed {_checker.__name__}")
            return state

    toml_text = (
        f"[deployments.{world}]\n"
        f'pghost = "{host}"\n'
        f'pgdatabase = "{db}"\n'
        f'pguser = "{role}"\n'
        f'pgschema = "{schema}"\n'
        f'pgkern = "{kern}"\n'
    )
    ui.emit(Paragraph(f"  --- queuing write: {toml_path} ---"))
    ui.emit(Paragraph("  " + toml_text.replace("\n", "\n  ")))
    plan = _plan(state)
    plan.append(PlanEntry(screen="boundary", item="multiplex TOML written",
                           lesson="the boundary service's own config file",
                           act=WriteAct(path=toml_path, content=toml_text)))

    argv = [str(REPO_ROOT / "bootstrap" / "new-project.sh"), dest,
            "--db", db, "--host", host,
            "--schema", schema, "--kern", kern, "--role", role,
            "--name", dep.get("name", world), "--force",
            "--boundary-url", boundary_url, "--boundary-deployment", world]
    if state.get("governed_patterns"):
        argv += ["--governed", governed_files.governed_flag_value(state["governed_patterns"])]
    ui.emit(Paragraph(f"  $ {' '.join(argv)}"))
    plan.append(PlanEntry(screen="boundary", item="deployment.json boundary keys written",
                           lesson="classic-mode re-scaffold: rewrites deployment.json + .claude/",
                           act=CommandAct(argv=tuple(argv))))

    # Interpreter RESOLUTION is a read-only probe (decision-phase legal); the START itself stays
    # a BackgroundAct below. Mirrors bootstrap/new-project.sh:319-320's own fallback (ADR-0012
    # P1: one pattern, not a second hand-rolled rule) -- preferred venv if executable, else
    # python3 on PATH -- and NEVER silently: which interpreter was picked, and why, is one
    # honest line to the operator either way (ADR-0002 rules 1/4). Resolved BEFORE the
    # can_start question (moved up from its original position) because the CHECKLIST-SPLIT-SPEC
    # `DaemonSelection` below needs the SAME resolved-interpreter fact, resolved once (spec §4:
    # "start-daemons uses the same resolved-interpreter fact, resolved once").
    preferred_python = os.path.expanduser("~/w/vdc/venvs/generic/bin/python")
    fallback_python = probes.which("python3")
    if os.access(preferred_python, os.X_OK):
        venv_python = preferred_python
        interp_reason = f"venv interpreter: {preferred_python}"
    elif fallback_python:
        venv_python = fallback_python
        interp_reason = f"venv absent -- using python3 on PATH: {fallback_python}"
    else:
        venv_python = None
        interp_reason = f"NEITHER {preferred_python} NOR python3 is on PATH"

    can_start = ui.confirm("Start the boundary service now (this process)?", default=True)
    if can_start:
        ui.emit(Paragraph(f"  interpreter: {interp_reason}"))
    if can_start and venv_python:
        argv2 = [venv_python, "-m", "serving.boundary_service", "--config", toml_path,
                 "--port", str(port)]
        ui.emit(Paragraph(f"  $ {' '.join(argv2)}   (background)"))
        plan.append(PlanEntry(screen="boundary", item="service started",
                               lesson="starts the boundary service, this process's own child",
                               act=BackgroundAct(argv=tuple(argv2), cwd=str(REPO_ROOT)),
                               produces=BOUNDARY_PROC_PRODUCES))

        # design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part C completion (row 1158/1159, item 2 --
        # FAILURE HONESTY): the BackgroundAct above reports ok=True the instant Popen() succeeds
        # (commit_executor.py's own _run_entry -- forking/exec'ing is not the same fact as "the
        # service actually came up"), so a genuinely failed start (the concrete case this closes:
        # the picked port is ALREADY occupied -- uvicorn's own bind refuses and the child exits
        # within milliseconds) would otherwise sail through as a false accept, and every act
        # queued AFTER it -- genesis, principal registration, charters, hydration -- would then
        # run against a boundary that is not there: a half-born world, no different from the
        # silent-fallback class this whole re-sequencing exists to foreclose. This CallableAct
        # (the one generic commit-time-effect escape hatch, plan.py's own docstring) polls the
        # SAME health URL for up to 10s (probes.wait_for_health, the automated sibling of this
        # screen's own operator-keypress _verify_boundary_started below) and is the ACT that
        # actually fails the commit -- REFUSED, with the last probe's own detail as teaching --
        # when the service never answers; per-act atomicity means NOTHING queued after this
        # entry ever runs (commit_executor.execute's own "stops at the FIRST entry whose act
        # does not succeed"). No silent fallback to legacy/led exists to reach for either way --
        # the operator's only lawful next step is fixing the port/env and re-running the commit
        # (which resumes exactly here, the journal's own resume-from-PENDING contract).
        def _boundary_health_gate() -> tuple[bool, str]:
            ok, last = probes.wait_for_health(f"{boundary_url}/d/{world}/health", timeout_s=10.0)
            if ok:
                return True, f"boundary healthy: {last}"
            return False, (
                f"REFUSED -- the boundary service never answered {boundary_url}/d/{world}/health "
                f"within 10s (last probe: {last}). The most likely cause is the port ({port}) "
                f"already being occupied by another process -- check with `ss -ltnp | grep "
                f"{port}` (or lsof -i :{port}), free the port or re-run this screen to pick a "
                f"different one, then retry the commit. NOTHING after this act ran (per-act "
                f"atomicity); genesis/principal-registration/hydration never touched a half-born "
                f"world.")
        plan.append(PlanEntry(screen="boundary", item="service health gate",
                               lesson="confirms the boundary actually came up before any "
                                      "ledger-writing act trusts it",
                               act=CallableAct(fn=_boundary_health_gate,
                                                label=f"poll {boundary_url}/d/{world}/health")))
        state["boundary_will_start"] = True
        state["boundary_world"] = world
    else:
        if can_start and not venv_python:
            # ADR-0002 rung 4: the operator answered yes, the auto-start could not proceed, and
            # here is the concrete, named reason -- never a silent downgrade to the block below.
            ui.emit(Note(f"  REFUSED auto-start: operator answered yes, but {interp_reason} -- "
                   f"falling back to the manual/systemd instructions below.", tone="refusal"))
            cl.add("boundary", "service auto-start", ck.REFUSED, interp_reason)
        unit_text = (
            f"[Unit]\nDescription=autoharn boundary service ({world})\n\n"
            f"[Service]\nExecStart={venv_python or preferred_python} -m serving.boundary_service "
            f"--config {toml_path}\nWorkingDirectory={REPO_ROOT}\nRestart=on-failure\n\n"
            f"[Install]\nWantedBy=multi-user.target\n"
        )
        ui.emit(Paragraph("  --- PREPARED: systemd unit text (operator installs/starts) ---"))
        ui.emit(Paragraph("  " + unit_text.replace("\n", "\n  ")))
        ui.emit(Paragraph("  --- end ---"))
        # CHECKLIST-SPLIT-SPEC ADDITION (§3): the boundary service becomes a `DaemonSelection`
        # ONLY on this (non-auto-start) leg -- the maintainer's g.1 commission and the field
        # observation ("had to manually start boundary-multiplex") that motivated the daemon
        # collection script, applied as a genuine FALLBACK, never a second concurrent start.
        # PRODUCT FIX, found live while building this feature (WDR1's own byte-identical-
        # filesystem witness, seen-red/setup-tui-dry-run-parity): an earlier draft added this
        # DaemonSelection unconditionally, reasoning the generated script's OWN idempotence
        # (a pidfile check) would make re-running it after a successful in-process auto-start a
        # safe no-op -- but the script's pidfile has no way to know a process the DIRECT
        # BackgroundAct already started IS that same daemon; running start-daemons anyway spawned
        # a SECOND real boundary_service bound to the SAME port, which failed to bind and
        # produced live, changing log content -- caught as a genuine WDR1 red (a live filesystem
        # diff under what should have been a no-op --dry-run rehydration), not a fixture artifact.
        plan.add_daemon(DaemonSelection(
            name="boundary",
            argv=(venv_python or preferred_python, "-m", "serving.boundary_service",
                  "--config", toml_path, "--port", str(port)),
            cwd=str(REPO_ROOT), env_notes="boundary-multiplex.toml's own deployment section",
            health_probe=f"http:{boundary_url}/d/{world}/health",
            prerequisite=(venv_python or preferred_python),
        ))
        ui.emit(Paragraph(f"  ({os.path.join(dest, 'start-daemons')} also starts this daemon once "
               f"committed, and refuses loudly, naming it, if the interpreter above turns out "
               f"not to exist on whatever machine runs it)"))
        # STATUS-SPLIT (design/FABLE-SETUP-TUI-CHECKLIST-SPLIT-SPEC.md §2): ck.INSTRUCTED, not
        # ck.PREPARED -- unit TEXT is shown; nothing about the world's state (the unit
        # installed, the service running) is confirmed. The narrowed PREPARED does not apply.
        cl.add("boundary", "service unit text", ck.INSTRUCTED, "systemd unit, not started")

        def _verify_boundary_started() -> None:
            ui.pause("Start the service by hand, then press enter to probe: ")
            ok_h, status_h, body_h = probes.http_get_json(f"{boundary_url}/d/{world}/health")
            ui.emit(Paragraph(f"  /health probe: {'GREEN' if ok_h else 'RED'} status={status_h} "
                   f"body={body_h}"))
            cl.add("boundary", "/health probe (post-keypress)", ck.WITNESSED,
                   f"status={status_h} ok={ok_h}")

        _dry_skip_or(ui, cl, state, "boundary", "/health probe (post-keypress)",
                     _verify_boundary_started)

    state["boundary_url"] = boundary_url
    state["boundary_port"] = port
    return state


# ---------------------------------------------------------------------------------------------
# Observability -- CHECKLIST-SPLIT-SPEC REWRITE (design/FABLE-SETUP-TUI-CHECKLIST-SPLIT-SPEC.md
# §1/§3, backflow finding 3): this screen used to be entirely PREPARED-block display -- text
# shown, nothing queued, nothing ever verified. That is the exact defect the spec names: "an
# opted-in monitoring feature produced zero coverage, silently, its PREPARED rows reading as
# assurance -- while the printed start line referenced a config file the scaffold never wrote."
#
# Now: selecting otelcol queues its own prerequisite (`otelcol-config.yaml`, an ordinary
# WriteAct -- content composed from `daemon_scaffold`'s DATA, never embedded prose here) AND a
# `DaemonSelection` fact; selecting otel-watch queues a `DaemonSelection` with no config
# prerequisite of its own. Both daemons are then started by the SAME generated
# `<dest>/start-daemons` script every other selected daemon shares (commit_executor.py's
# `_daemon_script_entry`), and both get a real end-of-run health/liveness verification row
# (VERIFIED_UP or the named NOT_UP absence -- never silence). The Claude-launch line has no
# daemon behind it (it is a one-shot foreground command, not a standing service) and stays a
# plain INSTRUCTED display row, per the vocabulary split (§2): shown, nothing about the world's
# state claimed.
# ---------------------------------------------------------------------------------------------

def screen_observability(ui, cl, state):
    ui.emit(Heading(screen_banner("observability")))
    _show_facts(ui, "observability_otelcol", "observability_watchdog")
    if not ui.confirm("Configure observability now?", default=True):
        cl.add("observability", "observability", ck.SKIPPED, skip_detail("observability"))
        return state
    # CONFIG-FILE SELF-SAVE (design/FABLE-SETUP-TUI-CONFIG-FILE-SPEC.md §4): the one bit
    # `config_seam.capture_resolved_config` cannot re-derive from `state`/the plan alone -- "was
    # this SCREEN even engaged" is otherwise indistinguishable from "both daemons declined".
    state["observability_engaged"] = True
    dest = state.get("dest") or ui.ask_text("Destination directory")
    state["dest"] = dest
    plan = _plan(state)

    if ui.confirm("Select the OTel collector (otelcol-contrib) to start with this world?",
                   default=False):
        export_path = os.path.join(dest, "otel-data", "claude-events.jsonl")
        config_path = os.path.join(dest, "otelcol-config.yaml")
        config_content = daemon_scaffold.otelcol_config_content(export_path)
        ui.emit(Paragraph(f"  --- queuing write: {config_path} ---"))
        ui.emit(Paragraph("  " + config_content.replace("\n", "\n  ")))
        plan.append(PlanEntry(
            screen="observability", item="otelcol-config.yaml written",
            lesson="otelcol's own config file -- the prerequisite the start line references "
                   "(backflow finding 3's own root cause: a printed start line pointing at a "
                   "config the scaffold never wrote)",
            act=WriteAct(path=config_path, content=config_content)))
        otelcol_bin = probes.which("otelcol-contrib")
        argv = (otelcol_bin or "otelcol-contrib", "--config", config_path)
        plan.add_daemon(DaemonSelection(
            name="otelcol", argv=argv, cwd=dest,
            env_notes="OTLP gRPC receiver on 127.0.0.1:4317, file exporter, health_check "
                       "extension on 127.0.0.1:13133 (design/FABLE-OTEL-SENTRY-SPEC.md's own "
                       "deployment-shape-A record)",
            health_probe=f"http:{daemon_scaffold.OTELCOL_HEALTH_URL}",
            prerequisite=(otelcol_bin or
                          "otelcol-contrib (not found on PATH at selection time)"),
        ))
        ui.emit(Paragraph(f"  queued daemon: {' '.join(argv)}   (started via <dest>/start-daemons at "
               f"commit; verified at end-of-run)"))
        cl.add("observability", "otelcol selected", ck.INSTRUCTED,
               f"argv={' '.join(argv)}; config queued: {config_path}")
    else:
        cl.add("observability", "otelcol selected", ck.SKIPPED, "operator declined")

    if ui.confirm("Select the OTel model-provenance watchdog (otel-watch) to start with this "
                   "world?", default=False):
        watch_bin = str(REPO_ROOT / "otel-watch")
        argv = (watch_bin, "--daemon")
        plan.add_daemon(DaemonSelection(
            name="otel-watch", argv=argv, cwd=str(REPO_ROOT),
            env_notes="tails the collector's own JSONL export; exposes no HTTP endpoint of "
                       "its own, verified by process liveness instead",
            health_probe=f"pidof:{watch_bin}",
            prerequisite=(watch_bin if os.path.isfile(watch_bin) else None),
        ))
        ui.emit(Paragraph(f"  queued daemon: {' '.join(argv)}   (started via <dest>/start-daemons at "
               f"commit; verified at end-of-run)"))
        cl.add("observability", "otel-watch selected", ck.INSTRUCTED, f"argv={' '.join(argv)}")
    else:
        cl.add("observability", "otel-watch selected", ck.SKIPPED, "operator declined")

    claude_line = f"cd {dest} && claude"
    ui.emit(Paragraph("  --- INSTRUCTED: Claude launch line ---"))
    ui.emit(Paragraph(f"  {claude_line}"))
    ui.emit(Paragraph("  what you should see: CLAUDE.md's governance preamble auto-loads (no paste needed)"))
    ui.emit(Paragraph("  --- end ---"))
    cl.add("observability", "claude launch line", ck.INSTRUCTED, claude_line)
    return state


# ---------------------------------------------------------------------------------------------
# Hydration -- PHASE 2: fork provenance / role charters / each durable-decision / each ADR
# adoption all become plan entries (`led decision`); CLAUDE.md compilation becomes ONE WriteAct
# whose content is a Hole on BIRTH_PRODUCES (durable_decisions.hydration_claude_md_write_act's own
# docstring explains why).
# ---------------------------------------------------------------------------------------------

def _decision_act(led: str, statement: str) -> tuple[CommandAct, str]:
    return CommandAct(argv=(led, "decision", statement)), f"decision:{hash(statement) & 0xffffffff}"


def screen_hydration(ui, cl, state):
    ui.emit(Heading(screen_banner("hydration")))
    if not ui.confirm("Run hydration now?", default=True):
        cl.add("hydration", "hydration", ck.SKIPPED, skip_detail("hydration"))
        return state
    state["hydration_engaged"] = True  # config-file self-save's own "was this screen engaged"
    dest = state.get("dest") or ui.ask_text("Destination directory (with a led shim)")
    state["dest"] = dest
    if state.get("dest_would_exist"):
        # design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part C completion (row 1158/1159): boundary
        # now runs BEFORE hydration in this same session's plan (screens.py's SCREENS list) --
        # by the time this act executes at commit time, the world's boundary is normally already
        # configured and live, so hydration's own writes go through the served path too, exactly
        # like genesis/principals-authority (all three re-sequenced in this same pass).
        # legacy-led-retirement inventory pass, part 3 (row 1149/1150): the decline branch this
        # used to fall back to is RETIRED (boundary now mandatory) -- always the served path.
        led = served_led_path(dest)
        cl.add("hydration", "led present", ck.DRY_SKIPPED,
               f"'{led}' queued earlier in this run (written by birth+boundary) -- not "
               f"independently checkable read-only, recorded honestly rather than faked")
    else:
        # An OUT-OF-SEQUENCE entry (--start-at hydration against an ALREADY-EXISTING world, not
        # queued this session) may predate this re-sequencing pass. `resolve_led` no longer
        # prefers legacy/led (retired with legacy-led.tmpl) -- just the served `./led`, live-
        # checked for existence exactly as before.
        led = resolve_led(dest)
        if led is None:
            ui.emit(Note(f"  REFUSED: no led found under {dest}.", tone="refusal"))
            cl.add("hydration", "led present", ck.WITNESSED, f"RED: no led under {dest}")
            return state
        cl.add("hydration", "led present", ck.WITNESSED, led)

    plan = _plan(state)
    selected_fragments: list[str] = []

    _show_facts(ui, "hydration_fork_provenance")
    if not ui.confirm("Hydrate: fork provenance?", default=False):
        cl.add("hydration", "fork provenance", ck.SKIPPED, "operator declined")
    else:
        ui.emit(Paragraph(f"  high-assurance act -- see {dest}/roles/README.md and, in the autoharn "
               f"checkout this world was scaffolded from, user-guide/USER-GPG-TRUST-LAYER-FAQ.md "
               f"/ design/MAINT-GPG-TRUST-LAYER.md."))
        statement = ui.ask_text("Statement for 'fork provenance' decision row")
        act, produces = _decision_act(led, statement)
        plan.append(PlanEntry(screen="hydration", item="fork provenance",
                               lesson="a real led decision row", act=act, produces=produces))
        ui.emit(Paragraph(f"  queued: {act.render()}"))

    _show_facts(ui, "hydration_role_charters")
    if not ui.confirm("Hydrate: role charters to register?", default=False):
        cl.add("hydration", "role charters to register", ck.SKIPPED, "operator declined")
    else:
        ui.emit(Paragraph(f"  high-assurance act -- see {dest}/roles/README.md and, in the autoharn "
               f"checkout this world was scaffolded from, user-guide/USER-GPG-TRUST-LAYER-FAQ.md "
               f"/ design/MAINT-GPG-TRUST-LAYER.md."))
        role = ui.ask_text("Role to charter (must already be a registered led principal)")
        path = ui.ask_text("Charter file path")
        argv = ("python3", str(REPO_ROOT / "tools" / "role_charter.py"), "register",
                role, path, "--led", led)
        ui.emit(Paragraph(f"  $ {' '.join(argv)}"))
        plan.append(PlanEntry(screen="hydration", item="role charters to register",
                               lesson="binds a role's charter text via role_charter.py",
                               act=CommandAct(argv=argv)))

    for decision in durable_decisions.CATALOG:
        _show_facts(ui, f"hydration_{decision.slug.replace('-', '_')}")
        if not ui.confirm(f"Hydrate durable decision: {decision.slug}?", default=False):
            cl.add("hydration", decision.slug, ck.SKIPPED, "operator declined")
            continue
        act, produces = _decision_act(led, decision.hydrates)
        plan.append(PlanEntry(screen="hydration", item=decision.slug,
                               lesson="a curated durable-decision row + CLAUDE.md fragment",
                               act=act, produces=produces))
        ui.emit(Paragraph(f"  queued: {act.render()}"))
        selected_fragments.append(decision.claude_md)

    _show_facts(ui, "hydration_adr_adoption")
    adrs = durable_decisions.list_adrs()
    ui.emit(Paragraph(f"  {len(adrs)} ADR(s) found under law/adr/ -- offering each individually:"))
    for number, title, relpath in adrs:
        label = f"ADR-{number}: {title}"
        if not ui.confirm(f"Adopt {label}?", default=False):
            cl.add("hydration", f"adr adoption ({label})", ck.SKIPPED, "operator declined")
            continue
        statement = durable_decisions.adr_decision_statement(number, title, relpath)
        act, produces = _decision_act(led, statement)
        plan.append(PlanEntry(screen="hydration", item=f"adr adoption ({label})",
                               lesson="a real led decision row adopting this ADR", act=act,
                               produces=produces))
        ui.emit(Paragraph(f"  queued: {act.render()}"))
        selected_fragments.append(durable_decisions.adr_claude_md_fragment(number, title, relpath))

    claude_write = durable_decisions.hydration_claude_md_write_act(
        dest, selected_fragments, state.get("birth_produces", BIRTH_PRODUCES))
    plan.append(PlanEntry(screen="hydration", item="CLAUDE.md durable-decisions section compiled",
                           lesson=f"{len(selected_fragments)} fragment(s) compiled between markers",
                           act=claude_write))
    ui.emit(Paragraph(f"  queued: write {os.path.join(dest, 'CLAUDE.md')} "
           f"({len(selected_fragments)} fragment(s))"))
    return state


# ---------------------------------------------------------------------------------------------
# Checklist / COMMIT BOUNDARY -- PHASE 2 (spec §2.3): the final screen phase. The full plan is
# rendered (the WOULD-DO table as centerpiece), one confirm, then commit_executor runs it with
# streamed output and per-entry checklist rows. Under --dry-run, this is where the decision phase
# stops: no commit_executor.execute call at all, only the plan's own render() and a WOULD-DO
# checklist row per entry (WPC7's parity: this IS the byte-identical rendering a committed run's
# pre-commit table would show, since both are plan.render() on the same Plan).
# ---------------------------------------------------------------------------------------------

def _dispatch_result(ui, cl, state, index: int, entry: PlanEntry, result, proc=None) -> None:
    """Per-entry checklist decision, run from commit_executor's on_result callback -- this is
    where the "inspect the real output" logic that used to live inline in each screen now lives,
    because the real output does not exist until this callback fires. Falls back to the ordinary
    ok-based WITNESSED/REFUSED for every entry with no special case.

    `proc` is commit_executor's own 4th on_result argument (PHASE-2 fix, that module's own note):
    the entry's just-started Popen for a succeeded BackgroundAct, None otherwise. Reading it HERE
    (never via state["_last_execution_background_procs"], which is only populated from
    CE.execute()'s eventual RETURN VALUE) is load-bearing, not cosmetic -- a defect caught live
    against a real boundary_service (seen-red/setup-tui-boundary-proc-cleanup): if a LATER plan
    entry's own on_result callback raises (an unanticipated defect after boundary already
    started), CE.execute() never returns at all, so a handle recorded only in its return value
    would be lost with it -- exactly the scenario app.py's abnormal-exit cleanup exists to guard
    against. state["boundary_proc"] must be set THE MOMENT the process starts, from the
    callback's own argument, not deferred to a return that may never come."""
    if entry.screen == "birth" and entry.item == "world birth":
        if not result.ok and _ALREADY_EXISTS_REFUSAL in result.detail:
            _render_partial_birth_teaching(
                ui, cl, state.get("birth_world", "?"), state.get("birth_host", "?"),
                state.get("birth_db", "?"), state.get("dest", "?"))
            return
        cl.add(entry.screen, entry.item, ck.WITNESSED if result.ok else ck.REFUSED,
               f"{'exit 0' if result.ok else 'exit nonzero'}")
        if result.ok:
            out_lines = result.detail.splitlines()
            marker_idx = next((i for i, ln in enumerate(out_lines)
                                if "LED_ACTOR=commissioner" in ln), None)
            if marker_idx is not None:
                opening = next((i for i in range(marker_idx - 1, max(-1, marker_idx - 8), -1)
                                 if "To SIGN this run's commission" in out_lines[i]), None)
                start = opening if opening is not None else max(0, marker_idx - 4)
                ui.emit(Rule())
                ui.emit(Paragraph("  --- maintainer copy-paste signing line (from the birth output above) ---"))
                for ln in out_lines[start:marker_idx + 1]:
                    ui.emit(Paragraph(f"  {ln.strip()}"))
                ui.emit(Paragraph("  --- end ---"))
        return

    if entry.screen == "signed-genesis" and entry.item == "ceremony gate (verify-commission)":
        # GENESIS-GATE HARD-STOP (ledger row 1918, closing the AUTOHARN_BACKFLOW.md finding-1
        # CLASS): this row's own status is always the honest gate verdict -- REFUSED when not
        # VERIFIED, regardless of the override, because the override does not make the signature
        # verify, it only decides whether the COMMIT halts on that fact (see the separate
        # override-exercised row below, `_verify_commission_ok`'s own docstring, and
        # signed_genesis.verify_commission_act's).
        body = signed_genesis.parse_verify_body(result.detail)
        verdict = body.get("verdict") or body.get("refusal") or "(no verdict parsed)"
        ui.emit(Paragraph(f"  verify-commission verdict: {verdict}"))
        if body.get("verdict") == "VERIFIED":
            cl.add(entry.screen, entry.item, ck.WITNESSED, f"VERIFIED: {str(body.get('detail', ''))[:200]}")
            return
        ui.emit(Note(f"  REFUSED to record the ceremony WITNESSED -- the gate's own verdict was not "
               f"VERIFIED ({verdict}); this renders the verb's own teaching honestly rather than "
               f"shortcutting the gate.", tone="refusal"))
        cl.add(entry.screen, entry.item, ck.REFUSED,
               f"NOT VERIFIED ({verdict}) -- override exercised, continuing (see the override "
               f"row below)" if result.ok else
               f"NOT VERIFIED ({verdict}) -- ceremony STOPPED here; see teaching below")
        if result.ok:
            # `verify_commission_act`'s own `verdict_check` only returns ok=True on a failed
            # verdict when --accept-unverified-genesis was given (signed_genesis.py's own
            # docstring) -- this branch IS the override path; record it as its own, separate,
            # eyes-open row (the commission's own "PLUS an explicit checklist row").
            ui.emit(Paragraph("  --accept-unverified-genesis was given: continuing DESPITE this unverified "
                   "genesis signature -- eyes open, on the record below. This world's audit "
                   "chain will anchor to a signature that did not verify; that is a deliberate "
                   "choice made for this run, not a bug."))
            cl.add(entry.screen, "verify-commission override exercised", ck.WITNESSED,
                   f"--accept-unverified-genesis: proceeded past verdict={verdict}")
            return
        # No override: this is the hard stop (result.ok is False, so commit_executor.execute()
        # halts after this on_result call returns -- the plan entries after this one never run).
        ui.emit(Rule())
        for text in SD.GENESIS_GATE_HARD_STOP_TEACHING:
            ui.emit(Paragraph(text))
        return

    if entry.screen == "boundary" and entry.item == "service started":
        cl.add(entry.screen, entry.item, ck.WITNESSED if result.ok else ck.REFUSED, result.detail)
        if result.ok:
            if proc is not None:
                state["boundary_proc"] = proc
            time.sleep(1.5)
            world = state.get("boundary_world", "?")
            boundary_url = state.get("boundary_url", "")
            ok_h, status_h, body_h = probes.http_get_json(f"{boundary_url}/d/{world}/health")
            ui.emit(Paragraph(f"  /health probe: {'GREEN' if ok_h else 'RED'} status={status_h} body={body_h}"))
            cl.add("boundary", "/health probe", ck.WITNESSED, f"status={status_h} ok={ok_h}")
            ok_m, status_m, body_m = probes.http_get_json(f"{boundary_url}/d/{world}/meta")
            ui.emit(Paragraph(f"  /meta probe: {'GREEN' if ok_m else 'RED'} status={status_m} body={body_m}"))
            cl.add("boundary", "/meta probe", ck.WITNESSED, f"status={status_m} ok={ok_m}")
        return

    cl.add(entry.screen, entry.item, ck.WITNESSED if result.ok else ck.REFUSED,
           result.detail[:300] if isinstance(result.detail, str) else str(result.detail))


def _maybe_self_save_config(ui, cl, state, *, dry_run: bool) -> None:
    """CONFIG-FILE SELF-SAVE (design/FABLE-SETUP-TUI-CONFIG-FILE-SPEC.md §4): "every birth saves
    its config" -- called from every `_execute_commit` exit path below, so a run reaches this
    exactly once regardless of which path it took. Same reachability test `screen_checklist`'s
    own "Save this checklist" gate already uses (`os.path.isdir` live, or `dest_would_exist`
    under `--dry-run`) -- a destination that was never queued this session has nothing to save
    into, silently skipped rather than refused (this is bookkeeping, not a decision the operator
    made). `config_seam.save_world_config` is the ONE declared exception this module hands off
    to (mirrors `checklist.Checklist.save`'s own precedent -- gates/setup_tui_purity_gate.py's
    EXEMPT table names both), because the resolved decision set is not complete until the commit
    itself has run (or been rendered, under `--dry-run`)."""
    dest = state.get("dest")
    reachable = bool(dest) and (os.path.isdir(dest) or (dry_run and state.get("dest_would_exist")))
    if not reachable:
        return
    path, wrote = config_seam.save_world_config(dest, state, dry_run=dry_run)
    if dry_run:
        ui.emit(Paragraph(f"  would save: {path} (self-application, spec §4)"))
        cl.add("checklist", "world-config.toml self-saved", ck.WOULD_DO, path)
    else:
        ui.emit(Paragraph(f"  saved: {path} (self-application, spec §4)"))
        cl.add("checklist", "world-config.toml self-saved",
               ck.WITNESSED if wrote else ck.REFUSED, path)


def _execute_commit(ui, cl, state) -> None:
    plan = _plan(state)
    dry_run = state.get("dry_run", False)
    ui.emit(Rule())
    ui.emit(Paragraph(plan.render()))
    ui.emit(Rule())

    if dry_run:
        for entry in plan.entries:
            cl.add(entry.screen, entry.item, ck.WOULD_DO, entry.act.render())
        if plan.daemons:
            # CHECKLIST-SPLIT-SPEC (§5: "dry-run must show the script/config as WOULD_DO rows
            # and write nothing"). The prerequisite config write(s), if any, are already ordinary
            # `plan.entries` and got their own WOULD_DO row in the loop above; this is the ONE
            # row `_daemon_script_entry` would add at commit -- summarized the same way
            # `WriteAct.render()` summarizes every other write ("write <path>"), never the full
            # generated script text (a WOULD-DO row is a summary, not a dump, runner.py's own
            # `summarize_content` convention).
            dry_dest = state.get("dest") or "<destination>"
            script_path = CE.daemon_script_path(dry_dest)
            cl.add(CE.DAEMON_SCREEN, CE.DAEMON_SCRIPT_ITEM, ck.WOULD_DO,
                   f"write {script_path} ({len(plan.daemons)} daemon(s): "
                   f"{', '.join(d.name for d in plan.daemons)})")
        _maybe_self_save_config(ui, cl, state, dry_run=True)
        return

    if not plan.entries and not plan.daemons:
        ui.emit(Paragraph("  nothing queued -- no commit needed."))
        return

    # commit_executor.execute() synthesizes TWO entries when plan.daemons is non-empty (the
    # start-daemons script write, then its best-effort run) -- see _daemon_script_entries there.
    total_entries = len(plan.entries) + (2 if plan.daemons else 0)
    if not ui.confirm(f"Commit this plan now? ({total_entries} entr"
                       f"{'y' if total_entries == 1 else 'ies'})", default=True):
        for entry in plan.entries:
            cl.add(entry.screen, entry.item, ck.SKIPPED, "operator declined the commit")
        if plan.daemons:
            cl.add(CE.DAEMON_SCREEN, CE.DAEMON_SCRIPT_ITEM, ck.SKIPPED,
                   "operator declined the commit")
        return

    dest = state.get("dest")
    if not dest:
        ui.emit(Note("  REFUSED: no destination directory known -- cannot commit (the commit journal "
               "lives in the destination).", tone="refusal"))
        for entry in plan.entries:
            cl.add(entry.screen, entry.item, ck.REFUSED, "no destination directory")
        if plan.daemons:
            cl.add(CE.DAEMON_SCREEN, CE.DAEMON_SCRIPT_ITEM, ck.REFUSED, "no destination directory")
        return

    def _on_step(i: int, entry: PlanEntry) -> None:
        ui.emit(Paragraph(f"  [{i + 1}/{total_entries}] {entry.screen}: {entry.item}"))
        ui.emit(Paragraph(f"    {entry.lesson}"))
        ui.emit(Paragraph(f"    $ {entry.act.render()}"))

    def _on_result(i: int, entry: PlanEntry, result, proc=None) -> None:
        _dispatch_result(ui, cl, state, i, entry, result, proc)

    # state["boundary_proc"] is set directly inside _dispatch_result, from on_result's own 4th
    # (proc) argument, the MOMENT the boundary service actually starts -- not from this return
    # value, which a later entry's own on_result raising would make unreachable (see
    # _dispatch_result's own docstring for the defect this closed, caught live).
    result = CE.execute(plan, dest, on_step=_on_step, on_result=_on_result)
    # FINDING-2: the scratch GNUPGHOME's REAL path (if this commit created one) is only knowable
    # from the commit's own real bindings -- never a decision-time variable, since the setup act
    # itself runs here, at commit. Stashed for _teardown_scratch_gnupghomes below.
    state["_last_commit_bindings"] = result.bindings

    # CHECKLIST-SPLIT-SPEC §3 point 3: the end-of-run verification sweep's own checklist rows --
    # `CE.execute` already ran the sweep (only when the commit fully completed) and handed back
    # its verdicts; THIS module (which owns `cl`) is where they become rows, same division of
    # labor as every other `_dispatch_result` translation above.
    for v in result.daemon_verifications:
        if v.up:
            ui.emit(Paragraph(f"  {v.daemon.name}: VERIFIED-UP -- {v.detail}"))
            cl.add(CE.DAEMON_SCREEN, f"{v.daemon.name} verified up", ck.VERIFIED_UP, v.detail)
        else:
            ui.emit(Paragraph(f"  {v.daemon.name}: NOT-UP -- {v.detail} (selected, attempted, not "
                   f"observably up -- never silence)"))
            cl.add(CE.DAEMON_SCREEN, f"{v.daemon.name} verified up", ck.NOT_UP, v.detail)

    if not result.completed:
        # GENESIS-GATE HARD-STOP (ledger row 1918) and every other commit halt share this same
        # fact: a halted commit is not a clean run, and this process's own exit code must say so
        # (app.py's `_drive_screens` reads this flag once the screen loop finishes) -- previously
        # ANY halted commit still exited 0, indistinguishable from success to a caller checking
        # only the process exit code, a hazard this fix closes for the whole class, not only the
        # genesis-gate instance that surfaced it.
        state["commit_halted"] = True
        ui.emit(Rule())
        ui.emit(Paragraph("  COMMIT HALTED -- the journal names the next PENDING step; re-run this tool "
               "(or --start-at checklist against the same destination) to resume, or finish by "
               "hand from the output above."))
    _maybe_self_save_config(ui, cl, state, dry_run=False)


def _teardown_scratch_gnupghomes(state) -> None:
    """PRODUCT FIX (caught live against a real gpg + real commit -- seen-red/setup-tui-signed-
    genesis WG1), FINDING-2-shaped (fresh-context review of b565db1): under Phase 2, a
    `--scripted` witnessing run's scratch GNUPGHOME is created by its own plan entry
    (`signed_genesis.prepare_scratch_gnupghome_act`), at COMMIT time -- never a decision-time
    filesystem effect any more. `state["scratch_gnupghome_produces_keys"]` (appended to by
    `screen_signed_genesis`) names the PRODUCES KEY, not a path -- the real path is resolved here
    against `state["_last_commit_bindings"]` (`_execute_commit`'s own stash of the commit's real
    bindings), which is empty/absent for every early-return path (dry-run, declined commit, empty
    plan, no destination) that never actually ran the setup act -- correctly nothing to tear down
    in those cases, rather than a decision-time path this function used to just assume existed."""
    bindings = state.get("_last_commit_bindings", {})
    for key in state.get("scratch_gnupghome_produces_keys", []):
        gnupghome = bindings.get(key)
        if gnupghome:
            signed_genesis.teardown_scratch(gnupghome)


def screen_checklist(ui, cl, state):
    ui.emit(Heading(screen_banner("checklist")))
    _execute_commit(ui, cl, state)
    _teardown_scratch_gnupghomes(state)
    ui.emit(Table(headers=("SCREEN", "ITEM", "STATUS", "DETAIL"),
                  rows=tuple((it.screen, it.item, it.status, it.detail) for it in cl.items)))
    ui.emit(Paragraph(f"totals: {cl.summary_line()}"))
    dry_run = state.get("dry_run", False)
    dest = state.get("dest")
    dest_reachable = bool(dest) and (
        os.path.isdir(dest) or (dry_run and state.get("dest_would_exist")))
    if dest_reachable and ui.confirm("Save this checklist into the new world?", default=True):
        path = cl.save(dest, dry_run=dry_run)
        if dry_run:
            ui.emit(Paragraph(f"  would save: {path}"))
            cl.add("checklist", "checklist saved", ck.WOULD_DO, path)
        else:
            ui.emit(Paragraph(f"  saved: {path}"))
            cl.add("checklist", "checklist saved", ck.WITNESSED, path)
    else:
        cl.add("checklist", "checklist saved", ck.SKIPPED,
               "no destination directory, or operator declined")
    return state


# ORDER IS LOAD-BEARING (design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part C completion, ledger
# row 1158/1159, item 1): each screen's own acts are appended to the shared plan in VISIT order
# (this list's order, in the normal top-to-bottom flow -- commit_executor.execute runs
# `plan.entries` strictly in that same order, stopping at the first failure), so "boundary"
# moving here, between "birth" and "principals-authority" -- ahead of EVERY act that writes a
# ledger row (principal registration, signed genesis, hydration decisions/charters) -- is what
# makes those later acts able to assume a live, already-configured boundary rather than
# defaulting to `legacy/led` for lack of one. Was: birth, principals-authority, signed-genesis,
# boundary, observability, hydration -- the exact ordering the original Part C attempt found as
# the reason `resolve_led`'s legacy-preference existed for those two screens' own led choice
# (their own module docstrings, `tools/setup_tui/signed_genesis.py`/`principals_authority.py`,
# named the OLD position verbatim: "this screen sits between Birth and Boundary"). Both modules'
# own led choice is updated in this same pass to `served_led_path` -- see their own docstrings.
SCREENS = [
    ("preflight", screen_preflight),
    ("substrate", screen_substrate),
    ("fork-target", screen_fork_target),
    ("rehearsal", screen_rehearsal),
    ("birth", screen_birth),
    ("boundary", screen_boundary),
    ("principals-authority", screen_principals_authority),
    ("signed-genesis", screen_signed_genesis),
    ("observability", screen_observability),
    ("hydration", screen_hydration),
    ("checklist", screen_checklist),
]

SCREEN_TITLES = {
    "preflight": "Preflight",
    "substrate": "Substrate",
    "fork-target": "Fork/target",
    "rehearsal": "Rehearsal",
    "birth": "Birth",
    "principals-authority": "Principals & authority",
    "signed-genesis": "Signed genesis",
    "boundary": "Boundary",
    "observability": "Observability",
    "hydration": "Hydration",
    "checklist": "Checklist",
}
SCREEN_NUMBER = {slug: i + 1 for i, (slug, _) in enumerate(SCREENS)}
SCREEN_TOTAL = len(SCREENS)


def screen_banner(slug: str) -> str:
    return f"{SCREEN_NUMBER[slug]}/{SCREEN_TOTAL} {SCREEN_TITLES[slug]}"


def skip_detail(slug: str, verb: str = "operator skipped") -> str:
    return f"{verb} screen {SCREEN_NUMBER[slug]}"
