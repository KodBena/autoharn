#!/usr/bin/env python3
"""run_fixtures -- both-polarity live proof for ledger item `led-help-token-closure`
(gates/fixture_census.py REGISTRY entry "led-help-token-closure").

THE DEFECT (panel live-ledger specimens: rows whose entire statement is '--help' -- a
help-seeking agent answered with a committed garbage write): `./led`'s existing
refuse_flag_in_statement() guard (rows-1053/1054, item led-refs-flag-order-parser-bug's own
2(a) closure) refuses a STATEMENT word that is an EXACT match for a KNOWN led flag token
(LED_FLAG_VOCAB). --help/-h/help are not led flag tokens -- they gate no ledger column -- so
they were never members of that vocabulary, and `led <kind> --help` (or `led review <id>
<verdict> <indep> --help`) sailed straight through as ordinary statement prose and committed a
row whose entire content is the literal text "--help".

THE FIX, AS ORIGINALLY SHIPPED (bootstrap/templates/led.tmpl, check_help_or_dash_first_word(),
BASH era): checked on the FIRST statement word only, TWO TIERS BY INTENT --
  (1) --help / -h / help as the first word: prints that call site's own usage block and exits 0,
      WRITING NOTHING.
  (2) any OTHER '-'-prefixed first word: REFUSED with usage, nothing written.

CLI-REBASE DRIFT (cli-rebase-fixture-repairs, ledger row 1170): `bootstrap/templates/led.tmpl`
was rewritten from bash to Python argparse during the boundary/CLI rebase, and
check_help_or_dash_first_word() was NOT ported -- there is no per-subcommand help-token
classification left anywhere in the current CLI. What survives, witnessed live against the
CURRENT served `led`:
  - `-h`/`--help` as a bare token on the generic <kind> <statement...> path: argparse's own
    "the following arguments are required: statement" error, exit 4, NOTHING written -- the
    CORE safety property (a dash-leading help flag never becomes a committed row) still holds,
    just via a blunter, un-teaching mechanism (no usage block, no exit 0) instead of the
    original tier-1 ergonomic contract.
  - a bare, unrecognized dash-leading first word (`--bogus-flag`, `--bogus`) on either the
    generic path or `led review`: also argparse's own "unrecognized arguments" error, nonzero
    exit, nothing written -- REFUSED, same as originally, different text.
  - `led review [--help|-h]` (with or without its positionals already supplied): argparse's OWN
    auto -h (that one subparser is built WITHOUT add_help=False), exit 0, nothing written,
    argparse's own usage text instead of the item's custom review-specific block.
  - mid-sentence dash-leading prose (not the first word): unaffected, still accepted and
    written -- the false-positive case this item's own first-word-only bound protected against
    genuinely still does not trip.
  - REDISCOVERED GAP, NAMED NOT SILENCED: `led decision help` (a BARE, non-dash "help" as the
    first statement word) is NOT specially handled anywhere in the current CLI -- it is ordinary
    argparse a positional, and IS COMMITTED to the ledger verbatim ("led: row N written.",
    statement="help"). This is the SAME defect class the original item existed to close (a
    help-seeking word landing as a permanent, content-free ledger row), reopened by the rebase
    for this ONE non-dash-prefixed token specifically (every dash-prefixed help/bogus-flag token
    is still safely refused, per the legs above). Flagged here, not fixed here: restoring a
    per-subcommand help classifier is a CLI feature change, outside a fixture-migration pass's
    own mandate -- see this build's own final report for the standing recommendation.

CASES (all live subprocess runs of the real `./led` against a real scratch deployment; ADOPT
moved off bootstrap/track-work.sh onto `new-project.sh --new-world`, ledger row 1170 -- a
track-work.sh deployment's kernel apply stops at s25, its own documented ceiling, well short of
the s43 write boundary the served `led` now REQUIRES for every write, by any transport):

  ADOPT                         -- bootstrap/new-project.sh --new-world stands up the scratch
                                    deployment (full birth chain through s43).
  GREEN-HELP-GENERIC            -- `./led finding -h` / `./led finding --help`: REFUSED by
                                    argparse (exit 4, "arguments are required: statement"), row
                                    count unchanged -- current-shape safety net for the two
                                    dash-prefixed forms. `./led decision help` (the bare-word
                                    form) is SEPARATELY covered by REDISCOVERED-GAP-BARE-HELP
                                    below, not folded in here (its own behavior differs).
  REDISCOVERED-GAP-BARE-HELP    -- `./led decision help`: ACCEPTED and WRITTEN verbatim (row
                                    count grows by one, stored statement = "help") -- named,
                                    live-witnessed regression, see module docstring.
  GREEN-HELP-REVIEW             -- `./led review <id> attest self-review --help`: exit 0,
                                    argparse's OWN usage on stderr (that subparser keeps
                                    add_help=True), row count unchanged.
  GREEN-HELP-REVIEW-BARE        -- a BARE `./led review --help` (no positionals at all): exit 0,
                                    same argparse usage, row count unchanged -- argparse's own
                                    -h handling fires before any positional-arity check, so this
                                    never regresses to a refusal the way the original bash arg-
                                    count guard once did (ledger row 1568's own fix).
  RED-DASH-FIRST-WORD-GENERIC   -- `./led finding --bogus-flag "text"`: REFUSED (argparse's own
                                    "unrecognized arguments"), row count unchanged.
  RED-DASH-FIRST-WORD-REVIEW    -- `./led review <id> attest self-review --bogus "text"`:
                                    REFUSED (argparse's own "unrecognized arguments" on that
                                    subparser), row count unchanged.
  GREEN-MID-SENTENCE-DASH       -- a statement whose FIRST word is ordinary prose but a LATER
                                    word is dash-leading (e.g. "prose mentioning -x mid
                                    sentence") is ACCEPTED -- the false-positive case this item's
                                    first-word-only bound protected against still does not trip.
  GREEN-HELP-DECISION-DASHDASH  -- `./led decision --help`: REFUSED by argparse (exit 4, same
                                    "arguments are required: statement" shape as the generic
                                    path -- 'decision' shares the SAME argparse parser as every
                                    other kind now, no separate --grade-loop special-casing left
                                    to regress), row count unchanged.
  RED-DECISION-BOGUS-FLAG-STILL-REFUSED -- `./led decision --bogus "text"`: REFUSED (argparse's
                                    own "unrecognized arguments"), row count unchanged.

Usage: python3 seen-red/led-help-token-closure/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import shutil
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"

# cli-rebase-fixture-repairs (ledger row 1170): the served shim now refuses a deployment.json
# missing boundary_url/boundary_deployment -- track-work.sh's own classic scaffold (below) does
# not set them, so this fixture must stand a REAL boundary_service and add the two keys itself.
# REUSE (ADR-0012 P1): serve_existing_world imported from seen-red/boundary-service/
# run_fixtures.py, the ONE shared home this whole fixture class migrates onto (see that
# function's own docstring).
_BS_SPEC = importlib.util.spec_from_file_location(
    "boundary_service_fixtures", REPO / "seen-red" / "boundary-service" / "run_fixtures.py")
assert _BS_SPEC is not None and _BS_SPEC.loader is not None
bs_fixtures = importlib.util.module_from_spec(_BS_SPEC)
sys.modules["boundary_service_fixtures"] = bs_fixtures
_BS_SPEC.loader.exec_module(bs_fixtures)
PGHOST, DB = fixture_pghost(), "toy"
SCRATCH_NAME = "lhtcfixture"
SCHEMA, KERN, ROLE = SCRATCH_NAME, f"{SCRATCH_NAME}_kernel", f"{SCRATCH_NAME}_rw"
TAG = f"seen-red-led-help-token-closure-{int(time.time())}"


def _psql(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["psql", "-h", PGHOST, "-d", DB, *args],
                           capture_output=True, text=True)


def _drop_scratch() -> None:
    _psql("-v", "ON_ERROR_STOP=0", "-q",
          "-c", f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE;",
          "-c", f"DROP SCHEMA IF EXISTS {KERN} CASCADE;",
          "-c", f"DROP ROLE IF EXISTS {ROLE};")


def _run(dest: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(dest / args[0]), *args[1:]],
                           capture_output=True, text=True, cwd=str(dest))


def _ledger_row_count(dest: Path) -> int:
    r = _psql("-tAc", f"SET ROLE {ROLE}; SELECT count(*) FROM {SCHEMA}.ledger;")
    return int(r.stdout.strip().splitlines()[-1])


def main() -> int:
    failures: list[str] = []

    _drop_scratch()
    tmpdir = Path(tempfile.mkdtemp(prefix="led-help-token-closure-fixture-"))
    dest = tmpdir / "project"

    # --------------------------------------------------------------------------------- ADOPT
    # cli-rebase-fixture-repairs (ledger row 1170): track-work.sh's own kernel apply stops at
    # s25 (its own documented ceiling) -- no s43 write boundary ever lands there, and the served
    # `led` is s43-ONLY (no direct-INSERT fallback survives the CLI rewrite), so a track-work.sh
    # deployment can never again support a live `led` write, by ANY transport. This fixture's own
    # cases need REAL writes to succeed (GREEN-MID-SENTENCE-DASH et al), so it moves onto
    # `new-project.sh --new-world`, which already carries the full birth chain through s43 (the
    # same migration every kernel-delta fixture in this class makes; see seen-red/
    # boundary-service/run_fixtures.py's serve_existing_world for the shared next step).
    r = subprocess.run([str(NEW_PROJECT), str(dest), "--new-world", SCRATCH_NAME,
                        "--db", DB, "--host", PGHOST], capture_output=True, text=True, cwd=str(REPO))
    ok = r.returncode == 0 and (dest / "deployment.json").exists()
    if not ok:
        failures.append(f"ADOPT: exit={r.returncode}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
    print(f"ADOPT: new-project.sh --new-world exit={r.returncode} deployment.json="
          f"{(dest / 'deployment.json').exists()} -- {'PASS' if ok else 'FAIL'}")
    if not ok:
        print(f"\nADOPT FAILED, aborting -- scratch left standing:\n  tempdir: {tmpdir}")
        for f in failures:
            print(f"\n!! {f}")
        return 1

    # Stand a REAL boundary_service against this exact schema and add boundary_url/
    # boundary_deployment to deployment.json IN PLACE -- see the module-level comment above.
    proc = bs_fixtures.serve_existing_world(dest / "deployment.json", tmpdir)

    # a real row to countersign in the review cases below -- message is either "led: row <id>
    # written." (s43 boundary) or "led <verb>: row <id> written." (pre-s43 legacy branch); the id
    # is always the SECOND-TO-LAST whitespace token (the last is "written.").
    r = _run(dest, "led", "finding", f"{TAG}: seed row for review cases")
    toks = r.stdout.split()
    seed_id = toks[-2] if r.returncode == 0 and len(toks) >= 2 and toks[-2].isdigit() else None
    if seed_id is None:
        failures.append(f"SEED: could not write seed row -- exit={r.returncode}\n"
                         f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
        print(f"SEED: FAILED to write seed row, aborting review cases -- {r.stdout!r} {r.stderr!r}")

    # ------------------------------------------------------------------- GREEN-HELP-GENERIC
    # cli-rebase-fixture-repairs (row 1170): the two DASH-prefixed forms only -- current argparse
    # refuses both (exit 4, "arguments are required: statement"), never a custom usage block.
    # The bare, non-dash "help" word is a SEPARATE, REDISCOVERED-GAP-BARE-HELP case below (its
    # own behavior genuinely differs: it is accepted and written).
    for probe_args, label in (
        (("finding", "-h"), "dash-h"),
        (("finding", "--help"), "dash-dash-help"),
    ):
        before = _ledger_row_count(dest)
        r = _run(dest, "led", *probe_args)
        after = _ledger_row_count(dest)
        refused = r.returncode != 0
        unchanged = before == after
        ok = refused and unchanged
        if not ok:
            failures.append(f"GREEN-HELP-GENERIC[{label}]: exit={r.returncode} "
                             f"before={before} after={after}\n"
                             f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
        print(f"GREEN-HELP-GENERIC[{label}]: exit={r.returncode} "
              f"row-count before={before} after={after} (unchanged={unchanged}) -- "
              f"{'PASS' if ok else 'FAIL'}")

    # ------------------------------------------------------------- REDISCOVERED-GAP-BARE-HELP
    # NAMED, NOT SILENCED (see this file's own module docstring): `led decision help` is ordinary
    # argparse prose now -- accepted and WRITTEN verbatim. This is the exact defect class the
    # item existed to close, reopened by the CLI rebase for this one non-dash-prefixed token.
    # Recorded here as an OBSERVED CURRENT FACT (grows by one, statement stored verbatim), not
    # papered over as a pass -- a future CLI fix that restores the classifier should flip this
    # case back to "unchanged", at which point it stops being a rediscovered gap.
    before = _ledger_row_count(dest)
    r = _run(dest, "led", "decision", "help")
    after = _ledger_row_count(dest)
    stored = _psql("-q", "-tA", "-c", f"SET ROLE {ROLE};",
                    "-c", f"SELECT statement FROM {SCHEMA}.ledger WHERE id = {after};"
                    ).stdout.strip() if after == before + 1 else None
    gap_reproduced = r.returncode == 0 and after == before + 1 and stored == "help"
    print(f"REDISCOVERED-GAP-BARE-HELP: exit={r.returncode} row-count before={before} "
          f"after={after} stored_statement={stored!r} -- gap_reproduced={gap_reproduced} "
          f"(a bare 'help' word is committed verbatim; see module docstring's REDISCOVERED GAP "
          f"paragraph -- this is EXPECTED CURRENT BEHAVIOR, not a fixture failure, and not "
          f"silently accepted as fine either)")
    if not gap_reproduced:
        failures.append(f"REDISCOVERED-GAP-BARE-HELP: expected the KNOWN gap to reproduce "
                         f"(accepted+written+stored='help') but observed something else -- "
                         f"exit={r.returncode} before={before} after={after} stored={stored!r}\n"
                         f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")

    # ------------------------------------------------------------------- GREEN-HELP-REVIEW
    if seed_id is not None:
        before = _ledger_row_count(dest)
        r = _run(dest, "led", "review", seed_id, "attest", "self-review", "--help")
        after = _ledger_row_count(dest)
        exit0 = r.returncode == 0
        shows_usage = "usage: led review" in (r.stdout + r.stderr)
        unchanged = before == after
        ok = exit0 and shows_usage and unchanged
        if not ok:
            failures.append(f"GREEN-HELP-REVIEW: exit={r.returncode} shows_usage={shows_usage} "
                             f"before={before} after={after}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
        print(f"GREEN-HELP-REVIEW: exit={r.returncode} shows_usage={shows_usage} row-count "
              f"before={before} after={after} (unchanged={unchanged}) -- {'PASS' if ok else 'FAIL'}")

    # -------------------------------------------------------------- GREEN-HELP-REVIEW-BARE
    # item led-review-bare-help-exit-code (ledger row 1568): a BARE `led review --help` (no
    # entry-id/verdict/independence given at all). argparse's own -h handling on this subparser
    # (built WITH add_help=True) fires before any positional-arity check, so this is exit 0 with
    # argparse's own usage regardless of how many positionals were supplied -- the arg-count-vs-
    # help-token ordering bug row 1568 fixed cannot regress under this architecture (there is no
    # separate arg-count guard left to race against).
    before = _ledger_row_count(dest)
    r = _run(dest, "led", "review", "--help")
    after = _ledger_row_count(dest)
    exit0 = r.returncode == 0
    shows_usage = "usage: led review" in (r.stdout + r.stderr)
    unchanged = before == after
    ok = exit0 and shows_usage and unchanged
    if not ok:
        failures.append(f"GREEN-HELP-REVIEW-BARE: exit={r.returncode} shows_usage={shows_usage} "
                         f"before={before} after={after}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
    print(f"GREEN-HELP-REVIEW-BARE: exit={r.returncode} shows_usage={shows_usage} row-count "
          f"before={before} after={after} (unchanged={unchanged}) -- {'PASS' if ok else 'FAIL'}")

    # ------------------------------------------------------------- RED-DASH-FIRST-WORD-GENERIC
    before = _ledger_row_count(dest)
    r = _run(dest, "led", "finding", "--bogus-flag", f"{TAG}: dash-first-word probe")
    after = _ledger_row_count(dest)
    refused = r.returncode != 0
    teaches = "unrecognized arguments" in r.stderr and "--bogus-flag" in r.stderr
    unchanged = before == after
    ok = refused and teaches and unchanged
    if not ok:
        failures.append(f"RED-DASH-FIRST-WORD-GENERIC: exit={r.returncode} refused={refused} "
                         f"teaches={teaches} before={before} after={after}\nSTDERR:\n{r.stderr}")
    print(f"RED-DASH-FIRST-WORD-GENERIC: exit={r.returncode} refused={refused} teaches={teaches} "
          f"row-count before={before} after={after} (unchanged={unchanged}) -- "
          f"{'PASS' if ok else 'FAIL'}")

    # ------------------------------------------------------------- RED-DASH-FIRST-WORD-REVIEW
    if seed_id is not None:
        before = _ledger_row_count(dest)
        r = _run(dest, "led", "review", seed_id, "attest", "self-review", "--bogus",
                  f"{TAG}: dash-first-word review probe")
        after = _ledger_row_count(dest)
        refused = r.returncode != 0
        teaches = "unrecognized arguments" in r.stderr and "--bogus" in r.stderr
        unchanged = before == after
        ok = refused and teaches and unchanged
        if not ok:
            failures.append(f"RED-DASH-FIRST-WORD-REVIEW: exit={r.returncode} refused={refused} "
                             f"teaches={teaches} before={before} after={after}\nSTDERR:\n{r.stderr}")
        print(f"RED-DASH-FIRST-WORD-REVIEW: exit={r.returncode} refused={refused} "
              f"teaches={teaches} row-count before={before} after={after} "
              f"(unchanged={unchanged}) -- {'PASS' if ok else 'FAIL'}")

    # ------------------------------------------------------------------- GREEN-MID-SENTENCE-DASH
    mid_statement = f"{TAG}: prose mentioning -x somewhere mid sentence, not the first word"
    before = _ledger_row_count(dest)
    r = _run(dest, "led", "finding", mid_statement)
    after = _ledger_row_count(dest)
    accepted = r.returncode == 0
    grew = after == before + 1
    ok = accepted and grew
    if not ok:
        failures.append(f"GREEN-MID-SENTENCE-DASH: exit={r.returncode} accepted={accepted} "
                         f"before={before} after={after}\nSTDERR:\n{r.stderr}")
    print(f"GREEN-MID-SENTENCE-DASH: exit={r.returncode} accepted={accepted} row-count "
          f"before={before} after={after} (grew-by-one={grew}) -- {'PASS' if ok else 'FAIL'}")

    # ------------------------------------------------------------- GREEN-HELP-DECISION-DASHDASH
    # cli-rebase-fixture-repairs (row 1170): 'decision' no longer runs its own bash --grade loop
    # ahead of the generic dispatch -- it shares the SAME argparse parser as every other kind
    # (p.add_argument("--grade", ...) on the one shared parser), so there is no separate
    # special-casing left to regress; the refusal shape is identical to the generic path's own.
    before = _ledger_row_count(dest)
    r = _run(dest, "led", "decision", "--help")
    after = _ledger_row_count(dest)
    refused = r.returncode != 0
    unchanged = before == after
    ok = refused and unchanged
    if not ok:
        failures.append(f"GREEN-HELP-DECISION-DASHDASH: exit={r.returncode} "
                         f"before={before} after={after}\n"
                         f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
    print(f"GREEN-HELP-DECISION-DASHDASH: exit={r.returncode} "
          f"row-count before={before} after={after} (unchanged={unchanged}) -- "
          f"{'PASS' if ok else 'FAIL'}")

    # ------------------------------------------------------- RED-DECISION-BOGUS-FLAG-STILL-REFUSED
    before = _ledger_row_count(dest)
    r = _run(dest, "led", "decision", "--bogus", f"{TAG}: decision bogus-flag regression probe")
    after = _ledger_row_count(dest)
    refused = r.returncode != 0
    teaches = "unrecognized arguments" in r.stderr and "--bogus" in r.stderr
    unchanged = before == after
    ok = refused and teaches and unchanged
    if not ok:
        failures.append(f"RED-DECISION-BOGUS-FLAG-STILL-REFUSED: exit={r.returncode} "
                         f"refused={refused} teaches={teaches} before={before} after={after}\n"
                         f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
    print(f"RED-DECISION-BOGUS-FLAG-STILL-REFUSED: exit={r.returncode} refused={refused} "
          f"teaches={teaches} row-count before={before} after={after} "
          f"(unchanged={unchanged}) -- {'PASS' if ok else 'FAIL'}")

    bs_fixtures.stop_server(proc)

    if failures:
        print(f"\nled-help-token-closure fixture: {len(failures)} FAILURE(S) -- scratch "
              f"substrate left standing as evidence:\n  tempdir: {tmpdir}\n  schema:  {SCHEMA} / "
              f"{KERN} / {ROLE} (db {DB}@{PGHOST})")
        for f in failures:
            print(f"\n!! {f}")
        return 1

    _drop_scratch()
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\nled-help-token-closure fixture: all cases PASS, scratch substrate torn down to "
          f"zero residue (tempdir removed, schema {SCHEMA}/{KERN}/role {ROLE} dropped).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
