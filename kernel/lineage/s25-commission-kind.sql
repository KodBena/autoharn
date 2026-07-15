-- s25 COMMISSION KIND — the intake-capture mechanism half (kernel delta; BACKLOG "Five-item
-- batch, maintainer-approved 2026-07-11 evening", item 2). Authored per the standing delegation
-- contract's class-ratified fail-safe path (CLAUDE.md ORCHESTRATION: "a kernel lineage delta
-- that only ADDS refusals, vocabulary, or derived views ... is pre-ratified as a class"),
-- scratch-witnessed both polarities, differential AGREE (see the dated BACKLOG entry beside
-- this file for the exact witness output). An ADDITIVE delta applied ON TOP of the
-- s15/s17/s17b/s19/s20/s21/s22/s23/s24 kernel (the established remediation-delta idiom), NOT a
-- retro-edit of a frozen sNN record (ADR-0005 Rule 8) and NOT a second hand-copy of the kind
-- vocabulary's one home (ADR-0012 P1: one home per mechanism).
--
-- WHY (operator-side prose; NOT subject-visible — only the catalog objects inside the opaque db
-- are): design/RETROSPECTIVE-RUN10.md Finding 5's harness recommendation, verbatim: "Capture
-- the commission at intake as a frozen ledger row ... so that 'deliverable versus commission'
-- can be checked mechanically against the source, not only against the agent's restatement of
-- it." The retrospective's could-not-answer item 4 named the identical gap from the other side:
-- "the original brief is absent from the ledger, git, and the journals; it survives only as
-- reviewer paraphrase." This delta is the mechanism half of that fix: 'commission' joins the
-- ledger kind vocabulary, so the ask itself — the verbatim task text a session receives — can be
-- written as its own first-class, append-only row, cited by every later decomposition/work_open
-- row via the kernel's existing `--refs row:<id>` channel (no new column, no new edge type —
-- the SAME cross-reference mechanism `led --refs` already offers every other kind, s15's own
-- documented convention: "a bare reference uses refs"). The maintainer's own design (BACKLOG,
-- near-verbatim) adds two SIGNING MODES on top of this one vocabulary member — full mode (the
-- commissioner principal signs it themselves) and lazy mode (the implementer transcribes it
-- vicariously, marked as such in the statement prose) — both built entirely at the operator-verb
-- and template layer (bootstrap/new-project.sh, bootstrap/templates/CLAUDE.md.tmpl); THIS delta
-- supplies only the one shared substrate both modes write through: a 'commission' kind is a
-- legal INSERT.
--
-- NOT A NEW COLUMN, NOT A NEW TABLE — the smallest sound thing. A commission is structurally
-- indistinguishable from any other prose ledger row (same statement/rationale/evidence/actor/
-- stamp columns every kind already carries); what makes it a commission is which STRING the
-- `kind` column holds, exactly the same shape every other kind vocabulary member already is
-- (s22's work_* additions were the one prior kind-vocabulary extension and needed five NEW
-- columns because work-item state genuinely has shape prose does not; a commission has no
-- structure beyond "here is prose, attributed, timestamped, stampable, citable" — ledger_kind_
-- check's existing shape already provides every one of those for free). No new view, no new
-- trigger, no new constraint beyond the one CHECK re-issue below.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 amendment):
--
--   - INVARIANT: `ledger_kind_check` (s15's inline CHECK, s22's own re-issue point — the ONE
--     home, unnamed-then-Postgres-auto-named, re-confirmed sole by the same grep s22's own
--     header already ran) admits 'commission' as a legal `kind` value. Every existing member
--     of the vocabulary remains legal, unchanged, in the identical order — this is a set
--     UNION, never a removal or a reordering (a CHECK ... IN (...) list is order-insensitive
--     to begin with, so "reordering" is not even a representable regression here).
--
--   - QUANTIFICATION UNIVERSE — enumerated by re-reading every site that could plausibly hold a
--     second hand-copy of the closed kind vocabulary, mirroring s22's own enumeration method
--     (grep, not assumption):
--       * kernel/lineage/*.sql — grepped for `'assumption','decision'` / `work_opened','work_
--         claimed'` shaped literals: every hit is an EARLIER, FROZEN sNN schema file (s10
--         through s15, s22 itself) — point-in-time records of an already-superseded CHECK
--         definition, never touched (ADR-0005 Rule 8); s22 is the ONE live re-issue point this
--         delta re-issues one delta later, exactly as s22 itself re-issued s15's original list.
--       * engine/lp/*.lp (the ASP programs) — grepped for a quoted kind literal (`"decision"` /
--         `'decision'`): ZERO hits. Every `.lp` program treats `kind` as an OPAQUE string atom
--         it passes through, never a closed-enumeration predicate it matches against — so no
--         ASP-side vocabulary exists to drift, and this delta requires no `.lp` change.
--       * engine/*.py (the SQL-floor / EDB producers) — grepped for a quoted kind literal used
--         as a CLOSED set (as opposed to a scratch fixture's own throwaway test rows, which
--         legitimately hardcode 'decision' as sample data and are not a vocabulary copy at
--         all): ZERO hits of a closed-set kind enumeration. `engine/ledger_floor.py`'s one hit
--         (`d.kind <> 'decision'`) is an EXCLUSION predicate over the observed value, not a
--         membership CHECK against a hand-maintained list — unaffected by this delta either
--         way, named here rather than silently skipped.
--       * bootstrap/templates/led.tmpl's `_led_kind_refusal_teach()` — re-queries
--         `pg_get_constraintdef` LIVE against the schema's own constraint at refusal time
--         (run-10 closure audit's own fix, already landed) — NEVER a hand-copied list. This
--         delta requires ZERO led.tmpl change for the refusal-teaching path to pick up
--         'commission' automatically the instant this delta applies to a world.
--       * ledger_current / countersigned_in_force / review_gap / question_status /
--         work_item_current / work_item_violations / review_stamp_distinctness — none of these
--         views enumerates kind VALUES (each reads the `kind` COLUMN generically, where it
--         reads it at all); a kind vocabulary extension does not touch any view's column list
--         (contrast s24, which added a whole new COLUMN and therefore had two views to
--         re-issue — this delta adds no column, so the "column-complete" class s20/s23/s24 each
--         had to re-check is not even applicable here, named rather than silently assumed
--         inapplicable).
--     So the "kind vocabulary" class has EXACTLY ONE live member requiring a re-issue
--     (ledger_kind_check, done below); every other candidate site is checked and confirmed NOT
--     a second hand-copy (named, not assumed) — an even narrower footprint than s24's own
--     two-view re-issue, because this delta adds no column at all.
--     TRIGGERS — NONE touched. No trigger reads or branches on the closed kind vocabulary by
--       value (validate_work_item branches on specific work_* kinds it already owns; it does
--       not enumerate the FULL vocabulary and requires no change to admit a new, unrelated
--       kind it never inspects).
--     ENGINE — NONE (mirrors s23's own "ENGINE — NONE" disclosure): this delta's whole
--       reason for existing is a capture-only vocabulary widening with no new derived-fact
--       consumer shipped in this same commission; a future `commission_provenance`-shaped ASP
--       view (e.g. "every work_opened row traceable to a commission row via --refs") is a
--       plausible FOLLOW-ON, filed as a possibility here, not built or claimed built.
--
--   - DENOMINATION: the vocabulary member is the bare text literal `'commission'`, matching the
--     existing members' own denomination exactly (bare lowercase snake_case strings, no prefix,
--     no namespacing) — never a second competing spelling (`'commissioning'`, `'commission_ask'`)
--     that would fragment the vocabulary the moment two spellings coexist.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): this delta ONLY adds a
-- vocabulary member — nothing existing is relaxed (every prior kind stays legal), no existing
-- semantics changes (a 'commission' row is written, read, stamped, cited, and countersigned
-- through the exact same generic-path machinery every other prose kind already uses — no new
-- refusal, no loosened refusal, no altered trigger). It is class-ratified per the maintainer's
-- 2026-07-09 ruling once scratch-witnessed both polarities with the SQL/ASP differential in
-- AGREE (both done, this same commission — see the dated BACKLOG entry beside this file for the
-- exact witness transcript) — it enters the birth chain without a per-delta maintainer question.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/s17/s20/s22/s23/s24):
-- schema/kern are psql variables (no :role-affecting change — CREATE ... does not touch grants,
-- and a DROP+ADD CONSTRAINT preserves the table's existing GRANTs unconditionally, unlike a
-- CREATE OR REPLACE VIEW) so this delta is VALIDATED on a throwaway substrate before any real
-- apply.
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s25val -v kern=s25val_kernel -v role=s25val_rw \
--        -f s15-schema.sql -f s17-stamp-mechanism.sql -f s17-independence-vocabulary.sql \
--        -f s19-trigger-search-path.sql -f s20-obligation-grants-and-view-refresh.sql \
--        -f s21-session-aware-distinctness.sql -f s22-work-item-ledger.sql \
--        -f s23-per-invocation-stamp-token.sql -f s24-declared-event-time.sql \
--        -f s25-commission-kind.sql
--   REAL: NEVER applied to any existing world by this delta's own authoring act (maintainer
--   ruling 2026-07-11, "runs are strictly linear" — run M>N settles run N as dust, read-only
--   evidence; there is no apply-to-existing-world step for anyone). This delta reaches reality
--   by entering the NEXT world's birth chain: bootstrap/new-project.sh's LINEAGE_CHAIN (this
--   same commission) applies it automatically to every `--new-world` scaffold from here on. It
--   was authored and scratch-witnessed on a scratch schema pair in the TOY db only (schema
--   s25val / s25val_kernel, role s25val_rw) — NOT applied to any live schema by this pass.
-- Run as the schema owner (bork). Idempotent (DROP+ADD CONSTRAINT).

\if :{?schema}
\else
  \set schema public
\endif
\if :{?kern}
\else
  \set kern kernel
\endif

-- ============================================================================================
-- THE VOCABULARY WIDENING (s22's own re-issue point, one member later — additive union, no
-- removal, no reordering of the pre-existing members).
-- ============================================================================================
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS ledger_kind_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT ledger_kind_check CHECK (kind IN
    ('assumption','decision','question','verification',
     'finding','snag','revision','note','review',
     'work_opened','work_claimed','work_depends_on','work_closed',
     'commission'));

COMMENT ON CONSTRAINT ledger_kind_check ON :"schema".ledger IS
  'The closed kind vocabulary (s15, extended s22, extended again s25). ''commission'' (s25) is
   a first-class ledger row for the verbatim ask a session received, written by ONE of two
   signing modes (design/... intake commission design, this same commission): a FULL-mode
   commission is signed by a registered ''commissioner'' principal
   (LED_ACTOR=commissioner ./led commission "<ask>"), distinguishable mechanically from a LAZY-
   mode vicarious transcription (the implementer''s own principal writes it, statement prefixed
   "(vicarious transcription by the implementer; carries no commissioner guarantee)") by TWO
   independent signals together, never prose claims alone: the row''s actor (which principal
   signed it) and its stamp state (whether a live Claude session invocation stamped it, or it
   was typed from a bare shell with no session -- an unstamped-but-attributed row). Structurally
   identical to every other prose kind (no new column, no new table) -- what makes a row a
   commission is which string this CHECK admits into `kind`, nothing else. Decomposition rows
   cite a commission via the existing `--refs row:<id>` channel (s15''s documented convention),
   never a new edge type.';
