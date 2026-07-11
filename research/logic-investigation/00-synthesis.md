# 00 — Synthesis: logics & automated deduction for autoharn

> Part of the autoharn **logics & automated-deduction investigation** — see the [index](README.md); coined terms (Pillar, *_violations gate, supersession, …) are defined in the root **[GLOSSARY.md](../../GLOSSARY.md)**.

## Thesis verdict

**The thesis is TRUE, but only in a *reduced* form — and the reduction is the whole finding.**

"Extended/non-classical logic + automated deduction, now authored-by-LLM, concretely improves LLM-based project management" survives for autoharn **iff** a candidate use passes two filters simultaneously:
1. the invariant is **genuinely non-classical** (non-monotonic supersession, minimal-explanation abduction, temporal ordering, paraconsistent coexistence), **and**
2. a cheap deterministic **Postgres view does not already express it**.

Run those filters across all 17 enumerated needs and the result is stark: **Pillar 2 (provenance) and most of Pillar 1 (classification) are a SQL-schema-plus-views job.** SQL `NULL` *is* Kleene K3; `CHECK kind IN (...)` makes the lib/solver/service/venv/script xor *impossible to write* (strictly better than any Z3/OWL *detector* that fires after the bad row exists); `WHERE t_crit >= t_result` is a better pre-registration gate than past-time LTL; `WHERE promoted AND tree_clean IS NOT TRUE` gates dirty-promotion for free. In those places the exotic logic is not just gratuitous — it is **net-negative**, because it adds a second, unreviewed artifact whose only effect is to re-derive what a constraint already enforced.

What passes both filters cleanly and uniquely is small and, tellingly, **almost entirely already installed**: the **Datalog spine** (supersedes-closure N5, the `_violations` idiom N10, Rule-4 class-keying N12) in Postgres `WITH RECURSIVE`; **non-monotonic defaults/supersession** (N15) and **minimal-explanation abduction** (N16a) in clingo; **consumption discipline** (N3) in CHR, already bundled in SWI-Prolog. That is the substance. Everything else — full Kripke/MCMAS, general linear logic (Celf/LolliMon), dedicated relevance provers (MaGIC 1995, llprover needs non-free SICStus), ASPIC+/DeLP, MLNs — is **hype, tourism, or abandonware** whose insight collapses into "a schema discipline" or "a 30-line FDE evaluator."

**Hype-vs-substance, one line:** the families cluster into a ~5-engine load-bearing core that is mostly already on disk, and a long tail of conceptually-illuminating, operationally-absent tools. For a metaproject whose Pillar 3 demands *every named mechanism still resolves on disk*, adopting dormant SML/Haskell provers would itself be a meta-sweep violation.

**The critic's strongest objection (steelmanned).** autoharn's value rests on an LLM translating an informal discipline into a formal encoding — the precise cognitive step the LLM is least reliable at and the project reviews least. Fatally, **a mis-encoding does not fail loudly**: a flipped `\+`, a `some`-vs-`only` typo, a `0.9`-vs-`0.09`, a wrong stratification yields a *confidently green* gate, a crisp `unsat`, a precise marginal — each wearing the borrowed authority of "a proof." So the formal layer does not *remove* the executive lapse Pillar 2 exists to catch; it **relocates** it from a visible English sentence the maintainer can challenge to an invisible artifact where it is harder to catch and wears a tuxedo. The evidence this is intrinsic, not incidental: **all 13 sections independently arrive at the identical "false authority" confession** — convergent failure across unrelated families is a property of the thesis, not of any one logic. Worse, the encoding is itself an artifact needing provenance and a gate, so every gate demands a meta-gate, and that regress bottoms out in human review — the very thing autoharn set out to mechanize away.

**The answer — honest, partial, and exactly on-brand.** autoharn's own disciplines blunt the *operational* edge: golden-fixture every gate with a known-bad case that **must** light it up (a violation-of-the-violations-check); keep EDB/IDB (loaded vs derived) separated so facts are auditable apart from inferences; store every encoding under `{commit, tree, session_id}` like any other reading; differential-check (Z3 vs cvc5 on shared SMT-LIB2); and — the strongest move — the **META-SWEEP forces every rule to declare an enforcement surface from a closed vocabulary that includes "review-only = presumptively decaying."** That is the design *structurally admitting* an un-fixtured encoding is not trusted. Where the answer does **not** reach: golden fixtures "verify the model, never the system" and certify nothing about unseen inputs; the regress genuinely bottoms out in human judgment. So the defensible north star is **not** "the same error is never seen twice" but the weaker, true: **"a *class* of mis-encoding, once caught and fixtured, is never seen twice"** — Rule 4 turned on the logic layer itself. That is genuinely valuable and is the honest ceiling on the whole enterprise: the logic layer is trustworthy exactly to the extent the surrounding mechanization is.

