#!/usr/bin/env python3
"""seen-red/setup-tui-config-file/run_fixtures.py -- the six-case witness plan
design/FABLE-SETUP-TUI-CONFIG-FILE-SPEC.md §6 names, ledger row 1944:

  (i)   --from-config full dry-run birth from the shipped exemplar, deterministic, zero prompts.
  (ii)  missing-key refusal names every missing key at once (red-then-green: per-key red
        controls, then a green control with every required key present).
  (iii) unknown-key refusal (red-then-green, same shape) -- including the two NAMED excluded
        keys ("world"/"dest") that must never validate even though an author might reach for
        them.
  (iv)  world-exists rejection on BOTH the schema leg (a live Postgres probe) and the sentinel
        leg (a destination directory whose `.autoharn-world.json` names a different world).
  (v)   --initial-config's scripted leg: a config default threads through the SAME navigation
        prior-answers seam a real revisit uses, and an individual prompt can still override it.
  (vi)  round-trip (spec §4's self-application property, checked mechanically): a LIVE birth's
        own saved `world-config.toml`, re-applied via `--from-config` to a second world, saves
        the SAME resolved decision set again -- a fixed point, not a byte-for-byte match against
        the hand-authored exemplar (which is archaeology, not machine output).

Cases (i)/(v)/(vi) need a live, reachable Postgres host (HARNESS_PGHOST/EPISTEMIC_PGHOST) --
UNEXERCISED, not FAILED, when neither is set (same convention seen-red/setup-tui-principals-
authority already uses). Case (v) ALSO needs `textual` importable (it drives the real Tree+Form
app via Pilot/`run_test()`, the current post-2026-07-22-rebuild surface for what `--initial-
config` does -- there is no textual-free way to exercise it any more, `--scripted`'s own
subprocess-and-parse-stdout shape having been deleted with that rebuild); UNEXERCISED, not
FAILED, on an interpreter without it -- guarded by a top-level `try`/`except ImportError` mirroring
`tools/setup_tui/app.py`'s own `tui_app` import guard (CLAUDE.md's lazy-import ban is about
function-BODY imports; a guarded top-of-file import is the project's own established idiom for an
optional heavy dependency, not a lazy import). Every scratch destination lives under a
fixture-owned tempdir, and every scratch world this fixture BIRTHS is torn down in a `finally`,
real teardown-world.sh (`--force-non-scratch` -- fixture-generated world names do not match the
scratch-safe pattern), zero residue regardless of outcome.

Real subprocess invocations of the actual CLI entry point (no mocks), matching every sibling
setup_tui fixture's own Rule 1 bar. Lazy imports banned."""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)

try:
    from textual.widgets import Input, Tree
except ImportError:
    Input = Tree = None  # type: ignore[assignment,misc]

from tools.configtree import NodeId  # noqa: E402
from tools.configtree.fields import get_field_value  # noqa: E402
from tools.setup_tui import config_file, config_seam, destination, steps  # noqa: E402
from tools.setup_tui import steps_principals_authority, steps_substrate  # noqa: E402

try:
    from tools.setup_tui import tui_app
except ImportError:
    tui_app = None  # type: ignore[assignment]

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own
# environment before any subprocess is spawned -- inherited by the whole process tree
# this fixture starts, so every repo-root verb invocation anywhere downstream carries it.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

PGHOST = os.environ.get("HARNESS_PGHOST") or os.environ.get("EPISTEMIC_PGHOST")
PGDB = "toy"
EXEMPLAR = os.path.join(REPO, "bootstrap", "templates", "known-good-blank.toml")


def run_app(argv: list[str], cwd: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "tools.setup_tui.app"] + argv, cwd=REPO,
                           capture_output=True, text=True, timeout=timeout,
                           env={**os.environ, "HARNESS_PGHOST": PGHOST or ""})


def teardown(world: str, dest: str) -> None:
    subprocess.run(
        ["bash", os.path.join(REPO, "bootstrap", "teardown-world.sh"), world,
         "--db", PGDB, "--host", PGHOST, "--dir", dest, "--force-non-scratch"],
        input=f"{world}\n", capture_output=True, text=True, timeout=60,
    )


