-- s29 OBLIGATION ITEM-KEY + TYPED CLOSE + OBLIGATION-TREE GUARANTEE
-- (design/MAINT-COUNTERSIGN-CLOSE-SEMANTICS-SPEC.md, Fable-authored spec, RATIFIED 2026-07-14
-- with the sec-9 typed-actor non-foreclosure rider -- this delta is AUTHORED and
-- SCRATCH-WITNESSED only; APPLYING it to any live/existing world is the maintainer's act at a
-- FUTURE world's birth (runs-are-strictly-linear ruling, 2026-07-11), never taken here). An
-- ADDITIVE delta applied ON TOP of the s15..s28 kernel (the established remediation-delta idiom),
-- NOT a retro-edit of a frozen sNN record (ADR-0005 Rule 8) and NOT a second hand-copy of any
-- existing mechanism (ADR-0012 P1: one home per mechanism).
--
-- PREREQUISITE (named, unlike s28's own deliberately-independent relationship to s27): this delta
-- REQUIRES s28 (kernel/lineage/s28-work-parent-edge.sql) applied first -- Element C's own spec
-- text names "children via ... the s28 parent edge" as part of the obligation tree, so
-- work_item_strict_blockers() below reads ledger.work_parent directly (a column s28, not s22,
-- adds). Applying this file on an s15..s27 kernel (no s28) fails loudly at CREATE FUNCTION time
-- (undefined column), not silently -- the correct, disclosed failure mode for a hard dependency.
--
-- WHY (operator-side prose; NOT subject-visible -- only the catalog objects inside the opaque db
-- are): the spec's own sec-1, three witnessed consequences of ONE defect (obligation identity,
-- lifecycle, and resolution are not typed): (1) a disclosed self-review written seconds before an
-- item's close still deposits actor-keyed review_gap debt that SURVIVES the close (the 12:15:05Z
-- re-arm, 37/41 additions traceable one-to-one to just-closed items); (2) the `reviewer2`
-- discharge mechanism -- a second identity distinct in id but not in independence -- invented
-- in-world to shut the conveyor off under stop-gate pressure; (3) an agent, blocked by the debt,
-- self-escalated to delete 813 obligation rows outright. This delta forecloses the class the spec
-- names (ADR-0000 Rule 2(a)): obligations keyed by WORK ITEM not actor (Element A), close as a
-- TYPED act with two constructors making a review-silent close unrepresentable (Element B), and an
-- OPT-IN obligation-tree guarantee with conjunction-DERIVED resolution, no stored verdict (Element
-- C) -- the pairing-RCA lesson (design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md) applied a second time:
-- never store a computed verdict a read-time derivation can answer.
--
-- ELEMENT A -- ITEM-KEYED OBLIGATION, NO NEW BASE TABLE (spec sec-3). The obligation this delta
-- creates (a deferred review disposition on a work_closed row) is the CLOSE ROW ITSELF -- its
-- own `work_slug` IS the item key, its own ledger `id` IS the origin identity Element B's own text
-- names ("the obligation row carries the close row's id as its origin identity"). No new table:
-- the s22/s28 "no new base table" doctrine holds here too (work-item facts ride ledger columns).
-- This is DELIBERATELY SEPARATE from the pre-existing actor-keyed `countersign_obligation` /
-- `review_gap` (s13/s15/s20) -- that mechanism is UNTOUCHED by this delta (still actor-keyed,
-- still governs non-work-item ledger rows exactly as before); `work_review_gap` below is its
-- NEW, item-keyed sibling for work-item close obligations specifically, not a replacement.
-- NAMED, NOT BURIED (ADR-0013 Rule 4, ADR-0000 Exceptions "filed, not buried"): wiring the
-- LEGACY actor-keyed countersign_obligation in as a third leaf-type of Element C's obligation
-- tree ("a countersign leaf by its recorded countersign act", spec sec-5) is NOT done in this
-- delta -- that table carries no work-item linkage today (its PK is `scope`, a free-text label,
-- per s13/s20; joining it to a specific work item's tree is a genuine, real type whose blast
-- radius is deferred, filed as ledger finding row 730 (this project's own live tracker, not
-- BACKLOG.md -- that file retired 2026-07-12; the ledger is the only liveness surface), per
-- ADR-0000's own Exceptions clause ("the type is real but its blast radius is deferred").
-- Element C below therefore resolves exactly the two leaf kinds the spec's own worked text
-- gives unambiguous construction for: the item's own review disposition, and its
-- work_depends_on/s28-child leaves.
--
-- ELEMENT B -- TWO CONSTRUCTORS, REVIEW-SILENT CLOSE UNREPRESENTABLE (spec sec-4). Two NEW columns
-- on a work_closed row: `work_review_disposition` (witnessed|deferred, MANDATORY -- a two-way
-- shape CHECK exactly like s22's own `work_resolution_kind_shape`, so a work_closed row with NO
-- disposition cannot exist even transiently) and `work_review_ref` (required non-empty iff
-- disposition=witnessed, mirroring s22's `work_shipped_requires_witness` CHECK pattern exactly).
-- NAMED CHOICE: `work_review_ref` is DELIBERATELY a NEW, separate column from s22's pre-existing
-- `work_witness` (the SHIP witness, gated on resolution=shipped) -- the two are orthogonal facts
-- (did you ship it vs. did someone review it) and reusing one flag/column for both would be an
-- SSOT violation the moment a `dropped`/`deferred` resolution (no ship witness required) still
-- wants a review witness, or a `shipped` item's review witness differs from its ship witness. Two
-- flags, two columns, two CHECKs, kept apart on purpose (ADR-0008: do not fuzzy-match two distinct
-- facts into one), matching s28's own "work_parent vs work_depends_on, deliberately DIFFERENT
-- relations" precedent.
--
-- ELEMENT C -- OPT-IN OBLIGATION-TREE GUARANTEE (spec sec-5). ONE new column,
-- `work_strict_close` (boolean, legal only on work_closed rows, opt-in PER CLOSE ACT -- a
-- deployment or item-class "declares" strict semantics by convention: its own operating discipline
-- always passes `--strict`, exactly as an opt-in POSTURE per the spec's own text, "a declared
-- posture, not a universal mandate"). When set, `validate_work_item()` (extended a THIRD time,
-- following s22's own precedent of extending one function rather than minting a second -- ADR-0012
-- P1) computes the derived conjunction via `work_item_strict_blockers()` (a STABLE SQL function,
-- the s28 `work_parent_would_cycle()` idiom) and REFUSES naming every unresolved leaf -- NO STORED
-- VERDICT anywhere (the pairing-RCA lesson): "resolved" is never written, only ever computed.
-- STRICT + DEFERRED IS A CONTRADICTION IN TERMS, REFUSED DIRECTLY (named, not discovered by the
-- generic blocker walk): a `--review-deferred` close creates a fresh, by-definition-unresolved
-- leaf obligation in the SAME act that strict mode would need it resolved -- so strict mode
-- REQUIRES `--review-witness` (constructor 1) at its own root, root's own leaf never delegated to
-- the blocker function (which only walks DESCENDANTS -- the row being inserted is not yet visible
-- to a query, BEFORE INSERT).
--
-- INDEPENDENCE GRADE (spec sec-5, "Independence is a typed grade, computed and carried at write
-- time" -- sharpened under the reviewer2 mandate, session f2fe167, superseding a weaker
-- join-at-read formulation this spec's own history records and rejects on the SAME ground as the
-- pairing RCA). ONE new column, `review_detail.discharge_grade`, CLOSED VOCABULARY
-- (same-principal|same-session|distinct-session|distinct-deployment), computed by EXTENDING
-- s21's `validate_independence()` (the SAME function, CREATE OR REPLACE, not a second trigger --
-- it already fetches the exact (stamp_session,stamp_agent) pairs this computation needs, ADR-0012
-- P1: reuse the query, don't re-derive it) -- computed for EVERY review-discharge act, not only an
-- independence-CLAIMING one (spec's own text: "every review-discharge act"). FAIL-SAFE DEFAULT
-- (spec's own point 3): an identity-absent discharge records `same-principal`, the
-- LEAST-independent assumption, never an optimistic default. `distinct-deployment` is CLOSED
-- VOCABULARY but UNREACHABLE from this function TODAY -- named, not hidden (see LIMITS below):
-- this schema carries no deployment-id fact to compare a discharging invocation against, so no
-- code path here can ever emit it; a future cross-deployment stamp fact is the type that would
-- make it reachable, filed as ledger finding row 731 (this project's own live tracker; BACKLOG.md
-- retired 2026-07-12), not silently claimed live. NO FLOOR IS WIRED (spec's own text: "the floor
-- is a deployment's declared posture, DEFAULT UNSET pending the maintainer's adjudication of the
-- ent precedent") -- this delta exposes the grade per leaf (queryable, per spec consequence (1))
-- and stops there; a `--min-grade` gate on strict close is NOT built, filed as ledger finding row
-- 732, per the spec's own explicit deferral, not an omission this delta is silently making on its
-- own authority.
--
-- SEC-9 FORWARD-COMPAT (typed actors are not foreclosed): every principal reference in this delta
-- (closer, discharging actor) is the EXISTING `kernel.principal.id` foreign key, unchanged -- no
-- actor-type/certification column is added here (the ratification note's own text: "an extension
-- for later ... neither blocks this ratification"). The independence GRADE (orthogonal, "how
-- separate") and a future actor TYPE (orthogonal, "how qualified") are kept deliberately apart, per
-- the ratification note's own forward-compatibility audit -- this delta touches neither
-- `kernel.principal` nor its schema.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 amendment):
--
--   - INVARIANT: every work-item close row carries a MANDATORY, closed-vocabulary review
--     disposition (witnessed|deferred) enforced at CONSTRUCTION TIME (a two-way shape CHECK, the
--     strongest available surface) -- a review-silent close is UNREPRESENTABLE, not merely
--     discouraged. Every review-discharge act (any review_detail row) carries a closed-vocabulary,
--     COMPUTED (never writer-asserted) independence grade. A strict-mode close's obligation-tree
--     resolution is a PURE, read-time-derived query over existing facts -- no verdict is ever
--     written to any column; "resolved" cannot be false in storage because it is never in storage.
--
--   - QUANTIFICATION UNIVERSE -- enumerated by re-reading every table/view the s15..s28 chain
--     exposes to :role (mirroring s22/s28's own re-verification discipline), checked against the
--     new columns/objects this delta adds:
--       TABLES reachable off :"schema"/:"kern": unchanged w.r.t. Element A/B/C proper -- still no
--         new base table under :"schema" (Element A's own no-new-table doctrine, re-applied). The
--         sec-10 AMENDMENT adds exactly ONE new base table, and it lives under :"kern" (not
--         :"schema"), mirroring :kern.chain_genesis/:kern.chain_high_water (s26/s27's own
--         precedent for a one-row, kernel-side infrastructure fact): :"kern".migration_epoch
--         (only_one, epoch, applied_ts, dump_path, applied_by), GRANT SELECT to :role, no
--         write grant (see the AMENDMENT section above for the full design and why a base table
--         was unavoidable here -- a CHECK constraint cannot read a value from another table, so
--         "exempt below a value read elsewhere" cannot be expressed any other way).
--       VIEWS re-read for the wildcard/column-complete class s20/s22/s23/s24/s26/s28 all named:
--         * ledger_current / countersigned_in_force -- explicit column lists (s20+). GAIN the
--           THREE new columns (work_review_disposition, work_review_ref, work_strict_close),
--           APPENDED AT THE END, HERE, else the column-complete class recurs one column later (the
--           s20 lesson, re-applied a fourth time).
--         * work_item_current (s22, extended s28) -- explicit column list. GAINS review_disposition
--           and review_ref (sourced from the SAME `closed` CTE that already carries
--           resolution/witness -- these are the SAME kind of fact, captured only on the closing
--           row).
--         * work_item_violations, work_item_descendants -- re-verified NOT members: neither reads
--           a general ledger-row column passthrough this delta's three new columns belong on
--           (both are s22/s28's own specialized derived shapes, untouched).
--         * review_gap / question_status / review_stamp_distinctness -- re-verified NOT members,
--           for the identical reasons s22/s24/s26/s28 each already gave (no general ledger-row
--           column passthrough a work-close fact belongs on); review_gap is ALSO deliberately left
--           semantically untouched (Element A's own "deliberately separate" note above).
--       KIND VOCABULARY -- unchanged. This delta adds no new `kind` value (mirrors s28's own
--         disclosure): the review disposition/ref/strict-close facts are carried entirely on the
--         EXISTING `work_closed` kind's own row, three more optional columns beside
--         work_resolution/work_witness.
--       GRANTS -- mirrors s22/s28's own posture: the ONE new view (`work_review_gap`) gets a fresh
--         GRANT SELECT; the three new ledger columns and the one new review_detail column ride
--         their already-granted base tables (INSERT+SELECT since s15), so no table-level grant
--         change is needed for them. The two new STABLE functions need no explicit GRANT (Postgres
--         grants EXECUTE on a function to PUBLIC by default, unless later REVOKEd -- verified
--         against s28's own `work_parent_would_cycle()`, which received no explicit GRANT either).
--       ENGINE -- `engine/lp/work_review.lp` (ASP) + `work_review_floor_atoms()`
--         (`engine/ledger_floor.py`, the SQL floor mirror) + this delta's own scratch fixture are
--         the engine-layer companions, authorized by THIS Fable-authored, maintainer-ratified spec
--         (sec-6). NOT wired into `judge`/`ledger_differential.py` -- mirrors s22's own verified
--         precedent (`judge` does not auto-discover `engine/lp/*.lp`; every non-core `.lp` file has
--         its own bespoke scratch-differential instead) -- no `judge` change is made or needed.
--
--   - DENOMINATION: the item key is the SLUG (s22/s28's own denomination, re-applied, never a
--     row id -- a slug is the stable per-ITEM identity this whole lineage already committed to).
--     The origin identity Element B's own text names ("the obligation row carries the close row's
--     id") is denominated in the LEDGER ROW ID of the work_closed act itself (a per-EVENT handle,
--     correctly so here -- Element A's own text: "with the obliged/acting principals as
--     attributes, never as the key" -- the KEY is the item/slug via work_slug on the SAME row; the
--     origin id is how a LATER discharging review names WHICH close act it discharges, exactly the
--     way `review_detail.antecedent`/`ledger.regards` already name a specific row, never a proxy).
--     The independence grade is denominated in the (stamp_session, stamp_agent) PAIR (s21's own
--     denomination, re-applied, never a proxy for it) -- never re-derived from `actor`, `ts`, or
--     any writer-supplied column.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): this delta is NOT
-- class-ratified fail-safe (the spec's own sec-7 says so explicitly: Element B changes the
-- semantics of an existing verb -- `work close` gains a MANDATORY disposition, which is a real
-- behavior change on a pre-existing, in-use verb, even though the change is refusal-shaped) -- it
-- IS the Fable-authored, maintainer-ratified delta the spec's own header names (RATIFIED
-- 2026-07-14). Elements A and C, taken alone, would be class-ratified (add refusals/keys/views
-- only); Element B is why the whole delta routes through ratification, per the spec's own sec-7
-- text, and it already has (this file's own header).
--
-- LIMITS (pre-registered, matching s22/s26/s28's own disclosure convention):
--   - `work_item_strict_blockers()` walks descendants via `work_parent` and antecedents via
--     `work_depends_on`, exactly the two leaf-kinds spec sec-5 gives unambiguous construction for.
--     The LEGACY actor-keyed countersign_obligation is NOT a leaf-kind in this tree (see ELEMENT A
--     above; filed as ledger finding row 730, not built).
--   - `discharge_grade`'s `distinct-deployment` value is closed vocabulary but PROVABLY UNREACHABLE
--     from this schema today (no deployment-id fact exists to compare) -- named, not hidden (see
--     INDEPENDENCE GRADE above; filed as ledger finding row 731).
--   - No floor/minimum-grade gate is wired on strict close (spec's own explicit DEFAULT UNSET
--     deferral to the maintainer; filed as ledger finding row 732, not an omission taken on this
--     delta's own authority).
--   - Like every trigger-enforced refusal in this lineage (s22/s26/s28's own disclosed bound), the
--     strict-close refusal and the review-disposition shape CHECKs bind ONLY the granted `:role`'s
--     ordinary INSERT path -- a schema-owner/superuser with DDL privilege can disable the trigger
--     or write directly, the same disclosed bound s26/s28 already name.
--   - `work_item_strict_blockers()`'s tree walk has NO explicit depth cap of its own (unlike s28's
--     `work_parent_would_cycle`/`work_item_descendants`, both capped at 10000): it is STRUCTURALLY
--     bounded by the SAME cycle-freedom s28 already proves (a legally-constructed work-parent tree
--     under ordinary INSERT cannot cycle, s28's own header proof, re-applied here without
--     re-arguing it) -- a bypassed-trigger cycle (the same disclosed bound above) could in
--     principle make this walk non-terminate; named, not defended against twice (s28's own
--     `work_item_descendants` cap already exists as the ONE authoritative defense for that
--     bypassed-trigger scenario across every consumer, ADR-0012 P1 -- this function does not
--     duplicate that cap, it inherits the same disclosed limit).
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/s20/s22/s28): schema/kern/role
-- are psql variables so this delta is VALIDATED on a throwaway substrate before any real apply.
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s29val -v kern=s29val_kernel -v role=s29val_rw \
--        -f s15-schema.sql -f s17-stamp-mechanism.sql -f s17-independence-vocabulary.sql \
--        -f s19-trigger-search-path.sql -f s20-obligation-grants-and-view-refresh.sql \
--        -f s21-session-aware-distinctness.sql -f s22-work-item-ledger.sql \
--        -f s23-per-invocation-stamp-token.sql -f s24-declared-event-time.sql \
--        -f s25-commission-kind.sql -f s26-row-hash-chain.sql -f s28-work-parent-edge.sql \
--        -f s29-obligation-item-key-and-typed-close.sql
--     (provision a genesis seed per s26's own block before the first ledger INSERT, or that
--     trigger refuses loudly -- this delta adds no genesis requirement of its own.)
--   REAL: NEVER applied to any existing world by this delta's own authoring act (maintainer ruling
--   2026-07-11, "runs are strictly linear"). This delta reaches reality by entering a FUTURE
--   world's birth chain, wired by a maintainer/orchestrator seam-integration pass into
--   `bootstrap/new-project.sh`'s `LINEAGE_CHAIN` -- NOT taken here (mirrors s28's own deferral,
--   same reasoning: avoid a builder racing edits to a shared script it does not own the seam of).
--   It was authored and scratch-witnessed on scratch schema pairs in the TOY db only -- NOT applied
--   to any live schema by this pass.
-- Run as the schema owner (bork). Idempotent (ADD COLUMN IF NOT EXISTS; DROP+ADD CONSTRAINT;
-- CREATE OR REPLACE + DROP/CREATE TRIGGER/FUNCTION/VIEW).

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
-- AMENDMENT-ONLY VARS (sec-10, 2026-07-15 night): provenance strings the applying act may supply;
-- both default to '' (NULLIF'd to NULL below) so a `psql -f` run with no extra `-v` at all -- e.g.
-- a --new-world birth-chain apply, which passes only schema/kern/role -- still runs correctly and
-- self-identifies epoch=0 by the ledger-emptiness argument in the migration_epoch block below, not
-- by these vars being set.
\if :{?epoch_dump_path}
\else
  \set epoch_dump_path ''
\endif
\if :{?epoch_applied_by}
\else
  \set epoch_applied_by ''
\endif

-- ============================================================================================
-- AMENDMENT (sec-10 of design/MAINT-COUNTERSIGN-CLOSE-SEMANTICS-SPEC.md, 2026-07-14 night,
-- RATIFIED 2026-07-15 pre-sleep -- ledger decision row 935 -- CONDITIONALLY, with the execution
-- rule that ANY rehearsal/apply breakage is the pre-accepted "harmful" branch, not a failure) --
-- THE PRE-MIGRATION EPOCH, option (ii) from the amendment's own two honest candidates.
--
-- WHY (falsified claim, named not buried): sec-7's "class-ratified fail-safe" framing assumed an
-- empty ledger (birth-chain-only delivery). The ent rehearsal (2026-07-14) witnessed the ORIGINAL
-- `work_review_disposition_kind_shape` -- a plain two-way `CHECK ((kind='work_closed') =
-- (disposition IS NOT NULL))` -- REFUSE to even ADD on a deployment carrying pre-s29 work_closed
-- rows (ent: 157): `ADD CONSTRAINT` validates EVERY EXISTING ROW at DDL time (unless `NOT VALID`),
-- and every one of those 157 rows has `disposition IS NULL` while `kind='work_closed'` -- an
-- immediate, universal violation. The amendment's REJECTED alternatives, both in this file's own
-- history, are also named here for a zero-context reader: (i) `NOT VALID` on the same CHECK is
-- Postgres-idiomatic but leaves the exemption living in unqueryable catalog state ("old rows were
-- never checked", an absence, not a fact); (iii) backfilling a disposition onto the 157 historical
-- rows was REJECTED outright -- `deferred` mints 157 fresh review_gap debt rows, RE-CREATING THE
-- EXACT CONVEYOR THIS SPEC EXISTS TO KILL (sec-1's own defect), and `witnessed` fabricates 157
-- review refs that were never made (s26's row_hash chain excludes these new columns from its
-- fixed column list, so this would not even be DETECTABLE as a fabrication after the fact) --
-- worse than the disease either way.
--
-- THE DESIGN: a one-row `migration_epoch` table (below), written ONCE by the applying act itself
-- (birth-chain OR in-place, this file draws no distinction -- see "BIRTH-CHAIN = EPOCH 0" below),
-- holding `epoch = the ledger's max id AT THE MOMENT THIS FILE IS APPLIED`. Every `work_closed`
-- row with `id > epoch` is GOVERNED (must carry a disposition, exactly sec-4's original invariant,
-- unchanged); every row at-or-before the epoch is EXEMPT BY TYPE -- a declared, queryable fact
-- (`SELECT epoch, dump_path, applied_by, applied_ts FROM migration_epoch`) a zero-context reader
-- or auditor can read directly, never a constraint-state subtlety inferred from what a `\d+
-- ledger` catalog dump does NOT show.
--
-- WHY THIS IS A TRIGGER, NOT A SECOND CHECK CONSTRAINT (a real Postgres limit, not a style
-- choice): a `CHECK` constraint is evaluated per-row against ONLY that row's own columns -- it
-- cannot contain a subquery or reference any other table (Postgres: "cannot contain subqueries
-- nor refer to variables other than columns of the current row"), so "exempt below a value read
-- from another table" is NOT EXPRESSIBLE as a `CHECK` at all, epoch table or not. This is why
-- `work_review_disposition_kind_shape` (the DECLARATIVE, construction-time CHECK sec-4's own text
-- calls "the strongest available surface") is DROPPED below and its invariant re-homed inside
-- `validate_work_item()` (the SAME BEFORE INSERT trigger this file already extends three times) --
-- named, not silently weakened: a BEFORE INSERT trigger refuses an illegal row exactly as
-- completely as a CHECK does (Postgres runs it before the row is ever visible to any other
-- transaction), it is simply the ONLY surface that can also consult `migration_epoch`. The three
-- OTHER Element B/C CHECK constraints below (`work_review_disposition_check`,
-- `work_review_ref_kind_shape`, `work_review_witnessed_requires_ref`, `work_strict_close_kind_shape`)
-- are UNCHANGED, still plain CHECKs: each one is vacuously satisfied by every historical row
-- (`work_review_disposition IS NULL`, `work_review_ref IS NULL`, `work_strict_close IS NULL` on
-- every pre-s29 row makes each of those four predicates TRUE regardless of epoch), so ONLY the
-- disposition-presence invariant needed to move -- a minimal-touch fix (ADR-0004), not a rewrite of
-- Element B's shape.
--
-- BIRTH-CHAIN = EPOCH 0, SEMANTICS UNCHANGED (verified, not asserted -- see the fixture below):
-- `bootstrap/new-project.sh --new-world` applies the FULL `kernel/lineage/` chain, s29 included,
-- to a schema with ZERO ledger rows, BEFORE the very first `led work open`/`led decision` etc. is
-- ever issued (new-project.sh's own ordering: kernel apply, THEN stamp-secret seed, THEN
-- chain-genesis seed, THEN principal registration -- all schema/DDL/seed acts, never a ledger
-- INSERT). `SELECT COALESCE(max(id),0) FROM ledger` against an empty ledger returns exactly 0 --
-- no special-casing, no `--new-world`-vs-in-place branch anywhere in this file: the SAME one
-- `INSERT INTO migration_epoch ... SELECT COALESCE(max(id),0) ...` statement below naturally
-- yields epoch=0 for a birth-chain world and epoch=<real max> for an in-place migration, because
-- the fact it reads (the ledger's own row population at apply time) IS the distinction, not a flag
-- this file has to be told. Epoch 0 makes `NEW.id > 0` true for literally every row a birth-chain
-- world will ever write (ledger `id` is a strictly-increasing serial starting at 1) -- so a
-- birth-chain world's disposition invariant governs EVERY work_closed row, byte-for-byte the
-- pre-amendment behavior; nothing about Element B/C's semantics changes for a fresh world.
-- ============================================================================================

-- ============================================================================================
-- migration_epoch -- the one-row, kernel-side (mirrors :kern.chain_genesis/:kern.chain_high_water,
-- s26/s27's own precedent -- infrastructure facts live in :kern, never in the subject-visible
-- :schema) provenance record of this delta's own epoch. `ON CONFLICT (only_one) DO NOTHING` makes
-- this WRITE-ONCE, permanently -- a second `psql -f` of this same file (idempotent re-apply, this
-- file's own standing contract) must NEVER re-widen an already-fixed epoch by recomputing
-- `max(id)` a second time against a now-larger ledger; the FIRST apply's epoch is the one that
-- governs for this world's whole remaining lifetime. `dump_path`/`applied_by` are OPTIONAL
-- provenance (sec-10: "provenance: dump path, date, applying authority") -- NULL when the applying
-- act supplies no `-v epoch_dump_path=...`/`-v epoch_applied_by=...` (every birth-chain apply, and
-- any manual in-place apply that omits them); `applied_ts` is always populated (`now()`, never
-- optional -- "date" from sec-10's own list is never absent). This table is ALSO a natural home
-- for a future root-provisioning anchor (sec-10's own aside, "this row is also a natural home for
-- the root-provisioning anchor going forward") -- named, not built: no such column exists here,
-- filed for whoever designs that mechanism to extend this table rather than mint a sibling one
-- (ADR-0012 P1).
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
-- No INSERT/UPDATE/DELETE grant to :role -- the epoch is written once, by the schema owner
-- applying this delta, exactly like :kern.chain_genesis's own posture (s26's own comment, "the
-- seed is written once, by the scaffold, as the schema owner -- the subject can read it ... but
-- cannot rewrite it"), one table over.

COMMENT ON TABLE :"kern".migration_epoch IS
  'sec-10 amendment (kernel/lineage/s29-obligation-item-key-and-typed-close.sql): the one-row,
   write-once record of the ledger id boundary this world''s s29 apply drew. work_closed rows with
   id <= epoch predate the review-disposition invariant and are EXEMPT BY TYPE (a declared,
   queryable fact -- see this file''s AMENDMENT header for the full rationale); rows with
   id > epoch are governed exactly as Element B''s original, unconditional text describes. A
   birth-chain (--new-world) apply always yields epoch=0 (the ledger is empty at apply time),
   which governs every row that world will ever write -- semantics unchanged for a fresh world.';

-- ============================================================================================
-- ELEMENT B -- THE THREE NEW COLUMNS on ledger (review disposition/ref legal+mandatory only on
-- work_closed; strict-close legal only on work_closed). No new base table.
-- ============================================================================================
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS work_review_disposition text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS work_review_ref         text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS work_strict_close       boolean;

COMMENT ON COLUMN :"schema".ledger.work_review_disposition IS
  'Element B (kernel/lineage/s29): the MANDATORY, closed-vocabulary review disposition of a
   work_closed row -- witnessed (a review already on record, cited by work_review_ref) or deferred
   (this close act ITSELF is the obligation, item-keyed by work_slug, origin-identified by this
   row''s own ledger id -- Element A). A work_closed row with NO disposition cannot exist even
   transiently (work_review_disposition_kind_shape below, a two-way CHECK) -- the review-silent
   close class is unrepresentable, not merely discouraged.';
COMMENT ON COLUMN :"schema".ledger.work_review_ref IS
  'Element B: the review reference (a ledger row id, commit hash, or artifact path) for
   disposition=witnessed. REQUIRED (non-empty) when work_review_disposition=''witnessed''
   (work_review_witnessed_requires_ref below). DELIBERATELY SEPARATE from work_witness (s22''s
   SHIP witness, gated on resolution=shipped) -- see this file''s header for why the two are kept
   apart rather than reusing one column/flag for both facts.';
COMMENT ON COLUMN :"schema".ledger.work_strict_close IS
  'Element C (kernel/lineage/s29): opt-in per close act. When true, validate_work_item() refuses
   this close unless work_review_disposition=''witnessed'' AND every leaf of this item''s
   obligation tree (its own descendants via work_parent, and every tree member''s
   work_depends_on antecedents) is independently resolved (work_item_strict_blockers()) --
   named, unresolved leaves in the refusal text, no stored verdict anywhere. NULL/false =
   non-strict (Element B''s deferral constructor remains available, the spec''s own "declared
   posture, not a universal mandate").';

-- ============================================================================================
-- SHAPE INVARIANTS (illegal states unrepresentable AT CONSTRUCTION, ADR-0000 Rule 1 -- the
-- strongest available surface WHERE a plain CHECK can express it). The TWO-WAY correlation that
-- makes a review-silent close unrepresentable (Element B's whole point) is, as of the sec-10
-- amendment, EPOCH-GATED -- see this file's AMENDMENT header for why that makes it a
-- `validate_work_item()` trigger clause (below) rather than a table CHECK: a CHECK cannot consult
-- `migration_epoch`, a different table, at all. This DROP is kept (idempotent cleanup) in case
-- this schema carries the CONSTRAINT from a PRE-amendment apply of this same file -- re-running
-- the amended file against such a schema must actively REMOVE the old, epoch-blind CHECK, not
-- merely fail to re-add it.
-- ============================================================================================
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_review_disposition_kind_shape;

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_review_disposition_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_review_disposition_check CHECK (
    work_review_disposition IS NULL OR work_review_disposition IN ('witnessed', 'deferred'));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_review_ref_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_review_ref_kind_shape CHECK (
    work_review_ref IS NULL OR kind = 'work_closed');

-- mirrors s22's work_shipped_requires_witness pattern exactly, one column over.
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_review_witnessed_requires_ref;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_review_witnessed_requires_ref CHECK (
    work_review_disposition IS DISTINCT FROM 'witnessed'
    OR (work_review_ref IS NOT NULL AND btrim(work_review_ref) <> ''));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_strict_close_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_strict_close_kind_shape CHECK (
    work_strict_close IS NULL OR kind = 'work_closed');

-- ============================================================================================
-- work_item_strict_blockers(root_slug) -- Element C's derived conjunction, the ONE home of
-- "is root_slug's obligation tree resolved" (ADR-0012 P1). Returns EMPTY iff resolved. Reads
-- work_parent (s28 -- this delta's own PREREQUISITE) to walk descendants; NO stored verdict is
-- read or written anywhere -- every row here is computed fresh from work_closed/review_detail/
-- work_depends_on facts. LANGUAGE sql STABLE: a pure read, safe to call from the trigger below.
-- Root's OWN leaf (its review disposition) is DELIBERATELY NOT checked here -- the row carrying
-- it is the one BEING INSERTED (not yet visible to a query, BEFORE INSERT) -- the trigger checks
-- root's own disposition directly against NEW.*, see below.
--
-- CORRECTED (out-of-frame hack-rationalization audit, same session, before this file's first
-- commit -- caught, not shipped): a first draft's `tree` CTE walked ONLY the s28 parent edge, and
-- treated a `work_depends_on` antecedent as resolved the moment it had ANY close row -- a one-hop
-- "is it closed" check standing in for "is it RESOLVED" (spec sec-5's own text: "Interior nodes
-- resolve derivationally as the conjunction of their children -- children via `work_depends_on`,
-- the s28 parent edge, AND the obligations keyed to the item"). WITNESSED ATTACK: open B, close B
-- --review-deferred (undischarged); open A depending on B (`work_depends_on`, no parent edge at
-- all); `led work close A ... --review-witness ref --strict` SUCCEEDED -- B's own outstanding
-- review obligation was invisible to the check, defeating the strict guarantee's whole point. THE
-- FIX (a type, not a special case, ADR-0000 Rule 2(a)): `tree` now walks BOTH edge kinds
-- TRANSITIVELY and UNIFORMLY -- a `work_depends_on` antecedent is a full tree member exactly like
-- an s28 child, so its OWN leaf resolution (and ITS OWN antecedents/children, recursively) is
-- checked, not merely its existence. This is deliberately the MORE INCLUSIVE reading (an
-- antecedent's own s28 sub-children also enter the tree) -- the fail-safe direction for a
-- guarantee feature: requiring MORE to be resolved before a strict close succeeds, never less.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".work_item_strict_blockers(root_slug text)
    RETURNS TABLE(blocking_slug text, reason text) LANGUAGE sql STABLE
    SET search_path = :"schema", pg_temp AS $fn$
  WITH RECURSIVE
  edges AS (
    -- both edge kinds feeding ONE combined successor relation (Postgres allows exactly ONE
    -- self-reference to a recursive CTE in its recursive term, so the two edge kinds are unioned
    -- HERE, outside the recursion, rather than as two separate recursive UNION arms). DIRECTION
    -- (both rows read "walking FROM `parent` we reach tree member `child`"): an s28 work_parent
    -- edge walks PARENT -> CHILD literally (child.work_parent = parent, matching the column
    -- names). A work_depends_on edge walks OPPOSITE its own column names -- the DEPENDENT plays
    -- the `parent` role here (it is the tree member we are walking FROM) and its ANTECEDENT plays
    -- the `child` role (the next tree member we reach) -- because a dependency's antecedent is a
    -- CHILD in obligation-tree terms (spec sec-5: "children via `work_depends_on`"): the item that
    -- depends on it needs the antecedent's own resolution, exactly as it needs an s28 child's.
    SELECT o.work_slug AS child, o.work_parent AS parent
    FROM ledger o WHERE o.kind = 'work_opened' AND o.work_parent IS NOT NULL
    UNION ALL
    SELECT dep.work_depends_on AS child, dep.work_slug AS parent
    FROM ledger dep WHERE dep.kind = 'work_depends_on'
  ),
  tree(slug) AS (
    SELECT root_slug
    UNION
    SELECT e.child FROM tree t JOIN edges e ON e.parent = t.slug
  ),
  closes AS (
    SELECT work_slug AS slug, id AS close_id, actor AS closer, work_review_disposition AS disp
    FROM ledger WHERE kind = 'work_closed'
  ),
  not_closed AS (
    SELECT t.slug, 'item is not yet closed'::text AS reason
    FROM tree t
    WHERE t.slug <> root_slug AND NOT EXISTS (SELECT 1 FROM closes c WHERE c.slug = t.slug)
  ),
  review_unresolved AS (
    SELECT c.slug, 'review disposition deferred and undischarged (close row ' || c.close_id || ')' AS reason
    FROM closes c
    JOIN tree t ON t.slug = c.slug
    WHERE c.disp = 'deferred'
      AND NOT EXISTS (
        SELECT 1 FROM ledger r
        JOIN review_detail d ON d.ledger_id = r.id
        WHERE r.kind = 'review' AND r.regards = c.close_id AND d.verdict = 'attest' AND r.actor <> c.closer
          AND NOT EXISTS (SELECT 1 FROM ledger s2 WHERE s2.supersedes = r.id)
      )
  )
  SELECT slug, reason FROM not_closed
  UNION ALL SELECT slug, reason FROM review_unresolved;
$fn$;

-- ============================================================================================
-- validate_work_item() EXTENDED A THIRD TIME (the SAME function s22 defined and s28 extended --
-- CREATE OR REPLACE, not a second copy; ADR-0012 P1). New: for kind='work_closed' with
-- work_strict_close true, refuse a deferred disposition outright (strict+deferred is a
-- contradiction in terms, see header), and refuse if work_item_strict_blockers() names any
-- unresolved descendant/dependency leaf. Every pre-existing branch (duplicate-open; dangling
-- parent/cycle; unopened-slug) is UNCHANGED, byte-for-byte, below.
-- ============================================================================================
-- sec-10 amendment: :"kern" is added to this function's search_path (mirrors s26's own
-- zz_set_row_hash(), "SET search_path = :"schema", :"kern", pg_temp" -- the SAME reason: psql
-- does NOT interpolate :"var" tokens INSIDE a dollar-quoted function BODY at all -- witnessed
-- directly authoring this amendment (`:"kern".migration_epoch` inside $fn$...$fn$ reaches the
-- server as a literal, un-substituted colon and fails with "syntax error at or near \":\""; only
-- the CREATE FUNCTION preamble, outside the dollar quotes, is ever substituted) -- so a bare
-- `migration_epoch` inside the body, resolved through search_path at RUNTIME, is the only correct
-- way to reach a :kern-schema table from inside this function, exactly s26's own established
-- idiom, not a new pattern.
CREATE OR REPLACE FUNCTION :"schema".validate_work_item() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  blockers text;
BEGIN
  IF NEW.kind = 'work_opened' THEN
    IF EXISTS (SELECT 1 FROM ledger WHERE kind = 'work_opened' AND work_slug = NEW.work_slug) THEN
      RAISE EXCEPTION 'Ledger policy: work item slug ''%'' already has an opening act — one opening act per slug (the Q5 defect: a decomposition ledgered twice under the same identity is refused, never silently duplicated).', NEW.work_slug;
    END IF;
    IF NEW.work_parent IS NOT NULL THEN
      IF NOT EXISTS (SELECT 1 FROM ledger WHERE kind = 'work_opened' AND work_slug = NEW.work_parent) THEN
        RAISE EXCEPTION 'Ledger policy: work item slug ''%'' names parent ''%'' which has no opening act — a --parent must reference an ALREADY-OPENED work item slug (dangling parents are refused here, unlike work_depends_on''s antecedent, which the spec deliberately leaves unrefused, s22). Open the parent first: ./led work open % "<title>", then retry this open with --parent %.', NEW.work_slug, NEW.work_parent, NEW.work_parent, NEW.work_parent;
      ELSIF work_parent_would_cycle(NEW.work_parent, NEW.work_slug) THEN
        RAISE EXCEPTION 'Ledger policy: work item slug ''%'' cannot be parented to ''%'' — ''%'' is already an ancestor of ''%'' in the work-tree, so this edge would create a cycle. Refused at construction, never a tolerated-but-flagged row (see work_item_violations.parent_cycle for the defense-in-depth read).', NEW.work_slug, NEW.work_parent, NEW.work_slug, NEW.work_parent;
      END IF;
    END IF;
  ELSIF NEW.kind IN ('work_claimed','work_depends_on','work_closed') THEN
    IF NOT EXISTS (SELECT 1 FROM ledger WHERE kind = 'work_opened' AND work_slug = NEW.work_slug) THEN
      RAISE EXCEPTION 'Ledger policy: work item slug ''%'' has no opening act — every later event on an item must reference an item that has been opened (invariant 2, item identity).', NEW.work_slug;
    END IF;
    -- sec-10 amendment: Element B's disposition-presence invariant, EPOCH-GATED (re-homed here
    -- from a plain CHECK -- see this file's AMENDMENT header for why a CHECK cannot express this).
    -- COALESCE(...,0) is the fail-safe direction if migration_epoch's one row were ever absent
    -- (it never should be -- this file's own INSERT above always seeds it before this trigger can
    -- run): epoch=0 means EVERYTHING is governed, the strict/safe reading, never fail-open.
    IF NEW.kind = 'work_closed'
       AND NEW.id > COALESCE((SELECT epoch FROM migration_epoch LIMIT 1), 0)
       AND NEW.work_review_disposition IS NULL THEN
      RAISE EXCEPTION 'Ledger policy: work_closed row for item ''%'' (ledger id %) carries no review disposition — every close act past this world''s migration epoch (id %, see %.migration_epoch) must be witnessed or deferred, never silent (s29 Element B, sec-10 epoch amendment). Retry with --review-witness <ref> or --review-deferred.', NEW.work_slug, NEW.id, (SELECT epoch FROM migration_epoch LIMIT 1), TG_TABLE_SCHEMA;
    END IF;
    IF NEW.kind = 'work_closed' AND COALESCE(NEW.work_strict_close, false) THEN
      IF NEW.work_review_disposition = 'deferred' THEN
        RAISE EXCEPTION 'Ledger policy: strict close of work item ''%'' requires --review-witness (a review already on record) — --review-deferred cannot satisfy strict mode''s immediate obligation-tree requirement, because a just-deferred obligation is, by definition, unresolved the moment it is created (s29 Element C). Record the review first (./led review ...), then close with --review-witness <ref>.', NEW.work_slug;
      ELSIF NEW.work_review_disposition = 'witnessed' THEN
        SELECT string_agg(format('%s (%s)', b.blocking_slug, b.reason), '; ' ORDER BY b.blocking_slug)
          INTO blockers
          FROM work_item_strict_blockers(NEW.work_slug) b;
        IF blockers IS NOT NULL THEN
          RAISE EXCEPTION 'Ledger policy: strict close of work item ''%'' refused — its obligation tree is unresolved: %. Resolve every named leaf, then retry (s29 Element C: strict close is a pure query over the derived conjunction, no stored verdict).', NEW.work_slug, blockers;
        END IF;
      END IF;
    END IF;
  END IF;
  RETURN NEW;
END; $fn$;
-- The trigger definition itself (name, timing, table) is UNCHANGED -- CREATE OR REPLACE FUNCTION
-- above is sufficient; re-issuing DROP/CREATE TRIGGER is harmless idempotence, kept for symmetry
-- with s22/s28's own script shape.
DROP TRIGGER IF EXISTS validate_work_item ON :"schema".ledger;
CREATE TRIGGER validate_work_item BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_work_item();

-- ============================================================================================
-- INDEPENDENCE GRADE -- ONE new column on review_detail, computed (never writer-asserted) by
-- EXTENDING validate_independence() (s17/s21's own function, CREATE OR REPLACE -- ADR-0012 P1:
-- it already fetches the (stamp_session,stamp_agent) pairs this grade needs). Closed vocabulary,
-- fail-safe same-principal default (spec Element C point 3). Nullable at the column level (this
-- delta does not assert the ORIGINAL review_detail shape it has not re-verified in full, ADR-0004
-- minimal-touch) -- the trigger below ALWAYS sets it on every insert, so it is NOT NULL in
-- practice without a second NOT NULL constraint asserted against a table shape this file does not
-- re-declare.
-- ============================================================================================
ALTER TABLE :"schema".review_detail ADD COLUMN IF NOT EXISTS discharge_grade text;
ALTER TABLE :"schema".review_detail DROP CONSTRAINT IF EXISTS discharge_grade_check;
ALTER TABLE :"schema".review_detail ADD CONSTRAINT discharge_grade_check CHECK (
    discharge_grade IS NULL
    OR discharge_grade IN ('same-principal', 'same-session', 'distinct-session', 'distinct-deployment'));
COMMENT ON COLUMN :"schema".review_detail.discharge_grade IS
  'Element C independence grade (kernel/lineage/s29): COMPUTED at write time by
   validate_independence() from the (stamp_session,stamp_agent) pair comparison between this
   review and the row it regards -- NEVER writer-asserted, closed vocabulary. Fail-safe default
   same-principal when either identity is absent (the least-independent assumption). This is a
   MACHINE-COMPUTED FACT about invocation separation ("how separate"), deliberately DISTINCT from
   the pre-existing writer-CLAIMED `independence` column ("technical"/"managerial"/"financial",
   s17) -- a claim of WHY independence matters vs. a computed fact of HOW separate the invocations
   actually were. distinct-deployment is closed vocabulary but UNREACHABLE from this function
   today (no deployment-id fact exists to compare) -- named in this file''s header, not hidden.';

CREATE OR REPLACE FUNCTION :"schema".validate_independence() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", pg_temp AS $fn$
DECLARE
  rev_session text; rev_agent text; rev_verified boolean; regards_id bigint;
  tgt_session text; tgt_agent text;
  distinct_pair boolean;
BEGIN
  SELECT stamp_session, stamp_agent, stamp_verified, regards
    INTO rev_session, rev_agent, rev_verified, regards_id FROM ledger WHERE id = NEW.ledger_id;
  SELECT stamp_session, stamp_agent INTO tgt_session, tgt_agent FROM ledger WHERE id = regards_id;

  IF NEW.independence IN ('technical','managerial','financial') THEN
    IF NOT COALESCE(rev_verified, false) THEN
      RAISE EXCEPTION 'Ledger policy: a review claiming independence (%) must carry a VERIFIED interception stamp — an unstamped review cannot establish it was a distinct invocation. Record independence=''self-review'' if you reviewed your own work, or write the review through a genuinely distinct stamped invocation (a separate agent).', NEW.independence;
    END IF;
    -- identity is the PAIR; a NULL half (on either row) is NEVER distinct — fail-safe, never fail-open.
    distinct_pair := (rev_session IS NOT NULL AND rev_agent IS NOT NULL
                       AND tgt_session IS NOT NULL AND tgt_agent IS NOT NULL)
                      AND (rev_session IS DISTINCT FROM tgt_session
                           OR rev_agent IS DISTINCT FROM tgt_agent);
    IF NOT distinct_pair THEN
      RAISE EXCEPTION 'Ledger policy: this review claims independence (%) but the SAME invocation (session=%, agent=%) wrote both it and the row it regards — one context cannot countersign its own work as independent (finding 31 / s21 session-aware distinctness). Record independence=''self-review'' if you reviewed your own work, or have a genuinely distinct invocation (a different session, or a different agent within this session) write the review.', NEW.independence, rev_session, rev_agent;
    END IF;
  END IF;

  -- Element C (s29): independence GRADE, computed for EVERY discharge act (not only an
  -- independence-CLAIMING one), closed vocabulary, fail-safe same-principal default.
  IF rev_session IS NULL OR rev_agent IS NULL OR tgt_session IS NULL OR tgt_agent IS NULL THEN
    NEW.discharge_grade := 'same-principal';
  ELSIF rev_session IS NOT DISTINCT FROM tgt_session AND rev_agent IS NOT DISTINCT FROM tgt_agent THEN
    NEW.discharge_grade := 'same-principal';
  ELSIF rev_session IS NOT DISTINCT FROM tgt_session THEN
    NEW.discharge_grade := 'same-session';
  ELSE
    -- 'distinct-deployment' is closed vocabulary but UNREACHABLE here today -- see header LIMITS.
    NEW.discharge_grade := 'distinct-session';
  END IF;

  RETURN NEW;
END; $fn$;
-- this trigger's home table is review_detail (s17), unchanged here.
DROP TRIGGER IF EXISTS validate_independence ON :"schema".review_detail;
CREATE TRIGGER validate_independence BEFORE INSERT ON :"schema".review_detail
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_independence();

-- ============================================================================================
-- s20/s22/s23/s24/s26/s28 LESSON RE-APPLIED: ledger_current + countersigned_in_force GAIN the
-- THREE new columns, APPENDED AT THE END. Explicit column lists throughout -- never `l.*`. Column
-- list = s28's exact list + the three s29 additions.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".ledger_current
    WITH (security_invoker = true) AS
SELECT l.id, l.ts, l.session, l.kind, l.statement, l.rationale, l.status, l.evidence,
       l.confidence, l.supersedes, l.refs, l.concern, l.enacts, l.actor, l.regards,
       l.amends, l.amends_scope, l.answers,
       l.stamp_session, l.stamp_agent, l.stamp_ts, l.stamp_hmac, l.stamp_verified,
       l.work_slug, l.work_title, l.work_depends_on, l.work_resolution, l.work_witness,
       l.stamp_invocation, l.event_declared_ts, l.row_hash, l.work_parent,
       l.work_review_disposition, l.work_review_ref, l.work_strict_close
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id);

CREATE OR REPLACE VIEW :"schema".countersigned_in_force
    WITH (security_invoker = true) AS
SELECT l.id, l.ts, l.session, l.kind, l.statement, l.rationale, l.status, l.evidence,
       l.confidence, l.supersedes, l.refs, l.concern, l.enacts, l.actor, l.regards,
       l.amends, l.amends_scope, l.answers,
       l.stamp_session, l.stamp_agent, l.stamp_ts, l.stamp_hmac, l.stamp_verified,
       l.work_slug, l.work_title, l.work_depends_on, l.work_resolution, l.work_witness,
       l.stamp_invocation, l.event_declared_ts, l.row_hash, l.work_parent,
       l.work_review_disposition, l.work_review_ref, l.work_strict_close
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".ledger r JOIN :"schema".review_detail d ON d.ledger_id = r.id
               WHERE r.kind = 'review' AND r.regards = l.id AND d.verdict = 'attest'
               AND NOT EXISTS (SELECT 1 FROM :"schema".ledger s2 WHERE s2.supersedes = r.id));

-- ============================================================================================
-- work_item_current (s22, extended s28) GAINS review_disposition/review_ref, sourced from the
-- SAME `closed` CTE that already carries resolution/witness (captured only on the closing row).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".work_item_current
    WITH (security_invoker = true) AS
WITH opened AS (
  SELECT work_slug AS slug, work_title AS title, work_parent AS parent_slug, id AS opened_id
  FROM :"schema".ledger WHERE kind = 'work_opened'
),
claimed AS (
  SELECT DISTINCT ON (work_slug) work_slug AS slug, actor AS claimant, id AS claimed_id
  FROM :"schema".ledger WHERE kind = 'work_claimed'
  ORDER BY work_slug, id DESC
),
closed AS (
  SELECT DISTINCT ON (work_slug) work_slug AS slug, work_resolution AS resolution,
         work_witness AS witness, work_review_disposition AS review_disposition,
         work_review_ref AS review_ref, id AS closed_id
  FROM :"schema".ledger WHERE kind = 'work_closed'
  ORDER BY work_slug, id DESC
)
SELECT o.slug, o.title,
       CASE WHEN c.slug IS NULL THEN 'open' ELSE 'closed' END AS state,
       c.resolution, c.witness, cl.claimant, o.parent_slug,
       c.review_disposition, c.review_ref
FROM   opened o
LEFT JOIN claimed cl ON cl.slug = o.slug
LEFT JOIN closed  c  ON c.slug  = o.slug;

-- ============================================================================================
-- work_review_gap -- Element A's item-keyed sibling of the pre-existing ACTOR-keyed `review_gap`
-- (s13/s15/s20, deliberately UNTOUCHED by this delta -- see header). One row per work_closed row
-- whose disposition is deferred and has NOT YET been discharged by a distinct-actor attest review
-- regarding the close row -- mirrors review_gap's own join shape (distinct actor, verdict=attest,
-- not superseded) exactly, one column over (item-keyed, not actor-keyed).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".work_review_gap
    WITH (security_invoker = true) AS
SELECT c.slug, c.close_id, c.closer
FROM (
  SELECT work_slug AS slug, id AS close_id, actor AS closer
  FROM :"schema".ledger WHERE kind = 'work_closed' AND work_review_disposition = 'deferred'
) c
WHERE NOT EXISTS (
  SELECT 1 FROM :"schema".ledger r
  JOIN :"schema".review_detail d ON d.ledger_id = r.id
  WHERE r.kind = 'review' AND r.regards = c.close_id AND d.verdict = 'attest' AND r.actor <> c.closer
    AND NOT EXISTS (SELECT 1 FROM :"schema".ledger s2 WHERE s2.supersedes = r.id)
);

-- ============================================================================================
-- GRANTS (mirrors s22/s28's own posture: append-only is inherited from the ledger/review_detail
-- themselves -- no new mutable surface exists to guard). ONE new view gets a fresh GRANT.
-- ============================================================================================
GRANT SELECT ON :"schema".work_review_gap TO :"role";
