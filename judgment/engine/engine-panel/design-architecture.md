<!-- engine-seed-panel wf_1ae3bf30-850; lens=architecture; MODEL-SERVED (self-report): claude-fable-5 -->

MODEL-SERVED: claude-fable-5

# The Deductive Engine — computational architecture, enforcement tiers, latency, and the verification discipline that survives compilation

**Lens:** architecture / latency / enforcement tiers. **Provenance:** designed against the primary sources read in full this invocation: `LEDGER-LOGIC-MARRIAGE.md` (body + Appendix A), the safety-critical-logging BRIEF (I1–I12, G/F register), `BRIEF-CONFORMANCE-MAP.md`, `instruments/core_a.lp`, `instruments/soundness.lp`, FINDINGS.md (F1–F53, incl. the F52/F53 ratifications), `consults/e17-analysis-consult-35.md`, ADR-0000 and ADR-0012 (in full through P9), plus code spot-checks of the built increment: `ledger_tnow.lp`, `ledger_floor.py`, `ledger_differential.py`, `clingo_run.py`, and the live write-time tier `harness/e17-build/s17-stamp-mechanism.sql` / `s17-independence-vocabulary.sql`. Not read: `e16-analysis-consult-31.md`, `never-again-synthesis.md` (optional), operator `.lp` files beyond the two named (flag-hazard posture), live psql. No file modified.

---

## 0. The thesis from this lens

The project already runs a deductive engine — it just runs it in three places that do not yet know they are one machine: plpgsql triggers at write time (e17, live), a hook design at turn boundaries (L1′/L2′, designed), and the solver+floor differential at close (marriage increment 1, built). The engine design job is therefore not "build a deducer"; it is to **type the tier ladder, prove which judgments may run at which rung, and extend the two-producer differential vertically so that a judgment compiled downward never escapes re-derivation.** The load-bearing fact that makes this tractable is structural, and the record already owns it: **append-only + strictly-backward edges make a large class of judgments prefix-determined**, and prefix-determined judgments compile to write time *losslessly* — their live verdict and their close verdict are the same mathematical function, so any divergence between tiers is a defect by construction, never a judgment call.

## 1. The tier ladder, typed

Three tiers, each with a fixed authority relationship. Names chosen to be usable in close-manifest lines.

**T0 — write-time (in-transaction).** Postgres BEFORE INSERT triggers on the kernel lineage; SECURITY DEFINER HMAC verification; refuse-and-teach with frozen teach text. This is the **only deny surface** the engine will ever have (the marriage §8 restraint, F28: everything else is flag-and-journal). Its computational envelope: the NEW row plus O(log n) indexed lookups into the prefix; no unbounded recursion in the trigger body (closures arrive via the maintained caches of §4, never computed by walking chains inside a transaction).

**T1 — live-turn (hook process, out-of-transaction).** A Python process on the Stop/PreToolUse path running the instrument payload contemporaneously: soundness closure, question status, observed-currency/read-currency warnings, stale-enactment debt, assumption expiry. **Never denies.** Time-budgeted, degrade-not-block, cursor-incremental, findings deduplicated by `FindingIdentity` (marriage §6.1 — the precondition for a live queue that does not re-nag). A T1 non-run is a loud QUARANTINED marker banked in the record, never a silent skip (the F49/A.8 lesson: an empty result over a non-empty record is quarantined, not clean).

**T2 — close-time (the court of record).** Full recomputation by two independent producers (SQL recursive CTE floor + clingo over the exported EDB), bit-identical differential, DerivationRecords, retention. Plus the D-class work only a solver does: k-parameterized SoD phase structure, `#minimize` minimal repair, z3 unsat-core explanations.

**The authority rule (one sentence):** every judgment has exactly one authoritative tier — T2 — and lower-tier instances are *shadows*: projections whose every verdict is re-derived and reconciled at close. A shadow that cannot be reconciled (because its inputs were not retained) is not permitted to exist — this forces the refusal journal of §6.

The BRIEF grounds the ladder: T0 mechanizes I3/I2/I6-class integrity at the strongest surface (the F15 lesson: append-only held because of the MAC, not the prompt; e17: the write-time refusal out-performed every prose prime); T1 is the ALCOA "Contemporaneous" arm — information delivered while the subject can still act on it; T2 is I9/I11 — discharge-status honesty and re-runnable evidence.