def _minimal_valid_values() -> dict[str, object]:
    # legacy-led-retirement inventory pass (ledger row 1149/1150): "boundary.configure" retired
    # (boundary is now mandatory, no decline gate); "boundary.start_now" moves from a
    # contextually-required scalar to REQUIRED_GATES (see config_file.py's own comment).
    return {
        # deploy-feature-manifest (ledger row 1274/1322): "features" is unconditional (no gate
        # of its own, mirrors "boundary"/"fork_target") -- its four scalars are REQUIRED_GATES
        # members exactly the way "boundary.start_now" already is (config_file.py's own comment).
        "features.portable_adrs": True, "features.vendored_skills": True,
        "features.panel_extension": False, "features.makespan_tier": "off",
        "substrate.run": False, "rehearsal.run": False, "birth.run": False,
        "principals_authority.run": False, "signed_genesis.run": False,
        "boundary.start_now": False, "observability.run": False, "hydration.run": False,
    }


def _doc(header: dict, values: dict) -> config_file.ConfigDoc:
    return config_file.ConfigDoc(path="<synthetic>", header=header, values=values)


VALID_HEADER = {"config_format": 1, "produced_by": "fixture", "source": "fixture"}


def case_missing_key() -> None:
    for missing in config_file.REQUIRED_GATES:
        values = _minimal_valid_values()
        del values[missing]
        try:
            config_file.validate(_doc(VALID_HEADER, values), require_complete=True)
            raise AssertionError(f"case ii RED control failed: '{missing}' absent did not refuse")
        except config_file.ConfigError as exc:
            assert missing in str(exc), f"case ii: refusal did not name '{missing}': {exc}"
    # all-missing-at-once: every gate absent -> every gate named in ONE refusal (spec §2: "naming
    # every missing key at once", never a first-one-wins early exit).
    try:
        config_file.validate(_doc({}, {}), require_complete=True)
        raise AssertionError("case ii RED control failed: fully empty doc did not refuse")
    except config_file.ConfigError as exc:
        msg = str(exc)
        for gate in config_file.REQUIRED_GATES:
            assert gate in msg, f"case ii: all-at-once refusal missing '{gate}': {msg}"
        for hk in sorted(config_file.HEADER_KEYS if hasattr(config_file, "HEADER_KEYS")
                          else {"config_format", "produced_by", "source"}):
            assert hk in msg, f"case ii: all-at-once refusal missing header field '{hk}': {msg}"
    # GREEN control: every required key present -> no refusal.
    config_file.validate(_doc(VALID_HEADER, _minimal_valid_values()), require_complete=True)
    print("case ii ok: missing-key refusal names every missing key (per-key red controls, "
          "an all-missing-at-once control naming every gate+header field in ONE refusal), "
          "green control passes")


def case_unknown_key() -> None:
    for bad_key in ("world", "dest", "destination", "substrate.bogus_typo_field"):
        values = {**_minimal_valid_values(), bad_key: "anything"}
        try:
            config_file.validate(_doc(VALID_HEADER, values), require_complete=True)
            raise AssertionError(f"case iii RED control failed: '{bad_key}' was not refused")
        except config_file.ConfigError as exc:
            assert bad_key in str(exc), f"case iii: refusal did not name '{bad_key}': {exc}"
    # GREEN control: the same minimal doc, no stray key -> no refusal.
    config_file.validate(_doc(VALID_HEADER, _minimal_valid_values()), require_complete=True)
    print("case iii ok: unknown-key refusal (including the two named-excluded CLI parameters, "
          "'world'/'dest', which are never legal config content), green control passes")


def case_world_exists_schema_leg(scratch: str) -> None:
    probe_world = f"cfgfixprobe{int(time.time())}"
    cp = subprocess.run(["psql", "-h", PGHOST, "-d", PGDB, "-c",
                          f"CREATE SCHEMA {probe_world}"], capture_output=True, text=True,
                         timeout=20)
    assert cp.returncode == 0, f"case iv setup: could not create probe schema: {cp.stderr}"
    try:
        dest = os.path.join(scratch, "iv-schema-leg")
        os.makedirs(dest, exist_ok=True)
        refusal = config_seam.check_world_and_dest(world=probe_world, dest=dest, host=PGHOST,
                                                     db=PGDB)
        assert refusal is not None and probe_world in refusal and "schema" in refusal, (
            f"case iv (schema leg): expected a REFUSED-and-named world-exists rejection, "
            f"got: {refusal!r}")
        # GREEN control: a name that does NOT exist as a schema is not refused on this leg.
        clean = config_seam.check_world_and_dest(
            world=f"{probe_world}neverexists", dest=dest, host=PGHOST, db=PGDB)
        assert clean is None, f"case iv (schema leg) green control: {clean!r}"
    finally:
        subprocess.run(["psql", "-h", PGHOST, "-d", PGDB, "-c",
                         f"DROP SCHEMA IF EXISTS {probe_world} CASCADE"],
                        capture_output=True, text=True, timeout=20)
    print("case iv ok (schema leg): world name REFUSED when its schema already exists on the "
          "target Postgres, named in the refusal; a genuinely-fresh name is not refused "
          "(green control)")


