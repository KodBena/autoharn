#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-12T23:33:13Z
#   last-change: 2026-07-12T23:33:39Z
#   contributors: 3c50e030/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures — both-polarity live proof for the `actual:` intake-validation feature
(tracker item `actual-intake-grammar`, 2026-07-13; gates/fixture_census.py REGISTRY entry
"actual-intake-validation"). Mirrors seen-red/estimate-intake-validation/run_fixtures.py's
scratch-and-drop pattern exactly: a throwaway project directory (via bootstrap/track-work.sh)
plus a throwaway schema pair in the TOY db, torn down after unless a case fails (left standing
as evidence, matching the standing-probe convention every other run_fixtures.py in this repo
uses).

WHAT THIS PROVES: `bootstrap/templates/led.tmpl` validates an `actual:`-prefixed decision
statement (whitespace-normalized copy) against the six-field grammar design/
USER-RETROSPECTIVE-RECIPE.md's "The `actual:` statement grammar" section specifies BEFORE the
INSERT -- field count, TASK-SLUG shape, TOOL-CALLS/SUBAGENT-SPAWNS bare-integer-no-range shape
(the one deliberate divergence from `estimate:`), WALL-CLOCK duration-or-range shape, TOKENS
exact-ish-K/M-or-OOM-bucket-or-small-bare-number shape, non-empty SOURCE -- refusing loudly
(exit nonzero, nothing written, teach-text naming the grammar and restating the never-police
invariant) on any single-field defect, and accepting a well-formed statement byte-exact.
`bootstrap/templates/pickup.tmpl`'s `_read_actuals()`/`estimates()` pairing renders an accepted
`actual:` row directly beneath the `estimate:` block sharing its TASK-SLUG, and lists an
unmatched actual afterward -- using the identical newline-normalization and leading-whitespace
coherence-partner contract `resources()`/`estimates()` already keep.

