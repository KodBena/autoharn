# A — Software landscape & install plan

> Part of the autoharn **logics & automated-deduction investigation** — see the [index](README.md); coined terms (Pillar, *_violations gate, supersession, …) are defined in the root **[GLOSSARY.md](../../../GLOSSARY.md)**.

*Consolidator's note: dedupe across all 13 family sections. Rows marked **✓** were independently web-verified (version/license/bindings) in June 2026; see "Web verification" at the end. Local probes confirmed: `swipl 9.3.31`, `clingo 5.8.0` + `gringo`, `java OpenJDK 25.0.2`, venv `python 3.13.13` with `z3-solver 4.16.0.0`, `networkx 3.6.1`, `sympy 1.14.0`, `scipy 1.17.1`, `cvxpy 1.9.1`, `ortools 9.15.6755`. The venv has **no** `clingo`/`cvc5`/`problog`/`owlready2` Python packages yet; `souffle`/`spot`/`tlc`/`maude` binaries absent.*

## Unified engine catalog

| engine | logic family | license | language / bindings | install cost | maturity | drivable-by-LLM? | verdict |
|---|---|---|---|---|---|---|---|
| **PostgreSQL `WITH RECURSIVE`** | Datalog / K3 three-valued (NULL) | PostgreSQL (BSD-ish) | SQL; psql, psycopg | **installed** | very high | very high | **Adopt** — the gate/ledger substrate; prototype every `_violations` view here first |
| **Z3** ✓ | SMT / classical FOL | MIT | C++; `z3-solver` (py), SMT-LIB2 CLI | **installed 4.16.0.0** | very high | very high | **Adopt** — primary feasibility/exclusivity engine |
| **SWI-Prolog** (+ `library(clpfd)`, `library(chr)`) ✓ | Prolog / CLP(FD) / CHR (resource) | BSD-2 | Prolog; `swipl` CLI, `janus-swi`, `pyswip` | **installed 9.3.31** (latest stable 10.0.2) | very high | high (cut/negation care) | **Adopt** — closure, defaults, CHR consumption gates; clpfd+chr bundled, zero extra cost |
| **clingo** (gringo+clasp) ✓ | ASP / defeasible / abduction | MIT | C++; `import clingo` (pip), CLI | **CLI installed 5.8.0**; pip for py-binding | very high | high (ASP idioms) | **Adopt** — flagship for gates, non-monotonic defaults, abduction; add Python wheel |
| **cvc5** ✓ | SMT / classical FOL | BSD-3 | C++; `cvc5` (pip), pythonic API, SMT-LIB2 | pip (trivial) **1.3.4** | high | high (Z3-like API) | **Install** — differential cross-check vs Z3 on shared SMT-LIB2 |
| **clorm** | ASP tooling (ORM) | MIT | Python | pip (trivial) | medium | high | **Install** — maps Postgres rows ↔ clingo facts cleanly |
| **janus-swi** ✓ | Prolog↔Python bridge | BSD-2 | pip (compiles small ext; needs SWI+CC, both present) | pip (light) | current (SWI team) | high | **Install** — CI glue from Python to SWI; ~5× faster than PySwip |
| **PySwip** | Prolog↔Python bridge | MIT | pip | pip | mature (community) | medium | Alternative to janus; more example code, slower |
| **networkx** | graph / Petri-net reachability | BSD-3 | Python | **installed 3.6.1** | high | high | **Reuse** — lightweight resource/reachability checks |
| **py-metric-temporal-logic** | MTL (real-time monitors) | MIT | pure Python | pip (trivial) | small/niche | high | **Install** — cheap `◇≤Δ` benchmark-timing monitors |
| **Owlready2** ✓ | Description Logic / OWL 2 | LGPL-3.0 | Python native; SQLite; bundles HermiT | pip; JRE present | mature | high | **Prototype** — capability classification + task→tool inference; **verify import on Py 3.13** (PyPI classifiers list only 3.6–3.10) |
| **HermiT** | OWL 2 DL reasoner | LGPL | Java (via Owlready2) | bundled jar + JRE | mature | medium | With Owlready2 (default reasoner) |
| **ELK** | OWL 2 EL reasoner | Apache-2.0 | Java (OWLAPI/CLI) | jar + JRE | mature | medium | Alt to HermiT if EL profile suffices |
| **s(CASP)** | goal-directed ASP + justification trees | Apache-2.0 | Prolog; SWI pack, CLI | `pack_install(scasp)` (light) | medium-high | medium | **Prototype** — when maintainer wants machine-checkable "why" |
| **Soufflé** ✓ | Datalog (compiled) | UPL-1.0 | `.dl` DSL; C++; CLI, CSV/SQLite I/O | apt or compile | high | high | **Prototype** — promote hot Postgres gates to native checkers if CI slows (**2.5**) |
| **ProbLog** ✓ | probabilistic LP (distribution semantics) | Apache-2.0 | Python lib + CLI | pip; **PyPI lists ≤Py3.12** → spike in 3.12 venv | mature | high | **Prototype** — the one tool for "hunch→confidence" + ranked regression abduction |
| **TLA+ / TLC** (tla2tools) | temporal model checking (LTL/state-machine) | MIT | Java jar; CLI | jar + JRE (present) | very high (industrial) | medium | **Prototype** — design-time proof of status-lifecycle protocol; ships with a must-fail canary spec |
| **Spot** ✓ | LTL/PSL ω-automata + runtime monitors | **GPL-3.0** | C++; first-class Python bindings, CLI | apt or compile | mature | high | **Prototype** — highest-value ordering/no-resurrection monitors (**2.15.1**); GPL copyleft OK for open repo |
| **Popper** ✓ | ILP (learning-from-failures) | MIT | Python CLI; needs SWI+clingo (present) | pip/git | active research | high | **Prototype (later)** — induce Rule-4 gates once ledger has dozens of labelled rows |
| **Aleph** | ILP (Progol-style) | GPL / academic | SWI pack | `pack_install(aleph)` | mature, less active | medium | Prototype (later) — alternative ILP, terse mode decls |
| **ILASP / FastLAS** | ILP over ASP | academic/free (non-OSI) | CLI, Python wrappers | binary download | medium | medium | Prototype (later); check license before public-repo use |
| **NuSMV** | symbolic CTL/LTL model checking | LGPL-2.1 | C; CLI (subprocess) | compile / binary | mature | medium | Compile-if-needed — OSS alternative to nuXmv |
| **Maude** | rewriting logic + LTL model-check | GPL-2.0 | C++; static binary + CLI | prebuilt binary (not in apt) | high (v3.5.1) | medium | Compile-if-needed — only to model-check the lifecycle |
| **MCMAS** | temporal-epistemic (CTLK) | open-source (academic) | C++/OBDD; ISPL CLI | compile (needs old `bison`, fiddly) | mature, niche | medium | Compile-if-needed — only when pre-registration must be machine-checked |
| **Konclude** | OWL 2 DL (tableau, fastest) | LGPL-3.0 / research | C++ binary | compile (heavy) or prebuilt | mature | low | Compile-if-needed — only if HermiT too slow |
| **TweetyProject** | structured argumentation (ASPIC+/DeLP) | LGPL-3.0 | Java; JVM jar | medium (no pip) | high (academic) | low | Heavy/ask-first — only for genuine attack-cycle semantics |
| **PSL** | probabilistic soft logic (hinge-loss) | Apache-2.0 | Java core + `pslpython` | JVM + pip wrapper | mature | medium | Heavy/ask-first — scale is irrelevant at autoharn's size |
| **SMCDEL** | symbolic dynamic epistemic logic (BDD) | GPL-2.0 | Haskell; CLI/web | compile (GHC/Stack), heavy | research | low | Heavy/ask-first — belief revision; overkill vs append-only ledger |
| **PyReason** ✓ | annotated many-valued/interval + temporal | BSD-3 | Python (numba) | pip **but Py 3.7–3.10 only** → separate venv | research 0.x | medium | Ask-first — version ceiling blocks the 3.13 venv; spike only for interval axis |
| **Celf / LolliMon** | CLF / linear logic | GPL-3.0 | Standard ML; CLI | compile (SML toolchain) | research, dormant | low | Reference only — CHR already gives consumption discipline |
| **nuXmv** ✓-flag | symbolic CTL/LTL (SMT, infinite-state) | **non-commercial binary only** | C; CLI | binary download | mature | low | **AVOID** — license incompatible with an open public CI repo |
| **DLV2 / I-DLV** | ASP | **free academic/non-profit only** | CLI; EmbASP | binary download | high | medium | **AVOID** — license friction for a public repo; use clingo instead |
| **pracmln** | Markov Logic Networks | BSD-2 | pure Python | pip | **unmaintained (~2018)** | low | **AVOID (abandoned)** — use ProbLog/PSL |
| **SPINdle** | defeasible logic | LGPL (research) | Java jar | medium | aging/inactive | low | Avoid unless full SDL needed |
| **llprover** | first-order linear-logic sequent prover | research/free | Prolog | compile; **needs non-free SICStus** | abandonware (1990s) | low | **AVOID (abandoned + non-free dep)** |
| **linTAP** | MELL tableau prover | research/free | Prolog | compile | abandonware (1990s) | low | **AVOID (abandoned)** |
| **MaGIC** | relevance matrix generator | free (ANU) | C | compile (rel. 2.1, **1995**) | dormant | low | **AVOID (abandoned)** |
| **FDE / Belnap eval (DIY)** | paraconsistent 4-valued | n/a (you write it) | SQL `CASE` / ~30 lines Python | none | n/a | high (truth tables) | **Adopt as pattern** — no prover exists worth running; encode `true/false/both/neither` in-store |
| **PyMC / pgmpy** | Bayesian / factor graphs (non-relational) | Apache-2.0 / MIT | Python | pip | mature | high | Fallback only — loses the logic layer |

