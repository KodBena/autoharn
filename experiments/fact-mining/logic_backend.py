#!/usr/bin/env python
"""logic_backend -- THE STANDARDIZED, PLUGGABLE LOGIC-BACKEND SEAM over the NLP
fact substrate.

This is the seam every logic plugs through. It is the direct analog of
`experiments/impedance/`'s `LibAdapter` (where "add a library = write one file"
over the numpy host interchange): here, "**add a logic = write one adapter**" over
the `FactBundle`/`Claim` interchange that `extract.doc_to_facts` ->
`contra_detect.claims_from_bundle` already produces. The `Claim` list IS the
logic-agnostic NLP interchange -- the analog of impedance's numpy-as-host carrier.
Every backend consumes ONLY that substrate and returns `LogicFinding`s; no backend
re-parses text, and no backend sees another engine's internals.

WHY a seam (the fair-trials breadth, made pluggable w.r.t. NLP): the
`docs/research/2026-06-27-logic-fair-trials/` survey enumerates 14 logic families.
Most will never share a solver -- ASP (clingo), SMT (z3), Datalog, defeasible
argumentation, etc. The maintainer's directive is that this breadth be "pluggable
w.r.t. NLP": each logic should attach to the SAME extracted-claim substrate through
ONE identical seam, so the choice of engine is an adapter detail, not a rewrite of
the pipeline. This module is that seam; `contra_asp.AspBackend` (clingo) and
`fde_z3.FdeZ3Backend` (z3) are the first two adapters, on DIFFERENT engines, proving
the seam is engine-neutral.

DEONTIC IS DELIBERATELY OFF THE MENU. This seam is for *reasoning over NLP-extracted
claims* -- consistency / contradiction / epistemic state (the CONSIST obligation of
`25-paraconsistent-manyvalued.md`). It is NOT for deontic obligation-*execution*
(detachment of duties, norm precedence, contrary-to-duty repair). Those live in a
different pillar (the obligations survey) and quantify over a state machine, not over
a bag of claims. A backend here answers "do these extracted claims conflict, and how
is the conflict contained?", never "what must the agent now do?".

THE DISCIPLINE (the fair-trials DEFLATION lesson -- `AUDIT.md`): a correctness gate
must be MECHANICAL, never a model's judgment. The seam ships the mechanism for that:
`cross_engine_differential` is a mechanical set-equality between two engines' findings
on the SAME substrate -- any divergence is an encoding bug surfaced before trust
(ADR-0000/INDEP: an independent channel that does not share the producer's bias).

LIBRARY-LIGHT: imports only `contra_detect` (the substrate types + the reference
oracle) and the stdlib. No clingo, no z3 -- those are each adapter's own lazy import.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

import contra_detect as cd

# The shared signature space. Both engines + the reference oracle land here; it is
# EXACTLY the tuple find_contradictions() dedups on (rule, subj_key, pred, claim_a,
# claim_b), made order-insensitive by sorting the two claim texts -- so A/B ordering
# and reverse-pair dedup cannot manufacture a false divergence. The ONLY thing under
# comparison is WHICH PAIRS each engine finds; the surfaces are identical by
# construction (every channel reuses contra_detect._claim_text).
Signature = tuple[str, str, str, tuple[str, str]]


@dataclass(frozen=True)
class LogicFinding:
    """One finding from a logic backend, in the engine-neutral seam shape.

    Carries the shared signature components (so any two engines are comparable
    without sharing a finding type) PLUS the many-valued ``value`` an engine derived
    on the atom -- e.g. ``"both"`` for an FDE/LP glut. ``value`` is the part a
    paraconsistent engine adds over a classical reject: a downstream consumer can SEE
    that the contradiction is a contained, queryable truth value, not an explosion.
    ``backend`` names the producing engine (for provenance in a mixed run)."""

    rule: str            # R-NEG | R-FUNC | R-NUM
    subj_key: str        # the canonical subject the two claims share (the join key)
    pred: str            # the predicate lemma the two claims share
    text_a: str          # human-readable claim A (contra_detect._claim_text)
    text_b: str          # human-readable claim B
    value: str | None = None   # derived many-valued truth value, e.g. "both" (FDE glut)
    backend: str = ""          # producing engine tag (provenance)
    extra: dict[str, object] = field(default_factory=dict)

    @property
    def signature(self) -> Signature:
        lo, hi = sorted((self.text_a, self.text_b))
        return (self.rule, self.subj_key, self.pred, (lo, hi))

    @classmethod
    def from_claims(
        cls, rule: str, a: cd.Claim, b: cd.Claim, *, value: str | None = None, backend: str = ""
    ) -> "LogicFinding":
        """Build from the two source ``Claim``s (an engine that pairs claims by id).
        ``a`` and ``b`` share ``subj_key``/``pred`` by construction of every rule, so
        ``a``'s are the finding's join keys."""
        return cls(
            rule=rule, subj_key=a.subj_key, pred=a.pred,
            text_a=cd._claim_text(a), text_b=cd._claim_text(b),
            value=value, backend=backend,
        )

    @classmethod
    def from_oracle(cls, f: cd.Finding, *, backend: str = "py-oracle") -> "LogicFinding":
        """Lift a reference ``contra_detect.Finding`` into the seam shape, so the
        Python oracle is itself just another backend the differential can compare."""
        value = "both" if f.rule == "R-NEG" else None
        return cls(
            rule=f.rule, subj_key=f.subj_key, pred=f.pred,
            text_a=f.claim_a, text_b=f.claim_b, value=value, backend=backend,
        )


@runtime_checkable
class LogicBackend(Protocol):
    """The STANDARDIZED seam every logic plugs into. Implement THREE members and you
    have an adapter:

      * ``name``  -- the engine tag (provenance).
      * ``rules`` -- the rule ids this engine derives. NOT every engine covers every
        rule: ``FdeZ3Backend`` deliberately covers only ``{"R-NEG"}`` (the
        paraconsistent glut it faithfully encodes), while ``AspBackend`` covers all
        three. ``rules`` is what makes a cross-engine differential HONEST -- it is run
        on the INTERSECTION of the two engines' rule sets, never forcing one engine to
        answer a rule it does not claim.
      * ``analyze(claims)`` -- consume the ``Claim`` substrate (the NLP interchange),
        return the findings. This is the whole obligation of "add a logic".

    Engine-SPECIFIC configuration (functional-predicate allowlist, defeaters, z3
    options) is constructor state on the concrete adapter, NOT in this Protocol --
    exactly as impedance keeps the per-library capability surface OFF the standardized
    seam. The seam pins the SHAPE of plugging in; the engine keeps its own knobs."""

    name: str
    rules: frozenset[str]

    def analyze(self, claims: list[cd.Claim]) -> list[LogicFinding]:
        ...


# ------------------------------------------------------------- the mechanical gate --
def signatures(backend: LogicBackend, claims: list[cd.Claim], rules: frozenset[str] | None = None) -> set[Signature]:
    """The set of finding signatures a backend produces, optionally restricted to
    ``rules`` (default: all the backend emits). The deduped set -- exactly the oracle's
    ``emit()`` semantics -- so duplicate-text pairs collapse identically on every
    engine."""
    out: set[Signature] = set()
    for f in backend.analyze(claims):
        if rules is None or f.rule in rules:
            out.add(f.signature)
    return out


def oracle_signatures(claims: list[cd.Claim], rules: frozenset[str] | None = None) -> set[Signature]:
    """The reference Python oracle's findings, in the SAME signature space -- the
    independent channel (ADR-0000/INDEP) both engines are differentialed against."""
    out: set[Signature] = set()
    for f in cd.find_contradictions(claims):
        if rules is None or f.rule in rules:
            out.add(LogicFinding.from_oracle(f).signature)
    return out


def shared_rules(a: LogicBackend, b: LogicBackend) -> frozenset[str]:
    """The rule ids BOTH engines claim -- the only honest ground for a cross-engine
    differential (do not ask z3 about R-FUNC if it does not claim R-FUNC)."""
    return a.rules & b.rules


def cross_engine_differential(
    a: LogicBackend, b: LogicBackend, claims: list[cd.Claim], rules: frozenset[str] | None = None
) -> tuple[set[Signature], set[Signature]]:
    """Return ``(only_in_a, only_in_b)`` over the shared rule set on the SAME
    ``Claim`` substrate. EMPTY-EMPTY == the gate passes: two DIFFERENT engines, on one
    NLP interchange, agree exactly on the contradiction signature. Anything else is an
    encoding bug surfaced before trust -- the mechanical (not model-judged) gate the
    fair-trials AUDIT lesson demands."""
    rs = rules if rules is not None else shared_rules(a, b)
    sa, sb = signatures(a, claims, rs), signatures(b, claims, rs)
    return (sa - sb, sb - sa)
