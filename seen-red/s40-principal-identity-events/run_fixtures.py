#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for kernel/lineage/s40-principal-identity-events.sql
(design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md §6 witness plan, as amended by C6 -- the
s40 slice; the s41 slice lives in seen-red/s41-principal-bindings-and-relations/). Real infra,
no mocks: CLASSIC-mode scaffolds (explicit --schema/--kern/--role, manual lineage apply in the
TOY db -- the s30..s39 scaffold_classic idiom), one REAL --new-world scaffold run, torn down
before AND after so re-running leaves no residue. Every refusal is witnessed on BOTH polarities,
red first (a gate never seen red is a claim -- ADR-0011's 2026-07-02 amendment).

WORLDS:
  WORLD A -- chain ends at s39 (s40 NOT applied): the detect sibling's f-polarity, and the
             pre-s40 contrast (a NULL-actor write lands silently under the default principal).
  WORLD B -- chain ends at s40, capped (unchanged): detect-t-on-s40 plus the one raw-SQL case
             (bare-anchor-refused-at-commit) that genuinely needs to predate s43 -- s43 revokes
             the role's raw INSERT grant on kernel.principal outright, foreclosing the very
             attempt this case exists to witness on any later chain.
  WORLD B2 -- cluster-1 fixture-repairs (ledger rows 1459/1464/1471): full current lineage
             (s40 through the head) + a served boundary standing over it -- every OTHER s40
             red/green polarity lives here now (moved off WORLD B, which cannot honestly serve
             both a pre-s43 raw-SQL leg and a served-boundary leg on the same schema/role).
  WORLD NW -- a REAL `bootstrap/new-project.sh --new-world` scaffold run on a scratch target,
             now also served (cluster-1 fixture-repairs -- it scaffolded the full chain
             already, but its own `led()` call had no served boundary standing over it): the
             birth sequence's FOUR explicit acts (author/reviewer/commissioner/write-boundary,
             s43 adds the fourth) land as events, TWO standing declarations land (s43's own
             dual declaration: granted role + login role), and the world's first ordinary
             ./led write succeeds with NO LED_ACTOR set (strict-on, zero friction -- the
             ratified reconciliation, witnessed end-to-end).

