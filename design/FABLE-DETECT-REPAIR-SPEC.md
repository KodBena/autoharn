# Detect-sibling repair — the lineage-head walk tells the truth again

<!-- doc-attest-exempt: build-basis spec; attestation rides witnessed delivery -->

**Status: Fable-authored 2026-07-18 (inside the freeze window), build basis.
AWAITING MAINTAINER RATIFICATION — the edits touch `kernel/lineage/*.detect.sql`
siblings (diagnostic surface, not semantics: no shipped `sNN-*.sql` delta file
changes, no trigger/function/table/view definition changes anywhere). Defects
witnessed at the omega-lab birth, ledger row 1657.**

## The two witnessed defects

1. **The s20 detect can never read true post-s43.**
   `s20-obligation-grants-and-view-refresh.detect.sql` probes an INSERT grant on
   `countersign_obligation`; s43's write-boundary revocation removes every such
   grant, so on every world whose chain includes s43 the walk stops there —
   `/meta`'s `lineage_head` and `migrate_core`'s manifest walk report
   `high_watermark_1` forever, on every current and future world.
2. **The s50 detect false-negatives under the standard search_path.** Its LIKE
   pattern assumes schema-qualified `pg_get_viewdef` output; with the schema on
   `search_path` (as every real caller sets it) the view renders unqualified and
   the pattern never matches, while the s50 shape is genuinely live.

## Mechanism

- **s20 detect**: re-fingerprint on facts s43 preserves — the delta's own durable
  observables (its view/table surface and the SELECT-side grants the role retains),
  never a write-privilege probe. The builder reads s20 and s43 in full and states,
  in the detect's header comment, WHY the chosen observables survive every later
  delta in the shipped chain (the enumerated universe: s21–s51 as of this spec).
- **s50 detect**: make the pattern search_path-robust — match both qualified and
  unqualified renderings (or normalize via `pg_get_viewdef` under a pinned
  search_path before matching). Same header-comment obligation.
- **Sweep, then stop**: run every OTHER `.detect.sql` in the chain against a fresh
  scratch birth at head; any additional detect reading false on a world where its
  delta is provably live is fixed under this same spec IF the fix is
  fingerprint-only, and REPORTED (not fixed) if it would need anything beyond the
  detect file. The report enumerates every detect checked with its verdict —
  per-file, no umbrella.
- **Readers unchanged**: `/meta` and `migrate_core` need no code change — the walk
  is correct once the fingerprints are; verify rather than edit, and report if that
  assumption fails.

## Witnesses

- **WD1** fresh scratch birth at head: every detect in the chain reads true;
  `/meta` (scratch-served) reports the actual head. Before/after captured — the
  pre-fix walk stopping at high_watermark_1 reproduced first.
- **WD2** each fixed detect on a world genuinely LACKING its delta (a mid-chain
  scratch or the detect run against a pre-delta schema state) → reads false (the
  fingerprint still discriminates; a detect that reads true everywhere is no
  detect).
- **WD3** search_path robustness: the s50 detect true under both a bare and a
  schema-including search_path on the same live world.

## Build conditions

Only `.detect.sql` files change (plus the report). No shipped delta files, no
readers unless WD1 falsifies the readers-unchanged assumption (then STOP and
report). Scratch-only; zero residue; per-claim witnessing.
