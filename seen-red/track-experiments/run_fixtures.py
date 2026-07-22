#!/usr/bin/env python3
"""run_fixtures — both-polarity live proof for bootstrap/track-experiments.sh (the standing
research-ledger recording-surface offering; BACKLOG "research-ledger-offering"; gates/
fixture_census.py REGISTRY entry "track-experiments"). Mirrors seen-red/track-work/
run_fixtures.py's own scratch-and-drop pattern (a throwaway project directory plus a throwaway
schema pair in the TOY db, torn down after unless a case fails) — read that file first if this
one is unclear; the two are deliberately shaped the same way.

WHY A SCRATCH SCHEMA PAIR, RENAMED (not literally "core"/"research"): stores/
001_research_ledger.sql hardcodes its two schema names (`CREATE SCHEMA IF NOT EXISTS core;`
/`... research;` -- NOT parameterized via psql -v the way the kernel lineage files are), so a
scratch validation of it needs a RENAMED copy of the DDL text applied under different schema
names, never the literal "core"/"research" (which is the STANDING db's own name, exclusively
apply-research-ledger.sh's to write). This is the SAME device BACKLOG's own 2026-07-11 scratch
validation used (schema pair `rlprobe_core`/`rlprobe_research`) -- this fixture's own pair is
named distinctly (`texpprobe_core`/`texpprobe_research`) so the two probes can never collide if
ever run concurrently. The substitution is a plain word-boundary sed over the DDL's own text
(comments included -- harmless, since this rewritten copy is never committed, only applied to a
throwaway schema pair and discarded); the DDL's own semantics (tables, constraints, triggers,
the derived view) are otherwise untouched.

CASES (both polarities, all live subprocess runs of the real script -- never a mock):

  RED-USAGE            -- omitting a required flag (--name) exits 2 with a usage message, no
                          config file written, no DB touched at all.
  GREEN-ADOPT           -- a fresh `track-experiments.sh <dir> --name <name> --db toy --host
                          <host> --core-schema texpprobe_core --research-schema
                          texpprobe_research` (schema pair pre-applied by this fixture's own
                          setup, mirroring bootstrap/apply-research-ledger.sh's OWN DDL apply,
                          never invoking that script itself) exits 0, writes research-ledger.json
                          + the record-reading shim, and the preflight correctly reports the
                          schema as ALREADY APPLIED.
  GREEN-ADOPT (live)     -- the record-reading shim actually WORKS end-to-end: a real
                          `record-reading` call (with a fresh instrument) and a real
                          `record-finding` call land real rows, read back via a direct SELECT
                          against the scratch schema (never trusted from the shim's own exit
                          code alone).
  RED-EXISTING          -- re-running the SAME command against the SAME dir with no --force is
                          REFUSED (exit 1), naming research-ledger.json, config file BYTE-
                          IDENTICAL across the refused re-run, and the reading/finding row counts
                          unchanged (no DB touch on refusal).
  GREEN-FORCE            -- the SAME command WITH --force succeeds again (exit 0); the config is
                          re-written (harmless -- it is deployment-local metadata, not the
                          ledger itself) and the existing reading/finding rows are untouched.
  RED-UNAPPLIED-SCHEMA   -- a SECOND throwaway project-dir, pointed via --core-schema/
                          --research-schema at a schema pair this fixture deliberately never
                          applies the DDL to: `track-experiments.sh` itself still exits 0 (it
                          never blocks on this -- see that script's own header, "WHAT THIS DOES
                          NOT DO"), printing the honest "NOT yet applied" preflight note, and a
                          REAL `record-reading` call through that dir's own shim is REFUSED
                          (non-zero exit, psql's own "relation ... does not exist" surfacing
                          through filing/record_reading.py's fail-loud RecordReadingError) --
                          proving the documented claim live, not merely asserting it.

Scratch-only: schema pair `texpprobe_core`/`texpprobe_research` (GREEN-ADOPT/RED-EXISTING/
GREEN-FORCE) and `texpprobe2_core`/`texpprobe2_research` (RED-UNAPPLIED-SCHEMA, deliberately
left unapplied) in the TOY db (192.168.122.1), plus two throwaway tempdirs -- schemas dropped
and tempdirs removed after, UNLESS a case FAILS (left standing as evidence, matching seen-red/
track-work/run_fixtures.py's own convention).

Usage: python3 seen-red/track-experiments/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402 (filing/pghost_resolve.py via seen-red/_fixture_env.py -- never a literal host default)


REPO = Path(__file__).resolve().parents[2]
TRACK_EXPERIMENTS = REPO / "bootstrap" / "track-experiments.sh"
DDL = REPO / "stores" / "001_research_ledger.sql"
PGHOST, DB = fixture_pghost(), "toy"

CORE_SCHEMA, RESEARCH_SCHEMA = "texpprobe_core", "texpprobe_research"
CORE_SCHEMA2, RESEARCH_SCHEMA2 = "texpprobe2_core", "texpprobe2_research"
PROJECT_ID = "texpfixture"

_WORD_CORE = re.compile(r"\bcore\b")
_WORD_RESEARCH = re.compile(r"\bresearch\b")


def _psql(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["psql", "-h", PGHOST, "-d", DB, *args], capture_output=True, text=True)


def _drop_scratch(core_schema: str, research_schema: str) -> None:
    _psql("-v", "ON_ERROR_STOP=0", "-q",
          "-c", f"DROP SCHEMA IF EXISTS {core_schema} CASCADE;",
          "-c", f"DROP SCHEMA IF EXISTS {research_schema} CASCADE;")


def _apply_renamed_ddl(core_schema: str, research_schema: str) -> subprocess.CompletedProcess:
    """Apply a RENAMED copy of stores/001_research_ledger.sql's DDL text (see this module's own
    docstring, "WHY A SCRATCH SCHEMA PAIR, RENAMED") -- never the real bootstrap/
    apply-research-ledger.sh, and never the literal core/research schema names."""
    text = DDL.read_text(encoding="utf-8")
    text = _WORD_CORE.sub(core_schema, text)
    text = _WORD_RESEARCH.sub(research_schema, text)
    fd, path = tempfile.mkstemp(suffix=".sql", prefix="texpprobe-ddl-")
    os.close(fd)
    try:
        Path(path).write_text(text, encoding="utf-8")
        return _psql("-v", "ON_ERROR_STOP=1", "-f", path)
    finally:
        os.unlink(path)


def _row_count(schema: str, table: str) -> int | None:
    """None if the schema/table does not exist yet."""
    r = _psql("-tAc", f"SELECT to_regclass('{schema}.{table}') IS NOT NULL;")
    if r.stdout.strip() != "t":
        return None
    r = _psql("-tAc", f"SELECT count(*) FROM {schema}.{table};")
    return int(r.stdout.strip())


def _run_track_experiments(dest: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(TRACK_EXPERIMENTS), str(dest), "--db", DB, "--host", PGHOST, *extra],
        capture_output=True, text=True, cwd=str(REPO))


def main() -> int:
    failures: list[str] = []
    _drop_scratch(CORE_SCHEMA, RESEARCH_SCHEMA)
    _drop_scratch(CORE_SCHEMA2, RESEARCH_SCHEMA2)
    tmpdir = Path(tempfile.mkdtemp(prefix="track-experiments-fixture-"))
    dest = tmpdir / "project"
    dest2 = tmpdir / "project-unapplied"

    # ---------------------------------------------------------------- RED-USAGE (no DB touched)
    r = subprocess.run([str(TRACK_EXPERIMENTS), str(dest), "--db", DB, "--host", PGHOST],
                       capture_output=True, text=True, cwd=str(REPO))
    config_written = (dest / "research-ledger.json").exists()
    if r.returncode != 2 or config_written:
        failures.append(f"RED-USAGE: expected exit 2 (missing --name) and no config written, "
                        f"got exit={r.returncode} config_written={config_written}\n{r.stderr}")
    print(f"RED-USAGE: exit={r.returncode} (expect 2), config_written={config_written} "
          f"(expect False) -- {'PASS' if r.returncode == 2 and not config_written else 'FAIL'}")

    # ------------------------------------------------------- setup: apply the renamed DDL, once
    # (mirrors bootstrap/apply-research-ledger.sh's OWN DDL apply -- never that script itself;
    # this fixture owns its own scratch substrate, exactly as seen-red/track-work's setup does
    # for the kernel lineage).
    r_ddl = _apply_renamed_ddl(CORE_SCHEMA, RESEARCH_SCHEMA)
    if r_ddl.returncode != 0:
        print(f"SETUP: DDL apply FAILED, aborting fixture:\n{r_ddl.stdout}\n{r_ddl.stderr}")
        return 1
    print(f"SETUP: renamed DDL applied clean to {CORE_SCHEMA}/{RESEARCH_SCHEMA}")

    # ---------------------------------------------------------------- GREEN-ADOPT
    r = _run_track_experiments(dest, "--name", PROJECT_ID,
                               "--core-schema", CORE_SCHEMA, "--research-schema", RESEARCH_SCHEMA)
    cfg_path = dest / "research-ledger.json"
    shim_path = dest / "record-reading"
    shim_ok = shim_path.exists() and bool(shim_path.stat().st_mode & 0o111)
    applied_reported = "IS applied" in r.stdout
    ok = r.returncode == 0 and cfg_path.exists() and shim_ok and applied_reported
    if not ok:
        failures.append(f"GREEN-ADOPT: exit={r.returncode} cfg_exists={cfg_path.exists()} "
                        f"shim_ok={shim_ok} applied_reported={applied_reported}\n"
                        f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
    print(f"GREEN-ADOPT: exit={r.returncode} research-ledger.json={cfg_path.exists()} "
          f"record-reading shim present+executable={shim_ok} preflight reported "
          f"applied={applied_reported} -- {'PASS' if ok else 'FAIL'}")

    cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
    cfg_ok = (cfg.get("project_id") == PROJECT_ID and cfg.get("db") == DB
             and cfg.get("host") == PGHOST and cfg.get("core_schema") == CORE_SCHEMA
             and cfg.get("research_schema") == RESEARCH_SCHEMA)
    if not cfg_ok:
        failures.append(f"GREEN-ADOPT: research-ledger.json content wrong: {cfg}")
    print(f"GREEN-ADOPT: research-ledger.json content matches invocation -- "
          f"{'PASS' if cfg_ok else 'FAIL'}")

    # ---------------------------------------------------------- GREEN-ADOPT (live): the shim
    # actually records real rows, read back via a direct SELECT -- never trusted from the
    # shim's own exit code alone (ADR-0013 Rule 5, verify the artifact).
    r_reading = subprocess.run(
        [str(shim_path), "record-reading", "--project", PROJECT_ID, "--metric", "fixture_metric",
         "--value", "3.14", "--git-commit", "0" * 40, "--git-tree", "clean",
         "--instrument-name", "fixture-instrument", "--instrument-kind", "script",
         "--source-hash", "a" * 64, "--instrument-git-commit", "0" * 40,
         "--instrument-git-tree", "clean"],
        capture_output=True, text=True, cwd=str(dest))
    reading_id = r_reading.stdout.strip()
    reading_ok = r_reading.returncode == 0 and reading_id.isdigit()
    if not reading_ok:
        failures.append(f"GREEN-ADOPT (live): record-reading failed: exit={r_reading.returncode}\n"
                        f"{r_reading.stdout}\n{r_reading.stderr}")
    print(f"GREEN-ADOPT (live): record-reading exit={r_reading.returncode} reading_id="
          f"{reading_id!r} -- {'PASS' if reading_ok else 'FAIL'}")

    r_finding = subprocess.run(
        [str(shim_path), "record-finding", "--project", PROJECT_ID, "--reading", reading_id or "0",
         "--interpretation", "fixture finding, both-polarity seen-red proof"],
        capture_output=True, text=True, cwd=str(dest))
    finding_ok = r_finding.returncode == 0 and r_finding.stdout.strip().isdigit()
    if not finding_ok:
        failures.append(f"GREEN-ADOPT (live): record-finding failed: exit={r_finding.returncode}\n"
                        f"{r_finding.stdout}\n{r_finding.stderr}")
    print(f"GREEN-ADOPT (live): record-finding exit={r_finding.returncode} -- "
          f"{'PASS' if finding_ok else 'FAIL'}")

    r_sel = _psql("-tAc",
                  f"SELECT metric, value FROM {RESEARCH_SCHEMA}.reading "
                  f"WHERE reading_id = {reading_id or '0'};")
    row_seen = r_sel.stdout.strip() == "fixture_metric|3.14"
    if not row_seen:
        failures.append(f"GREEN-ADOPT (live): direct SELECT did not confirm the reading row: "
                        f"{r_sel.stdout!r} {r_sel.stderr!r}")
    print(f"GREEN-ADOPT (live): direct SELECT confirms the reading row -- "
          f"{'PASS' if row_seen else 'FAIL'}")

    baseline_readings = _row_count(RESEARCH_SCHEMA, "reading")
    baseline_findings = _row_count(RESEARCH_SCHEMA, "finding")

    # ---------------------------------------------------------------- RED-EXISTING
    cfg_before = cfg_path.read_bytes()
    r = _run_track_experiments(dest, "--name", PROJECT_ID,
                               "--core-schema", CORE_SCHEMA, "--research-schema", RESEARCH_SCHEMA)
    cfg_after = cfg_path.read_bytes()
    refused = r.returncode == 1 and "already exists" in r.stderr
    untouched = (cfg_before == cfg_after
                and _row_count(RESEARCH_SCHEMA, "reading") == baseline_readings
                and _row_count(RESEARCH_SCHEMA, "finding") == baseline_findings)
    if not refused or not untouched:
        failures.append(f"RED-EXISTING: exit={r.returncode} refused={refused} "
                        f"cfg_unchanged={cfg_before == cfg_after} rows_untouched={untouched}\n"
                        f"{r.stderr}")
    print(f"RED-EXISTING: exit={r.returncode} (expect 1, 'already exists'), config byte-identical "
          f"and reading/finding rows unchanged -- {'PASS' if refused and untouched else 'FAIL'}")

    # ---------------------------------------------------------------- GREEN-FORCE
    r = _run_track_experiments(dest, "--name", PROJECT_ID, "--core-schema", CORE_SCHEMA,
                               "--research-schema", RESEARCH_SCHEMA, "--force")
    rows_after_force = (_row_count(RESEARCH_SCHEMA, "reading"), _row_count(RESEARCH_SCHEMA, "finding"))
    force_ok = r.returncode == 0 and rows_after_force == (baseline_readings, baseline_findings)
    if not force_ok:
        failures.append(f"GREEN-FORCE: exit={r.returncode} rows_after_force={rows_after_force} "
                        f"(expected {(baseline_readings, baseline_findings)}, unchanged -- --force "
                        f"only re-derives research-ledger.json + the shim, never touches ledger "
                        f"rows)\n{r.stdout}\n{r.stderr}")
    print(f"GREEN-FORCE: exit={r.returncode} reading/finding rows unchanged -- "
          f"{'PASS' if force_ok else 'FAIL'}")

    # ---------------------------------------------------------------- RED-UNAPPLIED-SCHEMA
    # Deliberately never applies the DDL to CORE_SCHEMA2/RESEARCH_SCHEMA2 -- proves the honest
    # "NOT yet applied" preflight message AND the real downstream refusal, live.
    r2 = _run_track_experiments(dest2, "--name", "texpfixture-unapplied",
                                "--core-schema", CORE_SCHEMA2, "--research-schema", RESEARCH_SCHEMA2)
    unapplied_reported = "NOT yet applied" in r2.stdout
    adopt_still_succeeds = r2.returncode == 0 and (dest2 / "research-ledger.json").exists()
    if not unapplied_reported or not adopt_still_succeeds:
        failures.append(f"RED-UNAPPLIED-SCHEMA: exit={r2.returncode} unapplied_reported="
                        f"{unapplied_reported} adopt_still_succeeds={adopt_still_succeeds}\n"
                        f"{r2.stdout}\n{r2.stderr}")
    print(f"RED-UNAPPLIED-SCHEMA: track-experiments.sh itself exit={r2.returncode} (expect 0, "
          f"never blocks), preflight reported NOT-yet-applied={unapplied_reported} -- "
          f"{'PASS' if unapplied_reported and adopt_still_succeeds else 'FAIL'}")

    r2_reading = subprocess.run(
        [str(dest2 / "record-reading"), "record-reading", "--project", "texpfixture-unapplied",
         "--metric", "should-fail", "--value", "1.0", "--git-commit", "0" * 40, "--git-tree", "clean",
         "--instrument-name", "n", "--instrument-kind", "script", "--source-hash", "b" * 64,
         "--instrument-git-commit", "0" * 40, "--instrument-git-tree", "clean"],
        capture_output=True, text=True, cwd=str(dest2))
    real_refusal = r2_reading.returncode != 0 and "REFUSED" in r2_reading.stderr
    if not real_refusal:
        failures.append(f"RED-UNAPPLIED-SCHEMA: record-reading against an unapplied schema should "
                        f"have been REFUSED, got exit={r2_reading.returncode}\n"
                        f"{r2_reading.stdout}\n{r2_reading.stderr}")
    print(f"RED-UNAPPLIED-SCHEMA: a real record-reading call against the unapplied schema is "
          f"REFUSED (exit={r2_reading.returncode}) -- {'PASS' if real_refusal else 'FAIL'}")

    if failures:
        print(f"\ntrack-experiments fixture: {len(failures)} FAILURE(S) -- scratch substrate left "
              f"standing as evidence:\n  tempdir: {tmpdir}\n"
              f"  schema:  {CORE_SCHEMA}/{RESEARCH_SCHEMA} + {CORE_SCHEMA2}/{RESEARCH_SCHEMA2} "
              f"(db {DB}@{PGHOST})")
        for f in failures:
            print(f"\n!! {f}")
        return 1

    _drop_scratch(CORE_SCHEMA, RESEARCH_SCHEMA)
    _drop_scratch(CORE_SCHEMA2, RESEARCH_SCHEMA2)
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\ntrack-experiments fixture: all cases PASS, scratch substrate torn down to zero "
          f"residue (tempdir removed, schemas {CORE_SCHEMA}/{RESEARCH_SCHEMA} + "
          f"{CORE_SCHEMA2}/{RESEARCH_SCHEMA2} dropped).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
