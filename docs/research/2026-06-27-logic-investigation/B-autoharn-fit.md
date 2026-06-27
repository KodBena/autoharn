# B — autoharn-fit & completeness critic

> Part of the autoharn **logics & automated-deduction investigation** — see the [index](README.md); coined terms (Pillar, *_violations gate, supersession, …) are defined in the root **[GLOSSARY.md](../../../GLOSSARY.md)**.

*Adversarial review of 13 logic families against autoharn's concrete needs. Local availability re-verified, not taken from the section text (corrections noted inline). Verified: `swipl 9.3.31`, `clingo 5.8.0` (CLI), `java` OpenJDK 25, `z3-solver 4.16.0`, `cvxpy 1.9.1`, `ortools 9.15`, `networkx 3.6.1`, `sympy 1.14`, `scipy 1.17` all present; **Soufflé absent**, **cvc5/problog/owlready2 absent**, and critically the **Python `clingo` binding is NOT in the 3.13 venv** (only the system CLI is — every "drives straight from Python, zero install" claim across the ASP/abduction/paraconsistency sections is overstated; it is subprocess-from-Python today, or `pip install clingo`). The generic venv is **Python 3.13.13**, which structurally excludes ProbLog (≤3.12) and PyReason (3.7–3.10) — a real integration gap, below.*

---

## 1. Coverage Matrix

Needs enumerated from the three pillars + cross-cutting shapes. "Best-fit" is *my* adjudication across the 13 sections (they frequently over-claim their own family); "Cheap floor" names what already suffices with zero new engines. Confidence is in the *fit claim*, not the engine's quality.

| # | Concrete need | Best-fit logic | Engine (status) | Conf. | Cheap floor that already covers it |
|---|---|---|---|---|---|
| N1 | Sharp classification `lib xor solver xor service xor venv xor script`, no fuzzy match | SMT exclusivity / DL disjointness — **detection only** | Z3 `PbEq(...,1)` (installed) / OWL `AllDisjoint` (absent) | **high** | **Postgres `CHECK … IN(...)` enforces by construction at write time** — strictly better than any *detector* |
| N2 | task-shape → blessed-tool eliciting map ("what does this PROVE") | Description Logic (routing as *inference* from task properties) | Owlready2+HermiT (absent; JRE present) | **med** | SQL mapping table + Datalog consistency gate; DL only wins if routing is *derived* |
| N3 | Liveness refreshable; refuted belief superseded not stale | Non-monotonic default-negation / linear consumption | clingo (CLI) / CHR in SWI (installed) | **med** | **Postgres ledger + TTL/`valid_until`** — deterministic & auditable (the prob-logic section itself concedes this is *more honest*) |
| N4 | Measurement SEPARATE from interpretation; "reading-of as data" unrepresentable | Datalog conflation *class-gate*; (modal de re/de dicto = flavor) | Postgres/Soufflé (PG yes, Soufflé no) | **med** | **Two-table schema** (reading ⟂ interpretation) + 1-line `conflation` gate |
| N5 | Append-only SUPERSEDES chain (Witness→Correction, prior never rewritten) | Deductive DB transitive-closure + non-monotonic latest-wins | Postgres `WITH RECURSIVE` → Soufflé | **high** | PG `WITH RECURSIVE` (awkward but works); immutability half is a TLA+/trigger concern |
| N6 | Pre-registration: criterion committed BEFORE result (temporal) | Past-time LTL / TLA+ states the *invariant* | TLA+/Spot (absent) | **high (as SSOT)** | **`WHERE t_crit >= t_result` violations-view** — every relevant section concedes SQL is the better *gate* |
| N7 | Every perf-token cites a reading or carries `[unsubstantiated]` | Datalog `_violations` (relevance/linear = semantics only) | Postgres/Soufflé | **high** | `perf_token` `NOT EXISTS reading_of AND NOT marked` view |
| N8 | DIRTY tree must NOT be promoted to confirmed | K3 (NULL) / Datalog gate; TLA+ proves *protocol* | Postgres (installed) | **high** | **`WHERE promoted AND tree_clean IS NOT TRUE`** — free in SQL's 3-valued logic |
| N9 | `{commit,tree,session_id}` else honest-NULL, never faked | Many-valued K3 (honest-NULL = first-class) | Postgres | **high** | `NOT NULL` discipline + NULL-as-suspect gate |
| N10 | Per-store `<store>_violations` CI gates | **Datalog / ASP integrity constraints — the flagship** | Postgres `WITH RECURSIVE` → Soufflé / clingo | **high** | PG is the brief's own plan; Soufflé only if CI gets slow |
| N11 | META-SWEEP: every rule declares an enforcement surface; mechanisms resolve on disk | Datalog over its own rule-catalog as EDB | Postgres/Souffle + FS scan | **med-high** | SQL over a `rules` table; the "resolves on disk" half is a *script*, not logic |
| N12 | Rule 4: key on CLASS of defect, never instances | **Datalog/ASP (universally-quantified rule heads)** | Postgres/Soufflé/clingo | **high** | Intrinsic to writing rules at all; the discipline, not the engine, enforces it |
| N13 | Status lifecycle provisional/confirmed/retracted | Temporal state-machine (TLA+) for transitions; epistemic K/B = *vocabulary* | TLA+ (absent) / SQL enum | **med** | enum column + transition-guard gate; modal logic adds inference-hygiene, not enforcement |
| N14 | Conflicting advisories COEXIST; suspect/DIRTY 3rd value, no explosion | **Paraconsistent/many-valued (Belnap FDE / K3)** | **Postgres NULL (installed)** | **high** | SQL `NULL` *is* K3; explicit `suspect` tag. Exotic provers are abandonware |
| N15 | Defaults later overridden; ADR-amendment supersession | **ASP / defeasible non-monotonic — genuine home turf** | clingo (CLI) / SWI `\+` | **high** | SQL needs hand-rolled `NOT EXISTS`; this is where logic earns keep |
| N16a | Hypothesis generation for a regression (abduction) | **ASP choice+`#minimize`** (ranked minimal) / ProbLog (posterior-ranked) | clingo (CLI) / ProbLog (absent, 3.13-blocked) | **high** | none cheap — genuinely needs a search engine |
| N16b | Learn `_violations` rules from examples (ILP) | Popper / Aleph | needs SWI+clingo (present) + pip | **med (premature)** | none — but **needs dozens of labelled rows the ledger doesn't have yet** |
| N17 | Statistical hunch vs provable truth bridge | **Probabilistic logic (ProbLog/PSL)** — only family that serves it | ProbLog (absent; **3.13 ceiling**) / PSL (JVM) | **med** | none — but the *gap is calibration*, which no logic supplies |

