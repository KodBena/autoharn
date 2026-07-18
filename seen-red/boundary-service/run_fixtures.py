#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T07:49:10Z
#   last-change: 2026-07-18T07:49:10Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity witness for design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md's
§8 witness plan (W1-W8). Real infra, no mocks: CLASSIC scaffolds + manual chain applies in the
TOY db (the exact pattern seen-red/s43-typed-verdict-write-boundary/run_fixtures.py already
banks, and this fixture imports nothing new for scaffolding -- same helpers, re-derived here
because the two fixtures scaffold DIFFERENT chains for different reasons, not because the
pattern needed a second home), plus a REAL `serving.boundary_service` uvicorn subprocess bound
to loopback, torn down before AND after every world.

WORLDS:
  WORLD PRE -- chain ends at s42 (no s43): W3, every write endpoint capability_absent.
  WORLD B   -- chain ends at s43, full birth via the boundary (author, write-boundary,
               boundary-service): W1 (accepted write + read-back), W2 (refused write,
               journaled, verdict verbatim), W4 (/credited capability_absent, never a
               fallback), W5 (history-with-cause + credited-only-style exclusion from
               /rows/current), W6 (audit_served.py AGREE leg + a tampered negative control
               caught nonzero), the §9 route-count closure assertion.
  (no DB)   -- W7 bind guard, both legs (refusal leg + explicit-flag-allowed leg), standalone
               subprocess invocations of `python3 -m serving.boundary_service`.
  (static)  -- W3's grep half (no DML string in serving/); W8 is UNEXERCISED BY CONSTRUCTION
               (panel-side; this repo never touches the panel repo) and is NAMED, not faked.

Usage: python3 seen-red/boundary-service/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
LINEAGE = REPO / "kernel" / "lineage"
SERVING = REPO / "serving"
PYVENV = Path.home() / "w" / "vdc" / "venvs" / "generic" / "bin" / "python"

sys.path.insert(0, str(REPO / "filing"))
sys.path.insert(0, str(SERVING))
import deployment_record  # noqa: E402
import pghost_resolve  # noqa: E402
import audit_served  # noqa: E402  (compare_row_sets -- the negative-control comparator, reused not re-derived)

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
    "s40-principal-identity-events.sql", "s41-principal-bindings-and-relations.sql",
    "s42-row-hash-full-coverage.sql",
]
CHAIN_PRE = CHAIN_COMMON  # s42 head -- no s43 (WORLD PRE)
CHAIN_B = CHAIN_COMMON + ["s43-typed-verdict-write-boundary.sql"]  # s43 head (WORLD B)

EXPECTED_ROUTES = {
    ("GET", "/health"), ("GET", "/rows/current"), ("GET", "/rows/{row_id}"),
    ("GET", "/rows/{row_id}/history"), ("GET", "/credited"),
    ("GET", "/standing/principals"), ("GET", "/work/items"),
    ("POST", "/write/ledger"), ("POST", "/write/review"),
    ("POST", "/write/registration"), ("POST", "/write/obligation"),
}


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
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-f", "/dev/stdin"], input=script)


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


def birth_pre_s43(world: str) -> None:
    """WORLD PRE has no boundary functions yet -- birth acts are the ordinary direct INSERT,
    exactly as bootstrap/new-project.sh's own pre-s43 scaffold path writes them."""
    S, K, R = world, f"{world}_kernel", f"{world}_rw"
    script = (
        f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
        f"INSERT INTO ledger (kind, statement, actor, principal_subject, principal_purpose)\n"
        f"VALUES ('principal_registered', 'author registered (fixture genesis exception)',\n"
        f"        (SELECT id FROM principal WHERE name='author'),\n"
        f"        (SELECT id FROM principal WHERE name='author'), 'fixture connection principal');\n"
        f"INSERT INTO ledger (kind, statement, actor, principal_subject, principal_db_role)\n"
        f"VALUES ('principal_standing_declared', 'role {R} -> author',\n"
        f"        (SELECT id FROM principal WHERE name='author'),\n"
        f"        (SELECT id FROM principal WHERE name='author'), '{R}');\n")
    r = psql_raw(script)
    if r.returncode != 0:
        raise RuntimeError(f"birth acts failed ({world}): {r.stderr[-600:]}")


