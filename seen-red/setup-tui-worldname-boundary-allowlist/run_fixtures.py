#!/usr/bin/env python3
"""seen-red/setup-tui-worldname-boundary-allowlist/run_fixtures.py -- both-polarity proof for work
item setup-tui-worldname-boundary-allowlist (row 1317 arc; flagged by the track-work-retirement
builder, out of that build's own scope).

THE DEFECT. `tools/setup_tui/idtypes.py`'s `WorldName` (BEFORE this fix) enforced only the shell/
SQL identifier allowlist (`[A-Za-z0-9_]+`) -- looser than the boundary service's own deployment-
slug contract (`serving/boundary_multiplex_config.py` spec §2, `[a-z0-9-]{1,64}`, lowercase only,
no underscore). `tools/setup_tui/steps_boundary.py`'s `submit()` writes `world` straight into
`boundary-multiplex.toml`'s `[deployments.{world}]` table key -- so a TUI-valid name like
`MyWorld` (uppercase, legal shell/SQL identifier) reached that write silently and only broke, at
the boundary SERVICE's own config-load gate, later and elsewhere: exactly the "silently break
downstream" class this fixture reproduces and then closes.

RED (the REAL, current `steps_boundary.py` -- its own validation LOGIC is unchanged by this build,
only a clarifying comment was added -- re-exec'd with `tools/setup_tui/idtypes.py` pinned to its
PRE-FIX source, commit PRE_FIX_COMMIT below, so the ONE thing under test is the contract
`WorldName` enforces, not `steps_boundary.py`'s own code): `WorldName.parse("MyWorld")` succeeds
under the pinned contract, `steps_boundary.submit()` accepts it and queues a
`boundary-multiplex.toml` WriteAct whose content the REAL, unmodified, CURRENT
`serving.boundary_multiplex_config.load_multiplex_config` then refuses to load
(`MultiplexConfigError`, deployment name does not match `_DEPLOYMENT_NAME_RE`) -- a real specimen
of the exact downstream break, produced on scratch, no live Postgres touched (the boundary write
is only QUEUED as a Plan entry here, never executed as a real commit; parsing that queued TOML
text is the real, current boundary-config loader, not a mock).

GREEN (current `idtypes.py`, current `steps_boundary.py`, no pinning at all): the SAME name is
refused at `WorldName` CONSTRUCTION, before `steps_boundary.submit()` ever builds a Plan entry --
the refusal text names the boundary-slug contract it protects. A clean name (`myworld123`) passes
end to end: `steps_boundary.submit()` succeeds AND the real `load_multiplex_config` accepts the
resulting TOML without complaint.

MECHANISM (no lazy imports -- CLAUDE.md, 2026-07-02): every module this file needs is imported
ONCE, at the top, in the ordinary way. The PRE-FIX `idtypes.py` source is fetched via `git show`
and `exec`'d into a synthetic module object -- `exec`/`compile` are function calls, not `import`
statements, so building a pinned module this way is not a lazy import (the same distinction the
law itself draws: "an `import` statement anywhere inside a function body is a violation" --
nothing here is an `import` statement, lazy or otherwise, inside a function). While that pinned
module object is built, `sys.modules['tools.setup_tui.idtypes']` is swapped to it for the single
`exec` call that needs it resolvable there (Python 3.13's dataclass processing looks up
`cls.__module__` in `sys.modules` while decorating `WorldName`/`DestPath`), then immediately
restored in a `finally` -- the real, current `idtypes` module (already imported at this file's own
top) is never mutated or re-imported, so every GREEN-leg check below uses the SAME `WorldName`/
`WorldNameError`/`steps_boundary` objects Python bound when this file itself was loaded.
`steps_boundary.py`'s own (unchanged) CURRENT source text is re-`exec`'d against the pinned
idtypes for the RED leg -- faithfully reproducing "today's steps_boundary code, yesterday's
WorldName contract" without a second git-show (steps_boundary.py's own diff in this build is a
comment only, confirmed below).

Zero mocks (real submit(), real Plan/Checklist, real boundary_multiplex_config loader), zero
residue (tempfile written under `tempfile.mkdtemp`, removed in `finally`)."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import types

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

import serving.boundary_multiplex_config as bmc  # noqa: E402
from tools.setup_tui import steps as _steps_mod  # noqa: E402
from tools.setup_tui import steps_boundary as sb_current  # noqa: E402
from tools.setup_tui.checklist import Checklist  # noqa: E402
from tools.setup_tui.idtypes import WorldName, WorldNameError  # noqa: E402
from tools.setup_tui.plan import Plan  # noqa: E402

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own
# environment before any subprocess is spawned -- inherited by the whole process tree
# this fixture starts, so every repo-root verb invocation anywhere downstream carries it.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

PRE_FIX_COMMIT = "73874cc62f27e2ab04791da0bfe26c30667fff1b"  # this build's own base commit (see
# STEP 0 / the build report) -- the last commit before idtypes.py's WorldName contract was
# strengthened to the boundary-slug intersection.

BAD_NAME = "MyWorld"      # TUI-valid pre-fix ([A-Za-z0-9_]+), boundary-invalid (uppercase not in
                          # [a-z0-9-]{1,64}) -- the real specimen from the current allowlists'
                          # divergence, not a hypothetical.
CLEAN_NAME = "myworld123"  # legal under BOTH contracts -- the end-to-end-pass leg.


def _pinned_idtypes_source() -> str:
    r = subprocess.run(
        ["git", "-C", REPO, "show", f"{PRE_FIX_COMMIT}:tools/setup_tui/idtypes.py"],
        capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip(), (
        f"could not read {PRE_FIX_COMMIT}:tools/setup_tui/idtypes.py -- {r.stderr}")
    assert "_CONTRACT_RE" not in r.stdout, (
        f"fixture assumption stale: {PRE_FIX_COMMIT}:tools/setup_tui/idtypes.py ALREADY carries "
        f"the boundary-slug intersection fix -- PRE_FIX_COMMIT needs repinning to a genuinely "
        f"earlier commit")
    return r.stdout


def _steps_boundary_diff_is_comment_only() -> bool:
    """Confirms this build's fixture assumption in the docstring above: `steps_boundary.py`'s own
    diff against PRE_FIX_COMMIT touches no non-comment, non-blank line -- so re-exec'ing its
    CURRENT source against a PINNED idtypes is a faithful stand-in for pinning steps_boundary.py
    itself at PRE_FIX_COMMIT too."""
    r = subprocess.run(
        ["git", "-C", REPO, "diff", f"{PRE_FIX_COMMIT}..HEAD", "--",
         "tools/setup_tui/steps_boundary.py"],
        capture_output=True, text=True)
    if r.returncode != 0:
        return False
    for line in r.stdout.splitlines():
        if not (line.startswith("+") or line.startswith("-")):
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        content = line[1:].strip()
        if content and not content.startswith("#"):
            return False
    return True


def _build_pinned_idtypes_module() -> types.ModuleType:
    mod = types.ModuleType("tools.setup_tui.idtypes")
    mod.__file__ = f"<pinned {PRE_FIX_COMMIT}:tools/setup_tui/idtypes.py>"
    src = _pinned_idtypes_source()
    prev = sys.modules.get("tools.setup_tui.idtypes")
    # Registered in sys.modules for the DURATION of this one exec only: the dataclass decorator
    # looks up `cls.__module__` in sys.modules while processing WorldName/DestPath's class bodies
    # (Python 3.13's `_is_type` helper) -- restored in `finally` regardless of outcome, so the
    # REAL current idtypes module (already bound to this file's own top-level names) is never
    # left swapped out.
    sys.modules["tools.setup_tui.idtypes"] = mod
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    finally:
        if prev is not None:
            sys.modules["tools.setup_tui.idtypes"] = prev
        else:
            sys.modules.pop("tools.setup_tui.idtypes", None)
    return mod


def _build_pinned_steps_boundary_module(pinned_idtypes: types.ModuleType) -> types.ModuleType:
    """Re-`exec`s `steps_boundary.py`'s CURRENT on-disk source (its own logic is unchanged by
    this build -- `_steps_boundary_diff_is_comment_only()` above confirms it live) with
    `sys.modules['tools.setup_tui.idtypes']` swapped to the PINNED pre-fix module for the
    duration of the exec, so its `from tools.setup_tui.idtypes import DestPath, DestPathError,
    WorldName, WorldNameError` binds to the pinned (looser) contract."""
    assert _steps_boundary_diff_is_comment_only(), (
        f"fixture assumption stale: tools/setup_tui/steps_boundary.py's own diff against "
        f"{PRE_FIX_COMMIT} is NOT comment-only anymore -- re-exec'ing current source against a "
        f"pinned idtypes no longer faithfully stands in for pinning steps_boundary.py itself; "
        f"pin steps_boundary.py via its own git-show instead")
    src_path = sb_current.__file__
    with open(src_path, encoding="utf-8") as f:
        src = f.read()
    mod = types.ModuleType("tools.setup_tui._pinned_steps_boundary_worldname_boundary_allowlist")
    mod.__file__ = src_path
    prev = sys.modules.get("tools.setup_tui.idtypes")
    sys.modules["tools.setup_tui.idtypes"] = pinned_idtypes
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    finally:
        if prev is not None:
            sys.modules["tools.setup_tui.idtypes"] = prev
        else:
            sys.modules.pop("tools.setup_tui.idtypes", None)
    return mod


def _fresh_state(dest: str, world: str) -> dict:
    return {"_checklist": Checklist(), "_plan": Plan(), "_repo_root": _steps_mod.REPO_ROOT,
            "dest": dest, "dest_would_exist": True, "birth_ok": True, "world": world}


def _answers() -> dict:
    return {"override": False, "host": "192.0.2.1", "db": "toy", "start_now": False}


def _toml_content_from_plan(plan) -> "str | None":
    for entry in plan.entries:
        if entry.item == "multiplex TOML written":
            return entry.act.content
    return None


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="setup-tui-worldname-boundary-allowlist-")
    scratch_toml = os.path.join(tmp, "boundary-multiplex.toml")
    ok = True
    try:
        # --- RED: current steps_boundary.py logic, PINNED pre-fix idtypes.py contract ---
        pinned_idtypes = _build_pinned_idtypes_module()
        sb_pinned = _build_pinned_steps_boundary_module(pinned_idtypes)
        state = _fresh_state(os.path.join(tmp, "red_dest"), BAD_NAME)
        result = sb_pinned.submit(state, _answers())
        assert result.ok, (
            f"RED setup failed: pre-fix-contract steps_boundary.submit() was expected to ACCEPT "
            f"{BAD_NAME!r} (the pre-fix WorldName contract has no boundary-slug check) -- "
            f"got errors={result.errors}")
        toml_text = _toml_content_from_plan(state["_plan"])
        assert toml_text is not None and f"[deployments.{BAD_NAME}]" in toml_text, (
            f"RED setup failed: expected a queued boundary-multiplex.toml entry naming "
            f"[deployments.{BAD_NAME}] -- got {toml_text!r}")
        print(f"case RED ok: pre-fix-contract WorldName + steps_boundary.submit() silently "
              f"accept {BAD_NAME!r} and queue [deployments.{BAD_NAME}] -- reproducing the "
              f"closed defect")

        with open(scratch_toml, "w", encoding="utf-8") as f:
            f.write(toml_text)
        try:
            bmc.load_multiplex_config(scratch_toml)
            raise AssertionError(
                "RED setup failed: the REAL boundary_multiplex_config loader ACCEPTED the "
                f"pre-fix-queued TOML naming [deployments.{BAD_NAME}] -- fixture assumption "
                "stale (has the boundary service's own contract changed?)")
        except bmc.MultiplexConfigError as exc:
            assert BAD_NAME in str(exc) and "does not match" in str(exc), (
                f"RED: boundary loader refused for the wrong reason -- {exc}")
            print(f"case RED ok: the REAL boundary service's config loader REFUSES the "
                  f"pre-fix-queued TOML naming [deployments.{BAD_NAME}] -- "
                  f"MultiplexConfigError: {exc}")
        os.remove(scratch_toml)

        # --- GREEN leg 1: current WorldName refuses the SAME bad name, at construction, before
        # steps_boundary.submit() ever builds a Plan entry (the module-level `sb_current`/
        # `WorldName`/`WorldNameError` imported at this file's own top -- untouched by the RED
        # leg's sys.modules swap, which was always restored in `finally` before this point) ---
        state2 = _fresh_state(os.path.join(tmp, "green_dest_bad"), BAD_NAME)
        result2 = sb_current.submit(state2, _answers())
        assert not result2.ok, (
            f"GREEN leg 1: current steps_boundary.submit() must REFUSE {BAD_NAME!r} -- got ok=True")
        assert not state2["_plan"].entries, (
            "GREEN leg 1: current steps_boundary.submit() must queue NOTHING when it refuses -- "
            f"got {len(state2['_plan'].entries)} plan entries")
        err_text = str(result2.errors)
        assert "boundary" in err_text.lower() or "a-z0-9" in err_text, (
            f"GREEN leg 1: refusal must teach the downstream boundary-slug contract -- {err_text}")
        try:
            WorldName(BAD_NAME)
            raise AssertionError(f"GREEN leg 1: WorldName({BAD_NAME!r}) must raise WorldNameError")
        except WorldNameError as exc:
            assert "boundary" in str(exc).lower() and "a-z0-9" in str(exc), (
                f"GREEN leg 1: WorldNameError must name the boundary-slug contract it protects "
                f"-- {exc}")
            print(f"case GREEN leg 1 ok: current WorldName refuses {BAD_NAME!r} at construction, "
                  f"naming the boundary-slug contract; steps_boundary.submit() never reaches a "
                  f"plan entry -- WorldNameError: {exc}")

        # --- GREEN leg 2: a clean name passes end to end ---
        state3 = _fresh_state(os.path.join(tmp, "green_dest_clean"), CLEAN_NAME)
        result3 = sb_current.submit(state3, _answers())
        assert result3.ok, f"GREEN leg 2: clean name must be accepted -- errors={result3.errors}"
        toml_text3 = _toml_content_from_plan(state3["_plan"])
        assert toml_text3 is not None and f"[deployments.{CLEAN_NAME}]" in toml_text3, (
            f"GREEN leg 2: expected a queued [deployments.{CLEAN_NAME}] entry -- got {toml_text3!r}")
        with open(scratch_toml, "w", encoding="utf-8") as f:
            f.write(toml_text3)
        loaded = bmc.load_multiplex_config(scratch_toml)
        assert CLEAN_NAME in loaded, (
            f"GREEN leg 2: the real boundary loader must accept the clean name -- got {loaded.keys()}")
        print(f"case GREEN leg 2 ok: clean name {CLEAN_NAME!r} passes steps_boundary.submit() AND "
              f"the real boundary_multiplex_config loader end to end")

        print("ALL CASES OK -- WorldName's boundary-slug-intersection contract, red before green, "
              "pinned pre-fix idtypes.py contract vs current, real steps_boundary.submit() + real "
              "boundary_multiplex_config loader, no live Postgres, zero mocks")
    except AssertionError as exc:
        print(f"FAILED: {exc}")
        ok = False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
