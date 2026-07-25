#!/usr/bin/env python3
"""Seen-red specimen for TWO courier findings (strengthened-tier review lap 2, serving axis):

MODERATE-SILENT (courier:123-207, batch-witness loss): when `_require()` raises on row N
mid-batch, earlier rows' outcomes (accepted AND refused) in the SAME run vanished from the
operator-facing report -- the reviewer witnessed a kernel-refused row 1 reported NOWHERE on
stdout when row 2 tripped `_require()`. FIX: `run_counterpart()` now accumulates a per-row
`outcomes` list AS PROCESSED and, on a mid-batch `_require()` raise, prints the accumulated
outcomes via `_print_batch_report()` before the exception propagates.

MODERATE-LOUD (courier:226-277, per-counterpart exit-code collapse): counterpart-side
`ProtocolVersionMismatch`/`BoundaryUnreachable`/`BoundaryRefusal`/`CourierConfigError` all
collapsed to exit 1, defeating bcc's own exit-code class discipline (0/1/3/4). FIX: `main()`
now tags each counterpart failure with bcc's own code for its class and, if every failure this
run belongs to ONE class, exits with THAT code; mixed classes exit 1 with a stderr line
enumerating every class seen.

Both reproduced RED against a deliberately reverted (never committed, discarded) copy of the
pre-fix code, and GREEN against the real, current `courier` -- a REAL boundary_service.py
instance (scratch port, never 8433/8422) plus REAL mock counterpart HTTP servers (stdlib
http.server, not stubbed at the Python-object level) reproducing each exact scenario the
reviewer's own fixed report describes.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

PGHOST = os.environ.get("HARNESS_PGHOST") or os.environ.get("EPISTEMIC_PGHOST") or "192.168.122.1"
PGDB = os.environ.get("HARNESS_PGDB", "toy")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LINEAGE = os.path.join(REPO, "kernel", "lineage")
COURIER = os.path.join(REPO, "courier")
SERVING = os.path.join(REPO, "serving")

CHAIN = [
    "high_watermark_1.sql", "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
    "s25-commission-kind.sql", "s26-row-hash-chain.sql", "s27-chain-high-water.sql",
    "s28-work-parent-edge.sql", "s29-obligation-item-key-and-typed-close.sql",
    "s30-typed-dependency-edges.sql", "s31-supersession-uniform-retraction.sql",
    "s32-edge-views-single-home.sql", "s33-composite-discharge.sql",
    "s34-computed-grade-refusal.sql", "s35-validation-decomposition.sql",
    "s36-decision-grade.sql", "s37-violation-disposition.sql", "s38-bookkeeping-close.sql",
    "s39-blocks-start.sql", "s40-principal-identity-events.sql",
    "s41-principal-bindings-and-relations.sql", "s42-row-hash-full-coverage.sql",
    "s43-typed-verdict-write-boundary.sql", "s45-standing-lifecycle.sql",
    "s44-model-identity-attestation.sql", "s46-credited-views.sql",
    "s47-claim-on-closed-refusal.sql", "s48-review-witness-existence.sql",
    "s49-journaler-overflow-guard.sql", "s50-defeat-input-raw-domain.sql",
    "s51-artifact-store.sql", "s52-artifact-witness-check.sql", "s53-belief-substrate.sql",
    "s54-belief-views.sql", "s55-dispatch-grain-independence.sql",
    "s56-reservation-residue.sql", "s57-obligation-revocation-event.sql",
    "s58-missive-substrate.sql", "s59-missive-views.sql",
]

FAILURES: list[str] = []


def _check(label: str, cond: bool) -> None:
    print(f"  [{'ok' if cond else 'FAIL'}] {label}")
    if not cond:
        FAILURES.append(label)


def sh(args: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def teardown(schema: str, kern: str, role: str) -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {schema} CASCADE; DROP SCHEMA IF EXISTS {kern} CASCADE;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {role};"])


def apply_chain(schema: str, kern: str, role: str) -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"CREATE ROLE {role} LOGIN;"])
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}"]
    for f in CHAIN:
        args += ["-f", os.path.join(LINEAGE, f)]
    cp = sh(args)
    if cp.returncode != 0:
        raise RuntimeError(f"chain apply FAILED:\n{cp.stdout[-2000:]}\n{cp.stderr[-2000:]}")


def dosql(schema: str, kern: str, role: str, sql: str) -> str:
    script = f"SET ROLE {role};\nSET search_path = {schema}, {kern};\n{sql}"
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1"], input=script)
    if cp.returncode != 0:
        raise RuntimeError(f"SQL failed:\n{cp.stdout}\n{cp.stderr}")
    return cp.stdout + cp.stderr


def birth(schema: str, kern: str, role: str, wname: str) -> None:
    genesis = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
        f"INSERT INTO {kern}.chain_genesis (seed) VALUES ('{genesis}') "
        f"ON CONFLICT (only_one) DO NOTHING;"])
    login_role = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAc", "SELECT session_user;"]).stdout.strip()
    dosql(schema, kern, role, f"""
