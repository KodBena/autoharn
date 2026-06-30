#!/usr/bin/env python
"""The encoding-trust gate for the STANDARDIZED logic-backend seam and its TWO
engine adapters (clingo/ASP + z3/FDE), over the SAME `FactBundle`/`Claim` substrate.

The fair-trials DEFLATION lesson (`docs/research/2026-06-27-logic-fair-trials/
AUDIT.md`): a correctness gate must be MECHANICAL, never a model's judgment. So none
of these trusts an encoding on its face:

  (a) PLUGGABILITY  -- both adapters satisfy the SAME `LogicBackend` Protocol and run
      through the SAME seam call on the SAME claims.
  (b) CROSS-ENGINE DIFFERENTIAL -- on the SHARED rule set (R-NEG), the z3/FDE engine,
      the clingo/ASP engine, AND the Python oracle agree EXACTLY, on the synthetic
      fixture AND a real RFC (rfc2616, which genuinely contains R-NEG -> non-vacuous).
  (c) FDE GOLDEN -- the planted R-NEG glut is the exactly-known finding set.
  (d) FDE MUTATION -- flip each load-bearing discriminator of the two-bit encoding;
      every mutant MUST change the verdict (an honest single-source/symmetry exclusion
      is named, like the ASP `A<B` exclusion).
  (e) NON-EXPLOSION -- the FDE earns-its-keep: where classical is UNSAT, FDE is SAT +
      a contained `both` value.

Requires en_core_web_sm; the ASP half additionally needs the clingo CLI (skipped if
absent). z3-solver and the FDE half need no external binary.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import contra_asp as ca
import contra_detect as cd
import extract
import fde_z3
import logic_backend as lb

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "contra_synthetic.txt"
_HAS_CLINGO = shutil.which("clingo") is not None
R_NEG = frozenset({"R-NEG"})


@pytest.fixture(scope="module")
def claims() -> list[cd.Claim]:
    nlp = extract.load_model("en_core_web_sm")
    return cd.claims_from_bundle(extract.doc_to_facts(nlp(FIXTURE.read_text("utf-8"))))


# ============================================================ (a) PLUGGABILITY ==
def test_both_adapters_satisfy_the_protocol():
    # structural conformance: both are LogicBackends by SHAPE (runtime_checkable).
    assert isinstance(fde_z3.FdeZ3Backend(), lb.LogicBackend)
    assert isinstance(ca.AspBackend(), lb.LogicBackend)


def test_fde_runs_through_the_seam(claims):
    # the FDE engine reached via the generic seam call (no z3 in this test's imports
    # path beyond the adapter) -- add-a-logic = one adapter, used uniformly.
    sigs = lb.signatures(fde_z3.FdeZ3Backend(), claims)
    assert ("R-NEG", "socrate", "be", tuple(sorted(("Socrates [be] a philosopher",
                                                     "Socrates [NOT be] a philosopher")))) in sigs


@pytest.mark.skipif(not _HAS_CLINGO, reason="clingo CLI not on PATH")
def test_asp_runs_through_the_seam(claims):
    sigs = lb.signatures(ca.AspBackend(), claims)
    rsp = {(r, s, p) for (r, s, p, _t) in sigs}
    assert rsp == {("R-NEG", "socrate", "be"),
                   ("R-FUNC", "capital", "be"),
                   ("R-NUM", "committee", "have")}


# ====================================================== (b) CROSS-ENGINE DIFF ====
def test_cross_engine_fde_vs_oracle_on_shared_rules(claims):
    # z3/FDE vs the independent Python oracle, on the shared rule set -- EXACT match.
    fde = lb.signatures(fde_z3.FdeZ3Backend(), claims, rules=R_NEG)
    ora = lb.oracle_signatures(claims, rules=R_NEG)
    assert fde == ora and fde, "FDE must equal the oracle on R-NEG (non-vacuous)"


@pytest.mark.skipif(not _HAS_CLINGO, reason="clingo CLI not on PATH")
def test_cross_engine_fde_vs_asp_synthetic(claims):
    # the headline: two DIFFERENT engines (z3, clingo) through ONE seam, SAME claims.
    only_fde, only_asp = lb.cross_engine_differential(
        fde_z3.FdeZ3Backend(), ca.AspBackend(), claims, rules=R_NEG
    )
    assert only_fde == set() and only_asp == set()
    # and non-vacuous: the shared signature really is present on both.
    assert lb.signatures(fde_z3.FdeZ3Backend(), claims, rules=R_NEG)


@pytest.mark.skipif(not _HAS_CLINGO, reason="clingo CLI not on PATH")
def test_cross_engine_fde_vs_asp_real_rfc():
    path = Path.home() / "distill" / "rfc" / "rfc2616.txt"
    if not path.exists():
        pytest.skip(f"{path} not present")
    body = extract.normalise(extract.load_body(str(path), None))
    paras = [p.strip() for p in body.split("\n\n") if p.strip()][:400]
    cl = ca.claims_from_paragraphs(paras)
    only_fde, only_asp = lb.cross_engine_differential(
        fde_z3.FdeZ3Backend(), ca.AspBackend(), cl, rules=R_NEG
    )
    # non-vacuous: rfc2616 genuinely contains R-NEG contradictions.
    assert lb.oracle_signatures(cl, rules=R_NEG), "rfc2616 produced no R-NEG -- pick a richer doc"
    assert only_fde == set() and only_asp == set()
    # three-way: FDE also equals the oracle on the real doc.
    assert lb.signatures(fde_z3.FdeZ3Backend(), cl, rules=R_NEG) == lb.oracle_signatures(cl, rules=R_NEG)


# ============================================================== (c) FDE GOLDEN ==
def test_fde_golden_exactly_the_one_planted_glut(claims):
    sigs = lb.signatures(fde_z3.FdeZ3Backend(), claims)
    assert {(r, s, p) for (r, s, p, _t) in sigs} == {("R-NEG", "socrate", "be")}


def test_fde_decoys_stay_silent(claims):
    # the pos-only / pos-pos decoys (capital, committee, marie, shelf) are NOT gluts:
    # a glut needs BOTH told-true and told-false on ONE atom.
    sigs = {s for (_r, s, _p, _t) in lb.signatures(fde_z3.FdeZ3Backend(), claims)}
    assert sigs == {"socrate"}


def test_fde_finding_carries_the_contained_both_value(claims):
    findings = fde_z3.FdeZ3Backend().analyze(claims)
    assert findings and all(f.value == "both" for f in findings)  # queryable glut, not explosion


# ============================================================ (d) FDE MUTATION ==
# Each mutation flips ONE load-bearing knob of the two-bit FDE encoding. The mutant
# MUST change the R-NEG glut verdict on the fixture; a surviving mutant = a knob that
# did no work (the z3 analog of the ASP `.lp` text mutations).
_MUTANTS = {
    "glut OR instead of AND (both-bits discriminator)":
        fde_z3.FdeSemantics(glut_is_both_bits=False),
    "pos source no longer told-true (pos polarity discriminator)":
        fde_z3.FdeSemantics(pos_value_t=False),
    "neg source no longer told-false (neg polarity discriminator)":
        fde_z3.FdeSemantics(neg_value_f=False),
    "Belnap join AND instead of OR (join discriminator)":
        fde_z3.FdeSemantics(join_is_or=False),
}


@pytest.mark.parametrize("name", list(_MUTANTS))
def test_every_fde_mutation_changes_the_verdict(name, claims):
    baseline = lb.signatures(fde_z3.FdeZ3Backend(), claims)
    mutated = lb.signatures(fde_z3.FdeZ3Backend(_MUTANTS[name]), claims)
    assert mutated != baseline, f"SURVIVING MUTANT (dead knob): {name}"


def test_honest_exclusion_is_genuinely_verdict_equivalent(claims):
    """The ONE honestly-EXCLUDED non-mutant, named so it is not dressed up as caught
    (the analog of the ASP `A<B` exclusion): the full T<->F symmetry
    (`pos_value_t=False` AND `neg_value_f=False` together) is a symmetric relabeling of
    the two bits -- it maps T<->F on every source, so a {pos,neg} pair is still Both and
    a same-polarity pair is still not. It SURVIVES (verdict-equivalent); excluded
    honestly, not claimed as a caught mutant."""
    baseline = lb.signatures(fde_z3.FdeZ3Backend(), claims)
    symmetry = lb.signatures(
        fde_z3.FdeZ3Backend(fde_z3.FdeSemantics(pos_value_t=False, neg_value_f=False)), claims
    )
    assert symmetry == baseline       # genuinely verdict-equivalent -> honest exclusion


# ========================================================== (e) NON-EXPLOSION ===
def test_fde_contains_what_classical_explodes():
    # the earns-its-keep, mechanical: a pos+neg atom is classically UNSAT (explodes),
    # FDE keeps it SAT and surfaces a contained `both`.
    assert fde_z3.classical_explodes([True, False]) is True     # a AND (not a) -> UNSAT
    assert fde_z3.atom_is_glut([True, False]) is True           # FDE: SAT + Both
    assert fde_z3.fde_contains([True, False]) is True
    # a consistent atom: classical SAT, FDE not a glut (no overclaim of containment).
    assert fde_z3.classical_explodes([True, True]) is False
    assert fde_z3.atom_is_glut([True, True]) is False
    assert fde_z3.fde_contains([True, True]) is False
