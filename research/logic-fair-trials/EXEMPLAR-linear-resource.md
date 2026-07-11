# Gold exemplar — Linear & Resource-aware Logic (non-deflated)

> Part of the autoharn **logic fair-trials** (the corrected, frontier-creed pass). Coined terms → root **[GLOSSARY.md](../../GLOSSARY.md)**. The honest status of every verdict here is **undecided-until-the-experiment-runs** — see [README](README.md) and [AUDIT.md](AUDIT.md).

## Linear & Resource-aware Logic — Fair Trial (GOLD EXEMPLAR, hand-authored)

> This section is **hand-authored by the maintainer + assistant**, not agent output. It exists because the
> first-pass `09-linear-resource` trial *deflated* — it conceded the discipline to a `UNIQUE(reading_id)`
> ("elegant, but Postgres does it with a constraint — I will not pretend otherwise") and the audit pass let
> it through. This is the same question answered **without** the retreat, as the reference for what a
> non-deflated trial looks like. Coined terms → root [GLOSSARY.md](../../GLOSSARY.md).

**The bet:** ledger discharge is a *resource* protocol — readings are consumed to discharge claims — and an
affine/linear discipline captures the whole protocol *as one rule-set*, where SQL needs a new constraint per
shape (a Rule-4 instance-net) and falls apart under concurrency.

## Maximal ambition

One declarative **resource calculus** over the ledger in which readings, corroboration budgets, and claims
are typed resources, and *every* discharge shape — single, partial, quorum, transforming, concurrent — is a
rule in the same calculus, with an automatically-derived **spend-trace** as a first-class provenance object
(*which* readings discharged *which* claim, consumed in *what* order). The summit: discharge becomes
**proof-carrying** — a confirmed claim ships the linear derivation that consumed its evidence, and
double-spending is not "caught," it is **unrepresentable** because the context has no second copy of the
token to consume.

## The expressiveness gap — the HARDEST cases, not single-spend

Single-spend (one reading → one claim) is the toy; it reduces to `UNIQUE`. The protocol's real shapes do not:

1. **Partial / budget consumption.** A reading is a *budget* of N corroborations; each claim draws it down;
   the gate must forbid the (N+1)-th. SQL: a counter column + a `CHECK (drawn <= N)` + a trigger to
   increment under the right isolation — three artifacts, and a different three for the next budgeted
   resource. CHR: one rule.
   ```prolog
   draw @ budget(R,N), claim_needs(C,R) <=> N > 0 | N1 is N-1, budget(R,N1), discharged(C,R).
   ```
2. **Quorum consumption.** A claim needs *k distinct* readings consumed **atomically** (corroboration). In
   SQL this is a `HAVING count(*) >= k` plus a guard against two claims racing for the same overlapping
   readings — not expressible as a single constraint. In linear logic it is one tensor of k resources in the
   rule body; the `<=>` consumes all k or none.
3. **Transforming consumption (a reborrow).** Discharging consumes readings **and produces** a *derived*
   reading (a meta-analysis whose own provenance is the consumed set). That is a borrow that returns a new
   borrow — exactly Rust's reborrow. SQL has no notion of "this row's existence consumed those rows"; you
   bolt on FKs + triggers and lose the invariant-as-one-statement.
4. **Concurrent commit.** Two sessions race to discharge against the same reading. Linearity makes the
   double-spend **structurally impossible** — the resource is in the context once. SQL needs `SERIALIZABLE`
   isolation *or* advisory locks *or* a unique partial index, **and** the right one differs per shape — an
   enumeration of instances, i.e. the [Rule 4](../../GLOSSARY.md#class-not-instance-net) violation the
   project forbids.

The decisive point is **trajectory, not snapshot** (the maintainer's ResNet-in-assembler argument): at one
shape, `UNIQUE` wins on familiarity. At four interacting shapes under concurrency, the SQL formulation is a
constraint/trigger thicket whose correctness no longer reads as a single invariant — and **the industrial
existence proof already exists.** Rust's borrow checker *is* affine logic + regions; when the hand-written
checker (NLL) hit exactly this wall, the frontier moved to **Polonius — the borrow checker reformulated as
Datalog**, run on the `datafrog` engine, because the imperative version's cost curve went vertical. The
resource discipline at scale became a logic in production. "Postgres does it with a constraint" is "implement
the borrow checker in SQL."

## The falsifiable experiment (the trial)

**Setup.** Instrument the real discharge protocol. Export `reading/3`, `claim/2`, `budget/2`,
`needs/2` (claim → required readings, with multiplicity). Encode the four shapes above in **SWI-Prolog
`library(chr)`** (installed) as ONE rule-set; in parallel, encode the *same* protocol as a Polonius-style
**Datalog** loan-analysis (clingo, installed) over discharge *events* (location-sensitive: a discharge is
valid at an event point iff the reading is live and unspent on every path to it).

**Success criterion.** (a) The single CHR/Datalog rule-set expresses all four shapes with no per-shape
constraint; (b) it flags a concurrent double-spend and an over-budget draw that a side-by-side SQL schema
either misses or needs ≥3 added constraints to catch; (c) the spend-trace is emitted as a reading-with-
provenance the maintainer can audit.

**KILL CONDITION (non-negotiable).** Retire resource logic here if, instrumented over one month of the real
protocol, **only single-spend ever occurs** — no budgets, no quorum, no transform, strictly one writer per
reading — *and* the SQL `UNIQUE` formulation catches every observed violation. Then the affine machinery is
genuinely unneeded and this is an **honest ash**, established by a search, not assumed.

## Neutralizing false authority (verification scaffolding)

- **Mutation fixtures:** a hand-built double-spend and an over-budget draw that the gate **must** light up;
  a gate that can't fail on its own mutant is dead.
- **Differential:** the CHR rule-set and the Polonius-style Datalog encoding must agree on every discharge;
  disagreement is an encoding alarm, not a green check.
- **Back-translation:** each rule carries an English gloss reviewed by the maintainer; the rule+gloss is the
  audited artifact.
- **Encoding-as-reading:** the rule-set is stored under `{commit, tree, session_id}` and is itself subject
  to the meta-sweep — the encoding is evidence, not authority.

## Verdict: phoenix or ash — and how we'll know

**Undecided-until-run, leaning phoenix** — and explicitly *not* "use a `UNIQUE` instead." The lean is earned
by the structural argument (four irreducible shapes + the concurrency impossibility + the Polonius existence
proof) and is falsifiable by the kill condition above. The single settling experiment: **instrument the real
discharge protocol for one month; if any non-single-spend shape appears even once, the resource calculus
captures the class that SQL must enumerate, and it is phoenix.** If the protocol is forever single-writer
single-spend, it is ash — honestly, by search. What it is *not* is "elegant but redundant," which was the
first pass's deflation, and which the borrow checker's own history refutes.

---
*Hand-authored exemplar (maintainer + assistant, claude-opus-4-8[1m]), 2026-06-27. Written to replace the
deflated first-pass `09-linear-resource` trial as the reference for a non-deflated fair trial. Draws on the
Rust borrow-checker / Polonius discussion in the session. The original deflated trial is preserved verbatim
as `09-linear-resource.md` (the Witness); this is the Correction.*