CASES (all live subprocess runs of the real `led`/`pickup` verbs against a real scratch
deployment -- never a mock):

  ADOPT                         -- bootstrap/track-work.sh stands up the scratch deployment.
  RED-MALFORMED-FIELDCOUNT      -- a 3-field `actual:` statement is REFUSED (nonzero exit), row
                                    count witnessed UNCHANGED before/after (atomicity by
                                    refusal-before-write).
  RED-RANGE-WHERE-POINT         -- a 6-field statement whose TOOL-CALLS field is an N-M range
                                    ("40-60", the shape `estimate:` accepts) is REFUSED -- the
                                    one deliberate divergence: a measurement is a point, not a
                                    range.
  RED-BARE-AMBIGUOUS-NUMBER     -- a 6-field statement whose TOKENS field is a bare unsuffixed
                                    number above 999 ("12000") is REFUSED, row count unchanged.
  RED-EMPTY-SOURCE              -- a 6-field statement whose SOURCE field is empty is REFUSED,
                                    row count unchanged.
  GREEN-WHOLE-ITEM               -- a well-formed whole-work-item `actual:` statement (TASK-SLUG
                                    naming a whole tracker item) is ACCEPTED (exit 0) and stored
                                    byte-exact.
  GREEN-SPAWN-GRANULARITY        -- a well-formed `actual:` statement whose TASK-SLUG names a
                                    single spawn within a work item (the
                                    `item-slug-b-round-2` granularity convention) is ACCEPTED and
                                    stored byte-exact.
  GREEN-OOM-BUCKET-TOKENS        -- a well-formed `actual:` statement using the closed OOM-bucket
                                    TOKENS vocabulary (shared with `estimate:`'s TOKEN-OOM) is
                                    ACCEPTED and stored byte-exact.
  GREEN-PICKUP-PAIRING           -- a matching `estimate:` row for GREEN-WHOLE-ITEM's TASK-SLUG
                                    is declared, and `./pickup`'s ESTIMATES section renders the
                                    `actual:` block directly beneath the matching `estimate:`
                                    block, with no "MALFORMED" string anywhere in the section.
  GREEN-PICKUP-UNMATCHED          -- GREEN-SPAWN-GRANULARITY's TASK-SLUG has no matching
                                    `estimate:` row on record, and `./pickup`'s ESTIMATES section
                                    lists it under its own unmatched-actuals listing.

Scratch-only: schema/kern/role derived from a throwaway name (`SCRATCH_NAME` below, distinct
from every other fixture's own scratch name in this repo) in the TOY db (192.168.122.1) plus a
throwaway tempdir -- both dropped/removed after, UNLESS a case FAILS (left standing as evidence,
kernel/fixtures/s22_work_item_fixture.py's own convention).

Usage: python3 seen-red/actual-intake-validation/run_fixtures.py
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
SCRATCH_NAME = "aivfixture"
SCHEMA, KERN, ROLE = SCRATCH_NAME, f"{SCRATCH_NAME}_kernel", f"{SCRATCH_NAME}_rw"

ACTUAL_MALFORMED_FIELDCOUNT = "actual: actual-intake-grammar | 47 | 2"
ACTUAL_RANGE_WHERE_POINT = "actual: actual-intake-grammar | 40-60 | 0 | 1h | 10K | a source"
ACTUAL_BARE_AMBIGUOUS_NUMBER = "actual: actual-intake-grammar | 47 | 2 | 1h | 12000 | a source"
ACTUAL_EMPTY_SOURCE = "actual: actual-intake-grammar | 47 | 2 | 1h | 10K |   "
# well-formed, whole-work-item granularity:
ACTUAL_WHOLE_ITEM = (
    "actual: actual-intake-grammar | 47 | 2 | 42m | 210K | harness task-notification "
    "duration_ms+subagent_tokens"
)
# well-formed, single-spawn granularity (the `item-slug-b-round-2` convention):
ACTUAL_SPAWN_GRANULARITY = (
    "actual: kr-titration-design-exploration-b-round-2 | 6 | 1 | 8m | 1.2M | orchestrator "
    "wall clock plus subagent's own self-reported token usage"
)
# well-formed, OOM-bucket TOKENS (shared closed vocabulary with estimate:'s TOKEN-OOM):
ACTUAL_OOM_BUCKET = (
    "actual: doc-legibility-sweep | 12 | 1 | 15m | 100K | orchestrator wall clock, "
    "subagent self-reported OOM bucket only"
)
# a matching estimate: row for ACTUAL_WHOLE_ITEM's TASK-SLUG, to prove pairing:
ESTIMATE_FOR_PAIRING = (
    "estimate: actual-intake-grammar | 40-60 | 0 | 3h-5h | 100K | scoped from "
    "cost-estimation-retro's own sibling grammar, a similarly-sized led.tmpl/pickup.tmpl "
    "validator pair plus one doc section and one seen-red fixture"
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

    def green_case(name: str, statement: str) -> None:
        before = _ledger_row_count(dest)
        r = _run(dest, "led", "decision", statement)
        after = _ledger_row_count(dest)
        accepted = r.returncode == 0
        grew = after == before + 1
        ok = accepted and grew
        if not ok:
            failures.append(f"{name}: exit={r.returncode} accepted={accepted} before={before} "
                             f"after={after}\nSTDERR:\n{r.stderr}")
        log(f"{name}: exit={r.returncode} accepted={accepted} row-count before={before} "
            f"after={after} (grew-by-one={grew}) -- {'PASS' if ok else 'FAIL'}")
        # Fetched by "most recent decision row" rather than a literal-quoted match against
        # `statement` -- several GREEN statements below carry an embedded apostrophe
        # ("subagent's own"), which a naive single-quoted SQL literal would mis-parse. This
        # script runs green_case() calls strictly sequentially with nothing interleaved, so
        # the newest decision row is always the one this call just inserted.
        r_stmt = _psql("-tAc", f"SET ROLE {ROLE}; SELECT statement FROM {SCHEMA}.ledger "
                                f"WHERE kind = 'decision' ORDER BY id DESC LIMIT 1;")
        stored_lines = [ln for ln in r_stmt.stdout.splitlines() if ln.strip()]
        stored_last = stored_lines[-1] if stored_lines else ""
        byte_exact = statement.strip() == stored_last
        if not byte_exact:
            failures.append(f"{name}: stored statement is not byte-exact\n"
                             f"EXPECTED:\n{statement!r}\nSTORED:\n{stored_last!r}")
        log(f"{name}: stored statement is byte-exact -- {'PASS' if byte_exact else 'FAIL'}")

    _drop_scratch()
    tmpdir = Path(tempfile.mkdtemp(prefix="actual-intake-validation-fixture-"))
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
    red_case("RED-MALFORMED-FIELDCOUNT", ACTUAL_MALFORMED_FIELDCOUNT, "got 3")
    red_case("RED-RANGE-WHERE-POINT", ACTUAL_RANGE_WHERE_POINT, "TOOL-CALLS")
    red_case("RED-BARE-AMBIGUOUS-NUMBER", ACTUAL_BARE_AMBIGUOUS_NUMBER, "TOKENS")
    red_case("RED-EMPTY-SOURCE", ACTUAL_EMPTY_SOURCE, "SOURCE")

    # --------------------------------------------------------------------------- GREEN cases
    green_case("GREEN-WHOLE-ITEM", ACTUAL_WHOLE_ITEM)
    green_case("GREEN-SPAWN-GRANULARITY", ACTUAL_SPAWN_GRANULARITY)
    green_case("GREEN-OOM-BUCKET-TOKENS", ACTUAL_OOM_BUCKET)

    # ------------------------------------------------------------------- GREEN-PICKUP-PAIRING
    # Declare a matching estimate: row for ACTUAL_WHOLE_ITEM's TASK-SLUG (actual-intake-grammar),
    # then confirm pickup's ESTIMATES section renders the actual beneath the matching estimate.
    r_est = _run(dest, "led", "decision", ESTIMATE_FOR_PAIRING)
    ok = r_est.returncode == 0
    if not ok:
        failures.append(f"GREEN-PICKUP-PAIRING setup: estimate: declare failed "
                         f"exit={r_est.returncode}\nSTDERR:\n{r_est.stderr}")
    log(f"GREEN-PICKUP-PAIRING setup: estimate: declared for pairing, exit={r_est.returncode} "
        f"-- {'PASS' if ok else 'FAIL'}")

    r_pickup = _run(dest, "pickup")
    out = r_pickup.stdout
    start = out.find("### SECTION: ESTIMATES")
    end = out.find("### SECTION:", start + 1)
    section_text = out[start:end if end != -1 else None].strip() if start != -1 else ""
    # The paired actual must appear on a line AFTER its matching estimate block's own header
    # line (slug + ledger row id), never before it and never inside the unmatched-actuals
    # listing.
    est_idx = section_text.find("actual-intake-grammar  (ledger row id=")
    act_idx = section_text.find("ACTUAL (ledger row id=")
    unmatched_idx = section_text.find("-- unmatched actuals")
    paired = (est_idx != -1 and act_idx != -1 and est_idx < act_idx
              and (unmatched_idx == -1 or act_idx < unmatched_idx)
              and "MALFORMED" not in section_text)
    if not paired:
        failures.append(f"GREEN-PICKUP-PAIRING: ESTIMATES section did not pair the actual "
                         f"beneath its matching estimate\n{section_text}")
    log(f"GREEN-PICKUP-PAIRING: ESTIMATES section pairs the actual-intake-grammar actual "
        f"beneath its matching estimate, no MALFORMED entries -- {'PASS' if paired else 'FAIL'}")
    log("--- pickup ESTIMATES section after pairing declaration (verbatim) ---")
    log(section_text)
    transcript.append(section_text)
    log("--- end pickup ESTIMATES section ---")

    # ------------------------------------------------------------------ GREEN-PICKUP-UNMATCHED
    # GREEN-SPAWN-GRANULARITY's TASK-SLUG (kr-titration-design-exploration-b-round-2) has no
    # matching estimate: row on record -- confirm it lists under the unmatched-actuals listing.
    unmatched_ok = (
        "-- unmatched actuals" in section_text
        and "kr-titration-design-exploration-b-round-2:" in section_text
    )
    if not unmatched_ok:
        failures.append(f"GREEN-PICKUP-UNMATCHED: unmatched actual not listed as expected\n"
                         f"{section_text}")
    log(f"GREEN-PICKUP-UNMATCHED: unmatched kr-titration-design-exploration-b-round-2 actual "
        f"listed under the unmatched-actuals listing -- {'PASS' if unmatched_ok else 'FAIL'}")

    if failures:
        print(f"\nactual-intake-validation fixture: {len(failures)} FAILURE(S) -- scratch "
              f"substrate left standing as evidence:\n  tempdir: {tmpdir}\n  schema:  {SCHEMA} / "
              f"{KERN} / {ROLE} (db {DB}@{PGHOST})")
        for f in failures:
            print(f"\n!! {f}")
        return 1

    _drop_scratch()
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\nactual-intake-validation fixture: all cases PASS, scratch substrate torn down to "
          f"zero residue (tempdir removed, schema {SCHEMA}/{KERN}/role {ROLE} dropped).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
