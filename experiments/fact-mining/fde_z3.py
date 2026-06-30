#!/usr/bin/env python
"""fde_z3 -- the SECOND logic-backend adapter, on a DIFFERENT engine (z3-solver),
proving the `logic_backend.LogicBackend` seam is engine-neutral over the SAME NLP
`Claim` substrate.

It encodes the R-NEG polarity contradiction in **Belnap-Dunn FDE / Priest's LP** via
the standard *two-bit* trick (`docs/research/2026-06-27-obligations-formalisms-survey/
formal-systems/25-paraconsistent-manyvalued.md`, the VERIFIED z3 encoding): each
canonical atom (subject, predicate, object) carries `_t` ("told true") and `_f`
("told false"); the four assignments are T(1,0), F(0,1), **Both(1,1)**, Neither(0,0).
A subject/predicate/object asserted (pos) AND denied (neg) yields told_true AND
told_false -> the atom's value is **Both** -- a contained, first-class, queryable
truth value, NOT ex contradictione quodlibet. The instance stays SAT (no explosion);
a classical `Bool a; assert a; assert (not a)` over the same atom is UNSAT and any
downstream `(=> false ...)` passes vacuously -- the exact lethal failure FDE removes
(see `classical_explodes` / `fde_contains` below).

WHAT IT IS / IS NOT (the honest earns-its-keep -- the AUDIT deflation discipline):
  * FDE's genuine win is **non-explosion + the queryable `both` value** (a downstream
    consumer can SEE the glut is contained and routed, not laundered). It is NOT a
    precision win: R-NEG is ALREADY the cheap SQL floor (`mining.contradiction`) and
    the ASP/Python R-NEG set. So this adapter does NOT claim to find more than ASP; it
    claims to find the SAME R-NEG set through a DIFFERENT paradigm/engine -- that
    agreement is the pluggability proof.
  * R-FUNC / R-NUM stay ASP's. They are functional-dependency defeasibility and
    numeric disequality -- NOT a paraconsistent many-valued concern, and forcing them
    into an FDE two-bit encoding would be unfaithful. They are flagged future work
    (`rules = {"R-NEG"}`), and the seam's `cross_engine_differential` runs only on the
    shared rule set, so this honest scoping is mechanical, not a hidden gap.

z3-solver 4.16.0 is installed; this imports `z3` directly (a real solve per atom, not
a Python shortcut). Conforms to `LogicBackend` structurally.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import z3  # type: ignore[import-untyped]

import contra_detect as cd
from logic_backend import LogicFinding


# ----------------------------------------------------- the FDE encoding's knobs --
@dataclass(frozen=True)
class FdeSemantics:
    """The three LOAD-BEARING discriminators of the two-bit FDE encoding, named as
    auditable knobs with their FAITHFUL defaults (`25-paraconsistent-manyvalued.md`).
    Production uses `DEFAULT`; the mutation gate (`test_logic_backend.py`) flips each
    knob and asserts the verdict changes -- the z3 analog of the ASP `.lp` text
    mutations. Each knob is a genuine semantic choice, so this is MORE honest than a
    blind text flip: a surviving mutant is a knob that did no work."""

    pos_value_t: bool = True   # a pos (asserted) source contributes told_TRUE evidence
    neg_value_f: bool = True   # a neg (denied)  source contributes told_FALSE evidence
    glut_is_both_bits: bool = True  # glut = told_true AND told_false (the FDE `Both` cell);
    #                                 the mutant (False) makes glut = told_true OR told_false
    join_is_or: bool = True    # Belnap join of evidence is OR (vs AND). LOAD-BEARING: a pos+neg
    #                            atom has a pos source with t=1 and a neg source with t=0, so the
    #                            join of the t-bits is True under OR but False under AND -- the
    #                            mutant (AND) collapses told_true and loses the real glut.


DEFAULT = FdeSemantics()


def _join(solver_bools: list[z3.BoolRef], use_or: bool) -> z3.BoolRef:
    """Belnap join of a polarity's evidence bits. Empty = no source spoke = False (the
    `Neither` floor for that bit). On a pos+neg pair the t-bits are {1, 0} (the pos
    source told-true, the neg source did not), so OR yields True and AND yields False --
    the join operator is load-bearing, not a relabeling."""
    if not solver_bools:
        return z3.BoolVal(False)
    return z3.Or(*solver_bools) if use_or else z3.And(*solver_bools)


# ------------------------------------------- the per-atom FDE two-bit evaluation --
def atom_is_glut(
    polarities: list[bool], sem: FdeSemantics = DEFAULT
) -> bool:
    """Run the two-bit FDE encoding for ONE canonical atom over its source claims
    (``polarities[i]`` is ``True`` for a pos source, ``False`` for a neg source) and
    return whether the atom's FDE value is **Both** (the contained glut).

    A genuine z3 solve, per the doc's verified encoding: each source gets a 2-bit
    value (pos = T(1,0), neg = F(0,1) under the faithful defaults), told_true /
    told_false are the Belnap joins, and `glut = And(told_true, told_false)`. The
    solver returns SAT (FDE never explodes) and the model's value of `glut` is read
    back -- the contained `Both`, surfaced as a Boolean a consumer can route on."""
    s = z3.Solver()
    t_bits: list[z3.BoolRef] = []
    f_bits: list[z3.BoolRef] = []
    for i, is_pos in enumerate(polarities):
        t = z3.Bool(f"t_{i}")
        f = z3.Bool(f"f_{i}")
        # each source has a DEFINITE 2-bit value (no free bits -> the glut is
        # determinate, not model-dependent). pos = (t,!f) by default; neg = (!t,f).
        if is_pos:
            s.add(t == z3.BoolVal(sem.pos_value_t), f == z3.BoolVal(not sem.pos_value_t))
        else:
            s.add(t == z3.BoolVal(not sem.neg_value_f), f == z3.BoolVal(sem.neg_value_f))
        t_bits.append(t)
        f_bits.append(f)
    told_true = _join(t_bits, sem.join_is_or)
    told_false = _join(f_bits, sem.join_is_or)
    glut = z3.And(told_true, told_false) if sem.glut_is_both_bits else z3.Or(told_true, told_false)
    g = z3.Bool("glut")
    s.add(g == glut)
    assert s.check() == z3.sat  # FDE is NON-EXPLOSIVE: the instance is always satisfiable
    model = s.model()
    return cast(bool, z3.is_true(model.eval(g, model_completion=True)))


# -------------------------------------------------------- non-explosion contrast --
def classical_explodes(polarities: list[bool]) -> bool:
    """The classical foil: assert the atom as ONE Bool, true for every pos source and
    false for every neg source. A pos+neg atom is then `a AND (not a)` -> UNSAT. Returns
    True iff the classical encoding is UNSAT (i.e. it 'explodes'). This is the win FDE
    buys: where this returns True, `atom_is_glut` returns True while staying SAT."""
    s = z3.Solver()
    a = z3.Bool("a")
    for is_pos in polarities:
        s.add(a if is_pos else z3.Not(a))
    return cast(bool, s.check() == z3.unsat)


def fde_contains(polarities: list[bool]) -> bool:
    """The earns-its-keep predicate, mechanical: on an atom the classical encoding
    EXPLODES (UNSAT), the FDE encoding instead CONTAINS the contradiction as a glut
    (SAT + value Both). True iff FDE strictly improves on classical here."""
    return classical_explodes(polarities) and atom_is_glut(polarities)


# --------------------------------------------------- the LogicBackend adapter ----
class FdeZ3Backend:
    """The SECOND adapter on the `logic_backend.LogicBackend` seam -- a DIFFERENT
    engine (z3) and a DIFFERENT paradigm (paraconsistent many-valued, where the
    contradiction is a first-class VALUE rather than a derived pair) onto the SAME
    `Claim` substrate. Covers ONLY R-NEG (the glut it faithfully encodes); see the
    module docstring for why R-FUNC/R-NUM stay ASP's. Conforms structurally."""

    name = "fde-z3"
    rules = frozenset({"R-NEG"})

    def __init__(self, sem: FdeSemantics = DEFAULT) -> None:
        self.sem = sem

    def analyze(self, claims: list[cd.Claim]) -> list[LogicFinding]:
        # group on the canonical atom (subj_key, pred, obj_key) -- the SAME grouping
        # the Python R-NEG rule uses; coref/entity-resolution is what unifies "France"
        # and "the country" onto one atom.
        by_atom: dict[tuple[str, str, str], list[int]] = {}
        for i, c in enumerate(claims):
            by_atom.setdefault((c.subj_key, c.pred, c.obj_key), []).append(i)
        out: list[LogicFinding] = []
        for ids in by_atom.values():
            # ask z3, PER PAIR, whether the two sources form an FDE glut. The glut
            # DECIDES the finding (no separate pos/neg gate) -- so the two-bit encoding
            # is genuinely load-bearing: a {pos,neg} pair is Both (emit), a {pos,pos} or
            # {neg,neg} pair is not (told_true xor told_false), exactly the pos x neg
            # cross product the Python/ASP R-NEG rule produces. The contained `both`
            # value rides on each finding (a consumer SEES the glut is contained).
            for x in range(len(ids)):
                for y in range(x + 1, len(ids)):
                    i, j = ids[x], ids[y]
                    pol = [not claims[i].negated, not claims[j].negated]
                    if not atom_is_glut(pol, self.sem):
                        continue
                    a, b = (i, j) if not claims[i].negated else (j, i)  # pos first (stable a/b)
                    out.append(
                        LogicFinding.from_claims(
                            "R-NEG", claims[a], claims[b], value="both", backend=self.name
                        )
                    )
        return out
