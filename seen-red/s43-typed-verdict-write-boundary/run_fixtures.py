#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for kernel/lineage/s43-typed-verdict-write-boundary
.sql (design/FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md §6's s43 witness plan). Real
infra, no mocks: CLASSIC scaffolds + manual chain applies in the TOY db, one REAL
`new-project.sh --new-world` run against the s43-wired scaffold, torn down before AND after.
Red first, per refusal.

WORLDS:
  WORLD A  -- chain ends at s42: detect f-polarity; the pre-s43 attribution marks
              (explicit/declared-default) for the output-equality comparison; the §6(xv)
              red -- the six s43 columns hand-added WITHOUT a serializer re-issue, shown
              outside the serialization by the coverage gate's own derivation logic.
  WORLD B  -- chain ends at s43: every boundary red/green polarity -- accepted writes;
              journaled policy/integrity/data refusals with committed write_refused rows
              and the chain INTACT through them; the forgery channel + the oracle tripwire
              (verify-chain exit 6); the client-rollback EXPLAIN gap; the journal
              double-failure loud abort; R6 unretractability; the infrastructure-class
              re-raise (57014, unjournaled); attribution output-equality; ./judge AGREE.
  WORLD NW -- a REAL --new-world run (chain s15..s43): birth through the boundary
              (write-boundary registered, dual standing declarations), first ordinary
              ./led write, CLI refusal ergonomics (nonzero exit + taught text), detect t.

Each check() names the witness that would show it false. Usage:
    python3 seen-red/s43-typed-verdict-write-boundary/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import hashlib
import hmac as hmac_mod
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
LINEAGE = REPO / "kernel" / "lineage"
ENGINE = REPO / "engine"
sys.path.insert(0, str(ENGINE))
sys.path.insert(0, str(REPO / "filing"))
sys.path.insert(0, str(REPO / "gates"))

import hash_coverage_gate  # noqa: E402  (FIELD_REF -- the gate's own serialized-set derivation)
import ledger_differential  # noqa: E402
import ledger_edb  # noqa: E402
import pghost_resolve  # noqa: E402

# cli-rebase-fixture-repairs (ledger row 1170): REUSE (ADR-0012 P1) serve_existing_world from
# seen-red/boundary-service/run_fixtures.py -- the served `led` shim refuses every write until
# this deployment.json gains boundary_url/boundary_deployment.
_BS_SPEC = importlib.util.spec_from_file_location(
    "boundary_service_fixtures", REPO / "seen-red" / "boundary-service" / "run_fixtures.py")
assert _BS_SPEC is not None and _BS_SPEC.loader is not None
bs_fixtures = importlib.util.module_from_spec(_BS_SPEC)
sys.modules["boundary_service_fixtures"] = bs_fixtures
_BS_SPEC.loader.exec_module(bs_fixtures)

PGHOST, PGDB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_S42 = [
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
    "s40-principal-identity-events.sql", "s41-principal-bindings-and-relations.sql",
    "s42-row-hash-full-coverage.sql",
]
CHAIN_S43 = CHAIN_S42 + ["s43-typed-verdict-write-boundary.sql"]

S43_COLS = ["refusal_sqlstate", "refusal_message", "refusal_surface",
            "refusal_payload_digest", "refusal_attempted_actor", "refusal_attempted_role"]


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


def psql_tuples(sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"psql failed: {cp.stdout[-500:]} {cp.stderr[-500:]}")
    return cp.stdout.strip()


def psql_raw(script: str) -> subprocess.CompletedProcess[str]:
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-f", "/dev/stdin"],
              input=script)


def detect(schema: str, kern: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tA",
             "-v", f"schema={schema}", "-v", f"kern={kern}",
             "-f", str(LINEAGE / "s43-typed-verdict-write-boundary.detect.sql")])
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
        raise RuntimeError(f"CLASSIC apply FAILED ({world}): {ra.stdout[-1500:]} {ra.stderr[-1500:]}")
    hexsecret = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
        "-c", f"TRUNCATE {kern}.stamp_secret;",
        "-c", f"INSERT INTO {kern}.stamp_secret (secret) VALUES (decode('{hexsecret}','hex'));"])
    genesis_hex = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
        "-c", f"INSERT INTO {kern}.chain_genesis (seed) VALUES ('{genesis_hex}') "
              f"ON CONFLICT (only_one) DO NOTHING;"])
    return world_dir


