# 08 — Description Logic & Ontologies (OWL) — Fair Trial (first pass)

> Part of the autoharn **logic fair-trials** (the corrected, frontier-creed pass). Coined terms → root **[GLOSSARY.md](../../../GLOSSARY.md)**. The honest status of every verdict here is **undecided-until-the-experiment-runs** — see [README](../../../research/logic-fair-trials/README.md) and [AUDIT.md](../../../research/logic-fair-trials/AUDIT.md).

> **Audit verdict:** `deflated = False` · 2 defect(s) noted · **not rewritten** (the hardening pass was a no-op).
>
> ⚠️ **Mechanical re-check flags this as a possible false-negative**: the auditor marked it `deflated=false`, yet 1 of its own defects cite reducible-only / concession tells.

## Description Logic & Ontologies (OWL) — Fair Trial

The bet on trial: that autoharn's Capability Registry and meta-sweep are not tables but a **terminology with definitional structure**, and that an OWL 2 DL reasoner can *derive* tool-membership, *entail* necessary conditions, and *prove* classification contradictions that a SQL view can only re-assert by hand — with LLM authorship removing the axiom-writing tedium that historically killed DL adoption.

## Maximal ambition

The frontier capability is a **self-classifying, contradiction-proving intent SSOT**. Today the Registry's "what does this tool prove" column is hand-maintained: a human writes the row `feasibility → Z3`. The maximal DL version is that **no mapping row is ever written** — you assert the *definitions* once (`SmtBlessable ≡ Task ⊓ ∃requires.DecidableProperty`, `Solver ⊑ ∃proves.DecidableProperty`) and the reasoner *entails* every routing decision, including ones nobody anticipated. When the LLM adds a new task with `requires some Feasibility`, classification routes it to Z3 *as a theorem*, not as a lookup the maintainer forgot to add. I verified this runs: an individual `t1` asserted only with `requires feas` was inferred into `FeasibilityTask` by HermiT with zero membership assertion.

Beyond routing, DL gives **machine-checked necessary-condition proofs over an open world**: "every `BlessedFor(SmtTask)` capability *must* `proveProperty some Decidable`" becomes an axiom whose violation makes the ontology *inconsistent* — a proof, with a justification set, that a registry entry is malformed. The most ambitious target is the **meta-sweep as a TBox theorem**: `RuleWithoutSurface ≡ Rule ⊓ ¬(∃declaresSurface.EnforcementSurface)` lets the reasoner *find* every under-mechanized discipline rule as a classified concept, keyed on the *class* of the defect (Rule 4), not an enumeration. This is the eliciting mechanism reified as deduction: the registry stops being a list the agent reads and becomes a theory the agent *queries for entailments*.

## The expressiveness gap (precise, not hand-wavy)

The honest, defensible gap is **three-fold and real**, not "nothing SQL can't do":

1. **Classification of *inferred* membership.** SQL `CHECK kind IN (...)` enforces xor only over a *stored* column. DL detects the violation when membership is *derived* from other properties — `bad` was asserted only as `Solver` and `Lib`; the `AllDisjoint` axiom made the whole ABox inconsistent (verified, `OwlReadyInconsistentOntologyError` raised). To replicate in SQL you must materialize every inference rule as a view *and* hand-write the pairwise disjointness check — the succinctness collapses as the vocabulary grows, and you lose the *proof* (a justification subset of axioms).

2. **Necessary conditions under the Open-World Assumption.** SQL is closed-world: absence = false. DL distinguishes *unknown* from *false*, so "this capability has no recorded `proves` edge" does not silently pass a gate — a key for a registry that is honest about partial knowledge. This is also the gap's *danger* (see below).

3. **Decidable subsumption.** "Is concept A necessarily a sub-kind of concept B given the axioms?" is decidable in OWL 2 EL in polynomial time and is *not* a SQL query at all — it is theorem-proving over the schema.

Where the gap **honestly closes**: the Provenance Ledger. Supersession is non-monotonic; OWA monotonic DL *cannot retract* an entailment and a single contradiction explodes the ABox (every query vacuously true). That is not a SQL win — it is an **ASP/Datalog-with-negation** win. The correct architecture is *layered*, not retreating: DL owns the static TBox; ASP owns the supersession chain. Scoping DL to where its semantics is an asset is the rigorous move, not the cowardly one.

