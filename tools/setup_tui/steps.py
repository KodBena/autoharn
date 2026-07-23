#!/usr/bin/env python3
"""tools/setup_tui/steps.py -- assembles the configuration tree's UI-free core into the
`SECTIONS` tuple and the `COMMIT` spec `tools/configtree` drives (design/FABLE-SETUP-TUI-REBUILD-
SPEC.md §3 v2/§6: autoharn is a thin consumer of the generic library). The per-section business
logic lives in the sibling `steps_*.py` modules (one file per pre-rebuild screen, or a small
natural grouping -- ADR-0007); this module only assembles them and owns the terminal commit
boundary (`screen_checklist`/`_execute_commit`'s pre-rebuild job). NOTHING here implies an order
-- `SECTIONS` is a plain tuple, iterated by `configtree.app` only to build the sidebar tree and
to check `all_sections_complete`; the operator may visit them in any order the tree allows."""
from __future__ import annotations

import os
from pathlib import Path

from tools.configtree import CommitSpec, SectionResult
from tools.setup_tui import checklist as ck
from tools.setup_tui import commit_executor as CE
from tools.setup_tui import config_seam, content, signed_genesis
from tools.setup_tui import steps_boundary, steps_fork_target, steps_hydration
from tools.setup_tui import steps_load_config, steps_observability, steps_preflight
from tools.setup_tui import steps_principals_authority
from tools.setup_tui import steps_rehearsal_birth, steps_signed_genesis, steps_substrate
from tools.setup_tui.plan import Plan

REPO_ROOT = Path(__file__).resolve().parents[2]

ACTIONS = (steps_load_config.STEP,)

SECTIONS = (
    steps_preflight.STEP,
    steps_substrate.STEP,
    steps_fork_target.STEP,
    steps_rehearsal_birth.REHEARSAL_STEP,
    steps_rehearsal_birth.BIRTH_STEP,
    steps_principals_authority.STEP,
    steps_signed_genesis.STEP,
    steps_boundary.STEP,
    steps_observability.STEP,
    steps_hydration.STEP,
)

SECTION_TITLES = {str(s.slug): str(s.title) for s in SECTIONS}


def initial_state(*, dry_run: bool = False, accept_unverified_genesis: bool = False,
                   initial_answers: "dict | None" = None) -> dict:
    """The shared wizard state every step reads/writes -- `_checklist`/`_plan`/`_repo_root` are
    the three infrastructure keys every `steps_*.py` module depends on; everything else is
    ordinary decision state (`dest`, `world`, `pghost`, ...), exactly the pre-rebuild `state`
    dict's own vocabulary, unchanged."""
    state: dict = {
        "_checklist": ck.Checklist(),
        "_plan": Plan(),
        "_repo_root": REPO_ROOT,
        "dry_run": dry_run,
        "accept_unverified_genesis": accept_unverified_genesis,
    }
    if initial_answers:
        state.update(initial_answers)
    return state


def reset_accumulators(state: dict) -> None:
    """`CommitSpec.reset` (design/FABLE-SETUP-TUI-REBUILD-SPEC.md §3 v2's live-model rebuild,
    2026-07-22 maintainer review): `tools.configtree.commit_pane.CommitPane`'s own submit sweep calls
    every section's `submit` FRESH on every commit attempt (a retry after fixing one section's
    business-rule refusal must re-derive the Plan from CURRENT field values, never append onto a
    stale prior attempt) -- this is the hook that resets THIS consumer's own accumulators
    (`_plan`/`_checklist`) before that replay, leaving every OTHER state key (every decided
    field's own value, `_repo_root`, `dry_run`, `accept_unverified_genesis`) untouched."""
    state["_plan"] = Plan()
    state["_checklist"] = ck.Checklist()


def _teardown_scratch_gnupghomes(state: dict) -> None:
    bindings = state.get("_last_commit_bindings", {})
    for key in state.get("scratch_gnupghome_produces_keys", []):
        gnupghome = bindings.get(key)
        if gnupghome:
            signed_genesis.teardown_scratch(gnupghome)


def render_summary(state: dict) -> str:
    plan = state["_plan"]
    return plan.render()


def _maybe_self_save_config(state: dict, *, dry_run: bool, lines: list) -> None:
    dest = state.get("dest")
    reachable = bool(dest) and (os.path.isdir(dest) or (dry_run and state.get("dest_would_exist")))
    if not reachable:
        return
    path, wrote = config_seam.save_world_config(dest, state, dry_run=dry_run)
    cl = state["_checklist"]
    if dry_run:
        lines.append(f"would save: {path}")
        cl.add("checklist", "world-config.toml self-saved", ck.WOULD_DO, path)
    else:
        lines.append(f"saved: {path}")
        cl.add("checklist", "world-config.toml self-saved", ck.WITNESSED if wrote else ck.REFUSED, path)


