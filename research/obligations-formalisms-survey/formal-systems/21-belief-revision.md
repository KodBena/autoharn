# 21 — Belief Revision (AGM, contraction/revision/update, ranking/Spohn, DDL)

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Abbreviations & tiers → **[KEY](../KEY.md)**; coined terms → root **[GLOSSARY.md](../../../GLOSSARY.md)**; index → [README](../README.md).

**Key for this document.** Full reference → [KEY.md](../KEY.md).  Guarantee-strength **5** deductive (kernel-checked) · **4** exhaustive-over-model · **3** bounded · **2** calibrated-CI · **1** defeasible.  Cost **T0** present locally · **T1** pip/jar · **T2** compile-from-source · **T3** encode into an existing host.

| code | meaning |
|---|---|
| [INV](../KEY.md#inv) | Safety-Invariant Maintenance — an "always"/barrier property holds in every reachable state; no silent excursion |
| [PROG](../KEY.md#prog) | Liveness & Real-Time Progress — required events eventually occur within deadline; no deadlock or correct-but-late action |
| [TRIG](../KEY.md#trig) | Conditional Activation — a triggered duty fires exactly when (and only when) its precondition holds |
| [DEGRADE](../KEY.md#degrade) | Contrary-to-Duty Reparation — once already violated/faulted, enter a DEFINED safe regime — not undefined behaviour |
| [AUTH](../KEY.md#auth) | Action Authorization & Norm Precedence — every effect is gated by an explicit permission; closure + norm priority resolve deterministically |
| [PROV](../KEY.md#prov) | Claim Provenance & Groundedness — every claim resolves via a finite replayable chain to primary evidence; no free-floating fact |
| [REVISE](../KEY.md#revise) | Belief Revision & Retraction — retracting a premise revisits every dependent conclusion; corrections append-only, AGM-rational |
| [CONSIST](../KEY.md#consist) | Consistency & Contradiction Containment — contradictions are quarantined; no ex-falso, no silent side-picking |
| [TRACE](../KEY.md#trace) | Traceability, Coverage & Change-Impact — hazard→req→design→code→test links total & navigable; coverage measured; change-impact closed on the artifact |
| [INDEP](../KEY.md#indep) | Independent Adjudication & Tool Qualification — load-bearing checks discharged by a mechanism that does NOT share the producer's bias (no LLM-judging-LLM) |
| [RECORD](../KEY.md#record) | Auditable Decision Record & Ordering — a tamper-evident trail authored at decision time; happens-before enforces criterion-before-result, approval-before-action |

Verified: clingo keeps the entrenched corrected reading, drops `p_high`, and `spillway_safe` is withdrawn. Now the section.

## Belief Revision (AGM, contraction/revision/update, ranking/Spohn, DDL)

The discipline of how a rational corpus of beliefs *changes* when new information arrives — what gets retracted, what survives, and how conclusions downstream of a withdrawn premise are re-justified rather than left stranded.

## Primer (becoming broadly expert)

Classical logic tells you what follows from a fixed theory; it is silent on what to do when the theory must *change*. Belief revision is that missing theory of change. The canonical frame is **AGM** (Alchourrón, Gärdenfors, Makinson, 1985): three operations on a belief set closed under consequence — **expansion** (add naively), **contraction** (remove a belief and enough of its support to make removal stick), and **revision** (add a belief consistently, retracting conflicts first). The famous **AGM postulates** pin down *rational* change, and the **Levi/Harper identities** tie revision and contraction together. The governing principle is **minimal change** (informational economy): give up as little as possible, ranked by **epistemic entrenchment** — some beliefs are more dear than others and are surrendered last. **Spohn's ranking functions** (OCFs) quantify this with ordinal degrees of disbelief, enabling iterated revision (Darwiche–Pearl) where AGM alone underdetermines the next step. A crucial distinction (Katsuno–Mendelzon): **revision** corrects belief about a *static* world (I was wrong), while **update** tracks a world that *changed* (it moved). The obligation this machinery is built to discharge is **[REVISE](../KEY.md#revise)**: when a premise falls, every conclusion that leaned on it is automatically revisited — the stale-conclusion failure mode is exactly what entrenchment-ordered contraction forbids.

## Obligations it discharges

**[REVISE](../KEY.md#revise) — Belief Revision & Retraction Propagation (primary, exact match).** This is the home obligation. [REVISE](../KEY.md#revise)'s failure mode is a stale conclusion reasoned forward from a knocked-out premise. AGM contraction's defining property is that removing `p` also removes the support that would re-derive `p` (and re-opens conclusions that depended on it); entrenchment fixes *which* supporting beliefs go. Guarantee strength: a **postulate-level guarantee** — the new belief state provably satisfies the AGM/DP rationality postulates (closure, success, minimal change, consistency), checkable mechanically. AGM's append-only/point-in-time aspect (keep "what we believed at decision time") is a discipline *around* the operator, not the operator itself.

**[CONSIST](../KEY.md#consist) — Consistency & Contradiction Containment (strong secondary).** Revision's *consistency postulate* guarantees the revised set is consistent whenever the input is, so contradictory inputs are resolved by principled retraction rather than ex-falso explosion. Where you must *retain* both horns and reason under the live contradiction, that is paraconsistency's job (assign there); AGM's stance is to *restore* consistency, so it serves [CONSIST](../KEY.md#consist) when the right answer is "pick a side, minimally, and log why."

**[PROV](../KEY.md#prov) — Claim Provenance (partial).** Justification-tracking variants (foundational/base revision, TMS) record *why* each belief is held, supporting groundedness; but AGM's coherentist core does not itself demand primary-evidence chains. Assign [PROV](../KEY.md#prov)'s core elsewhere; AGM contributes the retraction-propagation half.

**Does NOT serve:** [INV](../KEY.md#inv), [PROG](../KEY.md#prog), [TRIG](../KEY.md#trig) (temporal/real-time guarantees — wrong tool), [AUTH](../KEY.md#auth)/ATTR/COMMIT (deontic/agency — that is DDL's and STIT's province), [TRACE](../KEY.md#trace)/RECORD (these are *processes* AGM can sit inside, not what it proves). Notably **DDL (Defeasible Deontic Logic)** is a *cousin* here, not the same engine: it handles overridden obligations ([DEGRADE](../KEY.md#degrade)/AUTH precedence), not belief retraction — do not conflate the two under this heading's umbrella.

## A worked encoding

The piezometer case ([REVISE](../KEY.md#revise)'s own example): a raw reading `p_high` (low entrenchment, sensor noise) yields the verdict `spillway_safe`; a corrected calibration later asserts `neg_p_high` with higher entrenchment. Minimal-change revision must retract `p_high` and *withdraw the inherited verdict*. AGM partial-meet contraction encodes directly as a clingo optimization (verified to run, clingo 5.8.0):

```prolog
belief(p_high).      rank(p_high, 1).      % raw reading (low entrenchment)
belief(neg_p_high).  rank(neg_p_high, 3).  % corrected calibration (high)
conflict(p_high, neg_p_high).

{ in(B) : belief(B) }.
out(B) :- belief(B), not in(B).
:- conflict(X,Y), in(X), in(Y).          % restore consistency
:- conflict(X,Y), out(X), out(Y).        % no gratuitous loss
#minimize { R,B : out(B), rank(B,R) }.   % surrender least entrenched

spillway_safe :- in(p_high).             % conclusion rides a retractable premise
#show in/1. #show spillway_safe/0.
```

Output: `in(neg_p_high)`, `Optimization: 1` — `p_high` is dropped and **`spillway_safe` is not in the answer set**. The stale verdict dies with its evidence. Swapping the ranks (sensor more entrenched than calibration) flips the outcome — making the entrenchment ordering an explicit, auditable artifact rather than an implicit tie-break.

## Automation & tooling (the git-clone-runnable question)

**Dedicated tool: TweetyProject — Belief Dynamics library**, GNU LGPL v3, latest **v1.28 (2025-01-23)** (web-verified, [tweetyproject.org](https://tweetyproject.org/)). Mature, actively maintained Java toolkit with first-class implementations of AGM revision/contraction, base revision, Spohn ranking (OCF) reasoners, and the Hansson/Darwiche–Pearl operators. This is the off-the-shelf answer for autoharn's [REVISE](../KEY.md#revise) engine; it is library-grade, not research-throwaway. Requires OpenJDK 25 (available locally).

**Encoding path (host-native, no extra install).** For tighter integration with the rest of the harness, AGM revision is *directly* encodable in **ASP/clingo 5.8.0** (verified above): the minimize-over-entrenchment program *is* partial-meet contraction. **Equibel** (open-source, ASP-backed, Delgrande–Schaub lineage) demonstrates the consistency-based variant on a stock clingo backend. For ranked/iterated revision with numeric Spohn degrees, **Z3 4.16** carries the optimization (`Optimize` with weighted soft constraints over entrenchment). A justification-tracking (foundational) variant maps onto an **SWI-Prolog** truth-maintenance layer (`library(chr)` for the dependency-directed backtracking). So: a dedicated tool exists *and* a host-native encoding exists; autoharn can use TweetyProject as oracle and the clingo encoding as the in-loop, differentially cross-checking the two ([INDEP](../KEY.md#indep)).

## Honest leverage & kill-condition

**Load-bearing where:** beliefs are *propositional and rankable*, conflicts are detectable, and the cost of a stale conclusion is high — exactly [REVISE](../KEY.md#revise)'s territory (corrected lab value, superseded encounter flag, retracted calibration). Here AGM buys a postulate-checkable guarantee that no withdrawn premise leaves a live descendant.

**Where it is ash:** (1) When entrenchment is *contested or unknown*, AGM underdetermines the outcome — it tells you to change minimally but not, uniquely, *how*; garbage ranks yield confidently-wrong retractions. (2) When the world genuinely *changed* (update, not revision): applying revision semantics to a moved world silently corrupts state — the Katsuno–Mendelzon trap. (3) Logical-omniscience: AGM operates on deductively closed sets; real stores are not closed, so base-revision variants are mandatory and the closure guarantee weakens to the computed fragment.

**Falsifiable experiment / KILL CONDITION.** Build a golden corpus of N retraction scenarios (premise withdrawn → required downstream withdrawals, hand-labeled). Run the clingo encoding *and* TweetyProject; require both to withdraw exactly the labeled set under the declared entrenchment. **KILL if:** on realistic autoharn corpora the *entrenchment ordering cannot be elicited stably* (different qualified maintainers produce orderings that flip ≥X% of safety-relevant verdicts), because then the "minimal change" is a free parameter wearing a proof's costume — [REVISE](../KEY.md#revise) would be better served by a coarser append-only audit log ([RECORD](../KEY.md#record)) than by a precise operator over an arbitrary ranking. The operator is sound; its *inputs* are the residual risk, and that risk must be measured, not assumed away.

## References (edification)

- **Alchourrón, Gärdenfors & Makinson (1985), "On the Logic of Theory Change," *J. Symbolic Logic* 50** — the founding paper; teaches the contraction/revision postulates and partial-meet construction.
- **Gärdenfors, *Knowledge in Flux* (1988)** — the canonical textbook; teaches entrenchment, the Levi/Harper identities, and the philosophical intuition end-to-end.
- **Darwiche & Pearl (1997), "On the Logic of Iterated Belief Revision," *AIJ* 89** — teaches why AGM alone is too weak for repeated revision and how ranking functions fix it.
- **TweetyProject Belief Dynamics docs ([tweetyproject.org/lib](http://tweetyproject.org/lib/)) + Delgrande–Schaub Equibel** — teaches the runnable bridge from postulates to a clingo/Java solver.

Sources: [TweetyProject](https://tweetyproject.org/), [GitHub](https://github.com/TweetyProjectTeam/TweetyProject), [Delgrande, Belief Revision under ASP](https://www2.cs.sfu.ca/~jim/publications/LPNMR13.pdf).


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