def case_world_exists_sentinel_leg(scratch: str) -> None:
    dest = os.path.join(scratch, "iv-sentinel-leg")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "deployment.json"), "w") as f:
        json.dump({"name": "sentinel-world-a"}, f)
    os.makedirs(os.path.join(dest, "legacy"), exist_ok=True)
    with open(os.path.join(dest, "legacy", "led"), "w") as f:
        f.write("#!/bin/sh\n")
    with open(os.path.join(dest, destination.SENTINEL_NAME), "w") as f:
        json.dump({"world": "sentinel-world-a", "run": "", "born": "2026-01-01T00:00:00Z",
                   "autoharn_commit": "deadbeef", "schema": destination.SENTINEL_SCHEMA}, f)
    refusal = config_seam.check_world_and_dest(world="sentinel-world-b", dest=dest, host=PGHOST,
                                                 db=PGDB)
    assert refusal is not None and "sentinel-world-a" in refusal and "sentinel" in refusal, (
        f"case iv (sentinel leg): expected a refusal naming the sentinel's own world, "
        f"got: {refusal!r}")
    # GREEN control: the SAME world name the sentinel already names is not refused on this leg
    # (still refused on the destination-classification leg below, since the dir is AUTOHARN_
    # COMPLETE -- checked separately so this control isolates the sentinel-contradiction check).
    same_name = config_seam.check_world_and_dest(world="sentinel-world-a", dest=dest, host=PGHOST,
                                                   db=PGDB)
    assert same_name is not None and "classifies as" in same_name, (
        f"case iv (sentinel leg) green control: expected the destination-classification leg "
        f"(not the sentinel-contradiction leg) to be the one refusing: {same_name!r}")
    print("case iv ok (sentinel leg): world name REFUSED when the destination's own sentinel "
          "names a DIFFERENT world, that world named in the refusal")


def _find_node(tree: "Tree", kind: str, slug: "str | None" = None):
    """Mirrors seen-red/setup-tui-seeded-value-visibility/run_fixtures.py's own helper of the
    same name -- walks the sidebar Tree for the first node matching (kind, slug)."""
    def _walk(node):
        for child in node.children:
            data = child.data or {}
            if data.get("kind") == kind and (slug is None or data.get("slug") == slug):
                return child
            found = _walk(child)
            if found is not None:
                return found
        return None
    return _walk(tree.root)


