#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-19T20:05:03Z
#   last-change: 2026-07-19T20:05:03Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

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
  - `prepare_scratch_gnupghome`/`write_scratch_batch_file` (signed_genesis.py) create process-
    private `/tmp` scratch state for `--scripted` witnessing -- never `dest`, the operator's
    keyring, or any ledger, so the guarantee envelope's "nothing touched before commit" is
    unaffected; they call neither `run_command` nor `write_file` (a raw `open()`/`os.mkdir`), so
    the gate does not need to carve them out.

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
from tools.setup_tui import durable_decisions, feature_facts, governed_files, pghba, probes
from tools.setup_tui import principals_authority, signed_genesis
from tools.setup_tui.plan import BackgroundAct, CommandAct, Plan, PlanEntry, WriteAct
from tools.setup_tui.runner import run_command
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
    ui.say(feature_facts.facts_block(list(keys)))


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
    ui.banner(screen_banner("preflight"))
    if ui.confirm("Run preflight checks?", default=True) is False:
        cl.add("preflight", "all checks", ck.SKIPPED, skip_detail("preflight"))
        return state

    # repo commit / submodules populated -- read-only (probes.py, PHASE-2: moved off
    # runner.run_command so this screen holds no direct choke-point call at all).
    ui.say(f"$ git -C {REPO_ROOT} rev-parse HEAD")
    ok, out = probes.git_head_commit(str(REPO_ROOT))
    if ok:
        ui.say(f"  repo commit: GREEN ({out})")
        cl.add("preflight", "repo commit", ck.WITNESSED, out)
    else:
        ui.say("  repo commit: RED -- not a git checkout?")
        cl.add("preflight", "repo commit", ck.WITNESSED, "RED: git rev-parse HEAD failed")

    ui.say(f"$ git -C {REPO_ROOT} submodule status")
    sub_ok, sub_out = probes.git_submodule_status(str(REPO_ROOT))
    dash_lines = [ln for ln in sub_out.splitlines() if ln.strip().startswith("-")]
    if sub_ok and not dash_lines:
        ui.say("  submodules populated: GREEN")
        cl.add("preflight", "submodules populated", ck.WITNESSED, "no '-' prefixed entries")
    else:
        ui.say("  submodules populated: RED")
        ui.say("    fix: git -C <repo> submodule update --init --recursive")
        cl.add("preflight", "submodules populated", ck.WITNESSED,
               f"RED: {len(dash_lines)} uninitialized submodule(s)")

    for name in PREFLIGHT_BINARIES:
        _show_facts(ui, f"preflight_{name}")
        path = probes.which(name)
        if path:
            ui.say(f"  {name}: GREEN ({path})")
            cl.add("preflight", f"{name} found", ck.WITNESSED, path)
        elif name == "clingo":
            ui.say(f"  {name}: not found on PATH (non-fatal -- the engine differential proofs "
                   f"and ./judge need it, but this does not block setup)")
            cl.add("preflight", f"{name} found", ck.WITNESSED,
                   "not on PATH (non-fatal, matches bootstrap/bootstrap.sh's own posture)")
        else:
            ui.say(f"  {name}: RED -- not found on PATH")
            fix = {
                "idris2": "install idris2 (https://github.com/idris-lang/Idris2#installation) "
                          "and ensure it is on PATH",
                "python3": "install Python 3 and ensure it is on PATH",
                "psql": "install the postgresql-client package and ensure `psql` is on PATH",
            }[name]
            ui.say(f"    fix: {fix}")
            cl.add("preflight", f"{name} found", ck.WITNESSED, f"RED: not on PATH -- {fix}")

    host = os.environ.get("HARNESS_PGHOST") or os.environ.get("EPISTEMIC_PGHOST")
    if not host:
        ui.say("  HARNESS_PGHOST: RED -- not set")
        ui.say("    fix: export HARNESS_PGHOST=<your postgres host> (or EPISTEMIC_PGHOST)")
        cl.add("preflight", "HARNESS_PGHOST reachable", ck.WITNESSED,
               "RED: HARNESS_PGHOST/EPISTEMIC_PGHOST unset")
    else:
        ok2, detail = probes.pg_reachable(host)
        if ok2:
            ui.say(f"  HARNESS_PGHOST ({host}): GREEN -- {detail or 'reachable'}")
            cl.add("preflight", "HARNESS_PGHOST reachable", ck.WITNESSED, f"{host}: {detail}")
        else:
            ui.say(f"  HARNESS_PGHOST ({host}): RED -- {detail}")
            ui.say(f"    fix: confirm postgres is running and reachable at {host}, or set "
                   f"HARNESS_PGHOST to the correct host")
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
        ui.say(f"  {name}: {'available' if available else 'not installed'} ({note})")
        cl.add("preflight", f"{name} available", ck.WITNESSED,
               "available" if available else "not installed")
    return state


# ---------------------------------------------------------------------------------------------
# Substrate -- no runner-choke-point call sites (unchanged from Phase 1: the dedicated-db path
# only ever DISPLAYS PREPARED blocks for the operator to apply by hand on the cluster host; it
# never itself calls run_command/write_file/start_background). Builds no plan entries.
# ---------------------------------------------------------------------------------------------

