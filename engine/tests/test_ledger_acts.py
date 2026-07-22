"""test_ledger_acts -- the acts<->ledger consumers (ledger_acts.lp / acts_edb.py) against the
pre-registered oracle (harness/e15-build/PRE-REGISTERED-expectations.md Part 2), and the byte-identity
non-foreclosure proof (§1.6). The scratch runner ledger_acts_scratch.py is the executable oracle; this
pins the exact atom sets and the byte-identity so a regression is a red test (ADR-0013 Rule 5)."""
from __future__ import annotations

import tempfile
from pathlib import Path

import acts_edb
import ledger_acts_scratch as las
from ledger_differential import AGREE, DIVERGE_DEFECT, run_asp
from ledger_edb import export
from ledger_floor import floor_atoms

HERE = Path(__file__).resolve().parent


def _findings(atoms: set[str]) -> dict[str, set[str]]:
    return {p: {a for a in atoms if a.startswith(p + "(")}
            for p in ("stale_attestation", "stale_attest", "stale_nonattest",
                       "claimed_without_act", "unledgered_span")}


def test_honest_fixture_agrees_and_has_no_findings():
    las.setup(dishonest=False)
    res = las.acts_differential()
    assert res.verdict == AGREE, (res.only_asp, res.only_sql)
    f = _findings(res.asp)
    assert f["stale_attestation"] == set()
    assert f["claimed_without_act"] == set()
    assert f["unledgered_span"] == set()
    # base relations ARE present (non-foreclosure §1.1): act_ledgered 1..6 + claim_matched 30
    assert {a for a in res.asp if a.startswith("act_ledgered(")} == {f"act_ledgered({i})" for i in range(1, 7)}
    assert "claim_matched(30)" in res.asp


def test_dishonest_fixture_agrees_and_fires_each_consumer():
    las.setup(dishonest=True)
    res = las.acts_differential()
    assert res.verdict == AGREE, (res.only_asp, res.only_sql)
    f = _findings(res.asp)
    # EXACT pre-registered atoms (PRE-REGISTERED-expectations.md Part 2, dishonest fixture), UPDATED
    # per finding 49's odd-link diagnosis (autoharn ledger id 49, resolved oracle-drift-not-engine-
    # defect): the pre-registered oracle predates the dishonest fixture's finding-29 rows (21 = a
    # BLOCKING refusal of step2/11; 41 = the amend the refusal demanded), which legitimately add a
    # second, BENIGN member to the stale_attestation UNION (ledger_acts.lp's own comment: "stale_attestation
    # stays the UNION... only refinement, honestly"). ledger_acts_scratch.py's own main() already
    # asserts this split correctly (its `clean_split` check) -- this test previously only pinned the
    # unrefined union and had gone stale, not the engine. Pinning both the union AND its split members
    # closes the gap that pytest never actually exercised the verdict-aware refinement (finding 29).
    assert f["stale_attestation"] == {"stale_attestation(20,12)", "stale_attestation(21,11)"}
    assert f["stale_attest"] == {"stale_attest(20,12)"}       # 20 attests 12; 12 later amended by 40 -> load-bearing
    assert f["stale_nonattest"] == {"stale_nonattest(21,11)"}  # 21 refuses 11; 11 amended by 41 as demanded -> benign
    assert f["claimed_without_act"] == {"claimed_without_act(50)"}
    assert f["unledgered_span"] == {"unledgered_span(7,9)", "unledgered_span(11,11)"}


def test_honest_mutation_flips_red():
    las.setup(dishonest=False)
    edb = las.acts_edb(las.SCHEMA)
    with tempfile.TemporaryDirectory() as td:
        prog = las.mutated_program("honest_drop_claim_guard", Path(td))
        assert las.acts_differential(programs=prog, edb=edb).verdict == DIVERGE_DEFECT


def test_dishonest_mutation_flips_red():
    las.setup(dishonest=True)
    edb = las.acts_edb(las.SCHEMA)
    with tempfile.TemporaryDirectory() as td:
        prog = las.mutated_program("dishonest_drop_amends_stale", Path(td))
        assert las.acts_differential(programs=prog, edb=edb).verdict == DIVERGE_DEFECT


def test_banked_derivations_byte_identical():
    """§1.6: adding ledger_acts.lp changes NO banked s10-s13/nla atom (it is a separate program,
    never loaded for the banked targets' differential)."""
    # autoharn: the banked s10-s13/nla derivations are EVIDENCE-STAYS [A11] — read from the
    # claude_harness archive (read-only forever after the flip), like ledger_target's archive pins.
    d = Path("/home/bork/w/vdc/1/claude_harness/experiments/fact-mining/docs/ledger-marriage/derivations")
    for t in ("s10", "s11", "s12", "s13", "nla"):
        edb = export(t).edb_text()
        assert run_asp(t, edb).atoms == set((d / t / "asp_atoms.txt").read_text().split())
        assert floor_atoms(t) == set((d / t / "sql_atoms.txt").read_text().split())


def test_manifest_declares_families_loudly():
    """F49: every acts family declared PRODUCED or DEFERRED, never silent."""
    las.setup(dishonest=True)
    m = acts_edb.acts_manifest(las.SCHEMA)
    assert set(m) >= set(acts_edb.ACTS_PREDS)
    assert all(v.startswith(("PRODUCED", "DEFERRED")) for v in m.values())


def test_manifest_key_set_exactly_matches_acts_preds_db_free(monkeypatch):
    """F50 SSOT (ledger item acts-manifest-ssot-import-time): acts_manifest's key set literally
    equals ACTS_PREDS -- checked DB-free (no psql call, no scratch fixture build via las.setup()),
    unlike test_manifest_declares_families_loudly above which needs a live honest/dishonest
    fixture and only asserts a superset. acts_manifest()'s own `assert set(m) == set(ACTS_PREDS)`
    (acts_edb.py) is a call-time check, not an import-time one -- if a future consumer path stops
    calling acts_manifest() every run, drift detection goes silent again until something does.
    This pins the SAME invariant as a standalone, always-run unit test.

    Every capability probe (Target.has_relation / has_col) is monkeypatched to report absent, so
    every acts_manifest branch takes the DEFERRED path regardless of what schemas happen to exist
    on whatever DB is reachable -- no live DB connection is made at all. The schema name passed is
    ALSO one guaranteed never to exist (belt-and-suspenders with the mock, not a substitute for it)."""
    monkeypatch.setattr(acts_edb.Target, "has_relation", lambda self, qualified: False)
    monkeypatch.setattr(acts_edb.Target, "has_col", lambda self, col, table="ledger": False)
    m = acts_edb.acts_manifest("zz_acts_manifest_ssot_absent_schema_probe__db_free_test")
    assert set(m) == set(acts_edb.ACTS_PREDS)
    assert all(v.startswith("DEFERRED") for v in m.values())
