# FABLE-BOOKKEEPING-CLOSE-SPEC — a third, machine-verified close constructor (s38)

**What this document is.** The Fable-authored, maintainer-ratified specification required
to loosen s29 Element B (`kernel/lineage/s29-obligation-item-key-and-typed-close.sql`),
which today makes every `led work close` carry exactly one of two review dispositions —
`witnessed` (a review exists) or `deferred` (the close itself becomes review debt). This
spec adds a third disposition, `bookkeeping`, for closes with no judgment content, under a
machine-checked predicate. It is written for the executor (Sonnet) who builds it and for
any later auditor asking why a review-silent-looking close was ever allowed to exist.

**Ratification.** Maintainer, 2026-07-17, choosing option (b) of
`design/MAINT-DECISION-QUEUE-2026-07-17.md` Q1; the verbatim ratification and the
orchestrator's stated grounds are in the ledger (durable-graded decision row of the same
date). Because this loosens an existing refusal it is OUTSIDE the class-ratified fail-safe
lane by definition; this document plus that row are the required ceremony.

**Why loosen at all.** The panel deployment's git-transaction pairing convention (its
ledger rows 407/408) manufactures work items whose entire close content is "the commit
landed, here is its hash." Forcing `witnessed`/`deferred` onto those closes produces
either review-gap debt with nothing to review, or boilerplate countersigns — the
content-free-review failure shape `design/USER-RECIPES-FAQ.md`'s Review Discipline section
already names. Rubber stamps are not neutral: each one trains every reader that
countersigns are sometimes noise, which erodes the reviews that matter. The disciplined
fix is a typed distinction, not a stretched ceremony: the close KIND says whether there
was judgment, and the "no judgment" claim is checked by machine, never asserted by the
operator.

## The category is CLOSED (the creep guard)

v1 `bookkeeping` admits exactly ONE form: a close whose witness is a git commit that
verifiably exists in the world's own repository. Nothing else — no artifact paths, no
URLs, no ledger-row references, no free text — is admissible, even where those feel
morally equivalent. Widening the category requires a new Fable-authored, maintainer-
ratified spec; an executor extending it under any other authority is an ADR-0013
violation. The reason for the hard line: "bookkeeping" is exactly the label that judgment-
bearing closes will drift toward if drift is representable, and the commit-existence form
is the one whose truth a machine can actually check today.

## Element 1 — kernel delta `s38-bookkeeping-close.sql`

- Widen the vocabulary CHECK `work_review_disposition_check` to
  `('witnessed','deferred','bookkeeping')`. This is THE loosening this spec ratifies;
  everything else below narrows it back down.
- New shape CHECK `work_review_bookkeeping_requires_commit_ref`:
  `work_review_disposition IS DISTINCT FROM 'bookkeeping' OR work_review_ref ~
  '^commit:[0-9a-f]{7,40}$'` — a bookkeeping row without a commit-shaped review ref is
  unrepresentable, mirroring `work_review_witnessed_requires_ref`'s pattern one clause over.
- `validate_work_item()`'s mandatory-disposition arm accepts the third constructor;
  its strict-close arm keeps refusing it (see Element 2 — `--strict` demands `witnessed`,
  unchanged).
- The two places that quantify review debt over close dispositions are UNTOUCHED and must
  be VERIFIED to stay correct under the widened vocabulary: `work_review_gap`'s WHERE
  clause (`work_review_disposition = 'deferred'`, s29 Element A as re-issued through
  s32/s37) and the deferred-close filter inside `work_item_strict_blockers()` (the
  `disp = 'deferred'` CTE predicate in the same s29 file). Both select `'deferred'` by
  equality, so `'bookkeeping'` creates no review debt in either — that is the point,
  stated here plainly rather than left as an implication, and the executor's witness plan
  checks both, not just the view. (`review_gap`, the actor-keyed countersign view, has no
  work-close arm and is unaffected.)
