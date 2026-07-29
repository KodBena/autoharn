#!/usr/bin/env python3
"""seen-red/setup-tui-config-extension/run_fixtures.py -- the witness plan for work item
setup-tui-config-extension (ledger row 685's audit / row 693): the seven coverage gaps closed in
`tools/setup_tui/steps_boundary.py` (log_level, identity_enforcement hub-wide + per-deployment
override, sse_poll_interval_secs, max_sse_clients), the new `tools/setup_tui/steps_courier.py`
section (self/self_base derived, counterparts a ListField), the `birth_stamp_secret` feature
fact, and `config_schema.toml`'s closed --from-config keys for all of the above.

Cases:
  (a) DEFAULTS-UNCHANGED REGRESSION -- driving `steps_boundary.submit`/`steps_courier.submit`
      with every new field left at its own default emits BYTE-IDENTICAL output to before this
      build (boundary-multiplex.toml unchanged; courier.toml not written at all).
  (b) BOUNDARY NEW FIELDS THROUGH THE REAL LOADER -- non-default answers for all five fields,
      the emitted boundary-multiplex.toml parses through
      `serving.boundary_multiplex_config.load_multiplex_config_with_deployment_identity` (the
      REAL loader, no synthetic parser) with every value intact, including the per-deployment
      identity_enforcement override differing from the hub-wide default.
  (c) COURIER THROUGH THE REAL LOADER -- a non-empty counterparts list emits a courier.toml that
      parses through `libexec/autoharn/courier`'s own real `load_courier_config` with self/
      self_base/authn/counterparts intact; an EMPTY counterparts list emits no file at all.
  (d) CONFIG-SCHEMA ROUND-TRIP -- `config_file.render_toml`/`load_config_file`/`validate` round-
      trips every new key (green control), and a typo'd key is refused, naming it (red control).
  (e) PILOT-DRIVEN END-TO-END -- the REAL Tree+Form app (`tools.setup_tui.tui_app`, Textual
      `Pilot`/`run_test()`, the current post-rebuild surface, no synthetic screen): navigates to
      the real "boundary" section, sets the five new fields via real widget interactions (RadioSet
      clicks for the three ChoiceFields, typed Input text for the two numeric TextFields -- the
      SAME `.value =`/click mechanism seen-red/setup-tui-configtree-journey's own module docstring
      documents as posting the identical `Changed` message a live keystroke/click does), reads the
      persisted live-field slot back via `fields.get_field_value`, and confirms `steps_boundary.
      submit` with that SAME answers dict reaches the exact resolved values; navigates to the
      real "courier" section, drives the real Add-modal flow (click Add, type into the modal's
      Input fields, click Save -- the identical flow seen-red/setup-tui-configtree-journey's own
      case 24 already proved for a MasterDetailFieldWidget, exercised here against a plain
      `ListFieldWidget`/`AddItemModal` instead) to add one counterpart row, and confirms
      `steps_courier.submit` reaches it.

Zero residue: every scratch destination lives under a fixture-owned tempdir, removed in `finally`.
No live Postgres/GPG/boundary-service needed anywhere in this fixture (every case drives `submit`
directly or via Pilot against synthetic-but-real state, never a live birth) -- so nothing here is
UNEXERCISED for lack of HARNESS_PGHOST; case (e) is UNEXERCISED only if `textual` is not
importable (mirrors every sibling setup_tui fixture's own guard).

Lazy imports are banned (CLAUDE.md, 2026-07-02)."""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)

try:
    from textual.widgets import Button, Input, RadioSet, Tree
except ImportError:
    Button = Input = RadioSet = Tree = None  # type: ignore[assignment,misc]

from tools.configtree import NodeId  # noqa: E402
from tools.configtree.fields import default_of, get_field_value  # noqa: E402
from tools.configtree.ids import FieldName, ScopedFieldKey  # noqa: E402
from tools.setup_tui import boundary_config_values as bcv  # noqa: E402
from tools.setup_tui import config_file, steps, steps_boundary, steps_courier  # noqa: E402
from tools.setup_tui.checklist import Checklist  # noqa: E402
from tools.setup_tui.plan import Plan  # noqa: E402

try:
    from tools.setup_tui import tui_app
except ImportError:
    tui_app = None  # type: ignore[assignment]

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

sys.path.insert(0, os.path.join(REPO, "serving"))
sys.path.insert(0, os.path.join(REPO, "filing"))
import boundary_multiplex_config as bmc  # noqa: E402

