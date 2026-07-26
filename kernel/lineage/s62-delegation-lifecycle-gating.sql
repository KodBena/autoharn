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
-- ELEMENT 1 -- entitlement_act_class_of RE-ISSUED: ONE NEW BRANCH, EVERY EXISTING BRANCH
-- BYTE-PRESERVED. Diff against s60's Element 7 text (kernel/lineage/s60-entitlement-enforcement.sql
-- lines ~495-529): every IF/RETURN pair through 'work_depends_on' is copied verbatim, in the SAME
-- order, with the SAME early-return shape; the ONLY addition is the new branch below, placed
-- LAST (after the existing work_depends_on/gate_edge_supersession check, before the final
-- fall-through RETURN NULL) -- an ordering choice that touches no earlier branch's own
-- reachability (every earlier branch still RETURNs before control could ever reach this one; this
-- branch's own IF is the new final guard ahead of the pre-existing terminal 'RETURN NULL').
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
  -- FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §1 AMENDMENT, row 1385): principal_relation_asserted
  -- rows naming relation 'acts-for' -- FRESH OR SUPERSEDING, kind alone decides the class,
  -- s60's own precedent for every other branch above (fresh-vs-supersedes never distinguished by
  -- entitlement_act_class_of anywhere in this function; conjunct (b) below is what tells the two
  -- cases apart via the ACTOR's chain, not this classifier). r.principal_relation is the s41 D-5
  -- column already carrying the free-text relation token (principal_relations' own source
  -- column) -- read directly off NEW/candidate r, never a second lookup.
  IF r.kind = 'principal_relation_asserted' AND r.principal_relation = 'acts-for' THEN
    RETURN 'delegation_lifecycle';
  END IF;
  RETURN NULL;
END; $fn$;

COMMENT ON FUNCTION :"schema".entitlement_act_class_of(:"schema".ledger) IS
  'kernel/lineage/s60-entitlement-enforcement.sql (base), kernel/lineage/
   s62-delegation-lifecycle-gating.sql (AMENDMENT, row 1385): the act-class token a candidate
   ledger row belongs to, or NULL if it belongs to none. SEVEN tokens as of s62: the six s60
   tokens (principal_registered, principal_role_bound, standing_lifecycle, milestone_closure,
   gate_edge_supersession, entitlement_class_configured) plus delegation_lifecycle
   (principal_relation_asserted rows naming relation ''acts-for'', fresh or superseding) --
   validate_entitlement (Element 2 below) is the ONE caller.';