---

## 2. Over-served needs (plain SQL / Z3 already suffices; the fancy logic is gratuitous)

The striking finding: **most of the "killer fits" the sections trumpet are killed cheaper by Postgres + a violations view.** The exotic logic re-derives, with a second unreviewed artifact, what a schema constraint enforces by construction.

- **N1 classification** — Z3 `PbEq` and OWL `AllDisjoint` are *detectors* that fire after a bad row exists. A `CHECK kind IN (...)` / enum makes the xor **impossible to write**. Detection is strictly weaker than prevention here. The only non-gratuitous case is *inferred* class membership (DL), which autoharn does not appear to need for a hand-tagged 5-class registry.
- **N4 measurement/interpretation** — modal de re/de dicto and linear "reading-as-resource" are elegant, but separation is achieved by *two tables*; conflation is caught by one Datalog/SQL self-join. Modal depth and `⊗` add zero enforcement.
- **N6 pre-registration** — the Temporal section, the SMT section, and the Datalog section *all independently concede* a `t_crit >= t_result` view is the better gate. Past-time LTL is the prettier SSOT statement, not a needed engine.
- **N7 / N8 / N9 / N14** — perf-substantiation, dirty-promotion, honest-NULL provenance, and the suspect/DIRTY third value are **all Postgres-native K3** (`NULL` is Kleene-unknown; `IS NOT TRUE` surfaces dirty+unknown). The Paraconsistent and Many-valued sections admit this outright: *"you do not need exotic logic — you need to stop coercing unknown to false, which is schema discipline."*
- **N10 violations gates** — these *are* SQL `WITH RECURSIVE`; Soufflé is a performance upgrade for *hot* gates only, and it isn't installed.

**Bluntly: Pillar 2 (provenance) and most of Pillar 1 are a SQL-schema-plus-views job. Non-classical logic is over-served there and, worse, net-negative — see §4.**

---

## 3. Unserved or weakly-served needs (genuine gaps)