import importlib.util  # noqa: E402
from importlib.machinery import SourceFileLoader  # noqa: E402

_COURIER_VERB_PATH = os.path.join(REPO, "libexec", "autoharn", "courier")


def _load_courier_module():
    """`libexec/autoharn/courier` is a script (no `.py` suffix) -- loaded via `SourceFileLoader`
    rather than a normal import (there is no importable module name for it), the same shape any
    other repo-root-verb-as-a-library consumer would need."""
    loader = SourceFileLoader("courier_verb_fixture", _COURIER_VERB_PATH)
    spec = importlib.util.spec_from_loader("courier_verb_fixture", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def _boundary_state(dest: str, world: str = "cfgextworld") -> dict:
    return {
        "_checklist": Checklist(), "_plan": Plan(), "_repo_root": __import__("pathlib").Path(REPO),
        "dest": dest, "dest_would_exist": True, "world": world, "birth_ok": True,
    }


def _boundary_toml_from(state: dict, answers: dict) -> "tuple[object, str]":
    result = steps_boundary.submit(dict(state), answers)
    assert result.ok, f"steps_boundary.submit refused: {result.errors}"
    for e in state["_plan"].entries:
        if e.item == "multiplex TOML written":
            return result, e.act.content
    raise AssertionError("no 'multiplex TOML written' plan entry -- submit() logic changed shape")


def case_boundary_defaults_unchanged(scratch: str) -> None:
    dest = os.path.join(scratch, "a-boundary-defaults")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "deployment.json"), "w") as f:
        json.dump({}, f)
    state = _boundary_state(dest)
    fields = {str(f.name): f for f in steps_boundary.fields(state)}
    answers = {name: default_of(f) for name, f in fields.items()}
    _, content = _boundary_toml_from(state, answers)
    expected = ('[deployments.cfgextworld]\npghost = "192.168.122.1"\npgdatabase = "toy"\n'
                'pguser = "cfgextworld_rw"\npgschema = "cfgextworld"\npgkern = "cfgextworld_kernel"\n')
    assert content == expected, (
        f"case a RED: defaults-untouched boundary-multiplex.toml is NOT byte-identical to the "
        f"pre-existing shape:\n  got={content!r}\n  want={expected!r}")
    print("case a ok: every new boundary field left at its own default emits BYTE-IDENTICAL "
          "boundary-multiplex.toml to before this build (no top-level keys at all)")


def case_courier_defaults_unchanged(scratch: str) -> None:
    dest = os.path.join(scratch, "a-courier-defaults")
    os.makedirs(dest, exist_ok=True)
    state = {"_checklist": Checklist(), "_plan": Plan(), "dest": dest, "world": "cfgextworld",
             "boundary_url": "http://127.0.0.1:8420"}
    fields = {str(f.name): f for f in steps_courier.fields(state)}
    answers = {name: default_of(f) for name, f in fields.items()}
    result = steps_courier.submit(dict(state), answers)
    assert result.ok, f"steps_courier.submit refused: {result.errors}"
    written = [e for e in state["_plan"].entries if e.item == "courier.toml written"]
    assert not written, f"case a (courier) RED: courier.toml WAS queued with zero counterparts: {written}"
    assert not os.path.isfile(os.path.join(dest, "courier.toml"))
    print("case a ok (courier): zero counterparts entered -- courier.toml is NOT queued for "
          "writing at all")


