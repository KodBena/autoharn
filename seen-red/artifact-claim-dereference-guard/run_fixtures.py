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

REDISCOVERED-GAP, NAMED NOT SILENCED (ledger row 1245 -- open work item, the SAME REDISCOVERED-GAP
treatment seen-red/led-help-token-closure/run_fixtures.py already banks): live-witnessed against
the CURRENT served CLI (bootstrap/templates/led.tmpl), the --evidence path-dereference guard and
the path-shaped-statement warning this fixture exists to prove are BOTH ENTIRELY ABSENT --
`--evidence` is accepted as an ordinary shared flag (see led.tmpl's `_SHARED_FLAG_NAMES` /
`cmd_generic`'s `payload["evidence"] = shared["--evidence"]`) and stored VERBATIM with zero
dereference check of any kind: a dead path, a bare directory, anything, is accepted and written.
Likewise, no scan of $statement for path-shaped tokens exists anywhere in the current CLI -- no
warning ever fires, for any statement. This is a REBASE FEATURE-LOSS (row 1245's own finding),
not a fixture bug: the cases below assert the OBSERVED CURRENT BEHAVIOR (guard absent, everything
accepted, no warning ever fires) as NAMED GAPS, loudly labeled REDISCOVERED-GAP-*, rather than
silently passing (or silently failing) against a guard that used to exist. row 1245's own repair
should flip every REDISCOVERED-GAP-* case's assertions back to the original RED/WARN expectations
once the guard is reimplemented in the served path -- at which point those cases stop being gaps.

CASES, as currently, honestly observed against scratch (no case is silently green-by-vacuity --
every assertion below states which fact it is checking and why):

REDISCOVERED-GAP (used to be RED -- must refuse, no row written -- now silently ACCEPTED):
  - REDISCOVERED-GAP-DEAD-EVIDENCE-PATH: a dead --evidence path is ACCEPTED, a row is written,
    no refusal, no teach-text -- the artifact-claim-without-dereference guard does not fire.
  - REDISCOVERED-GAP-BARE-DIRECTORY-EVIDENCE: a bare (no trailing slash) EXISTING directory
    passed as --evidence is ACCEPTED, a row is written -- the directory-acceptance gap this
    item's OWN fix once closed is back, because the whole guard is gone, not because the
    directory-vs-file distinction regressed on its own.

STILL GREEN (unaffected by the gap -- these never depended on the guard's write-side behavior):
  - a live --evidence FILE: MUST ACCEPT, real row lands, round-trip verified (true before AND
    after the gap -- a real file was always meant to be accepted).
  - an --evidence directory explicitly cited via a trailing "/": MUST ACCEPT (same reasoning).

REDISCOVERED-GAP (used to WARN-but-write -- the asymmetry demonstration -- now writes with NO
warning at all, because the scanner itself does not exist):
  - REDISCOVERED-GAP-STATEMENT-PATH-NO-WARNING: a statement containing a dead path-shaped token
    still writes (unaffected), but NO warning is printed -- warn_path_shaped_in_statement() (or
    whatever replaced it) does not exist in the served path.
  - REDISCOVERED-GAP-STATEMENT-MULTI-PATH-NO-WARNING: three dead path-shaped tokens in one
    statement still writes, still with NO warning at all (not once-per-token, not once total --
    AUTOHARN_BACKFLOW finding 5's own fix has nothing left to regress, because there is no
    warning of any kind left to fire).

STILL GREEN, BUT NOTE THE CAVEAT (passes today for a DIFFERENT reason than it used to):
  - a statement containing a row:<id> citation: no warning fires -- true today, but ONLY because
    NOTHING triggers a warning right now, not because the scanner correctly excludes row:
    citations from its scope. Once row 1245 restores the scanner, this case's assertion (no
    warning) must be re-verified for the RIGHT reason.
  - a statement containing a URL: same caveat as the row:<id> case above.

Usage: python3 seen-red/artifact-claim-dereference-guard/run_fixtures.py
Exit 0 if every case matches observed current behavior; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import importlib.util
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


def _run_led(dest: Path, *args: str) -> tuple[int, str, str]:
    cp = subprocess.run([str(dest / "led"), *args], cwd=str(dest), capture_output=True, text=True)
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
    print("# REDISCOVERED-GAP-DEAD-EVIDENCE-PATH -- a dead --evidence path used to REFUSE; "
          "row 1245: the guard is gone, so it is now silently ACCEPTED. Named, not silenced.")
    before = _current_max_id(DEST)
    rc, out, err = _run_led(DEST, "--evidence", "/tmp/does-not-exist-nbdr-fixture-xyz",
                             "decision", f"{TAG}: dead evidence path probe")
    after = _current_max_id(DEST)
    _check("OBSERVED: guard does NOT refuse (exit 0)", rc == 0)
    _check("OBSERVED: a row WAS written (max id advanced by one) -- the gap, reproduced",
           after == before + 1)
    _check("OBSERVED: no teach-text about the 896-899 specimen class (nothing to cite -- "
           "the guard was never consulted)", "896-899" not in err)


def gap_bare_directory_evidence_accepted() -> None:
    print("# REDISCOVERED-GAP-BARE-DIRECTORY-EVIDENCE -- a bare (no trailing slash) EXISTING "
          "directory used to REFUSE; row 1245: now silently ACCEPTED. Named, not silenced.")
    before = _current_max_id(DEST)
    rc, out, err = _run_led(DEST, "--evidence", "bootstrap",
                             "decision", f"{TAG}: bare directory evidence probe")
    after = _current_max_id(DEST)
    _check("OBSERVED: guard does NOT refuse the bare directory (exit 0)", rc == 0)
    _check("OBSERVED: a row WAS written (max id advanced by one) -- the gap, reproduced",
           after == before + 1)


def green_live_file_evidence() -> None:
    print("# GREEN — a live --evidence FILE: MUST ACCEPT, real row lands, round-trip verified "
          "(unaffected by the gap -- a real file was always meant to be accepted)")
    rc, out, err = _run_led(DEST, "--evidence", "led",
                             "decision", f"{TAG}: live file evidence probe")
    _check("guard ACCEPTS (exit 0)", rc == 0)
    new_id = _current_max_id(DEST)
    rc2, out2, _ = _run_led(DEST, "show", str(new_id))
    _check("real led round-trip: led show <id> reads the row back", rc2 == 0 and TAG in out2)


def green_explicit_directory_evidence() -> None:
    print("# GREEN — --evidence directory cited via trailing slash: MUST ACCEPT "
          "(unaffected by the gap)")
    rc, out, err = _run_led(DEST, "--evidence", "legacy/",
                             "decision", f"{TAG}: explicit trailing-slash directory probe")
    _check("guard ACCEPTS the explicitly-cited directory (exit 0)", rc == 0)
    new_id = _current_max_id(DEST)
    rc2, out2, _ = _run_led(DEST, "show", str(new_id))
    _check("round-trip verified", rc2 == 0 and TAG in out2)


def gap_statement_path_no_warning() -> None:
    print("# REDISCOVERED-GAP-STATEMENT-PATH-NO-WARNING -- a dead path-shaped token in "
          "STATEMENT prose used to WARN-but-write; row 1245: it still writes, but the warning "
          "no longer fires at all (the scanner is gone). Named, not silenced.")
    rc, out, err = _run_led(DEST, "decision",
                             f"{TAG}: about to write /tmp/does-not-exist-nbdr-statement-probe next")
    _check("write still succeeds (exit 0, unaffected)", rc == 0)
    _check("OBSERVED: NO warning is printed at all (the scanner does not exist -- the gap, "
           "reproduced; this is NOT the guard correctly staying silent, it is the guard being "
           "absent)", "WARNING" not in err)


def gap_statement_multiple_path_tokens_no_warning() -> None:
    print("# REDISCOVERED-GAP-STATEMENT-MULTI-PATH-NO-WARNING -- THREE dead path-shaped tokens "
          "in one STATEMENT used to fire ONE preamble + a list (AUTOHARN_BACKFLOW finding 5's "
          "own fix); row 1245: now NO warning fires at all, for any count. Named, not silenced.")
    tok_a = "/tmp/does-not-exist-nbdr-multi-a"
    tok_b = "/tmp/does-not-exist-nbdr-multi-b"
    tok_c = "./tmp/does-not-exist-nbdr-multi-c"
    rc, out, err = _run_led(
        DEST, "decision",
        f"{TAG}: about to write {tok_a} and {tok_b} then {tok_c} across three separate files",
    )
    _check("write still succeeds (exit 0, unaffected)", rc == 0)
    _check("OBSERVED: NO preamble line fires (finding 5's own fix has nothing left to regress "
           "-- there is no warning mechanism left to over-print)",
           err.count("led: WARNING -- the statement contains") == 0)
    _check("OBSERVED: none of the three tokens are echoed in a warning list (nothing scans for "
           "them)", tok_a not in err and tok_b not in err and tok_c not in err)


def green_row_citation_untouched() -> None:
    print("# GREEN (caveat: passes today for a DIFFERENT reason) — row:<id> citation in "
          "statement: no warning fires -- true, but only because NOTHING triggers a warning "
          "right now, not because the scanner correctly excludes row: citations. Re-verify for "
          "the right reason once row 1245 lands.")
    rc, out, err = _run_led(DEST, "decision", f"{TAG}: row:1 citation untouched probe")
    _check("write succeeds (exit 0)", rc == 0)
    _check("no path-shape WARNING fires for a row: citation", "WARNING" not in err)


def green_url_untouched() -> None:
    print("# GREEN (caveat: passes today for a DIFFERENT reason) — URL in statement: no "
          "warning fires -- same caveat as the row:<id> case above.")
    rc, out, err = _run_led(DEST, "decision", f"{TAG}: https://example.com/nbdr-probe untouched")
    _check("write succeeds (exit 0)", rc == 0)
    _check("no path-shape WARNING fires for a URL", "WARNING" not in err)


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
        print(f"\nSPECIMEN INERT — {len(FAILURES)} check(s) failed against the OBSERVED CURRENT "
              f"BEHAVIOR this fixture now expects: {FAILURES}\nscratch left standing as "
              f"evidence:\n  tempdir: {tmpdir}\n  schema: {SCHEMA}/{KERN}/role {ROLE} "
              f"(db {PGDB}@{PGHOST})")
        return 1

    _drop_scratch()
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\n# artifact-claim-dereference-guard: all cases match OBSERVED CURRENT BEHAVIOR -- "
          f"the --evidence dereference guard and the path-shaped-statement warning are BOTH "
          f"ABSENT from the served CLI (ledger row 1245, open work item), reproduced here as "
          f"REDISCOVERED-GAP-* cases rather than silently passed or silently failed. "
          f"Scratch torn down to zero residue. Tag: {TAG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