## 2. The judgment classification — the theorem that decides tier placement

Two independent dimensions decide where a judgment may run: **complexity class** (what the judgment mathematically depends on) and **EDB availability** (whether its facts exist at that tier's moment). Both are checkable properties of the rule text, not vibes.

### 2.1 Complexity classes

**Class A — prefix-determined (per-row, decided forever at insert).** The judgment of row E is a function of the record prefix `{id ≤ E}` alone. Because ids are the total order (the ratified id-is-order law, strict `<`), edges validate backward, and the store is append-only, no later row can change the verdict. Membership is syntactic: every body literal is bounded by ids `< E` (or is the NEW row itself). Members today: `gate_ok`, `sound_ok`, `unsound_derivation`, `launder`, `alias_surface`, the `amends` quotation check, `answers`-target validation, id-precedence, HMAC stamp verification, and **the F53 stamp-distinctness gate** (a function of NEW plus the `regards`-target's stamp, both ≤ E). Consequences: computable exactly once; cacheable forever; and — the compilation guarantee — a T0 trigger computing a class-A judgment computes the *identical function* the T2 solver recomputes, so the tier differential admits **no DIVERGE_BY_DESIGN cell for class A**. Any A-class tier divergence is DIVERGE_DEFECT, mechanically.

**Class B — frontier-monotone (once true, true forever).** Becomes true when a later row lands, never retracts: `superseded(Y)`, `defeated(D)`, transitive `sup_star`. Syntactic criterion: derivable without default negation over facts that can still arrive. These are the incrementally-maintainable cache candidates (§4) — append-only caches for append-only truths, no invalidation logic ever needed.

**Class C — frontier-non-monotone.** Flips as the record grows: `in_force`, `head`, `stale_enactment_row` (debt appears when the antecedent is defeated, disappears when the enactment itself is superseded), `review_gap`, countersigned-in-force, question-answered where answered-ness keys on an in-force answer. Subclass **C_t — time-indexed**: I7 assumption expiry depends on `(record, now)`, not the record alone; every C_t derivation must pin its evaluation instant in its DerivationRecord or it is not reproducible (an addition to the A.4 discipline: `T_now` derivations carry `now` as a recorded input). Class C is **never compiled to refusal** — a deny keyed on a judgment that can moot later would refuse honest writes; C-class output is T1 flags and T2 lines only.

**Class D — global/combinatorial.** Choice + optimization over principals and obligation sets: core_a's k-phase table, minimal-repair blame, unsat cores, DTO faithfulness/MECE machinery. T2/on-demand only. No incremental story is attempted, and honestly none is needed: D-class state spaces are over principals and obligations (cardinal numbers in single digits), not over rows.

### 2.2 EDB availability

A judgment can run at a tier only if its facts exist at that tier's moment. Ledger rows and interception stamps are **live** (the PreToolUse hook mints stamps at write time). The **acts stream is retrospective today** — parsed from vendor transcripts at close — so any judgment joining ledger against acts (the F52 license-reading law; claims-vs-acts honesty differentials; `unledgered_span`) is close-time-bound *regardless of its complexity class*. This is a designable constraint, not a law of nature: the same interception surface that stamps ledger writes can journal every tool call contemporaneously into an apparatus-owned `acts_live` table, promoting acts-joined judgments to T1. That increment (§10, item 8) must be scoped inside the standing threat model — the harness distrusts ledger-vs-acts, not the subject as a sandbox adversary; live acts journaling is a *fidelity* mechanism (contemporaneity for the acts substrate, I1 applied to the apparatus's own evidence), and its parse is differentialed against the close-time transcript parse before anything consumes it.

## 3. What runs where — the component map

All of it Postgres + Python + clingo, all self-hosted, nothing new to buy.

**In Postgres (kernel schema, apparatus-owned):**
- T0 triggers (existing s17 pattern) for promoted class-A judgments.
- The **monotone caches** (§4) in an engine-owned schema (`engine_cache` or per-lineage), populated by AFTER INSERT triggers: `sup_star` closure rows, `superseded` marks, per-citation class-A verdicts. No subject grants — invisible to the subject role (no passive prime; the e12 lesson).
- The **refusal journal** (§6): append-only capture of every T0 refusal with the attempted payload, verdict, frozen teach text, stamp identity, and wall ts.
- `pg_stat_statements` (free, in-core contrib) for the T0 latency evidence (§5).

**In the hook process (Python, per-invocation, no daemon yet):**
- Watermark-cursored incremental evaluator: reads rows above the last cursor, updates its view from the caches, evaluates C-class flags, writes findings keyed by `FindingIdentity` with a frontier watermark on each finding.
- Budget enforcement: a hard deadline; on breach it banks a QUARANTINED non-run marker and exits cleanly (degrade-not-block). It never blocks a turn on solver availability.
- clingo is *not* on the T1 hot path initially. The A/B-class heavy lifting is SQL-side; C-class evaluation over cached B-facts is joins and complements. The L3′ engine-interrogation rung invokes clingo under the remaining budget and quarantines on timeout — clingo participates live only when the budget demonstrably accommodates it (§5 decides that with measurements, not hope).
- A resident daemon (LISTEN/NOTIFY-driven) is the designated evolution *if and only if* the latency ledger shows per-invocation startup (psycopg connect, interpreter start) dominating the budget. Until measured, per-invocation processes — a standing service nobody's first request pays for is also a standing service to operate and audit.

**In the solver layer (T2, as built, extended):**
- `ledger_floor.py` / `ledger_tnow.lp` / `ledger_differential.py` unchanged in role; the differential grows the vertical lines of §7.
- z3 lanes (quantities, unsat cores) close-time.
- core_a as a standing D-class instrument, fixture-pinned phase table.

**The one new authority (ADR-0012 P1 applied to the engine itself):** a **judgment registry** module — the typed, single home declaring, per judgment: id, rule citation (F-number / acts.ruling), complexity class (A/B/C/C_t/D) with the syntactic justification, EDB availability, tier placements (authoritative + shadows), fixture set, mutation set, promotion stage (§6), and teach text where compiled. Everything else — which close lines exist, which triggers may be armed, what the differential must reconcile — derives from this registry or is parity-pinned against it. Today the tier assignments live in prose across consults; that is cancer G (load-bearing knowledge in unenforceable convention) waiting to happen at exactly the moment the engine grows past one maintainer's working memory.

## 4. Incremental vs full recomputation

The split falls directly out of §2:

- **Class A:** computed once, at insert (T0 trigger or AFTER-trigger cache write). Never recomputed on the live path. T2 recomputes all of them from scratch at close — not for freshness (they cannot have changed) but as the shadow check.
- **Class B:** append-only cache maintenance. When `supersedes(X,Y)` lands, insert `sup_star(X,Y)` plus `sup_star(X,Z)` for each cached `sup_star(Y,Z)` — bounded by chain length, which the record shows is short (chains of 1–3), and every insert is monotone: no retraction logic exists because none is possible.
- **Class C:** evaluated at query time (T1 invocation) from B-caches: `in_force` = entries minus `superseded`; `stale_enactment_row` = in-force enacts-edges joined against `defeated` — set complements and joins over indexed caches, cheap at any plausible session size.
- **Class D:** full solver runs only.

**Squaring the caches with the T_now-never-stored law.** The two-theory split's law is that "currently valid" is derived, never stored, because a *stored* validity is a consumer trap (the e9 gate read T_event as T_now). The caches here do not violate the law's substance, and the design says why explicitly rather than hoping: (i) every cached fact is either class A (a historical fact about a prefix — as much T_event as the rows themselves) or class B (monotone — its stored form can never be stale in the dangerous direction); no class-C "currently valid" fact is ever materialized; (ii) the caches live in an apparatus schema with no subject-role grants and no consumer contract — nothing but the engine reads them; (iii) **cache_integrity** is a mandatory close line: rebuild every cache from scratch from the raw record and diff bit-identically against the maintained copy. A maintained cache that cannot survive rebuild-and-diff is a defect, red, non-skippable. The caches are memoization with a standing audit, not a second truth.

## 5. Latency budgets — established honestly, or not at all

This document deliberately asserts **no latency numbers**. Inventing budgets a priori is exactly the unsubstantiated-empirical-claim pattern the standing rules ban, and the round-literal hazard ADR-0000's denomination check names. Instead: the currencies, the measurement protocol, and the enforcement shape.

**Three budget currencies, each denominated in the resource that actually detonates:**
- **T0:** added milliseconds on the *subject's* INSERT path (the apparatus intruding on the collaboration). The detonation mode is not "slow" — it is that a slow trigger degrades into de facto denial-by-friction, and F26/F29 teach precisely what friction does: the subject thins the record until it fits the pipe. A T0 budget breach is therefore a *record-integrity* hazard, not a performance nicety.
- **T1:** seconds of turn-boundary stall (the subject waits for the hook).
- **T2:** close wall time (operator-facing; generous; the only enforcement is that a non-run is QUARANTINED red).

**The protocol:**
1. **Arm-time microbenchmark**, per experiment arming: N inserts into a scratch lineage on the real path (guest → 192.168.122.1) against the *armed* kernel and against the *bare* kernel; bank percentiles (p50/p95/p99) as a **LatencyRecord** {host, path, kernel config hash, N, percentiles, wall ts} — the DerivationRecord idiom applied to time. The armed-minus-bare delta is the trigger cost, measured where it is paid.
2. **First maintainer ruling sets each budget** from the first banked measurement (a ratified multiple of the measured baseline). Budgets are thereafter ratcheted from observed percentiles — never guessed, never a bare round literal.
3. **Arming check:** an arm whose microbench exceeds budget fails the arming, loudly — the exact shape of the existing `gate-journal-registered` arm-time check (finding 42), extended to time.
4. **In-production evidence:** `pg_stat_statements` on the harness DB gives per-statement timing including trigger overhead folded into INSERTs; a **latency_budget** close line compares the session's INSERT timing distribution against the armed baseline and flags drift. Per-row trigger self-timing inside plpgsql is deliberately not attempted (it perturbs what it measures and stock Postgres gives the statement-level view free).
5. **T1 deadline semantics:** the hook's deadline is enforced by the hook itself (watchdog around the payload); breach → banked QUARANTINED marker → close line goes red on a *pattern* of non-runs (a single timeout is a datum; a run whose hooks mostly didn't fire is an audit hole and must look like one).

