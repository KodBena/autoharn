# 19 — Deontic & Normative Logic (SDL, dyadic, defeasible, I/O logic, norm-change)

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Coined terms → root **[GLOSSARY.md](../../../../GLOSSARY.md)**. See the [index](../README.md).

The logic of *obligation, permission, and prohibition as first-class objects* — what the system **ought** to do, distinct from what it **will** do — including how duties detach from conditions, survive their own violation, and change when norms are added or repealed.

## Primer (becoming broadly expert)

Standard Deontic Logic (SDL) is modal **KD**: `O p` ("p is obligatory") with the single axiom `O p → ¬O¬p` (no genuine conflicts) and necessitation. SDL is famous mostly for its **paradoxes**, each of which is a real engineering failure mode: the *Good Samaritan*, *Ross's*, *gentle-murderer*, and above all **Chisholm's contrary-to-duty paradox** — SDL cannot consistently say "you ought not do X, but if you do X you ought to do Y." The repairs *are* the field. **Dyadic deontic logic** (von Wright; Hansson; Åqvist's system **E**; **Carmo–Jones**) makes obligation conditional and defeasible: `O(p | c)`, "p is obligatory *in context* c," with a preference/ideality ordering over worlds so that sub-ideal-but-best behaviour is well-defined. **Input/Output logic** (Makinson & van der Torre) drops truth-functional modality entirely: norms are *detachment machines* mapping situations (input) to obligations (output), with explicit operations and `out`/constraint variants for contrary-to-duty. **Defeasible deontic logic** (Nute; Governatori) adds defeasible rules, priorities, and **norm-change / AGM-style revision** (Alchourrón) — derogation and amendment as principled operations. The throughline: detach the right duty, keep reasoning *after* a violation, and never let one conflicting norm explode the rule base.

## Obligations it discharges

- **TRIG — Conditional Activation (primary fit).** Conditional norms `O(act | trigger)` *are* the detachment locus. I/O logic's `out` operator is literally "given this input situation, which obligations fire?" — factual detachment with the antecedent checked, robust to a chosen reasoning mode (with/without reusable output for cascading triggers). **Guarantee:** every active duty is *derivable from a named norm and a satisfied condition*; a missed or spurious trigger becomes a missing/extra output line you can diff, not an emergent behaviour.
- **DEGRADE — Contrary-to-Duty Reparation (primary fit).** This is the reason dyadic/CTD logics exist. Carmo–Jones gives a *defined* semantics for "primary obligation already violated → secondary reparative obligation now in force," distinguishing actual-vs-ideal worlds. **Guarantee:** "we are already non-compliant" has model-theoretic meaning; the safe-state/reparation regime is *entailed*, not bolted on, so a first violation does not cascade into undefined behaviour.
- **AUTH — Permission Closure & Norm Precedence (strong fit).** Deontic logic natively separates `O`/`P`/`F` and (in defeasible form) carries **priorities** between norms — exactly the standing-norm-vs-operator-override derogation order. Permission is the gate; the open/closed-world closure is the choice of weak vs strong permission. **Guarantee:** an act is permitted only via an explicit `P` derivation; override precedence resolves deterministically and is logged as a rule-priority decision.
- **CONSIST — Contradiction Containment (strong fit).** Constrained I/O logic and defeasible deontic logic are *designed* to take an inconsistent norm set and return a maximal consistent obligation output (or flag a genuine dilemma) **without ex-falso**. **Guarantee:** conflicting duties yield a quarantined dilemma marker, not a vacuous "everything permitted."
- **COMMIT — Directed Commitment (moderate fit).** Directed/bilateral deontic logic (obligation *of* debtor *toward* creditor) frames the lifecycle; pairs naturally with commitment-state machines.
- **REVISE — Norm-change (moderate fit).** AGM-on-norms (derogation/amendment) is the *normative* slice of REVISE — when a regulation is repealed, which derived duties withdraw.

**Does NOT serve:** real-time deadlines and WCET (**PROG** — deontic "eventually" has no metric clock; use timed/temporal logic), reachability **INV** (use model checking), float **CALIB**, and provenance-of-facts **PROV** (deontic logic governs duties, not evidence chains). It tells you *what ought to happen*, never *that the implementation does it* — that gap is **INDEP**'s job.

## A worked encoding

autoharn **AUTH/TRIG**: an AI agent *may propose* a spillway-control change but *must not deploy* it without human sign-off; if it deploys anyway (CTD), the change *must* be auto-reverted. Defeasible deontic logic in `s(CASP)` (runnable on the installed SWI-Prolog):

```prolog
:- use_module(library(scasp)).

% Permission to propose is unconditional for the agent.
permitted(agent, propose(Change)) :- change(Change).

% Prohibition: deploying without human approval.
forbidden(agent, deploy(C)) :- change(C), not approved_by_human(C).

% Contrary-to-duty: GIVEN a forbidden deploy happened, revert is obligatory.
obligatory(system, revert(C)) :- deployed(C), forbidden(agent, deploy(C)).

% Gate: an action is BLOCKED unless explicitly permitted and not forbidden.
blocked(A, Act) :- forbidden(A, Act).
blocked(A, Act) :- action(A, Act), not permitted(A, Act).

change(spillway_patch).
deployed(spillway_patch).        % the agent deployed it
% approved_by_human(spillway_patch).   % <-- absent: no sign-off

?- obligatory(system, revert(spillway_patch)).
```

s(CASP) returns the goal **with a justification tree**: `revert` is obligatory *because* `deploy` was forbidden *because* no `approved_by_human` fact held — a replayable, auditable derivation (serving **RECORD**). Flip in `approved_by_human/1` and the obligation vanishes; that diff is the mechanical gate. The closed-world `not` makes the permission closure *explicit and inspectable* rather than implicit.

## Automation & tooling (the git-clone-runnable question)

This logic is **well-tooled and runs today** on the installed stack — no shrug needed.

- **s(CASP)** (Apache-2.0; SWI-Prolog port actively maintained, packable into the installed SWI-Prolog 9.3.31). Goal-directed CASP with classical negation and constructive **justification trees** — ideal for **AUTH/TRIG/CONSIST**. A 2025 paper (*Modeling Deontic Modal Logic in s(CASP)*, arXiv:2507.05519) gives global-constraint encodings of `O`/`F` that resolve the classic paradoxes. **Primary autoharn host.**
- **SPINdle** (LGPLv3, Java, v2.x; defeasible + modal/deontic extensions, scales to >10⁶ rules). Dedicated defeasible-deontic reasoner with rule **priorities** — the natural engine for **AUTH** precedence and **DEGRADE** when you want a fast, decidable, non-interactive batch checker rather than a proof tree.
- **LogiKEy / Carmo–Jones DDL in Isabelle/HOL** (Benzmüller et al.; Isabelle is BSD-style, embedding in the AFP). A *faithful, sound-and-complete* shallow embedding of dyadic deontic logic into HOL — the heavyweight option when a CTD reparation argument must be **machine-checked** at the highest assurance (qualifiable for **INDEP/CALIB**), with `nitpick` countermodels for free.
- **I/O Logic Workbench / `rio`** (Steen; open-source, browser + TPTP CLI). `rio` (2026) reduces I/O detachment to **SAT** — directly usable to compute "which obligations fire" against the installed Z3 or any SAT backend for **TRIG**.

**Composition path for autoharn:** encode norms once as defeasible rules; route them to s(CASP) for *explained* per-decision gating (the runtime gate), to SPINdle for bulk consistency sweeps over the whole norm set, and escalate any CTD chain whose correctness is load-bearing to the Isabelle embedding for a checked proof. All four are leverageable from the installed Z3/SWI-Prolog/clingo without new infrastructure.

## Honest leverage & kill-condition

**Load-bearing** for autoharn's **AUTH, TRIG, DEGRADE, CONSIST**: these obligations are about *norms and their detachment*, which is precisely deontic logic's object of study, and the tools emit auditable derivations.

**Where it is ash:** the deontic layer governs the *spec of duties*, not their *execution*. It can prove "on this fact base, revert is obligatory" but **cannot** prove the deployed code actually reverts — that is an INV/PROG/INDEP obligation discharged by model checking and qualified test, not by `O`. Treating a green deontic check as evidence of *behavioural* compliance is the trap.

**Falsifiable experiment:** build a golden corpus of 40 normative scenarios (Chisholm CTD, conflicting overrides, expired interlock bypass, missed/spurious trigger), each with an adjudicated obligation set. Run s(CASP) and SPINdle; require justification trees to match the warranted derivation, and apply **mutation testing** (drop a norm, flip a priority, negate a trigger) — every mutant must change the output.

**KILL CONDITION:** if, on this corpus, the encodings (a) disagree with each other or the adjudicated set on >5% of CTD/conflict cases, **or** (b) a non-trivial mutant leaves the obligation output unchanged (the check is insensitive to the norm it claims to enforce), then deontic logic is *demoted to a documentation/spec aid* for autoharn and the runtime gate falls back to explicit imperative authorization checks. Honest ash is an acceptable result; a deontic check that passes regardless of the norms is not.

## References (edification)

- **Gabbay, Horty, Parent, van der Meyden, van der Torre (eds.), *Handbook of Deontic Logic and Normative Systems*, Vols. 1–2** — the field's canonical reference; teaches SDL, dyadic, I/O, and defeasible systems and *why each paradox forced a new system*.
- **Carmo & Jones, "Deontic Logic and Contrary-to-Duties" (2002)** — teaches the actual-vs-ideal-worlds semantics that gives **DEGRADE/CTD** a defined meaning.
- **Makinson & van der Torre, "Input/Output Logics" (JPL 2000)** — teaches norms-as-detachment-machines, the cleanest fit for **TRIG**.
- **Arias et al., *Modeling Deontic Modal Logic in s(CASP)* (arXiv:2507.05519, 2025)** — teaches the runnable encoding on the installed stack, paradoxes-resolved, with justification trees for **RECORD**.


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
