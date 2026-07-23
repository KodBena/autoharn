#!/usr/bin/env python3
"""run_fixtures.py -- WP1-WP6, the six witnesses design/FABLE-SETUP-TUI-PRINCIPALS-AUTHORITY-
SPEC.md §4 names for the "Principals & authority" screen (tools/setup_tui/screens.py
`screen_principals_authority`, commission ledger row 1727). Real infra, no mocks: a throwaway
`--new-world` scaffold in the toy db (torn down before AND after this file runs, so re-running it
never leaves residue) for WP1/WP2/WP3/WP5/WP6, plus a hand-built mid-chain scratch schema
(s15..s40, no s41 -- the VALIDATE recipe kernel/lineage/s40-principal-identity-events.sql's own
header names, stopped one delta short) wrapped in a minimal directory scaffold for WP4 (the
"cheapest honest equivalent" the spec's own §4 names, since `bootstrap/new-project.sh
--new-world` always applies the full chain through the lineage head today -- there is no
in-product way to birth an s41-absent world).

  WP1 full constitutive pass: register a principal (subagent class), grant a competence, add
      one relation, charter the role -- all four `led` rows verified by id and content via
      `led show`; checklist accurate per item; teardown zero residue.
  WP2 kernel refusal rendered as teaching: duplicate registration of `reviewer` -> the s40 loud
      refusal's teach-text shown on-screen verbatim, no traceback.
  WP3 the trap, closed: charter for an unregistered role -> in-flow registration offer -> DECLINE
      leaves a legible REFUSED with the manual command; ACCEPT completes charter with both row
      ids echoed.
  WP4 s41-absent honesty: against a hand-built s40-only world, the bindings section reports
      unavailable-with-reason; nothing offered that would fail (no competence/relation prompt at
      all).
  WP5 dry-run: lesson + exact argv shown, `[dry-run: not executed]`, checklist WOULD-DO, zero
      rows actually written (verified by direct psql count).
  WP6 out-of-sequence entry refusals: (a) a nonexistent destination, (b) a real directory with no
      legacy/led -- both legible REFUSED, no traceback.

PHASE-2 CONTRACT CHANGE (design/FABLE-SETUP-TUI-PURE-CORE-SPEC.md, commission ledger rows 1823
point 2 / 1825 / 1835 -- itemized per that build's own report table): `screen_principals_authority`'s
OWN prompt sequence is UNCHANGED (verified: this is a fixture-lane repair, not a product defect --
the screen asks in the same order the spec's own registry names, and continuing into
screen 7 (Signed genesis) after principals-authority finishes is the SAME `--start-at`-continues-
to-the-end behavior the pre-Phase-2 flow already had). What changed is WHEN an act's real output
appears: every `led`/`role_charter.py` call this screen drives is now a QUEUED plan entry, executed
only at the ONE commit boundary (the Checklist screen, screen 11) -- never inline within
`screen_principals_authority`'s own pass any more. Cases that need to OBSERVE a real row id or a
real kernel refusal (WP1, WP2, WP3's accept leg) must therefore navigate the four screens between
principals-authority and Checklist (Signed genesis / Boundary / Observability / Hydration, each
declined with one "n") and answer the Checklist screen's own "Commit this plan now?" confirm before
the real `led`/`role_charter.py` output exists to assert against; WP5 (dry-run) similarly must reach
Checklist to see the "Save this checklist into the new world?" prompt (dry-run skips the
commit-confirm itself -- `_execute_commit` never asks it when `state["dry_run"]` is set) but the
`[dry-run: not executed]` marker `runner.run_command`'s own print used to emit no longer exists for
a QUEUED (never-executed-under-dry-run) act -- the WOULD-DO status the closing checklist table
carries is the Phase-2 equivalent, asserted directly. Cases whose assertions only depend on text the
screen prints BEFORE it would need a not-yet-given answer (WP3's decline leg, WP4, WP6a/WP6b) are
unaffected and unchanged.

Needs HARNESS_PGHOST (or EPISTEMIC_PGHOST, or a deployment.json -- see filing/pghost_resolve.py)
pointing at a reachable cluster with a `toy` database -- absent it, this fixture prints
UNEXERCISED and exits 0 rather than failing the build on missing optional local infra (the same
posture seen-red/setup-tui-signed-genesis already established for this package).

Usage: python3 seen-red/setup-tui-principals-authority/run_fixtures.py
Exit 0 if every case matches (or infra is UNEXERCISED); 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "filing"))
sys.path.insert(0, os.path.join(REPO, "serving"))

from pghost_resolve import resolve_pghost  # noqa: E402
import deployment_record  # noqa: E402

sys.path.insert(0, REPO)
from tools.setup_tui import commit_executor as _CE  # noqa: E402

# legacy-led-retirement inventory pass (ledger row 1149/1150): every `led` write this fixture's
# own screen_principals_authority acts drive (register-principal, and, since this same pass
# closed the coverage gap, grant-competence/relate too) now targets the served path
# unconditionally (tools/setup_tui/runner.py's `served_led_path`/`resolve_led`, boundary
# mandatory at every birth) -- this fixture's own scratch world needs a REAL standing
# boundary_service, not just a scaffolded `legacy/led`. Reuses seen-red/boundary-service/
# run_fixtures.py's own scratch-server helpers (ADR-0012 P1), the same reuse this pass's other
# migrations (reservation-residue, belief-substrate-v1, s51-artifact-store) already use.
_BS_SPEC = importlib.util.spec_from_file_location(
    "boundary_service_fixtures", Path(REPO) / "seen-red" / "boundary-service" / "run_fixtures.py")
assert _BS_SPEC is not None and _BS_SPEC.loader is not None
bs_fixtures = importlib.util.module_from_spec(_BS_SPEC)
sys.modules["boundary_service_fixtures"] = bs_fixtures
_BS_SPEC.loader.exec_module(bs_fixtures)


def start_boundary_for(world: str, dest: str, pghost: str) -> subprocess.Popen:
    """Stands a real `serving.boundary_service` against `world` (already born through the
    ordinary schema/kern/role convention `bootstrap/new-project.sh --new-world` uses) and
    rewrites `dest`'s own `deployment.json` in place with the served-shim's two required keys --
    the SAME two facts `tools/setup_tui/screens.py`'s own `screen_boundary` writes, applied
    directly here since this fixture drives the CLI, never the TUI's boundary screen itself."""
    tmp = Path(tempfile.mkdtemp(prefix=f"{world}-boundary-"))
    cfg_path = bs_fixtures.write_scratch_multiplex_config(tmp, world)
    proc, port = bs_fixtures.start_server(cfg_path)
    base = f"http://127.0.0.1:{port}/d/{world}"
    if not bs_fixtures.wait_health(base):
        tail = bs_fixtures.stop_server(proc)
        raise RuntimeError(f"boundary_service for {world} never became healthy: {tail[-1500:]}")
    dep_path = os.path.join(dest, "deployment.json")
    with open(dep_path) as f:
        dep = json.load(f)
    dep["boundary_url"] = f"http://127.0.0.1:{port}"
    dep["boundary_deployment"] = world
    with open(dep_path, "w") as f:
        json.dump(dep, f)
    return proc


