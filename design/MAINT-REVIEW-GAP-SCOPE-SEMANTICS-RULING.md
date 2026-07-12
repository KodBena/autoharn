# review_gap scope semantics — DRAFT ruling for the maintainer

Audience: maintainer

STATUS: DRAFT — AWAITING MAINTAINER'S WORD (2026-07-11). Queued as item (a) of
HANDOFF.md's "Maintainer's morning batch" open-work entry (cited by name, not position —
an earlier revision of this line cited "HANDOFF open-work item 2," a pointer into a
superseded HANDOFF revision that by the time it was read pointed at unrelated work; a
positional cite into a doc that gets rewritten each session is a dangling pointer waiting
to happen, so this one is by name). An agent may draft a ruling; it may never file one as
made. Nothing changes until the maintainer answers the one question at the end.

## The question in plain words (read this first)

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
  round. SoD held; pairs stayed distinct; fail-safe direction both times. The root
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

**Ratify option A?** — "A countersign obligation binds the principal (all of their
rows, every kind); `scope` is a human-readable label, not a filter; the direction
discipline is carried by `led obligate`'s teach-text."

- **YES** → this file's status flips to RATIFIED (dated, maintainer-attributed), the
  teach-text's "no maintainer ruling yet" caveat is updated to cite it, and BACKLOG
  gets the disposition line. No kernel change, no delta, nothing to apply.
- **NO** → option B routes to the spec ceremony (Fable if available, else succession
  rules); nothing changes meanwhile and the fail-safe over-catch keeps standing.
