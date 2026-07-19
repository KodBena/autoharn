# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T21:34:05Z
#   last-change: 2026-07-18T23:39:19Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""tools/setup_tui/screens.py -- the nine screens (design/FABLE-SETUP-TUI-SPEC.md "The flow"),
in order. Each screen function takes `(ui, cl, state)` (Ui backend, Checklist, mutable dict of
flow state carried between screens) and returns the same `state` dict, mutated. Every screen is
individually skippable -- the skip itself is recorded on the checklist (spec: "every screen
skippable with the skip recorded").

Rule 1 in practice: every act on the cluster host or on the target directory goes through
`runner.run_command`, never a bare `subprocess` call buried in a screen -- so the printed
command is always the literal argv this module executes, not a paraphrase.

Feature-facts rendering (design/FABLE-SETUP-TUI-FEATURE-FACTS-SPEC.md §2, commission ledger row
1714): every screen below that offers a selectable act prints that act's facts line -- the
standards-conformance aspiration and external costs/dependencies -- from
`tools/setup_tui/feature_facts.py` BEFORE the operator commits to it, via `_show_facts` below.
No screen carries a facts string of its own (ADR-0012 P1, one home). `PREFLIGHT_BINARIES` and
`SUBSTRATE_CHOICES` just below are this module's own half of that spec's drift backstop: the
LIVE authority `feature_facts.derive_live_keys()`/the drift fixture compares against, so a
future binary or substrate choice added here without a matching registry key (or vice versa) is
caught, not silently drifted.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from tools.setup_tui import checklist as ck
from tools.setup_tui import durable_decisions, feature_facts, pghba, probes
from tools.setup_tui.runner import run_command

REPO_ROOT = Path(__file__).resolve().parents[2]

# The live authority side of feature_facts.py's drift backstop (module docstring above). Every
# name here MUST have a "preflight_<name>" entry in feature_facts.REGISTRY; the drift fixture
# (seen-red/setup-tui-feature-facts-drift/run_fixtures.py) checks both directions.
PREFLIGHT_BINARIES = ("idris2", "clingo", "python3", "psql")

# Same discipline for screen 2's ask_choice options -- every key here MUST have a
# "substrate_<key>" entry in feature_facts.REGISTRY.
SUBSTRATE_CHOICES = [
    ("existing", "existing-db path (zero manual steps, the omega-lab shape)"),
    ("dedicated", "dedicated-db path (generates a confined pg_hba block)"),
]


def _show_facts(ui, *keys: str) -> None:
    """Prints the facts line(s) for `keys` -- the ONE call site every screen below uses (spec
    §2: 'shown at the point of selection ... before the operator commits the act')."""
    ui.say(feature_facts.facts_block(list(keys)))


# ---------------------------------------------------------------------------------------------
# Screen 1: Preflight
# ---------------------------------------------------------------------------------------------

def screen_preflight(ui, cl, state):
    ui.banner("1/9 Preflight")
    if ui.confirm("Run preflight checks?", default=True) is False:
        cl.add("preflight", "all checks", ck.SKIPPED, "operator skipped screen 1")
        return state

    # repo commit
    res = run_command(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"])
    if res.ok:
        commit = res.output.strip()
        ui.say(f"  repo commit: GREEN ({commit})")
        cl.add("preflight", "repo commit", ck.WITNESSED, commit)
    else:
        ui.say("  repo commit: RED -- not a git checkout?")
        cl.add("preflight", "repo commit", ck.WITNESSED, "RED: git rev-parse HEAD failed")

    # submodules populated
    res = run_command(["git", "-C", str(REPO_ROOT), "submodule", "status"])
    dash_lines = [ln for ln in res.output.splitlines() if ln.strip().startswith("-")]
    if res.ok and not dash_lines:
        ui.say("  submodules populated: GREEN")
        cl.add("preflight", "submodules populated", ck.WITNESSED, "no '-' prefixed entries")
    else:
        ui.say("  submodules populated: RED")
        ui.say("    fix: git -C <repo> submodule update --init --recursive")
        cl.add("preflight", "submodules populated", ck.WITNESSED,
               f"RED: {len(dash_lines)} uninitialized submodule(s)")

    # binaries -- PREFLIGHT_BINARIES is this module's own half of feature_facts.py's drift
    # backstop (module docstring above); every name here needs a "preflight_<name>" registry
    # entry, checked by seen-red/setup-tui-feature-facts-drift/run_fixtures.py. `clingo` is
    # NON-FATAL (never RED-labeled) to match bootstrap/bootstrap.sh's own posture -- "the engine
    # differential proofs need it (not fatal to bootstrap)" -- everything else here is a hard
    # RED on absence, unchanged from before this build.
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

    # reachable HARNESS_PGHOST
    host = os.environ.get("HARNESS_PGHOST") or os.environ.get("EPISTEMIC_PGHOST")
    if not host:
        ui.say("  HARNESS_PGHOST: RED -- not set")
        ui.say("    fix: export HARNESS_PGHOST=<your postgres host> (or EPISTEMIC_PGHOST)")
        cl.add("preflight", "HARNESS_PGHOST reachable", ck.WITNESSED,
               "RED: HARNESS_PGHOST/EPISTEMIC_PGHOST unset")
    else:
        ok, detail = probes.pg_reachable(host)
        if ok:
            ui.say(f"  HARNESS_PGHOST ({host}): GREEN -- {detail or 'reachable'}")
            cl.add("preflight", "HARNESS_PGHOST reachable", ck.WITNESSED, f"{host}: {detail}")
        else:
            ui.say(f"  HARNESS_PGHOST ({host}): RED -- {detail}")
            ui.say(f"    fix: confirm postgres is running and reachable at {host}, or set "
                   f"HARNESS_PGHOST to the correct host")
            cl.add("preflight", "HARNESS_PGHOST reachable", ck.WITNESSED, f"RED: {detail}")
        state["pghost"] = host

    # UI backend -- informational only (app.py already picked InteractiveUi/ScriptedUi before
    # this screen ever ran, per tools/setup_tui/__init__.py's own v1-boundary docstring); this
    # re-checks LIVE via importlib.util.find_spec rather than trusting that docstring's
    # build-time claim, so the report stays honest if either package is installed later.
    for name in ("textual", "urwid"):
        _show_facts(ui, f"ui_backend_{name}")
        available = importlib.util.find_spec(name) is not None
        ui.say(f"  {name}: {'available' if available else 'not installed'} "
               f"(informational -- the numbered-menu fallback is used regardless of either "
               f"result, per v1 boundaries)")
        cl.add("preflight", f"{name} available", ck.WITNESSED,
               "available" if available else "not installed")
    return state


# ---------------------------------------------------------------------------------------------
# Screen 2: Substrate
# ---------------------------------------------------------------------------------------------

def screen_substrate(ui, cl, state):
    ui.banner("2/9 Substrate")
    if not ui.confirm("Configure substrate now?", default=True):
        cl.add("substrate", "path chosen", ck.SKIPPED, "operator skipped screen 2")
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

    # dedicated path
    db = ui.ask_text("New (dedicated) database name")
    role = ui.ask_text("New (dedicated) role name")
    # Interpreter-boundary allowlist (law/adr/0012's 2026-07-18 amendment: "a value crosses an
    # interpreter boundary as DATA... where no carrier exists, a strict validation to a closed
    # alphabet at the Port, which refuses what it cannot honor" -- the same check
    # bootstrap/teardown-world.sh already carries for schema/kern/role names). Both `db` and
    # `role` get spliced as program TEXT below -- into the pg_hba block (pghba.generate_block)
    # and into the createdb_cmd SQL string -- with no bind-variable carrier available for
    # either (this is advisory text for the OPERATOR to paste, not a query this process itself
    # runs), so the guard is the closed-alphabet refusal, checked once, adjacent to both splice
    # sites below.
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

    # Interpreter-boundary allowlist (law/adr/0012's 2026-07-18 amendment), same discipline as
    # the db/role check just above: each subnet token is spliced as program TEXT into the
    # pg_hba PREPARED block below (pghba.generate_block, one `host <db> <role> <subnet> trust`
    # line per token) with no bind-variable carrier available, so each is validated -- closed
    # alphabet AND a real parse via the stdlib `ipaddress` module, never a hand-rolled regex
    # standing in for one -- before it ever reaches the block generator.
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

    # probe_db="toy" -- the shared, already-reachable database this repo's own scratch-world
    # convention uses (its live pg_hba carries a catch-all 'host toy all ... trust' for this
    # cluster's usual client subnets); reading the live file needs SOME reachable database to
    # connect through, and 'postgres' is not universally grant-open the way 'toy' is here
    # (witnessed live 2026-07-18: a bare 'postgres' probe hit 'no pg_hba.conf entry' before
    # ever reaching pg_read_file).
    try:
        block, disclosure = pghba.build_prepared_block(host, db, role, subnet_list,
                                                         probe_db="toy")
    except pghba.PgHbaReadError as exc:
        ui.say(f"  could not read the live pg_hba.conf: {exc}")
        cl.add("substrate", "pg_hba block (dedicated)", ck.WITNESSED, f"REFUSED-READ: {exc}")
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

    ui.pause(f"Apply the two blocks above on {host}, then press enter to verify: ")
    ok, detail = probes.pg_connect(host, db, role=role)
    if ok:
        ui.say(f"  post-keypress verification probe: GREEN -- {detail}")
        cl.add("substrate", "dedicated-db connection verified", ck.WITNESSED, detail)
        state["dedicated_verified"] = True
    else:
        ui.say(f"  post-keypress verification probe: RED -- {detail}")
        ui.say("  REFUSED to advance: the connection probe did not succeed. This is the "
               "honesty-rule-2 gate -- pressing enter is not enough, the effect must be real.")
        cl.add("substrate", "dedicated-db connection verified", ck.WITNESSED,
               f"RED (refused to advance): {detail}")
        state["dedicated_verified"] = False
    return state


# ---------------------------------------------------------------------------------------------
# Screen 3: Fork/target
# ---------------------------------------------------------------------------------------------

def screen_fork_target(ui, cl, state):
    ui.banner("3/9 Fork/target")
    if not ui.confirm("Choose destination now?", default=True):
        cl.add("fork-target", "destination", ck.SKIPPED, "operator skipped screen 3")
        return state

    mode = ui.ask_choice("Destination kind?", [
        ("fresh", "fresh directory"),
        ("fork", "fork-copy of an existing project"),
    ])
    if mode == "fresh":
        dest = ui.ask_text("Fresh destination directory (will be created)")
        dest_path = Path(dest)
        if dest_path.exists():
            # Mirrors the fork branch's own existence check below: new-project.sh does not
            # refuse an occupied directory itself -- it MERGES the scaffold into whatever is
            # already there (silently overwriting scaffold-owned files it touches, per --force
            # semantics elsewhere, and leaving alone what it doesn't) -- never this tool's call
            # to make for a "fresh" directory the operator asked for by name.
            ui.say(f"  REFUSED: destination '{dest}' already exists -- a 'fresh directory' "
                   f"request against an occupied path would have new-project.sh merge into it "
                   f"silently. Nothing done.")
            cl.add("fork-target", "destination", ck.REFUSED, f"REFUSED: '{dest}' already exists")
            return state
        state["dest"] = dest
        cl.add("fork-target", "destination", ck.WITNESSED, f"fresh dir: {dest}")
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
    shutil.copytree(src_path, dest_path)
    cl.add("fork-target", "fork-copy", ck.WITNESSED, f"{src} -> {dest}")

    # the CLAUDE.md-preservation move the omega-lab pass established: rename the fork's own
    # CLAUDE.md to CLAUDE.project.md BEFORE the scaffold writes a fresh governance preamble at
    # CLAUDE.md, so the fork's original content survives under a different name rather than
    # being clobbered by bootstrap/new-project.sh's unconditional CLAUDE.md write.
    dest_claude = dest_path / "CLAUDE.md"
    if dest_claude.is_file():
        dest_project_claude = dest_path / "CLAUDE.project.md"
        ui.say(f"  $ mv {dest_claude} {dest_project_claude}")
        dest_claude.rename(dest_project_claude)
        cl.add("fork-target", "CLAUDE.md preserved", ck.WITNESSED,
               f"renamed to CLAUDE.project.md (the omega-lab pass's own move)")
    else:
        cl.add("fork-target", "CLAUDE.md preserved", ck.SKIPPED,
               "fork source had no CLAUDE.md to preserve")

    state["dest"] = str(dest_path)
    return state


# ---------------------------------------------------------------------------------------------
# Screen 4: Rehearsal
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


def screen_rehearsal(ui, cl, state):
    ui.banner("4/9 Rehearsal")
    if not ui.confirm("Run rehearsal (scratch birth + teardown + zero-residue check)?",
                       default=True):
        cl.add("rehearsal", "rehearsal", ck.SKIPPED, "operator skipped screen 4")
        state["rehearsal_green"] = False
        return state

    host = state.get("pghost") or ui.ask_text("Postgres host", default="192.168.122.1")
    db = state.get("db") or ui.ask_text("Database", default="toy")
    scratch_world = ui.ask_text("Scratch world name (must match teardown's scratch-safe "
                                 "pattern, e.g. probeworldNNNN)",
                                 default=f"probeworld{int(time.time())}")
    scratch_dir = ui.ask_text("Scratch scaffold directory (throwaway)",
                               default=f"/tmp/setup_tui_rehearsal_{scratch_world}")

    argv = _new_project_argv(scratch_dir, scratch_world, db, host, extra=["--force"])
    res = run_command(argv)
    birth_ok = res.ok
    cl.add("rehearsal", "scratch birth", ck.WITNESSED if birth_ok else ck.REFUSED,
           f"{'exit 0' if birth_ok else f'exit {res.returncode}'}")

    # --dir has teardown-world.sh itself remove the scaffold directory as part of its own
    # verified plan (rule 1: existing verbs, never a second implementation) -- this used to be
    # a separate, unconditional `shutil.rmtree(..., ignore_errors=True)` below, which claimed
    # WITNESSED regardless of whether the directory actually disappeared. Passing --dir here
    # instead makes removal part of teardown-world.sh's own printed plan and its own residue
    # check, and the claim below is checked against reality (os.path.isdir), not assumed.
    argv = _teardown_argv(scratch_world, db, host, extra=["--dir", scratch_dir])
    res = run_command(argv, stdin_text=f"{scratch_world}\n")
    teardown_ok = res.ok
    cl.add("rehearsal", "scratch teardown", ck.WITNESSED if teardown_ok else ck.REFUSED,
           f"{'exit 0' if teardown_ok else f'exit {res.returncode}'}")

    dir_removed = not os.path.isdir(scratch_dir)
    cl.add("rehearsal", "scratch scaffold dir removed",
           ck.WITNESSED if dir_removed else ck.REFUSED,
           scratch_dir if dir_removed else f"STILL PRESENT: {scratch_dir}")

    green = birth_ok and teardown_ok
    ui.say(f"  rehearsal: {'GREEN' if green else 'RED'}")
    cl.add("rehearsal", "rehearsal overall", ck.WITNESSED, "GREEN" if green else "RED")
    state["rehearsal_green"] = green
    return state


# ---------------------------------------------------------------------------------------------
# Screen 5: Birth
# ---------------------------------------------------------------------------------------------

def screen_birth(ui, cl, state):
    ui.banner("5/9 Birth")
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
        cl.add("birth", "world birth", ck.SKIPPED, "operator skipped screen 5")
        return state

    host = state.get("pghost") or ui.ask_text("Postgres host", default="192.168.122.1")
    db = state.get("db") or ui.ask_text("Database", default="toy")
    world = ui.ask_text("World name")
    dest = state.get("dest") or ui.ask_text("Destination directory")
    name = ui.ask_text("Project name (deployment.json 'name')", default=world)

    argv = _new_project_argv(dest, world, db, host, extra=["--name", name])
    res = run_command(argv)
    ok = res.ok
    cl.add("birth", "world birth", ck.WITNESSED, f"{'exit 0' if ok else f'exit {res.returncode}'}")
    state["world"] = world
    state["dest"] = dest
    state["birth_ok"] = ok

    # the maintainer copy-paste signing line new-project.sh prints at the end of a --new-world
    # run -- surfaced prominently here, not buried in the streamed log above. Anchored on the
    # LITERAL marker new-project.sh actually prints for the FULL-mode signing line
    # ("LED_ACTOR=commissioner ./led commission ..."), not a bare "sign" substring -- the old
    # substring match hit unrelated noise elsewhere in the same output (e.g. "self-assigned",
    # "keys/README.md", any prose line containing "sign") and, being an unordered filter over
    # ALL lines, could surface those matches instead of the real block hundreds of lines later.
    out_lines = res.output.splitlines()
    marker_idx = next((i for i, ln in enumerate(out_lines) if "LED_ACTOR=commissioner" in ln),
                       None)
    if marker_idx is not None:
        # Leading context: new-project.sh's own sentence introducing the signing line reads
        # "To SIGN this run's commission yourself (FULL mode -- ...), type / this in YOUR OWN
        # terminal, inside <dir> (...):" -- THREE lines (bootstrap/new-project.sh's own `echo`
        # calls, verified against source), not two: a fixed 2-line lookback starts mid-sentence
        # ("kind.sql; the ask carries..."). Prefer the real sentence-initial line ("To SIGN
        # this run's commission") if it is found within a few lines back; fall back to a fixed
        # 4-line lookback (still >= the 3 the real wrap needs) if that marker ever changes.
        opening = next((i for i in range(marker_idx - 1, max(-1, marker_idx - 8), -1)
                         if "To SIGN this run's commission" in out_lines[i]), None)
        start = opening if opening is not None else max(0, marker_idx - 4)
        sign_lines = out_lines[start:marker_idx + 1]
        ui.say("")
        ui.say("  --- maintainer copy-paste signing line (from the birth output above) ---")
        for ln in sign_lines:
            ui.say(f"  {ln.strip()}")
        ui.say("  --- end ---")
    return state


# ---------------------------------------------------------------------------------------------
# Screen 6: Boundary
# ---------------------------------------------------------------------------------------------

def screen_boundary(ui, cl, state):
    ui.banner("6/9 Boundary")
    _show_facts(ui, "boundary_service")
    # Gates on birth_ok EXACTLY as screen_birth gates on rehearsal_green above -- `not
    # state.get(...)` catches both an explicit False (birth ran and failed) and a missing key
    # (birth was never run/skipped) alike, so configuring a boundary for a world that may not
    # exist always needs an explicit override, never a silent proceed.
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
        cl.add("boundary", "boundary", ck.SKIPPED, "operator skipped screen 6")
        return state
    dest = state.get("dest") or ui.ask_text("Destination directory")
    state["dest"] = dest
    # Same pattern screen_hydration's led-existence check uses (os.path.isfile(led) before
    # ever touching it): a nonexistent dest is reachable here (--start-at boundary, or an
    # overridden birth gate above) and, unchecked, crashed with a raw FileNotFoundError
    # traceback at the `open(toml_path, "w")` write below instead of an explained refusal.
    if not os.path.isdir(dest):
        ui.say(f"  REFUSED: destination directory '{dest}' does not exist -- nothing to write "
               f"the multiplex TOML or deployment.json keys into. Run a birth first (or check "
               f"the path), then retry this screen.")
        cl.add("boundary", "destination exists", ck.REFUSED, f"'{dest}' not a directory")
        return state
    world = state.get("world") or ui.ask_text("World/deployment name")
    host = state.get("pghost") or ui.ask_text("Postgres host", default="192.168.122.1")
    db = state.get("db") or ui.ask_text("Database", default="toy")

    port = probes.free_port()
    boundary_url = f"http://127.0.0.1:{port}"
    ui.say(f"  picked free port: {port} ({boundary_url})")

    # write the multiplex TOML -- the tool's own file, in the target dir only (v1 boundary).
    toml_path = os.path.join(dest, "boundary-multiplex.toml")
    dep_json_path = os.path.join(dest, "deployment.json")
    dep = {}
    if os.path.isfile(dep_json_path):
        with open(dep_json_path) as f:
            dep = json.load(f)
    schema = dep.get("schema", world)
    kern = dep.get("kern", f"{world}_kernel")
    role = dep.get("role", f"{world}_rw")

    # Interpreter-boundary allowlist (law/adr/0012's 2026-07-18 amendment), same discipline as
    # the pg_hba site (screen_substrate) and probes.pg_connect: boundary-multiplex.toml is a
    # config file a SECOND evaluator (serving.boundary_multiplex_config's tomllib parser, then
    # boundary_service's own psql calls) reads -- host/db/role/schema/kern/world all get
    # f-string-spliced into it below with no bind-variable carrier available (this is TOML text,
    # not a query), so each is validated to a closed alphabet first, refusing on failure rather
    # than writing an unvalidated value into program text a second evaluator parses. `host` gets
    # the wider hostname/IP-safe alphabet (valid_hostname) since a real Postgres host is a
    # hostname or IP literal, never a bare identifier -- db/role/schema/kern/world stay on the
    # strict [A-Za-z0-9_]+ identifier alphabet used everywhere else in this package.
    #
    # `world` is spliced into the `[deployments.{world}]` TOML table-key line below -- the same
    # site db/role/schema/kern are spliced into, and (2026-07-19 out-of-sequence-entry spec
    # amendment: a screen entered via --start-at, or reached via the OVERRIDE path above past a
    # failed/skipped birth, must independently validate every precondition the normal sequence
    # would have established) previously the ONE field this loop left out. A hostile world name
    # reachable that way (e.g. `evil"] [deployments.pwn`) produced structurally corrupt TOML,
    # confirmed reproducible with tomllib, before this fix. In the ordinary flow `world` already
    # passes an identical allowlist inside bootstrap/new-project.sh's own --new-world derivation
    # before this screen could see it; this loop makes that guarantee THIS screen's own, not
    # inherited from an upstream caller it cannot verify actually ran.
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
    ui.say(f"  --- writing {toml_path} ---")
    ui.say("  " + toml_text.replace("\n", "\n  "))
    with open(toml_path, "w") as f:
        f.write(toml_text)
    cl.add("boundary", "multiplex TOML written", ck.WITNESSED, toml_path)

    # the two deployment.json keys, via the SAME verb that wrote deployment.json in the first
    # place (rule 1: driver of existing verbs, never a second implementation writing JSON by
    # hand into a file another verb owns) -- new-project.sh --force with the boundary flags.
    # Deliberately CLASSIC mode here (no --new-world): --new-world re-applies the FULL kernel
    # lineage chain even under --force (witnessed live: re-running --new-world --force against
    # an already-birthed world hit `ERROR: there is no unique or exclusion constraint matching
    # the ON CONFLICT specification` partway through s15-schema.sql, a kernel-lineage
    # idempotency gap this build does not own or patch -- kernel/lineage is frozen-record,
    # off limits per CLAUDE.md). Classic mode with the SAME --schema/--kern/--role the birth
    # already derived applies NO kernel DDL at all (USER-CONFIGURATION.md: "Classic mode (no
    # --new-world) applies no kernel DDL at all") -- it only rewrites the scaffold-owned files
    # (deployment.json, .claude/ wiring), which is exactly and only what this screen needs.
    argv = [str(REPO_ROOT / "bootstrap" / "new-project.sh"), dest,
            "--db", db, "--host", host,
            "--schema", schema, "--kern", kern, "--role", role,
            "--name", dep.get("name", world), "--force",
            "--boundary-url", boundary_url, "--boundary-deployment", world]
    res = run_command(argv)
    ok = res.ok
    cl.add("boundary", "deployment.json boundary keys written", ck.WITNESSED,
           f"{'exit 0' if ok else f'exit {res.returncode}'}")

    # start the service, or emit the unit text as PREPARED
    can_start = ui.confirm("Start the boundary service now (this process)?", default=True)
    venv_python = os.path.expanduser("~/w/vdc/venvs/generic/bin/python")
    if can_start and os.path.isfile(venv_python):
        # --port is load-bearing: boundary_service defaults to 127.0.0.1:8420, which this
        # picked `port` deliberately avoids colliding with (a live deployment -- e.g. the
        # maintainer's own omega-lab -- may already be bound there); witnessed live 2026-07-18
        # that omitting --port silently tries 8420 anyway and the bind fails with
        # 'address already in use' if anything else already holds it.
        argv = [venv_python, "-m", "serving.boundary_service", "--config", toml_path,
                "--port", str(port)]
        ui.say(f"  $ {' '.join(argv)}   (background)")
        proc = subprocess.Popen(argv, cwd=str(REPO_ROOT), stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, text=True)
        state["boundary_proc"] = proc
        time.sleep(1.5)
        if proc.poll() is not None:
            leftover = proc.stdout.read() if proc.stdout else ""
            ui.say(f"  service exited immediately (rc={proc.returncode}): {leftover.strip()}")
            cl.add("boundary", "service started", ck.WITNESSED,
                   f"RED: exited rc={proc.returncode}: {leftover.strip()[:300]}")
        else:
            cl.add("boundary", "service started", ck.WITNESSED, f"pid {proc.pid}, {boundary_url}")

        ok_h, status_h, body_h = probes.http_get_json(f"{boundary_url}/d/{world}/health")
        ui.say(f"  /health probe: {'GREEN' if ok_h else 'RED'} status={status_h} body={body_h}")
        cl.add("boundary", "/health probe", ck.WITNESSED, f"status={status_h} ok={ok_h}")

        ok_m, status_m, body_m = probes.http_get_json(f"{boundary_url}/d/{world}/meta")
        ui.say(f"  /meta probe: {'GREEN' if ok_m else 'RED'} status={status_m} body={body_m}")
        cl.add("boundary", "/meta probe", ck.WITNESSED, f"status={status_m} ok={ok_m}")
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
        ui.pause("Start the service by hand, then press enter to probe: ")
        ok_h, status_h, body_h = probes.http_get_json(f"{boundary_url}/d/{world}/health")
        ui.say(f"  /health probe: {'GREEN' if ok_h else 'RED'} status={status_h} body={body_h}")
        cl.add("boundary", "/health probe (post-keypress)", ck.WITNESSED,
               f"status={status_h} ok={ok_h}")

    state["boundary_url"] = boundary_url
    state["boundary_port"] = port
    return state


# ---------------------------------------------------------------------------------------------
# Screen 7: Observability
# ---------------------------------------------------------------------------------------------

def screen_observability(ui, cl, state):
    ui.banner("7/9 Observability")
    _show_facts(ui, "observability_otelcol", "observability_watchdog")
    if not ui.confirm("Show observability blocks?", default=True):
        cl.add("observability", "observability", ck.SKIPPED, "operator skipped screen 7")
        return state
    dest = state.get("dest") or ui.ask_text("Destination directory")
    state["dest"] = dest
    otelcol_line = "otelcol-contrib --config otelcol-config.yaml"
    ui.say("  --- PREPARED: OTel collector start line (localhost-only, per standing config) ---")
    ui.say(f"  cd {dest} && {otelcol_line}")
    ui.say("  what you should see: 'Everything is ready. Begin running and processing data.'")
    ui.say("  --- end ---")
    cl.add("observability", "otelcol start line", ck.PREPARED, otelcol_line)

    # The model-provenance watchdog (design/FABLE-OTEL-SENTRY-SPEC.md §3, repo-root verb
    # `./otel-watch`) -- a second PREPARED block, same shape as otelcol's above (no daemon
    # management beyond emitting the start line, per the parent spec's v1 boundary). It depends
    # on the otelcol collector already running (feature_facts.py's "observability_watchdog"
    # entry names this), so it is shown second, after otelcol's own block.
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
# Screen 8: Hydration
# ---------------------------------------------------------------------------------------------

def _run_decision(led: str, statement: str) -> tuple[bool, str]:
    """Runs `led decision <statement>`, returning (ok, detail) where detail is 'row <id>' when
    the row id can be parsed from the real output, else an exit-code fallback -- never a
    fabricated id. Same regex screen_hydration's pre-catalog code already used (led's own
    `led: row <id> written.` convention, serving/boundary_cli_client.py `write_and_report`)."""
    argv = [led, "decision", statement]
    res = run_command(argv)
    row_id = None
    m = re.search(r"\brow[_ ]?(?:id)?[:=]?\s*(\d+)\b", res.output, re.IGNORECASE)
    if m:
        row_id = m.group(1)
    detail = f"row {row_id}" if row_id else (f"exit {res.returncode}" if not res.ok else "written")
    return res.ok, detail


def screen_hydration(ui, cl, state):
    ui.banner("8/9 Hydration")
    if not ui.confirm("Run hydration now?", default=True):
        cl.add("hydration", "hydration", ck.SKIPPED, "operator skipped screen 8")
        return state
    dest = state.get("dest") or ui.ask_text("Destination directory (with a led shim)")
    state["dest"] = dest
    led = os.path.join(dest, "led")
    if not os.path.isfile(led):
        ui.say(f"  REFUSED: no ./led at {led} -- hydration writes only through led (v1 "
               f"boundary), and none was found.")
        cl.add("hydration", "led present", ck.WITNESSED, f"RED: {led} not found")
        return state

    selected_fragments: list[str] = []

    # fork_provenance / role_charters: unchanged, per-world facts (spec §3 "Relation to the
    # existing screen-8 items" -- these stay outside the durable-decisions catalog, they are not
    # durable decisions). adr_corpus and makespan_pointer's free-text prompts are RETIRED here,
    # absorbed into the catalog + ADR submenu below.
    _show_facts(ui, "hydration_fork_provenance")
    if not ui.confirm("Hydrate: fork provenance?", default=False):
        cl.add("hydration", "fork provenance", ck.SKIPPED, "operator declined")
    else:
        statement = ui.ask_text("Statement for 'fork provenance' decision row")
        ok, detail = _run_decision(led, statement)
        cl.add("hydration", "fork provenance", ck.WITNESSED if ok else ck.REFUSED, detail)

    _show_facts(ui, "hydration_role_charters")
    if not ui.confirm("Hydrate: role charters to register?", default=False):
        cl.add("hydration", "role charters to register", ck.SKIPPED, "operator declined")
    else:
        role = ui.ask_text("Role to charter (must already be a registered led principal)")
        path = ui.ask_text("Charter file path")
        argv = ["python3", str(REPO_ROOT / "tools" / "role_charter.py"), "register",
                role, path, "--led", led]
        res = run_command(argv)
        cl.add("hydration", "role charters to register", ck.WITNESSED if res.ok else ck.REFUSED,
               f"{'exit 0' if res.ok else f'exit {res.returncode}'}")

    # The durable-decisions catalog (design/FABLE-SETUP-TUI-FEATURE-FACTS-SPEC.md §3): each
    # selection writes ONE `led decision` row and, if accepted, contributes its `claude_md`
    # fragment to the compiled section below (declined entries contribute NOTHING -- WD2's own
    # bar: "SKIPPED in the checklist, zero rows, zero fragments").
    for decision in durable_decisions.CATALOG:
        _show_facts(ui, f"hydration_{decision.slug.replace('-', '_')}")
        if not ui.confirm(f"Hydrate durable decision: {decision.slug}?", default=False):
            cl.add("hydration", decision.slug, ck.SKIPPED, "operator declined")
            continue
        ok, detail = _run_decision(led, decision.hydrates)
        cl.add("hydration", decision.slug, ck.WITNESSED if ok else ck.REFUSED, detail)
        if ok:
            selected_fragments.append(decision.claude_md)

    # The ADR-adoption submenu (spec §3 item 3): DERIVED from law/adr/*.md at runtime, never a
    # hand list (WD3's own bar) -- absorbs and supersedes the old free-text `adr_corpus` item.
    _show_facts(ui, "hydration_adr_adoption")
    adrs = durable_decisions.list_adrs()
    ui.say(f"  {len(adrs)} ADR(s) found under law/adr/ -- offering each individually:")
    for number, title, relpath in adrs:
        label = f"ADR-{number}: {title}"
        if not ui.confirm(f"Adopt {label}?", default=False):
            cl.add("hydration", f"adr adoption ({label})", ck.SKIPPED, "operator declined")
            continue
        statement = durable_decisions.adr_decision_statement(number, title, relpath)
        ok, detail = _run_decision(led, statement)
        cl.add("hydration", f"adr adoption ({label})", ck.WITNESSED if ok else ck.REFUSED, detail)
        if ok:
            selected_fragments.append(
                durable_decisions.adr_claude_md_fragment(number, title, relpath))

    # CLAUDE.md compilation (spec §4) -- always runs once, even with zero fragments (an explicit
    # "(none selected at hydration time)" section is absence WITNESSED, not silently assumed by
    # leaving CLAUDE.md untouched). Idempotent: re-running this screen with the same selections
    # replaces only the marked section (WD4).
    claude_path = durable_decisions.compile_claude_md(dest, selected_fragments)
    ui.say(f"  CLAUDE.md compiled: {len(selected_fragments)} fragment(s) -> {claude_path}")
    cl.add("hydration", "CLAUDE.md durable-decisions section compiled", ck.WITNESSED,
           f"{len(selected_fragments)} fragment(s) -> {claude_path}")
    return state


# ---------------------------------------------------------------------------------------------
# Screen 9: Checklist
# ---------------------------------------------------------------------------------------------

def screen_checklist(ui, cl, state):
    ui.banner("9/9 Checklist")
    ui.say(cl.render())
    dest = state.get("dest")
    if dest and os.path.isdir(dest) and ui.confirm("Save this checklist into the new world?",
                                                     default=True):
        path = cl.save(dest)
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
    ("boundary", screen_boundary),
    ("observability", screen_observability),
    ("hydration", screen_hydration),
    ("checklist", screen_checklist),
]
