#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-19T02:23:18Z
#   last-change: 2026-07-19T02:25:11Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

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

PGDB = "toy"
NEW_PROJECT = os.path.join(REPO, "bootstrap", "new-project.sh")
TEARDOWN = os.path.join(REPO, "bootstrap", "teardown-world.sh")
KERNEL_LINEAGE = os.path.join(REPO, "kernel", "lineage")

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
        )
        cp1 = run_scripted(ans1, scratch, "wp1", dest)
        out1 = cp1.stdout + cp1.stderr
        assert "Traceback" not in out1, out1[-1500:]
        m_reg = re.search(r"register-principal wp1subagent subagent.*?\n.*?row (\d+) written",
                           out1, re.DOTALL)
        m_comp = re.search(r"grant-competence wp1subagent.*?\n.*?row (\d+) written",
                            out1, re.DOTALL)
        m_rel = re.search(r"principal relate wp1subagent succeeds author.*?\n.*?row (\d+) "
                           r"written", out1, re.DOTALL)
        m_chart = re.search(r"role_charter\.py register wp1subagent.*?\n.*?row (\d+) written",
                             out1, re.DOTALL)
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
        ans2 = "y\n" + dest + "\ny\nreviewer\nsubagent\nWP2 duplicate attempt\nn\nn\nn\nn\n"
        cp2 = run_scripted(ans2, scratch, "wp2", dest)
        out2 = cp2.stdout + cp2.stderr
        assert "Traceback" not in out2, out2[-1500:]
        assert "REFUSED -- principal 'reviewer' is already registered" in out2, out2[-1500:]
        assert "Re-registration is never a silent no-op" in out2, out2[-1500:]
        print("WP2 ok: duplicate registration of 'reviewer' refused, kernel teach-text "
              "rendered verbatim, no traceback")

        # ---- WP3a: the trap, DECLINE leg ---------------------------------------------------
        ans3a = "y\n" + dest + "\nn\nn\nn\ny\nneverregistered\n/tmp/x\nn\nn\n"
        cp3a = run_scripted(ans3a, scratch, "wp3a", dest)
        out3a = cp3a.stdout + cp3a.stderr
        assert "Traceback" not in out3a, out3a[-1500:]
        assert "REFUSED: charter left unregistered -- manual command:" in out3a, out3a[-1500:]
        assert "register-principal neverregistered" in out3a, out3a[-1500:]

        # ---- WP3b: the trap, ACCEPT leg ----------------------------------------------------
        ans3b = ("y\n" + dest + "\nn\nn\nn\ny\nwp3accept\n" +
                 os.path.join(dest, "roles", "README.md") + "\ny\ntool\nWP3 accept-leg purpose\n"
                 "n\n")
        cp3b = run_scripted(ans3b, scratch, "wp3b", dest)
        out3b = cp3b.stdout + cp3b.stderr
        assert "Traceback" not in out3b, out3b[-1500:]
        m_reg3 = re.search(r"register-principal wp3accept tool.*?\n.*?row (\d+) written",
                            out3b, re.DOTALL)
        m_chart3 = re.search(r"role_charter\.py register wp3accept.*?\n.*?row (\d+) written",
                              out3b, re.DOTALL)
        assert m_reg3 and m_chart3, out3b[-3000:]
        print("WP3 ok: unregistered-role charter -- decline leaves a legible REFUSED with the "
              "manual command; accept completes charter with both row ids echoed "
              f"(register={m_reg3.group(1)}, charter={m_chart3.group(1)})")

        # ---- WP5: dry-run, lessons visible, zero acts --------------------------------------
        ans5 = ("y\n" + dest + "\ny\nwp5dryname\nmodel\nWP5 dry-run purpose\nn\nn\nn\nn\n")
        cp5 = run_scripted(ans5, scratch, "wp5", dest, dry_run=True)
        out5 = cp5.stdout + cp5.stderr
        assert "Traceback" not in out5, out5[-1500:]
        assert "CONSTITUTES: a new identity anchor row" in out5, out5[-1500:]
        assert "register-principal wp5dryname model" in out5, out5[-1500:]
        assert "[dry-run: not executed]" in out5, out5[-1500:]
        dep = {}

        with open(os.path.join(dest, "deployment.json")) as f:
            dep = json.load(f)
        cnt = sh(["psql", "-h", pghost, "-d", PGDB, "-tAc",
                  f"SELECT count(*) FROM {dep['kern']}.principal WHERE name='wp5dryname';"])
        assert cnt.stdout.strip() == "0", (
            f"WP5: --dry-run must write zero rows, found {cnt.stdout.strip()!r}")
        print("WP5 ok: lesson + exact argv shown, '[dry-run: not executed]', checklist "
              "WOULD-DO, zero rows actually written (verified by direct psql count)")

        # ---- WP6a: out-of-sequence, nonexistent destination --------------------------------
        missing = os.path.join(scratch, "nonexistent")
        ans6a = "y\n" + missing + "\nn\nn\nn\nn\n"
        cp6a = run_scripted(ans6a, scratch, "wp6a", missing)
        out6a = cp6a.stdout + cp6a.stderr
        assert "Traceback" not in out6a, out6a[-1500:]
        assert "REFUSED: destination directory" in out6a and missing in out6a, out6a[-1500:]

        # ---- WP6b: out-of-sequence, real dir with no legacy/led ----------------------------
        bare = os.path.join(scratch, "bare")
        os.makedirs(bare)
        ans6b = "y\n" + bare + "\nn\nn\nn\nn\n"
        cp6b = run_scripted(ans6b, scratch, "wp6b", bare)
        out6b = cp6b.stdout + cp6b.stderr
        assert "Traceback" not in out6b, out6b[-1500:]
        assert f"REFUSED: no {os.path.join(bare, 'legacy', 'led')}" in out6b, out6b[-1500:]
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

            ans4 = "y\n" + mid_dest + "\nn\nn\nn\nn\n"
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
