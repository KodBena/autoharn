# autoharn — Architecture & the through-line

> The connective account the bottom-up research never states: *what the machine is, end to end, and
> where each piece sits inside it.* Vocabulary: obligation codes (`INV`, `PROV`, …) are defined in the
> survey's [KEY](research/2026-06-27-obligations-formalisms-survey/KEY.md); coined terms in the root
> [GLOSSARY](../GLOSSARY.md). This document is the structure; the
> [survey](research/2026-06-27-obligations-formalisms-survey/) is its parts list.

---

## 1. The problem, stated exactly

An LLM is now a co-author of software, including software whose failure is measured in lives — settlement
engines, flight control, spillway logic, oncology dosing. An LLM is fluent, fast, and **unreliably
honest**: it will emit a green check, a "proof," a confident number with *no warrant behind it*, and the
failure is **silent** — it looks exactly like success. The survey's running example is the whole thesis in
one line: *a 4× chemotherapy overdose ships green because a safety bound was "proven" by an LLM lemma that
looks like a Z3 certificate but was never submitted to Z3.*

At toy stakes you absorb this — you re-read, you spot-check, the cost of a miss is an afternoon. At
life-critical stakes you cannot, because the cost of one silent miss is unbounded and the volume of
LLM-authored claims is too high to hand-audit. **autoharn is the harness you `git clone` before you let an
LLM near such a codebase.** Its single job, from which everything else follows:

> **Make every compliance claim carry its warrant, or be refused.**

Not "help the LLM write better code" — that's a model problem. autoharn assumes the LLM will sometimes be
confidently wrong and builds the machine that *catches the unwarranted claim mechanically*, including the
LLM's claims, including its own.

## 2. The reframe: managing code = discharging obligations

The organizing move (the one the parts-list presupposes but never argues): **stop thinking in logics, think
in obligations.** A life-critical system bears a fixed, enumerable set of *responsibilities it must
guarantee* — the [obligation taxonomy](research/2026-06-27-obligations-formalisms-survey/01-obligation-taxonomy.md):
a safety invariant holds at every tick (`INV`); a required action completes within its deadline (`PROG`);
once already in violation, the system enters a *defined* safe regime (`DEGRADE`); every change is bound to an
agent who could have done otherwise (`ATTR`); every claim traces to primary evidence (`PROV`); and so on —
nineteen of them.

Each obligation has a **failure mode**: a specific way the world goes wrong if the obligation is unmet. And
here is the load-bearing claim: **a statement of compliance is admissible only if it is *discharged* by a
mechanism whose semantics match that failure mode, at a guarantee strength at least what the stakes demand,
and the discharge is recorded with its justification.** Everything in autoharn is plumbing around that
sentence.

This is why "which logic is best" was always the wrong question (the dead end of two earlier research
passes, kept as [Witnesses](research/2026-06-27-logic-fair-trials/)). You don't crown a logic. You take an
obligation, read off its failure mode as a semantic condition, and *assign* the formalism whose semantics
**is** that condition. A `□`/fixpoint-over-reachable-states condition wants a model checker; a
"you-ought-Y-given-you-already-did-the-forbidden-X" condition is *inconsistent* in any monadic-obligation
logic (Chisholm) and wants dyadic deontic logic; "could have done otherwise" is Halpern–Pearl actual
causation and nothing else. The 27 formal systems are not a menu to choose from — they are **components,
each occupying a slot defined by an obligation.**

## 3. The central object: the claim ledger with a justification spine

If obligations are the rows, the thing that makes autoharn a *system* rather than a pile of checkers is a
single shared object every component reads from and writes to: an **append-only claim ledger**.

- Every fact, datum, decision, and guarantee in the project is a **claim node**.
- Every claim carries a **justification**: a pointer to *what discharges it* — a model-checking certificate,
  an SMT proof, a posterior with its SBC result, a cited measurement, or, at the bottom, an explicitly
  **admitted human axiom**. (This is justification logic made operational: a claim is not `F`, it is
  `t : F` — "`F`, by warrant `t`".)
