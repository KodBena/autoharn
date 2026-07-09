-- high_watermark_1.sql — the CURRENT USER-FACING kernel, derived from the lineage.
--
-- A convenience apply-artifact ONLY: it \ir-chains the frozen sNN records in order and owns
-- no DDL of its own (ADR-0012 P1 — the kernel body has one home per mechanism; never
-- retro-edit an sNN record, README §"Never retro-edit"). A future kernel change lands as a
-- new sNN delta PLUS a new high_watermark_N.sql that chains it; this file is then frozen too.
--
-- DELIBERATELY EXCLUDED: s18-criterion-principals.sql — the INSERT-only criterion-reviewer
-- principals are the project's own experiment apparatus (Study mode), not part of the kernel
-- a downstream user stands up. The study harness applies s18 explicitly on top of this file.
--
-- Usage (pass EVERY var explicitly; a throwaway db, never an evidence ledger):
--   psql -h <host> -d <throwaway-db> -v schema=<ledger-schema> -v kern=<kernel-schema> \
--        -v role=<author-role> -f kernel/lineage/high_watermark_1.sql
--
-- Cluster-global residue a dropdb does NOT remove: the <author-role> LOGIN role (s15).

\set ON_ERROR_STOP on
\ir s15-schema.sql
\ir s17-stamp-mechanism.sql
\ir s17-independence-vocabulary.sql
\ir s19-trigger-search-path.sql
