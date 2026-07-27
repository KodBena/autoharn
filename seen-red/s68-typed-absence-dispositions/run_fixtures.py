#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for kernel/lineage/s68-typed-absence-dispositions.sql
(design/FABLE-S68-TYPED-ABSENCE-DISPOSITIONS-SPEC.md, RATIFIED 2026-07-27, ledger rows 1541/1542).
Real infra, no mocks: a CLASSIC scaffold + manual chain apply (s15..s67[..s68]) in the TOY db,
torn down before AND after. Modeled directly on seen-red/s65-refusal-attempted-kind/
run_fixtures.py (birth_via_boundary/bw_call/refusal_row helpers, same shape) and
seen-red/s66-s67-journal-totality/run_fixtures.py (the raw_insert_fails coupling-CHECK-only
helper, PRE/MAIN two-world split).

FIXTURE FAMILY CHOICE (stated per the build brief's own instruction, transcribed from kernel/
lineage/s68-typed-absence-dispositions.sql's own header): this is a NEW sibling family, not an
extension of seen-red/s66-s67-journal-totality/ -- that family's own RED/GREEN pair is a
self-contained two-delta story (forged-stamp branch + digest bound) already fully witnessed and
closed; s68 dispositions a DIFFERENT pair of columns (attempted-kind/attempted-actor) with their
own four-branch and three-branch vocabularies, closer in shape to s65's own standalone family.

RED, per the spec's own §3 witness plan (world s68fxpre, chain ends at s67, NO s68):
  RED-BASELINE-BARE-NULLS-NO-KIND     -- a refused payload with no `kind` key journals TODAY with
                                         a bare NULL refusal_attempted_kind and no disposition
                                         column at all (the conflation this delta closes).
  RED-BASELINE-BARE-NULLS-NONTEXT-KIND -- a refused payload with a non-string `kind` -- same bare
                                         NULL, indistinguishable from the missing-key case.
  RED-BASELINE-BARE-NULLS-OVERBOUND-KIND -- a refused payload with an over-256-byte `kind` --
                                         same bare NULL again, THREE different defects reading
                                         identically.
  RED-BASELINE-BARE-NULL-UNRESOLVABLE-ACTOR -- a refusal with no resolvable actor and no session
                                         default (a direct owner-role call, unbound role) --
                                         bare NULL refusal_attempted_actor, no disposition column.

GREEN (world s68fxmain, chain ends at s68), one case per witnessed branch:
  GREEN-KIND-ABSENT-DECLARED           -- no `kind` key -- refusal_attempted_kind NULL,
                                         refusal_attempted_kind_disposition='absent'.
  GREEN-KIND-NOT-A-STRING-DECLARED     -- `kind` a JSON number -- NULL, disposition='not_a_string'.
  GREEN-KIND-OVER-BOUND-DECLARED       -- `kind` a 300-byte string -- NULL, disposition='over_bound'.
  GREEN-KIND-EXTRACTED-DECLARED        -- an ordinary valid `kind` string -- token populated,
                                         disposition='extracted'.
  GREEN-ACTOR-RESOLVED-EXPLICIT-DECLARED -- payload actor = a registered principal id -- actor
                                         populated, disposition='resolved_explicit'.
  GREEN-ACTOR-RESOLVED-SESSION-DEFAULT-DECLARED -- no actor key, session's own standing-
                                         declaration default resolves -- actor populated,
                                         disposition='resolved_session_default'.
  GREEN-ACTOR-UNRESOLVABLE-DECLARED    -- a direct owner-role journal_write_refusal() call under a
                                         connecting role with NO principal_role binding at all --
                                         actor NULL, disposition='unresolvable' (the OWN mechanism
                                         s67's own RED-COUPLING legs use: a raw call, not through
                                         the boundary, to exercise a case the birth ceremony's own
                                         standing declaration makes otherwise unreachable through
                                         the boundary functions).
  GREEN-ACCEPTED-WRITE-BYTE-IDENTICAL  -- an ordinary accepted write's verdict shape, pre-s68
                                         (s67-head world) vs post-s68-birth, IDENTICAL.
  RED-COUPLING-REJECTS-KIND-NULL-WITH-EXTRACTED / RED-COUPLING-REJECTS-KIND-POPULATED-WITH-ABSENT
                                       -- direct table INSERTs claiming an inconsistent
                                         (refusal_attempted_kind, ..._disposition) pair -- REFUSED
                                         by the coupling CHECK itself.
  RED-COUPLING-REJECTS-ACTOR-NULL-WITH-RESOLVED-EXPLICIT / RED-COUPLING-REJECTS-ACTOR-POPULATED-
  WITH-UNRESOLVABLE                   -- same shape, the actor coupling CHECK.
  RED-KIND-STILL-FORBIDDEN-OFF-KIND / RED-ACTOR-STILL-FORBIDDEN-OFF-KIND -- a non-write_refused
                                         row carrying either nullable column populated is STILL
                                         refused by its own retained one-way kind-shape CHECK
                                         (the s67 fix-round precedent, kept alongside the new
                                         coupling CHECKs).
  ZERO-FRICTION-BIRTH                  -- a fresh classic scaffold's birth sequence through s68,
                                         unaffected.
  VERIFY-CHAIN-INTACT-THROUGH-REFUSALS -- ./autoharn verify-chain INTACT + the s43 refusal-oracle
                                         CONFIRMED, after every refusal above.
  AGREE-sql-asp-differential           -- SQL principal_authority_chain_reaches_genesis(pid) vs
                                         ASP reaches_genesis/1 on the s68-head world -- a
                                         non-regression sanity check (NO derivation reads any
                                         refusal_* column, s65's own §1 item 4 finding, unaffected
                                         by s68 -- named, not merely assumed).

Each check() names the witness that would show it false. Usage:
    python3 seen-red/s68-typed-absence-dispositions/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports are banned."""
from __future__ import annotations

import json
import os
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

import ledger_edb  # noqa: E402
import pghost_resolve  # noqa: E402

os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

PGHOST, PGDB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_S67 = [
    "high_watermark_1.sql", "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
    "s25-commission-kind.sql", "s26-row-hash-chain.sql", "s27-chain-high-water.sql",
    "s28-work-parent-edge.sql", "s29-obligation-item-key-and-typed-close.sql",
    "s30-typed-dependency-edges.sql", "s31-supersession-uniform-retraction.sql",
    "s32-edge-views-single-home.sql", "s33-composite-discharge.sql",
    "s34-computed-grade-refusal.sql", "s35-validation-decomposition.sql",
    "s36-decision-grade.sql", "s37-violation-disposition.sql",
    "s38-bookkeeping-close.sql", "s39-blocks-start.sql",
    "s40-principal-identity-events.sql", "s41-principal-bindings-and-relations.sql",
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
    "s65-refusal-attempted-kind.sql",
    "s66-forged-stamp-journal-totality.sql",
    "s67-refusal-digest-bound.sql",
]
CHAIN_S68 = CHAIN_S67 + ["s68-typed-absence-dispositions.sql"]


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
        f"DROP SCHEMA IF EXISTS {world} CASCADE; DROP SCHEMA IF EXISTS {world}_kernel CASCADE; "
        f"DROP OWNED BY {world}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {world}_rw;"])


def psql_tuples(sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"psql failed: {cp.stdout[-500:]} {cp.stderr[-500:]}")
    return cp.stdout.strip()


def psql_raw(script: str) -> subprocess.CompletedProcess[str]:
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-f", "/dev/stdin"],
              input=script)


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
        raise RuntimeError(f"CLASSIC apply FAILED ({world}): {ra.stdout[-1500:]} {ra.stderr[-1500:]}")
    genesis_hex = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
        "-c", f"INSERT INTO {kern}.chain_genesis (seed) VALUES ('{genesis_hex}') "
              f"ON CONFLICT (only_one) DO NOTHING;"])
    return world_dir


def bw_call(world: str, fn: str, payload: dict) -> dict:
    S, K, R = world, f"{world}_kernel", f"{world}_rw"
    pj = json.dumps(payload).replace("'", "''")
    r = psql_raw(
        f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
        f"SELECT to_jsonb(v) FROM {K}.{fn}('{pj}'::jsonb) v;\n")
    if r.returncode != 0:
        raise RuntimeError(f"NON-VERDICT: {r.stderr.strip()[-500:]}")
    lines = [ln for ln in r.stdout.splitlines() if ln.strip().startswith("{")]
    if not lines:
        raise RuntimeError(f"NO VERDICT LINE: stdout={r.stdout!r} stderr={r.stderr!r}")
    return json.loads(lines[-1])


def bw_call_raw_kind_key(world: str, fn: str, raw_json_text: str) -> dict:
    """Same as bw_call, but the payload is a LITERAL JSON text fragment the caller has already
    hand-built (used for the non-text-kind leg, where a Python dict/json.dumps would only ever
    produce a JSON string for a Python str -- we need a bare JSON number at the `kind` key)."""
    S, K, R = world, f"{world}_kernel", f"{world}_rw"
    pj = raw_json_text.replace("'", "''")
    r = psql_raw(
        f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
        f"SELECT to_jsonb(v) FROM {K}.{fn}('{pj}'::jsonb) v;\n")
    if r.returncode != 0:
        raise RuntimeError(f"NON-VERDICT: {r.stderr.strip()[-500:]}")
    lines = [ln for ln in r.stdout.splitlines() if ln.strip().startswith("{")]
    if not lines:
        raise RuntimeError(f"NO VERDICT LINE: stdout={r.stdout!r} stderr={r.stderr!r}")
    return json.loads(lines[-1])


def journal_direct(world: str, kern_fn_args: str) -> subprocess.CompletedProcess[str]:
    """A direct SCHEMA-OWNER call to kern.journal_write_refusal(...) -- REVOKE ALL FROM PUBLIC
    means no granted role holds EXECUTE, so this bypasses the boundary functions entirely, run as
    the connecting (owner) role. NOTE (found live authoring this fixture): the connecting psql
    user (bork, the schema owner running every command in this file) is ALSO the role
    birth_via_boundary binds to author via its own SECOND principal_standing_declared event (the
    "login role -> author (dual declaration)" birth act, needed for verify-chain's own raw reads)
    -- so a call made simply AS the connecting user is NOT actually unresolvable post-birth; it
    resolves via that dual declaration. This helper is used for the OTHER dispositions (absent/
    not_a_string/over_bound/extracted), where WHO the actor resolves to is irrelevant to the case
    under test. See journal_as_unbound_role() below for the genuinely unresolvable-actor case."""
    K = f"{world}_kernel"
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c",
               f"SET search_path = {world}, {K}; "
               f"SELECT {K}.journal_write_refusal({kern_fn_args});"])


def journal_as_unbound_role(world: str, kern_fn_args: str) -> subprocess.CompletedProcess[str]:
    """The genuinely 'unresolvable' witness: a FRESH login role, never declared as any
    principal's standing db_role (unlike the schema owner, which birth_via_boundary's own second
    declaration binds -- see journal_direct's own note above), temporarily granted EXECUTE on
    every kernel function (the ledger INSERT journal_write_refusal performs re-fires the table's
    own BEFORE INSERT trigger stack, which calls several OTHER kernel functions internally as the
    SAME connecting role, not as a definer -- transitive EXECUTE lets that existing stack run
    unmodified rather than hand-enumerating its own internal call graph), so its own
    session_user resolves to nothing via either the explicit-actor branch (no `actor` key in the
    probe payload) or the session-default fallback (no principal_role row at all for this role).
    CONNECTS DIRECTLY AS the probe role (-U), never merely `SET ROLE` from the owner's own
    connection -- found live authoring this fixture: `SET ROLE` changes current_user but NOT
    session_user, and journal_write_refusal's own session-default fallback keys on session_user,
    so a SET-ROLE-only probe would still resolve via the schema owner's OWN standing declaration
    (the freeze-at-stamp fixture's own -U precedent, seen-red/freeze-at-stamp/run_fixtures.py)."""
    K = f"{world}_kernel"
    probe_role = f"{world}_unbound_probe"
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
        f"DROP ROLE IF EXISTS {probe_role};"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
        f"CREATE ROLE {probe_role} LOGIN; "
        f"GRANT USAGE ON SCHEMA {world}, {K} TO {probe_role}; "
        f"GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA {K} TO {probe_role}; "
        f"GRANT SELECT, INSERT ON {world}.ledger TO {probe_role}; "
        f"GRANT SELECT ON {K}.principal, {K}.principal_role, {K}.refusal_seq, "
        f"{K}.chain_high_water, {K}.chain_genesis, {K}.stamp_secret, {K}.migration_epoch "
        f"TO {probe_role}; "
        f"GRANT USAGE ON SEQUENCE {K}.refusal_seq, {world}.ledger_id_seq TO {probe_role};"])
    r = sh(["psql", "-h", PGHOST, "-d", PGDB, "-U", probe_role, "-tAq", "-v", "ON_ERROR_STOP=1", "-c",
            f"SET search_path = {world}, {K}; "
            f"SELECT {K}.journal_write_refusal({kern_fn_args});"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
        f"DROP OWNED BY {probe_role}; DROP ROLE IF EXISTS {probe_role};"])
    return r


def birth_via_boundary(world: str) -> str:
    K = f"{world}_kernel"
    author = psql_tuples(f"SELECT id FROM {K}.principal WHERE name='author';")
    login_role = psql_tuples("SELECT session_user;")
    for fn, payload in [
        ("ledger_write", {"kind": "principal_registered",
                          "statement": "author registered (fixture genesis exception)",
                          "actor": author, "principal_subject": author,
                          "principal_purpose": "fixture connection principal"}),
        ("ledger_write", {"kind": "principal_standing_declared",
                          "statement": f"role {world}_rw -> author", "actor": author,
                          "principal_subject": author, "principal_db_role": f"{world}_rw",
                          "principal_binding_active": "true"}),
        ("ledger_write", {"kind": "principal_standing_declared",
                          "statement": f"login role {login_role} -> author (dual declaration)",
                          "actor": author, "principal_subject": author,
                          "principal_db_role": login_role,
                          "principal_binding_active": "true"}),
        ("registration_write", {"name": "write-boundary", "agent_class": "tool",
                                "actor": author,
                                "purpose": "s68 fixture's own write-boundary registration"}),
    ]:
        v = bw_call(world, fn, payload)
        if v["disposition"] != "accepted":
            raise RuntimeError(f"birth act refused: {v}")
    return author


def verify_chain(world_dir: Path) -> tuple[int, str]:
    cp = sh(["sh", str(world_dir / "autoharn"), "verify-chain"], cwd=str(world_dir))
    return cp.returncode, cp.stdout + cp.stderr


def refusal_row_pre(world: str, refusal_id: str) -> str:
    """world_pre's own chain ends at s67 -- NO disposition columns exist there at all."""
    return psql_tuples(
        f"SELECT refusal_surface || '|' || refusal_sqlstate || '|' || "
        f"coalesce(refusal_attempted_kind,'<NULL>') || '|' || "
        f"coalesce(refusal_attempted_actor::text,'<NULL>') "
        f"FROM {world}.ledger WHERE id = {refusal_id};")


def refusal_row(world: str, refusal_id: str) -> str:
    """world_main's own chain ends at s68 -- both disposition columns exist."""
    return psql_tuples(
        f"SELECT refusal_surface || '|' || refusal_sqlstate || '|' || "
        f"coalesce(refusal_attempted_kind,'<NULL>') || '|' || "
        f"coalesce(refusal_attempted_kind_disposition,'<NULL>') || '|' || "
        f"coalesce(refusal_attempted_actor::text,'<NULL>') || '|' || "
        f"coalesce(refusal_attempted_actor_disposition,'<NULL>') "
        f"FROM {world}.ledger WHERE id = {refusal_id};")


def raw_insert_fails(world: str, cols_vals: str) -> subprocess.CompletedProcess[str]:
    """A direct owner-role INSERT into the ledger table itself (not through a boundary
    function) -- used ONLY to exercise a raw table CHECK constraint in isolation, never to
    exercise application semantics (the s67 precedent, transcribed)."""
    return psql_raw(f"INSERT INTO {world}.ledger (kind, statement, actor, {cols_vals});\n")


def main() -> int:  # noqa: C901 -- one straight-line witness script, matching s65/s67's own shape
    failures: list[str] = []
    tmps: list[Path] = []
    world_pre, world_main, world_birth = "s68fxpre", "s68fxmain", "s68fxbirth"
    for w in (world_pre, world_main, world_birth):
        teardown(w)
    try:
        # ===================== WORLD PRE (s67 head, NO s68) =====================
        print(f"== scaffolding classic world {world_pre} (chain ends {CHAIN_S67[-1]}, NO s68) ==")
        wp = scaffold_classic(world_pre, CHAIN_S67)
        tmps.append(wp.parent)
        author_pre = birth_via_boundary(world_pre)

        v_missing_pre = bw_call(world_pre, "ledger_write",
                                 {"statement": "s68 fixture: no kind key (pre)", "actor": author_pre})
        detail_missing_pre = (refusal_row_pre(world_pre, v_missing_pre["refusal_id"])
                              if v_missing_pre["refusal_id"] else "N/A")
        cols_pre = psql_tuples(
            f"SELECT string_agg(column_name, ',') FROM information_schema.columns "
            f"WHERE table_schema='{world_pre}' AND table_name='ledger' "
            f"AND column_name IN ('refusal_attempted_kind_disposition', "
            f"'refusal_attempted_actor_disposition');")
        check("RED-BASELINE-BARE-NULLS-NO-KIND",
              v_missing_pre["disposition"] == "refused"
              and detail_missing_pre.split("|")[2] == "<NULL>" and cols_pre == "",
              f"pre-s68 (s67-head) world: a refusal with no `kind` key journals with a bare NULL "
              f"refusal_attempted_kind, and the world's own ledger table carries NO disposition "
              f"column at all (cols_pre={cols_pre!r}) -- detail={detail_missing_pre!r}", failures)

        v_num_pre = bw_call_raw_kind_key(
            world_pre, "ledger_write",
            json.dumps({"statement": "s68 fixture: non-text kind (pre)",
                        "actor": author_pre}).rstrip("}") + ', "kind": 42}')
        detail_num_pre = (refusal_row_pre(world_pre, v_num_pre["refusal_id"])
                          if v_num_pre["refusal_id"] else "N/A")
        check("RED-BASELINE-BARE-NULLS-NONTEXT-KIND",
              v_num_pre["disposition"] == "refused"
              and detail_num_pre.split("|")[2] == detail_missing_pre.split("|")[2] == "<NULL>",
              f"pre-s68 world: a non-string `kind` (42) journals with the SAME bare NULL as the "
              f"missing-key case -- indistinguishable (detail={detail_num_pre!r} vs "
              f"missing-key detail={detail_missing_pre!r}) -- the conflation this delta closes",
              failures)

        v_over_pre = bw_call(world_pre, "ledger_write",
                              {"kind": "x" * 300, "statement": "s68 fixture: over-bound kind (pre)",
                               "actor": author_pre})
        detail_over_pre = (refusal_row_pre(world_pre, v_over_pre["refusal_id"])
                           if v_over_pre["refusal_id"] else "N/A")
        check("RED-BASELINE-BARE-NULLS-OVERBOUND-KIND",
              v_over_pre["disposition"] == "refused"
              and detail_over_pre.split("|")[2] == detail_missing_pre.split("|")[2] == "<NULL>",
              f"pre-s68 world: a 300-byte `kind` (over the s65 256-byte bound) journals with the "
              f"SAME bare NULL, a THIRD distinct defect reading identically to the first two "
              f"(detail={detail_over_pre!r})", failures)

        r_unresolvable_pre = journal_as_unbound_role(
            world_pre, "'ledger', '{\"statement\": \"s68 fixture: unresolvable actor (pre)\"}'::jsonb, '22000', 'probe'")
        unresolvable_id_pre = r_unresolvable_pre.stdout.strip() if r_unresolvable_pre.returncode == 0 else None
        detail_unresolvable_pre = (refusal_row_pre(world_pre, unresolvable_id_pre)
                                   if unresolvable_id_pre and unresolvable_id_pre.isdigit() else "N/A")
        check("RED-BASELINE-BARE-NULL-UNRESOLVABLE-ACTOR",
              r_unresolvable_pre.returncode == 0 and detail_unresolvable_pre.split("|")[-1] == "<NULL>"
              and cols_pre == "",
              f"pre-s68 world: a refusal recorded by a role with NO principal_role binding at "
              f"all (journal_as_unbound_role) journals refusal_attempted_actor as a bare NULL, "
              f"no disposition column recording WHY -- detail={detail_unresolvable_pre!r}",
              failures)

        # ===================== WORLD MAIN (s68 head) =====================
        print(f"== scaffolding classic world {world_main} (chain ends {CHAIN_S68[-1]}) ==")
        wm = scaffold_classic(world_main, CHAIN_S68)
        tmps.append(wm.parent)
        author = birth_via_boundary(world_main)

        # ---- GREEN-KIND-ABSENT-DECLARED (payload deliberately omits `actor` too, so this SAME
        # row doubles as the GREEN-ACTOR-RESOLVED-SESSION-DEFAULT-DECLARED witness below) ----
        v_missing = bw_call(world_main, "ledger_write",
                             {"statement": "s68 fixture: no kind key, no actor key"})
        detail_missing = refusal_row(world_main, v_missing["refusal_id"]) if v_missing["refusal_id"] else "N/A"
        check("GREEN-KIND-ABSENT-DECLARED",
              v_missing["disposition"] == "refused"
              and detail_missing.split("|")[2:4] == ["<NULL>", "absent"],
              f"no `kind` key -- refusal_attempted_kind NULL, disposition='absent' "
              f"(detail={detail_missing!r})", failures)

        # ---- GREEN-KIND-NOT-A-STRING-DECLARED ----
        v_num = bw_call_raw_kind_key(
            world_main, "ledger_write",
            json.dumps({"statement": "s68 fixture: non-text kind",
                        "actor": author}).rstrip("}") + ', "kind": 42}')
        detail_num = refusal_row(world_main, v_num["refusal_id"]) if v_num["refusal_id"] else "N/A"
        check("GREEN-KIND-NOT-A-STRING-DECLARED",
              v_num["disposition"] == "refused"
              and detail_num.split("|")[2:4] == ["<NULL>", "not_a_string"],
              f"`kind` a JSON number (42) -- NULL, disposition='not_a_string' "
              f"(detail={detail_num!r})", failures)

        # ---- GREEN-KIND-OVER-BOUND-DECLARED ----
        v_over = bw_call(world_main, "ledger_write",
                          {"kind": "x" * 300, "statement": "s68 fixture: over-bound kind",
                           "actor": author})
        detail_over = refusal_row(world_main, v_over["refusal_id"]) if v_over["refusal_id"] else "N/A"
        check("GREEN-KIND-OVER-BOUND-DECLARED",
              v_over["disposition"] == "refused"
              and detail_over.split("|")[2:4] == ["<NULL>", "over_bound"],
              f"`kind` a 300-byte string (over the 256-byte bound) -- NULL, "
              f"disposition='over_bound' (detail={detail_over!r})", failures)

        # ---- GREEN-KIND-EXTRACTED-DECLARED (also carries the resolved_explicit actor leg) ----
        v_row = bw_call(world_main, "ledger_write",
                         {"kind": "row", "statement": "s68 fixture: ordinary invalid-kind write",
                          "actor": author})
        detail_row = refusal_row(world_main, v_row["refusal_id"]) if v_row["refusal_id"] else "N/A"
        check("GREEN-KIND-EXTRACTED-DECLARED",
              v_row["disposition"] == "refused"
              and detail_row.split("|")[2:4] == ["row", "extracted"],
              f"an ordinary valid `kind` string ('row') -- token populated, "
              f"disposition='extracted' (detail={detail_row!r})", failures)
        check("GREEN-ACTOR-RESOLVED-EXPLICIT-DECLARED",
              detail_row.split("|")[4] != "<NULL>" and detail_row.split("|")[5] == "resolved_explicit",
              f"the SAME row: payload actor={author} (a registered principal id) -- actor "
              f"populated, disposition='resolved_explicit' (detail={detail_row!r})", failures)

        # ---- GREEN-ACTOR-RESOLVED-SESSION-DEFAULT-DECLARED (the missing-kind row, actor omitted
        # from the payload -- the session's own standing-declaration default resolves to author,
        # since birth_via_boundary bound this world's login role to author) ----
        check("GREEN-ACTOR-RESOLVED-SESSION-DEFAULT-DECLARED",
              detail_missing.split("|")[4] != "<NULL>" and detail_missing.split("|")[5] == "resolved_session_default",
              f"the GREEN-KIND-ABSENT row: no explicit `actor` key in the payload, but this "
              f"world's own login role is bound to author (birth_via_boundary) -- the session "
              f"default resolves, disposition='resolved_session_default' "
              f"(detail={detail_missing!r})", failures)

        # ---- GREEN-ACTOR-UNRESOLVABLE-DECLARED: a role with NO principal_role binding at all ----
        r_unresolvable = journal_as_unbound_role(
            world_main, "'ledger', '{\"kind\": \"note\", \"statement\": \"s68 fixture: unresolvable actor\"}'::jsonb, '22000', 'probe'")
        unresolvable_id = r_unresolvable.stdout.strip() if r_unresolvable.returncode == 0 else None
        detail_unresolvable = (refusal_row(world_main, unresolvable_id)
                               if unresolvable_id and unresolvable_id.isdigit() else "N/A")
        check("GREEN-ACTOR-UNRESOLVABLE-DECLARED",
              r_unresolvable.returncode == 0
              and detail_unresolvable.split("|")[4:6] == ["<NULL>", "unresolvable"],
              f"a refusal recorded by a role with NO principal_role binding at all "
              f"(journal_as_unbound_role) -- actor NULL, disposition='unresolvable' "
              f"(detail={detail_unresolvable!r})", failures)

        # ---- GREEN-ACCEPTED-WRITE-BYTE-IDENTICAL ----
        v_pre_ok = bw_call(world_pre, "ledger_write",
                            {"kind": "decision", "statement": "an ordinary decision row, pre-s68",
                             "actor": author_pre})
        v_post_ok = bw_call(world_main, "ledger_write",
                             {"kind": "decision",
                              "statement": "an ordinary decision row, post-s68-birth",
                              "actor": author})
        check("GREEN-ACCEPTED-WRITE-BYTE-IDENTICAL",
              (v_pre_ok["disposition"], v_pre_ok["sqlstate"], v_pre_ok["message"])
              == (v_post_ok["disposition"], v_post_ok["sqlstate"], v_post_ok["message"])
              == ("accepted", None, None),
              f"an ordinary (kind='decision') write's verdict shape is IDENTICAL pre-s68 vs "
              f"post-s68-birth: pre={v_pre_ok}, post={v_post_ok}", failures)

        # ---- §2's own coupling-CHECK witness plan: direct table INSERTs, never through the
        # boundary -- pure CHECK-constraint proofs. ----
        r_c1 = raw_insert_fails(
            world_main,
            "refusal_sqlstate, refusal_message, refusal_surface, refusal_attempted_role, "
            "refusal_digest_disposition, refusal_attempted_kind_disposition, "
            "refusal_attempted_actor_disposition) VALUES "
            "('write_refused', 'coupling: kind NULL but disposition extracted', 1, 'P0001', "
            "'msg', 'ledger', 'fx', 'payload_over_bound', 'extracted', 'unresolvable'")
        check("RED-COUPLING-REJECTS-KIND-NULL-WITH-EXTRACTED",
              r_c1.returncode != 0 and "refusal_attempted_kind_disposition_coupling" in r_c1.stderr,
              f"a write_refused row claiming disposition='extracted' but refusal_attempted_kind "
              f"NULL is REFUSED by the table CHECK itself (stderr tail="
              f"{r_c1.stderr.strip()[-300:]!r})", failures)

        r_c2 = raw_insert_fails(
            world_main,
            "refusal_sqlstate, refusal_message, refusal_surface, refusal_attempted_role, "
            "refusal_digest_disposition, refusal_attempted_kind, "
            "refusal_attempted_kind_disposition, refusal_attempted_actor_disposition) VALUES "
            "('write_refused', 'coupling: kind populated but disposition absent', 1, 'P0001', "
            "'msg', 'ledger', 'fx', 'payload_over_bound', 'somekind', 'absent', 'unresolvable'")
        check("RED-COUPLING-REJECTS-KIND-POPULATED-WITH-ABSENT",
              r_c2.returncode != 0 and "refusal_attempted_kind_disposition_coupling" in r_c2.stderr,
              f"a write_refused row claiming disposition='absent' but a populated "
              f"refusal_attempted_kind is REFUSED by the table CHECK itself (stderr tail="
              f"{r_c2.stderr.strip()[-300:]!r})", failures)

        r_c4 = raw_insert_fails(
            world_main,
            "refusal_sqlstate, refusal_message, refusal_surface, refusal_attempted_role, "
            "refusal_digest_disposition, refusal_attempted_kind_disposition, "
            "refusal_attempted_actor_disposition) VALUES "
            "('write_refused', 'coupling: actor NULL but disposition resolved_explicit', 1, "
            "'P0001', 'msg', 'ledger', 'fx', 'payload_over_bound', 'absent', 'resolved_explicit'")
        check("RED-COUPLING-REJECTS-ACTOR-NULL-WITH-RESOLVED-EXPLICIT",
              r_c4.returncode != 0 and "refusal_attempted_actor_disposition_coupling" in r_c4.stderr,
              f"a write_refused row claiming disposition='resolved_explicit' but "
              f"refusal_attempted_actor NULL is REFUSED by the table CHECK itself (stderr tail="
              f"{r_c4.stderr.strip()[-300:]!r})", failures)

        r_c5 = raw_insert_fails(
            world_main,
            "refusal_sqlstate, refusal_message, refusal_surface, refusal_attempted_role, "
            "refusal_digest_disposition, refusal_attempted_kind_disposition, "
            "refusal_attempted_actor, refusal_attempted_actor_disposition) VALUES "
            "('write_refused', 'coupling: actor populated but disposition unresolvable', 1, "
            "'P0001', 'msg', 'ledger', 'fx', 'payload_over_bound', 'absent', 1, 'unresolvable'")
        check("RED-COUPLING-REJECTS-ACTOR-POPULATED-WITH-UNRESOLVABLE",
              r_c5.returncode != 0 and "refusal_attempted_actor_disposition_coupling" in r_c5.stderr,
              f"a write_refused row claiming disposition='unresolvable' but a populated "
              f"refusal_attempted_actor is REFUSED by the table CHECK itself (stderr tail="
              f"{r_c5.stderr.strip()[-300:]!r})", failures)

        r_kind_off = raw_insert_fails(
            world_main, "refusal_attempted_kind) VALUES "
                        "('note', 'RED leg: non-write_refused row carrying attempted-kind', 1, 'row'")
        check("RED-KIND-STILL-FORBIDDEN-OFF-KIND",
              r_kind_off.returncode != 0 and "refusal_attempted_kind_kind_shape" in r_kind_off.stderr,
              f"a non-write_refused ('note') row carrying a populated refusal_attempted_kind is "
              f"STILL refused by its own retained one-way kind-shape CHECK (stderr tail="
              f"{r_kind_off.stderr.strip()[-300:]!r})", failures)

        r_actor_off = raw_insert_fails(
            world_main, "refusal_attempted_actor) VALUES "
                        "('note', 'RED leg: non-write_refused row carrying attempted-actor', 1, 1")
        check("RED-ACTOR-STILL-FORBIDDEN-OFF-KIND",
              r_actor_off.returncode != 0 and "refusal_attempted_actor_kind_shape" in r_actor_off.stderr,
              f"a non-write_refused ('note') row carrying a populated refusal_attempted_actor is "
              f"STILL refused by its own retained one-way kind-shape CHECK (stderr tail="
              f"{r_actor_off.stderr.strip()[-300:]!r})", failures)

        # ---- ZERO-FRICTION-BIRTH ----
        print(f"== scaffolding classic world {world_birth} (chain ends {CHAIN_S68[-1]}, fresh "
              f"birth) ==")
        wb = scaffold_classic(world_birth, CHAIN_S68)
        tmps.append(wb.parent)
        author_birth = birth_via_boundary(world_birth)
        v_birth_ok = bw_call(world_birth, "ledger_write",
                              {"kind": "note", "statement": "zero-friction birth note",
                               "actor": author_birth})
        check("ZERO-FRICTION-BIRTH-accepted",
              v_birth_ok["disposition"] == "accepted",
              f"a fresh world's own s40/s43/s68 birth sequence, then an ordinary note write -- "
              f"ACCEPTED, no extra friction from this delta -- verdict={v_birth_ok}", failures)

        # ---- VERIFY-CHAIN-INTACT-THROUGH-REFUSALS + oracle reconciliation ----
        rc_v, out_v = verify_chain(wm)
        oracle_count = psql_tuples(
            f"SELECT count(*) FROM {world_main}.ledger WHERE kind='write_refused';")
        oracle_seq = psql_tuples(
            f"SELECT CASE WHEN is_called THEN last_value ELSE 0 END FROM "
            f"{world_main}_kernel.refusal_seq;")
        check("VERIFY-CHAIN-INTACT-THROUGH-REFUSALS",
              rc_v == 0 and "INTACT" in out_v and "REFUSAL-ORACLE-CONFIRMED" in out_v
              and oracle_count == oracle_seq,
              f"./autoharn verify-chain after every refusal above -- exit={rc_v}, "
              f"INTACT+ORACLE-CONFIRMED in output="
              f"{('INTACT' in out_v) and ('REFUSAL-ORACLE-CONFIRMED' in out_v)}, oracle count="
              f"{oracle_count} == sequence={oracle_seq}", failures)

        # ---- AGREE: SQL/ASP differential sanity (unscoped reaches_genesis) ----
        os.environ["LEDGER_DB"] = PGDB
        os.environ["LEDGER_SCHEMA"] = world_main
        os.environ["LEDGER_KERN"] = f"{world_main}_kernel"
        os.environ.setdefault("EPISTEMIC_PGHOST", PGHOST)
        try:
            exp = ledger_edb.export_entitlement("s68-fixture-oneoff")
            edb_text = exp.edb_text()
            clingo = sh(["clingo", str(ENGINE / "lp" / "ledger_tnow.lp"),
                        str(ENGINE / "lp" / "ledger_entitlement.lp"), "/dev/stdin", "0"],
                       input=edb_text)
            print(f"  [clingo raw stdout]\n{clingo.stdout}\n  [clingo raw stderr]\n{clingo.stderr}\n")
            asp_reaches: set[str] = set()
            for line in clingo.stdout.splitlines():
                if line.startswith("Answer"):
                    continue
                for tok in line.split():
                    if tok.startswith("reaches_genesis(") and tok.endswith(")"):
                        asp_reaches.add(tok[len("reaches_genesis("):-1])
            all_pids = psql_tuples(
                f"SELECT id FROM {world_main}_kernel.principal ORDER BY id;").splitlines()
            sql_reaches: set[str] = set()
            for pid in all_pids:
                r = psql_tuples(
                    f"SELECT {world_main}.principal_authority_chain_reaches_genesis({pid});")
                if r == "t":
                    sql_reaches.add(pid)
            check("AGREE-sql-asp-differential",
                  asp_reaches == sql_reaches,
                  f"SQL principal_authority_chain_reaches_genesis(pid) vs ASP reaches_genesis/1 "
                  f"on the s68-head world -- a non-regression sanity check, since NO derivation "
                  f"reads any refusal_* column -- symmetric_difference="
                  f"{sorted(asp_reaches ^ sql_reaches)}", failures)
        except ledger_edb.CapabilityError as e:
            check("AGREE-sql-asp-differential", False,
                  f"export_entitlement raised CapabilityError (target resolution gap, not a "
                  f"logic defect): {e}", failures)

    finally:
        for w in (world_pre, world_main, world_birth):
            teardown(w)
        for t in tmps:
            sh(["rm", "-rf", str(t)])

    print(f"\n{'ALL GREEN' if not failures else 'FAILURES: ' + ', '.join(failures)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
