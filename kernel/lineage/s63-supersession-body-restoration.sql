-- s63 SUPERSESSION-BODY RESTORATION (design/FABLE-S63-SUPERSESSION-BODY-RESTORATION-SPEC.md,
-- Fable-authored, ledger rows 1429/1430 -- the sweep that surfaced the finding and the
-- witnessed finding itself). FAIL-SAFE-ADDITIVE ON THE MERITS (CLAUDE.md 2026-07-09 class rule)
-- -- ROUTING RESOLVED (spec §5, 2026-07-26, ledger row 1434): this delta restores four refusal
-- branches that were live at s58 head and silently deleted by s61 Element 7's stale-base
-- `CREATE OR REPLACE`; read literally against CURRENT head it only ADDS refusals (nothing
-- currently permitted becomes newly refused), but because the branches it adds were DROPPED by
-- an unratified accident rather than never having existed, the class-ratified fail-safe-additive
-- family's own "doubt about which side a delta falls on IS the routing" clause applied, and the
-- spec asked the maintainer explicitly rather than self-certifying the fail-safe class -- the
-- maintainer DELEGATED the call (row 1434), and the resolution is: s63 RIDES THE CLASS (it
-- permits nothing new, returning the kernel to what s53/s58 already ratified; restoration rides
-- the class only when the drop itself is on the record as an accident, here row 1430 -- spec §5's
-- own cabining). This file was built and scratch-witnessed under the prior (open-question)
-- status; the routing question is now closed, and this header reflects the closed status, not
-- the state at authoring time.
--
-- THE DEFECT BEING REPAIRED (spec §1, zero-context): `validate_supersession_target`'s re-issue
-- chain for the function this file re-issues is s43 (first definer) -> s45 (Element 4, standing-
-- lifecycle discipline) -> s53 (Element 5, belief discipline) -> s58 (Element 5, missive
-- discipline, THREE more blocks) -> s61 (Element 7, signed-supersession symmetry). s61 Element 7
-- claimed "Base body = s45's (UNCHANGED by s60)" -- true that s45's write_refused/standing-
-- lifecycle blocks are byte-identical carried text, FALSE that s45 was the immediately-prior
-- re-issue: s53 and s58 both landed between s45 and s61 and were never consulted. s61's
-- `CREATE OR REPLACE` therefore silently DELETED s53's belief-holder-only-revision branch and
-- all three of s58's missive branches (missive_sent same-thread-successor-only, missive_received
-- unconditionally unretractable, missive_disposed same-regards-only) while correctly adding its
-- own (wanted) symmetry block. At the s62 head every newborn world accepts: (1) supersession of
-- a belief by a different principal or a different-kind row; (2) supersession of missive_sent by
-- anything other than a same-thread successor; (3) supersession of missive_received at all; (4)
-- supersession of missive_disposed by a different-kind or different-regards row. Leg 1 is
-- live-witnessed both polarities (this build's own scratch witness, below); legs 2-4 are
-- established textually -- the branches are simply absent from the deployed s61/s62 body, byte-
-- diffed against s58 Element 5's own text (this build's own witness table, WITNESSED, diff
-- commands + empty output).
--
-- THE FIX: this file re-issues `validate_supersession_target` ONE more time with the UNION body
-- -- s58 Element 5's four branches (the belief branch, byte-diffed VERBATIM against
-- kernel/lineage/s58-missive-substrate.sql:829-861, restored here byte-identically -- the
-- spec's own line-range citation covers the belief branch plus the three missive branches, one
-- contiguous span) restored VERBATIM, plus s61 Element 7's symmetry block (byte-diffed VERBATIM
-- against kernel/lineage/s61-signature-symmetry-and-key-binding.sql:580-609) retained VERBATIM.
-- No other semantics change; no other function is touched.
--
-- THE HEAD-BODY RULE (s45's own standing instruction, carried here verbatim per every prior
-- precedent): the immediately-prior re-issue of `validate_supersession_target` is s61
-- (kernel/lineage/s61-signature-symmetry-and-key-binding.sql) Element 7; the prior-prior is s58
-- (kernel/lineage/s58-missive-substrate.sql) Element 5. This delta exists BECAUSE s61's own base
-- claim was false -- s61 cited s45, not s58, as its base. The write_refused and standing-
-- lifecycle blocks below are byte-identical carried text from s43/s45 (verified: s58's and s61's
-- own copies of these two blocks differ from each other in COMMENT TEXT ONLY, diffed empty on
-- code); the DECLARE/SELECT INTO widening (three extra target columns: actor, missive_thread,
-- missive_regards) is s58's own Element 5 widening, required verbatim to feed the restored
-- missive/belief branches -- s61's narrower three-column SELECT is superseded by this wider one
-- exactly as s58 itself already established it should be. gates/lineage_reissue_lineage.py
-- (this same commit) DETECTS the class this delta closes when it is run: a re-issue's own header
-- must name its TRUE immediately-prior re-issue and hash-bind that prior's body, or the gate
-- reports the violation loudly. Stated honestly, not as an umbrella claim: this gate is not, as
-- of this commit, wired into any enforcement path (not hooks/pre-commit, no other invocation
-- site) -- it must be run explicitly to catch anything; wiring it into a standing enforcement
-- surface is a separate maintainer-batch hooks/ change, tracked apart from this delta.
--
-- PREREQUISITE: this delta REQUIRES s62 (kernel/lineage/s62-delegation-lifecycle-gating.sql)
-- applied first -- it re-issues `validate_supersession_target` in the exact shape s61 left it
-- (s62 does not touch this function at all, verified: s62's own re-issues are
-- entitlement_act_class_of and validate_entitlement only), so every object this file's body
-- assumes (signed_commissions, the four columns s61 added, the missive_* and belief_* columns
-- s53/s58 added) must already exist in its s58-through-s62 shape. Applying this file on a
-- pre-s61 kernel fails loudly at CREATE OR REPLACE FUNCTION time (signed_commissions or a
-- referenced column does not exist) -- the correct, disclosed failure mode, matching every prior
-- PREREQUISITE precedent.
--
-- REAL: NEVER applied to any existing world by this authoring act (runs-are-strictly-linear,
-- 2026-07-11). Enters a FUTURE world's birth chain via bootstrap/new-project.sh's LINEAGE_CHAIN
-- at the maintainer's own future integration act -- the ROUTING question (spec §5) is resolved
-- (row 1434, fail-safe-additive class), but wiring a delta into a REAL deployment's birth chain
-- is a separate, later maintainer act on that deployment's own scaffold, per runs-are-linear;
-- this file sits in kernel/lineage/ as a tracked, scratch-witnessed delta from its first commit
-- onward (bootstrap/new-project.sh's --new-world apply LOOP is glob-driven and N-thresholded,
-- not ratification-gated, so it picks this file up automatically on any --new-world run against
-- a tree that carries it -- exactly the mechanism this build's own scratch witness relies on;
-- the ratification boundary is which COMMIT of kernel/lineage/ a real deployment's birth reads
-- from, i.e. whether this file has reached the branch that deployment scaffolds from, never a
-- property the apply loop itself checks). Authored and scratch-witnessed on scratch schema pairs
-- in the TOY db only, per this build's own commission constraints.
-- ============================================================================================
-- ELEMENT 1 -- validate_supersession_target RE-ISSUED (SIXTH re-issue; immediately-prior
-- re-issue: s61 kernel/lineage/s61-signature-symmetry-and-key-binding.sql Element 7;
-- prior-prior: s58 kernel/lineage/s58-missive-substrate.sql Element 5). UNION BODY: the
-- write_refused/standing-lifecycle base (byte-identical carried text, s43/s45's own, unedited
-- since s45) plus s58 Element 5's FOUR branches (belief, missive_sent, missive_received,
-- missive_disposed -- byte-diffed VERBATIM against s58:829-861) plus s61 Element 7's symmetry
-- block (byte-diffed VERBATIM against s61:580-609). s61's DECLARE/SELECT INTO is widened back to
-- s58's own three-extra-column shape (actor, missive_thread, missive_regards) -- required
-- plumbing for the restored branches, not a new semantic.
-- prior-body-sha256: 6054bd8520ed7e0399c56c09bbafef7646490bfa47966ddcf618a58e034412e1 (s61-signature-symmetry-and-key-binding.sql)
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_supersession_target() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_target_kind text;
  v_target_db_role text;
  v_target_subject bigint;
  v_target_actor bigint;
  v_target_thread text;
  v_target_regards bigint;
  v_target_signed boolean;
  v_new_signed boolean;
