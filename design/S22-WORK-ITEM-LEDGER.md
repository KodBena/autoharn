# S22 SPEC — the work-item ledger (work state as ledger-derived fact)

Status: DESIGN, Fable-authored (session be693afb, 2026-07-09), commissioned by the maintainer's
direct mandate this date ("we need an SQL ledger for work"). Supersedes the wait-for-evidence
posture of design/WORK-ITEM-DECISION-MEMO.md: the run-2 rows, mined by the detector pass of the
same date (rationalization-ledger finding_id 6's FINDINGS block), answered four of the memo's
five evidence questions, so v1 freezes on that evidence. Sonnet authors the DDL from this spec
in the s20/s21 house style and scratch-witnesses it; APPLYING to any deployment is the
maintainer's act (`bootstrap/apply-delta.sh`).

## Evidence the freeze rests on (witnessed, run3.ledger, 2026-07-09)

- Q1: agents decompose into flat SEQUENCES, not hierarchies (rows 2–6). v1 models a parent
  item with ordered children via deps; no general tree machinery.
- Q2: obligation granularity friction is real — one batch-scoped countersign_obligation was
  closed per-item across six review rows (22–27). v1 gives items identity so obligations can
  reference them exactly.
- Q4: status never left 'open' in 33/33 rows — v1's state vocabulary is open→closed only, no
  disposition churn machinery.
- Q5: the same decomposition was ledgered twice (rows 2–6 duplicated as 7–11) — item identity
  across dispatches is the live defect v1 must make unrepresentable-or-visible.
- Q3 (what the operator asks between sessions): genuinely unexercised; v1's views are the
  minimal set below, extended only on witnessed operator questions.

## The type answer (binding invariants; DDL author maps them to the actual s15+ lineage surface)

1. **SSOT — no work fact has a home outside the ledger.** Work items and their events are
   ledger acts (rows), not a parallel table universe. If the ledger's kind/edge vocabulary is
   CHECK-listed, this delta extends those lists; it adds NO base table that stores work state.
   Derived state lives in views only. (This kills the BACKLOG-prose tracking mode and the
   omega-style sibling store alike — the memo's option 2 rejection, now enforced by shape.)
2. **Item identity.** A work item is identified by a slug carried on its opening act; every
   later event on that item references it. Two opening acts with the same slug in one ledger
   are refused (the Q5 defect made unrepresentable) — or, if refusal is unachievable at the
   ledger's trigger layer without breaking append-only semantics, made VISIBLE as a violations
   row (never silent).
3. **Event vocabulary, closed:** opened(slug, title) · claimed(actor) · depends_on(slug) ·
   closed(resolution ∈ shipped|superseded|dropped|deferred, witness). Open ⇒ no resolution;
   closed ⇒ resolution + witness reference, where `shipped` REQUIRES a witness (commit hash /
   ledger row / artifact path) — omega's shipped-without-ship-ref invariant, which is run 1's
   uncommitted-deliverable lesson enforced.
4. **Derived views:** `work_item_current` (one row per slug: title, state, resolution, witness,
   claimant — latest-event semantics, explicit column list, never `l.*`) and
   `work_item_violations` (duplicate-open per invariant 2; shipped-without-witness;
   depends_on naming an unknown slug; dependency cycles via recursive CTE — the omega port).
   A violations view returning rows is the fail-loud signal; empty means clean, and the view
   must be provably runnable (its fixture witnesses a non-empty result).
5. **Grants mirror the ledger's own posture** (the s20 lesson: a mechanism the subject is
   meant to reach must be granted to the subject role). Append-only is inherited from the
   ledger itself — no new mutable surface exists to guard.
6. **Engine reach.** The violations logic is the SQL floor; a matching `.lp` layer over the
   same facts (deps cycles, shipped-without-witness) is part of this spec's scope so the
   differential (AGREE/DIVERGE) covers work items from birth. engine/lp semantics changes are
   authorized by THIS Fable-authored spec, per the standing rule.

## Closure statement

- Invariant: every consumer of work state derives it from ledger acts through the two named
  views; no second store, no BACKLOG-resident work tracking for governed projects.
- Universe: the kind/edge vocabulary lists this delta touches, the two views, the grants, and
  the .lp layer — enumerated by the DDL author by grepping the full lineage for kind/edge
  CHECK lists and every existing view that would join or shadow these; each covered or named
  not-covered with the reason.
- Denomination: "work item" here is dispatch-transcending work identity (the conformance
  instrument's scope items are dispatch-scoped claims ABOUT such items; same world, two
  granularities, names kept distinct on purpose).

## Witness protocol (Sonnet-executable, scratch pair in the toy db, both polarities)

(1) open→claim→close(shipped, witness) round trip; work_item_current shows each state.
(2) shipped WITHOUT witness refused (or violations-visible) — the negative control.
(3) duplicate open on one slug refused-or-violations-visible (the Q5 witness).
(4) depends_on cycle appears in work_item_violations; acyclic deps do not.
(5) SQL floor vs .lp differential runs AGREE on the probe's facts.
(6) All of the above via `led` where the vocabulary permits, raw psql where it does not —
    what `led` cannot yet speak is reported as the follow-up verb list, not silently wrapped.