async def _case_initial_config_override_async(scratch: str) -> None:
    """REWRITE (work item setup-tui-config-file-retired-flags, row 1327/1336 arc): the ORIGINAL
    case v drove `--scripted`/`--start-at` -- both retired dead since the 2026-07-22 Tree+Form
    rebuild (design/FABLE-SETUP-TUI-REBUILD-SPEC.md; `--scripted`'s own `ScriptedUi` machinery is
    deleted, `config_seam.py`'s own module docstring names this explicitly) -- so this case has
    errored ('unrecognized arguments: --scripted --start-at ...') on every actual run since that
    rebuild, never caught because seen-red's own re-execution had not been exercised against it.

    COVERAGE CHECK (the claim this rewrite verifies, not assumes): seen-red/setup-tui-seeded-
    value-visibility/run_fixtures.py's case 3 already proves HALF of what the original case v
    asserted -- that a config-seeded value threads through as a field's own live value (there,
    via the in-UI "Load a configuration" action; `app.py`'s own comment confirms `--initial-
    config` calls the SAME `build_live_field_overrides` seeding function that action calls, so
    the mechanism is genuinely shared, not merely similarly-shaped). It does NOT cover the
    other half -- that an operator's own explicit answer OVERRIDES the seeded default, and the
    seeded value does not leak through once overridden -- no other fixture in this tree checks
    that. Retiring case v outright would silently drop that assertion; this rewrite carries it
    over, driven against the CURRENT surface (`tools.setup_tui.tui_app`'s real Tree+Form app via
    Textual's `Pilot`, `run_test()` -- the same mechanism seeded-value-visibility itself uses,
    since `--initial-config` launches the real interactive Textual app and needs a TTY, not a
    subprocess-and-parse-stdout shape `--scripted` used to provide).

    KEEP LEG: builds `state`/`_live_fields` exactly the way `app.py`'s own `_run_textual` does
    for `--initial-config` (`config_seam.build_live_field_overrides` +
    `build_initial_state_overrides`, the P1 SSOT both `--initial-config` and "Load a
    configuration" call) from a config seeding `substrate.db = "cfgfixtureinitdb"`, launches the
    real app, navigates to the substrate section, and reads the `db_existing` Input widget's OWN
    `.value` straight off the live app -- it must show the seeded value, unedited (the field's
    own live default, not a scripted-answers artifact).

    OVERRIDE LEG: the SAME app, the operator types a different value into that SAME Input widget
    (a real Textual `Input.Changed` message, `panes.py`'s own `on_input_changed` write-through --
    the identical path a real keystroke drives). Verified at BOTH ends of the write-through
    chain: (1) the widget's own `.value` shows the typed value, not the seeded one; (2) the
    persisted live-field slot (`fields.get_field_value`, the ONE place every `submit()` reads a
    field's current value from) agrees; (3) calling `steps_substrate.submit` with that SAME
    live-field-derived answers dict (the real function a commit sweep calls, not a mock) reports
    `state_updates["db"]` as the operator's typed value, never the seeded one -- the override
    reaches the exact function the original case v's stdout assertion was a proxy for."""
    values = {**_minimal_valid_values(), "substrate.run": True, "substrate.path": "existing",
              "substrate.host": "192.168.122.1", "substrate.db": "cfgfixtureinitdb"}
    cfg_path = os.path.join(scratch, "v-initial.toml")
    with open(cfg_path, "w") as f:
        f.write(config_file.render_toml(values, produced_by="fixture", source="fixture"))
    doc = config_file.load_config_file(cfg_path)
    config_file.validate(doc, require_complete=False)

    # Same construction app.py's own --initial-config handling performs (tools/setup_tui/app.py,
    # `_run_textual`): build_live_field_overrides seeds state["_live_fields"],
    # build_initial_state_overrides seeds the bare shared-state keys (pghost/db/...).
    state = steps.initial_state(dry_run=True)
    overrides, seeded, _unseedable = config_seam.build_live_field_overrides(doc)
    assert "substrate.db -> substrate.db_existing" in seeded, (
        f"case v setup: substrate.db was not seeded to db_existing as expected: {seeded!r}")
    state.setdefault("_live_fields", {}).update(overrides)
    state.update(config_seam.build_initial_state_overrides(doc))

    app = tui_app.build_app(state, dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)
        sub_node = _find_node(tree, "section", "substrate")
        tree.select_node(sub_node)
        tree.action_select_cursor()
        await pilot.pause()

        db_input = app.query_one("#pane-substrate #ct-field-db_existing", Input)

        # KEEP LEG: unedited, the field shows the seeded config default.
        assert db_input.value == "cfgfixtureinitdb", (
            f"case v (keep leg): expected the seeded config default 'cfgfixtureinitdb' as the "
            f"field's own live value, got {db_input.value!r}")
        seeded_value = get_field_value(
            state, NodeId("substrate"),
            next(fld for fld in steps_substrate.fields(state) if str(fld.name) == "db_existing"))
        assert seeded_value == "cfgfixtureinitdb", (
            f"case v (keep leg): the persisted live-field slot disagrees with the widget: "
            f"{seeded_value!r}")

        # OVERRIDE LEG: a real operator keystroke path -- Input.value assignment posts the same
        # Input.Changed message a live keystroke does, driving panes.py's own on_input_changed
        # write-through (verified below at both the widget and the persisted-slot end).
        db_input.value = "operatorchosendb"
        await pilot.pause()
        assert db_input.value == "operatorchosendb", (
            f"case v (override leg): the widget did not accept the operator's own answer: "
            f"{db_input.value!r}")
        overridden_value = get_field_value(
            state, NodeId("substrate"),
            next(fld for fld in steps_substrate.fields(state) if str(fld.name) == "db_existing"))
        assert overridden_value == "operatorchosendb", (
            f"case v (override leg): the seeded config default leaked through the write-through "
            f"choke point -- persisted live-field slot is {overridden_value!r}, expected the "
            f"operator's own answer")

        # The override reaches the REAL submit() a commit sweep would call, not just the widget.
        fields_by_name = {str(fld.name): fld for fld in steps_substrate.fields(state)}
        answers = {name: get_field_value(state, NodeId("substrate"), fld)
                   for name, fld in fields_by_name.items()}
        result = steps_substrate.submit(dict(state), answers)
        assert result.ok, f"case v (override leg): substrate.submit refused: {result.errors}"
        assert result.state_updates.get("db") == "operatorchosendb", (
            f"case v (override leg): substrate.submit's own resolved 'db' is "
            f"{result.state_updates.get('db')!r}, expected the operator's typed answer, not the "
            f"seeded config default")

    print("case v ok: a config-seeded value threads through --initial-config's SAME "
          "build_live_field_overrides seeding as the in-UI 'Load a configuration' action "
          "(seen-red/setup-tui-seeded-value-visibility's own case 3 covers that half); an "
          "operator's own typed answer overrides it end to end -- widget, persisted live-field "
          "slot, and the real substrate.submit() result all agree, the seeded default never "
          "leaking through (the half no other fixture covers, carried over from the retired "
          "--scripted case v rather than dropped)")


