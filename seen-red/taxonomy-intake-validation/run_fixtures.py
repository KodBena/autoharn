#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-12T13:58:46Z
#   last-change: 2026-07-12T13:58:46Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures — both-polarity live proof for the `taxon:`/`interface:` intake-validation
feature (tracker item `taxonomy-stage-a`, design/ORCH-SPEC-TASK-TAXONOMY.md §3/§7 Stage A;
gates/fixture_census.py REGISTRY entry "taxonomy-intake-validation"). Mirrors
seen-red/resource-intake-validation/run_fixtures.py's and
seen-red/estimate-intake-validation/run_fixtures.py's scratch-and-drop pattern exactly: a
throwaway project directory (via bootstrap/track-work.sh, which derives its schema/kern/role the
same way `bootstrap/new-project.sh --new-world` does -- track-work.sh's own module docstring
states this explicitly) plus a throwaway schema pair in the TOY db, torn down after unless a case
fails (left standing as evidence, matching the standing-probe convention every other
run_fixtures.py in this repo uses). Both grammars are exercised in ONE fixture file because they
are one feature (one tracker item, one `./pickup` TAXONOMIES section, one USER page) -- the same
granularity choice this repo already makes for e.g. multi-case fixtures elsewhere, not a
short-cut around per-grammar coverage (every case below is grammar-specific, both polarities,
both grammars).

WHAT THIS PROVES: `bootstrap/templates/led.tmpl` validates a `taxon:`-prefixed decision statement
(four fields: TAXONOMY | TAXON | PATTERNS | GLOSS) and an `interface:`-prefixed decision
statement (three fields: TAXONOMY | ARTIFACT-PATTERN | GLOSS) -- both against a
whitespace-normalized copy -- BEFORE the INSERT, refusing loudly (exit nonzero, nothing written,
teach-text naming the grammar and user-guide/USER-TAXONOMY-DECLARATION.md) on any single-field
defect, and accepting a well-formed statement byte-exact, embedded newline included.
`bootstrap/templates/pickup.tmpl`'s taxonomies() reader renders an accepted row cleanly under the
shared `### SECTION: TAXONOMIES` header (taxa first, then interfaces), using the identical
newline-normalization and leading-whitespace coherence-partner contract resources()/estimates()
already keep for `resource:`/`estimate:`.