All latency work is **apparatus qualification, not statistics** — the N=1 discipline applies: a LatencyRecord qualifies a configuration; it is never a performance claim about the future.

## 6. The promotion pipeline — how a solver judgment becomes a trigger, and what survives

e17 is the worked instance (finding 31 → F53 ratification → s17 trigger → live refuse-and-teach → honest convergence). The pipeline generalizes it into stages with checkable gates. A judgment's promotion stage lives in the registry (§3).

- **P0 — observed.** An instrument (retrospective) surfaces the dishonesty class; the specimen is banked as a fixture with its mutation (the §5 marriage discipline: a gate never seen red is a claim).
- **P1 — ratified.** Maintainer files the law (acts.ruling, F-number). No promotion without ratified semantics — the trigger will speak frozen teach text in the apparatus's voice; that text asserts law, so law must exist.
- **P2 — derived.** Both T2 producers compute it; differential AGREE on all banked targets; every load-bearing clause has a mutation that flips a verdict.
- **P3 — live-flagged.** The judgment runs at T1 as flag-and-teach through at least one organic exercise. This stage exists to observe the **F26 corruption test** before any cost attaches: *what does the judgment key on?* The e9/e17 contrast is the criterion, and it is the sharpest design rule in this document: **a promoted gate may key on a self-declared value only where it verifies the claim against an invariant witness the writer does not control — making the claim true-or-refused — never where it merely prices the label.** e9's enactment rule priced a label and the label migrated (`concern='process'`, escape economics); e17's independence gate verified the label against the HMAC stamp and the subject made the claim *true*. Verified-claim shape converts; priced-label shape corrupts. Class-A-ness is necessary for promotion; verified-claim shape is what makes promotion *safe for the record as a measurement*.
- **P4 — compiled.** Eligibility checklist, every item mechanical: (i) class A (or class B consumed via monotone cache) — C/C_t/D are constitutionally ineligible for refusal; (ii) EDB live at write time; (iii) verified-claim shape (the P3 test passed); (iv) frozen teach text naming the honest alternative — refuse-and-teach requires a teachable exit, and e17's synthesis is explicit that the *teaching at the moment of violation* is what converts ceremony into honesty; a refusal without a taught exit is just friction, and friction thins records (F29); (v) the trigger seen red on the banked fixture *before* arming (fixture replay against the armed scratch kernel is an arming check); (vi) **refusal journaling armed with it** — see below; (vii) transaction boundary declared: e17's partial-stub seam (a review row landing while its detail was refused, per-statement autocommit) is the standing specimen that a compiled judgment's atomicity envelope is part of its semantics, stated, not assumed.
- **P5 — shadowed, permanently.** The close recomputes the promoted judgment over the full record and reconciles against what the trigger actually did. Both directions: every row the semantics says should have been refused must appear in the refusal journal or be a divergence; every journaled refusal must be one the semantics reproduces. The refused rows are *not in the ledger* (they were refused), which is exactly why item (vi) is non-negotiable: **the refusal journal stores the attempted payload** (NEW row content, stamp identity, verdict, teach text, ts), making the shadow two-sided and making the apparatus's own denials first-class I4 negatives rather than id-gap inferences (e17's id-gap visibility was luck-adjacent; the journal makes it construction). The journal is append-only, apparatus-owned, and its integrity rides the existing `append_only_integrity` close line.

