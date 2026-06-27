# 16 — Epistemic & Dynamic Epistemic Logic (S5n, common knowledge, DEL/PAL/action models)

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Abbreviations & tiers → **[KEY](../KEY.md)**; coined terms → root **[GLOSSARY.md](../../../../GLOSSARY.md)**; index → [README](../README.md).

**Key for this document.** Full reference → [KEY.md](../KEY.md).  Guarantee-strength **5** deductive (kernel-checked) · **4** exhaustive-over-model · **3** bounded · **2** calibrated-CI · **1** defeasible.  Cost **T0** present locally · **T1** pip/jar · **T2** compile-from-source · **T3** encode into an existing host.

| code | meaning |
|---|---|
| [INV](../KEY.md#inv) | Safety-Invariant Maintenance — an "always"/barrier property holds in every reachable state; no silent excursion |
| [PROG](../KEY.md#prog) | Liveness & Real-Time Progress — required events eventually occur within deadline; no deadlock or correct-but-late action |
| [AUTH](../KEY.md#auth) | Action Authorization & Norm Precedence — every effect is gated by an explicit permission; closure + norm priority resolve deterministically |
| [ATTR](../KEY.md#attr) | Agency Attribution — every change bound to an identified agent who saw-to-it and could-have-done-otherwise |
| [COMMIT](../KEY.md#commit) | Directed Commitment & Handoff — an owed obligation has a tracked lifecycle; completes atomically or is unwound; no orphan/double handoff |
| [PROV](../KEY.md#prov) | Claim Provenance & Groundedness — every claim resolves via a finite replayable chain to primary evidence; no free-floating fact |
| [REVISE](../KEY.md#revise) | Belief Revision & Retraction — retracting a premise revisits every dependent conclusion; corrections append-only, AGM-rational |
| [CONSIST](../KEY.md#consist) | Consistency & Contradiction Containment — contradictions are quarantined; no ex-falso, no silent side-picking |
| [CALIB](../KEY.md#calib) | Substantiated & Calibrated Claims — each claim backed by a reproducible artifact at strength matched to its kind; honest confidence |
| [COHERE](../KEY.md#cohere) | Single-Authority / Single-Writer Coherence — one authoritative definition per fact; one owner per mutable state; references resolve to one correct target |
| [RECORD](../KEY.md#record) | Auditable Decision Record & Ordering — a tamper-evident trail authored at decision time; happens-before enforces criterion-before-result, approval-before-action |

Logics of *who knows what* — and, crucially, how knowledge *changes* when information events fire — giving autoharn a calculus for the knowledge-distribution failure modes that single-agent state tracking cannot even express: handoffs that drop a duty between two parties, decisions audited against what an agent knew *at the time*, and coordination that silently never reaches the agreement it assumes.

## Primer (becoming broadly expert)

The static core is **S5n**: n agents, each with an *indistinguishability* equivalence relation over possible worlds. `K_a φ` ("agent a knows φ") holds at world w iff φ is true in every world a cannot distinguish from w. S5 axioms encode idealized knowledge: **T** (`K_a φ → φ`, factivity — knowledge is grounded, unlike belief), **4** (positive introspection), **5** (negative introspection). Above individual knowledge sit **everybody-knows** `E_G φ` and **common knowledge** `C_G φ` (everyone knows that everyone knows… ad infinitum) — the fixpoint that coordinated action provably requires. The landmark negative result, the **Coordinated Attack / Two Generals theorem** (Halpern & Moses 1990): common knowledge is *unattainable* by any finite protocol over a channel that can lose messages. The dynamic layer — **Public Announcement Logic** (Plaza 1989) and the **action models** of **Baltag, Moss & Solecki (1998)** — adds update operators: `[!φ]ψ` ("after φ is truthfully announced, ψ holds"), computed as a *product update* that prunes or refines the model. This is the apparatus built for one obligation family: *what does each party know, and what do they know after this event* — the semantics of **handoff** and of **knew-at-decision-time**.

## Obligations it discharges

- **[COMMIT](../KEY.md#commit) — Directed Commitment & Handoff Integrity (primary fit).** A handoff is exactly an information event transferring an obligation between agents. DEL's product update *computes the receiver's post-handoff epistemic state*; the Coordinated Attack theorem turns the failure mode "a pending action falls between two clinicians" into a **provable** statement: if the protocol requires `C_{giver,receiver}(duty active)` over an unreliable channel, no finite acknowledgment discipline attains it — so the *correct* design target is bounded mutual knowledge to depth k, with the residual gap named, not assumed away. Guarantee strength: a decidable validity/model-checking verdict that a specific handoff protocol does or does not establish the required epistemic level.
- **[ATTR](../KEY.md#attr) / [RECORD](../KEY.md#record) — Agency Attribution & Decision Record.** "Bound to an agent who *saw to it* and could have done otherwise" and "reconstruct what was known at the moment of decision" are epistemic-snapshot claims: `K_a φ` evaluated at the decision world, with "could have done otherwise" as the existence of an accessible alternative. DEL pins *when* a fact entered an agent's knowledge (which announcement). Strength: model-checkable knowledge preconditions; pair with STIT for the agency half (assign, don't absorb).
- **[AUTH](../KEY.md#auth) — Knowledge-gated permission.** Many authorizations are epistemic: "may act only if it *knows* the interlock cleared." Action-model preconditions encode `K_a clear` as the gate, distinguishing genuine knowledge from mere truth.
- **[PROV](../KEY.md#prov) — partial.** S5 factivity gives knowledge a *grounded* (truth-entailing) flavor versus defeasible belief, useful for separating "known" from "assumed." But provenance *chains* belong to justification logic (Artemov); use epistemic logic only for the know/believe boundary.

Does **not** serve: **[INV](../KEY.md#inv)** (temporal "always" — LTL/CTL territory), **[PROG](../KEY.md#prog)** (real-time/liveness), **[CALIB](../KEY.md#calib)/STRUCT/CLASS** (numeric/type/partition obligations), **[CONSIST](../KEY.md#consist)** (paraconsistency), and **[REVISE](../KEY.md#revise)** (defeasible belief change — that is AGM / plausibility-model dynamic *doxastic* logic, an adjacent but distinct assignment). Epistemic logic is for *knowledge-state distribution*, not invariants, timing, or numerics.

## A worked encoding

ICU shift handoff ([COMMIT](../KEY.md#commit)): clinician `a` knows a pending antibiotic order `p`; after handing off to `b`, must `b` know it, and is it common knowledge? Real SMCDEL input:

```
-- handoff.smcdel
VARS 1
LAW  Top
OBS  alice: 1
     bob:

VALID? (1 -> alice knows that 1)            -- giver grounded in the order
VALID? [ ! 1 ] (bob knows that 1)           -- after announcing p, receiver knows p
VALID? [ ! 1 ] (Ck alice,bob (1))           -- after one announcement, COMMON knowledge?
```

Proposition `1` = "antibiotic order pending." `OBS` lists who observes which variable: `alice` sees `1`; `bob` sees nothing — he is initially ignorant, the handoff hazard. SMCDEL returns `True` for line 2 (a *truthful public* announcement does inform bob) and lets you probe `Ck` (common knowledge) for line 3. The lever is modeling the channel honestly: replace the idealized public announcement with a *private/lossy* action model (acknowledgment may fail) and the `Ck` query returns `False` for every finite protocol — autoharn surfaces "this handoff cannot guarantee common knowledge; specify the acknowledgment depth and the residual." Run: `smcdel handoff.smcdel`.

## Automation & tooling (the git-clone-runnable question)

A **dedicated open-source tool exists and is the right host**: **SMCDEL** — a *symbolic* (BDD-based) model checker for Dynamic Epistemic Logic, **GPL-2**, **v1.3.0**, Haskell, maintained by Malvin Gattinger (jrclogic/SMCDEL on GitHub; `smcdel` on Hackage). It checks S5n knowledge, common knowledge, public announcements, and action models, with a textual `.smcdel` input and a web/CLI front-end; mature and actively maintained, scaling via BDDs over the explicit Kripke blow-up. Complementary: **MCMAS** (GPL, ~v1.2.2; ISPL language) for combined *temporal-epistemic* (CTLK) and strategic properties — use it when the obligation couples knowledge with time/strategy.

Local: neither ships in this environment, but the **encoding fallback is direct and uses installed engines**. An S5n model is a set of worlds plus one equivalence relation per agent; `K_a φ` is universal quantification over an agent's equivalence class. In **clingo** (5.8.0, present): declare `world/1`, `indist(a,W1,W2)` as a reflexive-symmetric-transitive relation, `holds(W,Atom)`, and `knows(a,W,F) :- not someAccessibleCounterexample`. Public announcement `!φ` is a program transformation deleting `¬φ`-worlds (and their `indist` edges) — one rewrite per event. In **Z3** (4.16, present): worlds as an enumerated sort, accessibility as an uninterpreted relation constrained to be an equivalence, knowledge as a bounded quantifier; common knowledge to depth k as an unrolled fixpoint (full `C_G` needs the BDD/fixpoint approach SMCDEL already provides, which is why SMCDEL is preferred for `Ck`). So: SMCDEL first; clingo/Z3 encoding for bespoke action models or to fuse with autoharn's existing ASP/SMT gates.

## Honest leverage & kill-condition

**Load-bearing** precisely where autoharn obligations are genuinely *multi-agent and information-asymmetric*: ICU/DvP handoffs ([COMMIT](../KEY.md#commit)), Fed/NYSE decisions audited on "what was known when" ([ATTR](../KEY.md#attr)/RECORD), knowledge-gated authorization ([AUTH](../KEY.md#auth)). The unique, non-decorative payoff is the Coordinated-Attack class of bug: protocols that *assume* common knowledge an unreliable channel cannot deliver — invisible to a state machine plus an access-control list.

**Where it is ash:** single-agent invariants, timing, numerics — and, more sharply, any "handoff" that is really a single source of truth one party reads. There, S5 over one writer is ceremony already covered by [COHERE](../KEY.md#cohere)/RECORD.

**Falsifiable experiment:** take a corpus of real handoff/authorization incidents; for each, model the required epistemic level and run SMCDEL. **KILL CONDITION:** if every incident reduces to a single-writer state fact already caught by an ordinary invariant — i.e., none exhibits a genuine "A does not know that B knows" / lost-acknowledgment structure — then epistemic logic earns no place in autoharn beyond notation. It *lives* iff the corpus contains incidents whose root cause is missing mutual-knowledge depth that no single-agent gate flags.

## References (edification)

- **Fagin, Halpern, Moses & Vardi, *Reasoning About Knowledge* (MIT, 1995)** — the canonical text; teaches S5n, common knowledge, and the Coordinated Attack impossibility that grounds handoff guarantees.
- **van Ditmarsch, van der Hoek & Kooi, *Dynamic Epistemic Logic* (Springer, 2007)** — teaches PAL and action-model product update: how knowledge changes on an event (the handoff calculus).
- **Baltag, Moss & Solecki (1998), "The Logic of Public Announcements, Common Knowledge, and Private Suspicions"** — teaches action models, the formal engine for private/lossy (not just public) information events.
- **SMCDEL — jrclogic/SMCDEL (GitHub) & Hackage `smcdel`; van Benthem, van Eijck et al., "Symbolic Model Checking for DEL"** — teaches the runnable BDD encoding that makes the above checkable at scale.

Sources: [SMCDEL on GitHub](https://github.com/jrclogic/SMCDEL), [smcdel on Hackage](https://hackage.haskell.org/package/smcdel), [MCMAS](https://link.springer.com/article/10.1007/s10009-015-0378-x)


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
