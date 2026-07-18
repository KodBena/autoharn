-- s52 ARTIFACT WITNESS EXISTENCE CHECK (design/FABLE-ARTIFACT-WITNESS-CHECK-SPEC.md, "Status:
-- Fable-authored 2026-07-18 (inside the freeze window), build basis for one kernel lineage delta
-- ... AWAITING MAINTAINER RATIFICATION to build" -- ratified 2026-07-18, ledger row 1673 item 2,
-- "artifact-witness-check build YES"). CLASS-RATIFIED FAIL-SAFE (CLAUDE.md ORCHESTRATION,
-- 2026-07-09 ruling): this delta ONLY ADDS a refusal -- nothing existing is relaxed, no existing
-- refusal loosened, no existing edge/kind/column semantics changed. Sonnet-executed per the
-- standing delegation contract, from this ratified spec.
--
-- ADR-0000 2(a), the two questions this delta answers: (a) the TYPE that forecloses "an
-- artifact-witness citation naming bytes the store never received" is a construction-time
-- existence check on the review-witness field's `artifact:<hash>` sub-shape, scoped to exactly
-- the same two close-family kinds s48 already scopes to (work_closed, work_violation_disposition)
-- -- s48's own named LIMITS section called this out as the one sub-shape it left unchecked
-- ("a commit-hash or artifact-path witness ... is NOT existence-checked by this delta ... Filed
-- as a named non-goal, not a gap this delta claims to have closed"), and s51 gave that arm a
-- place existence could finally be checked AGAINST (`kernel.artifact`, content-addressed) --
-- this delta is that named successor, built once the store existed to check against (both s48's
-- own LIMITS text and s51's own CLOSURE STATEMENT name it as "a separate, later delta ... the
-- anticipated successor"); (b) the operational lapse (ADR-0000 Rule 2(b), self-directed) is that
-- s51 minted a place bytes could be looked up but left the ONE load-bearing citation position
-- that names them (work_review_ref's artifact: arm) unchecked against it -- a close could cite
-- `artifact:<hash>` for bytes nobody ever stored, the dangling-evidence-pointer shape (the same
-- class s48 already forecloses for the row: arm, one sub-shape over).
--
-- WHY (the defect, spec's own framing): s48 made `row:<id>` witness tokens existence-checked and
-- disclaimed the other two arms (commit, artifact) in its own LIMITS. s51 gave the `artifact:`
-- arm a place existence could be checked against -- `kernel.artifact` -- but nothing checked it:
-- a close could cite `artifact:<hash>` for bytes nobody ever stored, the dangling-evidence-
-- pointer shape (the row-1665 essential-records criterion's own test) in the one position
-- evidence pointers are load-bearing (s29 Element B's own COMMENT on work_review_ref: "a review
-- reference ... for disposition=witnessed").
--
-- MECHANISM (spec's own text, verbatim scoping): a NEW, standalone BEFORE INSERT trigger,
-- validate_artifact_witness_existence -- the s43/s48 validate_supersession_target/
-- validate_review_witness_existence idiom (a single-purpose write-boundary trigger added beside
-- the existing validate_* family, ADR-0012 P1: never folded into validate_work_item's dispatcher,
-- this check is orthogonal to every one of that dispatcher's leaf concerns and shares no state
-- with any of them, and shares no state with s48's own sibling trigger either -- TWO separate
-- triggers on the SAME two columns' SAME field, each independently scoped to its own token
-- sub-shape, exactly the "third/fourth sibling, never a competing factoring" precedent ADR-0012
-- P1 already established). Scope, deliberately identical to s48's own (spec's own words): ONLY
-- kind IN ('work_closed', 'work_violation_disposition') (the close-family kinds that carry
-- work_review_ref at all -- work_review_ref_kind_shape, s29/s37, already forecloses every other
-- kind from a non-NULL value there), and ONLY the review-witness field itself (work_review_ref)
-- -- NEVER the generic `refs` column (WK1-c's scope boundary, re-affirmed here rather than
-- silently re-litigated: prose citation of future/foreign rows stays legal everywhere else, this
-- delta touches nothing there). Tokens matching `artifact:<64-hex>` inside work_review_ref are
-- extracted; the CANDIDATE extraction is deliberately GREEDY on the delimiter, not on the hex
-- shape (`artifact:([^\s,]*)`, 'g' -- everything up to the next whitespace/comma/end-of-string,
-- INCLUDING an empty capture when `artifact:` is followed immediately by a delimiter or nothing)
-- so that a MALFORMED token is CAPTURED, not silently skipped: a hex-anchored extraction pattern
-- (e.g. `artifact:([0-9a-f]{64})`) would simply fail to match a too-short, too-long, or
-- wrong-alphabet token and let it through as though it were prose -- exactly the "a witness token
-- that parses as neither arm is not silently demoted to prose" refusal the spec's own Mechanism
-- section names. Each captured candidate is then classified in two steps: (1) SHAPE -- does it
-- match `^[0-9a-f]{64}$` (the SAME shape kernel.artifact's own artifact_hash_shape CHECK enforces,
-- s51 -- one hex-hash currency, project-wide, never a second one authored here)? If not, refused
-- as MALFORMED, naming the offending token verbatim. (2) EXISTENCE -- for a shape-valid
-- candidate, does `kernel.artifact` (read via the trigger's own `:"kern"` search_path member,
-- the SAME unqualified-table-name idiom s51's own artifact_write body already uses) hold a row
-- with that hash? If not, refused as MISSING, naming the hash and the put-first corrective
-- (`./legacy/led artifact put <file>`, then cite the printed hash -- s51's own documented CLI
-- surface, MECHANISM item 3, "put prints the hash").
--
-- HISTORY: safe -- ONE new object (a standalone BEFORE INSERT trigger function), ADDED beside
-- the existing validate_* family (now including s48's own sibling), calling nothing and touching
-- no pre-existing function/view/column. No table, column, kind, or CHECK constraint of any kind
-- is added or altered. The new trigger reads ONLY `kernel.artifact` (s51's own table, read-only
-- SELECT -- the same grant every :"role" already holds per s51 Element 1's own
-- `GRANT SELECT ON :"kern".artifact TO :"role"`, so this trigger needs no new grant of its own)
-- for hash existence, never mutating it. No pre-existing row's legality changes: a row whose
-- artifact-witness citation was already valid (because the hash was, in fact, already stored)
-- stays valid; a row that would have been accepted before this delta with a DANGLING or
-- MALFORMED artifact citation is now refused, which is this delta's own point, not a regression
-- -- and no PRE-s52 world's data is retroactively judged (this delta governs INSERTs from its own
-- application forward only, the standing trigger-refusal posture every prior delta in this
-- lineage shares). s48's own sibling trigger (row:<id> existence) is entirely untouched --
-- TWO independent triggers fire on the same BEFORE INSERT event, each scoped to its own token
-- sub-shape, neither reads nor writes any state the other owns.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 amendment; spec's own Mechanism section):
--
--   - INVARIANT: a work_closed or work_violation_disposition row whose work_review_ref carries
--     one or more `artifact:<token>` occurrences is admitted iff every such token is BOTH
--     shape-valid (matches `^[0-9a-f]{64}$`, the SAME 64-lowercase-hex currency
--     kernel.artifact.hash's own CHECK enforces) AND names a hash that already exists in
--     `kernel.artifact` at INSERT time -- an artifact-witness citation with a dangling or
--     malformed evidence pointer is unrepresentable, not merely discouraged.
--
--   - QUANTIFICATION UNIVERSE (enumerated OUTWARD, ADR-0000's 2026-07-02 amendment text):
--       TABLES reachable off :"schema"/:"kern": unchanged -- no new base table, no new column.
--         The check rides the EXISTING work_review_ref column (s29) and the EXISTING
--         kernel.artifact table (s51), nothing new to enumerate.
--       EVERY KIND THAT CARRIES work_review_ref: unchanged -- exactly the two kinds s29/s37
--         already license (work_closed, work_violation_disposition); this delta narrows WHICH OF
--         THOSE ROWS are admitted, it does not widen which kinds may carry the column.
--       VIEWS re-read for the wildcard/column-complete class (s20/s22/.../s51 all named):
--         ledger_current / countersigned_in_force -- unchanged, this delta adds no column and
--         reads neither view at all (the check reads kernel.artifact directly, by design, above)
--         -- re-verified NOT members needing re-issue. work_item_current -- unchanged, re-
--         verified NOT a member: this delta touches no work-item-state derivation, only the
--         artifact-witness citation's own referential integrity.
--       KIND VOCABULARY -- unchanged. No new `kind` value.
--       SCOPE BOUNDARY, named (not a silent narrowing, spec's own words): `refs` (the GENERIC
--         citation column) is DELIBERATELY NOT checked by this delta -- prose citation of a
--         future/foreign artifact hash stays legal everywhere it always was (WK4 below is this
--         delta's own scope-boundary witness, the WK1-c precedent one arm over). Only the
--         review-witness POSITION (work_review_ref, on the two close-family kinds) is load-
--         bearing evidence in the sense this delta forecloses. The `row:<id>` sub-shape (s48's
--         own surface) and the commit-hash sub-shape (s38's own git-existence CLI-side
--         machinery, s48's own named non-goal) are BOTH untouched by this delta -- it adds
--         exactly one new checked sub-shape, `artifact:<hash>`, beside s48's existing one.
--       GRANTS -- unchanged. The new trigger function needs no explicit GRANT beyond the
--         pre-existing SELECT on kernel.artifact every :"role" already holds (s51 Element 1); a
--         trigger function fires under the table owner's/trigger's own execution context, the
--         s19/s43/s48 discipline.
--       ENGINE -- VERIFIED, not merely asserted: this delta adds NO new predicate, NO new fact
--         emission, and touches NEITHER engine/ledger_edb.py NOR any engine/lp/*.lp file NOR
--         engine/ledger_floor.py at all -- it is a PURE construction-time refusal (a row that
--         fails this check is simply never written; there is no admitted-row shape for the
--         ASP/SQL floor to diverge over -- s30/s39/s47/s48's own "construction-time-only"
--         precedent, re-applied). Per the spec's own honesty rule: `./judge`'s differential is
--         checked for whether it covers this trigger's surface; if it does not (this delta emits
--         no ledger-visible predicate a differential run could observe diverging over), the
--         witness records UNEXERCISED-with-reason, never a vacuous AGREE (s51's own precedent for
--         this exact posture, its run_fixtures.py's own "NOT WITNESSED HERE, NAMED" section).
--
--   - DENOMINATION: unchanged. `artifact:<hash>` stays the existing bare-reference citation
--     vocabulary (s29's own COMMENT ON COLUMN work_review_ref: "a ledger row id, commit hash, or
--     artifact path"); "exists" is denominated in kernel.artifact.hash membership, the SAME
--     currency kernel.artifact's own PK already is -- never a proxy (e.g. a row COUNT, or a
--     cached high-water mark) for the fact that actually matters here. The hex-shape check is
--     denominated in the SAME `^[0-9a-f]{64}$` pattern kernel.artifact's own artifact_hash_shape
--     CHECK (s51) already enforces -- one hash-shape currency, project-wide, not a second one
--     minted here.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): CLASS-RATIFIED FAIL-SAFE.
-- This delta ONLY adds ONE refusal (a work_closed/work_violation_disposition INSERT whose
-- work_review_ref cites a missing-or-malformed artifact:<hash> is refused) -- nothing existing is
-- relaxed, no column/kind/CHECK is added or widened, the dispatcher is untouched, s48's own
-- sibling trigger is untouched. Per the standing ruling this qualifies for entry into the birth
-- chain without a per-delta maintainer question, PENDING the scratch-witness-on-both-polarities
-- this delta's own commissioning spec's "Witnesses" list requires and this file's own witness
-- pass performs (named here for the record, not claimed as a bypass of that witness).
--
-- LIMITS (pre-registered, matching s22/.../s48's own disclosure convention):
--   - Only the `artifact:<64-hex>` sub-shape of work_review_ref is checked by this delta; the
--     `row:<id>` sub-shape stays s48's own, untouched here, and the commit-hash sub-shape stays
--     s48's own named non-goal (s38's CLI-side git-existence machinery, never checked in SQL) --
--     this delta closes exactly the one gap s48's own LIMITS and s51's own CLOSURE STATEMENT
--     both named as the anticipated successor, nothing wider.
--   - `refs` (the generic citation column) is deliberately OUT OF SCOPE everywhere (see the
--     SCOPE BOUNDARY note above) -- exercised as WK4 in this delta's own fixture.
--   - Existence is checked against `kernel.artifact` membership ONLY -- this delta does not
--     re-verify the referenced bytes' own integrity (a corrupted-in-place row, the s51 WA6 named
--     gap) at citation time; that backstop is `led artifact get`'s own hash-on-read verification
--     (s51 MECHANISM item 3), unchanged and un-re-implemented here.
--   - Like every trigger-enforced refusal in this lineage, this refusal binds ONLY the granted
--     `:role`'s ordinary write path -- a schema-owner/superuser with DDL privilege can disable a
--     trigger or write directly, the same disclosed bound s26/s28/.../s48 already name.
--   - Worlds whose chain carries s48 but not s51 are impossible forward (both ride the same
--     chain going forward) and out of scope backward (runs are linear, 2026-07-11 ruling) -- this
--     delta REQUIRES s51 applied first (kernel.artifact must exist for the trigger's own SELECT
--     to resolve); applying this file on a pre-s51 kernel accepts this file's own DDL (plpgsql
--     does not early-bind table references inside a function body), but the FIRST INSERT that
--     reaches the artifact: branch fails loudly with an undefined-table error -- the correct,
--     disclosed failure mode for a hard dependency on an object this file does not itself create,
--     named here rather than silently assumed to fail at DDL time.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s51): schema/kern/role are
-- psql variables so this delta is VALIDATED on a throwaway substrate before any real apply.
--   VALIDATE (reachable throwaway; scratch CHAIN order matches gates/ledger_reader_allowlist.py's
--   and gates/kind_shape_manifest_gate.py's own extended CHAIN, s52 appended immediately after
--   s51 per the HEAD-BODY RULE s44/s46/s47/s48 already established):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s52val -v kern=s52val_kernel -v role=s52val_rw \
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
--        -f s52-artifact-witness-check.sql
--     (provision a genesis seed per s26's own block before the first ledger INSERT, or that
--     trigger refuses loudly -- this delta adds no genesis requirement of its own.)
--   REAL: NEVER applied to any existing world by this delta's own authoring act (maintainer
--   ruling 2026-07-11, "runs are strictly linear"). This delta reaches reality by entering a
--   FUTURE world's birth chain, wired into `bootstrap/new-project.sh`'s `LINEAGE_CHAIN` as the
--   MAINTAINER's own act at that future world's --new-world run (s47/s48's own precedent) -- NOT
--   wired into LINEAGE_CHAIN by this authoring pass -- birth-chain entry is the maintainer's act.
--   Authored and scratch-witnessed on scratch schema pairs in the TOY db only -- NOT applied to
--   any live schema by this pass, and NEVER written into omega1 or any other existing world.
-- Run as the schema owner (bork). Idempotent (CREATE OR REPLACE FUNCTION; DROP+CREATE TRIGGER).
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
-- ELEMENT 1 -- validate_artifact_witness_existence: a NEW, standalone BEFORE INSERT trigger (the
-- s43/s48 validate_supersession_target/validate_review_witness_existence idiom -- a single-
-- purpose write-boundary trigger added beside the existing validate_* family, never folded into
-- validate_work_item's dispatcher, ADR-0012 P1 -- this check shares no state with any of that
-- dispatcher's lifecycle leaves, nor with s48's own sibling trigger).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_artifact_witness_existence() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_token text;
  v_found text;
BEGIN
  -- Scope, deliberately narrow and IDENTICAL to s48's own scope (spec Mechanism section,
  -- verbatim): ONLY the two close-family kinds that carry work_review_ref at all
  -- (work_review_ref_kind_shape, s29/s37, already forecloses every other kind from a non-NULL
  -- value here -- this IF restates an existing invariant, it does not mint a new one), and ONLY
  -- the review-witness field itself -- never the generic `refs` column (WK4: prose citation of
  -- future/foreign artifact hashes stays legal everywhere else).
  IF NEW.kind IN ('work_closed', 'work_violation_disposition')
     AND NEW.work_review_ref IS NOT NULL THEN
    -- Extraction is GREEDY on the delimiter (whitespace/comma/end), never anchored on the hex
    -- shape itself -- a hex-anchored pattern would silently fail to match (and thus silently
    -- SKIP) a too-short, too-long, or wrong-alphabet token, letting a malformed witness citation
    -- through unrefused. Capturing everything up to the next delimiter (including an EMPTY
    -- capture when 'artifact:' is followed immediately by a delimiter or nothing) means every
    -- 'artifact:' occurrence is classified, none silently demoted to prose.
    FOR v_token IN
      SELECT (regexp_matches(NEW.work_review_ref, 'artifact:([^\s,]*)', 'g'))[1]
    LOOP
      IF v_token !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION 'Ledger policy: artifact-witness citation ''artifact:%'' in work_review_ref is refused — the token after the ''artifact:'' prefix is not a well-formed 64-character lowercase-hex SHA-256 digest (checked at INSERT time; review-witness position only, close-family kinds work_closed/work_violation_disposition -- s52). A witness token that parses as neither a valid row: nor a valid artifact: form is refused, not silently treated as prose. Cite the EXACT hash printed by ''./legacy/led artifact put <file>'' (kernel/lineage/s51-artifact-store.sql), or use --review-witness row:<id> / --review-deferred / --review-bookkeeping instead.',
          v_token;
      END IF;
      SELECT hash INTO v_found FROM artifact WHERE hash = v_token;
      IF v_found IS NULL THEN
        RAISE EXCEPTION 'Ledger policy: artifact-witness citation ''artifact:%'' in work_review_ref is refused — no artifact with that hash exists in kernel.artifact (checked at INSERT time; review-witness position only, close-family kinds work_closed/work_violation_disposition -- s52). The artifact store (kernel/lineage/s51-artifact-store.sql) is content-addressed: a witness citation naming bytes the store never received is a claim with a dangling evidence pointer, in the one place evidence pointers are load-bearing. Register the bytes FIRST — ''./legacy/led artifact put <file>'' — then cite the hash it prints (--review-witness artifact:<hash>).',
          v_token;
      END IF;
    END LOOP;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_artifact_witness_existence ON :"schema".ledger;
CREATE TRIGGER validate_artifact_witness_existence BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_artifact_witness_existence();

COMMENT ON FUNCTION :"schema".validate_artifact_witness_existence() IS
  'kernel/lineage/s52-artifact-witness-check.sql: a work_closed/work_violation_disposition row
   whose work_review_ref carries one or more artifact:<token> occurrences is refused unless every
   token is a well-formed 64-character lowercase-hex SHA-256 digest that already exists in
   kernel.artifact at INSERT time (s51''s content-addressed store). Malformed hex after the
   artifact: prefix refuses with the same shape as a missing hash -- a witness token that parses
   as neither the row: nor the artifact: form is refused, not silently demoted to prose. Scoped
   to the review-witness position on the two close-family kinds only -- prose `refs` citations of
   future/foreign hashes stay legal everywhere else, and s48''s own row:<id> sibling trigger is
   untouched (design/FABLE-ARTIFACT-WITNESS-CHECK-SPEC.md, ledger row 1673 item 2).';
-- ============================================================================================