def case_boundary_new_fields_real_loader(scratch: str) -> None:
    dest = os.path.join(scratch, "b-boundary-new-fields")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "deployment.json"), "w") as f:
        json.dump({}, f)
    state = _boundary_state(dest, world="cfgextb")
    fields = {str(f.name): f for f in steps_boundary.fields(state)}
    answers = {name: default_of(f) for name, f in fields.items()}
    answers.update({
        "log_level": "DEBUG", "identity_enforcement": "enforce",
        "identity_enforcement_override": "grace",
        "sse_poll_interval_secs": "5.5", "max_sse_clients": "42",
    })
    _, content = _boundary_toml_from(state, answers)
    toml_path = os.path.join(dest, "boundary-multiplex.toml")
    with open(toml_path, "w") as f:
        f.write(content)
    deployments, log_level, identity_enforcement, poll, clients, by_dep = (
        bmc.load_multiplex_config_with_deployment_identity(toml_path))
    assert "cfgextb" in deployments, deployments
    assert log_level == "DEBUG", log_level
    assert identity_enforcement == "enforce", identity_enforcement
    assert poll == 5.5, poll
    assert clients == 42, clients
    assert by_dep["cfgextb"].value == "grace", (
        f"per-deployment override did not win over the hub-wide default: {by_dep}")
    print("case b ok: boundary-multiplex.toml with all five new fields set to non-default "
          "values parses through the REAL serving.boundary_multiplex_config loader with every "
          "value intact -- including the per-deployment override ('grace') differing from the "
          "hub-wide default ('enforce')")

    # RED control: an invalid sse_poll_interval_secs is refused by submit() itself, before ever
    # reaching the real loader.
    state2 = _boundary_state(dest, world="cfgextb2")
    answers_bad = dict(answers)
    answers_bad["sse_poll_interval_secs"] = "0"
    result_bad = steps_boundary.submit(state2, answers_bad)
    assert not result_bad.ok and "sse_poll_interval_secs" in result_bad.errors, (
        f"case b RED control failed: out-of-range sse_poll_interval_secs was not refused: "
        f"{result_bad.errors}")
    print("case b ok (RED control): an out-of-range sse_poll_interval_secs ('0') is refused by "
          "steps_boundary.submit itself, naming the field")


def case_courier_new_fields_real_loader(scratch: str) -> None:
    dest = os.path.join(scratch, "c-courier-new-fields")
    os.makedirs(dest, exist_ok=True)
    state = {"_checklist": Checklist(), "_plan": Plan(), "dest": dest, "world": "cfgextc",
             "boundary_url": "http://127.0.0.1:8421"}
    answers = {"counterparts": [{"world": "cfgextcpeer", "base_url": "http://127.0.0.1:8500"}]}
    result = steps_courier.submit(dict(state), answers)
    assert result.ok, f"steps_courier.submit refused: {result.errors}"
    toml_path = None
    for e in state["_plan"].entries:
        if e.item == "courier.toml written":
            toml_path = e.act.path
            with open(toml_path, "w") as f:
                f.write(e.act.content)
    assert toml_path is not None, "no 'courier.toml written' plan entry -- submit() logic changed shape"
    mod = _load_courier_module()
    cfg = mod.load_courier_config(__import__("pathlib").Path(toml_path))
    assert cfg["self"] == "cfgextc", cfg
    assert cfg["self_base"] == "http://127.0.0.1:8421", cfg
    assert cfg["counterparts"] == {"cfgextcpeer": "http://127.0.0.1:8500"}, cfg
    print("case c ok: courier.toml with one counterpart parses through the REAL "
          "libexec/autoharn/courier load_courier_config with self/self_base/counterparts intact "
          f"({cfg})")

    # RED control: a counterpart named the same as this world's own name is refused.
    state2 = dict(state); state2["_plan"] = Plan(); state2["_checklist"] = Checklist()
    bad_answers = {"counterparts": [{"world": "cfgextc", "base_url": "http://127.0.0.1:8500"}]}
    result_bad = steps_courier.submit(state2, bad_answers)
    assert not result_bad.ok and "counterparts" in result_bad.errors, (
        f"case c RED control failed: a self-referencing counterpart was not refused: "
        f"{result_bad.errors}")
    print("case c ok (RED control): a counterpart named the same as this world's own name is "
          "refused by steps_courier.submit, naming the field")


def _minimal_valid_values() -> dict[str, object]:
    return {
        "features.portable_adrs": True, "features.vendored_skills": True,
        "features.panel_extension": False, "features.makespan_tier": "off",
        "substrate.run": False, "rehearsal.run": False, "birth.run": False,
        "principals_authority.run": False, "signed_genesis.run": False,
        "boundary.start_now": False, "observability.run": False, "hydration.run": False,
    }


VALID_HEADER = {"config_format": 1, "produced_by": "fixture", "source": "fixture"}


