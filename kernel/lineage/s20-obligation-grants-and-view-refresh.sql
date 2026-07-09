-- s20 OBLIGATION GRANTS + VIEW REFRESH — the countersign_obligation grants gap and the stale
-- `l.*` views (BACKLOG "Kernel defects found by full-surface exercise on toy (2026-07-09)").
--
-- An ADDITIVE delta applied ON TOP of the s15 kernel (the established remediation-delta idiom, cf.
-- s17-stamp-mechanism.sql / s19-trigger-search-path.sql / s13-remediation-*), NOT a retro-edit of a
-- frozen sNN record (ADR-0005 Rule 8) and NOT a second hand-copy of the kernel body (ADR-0012 P1:
-- one home per mechanism).
--
-- WHY (operator-side prose; NOT subject-visible — only the catalog objects inside the opaque db are):
--
--   Witnessed by the toy-pilot full-surface exercise (toy-project commit 9bf80c4, ledger rows
--   15-30). Two distinct defects, both members of the same broader class ("a capability the kernel's
--   own design commissions the subject to reach for is silently unreachable or silently stale"):
--
--   (1) GRANTS GAP. s15's preamble says the subject "is meant to reach for" the obligation/gap/
--       countersign fix-point, and s15's own GRANTS block grants SELECT on review_gap (the VIEW) —
--       but grants NOTHING on countersign_obligation (the TABLE the view joins, and the table a
--       subject must INSERT into to assign an obligation, and SELECT to read its own assignments).
--       review_gap is security_invoker, so the subject role gets "permission denied" reading
--       countersign_obligation through it AND writing an obligation directly. This is not new to
--       s15 — s13/s14 (grep-verified) never granted it either; it is a lineage-wide gap, not an s15
--       regression.
--   (2) STALE `l.*` VIEWS. ledger_current and countersigned_in_force are `SELECT l.*` views created
--       in s15. Postgres freezes a view's column *expansion* at CREATE time, so s17's five
--       `ALTER TABLE ledger ADD COLUMN stamp_*` never reached either view — both are verified (`\d`)
--       to lack stamp_session/stamp_agent/stamp_ts/stamp_hmac/stamp_verified. A consumer that wants
--       the stamp columns (e.g. to check `stamp_verified` before trusting a countersign, or to read
--       `stamp_agent` for the same distinctness question `review_stamp_distinctness` already answers
--       for reviews) must bypass the view and hit the base table directly — silently defeating the
--       view's whole purpose as the subject-facing read surface.
--
--   CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 amendment):
--
--     - INVARIANT: every catalog object that mediates a capability the kernel's own record commits
--       the subject to reach for is BOTH (a) actually GRANTed to the connecting role — not merely
--       defined — and (b) column-complete with respect to the base table it reads: a `SELECT l.*`/
--       `t.*` view is *frozen* at CREATE time (a Postgres property, not a bug, but a trap when the
--       base table is later ALTERed), so it must be re-issued with an EXPLICIT column list whenever
--       the base table gains a column, in the SAME delta that adds the column. A capability that
--       exists in DDL but is either ungranted or silently stale is, from the subject's chair,
--       indistinguishable from a capability that was never built.
--
--     - QUANTIFICATION UNIVERSE — enumerated by reading every table and view the s15+s17+s17b+s19
--       chain exposes to :role (the live, user-facing kernel per high_watermark_1.sql; s18's
--       reviewer-only INSERT posture is a deliberately different, narrower fence — consult 37 §1/§3
--       — and out of this class):
--         TABLES reachable off :"schema"/:"kern":
--           * ledger              — granted (s15).                            not in this class.
--           * review_detail       — granted (s15).                            not in this class.
--           * countersign_obligation — UNGRANTED since s13/s14/s15.           DEFECT (1), fixed here.
--           * kernel.principal        — granted (s15, measurement (d)).       not in this class.
--           * kernel.principal_role   — granted read-only (s15).              not in this class.
--         VIEWS (checked for BOTH the wildcard-expansion defect and the grant defect):
--           * ledger_current           — `SELECT l.*`, granted.   DEFECT (2), fixed here (columns only).
--           * countersigned_in_force   — `SELECT l.*`, granted.   DEFECT (2), fixed here (columns only).
--           * review_gap               — explicit columns already (l.id, l.actor, o.scope,
--             o.assigned_by), granted (s15).                                   not in this class.
--           * question_status          — explicit columns already, granted (s15).  not in this class.
--           * review_stamp_distinctness (s17) — explicit columns already, granted directly by s17.
--                                                                               not in this class.
--       So the wildcard-view defect has EXACTLY TWO members (both fixed here); the ungranted-table
--       defect has EXACTLY ONE member (fixed here). No other table or view in the applied chain
--       exhibits either defect — named, not assumed (ADR-0000 2026-07-02 amendment: the universe is
--       enumerated outward, not presumed to end at the two instances the exercise happened to hit).
--       The filed-but-not-folded-in candidate (s19 validate_* search_path residue, BACKLOG) is a
--       DIFFERENT class (schema-literal resolution, not grants/staleness) and is left for its own
--       ruling, per the BACKLOG entry's own text — folding it in here would be exactly the "the class
--       gets named at the scope of the fix already built" failure the amendment warns against.
--
--     - DENOMINATION: the grants fix is denominated directly in the object actually needed — TABLE-
--       level SELECT, INSERT on countersign_obligation itself, mirroring the ledger's own grant line
--       (`GRANT INSERT, SELECT ON :"schema".ledger TO :"role"`) — no schema-wide grant, no proxy
--       privilege. The view fix is denominated in the base table's OWN column set, enumerated
--       explicitly at authoring time — never a wildcard. This durability is only as good as the NEXT
--       delta's discipline: an explicit list is a POINT-IN-TIME snapshot, so a future `ALTER TABLE
--       ledger ADD COLUMN` must ship its own view refresh in the SAME delta or the class recurs one
--       column later. No mechanized check exists for that discipline today (review-only, per ADR-0000
--       Rule 2(b) — named, not silently left); a candidate future gate is a lineage-wide grep asserting
--       no bare `.*` selector survives in any `CREATE ... VIEW` under kernel/lineage/ — filed, not built,
--       since authoring a new gate is outside this delta's scope.
--
--   ON THE APPEND-ONLY QUESTION (posed by the task, answered from the record, not guessed): should
--   countersign_obligation ALSO gain the append-only/TRUNCATE guard trigger review_detail carries?
--   NO — the record already settles this. `s13-remediation-review-detail-truncate-guard.sql` (2026-
--   07-07) states explicitly: "review_detail is append-only attestation evidence (countersign_
--   obligation is mutable config in both, correctly unguarded)" — a DELIBERATE, dated, ratified
--   distinction: review_detail is a frozen verdict (an audit fact, once written, never revised), while
--   countersign_obligation is standing POLICY CONFIG (who currently obliges whom to countersign which
--   scope) that an operator may legitimately need to revise or revoke — e.g. reassigning an obligation
--   when a principal is retired, without that revision itself being a forgeable audit event the way a
--   rewritten verdict would be. Reversing that ruling here, without a new fact that contradicts it,
--   would itself be the ADR-0000 patch-reflex (changing a class's disposition to match the shape of a
--   different, unrelated fix already in hand). The `obligation_not_self_assigned` CHECK and the
--   ordinary table-level privilege model (no UPDATE/DELETE granted to :role at all — see below) remain
--   the sufficient, already-ratified posture; this delta touches ONLY SELECT/INSERT.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15): schema/role are psql variables
--   so this delta is VALIDATED on a throwaway substrate before any real apply. (No :kern variable is
--   declared — this delta touches no kernel-schema object.)
--     VALIDATE (reachable throwaway):
--        psql -h 192.168.122.1 -d harness -v schema=s20val -v role=s20val_rw \
--          -f s15-schema.sql -f s17-stamp-mechanism.sql -f s17-independence-vocabulary.sql \
--          -f s19-trigger-search-path.sql -f s20-obligation-grants-and-view-refresh.sql
--     REAL (owed to a maintainer-assented apply on the live vsr deployment, NOT taken here):
--        psql -h 192.168.122.1 -d vsr -f s20-obligation-grants-and-view-refresh.sql
--   NEVER apply bare against a deployment that matters — spell out every -v var explicitly (standing
--   rule). This delta was authored and witnessed on a scratch schema pair only; see BACKLOG for the
--   scratch schema name and the exact toycolors apply one-liner pending maintainer assent.
-- Run as the schema owner (bork). Idempotent (GRANT is idempotent; CREATE OR REPLACE + DROP/CREATE
-- TRIGGER are idempotent).

\if :{?schema}
\else
  \set schema public
\endif
\if :{?role}
\else
  \set role vsr_rw
\endif

-- ============================================================================================
-- DEFECT (1) — the countersign_obligation grants gap
-- ============================================================================================
-- Mirrors the ledger's own grant posture exactly (GRANT INSERT, SELECT ON :"schema".ledger TO
-- :"role"): the subject may append its own obligation assignments and read them back. The
-- obligation_not_self_assigned CHECK (s15) and the absence of any UPDATE/DELETE grant (the mutable-
-- config posture is operator-only revision, per the s13-remediation record above) continue to govern
-- unchanged — this delta widens no other privilege.
GRANT SELECT, INSERT ON :"schema".countersign_obligation TO :"role";

-- ============================================================================================
-- DEFECT (2) — the stale `l.*` views, refreshed with EXPLICIT column lists (never `l.*` again —
-- that idiom is how this class formed). Column order matches the base table's own declaration order
-- (s15 + the five s17 stamp_* additions); WITH (security_invoker = true) is preserved unchanged.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".ledger_current
    WITH (security_invoker = true) AS
SELECT l.id, l.ts, l.session, l.kind, l.statement, l.rationale, l.status, l.evidence,
       l.confidence, l.supersedes, l.refs, l.concern, l.enacts, l.actor, l.regards,
       l.amends, l.amends_scope, l.answers,
       l.stamp_session, l.stamp_agent, l.stamp_ts, l.stamp_hmac, l.stamp_verified
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id);

CREATE OR REPLACE VIEW :"schema".countersigned_in_force
    WITH (security_invoker = true) AS
SELECT l.id, l.ts, l.session, l.kind, l.statement, l.rationale, l.status, l.evidence,
       l.confidence, l.supersedes, l.refs, l.concern, l.enacts, l.actor, l.regards,
       l.amends, l.amends_scope, l.answers,
       l.stamp_session, l.stamp_agent, l.stamp_ts, l.stamp_hmac, l.stamp_verified
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".ledger r JOIN :"schema".review_detail d ON d.ledger_id = r.id
               WHERE r.kind = 'review' AND r.regards = l.id AND d.verdict = 'attest'
               AND NOT EXISTS (SELECT 1 FROM :"schema".ledger s2 WHERE s2.supersedes = r.id));