**What survives compilation, precisely:**
- **Survives:** the judgment *function* on the write prefix — bit-identically checkable forever, because class A admits no by-design divergence. This is the strongest guarantee in the system and it is free: it follows from the record's own structural laws (append-only, backward edges, id-is-order).
- **Does not survive, mitigated:** encoding singularity. The plpgsql trigger is today a *hand-written second author* of a judgment the `.lp` and the SQL floor also author — ADR-0012 P7's two-writers-of-one-truth, across the hardest boundary to audit. The design names the target state per P7's hierarchy: **one authority module generating all three encodings** (the `.lp` fragment, the floor CTE fragment, the plpgsql body) for promoted judgments — generate-from-one-source over the current floor of differential-plus-mutations-as-backstop. Increment 7 is a codegen spike on exactly one judgment to decide adopt/abandon on evidence. Until then, honest status: the P5 shadow *is* the standing net, and each hand encoding carries its own mutation set.
- **Does not survive, by design:** explanations. The trigger yields the frozen teach text; minimal-repair blame, unsat cores, and any "which obligations jointly conflict" narrative remain T2 goods. A subject that wants the full derivation reads the close artifacts; the write-time surface stays thin on purpose (ids-not-text, flag-hazard posture, and the smaller the trigger the smaller its audit surface).