CASES (all live subprocess runs of the real `led`/`pickup` verbs against a real scratch
deployment -- never a mock):

  ADOPT                            -- bootstrap/track-work.sh stands up the scratch deployment.

  -- taxon: grammar --
  RED-TAXON-FIELDCOUNT             -- a 2-field `taxon:` statement is REFUSED, row count
                                       unchanged (atomicity by refusal-before-write).
  RED-TAXON-BAD-TAXONOMY           -- a 4-field statement whose TAXONOMY is not a bare slug
                                       (uppercase/space) is REFUSED, row count unchanged.
  RED-TAXON-BAD-TAXON              -- a 4-field statement whose TAXON is not a bare slug is
                                       REFUSED, row count unchanged.
  RED-TAXON-EMPTY-PATTERNS         -- a 4-field statement whose PATTERNS field is empty is
                                       REFUSED, row count unchanged.
  RED-TAXON-EMPTY-GLOSS            -- a 4-field statement whose GLOSS field is empty is REFUSED,
                                       row count unchanged.
  GREEN-TAXON-WELL-FORMED          -- a well-formed statement (the omega licensing specimen,
                                       design/ORCH-SPEC-TASK-TAXONOMY.md §3 / design/
                                       USER-TAXONOMY-DECLARATION.md's worked example) is ACCEPTED
                                       and stored byte-exact.
  GREEN-TAXON-EMBEDDED-NEWLINE     -- a statement with an embedded newline + indent mid-word is
                                       ACCEPTED after whitespace normalization, and the STORED row
                                       preserves the embedded newline verbatim.
  GREEN-TAXON-PICKUP-RENDERS       -- `./pickup`'s TAXONOMIES section shows the accepted row as
                                       one clean `TAXON [...]` block and contains no "MALFORMED"
                                       string anywhere in the TAXONOMIES section.
  GREEN-TAXON-LEADING-WHITESPACE   -- a `taxon:` declaration with LEADING whitespace is accepted
                                       by led AND renders in pickup's TAXONOMIES section -- the
                                       coherence-partner contract proven live.

  -- interface: grammar --
  RED-INTERFACE-FIELDCOUNT         -- a 2-field `interface:` statement is REFUSED, row count
                                       unchanged.
  RED-INTERFACE-BAD-TAXONOMY       -- a 3-field statement whose TAXONOMY is not a bare slug is
                                       REFUSED, row count unchanged.
  RED-INTERFACE-EMPTY-PATTERN      -- a 3-field statement whose ARTIFACT-PATTERN is empty is
                                       REFUSED, row count unchanged.
  RED-INTERFACE-EMPTY-GLOSS        -- a 3-field statement whose GLOSS is empty is REFUSED, row
                                       count unchanged.
  GREEN-INTERFACE-WELL-FORMED      -- a well-formed statement (the omega specimen's own interface
                                       row) is ACCEPTED and stored byte-exact.
  GREEN-INTERFACE-EMBEDDED-NEWLINE -- a statement with an embedded newline + indent mid-word is
                                       ACCEPTED, stored with the newline preserved.
  GREEN-INTERFACE-PICKUP-RENDERS   -- `./pickup`'s TAXONOMIES section shows the accepted row as
                                       one clean `INTERFACE [...]` block, no "MALFORMED" anywhere.
  GREEN-INTERFACE-LEADING-WHITESPACE -- an `interface:` declaration with LEADING whitespace is
                                       accepted and renders -- the coherence-partner contract.

Scratch-only: schema/kern/role derived from a throwaway name (`SCRATCH_NAME` below, distinct from
every other fixture's own scratch name in this repo) in the TOY db (192.168.122.1) plus a
throwaway tempdir -- both dropped/removed after, UNLESS a case FAILS (left standing as evidence,
kernel/fixtures/s22_work_item_fixture.py's own convention).

Usage: python3 seen-red/taxonomy-intake-validation/run_fixtures.py
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
SCRATCH_NAME = "taxivfixture"
SCHEMA, KERN, ROLE = SCRATCH_NAME, f"{SCRATCH_NAME}_kernel", f"{SCRATCH_NAME}_rw"

# --- taxon: specimens -----------------------------------------------------------------------
TAXON_FIELDCOUNT = "taxon: license | mit-derivative"
TAXON_BAD_TAXONOMY = "taxon: Bad Taxonomy | mit-derivative | backend/qeubo/** | a gloss"
TAXON_BAD_TAXON = "taxon: license | Bad Taxon | backend/qeubo/** | a gloss"
TAXON_EMPTY_PATTERNS = "taxon: license | mit-derivative |   | a gloss"
TAXON_EMPTY_GLOSS = "taxon: license | mit-derivative | backend/qeubo/** |   "
# the omega licensing specimen, design/ORCH-SPEC-TASK-TAXONOMY.md §3, transcribed verbatim:
TAXON_WELL_FORMED = "taxon: license | mit-derivative | backend/qeubo/** | upstream qEUBO derivative"
# an embedded newline + 4-space indent splitting "qEUBO" from its own continuation:
TAXON_EMBEDDED_NEWLINE = (
    "taxon: license | mit-derivative-fork | vendor/qeubo-fork/** | a locally-patched fork of "
    "the upstream qEUBO\n    derivative, kept separate pending upstreaming"
)
TAXON_LEADING_WHITESPACE = "  taxon: arch-layer | domain | src/domain/** | pure business logic, no I/O"

# --- interface: specimens --------------------------------------------------------------------
INTERFACE_FIELDCOUNT = "interface: license | backend/qeubo/__init__.py"
INTERFACE_BAD_TAXONOMY = "interface: Bad Taxonomy | backend/qeubo/__init__.py | the public surface"
INTERFACE_EMPTY_PATTERN = "interface: license |   | the public surface"
INTERFACE_EMPTY_GLOSS = "interface: license | backend/qeubo/__init__.py |   "
# the omega licensing specimen's own interface row, design/ORCH-SPEC-TASK-TAXONOMY.md §3:
INTERFACE_WELL_FORMED = "interface: license | backend/qeubo/__init__.py | the documented public surface"
INTERFACE_EMBEDDED_NEWLINE = (
    "interface: arch-layer | src/domain/ports.py | the only module an adapter may import "
    "from the domain\n    layer, per the arch-layer taxonomy's own boundary"
)
INTERFACE_LEADING_WHITESPACE = "  interface: arch-layer | src/domain/ports.py | the domain layer's own port module"


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
                           capture_output=True, text=True, cwd=str(dest), env=os.environ.copy())


def _ledger_row_count(dest: Path) -> int:
    r = _psql("-tAc", f"SET ROLE {ROLE}; SELECT count(*) FROM {SCHEMA}.ledger;")
    return int(r.stdout.strip().splitlines()[-1])


def main() -> int:
    failures: list[str] = []
    transcript: list[str] = []

    def log(line: str) -> None:
        print(line)
        transcript.append(line)

    def red_case(dest: Path, name: str, statement: str, expect_substr: str) -> None:
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

    def green_case(dest: Path, name: str, statement: str) -> None:
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

    def byte_exact_check(name: str, prefix: str, expected_substr: str) -> None:
        r_stmt = _psql("-tAc", f"SET ROLE {ROLE}; SELECT statement FROM {SCHEMA}.ledger "
                                f"WHERE kind = 'decision' AND statement LIKE '{prefix}%' "
                                f"ORDER BY id DESC LIMIT 1;")
        stored = r_stmt.stdout
        ok = expected_substr in stored
        if not ok:
            failures.append(f"{name}: stored statement lost byte fidelity\nSTORED:\n{stored!r}")
        log(f"{name}: stored statement is byte-exact -- {'PASS' if ok else 'FAIL'}")

    def pickup_renders(dest: Path, name: str, expect_substr: str, absent_substr: str = "MALFORMED") -> None:
        r_pickup = _run(dest, "pickup")
        out = r_pickup.stdout
        start = out.find("### SECTION: TAXONOMIES")
        end = out.find("### SECTION:", start + 1)
        section_text = out[start:end if end != -1 else None].strip() if start != -1 else ""
        ok = expect_substr in section_text and absent_substr not in section_text
        if not ok:
            failures.append(f"{name}: TAXONOMIES section did not render as expected\n{section_text}")
        log(f"{name}: TAXONOMIES section renders {expect_substr!r} with no {absent_substr!r} -- "
            f"{'PASS' if ok else 'FAIL'}")
        log(f"--- pickup TAXONOMIES section ({name}, verbatim) ---")
        log(section_text)
        transcript.append(section_text)
        log("--- end pickup TAXONOMIES section ---")

    _drop_scratch()
    tmpdir = Path(tempfile.mkdtemp(prefix="taxonomy-intake-validation-fixture-"))
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

    # ---------------------------------------------------------------------------- taxon: RED
    red_case(dest, "RED-TAXON-FIELDCOUNT", TAXON_FIELDCOUNT, "got 2")
    red_case(dest, "RED-TAXON-BAD-TAXONOMY", TAXON_BAD_TAXONOMY, "TAXONOMY field")
    red_case(dest, "RED-TAXON-BAD-TAXON", TAXON_BAD_TAXON, "TAXON field")
    red_case(dest, "RED-TAXON-EMPTY-PATTERNS", TAXON_EMPTY_PATTERNS, "PATTERNS field")
    red_case(dest, "RED-TAXON-EMPTY-GLOSS", TAXON_EMPTY_GLOSS, "GLOSS field")

    # -------------------------------------------------------------------------- taxon: GREEN
    green_case(dest, "GREEN-TAXON-WELL-FORMED", TAXON_WELL_FORMED)
    byte_exact_check("GREEN-TAXON-WELL-FORMED", "taxon:", TAXON_WELL_FORMED)

    green_case(dest, "GREEN-TAXON-EMBEDDED-NEWLINE", TAXON_EMBEDDED_NEWLINE)
    byte_exact_check("GREEN-TAXON-EMBEDDED-NEWLINE", "taxon: license | mit-derivative-fork",
                      "\n    derivative, kept separate")

    pickup_renders(dest, "GREEN-TAXON-PICKUP-RENDERS", "TAXON [license] mit-derivative ")

    green_case(dest, "GREEN-TAXON-LEADING-WHITESPACE", TAXON_LEADING_WHITESPACE)
    pickup_renders(dest, "GREEN-TAXON-LEADING-WHITESPACE", "TAXON [arch-layer] domain")

    # ------------------------------------------------------------------------ interface: RED
    red_case(dest, "RED-INTERFACE-FIELDCOUNT", INTERFACE_FIELDCOUNT, "got 2")
    red_case(dest, "RED-INTERFACE-BAD-TAXONOMY", INTERFACE_BAD_TAXONOMY, "TAXONOMY field")
    red_case(dest, "RED-INTERFACE-EMPTY-PATTERN", INTERFACE_EMPTY_PATTERN, "ARTIFACT-PATTERN field")
    red_case(dest, "RED-INTERFACE-EMPTY-GLOSS", INTERFACE_EMPTY_GLOSS, "GLOSS field")

    # ---------------------------------------------------------------------- interface: GREEN
    green_case(dest, "GREEN-INTERFACE-WELL-FORMED", INTERFACE_WELL_FORMED)
    byte_exact_check("GREEN-INTERFACE-WELL-FORMED", "interface:", INTERFACE_WELL_FORMED)

    green_case(dest, "GREEN-INTERFACE-EMBEDDED-NEWLINE", INTERFACE_EMBEDDED_NEWLINE)
    byte_exact_check("GREEN-INTERFACE-EMBEDDED-NEWLINE", "interface: arch-layer | src/domain/ports.py",
                      "\n    layer, per the arch-layer")

    pickup_renders(dest, "GREEN-INTERFACE-PICKUP-RENDERS", "INTERFACE [license] backend/qeubo/__init__.py")

    green_case(dest, "GREEN-INTERFACE-LEADING-WHITESPACE", INTERFACE_LEADING_WHITESPACE)
    pickup_renders(dest, "GREEN-INTERFACE-LEADING-WHITESPACE",
                    "INTERFACE [arch-layer] src/domain/ports.py")

    if failures:
        print(f"\ntaxonomy-intake-validation fixture: {len(failures)} FAILURE(S) -- scratch "
              f"substrate left standing as evidence:\n  tempdir: {tmpdir}\n  schema:  {SCHEMA} / "
              f"{KERN} / {ROLE} (db {DB}@{PGHOST})")
        for f in failures:
            print(f"\n!! {f}")
        return 1

    _drop_scratch()
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\ntaxonomy-intake-validation fixture: all cases PASS, scratch substrate torn down to "
          f"zero residue (tempdir removed, schema {SCHEMA}/{KERN}/role {ROLE} dropped).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