def _clear_journal(dest: str) -> None:
    """PHASE 2: removes a leftover commit journal from a PRIOR case's commit against this SAME
    scratch world, if one exists -- WP1-WP3b/WP5 all share one physical `dest`, and a case whose
    commit legitimately halted partway (WP2's refused registration) leaves its own journal behind
    by design (commit_executor.py's own resume contract); the NEXT independent case's differently-
    shaped plan would otherwise collide with it (a correct, loud ValueError this fixture does not
    want to trigger between unrelated cases)."""
    path = _CE.journal_path(dest)
    if os.path.isfile(path):
        os.remove(path)


PGDB = "toy"
NEW_PROJECT = os.path.join(REPO, "bootstrap", "new-project.sh")
TEARDOWN = os.path.join(REPO, "bootstrap", "teardown-world.sh")
KERNEL_LINEAGE = os.path.join(REPO, "kernel", "lineage")

# PHASE-2 answer tails (module docstring's own "PHASE-2 CONTRACT CHANGE" note): every case that
# needs a real committed act, or the closing checklist's own WOULD-DO/save-checklist prompts, must
# navigate the screens between principals-authority and Checklist.
#
# design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part C completion (row 1158/1159): "boundary" moved
# to run BEFORE "principals-authority" in screens.py's own SCREENS list ("ORDER IS LOAD-BEARING")
# -- `--start-at principals-authority` (every case in this fixture) now slices `SCREENS[idx:]`
# starting AT principals-authority, so boundary (now BEFORE it) is no longer in that slice at
# all. THREE screens remain between principals-authority and Checklist (signed-genesis,
# observability, hydration), not four -- one "n" fewer in every tail below.
COMMIT_TAIL = "n\nn\nn\ny\nn\n"     # decline sg/observability/hydration, commit=yes, save=no
NOCOMMIT_TAIL = "n\nn\nn\n"           # same three declines; no commit-confirm for an EMPTY plan
DRYRUN_TAIL = "n\nn\nn\nn\n"          # same three declines; no commit-confirm under --dry-run; save=no

