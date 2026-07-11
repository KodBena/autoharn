# Logic-discipline coverage — status map (2026-07-11)

Answering the maintainer's question: what logic disciplines does our work cover, how many
are missing, which are inapplicable? Grounded in a full-corpus survey (night shift,
2026-07-11) over research/logic-investigation/ (retracted), research/logic-fair-trials/
(14 trials, superseded, every verdict undecided-until-run), and
research/obligations-formalisms-survey/ (27 systems, the settled frame), checked against
what engine/lp/ + the kernel actually run. Citations live in those docs; this is the
status condensation. Supersedes nothing; a later survey pass supersedes this.

## Running in production semantics today (the covered set, ~10)

1. **Classical relational (SQL floor)** — every kernel view; engine/ledger_floor.py.
2. **Datalog** — as ASP's stratified fragment + Postgres WITH RECURSIVE; PROV/TRACE's
   normal form.
3. **ASP / stable-model with NAF** — engine/lp/*.lp, six programs, differential-married
   bit-identically to the SQL floor (the project's raison d'être, live since the first
   AGREE).
4. **Defeasible / non-monotonic (the classics' working core)** — supersession closure,
   clause-defeat, NAF seams throughout the .lp files.
5. **Deontic, via the Anderson reduction** — obligation = recorded other-assigned fact
   (countersign_obligation), violation = derived flag (review_gap,
   work_item_violations). Deliberately NO modal O/P/F operators — a position that
   survived a dedicated adversarial refutation pass.
6. **Temporal, as the T_event/T_now two-theory split** — id-is-order-never-ts
   (ledger_tnow.lp); assumption validity bounds (ledger_assumes.lp, with the known
   now-not-hash-pinned replay defect on file).
7. **Paraconsistency, as posture** — zero integrity constraints in the .lp corpus (the
   record stays satisfiable; contradiction is data), FDE/Belnap as a report-side lens
   only; the quotational stance dissolves kernel-level paraconsistency.
8. **Optimization-as-logic** — #minimize minimal-repair probes (provably beyond a SQL
   view); cvxpy/or-tools precedents live in chocofarm.
9. **SMT (z3)** — quantity + unsat-core lanes; the k-parameterized SoD UNSAT sweep
   (instruments/core_a.lp) partially discharges the maintainer's min-unsat-core concern.
10. **Type theory as foundation** — ADR-0000's illegal-states-unrepresentable, the frozen
    verdict vocabularies, the five-component judgment type.

## Investigated, not built (the corpus's own verdicts stand)

TLA+/model checking (phoenix IFF concurrent writers exist — an architecture fact only
the maintainer decides); abduction (runnable demo; NOTE: silently lost its standalone
slot between the 14-trial and 27-system passes — flagged, since silently-dropped is this
project's least favorite state); ILP (candidate-generator only, data-gated); description
logic (narrow TBox home; OWA gives nothing without disjointness); epistemic/DEL and
alethic/modal (the maintainer pre-flagged both "probably specious" — the corpus
corroborated him on both); argumentation theory (rejected for the kernel: "a second,
un-ratified law register"); AGM belief revision; separation/linear logic (industrially
strong, open — the borrow-checker EXEMPLAR is the fair-trials' gold standard);
HOL/proof assistants (small catastrophic cores only); μ-calculus; STIT ("unfalsifiable
theater" risk); Halpern-Pearl causal (the only formalism distinguishing rubber-stamp
from supervision — open, benchmark-gated); probabilistic logic (graded verdicts rejected
outright: "a graded verdict is a boolean that learned to mumble"; MLN tooling dead).

## Missing — named by the corpus itself, nothing implements

Ranked by the survey's own coverage report: **abstract interpretation** ("the single
most damaging omission"), **runtime verification as a discipline**, differential dynamic
logic / hybrid systems, probabilistic model checking (PRISM/Storm), commitment
protocols / session types, auto-active verifiers (Dafny/SPARK), reactive synthesis.
Obligations with no strong discharger: COMMIT (weakest-covered), the cryptographic half
of RECORD (tamper-evident happens-before — no logic family owns it),
**hyperproperties/2-safety** (verifier independence is itself a relation over trace-sets
no single-trace formalism expresses — "the deeper structural miss"). Never even named:
GLP, full ATL/coalition logic, process calculi as distinct from TLA+, relevant logic
proper, categorical/topos logic, quantum logic.

## Inapplicable — with the honesty that "absolutely impossible" is a strong word

Nothing is impossible in principle; three honest tiers:

- **Rejected with reasons that survived adversarial refutation** (the settled no's):
  Kripke/LTL temporal-modal layer (the record is not a trace of world states; runtime
  LTL "ash by Kamp's theorem" absent concurrent writers); modal deontic operators (the
  Anderson reduction does the work); kernel-level paraconsistency (quotational stance).
- **Inapplicable by domain fact**: WCET/hard-real-time logics (a decision ledger makes
  no timing claim — declared exclusion in the BRIEF conformance map, F14); hybrid
  systems/dL (no continuous dynamics anywhere in the subject); quantum logic.
- **Ash by the corpus's own adjudication** (cheaper substitutes exist): justification
  logic (Datalog why-provenance, equal strength), truthmaker/grounding (collapses to
  graph acyclicity), fuzzy-for-calibration ("CALIB's own failure mode reborn one level
  up"), dialetheism-as-philosophy (the value lattice survives, the metaphysics is ash).

## The two standing methodological axioms (worth restating anywhere this map travels)

No LLM-as-judge in any verdict path; and licensing/maintenance is a separate verdict
axis (dead tooling disqualifies a live semantics — the MLN lesson). The residual even
perfect coverage cannot buy: "a wrong human axiom still passes" — fixture-adjudication
quality is measured, never assumed.