def bw_call(world: str, fn: str, payload: dict, guc_setup: str = "") -> dict:
    """One boundary-function call as the granted role; returns the verdict as a dict.
    Raises on a NON-verdict failure (psql error / re-raised infrastructure class) with the
    stderr attached -- the caller distinguishes the two deliberately."""
    S, K, R = world, f"{world}_kernel", f"{world}_rw"
    pj = json.dumps(payload).replace("'", "''")
    r = psql_raw(
        f"SET ROLE {R};\nSET search_path = {S}, {K};\n{guc_setup}"
        f"SELECT to_jsonb(v) FROM {K}.{fn}('{pj}'::jsonb) v;\n")
    if r.returncode != 0:
        raise RuntimeError(f"NON-VERDICT: {r.stderr.strip()[-500:]}")
    line = [ln for ln in r.stdout.splitlines() if ln.strip().startswith("{")][-1]
    return json.loads(line)


def birth_via_boundary(world: str) -> None:
    """The s40/s43 birth acts, hand-driven THROUGH the boundary (the scaffold's scripted
    form is witnessed on WORLD NW): author event, role standing declaration, write-boundary
    registration."""
    S, K = world, f"{world}_kernel"
    author = psql_tuples(f"SELECT id FROM {K}.principal WHERE name='author';")
    # the s43 DUAL declaration (Element 8): set_actor resolves on SESSION_USER now, so the
    # LOGIN role needs its own declared standing beside the granted :role -- exactly the
    # scaffold's own birth step 2/2b (witnessed scripted on WORLD NW; hand-driven here).
    login_role = psql_tuples("SELECT session_user;")
    for fn, payload in [
        ("ledger_write", {"kind": "principal_registered",
                          "statement": "author registered (fixture genesis exception)",
                          "actor": author, "principal_subject": author,
                          "principal_purpose": "fixture connection principal"}),
        ("ledger_write", {"kind": "principal_standing_declared",
                          "statement": f"role {world}_rw -> author", "actor": author,
                          "principal_subject": author, "principal_db_role": f"{world}_rw"}),
        ("ledger_write", {"kind": "principal_standing_declared",
                          "statement": f"login role {login_role} -> author (dual declaration)",
                          "actor": author, "principal_subject": author,
                          "principal_db_role": login_role}),
        ("registration_write", {"name": "write-boundary", "agent_class": "tool",
                                "actor": author,
                                "purpose": "the kernel write boundary's own recording "
                                           "identity (s43 fixture birth)"}),
    ]:
        v = bw_call(world, fn, payload)
        if v["disposition"] != "accepted":
            raise RuntimeError(f"birth act refused: {v}")


def verify_chain(world_dir: Path) -> tuple[int, str]:
    cp = sh(["sh", str(world_dir / "verify-chain")], cwd=str(world_dir))
    return cp.returncode, cp.stdout + cp.stderr


