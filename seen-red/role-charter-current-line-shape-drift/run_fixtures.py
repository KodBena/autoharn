#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity witness for tools/role_charter.py's fix round (row 1295,
flagged by tools/role_brief.py's own 417b200 fix-round commit as an identical shape out of that
commit's scope -- see mock_led.py's own docstring in this same directory for the full defect
description and this fixture's disclosed mock-vs-real-infra scoping).

WITNESSES:
  R1  RED-FIRST, PRE-FIX CODE (git 417b200's own tools/role_charter.py, checked out verbatim
      into this fixture's tmp dir -- the exact code this work item's ledger row (1295) named):
      against the `corrupt` scenario, `register` silently writes a SECOND, conflicting
      charter-registration row and exits 0 -- the existing in-force registration was invisible
      to `find_current_registrations` because its `current` line was skipped, so this tool's
      own JC4 double-registration refusal never fires. The vacuous-pass reproduced directly.
  R2  POST-FIX CODE, `corrupt` scenario: refuses loudly -- CharterError naming the offending
      line and the producing command (`<led> current <N>`), exit 1. Nothing is registered.
  R3  POST-FIX CODE, `clean` scenario (same registration row, not corrupted): `register` sees
      the existing row and correctly REFUSES via JC4 ("already carries an in-force charter
      registration"), exit 1 -- the fix does not disturb the legitimate refusal path.
  R4  RED-FIRST, PRE-FIX CODE (git cc12b46's own tools/role_charter.py -- this branch's tip
      BEFORE the re-lap review's parse_served_show finding): against `show_corrupt`, `show`'s
      best-effort written_by lookup silently drops row 7's width-drifted 'actor' line and
      renders "written by actor id '(unknown)'", exit 0 -- a real field silently
      misrepresented as absent.
  R5  POST-FIX CODE, `show_corrupt` scenario: `show` refuses loudly -- CharterError naming the
      offending `led show 7` line and command, exit 1.
  R6  POST-FIX CODE, `show_clean` scenario (same row 7, actor field at the correct width):
      `show` renders the real actor id, exit 0 -- the fix does not disturb the legitimate path.
  R7  POST-FIX CODE, `show_longkey` scenario (this fix round's residual #1 -- served_shapes.py's
      own module docstring names a real >=28-char column, `principal_competence_activity`
      (29 chars), as its CENTRAL motivating case; nothing exercised it before this addendum):
      row 7's `led show 7` output carries that column UNPADDED, exactly as cmd_show really
      emits it, alongside its own correctly-padded `actor` line. `show editor` renders
      end-to-end, exit 0 -- a well-formed line is never refused as a false SHAPE DRIFT.
      Directly alongside: served_shapes.parse_served_show, called in-process against the exact
      same line, returns the column IN its dict (the parse itself, not merely "nothing
      crashed").
  R8  RED-FIRST, PRE-FIX CODE (git cc12b46's own parse_served_show, loaded in-process from the
      same temp checkout R4 already materializes above). Called directly on the IDENTICAL
      `show_longkey` line: the fixed-slice `line[28:30] != ": "` check silently `continue`s past
      it (29-char unpadded key means the real separator sits at columns 29-31, not 28-30) -- the
      column is simply ABSENT from the returned dict, the silent-drop class this fix round
      exists to kill, now shown on the module's own named motivating case rather than only on
      R4's one-column actor-width drift.

Usage: python3 seen-red/role-charter-current-line-shape-drift/run_fixtures.py
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
POST_FIX_ROLE_CHARTER = REPO / "tools" / "role_charter.py"
PRE_FIX_COMMIT = "417b200"
PRE_SHOW_FIX_COMMIT = "cc12b46"

# R7/R8 below call served_shapes.parse_served_show directly (the post-fix module) rather than
# only through a subprocess -- served_shapes.py is a pure stdlib parsing library with no side
# effects, so a direct in-process call is the cheapest honest way to assert "the field is
# actually IN the parsed dict" rather than merely "the CLI process didn't crash". Imported here,
# at module top (CLAUDE.md's lazy-imports ban applies to this fixture script too -- gates/
# no_lazy_imports.py does not exclude seen-red/), immediately after putting tools/ on sys.path.
sys.path.insert(0, str(REPO / "tools"))
import served_shapes

# Shared with mock_led.py's own SHOW_ROWS["7"] `show_longkey` line -- the exact byte shape
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


def run_register(role_charter_path: Path, scenario: str, charter_file: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(role_charter_path), "register", "editor", str(charter_file),
         "--led", str(MOCK_LED), "--scan-limit", "100"],
        capture_output=True, text=True,
        env={"MOCK_LED_SCENARIO": scenario, "PATH": "/usr/bin:/bin"},
    )


def run_show(role_charter_path: Path, scenario: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(role_charter_path), "show", "editor",
         "--led", str(MOCK_LED), "--scan-limit", "100"],
        capture_output=True, text=True,
        env={"MOCK_LED_SCENARIO": scenario, "PATH": "/usr/bin:/bin"},
    )


def main() -> int:
    print("=== role-charter-current-line-shape-drift: seen-red witness ===\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        charter_file = Path(tmpdir) / "CHARTER.md"
        charter_file.write_text("# editor charter\n\nfixture only -- binds nothing real.\n",
                                 encoding="utf-8")

        # R1: PRE-FIX code (417b200, byte-identical to what row 1295 named), against the
        # corrupted fixture. Materialized into a real tmp file so subprocess.run stays uniform
        # with the post-fix invocation (no cross-import, no monkeypatching -- a real separate
        # process running the real pre-fix bytes).
        pre_fix_src = subprocess.run(
            ["git", "-C", str(REPO), "show", f"{PRE_FIX_COMMIT}:tools/role_charter.py"],
            capture_output=True, text=True, check=True,
        ).stdout
        with tempfile.NamedTemporaryFile("w", suffix="_role_charter_pre_fix.py",
                                          delete=False) as f:
            f.write(pre_fix_src)
            pre_fix_path = Path(f.name)
        try:
            r1 = run_register(pre_fix_path, "corrupt", charter_file)
            r1_dup = "role_charter: registered -- role 'editor' -> charter row 9" in r1.stdout
            check("R1-pre-fix-corrupt-silently-writes-duplicate-registration",
                  r1.returncode == 0 and r1_dup,
                  f"exit={r1.returncode} wrote-duplicate-registration={r1_dup} (pre-fix commit "
                  f"{PRE_FIX_COMMIT}, the exact code row 1295 named) -- this is the vacuous "
                  f"pass: an existing in-force registration is invisible because its corrupted "
                  f"`current` line was silently skipped, so JC4's double-registration refusal "
                  f"never fires and a second, conflicting registration is written, exit 0")
        finally:
            pre_fix_path.unlink(missing_ok=True)

        # R2: POST-FIX code, corrupt scenario -- must refuse loudly, never register.
        r2 = run_register(POST_FIX_ROLE_CHARTER, "corrupt", charter_file)
        r2_refused = ("REFUSED -- SHAPE DRIFT" in r2.stderr
                      and "does not match the expected `[id] kind: statement` shape" in r2.stderr
                      and "current 100" in r2.stderr
                      and "TRUNCATED ROW" in r2.stderr)
        r2_no_register = "role_charter: registered" not in r2.stdout
        check("R2-post-fix-corrupt-refuses-loudly",
              r2.returncode == 1 and r2_refused and r2_no_register,
              f"exit={r2.returncode} names-shape-drift={r2_refused} "
              f"no-registration-written={r2_no_register}\n  stderr={r2.stderr.strip()!r}")

        # R3: POST-FIX code, clean scenario -- the existing registration is SEEN, so `register`
        # correctly refuses via JC4 (this tool's own duplicate-registration guard), exit 1 --
        # the fix does not disturb the legitimate refusal path.
        r3 = run_register(POST_FIX_ROLE_CHARTER, "clean", charter_file)
        r3_jc4 = "already carries an in-force charter registration" in r3.stderr
        r3_no_register = "role_charter: registered" not in r3.stdout
        check("R3-post-fix-clean-existing-registration-correctly-refused",
              r3.returncode == 1 and r3_jc4 and r3_no_register,
              f"exit={r3.returncode} names-existing-registration={r3_jc4} "
              f"no-registration-written={r3_no_register}")

        # R4: PRE-FIX code, `cc12b46` (this branch's tip before the re-lap review's
        # parse_served_show finding -- byte-identical to what that review actually examined),
        # against `show_corrupt`.
        pre_show_fix_src = subprocess.run(
            ["git", "-C", str(REPO), "show", f"{PRE_SHOW_FIX_COMMIT}:tools/role_charter.py"],
            capture_output=True, text=True, check=True,
        ).stdout
        with tempfile.NamedTemporaryFile("w", suffix="_role_charter_pre_show_fix.py",
                                          delete=False) as f:
            f.write(pre_show_fix_src)
            pre_show_fix_path = Path(f.name)
        try:
            r4 = run_show(pre_show_fix_path, "show_corrupt")
            r4_unknown = "written by actor id '(unknown)'" in r4.stdout
            check("R4-pre-show-fix-corrupt-actor-silently-shows-unknown",
                  r4.returncode == 0 and r4_unknown,
                  f"exit={r4.returncode} written-by-silently-unknown={r4_unknown} (pre-fix "
                  f"commit {PRE_SHOW_FIX_COMMIT}, this branch's own tip before this addendum) -- "
                  f"a real 'actor' field silently vanishes because its width-drifted `led show` "
                  f"line was silently skipped, exactly the silent-drop class this branch's "
                  f"earlier fixes killed in parse_current_line, still alive in "
                  f"parse_served_show")
        finally:
            pre_show_fix_path.unlink(missing_ok=True)

        # R5: POST-FIX code, `show_corrupt` scenario -- must refuse loudly, naming the
        # `led show 7` line and command, never silently render "(unknown)".
        r5 = run_show(POST_FIX_ROLE_CHARTER, "show_corrupt")
        r5_refused = ("REFUSED -- SHAPE DRIFT" in r5.stderr
                      and "show output line" in r5.stderr
                      and "show 7" in r5.stderr)
        r5_no_show = "IN-FORCE charter registration" not in r5.stdout
        check("R5-post-fix-show-corrupt-refuses-loudly",
              r5.returncode == 1 and r5_refused and r5_no_show,
              f"exit={r5.returncode} names-shape-drift={r5_refused} no-show-rendered={r5_no_show}\n"
              f"  stderr={r5.stderr.strip()!r}")

        # R6: POST-FIX code, `show_clean` scenario (same row 7, actor field at the correct
        # width) -- `show` renders the real actor id, exit 0 -- the fix does not disturb the
        # legitimate path.
        r6 = run_show(POST_FIX_ROLE_CHARTER, "show_clean")
        r6_actor_shown = "written by actor id '1'" in r6.stdout
        check("R6-post-fix-show-clean-actor-renders",
              r6.returncode == 0 and r6_actor_shown,
              f"exit={r6.returncode} actor-id-rendered={r6_actor_shown}\n  stdout={r6.stdout.strip()!r}")

        # R7: POST-FIX code, `show_longkey` scenario -- the module docstring's own CENTRAL
        # motivating case (residual #1): a real >=28-char column, unpadded, in an otherwise
        # well-formed `led show`. `show editor` prints the raw `led show 7` text verbatim under
        # its own "-- full ledger row --" banner (role_charter.py's own cmd_show), so the
        # long-key line's LITERAL, unpadded appearance in stdout is direct rendered evidence, not
        # just "nothing crashed". Alongside: the CURRENT, POST-FIX served_shapes.parse_served_show
        # (same process, no subprocess needed -- a pure stdlib parsing library with no side
        # effects), called on the identical line, must also return the column IN its dict.
        r7 = run_show(POST_FIX_ROLE_CHARTER, "show_longkey")
        r7_renders = "written by actor id '1'" in r7.stdout
        r7_line_verbatim = LONGKEY_LINE.rstrip("\n") in r7.stdout
        longkey_detail = served_shapes.parse_served_show(Exception, "<mock> show 7", LONGKEY_LINE)
        r7_field_present = (longkey_detail.get("principal_competence_activity")
                             == "onboarding-queue-triage")
        check("R7-post-fix-show-longkey-parses-and-renders",
              r7.returncode == 0 and r7_renders and r7_line_verbatim and r7_field_present,
              f"exit={r7.returncode} show-renders={r7_renders} "
              f"longkey-line-verbatim-in-stdout={r7_line_verbatim} "
              f"field-present-in-parsed-dict={r7_field_present} "
              f"(parsed={longkey_detail!r}) -- the module docstring's own named motivating "
              f"case, now actually exercised")

        # R8: RED-FIRST, PRE-FIX CODE (`cc12b46`'s own tools/role_charter.py, the exact temp
        # checkout R4 already materialized above -- loaded in-process this time, since its
        # parse_served_show took only `text` with no error_cls/label yet, see served_shapes.py's
        # own header on the extraction). Called directly on the IDENTICAL `show_longkey` line:
        # the fixed-slice `line[28:30] != ": "` check silently `continue`s past it (29-char
        # unpadded key means the real separator sits at columns 29-31, not 28-30) -- the column
        # is simply ABSENT from the returned dict, the silent-drop class this fix round exists
        # to kill, now shown on the module's own named motivating case rather than only on R4's
        # one-column actor-width drift.
        pre_show_fix_src_r8 = subprocess.run(
            ["git", "-C", str(REPO), "show", f"{PRE_SHOW_FIX_COMMIT}:tools/role_charter.py"],
            capture_output=True, text=True, check=True,
        ).stdout
        with tempfile.NamedTemporaryFile("w", suffix="_role_charter_pre_show_fix_r8.py",
                                          delete=False) as f:
            f.write(pre_show_fix_src_r8)
            pre_show_fix_path_r8 = Path(f.name)
        try:
            spec = importlib.util.spec_from_file_location("role_charter_cc12b46_r8",
                                                            pre_show_fix_path_r8)
            old_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(old_mod)
            old_detail = old_mod.parse_served_show(LONGKEY_LINE)
            r8_silently_dropped = "principal_competence_activity" not in old_detail
            check("R8-pre-show-fix-longkey-silently-dropped",
                  r8_silently_dropped,
                  f"field-absent-from-parsed-dict={r8_silently_dropped} (pre-fix commit "
                  f"{PRE_SHOW_FIX_COMMIT}) parsed={old_detail!r} -- the well-formed long-key "
                  f"line vanishes with no error at all, not even the `continue`-based skip "
                  f"surfacing anywhere; a caller reading this key back gets exactly the same "
                  f"shape as a genuinely null column")
        finally:
            pre_show_fix_path_r8.unlink(missing_ok=True)

    if FAILURES:
        print(f"role-charter-current-line-shape-drift: {len(FAILURES)} case(s) FAILED: {FAILURES}")
        return 1
    print("all role-charter-current-line-shape-drift cases WITNESSED clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
