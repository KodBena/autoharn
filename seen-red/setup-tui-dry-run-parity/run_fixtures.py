#!/usr/bin/env python3
"""run_fixtures.py -- WDR1 and WDR2, the two `--dry-run` witnesses (design/FABLE-SETUP-TUI-SPEC.md
2026-07-19 amendment, commission ledger row 1719) that need REAL infra: a live, reachable
Postgres host and a real boundary_service process. (WDR3 -- a dry run refuses a hostile input
identically to the live path -- needs neither and lives in
seen-red/setup-tui-scripted-smoke/run_fixtures.py's case 9 instead.)

WDR1 -- "a full dry-run flow against a real destination directory leaves the filesystem
byte-identical (before/after tree hash compared mechanically) and writes zero ledger rows."
This fixture births a REAL scratch world (real `led`, real boundary_service, real led-decision
rows from a full hydration pass), then reruns hydration a SECOND time -- same catalog item, same
ADR, same destination, same REAL, REACHABLE `led` -- under `--dry-run --start-at hydration`, and
checks (not assumes): the destination's file tree hashes identically before/after, and the
world's own max ledger-row id is unchanged. A dry run that merely never got far enough to touch
anything would be a much weaker proof than this -- the live counterpart of every dry-run act
here provably WOULD have written something (rows 7/8, a rewritten CLAUDE.md, a rewritten
checklist file), so "unchanged" is a real claim, not a vacuous one.

WDR2 -- "on the scripted happy path, the WOULD-DO table's argv list equals the argv list a real
scratch run actually executes (compared mechanically, order included)." This fixture runs the
SAME pinned scripted answers twice against the same destination path -- once live (a real
scratch birth, torn down immediately after so the second run starts from the identical
nonexistent-destination precondition), once `--dry-run`.

PHASE-2 CONTRACT CHANGE (design/FABLE-SETUP-TUI-PURE-CORE-SPEC.md, commission ledger rows 1823
point 2 / 1825 / 1835): the pre-Phase-2 comparator diffed the two runs' `$ `-prefixed argv-echo
lines (`runner.run_command`/`start_background`'s own unconditional print) because every screen
called those choke points directly, live or dry alike, so the SAME print fired both ways. Under
the pure-core rewrite, a screen never calls a choke point at all (except `screen_rehearsal`'s
declared exception) -- an act is QUEUED, and only `commit_executor.execute` (reached from the
terminal Checklist screen's commit boundary) ever calls `runner.run_command`, and ONLY on a real,
committed, live run; a `--dry-run` run never reaches that call at all, so it never prints a `$ `
line for a queued act. Comparing raw `$ ` lines between live and dry therefore compares "every
act's real, shell-quoted commit-time echo" against "nothing" -- not the claim WDR2 exists to
prove. The Phase-2-shaped equivalent of the SAME claim is `Plan.render()`'s own PRE-commit table
(the "SCREEN ITEM ACT" block `_execute_commit` prints via `ui.emit(Paragraph(plan.render()))`
UNCONDITIONALLY,
before it branches on `dry_run` at all) -- both a live run (before it commits) and a dry run
(which stops there) print this EXACT table for the same decisions, by construction (this is
`plan.py`'s own WPC7 property: "a dry run's plan rendering is byte-identical to a committed run's
pre-commit rendering for the same answers"). `plan_table()` below extracts that block; the
comparison is table-for-table, not line-for-line against a print that no longer fires under dry
run at all.

WGF -- the governed-files exposure's LIVE end-to-end witness (design/FABLE-SETUP-TUI-SPEC.md
2026-07-19 amendment, commission ledger row 1730; tools/setup_tui/governed_files.py's own module
docstring, the CORRECTED single-writer design): WDR1's own real birth now runs the fork/target
screen for real (fresh mode, extending the pattern set) instead of skipping it, so this fixture
gets this witness for free from infrastructure it already pays for. Asserts, against the SAME
real destination, AFTER both `new-project.sh` invocations this flow makes (screen_birth's
`--new-world` call AND screen_boundary's later classic-mode `--force` re-scaffold, which rewrites
the SAME `.claude/` wiring): the FINAL `.claude/governed_files.json` on disk still carries the
extended set, parsed by hooks/pretooluse_change_gate.py's OWN `_load_governed_patterns` (imported
read-only, never edited) -- proving the operator's screen-3 choice survives BOTH writers rather
than being silently clobbered back to the bare default by the second one (the exact hazard an
out-of-frame review caught in this feature's first-pass design, which wrote the file directly at
screen 3 and raced `new-project.sh`'s own later unconditional rewrite).

Real infra, no mocks, zero residue (every scratch world torn down in a `finally`, every scratch
dir removed). Needs HARNESS_PGHOST (or EPISTEMIC_PGHOST, or a deployment.json -- see
filing/pghost_resolve.py) pointing at a reachable cluster with a `toy` database, AND
~/w/vdc/venvs/generic/bin/python (the same venv tools/setup_tui/screens.py's own
screen_boundary hardcodes for starting the boundary service) -- absent either, this fixture
prints UNEXERCISED and exits 0 rather than failing the build on missing optional local infra.

Usage: python3 seen-red/setup-tui-dry-run-parity/run_fixtures.py
Exit 0 if every case matches (or infra is UNEXERCISED); 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "filing"))
sys.path.insert(0, str(REPO / "hooks"))

from pghost_resolve import resolve_pghost  # noqa: E402
import pretooluse_change_gate  # noqa: E402  -- the governed-files witness's REAL contract
# (its own _load_governed_patterns), imported read-only, never edited: see WGF below.

PGDB = "toy"
VENV_PYTHON = os.path.expanduser("~/w/vdc/venvs/generic/bin/python")
TEARDOWN = str(REPO / "bootstrap" / "teardown-world.sh")


def sh(argv: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, **kw)


def run_scripted(answers: str, scratch: str, tag: str,
                  extra_argv: list[str] | None = None) -> subprocess.CompletedProcess:
    ans_path = os.path.join(scratch, f"answers-{tag}.txt")
    with open(ans_path, "w") as f:
        f.write(answers)
    argv = [sys.executable, "-m", "tools.setup_tui.app", "--scripted", ans_path]
    if extra_argv:
        argv += extra_argv
    return subprocess.run(argv, cwd=str(REPO), capture_output=True, text=True, timeout=180)


def argv_lines(text: str) -> list[str]:
    """Every `$ `-prefixed line -- `runner.run_command`/`runner.start_background`'s own
    unconditional echo. Under Phase 2 this ONLY ever fires for `screen_rehearsal`'s declared-
    exception direct calls and for whatever a LIVE commit actually executes -- never for a
    `--dry-run` run (see module docstring's Phase-2 note). Kept for any caller that still wants
    the raw commit-time transcript; WDR2 itself now uses `plan_table()` below."""
    return [ln for ln in text.splitlines() if ln.startswith("$ ")]


def plan_table(text: str) -> list[str]:
    """The `Plan.render()` block `_execute_commit` prints UNCONDITIONALLY (before it branches on
    `dry_run`) -- the lines from the "SCREEN ITEM ACT" header through the "N entr{y,ies} total"
    footer, inclusive. Both a live run (before it commits) and a dry run (which stops there)
    print this exact block for the same decisions, by construction (plan.py's own WPC7 property)
    -- this is the Phase-2-shaped WDR2 comparand, module docstring's own note explains why."""
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines)
                  if ln.strip().startswith("SCREEN") and "ITEM" in ln and "ACT" in ln), None)
    if start is None:
        return []
    end = next((i for i in range(start, len(lines)) if "total" in lines[i] and "entr" in lines[i]),
               None)
    return lines[start:end + 1] if end is not None else []


