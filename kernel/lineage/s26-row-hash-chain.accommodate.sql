-- s26-row-hash-chain.accommodate.sql -- ACCOMMODATION sibling for
-- kernel/lineage/s26-row-hash-chain.sql (design/MAINT-MIGRATION-ACCOMMODATIONS-SPEC.md, Fable-
-- authored spec, maintainer-ratified 2026-07-15). Never a hand-edit of the frozen s26 file
-- itself (ADR-0005 Rule 8; sec-2's own "frozen deltas stay byte-frozen" principle) -- a sibling,
-- exactly the same convention family as `.detect.sql`/`.verify.sql` (sec-2's own precedent
-- argument).
--
-- WHY THIS FILE EXISTS (ledger finding row 972, the spec's own motivating evidence): s26's own
-- frozen text ends with an UNCONDITIONAL
--     ALTER TABLE :"schema".ledger ALTER COLUMN row_hash SET NOT NULL;
-- which VALIDATES EVERY EXISTING ROW at ALTER time. Against a real deployment's history (any
-- world with pre-s26 ledger rows -- row_hash did not exist before s26, so every such row's
-- row_hash is NULL) this statement fails loudly:
--     ERROR:  column "row_hash" of relation "ledger" contains null values
-- witnessed directly, 2026-07-15, rehearsing this accommodation's own build against a byte-
-- faithful clone of the REAL autoharn1 deployment (997 pre-existing rows, head s25): the bare
-- frozen chain (s26..s29 applied verbatim) fails at exactly this statement, at exactly this
-- error text. This is the SAME class sec-10 of design/MAINT-COUNTERSIGN-CLOSE-SEMANTICS-SPEC.md
-- already cured for s29 (its own `migration_epoch` amendment) -- generalized here, nothing
-- reinvented (spec sec-2).
--
-- SUBSTITUTION (spec sec-2's own reviewability requirement: "the accommodation file itself
-- carries, in its header, the exact statements of the frozen delta it substitutes for, so the
-- substitution is reviewable line-against-line"). `./migrate` (bootstrap/migrate_core.py),
-- on detecting an `.accommodate.sql` sibling for a missing delta, applies the frozen file with
-- ONLY the exact statement below textually removed (a byte-for-byte match against the frozen
-- file's own on-disk text -- migrate refuses loudly if the match is not found, rather than
-- guessing), immediately followed by THIS file, in the SAME transaction. The frozen file on
-- disk is never edited; this is a substitution performed only in the text `./migrate` feeds to
-- psql for an in-place migration, never during a birth-chain `--new-world` apply (spec sec-2's
-- "who applies what" bullet: birth-chain worlds never read `.accommodate.sql` files at all --
-- new-project.sh's own `-f` invocation names only frozen files).
--
-- THE EXACT SUBSTITUTED STATEMENT (copied verbatim from kernel/lineage/s26-row-hash-chain.sql,
-- the line immediately after its own "NOT NULL, enforced last" comment -- diff this block
-- against that file directly to confirm the match holds). Delimited below by a BEGIN/END marker
-- pair (see this block's own opening line) that `bootstrap/migrate_core.py` parses MECHANICALLY
-- (not by re-typing this text a second time): it extracts the exact text between the two marker
-- lines, confirms it is a byte-exact substring of the frozen file's own on-disk text (a refusal,
-- never a silent guess, if the two have drifted), and removes ONLY that substring from an in-
-- memory copy of the frozen file before feeding [modified frozen file, this file] to psql in one
-- transaction -- the frozen file on disk is never touched (sec-2, "frozen deltas stay
-- byte-frozen"). NOTE for whoever authors the next accommodation: the marker line text itself
-- must appear EXACTLY ONCE in this file outside the block it delimits, or a naive first-match
-- parser (this one) finds the wrong occurrence -- keep any prose reference to the marker's NAME
-- paraphrased, as done here, never spelling out the literal marker line a second time.
--
-- (kept as a SQL comment here, one leading "-- " per line, so this file stays valid, inert SQL
-- on its own -- `bootstrap/migrate_core.py`'s extraction strips exactly that one prefix per line
-- before comparing against the frozen file's own, uncommented, live statement.)
-- ACCOMMODATE-SUBSTITUTES-BEGIN
-- ALTER TABLE :"schema".ledger ALTER COLUMN row_hash SET NOT NULL;
-- ACCOMMODATE-SUBSTITUTES-END
-- THE ACCOMMODATION ITSELF (sec-2's typed-exemption principle, applied): the unconditional
-- table-level NOT NULL is replaced by an EPOCH-GATED trigger invariant -- "every ledger row
-- with id > migration_epoch.epoch carries a non-NULL row_hash", enforced going forward, never
-- retroactively. Rows at-or-before the epoch (this world's pre-existing history) are EXEMPT BY
-- TYPE, a declared queryable fact (`SELECT epoch FROM :kern.migration_epoch`), never a
-- constraint-state subtlety -- the identical legibility argument sec-10 already ratified for
-- s29's own disposition invariant, applied uniformly here (spec sec-2, bullet 3).
--
-- WHY A TRIGGER, NOT A SECOND CHECK CONSTRAINT (same real Postgres limit s29's own AMENDMENT
-- header already names): a `CHECK` constraint cannot contain a subquery or reference another
-- table, so "NOT NULL below a value read from `migration_epoch`" is not expressible as a CHECK
-- at all, epoch table or not.
--
-- WHY THIS INVARIANT IS ALREADY MECHANICALLY TRUE FOR EVERY POST-s26 INSERT, AND WHY THE
-- TRIGGER IS STILL ADDED (belt-and-braces, named rather than silently assumed): s26's own
-- `zz_set_row_hash` trigger unconditionally computes `NEW.row_hash := compute_row_hash(...)`
-- for every INSERT once this delta (accommodated or not) is applied -- `compute_row_hash`
-- always returns a SHA-256 hex digest, never NULL, so no ordinary INSERT through the granted
-- `:role` can ever produce a NULL `row_hash` post-migration. The added trigger below
-- (`zzz_enforce_row_hash_not_null`, named to sort alphabetically AFTER `zz_set_row_hash` among
-- this table's BEFORE INSERT triggers -- s26's own trigger-name-ordering mechanism, reused, not
-- reinvented, per ADR-0012 P1) is the SAME defense-in-depth posture the plain `SET NOT NULL`
-- itself was: an independent, declarative-adjacent guarantee that does not rely solely on
-- trusting that `zz_set_row_hash` was never bypassed (s26's own LIMITS section already names a
-- schema-owner/superuser bypass as the one adversary class this whole mechanism does not
-- defend against; this trigger is a tripwire against an ORDINARY bug or a granted-role write
-- path that somehow supplies `row_hash` directly, not a defense against that named adversary).
-- Fires on BEFORE INSERT OR UPDATE (UPDATE is already refused for the granted `:role` by s15's
-- `append_only_row` trigger; included here anyway for the same "declarative, not merely relied-
-- upon" reason, symmetric with s26's own append-only precedent one delta over).
--
-- NOTHING RELAXES FOR POST-EPOCH ROWS (spec sec-2, bullet 4, the mechanical test): a row with
-- `id > epoch` and NULL `row_hash` is refused by this trigger EXACTLY as it would have been
-- refused by the unconditional `SET NOT NULL` the accommodated world never got to run --
-- `NEW.id > COALESCE(epoch, 0)` is true for every row this world writes after the migration
-- epoch was drawn, no different from the birth-chain case where epoch=0 makes it true for
-- literally every row (mirrors s29's own "BIRTH-CHAIN = EPOCH 0, SEMANTICS UNCHANGED" argument,
-- restated here for this delta's own invariant). See s26-row-hash-chain.accommodate.verify.sql
-- for the behavioral proof: an attempted post-epoch NULL row_hash is refused; a pre-epoch
-- historical row is left alone; the chain walk over the whole migrated history (pre- and post-
-- epoch rows both) is IDENTICAL to what `bootstrap/templates/verify-chain.tmpl` reports for a
-- birth-chain world with the same post-epoch content.
--
-- `migration_epoch` -- the ONE home for this fact (s29's own table, `:kern.migration_epoch`;
-- ADR-0012 P1 forbids a second one). This accommodation may run BEFORE s29 in the missing
-- chain (a world migrating only through s26/s27/s28, not yet s29) or AFTER it is already
-- present (re-applying this accommodation, or a world whose s29 was already migrated first for
-- some other reason) -- the DDL below is therefore the IDENTICAL `CREATE TABLE IF NOT EXISTS`
-- + `INSERT ... ON CONFLICT (only_one) DO NOTHING` shape s29 itself uses, copied verbatim (not
-- re-derived) so whichever of s26's accommodation or s29 runs FIRST in a given migration
-- transaction is the one that actually WRITES the epoch row; the second is a proven no-op
-- (`ON CONFLICT DO NOTHING`) that reads the SAME already-fixed epoch, never a second, possibly-
-- different computation -- both read `COALESCE(max(id), 0) FROM ledger` at a point in the SAME
-- transaction where no row has yet been inserted by this migration, so even in the hypothetical
-- of both being the "first" writer in two different migration runs, they would compute the
-- identical value; `ON CONFLICT DO NOTHING` makes this moot in the single-transaction case that
-- actually occurs.
--
-- FAIL-SAFE CLASSIFICATION: this accommodation ONLY substitutes an unconditional, history-
-- blind statement for an epoch-gated equivalent that governs every post-epoch row IDENTICALLY
-- to the substituted statement, and adds one new table + one new trigger, both additive.
-- Nothing existing is relaxed; no post-epoch guarantee weakens (spec sec-2, bullet 4's
-- disqualifying condition for "not an accommodation" does not apply here). Per the spec's own
-- "who applies what" bullet, this file is NEVER read by a birth-chain `--new-world` apply.
--
-- VALIDATE (reachable throwaway, same substrate convention as every other kernel/lineage file):
-- applied by `./migrate` only, against a scratch restore carrying real pre-existing history --
-- see design/MAINT-MIGRATION-ACCOMMODATIONS-SPEC.md sec-4 and this build's own witness table for
-- the live run.

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
-- migration_epoch -- s29's own table (kernel/lineage/s29-obligation-item-key-and-typed-close.sql,
-- sec-10 amendment), copied verbatim here (ADR-0012 P1: one home, reused not re-derived) so this
-- accommodation is self-sufficient regardless of whether s29 has already run in this same
-- migration transaction.
-- ============================================================================================
CREATE TABLE IF NOT EXISTS :"kern".migration_epoch (
    only_one   boolean PRIMARY KEY DEFAULT true CHECK (only_one),
    epoch      bigint NOT NULL,
    applied_ts timestamptz NOT NULL DEFAULT now(),
    dump_path  text,
    applied_by text
);
INSERT INTO :"kern".migration_epoch (only_one, epoch, dump_path, applied_by)
SELECT true, COALESCE(max(id), 0), NULLIF(:'epoch_dump_path', ''), NULLIF(:'epoch_applied_by', '')
FROM :"schema".ledger
ON CONFLICT (only_one) DO NOTHING;

GRANT SELECT ON :"kern".migration_epoch TO :"role";

COMMENT ON TABLE :"kern".migration_epoch IS
  'sec-10 amendment (kernel/lineage/s29-obligation-item-key-and-typed-close.sql), also written by
   kernel/lineage/s26-row-hash-chain.accommodate.sql when it runs first in a given migration: the
   one-row, write-once record of the ledger id boundary this world''s in-place migration drew.';

-- ============================================================================================
-- zzz_enforce_row_hash_not_null -- epoch-gated substitute for the frozen file's unconditional
-- `ALTER COLUMN row_hash SET NOT NULL` (see this file's own header for the full argument).
-- Named to sort alphabetically AFTER zz_set_row_hash (s26's own trigger) among this table's
-- BEFORE INSERT triggers, so it observes zz_set_row_hash's already-computed NEW.row_hash.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".zzz_enforce_row_hash_not_null() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_epoch bigint;
BEGIN
  SELECT epoch INTO v_epoch FROM migration_epoch LIMIT 1;
  IF NEW.row_hash IS NULL AND NEW.id > COALESCE(v_epoch, 0) THEN
    RAISE EXCEPTION 'row_hash chain: ledger row id % carries no row_hash past this world''s migration epoch (epoch=%, see %.migration_epoch) -- kernel/lineage/s26-row-hash-chain.accommodate.sql', NEW.id, COALESCE(v_epoch, 0), TG_TABLE_SCHEMA;
  END IF;
  RETURN NEW;
END; $fn$;

DROP TRIGGER IF EXISTS zzz_enforce_row_hash_not_null ON :"schema".ledger;
CREATE TRIGGER zzz_enforce_row_hash_not_null BEFORE INSERT OR UPDATE ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".zzz_enforce_row_hash_not_null();

COMMENT ON COLUMN :"schema".ledger.row_hash IS
  'SHA-256 (hex) of this row''s own content, chained to the predecessor row''s row_hash (see
   kernel/lineage/s26-row-hash-chain.sql for the base mechanism). On a world migrated in place
   via kernel/lineage/s26-row-hash-chain.accommodate.sql, rows with id <= this world''s
   migration_epoch predate the chain and are legitimately NULL (exempt by type, a declared
   queryable fact -- SELECT epoch FROM kernel.migration_epoch); rows with id > epoch are
   governed exactly as the frozen file''s original, unconditional NOT NULL describes, enforced
   here by the zzz_enforce_row_hash_not_null trigger rather than a table constraint (a CHECK
   cannot reference another table -- see this file''s own header).';
