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

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "filing"))

from pghost_resolve import resolve_pghost  # noqa: E402

sys.path.insert(0, REPO)
from tools.setup_tui import commit_executor as _CE  # noqa: E402


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
# navigate the four screens between principals-authority and Checklist.
COMMIT_TAIL = "n\nn\nn\nn\ny\nn\n"     # decline sg/boundary/observability/hydration, commit=yes, save=no
NOCOMMIT_TAIL = "n\nn\nn\nn\n"           # same four declines; no commit-confirm for an EMPTY plan
DRYRUN_TAIL = "n\nn\nn\nn\nn\n"          # same four declines; no commit-confirm under --dry-run; save=no

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
    r = sh([os.path.join(dest, "legacy", "led"), "show", str(row_id)])
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
    try:
        # ---- birth a real scratch world (WP1/WP2/WP3/WP5/WP6's own substrate) -----------------
        res = sh([NEW_PROJECT, dest, "--new-world", world, "--db", PGDB, "--host", pghost,
                  "--name", "paw-fixture"], timeout=180)
        if res.returncode != 0:
            print(f"UNEXERCISED: scratch birth failed (not this fixture's own failure):\n"
                  f"{(res.stdout + res.stderr)[-2000:]}")
            return 0

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
        assert "REFUSED -- principal 'reviewer' is already registered" in out2, out2[-1500:]
        assert "Re-registration is never a silent no-op" in out2, out2[-1500:]
        print("WP2 ok: duplicate registration of 'reviewer' refused, kernel teach-text "
              "rendered verbatim, no traceback")

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
        would_do_line = next(
            (ln for ln in out5.splitlines()
             if "register principal 'wp5dryname'" in ln and "WOULD-DO" in ln), None)
        assert would_do_line is not None and "register-principal wp5dryname model" in would_do_line, (
            f"WP5: the WOULD-DO checklist row must carry the exact argv: {out5[-1500:]}")
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
        ans6a = "y\n" + missing + "\nn\nn\nn\nn\n"
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
        ans6b = "y\n" + bare + "\nn\nn\nn\nn\nn\n"  # PHASE 2: bare exists -- save-checklist IS asked
        cp6b = run_scripted(ans6b, scratch, "wp6b", bare)
        out6b = cp6b.stdout + cp6b.stderr
        assert "Traceback" not in out6b, out6b[-1500:]
        assert f"REFUSED: '{bare}' classifies as foreign" in out6b, out6b[-1500:]
        print("WP6 ok: out-of-sequence entry refuses legibly against (a) a nonexistent "
              "destination and (b) a real directory with no legacy/led, no traceback")

    finally:
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
            led_shim = (
                "#!/bin/sh\n"
                'HERE="$(cd "$(dirname "$0")" && cd .. && pwd)"\n'
                f'exec env PICKUP_DEPLOYMENT="$HERE/deployment.json" '
                f'{os.path.join(REPO, "bootstrap", "templates", "legacy-led.tmpl")} "$@"\n'
            )
            led_path = os.path.join(mid_dest, "legacy", "led")
            with open(led_path, "w") as f:
                f.write(led_shim)
            os.chmod(led_path, 0o755)

            ans4 = "y\n" + mid_dest + "\nn\nn\nn\nn\nn\nn\n"  # PHASE 2: reach Checklist cleanly (empty plan, real dest)
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
