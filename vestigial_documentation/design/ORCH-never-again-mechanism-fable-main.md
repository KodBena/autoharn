# The "never again" gap — Fable main-loop's own shape (written BEFORE the blind consult returns)

Audience: orchestrator

Commissioned 2026-07-07 ~02:30. The maintainer flagged bias risk from his own proposal;
this note is my independent shape, committed before consulting a second Fable (whose brief
contains facts only — neither this note nor the maintainer's proposal). Comparison comes
after both exist.

## The failure class, from tonight's specimens

Lapse-type failures — no motivated reasoning, no scope drift, just omission and staleness:
the arm-script host TYPO (192.168.192.1 hand-copied where a registry held the truth); the
FORGOTTEN DDL apply (db+role+pg_hba done, kernel tables not); the e15 packet silently
DROPPING the block-and-ask mandate the e14 packet carried; the adapter knowing Task but
not Agent; the acts-schema DROP taking acts.ruling as collateral. ADR-0000's two questions
apply to each: what made it possible; what forecloses the CLASS.

## Where the current machinery stops

The findings ledger captures the instance and its disposition. But `fixed` forecloses the
INSTANCE, `filed` points at future work — and NOTHING tracks whether the class-foreclosure
ever happened. The conversion finding→mechanism (a gate, a fixture, a checklist line, a
lint) is manual, unlogged, and unverified. "Disposed" and "class-foreclosed" are different
states and the record cannot currently tell them apart. That's the gap: the never-again
step is prose-hoped, not machine-owed.

## My shape: a FORECLOSURE EDGE + a derived debt judgment — no new hand-maintained store

1. **`forecloses(mechanism_ref, finding_id)` as a first-class, machine-readable edge.**
   Every gate/fixture/lint/checklist-line born from a finding carries a marker citing the
   finding id (docstring convention `FORECLOSES: finding-28`, close-manifest registry
   column, pre-commit config comment). The edge is cheap to write at fix time — the moment
   the knowledge is hot.
2. **Maturity is DERIVED, never declared.** A finding's class is CLOSED iff: (a) a
   mechanism citing it EXISTS in the repo/registry, (b) that mechanism is REGISTERED
   somewhere that runs (close manifest, pre-commit, CI — a mechanism nothing runs is
   prose), and (c) it has been SEEN RED (ADR-0011: the banked mutation-flip/negative-
   control artifact). All three are mechanically checkable today: repo grep, registry
   read, artifact existence.
3. **The debt judgment**: `class_open(F)` — disposed-but-unforeclosed findings older than
   K increments — emitted as a standing close-manifest line, F49-loud. THIS is the
   automatic backlog: nobody files it; it derives. The reminder the maintainer is tired
   of writing by hand becomes a query.
4. **The meta-law, enforced at the disposition trigger** (the declarative shape): for
   lapse-class findings, the `fixed` disposition REQUIRES a foreclosure ref, exactly as
   `waived` requires a ruling ref today — a disposition claiming "never again" must point
   at the running thing that makes it true AT DISPOSITION TIME. Evidence-at-that-time,
   or the disposition is refused by the same trigger idiom we already have.
5. **The typo sub-class needs its own foreclosure shape**: hand-copied literals duplicating
   a registry (the 192.168.192.1 specimen — ledger_target held the truth; the script
   copied it wrong). Class-foreclosure = single-home derivation (scripts READ the
   registry) + a lint for known-registry literals appearing outside their home. ADR-0012
   P1 applied to configuration.

## What I deliberately do NOT propose

A separate tracked-objects database maintained by hand. Every hand-maintained mirror of
reality is itself a staleness lapse waiting to fire (the instance-keyed-apparatus lesson,
F33/F49). Whatever registry the mechanism needs should be derived from the repo + the
existing stores at check time, or be the registry something already RUNS from (like
ledger_target) — never a second bookkeeping surface that can drift from the first.
