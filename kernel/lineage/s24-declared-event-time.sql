-- s24 DECLARED EVENT TIME — the late-entry discipline's mechanism half (kernel delta + Proposal 2
-- of design/LATE-ENTRY-AND-INTAKE-SEMANTICS.md; RATIFIED by the maintainer 2026-07-11 evening,
-- "Late-entry design RATIFIED, all three proposals", BACKLOG.md). Authored FROM the ratified memo
-- (Sonnet-authored per the delegation contract), scratch-witnessed both polarities, differential
-- AGREE. An ADDITIVE delta applied ON TOP of the s15/s17/s17b/s19/s20/s21/s22/s23 kernel (the
-- established remediation-delta idiom, cf. s17-stamp-mechanism.sql / s20-* / s22-* / s23-*), NOT a
-- retro-edit of a frozen sNN record (ADR-0005 Rule 8) and NOT a second hand-copy of the kernel
-- body (ADR-0012 P1: one home per mechanism).
--
-- WHY (operator-side prose; NOT subject-visible — only the catalog objects inside the opaque db are):
--
--   design/LATE-ENTRY-AND-INTAKE-SEMANTICS.md's Proposal 2. Real-world paper-trail mandates
--   (ALCOA+) treat a genuinely late entry as LEGAL when it is *declared* ("late entry, event
--   occurred at T, reason") — what they forbid is narrating past conduct as if it were live,
--   undeclared. The kernel had a way to write a row and a way (s23) to say WHICH INVOCATION wrote
--   it, but no way for a writer to say WHEN THE EVENT ITSELF happened, distinct from `ts` (INSERT
--   time). This delta adds exactly that: a nullable `event_declared_ts` column any writer may
--   optionally set at INSERT time via `led --event-time <iso-ts> ...` (bootstrap/templates/
--   led.tmpl, this same commission). Part 2's audit verb (engine/contemp_audit.py +
--   engine/lp/contemporaneity.lp, this same commission) is the ONLY consumer: a row whose declared
--   event time precedes its own `ts` by more than a measured threshold, and that DOES carry a
--   declared time, verdicts LATE_DECLARED (exit 0 — the mandate permits it); the identical gap
--   with NO declared time still verdicts BACKFILL_SUSPECT (exit 1 — undeclared, unchanged).
--
--   NOT A STAMP; A DECLARATION (the load-bearing distinction from s23's `stamp_invocation`,
--   named so a future reader never conflates the two). `stamp_invocation` is CAPTURE-ONLY —
--   read from a hook-injected GUC the writer cannot type into an INSERT, so it is trustworthy
--   exactly to the degree the interception choke point is trustworthy (s17's disclosed
--   tripwire-not-authentication posture). `event_declared_ts` is the OPPOSITE shape: it is a
--   plain writer-supplied column, bound the same way `evidence`/`confidence`/`rationale` already
--   are (a psql `-v` bind in the generic INSERT, no trigger, no GUC, no HMAC). A writer can set it
--   to anything, including a lie. That is not a defect to close here — it is the exact shape a
--   paper late-entry declaration has always had (the record trusts the declaration the way it
--   trusts every other prose field; a false declaration is a provenance question for review/audit
--   to catch, not something a database CHECK can refute) — and it is why this delta adds NO
--   refusal and NO verification semantics: the column is honest exactly as far as the writer is
--   honest, disclosed plainly, same posture s23 already disclosed for its own unauthenticated
--   token (`the token makes the record's SHAPE honest, not the mind legible`). So this delta
--   relaxes no refusal and alters no existing semantics — the class-ratified fail-safe shape
--   (maintainer ruling 2026-07-09: ADDS a derived-nothing, writer-supplied-nullable column only,
--   touching no trigger, no CHECK, no existing view's WHERE clause).
--
--   BACKWARD-HONEST: rows written before this ALTER carry NULL event_declared_ts (nullable, no
--   DEFAULT) — visibly "pre-s24 era", never guessed. engine/contemp_edb.py (this same commission)
--   capability-gates on the column's presence exactly as it already does for `stamp_invocation`:
--   a pre-s24 world simply emits no `row_declared/2` facts, so the LATE_DECLARED verdict member
--   can never fire there and the identical-gap-undeclared BACKFILL_SUSPECT path is UNCHANGED —
--   the wiredness-not-corpus-emptiness discipline (BACKLOG "run9" fix) applied one delta later.
--
--   CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 amendment):
--
--     - INVARIANT: `event_declared_ts` is a plain nullable timestamptz column on `ledger`,
--       writer-supplied at INSERT (no trigger, no GUC, no verification) — and, the s20/s22/s23
--       lesson RE-APPLIED to this new column, not merely cited — every view that reads `ledger`
--       with an EXPLICIT column list is re-issued to append event_declared_ts IN THIS SAME DELTA,
--       or the "column-complete w.r.t. the base table" class s20 fixed (and s23 re-fixed one
--       column later) recurs a second time.
--
--     - QUANTIFICATION UNIVERSE — enumerated by re-reading every view the s15+s17+s17b+s19+s20+
--       s21+s22+s23 chain exposes to :role (the live, user-facing kernel), re-verifying s20's/
--       s23's own enumeration against the ONE new column:
--         * ledger_current           — explicit column list (s20/s22/s23). GAINS event_declared_ts
--           HERE, APPENDED AT THE END (CREATE OR REPLACE VIEW forbids reordering/renaming existing
--           columns without dropping the GRANT, so the new column cannot be grouped next to `ts` —
--           it appends, exactly as s23's own stamp_invocation had to append after the work_* block).
--         * countersigned_in_force   — same: explicit list (s20/s22/s23), GAINS event_declared_ts
--           HERE.
--         * review_gap               — explicit cols (l.id, l.actor, o.scope, o.assigned_by); a
--           declared event time is not meaningful to an obligation-gap read. NOT extended — named.
--         * question_status          — explicit cols, no ledger-row passthrough. NOT in this class.
--         * work_item_current / work_item_violations (s22) — derived work-state aggregates, no
--           general ledger-row passthrough; a declared event time is not a work-state fact. NOT in
--           this class — named, not silently skipped.
--         * review_stamp_distinctness (s17/s21) — reads only stamp_session/stamp_agent/actor via
--           r./g. aliases (the distinctness question keys on the WRITING invocation, never on a
--           declared event time). NOT in this class; deliberately NOT extended.
--       So the "column-complete" class has EXACTLY TWO members this delta must re-issue (both done
--       here); four views are checked and confirmed NOT members (named, not assumed) — the same
--       four s23 named, re-verified rather than merely cited.
--     TRIGGERS — NONE touched. `event_declared_ts` is NOT captured by set_stamp (s17/s19/s23's sole
--       capture path, grep-verified untouched by this delta) — it is an ordinary writer-supplied
--       INSERT column, bound the same way `evidence`/`rationale`/`confidence` already are. No
--       trigger-definition change of any kind ships in this delta.
--     ENGINE — engine/contemp_edb.py (this same commission) reads this column, capability-gated
--       exactly as it already reads stamp_invocation: `has_col("event_declared_ts")` determines
--       whether `row_declared/2` facts are emitted at all; engine/lp/contemporaneity.lp's
--       LATE_DECLARED verdict logic is the sole consumer (design/LATE-ENTRY-AND-INTAKE-
--       SEMANTICS.md Proposal 2) — named here, unlike s23's "ENGINE — NONE", because this delta's
--       whole reason for existing IS an engine consumer, not a capture-only kernel fact with no
--       reader yet.
--
--     - DENOMINATION: the column is `timestamptz` (matching `ledger.ts`'s own type exactly, so the
--       audit's gap arithmetic — declared time vs. write time — is a same-type subtraction, never a
--       cross-type cast), nullable with no DEFAULT (the pre-s24 era, and every row where a writer
--       chooses not to declare a time, must read as NULL, never a fabricated value). No GUC is
--       involved (contrast s23's `app.vendor_invocation`): this column is bound the same way every
--       other writer-supplied ledger column already is, via `bootstrap/templates/led.tmpl`'s
--       existing psql `-v`/NULLIF idiom (this same commission's `--event-time` flag).
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/s17/s20/s22/s23): schema/kern
--   are psql variables (no :role-affecting change — CREATE OR REPLACE VIEW preserves the existing
--   GRANTs, and this delta adds no new grantable object) so this delta is VALIDATED on a throwaway
--   substrate before any real apply.
--     VALIDATE (reachable throwaway):
--        psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--          -v schema=s24val -v kern=s24val_kernel -v role=s24val_rw \
--          -f s15-schema.sql -f s17-stamp-mechanism.sql -f s17-independence-vocabulary.sql \
--          -f s19-trigger-search-path.sql -f s20-obligation-grants-and-view-refresh.sql \
--          -f s21-session-aware-distinctness.sql -f s22-work-item-ledger.sql \
--          -f s23-per-invocation-stamp-token.sql -f s24-declared-event-time.sql
--     REAL: NEVER applied to any existing world by this delta's own authoring act (maintainer
--     ruling 2026-07-11, "runs are strictly linear" — run M>N settles run N as dust, read-only
--     evidence; the ruling states there is no apply-to-existing-world step for anyone, and names
--     bootstrap/apply-delta.sh as retired). HONEST DISCREPANCY, NAMED (not silently routed
--     around): as of this delta's authoring, bootstrap/apply-delta.sh is STILL PRESENT and
--     EXECUTABLE on disk — the ruling retired it as POLICY (CAPABILITIES.md item 14: "DEMOTED TO
--     HISTORY... no longer part of the operator surface"), it was never deleted or neutered as a
--     mechanism, so an operator who ran it against this delta today would succeed, silently
--     violating the linearity ruling. Flagged in BACKLOG.md's dated entry beside this delta
--     (CLAUDE.md's engineering-responsibility corollary: a hazard met in passing is fixed or
--     flagged, never routed around) — deleting/neutering the script is a separate, larger
--     decision outside this delta's own scope, not taken here. This delta reaches reality by
--     entering the NEXT world's birth chain: bootstrap/new-project.sh's LINEAGE_CHAIN (this same
--     commission) applies it automatically to every `--new-world` scaffold from here on. It was
--     authored and scratch-witnessed on a scratch schema pair in the TOY db only (schema s24val /
--     s24val_kernel, role s24val_rw) — NOT applied to any live schema by this pass.
-- Run as the schema owner (bork). Idempotent (ADD COLUMN IF NOT EXISTS; CREATE OR REPLACE VIEW).

\if :{?schema}
\else
  \set schema public
\endif
\if :{?kern}
\else
  \set kern kernel
\endif

-- ============================================================================================
-- THE DECLARED-EVENT-TIME COLUMN (nullable, no DEFAULT — a writer opts in per row; omitting it
-- means "this row records a present act", today's semantics unchanged).
-- ============================================================================================
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS event_declared_ts timestamptz;

COMMENT ON COLUMN :"schema".ledger.event_declared_ts IS
  'The writer-DECLARED time the recorded event actually occurred, distinct from `ts` (INSERT time).
   NOT a stamp: writer-supplied at INSERT via bootstrap/templates/led.tmpl''s `--event-time <iso-ts>`
   flag, no trigger, no GUC, no HMAC, no verification -- trusted exactly as far as the writer is
   honest, the same posture every other prose/evidence field on this table already carries. NULL
   means "this row records a present act" (today''s semantics, unchanged) or predates s24 (the
   pre-s24 era). Consumed by design/LATE-ENTRY-AND-INTAKE-SEMANTICS.md Proposal 2''s LATE_DECLARED
   verdict (engine/contemp_audit.py + engine/lp/contemporaneity.lp): a row whose declared time
   precedes `ts` by more than the measured threshold, AND carries a declared time, satisfies the
   late-entry mandate (exit 0); the identical gap with NO declared time still verdicts
   BACKFILL_SUSPECT (exit 1) -- the refusal semantics SHARPEN, nothing existing relaxes.';

-- ============================================================================================
-- s20/s22/s23 LESSON RE-APPLIED: ledger_current + countersigned_in_force GAIN event_declared_ts,
-- APPENDED AT THE END (CREATE OR REPLACE VIEW forbids renaming/reordering the existing columns, so
-- the new column appends — exactly as s23's own stamp_invocation had to). Explicit column lists
-- throughout — never `l.*` again. Column list = s23's exact list + l.event_declared_ts.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".ledger_current
    WITH (security_invoker = true) AS
SELECT l.id, l.ts, l.session, l.kind, l.statement, l.rationale, l.status, l.evidence,
       l.confidence, l.supersedes, l.refs, l.concern, l.enacts, l.actor, l.regards,
       l.amends, l.amends_scope, l.answers,
       l.stamp_session, l.stamp_agent, l.stamp_ts, l.stamp_hmac, l.stamp_verified,
       l.work_slug, l.work_title, l.work_depends_on, l.work_resolution, l.work_witness,
       l.stamp_invocation, l.event_declared_ts
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id);

CREATE OR REPLACE VIEW :"schema".countersigned_in_force
    WITH (security_invoker = true) AS
SELECT l.id, l.ts, l.session, l.kind, l.statement, l.rationale, l.status, l.evidence,
       l.confidence, l.supersedes, l.refs, l.concern, l.enacts, l.actor, l.regards,
       l.amends, l.amends_scope, l.answers,
       l.stamp_session, l.stamp_agent, l.stamp_ts, l.stamp_hmac, l.stamp_verified,
       l.work_slug, l.work_title, l.work_depends_on, l.work_resolution, l.work_witness,
       l.stamp_invocation, l.event_declared_ts
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".ledger r JOIN :"schema".review_detail d ON d.ledger_id = r.id
               WHERE r.kind = 'review' AND r.regards = l.id AND d.verdict = 'attest'
               AND NOT EXISTS (SELECT 1 FROM :"schema".ledger s2 WHERE s2.supersedes = r.id));