DO $bw$
DECLARE v {kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {kern}.ledger_write(jsonb_build_object(
    'kind', 'principal_registered', 'statement', 'author self-attributed',
    'actor', (SELECT id FROM principal WHERE name = 'author'),
    'principal_subject', (SELECT id FROM principal WHERE name = 'author'),
    'principal_purpose', 'courier witness fixture'));
  IF v.disposition <> 'accepted' THEN RAISE EXCEPTION 'refused: %', v.message; END IF;
END $bw$;
""")
    for drole in (role, login_role):
        dosql(schema, kern, role, f"""
SELECT set_config('birth.drole', '{drole}', false);
DO $bw$
DECLARE v {kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {kern}.ledger_write(jsonb_build_object(
    'kind', 'principal_standing_declared', 'statement', 'standing',
    'actor', (SELECT id FROM principal WHERE name = 'author'),
    'principal_subject', (SELECT id FROM principal WHERE name = 'author'),
    'principal_db_role', current_setting('birth.drole'),
    'principal_binding_active', true));
  IF v.disposition <> 'accepted' THEN RAISE EXCEPTION 'refused: %', v.message; END IF;
END $bw$;
""")
    for pname, pclass in (("write-boundary", "tool"), ("courier", "tool")):
        dosql(schema, kern, role, f"""
SELECT set_config('birth.pname', '{pname}', false), set_config('birth.pclass', '{pclass}', false);
DO $bw$
DECLARE v {kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {kern}.registration_write(jsonb_build_object(
    'name', current_setting('birth.pname'), 'agent_class', current_setting('birth.pclass'),
    'purpose', 'courier witness fixture', 'statement', 'registered',
    'actor', (SELECT id FROM principal WHERE name = 'author')));
  IF v.disposition <> 'accepted' THEN RAISE EXCEPTION '% registration refused: %', current_setting('birth.pname'), v.message; END IF;
END $bw$;
""")
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
        f"INSERT INTO {kern}.world_identity (world_name) VALUES ('{wname}') "
        f"ON CONFLICT (one_row) DO NOTHING;"])


# ------------------------------------------------------------------------------------------
# Mock counterpart HTTP servers (real sockets, stdlib http.server -- not Python-level stubs).
# ------------------------------------------------------------------------------------------

class _BatchLossHandler(BaseHTTPRequestHandler):
    """world=mockworld: row 1 has a malformed missive_provenance (real kernel refusal on the
    self side); row 2 is missing 'missive_act' entirely (courier's own _require())."""
    ROW1 = {"id": 1, "ts": "2026-07-25T00:00:00+00:00", "statement": "row one",
            "missive_act": "request", "missive_seq": 1, "missive_cites": None,
            "missive_thread": "mockworld/batch-1", "missive_protocol": 1,
            "missive_provenance": "xrow:mockworld:1:ZZZZ",
            "missive_disposition": None, "missive_responds_to": None,
            "missive_author_world": "mockworld", "missive_addressee_world": "selfworld"}
    ROW2 = {"id": 2, "ts": "2026-07-25T00:00:01+00:00", "statement": "row two",
            "missive_seq": 2, "missive_cites": None,
            "missive_thread": "mockworld/batch-2", "missive_protocol": 1,
            "missive_provenance": "xrow:mockworld:2:" + "a" * 64,
            "missive_disposition": None, "missive_responds_to": None,
            "missive_author_world": "mockworld", "missive_addressee_world": "selfworld"}

    def log_message(self, fmt, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/d/mockworld/health"):
            body = json.dumps({"world": "mockworld", "service_principal": None,
                               "capabilities": {}, "protocol_version": "1",
                               "authn_mode": "single-operator"}).encode()
        elif self.path.startswith("/d/mockworld/views/missive_outbound"):
            body = (json.dumps([self.ROW1, self.ROW2]).encode()
                    if "after_id=0" in self.path or "after_id=" not in self.path
                    else json.dumps([]).encode())
        else:
            self.send_response(404); self.end_headers(); self.wfile.write(b'{"detail":"nf"}')
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)


class _RefusalHandler(BaseHTTPRequestHandler):
    """world configurable via class attribute WORLD -- health OK, outbound 404s."""
    WORLD = "refusalworld"

    def log_message(self, fmt, *a):
        pass

    def do_GET(self):
        if self.path.startswith(f"/d/{self.WORLD}/health"):
            body = json.dumps({"world": self.WORLD, "service_principal": None,
                               "capabilities": {}, "protocol_version": "1",
                               "authn_mode": "single-operator"}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.end_headers(); self.wfile.write(body)
        elif self.path.startswith(f"/d/{self.WORLD}/views/missive_outbound"):
            self.send_response(404); self.send_header("Content-Type", "application/json")
            self.end_headers(); self.wfile.write(b'{"detail":"unknown_view (mock refusal)"}')
        else:
            self.send_response(404); self.end_headers(); self.wfile.write(b'{"detail":"nf"}')


def _make_refusal_handler(world: str) -> type:
    return type(f"_RefusalHandler_{world}", (_RefusalHandler,), {"WORLD": world})


class _SkewHandler(BaseHTTPRequestHandler):
    """world=skewworld: health answers a WRONG protocol_version."""
    def log_message(self, fmt, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/d/skewworld/health"):
            body = json.dumps({"world": "skewworld", "service_principal": None,
                               "capabilities": {}, "protocol_version": "999",
                               "authn_mode": "single-operator"}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.end_headers(); self.wfile.write(body)
        else:
            self.send_response(404); self.end_headers(); self.wfile.write(b'{"detail":"nf"}')


def _serve(handler_cls: type) -> tuple[HTTPServer, int]:
    srv = HTTPServer(("127.0.0.1", 0), handler_cls)
    port = srv.server_address[1]
    t = Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, port


def _wait_up(port: int, path: str) -> None:
    for _ in range(50):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=0.2)
            return
        except Exception:
            time.sleep(0.05)
    raise RuntimeError(f"mock server on port {port} never came up")


def _run_courier(courier_path: str, toml_path: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    return sh(["python3", courier_path, "--courier-toml", toml_path], env=env, cwd=REPO)


def _write_toml(path: str, self_base: str, counterparts: dict[str, str]) -> None:
    lines = ["[courier]", 'authn = "single-operator"', 'self = "selfworld"',
             f'self_base = "{self_base}"', "", "[courier.counterparts]"]
    for name, base in counterparts.items():
        lines.append(f'{name} = "{base}"')
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def _reverted_courier_no_batch_report(tmp_path: str) -> None:
    """A throwaway copy of `courier` with the batch-witness-loss fix reverted (no `outcomes`
    accumulation, no `_print_batch_report` call) -- reproduces the reviewer's own finding.
    Never committed; discarded after use."""
    with open(COURIER) as f:
        text = f.read()
    old = '''    outcomes: list[str] = []
    for r in candidates:
        try:
            payload = {
                "kind": "missive_received",
                "statement": _require(r, "statement", route=outbound_route, counterpart=counterpart),
                "actor": actor_id,
                "missive_protocol": _require(r, "missive_protocol", route=outbound_route, counterpart=counterpart),
                "missive_author_world": _require(r, "missive_author_world", route=outbound_route, counterpart=counterpart),
                "missive_addressee_world": _require(r, "missive_addressee_world", route=outbound_route, counterpart=counterpart),
                "missive_thread": _require(r, "missive_thread", route=outbound_route, counterpart=counterpart),
                "missive_seq": _require(r, "missive_seq", route=outbound_route, counterpart=counterpart),
                "missive_act": _require(r, "missive_act", route=outbound_route, counterpart=counterpart),
                "missive_provenance": _require(r, "missive_provenance", route=outbound_route, counterpart=counterpart),
            }
        except CourierConfigError:
            _print_batch_report(counterpart, outcomes)
            raise
        if r.get("missive_responds_to") is not None:
            payload["missive_responds_to"] = r["missive_responds_to"]
        if r.get("missive_cites") is not None:
            payload["missive_cites"] = r["missive_cites"]
        exit_code, verdict = bcc.post_write(f"{self_base}/d/{self_name}", "ledger", payload)
        if exit_code == 0:
            recorded.append(verdict["row_id"])
            outcomes.append(f"row id={r['id']} thread={r['missive_thread']!r} "
                            f"seq={r['missive_seq']}: accepted (recorded row_id={verdict['row_id']})")
        else:
            msg = verdict.get("message") or ""
            if "already exists" in msg and "exactly-once RECORDING" in msg:
                dedup_raced += 1  # the race backstop, spec §5 step 3 -- logged, pass continues.
                outcomes.append(f"row id={r['id']} thread={r['missive_thread']!r} "
                                f"seq={r['missive_seq']}: refused (dedup race, idempotent)")
            else:
                errors.append(
                    f"missive (thread={r['missive_thread']!r} seq={r['missive_seq']}) refused "
                    f"NOT as a dedup race: {msg}")
                outcomes.append(f"row id={r['id']} thread={r['missive_thread']!r} "
                                f"seq={r['missive_seq']}: refused (NOT dedup): {msg}")

    return {
        "pulled": len(outbound), "new": len(candidates),
        "recorded": recorded, "dedup_raced": dedup_raced, "errors": errors, "outcomes": outcomes,
    }'''
    new = '''    for r in candidates:
        payload = {
            "kind": "missive_received",
            "statement": _require(r, "statement", route=outbound_route, counterpart=counterpart),
            "actor": actor_id,
            "missive_protocol": _require(r, "missive_protocol", route=outbound_route, counterpart=counterpart),
            "missive_author_world": _require(r, "missive_author_world", route=outbound_route, counterpart=counterpart),
            "missive_addressee_world": _require(r, "missive_addressee_world", route=outbound_route, counterpart=counterpart),
            "missive_thread": _require(r, "missive_thread", route=outbound_route, counterpart=counterpart),
            "missive_seq": _require(r, "missive_seq", route=outbound_route, counterpart=counterpart),
            "missive_act": _require(r, "missive_act", route=outbound_route, counterpart=counterpart),
            "missive_provenance": _require(r, "missive_provenance", route=outbound_route, counterpart=counterpart),
        }
        if r.get("missive_responds_to") is not None:
            payload["missive_responds_to"] = r["missive_responds_to"]
        if r.get("missive_cites") is not None:
            payload["missive_cites"] = r["missive_cites"]
        exit_code, verdict = bcc.post_write(f"{self_base}/d/{self_name}", "ledger", payload)
        if exit_code == 0:
            recorded.append(verdict["row_id"])
        else:
            msg = verdict.get("message") or ""
            if "already exists" in msg and "exactly-once RECORDING" in msg:
                dedup_raced += 1
            else:
                errors.append(
                    f"missive (thread={r['missive_thread']!r} seq={r['missive_seq']}) refused "
                    f"NOT as a dedup race: {msg}")

    return {
        "pulled": len(outbound), "new": len(candidates),
        "recorded": recorded, "dedup_raced": dedup_raced, "errors": errors,
    }'''
    if old not in text:
        raise RuntimeError("RED REPRO SETUP FAILED: batch-loss revert target text not found -- "
                            "courier's own body has changed shape; update this fixture.")
    with open(tmp_path, "w") as f:
        f.write(text.replace(old, new))


def batch_witness_loss_case(schema: str, kern: str, role: str) -> None:
    srv, port = _serve(_BatchLossHandler)
    try:
        _wait_up(port, "/d/mockworld/health")
        toml_path = "/tmp/mkf_courier_batch.toml"
        _write_toml(toml_path, f"http://127.0.0.1:{_SELF_PORT}", {"mockworld": f"http://127.0.0.1:{port}"})

        # RED: reverted copy -- row 1's kernel refusal must be reported NOWHERE.
        red_path = "/tmp/mkf_courier_batch_reverted.py"
        _reverted_courier_no_batch_report(red_path)
        red_env = dict(os.environ)
        red_env["PYTHONPATH"] = SERVING + os.pathsep + red_env.get("PYTHONPATH", "")
        cp = sh(["python3", red_path, "--courier-toml", toml_path], cwd=REPO, env=red_env)
        red_out = cp.stdout + cp.stderr
        print("  RED stdout+stderr:\n" + "\n".join(f"    {l}" for l in red_out.splitlines()))
        _check("RED: row 1's kernel-refusal (provenance shape) is reported NOWHERE",
               "missive_provenance_shape" not in red_out)
        _check("RED: row 2's _require failure IS reported (the only visible outcome)",
               "missive_act" in red_out)
        os.remove(red_path)

        # GREEN: the real, current courier -- row 1's outcome must survive the mid-batch raise.
        cp = _run_courier(COURIER, toml_path)
        green_out = cp.stdout + cp.stderr
        print("  GREEN stdout+stderr:\n" + "\n".join(f"    {l}" for l in green_out.splitlines()))
        _check("GREEN: row 1's kernel-refusal (provenance shape) IS reported",
               "missive_provenance_shape" in green_out)
        _check("GREEN: row 2's _require failure is ALSO reported",
               "missive_act" in green_out)
        _check("GREEN: exit code is 1 (config-error class, uniform)", cp.returncode == 1)
    finally:
        srv.shutdown()


def exit_code_aggregation_cases(schema: str, kern: str, role: str) -> None:
    skew_srv, skew_port = _serve(_SkewHandler)
    refusal_srv, refusal_port = _serve(_make_refusal_handler("refusalworld"))
    refusal2_srv, refusal2_port = _serve(_make_refusal_handler("refusalworld2"))
    mock_srv, mock_port = _serve(_BatchLossHandler)
    dead_port = 1  # nothing listens on port 1 as an unprivileged user -- BoundaryUnreachable.
    try:
        _wait_up(skew_port, "/d/skewworld/health")
        _wait_up(refusal_port, "/d/refusalworld/health")
        _wait_up(refusal2_port, "/d/refusalworld2/health")
        _wait_up(mock_port, "/d/mockworld/health")

        # Scenario A: uniform class 4 (version mismatch + unreachable) -> exit 4.
        toml_a = "/tmp/mkf_courier_A.toml"
        _write_toml(toml_a, f"http://127.0.0.1:{_SELF_PORT}",
                    {"skewworld": f"http://127.0.0.1:{skew_port}",
                     "deadworld": f"http://127.0.0.1:{dead_port}"})
        cp = _run_courier(COURIER, toml_a)
        print(f"  scenario A (uniform class 4): exit={cp.returncode}")
        print("    " + (cp.stdout + cp.stderr).replace("\n", "\n    "))
        _check("scenario A: uniform boundary-unreachable/version-mismatch -> exit 4",
               cp.returncode == 4)

        # Scenario B: uniform class 3 (both counterparts BoundaryRefusal) -> exit 3.
        toml_b = "/tmp/mkf_courier_B.toml"
        _write_toml(toml_b, f"http://127.0.0.1:{_SELF_PORT}",
                    {"refusalworld": f"http://127.0.0.1:{refusal_port}",
                     "refusalworld2": f"http://127.0.0.1:{refusal2_port}"})
        cp = _run_courier(COURIER, toml_b)
        print(f"  scenario B (uniform class 3): exit={cp.returncode}")
        print("    " + (cp.stdout + cp.stderr).replace("\n", "\n    "))
        _check("scenario B: uniform boundary-refused -> exit 3", cp.returncode == 3)

        # Scenario C: mixed classes (4, 3, 1) -> exit 1 with an enumeration line.
        toml_c = "/tmp/mkf_courier_C.toml"
        _write_toml(toml_c, f"http://127.0.0.1:{_SELF_PORT}",
                    {"deadworld": f"http://127.0.0.1:{dead_port}",
                     "refusalworld": f"http://127.0.0.1:{refusal_port}",
                     "mockworld": f"http://127.0.0.1:{mock_port}"})
        cp = _run_courier(COURIER, toml_c)
        out = cp.stdout + cp.stderr
        print(f"  scenario C (mixed): exit={cp.returncode}")
        print("    " + out.replace("\n", "\n    "))
        _check("scenario C: mixed classes -> exit 1", cp.returncode == 1)
        _check("scenario C: stderr enumerates all three classes seen",
               all(tag in out for tag in ("4 (", "3 (", "1 (")) and "MIXED" in out)
    finally:
        skew_srv.shutdown()
        refusal_srv.shutdown()
        refusal2_srv.shutdown()
        mock_srv.shutdown()


_SELF_PORT = 0


def main() -> int:
    global _SELF_PORT
    suffix = "mkfcourier"
    schema, kern, role = f"{suffix}_scratch", f"{suffix}_scratch_kernel", f"{suffix}_scratch_rw"
    teardown(schema, kern, role)
    boundary_proc = None
    try:
        apply_chain(schema, kern, role)
        birth(schema, kern, role, "selfworld")

        toml_path = "/tmp/mkf_courier_multiplex.toml"
        with open(toml_path, "w") as f:
            f.write(f"""[deployments.selfworld]
pghost = "{PGHOST}"
pgdatabase = "{PGDB}"
pguser = "{role}"
pgschema = "{schema}"
pgkern = "{kern}"
""")
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        _SELF_PORT = s.getsockname()[1]
        s.close()
        boundary_proc = subprocess.Popen(
            ["python3", "boundary_service.py", "--config", toml_path,
             "--port", str(_SELF_PORT)],
            cwd=SERVING, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        _wait_up(_SELF_PORT, f"/d/selfworld/health")

        print("### batch-witness-loss (moderate-silent)")
        batch_witness_loss_case(schema, kern, role)
        print("\n### exit-code aggregation (moderate-loud)")
        exit_code_aggregation_cases(schema, kern, role)
    finally:
        if boundary_proc is not None:
            boundary_proc.terminate()
            boundary_proc.wait(timeout=10)
        teardown(schema, kern, role)

    if FAILURES:
        print(f"\ncourier_witness_fixtures: {len(FAILURES)} FAILURE(S): {FAILURES}")
        return 1
    print("\ncourier_witness_fixtures: all cases behaved as expected. ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
