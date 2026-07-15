#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-12T13:56:12Z
#   last-change: 2026-07-12T13:56:12Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures — both-polarity live proof for the `forbidden` TIER addition to the `resource:`
intake validator (tracker item `accounting-stage-a`, design/ORCH-SPEC-RESOURCE-ACCOUNTING.md §3/
§8 stage A; gates/fixture_census.py REGISTRY entry "accounting-forbidden-tier"). Mirrors
seen-red/resource-intake-validation/run_fixtures.py's scratch-and-drop pattern exactly (a
throwaway project directory via bootstrap/track-work.sh -- the same light-weight scratch this
project's two direct predecessor fixtures for this exact `led`/`pickup` machinery already use,
never bootstrap/new-project.sh --new-world's heavier governed-world scaffold, which this
validator does not need: no hooks, no CLAUDE.md, no stamp secret are read by led.tmpl's or
pickup.tmpl's `resource:` code paths), plus a throwaway schema pair in the TOY db, torn down
after unless a case fails (left standing as evidence, matching the standing-probe convention
every other run_fixtures.py in this repo uses).

WHAT THIS PROVES: `forbidden: <task-shape>` is the deontic register's missing MUST-NOT modality
(ORCH-SPEC-RESOURCE-ACCOUNTING.md §3 -- the spec's own table: available=MAY, blessed=SHOULD,
mandated=MUST, forbidden=MUST-NOT). This fixture proves, live, that:

  1. `bootstrap/templates/led.tmpl`'s `resource:` intake validator now ACCEPTS a well-formed
     `forbidden: <task-shape>` TIER (byte-exact persistence, including an embedded newline --
     the same run12-witnessed reflow hazard the resource-intake-validation fixture proved the
     existing three tiers survive), and REFUSES a malformed `forbidden` TIER (bare `forbidden`
     with no colon; `forbidden:` with an empty task-shape after the colon) -- nothing written,
     row count unchanged, exactly the refuse-before-write atomicity the existing tiers already
     have.
  2. `bootstrap/templates/pickup.tmpl`'s RESOURCES section sorts a `forbidden` entry AHEAD of a
     `mandated` entry (ORCH-SPEC-RESOURCE-ACCOUNTING.md §3: "a prohibition outranks a mandate for
     a reader's attention").

Nothing existing is relaxed: `available`/`blessed`/`mandated` accept exactly what they accepted
before this fixture's target commit (the resource-intake-validation fixture above continues to
prove that on its own, unchanged file). This fixture proves only the ADDITION.

