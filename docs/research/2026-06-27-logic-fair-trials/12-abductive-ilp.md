# 12 — Abductive Reasoning & Inductive Logic Programming — Fair Trial (first pass)

> Part of the autoharn **logic fair-trials** (the corrected, frontier-creed pass). Coined terms → root **[GLOSSARY.md](../../../GLOSSARY.md)**. The honest status of every verdict here is **undecided-until-the-experiment-runs** — see [README](README.md) and [AUDIT.md](AUDIT.md).

> **Audit verdict:** `deflated = False` · 3 defect(s) noted · **not rewritten** (the hardening pass was a no-op).

## Abductive Reasoning & Inductive Logic Programming — Fair Trial

The bet: when a perf-token flips to "regression" or a row trips a gate, autoharn should not just say UNSAT — it should *abduce* the minimal consistent cause-set, and over time *induce* the `_violations` gate itself from labelled ledger rows, with LLM authorship paying the encoding tax that killed these tools in 1995.

## Maximal ambition

The frontier claim is **self-extending deductive maintenance**: a Logic Safety Net that not only checks invariants but *proposes* them. Two capabilities the familiar stack cannot reach:

1. **Parsimonious, ranked root-cause as a first-class ledger artifact.** SQL/Z3 answer "is X true / is C satisfiable." Neither enumerates the *minimal sets of ground facts that would make the observation derivable under autoharn's causal theory*, ranked by Occam cardinality, with all co-optimal explanations surfaced. That is abduction's native output. For a regression token, autoharn emits not "FAIL" but "{dep_bump ∧ touched(solver_lib)} OR {dirty_tree} — two minimal explanations, status=suspect" — a provenance reading a maintainer can adjudicate, not a dead red light.

2. **Rule-4 compliance by construction.** Pillar 3's Rule 4 forbids gates that enumerate *instances*. A hand-written `WITH RECURSIVE` gate is one human's guess at the defect *class*. ILP (Popper/Aleph) *searches the hypothesis space* for the smallest program covering every labelled-bad row and excluding every labelled-good row — it returns the class predicate itself. The ambition: the ledger's own history of blessed/rejected findings becomes the training set, and the gate that polices future findings is *induced from* and *provably consistent with* that history. The safety net learns to write itself, and the induced clause is a falsifiable, version-pinned object — not folklore.

## The expressiveness gap (precise, not hand-wavy)

Honest and load-bearing, in two parts.

**Abduction — a real gap, in succinctness and search semantics.** Minimal-cardinality, all-co-optimal-models enumeration over a declared abducible set with integrity constraints is not something a SQL view *expresses* — it is a combinatorial minimization with model enumeration. You could bolt subset-minimization onto SQL only by materializing the powerset of abducibles and post-filtering: exponential blow-up and zero clarity. clingo's `{abducibles}` + `:- not observation` + `#minimize` states it in five lines and the solver does the search. Tested, runs on the installed 5.8.0:

```prolog
cause(dirty_tree). cause(dep_bump). cause(env_drift).
{ holds(C) : cause(C) }.
regression :- holds(dirty_tree).
regression :- holds(dep_bump), touched(solver_lib).
touched(solver_lib).
:- not regression.                 % integrity: must explain O
#minimize { 1,C : holds(C) }.      % Occam
```
→ two co-optimal explanations: `holds(dep_bump)` and `holds(dirty_tree)`, both cardinality 1.

**ILP — the gap is epistemic, not just syntactic.** SQL can only *check a rule you already wrote*. ILP answers a strictly harder question SQL cannot pose: *given examples, what is the rule?* That is the difference between verification and synthesis. Once induced, the rule is executable in plain SQL — so ILP's value is concentrated entirely at authoring time. That is a genuine capability (predicate invention, generalization to unseen rows), but it is honest to say the *runtime* gate it produces is ordinary. ILP earns its place as a **rule factory**, not a runtime engine.

## The falsifiable experiment (the trial)

**Setup.** Take 30+ real ledger findings with maintainer labels (bad = perf-claim token with no stored reading, or DIRTY-tree confirmed-pass). Background facts (`perf_token/1`, `no_reading/1`, `dirty/1`, `tree_clean/1`) come straight from the provenance ledger via a Datalog dump.

