#!/usr/bin/env python3
"""run_fixtures — both-polarity live proof for ORCH-SPEC-RESOURCE-REGISTRY.md stage 1
(design/ORCH-SPEC-RESOURCE-REGISTRY.md §8's own witness plan; gates/fixture_census.py REGISTRY
entry "resource-registry"). Mirrors seen-red/track-work/run_fixtures.py's scratch-and-drop
pattern exactly: a throwaway project directory (via bootstrap/track-work.sh, the standing
work-tracking scaffold) plus a throwaway schema pair in the TOY db, torn down after unless a
case fails (left standing as evidence, matching the standing-probe convention).

CASES (all live subprocess runs of the real `led`/`pickup` verbs against a real scratch
deployment -- never a mock):

  ADOPT               -- bootstrap/track-work.sh stands up the scratch deployment (deployment.json
                        + the seven verb shims + the reviewer/commissioner principals).
  RESOURCES-DECLARED  -- three `./led decision "resource: ..."` calls, one per TIER (available,
                        blessed: <task-shape>, mandated: <task-shape>) -- the spec's §2 statement
                        convention, exercised live.
  PICKUP-TIER-SORTED  -- `./pickup` shows a RESOURCES section (this fixture's own proof that
                        bootstrap/templates/pickup.tmpl's `resources()` function, added this
                        session, actually parses the convention) with the mandated declaration's
                        block printed before blessed's, before available's -- spec §3's "mandated
                        first" ordering, checked by STRING POSITION in the real captured stdout,
                        not asserted.
  RED-REVIEW-GAP      -- a mandated-shape work item (the OR-Tools-CP-SAT resource's own
                        hyperparameter-enumeration task shape) is opened, claimed, and closed
                        --witness citing the evidence shape, ALL as the obligated `author`
                        principal, with `./led obligate` run first (spec §4 stage 1's convention)
                        and NO countersigning review yet -- `./led review-gap` must show every one
                        of author's outstanding rows as debt (the documented KNOWN OVER-CATCH:
                        once obliged, review_gap counts every uncountersigned row that principal
                        ever writes, not only the mandated-shape one -- led.tmpl's own `led
                        obligate` comment names this; this fixture demonstrates it rather than
                        hiding it).
  GREEN-REVIEW-CLEAN  -- every outstanding row is countersigned by a DISTINCT principal
                        (LED_ACTOR=reviewer), independence=self-review (this scratch deployment
                        is UNWIRED -- track-work.sh provisions no stamp secret, so
                        technical/managerial/financial independence would be refused by the
                        kernel's own stamp-distinctness CHECK; self-review is the honest value
                        here, same as any unwired deployment), the mandated-shape CLOSE row's
                        review explicitly citing the evidence shape (the committed declarative
                        model file this fixture fabricates) -- `./led review-gap` (a raw `SELECT
                        * FROM review_gap`) must then read back "(0 rows)"; `./pickup`'s own
                        REVIEW-DEBT section (the friendlier "(no review debt outstanding)"
                        wording) reads the identical view.

Scratch-only: schema/kern/role derived from a throwaway name (`SCRATCH_NAME` below, chosen not
to collide with engine/targets.py's curated registry or scratch-naming conventions) in the TOY
db (192.168.122.1) plus a throwaway tempdir -- both dropped/removed after, UNLESS a case FAILS
(left standing as evidence, kernel/fixtures/s22_work_item_fixture.py's own convention, reused
verbatim by seen-red/track-work/run_fixtures.py).

Usage: python3 seen-red/resource-registry/run_fixtures.py
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
SCRATCH_NAME = "rrfixture"
SCHEMA, KERN, ROLE = SCRATCH_NAME, f"{SCRATCH_NAME}_kernel", f"{SCRATCH_NAME}_rw"

RESOURCE_AVAILABLE = (
    "resource: redis | service | tcp://localhost:6379 | ephemeral key/value cache or queue "
    "| use for ephemeral state/coordination only, never durable ledger data | available"
)
RESOURCE_BLESSED = (
    "resource: cvxpy | library | import:cvxpy | global optimum proof for convex allocation "
    "problems | use for convex, continuous resource-allocation problems; not for "
    "combinatorial/integer structure | blessed: convex-allocation"
)
RESOURCE_MANDATED = (
    "resource: OR-Tools-CP-SAT | library | import:ortools.sat.python.cp_model | finite "
    "enumeration -> exact hyperparameter search proof | use for hyperparameter enumeration "
    "over heuristic search; discharge evidence = committed declarative model file "
    "models/hp_enum_model.py | mandated: hyperparameter-enumeration"
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


def main() -> int:
    failures: list[str] = []
    transcript: list[str] = []

    def log(line: str) -> None:
        print(line)
        transcript.append(line)

    _drop_scratch()
    tmpdir = Path(tempfile.mkdtemp(prefix="resource-registry-fixture-"))
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

    # ---------------------------------------------------------------- RESOURCES-DECLARED
    decl_results = []
    for label, stmt in (("available", RESOURCE_AVAILABLE), ("blessed", RESOURCE_BLESSED),
                         ("mandated", RESOURCE_MANDATED)):
        r = _run(dest, "led", "decision", stmt)
        decl_results.append((label, r.returncode == 0, r))
        log(f"RESOURCES-DECLARED ({label}): exit={r.returncode} -- "
            f"{'PASS' if r.returncode == 0 else 'FAIL'}")
        if r.returncode != 0:
            failures.append(f"RESOURCES-DECLARED ({label}): exit={r.returncode}\n{r.stderr}")

    # ---------------------------------------------------------------- PICKUP-TIER-SORTED
    r_pickup = _run(dest, "pickup")
    out = r_pickup.stdout
    has_section = "SECTION: RESOURCES" in out
    idx_mandated = out.find("OR-Tools-CP-SAT")
    idx_blessed = out.find("cvxpy")
    idx_available = out.find("redis")
    tier_sorted = has_section and -1 < idx_mandated < idx_blessed < idx_available
    if not tier_sorted:
        failures.append(f"PICKUP-TIER-SORTED: has_section={has_section} "
                         f"idx(mandated,blessed,available)=({idx_mandated},{idx_blessed},"
                         f"{idx_available})\nSTDOUT:\n{out}")
    log(f"PICKUP-TIER-SORTED: exit={r_pickup.returncode} RESOURCES section present={has_section} "
        f"order mandated<blessed<available={idx_mandated < idx_blessed < idx_available if -1 not in (idx_mandated, idx_blessed, idx_available) else False} "
        f"-- {'PASS' if tier_sorted else 'FAIL'}")
    log("--- pickup RESOURCES section (verbatim) ---")
    if has_section:
        start = out.find("### SECTION: RESOURCES")
        end = out.find("### SECTION:", start + 1)
        section_text = out[start:end if end != -1 else None].strip()
        log(section_text)
        transcript.append(section_text)
    log("--- end pickup RESOURCES section ---")

    # ---------------------------------------------------------------- RED-REVIEW-GAP
    r_obligate = _run(dest, "led", "obligate", "mandated-tool-review", "commissioner", "author")
    log(f"RED-REVIEW-GAP: led obligate exit={r_obligate.returncode} -- "
        f"{'PASS' if r_obligate.returncode == 0 else 'FAIL'}")
    if r_obligate.returncode != 0:
        failures.append(f"RED-REVIEW-GAP: led obligate failed\n{r_obligate.stderr}")

    r_open = _run(dest, "led", "work", "open", "hp-enum", "Hyperparameter enumeration via OR-Tools CP-SAT")
    r_claim = _run(dest, "led", "work", "claim", "hp-enum")
    r_close = _run(dest, "led", "work", "close", "hp-enum", "shipped", "--witness",
                   "models/hp_enum_model.py (committed declarative model file -- the evidence "
                   "shape named on the OR-Tools-CP-SAT resource declaration, TIER=mandated: "
                   "hyperparameter-enumeration)")
    work_ok = r_open.returncode == 0 and r_claim.returncode == 0 and r_close.returncode == 0
    if not work_ok:
        failures.append(f"RED-REVIEW-GAP: work open/claim/close exit="
                         f"{r_open.returncode}/{r_claim.returncode}/{r_close.returncode}\n"
                         f"{r_open.stderr}\n{r_claim.stderr}\n{r_close.stderr}")
    log(f"RED-REVIEW-GAP: work open/claim/close exit={r_open.returncode}/{r_claim.returncode}/"
        f"{r_close.returncode} -- {'PASS' if work_ok else 'FAIL'}")

    r_gap_red = _run(dest, "led", "review-gap")
    gap_red_out = r_gap_red.stdout
    # `led review-gap` is a raw `SELECT * FROM review_gap` (bootstrap/templates/led.tmpl) --
    # psql's own table format prints "(0 rows)" for an empty result and "(N rows)" (N>0) with a
    # real table above it otherwise. The friendlier "(no review debt outstanding)" wording is
    # `./pickup`'s own REVIEW-DEBT section, not this raw verb -- checked against the actual
    # substring psql prints, not an invented one.
    gap_shows_debt = r_gap_red.returncode == 0 and "(0 rows)" not in gap_red_out
    if not gap_shows_debt:
        failures.append(f"RED-REVIEW-GAP: review-gap did not show debt\n{gap_red_out}")
    log(f"RED-REVIEW-GAP: led review-gap shows outstanding debt -- "
        f"{'PASS' if gap_shows_debt else 'FAIL'}")
    log("--- led review-gap (RED, before any countersign) ---")
    log(gap_red_out.strip())
    log("--- end led review-gap (RED) ---")

    # ---------------------------------------------------------------- GREEN-REVIEW-CLEAN
    # Fetch every outstanding row id straight from the DB (the known over-catch means this
    # includes the three resource declarations too, not only hp-enum's three work_* rows --
    # documented in this file's own docstring and in user-guide/USER-BLESSED-TABLE-TEMPLATE.md's
    # "mandated-tier review convention" section, not hidden here).
    r_ids = _psql("-tAc", f"SET ROLE {ROLE}; SELECT id FROM {SCHEMA}.review_gap ORDER BY id;")
    # -t -A echoes one leading "SET" line for the preceding `SET ROLE` statement (the same
    # convention bootstrap/templates/pickup.tmpl's own _psql_tuples() docstring names) -- filter
    # to digit-only lines rather than dropping a fixed line count, so this stays correct even if
    # a future edit adds/removes a leading statement.
    outstanding_ids = [ln.strip() for ln in r_ids.stdout.strip().splitlines() if ln.strip().isdigit()]
    log(f"GREEN-REVIEW-CLEAN: {len(outstanding_ids)} outstanding row(s) to countersign: {outstanding_ids}")

    review_failures = []
    for row_id in outstanding_ids:
        # cite the evidence shape explicitly for the mandated-shape work item's own rows
        # (work_opened/work_claimed/work_closed for hp-enum); a plain administrative note for
        # the rest (the resource declarations themselves are not mandated-shape work).
        r_kind = _psql("-tAc", f"SET ROLE {ROLE}; SELECT kind FROM {SCHEMA}.ledger WHERE id = {row_id};")
        kind = r_kind.stdout.strip()
        if kind.startswith("work_"):
            basis = (f"evidence shape present: models/hp_enum_model.py (committed declarative "
                     f"model file), citing the OR-Tools-CP-SAT resource declaration's "
                     f"mandated: hyperparameter-enumeration TIER -- discipline followed")
        else:
            basis = "reviewed; not a mandated-shape discharge row, no evidence-shape citation required"
        r_rev = _run(dest, "led", "review", row_id, "attest", "self-review", basis,
                     env={"LED_ACTOR": "reviewer"})
        if r_rev.returncode != 0:
            review_failures.append(f"review of row {row_id} ({kind}) failed: {r_rev.stderr}")

    if review_failures:
        failures.append("GREEN-REVIEW-CLEAN: " + "; ".join(review_failures))
    log(f"GREEN-REVIEW-CLEAN: countersigned {len(outstanding_ids) - len(review_failures)}/"
        f"{len(outstanding_ids)} outstanding rows -- {'PASS' if not review_failures else 'FAIL'}")

    r_gap_green = _run(dest, "led", "review-gap")
    gap_green_out = r_gap_green.stdout
    gap_clean = r_gap_green.returncode == 0 and "(0 rows)" in gap_green_out
    if not gap_clean:
        failures.append(f"GREEN-REVIEW-CLEAN: review-gap not clean after countersigning\n{gap_green_out}")
    log(f"GREEN-REVIEW-CLEAN: led review-gap clean after countersigning -- "
        f"{'PASS' if gap_clean else 'FAIL'}")
    log("--- led review-gap (GREEN, after countersigning every outstanding row) ---")
    log(gap_green_out.strip())
    log("--- end led review-gap (GREEN) ---")

    if failures:
        print(f"\nresource-registry fixture: {len(failures)} FAILURE(S) -- scratch substrate "
              f"left standing as evidence:\n  tempdir: {tmpdir}\n  schema:  {SCHEMA} / {KERN} / "
              f"{ROLE} (db {DB}@{PGHOST})")
        for f in failures:
            print(f"\n!! {f}")
        return 1

    _drop_scratch()
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\nresource-registry fixture: all cases PASS, scratch substrate torn down to zero "
          f"residue (tempdir removed, schema {SCHEMA}/{KERN}/role {ROLE} dropped).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
