# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T21:34:05Z
#   last-change: 2026-07-19T18:35:41Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""tools/setup_tui/screens.py -- the eleven screens (design/FABLE-SETUP-TUI-SPEC.md "The flow" +
design/FABLE-SETUP-TUI-PRINCIPALS-AUTHORITY-SPEC.md's own "Principals & authority" screen,
inserted between Birth and Signed genesis, commission ledger row 1727 +
design/FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md's own "Signed genesis" screen, inserted between
Principals & authority and Boundary, commission ledger rows 1724/1725), in order. Each screen
function takes
`(ui, cl, state)` (Ui backend, Checklist, mutable dict of flow state carried between screens) and
returns the same `state` dict, mutated. Every screen is individually skippable -- the skip itself
is recorded on the checklist (spec: "every screen skippable with the skip recorded").

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

`--dry-run` (design/FABLE-SETUP-TUI-SPEC.md 2026-07-19 amendment): `state["dry_run"]` (set once
by `app.py`) is read at each destructive act's own call site and passed straight through to
`runner.run_command`/`runner.start_background`/`runner.write_file` -- the ONE flag, the parent
spec's own words, never re-derived per screen. Read-only probes (preflight, connection checks,
the pg_hba read, `durable_decisions.list_adrs`) take NO `dry_run` argument at all -- they run
identically in both modes, because a rehearsal that fakes its reads is a lie. A PREPARED block's
"press enter when done" verification gate (the post-keypress probe) is the one shape that is
neither a live act NOR a bare read: under dry-run it is not run at all (there is nothing to
verify -- the prepared act was never taken) and the checklist records `ck.DRY_SKIPPED`, never a
faked pass, via `_dry_skip_or` below.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import time
from pathlib import Path

from tools.setup_tui import checklist as ck
from tools.setup_tui import durable_decisions, feature_facts, governed_files, pghba, probes
from tools.setup_tui import principals_authority, signed_genesis
from tools.setup_tui.runner import (
    parse_row_id, run_command, start_background, summarize_content, write_file,
)
from tools.setup_tui.ui import ScriptedUi

REPO_ROOT = Path(__file__).resolve().parents[2]

# The live authority side of feature_facts.py's drift backstop (module docstring above). Every
# name here MUST have a "preflight_<name>" entry in feature_facts.REGISTRY; the drift fixture
# (seen-red/setup-tui-feature-facts-drift/run_fixtures.py) checks both directions.
PREFLIGHT_BINARIES = ("idris2", "clingo", "python3", "psql")

# Same discipline for the substrate screen's ask_choice options -- every key here MUST have a
# "substrate_<key>" entry in feature_facts.REGISTRY.
SUBSTRATE_CHOICES = [
    ("existing", "existing-db path (zero manual steps, the omega-lab shape)"),
    ("dedicated", "dedicated-db path (generates a confined pg_hba block)"),
]


def _show_facts(ui, *keys: str) -> None:
    """Prints the facts line(s) for `keys` -- the ONE call site every screen below uses (spec
    §2: 'shown at the point of selection ... before the operator commits the act')."""
    ui.say(feature_facts.facts_block(list(keys)))


def _dry_skip_or(ui, cl, state, screen: str, item: str, verify) -> None:
    """A PREPARED block's post-keypress verification gate (honesty rule 2: "VERIFIES the effect
    ... rather than trusting the keypress"), made `--dry-run`-aware in ONE place instead of at
    every one of this module's PREPARED-block sites. Under `state["dry_run"]`, `verify` (a
    zero-arg callable that would otherwise `ui.pause(...)` then run a live probe and `cl.add`
    its own result) is never called at all -- there is no live act behind the prepared block to
    verify -- and a single `ck.DRY_SKIPPED` row is recorded instead (spec: "recorded as
    DRY-SKIPPED, never silently passed"). Live mode calls `verify` unchanged."""
    if state.get("dry_run"):
        cl.add(screen, item, ck.DRY_SKIPPED, "dry-run: prepared act not taken, not verified")
        return
    verify()


# ---------------------------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------------------------

def screen_preflight(ui, cl, state):
    ui.banner(screen_banner("preflight"))
    if ui.confirm("Run preflight checks?", default=True) is False:
        cl.add("preflight", "all checks", ck.SKIPPED, skip_detail("preflight"))
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

    # UI backend -- informational only in the sense that this check cannot change anything
    # mid-flow (app.py's `_select_backend` already picked TextualUi/InteractiveUi/ScriptedUi
    # before this screen ever ran, design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md's own selection
    # rule); it re-checks LIVE via importlib.util.find_spec rather than trusting a build-time
    # claim, so the report stays honest across runs of the SAME installed interpreter. `textual`
    # availability is NOT merely informational for the FACE this flow is running under, though
    # -- when it is importable, TextualUi is the real interactive backend, not a numbered-menu
    # fallback; `urwid` stays informational-only (this package never adopted it as a backend).
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
# Substrate
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
    # runs). `pghba.generate_block` now validates its own db/role/subnets arguments AT the
    # boundary function itself (ledger row 1799 finding 4) -- this loop is belt-and-braces for
    # THAT splice site (an earlier, screen-level refusal before any live pg_hba read is even
    # attempted) and remains load-bearing for the createdb_cmd SQL splice below, which has no
    # boundary function of its own.
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
    except pghba.PgHbaValidationError as exc:
        # Belt-and-braces (the loop above already refused a hostile db/role/subnet before this
        # point): the boundary function's OWN refusal (ledger row 1799 finding 4), reached only
        # if a future caller bypasses this screen's pre-check.
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

    # Under --dry-run there is no live act behind the prepared blocks above to verify (nothing
    # was applied on the cluster host) -- _dry_skip_or records DRY_SKIPPED instead of pausing for
    # a keypress that would verify nothing real.
    _dry_skip_or(ui, cl, state, "substrate", "dedicated-db connection verified", _verify_dedicated)
    return state


# ---------------------------------------------------------------------------------------------
# Fork/target
# ---------------------------------------------------------------------------------------------