def commit(state: dict) -> SectionResult:
    """The terminal commit boundary, ported from `_execute_commit`/`screen_checklist`. `--dry-run`
    stops after rendering the plan (no `commit_executor.execute` call); a live run drives the SAME
    commit boundary the pre-rebuild wizard used, unchanged."""
    plan = state["_plan"]
    cl = state["_checklist"]
    dry_run = state.get("dry_run", False)
    lines: list[str] = []

    if dry_run:
        for entry in plan.entries:
            cl.add(entry.screen, entry.item, ck.WOULD_DO, entry.act.render())
        if plan.daemons:
            dry_dest = state.get("dest") or "<destination>"
            cl.add(CE.DAEMON_SCREEN, CE.DAEMON_SCRIPT_ITEM, ck.WOULD_DO,
                   f"write {CE.daemon_script_path(dry_dest)} ({len(plan.daemons)} daemon(s))")
        _maybe_self_save_config(state, dry_run=True, lines=lines)
        ok = True
    else:
        dest = state.get("dest")
        if not dest:
            for entry in plan.entries:
                cl.add(entry.screen, entry.item, ck.REFUSED, "no destination directory")
            state["commit_halted"] = True
            return SectionResult(ok=False, info_lines=("REFUSED: no destination directory known.",))

        def _on_step(i, entry):
            lines.append(f"[{i + 1}] {entry.screen}: {entry.item} -- {entry.lesson}")
            lines.append(f"  $ {entry.act.render()}")

        def _on_result(i, entry, result, proc=None):
            _dispatch_result(state, entry, result, proc, lines)

        result = CE.execute(plan, dest, on_step=_on_step, on_result=_on_result)
        state["_last_commit_bindings"] = result.bindings
        for v in result.daemon_verifications:
            status = ck.VERIFIED_UP if v.up else ck.NOT_UP
            cl.add(CE.DAEMON_SCREEN, f"{v.daemon.name} verified up", status, v.detail)
            lines.append(f"{v.daemon.name}: {'VERIFIED-UP' if v.up else 'NOT-UP'} -- {v.detail}")
        ok = result.completed
        if not ok:
            state["commit_halted"] = True
            lines.append("COMMIT HALTED -- the journal names the next PENDING step; re-run this "
                         "tool against the same destination to resume.")
        _maybe_self_save_config(state, dry_run=False, lines=lines)
        _teardown_scratch_gnupghomes(state)

    cl.add("checklist", "checklist", ck.WITNESSED if ok else ck.REFUSED, "commit phase complete")
    lines.append(cl.render())
    dest = state.get("dest")
    dest_reachable = bool(dest) and (os.path.isdir(dest) or (dry_run and state.get("dest_would_exist")))
    if dest_reachable:
        path = cl.save(dest, dry_run=dry_run)
        lines.append(f"{'would save' if dry_run else 'saved'} checklist: {path}")
    return SectionResult(ok=ok, info_lines=tuple(lines))


def _dispatch_result(state: dict, entry, result, proc, lines: list) -> None:
    """A thin port of `_dispatch_result` -- the boundary/genesis-gate/birth-refusal special
    cases stay named; everything else is the ordinary ok-based WITNESSED/REFUSED row."""
    cl = state["_checklist"]
    if entry.screen == "birth" and entry.item == "world birth" and not result.ok:
        if "deployment.json already exists" in result.detail:
            fmt = {"dest": state.get("dest", "?"), "world": state.get("birth_world", "?"),
                   "teardown_argv": " ".join([str(state["_repo_root"] / "bootstrap" /
                                              "teardown-world.sh"), state.get("birth_world", "?"),
                                              "--db", state.get("birth_db", "?"), "--host",
                                              state.get("birth_host", "?"), "--dir",
                                              state.get("dest", "?")])}
            for kind, template in content.PARTIAL_BIRTH_TEACHING:
                lines.append(template.format(**fmt))
            cl.add(entry.screen, entry.item, ck.REFUSED,
                   f"REFUSED (partial-birth): deployment.json exists at '{fmt['dest']}'")
            return
    if entry.screen == "boundary" and entry.item == "service started" and result.ok and proc is not None:
        state["boundary_proc"] = proc
    if entry.screen == "signed-genesis" and entry.item == "ceremony gate (verify-commission)":
        body = signed_genesis.parse_verify_body(result.detail)
        verdict = body.get("verdict") or body.get("refusal") or "(no verdict parsed)"
        lines.append(f"verify-commission verdict: {verdict}")
        if body.get("verdict") == "VERIFIED":
            cl.add(entry.screen, entry.item, ck.WITNESSED, str(body.get("detail", ""))[:200])
            return
        cl.add(entry.screen, entry.item, ck.REFUSED, f"NOT VERIFIED ({verdict})")
        if result.ok:
            cl.add(entry.screen, "verify-commission override exercised", ck.WITNESSED,
                   f"--accept-unverified-genesis: proceeded past verdict={verdict}")
        else:
            lines.extend(content.GENESIS_GATE_HARD_STOP_TEACHING)
        return
    cl.add(entry.screen, entry.item, ck.WITNESSED if result.ok else ck.REFUSED,
           result.detail[:300] if isinstance(result.detail, str) else str(result.detail))
    lines.append(f"  -> {'WITNESSED' if result.ok else 'REFUSED'}")


COMMIT = CommitSpec(render_summary=render_summary, commit=commit, confirm_label="Commit this plan",
                     reset=reset_accumulators)