## Install plan (three buckets, respecting "ask before obscure/disk-heavy")

### 1. Install now — cheap, high-leverage, already-present or one pip/pack
**Already usable (no action):** PostgreSQL `WITH RECURSIVE`; Z3 4.16; SWI-Prolog 9.3.31 with bundled `library(clpfd)` + `library(chr)`; clingo 5.8.0 + gringo (CLI); networkx, cvxpy, sympy, scipy, ortools; OpenJDK 25 (so any JVM reasoner runs out of the box).

**`pip` into `venvs/generic` (3.13) — all wheels/pure-py, Py 3.13-safe, trivial:**
- `clingo` — Python binding so ASP drives from the harness (CLI already present).
- `cvc5` 1.3.4 — second SMT engine for differential cross-checking against Z3 on shared SMT-LIB2.
- `clorm` — Postgres rows ↔ ASP facts.
- `janus-swi` — Prolog↔Python CI glue (compiles a small ext; C compiler + SWI present).
- `py-metric-temporal-logic` — real-time benchmark-timing monitors.
- `owlready2` 0.51 (HermiT bundled, JRE present) — **gate on a 3.13 import smoke-test first**; PyPI classifiers advertise only 3.6–3.10, though the core is largely pure-Python.

**One SWI command:** `pack_install(scasp)` for justification trees (decide alongside owlready2).