def bw_call(world: str, fn: str, payload: dict) -> dict:
    S, K, R = world, f"{world}_kernel", f"{world}_rw"
    pj = json.dumps(payload).replace("'", "''")
    r = psql_raw(
        f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
        f"SELECT to_jsonb(v) FROM {K}.{fn}('{pj}'::jsonb) v;\n")
    if r.returncode != 0:
        raise RuntimeError(f"NON-VERDICT: {r.stderr.strip()[-500:]}")
    line = [ln for ln in r.stdout.splitlines() if ln.strip().startswith("{")][-1]
    return json.loads(line)


def birth_via_boundary(world: str) -> tuple[int, int]:
    """The s40/s43 birth acts through the boundary (WORLD B), PLUS this service's own s40
    registration ceremony (spec §4: "the service is registered at deployment as a principal
    (class tool, the s40 ceremony)") -- `boundary-service`, alongside `write-boundary`.
    Returns (author_id, boundary_service_principal_id)."""
    S, K = world, f"{world}_kernel"
    author = int(psql_tuples(f"SELECT id FROM {K}.principal WHERE name='author';"))
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
        ("registration_write", {"name": "boundary-service", "agent_class": "tool",
                                "actor": author,
                                "purpose": "the FastAPI outer boundary Port's own registered "
                                           "principal (design/FABLE-LEDGER-BOUNDARY-SERVICE-"
                                           "SPEC.md §4 -- fixture-birth ceremony)"}),
    ]:
        v = bw_call(world, fn, payload)
        if v["disposition"] != "accepted":
            raise RuntimeError(f"birth act refused: {v}")
    boundary_service_id = int(psql_tuples(f"SELECT id FROM {K}.principal WHERE name='boundary-service';"))
    return author, boundary_service_id


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def write_scratch_deployment(tmpdir: Path, world: str) -> Path:
    rec = deployment_record.DeploymentRecord(
        db=PGDB, host=PGHOST, schema=world, kern=f"{world}_kernel", role=f"{world}_rw", name=world)
    path = tmpdir / f"{world}-deployment.json"
    deployment_record.write_deployment(path, rec)
    return path


def start_server(deployment_path: Path, host: str = "127.0.0.1", port: int | None = None,
                  extra_flag: bool = False) -> tuple[subprocess.Popen, int]:
    if port is None:
        port = free_port()
    args = [str(PYVENV), "-m", "serving.boundary_service",
            "--deployment", str(deployment_path), "--host", host, "--port", str(port)]
    if extra_flag:
        args.append("--i-understand-this-exposes-the-ledger")
    proc = subprocess.Popen(args, cwd=str(REPO), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True)
    return proc, port