def _governed_files_step(ui, cl, state, dest: str) -> None:
    """The governed-files exposure amendment (design/FABLE-SETUP-TUI-SPEC.md 2026-07-19,
    commission ledger row 1730): surfaces the class-keyed pattern set
    `hooks/pretooluse_change_gate.py` governs by (F33) -- shows the default, the teaching line
    (the witnessed autoharn-panel .py-only specimen), and asks the operator to confirm or extend
    for the languages their project actually contains. Extensions are validated to a closed
    alphabet BEFORE the choice is recorded (witness (b): refused before any write anywhere).

    ONE WRITER (governed_files.py's own module docstring, the corrected design): this function
    records the CHOICE on `state["governed_patterns"]` and shows a PREVIEW of the eventual file
    content -- it never opens `<dest>/.claude/governed_files.json` itself. `screen_birth` and
    `screen_boundary` are the two `new-project.sh` call sites that actually own that path (every
    invocation rewrites the full `.claude/` wiring unconditionally); both thread
    `state["governed_patterns"]` into their own `--governed` flag, so the file is written once,
    by the same script that owns every other byte of `.claude/`, never raced. Called from BOTH of
    screen_fork_target's exit paths (fresh and fork-copy) -- unlike the file write, the CHOICE
    itself needs no live destination, so this function no longer branches on whether `dest`
    exists yet."""
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

    dry_run = state.get("dry_run", False)
    ui.say(f"  $ cp -a {src} {dest}")
    if dry_run:
        cl.add("fork-target", "fork-copy", ck.WOULD_DO, f"{src} -> {dest} (directory tree copy)")
    else:
        shutil.copytree(src_path, dest_path)
        cl.add("fork-target", "fork-copy", ck.WITNESSED, f"{src} -> {dest}")
    # Either way `dest` would exist from here on (a real copy, or -- under --dry-run -- the
    # would-be copy above): screen_boundary's out-of-sequence precondition check reads this same
    # flag screen_birth sets on a (real or simulated) successful birth.
    state["dest_would_exist"] = True

    # the CLAUDE.md-preservation move the omega-lab pass established: rename the fork's own
    # CLAUDE.md to CLAUDE.project.md BEFORE the scaffold writes a fresh governance preamble at
    # CLAUDE.md, so the fork's original content survives under a different name rather than
    # being clobbered by bootstrap/new-project.sh's unconditional CLAUDE.md write.
    #
    # Checked against SRC, not dest -- under --dry-run dest was never actually copied (above), so
    # dest_path/"CLAUDE.md" would never exist regardless of whether the fork source has one; src
    # is read-only here (a live read of a file that already exists, unaffected by --dry-run) and
    # is the only way to answer "would this rename happen" honestly in either mode.
    would_preserve = (src_path / "CLAUDE.md").is_file()
    dest_claude = dest_path / "CLAUDE.md"
    dest_project_claude = dest_path / "CLAUDE.project.md"
    if would_preserve:
        ui.say(f"  $ mv {dest_claude} {dest_project_claude}")
        if dry_run:
            cl.add("fork-target", "CLAUDE.md preserved", ck.WOULD_DO,
                   f"would rename to CLAUDE.project.md (the omega-lab pass's own move)")
        else:
            dest_claude.rename(dest_project_claude)
            cl.add("fork-target", "CLAUDE.md preserved", ck.WITNESSED,
                   f"renamed to CLAUDE.project.md (the omega-lab pass's own move)")
    else:
        cl.add("fork-target", "CLAUDE.md preserved", ck.SKIPPED,
               "fork source had no CLAUDE.md to preserve")

    state["dest"] = str(dest_path)
    _governed_files_step(ui, cl, state, str(dest_path))
    return state


# ---------------------------------------------------------------------------------------------
# Rehearsal
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


# The exact refusal text bootstrap/new-project.sh prints when `deployment.json` already exists
# and `--force` was not passed (line ~328 of that script, verified against source): "<path>/
# deployment.json already exists -- refusing to overwrite (pass --force to replace it)." Matched
# on the stable "deployment.json already exists -- refusing to overwrite" clause -- NOT the
# bare "already exists -- refusing to overwrite" tail alone, which new-project.sh's OWN
# `--pin submodule` leg also prints for an unrelated refusal ("<path>/.autoharn already exists
# -- refusing to overwrite", line ~343) that this teaching block's diagnosis (partial birth,
# teardown-world.sh) does not apply to at all -- `screen_birth` never passes `--pin submodule`
# today, but the narrower anchor keeps this match correct even if that ever changes, rather than
# silently misdiagnosing a stray `.autoharn` submodule as a partial kernel birth. A wording
# tweak to the parenthetical alone still leaves this substring intact.
_ALREADY_EXISTS_REFUSAL = "deployment.json already exists -- refusing to overwrite"


