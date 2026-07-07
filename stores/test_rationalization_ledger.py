# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-06T15:59:19Z
#   last-change: 2026-07-06T15:59:19Z
#   contributors: 37017f46/main
# <<< PROVENANCE-STAMP <<<

"""test_rationalization_ledger -- the qualification gates for the rationalization ledger (Increment 3
item 5; db/harness/002_rationalization_ledger.sql + tools/file_rationalization.py). Every load-bearing
claim of the store is a mechanized check here, driven through the SAME filing CLI a detector fire uses
(so the demo and the gate agree), on a THROWAWAY schema dropped in teardown (never the real `harness`
corpus). These skip (not fail) when the harness host is unreachable -- a substrate verdict is not a
code verdict (ADR-0015 Rule 3).

Pinned invariants: idempotent re-file; finding IMMUTABLE (trigger); disposition APPEND-ONLY (F28,
trigger); the duplicate-of CHECK; the DERIVED current-label / confirmed views (id-is-order, the latest
act stands); and gen-known-cases (design lean (a): SEED + confirmed rows, no bootstrap loop when empty).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]   # autoharn: stores/<this> -> repo root (was parents[2] in fact-mining)
SCRIPT = REPO_ROOT / "filing" / "file_rationalization.py"   # autoharn: filing/ (was tools/)
PGHOST = os.environ.get("HARNESS_PGHOST", os.environ.get("EPISTEMIC_PGHOST", "192.168.122.1"))
DB = "harness"
SCRATCH = "rat_test_scratch"


def _db_up() -> bool:
    try:
        r = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-tAc", "SELECT 1;"],
                           capture_output=True, text=True, timeout=10)
        return r.returncode == 0 and r.stdout.strip() == "1"
    except Exception:  # noqa: BLE001
        return False


needs_db = pytest.mark.skipif(not _db_up(), reason="harness host unreachable (substrate, not code)")


def _cli(*args: str) -> str:
    r = subprocess.run([sys.executable, str(SCRIPT), "--schema", SCRATCH, *args],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"CLI failed: {r.stderr.strip()}"
    return r.stdout.strip()


def _psql(sql: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-tAc", sql], capture_output=True, text=True)


@pytest.fixture()
def store() -> "object":
    """A freshly-built throwaway rationalization store, dropped afterward. Never the real harness corpus
    (and the finding/disposition rows are immutable/append-only, so the schema MUST be dropped, not
    row-deleted, to clean up -- which is exactly the audit posture the store enforces)."""
    _psql(f"DROP SCHEMA IF EXISTS {SCRATCH} CASCADE;")  # declared-drop: {SCRATCH} (declared scratch/test reset; blast radius = this schema only)
    _cli("ensure-schema")
    yield None
    _psql(f"DROP SCHEMA IF EXISTS {SCRATCH} CASCADE;")  # declared-drop: {SCRATCH} (declared scratch/test reset; blast radius = this schema only)


@needs_db
def test_file_is_idempotent(store: object) -> None:
    """Re-filing the same (context, quoted, detector_version) returns the SAME finding_id -- one fire,
    one row (no duplicate corpus entries on a re-run)."""
    a = _cli("file", "--quoted", "scope creep, one notch deeper", "--register", "scope creep",
             "--context", "PR#1 gate", "--detector-version", "v1")
    b = _cli("file", "--quoted", "scope creep, one notch deeper", "--register", "scope creep",
             "--context", "PR#1 gate", "--detector-version", "v1")
    assert a == b and int(a) >= 1


@needs_db
def test_finding_is_immutable(store: object) -> None:
    """A finding is an audit fact: UPDATE and DELETE are refused by the trigger (the gap the out-of-frame
    audit found; a correction is a new finding + a duplicate-of disposition, never an in-place edit)."""
    fid = _cli("file", "--quoted", "q", "--register", "r", "--context", "c", "--detector-version", "v1")
    up = _psql(f"UPDATE {SCRATCH}.rationalization_finding SET register='X' WHERE finding_id={fid};")
    de = _psql(f"DELETE FROM {SCRATCH}.rationalization_finding WHERE finding_id={fid};")
    assert up.returncode != 0 and "IMMUTABLE" in up.stderr
    assert de.returncode != 0 and "IMMUTABLE" in de.stderr


@needs_db
def test_disposition_is_append_only(store: object) -> None:
    """F28: a disposition act is a fact -- UPDATE and DELETE are refused. A reversal is a NEW act."""
    fid = _cli("file", "--quoted", "q", "--register", "r", "--context", "c", "--detector-version", "v1")
    did = _cli("dispose", "--finding", fid, "--act", "confirmed-hack", "--actor", "bork")
    up = _psql(f"UPDATE {SCRATCH}.rationalization_disposition SET act='false-positive' WHERE disposition_id={did};")
    de = _psql(f"DELETE FROM {SCRATCH}.rationalization_disposition WHERE disposition_id={did};")
    assert up.returncode != 0 and "APPEND-ONLY" in up.stderr
    assert de.returncode != 0 and "APPEND-ONLY" in de.stderr


@needs_db
def test_duplicate_of_requires_target(store: object) -> None:
    """The CLI refuses `duplicate-of` with no target and a non-dup act WITH a target; the DB CHECK is the
    backstop (act='duplicate-of' <=> duplicate_of IS NOT NULL)."""
    fid = _cli("file", "--quoted", "q", "--register", "r", "--context", "c", "--detector-version", "v1")
    r = subprocess.run([sys.executable, str(SCRIPT), "--schema", SCRATCH, "dispose", "--finding", fid,
                        "--act", "duplicate-of", "--actor", "x"], capture_output=True, text=True)
    assert r.returncode != 0 and "duplicate-of" in r.stderr
    # DB backstop: a non-dup act carrying a target violates the CHECK.
    bad = _psql(f"INSERT INTO {SCRATCH}.rationalization_disposition (finding_id,act,duplicate_of,actor) "
                f"VALUES ({fid},'false-positive',{fid},'x');")
    assert bad.returncode != 0


@needs_db
def test_confirmed_view_is_latest_act(store: object) -> None:
    """id-is-order: the CURRENT label is the LATEST disposition; confirmed = current_act 'confirmed-hack'.
    A later false-positive act (F28: nothing auto-resolves; reversal is a new act) drops it from the
    confirmed set -- the view auto-revises, it is never a writable flag."""
    fid = _cli("file", "--quoted", "q", "--register", "r", "--context", "c", "--detector-version", "v1")
    _cli("dispose", "--finding", fid, "--act", "confirmed-hack", "--actor", "bork")
    got = _psql(f"SELECT finding_id FROM {SCRATCH}.rationalization_confirmed;")
    assert got.stdout.strip() == fid
    _cli("dispose", "--finding", fid, "--act", "false-positive", "--actor", "bork", "--note", "on review, not a hack")
    got2 = _psql(f"SELECT count(*) FROM {SCRATCH}.rationalization_confirmed;")
    cur = _psql(f"SELECT current_act FROM {SCRATCH}.rationalization_current WHERE finding_id={fid};")
    assert got2.stdout.strip() == "0"                 # newest act stands: no longer confirmed
    assert cur.stdout.strip() == "false-positive"


@needs_db
def test_gen_known_cases_seed_then_confirmed(store: object, tmp_path: Path) -> None:
    """gen-known-cases (design lean (a)): with zero confirmed rows the output is the SEED + the empty
    note (NO bootstrap loop); after a confirmed disposition the case is rendered from the corpus."""
    out = tmp_path / "kc.md"
    _cli("gen-known-cases", "--out", str(out))
    body = out.read_text(encoding="utf-8")
    assert "Case A — the per-producer gate" in body and "Case B — the stringly-typed error" in body
    assert "No confirmed cases in the ledger yet" in body      # empty corpus -> seed only
    fid = _cli("file", "--quoted", "the ownership model is scope creep", "--register", "scope creep",
               "--context", "PR#9 cardTree", "--detector-version", "v1", "--better-fix", "explicit owner")
    _cli("dispose", "--finding", fid, "--act", "confirmed-hack", "--actor", "bork")
    _cli("gen-known-cases", "--out", str(out))
    body2 = out.read_text(encoding="utf-8")
    assert f"Confirmed case #{fid}" in body2 and "the ownership model is scope creep" in body2
    assert "Case A — the per-producer gate" in body2           # seed always leads
