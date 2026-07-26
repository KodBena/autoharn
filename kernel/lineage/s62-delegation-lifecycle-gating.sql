-- s62 DELEGATION-LIFECYCLE GATING (design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §1 AMENDMENT,
-- 2026-07-26, ledger row 1385 -- closing the spec-authoring defect that ledger row 1385 itself
-- found and owns). FAIL-SAFE-ADDITIVE (CLAUDE.md 2026-07-09 class rule): this delta ONLY ADDS a
-- refusal -- one new act-class branch inside an EXISTING function (entitlement_act_class_of, a
-- CREATE OR REPLACE of s60's own function, EVERY EXISTING BRANCH BYTE-PRESERVED, see the
-- diff-by-eye note at ELEMENT 1 below), one corrected remedy STRING inside another EXISTING
-- function (validate_entitlement, s60's trigger body -- teach-text only, the conjunct (a)/(b)
-- LOGIC untouched, see ELEMENT 2), zero new columns, zero new kinds, zero new CHECKs, zero new
-- triggers. Sonnet-built per the standing delegation contract, from the ratified spec amendment.
--
-- THE HOLE THIS CLOSES (row 1385, verbatim finding, owned as an authoring defect): s60's own
-- Element 7 classifies principal_registered/principal_role_bound/the three standing kinds/
-- work_closed-as-milestone/work_depends_on-as-gate-supersession/entitlement_class_configured as
-- authority-bearing, but NEVER principal_relation_asserted (the acts-for delegation kind itself)
-- -- so a principal_relation_asserted row asserting OR superseding an 'acts-for' edge sailed
-- through validate_entitlement's early return (entitlement_act_class_of returned NULL for it)
-- with ZERO gating, in EITHER direction. Consequence: conjunct (b) (kernel/lineage/
-- s60-entitlement-enforcement.sql Element 8, "the actor's authority chain must root at genesis")
-- was SELF-SERVABLE -- a principal refused on conjunct (b) for lacking a chain to genesis could
-- simply WRITE THEMSELVES an acts-for edge to any already-chained principal (nothing checked that
-- write) and retry, now holding a live chain the kernel had just told them to go build. s60's own
-- conjunct (b) refusal remedy text (Element 8's RAISE EXCEPTION) literally taught this bypass:
-- "./led principal relate <your-principal-name> acts-for <delegator-principal-name>" -- run BY
-- the refused principal, about themselves. Found by the maintainer's own question ("what about
-- revocation/suspension of authority?"), not by the kernel review's own probes (its no-chain and
-- severed-chain legs both tested REFUSAL, never tried writing a fresh edge to ESCAPE refusal).
--
-- THE FIX, EXACTLY THE SPEC AMENDMENT'S OWN SHAPE, THE SPKI PROPERTY NAMED IN THE CONSULT ("a
-- chain of grants each itself authorized"): principal_relation_asserted rows naming relation
-- 'acts-for' (fresh assertion AND supersession -- s60's OWN uniform treatment of "kind, not
-- fresh-vs-supersedes, decides the class", see e.g. principal_registered, gated identically
-- whichever way a row arrives) join the authority-bearing set as a SEVENTH act-class token,
-- 'delegation_lifecycle' -- conjunct (b) now requires the WRITER (NEW.actor, the one issuing the
-- relate/supersede act, ordinarily the DELEGATOR granting downstream authority, see ELEMENT 2's
-- corrected remedy text) to already chain-reach genesis before their write of a NEW acts-for edge
-- is accepted -- "each grant itself authorized". The self-servable loop is closed: a chainless
-- principal's own attempt to assert (or supersede) an acts-for edge is now itself an
-- authority-bearing act, refused by the SAME conjunct (b) that refused their original act,
-- because THEY do not chain-reach genesis either -- there is no longer a write available to a
-- chainless principal that manufactures the very fact conjunct (b) tests.
--
-- GENESIS BOOTSTRAPS THE FIRST EDGES EXACTLY AS s60's CONFIGURATION ROWS DO (spec amendment,
-- verbatim): a world with NO genesis principal yet trivially passes every chain check (s60
-- Element 6's own genesis exception, entirely UNCHANGED by this delta -- this file re-issues
-- NEITHER entitlement_genesis_principal NOR principal_authority_chain_reaches_genesis, both
-- byte-identical to their s60 text); once genesis exists, genesis's own chain trivially reaches
-- itself (self-loop, s60 Element 6's base case), so genesis MAY write the FIRST acts-for edge(s)
-- unaided -- exactly the same bootstrapping shape s60's own birth sequence uses for
-- entitlement_class_configured (an authority-bearing class with no possible prior configurer,
-- discharged by genesis alone at birth). bootstrap/new-project.sh's OWN birth sequence writes NO
-- principal_relation_asserted row at all (verified by inspection, this same commit's header note
-- at the scaffold edit below) -- so THIS particular gate NEVER FIRES during a scaffold's own
-- birth, the zero-friction leg holds by the birth sequence simply never reaching this act class,
-- not by any special-casing this file would otherwise owe it.
--
-- A DIVERGENCE SURFACED, NOT SILENTLY FOLDED IN (CLAUDE.md's hazard-in-reach corollary; found
-- while tracing this delta's own "does the birth order still work" question, per this delta's own
-- commission): a REAL per-deployment ceremony DOES write principal_relation_asserted/'acts-for'
-- rows outside any kernel birth sequence -- tools/setup_tui/steps_principals_authority.py's
-- "Principals & authority" section (design/AUDIT-AC-IA-POSTURE-2026-07-21.md's own witnessed
-- specimen: "the authority relation 'orchestrator acts-for maintainer' recorded"). That act's
-- OWN actor is NOT the genesis-chained scaffold principal ('author') -- tools/setup_tui/
-- principals_authority.py's relate_act() drives it as `LED_ACTOR=commissioner led principal
-- relate ...`, and 'commissioner' is registered by 'author' (s40 birth sequence step 3/4) with NO
-- acts-for edge of its own ever asserted. Under THIS delta, 'commissioner' does NOT chain-reach
-- genesis, so that EXISTING per-deployment flow, run against a world carrying this delta, would
-- now be REFUSED on conjunct (b) -- a real downstream break this delta's own kernel-side fixture
-- cannot exercise (it needs the setup TUI's own deployment surface, out of this delta's scope to
-- touch). NOT fixed here (repointing LED_ACTOR, or granting 'commissioner' a chain, is the setup
-- TUI's own commission, not a kernel-lineage act) -- named loudly for the maintainer's own
-- attention, per CLAUDE.md's "flag it loudly" branch of the hazard corollary, rather than silently
-- absorbed or silently worked around.
--
-- PREREQUISITE: this delta REQUIRES s60 (kernel/lineage/s60-entitlement-enforcement.sql) applied
-- first -- it CREATE OR REPLACEs entitlement_act_class_of and validate_entitlement in the EXACT
-- text s60 left them (verified by inspection against s60's own head text, THE HEAD-BODY RULE,
-- s45's own standing instruction, carried here verbatim as every prior PREREQUISITE precedent
-- states it). Applying this file on a pre-s60 kernel fails loudly at CREATE OR REPLACE FUNCTION
-- time -- this function's OWN body reads entitlement_class_roles/
-- principal_authority_chain_reaches_genesis/entitlement_genesis_principal, all s60 objects -- a
-- pre-s60 kernel fails loudly at CREATE TIME with "relation entitlement_class_roles does not
-- exist" / "function ... does not exist", the correct, disclosed failure mode, matching every
-- prior PREREQUISITE precedent verbatim.
--
-- FIX ROUND 1 (2026-07-26, fresh-context review BLOCKS MERGE finding, ledger row 1394,
-- SUPERSEDED IN SHAPE BY FIX ROUND 2 BELOW -- kept here as history, not deleted, because ROUND
-- 2's own header explains exactly how it subsumes this text): the ORIGINAL text of the new
-- branch classified 'delegation_lifecycle' solely off the CANDIDATE row's own principal_relation
-- = 'acts-for' -- correct for a fresh assertion, but wrong for a supersession, because s45
-- (kernel/lineage/s45-standing-lifecycle.sql lines ~135-163) deliberately does not enforce
-- value-continuity between a superseding row and its target for the s41 relation kinds. A
-- chainless, roleless third party could therefore write {kind: principal_relation_asserted,
-- principal_relation: 'dispatched-by', supersedes: <id of a live acts-for edge>} -- the
-- classifier returned NULL, validate_entitlement's early return let it through ungated, and the
-- write severed the target's delegation edge: full sabotage/DoS on the authority graph,
-- demonstrated live by the reviewer on scratch. ROUND 1's fix classified 'delegation_lifecycle'
-- on the UNION of (a) the candidate's own principal_relation = 'acts-for' (unchanged) and (b)
-- r.supersedes IS NOT NULL and the TARGET row's principal_relation = 'acts-for' (new) --
-- mirroring the sibling gate_edge_supersession branch's own target-read shape.
--
-- FIX ROUND 2 (2026-07-26, SECOND fresh-context re-review, ledger rows 1403/1403-BLOCKS-MERGE):
-- round 1's fix was ITSELF too narrow -- it special-cased ONE candidate kind
-- (principal_relation_asserted) reading ONE target relation value (acts-for). The re-review
-- witnessed live that ledger_current severs kind-AGNOSTICALLY (ANY row of ANY kind whose
-- supersedes names a live row removes it from ledger_current), while round 1's target-read lived
-- entirely inside the principal_relation_asserted branch -- so a CHAINLESS, ROLELESS saboteur
-- opens an ordinary work_opened item, then writes a work_depends_on row with supersedes = a live
-- acts-for edge's id: the work_depends_on branch (below) reads the target's edge_type (NULL on a
-- principal_relation_asserted row, never 'blocks-start') -> falls through -> RETURN NULL ->
-- ungated -> ACCEPTED -> the delegation edge is severed, same blast radius as round 1's own
-- attack, one kind over. The SAME vessel shape severs ANY gated target kind wherever the
-- CANDIDATE kind's OWN branch is conditional (or simply absent, i.e. every one of the twenty-
-- plus ordinary kinds this function never mentions at all) -- round 1's fix, being scoped to one
-- candidate kind reading one target attribute, could never have closed this: it fixed an
-- instance, not the shape.
--
-- THE ROUND-2 FIX RULE (orchestrator-authored, row 1403, verbatim): severance is an act against
-- the TARGET's class, not only the candidate's own. When r.supersedes IS NOT NULL and the TARGET
-- row's kind carries a non-NULL entitlement class, entitlement must hold for the TARGET's class
-- IN ADDITION TO any class the candidate row's own kind carries -- BOTH conjuncts, never
-- precedence or replacement (no existing gate is relaxed in any corner). Mechanically: a NEW
-- function, entitlement_act_class_of_target(t), classifies an arbitrary row t PURELY FROM ITS OWN
-- COLUMNS (kind, edge_type, principal_relation, work_slug) -- it NEVER chases t.supersedes (one
-- hop only, per the fix rule's own recursion note: "classify the target as if fresh"). This is a
-- DIFFERENT computation from entitlement_act_class_of's own candidate-side gate_edge_supersession
-- branch (which reads the CANDIDATE's supersedes-target's edge_type to decide what the CANDIDATE
-- itself is doing) -- entitlement_act_class_of_target instead asks "is THIS ROW, by its own
-- identity, an in-force member of a protected class" (e.g. a work_depends_on row IS itself a
-- live blocks-start gate the moment t.edge_type = 'blocks-start', no further indirection needed
-- to know that). validate_entitlement (Element 2 below) now computes BOTH v_act_class
-- (candidate, unchanged mechanism) and v_target_act_class (new, via entitlement_act_class_of_target
-- on the row NEW.supersedes names, when present) and requires BOTH, independently, through the
-- SAME two-conjunct predicate (factored into a new helper, entitlement_enforce_class, Element 1c
-- below, to avoid duplicating the role-lookup/chain-lookup logic for two callers).
--
-- ROUND 1'S SPECIAL CASE IS DELETED HERE, SUBSUMED, NOT KEPT BESIDE THE GENERAL RULE (verified
-- equivalence, per the round-2 commission's own instruction): round 1's branch fired when (a
-- principal_relation_asserted candidate, own relation != acts-for, supersedes IS NOT NULL, target
-- relation = acts-for) -- exactly the set of rows for which entitlement_act_class_of_target(target)
-- now independently returns 'delegation_lifecycle' (target kind principal_relation_asserted,
-- target relation = acts-for), gated through the SAME 'delegation_lifecycle' string in
-- entitlement_class_roles and the SAME seven-token authority-bearing set -- an identical
-- classification result reached by a strictly MORE GENERAL mechanism (it fires for every
-- candidate KIND, not only principal_relation_asserted). Keeping round 1's branch beside the
-- general rule would be dead-weight duplication, not extra safety (CLAUDE.md's altitude-cleanup
-- spirit: two mechanisms proving the identical fact is confusion, not redundancy-as-safety, when
-- one strictly generalizes the other with no gap between them). One DECLARE (v_target_relation)
-- from round 1 is removed with it; entitlement_act_class_of's remaining DECLARE
-- (v_target_edge_type) is untouched, preserving the byte-identity claim for the sibling
-- gate_edge_supersession branch, which this round does NOT edit.
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
-- ELEMENT 1 -- entitlement_act_class_of RE-ISSUED: BACK TO s60's OWN SHAPE PLUS ONE UNCONDITIONAL
-- BRANCH (round 1's supersedes-chasing union is GONE, subsumed by ELEMENT 1b below). Diff against
-- s60's Element 7 text (kernel/lineage/s60-entitlement-enforcement.sql lines ~495-529): every
-- IF/RETURN pair through 'work_depends_on' is copied verbatim, in the SAME order, with the SAME
-- early-return shape; the ONLY addition is the new principal_relation_asserted branch below,
-- placed LAST, testing ONLY the candidate's OWN principal_relation (no target read here anymore --
-- target-side gating is ELEMENT 1b's job, called from validate_entitlement, Element 2).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".entitlement_act_class_of(r :"schema".ledger)
    RETURNS text LANGUAGE plpgsql STABLE
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_target_edge_type text;
BEGIN
  IF r.kind = 'principal_registered' THEN
    RETURN 'principal_registered';
  END IF;
  IF r.kind = 'principal_role_bound' THEN
    RETURN 'principal_role_bound';
  END IF;
  IF r.kind IN ('principal_standing_declared', 'principal_suspended', 'principal_revoked') THEN
    RETURN 'standing_lifecycle';
  END IF;
  IF r.kind = 'entitlement_class_configured' THEN
    RETURN 'entitlement_class_configured';
  END IF;
  IF r.kind = 'work_closed' THEN
    IF EXISTS (SELECT 1 FROM work_edge_blocks_start e
               JOIN ledger_current lc ON lc.id = e.edge_row_id
               WHERE e.antecedent_slug = r.work_slug) THEN
      RETURN 'milestone_closure';
    END IF;
    RETURN NULL;
  END IF;
  IF r.kind = 'work_depends_on' AND r.supersedes IS NOT NULL THEN
    SELECT l.edge_type INTO v_target_edge_type FROM ledger l WHERE l.id = r.supersedes;
    IF v_target_edge_type = 'blocks-start' THEN
      RETURN 'gate_edge_supersession';
    END IF;
    RETURN NULL;
  END IF;
  -- s62 (kernel/lineage/s62-delegation-lifecycle-gating.sql, design/
  -- FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §1 AMENDMENT, row 1385): a principal_relation_asserted
  -- row joins 'delegation_lifecycle' when ITS OWN principal_relation = 'acts-for' -- a fresh
  -- assertion, or a same-relation supersession (a superseding row's own principal_relation is
  -- independently populated by the writer, s41 D-5). ROUND 2 (row 1403) REMOVED the target-read
  -- sub-branch round 1 added here (a candidate naming a DIFFERENT relation while superseding a
  -- live acts-for edge) -- that gap is now closed GENERALLY, for every candidate KIND, not only
  -- this one, by entitlement_act_class_of_target (Element 1b) plus validate_entitlement's own
  -- target-class enforcement (Element 2) -- see this file's own header FIX ROUND 2 note for the
  -- verified-equivalent subsumption argument.
  IF r.kind = 'principal_relation_asserted' AND r.principal_relation = 'acts-for' THEN
    RETURN 'delegation_lifecycle';
  END IF;
  RETURN NULL;
END; $fn$;

COMMENT ON FUNCTION :"schema".entitlement_act_class_of(:"schema".ledger) IS
  'kernel/lineage/s60-entitlement-enforcement.sql (base), kernel/lineage/
   s62-delegation-lifecycle-gating.sql (AMENDMENT, row 1385, round 2 row 1403): the act-class
   token a CANDIDATE ledger row belongs to by its OWN kind/attributes, or NULL if it belongs to
   none. SEVEN tokens as of s62: the six s60 tokens (principal_registered, principal_role_bound,
   standing_lifecycle, milestone_closure, gate_edge_supersession, entitlement_class_configured)
   plus delegation_lifecycle (principal_relation_asserted rows naming relation ''acts-for'').
   Does NOT, since round 2, look at what a row SUPERSEDES to decide the CANDIDATE''s own class
   beyond the pre-existing gate_edge_supersession branch -- entitlement_act_class_of_target
   (Element 1b) is the target-side twin validate_entitlement (Element 2) additionally consults.';

-- ============================================================================================
-- ELEMENT 1b -- entitlement_act_class_of_target(kind, edge_type, principal_relation, work_slug):
-- NEW (round 2, row 1403) -- classifies an arbitrary row PURELY FROM ITS OWN COLUMNS, never
-- chasing its own supersedes (one hop only from the original candidate: validate_entitlement
-- calls this ONCE, on the row NEW.supersedes names, never recursively on THAT row's own
-- supersedes target -- "classify the target as if fresh", the fix rule's own phrase). SCALAR
-- PARAMETERS, NOT a composite :"schema".ledger row (contrast entitlement_act_class_of's own `r`
-- parameter, whose composite type IS resolvable because it sits in the function SIGNATURE,
-- substituted by psql BEFORE the dollar-quoted body -- a local variable DECLARED *inside* a
-- dollar-quoted body cannot use :"schema" substitution at all, psql''s interpolation does not
-- reach inside $fn$...$fn$ text; verified empirically THIS delta''s own first scratch-witness
-- attempt with a `v_target_row :"schema".ledger;` DECLARE, which failed loudly at CREATE FUNCTION
-- time with a plain Postgres parse error, "syntax error at or near \":\""  -- caught here rather
-- than shipped, matching the s39/s60 precedent of naming an empirically-caught pitfall rather
-- than silently avoiding it with no trace). validate_entitlement (Element 2) therefore selects
-- the target row''s four relevant columns into plain scalars and passes them here, matching this
-- file''s OWN pre-existing idiom (v_target_edge_type in the gate_edge_supersession branch above
-- is exactly this pattern, one column, one scalar, no composite type ever declared locally
-- anywhere in this lineage -- grep-verified against kernel/lineage/*.sql before choosing this
-- shape). This is a DIFFERENT question from entitlement_act_class_of's own gate_edge_supersession
-- branch above (which asks "what is the CANDIDATE doing to whatever it supersedes" by reading
-- the candidate's target's edge_type) -- this function instead asks "is THIS ROW, by its own
-- identity, presently an in-force member of a protected class" (e.g. a work_depends_on row
-- simply IS a live blocks-start gate the moment its OWN edge_type column reads 'blocks-start' --
-- no further indirection needed to know that). Six branches, mirroring the six s60 tokens plus
-- delegation_lifecycle, EXCEPT work_depends_on's own shape is deliberately NOT "supersedes IS
-- NOT NULL and target reads blocks-start" (that would be a second hop) -- it is simply "IS this
-- row a blocks-start edge", read off its own edge_type column.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".entitlement_act_class_of_target(
    p_kind text, p_edge_type text, p_principal_relation text, p_work_slug text)
    RETURNS text LANGUAGE plpgsql STABLE
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
BEGIN
  IF p_kind = 'principal_registered' THEN
    RETURN 'principal_registered';
  END IF;
  IF p_kind = 'principal_role_bound' THEN
    RETURN 'principal_role_bound';
  END IF;
  IF p_kind IN ('principal_standing_declared', 'principal_suspended', 'principal_revoked') THEN
    RETURN 'standing_lifecycle';
  END IF;
  IF p_kind = 'entitlement_class_configured' THEN
    RETURN 'entitlement_class_configured';
  END IF;
  IF p_kind = 'work_closed' THEN
    IF EXISTS (SELECT 1 FROM work_edge_blocks_start e
               JOIN ledger_current lc ON lc.id = e.edge_row_id
               WHERE e.antecedent_slug = p_work_slug) THEN
      RETURN 'milestone_closure';
    END IF;
    RETURN NULL;
  END IF;
  IF p_kind = 'work_depends_on' AND p_edge_type = 'blocks-start' THEN
    RETURN 'gate_edge_supersession';
  END IF;
  IF p_kind = 'principal_relation_asserted' AND p_principal_relation = 'acts-for' THEN
    RETURN 'delegation_lifecycle';
  END IF;
  RETURN NULL;
END; $fn$;

COMMENT ON FUNCTION :"schema".entitlement_act_class_of_target(text, text, text, text) IS
  'kernel/lineage/s62-delegation-lifecycle-gating.sql (round 2, row 1403): the act-class token a
   row belongs to, judged PURELY from four of its own columns (kind, edge_type,
   principal_relation, work_slug), one hop only (its own supersedes is never chased). Called by
   validate_entitlement (Element 2) on the row NEW.supersedes names, to gate "severing a member
   of a protected class" as an act against THAT class, IN ADDITION to whatever class NEW''s own
   kind carries (entitlement_act_class_of above) -- the fix for the cross-kind supersession
   vessel (ledger_current severs kind-agnostically; classification, pre-round-2, lived only
   inside each candidate kind''s own conditional branch). Scalar parameters, not a composite row
   -- see this function''s own header for why (psql :"schema" substitution does not reach inside
   a dollar-quoted function body).';

-- ============================================================================================
-- ELEMENT 1c -- entitlement_enforce_class(actor, act_class, source): NEW (round 2, row 1403) --
-- the two-conjunct predicate FACTORED OUT of validate_entitlement so it has exactly ONE home
-- (ADR-0012 P1) and TWO callers below can share it without duplicating the role-lookup/chain-
-- lookup logic: once for the CANDIDATE's own class (v_act_class), once for the TARGET's class
-- (v_target_act_class) -- "BOTH conjuncts, never precedence or replacement" (row 1403, verbatim).
-- A no-op (RETURN, no exception) when act_class IS NULL, so both call sites can pass a possibly-
-- NULL class unconditionally with no caller-side branching. `source` is teach-text ONLY (which
-- of the two checks this is, embedded in the refusal message) -- it changes no logic.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".entitlement_enforce_class(
    p_actor bigint, p_act_class text, p_source text)
    RETURNS void LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_required_role text;
  v_has_role boolean;
  v_authority_bearing boolean;
  v_reaches boolean;
BEGIN
  IF p_act_class IS NULL THEN
    RETURN;
  END IF;

  -- CONJUNCT (a): an in-force role binding naming the configured role for this act class, IF
  -- one is configured (entitlement_class_roles, s60 Element 4). Logic byte-identical to s60's
  -- own text (moved here from validate_entitlement, unedited beyond the parameter names) --
  -- delegation_lifecycle is NOT in the default conjunct-(a) map (Element 3's own note explains
  -- why), so this block reads unconfigured/vacuous for it by default, exactly as s60's own
  -- attention-point-1 policy already permits for any unconfigured class.
  SELECT role_name INTO v_required_role FROM entitlement_class_roles WHERE act_class = p_act_class;
  IF v_required_role IS NOT NULL THEN
    SELECT EXISTS (SELECT 1 FROM principal_role_bindings prb
                   WHERE prb.subject = p_actor AND prb.role_name = v_required_role)
      INTO v_has_role;
    IF NOT v_has_role THEN
      RAISE EXCEPTION 'Ledger policy: entitlement refused (s60/s62/round-2 row 1403, factored acceptance predicate conjunct a, %) — act class ''%'' requires an in-force role binding named ''%'' (this world''s configured entitlement map, see entitlement_class_roles); actor % holds no such binding. Remedy: a principal who ALREADY holds the ''%'' role (or genesis-chain authority) binds it to you: ./led principal bind-role <your-principal-name> "%" (kernel/lineage/s41-principal-bindings-and-relations.sql), then retry this act. See design/USER-RECIPES-FAQ.md''s entitlement-enforcement recipe for the worked example (kernel/lineage/s60-entitlement-enforcement.sql).', p_source, p_act_class, v_required_role, p_actor, v_required_role, v_required_role;
    END IF;
  END IF;

  -- CONJUNCT (b): for the authority-bearing act set -- SEVEN tokens as of s62 -- the actor's
  -- authority chain must root at genesis -- UNCONDITIONAL, never configuration-gated, logic
  -- byte-identical to s60's own text (moved here from validate_entitlement, unedited beyond the
  -- parameter names).
  v_authority_bearing := p_act_class IN (
      'principal_registered', 'principal_role_bound', 'standing_lifecycle',
      'milestone_closure', 'gate_edge_supersession', 'entitlement_class_configured',
      'delegation_lifecycle');
  IF v_authority_bearing THEN
    SELECT principal_authority_chain_reaches_genesis(p_actor) INTO v_reaches;
    IF NOT v_reaches THEN
      RAISE EXCEPTION 'Ledger policy: entitlement refused (s60/s62/round-2 row 1403, factored acceptance predicate conjunct b, %) — act class ''%'' is authority-bearing (design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §1.1b, delegation_lifecycle per the 2026-07-26 amendment, row 1385; the TARGET-class conjunct per row 1403''s round-2 fix rule -- "severance is an act against the TARGET''s class"); actor %''s authority chain (transitive reachability over in-force acts-for relations, kernel/lineage/s41-principal-bindings-and-relations.sql) does not reach this world''s genesis principal. Remedy: this is NOT a write you can perform on yourself — have your DELEGATOR run, on your behalf: ./autoharn led principal relate <delegator-principal-name> acts-for <a-principal-already-chain-connected-to-genesis>, covering you (i.e. the delegator asserts/extends the chain; a refused principal asserting their OWN acts-for edge is the exact self-service bypass s62 closes, kernel/lineage/s62-delegation-lifecycle-gating.sql, row 1385) — or have a severed link repaired (suspension/revocation severs a chain PROSPECTIVELY only; past accepted acts through that link stay credited, kernel/lineage/s45-standing-lifecycle.sql''s I5 asymmetry).', p_source, p_act_class, p_actor;
    END IF;
  END IF;
END; $fn$;

COMMENT ON FUNCTION :"schema".entitlement_enforce_class(bigint, text, text) IS
  'kernel/lineage/s62-delegation-lifecycle-gating.sql (round 2, row 1403): the two-conjunct
   acceptance predicate, factored out of validate_entitlement to serve TWO call sites (candidate
   class, target class) with one shared implementation, ADR-0012 P1. A no-op when act_class IS
   NULL. `source` is teach-text only, embedded in the refusal message to say WHICH class failed
   (this row''s own act class, or the class of the row it supersedes).';

-- ============================================================================================
-- ELEMENT 2 -- validate_entitlement RE-ISSUED (round 2, row 1403): NOW COMPUTES TWO CLASSES AND
-- ENFORCES BOTH. v_act_class is UNCHANGED (entitlement_act_class_of(NEW), the candidate's own
-- class). v_target_act_class is NEW: when NEW.supersedes IS NOT NULL, the target row is read
-- ONCE (raw `ledger`, by id -- the same "row-addressed, HISTORY-typed" read shape
-- validate_supersession_target itself already uses) and classified by
-- entitlement_act_class_of_target (Element 1b, one hop, no further chase). BOTH classes are then
-- run through entitlement_enforce_class (Element 1c) -- "BOTH conjuncts, never precedence or
-- replacement" (row 1403): a write with an entitled candidate class but an UNENTITLED target
-- class is STILL refused (the fix closes not only the "candidate falls through to NULL" vessel
-- the reviewer witnessed live, but also the narrower "candidate class differs from target class
-- under a deployment that configures DIFFERENT conjunct-(a) roles per class" case -- see this
-- file's own vessel-audit note in LIMITS). When both classes are NULL, the trigger no-ops exactly
-- as before (early RETURN, no role/chain lookups at all -- the zero-friction leg for the
-- overwhelming majority of ordinary writes is unchanged).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_entitlement() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_act_class text;
  v_target_kind text;
  v_target_edge_type text;
  v_target_relation text;
  v_target_work_slug text;
  v_target_act_class text;
BEGIN
  v_act_class := entitlement_act_class_of(NEW);

  v_target_act_class := NULL;
  IF NEW.supersedes IS NOT NULL THEN
    SELECT l.kind, l.edge_type, l.principal_relation, l.work_slug
      INTO v_target_kind, v_target_edge_type, v_target_relation, v_target_work_slug
      FROM ledger l WHERE l.id = NEW.supersedes;
    IF FOUND THEN
      v_target_act_class := entitlement_act_class_of_target(
          v_target_kind, v_target_edge_type, v_target_relation, v_target_work_slug);
    END IF;
  END IF;

  IF v_act_class IS NULL AND v_target_act_class IS NULL THEN
    RETURN NEW;
  END IF;

  PERFORM entitlement_enforce_class(NEW.actor, v_act_class, 'this row''s own act class');
  PERFORM entitlement_enforce_class(
      NEW.actor, v_target_act_class,
      format('the class of row %s, which this write supersedes', NEW.supersedes));

  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_entitlement ON :"schema".ledger;
CREATE TRIGGER validate_entitlement BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_entitlement();

COMMENT ON FUNCTION :"schema".validate_entitlement() IS
  'kernel/lineage/s60-entitlement-enforcement.sql (base), kernel/lineage/
   s62-delegation-lifecycle-gating.sql (AMENDMENT, row 1385; round 2, row 1403): the factored
   acceptance predicate (entitlement_enforce_class, Element 1c), applied TWICE -- once to the
   CANDIDATE row''s own act class (entitlement_act_class_of), once to the act class of the row
   it SUPERSEDES, if any (entitlement_act_class_of_target, Element 1b) -- "severance is an act
   against the target''s class" (row 1403). Fires (does real work) only when at least one of the
   two classes is non-NULL; a no-op for every ordinary kind whose row neither carries nor
   supersedes a protected class. Refusals journal as write_refused rows via the s43 boundary,
   unchanged.';

-- ============================================================================================
-- ELEMENT 3 -- NO BIRTH-SEQUENCE ACT OF THIS FILE'S OWN (contrast s60's own Element 9/§1.3):
-- unlike s60's five default-mapped conjunct-(a) classes, delegation_lifecycle is deliberately
-- left OUT of the default entitlement_class_roles map (conjunct (a) stays vacuous for it by
-- default -- ONLY conjunct (b), unconditional, gates it) -- there is no fresh
-- entitlement_class_configured row for this delta to add at birth. bootstrap/new-project.sh's
-- own scaffold birth sequence writes NO principal_relation_asserted row at all (verified by
-- inspection this same commit: the s40/s43/s60 birth sequence registers author/reviewer/
-- commissioner/write-boundary and binds/configures roles, never an acts-for relation) -- so this
-- delta needs no scaffold edit, and the zero-friction leg holds by this act class simply never
-- being reached during any scaffold's own birth, not by any special-casing. The maintainer's
-- OWN per-deployment "Principals & authority" ceremony (tools/setup_tui/
-- steps_principals_authority.py, which DOES write such rows, e.g. "orchestrator acts-for
-- maintainer") is a SEPARATE, later, operator-driven surface outside any kernel birth chain --
-- this file's own header names the exact hazard that ceremony now runs into under this delta
-- (its 'commissioner' actor does not chain-reach genesis), surfaced rather than silently
-- absorbed, fix deliberately left to that surface's own future commission.
-- ============================================================================================

-- ============================================================================================
-- HISTORY: safe -- per-mechanism grounds:
--   * entitlement_act_class_of re-issued: ROUND 1's supersedes-chasing union sub-branch is
--     REMOVED (subsumed, see FIX ROUND 2 header note); every OTHER branch (through the
--     principal_relation_asserted own-relation check) is byte-identical to s60's/round-1's head
--     text -- no pre-existing branch's reachability or output changed for any row that was
--     ALREADY classified before round 2; the ONE row-shape that changes classification RESULT
--     from round 1 to round 2 (a principal_relation_asserted candidate naming a non-acts-for
--     relation while superseding a live acts-for edge) still ends up GATED, just via the
--     target-side check (Element 1b/2) rather than this function's own former union branch --
--     net refusal coverage for that specific row shape is UNCHANGED, not widened or narrowed.
--   * entitlement_act_class_of_target (Element 1b) and entitlement_enforce_class (Element 1c)
--     are BRAND NEW functions with no pre-existing reader -- pure additions.
--   * validate_entitlement re-issued: conjunct (a) and conjunct (b) TEST LOGIC (now living in
--     entitlement_enforce_class) is byte-identical to round 1's own text, moved not edited,
--     parameterized over `p_actor`/`p_act_class` instead of `NEW.actor`/`v_act_class` (mechanical
--     rename for reuse, no semantic change) -- STILL the SAME seven-token authority-bearing SET,
--     STILL the SAME entitlement_class_roles read. What is NEW is that validate_entitlement now
--     CALLS this identical predicate TWICE per write (candidate class, then target class) instead
--     of once -- a widened refusal (MORE writes now require passing the check: a write refused
--     before round 2 is STILL refused after it, by the identical test, for its own class; a write
--     that ALSO now fails on its TARGET's class is a NEWLY refused write, never a newly ACCEPTED
--     one -- no write accepted under round 1 becomes MORE PERMISSIVELY accepted under round 2).
--   * validate_entitlement's TRIGGER itself is DROP/CREATE of the SAME member at the SAME
--     alphabetical position (s60 Element 8's own ordering note, unchanged) -- not a new trigger,
--     a re-issue of an existing one, matching s45/s53's own re-issue precedent for a live
--     trigger BODY -- still the s45/s53 "re-issue an EXISTING trigger body, new-refusal-only"
--     shape, inside the class-ratified fail-safe family because the delta ONLY WIDENS which rows
--     the SAME unconditional-conjunct-(b)/configurable-conjunct-(a) checks reach, never loosens
--     any existing CHECK/trigger outcome.
--   * zero new columns, zero new kinds, zero new CHECK constraints, zero re-issues of
--     compute_row_hash/ledger_current/countersigned_in_force/entitlement_class_roles/
--     entitlement_genesis_principal/principal_authority_chain_reaches_genesis (all byte-identical
--     to their s60 head text, untouched by this file, both rounds).
--
-- VESSEL AUDIT (round 2, row 1403's own commission -- every kind entitlement_act_class_of OR
-- entitlement_act_class_of_target can name as a GATED CLASS, cross-checked against
-- validate_supersession_target's OWN kind-continuity restrictions, which independently protect
-- three families regardless of entitlement):
--   * principal_registered   -- SEVERABLE PRE-FIX (any of the ~20 kinds entitlement never
--     classifies at all -- e.g. work_opened, commission, note, assumption, decision -- could
--     supersede a live principal_registered row with zero gating; validate_supersession_target
--     places NO kind restriction on this target). GATED POST-FIX (target-class check).
--   * principal_role_bound   -- SEVERABLE PRE-FIX (the SECOND round-2 witnessed attack,
--     RED-CROSS-KIND-ROLE-BINDING below, via an unclassified work_depends_on candidate).
--     GATED POST-FIX.
--   * entitlement_class_configured -- SEVERABLE PRE-FIX (an unclassified candidate superseding
--     the GOVERNING configuration row for a class would make entitlement_class_roles read that
--     class as UNCONFIGURED again -- vacuous conjunct (a) -- "quietly unbolting the gate that
--     decides who may reconfigure the gates"). GATED POST-FIX.
--   * standing_lifecycle (principal_standing_declared/suspended/revoked) -- NOT SEVERABLE
--     PRE-FIX, independently of entitlement: validate_supersession_target (s45 §3.4) refuses
--     any supersession whose OWN kind differs from the target's kind for these three, so the
--     ONLY candidate that could ever reach this target is the SAME kind, which
--     entitlement_act_class_of ALREADY classified unconditionally as standing_lifecycle before
--     round 2 -- candidate class and target class always coincide here. GATED POST-FIX
--     (redundant with the pre-existing candidate-side check, not a behavior change).
--   * milestone_closure (work_closed, target itself qualifying as a milestone) -- SEVERABLE
--     PRE-FIX (an unclassified candidate, e.g. a fresh 'note' row, superseding a live
--     milestone-closing work_closed row -- entitlement_act_class_of's OWN work_closed branch
--     never reads r.supersedes at all, only r.work_slug, so it could not have caught this even
--     for a work_closed CANDIDATE). GATED POST-FIX.
--   * gate_edge_supersession (work_depends_on, target itself a live blocks-start edge) --
--     SEVERABLE PRE-FIX for any candidate KIND OTHER than work_depends_on (the work_depends_on
--     -on-work_depends_on case was ALREADY gated since s60 -- that is the pre-existing
--     candidate-side branch this round does not edit; a DIFFERENT candidate kind reaching the
--     same target was the uncovered case). GATED POST-FIX (general target check, kind-agnostic).
--   * delegation_lifecycle (principal_relation_asserted, relation acts-for) -- THE HEADLINE,
--     SEVERABLE PRE-FIX both via a principal_relation_asserted candidate naming a different
--     relation (round 1's own fix, now via the general mechanism) AND via any OTHER unclassified
--     candidate kind (the round-2 reviewer's own witnessed attack, work_depends_on). GATED
--     POST-FIX (both shapes, one mechanism).
--   * belief / missive_sent / missive_received / missive_disposed / write_refused -- NOT
--     SEVERABLE, and NOT part of entitlement's classified vocabulary at all (never authority-
--     bearing) -- protected, where protected, entirely by validate_supersession_target's OWN
--     same-kind/same-actor/unretractable rules (s53/s58/s43), a disjoint mechanism this delta
--     does not touch and does not need to.
--   RESIDUAL (narrower, disclosed in LIMITS below, NOT closed by round 1, CLOSED by round 2):
--   a candidate kind whose OWN class is non-NULL (so round 1's "candidate falls through to NULL"
--   framing does not name it) could still under-gate a supersession if a deployment configures
--   DIFFERENT conjunct-(a) roles for the candidate's class and the target's class -- e.g. an
--   actor holding the role principal_registered requires, chain-connected, writes a
--   principal_registered row that ALSO supersedes a live principal_role_bound row, without ever
--   holding whatever role principal_role_bound's own conjunct (a) requires. Round 2's
--   BOTH-conjuncts rule closes this too, since it enforces the target's class independently of
--   whether the candidate's own class already passed.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form):
--   - INVARIANT (round 2, row 1403): a write is accepted only when BOTH (a) its own act class
--     (if any) passes the factored predicate for THAT class, AND (b) the act class of the row it
--     supersedes (if any, and if that row's kind carries a non-NULL entitlement class) ALSO
--     passes the SAME predicate for THAT class -- "severance is an act against the target's
--     class" (row 1403, verbatim). Both conjuncts, never precedence or replacement -- no
--     pre-existing refusal is relaxed in any corner (the VESSEL AUDIT above enumerates every
--     kind this applies to).
--   - QUANTIFICATION UNIVERSE: ACT CLASSES gated by conjunct (b): still exactly SEVEN tokens
--     (unchanged from round 1's own head -- delegation_lifecycle joined the pre-existing six at
--     round 1; round 2 adds NO eighth token, only a SECOND application site of the identical
--     seven-token set) -- enumerated once, inside entitlement_enforce_class (Element 1c), never
--     a second copy, called from validate_entitlement's two sites. ACT CLASSES gated by
--     conjunct (a): unchanged POLICY set (whichever tokens entitlement_class_roles currently
--     governs); delegation_lifecycle still NOT in the default map (Element 3, untouched).
--     KINDS/COLUMNS: zero touched (this round reads the SAME columns round 1 already read --
--     kind, edge_type, principal_relation, work_slug, supersedes -- adding no column and no
--     CHECK). VIEWS: zero touched. FUNCTIONS: entitlement_act_class_of RE-ISSUED (one branch
--     removed, net-equivalent coverage per the VESSEL AUDIT); validate_entitlement RE-ISSUED
--     (predicate logic factored out, not changed); TWO NEW functions
--     (entitlement_act_class_of_target, entitlement_enforce_class) -- five function objects
--     total touched by this file across both rounds, zero of s60's OWN five untouched functions
--     (entitlement_class_roles, entitlement_genesis_principal,
--     principal_authority_chain_reaches_genesis, compute_row_hash, ledger_current/
--     countersigned_in_force) re-issued a second time. TRIGGERS: ONE re-issued (validate_
--     entitlement's own trigger, DROP/CREATE of the SAME member, same position) -- no new
--     trigger. ENGINE: the ASP twin (engine/lp/ledger_entitlement.lp) STILL needs NO new
--     predicate and STILL carries no act-class classification of its own -- STATED, not skipped
--     (row 1403's own commission asked this be re-confirmed, not assumed): reaches_genesis/1
--     derives reachability from in_force/1 acts-for edges alone, generic over every act class
--     that gates via chain-to-genesis by construction; it has never computed, and does not need
--     to compute, WHICH writes were refused -- that is SQL-side, write-time, trigger-enforced
--     machinery this delta's own round-1 CLOSURE STATEMENT already named as outside AGREE's
--     scope, a scoping this round does not revisit or weaken. ./judge holds AGREE on this
--     delta's fixture (seen-red/s62-delegation-lifecycle-gating/) on the SAME
--     chain-derivation-consistency-only footing round 1's own CLOSURE STATEMENT already
--     disclosed (verbatim, unchanged by this round): AGREE proves the SQL function
--     (principal_authority_chain_reaches_genesis) and the ASP closure (reaches_genesis/1) compute
--     the IDENTICAL reachable set from the SAME in-force acts-for edges on the post-mutation
--     snapshot; it says nothing about write-time refusal, which is what the RED/GREEN fixtures
--     (including this round's own RED-CROSS-KIND-WORK-DEPENDS-ON / RED-CROSS-KIND-ROLE-BINDING)
--     prove, complementary to AGREE, never redundant with it.
--   - DENOMINATION: unchanged from s60/round-1 -- entitlement in in-force EVENTS, computed
--     fresh, never cached; act-class identity in the SAME kernel-computed string vocabulary,
--     still seven members; no bound is a bare round literal.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): CLASS-RATIFIED FAIL-SAFE
-- shape, round 2 as much as round 1 -- this round only WIDENS an existing predicate's reach (the
-- SAME seven-token, two-conjunct check, applied to a SECOND row -- the supersession target --
-- when one is named) and factors existing logic into a shared helper; nothing existing is
-- relaxed, no existing CHECK narrowed, no existing grant revoked, no existing accepted-write
-- class newly refused (the VESSEL AUDIT above and the HISTORY section's own per-mechanism
-- grounds both confirm no previously-accepted write becomes newly accepted, only the reverse).
-- Riding the 2026-07-09 class rule, not routed for a separate maintainer ratification question --
-- stated here for the record, matching s60's own disclosure convention.
--
-- LIMITS (pre-registered, round 2 supersedes round 1's own LIMITS list where they overlap):
--   - delegation_lifecycle is NOT in the default conjunct-(a) role map (Element 3) -- a
--     deployment wanting a role requirement on delegation acts, not merely a chain requirement,
--     configures it explicitly via a fresh (chain-gated) entitlement_class_configured row.
--   - No construction-time cycle refusal for acts-for relations (s60's own pre-registered
--     limit, unchanged by this delta) -- a delegation cycle that never reaches genesis is
--     fail-safe (every act through it, including further delegation acts, refused), never a
--     bypass.
--   - The setup TUI's per-deployment "Principals & authority" ceremony hazard (this file's own
--     header) is NAMED, not fixed, here -- out of this kernel-lineage delta's own scope.
--   - Trigger/CHECK refusals bind the granted role's ordinary INSERT path only; the schema-
--     owner/superuser bypass stands (the standing s26..s60 disclosed bound).
--   - entitlement_act_class_of_target reads ONE hop only (the row NEW.supersedes directly names)
--     -- it deliberately does NOT chase that row's OWN supersedes chain. A row whose PROTECTED
--     status is only reachable two-or-more supersession hops away from the write under
--     evaluation is NOT found by this mechanism -- named as a limit, not silently assumed
--     sufficient: ledger_current's own kind-agnostic severance rule only ever looks at the ONE
--     row a given write directly names in `supersedes`, never a transitive chain of them, so a
--     single hop is the mechanism's own natural unit and this function matches it exactly; no
--     row in this project's current kind vocabulary is known to need a second hop, but the
--     limit is named rather than left implicit.
--   - The narrower "candidate class passes, target class under a DIFFERENT configured role
--     requirement does not" scenario (VESSEL AUDIT's own RESIDUAL note above) is CLOSED by this
--     round's both-conjuncts rule but was never separately fixture-witnessed as its OWN red leg
--     (this round's two new red legs both use a CHAINLESS, ROLELESS attacker, which already
--     fails conjunct (a) or (b) on EITHER class alone -- the narrower "has SOME role, wrong
--     one" shape is logically covered by the same code path but not independently exercised;
--     UNEXERCISED, not UNWITNESSED-and-assumed-fine -- the underlying mechanism, both conjuncts
--     evaluated independently per class, is exercised by every other leg in this file).
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s60):
--   VALIDATE (reachable throwaway): apply the FULL s15..s60 chain (see kernel/lineage/
--   s60-entitlement-enforcement.sql's own VALIDATE block for the complete -f list), THEN
--   -f s62-delegation-lifecycle-gating.sql (genesis seed per s26; register the write-boundary
--   principal and discharge the s40/s43/s60 birth sequence BEFORE exercising any delegation
--   act, exactly as s60's own VALIDATE note requires).
--   REAL: NEVER applied to any existing world by this authoring act (runs-are-strictly-linear,
--   2026-07-11). Enters a FUTURE world's birth chain via bootstrap/new-project.sh's
--   LINEAGE_CHAIN at the maintainer's own future integration act, alongside s58/s59/s60
--   (currently unwired there too, s60's own PREREQUISITE section names the gap). Authored and
--   scratch-witnessed on scratch schema pairs in the TOY db only.
-- Run as the schema owner (bork). Idempotent (CREATE OR REPLACE FUNCTION; DROP/CREATE TRIGGER).
-- ============================================================================================