def _render_partial_birth_teaching(ui, cl, world, host, db, dest) -> None:
    """Ledger row 1790 finding 4 / finding 5 (NOT this build's kernel item -- ledger row 1792
    routes THAT one to the maintainer/Fable-spec lane): when `screen_birth`'s call to
    new-project.sh hits its OWN "already exists -- refusing to overwrite" refusal, teach the
    operator what state they are likely in and what to do next, rather than leaving a bare
    nonzero exit for them to puzzle out.

    What this function does NOT do: attempt teardown, retry with --force, or otherwise act --
    it only renders the teaching block and lets the checklist record REFUSED. The underlying
    kernel gap (s15-schema.sql is non-idempotent under re-application -- `new-project.sh --force
    --new-world` against a partially-born world hits 'no unique or exclusion constraint matching
    the ON CONFLICT specification' partway through) is kernel/lineage, frozen-record, and out of
    this build's scope; row 1792 is where that fix is tracked."""
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

    # --dir has teardown-world.sh itself remove the scaffold directory as part of its own
    # verified plan (rule 1: existing verbs, never a second implementation) -- this used to be
    # a separate, unconditional `shutil.rmtree(..., ignore_errors=True)` below, which claimed
    # WITNESSED regardless of whether the directory actually disappeared. Passing --dir here
    # instead makes removal part of teardown-world.sh's own printed plan and its own residue
    # check, and the claim below is checked against reality (os.path.isdir), not assumed.
    argv = _teardown_argv(scratch_world, db, host, extra=["--dir", scratch_dir])
    res = run_command(argv, stdin_text=f"{scratch_world}\n", dry_run=dry_run)
    teardown_ok = res.ok
    cl.add("rehearsal", "scratch teardown", ck.status_for(res),
           f"{'exit 0' if teardown_ok else f'exit {res.returncode}'}")

    # Under --dry-run, scratch_dir was never created (the birth above was never actually run),
    # so `os.path.isdir(scratch_dir)` answers a question this rehearsal did not ask -- it would
    # spuriously report WITNESSED "removed" for a directory that was never there to begin with.
    # Recorded WOULD_DO instead: nothing to check read-only, nothing faked.
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
# Birth
# ---------------------------------------------------------------------------------------------

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

    # Threading the governed-files CHOICE the fork-target screen recorded (governed_files.py's
    # own module docstring, the corrected single-writer design): `new-project.sh` is the one
    # script that actually writes `.claude/governed_files.json`, on every invocation,
    # unconditionally -- `--governed` is ITS own sanctioned flag for steering that write.
    # Omitted (no fork-target-screen choice in this run, e.g. an out-of-sequence
    # `--start-at birth`) means new-project.sh falls
    # back to its own bare *.py default with its own loud notice -- the same honest fallback
    # this flag already provides, never re-implemented here.
    extra = ["--name", name]
    if state.get("governed_patterns"):
        extra += ["--governed", governed_files.governed_flag_value(state["governed_patterns"])]
    argv = _new_project_argv(dest, world, db, host, extra=extra)
    res = run_command(argv, dry_run=state.get("dry_run", False))
    ok = res.ok
    dry_run = state.get("dry_run", False)
    # Finding 5 (ledger row 1790; the kernel item it borders, row 1792, is NOT this build's to
    # fix -- see _render_partial_birth_teaching's own docstring): new-project.sh's "already
    # exists -- refusing to overwrite" refusal only ever fires live (a dry run always reports a
    # SIMULATED ok=True, runner.run_command's own contract) -- render the teaching block instead
    # of the bare exit-code checklist row this refusal used to get.
    if not dry_run and not ok and _ALREADY_EXISTS_REFUSAL in res.output:
        _render_partial_birth_teaching(ui, cl, world, host, db, dest)
    else:
        cl.add("birth", "world birth", ck.status_for(res),
               f"{'exit 0' if ok else f'exit {res.returncode}'}")
    state["world"] = world
    state["dest"] = dest
    state["birth_ok"] = ok
    # `dest_would_exist` (read by screen_boundary's out-of-sequence-entry precondition check,
    # spec amendment 2026-07-19: "a dry run validates every precondition it can check read-only
    # and records honestly as DRY-SKIPPED any it cannot") -- a real birth's success means `dest`
    # really exists (os.path.isdir already tells the truth); a SIMULATED (`--dry-run`) success
    # means it WOULD, which is the one fact `os.path.isdir` cannot see for itself.
    if ok:
        state["dest_would_exist"] = True

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
# Principals & authority (design/FABLE-SETUP-TUI-PRINCIPALS-AUTHORITY-SPEC.md,
# commission ledger row 1727) -- sits BETWEEN Birth and Signed genesis (so the genesis bequeathal
# can name authority just constituted here). ON BY DEFAULT (confirm default=True), one recorded
# keypress to skip, never nagged again this run -- same benign-and-skippable test the genesis
# screen uses (every world already carries author/reviewer/commissioner). Driven from
# tools/setup_tui/principals_authority.py (this module's own signed_genesis.py-style split):
# every led act below goes through that module's functions, which themselves go through
# runner.run_command -- rule 1 and the --dry-run choke point stay structural properties. The
# propaedeutic discipline (spec §2) is BINDING: every act renders (a) the one-line lesson, (b)
# the exact `led` command (run_command's own echo), (c) the real streamed output, (d) the
# checklist entry -- lesson text lives in tools/setup_tui/principals_authority.py, ONE home.
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

    dry_run = state.get("dry_run", False)
    dest = state.get("dest") or ui.ask_text("Destination directory (the born world)")
    state["dest"] = dest

    # Out-of-sequence-entry amendment (design/FABLE-SETUP-TUI-SPEC.md 2026-07-19): validate
    # destination, ./led presence (legacy/led -- module docstring: the boundary is not
    # configured yet at this point in the flow), and lineage-head readability BEFORE offering
    # anything (spec §3). Same dest_would_exist trust pattern screen_signed_genesis/
    # screen_boundary already carry for a NORMAL-sequence dry run.
    if not os.path.isdir(dest):
        if dry_run and state.get("dest_would_exist"):
            cl.add("principals-authority", "destination exists", ck.DRY_SKIPPED,
                   f"'{dest}' would exist (created earlier in this dry run) -- not "
                   f"independently checkable read-only, recorded honestly rather than faked")
            cl.add("principals-authority", "legacy/led present", ck.DRY_SKIPPED,
                   "trusted along with the destination above -- always scaffolded by birth")
            cl.add("principals-authority", "world readable (lineage-head check)", ck.DRY_SKIPPED,
                   "no live world to read under a simulated destination")
            return state
        ui.say(f"  REFUSED: destination directory '{dest}' does not exist -- nothing to "
               f"constitute against. Run a birth first (or check the path), then retry this "
               f"screen.")
        cl.add("principals-authority", "destination exists", ck.REFUSED, f"'{dest}' not a directory")
        return state

    legacy_led = os.path.join(dest, "legacy", "led")
    if not os.path.isfile(legacy_led):
        ui.say(f"  REFUSED: no {legacy_led} -- this screen drives this world's own direct-psql "
               f"recovery shim (the boundary is not configured yet at this point in the flow, "
               f"the same reason the Signed genesis screen uses it). This does not look like a "
               f"world this project's own scaffold produced. Nothing done.")
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

    # The scaffold's own base, shown first (spec §1 item 1: "the screen first SHOWS the three
    # principals the scaffold already registered ... so the operator constitutes on top of a
    # visible base, not a mystery"). Read from the world's OWN view -- never re-derived.
    ui.say(f"  existing principals ({len(existing)}), from {dest}'s own principal_standing_"
           f"current view:")
    for p in existing:
        ui.say(f"    id={p['id']:<4} name={p['name']:<14} class={p['agent_class']:<9} "
               f"standing={p['standing']:<9} purpose={p.get('purpose') or '(none recorded)'}")
    cl.add("principals-authority", "existing principals shown", ck.WITNESSED,
           ", ".join(f"{p['name']}({p['agent_class']})" for p in existing) or "(none)")

    # --- item 1: register principals ---------------------------------------------------------
    while ui.confirm("Register a principal now?", default=False):
        ui.say("  " + principals_authority.LESSON_REGISTER)
        name = ui.ask_text("Principal name")
        agent_class = ui.ask_choice("Class (kernel/lineage/s40-schema.sql agent_class CHECK)",
                                     principals_authority.CLASS_CHOICES)
        purpose = ui.ask_text("Stated purpose (mandatory -- AC-2's 'account with a stated "
                               "purpose')")
        res, row_id = principals_authority.register_principal(dest, name, agent_class, purpose,
                                                                dry_run=dry_run)
        detail = f"row {row_id}" if row_id is not None else (
            "would write" if dry_run else res.output.strip()[-300:])
        cl.add("principals-authority", f"register principal '{name}'", ck.status_for(res), detail)
        if not res.ok and not dry_run:
            ui.say(f"  {res.output.strip().splitlines()[-1] if res.output.strip() else '(no output)'}")

    # --- item 2: authority bindings (s41 vocabulary, worlds at s41+) -------------------------
    available, reason = principals_authority.s41_status(dest)
    if not available:
        ui.say(f"  authority bindings section UNAVAILABLE: {reason}")
        cl.add("principals-authority", "authority bindings (s41)", ck.SKIPPED, reason)
    else:
        cl.add("principals-authority", "authority bindings (s41) available", ck.WITNESSED, reason)
        while ui.confirm("Grant a competence now?", default=False):
            ui.say("  " + principals_authority.LESSON_COMPETENCE)
            name = ui.ask_text("Principal name (must already be registered)")
            activity = ui.ask_text("Activity")
            band = ui.ask_text("Band")
            basis = ui.ask_text("Basis")
            res, row_id = principals_authority.grant_competence(dest, name, activity, band,
                                                                  basis, dry_run=dry_run)
            detail = f"row {row_id}" if row_id is not None else (
                "would write" if dry_run else res.output.strip()[-300:])
            cl.add("principals-authority", f"grant competence '{activity}' to '{name}'",
                   ck.status_for(res), detail)

        while ui.confirm("Add a typed relation now?", default=False):
            ui.say("  " + principals_authority.LESSON_RELATION)
            subj = ui.ask_text("Subject principal name")
            rel = ui.ask_choice("Relation (kernel/lineage/s41 principal_relation_check CHECK)",
                                 principals_authority.RELATION_CHOICES)
            obj = ui.ask_text("Object principal name")
            res, row_id = principals_authority.relate(dest, subj, rel, obj, dry_run=dry_run)
            detail = f"row {row_id}" if row_id is not None else (
                "would write" if dry_run else res.output.strip()[-300:])
            cl.add("principals-authority", f"relate '{subj}' {rel} '{obj}'",
                   ck.status_for(res), detail)

    # --- item 3: role charters, trap resolved -------------------------------------------------
    while ui.confirm("Register a role charter now?", default=False):
        ui.say("  " + principals_authority.LESSON_CHARTER)
        role = ui.ask_text("Role name (must be a registered principal)")
        path = ui.ask_text("Charter file path")
        if not principals_authority.is_registered(dest, role):
            ui.say(f"  '{role}' is not yet a registered principal -- the charter "
                   f"pre-registration trap (spec WP3).")
            if not ui.confirm(f"Register '{role}' now, in-flow, so the charter can proceed?",
                               default=True):
                manual = (f"{legacy_led} register-principal {role} <class> --purpose \"<why>\", "
                          f"then retry this charter")
                ui.say(f"  REFUSED: charter left unregistered -- manual command: {manual}")
                cl.add("principals-authority", f"charter '{role}' (unregistered, declined)",
                       ck.REFUSED, manual)
                continue
            agent_class = ui.ask_choice(f"Class for '{role}'",
                                         principals_authority.CLASS_CHOICES)
            purpose = ui.ask_text(f"Stated purpose for '{role}'")
            reg_res, reg_row_id = principals_authority.register_principal(
                dest, role, agent_class, purpose, dry_run=dry_run)
            reg_detail = f"row {reg_row_id}" if reg_row_id is not None else (
                "would write" if dry_run else reg_res.output.strip()[-300:])
            cl.add("principals-authority", f"register principal '{role}' (in-flow, from charter)",
                   ck.status_for(reg_res), reg_detail)
            if not dry_run and not reg_res.ok:
                cl.add("principals-authority", f"charter '{role}'", ck.REFUSED,
                       "in-flow registration failed -- charter not attempted")
                continue
        res = principals_authority.charter_register(dest, role, path, dry_run=dry_run)
        detail = ("would write" if dry_run else res.output.strip()[-300:])
        cl.add("principals-authority", f"charter '{role}' <- {path}", ck.status_for(res), detail)

    # --- item 4: the workflow on-ramp (pointer, not machinery) --------------------------------
    ui.say("  " + principals_authority.LESSON_WORKFLOW_POINTER)
    cl.add("principals-authority", "workflow on-ramp pointer", ck.WITNESSED,
           "spec §1 item 4 -- checklist-only note, no mechanism added")
    return state


