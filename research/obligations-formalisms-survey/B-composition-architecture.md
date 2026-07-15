# B — Composition: many formalisms, one accountable ledger

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Abbreviations & tiers → **[KEY](KEY.md)**; coined terms → root **[GLOSSARY.md](../../GLOSSARY.md)**; index → [README](README.md).

**Key for this document.** Full reference → [KEY.md](KEY.md).  Guarantee-strength **5** deductive (kernel-checked) · **4** exhaustive-over-model · **3** bounded · **2** calibrated-CI · **1** defeasible.  Cost **T0** present locally · **T1** pip/jar · **T2** compile-from-source · **T3** encode into an existing host.

| code | meaning |
|---|---|
| [INV](KEY.md#inv) | Safety-Invariant Maintenance — an "always"/barrier property holds in every reachable state; no silent excursion |
| [AUTH](KEY.md#auth) | Action Authorization & Norm Precedence — every effect is gated by an explicit permission; closure + norm priority resolve deterministically |
| [ATTR](KEY.md#attr) | Agency Attribution — every change bound to an identified agent who saw-to-it and could-have-done-otherwise |
| [PROV](KEY.md#prov) | Claim Provenance & Groundedness — every claim resolves via a finite replayable chain to primary evidence; no free-floating fact |
| [REVISE](KEY.md#revise) | Belief Revision & Retraction — retracting a premise revisits every dependent conclusion; corrections append-only, AGM-rational |
| [CALIB](KEY.md#calib) | Substantiated & Calibrated Claims — each claim backed by a reproducible artifact at strength matched to its kind; honest confidence |
| [STRUCT](KEY.md#struct) | Structural Soundness by Construction — defect classes made unrepresentable (typed absence, honest signatures, fault isolation), not patched |
| [TRACE](KEY.md#trace) | Traceability, Coverage & Change-Impact — hazard→req→design→code→test links total & navigable; coverage measured; change-impact closed on the artifact |
| [INDEP](KEY.md#indep) | Independent Adjudication & Tool Qualification — load-bearing checks discharged by a mechanism that does NOT share the producer's bias (no LLM-judging-LLM) |
| [RECORD](KEY.md#record) | Auditable Decision Record & Ordering — a tamper-evident trail authored at decision time; happens-before enforces criterion-before-result, approval-before-action |

Verified. The guardrail propagates self-certification correctly (cycle + downstream lose their external descent and flag; `final_clearance` survives because it retains one grounded warrant through `change_attributed`), and the weakest-link `#min` collapses a 5-4-2-3 chain to strength 2. One sound-ness subtlety surfaced and is noted below. Here is the deliverable.

---

## COMPOSITION ARCHITECTURE — one accountable ledger over 27 discharge engines

The 27 sections each answer "which formalism matches this obligation's failure mode." This section answers the question that makes `git clone autoharn` a system rather than a toolbox: **once Z3 has proved an [INV](KEY.md#inv) barrier, TLC has exhausted a protocol, clingo has closed a permission set, NumPyro has returned a calibrated tail probability, and SWI-Prolog has emitted a deontic justification tree — what binds those heterogeneous verdicts into a single record a Federal-Reserve auditor can replay, and what stops the binding layer from quietly certifying itself?** The architecture has four load-bearing parts: a **claim ledger** (the substrate), a **justification spine** (the lingua franca), **predicate hand-off seams** (how a guarantee in one logic becomes an input to another with its strength preserved), and a **self-audit layer** (GL/Löb as the anti-self-certification guardrail). None of it requires an engine beyond the installed Postgres + clingo + Z3 + SWI-Prolog stack.

### 1. The substrate: an append-only claim ledger (RECORD is the floor, not a feature)

Every discharge — regardless of which engine produced it — writes exactly one immutable row:

```
discharge(
  obligation_id, obligation_kind,        -- e.g. INV, the taxonomy cell
  artifact_hash,                         -- the exact code/spec under analysis
  formalism, tool, tool_version,         -- 'separation-logic', 'verifast', '25.11'
  encoding_hash,                         -- hash of the LLM-authored .lp/.smt2/.tla (itself on trial)
  verdict,                               -- pass | fail | unknown  (unknown ≠ pass, fail-closed)
  certificate,                           -- the native proof object: Z3 unsat-core, TLC trace, clingo stable model, Lean term
  guarantee_strength,                    -- 5..1, see §3
  recheck_tool, recheck_verdict,         -- the diverse oracle (INDEP); NULL is itself a finding
  witness,                               -- counterexample / countermodel on fail
  decision_clock,                        -- Lamport/logical tick (RECORD happens-before)
  authored_at, authored_by              -- wall-clock + authenticated actor (ATTR)
)
```

Two Postgres-level invariants make this a ledger and not a log. **(a) Append-only with dated sibling-revision:** a correction never `UPDATE`s a row; it inserts a new row citing `supersedes`, so "what did we believe at decision time" ([REVISE](KEY.md#revise)'s append-only demand, [RECORD](KEY.md#record)'s verbatim demand) survives by construction — enforced by a `REVOKE UPDATE/DELETE` and a `BEFORE` trigger. **(b) Criterion-before-result / approval-before-action:** a `CHECK` that the gating `discharge` row's `decision_clock` strictly precedes the action it gates — the mechanical kill for the NYSE clock-skew failure ([RECORD](KEY.md#record) #17). The logical clock, not wall-clock, is authoritative because async writes and clock skew are precisely the attack surface; wall-clock is recorded but never adjudicated on.

This is the seam where TLA+'s *temporal-ordering-on-the-model* (it proves the design admits no out-of-order behavior) hands off to *temporal-ordering-on-the-artifact* (Postgres enforces it on the real trail). Neither alone discharges [RECORD](KEY.md#record); the model proves the protocol can be ordered, the ledger proves this run was.

### 2. The spine: justification-logic terms as the cross-engine currency

A bare verdict (`pass`) is not admissible. A claim `C` enters the ledger only as a **justification term** `t : C` in the Artemov LP algebra (§ Justification Logic), and the spine is the single place all 27 engines become commensurable:

- **A tool certificate is a leaf, not a root.** Z3's `unsat`, TLC's clean enumeration, clingo's stable model are each a constant `c : F` — but they become an *admitted* constant-specification root **only after** an independent diverse oracle re-checks them (cvc5 replays the Z3 proof; µ-toksia re-adjudicates the clingo AF; a second NumPyro seed + SBC re-runs the posterior). This is the `!t : (t:F)` operator made operational: the ledger stores *evidence that the evidence was checked, by a channel that does not share the producer's bias*. An un-rechecked certificate is a leaf with no warrant — the spine refuses it exactly as it refuses a confabulated citation.
- **`app` (application) internalizes cross-obligation detachment.** When [INV](KEY.md#inv)'s barrier proof *uses* [CALIB](KEY.md#calib)'s calibrated bound as a monitored assumption, the composite witness is `app(s_INV, t_CALIB)` — the [INV](KEY.md#inv) proof of `(bound → safe)` applied to the [CALIB](KEY.md#calib) justification of `bound`. The dependency is now a first-class, replayable object, not a comment in two disconnected reports.
- **`+` (sum) is the [INDEP](KEY.md#indep) corroboration operator.** "Two *distinct, separately-checking* justifications exist" — the one production case that justifies JL over plain Datalog provenance — is `s + t` where `s` and `t` are required to trace to non-common-cause roots. This is how the [ATTR](KEY.md#attr)/INDEP demand "real diversity, no shared spec defect" becomes an object-level, queryable fact rather than an organizational promise.

The spine is hosted as a Horn-clause `justifies/2` meta-interpreter in SWI-Prolog (the JL section's worked encoding) for per-claim *checking*, with the EDB of admitted constants in Postgres. Checking a supplied witness is decidable linear-bottomed SLD resolution — the term **cannot lie**: a forged `app(cite, enc_9999)` whose leaf is not in the store simply fails to re-check.

### 3. Legibility: the guarantee-strength lattice and weakest-link composition

[CALIB](KEY.md#calib)'s hardest clause — "confidence that **composes correctly**" — is discharged here, mechanically, not narratively. Each discharge carries an ordinal:

```
5 deductive proof (kernel-checked: Lean/Rocq Qed, Z3 unsat re-checked)
4 exhaustive-over-model (TLC/NuSMV/mCRL2 — sound relative to the abstraction)
3 bounded (BMC/k-bounded SMT/finite-grounding ASP — sound to depth k only)
2 calibrated-CI (NumPyro/ProbLog — exact propagation of stated priors)
1 defeasible (ILP-recovered rule, grounded-extension verdict — conjectural beyond corpus)
```

A composite claim's effective strength is the **meet (min) over its support graph** — the weakest link governs, and this is the verified core (run on clingo 5.8.0):

```prolog
eff(C,V) :- str(C,V), external(C).
eff(C,M) :- claim(C), M = #min { Vs : support(C,S), eff(S,Vs) ; Vo : str(C,Vo) }.
```

On the dam chain `signed_egfr(5) → pore_calibrated(2) → barrier_inv(4) → deploy_permitted → final_clearance`, the verified output is `eff(final_clearance, 2)`: a deploy authorization that *looks* proof-backed inherits the strength of its **calibrated** link. This is the explicit, falsifiable artifact that kills [CALIB](KEY.md#calib)'s "wrong bar" failure — you cannot launder a probabilistic bound into a barrier certificate, because the meet exposes the 2 at the top of the chain, and the ledger gates deploy on `eff ≥ required_strength(obligation)`. The **residual-risk** field is dually the *union* of each link's modeled-vs-real gap (the TLA+ abstraction gap ∪ the SCM-faithfulness gap ∪ the prior-misspecification gap), never the min — strength is bottlenecked, risk accumulates.

**One soundness subtlety the verification surfaced and the architecture must enforce:** strength composition is only sound on the **grounded** subgraph. In the injected-cycle mutant, `#min` over a mutual-admiration loop returned a spurious `eff=4` for the self-certifying claim. Therefore the pipeline order is mandatory and gated: **(i)** run the Löb guardrail (§4); **(ii)** delete every `self_certifying` claim from the support graph; **(iii)** only then compute `eff`. Computing strength before groundedness lets a cycle manufacture confidence — a qualification gate in autoharn's own test suite.

### 4. The seams: predicate hand-off between formalisms

Composition is not "run 27 tools and staple the PDFs." It is a directed graph of **exported-atom → imported-fact** hand-offs, each one a row whose `support` edge is checked by the spine:

- **DL/OWL → TLC/clingo (atemporal → temporal).** A Description-Logic reasoner classifies the per-tick state (`case : Tier1`); that realized predicate is exported as a TLA+/clingo input fact, and the model checker discharges the across-time [INV](KEY.md#inv)/PROG envelope. DL supplies *which bucket now*; TLC supplies *always*. Composite strength `min(DL-exact=5, TLC-exhaustive=4)=4`, residual = the abstraction gap.
- **Datalog/ProbLog → Z3/SMT (grounded fact → numeric check).** Datalog grounds the provenance chain to a primary measurement ([PROV](KEY.md#prov)); that grounded value becomes the leaf constant Z3 reasons over for the [STRUCT](KEY.md#struct)/INV bound. A reading with no current-encounter grounding is simply *not in the least model*, so Z3 is never handed an ungrounded number — the superseded-encounter dose-reduction bug dies at the Datalog seam, before SMT runs.
- **STL/MTL → [RECORD](KEY.md#record), gated on timestamp provenance.** RTAMT's deadline robustness is only as honest as its clock; the seam *requires* the timestamp source to be an independent, signed input (an `external` root), or the STL verdict is downgraded — closing the coupling where a monitor over skewed clocks launders the very [RECORD](KEY.md#record) failure it should catch.
- **Deontic/STIT → ledger (norm → enforced gate).** s(CASP) proves `O(revert)` *with a justification tree*; that tree is the certificate, but the deontic layer governs the *spec of duties, not behavior*. The seam mandates that a deontic `pass` is composed via `app` with an [INV](KEY.md#inv)/INDEP discharge proving the code *actually reverts* — a green deontic check alone can never reach `eff ≥ 3` for a behavioral obligation. This is the architecturally-enforced version of every deontic section's kill-condition.
- **Belief-revision / argumentation → the whole ledger ([REVISE](KEY.md#revise) is a graph operation, not a row).** When a premise leaf is retracted (corrected piezometer calibration), the spine recomputes `justifies/2`: every `app`-term whose leaf vanished loses its witness, and the dependent `discharge` rows are re-adjudicated (new sibling rows, old ones retained). The grounded-extension / AGM-minimize encodings (verified runnable in the respective sections) are the *operators*; the ledger is the *substrate they operate on*. The stale "spillway safe" verdict cannot survive its own evidence because it is an `app`-term, and `app` re-checks to failure the instant its measurement leaf is gone.

### 5. The self-audit layer: GL/Löb as the guardrail, and the coverage anti-paradox

The mission was wounded by exactly one failure mode — "the deflation-detector that deflated," an LLM judging LLM output and ratifying its shared bias. The composition layer's defense is **structural, not vigilant**: it is the provability-logic guardrail (§ GL/Löb), and it runs as the gate on every load-bearing claim (verified, clingo):

```prolog
grounded(C) :- external(C).
grounded(C) :- support(C,S), grounded(S).
self_certifying(C) :- claim(C), not grounded(C).
```

`external/1` is bound **only** to (a) cryptographically signed primary inputs and (b) tool certificates that passed a diverse re-check — never to a node the producer authored. The verified mutant run confirms the teeth: a laundered `barrier ↔ llm_lemma` cycle flags `self_certifying(llm_lemma)`, `self_certifying(barrier_inv)`, and the downstream `self_certifying(deploy_permitted)`, while `final_clearance` correctly *survives* because it retains an independent grounded warrant through `change_attributed`. This is Löb's theorem operationalized: `□A → A` (the move "autoharn derived it, therefore it holds") adds nothing; only descent to a source autoharn did not author terminates a justification chain. The clingo stable-model semantics *is* the converse-well-founded fixpoint GL's frames require — the guardrail is not an analogy to GL, it is GL's frame condition computed.

**The coverage anti-paradox (the deepest seam).** autoharn must prove its own [TRACE](KEY.md#trace) coverage — "every obligation in the ratified mandate has a discharge record." This is the one place the system reasons about itself, and Löb forbids it doing so naively: a coverage prover that certifies its own completeness from the ledger's self-report is the `□(coverage) → coverage` collapse. The architecture's rule: the **mandate enumeration is a separate signed input** (an `external` root, authored by the ratifying authority, not by autoharn), and the coverage query is a *differential* between that independent enumeration and the ledger — an orphan (code with no obligation) or a gap (mandated obligation with no discharge) is a set-difference, adjudicated against a source the prover cannot have written. Gödel's `¬□⊥` is the discipline: autoharn may not prove its own consistency/coverage from inside; it exhibits the gap or descends to an external mandate.

### 6. Qualifying the composition layer itself (it is on trial too)

The spine, the strength meet, and the guardrail are LLM-authorable code, so they inherit the session's hardest lesson: **no LLM judge in the loop, only mechanical gates.** The composition layer ships with: **golden fixtures** (the verified clearing/blocking assurance graphs as pinned oracles); **mutation tests** (inject a self-cert cycle → guardrail must flag it and downstream; flip a strength leaf → meet must change; drop a re-check → certificate must become an inadmissible leaf); and **differential cross-engine** agreement (the same assurance graph evaluated in clingo *and* as a Datalog reachability query in Postgres recursive CTEs — disagreement disqualifies the encoding, not the obligation).

**KILL CONDITION for the architecture.** If, on a corpus of seeded assurance graphs, the guardrail fails to flag any laundered self-cert cycle, OR the strength meet ever reports a composite strength exceeding its weakest grounded link, OR `external/1` can be satisfied by a producer-authored node (the independence tag is not mechanically enforced upstream by [PROV](KEY.md#prov)) — then the composition is decorative and the ledger is a log with extra ceremony. The architecture survives only if (i) every laundered cycle is caught, (ii) the meet is monotone-down over the grounded subgraph, and (iii) every `external` root resolves to a signed input or a diversely-rechecked certificate. The strength computation running *before* the groundedness gate is itself a registered defect class (it manufactured a spurious `eff=4` in test) — the gate order is part of the qualified artifact, not an implementation detail.

**Honest residual.** This architecture composes *guarantees about models and encodings*; it cannot exceed the fidelity of the weakest abstraction in any chain, and the weakest-link meet is precisely the mechanism that refuses to pretend otherwise. Its genuine, non-cheerleading contribution is that it makes the residual risk of a 27-engine composition a single computed, falsifiable number per claim — and makes self-certification a structural impossibility rather than a reviewer's good intentions.

**Integration seams, one line each (the map):** Postgres = substrate ([RECORD](KEY.md#record)/REVISE append-only, happens-before). SWI-Prolog `justifies/2` = spine checker ([PROV](KEY.md#prov), the `app`/`+`/`!` algebra). clingo = assurance-graph evaluator (the Löb guardrail + strength meet + [AUTH](KEY.md#auth)/CLASS/REVISE operators). Z3 + cvc5 = the diverse-oracle pair that turns a certificate into an admissible root ([INDEP](KEY.md#indep)/CALIB). Every other engine (TLC, mCRL2, NuSMV, RTAMT, VeriFast, NumPyro, s(CASP), HP2SAT, …) is a *leaf producer* whose verdict is inadmissible until re-checked and whose strength is governed by the meet.


---
*Cross-cut — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
