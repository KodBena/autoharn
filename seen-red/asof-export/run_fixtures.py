#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T10:34:23Z
#   last-change: 2026-07-18T10:38:43Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures — both-polarity live proof for ../../asof-export (bootstrap/templates/
asof-export.tmpl; gates/fixture_census.py REGISTRY entry "asof-export"). Ledger item
`asof-export-inspection-copy`. Real infra, no mocks: bootstrap/track-work.sh stands up a
throwaway scratch deployment in the TOY db, torn down after unless a case fails (left standing
as evidence, the standing-probe convention e.g. seen-red/track-work/run_fixtures.py already
uses).

THE POLARITY THIS ITEM'S OWN COMMISSIONING TEXT NAMES, VERBATIM: "witness both polarities (an
as-of before a supersession shows the superseded row in force; after, the superseding one)."
Two ledger rows are written, the second superseding the first. Every case below reads the
ACTUAL `ts` postgres assigned each row (never a wall-clock guess, which would be exposed to
session-timezone ambiguity the same way `led work asof`'s own bound `:asof::timestamptz` is —
see asof-export.tmpl's own module docstring, "DELIBERATE CHOICE" paragraph) so the as-of
boundaries used below are exact, not approximate.

CASES:

  GREEN-BEFORE   -- `./asof-export read --asof <midpoint between row1.ts and row2.ts>` shows
                    row1 (the superseded row) IN FORCE, row2 absent.
  GREEN-AFTER    -- the same read at (row2.ts + a small delta) shows row2 (the superseding row)
                    IN FORCE, row1 absent (retracted, reinstatement-free — s31's own semantics,
                    generalized into time by this verb).
  GREEN-EXPORT   -- `./asof-export export --asof <after> --out DIR` writes ledger-asof.txt,
                    ledger-asof.json, manifest.sha256; `sha256sum -c manifest.sha256` verifies
                    clean; the JSON's row_count/rows match the read case; re-running WITHOUT
                    --force is REFUSED (exit 1, no file touched — ADR-0002, an inspection copy is
                    not silently overwritten); WITH --force it succeeds again.
  RED-NAIVE-QUERY -- the DEFECT this verb's query design forecloses, reproduced directly: the
                    SAME reconstruction with the temporal guard dropped from the retraction side
                    (`NOT EXISTS (SELECT 1 FROM ledger s WHERE s.supersedes = l.id)`, no
                    `s.ts <= :asof` conjunct — i.e. "ledger_current's own filter, naively reused
                    at a past timestamp") queried at the SAME "before" instant as GREEN-BEFORE:
                    it incorrectly shows row1 ALREADY retracted (zero rows in force), because the
                    naive query treats "supersedes exists" as sufficient regardless of when the
                    superseding row itself landed. This is the row_reader class asof-export.tmpl's
                    own module docstring ("THE QUERY") names as the second conjunct's whole job —
                    reproduced here as banked evidence that the conjunct is load-bearing, not
                    decorative.
  RED-BAD-ASOF   -- `--asof "not-a-timestamp"` is REFUSED loudly (exit 2, named psql error on
                    stderr), never a silent empty result.
  RED-USAGE      -- `export` with no `--out` is refused by argparse (exit 2) — this verb never
                    guesses where an inspection copy belongs (ADR-0002).

Usage: python3 seen-red/asof-export/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
TRACK_WORK = REPO / "bootstrap" / "track-work.sh"
PGHOST, DB = fixture_pghost(), "toy"
SCRATCH_NAME = "aeexfixture"
SCHEMA, KERN, ROLE = SCRATCH_NAME, f"{SCRATCH_NAME}_kernel", f"{SCRATCH_NAME}_rw"
TAG = f"seen-red-asof-export-{int(time.time())}"


def _psql(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["psql", "-h", PGHOST, "-d", DB, *args], capture_output=True, text=True)


def _drop_scratch() -> None:
    _psql("-v", "ON_ERROR_STOP=0", "-q",
          "-c", f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE;",
          "-c", f"DROP SCHEMA IF EXISTS {KERN} CASCADE;",
          "-c", f"DROP ROLE IF EXISTS {ROLE};")


def _run(dest: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(dest / args[0]), *args[1:]], capture_output=True, text=True, cwd=str(dest))


def _row_ts_epoch(dest: Path, row_id: int) -> float:
    out = subprocess.run(
        ["psql", "-h", PGHOST, "-d", DB, "-tAc",
         f"SELECT extract(epoch FROM ts) FROM {SCHEMA}.ledger WHERE id = {row_id};"],
        capture_output=True, text=True)
    return float(out.stdout.strip())


def _iso_z(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> int:
    failures: list[str] = []
    _drop_scratch()
    tmpdir = Path(tempfile.mkdtemp(prefix="asof-export-fixture-"))
    dest = tmpdir / "project"

    # --------------------------------------------------------------------------------- ADOPT
    r = subprocess.run(["bash", str(TRACK_WORK), str(dest), "--name", SCRATCH_NAME,
                        "--db", DB, "--host", PGHOST], capture_output=True, text=True, cwd=str(REPO))
    for verb in ("led", "judge", "pickup", "audit", "distance-to-clean", "asof-export"):
        p = dest / verb
        if p.exists():
            p.chmod(0o755)
    ok = (r.returncode == 0 and (dest / "deployment.json").exists()
          and (dest / "asof-export").exists())
    if not ok:
        failures.append(f"ADOPT: exit={r.returncode} asof-export shim written="
                         f"{(dest / 'asof-export').exists()}\nSTDOUT:\n{r.stdout[-1500:]}\n"
                         f"STDERR:\n{r.stderr[-1500:]}")
        print(f"ADOPT: FAIL\n{failures[-1]}")
        print(f"\nADOPT FAILED, aborting -- scratch left standing:\n  tempdir: {tmpdir}")
        return 1
    print(f"ADOPT: track-work.sh exit={r.returncode} deployment.json=True asof-export shim=True -- PASS")

    # ------------------------------------------------------------------------------- SETUP
    r1 = _run(dest, "led", "note", f"{TAG} original statement")
    if r1.returncode != 0:
        failures.append(f"SETUP row1: exit={r1.returncode}\nSTDERR:\n{r1.stderr}")
    id1_line = [l for l in _run(dest, "led", "--recent", "1").stdout.splitlines() if l.strip()]
    id1 = int(id1_line[0].split("|")[0]) if id1_line else -1
    time.sleep(1.2)
    r2 = _run(dest, "led", "--supersedes", str(id1), "note", f"{TAG} revised statement")
    if r2.returncode != 0:
        failures.append(f"SETUP row2 (supersede): exit={r2.returncode}\nSTDERR:\n{r2.stderr}")
    id2_line = [l for l in _run(dest, "led", "--recent", "1").stdout.splitlines() if l.strip()]
    id2 = int(id2_line[0].split("|")[0]) if id2_line else -1
    print(f"SETUP: row1 id={id1} row2(supersedes {id1}) id={id2} -- "
          f"{'PASS' if r1.returncode == 0 and r2.returncode == 0 and id1 > 0 and id2 == id1 + 1 else 'FAIL'}")

    ts1 = _row_ts_epoch(dest, id1)
    ts2 = _row_ts_epoch(dest, id2)
    if not ts2 > ts1:
        failures.append(f"SETUP: expected row2.ts > row1.ts, got ts1={ts1} ts2={ts2}")
    before_ts = _iso_z((ts1 + ts2) / 2.0)
    after_ts = _iso_z(ts2 + 0.5)

    # ----------------------------------------------------------------------- GREEN-BEFORE
    r = _run(dest, "asof-export", "read", "--asof", before_ts)
    has1 = f"id={id1}" in r.stdout or f"id                          : {id1}" in r.stdout
    has2 = f"id={id2}" in r.stdout or f"id                          : {id2}" in r.stdout
    ok = r.returncode == 0 and has1 and not has2
    if not ok:
        failures.append(f"GREEN-BEFORE: exit={r.returncode} has_row1={has1} has_row2={has2}\n"
                         f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
    print(f"GREEN-BEFORE (asof={before_ts}): row1_in_force={has1} row2_in_force={has2} -- "
          f"{'PASS' if ok else 'FAIL'}")

    # ------------------------------------------------------------------------ GREEN-AFTER
    r = _run(dest, "asof-export", "read", "--asof", after_ts)
    has1 = f"id                          : {id1}" in r.stdout
    has2 = f"id                          : {id2}" in r.stdout
    ok = r.returncode == 0 and has2 and not has1
    if not ok:
        failures.append(f"GREEN-AFTER: exit={r.returncode} has_row1={has1} has_row2={has2}\n"
                         f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
    print(f"GREEN-AFTER (asof={after_ts}): row1_in_force={has1} row2_in_force={has2} -- "
          f"{'PASS' if ok else 'FAIL'}")

    # ----------------------------------------------------------------------- GREEN-EXPORT
    out_dir = dest / "inspection-copy-out"
    r = _run(dest, "asof-export", "export", "--asof", after_ts, "--out", str(out_dir))
    files_exist = all((out_dir / f).exists() for f in ("ledger-asof.txt", "ledger-asof.json", "manifest.sha256"))
    verify = subprocess.run(["sha256sum", "-c", "manifest.sha256"], cwd=str(out_dir),
                             capture_output=True, text=True)
    row_count_ok = False
    if files_exist:
        doc = json.loads((out_dir / "ledger-asof.json").read_text())
        row_count_ok = doc["row_count"] == 1 and doc["rows"][0]["id"] == id2
    ok = r.returncode == 0 and files_exist and verify.returncode == 0 and row_count_ok
    if not ok:
        failures.append(f"GREEN-EXPORT: exit={r.returncode} files_exist={files_exist} "
                         f"verify_rc={verify.returncode} row_count_ok={row_count_ok}\n"
                         f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}\nVERIFY:\n{verify.stdout}{verify.stderr}")
    print(f"GREEN-EXPORT: exit={r.returncode} files_exist={files_exist} "
          f"sha256sum_-c={'OK' if verify.returncode == 0 else 'FAIL'} row_count_ok={row_count_ok} -- "
          f"{'PASS' if ok else 'FAIL'}")

    # ------------------------------------------------------------------- GREEN-EXPORT-NO-CLOBBER
    r_noforce = _run(dest, "asof-export", "export", "--asof", after_ts, "--out", str(out_dir))
    r_force = _run(dest, "asof-export", "export", "--asof", after_ts, "--out", str(out_dir), "--force")
    ok = r_noforce.returncode == 1 and "REFUSED" in r_noforce.stderr and r_force.returncode == 0
    if not ok:
        failures.append(f"GREEN-EXPORT-NO-CLOBBER: noforce_exit={r_noforce.returncode} "
                         f"noforce_stderr={r_noforce.stderr!r} force_exit={r_force.returncode}")
    print(f"GREEN-EXPORT-NO-CLOBBER: no-force refused={r_noforce.returncode == 1} "
          f"force succeeds={r_force.returncode == 0} -- {'PASS' if ok else 'FAIL'}")

    # ----------------------------------------------------------------------- RED-NAIVE-QUERY
    # The defect this verb's second temporal conjunct (`s.ts <= :asof`) forecloses, reproduced
    # directly: drop that conjunct and requery at the SAME before_ts GREEN-BEFORE used.
    naive_sql = f"""SET ROLE {ROLE};
SELECT count(*) FROM (
  SELECT l.id FROM {SCHEMA}.ledger l
  WHERE l.ts <= :'asof'::timestamptz
    AND NOT EXISTS (SELECT 1 FROM {SCHEMA}.ledger s WHERE s.supersedes = l.id)
) t;
"""
    r = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-t", "-A", "-q",
                        "-v", "ON_ERROR_STOP=1", "-v", f"asof={before_ts}"],
                        input=naive_sql, capture_output=True, text=True)
    naive_lines = [l for l in r.stdout.splitlines() if l.strip() and l.strip() != "SET"]
    naive_count = int(naive_lines[0]) if naive_lines else -1
    # DEFECT REPRODUCED iff the naive query shows ZERO rows in force at before_ts (row1 wrongly
    # excluded, because "supersedes exists at all" fired regardless of when row2 itself landed) --
    # the correct query (GREEN-BEFORE above) shows exactly 1 (row1).
    defect_reproduced = r.returncode == 0 and naive_count == 0
    if not defect_reproduced:
        failures.append(f"RED-NAIVE-QUERY: exit={r.returncode} naive_count={naive_count} "
                         f"(expected 0, reproducing row1 wrongly excluded)\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
    print(f"RED-NAIVE-QUERY (naive filter, no temporal guard on retraction side, asof={before_ts}): "
          f"in-force count={naive_count} (correct query gave 1 at this same instant) -- "
          f"{'PASS (defect reproduced)' if defect_reproduced else 'FAIL'}")

    # ------------------------------------------------------------------------- RED-BAD-ASOF
    r = _run(dest, "asof-export", "read", "--asof", "not-a-timestamp")
    ok = r.returncode == 2 and "REFUSED" in r.stderr and "invalid input syntax" in r.stderr
    if not ok:
        failures.append(f"RED-BAD-ASOF: exit={r.returncode} stderr={r.stderr!r}")
    print(f"RED-BAD-ASOF: exit={r.returncode} refused_loudly={'REFUSED' in r.stderr} -- "
          f"{'PASS' if ok else 'FAIL'}")

    # --------------------------------------------------------------------------- RED-USAGE
    r = _run(dest, "asof-export", "export", "--asof", after_ts)  # no --out
    ok = r.returncode == 2 and ("--out" in r.stderr or "required" in r.stderr)
    if not ok:
        failures.append(f"RED-USAGE: exit={r.returncode} stderr={r.stderr!r}")
    print(f"RED-USAGE (export with no --out): exit={r.returncode} -- {'PASS' if ok else 'FAIL'}")

    if failures:
        print(f"\nasof-export fixture: {len(failures)} FAILURE(S) -- scratch substrate left "
              f"standing as evidence:\n  tempdir: {tmpdir}\n  schema:  {SCHEMA} / {KERN} / {ROLE} "
              f"(db {DB}@{PGHOST})")
        for f in failures:
            print(f"\n!! {f}")
        return 1

    _drop_scratch()
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\nasof-export fixture: all cases PASS, scratch substrate torn down to zero residue "
          f"(tempdir removed, schema {SCHEMA}/{KERN}/role {ROLE} dropped).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