BEGIN
  IF NEW.supersedes IS NOT NULL THEN
    SELECT l.kind, l.principal_db_role, l.principal_subject, l.actor, l.missive_thread,
           l.missive_regards
      INTO v_target_kind, v_target_db_role, v_target_subject, v_target_actor, v_target_thread,
           v_target_regards
      FROM ledger l WHERE l.id = NEW.supersedes;

    IF v_target_kind = 'write_refused' THEN
      RAISE EXCEPTION 'Ledger policy: a write_refused row is UNRETRACTABLE (s43, ratified R6) — row % records a historical fact about a refused attempt; it asserts nothing retractable, and superseding it is the one path by which a later writer could make a refusal vanish from every current view. The record stands; if the refusal was wrong, the corrected write simply succeeds beside it (kernel/lineage/s43-typed-verdict-write-boundary.sql Element 2).', NEW.supersedes;
    END IF;

    -- s45 §3.4: standing-lifecycle supersession discipline (the conversion-found closure --
    -- without it, ANY writer could lift a revocation or resurrect a stale declaration by
    -- superseding it with an unrelated row of a different kind).
    IF v_target_kind IN ('principal_standing_declared', 'principal_suspended', 'principal_revoked') THEN
      IF NEW.kind IS DISTINCT FROM v_target_kind THEN
        RAISE EXCEPTION 'Ledger policy: a standing-lifecycle row (kind ''%'', row %) is superseded ONLY by its OWN kind (s45, kernel/lineage/s45-standing-lifecycle.sql §3.4) — this write is kind ''%''. Rotation/re-declaration or unbind for declarations (./led principal declare-standing / ./led principal undeclare-standing); re-suspend-correction or lift for suspensions (./led principal suspend --supersedes / ./led principal lift-suspension); re-revoke-correction for revocations. A cross-kind supersession would silently alter derived standing (who a role speaks for, or whether a principal is suspended/revoked) with no typed act — refused at construction.', v_target_kind, NEW.supersedes, NEW.kind;
      END IF;

      IF v_target_kind = 'principal_standing_declared' THEN
        IF NEW.principal_db_role IS DISTINCT FROM v_target_db_role THEN
          RAISE EXCEPTION 'Ledger policy: a row superseding a standing declaration must restate the SAME db_role its target governs (s45 §3.4) — target row % binds role ''%'', this write names ''%''. A rotation or unbind restates the role it governs; to bind a DIFFERENT role, write a fresh (non-superseding) declaration instead.', NEW.supersedes, v_target_db_role, NEW.principal_db_role;
        END IF;
        IF NEW.principal_binding_active = false AND NEW.principal_subject IS DISTINCT FROM v_target_subject THEN
          RAISE EXCEPTION 'Ledger policy: an UNBIND must restate the SAME subject principal its target declaration binds (s45 §3.4) — target row % binds principal %, this unbind names %. A ROTATION (principal_binding_active=true) may repoint the subject by design; an unbind may not.', NEW.supersedes, v_target_subject, NEW.principal_subject;
        END IF;
      ELSIF v_target_kind IN ('principal_suspended', 'principal_revoked') THEN
        IF NEW.principal_subject IS DISTINCT FROM v_target_subject THEN
          RAISE EXCEPTION 'Ledger policy: a lift or rationale-correction must restate the SAME subject principal its target row regards (s45 §3.4) — target row % (kind ''%'') regards principal %, this write names %.', NEW.supersedes, v_target_kind, v_target_subject, NEW.principal_subject;
        END IF;
      END IF;
    END IF;

    -- s53: belief supersession discipline (unedited).
    IF v_target_kind = 'belief' THEN
      IF NEW.kind IS DISTINCT FROM 'belief' THEN
        RAISE EXCEPTION 'belief policy: a belief is revised only by its own holder through supersession (s31 uniform retraction), same kind (s53, design/FABLE-BELIEF-SUBSTRATE-SPEC.md §3.3) — this write is kind ''%'', but row % is a belief. Another principal''s contrary position is a CONTEST — write your own belief with contests=row:% and both enter visible doubt until resolved by evidence class or withdrawal (Q3, paraconsistent; recency never decides between principals).', NEW.kind, NEW.supersedes, NEW.supersedes;
      ELSIF NEW.actor IS NOT NULL AND v_target_actor IS NOT NULL AND NEW.actor <> v_target_actor THEN
        RAISE EXCEPTION 'belief policy: a belief is superseded only by its own holder (supersession = self-revision, s31) — row % is held by a different principal than this write''s actor (s53, design/FABLE-BELIEF-SUBSTRATE-SPEC.md §3.3). Another principal''s contrary position is a CONTEST — write your own belief with contests=row:% and both enter visible doubt until resolved by evidence class or withdrawal (Q3, paraconsistent; recency never decides between principals).', NEW.supersedes, NEW.supersedes;
      END IF;
    END IF;

    -- s58: missive_sent supersession discipline (Q7 ratified, spec §2.5) -- superseding a
    -- missive_sent row is refused unless the superseding row is itself the successor missive
    -- in the SAME thread. No same-actor condition -- the party is the world, not the principal
    -- (spec §13 item 6).
    IF v_target_kind = 'missive_sent' THEN
      IF NOT (NEW.kind = 'missive_sent' AND NEW.missive_thread = v_target_thread) THEN
        RAISE EXCEPTION 'missive policy: a missive_sent row (row %, thread ''%'') is superseded ONLY by a same-thread successor missive_sent row (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.5, Q7 ratified) — an author revising its position SENDS the revision (a withdrawal, or a successor assertion/request with responds_to) so the supersession itself travels and the addressee''s missive_stale view sees it; a silent local retraction is exactly the staleness class this family exists to close.', NEW.supersedes, v_target_thread;
      END IF;
    END IF;

    -- s58: missive_received target refused outright -- a receipt is unretractable history
    -- (spec §2.5, §13 item 6).
    IF v_target_kind = 'missive_received' THEN
      RAISE EXCEPTION 'missive policy: a missive_received row (row %) may NEVER be superseded — a receipt is a historical fact of arrival; superseding it is the one path by which delivery could be un-recorded and by which the dedup guarantee could be argued around (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.5, §13 item 6). Nothing was recorded.', NEW.supersedes;
    END IF;

    -- s58: missive_disposed supersession discipline -- re-disposition of the SAME receipt only
    -- (the s45 identity-continuity pattern, spec §2.5; AMENDMENT 1: was `regards`, now
    -- `missive_regards`).
    IF v_target_kind = 'missive_disposed' THEN
      IF NOT (NEW.kind = 'missive_disposed' AND NEW.missive_regards = v_target_regards) THEN
        RAISE EXCEPTION 'missive policy: a missive_disposed row (row %, regards %) is superseded ONLY by a same-kind re-disposition regarding the SAME receipt (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.5) — this write is kind ''%'' regarding %.', NEW.supersedes, v_target_regards, NEW.kind, NEW.missive_regards;
      END IF;
    END IF;

    -- s61 (design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §2 item 1): SIGNED SUPERSESSION
    -- SYMMETRY. "signed force" for a row R = R itself is a commission independently attested
    -- VERIFIED (Element 5's signed_commissions view, keyed by commission id) OR R carries a
    -- signature_symmetry_witness naming such an attestation directly (Element 6 already
    -- refused a malformed witness at construction, so any non-NULL witness reaching this point
    -- IS a genuine commission_signature_verified row id). Computed for the TARGET via the
    -- row-addressed read above (extended by two columns); computed for NEW directly from the
    -- trigger row (no query needed -- NEW.kind/NEW.signature_symmetry_witness are already in
    -- hand). NEW can never satisfy the "itself an attested commission" disjunct (the
    -- attestation, by construction, can only be written AFTER the commission row it attests
    -- already exists -- so a commission row can never attest itself in the same statement this
    -- trigger fires within) -- this is not a gap, it is the correct asymmetry: a supersessor's
    -- OWN force can only rest on a signature by CITING an already-independently-verified
    -- commission, never by being verified in the same breath as its own insertion.
    SELECT EXISTS (SELECT 1 FROM signed_commissions sc WHERE sc.commission_id = NEW.supersedes)
        OR (v_target_kind IS NOT NULL AND EXISTS (
              SELECT 1 FROM ledger l WHERE l.id = NEW.supersedes
              AND l.signature_symmetry_witness IS NOT NULL
              AND EXISTS (SELECT 1 FROM signed_commissions sc2
                          WHERE sc2.row_id = l.signature_symmetry_witness)))
      INTO v_target_signed;
    IF v_target_signed THEN
      SELECT (NEW.signature_symmetry_witness IS NOT NULL
              AND EXISTS (SELECT 1 FROM signed_commissions sc3
                          WHERE sc3.row_id = NEW.signature_symmetry_witness))
        INTO v_new_signed;
      IF NOT v_new_signed THEN
        RAISE EXCEPTION 'Ledger policy: SIGNED supersession symmetry refused (s61, design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §2 item 1) — target row % (kind ''%'') rests its force on a VERIFIED signature (an independently GPG-attested commission); it may only be superseded by an act whose OWN force also rests on a verified signature. This write carries no signature_symmetry_witness naming a commission_signature_verified row. Remedy: have the maintainer write a SIGNED commission directing this supersession (gpg --detach-sign --armor, then LED_ACTOR=commissioner ./led commission "<the ask>", then ./verify-commission --attest --id <that commission''s id> — VERIFIED only), then supply --signature-witness <the attestation row''s id> on this write.', NEW.supersedes, v_target_kind;
      END IF;
    END IF;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_supersession_target ON :"schema".ledger;
CREATE TRIGGER validate_supersession_target BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_supersession_target();

COMMENT ON FUNCTION :"schema".validate_supersession_target() IS
  'BEFORE INSERT trigger (s43 Element 2/R6, widened s45 §3.4, widened s53 §3.2 item 4/§3.3,
   widened s58 §2.5/Q7, widened s61 item 1, RESTORED s63 -- s61 Element 7 silently dropped the
   s53/s58 branches by citing a stale base; s63 restores them, ledger row 1430): (1) a
   write_refused row is unretractable; (2) the three standing-lifecycle kinds accept only
   SAME-KIND, IDENTITY-CONTINUOUS supersessors; (3) a belief row is superseded only by its own
   holder; (4) a missive_sent row is superseded only by a same-thread successor missive_sent
   row; (5) a missive_received row may never be superseded; (6) a missive_disposed row is
   superseded only by a same-regards re-disposition; (7) a target row whose force rests on a
   VERIFIED signature may only be superseded by a row that itself carries a valid
   signature_symmetry_witness. All seven refusals are checked in this ONE home, never a
   parallel trigger (kernel/lineage/s63-supersession-body-restoration.sql).';
-- ============================================================================================
-- USAGE (byte-diff witness, run from the repository root against a checkout that carries both
-- this file and its two sources):
--   diff <(sed -n '829,861p' kernel/lineage/s58-missive-substrate.sql) \
--        <(sed -n '/-- s53: belief supersession discipline/,/END IF;\s*$/{ /missive_disposed row (row/,/^    END IF;$/p; }' kernel/lineage/s63-supersession-body-restoration.sql)
--   -- see this build's own report for the exact diff invocation and its empty (byte-identical)
--   output; the two block extractions above are pinned to fixed line ranges precisely so the
--   diff is mechanical, not eyeballed.
-- REAL: NEVER applied to any existing world by this authoring act. The spec §5 routing question
-- is RESOLVED (row 1434, fail-safe-additive class); this delta still enters any REAL
-- deployment's birth chain only via that deployment's own future maintainer LINEAGE_CHAIN
-- integration act (runs-are-linear).
-- Run as the schema owner (bork). Idempotent (CREATE OR REPLACE FUNCTION; DROP/CREATE TRIGGER).
-- ============================================================================================
