# 04 — Defeasible / Non-monotonic Reasoning & Formal Argumentation

> Part of the autoharn **logics & automated-deduction investigation** — see the [index](README.md); coined terms (Pillar, *_violations gate, supersession, …) are defined in the root **[GLOSSARY.md](../../GLOSSARY.md)**.

Logics where conclusions are *retractable*: adding new facts can withdraw a previously-derived conclusion (non-monotonic), and conflicting rules are resolved by priority/specificity rather than exploding into contradiction (defeasible / argumentation). The natural home for "defaults later overridden", supersession, and "conflicting advisories coexist".

## Primer

Classical logic (and Z3) is **monotonic**: once `p` is proven, no new axiom un-proves it; one contradiction makes *everything* provable. Real engineering belief isn't like that. "z3 is installed" holds *until refuted*; "ADR-7 says X" holds *until amended*. The core move is **negation-as-failure** + **defeat**: a rule fires *unless* a stronger rule or a refuting fact blocks it. Two concepts carry the weight: (1) a **default** = "conclude D unless you can show an exception" — encoded `usable(C) :- declared(C), not refuted(C).`; (2) **priority between rules** so two opposing conclusions don't deadlock — the more-specific / more-recent / higher-status rule *defeats* the other and you keep reasoning. Use this logic when truth is **provisional**, beliefs get **superseded**, and you must keep a usable answer while contradictions sit unresolved — exactly where a SQL `WHERE` clause forces you to hand-maintain "which row wins" and Z3's `unsat` just dies.

## Applicability to autoharn

**1. DEFAULTS later overridden + liveness as refreshable fact (PILLAR 1 / non-monotonic shape) — fit: HIGH.** A declared capability is presumed usable; a *refuted* resource belief must be superseded, not stale. This is the textbook default-with-exception. In clingo (installed, 5.8.0):

```prolog
usable(C) :- declared(C), not refuted(C).
refuted(C) :- liveness(C, dead, _).
% liveness(z3,"alive",s1). liveness(cvxpy,"dead",s2). declared(z3). declared(cvxpy).
```

Add `liveness(cvxpy,dead,_)` and `usable(cvxpy)` silently disappears — no row to hand-delete. Beats SQL because the retraction is *derived*, not a manual `UPDATE`; beats Z3 because `not` here is defeasible default-negation, not classical.

**2. SUPERSEDES chains: ADR amendments & provisional decisions (PILLAR 2, non-monotonic shape) — fit: HIGH.** Append-only findings where the latest live decision wins but priors are never rewritten:

```prolog
holds(D,V) :- decision(D,V,T), not overridden(D,T).
overridden(D,T) :- decision(D,_,T), decision(D,_,T2), T2 > T.
```

`holds/2` returns only the surviving decision while every `decision/3` row stays on disk — the ledger's "prior is never rewritten" invariant is *enforced by the reasoner*, not by trusting an author.

**3. Conflicting advisories / not-yet-corroborated findings COEXIST without the gate exploding (paraconsistency, the DIRTY tag, 3rd "suspect" value) — fit: HIGH.** This is the killer case. Two findings assert opposite things; classical logic gives `unsat` and the whole CI gate is meaningless. Defeasible status-priority keeps both rows yet yields a usable verdict:

```prolog
verdict(F,P) :- finding(F,P,confirmed).
verdict(F,P) :- finding(F,P,provisional), not finding(F,_,confirmed).
suspect(F)   :- finding(F,P,_), finding(F,Q,_), P!=Q.   % 3rd value, doesn't explode
```

`suspect/1` is the "unknown/DIRTY" third truth-value: contradictory findings surface *as data* instead of detonating the gate. A `<store>_violations` query (PILLAR 3) can then key on `suspect(F)` — the CLASS of "uncorroborated conflict" (Rule 4: structural, not an enumeration of instances). Plain SQL can compute this with a self-join, but the *open-world default* ("provisional holds unless a confirmed contradicts") is awkward to keep correct as rules grow; ASP makes it one stratified rule.

**4. Accountability: "why did this conclusion hold?" (PILLAR 2 provenance) — fit: MED.** `s(CASP)` (goal-directed ASP, SWI-Prolog pack) returns a **justification tree** for each answer — a literal proof of *why* `usable(z3)` survived and which refutation would kill it. That is a machine-checkable "reading-of vs interpretation" trail no SQL query yields. MED only because it overlaps the SQL ledger; its value is the *derivation*, not storage.

**5. HYPOTHESIS GENERATION for a regression (abduction) — fit: MED/forced.** s(CASP) and ASP with `#minimize` over abducibles can enumerate minimal explanations ("which dirty-tree commit explains the 12x→3x drop"). Honestly this is **better served by dedicated abduction/ILP tooling** (see that section); defeasible logic does it but it's not the sharpest tool — listed for honesty.