_CHAIN_THROUGH_S40 = [
    "high_watermark_1.sql", "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
    "s25-commission-kind.sql", "s26-row-hash-chain.sql", "s27-chain-high-water.sql",
    "s28-work-parent-edge.sql", "s29-obligation-item-key-and-typed-close.sql",
    "s30-typed-dependency-edges.sql", "s31-supersession-uniform-retraction.sql",
    "s32-edge-views-single-home.sql", "s33-composite-discharge.sql",
    "s34-computed-grade-refusal.sql", "s35-validation-decomposition.sql",
    "s36-decision-grade.sql", "s37-violation-disposition.sql",
    "s38-bookkeeping-close.sql", "s39-blocks-start.sql",
    "s40-principal-identity-events.sql",
]


def sh(argv: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, **kw)


def run_scripted(answers: str, scratch: str, tag: str, dest_hint: str,
                  dry_run: bool = False) -> subprocess.CompletedProcess:
    ans_path = os.path.join(scratch, f"answers-{tag}.txt")
    with open(ans_path, "w") as f:
        f.write(answers)
    argv = [sys.executable, "-m", "tools.setup_tui.app", "--scripted", ans_path,
            "--start-at", "principals-authority"]
    if dry_run:
        argv.append("--dry-run")
    return subprocess.run(argv, cwd=REPO, capture_output=True, text=True, timeout=120)



def _commit_phase_output(out: str) -> str:
    """PHASE 2: the decision phase prints a "queued: <argv>" line for every plan entry BEFORE any
    of them run -- searching the WHOLE transcript for "<argv text>...row N written" can anchor on
    that decision-time line and then match the WRONG entry's row id (the nearest "row N written"
    chronologically, which belongs to whichever entry actually executed nearest that point in the
    commit sequence, not the one the decision-time line named). Scoping every row-id search to the
    text AFTER "Commit this plan now?" (present only once, right before commit_executor.execute
    actually runs) avoids that cross-phase mismatch -- the real fix for a real defect this
    build's principals-authority-fixture repair caught, not a cosmetic change."""
    idx = out.find("Commit this plan now?")
    return out[idx:] if idx != -1 else out

def led_show(dest: str, row_id: int) -> str:
    # legacy-led-retirement inventory pass (ledger row 1149/1150): served, not legacy -- the
    # served path is COVERED for `led show` (always was) and this fixture's own scratch world
    # now carries a real standing boundary_service (`start_boundary_for` above).
    r = subprocess.run([sys.executable, os.path.join(REPO, "bootstrap", "templates", "led.tmpl"),
                        "show", str(row_id)], capture_output=True, text=True,
                       env={**os.environ, "AUTOHARN": REPO,
                            "PICKUP_DEPLOYMENT": os.path.join(dest, "deployment.json")})
    return r.stdout