def led(world_dir: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    e = dict(os.environ)
    if env:
        e.update(env)
    return sh(["bash", str(world_dir / "led"), *args], cwd=str(world_dir), env=e)


def oracle(world: str) -> tuple[int, int]:
    out = psql_tuples(
        f"SELECT (SELECT count(*) FROM {world}.ledger WHERE kind='write_refused') || '|' || "
        f"(SELECT CASE WHEN is_called THEN last_value ELSE 0 END FROM {world}_kernel.refusal_seq);")
    a, b = out.split("|")
    return int(a), int(b)


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    world_a, world_b, world_nw = "s43fxa", "s43fxb", "s43fxnw"
    for w in (world_a, world_b, world_nw):
        teardown(w)
    try:
        # ===================== WORLD A (s42 head) =====================
        print(f"== scaffolding classic world {world_a} (chain ends {CHAIN_S42[-1]}) ==")
        wa = scaffold_classic(world_a, CHAIN_S42)
        tmps.append(wa.parent)
        S, K, R = world_a, f"{world_a}_kernel", f"{world_a}_rw"
        # pre-s43 birth acts (direct INSERT -- the grant still exists here)
        r = psql_raw(
            f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
            f"INSERT INTO ledger (kind, statement, actor, principal_subject, principal_purpose)\n"
            f"VALUES ('principal_registered', 'author registered (fixture genesis exception)',\n"
            f"        (SELECT id FROM principal WHERE name='author'),\n"
            f"        (SELECT id FROM principal WHERE name='author'), 'fixture principal');\n"
            f"INSERT INTO ledger (kind, statement, actor, principal_subject, principal_db_role)\n"
            f"VALUES ('principal_standing_declared', 'role {R} -> author',\n"
            f"        (SELECT id FROM principal WHERE name='author'),\n"
            f"        (SELECT id FROM principal WHERE name='author'), '{R}');\n"
            f"INSERT INTO ledger (kind, statement) VALUES ('note','pre-s43 declared-default');\n"
            f"INSERT INTO ledger (kind, statement, actor) SELECT 'note','pre-s43 explicit', id "
            f"FROM principal WHERE name='author';\n")
        if r.returncode != 0:
            raise RuntimeError(f"world A fixture failed: {r.stderr[-500:]}")
        check("detect-f-on-s42", detect(S, K) == "f",
              f"s43 detect on an s42-head chain reads {detect(S, K)!r} (expect f)", failures)
        pre_marks = psql_tuples(
            f"SELECT statement || '=' || coalesce(p.name,'?') || '/' || principal_actor_resolution "
            f"FROM {S}.ledger l JOIN {K}.principal p ON p.id = l.actor "
            f"WHERE statement LIKE 'pre-s43%' ORDER BY l.id;")
        # §6(xv) RED: the six s43 columns hand-added with NO serializer re-issue -- shown
        # outside the serialization by the gate's own two-sided derivation (catalog columns
        # vs FIELD_REF over pg_get_functiondef), run against THIS world.
        for c in S43_COLS:
            ty = "bigint" if c == "refusal_attempted_actor" else "text"
            psql_tuples(f"ALTER TABLE {S}.ledger ADD COLUMN {c} {ty}; SELECT 1;")
        table_side = set(psql_tuples(
            f"SELECT column_name FROM information_schema.columns WHERE table_schema='{S}' "
            f"AND table_name='ledger';").splitlines()) - {"row_hash"}
        fndef = psql_tuples(
            f"SELECT pg_get_functiondef(p.oid) FROM pg_proc p JOIN pg_namespace n "
            f"ON n.oid = p.pronamespace WHERE n.nspname='{S}' AND p.proname='compute_row_hash' "
            f"AND p.prokind='f';")
        fn_side = set(hash_coverage_gate.FIELD_REF.findall(fndef))
        missing = sorted(table_side - fn_side)
        check("xv-red-s43-columns-without-reissue",
              missing == sorted(S43_COLS),
              f"on an s42-serializer schema carrying the six s43 columns, the coverage "
              f"derivation reports missing={missing!r} (expect exactly the six refusal "
              f"columns) -- the per-delta law's red, the exact shape the gate refuses",
              failures)
        # ...and the real repository gate is green on the real chain head (s43's re-issue).
        # cli-rebase-fixture-repairs (row 1170): the literal "58" is stale (the repo head has
        # grown past s43 since this fixture was authored) -- checked against "clean" instead,
        # same fix as s45's own identical hardcoded-column-count case (see that fixture for the
        # full rationale: the count's single home is gates/hash_coverage_gate.py itself).
        gg = sh([sys.executable, str(REPO / "gates" / "hash_coverage_gate.py")])
        check("xv-green-gate-on-s43-head", gg.returncode == 0 and "clean" in gg.stdout,
              f"gates/hash_coverage_gate.py exit={gg.returncode} stdout={gg.stdout.strip()!r}",
              failures)

        # ===================== WORLD B (s43 head) =====================
        print(f"== scaffolding classic world {world_b} (chain ends {CHAIN_S43[-1]}) ==")
        wb = scaffold_classic(world_b, CHAIN_S43)
        tmps.append(wb.parent)
        S, K, R = world_b, f"{world_b}_kernel", f"{world_b}_rw"
        birth_via_boundary(world_b)
        check("detect-t-on-s43", detect(S, K) == "t",
              f"s43 detect on the s43 chain reads {detect(S, K)!r} (expect t)", failures)
        author = psql_tuples(f"SELECT id FROM {K}.principal WHERE name='author';")

        # (ii) then (i): the SAME write legal -> accepted; under a REVOKED principal ->
        # refused-as-verdict, journaled, chain INTACT through it, the refused row absent.
        v = bw_call(world_b, "registration_write",
                    {"name": "badguy", "agent_class": "model", "purpose": "revocation fixture",
                     "actor": author})
        badguy = psql_tuples(f"SELECT id FROM {K}.principal WHERE name='badguy';")
        v_ok = bw_call(world_b, "ledger_write",
                       {"kind": "note", "statement": "legal write by badguy", "actor": badguy})
        bw_call(world_b, "ledger_write",
                {"kind": "principal_revoked", "statement": "badguy revoked",
                 "actor": author, "principal_subject": badguy})
        v_ref = bw_call(world_b, "ledger_write",
                        {"kind": "note", "statement": "post-revocation write", "actor": badguy})
        ref_row = psql_tuples(
            f"SELECT refusal_sqlstate || '|' || refusal_surface || '|' || "
            f"coalesce(refusal_attempted_actor::text,'') || '|' || refusal_attempted_role || "
            f"'|' || (actor = (SELECT id FROM {K}.principal WHERE name='write-boundary'))::text "
            f"|| '|' || (length(refusal_payload_digest) = 64)::text "
            f"FROM {S}.ledger WHERE id = {v_ref['refusal_id']};")
        absent = psql_tuples(
            f"SELECT count(*) FROM {S}.ledger WHERE statement = 'post-revocation write';")
        rc_v, out_v = verify_chain(wb)
        check("revoked-principal-refusal-journaled",
              v_ok["disposition"] == "accepted" and v_ref["disposition"] == "refused"
              and v_ref["sqlstate"] == "P0001"
              and ref_row == f"P0001|ledger|{badguy}|bork|true|true"
              and absent == "0" and rc_v == 0 and "INTACT" in out_v
              and "REFUSAL-ORACLE-CONFIRMED" in out_v,
              f"legal write accepted (row {v_ok['row_id']}); post-revocation write refused "
              f"as a verdict, journaled as row {v_ref['refusal_id']} carrying "
              f"{ref_row!r} (sqlstate|surface|attempted-actor|attempted-role|"
              f"actor-is-write-boundary|digest-64hex); the refused row itself absent; "
              f"verify-chain INTACT + oracle CONFIRMED through the refusal", failures)

        # (iii) review ceremony: D-6 managerial by a stamp-distinct MODEL -> journaled with
        # surface 'review', BOTH ceremony rows absent; technical (green) accepted.
        secret = bytes.fromhex(psql_tuples(f"SELECT encode(secret,'hex') FROM {K}.stamp_secret;"))

        def guc(agent: str) -> str:
            ts = int(time.time())
            mac = hmac_mod.new(secret, f"sessFX|{agent}|{ts}".encode(),
                               hashlib.sha256).hexdigest()
            return (f"SELECT set_config('app.vendor_session','sessFX',false),"
                    f" set_config('app.vendor_agent','{agent}',false),"
                    f" set_config('app.vendor_ts','{ts}',false),"
                    f" set_config('app.vendor_hmac','{mac}',false) \\gset _\n")

        bw_call(world_b, "registration_write",
                {"name": "botty", "agent_class": "model", "purpose": "model reviewer fixture",
                 "actor": author})
        botty = psql_tuples(f"SELECT id FROM {K}.principal WHERE name='botty';")
        v_tgt = bw_call(world_b, "ledger_write",
                        {"kind": "decision", "statement": "d6 target", "actor": author},
                        guc_setup=guc("agent0"))
        tgt = str(v_tgt["row_id"])
        n_led, n_det = psql_tuples(
            f"SELECT (SELECT count(*) FROM {S}.ledger WHERE kind='review') || '|' || "
            f"(SELECT count(*) FROM {S}.review_detail);").split("|")
        v_m = bw_call(world_b, "review_write",
                      {"regards": tgt, "statement": "m-claim", "verdict": "attest",
                       "independence": "managerial", "basis": "b", "actor": botty},
                      guc_setup=guc("agentM"))
        v_t = bw_call(world_b, "review_write",
                      {"regards": tgt, "statement": "t-claim", "verdict": "attest",
                       "independence": "technical", "basis": "b", "actor": botty},
                      guc_setup=guc("agentT"))
        n_led2, n_det2 = psql_tuples(
            f"SELECT (SELECT count(*) FROM {S}.ledger WHERE kind='review') || '|' || "
            f"(SELECT count(*) FROM {S}.review_detail);").split("|")
        m_surface = psql_tuples(
            f"SELECT refusal_surface FROM {S}.ledger WHERE id = {v_m['refusal_id']};")
        check("review-ceremony-d6-refusal-journaled",
              v_m["disposition"] == "refused" and "no schema can witness" in v_m["message"]
              and m_surface == "review"
              and v_t["disposition"] == "accepted"
              and int(n_led2) == int(n_led) + 1 and int(n_det2) == int(n_det) + 1,
              f"managerial-by-model refused (taught: 'no schema can witness'), journaled "
              f"surface {m_surface!r}, BOTH ceremony rows rolled (review rows {n_led}->"
              f"{n_led2}, details {n_det}->{n_det2} -- exactly the one accepted technical "
              f"ceremony); technical accepted (row {v_t['row_id']})", failures)

        # (iv) registration ceremony refusals: duplicate name (23505) and a purpose-less
        # event (23514, the kind-shape refusal caught INSIDE the guarded block before the
        # deferred trigger's scope even matters) -- both journaled, surface 'registration',
        # and NO bare anchor survives either. HONEST NOTE (renegotiated shape of §6(iv)'s
        # "bare anchor via a hand-driven call constructed to skip the event"): THROUGH the
        # handler the bare-anchor state is unreachable BY CONSTRUCTION (the function always
        # writes the event beside the anchor; SET CONSTRAINTS ALL IMMEDIATE exists for the
        # class of future deferred refusals) -- so the deferred trigger's own red stays the
        # s40 fixture's raw-path witness, and THIS fixture witnesses the handler-caught
        # ceremony refusals plus the no-bare-anchor invariant.
        v_dup = bw_call(world_b, "registration_write",
                        {"name": "botty", "agent_class": "model", "purpose": "dup",
                         "actor": author})
        v_nop = bw_call(world_b, "registration_write",
                        {"name": "ghost2", "agent_class": "model", "actor": author})
        bare = psql_tuples(
            f"SELECT count(*) FROM {K}.principal p WHERE p.name IN ('ghost2') OR NOT EXISTS "
            f"(SELECT 1 FROM {S}.ledger e WHERE e.kind='principal_registered' "
            f"AND e.principal_subject = p.id) AND p.name <> 'author';")
        check("registration-ceremony-refusals-journaled",
              v_dup["disposition"] == "refused" and v_dup["sqlstate"] == "23505"
              and v_nop["disposition"] == "refused" and v_nop["sqlstate"] == "23514"
              and bare == "0",
              f"duplicate name refused ({v_dup['sqlstate']}, journaled row "
              f"{v_dup['refusal_id']}); purpose-less registration refused "
              f"({v_nop['sqlstate']}, row {v_nop['refusal_id']}); zero bare anchors survive "
              f"(the anchor rolls with its ceremony)", failures)

        # (v) malformed payloads: unknown key; server-owned key; bad cast (22P02).
        v_uk = bw_call(world_b, "ledger_write", {"kind": "note", "statement": "x", "bogus": "y"})
        v_so = bw_call(world_b, "ledger_write",
                       {"kind": "note", "statement": "x", "stamp_verified": "true"})
        v_bc = bw_call(world_b, "ledger_write",
                       {"kind": "note", "statement": "x", "supersedes": "not-a-number"})
        check("malformed-payloads-journaled",
              v_uk["disposition"] == "refused" and "not a ledger column" in v_uk["message"]
              and v_so["disposition"] == "refused" and "SERVER-OWNED" in v_so["message"]
              and v_bc["disposition"] == "refused" and v_bc["sqlstate"] == "22P02",
              f"unknown key refused ({v_uk['sqlstate']}); server-owned key refused "
              f"({v_so['sqlstate']}); bad cast refused ({v_bc['sqlstate']} -- class 22) -- "
              f"all journaled as verdicts", failures)

        # (vi) the forgery channel: kind=write_refused in a payload -> refused; a hand-forged
        # write_refused INSERT as OWNER -> oracle count > sequence -> verify-chain exit 6.
        v_fg = bw_call(world_b, "ledger_write", {"kind": "write_refused", "statement": "forged"})
        wbid = psql_tuples(f"SELECT id FROM {K}.principal WHERE name='write-boundary';")
        rfg = psql_raw(
            f"INSERT INTO {S}.ledger (kind, statement, actor, refusal_sqlstate, "
            f"refusal_message, refusal_surface, refusal_payload_digest, refusal_attempted_role) "
            f"VALUES ('write_refused','owner-forged refusal', {wbid}, 'P0001','forged',"
            f"'ledger', repeat('0',64), 'bork');\n")
        rc6, out6 = verify_chain(wb)
        # repair the forgery for the rest of the run: bump the sequence to re-reconcile
        # (owner-side, exactly what a real forgery investigation would NOT do -- this is
        # fixture bookkeeping so later legs' counts stay interpretable, noted).
        psql_tuples(f"SELECT nextval('{K}.refusal_seq');")
        check("forgery-channel-and-oracle-tripwire",
              v_fg["disposition"] == "refused" and "forgery channel" in v_fg["message"]
              and rfg.returncode == 0
              and rc6 == 6 and "REFUSAL-ORACLE-FORGERY-SUSPECT" in out6,
              f"payload kind=write_refused refused ({v_fg['sqlstate']}, taught); an OWNER-"
              f"forged write_refused row then trips the oracle: verify-chain exit={rc6} "
              f"with FORGERY-SUSPECT (count > sequence -- the flaw-1 second witness firing)",
              failures)

        # (vii) raw INSERT as the granted role -> SQLSTATE 42501 at the privilege layer,
        # no kernel row (REFUSED-AS-EXPECTED; the server log is the named residual home).
        rraw = psql_raw(f"SET ROLE {R};\nSET search_path={S},{K};\n"
                        f"INSERT INTO ledger (kind, statement) VALUES ('note','bypass');\n")
        n_bypass = psql_tuples(f"SELECT count(*) FROM {S}.ledger WHERE statement='bypass';")
        check("raw-insert-privilege-refusal",
              rraw.returncode != 0 and "permission denied" in rraw.stderr and n_bypass == "0",
              f"raw INSERT as {R} refused at the privilege layer (42501-class, "
              f"'permission denied'), zero rows landed -- the bypass path does not exist",
              failures)

        # (viii) an INFRASTRUCTURE-class error (57014 query_canceled via statement_timeout
        # around a deliberately heavy statement) is RE-RAISED unjournaled, sequence untouched.
        rows0, seq0 = oracle(world_b)
        big = "x" * 5_000_000
        infra_raised = False
        for _ in range(5):
            r57 = psql_raw(
                f"SET ROLE {R};\nSET search_path={S},{K};\n"
                f"SET statement_timeout = '2ms';\n"
                f"SELECT {K}.ledger_write(jsonb_build_object('kind','note','statement',"
                f"repeat('x', 5000000)));\n")
            if r57.returncode != 0 and "statement timeout" in r57.stderr:
                infra_raised = True
                break
        rows1, seq1 = oracle(world_b)
        check("infrastructure-class-reraised-unjournaled",
              infra_raised and rows1 == rows0 and seq1 == seq0,
              f"57014 (statement timeout) re-raised as a REAL error, never a verdict "
              f"(raised={infra_raised}); refusal rows {rows0}->{rows1} and sequence "
              f"{seq0}->{seq1} both untouched -- infrastructure failure is not a denied "
              f"attempt", failures)

        # (ix) the oracle's two legs: N==N (confirmed above, re-checked); a client-wrapped
        # ROLLBACK around a refused call -> sequence ahead by one, verify-chain EXPLAINs
        # (exit 0); a journal-INSERT double failure (induced: a temporary NOT VALID CHECK
        # that refuses write_refused rows) -> loud abort + counted gap.
        rows0, seq0 = oracle(world_b)
        rwrap = psql_raw(
            f"SET ROLE {R};\nSET search_path={S},{K};\n"
            f"BEGIN;\nSELECT {K}.ledger_write(jsonb_build_object('kind','bogus_kind',"
            f"'statement','wrapped'));\nROLLBACK;\n")
        rows1, seq1 = oracle(world_b)
        rc_g, out_g = verify_chain(wb)
        psql_tuples(f"ALTER TABLE {S}.ledger ADD CONSTRAINT zz_seenred_break_journal "
                    f"CHECK (kind <> 'write_refused') NOT VALID; SELECT 1;")
        rdbl = psql_raw(
            f"SET ROLE {R};\nSET search_path={S},{K};\n"
            f"SELECT {K}.ledger_write(jsonb_build_object('kind','bogus_kind',"
            f"'statement','double failure'));\n")
        psql_tuples(f"ALTER TABLE {S}.ledger DROP CONSTRAINT zz_seenred_break_journal; SELECT 1;")
        rows2, seq2 = oracle(world_b)
        check("oracle-gap-legs-explained",
              rwrap.returncode == 0 and rows1 == rows0 and seq1 == seq0 + 1
              and rc_g == 0 and "GAP, explained" in out_g
              and rdbl.returncode != 0 and rows2 == rows1 and seq2 == seq1 + 1,
              f"client-wrapped ROLLBACK: rows {rows0}->{rows1}, sequence {seq0}->{seq1} "
              f"(counted, row discarded), verify-chain exit={rc_g} EXPLAINing the gap; "
              f"journal double failure: LOUD abort (exit={rdbl.returncode}), another counted "
              f"gap ({seq1}->{seq2}) -- fail-safe on both legs, one-directional honesty",
              failures)

        # (x) R6: superseding a write_refused row is refused (trigger, taught) -- and the
        # refusal of the hide attempt is itself journaled; superseding an ordinary row works.
        some_ref = psql_tuples(
            f"SELECT min(id) FROM {S}.ledger WHERE kind='write_refused';")
        v_hide = bw_call(world_b, "ledger_write",
                         {"kind": "note", "statement": "hide it", "supersedes": some_ref})
        v_sup = bw_call(world_b, "ledger_write",
                        {"kind": "decision", "statement": "replaces the d6 target",
                         "supersedes": tgt})
        check("r6-unretractable-both-polarities",
              v_hide["disposition"] == "refused" and "UNRETRACTABLE" in v_hide["message"]
              and v_sup["disposition"] == "accepted",
              f"superseding write_refused row {some_ref} refused (taught, journaled row "
              f"{v_hide['refusal_id']}); superseding an ordinary row accepted (row "
              f"{v_sup['row_id']}) -- unretractability confined to the one kind", failures)

        # (xi) attribution output-equality: declared-default and explicit boundary writes
        # carry the SAME actor + resolution marks the pre-s43 direct path produced (world A).
        v_dd = bw_call(world_b, "ledger_write", {"kind": "note", "statement": "pre-s43 declared-default"})
        v_ex = bw_call(world_b, "ledger_write",
                       {"kind": "note", "statement": "pre-s43 explicit", "actor": author})
        post_marks = psql_tuples(
            f"SELECT statement || '=' || coalesce(p.name,'?') || '/' || principal_actor_resolution "
            f"FROM {S}.ledger l JOIN {K}.principal p ON p.id = l.actor "
            f"WHERE l.id IN ({v_dd['row_id']}, {v_ex['row_id']}) ORDER BY l.id;")
        check("attribution-output-equality",
              pre_marks == post_marks
              and pre_marks == ("pre-s43 declared-default=author/declared-default\n"
                                "pre-s43 explicit=author/explicit"),
              f"pre-s43 direct-path marks (world A):\n    {pre_marks!r}\n  s43 boundary "
              f"marks (world B): \n    {post_marks!r} -- identical (session_user resolution "
              f"is output-equal on the resolve path)", failures)

        # (xiii) ./judge SQL/ASP differential in AGREE with write_refused rows live.
        os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"] = PGDB, S, K
        try:
            edb_text = ledger_edb.export(S).edb_text()
            res_tnow = ledger_differential.run_differential(S, edb_text=edb_text)
            res_work = ledger_differential.run_layer_differential(S, "work")
        finally:
            del os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"]
        v_tnow, v_work = res_tnow.verdict(), res_work.verdict()
        n_wr = psql_tuples(f"SELECT count(*) FROM {S}.ledger WHERE kind='write_refused';")
        check("differential-agree-with-write-refused-live",
              v_tnow == "AGREE" and v_work == "AGREE" and int(n_wr) > 0,
              f"tnow={v_tnow} work={v_work} with {n_wr} write_refused row(s) live "
              f"(expect AGREE/AGREE)", failures)

        # ===================== WORLD NW (the s43-wired --new-world) =====================
        print(f"== REAL --new-world scaffold run ({world_nw}, chain s15..s43) ==")
        tmpnw = Path(tempfile.mkdtemp(prefix=f"{world_nw}-seenred-"))
        tmps.append(tmpnw)
        nwdir = tmpnw / world_nw
        rnw = sh(["bash", str(NEW_PROJECT), str(nwdir), "--new-world", world_nw,
                  "--db", PGDB, "--host", PGHOST])
        proc_nw = bs_fixtures.serve_existing_world(nwdir / "deployment.json", tmpnw) \
            if rnw.returncode == 0 else None
        det_nw = detect(world_nw, f"{world_nw}_kernel") if rnw.returncode == 0 else "?"
        principals = psql_tuples(
            f"SELECT string_agg(name, ',' ORDER BY id) FROM {world_nw}_kernel.principal;") \
            if rnw.returncode == 0 else "?"
        login_decl = psql_tuples(
            f"SELECT count(*) FROM {world_nw}.ledger_current WHERE "
            f"kind='principal_standing_declared';") if rnw.returncode == 0 else "?"
        rfirst = led(nwdir, "decision", "first write in an s43 world") \
            if rnw.returncode == 0 else None
        rrefuse = led(nwdir, "bogus_kind", "x") if rnw.returncode == 0 else None
        refuse_out = (rrefuse.stdout + rrefuse.stderr) if rrefuse else ""
        # cli-rebase-fixture-repairs (row 1170): the boundary's own refusal text no longer
        # includes a friendly "valid kinds" list -- it passes through the raw postgres
        # CHECK-violation text ("... violates check constraint \"ledger_kind_check\"") verbatim
        # instead. Wording drift, not a functional regression: the write is still refused, still
        # attributed to the kernel write boundary, still names the CHECK that fired.
        check("new-world-s43-birth",
              rnw.returncode == 0 and det_nw == "t"
              and principals == "author,reviewer,commissioner,write-boundary"
              and login_decl == "2"
              and rfirst is not None and rfirst.returncode == 0
              and rrefuse is not None and rrefuse.returncode != 0
              and "REFUSED by the kernel write boundary" in refuse_out
              and "ledger_kind_check" in refuse_out,
              f"scaffold exit={rnw.returncode}; detect={det_nw!r}; principals="
              f"{principals!r} (write-boundary birth-registered); {login_decl} standing "
              f"declarations (role + login, the s43 dual declaration); first ordinary "
              f"./led write exit={(rfirst.returncode if rfirst else '?')} with no "
              f"LED_ACTOR (strict-on zero-friction end-to-end); a CLI refusal exits "
              f"nonzero with the boundary's taught text AND the kind-vocabulary teach",
              failures)

        # the Idris parity net (the s43 extension's own freshness gate)
        gid = sh([sys.executable, str(REPO / "gates" / "idris_model_freshness.py")])
        check("idris-freshness-green", gid.returncode == 0,
              f"gates/idris_model_freshness.py exit={gid.returncode} (AS-OF s43 vs "
              f"mechanical head s43, elaboration clean)", failures)

    finally:
        proc_nw_ = locals().get("proc_nw")
        if proc_nw_ is not None:
            bs_fixtures.stop_server(proc_nw_)
        for w in (world_a, world_b, world_nw):
            teardown(w)
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- s43 typed-verdict-write-boundary both-polarity proof, zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
