#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T04:03:04Z
#   last-change: 2026-07-18T04:04:46Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for kernel/lineage/s42-row-hash-full-coverage.sql
(design/FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md §6's s42 witness plan, items
(i)-(vii)). Real infra, no mocks: CLASSIC scaffolds + manual chain applies in the TOY db, torn
down before AND after. Red first, per mechanism.

WORLDS:
  WORLD H -- chain ends at s41 (the v1 serializer): THE HAZARD, RED -- an owner-side tamper of
             `work_parent` on a committed row leaves ./verify-chain reporting INTACT (ledger
             row 1449 witnessed as such); s42 detect reads f.
  WORLD V -- chain ends at s42: s42 detect t; then THE FIX, QUANTIFIED OVER THE CLASS -- a
             scripted loop over EVERY serialized column (all 52, per-column, never sampled)
             tampers that column on a committed fixture row (owner-side, user triggers disabled
             for the tamper, restored after) and asserts ./verify-chain goes BROKEN AT that
             row, then restores and asserts INTACT; the NULL<->empty-string tamper (the s26
             injectivity property re-witnessed under v2); the timezone leg (same rows verified
             INTACT from sessions in two different timezones -- and the harness NOTES the s42
             header's SPEC DIVERGENCE finding: stamp_ts is bigint, so there never was a
             stamp_ts TZ red to reproduce; the two real timestamptz columns are epoch-rendered
             since s26, witnessed green here); gates/hash_coverage_gate.py green on the clean
             head and red under --inject-column (the mutation self-check); ./judge SQL/ASP
             differential in AGREE on this fixture.

Each check() names the witness that would show it false. Usage:
    python3 seen-red/s42-row-hash-full-coverage/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import hashlib
import hmac as hmac_mod
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

import ledger_differential  # noqa: E402
import ledger_edb  # noqa: E402
import pghost_resolve  # noqa: E402

PGHOST, PGDB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_S41 = [
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
]
CHAIN_S42 = CHAIN_S41 + ["s42-row-hash-full-coverage.sql"]

FP = "ABCDEF0123456789ABCDEF0123456789ABCDEF01"
FP2 = "0123456789ABCDEF0123456789ABCDEF01234567"


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
             "-f", str(LINEAGE / "s42-row-hash-full-coverage.detect.sql")])
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


def birth_acts(world: str) -> None:
    S, K, R = world, f"{world}_kernel", f"{world}_rw"
    r = psql_raw(
        f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
        f"INSERT INTO ledger (kind, statement, actor, principal_subject, principal_purpose)\n"
        f"VALUES ('principal_registered', 'author registered (fixture genesis exception)',\n"
        f"        (SELECT id FROM principal WHERE name='author'),\n"
        f"        (SELECT id FROM principal WHERE name='author'), 'fixture connection principal');\n"
        f"INSERT INTO ledger (kind, statement, actor, principal_subject, principal_db_role)\n"
        f"VALUES ('principal_standing_declared', 'role {R} -> author',\n"
        f"        (SELECT id FROM principal WHERE name='author'),\n"
        f"        (SELECT id FROM principal WHERE name='author'), '{R}');\n")
    if r.returncode != 0:
        raise RuntimeError(f"birth acts failed ({world}): {r.stderr[-600:]}")


def verify_chain(world_dir: Path, extra_env: dict | None = None) -> tuple[int, str]:
    e = dict(os.environ)
    if extra_env:
        e.update(extra_env)
    cp = sh(["sh", str(world_dir / "verify-chain")], cwd=str(world_dir), env=e)
    return cp.returncode, cp.stdout + cp.stderr


