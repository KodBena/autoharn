# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-06T16:58:38Z
#   last-change: 2026-07-06T16:58:43Z
#   contributors: 37017f46/main
# <<< PROVENANCE-STAMP <<<

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
            for p in ("stale_attestation", "claimed_without_act", "unledgered_span")}


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
    # EXACT pre-registered atoms (PRE-REGISTERED-expectations.md Part 2, dishonest fixture)
    assert f["stale_attestation"] == {"stale_attestation(20,12)"}
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
