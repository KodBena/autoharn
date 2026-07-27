# FABLE-S65-REFUSAL-ATTEMPTED-KIND-SPEC — the refusal journal records the attempted kind

<!-- doc-attest-exempt: Fable-authored spec 2026-07-27, ratified by the maintainer the
same day ("Yes, let's have that column", ledger row 1487); the A:B:C loop runs on the
build, not the proposal text. Removal condition: superseded by the s65 merge record. -->
<!-- design-currency: status=discharged discharged-by=2fb06c046f8830ac3e64dd0a72204b443bd59c8f -->

- **Status:** RATIFIED 2026-07-27 (maintainer, verbatim on ledger row 1487); build
  dispatched the same day.
- **Basis:** ledger rows 1474/1476 (the unattributed refusal probes), 1483 (the
  attribution post-mortem: knowing the attempted KIND would have made the cause obvious
  in seconds), 1487 (the ratification). The s43 refusal journal
  ([`kernel/lineage/s43-typed-verdict-write-boundary.sql`](../kernel/lineage/s43-typed-verdict-write-boundary.sql))
  deliberately journals the payload as a DIGEST only (the R4 privacy discipline —
  statement content stays out of the journal); that discipline is UNCHANGED by this
  delta. The attempted kind is a single, low-sensitivity vocabulary token, and its
  absence is what forced a three-agent interrogation to answer a one-word question.

## 1. The delta (s65, one file)

`kernel/lineage/s65-refusal-attempted-kind.sql`:

1. **One new nullable column** on `ledger`: `refusal_attempted_kind text`, kind-scoped
   to `write_refused` rows by the same two-way kind-shape CHECK idiom every kind-scoped
   column family uses (a non-`write_refused` row carrying it refuses; a `write_refused`
   row may carry it or NULL — NULL means "not extractable", never "not attempted").
2. **`kernel.journal_write_refusal` re-issued** (head-body rule: cite the
   immediately-prior re-issue file, carry `-- prior-body-sha256`) to extract the `kind`
   key from the refused jsonb payload BEFORE digesting and record it in the new column.
   Extraction is TOTAL in the s49 precedent's sense: a payload with no `kind` key, a
   non-text kind, a malformed payload — all journal with `refusal_attempted_kind NULL`
   and never abort the refusal recording (more refusals recorded, never fewer). The
   digest computation is byte-identical to before — the column is additional, not a
   substitute. **Length bound (amendment, see §5):** the extracted token is stored
   verbatim only up to 256 bytes; a longer kind journals as NULL (same "not
   extractable" meaning — a real vocabulary token is never that long, and the refusal
   path is precisely where hostile input arrives). The kind-shape CHECK carries the
   same bound so the invariant is table-level, not function-trust.
3. **`compute_row_hash` re-issued** to cover the new column, under the s42 law
   (full-column coverage; `gates/hash_coverage_gate.py` must pass), with its own
   lineage citations.
4. **The ASP twin**: no change to any derivation — journal columns are EDB facts like
   any other ledger column; the builder confirms (and states) whether any exporter
   emits refusal columns today and mirrors the addition only where an existing family
   already carries the sibling `refusal_*` columns. Per the s63 finding, the
   differential cannot see write-boundary behavior; the coverage for this delta is its
   fixtures.

## 2. Class routing

Fail-safe-additive by the 2026-07-09 ruling read plainly: the delta adds one column,
one narrowing CHECK, and additional recording inside an existing refusal path; nothing
existing is relaxed, no new act is permitted, refusal behavior toward callers is
byte-identical. The privacy consideration — the one axis on which "additive" could be
doubted, since the journal now reveals one more token — is not delegated to the class:
the maintainer ratified this specific revelation in his own words (row 1487). No
residual routing question.

## 3. Witness plan (scratch, both polarities, red first)

RED: a non-`write_refused` row attempting to carry `refusal_attempted_kind` refuses
(the kind-shape CHECK); the pre-delta baseline re-witnessed (an invalid-kind write
journals with no attempted-kind information — the rows-1474/1476 shape).
GREEN: an invalid-kind write through the boundary journals `write_refused` with
`refusal_attempted_kind` = the attempted token (witness with kind `row`, the incident's
own probable specimen); a malformed no-kind payload journals with NULL, refusal still
recorded, nothing aborts (the s49 totality leg); an ordinary accepted write is
byte-identical pre/post; `verify-chain` INTACT with the refusal oracle reconciling;
full newborn birth through the generated chain including s65; `./judge` AGREE;
`gates/hash_coverage_gate.py`, `gates/lineage_reissue_lineage.py`,
`gates/kernel_function_census.py` (bank updated in the same commit) all clean.

## 4. Closure statement

Quantification universe, per ADR-0000 Rule 2(a): the write surfaces that journal
refusals are exactly the SECURITY DEFINER boundary functions calling
`journal_write_refusal` (the builder enumerates them by grep and lists them in the
build report — every caller inherits the enrichment through the one shared journaler,
which is the single home; no per-surface edit exists to forget). Axes: payload with
valid kind / missing kind / non-text kind / malformed jsonb — all four witnessed or
refused-as-expected. Not covered, stated honestly: refusals that never reach the
kernel (service-layer 409/422/timeouts) journal nothing, before and after — that is
the logging direction's territory (row 1486), not this delta's.

## 5. Amendment 2026-07-27 — the unbounded-storage premise was falsified in review

The fresh-context review of the first build (fc7f5d5) witnessed a 2 MiB string
supplied as `kind` stored VERBATIM in the journal column. The Basis section's framing
of the attempted kind as "a single, low-sensitivity vocabulary token" implicitly
assumed oversized/hostile strings would be refused before extraction; that is
backwards — refusal IS the path that reaches this extraction, so the refusal journal
is exactly where adversarial payloads arrive. Contrast s51's `artifact_too_large`
bound (1 MiB) on the artifact path. The maintainer's ratification (row 1487) was
given on the unamended text; this amendment narrows the delta (bounded verbatim
storage, NULL beyond the bound — strictly fewer bytes revealed than the ratified
reading), so it stays inside the fail-safe-additive class and the ratified privacy
envelope. Surfaced to the maintainer on the record at amendment time.

## License

Public Domain (The Unlicense).
