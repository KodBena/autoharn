#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T09:07:27Z
#   last-change: 2026-07-18T09:08:45Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

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

THE FIX (bootstrap/templates/led.tmpl, check_help_or_dash_first_word(), called immediately
before refuse_flag_in_statement() at both of that guard's own two call sites -- the generic
<kind> <statement...> path and `led review`): checked on the FIRST statement word only,
TWO TIERS BY INTENT --
  (1) --help / -h / help as the first word: prints that call site's own usage block and exits 0,
      WRITING NOTHING (a question, not a statement -- never a refusal, never a row).
  (2) any OTHER '-'-prefixed first word: REFUSED with usage, in refuse_flag_in_statement's own
      voice, nothing written -- closes the same silent-garbage-row gap for an UNKNOWN
      dash-leading first word that isn't a recognized help token either.
Genuinely dash-leading prose MID-SENTENCE (not the first word) is untouched -- first-word-only,
the same bound the pre-existing whole-word rule already uses to avoid false-positiving on
legitimately quoted prose.

CASES (all live subprocess runs of the real `./led` against a real scratch deployment, following
seen-red/led-refs-flag-order-parser-bug/run_fixtures.py's own scratch-and-drop pattern):

  ADOPT                         -- bootstrap/track-work.sh stands up the scratch deployment.
  GREEN-HELP-GENERIC            -- `./led decision help` and `./led finding -h` and
                                    `./led finding --help`: exit 0, usage text on stderr,
                                    row count UNCHANGED (nothing written).
  GREEN-HELP-REVIEW             -- `./led review <id> attest self-review --help`: exit 0,
                                    review-specific usage on stderr, row count unchanged.
  RED-DASH-FIRST-WORD-GENERIC   -- `./led finding --bogus-flag "text"`: REFUSED (nonzero exit),
                                    teach-text names the first word and usage, row count
                                    unchanged.
  RED-DASH-FIRST-WORD-REVIEW    -- `./led review <id> attest self-review --bogus "text"`:
                                    REFUSED, row count unchanged.
  GREEN-MID-SENTENCE-DASH       -- a statement whose FIRST word is ordinary prose but a LATER
                                    word is dash-leading (e.g. "prose mentioning -x mid
                                    sentence") is ACCEPTED, unchanged from before this item --
                                    the false-positive case this item's first-word-only bound
                                    must not trip.

Usage: python3 seen-red/led-help-token-closure/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import subprocess
import sys
import shutil
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
TRACK_WORK = REPO / "bootstrap" / "track-work.sh"
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
    r = subprocess.run([str(TRACK_WORK), str(dest), "--name", SCRATCH_NAME, "--db", DB,
                        "--host", PGHOST, "--schema", SCHEMA, "--kern", KERN, "--role", ROLE],
                        capture_output=True, text=True, cwd=str(REPO))
    ok = r.returncode == 0 and (dest / "deployment.json").exists()
    if not ok:
        failures.append(f"ADOPT: exit={r.returncode}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
    print(f"ADOPT: track-work.sh exit={r.returncode} deployment.json="
          f"{(dest / 'deployment.json').exists()} -- {'PASS' if ok else 'FAIL'}")
    if not ok:
        print(f"\nADOPT FAILED, aborting -- scratch left standing:\n  tempdir: {tmpdir}")
        for f in failures:
            print(f"\n!! {f}")
        return 1

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
    for probe_args, label in (
        (("decision", "help"), "help-word"),
        (("finding", "-h"), "dash-h"),
        (("finding", "--help"), "dash-dash-help"),
    ):
        before = _ledger_row_count(dest)
        r = _run(dest, "led", *probe_args)
        after = _ledger_row_count(dest)
        exit0 = r.returncode == 0
        shows_usage = "usage: led [flags] <kind> <statement...>" in r.stderr
        unchanged = before == after
        ok = exit0 and shows_usage and unchanged
        if not ok:
            failures.append(f"GREEN-HELP-GENERIC[{label}]: exit={r.returncode} "
                             f"shows_usage={shows_usage} before={before} after={after}\n"
                             f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
        print(f"GREEN-HELP-GENERIC[{label}]: exit={r.returncode} shows_usage={shows_usage} "
              f"row-count before={before} after={after} (unchanged={unchanged}) -- "
              f"{'PASS' if ok else 'FAIL'}")

    # ------------------------------------------------------------------- GREEN-HELP-REVIEW
    if seed_id is not None:
        before = _ledger_row_count(dest)
        r = _run(dest, "led", "review", seed_id, "attest", "self-review", "--help")
        after = _ledger_row_count(dest)
        exit0 = r.returncode == 0
        shows_usage = "usage: led review <entry-id> <verdict> <independence>" in r.stderr
        unchanged = before == after
        ok = exit0 and shows_usage and unchanged
        if not ok:
            failures.append(f"GREEN-HELP-REVIEW: exit={r.returncode} shows_usage={shows_usage} "
                             f"before={before} after={after}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
        print(f"GREEN-HELP-REVIEW: exit={r.returncode} shows_usage={shows_usage} row-count "
              f"before={before} after={after} (unchanged={unchanged}) -- {'PASS' if ok else 'FAIL'}")

    # ------------------------------------------------------------- RED-DASH-FIRST-WORD-GENERIC
    before = _ledger_row_count(dest)
    r = _run(dest, "led", "finding", "--bogus-flag", f"{TAG}: dash-first-word probe")
    after = _ledger_row_count(dest)
    refused = r.returncode != 0
    teaches = "dash-leading" in r.stderr and "--bogus-flag" in r.stderr
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
        teaches = "dash-leading" in r.stderr and "--bogus" in r.stderr
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