def case_config_schema_round_trip(scratch: str) -> None:
    values = {**_minimal_valid_values(),
              "boundary.log_level": "DEBUG", "boundary.identity_enforcement": "enforce",
              "boundary.identity_enforcement_override": "grace",
              "boundary.sse_poll_interval_secs": 5.5, "boundary.max_sse_clients": 42,
              "courier.counterparts": [{"world": "cfgextcpeer", "base_url": "http://127.0.0.1:8500"}]}
    doc = config_file.ConfigDoc(path="<synthetic>", header=VALID_HEADER, values=values)
    config_file.validate(doc, require_complete=True)  # GREEN control: no refusal.

    rendered = config_file.render_toml(values, produced_by="fixture", source="fixture")
    path = os.path.join(scratch, "d-roundtrip.toml")
    with open(path, "w") as f:
        f.write(rendered)
    doc2 = config_file.load_config_file(path)
    config_file.validate(doc2, require_complete=True)
    assert doc2.values == values, (
        f"case d RED: round-trip is not a fixed point:\n  a={values}\n  b={doc2.values}")
    print("case d ok: every new key (boundary.log_level/identity_enforcement/"
          "identity_enforcement_override/sse_poll_interval_secs/max_sse_clients, "
          "courier.counterparts) round-trips through render_toml -> load_config_file -> "
          "validate as a fixed point")

    # RED control: a typo'd key refuses, naming it.
    bad = {**_minimal_valid_values(), "boundary.log_leveel": "DEBUG"}
    try:
        config_file.validate(config_file.ConfigDoc(path="<synthetic>", header=VALID_HEADER,
                                                     values=bad), require_complete=True)
        raise AssertionError("case d RED control failed: typo'd key was not refused")
    except config_file.ConfigError as exc:
        assert "boundary.log_leveel" in str(exc), exc
    print("case d ok (RED control): a typo'd key ('boundary.log_leveel') is refused, named in "
          "the refusal")


def _find_node(tree, kind: str, slug: "str | None" = None):
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


