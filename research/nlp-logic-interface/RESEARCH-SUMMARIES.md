# RESEARCH-SUMMARIES — the four 2026-06-27 corpora + the reified-boundaries search

Faithful, one-page-each summaries of the four research corpora under
`docs/research/2026-06-27-*`, produced as evidence for the NLP↔logic interface
commissioning. Each corpus is reported (QUESTIONS / METHOD / CONCLUSIONS), not
re-litigated. A final section resolves the maintainer's half-remembered
"reifying-abstract-boundaries" remark.

**Coined terms, legible on first use.**
- **deflation** — the failure mode where an investigation retreats to the familiar tool
  (SQL, a script) while dressing the retreat as honesty; the fair-trials corpus audits
  itself for it.
- **false authority / encoding-trust gap** — an LLM mis-encoding a rule produces a
  *confidently green* gate that is wrong; the recurring cross-corpus risk, said to "bottom
  out in human judgment".
- **obligation** — a unit of what auditable software owes (e.g. ATTR = attribution,
  COMMIT = commitment, INDEP = independence), used by the obligations survey as the
  organizing axis *instead of* the logic family.
- **differential solving** — qualifying an encoding by running two independent
  implementations and comparing (the same mechanical gate the shipped `contra_asp` /
  `fde_z3` code implements).

---

## 1. `2026-06-27-foundational-map/`

