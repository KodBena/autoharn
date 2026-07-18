# Artifact witness refs become existence-checked — s48's named successor

<!-- doc-attest-exempt: build-basis spec; attestation rides witnessed delivery -->

**Status: Fable-authored 2026-07-18 (inside the freeze window), build basis for one
kernel lineage delta (next free sNN at build time). AWAITING MAINTAINER RATIFICATION
to build; birth-chain entry is separately his act. This is the successor both the
artifact-store spec ([FABLE-ARTIFACT-STORE-SPEC.md](FABLE-ARTIFACT-STORE-SPEC.md),
"anticipated successor, not smuggled in") and s48's own LIMITS section name.**

## Class statement

**2(a) fail-safe — ADDS a refusal, relaxes nothing, changes no existing semantics.**
Same class and same scope discipline as s48 (ledger row 1600 family): only the
review-witness position of close-family kinds; prose refs stay legal and unchecked.

## Defect

s48 made `row:<id>` witness tokens existence-checked and disclaimed the other two
arms in LIMITS. s51 gave the `artifact:` arm a place existence could be checked
against — `kernel.artifact` — but nothing checks it: a close may cite
`artifact:<hash>` for bytes nobody ever stored, the dangling-evidence-pointer shape
(the row-1665 essential-records criterion's own test) in the one position evidence
pointers are load-bearing.

## Mechanism

Extend the s48 trigger's surface (as a NEW lineage file re-issuing it, shipped files
untouched): where the review-witness field of the two close-family kinds contains
`artifact:<64-hex>` tokens, each hash must exist in `kernel.artifact` at insert
time. Missing → RAISE with a teaching message naming the hash, stating the store is
content-addressed, and giving the corrective form (`./legacy/led artifact put
<file>` first, then cite the printed hash). Malformed hex after the `artifact:`
prefix → the same refusal shape (a witness token that parses as neither arm is not
silently demoted to prose). Commit-arm tokens and prose refs: untouched, verified by
witness. Worlds whose chain carries s48 but not s51 are impossible forward (both
ride the same chain) and out of scope backward (runs are linear).

## Witnesses (scratch pair, both polarities, judge differential AGREE where covered
— if the differential does not cover the trigger surface, UNEXERCISED-with-reason
per the s51 precedent, never vacuous)

- **WX1** close citing `artifact:<hash-of-stored-bytes>` → accepted.
- **WX2** close citing `artifact:<absent 64-hex>` → refused, teaching names the
  hash and the put-first corrective; nothing written; refusal journaled.
- **WX3** close citing a malformed `artifact:zz…` token → refused, same shape.
- **WX4** scope: a non-close kind whose refs prose mentions `artifact:<absent>` →
  accepted (prose untouched); a close citing `row:<existing>` + commit arm →
  accepted (sibling arms unregressed).

## Build conditions

New lineage file + `.detect.sql` sibling (search_path-robust per row 1657); no
edits to shipped lineage, new-project.sh, law/, or the boundary; scratch-only
wiring; led CLI needs no change (the token grammar already exists).