def screen_substrate(ui, cl, state):
    ui.banner(screen_banner("substrate"))
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
        ui.say(f"  reachability probe: {'GREEN' if ok else 'RED'} -- {detail}")
        cl.add("substrate", f"existing-db {db}@{host} reachable", status,
               f"{'GREEN' if ok else 'RED'}: {detail}")
        return state

    db = ui.ask_text("New (dedicated) database name")
    role = ui.ask_text("New (dedicated) role name")
    for _label, _val in (("database name", db), ("role name", role)):
        if not probes.valid_identifier(_val):
            ui.say(f"  REFUSED: {_label} '{_val}' contains characters outside [A-Za-z0-9_] -- "
                   f"refusing to splice it into pg_hba/SQL text (law/adr/0012's interpreter-"
                   f"boundary rule). Nothing generated.")
            cl.add("substrate", "dedicated db/role name validated", ck.REFUSED,
                   f"'{_val}' ({_label}) not in [A-Za-z0-9_]+")
            return state
    subnets = ui.ask_text("Subnets to trust (comma-separated CIDR)",
                           default="192.168.122.68/32,192.168.122.1/32")
    subnet_list = [s.strip() for s in subnets.split(",") if s.strip()]

    for _subnet in subnet_list:
        if not probes.valid_subnet(_subnet):
            ui.say(f"  REFUSED: subnet '{_subnet}' is not a valid CIDR/host token -- refusing "
                   f"to splice it into the pg_hba block (law/adr/0012's interpreter-boundary "
                   f"rule). Nothing generated.")
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
        ui.say(f"  could not read the live pg_hba.conf: {exc}")
        cl.add("substrate", "pg_hba block (dedicated)", ck.WITNESSED, f"REFUSED-READ: {exc}")
        return state
    except pghba.PgHbaValidationError as exc:
        ui.say(f"  REFUSED: {exc}")
        cl.add("substrate", "pg_hba block (dedicated)", ck.REFUSED, f"REFUSED: {exc}")
        return state

    ui.say("  " + disclosure.replace("\n", "\n  "))
    ui.say("")
    ui.say("  --- PREPARED: pg_hba.conf block (operator applies, on the cluster host) ---")
    for line in block.splitlines():
        ui.say(f"  {line}")
    ui.say("  --- end block ---")
    ui.say("")
    createdb_cmd = f"CREATE ROLE {role} LOGIN; CREATE DATABASE {db} OWNER {role};"
    ui.say("  --- PREPARED: createdb/reload block (operator applies, on the cluster host) ---")
    ui.say(f"  psql -h {host} -c \"{createdb_cmd}\"")
    ui.say(f"  # insert the pg_hba block above into pg_hba.conf, then:")
    ui.say(f"  psql -h {host} -c \"SELECT pg_reload_conf();\"")
    ui.say("  what you should see: CREATE ROLE / CREATE DATABASE / one-row 't' from reload")
    ui.say("  --- end block ---")
    cl.add("substrate", "pg_hba block generated", ck.PREPARED,
           f"db={db} role={role} subnets={subnet_list}")
    cl.add("substrate", "createdb/reload block", ck.PREPARED, f"db={db} host={host}")

    def _verify_dedicated() -> None:
        ui.pause(f"Apply the two blocks above on {host}, then press enter to verify: ")
        ok, detail = probes.pg_connect(host, db, role=role)
        if ok:
            ui.say(f"  post-keypress verification probe: GREEN -- {detail}")
            cl.add("substrate", "dedicated-db connection verified", ck.WITNESSED, detail)
            state["dedicated_verified"] = True
        else:
            ui.say(f"  post-keypress verification probe: RED -- {detail}")
            ui.say("  REFUSED to advance: the connection probe did not succeed. This is the "
                   "honesty-rule-2 gate -- pressing enter is not enough, the effect must be "
                   "real.")
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
    ui.say("  " + governed_files.TEACHING_LINE)
    ui.say(f"  default pattern set: {governed_files.DEFAULT_PATTERNS}")
    extend = ui.confirm("Extend the governed-files pattern set beyond the default (*.py) for "
                         "the other languages this project contains?", default=False)
    if not extend:
        patterns, hostile = governed_files.DEFAULT_PATTERNS, []
        cl.add("fork-target", "governed-files pattern set chosen", ck.WITNESSED,
               f"kept default (operator declined to extend): {patterns}")
    else:
        raw = ui.ask_text("Extensions to add, comma-separated (e.g. .ts,.vue,.html)")
        patterns, hostile = governed_files.build_pattern_set(raw)
        if hostile:
            ui.say(f"  REFUSED: extension token(s) {hostile} contain characters outside "
                   f"'.' + [A-Za-z0-9] -- refusing to splice into the --governed argv (law/"
                   f"adr/0012's interpreter-boundary rule). Falling back to the default set; "
                   f"nothing recorded beyond it.")
            cl.add("fork-target", "governed-files pattern set chosen", ck.REFUSED,
                   f"hostile token(s) {hostile}; reverted to default {patterns}")
        else:
            cl.add("fork-target", "governed-files pattern set chosen", ck.WITNESSED,
                   f"extended: {patterns}")
    state["governed_patterns"] = patterns

    path = governed_files.governed_files_path(dest)
    preview = json.dumps({"patterns": patterns}, indent=2) + "\n"
    ui.say(f"  --- PREVIEW: {path} (written by new-project.sh --governed at birth, and again "
           f"at any later scaffold re-run this flow performs -- never by this screen directly) "
           f"---")
    ui.say("  " + preview.replace("\n", "\n  "))