- **The encoding-trust gap (THE deepest unserved need).** *Every one of the 13 sections independently confesses the same "false authority from mis-encoding" failure* — a confidently-empty `violations`, a crisp `unsat`, a precise `0.9`, all of which launder a guess into a proof. **No logic family closes this.** The only mitigation offered everywhere is *golden fixtures + human review* — i.e. discipline, not logic. autoharn's Mechanization Discipline says "convert every lapse into a mechanism," but the mechanism that would catch a bad encoding is itself an encoding, and that regress bottoms out in human judgment. This is unserved *in principle*, and it is the load-bearing weakness (see §5).
- **N17 statistical-hunch bridge — engine exists, epistemics don't.** ProbLog is the only fit, but (a) it is **absent and blocked by the 3.13 venv ceiling**, forcing a separate 3.12 environment, and (b) the real gap is *calibration* — "a number nobody calibrated" — which no probabilistic logic supplies. Weakly served: you can compute a marginal, but you cannot *justify* the prior, so it violates the perf-token substantiation rule it was meant to bridge.
- **N16b ILP — right idea, no data.** Popper/Aleph genuinely synthesize Rule-4-class gates from examples, which nothing else does. But ILP is data-hungry and **autoharn's ledger is near-empty**; with 3 findings it overfits or finds nothing. Unserved-for-now; a later-stage mechanism, not a foundation.
- **N11 "every mechanism resolves on disk" — the logic part is thin.** The interesting half is a *filesystem scan* feeding EDB facts; the Datalog over it is trivial. No family "covers" the freshness of the on-disk check; it's a cron/CI script. Honestly a non-logic need wearing a logic costume.
- **N13 lifecycle transition-safety across interleavings** — TLA+/TLC genuinely proves "no dirty→confirmed edge reachable," which a snapshot CHECK cannot. But TLC is **design-time only** (state explosion; not a live query over Postgres) and **not installed**. So the *protocol* guarantee is weakly served at runtime — you get a one-time design proof, then drift is policed by the cheap snapshot gate.

---

## 4. Solutions-in-search-of-a-problem — tourism vs. load-bearing (blunt)

**Genuinely load-bearing for THIS project (keep):**
- **Datalog / Deductive DB (Postgres `WITH RECURSIVE`, later Soufflé).** The actual spine: supersedes-closure (N5), the `_violations` idiom (N10), Rule-4 class-keying (N12), meta-sweep (N11). Zero install, already the brief's plan.
- **ASP / clingo.** The one family with a *unique* claim: non-monotonic defaults-overridden (N15) and minimal-explanation abduction (N16a) that SQL cannot express and Z3 cannot rank. Caveat: needs `pip install clingo` for the Python binding; today it's subprocess.
- **SMT / Z3.** Consistency/exclusivity/forced-mapping gates (N1 detection, N2 consistency) with unsat-cores as blame assignment. Installed, industrial, differential-checkable against cvc5.
- **CHR (linear-logic *discipline*, already in SWI).** The 10% of substructural logic that's real: liveness consumption gates (N3). The rest of linear logic is not.

**Intellectual tourism for autoharn (name-and-shame):**
- **Relevance & Substructural logics (as infrastructure).** The section *admits it*: "do not adopt a dedicated prover," tooling is **abandonware** (MaGIC 1995, llprover needs non-free SICStus, linTAP a fragment). The entire payoff "collapses into a 30-line FDE evaluator plus discipline." That is tourism with a citation list. FDE-as-a-concept is fine; FDE-as-a-family-you-adopt is not.
- **General Linear logic (Celf / LolliMon).** "Dormant academic code," SML toolchain, a *maintenance liability for a metaproject that prizes mechanisms still resolving on disk* (self-refuting against Pillar 3). Tourism; CHR already delivers the consumption discipline.
- **Modal & Epistemic logic (full Kripke / MCMAS / CTLK).** The K (factive) vs B (defeasible) distinction is the prettiest idea in the whole brief and the **least load-bearing**: enforcement collapses to a status enum + a transition gate, MCMAS "needs an old bison," and the section warns of logical-omniscience and frame-mis-modeling traps. Keep the *vocabulary* (confirmed=knows, provisional=believes); discard the Kripke machinery. Tourism.
- **Description Logic / OWL.** Narrowly load-bearing *only* for N2 task→tool inference, and *only if* routing becomes definitionally rich. For a 5-class registry it is a heavyweight reasoner (absent; needs install) doing a `CHECK` constraint's job, and the section itself says "do not use OWL for the provenance ledger." 90% tourism.
- **Many-valued/Paraconsistent (as exotic engines).** The substance (K3) is *already in Postgres `NULL`*; the exotic part is marketing. PyReason can't even run in the 3.13 venv. Tourism above the SQL floor.
- **Probabilistic logic.** Not tourism in principle (N17 is real), but **deterministic-by-design tension**: "a probability is the enemy of 'never seen twice.'" A narrow three-corner tool (hunch-bridge, abduction-ranking, soft advisories), currently un-runnable in-venv. Provisionally-shelved, not adopted.
- **Temporal/TLA+.** Load-bearing as a *design-time* discipline for the lifecycle protocol (N13) and as the SSOT *statement* of ordering invariants (N6) — but **not** as a runtime gate (state explosion, not installed). Use precisely there, nowhere else.