Cases (each names the witness that would show it false):
  detect-f-on-s39 / detect-t-on-s40  -- the .detect.sql sibling, both polarities.
  pre-s40-silent-default             -- WORLD A: a NULL-actor write lands under 'author' with no
                                        refusal (the undeclared-fallback class s40 forecloses),
                                        witnessed live before s40 exists anywhere. Written as a
                                        direct role-scoped raw INSERT (cluster-1 fixture-repairs:
                                        `led` is now boundary-only and standing a boundary here
                                        would require s43, which cannot exist pre-s40 without
                                        erasing the case) -- not an era-witness conversion, a
                                        write-path swap only; the kernel fact under test is
                                        unchanged and world_a's raw INSERT grant is still intact.
  bare-anchor-refused-at-commit      -- WORLD B: INSERT INTO principal with no same-transaction
                                        registration event cannot COMMIT (deferred trigger). Kept
                                        on the capped, pre-s43 WORLD B deliberately (see WORLD B's
                                        own note above).
  undeclared-write-refused           -- WORLD B2: NULL-actor write, no standing declaration ->
                                        refused with the declare-standing teach-text (this is
                                        ALSO the table->view gap-window polarity: refused, never
                                        misattributed).
  declared-write-resolves            -- WORLD B2: after `led principal declare-standing`, the
                                        same NULL-actor write resolves to the declared principal
                                        (the never-refuses leg) and carries
                                        principal_actor_resolution='declared-default' (C6 i).
  explicit-write-marked              -- WORLD B2: a LED_ACTOR write carries 'explicit' (C6 i).
  register-duplicate-same-class /
  register-duplicate-class-mismatch  -- WORLD B2: GENUINE RESIDUAL RED, found running this
                                        fixture, unrelated to the s43 cascade -- see the inline
                                        comment at these two cases' own call sites for the full
                                        root cause (bootstrap/templates/led.tmpl's register-
                                        principal has no client-side duplicate check, and
                                        kernel.registration_write's own catch-all surfaces a raw
                                        postgres uniqueness-violation string, never the s40-
                                        designed teach text these cases' names describe). Left
                                        asserting the TRUE designed behavior (never weakened);
                                        out of this commission's scope to fix (bootstrap/ is
                                        off-limits here).
  purpose-optional-with-placeholder  -- WORLD B2 (RENAMED from "purpose-mandatory", dated
                                        2026-07-27): register-principal without --purpose
                                        SUCCEEDS with a placeholder purpose string -- a ratified,
                                        already-shipped design decision (bootstrap/templates/
                                        led.tmpl's own dated comment, design/FABLE-LEGACY-LED-
                                        RETIREMENT-SPEC.md Part C completion, row 1158/1159),
                                        predating this migration and unrelated to it; the
                                        original "refused without --purpose" assertion was
                                        simply stale.
  suspend-refuses-writes             -- WORLD B2: write under a suspended principal refused,
                                        naming the standing event row id.
  revoke-refuses-writes / successor-passes -- WORLD B2: revoked principal's writes refuse;
                                        a fresh successor principal's writes pass (the only v1
                                        reinstatement path, witnessed as what it is).
  precedence-both-orders             -- WORLD B2: suspend-then-revoke AND revoke-then-suspend
                                        (two subjects) -> principal_standing() = 'revoked' in
                                        both construction orders.
  rotation                           -- WORLD B2: a second declare-standing supersedes the first;
                                        the principal_role view shows EXACTLY the new binding for
                                        that db_role (C6 ii).
  anchor-append-only                 -- WORLD B2: UPDATE/DELETE on kernel.principal refused
                                        (s43 revokes INSERT only, never UPDATE/DELETE -- this
                                        stays a trigger-level refusal, unaffected by the chain
                                        extension).
  gates-green                        -- gates/ledger_reader_allowlist.py + gates/
                                        kind_shape_manifest_gate.py both exit 0 on their own
                                        standing CHAINs (which include s40 as of this commit).
  differential-agree-both-layers     -- WORLD B2 (carrying all four s40 kinds): the STANDING
                                        ./judge differential (tnow + work layers) AGREEs -- the
                                        new kinds flow through entry/6 generically, witnessed
                                        not asserted.
  new-world-birth-sequence           -- WORLD NW: the FOUR birth acts land as events, TWO
                                        standing declarations land (s43's dual declaration);
                                        first ordinary ./led write succeeds with no LED_ACTOR.

Usage: python3 seen-red/s40-principal-identity-events/run_fixtures.py
Exit 0 if every case matches; 1 otherwise (register-duplicate-same-class/register-duplicate-
class-mismatch are EXPECTED to still fail -- see their own note above, a real, out-of-scope CLI
gap this migration did not introduce and cannot fix within its own boundaries).
Lazy imports banned."""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
LINEAGE = REPO / "kernel" / "lineage"
ENGINE = REPO / "engine"
sys.path.insert(0, str(ENGINE))
sys.path.insert(0, str(REPO / "filing"))

import ledger_differential  # noqa: E402
import ledger_edb  # noqa: E402
import pghost_resolve  # noqa: E402

# cluster-1 fixture-repairs (ledger rows 1459/1464/1471): the served `led` shim now
# unconditionally refuses a deployment.json missing boundary_url/boundary_deployment, and the
# served boundary itself refuses every write with 409 capability_absent unless the schema
# carries the s43 kernel-lineage delta. WORLD B below drives real `led()` dispatcher writes
# (register-principal/declare-standing/suspend/revoke/etc), so it needs a REAL served boundary
# standing over a schema that carries s43 -- REUSE (ADR-0012 P1) serve_existing_world/
# stop_server, the s26-row-hash-chain-deletion pattern, rather than re-implementing.
_BS_SPEC = importlib.util.spec_from_file_location(
    "boundary_service_fixtures", REPO / "seen-red" / "boundary-service" / "run_fixtures.py")
assert _BS_SPEC is not None and _BS_SPEC.loader is not None
bs_fixtures = importlib.util.module_from_spec(_BS_SPEC)
sys.modules["boundary_service_fixtures"] = bs_fixtures
_BS_SPEC.loader.exec_module(bs_fixtures)

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own
# environment before any subprocess is spawned -- inherited by the whole process tree
# this fixture starts, so every repo-root verb invocation anywhere downstream carries it.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

PGHOST, PGDB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_COMMON = [
    "s15-schema.sql", "s17-stamp-mechanism.sql", "s17-independence-vocabulary.sql",
    "s19-trigger-search-path.sql", "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
    "s25-commission-kind.sql", "s26-row-hash-chain.sql", "s27-chain-high-water.sql",
    "s28-work-parent-edge.sql", "s29-obligation-item-key-and-typed-close.sql",
    "s30-typed-dependency-edges.sql", "s31-supersession-uniform-retraction.sql",
    "s32-edge-views-single-home.sql", "s33-composite-discharge.sql",
    "s34-computed-grade-refusal.sql", "s35-validation-decomposition.sql",
    "s36-decision-grade.sql", "s37-violation-disposition.sql",
    "s38-bookkeeping-close.sql", "s39-blocks-start.sql",
]
CHAIN_A = CHAIN_COMMON
# WORLD B stays capped EXACTLY at s40 (unchanged) -- it hosts the two cases that need a raw,
# unmediated SQL path into kernel.principal (bare-anchor-refused-at-commit's whole point is
# probing what a bypass-the-ceremony INSERT does; the s43 write boundary REVOKES INSERT on
# kernel.principal outright -- see s43's own Element 7 -- so on any chain carrying s43 that raw
# INSERT gets "permission denied" a full step before it would ever reach the deferred trigger
# this case exists to witness. Verified empirically: run 1 of this fixture's own migration hit
# exactly that message once CHAIN_B was (wrongly) pushed past s43. This is the genuine
# "assertion depends on an earlier generation" case ledger row 1471 anticipates -- not a
# candidate for full-chain migration without erasing what it tests.
CHAIN_B = CHAIN_COMMON + ["s40-principal-identity-events.sql"]
# WORLD B2 -- cluster-1 fixture-repairs (ledger rows 1459/1464/1471): every OTHER s40 red/green
# case drives a real `led()` dispatcher write (register-principal/declare-standing/suspend/
# revoke/note/work), which now requires a served boundary, which itself refuses (409
# capability_absent) unless the schema carries s43 (and capability detection is a straight
# object-existence probe, not a generation ceiling -- so the full current lineage is what's
# needed, not merely s43). s40 was never a deliberate era ceiling for THESE cases (nothing here
# tests "s40 behavior specifically BEFORE some later generation") -- migrating to the FULL
# current lineage on a SEPARATE world is a pure capability fix, not a weakening: every
# assertion below still holds unchanged (verified by running this fixture, not assumed), since
# scaffold_classic's manual DDL apply -- unlike --new-world -- never births ANY ledger row, so
# the empty-ledger genesis-principal bootstrapping this fixture's own hand-driven 'author'
# registration relies on is untouched by how far past s40 the chain reaches. Kept as a SEPARATE
# world from WORLD B (not CHAIN_B extended in place) precisely because bare-anchor-refused-at-
# commit above needs the OPPOSITE (pre-s43) shape on the SAME schema-role pair -- one schema
# cannot honestly serve both.
CHAIN_B2 = CHAIN_B + [
    "s41-principal-bindings-and-relations.sql",
    "s42-row-hash-full-coverage.sql", "s43-typed-verdict-write-boundary.sql",
    "s44-model-identity-attestation.sql", "s45-standing-lifecycle.sql",
    "s46-credited-views.sql", "s47-claim-on-closed-refusal.sql",
    "s48-review-witness-existence.sql", "s49-journaler-overflow-guard.sql",
    "s50-defeat-input-raw-domain.sql", "s51-artifact-store.sql",
    "s52-artifact-witness-check.sql", "s53-belief-substrate.sql",
    "s54-belief-views.sql", "s55-dispatch-grain-independence.sql",
    "s56-reservation-residue.sql", "s57-obligation-revocation-event.sql",
    "s58-missive-substrate.sql", "s59-missive-views.sql",
    "s60-entitlement-enforcement.sql", "s61-signature-symmetry-and-key-binding.sql",
    "s62-delegation-lifecycle-gating.sql", "s63-supersession-body-restoration.sql",
    "s64-principal-stamps-delegation-conditions.sql",
]


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def teardown(world: str) -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {world} CASCADE; DROP SCHEMA IF EXISTS {world}_kernel CASCADE; "  # declared-drop: scratch reset
        f"DROP OWNED BY {world}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {world}_rw;"])


def led(world_dir: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    e = dict(os.environ)
    if env:
        e.update(env)
    # §6 amendment (2026-07-26, rows 1357/1365/1366/1367): routed through the one dispatcher now.
    return sh(["bash", str(world_dir / "autoharn"), "led", *args], cwd=str(world_dir), env=e)


def psql_tuples(sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"psql failed: {cp.stdout[-500:]} {cp.stderr[-500:]}")
    return cp.stdout.strip()


def psql_raw(script: str) -> subprocess.CompletedProcess[str]:
    """A script allowed to FAIL (red-polarity probes) -- caller inspects returncode/stderr."""
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-f", "/dev/stdin"],
              input=script)


def detect(schema: str, kern: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tA",
             "-v", f"schema={schema}", "-v", f"kern={kern}",
             "-f", str(LINEAGE / "s40-principal-identity-events.detect.sql")])
    return cp.stdout.strip()


def scaffold_classic(world: str, chain: list[str]) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix=f"{world}-seenred-"))
    world_dir = tmp / world
    schema, kern, role = world, f"{world}_kernel", f"{world}_rw"
    r = sh(["bash", str(NEW_PROJECT), str(world_dir),
            "--db", PGDB, "--host", PGHOST,
            "--schema", schema, "--kern", kern, "--role", role])
    if r.returncode != 0:
        raise RuntimeError(f"CLASSIC SCAFFOLD FAILED ({world}): {r.stdout[-1500:]} {r.stderr[-1500:]}")
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}"]
    for name in chain:
        args += ["-f", str(LINEAGE / name)]
    ra = sh(args)
    if ra.returncode != 0:
        raise RuntimeError(f"CLASSIC apply FAILED ({world}, chain ends {chain[-1]}): "
                           f"{ra.stdout[-1500:]} {ra.stderr[-1500:]}")
    hexsecret = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
        "-c", f"TRUNCATE {kern}.stamp_secret;",
        "-c", f"INSERT INTO {kern}.stamp_secret (secret) VALUES (decode('{hexsecret}','hex'));"])
    genesis_hex = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
        "-c", f"INSERT INTO {kern}.chain_genesis (seed) VALUES ('{genesis_hex}') "
              f"ON CONFLICT (only_one) DO NOTHING;"])
    return world_dir


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    world_a, world_b, world_b2, world_nw = "s40fxa", "s40fxb", "s40fxb2", "s40fxnw"
    for w in (world_a, world_b, world_b2, world_nw):
        teardown(w)
    try:
        # =========================================================================================
        # WORLD A -- s39 head: detect f-polarity + the pre-s40 silent-default contrast.
        # =========================================================================================
        print(f"== scaffolding classic world {world_a} (chain ends {CHAIN_A[-1]}, s40 NOT applied) ==")
        wa = scaffold_classic(world_a, CHAIN_A)
        tmps.append(wa.parent)

        check("detect-f-on-s39", detect(world_a, f"{world_a}_kernel") == "f",
              f"s40 detect sibling on an s39-head chain reads {detect(world_a, f'{world_a}_kernel')!r} (expect f)",
              failures)

        # cluster-1 fixture-repairs (ledger rows 1459/1464/1471): `led()` (the served-CLI
        # dispatcher) now unconditionally refuses without boundary_url/boundary_deployment, and
        # standing a served boundary here would REQUIRE s43 -- which is AFTER s40 in the
        # lineage, so it cannot exist on a chain that stops at s39 without erasing the very
        # thing this case tests ("before s40 exists"). This is NOT an era-witness conversion,
        # though: the claim under test is a KERNEL fact (does the set_actor trigger silently
        # default a NULL-actor write?), not a CLI fact -- and world_a's schema, capped at s39,
        # never had its role's raw INSERT grant revoked (that revocation is s43's own doing).
        # So the fix is a plain write-path swap, same mechanism `bare-anchor-refused-at-commit`/
        # `undeclared-write-refused` below already use for WORLD B's own red-polarity probes:
        # a direct role-scoped INSERT, never the (now boundary-only) `led` CLI.
        ra = psql_raw(f"SET ROLE {world_a}_rw;\nSET search_path = {world_a}, {world_a}_kernel;\n"
                      f"INSERT INTO ledger (kind, statement) VALUES "
                      f"('note', 'pre-s40 contrast: NULL-actor write');\n")
        landed = psql_tuples(f"SELECT p.name FROM {world_a}.ledger l JOIN {world_a}_kernel.principal p "
                             f"ON p.id = l.actor WHERE l.kind='note' ORDER BY l.id DESC LIMIT 1;")
        check("pre-s40-silent-default", ra.returncode == 0 and landed == "author",
              f"WORLD A (pre-s40): NULL-actor raw INSERT exit={ra.returncode}, landed under "
              f"{landed!r} with no refusal anywhere -- the undeclared silent fallback s40 "
              f"forecloses, witnessed live (direct role-scoped INSERT, not the now boundary-"
              f"only `led` CLI -- see comment above)", failures)

        # =========================================================================================
        # WORLD B -- s40 head, capped (unchanged). detect-t-on-s40 + the one raw-SQL case that
        # genuinely needs to predate s43 (bare-anchor-refused-at-commit -- see CHAIN_B's own
        # comment above for why).
        # =========================================================================================
        print(f"== scaffolding classic world {world_b} (chain ends {CHAIN_B[-1]}) ==")
        wb = scaffold_classic(world_b, CHAIN_B)
        tmps.append(wb.parent)
        S, K, R = world_b, f"{world_b}_kernel", f"{world_b}_rw"

        check("detect-t-on-s40", detect(S, K) == "t",
              f"s40 detect sibling on the s40 chain reads {detect(S, K)!r} (expect t)", failures)

        # bare anchor INSERT: cannot COMMIT (deferred trigger) -- this schema predates s43, so
        # the role's raw INSERT grant on kernel.principal is still intact (s43's own Element 7 is
        # what later revokes it); this case witnesses the deferred trigger directly, the ONLY
        # generation on which that grant exists to make the attempt possible at all.
        rb = psql_raw(f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
                      f"INSERT INTO {K}.principal (name, agent_class) VALUES ('bare-bob','model');\n")
        out = rb.stdout + rb.stderr
        check("bare-anchor-refused-at-commit",
              rb.returncode != 0 and "BARE principal registration is unrepresentable" in out
              and psql_tuples(f"SELECT count(*) FROM {K}.principal WHERE name='bare-bob';") == "0",
              f"exit={rb.returncode}; teach excerpt={out.strip()[-200:]!r}; no anchor row landed",
              failures)

        # =========================================================================================
        # WORLD B2 -- full current lineage (s40 through the head), a served boundary standing
        # over it. Every OTHER s40 red/green case lives here (see CHAIN_B2's own comment above
        # for why this is a separate world from WORLD B, not CHAIN_B extended in place).
        # =========================================================================================
        print(f"== scaffolding classic world {world_b2} (chain ends {CHAIN_B2[-1]}) ==")
        wb2 = scaffold_classic(world_b2, CHAIN_B2)
        tmps.append(wb2.parent)

        # cluster-1 fixture-repairs (ledger rows 1459/1464/1471): every case below drives real
        # led()/dispatcher writes (register-principal/declare-standing/suspend/revoke/note/work)
        # -- these need a REAL served boundary standing over this EXACT schema (CHAIN_B2 reaches
        # s43 and beyond, so the capability the boundary probes for is present). Matches the
        # s26-row-hash-chain-deletion guard shape verbatim: any failure between serve and this
        # function's own return must not leak the boundary-service subprocess.
        proc_b2 = bs_fixtures.serve_existing_world(wb2 / "deployment.json", wb2.parent)
        try:
            S2, K2, R2 = world_b2, f"{world_b2}_kernel", f"{world_b2}_rw"

            # birth acts, hand-driven (the scaffold's own scripted form is witnessed on WORLD NW).
            # cluster-1 fixture-repairs: s43's own Element 7 revokes the role's raw INSERT grant
            # on ledger/kernel.principal outright, so the ORIGINAL raw-INSERT form of this act
            # (still used by WORLD A/WORLD B above, both pre-s43) now gets "permission denied"
            # here. Fixed by routing through kernel.ledger_write(jsonb) -- the SAME SECURITY
            # DEFINER boundary function bootstrap/new-project.sh's own --new-world birth
            # sequence (step 1) uses for this exact genesis exception, self-attributed for the
            # identical reason: no earlier-registered principal exists yet to attribute it to.
            r1 = psql_raw(
                f"SET ROLE {R2};\nSET search_path = {S2}, {K2};\n"
                f"DO $bw$\nDECLARE v {K2}.write_verdict;\nBEGIN\n"
                f"  SELECT * INTO v FROM {K2}.ledger_write(jsonb_build_object(\n"
                f"    'kind', 'principal_registered',\n"
                f"    'statement', 'principal ''author'' registered (class model) -- fixture "
                f"genesis exception: self-attributed, the first identity event of this "
                f"fixture''s hand-driven world (no earlier-registered principal exists to "
                f"attribute it to)',\n"
                f"    'actor', (SELECT id FROM principal WHERE name='author'),\n"
                f"    'principal_subject', (SELECT id FROM principal WHERE name='author'),\n"
                f"    'principal_purpose', 'fixture connection principal'));\n"
                f"  IF v.disposition <> 'accepted' THEN\n"
                f"    RAISE EXCEPTION 'author registration event refused (SQLSTATE %): %', "
                f"v.sqlstate, v.message;\n"
                f"  END IF;\n"
                f"END $bw$;\n")
            if r1.returncode != 0:
                raise RuntimeError(f"author registration event failed: {r1.stdout[-500:]} {r1.stderr[-500:]}")

            # cluster-1 fixture-repairs (found running this fixture, not assumed): s43 Element 6
            # requires a registered 'write-boundary' tool principal to AUTHOR every write_refused
            # journal row -- absent it, a REFUSED write (which every red-polarity case below
            # deliberately triggers) itself 500s inside journal_write_refusal, never reaching a
            # clean kernel verdict at all (witnessed live: "the 'write-boundary' tool principal
            # is not registered in this world"). bootstrap/new-project.sh's own s40/s43 birth
            # sequence registers this principal (step 4) via registration_write(), actor=author,
            # explicit -- mirrored here verbatim, BEFORE the first refused write below (order
            # matters: this is a NEW required bootstrap element s43 adds, not present when this
            # fixture was first authored pre-s43).
            r0wb = psql_raw(
                f"SET ROLE {R2};\nSET search_path = {S2}, {K2};\n"
                f"DO $bw$\nDECLARE v {K2}.write_verdict;\nBEGIN\n"
                f"  SELECT * INTO v FROM {K2}.registration_write(jsonb_build_object(\n"
                f"    'name', 'write-boundary', 'agent_class', 'tool',\n"
                f"    'purpose', 'the kernel write boundary''s own recording identity: every "
                f"write_refused meta-event is authored by this principal (fixture bootstrap, "
                f"mirrors bootstrap/new-project.sh''s s43 birth sequence step 4)',\n"
                f"    'statement', 'principal ''write-boundary'' registered (class tool) -- "
                f"fixture bootstrap, registrar: author',\n"
                f"    'actor', (SELECT id FROM principal WHERE name='author')));\n"
                f"  IF v.disposition <> 'accepted' THEN\n"
                f"    RAISE EXCEPTION 'write-boundary registration refused (SQLSTATE %): %', "
                f"v.sqlstate, v.message;\n"
                f"  END IF;\n"
                f"END $bw$;\n")
            if r0wb.returncode != 0:
                raise RuntimeError(f"write-boundary registration failed: {r0wb.stdout[-500:]} {r0wb.stderr[-500:]}")

            # undeclared write refused (also the table->view gap-window polarity: refused, never
            # misattributed -- no standing declaration exists yet on this hand-driven chain for
            # the CONNECTING role -- registering author/write-boundary above declares no standing
            # for it, so this premise is untouched by the reordering above)
            ru = led(wb2, "note", "undeclared write, should refuse")
            out = ru.stdout + ru.stderr
            check("undeclared-write-refused",
                  ru.returncode != 0 and "strict attribution (s40)" in out
                  and "declare-standing" in out,
                  f"exit={ru.returncode}; teach excerpt={out.strip()[-200:]!r}", failures)

            rd = led(wb2, "principal", "declare-standing", "author", env={"LED_ACTOR": "author"})
            if rd.returncode != 0:
                raise RuntimeError(f"declare-standing failed: {rd.stdout[-500:]} {rd.stderr[-500:]}")

            # cluster-1 fixture-repairs (found running this fixture, not assumed): s43's own
            # dual declaration (Element 8) is load-bearing here in a way it never was pre-
            # boundary -- `serving/boundary_service.py`'s own `_psql` connects as the SAME OS
            # login every psql invocation in this process uses (no per-role authentication;
            # `SET ROLE :role` changes CURRENT_USER only), so `set_actor`'s strict-attribution
            # resolution (keyed on SESSION_USER, s43's own re-issue) sees the LOGIN role, never
            # R2 -- the declare-standing call just above (implicit --db-role, defaults to R2)
            # governs the `rotation` case's view-content assertion below (unchanged, matches the
            # original design) but is NEVER what a served write actually resolves through. This
            # mirrors bootstrap/new-project.sh's own s40/s43 birth sequence exactly (its "for
            # _drole in $ROLE $LOGIN_ROLE" loop, step 2 -- see that script's own comment), just
            # hand-driven: without this second declaration, every no-LED_ACTOR write below
            # (declared-write-resolves and the register-principal calls that follow it) still
            # refuses "login role '<login>' has no standing declaration" -- witnessed live while
            # building this migration.
            login_role = psql_tuples("SELECT session_user;")
            rd2 = led(wb2, "principal", "declare-standing", "author", "--db-role", login_role,
                      env={"LED_ACTOR": "author"})
            if rd2.returncode != 0:
                raise RuntimeError(f"declare-standing (login role {login_role!r}) failed: "
                                   f"{rd2.stdout[-500:]} {rd2.stderr[-500:]}")

            # never-refuses leg + C6(i) declared-default mark
            rg = led(wb2, "note", "declared default write")
            row = psql_tuples(f"SELECT p.name || '|' || l.principal_actor_resolution FROM {S2}.ledger l "
                              f"JOIN {K2}.principal p ON p.id = l.actor "
                              f"WHERE l.statement = 'declared default write';")
            check("declared-write-resolves", rg.returncode == 0 and row == "author|declared-default",
                  f"NULL-actor write exit={rg.returncode}, resolved+marked {row!r} "
                  f"(expect author|declared-default)", failures)

            # register reviewer2 through the ceremony (green), then C6(i) explicit mark
            rr2 = led(wb2, "register-principal", "reviewer2", "model",
                      "--purpose", "fixture reviewer principal")
            if rr2.returncode != 0:
                raise RuntimeError(f"register reviewer2 failed: {rr2.stdout[-500:]} {rr2.stderr[-500:]}")
            rx = led(wb2, "note", "explicit actor write", env={"LED_ACTOR": "reviewer2"})
            rowx = psql_tuples(f"SELECT p.name || '|' || l.principal_actor_resolution FROM {S2}.ledger l "
                               f"JOIN {K2}.principal p ON p.id = l.actor "
                               f"WHERE l.statement = 'explicit actor write';")
            check("explicit-write-marked", rx.returncode == 0 and rowx == "reviewer2|explicit",
                  f"LED_ACTOR write exit={rx.returncode}, resolved+marked {rowx!r} "
                  f"(expect reviewer2|explicit)", failures)

            # duplicate registration, both class polarities (red). GENUINE RESIDUAL RED, found
            # running this fixture, NOT part of the s43 cascade this migration exists to fix and
            # NOT weakened here: kernel.registration_write (kernel/lineage/s43-typed-verdict-
            # write-boundary.sql, read in full) does a bare `INSERT INTO principal` with no
            # pre-check at all, catching the resulting unique_violation generically and
            # surfacing postgres's own raw "duplicate key value violates unique constraint..."
            # text; grepping the whole tree (bootstrap/templates/led.tmpl, every kernel/lineage/
            # *.sql, serving/*.py) for this case's own expected teach phrases ("already
            # registered", "never a silent no-op", "classes are IMMUTABLE") finds them NOWHERE --
            # the s40-designed friendly duplicate-refusal UX these two cases' own module-
            # docstring lines name ("Axis 6 silent no-op, closed" / "succession teach, classes
            # immutable") does not currently exist on the served CLI path. This is a real gap in
            # bootstrap/templates/led.tmpl's register-principal (or a kernel-side pre-check that
            # was never ported there), out of this commission's scope to fix (bootstrap/ is
            # explicitly off-limits here) and unrelated to capability_absent -- left asserting
            # the TRUE designed behavior (never weakened) so the fixture stays honestly red until
            # a properly-scoped fix lands.
            rds = led(wb2, "register-principal", "reviewer2", "model", "--purpose", "dup")
            outs = rds.stdout + rds.stderr
            check("register-duplicate-same-class",
                  rds.returncode != 0 and "already registered" in outs
                  and "fixture reviewer principal" in outs and "never a silent no-op" in outs,
                  f"exit={rds.returncode}; teach quotes purpose={'fixture reviewer principal' in outs}; "
                  f"excerpt={outs.strip()[-160:]!r}", failures)
            rdm = led(wb2, "register-principal", "reviewer2", "human", "--purpose", "dup")
            outm = rdm.stdout + rdm.stderr
            check("register-duplicate-class-mismatch",
                  rdm.returncode != 0 and "classes are IMMUTABLE" in outm and "succeeds" in outm,
                  f"exit={rdm.returncode}; excerpt={outm.strip()[-160:]!r}", failures)

            # purpose-optional-with-placeholder (RENAMED from "purpose-mandatory", dated
            # 2026-07-27, law/adr/0005 Rule 8): bootstrap/templates/led.tmpl's own
            # `cmd_register_principal`/argparse block for `register-principal` (read in full)
            # carries its OWN dated comment -- "design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part C
            # completion (row 1158/1159): ... `--purpose` is OPTIONAL here exactly as legacy's
            # own grammar treats it (a caller that omits it gets this CLI's own placeholder
            # text)" -- a ratified, ALREADY-SHIPPED design decision predating this migration, not
            # a consequence of the s43 cascade. The original "refused without --purpose"
            # assertion is simply stale against that shipped decision; asserting the CURRENT,
            # real, intentional behavior here (registration succeeds, placeholder purpose lands)
            # is a dated correction of a stale banked expectation, not a weakening of any live
            # refusal (none was ever live on this CLI to begin with).
            rp = led(wb2, "register-principal", "nopurpose", "model")
            outp = rp.stdout + rp.stderr
            purpose_landed = psql_tuples(
                f"SELECT principal_purpose FROM {S2}.ledger WHERE kind='principal_registered' "
                f"AND principal_subject = (SELECT id FROM {K2}.principal WHERE name='nopurpose');")
            check("purpose-optional-with-placeholder",
                  rp.returncode == 0
                  and purpose_landed == "registered via ./autoharn led register-principal",
                  f"exit={rp.returncode}; purpose landed={purpose_landed!r} (expect the CLI's "
                  f"own placeholder text -- --purpose is optional by ratified, already-shipped "
                  f"design, bootstrap/templates/led.tmpl's own dated comment); excerpt="
                  f"{outp.strip()[-140:]!r}", failures)

            # suspend reviewer2 -> its writes refuse, naming the standing event row
            rs = led(wb2, "principal", "suspend", "reviewer2", "fixture suspension",
                     env={"LED_ACTOR": "author"})
            if rs.returncode != 0:
                raise RuntimeError(f"suspend failed: {rs.stdout[-400:]} {rs.stderr[-400:]}")
            rw = led(wb2, "note", "write as suspended", env={"LED_ACTOR": "reviewer2"})
            outw = rw.stdout + rw.stderr
            check("suspend-refuses-writes",
                  rw.returncode != 0 and "is suspended (standing event row" in outw,
                  f"exit={rw.returncode}; excerpt={outw.strip()[-180:]!r}", failures)

            # revoke reviewer2 (suspend-then-revoke order); register successor; successor passes
            rv = led(wb2, "principal", "revoke", "reviewer2", "fixture revocation",
                     env={"LED_ACTOR": "author"})
            if rv.returncode != 0:
                raise RuntimeError(f"revoke failed: {rv.stdout[-400:]} {rv.stderr[-400:]}")
            rwr = led(wb2, "note", "write as revoked", env={"LED_ACTOR": "reviewer2"})
            outr = rwr.stdout + rwr.stderr
            rsucc = led(wb2, "register-principal", "reviewer3", "model",
                        "--purpose", "successor of reviewer2 (fixture)", env={"LED_ACTOR": "author"})
            rws = led(wb2, "note", "write as successor", env={"LED_ACTOR": "reviewer3"})
            check("revoke-refuses-writes / successor-passes",
                  rwr.returncode != 0 and "is revoked (standing event row" in outr
                  and rsucc.returncode == 0 and rws.returncode == 0,
                  f"revoked write exit={rwr.returncode} ({outr.strip()[-120:]!r}); successor "
                  f"registration exit={rsucc.returncode}; successor write exit={rws.returncode}",
                  failures)

            # precedence, both construction orders: reviewer2 was suspend-then-revoke; make a fresh
            # subject for revoke-then-suspend.
            led(wb2, "register-principal", "rts", "model", "--purpose", "revoke-then-suspend subject",
                env={"LED_ACTOR": "author"})
            led(wb2, "principal", "revoke", "rts", env={"LED_ACTOR": "author"})
            led(wb2, "principal", "suspend", "rts", env={"LED_ACTOR": "author"})
            st1 = psql_tuples(f"SELECT {K2}.principal_standing(id) FROM {K2}.principal WHERE name='reviewer2';")
            st2 = psql_tuples(f"SELECT {K2}.principal_standing(id) FROM {K2}.principal WHERE name='rts';")
            check("precedence-both-orders", st1 == "revoked" and st2 == "revoked",
                  f"suspend-then-revoke reads {st1!r}, revoke-then-suspend reads {st2!r} "
                  f"(expect revoked/revoked -- strict severity ordering, both orders)", failures)

            # rotation (C6 ii): re-declare the role's standing to reviewer3; view shows exactly it.
            # declare-standing with no --db-role defaults to R2 (cfg.record.role) -- the SAME
            # implicit default the FIRST declare-standing call above used -- so this rotates
            # R2's own governing row only, leaving the separate login_role row (declared above,
            # the one that actually governs set_actor resolution) untouched; filtered to R2's
            # own row below for exactly that reason (two db_role rows now legitimately coexist
            # in principal_role, not one -- the dual-declaration reality named above).
            rrot = led(wb2, "principal", "declare-standing", "reviewer3", env={"LED_ACTOR": "author"})
            view = psql_tuples(f"SELECT db_role || '|' || p.name FROM {K2}.principal_role pr "
                               f"JOIN {K2}.principal p ON p.id = pr.principal_id "
                               f"WHERE pr.db_role = '{R2}';")
            check("rotation", rrot.returncode == 0 and view == f"{R2}|reviewer3"
                  and "rotating -- superseding standing declaration row" in (rrot.stdout + rrot.stderr),
                  f"exit={rrot.returncode}; principal_role (db_role={R2!r}) now reads {view!r} "
                  f"(expect exactly {R2}|reviewer3, one row); rotation notice printed", failures)
            # rotate BACK to author so the differential below runs under a live default
            led(wb2, "principal", "declare-standing", "author", env={"LED_ACTOR": "author"})

            # anchor append-only (red) -- s43 revokes INSERT on kernel.principal, but NOT
            # UPDATE/DELETE (its own Element 7 names INSERT specifically); the append-only
            # refusal below is a TRIGGER, not a grant, so it still fires here unchanged.
            rup = psql_raw(f"UPDATE {K2}.principal SET agent_class='human' WHERE name='reviewer3';")
            rdel = psql_raw(f"DELETE FROM {K2}.principal WHERE name='reviewer3';")
            check("anchor-append-only",
                  rup.returncode != 0 and rdel.returncode != 0
                  and "append-only" in (rup.stdout + rup.stderr),
                  f"UPDATE exit={rup.returncode}, DELETE exit={rdel.returncode} (both refused)",
                  failures)

            # gates green on their own standing CHAINs (now including s40)
            g1 = sh([sys.executable, str(REPO / "gates" / "ledger_reader_allowlist.py")])
            g2 = sh([sys.executable, str(REPO / "gates" / "kind_shape_manifest_gate.py")])
            check("gates-green", g1.returncode == 0 and g2.returncode == 0,
                  f"ledger_reader_allowlist exit={g1.returncode}; kind_shape_manifest_gate "
                  f"exit={g2.returncode}", failures)

            # the standing ./judge differential, both layers, on WORLD B2 (all four s40 kinds
            # live: registered/suspended/revoked/standing_declared rows all exist above) + a
            # work item so the work layer has substance.
            led(wb2, "work", "open", "s40fx-item", "differential fixture item")
            kinds = psql_tuples(f"SELECT count(DISTINCT kind) FROM {S2}.ledger WHERE kind LIKE 'principal_%';")
            os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"] = \
                PGDB, S2, K2
            try:
                edb_text = ledger_edb.export(S2).edb_text()
                res_tnow = ledger_differential.run_differential(S2, edb_text=edb_text)
                res_work = ledger_differential.run_layer_differential(S2, "work")
            finally:
                del os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"]
            v_tnow, v_work = res_tnow.verdict(), res_work.verdict()
            check("differential-agree-both-layers",
                  v_tnow == "AGREE" and v_work == "AGREE" and kinds == "4",
                  f"tnow={v_tnow} work={v_work} with {kinds} distinct principal_* kinds on the "
                  f"fixture ledger (expect AGREE/AGREE/4)", failures)
        finally:
            bs_fixtures.stop_server(proc_b2)

        # =========================================================================================
        # WORLD NW -- the REAL --new-world scaffold run (basis §6's scaffold leg).
        # =========================================================================================
        print(f"== REAL --new-world scaffold run ({world_nw}) ==")
        tmpnw = Path(tempfile.mkdtemp(prefix=f"{world_nw}-seenred-"))
        tmps.append(tmpnw)
        nwdir = tmpnw / world_nw
        rnw = sh(["bash", str(NEW_PROJECT), str(nwdir), "--new-world", world_nw,
                  "--db", PGDB, "--host", PGHOST])
        events = psql_tuples(
            f"SELECT count(*) FROM {world_nw}.ledger WHERE kind='principal_registered';") if rnw.returncode == 0 else "?"
        decls = psql_tuples(
            f"SELECT count(*) FROM {world_nw}.ledger WHERE kind='principal_standing_declared';") if rnw.returncode == 0 else "?"
        rfirst = None
        first_row = "?"
        if rnw.returncode == 0:
            # cluster-1 fixture-repairs (ledger rows 1459/1464/1471, per-family note case (2)):
            # WORLD NW's own --new-world scaffold already applies the full current lineage
            # (s43 included) and runs the real birth sequence, but this fixture's OWN `led()`
            # call for the first ordinary write still went through the now-dead legacy path (no
            # served boundary stood up over it) -- exactly the gap the per-family note named.
            # Fixed the same way as every other world above: serve_existing_world/stop_server,
            # the s26-row-hash-chain-deletion guard shape (any failure between serve and return
            # must not leak the subprocess).
            for verb in ("autoharn",):
                p = nwdir / verb
                if p.exists():
                    p.chmod(0o755)
            proc_nw = bs_fixtures.serve_existing_world(nwdir / "deployment.json", tmpnw)
            try:
                rfirst = led(nwdir, "decision", "first ordinary write in a strict-on world, no LED_ACTOR")
                first_row = psql_tuples(
                    f"SELECT p.name || '|' || l.principal_actor_resolution FROM {world_nw}.ledger l "
                    f"JOIN {world_nw}_kernel.principal p ON p.id = l.actor "
                    f"WHERE l.kind='decision' ORDER BY l.id DESC LIMIT 1;")
            finally:
                bs_fixtures.stop_server(proc_nw)
        # cluster-1 fixture-repairs: registration events/standing declarations are now 4/2, not
        # the original 3/1 -- s43's own birth sequence (bootstrap/new-project.sh, read in full
        # above) adds a FOURTH principal_registered event (the 'write-boundary' tool principal,
        # s43 Element 6) and a SECOND standing declaration (s43 Element 8's dual declaration: the
        # granted role AND the login role the world's DSN authenticates as each get their own
        # declaration). Verified by reading bootstrap/new-project.sh's own birth-sequence code
        # (not assumed) and confirmed by this run's own real output -- not a weakened assertion,
        # the true current birth sequence this scaffold now performs, asserted exactly.
        check("new-world-birth-sequence",
              rnw.returncode == 0 and events == "4" and decls == "2"
              and rfirst is not None and rfirst.returncode == 0
              and first_row == "author|declared-default",
              f"scaffold exit={rnw.returncode}; registration events={events} (author, reviewer, "
              f"commissioner, write-boundary), standing declarations={decls} (granted role + "
              f"login role -- s43's own dual declaration); first no-LED_ACTOR write "
              f"exit={(rfirst.returncode if rfirst else '?')}, attributed {first_row!r} "
              f"(expect author|declared-default -- strict-on, zero friction)", failures)

    finally:
        for w in (world_a, world_b, world_b2, world_nw):
            teardown(w)
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- s40 principal-identity-events both-polarity proof "
          "(detect t/f, bare-anchor commit refusal, strict attribution red+green, ceremony "
          "duplicate refusals both class polarities, suspend/revoke + successor, precedence "
          "both orders, rotation, anchor append-only, gates green, ./judge AGREE both layers, "
          "REAL --new-world birth sequence end-to-end), zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