def case_initial_config_override(scratch: str) -> None:
    asyncio.run(_case_initial_config_override_async(scratch))


def case_full_dry_run_and_roundtrip(scratch: str) -> None:
    world1 = f"cfgfxa{int(time.time())}"
    dest1 = os.path.join(scratch, "vi-world1")
    # (i) full dry-run birth from the shipped exemplar, deterministic, zero prompts.
    cp = run_app(["--from-config", EXEMPLAR, "--world", world1, dest1, "--dry-run"], scratch)
    out = cp.stdout + cp.stderr
    assert cp.returncode == 0, f"case i: exit {cp.returncode}: {out[-2000:]}"
    assert "ScriptExhausted" not in out and "Traceback" not in out, (
        f"case i: not a clean zero-prompt run: {out[-2000:]}")
    assert "world-config.toml" in out and "WOULD-DO" in out, (
        f"case i: self-save was not queued: {out[-2000:]}")
    for expect in ("register-principal maintainer human", "register-principal orchestrator model",
                   "principal relate orchestrator acts-for maintainer",
                   "new-project.sh", "boundary_service"):
        assert expect in out, f"case i: expected content missing ({expect!r}): {out[-2000:]}"
    print("case i ok: --from-config drives a full eleven-screen dry-run birth from the shipped "
          "exemplar to a clean exit 0, zero prompts left to a human, every queued act visible")

    if not PGHOST:
        print("case vi UNEXERCISED: no HARNESS_PGHOST/EPISTEMIC_PGHOST -- needs a live, "
              "reachable Postgres host for two real births")
        return

    world2 = f"cfgfxb{int(time.time())}"
    dest2 = os.path.join(scratch, "vi-world2")
    boundary_pid1 = boundary_pid2 = None
    try:
        cp1 = run_app(["--from-config", EXEMPLAR, "--world", world1, dest1], scratch, timeout=180)
        out1 = cp1.stdout + cp1.stderr
        assert cp1.returncode == 0, f"case vi: live birth 1 exit {cp1.returncode}: {out1[-2000:]}"
        boundary_pid1 = _discover_boundary_pid(dest1)
        cfg_a = os.path.join(dest1, "world-config.toml")
        assert os.path.isfile(cfg_a), f"case vi: {cfg_a} was not saved: {out1[-2000:]}"
        doc_a = config_file.load_config_file(cfg_a)
        config_file.validate(doc_a, require_complete=True)

        cp2 = run_app(["--from-config", cfg_a, "--world", world2, dest2], scratch, timeout=180)
        out2 = cp2.stdout + cp2.stderr
        assert cp2.returncode == 0, f"case vi: live birth 2 (re-applied) exit {cp2.returncode}: {out2[-2000:]}"
        boundary_pid2 = _discover_boundary_pid(dest2)
        cfg_b = os.path.join(dest2, "world-config.toml")
        assert os.path.isfile(cfg_b), f"case vi: {cfg_b} was not saved: {out2[-2000:]}"
        doc_b = config_file.load_config_file(cfg_b)
        config_file.validate(doc_b, require_complete=True)

        assert doc_a.values == doc_b.values, (
            f"case vi: the round-trip is not a fixed point:\n  a={doc_a.values}\n  "
            f"b={doc_b.values}")
        print("case vi ok: a live birth's own saved world-config.toml, re-applied via "
              "--from-config to a SECOND world, saves the SAME resolved decision set again "
              "(a fixed point, checked mechanically)")
    finally:
        _kill_boundary(boundary_pid1)
        _kill_boundary(boundary_pid2)
        teardown(world1, dest1)
        teardown(world2, dest2)