async def _case_pilot_driven_async(scratch: str) -> None:
    dest = os.path.join(scratch, "e-pilot")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "deployment.json"), "w") as f:
        json.dump({}, f)

    state = steps.initial_state(dry_run=True)
    state.update({"dest": dest, "dest_would_exist": True, "world": "cfgextpilot",
                  "birth_ok": True,
                  # courier's own `_blocked_needs_boundary` gate needs this PRESENT AT APP
                  # CONSTRUCTION TIME (a `SectionPane`'s own `.state` is `app.state`, a SEPARATE
                  # dict object from this one for any top-level key not already shared, see the
                  # "_live_fields" note just below) -- pre-seeded here rather than set later
                  # through steps_boundary's own submit, since this case is testing the boundary
                  # and courier FIELDS, not the tree's blocked/unblocked transition (that is
                  # seen-red/setup-tui-configtree-journey's own case 1's job).
                  "boundary_url": "http://127.0.0.1:8420"})
    # `ConfigTreeApp.__init__` shallow-copies `initial_state` (`self.state = dict(initial_state or
    # {})`) -- pre-seeding the "_live_fields" NESTED dict here, before `build_app`, means the
    # shallow copy shares THIS SAME nested dict object with `app.state`, so every write-through
    # this Pilot session drives is visible on the OUTER `state` variable too (the same trick
    # seen-red/setup-tui-config-file's own case v relies on, `build_live_field_overrides`'s pre-
    # seeded overrides dict there) -- without this, `get_field_value(state, ...)` below would read
    # stale defaults off a dict the running app never actually mutates.
    state["_live_fields"] = {}

    app = tui_app.build_app(state, dry_run=True)
    async with app.run_test(size=(150, 400)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)

        # --- BOUNDARY: three ChoiceFields (RadioSet click) + two TextFields (typed Input) -------
        b_node = _find_node(tree, "section", "boundary")
        tree.select_node(b_node)
        tree.action_select_cursor()
        await pilot.pause()

        log_rs = app.query_one("#pane-boundary #ct-field-log_level", RadioSet)
        debug_idx = [str(v) for v, _ in steps_boundary._LOG_LEVEL_CHOICES].index("DEBUG")
        await pilot.click(log_rs.children[debug_idx])
        await pilot.pause()

        ie_rs = app.query_one("#pane-boundary #ct-field-identity_enforcement", RadioSet)
        enforce_idx = [str(v) for v, _ in steps_boundary._IDENTITY_ENFORCEMENT_CHOICES].index("enforce")
        await pilot.click(ie_rs.children[enforce_idx])
        await pilot.pause()

        ieo_rs = app.query_one("#pane-boundary #ct-field-identity_enforcement_override", RadioSet)
        grace_idx = [str(v) for v, _ in steps_boundary._IDENTITY_ENFORCEMENT_OVERRIDE_CHOICES].index("grace")
        await pilot.click(ieo_rs.children[grace_idx])
        await pilot.pause()

        poll_input = app.query_one("#pane-boundary #ct-field-sse_poll_interval_secs", Input)
        poll_input.value = ""
        await pilot.click(poll_input)
        for ch in "5.5":
            await pilot.press(ch)
        await pilot.pause()

        clients_input = app.query_one("#pane-boundary #ct-field-max_sse_clients", Input)
        clients_input.value = ""
        await pilot.click(clients_input)
        for ch in "42":
            await pilot.press(ch)
        await pilot.pause()

        b_fields = {str(f.name): f for f in steps_boundary.fields(state)}
        b_answers = {name: get_field_value(state, NodeId("boundary"), f)
                     for name, f in b_fields.items()}
        assert b_answers["log_level"] == "DEBUG", b_answers
        assert b_answers["identity_enforcement"] == "enforce", b_answers
        assert b_answers["identity_enforcement_override"] == "grace", b_answers
        assert b_answers["sse_poll_interval_secs"] == "5.5", b_answers
        assert b_answers["max_sse_clients"] == "42", b_answers

        b_result = steps_boundary.submit(dict(state), b_answers)
        assert b_result.ok, f"steps_boundary.submit refused: {b_result.errors}"
        state.update(b_result.state_updates)
        assert state["boundary_log_level"] == "DEBUG"
        assert state["boundary_identity_enforcement_override"] == "grace"
        assert state["boundary_sse_poll_interval_secs"] == 5.5
        assert state["boundary_max_sse_clients"] == 42
        print("case e ok (boundary): three real RadioSet clicks + two real typed Inputs thread "
              "through get_field_value into the exact answers dict steps_boundary.submit "
              "resolves, matching the widget state end to end")

        # --- COURIER: the real Add-modal flow (plain ListField, not MasterDetail) --------------
        c_node = _find_node(tree, "section", "courier")
        tree.select_node(c_node)
        tree.action_select_cursor()
        await pilot.pause()

        add_btn = app.query_one("#pane-courier #ct-field-counterparts-add", Button)
        add_btn.scroll_visible(animate=False)
        await pilot.pause()
        await pilot.click(add_btn)
        await pilot.pause()
        modal = app.screen
        world_input = modal.query_one("#ct-field-world", Input)
        await pilot.click(world_input)
        for ch in "cfgextcpeer":
            await pilot.press(ch)
        await pilot.pause()
        url_input = modal.query_one("#ct-field-base_url", Input)
        await pilot.click(url_input)
        for ch in "http://127.0.0.1:8500":
            await pilot.press(ch)
        await pilot.pause()
        save_btn = modal.query_one("#ct-modal-save", Button)
        await pilot.click(save_btn)
        await pilot.pause()

        c_fields = {str(f.name): f for f in steps_courier.fields(state)}
        c_answers = {name: get_field_value(state, NodeId("courier"), f)
                     for name, f in c_fields.items()}
        assert c_answers["counterparts"] == [
            {"world": "cfgextcpeer", "base_url": "http://127.0.0.1:8500"}], c_answers
        c_result = steps_courier.submit(dict(state), c_answers)
        assert c_result.ok, f"steps_courier.submit refused: {c_result.errors}"
        assert c_result.state_updates["courier_counterparts"] == [
            {"world": "cfgextcpeer", "base_url": "http://127.0.0.1:8500"}]
        print("case e ok (courier): a real Add-button click + real typed modal Input fields + "
              "real Save-button click lands a counterpart row through the SAME AddItemModal a "
              "plain ListField uses, and steps_courier.submit reaches it")


def case_pilot_driven(scratch: str) -> None:
    asyncio.run(_case_pilot_driven_async(scratch))


