<!-- engine-seed-panel wf_1ae3bf30-850; lens=evaluation; MODEL-SERVED (self-report): claude-fable-5 -->

MODEL-SERVED: claude-fable-5 (basis: my system prompt states "You are powered by the model named Fable 5. The exact model ID is claude-fable-5"; I have no introspective channel that could detect a silent mid-run downgrade, so per the project's model-provenance-honesty rule this is the requested-and-reported identity, and the run's own text should be judged against that caveat, not the label alone.)

# The Deductive Engine, from the Evaluation Lens — how anyone knows it is right

**Scope of this document.** The engine's judgment set, engine assignment, and EDB shape are settled law elsewhere (LEDGER-LOGIC-MARRIAGE §3–§4, as corrected by its Appendix A). This document designs the part the commission assigned to this lens: the evaluation harness — what ground truth is, what "metrics" mean under the N=1 discipline, how regressions are caught as rules evolve, how the engine's own failure modes are made loud, and the first three milestones. It is written so a competent builder can start, and it names its unknowns.

**The governing insight, stated once.** This project is unusually rich in ground truth and unusually hostile to statistics — and those two facts fit together. Fourteen-plus experiments produced not a distribution but a *specimen collection*: adjudicated defects, banked instrument outputs, ratified laws, and live write-time gate events, each tied to specific rows in an append-only record. The right evaluation harness is therefore not a benchmark with a score; it is a **per-obligation discharge record over that specimen collection** — the engine's evaluation should have exactly the shape the BRIEF demands of the records the engine audits (F4/F5: every obligation named, every status one of a closed honest vocabulary, nothing summed away). The evaluation harness self-applies the standard it serves. Anything less would be the auditor failing the audit — which this project has already done once (the F11 retraction) and learned from.

---

## 1. Ground truth: what the project has already banked, in three tiers

Ground truth here is not "what a human would say" — it is three concrete, already-paid-for asset classes, each with a different (and honestly different) evidentiary strength. The tiers must never be conflated in an acceptance claim; a milestone states which tier each of its checks rests on.

### Tier 1 — mechanically banked outputs (bar: bit-identical reproduction)

These are outputs of instruments that were themselves validated against independently-known facts, then retained with hashes:

- `experiments/fact-mining/docs/ledger-marriage/derivations/{s10,s11,s12,s13,nla}/` — DerivationRecords {engine+version, config, EDB/program/output hashes} from marriage increment 1. The SQL floor (`ledger_floor.py`) and clingo (`ledger_tnow.lp`) already agree bit-identically (output hashes equal) on all five targets.
- `epistemic-operator/instruments/sweep-results.txt` — the banked s1–s7 contemporaneity numbers; the banked s9–s14 instrument numbers referenced as the four-arm reproduction targets in marriage §5.
- The `soundness.lp` shown model (alias_surface/unsound_derivation/launder/inexpressible atoms on the s10 EDB), now id-keyed and twinned against `soundness.py` via `soundness_twin.py` as a standing close line.

Tier-1 truth is the strongest thing the project owns: a number someone already verified, pinned by hash, reproducible by re-running retained programs on retained EDBs. The engine's first duty is to reproduce all of it exactly. Any engine that cannot is wrong before any new capability is discussed.

### Tier 2 — adjudicated specimens (bar: expected finding-signature match)

These are defects and behaviors that a human (maintainer/consult chain) adjudicated against specific rows, several ratified as law:

