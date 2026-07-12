# review_gap scope semantics — answered by the maintainer's reframe

Audience: maintainer

STATUS: ANSWERED — NOT AS ASKED (2026-07-12). The maintainer's written answer (his
`~/q1_partial_response`, transcribed in full in "The maintainer's answer" below) rejected
this document's A/B binary as a framing error: review scope is a POLICY decision with a
deontic character (deontic: the vocabulary of permission and obligation), not a
yes/no on one join. The general vocabulary he called for now lives in
[ORCH-SPEC-RESOURCE-REGISTRY.md](ORCH-SPEC-RESOURCE-REGISTRY.md) §4 (obligation
attachment: principal | task_type | commission — his three enumerated cases, typed).
The kernel is UNCHANGED meanwhile: obligations still bind the whole principal, the
fail-safe over-catch stands, and this document's options A/B/C below are preserved as
the historical record of the question as it was first (badly) posed. Sections below the
answer are the original draft, preserved except this status block, the two new sections
that follow it, and three legibility repairs from the fresh-context audit (a
superseded-marker on the original entry-point heading, a MOOT banner on the final
question, and one acronym expansion).

## The maintainer's answer (2026-07-12, transcribed from ~/q1_partial_response)

His text, verbatim in substance: the question's framing makes it seem like second pairs
of eyes exist so "a *trainee* doesn't bungle the project." In reality a second pair of
eyes can be warranted in a variety of circumstances; it is a *policy* decision. His
examples: (1) a countersigner might conditionally state that the work being commissioned
must be reviewed by a second pair of eyes; (2) the trainee case — everything they do
needs a second pair of eyes ("for the Claude application case this is essentially a
non-sequitur because they're not trainees, but if you think about less capable models,
it may warrant a second pair of eyes"); (3) a specific type of task may require a second
pair of eyes. "Probably, there are others. There's a deontic smell to the entire
question." The system should lean toward general solutions; "in principle I would say
that the answer must be 'no' but only because of how the question is framed." And his
question back: what is the context and rationale — the history — for asking this
question in the first place; what specific problem does an answer to it solve?

## The history he asked for, and the problem an answer solves

Where the question came from: two paid episodes (run 5 and run 7, both detailed under
"The two paid episodes" below) in which an agent assumed `led obligate`'s scope word
filters which rows need countersign. It does not — the `review_gap` view joins on actor
identity alone, so an obligation catches EVERYTHING the principal writes. The draft
ruling was written to make that behavior official or commission filtering.

What a scope answer actually decides: **what `review_gap` lists** — the system's live
definition of outstanding review debt. That definition is load-bearing three times over:
it is what a run's reviewer passes must discharge, what the decomposition-review
execution blocker (tracker item `decomposition-review-blocker`, the maintainer's
2026-07-12 ruling) denies on, and what a closing pass must drain before a commission can
end. Run 12 (2026-07-12) then produced the definitive specimen of the blanket-principal
cost, unknown when this draft was written: because every row the author wrote became
debt — including the bookkeeping rows that merely *dispatched* reviewers — the run's
tail (its ledger rows 88–93) became reviewers countersigning the rows that dispatched
them, a regress the closing agent could only end by declaring the chain terminated as a
judgment call. Fail-safe, but ritual-shaped: review effort spent on rows whose content
is process bookkeeping. That specimen is the first witnessed *scope-shaped* (not
direction-shaped) cost, and it is exactly what the registry spec §4's typed attachment
vocabulary (task_type and commission attachments alongside blanket principal) exists to
relieve — its kernel stage remains gated on witnessed need, and run 12's tail is that
need's first data point, banked here for the next reader.

## The question in plain words (the original entry point, superseded above)

The kernel lets you place a principal under a countersign obligation
(`./led obligate <scope> <principal>`): from then on, every ledger row that principal
writes counts as unreviewed debt — listed by `./led review-gap` — until a DIFFERENT
actor attests it. When you create the obligation you type a scope word (e.g.
"decomposition"). Twice now an agent assumed that word FILTERS — that only rows about
the decomposition would need countersign. It does not, and cannot: ledger rows carry no
scope, so the kernel ignores the word except as a human-readable label, and the
obligation catches EVERYTHING the principal writes. The question below asks you to make
that behavior official (option A: scope is a label, the obligation binds the whole
person) or to commission real filtering (option B: kernel surgery that would make the
safety net catch fewer rows). Recommendation: A — both witnessed incidents were actually
caused by obliging the wrong person (the reviewer instead of the worker), not by the
missing filter, and over-catching errs toward more review, never less.

## What the kernel actually does today (re-verified 2026-07-11 at source)

`countersign_obligation` (kernel/lineage/s13-schema.sql:393-417, identical in s14,
untouched by s20 — s20's own comment lists review_gap as "not in this class"):

```sql
CREATE TABLE IF NOT EXISTS s13.countersign_obligation (
    scope         text PRIMARY KEY,
    assigned_by   bigint NOT NULL REFERENCES kernel.principal(id),
    obliges_actor bigint NOT NULL REFERENCES kernel.principal(id)
);
...
CREATE OR REPLACE VIEW s13.review_gap ... AS
SELECT l.id, l.actor, o.scope, o.assigned_by
FROM   s13.ledger l
JOIN   s13.countersign_obligation o ON o.obliges_actor = l.actor
WHERE  NOT EXISTS (... l superseded ...)
AND    NOT EXISTS (... distinct-actor attest review of l ...);
```

The join is on **actor identity alone**. The ledger table has no scope column, so
`scope` cannot filter anything: it is a human-readable label (and the row's PK), nothing
more. Once a principal is obliged, EVERY uncountersigned row that principal writes — any
kind, including their own later review rows — shows as debt until a distinct actor
attests it.

## The two paid episodes

- **Run 5 (BACKLOG 2026-07-10):** obligate direction/scope confusion cost a workaround
  round (first occurrence).
- **Run 7 (BACKLOG run-7 finding 1):** an obligation meant to cover the decomposition
  caught the REVIEWER's own countersign rows, forcing an author counter-countersign
  round. SoD (separation of duties) held; pairs stayed distinct; fail-safe direction
  both times. The root
  cause in both episodes was the DIRECTION mistake (obliging the reviewer instead of the
  worker), not a genuine need for scope filtering.

Already landed against the root cause (this session, sub-constitutional, text-only):
`led obligate`'s help and invocation-time teach-text now spell out the direction, the
label-not-filter nature of `<scope>`, the over-catch, and a worked example with its
consequence stated.

## The options, with costs

**A — Ratify current semantics as intended (RECOMMENDED).**
An obligation binds a PRINCIPAL: "everything this principal writes requires independent
eyes until attested." `scope` is a label. Direction discipline lives in the teach-text.
- Cost: zero code. The over-catch stands, but it is fail-safe, and with the direction
  taught correctly (oblige the worker, never the reviewer) the witnessed pain does not
  recur. A wrongly-obliged reviewer still costs one counter-countersign round — the
  system erring toward more review, never less.
- This converts "known over-catch, no ruling" into ratified semantics; the teach-text's
  caveat line then cites this ruling instead of "no maintainer ruling yet".

**B — True scope-filtered obligations.**
Requires giving ledger rows a queryable scope linkage (a new column or a refs
convention) AND rewriting `review_gap`'s join — a change to EXISTING view semantics that
can only ever catch FEWER rows. Not class-covered (it relaxes, not adds); needs a
Fable-authored or succession-ceremony spec, scratch witness, differential.
- Cost: a spec cycle plus a permanent narrowing of the safety net, bought to fix a pain
  whose actual cause was direction, not scope. Unwarranted on present evidence; becomes
  worth revisiting only if a run pays a scope-shaped (not direction-shaped) workaround.

**C — Exclude the obliged principal's own review-kind rows from the gap.**
REJECTED outright, both by rule and by shape: it relaxes a refusal (never class-covered)
and it opens an evasion channel — an obliged principal could launder any statement past
the gap by writing it as `kind=review`.

## The question (one, prepared, yes/no)

MOOT — superseded by the maintainer's answer above; preserved verbatim as the historical
record of the question's original framing. Do not act on the branches below.

**Ratify option A?** — "A countersign obligation binds the principal (all of their
rows, every kind); `scope` is a human-readable label, not a filter; the direction
discipline is carried by `led obligate`'s teach-text."

- **YES** → this file's status flips to RATIFIED (dated, maintainer-attributed), the
  teach-text's "no maintainer ruling yet" caveat is updated to cite it, and BACKLOG
  gets the disposition line. No kernel change, no delta, nothing to apply.
- **NO** → option B routes to the spec ceremony (Fable if available, else succession
  rules); nothing changes meanwhile and the fail-safe over-catch keeps standing.
