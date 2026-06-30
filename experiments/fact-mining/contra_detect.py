#!/usr/bin/env python
"""Contradiction detection — the transparent logic-layer FIRST PASS (NOT NLP-grade).

A pure function of the SSOT ``FactBundle`` that ``extract.doc_to_facts`` already
produces: it adds NO second parse and NO fact the extractor did not emit (ADR-0012
P1; ADR-0000). It normalises the bundle's triples into ``Claim``s (canonical keys +
surface + sentence + a TRANSPARENTLY parsed number) and runs three explicit rules
over claim pairs, each a pure predicate joining on the canonical keys the extractor
computed (the same keys ``mining.contradiction`` joins on).

Honesty posture (ADR-0002 / ADR-0009 — decisive here, an epistemic-state
interrogator must NOT invent the numbers it reports):

  * every ``Finding`` carries its ``rule`` id (R-NEG | R-FUNC | R-NUM) and a
    ``grounding`` string (the spans + the rule-specific evidence). THAT PAIR is the
    confidence — transparent provenance, not a probability.
  * there is NO score / probability field anywhere. The numeric parser NEVER guesses:
    an unparseable object leaves ``number=None`` and cannot match (no sentinel-as-value).
  * the functional-predicate judgement lives ENTIRELY in the explicit ``FUNCTIONAL_PREDS``
    allowlist, named in every R-FUNC finding's grounding — the precision control is
    visible, never hidden.

This is the demonstrator + the scaffold the logic layer (Prolog/ASP/SMT) later
replaces. It imports only ``extract`` (import-light: no spaCy at module scope) and the
stdlib; ``claims_from_bundle`` / ``find_contradictions`` touch no spaCy at all.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from itertools import combinations
from typing import Mapping

from extract import FactBundle

# --- the functional-predicate allowlist (the R-FUNC precision control) ----------
# Verb lemmas that admit AT MOST ONE object per subject (a hand-curated stand-in for a
# real functional-dependency declaration in ASP/SMT). The allowlist IS the precision
# control and is named in every R-FUNC finding's grounding, never hidden. A predicate
# not here does not fire by construction ("Marie visited Paris/Lyon" stays silent).
FUNCTIONAL_PREDS: frozenset[str] = frozenset(
    {"be", "equal", "bear", "locate", "situate", "capital"}
)

# --- the transparent numeric parser (R-NUM) -------------------------------------
# digits via float() + a small spelled-number map. No fuzzy NLP; an object that does
# not parse to a number leaves Claim.number = None and cannot match (ADR-0002: no
# sentinel-as-value, the system never guesses a number it did not read).
_SPELLED: dict[str, float] = {
    "zero": 0.0, "one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0, "five": 5.0,
    "six": 6.0, "seven": 7.0, "eight": 8.0, "nine": 9.0, "ten": 10.0,
    "eleven": 11.0, "twelve": 12.0,
}
_TOKEN = re.compile(r"[A-Za-z]+|\d+(?:\.\d+)?")


def parse_number(surface: str) -> float | None:
    """First parseable numeric value in ``surface``, else None (never a guess).

    Scans whitespace/word tokens left to right: a spelled number (``three``) or a
    digit literal (``3``, ``3.5``) returns its float; anything else is skipped. An
    object surface with no number yields None — it cannot participate in R-NUM."""
    for tok in _TOKEN.findall(surface.lower()):
        if tok in _SPELLED:
            return _SPELLED[tok]
        try:
            return float(tok)
        except ValueError:
            continue
    return None


# --- the normalised claim (the bridge type — a PURE function of the FactBundle) --
@dataclass(frozen=True)
class Claim:
    """Exactly what the rules read, ALL derived from the ``FactBundle`` (ADR-0000: it
    adds no fact the extractor did not already produce). ``subj_key``/``obj_key`` are
    the canonical (coref + entity-resolved) constants the rules join on; ``number`` is
    the transparent parse of ``obj_surface`` (or None)."""

    subj_key: str        # canonical subject constant — the join key
    pred: str            # verb lemma (the predicate)
    obj_key: str         # canonical object constant
    negated: bool        # spaCy `neg` dependency on the verb (already in TripleRecord)
    subj_surface: str    # human-readable subtree text (for grounding)
    obj_surface: str
    sent_i: int          # provenance: sentence index
    sent_text: str       # provenance: the source sentence
    number: float | None # parsed numeric value of the object, or None if not a number


def claims_from_bundle(bundle: FactBundle) -> list[Claim]:
    """``FactBundle`` -> ``list[Claim]`` (no re-parse). Zips each triple with its
    sentence text (by the doc-local sentence index), parses the object's number, and
    DROPS claims with an empty ``subj_key`` or ``obj_key`` (unresolved pronoun /
    punctuation — not usable constants), exactly as ``mining.fact_classical`` excludes
    them."""
    sent_text: dict[int, str] = {s["index"]: s["text"] for s in bundle["sents"]}
    claims: list[Claim] = []
    for t in bundle["triples"]:
        if not t["subj_key"] or not t["obj_key"]:
            continue
        claims.append(Claim(
            subj_key=t["subj_key"],
            pred=t["pred"],
            obj_key=t["obj_key"],
            negated=t["negated"],
            subj_surface=t["subj"],
            obj_surface=t["obj"],
            sent_i=t["sent"],
            sent_text=sent_text.get(t["sent"], ""),
            number=parse_number(t["obj"]),
        ))
    return claims


def _claim_text(c: Claim) -> str:
    """Compact human-readable reconstruction of a claim (the claim_a/claim_b cell)."""
    neg = "NOT " if c.negated else ""
    return f"{c.subj_surface} [{neg}{c.pred}] {c.obj_surface}"


# --- the finding (a candidate contradictory claim-pair a rule produced) ----------
@dataclass(frozen=True)
class Finding:
    """One candidate contradiction. Carries its ``rule`` id + ``grounding`` (the
    confidence — no probability field exists) and the source spans for the
    adjudicator. ``as_row`` is the wire to ``contra.finding`` (the cross-package
    coupling is THESE ROWS, not a Python import)."""

    rule: str            # 'R-NEG' | 'R-FUNC' | 'R-NUM'
    subj_key: str        # the canonical subject the two claims share (the join key)
    pred: str            # the predicate lemma the two claims share
    claim_a: str         # human-readable claim A
    claim_b: str         # human-readable claim B
    span_a: str          # the source sentence grounding claim A
    span_b: str          # the source sentence grounding claim B
    grounding: str       # the rule-specific evidence (allowlist entry / numbers / polarity)
    extra: Mapping[str, object] = field(default_factory=dict)

    def as_row(self) -> dict[str, str]:
        """The string row the store inserts into ``contra.finding`` (source_doc is
        added by the store, the one home for that provenance)."""
        return {
            "rule": self.rule,
            "subj_key": self.subj_key,
            "pred": self.pred,
            "claim_a": self.claim_a,
            "claim_b": self.claim_b,
            "span_a": self.span_a,
            "span_b": self.span_b,
            "grounding": self.grounding,
        }


def _finding(rule: str, a: Claim, b: Claim, grounding: str) -> Finding:
    return Finding(
        rule=rule,
        subj_key=a.subj_key,
        pred=a.pred,
        claim_a=_claim_text(a),
        claim_b=_claim_text(b),
        span_a=a.sent_text,
        span_b=b.sent_text,
        grounding=grounding,
        extra={"sent_a": a.sent_i, "sent_b": b.sent_i},
    )


def find_contradictions(
    claims: list[Claim], functional_preds: frozenset[str] = FUNCTIONAL_PREDS
) -> list[Finding]:
    """Apply the three transparent rules to claim pairs; return the findings.

    R-NEG  — polarity clash on (subj_key, pred, obj_key): one asserted, one denied.
    R-FUNC — differing obj_key on a functional predicate (both asserted), pred on the
             allowlist.
    R-NUM  — different parsed numbers on (subj_key, pred) (both asserted).

    Each rule groups on its canonical keys, then pairs within the group, so coref /
    entity resolution is what lets "France" and "the country" be the same subject.
    Findings are deduplicated by (rule, subj_key, pred, claim_a, claim_b)."""
    findings: list[Finding] = []
    seen: set[tuple[str, str, str, str, str]] = set()

    def emit(f: Finding) -> None:
        sig = (f.rule, f.subj_key, f.pred, f.claim_a, f.claim_b)
        rev = (f.rule, f.subj_key, f.pred, f.claim_b, f.claim_a)
        if sig in seen or rev in seen:
            return
        seen.add(sig)
        findings.append(f)

    # ---- R-NEG: group on (subj_key, pred, obj_key); pair asserted vs denied --------
    by_spo: dict[tuple[str, str, str], list[Claim]] = {}
    for c in claims:
        by_spo.setdefault((c.subj_key, c.pred, c.obj_key), []).append(c)
    for (sk, pred, ok), group in by_spo.items():
        pos = [c for c in group if not c.negated]
        neg = [c for c in group if c.negated]
        for a in pos:
            for b in neg:
                emit(_finding(
                    "R-NEG", a, b,
                    f"polarity clash on (subj_key={sk!r}, pred={pred!r}, obj_key={ok!r}): "
                    f"claim A asserted, claim B denied (spaCy neg dependency)"))

    # ---- R-FUNC and R-NUM: group on (subj_key, pred), assertions only --------------
    by_sp: dict[tuple[str, str], list[Claim]] = {}
    for c in claims:
        if c.negated:
            continue
        by_sp.setdefault((c.subj_key, c.pred), []).append(c)
    for (sk, pred), group in by_sp.items():
        for a, b in combinations(group, 2):
            # R-FUNC: functional predicate, differing canonical object
            if pred in functional_preds and a.obj_key != b.obj_key:
                emit(_finding(
                    "R-FUNC", a, b,
                    f"functional predicate {pred!r} (FUNCTIONAL_PREDS allowlist) with "
                    f"differing objects {a.obj_key!r} vs {b.obj_key!r}; functional-by: {pred!r}"))
            # R-NUM: both objects parse to a number, and the numbers differ
            if a.number is not None and b.number is not None and a.number != b.number:
                emit(_finding(
                    "R-NUM", a, b,
                    f"numeric mismatch on (subj_key={sk!r}, pred={pred!r}): "
                    f"{a.number} vs {b.number} (transparent parse of the object surface)"))

    return findings
