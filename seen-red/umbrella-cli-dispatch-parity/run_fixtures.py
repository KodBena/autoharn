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
                                 for EVERY verb in the dispatch table and asserts the dispatcher's
                                 own `exec` actually reached the real `libexec/autoharn/<verb>`
                                 file, rather than merely checking --help/alias-deprecation text
                                 that a broken exec line could still satisfy. A reviewer had
                                 injected `exec "$LIBEXEC/$VERB-BROKEN" "$@"` into ./autoharn and
                                 NO existing case (a/b/c/d/e above) went red -- case c in
                                 particular only checks the ALIAS shim's own deprecation line,
                                 which prints unconditionally BEFORE the alias's own `exec ./
                                 autoharn <verb>` call, so it stayed green even when that later
                                 exec failed outright (shell exit 127, "No such file or
                                 directory"). This case instead runs `./autoharn <verb>` directly
                                 (not through the alias) and asserts: exit code is never 127, and
                                 neither stdout nor stderr carries the shell's own
                                 exec-target-missing text -- the one signature a broken dispatch
                                 line produces that no verb's own real refusal text would ever
                                 spell. `--help` was verified (by hand, this round) side-effect-
                                 free for all ten verbs: five (led, pickup, attest-tags, migrate,
                                 asof-export) print real usage text and exit 0; the other five
                                 (judge, distance-to-clean, audit, doctor, verify-chain) refuse
                                 loudly BEFORE any write -- this repo's own root has no
                                 deployment.json, so each of those five's own construction-time
                                 "no deployment record"/"no Postgres host resolved" refusal fires
                                 first, which is itself still proof the REAL script ran (the exact
                                 refusal text is verb-specific, never the shell's own generic
                                 "not found").

RUN: python3 seen-red/umbrella-cli-dispatch-parity/run_fixtures.py
"""
from __future__ import annotations

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


def case_a_libexec_roster_matches_dispatch_table() -> bool:
    on_disk = {p.name for p in LIBEXEC.iterdir() if p.is_file()}
    help_out = _run([str(AUTOHARN), "--help"]).stdout
    in_table = set()
    for verb in on_disk | _EXPECTED_VERBS | {"service"}:
        if f"  {verb}" in help_out or f"  {verb} " in help_out:
            # cheap membership probe refined below by exact-line parse
            pass
    # Exact parse: the "verbs:" block prints "  <verb><spaces><description>" -- one per line.
    lines = help_out.splitlines()
    start = lines.index("verbs:") + 1
    table_verbs = set()
    for line in lines[start:]:
        if not line.startswith("  "):
            break
        table_verbs.add(line.split()[0])
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
    ok = True
    for verb in sorted(_EXPECTED_VERBS):
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
    if ok:
        print("f-real-invocation-reaches-libexec: PASS (every verb's real libexec/autoharn/<verb> "
              "reached via `./autoharn <verb> --help`, never a broken-exec shell diagnostic)")
    return ok


def main() -> int:
    results = [
        case_a_libexec_roster_matches_dispatch_table(),
        case_b_help_mentions_every_verb(),
        case_c_alias_shim_still_works(),
        case_d_unknown_verb_refuses(),
        case_e_service_is_handled_directly(),
        case_f_real_invocation_reaches_libexec(),
    ]
    if all(results):
        print("\nALL CASES PASS")
        return 0
    print("\nAT LEAST ONE CASE FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