- The five fixture families of marriage §5: rows 25/27 (e9, `gate_ok ∧ ¬sound_ok` — unsound derivation); the launder proof (auto-resolve rewrites 25/27→22, coherent and false — the standing *negative control* for any resolution rule); row 31→27 (e12/F42 derived-id miscite, with the kind-luck near-miss as its mutation); event 61 (F45 coincidental-basename unlock); the F44 aspectual triple (row 5-vs-29, e10 r28, e11 17→4).
- The e17 live specimens (consult 35): row 12 (the refused independence-inflation stub, `proxy_written(12)`); rows 17/18 (stamp-distinct genuine SoD, `self_performed(17,18)`, supersedes 17→12); the two distinct refused-insert events (row-15 id gap from the nonexistent-`enacts` typo at act 498; the review-detail refusal) — note consult 35 §0's erratum: the *corrected* mapping is the ground truth, and the eval fixture must encode the correction, not the trailer's original wrong mapping; the `unbound_row(2,3,5,6,7,8,14)` binder artifact (a labeled *instrument* defect — a fixture for the acts-join, not for the subject); `unledgered_span(463,464)` (the delegation event with no ledger representation — a labeled *coverage boundary*, not a derivable defect).
- The F-register (FINDINGS.md F1–F53) and the sha-anchored `acts.ruling` rows (F52/F53 filed as binding rulings). Each ratified finding that asserts a mechanically checkable property of a specific record is a label.

