# Kernel intake pair — review-witness row existence; journaler overflow guard

<!-- doc-attest-exempt: build-basis spec; attestation rides witnessed delivery -->

**Status: Fable-authored 2026-07-18, build basis for two small kernel lineage deltas
(next free sNN numbers at build time), maintainer-prioritized this date ("Block F
must be independent, you should see to it right away ... a priority item not only to
spec but to implement"). Per runs-are-linear, each delta is a file + scratch
witnesses; it reaches reality in the NEXT world's birth chain, and entry into
`bootstrap/new-project.sh`'s LINEAGE_CHAIN remains the maintainer's act (s47
precedent). Class statements per delta below; the CLI-side siblings ride the
separate led.tmpl bundle (Block A), not these deltas.**

## Delta 1 — review-witness row existence (ledger row 1600)

**Class: 2(a) fail-safe — ADDS a refusal, relaxes nothing, changes no existing
semantics.** Witnessed trigger (2026-07-18): `led work close` accepted
`--review-witness row:1594` when no row 1594 existed — the orchestrator guessed its
own decision row's id. A witness citation naming a nonexistent row is a claim with
a dangling evidence pointer, in the one place evidence pointers are load-bearing.

**Mechanism.** On INSERT of a row whose `work_review_ref` (or review-witness field
as built — the builder reads the s29/s37 close path and names the actual column) or
whose `refs`/witness text contains one or more `row:<id>` tokens **in the
review-witness position specifically** (not prose `refs` generally — prose citation
of future/foreign rows stays legal), a trigger verifies each cited `<id>` exists in
`ledger` at insert time. A missing id → RAISE with a teaching message naming the
missing id, the row kinds checked, and the corrective form. Scope deliberately
narrow: only close-family kinds (`work_closed`, `work_violation_disposition`), only
their review-witness field. Self-reference (citing the id the row itself will
receive) is impossible by construction and the message says so when the cited id
equals `currval`-adjacent guesses — the exact failure mode witnessed.

**Witnesses (scratch schema, both polarities, judge differential AGREE):**
- **WK1-a** close citing an existing row → accepted, row lands (no regression).
- **WK1-b** close citing `row:<absent id>` → refused, message names the id and the
  teaching; nothing written; sequence-gap accounting unaffected.
- **WK1-c** a plain `led decision --refs "row:<absent>"` (NON-close kind) → still
  accepted (scope check: prose refs not captured by this refusal).

## Delta 2 — journaler attempted-identity overflow guard (ledger row 1581)

**Class: NOT letter-2(a)** (it edits an existing function body via CREATE OR
REPLACE), **built under the maintainer's direct instruction of 2026-07-18** (quoted
in the Status block; his instruction is the ratification, read plainly per the
2026-07-11 vocabulary note). Effect is strictly fail-safe: MORE refusals get
recorded, nothing is newly permitted.

**Defect, witnessed 2026-07-18 (row 1581).** `kernel.journal_write_refusal`
resolves the attempted identity by regex `^[0-9]+$` then an unguarded
`(p_payload->>'actor')::bigint` cast (s43 line ~730). An over-bigint digit string —
which is exactly the kind of payload that ARRIVES at the journaler, since it
arrives refused — makes the cast raise 22003 inside the journaler: the refusal
recording itself aborts, the `write_refused` row is never written, and only the
oracle sequence gap remains. The recording path fails on precisely the inputs it
exists to record.

**Mechanism.** The attempted-identity resolution becomes total: the cast is guarded
(length/value pre-check or an exception handler local to the resolution — builder's
choice, stated in the delta's header comment with the reason) so an unresolvable
`actor` yields `v_attempted := NULL` — the same value the function already uses for
"neither resolves" — and journaling proceeds. No other line of the function
changes; the oracle bump stays first; the loud-abort semantics for a genuinely
failing INSERT stay.

**Witnesses (scratch schema, both polarities, judge differential AGREE):**
- **WK2-a** a boundary write refused with `actor` = a 30-digit numeral → the
  refusal IS journaled: `write_refused` row present, `refusal_attempted_actor`
  NULL, `refusal_attempted_role` populated, sqlstate/message = the ORIGINAL
  refusal's, not 22003.
- **WK2-b** a refused write with a normal in-range wrong `actor` → journaled with
  the attempted id resolved (no regression on the resolving path).
- **WK2-c** the pre-fix polarity witnessed on the scratch schema BEFORE applying
  the delta: the same 30-digit payload crashes the journaler (22003, no row,
  sequence gap) — the defect reproduced, then killed by the delta, on the same
  schema pair.

## Shared build conditions

Scratch-only harness wiring; `.detect.sql` sibling per delta per house convention;
SQL/ASP differential in AGREE per the standing class requirement; NO edits to
`bootstrap/new-project.sh` (maintainer's chain act); NO edits to s43's shipped file
(delta 2 is a NEW lineage file re-issuing the function, the same way every
amendment to a shipped function has landed since runs-are-linear).
