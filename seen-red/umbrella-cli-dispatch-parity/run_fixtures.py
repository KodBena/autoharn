#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for design/FABLE-AUTOHARN-UMBRELLA-CLI-SPEC.md §1/§7:
the generated `autoharn --help` roster cannot drift from what actually runs, every relocated verb
is reachable via `./autoharn <verb>` and dispatches to the real `libexec/autoharn/<verb>` file
(not a wrong-target swap), and an unrecognized verb refuses loudly teaching the same roster.

(Dated note, 2026-07-26, work item courier-umbrella-rebase, ledger rows 1369/1370 -- ADR-0005
Rule 8, corrected in place rather than appended since this is the file's own live summary, not a
frozen spec: this sentence used to also claim "and via their deprecated `./<verb>` alias shims" --
those ten aliases were deleted outright by root-shim-pruning, ledger row 1357, and this file's own
case c, which drove them, is REMOVED below rather than left describing a surface that no longer
exists. The roster is now eleven verbs (courier added this item, wired the same way as the other
ten but with NO alias -- the alias pattern itself is retired, not merely descoped).)

Cases:
  a-libexec-roster-matches-dispatch-table -- every file under libexec/autoharn/ has an entry in
                                 `autoharn`'s own dispatch table, and vice versa (RED if either
                                 side has an entry the other lacks).
  b-help-mentions-every-verb -- `autoharn --help`'s stdout names every libexec/autoharn/ verb
                                 (mechanical grep, not hand-maintained).
  c-alias-shim-still-works -- REMOVED 2026-07-26 (work item courier-umbrella-rebase, ledger rows
                                 1369/1370; ADR-0005 Rule 8, dated note rather than a silent
                                 rewrite of this docstring's history above -- the case's own
                                 description above is kept verbatim). root-shim-pruning (ledger
                                 row 1357) deleted the ten `./<verb>` deprecation alias shims this
                                 case drove -- the alias-shim pattern is RETIRED, not merely this
                                 build's out-of-scope follow-on -- but that deletion never touched
                                 this fixture, leaving case c calling a nonexistent path
                                 (`REPO_ROOT / verb`) for every verb and crashing with an
                                 uncaught `FileNotFoundError` before any later case could even
                                 run: a hazard found in reach of THIS build's own required touch
                                 to this exact file (extending it to cover courier per the work
                                 item's own instructions), fixed here per CLAUDE.md's
                                 hazard-flagging duty rather than routed around. There is nothing
                                 left for this case to drive -- no alias survives for any verb,
                                 and the umbrella build's own policy (row 1357) is that no future
                                 verb gets one either (courier, wired into this same dispatch
                                 table by this same work item, gets NO root alias, per that
                                 policy) -- so the case is deleted outright, not stubbed to a
                                 vacuous pass; the remaining cases (a/b/d/e/f/g, function names
                                 kept as-is rather than renumbered) already independently prove
                                 dispatch integrity without ever touching the retired alias
                                 surface.
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
                                 free for all ten verbs -- all ten now print real, self-
                                 identifying usage text and exit 0 (round-3 review note below:
                                 this was NOT yet true for four of them at the time this sentence
                                 was first written; the STALE claim that their construction-time
                                 deployment/PGHOST refusal was "still proof the REAL script ran"
                                 is corrected there, not repeated here). ALSO (round-2 review
                                 AXIS 1 disqualifying fix): a
                                 wrong-target dispatch -- a verb FILE whose content is a DIFFERENT
                                 verb's implementation, filename right, content wrong, the exact
                                 risk of a ten-file relocation -- would still satisfy every check
                                 above (exit 0, real-looking usage text, no shell exec-failure
                                 signature). So this case additionally asserts VERB IDENTITY.
                                 `audit` was the one verb that FAILED this when first checked
                                 (its --help fell all the way through to engine/contemp_audit.py's
                                 eager, import-time PGHOST resolution before argparse ever saw
                                 argv, producing the SAME generic "REFUSED: no Postgres host
                                 resolved" text every OTHER PGHOST-needing verb produces, no
                                 "audit" substring anywhere) -- fixed per the reviewer's own
                                 instruction (a marker added to the TEMPLATE, not a weakened
                                 assertion): bootstrap/templates/audit.tmpl intercepts --help/-h
                                 itself, before any Python/DB code runs, and prints a real,
                                 self-identifying usage line.

                                 ROUND-3 REVIEW (SEVERE, two escapes -- both reproduced red, then
                                 fixed, this round): the round-2 identity check (a bare "verb name
                                 appears as a whole token anywhere in combined output" test) was
                                 ITSELF still an escape for the OTHER four PGHOST/deployment-
                                 resolving verbs. judge, distance-to-clean, doctor, and
                                 verify-chain (unlike audit) had NO --help interception at all:
                                 each fell through, unconditionally, to
                                 filing/deployment_record.py's own missing-file refusal, whose
                                 text literally reads "...the LEDGER_DEPLOYMENT or
                                 PICKUP_DEPLOYMENT environment variable (used by pickup, judge,
                                 and led alike)". So a wrong-target dispatch swapping ANY TWO of
                                 those four verbs (reproduced red: libexec/autoharn/judge
                                 rewritten to `exec ... verify-chain.tmpl "$@"`) still printed
                                 output containing the literal substring "judge" -- via that
                                 SHARED boilerplate, not via anything specific to the real verb --
                                 so the whole-token check passed even though the WRONG verb's
                                 implementation was running underneath. FIXED (this round):
                                 bootstrap/templates/judge.tmpl, doctor.tmpl,
                                 distance-to-clean.tmpl (+ its legacy- sibling, actually reached
                                 by THIS repo's own dispatch), and verify-chain.tmpl now all
                                 intercept --help/-h before any deployment/config resolution,
                                 exactly like audit.tmpl already did (discharges the standing
                                 row-1159 residual for these four -- see each template's own
                                 comment). The identity check itself is ALSO tightened: rather
                                 than a bare verb-name token, `_USAGE_MARKERS` (module level,
                                 shared with case c) holds each verb's own self-identifying
                                 usage/header LINE, and `_assert_no_shared_boilerplate` positively
                                 asserts the shared deployment/PGHOST refusal text is ABSENT --
                                 the shared-boilerplate collision is now structurally impossible,
                                 not merely unlikely.
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

import subprocess
import sys
from pathlib import Path

import os
# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own
# environment before any subprocess is spawned -- inherited by the whole process tree
# this fixture starts, so every repo-root verb invocation anywhere downstream carries it.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

# Every real invocation of AUTOHARN in this fixture is either --help/-h/"service"/an
# unrecognized-verb probe (statically safe, see gates/fixture_deployment_pin_guard.py's own
# `dispatcher_invocation_is_safe` -- the dispatcher's own source returns/execs into an
# env-parameterized script before ever touching a deployment path in every one of those cases,
# so those call sites need no waiver at all) or, in case_f_real_invocation_reaches_libexec /
# case_g_help_sweep_never_writes, `[str(AUTOHARN), verb, "--help"]` where `verb` is a LOOP
# VARIABLE this gate's static census cannot read the value of -- those TWO call sites carry
# their own waiver comment, at the call, not here (round-2 review fix, finding 1: a waiver on
# THIS binding line used to blanket every use of AUTOHARN below, including any future unreviewed
# one; gates/fixture_deployment_pin_guard.py review, 2026-07-26).
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AUTOHARN = REPO_ROOT / "autoharn"
LIBEXEC = REPO_ROOT / "libexec" / "autoharn"

# The ten relocated verbs -- named here, once, as this fixture's OWN expectation (not derived
# from the dispatch table itself, or a defect in the table could never be caught: this is the
# independent census the parity check below compares the table against).
_EXPECTED_VERBS = {
    "led", "judge", "pickup", "distance-to-clean", "attest-tags", "audit", "doctor",
    "migrate", "asof-export", "verify-chain",
    # courier -- added 2026-07-26 by work item courier-umbrella-rebase (ledger rows 1369/1370):
    # rebased from an unregistered root file into libexec/autoharn/courier, wired into
    # ./autoharn's dispatch table, same as the ten verbs above. Unlike those ten, courier gets
    # NO `./<verb>` alias (the deprecation-shim pattern is retired, row 1357) -- it was never
    # covered by the now-removed case c and needs no exemption there.
    "courier",
}

# Round-3 review fix: per-verb identity MARKERS, one literal substring per verb, each verified
# by hand (this round) against that verb's OWN real --help output (see the module docstring's
# round-3 addendum). This replaces the old bare "verb name appears as a whole token anywhere in
# combined output" check, which the round-3 reviewer broke on both polarities: (1) all four of
# judge/distance-to-clean/doctor/verify-chain used to fall through, --help-unhandled, to
# filing/deployment_record.py's own shared missing-file refusal text, which literally contains
# the substring "pickup, judge, and led alike" -- so EVERY ONE of those four verbs' "--help"
# output satisfied a same-verb identity check trivially, even under a wrong-target dispatch that
# swapped one of the four for another (the swapped-in verb's OWN refusal text still names the
# original verb via that shared boilerplate); (2) a bare substring/whole-token match on the verb
# name is satisfiable by ANY of the four verbs' real usage prose mentioning another verb by name
# in passing (e.g. distance-to-clean's own usage text says "same views `led review-gap` ...
# already expose"), so "led" would falsely register as present in distance-to-clean's own
# output. Each marker below is the verb's own self-identifying usage/header LINE (or a
# distinctive fragment of it), chosen so it cannot appear in any OTHER verb's real output or in
# the shared deployment/PGHOST refusal boilerplate -- verified per verb, by hand, this round.
# `pickup`'s marker deliberately does NOT use "usage: pickup" -- its underlying argparse `prog`
# is still the pre-relocation filename `legacy-pickup.tmpl` (a separate, smaller naming quirk
# out of this round's scope), so its own docstring header line is used instead.
_USAGE_MARKERS = {
    "led": "led -- read from and write to this project's decision ledger.",
    "judge": "usage: judge [--drop-record] [extra ledger_differential.py flags...]",
    "pickup": "pickup — the resume verb (",
    # Round-4 review SEVERE fix: pinned to the LEGACY variant's own distinguishing suffix (see
    # _SIBLING_SERVED_MARKERS below) -- legacy-distance-to-clean.tmpl is the file
    # libexec/autoharn/distance-to-clean actually execs for this repo's own root.
    "distance-to-clean": "usage: distance-to-clean  (LEGACY direct-psql original)",
    "attest-tags": "usage: attest-tags [--repo PATH] [--keys-dir PATH] [--json]",
    "audit": "usage: audit [--retain] [--differential]",
    "doctor": "usage: doctor",
    "migrate": "usage: migrate <deployment-dir> [--dry-run]",
    "asof-export": "usage: asof-export [-h] {read,export} ...",
    "verify-chain": "usage: verify-chain [--head]",
    # courier -- verified by hand (2026-07-26) against its real --help output; argparse's own
    # generated usage line, distinctive (no other verb is named "courier").
    "courier": "usage: courier [-h] [--courier-toml COURIER_TOML]",
}

# Round-4 review SEVERE fix. THE SIBLING-PAIR CLASS: several relocated verbs have TWO templates
# under bootstrap/templates/ -- a "served via the boundary" variant and a "legacy-<verb>.tmpl"
# direct-psql original (design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md §5) -- of which
# this repo's own libexec/autoharn/<verb> dispatch contractually execs the LEGACY one (existing-
# world policy, runs-are-linear, see each dispatch script's own header comment). A sibling pair
# whose own usage/header text happens to be byte-identical between the two variants is an escape
# THE SAME SHAPE AS THE ROUND-3 SHARED-BOILERPLATE ESCAPE ABOVE: `_USAGE_MARKERS`' presence check
# alone would pass even if libexec/autoharn/<verb> were swapped to exec the WRONG (served) sibling
# -- the marker constant is fully satisfiable by BOTH files at once, so the check proves nothing
# about WHICH one actually ran. Reproduced red for distance-to-clean this round (the served and
# legacy templates both printed the bare "usage: distance-to-clean"); a sweep of every OTHER verb
# with a served/legacy split found the SAME shape in asof-export (both templates' argparse
# `prog="asof-export"` usage line is mechanically identical: "usage: asof-export [-h]
# {read,export} ..."). Checked and found ALREADY SAFE: pickup (bootstrap/templates/pickup.tmpl
# vs legacy-pickup.tmpl) -- legacy-pickup.tmpl's own docstring header uses an em dash ("—",
# absent everywhere in the served pickup.tmpl, verified `grep -c` = 0) so its existing
# `_USAGE_MARKERS["pickup"]` entry already cannot double as the served variant's marker; no
# template edit or extra check needed there. led has no legacy sibling at all (legacy-led.tmpl is
# deleted outright, per libexec/autoharn/led's own comment) -- not a pair.
#
# For each verb below, this is the SERVED sibling's own distinguishing text (verified, by hand,
# this round, to be absent from that verb's real LEGACY --help output) -- `_assert_sibling_pair`
# asserts it is ABSENT from combined output alongside the (legacy) `_USAGE_MARKERS` entry's
# presence, so a wrong-target dispatch swapping in the served sibling is caught even though the
# swapped-in file's own usage/header text would otherwise satisfy `_USAGE_MARKERS` alone.
# A FUTURE VERB THAT GROWS A SERVED/LEGACY SPLIT SHOULD GET THE SAME TREATMENT: add its served
# variant's distinguishing text here, or confirm (and note, as done above for pickup) that its
# existing marker already cannot collide.
_SIBLING_SERVED_MARKERS = {
    "distance-to-clean": "usage: distance-to-clean  (served via the boundary)",
    "asof-export": "Served via the boundary",
}

# The shared boilerplate that caused the round-3 SEVERE escapes: filing/deployment_record.py's
# missing-file message (names "pickup, judge, and led" as PICKUP_DEPLOYMENT/LEDGER_DEPLOYMENT
# consumers) and filing/pghost_resolve.py's PGHOST-resolution refusal (the same shape that
# tripped audit.tmpl in round 2). A verb's --help output must never contain either -- structural
# proof the shared-boilerplate collision is no longer possible, not merely an assertion in prose.
_SHARED_REFUSAL_MARKERS = (
    "pickup, judge, and led alike",
    "REFUSED: no Postgres host resolved",
)


def _assert_no_shared_boilerplate(verb: str, combined: str) -> str | None:
    """Returns a FAIL message, or None if clean."""
    for marker in _SHARED_REFUSAL_MARKERS:
        if marker in combined:
            return (f"'{verb} --help' output contains the shared deployment/PGHOST refusal "
                     f"boilerplate ({marker!r}) -- this is the exact round-3 escape (a verb's "
                     f"--help falling through to a shared refusal that happens to name other "
                     f"verbs too); combined output: {combined!r}")
    return None


def _assert_sibling_pair_identity(verb: str, combined: str) -> str | None:
    """Round-4 review SEVERE fix. Returns a FAIL message, or None if clean. For a verb with a
    served/legacy sibling split (see `_SIBLING_SERVED_MARKERS`'s own comment above), asserts the
    SERVED sibling's own distinguishing text is ABSENT from real output -- the presence-only
    `_USAGE_MARKERS` check cannot, by itself, distinguish "the real legacy verb ran" from "the
    served sibling ran instead" when the two variants' usage/header text collides (the exact
    class of escape reproduced red this round for distance-to-clean, then found again by sweep in
    asof-export). Verbs with no sibling split, or an already-safe pair, are simply absent from
    `_SIBLING_SERVED_MARKERS` and this is a no-op for them."""
    served_marker = _SIBLING_SERVED_MARKERS.get(verb)
    if served_marker is None:
        return None
    if served_marker in combined:
        return (f"'{verb}' output contains its SERVED sibling template's own distinguishing text "
                f"({served_marker!r}) -- this repo's dispatch is contracted to exec the LEGACY "
                f"direct-psql variant for this verb, so this looks like a wrong-target dispatch "
                f"serving the OTHER sibling template underneath; combined output: {combined!r}")
    return None


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


# case_c_alias_shim_still_works REMOVED 2026-07-26 (work item courier-umbrella-rebase, ledger
# rows 1369/1370) -- see the module docstring's dated note at case c's own entry above for the
# reproduction (root-shim-pruning, row 1357, deleted the ten alias shims this case drove but
# never touched this file, leaving it crashing with an uncaught FileNotFoundError) and the
# reasoning for deletion rather than a stub (the alias pattern is retired, not merely
# out-of-scope; courier gets no alias either, per that same retirement).


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
    # `verb` ranges only over the parsed dispatch table, always paired with a literal trailing
    # "--help" (never a real write) -- proven non-mutating by case_g_help_sweep_never_writes's
    # own git-status-byte-identical witness. A future edit pairing AUTOHARN with a variable verb
    # WITHOUT a trailing --help needs its own fresh review (gates/fixture_deployment_pin_guard.py
    # review, 2026-07-26).
    for verb in verbs:
        r = _run(  # fixture-scratch-pinning-guard-waiver: see comment above this loop
            [str(AUTOHARN), verb, "--help"])
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
        # ROUND-2 REVIEW AXIS 1 DISQUALIFYING FIX (tightened round 3, see below): a wrong-target
        # dispatch (a verb FILE whose CONTENT is a DIFFERENT verb's implementation -- filename
        # right, implementation wrong, exactly the risk of a ten-file relocation) would satisfy
        # every check above: exit 0 (or whatever exit the OTHER verb's --help produces),
        # plausible-looking usage/refusal text, no shell exec-failure signature. Round 2 caught
        # this by asserting the verb's own name appears as a whole token anywhere in combined
        # output. ROUND 3 REVIEW: that whole-token check was ITSELF still an escape -- with all
        # four of judge/distance-to-clean/doctor/verify-chain falling through, --help-unhandled,
        # to filing/deployment_record.py's shared missing-file refusal (which literally reads
        # "...used by pickup, judge, and led alike"), a wrong-target dispatch swapping any TWO of
        # those four verbs still produced a whole-token match on the ORIGINAL verb's name (via
        # that shared boilerplate, not via any content specific to the real verb) -- reproduced
        # red, and fixed, THIS round (module docstring's round-3 addendum): `bootstrap/templates/
        # judge.tmpl`, `doctor.tmpl`, `distance-to-clean.tmpl` (+ its `legacy-` sibling actually
        # reached by this repo's own dispatch), and `verify-chain.tmpl` now all intercept
        # --help/-h before any deployment/config resolution, exactly like `audit.tmpl` already
        # did. The identity check below is now the per-verb `_USAGE_MARKERS` marker (module-
        # level, shared with case c) -- each verb's own self-identifying usage/header LINE, not
        # merely its bare name -- PLUS an explicit assertion that the shared deployment/PGHOST
        # refusal boilerplate is ABSENT, so the shared-boilerplate collision is now structurally
        # impossible rather than merely unlikely.
        marker = _USAGE_MARKERS.get(verb)
        if marker is None:
            print(f"f-real-invocation-reaches-libexec: FAIL -- no _USAGE_MARKERS entry for "
                  f"{verb!r} (the dispatch table grew a verb this fixture doesn't know how to "
                  f"identify -- add one)")
            ok = False
            continue
        if marker not in combined:
            print(f"f-real-invocation-reaches-libexec: FAIL -- 'autoharn {verb} --help' output "
                  f"never shows {verb}'s own usage marker ({marker!r}) -- looks like a "
                  f"WRONG-TARGET dispatch (another verb's implementation served under this "
                  f"verb's filename). combined output: {combined!r}")
            ok = False
            continue
        boilerplate_fail = _assert_no_shared_boilerplate(verb, combined)
        if boilerplate_fail:
            print(f"f-real-invocation-reaches-libexec: FAIL -- {boilerplate_fail}")
            ok = False
        sibling_fail = _assert_sibling_pair_identity(verb, combined)
        if sibling_fail:
            print(f"f-real-invocation-reaches-libexec: FAIL -- {sibling_fail}")
            ok = False
    if ok:
        print("f-real-invocation-reaches-libexec: PASS (every verb's real libexec/autoharn/<verb> "
              "reached via `./autoharn <verb> --help`, never a broken-exec shell diagnostic, "
              "each verb's own self-identifying usage marker is present, and none of them fall "
              "through to the shared deployment/PGHOST refusal boilerplate -- no wrong-target "
              "dispatch, no shared-boilerplate collision)")
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
    # Same scoped invariant as case f's own loop (verb ranges over the parsed dispatch table,
    # always paired with a literal --help) -- proven non-mutating by THIS case's own before/after
    # git-status comparison below.
    for verb in sorted(_parsed_table_verbs(help_out) - {"service"}):
        _run(  # fixture-scratch-pinning-guard-waiver: see comment above this loop
            [str(AUTOHARN), verb, "--help"])
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
        # case c (alias shim) REMOVED 2026-07-26 -- see module docstring's dated note.
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