## 7. The independent-verification discipline, extended vertically

Today's differential is horizontal: two producers, one tier, set-equality, closed verdict vocabulary {AGREE, DIVERGE_BY_DESIGN, DIVERGE_DEFECT, QUARANTINED}, quarantine-turns-red. The engine keeps that vocabulary — closed vocabularies should not multiply — and adds **tier-pair lines**:

- **T2-internal (exists):** SQL floor ↔ ASP, bit-identical on the defeater-free floor. Unchanged. One honesty note carried forward: the two producers share the target-resolution SSOT (`ledger_edb.resolve`) deliberately — one home for *which relation* — while the fact semantics are independent; a fact-extraction bug in the EDB export is itself caught by the floor reading the ledger directly. The shared/independent boundary is declared, not blurred.
- **tier_consistency (T0 ↔ T2), new, per promoted judgment:** the P5 shadow. Verdict rule: class A ⇒ any divergence is DIVERGE_DEFECT (no by-design cell exists); a missing refusal-journal entry or an unreconcilable refusal is QUARANTINED. Red, non-skippable, from the day a trigger arms.
- **hook_fidelity (T1 ↔ T2), new, per finding:** every T1 finding carries the frontier watermark W at which it fired. At close, T2 re-derives the finding **over the prefix ≤ W** (the EDB export grows a watermark parameter — cheap, id-cursored). Class-A findings must also hold at close; class-B/C findings may have legitimately mooted as the record grew — verdict DIVERGE_BY_DESIGN **with the mooting edge named** (the naming is what keeps by-design from becoming a landfill; an unnamed moot is DEFECT). A T1 finding T2 cannot reproduce even at its own watermark is DIVERGE_DEFECT — the hook's encoding is wrong, and it was teaching the subject falsehoods live, which is worse than silence and must surface as red.
- **cache_integrity, new:** §4's rebuild-and-diff of every maintained cache. Bit-identical or red.
- **acts_parity (conditional, with increment 8):** live-journaled acts ↔ close-time transcript parse, differentialed before any judgment consumes the live stream.

