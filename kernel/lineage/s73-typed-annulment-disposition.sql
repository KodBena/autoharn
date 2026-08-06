-- s73 TYPED ANNULMENT DISPOSITION (design/FABLE-TYPED-ANNULMENT-DISPOSITION-SPEC.md, Fable-
-- authored, MAINTAINER-RATIFIED 2026-08-06, ledger row 1087, dispatched via
-- design/BRIEF-TYPED-ANNULMENT-DELTA-2026-08-06.md, item review-obligation-annulment-vocabulary
-- part (c), provenance rows 1025/1008). Sonnet-authored per the standing delegation contract
-- (CLAUDE.md ORCHESTRATION). This delta is AUTHORED and SCRATCH-WITNESSED only; APPLYING it to
-- any live/existing world is the maintainer's act at a FUTURE world's birth (runs-are-
-- strictly-linear ruling, 2026-07-11), never taken here. An ADDITIVE delta applied ON TOP of the
-- s15..s72 kernel (the established remediation-delta idiom), NOT a retro-edit of a frozen sNN
-- record (ADR-0005 Rule 8) and NOT a second hand-copy of any existing mechanism (ADR-0012 P1:
-- this delta reuses work_review_disposition/work_review_ref, the row:<id> citation vocabulary
-- s48/s69 already validate, and s21's session-aware distinctness predicate wholesale, rather
-- than minting parallel columns or a second distinctness test).
--
-- PREREQUISITE: this delta REQUIRES s72 (kernel/lineage/s72-stamp-binding-conjunct.sql) applied
-- first -- it is built at the current lineage head; the two functions it re-issues
-- (validate_work_item_close, validate_review_witness_existence) were both last shaped by s69 and
-- untouched since (grepped: no s70/s71/s72 file re-issues either), so their TRUE immediately-
-- prior re-issue is s69 in both cases (named per-ELEMENT below, with the prior-body-sha256 the
-- lineage_reissue_lineage gate requires at N>=63). Applying this file on a pre-s69 kernel fails
-- loudly at CREATE OR REPLACE FUNCTION time or at the gate's own hash-mismatch check, the correct,
-- disclosed failure mode for a hard dependency, matching every prior delta's own PREREQUISITE
-- precedent.
--
-- WHY (the spec's own §0, distilled): the only two constructors on a work_closed row's review
-- disposition are witnessed (a lie without evidence, when no review was ever warranted) and
-- deferred (which re-mints the very debt an annulment is meant to discharge). A legitimate
-- consider-and-decline -- an authority distinct from the obligor examines a deferred review debt
-- and rules it unwarranted, for a recorded reason -- has had no type; the only expressible
-- discharge rode verdict=attest with a prose disclaimer, an ADR-0008 fuzzy-fit the maintainer's
-- own forwarded remark named as an ADR-0000 smell. This delta closes exactly that gap (spec's
-- §1, item (c)) -- items (a)/(b) (the supersede-and-reclose surface verb, its teach-text) are the
-- separate B2 build the spec's §4 schedules next, explicitly out of THIS delta's scope (the
-- brief's own "out of scope" line).
--
-- THE VOCABULARY (spec §2, first paragraph): `work_review_disposition` gains a third legal
-- value, `annulled` -- this close's review obligation was considered and declined by an
-- authority distinct from the obligor, for a recorded reason. SCOPED TO kind='work_closed'
-- ALONE (a builder judgment, named): the spec's own substrate, provenance, and every worked
-- example is about work-item close review debt; `work_violation_disposition` rows (s37) answer a
-- DIFFERENT question (which violations-view member does this act answer), and nothing in the
-- spec's text or closure statement claims annulment for that kind. Widening the vocabulary onto
-- an unnamed second kind would be the ADR-0008 negative-register failure (fabricating a category
-- fit the spec never asked for); scoping it to work_closed alone mirrors s38's own
-- work_review_bookkeeping_kind_shape precedent exactly (a new disposition value, legal on
-- work_closed only, via the SAME PARTIAL-VALUE CHECK idiom, tracked in
-- gates/kind_shape_manifest_gate.py's VALUE_PARTITION_MANIFEST).
--
-- ELEMENT 1 -- THE VALUE + THE TWO CHECKS. work_review_disposition_check (last widened s38, to
-- admit 'bookkeeping') widens again to admit 'annulled' -- a flat, un-kind-tested vocabulary
-- CHECK, unchanged in shape, one legal value wider (HISTORY: safe -- no pre-existing row can
-- carry the new value, the value is born in this delta). work_review_annulled_kind_shape (NEW,
-- the work_review_bookkeeping_kind_shape idiom one value over) scopes 'annulled' to
-- kind='work_closed' alone. work_review_annulled_requires_ref (NEW, the
-- work_review_witnessed_requires_ref idiom one value over, s29) makes work_review_ref MANDATORY
-- (non-empty) whenever disposition='annulled' -- refusal 1 of the spec's three construction-time
-- refusals ("work_review_ref is MANDATORY").
--
-- ELEMENT 2 -- THE AUTHORITY CITATION + NO-SELF-ANNULMENT (spec §2, refusals 1/2). Both live
-- inside `validate_review_witness_existence` (s48/s69's own standing single home of "does
-- work_review_ref's row:<id> vocabulary check out", ADR-0012 P1 -- a fourth sibling concern
-- folded into the SAME loop that already resolves each cited row's existence, never a second,
-- competing trigger scanning the same column). Re-issued (true immediately-prior re-issue: s69
-- Element 2; every pre-existing branch below -- the s48 existence check and the s69 evidentiary-
-- shape check -- is BYTE-IDENTICAL, with ONE additive widening named at its own site: the s69
-- evidentiary-shape refusal (kind IN (review,finding), or an in-force child work_opened row) now
-- also passes when this row's own disposition is 'annulled' -- vacuously safe, since no
-- pre-existing row could ever have carried that value. An annulment's authority is a DIFFERENT
-- question ("is this actor's ruling distinct from the obligor's", not "is this a review"), so it
-- is checked SEPARATELY, by the new block appended below, rather than folded into or replacing
-- s69's own review-shape test).
--
-- THE DISTINCTNESS PREDICATE, NAMED AND DEFENDED (the spec's own open design point, "the
-- precise predicate is the builder's to design against the s40/s41 identity substrate and to
-- defend in the delta header"): TWO INDEPENDENT TESTS, BOTH REQUIRED, mirroring the SAME
-- composition review countersigns already carry across TWO separate functions one column over
-- (validate_review's plain actor-identity segregation-of-duties check, s15/s69; and
-- validate_independence's (stamp_session, stamp_agent)-PAIR distinctness for an
-- independence-CLAIMING review, s17/s21/s29/s41) --
--   (1) ACTOR DISTINCTNESS: the authority row's `actor` (a kernel.principal id, s40/s41's own
--       identity substrate) must differ from the obligor's `actor` -- the plain segregation-of-
--       duties test validate_review already performs for an ordinary countersign, reused here at
--       the same granularity (a principal cannot rule on its own debt).
--   (2) STAMP-PAIR DISTINCTNESS (s21): the authority row's (stamp_session, stamp_agent) pair must
--       differ from the obligor's own pair, with a NULL half on EITHER side read as NOT distinct
--       (fail-safe, never fail-open -- s21's own denomination, reused verbatim, never re-derived).
--       This is the SAME predicate s21/s29/s41 already use for an independence-CLAIMING review
--       countersign (validate_independence's `distinct_pair` computation), reused here rather
--       than re-typed, because the spec's own text asks for EXACTLY that composition ("same
--       session + same agent cannot manufacture the distinction... exactly as review countersigns
--       do").
-- WHY BOTH, not either: (1) alone would admit a genuinely-distinct principal id resolved from the
-- SAME session/agent via strict attribution's declared-default path (s40 Element 6) -- two
-- "different" actors that are, in fact, one invocation typing two names, exactly the loophole
-- (2) forecloses. (2) alone would admit the SAME principal acting through two literally different
-- stamped invocations (two terminal tabs, one operator) -- a real distinctness of INVOCATION but
-- not of AUTHORITY, exactly the loophole (1) forecloses. Requiring BOTH is the fail-safe
-- direction for a guarantee feature (s29 Element C's own precedent for the same posture: a
-- strict-close guarantee always chooses the MORE inclusive resolved-tree reading, never the less).
--
-- THE OBLIGOR (spec §2 refusal 2, verbatim: "the actor of the superseded deferred close (or of
-- the close row itself where no predecessor exists)"): resolved ONCE per INSERT, before the
-- row:<id> loop (it does not depend on which token is being checked) -- `NEW.supersedes`, when
-- present, names the deferred close this annulment discharges (a raw, row-addressed lookup by id,
-- the SAME "row-addressed forensics, not a truth projection" posture validate_review/
-- validate_supersession_target already hold, s21/s43's own house idiom); when absent, the obligor
-- IS this very close act (NEW.actor/NEW.stamp_session/NEW.stamp_agent directly -- NEW.id does not
-- exist yet, a BEFORE INSERT trigger's row has no id, so the obligor's identity is read off NEW
-- itself, never a self-SELECT that could never match).
--
-- THE AUTHORITY MUST BE IN-FORCE (spec §2 refusal 1, "must cite an in-force ledger row"): a
-- THIRD, NEW check, distinct from s48's existence test (raw ledger, "was this row ever written")
-- -- annulment specifically additionally requires the cited row to be CURRENT (`ledger_current`,
-- s31's own single home of "in force") at construction time. A superseded/retracted authority row
-- existed once but is no longer standing, and the spec's own text is explicit ("an in-force
-- ledger row"), so existence alone (s48's bar for witnessed) is not sufficient here.
--
-- NO KIND RESTRICTION ON THE AUTHORITY ROW (ADR-0008 negative register, applied deliberately):
-- the spec names the authority row functionally ("whose statement carries the annulment
-- rationale"), never by kind -- s69's own review/finding vocabulary answers "is this a review",
-- a different, narrower question than "is this a distinct actor's ruling"; the most natural
-- instance in this project's own practice is a `decision` row (a maintainer ruling, exactly this
-- delta's own row 1087). Inventing a closed kind vocabulary the spec never states would be the
-- fabricated-category failure ADR-0008's negative register forbids; the existence-in-force test
-- plus the two distinctness tests are the whole check.
--
-- REFUSAL 3 (spec §2, "annulled is legal ONLY where deferred would have been legal... never a
-- substitute for a ship witness or any other close requirement"): Element 3, below, re-issues
-- validate_work_item_close so its strict-mode branch refuses `annulled` on the SAME footing as
-- `deferred`/`bookkeeping` -- an annulled close carries no reviewer verdict to check the
-- obligation tree against, exactly the s38 bookkeeping precedent one value over. No OTHER
-- close-time refusal (ship witness, closer-is-claimant-of-record, epoch-gated disposition
-- presence) inspects the disposition VALUE at all -- they bind uniformly regardless, so nothing
-- else needs a line changed for `annulled` to inherit every one of them unrelaxed.
--
-- ELEMENT 4 -- DERIVED TRUTH (spec's "Derived truth" paragraph).
--   (a) work_review_gap (last re-issued s37) TREATS AN IN-FORCE ANNULLED CLOSE AS DISCHARGED
--       WITH ZERO CODE CHANGE -- VERIFIED, not asserted: both its arms filter
--       `work_review_disposition = 'deferred'` (an exact-equality test, never an enumeration or a
--       NOT-witnessed negative test), and `annulled` is disjoint from `deferred` by construction
--       (the CHECK forbids a row from carrying two disposition values at once) -- so an
--       annulled close can never enter this view's candidate set in the first place. This is the
--       stronger reading of "discharged": not merely answered, never even debited. Re-verified
--       NOT a member needing re-issue.
--   (b) THE NEW SINGLE-HOME AUDIT VIEW, work_review_annulled (Element 5 below) -- every in-force
--       annulled close with its authority row's content and current standing, so annulments are
--       enumerable, never silent (the spec's own "the two-biases guard's structural answer").
--   (c) THE DEFENSE-IN-DEPTH JUDGMENT CALL (spec's own open question, "the builder's judgment,
--       stated either way in LIMITS"): TAKEN, in the affirmative. work_item_violations and
--       work_violation_history (both last re-issued s39) gain ONE new member,
--       annulled_authority_retracted -- an in-force annulled close whose cited authority row has
--       since lapsed from ledger_current (superseded after the annulment was written). This
--       mirrors orphaned_by_retraction's own precedent (s31) exactly: a fact that construction-
--       time refusal cannot foreclose (the authority WAS in force at INSERT time; a LATER,
--       independent act retracted it), so the honest disposition is SURFACE it, never silently
--       tolerate it -- CLAUDE.md's own engineering-responsibility corollary, applied to a hazard
--       genuinely in this delta's own reach (an annulment whose only cited justification has
--       since been struck from the record is exactly the kind of silent debt-discharge the spec's
--       whole provenance exists to foreclose). Reused, not re-derived (ADR-0012 P1): both views
--       read `work_review_annulled`'s own `authority_in_force` computation rather than
--       re-deriving the row:<id> extraction a second time.
--
-- ============================================================================================
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
-- ELEMENT 1 -- THE VALUE + THE TWO CHECKS.
-- ============================================================================================
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_review_disposition_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_review_disposition_check CHECK (
    work_review_disposition IS NULL
    OR work_review_disposition IN ('witnessed', 'deferred', 'bookkeeping', 'annulled'));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_review_annulled_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_review_annulled_kind_shape CHECK (
    work_review_disposition IS DISTINCT FROM 'annulled' OR kind = 'work_closed');

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_review_annulled_requires_ref;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_review_annulled_requires_ref CHECK (
    work_review_disposition IS DISTINCT FROM 'annulled'
    OR (work_review_ref IS NOT NULL AND btrim(work_review_ref) <> ''));

COMMENT ON CONSTRAINT work_review_disposition_check ON :"schema".ledger IS
  'kernel/lineage/s73-typed-annulment-disposition.sql: widens s38''s three-value vocabulary
   (witnessed|deferred|bookkeeping) to a fourth, annulled -- this close''s review obligation was
   considered and declined by a distinct-actor authority, for a recorded reason. Construction-time
   requirements (mandatory in-force authority citation, no self-annulment) live in
   validate_review_witness_existence, below; scope to work_closed alone lives in
   work_review_annulled_kind_shape, one constraint over.';
COMMENT ON CONSTRAINT work_review_annulled_kind_shape ON :"schema".ledger IS
  'kernel/lineage/s73-typed-annulment-disposition.sql: annulled is licensed on kind=work_closed
   ALONE (never work_violation_disposition -- the spec''s own substrate and every worked example
   is exclusively about work-item close review debt; mirrors work_review_bookkeeping_kind_shape
   (s38) one value over, the same PARTIAL-VALUE idiom).';
COMMENT ON CONSTRAINT work_review_annulled_requires_ref ON :"schema".ledger IS
  'kernel/lineage/s73-typed-annulment-disposition.sql: work_review_ref is MANDATORY, non-empty,
   whenever disposition=annulled (spec §2 refusal 1) -- mirrors work_review_witnessed_requires_ref
   (s29) one value over. The MANDATORY citation must additionally resolve to an IN-FORCE ledger
   row and pass the no-self-annulment distinctness test -- both enforced in
   validate_review_witness_existence (a value-shape requirement this table CHECK cannot express:
   it needs a cross-row lookup and a currency read against ledger_current, neither expressible in
   a CHECK, s29''s own sec-10 amendment names the identical Postgres limit for the same reason).';

-- ============================================================================================
-- ELEMENT 2 -- validate_review_witness_existence RE-ISSUED (the authority citation + no-self-
-- annulment). True immediately-prior re-issue: s69 (kernel/lineage/s69-role-coherence-refusals.sql)
-- Element 2 (its only prior definition since s48 -- confirmed, grepped, before authoring this
-- delta: no s49..s72 file re-issues this function). The s48 existence check and the row/actor/
-- session/agent SELECT immediately below it are carried forward; that SELECT's column list widens
-- (kind was the only prior output; actor/stamp_session/stamp_agent are appended) to feed the new
-- annulment block below WITHOUT a second, competing lookup of the same row (ADR-0012 P1) --
-- behavior-preserving for every pre-existing reader of v_cited_kind, which is untouched. The s69
-- evidentiary-shape refusal gains ONE additive disjunct (named in this file's own header above);
-- every other pre-existing line is BYTE-IDENTICAL. The new annulment block is appended after it,
-- inside the SAME loop iteration; the post-loop "no citation at all" refusal is appended after
-- the loop closes.
-- prior-body-sha256: 9ae6827a29cea3436489f455257d8d83ac9a039c09c7d5bff18a0099b97008df (s69-role-coherence-refusals.sql)
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_review_witness_existence() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_match text;
  v_id bigint;
  v_head bigint;
  v_cited_kind text;
  v_cited_actor bigint;
  v_cited_session text;
  v_cited_agent text;
  v_obligor_actor bigint;
  v_obligor_session text;
  v_obligor_agent text;
  v_annul_found boolean := false;
BEGIN
  -- s73: the obligor's identity, resolved ONCE (it does not depend on which row:<id> token is
  -- being checked) -- the superseded deferred close's own actor/stamp pair when NEW.supersedes
  -- names one, else this very close act's own NEW.* fields (NEW.id does not exist pre-INSERT).
  IF NEW.work_review_disposition = 'annulled' THEN
    IF NEW.supersedes IS NOT NULL THEN
      SELECT l.actor, l.stamp_session, l.stamp_agent
        INTO v_obligor_actor, v_obligor_session, v_obligor_agent
        FROM ledger l WHERE l.id = NEW.supersedes;
    ELSE
      v_obligor_actor := NEW.actor;
      v_obligor_session := NEW.stamp_session;
      v_obligor_agent := NEW.stamp_agent;
    END IF;
  END IF;

  IF NEW.kind IN ('work_closed', 'work_violation_disposition')
     AND NEW.work_review_ref IS NOT NULL THEN
    FOR v_match IN
      SELECT (regexp_matches(NEW.work_review_ref, 'row:([0-9]+)', 'g'))[1]
    LOOP
      v_id := v_match::bigint;
      IF NOT EXISTS (SELECT 1 FROM ledger WHERE id = v_id) THEN
        SELECT max(id) INTO v_head FROM ledger;
        RAISE EXCEPTION 'Ledger policy: review-witness citation ''row:%'' in work_review_ref is refused — no ledger row % exists (checked at INSERT time; review-witness position only, close-family kinds work_closed/work_violation_disposition -- s48). A witness citation naming a nonexistent row is a claim with a dangling evidence pointer, in the one place evidence pointers are load-bearing.%  Cite an EXISTING row instead (e.g. --review-witness row:<id> naming an already-recorded review event), or use --review-deferred/--review-bookkeeping if no review exists yet.',
          v_id, v_id,
          CASE WHEN v_head IS NOT NULL AND v_id > v_head
               THEN ' This id is AT OR BEYOND the ledger''s current head — if you meant to cite THIS row''s own id, that is impossible by construction: ledger `id` is server-assigned (s15) and is never visible to the row being inserted.'
               ELSE '' END;
      END IF;

      SELECT l.kind, l.actor, l.stamp_session, l.stamp_agent
        INTO v_cited_kind, v_cited_actor, v_cited_session, v_cited_agent
        FROM ledger l WHERE l.id = v_id;
      IF v_cited_kind NOT IN ('review', 'finding')
         AND NOT EXISTS (
           SELECT 1 FROM ledger_current lc
           WHERE lc.id = v_id AND lc.kind = 'work_opened' AND lc.work_parent = NEW.work_slug
         )
         AND NEW.work_review_disposition IS DISTINCT FROM 'annulled'
      THEN
        RAISE EXCEPTION 'Ledger policy: review-witness citation ''row:%'' in work_review_ref is refused — row % exists but is not evidence: its kind is ''%'', not ''review'' or ''finding'', and it is not an in-force work_opened row of a CHILD of this closing item (s69 §2, design/FABLE-S69-ROLE-COHERENCE-REFUSALS-SPEC.md). Legal witnesses here are: a review or finding row (the judgment itself), or — for a planning/parent item discharged by decomposition — the work_opened row of a child slug naming THIS item as its --parent (the planning-close carve-in). A work_claimed row (or any other kind) is not a review, whatever it cites (the autoharn2 row-1265 specimen this refusal closes).', v_id, v_id, v_cited_kind;
      END IF;

      -- s73 (design/FABLE-TYPED-ANNULMENT-DISPOSITION-SPEC.md §2): the annulment authority
      -- citation -- runs for every row:<id> token when THIS close's own disposition is
      -- 'annulled', independent of the review/finding evidentiary-shape test above (an
      -- annulment's authority is not "a review"; see this file's own header for why no kind
      -- restriction is imposed).
      IF NEW.work_review_disposition = 'annulled' THEN
        v_annul_found := true;
        IF NOT EXISTS (SELECT 1 FROM ledger_current lc WHERE lc.id = v_id) THEN
          RAISE EXCEPTION 'Ledger policy: annulment authority citation ''row:%'' in work_review_ref is refused — row % exists but is NOT IN FORCE (superseded/retracted) — an annulment must cite an authority row that is CURRENTLY STANDING, never a lapsed one (s73, design/FABLE-TYPED-ANNULMENT-DISPOSITION-SPEC.md §2). Cite a currently in-force row, or record a fresh annulment once a standing authority is on record.', v_id, v_id;
        END IF;
        IF v_obligor_actor IS NOT DISTINCT FROM v_cited_actor
           OR NOT (
             v_obligor_session IS NOT NULL AND v_obligor_agent IS NOT NULL
             AND v_cited_session IS NOT NULL AND v_cited_agent IS NOT NULL
             AND (v_obligor_session IS DISTINCT FROM v_cited_session
                  OR v_obligor_agent IS DISTINCT FROM v_cited_agent)
           )
        THEN
          RAISE EXCEPTION 'Ledger policy: annulment refused — the authority row (row:%, actor %) is not distinct from the annulled obligation''s obligor (actor %: the superseded deferred close''s own actor, or this close''s own actor where no predecessor exists) — no self-annulment (s73 §2). Distinctness requires BOTH a distinct actor AND a distinct (session, agent) invocation pair (a NULL half on either side reads as NOT distinct, fail-safe) — composing with s21 session-aware distinctness exactly as an independence-claiming review countersign already does: the same invocation cannot manufacture the distinction by resolving to a different principal id. Cite a genuinely distinct actor''s ruling, written through a genuinely distinct invocation.', v_id, v_cited_actor, v_obligor_actor;
        END IF;
      END IF;
    END LOOP;
  END IF;

  IF NEW.work_review_disposition = 'annulled' AND NOT v_annul_found THEN
    RAISE EXCEPTION 'Ledger policy: annulled close of work item ''%'' refused — work_review_ref carries no row:<id> citation — annulment requires a citation to an IN-FORCE LEDGER ROW as its authority (s73, design/FABLE-TYPED-ANNULMENT-DISPOSITION-SPEC.md §2); a commit hash or free-text/artifact-path reference does not satisfy this. Cite the authority ruling in work_review_ref using the row:<id> form (e.g. row:1087).', NEW.work_slug;
  END IF;

  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_review_witness_existence ON :"schema".ledger;
CREATE TRIGGER validate_review_witness_existence BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_review_witness_existence();

COMMENT ON FUNCTION :"schema".validate_review_witness_existence() IS
  'kernel/lineage/s73-typed-annulment-disposition.sql (s48/s69-widened): a work_closed/
   work_violation_disposition row''s work_review_ref row:<id> tokens must EXIST (s48) and be
   SHAPED as evidence -- review/finding, an in-force child work_opened row, OR (s73) this close''s
   own disposition is annulled. An annulled close additionally requires at least one row:<id>
   citation to an IN-FORCE row whose actor AND (stamp_session, stamp_agent) pair are BOTH distinct
   from the annulled obligation''s obligor (no self-annulment, s73 §2).';
-- ============================================================================================

-- ============================================================================================
-- ELEMENT 3 -- validate_work_item_close RE-ISSUED (refusal 3: annulled cannot satisfy strict
-- mode, the SAME footing as deferred/bookkeeping). True immediately-prior re-issue: s69
-- (kernel/lineage/s69-role-coherence-refusals.sql) Element 1 (its only prior definition since
-- s38 -- confirmed, grepped, before authoring this delta: no s39..s72 file re-issues this
-- function). Every pre-existing branch is BYTE-IDENTICAL below; ONE new ELSIF appended to the
-- strict-mode chain.
-- prior-body-sha256: 8d6e3e3b6059e4ce482c615dd4ccb005ae73ff881c543a471c60c8cc21c04516 (s69-role-coherence-refusals.sql)
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_work_item_close(r :"schema".ledger, is_composite boolean, tg_schema text)
    RETURNS :"schema".ledger LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  blockers text;
  v_claimant bigint;
BEGIN
  SELECT wic.claimant INTO v_claimant FROM work_item_current wic WHERE wic.slug = r.work_slug;
  IF r.actor IS DISTINCT FROM v_claimant THEN
    RAISE EXCEPTION 'Ledger policy: close of work item ''%'' refused — closing actor % is not the item''s claimant-of-record (%), defined as the actor of the LATEST in-force work_claimed row for this slug (s69 §1, design/FABLE-S69-ROLE-COHERENCE-REFUSALS-SPEC.md; the SAME resolution work_item_current.claimant already computes). A cross-identity close is a HANDOFF, and handoffs are claims: claim the item as yourself first (./autoharn led work claim %), then close. If the current claimant is inept or unavailable, a higher authority DEFEATS the claim with a fresh one (claim-stealing is legal by design, s47) and closes as the new claimant — nothing here forecloses reclaim.', r.work_slug, r.actor, COALESCE(v_claimant::text, '<none — this item was never claimed>'), r.work_slug;
  END IF;

  IF r.id > COALESCE((SELECT epoch FROM migration_epoch LIMIT 1), 0)
     AND r.work_review_disposition IS NULL THEN
    RAISE EXCEPTION 'Ledger policy: work_closed row for item ''%'' (ledger id %) carries no review disposition — every close act past this world''s migration epoch (id %, see %.migration_epoch) must be witnessed or deferred, never silent (s29 Element B, sec-10 epoch amendment). Retry with --review-witness <ref> or --review-deferred.', r.work_slug, r.id, (SELECT epoch FROM migration_epoch LIMIT 1), tg_schema;
  END IF;
  IF (COALESCE(r.work_strict_close, false) OR COALESCE(is_composite, false)) THEN
    IF r.work_review_disposition = 'deferred' THEN
      RAISE EXCEPTION 'Ledger policy: strict close of work item ''%'' requires --review-witness (a review already on record) — --review-deferred cannot satisfy strict mode''s immediate obligation-tree requirement, because a just-deferred obligation is, by definition, unresolved the moment it is created (s29 Element C). Record the review first (./led review ...), then close with --review-witness <ref>.', r.work_slug;
    ELSIF r.work_review_disposition = 'bookkeeping' THEN
      RAISE EXCEPTION 'Ledger policy: strict close of work item ''%'' requires --review-witness (a review already on record) — --review-bookkeeping is a judgment-free close and cannot satisfy strict mode''s obligation-tree requirement (a bookkeeping close carries no reviewer verdict to check the tree against; s38 Element 2, same footing as --review-deferred --strict). Record the review first (./led review ...), then close with --review-witness <ref>.', r.work_slug;
    ELSIF r.work_review_disposition = 'annulled' THEN
      RAISE EXCEPTION 'Ledger policy: strict close of work item ''%'' requires --review-witness (a review already on record) — an annulled disposition is a typed consider-and-decline of REVIEW DEBT, never a substitute for strict mode''s obligation-tree requirement (a distinct-actor authority declined the review; it did not perform one, so there is no verdict to check the tree against; s73, design/FABLE-TYPED-ANNULMENT-DISPOSITION-SPEC.md §2, same footing as --review-deferred/--review-bookkeeping --strict). Record the review first (./led review ...), then close with --review-witness <ref>.', r.work_slug;
    ELSIF r.work_review_disposition = 'witnessed' THEN
      SELECT string_agg(format('%s (%s)', b.blocking_slug, b.reason), '; ' ORDER BY b.blocking_slug)
        INTO blockers
        FROM work_item_strict_blockers(r.work_slug) b;
      IF blockers IS NOT NULL THEN
        RAISE EXCEPTION 'Ledger policy: strict close of work item ''%'' refused — its obligation tree is unresolved: %. Resolve every named leaf, then retry (s29 Element C: strict close is a pure query over the derived conjunction, no stored verdict).', r.work_slug, blockers;
      END IF;
    END IF;
  END IF;
  RETURN r;
END; $fn$;
-- No DROP/CREATE TRIGGER needed: the dispatcher (validate_work_item()) already calls
-- validate_work_item_close(...) by name (s35's own dispatcher body, untouched here) -- CREATE OR
-- REPLACE FUNCTION above is sufficient for the new body to take effect on the next call.

COMMENT ON FUNCTION :"schema".validate_work_item_close(:"schema".ledger, boolean, text) IS
  'kernel/lineage/s73-typed-annulment-disposition.sql: the s35 leaf, s38-widened (bookkeeping),
   s69-widened (closer-is-claimant-of-record), s73-widened (annulled): (1) the closing actor must
   equal work_item_current.claimant; (2) a close past the migration epoch needs a review
   disposition; (3) a strict/composite close of disposition deferred/bookkeeping/annulled is
   refused (none carries a reviewer verdict to check the tree against), and a witnessed strict
   close re-checks the obligation tree.';

-- ============================================================================================
-- ELEMENT 5 -- work_review_annulled, THE NEW SINGLE-HOME AUDIT VIEW (spec's "Derived truth"
-- paragraph: "a new single-home view lists every annulled close with its authority row for the
-- audit read"). A view over `ledger`/`ledger_current` mixed by declared design (the s37
-- work_violation_history / s38 work_bookkeeping_closes precedent): the CLOSE side reads
-- ledger_current (only an IN-FORCE annulled close is a live audit-worthy fact -- a retracted
-- close is no longer standing debt-discharge at all, Element 1's own view-level analogue of
-- work_review_gap's exclusion); the AUTHORITY side reads raw `ledger` (a LEFT JOIN, so the
-- authority row's content is shown even when it has since lapsed -- authority_in_force names
-- that fact explicitly, feeding the defense-in-depth member below rather than silently going
-- blank). Only the FIRST row:<id> token in work_review_ref is surfaced here (regexp_match, not
-- _matches) -- the construction-time check above validates EVERY cited token, but the audit
-- read's own single-row-per-close shape needs one denominated authority; named as a LIMIT below,
-- not silently narrowed.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".work_review_annulled
    WITH (security_invoker = true) AS
SELECT c.id AS close_id, c.work_slug AS slug, c.actor AS closer, c.ts AS closed_at,
       c.rationale AS close_rationale,
       (regexp_match(c.work_review_ref, 'row:([0-9]+)'))[1]::bigint AS authority_row_id,
       auth.actor AS authority_actor, auth.statement AS authority_statement,
       auth.rationale AS authority_rationale, auth.kind AS authority_kind,
       EXISTS (
         SELECT 1 FROM :"schema".ledger_current lc
         WHERE lc.id = (regexp_match(c.work_review_ref, 'row:([0-9]+)'))[1]::bigint
       ) AS authority_in_force
FROM   :"schema".ledger_current c
LEFT JOIN :"schema".ledger auth
       ON auth.id = (regexp_match(c.work_review_ref, 'row:([0-9]+)'))[1]::bigint
WHERE  c.kind = 'work_closed' AND c.work_review_disposition = 'annulled';

COMMENT ON VIEW :"schema".work_review_annulled IS
  'kernel/lineage/s73-typed-annulment-disposition.sql: the single home of "every IN-FORCE
   annulled close, with its authority row" -- the audit read the spec''s own Derived-truth
   paragraph commissions. authority_in_force names whether the cited authority row is still
   standing (superseded not un-cited: an authority row that has since been retracted still shows
   here, marked false) -- feeds work_item_violations.annulled_authority_retracted (reused, not
   re-derived, ADR-0012 P1) rather than the defense-in-depth CTEs re-parsing work_review_ref a
   second time.';

GRANT SELECT ON :"schema".work_review_annulled TO :"role";

-- ============================================================================================
-- ELEMENT 6 -- work_item_violations RE-ISSUED: gains annulled_authority_retracted (the defense-
-- in-depth member, this file's own header, taken in the affirmative). True immediately-prior
-- re-issue: s39 (kernel/lineage/s39-blocks-start.sql) (no s40..s72 file re-issues this VIEW --
-- gates/lineage_reissue_lineage.py's own function-only scope does not police views, but the
-- same true-prior discipline is followed by hand here for the same reason). Every pre-existing
-- CTE and arm's EXECUTABLE SQL is byte-identical below (comment-stripped diff against s39); only
-- the one new CTE (annulled_retracted) and the one new UNION ALL arm are appended. The v3 final
-- gate (`JOIN ledger_current tgt ON tgt.id = rv.target_id`) and the disposition-answering
-- machinery (disposition_basis_holds) cover the new arm automatically, with no edit of their own
-- (s39's own comment on this same property, re-verified here: annulled_retracted's target_id is
-- the close row's own id, ALREADY current by construction -- work_review_annulled itself reads
-- ledger_current for the close side).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".work_item_violations
    WITH (security_invoker = true) AS
WITH RECURSIVE
  opens_cur AS (
    SELECT work_slug AS slug, count(*) AS n
    FROM :"schema".ledger_current WHERE kind = 'work_opened'
    GROUP BY work_slug
  ),
  dup_open AS (
    SELECT slug FROM opens_cur WHERE n > 1
  ),
  shipped_no_witness AS (
    SELECT work_slug AS slug, id
    FROM :"schema".ledger_current
    WHERE kind = 'work_closed' AND work_resolution = 'shipped'
      AND (work_witness IS NULL OR btrim(work_witness) = '')
  ),
  deps AS (
    SELECT work_slug AS dependent, work_depends_on AS antecedent, id
    FROM :"schema".ledger_current WHERE kind = 'work_depends_on'
  ),
  dangling_dep AS (
    SELECT d.dependent AS slug, d.antecedent, d.id
    FROM deps d
    WHERE NOT EXISTS (SELECT 1 FROM :"schema".ledger o
                       WHERE o.kind = 'work_opened' AND o.work_slug = d.antecedent)
  ),
  bc_deps AS (
    SELECT e.dependent_slug AS dependent, e.antecedent_slug AS antecedent
    FROM :"schema".work_edge_blocks_close e
    JOIN :"schema".ledger_current lc ON lc.id = e.edge_row_id
  ),
  bc_reach_dep(start_slug, cur) AS (
    SELECT dependent, antecedent FROM bc_deps
    UNION
    SELECT r.start_slug, d.antecedent FROM bc_reach_dep r JOIN bc_deps d ON d.dependent = r.cur
  ),
  dep_cycle AS (
    SELECT DISTINCT start_slug AS slug FROM bc_reach_dep WHERE cur = start_slug
  ),
  parents AS (
    SELECT e.child_slug AS slug, e.parent_slug, e.edge_row_id
    FROM :"schema".work_edge_parent e
    JOIN :"schema".ledger_current lc ON lc.id = e.edge_row_id
  ),
  dangling_parent AS (
    SELECT p.slug, p.parent_slug, p.edge_row_id
    FROM parents p
    WHERE NOT EXISTS (SELECT 1 FROM :"schema".ledger o
                       WHERE o.kind = 'work_opened' AND o.work_slug = p.parent_slug)
  ),
  parent_anc(start_slug, cur, depth) AS (
    SELECT slug, parent_slug, 1 FROM parents
    UNION ALL
    SELECT pa.start_slug, p.parent_slug, pa.depth + 1
    FROM parent_anc pa JOIN parents p ON p.slug = pa.cur
    WHERE pa.depth < 10000
  ),
  parent_cycle AS (
    SELECT DISTINCT start_slug AS slug FROM parent_anc WHERE cur = start_slug
  ),
  blocks_close_deps AS (
    SELECT e.dependent_slug AS dependent, e.antecedent_slug AS antecedent
    FROM :"schema".work_edge_blocks_close e
    JOIN :"schema".ledger_current lc ON lc.id = e.edge_row_id
  ),
  bc_reach(start_slug, cur) AS (
    SELECT dependent, antecedent FROM blocks_close_deps
    UNION
    SELECT r.start_slug, d.antecedent FROM bc_reach r JOIN blocks_close_deps d ON d.dependent = r.cur
  ),
  blocks_close_cycle AS (
    SELECT DISTINCT start_slug AS slug FROM bc_reach WHERE cur = start_slug
  ),
  blocks_start_deps AS (
    SELECT e.dependent_slug AS dependent, e.antecedent_slug AS antecedent
    FROM :"schema".work_edge_blocks_start e
    JOIN :"schema".ledger_current lc ON lc.id = e.edge_row_id
  ),
  bs_reach(start_slug, cur) AS (
    SELECT dependent, antecedent FROM blocks_start_deps
    UNION
    SELECT r.start_slug, d.antecedent FROM bs_reach r JOIN blocks_start_deps d ON d.dependent = r.cur
  ),
  blocks_start_cycle AS (
    SELECT DISTINCT start_slug AS slug FROM bs_reach WHERE cur = start_slug
  ),
  opened_current AS (
    SELECT work_slug AS slug FROM :"schema".ledger_current WHERE kind = 'work_opened'
  ),
  orphan_claims AS (
    SELECT lc.id, lc.work_slug AS slug FROM :"schema".ledger_current lc
    WHERE lc.kind = 'work_claimed'
      AND NOT EXISTS (SELECT 1 FROM opened_current oc WHERE oc.slug = lc.work_slug)
  ),
  orphan_closes AS (
    SELECT lc.id, lc.work_slug AS slug FROM :"schema".ledger_current lc
    WHERE lc.kind = 'work_closed'
      AND NOT EXISTS (SELECT 1 FROM opened_current oc WHERE oc.slug = lc.work_slug)
  ),
  orphan_deps AS (
    SELECT lc.id, lc.work_slug AS slug FROM :"schema".ledger_current lc
    WHERE lc.kind = 'work_depends_on'
      AND NOT EXISTS (SELECT 1 FROM opened_current oc WHERE oc.slug = lc.work_slug)
  ),
  orphan_children AS (
    SELECT e.edge_row_id AS id, e.child_slug AS slug, e.parent_slug
    FROM :"schema".work_edge_parent e
    JOIN :"schema".ledger_current lc ON lc.id = e.edge_row_id
    WHERE NOT EXISTS (SELECT 1 FROM opened_current oc WHERE oc.slug = e.parent_slug)
  ),
  composites AS (
    SELECT work_slug AS slug
    FROM :"schema".ledger_current WHERE kind = 'work_opened' AND work_discharge = 'composite'
  ),
  composite_hand_closed AS (
    SELECT c.slug, lc.id AS close_id
    FROM composites c
    JOIN :"schema".ledger_current lc ON lc.kind = 'work_closed' AND lc.work_slug = c.slug
  ),
  closed_but_tree_defeated AS (
    SELECT chc.slug, chc.close_id,
           (SELECT string_agg(format('%s (%s)', b.blocking_slug, b.reason), '; ' ORDER BY b.blocking_slug)
              FROM :"schema".work_item_strict_blockers(chc.slug) b) AS blockers
    FROM composite_hand_closed chc
    WHERE EXISTS (SELECT 1 FROM :"schema".work_item_strict_blockers(chc.slug))
  ),
  -- s73 -- the ONE new CTE: an in-force annulled close whose cited authority row has lapsed
  -- from ledger_current. Reused, not re-derived (ADR-0012 P1): reads work_review_annulled's
  -- own authority_in_force computation rather than re-parsing work_review_ref a second time.
  annulled_retracted AS (
    SELECT wra.close_id AS id, wra.slug, wra.authority_row_id
    FROM :"schema".work_review_annulled wra
    WHERE wra.authority_row_id IS NOT NULL AND NOT wra.authority_in_force
  ),
  raw_violations AS (
    SELECT 'duplicate_open'::text AS violation, slug, NULL::text AS detail,
           (SELECT min(id) FROM :"schema".ledger_current WHERE kind = 'work_opened' AND work_slug = dup_open.slug) AS target_id
    FROM dup_open
    UNION ALL
    SELECT 'shipped_without_witness', slug, 'ledger row ' || id, id FROM shipped_no_witness
    UNION ALL
    SELECT 'depends_on_unknown_slug', slug, 'depends on ' || antecedent, id FROM dangling_dep
    UNION ALL
    SELECT 'dependency_cycle', slug, NULL,
           (SELECT id FROM :"schema".ledger_current WHERE kind = 'work_opened' AND work_slug = dep_cycle.slug) AS target_id
    FROM dep_cycle
    UNION ALL
    SELECT 'dangling_parent', slug, 'parent ' || parent_slug || ' has no opening act', edge_row_id
    FROM dangling_parent
    UNION ALL
    SELECT 'parent_cycle', slug, NULL,
           (SELECT id FROM :"schema".ledger_current WHERE kind = 'work_opened' AND work_slug = parent_cycle.slug) AS target_id
    FROM parent_cycle
    UNION ALL
    SELECT 'blocks_close_cycle', slug, NULL,
           (SELECT id FROM :"schema".ledger_current WHERE kind = 'work_opened' AND work_slug = blocks_close_cycle.slug) AS target_id
    FROM blocks_close_cycle
    UNION ALL
    SELECT 'blocks_start_cycle', slug, NULL,
           (SELECT id FROM :"schema".ledger_current WHERE kind = 'work_opened' AND work_slug = blocks_start_cycle.slug) AS target_id
    FROM blocks_start_cycle
    UNION ALL
    SELECT 'orphaned_by_retraction', slug, 'surviving work_claimed row ' || id || ' cites a retracted opening act', id FROM orphan_claims
    UNION ALL
    SELECT 'orphaned_by_retraction', slug, 'surviving work_closed row ' || id || ' cites a retracted opening act', id FROM orphan_closes
    UNION ALL
    SELECT 'orphaned_by_retraction', slug, 'surviving work_depends_on row ' || id || ' cites a retracted opening act', id FROM orphan_deps
    UNION ALL
    SELECT 'orphaned_by_retraction', slug, 'surviving child work_opened row ' || id || ' names a retracted parent opening act (' || parent_slug || ')', id FROM orphan_children
    UNION ALL
    SELECT 'closed_but_tree_defeated', slug, 'close row ' || close_id || '; unresolved: ' || blockers, close_id FROM closed_but_tree_defeated
    UNION ALL
    -- s73 -- the NEW arm, target_id = the annulled close's own row id (already current by
    -- construction, work_review_annulled's own ledger_current-typed close side).
    SELECT 'annulled_authority_retracted', slug,
           'close row ' || id || ' cites annulment authority row ' || authority_row_id || ', now retracted', id
    FROM annulled_retracted
  ),
  dispositions AS (
    SELECT lc.id AS disp_id, lc.work_violation_class AS class, lc.work_violation_target_id AS target_id,
           lc.work_resolution AS resolution, lc.work_violation_witness AS witness_id
    FROM :"schema".ledger_current lc
    WHERE lc.kind = 'work_violation_disposition'
  ),
  disposition_basis_holds AS (
    SELECT d.class, d.target_id
    FROM dispositions d
    JOIN :"schema".ledger_current t ON t.id = d.target_id
    WHERE
      (d.resolution = 'retired' AND (
         t.kind <> 'work_opened'
         OR EXISTS (SELECT 1 FROM :"schema".work_item_current wic
                    WHERE wic.slug = t.work_slug AND wic.state = 'closed')
      ))
      OR
      (d.resolution = 'reissued' AND (
         d.witness_id IS NULL
         OR EXISTS (SELECT 1 FROM :"schema".ledger_current w WHERE w.id = d.witness_id)
      ))
  )
SELECT rv.violation, rv.slug, rv.detail, rv.target_id
FROM   raw_violations rv
JOIN   :"schema".ledger_current tgt ON tgt.id = rv.target_id
WHERE  NOT EXISTS (
         SELECT 1 FROM disposition_basis_holds dbh
         WHERE dbh.class = rv.violation AND dbh.target_id = rv.target_id
       );

COMMENT ON VIEW :"schema".work_item_violations IS
  'kernel/lineage/s73-typed-annulment-disposition.sql (s39 body + ONE new member,
   annulled_authority_retracted): defense-in-depth surfacing of an in-force annulled close whose
   cited authority row has since lapsed from ledger_current -- reuses work_review_annulled''s own
   authority_in_force computation. See kernel/lineage/s37-violation-disposition.sql for the v3
   debt-projection semantics this view inherits unchanged.';

-- ============================================================================================
-- ELEMENT 7 -- work_violation_history RE-ISSUED: the SAME new member, raw/unfiltered, mirroring
-- Element 6 one view over (the s37/s39 declared-history-reader posture, "every member ever
-- surfaced, never thinner"). True immediately-prior re-issue: s39 (same "no s40..s72 re-issue"
-- verification as Element 6). Every pre-existing CTE/arm is byte-identical below; only the one
-- new CTE and the one new UNION ALL arm are appended.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".work_violation_history
    WITH (security_invoker = true) AS
WITH RECURSIVE
  opens AS (
    SELECT work_slug AS slug, count(*) AS n
    FROM :"schema".ledger WHERE kind = 'work_opened'
    GROUP BY work_slug
  ),
  dup_open AS (SELECT slug FROM opens WHERE n > 1),
  shipped_no_witness AS (
    SELECT work_slug AS slug, id
    FROM :"schema".ledger
    WHERE kind = 'work_closed' AND work_resolution = 'shipped'
      AND (work_witness IS NULL OR btrim(work_witness) = '')
  ),
  deps AS (
    SELECT work_slug AS dependent, work_depends_on AS antecedent, id
    FROM :"schema".ledger WHERE kind = 'work_depends_on'
  ),
  dangling_dep AS (
    SELECT d.dependent AS slug, d.antecedent, d.id FROM deps d
    WHERE NOT EXISTS (SELECT 1 FROM :"schema".ledger o
                       WHERE o.kind = 'work_opened' AND o.work_slug = d.antecedent)
  ),
  bc_deps AS (
    SELECT dependent_slug AS dependent, antecedent_slug AS antecedent
    FROM :"schema".work_edge_blocks_close
  ),
  bc_reach_dep(start_slug, cur) AS (
    SELECT dependent, antecedent FROM bc_deps
    UNION
    SELECT r.start_slug, d.antecedent FROM bc_reach_dep r JOIN bc_deps d ON d.dependent = r.cur
  ),
  dep_cycle AS (SELECT DISTINCT start_slug AS slug FROM bc_reach_dep WHERE cur = start_slug),
  parents AS (
    SELECT child_slug AS slug, parent_slug, edge_row_id FROM :"schema".work_edge_parent
  ),
  dangling_parent AS (
    SELECT p.slug, p.parent_slug, p.edge_row_id FROM parents p
    WHERE NOT EXISTS (SELECT 1 FROM :"schema".ledger o
                       WHERE o.kind = 'work_opened' AND o.work_slug = p.parent_slug)
  ),
  parent_anc(start_slug, cur, depth) AS (
    SELECT slug, parent_slug, 1 FROM parents
    UNION ALL
    SELECT pa.start_slug, p.parent_slug, pa.depth + 1
    FROM parent_anc pa JOIN parents p ON p.slug = pa.cur
    WHERE pa.depth < 10000
  ),
  parent_cycle AS (SELECT DISTINCT start_slug AS slug FROM parent_anc WHERE cur = start_slug),
  blocks_close_deps AS (
    SELECT dependent_slug AS dependent, antecedent_slug AS antecedent FROM :"schema".work_edge_blocks_close
  ),
  bc_reach(start_slug, cur) AS (
    SELECT dependent, antecedent FROM blocks_close_deps
    UNION
    SELECT r.start_slug, d.antecedent FROM bc_reach r JOIN blocks_close_deps d ON d.dependent = r.cur
  ),
  blocks_close_cycle AS (SELECT DISTINCT start_slug AS slug FROM bc_reach WHERE cur = start_slug),
  blocks_start_deps AS (
    SELECT dependent_slug AS dependent, antecedent_slug AS antecedent FROM :"schema".work_edge_blocks_start
  ),
  bs_reach(start_slug, cur) AS (
    SELECT dependent, antecedent FROM blocks_start_deps
    UNION
    SELECT r.start_slug, d.antecedent FROM bs_reach r JOIN blocks_start_deps d ON d.dependent = r.cur
  ),
  blocks_start_cycle AS (SELECT DISTINCT start_slug AS slug FROM bs_reach WHERE cur = start_slug),
  opened_current AS (
    SELECT work_slug AS slug FROM :"schema".ledger_current WHERE kind = 'work_opened'
  ),
  orphan_claims AS (
    SELECT lc.id, lc.work_slug AS slug FROM :"schema".ledger_current lc
    WHERE lc.kind = 'work_claimed'
      AND NOT EXISTS (SELECT 1 FROM opened_current oc WHERE oc.slug = lc.work_slug)
  ),
  orphan_closes AS (
    SELECT lc.id, lc.work_slug AS slug FROM :"schema".ledger_current lc
    WHERE lc.kind = 'work_closed'
      AND NOT EXISTS (SELECT 1 FROM opened_current oc WHERE oc.slug = lc.work_slug)
  ),
  orphan_deps AS (
    SELECT lc.id, lc.work_slug AS slug FROM :"schema".ledger_current lc
    WHERE lc.kind = 'work_depends_on'
      AND NOT EXISTS (SELECT 1 FROM opened_current oc WHERE oc.slug = lc.work_slug)
  ),
  orphan_children AS (
    SELECT e.edge_row_id AS id, e.child_slug AS slug, e.parent_slug
    FROM :"schema".work_edge_parent e
    JOIN :"schema".ledger_current lc ON lc.id = e.edge_row_id
    WHERE NOT EXISTS (SELECT 1 FROM opened_current oc WHERE oc.slug = e.parent_slug)
  ),
  composites AS (
    SELECT work_slug AS slug
    FROM :"schema".ledger_current WHERE kind = 'work_opened' AND work_discharge = 'composite'
  ),
  composite_hand_closed AS (
    SELECT c.slug, lc.id AS close_id
    FROM composites c
    JOIN :"schema".ledger_current lc ON lc.kind = 'work_closed' AND lc.work_slug = c.slug
  ),
  closed_but_tree_defeated AS (
    SELECT chc.slug, chc.close_id,
           (SELECT string_agg(format('%s (%s)', b.blocking_slug, b.reason), '; ' ORDER BY b.blocking_slug)
              FROM :"schema".work_item_strict_blockers(chc.slug) b) AS blockers
    FROM composite_hand_closed chc
    WHERE EXISTS (SELECT 1 FROM :"schema".work_item_strict_blockers(chc.slug))
  ),
  -- s73 -- the raw/unfiltered mirror of Element 6's own new CTE, same reuse discipline.
  annulled_retracted AS (
    SELECT wra.close_id AS id, wra.slug, wra.authority_row_id
    FROM :"schema".work_review_annulled wra
    WHERE wra.authority_row_id IS NOT NULL AND NOT wra.authority_in_force
  ),
  raw_violations AS (
    SELECT 'duplicate_open'::text AS violation, slug, NULL::text AS detail,
           (SELECT min(id) FROM :"schema".ledger WHERE kind = 'work_opened' AND work_slug = dup_open.slug) AS target_id
    FROM dup_open
    UNION ALL
    SELECT 'shipped_without_witness', slug, 'ledger row ' || id, id FROM shipped_no_witness
    UNION ALL
    SELECT 'depends_on_unknown_slug', slug, 'depends on ' || antecedent, id FROM dangling_dep
    UNION ALL
    SELECT 'dependency_cycle', slug, NULL,
           (SELECT id FROM :"schema".ledger WHERE kind = 'work_opened' AND work_slug = dep_cycle.slug)
    FROM dep_cycle
    UNION ALL
    SELECT 'dangling_parent', slug, 'parent ' || parent_slug || ' has no opening act', edge_row_id
    FROM dangling_parent
    UNION ALL
    SELECT 'parent_cycle', slug, NULL,
           (SELECT id FROM :"schema".ledger WHERE kind = 'work_opened' AND work_slug = parent_cycle.slug)
    FROM parent_cycle
    UNION ALL
    SELECT 'blocks_close_cycle', slug, NULL,
           (SELECT id FROM :"schema".ledger WHERE kind = 'work_opened' AND work_slug = blocks_close_cycle.slug)
    FROM blocks_close_cycle
    UNION ALL
    SELECT 'blocks_start_cycle', slug, NULL,
           (SELECT id FROM :"schema".ledger WHERE kind = 'work_opened' AND work_slug = blocks_start_cycle.slug)
    FROM blocks_start_cycle
    UNION ALL
    SELECT 'orphaned_by_retraction', slug, 'surviving work_claimed row ' || id || ' cites a retracted opening act', id FROM orphan_claims
    UNION ALL
    SELECT 'orphaned_by_retraction', slug, 'surviving work_closed row ' || id || ' cites a retracted opening act', id FROM orphan_closes
    UNION ALL
    SELECT 'orphaned_by_retraction', slug, 'surviving work_depends_on row ' || id || ' cites a retracted opening act', id FROM orphan_deps
    UNION ALL
    SELECT 'orphaned_by_retraction', slug, 'surviving child work_opened row ' || id || ' names a retracted parent opening act (' || parent_slug || ')', id FROM orphan_children
    UNION ALL
    SELECT 'closed_but_tree_defeated', slug, 'close row ' || close_id || '; unresolved: ' || blockers, close_id FROM closed_but_tree_defeated
    UNION ALL
    SELECT 'annulled_authority_retracted', slug,
           'close row ' || id || ' cites annulment authority row ' || authority_row_id || ', now retracted', id
    FROM annulled_retracted
  )
SELECT rv.violation, rv.slug, rv.detail, rv.target_id,
       d.id AS disposition_id, d.work_resolution AS disposition_resolution,
       d.rationale AS disposition_basis, d.work_violation_witness AS disposition_witness,
       (d.id IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM :"schema".ledger s2 WHERE s2.supersedes = d.id)) AS disposition_in_force,
       EXISTS (SELECT 1 FROM :"schema".ledger_current tgt WHERE tgt.id = rv.target_id) AS target_in_force,
       (SELECT s3.id FROM :"schema".ledger s3 WHERE s3.supersedes = rv.target_id) AS target_retraction_id
FROM   raw_violations rv
LEFT JOIN :"schema".ledger d
       ON d.kind = 'work_violation_disposition'
      AND d.work_violation_class = rv.violation
      AND d.work_violation_target_id = rv.target_id
ORDER BY rv.violation, rv.slug, d.id;

COMMENT ON VIEW :"schema".work_violation_history IS
  'kernel/lineage/s73-typed-annulment-disposition.sql, re-issued to add the
   annulled_authority_retracted raw/unfiltered arm (mirroring Element 6 one view over) -- UNFILTERED
   read, every work_item_violations member ever surfaced, never thinner. See s37''s own header for
   the full semantics this view carries unchanged.';

GRANT SELECT ON :"schema".work_violation_history TO :"role";

-- ============================================================================================
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 amendment):
--
--   - INVARIANT: `work_review_disposition` carries a FOURTH legal value, `annulled`, licensed
--     ONLY on kind='work_closed' -- a construction-time-unrepresentable state without BOTH (a) a
--     mandatory, non-empty work_review_ref, and (b) at least one row:<id> token in that ref
--     naming an IN-FORCE ledger row whose actor and (stamp_session, stamp_agent) pair are BOTH
--     distinct from the annulled obligation's obligor (the superseded deferred close's own actor,
--     or this close's own actor absent a predecessor). A strict/composite close of disposition
--     annulled is refused on the SAME footing as deferred/bookkeeping (no reviewer verdict to
--     check the tree against). An in-force annulled close is EXCLUDED from work_review_gap by
--     construction (disjoint from 'deferred'), never merely answered. An annulled close whose
--     cited authority row has since lapsed from ledger_current is SURFACED (never silently
--     tolerated) as a new work_item_violations/work_violation_history member,
--     annulled_authority_retracted, answerable by the SAME work_violation_disposition mechanism
--     every other member already uses.
--
--   - QUANTIFICATION UNIVERSE -- enumerated OUTWARD (ADR-0000's own 2026-07-02 amendment text),
--     checked against the FULL s15..s72 chain this delta applies on top of:
--       TABLES: unchanged -- no new base table, no new column. The annulled fact rides the
--         EXISTING work_review_disposition/work_review_ref columns (s29), widened by one CHECK
--         value and two new CHECKs, exactly the s38-bookkeeping/s39-blocks-start precedent for a
--         pure vocabulary widening on an existing column.
--       EVERY KIND THAT CARRIES work_review_disposition/work_review_ref: unchanged (work_closed,
--         work_violation_disposition, s29/s37) -- this delta narrows WHICH VALUE is legal on
--         WHICH of those two kinds (annulled: work_closed alone), it does not widen either
--         column's kind licensing.
--       VIEWS re-read for the wildcard/column-complete class (s20/s22/.../s72 all named):
--         ledger_current / countersigned_in_force -- NEITHER gains a column here (this delta adds
--         no column, only new legal VALUES/CHECKs on existing columns) -- re-verified NOT members
--         needing re-issue. work_item_current -- re-verified NOT a member: it carries no
--         disposition-value-specific column and needs none. work_review_gap -- re-verified NOT a
--         member (see this file's header, Element 4(a): its exact-equality filter on 'deferred'
--         already, vacuously, excludes 'annulled' -- VERIFIED by reading its s37-head text above,
--         not merely asserted).
--       KIND VOCABULARY -- unchanged. This delta adds no new `kind` value: the annulment fact
--         rides the EXISTING work_closed kind's own columns, exactly like s38's bookkeeping value
--         one column-value over.
--       GRANTS -- mirrors s38/s39's own posture: the ONE new view (work_review_annulled) gets a
--         fresh GRANT SELECT; work_item_violations/work_violation_history keep their EXISTING
--         grants (s21's additive-column-order idiom: zero columns added or removed by either
--         re-issue -- both column lists are byte-identical to their s39 predecessors). The
--         re-issued validate_review_witness_existence/validate_work_item_close functions need no
--         explicit GRANT (Postgres grants EXECUTE to PUBLIC by default, verified against every
--         prior re-issue of either function, none of which received one either).
--       ENGINE -- VERIFIED, not merely asserted (per this codebase's own standing instruction):
--         `engine/lp/work_review.lp`'s own-leaf-unresolved rule
--         (`w_closed_in_force(Slug,R,_), w_disposition(R,deferred), not w_discharged(R)`) and its
--         SQL floor twin (`engine/ledger_floor.py`'s `own_unresolved` CTE,
--         `WHERE c.disp = 'deferred' AND ...`) BOTH test EQUALITY against the single literal
--         `deferred` -- neither enumerates the disposition vocabulary as a closed set (mirroring
--         s38's own bookkeeping precedent, verified against the SAME two files a second time,
--         literal for literal). `engine/ledger_edb.py`'s `w_disposition(RowId, Disp)` emission
--         passes through WHATEVER value the column holds, with no hardcoded value list to widen.
--         An annulled-disposition close therefore already produces `w_disposition(RowId,annulled)`
--         with ZERO engine-layer edits, and is already correctly excluded from
--         `w_own_leaf_unresolved`/its SQL twin by the SAME not-equal-to-deferred logic that
--         already excludes witnessed/bookkeeping. `annulled_authority_retracted` (Element 6/7,
--         SQL-side only, construction-time-defense-in-depth, exactly s28/s30/s39's own disclosed
--         "ENGINE -- NONE" precedent for a defense-in-depth cycle/orphan member) has no ASP-side
--         counterpart and needs none -- `./judge`'s existing SQL/ASP differential is UNAFFECTED
--         and continues to AGREE, witnessed in this delta's own scratch acceptance below.
--
--   - DENOMINATION: `annulled` stays `text`, the SAME closed-vocabulary column
--     (work_review_disposition) every other disposition value already lives on -- never a new
--     boolean or a parallel flag. The authority citation is denominated in the EXISTING row:<id>
--     bare-reference vocabulary (s48/s53/s58's own established form), never a new reference
--     syntax. Distinctness is denominated in the SAME two currencies s21/s29's own Element C
--     already uses -- the principal `actor` id, and the (stamp_session, stamp_agent) PAIR -- never
--     re-derived from `ts` or any writer-supplied column.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): this delta is NOT
-- class-ratified fail-safe -- the spec's own §3 says so explicitly and states why: "a vocabulary
-- value that lets recorded debt be discharged without a review is a relaxation under the
-- standing class test," even though every construction is refusal-guarded and nothing existing
-- is widened for a writer who never uses the new value. It ships under the maintainer's own
-- explicit ratification of design/FABLE-TYPED-ANNULMENT-DISPOSITION-SPEC.md (ledger row 1087,
-- 2026-08-06, cited above), the spec's own §3 authority, not the 2026-07-09 class rule.
--
-- LIMITS (pre-registered, matching s22/.../s72's own disclosure convention):
--   - `annulled` is licensed on kind='work_closed' ALONE (Element 1's own header) -- a
--     work_violation_disposition row cannot carry it. A future delta wanting that extension
--     widens work_review_annulled_kind_shape's own value set, not a second CHECK.
--   - The authority citation's evidentiary requirement is DELIBERATELY UNSCOPED BY KIND (this
--     file's own header, "no kind restriction on the authority row") -- any in-force, distinct-
--     actor ledger row satisfies it, including an ordinary `decision`/`finding`/`note` row. This
--     is a wider net than s69's own review/finding evidentiary-shape test, by design: annulment
--     authority is a distinct-actor RULING, not a review.
--   - Only the FIRST row:<id> token is surfaced by work_review_annulled's own audit columns
--     (Element 5's own header) -- the construction-time check validates EVERY cited token for
--     existence/distinctness/in-force status, but the single-row-per-close audit shape denominates
--     on one authority. A close citing multiple authority rows is fully construction-time-valid;
--     its audit row simply names the first.
--   - Like every trigger-enforced refusal in this lineage, the construction-time refusals here
--     bind ONLY the granted `:role`'s ordinary INSERT path -- a schema-owner/superuser with DDL
--     privilege can disable a trigger or write directly, the same disclosed bound s26/.../s72
--     already name.
--   - `annulled_authority_retracted` is SURFACED, never refused at construction (it cannot be --
--     the authority was in force when the annulment was written; only a LATER, independent act
--     retracts it) -- the spec's own verb, applied here exactly as `orphaned_by_retraction` (s31)
--     already established the pattern.
--   - The no-self-annulment predicate composes s21's fail-safe pair-distinctness with a plain
--     actor-identity check (this file's own header, "WHY BOTH") -- it does NOT compose with s41's
--     agent_class-scoped independence honesty (D-6, "human-attested scoping" for
--     managerial/financial review claims): that refusal is specific to the review_detail
--     independence vocabulary (a DIFFERENT table, a DIFFERENT claim shape) and is out of this
--     delta's own quantification universe (the spec's own §2a closure statement names
--     work_review_disposition/work_review_gap/the audit view/the B2 verb, not review_detail).
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s72): schema/kern/role
-- are psql variables so this delta is VALIDATED on a throwaway substrate before any real apply.
--   VALIDATE (reachable throwaway; scratch CHAIN order matches gates/ledger_reader_allowlist.py's
--   and gates/kind_shape_manifest_gate.py's own extended CHAIN):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s73val -v kern=s73val_kernel -v role=s73val_rw \
--        -f high_watermark_1.sql -f s20-obligation-grants-and-view-refresh.sql \
--        -f s21-session-aware-distinctness.sql -f s22-work-item-ledger.sql \
--        -f s23-per-invocation-stamp-token.sql -f s24-declared-event-time.sql \
--        -f s25-commission-kind.sql -f s26-row-hash-chain.sql -f s27-chain-high-water.sql \
--        -f s28-work-parent-edge.sql -f s29-obligation-item-key-and-typed-close.sql \
--        -f s30-typed-dependency-edges.sql -f s31-supersession-uniform-retraction.sql \
--        -f s32-edge-views-single-home.sql -f s33-composite-discharge.sql \
--        -f s34-computed-grade-refusal.sql -f s35-validation-decomposition.sql \
--        -f s36-decision-grade.sql -f s37-violation-disposition.sql \
--        -f s38-bookkeeping-close.sql -f s39-blocks-start.sql \
--        -f s40-principal-identity-events.sql -f s41-principal-bindings-and-relations.sql \
--        -f s42-row-hash-full-coverage.sql -f s43-typed-verdict-write-boundary.sql \
--        -f s45-standing-lifecycle.sql -f s44-model-identity-attestation.sql \
--        -f s46-credited-views.sql -f s47-claim-on-closed-refusal.sql \
--        -f s48-review-witness-existence.sql -f s49-journaler-overflow-guard.sql \
--        -f s50-defeat-input-raw-domain.sql -f s51-artifact-store.sql \
--        -f s52-artifact-witness-check.sql -f s53-belief-substrate.sql \
--        -f s54-belief-views.sql -f s55-dispatch-grain-independence.sql \
--        -f s56-reservation-residue.sql -f s57-obligation-revocation-event.sql \
--        -f s58-missive-substrate.sql -f s59-missive-views.sql \
--        -f s60-entitlement-enforcement.sql -f s61-signature-symmetry-and-key-binding.sql \
--        -f s62-delegation-lifecycle-gating.sql -f s63-supersession-body-restoration.sql \
--        -f s64-principal-stamps-delegation-conditions.sql -f s65-refusal-attempted-kind.sql \
--        -f s66-forged-stamp-journal-totality.sql -f s67-refusal-digest-bound.sql \
--        -f s68-typed-absence-dispositions.sql -f s69-role-coherence-refusals.sql \
--        -f s70-scope-binding.sql -f s71-row-level-scope-policies.sql \
--        -f s72-stamp-binding-conjunct.sql -f s73-typed-annulment-disposition.sql
--     (provision a genesis seed per s26's own block before the first ledger INSERT; the world's
--     principals must be REGISTERED and a standing DECLARED per s40's own birth-step note.)
--   REAL: NEVER applied to any existing world by this delta's own authoring act (maintainer
--   ruling 2026-07-11, "runs are strictly linear"). This delta reaches reality by entering a
--   FUTURE world's birth chain, wired into `bootstrap/new-project.sh`'s `LINEAGE_CHAIN` in this
--   SAME commit (s37/s38/s39 precedent). Authored and scratch-witnessed on scratch schema pairs
--   in the TOY db only -- NOT applied to any live schema by this pass.
-- Run as the schema owner (bork). Idempotent (DROP+ADD CONSTRAINT; CREATE OR REPLACE).
-- ============================================================================================