**Encoding (Popper).**
```prolog
% bias.pl
head_pred(bad_finding,1).
body_pred(perf_token,1).  body_pred(no_reading,1).  body_pred(dirty,1).
max_vars(2). max_body(2).
% examples.pl
pos(bad_finding(f12)).  neg(bad_finding(f07)).
% bk.pl  (from ledger)
perf_token(f12). no_reading(f12). dirty(f07). tree_clean(f12).
```
Expected induction: `bad_finding(X) :- perf_token(X), no_reading(X).`

**Abduction trial (separate, already runs):** the clingo theory above against a real regression event.

**Success criterion.** (a) Popper induces a rule that matches the maintainer's hand-written `_violations` gate on a held-out 20% test split with zero false-negatives; (b) abduction returns the maintainer-agreed minimal cause-set as one of its co-optimal answers on ≥4 of 5 historical regressions.

**KILL CONDITION (non-negotiable).** Retire ILP if, on the held-out split, the induced rule either (i) fails to recover the known gate predicate, or (ii) admits a labelled-good row (false-positive gate) in ≥2 of 5 cross-validation folds — i.e. it cannot match a rule a human already wrote correctly. Retire abduction if, across the 5 regressions, the *true* cause is absent from the co-optimal set in ≥2 cases (the abducible set is too brittle to be load-bearing) **and** widening the abducibles to fix it makes every event return ≥4 co-optimal explanations (no discriminating power). Either outcome is a failed experiment with data, not a familiarity argument.

## Neutralizing false authority (verification scaffolding)

The encoding is the attack surface, and it is an engineering problem with concrete, tested defenses:

- **Mutation fixtures (demonstrated).** I dropped the `:- not regression` integrity constraint and the solver happily returned the empty explanation set (`Optimization: 0`). A mutation fixture asserting "an explanation of cardinality 0 is impossible" *catches exactly this* mis-encoding. Every abducible theory ships with mutants (drop a constraint, drop a rule body) that MUST flip the answer; a green run on a mutant is a failed gate.
- **Metamorphic tests (demonstrated).** Removing `touched(solver_lib)` correctly dropped `dep_bump`, leaving only `dirty_tree`. Property: removing a background fact that licenses a cause must remove that cause from every co-optimal model. Runs in milliseconds; encodes the encoding's *intended* semantics independently of the LLM's prose.
- **Golden + held-out fixtures** for Popper: the induced rule is back-tested on rows it never saw.
- **Differential solver:** induce with Popper, re-derive the same examples with Aleph (inverse entailment); disagreement on the learned clause = halt.
- **Back-translation:** the induced clause `bad_finding(X):-perf_token(X),no_reading(X)` round-trips to English ("a finding is bad if it makes a perf claim with no stored reading") for maintainer sign-off before promotion.
- **Provenance + status lifecycle:** the theory/bias is a reading carrying `{commit,tree,session_id}`; induced rules enter **provisional**, never auto-promoted to CI. ≥1 abductive explanation = `suspect`, never `confirmed` — matching the paraconsistent shape.

## Verdict: phoenix or ash — and how we'll know

**Split verdict, both evidence-based. Abduction: phoenix** — the ranked-minimal-cause output is a real expressiveness gap, the five-line encoding runs *today* on the installed clingo, and the false-authority risk is already covered by mutation + metamorphic fixtures I executed. **ILP: undecided-until-trial**, leaning cautious-phoenix as a build-time rule factory, gated on the ledger reaching 30+ clean labelled rows. The single settling experiment is the Popper held-out cross-validation above. What flips ILP to ash: it cannot recover a gate a human already wrote correctly (the KILL condition) — that would prove the synthesis buys nothing over the human+SQL it claims to replace. What flips abduction to ash: the abducible set is either too brittle to contain the true cause or too loose to discriminate. Neither verdict is "use SQL instead" — abduction does something SQL cannot express, and that is the frontier we are testing.


---
*Verbatim first-pass output of the fair-trials workflow (run `wwr77eg5b`, claude-opus-4-8[1m]), 2026-06-27. The Witness — preserved un-corrected; read with the audit verdict above.*