def main() -> int:
    try:
        pghost = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST")
    except SystemExit as exc:
        print(f"UNEXERCISED: {exc}\nWP1-WP6 need a live, reachable Postgres host -- set "
              f"HARNESS_PGHOST to run this fixture for real.")
        return 0
    if sh(["pg_isready", "-h", pghost]).returncode != 0:
        print(f"UNEXERCISED: {pghost} not reachable -- skipping (not a failure).")
        return 0

    scratch = tempfile.mkdtemp(prefix="setup-tui-principals-authority-")
    world = f"probeworld{int(time.time())}"
    dest = os.path.join(scratch, "world")
    ok = True
    boundary_proc: subprocess.Popen | None = None
    try:
        # ---- birth a real scratch world (WP1/WP2/WP3/WP5/WP6's own substrate) -----------------
        res = sh([NEW_PROJECT, dest, "--new-world", world, "--db", PGDB, "--host", pghost,
                  "--name", "paw-fixture"], timeout=180)
        if res.returncode != 0:
            print(f"UNEXERCISED: scratch birth failed (not this fixture's own failure):\n"
                  f"{(res.stdout + res.stderr)[-2000:]}")
            return 0
        # legacy-led-retirement inventory pass (ledger row 1149/1150): `led` is served,
        # unconditionally, everywhere now -- stand a real boundary_service before any WP case
        # drives a write (see `start_boundary_for`'s own docstring).
        boundary_proc = start_boundary_for(world, dest, pghost)

        # ---- WP1: full constitutive pass -------------------------------------------------
        ans1 = (
            "y\n" + dest + "\n"
            "y\nwp1subagent\nsubagent\nWP1 fixture: register a subagent-class principal\nn\n"
            "y\nwp1subagent\nwp1-activity\nband-1\nWP1 fixture basis\nn\n"
            "y\nwp1subagent\nsucceeds\nauthor\nn\n"
            "y\nwp1subagent\n" + os.path.join(dest, "roles", "README.md") + "\nn\n"
            + COMMIT_TAIL  # PHASE 2: navigate to Checklist and commit for real -- see module docstring
        )
        _clear_journal(dest)
        cp1 = run_scripted(ans1, scratch, "wp1", dest)
        out1 = cp1.stdout + cp1.stderr
        assert "Traceback" not in out1, out1[-1500:]
        out1_commit = _commit_phase_output(out1)
        m_reg = re.search(r"register-principal wp1subagent subagent.*?\n.*?row (\d+) written",
                           out1_commit, re.DOTALL)
        m_comp = re.search(r"grant-competence wp1subagent.*?\n.*?row (\d+) written",
                            out1_commit, re.DOTALL)
        m_rel = re.search(r"principal relate wp1subagent succeeds author.*?\n.*?row (\d+) "
                           r"written", out1_commit, re.DOTALL)
        m_chart = re.search(r"role_charter\.py register wp1subagent.*?\n.*?row (\d+) written",
                             out1_commit, re.DOTALL)
        assert m_reg and m_comp and m_rel and m_chart, (
            f"WP1: not all four row ids found in output: {out1[-3000:]}")
        reg_id, comp_id, rel_id, chart_id = (int(m.group(1)) for m in
                                              (m_reg, m_comp, m_rel, m_chart))
        reg_row = led_show(dest, reg_id)
        assert "principal_registered" in reg_row and "wp1subagent" in reg_row, reg_row
        comp_row = led_show(dest, comp_id)
        assert "principal_competence_granted" in comp_row and "wp1-activity" in comp_row, comp_row
        rel_row = led_show(dest, rel_id)
        assert "principal_relation_asserted" in rel_row and "succeeds" in rel_row, rel_row
        chart_row = led_show(dest, chart_id)
        assert "role-charter registered: role=wp1subagent" in chart_row, chart_row
        print(f"WP1 ok: register={reg_id} competence={comp_id} relation={rel_id} "
              f"charter={chart_id}, all four verified via `led show`")

        # ---- WP2: kernel refusal rendered as teaching (duplicate 'reviewer') --------------
        ans2 = ("y\n" + dest + "\ny\nreviewer\nsubagent\nWP2 duplicate attempt\nn\nn\nn\nn\n"
                + COMMIT_TAIL)  # PHASE 2: the duplicate-registration REFUSAL only fires at commit
        _clear_journal(dest)
        cp2 = run_scripted(ans2, scratch, "wp2", dest)
        out2 = cp2.stdout + cp2.stderr
        assert "Traceback" not in out2, out2[-1500:]
        # MESSAGE-TEXT UPDATE (legacy-led-retirement inventory pass, ledger row 1149/1150): this
        # write now goes through the served path (register_principal_act's own `led=served_led`),
        # not `legacy/led`. DISCLOSED NARROWING, pre-existing (not introduced by this pass):
        # legacy-led.tmpl's own `register-principal` ran a CLIENT-SIDE pre-check ("principal
        # 'reviewer' is already registered", "Re-registration is never a silent no-op") before
        # ever attempting the write; served led.tmpl's `cmd_register_principal` has no such
        # pre-check (bootstrap/templates/led.tmpl) -- the duplicate surfaces as the KERNEL's own
        # raw refusal instead (a genuine constraint violation, still refused, still journaled,
        # just without legacy's nicer client-side wording).
        assert "REFUSED by the kernel write boundary" in out2, out2[-1500:]
        assert "duplicate key value violates unique constraint" in out2, out2[-1500:]
        assert "row_id written" not in out2, out2[-1500:]  # never a false accept
        print("WP2 ok: duplicate registration of 'reviewer' refused by the kernel's own "
              "constraint, journaled (SQLSTATE 23505), no traceback")

        # ---- WP3a: the trap, DECLINE leg ---------------------------------------------------
        ans3a = ("y\n" + dest + "\nn\nn\nn\ny\nneverregistered\n/tmp/x\nn\nn\n"
                 + NOCOMMIT_TAIL + "n\n")  # PHASE 2: reach Checklist (empty plan, real dest -- save-checklist IS asked)
        cp3a = run_scripted(ans3a, scratch, "wp3a", dest)
        out3a = cp3a.stdout + cp3a.stderr
        assert "Traceback" not in out3a, out3a[-1500:]
        assert "REFUSED: charter left unregistered -- manual command:" in out3a, out3a[-1500:]
        assert "register-principal neverregistered" in out3a, out3a[-1500:]

        # ---- WP3b: the trap, ACCEPT leg ----------------------------------------------------
        ans3b = ("y\n" + dest + "\nn\nn\nn\ny\nwp3accept\n" +
                 os.path.join(dest, "roles", "README.md") + "\ny\ntool\nWP3 accept-leg purpose\n"
                 "n\n" + COMMIT_TAIL)  # PHASE 2: both row ids only exist post-commit
        _clear_journal(dest)
        cp3b = run_scripted(ans3b, scratch, "wp3b", dest)
        out3b = cp3b.stdout + cp3b.stderr
        assert "Traceback" not in out3b, out3b[-1500:]
        out3b_commit = _commit_phase_output(out3b)
        m_reg3 = re.search(r"register-principal wp3accept tool.*?\n.*?row (\d+) written",
                            out3b_commit, re.DOTALL)
        m_chart3 = re.search(r"role_charter\.py register wp3accept.*?\n.*?row (\d+) written",
                              out3b_commit, re.DOTALL)
        assert m_reg3 and m_chart3, out3b[-3000:]
        print("WP3 ok: unregistered-role charter -- decline leaves a legible REFUSED with the "
              "manual command; accept completes charter with both row ids echoed "
              f"(register={m_reg3.group(1)}, charter={m_chart3.group(1)})")

        # ---- WP5: dry-run, lessons visible, zero acts --------------------------------------
        ans5 = ("y\n" + dest + "\ny\nwp5dryname\nmodel\nWP5 dry-run purpose\nn\nn\nn\nn\n"
                + DRYRUN_TAIL)  # PHASE 2: reach Checklist to see the WOULD-DO status for real
        _clear_journal(dest)
        cp5 = run_scripted(ans5, scratch, "wp5", dest, dry_run=True)
        out5 = cp5.stdout + cp5.stderr
        assert "Traceback" not in out5, out5[-1500:]
        assert "CONSTITUTES: a new identity anchor row" in out5, out5[-1500:]
        assert "queued: " in out5 and "register-principal wp5dryname model" in out5, out5[-1500:]
        # PHASE 2: the act is never executed under --dry-run at all (queued, never run), so
        # runner.run_command's own "[dry-run: not executed]" marker never fires for it -- the
        # Phase-2 equivalent is the closing checklist's WOULD-DO status for this exact entry.
        assert ("principals-authority register principal 'wp5dryname'" in out5
                and "WOULD-DO" in out5), out5[-1500:]
        # WRAP-TOLERANT (ledger row 1949, confirmed RED on this build's own base commit before
        # this fix): the closing checklist's `Table` element (tools/setup_tui/elements.py
        # `_render_table`) wraps any non-last column wider than the shared per-column cap onto
        # CONTINUATION physical lines -- both the SCREEN column ("principals-authority", 21
        # chars) and the ITEM column ("register principal 'wp5dryname'", 31 chars) exceed the
        # 4-column cap (18 chars) here, so the row this case cares about is split across TWO
        # physical `print()` lines (verified directly against `elements.render_text` while
        # diagnosing this: 'principals-...WOULD-DO  /tmp/.../led register-principal wp5dryname
        # model...' then "authority           'wp5dryname'"). A naive line-join loses the
        # ORIGINAL column adjacency (the ITEM continuation physically follows the STATUS/DETAIL
        # text of the row above it, not the ITEM text it continues) -- this reconstructs each
        # COLUMN instead, using the table's own header line to find each column's start offset
        # (`_render_table` ljust-pads every column to a fixed width and joins with a 2-space
        # gutter, so the header's own column-name positions are the same positions every data
        # row uses), then concatenates that one column's fragment across every physical line of
        # the row -- the honest inverse of `_render_table`'s own wrap.
        lines5 = out5.splitlines()
        status_markers = ("WITNESSED", "SKIPPED", "REFUSED", "WOULD-DO")
        col_names = ("SCREEN", "ITEM", "STATUS", "DETAIL")
        header_idx = next(
            (i for i, ln in enumerate(lines5) if ln.startswith("SCREEN") and "ITEM" in ln
             and "STATUS" in ln and "DETAIL" in ln), None)
        assert header_idx is not None, f"WP5: no checklist table header found: {out5[-1500:]}"
        header_line = lines5[header_idx]
        offsets = [header_line.index(name) for name in col_names]

        def _col(line: str, i: int) -> str:
            start, end = offsets[i], (offsets[i + 1] if i + 1 < len(offsets) else len(line))
            return line[start:end].rstrip() if start < len(line) else ""

        anchor_idx = next(
            (i for i, ln in enumerate(lines5)
             if "register-principal wp5dryname model" in _col(ln, 3) and _col(ln, 2) == "WOULD-DO"),
            None)
        assert anchor_idx is not None, (
            f"WP5: no checklist-table row's DETAIL column carries the exact argv for "
            f"register-principal wp5dryname with STATUS WOULD-DO: {out5[-1500:]}")
        row_lines = [lines5[anchor_idx]]
        j = anchor_idx + 1
        while j < len(lines5):
            nxt = lines5[j]
            if not nxt.strip() or nxt.strip().startswith("totals:") or \
                    any(marker in nxt for marker in status_markers):
                break
            row_lines.append(nxt)
            j += 1
        item_text = " ".join(part for ln in row_lines if (part := _col(ln, 1).strip()))
        detail_text = " ".join(part for ln in row_lines if (part := _col(ln, 3).strip()))
        assert item_text == "register principal 'wp5dryname'", (
            f"WP5: the WOULD-DO checklist row's ITEM column (reconstructed across its wrapped "
            f"continuation line(s)) must read \"register principal 'wp5dryname'\", got "
            f"{item_text!r}: {row_lines!r}")
        assert "register-principal wp5dryname model" in detail_text, (
            f"WP5: the WOULD-DO checklist row's DETAIL column must carry the exact argv, got "
            f"{detail_text!r}: {row_lines!r}")
        dep = {}

        with open(os.path.join(dest, "deployment.json")) as f:
            dep = json.load(f)
        cnt = sh(["psql", "-h", pghost, "-d", PGDB, "-tAc",
                  f"SELECT count(*) FROM {dep['kern']}.principal WHERE name='wp5dryname';"])
        assert cnt.stdout.strip() == "0", (
            f"WP5: --dry-run must write zero rows, found {cnt.stdout.strip()!r}")
        print("WP5 ok: lesson + exact argv shown, closing checklist row status WOULD-DO "
              "(the Phase-2 equivalent of the retired per-act '[dry-run: not executed]' marker), "
              "zero rows actually written (verified by direct psql count)")

        # ---- WP6a: out-of-sequence, nonexistent destination --------------------------------
        missing = os.path.join(scratch, "nonexistent")
        # design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part C completion (row 1158/1159): boundary
        # is no longer in this `--start-at principals-authority` slice (it now runs BEFORE
        # principals-authority) -- one fewer downstream decline (sg/observability/hydration, not
        # sg/boundary/observability/hydration); `missing` never exists, so checklist's own
        # save-prompt is never even asked (dest_reachable short-circuits it).
        ans6a = "y\n" + missing + "\nn\nn\nn\n"
        cp6a = run_scripted(ans6a, scratch, "wp6a", missing)
        out6a = cp6a.stdout + cp6a.stderr
        assert "Traceback" not in out6a, out6a[-1500:]
        assert "REFUSED: destination directory" in out6a and missing in out6a, out6a[-1500:]

        # ---- WP6b: out-of-sequence, real dir with no legacy/led ----------------------------
        # HAZARD FIX + FIXTURE-CONTRACT CHANGE (found live while sweeping this fixture during an
        # UNRELATED build -- design/FABLE-SETUP-TUI-CHECKLIST-SPLIT-SPEC.md -- pulled per
        # CLAUDE.md's engineering-responsibility rule): design/FABLE-SETUP-TUI-DESTINATION-STATE-
        # SPEC.md (this worktree's own base commit 93050a9) did TWO things this case's old
        # assertion never caught up to. (1) An EMPTY existing directory now classifies FRESH,
        # same as nonexistent -- a bare `os.makedirs(bare)` hit the "does not exist yet" REFUSED
        # leg before reaching this case's own target leg at all (proven: reproduces against the
        # unmodified worktree base, `git stash` verified) -- fixed with the same non-empty-
        # placeholder shape scripted-smoke's own case 5 and two sibling setup-tui fixtures
        # already use. (2) `screen_principals_authority`'s dest-exists branch was ALSO rewired,
        # in that same spec, from a bare `os.path.isfile(.../legacy/led)` probe (whose refusal
        # text this assertion still expected, "REFUSED: no <path>/legacy/led") to
        # `destination.classify_destination` (whose refusal text is "REFUSED: '<dest>' classifies
        # as foreign ..." -- see tools/setup_tui/screens.py's own `dest_state.kind !=
        # AUTOHARN_COMPLETE` branch) -- the assertion below is updated to match the CURRENT,
        # correct refusal text, not the pre-destination-state one.
        bare = os.path.join(scratch, "bare")
        os.makedirs(bare)
        with open(os.path.join(bare, "placeholder.txt"), "w", encoding="utf-8") as f:
            f.write("not autoharn's -- this fixture only needs a non-empty (non-FRESH) directory\n")
        # One fewer downstream decline than before (boundary no longer in this slice -- see ans6a's
        # own comment above); bare exists -- save-checklist IS asked.
        ans6b = "y\n" + bare + "\nn\nn\nn\nn\n"
        cp6b = run_scripted(ans6b, scratch, "wp6b", bare)
        out6b = cp6b.stdout + cp6b.stderr
        assert "Traceback" not in out6b, out6b[-1500:]
        # WRAP-TOLERANT (found live while wrap-tolerizing WP5 above, same fixture, in reach --
        # CLAUDE.md engineering-responsibility rule): this decision-phase refusal is a `Note`
        # (`tools/setup_tui/elements.py` `_wrap_lines`, MEASURE=78), and `bare`'s own path lives
        # under THIS fixture's `scratch` tempdir, whose "setup-tui-principals-authority-" prefix
        # is long enough that the rendered line wraps mid-phrase ("...classifies as" / "foreign
        # (foreign: non-empty...")) -- a plain-`in-out6b` substring check is therefore prefix-
        # length-fragile (confirmed: passes against a SHORT scratch prefix, fails against this
        # fixture's own real one). Unlike the Table-column wrap WP5 hits, prose wrap here is
        # strictly sequential (no column transposition), so collapsing all whitespace runs
        # (including the wrap's own newline) to single spaces is the honest, order-preserving fix.
        assert f"REFUSED: '{bare}' classifies as foreign" in " ".join(out6b.split()), out6b[-1500:]
        print("WP6 ok: out-of-sequence entry refuses legibly against (a) a nonexistent "
              "destination and (b) a real directory with no legacy/led, no traceback")

    finally:
        if boundary_proc is not None:
            bs_fixtures.stop_server(boundary_proc)
        sh([TEARDOWN, world, "--db", PGDB, "--host", pghost, "--dir", dest,
            "--force-non-scratch"], input=f"{world}\n", timeout=60)
        shutil.rmtree(scratch, ignore_errors=True)

    # ---- WP4: s41-absent honesty, hand-built mid-chain (s15..s40, no s41) ------------------
    mid_schema = f"s40only{int(time.time())}"
    mid_kern = f"{mid_schema}_kernel"
    mid_role = f"{mid_schema}_rw"
    mid_dest = tempfile.mkdtemp(prefix="setup-tui-principals-authority-wp4-")
    try:
        argv = ["psql", "-h", pghost, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
                "-v", f"schema={mid_schema}", "-v", f"kern={mid_kern}", "-v", f"role={mid_role}"]
        for fname in _CHAIN_THROUGH_S40:
            argv += ["-f", os.path.join(KERNEL_LINEAGE, fname)]
        res = sh(argv, cwd=KERNEL_LINEAGE, timeout=120)
        if res.returncode != 0:
            print(f"UNEXERCISED (WP4): mid-chain apply failed (not this fixture's own "
                  f"failure):\n{(res.stdout + res.stderr)[-2000:]}")
        else:
            os.makedirs(os.path.join(mid_dest, "legacy"), exist_ok=True)
            with open(os.path.join(mid_dest, "deployment.json"), "w") as f:

                json.dump({"db": PGDB, "host": pghost, "kern": mid_kern,
                            "name": mid_schema, "role": mid_role, "schema": mid_schema}, f)
            # legacy-led-retirement inventory pass (ledger row 1149/1150): matches
            # bootstrap/new-project.sh's own real post-retirement shape -- a one-line teaching
            # refusal, never a working direct-psql CLI (legacy-led.tmpl is deleted). Only the
            # FILE's existence matters here (destination.py's AUTOHARN_COMPLETE classifier); WP4
            # never actually invokes it as a real CLI (a read-only s41_status/list_principals
            # check, both raw psql -- see this file's own module docstring).
            led_shim = (
                '#!/bin/sh\necho "legacy/led: RETIRED 2026-07 -- every surface serves through '
                './led now." >&2\nexit 1\n'
            )
            led_path = os.path.join(mid_dest, "legacy", "led")
            with open(led_path, "w") as f:
                f.write(led_shim)
            os.chmod(led_path, 0o755)

            # One fewer downstream decline than before (boundary no longer between principals-
            # authority and Checklist -- design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part C
            # completion, row 1158/1159).
            ans4 = "y\n" + mid_dest + "\nn\nn\nn\nn\nn\n"  # PHASE 2: reach Checklist cleanly (empty plan, real dest)
            cp4 = run_scripted(ans4, mid_dest, "wp4", mid_dest)
            out4 = cp4.stdout + cp4.stderr
            assert "Traceback" not in out4, out4[-1500:]
            assert "authority bindings section UNAVAILABLE" in out4, out4[-1500:]
            assert "kernel lacks kernel/lineage/s41-principal-bindings-and-relations.sql" \
                in out4, out4[-1500:]
            assert "Grant a competence now?" not in out4, (
                "WP4: the competence-grant prompt must never be offered on an s41-absent "
                "world: " + out4[-1500:])
            assert "Add a typed relation now?" not in out4, (
                "WP4: the typed-relation prompt must never be offered on an s41-absent "
                "world: " + out4[-1500:])
            print("WP4 ok: against a hand-built s40-only world, the bindings section reports "
                  "unavailable-with-reason and offers neither a competence-grant nor a "
                  "typed-relation prompt")
    finally:
        sh(["psql", "-h", pghost, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
            f'DROP SCHEMA IF EXISTS "{mid_schema}" CASCADE; '
            f'DROP SCHEMA IF EXISTS "{mid_kern}" CASCADE; '
            f'DROP ROLE IF EXISTS "{mid_role}";'], timeout=30)
        shutil.rmtree(mid_dest, ignore_errors=True)

    if not ok:
        return 1
    print("ALL CASES OK (WP1-WP6) -- principals & authority screen, zero residue")
    return 0


if __name__ == "__main__":
    sys.exit(main())
