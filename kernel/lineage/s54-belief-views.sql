-- s54 BELIEF VIEWS (design/FABLE-BELIEF-SUBSTRATE-SPEC.md v2 Delta B2, §3.4 -- ratified build
-- basis, ledger rows 1914/1919). VIEW-ONLY, ZERO NEW LEDGER COLUMNS, ZERO NEW KINDS -- therefore
-- compute_row_hash is UNTOUCHED and gates/hash_coverage_gate.py stays green trivially (the s46
-- discipline, stated here rather than left inferred). Writes are unaffected -- the s43 boundary
-- continues to own them; this delta touches no INSERT path whatsoever.
--
-- Sonnet-executed per the standing delegation contract, from this Fable-authored, maintainer-
-- ratified spec. This delta is AUTHORED and SCRATCH-WITNESSED only; APPLYING it to any live/
-- existing world is the maintainer's act at a FUTURE world's birth (runs-are-strictly-linear,
-- 2026-07-11) -- never taken here.
--
-- PREREQUISITE: s53 (kernel/lineage/s53-belief-substrate.sql) -- a HARD dependency (the s44/s46
-- precedent transposed): these views read the TYPED belief columns only -- a kernel view parsing
-- the v1 statement convention would be load-bearing knowledge in an unenforceable convention
-- inside the kernel, refused here explicitly (the same cancer G s46's own header names). THE
-- HEAD-BODY RULE: at this delta's authoring the lineage head is s53 (this same commission's
-- sibling, landing immediately before this file) -- ledger_current's column list this file reads
-- FROM is s53's own (74 columns), verified against that file's own text. This file does NOT
-- re-issue ledger_current/countersigned_in_force (it has no columns of its own to append).
--
-- WHY (operator-side prose; NOT subject-visible): spec §3.4's own framing -- the substrate's
-- read surface: "what currently stands as belief" minus what an unresolved contest demotes,
-- restricted to what is well-founded (its chain bottoms out in witnessed observation or in-force
-- undefeated non-belief rows) -- computed fresh on every read, nothing stored. The engine layer
-- (engine/lp/ledger_belief.lp + its SQL twin engine/belief_floor.py, already shipped with v1,
-- ledger rows 1914/1919, and widened this same commission with a typed-arm branch per s53's own
-- header) is the AUTHORITATIVE computation (`./judge --layer belief`, agreement is the
-- authority, the s46 precedent restated); these SQL kernel views are the DISPLAY surface for an
-- operator/SPA reader who wants a fast, no-clingo-required read of the same judgment restricted
-- to the typed (s53+) arm, exactly as model_defeated_rows/credited_current (s46) are the display
-- surface beside the defeat engine layer.
--
-- ELEMENT 1 -- belief_current (spec §3.4 item 1): in-force belief rows with their typed columns,
-- security_invoker, factoring through ledger_current exclusively (no raw-`ledger` leg). Consumer
-- (row 1906): the other views below (base); operator/pickup reads; the SPA read surface.
--
-- ELEMENT 2 -- contested_beliefs (spec §3.4 item 2): one row per contest edge between two
-- in-force beliefs -- (belief_id, contested_by, contest_basis, target_basis, resolved_survivor
-- NULLABLE). Evidence-class precedence (spec §3.3, closed, small): observed > derived >
-- testimony > assumed; on strict inequality the higher-basis side is the resolved survivor, on a
-- tie neither resolves. Cause always visible (the s46 auditability-wall rule, restated here as
-- binding, spec's own words). Consumer: the operator adjudicating doubt (pickup/audit reads);
-- credited_beliefs below.
--
-- ELEMENT 3 -- credited_beliefs (spec §3.4 item 3): TYPED (s53+) ARM ONLY -- the v1 convention-
-- row arm stays the engine floor's own concern (cancer G, s46's own precedent transposed one
-- layer over). In-force, TYPED belief rows that are (i) not demoted by an UNRESOLVED contest
-- (a resolved survivor re-enters), and (ii) well-founded: basis=observed is grounded by its own
-- mandatory, trigger-existence-checked witness/universe; basis=derived/testimony is well-founded
-- iff every premise/source is itself well-founded (a belief) or grounded (an in-force, TYPED-arm
-- non-belief row) -- computed via a recursive CTE over the belief_premises array and
-- belief_source edge (Postgres CAN express this one recursively, unlike the v1 SQL floor's
-- Python-driven fixpoint: the array/self-FK typed shape has no "universal quantification inside
-- a NOT EXISTS" obstruction the v1 regex-parsed comma-list did -- named here as a genuine,
-- reported simplification the typed shape buys, not a silent deviation from the v1 floor's own
-- idiom). basis=assumed is NEVER credited (spec §3.4 -- "an assumption's consumer is its future
-- defeat, not credit"). Model-identity defeat composes via s46's own credited_current (a premise/
-- source naming a row model_defeated_rows lists un-founds the chain resting on it -- the SAME
-- composition ledger_belief.lp performs via model_defeated_row/1, neither calculus knowing the
-- other's internals). Consumer: warrant-directed verification (row 1895's staged queue, §8.2 of
-- the spec, NOT built here); operator reads; the ratification-question surface.
--
-- ELEMENT 4 -- corroboration (spec §3.4 item 4): per credited (typed-arm) belief, the derived
-- witness-diversity grade -- uncorroborated | corroborated-same-class | corroborated-cross-class
-- -- from concurrence-connected, SoD-distinct (validate_belief_edges' own different-actor rule,
-- s53), in-force beliefs joined to kernel.principal.agent_class. Reported, gating nothing (the
-- s44 attestation-grade precedent). Consumer: the A:B:C loop's escalation judgment and audit
-- briefs; the future doubt tier's warrant ranking (spec §8.2, not built here).
--
-- ELEMENT 5 -- shared_premise (spec §3.4 item 5): for concurrence-connected typed-arm belief
-- pairs, the common ancestors of their premise/source closures -- a recursive CTE over the SAME
-- belief_premises/belief_source edges ELEMENT 3 already closes. Consumer: independence audits
-- (ADR-0000 Revisit-#4); ADR-0014 second-opinion dispatch decisions.
--
-- WHAT THIS DELTA DOES NOT TOUCH: ZERO new ledger columns (compute_row_hash untouched); ZERO new
-- kinds (no kind_shape_manifest_gate.py MANIFEST edit -- CHAIN gains this file purely to exercise
-- these five views under the scratch apply); ZERO triggers; ZERO writes (five CREATE OR REPLACE
-- VIEW statements, nothing else); ZERO edits to s53's own objects.
--
-- HISTORY: safe -- all five objects are NEW (no pre-existing reader of any view name); reading
-- ledger_current is the standing s31-discipline read every prior view in this lineage already
-- performs; no existing object's behavior changes.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form; this delta's own slice):
--   - INVARIANT: in an s54 world, belief_current/contested_beliefs/credited_beliefs/
--     corroboration/shared_premise show exactly the typed (s53+) belief-substrate reading the
--     engine layer (`./judge --layer belief`) computes for the SAME arm -- a contest's cause is
--     always reconstructable (contested_beliefs names both sides and the resolved survivor,
--     never hidden); a credited belief's chain bottoms out in witnessed observation or in-force,
--     undefeated (s46-composed), typed non-belief rows.
--   - QUANTIFICATION UNIVERSE: belief sources -- TYPED (s53+) ARM ONLY, the v1 convention-row
--     arm is DELIBERATELY EXCLUDED from this kernel surface (cancer G) and remains the engine
--     floor's own concern; contest resolution -- evidence-class precedence only, recency never
--     (Q3); corroboration -- agent_class diversity only, never a witness COUNT; worlds -- s53+
--     only (this file cannot apply without s53's columns existing).
--   - DENOMINATION: every compared value is an immutable ledger row id or a closed-vocabulary
--     atom (polarity/basis/corroboration grade) -- no text convention crosses (contrast the v1
--     arm, which this view refuses to read at all, the s46 precedent transposed).
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): CLASS-RATIFIED FAIL-SAFE
-- CANDIDATE in SHAPE (view-only, zero columns, zero kinds, strictly additive) but NOT claimed as
-- such -- it ships under design/FABLE-BELIEF-SUBSTRATE-SPEC.md's own ratification (rows
-- 1914/1919) plus this build's own commission, the s46-precedented, more conservative routing.
--
-- LIMITS (pre-registered):
--   - TYPED-ARM ONLY, named above -- a world running v1-only beliefs shows NO rows here even
--     though the engine floor (which reads BOTH arms) may show some; the engine differential
--     stays the authoritative computation a consumer binds to consistently (the s46 display-
--     contract precedent).
--   - Live operation awaits an s53+ world entering a scaffold's LINEAGE_CHAIN -- UNEXERCISED
--     live, scratch-witnessed only, this build's own report.
--   - Everything in the spec's own §9 (Honest limits) applies transitively: a lazy universe is
--     representable, not impossible; contest/concurrence noticing is not automatic; evidence-
--     class precedence ranks bases, not quality within a basis.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s53):
--   VALIDATE (reachable throwaway): apply the full chain through s53, then
--   -f s54-belief-views.sql.
--   REAL: NEVER applied to any existing world by this authoring act. Enters a FUTURE world's
--   birth chain via bootstrap/new-project.sh's LINEAGE_CHAIN, wired in the SAME commit as s53
--   (see s53's own ELEMENT 6). Authored and scratch-witnessed on scratch schema pairs in the TOY
--   db only.
-- Run as the schema owner (bork). Idempotent (CREATE OR REPLACE VIEW).
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
-- ELEMENT 1 -- belief_current.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".belief_current
    WITH (security_invoker = true) AS
SELECT lc.id, lc.ts, lc.actor, lc.statement AS proposition, lc.confidence,
       lc.belief_polarity, lc.belief_basis, lc.belief_universe, lc.belief_witness,
       lc.belief_source, lc.belief_premises, lc.belief_subject, lc.belief_contests,
       lc.belief_concurs
FROM   :"schema".ledger_current lc
WHERE  lc.kind = 'belief';

COMMENT ON VIEW :"schema".belief_current IS
  'design/FABLE-BELIEF-SUBSTRATE-SPEC.md §3.4 item 1: in-force typed belief rows, factored
   through ledger_current exclusively. kernel/lineage/s54-belief-views.sql.';

GRANT SELECT ON :"schema".belief_current TO :"role";

-- ============================================================================================
-- ELEMENT 2 -- contested_beliefs (spec §3.4 item 2). Evidence-class precedence: observed(4) >
-- derived(3) > testimony(2) > assumed(1); strict inequality resolves, a tie does not.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".contested_beliefs
    WITH (security_invoker = true) AS
WITH rank(basis, r) AS (VALUES ('observed',4), ('derived',3), ('testimony',2), ('assumed',1))
SELECT c.id AS belief_id, t.id AS contested_by,
       c.belief_basis AS contest_basis, t.belief_basis AS target_basis,
       CASE WHEN rc.r > rt.r THEN c.id
            WHEN rt.r > rc.r THEN t.id
            ELSE NULL END AS resolved_survivor
FROM   :"schema".belief_current c
JOIN   :"schema".belief_current t ON t.id = c.belief_contests
JOIN   rank rc ON rc.basis = c.belief_basis
JOIN   rank rt ON rt.basis = t.belief_basis;

COMMENT ON VIEW :"schema".contested_beliefs IS
  'design/FABLE-BELIEF-SUBSTRATE-SPEC.md §3.4 item 2: one row per contest edge between two
   in-force typed beliefs -- (belief_id, contested_by, contest_basis, target_basis,
   resolved_survivor NULLABLE). Evidence-class precedence only (observed>derived>testimony>
   assumed); recency never resolves a contest between distinct principals (Q3).
   kernel/lineage/s54-belief-views.sql.';

GRANT SELECT ON :"schema".contested_beliefs TO :"role";

-- ============================================================================================
-- ELEMENT 3 -- credited_beliefs (spec §3.4 item 3). TYPED ARM ONLY. Well-foundedness via a
-- recursive CTE over belief_premises/belief_source (the typed shape's array/self-FK make this
-- expressible recursively -- unlike the v1 SQL floor's Python-driven fixpoint, see this file's
-- own ELEMENT 3 header note above). model-identity defeat composed via s46's model_defeated_rows
-- (an in-force premise/source that is itself model-defeated un-founds the chain resting on it).
-- ============================================================================================
-- NAMED SQL-EXPRESSIBILITY NOTE (ADR-0000 Rule 2(a), reported not silent): well-foundedness is
-- an AND-type (conjunctive, "every premise founded") fixpoint -- engine/belief_floor.py's own
-- docstring names this exact obstruction for the v1 floor ("Postgres forbids a recursive CTE's
-- self-reference inside a NOT EXISTS/aggregate subquery... no single recursive CTE expresses
-- it... computes the well-founded closure via an explicit Python fixpoint loop"). A KERNEL VIEW
-- has no procedural driver available, so this delta uses the standard SQL pattern for AND-type
-- recursive closure that respects the "self-reference only directly in FROM, never inside a
-- sub-SELECT" rule: an edge table (premise/source targets) is joined DIRECTLY (not via a
-- subquery) against the recursive CTE and a non-recursive `grounded` CTE, then a HAVING
-- count(DISTINCT target) = (total edges for this id) closes each node only once EVERY one of
-- its edges resolves -- the same semi-naive fixpoint the Python loop computes, expressed as a
-- join-and-count instead of a NOT EXISTS.
CREATE OR REPLACE VIEW :"schema".credited_beliefs
    WITH (security_invoker = true) AS
WITH RECURSIVE undoubted AS (
  -- an in-force typed belief NOT demoted by an unresolved contest, and not the losing side of a
  -- resolved one, on EITHER edge direction (a belief may be the challenger or the target).
  SELECT b.id FROM :"schema".belief_current b
  WHERE NOT EXISTS (
    SELECT 1 FROM :"schema".contested_beliefs cb
    WHERE (cb.belief_id = b.id OR cb.contested_by = b.id)
      AND (cb.resolved_survivor IS NULL OR cb.resolved_survivor <> b.id)
  )
),
grounded AS (
  -- an in-force, non-belief row not model-defeated (s46 composition).
  SELECT lc.id FROM :"schema".ledger_current lc
  WHERE lc.kind <> 'belief'
    AND NOT EXISTS (SELECT 1 FROM :"schema".model_defeated_rows mdr WHERE mdr.row_id = lc.id)
),
base_founded AS (
  -- basis=observed: grounded by its own mandatory, trigger-existence-checked witness/universe.
  SELECT u.id FROM undoubted u
  JOIN :"schema".belief_current b ON b.id = u.id
  WHERE b.belief_basis = 'observed'
    AND ((b.belief_polarity = 'existential' AND b.belief_witness IS NOT NULL)
         OR (b.belief_polarity = 'universal' AND b.belief_universe IS NOT NULL))
),
edge(id, target) AS (
  SELECT b.id, p.pid FROM :"schema".belief_current b, unnest(b.belief_premises) p(pid)
    WHERE b.belief_basis = 'derived' AND b.belief_premises IS NOT NULL
  UNION ALL
  SELECT b.id, b.belief_source FROM :"schema".belief_current b
    WHERE b.belief_basis = 'testimony' AND b.belief_source IS NOT NULL
),
edge_count(id, n) AS ( SELECT id, count(*) FROM edge GROUP BY id ),
founded(id) AS (
  SELECT id FROM base_founded
  UNION
  SELECT sat.id
  FROM (
    SELECT e.id, e.target FROM edge e JOIN grounded g ON g.id = e.target
    UNION ALL
    SELECT e.id, e.target FROM edge e JOIN founded f ON f.id = e.target
  ) sat
  JOIN   undoubted u ON u.id = sat.id
  JOIN   edge_count ec ON ec.id = sat.id
  GROUP BY sat.id, ec.n
  HAVING count(DISTINCT sat.target) = ec.n
)
SELECT bc.id AS belief_id, bc.actor, bc.proposition, bc.belief_polarity, bc.belief_basis
FROM   :"schema".belief_current bc
WHERE  bc.id IN (SELECT id FROM founded);

COMMENT ON VIEW :"schema".credited_beliefs IS
  'design/FABLE-BELIEF-SUBSTRATE-SPEC.md §3.4 item 3: TYPED (s53+) ARM ONLY -- in-force,
   uncontested (or resolved-survivor), well-founded typed beliefs; basis=assumed is NEVER
   credited (recorded, defeasible, its consumer is its future defeat). Model-identity defeat
   composed via s46''s model_defeated_rows -- a defeated premise/source un-founds the chain
   resting on it. kernel/lineage/s54-belief-views.sql.';

GRANT SELECT ON :"schema".credited_beliefs TO :"role";

-- ============================================================================================
-- ELEMENT 4 -- corroboration (spec §3.4 item 4). Concurrence-connected, SoD-distinct (s53's own
-- different-actor rule), in-force beliefs joined to kernel.principal.agent_class.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".corroboration
    WITH (security_invoker = true) AS
WITH concur_pair AS (
  SELECT c.id AS a, c.belief_concurs AS b FROM :"schema".belief_current c WHERE c.belief_concurs IS NOT NULL
  UNION
  SELECT c.belief_concurs AS a, c.id AS b FROM :"schema".belief_current c WHERE c.belief_concurs IS NOT NULL
),
classes AS (
  SELECT cp.a AS belief_id, p0.agent_class AS own_class, p1.agent_class AS peer_class
  FROM   concur_pair cp
  JOIN   :"schema".belief_current b0 ON b0.id = cp.a
  JOIN   :"schema".belief_current b1 ON b1.id = cp.b
  JOIN   :"kern".principal p0 ON p0.id = b0.actor
  JOIN   :"kern".principal p1 ON p1.id = b1.actor
)
SELECT cb.belief_id,
       CASE WHEN bool_or(cl.peer_class IS DISTINCT FROM cl.own_class) THEN 'corroborated-cross-class'
            WHEN count(cl.peer_class) > 0 THEN 'corroborated-same-class'
            ELSE 'uncorroborated' END AS grade
FROM   :"schema".credited_beliefs cb
LEFT JOIN classes cl ON cl.belief_id = cb.belief_id
GROUP BY cb.belief_id;

COMMENT ON VIEW :"schema".corroboration IS
  'design/FABLE-BELIEF-SUBSTRATE-SPEC.md §3.4 item 4: per credited (typed-arm) belief, the
   witness-diversity grade (uncorroborated | corroborated-same-class | corroborated-cross-class)
   from agent_class over the concurrence-connected, SoD-distinct set -- never a witness COUNT.
   Reported, gating nothing. kernel/lineage/s54-belief-views.sql.';

GRANT SELECT ON :"schema".corroboration TO :"role";

-- ============================================================================================
-- ELEMENT 5 -- shared_premise (spec §3.4 item 5). Common ancestors of concurrence-connected
-- typed-arm belief pairs' premise/source closures.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".shared_premise
    WITH (security_invoker = true) AS
WITH RECURSIVE direct_edge(id, anc) AS (
  SELECT b.id, p.pid FROM :"schema".belief_current b, unnest(b.belief_premises) p(pid)
    WHERE b.belief_premises IS NOT NULL
  UNION
  SELECT b.id, b.belief_source FROM :"schema".belief_current b WHERE b.belief_source IS NOT NULL
),
ancestor(id, anc) AS (
  SELECT id, anc FROM direct_edge
  UNION
  SELECT a.id, e.anc FROM ancestor a JOIN direct_edge e ON e.id = a.anc
),
concur_pair AS (
  SELECT LEAST(c.id, c.belief_concurs) AS belief_a, GREATEST(c.id, c.belief_concurs) AS belief_b
  FROM :"schema".belief_current c WHERE c.belief_concurs IS NOT NULL
)
SELECT DISTINCT cp.belief_a, cp.belief_b, aa.anc AS shared_ancestor
FROM   concur_pair cp
JOIN   ancestor aa ON aa.id = cp.belief_a
JOIN   ancestor ab ON ab.id = cp.belief_b AND ab.anc = aa.anc;

COMMENT ON VIEW :"schema".shared_premise IS
  'design/FABLE-BELIEF-SUBSTRATE-SPEC.md §3.4 item 5: for concurrence-connected typed-arm
   belief pairs, (belief_a, belief_b, shared_ancestor) -- the common ancestors of their
   premise/source closures. "Five independent layers checked this" becomes a query whose
   answer can be no. kernel/lineage/s54-belief-views.sql.';

GRANT SELECT ON :"schema".shared_premise TO :"role";
-- ============================================================================================
