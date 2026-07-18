# Ledger tag folksonomy — build basis (the derived-view delta and the capture verb)

<!-- doc-attest-exempt: build-basis spec awaiting maintainer ratification; attestation
     rides the ratified revision -->

**Status: Fable-authored 2026-07-18, awaiting maintainer ratification. Build gated by
work item `ledger-tag-folksonomy` (row 1608) and its blocks-start edge on
`fastapi-boundary-service` (row 1609). Basis: the banked consult
`design/FABLE-LEDGER-TAG-FOLKSONOMY-CONSULT.md` (f5e584f), adopted by the maintainer
2026-07-18 ("a nice factorization"). This spec is deliberately small: it binds the
consult's four-part design to buildable surfaces and closes the grammar, so the whole
item is executable by the default implementer once the gates open.**

## 1. Scope and class

One additive kernel lineage delta (next free `sNN` number at build time) plus one
operator-verb addition to `bootstrap/templates/led.tmpl`. The delta ADDS two derived
views and nothing else: no table changes, no relaxed refusal, no altered semantics —
squarely the pre-ratified 2(a) fail-safe class, so it enters the birth chain by class
once witnessed on a scratch schema on both polarities with the SQL/ASP differential in
AGREE. Scaffold `LINEAGE_CHAIN` wiring in the delta's own scratch harness only; entry
into `bootstrap/new-project.sh` is the maintainer's birth-chain act, per the s47
precedent, not the builder's.

Out of scope, named so the omissions read as decisions: no clingo-side EDB predicate
(that is promotion-stage work — a token something wants to *reason* over gets promoted
first, per §5); no tag column (refuted by the consult's Fact A: the ledger is
append-only, and lore is retrospective); no changes to `refs` parsing in
`engine/lp/`.

## 2. The capture convention (normative; zero schema change)

A tag is an ordinary ledger row: `kind = note`, `refs` containing one or more
`row:<id>` tokens naming the annotated row(s) (the documented bare-reference
convention), `statement` matching this closed grammar exactly:

```
statement := "tag:" token " -- " prose
token     := [a-z0-9][a-z0-9-]{0,63}        (no leading hyphen, ≤ 64 bytes)
prose     := any non-empty text
```

One separator form (`" -- "`, ASCII, four bytes including both spaces), not several —
a parse grammar with dialects is how drift starts at the syntax layer before the
vocabulary layer gets a chance. A `kind=note` row whose statement begins with the four
bytes `tag:` but does not match the grammar is MALFORMED — surfaced loudly by the view
family (§3), never silently dropped and never silently repaired. Rows whose statement
does not begin `tag:` are outside this spec's universe entirely.

Tags are supersedable like everything else: a wrong tag is defeated by an ordinary
supersession, and the view family reads `ledger_current`, so a defeated tag vanishes
from every derived surface without any tag-specific mechanism.

## 3. The delta: two derived views (the consumer, so the seam is not dead)

Both `security_invoker`, both reading `ledger_current` only.

- **`tag_annotation`** — one output row per (tag row, target reference): tag row id,
  `ts`, `actor`, parsed `token` (NULL when malformed), target row id parsed from
  `refs` (NULL when absent), and a `shape` column with a closed vocabulary:
  `well_formed | malformed_token | missing_target_ref | dangling_target`
  (`dangling_target`: the `row:<id>` names no ledger row — flagged loudly, echoing
  the row-existence lesson of row 1600, not hidden).
- **`tag_census`** — per observed token: use count, distinct-target count, first/last
  `ts`, and a malformed-rows count surfaced in the same view (not a separate place
  nobody looks). This is the drift-loudness instrument: `hazard` vs `hazards`
  adjacency is meant to be seen here, per ADR-0002 — visible, not forbidden.

**Closure statement (ADR-0000 2(a) form).** Quantification universe: every
`ledger_current` row with `kind = note` whose `statement` begins with the four bytes
`tag:`. Claim: each such row is classified by `tag_annotation` into exactly one
`shape` per target reference (and into `missing_target_ref` when it has none), and no
row in the universe is absent from the view. Rows outside the universe are untouched
by construction — the delta reads; it cannot refuse, relax, or rewrite anything.

## 4. The verb: `led tag <row-id> <token> <prose...>`

A `led.tmpl` subcommand writing an ordinary note row through the EXISTING write path —
no new kernel surface. Client-side teaching refusals, before any write: token
violating the grammar (refusal quotes the grammar); target row absent (refusal names
the id; this is the CLI-side courtesy check — the kernel-side existence refusal
remains item `review-witness-row-existence-check`'s own scope, row 1600, not this
build's); empty prose. The verb composes the statement/refs itself so the grammar has
one writer; hand-written `led decision`/`led note` rows that happen to start with
`tag:` are still classified by the views like any other universe member — the verb is
convenience, not a gatekeeper.

## 5. The bright line (normative, on the record)

Tag rows and tokens are **diagnostic-grade until promoted**. No gate, verdict,
routing decision, or refusal may read an unpromoted token. Promotion on recurrence:
when a token is wanted mechanically, it is minted into closed vocabulary by its own
additive delta (s25 precedent), and the folk rows are superseded or migrated as that
delta's spec directs. The consult's four falsifiers (capture friction persisting,
a consumer sneaking in, the census view drowning in near-duplicates, retro-tagging
proving rare) are the review criteria at the first harvest pass; the harvest itself
rides the existing method-harvesting posture.

## 6. Witnesses (scratch schema, both polarities, differential in AGREE)

- **WT1** `led tag` on an existing row → the note row lands; `tag_annotation` shows it
  `well_formed` with the right token/target; `tag_census` counts it.
- **WT2** malformed statements written directly (bad token grammar; `tag:` prefix with
  no ` -- `; well-formed statement with no `row:` ref) → each classified into its
  named shape, none absent, none repaired.
- **WT3** a `row:<id>` naming no ledger row → `dangling_target`, loud.
- **WT4** superseding a tag row → it vanishes from both views; the census count drops.
- **WT5** `led tag` refusal legs: bad token, absent target, empty prose — each refusal
  teaches (quotes the grammar / names the id), exit nonzero, nothing written.
- **WT6** the delta's detect leg both polarities and the SQL/ASP differential AGREE,
  per the standing class requirement.
