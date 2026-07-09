# kernel/lineage/ — the subject decision-ledger DDL lineage

The subject-side decision-ledger kernel, in lineage order, append-only. For the first
time this lineage is `ls`-legible AS a lineage (in the old repos it was scattered across
`epistemic-operator/harness/e*-build/`, invisible as one thing).

## The idiom switch — standalone generations, then additive deltas

- **s10 … s15 are STANDALONE full-schema generations.** Each `sNN-schema.sql` recreates
  the whole kernel from scratch at that generation (its own `principal`/`ledger`/triggers).
  You apply exactly ONE of them to stand up a kernel of that generation. s15 is the
  current generation (the s13 kernel + Ruling A's typed `antecedent` column, in an isolated
  opaque database).
- **s17+ are ADDITIVE DELTAS chained on s15.** They are `ALTER`/`CREATE OR REPLACE`
  increments applied ON TOP of an s15 base, never a second hand-copy of the ~342-line
  kernel body (ADR-0012 P1: one home per mechanism). Apply order for the current kernel:

  ```
  s15-schema.sql
    → s17-stamp-mechanism.sql          (stamp_secret + HMAC stamp columns + set_stamp)
    → s17-independence-vocabulary.sql  (self-review vocab + stamp-distinctness)
    → s18-criterion-principals.sql     (INSERT-only criterion-reviewer principals)
    → s19-trigger-search-path.sql      (forecloses the set_actor schema-literal class — findings 16/37/45)
  ```

- **Side entries.** `nla-schema.sql` is a catalog-isolated `nla` re-instantiation (a
  parallel domain profile, not a generation in the s-line). `s13-remediation-review-detail-
  truncate-guard.sql` is a targeted remediation delta on the s13 generation.
- **`high_watermark_1.sql` — the derived one-shot apply for the current USER-FACING kernel**
  (s15 → s17-stamp → s17-independence → s19). A convenience `\ir` chain that owns no DDL;
  it deliberately EXCLUDES `s18-criterion-principals.sql`, which is the project's own
  experiment apparatus (the study harness applies s18 explicitly on top). A future kernel
  delta lands as a new sNN file plus a new `high_watermark_N.sql`.

## Never retro-edit an `sNN` record (ADR-0005 Rule 8)

Each `sNN-schema.sql` is a point-in-time record. A defect discovered in a shipped
generation is foreclosed by a NEW dated increment (the s19 pattern), never by editing the
frozen file. That is why s13/s14/s15 still carry the historical `set_actor` `kernel.`
hardcode: they are frozen records; the live deployment applies s15 **plus s19**, and s19
is the structural foreclosure of that class.
