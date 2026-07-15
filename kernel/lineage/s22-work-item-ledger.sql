-- s22 WORK-ITEM LEDGER — work state as ledger-derived fact (design/S22-WORK-ITEM-LEDGER.md,
-- Fable-authored spec, session be693afb, 2026-07-09, PENDING MAINTAINER RATIFICATION — this delta
-- is AUTHORED and SCRATCH-WITNESSED only; APPLYING it to any live deployment is the maintainer's
-- act (bootstrap/apply-delta.sh), not taken here). An ADDITIVE delta applied ON TOP of the
-- s15/s17/s17b/s19/s20/s21 kernel (the established remediation-delta idiom), NOT a retro-edit of a
-- frozen sNN record (ADR-0005 Rule 8) and NOT a second hand-copy of the kernel body (ADR-0012 P1:
-- one home per mechanism).
--
-- WHY (operator-side prose; NOT subject-visible — only the catalog objects inside the opaque db
-- are): design/WORK-ITEM-DECISION-MEMO.md named the gap ("is my task automatically tracked, or a
-- manual chore?" currently answers: manual chore) and named candidate (1) — work-item EVENTS live
-- in the ledger, state is a DERIVED VIEW — as the leading candidate pending run-2/run-3 evidence.
-- design/S22-WORK-ITEM-LEDGER.md freezes on that evidence (Q1/Q2/Q4/Q5 answered; Q3 stays
-- unexercised, deferred to witnessed operator questions). This delta is the DDL author's mapping
-- of the spec's six binding invariants onto the REAL s15+ lineage surface.
--
-- SSOT (spec invariant 1): NO new base table. Work items are FIVE NEW COLUMNS on the existing
-- `ledger` table (work_slug/work_title/work_depends_on/work_resolution/work_witness) plus FOUR
-- NEW `kind` VALUES (work_opened/work_claimed/work_depends_on/work_closed) — the kind/edge
-- vocabulary extension the spec licenses, never a parallel table universe. Derived state lives
-- ONLY in the two new views below.
--
-- INVARIANT 2 CHOICE — NAMED (the task's own instruction: name the refused-vs-visible choice and
-- why). "Two opening acts with the same slug ... refused (the Q5 defect made unrepresentable) —
-- or, if refusal is unachievable at the ledger's trigger layer without breaking append-only
-- semantics, made VISIBLE as a violations row." REFUSAL IS CHOSEN. The trigger architecture
-- already refuses malformed inserts without touching append-only semantics — append-only forbids
-- UPDATE/DELETE/TRUNCATE of EXISTING rows (append_only()), never a BEFORE INSERT trigger refusing
-- a NEW row before it lands (validate_enacts/validate_review/validate_amends/validate_answers are
-- the standing precedent: each REFUSES a malformed INSERT outright). A duplicate-open INSERT is
-- refused by `validate_work_item()` below, the identical mechanism. This is also the STRONGER
-- ADR-0000 answer (Rule 2(a): the loudest possible failure is at construction time, not a
-- tolerated-but-flagged row) — so refusal is preferred wherever the trigger layer can carry it,
-- and it can, here. `work_item_violations` STILL carries a duplicate-open member (defense in
-- depth, matching this codebase's own belt-and-braces precedent — ledger_dto.lp's
-- decomp_sod_violation flags a state decomp_attested's own SoD gate already forbids, and
-- ledger_support.lp's affirm_sod_violation mirrors it) — under normal operation via this trigger
-- it is PROVABLY VACUOUS (unreachable through ordinary INSERT), not a live detector; named, not
-- silently claimed as reachable.
--
-- THE SAME CHOICE, EXTENDED TO INVARIANT 3's OWN TEXT. Invariant 3 states plainly (no hedge):
-- "closed ⇒ resolution + witness reference, where `shipped` REQUIRES a witness" — the omega
-- shipped-without-ship-ref invariant, run 1's uncommitted-deliverable lesson. This is enforced as
-- a table CHECK constraint (work_shipped_requires_witness below) — CONSTRUCTION-TIME refusal, the
-- strongest form (stronger even than a trigger: an illegal row cannot exist even transiently).
-- `work_item_violations` carries a shipped-without-witness member too, same belt-and-braces
-- reasoning, same provable-vacuity-under-normal-operation caveat, named.
--
-- INVARIANT 2's OWN COROLLARY, APPLIED (not scope creep — the spec's own sentence: "every LATER
-- event on that item REFERENCES it"). A work_claimed/work_depends_on/work_closed row naming a
-- slug with NO prior work_opened row is the same identity-integrity hazard duplicate-open is, one
-- token over (a typo'd slug on a claim/close is exactly as silent as a typo'd slug on an open) —
-- CLAUDE.md's engineering-responsibility clause names this the kind of hazard met in passing that
-- gets fixed, not routed around, when it sits inside the very columns/trigger being authored.
-- `validate_work_item()` refuses this too, as a direct reading of invariant 2's own sentence.
-- Deliberately NOT extended further: a claim-after-close or a second close on an already-closed
-- slug is NOT refused (Q4's evidence — "status never left 'open' in 33/33 rows" — gives no basis
-- for inventing disposition-churn machinery the spec's Q4 evidence explicitly says v1 forgoes;
-- named here as OUT of this delta's scope, not silently omitted).
--
-- WHAT IS DELIBERATELY *NOT* REFUSED AT INSERT (spec invariant 4's own text, no hedge offered):
-- a `work_depends_on` row's ANTECEDENT slug (the slug it names as depended-upon, as opposed to
-- its OWN work_slug, which IS gated per the paragraph above) may name a slug never opened — a
-- forward-declared or Q5-typo'd dependency. The spec lists "depends_on naming an unknown slug" as
-- a `work_item_violations` member with no refusal option offered, so this is left VISIBLE-ONLY,
-- genuinely reachable (unlike the two provably-vacuous members above) — the scratch witness's
-- non-empty-result fixture (spec invariant 4's own requirement) is carried by this member and by
-- dependency-cycle detection, both left unrefused by design.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 amendment):
--
--   - INVARIANT: every work-item fact is a ledger row under the extended kind/edge vocabulary;
--     "current state" and every cross-item judgment (duplicate identity, dangling dependency,
--     dependency cycle, shipped-without-witness) are DERIVED views, never a second table; and —
--     the s20 lesson, RE-APPLIED here to my own new columns, not only cited — every view that
--     already read `ledger` with an EXPLICIT column list is re-issued to append the five new
--     columns IN THIS SAME DELTA, or the "column-complete w.r.t. the base table" class s20 fixed
--     recurs one column later.
--
--   - QUANTIFICATION UNIVERSE — enumerated by reading every table and view the
--     s15+s17+s17b+s19+s20+s21 chain exposes to :role (the live, user-facing kernel per
--     high_watermark_1.sql), re-verifying s20's own enumeration and checking it against the five
--     NEW columns:
--       TABLES reachable off :"schema"/:"kern": unchanged — no new base table (invariant 1).
--       VIEWS re-read for the wildcard-and-staleness class s20 named:
--         * ledger_current         — explicit column list (s20). GAINS the 5 new columns HERE
--           (APPENDED at the end, s21's own additive-column-order idiom), else it silently
--           stales exactly as s20's own defect (2) did for the stamp_* columns.
--         * countersigned_in_force — same: explicit list (s20), GAINS the 5 new columns HERE.
--         * review_gap             — explicit cols (l.id, l.actor, o.scope, o.assigned_by); NONE
--           of the 5 new columns is meaningful to an obligation-gap read. NOT extended — named,
--           not silently skipped.
--         * question_status        — explicit cols, no ledger-row passthrough at all. NOT in
--           this class.
--         * review_stamp_distinctness (s17/s21) — reads only stamp_*/actor via r./g. aliases, no
--           general ledger passthrough. NOT in this class.
--       So the "column-complete" class has exactly TWO members this delta must re-issue (both
--       done here); three views are checked and confirmed NOT members (named, not assumed).
--     KIND VOCABULARY — the ONE CHECK list (`ledger_kind_check`, s15's inline CHECK, unnamed-then-
--       auto-named by Postgres) is the sole home; grepped, confirmed no second hand-copy exists
--       anywhere in kernel/lineage/ or toy-project (toy-project untouched by this delta in any
--       case, per the operator's own apply-only posture).
--     GRANTS — mirrors the ledger's own posture (invariant 5): the two NEW views get a fresh
--       GRANT SELECT (the s20 grants-gap lesson, applied FROM THE START rather than discovered
--       later); the five new columns live on the ALREADY-granted `ledger` table (INSERT+SELECT
--       since s15), so no table-level grant change is needed for them.
--     ENGINE — invariant 6: `engine/lp/work_items.lp` (ASP) + `work_item_floor_atoms()`
--       (`engine/ledger_floor.py`, the SQL floor mirror, Increment 3 section appended) +
--       `engine/work_item_scratch.py` / `kernel/fixtures/s22_work_item_fixture.py` (the
--       differential harness) are this delta's engine-layer companions, authorized by THIS
--       Fable-authored spec per the standing rule (item 6). NOT wired into `judge`
--       (bootstrap/templates/judge.tmpl calls `ledger_differential.py` hardcoded to
--       `ledger_tnow.lp` only) — verified: `judge` does not auto-discover `engine/lp/*.lp`, and
--       NEITHER does any of the four pre-existing non-core `.lp` files (ledger_dto.lp,
--       ledger_support.lp, ledger_acts.lp, ledger_assumes.lp) get any `judge` wiring; each has its
--       own bespoke scratch-differential script instead. `work_items.lp` follows that exact,
--       established precedent — no `judge`/`ledger_differential.py` change is made or needed.
--
--   - DENOMINATION: the identity primitive is the SLUG (a stable text identity spanning
--     dispatches — design memo's axis-2 "item identity across dispatches"), never the ledger row
--     id (which is per-EVENT, not per-ITEM) — a slug is carried on every work_* row exactly once
--     per its role (opening act titles it, later acts merely cite it). The shipped-without-
--     witness bound is denominated in the WITNESS FIELD ITSELF (a non-empty text — a commit hash /
--     ledger row ref / artifact path, per the spec), never a proxy (e.g. "resolution is present" is
--     NOT treated as "witness is present" — the CHECK below tests `work_witness` directly).
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/s17/s19/s20/s21): schema/kern
--   are psql variables (no :role-affecting change beyond the two new view GRANTs, which use the
--   existing :role var) so this delta is VALIDATED on a throwaway substrate before any real apply.
--     VALIDATE (reachable throwaway):
--        psql -h 192.168.122.1 -d harness -v schema=s22val -v kern=s22val_kernel -v role=s22val_rw \
--          -f s15-schema.sql -f s17-stamp-mechanism.sql -f s17-independence-vocabulary.sql \
--          -f s19-trigger-search-path.sql -f s20-obligation-grants-and-view-refresh.sql \
--          -f s21-session-aware-distinctness.sql -f s22-work-item-ledger.sql
--     REAL (owed to a maintainer-assented apply on a live deployment — NOT taken here; RATIFICATION
--     PENDING, per this file's own header — never apply bare, spell out every -v var explicitly):
--        psql -h 192.168.122.1 -d <db> -v schema=<schema> -v kern=<kern> -v role=<role> \
--          -f s22-work-item-ledger.sql
--   This delta was authored and scratch-witnessed on a scratch schema pair in the TOY db only
--   (schema s22probe / s22probe_kernel, role s22probe_rw; kernel/fixtures/s22_work_item_fixture.py).
--   NEVER applied to toycolors, run3, run4, or any live schema by this pass.
-- Run as the schema owner (bork). Idempotent (ADD COLUMN IF NOT EXISTS; DROP+ADD CONSTRAINT;
-- CREATE OR REPLACE + DROP/CREATE TRIGGER).

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
-- THE FIVE NEW COLUMNS (invariant 1: SSOT — no new base table; work state rides the ledger row).
-- ============================================================================================
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS work_slug        text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS work_title       text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS work_depends_on  text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS work_resolution  text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS work_witness     text;

COMMENT ON COLUMN :"schema".ledger.work_slug IS
  'Work-item identity (spec invariant 2): the stable text slug this event concerns, carried on
   every work_opened/work_claimed/work_depends_on/work_closed row. NOT NULL for those four kinds,
   NULL for every other kind (work_slug_kind_shape below). One opening act per slug (refused,
   validate_work_item); every later event must reference an already-opened slug (same trigger).';
COMMENT ON COLUMN :"schema".ledger.work_title IS
  'The item''s title, carried ONLY on its opening act (work_title_kind_shape below). Prose lives
   here, not in the engine EDB (IDS ARE THE INTERCHANGE; TEXT STAYS HOME, ledger_edb.py rule 1).';
COMMENT ON COLUMN :"schema".ledger.work_depends_on IS
  'For a work_depends_on row: the ANTECEDENT slug this item (work_slug) depends on. Deliberately
   NOT refused when the antecedent names a slug never opened (spec invariant 4 offers no refusal
   option here) — surfaced instead by work_item_violations.depends_on_unknown_slug and by
   engine/lp/work_items.lp''s work_depends_on_unknown/2.';
COMMENT ON COLUMN :"schema".ledger.work_resolution IS
  'For a work_closed row: one of shipped|superseded|dropped|deferred (spec invariant 3''s closed
   vocabulary). NULL for every other kind (work_resolution_kind_shape below).';
COMMENT ON COLUMN :"schema".ledger.work_witness IS
  'For a work_closed row: the witness reference (commit hash / ledger row / artifact path).
   REQUIRED (non-empty) when work_resolution=''shipped'' (work_shipped_requires_witness below —
   the omega shipped-without-ship-ref invariant, enforced at construction time).';

-- ============================================================================================
-- KIND VOCABULARY EXTENSION (invariant 3's event vocabulary; invariant 1's "extends the CHECK
-- list, adds no base table"). ledger_kind_check is s15's inline CHECK, Postgres-auto-named.
-- ============================================================================================
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS ledger_kind_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT ledger_kind_check CHECK (kind IN
    ('assumption','decision','question','verification',
     'finding','snag','revision','note','review',
     'work_opened','work_claimed','work_depends_on','work_closed'));

-- ============================================================================================
-- SHAPE INVARIANTS (illegal states unrepresentable AT CONSTRUCTION, ADR-0000 Rule 1 — the
-- strongest available surface, stronger than a trigger: a table CHECK admits no illegal row even
-- transiently). Each is a two-way correlation: the column is present IFF the kind licenses it.
-- ============================================================================================
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_slug_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_slug_kind_shape CHECK (
    (kind IN ('work_opened','work_claimed','work_depends_on','work_closed')) = (work_slug IS NOT NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_title_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_title_kind_shape CHECK (
    (kind = 'work_opened') = (work_title IS NOT NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_depends_on_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_depends_on_kind_shape CHECK (
    (kind = 'work_depends_on') = (work_depends_on IS NOT NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_resolution_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_resolution_kind_shape CHECK (
    (kind = 'work_closed') = (work_resolution IS NOT NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_witness_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_witness_kind_shape CHECK (
    work_witness IS NULL OR kind = 'work_closed');

-- the closed resolution vocabulary (spec invariant 3).
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_resolution_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_resolution_check CHECK (
    work_resolution IS NULL OR work_resolution IN ('shipped','superseded','dropped','deferred'));

-- the omega shipped-without-ship-ref invariant, ENFORCED at construction time (invariant 3, no
-- hedge in the spec's own text: shipped "REQUIRES a witness"). A shipped resolution with a NULL
-- or blank witness is unconstructable.
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_shipped_requires_witness;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_shipped_requires_witness CHECK (
    work_resolution IS DISTINCT FROM 'shipped'
    OR (work_witness IS NOT NULL AND btrim(work_witness) <> ''));

-- ============================================================================================
-- WRITE-BOUNDARY TRIGGER (invariant 2: item identity, REFUSAL chosen — see header). Fires
-- BEFORE INSERT; per-function SET search_path (the s19/s21 lesson APPLIED FROM THE START rather
-- than re-discovered later — this function reads only the ledger's OWN schema, unqualified,
-- exactly the validate_enacts/review/amends/answers shape s19+s21 had to retrofit).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_work_item() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", pg_temp AS $fn$
BEGIN
  IF NEW.kind = 'work_opened' THEN
    IF EXISTS (SELECT 1 FROM ledger WHERE kind = 'work_opened' AND work_slug = NEW.work_slug) THEN
      RAISE EXCEPTION 'Ledger policy: work item slug ''%'' already has an opening act — one opening act per slug (the Q5 defect: a decomposition ledgered twice under the same identity is refused, never silently duplicated).', NEW.work_slug;
    END IF;
  ELSIF NEW.kind IN ('work_claimed','work_depends_on','work_closed') THEN
    IF NOT EXISTS (SELECT 1 FROM ledger WHERE kind = 'work_opened' AND work_slug = NEW.work_slug) THEN
      RAISE EXCEPTION 'Ledger policy: work item slug ''%'' has no opening act — every later event on an item must reference an item that has been opened (invariant 2, item identity).', NEW.work_slug;
    END IF;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_work_item ON :"schema".ledger;
CREATE TRIGGER validate_work_item BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_work_item();

-- ============================================================================================
-- s20 LESSON RE-APPLIED: ledger_current + countersigned_in_force GAIN the 5 new columns, APPENDED
-- at the end (s21's own additive-column-order idiom — GRANT survives CREATE OR REPLACE VIEW only
-- if pre-existing columns keep their name/type/order). Explicit column lists throughout — never
-- `l.*` again (the class this re-issue exists to foreclose one more time).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".ledger_current
    WITH (security_invoker = true) AS
SELECT l.id, l.ts, l.session, l.kind, l.statement, l.rationale, l.status, l.evidence,
       l.confidence, l.supersedes, l.refs, l.concern, l.enacts, l.actor, l.regards,
       l.amends, l.amends_scope, l.answers,
       l.stamp_session, l.stamp_agent, l.stamp_ts, l.stamp_hmac, l.stamp_verified,
       l.work_slug, l.work_title, l.work_depends_on, l.work_resolution, l.work_witness
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id);

CREATE OR REPLACE VIEW :"schema".countersigned_in_force
    WITH (security_invoker = true) AS
SELECT l.id, l.ts, l.session, l.kind, l.statement, l.rationale, l.status, l.evidence,
       l.confidence, l.supersedes, l.refs, l.concern, l.enacts, l.actor, l.regards,
       l.amends, l.amends_scope, l.answers,
       l.stamp_session, l.stamp_agent, l.stamp_ts, l.stamp_hmac, l.stamp_verified,
       l.work_slug, l.work_title, l.work_depends_on, l.work_resolution, l.work_witness
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".ledger r JOIN :"schema".review_detail d ON d.ledger_id = r.id
               WHERE r.kind = 'review' AND r.regards = l.id AND d.verdict = 'attest'
               AND NOT EXISTS (SELECT 1 FROM :"schema".ledger s2 WHERE s2.supersedes = r.id));

-- ============================================================================================
-- work_item_current (invariant 4): one row per slug, LATEST-EVENT semantics, explicit columns.
-- Driven by `opened` (exactly one row per slug — duplicates refused by validate_work_item), left-
-- joined to the latest claim (by id, the id-is-order convention this whole lineage uses — never
-- ts) and the latest close.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".work_item_current
    WITH (security_invoker = true) AS
WITH opened AS (
  SELECT work_slug AS slug, work_title AS title, id AS opened_id
  FROM :"schema".ledger WHERE kind = 'work_opened'
),
claimed AS (
  SELECT DISTINCT ON (work_slug) work_slug AS slug, actor AS claimant, id AS claimed_id
  FROM :"schema".ledger WHERE kind = 'work_claimed'
  ORDER BY work_slug, id DESC
),
closed AS (
  SELECT DISTINCT ON (work_slug) work_slug AS slug, work_resolution AS resolution,
         work_witness AS witness, id AS closed_id
  FROM :"schema".ledger WHERE kind = 'work_closed'
  ORDER BY work_slug, id DESC
)
SELECT o.slug, o.title,
       CASE WHEN c.slug IS NULL THEN 'open' ELSE 'closed' END AS state,
       c.resolution, c.witness, cl.claimant
FROM   opened o
LEFT JOIN claimed cl ON cl.slug = o.slug
LEFT JOIN closed  c  ON c.slug  = o.slug;

-- ============================================================================================
-- work_item_violations (invariant 4): the omega port. Four members, ONE recursive-CTE query
-- (Postgres requires a single `WITH RECURSIVE` header covering every CTE when any one is
-- recursive — `reach` is the recursive member; the rest are plain). duplicate_open and
-- shipped_without_witness are PROVABLY VACUOUS under normal operation (both refused at
-- construction above) — defense in depth, named as such in the header, not claimed reachable.
-- depends_on_unknown_slug and dependency_cycle are genuinely reachable (deliberately unrefused —
-- see header) and are what the scratch witness's non-empty-result fixture exercises.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".work_item_violations
    WITH (security_invoker = true) AS
WITH RECURSIVE
  opens AS (
    SELECT work_slug AS slug, count(*) AS n
    FROM :"schema".ledger WHERE kind = 'work_opened'
    GROUP BY work_slug
  ),
  dup_open AS (
    SELECT slug FROM opens WHERE n > 1
  ),
  shipped_no_witness AS (
    SELECT work_slug AS slug, id
    FROM :"schema".ledger
    WHERE kind = 'work_closed' AND work_resolution = 'shipped'
      AND (work_witness IS NULL OR btrim(work_witness) = '')
  ),
  deps AS (
    SELECT work_slug AS dependent, work_depends_on AS antecedent
    FROM :"schema".ledger WHERE kind = 'work_depends_on'
  ),
  dangling_dep AS (
    SELECT d.dependent AS slug, d.antecedent
    FROM deps d
    WHERE NOT EXISTS (SELECT 1 FROM :"schema".ledger o
                       WHERE o.kind = 'work_opened' AND o.work_slug = d.antecedent)
  ),
  reach(start_slug, cur) AS (
    SELECT dependent, antecedent FROM deps
    UNION
    SELECT r.start_slug, d.antecedent FROM reach r JOIN deps d ON d.dependent = r.cur
  ),
  dep_cycle AS (
    SELECT DISTINCT start_slug AS slug FROM reach WHERE cur = start_slug
  )
SELECT 'duplicate_open'::text AS violation, slug, NULL::text AS detail FROM dup_open
UNION ALL
SELECT 'shipped_without_witness', slug, 'ledger row ' || id FROM shipped_no_witness
UNION ALL
SELECT 'depends_on_unknown_slug', slug, 'depends on ' || antecedent FROM dangling_dep
UNION ALL
SELECT 'dependency_cycle', slug, NULL FROM dep_cycle;

-- ============================================================================================
-- GRANTS (invariant 5: mirror the ledger's own posture; the s20 grants-gap lesson applied FROM
-- THE START). Append-only is inherited from the ledger itself — no new mutable surface exists to
-- guard (no new table; the 5 new columns ride the already-append-only `ledger` row).
-- ============================================================================================
GRANT SELECT ON :"schema".work_item_current, :"schema".work_item_violations TO :"role";
