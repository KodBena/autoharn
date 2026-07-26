#!/usr/bin/env python3
"""Seen-red specimen for night-build-defect-repair DEFECT 2 (bootstrap/templates/led.tmpl's
--evidence path-dereference guard, item artifact-claim-dereference-guard).

RCA (fresh-context verifier, this session's parent decision row): the guard shipped in b77ee7a
only inspected --evidence, never $statement, so the literal ledger rows 896-897 specimen (a path
embedded in STATEMENT PROSE, not passed via --evidence at all) still escapes; and it accepted a
directory because `test -e` is true for a directory too, even though row 898's own remediation is
explicitly "ls/wc of a FILE". b77ee7a shipped as one-off live writes with no re-runnable suite --
that absence is itself named as part of the gap this fixture closes.

SCRATCH REWIRE (fixture-repairs review, 2026-07-23 -- see this dir's red.txt for the dated note):
this fixture used to drive the REPO-ROOT `./led` (ROOT/parents[2]) against THIS CHECKOUT'S OWN
deployment.json -- whatever real deployment that checkout happened to be pointed at. That is
exactly the register a live incident later confirmed as a hazard: during the fixture-repairs
batch (a74978e0), this fixture's own probe writes landed 8 garbage rows in the REAL kernel (ledger
rows 1237-1244, marked garbage by finding row 1248) because the checkout's deployment.json
resolved to a live deployment, not a scratch one. This fixture now scaffolds its OWN scratch
world via `bootstrap/new-project.sh --new-world` (full birth chain through s43) and stands a real
`serving.boundary_service` against it via `serve_existing_world` (seen-red/boundary-service/
run_fixtures.py -- the ONE shared home, ADR-0012 P1, every migrated fixture in this class already
imports), exactly the pattern seen-red/led-help-token-closure/run_fixtures.py and its siblings
already use. Every `led` invocation below runs against THAT scratch project, never the repo's own
deployment.json.

GAP CLOSED (ledger row 1245, this repair pass): both the --evidence path-dereference guard and
the path-shaped-statement warning are REIMPLEMENTED in the served CLI
(bootstrap/templates/led.tmpl's `_evidence_dereference_violation`/`_warn_path_shaped_in_statement`
functions, wired into `cmd_generic` right after the existing garbage-statement/grammar pre-flight
checks, and `_warn_path_shaped_in_statement` additionally wired into `cmd_review`). This is a
CLI-SIDE re-implementation, deliberately at the SAME layer the existing garbage-statement guard
(ledger row 1159) and the eight ported statement grammars already live at (cmd_generic's own
pre-flight, before any payload is ever built) -- the check dereferences THIS OPERATOR'S OWN
filesystem, which only the CLI process (running on the operator's own checkout) can see; the
boundary service may run on a different host entirely, so a boundary-side dereference would
inspect the WRONG filesystem for a local `--evidence <path>` claim.

Every case below was RED against the served CLI before this repair (see this file's own git
history for the dated live-witness of the gap) and is GREEN now that the guard/warning are back --
the REDISCOVERED-GAP-* case names are KEPT (not renamed) so this file's own history stays
legible: they now assert the GUARD HOLDS, the mirror image of what they asserted while the gap
was open.

CASES, live-witnessed against scratch (no case is silently green-by-vacuity -- every assertion
below states which fact it is checking and why):

REDISCOVERED-GAP, NOW CLOSED (must refuse, no row written -- and it does):
  - REDISCOVERED-GAP-DEAD-EVIDENCE-PATH: a dead --evidence path is REFUSED, no row written,
    teach-text cites the 896-899 specimen class -- the artifact-claim-without-dereference guard
    fires.
  - REDISCOVERED-GAP-BARE-DIRECTORY-EVIDENCE: a bare (no trailing slash) EXISTING directory
    passed as --evidence is REFUSED, no row written -- the directory-vs-file distinction this
    item's own night-build-defect-repair follow-on originally closed is back.

STILL GREEN (unaffected either way -- these never depended on the guard's refusal-side behavior):
  - a live --evidence FILE: MUST ACCEPT, real row lands, round-trip verified.
  - an --evidence directory explicitly cited via a trailing "/": MUST ACCEPT (same reasoning).

REDISCOVERED-GAP, NOW CLOSED (used to WARN-but-write; the warning is back):
  - REDISCOVERED-GAP-STATEMENT-PATH-NO-WARNING: a statement containing a dead path-shaped token
    still writes (unaffected -- WARN-only, never a refusal), and a WARNING is printed --
    `_warn_path_shaped_in_statement` fires.
  - REDISCOVERED-GAP-STATEMENT-MULTI-PATH-NO-WARNING: three dead path-shaped tokens in one
    statement still write, with exactly ONE preamble + a three-item list (AUTOHARN_BACKFLOW
    finding 5's own collapse-the-spam fix, preserved by the reimplementation), not once per token.

GREEN, RIGHT REASON NOW VERIFIED (the caveat this file used to carry while the gap was open):
  - a statement containing a row:<id> citation: no warning fires -- now verified for the RIGHT
    reason (the scanner exists and correctly excludes row: citations from its scope), not merely
    because nothing scans at all.
  - a statement containing a URL: same, now verified for the right reason (the scanner exists and
    correctly excludes URLs).

THIRD GUARD-TRIO MEMBER ADDED (strengthened-tier fresh-context review of THIS arc's own guard-trio
commit, MODERATE/SILENT finding, 2026-07-25): legacy-led.tmpl's `review` case called
`warn_content_free_review_statement` immediately alongside `warn_path_shaped_in_statement` (git
show 93affa0^, the `review` case body -- both calls back to back right after `statement="$*"`),
but only the path-shape scanner was ported into `cmd_review` when this arc's repair landed --
the content-free sibling guard was silently left behind, so a content-free `led review` statement
(run12 ledger row 20's own specimen, `"test"`, 4 chars) discharging a countersign obligation got
no CLI-side catch at all outside `engine/review_gap_audit.py`'s own retroactive, discharge-scoped
check. Ported here too, `_warn_content_free_review_statement`, wired into `cmd_review` alongside
the path-shape scanner (legacy's own call order preserved: content-free check first). New cases,
same real-served-CLI pattern as every case above:
  - RED-FIRST-CONTENT-FREE-REVIEW-STATEMENT: `led review` on a content-free statement (run12's
    own 4-char specimen) still writes (WARN-only, never a refusal), and a WARNING naming
    engine/review_gap_audit.py / tracker item `content-free-review-audit` is printed. Captured RED
    against the pre-repair led.tmpl (this repair's own parent commit, guard absent -> silent),
    GREEN after (guard ported -> warns) -- see this dir's red.txt for the dated dual capture.
  - GREEN-GENUINE-REVIEW-STATEMENT-NO-WARNING: a review statement of ordinary length gets NO
    content-free warning -- verified for the right reason (the guard exists and correctly passes
    a genuine statement), not merely because nothing checks at all.

Usage: python3 seen-red/artifact-claim-dereference-guard/run_fixtures.py
Exit 0 if every case matches expected (guard-holds) behavior; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"

sys.path.insert(0, str(REPO / "seen-red"))  # for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own
# environment before any subprocess is spawned -- inherited by the whole process tree
# this fixture starts, so every repo-root verb invocation anywhere downstream carries it.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

# REUSE (ADR-0012 P1): serve_existing_world from seen-red/boundary-service/run_fixtures.py -- the
# ONE shared home every migrated fixture in this class imports via this same importlib pattern
# (see that function's own docstring, and its own leak-class refusal added by this same review:
# it refuses any deployment_path not living under tempfile.gettempdir()).
_BS_SPEC = importlib.util.spec_from_file_location(
    "boundary_service_fixtures", REPO / "seen-red" / "boundary-service" / "run_fixtures.py")
assert _BS_SPEC is not None and _BS_SPEC.loader is not None
bs_fixtures = importlib.util.module_from_spec(_BS_SPEC)
sys.modules["boundary_service_fixtures"] = bs_fixtures
_BS_SPEC.loader.exec_module(bs_fixtures)

PGHOST, PGDB = fixture_pghost(), "toy"
SCRATCH_NAME = "acdgfixture"
SCHEMA, KERN, ROLE = SCRATCH_NAME, f"{SCRATCH_NAME}_kernel", f"{SCRATCH_NAME}_rw"
TAG = f"seen-red-artifact-claim-dereference-guard-{int(time.time())}"

FAILURES: list[str] = []


def _check(label: str, cond: bool) -> None:
    print(f"  [{'ok' if cond else 'FAIL'}] {label}")
    if not cond:
        FAILURES.append(label)


def _psql(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["psql", "-h", PGHOST, "-d", PGDB, *args],
                           capture_output=True, text=True)


def _drop_scratch() -> None:
    _psql("-v", "ON_ERROR_STOP=0", "-q",
          "-c", f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE;",
          "-c", f"DROP SCHEMA IF EXISTS {KERN} CASCADE;",
          "-c", f"DROP ROLE IF EXISTS {ROLE};")


def _run_led(dest: Path, *args: str, env: dict | None = None) -> tuple[int, str, str]:
    full_env = None
    if env:
        full_env = os.environ.copy()
        full_env.update(env)
    # §6 amendment (2026-07-26, rows 1357/1365/1366/1367): routed through the one dispatcher now.
    cp = subprocess.run([str(dest / "autoharn"), "led", *args], cwd=str(dest),
                         capture_output=True, text=True, env=full_env)
    return cp.returncode, cp.stdout, cp.stderr


def _current_max_id(dest: Path) -> int:
    # cli-rebase-fixture-repairs (ledger row 1170): `led --recent`'s own output shape changed
    # from a pipe-delimited row to "[<id>] <kind>: <statement>" during the CLI rebase -- parsed
    # with a leading-bracket regex now instead of a stale pipe-split.
    rc, out, _ = _run_led(dest, "--recent", "1")
    if rc != 0 or not out.strip():
        return -1
    m = re.match(r"^\[(\d+)\]", out.strip().splitlines()[0])
    if not m:
        raise RuntimeError(f"could not parse a row id from `led --recent 1` output: {out!r}")
    return int(m.group(1))


def gap_dead_evidence_path_accepted() -> None:
    print("# REDISCOVERED-GAP-DEAD-EVIDENCE-PATH, NOW CLOSED -- a dead --evidence path must "
          "REFUSE (row 1245's repair: the guard is back).")
    before = _current_max_id(DEST)
    rc, out, err = _run_led(DEST, "--evidence", "/tmp/does-not-exist-nbdr-fixture-xyz",
                             "decision", f"{TAG}: dead evidence path probe")
    after = _current_max_id(DEST)
    _check("guard REFUSES (nonzero exit)", rc != 0)
    _check("no row was written (max id unchanged)", after == before)
    _check("teach-text cites the 896-899 specimen class", "896-899" in err)


def gap_bare_directory_evidence_accepted() -> None:
    print("# REDISCOVERED-GAP-BARE-DIRECTORY-EVIDENCE, NOW CLOSED -- a bare (no trailing "
          "slash) EXISTING directory must REFUSE (row 1245's repair: the directory-vs-file "
          "distinction is back).")
    before = _current_max_id(DEST)
    # REAL BUG, FOUND AND FIXED IN THIS SAME REPAIR PASS: the scratch-rewire commit (edd0cb1)
    # truncated this probe's value from the ORIGINAL fixture's own "bootstrap/templates" (git
    # show 6361c82) down to a bare "bootstrap" -- losing the "/" that makes a value PATH-SHAPED
    # at all (`_is_path_shaped`'s own rule, ported byte-faithfully off legacy's `/*|./*|*/*` case
    # pattern: a value with NO "/" anywhere, and not starting with "/" or "./", is never
    # path-shaped, so the guard never even LOOKS at it -- silently vacuous, not merely wrong).
    # Worse, the scratch project scaffold (bootstrap/new-project.sh --new-world) carries no
    # "bootstrap/" tree of its own at all, so even the untruncated value would not have existed
    # in THIS DEST regardless. ".claude/logs" is a real, EXISTING directory every scaffolded
    # project carries (bootstrap/new-project.sh's own apparatus.json/logs scaffold), and it
    # genuinely contains a "/" -- the value this case actually needs to exercise the check.
    rc, out, err = _run_led(DEST, "--evidence", ".claude/logs",
                             "decision", f"{TAG}: bare directory evidence probe")
    after = _current_max_id(DEST)
    _check("guard REFUSES the bare directory (nonzero exit)", rc != 0)
    _check("no row was written (max id unchanged)", after == before)
    _check("teach-text names it a DIRECTORY, not a file", "DIRECTORY" in err)


def green_live_file_evidence() -> None:
    print("# GREEN — a live --evidence FILE: MUST ACCEPT, real row lands, round-trip verified "
          "(unaffected either way -- a real file was always meant to be accepted)")
    rc, out, err = _run_led(DEST, "--evidence", "led",
                             "decision", f"{TAG}: live file evidence probe")
    _check("guard ACCEPTS (exit 0)", rc == 0)
    new_id = _current_max_id(DEST)
    rc2, out2, _ = _run_led(DEST, "show", str(new_id))
    _check("real led round-trip: led show <id> reads the row back", rc2 == 0 and TAG in out2)


def green_explicit_directory_evidence() -> None:
    print("# GREEN — --evidence directory cited via trailing slash: MUST ACCEPT "
          "(unaffected either way)")
    rc, out, err = _run_led(DEST, "--evidence", "legacy/",
                             "decision", f"{TAG}: explicit trailing-slash directory probe")
    _check("guard ACCEPTS the explicitly-cited directory (exit 0)", rc == 0)
    new_id = _current_max_id(DEST)
    rc2, out2, _ = _run_led(DEST, "show", str(new_id))
    _check("round-trip verified", rc2 == 0 and TAG in out2)


def gap_statement_path_no_warning() -> None:
    print("# REDISCOVERED-GAP-STATEMENT-PATH-NO-WARNING, NOW CLOSED -- a dead path-shaped "
          "token in STATEMENT prose must WARN-but-write (row 1245's repair: the scanner is "
          "back).")
    rc, out, err = _run_led(DEST, "decision",
                             f"{TAG}: about to write /tmp/does-not-exist-nbdr-statement-probe next")
    _check("write still succeeds (exit 0, WARN-only, never a refusal)", rc == 0)
    _check("a WARNING IS printed (the scanner fires)", "WARNING" in err)
    _check("the flagged token itself is echoed in the warning",
           "/tmp/does-not-exist-nbdr-statement-probe" in err)


def gap_statement_multiple_path_tokens_no_warning() -> None:
    print("# REDISCOVERED-GAP-STATEMENT-MULTI-PATH-NO-WARNING, NOW CLOSED -- THREE dead "
          "path-shaped tokens in one STATEMENT must fire ONE preamble + a list (AUTOHARN_"
          "BACKFLOW finding 5's own fix, preserved by the reimplementation), not once per "
          "token.")
    tok_a = "/tmp/does-not-exist-nbdr-multi-a"
    tok_b = "/tmp/does-not-exist-nbdr-multi-b"
    tok_c = "./tmp/does-not-exist-nbdr-multi-c"
    rc, out, err = _run_led(
        DEST, "decision",
        f"{TAG}: about to write {tok_a} and {tok_b} then {tok_c} across three separate files",
    )
    _check("write still succeeds (exit 0, WARN-only, never a refusal)", rc == 0)
    _check("exactly ONE preamble line fires (finding 5's own collapse-the-spam fix holds)",
           err.count("led: WARNING -- the statement contains") == 1)
    _check("all three tokens are echoed in the ONE warning's list",
           tok_a in err and tok_b in err and tok_c in err)


def green_row_citation_untouched() -> None:
    print("# GREEN, RIGHT REASON NOW VERIFIED — row:<id> citation in statement: no warning "
          "fires, and now for the RIGHT reason (the scanner exists and correctly excludes "
          "row: citations from its scope), not merely because nothing scans at all.")
    rc, out, err = _run_led(DEST, "decision", f"{TAG}: row:1 citation untouched probe")
    _check("write succeeds (exit 0)", rc == 0)
    _check("no path-shape WARNING fires for a row: citation", "WARNING" not in err)


def green_url_untouched() -> None:
    print("# GREEN, RIGHT REASON NOW VERIFIED — URL in statement: no warning fires, now "
          "verified for the right reason (the scanner exists and correctly excludes URLs).")
    rc, out, err = _run_led(DEST, "decision", f"{TAG}: https://example.com/nbdr-probe untouched")
    _check("write succeeds (exit 0)", rc == 0)
    _check("no path-shape WARNING fires for a URL", "WARNING" not in err)


def red_first_content_free_review_statement() -> None:
    print("# RED-FIRST-CONTENT-FREE-REVIEW-STATEMENT -- `led review` on a content-free "
          "statement (run12 ledger row 20's own 4-char specimen, verbatim) still writes "
          "(WARN-only, never a refusal), and now prints a WARNING naming the "
          "content-free-review-audit tracker item (strengthened-tier review finding, this arc: "
          "the guard was byte-faithfully ported off legacy-led.tmpl's own "
          "warn_content_free_review_statement, but silently left un-wired from cmd_review when "
          "the sibling path-shape scanner was reinstated).")
    rc0, out0, err0 = _run_led(DEST, "decision", f"{TAG}: content-free-review target row")
    assert rc0 == 0, f"could not seed a target row: {out0!r} {err0!r}"
    target_id = _current_max_id(DEST)
    rc1, out1, err1 = _run_led(DEST, "register-principal", "acdg-reviewer", "model",
                                "--purpose", "artifact-claim-dereference-guard fixture "
                                "content-free-review case")
    assert rc1 == 0, f"could not register reviewer principal: {out1!r} {err1!r}"
    rc, out, err = _run_led(DEST, "review", str(target_id), "attest", "self-review", "test",
                             env={"LED_ACTOR": "acdg-reviewer"})
    _check("write still succeeds (exit 0, WARN-only, never a refusal)", rc == 0)
    _check("a WARNING is printed (the content-free guard fires)", "WARNING" in err)
    _check("the warning names this tracker item",
           "content-free-review-audit" in err)
    _check("the warning points at the retroactive check (./audit --review-gap)",
           "review-gap" in err)
    _check("the warning states the normalized 4-char length of the specimen",
           "4" in err and "whitespace-normalized" in err)


def green_genuine_review_statement_no_warning() -> None:
    print("# GREEN, RIGHT REASON VERIFIED — a review statement of ordinary length gets NO "
          "content-free warning: verified for the right reason (the guard exists and correctly "
          "passes a genuine statement), not merely because nothing checks at all.")
    rc0, out0, err0 = _run_led(DEST, "decision", f"{TAG}: genuine-review target row")
    assert rc0 == 0, f"could not seed a target row: {out0!r} {err0!r}"
    target_id = _current_max_id(DEST)
    rc1, out1, err1 = _run_led(DEST, "register-principal", "acdg-reviewer-2", "model",
                                "--purpose", "artifact-claim-dereference-guard fixture "
                                "genuine-review case")
    assert rc1 == 0, f"could not register reviewer principal: {out1!r} {err1!r}"
    rc, out, err = _run_led(
        DEST, "review", str(target_id), "attest", "self-review",
        f"Confirmed: reviewed this decision's statement directly against the stated criteria "
        f"row {target_id}; matches exactly, no discrepancies found ({TAG}).",
        env={"LED_ACTOR": "acdg-reviewer-2"})
    _check("write succeeds (exit 0)", rc == 0)
    _check("no content-free WARNING fires for a genuine-length statement", "WARNING" not in err)


DEST: Path


def main() -> int:
    global DEST
    _drop_scratch()
    tmpdir = Path(tempfile.mkdtemp(prefix="artifact-claim-dereference-guard-fixture-"))
    DEST = tmpdir / "project"

    # ------------------------------------------------------------------------------- ADOPT
    r = subprocess.run([str(NEW_PROJECT), str(DEST), "--new-world", SCRATCH_NAME,
                        "--db", PGDB, "--host", PGHOST], capture_output=True, text=True, cwd=str(REPO))
    ok = r.returncode == 0 and (DEST / "deployment.json").exists()
    print(f"ADOPT: new-project.sh --new-world exit={r.returncode} deployment.json="
          f"{(DEST / 'deployment.json').exists()} -- {'PASS' if ok else 'FAIL'}")
    if not ok:
        print(f"\nADOPT FAILED, aborting -- scratch left standing:\n  tempdir: {tmpdir}\n"
              f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
        return 1

    # fixture-repairs review (MODERATE-silent finding): serve_existing_world itself can raise
    # (its health-check timeout path) -- it used to sit OUTSIDE this try/finally, so a raise
    # from it would orphan the scratch schema/role/tempdir with no cleanup at all (the
    # boundary_service subprocess in that case never started, or was already reaped by
    # serve_existing_world's own failure path, so only the scratch substrate was ever at risk
    # here). `proc` is seeded None before the try so the finally below can tell "never started"
    # apart from "started, needs reaping", and the call itself now lives inside the try so its
    # own raise still reaches the except/finally cleanup below.
    proc: subprocess.Popen | None = None
    crashed_with: BaseException | None = None
    try:
        proc = bs_fixtures.serve_existing_world(DEST / "deployment.json", tmpdir)
        gap_dead_evidence_path_accepted()
        gap_bare_directory_evidence_accepted()
        green_live_file_evidence()
        green_explicit_directory_evidence()
        gap_statement_path_no_warning()
        gap_statement_multiple_path_tokens_no_warning()
        green_row_citation_untouched()
        green_url_untouched()
        red_first_content_free_review_statement()
        green_genuine_review_statement_no_warning()
    except BaseException as exc:  # noqa: BLE001 -- last-resort net, see led-help-token-closure's
        # own identical fix for the reasoning: an uncaught exception here must not leak the
        # boundary_service subprocess or the scratch schema/kern/role.
        crashed_with = exc
        FAILURES.append(f"UNCAUGHT EXCEPTION mid-fixture: {exc!r}")
        print(f"\n!! UNCAUGHT EXCEPTION mid-fixture -- {exc!r} -- reaping server and dropping "
              f"scratch before re-raising")
    finally:
        if proc is not None:
            bs_fixtures.stop_server(proc)

    if crashed_with is not None:
        _drop_scratch()
        shutil.rmtree(tmpdir, ignore_errors=True)
        print("artifact-claim-dereference-guard fixture: crashed -- server reaped, scratch "
              "dropped")
        raise crashed_with

    if FAILURES:
        print(f"\nSPECIMEN RED — {len(FAILURES)} check(s) failed against the EXPECTED "
              f"(guard-holds) BEHAVIOR this fixture now requires: {FAILURES}\nscratch left "
              f"standing as evidence:\n  tempdir: {tmpdir}\n  schema: {SCHEMA}/{KERN}/role "
              f"{ROLE} (db {PGDB}@{PGHOST})")
        return 1

    _drop_scratch()
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\n# artifact-claim-dereference-guard: all cases match EXPECTED (guard-holds) "
          f"BEHAVIOR -- the --evidence dereference guard, the path-shaped-statement warning, "
          f"and the content-free-review-statement warning are ALL wired into the served CLI "
          f"(ledger row 1245 + this arc's own strengthened-tier-review follow-up), the "
          f"REDISCOVERED-GAP-*/RED-FIRST-* cases now asserting each guard holds rather than the "
          f"gap reproducing. Scratch torn down to zero residue. Tag: {TAG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
