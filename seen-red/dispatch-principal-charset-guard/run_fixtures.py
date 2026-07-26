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

  A confirming review round on this same tool found four further issues; R6-R8 witness the
  moderate one and the length-cap half of the two minors closed by the same charset tightening
  (the other two minors -- the tool's own arg parser colliding with its own flag names, and the
  `--scan-limit` docstring's fetch-cost overclaim -- are documentation-only, named in the module
  and function docstrings rather than fixture-witnessed, since neither changes any code path):
  R6  RED-FIRST, PRE-FIX CODE (git 81a7268, this branch's own tip immediately before the
      moderate finding's fix): a leading-hyphen name (`-foo`) passes 81a7268's own charset
      pattern and reaches the registration check, which REFUSES (unregistered) and teaches a
      `led register-principal -foo subagent --purpose "..."` remediation. That EXACT taught
      command, extracted from the refusal's own printed text and actually run through
      `register_principal_argparse_witness.py` (the identical argparse shape `led.tmpl` itself
      uses for this verb), FAILS to parse -- the moderate finding reproduced end to end: the
      pre-fix tool's own teaching is non-actionable for exactly the names its charset let
      through.
  R7  POST-FIX CODE, GREEN counterpart to R6: the same leading-hyphen name now refuses on
      CHARSET before ever reaching the registration check, so no register-principal command is
      taught at all -- nothing left to be non-actionable.
  R8  POST-FIX CODE, the length-cap boundary: a 65-character name refuses on charset before any
      `led` call; a 64-character name is charset-legal and reaches the registration check.

  R9-R12 (ledger row 1384, dispatch-principal-run-led-shlex): a fresh migration micro-round
  flagged that `run_led`'s own `[led] + args` never shlex-split `led` at all and had none of
  the LedUnusable-class handling the three sibling `run_led` homes (drive.py's DRIVE_TEMPLATE,
  role_charter.py, role_brief.py) just got in the confirming-review round above -- same class,
  a fourth home, pre-existing at the time of that round (out of scope for it, filed instead).
  R9  RED-FIRST, PRE-FIX CODE (git 875d0cd, this branch's own tip immediately before this
      fix): a multi-token `--led "python3 <path>"` value -- a legitimate way to invoke a
      non-executable-bit `led` wrapper via its interpreter -- fails, `subprocess.run` treating
      the whole string as one literal (nonexistent) program name.
  R10 POST-FIX CODE, GREEN counterpart to R9: the identical multi-token `--led` value now
      shlex-splits into a real argv prefix and the dispatch succeeds.
  R11 POST-FIX CODE: an empty/whitespace `--led` value refuses BEFORE any subprocess is
      attempted (would otherwise exec args[0] itself as the program, silently).
  R12 POST-FIX CODE: a malformed-quoting `--led` value (an unterminated quote) is a named,
      teaching refusal, never an uncaught ValueError traceback.

Usage: python3 seen-red/dispatch-principal-charset-guard/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned; stdlib only.
"""
from __future__ import annotations

import json
import os
import shlex
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
# confirming review round's own pre-fix tip: this branch's HEAD immediately before the
# leading-hyphen/length-cap fix (R6 below) -- distinct from PRE_FIX_COMMIT above, which is the
# tip immediately before the ORIGINAL charset-injection fix (R1). Both are real commits on this
# branch's own history, not synthetic.
PRE_FIX_COMMIT_HYPHEN = "81a7268"
# row 1384's own pre-fix tip: this branch's HEAD immediately before the run_led shlex fix
# (R9-R12 below) -- distinct from both commits above, which predate two EARLIER fix rounds.
PRE_FIX_COMMIT_SHLEX = "875d0cd"
REGISTER_PRINCIPAL_ARGPARSE_WITNESS = HERE / "register_principal_argparse_witness.py"

HOSTILE_NAME = "builder$(touch PWNED)"
CLEAN_NAME = "builder-ok"
HYPHEN_NAME = "-foo"

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


def run_preamble_with_led(dispatch_principal_path: Path, name: str, led: str,
                           scenario: str) -> subprocess.CompletedProcess:
    """Same as run_preamble, but with an explicit, possibly multi-token/malformed/empty `--led`
    value -- R9-R12's own axis (row 1384), distinct from run_preamble's fixed MOCK_LED path."""
    return subprocess.run(
        [sys.executable, str(dispatch_principal_path), "preamble", name,
         "--led", led, "--scan-limit", "100"],
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


def materialize_git_blob(commit: str, relpath: str, suffix: str) -> Path:
    """Check out `<commit>:<relpath>` verbatim into a real temp file and return its path --
    the shared helper R1 and R6 both use so every "pre-fix" run below is a real subprocess
    executing the actual historical bytes, never a re-derivation or a monkeypatch."""
    src = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{commit}:{relpath}"],
        capture_output=True, text=True, check=True,
    ).stdout
    with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False) as f:
        f.write(src)
        return Path(f.name)


def main() -> int:
    print("=== dispatch-principal-charset-guard: seen-red witness ===\n")

    # R1: RED-FIRST, PRE-FIX CODE (b4bb250, byte-identical to this branch's own tip immediately
    # before this fix round) -- checked out into a real temp file, run as a real subprocess,
    # never imported/monkeypatched, so the eval-witness below evals text the actual pre-fix
    # binary actually printed.
    pre_fix_path = materialize_git_blob(PRE_FIX_COMMIT, "tools/dispatch_principal.py",
                                         "_dispatch_principal_pre_fix.py")
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

    # R6: RED-FIRST, PRE-FIX CODE (81a7268, this branch's own tip immediately before the
    # moderate finding's fix -- distinct commit from R1's b4bb250, the tip before the ORIGINAL
    # charset-injection fix) -- a leading-hyphen name (`-foo`) is charset-LEGAL under 81a7268's
    # own `^[A-Za-z0-9_-]+$` pattern, so `preamble` reaches the registration check, finds it
    # unregistered (mock scenario "empty"), and REFUSES teaching a `led register-principal -foo
    # subagent --purpose "..."` remediation. The moderate finding: that taught command is
    # non-actionable -- `led register-principal`'s own argparse treats a leading-`-` positional
    # as an unrecognized flag. Witnessed here by taking the EXACT teaching line 81a7268 printed,
    # extracting its own arguments, and actually running them through
    # register_principal_argparse_witness.py (the identical argparse shape `led.tmpl` itself
    # uses for this verb) -- one subprocess call, the real failure a caller pasting this taught
    # command would hit, not a re-derivation of "this looks like it wouldn't work."
    pre_fix_hyphen_path = materialize_git_blob(PRE_FIX_COMMIT_HYPHEN, "tools/dispatch_principal.py",
                                                "_dispatch_principal_pre_fix_hyphen.py")
    try:
        r6 = run_preamble(pre_fix_hyphen_path, HYPHEN_NAME, "empty")
        r6_charset_accepted = "not a valid principal name" not in r6.stderr
        taught_line = None
        for line in r6.stderr.splitlines():
            if "register-principal" in line and HYPHEN_NAME in line:
                taught_line = line.strip()
                break
        if taught_line is None:
            check("R6-pre-fix-leading-hyphen-accepted-teaches-unusable-command", False,
                  f"no register-principal teaching line found in stderr={r6.stderr!r}")
        else:
            # taught_line looks like: "<led> register-principal -foo subagent --purpose \"...\""
            taught_argv = shlex.split(taught_line)
            idx = taught_argv.index("register-principal")
            argparse_argv = taught_argv[idx + 1:]  # ['-foo', 'subagent', '--purpose', '<why...>']
            witness = subprocess.run(
                [sys.executable, str(REGISTER_PRINCIPAL_ARGPARSE_WITNESS)] + argparse_argv,
                capture_output=True, text=True,
            )
            r6_taught_command_fails = witness.returncode == 4
            check("R6-pre-fix-leading-hyphen-accepted-teaches-unusable-command",
                  r6.returncode == 1 and r6_charset_accepted and r6_taught_command_fails,
                  f"preamble-exit={r6.returncode} charset-accepted-the-name={r6_charset_accepted} "
                  f"taught-line={taught_line!r} taught-command-argparse-exit={witness.returncode} "
                  f"(4 == led.tmpl's own parse-failure exit) taught-command-stderr="
                  f"{witness.stderr.strip()!r} -- the moderate finding reproduced end to end: "
                  f"the pre-fix refusal's own remediation command does not parse")
    finally:
        pre_fix_hyphen_path.unlink(missing_ok=True)

    # R7: POST-FIX CODE, GREEN counterpart to R6 -- the same leading-hyphen name now refuses on
    # CHARSET before ever reaching the registration check or teaching any register-principal
    # command at all (nothing left to be non-actionable).
    r7 = run_preamble(POST_FIX_DISPATCH_PRINCIPAL, HYPHEN_NAME, "empty")
    r7_refused_charset = ("not a valid principal name" in r7.stderr
                           and "start with a letter, digit, or '_'" in r7.stderr)
    # the refusal text is allowed to MENTION `led register-principal` descriptively (it does,
    # explaining WHY a leading hyphen is unregistrable) -- what R6 proved must be gone is an
    # actual TAUGHT command line naming this specific hyphen name as an argument to it.
    r7_no_teaching = f"register-principal {HYPHEN_NAME} subagent" not in r7.stderr
    check("R7-post-fix-leading-hyphen-refused-on-charset-before-any-teaching",
          r7.returncode == 1 and r7_refused_charset and r7_no_teaching,
          f"exit={r7.returncode} refused-on-charset={r7_refused_charset} "
          f"no-register-principal-teaching={r7_no_teaching}\n  stderr={r7.stderr.strip()!r}")

    # R8: POST-FIX CODE, length-cap boundary (minor finding, confirming review round) -- a
    # 65-character name refuses on charset before any `led` call; a 64-character name is
    # charset-LEGAL (passes through to the registration check, which the "empty" scenario then
    # answers NOT-REGISTERED for, distinguishing "refused on charset" from "refused as
    # unregistered" by message content, same technique R3 uses).
    name_64 = "a" * 64
    name_65 = "a" * 65
    r8_65 = run_check("empty", name_65, json_flag=False)
    r8_65_refused_charset = ("not a valid principal name" in r8_65.stderr
                              and "at most 64" in r8_65.stderr)
    r8_64 = run_check("empty", name_64, json_flag=False)
    r8_64_passed_charset = ("not a valid principal name" not in r8_64.stderr
                             and "NOT-REGISTERED" in r8_64.stdout)
    check("R8-post-fix-length-cap-boundary-65-refused-64-accepted",
          r8_65.returncode == 1 and r8_65_refused_charset
          and r8_64.returncode == 1 and r8_64_passed_charset,
          f"65-char: exit={r8_65.returncode} refused-on-charset={r8_65_refused_charset} "
          f"stderr={r8_65.stderr.strip()!r}\n"
          f"  64-char: exit={r8_64.returncode} passed-charset-reached-registration-check="
          f"{r8_64_passed_charset} stdout={r8_64.stdout.strip()!r}")

    # R9: RED-FIRST, PRE-FIX CODE (875d0cd, this branch's own tip immediately before the
    # run_led shlex fix) -- a multi-token `--led "python3 <path>"` value fails as one literal
    # (nonexistent) program name, `subprocess.run` never shlex-splitting it.
    pre_fix_shlex_path = materialize_git_blob(PRE_FIX_COMMIT_SHLEX, "tools/dispatch_principal.py",
                                               "_dispatch_principal_pre_fix_shlex.py")
    multi_token_led = f"{sys.executable} {MOCK_LED}"
    try:
        r9 = run_preamble_with_led(pre_fix_shlex_path, CLEAN_NAME, multi_token_led, "clean-registered")
        r9_failed_as_one_literal = "No such file or directory" in r9.stderr
        check("R9-pre-fix-multi-token-led-fails-as-one-literal-program-name",
              r9.returncode == 1 and r9_failed_as_one_literal,
              f"exit={r9.returncode} led={multi_token_led!r} stderr={r9.stderr.strip()!r}")
    finally:
        pre_fix_shlex_path.unlink(missing_ok=True)

    # R10: POST-FIX CODE, GREEN counterpart to R9 -- the identical multi-token `--led` value
    # now shlex-splits into a real argv prefix and the dispatch succeeds.
    r10 = run_preamble_with_led(POST_FIX_DISPATCH_PRINCIPAL, CLEAN_NAME, multi_token_led, "clean-registered")
    check("R10-post-fix-multi-token-led-shlex-splits-and-succeeds",
          r10.returncode == 0 and r10.stdout.strip() == f"export LED_ACTOR={CLEAN_NAME}",
          f"exit={r10.returncode} led={multi_token_led!r} stdout={r10.stdout.strip()!r} stderr={r10.stderr.strip()!r}")

    # R11: POST-FIX CODE -- empty/whitespace `--led` refuses before any subprocess is attempted
    # (would otherwise exec args[0] itself as the program, silently).
    r11 = run_preamble_with_led(POST_FIX_DISPATCH_PRINCIPAL, CLEAN_NAME, "   ", "clean-registered")
    check("R11-post-fix-empty-led-refuses-before-any-exec",
          r11.returncode == 1 and "empty/whitespace" in r11.stderr
          and "export LED_ACTOR" not in r11.stdout,
          f"exit={r11.returncode} stderr={r11.stderr.strip()!r}")

    # R12: POST-FIX CODE -- malformed shell quoting in `--led` is a named, teaching refusal,
    # never an uncaught ValueError traceback.
    r12 = run_preamble_with_led(POST_FIX_DISPATCH_PRINCIPAL, CLEAN_NAME, 'unterminated "quote', "clean-registered")
    check("R12-post-fix-malformed-led-quoting-is-a-named-refusal-not-a-traceback",
          r12.returncode == 1 and "malformed shell quoting" in r12.stderr
          and "Traceback" not in r12.stderr,
          f"exit={r12.returncode} stderr={r12.stderr.strip()!r}")

    if FAILURES:
        print(f"dispatch-principal-charset-guard: {len(FAILURES)} case(s) FAILED: {FAILURES}")
        return 1
    print("all dispatch-principal-charset-guard cases WITNESSED clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