def case_typed_construction() -> None:
    """Fix round (review row 776, finding 1): one RED (out-of-contract value refused at
    construction, message naming the contract) + one GREEN (valid value round-trips through
    `.value`/`.raw`) pair per typed home in `tools/setup_tui/boundary_config_values.py` -- the
    five NEW boundary-multiplex values no longer travel as bare str/float/int without a single
    constructing home checking their contract. `bcv` is imported at module level above (CLAUDE.md's
    lazy-import ban)."""
    # LogLevel: RED (unknown level, message names the vocabulary) + GREEN (round-trips).
    try:
        bcv.LogLevel.parse("BOGUS")
        raise AssertionError("case f RED failed: LogLevel accepted an out-of-vocabulary value")
    except ValueError as exc:
        assert "LEVELS" in str(exc) or "DEBUG" in str(exc), exc
    assert bcv.LogLevel.parse("DEBUG").value == "DEBUG"
    assert bcv.LogLevel.default().value == "INFO"

    # IdentityEnforcementPosture (hub-wide default, re-used from serving/boundary_multiplex_config.py):
    # RED (unknown posture, message names both key locations) + GREEN (round-trips).
    try:
        bcv.IdentityEnforcementPosture.parse("BOGUS", where="identity_enforcement (hub-wide default)",
                                              path=__import__("pathlib").Path("<fixture>"))
        raise AssertionError("case f RED failed: IdentityEnforcementPosture accepted an "
                              "out-of-vocabulary value")
    except bcv.boundary_multiplex_config.MultiplexConfigError as exc:
        assert "grace" in str(exc) and "enforce" in str(exc), exc
    assert bcv.IdentityEnforcementPosture.parse(
        "enforce", where="identity_enforcement (hub-wide default)",
        path=__import__("pathlib").Path("<fixture>")).value == "enforce"
    assert bcv.IdentityEnforcementPosture.default().value == "grace"

    # IdentityEnforcementOverride: RED (unknown override value, same teach-text as the hub-wide
    # default) + GREEN (both "inherit" and a valid posture round-trip; .inherits flags correctly).
    try:
        bcv.IdentityEnforcementOverride.parse("BOGUS")
        raise AssertionError("case f RED failed: IdentityEnforcementOverride accepted an "
                              "out-of-vocabulary value")
    except bcv.boundary_multiplex_config.MultiplexConfigError as exc:
        assert "grace" in str(exc) and "enforce" in str(exc), exc
    assert bcv.IdentityEnforcementOverride.parse("inherit").inherits is True
    assert bcv.IdentityEnforcementOverride.parse("grace").inherits is False
    assert bcv.IdentityEnforcementOverride.parse("grace").raw == "grace"
    assert bcv.IdentityEnforcementOverride.default().raw == bcv.IDENTITY_ENFORCEMENT_OVERRIDE_INHERIT

    # SsePollIntervalSecs: RED (zero, out of (0, MAX]; message names the bound) + GREEN.
    try:
        bcv.SsePollIntervalSecs.parse("0")
        raise AssertionError("case f RED failed: SsePollIntervalSecs accepted 0")
    except ValueError as exc:
        assert "0" in str(exc) and str(bcv.boundary_multiplex_config.MAX_SSE_POLL_INTERVAL_SECS) in str(exc), exc
    assert bcv.SsePollIntervalSecs.parse("5.5").value == 5.5
    assert bcv.SsePollIntervalSecs.default().value == bcv.boundary_multiplex_config.DEFAULT_SSE_POLL_INTERVAL_SECS

    # MaxSseClients: RED (zero, out of [1, CEILING]; message names the bound) + GREEN.
    try:
        bcv.MaxSseClients.parse("0")
        raise AssertionError("case f RED failed: MaxSseClients accepted 0")
    except ValueError as exc:
        assert "0" in str(exc) and str(bcv.boundary_multiplex_config.MAX_SSE_CLIENTS_CEILING) in str(exc), exc
    assert bcv.MaxSseClients.parse("42").value == 42
    assert bcv.MaxSseClients.default().value == bcv.boundary_multiplex_config.DEFAULT_MAX_SSE_CLIENTS

    print("case f ok: each of the five typed homes in boundary_config_values.py refuses an "
          "out-of-contract value at construction (naming the contract) and round-trips a valid "
          "one -- LogLevel, IdentityEnforcementPosture, IdentityEnforcementOverride, "
          "SsePollIntervalSecs, MaxSseClients")


def main() -> int:
    scratch = tempfile.mkdtemp(prefix="setup-tui-config-extension-")
    try:
        case_boundary_defaults_unchanged(scratch)
        case_courier_defaults_unchanged(scratch)
        case_boundary_new_fields_real_loader(scratch)
        case_courier_new_fields_real_loader(scratch)
        case_config_schema_round_trip(scratch)
        if tui_app is None:
            print("case e UNEXERCISED: 'textual' is not importable on this interpreter -- case "
                  "e drives the real Tree+Form app via Pilot/run_test()")
        else:
            case_pilot_driven(scratch)
        case_typed_construction()
        print("ALL CASES OK (or honestly UNEXERCISED) -- setup-tui-config-extension "
              "(ledger row 685's audit / row 693), zero residue")
        return 0
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