**The pattern:** the families cluster into a small load-bearing core (Datalog + ASP + Z3 + CHR + Postgres-K3, almost all already installed) and a long tail of conceptually-illuminating, operationally-absent or abandonware families whose insight reduces to "a schema discipline" or "a 30-line evaluator." For a metaproject whose Pillar 3 demands *every named mechanism still resolves on disk*, adopting dormant SML/Java provers is a self-inflicted meta-sweep violation.

---

## 5. The strongest single objection (steelman) — and whether autoharn answers it

**Steelman.** autoharn's entire value rests on an LLM translating an informal discipline ("don't promote a dirty benchmark") into a formal encoding (a Datalog rule, an ASP `not`, a Kripke frame, a `0.9` weight). But that translation is the precise cognitive step the LLM is *least reliable at and the project leaves least reviewed* — and, fatally, **a mis-encoding does not fail loudly.** It yields a confidently *green* gate, a crisp `unsat`, a precise marginal — each carrying the borrowed authority of "a proof." So the formal layer does not *remove* the executive lapse Pillar 2 exists to catch; it *relocates* it from a visible place (an English sentence the maintainer can challenge) to an invisible one (a stratification, a flipped `\+`, a `some`-vs-`only` typo, `0.9` vs `0.09`) where it is *harder* to catch and *wears a tuxedo*. The evidence this is intrinsic, not incidental: **all 13 sections independently arrive at the identical "false authority" confession** — convergent failure across unrelated families is a property of the thesis, not of any one logic. And it gets worse recursively: the formal layer *adds* an artifact (the encoding) that itself needs provenance, review, and a violations gate — so by autoharn's own Mechanization Discipline every gate demands a meta-gate (golden fixtures), and **that recursion has no fixed point the logic supplies**; it terminates in human review, the very thing the project set out to mechanize away. Net: you have spent install cost and a second engine to move the lapse somewhere darker.

**Does the design answer it? Partially — and honestly only in reduced form.**

*Where the answer holds.* autoharn's mitigations are exactly on-brand and genuinely blunt the objection's *operational* edge: golden-test every gate with known-bad fixtures (a *violation-of-the-violations-check* that must light up), keep EDB/IDB separated so loaded facts are auditable apart from derived ones, store every encoding under `{commit,tree,session_id}` like any other reading, differential cross-check (Z3 vs cvc5; emit s(CASP)/unsat-core/model as a *reading* separate from its interpretation), and the META-SWEEP forces every rule to declare an enforcement surface from a closed vocabulary including **"review-only = presumptively decaying"** — which is precisely the design admitting, structurally, that an un-fixtured encoding is *not trusted*. That last move is the strongest part of the answer: autoharn does not claim its encodings are sound; it tags unproven ones as decaying and gates on it.

*Where it does not.* The answer is incomplete *in principle*, and the design's own analogies prove it: golden fixtures "verify the model, never the system" (TLA+ section) and "only test the cases you thought of" — identical to the ILP/model-checking limit. They certify nothing about *unseen* inputs. The regress (who tests the golden test?) really does bottom out in human judgment. So the defensible claim is **not** "the same error is never seen twice" but the weaker, true "**a *class* of mis-encoding, once caught and fixtured, is never seen twice**" — which is exactly Rule 4 turned on the logic layer itself, and is genuinely valuable, but is a smaller promise than the north star's wording.

**Verdict.** The thesis survives, *reduced*: non-classical logic is justified only where **(a)** the invariant is genuinely non-classical — non-monotonic supersession (N15), paraconsistent coexistence (N14, but SQL-K3 already delivers it), temporal ordering (N6, but SQL already gates it), minimal-explanation abduction (N16a) — **and (b)** a cheap deterministic Postgres view does *not* already express it. Condition (b) eliminates most of Pillars 1–2, where the exotic logic is net-negative: it adds an unreviewed artifact whose only effect is to *launder*. The only need that passes both filters cleanly and uniquely is **N15/N16a (clingo) and the N5/N10/N12 deductive spine (Datalog)** — and tellingly, *those are already installed*. The objection's deepest barb — that the encoding is the least-reviewed, highest-authority artifact — is answered not by any logic but by autoharn's discipline of treating every encoding as a *finding needing a Witness*, decaying until fixtured. That is the right answer; it is also an admission that the logic layer is trustworthy only to the exact extent the surrounding mechanization is, which is the honest ceiling on the whole enterprise.


---
*Verbatim output of the `autoharn-logics-investigation` workflow (run `wf_6be06f87-68d`, model claude-opus-4-8[1m]), 2026-06-27 — one expert agent per logic family, grounded in autoharn. The maintainer should treat engine version/license claims as agent-reported (web-checked where noted), worth a confirm before install.*
