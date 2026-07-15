#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T01:50:17Z
#   last-change: 2026-07-14T01:50:17Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures — both-polarity live proof for the `outcome:` intake-validation feature (work item
`model-attribution-tracking`, maintainer ask 2026-07-12 ~noon: "track which MODEL executed each
dispatched task and what misses it produced"). Mirrors
seen-red/estimate-intake-validation/run_fixtures.py's scratch-and-drop pattern exactly: a
throwaway project directory (via bootstrap/track-work.sh) plus a throwaway schema pair in the TOY
db, torn down after unless a case fails (left standing as evidence).

WHAT THIS PROVES: `bootstrap/templates/led.tmpl` validates an `outcome:`-prefixed decision
statement (whitespace-normalized copy) against the five-field grammar
design/USER-RETROSPECTIVE-RECIPE.md's "The `outcome:` statement grammar" section (Section 7)
specifies BEFORE the INSERT -- field count, TASK-SLUG shape, MODEL shape, non-empty
SEAM-VERDICT/DEFECTS-FOUND-AT-SEAM/NOTES -- refusing loudly (exit nonzero, nothing written,
teach-text naming the grammar) on any single-field defect, and accepting a well-formed statement
byte-exact. UNLIKE `estimate:`/`actual:`, `outcome:` has no `./pickup` display section by design
(Section 7's own "consumption surface" -- retrospective-only, read via a documented psql+Python
method, deliberately never a live ranking surface) -- this fixture proves the row is readable
straight off `ledger_current` instead of proving a pickup section renders it.

CASES (all live subprocess runs of the real `led` verb against a real scratch deployment -- never
a mock):

  ADOPT                        -- bootstrap/track-work.sh stands up the scratch deployment.
  RED-MALFORMED-FIELDCOUNT     -- a 3-field `outcome:` statement is REFUSED (nonzero exit), row
                                  count witnessed UNCHANGED before/after (atomicity by
                                  refusal-before-write).
  RED-MALFORMED-SLUG           -- a well-formed-shaped 5-field statement whose TASK-SLUG contains
                                  an illegal character (uppercase/space) is REFUSED, row count
                                  unchanged.
  RED-MALFORMED-MODEL          -- a 5-field statement whose MODEL field contains a space is
                                  REFUSED, row count unchanged.
  RED-MALFORMED-VERDICT        -- a 5-field statement whose SEAM-VERDICT field is empty is
                                  REFUSED, row count unchanged.
  RED-MALFORMED-DEFECTS        -- a 5-field statement whose DEFECTS-FOUND-AT-SEAM field is empty
                                  is REFUSED, row count unchanged.
  RED-MALFORMED-NOTES          -- a 5-field statement whose NOTES field is empty is REFUSED, row
                                  count unchanged.
  GREEN-WELL-FORMED            -- a well-formed statement is ACCEPTED (exit 0) and stored
                                  byte-exact.
  GREEN-EMBEDDED-NEWLINE       -- a statement with an embedded newline + indent mid-word is
                                  ACCEPTED after whitespace normalization, and the STORED row
                                  preserves the embedded newline verbatim (normalization is
                                  validation-only scratch, never persisted).
  GREEN-LEADING-WHITESPACE     -- an `outcome:` declaration with LEADING whitespace (two spaces
                                  before the prefix) is accepted by led -- the same
                                  coherence-partner-adjacent trigger-condition contract every
                                  other prefix convention in this file proves.
  GREEN-READABLE-VIA-LEDGER    -- the accepted well-formed row is readable straight off
                                  `ledger_current` (the view every reader in this project's own
                                  `pickup.tmpl` already queries), proving the row is genuinely
                                  consumable by a future retrospective read, not merely stored.