### 2. Prototype next — worth a focused spike before committing
- **Soufflé 2.5** (apt/compile) — same Datalog source as the Postgres prototypes; promote only hot gates.
- **Spot 2.15.1** (apt/compile) — LTL-with-past runtime monitors for pre-registration / no-resurrection / lifecycle-monotonicity; GPL-3.0 is fine for an open repo (note copyleft).
- **TLA+ / TLC** (download `tla2tools` jar, JRE present) — design-time model-check of the status protocol; mandate a deliberately-broken variant TLC must reject.
- **ProbLog 2.2.10** — only engine for the "statistical hunch vs provable truth" axis + ranked abduction; **spike in a Python-3.12 venv** (PyPI wheels list ≤3.12) before trusting on 3.13.
- **Popper / Aleph** (deps already present) — ILP to *induce* Rule-4 gates; defer real use until the ledger holds dozens of labelled rows. Induced rules enter as **provisional**, never auto-promoted.
- **ILASP / FastLAS** — ASP-based ILP; vet the (non-OSI) license before shipping in a public gate.

### 3. Compile-if-needed / heavy / ask-first
- **Maude** (prebuilt binary, GPL-2) — only to model-check the lifecycle as rewrite rules.
- **NuSMV** (LGPL, compile) — OSS CTL/LTL alternative if symbolic checking is wanted.
- **MCMAS** (compile, needs an old `bison`) — only when temporal-epistemic pre-registration must be machine-checked.
- **Konclude** (compile heavy / prebuilt) — only if HermiT is too slow on the capability TBox.
- **TweetyProject** (JVM jar), **SMCDEL** (Haskell/GHC/Stack, heavy), **PSL** (JVM + `pslpython`) — ask-first; each is JVM/Haskell-heavy and serves a need (full argumentation / dynamic epistemic / soft-logic-at-scale) autoharn does not yet have.
- **PyReason** (BSD-3, **Python 3.7–3.10 only**) — ask-first: requires a separate 3.10 venv (extra disk + isolated interpreter); research-grade 0.x.
- **Celf / LolliMon** (SML toolchain) — reference reading only; CHR already delivers the consumption discipline.