def screen_fork_target(ui, cl, state):
    ui.banner(screen_banner("fork-target"))
    if not ui.confirm("Choose destination now?", default=True):
        cl.add("fork-target", "destination", ck.SKIPPED, skip_detail("fork-target"))
        return state

    mode = ui.ask_choice("Destination kind?", [
        ("fresh", "fresh directory"),
        ("fork", "fork-copy of an existing project"),
    ])
    if mode == "fresh":
        dest = ui.ask_text("Fresh destination directory (will be created)")
        dest_path = Path(dest)
        if dest_path.exists():
            ui.say(f"  REFUSED: destination '{dest}' already exists -- a 'fresh directory' "
                   f"request against an occupied path would have new-project.sh merge into it "
                   f"silently. Nothing done.")
            cl.add("fork-target", "destination", ck.REFUSED, f"REFUSED: '{dest}' already exists")
            return state
        state["dest"] = dest
        cl.add("fork-target", "destination", ck.WITNESSED, f"fresh dir: {dest}")
        _governed_files_step(ui, cl, state, dest)
        return state

    src = ui.ask_text("Existing project directory to fork-copy")
    dest = ui.ask_text("Destination directory for the fork-copy")
    src_path = Path(src)
    dest_path = Path(dest)
    if not src_path.is_dir():
        ui.say(f"  REFUSED: source '{src}' is not a directory -- nothing copied.")
        cl.add("fork-target", "fork-copy", ck.REFUSED, f"REFUSED: '{src}' not a directory")
        return state
    if dest_path.exists():
        ui.say(f"  REFUSED: destination '{dest}' already exists -- nothing copied.")
        cl.add("fork-target", "fork-copy", ck.REFUSED, f"REFUSED: '{dest}' already exists")
        return state

    ui.say(f"  $ cp -a {src} {dest}")
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
        ui.say(f"  $ mv {dest_claude} {dest_project_claude}")
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
    ui.say("")
    ui.say("  --- REFUSED: new-project.sh's own \"already exists\" gate ---")
    ui.say(f"  deployment.json already exists at '{dest}' -- new-project.sh refused rather than")
    ui.say(f"  silently overwrite it (pass --force to replace it, which this screen deliberately")
    ui.say(f"  does NOT do on your behalf).")
    ui.say("")
    ui.say("  Likely state: a PARTIAL birth. The most common way to reach this refusal is a prior")
    ui.say(f"  '{world}' birth that died mid-DDL (killed, crashed, network drop) after")
    ui.say("  new-project.sh had already written deployment.json but before the kernel lineage")
    ui.say("  chain finished applying -- the world is neither cleanly born nor cleanly absent.")
    ui.say("")
    ui.say("  Safe next step -- teardown, NOT a --force re-birth:")
    teardown_argv = _teardown_argv(world, db, host, extra=["--dir", dest])
    ui.say(f"    $ {' '.join(teardown_argv)}")
    ui.say(f"    (teardown-world.sh will ask you to type '{world}' back to confirm -- it is")
    ui.say("     destructive and irreversible: DROP SCHEMA ... CASCADE / DROP ROLE, no undo.)")
    ui.say("  HONEST CAVEAT: teardown-world.sh was built and witnessed against CLEANLY-born")
    ui.say("  worlds. Running it against a PARTIAL kernel chain (this situation) is UNEXERCISED")
    ui.say("  -- it is very likely to work (the same DROP SCHEMA/ROLE statements apply regardless")
    ui.say("  of how far the chain got), but it has not been witnessed doing so. If teardown")
    ui.say("  itself errors, that is new information for the same row below, not a second dead")
    ui.say("  end to solve alone.")
    ui.say("")
    ui.say("  KNOWN DEAD END, do not attempt: `new-project.sh --force --new-world` against this")
    ui.say("  same destination. s15-schema.sql (kernel/lineage, frozen-record) is non-idempotent")
    ui.say("  under re-application -- a --force re-birth over a partial chain hits 'no unique or")
    ui.say("  exclusion constraint matching the ON CONFLICT specification' partway through DDL,")
    ui.say("  a KERNEL gap this build does not own or patch (ledger row 1792: routed to the")
    ui.say("  maintainer/Fable-spec lane, parked pending bandwidth -- NOT this build's to fix).")
    ui.say("  --- end ---")
    cl.add("birth", "world birth", ck.REFUSED,
           f"REFUSED (new-project.sh's own gate): deployment.json exists at '{dest}' -- likely "
           f"a partial prior birth. Taught: {' '.join(teardown_argv)} (destructive, "
           f"UNEXERCISED against a partial chain -- ledger row 1792), --force re-birth is a "
           f"known kernel-s15-non-idempotency dead end, NOT attempted.")


