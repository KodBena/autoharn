# 20 — STIT & Logics of Agency / Responsibility attribution

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Abbreviations & tiers → **[KEY](../KEY.md)**; coined terms → root **[GLOSSARY.md](../../../GLOSSARY.md)**; index → [README](../README.md).

**Key for this document.** Full reference → [KEY.md](../KEY.md).  Guarantee-strength **5** deductive (kernel-checked) · **4** exhaustive-over-model · **3** bounded · **2** calibrated-CI · **1** defeasible.  Cost **T0** present locally · **T1** pip/jar · **T2** compile-from-source · **T3** encode into an existing host.

| code | meaning |
|---|---|
| [INV](../KEY.md#inv) | Safety-Invariant Maintenance — an "always"/barrier property holds in every reachable state; no silent excursion |
| [TRIG](../KEY.md#trig) | Conditional Activation — a triggered duty fires exactly when (and only when) its precondition holds |
| [DEGRADE](../KEY.md#degrade) | Contrary-to-Duty Reparation — once already violated/faulted, enter a DEFINED safe regime — not undefined behaviour |
| [AUTH](../KEY.md#auth) | Action Authorization & Norm Precedence — every effect is gated by an explicit permission; closure + norm priority resolve deterministically |
| [ATTR](../KEY.md#attr) | Agency Attribution — every change bound to an identified agent who saw-to-it and could-have-done-otherwise |
| [PROV](../KEY.md#prov) | Claim Provenance & Groundedness — every claim resolves via a finite replayable chain to primary evidence; no free-floating fact |
| [REVISE](../KEY.md#revise) | Belief Revision & Retraction — retracting a premise revisits every dependent conclusion; corrections append-only, AGM-rational |
| [COHERE](../KEY.md#cohere) | Single-Authority / Single-Writer Coherence — one authoritative definition per fact; one owner per mutable state; references resolve to one correct target |
| [INDEP](../KEY.md#indep) | Independent Adjudication & Tool Qualification — load-bearing checks discharged by a mechanism that does NOT share the producer's bias (no LLM-judging-LLM) |
| [RECORD](../KEY.md#record) | Auditable Decision Record & Ordering — a tamper-evident trail authored at decision time; happens-before enforces criterion-before-result, approval-before-action |

STIT ("sees to it that") is the modal logic of *what an agent brings about by acting*, distinguishing an outcome an agent guaranteed and could have avoided from one that merely happened. It is autoharn's native logic for binding state mutations to a responsible, alternative-bearing agent.

## Primer (becoming broadly expert)

STIT, due to Belnap, Perloff and Xu (*Facing the Future*, 2001), interprets agency over *branching time*: at each moment, histories fan out into the future, and each agent partitions the histories through that moment into the **choice cells** available to it now. The Chellas operator `[α stit: φ]` holds at a moment/history pair when φ is guaranteed across *every* history in α's currently-selected cell — α's choice *settles* φ regardless of what other agents and nature do (**independence of agents** is an axiom). The **deliberative** variant `[α dstit: φ]` adds the **negative condition**: φ is not already settled-true *independently* of α's choice — i.e., α **could have done otherwise**. That conjunction (guaranteed-by-me AND avoidable-by-me) is exactly the counterfactual core of moral/legal responsibility, separating authorship from coincidence and from coercion. Horty (*Agency and Deontic Logic*, 2001) grafts utilitarian obligation on top: a *dominance ought* says an agent ought to see to φ when choosing φ dominates across the choices of others, giving agent-relative obligations and a clean treatment of what one is to blame for. STIT is the logic built to discharge **attribution**: who saw to it, with a real alternative.

## Obligations it discharges

- **[ATTR](../KEY.md#attr) — Agency Attribution & Non-Repudiable Change (primary).** STIT's `dstit` *is* the formal content of "an identified agent saw to it that, and could have done otherwise." The failure mode — responsibility voids, many-hands, accountability pinned on an agent with no exercisable alternative — maps directly onto STIT's two conditions failing. If no agent's selected choice cell guarantees the outcome, attribution is genuinely void (and autoharn should *say so* rather than rubber-stamp a shared account); if the outcome is settled-true across all of the agent's cells, the negative condition fails and blaming that agent is a category error STIT mechanically detects. **Guarantee strength:** a model-checkable necessary condition for legitimate attribution — it cannot manufacture a human signer, but it can *refuse* any attribution lacking guarantee-plus-alternative.

- **[TRIG](../KEY.md#trig) — Conditional Activation.** Deontic STIG handles agentive detachment: an obligation `O[α stit: φ]` activates only when α's choice structure makes φ achievable, separating "α ought to see to φ" from non-agentive "φ ought to obtain." This blocks duties detached onto agents who cannot influence the trigger.

- **[DEGRADE](../KEY.md#degrade) — Contrary-to-Duty Reparation.** Horty's dominance-ought composes contrary-to-duty structure agent-relatively: when the primary `O[α stit: φ]` is already violated, the *next-best dominant choice* defines the reparational duty, rather than ex-falso collapse.

- **[AUTH](../KEY.md#auth)** (secondary): STIT distinguishes "may propose" from "may deploy" as choices in different cells, but permission-closure and norm-precedence are better carried by deontic/defeasible layers; STIT supplies only the agency substrate.

**Does NOT serve:** invariants and timing (**[INV](../KEY.md#inv)/PROG** — STIT has no metric time or trace semantics), provenance/groundedness (**[PROV](../KEY.md#prov)**), belief revision (**[REVISE](../KEY.md#revise)**), data-flow coherence (**[COHERE](../KEY.md#cohere)**). Routing those to STIT would over-reach badly.

## A worked encoding

[ATTR](../KEY.md#attr) for a Federal Reserve risk-limit loosening. Model the moment's choice structure in ASP and derive `dstit`.

```prolog
% histories through the current moment
history(h1;h2;h3;h4).
agent(operator).

% operator's available choices partition the histories into cells
cell(operator, c_loosen, h1). cell(operator, c_loosen, h2).
cell(operator, c_hold,   h3). cell(operator, c_hold,   h4).
selected(operator, c_loosen).          % the choice actually made

loosened(h1). loosened(h2).            % outcome per history (h3,h4: not loosened)

% Chellas positive condition: phi guaranteed across the WHOLE selected cell
in_selected(A,H) :- selected(A,C), cell(A,C,H).
pos_fail(A)  :- in_selected(A,H), not loosened(H).
positive(A)  :- agent(A), not pos_fail(A).

% Deliberative negative condition: could have done otherwise
could_otherwise(A) :- agent(A), history(H), not loosened(H).

dstit(A) :- positive(A), could_otherwise(A).

% ATTR gate: a world-affecting change with no dstit agent is a responsibility void
void :- not some_agent_saw_to_it.
some_agent_saw_to_it :- dstit(_).
#show dstit/1. #show void/0.
```

`clingo` returns `dstit(operator)` — attribution holds. Mutate the fixture so every cell yields `loosened` (the limit drops no matter what the operator picks — a forced/automated change): `could_otherwise` fails, `dstit` empties, and `void` fires — autoharn flags a change that *looks* operator-authored but had no exercisable alternative (the shared-service-account / rubber-stamp pattern). This is a **golden/mutation fixture** for [INDEP](../KEY.md#indep) qualification of the gate.

## Automation & tooling (the git-clone-runnable question)

**No mature dedicated STIT prover exists.** The state-of-the-art decision procedure — Lyon & van Berkel, *Proof Theory and Decision Procedures for Deontic STIT Logics* (arXiv:2402.03148, 2024) — gives labeled sequent calculi `G3DS` with explicit loop-checking and (in)validity certificates, but reports **no runnable implementation**. Complexity is settled: single-agent STIT is **NP-complete**, multi-agent **NEXPTIME-complete**.

**Realistic encoding paths, both git-clone-runnable here:**

1. **ASP/clingo (recommended for autoharn).** A STIT *moment* is a finite choice structure; checking `cstit`/`dstit` at a fixed moment is exactly the grounded model query above. clingo 5.8.0 is installed. This covers the operational need — *attribution checking on a concrete decision record* — without paying full theorem-proving cost. For deontic dominance-ought, compose with **Deolingo** (deontic ASP over clingo, MIT-licensed, on PyPI) or the Defeasible-Deontic-Logic ASP encoding, layering Horty's ought atop the STIT substrate.

2. **SMT/Z3** for *validity* over a bounded set of agents/histories: encode the Kripke-STIT frame (choice-equivalence relations + independence-of-agents constraint) and check formula satisfiability; Z3 4.16 is present. Bounded, not a full decision procedure, but yields counter-models.

3. **Tableau/sequent host** (MetTeL or LoTREC) to *generate* a STIT prover from the `G3DS` rules — the heaviest path, warranted only if full multi-agent validity certificates become load-bearing.

Plan of record: clingo for per-decision attribution gates; Deolingo for the deontic layer; Z3 for bounded validity spot-checks.

## Honest leverage & kill-condition

**Load-bearing:** STIT turns [ATTR](../KEY.md#attr) from prose into a mechanical gate — every state mutation in the audit record must carry a choice structure in which some identified agent's `dstit` holds; absence is flagged as a responsibility void. The "could-have-done-otherwise" check is something neither logging nor permission systems express.

**Where it is ash:** STIT needs a *modeled choice structure* — the available cells and per-history outcomes. If autoharn cannot recover what alternatives the agent actually had, `dstit` is unfalsifiable theater (any outcome looks "chosen"). It also says nothing about timing, data provenance, or invariants.

**Falsifiable experiment:** instrument 50 real change events (Git/CI/operator actions); for each, reconstruct the choice cells from branch-protection + approval graph and run the clingo gate. **KILL CONDITION:** if, for a representative majority, the choice structure cannot be recovered from available audit data *without* hand-authored fiction — or if every recovered structure trivially yields `could_otherwise` (making the negative condition a rubber stamp) — then STIT is decorative for autoharn and [ATTR](../KEY.md#attr) must be carried by [RECORD](../KEY.md#record)/provenance instrumentation instead. If instead the gate catches the forced-change/shared-account pattern that approval logs pass, STIT is vindicated.

## References (edification)

- Belnap, Perloff, Xu, *Facing the Future* (2001) — the canonical source; teaches branching-time semantics, choice cells, and the cstit/dstit operators from the ground up.
- Horty, *Agency and Deontic Logic* (2001) — teaches how to put *obligation* on agents (dominance ought) and handle contrary-to-duty agent-relatively.
- Lyon & van Berkel, *Proof Theory and Decision Procedures for Deontic STIT Logics*, [arXiv:2402.03148](https://arxiv.org/abs/2402.03148) (2024) — the current decision-procedure/complexity picture and the certificate-generating calculi; your blueprint for a real solver.
- Broersen, "Deontic Epistemic stit logic distinguishing modes of mens rea" (J. Applied Logic, 2011) — teaches how STIT formalizes intentional vs. negligent agency, directly relevant to [ATTR](../KEY.md#attr)'s culpability gradations.

Sources: [Deolingo](https://pypi.org/project/deolingo/), [Lyon & van Berkel arXiv:2402.03148](https://arxiv.org/abs/2402.03148), [Defeasible-Deontic-Logic ASP](https://github.com/gvdgdo/Defeasible-Deontic-Logic).


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