## Applicability matrix (concise)

| autoharn need | Logic family that earns its place | Engine | Confidence |
|---|---|---|---|
| Supersedes-closure / live-head (N5); `_violations` idiom (N10); Rule-4 class-keying (N12); meta-sweep (N11) | **Datalog / deductive DB** — the spine | Postgres `WITH RECURSIVE` → Soufflé if CI slows | **high** |
| Defaults later overridden; ADR-amendment supersession; refuted-belief retraction (N15) | **ASP / non-monotonic (default negation)** — *unique* claim SQL can't express cleanly | clingo | **high** |
| Ranked minimal hypotheses for a regression (N16a) | **Abduction (ASP choice + `#minimize`)** — no cheap floor exists | clingo (ProbLog if posterior-ranking wanted) | **high** |
| Liveness as consume-once resource; refutation *spends* the live token (N3) | **Linear-logic discipline → CHR** (the real 10% of substructural logic) | SWI-Prolog `library(chr)` | **med-high** |
| Honest-NULL / suspect / DIRTY third value; conflicting advisories coexist without explosion (N9, N14) | **Many-valued K3 / Belnap FDE** — but the substance *is already* Postgres `NULL` | Postgres (FDE in ~30 lines if `both` ever needed) | **high** (cheap floor wins) |
| Classification xor (N1); task-shape→tool *consistency*; forced-mapping gates (N1/N2) | **SMT / classical FOL** — detection + unsat-core blame; but `CHECK`/enum *prevents* by construction | Z3 (differential vs cvc5) | **high** for consistency gates; classification over-served by SQL |
| Lifecycle protocol: no dirty→confirmed edge across *all* interleavings (N13); ordering-invariant SSOT (N6) | **Temporal / TLA+ (design-time); LTL-with-past monitors (runtime)** | TLC (offline proof) / Spot (replay monitor) | **med** — design-time only; SQL gates the snapshot |
| Task-shape→tool routing *as inference* (N2) | **Description Logic** — *only if* routing becomes definitionally rich | Owlready2 + HermiT | **low-med** (90% tourism for a hand-tagged 5-class registry) |
| Induce `_violations` rules from labelled examples (N16b) | **ILP** — synthesizes Rule-4-class gates nothing else can | Popper / Aleph | **med (premature)** — needs dozens of labelled rows the ledger lacks |
| Statistical-hunch↔provable-truth bridge (N17) | **Probabilistic logic** — only family that serves it | ProbLog / PSL | **med** — engine exists, *calibration* doesn't; 3.13-venv-blocked |

## Recommended stack (tiered)

### ADOPT NOW — already present, high-leverage, zero or one trivial install
- **Postgres `WITH RECURSIVE`** (installed) — the gate/ledger substrate. Job: every `<store>_violations` view, the supersedes-closure, honest-NULL/K3 third value, dirty-promotion gate. *Prototype every gate here first.* **Install cost: none.**
- **Z3 4.16** (installed) — classification-xor detection (`PbEq(...,1)`), task→tool consistency, forced-mapping gates with unsat-core as blame assignment. **Install cost: none.**
- **SWI-Prolog 9.3.31 + `library(chr)`** (installed, bundled) — liveness/claim/promotion consumption gates; the one real slice of linear logic. **Install cost: none.**
- **clingo 5.8.0** — non-monotonic supersession (N15) and minimal abduction (N16a): the two needs that uniquely justify the whole non-classical thesis. **CLI installed (subprocess-drivable today); `pip install clingo` for the Python binding — trivial, MIT.** *Note: every "drives straight from Python, zero install" claim in the source sections is overstated — the binding is not in the 3.13 venv yet.*

### PROTOTYPE NEXT — focused spike before committing
- **cvc5 1.3.4** — `pip`, BSD-3. Differential cross-check vs Z3 on shared SMT-LIB2 (disagreement = encoding bug). Directly serves the encoding-trust mitigation.
- **s(CASP)** — `pack_install(scasp)` on SWI, light. Justification trees: machine-checkable "why did `usable(z3)` survive," emitted as a *reading* separate from its interpretation.
- **Soufflé 2.5** — apt/compile, UPL-1.0. Same `.dl` source as the Postgres prototypes; promote *only* hot gates if CI measurably slows. Do not pre-optimize.
- **Spot 2.15.1** — apt/compile, **GPL-3.0** (copyleft, fine for an open repo — confirm policy). LTL-with-past runtime monitors for pre-registration / no-resurrection / lifecycle-monotonicity, replayed over the event log.
- **TLA+ / TLC** (`tla2tools` jar; OpenJDK 25 present) — design-time proof that no dirty→confirmed edge is reachable across all interleavings. **Mandate a deliberately-broken variant TLC must reject.** Design-time only — not a live query.
- **ProbLog 2.2.10** — Apache-2.0, **but PyPI wheels list ≤Py3.12; the generic venv is 3.13** → spike in a separate 3.12 venv. The only engine for the hunch↔confidence axis + posterior-ranked abduction. Provisional, not adopted — see Open Questions on the calibration gap and two-venv tax.

