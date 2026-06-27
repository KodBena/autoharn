# C — Qualifying an LLM-authored encoding at life-critical stakes

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Coined terms → root **[GLOSSARY.md](../../../GLOSSARY.md)**. See the [index](README.md).

I have verified the local toolchain (Z3 4.16.0, clingo 5.8.0, SWI-Prolog 9.3.31, OpenJDK 25, z3-solver 4.16.0.0 in Python; note: `ortools` and `jax` are NOT importable from the system `python3` — they live in a separate env, a fact the qualification harness must itself pin). Here is the synthesis section.

---

## Qualifiable LLM-Authored Encoding at Life-Critical Stakes — the Discipline that Gates the Gates

Every other section in this survey ends with the same confession in different words: *the solver is sound; the encoding is on trial.* Z3's `unsat` is a proof over its model, TLC's green is exhaustive over its model, the deontic justification tree is valid for the fact base it was handed — and in autoharn an LLM wrote the model, the fact base, the `.lp`, the `.tla`, the SMT-LIB. The encoding is the single largest unmitigated attack surface in the deliverable, and the thing that makes it dangerous is precisely that it *looks like the discharge*. This section is the cross-cutting obligation discharge for **INDEP, CALIB, and RECORD as they apply to the encoding artifact itself**: a reusable, mechanical, DO-178C-flavored qualification discipline that an LLM-authored formal encoding must pass *before it is allowed to gate anything*, plus the runnable checklist.

The organizing principle is hard-won and was proven in this session: **an LLM judge shares the bias it is meant to catch.** The deflation-detector deflated — a model asked to find the over-claim in model-authored text ratified the over-claim. Therefore *no step in this discipline may rest on a model's judgment of a model's output.* Every gate below terminates at a mechanism with no common cause with the author: a different solver codebase, a syntactic transformation, a property that holds or fails by execution, or a human-admitted axiom. This is the Löb/GL guardrail (§Provability Logic) made operational: a verdict whose support resolves back to its own author is worthless, so every gate's support chain is converse-well-founded down to a non-LLM oracle.

### Primer: what "qualifying an encoding" means and why it is not "testing the system"

DO-178C distinguishes *verifying the software* from *qualifying the tool that verifies the software*. A tool whose output you trust **in lieu of** doing the check yourself (TQL-1/criteria-1) must itself be qualified to a standard as high as the thing it clears. An LLM-authored encoding is exactly such a tool: autoharn trusts `souffle --provenance` or a Z3 `unsat` *instead of* re-deriving the property by hand, so the encoding inherits the criticality of the obligation it gates. The qualification question is therefore **not** "is the system correct?" (that is what the encoding is *for*) but two prior questions:

1. **Faithfulness (the translation problem):** does the formal artifact *mean* what the obligation says? A faithful-looking SMT model of an unfaithful abstraction is the lethal case — `unsat` (green) on a property the real system violates, because the encoding quietly dropped the bound, weakened the antecedent to `False`, or modeled a `0..100` integer where the silicon has a float. This is CALIB's "false authority" reborn one level up, and it is *invisible to the solver*, which faithfully proves whatever it was handed.
2. **Sensitivity (the vacuity problem):** does the artifact actually *constrain*? A theorem with an unsatisfiable antecedent `Qed`s trivially; an integrity constraint over an empty grounding is vacuously satisfied; a `□φ` over a frame with no reachable bad state passes by abstraction. The encoding can be *valid and meaningless*.

Faithfulness and sensitivity are the two failure axes; the four techniques below attack them mechanically, and the checklist is their conjunction.

### The four mechanical techniques (and the one forbidden one)

**1. Differential solving (kills solver-error and some faithfulness error; the INDEP backbone).** Compile the *same source-of-truth obligation* into two engines with no common code lineage and require bit-identical verdicts on every fixture. This is leverageable *today* on the installed stack because nearly every formalism in this survey has a dissimilar second host:

| Obligation family | Primary | Dissimilar differential oracle |
|---|---|---|
| PROV/TRACE/AUTH (Datalog/ASP) | clingo 5.8.0 | Soufflé (UPL) / SWI tabled Prolog / Postgres recursive |
| INV/STRUCT/COHERE (SMT) | Z3 4.16.0 | cvc5 (different codebase, Alethe proofs) |
| INV/PROG (temporal) | NuSMV / TLC | Spot `ltlcross`; Apalache (Z3-backed) vs TLC |
| CLASS/CONSIST (finite) | OR-Tools CP-SAT | MiniZinc → Chuffed/Gecode; clingo |
| Argumentation (AF) | clingo encoding | µ-toksia (SAT-based, no common solver) |
| Causation (HP) | HP2SAT | clingo witness-search encoding |

