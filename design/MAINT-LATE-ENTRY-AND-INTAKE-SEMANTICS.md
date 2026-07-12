# Late entries and intake bursts — DRAFT design for the maintainer

STATUS: RATIFIED (2026-07-11, maintainer: "you had three points on the contemporaneity
question, and I agree with all of them"). Drafted the same day from run 10's first live
audit verdict and its adjudication (BACKLOG, "Run-10 first audit verdict adjudicated",
2026-07-11); implementation commissioned at ratification.

RATIFICATION NOTE — the "own up" reading (maintainer, at ratification): the author of
batched ledger rows must own up to the batching, "at least in spirit if not mechanized,"
with the caveat that "a mechanization could be brittle if not done right." Confirmed, and
here is where each half already lives: the MECHANIZED owning-up is the s23 invocation token
itself — it is injected by hook, involuntarily, so a batch declares itself in a way the
writer can neither omit nor fake (this is exactly why the verdict is named
BATCHED_**DECLARED**), and it is non-brittle for that same reason. The SPIRIT-level duty is
Proposal 3's preamble line plus the declared event time of Proposal 2 for the late case.
What this design deliberately does NOT do — agreeing with the brittleness instinct — is
mandate prose "I am batching" rows: a voluntary confession requirement would be enumerable,
fakeable, and noise; the involuntary token already tells the truth.

## The question in plain words (read this first)

The new `./audit` verb correctly flagged run 10's first eleven ledger rows as
BATCHED_DECLARED: ten rows written by one invocation, under a second apart. Adjudication
showed the batch was honest — the ten rows were a task decomposition being *authored*, not
past work being *narrated* (decisive evidence: the first task's subject, `git init`, had
not even happened yet when the adjudicator checked). Real-world paper-trail mandates draw
exactly this line: batching is a shape, backfill is a lie about time, and even genuinely
late entries are legal when they are *declared* ("late entry, event occurred at T,
reason"). Our vocabulary can distinguish declared batching from suspected backfill, but it
has no way for a writer to declare a late entry, and no way for the audit to recognize an
intake burst as the benign shape it provably is. This memo proposes both, smallest change
first. Nothing here loosens any refusal; everything is additive.

## The three specimens this design is measured against

1. **Benign: the run-10 intake burst.** Rows 2–11, one invocation token, statements are
   present-tense declarations ("task N: ..."), written before any tool activity existed.
   Predicted by the intake discipline (preamble point 1) and causally incapable of being
   backfill — the described events had not occurred yet.
2. **Honest late entry, improvised: run-10 row 1.** The agent investigated for ~2 minutes
   before its first ledger write, then *self-reported* the gap in prose: "was performed
   before any ledger entry existed... Recording this gap honestly rather than back-dating."
   This is exactly the declared-late-entry act, performed without a mechanism to hold it.
3. **Hostile: the runs 5–8 pattern.** Bursts of rows 0.02–0.16s apart narrating minutes of
   prior conduct as if live, undeclared (BACKLOG "Contemporaneity indictment", 2026-07-11).
   This is the shape the mandate forbids and BACKFILL_SUSPECT exists for.

## Proposal 1 — teach the audit the intake shape (no vocabulary change, no kernel change)

A burst whose rows all precede the world's first tool_event is benign by construction:
there was no conduct yet to narrate. The audit report annotates such a burst
`intake-shape (precedes all tool activity)` on the existing BATCHED_DECLARED verdict line.
The closed verdict vocabulary is untouched; the operator stops having to decode the benign
case by hand (the run-10 session's operator could not tell, and stopped a healthy run over
the previous such ambiguity). Deterministic, engine-side only.

## Proposal 2 — declared late entries (kernel delta + one new verdict; needs the word)

- `led` gains an optional declared event time (e.g. `./led --event-time <ts> finding
  "..."`), stored in a new NULLABLE ledger column. Writing it is always optional; omitting
  it means "this row records a present act", which is today's semantics unchanged.
- The audit gains one verdict: **LATE_DECLARED** — the row's declared event time precedes
  its write time beyond threshold, and the writer said so. Exit 0: a declared late entry
  satisfies the mandate (ALCOA+ permits it; what it forbids is the undeclared kind).
  BACKFILL_SUSPECT then means precisely: an *undeclared* gap inferred from the machine
  record. The refusal semantics sharpen; nothing existing relaxes.
- Routing: the column is a strictly additive, fail-safe kernel delta (class-ratified shape
  on its face), but the verdict set is a closed vocabulary under ADR-0000 — extending it is
  the maintainer's act, so the whole proposal routes to the maintainer as one question.
  Per the linearity ruling it reaches reality in the NEXT world's birth chain; no existing
  world is touched.

## Proposal 3 — one preamble teaching line (sub-constitutional text)

Add to the world preamble: "Record as you go — one row at the moment of the act. Batching
declarations you are making right now (an intake decomposition) is fine; the token declares
it. If you must record an act after the fact, declare its event time — never narrate the
past as if live." Run-10 row 1 shows agents already reach for this honesty; the line gives
it a name and Proposal 2 gives it a mechanism.

## The question (one, prepared, yes/no)

**Adopt the late-entry discipline?** YES ratifies all three proposals: intake-shape
annotation (engine-side, lands immediately), the declared-event-time column + LATE_DECLARED
verdict (spec'd and scratch-witnessed by a delegated executor, enters the next world's
birth chain), and the preamble line. NO leaves the current vocabulary standing — honest
batches keep reading as bare BATCHED_DECLARED and improvised prose disclosures like run-10
row 1 remain uncredited by the audit. Recommendation: YES — every part is additive, the
mandate's own late-entry concept is the missing piece, and the first three specimens are
already banked.