- New audit projection `work_bookkeeping_closes` (a view over `ledger`, not
  `ledger_current` — record semantics, everything forever, like s37's
  `work_violation_history`): slug, close id, actor, review ref, closed-at. Every use of
  the escape hatch is enumerable in one query, so the category's growth rate is itself an
  auditable fact. This view is the mechanism that keeps Element 1 honest under ADR-0013
  Rule 3: the ceremony is removed only where a machine check replaces it, and the removals
  are permanently visible.
- Header carries the formal `HISTORY: safe` line (vocabulary widening + new CHECK
  narrowing only the new value + new view: existing rows and existing constructors are
  byte-for-byte unaffected; grounds: re-issue-only / additive-vocabulary). Detect sibling
  fingerprints behavior (the widened vocabulary and the new CHECK), never a pinned name,
  per the s29/s30 detect ruling of 2026-07-16.

## Element 2 — CLI constructor in `bootstrap/templates/led.tmpl`

`led work close <slug> <verdict> --review-bookkeeping --witness commit:<sha>`:

- `--review-bookkeeping` takes no argument. The CLI derives `work_review_ref` from the
  mandatory `--witness commit:<sha>` after BOTH machine checks pass: (1) the witness
  matches the commit-shape regex; (2) `git cat-file -e <sha>^{commit}` succeeds against
  the world root's repository. Either failure refuses with a teach-text naming the failed
  check and the two honest alternatives (`--review-witness`, `--review-deferred`).
- Refused combinations, each with its own teach-text: with `--review-witness` or
  `--review-deferred` (one constructor per close, s29's own rule); with `--strict`
  (strict demands a witnessed review — a strict bookkeeping close is a contradiction,
  same footing as the existing `--review-deferred --strict` refusal at led.tmpl:1432).
- The existing refusal text ("a review-silent close is unrepresentable") stays true and
  stays put: a close naming NO constructor is still refused; the teach-text gains one line
  naming the third constructor and its narrow admission condition.

## Element 3 — the honest trust boundary (ADR-0011)

The kernel enforces SHAPE (commit-form ref, vocabulary, non-null); commit EXISTENCE is
checked CLI-side at construction only. A hand-issued INSERT could therefore cite a
nonexistent commit — the same boundary every CLI-side check in this project already has,
and the standing no-raw-writes instruction is the (social) control for it. The spec
declines to pretend otherwise; `work_bookkeeping_closes` gives auditors the row set to
spot-check against the repository, which is the strongest honest claim available.

## Closure statement (ADR-0000 Rule 2(a) — enumerated universe)

Quantification universe: the three constructors of `work_review_disposition` on a
`work_closed` row — `witnessed`, `deferred`, `bookkeeping` — plus the refusal (no
constructor). For every row reaching the ledger through the CLI: `witnessed` carries a
non-empty review ref (s29 CHECK, unchanged); `deferred` enters review-gap debt (s29 view,
unchanged); `bookkeeping` carries a commit-shaped ref (new CHECK) whose commit existed in
the world repository at construction (CLI check) and appears in `work_bookkeeping_closes`
(new view); no-constructor is refused (s29 trigger, unchanged). No fourth value is
representable (vocabulary CHECK); no bookkeeping row without a commit-shaped ref is
representable (new CHECK); review-gap debt quantifies over `deferred` only, before and
after. Witness plan: scratch schema, both polarities (construct-succeeds with a real
commit and appears in the view creating no review debt; refused on nonexistent commit, on
malformed witness, on each forbidden flag combination), detect sibling both polarities,
and the SQL/ASP differential (`./judge`) in AGREE — the executor checks whether the
engine's work-layer rules enumerate disposition vocabulary and extends them in the same
change if so.

## Sequencing note for the executor

This change touches `led.tmpl`; it builds only after the `build/effective-state-display`
branch (in independent review at the time of writing) has merged, and rebases on whatever
`led.tmpl` then looks like. Birth-chain wiring (`bootstrap/new-project.sh`) and a probe
world follow the s36/s37 precedent exactly.
