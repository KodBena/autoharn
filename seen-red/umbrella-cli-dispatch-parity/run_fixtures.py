#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for design/FABLE-AUTOHARN-UMBRELLA-CLI-SPEC.md §1/§7:
the generated `autoharn --help` roster cannot drift from what actually runs, the ten relocated
verbs are reachable BOTH via `./autoharn <verb>` and via their deprecated `./<verb>` alias
shims, and an unrecognized verb refuses loudly teaching the same roster.

Cases:
  a-libexec-roster-matches-dispatch-table -- every file under libexec/autoharn/ has an entry in
                                 `autoharn`'s own dispatch table, and vice versa (RED if either
                                 side has an entry the other lacks).
  b-help-mentions-every-verb -- `autoharn --help`'s stdout names every libexec/autoharn/ verb
                                 (mechanical grep, not hand-maintained).
  c-alias-shim-still-works -- each deprecated `./<verb>` alias execs successfully (--help exits
                                 0, or its own pre-existing --help behavior, both proving the
                                 relocation did not break dispatch) AND prints its one-line
                                 deprecation notice to stderr.
  d-unknown-verb-refuses -- `autoharn frobnicate-not-a-verb` exits 2, refuses without touching
                                 anything, and its stderr names the known roster.
  e-service-is-handled-directly -- `autoharn service --help` exits 0 without going through
                                 libexec/autoharn/ (service is not one of the ten relocated verbs).
  f-real-invocation-reaches-libexec -- round-1 review SEVERE-1: runs `./autoharn <verb> --help`
                                 (a read-only, side-effect-free probe -- confirmed per verb below)
                                 for EVERY verb in the dispatch table (the SAME parsed roster case
                                 a checks, via `_parsed_table_verbs` -- round-2 review MODERATE
                                 fix: this case used to iterate a separately hand-typed
                                 `_EXPECTED_VERBS` census, so a new verb added only to the dispatch
                                 table would never be auto-covered here; now there is one parse,
                                 not two hand-synced lists) and asserts the dispatcher's own `exec`
                                 actually reached the real `libexec/autoharn/<verb>` file, rather
                                 than merely checking --help/alias-deprecation text that a broken
                                 exec line could still satisfy. A reviewer had injected `exec
                                 "$LIBEXEC/$VERB-BROKEN" "$@"` into ./autoharn and NO existing case
                                 (a/b/c/d/e above) went red -- case c in particular only checks the
                                 ALIAS shim's own deprecation line, which prints unconditionally
                                 BEFORE the alias's own `exec ./autoharn <verb>` call, so it stayed
                                 green even when that later exec failed outright (shell exit 127,
                                 "No such file or directory"). This case instead runs `./autoharn
                                 <verb>` directly (not through the alias) and asserts: exit code is
                                 never 127, and neither stdout nor stderr carries the shell's own
                                 exec-target-missing text -- the one signature a broken dispatch
                                 line produces that no verb's own real refusal text would ever
                                 spell. `--help` was verified (by hand, this round) side-effect-
                                 free for all ten verbs: six (led, pickup, attest-tags, migrate,
                                 asof-export, audit) print real usage text and exit 0; the other
                                 four (judge, distance-to-clean, doctor, verify-chain) refuse
                                 loudly BEFORE any write -- this repo's own root has no
                                 deployment.json, so each of those four's own construction-time
                                 "no deployment record"/"no Postgres host resolved" refusal fires
                                 first, which is itself still proof the REAL script ran (the exact
                                 refusal text is verb-specific, never the shell's own generic
                                 "not found"). ALSO (round-2 review AXIS 1 disqualifying fix): a
                                 wrong-target dispatch -- a verb FILE whose content is a DIFFERENT
                                 verb's implementation, filename right, content wrong, the exact
                                 risk of a ten-file relocation -- would still satisfy every check
                                 above (exit 0, real-looking usage text, no shell exec-failure
                                 signature). So this case additionally asserts VERB IDENTITY: the
                                 combined stdout+stderr of `./autoharn <verb> --help` must contain
                                 that verb's own name as a literal substring (verified per verb, by
                                 hand, this round -- every one of the ten already does, e.g. "led --
                                 read from..." / "usage: attest-tags ..." / "judge: deployment
                                 record not found..."). `audit` was the one verb that FAILED this
                                 when first checked (its --help fell all the way through to
                                 engine/contemp_audit.py's eager, import-time PGHOST resolution
                                 before argparse ever saw argv, producing the SAME generic
                                 "REFUSED: no Postgres host resolved" text every OTHER
                                 PGHOST-needing verb produces, no "audit" substring anywhere) --
                                 fixed per the reviewer's own instruction (a marker added to the
                                 TEMPLATE, not a weakened assertion): bootstrap/templates/audit.tmpl
                                 now intercepts --help/-h itself, before any Python/DB code runs,
                                 and prints a real, self-identifying usage line.
  g-help-sweep-never-writes -- round-2 review AXIS 1 moderate fix: `./autoharn`'s own comment
                                 claimed "this TOP-LEVEL `autoharn --help`/`autoharn service
                                 --help` behavior IS witnessed directly by ... case f ... and
                                 never writes" -- case f never actually witnessed top-level --help
                                 (that is cases a/b/e) NOR "never writes" (nothing did). This case
                                 witnesses the never-writes claim directly: a `git status
                                 --porcelain` snapshot of the whole repo, taken immediately before
                                 and immediately after running `autoharn --help`, `autoharn service
                                 --help`, and `autoharn <verb> --help` for every verb in the parsed
                                 dispatch table (the same sweep case f drives), asserts byte-
                                 identical output -- proving the entire --help surface leaves
                                 zero filesystem trace, not merely asserting it in prose.

RUN: python3 seen-red/umbrella-cli-dispatch-parity/run_fixtures.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AUTOHARN = REPO_ROOT / "autoharn"
LIBEXEC = REPO_ROOT / "libexec" / "autoharn"

# The ten relocated verbs -- named here, once, as this fixture's OWN expectation (not derived
# from the dispatch table itself, or a defect in the table could never be caught: this is the
# independent census the parity check below compares the table against).
_EXPECTED_VERBS = {
    "led", "judge", "pickup", "distance-to-clean", "attest-tags", "audit", "doctor",
    "migrate", "asof-export", "verify-chain",
}


def _run(argv: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, capture_output=True, text=True, cwd=str(REPO_ROOT), **kw)


def _parsed_table_verbs(help_out: str) -> set[str]:
    """The ONE parse of `autoharn --help`'s own "verbs:" block (one "  <verb><spaces>
    <description>" line per entry) -- round-2 review MODERATE fix: this used to live only inside
    case a; case f separately iterated a hand-typed `_EXPECTED_VERBS` census, so a new verb added
    to the dispatch table (autoharn's own cat<<'EOF' block) was never automatically covered by
    case f's per-verb sweep. Both case a (which still separately checks the parsed table against
    the independent on-disk census, `_EXPECTED_VERBS`, below -- that comparison is the whole
    point of case a and stays) and case f (which now iterates THIS parsed set, minus 'service')
    call this SAME function -- one parse, not two hand-synced lists."""
    lines = help_out.splitlines()
    start = lines.index("verbs:") + 1
    table_verbs = set()
    for line in lines[start:]:
        if not line.startswith("  "):
            break
        table_verbs.add(line.split()[0])
    return table_verbs


def case_a_libexec_roster_matches_dispatch_table() -> bool:
    on_disk = {p.name for p in LIBEXEC.iterdir() if p.is_file()}
    help_out = _run([str(AUTOHARN), "--help"]).stdout
    table_verbs = _parsed_table_verbs(help_out)
    ok = True
    missing_from_table = on_disk - table_verbs
    extra_in_table = (table_verbs - on_disk) - {"service"}  # service is handled directly, not on disk
    if missing_from_table:
        print(f"a-libexec-roster-matches-dispatch-table: FAIL -- on disk but not in --help: {sorted(missing_from_table)}")
        ok = False
    if extra_in_table:
        print(f"a-libexec-roster-matches-dispatch-table: FAIL -- in --help but not on disk: {sorted(extra_in_table)}")
        ok = False
    if on_disk != _EXPECTED_VERBS:
        print(f"a-libexec-roster-matches-dispatch-table: FAIL -- libexec/autoharn/ roster drifted "
              f"from this fixture's own census: disk={sorted(on_disk)} expected={sorted(_EXPECTED_VERBS)}")
        ok = False
    if ok:
        print("a-libexec-roster-matches-dispatch-table: PASS")
    return ok


def case_b_help_mentions_every_verb() -> bool:
    help_out = _run([str(AUTOHARN), "--help"]).stdout
    missing = [v for v in _EXPECTED_VERBS | {"service"} if v not in help_out]
    if missing:
        print(f"b-help-mentions-every-verb: FAIL -- --help never mentions {missing}")
        return False
    print("b-help-mentions-every-verb: PASS")
    return True


def case_c_alias_shim_still_works() -> bool:
    ok = True
    for verb in sorted(_EXPECTED_VERBS):
        r = _run([str(REPO_ROOT / verb), "--help"])
        if f"DEPRECATED spelling -- use 'autoharn {verb}'" not in r.stderr:
            print(f"c-alias-shim-still-works: FAIL -- ./{verb} --help printed no deprecation notice")
            ok = False
    if ok:
        print("c-alias-shim-still-works: PASS (all ten alias shims print their deprecation notice)")
    return ok


def case_d_unknown_verb_refuses() -> bool:
    r = _run([str(AUTOHARN), "frobnicate-not-a-verb"])
    if r.returncode != 2:
        print(f"d-unknown-verb-refuses: FAIL -- exit {r.returncode}, expected 2")
        return False
    if "REFUSED" not in r.stderr or "frobnicate-not-a-verb" not in r.stderr:
        print("d-unknown-verb-refuses: FAIL -- stderr does not teach the unrecognized verb by name")
        return False
    if "Known verbs:" not in r.stderr:
        print("d-unknown-verb-refuses: FAIL -- stderr does not name the known roster")
        return False
    print("d-unknown-verb-refuses: PASS (RED case: exit 2, named refusal, roster taught)")
    return True


def case_e_service_is_handled_directly() -> bool:
    r = _run([str(AUTOHARN), "service", "--help"])
    if r.returncode != 0:
        print(f"e-service-is-handled-directly: FAIL -- exit {r.returncode}")
        return False
    if "status" not in r.stdout or "start" not in r.stdout or "stop" not in r.stdout:
        print("e-service-is-handled-directly: FAIL -- usage does not name status/start/stop")
        return False
    print("e-service-is-handled-directly: PASS")
    return True


def case_f_real_invocation_reaches_libexec() -> bool:
    # The one shell-level signature a broken `exec "$LIBEXEC/$VERB-BROKEN" "$@"` (or any dispatch
    # line naming a nonexistent file) produces -- distinct from every verb's own real refusal
    # text, which is always verb-specific prose, never this generic shell diagnostic.
    _EXEC_FAILURE_SIGNATURE = "No such file or directory"
    # Round-2 review MODERATE fix: iterate the PARSED dispatch table (case a's own source of
    # truth via `_parsed_table_verbs`), not a second, separately hand-typed census -- a new verb
    # dropped into the dispatch table is auto-covered here without touching this file. 'service'
    # is excluded: it is not a libexec/autoharn/<verb> file, and case e already covers it.
    help_out = _run([str(AUTOHARN), "--help"]).stdout
    verbs = sorted(_parsed_table_verbs(help_out) - {"service"})
    ok = True
    for verb in verbs:
        r = _run([str(AUTOHARN), verb, "--help"])
        combined = r.stdout + r.stderr
        if r.returncode == 127 or _EXEC_FAILURE_SIGNATURE in combined:
            print(f"f-real-invocation-reaches-libexec: FAIL -- 'autoharn {verb} --help' exit "
                  f"{r.returncode} looks like a broken dispatch, not the real verb "
                  f"(combined output: {combined!r})")
            ok = False
            continue
        if not combined.strip():
            print(f"f-real-invocation-reaches-libexec: FAIL -- 'autoharn {verb} --help' produced "
                  f"no output at all -- cannot confirm the real script ran")
            ok = False
            continue
        # ROUND-2 REVIEW AXIS 1 DISQUALIFYING FIX: a wrong-target dispatch (a verb FILE whose
        # CONTENT is a DIFFERENT verb's implementation -- filename right, implementation wrong,
        # exactly the risk of a ten-file relocation) would satisfy every check above: exit 0 (or
        # whatever exit the OTHER verb's --help produces), plausible-looking usage/refusal text,
        # no shell exec-failure signature. Catch it by asserting VERB IDENTITY: this verb's own
        # name must appear, literally, as a whole token, somewhere in its own --help output.
        # WHOLE-TOKEN, not a bare substring test: a bare `verb in combined` check was FIRST
        # tried and itself went red on a legitimate case -- "led" is a substring of "ledger",
        # so pickup's real --help text ("... only ledger rows newer than this ...") served under
        # `led`'s own filename (the reviewer's exact attack, reproduced below) still satisfied a
        # bare substring check. The boundary below (neither character adjacent to the match may
        # be alnum/hyphen/underscore) treats hyphenated verb names as one token and rejects
        # "ledger" while still matching "led -- read from...", "usage: attest-tags ...", etc. --
        # every one of the ten verbs' real --help text was verified (by hand, this round) to
        # satisfy this exact boundary check; see this file's own module docstring.
        if re.search(rf"(?<![A-Za-z0-9_-]){re.escape(verb)}(?![A-Za-z0-9_-])", combined) is None:
            print(f"f-real-invocation-reaches-libexec: FAIL -- 'autoharn {verb} --help' output "
                  f"never names {verb!r} anywhere -- looks like a WRONG-TARGET dispatch (another "
                  f"verb's implementation served under this verb's filename). "
                  f"combined output: {combined!r}")
            ok = False
    if ok:
        print("f-real-invocation-reaches-libexec: PASS (every verb's real libexec/autoharn/<verb> "
              "reached via `./autoharn <verb> --help`, never a broken-exec shell diagnostic, and "
              "each verb's own name appears in its own --help output -- no wrong-target dispatch)")
    return ok


def case_g_help_sweep_never_writes() -> bool:
    """Round-2 review AXIS 1 moderate fix: `./autoharn`'s own comment claimed the top-level
    --help/service --help "never writes" claim is witnessed by case f -- it never was. This
    directly witnesses it: a `git status --porcelain` snapshot of the whole repo, taken
    immediately before and immediately after sweeping `autoharn --help`, `autoharn service
    --help`, and `autoharn <verb> --help` for every verb in the parsed dispatch table, must be
    byte-identical."""
    before = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True,
                             cwd=str(REPO_ROOT)).stdout
    help_out = _run([str(AUTOHARN), "--help"]).stdout
    _run([str(AUTOHARN), "service", "--help"])
    for verb in sorted(_parsed_table_verbs(help_out) - {"service"}):
        _run([str(AUTOHARN), verb, "--help"])
    after = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True,
                            cwd=str(REPO_ROOT)).stdout
    if before != after:
        print(f"g-help-sweep-never-writes: FAIL -- repo's own git status changed across the "
              f"--help sweep.\nBEFORE:\n{before!r}\nAFTER:\n{after!r}")
        return False
    print("g-help-sweep-never-writes: PASS (git status --porcelain byte-identical before/after "
          "the full top-level + service + per-verb --help sweep -- zero filesystem trace)")
    return True


def main() -> int:
    results = [
        case_a_libexec_roster_matches_dispatch_table(),
        case_b_help_mentions_every_verb(),
        case_c_alias_shim_still_works(),
        case_d_unknown_verb_refuses(),
        case_e_service_is_handled_directly(),
        case_f_real_invocation_reaches_libexec(),
        case_g_help_sweep_never_writes(),
    ]
    if all(results):
        print("\nALL CASES PASS")
        return 0
    print("\nAT LEAST ONE CASE FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
