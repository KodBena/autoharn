#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T05:48:54Z
#   last-change: 2026-07-18T05:53:27Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for kernel/lineage/s45-standing-lifecycle.sql
(design/FABLE-STANDING-LIFECYCLE-SPEC.md §6's s45 witness plan). Real infra, no mocks: CLASSIC
scaffolds + manual chain applies in the TOY db, one REAL new-project.sh --new-world run against
the s45-wired scaffold, torn down before AND after. Red first, per refusal -- the resurrection
trap leads (a gate/mechanism never seen red is a claim, not a net).

WORLDS:
  WORLD A  -- chain ends at s43 (NO s45): detect f-polarity; the CLI teach-text refusal for
              undeclare-standing/lift-suspension on a pre-s45 kernel.
  WORLD B  -- chain ends at s45: the resurrection trap (naive vs shipped view, harness-local
              naive variant only); §3.1 flag shape; §3.2 rotation/unbind/rebind; §3.3 suspend/
              lift/precedence-both-orders/lift-under-revocation-no-op, the naive-function red
              twins (harness-local); §3.4 the three cross-kind hide attempts + value-continuity
              refusals + legal corrections; §3.5 the write-boundary teach-text branches; §3.8
              CLI verb legs (guards, refusals, the unbind NULL-actor attribution, the
              write-boundary suspension repair leg); §3.7/§3.10 gates + detect + ./judge AGREE.
  WORLD NW -- a REAL --new-world run (chain s15..s45): birth acts carry principal_binding_active
              true, detect t, first ordinary ./led write, undeclare-standing/lift-suspension
              CLI round trip end to end.

Each check() names the witness that would show it false. Usage:
    python3 seen-red/s45-standing-lifecycle/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports are banned."""
from __future__ import annotations

import json
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
sys.path.insert(0, str(REPO / "gates"))

import ledger_differential  # noqa: E402
import ledger_edb  # noqa: E402
import pghost_resolve  # noqa: E402

PGHOST, PGDB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_S43 = [
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
    "s42-row-hash-full-coverage.sql", "s43-typed-verdict-write-boundary.sql",
]
CHAIN_S45 = CHAIN_S43 + ["s45-standing-lifecycle.sql"]


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
             "-f", str(LINEAGE / "s45-standing-lifecycle.detect.sql")])
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


def bw_call(world: str, fn: str, payload: dict) -> dict:
    """One boundary-function call as the granted role; returns the verdict as a dict. Raises
    on a NON-verdict failure (psql error / re-raised infrastructure class) with stderr
    attached -- the caller distinguishes the two deliberately."""
    S, K, R = world, f"{world}_kernel", f"{world}_rw"
    pj = json.dumps(payload).replace("'", "''")
    r = psql_raw(
        f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
        f"SELECT to_jsonb(v) FROM {K}.ledger_write('{pj}'::jsonb) v;\n" if fn == "ledger_write" else
        f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
        f"SELECT to_jsonb(v) FROM {K}.{fn}('{pj}'::jsonb) v;\n")
    if r.returncode != 0:
        raise RuntimeError(f"NON-VERDICT: {r.stderr.strip()[-500:]}")
    line = [ln for ln in r.stdout.splitlines() if ln.strip().startswith("{")][-1]
    return json.loads(line)


def birth_via_boundary(world: str) -> None:
    """The s40/s43 birth acts, hand-driven THROUGH the boundary (the scaffold's scripted form
    is witnessed on WORLD NW): author event, dual standing declarations (WITH
    principal_binding_active true on an s45 world), write-boundary registration."""
    S, K = world, f"{world}_kernel"
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
                                "purpose": "the kernel write boundary's own recording "
                                           "identity (s45 fixture birth)"}),
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


def governing_role(world: str, role: str) -> str:
    """The current kernel.principal_role governing-row's principal_id for `role`, or '' if
    undeclared -- the SHIPPED (resurrection-proof) view, read directly."""
    K = f"{world}_kernel"
    return psql_tuples(f"SELECT coalesce(principal_id::text,'') FROM {K}.principal_role "
                       f"WHERE db_role = '{role}';")


def naive_governing_role(world: str, role: str) -> str:
    """The RESURRECTION-TRAP variant, built HARNESS-LOCAL ONLY (never shipped): filters
    active INSIDE the max-id subquery -- the exact trap the shipped view's own header names."""
    S, K = world, f"{world}_kernel"
    return psql_tuples(
        f"SELECT coalesce((SELECT lc.principal_subject::text FROM {S}.ledger_current lc "
        f"WHERE lc.kind='principal_standing_declared' AND lc.principal_db_role='{role}' "
        f"AND lc.id = (SELECT max(lc2.id) FROM {S}.ledger_current lc2 "
        f"WHERE lc2.kind='principal_standing_declared' AND lc2.principal_db_role='{role}' "
        f"AND lc2.principal_binding_active)),'');")


def naive_principal_standing(world: str, pid: str) -> str:
    """The PRE-FIX naive standing function -- the bare kind-EXISTS test with NO in-force
    filter, the exact s40-era shape s45's Element 3 replaces. HARNESS-LOCAL ONLY."""
    S = world
    out = psql_tuples(
        f"SELECT CASE "
        f"WHEN EXISTS (SELECT 1 FROM {S}.ledger_current e WHERE e.kind='principal_revoked' "
        f"AND e.principal_subject={pid}) THEN 'revoked' "
        f"WHEN EXISTS (SELECT 1 FROM {S}.ledger_current e WHERE e.kind='principal_suspended' "
        f"AND e.principal_subject={pid}) THEN 'suspended' "
        f"ELSE 'active' END;")
    return out


def naive_standing_basis(world: str, pid: str) -> str:
    """The FORK-TRAP naive form: a bare active conjunct on the single-query basis lookup --
    DROPS every revocation (which never carries the flag). HARNESS-LOCAL ONLY."""
    S = world
    return psql_tuples(
        f"SELECT coalesce((SELECT e.id::text FROM {S}.ledger_current e "
        f"WHERE e.principal_subject={pid} AND e.kind IN ('principal_revoked','principal_suspended') "
        f"AND e.principal_binding_active "
        f"ORDER BY (e.kind='principal_revoked') DESC, e.id DESC LIMIT 1),'');")


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    world_a, world_b, world_nw = "s45fxa", "s45fxb", "s45fxnw"
    for w in (world_a, world_b, world_nw):
        teardown(w)
    try:
        # ===================== WORLD A (s43 head, NO s45) =====================
        print(f"== scaffolding classic world {world_a} (chain ends {CHAIN_S43[-1]}, no s45) ==")
        wa = scaffold_classic(world_a, CHAIN_S43)
        tmps.append(wa.parent)
        check("detect-f-on-s43-head", detect(world_a, f"{world_a}_kernel") == "f",
              f"s45 detect on an s43-head chain reads {detect(world_a, f'{world_a}_kernel')!r} (expect f)",
              failures)
        birth_via_boundary_noflag = None  # (defined below, world A uses the s43-era payload shape)
        S, K, R = world_a, f"{world_a}_kernel", f"{world_a}_rw"
        author = psql_tuples(f"SELECT id FROM {K}.principal WHERE name='author';")
        for fn, payload in [
            ("ledger_write", {"kind": "principal_registered",
                              "statement": "author registered", "actor": author,
                              "principal_subject": author, "principal_purpose": "fixture"}),
            ("ledger_write", {"kind": "principal_standing_declared",
                              "statement": f"role {R} -> author", "actor": author,
                              "principal_subject": author, "principal_db_role": R}),
            ("registration_write", {"name": "write-boundary", "agent_class": "tool",
                                    "actor": author, "purpose": "s45 fixture world A birth"}),
        ]:
            v = bw_call(world_a, fn, payload)
            if v["disposition"] != "accepted":
                raise RuntimeError(f"world A birth act refused: {v}")
        # a payload carrying principal_binding_active on an s43-only kernel is refused (the
        # CHECK does not yet license the kind) -- confirms the flag is genuinely NEW territory.
        v_flag_pre_s45 = bw_call(world_a, "ledger_write",
                                 {"kind": "principal_standing_declared",
                                  "statement": "flagged declaration on a pre-s45 kernel",
                                  "actor": author, "principal_subject": author,
                                  "principal_db_role": R, "principal_binding_active": "true"})
        check("flag-refused-on-pre-s45-kernel",
              v_flag_pre_s45["disposition"] == "refused" and v_flag_pre_s45["sqlstate"] == "23514",
              f"principal_binding_active on a declaration is REFUSED pre-s45 ({v_flag_pre_s45['sqlstate']}) "
              f"-- the CHECK genuinely does not license it there", failures)
        # the CLI teach-text refusal for both new verbs on a pre-s45 kernel, kernel untouched.
        r_undeclare = led(wa, "principal", "undeclare-standing")
        r_lift = led(wa, "principal", "lift-suspension", "author")
        out_u = r_undeclare.stdout + r_undeclare.stderr
        out_l = r_lift.stdout + r_lift.stderr
        check("cli-refuses-new-verbs-on-pre-s45-kernel",
              r_undeclare.returncode != 0 and "predates" in out_u and "s45-standing-lifecycle" in out_u
              and r_lift.returncode != 0 and "predates" in out_l and "s45-standing-lifecycle" in out_l,
              f"undeclare-standing exit={r_undeclare.returncode} ({'taught' if 'predates' in out_u else 'NOT taught'}); "
              f"lift-suspension exit={r_lift.returncode} ({'taught' if 'predates' in out_l else 'NOT taught'})",
              failures)

        # ===================== WORLD B (s45 head) =====================
        print(f"== scaffolding classic world {world_b} (chain ends {CHAIN_S45[-1]}) ==")
        wb = scaffold_classic(world_b, CHAIN_S45)
        tmps.append(wb.parent)
        S, K, R = world_b, f"{world_b}_kernel", f"{world_b}_rw"
        birth_via_boundary(world_b)
        check("detect-t-on-s45-head", detect(S, K) == "t",
              f"s45 detect on the s45 chain reads {detect(S, K)!r} (expect t)", failures)
        author = psql_tuples(f"SELECT id FROM {K}.principal WHERE name='author';")

        # ---- THE RESURRECTION-TRAP RED (commissioned centerpiece, run FIRST) ----
        v_c = bw_call(world_b, "registration_write",
                      {"name": "carol", "agent_class": "model", "purpose": "resurrection fixture",
                       "actor": author})
        carol = psql_tuples(f"SELECT id FROM {K}.principal WHERE name='carol';")
        v_d = bw_call(world_b, "registration_write",
                      {"name": "dave", "agent_class": "model", "purpose": "resurrection fixture",
                       "actor": author})
        dave = psql_tuples(f"SELECT id FROM {K}.principal WHERE name='dave';")
        # two UNSUPERSEDED declarations for the SAME role, R2 -> carol, R2 -> dave (no
        # supersedes -- the legal shape a direct boundary caller can produce, which the CLI's
        # auto-supersede usually avoids).
        v_r2c = bw_call(world_b, "ledger_write",
                        {"kind": "principal_standing_declared", "statement": "R2 -> carol",
                         "actor": author, "principal_subject": carol,
                         "principal_db_role": "R2", "principal_binding_active": "true"})
        v_r2d = bw_call(world_b, "ledger_write",
                        {"kind": "principal_standing_declared", "statement": "R2 -> dave",
                         "actor": author, "principal_subject": dave,
                         "principal_db_role": "R2", "principal_binding_active": "true"})
        pre_naive = naive_governing_role(world_b, "R2")
        pre_shipped = governing_role(world_b, "R2")
        # unbind the GOVERNING (dave) declaration.
        v_unbind = bw_call(world_b, "ledger_write",
                           {"kind": "principal_standing_declared", "statement": "R2 unbound",
                            "actor": author, "principal_subject": dave,
                            "principal_db_role": "R2", "principal_binding_active": "false",
                            "supersedes": v_r2d["row_id"]})
        post_naive = naive_governing_role(world_b, "R2")
        post_shipped = governing_role(world_b, "R2")
        # re-bind: a fresh declaration becomes governing again.
        v_r2rebind = bw_call(world_b, "ledger_write",
                             {"kind": "principal_standing_declared", "statement": "R2 -> carol (rebind)",
                              "actor": author, "principal_subject": carol,
                              "principal_db_role": "R2", "principal_binding_active": "true"})
        rebind_shipped = governing_role(world_b, "R2")
        check("resurrection-trap-both-forms",
              v_r2c["disposition"] == "accepted" and v_r2d["disposition"] == "accepted"
              and pre_naive == dave and pre_shipped == dave
              and v_unbind["disposition"] == "accepted"
              and post_naive == carol  # RED: the naive form silently resurrects carol
              and post_shipped == ""   # GREEN: the shipped view correctly reads undeclared
              and v_r2rebind["disposition"] == "accepted" and rebind_shipped == carol,
              f"before unbind both variants read governing=dave (naive={pre_naive!r} "
              f"shipped={pre_shipped!r}); AFTER unbinding dave's declaration: "
              f"NAIVE VARIANT (harness-local, never shipped) resurrects to {post_naive!r} "
              f"(the RED this delta's own header warns against) while the SHIPPED view "
              f"correctly reads {post_shipped!r} (undeclared, empty); a fresh declaration "
              f"then re-binds governing={rebind_shipped!r}", failures)
        # a NULL-actor write under R2 while undeclared is refused, journaled, then accepted
        # once carol's rebind lands (already re-bound above -- exercised via a live SET ROLE).
        r_undeclared_write = psql_raw(
            f"SET ROLE R2;\nSET search_path={S},{K};\nSELECT set_config('x','1',false);\n")
        # (R2 is not a real login role in this scratch -- the undeclared-write refusal is
        # witnessed properly below via the boundary path instead, since only :role/session_user
        # actually authenticate here; this block intentionally left as a no-op probe.)
        del r_undeclared_write

        # ---- §3.1 flag shape ----
        v_decl_noflag = bw_call(world_b, "ledger_write",
                                {"kind": "principal_standing_declared", "statement": "no flag",
                                 "actor": author, "principal_subject": carol,
                                 "principal_db_role": "R3"})
        v_susp_noflag = bw_call(world_b, "ledger_write",
                                {"kind": "principal_suspended", "statement": "no flag",
                                 "actor": author, "principal_subject": carol})
        v_decl_inactive_birth = bw_call(world_b, "ledger_write",
                                        {"kind": "principal_standing_declared",
                                         "statement": "inactive from birth", "actor": author,
                                         "principal_subject": carol, "principal_db_role": "R4",
                                         "principal_binding_active": "false"})
        v_revoke_with_flag = bw_call(world_b, "ledger_write",
                                     {"kind": "principal_revoked", "statement": "flagged revoke",
                                      "actor": author, "principal_subject": carol,
                                      "principal_binding_active": "true"})
        check("section-3.1-flag-shape",
              v_decl_noflag["disposition"] == "refused" and v_decl_noflag["sqlstate"] == "23514"
              and v_susp_noflag["disposition"] == "refused" and v_susp_noflag["sqlstate"] == "23514"
              and v_decl_inactive_birth["disposition"] == "refused"
              and v_revoke_with_flag["disposition"] == "refused",
              f"declaration w/o flag refused ({v_decl_noflag['sqlstate']}); suspension w/o "
              f"flag refused ({v_susp_noflag['sqlstate']}); inactive-from-birth declaration "
              f"refused ({v_decl_inactive_birth['sqlstate']}); revocation WITH any flag value "
              f"refused ({v_revoke_with_flag['sqlstate']}) -- all four, verdicts, journaled",
              failures)

        # ---- §3.3 suspend / lift / precedence / lift-under-revocation ----
        v_erin = bw_call(world_b, "registration_write",
                         {"name": "erin", "agent_class": "model", "purpose": "s3.3 fixture",
                          "actor": author})
        erin = psql_tuples(f"SELECT id FROM {K}.principal WHERE name='erin';")
        v_susp_e = bw_call(world_b, "ledger_write",
                           {"kind": "principal_suspended", "statement": "erin suspended",
                            "actor": author, "principal_subject": erin,
                            "principal_binding_active": "true"})
        standing_after_suspend = psql_tuples(f"SELECT {K}.principal_standing({erin});")
        naive_after_suspend = naive_principal_standing(world_b, erin)
        v_lift_e = bw_call(world_b, "ledger_write",
                           {"kind": "principal_suspended", "statement": "erin lifted",
                            "actor": author, "principal_subject": erin,
                            "principal_binding_active": "false", "supersedes": v_susp_e["row_id"]})
        standing_after_lift = psql_tuples(f"SELECT {K}.principal_standing({erin});")
        naive_after_lift = naive_principal_standing(world_b, erin)  # RED: still 'suspended'
        check("section-3.3-lift-in-force-filter",
              v_susp_e["disposition"] == "accepted"
              and standing_after_suspend == "suspended" and naive_after_suspend == "suspended"
              and v_lift_e["disposition"] == "accepted"
              and standing_after_lift == "active"
              and naive_after_lift == "suspended",  # the PRE-FIX shape, harness-local
              f"after suspend: shipped={standing_after_suspend!r} naive={naive_after_suspend!r} "
              f"(agree); after lift: SHIPPED={standing_after_lift!r} (correctly 'active') vs "
              f"NAIVE={naive_after_lift!r} (the RED s45 Element 3 fixes -- a lifted suspension "
              f"would read suspended FOREVER under the naive bare-EXISTS form)", failures)

        # precedence both orders + lift-under-revocation no-op
        v_frank = bw_call(world_b, "registration_write",
                          {"name": "frank", "agent_class": "model", "purpose": "precedence A",
                           "actor": author})
        frank = psql_tuples(f"SELECT id FROM {K}.principal WHERE name='frank';")
        v_grace = bw_call(world_b, "registration_write",
                          {"name": "grace", "agent_class": "model", "purpose": "precedence B",
                           "actor": author})
        grace = psql_tuples(f"SELECT id FROM {K}.principal WHERE name='grace';")
        bw_call(world_b, "ledger_write", {"kind": "principal_suspended", "statement": "frank suspend",
                                          "actor": author, "principal_subject": frank,
                                          "principal_binding_active": "true"})
        bw_call(world_b, "ledger_write", {"kind": "principal_revoked", "statement": "frank revoke",
                                          "actor": author, "principal_subject": frank})
        frank_standing = psql_tuples(f"SELECT {K}.principal_standing({frank});")
        bw_call(world_b, "ledger_write", {"kind": "principal_revoked", "statement": "grace revoke",
                                          "actor": author, "principal_subject": grace})
        v_grace_susp = bw_call(world_b, "ledger_write",
                               {"kind": "principal_suspended", "statement": "grace suspend under revoke",
                                "actor": author, "principal_subject": grace,
                                "principal_binding_active": "true"})
        grace_standing = psql_tuples(f"SELECT {K}.principal_standing({grace});")
        grace_basis = psql_tuples(f"SELECT {K}.principal_standing_basis({grace});")
        grace_basis_naive = naive_standing_basis(world_b, grace)  # RED: the WRONG row
        v_grace_lift = bw_call(world_b, "ledger_write",
                               {"kind": "principal_suspended", "statement": "grace lift under revoke",
                                "actor": author, "principal_subject": grace,
                                "principal_binding_active": "false",
                                "supersedes": v_grace_susp["row_id"]})
        grace_standing_after_lift = psql_tuples(f"SELECT {K}.principal_standing({grace});")
        # a SECOND fork-trap demonstration, cleaner: a principal revoked and NEVER suspended --
        # the naive bare conjunct evaluates `AND e.principal_binding_active` against the
        # revocation row's NULL flag, dropping it entirely (empty), where the shipped
        # kind-aware form still names it.
        v_irene = bw_call(world_b, "registration_write",
                          {"name": "irene", "agent_class": "model", "purpose": "fork-trap fixture",
                           "actor": author})
        irene = psql_tuples(f"SELECT id FROM {K}.principal WHERE name='irene';")
        bw_call(world_b, "ledger_write", {"kind": "principal_revoked", "statement": "irene revoke",
                                          "actor": author, "principal_subject": irene})
        irene_basis = psql_tuples(f"SELECT {K}.principal_standing_basis({irene});")
        irene_basis_naive = naive_standing_basis(world_b, irene)
        check("section-3.3-precedence-both-orders-and-lift-under-revocation",
              frank_standing == "revoked" and grace_standing == "revoked"
              and v_grace_susp["disposition"] == "accepted"
              and grace_basis is not None and grace_basis != ""
              and grace_basis_naive != "" and grace_basis_naive != grace_basis
              # ^ the naive bare-AND wrongly picks the SUSPENSION row's id as the "basis" even
              # though revocation dominates -- a different, wrong answer, not merely absent.
              and irene_basis != "" and irene_basis_naive == ""
              # ^ the cleaner instance the spec names: a revoked-only principal's basis
              # VANISHES entirely under the naive bare conjunct (NULL AND'd against nothing).
              and v_grace_lift["disposition"] == "accepted"
              and grace_standing_after_lift == "revoked",  # the observable no-op
              f"suspend-then-revoke -> {frank_standing!r}; revoke-then-suspend -> "
              f"{grace_standing!r} (both 'revoked', precedence unchanged); for grace (revoked "
              f"+ an unlifted suspension), principal_standing_basis={grace_basis!r} (the "
              f"revocation row) while the NAIVE bare-conjunct form (harness-local) wrongly "
              f"yields {grace_basis_naive!r} (the SUSPENSION row -- a different, wrong "
              f"governing basis); for irene (revoked, never suspended), shipped basis="
              f"{irene_basis!r} vs naive={irene_basis_naive!r} (empty -- the revocation "
              f"VANISHES under the bare conjunct, the fork trap's cleanest form, s45 Element "
              f"3); lift-under-revocation is ACCEPTED and CHANGES NOTHING OBSERVABLE "
              f"({grace_standing_after_lift!r}, the ratified I5 no-op)", failures)

        # ---- §3.4 the three cross-kind hide attempts + value-continuity + legal corrections ----
        v_h1 = bw_call(world_b, "ledger_write",
                       {"kind": "note", "statement": "hide the declaration",
                        "supersedes": v_r2rebind["row_id"]})
        v_susp_h = bw_call(world_b, "ledger_write",
                           {"kind": "principal_suspended", "statement": "hide-target suspend",
                            "actor": author, "principal_subject": erin,
                            "principal_binding_active": "true"})
        v_h2 = bw_call(world_b, "ledger_write",
                       {"kind": "note", "statement": "hide the suspension",
                        "supersedes": v_susp_h["row_id"]})
        v_revoke_h = bw_call(world_b, "ledger_write",
                             {"kind": "principal_revoked", "statement": "hide-target revoke",
                              "actor": author, "principal_subject": frank})
        v_h3 = bw_call(world_b, "ledger_write",
                       {"kind": "note", "statement": "hide the revocation",
                        "supersedes": v_revoke_h["row_id"]})
        check("section-3.4-three-cross-kind-hide-attempts-journaled",
              v_h1["disposition"] == "refused" and "superseded ONLY by its OWN kind" in v_h1["message"]
              and v_h2["disposition"] == "refused" and "superseded ONLY by its OWN kind" in v_h2["message"]
              and v_h3["disposition"] == "refused" and "superseded ONLY by its OWN kind" in v_h3["message"],
              f"a `note` superseding a declaration ({v_h1['sqlstate']}, journaled row "
              f"{v_h1['refusal_id']}), a suspension ({v_h2['sqlstate']}, row {v_h2['refusal_id']}), "
              f"and a revocation ({v_h3['sqlstate']}, row {v_h3['refusal_id']}) are each "
              f"REFUSED-AS-EXPECTED -- the hide attempt ITSELF becomes a committed record",
              failures)

        v_mismatch_role = bw_call(world_b, "ledger_write",
                                  {"kind": "principal_standing_declared",
                                   "statement": "wrong role", "actor": author,
                                   "principal_subject": carol, "principal_db_role": "WRONGROLE",
                                   "principal_binding_active": "false",
                                   "supersedes": v_r2rebind["row_id"]})
        v_mismatch_subj_susp = bw_call(world_b, "ledger_write",
                                       {"kind": "principal_suspended",
                                        "statement": "wrong subject", "actor": author,
                                        "principal_subject": frank,
                                        "principal_binding_active": "false",
                                        "supersedes": v_susp_h["row_id"]})
        v_mismatch_subj_rev = bw_call(world_b, "ledger_write",
                                      {"kind": "principal_revoked",
                                       "statement": "wrong subject correction", "actor": author,
                                       "principal_subject": erin,
                                       "supersedes": v_revoke_h["row_id"]})
        check("section-3.4-value-continuity-mismatches-refused",
              v_mismatch_role["disposition"] == "refused"
              and "SAME db_role" in v_mismatch_role["message"]
              and v_mismatch_subj_susp["disposition"] == "refused"
              and "SAME subject" in v_mismatch_subj_susp["message"]
              and v_mismatch_subj_rev["disposition"] == "refused"
              and "SAME subject" in v_mismatch_subj_rev["message"],
              f"declaration-db_role mismatch refused ({v_mismatch_role['sqlstate']}); "
              f"suspension-subject mismatch refused ({v_mismatch_subj_susp['sqlstate']}); "
              f"revocation-subject mismatch refused ({v_mismatch_subj_rev['sqlstate']})",
              failures)

        v_rotate_ok = bw_call(world_b, "ledger_write",
                              {"kind": "principal_standing_declared",
                               "statement": "rotation repoints subject", "actor": author,
                               "principal_subject": dave, "principal_db_role": "R2",
                               "principal_binding_active": "true",
                               "supersedes": v_r2rebind["row_id"]})
        v_unbind_ok = bw_call(world_b, "ledger_write",
                              {"kind": "principal_standing_declared",
                               "statement": "unbind matching both", "actor": author,
                               "principal_subject": dave, "principal_db_role": "R2",
                               "principal_binding_active": "false",
                               "supersedes": v_rotate_ok["row_id"]})
        v_resuspend_ok = bw_call(world_b, "ledger_write",
                                 {"kind": "principal_suspended",
                                  "statement": "re-suspend correction", "actor": author,
                                  "principal_subject": erin, "principal_binding_active": "true",
                                  "supersedes": v_susp_h["row_id"]})
        v_rerevoke_ok = bw_call(world_b, "ledger_write",
                                {"kind": "principal_revoked",
                                 "statement": "re-revoke correction", "actor": author,
                                 "principal_subject": frank, "supersedes": v_revoke_h["row_id"]})
        frank_standing_after_correction = psql_tuples(f"SELECT {K}.principal_standing({frank});")
        check("section-3.4-legal-corrections-accepted",
              v_rotate_ok["disposition"] == "accepted"
              and v_unbind_ok["disposition"] == "accepted"
              and v_resuspend_ok["disposition"] == "accepted"
              and v_rerevoke_ok["disposition"] == "accepted"
              and frank_standing_after_correction == "revoked",
              f"rotation repointing subject (row {v_rotate_ok['row_id']}), unbind matching "
              f"both fields (row {v_unbind_ok['row_id']}), re-suspend correction (row "
              f"{v_resuspend_ok['row_id']}), re-revoke correction (row {v_rerevoke_ok['row_id']}) "
              f"all ACCEPTED; standing after the re-revoke correction is still "
              f"{frank_standing_after_correction!r}", failures)

        # ---- §3.5 write-boundary teach-text branches ----
        v_susp_write_probe = bw_call(world_b, "ledger_write",
                                     {"kind": "note", "statement": "attempt while suspended",
                                      "actor": erin})
        v_rev_write_probe = bw_call(world_b, "ledger_write",
                                    {"kind": "note", "statement": "attempt while revoked",
                                     "actor": frank})
        check("section-3.5-teach-text-branches",
              v_susp_write_probe["disposition"] == "refused"
              and "lift-suspension" in v_susp_write_probe["message"]
              and v_rev_write_probe["disposition"] == "refused"
              and "TERMINAL BY TYPE" in v_rev_write_probe["message"]
              and "lift-suspension" not in v_rev_write_probe["message"],
              f"a write under a suspended actor teaches lift-suspension: "
              f"{v_susp_write_probe['message'][:90]!r}...; under a revoked actor teaches "
              f"TERMINAL BY TYPE / succession, no lift-suspension mention: "
              f"{v_rev_write_probe['message'][:90]!r}...", failures)
        v_lift_erin_again = bw_call(world_b, "ledger_write",
                                    {"kind": "principal_suspended",
                                     "statement": "lift erin again", "actor": author,
                                     "principal_subject": erin, "principal_binding_active": "false",
                                     "supersedes": v_resuspend_ok["row_id"]})
        v_erin_write_after_lift = bw_call(world_b, "ledger_write",
                                          {"kind": "note", "statement": "erin writes after lift",
                                           "actor": erin})
        check("section-3.5-write-accepted-after-lift",
              v_lift_erin_again["disposition"] == "accepted"
              and v_erin_write_after_lift["disposition"] == "accepted",
              f"lift accepted (row {v_lift_erin_again['row_id']}); erin's next write accepted "
              f"(row {v_erin_write_after_lift['row_id']}) -- the never-refuses-after-lift leg",
              failures)

        # ---- §3.8 CLI verb legs ----
        r_undeclare_none = led(wb, "principal", "undeclare-standing", "--db-role", "NOSUCHROLE")
        out_un = r_undeclare_none.stdout + r_undeclare_none.stderr
        r_lift_none = led(wb, "principal", "lift-suspension", "carol")
        out_ln = r_lift_none.stdout + r_lift_none.stderr
        check("section-3.8-cli-no-target-refusals",
              r_undeclare_none.returncode != 0 and "nothing to unbind" in out_un
              and r_lift_none.returncode != 0 and "no in-force suspension" in out_ln,
              f"undeclare-standing on an undeclared role: exit={r_undeclare_none.returncode} "
              f"({'taught' if 'nothing to unbind' in out_un else 'NOT taught'}); "
              f"lift-suspension on a non-suspended principal: exit={r_lift_none.returncode} "
              f"({'taught' if 'no in-force suspension' in out_ln else 'NOT taught'})", failures)

        # frank (suspended THEN revoked above, never lifted) still carries an in-force
        # (unsuperseded, active=true) suspension row -- grace's own was already lifted as
        # part of the lift-under-revocation leg just above, so frank is the live target here.
        r_susp_dup = led(wb, "principal", "suspend", "frank", "second")
        out_dup = r_susp_dup.stdout + r_susp_dup.stderr
        check("section-3.8-cli-suspend-duplicate-guard",
              r_susp_dup.returncode != 0 and "no duplicate active truth" in out_dup,
              f"CLI `suspend frank` while frank already carries an in-force suspension "
              f"(from the precedence leg above, never lifted): exit={r_susp_dup.returncode} "
              f"({'taught' if 'no duplicate active truth' in out_dup else 'NOT taught'})",
              failures)

        r_declare_h = led(wb, "principal", "declare-standing", "erin", "--db-role", "R5")
        r_undeclare_h = led(wb, "principal", "undeclare-standing", "--db-role", "R5")
        gov_after_cli_unbind = governing_role(world_b, "R5")
        unbind_attribution = psql_tuples(
            f"SELECT p.name FROM {S}.ledger l JOIN {K}.principal p ON p.id = l.actor "
            f"WHERE l.kind='principal_standing_declared' AND l.principal_db_role='R5' "
            f"AND l.principal_binding_active = false ORDER BY l.id DESC LIMIT 1;")
        check("section-3.8-cli-declare-then-undeclare-round-trip",
              r_declare_h.returncode == 0 and r_undeclare_h.returncode == 0
              and gov_after_cli_unbind == "" and unbind_attribution == "author",
              f"declare-standing exit={r_declare_h.returncode}; undeclare-standing "
              f"exit={r_undeclare_h.returncode}; governing role after unbind={gov_after_cli_unbind!r} "
              f"(undeclared); the unbind row's own actor={unbind_attribution!r} (the outgoing "
              f"principal's own last act under the role -- set_actor resolves BEFORE the row "
              f"lands, while the declaration is still governing)", failures)

        # LED_ACTOR names a SECOND active principal distinct from frank -- 'erin' (registered
        # earlier, lifted and active again by section-3.5) rather than 'reviewer'/'commissioner'
        # (this CLASSIC-scaffolded world's birth_via_boundary only registers author +
        # write-boundary; the standard reviewer/commissioner pair is a --new-world-only birth
        # act, witnessed separately on WORLD NW below).
        r_lift_by_second = led(wb, "principal", "lift-suspension", "frank", "released", "by", "second",
                               "actor", env={"LED_ACTOR": "erin"})
        frank_standing_final = psql_tuples(f"SELECT {K}.principal_standing({frank});")
        check("section-3.8-cli-lift-by-second-active-principal",
              r_lift_by_second.returncode == 0 and frank_standing_final == "revoked",
              f"`lift-suspension frank` run as a SECOND active principal (LED_ACTOR=erin): "
              f"exit={r_lift_by_second.returncode}; frank's standing stays {frank_standing_final!r} "
              f"(revoked dominates -- the note the verb itself is supposed to print)", failures)

        # the write-boundary suspension-repair leg: suspend write-boundary via a DIRECT
        # boundary call (the CLI itself refuses this -- see world A's guard, unchanged), then
        # repair it through lift-suspension run by another principal.
        wbid = psql_tuples(f"SELECT id FROM {K}.principal WHERE name='write-boundary';")
        v_susp_wb = bw_call(world_b, "ledger_write",
                            {"kind": "principal_suspended",
                             "statement": "direct suspension of write-boundary (bypassing the "
                                          "CLI guard, fixture-only)",
                             "actor": author, "principal_subject": wbid,
                             "principal_binding_active": "true"})
        r_lift_wb = led(wb, "principal", "lift-suspension", "write-boundary")
        wb_standing_after = psql_tuples(f"SELECT {K}.principal_standing({wbid});")
        check("section-3.8-write-boundary-repair-leg",
              v_susp_wb["disposition"] == "accepted" and r_lift_wb.returncode == 0
              and wb_standing_after == "active",
              f"write-boundary suspended via a direct (non-CLI) call (row {v_susp_wb['row_id']}); "
              f"`lift-suspension write-boundary` by another active principal repairs it through "
              f"the sanctioned surface: exit={r_lift_wb.returncode}, standing after={wb_standing_after!r}",
              failures)

        # ---- §3.7/§3.10 gates + ./judge ----
        gk = sh([sys.executable, str(REPO / "gates" / "kind_shape_manifest_gate.py")])
        check("gate-kind-shape-manifest-green", gk.returncode == 0,
              f"gates/kind_shape_manifest_gate.py exit={gk.returncode} on the real repo head "
              f"(the widened principal_binding_active row)", failures)
        gr = sh([sys.executable, str(REPO / "gates" / "ledger_reader_allowlist.py")])
        check("gate-reader-allowlist-green", gr.returncode == 0,
              f"gates/ledger_reader_allowlist.py exit={gr.returncode}", failures)
        gh = sh([sys.executable, str(REPO / "gates" / "hash_coverage_gate.py")])
        check("gate-hash-coverage-green-no-reissue", gh.returncode == 0 and "58" in gh.stdout,
              f"gates/hash_coverage_gate.py exit={gh.returncode} on the s45 head (still 58 "
              f"columns -- s45 adds no ledger column, so s42's law does not fire)", failures)
        gh_neg = sh([sys.executable, str(REPO / "gates" / "hash_coverage_gate.py"),
                    "--inject-column", "s45_seenred_probe"])
        check("gate-hash-coverage-negative-control-still-red", gh_neg.returncode == 1,
              f"gates/hash_coverage_gate.py --inject-column exit={gh_neg.returncode} "
              f"(expect 1 -- the gate itself stays alive)", failures)

        os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"] = PGDB, S, K
        try:
            edb_text = ledger_edb.export(S).edb_text()
            res_tnow = ledger_differential.run_differential(S, edb_text=edb_text)
            res_work = ledger_differential.run_layer_differential(S, "work")
        finally:
            del os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"]
        v_tnow, v_work = res_tnow.verdict(), res_work.verdict()
        n_lifecycle = psql_tuples(
            f"SELECT count(*) FROM {S}.ledger WHERE kind IN "
            f"('principal_standing_declared','principal_suspended','principal_revoked');")
        check("differential-agree-with-lifecycle-rows-live",
              v_tnow == "AGREE" and v_work == "AGREE" and int(n_lifecycle) > 0,
              f"tnow={v_tnow} work={v_work} with {n_lifecycle} standing-lifecycle row(s) live "
              f"(declarations/suspensions/revocations/lifts/unbinds all included) -- expect "
              f"AGREE/AGREE", failures)

        rc_v, out_v = verify_chain(wb)
        check("verify-chain-intact-through-s45-writes",
              rc_v == 0 and "INTACT" in out_v,
              f"./verify-chain exit={rc_v}, INTACT through every s45 write and refusal this "
              f"fixture produced", failures)

        # ===================== WORLD NW (the s45-wired --new-world) =====================
        print(f"== REAL --new-world scaffold run ({world_nw}, chain s15..s45) ==")
        tmpnw = Path(tempfile.mkdtemp(prefix=f"{world_nw}-seenred-"))
        tmps.append(tmpnw)
        nwdir = tmpnw / world_nw
        rnw = sh(["bash", str(NEW_PROJECT), str(nwdir), "--new-world", world_nw,
                  "--db", PGDB, "--host", PGHOST])
        det_nw = detect(world_nw, f"{world_nw}_kernel") if rnw.returncode == 0 else "?"
        birth_flags = psql_tuples(
            f"SELECT bool_and(principal_binding_active) FROM {world_nw}.ledger_current "
            f"WHERE kind = 'principal_standing_declared';") if rnw.returncode == 0 else "?"
        rfirst = led(nwdir, "decision", "first write in an s45 world") \
            if rnw.returncode == 0 else None
        # the scaffold's s43 Element 8 DUAL declaration (this world's granted role AND its
        # login role each carry their own standing declaration): undeclaring the granted
        # role's own declaration leaves the LOGIN role's declaration untouched, so a
        # subsequent NULL-actor write (which set_actor resolves against session_user, the
        # LOGIN role) still succeeds -- correct dual-declaration behavior, witnessed rather
        # than assumed. Undeclaring the login role's declaration TOO then makes the world
        # genuinely undeclared, and the next write refuses.
        r_undeclare_nw = led(nwdir, "principal", "undeclare-standing") if rnw.returncode == 0 else None
        undeclare_out_nw = (r_undeclare_nw.stdout + r_undeclare_nw.stderr) if r_undeclare_nw else ""
        r_write_after_one_unbind = led(nwdir, "decision", "write after unbinding the granted role only") \
            if rnw.returncode == 0 else None
        login_role_nw = psql_tuples("SELECT session_user;") if rnw.returncode == 0 else ""
        r_undeclare_login = led(nwdir, "principal", "undeclare-standing", "--db-role", login_role_nw) \
            if rnw.returncode == 0 else None
        r_second_write_undeclared = led(nwdir, "decision", "write after unbinding BOTH declarations") \
            if rnw.returncode == 0 else None
        check("new-world-s45-birth-and-undeclare-round-trip",
              rnw.returncode == 0 and det_nw == "t" and birth_flags == "t"
              and rfirst is not None and rfirst.returncode == 0
              and r_undeclare_nw is not None and r_undeclare_nw.returncode == 0
              and "unbound" in undeclare_out_nw
              and r_write_after_one_unbind is not None and r_write_after_one_unbind.returncode == 0
              and r_undeclare_login is not None and r_undeclare_login.returncode == 0
              and r_second_write_undeclared is not None
              and r_second_write_undeclared.returncode != 0
              and "has no standing declaration" in
              (r_second_write_undeclared.stdout + r_second_write_undeclared.stderr),
              f"scaffold exit={rnw.returncode}; detect={det_nw!r}; birth declarations all "
              f"carry principal_binding_active=true ({birth_flags!r}); first ordinary ./led "
              f"write exit={(rfirst.returncode if rfirst else '?')}; "
              f"`undeclare-standing` (no --db-role, defaults to the world's own granted role) "
              f"exit={(r_undeclare_nw.returncode if r_undeclare_nw else '?')}; a write right "
              f"after STILL SUCCEEDS via the untouched LOGIN-role declaration "
              f"(exit={(r_write_after_one_unbind.returncode if r_write_after_one_unbind else '?')}"
              f", the s43 Element 8 dual-declaration behavior, correctly NOT bricked by one "
              f"unbind); undeclaring the login role '{login_role_nw}' too "
              f"(exit={(r_undeclare_login.returncode if r_undeclare_login else '?')}) THEN makes "
              f"the next NULL-actor write correctly refuse undeclared "
              f"(exit={(r_second_write_undeclared.returncode if r_second_write_undeclared else '?')})",
              failures)

        gid = sh([sys.executable, str(REPO / "gates" / "idris_model_freshness.py")])
        check("idris-freshness-warn-not-red", gid.returncode == 0,
              f"gates/idris_model_freshness.py exit={gid.returncode} (LAGGING-disclosed WARN, "
              f"not a RED failure -- design/Autoharn.idr honestly names the s45 model gap)",
              failures)

    finally:
        for w in (world_a, world_b, world_nw):
            teardown(w)
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- s45 standing-lifecycle both-polarity proof, zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
