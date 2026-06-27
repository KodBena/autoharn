# 26 — Substructural Logic: Linear, Affine, Relevant & BI/Separation (resource, the borrow-checker lineage)

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Coined terms → root **[GLOSSARY.md](../../../../GLOSSARY.md)**. See the [index](../README.md).

Logics that drop the structural rules — weakening, contraction, exchange — so that a hypothesis is a *resource consumed exactly once* rather than a fact freely reusable. This is the formal machinery behind ownership, linear types, the Rust borrow-checker, and separation logic's reasoning about disjoint heap.

## Primer (becoming broadly expert)

Classical and intuitionistic logic treat `A` as eternally available: from `A` you may derive `A ∧ A` (contraction) and you may discard unused hypotheses (weakening). Substructural logics *forbid* one or both. **Linear logic** (Girard, 1987) forbids both: a proof must use each premise exactly once, splitting conjunction into multiplicative `⊗` ("I have A *and separately* B, consuming both") versus additive `&` ("I may choose A or B from the same resource"), with `!` ("of course") marking the reusable. **Affine** logic keeps weakening (use *at most* once — discardable but not duplicable: the affine-type lineage of Rust's move semantics). **Relevant** logic keeps contraction but drops weakening (the antecedent must be *actually used* — premises must be relevant to the conclusion). **BI** (O'Hearn & Pym, 1999) fuses an additive and a multiplicative conjunction in one logic; its model on heaps is **Separation Logic** (Reynolds, O'Hearn, Yang, 2001–02), whose separating conjunction `P * Q` asserts P and Q hold on *disjoint* regions, and whose **frame rule** — `{P} c {Q}` entails `{P * R} c {Q * R}` — is the local-reasoning engine. The intuition: these logics are built to discharge obligations about *finite resources that must not be silently duplicated, leaked, or aliased* — the failure modes of ownership, not of truth.

## Obligations it discharges

**STRUCT — Structural Soundness by Construction (primary assignment).** The whole point of substructural typing is to make a defect class *unrepresentable*: a value that is moved cannot be used again (no use-after-free, no double-discharge), a borrowed reference cannot outlive its owner, an `optional`/`expected` cannot be ignored. Separation logic's `P * Q` makes *aliasing* — the precondition that two writers touch disjoint memory — a checkable proposition rather than a hope. Guarantee strength: **machine-checked proof** (in Iris/VeriFast) or **type-soundness theorem** (in the affine-type lineage) that the bad state is not constructible. This is the strongest tier autoharn offers for the "lying signature / bare sentinel / partition-crossing fault" failure mode.

**COMMIT — Directed Commitment & Handoff Integrity.** A commitment is the canonical linear resource: created once, discharged exactly once, *or* explicitly delegated (ownership transfer) — never double-counted, never silently dropped. Linearity is the exact semantics for "either completes atomically or is explicitly unwound": a leaked linear token is a *type error*, which is precisely the Herstatt/orphaned-settlement-leg failure mode. Strength: an unconsumed obligation fails to typecheck.

**COHERE — Single-Authority / Single-Writer Coherence.** Separating conjunction *is* single-writer reasoning: `x ↦ v` is an exclusive ownership assertion; you cannot have `x ↦ v * x ↦ w` because the heaplets must be disjoint. This directly encodes "one owner with a coherence invariant quantified over all writers" and forbids the torn/stale-read second writer. Iris's fractional and ghost-state permissions express *shared-read/exclusive-write* coherence precisely.

**AUTH — partial.** Linear *capabilities* (a permission token consumed on use) model "every action gated by a checkable permission before the effect," and consumption gives non-reusable, single-shot authority — but substructural logic carries no *norm-precedence/derogation* ordering; pair it with deontic/defeasible layers for that.

**Does NOT serve:** temporal "always/eventually" properties (INV/PROG — that is temporal logic's job), deontic detachment (TRIG), contrary-to-duty reparation (DEGRADE), provenance chains (PROV), belief revision (REVISE), or paraconsistent containment (CONSIST). Substructural logic governs *resource discipline*, not time, obligation, or contradiction. Assign it where the failure mode is duplication/leak/alias; never stretch it to cover an "always"-property.

## A worked encoding

A Fed settlement leg as a linear commitment in **VeriFast** C separation logic — the COMMIT/COHERE obligation that a DvP leg is neither double-discharged nor leaked:

```c
/*@ predicate leg(struct leg *l; int amount); @*/

struct leg { int amount; bool settled; };

void discharge(struct leg *l)
//@ requires leg(l, ?amt) &*& amt > 0;
//@ ensures  emp;            // the resource is CONSUMED, not left dangling
{
  //@ open leg(l, amt);
  l->settled = true;
  free(l);
  //@ leak nothing;          // VeriFast rejects if any chunk remains
}
```

The `&*&` is separating conjunction; `requires leg(...)` consumes the leg chunk and `ensures emp` proves it is gone. If a caller tried to `discharge(l)` twice, the second call has no `leg(l,_)` chunk to consume — a *verification failure*, the double-settlement caught statically. A leaked leg (never discharged) fails VeriFast's no-leak check at function exit. This is the autoharn STRUCT+COMMIT gate as a compile-time obligation.

## Automation & tooling (the git-clone-runnable question)

**Dedicated, mature, git-clone-runnable tools exist — this is among the most industrially landed logics in the survey.**

- **VeriFast** (modular separation-logic verifier for C, Java, Rust) — **MIT license**, latest **25.11**, actively maintained; ships prebuilt Linux binaries. Discharges STRUCT/COMMIT/COHERE on real code. ([repo](https://github.com/verifast/verifast), [releases](https://github.com/verifast/verifast/releases))
- **Iris** (higher-order concurrent separation logic in Rocq/Coq) — **BSD-3-Clause**, latest **coq-iris 4.4.0** (2025-06-04); the research-grade frontier for machine-checked concurrent ownership proofs. ([package](https://rocq-prover.org/p/coq-iris/4.4.0))
- **Viper** (intermediate verification infrastructure, permission-based separation logic; backs Prusti for Rust) — Mozilla/Apache-style open license, actively maintained by ETH.
- **Rust's borrow-checker itself** is the affine-type lineage shipped to millions — the existence proof that this logic is industrially load-bearing.

For **pure linear-logic** sequents (resource arithmetic without heaps), there is no single dominant solver, but the encoding path is concrete: linear-logic provability maps to **SMT/Z3 4.16** (local — verified) as a *frame-condition* problem, or to **ASP/clingo 5.8** by modeling each linear hypothesis as an atom that a rule *consumes* (delete from the working set) — clingo's stable-model semantics naturally enforces single-use when you forbid an atom appearing in two simultaneous derivations. Multiplicative resource-splitting becomes a partition constraint Z3 discharges directly. So even the "no dedicated solver" corner yields an encoding, not a shrug.

## Honest leverage & kill-condition

**Load-bearing:** where an autoharn obligation is genuinely about *finite resource discipline* — settlement legs (COMMIT), exclusive heap/config ownership (COHERE), absence-as-typed-value and no-use-after-move (STRUCT). Here VeriFast/Iris buy machine-checked guarantees no test suite approximates.

**Ash:** if you reach for it to express "the spillway is *always* safe" (a temporal invariant) or "the operator *may* override" (a deontic permission), you will contort the encoding and get a brittle, unconvincing proof. Substructural logic has nothing to say about time or norms.

**Falsifiable experiment + KILL CONDITION:** Take 50 real autoharn resource-discipline obligations (double-discharge, leak, alias, use-after-move). Encode each in VeriFast; build a mutation/golden fixture set that injects exactly those four defect classes. **KILL CONDITION:** if VeriFast fails to reject ≥95% of the seeded defects, *or* if the median LLM-authored spec annotation introduces an unsound `assume`/axiom that lets a seeded defect pass (caught by an independent Z3 differential re-check of the frame conditions — INDEP), then the LLM-encoded separation-logic layer is not qualifiable for life-critical use and must be demoted to advisory. The tool is mature; the *LLM-authored annotation* is what is on trial.

## References (edification)

- **Reynolds, "Separation Logic: A Logic for Shared Mutable Data Structures" (LICS 2002).** The founding paper; teaches the frame rule and `*` from first principles.
- **Girard, "Linear Logic" (TCS 1987).** The source; teaches `⊗`/`&`/`!` and why dropping contraction/weakening makes proofs resource-aware.
- **Jung et al., "Iris from the Ground Up" (JFP 2018).** Teaches how concurrent ownership, ghost state, and invariants are built modularly and machine-checked. ([Cambridge Core](https://www.cambridge.org/core/journals/journal-of-functional-programming/article/iris-from-the-ground-up-a-modular-foundation-for-higherorder-concurrent-separation-logic/26301B518CE2C52796BFA12B8BAB5B5F))
- **VeriFast tutorial (Jacobs et al.).** Teaches how to actually *write* the annotations above on C/Java/Rust and run the checker. ([repo](https://github.com/verifast/verifast))


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