Where it's **forced**: classification discipline (PILLAR 1 `lib xor solver xor...`) is a *hard* mutual-exclusion constraint — use Z3/an integrity constraint, not defaults. Pre-registration's temporal "before/after" is better as a SQL timestamp check than a logic rule.

## Software to leverage

| tool | role | license | language / bindings | install cost | maturity | LLM-friendliness |
|---|---|---|---|---|---|---|
| clingo (Potassco) | ASP grounder+solver; defaults, defeat, integrity constraints, `#minimize` | MIT | C++; Python (`import clingo`), CLI | **already installed** (5.8.0; latest 5.8.1/6.0.0). `pip install clingo` / conda | very high, active | high — terse declarative rules, easy to generate & validate |
| s(CASP) | goal-directed ASP with **justification trees** + constraints | Apache-2.0 (SWI pack; Ciao-derived) | Prolog; SWI pack, CLI | light: `pack_install(scasp)` on SWI 9.3.31 (installed) | medium-high, research-grade | med — explanations are gold, syntax less familiar |
| SWI-Prolog | host for s(CASP); ad-hoc defeasible meta-interpreters | BSD-2-Clause | Prolog; C/Python (`janus`) | **already installed** (9.3.31) | very high | med |
| TweetyProject | abstract + structured argumentation (ASPIC+, DeLP) labelings/extensions | LGPL-3.0 | Java; CLI/JVM | medium: JVM jar, no pip | high (academic) | low-med — Java, verbose |
| SPINdle | dedicated standard/modal **defeasible logic** reasoner | LGPL (research) | Java | medium: jar | aging (less active) | low |

Recommendation: stay on **clingo** (zero install, MIT, Python-drivable) for the gates; add **s(CASP)** when the maintainer wants *explanations*. Skip the Java stack unless full ASPIC+ argument semantics are genuinely needed.

## Limits & honest take

- **Not for hard constraints.** Classification-discipline mutual exclusion and feasibility are crisp SAT/SMT jobs; doing them with defaults invites silent gaps. Defeasible logic is for *belief that changes*, not *facts that must hold*.
- **The false-authority risk is real and acute here.** An LLM writing `not refuted(C)` where it meant classical `-refuted(C)`, or mis-ordering a priority, yields a confident `usable(z3)` that is *wrong* — and ASP gives no type error, just a different answer set. A bad encoding launders a guess into a "proof". Mitigations: **always emit the s(CASP) justification** and diff it against the maintainer's intent; treat any reasoner verdict feeding CI as `review-only = presumptively decaying` until a human signs the rule.
- **Semantic subtlety.** Multiple answer sets (skeptical vs credulous) and grounding blow-up on large stores can surprise; the maintainer must pick a stance explicitly, not by accident.
- **Hype check:** "argumentation framework" sounds grander than the payoff for autoharn. The 80% win is plain non-monotonic defaults (needs 1–4 above) — full Dung/ASPIC+ machinery is overkill unless advisories form genuine attack cycles.

## References & learning

- *Knowledge Representation, Reasoning and Declarative Problem Solving* — Baral — teaches ASP defaults/negation-as-failure rigorously, the foundation under clingo.
- Potassco **clingo guide** (potassco.org/clingo) — teaches the exact syntax you'll ship, with `#minimize`/integrity-constraint patterns matching the `_violations` gates.
- Arias et al., *s(CASP)* (ceur-ws.org/Vol-2970/gdeinvited4.pdf) — teaches goal-directed ASP with justification trees, i.e. machine-checkable "why".
- Prakken & Vreeswijk, *Logics for Defeasible Argumentation* — teaches the defeat/priority theory if advisory-conflict modeling grows beyond simple defaults.

Sources: [clingo releases](https://github.com/potassco/clingo/releases/), [clingo LICENSE](https://github.com/potassco/clingo/blob/master/LICENSE.md), [sCASP pack](https://github.com/SWI-Prolog/sCASP), [s(CASP) for SWI-Prolog](https://ceur-ws.org/Vol-2970/gdeinvited4.pdf), [TweetyProject](http://tweetyproject.org/lib/), [SPINdle](https://research.csiro.au/bpli/tools/spindle/)


---
*Verbatim output of the `autoharn-logics-investigation` workflow (run `wf_6be06f87-68d`, model claude-opus-4-8[1m]), 2026-06-27 — one expert agent per logic family, grounded in autoharn. The maintainer should treat engine version/license claims as agent-reported (web-checked where noted), worth a confirm before install.*