def tree_hash(root: str) -> dict[str, str]:
    out = {}
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root)
            with open(path, "rb") as f:
                out[rel] = hashlib.sha256(f.read()).hexdigest()
    return out


def max_led_row(dest: str) -> int:
    led = os.path.join(dest, "led")
    cp = sh([led, "--recent", "1"])
    text = cp.stdout + cp.stderr
    m = re.search(r"^\[(\d+)\]", text, re.MULTILINE)
    return int(m.group(1)) if m else 0


def teardown(host: str, world: str, dest: str) -> None:
    """Best-effort, idempotent: called from `finally` for worlds that may already be torn down
    (or never fully born) -- errors here are swallowed (nothing left to report on a world that
    never existed), the point is zero residue, not a fresh assertion."""
    sh([TEARDOWN, world, "--db", PGDB, "--host", host, "--dir", dest],
       input=f"{world}\n", timeout=60)


def main() -> int:
    try:
        pghost = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST")
    except SystemExit as exc:
        print(f"UNEXERCISED: {exc}\nWDR1/WDR2 need a live, reachable Postgres host -- set "
              f"HARNESS_PGHOST to run this fixture for real.")
        return 0
    # tools/setup_tui/screens.py screen_preflight ALSO reads HARNESS_PGHOST/EPISTEMIC_PGHOST
    # directly (never a deployment.json fallback -- that's this fixture's own resolve_pghost()
    # extra reach) and, if set, populates `state["pghost"]` there -- which makes
    # screen_substrate's own "Postgres host" prompt SKIP entirely (`state.get("pghost") or
    # ui.ask_text(...)`). Requiring the SAME env var here (not resolve_pghost's deployment.json
    # fallback) keeps this fixture's own scripted-answer count deterministic: the host prompt
    # never fires when this fixture is actually exercised, so no answer is reserved for it below.
    if not (os.environ.get("HARNESS_PGHOST") or os.environ.get("EPISTEMIC_PGHOST")):
        print("UNEXERCISED: HARNESS_PGHOST/EPISTEMIC_PGHOST resolved only via deployment.json "
              "(this fixture's own scripted-answer counts assume the env var is what preflight "
              "sees, matching screen_preflight's own resolution) -- set HARNESS_PGHOST directly "
              "to run this fixture for real.")
        return 0
    if not os.path.isfile(VENV_PYTHON):
        print(f"UNEXERCISED: {VENV_PYTHON} not found -- WDR1's real led writes need a real "
              f"boundary_service process, which needs this venv (the same path "
              f"tools/setup_tui/screens.py's own screen_boundary hardcodes). Set it up to "
              f"exercise WDR1/WDR2 for real.")
        return 0

    base = int(time.time())
    scratch = tempfile.mkdtemp(prefix="setup-tui-dry-run-parity-")
    live_worlds: list[tuple[str, str]] = []  # (world, dest) still needing teardown
    try:
        # =========================== WDR1: real destination, real led ===========================
        world_a = f"probeworld{base}1"
        scratch_world_a = f"probeworld{base}2"
        dest_a = os.path.join(scratch, "dest_a")
        answers_a = "\n".join([
            "y",                                                  # preflight
            "y", "existing", PGDB,                        # substrate
            "y", "fresh", dest_a, "y", ".ts,.vue,.html",           # fork-target: destination
                                                                    # (fresh mode -- WGF's own
                                                                    # live half needs a REAL
                                                                    # fork/target pass, not the
                                                                    # skip this fixture used
                                                                    # before) + governed-files
                                                                    # extend (commission row
                                                                    # 1730's own witnessed
                                                                    # specimen extensions)
            "y", scratch_world_a, os.path.join(scratch, "reh_a"),  # rehearsal
            "y", world_a, world_a,                                # birth: confirm, world, name
                                                                    # (dest already set by
                                                                    # fork-target above)
            "n",                                                   # principals-authority skip
                                                                    # (design/FABLE-SETUP-TUI-
                                                                    # PRINCIPALS-AUTHORITY-
                                                                    # SPEC.md, inserted between
                                                                    # Birth and Signed genesis)
            "n",                                                   # signed-genesis skip (design/
                                                                    # FABLE-SETUP-TUI-SIGNED-
                                                                    # GENESIS-SPEC.md, inserted
                                                                    # between Principals &
                                                                    # authority and Boundary)
            "y", "y",                                             # boundary configure + start
            "n",                                                  # observability skip
            "y",                                                  # hydration run
            "n", "n",                                             # fork provenance / role charter
        ] + ["y"] + ["n"] * 11                                    # catalog: accept item 1
          + ["y"] + ["n"] * 18                                    # ADRs: accept ADR-0000
          + ["y"]                                                 # PHASE 2: commit this plan now
          + ["n"]) + "\n"                                         # decline checklist save
        cp = run_scripted(answers_a, scratch, "wdr1-live")
        out_a = cp.stdout + cp.stderr
        assert cp.returncode == 0, f"WDR1 setup (real birth) failed: {out_a[-2000:]}"
        assert "Traceback" not in out_a, out_a[-2000:]
        live_worlds.append((world_a, dest_a))

        # WGF (module docstring): by this point BOTH new-project.sh invocations this flow makes
        # have run against dest_a -- screen_birth's --new-world call, AND screen_boundary's
        # later classic-mode --force re-scaffold (the "y", "y" boundary-configure answers above).
        # The FINAL governed_files.json on disk must still carry the extended set, parsed by the
        # REAL change-gate loader -- proving the second writer did not clobber the first.
        gf_path = os.path.join(dest_a, ".claude", "governed_files.json")
        gf_patterns = pretooluse_change_gate._load_governed_patterns(gf_path)
        assert gf_patterns == ["*.py", "*.ts", "*.vue", "*.html"], (
            f"WGF: expected the extended pattern set to survive both new-project.sh writers "
            f"(birth + boundary's re-scaffold), got {gf_patterns!r} from {gf_path} -- "
            f"{out_a[-2000:]}")
        print(f"WGF ok: the extended governed-files pattern set survives BOTH new-project.sh "
              f"writers (screen_birth's --new-world call and screen_boundary's later classic-"
              f"mode re-scaffold) and parses correctly through hooks/pretooluse_change_gate.py's "
              f"OWN _load_governed_patterns: {gf_patterns}")

        # PHASE 2: commit_executor.py's own BackgroundAct handling is generic (it does not know
        # about a "boundary URL" concept) -- the checklist DETAIL for "service started" is now
        # just "pid <N>", no longer the pre-Phase-2 combined "pid <N>, http://..." string.
        m = re.search(r"service started\s+WITNESSED\s+pid (\d+)", out_a)
        assert m, f"WDR1 setup: no 'service started pid ...' checklist row found: {out_a[-1500:]}"
        boundary_pid = int(m.group(1))
        # PHASE 2: the checklist DETAIL for a hydration decision is now the RAW streamed commit
        # output ("led: row <N> written."), not the pre-Phase-2 post-processed "row <N>" string
        # (that formatting lived in a _run_decision helper this rewrite retired -- the checklist
        # now shows exactly what commit_executor's on_result callback received, real and
        # unprocessed, per spec's own "checklist per entry" rule).
        assert ("hydration      makespan-scheduling-by-mandate         WITNESSED  led: row" in
                out_a), (
            f"WDR1 setup: expected a REAL led-decision row for the catalog item: {out_a[-2000:]}")

        rows_before = max_led_row(dest_a)
        assert rows_before > 0, f"WDR1 setup: expected real led rows, got max id={rows_before}"
        tree_before = tree_hash(dest_a)

        # The dry rerun: SAME catalog item + SAME ADR selection, against the SAME real dest and
        # the SAME real, live, reachable led -- a REAL duplicate write if this were not --dry-run.
        answers_dry = "\n".join([
            "y", dest_a,                                          # hydration run, dest
            "n", "n",                                             # fork provenance / role charter
        ] + ["y"] + ["n"] * 11
          + ["y"] + ["n"] * 18
          + ["n"]) + "\n"                                         # decline checklist save
        cp = run_scripted(answers_dry, scratch, "wdr1-dry",
                           extra_argv=["--dry-run", "--start-at", "hydration"])
        out_dry = cp.stdout + cp.stderr
        assert cp.returncode == 0, f"WDR1 dry rerun failed: {out_dry[-2000:]}"
        assert "Traceback" not in out_dry, out_dry[-2000:]
        for ln in out_dry.splitlines():
            if ln.startswith("hydration") and " WITNESSED " in ln:
                raise AssertionError(
                    f"WDR1: a hydration item claimed WITNESSED under --dry-run "
                    f"(should be WOULD-DO): {ln}")
        assert "WOULD-DO" in out_dry, out_dry[-1500:]

        tree_after = tree_hash(dest_a)
        assert tree_before == tree_after, (
            f"WDR1: filesystem changed under --dry-run -- diff: "
            f"{set(tree_before) ^ set(tree_after)} or content changed for "
            f"{[k for k in tree_before if tree_before.get(k) != tree_after.get(k)]}")

        rows_after = max_led_row(dest_a)
        assert rows_after == rows_before, (
            f"WDR1: led row count changed under --dry-run: {rows_before} before, "
            f"{rows_after} after -- a real write happened when none should have")

        print(f"WDR1 ok: --dry-run rehydration against a REAL destination with a REAL, "
              f"connected led ({dest_a}) left the filesystem byte-identical "
              f"({len(tree_before)} files checked) and the ledger row count unchanged "
              f"(max id {rows_before} before and after)")

        sh(["kill", str(boundary_pid)])
        time.sleep(1)
        teardown(pghost, world_a, dest_a)
        live_worlds.remove((world_a, dest_a))

        # ============================ WDR2: argv parity, live vs dry ============================
        world_b = f"probeworld{base}3"
        scratch_world_b = f"probeworld{base}4"
        dest_b = os.path.join(scratch, "dest_b")
        # boundary's `can_start="y"` (in-process start) deliberately AVOIDS the PREPARED-block
        # path's `ui.pause(...)` -- that call is skipped entirely under `--dry-run`
        # (`_dry_skip_or`, DRY_SKIPPED, no prompt) but fires live, which would consume ONE MORE
        # scripted answer live than dry and misalign every prompt after the boundary screen between the two
        # runs (a test-harness artifact, not a subject-under-test one). The in-process-start
        # branch has no such asymmetry: 0 extra prompts, live or dry.
        answers_b = "\n".join([
            "y",
            "y", "existing", PGDB,
            "n",
            "y", scratch_world_b, os.path.join(scratch, "reh_b"),
            "y", world_b, dest_b, world_b,
            "n",               # principals-authority skip (design/FABLE-SETUP-TUI-PRINCIPALS-
                                 # AUTHORITY-SPEC.md, inserted between Birth and Signed genesis)
            "n",               # signed-genesis skip (design/FABLE-SETUP-TUI-SIGNED-GENESIS-
                                 # SPEC.md, inserted between Principals & authority and Boundary)
            "y", "y",         # boundary configure + in-process start
            "n",               # observability skip
            "n",               # hydration skip -- keeps this leg independent of a live led
            "y",               # PHASE 2: commit this plan now -- LIVE leg only consumes this;
                                 # under --dry-run the commit-confirm is never asked at all, so
                                 # this token is simply unused there (harmless -- ScriptedUi does
                                 # not require every line to be consumed, only running OUT is an
                                 # error), which is exactly why the SAME answers file still drives
                                 # both legs.
            "n",               # decline checklist save
        ]) + "\n"
        cp_live = run_scripted(answers_b, scratch, "wdr2-live")
        out_live = cp_live.stdout + cp_live.stderr
        assert cp_live.returncode == 0, f"WDR2 live run failed: {out_live[-2000:]}"
        assert "Traceback" not in out_live, out_live[-2000:]
        live_worlds.append((world_b, dest_b))
        table_live = plan_table(out_live)
        assert table_live, f"WDR2: no plan table captured from the live run: {out_live[-800:]}"

        m_b = re.search(r"service started\s+WITNESSED\s+pid (\d+)", out_live)
        if m_b:
            sh(["kill", m_b.group(1)])
            time.sleep(1)
        teardown(pghost, world_b, dest_b)
        live_worlds.remove((world_b, dest_b))
        assert not os.path.exists(dest_b), (
            f"WDR2: {dest_b} should be gone after teardown, before the dry rerun starts from "
            f"the identical nonexistent-destination precondition")

        cp_dry = run_scripted(answers_b, scratch, "wdr2-dry", extra_argv=["--dry-run"])
        out_dry2 = cp_dry.stdout + cp_dry.stderr
        assert cp_dry.returncode == 0, f"WDR2 dry run failed: {out_dry2[-2000:]}"
        assert "Traceback" not in out_dry2, out_dry2[-2000:]
        assert not os.path.exists(dest_b), (
            f"WDR2: --dry-run must never create {dest_b} -- found it on disk after the run")
        table_dry = plan_table(out_dry2)
        assert table_dry, f"WDR2: no plan table captured from the dry run: {out_dry2[-800:]}"

        assert table_live == table_dry, (
            "WDR2: the pre-commit plan table differs between the live scratch run and the dry "
            "run (order included) -- live:\n  " + "\n  ".join(table_live) +
            "\ndry:\n  " + "\n  ".join(table_dry))
        print(f"WDR2 ok: the --dry-run plan table ({len(table_dry)} lines, "
              f"{table_dry[-1] if table_dry else '?'}) is byte-identical, order included, to "
              f"the real scratch run's own PRE-commit plan table (same pinned world/dest/host/"
              f"db, live run committed and torn down with zero residue before the dry rerun)")

        print("ALL CASES OK -- setup_tui --dry-run WDR1 (byte-identical filesystem + zero new "
              "ledger rows against a real, led-connected destination) and WDR2 (argv parity vs "
              "a real scratch run), zero residue")
        return 0
    finally:
        # `pghost` is always bound here -- both earlier UNEXERCISED branches `return` before this
        # try/finally is ever entered.
        for world, dest in live_worlds:
            teardown(pghost, world, dest)
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
