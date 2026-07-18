# 08 — Description Logic & Ontologies (OWL)

> Part of the autoharn **logics & automated-deduction investigation** — see the [index](README.md); coined terms (Pillar, *_violations gate, supersession, …) are defined in the root **[GLOSSARY.md](../../../GLOSSARY.md)**.

Description Logics (DLs) are decidable fragments of first-order logic for modeling a domain as **concepts** (classes), **roles** (binary relations), and **individuals**, with a reasoner that computes logical entailments (subsumption, classification, consistency). OWL 2 is the W3C-standardized, web-serialized DL family.

## Primer

You know Z3 proves "is this formula SAT over these theories." A DL reasoner answers a narrower, more *structural* question: given a **TBox** (schema axioms: `Solver ⊑ Capability`, `Capability ≡ Lib ⊔ Solver ⊔ Service ⊔ Venv ⊔ Script`, plus *disjointness* `Lib ⊓ Solver ⊑ ⊥`) and an **ABox** (facts: `z3 : Solver`), what is *necessarily* true? Two ideas matter. (1) **Open-world + terminology**: you assert partial knowledge and the reasoner *derives* the rest and *flags contradictions* — assert `z3 : Lib` and `z3 : Solver` and a disjointness axiom and it proves the ABox **inconsistent**, no enumeration of pairs needed. (2) **Subsumption/classification**: it auto-arranges your defined classes into a hierarchy from their *definitions*. DL is the right tool when your domain is a **controlled vocabulary with rich class-membership rules** and you want *membership and contradiction* derived, not when you need arithmetic/optimization (Z3/CP-SAT) or recursive graph reachability (Datalog).

## Applicability to autoharn

**Classification discipline (Pillar 1) — fit: medium-high.** The "lib xor solver xor service xor venv xor script" rule is *literally* a DL covering+disjointness axiom set. SQL can enforce a `CHECK kind IN (...)` but cannot *prove* a row violates xor when membership is *inferred* from other properties. Owlready2 (Manchester/Python syntax):

```python
class Capability(Thing): pass
class Lib(Capability): pass
class Solver(Capability): pass
AllDisjoint([Lib, Solver, Service, Venv, Script])
Capability.equivalent_to = [Lib | Solver | Service | Venv | Script]  # covering
z3 = Solver("z3"); z3.is_a.append(Lib)   # double-classified
default_world.inconsistent_classes()      # reasoner flags ⊥
```

This beats a Python script because the contradiction is a *machine-checked proof*, and beats Z3 because classification (the task-shape→tool hierarchy `feasibility ⊑ ProvableBySMT`) comes free from the class graph.

**Task-shape → blessed-tool mapping (Pillar 1) — fit: high.** Define tools by the *properties* of the task, let the reasoner assign:

```python
class FeasibilityTask(Thing): pass
class SMTSuitable(Thing):
    equivalent_to = [Task & (provesProperty.some(Feasibility))]
# reasoner derives FeasibilityTask ⊑ SMTSuitable, so "feasibility → Z3" is ENTAILED
```

This is the "eliciting mechanism" as *inference*: add a new task with a `provesProperty`, classification routes it automatically. SQL needs you to hand-write every mapping row; DL derives them from one defining axiom — directly serving Rule 4 (key on the *class* of task, never an enumeration).

**Status lifecycle / belief (cross-cutting) — fit: low-medium (forced).** `provisional ⊑ Belief`, `confirmed ⊑ Knowledge` is expressible, but DL is **monotonic and open-world**: it cannot *retract* an entailment when a finding is superseded, and cannot represent the **DIRTY/suspect third value** (paraconsistency) — a single contradiction makes the *whole* ABox inconsistent and every reasoner query becomes vacuously true (explosion). This is exactly the "gate exploding" failure the brief warns against. Datalog-with-negation or ASP fits supersession/non-monotonicity far better; honest verdict: **do not use OWL for the provenance ledger.**

**Provenance separation (Pillar 2) — fit: low.** "Measurement separate from interpretation" and `{commit, tree, session_id}` provenance is relational/temporal bookkeeping; OWL adds nothing over Postgres and its open-world assumption actively *hurts* (a missing `tree` is "unknown," not honest-NULL-you-can-gate-on).

