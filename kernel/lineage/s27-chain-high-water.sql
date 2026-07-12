-- s27 CHAIN HIGH-WATER WITNESS — closing the tail-deletion gap s26's own fixture named and filed
-- (tracker item s26-tail-deletion-witness; design decisions ratified in the ledger's decision
-- row 192, dated 2026-07-12 -- `./led show 192` or a direct read of the ledger prints it in
-- full). An ADDITIVE delta applied ON TOP of the s15/s17/s17b/s19/s20/s21/s22/
-- s23/s24/s25/s26 kernel (the established remediation-delta idiom), NOT a retro-edit of a frozen
-- sNN record (ADR-0005 Rule 8) and NOT a second hand-copy of any existing mechanism (ADR-0012 P1).
--
-- WHY (operator-side prose; NOT subject-visible): seen-red/s26-row-hash-chain-deletion/'s own
-- closure statement proved, empirically, that s26's row_hash chain detects every INTERIOR row
-- deletion (the next surviving row's predecessor-hash reference silently re-points past the gap
-- and its stored hash no longer matches) but is STRUCTURALLY BLIND to a TAIL deletion: deleting
-- the highest-id row leaves no later row whose predecessor lookup depended on it, so
-- `./verify-chain` reports INTACT over the silently-shortened chain with no diagnostic that a row
-- ever existed past the new head. That gap is the literature's TRUNCATION ATTACK against an
-- append-only log — a chain that authenticates "nothing between the ends was altered" but not
-- "nothing was cut off the end" — named in Schneier & Kelsey 1998 ("Cryptographic Support for
-- Secure Logs on Untrusted Machines") [web-verified 2026-07-12 against the published sources; ledger finding row 194], the
-- forward-secure aggregate-MAC literature (Ma & Tsudik, "A New Approach to Secure Logging",
-- DBSec 2008 / ACM TOS 2009 -- NOT CCS 2007, a common misattribution; FssAgg) [web-verified 2026-07-12 against the published sources; ledger finding row 194], Crosby & Wallach 2009 ("Efficient Data Structures for Tamper-Evident
-- Logging") [web-verified 2026-07-12 against the published sources; ledger finding row 194], and RFC 6962/9162's Certificate
-- Transparency signed tree heads, which exist BECAUSE a Merkle log's own internal consistency
-- proof says nothing about whether the log was truncated between two observations
-- [web-verified 2026-07-12 against the published sources; ledger finding row 194]. This delta is this project's in-domain
-- instance of that literature's own remedy shape: a monotonic witness of "how far the sequence
-- has reached", held OUTSIDE the audited table, that a truncation cannot roll back without
-- rewriting the witness too — and, per that same literature's unanimous verdict, this witness is
-- TRIPWIRE-grade, not a trust-root: it defends against a truncation that leaves the witness alone,
-- not against a schema-owner adversary who can rewrite both the ledger AND this table (same
-- adversary class s26's own LIMITS section already names as out of scope). The prior-arted
-- CLOSING move for that stronger adversary remains unchanged: the externally-held, human-signed
-- chain head (design/MAINT-GPG-TRUST-LAYER.md §4, Rung 3, Ceremony 3) — a witness whose custody
-- never touches this database at all. This delta narrows the gap between "detects mid-chain
-- tamper" and "detects truncation too" WITHOUT waiting on that human ceremony to fire every time.
--
-- SHAPE CHOSEN, AND WHY NOT THE ALTERNATIVE (ratified in decision row 192): a kernel-side ONE-ROW
-- monotonic high-water relation, `:kern.chain_high_water(max_id)`, bumped to
-- `GREATEST(max_id, NEW.id)` by a trigger that fires IN THE SAME TRANSACTION as the ledger INSERT
-- it witnesses — this is the PRIMARY shape, not the alternative the tracker item's own filing
-- floated (comparing against `pg_sequences.last_value`/the bigserial sequence's `last_value`
-- directly), because a Postgres sequence's `nextval()` is NOT transactional: it is consumed and
-- durably advanced the instant it is called, and does NOT roll back if the INSERT that called it
-- is later rolled back (`nextval()` is explicitly documented as non-transactional to avoid
-- blocking concurrent inserters on a shared counter). A rolled-back INSERT therefore leaves
-- `last_value` PERMANENTLY ahead of the highest row that actually committed — a legitimate,
-- routine gap (an aborted transaction, a constraint violation, an explicit ROLLBACK) that a naive
-- sequence-vs-ledger comparison would misreport as TAIL-DELETION-SUSPECT on every world that has
-- ever rolled back a single INSERT, which is not a rare event. The high-water TABLE this delta
-- adds is bumped by an ordinary trigger inside the SAME transaction as the row it witnesses, so a
-- rolled-back INSERT rolls the bump back with it — no false-positive class from this shape. The
-- sequence's `last_value` is NOT abandoned: `./verify-chain` reports it alongside the table-backed
-- witness as SECONDARY, EXPLAIN-NOT-FAIL corroboration (never causes a non-zero exit on its own;
-- see verify-chain.tmpl), because a sequence surviving row deletion (unlike a table row, which a
-- DELETE removes) is still informative when it agrees with the primary witness and is silently
-- explained, not silently trusted, when it does not.
--
-- WHY NO ADVISORY LOCK IS NEEDED HERE (contrast s26's own trigger, which DOES need one): s26's
-- `zz_set_row_hash` reads "the current last row" via `ORDER BY id DESC LIMIT 1` and had to
-- serialize concurrent inserts against each other to avoid embedding the wrong predecessor hash.
-- This delta's bump is `UPDATE chain_high_water SET max_id = GREATEST(max_id, NEW.id)` against a
-- single, pre-existing row — an ordinary UPDATE of one row is already serialized by Postgres's own
-- row-level locking (a second concurrent UPDATE against the same row blocks until the first
-- commits, then reads the first's committed value), so `GREATEST` is applied correctly under any
-- interleaving with no additional lock. Simpler than s26's mechanism because the invariant here
-- ("the highest id ever committed") does not depend on locating a specific PRIOR row by identity,
-- only on a monotonic maximum, which Postgres's standard row lock already makes race-free.
--
-- NAMED HAZARD, CLOSED (the commission's own instruction; CLAUDE.md's engineering-responsibility
-- corollary): the subject role (`:role`) MUST be able to SELECT this witness (an operator or
-- `./verify-chain` reading it needs no elevated privilege) but MUST NOT be able to lower or
-- rewrite it directly — a witness the audited role can roll back is not a witness. Closed exactly
-- as s17's `stamp_valid()` closes the symmetric read-side hazard (kernel/lineage/
-- s17-stamp-mechanism.sql, "SECURITY DEFINER recompute — the subject may CALL it, never READ the
-- secret"), mirrored here for the write side: `:role` is granted SELECT only on
-- `chain_high_water` (no INSERT/UPDATE/DELETE grant), and the ONLY path that ever writes the
-- table is `bump_chain_high_water()`, a SECURITY DEFINER trigger function owned by the schema
-- owner — a trigger function's default (non-SECURITY-DEFINER) execution runs with the INVOKING
-- role's privileges (`:role`, since `:role` is who performs the ledger INSERT that fires it), so
-- without SECURITY DEFINER the write would need a direct grant to `:role`, defeating the hazard
-- closure; WITH SECURITY DEFINER the function runs as its OWNER regardless of who inserts into
-- ledger, so `:role` gets the witness's protective bump for free without ever holding the
-- privilege to touch the table directly. Witnessed live, both polarities (the bump landing on
-- ordinary INSERT; a direct `:role`-as UPDATE refused) — see
-- `seen-red/s27-chain-high-water/red.txt`.
--
-- LIMITS (pre-registered, matching s26's own disclosure convention — a tripwire, not a
-- cryptographic fortress against every adversary class):
--   - A superuser or the schema owner can still `ALTER TABLE ... DISABLE TRIGGER`, lower
--     `chain_high_water.max_id` directly, or `DROP` the table outright — this delta does not
--     defend against an adversary with DDL/superuser privilege on the schema itself, the
--     identical adversary class s26's own LIMITS section already names as out of scope. What it
--     DOES defend against: a truncation performed by deleting ledger rows alone (the s26 fixture's
--     exact demonstrated attack), without ALSO touching this separate, out-of-band witness.
--   - This witness is a TRIPWIRE, not a trust root, per the truncation-attack literature's own
--     verdict (see WHY): it raises the cost and changes the shape of a convincing truncation (the
--     adversary must now also rewrite a second, separately-privileged relation), it does not make
--     truncation cryptographically infeasible the way an externally-held signed head does. The
--     actual closing move for a schema-owner-level adversary remains Ceremony 3
--     (design/MAINT-GPG-TRUST-LAYER.md §4, the GPG-signed chain head held outside the database).
--   - `./verify-chain`'s comparison (max ledger id actually walked vs this witness) can name a
--     SUSPECT tail deletion; it cannot, by itself, recover the deleted row's content — the row is
--     genuinely gone from the table. It proves that fewer rows survive than once existed, not what
--     they said.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 amendment):
--
--   - INVARIANT: `:kern.chain_high_water` carries exactly one row whose `max_id` is, at every
--     point after this delta applies, greater than or equal to the highest `id` any row in
--     `:schema.ledger` has EVER carried in this world (including ids of rows since deleted) —
--     bumped to `GREATEST(max_id, NEW.id)` by a trigger firing in the SAME transaction as each
--     ledger INSERT, so a rolled-back insert cannot leave the witness ahead of a row that never
--     durably existed, and a committed insert can never leave the witness behind a row that did.
--
--   - QUANTIFICATION UNIVERSE: this delta touches exactly one NEW relation (`chain_high_water`,
--     one row, one column of substance: `max_id`), one NEW SECURITY DEFINER trigger function
--     (`bump_chain_high_water`), and one NEW trigger on the EXISTING `:schema.ledger` table
--     (`zz_bump_chain_high_water`, an AFTER INSERT trigger, unlike s26's own BEFORE INSERT
--     `zz_set_row_hash` — the two never compete for BEFORE-trigger alphabetical ordering at all,
--     because this delta's logic depends only on `NEW.id`, which `nextval()` fixes before ANY
--     trigger runs, BEFORE or AFTER; ordering relative to `zz_set_row_hash` is therefore provably
--     immaterial, not merely assumed so). No existing
--     column, view, trigger, or grant is altered. The two "column-complete" views
--     (`ledger_current`, `countersigned_in_force`) carry no `chain_high_water` fact and need no
--     re-issue — this delta adds a SIBLING relation, not a ledger column, so s24/s26's own
--     view-reissue obligation does not apply here (named, not silently skipped: re-checked against
--     s26's own precedent and found genuinely inapplicable, not merely unconsidered). ENGINE — NONE
--     shipped in this delta (mirrors s23/s25/s26's own "ENGINE — NONE" disclosure): the witness
--     comparison lives in `bootstrap/templates/verify-chain.tmpl`, a standalone SQL-driven verb,
--     not an ASP/`engine/lp/*.lp` consumer. The EXISTING SQL/ASP differential
--     (`./judge`, `engine/ledger_differential.py`) is unaffected (it derives T_now facts from
--     `kind`/`status`/`supersedes`/etc., none of which this delta touches) and continues to AGREE —
--     scratch-witnessed as part of this delta's own acceptance (see
--     `seen-red/s27-chain-high-water/`).
--
--   - DENOMINATION: `max_id` is `bigint`, matching `ledger.id`'s own `bigserial` (`bigint`)
--     denomination exactly — no unit conversion, no proxy currency (ADR-0012 P1: a bound
--     denominated in the resource that actually detonates, never a proxy).
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): this delta ONLY adds a new
-- relation, a new SECURITY DEFINER function, and one new trigger that WRITES ONLY THE NEW
-- RELATION — nothing existing is relaxed (every prior trigger, view, constraint, grant, and
-- refusal on `:schema.ledger` is untouched; `chain_high_water` is derived-and-maintained
-- out-of-band, never read by any prior mechanism), no existing semantics changes. Class-ratified
-- per the maintainer's 2026-07-09 ruling once scratch-witnessed both polarities (an intact chain
-- with the witness in agreement; a tail-deleted chain with the witness AHEAD of the walked max,
-- reported SUSPECT; the role-cannot-lower refusal) with the SQL/ASP differential in AGREE — see
-- `seen-red/s27-chain-high-water/` — it enters the birth chain without a per-delta maintainer
-- question.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/s17/s20/.../s26):
-- schema/kern/role are psql variables so this delta is VALIDATED on a throwaway substrate before
-- any real apply.
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s27val -v kern=s27val_kernel -v role=s27val_rw \
--        -f s15-schema.sql -f s17-stamp-mechanism.sql -f s17-independence-vocabulary.sql \
--        -f s19-trigger-search-path.sql -f s20-obligation-grants-and-view-refresh.sql \
--        -f s21-session-aware-distinctness.sql -f s22-work-item-ledger.sql \
--        -f s23-per-invocation-stamp-token.sql -f s24-declared-event-time.sql \
--        -f s25-commission-kind.sql -f s26-row-hash-chain.sql -f s27-chain-high-water.sql
--   REAL: NEVER applied to any existing world by this delta's own authoring act (maintainer
--   ruling 2026-07-11, "runs are strictly linear"). This delta reaches reality by entering the
--   NEXT world's birth chain: `bootstrap/new-project.sh`'s `LINEAGE_CHAIN` (this same commission)
--   applies it automatically to every `--new-world` scaffold from here on. No genesis-style
--   scaffold seeding step is needed (contrast s26's `chain_genesis`, which needs a random
--   world-birth secret provisioned once): the singleton `chain_high_water` row is created by THIS
--   DDL itself (`INSERT ... ON CONFLICT DO NOTHING`, idempotent), starting at `max_id = 0`, which
--   is already correct for an empty birth-chain ledger (no row has ever carried an id yet). It was
--   authored and scratch-witnessed on scratch schema pairs in the TOY db only — NOT applied to any
--   live schema by this pass.
-- Run as the schema owner (bork). Idempotent (CREATE TABLE IF NOT EXISTS; INSERT ... ON CONFLICT
-- DO NOTHING; CREATE OR REPLACE FUNCTION; DROP/CREATE TRIGGER).

\if :{?schema}
\else
  \set schema public
\endif
\if :{?kern}
\else
  \set kern kernel
\endif
\if :{?role}
\else
  \set role vsr_rw
\endif

-- ============================================================================================
-- chain_high_water — the one-row, kernel-side monotonic witness. Bumped to GREATEST(max_id,
-- NEW.id) inside the same transaction as each ledger INSERT; NEVER lowered by anything this
-- delta grants :role. Seeded to max_id=0 by this DDL itself (idempotent) -- correct starting
-- value for a birth-chain ledger with no rows yet.
-- ============================================================================================
CREATE TABLE IF NOT EXISTS :"kern".chain_high_water (
    only_one boolean PRIMARY KEY DEFAULT true CHECK (only_one),
    max_id   bigint  NOT NULL DEFAULT 0
);
INSERT INTO :"kern".chain_high_water (only_one, max_id) VALUES (true, 0)
  ON CONFLICT (only_one) DO NOTHING;

COMMENT ON TABLE :"kern".chain_high_water IS
  'The one-row monotonic high-water witness (kernel/lineage/s27-chain-high-water.sql):
   max_id = the highest ledger.id ever committed in this world, including ids of rows since
   deleted -- a tail deletion leaves this value AHEAD of the highest surviving ledger id, which
   ./verify-chain reports as TAIL-DELETION-SUSPECT. Bumped by bump_chain_high_water() (SECURITY
   DEFINER; :role has SELECT only, never write) in the same transaction as the ledger insert it
   witnesses, so a rolled-back insert rolls the bump back too -- no false-positive class from a
   routine rollback (contrast comparing against the ledger id sequence''s last_value, which is
   NOT transactional and does advance permanently on a rolled-back insert; see this file''s own
   header). TRIPWIRE-grade against a truncation that leaves this table alone; does NOT defend
   against a schema-owner-level adversary who rewrites this table too -- Ceremony 3''s externally
   held signed chain head (design/MAINT-GPG-TRUST-LAYER.md §4) remains the closing move for that
   adversary class.';

-- No GRANT of INSERT/UPDATE/DELETE to :role: the subject may read the witness (it is not a
-- secret -- unlike stamp_secret -- its value is exactly "the highest id ever seen", already
-- inferable from the subject's own ledger reads) but may never lower or rewrite it directly.
GRANT SELECT ON :"kern".chain_high_water TO :"role";

-- ============================================================================================
-- bump_chain_high_water() -- SECURITY DEFINER: runs as the schema owner (this DDL's invoker)
-- regardless of who performs the ledger INSERT that fires it, so :role's ordinary write to
-- ledger can trigger a write to chain_high_water without :role ever holding a grant to write
-- chain_high_water directly (mirrors s17-stamp-mechanism.sql's stamp_valid() read-side closure,
-- applied here to the write side -- see this file's own NAMED HAZARD note above).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"kern".bump_chain_high_water() RETURNS trigger LANGUAGE plpgsql
    SECURITY DEFINER SET search_path = :"kern", pg_temp AS $fn$
BEGIN
  UPDATE chain_high_water SET max_id = GREATEST(max_id, NEW.id);
  RETURN NEW;
END; $fn$;

DROP TRIGGER IF EXISTS zz_bump_chain_high_water ON :"schema".ledger;
CREATE TRIGGER zz_bump_chain_high_water AFTER INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"kern".bump_chain_high_water();