def screen_rehearsal(ui, cl, state):
    ui.banner(screen_banner("rehearsal"))
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
    ui.say(f"  rehearsal: {'GREEN' if green else 'RED'}{' (simulated, --dry-run)' if dry_run else ''}")
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
    ui.banner(screen_banner("birth"))
    if not state.get("rehearsal_green"):
        ui.say("  REFUSED: rehearsal did not report GREEN (or was skipped) -- the real birth "
               "is gated on rehearsal green (spec screen 4: 'the real birth is gated on "
               "rehearsal green, the ratified discipline'). Go back and run a green rehearsal "
               "first, or explicitly override below.")
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

    extra = ["--name", name]
    if state.get("governed_patterns"):
        extra += ["--governed", governed_files.governed_flag_value(state["governed_patterns"])]
    argv = _new_project_argv(dest, world, db, host, extra=extra)
    ui.say(f"  $ {' '.join(argv)}")
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
    ui.say("  (the real birth output, and the maintainer's own copy-paste signing line, stream "
           "at commit time -- this screen only queues the act.)")
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
    ui.banner(screen_banner("principals-authority"))
    _show_facts(ui, "principals_authority")
    if not ui.confirm(
        "Constitute principals & authority now? (register identities, grant competences, "
        "assert typed relations, and register role charters -- every world already has "
        "author/reviewer/commissioner from the scaffold, so skipping leaves a complete world; "
        "propaedeutic value is the point of walking it once)", default=True,
    ):
        cl.add("principals-authority", "screen", ck.SKIPPED,
               "operator skipped (declared-not-silent default=yes) -- legitimate and legible")
        return state

    dest = state.get("dest") or ui.ask_text("Destination directory (the born world)")
    state["dest"] = dest
    plan = _plan(state)
    queued_names: set[str] = state.setdefault("planned_principal_names", set())

    dest_exists = os.path.isdir(dest)
    # Out-of-sequence-entry amendment (design/FABLE-SETUP-TUI-SPEC.md 2026-07-19): a nonexistent
    # `dest` is legitimate ONLY when THIS session already queued a birth for it
    # (`state["dest_would_exist"]`, set by screen_birth/screen_fork_target) -- a genuinely
    # out-of-sequence entry (no birth in this run at all, e.g. `--start-at principals-authority`
    # against a path nobody ever discussed) must refuse legibly here, the same precondition check
    # every other screen in this module already carries. PRODUCT FIX (not a fixture issue): an
    # earlier pass of this rewrite let ANY nonexistent `dest` fall through to the spec §2.7
    # scaffold-base display below, silently treating a true out-of-sequence entry as "not yet
    # born, normal sequence" -- caught live against real Postgres (seen-red/setup-tui-principals-
    # authority WP6a).
    if not dest_exists and not state.get("dest_would_exist"):
        ui.say(f"  REFUSED: destination directory '{dest}' does not exist -- nothing to "
               f"constitute against. Run a birth first (or check the path), then retry this "
               f"screen.")
        cl.add("principals-authority", "destination exists", ck.REFUSED, f"'{dest}' not a directory")
        return state
    if dest_exists:
        legacy_led = os.path.join(dest, "legacy", "led")
        if not os.path.isfile(legacy_led):
            ui.say(f"  REFUSED: no {legacy_led} -- this does not look like a world this "
                   f"project's own scaffold produced. Nothing done.")
            cl.add("principals-authority", "legacy/led present", ck.REFUSED, f"missing: {legacy_led}")
            return state
        cl.add("principals-authority", "legacy/led present", ck.WITNESSED, legacy_led)
        try:
            existing = principals_authority.list_principals(dest)
        except Exception as exc:  # noqa: BLE001 -- a read-only probe; report, never crash the flow
            ui.say(f"  REFUSED: could not read this world's own principal_standing_current view "
                   f"({exc}) -- lineage-head readability check failed. Nothing offered.")
            cl.add("principals-authority", "world readable (lineage-head check)", ck.REFUSED, str(exc))
            return state
        cl.add("principals-authority", "world readable (lineage-head check)", ck.WITNESSED,
               f"{len(existing)} principal(s) found")
        ui.say(f"  existing principals ({len(existing)}), from {dest}'s own principal_standing_"
               f"current view:")
        for p in existing:
            ui.say(f"    id={p['id']:<4} name={p['name']:<14} class={p['agent_class']:<9} "
                   f"standing={p['standing']:<9} purpose={p.get('purpose') or '(none recorded)'}")
        cl.add("principals-authority", "existing principals shown", ck.WITNESSED,
               ", ".join(f"{p['name']}({p['agent_class']})" for p in existing) or "(none)")
        existing_names = {p["name"] for p in existing}
        s41_available, s41_reason = principals_authority.s41_status(dest)
    else:
        # Spec §2.7: shows the SCAFFOLD's contractual base, not a born world's views (which do
        # not exist yet -- birth is a still-PENDING plan entry in the normal sequence).
        cl.add("principals-authority", "destination exists", ck.DRY_SKIPPED if state.get("dry_run")
               else ck.WITNESSED, f"'{dest}' does not exist yet -- queued for this commit")
        ui.say(f"  {dest} does not exist yet -- showing the SCAFFOLD's contractual base (every "
               f"world this package births carries exactly these three, unconditionally):")
        for slug, agent_class, purpose in principals_authority.SCAFFOLD_BASE_PRINCIPALS:
            ui.say(f"    name={slug:<14} class={agent_class:<9} purpose={purpose}")
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
        ui.say("  " + principals_authority.LESSON_REGISTER)
        name = ui.ask_text("Principal name")
        agent_class = ui.ask_choice("Class (kernel/lineage/s40-schema.sql agent_class CHECK)",
                                     principals_authority.CLASS_CHOICES)
        purpose = ui.ask_text("Stated purpose (mandatory -- AC-2's 'account with a stated "
                               "purpose')")
        act, produces = principals_authority.register_principal_act(dest, name, agent_class, purpose)
        plan.append(PlanEntry(screen="principals-authority", item=f"register principal '{name}'",
                               lesson=principals_authority.LESSON_REGISTER, act=act,
                               produces=produces))
        queued_names.add(name)
        ui.say(f"  queued: {act.render()}")

    # --- item 2: authority bindings (s41 vocabulary, worlds at s41+) -------------------------
    if not s41_available:
        ui.say(f"  authority bindings section UNAVAILABLE: {s41_reason}")
        cl.add("principals-authority", "authority bindings (s41)", ck.SKIPPED, s41_reason)
    else:
        cl.add("principals-authority", "authority bindings (s41) available", ck.WITNESSED, s41_reason)
        while ui.confirm("Grant a competence now?", default=False):
            ui.say("  " + principals_authority.LESSON_COMPETENCE)
            name = ui.ask_text("Principal name (must already be registered)")
            activity = ui.ask_text("Activity")
            band = ui.ask_text("Band")
            basis = ui.ask_text("Basis")
            act, produces = principals_authority.grant_competence_act(dest, name, activity, band, basis)
            plan.append(PlanEntry(screen="principals-authority",
                                   item=f"grant competence '{activity}' to '{name}'",
                                   lesson=principals_authority.LESSON_COMPETENCE, act=act,
                                   produces=produces))
            ui.say(f"  queued: {act.render()}")

        while ui.confirm("Add a typed relation now?", default=False):
            ui.say("  " + principals_authority.LESSON_RELATION)
            subj = ui.ask_text("Subject principal name")
            rel = ui.ask_choice("Relation (kernel/lineage/s41 principal_relation_check CHECK)",
                                 principals_authority.RELATION_CHOICES)
            obj = ui.ask_text("Object principal name")
            act, produces = principals_authority.relate_act(dest, subj, rel, obj)
            plan.append(PlanEntry(screen="principals-authority", item=f"relate '{subj}' {rel} '{obj}'",
                                   lesson=principals_authority.LESSON_RELATION, act=act,
                                   produces=produces))
            ui.say(f"  queued: {act.render()}")

    # --- item 3: role charters, trap resolved -------------------------------------------------
    while ui.confirm("Register a role charter now?", default=False):
        ui.say("  " + principals_authority.LESSON_CHARTER)
        role = ui.ask_text("Role name (must be a registered principal)")
        path = ui.ask_text("Charter file path")
        if not _is_known(role):
            ui.say(f"  '{role}' is not yet a registered principal -- the charter "
                   f"pre-registration trap (spec WP3).")
            if not ui.confirm(f"Register '{role}' now, in-flow, so the charter can proceed?",
                               default=True):
                manual = (f"{os.path.join(dest, 'legacy', 'led')} register-principal {role} "
                          f"<class> --purpose \"<why>\", then retry this charter")
                ui.say(f"  REFUSED: charter left unregistered -- manual command: {manual}")
                cl.add("principals-authority", f"charter '{role}' (unregistered, declined)",
                       ck.REFUSED, manual)
                continue
            agent_class = ui.ask_choice(f"Class for '{role}'",
                                         principals_authority.CLASS_CHOICES)
            purpose = ui.ask_text(f"Stated purpose for '{role}'")
            reg_act, reg_produces = principals_authority.register_principal_act(
                dest, role, agent_class, purpose)
            plan.append(PlanEntry(screen="principals-authority",
                                   item=f"register principal '{role}' (in-flow, from charter)",
                                   lesson=principals_authority.LESSON_REGISTER, act=reg_act,
                                   produces=reg_produces))
            queued_names.add(role)
            ui.say(f"  queued: {reg_act.render()}")
        act, produces = principals_authority.charter_register_act(dest, role, path)
        plan.append(PlanEntry(screen="principals-authority", item=f"charter '{role}' <- {path}",
                               lesson=principals_authority.LESSON_CHARTER, act=act,
                               produces=produces))
        ui.say(f"  queued: {act.render()}")

    # --- item 4: the workflow on-ramp (pointer, not machinery) --------------------------------
    ui.say("  " + principals_authority.LESSON_WORKFLOW_POINTER)
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
    ui.banner(screen_banner("signed-genesis"))
    _show_facts(ui, "signed_genesis")
    if not ui.confirm(
        "Run the Signed genesis ceremony now? (generates a keypair, exports the public half "
        "into this world's keys/, signs the genesis commission, and verifies it against your "
        "own key -- one-time, no ongoing signing burden afterward)", default=True,
    ):
        cl.add("signed-genesis", "ceremony", ck.SKIPPED,
               "operator skipped (declared-not-silent default=yes, ledger row 1725) -- "
               "legitimate and legible, never nagged again this run")
        return state

    dry_run = state.get("dry_run", False)
    dest = state.get("dest") or ui.ask_text("Destination directory (the born world)")
    state["dest"] = dest
    plan = _plan(state)

    dest_exists = os.path.isdir(dest)
    if not dest_exists:
        if state.get("dest_would_exist"):
            cl.add("signed-genesis", "destination exists", ck.DRY_SKIPPED,
                   f"'{dest}' queued earlier in this run -- not independently checkable "
                   f"read-only, recorded honestly rather than faked")
            cl.add("signed-genesis", "world has keys/+verify-commission+legacy/led", ck.DRY_SKIPPED,
                   "trusted along with the destination above -- always scaffolded by birth")
        else:
            ui.say(f"  REFUSED: destination directory '{dest}' does not exist -- nothing to "
                   f"run the ceremony against. Run a birth first (or check the path), then "
                   f"retry this screen.")
            cl.add("signed-genesis", "destination exists", ck.REFUSED, f"'{dest}' not a directory")
            return state
    else:
        keys_dir = os.path.join(dest, "keys")
        verify_bin = os.path.join(dest, "verify-commission")
        legacy_led = os.path.join(dest, "legacy", "led")
        checks = (("keys/", os.path.isdir(keys_dir)), ("verify-commission", os.path.isfile(verify_bin)),
                  ("legacy/led", os.path.isfile(legacy_led)))
        missing = [name for name, ok in checks if not ok]
        if missing:
            ui.say(f"  REFUSED: {dest} is missing {', '.join(missing)} -- this does not look "
                   f"like a world this project's own scaffold produced. Nothing done.")
            cl.add("signed-genesis", "world has keys/+verify-commission+legacy/led", ck.REFUSED,
                   f"missing: {missing}")
            return state
        cl.add("signed-genesis", "world has keys/+verify-commission+legacy/led", ck.WITNESSED, dest)

    gpg_path = probes.which("gpg")
    if not gpg_path:
        ui.say("  REFUSED: 'gpg' is not on PATH -- the Signed genesis ceremony needs GnuPG "
               "installed (user-guide/USER-GPG-TRUST-LAYER-FAQ.md). Nothing done.")
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
            ui.say(f"  could not list existing commissions ({exc}) -- proceeding as if none exist")
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
        ui.say("  no existing commission designated -- a NEW founding commission will be "
               "written at commit time (FULL mode, via legacy/led) -- its row id is a symbolic "
               "hole until then.")
        statement = ui.ask_text("Founding commission statement (the ask this world exists to "
                                 "carry out)")
        act, produces = signed_genesis.write_commission_act(dest, statement)
        plan.append(PlanEntry(screen="signed-genesis", item="genesis commission written",
                               lesson="the world's founding commission row", act=act,
                               produces=produces))
        commission_id_arg = signed_genesis.commission_id_hole()
        ui.say(f"  queued: {act.render()}")
        cl.add("signed-genesis", "genesis commission designated", ck.WITNESSED,
               f"<row-id of the just-queued write> (symbolic until commit)")

    # --- keygen: ONE fixed shape, no quiz (spec step 1) -------------------------------------
    is_scripted = isinstance(ui, ScriptedUi)
    scratch_gnupghome = None
    if is_scripted:
        ui.say("  --scripted witnessing: a scratch GNUPGHOME + fixture passphrase is used "
               "(never the operator's own ~/.gnupg) at commit time.")
        name = ui.ask_text("Key Name-Real (scripted/fixture keygen)",
                            default="AUTOHARN SETUP-TUI FIXTURE KEY -- THROWAWAY")
        email = ui.ask_text("Key Name-Email (scripted/fixture keygen)",
                             default="setup-tui-fixture@example.invalid")
        scratch_gnupghome = signed_genesis.prepare_scratch_gnupghome()
        batch_path = signed_genesis.write_scratch_batch_file(scratch_gnupghome, name, email)
        act, produces = signed_genesis.keygen_scripted_act(scratch_gnupghome, batch_path)
        gnupghome = scratch_gnupghome
    else:
        name = ui.ask_text("Key Name-Real (your name)")
        email = ui.ask_text("Key Name-Email")
        gnupghome_in = ui.ask_text("GNUPGHOME to use for this key (blank = your default "
                                    "~/.gnupg)", default="")
        gnupghome = gnupghome_in or None
        ui.say("  gpg will now prompt YOU, interactively, for a passphrase (its own pinentry "
               "prompt -- never captured or scripted by this tool) -- AT COMMIT TIME.")
        act, produces = signed_genesis.keygen_operator_act(name, email, gnupghome)

    plan.append(PlanEntry(screen="signed-genesis", item="keypair generated",
                           lesson="ONE fixed shape (ed25519, sign-only, no expiry), no quiz",
                           act=act, produces=produces))
    ui.say(f"  queued: {act.render()}")

    gnupghome_display = gnupghome or "your default ~/.gnupg"
    ui.say(f"  private key custody: {gnupghome_display} -- this tool never reads, copies, or "
           f"moves it (user-guide/USER-GPG-TRUST-LAYER-FAQ.md §2: print the revocation "
           f"certificate and store it offline).")
    cl.add("signed-genesis", "private key custody (facts line, not a file)", ck.WITNESSED,
           gnupghome_display)

    # list-secret-keys (fingerprint) -- queued immediately after keygen, same commit.
    list_act, list_produces = signed_genesis.list_secret_key_act(gnupghome)
    plan.append(PlanEntry(screen="signed-genesis", item="fingerprint listed",
                           lesson="the real fingerprint keygen just produced", act=list_act,
                           produces=list_produces))
    ui.say(f"  queued: {list_act.render()}")

    # --- key lands where the record expects it (spec step 2) -------------------------------
    filename = signed_genesis.key_filename(name)
    keys_path = os.path.join(dest, "keys", filename)
    export_act, export_produces = signed_genesis.export_public_key_act(gnupghome)
    plan.append(PlanEntry(screen="signed-genesis", item="public key exported",
                           lesson="exports the real key to armored text", act=export_act,
                           produces=export_produces))
    ui.say(f"  queued: {export_act.render()}")

    keys_write = signed_genesis.keys_write_act(dest, filename)
    plan.append(PlanEntry(screen="signed-genesis", item="public key written to keys/",
                           lesson=f"discharges keys/{filename}", act=keys_write))
    ui.say(f"  queued: write {keys_path}")

    discharge = signed_genesis.discharge_write_act(dest, filename, name, email)
    plan.append(PlanEntry(screen="signed-genesis", item="keys/README.md AWAITING-KEY discharged",
                           lesson="rewrites keys/README.md's AWAITING-KEY section", act=discharge))
    ui.say(f"  queued: write {os.path.join(dest, 'keys', 'README.md')}")

    # --- sign the genesis act (spec step 3) -------------------------------------------------
    asc_path = signed_genesis.asc_path_arg(dest, commission_id_arg)
    sign_act, sign_produces = signed_genesis.sign_statement_act(
        gnupghome, statement or "", asc_path, scripted=is_scripted)
    plan.append(PlanEntry(screen="signed-genesis", item="genesis commission signed",
                           lesson="detached signature over the designated commission's statement",
                           act=sign_act, produces=sign_produces))
    ui.say(f"  queued: {sign_act.render()}")

    # --- the gate verifies, not the keypress (spec step 4) ----------------------------------
    if dry_run:
        cl.add("signed-genesis", "ceremony gate (verify-commission)", ck.DRY_SKIPPED,
               "cannot verify a signature that was never made (spec §3) -- never a faked "
               "VERIFIED; this entry is never even queued under --dry-run")
    else:
        verify_act, verify_produces = signed_genesis.verify_commission_act(dest, commission_id_arg)
        plan.append(PlanEntry(screen="signed-genesis", item="ceremony gate (verify-commission)",
                               lesson="requires the VERIFIED verdict before recording WITNESSED",
                               act=verify_act, produces=verify_produces))
        ui.say(f"  queued: {verify_act.render()}")

    ui.say("  Signed genesis complete for this run: nothing further in this flow, or in the "
           "world's ongoing operation, demands another signature (spec §1 item 5) -- "
           "subsequent acts ride the ledger's own append-only record; SIGNED remains available "
           "for later commissions as a deliberate act (user-guide/USER-GPG-TRUST-LAYER-FAQ.md "
           "§5), never a nag.")
    cl.add("signed-genesis", "no ongoing signing burden after this screen", ck.WITNESSED,
           "spec §1 item 5 -- checklist-only note, no mechanism added")
    if scratch_gnupghome:
        state.setdefault("scratch_gnupghomes", []).append(scratch_gnupghome)
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
    ui.banner(screen_banner("boundary"))
    _show_facts(ui, "boundary_service")
    if not state.get("birth_ok"):
        ui.say("  REFUSED: birth did not report success (state['birth_ok'] is not truthy) -- "
               "configuring the boundary service for a world that may not exist would be "
               "building on nothing. Go back and get a successful birth first, or explicitly "
               "override below.")
        if not ui.confirm("Override and proceed WITHOUT a confirmed successful birth? "
                           "(not recommended)", default=False):
            cl.add("boundary", "boundary", ck.REFUSED, "refused: birth_ok not truthy")
            return state
        cl.add("boundary", "birth gate", ck.WITNESSED, "OVERRIDDEN by operator")

    if not ui.confirm("Configure the boundary service now?", default=True):
        cl.add("boundary", "boundary", ck.SKIPPED, skip_detail("boundary"))
        return state
    dest = state.get("dest") or ui.ask_text("Destination directory")
    state["dest"] = dest
    if not os.path.isdir(dest):
        if state.get("dest_would_exist"):
            cl.add("boundary", "destination exists", ck.DRY_SKIPPED,
                   f"'{dest}' queued earlier in this run -- not independently checkable "
                   f"read-only, recorded honestly rather than faked")
        else:
            ui.say(f"  REFUSED: destination directory '{dest}' does not exist -- nothing to "
                   f"write the multiplex TOML or deployment.json keys into. Run a birth first "
                   f"(or check the path), then retry this screen.")
            cl.add("boundary", "destination exists", ck.REFUSED, f"'{dest}' not a directory")
            return state
    world = state.get("world") or ui.ask_text("World/deployment name")
    host = state.get("pghost") or ui.ask_text("Postgres host", default="192.168.122.1")
    db = state.get("db") or ui.ask_text("Database", default="toy")

    port = probes.free_port()
    boundary_url = f"http://127.0.0.1:{port}"
    ui.say(f"  picked free port: {port} ({boundary_url})")

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
            ui.say(f"  REFUSED: {_label} '{_val}' fails the interpreter-boundary allowlist -- "
                   f"refusing to splice it into boundary-multiplex.toml (law/adr/0012's "
                   f"interpreter-boundary rule). Nothing written.")
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
    ui.say(f"  --- queuing write: {toml_path} ---")
    ui.say("  " + toml_text.replace("\n", "\n  "))
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
    ui.say(f"  $ {' '.join(argv)}")
    plan.append(PlanEntry(screen="boundary", item="deployment.json boundary keys written",
                           lesson="classic-mode re-scaffold: rewrites deployment.json + .claude/",
                           act=CommandAct(argv=tuple(argv))))

    can_start = ui.confirm("Start the boundary service now (this process)?", default=True)
    venv_python = os.path.expanduser("~/w/vdc/venvs/generic/bin/python")
    if can_start and os.path.isfile(venv_python):
        argv2 = [venv_python, "-m", "serving.boundary_service", "--config", toml_path,
                 "--port", str(port)]
        ui.say(f"  $ {' '.join(argv2)}   (background)")
        plan.append(PlanEntry(screen="boundary", item="service started",
                               lesson="starts the boundary service, this process's own child",
                               act=BackgroundAct(argv=tuple(argv2), cwd=str(REPO_ROOT)),
                               produces=BOUNDARY_PROC_PRODUCES))
        state["boundary_will_start"] = True
        state["boundary_world"] = world
    else:
        unit_text = (
            f"[Unit]\nDescription=autoharn boundary service ({world})\n\n"
            f"[Service]\nExecStart={venv_python} -m serving.boundary_service "
            f"--config {toml_path}\nWorkingDirectory={REPO_ROOT}\nRestart=on-failure\n\n"
            f"[Install]\nWantedBy=multi-user.target\n"
        )
        ui.say("  --- PREPARED: systemd unit text (operator installs/starts) ---")
        ui.say("  " + unit_text.replace("\n", "\n  "))
        ui.say("  --- end ---")
        cl.add("boundary", "service unit text", ck.PREPARED, "systemd unit, not started")

        def _verify_boundary_started() -> None:
            ui.pause("Start the service by hand, then press enter to probe: ")
            ok_h, status_h, body_h = probes.http_get_json(f"{boundary_url}/d/{world}/health")
            ui.say(f"  /health probe: {'GREEN' if ok_h else 'RED'} status={status_h} "
                   f"body={body_h}")
            cl.add("boundary", "/health probe (post-keypress)", ck.WITNESSED,
                   f"status={status_h} ok={ok_h}")

        _dry_skip_or(ui, cl, state, "boundary", "/health probe (post-keypress)",
                     _verify_boundary_started)

    state["boundary_url"] = boundary_url
    state["boundary_port"] = port
    return state