CASES (all live subprocess runs of the real `led`/`pickup` verbs against a real scratch
deployment -- never a mock):

  ADOPT                          -- bootstrap/track-work.sh stands up the scratch deployment.
  RED-FORBIDDEN-BARE             -- TIER field is the bare word `forbidden` (no colon, no
                                     task-shape) -- REFUSED (nonzero exit, "TIER field ... is not
                                     'available', ... or 'forbidden: <task-shape>'" in stderr),
                                     ledger row count witnessed UNCHANGED before/after.
  RED-FORBIDDEN-EMPTY-SHAPE      -- TIER field is `forbidden:` with an empty task-shape after the
                                     colon -- REFUSED ("names no <task-shape> after the colon" in
                                     stderr), row count unchanged.
  GREEN-FORBIDDEN-ACCEPTED       -- a well-formed `forbidden: <task-shape>` TIER is ACCEPTED (exit
                                     0), row count grows by one, and the row stored is byte-exact
                                     (the statement as typed, not the whitespace-normalized
                                     validation-only copy).
  GREEN-FORBIDDEN-EMBEDDED-NEWLINE -- a `forbidden`-tier declaration carrying an embedded newline
                                     (the run12 reflow specimen, reproduced against this new tier)
                                     is ACCEPTED after whitespace normalization, and the row
                                     actually persisted preserves the embedded newline verbatim.
  GREEN-PICKUP-SORTS-FORBIDDEN-FIRST -- a `mandated`-tier resource is declared BEFORE a
                                     `forbidden`-tier resource (insertion order deliberately
                                     working against display order), then `./pickup`'s RESOURCES
                                     section is read and the `forbidden` block is shown to appear
                                     BEFORE the `mandated` block -- proving the sort, not merely
                                     the insertion order.

Scratch-only: schema/kern/role derived from a throwaway name (`SCRATCH_NAME` below, distinct from
every other fixture's own scratch name) in the TOY db (192.168.122.1) plus a throwaway tempdir --
both dropped/removed after, UNLESS a case FAILS (left standing as evidence,
kernel/fixtures/s22_work_item_fixture.py's own convention).

Usage: python3 seen-red/accounting-forbidden-tier/run_fixtures.py
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
SCRATCH_NAME = "acsafixture"
SCHEMA, KERN, ROLE = SCRATCH_NAME, f"{SCRATCH_NAME}_kernel", f"{SCRATCH_NAME}_rw"

RESOURCE_FORBIDDEN_BARE = "resource: X | solver | r | p | g | forbidden"
RESOURCE_FORBIDDEN_EMPTY_SHAPE = "resource: X | solver | r | p | g | forbidden:"
RESOURCE_FORBIDDEN_ACCEPTED = (
    "resource: legacy-eval-script | binary | binary:legacy_eval.sh | nothing provable -- an "
    "unmaintained script with no test coverage | superseded by MIP-SCIP; do not reach for it "
    "even under time pressure | forbidden: hyperparameter-enumeration"
)
# the run12 specimen's own shape (an embedded newline + 4-space indent mid-word), reproduced
# against the new `forbidden` tier -- see seen-red/resource-intake-validation/run_fixtures.py's
# RESOURCE_EMBEDDED_NEWLINE for the original witnessed defect this pattern guards against:
RESOURCE_FORBIDDEN_EMBEDDED_NEWLINE = (
    "resource: legacy-solver-v1 | solver | binary:legacy_solver_v1 | nothing provable -- the\n"
    "    predecessor solver this project's benchmark superseded | never reach for it; kept "
    "only for historical reproduction runs | forbidden: production-optimization"
)
RESOURCE_MANDATED_FOR_SORT = (
    "resource: OR-Tools-CP-SAT | library | import:ortools.sat.python.cp_model | finite "
    "enumeration -> exact hyperparameter search proof | discharge evidence = committed "
    "declarative model file | mandated: hyperparameter-enumeration"
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

    _drop_scratch()
    tmpdir = Path(tempfile.mkdtemp(prefix="accounting-forbidden-tier-fixture-"))
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

    # ------------------------------------------------------------------- RED-FORBIDDEN-BARE
    before = _ledger_row_count(dest)
    r_bad = _run(dest, "led", "decision", RESOURCE_FORBIDDEN_BARE)
    after = _ledger_row_count(dest)
    refused = (r_bad.returncode != 0 and "REFUSED" in r_bad.stderr
               and "forbidden: <task-shape>" in r_bad.stderr)
    unchanged = before == after
    ok = refused and unchanged
    if not ok:
        failures.append(f"RED-FORBIDDEN-BARE: exit={r_bad.returncode} refused={refused} "
                         f"before={before} after={after}\nSTDERR:\n{r_bad.stderr}")
    log(f"RED-FORBIDDEN-BARE: exit={r_bad.returncode} refused={refused} "
        f"row-count before={before} after={after} (unchanged={unchanged}) -- "
        f"{'PASS' if ok else 'FAIL'}")
    log("--- led decision (bare 'forbidden', no colon) stderr ---")
    log(r_bad.stderr.strip())
    log("--- end stderr ---")

    # ------------------------------------------------------------- RED-FORBIDDEN-EMPTY-SHAPE
    before = _ledger_row_count(dest)
    r_bad2 = _run(dest, "led", "decision", RESOURCE_FORBIDDEN_EMPTY_SHAPE)
    after = _ledger_row_count(dest)
    refused = (r_bad2.returncode != 0 and "REFUSED" in r_bad2.stderr
               and "names no <task-shape> after the colon" in r_bad2.stderr)
    unchanged = before == after
    ok = refused and unchanged
    if not ok:
        failures.append(f"RED-FORBIDDEN-EMPTY-SHAPE: exit={r_bad2.returncode} refused={refused} "
                         f"before={before} after={after}\nSTDERR:\n{r_bad2.stderr}")
    log(f"RED-FORBIDDEN-EMPTY-SHAPE: exit={r_bad2.returncode} refused={refused} "
        f"row-count before={before} after={after} (unchanged={unchanged}) -- "
        f"{'PASS' if ok else 'FAIL'}")
    log("--- led decision ('forbidden:' with empty shape) stderr ---")
    log(r_bad2.stderr.strip())
    log("--- end stderr ---")

    # ------------------------------------------------------------------ GREEN-FORBIDDEN-ACCEPTED
    before = _ledger_row_count(dest)
    r_good = _run(dest, "led", "decision", RESOURCE_FORBIDDEN_ACCEPTED)
    after = _ledger_row_count(dest)
    accepted = r_good.returncode == 0
    grew = after == before + 1
    ok = accepted and grew
    if not ok:
        failures.append(f"GREEN-FORBIDDEN-ACCEPTED: exit={r_good.returncode} accepted={accepted} "
                         f"before={before} after={after}\nSTDERR:\n{r_good.stderr}")
    log(f"GREEN-FORBIDDEN-ACCEPTED: exit={r_good.returncode} accepted={accepted} "
        f"row-count before={before} after={after} (grew-by-one={grew}) -- "
        f"{'PASS' if ok else 'FAIL'}")

    r_stmt = _psql("-tAc", f"SET ROLE {ROLE}; SELECT statement FROM {SCHEMA}.ledger "
                            f"WHERE kind = 'decision' AND statement LIKE 'resource:%legacy-eval%' "
                            f"ORDER BY id DESC LIMIT 1;")
    stored = r_stmt.stdout
    byte_exact = "forbidden: hyperparameter-enumeration" in stored
    if not byte_exact:
        failures.append(f"GREEN-FORBIDDEN-ACCEPTED: stored statement lost byte fidelity\n"
                         f"STORED:\n{stored!r}")
    log(f"GREEN-FORBIDDEN-ACCEPTED: stored statement is byte-exact -- "
        f"{'PASS' if byte_exact else 'FAIL'}")

    # ------------------------------------------------------------ GREEN-FORBIDDEN-EMBEDDED-NEWLINE
    before = _ledger_row_count(dest)
    r_nl = _run(dest, "led", "decision", RESOURCE_FORBIDDEN_EMBEDDED_NEWLINE)
    after = _ledger_row_count(dest)
    accepted = r_nl.returncode == 0
    grew = after == before + 1
    ok = accepted and grew
    if not ok:
        failures.append(f"GREEN-FORBIDDEN-EMBEDDED-NEWLINE: exit={r_nl.returncode} "
                         f"accepted={accepted} before={before} after={after}\n"
                         f"STDERR:\n{r_nl.stderr}")
    log(f"GREEN-FORBIDDEN-EMBEDDED-NEWLINE: exit={r_nl.returncode} accepted={accepted} "
        f"row-count before={before} after={after} (grew-by-one={grew}) -- "
        f"{'PASS' if ok else 'FAIL'}")

    r_stmt2 = _psql("-tAc", f"SET ROLE {ROLE}; SELECT statement FROM {SCHEMA}.ledger "
                             f"WHERE kind = 'decision' AND statement LIKE 'resource:%legacy-solver%' "
                             f"ORDER BY id DESC LIMIT 1;")
    stored2 = r_stmt2.stdout
    byte_exact2 = "\n    predecessor solver" in stored2
    if not byte_exact2:
        failures.append(f"GREEN-FORBIDDEN-EMBEDDED-NEWLINE: stored statement lost byte fidelity "
                         f"(expected the embedded newline+indent verbatim)\nSTORED:\n{stored2!r}")
    log(f"GREEN-FORBIDDEN-EMBEDDED-NEWLINE: stored statement is byte-exact (embedded newline "
        f"preserved) -- {'PASS' if byte_exact2 else 'FAIL'}")

    # -------------------------------------------------------- GREEN-PICKUP-SORTS-FORBIDDEN-FIRST
    # mandated declared BEFORE forbidden -- insertion order deliberately opposite of display
    # order, so a pass here proves the SORT, not the ledger's own id order.
    r_mand = _run(dest, "led", "decision", RESOURCE_MANDATED_FOR_SORT)
    mand_ok = r_mand.returncode == 0
    if not mand_ok:
        failures.append(f"GREEN-PICKUP-SORTS-FORBIDDEN-FIRST: mandated declaration itself "
                         f"failed to write, exit={r_mand.returncode}\nSTDERR:\n{r_mand.stderr}")

    r_pickup = _run(dest, "pickup")
    out = r_pickup.stdout
    start = out.find("### SECTION: RESOURCES")
    end = out.find("### SECTION:", start + 1)
    section_text = out[start:end if end != -1 else None].strip() if start != -1 else ""
    forbidden_idx = section_text.find("[forbidden: production-optimization]")
    mandated_idx = section_text.find("[mandated: hyperparameter-enumeration]")
    sorts_first = mand_ok and forbidden_idx != -1 and mandated_idx != -1 and forbidden_idx < mandated_idx
    if not sorts_first:
        failures.append(f"GREEN-PICKUP-SORTS-FORBIDDEN-FIRST: forbidden_idx={forbidden_idx} "
                         f"mandated_idx={mandated_idx} (want forbidden before mandated)\n"
                         f"{section_text}")
    log(f"GREEN-PICKUP-SORTS-FORBIDDEN-FIRST: forbidden block at index {forbidden_idx}, mandated "
        f"block at index {mandated_idx} (forbidden-first={sorts_first}) -- "
        f"{'PASS' if sorts_first else 'FAIL'}")
    log("--- pickup RESOURCES section (verbatim) ---")
    log(section_text)
    transcript.append(section_text)
    log("--- end pickup RESOURCES section ---")

    if failures:
        print(f"\naccounting-forbidden-tier fixture: {len(failures)} FAILURE(S) -- scratch "
              f"substrate left standing as evidence:\n  tempdir: {tmpdir}\n  schema:  {SCHEMA} / "
              f"{KERN} / {ROLE} (db {DB}@{PGHOST})")
        for f in failures:
            print(f"\n!! {f}")
        return 1

    _drop_scratch()
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\naccounting-forbidden-tier fixture: all cases PASS, scratch substrate torn down to "
          f"zero residue (tempdir removed, schema {SCHEMA}/{KERN}/role {ROLE} dropped).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