**QUESTIONS.** What existing conventions in the `chocofarm` and `omega` repos should a
proposed "harness" (autoharn) grow *out of* rather than override? Specifically: what does
the Mechanization-Discipline ADR (0011) require in each repo; which disciplines are
already mechanized vs merely review-policed; what SQL/lint machinery already exists
(omega's work-status Postgres layer, five lint gates); how are benchmark/perf claims
attributed today; how are resource/capability facts surfaced to an agent; and what
tool/solver capability (Z3, OR-Tools, cvxpy, …) exists but goes undiscovered.

**METHOD.** Nine of twelve reports are verbatim structured output from a 10-reader
parallel agent workflow (`wf_64eb31fd-6c9`), each citing `file:line`; report 10 was
hand-authored after its reader exceeded its retry cap; report 00 synthesizes. Sources:
both repos' ADRs (0000, 0008, 0009, 0011, 0013, 0014), omega's `schema.sql`/lint gates,
chocofarm's `exp_db.py`/`code_stamp.py`, git history, gitignored resource-fact files, and
a verified-import census of the shared venv.

**CONCLUSIONS.** ADR-0011 exists in forked, divergent form (omega: 5 rules/7 rungs;
chocofarm: 4 rules/5 rungs), each explicitly disclaiming self-mechanization (chocofarm:
"no automated enforcement of this tenet itself; it is review-and-audit-policed"). Both
repos hold partial, unconnected prototypes of capability/provenance and lint-gate
patterns. Established gap: perf-claim numbers in commit bodies are hand-typed prose
"machine-linked to NOTHING," and no Claude session-id column exists anywhere. **Left
open:** eight explicit maintainer decisions (shared vs per-project DB, vocabulary
reconciliation, session_id sourcing, DIRTY-tree policy, clingo/Soufflé adoption, repo
placement, gate-vs-advisory default, measure-first baselines) and an unexecuted 8-step
sequencing plan.

---

## 2. `2026-06-27-logic-fair-trials/`

**QUESTIONS.** Can ~60 years of non-classical logic be made "industrially load-bearing"
for autoharn now that an LLM can pay the formalization cost? For each of 14 logics: is
there a precise, non-hand-wavy expressiveness gap versus SQL/plain scripts/Z3, and does
that gap bite on autoharn's real data? Second-order: can the investigation itself avoid
**deflation**?

**METHOD.** Each logic run through a fixed "fair trial" template (maximal ambition;
precise expressiveness-gap statement; one falsifiable experiment with a class-level kill
condition; false-authority verification scaffolding), followed by an adversarial deflation
audit and a re-synthesis into a research program (E0–E7). One trial (linear/resource) was
hand-authored as a gold exemplar.

**CONCLUSIONS.** Every verdict is explicitly **undecided-until-run** — no logic was
empirically confirmed or retired; only designs were produced. The one *settled* finding is
a process one: the adversarial hardening pass was a no-op (0/14 trials rewritten, every
auditor said `deflated=false`), yet the audit's own notes contradict that verdict in 7/14
cases, and the synthesis then falsely claimed deflation had been "hardened out" — a third
instance of the very false-authority failure under investigation. **Left open:** running
the experiments; five maintainer-only forks (concurrency reality, contradiction-tolerance
policy, ILP budget, auditability/latency thresholds, hard-gate vs advisory); five named,
unmeasured risks. This directory is marked **superseded** by the obligations survey. (This
corpus is the one the shipped code cites as `AUDIT.md`'s "deflation lesson" — the mandate
that a correctness gate be mechanical, not a model's judgement.)

---

## 3. `2026-06-27-logic-investigation/`

**QUESTIONS.** Do logics / automated-deduction tools have genuine applicability to
autoharn's three Pillars (classification, provenance, CI-logic safety-net), and what
open-source software implements each family? Thesis: "extended/non-classical logic +
automated deduction, now authored-by-LLM, concretely improves LLM-based project
management."

**METHOD.** 13 parallel per-family reports (`wf_6be06f87-68d`, each primer / applicability
/ software table / honest-limits), a 14th hand-commissioned report (probabilistic
programming), an adversarial "fit-critic" report (B, a coverage matrix), a
software-landscape catalog with install plan (A), and a synthesis (00). Local tools
probed; license claims web-checked.

**CONCLUSIONS.** The thesis holds only in **reduced form** — justified only where the
invariant is genuinely non-classical *and* a cheap deterministic SQL view does not already
express it; under that filter most Pillar-2 provenance and much of Pillar-1 is "a SQL
job," and exotic logic there is "net-negative." The load-bearing core is small:
Datalog/Postgres recursion, ASP/clingo for non-monotonic supersession, CHR for consumption
discipline, Z3 for consistency gates. Convergent finding: **false authority** is the
dominant risk. One first experiment (abductive ASP for regression-hypothesis generation)
was specified, not run. **Left open:** ProbLog venv-cost tradeoff, clingo/Soufflé adoption
timing, license policy, and (report B) the **encoding-trust gap** that no logic family
closes and that "bottoms out in human judgment" — called "the honest ceiling on the whole
enterprise." Marked **superseded/corrected**. (This corpus is the one the shipped code
cites as `B-autoharn-fit` — the source of "ASP earns its keep over the SQL floor" for the
defeasible R-FUNC and the minimal-repair `#minimize`.)

---

## 4. `2026-06-27-obligations-formalisms-survey/`

**QUESTIONS.** Can non-classical / "merely philosophical" logic (deontic, epistemic,
justification, provability, STIT, defeasible, paraconsistent, substructural,
temporal-metric, counterfactual-causal, hyperintensional, …) be made industrially
load-bearing for extreme auditability of AI-assisted, life-critical software? Organized by
a taxonomy of 17→19 **obligations** rather than by logic: for each, which formalism's
semantics matches its failure mode, is it automatable today, and how is an LLM-authored
encoding *qualified* rather than merely trusted?

**METHOD.** Four verbatim-workflow layers (`wf_2b657cd5-b06`, 38 agents): (1) the
obligation taxonomy (WHAT / FAILURE MODE / EXAMPLE); (2) 27 per-formal-system trials, each
with primer, "obligations it discharges" (+ explicit "does NOT serve" boundaries), a
runnable encoding, tool/license verification, and a falsifiable kill-condition; (3)
cross-cutting analyses — automation/encoding-host (A); composition architecture (B: a
single append-only claim ledger + a justification-logic spine + a guarantee-strength meet +
a Gödel–Löb self-audit guardrail); a DO-178C-style qualification discipline (C, QUAL-0–10,
using **differential solving**, mutation/golden fixtures, back-translation,
provenance-covered reading); and a coverage/completeness matrix with an adversarial critic
(D); (4) a master synthesis.

**CONCLUSIONS.** Thesis "confirmed, but with a precisely bounded scope": ~20/27 formal
systems run today with zero new dependencies (Z3, clingo, SWI-Prolog, OR-Tools, Postgres,
JAX/NumPyro); different obligations genuinely need different semantics (DEGRADE has no
meaning outside dyadic deontic logic; ATTR is Halpern–Pearl causation specifically); the
composition layer is presented as the novel artifact that makes self-certification "a
structural impossibility." All verdicts are labeled **agent-reasoned, not yet
experimentally settled**. **Left open:** COMMIT is "the weakest-covered obligation";
WCET/hard-real-time bounds undischarged; cryptographic/distributed RECORD has no owning
formalism; ATTR is "covered but not qualifiable" (risk of "unfalsifiable theater");
confidentiality/information-flow and hyperproperties are absent from the roster; six
maintainer decisions posed; a proposed first experiment (≥50 LLM-authored encodings with
seeded pathologies, to test whether the qualification discipline catches injected faults)
is named as unexecuted. (This corpus is the one the shipped `fde_z3.py` / `logic_layer.lp`
cite as `25-paraconsistent-manyvalued.md` — the verified two-bit FDE/Belnap Z3 encoding,
and the CONSIST obligation the paraconsistent glut discharges.)

---

## The "reifying abstract boundaries" remark — located or confirmed absent

**Finding: the remembered remark is ABSENT from all four corpora.** An exhaustive,
iterative grep sweep across all 63 files (including the `formal-systems/` subdirectory)
covered every variant of the phrasing: `reif` / `reified` / `reifying` / `reification`;
`boundary` / `boundaries`; `discharge(d/s)` (a very common section-header term — "obligations
it discharges"); `work unit` / `unit of work`; `first-class` / `first class`; `audit`
(broad, and combined with entity/object-language); and formulations like "as a
separate/distinct entity/object" and "abstract boundary/boundaries". No file contains
"reifying abstract boundaries," "work unit and discharge as separate first-class
entities," or an equivalent formulation.

**The three nearest conceptual neighbors (verbatim quotes + paths), each distinct from the
remembered remark:**

1. On the **COMMIT** obligation — tracking one commitment's *lifecycle* as a single
   object (not work-and-discharge as two reified entities):
   > "[COMMIT] is the **thinnest-covered** obligation — no surveyed system tracks the full
   > commitment lifecycle (created→active→discharged→delegated→cancelled→violated with
   > creditor entitlement) as one object …"
   `docs/research/2026-06-27-obligations-formalisms-survey/00-synthesis.md:95`

2. On distinct justification *witnesses* as an object-level fact (about justification
   terms, not work units):
   > "… an [INDEP] cross-channel rule that must assert 'two *distinct, separately-checking*
   > justifications exist' as an object-level fact."
   `docs/research/2026-06-27-obligations-formalisms-survey/formal-systems/17-justification-logic.md:82`

3. The closest *auditability-via-reified-state* mechanism in the corpus — an
   `audit_log` + trigger + `table_asof()` row-level history pattern (git-correlated,
   actor-attributed time-travel), but about **row-level history**, not "work units and
   their discharges" as separate first-class entities:
   `docs/research/2026-06-27-foundational-map/06-omega-work-status-sql-anti-corruption-layer.md`
   (see also `08-cross-benchmark-attribution-today.md`, `09-cross-memories-and-resource-facts.md`).

Additional near-uses of "reify/reified" that are *not* the remark: truth-values reified as
a `suspect`/`confirmed`/`retracted` enum, and deduction reified as a theory — in
`2026-06-27-logic-fair-trials/08-description-logic.md:17`,
`2026-06-27-logic-investigation/01-datalog.md:69`, and `…/11-smt-fol.md:51`.

**Disposition.** The remark the maintainer recalls is either from a document/session
*outside* these four directories, or is a paraphrase/composite of the COMMIT-lifecycle
"as one object" discussion (neighbor 1) and the `audit_log`/provenance-ledger pattern
(neighbor 3). It is not a verbatim passage in this corpus set. (Confirmed by direct
re-read of the two load-bearing quotes above at the cited lines.)
