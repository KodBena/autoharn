# 01 — The obligation taxonomy (the spine)

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Abbreviations & tiers → **[KEY](KEY.md)**; coined terms → root **[GLOSSARY.md](../../GLOSSARY.md)**; index → [README](README.md).


> The responsibility classes a life-critical, AI-assisted software process must guarantee. Every formal-system section maps to these by name. (Anchors per code; the at-a-glance table is in [KEY.md](KEY.md).)

<a id="inv"></a>

1. **[INV](KEY.md#inv) — Safety-Invariant Maintenance.** WHAT: a stated invariant / prohibited region holds in *every* reachable state across the whole interval it is in force (an "always"-property, a "keep-it-true," a barrier never crossed); any departure surfaces through the strongest applicable channel rather than being silently absorbed. FAILURE MODE: a transient or unanticipated-interaction excursion violates the invariant and self-heals or is silently coerced — correct on average, lethal at one tick, invisible at origin. EXAMPLE: dam spillway logic admits a single undetected hour with reservoir level above crest during a flood.

<a id="prog"></a>

2. **[PROG](KEY.md#prog) — Liveness & Real-Time Progress.** WHAT: required events *eventually* occur and within their deadline — the safe-state transition completes, the alarm fires, the control loop closes each period; freedom from deadlock/livelock/starvation; WCET and resource bounds established. FAILURE MODE: no single state is wrong, but the required event never arrives (hang) or arrives too late; a correct-but-late safety action is a failure. EXAMPLE: a sepsis order is correct at every instant but the antibiotic is never actually hung within the 60-minute window.

<a id="trig"></a>

3. **[TRIG](KEY.md#trig) — Conditional Activation (Triggered Duty).** WHAT: an obligation that does not exist until its precondition fires must activate exactly when (and only when) its trigger is satisfied — correct antecedent→consequent detachment, robust to degraded sensing. FAILURE MODE: trigger missed (duty never activates though its condition held) or spurious (duty fires without grounds); the deontic-detachment locus. EXAMPLE: oxygen masks must deploy iff cabin altitude exceeds threshold, and a degraded sensor must not suppress or falsely raise the trigger.

<a id="degrade"></a>

4. **[DEGRADE](KEY.md#degrade) — Contrary-to-Duty Reparation & Safe-State Reaction.** WHAT: once a primary obligation is already violated (or a fault detected), the system enters a *defined* sub-ideal reparation regime / safe state within a bounded fault-tolerant interval — graceful degradation, not undefined behavior or an assertion-crash. FAILURE MODE: no semantics for "we are already non-compliant," so a first violation cascades; or a fault is silent, or its "safe state" is unsafe in context. EXAMPLE: NASA GNC loses attitude reference and must enter a defined safe-hold and reacquire, not crash the stack.

<a id="auth"></a>

5. **[AUTH](KEY.md#auth) — Action Authorization, Permission Closure & Norm Precedence.** WHAT: every world-affecting action is gated *before* the effect by an explicit, checkable permission; the closure rule for the unmentioned (open- vs closed-world) is declared; and the source/priority of every active norm (durable standing norm vs transient operator override) resolves deterministically via a logged derogation order. FAILURE MODE: authority leakage — an act permitted because no rule named it, a needed act blocked by wrong closure, or an ad-hoc override silently and permanently shadowing a standing safety norm. EXAMPLE: an AI "optimize" agent can push directly to the dam spillway-control production branch with no gate distinguishing "may propose" from "may deploy"; a maintenance interlock bypass outlives its window.

<a id="attr"></a>

6. **[ATTR](KEY.md#attr) — Agency Attribution & Non-Repudiable Change.** WHAT: every guaranteed outcome and every state mutation is bound to an identified agent who *saw to it* and *could have done otherwise*, with authenticated actor, timestamp, and authorizing intent — a defensible causal-deontic record. FAILURE MODE: responsibility voids ("the computer said no" / many-hands), accountability assigned to an agent who had no exercisable alternative, or a change attributed to a forgeable shared account. EXAMPLE: an overnight loosening of a Federal Reserve risk limit traces only to a shared service account, with no link to a human, ticket, or real alternative — rubber-stamp indistinguishable from supervision.

<a id="commit"></a>

7. **[COMMIT](KEY.md#commit) — Directed Commitment & Handoff Integrity.** WHAT: an obligation owed by one party to a counterparty has a tracked lifecycle (created, active, discharged, delegated, cancelled, violated) and either completes atomically or is explicitly unwound; a creditor is entitled to the discharge. FAILURE MODE: orphaned or double-counted commitments — a duty whose creditor vanished, a delegation that drops the obligation in transit, a discharge credited without entitlement satisfied. EXAMPLE: a DvP settlement leg that is neither discharged nor live is Herstatt-risk exposure; an ICU shift handoff where a pending action falls between two clinicians.

<a id="prov"></a>

8. **[PROV](KEY.md#prov) — Claim Provenance & Groundedness.** WHAT: every claim, datum, and decision resolves through a finite, inspectable, replayable chain to primary evidence (a measurement, signed input, cited authority, or admitted axiom) with verified integrity and pedigree; no free-floating fact. FAILURE MODE: an ungrounded assertion true in the store but unexplainable, or a confabulated chain that *looks* grounded (a citation that does not support its claim, a derivation edge with no warrant). EXAMPLE: an oncology system recommends a 40% dose reduction "for renal impairment" when no creatinine/eGFR value supports it — a flag inherited from a superseded encounter.

<a id="revise"></a>

9. **[REVISE](KEY.md#revise) — Belief Revision & Retraction Propagation.** WHAT: when a premise is retracted, refuted, or superseded, every conclusion that depended on it is automatically revisited and re-justified or withdrawn; corrections are append-only (old belief retained, not overwritten) and rational (AGM minimal-change / consistency-restoring). FAILURE MODE: destructive update erasing "what did we believe at decision time," or a stale conclusion reasoned forward from a premise already knocked out. EXAMPLE: a corrected piezometer calibration is written, but the "spillway safe" verdict derived from the old reading survives its own evidence.

<a id="consist"></a>

10. **[CONSIST](KEY.md#consist) — Consistency & Contradiction Containment.** WHAT: contradictory inputs are localized and quarantined so the system neither derives anything (ex falso) nor silently picks a side; requirement sets are free of unresolved antinomies; reasoning stays useful *in the presence of* conflict. FAILURE MODE: two conflicting facts let a classical engine prove everything (all gates pass vacuously) or arbitrarily launder the conflict into apparent consensus. EXAMPLE: two redundant sensors report mutually exclusive altitudes and a classical rule base derives a vacuously-true clearance for *every* maneuver instead of a quarantined degraded-mode decision.

<a id="calib"></a>

11. **[CALIB](KEY.md#calib) — Substantiated & Calibrated Claims.** WHAT: every load-bearing property claim is backed by a reproducible artifact with guarantee strength matched to the quantity's kind (logic invariant asserted exactly, float-sensitive numerics to a stated tolerance/CI), and carries a calibrated confidence that composes correctly and is matched against the obligation's required strength. FAILURE MODE: false authority (a claim wearing a proof's costume but never discharged by an independent oracle), over/under-confidence uncorrelated with evidence, or the wrong bar (bit-pinning a float, relaxing a logic invariant). EXAMPLE: a 4× chemo overdose ships green because a safety bound was "proven" by an LLM lemma that looks like a Z3 certificate but was never submitted to Z3.

<a id="class"></a>

12. **[CLASS](KEY.md#class) — Honest Sharp Classification.** WHAT: a value drawn from a closed vocabulary is assigned to exactly one cell of a total, mutually-exclusive-and-exhaustive partition (or explicitly to "unknown"); no entity is dual-classed, forced into the nearest-wrong bucket, or dropped through a gap; misfit is surfaced loudly, not absorbed. FAILURE MODE: silent mis-sortation into the closest-but-wrong category (the vocabulary *had* a slot, so nothing complains) or order-dependent dispatch when two rules match. EXAMPLE: a triage model lacks a code for a novel presentation and maps it to the nearest acuity tier, routing a time-critical patient to a low-priority queue.

<a id="struct"></a>

13. **[STRUCT](KEY.md#struct) — Structural Soundness by Construction.** WHAT: defect classes are made unrepresentable rather than patched — absence/failure carried as typed must-handle values, signatures honestly carrying what their bodies rely on, robust guards at boundaries (overflow/saturation/out-of-range), no undefined behavior, and spatial/temporal fault isolation so a fault cannot exceed its containment region. FAILURE MODE: a bug band-aided at one site while its class stays expressible; a "lying signature" or bare sentinel that lets a missed check pass silently; a low-criticality fault scribbling across a partition boundary into a safety function. EXAMPLE: a Fed settlement engine repeatedly mishandles "no quote" as magic `-1`; making absence an `optional`/`expected` the compiler refuses to ignore converts a recurring catastrophe into a compile error.

<a id="cohere"></a>

14. **[COHERE](KEY.md#cohere) — Single-Authority / Single-Writer Coherence.** WHAT: each fact crossing a boundary (wire layout, unit, key, config, API contract) has one authoritative definition every side *derives* from; mutable state has one owner with a coherence invariant quantified over all writers; every reference resolves to exactly one current, correctly-identified target; the deployed configuration is the verified one. FAILURE MODE: two sides re-author one truth and drift silently (each internally consistent); a second writer mutates without bumping a cache signature (torn/stale read); a dangling or aliased reference resolves to the wrong entity. EXAMPLE: two patients merged on a weak key — every reference resolves successfully, to the wrong human, and a targeted therapy is chosen against someone else's tumor.

<a id="trace"></a>

15. **[TRACE](KEY.md#trace) — Traceability, Coverage & Change-Impact Closure.** WHAT: hazard→requirement→design→code→test links are total and navigable both ways (no orphan code, no untraced requirement); verification *measurably* exercises the whole of what must be shown (structural/MC-DC, requirements, abnormal cases); every change's impact is analyzed across the actual dependency graph with exactly the affected verification re-run; the full ratified mandate is discharged and verified on the *artifact*, not narrated. FAILURE MODE: a requirement ships unimplemented, a lethal branch is never exercised, a change is scoped by intuition and perturbs an off-screen contract, or an executor silently narrows scope and marks unverified work "done." EXAMPLE: an AI asked to fix a comment in a 700-line flight-control mixer re-emits the file and transposes a positional sensor-fusion block; every test passes but the change touched contracts no test covered.

<a id="indep"></a>

16. **[INDEP](KEY.md#indep) — Independent Adjudication & Tool Qualification.** WHAT: load-bearing checks are discharged by a mechanism that does *not* share the producer's bias — genuine independence of verifier from developer, real diversity/no-common-cause across redundant channels, qualification of any tool (including an LLM-authored encoding) trusted in lieu of review, and a mechanical second opinion triggered when a problem demonstrably resists (≥2 mis-targeted attempts). FAILURE MODE: the checker inherits the blind spot it exists to catch (an LLM judging LLM output ratifies rather than tests — the deflation-detector that deflated), redundant channels share a hidden common cause, or an unqualified autocoder/analyzer's verdict is trusted. EXAMPLE: triple-redundant flight computers run identical software with a shared spec defect; all three agree on the wrong answer and outvote the one dissimilar correct channel.

<a id="record"></a>

17. **[RECORD](KEY.md#record) — Auditable Decision Record & Temporal Ordering.** WHAT: a durable, tamper-evident, single-source-of-truth trail authored *at the moment of decision* lets any output/decision be independently reconstructed (rationale, evidence, assurance argument with every sub-claim discharged and assumptions monitored); point-in-time records are preserved verbatim and corrected only by dated sibling-revision; and provable happens-before ordering enforces criterion-before-result and approval-before-action. FAILURE MODE: rationale that cannot be reconstructed at audit, an assurance argument with a hidden gap between evidence and conclusion, a success criterion retro-fitted after results are in, or an approval whose timestamp follows the action it "gated." EXAMPLE: an NYSE pre-trade approval is logged with a timestamp later than the order it supposedly gated (clock skew / async write) — trades cleared against a gate that did not yet exist.


---
*Obligation taxonomy — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