### WATCH — real, but not yet
- **Popper / Aleph** (deps present) — ILP to *induce* Rule-4 gates. Defer until the ledger holds dozens of labelled rows; induced rules enter as **provisional**, never auto-promoted.
- **Owlready2 + HermiT** (`pip`, LGPL-3.0; **gate on a 3.13 import smoke-test** — classifiers advertise only 3.6–3.10) — adopt only if task→tool routing becomes definitionally rich. For a hand-tagged 5-class registry it is a heavyweight reasoner doing a `CHECK`'s job.
- **py-metric-temporal-logic** (`pip`, MIT) — cheap `◇≤Δ` benchmark-timing monitors if real-time bounds ever matter.

### ACADEMIC-CURIOSITY-ONLY — read for insight, do not put in CI
- **FDE / Belnap four-valued** — adopt the *concept* (`true/false/both/neither`) as a ~30-line SQL/Python evaluator if `both` is ever needed; there is **no prover worth running** (the entire relevance/linear-prover tier — MaGIC 1995, llprover/non-free SICStus, linTAP — is abandonware).
- **Celf / LolliMon** — dormant SML research code; CHR already delivers the consumption discipline. Reference reading only.
- **Full Kripke / MCMAS / SMCDEL (modal-epistemic, DEL)** — keep the *vocabulary* (confirmed=knows, provisional=believes); discard the machinery. Enforcement collapses to a status enum + a transition gate.
- **TweetyProject (ASPIC+/DeLP), PSL/MLN (pracmln unmaintained ~2018)** — scale autoharn never reaches; only for genuine attack-cycle argumentation, which the ledger does not yet have.
- **PyReason** — BSD-3 but **Python 3.7–3.10 only**; cannot live in the 3.13 venv. Interval axis only, research-grade 0.x.
- **AVOID outright (license-incompatible with an open public CI repo):** **nuXmv** (non-commercial binary-only) and **DLV2 / I-DLV** (free academic/non-profit only) — both have in-plan OSS substitutes (Spot/NuSMV/TLA+; clingo). Vet **ILASP/FastLAS** (non-OSI "free-for-research") before any public-repo gate.

## Learning path (builds from SQL + Z3 → the exotic)

Each rung: the single best resource, and the autoharn artifact to build *at that rung* so learning is hands-on.

