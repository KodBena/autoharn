# A — Automation & encoding-host strategy (the git-clone-runnable path)

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Coined terms → root **[GLOSSARY.md](../../../GLOSSARY.md)**. See the [index](README.md).

Verification complete. All load-bearing tools confirmed current. Below is the consolidated AUTOMATION & ENCODING-HOST STRATEGY.

---

# AUTOMATION & ENCODING-HOST STRATEGY — autoharn run plan

**Web-verified spine (as of 2026-06-27):** Z3 4.16.0 (MIT, 2026-02-19) · cvc5 1.3.4 (BSD-3, 2026-05-07) · clingo 5.8.0 (MIT — **current; no 6.0/5.8.1 exists, correcting the ASP section's claim**) · OR-Tools 9.15.6755 (Apache-2.0, 2026-01) · mCRL2 202507.0 (Boost) · Spot 2.15.1 (GPLv3, 2026-04-25) · Lean 4.31.0 (Apache-2.0, 2026-06-13) · Rocq 9.2.0 (LGPL-2.1, 2026-03-27) · NuSMV 2.7.1 (LGPL) · Soufflé 2.5.0 (UPL-1.0) · TweetyProject 1.28 (LGPL-3, 2025-01-23) · VeriFast (MIT, active 2026, KU Leuven). **Local verified:** Z3 4.16.0, clingo 5.8.0, SWI-Prolog 9.3.31, OR-Tools, OpenJDK 25.0.2, Python 3.13, JAX. **Confirmed absent locally:** minizinc, souffle, nusmv, spot, mcrl2, lean/rocq/isabelle, problog, owlready2, rtamt, tla2tools.jar.

## (1) MASTER TABLE — formal system → how the harness runs it

| # | Formal system | Dedicated OSS tool (license, ver) | Local? | Encoding host if none / not-local | Cost tier | LLM-drivable? |
|---|---|---|---|---|---|---|
|1|Datalog / deductive DB|Soufflé (UPL-1.0, 2.5.0); Nemo (Rust)|no|**clingo** / SWI `tabling` / Postgres `WITH RECURSIVE`|T2 (or T0 via host)|Yes — `.dl`/`.lp`|
|2|Prolog, CLP, meta-interp.|**SWI-Prolog (BSD-2, 9.3.31)** +chr|**yes**|— (is host); s(CASP) pack|T0|Yes — clauses|
|3|Answer Set Programming|**clingo (MIT, 5.8.0)**|**yes**|— (host *is* tool)|T0|Yes — `.lp`|
|4|SMT / classical FOL|**Z3 (MIT, 4.16.0)**; cvc5 (BSD-3, 1.3.4) as diverse oracle|**yes** (Z3)|—|T0 (Z3) / T1 (cvc5 pip)|Yes+gate — SMT-LIB|
|5|SAT / CP / finite-domain|**OR-Tools CP-SAT (Apache, 9.15)**; MiniZinc (MPL-2, 2.9.7)|**yes** (CP-SAT)|Z3/clingo for UNSAT-proof|T0 / T1 (mzn)|Yes — Python/mzn|
|6|LTL/CTL model checking|NuSMV (LGPL, 2.7.1); Spot (GPLv3, 2.15.1). **Exclude nuXmv (non-commercial)**|no|encode bounded LTL→Z3 BMC|T2|Yes — `.smv`/`.ltl`|
|7|TLA+ / TLC refinement|**tla2tools.jar (MIT)**; Apalache (Apache, →Z3)|JVM yes, jar no|Apalache reuses local Z3|T1 (vendor jar)|Yes+gate — `.tla`|
|8|Metric/real-time/interval (MTL/STL, Allen/HS)|RTAMT (BSD); MoonLight (Apache)|no|**bounded MTL/STL→Z3 unrolling; Allen endpoints→Z3 LIA / clingo**|T1 (pip) / T3|Yes — STL text / SMT|
|9|μ-calculus / process logics|mCRL2 (Boost, 202507.0). **Exclude CADP (academic)**|no|**parity game→clingo; ν-invariant→Z3 k-induction**|T2 / T3|Yes+gate — `.mcf`|
|10|Description Logic / OWL|owlready2 (LGPL,0.51)+HermiT/Pellet; ELK; **ROBOT (BSD, JVM)**|JVM yes|temporal/prob DL: snapshot→TLC/clingo; prob→ProbLog|T1|Yes — OWL func. syntax|
|11|HOL / dependent types / proof asst.|Rocq (LGPL-2.1,9.2); Lean (Apache,4.31); Isabelle (BSD,2025)|no (Z3 backend yes)|hammer discharges into local Z3|T2|**Assisted** — vacuity-gated|
|12|Probabilistic logic / SRL|ProbLog (Apache,2.2.x); PSL (Apache,JVM). **MLN tools dead**|no|**MLN→clingo weak constraints; WMC→ProbLog**|T1 / T3|Yes+gate — `.pl`|
|13|Prob. programming / Bayesian|**NumPyro (Apache,0.21, via JAX)**; PyMC; CmdStan; ArviZ|**yes**|—|T0/T1|Yes+gate — model+SBC|
|14|Inductive Logic Programming|Popper (MIT,5.0.1, ASP backend); Aleph (SWI pack)|backend yes|Popper compiles to **clingo** (replayable)|T1|Yes — bias/bk/exs|
|15|Modal logic substrate (K–S5)|MetTeL2 (GPL-3, gen); LoTREC (GPL)|no|**standard translation ST→Z3 / clingo** (local)|T2 / T3|Yes — ST→SMT|
|16|Epistemic / DEL (S5n, PAL)|SMCDEL (GPL-2,1.3.0, Haskell); MCMAS (GPL)|no|**S5n classes→clingo; bounded Ck→Z3**|T2 / T3|Yes+gate — `.smcdel`|
|17|Justification Logic (LP)|**none production**|—|**SWI-Prolog meta-interpreter** (local); Datalog why-prov|T3|Yes — Horn checker|
|18|Provability Logic (GL/Löb)|none dominant (LoTREC/HOL-Light oracle)|—|**clingo well-foundedness guardrail** (local); Z3 finite frames|T3 (T0 guardrail)|Yes — `.lp` graph|
|19|Deontic / normative|s(CASP) (Apache, SWI pack); SPINdle (LGPL,JVM); LogiKEy/Isabelle; rio→SAT|pack/JVM yes|s(CASP) on local SWI; SPINdle jar|T1|Yes+gate — `.pl`|
|20|STIT / agency|**none mature** (Deolingo MIT, pip)|—|**clingo choice-cells** (local); Z3 bounded validity|T3 (T0 core)|Yes — `.lp`|
|21|Belief revision (AGM/Spohn)|TweetyProject (LGPL,1.28, JVM)|JVM yes|**AGM→clingo `#minimize`** (local); Equibel; Z3 ranked|T1 (T0 encode)|Yes+gate — `.lp`|
|22|Default / circumscription / autoepistemic|**clingo** (defaults/AEL direct); circ2dlp (GPL)|**yes**|circumscription: circ2dlp→clingo or `Ab`-`#minimize`|T0 / T1|Yes — `.lp`|
|23|Defeasible / argumentation (Dung/ASPIC+/DeLP)|µ-toksia (MIT,SAT); PyArg; py-aspic; Tweety/DeLP|no (clingo yes)|**AF→clingo** (local); µ-toksia as INDEP channel|T1 (T0 core)|Yes+mutation-gate|
|24|Counterfactual / causal (Lewis/HP)|HP2SAT (MIT,JVM); chirho; DoWhy (MIT,0.14)|JVM yes|**HP AC2/AC3→clingo / Z3** (local)|T1 (T0 encode)|Yes+gate — SCM|
|25|Paraconsistent / many-valued / fuzzy (FDE/LP/t-norm)|none everyday (MULTLOG gen; mNiBLoS)|—|**FDE/LP two-bit→Z3; t-norm→Z3 LRA/NRA; clingo conflict atoms** (local)|T3|Yes — SMT/`.lp`|
|26|Substructural / linear / separation / BI|**VeriFast (MIT, 25.11)**; Iris/coq-iris (BSD,4.4.0); Viper|no|linear resource arith→Z3/clingo (proof needs VeriFast)|T2|**Assisted** — annot.-gate|
|27|Hyperintensional (truthmaker/grounding/dependence/free)|free logic: Benzmüller–Scott Isabelle embed|no|**dependence→clingo; free→Isabelle; truthmaker/grounding→clingo/Z3 lattice (FRONTIER)**|T3 / T4|Frontier|

## (2) TIERED RUN PLAN

**Tier 0 — ALREADY PRESENT (zero install; the load-bearing majority):** Z3 4.16.0, clingo 5.8.0, SWI-Prolog 9.3.31 (+chr), OR-Tools CP-SAT 9.15, Postgres recursive, OpenJDK 25, JAX/NumPyro. These alone host obligations #2,3,4,5,13,22 directly and #1,8,9,14,15,16,17,18,20,21,23,24,25,27 by encoding. **≈20 of 27 formal systems are runnable today with no new dependency.**

**Tier 1 — PIP-OR-APT (one permissive command):** `pip`: owlready2, problog, rtamt, popper-ilp, deolingo, dowhy, minizinc, pymc, cmdstanpy, cvc5, spot (conda/pip). SWI packs: `pack_install(scasp)`, `pack_install(aleph)`. Vendored jars on the present JDK (single `wget` each, T1 not T2): **tla2tools.jar** (TLA+/TLC, MIT), ROBOT (OWL CI), TweetyProject (belief revision/argumentation), HP2SAT (causation), SPINdle (deontic), µ-toksia binary.

**Tier 2 — COMPILE / PREBUILT BINARY:** Soufflé (apt/source), NuSMV 2.7.1, mCRL2 202507.0, VeriFast 25.11 (prebuilt Linux binaries — no build), Konclude, SMCDEL (Hackage/stack), MCMAS, MetTeL2/LoTREC (Java), one proof assistant (Lean via `elan` is the lightest single-binary).

**Tier 3 — ENCODE-INTO-HOST (no dedicated tool ships; standard/lossless encoding into Tier-0):** Justification Logic→SWI meta-interpreter · Provability GL→clingo well-foundedness + Z3 finite frames · STIT→clingo choice-cells · FDE/LP/K3→Z3 two-bit, t-norm→Z3 LRA/NRA · modal K–S5→ST→Z3/clingo · DEL S5n→clingo/Z3 · circumscription→circ2dlp/clingo · AGM revision→clingo `#minimize` · bounded MTL/STL→Z3 unrolling, Allen/HS→Z3 LIA · μ-calculus parity game→clingo · dependence logic→clingo · HP causation→clingo/Z3 · linear/separation frame-conditions→Z3. **This tier is the thesis made concrete: toolless ≠ unleverageable.**

**Tier 4 — HARD / FRONTIER (qualify heavily or hold advisory):** truthmaker semantics & metaphysical grounding (no tool, semantics open — flagged speculative) · full multi-agent STIT validity (NEXPTIME, no implementation) · temporal & probabilistic DL (no production reasoner) · paraconsistent graded DL · full-HS satisfiability (undecidable — restrict to point algebra) · MLN exact marginals (pracmln/Tuffy unmaintained — encode instead) · LLM-authored proof-assistant **specifications** (vacuity is the live risk, not the proof).

## (3) ENCODING-HOST META-TOOLS — standardize on seven

1. **clingo (ASP)** — universal finite-domain / nonmonotonic / stable-model host. Carries 11+ toolless or not-local logics: Datalog, default/circumscription/autoepistemic, Dung/ASPIC+ argumentation, STIT choice-cells, AGM revision, DEL S5n, μ-calculus parity games, dependence logic, HP-causation, MLN MAP (weak constraints), GL well-foundedness guardrail, paraconsistent conflict atoms.
2. **Z3 (SMT)** — rich-theory exact oracle + countermodel generator. Carries INV/STRUCT/COHERE/CLASS, modal ST→FOL, bounded MTL/STL + Allen intervals (LIA), FDE two-bit + t-norm fuzzy (LRA/NRA), HP-causation, ranked belief revision, GL finite frames, linear-logic frame conditions, proof-assistant `hammer` backend. **Pair with cvc5 as the no-common-cause second checker (INDEP).**
3. **SWI-Prolog (+CHR, +s(CASP), +tabling)** — meta-interpreter / labelled-deduction / justification-tree host. Carries Justification Logic, defeasible-deontic labelled interpreters, TMS for REVISE, Datalog via tabling, CHR paraconsistent quarantine, Aleph ILP, and s(CASP)'s natural-language justification trees (PROV/RECORD primitive).
4. **Postgres recursive CTE** — when the EDB already lives in the audit DB: linear-recursive Datalog, TRACE reachability, grounding/acyclicity checks.
5. **OR-Tools CP-SAT + MiniZinc** — finite-domain certificate engine plus the portable cross-solver diversity layer (one `.mzn`, retarget Chuffed/Gecode/CP-SAT for INDEP).
6. **JVM (OpenJDK 25) as vendored-jar host** — one runtime, many qualified jars: TLA+/TLC + Apalache, ROBOT (OWL), TweetyProject (belief revision/argumentation/DeLP), HP2SAT (causation), SPINdle (deontic). No per-tool toolchain.
7. **JAX/NumPyro + ArviZ** — the calibrated-numeric channel with mechanical convergence gates (R̂, ESS, divergences, SBC) as DO-178C-style tool-qualification evidence.

**Cross-cutting qualification rule (INDEP, mandatory):** every LLM-authored encoding is discharged by a mechanical second channel from a *different* host family — clingo↔Z3, Z3↔cvc5, NuSMV↔Spot, mCRL2↔(clingo parity + Z3 k-induction), clingo↔µ-toksia, Popper↔clingo-replay, TweetyProject↔clingo — gated by golden fixtures + mutation score, **never by an LLM judge** (the deflation-detector that deflated). Disagreement disqualifies the encoding, not the obligation.

**Redistribution exclusions for the `git clone autoharn` deliverable:** nuXmv (non-commercial binary), CADP (academic license) — usable only as offline cross-checkers, never in the shipped gate. Archived/dead, route around: DDlog (archived → Nemo), pracmln/Tuffy (unmaintained → encode MLN into clingo/ProbLog).

Sources: [Z3 releases](https://github.com/z3prover/z3/releases) · [cvc5 releases](https://github.com/cvc5/cvc5/releases) · [clingo releases](https://github.com/potassco/clingo/releases) · [mCRL2 202507.0](https://zenodo.org/records/17278624) · [OR-Tools releases](https://github.com/google/or-tools/releases) · [Spot](https://spot.lre.epita.fr/) · [Lean 4 releases](https://github.com/leanprover/lean4/releases) · [Rocq 9.2.0](https://rocq-prover.org/releases/9.2.0) · [NuSMV 2.7.1](https://nusmv.fbk.eu/articles/271/) · [Soufflé 2.5](https://souffle-lang.github.io/release-2.5.0.html) · [TweetyProject](https://github.com/TweetyProjectTeam/TweetyProject/releases) · [VeriFast](https://github.com/verifast/verifast)


---
*Cross-cut — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
