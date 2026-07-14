# SPEC: doc-attestation/2 — a first-class adjudication field for escalated attestation records

Audience: orchestrator (+secondary: maintainer — the section below names both: "whoever maintains that gate" and "the maintainer reviewing this change")

## What this document is, who it is for, and what it decides

This is a small, self-contained specification for the next version of the attestation record
format the [doc-attestation gate](../gates/doc_attestation_presence.py) reads and writes. It is
written for whoever maintains that gate or the [A:B:C audit-loop recipe](ORCH-ABC-AUDIT-LOOP-RECIPE.md),
and for the maintainer reviewing this change. It decides exactly one thing: **an attestation
record for an *escalated* fresh-context review loop must record the escalation recipient's
adjudication — who adjudicated it, what they applied, and when — in a typed field of its own,
instead of in the free-text `b_id` string where that information currently hides.** Everything
else about the format stays as it is.

Background in one paragraph, so a reader who has not followed the discipline can still read this.
[ADR-0017 (the zero-context reader)](../law/adr/0017-the-zero-context-reader.md) requires every
maintainer-facing markdown document to pass a **fresh-context audit loop** before it ships: an
author (A) writes it, a separately-forked reviewer (B) who has seen only the document and the ADR
reviews it for legibility, and a repairer (C) fixes what B found. The loop runs at most two B→C
rounds; if B still finds defects at the cap, the document does not grind a third round — it
**escalates** as a "non-converging-review-loop", a typed event handed to a higher-authority
recipient (the orchestrator, or a human) who **adjudicates**: decides what to apply and applies
it. Each loop is recorded as one JSON line — an *attestation record* — in the append-only ledger
[`attestations/doc-legibility-attestations.jsonl`](../attestations/doc-legibility-attestations.jsonl).
The gate checks, at commit time, that every changed document has a well-shaped record for its
exact current bytes. The record format's current version is called `doc-attestation/1`; this spec
defines `doc-attestation/2`.

## The seam this closes