1. **K3 / three-valued SQL** *(you already know SQL).* Resource: re-read the brief's own `WHERE promoted AND tree_clean IS NOT TRUE` pattern + Priest, *Intro to Non-Classical Logic*, K3/LP chapter. **Build:** the dirty-promotion and honest-NULL `_violations` views, each with a known-bad fixture that must light it up. *Lesson: stop coercing unknown→false; `NULL` is Kleene-unknown.*
2. **SMT exclusivity** *(you already know Z3).* Resource: the Z3 Guide (microsoft.github.io/z3guide), the SAT/UNSAT/model/core loop. **Build:** the classification `PbEq(...,1)` detector **and** the equivalent `CHECK kind IN (...)` — see for yourself that prevention beats detection. Add a cvc5 differential run.
3. **Datalog proper** *(generalize the recursive views).* Resource: Abiteboul/Hull/Vianu, *Foundations of Databases*, Ch. 12–15 (free PDF) + the Soufflé tutorial. **Build:** recast the supersedes-closure as a `.dl` program; learn stratified negation and the EDB/IDB split (auditable facts vs derivations).
4. **CHR / consumption discipline** *(your first substructural step).* Resource: Frühwirth, *Constraint Handling Rules* + SWI `library(chr)` docs. **Build:** the liveness gate where `refute` *consumes* the matching `live` token.
5. **ASP / clingo — non-monotonic + abduction** *(the load-bearing exotic).* Resource: Gebser/Kaminski/Kaufmann/Schaub, *Answer Set Solving in Practice*, ch. 1–3 + the Potassco guide. **Build:** `holds(F) :- finding(F), not superseded(F)` with the `:- result(R), dirty(R), confirmed(R)` integrity constraint, plus the `#minimize` regression-abduction program. Emit s(CASP) justification trees.
6. **Temporal / TLA+** *(reasoning over histories, not snapshots).* Resource: Hillel Wayne, learntla.com (running model-check in an afternoon) → Lamport, *Specifying Systems*. **Build:** the status-lifecycle spec with a deliberately-broken variant TLC must reject.
7. **Probabilistic logic** *(the hunch↔truth axis — last, because it's the most dangerous).* Resource: De Raedt/Kimmig/Toivonen, ProbLog (IJCAI 2007) + problog.readthedocs.io. **Build (in a 3.12 venv):** a posterior-ranked regression-cause query — then confront calibration: store every weight with the reading that justifies it, or mark `[unsubstantiated]`.
8. **ILP / Popper** *(synthesize a gate from examples).* Resource: Cropper & Dumančić, "ILP at 30" (JAIR 2022) + Popper README. **Build (once the ledger has data):** induce `bad_finding(X) :- perf_token(X), no_reading(X)` from labelled rows; enter it as **provisional**.

## First concrete experiment

**One logic:** abductive ASP (non-monotonic search). **One engine:** clingo (CLI today, or `pip install clingo`). **One invariant:** Pillar-3 hypothesis-generation-to-explain-a-regression (N16a).

Chosen because it is the single need with **no cheap Postgres floor** — SQL cannot rank minimal explanations and Z3 gives one model with no parsimony story — so it is the cleanest test of whether the logic layer is non-gratuitous. It also forces the encoding-trust mitigation into the loop.

**Spike:** seed a small theory of candidate causes (`dirty_tree`, `dep_bump`, `env_drift`, `cold_cache`) with background `touched/1` readings drawn from a real ledger row, encode the observed slowdown as `:- not regression`, and enumerate answer sets under `#minimize { 1,C : holds(C) }`. Store the encoding as a finding under `{commit, tree, session_id}`; emit each answer set as a *reading* separate from its interpretation.

**Success criterion (must hit all three):**
1. **Correctness:** returns the seeded minimal cause-set as the top-ranked explanation, and treats "≥1 explanation" as **suspect**, never **confirmed**.
2. **Encoding-trust (the load-bearing test):** a **mutation test** — silently dropping one abducible or flipping one `not` — makes the gate return a wrong or empty explanation, *and a golden fixture catches that mutation*. This is the "class of mis-encoding, once fixtured, never seen twice" claim, made executable.
3. **Earns-its-keep (the honest control):** a side-by-side attempt to express the same ranked-minimal abduction in Postgres. If SQL turns out comparably clear, the spike's verdict is "ASP does **not** earn its keep here" — and that is a successful, publishable result, not a failure.

## Open questions (genuine forks only the maintainer can decide)

1. **The two-venv tax for probability.** Is the hunch↔confidence bridge (N17) worth maintaining a separate Python-3.12 environment for ProbLog — *given that the real gap is calibration*, which no probabilistic logic supplies ("a number nobody calibrated")? Or stay **clingo-only** (crisp minimal explanations, no priors to justify), and accept that the statistical-hunch axis is served by discipline, not by a marginal? A probability is, as the source notes, "the enemy of *never seen twice*."

2. **Postgres-first vs. second-runtime-in-CI.** Keep the entire gate layer in Postgres (one store, zero install, the brief's own plan) and promote to Soufflé/clingo *only* on measured CI slowness — or invest early in clingo as a standing CI engine for the non-monotonic/abductive gates? This is a fork about how much ASP's declarative clarity justifies a second runtime and its own failure modes (grounding explosion, the un-typed `not`).

3. **The north-star wording.** Adopt the **reduced** claim explicitly in the charter — *"a CLASS of mis-encoding, once caught and fixtured, is never seen twice"* — or retain the stronger *"the same error is never seen twice"*? This is a values fork: the reduced form is the one the design can actually defend; the stronger form over-promises against the encoding-trust ceiling.

4. **Does routing ever become definitional?** Will task-shape→tool routing (N2) acquire enough definitional structure (derive `SMTSuitable` from task *properties*) to justify a DL reasoner — or is it permanently a hand-tagged 5-class `CHECK` + SQL mapping? This decides whether Owlready2/HermiT is **WATCH** or **drop**.

5. **License policy for a public CI repo.** Hard rules needed on: **GPL-3.0 copyleft** (Spot) shipped in CI; **non-OSI "free-for-research"** (ILASP/FastLAS, DLV2); and confirming the **non-commercial** AVOIDs (nuXmv) stay out. Only the maintainer sets the repo's license bar.


---
*Verbatim output of the `autoharn-logics-investigation` workflow (run `wf_6be06f87-68d`, model claude-opus-4-8[1m]), 2026-06-27 — one expert agent per logic family, grounded in autoharn. The maintainer should treat engine version/license claims as agent-reported (web-checked where noted), worth a confirm before install.*