## Flags: abandoned or license-incompatible (open public repo)
- **License-incompatible with open CI:** **nuXmv** (non-commercial binary-only license) and **DLV2 / I-DLV** (free academic/non-profit only; commercial needs a license). Both have viable OSS substitutes already in plan — **NuSMV/Spot/TLA+** and **clingo** respectively. **ILASP/FastLAS** licenses are non-OSI "free for research" — vet before public-repo use.
- **Abandoned / unmaintained:** **pracmln** (last touched ~2018; use ProbLog/PSL); **llprover** (1990s, *and* needs non-free SICStus), **linTAP** (1990s), **MaGIC** (rel. 2.1, 1995) — the entire dedicated relevance/linear-prover tier is abandonware; encode FDE in ~30 lines instead. **SPINdle** is aging/inactive. **Celf/LolliMon** are dormant research code (compile only as reference).

## Web verification (June 2026, what I confirmed)
- **Z3** — `z3-solver` **4.16.0.0** (Feb 19 2026), **MIT**, pip; matches installed venv version. [PyPI](https://pypi.org/project/z3-solver/), [Z3 GitHub](https://github.com/Z3Prover/z3)
- **cvc5** — **1.3.4** (May 7 2026), **BSD-3-Clause**, `pip install cvc5` (C++/Python/Java bindings). [PyPI](https://pypi.org/project/cvc5/), [cvc5 GitHub](https://github.com/cvc5/cvc5)
- **clingo** — **5.8.0** (latest on PyPI, Apr 3 2025), **MIT**, `pip install clingo` (first-class Python). [PyPI](https://pypi.org/project/clingo/), [potassco/clingo releases](https://github.com/potassco/clingo/releases/)
- **Soufflé** — **2.5** (Mar), **UPL-1.0**, `.dl`/C++/CLI. [souffle releases](https://github.com/souffle-lang/souffle/releases), [LICENSE](https://github.com/souffle-lang/souffle/blob/master/licenses/SOUFFLE-UPL.txt)
- **Spot** — **2.15.1** (Apr 25 2026), **GPL-3.0**, first-class Python bindings. [spot.lre.epita.fr](https://spot.lre.epita.fr/)
- **SWI-Prolog** — installed **9.3.31**; latest stable line **10.0.x** (10.0.2 changelog), **BSD-2**; `janus-swi` on PyPI (CPython ≥3.6 + SWI ≥9.1.12 + C compiler). [versions](https://www.swi-prolog.org/versions.md), [janus-swi PyPI](https://pypi.org/project/janus-swi/)
- **ProbLog** — **2.2.10**, **Apache-2.0**; PyPI wheels advertised **≤Python 3.12** (3.13 unconfirmed → spike in 3.12 venv). [PyPI](https://pypi.org/project/problog/), [install docs](https://problog.readthedocs.io/en/latest/install.html)
- **Owlready2** — **0.51** (Jun 22 2026), **LGPL-3.0-or-later**; classifiers list **Python 3.6–3.10** only (verify 3.13 import). [PyPI](https://pypi.org/project/owlready2/)
- **Popper** — **MIT**, active main branch, `pip install git+https://github.com/logic-and-learning-lab/Popper@main` (needs SWI+clingo, both present). [Popper GitHub](https://github.com/logic-and-learning-lab/Popper)
- **PyReason** — **BSD-3**, confirmed **Python 3.7–3.10 only** (multi-core parallel only on 3.9/3.10) → cannot live in the 3.13 venv. [lab-v2/pyreason](https://github.com/lab-v2/pyreason)

Sources: [potassco/clingo](https://github.com/potassco/clingo/releases/), [clingo PyPI](https://pypi.org/project/clingo/), [cvc5 PyPI](https://pypi.org/project/cvc5/), [z3-solver PyPI](https://pypi.org/project/z3-solver/), [souffle releases](https://github.com/souffle-lang/souffle/releases), [Spot](https://spot.lre.epita.fr/), [SWI-Prolog versions](https://www.swi-prolog.org/versions.md), [janus-swi PyPI](https://pypi.org/project/janus-swi/), [problog PyPI](https://pypi.org/project/problog/), [owlready2 PyPI](https://pypi.org/project/owlready2/), [Popper](https://github.com/logic-and-learning-lab/Popper), [pyreason](https://github.com/lab-v2/pyreason)


---
*Verbatim output of the `autoharn-logics-investigation` workflow (run `wf_6be06f87-68d`, model claude-opus-4-8[1m]), 2026-06-27 — one expert agent per logic family, grounded in autoharn. The maintainer should treat engine version/license claims as agent-reported (web-checked where noted), worth a confirm before install.*
