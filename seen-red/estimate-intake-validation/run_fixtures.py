#!/usr/bin/env python3
"""run_fixtures — both-polarity live proof for the `estimate:` intake-validation feature
(tracker item `cost-estimation-retro`, 2026-07-12; gates/fixture_census.py REGISTRY entry
"estimate-intake-validation"). Mirrors seen-red/resource-intake-validation/run_fixtures.py's
scratch-and-drop pattern exactly: a throwaway project directory (via bootstrap/track-work.sh)
plus a throwaway schema pair in the TOY db, torn down after unless a case fails (left standing
as evidence, matching the standing-probe convention every other run_fixtures.py in this repo
uses).

WHAT THIS PROVES: `bootstrap/templates/led.tmpl` validates an `estimate:`-prefixed decision
statement (whitespace-normalized copy) against the six-field grammar
user-guide/USER-RETROSPECTIVE-RECIPE.md's "Estimate statement grammar" section specifies BEFORE the
INSERT -- field count, TASK-SLUG shape, TOOL-CALLS/SUBAGENT-SPAWNS count-or-range shape,
WALL-CLOCK duration-or-range shape, TOKEN-OOM closed vocabulary, non-empty BASIS -- refusing
loudly (exit nonzero, nothing written, teach-text naming the grammar) on any single-field defect,
and accepting a well-formed statement byte-exact. `bootstrap/templates/pickup.tmpl`'s estimates()
reader renders an accepted row cleanly under its own `### SECTION: ESTIMATES` header, using the
identical newline-normalization and leading-whitespace coherence-partner contract `resources()`
already keeps for `resource:`.

CASES (all live subprocess runs of the real `led`/`pickup` verbs against a real scratch
deployment -- never a mock):

  ADOPT                       -- bootstrap/track-work.sh stands up the scratch deployment.
  RED-MALFORMED-FIELDCOUNT    -- a 2-field `estimate:` statement is REFUSED (nonzero exit), row
                                 count witnessed UNCHANGED before/after (atomicity by
                                 refusal-before-write).
  RED-MALFORMED-SLUG          -- a well-formed-shaped 6-field statement whose TASK-SLUG contains
                                 an illegal character (uppercase/space) is REFUSED, row count
                                 unchanged.
  RED-MALFORMED-COUNT         -- a 6-field statement whose TOOL-CALLS field is not an integer or
                                 an N-M range ("many") is REFUSED, row count unchanged.
  RED-MALFORMED-DURATION      -- a 6-field statement whose WALL-CLOCK field matches no duration
                                 grammar ("soonish") is REFUSED, row count unchanged.
  RED-MALFORMED-TOKEN-OOM     -- a 6-field statement whose TOKEN-OOM field is outside the closed
                                 vocabulary ("500K") is REFUSED, row count unchanged.
  RED-MALFORMED-BASIS         -- a 6-field statement whose BASIS field is empty is REFUSED, row
                                 count unchanged.
  GREEN-WELL-FORMED           -- a well-formed statement using both range grammars (TOOL-CALLS
                                 and WALL-CLOCK as ranges) is ACCEPTED (exit 0) and stored
                                 byte-exact.
  GREEN-EMBEDDED-NEWLINE      -- a statement with an embedded newline + indent mid-word (the same
                                 shape the resource-intake-validation fixture reproduces for
                                 `resource:`) is ACCEPTED after whitespace normalization, and the
                                 STORED row preserves the embedded newline verbatim (normalization
                                 is validation-only scratch, never persisted).
  GREEN-PICKUP-RENDERS        -- `./pickup`'s ESTIMATES section shows the accepted well-formed row
                                 as one clean block and contains NO "MALFORMED" string anywhere in
                                 the ESTIMATES section.
  GREEN-LEADING-WHITESPACE    -- an `estimate:` declaration with LEADING whitespace (two spaces
                                 before the prefix) is accepted by led AND renders in pickup's
                                 ESTIMATES section -- the coherence-partner contract proven live,
                                 exactly as resource-intake-validation proves it for `resource:`.

Scratch-only: schema/kern/role derived from a throwaway name (`SCRATCH_NAME` below, distinct from
every other fixture's own scratch name in this repo) in the TOY db (192.168.122.1) plus a
throwaway tempdir -- both dropped/removed after, UNLESS a case FAILS (left standing as evidence,
kernel/fixtures/s22_work_item_fixture.py's own convention).

Usage: python3 seen-red/estimate-intake-validation/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402 (filing/pghost_resolve.py via seen-red/_fixture_env.py -- never a literal host default)


REPO = Path(__file__).resolve().parents[2]
TRACK_WORK = REPO / "bootstrap" / "track-work.sh"
PGHOST, DB = fixture_pghost(), "toy"
SCRATCH_NAME = "eivfixture"
SCHEMA, KERN, ROLE = SCRATCH_NAME, f"{SCRATCH_NAME}_kernel", f"{SCRATCH_NAME}_rw"

ESTIMATE_MALFORMED_FIELDCOUNT = "estimate: cost-estimation-retro | 40-60"
ESTIMATE_MALFORMED_SLUG = "estimate: Cost Retro | 10 | 0 | 1h | 10K | a basis"
ESTIMATE_MALFORMED_COUNT = "estimate: cost-estimation-retro | many | 0 | 1h | 10K | a basis"
ESTIMATE_MALFORMED_DURATION = "estimate: cost-estimation-retro | 10 | 0 | soonish | 10K | a basis"
ESTIMATE_MALFORMED_TOKEN_OOM = "estimate: cost-estimation-retro | 10 | 0 | 1h | 500K | a basis"
ESTIMATE_MALFORMED_BASIS = "estimate: cost-estimation-retro | 10 | 0 | 1h | 10K |   "
# well-formed, exercising BOTH range grammars (TOOL-CALLS and WALL-CLOCK as N-M ranges):
ESTIMATE_WELL_FORMED = (
    "estimate: cost-estimation-retro | 40-60 | 0 | 3h-5h | 100K | scoped from "
    "resource-accounting-spec stage A, a similarly-sized led.tmpl/pickup.tmpl validator "
    "pair plus one doc section and one seen-red fixture"
)
# an embedded newline + 4-space indent splitting "operational-efficiency" from its own
# continuation -- the same shape resource-intake-validation reproduces for `resource:`:
ESTIMATE_EMBEDDED_NEWLINE = (
    "estimate: doc-legibility-sweep | 20-30 | 1 | 2h | 10K | a routine pass over the "
    "operational-efficiency\n    retrospective backlog, similar in scope to the last one"
)
# leading whitespace before the prefix -- the coherence-partner case:
ESTIMATE_LEADING_WHITESPACE = (
    "  estimate: tsort-port | 5 | 0 | 30m | 1K | trivial binary wrap, no arithmetic surface"
)


def _psql(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["psql", "-h", PGHOST, "-d", DB, *args],
                           capture_output=True, text=True)


def _drop_scratch() -> None:
    _psql("-v", "ON_ERROR_STOP=0", "-q",
          "-c", f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE;",
          "-c", f"DROP SCHEMA IF EXISTS {KERN} CASCADE;",
          "-c", f"DROP ROLE IF EXISTS {ROLE};")


def _run(dest: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    return subprocess.run([str(dest / args[0]), *args[1:]],
                           capture_output=True, text=True, cwd=str(dest), env=full_env)


def _ledger_row_count(dest: Path) -> int:
    r = _psql("-tAc", f"SET ROLE {ROLE}; SELECT count(*) FROM {SCHEMA}.ledger;")
    return int(r.stdout.strip().splitlines()[-1])


def main() -> int:
    failures: list[str] = []
    transcript: list[str] = []

    def log(line: str) -> None:
        print(line)
        transcript.append(line)

    def red_case(name: str, statement: str, expect_substr: str) -> None:
        before = _ledger_row_count(dest)
        r = _run(dest, "led", "decision", statement)
        after = _ledger_row_count(dest)
        refused = r.returncode != 0 and "REFUSED" in r.stderr and expect_substr in r.stderr
        unchanged = before == after
        ok = refused and unchanged
        if not ok:
            failures.append(f"{name}: exit={r.returncode} refused={refused} before={before} "
                             f"after={after}\nSTDERR:\n{r.stderr}")
        log(f"{name}: exit={r.returncode} refused={refused} row-count before={before} "
            f"after={after} (unchanged={unchanged}) -- {'PASS' if ok else 'FAIL'}")

    _drop_scratch()
    tmpdir = Path(tempfile.mkdtemp(prefix="estimate-intake-validation-fixture-"))
    dest = tmpdir / "project"

    # --------------------------------------------------------------------------------- ADOPT
    r = subprocess.run([str(TRACK_WORK), str(dest), "--name", SCRATCH_NAME, "--db", DB,
                        "--host", PGHOST, "--schema", SCHEMA, "--kern", KERN, "--role", ROLE],
                        capture_output=True, text=True, cwd=str(REPO))
    ok = r.returncode == 0 and (dest / "deployment.json").exists()
    if not ok:
        failures.append(f"ADOPT: exit={r.returncode}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
    log(f"ADOPT: track-work.sh exit={r.returncode} deployment.json="
        f"{(dest / 'deployment.json').exists()} -- {'PASS' if ok else 'FAIL'}")

    # ---------------------------------------------------------------------------- RED cases
    red_case("RED-MALFORMED-FIELDCOUNT", ESTIMATE_MALFORMED_FIELDCOUNT, "got 2")
    red_case("RED-MALFORMED-SLUG", ESTIMATE_MALFORMED_SLUG, "TASK-SLUG")
    red_case("RED-MALFORMED-COUNT", ESTIMATE_MALFORMED_COUNT, "TOOL-CALLS")
    red_case("RED-MALFORMED-DURATION", ESTIMATE_MALFORMED_DURATION, "WALL-CLOCK")
    red_case("RED-MALFORMED-TOKEN-OOM", ESTIMATE_MALFORMED_TOKEN_OOM, "TOKEN-OOM")
    red_case("RED-MALFORMED-BASIS", ESTIMATE_MALFORMED_BASIS, "BASIS")

    # -------------------------------------------------------------------------- GREEN-WELL-FORMED
    before = _ledger_row_count(dest)
    r_good = _run(dest, "led", "decision", ESTIMATE_WELL_FORMED)
    after = _ledger_row_count(dest)
    accepted = r_good.returncode == 0
    grew = after == before + 1
    ok = accepted and grew
    if not ok:
        failures.append(f"GREEN-WELL-FORMED: exit={r_good.returncode} accepted={accepted} "
                         f"before={before} after={after}\nSTDERR:\n{r_good.stderr}")
    log(f"GREEN-WELL-FORMED: exit={r_good.returncode} accepted={accepted} "
        f"row-count before={before} after={after} (grew-by-one={grew}) -- "
        f"{'PASS' if ok else 'FAIL'}")

    r_stmt = _psql("-tAc", f"SET ROLE {ROLE}; SELECT statement FROM {SCHEMA}.ledger "
                            f"WHERE kind = 'decision' AND statement LIKE 'estimate:%' "
                            f"ORDER BY id DESC LIMIT 1;")
    stored = r_stmt.stdout
    # -tAc with a leading "SET ROLE ...;" in the same -c string echoes one "SET" notice line
    # ahead of the query's own result (the same leading-line convention this file's
    # _ledger_row_count / _psql_tuples-style reads elsewhere in this repo already drop) -- the
    # query's own result is always the LAST non-empty line.
    stored_lines = [ln for ln in stored.splitlines() if ln.strip()]
    stored_last = stored_lines[-1] if stored_lines else ""
    byte_exact = ESTIMATE_WELL_FORMED.strip() == stored_last
    if not byte_exact:
        failures.append(f"GREEN-WELL-FORMED: stored statement is not byte-exact\n"
                         f"EXPECTED:\n{ESTIMATE_WELL_FORMED!r}\nSTORED:\n{stored_last!r}")
    log(f"GREEN-WELL-FORMED: stored statement is byte-exact -- {'PASS' if byte_exact else 'FAIL'}")

    # -------------------------------------------------------------------- GREEN-EMBEDDED-NEWLINE
    before = _ledger_row_count(dest)
    r_nl = _run(dest, "led", "decision", ESTIMATE_EMBEDDED_NEWLINE)
    after = _ledger_row_count(dest)
    accepted = r_nl.returncode == 0
    grew = after == before + 1
    ok = accepted and grew
    if not ok:
        failures.append(f"GREEN-EMBEDDED-NEWLINE: exit={r_nl.returncode} accepted={accepted} "
                         f"before={before} after={after}\nSTDERR:\n{r_nl.stderr}")
    log(f"GREEN-EMBEDDED-NEWLINE: exit={r_nl.returncode} accepted={accepted} "
        f"row-count before={before} after={after} (grew-by-one={grew}) -- "
        f"{'PASS' if ok else 'FAIL'}")

    r_stmt_nl = _psql("-tAc", f"SET ROLE {ROLE}; SELECT statement FROM {SCHEMA}.ledger "
                              f"WHERE kind = 'decision' AND statement LIKE 'estimate: doc-legibility-sweep%' "
                              f"ORDER BY id DESC LIMIT 1;")
    stored_nl = r_stmt_nl.stdout
    byte_exact_nl = "\n    retrospective backlog" in stored_nl
    if not byte_exact_nl:
        failures.append(f"GREEN-EMBEDDED-NEWLINE: stored statement lost byte fidelity "
                         f"(expected the embedded newline+indent verbatim)\nSTORED:\n{stored_nl!r}")
    log(f"GREEN-EMBEDDED-NEWLINE: stored statement is byte-exact (embedded newline preserved) -- "
        f"{'PASS' if byte_exact_nl else 'FAIL'}")

    # ------------------------------------------------------------------------ GREEN-PICKUP-RENDERS
    r_pickup = _run(dest, "pickup")
    out = r_pickup.stdout
    start = out.find("### SECTION: ESTIMATES")
    end = out.find("### SECTION:", start + 1)
    section_text = out[start:end if end != -1 else None].strip() if start != -1 else ""
    renders_clean = ("cost-estimation-retro" in section_text
                      and "MALFORMED" not in section_text)
    if not renders_clean:
        failures.append(f"GREEN-PICKUP-RENDERS: ESTIMATES section did not render cleanly\n"
                         f"{section_text}")
    log(f"GREEN-PICKUP-RENDERS: ESTIMATES section renders 'cost-estimation-retro' with no "
        f"MALFORMED entries -- {'PASS' if renders_clean else 'FAIL'}")
    log("--- pickup ESTIMATES section (verbatim) ---")
    log(section_text)
    transcript.append(section_text)
    log("--- end pickup ESTIMATES section ---")

    # -------------------------------------------------------------- GREEN-LEADING-WHITESPACE
    before = _ledger_row_count(dest)
    r_ws = _run(dest, "led", "decision", ESTIMATE_LEADING_WHITESPACE)
    after = _ledger_row_count(dest)
    accepted = r_ws.returncode == 0
    grew = after == before + 1
    ok = accepted and grew
    if not ok:
        failures.append(f"GREEN-LEADING-WHITESPACE: led exit={r_ws.returncode} "
                         f"accepted={accepted} before={before} after={after}\n"
                         f"STDERR:\n{r_ws.stderr}")
    log(f"GREEN-LEADING-WHITESPACE: led exit={r_ws.returncode} accepted={accepted} "
        f"row-count before={before} after={after} (grew-by-one={grew}) -- "
        f"{'PASS' if ok else 'FAIL'}")

    r_pickup_ws = _run(dest, "pickup")
    out_ws = r_pickup_ws.stdout
    start = out_ws.find("### SECTION: ESTIMATES")
    end = out_ws.find("### SECTION:", start + 1)
    section_ws = out_ws[start:end if end != -1 else None].strip() if start != -1 else ""
    renders = ("tsort-port" in section_ws and "MALFORMED" not in section_ws)
    if not renders:
        failures.append(f"GREEN-LEADING-WHITESPACE: pickup ESTIMATES did not render the "
                         f"leading-whitespace declaration\n{section_ws}")
    log(f"GREEN-LEADING-WHITESPACE: pickup ESTIMATES renders 'tsort-port' with no MALFORMED "
        f"entries -- {'PASS' if renders else 'FAIL'}")
    log("--- pickup ESTIMATES section after leading-whitespace declaration (verbatim) ---")
    log(section_ws)
    transcript.append(section_ws)
    log("--- end pickup ESTIMATES section ---")

    if failures:
        print(f"\nestimate-intake-validation fixture: {len(failures)} FAILURE(S) -- scratch "
              f"substrate left standing as evidence:\n  tempdir: {tmpdir}\n  schema:  {SCHEMA} / "
              f"{KERN} / {ROLE} (db {DB}@{PGHOST})")
        for f in failures:
            print(f"\n!! {f}")
        return 1

    _drop_scratch()
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\nestimate-intake-validation fixture: all cases PASS, scratch substrate torn down to "
          f"zero residue (tempdir removed, schema {SCHEMA}/{KERN}/role {ROLE} dropped).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
