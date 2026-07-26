#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity witness for tools/role_brief.py's fix round (commit a2750f6
fresh-context review, BLOCKS MERGE, SEVERE finding on parse_current_line -- see mock_led.py's own
docstring in this same directory for the full defect description and this fixture's disclosed
mock-vs-real-infra scoping).

WITNESSES:
  R1  RED-FIRST, PRE-FIX CODE (git a2750f6's own tools/role_brief.py, checked out verbatim into
      this fixture's tmp dir): against the `corrupt` scenario, renders STANDING as ACTIVE and
      exits 0 -- the silent vacuous-pass the review caught, reproduced directly.
  R2  POST-FIX CODE, `corrupt` scenario: refuses loudly -- BriefError naming the offending line
      and the producing command (`<led> current <N>`), exit 1. Nothing renders as a clean brief.
  R3  POST-FIX CODE, `clean` scenario (same suspension row, not corrupted): STANDING renders
      SUSPENDED at the TOP of the brief, exit 0 -- the fix does not disturb the legitimate path.
  R4  RED-FIRST, PRE-FIX CODE (git cc12b46's own tools/role_brief.py -- this branch's tip BEFORE
      the re-lap review's parse_served_show finding): against `show_corrupt`, a real in-force
      decision row (row 2) whose `led show` actor line carries a one-column width drift silently
      drops out of IN-FORCE DECISIONS -- an emptier-but-exit-0 brief, the same silent-drop class
      already killed in parse_current_line, still alive in parse_served_show at cc12b46.
  R5  POST-FIX CODE, `show_corrupt` scenario: refuses loudly -- BriefError naming the offending
      `led show 2` line and command, exit 1. Nothing renders.
  R6  POST-FIX CODE, `show_clean` scenario (same row 2, actor field at the correct width): row 2
      renders in IN-FORCE DECISIONS, exit 0 -- the fix does not disturb the legitimate path.
  R7  POST-FIX CODE, `show_longkey` scenario (this fix round's residual #1 -- served_shapes.py's
      own module docstring names a real >=28-char column, `principal_competence_activity`
      (29 chars), as its CENTRAL motivating case; nothing exercised it before this addendum):
      row 1's `led show 1` output carries that column UNPADDED, exactly as cmd_show really
      emits it. The full brief renders end-to-end, exit 0 -- a well-formed line is never refused
      as a false SHAPE DRIFT. Directly alongside: served_shapes.parse_served_show, called
      in-process against the exact same line, returns the column IN its dict (the parse itself,
      not merely "nothing crashed").
  R8  RED-FIRST, PRE-FIX CODE (git cc12b46's own served_shapes-equivalent parse_served_show,
      loaded in-process from the same temp checkout R4 uses): called directly against the
      IDENTICAL `show_longkey` line, it returns a dict with NO `principal_competence_activity`
      key at all -- the fixed-slice `line[28:30] != ": "` check silently `continue`s past this
      well-formed, unpadded long-key line, exactly the silent-drop class this fix round exists
      to kill, now shown on the module's own named motivating case rather than only on the
      one-column actor-width drift R4 covers.

Usage: python3 seen-red/role-brief-current-line-shape-drift/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned; stdlib only.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
MOCK_LED = HERE / "mock_led.py"
POST_FIX_ROLE_BRIEF = REPO / "tools" / "role_brief.py"
PRE_FIX_COMMIT = "a2750f6"
PRE_SHOW_FIX_COMMIT = "cc12b46"

# R7/R8 below call served_shapes.parse_served_show directly (the post-fix module) rather than
# only through a subprocess -- served_shapes.py is a pure stdlib parsing library with no side
# effects, so a direct in-process call is the cheapest honest way to assert "the field is
# actually IN the parsed dict" rather than merely "the CLI process didn't crash". Imported here,
# at module top (CLAUDE.md's lazy-imports ban applies to this fixture script too -- gates/
# no_lazy_imports.py does not exclude seen-red/), immediately after putting tools/ on sys.path.
sys.path.insert(0, str(REPO / "tools"))
import served_shapes

import os
# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own
# environment before any subprocess is spawned -- inherited by the whole process tree
# this fixture starts, so every repo-root verb invocation anywhere downstream carries it.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

# Shared with mock_led.py's own SHOW_ROWS["1"] `show_longkey` line -- the exact byte shape
# cmd_show emits for a real, currently-schema'd >=28-char column, UNPADDED (see mock_led.py's
# own LONGKEY_LINE for the citation). Duplicated here as a literal (not imported from mock_led,
# whose own SCENARIO global is read once at import time off this process's own environment, not
# the child subprocess's) so R7/R8's direct parse_served_show calls exercise byte-identical text
# to what the `show_longkey` scenario's subprocess run actually receives.
LONGKEY_LINE = "principal_competence_activity: onboarding-queue-triage\n"

FAILURES: list[str] = []


def check(label: str, cond: bool, detail: str) -> None:
    tag = "ok" if cond else "FAIL"
    print(f"=== {label} ===\n  [{tag}] {detail}\n")
    if not cond:
        FAILURES.append(label)


def run_brief(role_brief_path: Path, scenario: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(role_brief_path), "brief", "s45",
         "--led", str(MOCK_LED), "--scan-limit", "100"],
        capture_output=True, text=True,
        env={"MOCK_LED_SCENARIO": scenario, "PATH": "/usr/bin:/bin"},
    )


def main() -> int:
    print("=== role-brief-current-line-shape-drift: seen-red witness ===\n")

    # R1: PRE-FIX code (a2750f6, byte-identical to what the review actually examined), against
    # the corrupted fixture. Materialize it into a real tmp file so subprocess.run stays uniform
    # with the post-fix invocation (no cross-import, no monkeypatching -- a real separate process
    # running the real pre-fix bytes).
    pre_fix_src = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{PRE_FIX_COMMIT}:tools/role_brief.py"],
        capture_output=True, text=True, check=True,
    ).stdout
    with tempfile.NamedTemporaryFile("w", suffix="_role_brief_pre_fix.py", delete=False) as f:
        f.write(pre_fix_src)
        pre_fix_path = Path(f.name)
    try:
        r1 = run_brief(pre_fix_path, "corrupt")
        r1_active = "ACTIVE -- no suspend/lift/revoke event found" in r1.stdout
        check("R1-pre-fix-corrupt-silently-renders-active", r1.returncode == 0 and r1_active,
              f"exit={r1.returncode} STANDING-shows-ACTIVE={r1_active} (pre-fix commit "
              f"{PRE_FIX_COMMIT}, the exact code the fresh-context review examined) -- this is "
              f"the vacuous-pass the review caught: a role suspended in the ledger renders as "
              f"an ACTIVE, exit-0 brief because the corrupted line was silently skipped")
    finally:
        pre_fix_path.unlink(missing_ok=True)

    # R2: POST-FIX code, corrupt scenario -- must refuse loudly, never render a brief.
    r2 = run_brief(POST_FIX_ROLE_BRIEF, "corrupt")
    r2_refused = ("REFUSED -- SHAPE DRIFT" in r2.stderr
                  and "does not match the expected `[id] kind: statement` shape" in r2.stderr
                  and "current 100" in r2.stderr
                  and "TRUNCATED ROW" in r2.stderr)
    r2_no_brief = "# BRIEF" not in r2.stdout or "STANDING" not in r2.stdout
    check("R2-post-fix-corrupt-refuses-loudly", r2.returncode == 1 and r2_refused and r2_no_brief,
          f"exit={r2.returncode} names-shape-drift={r2_refused} no-standing-rendered={r2_no_brief}\n"
          f"  stderr={r2.stderr.strip()!r}")

    # R3: POST-FIX code, clean scenario -- SUSPENDED renders at the top of the brief, exit 0.
    r3 = run_brief(POST_FIX_ROLE_BRIEF, "clean")
    lines = r3.stdout.splitlines()
    standing_idx = next((i for i, ln in enumerate(lines) if ln.startswith("## STANDING")), None)
    decisions_idx = next((i for i, ln in enumerate(lines) if ln.startswith("## IN-FORCE DECISIONS")), None)
    r3_suspended = "SUSPENDED (row 7): principal 's45' suspended" in r3.stdout
    r3_at_top = (standing_idx is not None and decisions_idx is not None and standing_idx < decisions_idx)
    check("R3-post-fix-clean-suspension-renders-at-top", r3.returncode == 0 and r3_suspended and r3_at_top,
          f"exit={r3.returncode} SUSPENDED-line-present={r3_suspended} "
          f"STANDING-before-IN-FORCE-DECISIONS={r3_at_top}")

    # R4: PRE-FIX code, `cc12b46` (this branch's tip before the re-lap review's parse_served_show
    # finding -- byte-identical to what that review actually examined), against `show_corrupt`.
    pre_show_fix_src = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{PRE_SHOW_FIX_COMMIT}:tools/role_brief.py"],
        capture_output=True, text=True, check=True,
    ).stdout
    with tempfile.NamedTemporaryFile("w", suffix="_role_brief_pre_show_fix.py", delete=False) as f:
        f.write(pre_show_fix_src)
        pre_show_fix_path = Path(f.name)
    try:
        r4 = run_brief(pre_show_fix_path, "show_corrupt")
        r4_row2_missing = "row 2 [decision]" not in r4.stdout
        r4_decisions_empty = "## IN-FORCE DECISIONS" in r4.stdout and (
            "(none)" in r4.stdout.split("## IN-FORCE DECISIONS", 1)[1].split("##", 1)[0])
        check("R4-pre-show-fix-corrupt-actor-silently-drops-row",
              r4.returncode == 0 and r4_row2_missing and r4_decisions_empty,
              f"exit={r4.returncode} row-2-absent={r4_row2_missing} "
              f"decisions-section-empty={r4_decisions_empty} (pre-fix commit "
              f"{PRE_SHOW_FIX_COMMIT}, this branch's own tip before this addendum) -- a real "
              f"in-force decision row silently vanishes from IN-FORCE DECISIONS because its "
              f"`led show`'s width-drifted actor line was silently skipped, exactly the "
              f"silent-drop class this branch's earlier fixes killed in parse_current_line, "
              f"still alive in parse_served_show")
    finally:
        pre_show_fix_path.unlink(missing_ok=True)

    # R5: POST-FIX code, `show_corrupt` scenario -- must refuse loudly, naming the `led show 2`
    # line and command, never silently render an emptier brief.
    r5 = run_brief(POST_FIX_ROLE_BRIEF, "show_corrupt")
    r5_refused = ("REFUSED -- SHAPE DRIFT" in r5.stderr
                  and "show output line" in r5.stderr
                  and "show 2" in r5.stderr)
    r5_no_brief = "# BRIEF" not in r5.stdout or "STANDING" not in r5.stdout
    check("R5-post-fix-show-corrupt-refuses-loudly",
          r5.returncode == 1 and r5_refused and r5_no_brief,
          f"exit={r5.returncode} names-shape-drift={r5_refused} no-brief-rendered={r5_no_brief}\n"
          f"  stderr={r5.stderr.strip()!r}")

    # R6: POST-FIX code, `show_clean` scenario (same row 2, actor field at the correct width) --
    # row 2 renders in IN-FORCE DECISIONS, exit 0 -- the fix does not disturb the legitimate path.
    r6 = run_brief(POST_FIX_ROLE_BRIEF, "show_clean")
    r6_row2_present = "row 2 [decision]: role 's45' handles onboarding queue triage" in r6.stdout
    check("R6-post-fix-show-clean-row-renders",
          r6.returncode == 0 and r6_row2_present,
          f"exit={r6.returncode} row-2-in-decisions={r6_row2_present}")

    # R7: POST-FIX code, `show_longkey` scenario -- the module docstring's own CENTRAL motivating
    # case (residual #1): a real >=28-char column, unpadded, in an otherwise well-formed
    # `led show`. First, the end-to-end CLI: the full brief must render, exit 0, never a false
    # SHAPE DRIFT refusal. Second, directly alongside (same process, no subprocess needed --
    # served_shapes.py is a pure stdlib parsing library with no side effects): the CURRENT,
    # POST-FIX served_shapes.parse_served_show, called on the identical line, must return the
    # column IN its dict -- "renders" alone (nothing crashed) would not distinguish "parsed
    # correctly" from "silently dropped and nothing downstream happened to notice".
    r7 = run_brief(POST_FIX_ROLE_BRIEF, "show_longkey")
    r7_renders = "# BRIEF" in r7.stdout and "STANDING" in r7.stdout
    longkey_detail = served_shapes.parse_served_show(Exception, "<mock> show 1", LONGKEY_LINE)
    r7_field_present = (longkey_detail.get("principal_competence_activity")
                         == "onboarding-queue-triage")
    check("R7-post-fix-show-longkey-parses-and-renders",
          r7.returncode == 0 and r7_renders and r7_field_present,
          f"exit={r7.returncode} brief-renders={r7_renders} "
          f"field-present-in-parsed-dict={r7_field_present} "
          f"(parsed={longkey_detail!r}) -- the module docstring's own named motivating case, "
          f"now actually exercised")

    # R8: RED-FIRST, PRE-FIX CODE (`cc12b46`'s own tools/role_brief.py, the exact temp checkout
    # R4 already materialized above -- loaded in-process this time, since its parse_served_show
    # took only `text` with no error_cls/label yet, see served_shapes.py's own header on the
    # extraction). Called directly on the IDENTICAL `show_longkey` line: the fixed-slice
    # `line[28:30] != ": "` check silently `continue`s past it (29-char unpadded key means the
    # real separator sits at columns 29-31, not 28-30) -- the column is simply ABSENT from the
    # returned dict, the silent-drop class this fix round exists to kill, now shown on the
    # module's own named motivating case rather than only on R4's one-column actor-width drift.
    pre_show_fix_src = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{PRE_SHOW_FIX_COMMIT}:tools/role_brief.py"],
        capture_output=True, text=True, check=True,
    ).stdout
    with tempfile.NamedTemporaryFile("w", suffix="_role_brief_pre_show_fix_r8.py",
                                      delete=False) as f:
        f.write(pre_show_fix_src)
        pre_show_fix_path_r8 = Path(f.name)
    try:
        spec = importlib.util.spec_from_file_location("role_brief_cc12b46_r8", pre_show_fix_path_r8)
        old_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(old_mod)
        old_detail = old_mod.parse_served_show(LONGKEY_LINE)
        r8_silently_dropped = "principal_competence_activity" not in old_detail
        check("R8-pre-show-fix-longkey-silently-dropped",
              r8_silently_dropped,
              f"field-absent-from-parsed-dict={r8_silently_dropped} (pre-fix commit "
              f"{PRE_SHOW_FIX_COMMIT}) parsed={old_detail!r} -- the well-formed long-key line "
              f"vanishes with no error at all, not even the `continue`-based skip surfacing "
              f"anywhere; a caller reading this key back gets exactly the same shape as a "
              f"genuinely null column")
    finally:
        pre_show_fix_path_r8.unlink(missing_ok=True)

    if FAILURES:
        print(f"role-brief-current-line-shape-drift: {len(FAILURES)} case(s) FAILED: {FAILURES}")
        return 1
    print("all role-brief-current-line-shape-drift cases WITNESSED clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
