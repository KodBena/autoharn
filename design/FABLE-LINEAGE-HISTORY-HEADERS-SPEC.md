# FABLE-LINEAGE-HISTORY-HEADERS-SPEC — conforming HISTORY headers for s41/s42/s49

<!-- doc-attest-exempt: comment-only conformance spec, frozen 2026-07-22, awaiting the
maintainer's yes/no; consumer, named: the ./migrate header gate (_require_history_headers)
and the maintainer ratifying this exact edit. Removal condition: strike when superseded
by a polished live edition, if one is ever needed. -->

- **Status:** DRAFT FOR MAINTAINER RATIFICATION (yes/no). Fable-authored 2026-07-22.
- **What this licenses, exactly:** adding one `-- HISTORY: safe -- <grounds>` header line
  to each of three `kernel/lineage/` files, plus one wording repair inside s49 and one
  false-prose repair in `bootstrap/new-project.sh`. **No SQL statement changes. Zero
  semantic delta.** All three files are AUTHORED/SCRATCH-WITNESSED only — never applied
  to any world — so ADR-0005 Rule 8 (frozen records) does not bind them; CLAUDE.md's
  nobody-edits-kernel-without-a-ratified-spec rule does, hence this document.

## Why (the blocker, witnessed 2026-07-22)

`./migrate <panel-deployment> --dry-run` REFUSED at its header gate: s41, s42, s49 carry
no line matching `^-- HISTORY: (safe|requires accommodation)`. The gate is right to
refuse (an undeclared delta must not reach a rehearsal), and the declarations below are
grounded in a per-delta read of all thirteen missing deltas (s40–s52) against the
experience world's 1753 pre-existing rows, reported this same day by the rehearsal agent.

## The three edits (verbatim insertions)

1. **`kernel/lineage/s41-principal-bindings-and-relations.sql`** — top-of-file, after
   the existing title comment block:

   `-- HISTORY: safe -- every ledger-touching statement is ADD COLUMN IF NOT EXISTS (no
   DEFAULT) plus kind-shape CHECKs of the form ((kind IN (<new kinds>)) = (col IS NOT
   NULL)), vacuously true on every pre-existing row since no prior row carries a new
   kind; the file's own D-8 sub-header already states the per-mechanism grounds for its
   one internal design point and remains untouched.`

2. **`kernel/lineage/s42-row-hash-full-coverage.sql`** — top-of-file:

   `-- HISTORY: safe -- function/view re-issues and brand-new objects only; no
   history-validating statement (no ALTER of existing constraints, no CHECK over
   pre-existing rows, no SET NOT NULL, no DROP COLUMN) exists in this file.`

3. **`kernel/lineage/s49-journaler-overflow-guard.sql`** — its existing line 70 reads
   `-- HISTORY: NOT additive-safe by s43's own per-mechanism grounds (...)`, which uses
   CLAUDE.md's *class-ratification* vocabulary in the slot the migration gate reserves
   for the accommodations spec's *history-validation* vocabulary — two vocabularies in
   one word-slot, exactly the collision that trips the gate. Repair: **rename that
   existing line's prefix** from `-- HISTORY:` to `-- CLASS-RATIFICATION:` (its content
   is about fail-safe-class standing, and it stays, verbatim otherwise), and add the
   history declaration it never made:

   `-- HISTORY: safe -- this file is a single CREATE OR REPLACE FUNCTION; it validates
   nothing about existing rows (the accommodations spec's history-validation sense).
   Its class-ratification standing is a separate question, stated on the
   CLASS-RATIFICATION line below.`

4. **`bootstrap/new-project.sh`** (not kernel/, included for the same gate's honesty):
   the LINEAGE_CHAIN comment asserts s42 is "HISTORY: safe per its own header" — false
   against the file's on-disk text until edit 2 lands. The comment is corrected in the
   same commit so prose and file agree the moment both exist.

## Closure statement

Quantified over: the three files the migrate gate named on 2026-07-22 plus the one
`new-project.sh` comment that references them. Every edit above is a comment line;
`git diff` of the commit must show zero non-comment changes, and the committer verifies
this mechanically (`git diff -G'^[^-]' --stat` empty, or equivalent) and states the
check in the commit message. After the edits, `./migrate`'s header gate passes these
three files and the full rehearsal (scratch restore, byte-identity, .verify.sql, chain
walk) becomes runnable — rehearsal outcomes are that run's evidence, deliberately not
prejudged here.
