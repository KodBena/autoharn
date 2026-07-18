# Artifact store — content-addressed custody for artifacts that should be kept

<!-- doc-attest-exempt: build-basis spec; attestation rides witnessed delivery -->

**Status: Fable-authored 2026-07-18, ratified-to-author same date (maintainer, decision
queue; his framing verbatim: "a new table precisely for 'artifacts that should be
kept'"). Build basis for ONE kernel lineage delta (next free sNN at build time) + its
CLI verb. NOT class-ratified fail-safe — it adds a write path (a fifth SECURITY
DEFINER function beside s43's four), so the BUILD DISPATCH and the birth-chain entry
each remain the maintainer's ratification, per the standing contract. Per
runs-are-linear the delta is a file + scratch witnesses; it reaches reality in the
next world's birth chain.**

## The custody gap this closes

Ledger rows reference external artifacts by hash (charter registrations per
[design/FABLE-ROLE-CHARTERS-AND-BRIEFS-SPEC.md](FABLE-ROLE-CHARTERS-AND-BRIEFS-SPEC.md);
the s48 witness-ref `Artifact` arm, existence-unchecked by that delta's own LIMITS).
The hash guarantees identity but not retrievability: the referent lives outside the
database's custody domain, so a single database backup does not cover what its own
records rely on — the recurring records-duty gap (retrievability + integrity +
retention, ISO 15489-family; under the house bar this is a mechanism that happens to
discharge the duty, not paperwork). Git remains SECONDARY custody; this delta makes
the database primary.

## Mechanism

1. **`kernel.artifact`** — content-addressed: `hash` (sha256 hex, PK), `bytes`
   (bytea), `size` (bigint, derived server-side and CHECKed against `octet_length`),
   `media_type` (closed vocabulary v1: `text/markdown`, `text/plain`,
   `application/toml`, `application/json`; unknown → typed refusal), `registered_at`,
   `registered_by` (principal, resolved by the same s40/s43 attribution discipline as
   every write). Append-only: no UPDATE/DELETE grants to any non-owner role; the
   TRIGGER surface refuses both. Content-addressing makes re-registration of
   identical bytes an idempotent no-op that returns the existing hash (not an error,
   not a duplicate row).
2. **`kernel.artifact_write(p_payload jsonb)`** — the fifth SECURITY DEFINER
   function, same shape discipline as s43's four: typed verdict, refusal caught and
   journaled (a refused artifact write is a committed `write_refused` row, digest
   only — the bytes NEVER enter the refusal journal), server-side hash computation
   with a mismatch refusal if the caller also asserts a hash (assert-and-verify, the
   caller may not name a hash the server did not compute). **Size cap as a typed
   refusal**: `artifact_too_large` at 1 MiB v1 (a deliberate constant with its
   reason in the delta header: charters/TOMLs/specs are KB-scale; raising the cap is
   an amendment with a stated need, never a silent bump). Transport: bytes travel
   base64 in the jsonb payload; the CLI feeds via stdin/-f (the argstrlen wall and
   psql -c no-op both already witnessed — same fix shape as rows 1637/1643).
3. **`led artifact put <path>` / `led artifact get <hash> [--out <path>]` /
   `led artifact stat <hash>`** — the verb surface (template-side). `put` prints the
   hash; `get` verifies bytes-vs-hash on the way out and REFUSES to emit on mismatch
   (a corrupt store must fail loud, never serve silently wrong bytes); `stat` shows
   size/media/registrant without bytes.
4. **References stay hash-only.** No ledger column changes in this delta. Charter
   registration rows and s48 `artifact:` witness refs simply become RESOLVABLE
   in-db; making s48's artifact arm existence-CHECKED at write time is a separate,
   later delta (it tightens an existing surface — its own ratification), noted here
   as the anticipated successor, not smuggled in.
5. **Boundary**: NOT routed in v1. The store is reachable via `./legacy/led` (and
   any direct-psql world verb); adding `/artifacts/{hash}` routes is a route-table
   amendment under the read-surface spec's own re-ratification discipline — named
   as future work, out of scope here.

## Witnesses (scratch schema, both polarities, judge differential AGREE where the
delta touches surfaces the differential covers; per-claim, no umbrella)

- **WA1** put → hash printed; get → bytes byte-identical (round-trip); stat sane.
- **WA2** idempotent re-put of identical bytes → same hash, no second row, verdict
  says already-present.
- **WA3** size cap: a >1 MiB input → `artifact_too_large` typed refusal, journaled
  digest-only, nothing stored.
- **WA4** unknown media type → typed refusal naming the closed vocabulary.
- **WA5** asserted-hash mismatch → refusal (the server's own computation governs).
- **WA6** corruption drill (scratch only, as owner, simulating substrate fault):
  tamper a stored row's bytes directly; `get` refuses loudly on hash mismatch.
- **WA7** custody: `pg_dump` of the scratch pair, restore to a second scratch pair,
  `get` returns byte-identical content — the backup-covers-referents claim
  witnessed, not asserted.
- **WA8** charter integration: register a charter whose bytes are in the store;
  `role_charter.py show` resolves the referent in-db and reports drift against the
  working file exactly as before.

## Amendment — 2026-07-18, same day: what belongs in the store (the
essential-records criterion, post-hoc and saying so)

The maintainer's own words, kept because honesty about provenance is house law:
this delineation is "a *post-hoc rationalization* ... for why we do it this way and
what it suggests should be stored in the blob storage area. ... I stand by it none
the less, because I think it leans on something real." It is recorded as exactly
that — a criterion recognized after the design was drawn, which nonetheless
predicts the design and governs admission going forward.

The industry frame: records management's **essential records** (ARMA's current
term; historically "vital records") — the records the organization's EXECUTIVE
FUNCTION relies on to operate and to reconstitute itself, as distinct from the
products it produces. Beneath it sits ISO 15489's record/document cut: a record is
fixed evidence of a decision or transaction, maintained as evidence; a document is
mutable work product.

The ADR-0008 delineation (one fundamentum divisionis, MECE over "artifacts a world
touches"):

- **Essential records → the store.** An artifact is admitted when a ledger row's
  evidentiary force RELIES on retrieving these exact bytes: charters, commission
  texts, ratified specs, attestation bodies, witness transcripts cited by hash.
  Test: if the bytes vanished, would a ledger row's claim dangle? Yes → store.
- **Product artifacts → NOT the store.** The governed project's own outputs — code,
  builds, data, docs-as-deliverables — live in their own custody (git, build
  systems). The ledger may cite them (commit hashes, paths), but the citation is
  provenance, not reliance: the org's executive function survives their loss;
  reconstituting the PRODUCT is the product custody's job.

The v1 closed media vocabulary (markdown/plain/toml/json — governance registers,
no binaries) is this criterion enforced mechanically at the type level; widening it
is an amendment that must argue the essential-records test, not convenience.

## Build conditions

New lineage file + `.detect.sql` sibling per convention (fingerprint the artifact
table's existence + the write function's signature — mind the row-1657 search_path
lesson when writing the LIKE patterns); scratch-only harness wiring; NO edits to
`bootstrap/new-project.sh` (chain entry is the maintainer's act); NO edits to
shipped lineage files; led verb lands template-side with the legacy family covered.