BREAK_RE = re.compile(r"BROKEN -- first break at row id (\d+)")


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    world_h, world_v = "s42fxh", "s42fxv"
    for w in (world_h, world_v):
        teardown(w)
    try:
        # ===================== WORLD H (s41 head -- the hazard, red) =====================
        print(f"== scaffolding classic world {world_h} (chain ends {CHAIN_S41[-1]}) ==")
        wh = scaffold_classic(world_h, CHAIN_S41)
        tmps.append(wh.parent)
        S, K, R = world_h, f"{world_h}_kernel", f"{world_h}_rw"
        birth_acts(world_h)
        check("detect-f-on-s41", detect(S, K) == "f",
              f"s42 detect on an s41-head chain reads {detect(S, K)!r} (expect f)", failures)
        # a committed work_opened row whose work_parent we then tamper as the owner
        r = psql_raw(f"SET ROLE {R};\nSET search_path={S},{K};\n"
                     f"INSERT INTO ledger (kind, statement, work_slug, work_title) "
                     f"VALUES ('work_opened','hazard fixture','hz','hazard item');\n"
                     f"INSERT INTO ledger (kind, statement) VALUES ('note','tail row');\n")
        if r.returncode != 0:
            raise RuntimeError(f"world H fixture failed: {r.stderr[-500:]}")
        rc0, out0 = verify_chain(wh)
        rt = psql_raw(f"ALTER TABLE {S}.ledger DISABLE TRIGGER USER;\n"
                      f"UPDATE {S}.ledger SET work_parent = 'tampered-parent' "
                      f"WHERE kind = 'work_opened';\n"
                      f"ALTER TABLE {S}.ledger ENABLE TRIGGER USER;\n")
        rc1, out1 = verify_chain(wh)
        check("hazard-red-v1-blind-to-post-s24-columns",
              rc0 == 0 and rt.returncode == 0 and rc1 == 0 and "INTACT" in out1,
              f"pre-tamper verify exit={rc0}; owner-tamper of work_parent on a committed row "
              f"then verify exit={rc1} with {'INTACT' if 'INTACT' in out1 else out1[-120:]!r} "
              f"-- the v1 chain does NOT see it (ledger row 1449's hazard, witnessed as such; "
              f"under s42 the same tamper is the per-column loop's red)", failures)

        # ===================== WORLD V (s42 head -- the fix) =====================
        print(f"== scaffolding classic world {world_v} (chain ends {CHAIN_S42[-1]}) ==")
        wv = scaffold_classic(world_v, CHAIN_S42)
        tmps.append(wv.parent)
        S, K, R = world_v, f"{world_v}_kernel", f"{world_v}_rw"
        birth_acts(world_v)
        check("detect-t-on-s42", detect(S, K) == "t",
              f"s42 detect on the s42 chain reads {detect(S, K)!r} (expect t)", failures)

        # -- fixture rows: one legal carrier per serialized column (all through the GRANTED
        #    role's ordinary INSERT path -- kernel semantics fully live at write time).
        # register a HUMAN principal (key bindings demand one) through the full ceremony.
        r = psql_raw(
            f"SET ROLE {R};\nSET search_path={S},{K};\n"
            f"WITH new_p AS (INSERT INTO principal (name, agent_class) VALUES ('hume','human') RETURNING id)\n"
            f"INSERT INTO ledger (kind,statement,actor,principal_subject,principal_purpose)\n"
            f"SELECT 'principal_registered','fx: hume registered',"
            f"(SELECT id FROM principal WHERE name='author'),id,'human fixture' FROM new_p;\n")
        if r.returncode != 0:
            raise RuntimeError(f"hume registration failed: {r.stderr[-500:]}")
        author = psql_tuples(f"SELECT id FROM {K}.principal WHERE name='author';")
        hume = psql_tuples(f"SELECT id FROM {K}.principal WHERE name='hume';")
        # stamped note (real HMAC against the world's own secret) -- the stamp-column carrier,
        # also carrying event_declared_ts (a real timestamptz) and the full prose columns.
        secret = bytes.fromhex(psql_tuples(f"SELECT encode(secret,'hex') FROM {K}.stamp_secret;"))
        ts0 = int(time.time())
        mac0 = hmac_mod.new(secret, f"sessFX|agent0|{ts0}".encode(), hashlib.sha256).hexdigest()
        r = psql_raw(
            f"SET ROLE {R};\nSET search_path={S},{K};\n"
            f"SELECT set_config('app.vendor_session','sessFX',false),"
            f" set_config('app.vendor_agent','agent0',false),"
            f" set_config('app.vendor_ts','{ts0}',false),"
            f" set_config('app.vendor_hmac','{mac0}',false) \\gset _\n"
            f"INSERT INTO ledger (kind,statement,rationale,evidence,confidence,refs,concern,"
            f"event_declared_ts) VALUES ('note','fx: stamped','why','row:1','high','row:2',"
            f"'process', now() - interval '1 hour');\n")
        if r.returncode != 0:
            raise RuntimeError(f"stamped note failed: {r.stderr[-500:]}")
        # work lifecycle + violation disposition + question/answer + bindings + competence
        r = psql_raw(
            f"SET ROLE {R};\nSET search_path={S},{K};\n"
            f"INSERT INTO ledger (kind,statement) VALUES ('question','fx: q');\n"
            f"INSERT INTO ledger (kind,statement,work_slug,work_title) "
            f"VALUES ('work_opened','fx: open','fxa','fixture item');\n"
            f"INSERT INTO ledger (kind,statement,work_slug) VALUES ('work_claimed','fx: claim','fxa');\n"
            f"INSERT INTO ledger (kind,statement,work_slug,work_depends_on,edge_type) "
            f"VALUES ('work_depends_on','fx: dep','fxa','ghost','informs');\n"
            f"INSERT INTO ledger (kind,statement,work_slug,work_resolution,work_witness,"
            f"work_review_disposition,work_review_ref,work_strict_close) "
            f"VALUES ('work_closed','fx: close','fxa','dropped','row:1','witnessed','row:2',false);\n"
            f"INSERT INTO ledger (kind,statement,work_violation_class,work_violation_target_id,"
            f"work_resolution,rationale,work_review_disposition,work_review_ref) "
            f"SELECT 'work_violation_disposition','fx: vd','depends_on_unknown_slug',v.target_id,"
            f"'retired','moot in fixture','witnessed','row:2' "
            f"FROM work_item_violations v WHERE v.violation='depends_on_unknown_slug' LIMIT 1;\n"
            f"INSERT INTO ledger (kind,statement,answers) "
            f"SELECT 'decision','fx: answer',q.id FROM ledger q WHERE q.statement='fx: q';\n"
            f"INSERT INTO ledger (kind,statement,principal_subject,principal_object,"
            f"principal_relation,principal_binding_active) VALUES "
            f"('principal_relation_asserted','fx: rel',{hume},{author},'acts-for',true);\n"
            f"INSERT INTO ledger (kind,statement,principal_subject,principal_role_name,"
            f"principal_binding_active) VALUES ('principal_role_bound','fx: role',{hume},'scout',true);\n"
            f"INSERT INTO ledger (kind,statement,principal_subject,principal_role_name,"
            f"principal_binding_active,supersedes) SELECT 'principal_role_bound','fx: role-out',"
            f"{hume},'scout',false,b.id FROM ledger b WHERE b.statement='fx: role';\n"
            f"INSERT INTO ledger (kind,statement,principal_subject,principal_key_fingerprint,"
            f"principal_binding_active) VALUES ('principal_key_bound','fx: key',{hume},'{FP}',true);\n"
            f"INSERT INTO ledger (kind,statement,principal_subject,principal_competence_activity,"
            f"principal_competence_band,principal_competence_basis,principal_binding_active) VALUES "
            f"('principal_competence_granted','fx: comp',{hume},'sql-review','B','track record',true);\n"
            f"INSERT INTO ledger (kind,statement,amends,amends_scope) "
            f"SELECT 'revision','fx: amends',n.id,'fx: stamped' FROM ledger n WHERE n.statement='fx: stamped';\n"
            f"INSERT INTO ledger (kind,statement,enacts) "
            f"SELECT 'note','fx: enacts',ARRAY[n.id] FROM ledger n WHERE n.statement='fx: stamped';\n"
            f"INSERT INTO ledger (kind,statement) VALUES ('note','fx: tail');\n")
        if r.returncode != 0:
            raise RuntimeError(f"fixture rows failed: {r.stdout[-500:]} {r.stderr[-800:]}")
        # one review + review_detail pair (the regards carrier) through a distinct stamped agent
        ts1 = int(time.time())
        mac1 = hmac_mod.new(secret, f"sessFX|agentR|{ts1}".encode(), hashlib.sha256).hexdigest()
        r = psql_raw(
            f"SET ROLE {R};\nSET search_path={S},{K};\n"
            f"SELECT set_config('app.vendor_session','sessFX',false),"
            f" set_config('app.vendor_agent','agentR',false),"
            f" set_config('app.vendor_ts','{ts1}',false),"
            f" set_config('app.vendor_hmac','{mac1}',false) \\gset _\n"
            f"BEGIN;\n"
            f"INSERT INTO ledger (kind,statement,regards,actor) SELECT 'review','fx: review',n.id,"
            f"{hume} FROM ledger n WHERE n.statement='fx: stamped' RETURNING id \\gset r_\n"
            f"INSERT INTO review_detail (ledger_id,verdict,independence,basis) VALUES "
            f"(:r_id,'attest','technical','fx basis');\nCOMMIT;\n")
        if r.returncode != 0:
            raise RuntimeError(f"review pair failed: {r.stdout[-400:]} {r.stderr[-600:]}")

        rc, out = verify_chain(wv)
        check("intact-before-tampering", rc == 0 and "INTACT" in out,
              f"verify-chain exit={rc} on the untampered fixture chain", failures)

        # -- row ids by marker, for the per-column tamper plan
        def row_id(marker: str) -> str:
            return psql_tuples(f"SELECT id FROM {S}.ledger WHERE statement = '{marker}';")

        rid = {m: row_id(m) for m in
               ("fx: stamped", "fx: open", "fx: claim", "fx: dep", "fx: close", "fx: vd",
                "fx: rel", "fx: role", "fx: role-out", "fx: key", "fx: comp", "fx: review",
                "fx: amends", "fx: answer", "fx: enacts", "fx: tail")}
        reg_id = psql_tuples(f"SELECT id FROM {S}.ledger WHERE kind='principal_registered' "
                             f"AND statement LIKE '%genesis exception%';")
        decl_id = psql_tuples(f"SELECT id FROM {S}.ledger WHERE kind='principal_standing_declared';")

        # THE PER-COLUMN TAMPER PLAN -- all 52 serialized columns, each (target row id, tamper
        # SQL expression legal under every table CHECK/FK with user triggers disabled). The
        # completeness of THIS list is itself asserted below against the live catalog, so a
        # future column cannot silently drop out of the loop.
        plan: dict[str, tuple[str, str]] = {
            "id":            (rid["fx: tail"], "id + 1000"),
            "ts":            (rid["fx: stamped"], "ts + interval '1 second'"),
            "session":       (rid["fx: stamped"], "'other-session'"),
            "kind":          (rid["fx: tail"], "'decision'"),
            "statement":     (rid["fx: tail"], "'tampered statement'"),
            "rationale":     (rid["fx: stamped"], "'tampered why'"),
            "status":        (rid["fx: stamped"], "'held'"),
            "evidence":      (rid["fx: stamped"], "'row:3'"),
            "confidence":    (rid["fx: stamped"], "'low'"),
            "supersedes":    (rid["fx: tail"], reg_id),
            "refs":          (rid["fx: stamped"], "'row:9'"),
            "concern":       (rid["fx: stamped"], "'design'"),
            "enacts":        (rid["fx: enacts"], f"ARRAY[{reg_id}::bigint]"),
            "actor":         (rid["fx: stamped"], hume),
            "regards":       (rid["fx: review"], reg_id),
            "amends":        (rid["fx: amends"], reg_id),
            "amends_scope":  (rid["fx: amends"], "'tampered scope quote'"),
            "answers":       (rid["fx: answer"], reg_id),
            "stamp_session": (rid["fx: stamped"], "'sessZZ'"),
            "stamp_agent":   (rid["fx: stamped"], "'agentZZ'"),
            "stamp_ts":      (rid["fx: stamped"], "stamp_ts + 1"),
            "stamp_hmac":    (rid["fx: stamped"], "repeat('0', 64)"),
            "stamp_verified": (rid["fx: stamped"], "NOT stamp_verified"),
            "work_slug":     (rid["fx: claim"], "'fxb'"),
            "work_title":    (rid["fx: open"], "'tampered title'"),
            "work_depends_on": (rid["fx: dep"], "'phantom'"),
            "work_resolution": (rid["fx: close"], "'deferred'"),
            "work_witness":  (rid["fx: close"], "'row:7'"),
            "stamp_invocation": (rid["fx: stamped"], "'tok-tampered'"),
            "event_declared_ts": (rid["fx: stamped"], "event_declared_ts + interval '1 hour'"),
            "work_parent":   (rid["fx: open"], "'phantom-parent'"),
            "work_review_disposition": (rid["fx: close"], "'deferred'"),
            "work_review_ref": (rid["fx: close"], "'row:8'"),
            "work_strict_close": (rid["fx: close"], "NOT work_strict_close"),
            "edge_type":     (rid["fx: dep"], "'blocks-close'"),
            "work_discharge": (rid["fx: open"], "'composite'"),
            "decision_grade": (rid["fx: answer"], "'durable'"),
            "work_violation_class": (rid["fx: vd"], "'dependency_cycle'"),
            "work_violation_target_id": (rid["fx: vd"], reg_id),
            "work_violation_witness": (rid["fx: vd"], reg_id),
            "principal_subject": (reg_id, hume),
            "principal_purpose": (reg_id, "'tampered purpose'"),
            "principal_db_role": (decl_id, "'other_role'"),
            "principal_actor_resolution": (rid["fx: stamped"], "'explicit'"),
            "principal_binding_active": (rid["fx: role-out"], "true"),
            "principal_object": (rid["fx: rel"], hume),
            "principal_relation": (rid["fx: rel"], "'succeeds'"),
            "principal_role_name": (rid["fx: role"], "'tampered-role'"),
            "principal_key_fingerprint": (rid["fx: key"], f"'{FP2}'"),
            "principal_competence_activity": (rid["fx: comp"], "'other-activity'"),
            "principal_competence_band": (rid["fx: comp"], "'A'"),
            "principal_competence_basis": (rid["fx: comp"], "'tampered basis'"),
        }
        live_cols = set(psql_tuples(
            f"SELECT column_name FROM information_schema.columns WHERE table_schema='{S}' "
            f"AND table_name='ledger';").splitlines())
        check("tamper-plan-covers-every-serialized-column",
              set(plan) == live_cols - {"row_hash"},
              f"plan covers {len(plan)} columns; catalog minus row_hash has "
              f"{len(live_cols) - 1}; symmetric difference: "
              f"{sorted(set(plan) ^ (live_cols - {'row_hash'}))!r}", failures)

        # the per-column loop: tamper (owner-side, user triggers off) -> BROKEN AT the row ->
        # restore -> INTACT. `id` is the one special case: the break lands at the NEW id.
        bad_cols: list[str] = []
        for col, (target, expr) in plan.items():
            orig = psql_tuples(
                f"SELECT COALESCE({col}::text, '\\N') FROM {S}.ledger WHERE id = {target};")
            rt = psql_raw(f"ALTER TABLE {S}.ledger DISABLE TRIGGER USER;\n"
                          f"UPDATE {S}.ledger SET {col} = ({expr}) WHERE id = {target};\n"
                          f"ALTER TABLE {S}.ledger ENABLE TRIGGER USER;\n")
            if rt.returncode != 0:
                bad_cols.append(f"{col} (tamper itself failed: {rt.stderr.strip()[-120:]})")
                continue
            rc_b, out_b = verify_chain(wv)
            m = BREAK_RE.search(out_b)
            if col != "id":
                expect_id = target
            else:
                # an id tamper MOVES the row in walk order: the break surfaces at the first
                # row whose predecessor-hash re-points across the gap -- the original row's
                # SUCCESSOR when one exists (its stored hash embedded the old id's hash), else
                # at the relocated row itself. Exactly verify-chain's own documented "no later
                # than immediately after the true alteration point".
                succ = psql_tuples(f"SELECT COALESCE(min(id)::text, '') FROM {S}.ledger "
                                   f"WHERE id > {target} AND id < {int(target) + 1000};")
                expect_id = succ if succ else str(int(target) + 1000)
            if rc_b != 1 or not m or m.group(1) != expect_id:
                bad_cols.append(f"{col} (exit={rc_b}, break at "
                                f"{m.group(1) if m else 'NONE'!r}, expected {expect_id})")
            # restore (typed cast back from the captured text; '\\N' marks SQL NULL)
            if orig == "\\N":
                restore_val = "NULL"
            else:
                esc = orig.replace("'", "''")
                coltype = psql_tuples(
                    f"SELECT format_type(a.atttypid, a.atttypmod) FROM pg_attribute a "
                    f"JOIN pg_class c ON c.oid = a.attrelid "
                    f"JOIN pg_namespace n ON n.oid = c.relnamespace "
                    f"WHERE n.nspname='{S}' AND c.relname='ledger' AND a.attname='{col}';")
                restore_val = f"'{esc}'::{coltype}"
            where_id = target if col != "id" else str(int(target) + 1000)
            rr = psql_raw(f"ALTER TABLE {S}.ledger DISABLE TRIGGER USER;\n"
                          f"UPDATE {S}.ledger SET {col} = {restore_val} WHERE id = {where_id};\n"
                          f"ALTER TABLE {S}.ledger ENABLE TRIGGER USER;\n")
            if rr.returncode != 0:
                bad_cols.append(f"{col} (RESTORE failed: {rr.stderr.strip()[-120:]})")
                break
        rc_f, out_f = verify_chain(wv)
        check("per-column-tamper-breaks-at-the-row-all-52",
              not bad_cols and rc_f == 0 and "INTACT" in out_f,
              f"every serialized column's tamper broke the chain AT its row and restored clean "
              f"(final verify exit={rc_f}); deviations: {bad_cols!r}", failures)

        # NULL <-> empty-string tamper on a text column (the s26 injectivity property, under v2)
        rt = psql_raw(f"ALTER TABLE {S}.ledger DISABLE TRIGGER USER;\n"
                      f"UPDATE {S}.ledger SET rationale = '' WHERE id = {rid['fx: tail']};\n"
                      f"ALTER TABLE {S}.ledger ENABLE TRIGGER USER;\n")
        rc_n, out_n = verify_chain(wv)
        m = BREAK_RE.search(out_n)
        psql_raw(f"ALTER TABLE {S}.ledger DISABLE TRIGGER USER;\n"
                 f"UPDATE {S}.ledger SET rationale = NULL WHERE id = {rid['fx: tail']};\n"
                 f"ALTER TABLE {S}.ledger ENABLE TRIGGER USER;\n")
        check("null-vs-empty-injectivity-v2",
              rt.returncode == 0 and rc_n == 1 and m and m.group(1) == rid["fx: tail"],
              f"NULL->'' tamper on rationale: verify exit={rc_n}, break at "
              f"{(m.group(1) if m else None)!r} (expect {rid['fx: tail']}) -- hashfield's "
              f"N:/V0: distinction holding under the v2 serialization", failures)

        # the timezone leg: same rows verified INTACT from two different session timezones
        # (PGTZ reaches every psql the verb spawns). SPEC-DIVERGENCE NOTE, witnessed: stamp_ts
        # is BIGINT (epoch seconds) -- there never was a stamp_ts timezone hazard to reproduce
        # red (the s42 delta header's own finding); the two real timestamptz columns
        # (ts, event_declared_ts) are epoch-rendered and this leg witnesses the whole
        # serialization timezone-independent end to end.
        stamp_type = psql_tuples(
            f"SELECT data_type FROM information_schema.columns WHERE table_schema='{S}' "
            f"AND table_name='ledger' AND column_name='stamp_ts';")
        rc_tz1, out_tz1 = verify_chain(wv, {"PGTZ": "UTC"})
        rc_tz2, out_tz2 = verify_chain(wv, {"PGTZ": "Pacific/Kiritimati"})
        check("timezone-independence",
              stamp_type == "bigint" and rc_tz1 == 0 and rc_tz2 == 0
              and "INTACT" in out_tz1 and "INTACT" in out_tz2,
              f"stamp_ts catalog type={stamp_type!r} (bigint -- the spec §3.1 divergence "
              f"finding, witnessed); verify INTACT under PGTZ=UTC (exit={rc_tz1}) and "
              f"PGTZ=Pacific/Kiritimati (exit={rc_tz2}) on rows carrying non-NULL stamp_ts "
              f"AND event_declared_ts", failures)

        # the coverage gate: green on the clean head, red under the injected column
        gg = sh([sys.executable, str(REPO / "gates" / "hash_coverage_gate.py")])
        gr = sh([sys.executable, str(REPO / "gates" / "hash_coverage_gate.py"),
                 "--inject-column", "zz_seenred_probe"])
        check("coverage-gate-both-polarities",
              gg.returncode == 0 and gr.returncode == 1
              and "zz_seenred_probe" in gr.stdout,
              f"clean head exit={gg.returncode} (expect 0); --inject-column exit="
              f"{gr.returncode} (expect 1) naming the injected column", failures)

        # ./judge SQL/ASP differential in AGREE on this fixture
        os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"] = PGDB, S, K
        try:
            edb_text = ledger_edb.export(S).edb_text()
            res_tnow = ledger_differential.run_differential(S, edb_text=edb_text)
            res_work = ledger_differential.run_layer_differential(S, "work")
        finally:
            del os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"]
        v_tnow, v_work = res_tnow.verdict(), res_work.verdict()
        check("differential-agree-both-layers",
              v_tnow == "AGREE" and v_work == "AGREE",
              f"tnow={v_tnow} work={v_work} on the s42 fixture (expect AGREE/AGREE)", failures)

    finally:
        for w in (world_h, world_v):
            teardown(w)
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- s42 row-hash-full-coverage both-polarity proof, zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
