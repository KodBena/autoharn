#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-12T06:33:13Z
#   last-change: 2026-07-12T06:40:56Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures — both-polarity live proof for the `resource:` intake-validation fix
(BACKLOG 2026-07-12, work item `resource-intake-validation`; gates/fixture_census.py REGISTRY
entry "resource-intake-validation"). Mirrors seen-red/resource-registry/run_fixtures.py's
scratch-and-drop pattern exactly: a throwaway project directory (via bootstrap/track-work.sh)
plus a throwaway schema pair in the TOY db, torn down after unless a case fails (left standing
as evidence, matching the standing-probe convention every other run_fixtures.py in this repo
uses).

THE DEFECT WITNESSED LIVE (run12, LED_ACTOR=commissioner, 2026-07-12): a maintainer-pasted
`resource:` statement carried an embedded newline from terminal line-wrap mid-word. The write
SUCCEEDED SILENTLY with only 4 of the grammar's 6 fields, and `./pickup`'s RESOURCES section
then further shredded the one row into TWO spurious MALFORMED entries (one of them reporting
`id=experiments`, the tail of the pasted text misread as a row id) because its reader iterated
psql's own physical output lines rather than result rows. THE FIX, in two halves:

  1. bootstrap/templates/led.tmpl now validates a `resource:`-prefixed statement (against a
     WHITESPACE-NORMALIZED copy -- newline runs collapsed to one space) BEFORE the INSERT, and
     refuses loudly (exit nonzero, nothing written) if it does not carry exactly the six-field
     grammar design/USER-BLESSED-TABLE-TEMPLATE.md's "statement grammars" section specifies, or
     if CLASS/TIER fall outside that section's closed vocabularies. The row actually written on
     success is the statement AS TYPED (byte-exact, embedded newline included).
  2. bootstrap/templates/pickup.tmpl's resources() reader now performs the identical newline-
     collapse SERVER-SIDE (a `regexp_replace` in the SELECT itself), so a legitimate embedded
     newline in an ACCEPTED statement renders as one row, not two shredded ones.

CASES (all live subprocess runs of the real `led`/`pickup` verbs against a real scratch
deployment -- never a mock):

  ADOPT                    -- bootstrap/track-work.sh stands up the scratch deployment.
  RED-MALFORMED-FIELDCOUNT -- a 3-field `resource:` statement is REFUSED (nonzero exit) and the
                              ledger row count is witnessed UNCHANGED before/after (atomicity by
                              refusal-before-write).
  RED-MALFORMED-CLASS      -- a well-formed-shaped 6-field statement whose CLASS is not one of
                              the closed vocabulary (solver|service|backend|binary|library) is
                              likewise REFUSED, row count unchanged.
  RED-MALFORMED-TIER       -- a 6-field statement whose TIER is neither `available`,
                              `blessed: <task-shape>`, nor `mandated: <task-shape>` is REFUSED,
                              row count unchanged.
  GREEN-EMBEDDED-NEWLINE   -- run12's own specimen, reproduced verbatim (an embedded newline plus
                              leading indent mid-word, splitting the WHAT-IT-PROVES field from its
                              own continuation) is ACCEPTED (exit 0) -- because after whitespace
                              normalization it carries exactly six fields.
  GREEN-PICKUP-RENDERS     -- `./pickup`'s RESOURCES section shows the accepted row as ONE clean
                              `[available] QEUBO (backend)` block and contains NO "MALFORMED"
                              string anywhere in the RESOURCES section -- the run12 read-side
                              defect, closed.
  GREEN-LEADING-WHITESPACE -- a `resource:` declaration with LEADING whitespace (two spaces
                              before the prefix) is accepted by led AND renders in pickup's
                              RESOURCES section -- the coherence-partner contract proven live:
                              led's validator trigger (leading POSIX [:space:] stripped, then
                              the `resource:` prefix) and pickup's SQL filter
                              (`statement ~ '^[[:space:]]*resource:'`) admit the IDENTICAL
                              statement set, so nothing led validates can vanish from the read
                              side (the incoherence a position-0 LIKE filter used to permit).