# ---------------------------------------------------------------------------------------------
# Observability -- entirely PREPARED-block display (no effect at all, before OR after this
# build). Builds no plan entries. Unchanged.
# ---------------------------------------------------------------------------------------------

def screen_observability(ui, cl, state):
    ui.banner(screen_banner("observability"))
    _show_facts(ui, "observability_otelcol", "observability_watchdog")
    if not ui.confirm("Show observability blocks?", default=True):
        cl.add("observability", "observability", ck.SKIPPED, skip_detail("observability"))
        return state
    dest = state.get("dest") or ui.ask_text("Destination directory")
    state["dest"] = dest
    otelcol_line = "otelcol-contrib --config otelcol-config.yaml"
    ui.say("  --- PREPARED: OTel collector start line (localhost-only, per standing config) ---")
    ui.say(f"  cd {dest} && {otelcol_line}")
    ui.say("  what you should see: 'Everything is ready. Begin running and processing data.'")
    ui.say("  --- end ---")
    cl.add("observability", "otelcol start line", ck.PREPARED, otelcol_line)

    watchdog_line = f"{REPO_ROOT / 'otel-watch'} --daemon"
    ui.say("  --- PREPARED: OTel model-provenance watchdog start line ---")
    ui.say(f"  {watchdog_line}")
    ui.say("  what you should see: a coverage notice per watched session (never silent) -- "
           "design/FABLE-OTEL-SENTRY-SPEC.md §3")
    ui.say("  --- end ---")
    cl.add("observability", "otel-watch start line", ck.PREPARED, watchdog_line)

    claude_line = f"cd {dest} && claude"
    ui.say("  --- PREPARED: Claude launch line ---")
    ui.say(f"  {claude_line}")
    ui.say("  what you should see: CLAUDE.md's governance preamble auto-loads (no paste needed)")
    ui.say("  --- end ---")
    cl.add("observability", "claude launch line", ck.PREPARED, claude_line)
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
    ui.banner(screen_banner("hydration"))
    if not ui.confirm("Run hydration now?", default=True):
        cl.add("hydration", "hydration", ck.SKIPPED, skip_detail("hydration"))
        return state
    dest = state.get("dest") or ui.ask_text("Destination directory (with a led shim)")
    state["dest"] = dest
    led = os.path.join(dest, "led")
    if not os.path.isfile(led):
        if state.get("dest_would_exist"):
            cl.add("hydration", "led present", ck.DRY_SKIPPED,
                   f"'{led}' queued earlier in this run (written by birth) -- not "
                   f"independently checkable read-only, recorded honestly rather than faked")
        else:
            ui.say(f"  REFUSED: no ./led at {led} -- hydration writes only through led (v1 "
                   f"boundary), and none was found.")
            cl.add("hydration", "led present", ck.WITNESSED, f"RED: {led} not found")
            return state

    plan = _plan(state)
    selected_fragments: list[str] = []

    _show_facts(ui, "hydration_fork_provenance")
    if not ui.confirm("Hydrate: fork provenance?", default=False):
        cl.add("hydration", "fork provenance", ck.SKIPPED, "operator declined")
    else:
        ui.say(f"  high-assurance act -- see {dest}/roles/README.md and, in the autoharn "
               f"checkout this world was scaffolded from, user-guide/USER-GPG-TRUST-LAYER-FAQ.md "
               f"/ design/MAINT-GPG-TRUST-LAYER.md.")
        statement = ui.ask_text("Statement for 'fork provenance' decision row")
        act, produces = _decision_act(led, statement)
        plan.append(PlanEntry(screen="hydration", item="fork provenance",
                               lesson="a real led decision row", act=act, produces=produces))
        ui.say(f"  queued: {act.render()}")

    _show_facts(ui, "hydration_role_charters")
    if not ui.confirm("Hydrate: role charters to register?", default=False):
        cl.add("hydration", "role charters to register", ck.SKIPPED, "operator declined")
    else:
        ui.say(f"  high-assurance act -- see {dest}/roles/README.md and, in the autoharn "
               f"checkout this world was scaffolded from, user-guide/USER-GPG-TRUST-LAYER-FAQ.md "
               f"/ design/MAINT-GPG-TRUST-LAYER.md.")
        role = ui.ask_text("Role to charter (must already be a registered led principal)")
        path = ui.ask_text("Charter file path")
        argv = ("python3", str(REPO_ROOT / "tools" / "role_charter.py"), "register",
                role, path, "--led", led)
        ui.say(f"  $ {' '.join(argv)}")
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
        ui.say(f"  queued: {act.render()}")
        selected_fragments.append(decision.claude_md)

    _show_facts(ui, "hydration_adr_adoption")
    adrs = durable_decisions.list_adrs()
    ui.say(f"  {len(adrs)} ADR(s) found under law/adr/ -- offering each individually:")
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
        ui.say(f"  queued: {act.render()}")
        selected_fragments.append(durable_decisions.adr_claude_md_fragment(number, title, relpath))

    claude_write = durable_decisions.hydration_claude_md_write_act(
        dest, selected_fragments, state.get("birth_produces", BIRTH_PRODUCES))
    plan.append(PlanEntry(screen="hydration", item="CLAUDE.md durable-decisions section compiled",
                           lesson=f"{len(selected_fragments)} fragment(s) compiled between markers",
                           act=claude_write))
    ui.say(f"  queued: write {os.path.join(dest, 'CLAUDE.md')} "
           f"({len(selected_fragments)} fragment(s))")
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
                ui.say("")
                ui.say("  --- maintainer copy-paste signing line (from the birth output above) ---")
                for ln in out_lines[start:marker_idx + 1]:
                    ui.say(f"  {ln.strip()}")
                ui.say("  --- end ---")
        return

    if entry.screen == "signed-genesis" and entry.item == "ceremony gate (verify-commission)":
        body = signed_genesis.parse_verify_body(result.detail)
        verdict = body.get("verdict") or body.get("refusal") or "(no verdict parsed)"
        ui.say(f"  verify-commission verdict: {verdict}")
        if body.get("verdict") == "VERIFIED":
            cl.add(entry.screen, entry.item, ck.WITNESSED, f"VERIFIED: {str(body.get('detail', ''))[:200]}")
        else:
            ui.say(f"  REFUSED to record the ceremony WITNESSED -- the gate's own verdict was "
                   f"not VERIFIED ({verdict}); this renders the verb's own teaching honestly "
                   f"rather than shortcutting the gate.")
            cl.add(entry.screen, entry.item, ck.REFUSED, verdict)
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
            ui.say(f"  /health probe: {'GREEN' if ok_h else 'RED'} status={status_h} body={body_h}")
            cl.add("boundary", "/health probe", ck.WITNESSED, f"status={status_h} ok={ok_h}")
            ok_m, status_m, body_m = probes.http_get_json(f"{boundary_url}/d/{world}/meta")
            ui.say(f"  /meta probe: {'GREEN' if ok_m else 'RED'} status={status_m} body={body_m}")
            cl.add("boundary", "/meta probe", ck.WITNESSED, f"status={status_m} ok={ok_m}")
        return

    cl.add(entry.screen, entry.item, ck.WITNESSED if result.ok else ck.REFUSED,
           result.detail[:300] if isinstance(result.detail, str) else str(result.detail))


