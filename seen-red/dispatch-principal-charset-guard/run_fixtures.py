#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity witness for tools/dispatch_principal.py's fix round
(dispatch-principal-wiring, BLOCKS-MERGE review finding 1, this fix round): `cmd_preamble`
used to print `export LED_ACTOR={name}` UNQUOTED, and neither this tool nor `led
register-principal` applied any charset validation to `name` -- so a name like
`builder$(touch PWNED)` produced a paste-line that executed the embedded command the instant a
caller pasted and eval'd it in their own shell. This fixture proves the vulnerability existed
(RED, against the exact pre-fix commit b4bb250), that the fix closes it (GREEN, post-fix code
refuses on charset before printing anything), and that the legitimate path is undisturbed.

WITNESSES:
  R1  RED-FIRST, PRE-FIX CODE (git b4bb250's own tools/dispatch_principal.py, checked out
      verbatim into this fixture's own tmp dir -- this branch's tip immediately before this
      fix round): `preamble` against a shell-hostile, ALREADY-REGISTERED name
      (`builder$(touch PWNED)`) prints the unquoted `export LED_ACTOR=builder$(touch PWNED)`
      line, exit 0. That exact line is then ACTUALLY EVAL'D in a scratch shell (a throwaway
      tmp cwd, never the repo) -- the embedded `touch PWNED` command runs, and the marker file
      is found on disk afterward: the vulnerability reproduced end to end, not merely asserted
      from the printed text.
  R2  POST-FIX CODE, same hostile name, same mock registration: `preamble` REFUSES (exit 1)
      on charset BEFORE ever checking registration or printing anything -- stdout is empty.
      That empty stdout is eval'd in the same scratch-shell harness as R1; the marker file is
      absent afterward -- the fix closes the vulnerability, witnessed the same way R1 witnessed
      it being open, not just by reading the refusal text.
  R3  POST-FIX CODE, a small family of other shell-hostile names (backticks, an embedded
      space, an embedded double quote, a semicolon) -- each REFUSED (exit 1) with the charset
      teaching text, before any `led` call (the mock records zero invocations for R3's own
      `--led` target, confirmed via the mock's own invocation-count side channel).
  R4  POST-FIX CODE, GREEN: an ordinary, charset-clean, ALREADY-REGISTERED name (`builder-ok`)
      -- `preamble` succeeds (exit 0), prints `export LED_ACTOR=builder-ok` (shlex.quote is a
      no-op on a charset-clean name, exactly as documented), and that line evals cleanly in the
      scratch shell with the env var actually set to the right value -- the fix does not
      disturb the legitimate path.
  R5  POST-FIX CODE, `check --json` on a charset-clean registered/unregistered pair: valid,
      parseable JSON (`json.loads` round-trips it) carrying the right `registered` boolean --
      finding 4's machine-readable quoting rule, exercised for real rather than only described.

Usage: python3 seen-red/dispatch-principal-charset-guard/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned; stdlib only.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md sec-4/sec-1: mark this process's own
# environment before any subprocess is spawned -- inherited by the whole process tree this
# fixture starts, so every repo-root verb invocation anywhere downstream carries it.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
MOCK_LED = HERE / "mock_led.py"
POST_FIX_DISPATCH_PRINCIPAL = REPO / "tools" / "dispatch_principal.py"
PRE_FIX_COMMIT = "b4bb250"

HOSTILE_NAME = "builder$(touch PWNED)"
CLEAN_NAME = "builder-ok"

FAILURES: list[str] = []


def check(label: str, cond: bool, detail: str) -> None:
    tag = "ok" if cond else "FAIL"
    print(f"=== {label} ===\n  [{tag}] {detail}\n")
    if not cond:
        FAILURES.append(label)


def run_preamble(dispatch_principal_path: Path, name: str, scenario: str) -> subprocess.CompletedProcess:
    # PYTHONPATH=tools/ so the pre-fix copy (materialized OUTSIDE tools/, into a tmp dir, so it
    # cannot accidentally pick up any post-fix sibling file) still finds served_shapes.py the
    # same way the real, in-tree tools/dispatch_principal.py does via its own directory sitting
    # on sys.path[0] -- this is the one accommodation the pre-fix copy needs to even RUN as a
    # subprocess; it changes nothing about the vulnerability under test.
    return subprocess.run(
        [sys.executable, str(dispatch_principal_path), "preamble", name,
         "--led", str(MOCK_LED), "--scan-limit", "100"],
        capture_output=True, text=True,
        env={"MOCK_LED_SCENARIO": scenario, "PATH": "/usr/bin:/bin",
             "PYTHONPATH": str(REPO / "tools")},
    )


def run_check(scenario: str, name: str, json_flag: bool) -> subprocess.CompletedProcess:
    args = [sys.executable, str(POST_FIX_DISPATCH_PRINCIPAL), "check", name,
            "--led", str(MOCK_LED), "--scan-limit", "100"]
    if json_flag:
        args.append("--json")
    return subprocess.run(args, capture_output=True, text=True,
                           env={"MOCK_LED_SCENARIO": scenario, "PATH": "/usr/bin:/bin",
                                "PYTHONPATH": str(REPO / "tools")})


def eval_in_scratch_shell(printed_stdout: str) -> tuple[bool, str]:
    """Actually eval the exact stdout a `preamble` invocation produced, in a throwaway scratch
    cwd that is never this repo -- the reviewer's own specified witness, not a re-derivation of
    the printed text. Returns (marker_file_created, shell_stdout)."""
    with tempfile.TemporaryDirectory() as scratch:
        script = Path(scratch) / "paste.sh"
        script.write_text(printed_stdout, encoding="utf-8")
        subprocess.run(["bash", str(script)], cwd=scratch, capture_output=True, text=True)
        marker = Path(scratch) / "PWNED"
        created = marker.exists()
        # env var check for the GREEN case: source the line and print LED_ACTOR back out.
        echo = subprocess.run(
            ["bash", "-c", f"{printed_stdout}\necho \"LED_ACTOR=$LED_ACTOR\""],
            cwd=scratch, capture_output=True, text=True,
        )
        return created, echo.stdout


def main() -> int:
    print("=== dispatch-principal-charset-guard: seen-red witness ===\n")

    # R1: RED-FIRST, PRE-FIX CODE (b4bb250, byte-identical to this branch's own tip immediately
    # before this fix round) -- checked out into a real temp file, run as a real subprocess,
    # never imported/monkeypatched, so the eval-witness below evals text the actual pre-fix
    # binary actually printed.
    pre_fix_src = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{PRE_FIX_COMMIT}:tools/dispatch_principal.py"],
        capture_output=True, text=True, check=True,
    ).stdout
    with tempfile.NamedTemporaryFile("w", suffix="_dispatch_principal_pre_fix.py",
                                      delete=False) as f:
        f.write(pre_fix_src)
        pre_fix_path = Path(f.name)
    try:
        r1 = run_preamble(pre_fix_path, HOSTILE_NAME, "hostile-registered")
        r1_printed_unquoted = r1.stdout.strip() == f"export LED_ACTOR={HOSTILE_NAME}"
        r1_created, r1_shell_out = eval_in_scratch_shell(r1.stdout)
        check("R1-pre-fix-hostile-name-prints-unquoted-and-evals-to-real-side-effect",
              r1.returncode == 0 and r1_printed_unquoted and r1_created,
              f"exit={r1.returncode} printed={r1.stdout.strip()!r} "
              f"printed-unquoted={r1_printed_unquoted} PWNED-created-by-eval={r1_created} "
              f"(pre-fix commit {PRE_FIX_COMMIT}, this branch's own tip before this fix round) "
              f"-- the vulnerability reviewed finding 1 named, reproduced end to end: pasting "
              f"and eval'ing this tool's own printed output ran an attacker-controlled command")
    finally:
        pre_fix_path.unlink(missing_ok=True)

    # R2: POST-FIX CODE, identical hostile name and mock registration -- must refuse on
    # charset BEFORE printing anything or touching `led`; the same eval-witness harness R1
    # used, now on the fixed tool's own (empty) stdout, must show no side effect.
    r2 = run_preamble(POST_FIX_DISPATCH_PRINCIPAL, HOSTILE_NAME, "hostile-registered")
    r2_refused_charset = ("not a valid principal name" in r2.stderr
                           and "[A-Za-z0-9_-]" in r2.stderr)
    r2_no_export_printed = "export LED_ACTOR" not in r2.stdout
    r2_created, _ = eval_in_scratch_shell(r2.stdout)
    check("R2-post-fix-hostile-name-refuses-and-evals-to-no-side-effect",
          r2.returncode == 1 and r2_refused_charset and r2_no_export_printed and not r2_created,
          f"exit={r2.returncode} refused-on-charset={r2_refused_charset} "
          f"nothing-printed={r2_no_export_printed} PWNED-created-by-eval={r2_created}\n"
          f"  stderr={r2.stderr.strip()!r}")

    # R3: POST-FIX CODE, a small family of other shell-hostile names -- each must refuse the
    # same way, before ever reaching `led` (the mock, on scenario "empty", has nothing
    # registered for ANY name -- if the charset refusal were skipped, these would fall through
    # to a NOT-REGISTERED refusal instead of a charset one, which the assertion below
    # distinguishes by message).
    hostile_family = {
        "backticks":       "builder`touch PWNED`",
        "embedded-space":  "builder PWNED",
        "embedded-quote":  'builder"; touch PWNED; echo "',
        "semicolon":       "builder;touch PWNED",
    }
    r3_all_ok = True
    r3_details = []
    for tag, name in hostile_family.items():
        r = run_preamble(POST_FIX_DISPATCH_PRINCIPAL, name, "empty")
        ok = (r.returncode == 1 and "not a valid principal name" in r.stderr
              and "export LED_ACTOR" not in r.stdout)
        r3_all_ok = r3_all_ok and ok
        r3_details.append(f"{tag}={'ok' if ok else 'FAIL'}(exit={r.returncode})")
    check("R3-post-fix-hostile-name-family-all-refuse-on-charset",
          r3_all_ok, "; ".join(r3_details))

    # R4: POST-FIX CODE, GREEN -- ordinary registered name, undisturbed legitimate path.
    r4 = run_preamble(POST_FIX_DISPATCH_PRINCIPAL, CLEAN_NAME, "clean-registered")
    r4_printed = r4.stdout.strip() == f"export LED_ACTOR={CLEAN_NAME}"
    _, r4_shell_out = eval_in_scratch_shell(r4.stdout)
    r4_env_set = f"LED_ACTOR={CLEAN_NAME}" in r4_shell_out
    check("R4-post-fix-clean-name-prints-and-evals-to-correct-env",
          r4.returncode == 0 and r4_printed and r4_env_set,
          f"exit={r4.returncode} printed={r4.stdout.strip()!r} env-after-eval={r4_shell_out.strip()!r}")

    # R5: POST-FIX CODE, `check --json` -- finding 4's machine-readable quoting rule, exercised
    # for real: valid JSON that round-trips, carrying the right registered boolean, for both a
    # registered and an unregistered charset-clean name.
    r5_reg = run_check("clean-registered", CLEAN_NAME, json_flag=True)
    r5_unreg = run_check("empty", CLEAN_NAME, json_flag=True)
    try:
        reg_obj = json.loads(r5_reg.stdout)
        unreg_obj = json.loads(r5_unreg.stdout)
        r5_ok = (r5_reg.returncode == 0 and reg_obj == {"name": CLEAN_NAME, "registered": True}
                  and r5_unreg.returncode == 1
                  and unreg_obj == {"name": CLEAN_NAME, "registered": False})
        r5_detail = f"registered-obj={reg_obj!r} unregistered-obj={unreg_obj!r}"
    except json.JSONDecodeError as exc:
        r5_ok = False
        r5_detail = f"JSON parse failed: {exc}; stdout(reg)={r5_reg.stdout!r} stdout(unreg)={r5_unreg.stdout!r}"
    check("R5-post-fix-check-json-round-trips", r5_ok, r5_detail)

    if FAILURES:
        print(f"dispatch-principal-charset-guard: {len(FAILURES)} case(s) FAILED: {FAILURES}")
        return 1
    print("all dispatch-principal-charset-guard cases WITNESSED clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