Scratch-only: schema/kern/role derived from a throwaway name (`SCRATCH_NAME` below, distinct
from resource-registry's own `rrfixture`) in the TOY db (192.168.122.1) plus a throwaway
tempdir -- both dropped/removed after, UNLESS a case FAILS (left standing as evidence,
kernel/fixtures/s22_work_item_fixture.py's own convention).

Usage: python3 seen-red/resource-intake-validation/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TRACK_WORK = REPO / "bootstrap" / "track-work.sh"
PGHOST, DB = "192.168.122.1", "toy"
SCRATCH_NAME = "rivfixture"
SCHEMA, KERN, ROLE = SCRATCH_NAME, f"{SCRATCH_NAME}_kernel", f"{SCRATCH_NAME}_rw"

# run12's own specimen, reproduced verbatim (an embedded newline + 4-space indent splitting
# "maintainer's" from "experiments", exactly as the maintainer's terminal wrapped it):
RESOURCE_EMBEDDED_NEWLINE = (
    "resource: QEUBO | backend | http://192.168.122.68:8764 | preference-optimization result "
    "for this maintainer's\n    experiments | auth via /auth/register then /auth/token; "
    "interactive docs at /docs; six /qeubo/experiment* routes | available"
)
RESOURCE_MALFORMED_FIELDCOUNT = "resource: X | solver | reach-only"
RESOURCE_MALFORMED_CLASS = "resource: X | notaclass | r | p | g | available"
RESOURCE_MALFORMED_TIER = "resource: X | solver | r | p | g | sometier"
# leading whitespace before the prefix -- the coherence-partner case: led's validator strips
# leading [:space:] before its `resource:` trigger, and pickup's SQL filter admits the same via
# `~ '^[[:space:]]*resource:'`; both sides must see this statement or the two mechanisms have
# diverged on what "a resource declaration" is:
RESOURCE_LEADING_WHITESPACE = (
    "  resource: tsort | binary | binary:tsort | a topological order over a DAG, or a cycle "
    "if none exists | use for simple pairwise precedence with no arithmetic or resource "
    "dimension | available"
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
    tmpdir = Path(tempfile.mkdtemp(prefix="resource-intake-validation-fixture-"))
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

    # ------------------------------------------------------------- RED-MALFORMED-FIELDCOUNT
    before = _ledger_row_count(dest)
    r_bad = _run(dest, "led", "decision", RESOURCE_MALFORMED_FIELDCOUNT)
    after = _ledger_row_count(dest)
    refused = r_bad.returncode != 0 and "REFUSED" in r_bad.stderr and "got 3" in r_bad.stderr
    unchanged = before == after
    ok = refused and unchanged
    if not ok:
        failures.append(f"RED-MALFORMED-FIELDCOUNT: exit={r_bad.returncode} refused={refused} "
                         f"before={before} after={after}\nSTDERR:\n{r_bad.stderr}")
    log(f"RED-MALFORMED-FIELDCOUNT: exit={r_bad.returncode} refused={refused} "
        f"row-count before={before} after={after} (unchanged={unchanged}) -- "
        f"{'PASS' if ok else 'FAIL'}")
    log("--- led decision (malformed field-count) stderr ---")
    log(r_bad.stderr.strip())
    log("--- end stderr ---")

    # ------------------------------------------------------------------ RED-MALFORMED-CLASS
    before = _ledger_row_count(dest)
    r_bad_cls = _run(dest, "led", "decision", RESOURCE_MALFORMED_CLASS)
    after = _ledger_row_count(dest)
    refused = r_bad_cls.returncode != 0 and "REFUSED" in r_bad_cls.stderr and "CLASS" in r_bad_cls.stderr
    unchanged = before == after
    ok = refused and unchanged
    if not ok:
        failures.append(f"RED-MALFORMED-CLASS: exit={r_bad_cls.returncode} refused={refused} "
                         f"before={before} after={after}\nSTDERR:\n{r_bad_cls.stderr}")
    log(f"RED-MALFORMED-CLASS: exit={r_bad_cls.returncode} refused={refused} "
        f"row-count before={before} after={after} (unchanged={unchanged}) -- "
        f"{'PASS' if ok else 'FAIL'}")

    # ------------------------------------------------------------------- RED-MALFORMED-TIER
    before = _ledger_row_count(dest)
    r_bad_tier = _run(dest, "led", "decision", RESOURCE_MALFORMED_TIER)
    after = _ledger_row_count(dest)
    refused = r_bad_tier.returncode != 0 and "REFUSED" in r_bad_tier.stderr and "TIER" in r_bad_tier.stderr
    unchanged = before == after
    ok = refused and unchanged
    if not ok:
        failures.append(f"RED-MALFORMED-TIER: exit={r_bad_tier.returncode} refused={refused} "
                         f"before={before} after={after}\nSTDERR:\n{r_bad_tier.stderr}")
    log(f"RED-MALFORMED-TIER: exit={r_bad_tier.returncode} refused={refused} "
        f"row-count before={before} after={after} (unchanged={unchanged}) -- "
        f"{'PASS' if ok else 'FAIL'}")

    # -------------------------------------------------------------------- GREEN-EMBEDDED-NEWLINE
    before = _ledger_row_count(dest)
    r_good = _run(dest, "led", "decision", RESOURCE_EMBEDDED_NEWLINE)
    after = _ledger_row_count(dest)
    accepted = r_good.returncode == 0
    grew = after == before + 1
    ok = accepted and grew
    if not ok:
        failures.append(f"GREEN-EMBEDDED-NEWLINE: exit={r_good.returncode} accepted={accepted} "
                         f"before={before} after={after}\nSTDERR:\n{r_good.stderr}")
    log(f"GREEN-EMBEDDED-NEWLINE: exit={r_good.returncode} accepted={accepted} "
        f"row-count before={before} after={after} (grew-by-one={grew}) -- "
        f"{'PASS' if ok else 'FAIL'}")

    # Byte-fidelity check: the row actually written carries the embedded newline verbatim, not
    # a normalized copy (led.tmpl's own stated contract -- normalization is validation-only
    # scratch, never persisted).
    r_stmt = _psql("-tAc", f"SET ROLE {ROLE}; SELECT statement FROM {SCHEMA}.ledger "
                            f"WHERE kind = 'decision' AND statement LIKE 'resource:%' "
                            f"ORDER BY id DESC LIMIT 1;")
    stored = r_stmt.stdout
    byte_exact = "\n    experiments" in stored
    if not byte_exact:
        failures.append(f"GREEN-EMBEDDED-NEWLINE: stored statement lost byte fidelity "
                         f"(expected the embedded newline+indent verbatim)\nSTORED:\n{stored!r}")
    log(f"GREEN-EMBEDDED-NEWLINE: stored statement is byte-exact (embedded newline preserved) -- "
        f"{'PASS' if byte_exact else 'FAIL'}")

    # ------------------------------------------------------------------------ GREEN-PICKUP-RENDERS
    r_pickup = _run(dest, "pickup")
    out = r_pickup.stdout
    start = out.find("### SECTION: RESOURCES")
    end = out.find("### SECTION:", start + 1)
    section_text = out[start:end if end != -1 else None].strip() if start != -1 else ""
    renders_clean = ("[available] QEUBO (backend)" in section_text
                      and "MALFORMED" not in section_text
                      and "id=experiments" not in section_text)
    if not renders_clean:
        failures.append(f"GREEN-PICKUP-RENDERS: RESOURCES section did not render cleanly\n"
                         f"{section_text}")
    log(f"GREEN-PICKUP-RENDERS: RESOURCES section renders '[available] QEUBO (backend)' with no "
        f"MALFORMED entries -- {'PASS' if renders_clean else 'FAIL'}")
    log("--- pickup RESOURCES section (verbatim) ---")
    log(section_text)
    transcript.append(section_text)
    log("--- end pickup RESOURCES section ---")

    # -------------------------------------------------------------- GREEN-LEADING-WHITESPACE
    before = _ledger_row_count(dest)
    r_ws = _run(dest, "led", "decision", RESOURCE_LEADING_WHITESPACE)
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

    # ...and the SAME statement must render in pickup's RESOURCES section -- the read side's
    # filter admitting exactly what the write side validated (coherence-partner contract).
    r_pickup_ws = _run(dest, "pickup")
    out_ws = r_pickup_ws.stdout
    start = out_ws.find("### SECTION: RESOURCES")
    end = out_ws.find("### SECTION:", start + 1)
    section_ws = out_ws[start:end if end != -1 else None].strip() if start != -1 else ""
    renders = ("[available] tsort (binary)" in section_ws
                and "MALFORMED" not in section_ws)
    if not renders:
        failures.append(f"GREEN-LEADING-WHITESPACE: pickup RESOURCES did not render the "
                         f"leading-whitespace declaration\n{section_ws}")
    log(f"GREEN-LEADING-WHITESPACE: pickup RESOURCES renders '[available] tsort (binary)' with "
        f"no MALFORMED entries -- {'PASS' if renders else 'FAIL'}")
    log("--- pickup RESOURCES section after leading-whitespace declaration (verbatim) ---")
    log(section_ws)
    transcript.append(section_ws)
    log("--- end pickup RESOURCES section ---")

    if failures:
        print(f"\nresource-intake-validation fixture: {len(failures)} FAILURE(S) -- scratch "
              f"substrate left standing as evidence:\n  tempdir: {tmpdir}\n  schema:  {SCHEMA} / "
              f"{KERN} / {ROLE} (db {DB}@{PGHOST})")
        for f in failures:
            print(f"\n!! {f}")
        return 1

    _drop_scratch()
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\nresource-intake-validation fixture: all cases PASS, scratch substrate torn down to "
          f"zero residue (tempdir removed, schema {SCHEMA}/{KERN}/role {ROLE} dropped).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