def _execute_commit(ui, cl, state) -> None:
    plan = _plan(state)
    dry_run = state.get("dry_run", False)
    ui.say("")
    ui.say(plan.render())
    ui.say("")

    if dry_run:
        for entry in plan.entries:
            cl.add(entry.screen, entry.item, ck.WOULD_DO, entry.act.render())
        return

    if not plan.entries:
        ui.say("  nothing queued -- no commit needed.")
        return

    if not ui.confirm(f"Commit this plan now? ({len(plan.entries)} entr"
                       f"{'y' if len(plan.entries) == 1 else 'ies'})", default=True):
        for entry in plan.entries:
            cl.add(entry.screen, entry.item, ck.SKIPPED, "operator declined the commit")
        return

    dest = state.get("dest")
    if not dest:
        ui.say("  REFUSED: no destination directory known -- cannot commit (the commit journal "
               "lives in the destination).")
        for entry in plan.entries:
            cl.add(entry.screen, entry.item, ck.REFUSED, "no destination directory")
        return

    def _on_step(i: int, entry: PlanEntry) -> None:
        ui.say(f"  [{i + 1}/{len(plan.entries)}] {entry.screen}: {entry.item}")
        ui.say(f"    {entry.lesson}")
        ui.say(f"    $ {entry.act.render()}")

    def _on_result(i: int, entry: PlanEntry, result, proc=None) -> None:
        _dispatch_result(ui, cl, state, i, entry, result, proc)

    # state["boundary_proc"] is set directly inside _dispatch_result, from on_result's own 4th
    # (proc) argument, the MOMENT the boundary service actually starts -- not from this return
    # value, which a later entry's own on_result raising would make unreachable (see
    # _dispatch_result's own docstring for the defect this closed, caught live).
    result = CE.execute(plan, dest, on_step=_on_step, on_result=_on_result)
    if not result.completed:
        ui.say("")
        ui.say("  COMMIT HALTED -- the journal names the next PENDING step; re-run this tool "
               "(or --start-at checklist against the same destination) to resume, or finish by "
               "hand from the output above.")


