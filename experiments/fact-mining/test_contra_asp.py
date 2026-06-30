#!/usr/bin/env python
"""The encoding-trust gate for the ASP logic layer (contra_asp / logic_layer.lp).

The central risk (B-autoharn-fit s.5; ADR-0000): a mis-encoded logic layer fails
SILENTLY -- a confidently-green gate wearing a proof's costume. Three independent
checks close it, none of which trusts the .lp on its face:

  (a) GOLDEN -- the planted fixture must produce EXACTLY the known finding set.
  (b) MUTATION -- flip each load-bearing discriminator in the .lp; EVERY mutant
      MUST change the verdict on the fixture (a surviving mutant = a dead clause).
  (c) DIFFERENTIAL -- the clingo findings must MATCH find_contradictions() EXACTLY
      on the fixture AND on a real RFC; any divergence is an encoding bug surfaced
      BEFORE trust (ADR-0002 fail-loud).

It also pins the two ASP-over-SQL wins: defeasible R-FUNC (a multi_valued/2 fact
retracts a finding non-monotonically) and minimal-repair (a #minimize SQL cannot
rank). Requires the clingo CLI on PATH and en_core_web_sm.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import contra_asp as ca
import contra_detect as cd
import extract

pytestmark = pytest.mark.skipif(
    shutil.which("clingo") is None, reason="clingo CLI not on PATH"
)

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "contra_synthetic.txt"


@pytest.fixture(scope="module")
def claims() -> list[cd.Claim]:
    nlp = extract.load_model("en_core_web_sm")
    return cd.claims_from_bundle(extract.doc_to_facts(nlp(FIXTURE.read_text("utf-8"))))


def _rule_subj_pred(sigs) -> set:
    return {(r, s, p) for (r, s, p, _texts) in sigs}


# ============================================================== (a) GOLDEN =====
def test_golden_exactly_the_three_planted_findings(claims):
    # the SAME planted set test_contra_detect pins, re-derived by clingo.
    assert _rule_subj_pred(ca.asp_signatures(claims)) == {
        ("R-NEG", "socrate", "be"),
        ("R-FUNC", "capital", "be"),
        ("R-NUM", "committee", "have"),
    }


def test_golden_decoys_stay_silent(claims):
    sigs = _rule_subj_pred(ca.asp_signatures(claims))
    assert ("R-FUNC", "marie", "visit") not in sigs   # 'visit' not functional DATA
    assert ("R-NUM", "shelf", "hold") not in sigs      # same number, no mismatch
    assert not any(s in {"library", "staff", "visitor", "garden"} for (_, s, _) in sigs)


# ========================================================== (c) DIFFERENTIAL ===
def test_differential_synthetic_matches_oracle_exactly(claims):
    only_asp, only_py = ca.differential(claims)
    assert only_asp == set() and only_py == set()


@pytest.mark.parametrize("rfc", ["rfc791.txt", "rfc2616.txt", "rfc793.txt"])
def test_differential_real_rfc_matches_oracle_exactly(rfc):
    path = Path.home() / "distill" / "rfc" / rfc
    if not path.exists():
        pytest.skip(f"{path} not present")
    body = extract.normalise(extract.load_body(str(path), None))
    paras = [p.strip() for p in body.split("\n\n") if p.strip()][:400]
    cl = ca.claims_from_paragraphs(paras)
    only_asp, only_py = ca.differential(cl)
    # non-vacuous: this doc DOES contain contradictions (the gate is not empty==empty)
    assert ca.py_signatures(cl), f"{rfc} produced no findings -- pick a richer doc"
    assert only_asp == set() and only_py == set()


# ============================================================= (b) MUTATION ====
# Each mutation flips ONE load-bearing discriminator in logic_layer.lp. The mutant
# program MUST yield a different finding set on the fixture; a surviving mutant means
# that clause did no work (a dead clause silently passing). We mutate ONLY genuinely
# load-bearing tokens -- e.g. `A < B` is dedup-equivalent under the signature set and
# is HONESTLY excluded, not dressed up as a caught mutant.
_MUTATIONS = {
    "R-NEG polarity (neg->pos)":
        ("assertion(B,S,P,O,neg)", "assertion(B,S,P,O,pos)"),
    "R-FUNC object disequality (!=  -> ==)":
        ("Oa != Ob, A < B,", "Oa == Ob, A < B,"),
    "R-FUNC defeater negation (not exception -> exception)":
        ("A < B,\n                       not exception(S,P).",
         "A < B,\n                       exception(S,P)."),
    "R-FUNC allowlist gate (drop functional/1)":
        ("finding(func, A, B) :- functional(P),", "finding(func, A, B) :- "),
    "R-NUM value disequality (!=  -> ==)":
        ("number(A,Na), number(B,Nb), Na != Nb.",
         "number(A,Na), number(B,Nb), Na == Nb."),
}


def _findings_with_program(program_text: str, claims, tmp_path) -> set:
    lp = tmp_path / "mutant.lp"
    lp.write_text(program_text, encoding="utf-8")
    edb = ca.edb_from_claims(claims)
    atoms = ca.run_clingo([lp], edb)
    return {
        ca._signature(ca._TAG_TO_RULE[tag], claims[a], claims[b])
        for (tag, a, b) in ca._parse_finding_atoms(atoms)
    }


@pytest.mark.parametrize("name", list(_MUTATIONS))
def test_every_mutation_changes_the_verdict(name, claims, tmp_path):
    src = ca.LOGIC_LP.read_text(encoding="utf-8")
    old, new = _MUTATIONS[name]
    assert src.count(old) == 1, f"mutation target not unique: {name}"
    mutant = src.replace(old, new)
    baseline = ca.asp_signatures(claims)
    mutated = _findings_with_program(mutant, claims, tmp_path)
    assert mutated != baseline, f"SURVIVING MUTANT (dead clause): {name}"


# ==================================================== ASP-over-SQL: defeasible ==
def test_defeasible_func_a_multi_valued_fact_retracts_the_finding(claims):
    # SQL's mining.contradiction cannot express this: a single EDB fact, no program
    # edit, non-monotonically RETRACTS the R-FUNC capital finding (recursion-through-
    # negation). This is the genuine win over the SQL floor (B-autoharn-fit N15).
    base = _rule_subj_pred(ca.asp_signatures(claims))
    assert ("R-FUNC", "capital", "be") in base
    defeated = _rule_subj_pred(
        ca.asp_signatures(claims, extra_facts='multi_valued("capital","be").')
    )
    assert ("R-FUNC", "capital", "be") not in defeated      # retracted
    assert ("R-NEG", "socrate", "be") in defeated           # others untouched
    assert ("R-NUM", "committee", "have") in defeated


# ====================================================== ASP-over-SQL: repair ====
def test_minimal_repair_retracts_exactly_one_of_the_functional_pair(claims):
    ids = ca.minimal_repair(claims)
    capital_ids = {i for i, c in enumerate(claims)
                   if c.subj_key == "capital" and c.pred == "be" and not c.negated}
    assert len(ids) == 1                       # minimum-cardinality repair
    assert set(ids) <= capital_ids             # blame lands on the conflicting pair
