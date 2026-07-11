-- s26 ROW-HASH CHAIN — the anchored ledger's kernel half (design/GPG-TRUST-LAYER.md §4, Rung 3).
-- An ADDITIVE delta applied ON TOP of the s15/s17/s17b/s19/s20/s21/s22/s23/s24/s25 kernel (the
-- established remediation-delta idiom), NOT a retro-edit of a frozen sNN record (ADR-0005 Rule 8)
-- and NOT a second hand-copy of any existing mechanism (ADR-0012 P1: one home per mechanism).
--
-- WHY (operator-side prose; NOT subject-visible — only the catalog objects inside the opaque db
-- are): design/GPG-TRUST-LAYER.md §4's own framing, verbatim: "tamper-evident happens-before is
-- owned by no logic family — it is cryptography's job." Every existing kernel mechanism proves
-- WHO wrote a row (stamp_*, s17/s23) and WHETHER two rows may legally reference each other
-- (validate_enacts/review/amends/answers/work_item, s15/s22) — none of them proves that the
-- SEQUENCE of rows itself has not been retroactively altered by someone with schema-owner
-- privilege (a superuser could UPDATE a historical row's `statement` directly, bypassing every
-- trigger; `append_only_row` (s15) refuses an UPDATE/DELETE through the granted `:role`, but a
-- superuser is not bound by a trigger it can also drop). A hash CHAIN closes that gap the way a
-- blockchain's simplest form does: every row's `row_hash` commits to its own content AND to the
-- immediately preceding row's `row_hash`, so altering any historical row's content (or deleting
-- it, or reordering it) changes that row's own hash, which then mismatches every LATER row's
-- embedded predecessor-hash — the alteration is detectable from the FIRST altered row onward, by
-- anyone who re-walks the chain, without needing to trust the database at all (only the arithmetic).
--
-- SHA-256 CHOICE (verified against this toy db before assuming, per this commission's own
-- instruction): PostgreSQL 18.4 here ships a BUILT-IN `sha256(bytea) RETURNS bytea` core SQL
-- function (added PostgreSQL 11, no extension) — confirmed live: `SELECT sha256('abc'::bytea)`
-- returns the correct digest with no `CREATE EXTENSION`. `pgcrypto` IS also installed on this
-- toy db (`SELECT extname FROM pg_extension` shows it, already required by s17's HMAC), but this
-- delta does NOT depend on it — the built-in core function is strictly sufficient and carries one
-- fewer extension dependency than reusing pgcrypto's `digest()` would, so it is preferred (a
-- smaller footprint is not "for now" scope-shaving — ADR-0012 P7/P8's no-scale-excuse posture
-- read the other direction: depending on LESS than what is available, when less is sufficient, is
-- the honest minimum, not a corner cut).
--
-- CANONICAL SERIALIZATION (the one home, `compute_row_hash()` below — called by BOTH the insert
-- trigger and `./verify-chain`'s walk, so there is exactly ONE implementation of "what a row's
-- content means" (ADR-0012 P1/P7: two independent re-derivations of the same canonicalization is
-- the "two writers of one truth" cancer, here foreclosed by construction, not by discipline).
-- Every ledger column this generation carries (s15 through s24; s25 added no column), plus the
-- predecessor's row_hash as a final field, each rendered through `hc()` (below) into a
-- LENGTH-PREFIXED, presence-tagged token — `N:` for SQL NULL, `V<char-length>:<value>` for a
-- present value (including the empty string) — and concatenated directly (the length prefix
-- makes the encoding self-delimiting, so no separator between tokens is needed for injectivity;
-- one is still inserted, `\x1f`, purely for human-eyeball legibility in a printed digest).
--
-- INJECTIVITY, FOUND BROKEN AND FIXED BEFORE THIS SHIPPED (an out-of-frame hack-rationalization
-- audit caught this before the commission was reported done — CLAUDE.md's engineering-
-- responsibility corollary in action, not a corner routed around). An EARLIER version of this
-- function joined `coalesce(field, '')` values with the `\x1f` delimiter and no length prefix,
-- and claimed (wrongly) that this was merely "not collision-resistant against a schema-owner
-- adversary who already has stronger attacks available." That framing does not survive scrutiny:
-- `coalesce(rationale, '')` maps BOTH `rationale IS NULL` and `rationale = ''` — two genuinely
-- different, SQL-observable facts — to the identical serialized token, a real hash COLLISION, not
-- merely an adversarial-hardening gap. Worse: no CHECK constraint anywhere in this table's
-- lineage forbids an ordinary `text` column from containing a literal `\x1f` byte, so the
-- "delimiter cannot appear under normal operation" premise was itself unenforced. Concretely, the
-- collision let a schema-owner tamper (`UPDATE ledger SET rationale = '' WHERE id = N AND
-- rationale IS NULL`, bypassing `append_only_row` exactly as the LIMITS section already concedes
-- is possible) produce ZERO change to the stored `row_hash` at row N and EVERY downstream row —
-- defeating not just the chain walk but the §4 SIGNED HEAD backstop this design names as the
-- actual closing move, for free, with no recomputation needed anywhere. The length-prefixed
-- encoding below closes this: two different column-value tuples can no longer serialize to the
-- same string (a standard self-delimiting/prefix-free code, the same principle netstrings and
-- Bencode byte-strings use), so the chain's detection guarantee holds against this class, not
-- merely against a delimiter an adversary is assumed not to type.
--
-- TIMEZONE-SAFE TIMESTAMPS (a hazard caught and closed here, not left for `./verify-chain` to
-- trip over later — CLAUDE.md's engineering-responsibility corollary): `ts::text` and
-- `event_declared_ts::text` render in the CONNECTION's session timezone, which can legitimately
-- differ between the moment a row is inserted (the intercepted psql session) and the moment
-- `./verify-chain` later re-walks the chain (a different connection, possibly a different
-- operator timezone) — a spurious "chain broken" from nothing but a TZ-offset string differing
-- while the underlying instant is identical. `compute_row_hash()` uses `extract(epoch FROM ...)`
-- instead — a timezone-independent numeric instant — for both timestamp columns, so the
-- canonicalization is honest about what actually changed vs. what merely rendered differently.
--
-- GENESIS SEED (a world-birth nonce, NOT a secret — contrast s17's `stamp_secret`, which the
-- subject role must NEVER read). The first row's "predecessor" is `:kern.chain_genesis.seed`, a
-- random value the SCAFFOLD provisions once per world (mirrors `stamp_secret`'s idempotent
-- `openssl rand -hex 32` seeding block in `bootstrap/new-project.sh`, but grantable to `:role`
-- for SELECT — the genesis value's job is only to make two worlds' row-1 hashes differ even when
-- row 1's content is byte-identical between them; it carries no confidentiality requirement, so
-- restricting subject SELECT the way `stamp_secret` does would add ceremony with no security
-- benefit). Absent a provisioned seed, the trigger REFUSES loudly (RAISE EXCEPTION) rather than
-- inventing one silently — a world with no genesis seed cannot begin a chain at all, and that is
-- the correct failure, not a `NULL`-seeded fallback.
--
-- CONCURRENCY RACE, FOUND AND CLOSED (not merely flagged — a hazard within reach of the work
-- being touched, CLAUDE.md's corollary). Under PostgreSQL, a `bigserial` column's `nextval()` is
-- consumed BEFORE a `BEFORE INSERT` trigger runs, so `NEW.id` is already assigned when this
-- trigger reads "the current last row" as its predecessor. Two genuinely concurrent INSERTs (T1
-- destined for id=10, T2 destined for id=11) could each have their trigger's predecessor-SELECT
-- execute before the other commits, and — depending on commit interleaving under READ COMMITTED
-- — T1's trigger could observe T2's ALREADY-COMMITTED row (id=11) as "the last row", embedding a
-- HIGHER id's hash into a LOWER id's predecessor field: the chain would not merely be broken, it
-- would be built wrong from the start, in a way `./verify-chain`'s ascending walk could not even
-- describe sensibly. Closed here with `pg_advisory_xact_lock(hashtext(TG_TABLE_SCHEMA ||
-- '.row_hash_chain')::bigint)` at the top of the trigger: every INSERT on this world's ledger now
-- serializes against every other concurrent INSERT on the SAME world's ledger (the lock key is
-- schema-scoped via `TG_TABLE_SCHEMA`, so concurrent writers in DIFFERENT worlds never contend
-- with each other), released automatically at transaction end. The cost is one lock acquisition
-- per ledger write — negligible next to the write itself, and the ledger's own operating mode
-- (CLAUDE.md: "Record as you go — one row at the moment of the act") is already low-concurrency
-- by design, so this lock is rarely, if ever, actually contended; it is cheap insurance against a
-- rare-but-real race, not a throughput compromise.
--
-- LIMITS (pre-registered, matching s17's own disclosure convention — a tripwire, not a
-- cryptographic fortress against every adversary class):
--   - A superuser (or the schema owner) can still `DROP TRIGGER zz_set_row_hash`, alter a row,
--     and re-run a script that recomputes a consistent-looking chain from that point forward —
--     this delta does not defend against an adversary with DDL privilege on the schema itself.
--     What it DOES defend against: retroactive alteration that does NOT also forge every
--     downstream row_hash, AND — the actual closing move, per spec §4 — a chain whose HEAD is
--     separately GPG-signed by a human key that lives OUTSIDE the database entirely (the
--     "signed head" ceremony, FAQ'd, `./verify-chain --head`). From the moment a head is signed,
--     ANY retroactive alteration — including a superuser silently rewriting rows AND recomputing
--     every downstream hash to match — breaks the chain against a head an external, unforgeable
--     signature vouches for. "Append-only by trigger" becomes "append-only or provably broken",
--     exactly the spec's own words.
--   - The serialization's injectivity (no two different column-value tuples hash the same,
--     including the NULL-vs-empty-string case) is holding as designed — see CANONICAL
--     SERIALIZATION above for the length-prefixed encoding that guarantees it and the specific
--     collision an earlier version of this file had and closed before shipping. What remains
--     genuinely unclaimed: SHA-256 preimage/collision resistance against an adversary who can
--     choose arbitrary column CONTENT (not structure) — the same bound every SHA-256 use in this
--     project already carries, not a gap specific to this delta.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 amendment):
--
--   - INVARIANT: every `ledger` row, from the moment this delta applies onward, carries a
--     NOT-NULL `row_hash` that is the SHA-256 (hex-encoded) of a canonical, delimiter-joined,
--     NULL-coalesced serialization of every OTHER column this generation carries, concatenated
--     with the immediately-preceding row's `row_hash` (or the world's genesis seed for the first
--     row) — computed by ONE shared function (`compute_row_hash`), called identically by the
--     insert-time trigger and by `./verify-chain`'s read-only walk, so there is no second
--     re-derivation of "what a row's content means" to drift from the first.
--
--   - QUANTIFICATION UNIVERSE — enumerated by re-reading every column `ledger` carries as of
--     s24 (s25 added no column, confirmed by its own closure statement), mirroring s24's own
--     enumeration method:
--       * EVERY ledger column EXCEPT `row_hash` itself is included in the serialization (id, ts,
--         session, kind, statement, rationale, status, evidence, confidence, supersedes, refs,
--         concern, enacts, actor, regards, amends, amends_scope, answers, stamp_session,
--         stamp_agent, stamp_ts, stamp_hmac, stamp_verified, work_slug, work_title,
--         work_depends_on, work_resolution, work_witness, stamp_invocation, event_declared_ts) —
--         `row_hash` cannot include itself (it is what is being computed) and is the only column
--         deliberately excluded, named here rather than silently omitted.
--       * VIEWS — `ledger_current` and `countersigned_in_force` (the s20/s22/s23/s24
--         "column-complete" class) GAIN `row_hash`, APPENDED AT THE END, HERE, for the same
--         reason s24 had to append `event_declared_ts`: `CREATE OR REPLACE VIEW` forbids
--         reordering/renaming existing columns without dropping the GRANT. `review_gap`,
--         `question_status`, `work_item_current`, `work_item_violations`,
--         `review_stamp_distinctness` — re-verified NOT members of this class, for the identical
--         reasons s24's own enumeration already gave for each (none does general ledger-row
--         column passthrough that a hash-chain fact belongs on); not silently skipped.
--       * TRIGGERS — `zz_set_row_hash` is the ONLY new trigger; it reads (never writes) every
--         prior trigger's OUTPUT via `NEW`, and its name is chosen to sort alphabetically LAST
--         among this table's `BEFORE INSERT` triggers (`set_actor`, `set_stamp`, `validate_amends`,
--         `validate_answers`, `validate_enacts`, `validate_review`, `validate_work_item`, then
--         `zz_set_row_hash`) — PostgreSQL fires same-timing triggers on one table in trigger-name
--         alphabetical order, so this is the mechanism (not a comment-only convention) that
--         guarantees `row_hash` is computed from every OTHER trigger's final, settled NEW values
--         (in particular `set_stamp`'s stamp_* columns), never a stale pre-stamp snapshot. No
--         existing trigger definition is touched.
--       * ENGINE — NONE shipped in this delta (mirrors s23/s25's own "ENGINE — NONE" disclosure):
--         `./verify-chain` is a standalone SQL-driven verb (bootstrap/templates/
--         verify-chain.tmpl), not an ASP/`engine/lp/*.lp` consumer — a future
--         `chain_integrity`-shaped ASP predicate is a plausible FOLLOW-ON, filed as a possibility,
--         not built or claimed built. The EXISTING SQL/ASP differential (`./judge`,
--         `engine/ledger_differential.py`) is unaffected by this delta (it derives T_now facts
--         from `kind`/`status`/`supersedes`/etc., none of which this delta touches) and continues
--         to AGREE — scratch-witnessed as part of this delta's own acceptance (see
--         `seen-red/s26-row-hash-chain/`).
--     So the "column-complete" class has EXACTLY TWO members this delta must re-issue (both done
--     here); the trigger-ordering fact is the mechanism the invariant depends on, stated
--     explicitly rather than left implicit in trigger-naming convention alone.
--
--   - DENOMINATION: `row_hash` is `text` (64 lowercase hex characters, matching `stamp_hmac`'s
--     own hex-text denomination — s17's precedent — rather than `bytea`, so the column is
--     directly human-legible and directly comparable to a Python `hashlib.sha256(...).hexdigest()`
--     string with no decode step on either side of `./verify-chain`). The genesis seed
--     (`:kern.chain_genesis.seed`) is likewise `text` (hex, from `openssl rand -hex 32`, matching
--     `stamp_secret`'s own generation command though NOT its confidentiality — see GENESIS SEED
--     above for why the two are grantable differently).
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): this delta ONLY adds a
-- column, a genesis-seed table, a shared hash function, and one new trigger that fires last and
-- WRITES ONLY THE NEW COLUMN — nothing existing is relaxed (every prior trigger, view, constraint,
-- and refusal is untouched; `row_hash` is derived-and-appended, never read by any prior
-- mechanism), no existing semantics changes. Class-ratified per the maintainer's 2026-07-09
-- ruling once scratch-witnessed both polarities (an intact chain verifies; a surgically altered
-- historical row breaks the chain AT THE ALTERED ROW) with the SQL/ASP differential in AGREE —
-- both done, this same commission (see `seen-red/s26-row-hash-chain/`) — it enters the birth
-- chain without a per-delta maintainer question.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/s17/s20/s22/s23/s24/s25):
-- schema/kern/role are psql variables so this delta is VALIDATED on a throwaway substrate before
-- any real apply.
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s26val -v kern=s26val_kernel -v role=s26val_rw \
--        -f s15-schema.sql -f s17-stamp-mechanism.sql -f s17-independence-vocabulary.sql \
--        -f s19-trigger-search-path.sql -f s20-obligation-grants-and-view-refresh.sql \
--        -f s21-session-aware-distinctness.sql -f s22-work-item-ledger.sql \
--        -f s23-per-invocation-stamp-token.sql -f s24-declared-event-time.sql \
--        -f s25-commission-kind.sql -f s26-row-hash-chain.sql
--     (then provision the genesis seed as `bootstrap/new-project.sh` does — see that script's
--     --new-world block — before the first ledger INSERT, or the trigger refuses loudly.)
--   REAL: NEVER applied to any existing world by this delta's own authoring act (maintainer
--   ruling 2026-07-11, "runs are strictly linear"). This delta reaches reality by entering the
--   NEXT world's birth chain: `bootstrap/new-project.sh`'s `LINEAGE_CHAIN` (this same commission)
--   applies it automatically to every `--new-world` scaffold from here on, immediately followed by
--   the genesis-seed provisioning step (this same commission's addition to that script). It was
--   authored and scratch-witnessed on scratch schema pairs in the TOY db only — NOT applied to
--   any live schema by this pass.
-- Run as the schema owner (bork). Idempotent (ADD COLUMN IF NOT EXISTS; CREATE OR REPLACE
-- FUNCTION/VIEW; DROP/CREATE TRIGGER; SET NOT NULL is a documented no-op if already set, and
-- fails LOUDLY — never silently — if a legacy NULL row is somehow present, which never happens on
-- the intended empty-ledger birth-chain application).

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
-- GENESIS SEED — a world-birth nonce (NOT a secret; SELECT-grantable to :role, contrast
-- stamp_secret). Provisioned by the scaffold (openssl rand -hex 32), never by this DDL.
-- ============================================================================================
CREATE TABLE IF NOT EXISTS :"kern".chain_genesis (
    only_one  boolean PRIMARY KEY DEFAULT true CHECK (only_one),
    seed      text NOT NULL,
    seeded_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT ON :"kern".chain_genesis TO :"role";
-- No INSERT/UPDATE/DELETE grant to :role: the seed is written once, by the scaffold, as the
-- schema owner -- the subject can read it (it is embedded into every row_hash and is not secret)
-- but cannot rewrite it.

COMMENT ON TABLE :"kern".chain_genesis IS
  'The one-row world-birth seed row_hash''s genesis computation hashes against, for this world''s
   very first ledger row (kernel/lineage/s26-row-hash-chain.sql). NOT a secret (contrast
   kernel.stamp_secret): its only job is making two worlds'' row-1 hashes differ even on
   byte-identical content; SELECT is granted to the subject role.';

-- ============================================================================================
-- row_hash COLUMN
-- ============================================================================================
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS row_hash text;

COMMENT ON COLUMN :"schema".ledger.row_hash IS
  'SHA-256 (hex) of this row''s own content (every OTHER column, canonically serialized -- see
   compute_row_hash()) concatenated with the predecessor row''s row_hash (or the world''s genesis
   seed for the first row). Computed by the zz_set_row_hash trigger at INSERT; never writer-set,
   never NULL from this delta onward. design/GPG-TRUST-LAYER.md Rung 3: walked by ./verify-chain,
   which reports the FIRST row where the stored value disagrees with a fresh recomputation --
   proof that no row between the genesis seed and that point was retroactively altered.';

-- ============================================================================================
-- hashfield() -- the length-prefixed, presence-tagged token that makes compute_row_hash()'s
-- serialization INJECTIVE (see header's INJECTIVITY note for the collision this closes). 'N:'
-- for SQL NULL; 'V<char-length>:<value>' for a present value (including ''). Self-delimiting: a
-- reader consumes exactly the declared number of characters, so no field's content -- however
-- constructed -- can be mistaken for a token boundary. LANGUAGE sql IMMUTABLE: a pure function
-- of its one input.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".hashfield(v text) RETURNS text LANGUAGE sql IMMUTABLE AS $fn$
  SELECT CASE WHEN v IS NULL THEN 'N:' ELSE 'V' || length(v)::text || ':' || v END;
$fn$;

-- ============================================================================================
-- compute_row_hash() -- the ONE home of "what a row's content means" (ADR-0012 P1/P7). Called
-- BOTH by the insert trigger below AND by ./verify-chain's read-only walk -- never re-derived.
-- LANGUAGE sql (not plpgsql): a pure expression of its two inputs, no control flow needed.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".compute_row_hash(r :"schema".ledger, predecessor_hash text)
    RETURNS text LANGUAGE sql IMMUTABLE
    SET search_path = :"schema", pg_temp AS $fn$
  SELECT encode(sha256(convert_to(
    array_to_string(ARRAY[
      hashfield(r.id::text),
      hashfield(extract(epoch FROM r.ts)::text),               -- timezone-safe (see header WHY)
      hashfield(r.session),
      hashfield(r.kind),
      hashfield(r.statement),
      hashfield(r.rationale),
      hashfield(r.status),
      hashfield(r.evidence),
      hashfield(r.confidence),
      hashfield(r.supersedes::text),
      hashfield(r.refs),
      hashfield(r.concern),
      hashfield(array_to_string(r.enacts, ',')),
      hashfield(r.actor::text),
      hashfield(r.regards::text),
      hashfield(r.amends::text),
      hashfield(r.amends_scope),
      hashfield(r.answers::text),
      hashfield(r.stamp_session),
      hashfield(r.stamp_agent),
      hashfield(r.stamp_ts::text),
      hashfield(r.stamp_hmac),
      hashfield(r.stamp_verified::text),
      hashfield(r.work_slug),
      hashfield(r.work_title),
      hashfield(r.work_depends_on),
      hashfield(r.work_resolution),
      hashfield(r.work_witness),
      hashfield(r.stamp_invocation),
      hashfield(extract(epoch FROM r.event_declared_ts)::text),
      hashfield(predecessor_hash)
    ], E'\x1f'),
  'utf8')), 'hex');
$fn$;

-- ============================================================================================
-- zz_set_row_hash TRIGGER -- fires BEFORE INSERT, LAST among this table's BEFORE INSERT triggers
-- by alphabetical trigger-name ordering (see closure statement's TRIGGERS section for why this is
-- a mechanism, not a convention). Serializes concurrent inserts against a per-schema advisory
-- lock (the concurrency race closed, per header WHY).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".zz_set_row_hash() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_predecessor text;
BEGIN
  PERFORM pg_advisory_xact_lock(hashtext(TG_TABLE_SCHEMA || '.row_hash_chain')::bigint);

  SELECT row_hash INTO v_predecessor FROM ledger ORDER BY id DESC LIMIT 1;
  IF v_predecessor IS NULL THEN
    SELECT seed INTO v_predecessor FROM chain_genesis LIMIT 1;
    IF v_predecessor IS NULL THEN
      RAISE EXCEPTION 'row_hash chain: no world-birth seed in %.chain_genesis -- the scaffold must provision one (openssl rand -hex 32) before the first ledger write; see kernel/lineage/s26-row-hash-chain.sql and bootstrap/new-project.sh''s --new-world seeding block.', TG_TABLE_SCHEMA;
    END IF;
  END IF;

  NEW.row_hash := compute_row_hash(NEW, v_predecessor);
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS zz_set_row_hash ON :"schema".ledger;
CREATE TRIGGER zz_set_row_hash BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".zz_set_row_hash();

-- NOT NULL, enforced last (so the ADD COLUMN above is always legal even if re-run against a
-- schema mid-migration): idempotent no-op if already NOT NULL; fails LOUDLY if any legacy NULL
-- row is present (never true on the intended empty-ledger birth-chain application -- ADR-0002,
-- fail loud rather than silently coerce a historical NULL into a fabricated hash).
ALTER TABLE :"schema".ledger ALTER COLUMN row_hash SET NOT NULL;

-- ============================================================================================
-- s20/s22/s23/s24 LESSON RE-APPLIED: ledger_current + countersigned_in_force GAIN row_hash,
-- APPENDED AT THE END. Explicit column lists throughout -- never `l.*`. Column list = s24's exact
-- list + l.row_hash.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".ledger_current
    WITH (security_invoker = true) AS
SELECT l.id, l.ts, l.session, l.kind, l.statement, l.rationale, l.status, l.evidence,
       l.confidence, l.supersedes, l.refs, l.concern, l.enacts, l.actor, l.regards,
       l.amends, l.amends_scope, l.answers,
       l.stamp_session, l.stamp_agent, l.stamp_ts, l.stamp_hmac, l.stamp_verified,
       l.work_slug, l.work_title, l.work_depends_on, l.work_resolution, l.work_witness,
       l.stamp_invocation, l.event_declared_ts, l.row_hash
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id);

CREATE OR REPLACE VIEW :"schema".countersigned_in_force
    WITH (security_invoker = true) AS
SELECT l.id, l.ts, l.session, l.kind, l.statement, l.rationale, l.status, l.evidence,
       l.confidence, l.supersedes, l.refs, l.concern, l.enacts, l.actor, l.regards,
       l.amends, l.amends_scope, l.answers,
       l.stamp_session, l.stamp_agent, l.stamp_ts, l.stamp_hmac, l.stamp_verified,
       l.work_slug, l.work_title, l.work_depends_on, l.work_resolution, l.work_witness,
       l.stamp_invocation, l.event_declared_ts, l.row_hash
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".ledger r JOIN :"schema".review_detail d ON d.ledger_id = r.id
               WHERE r.kind = 'review' AND r.regards = l.id AND d.verdict = 'attest'
               AND NOT EXISTS (SELECT 1 FROM :"schema".ledger s2 WHERE s2.supersedes = r.id));