- Justification chains are required to **terminate at non-LLM roots**. A claim whose warrant bottoms out in
  "the LLM said so" is not discharged; it is *advisory*. The provability-logic guardrail (Löb's theorem) is
  what makes "the system proves itself correct" a **structural impossibility** rather than a reviewer's good
  intention.

The ledger is the single source of truth; the formalisms are **producers of justified claims into it**, and
they compose *through* it, never directly. This one object is simultaneously `PROV` (groundedness),
`RECORD` (the tamper-evident, decision-time trail), `REVISE` (retract a premise and every dependent claim is
revisited — AGM, append-only), and `INDEP` (the justification is checkable by a mechanism that didn't author
it). The survey's [composition cross-cut](research/2026-06-27-obligations-formalisms-survey/B-composition-architecture.md)
is the detailed design of this spine; this section is its reason for being.

## 4. The lifecycle of one change — the through-line

Here is what *using* autoharn actually looks like, end to end, for a single change. This is the narrative
the survey never walks:

1. **Propose.** An LLM (or a human) proposes a diff.
2. **Trigger.** The change's footprint *triggers* a set of obligations — touching the spillway control law
   triggers `INV` and `PROG`; touching who-can-deploy triggers `AUTH` and `ATTR`; touching a settlement leg
   triggers `COMMIT` and `COHERE`. Which obligations are in force is itself a derived, recorded fact.
3. **Route.** Each triggered obligation is routed to its **assigned formalism** (the survey's assignment
   table is exactly this routing function).
4. **Author the encoding.** The LLM writes the formal artifact — the TLA+ spec, the clingo program, the
   separation-logic annotation, the NumPyro model. *This is the step the LLM is genuinely good at and humans
   historically were too slow for — the "encoding tax" the thesis says LLMs now pay.*
5. **Qualify the encoding.** Because at these stakes **the encoding is itself on trial**, it must pass
   mechanical [qualification gates](research/2026-06-27-obligations-formalisms-survey/C-encoding-qualification.md)
   before it is allowed to discharge anything: differential solvers (Z3 vs cvc5 on the same SMT-LIB),
   mutation fixtures (a known-bad input *must* turn the gate red), vacuity detection (the spec isn't
   trivially satisfied), and conformance (the model actually over-approximates the real artifact — abstract
   interpretation / runtime verification, so "green on the model" can't launder into "green on the system").
6. **Discharge.** A qualified encoding that passes **writes a claim into the ledger at a guarantee strength**
   (`5` deductive … `1` defeasible) with its justification term.
7. **Admit or demote.** The change is **admissible iff every in-force obligation is discharged at or above
   the strength its stakes require.** Where it is — the change lands with a complete, replayable assurance
   case. Where it is *not* — the obligation is **demoted to advisory with a logged human gate**: autoharn
   refuses to ship green, names exactly which obligation is under-discharged and by how much, and routes it
   to a human who signs an admitted axiom (which becomes a ledger root, with its own provenance).

That step 7 is the whole ethic. autoharn does not pretend to guarantee what it cannot. It **converts the
LLM's silent over-claim into a loud, located, measured gap** — and that conversion is the product.

## 5. Why a portfolio, and why it still composes

The instinct to want *one* engine is the instinct to minimize moving parts, and it is wrong here for a
provable reason: the obligations have **genuinely different failure semantics**, and no single logic's
model theory expresses all of them (the survey demonstrates three obligations with *exactly one* home each).
Formalisms are interchangeable **within** a slot — Z3 or cvc5 for an `INV` discharge — and emphatically not
**across** slots. So the system is heterogeneous by necessity. What keeps a 27-engine stack from being 27
unaccountable oracles is precisely §3: every engine's output is a *justified claim in one ledger*, with one
strength scale and one Löb-guarded justification spine, so the **residual risk of the whole composition is a
single computed number per claim**, not an act of faith in twenty-seven tools.

## 6. The guarantee, and its honest boundary

What autoharn buys you: for every obligation, a guarantee *matched to its failure mode* at a *known
strength*, with a *replayable justification*, and a *mechanical refusal* to call something proven that
isn't. What it does **not** buy you, stated plainly because the alternative is the very false authority it
exists to kill: autoharn qualifies an encoding **against a written obligation and an adjudicated fixture
corpus.** If the obligation text is wrong, or the fixtures are mis-adjudicated, the harness will faithfully
clear a faithful encoding of *the wrong thing*. The Löb guardrail forces every chain to a non-LLM root — but
**a wrong human axiom still passes.**

The honest boundary, then, is exactly here: autoharn drives residual risk **down to the quality of
human-admitted roots and fixture adjudication, makes that residual a *measured quantity* (inter-adjudicator
agreement), and refuses to ship green when it falls below the obligation's required strength.** A harness
that hid this — that let a confident composition stand in for an unexamined axiom — would be the false
authority it was built to prevent. Which is why the discipline turns on the harness *itself*: this very
project watched an adversarial LLM auditor, built to catch a bias, **exhibit that bias and acquit** (the
"deflation cascade"). The lesson is encoded as `INDEP`: a load-bearing check may not be another model's
judgment; it must be mechanical, or independently diverse, or kernel-checked.

## 7. Where this actually stands

autoharn is a **metaproject at research stage**, not a product. As of this writing: the obligation taxonomy
is derived; the obligation→formalism assignment is mapped; **~20 of 27 formalisms are runnable today** on a
stock toolbox (Z3, clingo, SWI-Prolog, OR-Tools, Postgres, a JVM, JAX) — most of the "merely philosophical"
ones via *standard encodings into those hosts*, which is the "toolless ≠ unleverageable" result made
concrete. What is **specified but not yet built**: the ledger and its justification spine, the qualification
gate-runner, and the routing function. The honest next step is small and real: **instantiate the ledger,
take one obligation (the cheapest with no shortcut — regression-cause abduction in clingo), and run it
end-to-end against one real change**, including the mutation test that proves the gate can fail. A verdict
is earned by that experiment, not by this prose.

## 8. How to read the repository

- **This file** — the through-line. Start here.
- [GLOSSARY.md](../GLOSSARY.md) — coined terms (Pillar, intent SSOT, supersession, …).
- [research/.../KEY.md](research/2026-06-27-obligations-formalisms-survey/KEY.md) — obligation codes, tiers, tools.
- [research/.../00-synthesis.md](research/2026-06-27-obligations-formalisms-survey/00-synthesis.md) — the assignment, defended.
- [research/.../B-composition-architecture.md](research/2026-06-27-obligations-formalisms-survey/B-composition-architecture.md) — the ledger/spine design (§3 in detail).
- [research/2026-06-27-foundational-map/](research/2026-06-27-foundational-map/) — where this began: the two real projects whose hard-won disciplines seeded the obligation taxonomy.