-- ============================================================================================
-- ELEMENT 2 -- validate_entitlement RE-ISSUED: THE AUTHORITY-BEARING SET WIDENED BY ONE TOKEN
-- (conjunct (b) LOGIC untouched -- same chain-reaches-genesis test, same early-return shape,
-- same conjunct (a) block byte-preserved verbatim) PLUS THE CONJUNCT-(b) REMEDY TEXT CORRECTED
-- (row 1385's second half): s60's own remedy told the REFUSED principal to relate THEMSELVES to
-- a delegator ("./led principal relate <your-principal-name> acts-for <delegator-principal-name>"
-- -- a self-asserted edge, the exact bypass this delta's own header explains). The corrected text
-- names the DELEGATOR as the one who must run the command, covering the refused principal --
-- consistent with, and now MECHANICALLY enforced by, this same file's Element 1 addition (a
-- self-asserted edge from the refused principal is now ITSELF refused on this same conjunct,
-- since the refused principal's own actor-chain does not reach genesis either). Conjunct (a)'s
-- own text (the role-binding remedy) is UNCHANGED -- row 1385 names only the conjunct (b)
-- delegation remedy as taught-the-bypass; conjunct (a)'s remedy ("a principal who ALREADY holds
-- the role... binds it to you") was never self-servable (binding a role to yourself requires
-- ALREADY holding a role that can bind roles, s41's own principal_role_bound act -- itself
-- authority-bearing since s60 birth, so a chainless/roleless principal could not use IT to
-- escape either; row 1385 names no defect in conjunct (a)'s text).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_entitlement() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_act_class text;
  v_required_role text;
  v_has_role boolean;
  v_authority_bearing boolean;
  v_reaches boolean;
BEGIN
  v_act_class := entitlement_act_class_of(NEW);
  IF v_act_class IS NULL THEN
    RETURN NEW;
  END IF;

  -- CONJUNCT (a): an in-force role binding naming the configured role for this act class, IF
  -- one is configured (entitlement_class_roles, s60 Element 4). Byte-identical to s60's own
  -- text -- delegation_lifecycle is NOT in the default conjunct-(a) map (this file's own
  -- Element 3 birth-sequence note explains why), so this block reads unconfigured/vacuous for
  -- it by default, exactly as s60's own attention-point-1 policy already permits for any
  -- unconfigured class -- a deployment MAY configure it later by writing a fresh
  -- entitlement_class_configured row, itself authority-bearing and therefore chain-gated.
  SELECT role_name INTO v_required_role FROM entitlement_class_roles WHERE act_class = v_act_class;
  IF v_required_role IS NOT NULL THEN
    SELECT EXISTS (SELECT 1 FROM principal_role_bindings prb
                   WHERE prb.subject = NEW.actor AND prb.role_name = v_required_role)
      INTO v_has_role;
    IF NOT v_has_role THEN
      RAISE EXCEPTION 'Ledger policy: entitlement refused (s60, factored acceptance predicate conjunct a) — act class ''%'' requires an in-force role binding named ''%'' (this world''s configured entitlement map, see entitlement_class_roles); actor % holds no such binding. Remedy: a principal who ALREADY holds the ''%'' role (or genesis-chain authority) binds it to you: ./led principal bind-role <your-principal-name> "%" (kernel/lineage/s41-principal-bindings-and-relations.sql), then retry this act. See design/USER-RECIPES-FAQ.md''s entitlement-enforcement recipe for the worked example (kernel/lineage/s60-entitlement-enforcement.sql).', v_act_class, v_required_role, NEW.actor, v_required_role, v_required_role;
    END IF;
  END IF;

  -- CONJUNCT (b): for the authority-bearing act set -- SEVEN tokens as of s62 (this file's own
  -- Element 1 adds 'delegation_lifecycle') -- the actor's authority chain must root at genesis --
  -- UNCONDITIONAL, never configuration-gated, byte-identical logic to s60's own text; only the
  -- SET LITERAL and the REMEDY STRING below change.
  v_authority_bearing := v_act_class IN (
      'principal_registered', 'principal_role_bound', 'standing_lifecycle',
      'milestone_closure', 'gate_edge_supersession', 'entitlement_class_configured',
      'delegation_lifecycle');
  IF v_authority_bearing THEN
    SELECT principal_authority_chain_reaches_genesis(NEW.actor) INTO v_reaches;
    IF NOT v_reaches THEN
      RAISE EXCEPTION 'Ledger policy: entitlement refused (s60/s62, factored acceptance predicate conjunct b) — act class ''%'' is authority-bearing (design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §1.1b, delegation_lifecycle per the 2026-07-26 amendment, row 1385); actor %''s authority chain (transitive reachability over in-force acts-for relations, kernel/lineage/s41-principal-bindings-and-relations.sql) does not reach this world''s genesis principal. Remedy: this is NOT a write you can perform on yourself — have your DELEGATOR run, on your behalf: ./autoharn led principal relate <delegator-principal-name> acts-for <a-principal-already-chain-connected-to-genesis>, covering you (i.e. the delegator asserts/extends the chain; a refused principal asserting their OWN acts-for edge is the exact self-service bypass s62 closes, kernel/lineage/s62-delegation-lifecycle-gating.sql, row 1385) — or have a severed link repaired (suspension/revocation severs a chain PROSPECTIVELY only; past accepted acts through that link stay credited, kernel/lineage/s45-standing-lifecycle.sql''s I5 asymmetry).', v_act_class, NEW.actor;
    END IF;
  END IF;

  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_entitlement ON :"schema".ledger;
CREATE TRIGGER validate_entitlement BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_entitlement();

COMMENT ON FUNCTION :"schema".validate_entitlement() IS
  'kernel/lineage/s60-entitlement-enforcement.sql (base), kernel/lineage/
   s62-delegation-lifecycle-gating.sql (AMENDMENT, row 1385): the factored acceptance predicate,
   conjunct (a) role-gate unchanged, conjunct (b) authority-chain-to-genesis now over SEVEN
   authority-bearing tokens (+delegation_lifecycle) with a corrected remedy string naming the
   DELEGATOR as the one who must write a new acts-for edge, never the refused principal
   themselves. Fires only when entitlement_act_class_of(NEW) is non-NULL; a no-op for every
   ordinary kind. Refusals journal as write_refused rows via the s43 boundary, unchanged.';

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
--   * entitlement_act_class_of re-issued with ONE new terminal branch appended after every
--     pre-existing branch's own early return -- no pre-existing branch's reachability or output
--     changed (byte-diff of every line through the pre-existing 'work_depends_on' check against
--     s60's own head text: identical).
--   * validate_entitlement re-issued: conjunct (a) block byte-identical; conjunct (b)'s test
--     (principal_authority_chain_reaches_genesis) byte-identical; only the SET LITERAL (+1
--     token) and the RAISE EXCEPTION remedy STRING changed -- a widened refusal (MORE writes now
--     require the chain check) plus a corrected teach-text, never a narrowed or relaxed check on
--     any of the six pre-existing tokens (a principal_registered/principal_role_bound/standing_
--     lifecycle/milestone_closure/gate_edge_supersession/entitlement_class_configured write that
--     was refused before this delta is STILL refused, by the identical test, after it; one that
--     was accepted before is still accepted, since neither the chain function nor conjunct (a)
--     changed for those six tokens).
--   * validate_entitlement's TRIGGER itself is DROP/CREATE of the SAME member at the SAME
--     alphabetical position (s60 Element 8's own ordering note, unchanged) -- not a new trigger,
--     a re-issue of an existing one, matching s45/s53's own re-issue precedent for a live
--     trigger BODY (contrast the fail-safe-additive-eligible s34/s36/s47/s52 shape, which never
--     re-issue a body) -- NAMED explicitly: this delta is NOT the narrower "one new trigger
--     member, zero body re-issues" shape s60 itself carried; it is the s45/s53 "re-issue an
--     EXISTING trigger body, new-refusal-only" shape, still inside the class-ratified fail-safe
--     family because the delta ONLY WIDENS which rows the SAME unconditional-conjunct-(b) check
--     reaches and corrects a STRING, never loosens any existing CHECK/trigger outcome.
--   * zero new columns, zero new kinds, zero new CHECK constraints, zero re-issues of
--     compute_row_hash/ledger_current/countersigned_in_force/entitlement_class_roles/
--     entitlement_genesis_principal/principal_authority_chain_reaches_genesis (all byte-identical
--     to their s60 head text, untouched by this file).
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form):
--   - INVARIANT: a principal_relation_asserted row naming relation 'acts-for' (fresh or
--     superseding) is accepted only when its writing actor's authority chain, transitive over
--     in-force acts-for relations, roots at the world's genesis principal, evaluated fresh at
--     act time -- identical machinery to the six pre-existing s60 authority-bearing classes, no
--     new mechanism, one new classified token.
--   - QUANTIFICATION UNIVERSE: ACT CLASSES gated by conjunct (b): exactly SEVEN tokens now
--     (s60's six, unchanged, PLUS delegation_lifecycle) -- enumerated once, inside
--     validate_entitlement, never a second copy. Every other kind remains untouched --
--     entitlement_act_class_of returns NULL for all of them. ACT CLASSES gated by conjunct (a):
--     unchanged POLICY set (whichever tokens entitlement_class_roles currently governs);
--     delegation_lifecycle is NOT added to the default map by this delta (Element 3).
--     KINDS/COLUMNS: zero touched (this delta reads r.principal_relation, an EXISTING s41
--     column, and r.kind, adding no column and no CHECK). VIEWS: zero touched. FUNCTIONS: TWO
--     re-issued (entitlement_act_class_of, validate_entitlement), both listed above; zero new
--     functions. TRIGGERS: ONE re-issued (validate_entitlement's own trigger, DROP/CREATE of
--     the SAME member, same position) -- no new trigger. ENGINE: the ASP twin
--     (engine/lp/ledger_entitlement.lp) needs NO new predicate -- reaches_genesis/1 is already
--     generic over EVERY act class that gates via chain-to-genesis, delegation_lifecycle
--     included, by construction (it was never act-class-specific); this delta's own header note
--     there, and in engine/ledger_edb.py's export_entitlement() docstring, records the s62
--     extension for the record. ./judge holds AGREE on this delta's fixture
--     (seen-red/s62-delegation-lifecycle-gating/), including on the attack scenario itself (a
--     refused principal's self-asserted edge is never written, so it never enters either side's
--     EDB -- AGREE is a statement about the CHAIN the exporter reads, unaffected by which writes
--     the trigger refused before they became rows).
--   - DENOMINATION: unchanged from s60 -- entitlement in in-force EVENTS, computed fresh, never
--     cached; act-class identity in the SAME kernel-computed string vocabulary, now seven
--     members; no bound is a bare round literal.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): CLASS-RATIFIED FAIL-SAFE
-- shape -- this delta only WIDENS an existing refusal's reach (one new act-class token added to
-- an existing, unconditional conjunct (b) check) and CORRECTS a teach-text string; nothing
-- existing is relaxed, no existing CHECK narrowed, no existing grant revoked, no existing
-- accepted-write class newly refused. Per the spec amendment's own framing ("fail-safe additive,
-- class-ratified path"), riding the 2026-07-09 class rule, not routed for a separate maintainer
-- ratification question -- stated here for the record, matching s60's own disclosure convention.
--
-- LIMITS (pre-registered):
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
