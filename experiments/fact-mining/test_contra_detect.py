#!/usr/bin/env python
"""The ADR-0013 Rule 5 artifact check: the contradiction demo is a CHECKABLE test,
not a narrated claim. Asserts the EXACT finding set the planted synthetic fixture must
produce — one hit per rule — and the decoys it must NOT produce (the gates suppress the
obvious false positives). ADR-0002 fail-loud: if a rule stops firing, or a decoy starts,
this test goes red.

Runs the REUSED extractor (``extract.build_nlp``/``doc_to_facts``) on the committed
fixture, then the pure ``contra_detect`` rules. No DB, no network — the detection logic
in isolation."""

from __future__ import annotations

from pathlib import Path

import pytest

import contra_detect as cd
import extract

FIXTURE = Path(__file__).parent / "fixtures" / "contra_synthetic.txt"


@pytest.fixture(scope="module")
def findings() -> list[cd.Finding]:
    nlp = extract.load_model("en_core_web_sm")
    doc = nlp(FIXTURE.read_text(encoding="utf-8"))
    bundle = extract.doc_to_facts(doc)
    claims = cd.claims_from_bundle(bundle)
    return cd.find_contradictions(claims)


def _sigs(findings: list[cd.Finding]) -> set[tuple[str, str, str]]:
    return {(f.rule, f.subj_key, f.pred) for f in findings}


def test_exactly_the_three_planted_findings(findings: list[cd.Finding]) -> None:
    # one planted hit per rule, on the canonical (subj_key, pred) the extractor computes.
    assert _sigs(findings) == {
        ("R-NEG", "socrate", "be"),       # "Socrates is a philosopher" / "... is not ..."
        ("R-FUNC", "capital", "be"),      # "The capital of France is Paris" / "... Lyon"
        ("R-NUM", "committee", "have"),   # "The committee has three members" / "... five ..."
    }


def test_each_rule_fires_once(findings: list[cd.Finding]) -> None:
    rules = sorted(f.rule for f in findings)
    assert rules == ["R-FUNC", "R-NEG", "R-NUM"]


def test_decoys_stay_silent(findings: list[cd.Finding]) -> None:
    sigs = _sigs(findings)
    # "Marie visited Paris / Lyon" — 'visit' is NOT on FUNCTIONAL_PREDS, so R-FUNC is silent.
    assert ("R-FUNC", "marie", "visit") not in sigs
    # "The shelf holds three books / three novels" — SAME number, so R-NUM is silent.
    assert ("R-NUM", "shelf", "hold") not in sigs
    # the control paragraph (library/staff/visitor) plants no clash — no findings touch it.
    control_subjects = {"library", "staff", "visitor", "garden"}
    assert not any(f.subj_key in control_subjects for f in findings)


def test_negation_finding_has_polarity_grounding(findings: list[cd.Finding]) -> None:
    neg = next(f for f in findings if f.rule == "R-NEG")
    assert "asserted" in neg.grounding and "denied" in neg.grounding
    assert "NOT" in neg.claim_b and "NOT" not in neg.claim_a  # B is the denied claim

def test_num_finding_carries_the_two_parsed_numbers(findings: list[cd.Finding]) -> None:
    num = next(f for f in findings if f.rule == "R-NUM")
    assert "3.0" in num.grounding and "5.0" in num.grounding


def test_func_finding_names_the_allowlist_entry(findings: list[cd.Finding]) -> None:
    func = next(f for f in findings if f.rule == "R-FUNC")
    assert "functional-by: 'be'" in func.grounding


# --- the transparent numeric parser, in isolation (it NEVER guesses) -------------
def test_parse_number_digits_and_spelled() -> None:
    assert cd.parse_number("three members") == 3.0
    assert cd.parse_number("5 members") == 5.0
    assert cd.parse_number("3.5 metres") == 3.5
    assert cd.parse_number("twelve") == 12.0


def test_parse_number_returns_none_when_no_number() -> None:
    # no sentinel-as-value: an object with no number cannot participate in R-NUM.
    assert cd.parse_number("Paris") is None
    assert cd.parse_number("a philosopher") is None
    assert cd.parse_number("") is None