Scratch-only: schema/kern/role derived from a throwaway name (`SCRATCH_NAME` below, distinct from
every other fixture's own scratch name in this repo) in the TOY db (192.168.122.1) plus a
throwaway tempdir -- both dropped/removed after, UNLESS a case FAILS (left standing as evidence).

Usage: python3 seen-red/outcome-intake-validation/run_fixtures.py
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
SCRATCH_NAME = "oivfixture"
SCHEMA, KERN, ROLE = SCRATCH_NAME, f"{SCRATCH_NAME}_kernel", f"{SCRATCH_NAME}_rw"

OUTCOME_MALFORMED_FIELDCOUNT = "outcome: model-attribution-tracking | sonnet | DELIVERED"
OUTCOME_MALFORMED_SLUG = "outcome: Model Attribution | sonnet | DELIVERED | 0 | none"
OUTCOME_MALFORMED_MODEL = "outcome: model-attribution-tracking | claude sonnet | DELIVERED | 0 | none"
OUTCOME_MALFORMED_VERDICT = "outcome: model-attribution-tracking | sonnet |   | 0 | none"
OUTCOME_MALFORMED_DEFECTS = "outcome: model-attribution-tracking | sonnet | DELIVERED |   | none"
OUTCOME_MALFORMED_NOTES = "outcome: model-attribution-tracking | sonnet | DELIVERED | 0 |   "
# well-formed:
OUTCOME_WELL_FORMED = (
    "outcome: model-attribution-tracking | sonnet | DELIVERED, merge HELD (ent gap) | 0 | "
    "all sec-6 items witnessed; hooks/led.tmpl/design legs built and fixture-verified"
)
# an embedded newline + 4-space indent splitting "attribution" from its own continuation:
OUTCOME_EMBEDDED_NEWLINE = (
    "outcome: doc-legibility-sweep | opus | QUARANTINED, review loop did not converge | "
    "2 (both doc-legibility) | a routine pass over the operational-efficiency\n    retrospective "
    "backlog, similar in scope to the last one"
)
# leading whitespace before the prefix:
OUTCOME_LEADING_WHITESPACE = (
    "  outcome: tsort-port | sonnet | DELIVERED | 0 | trivial binary wrap, no arithmetic surface"
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
    tmpdir = Path(tempfile.mkdtemp(prefix="outcome-intake-validation-fixture-"))
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
    red_case("RED-MALFORMED-FIELDCOUNT", OUTCOME_MALFORMED_FIELDCOUNT, "got 3")
    red_case("RED-MALFORMED-SLUG", OUTCOME_MALFORMED_SLUG, "TASK-SLUG")
    red_case("RED-MALFORMED-MODEL", OUTCOME_MALFORMED_MODEL, "MODEL")
    red_case("RED-MALFORMED-VERDICT", OUTCOME_MALFORMED_VERDICT, "SEAM-VERDICT")
    red_case("RED-MALFORMED-DEFECTS", OUTCOME_MALFORMED_DEFECTS, "DEFECTS-FOUND-AT-SEAM")
    red_case("RED-MALFORMED-NOTES", OUTCOME_MALFORMED_NOTES, "NOTES")

    # -------------------------------------------------------------------------- GREEN-WELL-FORMED
    before = _ledger_row_count(dest)
    r_good = _run(dest, "led", "decision", OUTCOME_WELL_FORMED)
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
                            f"WHERE kind = 'decision' AND statement LIKE 'outcome:%' "
                            f"ORDER BY id DESC LIMIT 1;")
    stored = r_stmt.stdout
    stored_lines = [ln for ln in stored.splitlines() if ln.strip()]
    stored_last = stored_lines[-1] if stored_lines else ""
    byte_exact = OUTCOME_WELL_FORMED.strip() == stored_last
    if not byte_exact:
        failures.append(f"GREEN-WELL-FORMED: stored statement is not byte-exact\n"
                         f"EXPECTED:\n{OUTCOME_WELL_FORMED!r}\nSTORED:\n{stored_last!r}")
    log(f"GREEN-WELL-FORMED: stored statement is byte-exact -- {'PASS' if byte_exact else 'FAIL'}")

    # -------------------------------------------------------------------- GREEN-EMBEDDED-NEWLINE
    before = _ledger_row_count(dest)
    r_nl = _run(dest, "led", "decision", OUTCOME_EMBEDDED_NEWLINE)
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
                              f"WHERE kind = 'decision' AND statement LIKE 'outcome: doc-legibility-sweep%' "
                              f"ORDER BY id DESC LIMIT 1;")
    stored_nl = r_stmt_nl.stdout
    byte_exact_nl = "\n    retrospective backlog" in stored_nl
    if not byte_exact_nl:
        failures.append(f"GREEN-EMBEDDED-NEWLINE: stored statement lost byte fidelity "
                         f"(expected the embedded newline+indent verbatim)\nSTORED:\n{stored_nl!r}")
    log(f"GREEN-EMBEDDED-NEWLINE: stored statement is byte-exact (embedded newline preserved) -- "
        f"{'PASS' if byte_exact_nl else 'FAIL'}")

    # -------------------------------------------------------------------- GREEN-LEADING-WHITESPACE
    before = _ledger_row_count(dest)
    r_ws = _run(dest, "led", "decision", OUTCOME_LEADING_WHITESPACE)
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

    # ------------------------------------------------------------------- GREEN-READABLE-VIA-LEDGER
    r_ledger_current = _psql("-tAc", f"SET ROLE {ROLE}; SELECT statement FROM {SCHEMA}.ledger_current "
                                      f"WHERE kind = 'decision' AND statement LIKE 'outcome: "
                                      f"model-attribution-tracking%';")
    out_lc = r_ledger_current.stdout
    readable = "DELIVERED" in out_lc and "model-attribution-tracking" in out_lc
    if not readable:
        failures.append(f"GREEN-READABLE-VIA-LEDGER: the accepted outcome row is not readable off "
                         f"ledger_current\nSTDOUT:\n{out_lc}\nSTDERR:\n{r_ledger_current.stderr}")
    log(f"GREEN-READABLE-VIA-LEDGER: the accepted well-formed outcome row is readable off "
        f"ledger_current -- {'PASS' if readable else 'FAIL'}")

    if failures:
        print(f"\noutcome-intake-validation fixture: {len(failures)} FAILURE(S) -- scratch "
              f"substrate left standing as evidence:\n  tempdir: {tmpdir}\n  schema:  {SCHEMA} / "
              f"{KERN} / {ROLE} (db {DB}@{PGHOST})")
        for f in failures:
            print(f"\n!! {f}")
        return 1

    _drop_scratch()
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\noutcome-intake-validation fixture: all cases PASS, scratch substrate torn down to "
          f"zero residue (tempdir removed, schema {SCHEMA}/{KERN}/role {ROLE} dropped).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