## The falsifiable experiment (the trial)

**Setup.** Encode the real Registry vocabulary (`Lib|Solver|Service|Venv|Script` covering+disjoint) and the meta-sweep rule ontology in Owlready2 + bundled HermiT (installed and **passing** under OpenJDK 25, `owlready2-0.51`). Load the actual blessed-tool table and the actual discipline-rule list from autoharn.

**Encoding** (runs today):
```python
AllDisjoint([Lib, Solver, Service, Venv, Script])
Capability.equivalent_to = [Lib | Solver | Service | Venv | Script]
class FeasibilityTask(Task):
    equivalent_to = [Task & requires.some(Feasibility)]   # routing-by-entailment
class RuleWithoutSurface(Rule):
    equivalent_to = [Rule & Not(declaresSurface.some(EnforcementSurface))]
```

**Success criterion.** (a) Reasoner infers ≥1 task→tool routing that is *not* asserted (proved possible: `t1`). (b) Reasoner flags ≥1 *real* registry malformation (e.g. a tool double-kinded, or a `BlessedFor` lacking its necessary `proves` edge) that the current `CHECK` constraints miss. (c) `RuleWithoutSurface.instances()` returns exactly the rules a human audit confirms are unmechanized — zero false negatives.

**KILL CONDITION (non-negotiable).** Retire OWL for autoharn if *either*: **(K1)** the only violations the reasoner finds are ones a single SQL `CHECK`/`GROUP BY HAVING` already catches — i.e. the inferred-membership cases (3 above) never actually arise in the real registry because all membership is stored, not derived — making the expressiveness moot in *practice*; **OR (K2)** the meta-sweep TBox cannot be authored without `≥1` axiom that, when mutated by the mutation harness below, *changes the entailment without any fixture catching it* AND the maintainer cannot read the back-translation to verify it — i.e. false authority proves un-neutralizable here.

## Neutralizing false authority (verification scaffolding)

The "LLM mis-encodes one axiom, gate wears false authority" objection is the central engineering problem, and DL is unusually *amenable* to solving it because the reasoner emits proofs:

- **Mutation fixtures.** For each axiom, an automated mutant (`some`→`only`, drop an `AllDisjoint`, `equivalent_to`→`is_a`). Each mutant **must** flip at least one golden entailment-assertion or one inconsistency-canary; a surviving mutant is a hole in the test set, failing the gate. This directly attacks the silent `some/only` confusion the prior section flagged.
- **Inconsistency canary + positive-entailment fixtures.** A known-bad ABox that *must* raise `OwlReadyInconsistentOntologyError` (verified working) and a known-good ABox with expected `instances()` — both run before any real query is trusted.
- **Differential reasoners.** Cross-check HermiT vs ELK (EL fragment) vs Konclude on classification; divergence = encoding in a fragment the LLM misjudged.
- **Justification-carrying output.** `explain` the axiom subset behind every entailment; store it as a **reading-with-provenance** (`{commit, tree, session_id}`), so the proof, not just the verdict, is auditable.
- **Back-translation.** Render each axiom to Manchester English (`Capability that proves some Decidable…`) for maintainer sign-off — the gate's authority is conditioned on a human having read the *meaning*.

## Verdict: phoenix or ash — and how we'll know

**Phoenix — narrowly and confidently, for Pillar 1's TBox and the meta-sweep; ash for the ledger.** The reasoner runs *today* (verified), the killer features (inferred-membership contradiction, routing-by-entailment, classified rule-gaps) are genuine and non-trivially-SQL, and false authority is here an *engineering problem with proof-carrying answers*, not an excuse. The single settling experiment is **K1**: load the real registry and meta-sweep and measure whether inferred-membership violations *actually occur*. If they do, DL earns a permanent frontier seat as the registry's reasoning core; if every membership is stored and no entailed contradiction ever fires, K1 retires it as elegant-but-inert. What flips me to ash: K1 empty *and* mutation testing (K2) showing the meta-sweep axioms are un-auditably fragile. What deepens the phoenix: a real entailed routing decision no human had written.


---
*Verbatim first-pass output of the fair-trials workflow (run `wwr77eg5b`, claude-opus-4-8[1m]), 2026-06-27. The Witness — preserved un-corrected; read with the audit verdict above.*