def _teardown_scratch_gnupghomes(state) -> None:
    """PRODUCT FIX (caught live against a real gpg + real commit -- seen-red/setup-tui-signed-
    genesis WG1): under Phase 2, a `--scripted` witnessing run's scratch GNUPGHOME
    (`signed_genesis.prepare_scratch_gnupghome`, called at DECISION time by
    `screen_signed_genesis` so the keygen act has a homedir to target) is no longer torn down
    inline right after the ceremony -- the ceremony itself is now deferred to commit, and nothing
    called `signed_genesis.teardown_scratch` afterward at all. Every scratch GNUPGHOME this run
    created (`state["scratch_gnupghomes"]`, appended to by `screen_signed_genesis`) is removed
    here, unconditionally, once the terminal commit boundary has run (or been declined, or been a
    dry run) -- WG1's own "zero scratch-GNUPGHOME residue" bar, restored."""
    for gnupghome in state.get("scratch_gnupghomes", []):
        signed_genesis.teardown_scratch(gnupghome)


def screen_checklist(ui, cl, state):
    ui.banner(screen_banner("checklist"))
    _execute_commit(ui, cl, state)
    _teardown_scratch_gnupghomes(state)
    ui.say(cl.render())
    dry_run = state.get("dry_run", False)
    dest = state.get("dest")
    dest_reachable = bool(dest) and (
        os.path.isdir(dest) or (dry_run and state.get("dest_would_exist")))
    if dest_reachable and ui.confirm("Save this checklist into the new world?", default=True):
        path = cl.save(dest, dry_run=dry_run)
        if dry_run:
            ui.say(f"  would save: {path}")
            cl.add("checklist", "checklist saved", ck.WOULD_DO, path)
        else:
            ui.say(f"  saved: {path}")
            cl.add("checklist", "checklist saved", ck.WITNESSED, path)
    else:
        cl.add("checklist", "checklist saved", ck.SKIPPED,
               "no destination directory, or operator declined")
    return state


SCREENS = [
    ("preflight", screen_preflight),
    ("substrate", screen_substrate),
    ("fork-target", screen_fork_target),
    ("rehearsal", screen_rehearsal),
    ("birth", screen_birth),
    ("principals-authority", screen_principals_authority),
    ("signed-genesis", screen_signed_genesis),
    ("boundary", screen_boundary),
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