When the discipline was first enforced live (BACKLOG, "First live enforcement of ADR-0017's loop
— on the orchestrator's own merge", 2026-07-11), the very first escalation exposed a gap the
format's designers had not yet hit: **the attestation record has no field for the escalation
recipient's adjudication.** An escalated loop still gets a record — ADR-0017 is explicit that
"recording a DEFECT verdict with `escalated: true` is not a failure to record, it is the honest
record of what happened" — but the *disposition* of that escalation (who resolved it, and how)
had nowhere structured to go. So it went into `b_id`, a field whose stated purpose is only to
identify B's invocation. The seven escalated records already in the ledger show the workaround
verbatim; for example, record 5's `b_id` reads:

<!-- doc-shapes-allow: quoted defect specimen, per ADR-0017 Exceptions (quoted defects) -->
> "... ESCALATION ADJUDICATED: round 2's one surviving finding ... was adjudicated by the
> orchestrator (Fable) as escalation recipient — B's own suggested one-clause reorder applied
> verbatim, no content change ... Recipe seam flagged in BACKLOG: the record format has no
> adjudication field."

That is load-bearing audit information — the "who decided, and what they applied" that
[ADR-0013 Rule 1/2](../law/adr/0013-execution-integrity.md) makes the
ratifier's to own — carried in a string the gate treats as opaque identity text. A reader
auditing an escalation cannot find the adjudication by field; they must read prose. That is the
[ADR-0012 P1](../law/adr/0012-compositional-and-structural-hygiene.md) single-source-of-truth
defect (a fact with no home of its own) and the
[ADR-0002](../law/adr/0002-fail-loudly.md) lying-signature defect (a field carrying a payload its
name does not advertise), in miniature.

## The type-driven fix (ADR-0000)

Per [ADR-0000 Rule 2(a)](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md), the first
question is not "how do we fix this record" but "what type would make this defect class
unrepresentable". The answer is a typed field. `doc-attestation/2` adds one object, `adjudication`,
and binds it to the `escalated` flag so that, **for an honest `/2` record**, the two illegal states
are refused:

- A record that **escalated** but records **no adjudication** — the seam — is refused.
- A record that did **not** escalate but carries an **adjudication** — a loop that converged CLEAN
  yet claims someone adjudicated an escalation that never happened — is also refused, because it is
  a lying record.

The qualifier "for an honest record" is load-bearing and stated plainly rather than overclaimed.
This gate polices the *artifact's shape*, never the author's *identity or honesty* — ADR-0017's
own design ("the enforced surface is the attestation, not the agent's identity", because "identity
enumeration fails open"). A record that lies to dodge — tags itself `schema: doc-attestation/1` so
the `/2` rule never runs, or sets `escalated: false` on a loop that truly escalated — is the **same
evasion class as a fabricated CLEAN verdict**, which this gate has never claimed to catch and which
no shape-check can soundly close (the dodger who would omit the adjudication would equally forge a
clean verdict). So `/2` does not make the seam *adversarially* impossible; it makes an honest
escalation record *unable to hide its adjudication in prose*, and it routes the sanctioned writer
(`--record`) to `/2` by default. That is the real, bounded claim; the stronger one would be the
acronym-gate mistake ADR-0017 warns against — a legibility gate whose over-broad rule fired ~1600
false positives and so trained everyone to ignore it.

The `adjudication` object has exactly three fields — no more (extra keys are refused, so the field
cannot itself become the next free-text overload home) — each a non-empty string, matching the
three facts the seam names:

```json
{
  "schema": "doc-attestation/2",
  "doc": "CAPABILITIES.md",
  "content_sha256": "<64-hex sha256 of the document's FINAL on-disk bytes at record time>",
  "b_id": "<identifies B's invocation, as in /1 — no longer overloaded with the adjudication>",
  "rounds": [ ... unchanged from /1 ... ],
  "escalated": true,
  "adjudication": {
    "adjudicated_by": "orchestrator (Fable), escalation recipient",
    "disposition": "applied B round-2's own suggested one-clause reorder verbatim, adding nothing of my own",
    "adjudicated_at": "2026-07-12T00:00:00Z"
  },
  "attested_at": "2026-07-12T00:00:00Z"
}
```

`adjudicated_by` is *who*, `disposition` is *what was applied*, `adjudicated_at` is *when* — the
three the seam calls out. Every other field is identical to `doc-attestation/1`.

One clarification the seam's own records already settle, stated here so a reader does not trip on
it: when an adjudication *applies a repair*, the shipped bytes change, so `content_sha256` is the
document's **final on-disk bytes at record time**, not the earlier bytes B read in a prior round —
`--record` computes it from disk itself, never trusting a supplied hash, so the recorded hash always
equals the committed file's, which is what the commit-time gate checks. (This is the convention the
existing escalated `/1` records already follow — record 5's own note, "sha above is the
post-adjudication bytes.") A `disposition` phrased as "applied B's reorder verbatim" therefore means
"applied exactly B's suggested edit, adding no content of my own" — not "the bytes are unchanged",
which a reorder of course changes.

## What the gate checks, and what it does not

The gate's posture is unchanged and deliberately narrow: it checks **presence and shape, never
conclusions**. ADR-0017's ratified constraint — "no LLM verdict blocks anything", and by
extension no human judgment's *content* blocks — governs the new field exactly as it governs
`b_id` and B's own verdict. So the gate verifies that `adjudication` is *present* (when escalated)
and *well-shaped* (three non-empty strings); it does **not** and must **not** judge whether the
disposition was correct, wise, or complete. Whether "applied B's repairs verbatim" was the right
call is a review question, adjudicated by a human, never by this gate. The field makes the
adjudication *auditable by field* rather than *findable only in prose*; it does not make it
machine-graded.

Enforcement surface, in [ADR-0011 Rule 1's](../law/adr/0011-mechanization-discipline.md) closed
vocabulary: **test/CI gate at commit time** (the same surface `doc-attestation/1` already binds),
plus a **write-time refusal** in `--record` so a malformed record is refused before it enters the
ledger, never discovered later at commit. Nothing here reads prose comprehension.

Two honest scoping notes, so the claim is not read wider than it is:

- **`b_id` stays free text, unpoliced.** `/2` gives the adjudication its own typed home, so it no
  longer *needs* to ride `b_id`. It does not, and cannot, *stop* an author from also writing
  "ESCALATION ADJUDICATED …" into `b_id` — the gate treats `b_id` as opaque identity text by
  ADR-0017's explicit reasoning (no sound predicate separates a genuine identifier from a claimed
  one). `/2` removes the *need* to overload `b_id`, not the *ability*; a `b_id` still stuffed with
  adjudication prose is reviewed like any other claim, not refused here.
- **When the record is written, and why there is no "pending" state.** The attestation is recorded
  once the loop is *fully dispositioned* — for an escalated loop, that means after the recipient has
  adjudicated. A loop that has escalated but whose recipient (a human, say) has not yet decided is an
  *uncommitted working state*, not a ledger row: no record is appended, and the commit-time gate
  therefore holds the document back until a record — carrying the adjudication — exists. The
  append-only ledger correctly never holds a half-escalation, so `escalated: true` requiring all
  three adjudication fields is not a lost state; the pending state simply lives in the working tree,
  where the gate's own refusal keeps the doc until the loop is finished.

## Migration — honest, additive, and non-destructive

The migration posture follows [ADR-0017's Exceptions](../law/adr/0017-the-zero-context-reader.md)
(point-in-time records are never retro-edited) and
[ADR-0013](../law/adr/0013-execution-integrity.md) (finish the real
change, honestly):

1. **Existing `/1` records stay valid, forever, unchanged.** The ~20 records already in the ledger
   are point-in-time records of loops that ran under `/1`. They are validated under `/1`'s rules,
   which are untouched by this spec. They are **never rewritten** to `/2` — a `/1` record is not
   "wrong", it is older, and rewriting a frozen point-in-time record to add a field it never had
   would be exactly the retro-edit ADR-0017 forbids. The seven escalated `/1` records keep their
   `b_id`-carried adjudication as the honest record of how the loop was dispositioned at the time.
2. **The gate accepts both versions.** It dispatches on the `schema` string. An unknown `schema`
   is refused (fail-closed): a version whose rules the gate does not know cannot be shape-checked,
   so it must not pass silently.
3. **New records are written at `/2`.** `--record` emits `schema: doc-attestation/2`. A new
   escalated loop records its adjudication in the typed field; a new converged loop records no
   adjudication, exactly as before but under the new version tag.
4. **No back-sweep.** There is no `/1`-to-`/2` migration pass and none is wanted — consistent with
   ADR-0017 Rule 4's "migrates on touch, not by sweep" and
   [ADR-0004's](../law/adr/0004-minimal-touch-edits-to-partially-visible-files.md) minimal-touch
   posture. The back-catalog simply stops growing in `/1`; it does not get rewritten.

This is additive in spirit: `/2` adds a refusal (the seam is now caught) and a field; it relaxes
nothing and changes no existing record's validity.

## What this spec deliberately does NOT do (scope, named)

- **It does not touch [ADR-0017](../law/adr/0017-the-zero-context-reader.md) or any file under
  `law/`.** The law is the frozen constitutional layer (CLAUDE.md ORCHESTRATION); a future
  ADR-0017 amendment could fold `/2` into its Revisit-when #2, but that routes to the maintainer
  and is out of this spec's scope. This spec is the mechanization; the ADR remains its law.
- **It does not derive `escalated` from the rounds.** One could argue `escalated` is derivable
  (a still-DEFECT final round at the two-round cap) and so violates ADR-0012 P1 by being stored.
  That is a real observation, but it is a `/1`-inherited design choice, orthogonal to the
  adjudication seam, and re-opening it would be scope inflation. `escalated` stays an explicit
  flag; this spec only binds `adjudication` to it. Filed as an observation, not fixed here.
- **It does not verify `escalated` against the final verdict beyond the existing rule.** The gate's
  one cross-check is the `/1`-inherited "still-DEFECT at the cap must be `escalated: true`". It does
  NOT refuse `escalated: true` on a loop whose final round is CLEAN (a converged loop mislabelled
  escalated). Such a record is *admitted* under `/2` as long as it carries a well-shaped
  adjudication; its honesty is left to review. This axis is **named as not covered** here rather
  than silently left, per ADR-0000's closure discipline.
- **It does not update the recipe prose in this pass.** [ABC-AUDIT-LOOP-RECIPE.md](ORCH-ABC-AUDIT-LOOP-RECIPE.md)
  step 6 delegates the exact schema to the gate docstring, so it stays correct; its step-5 summary
  of escalation does not yet mention the adjudication field. Because `--record` now *teaches* the
  requirement on refusal (it names the missing field and points here), the staleness is a
  loud-and-self-correcting signpost, not a silent hazard, so it is **filed** (ADR-0013 Rule 4) as a
  BACKLOG follow-up rather than fixed in-pass — keeping this change small.

## Closure statement (ADR-0000, 2026-07-02 amendment form)

**The invariant.** For every attestation record the gate reads or writes: the record's `schema` is
a version the gate knows (`doc-attestation/1` or `/2`); and under `/2`, the escalation recipient's
adjudication is present-and-well-shaped exactly when the loop escalated, and absent exactly when it
did not. "Who adjudicated an escalation, and what they applied" has one typed home, not free text.

**The quantification universe.** The axes over which the invariant is quantified, each enumerated:

- *Schema version:* `/1` (legacy, rules unchanged), `/2` (new), and unknown (refused). All three
  reach the gate; all three are dispositioned.
- *Escalation state:* `escalated: true` and `escalated: false`. Both are covered under `/2`; the
  adjudication requirement flips on this axis.
- *Adjudication presence:* present and absent. Both are covered on both escalation states — the
  four combinations are the heart of the enumeration below.
- *Adjudication shape (when present):* the object is exactly the three fields `adjudicated_by` /
  `disposition` / `adjudicated_at`, each checked for non-empty-string. A missing field, an empty
  field, AND any *extra* key are all refused — the object is closed, so it cannot itself become the
  next free-text overload home.
- *Sibling surfaces:* both entry points that admit a record — the commit-time **gate** (validates
  records already in the ledger) and the **`--record` writer** (validates before append) — run the
  identical `validate_record`, so the invariant holds at both, not just one.
- *Not covered, named:* whether `escalated` is *consistent with the final round's verdict* beyond
  the still-DEFECT-at-cap rule (an `escalated: true` record with a CLEAN final round is admitted);
  whether the adjudication's *content* is correct (a review question, never the gate's); whether
  `b_id` distinctness or `adjudicated_by` identity is genuine (self-declared, reviewed, not policed
  — the same reasoning ADR-0017 gives for `b_id`); whether the record is honest about its own
  `schema`/`escalated` (a dodging record is the fabricated-verdict evasion class, uncatchable by any
  shape-check); and the record's *top-level* key set, which is deliberately NOT closed (a
  `/1`-inherited tolerance — the gate has always ignored unknown top-level keys; only the new
  `adjudication` object is closed, born strict in `/2` since it breaks no existing record).

**The denomination check.** The requirement is denominated in the thing that actually detonated:
the *presence of a typed adjudication on an escalated record*, not a proxy. It is not a round
count, not a string-length heuristic on `b_id`, not a regex hunting the word "adjudicated" in free
text — it is the field itself, bound to the `escalated` flag. The refusal fires on the real
condition (escalation without a home for its disposition), so it cannot be satisfied by a record
that merely *looks* adjudicated while the field is absent.

**The universe of record shapes this spec admits and refuses is exactly:**

ADMITTED (validate clean):
1. A `/1` record well-shaped under `/1`'s unchanged rules — any escalation state, no `adjudication`
   field (or one present-but-ignored, since `/1` does not bind extra fields).
2. A `/2` record, `escalated: false`, with **no** `adjudication` field, otherwise well-shaped.
3. A `/2` record, `escalated: true`, carrying an `adjudication` object of three non-empty strings
   (`adjudicated_by`, `disposition`, `adjudicated_at`), otherwise well-shaped — including the
   named-not-covered case where the final round is CLEAN yet `escalated: true`.

REFUSED:
4. A `/2` record, `escalated: true`, with **no** `adjudication` field — the seam, now closed.
5. A `/2` record, `escalated: true`, with an `adjudication` that is not an object, or is missing
   any of the three fields, or has any field that is not a non-empty string, or carries **any key
   beyond the three** (the object is closed).
6. A `/2` record, `escalated: false`, that carries a **non-null** `adjudication` value — the lying
   record. (A JSON `null` is treated as *absent* on either escalation state, because a null
   adjudication asserts nothing and so is not a lie; only a populated adjudication on a
   non-escalated record is refused.)
7. Any record whose `schema` is neither `/1` nor `/2` — refused fail-closed.
8. Every shape `/1` already refused, refused identically under both versions: a missing top-level
   field; a `content_sha256` that is not 64-hex; a `rounds` list outside 1..2 entries; a DEFECT
   round with no findings, or a finding missing `file`/`line`/`quote`/`repair`; a CLEAN round not
   enumerating all four Rule-1 clauses; a round whose `round` number is out of sequence; a
   still-DEFECT final round at the two-round cap with `escalated: false`; a non-boolean `escalated`;
   an empty `b_id`.

The enumeration is total over its axes — `schema` (known or unknown), and for a known schema an
`escalated` boolean and an `adjudication` that is present-or-absent and, when present, closed to
exactly its three fields. The one degree of freedom left open is named above, not hidden: the
record's *top-level* key set is not closed (the `/1`-inherited tolerance of unknown top-level
keys), so a well-shaped record carrying an extra top-level key is admitted — a bounded, declared
looseness, not a gap in the escalation/adjudication invariant this spec governs.

## Related

- [ADR-0017 (the zero-context reader)](../law/adr/0017-the-zero-context-reader.md) — the law this
  record format mechanizes; "The fresh-context audit loop" section designs the loop and its
  escalation; Revisit-when #2 is where a future maintainer amendment would cite this spec.
- [`gates/doc_attestation_presence.py`](../gates/doc_attestation_presence.py) — the gate; its
  module docstring's "SCHEMA VERSIONS" block is the SSOT of the on-disk format, this spec is its
  rationale.
- [ABC-AUDIT-LOOP-RECIPE.md](ORCH-ABC-AUDIT-LOOP-RECIPE.md) — the operator recipe for running the loop
  and recording a record.
- [ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md) — the type-driven fix
  and the closure-statement form used above.
- BACKLOG.md, "First live enforcement of ADR-0017's loop — on the orchestrator's own merge"
  (2026-07-11) — where the seam was found and named.