A disagreement does not tell you *which* engine is right — it tells you the **encoding is disqualified until reconciled.** Differential agreement is necessary, not sufficient: two engines fed the *same mis-translation* agree on the wrong answer (common-cause through the shared encoding). That is why differential solving alone never clears the bar.

**2. Mutation + golden fixtures (kills sensitivity/vacuity — the load-bearing gate).** Two distinct mutation campaigns, because they catch different failures:

- **System-mutation (faithfulness-of-direction):** inject seeded faults into the *system under analysis* — off-by-one in `RELEASE`, sign flip, dropped bound, a deploy without approval, a superseded-encounter flag. Require the encoding to **flip green→red on every one.** A mutant that stays green means the encoding does not see the bug class it claims to gate. (Pre-register the mutant set; require, e.g., a fixed kill rate ≥ the obligation's residual-risk budget.)
- **Encoding-mutation (sensitivity):** mutate the *encoding itself* — delete a `blocked` clause, flip a default, weaken `inflow ≤ RELEASE` to `inflow ≤ 200`, change `[0,60]` to `[0,∞]`, drop a `DisjointClasses` axiom, replace the invariant with `True`. Require the **golden fixture set to break** on every mutation. A mutation that leaves all verdicts unchanged means the corresponding clause is dead — the check is insensitive to the very thing it claims to enforce. This is the single most diagnostic gate, because it directly attacks the vacuity failure that no solver and no second solver can see.

Mutation score is the qualification metric. A pre-registered threshold (this survey's sections converge on ~95% for catch-rate, 100% for the safety-critical seeds) is the pass/fail line, and it is *mechanical* — a count of caught mutants, not a judgment.

**3. Back-translation / round-tripping (kills faithfulness without a human re-reading the formula).** The encoding `E(obligation)` is suspect because the LLM wrote it; asking the *same* LLM "does this encode the obligation?" is the deflation trap. Instead, mechanically generate **concrete witnesses** from the formal artifact and check them against an independently-specified oracle:
- For an `unsat` (a universal claim), perturb to force `sat` and require the **countermodel** to be a hand-recognizable instance of the hazard (Z3 `get-model`, TLC's shortest counterexample trace, the CP-SAT counterexample point). A countermodel that is *not* a real hazard instance means the model's state space is wrong.
- For a `sat`/accepted claim, replay the **proof object / justification tree / derivation** (souffle `--provenance`, s(CASP) justification, Z3 `get-proof` replayed in a *different* checker, Lean's kernel) and require every leaf to be an admitted axiom or primary datum — no free-floating edge. This is the Justification-Logic discipline (§JL): the witness term cannot lie, because re-checking is a syntactic operation independent of how the term was produced.
- For temporal/conformance claims, synthesize a **runtime monitor** from the LTL/STL spec and replay it against the *executable artifact* (RTAMT over real traces, a refinement check model ⊑ code). A model that does not refine the artifact is narration; the monitor catches the abstraction gap the model checker cannot.

The defining property of back-translation: the witness's validity is decided by *execution or by an oracle the LLM did not author*, so it does not share the encoding's bias.

**4. Encoding-as-reading-with-provenance (makes faithfulness auditable line-by-line).** The encoding must ship as a literate artifact where **every formal clause carries a provenance edge to the exact obligation-text span it discharges**, and the union of edges must *cover* the obligation (no unmapped requirement → TRACE; no clause without a mandate → no smuggled assumption). This is a Datalog/coverage check, not a reading: `:- obligation_clause(C), not covered_by(C, _).` over the link table must be UNSAT, and `:- encoding_clause(E), not justifies(E, _).` likewise. The point is not that a human reads the formula — at Fed/NASA scale they won't read all of it — but that the *coverage relation is itself a mechanical gate* and any LLM-introduced clause with no obligation behind it (a "comfortable spec," an antecedent quietly strengthened) shows up as an uncovered or unjustified edge. Pair with RECORD: the provenance table, the fixture corpus, the mutation log, and the solver verdicts are written at gate-time into a tamper-evident, happens-before-ordered record (criterion before result, fixture-set frozen before the verdict it clears).

**The forbidden technique: LLM-as-judge.** No gate may be "ask a model whether this is faithful/vacuous/correct." The deflation-detector result is the kill-proof: the auditing model shares the authoring model's blind spot and ratifies. A model may *propose* fixtures, mutations, or provenance links (cheap generation), but the *verdict* on every one must be rendered by a solver, an execution, a syntactic checker, or a human-admitted axiom. If a step's pass/fail cannot be reduced to one of those four, it is not a gate.

### The concrete qualification checklist (a harness encoding must pass ALL before it gates anything)

```
QUAL-0  PROVENANCE OF THE TOOLCHAIN.  Every engine pinned by version AND content hash;
        every interpreter/env pinned (note: ortools/jax here live in a separate env, not
        system python3 — pin the venv). Lockfile committed. Non-"releases" tools (RTAMT,
        Popper) pinned to a commit SHA. A floating dependency is an unqualified tool.

QUAL-1  OBLIGATION→ENCODING COVERAGE.  Bidirectional link table; mechanically check
        (Datalog/clingo) that every obligation span maps to ≥1 clause AND every clause
        maps to ≥1 span. Uncovered obligation OR unjustified clause = FAIL.

QUAL-2  DIFFERENTIAL AGREEMENT.  Same source compiled to ≥2 dissimilar engines (table above);
        100% verdict agreement on the full fixture corpus. Any disagreement = FAIL (encoding
        disqualified until root-caused, not until "the better engine is chosen").

QUAL-3  SYSTEM-MUTATION CATCH-RATE.  Pre-registered seeded faults in the system-under-analysis;
        encoding must flip green→red on each. Safety-critical seeds: 100%. Catch-rate below the
        obligation's pre-registered residual-risk budget = FAIL.

QUAL-4  ENCODING-MUTATION SENSITIVITY.  Mutate the encoding (drop clause, weaken bound, antecedent
        →False, invariant→True, drop disjointness/fairness/closure). Every mutant MUST break ≥1
        golden fixture. A surviving encoding-mutant = a dead/vacuous clause = FAIL.

QUAL-5  VACUITY / NON-TRIVIALITY.  Mechanically prove the property is non-trivial: antecedent is
        satisfiable (Z3 sat-check on the hypothesis alone), grounding is non-empty (clingo count),
        invariant is not implied by False, the bad state is reachable in the abstraction. A
        vacuously-true theorem = FAIL even with a valid Qed.

QUAL-6  WITNESS BACK-TRANSLATION.  Forced countermodel is a recognized hazard instance; replayed
        proof/justification has every leaf grounded in an admitted axiom or primary datum
        (independent re-checker, NOT the producing engine where possible — cvc5 replays Z3,
        kernel replays tactic). Ungrounded leaf OR nonsense countermodel = FAIL.

QUAL-7  CONFORMANCE TO THE ARTIFACT (where the obligation is about running code).  Model ⊑ code
        via synthesized runtime monitor / refinement check on real traces. Green-on-model with no
        established refinement = ADVISORY ONLY, never a gate. Abstraction-laundered bug = FAIL.

QUAL-8  GUARANTEE-STRENGTH MATCH (CALIB).  Verdict kind matches quantity kind: logic invariant
        asserted exactly (not a probability, not a bounded-k BMC sold as ∀); float-sensitive numeric
        to a stated tolerance/CI with a passing calibration gate (R̂<1.01, SBC-uniform, ECE≤budget).
        `unknown`/timeout/divergence treated as FAIL-CLOSED, never green. Wrong bar = FAIL.

QUAL-9  INDEPENDENCE OF THE TAG.  Any "external/primary-evidence/admitted-axiom" tag that terminates
        a justification chain must be bound to a source the producer did NOT author (signed input,
        cryptographic provenance, human sign-off). A self-authored "external" node = self-
        certification (Löb violation) = FAIL.  ≥2 mis-targeted encoding attempts on one obligation
        triggers a mandatory independent (human or dissimilar-method) second channel.

QUAL-10 RECORD.  Fixture corpus, mutation set, and acceptance thresholds FROZEN and timestamped
        BEFORE the verdict they clear (happens-before, no retrofitted criterion). Full gate
        transcript persisted, tamper-evident, replayable. A verdict whose criterion postdates it = FAIL.
```

The gate is the **conjunction** — passing QUAL-2 (differential) while failing QUAL-4 (sensitivity) is the classic "two engines agree on a vacuous spec." Each `FAIL` is mechanically decidable; none requires a model to judge a model.

### A worked mechanical gate (runs on the installed stack)

Take the AUTH encoding from the Prolog and ASP sections (spillway deploy gate). QUAL-2 + QUAL-4, fully mechanical, no LLM in the verdict path:

```bash
# QUAL-2 differential: same policy, two dissimilar engines, verdicts must match
swipl -g "gate(ai_optimizer,deploy(spillway_ctrl),R),writeln(R),halt" policy.pl   > swipl.out
clingo policy.lp --outf=1 | grep -o 'blocked([^)]*)' | sort                        > clingo.out
# reconcile: a normalizer maps both to {agent,action,allow|deny}; diff must be empty

# QUAL-4 sensitivity: mutate the encoding, the golden fixture MUST break
for m in mutants/*.lp; do
  if clingo "$m" fixtures.lp --outf=1 | grep -q "FIXTURE_OK"; then
     echo "SURVIVING ENCODING-MUTANT $m  -> dead clause -> QUAL-4 FAIL"; exit 1
  fi
done
```

The mutants are generated by deleting one `blocked`/`forbidden` clause, flipping one default, or removing the closure rule; the `fixtures.lp` asserts the hand-adjudicated allow/deny outcomes. A mutant that leaves `FIXTURE_OK` standing has proven a clause is inert. The verdict is a `grep` and an `exit 1` — a mechanical gate, the deflation-detector cannot reach it.

### Honest leverage & kill-condition

**Load-bearing:** this discipline is what converts the whole survey from "logics that *could* gate" into "encodings that are *allowed* to gate." Its leverage is structural and real: differential disagreement, surviving encoding-mutants, vacuous antecedents, and ungrounded justification leaves are each detectable *without* trusting the author, and the four-technique conjunction closes the faithfulness × sensitivity grid that any single technique leaves open. The GL/Löb topology check (QUAL-9) is the part the mission already paid for in blood — it is the only gate that catches the self-certifying assurance graph that defeats LLM-on-LLM review.

**Where it is ash:** the discipline cannot manufacture a faithful *obligation*. Every gate qualifies the encoding *against a written obligation and a fixture corpus*; if the obligation text itself is wrong, or the golden fixtures are mis-adjudicated, the harness faithfully clears a faithful encoding of the wrong thing — CALIB's failure pushed one level further out, to the human-admitted root. QUAL-9's independence requirement bounds but does not eliminate this: it forces the chain to terminate at a non-LLM source, but a wrong human axiom still passes. The residual risk is the *adjudication of the fixtures*, and it must be measured (inter-adjudicator agreement on the golden set), not assumed away.

**Falsifiable experiment / KILL CONDITION.** Assemble a corpus of N LLM-authored encodings across ≥5 formalisms, each in two variants: a faithful one and one with a *seeded encoding pathology* (vacuous antecedent, weakened bound, dropped disjointness, self-authored "external" tag, retrofitted criterion). Run the full QUAL checklist. **KILL the discipline if** any seeded pathology clears all ten gates green — i.e., the conjunction has a blind spot — OR if the catch is attributable to a step that secretly required model judgment (a hidden LLM-as-judge). **Second kill:** if, on realistic autoharn obligations, the fixture-adjudication itself cannot be performed at inter-adjudicator agreement above the residual-risk budget — then the harness is qualifying encodings against an un-qualifiable oracle, and the honest move is to demote those obligations to advisory and route the decision to a human gate with a logged alternative (ATTR/dstit), not to ship a green that launders the disagreement. Honest ash here — "this obligation's fixtures cannot be adjudicated mechanically at this stakes level" — is an acceptable, even mandatory, result; a harness that reports green regardless of fixture quality is not.

### References (edification)

- **RTCA DO-178C / DO-330, "Software Tool Qualification Considerations" (2011).** The source discipline: when a tool's output is trusted in lieu of review, the tool is qualified to the criticality it clears. The template for this entire section.
- **Ammann & Offutt, *Introduction to Software Testing* (2nd ed., 2016), ch. on mutation analysis.** Teaches mutation score as a *sensitivity* metric — the mechanical anti-vacuity gate (QUAL-3/4).
- **Cousot, "Abstract Interpretation" (and the soundness-of-abstraction literature).** Teaches exactly the faithfulness gap QUAL-7 attacks: a green on the abstraction is not a green on the artifact unless refinement is established.
- **Talts, Betancourt et al., "Validating Bayesian Inference Algorithms with Simulation-Based Calibration" (2018)** and **Boolos, *The Logic of Provability* (1993).** The two ends of the mechanical-gate spectrum: SBC as a calibration gate that cannot be faked by a passing R̂ (QUAL-8), and Löb's theorem as the proof that self-certification is vacuous (QUAL-9) — the formal statement of why the deflation-detector deflated.


---
*Cross-cut — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