def _discover_boundary_pid(dest: str) -> "int | None":
    """PID-TRACKING, THE HONEST SHAPE (work item setup-tui-fixture-kill-boundary-never-matches,
    ledger row 1334/1337): the fixture spawns this process (transitively, through `run_app`'s own
    `python -m tools.setup_tui.app --from-config ...` subprocess, which `steps_boundary.py`'s
    `BackgroundAct` Popen()s as ITS OWN child before that subprocess exits and the boundary
    service is reparented) -- it should never need pgrep GUESSING to find it again later. The OLD
    code guessed `boundary_service.*{world}` at KILL time, long after spawn -- but
    `steps_boundary.py` launches the service with `--config <dest>/boundary-multiplex.toml
    --port <port>`, an argv that NEVER contains the bare world name at all (verified: `grep -n
    boundary_service tools/setup_tui/steps_boundary.py` shows only `--config`/`--port`), so that
    pattern never matched, ANY --new-world/--profile-tracker run of it, ever -- every live case-vi
    run leaked a boundary_service process, silently, on the shared scratch host (five found
    already-orphaned from earlier sessions before this fix, ports 8420-8425).

    THIS discovery call runs EXACTLY ONCE, immediately after the birth subprocess (`cp1`/`cp2`)
    reports success -- at that point the service has ALREADY answered its own health probe
    (`steps_boundary.py`'s own commit-time health gate, `probes.wait_for_health`, blocks the
    birth subprocess's own exit until it does), so the process is provably up and its argv is
    provably stable. The match target is `--config <dest>/boundary-multiplex.toml` -- a path
    unique to THIS fixture's own scratch tempdir (`tempfile.mkdtemp`), not a name that could ever
    collide with an unrelated process the way a bare world-name substring guess could. Returns the
    discovered pid (an `int`, captured ONCE, held for the rest of this case's lifetime) or `None`
    if boundary never started (e.g. no venv interpreter found -- steps_boundary.py's own
    documented decline path) -- teardown becomes a no-op in that case, never a guess."""
    target = os.path.join(dest, "boundary-multiplex.toml")
    cp = subprocess.run(["pgrep", "-f", f"boundary_service.*--config {target}"],
                         capture_output=True, text=True, timeout=10)
    pids = [int(p) for p in cp.stdout.split()]
    if not pids:
        return None
    assert len(pids) == 1, f"case vi: expected exactly one boundary_service for {target}, found {pids}"
    return pids[0]