# ---------------------------------------------------------------------------------------------
# Signed genesis (design/FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md, commission ledger
# rows 1724/1725) -- ON BY DEFAULT (confirm default=True), one recorded keypress to skip, never
# nagged again this run. Driven from tools/setup_tui/signed_genesis.py (this module's own
# pghba.py/probes.py split, applied to the new screen): every gpg/led act below goes through
# that module's functions, which themselves go through runner.run_command/write_file -- rule 1
# and the --dry-run choke point stay structural properties, not a per-screen promise.
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

    # Out-of-sequence-entry amendment (design/FABLE-SETUP-TUI-SPEC.md 2026-07-19): independently
    # validate every precondition the normal sequence (right after a successful Birth) would
    # have established, refusing legibly per precondition -- same `dest_would_exist` trust
    # pattern screen_boundary/screen_hydration already carry for a NORMAL-sequence dry run where
    # `dest` was never really created (birth's own write was simulated).
    if not os.path.isdir(dest):
        if dry_run and state.get("dest_would_exist"):
            cl.add("signed-genesis", "destination exists", ck.DRY_SKIPPED,
                   f"'{dest}' would exist (created earlier in this dry run) -- not "
                   f"independently checkable read-only, recorded honestly rather than faked")
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

    # --- designate the genesis commission (spec step 3: the world's own founding commission,
    # or write one now through led, FULL mode first) ---------------------------------------
    commission_id = None
    statement = None
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
            commission_id = latest["id"]
            statement = signed_genesis.fetch_commission_statement(dest, commission_id)
            cl.add("signed-genesis", "genesis commission designated", ck.WITNESSED,
                   f"row {commission_id} (existing)")

    if commission_id is None:
        ui.say("  no existing commission designated -- writing a new FOUNDING commission now "
               "(FULL mode, via legacy/led, since the boundary is not configured yet).")
        statement = ui.ask_text("Founding commission statement (the ask this world exists to "
                                 "carry out)")
        res, commission_id = signed_genesis.write_commission(dest, statement, dry_run=dry_run)
        detail = (f"row {commission_id}" if commission_id is not None else
                  ("would write (id known only once the write is real)" if dry_run
                   else f"exit {res.returncode}"))
        cl.add("signed-genesis", "genesis commission written", ck.status_for(res), detail)
        if not dry_run and commission_id is None:
            ui.say("  REFUSED: could not write the founding commission -- nothing to sign.")
            return state

    id_display = str(commission_id) if commission_id is not None else "<id>"

    # --- keygen: ONE fixed shape, no quiz (spec step 1) -------------------------------------
    is_scripted = isinstance(ui, ScriptedUi)
    if is_scripted:
        ui.say("  --scripted witnessing: a scratch GNUPGHOME + fixture passphrase is used "
               "(never the operator's own ~/.gnupg) -- gpg_trust.py's scratch-keyring "
               "mechanics, applied to a keygen rather than an import.")
        name = ui.ask_text("Key Name-Real (scripted/fixture keygen)",
                            default="AUTOHARN SETUP-TUI FIXTURE KEY -- THROWAWAY")
        email = ui.ask_text("Key Name-Email (scripted/fixture keygen)",
                             default="setup-tui-fixture@example.invalid")
        keygen = signed_genesis.keygen_scripted(name, email, dry_run=dry_run)
    else:
        name = ui.ask_text("Key Name-Real (your name)")
        email = ui.ask_text("Key Name-Email")
        gnupghome_in = ui.ask_text("GNUPGHOME to use for this key (blank = your default "
                                    "~/.gnupg)", default="")
        gnupghome = gnupghome_in or None

        # Resume-after-death (ledger row 1799 finding 7): BEFORE any keygen call, check whether
        # a prior run of THIS ceremony already left partial state for this name's key -- never
        # under --dry-run (a rehearsal never keygens for real either way, so there is no live
        # double-keygen hazard to guard against, and skipping this here keeps dry-run's own
        # WOULD-DO argv line for keygen_operator unconditional, per that mode's own doctrine).
        resume = None if dry_run else signed_genesis.detect_resumable(
            dest, name, gnupghome, commission_id)
        if resume is not None:
            ui.say("  a PARTIAL Signed genesis ceremony already appears to exist for this "
                   "key/world -- generating a fresh key now would strand the existing one "
                   "unrecorded, instead of resuming:")
            ui.say(f"    key exported ({resume.keys_path}): "
                   f"{'yes' if resume.key_exported else 'no'}")
            ui.say(f"    keys/README.md discharged: {'yes' if resume.readme_discharged else 'no'}"
                   + (f" (fingerprint {resume.fingerprint})" if resume.fingerprint else ""))
            if resume.asc_path:
                ui.say(f"    commission signed ({resume.asc_path}): "
                       f"{'yes' if resume.asc_signed else 'no'}")
            if resume.fingerprint and resume.secret_key_present:
                if ui.confirm("Reuse the existing key and continue from the unfinished steps, "
                               "instead of generating a NEW key?", default=True):
                    ui.say(f"  RESUMING with existing fingerprint {resume.fingerprint} -- no "
                           f"new key generated.")
                    # returncode=None (KeygenResult's own docstring): no gpg subprocess ran here
                    # at all -- this is a reuse of an already-verified existing key, the explicit
                    # derivable input rather than a hand-set ok=True (ledger row 1810 finding 2).
                    keygen = signed_genesis.KeygenResult(
                        gnupghome=gnupghome, fingerprint=resume.fingerprint,
                        argv=["(resumed -- existing key reused, no keygen invoked)"],
                        scratch=False, returncode=None)
                else:
                    ui.say("  REFUSED: declined to resume -- refusing to generate a SECOND key "
                           "over an existing partial ceremony (never a silent double-keygen). "
                           "Clean up the partial state by hand, or re-run and choose reuse.")
                    cl.add("signed-genesis", "keypair generated", ck.REFUSED,
                           "declined resume; refused rather than double-keygen")
                    return state
            else:
                ui.say("  REFUSED: partial ceremony state found, but no matching secret key is "
                       "present in this GNUPGHOME to safely reuse -- refusing to auto-delete "
                       "anything or silently generate a second key. Investigate by hand (the "
                       "recorded fingerprint may point at a different keyring).")
                cl.add("signed-genesis", "keypair generated", ck.REFUSED,
                       "partial ceremony state found, no reusable secret key -- refused")
                return state
        else:
            ui.say("  gpg will now prompt YOU, interactively, for a passphrase (its own pinentry "
                   "prompt -- never captured or scripted by this tool).")
            # Interactive child (design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md §2 item 4): gpg's own
            # pinentry needs the real terminal, not the Textual alternate screen. `ui.suspend()`
            # is a no-op under the plain/scripted backends (`Ui`'s own base-class contract,
            # `tools/setup_tui/ui.py`) -- this screen stays backend-blind either way.
            with ui.suspend():
                keygen = signed_genesis.keygen_operator(name, email, gnupghome, dry_run=dry_run)

    if dry_run:
        cl.add("signed-genesis", "keypair generated", ck.WOULD_DO,
               f"argv: {' '.join(keygen.argv)}")
    elif keygen.ok and keygen.fingerprint:
        cl.add("signed-genesis", "keypair generated", ck.WITNESSED,
               f"fingerprint {keygen.fingerprint}")
    else:
        ui.say("  REFUSED: keygen did not produce a usable secret key -- nothing to export or "
               "sign with. See the gpg output above.")
        cl.add("signed-genesis", "keypair generated", ck.REFUSED,
               "gpg keygen failed or produced no fingerprint")
        signed_genesis.teardown_scratch(keygen)
        return state

    gnupghome_display = keygen.gnupghome or "your default ~/.gnupg"
    ui.say(f"  private key custody: {gnupghome_display} -- this tool never reads, copies, or "
           f"moves it (user-guide/USER-GPG-TRUST-LAYER-FAQ.md §2: print the revocation "
           f"certificate and store it offline).")
    cl.add("signed-genesis", "private key custody (facts line, not a file)", ck.WITNESSED,
           gnupghome_display)

    # --- key lands where the record expects it (spec step 2) -------------------------------
    fpr_display = keygen.fingerprint or "<fingerprint>"
    filename = signed_genesis.key_filename(name)
    keys_path = os.path.join(dest, "keys", filename)
    _res, armored = signed_genesis.export_public_key(keygen.gnupghome, fpr_display, dry_run=dry_run)
    if not dry_run and not armored.strip():
        ui.say("  REFUSED: export produced no armored key text -- nothing written.")
        cl.add("signed-genesis", "public key exported", ck.REFUSED, "empty export output")
        signed_genesis.teardown_scratch(keygen)
        return state
    wrote = write_file(keys_path, armored, dry_run=dry_run)
    if wrote:
        ui.say(f"  wrote {keys_path}")
        cl.add("signed-genesis", "public key exported", ck.WITNESSED, keys_path)
    else:
        cl.add("signed-genesis", "public key exported", ck.WOULD_DO,
               f"{keys_path} :: {summarize_content(armored) if armored else '(dry-run placeholder)'}")

    readme_path, readme_text, wrote_readme = signed_genesis.discharge_keys_readme(
        dest, filename, fpr_display, name, email, dry_run=dry_run)
    if wrote_readme:
        cl.add("signed-genesis", "keys/README.md AWAITING-KEY discharged", ck.WITNESSED,
               readme_path)
    else:
        cl.add("signed-genesis", "keys/README.md AWAITING-KEY discharged", ck.WOULD_DO,
               f"{readme_path} :: {summarize_content(readme_text)}")

    # --- sign the genesis act (spec step 3) -------------------------------------------------
    # Interactive child, operator path only (design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md §2 item 4):
    # gpg's detach-sign can prompt via pinentry again here too (the agent's passphrase cache from
    # the keygen step above is not guaranteed still warm) -- suspend for the same reason as the
    # keygen call. The `--scripted` leg passes `--pinentry-mode loopback` with the fixture
    # passphrase (signed_genesis.sign_statement's own docstring) and is fully non-interactive, so
    # it never needs the terminal and is deliberately NOT suspended (`ScriptedUi.suspend()` is
    # already a no-op, but skipping the call entirely keeps the intent legible in the diff too).
    asc_path = os.path.join(dest, ".claude", f"commission-{id_display}.asc")
    if is_scripted:
        sres = signed_genesis.sign_statement(keygen.gnupghome, statement or "", asc_path,
                                              scripted=is_scripted, dry_run=dry_run)
    else:
        with ui.suspend():
            sres = signed_genesis.sign_statement(keygen.gnupghome, statement or "", asc_path,
                                                  scripted=is_scripted, dry_run=dry_run)
    cl.add("signed-genesis", "genesis commission signed", ck.status_for(sres), asc_path)

    # --- the gate verifies, not the keypress (spec step 4) ----------------------------------
    if dry_run:
        cl.add("signed-genesis", "ceremony gate (verify-commission)", ck.DRY_SKIPPED,
               "cannot verify a signature that was never made (spec §3) -- never a faked "
               "VERIFIED")
    elif commission_id is None:
        cl.add("signed-genesis", "ceremony gate (verify-commission)", ck.REFUSED,
               "no real commission id -- nothing to verify")
    else:
        vres, body = signed_genesis.run_verify_commission(dest, commission_id)
        verdict = body.get("verdict") or body.get("refusal") or f"exit {vres.returncode}"
        ui.say(f"  verify-commission verdict: {verdict}")
        if body.get("verdict") == "VERIFIED":
            cl.add("signed-genesis", "ceremony gate (verify-commission)", ck.WITNESSED,
                   f"VERIFIED: {str(body.get('detail', ''))[:200]}")
        else:
            ui.say(f"  REFUSED to record the ceremony WITNESSED -- the gate's own verdict was "
                   f"not VERIFIED ({verdict}); this renders the verb's own teaching honestly "
                   f"rather than shortcutting the gate.")
            cl.add("signed-genesis", "ceremony gate (verify-commission)", ck.REFUSED, verdict)

    signed_genesis.teardown_scratch(keygen)

    ui.say("  Signed genesis complete for this run: nothing further in this flow, or in the "
           "world's ongoing operation, demands another signature (spec §1 item 5) -- "
           "subsequent acts ride the ledger's own append-only record; SIGNED remains available "
           "for later commissions as a deliberate act (user-guide/USER-GPG-TRUST-LAYER-FAQ.md "
           "§5), never a nag.")
    cl.add("signed-genesis", "no ongoing signing burden after this screen", ck.WITNESSED,
           "spec §1 item 5 -- checklist-only note, no mechanism added")
    state["genesis_commission_id"] = commission_id
    return state


