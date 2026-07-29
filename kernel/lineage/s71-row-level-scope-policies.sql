-- s71 ROW-LEVEL SCOPE POLICIES (design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md §2/§5
-- item 6, "RLS slot (future birth, after S2b lands in a chain; named, not built)" -- S2b landed
-- 0e2eda39/513c91e2, ledger row 600; this delta is that future birth, lifted from named slot to
-- built sibling per the maintainer's 2026-07-29 Grothendieck directive, work item
-- ac-rls-s71-delta). FAIL-SAFE-ADDITIVE (CLAUDE.md 2026-07-09 class rule): this delta adds ONE
-- new function (scope_row_visible, SECURITY DEFINER, called ONLY from this delta's own new
-- POLICY) and enables Postgres ROW LEVEL SECURITY on :"schema".ledger with exactly ONE new
-- FOR-SELECT policy. It re-issues NOTHING: no column added, no kind added, no existing CHECK/
-- function/view/trigger touched -- compute_row_hash/ledger_current/countersigned_in_force are
-- NOT re-issued (no new column), unlike every column-bearing sNN before it. Nothing existing is
-- relaxed; the new policy can only ever REMOVE rows a role could see, never add visibility a
-- role lacked before this delta (RLS's own denial-only nature; see LIMITS for the two disclosed
-- edges where "remove" does not fire). Sonnet-built per the standing delegation contract.
--
-- PREREQUISITE: this delta REQUIRES s70 (kernel/lineage/s70-scope-binding.sql) applied first --
-- it reads :"schema".principal_scopes (s70 Element 5), a view that does not exist before s70.
-- Applying this file on a pre-s70 kernel fails loudly at CREATE FUNCTION time (principal_scopes
-- does not exist), the correct, disclosed failure mode, matching every prior PREREQUISITE
-- precedent (s70's own header, s60/s62/s64's own headers). THE HEAD-BODY RULE (s45's own
-- standing instruction, carried here verbatim): at this delta's authoring the lineage head is
-- s70 (kernel/lineage/'s own directory listing, confirmed by the builder before authoring). No
-- function/view/CHECK is RE-ISSUED by this delta (Element 1's own header), so no
-- `-- prior-body-sha256:` line is needed anywhere in this file (gates/lineage_reissue_lineage.py
-- has nothing to check here -- confirmed by that gate's own docstring, which mechanizes ONLY
-- re-issued bodies' text-continuity, never a delta that re-issues zero objects).
--
-- WHY (spec §2's second enforcement point, read literally against this delta's own scope): the
-- spec names THREE layered enforcement points -- (1) boundary-side filtering, the serving
-- layer's own route-level concern, NOT built here; (2) Postgres RLS, "the end state, kernel-
-- grade... RLS policies keyed on a per-request SET-scoped principal are only real once the
-- connecting role is not the owner" -- THIS delta, now that S2b (0e2eda39) has landed a chain;
-- (3) the side-channel honesty note (raw-psql ban, change-gate/sweep pair) -- unaffected,
-- untouched by this delta. This delta builds (2) ONLY: a per-request GUC, named here
-- `app.scope_principal` (a bigint-as-text value, the SAME `current_setting(..., true)`/
-- `app.vendor_*` idiom s23/s24's own header already establishes for this project's GUC family --
-- missing_ok=true throughout, so an unset GUC never raises, it reads NULL), consulted by ONE new
-- SECURITY DEFINER function (scope_row_visible) that a single new FOR-SELECT policy on
-- :"schema".ledger calls per candidate row. THE ROW-LEVEL HALF ONLY: spec §1b splits a scope
-- into GRANTED READ SURFACES (scope_surfaces -- a route/view-name grant, a SERVING-layer, not a
-- row-level, concept -- this delta does NOT enforce it, see LIMITS) and an OPTIONAL row-level
-- EXCLUSION FAMILY (scope_exclusions -- kind-class/thread/work-item-lineage/rows, s70 Element 2's
-- own closed four-member vocabulary, shape-CHECKed there by scope_exclusions_shape_ok). This
-- delta enforces EXACTLY the exclusion family, at the one place a per-ROW Postgres predicate can
-- actually bind: a candidate row is invisible to a scoped read iff it matches one of the bound
-- principal's own scope_exclusions entries; every other row (including every row when the
-- principal holds NO bound scope, or a bound scope with NO exclusions, or no GUC is set at all)
-- passes -- THE FAIL-SAFE DEFAULT, restated here one layer over from s70's own: unarmed (no GUC)
-- is byte-identical to today; a principal with the open scope (no principal_scopes row) is
-- byte-identical to today; a principal with a scope that GRANTS surfaces but excludes nothing
-- is byte-identical to today for every row this delta can filter.
--
-- WHY SECURITY DEFINER (the recursion this delta must NOT create): scope_row_visible's own body
-- queries :"schema".principal_scopes, a security_invoker VIEW factored through ledger_current,
-- which itself reads raw :"schema".ledger -- THE SAME TABLE this delta is about to gate with RLS.
-- A plain (invoker-rights) helper function would recurse: evaluating row-visibility for row R
-- would re-invoke RLS to fetch the scope-binding rows powering that very evaluation, which would
-- themselves need row-visibility evaluated, unbounded. SECURITY DEFINER breaks this cleanly and
-- by ORDINARY Postgres semantics, not a special case authored for this file: inside a SECURITY
-- DEFINER function call, current_user becomes the function's OWNER for the call's duration
-- (documented Postgres behavior, the SAME mechanism s43 Element 8's own set_actor() note already
-- relies on: "SECURITY DEFINER changes current_user to the function's owner"); a
-- security_invoker view's permission AND row-security check is performed against whichever role
-- is CURRENTLY executing the query, so a call from inside this SECURITY DEFINER function reads
-- principal_scopes (and, transitively, ledger_current/ledger) AS THE FUNCTION'S OWNER -- who
-- IS the table owner (this delta's function, like every other SECURITY DEFINER function in this
-- lineage, is created while the schema is still owned by the invoking migration identity, then
-- swept into the S2b split's generic per-object OWNER TO reassignment loop exactly like s17's
-- stamp_valid/s43's four write functions/s44's model_identity_attested writer -- no bespoke
-- carve-out needed, bootstrap/new-project.sh's existing reassignment loop already iterates every
-- function in the two namespaces). The TABLE OWNER bypasses RLS by ordinary Postgres semantics
-- (unless FORCE ROW LEVEL SECURITY is set -- deliberately NOT set here, see ELEMENT 2's own note
-- and LIMITS below) -- so the DEFINER's own internal read never re-enters this delta's policy at
-- all, closing the recursion by construction, not by a depth guard.
--
-- HONEST BOUND ON WHAT "INERT PRE-SPLIT" MEANS (stated precisely, not as folklore -- the
-- commission's own text says "on a world without the S2b split (connecting role owns the
-- schema) the policies are inert-by-Postgres-semantics"; this header names EXACTLY the Postgres
-- fact that sentence is standing on, and separately discloses where it does NOT reduce to "no
-- S2b split ran"): Postgres's RLS bypass fires for exactly two identities -- an actual superuser,
-- and (absent FORCE ROW LEVEL SECURITY, never set by this delta) the RELATION'S OWNER -- for
-- ANY OTHER role, ENABLE ROW LEVEL SECURITY is unconditionally live the instant this file is
-- applied, regardless of whether the S2b split ever ran. In THIS project's own default shape,
-- the GRANTED ACCESS ROLE (:"role", e.g. a world's `<name>_rw`) has NEVER been the schema owner,
-- split or not (s15's own header: "Run as the schema owner (bork)" -- a login superuser identity,
-- distinct from :role, since s15; S2b (0e2eda39) only moves ownership OFF that shared superuser
-- onto a freshly minted, non-login $OWNER role, still distinct from :role either way -- see that
-- commit's own text, "Row 600's REJECTED shape is the granted access role owning the schema;
-- that is NOT what happens today"). So the precise, witnessed claim this delta stands behind is:
-- a QUERYING IDENTITY THAT IS THE TABLE'S CURRENT OWNER sees every row, unconditionally, whether
-- or not a scope with exclusions is bound to that identity's own principal_subject -- witnessed
-- BOTH as a split world's fresh $OWNER role (inert by construction, never the reading identity a
-- served route uses) AND as a raw, non-split scratch chain's connecting superuser identity
-- (inert, the literal "connecting role owns the schema" configuration the commission names,
-- witnessed directly rather than assumed). The DISTINCT, NOT-inert claim, named so no reader
-- conflates the two: a GRANTED, NON-OWNER role (:"role" as this project actually configures it,
-- in EITHER a split or non-split world) is never exempt from this delta's policy by ownership --
-- for that role the only fail-safe path to full/byte-identical reads is the UNARMED path (no
-- GUC set, or a bound scope with no exclusions), the SAME "unarmed is byte-identical" guarantee
-- s70's own header states, independent of split status. This delta's WITNESS section below
-- exercises both the inert-by-ownership case and the armed/enforced :"role" case; neither is
-- silently assumed from the other.
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
-- ELEMENT 1 -- scope_row_visible: THE ONE NEW FUNCTION. SECURITY DEFINER (see header WHY),
-- STABLE (reads the catalog-backed principal_scopes view but performs no write), owned by
-- whichever identity runs this file (swept into the S2b split's generic reassignment loop on a
-- split birth, matching every prior SECURITY DEFINER helper in this lineage -- no bespoke carve-
-- out). Takes the CANDIDATE ROW itself (the row a policy is currently deciding), never a bare id
-- (a superseded-and-re-inserted row could share the SAME id-domain concept as one that
-- shouldn't -- reading the row's OWN kind/work_slug/missive_thread columns directly is the same
-- "classify what IS, not a second hop" idiom s62 round 2 already established for
-- entitlement_act_class_of_target).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".scope_row_visible(r :"schema".ledger)
    RETURNS boolean LANGUAGE plpgsql STABLE SECURITY DEFINER
    SET search_path = :"schema", pg_temp AS $fn$
DECLARE
  v_principal_raw text;
  v_principal     bigint;
  v_exclusions    jsonb;
  v_elem          jsonb;
  v_family        text;
  v_value         jsonb;
BEGIN
  -- UNARMED PATH 1: no GUC set at all -- current_setting(..., true) (missing_ok) returns NULL
  -- rather than raising, the SAME idiom app.vendor_session/app.vendor_invocation already use
  -- (s23/s24's own header). No bound principal in this session: every row passes, byte-identical
  -- to a world without this delta.
  v_principal_raw := current_setting('app.scope_principal', true);
  IF v_principal_raw IS NULL OR btrim(v_principal_raw) = '' THEN
    RETURN true;
  END IF;

  -- MALFORMED-GUC PATH: a non-numeral value in app.scope_principal is treated as UNARMED (fail-
  -- safe open), never a hard error inside a row-security predicate -- an exception raised from
  -- inside a policy expression surfaces as a query-wide error, which would make a malformed GUC
  -- a DENIAL-OF-SERVICE lever on every read this role attempts, the opposite of fail-safe. This
  -- is the SAME "fail open, not fail loud, inside a per-row filter" posture named explicitly
  -- below as a disclosed LIMIT, not silently accepted.
  IF v_principal_raw !~ '^[0-9]+$' THEN
    RETURN true;
  END IF;

  -- OUT-OF-RANGE-NUMERAL PATH (fix round, adjudication row 890): the regex above accepts ANY
  -- run of digits, including one that is a purely numeral value too large for bigint (e.g. 25
  -- nines) -- v_principal_raw::bigint would then RAISE numeric_value_out_of_range from INSIDE
  -- this policy predicate, the exact query-wide-error DoS lever the MALFORMED-GUC PATH comment
  -- above names as the reason this function fails open rather than raises. A digit-only string
  -- passing the regex is not yet a guarantee it fits bigint, so the cast itself is wrapped in
  -- its own exception handler: ANY error the cast raises (out-of-range being the one this GUC
  -- can actually produce, since the regex already rules out a non-numeral) is treated exactly
  -- like the non-numeral case one step up -- fail OPEN, never raise. This keeps the disclosed
  -- guarantee ("a malformed GUC fails open, never raises") true for the WHOLE input space, not
  -- merely the non-numeral subset of it.
  BEGIN
    v_principal := v_principal_raw::bigint;
  EXCEPTION WHEN OTHERS THEN
    RETURN true;
  END;

  -- UNARMED PATH 2: the bound principal holds NO in-force principal_scopes row (s70's own
  -- fail-safe default, the open scope) -- every row passes.
  -- Bare (unqualified) relation name, relying on this function's own SET search_path clause --
  -- the SAME convention every reader in this lineage uses inside a dollar-quoted PL/pgSQL
  -- function body (psql's colon-variable interpolation is a LEXICAL, pre-send substitution that
  -- does not reach inside a dollar-quoted body's text; verified live during this delta's own
  -- authoring -- entitlement_act_class_of and every other function this lineage ships reference
  -- their tables bare for the same reason, never schema-qualified via a psql variable inside
  -- their own body).
  SELECT ps.scope_exclusions INTO v_exclusions
  FROM principal_scopes ps
  WHERE ps.subject = v_principal;

  -- UNARMED PATH 3: a bound scope that carries NO exclusion family (scope_exclusions IS NULL,
  -- s70 Element 2 -- a scope that grants surfaces but excludes no row) -- every row passes.
  IF v_exclusions IS NULL THEN
    RETURN true;
  END IF;

  -- ARMED: walk the closed four-member exclusion-family vocabulary (s70's own
  -- scope_exclusions_shape_ok CHECK already guarantees this jsonb's shape at write time -- this
  -- function trusts that shape, never re-validates it, the same "the CHECK is the one home"
  -- posture every reader in this lineage takes toward an already-CHECK-guarded column).
  FOR v_elem IN SELECT * FROM jsonb_array_elements(v_exclusions) LOOP
    v_family := v_elem->>'family';
    v_value  := v_elem->'value';
    IF v_family = 'kind-class' AND r.kind = (v_value #>> '{}') THEN
      RETURN false;
    ELSIF v_family = 'thread' AND r.missive_thread = (v_value #>> '{}') THEN
      RETURN false;
    ELSIF v_family = 'work-item-lineage' AND r.work_slug = (v_value #>> '{}') THEN
      RETURN false;
    ELSIF v_family = 'rows' THEN
      IF EXISTS (SELECT 1 FROM jsonb_array_elements_text(v_value) AS rid(v)
                 WHERE rid.v = r.id::text) THEN
        RETURN false;
      END IF;
    END IF;
  END LOOP;

  RETURN true;
END; $fn$;

COMMENT ON FUNCTION :"schema".scope_row_visible(:"schema".ledger) IS
  'kernel/lineage/s71-row-level-scope-policies.sql (design/FABLE-ACCESS-CONTROL-AND-INFORMATION-
   FLOW-SPEC.md §2): true iff the CURRENT SESSION (per the app.scope_principal GUC, unauthenticated
   at this layer -- see this delta''s own header LIMIT) is unarmed (no GUC, a GUC that is not a
   valid in-range bigint -- non-numeral or numeral-but-overflowing, both fail open, never raise --
   no bound scope, or a bound scope with no exclusions) OR the candidate row does not match any
   exclusion family the bound principal''s in-force principal_scopes row carries. SECURITY DEFINER so its own internal
   read of principal_scopes (itself ledger_current-factored, hence raw-ledger-backed) runs as the
   TABLE OWNER, bypassing this delta''s own RLS policy rather than recursing through it -- see
   header WHY. Called ONLY from this delta''s own ledger_scope_read policy.';

REVOKE ALL ON FUNCTION :"schema".scope_row_visible(:"schema".ledger) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION :"schema".scope_row_visible(:"schema".ledger) TO :"role";

-- ============================================================================================
-- ELEMENT 2 -- ROW LEVEL SECURITY, ENABLED (not FORCED -- deliberate, see header's own "HONEST
-- BOUND" note and LIMITS below): the table OWNER and an actual Postgres superuser both keep
-- their standing bypass, unconditionally, exactly the same disclosed bound every s26..s70 delta
-- already carries for owner/superuser direct DML. FORCE ROW LEVEL SECURITY would additionally
-- bind the owner itself -- NOT taken here: the SECURITY DEFINER write/read functions this whole
-- lineage is built on (s17/s27/s40/s43/s44/s45/s51/s57/s58/this delta's own Element 1, ...) run
-- AS the owner precisely so they can see/write the full, unfiltered table; forcing RLS would
-- gate every one of them too, a materially larger and un-commissioned surface change this delta
-- does not take.
-- ============================================================================================
ALTER TABLE :"schema".ledger ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS ledger_scope_read ON :"schema".ledger;
CREATE POLICY ledger_scope_read ON :"schema".ledger
    FOR SELECT
    USING (:"schema".scope_row_visible(ledger));

COMMENT ON POLICY ledger_scope_read ON :"schema".ledger IS
  'kernel/lineage/s71-row-level-scope-policies.sql (design/FABLE-ACCESS-CONTROL-AND-INFORMATION-
   FLOW-SPEC.md §2, mechanism roster item 6, "the RLS slot"): the ONE new SELECT-only policy this
   delta ships. Read path only -- INSERT/UPDATE/DELETE are unaffected (no policy for any of the
   three is added; :"role" has held no UPDATE/DELETE grant on this table since birth, and s43
   REVOKEd its INSERT grant, so the write path was, and remains, exclusively the owner-run
   SECURITY DEFINER functions this ENABLE does not gate, see this file''s own ELEMENT 2 header).
   Applies to every reader of :"schema".ledger AND, by ordinary view inheritance, to every
   security_invoker view factored through it (ledger_current, countersigned_in_force,
   principal_scopes, credited_current, review_verdicts, ... -- the s31 discipline''s own
   consequence: one enforcement point covers the whole read-surface family for free, no second
   policy needed per view).';

-- ============================================================================================
-- HISTORY: safe -- per-mechanism grounds:
--   * scope_row_visible is a BRAND NEW function with no pre-existing caller; SECURITY DEFINER,
--     REVOKEd from PUBLIC, GRANTed only to :"role" (the s17/s43 standing idiom for a definer
--     helper a non-owner role must be able to invoke).
--   * ENABLE ROW LEVEL SECURITY + ONE new FOR-SELECT policy: no pre-existing SELECT this table
--     ever served is WIDENED by this delta (RLS can only ever NARROW a role''s visible row set
--     relative to "no RLS" -- Postgres''s own semantics, not an assertion this file must enforce
--     separately); the owner/superuser bypass (unforced) means every EXISTING owner-run write/
--     read path (every SECURITY DEFINER function in this lineage, and any direct owner/superuser
--     session) is BYTE-IDENTICAL before and after this delta. For :"role" specifically: a
--     session with no bound scope (the fail-safe default, s70) or an unset/malformed GUC sees
--     every row it always saw -- the new policy''s USING clause reduces to `true` for that
--     session on every row, provably (Element 1''s own three UNARMED PATH branches, each an
--     unconditional early RETURN true before the exclusion walk ever runs).
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form):
--   - INVARIANT: for a querying identity that is neither an actual Postgres superuser nor the
--     current owner of :"schema".ledger, a candidate row is visible iff either (a) the session''s
--     app.scope_principal GUC is unset/malformed, or (b) that principal holds no in-force
--     principal_scopes row, or (c) that row''s scope_exclusions is NULL, or (d) the row matches
--     no entry of that scope''s scope_exclusions family list (kind-class/thread/work-item-
--     lineage/rows, s70''s own closed four-member vocabulary). For the table owner or an actual
--     superuser, EVERY row is visible unconditionally (ENABLE, not FORCE, ROW LEVEL SECURITY).
--   - QUANTIFICATION UNIVERSE: ONE table (:"schema".ledger) gains RLS; every security_invoker
--     view factored through it inherits the SAME filter with no separate policy (enumerated in
--     the policy''s own COMMENT above); ONE new function (scope_row_visible); ONE GUC name
--     (app.scope_principal); the four-member exclusion-family vocabulary is s70''s OWN, not a
--     second copy (ADR-0012 P1) -- this delta introduces no new family and no new shape-CHECK.
--   - DENOMINATION: exclusion families remain denominated in the ledger''s own vocabulary (kind
--     names, missive threads, work-item slugs, an explicit enumerated row-id SET) -- never row-
--     id arithmetic or byte offsets (spec §4), unchanged from s70, simply CONSULTED rather than
--     re-specified here.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): CLASS-RATIFIED FAIL-SAFE
-- shape -- this delta only ADDS a refusal-shaped read-time filter (never a write-time refusal,
-- but the SAME "adds a NEW way for a read to be denied, never a new way for one to be permitted"
-- direction the class rule's own text names) and one read-only helper function; nothing existing
-- is relaxed, no existing grant widened, no existing trigger/CHECK/view touched at all. Ridden
-- under the SAME ratified mechanism-level basis s70 rode (row 639, design/FABLE-ACCESS-CONTROL-
-- AND-INFORMATION-FLOW-SPEC.md, mechanism roster item 6 explicitly named "future birth, after
-- S2b lands in a chain" -- S2b (0e2eda39/513c91e2) is that landed chain), not routed for a
-- separate maintainer ratification question beyond the standing class rule + the spec''s own
-- pre-registered roster slot for this exact mechanism.
--
-- LIMITS (pre-registered, matching every prior delta''s own disclosure convention):
--   - THE GUC IS UNAUTHENTICATED AT THIS LAYER (the load-bearing bound, stated first): any
--     session that can SET app.scope_principal can claim to BE any principal for this policy''s
--     purposes (favorably, claiming an unbound id yields only the fail-safe OPEN default;
--     unfavorably, claiming a bound-and-excluding id and getting REFUSED entries filtered is the
--     WORST case a forger achieves -- forging cannot WIDEN what a forger sees beyond the union of
--     every scope''s grants, since this delta only ever narrows). Spec §1a''s own read-path
--     IDENTITY RESOLUTION (verifying who may legitimately SET this GUC to what) is a named,
--     NOT-built serving-layer follow-on -- exactly the same "tripwire-bounded, not
--     cryptographic" grade s17''s own LIMITS register already discloses for app.vendor_*,
--     restated here for the same reason.
--   - ONLY THE ROW-LEVEL EXCLUSION HALF OF A SCOPE IS ENFORCED HERE. scope_surfaces (the GRANTED
--     READ SURFACE half, §1b) is a route/view-NAME grant, not expressible as a per-row Postgres
--     predicate on ledger alone -- enforcing it is the boundary-side filter, spec §2''s FIRST
--     enforcement point, still a named, NOT-built serving-layer follow-on (unchanged from s70''s
--     own disclosure): a world carrying this delta alone lets a scoped :"role" session read every
--     ROUTE/VIEW it could always read, filtered only by row-level exclusions, never additionally
--     restricted to a granted surface subset.
--   - scope_disclosure_mode (marked | hash_stub | full, s70 §1c) is NOT DIFFERENTIATED by this
--     delta. Postgres RLS can only ever ADMIT or EXCLUDE a row outright from a result set -- it
--     cannot substitute a typed redaction-marker row in place of an excluded one (the "marked"
--     tier''s own defining behavior, §1c) nor emit a visible row_hash-only stub ("hash_stub").
--     What THIS delta actually realizes, for every excluded row regardless of that binding''s own
--     declared scope_disclosure_mode value, is the ROW-LEVEL EFFECT of the "full" tier alone (the
--     row does not cross at all) -- named here explicitly so no reader mistakes "an exclusion
--     family is enforced" for "the bound tier''s own disclosure semantics are honored". A
--     marked/hash_stub-tiered redaction SURFACE, if ever built, is a serving-layer follow-on this
--     delta does not build (the same boundary layer named above).
--   - NO IDENTITY-CONTINUITY OR EXISTENCE CHECK beyond what s70 already disclosed for
--     scope_exclusions itself (a "rows" family entry naming a nonexistent/future row id is legal
--     to write and simply never matches; this delta''s reader inherits, not re-derives, that
--     bound).
--   - Free-text kind/thread/slug matching is byte-equality only (s70''s own free-text-policy-
--     token precedent, unchanged): an unrecognized or misspelled family value silently excludes
--     nothing, rather than refusing at write time (that refusal, if any is wanted for THIS
--     specific mismatch class, is s70''s own write-time CHECK surface, not this delta''s read-time
--     one).
--   - A MALFORMED app.scope_principal VALUE FAILS OPEN (Element 1''s own MALFORMED-GUC PATH AND
--     OUT-OF-RANGE-NUMERAL PATH, fix round adjudication row 890), never raises -- named as a
--     deliberate LIMIT, not an oversight: a policy expression that raises turns a bad GUC into a
--     query-wide error for every read that role attempts, which this delta judges a worse
--     failure mode (an availability hazard on a read path) than the narrower information-
--     exposure a fail-open malformed value could theoretically create (and even that exposure is
--     bounded to "no filtering applied", i.e. today''s pre-delta behavior, never MORE than
--     today). "Malformed" is read over the WHOLE input space here, not merely non-numeral
--     strings: a purely-numeral value that overflows bigint (e.g. 25 nines) passes the regex
--     guard but is caught by the cast''s own exception handler and fails open identically --
--     the fix-round finding this LIMIT was widened to close.
--   - The superuser/table-owner bypass (unforced, Element 2''s own header) is the standing
--     s26..s70 disclosed bound, restated: owner-side direct DML/DQL is out of this delta''s reach.
--   - In a solo world, every scope binding is authored by machinery the one operator controls --
--     complete and attributed, not adversarially independent (s17''s own honesty, inherited,
--     restated here one mechanism further exactly as s70''s own header restates it).
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s70):
--   VALIDATE (reachable throwaway): apply the FULL s15..s70 chain (see kernel/lineage/
--   s70-scope-binding.sql''s own VALIDATE block for the complete -f list, itself s69''s VALIDATE
--   block +1), THEN -f s71-row-level-scope-policies.sql.
--   REAL: NEVER applied to any existing world by this authoring act (runs-are-strictly-linear,
--   2026-07-11). Enters a FUTURE world''s birth chain automatically via bootstrap/new-project.sh's
--   --new-world glob-driven apply list the moment a tree carrying it is scaffolded from; the
--   hand-maintained CLASSIC-scaffold LINEAGE_CHAIN narrative list is a SEPARATE, later maintainer
--   integration act (this delta''s own commission text: "Follow the s70 completion precedent" --
--   taken here in THIS SAME commit, not deferred, since the precedent commit (b34a0108) is the
--   one this delta''s own commission explicitly points at as the shape to follow). Authored and
--   scratch-witnessed on scratch schema pairs in the TOY db only.
-- Run as the schema owner (bork) for a raw scratch apply, or via bootstrap/new-project.sh for a
-- CLASSIC birth (idempotent either way: DROP+CREATE POLICY, CREATE OR REPLACE FUNCTION,
-- ENABLE ROW LEVEL SECURITY is itself idempotent -- re-running it on an already-enabled table is
-- a no-op, verified live in this delta''s own witness run).
-- ============================================================================================