The producers stay genuinely independent where independence is the point (no shared closure code between floor and ASP; the trigger — until codegen — is a third independent encoding, and the shadow exploits that: three encodings agreeing is stronger evidence than two). Where sharing is deliberate (target resolution, the id-is-order law itself), it is declared as shared law, not laundered as independence.

## 8. clingo grounding and scale

Current records are tens of rows; grounding is trivially fast and it would be dishonest to claim a scaling problem exists today. The design's obligation is to make growth *measured* and the response *pre-registered*, so scale never arrives as a surprise:

1. **Program hygiene rule (immediate, one worked retrofit):** every rule variable ranging over entries must be domain-restricted to a consumer-relevant generator. The one offender in the built program is the `defeated_asof(D,E)` idiom (both `soundness.lp` and `ledger_tnow.lp`): `E` ranges over *all* entries, grounding O(|defeated| × n) instances, though `E` is only ever consumed at citing rows. Restrict via `cites(E) :- enacts(E,_).` (∪ amends/answers sources) and key the rule on `cites(E)` — grounding drops from row-quadratic to edge-linear. On banked records the shown models are unchanged (the restriction removes only never-consumed atoms); the differential and fixture replay prove that, byte-identically, before the retrofit is trusted — the id-keying retrofit in `soundness.lp` is the worked precedent for exactly this kind of semantics-preserving re-encoding under a standing net.
2. **Grounding ledger (immediate):** clingo's JSON emits grounding/solving statistics; the DerivationRecord grows a stats field (ground atoms, ground rules, ground time, solve time). Banked every run, a standing series — the scaling decision becomes data.
3. **Growth gate (pre-registered):** a close line checks ground-atoms / (rows + edges) stays bounded (near-constant after item 1). A superlinearity trip is either a hygiene defect in a new rule (fix the rule) or the genuine scale threshold (fire item 4). The gate makes the trip loud instead of gradual.
4. **The designated growth path:** clingo multi-shot/incremental solving via the Python `clingo` module (free software; the adoption cost is a maintainer decision about the shared generic venv, plus the no-lazy-imports discipline — a new `engine_solver` module whose top-of-file import is honest). Not built now, because the honest position is that the live path does not need clingo at all (§3: A/B work is SQL-incremental; C is joins over caches), so solver scale pressure is close-time only, where full recomputation *is the audit* and minutes are acceptable. The incremental solver is built when the grounding ledger — not intuition — says so.
5. **Partitioning law:** the session is the grounding unit. `T_now` judgments never span sessions (the session is the theory boundary; consult 11's two-theory split is per-record). Cross-session accumulation happens at the KB layer under content-hash identity (marriage §6.2) as *findings*, never as one giant atom base. This caps n structurally: the engine grounds a session, not a life.

## 9. Zero-budget / self-hosted, held

Everything above is Postgres (in-core features + contrib `pg_stat_statements` + `pgcrypto`, already in use), Python in the existing generic venv, and clingo (installed; CLI today, Python module as the one flagged adoption decision). No daemons required initially; no external services; no paid anything. The single potential cost-shaped decision — resident hook daemon vs per-invocation process — is deferred behind a measurement and both options are free; the criterion is the latency ledger, not preference.

## 10. Build increments (sequence, not menu; each with an acceptance target)

1. **Judgment registry.** The typed authority module enumerating every existing judgment with class, availability, tier placement, fixtures, promotion stage. *Accept:* every judgment named in `ledger_tnow.lp`/floor/instruments appears exactly once; a parity test fails if a `.lp` `#show` or close line exists with no registry row; the e17 independence gate is recorded at P4/P5-pending.
2. **Monotone caches + cache_integrity line.** AFTER-trigger maintenance of `sup_star`/`superseded` and per-citation class-A verdicts on a scratch lineage first. *Accept:* rebuild-and-diff bit-identical across all banked targets (s10–s13, nla); the caches reproduce the banked instrument numbers through the floor unchanged.
3. **Refusal journal + tier_consistency shadow, retrofit onto the live e17 gate first.** The one production trigger enters the discipline before any new trigger is minted. *Accept:* replaying the e17 fixture set against an armed scratch kernel populates the journal; the shadow reconciles the banked e17 refusals (row-12 stub event, act-498 typo refusal) exactly; a synthetic false-refusal fixture turns the line red.
4. **Hook increment (L1′/L2′) with watermark cursor, FindingIdentity dedup, deadline/quarantine semantics, hook_fidelity close line.** *Accept:* planted ledger defect found live; unchanged record re-run inserts zero findings; a deliberately-killed payload banks QUARANTINED and the close shows it; prefix re-derivation reproduces every live finding at its watermark.
5. **Latency ledger.** Arm-time microbench + LatencyRecord + `pg_stat_statements` close line; first budget ruling requested from the maintainer on the first banked measurement. *Accept:* armed-vs-bare deltas banked for the s17 kernel; an artificial slow-trigger fixture fails arming.
6. **Grounding hygiene + growth gate.** The `defeated_asof` domain restriction; stats into DerivationRecords; the boundedness close line. *Accept:* byte-identical models on all banked targets post-retrofit; stats series populated retroactively for retained derivations where re-runnable (they are — F16).
7. **Codegen spike (decide by evidence).** One authority → `.lp` fragment + floor fragment + plpgsql body for exactly one class-A judgment; three-way differential. *Accept:* three generated encodings agree bit-identically on all fixtures and mutations flip all three; a written adopt/abandon recommendation with the observed cost.
8. **Live acts journaling (unlocks F52-class at T1).** Extend the interception hook to journal tool calls into `acts_live`; acts_parity differential against the close-time parse across one full experiment before anything consumes it. *Accept:* parity AGREE on a whole run; the F52 license-reading judgment derivable at T1 on the banked e16/e17 records replayed.

## 11. Honest unknowns, and how each is found out

- **Trigger cost at the armed kernel** on the real network path: unknown until increment 5's first microbench; no number asserted here.
- **Grounding growth constants** past toy scale: unknown; the stats series (increment 6) converts it from speculation to a chart, and the growth gate pre-registers the response.
- **Whether the refusal journal perturbs subject behavior:** the journal is subject-invisible (no grants) and refusals were already subject-visible events, so the expected delta is nil — but that is an expectation, not a finding; the standing PASSIVE-prime audit posture covers it, and the first armed experiment's analysis should look.
- **Codegen feasibility for plpgsql** from one authority: genuinely open (plpgsql is an awkward compilation target); the spike is sized to answer it cheaply, and the fallback (hand encodings under the three-way shadow + mutations) is already the operating floor, not a cliff.
- **Live acts parse fidelity** vs the close-time transcript parse: unknown; acts_parity is designed as the gate, and nothing consumes the live stream before it holds on a whole run.
- **Resident daemon need:** decided by the latency ledger, not by taste.

## 12. Deliberately not done

- **No new deny surfaces beyond promoted class-A triggers.** T1 never denies; C/D-class judgments never compile to refusal; the deontic line (status derived, action never prescribed) holds — the engine reports, the write boundary refuses, nothing else enforces.
- **No stored T_now.** The caches are A/B-class memoization under rebuild-and-diff, subject-invisible, consumer-contract-free; no class-C validity fact is ever materialized (§4's reconciliation, stated so the law is met in substance, not routed around).
- **No latency numbers, no scaling claims.** Budgets and thresholds arrive from banked measurements and maintainer rulings; this document supplies only the currencies, protocols, and enforcement shapes.
- **No new kinds/edges, no kernel truth-value change, no NLP-lane coupling** — the marriage §8 restraint is inherited wholesale.
- **No statistical framing.** Every acceptance target is a specimen or a bit-identical reproduction; N=1 apparatus discipline throughout.