Tier-2 truth is adjudication — strong, but fallible, and the project has the receipts: F11 was retracted (the auditor's own RLS-view bug, not confabulation), F17's "use" claim was corrected to "entry proven, use falsified." **Therefore labels are ledger rows, not constants** (§2).

### Tier 3 — synthetic plants (bar: found/refused as designed; always labeled synthetic)

Where the organic record is censored — and the standing rule forbids arguing "no demand" from absence in our own runs — ground truth is manufactured: planted ledger defects in scratch lineages (the marriage §7 witness plan's synthetic stale-antecedent edit), labeled synthetic principals (the A.6 DTO acceptance precedent), mutation fixtures (every load-bearing clause's named red case), and same-second-neighbour id-vs-ts fixtures (A.3). Two disciplines bind Tier 3: **synthetics are labeled as synthetic in the record itself** (never launderable into organic evidence), and **probe-vocabulary independence** (F33's lesson): no plant may be phrased in vocabulary copied from a prior subject's emergent choices; every eval sweep includes at least one novel-name/novel-shape case, because every instrument defect in this project's history (F33, F49) was an instrument keyed to instance constants passing green on the instance it was written against.

### What is deliberately NOT ground truth

- **Statistics over runs.** N=1 per specimen; a reproduced fixture is a proof of mechanism, not a rate. The eval harness computes no accuracy percentage anywhere.
- **The subject's self-report** (F18/F22: narration asserts disciplines the witness refutes) and **any consumer's plausibility judgment** (the fair-trials deflation lesson: the correctness gate is set equality against an independent producer, never a model's opinion).
- **Absence in the lab record** as evidence of absent demand (BRIEF-authoritative rule). The BRIEF's register defines what judgment families the engine must eventually support; the eval harness tracks unexercised families as *declared exclusions with reasons* (conformance-map vocabulary), never as "not needed."
- **Judgment residue** (F20/F27 class): reference *truth* (does cited content match citing intent), use-as-claimed, MECE-of-meaning. No fixture will ever exist for these because no oracle does; the eval harness carries them as a permanent, enumerated out-of-scope declaration (I12), and any engine output that pretends to adjudicate them is itself an eval failure.

---

## 2. The oracle problem: expectations are an append-only, adjudicated ledger

The F11 story is the design-forcing specimen: the *operator* asserted "RLS is intact" from an incomplete check, accused the subject of confabulation, and was wrong. Ground truth in this project has already been wrong once and corrected non-destructively. So the evaluation corpus must have the same integrity shape as the record it validates:

**Build `eval/expectations/` as a ledger, not a config file.** One row per expected judgment: `{expectation_id, substrate (session/schema + as-of max id), judgment family, expected finding signature or output hash, tier (1/2/3), provenance (finding id / consult / acts.ruling sha / DerivationRecord hash), status}`. Corrections are quote-and-strike rows (`supersedes`), never in-place edits — exactly the F11-retraction discipline. When a finding is retracted or corrected upstream (as F11 and F17 were), the expectation row is superseded *with the correction's provenance*, and the eval harness re-keys automatically; an expectation whose provenance row has been superseded upstream and not re-keyed is itself a loud eval defect ("stale label" — the engine's staleness law applied to its own oracle).

Concretely: a small Python authority module (kb_ledger-style content-hash identity — `FindingIdentity` semantics, marriage §6.1) generating both the expectations table DDL and the parity test, per the established Python-authority/generated-DDL/live-parity discipline. Finding signatures are content-hashed on (substrate id, judgment family, participating row ids) so a persisting expectation is one stored row re-observed across eval runs, never re-injected.

---

## 3. Metrics under the N=1 discipline: the discharge table

The eval harness's output is a **discharge table** — deliberately the same shape as Rodin's proving perspective and the BRIEF's F4/F5, because I9 (discharge-status honesty) is the invariant this project exists to defend and its own evaluation must not violate it. Per expectation row, exactly one verdict from a closed vocabulary (extending the already-ratified differential vocabulary rather than minting a parallel one):

| Verdict | Meaning | Exit color |
|---|---|---|
| `REPRODUCED` | Tier-1: output hash bit-identical to the banked DerivationRecord | green |
| `DERIVED` | Tier-2/3: engine's finding-signature set contains the expected signature (set membership, mechanical) | green |
| `DIVERGE_BY_DESIGN` | differs from the banked expectation for a **pre-registered, named** reason (e.g., a defeater fires where the SQL floor is blind — the honest ASP verdict) | green, listed |
| `DIVERGE_DEFECT` | differs, no pre-registered reason | **red** |
| `QUARANTINED` | the check did not run (solver error/timeout/empty derivation over non-empty EDB/missing capability) | **red** |
| `EXCLUDED(reason)` | declared out of derivable scope, reason named (J-boundary, judgment residue, unbuilt fact family) | listed, never silent |
| `SUPERSEDED` | expectation retired by upstream retraction, replacement row named | listed |

Three rules give this table its teeth:

1. **No aggregate ever replaces the rows.** A summary line may count verdicts (F5-style), but every non-green row is named in the output; "47/50 green" without the three named reds is a forbidden output shape. A close cannot read as complete without every mandatory line's status (the `close_manifest` pattern, generalized to evaluation — this is the finding-36/finding-42 lesson: at e14, *none* of the three mandatory close lines ran and nothing flagged the non-run; at e17 a skipped arming step silently rendered a mandatory line N/A. The eval manifest makes "the check didn't run" structurally as loud as "the check failed").
2. **Mutation obligations, not mutation scores.** Per LOGIC-LAYER-ASP discipline and ADR-0011 ("a gate never seen red is a claim, not a net"): every load-bearing rule in every engine program carries a *named* mutation fixture that must flip a *named* verdict. The eval harness maintains a `rules × mutations` registry; a rule with no registered mutation is a red row in the discharge table (`UNCOVERED-RULE`), and honest exclusions (clauses whose mutation is genuinely untestable) are named as exclusions, not dressed up. This is a checklist that must be complete, not a kill-ratio to maximize.
3. **The differential is a standing producer-pair, and its independence is an audited property.** The SQL recursive-CTE floor and the ASP program are two genuinely independent encodings; set-equality of finding signatures on the defeater-free floor is the mechanical gate. When rules evolve, the *first* question is always "did both producers move, or one?" — a change that touches both sides in one commit weakens the differential and must say so. (Where feasible, floor changes and ASP changes land in separate commits with the differential green between them.)

**What replaces "accuracy" as the headline claim:** the coverage census (§6, M2) — an enumeration of the F-register and the BRIEF register into {mechanically derivable and derived; derivable given a named unbuilt fact family; permanently judgment-residue}. The engine's quality claim is "these N obligations discharge, these M are excluded for these named reasons," which is an I12 self-disclosure, not a score. That is the claim an NRC reviewer can act on.

---

## 4. Regression discipline as rules evolve

Rules will evolve — DTO edges will land as EDB facts, new judgment families (delegation rows, review-fixpoint, validity-bound expiry) will arrive, and encodings will be refactored. The discipline:

1. **Full-corpus re-run on every rule change.** The banked substrates are small (tens of rows each; nla = 55) and clingo grounds them in milliseconds — there is no cost argument for a partial sweep, and the project's instrument-defect history (F33, F49) is precisely a history of partial checking passing green. Every change to any `.lp` file, `ledger_floor.py`, `ledger_edb.py`, or an instrument re-runs *all* expectations on *all* substrates. Wire this as a pre-commit/CI gate on both repos' relevant paths.
2. **Pre-registered expected diffs.** A rule change that intends to change any verdict declares, before merge, exactly which expectation rows flip and why (a `DIVERGE_BY_DESIGN` registration keyed to the change). Any *unregistered* flip is `DIVERGE_DEFECT`, red, blocking. This inverts the burden the same way the frontier creed does: the corpus is presumed right; the change must justify each departure.
3. **Program-hash pinning via the existing DerivationRecord.** A.4 already banks {program hash, EDB hash, output hash} per run. The regression layer adds: the expectations ledger records which program hash last discharged each row, so "what changed since this last passed" is always answerable from the record, and a verdict is never compared across un-noted program changes.
4. **The mutation ratchet.** Every new rule ships with its red case *in the same change* (the ADR-0000 Rule 2(b) posture: the net arrives with the type). The `rules × mutations` registry is append-only; deleting a mutation requires a quote-and-strike row naming why the clause it covered no longer exists.
5. **Novel-substrate obligation.** Each regression sweep includes at least one substrate the encodings were *not* developed against (rotating: a fresh scratch lineage, a synthetic schema-variant). This is F33's probe-vocabulary-independence lesson mechanized: an eval suite whose fixtures all share the engine's birth vocabulary measures the engine against itself.
6. **Closure statements on eval-found defects.** When the eval harness catches an engine defect, the fix is governed by ADR-0000 Rule 2(a) as amended: the class is named with a closure statement (invariant, quantification universe with axes and siblings enumerated, denomination check), the class is presumed too narrow as first named, and the fixture that caught it plus the fixture for the *adjacent sibling axis* both enter the corpus. (Worked precedent: A.8's empty-model hazard — the fix quarantined the marriage consumer, but the closure statement's universe includes every `clingo_run` consumer; see §5 and §8.)

---

## 5. The engine's own failure modes, made loud — each with its mechanism AND its negative control

The commission names four; the project's history supplies a fifth. For each: the mechanism, and — because a gate never seen red is a claim — the standing negative control that proves the mechanism fires. Negative controls run in every full sweep, not once at build time.

### 5.1 Silent vacuous pass on wrong/empty substrate (the F49 class — the project's own most-repeated instrument defect)

- **Mechanism (largely built; the engine inherits it):** capability-manifest EDB export with declared exclusions and loud refusal of absent capabilities (A.2); `ledger_target` SSOT substrate resolution with UNREGISTERED → REQUIRED-ABSENT (finding-36 gate); empty-derivation-over-non-empty-EDB → QUARANTINED (A.8).
- **Engine-specific addition — the pilot-light atom.** Every engine program includes one judgment that is *always derivable on any well-formed non-empty EDB* (e.g., `edb_witness(MaxId)` derived from the highest entry id, echoed into the output). A derivation output lacking its pilot light is QUARANTINED regardless of what else it says. This closes the residual gap A.8 left: a grounding error that produces a *partially* empty model (some atoms, wrong atoms) rather than a fully empty one.
- **Negative controls:** (a) feed an empty EDB against a substrate manifest claiming rows — must go REQUIRED-ABSENT; (b) feed a deliberately broken program (undefined predicate) — must QUARANTINE, never bank `[]`; (c) the e14 reproduction: point the harness at a substrate whose registration is missing — must refuse to arm (finding-42 gate).

### 5.2 Stale inputs (F42/F46, applied to the engine itself)

The law the record taught — *citation currency must be record-observed at the moment of citation; memory-grounded correctness fails closed only by luck* — binds the engine as a consumer too. An engine verdict is a citation of the record.

- **Mechanism:** every EDB export is stamped `as_of = max(id)` per substrate (plus the export's own timestamp and source hash, already in the DerivationRecord). Every verdict the engine emits carries its `as_of`. Any *live* consumer (hook rung, review queue) compares verdict-`as_of` against current `max(id)` at presentation time: behind ⇒ the verdict is presented as `STALE(as_of=N, now=M)`, never as current. Staleness is a display-honesty property, not an error — a stale verdict about ids ≤ N remains true *about the record as of N* (T_event is monotone); what is forbidden is wearing it as a statement about now (that would be the engine reading its own T_event output as T_now — the e9 gate's exact sin, one level up).
- **Negative control:** in a scratch session, derive; append one row; assert the presentation layer marks the prior verdict STALE. Plus the same-second-neighbour fixture proving all precedence keys on id, never ts (A.3, already built — adopt into the corpus).

### 5.3 Solver timeouts and non-runs

- **Mechanism:** per-judgment-family time budgets (retrospective/close mode: generous, but finite and configured, never infinite); a timeout or crash is QUARANTINED — a first-class red verdict occupying the row, never a dropped row. In live/hook mode the shell discipline is degrade-not-block: the hook never stalls the subject, but the non-run is written into the eval/close manifest as QUARANTINED so the *record* shows the engine didn't run even though the *subject* wasn't blocked. Budgets are set from measured grounding/solve times on the banked substrates (an M1 measurement output), with headroom stated, not guessed (no bare round literals — ADR-0000 specimen 3's denomination lesson: the budget is denominated in observed solve time on the largest banked substrate, and re-derived when substrates grow).
- **Negative control:** a fixture program with a deliberate combinatorial blowup under a 1-second budget — must QUARANTINE within budget + grace, and the manifest must go red.

### 5.4 Self-unsoundness: the engine reading T_event as T_now, or laundering

- **Mechanism:** the two-theory split is enforced in the engine's *output vocabulary*: atoms are namespaced `history_*` (monotone, derivable from T_event alone) vs `now_*` (closure over defeaters), and the differential checks them against different floors. No engine output ever *rewrites* a pointer (F28 flag-never-auto-resolve): the engine derives flags, never resolutions.
- **Negative control (already paid for):** the launder fixture — run the banked auto-resolve-shaped mutation of the resolution rules; it must flip `launder/3` atoms into existence, and any engine version in which the launder mutation *fails to flip* is broken. The e9 rows-25/27 fixture is the positive twin.

### 5.5 The instrument-defect class the history actually produced: green-on-the-wrong-question

F33 (governed set keyed to an instance name — probes drawn from the same vocabulary passed green), F49 (instruments keyed to a prior arm's env constants — silently didn't run), the e17 arming gap (a manual checklist line silently N/A). The common shape: **the check ran against the checker's own assumptions, not the world.** Mechanisms already adopted (SSOT substrate resolution, capability probing, close manifest) cover the known instances; the eval harness's standing defense against the *unknown next instance* is §4.5's novel-substrate obligation plus one structural rule: **every mandatory eval line is registered in a manifest that is itself checked for completeness against the expectations ledger** — a judgment family with expectations but no manifest line is a red at arm time, the finding-42 gate generalized.

---

## 6. The first three evaluation milestones

Each milestone is a discharge table with named rows; acceptance is "every row green or named-and-justified," never a fraction.

### M1 — The reproduction gate (retrospective; the engine earns the right to exist)

**Substrates:** s10–s13, nla (the five banked targets), plus the e17 record.
**Obligations:**
1. Every Tier-1 DerivationRecord reproduces bit-identically (output-hash equality) under the current engine.
2. All five §5 fixture families derive their expected signatures; every registered mutation flips its named verdict (launder, kind-luck near-miss, same-second-neighbour included).
3. The SQL-floor/ASP differential is AGREE on the defeater-free floor for every substrate; every divergence is a registered DIVERGE_BY_DESIGN.
4. All §5.x negative controls fire red as designed (empty EDB, broken program, unregistered substrate, timeout fixture, staleness fixture).
5. Measured outputs banked: grounding/solve time per substrate per program (the denomination source for §5.3 budgets).

**Exit:** a committed discharge table + DerivationRecords for the eval run itself (the eval harness's own runs are I8/I11-conformant: retained EDBs, programs, outputs, hashes — evaluation evidence is evidence).

### M2 — The derivability census (the honest scope claim; the milestone that answers "what is this engine, exactly")

Take the ratified corpus — FINDINGS F1–F53, the conformance map's register rows, and consult 35's synthesis list of live-derivable candidates (independence class: retired-as-derived at e17; partial-stub refusal; delegation events; review-fixpoint) — and classify *every* entry:

- **(a) Mechanically re-derivable now:** express it as an expectation row; run the engine blind on the raw record (the engine is never shown FINDINGS.md); the expected signature must appear in the derived set. Candidates from the record: unsound-derivation (F28), the F42 miscite, F45's coincidental unlock, stale-enactment debt, question-status/answers round-trips, the e17 stamp/SoD facts (`proxy_written`, `self_performed`, stamp-distinctness), refused-insert visibility (id-gap accounting), amends-accumulation, read/observed-currency verdicts.
- **(b) Derivable given a named unbuilt fact family:** e.g., delegation-event judgments need the delegation row kind; binder one-act-many-rows needs the acts-join fix. Filed as EXCLUDED(unbuilt: <family>) with the build named — the census *is* the engine's honest backlog.
- **(c) Judgment residue:** F20-class, J-boundary items — permanently EXCLUDED(no-oracle), enumerated.

**Two disciplines:** the classification of each finding is itself adjudicated (maintainer ratifies the census — it is a scope ruling, not an engineering convenience); and the blind is real (the engine's inputs are the ledger+acts EDB and rulings-as-facts, never the findings prose; an engine that ingests its own answer key measures nothing).

**Exit:** the census document + the (a)-set green in the discharge table. This census is the engine's I12 self-disclosure and the honest sentence for the NRC bar: "of 53 ratified findings, these are machine-derived from the record alone, these await named fact families, these are permanently human." *How many land in (a) is a genuine unknown* — my read of the record suggests a substantial majority of the mechanical-trigger findings, but the census exists precisely because that is currently an impression, not a fact.

### M3 — The live shadow (the engine during a run, proven against the kernel's own gates)

Run the engine contemporaneously (the hook rungs L1′/L2′ of marriage §7) in *shadow* — deriving, journaling, gating nothing — alongside e18 (or the next live experiment the maintainer schedules; the review-fixpoint lever already armed for e18 is a natural fit since `review_fixpoint` is an engine-shaped judgment).

**Obligations:**
1. **Kernel-agreement:** every write-time gate event the kernel fires (refusals, stamp verdicts) is independently re-derived by the engine from ledger+acts within its budget — per-event AGREE/DIVERGE, any DIVERGE a red to adjudicate. (The kernel's HMAC-stamped trigger layer and the engine are two producers of the independence judgment; e17 proved the kernel live, M3 proves the engine matches it. Note the asymmetry honestly: the kernel sees the secret, the engine sees only the recorded stamps — the engine re-derives the *verdict*, not the HMAC verification itself; that residual trust is a declared exclusion.)
2. **Planted-defect find:** at least one Tier-3 plant in a scratch session (a stale-antecedent edit; a synthetic independence inflation under labeled synthetic principals) surfaced by the shadow engine within budget, with the finding durably stored under FindingIdentity and *not* re-injected on the next tick (idempotency — re-running on an unchanged record inserts zero rows).
3. **Loudness under sabotage:** during the shadow run, deliberately (i) kill the solver mid-derivation, (ii) feed a stale EDB, (iii) unregister a capability — each must surface as QUARANTINED/STALE in the run's manifest, none may surface as a green or a silence.
4. **Budget conformance:** end-to-end shadow latency measured and banked against the hook's degrade-not-block budget.

**Exit:** the shadow run's whole-session evidence persisted per the ephemera discipline; a maintainer ruling on whether kernel-agreement holds well enough to schedule the first *consulted* (still non-gating) live use. Enforcement stays with the write-boundary triggers indefinitely — the engine derives and flags; F26/F28 law means the engine layer never becomes a deny surface in this design, and M3's acceptance explicitly does not include gating.

---

## 7. Unknowns, stated, with the experiment that answers each

1. **How much of the F-register is mechanically derivable** — answered by M2's census; do not pre-commit a number.
2. **Whether ASP grounding stays inside live-hook budgets as records grow** (55 rows is trivial; a long-running deployment ledger is not; grounding is polynomial in edges but the constant matters) — answered by M1's measurements plus a synthetic large-ledger fixture (generate a 10^4-row scratch lineage; measure; set the budget denomination from data). If it doesn't fit, the fallback is architectural and known in advance: cursor-incremental derivation (the hook discipline already names it) — evaluate *that* against full-rederivation equality as its own differential.
3. **FindingIdentity stability across rule refactors** — a renamed atom or re-factored rule must not orphan durable findings. Answer: the identity hashes on (substrate, family, row ids), never on atom names; prove it with a refactor fixture in M1 (rename an atom, re-run, assert zero new finding rows).
4. **The solver-file safety-flag hazard** (marriage §10): environmental, not engineerable-away; the eval harness keeps engine inputs ids-not-text and pre-registers the hazard as an operational assumption. If a degradation event lands mid-eval, the model-provenance line in the eval's DerivationRecord is what keeps the run honest.
5. **Whether kernel-agreement (M3.1) can be exact** given the engine's stamp-trust exclusion — possibly some gate events are kernel-derivable only. The census pattern applies: enumerate them as declared exclusions rather than softening the agreement bar.

## 8. A hazard within reach, flagged loudly (not this design's to defer again)

A.8 found that the shared `clingo_run` returns `[]` on a grounding error (clingo emits valid JSON with an empty model), and the durable fix — an UNKNOWN/error raise at the `clingo_run` level — was *filed for a future touch* to avoid cross-consumer blast radius, with the marriage consumer locally quarantined. The evaluation harness is that future touch: M1 makes every `clingo_run` consumer's output an evaluated artifact, and an eval layer built on a runner that silently converts grounding errors into empty models is building the F49 class into its own foundation. The M1 build therefore includes the `clingo_run` fix (raise on grounding error / non-SAT-non-UNSAT outcomes), with the blast radius handled the honest way: run the full-corpus sweep across *all* its consumers (`contra_asp`, the marriage lanes, `core_a`'s sweep script) before and after, with every verdict change pre-registered. The plank has a nail in it; M1 walks across the plank.

---

*Record basis for this document: LEDGER-LOGIC-MARRIAGE.md (body + Appendix A) in full; safety-critical-logging-standards/BRIEF.md in full; BRIEF-CONFORMANCE-MAP.md in full; instruments/core_a.lp and soundness.lp in full; FINDINGS.md in full (both pages); consults/e17-analysis-consult-35.md in full; ADR-0000 in full (incl. the 2026-07-02 closure-statement amendment) and ADR-0012 (P1–P9 and the checklist; file read to its C++-guidance section); directory listings of epistemic-operator/instruments/, fact-mining/, and docs/ledger-marriage/derivations/. Not read: instruments/*.lp beyond the two named (flag-hazard posture), tainted/, the e15/e16 consults. No database touched; no repo file modified.*