def _kill_boundary(pid: "int | None") -> None:
    """Terminate-with-wait, mirroring row 1332's own wait-confirm-escalate posture in miniature
    (a graceful SIGTERM first, confirmed via `/proc/<pid>` liveness polling rather than assumed,
    escalating to SIGKILL only if the process is still alive after the grace window) -- no
    pgrep guessing at kill time, just the pid `_discover_boundary_pid` already captured."""
    if pid is None:
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return  # already gone
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if not os.path.exists(f"/proc/{pid}"):
            return  # confirmed gone -- SIGTERM was enough
        time.sleep(0.2)
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def case_plan_key_capture(scratch: str) -> None:
    """config-seam-plan-key-silent-loss (ledger rows 1330/1331): `capture_resolved_config`
    used to read `state.get("plan")` -- every `steps_*.py` module's own real state key is
    `state["_plan"]` (`app.py`/`steps.py`'s own `initial_state`, `steps_principals_authority.
    submit` and its siblings all agree) -- so `principals_authority.register`/`.competences`/
    `.relations` always captured as `[]` in world-config.toml's self-save, a SILENT loss on
    every wizard run since fbbe7b547d ("loadable config files"), exit 0, nothing to catch it.
    This case drives the REAL wizard step (`steps_principals_authority.submit`, no mock, the
    same function `screens.py` calls for a live keystroke) to queue one register/competence/
    relation row, then captures + renders `world-config.toml` through the real `config_seam`/
    `config_file` path, and asserts the rows actually reached the rendered file -- the exact
    round-trip an operator relies on."""
    dest = os.path.join(scratch, "vii-plan-key")
    os.makedirs(dest, exist_ok=True)
    state = steps.initial_state(dry_run=True)
    state["dest"] = dest
    # post-birth dry-run shape (the same convention steps_rehearsal_birth.py's own dry-run leg
    # uses): principals-authority is reachable once a destination is recorded, real filesystem
    # birth not required to prove the CAPTURE path this case targets.
    state["dest_would_exist"] = True
    answers = {
        "register": [{"name": "fixtureprincipal", "agent_class": "model",
                       "purpose": "plan-key witness"}],
        "competences": [{"name": "fixtureprincipal", "activity": "witness",
                          "band": "b1", "basis": "fixture"}],
        "relations": [{"subject": "fixtureprincipal", "relation": "acts-for",
                        "object": "maintainer"}],
        "charters": [],
    }
    result = steps_principals_authority.submit(state, answers)
    assert result.ok, f"case vii setup: principals-authority submit refused: {result.errors}"
    state.update(result.state_updates)

    resolved = config_seam.capture_resolved_config(state)
    rendered = config_file.render_toml(
        resolved, produced_by="fixture", source="fixture (case vii, plan-key witness)")

    assert resolved.get("principals_authority.register"), (
        "case vii RED: principals_authority.register captured empty -- the plan-key silent "
        f"loss is back (resolved={resolved.get('principals_authority.register')!r})")
    assert resolved.get("principals_authority.competences"), (
        "case vii RED: principals_authority.competences captured empty -- the plan-key silent "
        f"loss is back (resolved={resolved.get('principals_authority.competences')!r})")
    assert resolved.get("principals_authority.relations"), (
        "case vii RED: principals_authority.relations captured empty -- the plan-key silent "
        f"loss is back (resolved={resolved.get('principals_authority.relations')!r})")
    assert "fixtureprincipal" in rendered, (
        "case vii RED: the registered principal's own name is absent from the rendered "
        f"world-config.toml -- silent loss:\n{rendered}")

    # THE NET (row 1330's own postmortem question, ADR-0000 (b)): a state dict missing the
    # '_plan' infrastructure key entirely is malformed, not "no plan yet" -- capture_resolved_
    # config must fail LOUDLY on it, never silently degrade to an empty plan (that silent
    # degrade is the exact shape of the bug this whole case exists to catch).
    broken_state = dict(state)
    del broken_state["_plan"]
    try:
        config_seam.capture_resolved_config(broken_state)
        raise AssertionError(
            "case vii (net) RED: capture_resolved_config silently accepted a state dict with "
            "no '_plan' key instead of failing loudly -- the net the plan-key postmortem "
            "asked for is not actually there")
    except KeyError as exc:
        assert "_plan" in str(exc), f"case vii (net): KeyError did not name '_plan': {exc}"

    print("case vii ok: capture_resolved_config reads the wizard's real '_plan' state key -- a "
          "registered principal's register/competences/relations rows survive into the "
          "rendered world-config.toml (plan-key silent-loss regression guard, ledger row 1330)")


def main() -> int:
    scratch = tempfile.mkdtemp(prefix="setup-tui-config-file-")
    try:
        case_missing_key()
        case_unknown_key()
        case_plan_key_capture(scratch)
        if PGHOST:
            case_world_exists_schema_leg(scratch)
        else:
            print("case iv (schema leg) UNEXERCISED: no HARNESS_PGHOST/EPISTEMIC_PGHOST")
        case_world_exists_sentinel_leg(scratch)  # read-only, no live Postgres needed
        if not PGHOST:
            print("case v UNEXERCISED: no HARNESS_PGHOST/EPISTEMIC_PGHOST")
        elif tui_app is None:
            print("case v UNEXERCISED: 'textual' is not importable on this interpreter -- "
                  "case v drives the real Tree+Form app via Pilot/run_test()")
        else:
            case_initial_config_override(scratch)
        case_full_dry_run_and_roundtrip(scratch)
        print("ALL CASES OK (or honestly UNEXERCISED) -- setup_tui config-file feature "
              "(design/FABLE-SETUP-TUI-CONFIG-FILE-SPEC.md), zero residue")
        return 0
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