**Meta-sweep ontology (Pillar 3) — fit: medium.** The "every rule DECLARES an enforcement surface (closed vocabulary incl. review-only)" is a small TBox; OWL's disjoint-union over `{ci-gate, lint, review-only, ...}` plus a class `MechanismWithoutSurface ≡ Rule ⊓ ¬declaresSurface.some` lets the reasoner *find* under-specified rules. But Postgres `WITH RECURSIVE` already prototypes the violation gates and keeps everything in one store — OWL only wins if the vocabulary grows rich definitional structure.

## Software to leverage

| tool | role | license | language / bindings | install cost | maturity | LLM-friendliness |
|---|---|---|---|---|---|---|
| **Owlready2** 0.50 | ontology authoring + reasoner driver, SQLite-backed | LGPL-3.0 | Python (native) | `pip install owlready2` | mature, active (2026) | high — Pythonic class syntax LLMs emit well |
| **HermiT** 1.3.8/5.x | full OWL 2 DL reasoner (consistency, classification) | LGPL | Java (bundled in Owlready2; OWLAPI) | bundled jar; needs JRE (OpenJDK 25 **present**) | mature, de-facto reference | medium — invoked via Owlready2 |
| **ELK** 0.6.0 | OWL 2 **EL** reasoner, polynomial, multicore | Apache-2.0 | Java (Protégé/OWLAPI/CLI) | jar download; JRE | mature | medium |
| **Konclude** | fast OWL 2 DL (tableau) reasoner | LGPL/research | C++ binary | **compile-from-source (heavy)** or prebuilt binary | mature, fastest in benchmarks | low — CLI only |

Local check: `owlready2` not yet installed (pip, cheap); `java` = OpenJDK 25 already present, so HermiT/ELK run out of the box. Recommendation: **Owlready2 + bundled HermiT** — single `pip`, no extra disk, Python-drivable from the same venv as Z3/CP-SAT.

## Limits & honest take

OWL helps *only* Pillar 1 (vocabulary + task→tool inference) and the meta-sweep TBox. It is the **wrong tool** for the provenance ledger, supersession chains, pre-registration temporality, and perf-claim substantiation — all non-monotonic, temporal, or relational, where DL's open-world monotonic semantics is a liability, not a feature.

**The false-authority risk is acute here.** An LLM that mis-models *one* axiom (e.g., forgets `AllDisjoint`, or writes `equivalent_to` where `is_a`/subclass was meant) produces a reasoner that **confidently returns the wrong classification with a "proof."** Owlready2's terse syntax makes `some` vs `only` vs `value` confusions easy and silent — a `restriction.only` typo doesn't error, it just changes the entailment. Open-world also surprises engineers: "the reasoner didn't say z3 is a Lib" means *unknown*, **not** *false*, so naïve gates built on absence are wrong. Mitigation: never trust a classification without (a) an asserted *positive* test ontology with known-good expected entailments, and (b) an asserted *inconsistency* canary. Hype to discount: "ontologies = automatic knowledge." The reasoning is real and decidable, but it only ever re-derives what your axioms already entailed — garbage TBox in, authoritative garbage out.

## References & learning

- **Baader et al., *An Introduction to Description Logic* (2017)** — the canonical textbook; teaches TBox/ABox, subsumption, and *why* DLs are decidable where FOL is not.
- **W3C *OWL 2 Primer* (2nd ed.)** — teaches the concrete OWL constructs (disjointness, covering, restrictions) you'd encode for the capability registry.
- **Owlready2 docs (lesfleursdunormal.fr / readthedocs 0.50)** — teaches the exact Python API, reasoner invocation, and SQLite store autoharn would use.
- **Abicht, "OWL Reasoners still useable in 2023" (arXiv:2309.06888)** — teaches which reasoners actually still run, sparing you dead-tool install cost.

Sources: [owlready2 PyPI](https://pypi.org/project/owlready2/), [Owlready2 reasoning docs](https://owlready2.readthedocs.io/en/latest/reasoning.html), [HermiT](https://github.com/owlcs/hermit-reasoner/), [ELK](https://github.com/liveontologies/elk-reasoner), [Reasoners 2023 survey](https://arxiv.org/pdf/2309.06888)


---
*Verbatim output of the `autoharn-logics-investigation` workflow (run `wf_6be06f87-68d`, model claude-opus-4-8[1m]), 2026-06-27 — one expert agent per logic family, grounded in autoharn. The maintainer should treat engine version/license claims as agent-reported (web-checked where noted), worth a confirm before install.*