# ---------------------------------------------------------------------------------------------
# Boundary
# ---------------------------------------------------------------------------------------------

def screen_boundary(ui, cl, state):
    ui.banner(screen_banner("boundary"))
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
        cl.add("boundary", "boundary", ck.SKIPPED, skip_detail("boundary"))
        return state
    dry_run = state.get("dry_run", False)
    dest = state.get("dest") or ui.ask_text("Destination directory")
    state["dest"] = dest
    # Same pattern screen_hydration's led-existence check uses (os.path.isfile(led) before
    # ever touching it): a nonexistent dest is reachable here (--start-at boundary, or an
    # overridden birth gate above) and, unchecked, crashed with a raw FileNotFoundError
    # traceback at the `open(toml_path, "w")` write below instead of an explained refusal.
    #
    # Under --dry-run in the NORMAL sequence, `dest` genuinely does not exist yet -- birth's own
    # act was simulated, never taken (screen_birth sets `state["dest_would_exist"]` on a real OR
    # simulated success, the one fact this on-disk check cannot see for itself). The out-of-
    # sequence-entry amendment binds unchanged for the case that flag is ALSO absent (true
    # out-of-sequence entry, e.g. `--start-at boundary` with no prior birth in this run at all):
    # that still REFUSES, live or dry, because there is no precondition of any kind to trust.
    if not os.path.isdir(dest):
        if dry_run and state.get("dest_would_exist"):
            cl.add("boundary", "destination exists", ck.DRY_SKIPPED,
                   f"'{dest}' would exist (created earlier in this dry run) -- not "
                   f"independently checkable read-only, recorded honestly rather than faked")
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
    wrote = write_file(toml_path, toml_text, dry_run=dry_run)
    if wrote:
        cl.add("boundary", "multiplex TOML written", ck.WITNESSED, toml_path)
    else:
        cl.add("boundary", "multiplex TOML written", ck.WOULD_DO,
               f"{toml_path} :: {summarize_content(toml_text)}")

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
    # This re-scaffold rewrites the SAME `.claude/` wiring `screen_birth` wrote, unconditionally
    # -- governed_files.json included (governed_files.py's own module docstring: EVERY
    # new-project.sh invocation this package makes owns that path). Re-threading the operator's
    # fork-target-screen choice here is what keeps it from being silently clobbered back to the
    # bare *.py default by this later call -- the exact hazard an out-of-frame review caught in
    # this feature's first pass (a direct write at the fork-target screen that this same
    # re-scaffold call raced and lost to).
    if state.get("governed_patterns"):
        argv += ["--governed", governed_files.governed_flag_value(state["governed_patterns"])]
    res = run_command(argv, dry_run=dry_run)
    ok = res.ok
    cl.add("boundary", "deployment.json boundary keys written", ck.status_for(res),
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
        bg = start_background(argv, cwd=str(REPO_ROOT), dry_run=dry_run)
        if dry_run:
            cl.add("boundary", "service started", ck.WOULD_DO, f"{boundary_url}")
            # No live service exists to probe under --dry-run -- the same "prepared act, no
            # live verification" shape the PREPARED branch below already carries, so the two
            # post-start probes are DRY-SKIPPED, not faked.
            cl.add("boundary", "/health probe", ck.DRY_SKIPPED, "dry-run: service not started")
            cl.add("boundary", "/meta probe", ck.DRY_SKIPPED, "dry-run: service not started")
        else:
            proc = bg.proc
            state["boundary_proc"] = proc
            time.sleep(1.5)
            if proc.poll() is not None:
                leftover = proc.stdout.read() if proc.stdout else ""
                ui.say(f"  service exited immediately (rc={proc.returncode}): {leftover.strip()}")
                cl.add("boundary", "service started", ck.WITNESSED,
                       f"RED: exited rc={proc.returncode}: {leftover.strip()[:300]}")
            else:
                cl.add("boundary", "service started", ck.WITNESSED,
                       f"pid {proc.pid}, {boundary_url}")

            ok_h, status_h, body_h = probes.http_get_json(f"{boundary_url}/d/{world}/health")
            ui.say(f"  /health probe: {'GREEN' if ok_h else 'RED'} status={status_h} "
                   f"body={body_h}")
            cl.add("boundary", "/health probe", ck.WITNESSED, f"status={status_h} ok={ok_h}")

            ok_m, status_m, body_m = probes.http_get_json(f"{boundary_url}/d/{world}/meta")
            ui.say(f"  /meta probe: {'GREEN' if ok_m else 'RED'} status={status_m} "
                   f"body={body_m}")
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
# Observability
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
# Hydration
# ---------------------------------------------------------------------------------------------

def _run_decision(led: str, statement: str, dry_run: bool = False) -> tuple[str, str]:
    """Runs `led decision <statement>` (or, under `dry_run`, shows the exact argv and writes
    nothing -- `runner.run_command`'s own choke point), returning (status, detail): status is a
    `checklist` status via `ck.status_for`, detail is 'row <id>' when the row id can be parsed
    from real output, the verbatim statement when dry-run (spec: 'the ledger rows it would
    write verbatim'), else an exit-code fallback -- never a fabricated id. `runner.parse_row_id`
    is the one home for the parse (led's own `led: row <id> written.` convention,
    serving/boundary_cli_client.py `write_and_report`) -- ledger row 1799 finding 1."""
    argv = [led, "decision", statement]
    res = run_command(argv, dry_run=dry_run)
    if dry_run:
        return ck.status_for(res), f"would write: led decision {statement!r}"
    row_id = parse_row_id(res.output)
    detail = f"row {row_id}" if row_id else (f"exit {res.returncode}" if not res.ok else "written")
    return ck.status_for(res), detail


def screen_hydration(ui, cl, state):
    ui.banner(screen_banner("hydration"))
    if not ui.confirm("Run hydration now?", default=True):
        cl.add("hydration", "hydration", ck.SKIPPED, skip_detail("hydration"))
        return state
    dry_run = state.get("dry_run", False)
    dest = state.get("dest") or ui.ask_text("Destination directory (with a led shim)")
    state["dest"] = dest
    led = os.path.join(dest, "led")
    if not os.path.isfile(led):
        # Same dry-run precondition shape screen_boundary's destination-exists check uses: under
        # a normal-sequence dry run, birth's own scaffold write (which is what actually creates
        # the `led` shim) was simulated, never taken -- `led` genuinely does not exist on disk,
        # and that is not independently checkable read-only. A TRUE out-of-sequence entry with
        # no birth in this run at all (dest_would_exist absent) still REFUSES, live or dry.
        if state.get("dry_run") and state.get("dest_would_exist"):
            cl.add("hydration", "led present", ck.DRY_SKIPPED,
                   f"'{led}' would exist (written by birth earlier in this dry run) -- not "
                   f"independently checkable read-only, recorded honestly rather than faked")
        else:
            ui.say(f"  REFUSED: no ./led at {led} -- hydration writes only through led (v1 "
                   f"boundary), and none was found.")
            cl.add("hydration", "led present", ck.WITNESSED, f"RED: {led} not found")
            return state

    selected_fragments: list[str] = []
    _would_succeed = {ck.WITNESSED, ck.WOULD_DO}

    # fork_provenance / role_charters: unchanged, per-world facts (spec §3 "Relation to the
    # existing screen-8 items" -- these stay outside the durable-decisions catalog, they are not
    # durable decisions). adr_corpus and makespan_pointer's free-text prompts are RETIRED here,
    # absorbed into the catalog + ADR submenu below.
    _show_facts(ui, "hydration_fork_provenance")
    if not ui.confirm("Hydrate: fork provenance?", default=False):
        cl.add("hydration", "fork provenance", ck.SKIPPED, "operator declined")
    else:
        # High-assurance pointer (design/FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md §2): fork
        # provenance is one of the authority-carrying hydration acts §2 names explicitly -- one
        # added facts line, at the point of decision, pointing at the world's own copies of the
        # charter/GPG-trust docs (world-relative paths the scaffold ships).
        ui.say(f"  high-assurance act -- see {dest}/roles/README.md and, in the autoharn "
               f"checkout this world was scaffolded from, user-guide/USER-GPG-TRUST-LAYER-FAQ.md "
               f"/ design/MAINT-GPG-TRUST-LAYER.md.")
        statement = ui.ask_text("Statement for 'fork provenance' decision row")
        status, detail = _run_decision(led, statement, dry_run=dry_run)
        cl.add("hydration", "fork provenance", status, detail)

    _show_facts(ui, "hydration_role_charters")
    if not ui.confirm("Hydrate: role charters to register?", default=False):
        cl.add("hydration", "role charters to register", ck.SKIPPED, "operator declined")
    else:
        # High-assurance pointer (design/FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md §2): role-charter
        # registration binds authority -- named explicitly as the other §2 pointer site.
        ui.say(f"  high-assurance act -- see {dest}/roles/README.md and, in the autoharn "
               f"checkout this world was scaffolded from, user-guide/USER-GPG-TRUST-LAYER-FAQ.md "
               f"/ design/MAINT-GPG-TRUST-LAYER.md.")
        role = ui.ask_text("Role to charter (must already be a registered led principal)")
        path = ui.ask_text("Charter file path")
        argv = ["python3", str(REPO_ROOT / "tools" / "role_charter.py"), "register",
                role, path, "--led", led]
        res = run_command(argv, dry_run=dry_run)
        cl.add("hydration", "role charters to register", ck.status_for(res),
               f"{'exit 0' if res.ok else f'exit {res.returncode}'}")

    # The durable-decisions catalog (design/FABLE-SETUP-TUI-FEATURE-FACTS-SPEC.md §3): each
    # selection writes ONE `led decision` row and, if accepted, contributes its `claude_md`
    # fragment to the compiled section below (declined entries contribute NOTHING -- WD2's own
    # bar: "SKIPPED in the checklist, zero rows, zero fragments"). Under --dry-run, a selection
    # still contributes its fragment (WOULD_DO counts as "accepted" for CLAUDE.md-preview
    # purposes below) -- the whole point of a rehearsal is to show what the compiled file WOULD
    # contain, not stop short of it.
    for decision in durable_decisions.CATALOG:
        _show_facts(ui, f"hydration_{decision.slug.replace('-', '_')}")
        if not ui.confirm(f"Hydrate durable decision: {decision.slug}?", default=False):
            cl.add("hydration", decision.slug, ck.SKIPPED, "operator declined")
            continue
        status, detail = _run_decision(led, decision.hydrates, dry_run=dry_run)
        cl.add("hydration", decision.slug, status, detail)
        if status in _would_succeed:
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
        status, detail = _run_decision(led, statement, dry_run=dry_run)
        cl.add("hydration", f"adr adoption ({label})", status, detail)
        if status in _would_succeed:
            selected_fragments.append(
                durable_decisions.adr_claude_md_fragment(number, title, relpath))

    # CLAUDE.md compilation (spec §4) -- always runs once, even with zero fragments (an explicit
    # "(none selected at hydration time)" section is absence WITNESSED, not silently assumed by
    # leaving CLAUDE.md untouched). Idempotent: re-running this screen with the same selections
    # replaces only the marked section (WD4).
    claude_path, claude_text, wrote = durable_decisions.compile_claude_md(
        dest, selected_fragments, dry_run=dry_run)
    ui.say(f"  CLAUDE.md {'compiled' if wrote else 'would be compiled'}: "
           f"{len(selected_fragments)} fragment(s) -> {claude_path}")
    if wrote:
        cl.add("hydration", "CLAUDE.md durable-decisions section compiled", ck.WITNESSED,
               f"{len(selected_fragments)} fragment(s) -> {claude_path}")
    else:
        cl.add("hydration", "CLAUDE.md durable-decisions section compiled", ck.WOULD_DO,
               f"{claude_path} :: {summarize_content(claude_text)}")
    return state


# ---------------------------------------------------------------------------------------------
# Checklist
# ---------------------------------------------------------------------------------------------

def screen_checklist(ui, cl, state):
    ui.banner(screen_banner("checklist"))
    ui.say(cl.render())
    dry_run = state.get("dry_run", False)
    dest = state.get("dest")
    # Same dry-run precondition shape screen_boundary's destination-exists check uses: a real
    # directory (WDR1's own case) is checked for real; a directory that WOULD exist from an
    # earlier act in THIS dry run (state["dest_would_exist"]) is trusted for the same reason
    # os.path.isdir cannot see it -- nothing was actually created.
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

# Drift-proofing (ledger row 1790, finding 3): banner numbers ("N/11 Title") and checklist
# skip-detail strings ("operator skipped screen N") were hand-typed in two separate places per
# screen and drifted apart the moment principals-authority/signed-genesis were inserted between
# Birth and Boundary -- boundary/observability/hydration's skip details kept the PRE-insertion
# numbers while their banners correctly picked up the new ones. Both are now derived from THIS
# list's own order, the one place a screen's position is decided -- an insertion here updates
# every consumer at once; there is nothing left to hand-renumber.
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
    """`"N/TOTAL Title"` for `slug`, derived from SCREENS' own order + SCREEN_TITLES -- the one
    call site every screen_*'s `ui.banner(...)` call uses (see the module-level comment above
    SCREEN_TITLES)."""
    return f"{SCREEN_NUMBER[slug]}/{SCREEN_TOTAL} {SCREEN_TITLES[slug]}"


def skip_detail(slug: str, verb: str = "operator skipped") -> str:
    """`"<verb> screen N"` for `slug`'s checklist skip-detail row, same derivation as
    `screen_banner` above -- the two can no longer disagree."""
    return f"{verb} screen {SCREEN_NUMBER[slug]}"