def wait_health(base_url: str, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(base_url + "/health", timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(0.3)
    return False


def http_get(url: str) -> tuple[int, object]:
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def http_post(url: str, payload: dict) -> tuple[int, object]:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def stop_server(proc: subprocess.Popen) -> str:
    proc.terminate()
    try:
        out, _ = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _ = proc.communicate(timeout=5)
    return out or ""


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    procs: list[subprocess.Popen] = []
    world_pre, world_b = "svcfxpre", "svcfxb"
    for w in (world_pre, world_b):
        teardown(w)
    try:
        # ============================= W3: WORLD PRE (no s43) =============================
        print(f"== scaffolding classic world {world_pre} (chain ends {CHAIN_PRE[-1]}) ==")
        wpre = scaffold_classic(world_pre, CHAIN_PRE)
        tmps.append(wpre.parent)
        birth_pre_s43(world_pre)
        dep_pre = write_scratch_deployment(wpre.parent, world_pre)
        proc_pre, port_pre = start_server(dep_pre)
        procs.append(proc_pre)
        up = wait_health(f"http://127.0.0.1:{port_pre}")
        results = {}
        if up:
            for surface in ("ledger", "review", "registration", "obligation"):
                status, body = http_post(f"http://127.0.0.1:{port_pre}/write/{surface}", {"x": "y"})
                results[surface] = (status, body)
        out_pre = stop_server(proc_pre)
        grep_dml = subprocess.run(
            ["grep", "-nE", "INSERT INTO [A-Za-z_.]+ *\\(|UPDATE [A-Za-z_.]+ SET|DELETE FROM [A-Za-z_.]+ ",
             str(SERVING / "boundary_service.py"), str(SERVING / "audit_served.py"),
             str(SERVING / "boundary_models.py")],
            capture_output=True, text=True)
        check("w3-pre-s43-capability-absent-and-no-dml-string",
              up and all(status == 409 and body.get("disposition") == "capability_absent"
                         and body.get("capability") == "s43-boundary"
                         for status, body in results.values())
              and grep_dml.returncode == 1,  # grep exit 1 = no match found anywhere
              f"server up={up}; per-surface (status, disposition, capability)="
              f"{ {k: (v[0], v[1].get('disposition'), v[1].get('capability')) for k, v in results.items()} }; "
              f"grep for INSERT/UPDATE/DELETE DML strings in serving/*.py: "
              f"{'NONE FOUND (exit 1)' if grep_dml.returncode == 1 else grep_dml.stdout}; "
              f"server tail: {out_pre[-300:] if not up else '(server came up cleanly)'}",
              failures)

        # ============================= WORLD B (s43 head) =============================
        print(f"== scaffolding classic world {world_b} (chain ends {CHAIN_B[-1]}) ==")
        wb = scaffold_classic(world_b, CHAIN_B)
        tmps.append(wb.parent)
        author_id, svc_id = birth_via_boundary(world_b)
        dep_b = write_scratch_deployment(wb.parent, world_b)
        proc_b, port_b = start_server(dep_b)
        procs.append(proc_b)
        base = f"http://127.0.0.1:{port_b}"
        up_b = wait_health(base)

        # -- /health: route count (§9 closure), capability manifest, service_principal named.
        st_h, body_h = http_get(base + "/health") if up_b else (0, {})
        check("closure-health-and-route-count",
              up_b and st_h == 200 and body_h.get("capabilities", {}).get("s43_boundary") is True
              and body_h.get("service_principal") == "boundary-service",
              f"health status={st_h} body={body_h}", failures)

        # -- W1: accepted write, read back verbatim.
        st1, v1 = http_post(base + "/write/ledger",
                            {"kind": "note", "statement": "boundary-service W1 accepted write",
                             "actor": author_id}) if up_b else (0, {})
        st1r, row1 = http_get(f"{base}/rows/{v1.get('row_id')}") if up_b and v1.get("disposition") == "accepted" else (0, {})
        check("w1-accepted-write-and-readback",
              up_b and st1 == 200 and v1.get("disposition") == "accepted" and v1.get("row_id")
              and st1r == 200 and row1.get("statement") == "boundary-service W1 accepted write"
              and row1.get("id") == v1.get("row_id"),
              f"POST /write/ledger status={st1} verdict={v1}; GET /rows/{{id}} status={st1r} "
              f"row.statement={row1.get('statement')!r}", failures)

        # -- W2: refused write (illegal kind -> kernel CHECK, journaled, verdict verbatim).
        st2, v2 = http_post(base + "/write/ledger",
                            {"kind": "bogus_kind_not_in_vocabulary",
                             "statement": "boundary-service W2 refused write"}) if up_b else (0, {})
        wr_row = None
        if up_b and v2.get("disposition") == "refused" and v2.get("refusal_id"):
            _, wr_row = http_get(f"{base}/rows/{v2['refusal_id']}")
        check("w2-refused-write-journaled-verdict-verbatim",
              up_b and st2 == 200 and v2.get("disposition") == "refused" and v2.get("sqlstate") == "23514"
              and v2.get("refusal_id") and v2.get("message")
              and wr_row is not None and wr_row.get("kind") == "write_refused"
              and wr_row.get("refusal_sqlstate") == "23514" and wr_row.get("refusal_surface") == "ledger",
              f"POST /write/ledger status={st2} verdict={v2}; committed write_refused row: "
              f"kind={wr_row.get('kind') if wr_row else '?'} "
              f"sqlstate={wr_row.get('refusal_sqlstate') if wr_row else '?'}", failures)

        # -- W4: /credited capability_absent (no fallback -- this world has no s44 view).
        st4, v4 = http_get(base + "/credited") if up_b else (0, {})
        check("w4-credited-capability-absent-never-fallback",
              up_b and st4 == 409 and v4.get("disposition") == "capability_absent"
              and v4.get("capability") == "s44-credited-view",
              f"GET /credited status={st4} body={v4}", failures)

        # -- W5: history-with-cause + credited-only-style exclusion from /rows/current.
        st5a, orig = http_post(base + "/write/ledger",
                               {"kind": "decision", "statement": "W5 original decision",
                                "actor": author_id}) if up_b else (0, {})
        st5b, sup = http_post(base + "/write/ledger",
                              {"kind": "decision", "statement": "W5 superseding decision",
                               "actor": author_id, "supersedes": orig.get("row_id")}) if up_b else (0, {})
        st5h, hist = http_get(f"{base}/rows/{sup.get('row_id')}/history") if up_b else (0, [])
        hist_ids = {r["id"] for r in hist} if isinstance(hist, list) else set()
        st5c, current_page = http_get(f"{base}/rows/current?after_id=0&limit=1000") if up_b else (0, [])
        current_ids = {r["id"] for r in current_page} if isinstance(current_page, list) else set()
        check("w5-history-with-cause-and-current-exclusion",
              up_b and st5a == 200 and st5b == 200 and orig.get("disposition") == "accepted"
              and sup.get("disposition") == "accepted"
              and orig["row_id"] in hist_ids and sup["row_id"] in hist_ids
              and orig["row_id"] not in current_ids and sup["row_id"] in current_ids,
              f"original row {orig.get('row_id')} + superseding row {sup.get('row_id')} both "
              f"reachable via /rows/{{id}}/history ({sorted(hist_ids)}); original ABSENT from "
              f"/rows/current ({orig.get('row_id') in current_ids}), superseding row present "
              f"({sup.get('row_id') in current_ids})", failures)

        # -- W6: audit_served.py AGREE leg + a tampered negative control caught nonzero.
        audit_cp = sh([str(PYVENV), str(SERVING / "audit_served.py"),
                      "--base-url", base, "--deployment", str(dep_b)]) if up_b else None
        served_ok, served_rows = http_get(f"{base}/rows/current?after_id=0&limit=1000") if up_b else (0, [])
        tampered = [dict(r, statement="TAMPERED-FOR-NEGATIVE-CONTROL") for r in served_rows[:1]] + served_rows[1:]
        neg_diffs = audit_served.compare_row_sets(tampered, served_rows) if served_rows else ["no rows to tamper"]
        check("w6-audit-served-agree-and-negative-control",
              up_b and audit_cp is not None and audit_cp.returncode == 0 and "AGREE" in audit_cp.stdout
              and len(neg_diffs) > 0,
              f"audit_served.py exit={audit_cp.returncode if audit_cp else '?'} "
              f"stdout={(audit_cp.stdout.strip() if audit_cp else '?')!r}; tampered-vs-real "
              f"negative control diffs={neg_diffs} (nonzero expected -- the comparator catches "
              f"the deliberate perturbation)", failures)

        # -- §9 closure: the route table IS the enumeration -- fetch the OpenAPI schema and
        # count (method,path) pairs against the spec's fixed §3+§4 table, no more no less.
        st9, schema = http_get(base + "/openapi.json") if up_b else (0, {})
        actual_routes = set()
        if st9 == 200:
            for path, methods in schema.get("paths", {}).items():
                for m in methods:
                    actual_routes.add((m.upper(), path))
        check("closure-route-table-is-the-enumeration",
              up_b and st9 == 200 and actual_routes == EXPECTED_ROUTES,
              f"OpenAPI route set == spec's fixed §3+§4 table: {actual_routes == EXPECTED_ROUTES}; "
              f"actual={sorted(actual_routes)}", failures)

        out_b = stop_server(proc_b)
        if not up_b:
            print(f"  (WORLD B server tail on failure-to-come-up: {out_b[-1000:]})")

    finally:
        for p in procs:
            if p.poll() is None:
                stop_server(p)
        for w in (world_pre, world_b):
            teardown(w)
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    # ============================= W7: bind guard, both legs (no DB) =============================
    tmp7 = Path(tempfile.mkdtemp(prefix="svcfxw7-"))
    try:
        fake_dep = tmp7 / "fake-deployment.json"
        deployment_record.write_deployment(
            fake_dep, deployment_record.DeploymentRecord(
                db="toy", host=PGHOST, schema="doesnotmatterw7", kern="doesnotmatterw7_kernel",
                role="doesnotmatterw7_rw"))
        port7 = free_port()
        r_refused = sh([str(PYVENV), "-m", "serving.boundary_service", "--deployment", str(fake_dep),
                       "--host", "8.8.8.8", "--port", str(port7)], cwd=str(REPO))
        check("w7-bind-guard-refusal-leg",
              r_refused.returncode == 2 and "REFUSED" in r_refused.stderr
              and "--i-understand-this-exposes-the-ledger" in r_refused.stderr,
              f"non-loopback host without the flag: exit={r_refused.returncode}, "
              f"stderr={r_refused.stderr.strip()[-400:]!r} -- refused BEFORE any socket bind "
              f"(construction-time, ADR-0002 rung 1)", failures)

        # WORLD PRE (a throwaway, born just for W7's allowed leg -- torn down immediately after;
        # only /health needs to answer, so a pre-s43 world is deliberately reused rather than a
        # second full s43 scaffold).
        w7world = "svcfxw7ok"
        teardown(w7world)
        w7dir = scaffold_classic(w7world, CHAIN_PRE)
        tmps2 = [w7dir.parent]
        birth_pre_s43(w7world)
        dep7ok = write_scratch_deployment(w7dir.parent, w7world)
        port7b = free_port()
        proc7, _ = start_server(dep7ok, host="0.0.0.0", port=port7b, extra_flag=True)
        up7 = wait_health(f"http://127.0.0.1:{port7b}")
        out7 = stop_server(proc7)
        teardown(w7world)
        for t in tmps2:
            shutil.rmtree(t, ignore_errors=True)
        check("w7-bind-guard-allowed-leg",
              up7,
              f"0.0.0.0 WITH --i-understand-this-exposes-the-ledger: server came up and "
              f"answered /health over loopback (up={up7}); tail={out7[-300:] if not up7 else '(clean)'}",
              failures)
    finally:
        shutil.rmtree(tmp7, ignore_errors=True)

    # ============================= W8: panel-side, UNEXERCISED BY CONSTRUCTION =============
    print("=== w8-deprecation-mark-panel-side ===")
    print("  [UNEXERCISED] the marked legacy path lives in the autoharn-panel repository, which "
          "this build never touches (spec §6, §10.4 'panel-side is a separate session's item "
          "citing this spec'). No live check is possible from this repo; recorded here so the "
          "gap is named, not silently absent from the witness plan.")
    print()

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- boundary-service both-polarity proof (W1-W7 live; W8 UNEXERCISED, named).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
