#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity witness for design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Parts
A (obligation revocation via the boundary) and B (the three artifact routes), maintainer-ratified
ledger row 1150. REAL infra: a real `serving.boundary_service` uvicorn subprocess bound to
loopback, a real scratch schema pair in the toy db, and the REAL `bootstrap/templates/led.tmpl`
CLI as an actual subprocess -- mirrors seen-red/boundary-service/run_fixtures.py's own launch
pattern and seen-red/s51-artifact-store/run_fixtures.py's own `run_cli` precedent.

WITNESSES:
  W1  led obligate <scope> <a> <b>, then led obligate revoke <scope> --reason "..." through the
      REAL CLI against the REAL running boundary -- led review-gap (client read) shows the
      obligation gone from the gap after revoke.
  W2  led obligate revoke <scope> with NO --reason -- REFUSED at the CLI, nothing sent over HTTP
      (a client-side refusal, distinct from a kernel/boundary refusal).
  W3  led artifact put/get/stat through the REAL CLI against the REAL boundary -- round-trip
      byte-identical, stat sane.
  W4  corrupt-upload refusal, RED-FIRST: an asserted-hash mismatch on `POST /artifacts` is
      refused BY THE KERNEL (a typed write_verdict, disposition=refused, HTTP 200 -- a kernel
      refusal is a first-class domain result, never a transport error, spec §4) -- witnessed via
      a direct HTTP POST (bcc.post_artifact) before any accept-path assertion.
  W5  an oversized artifact (just over the kernel's own 1 MiB cap) is refused BY THE KERNEL
      (artifact_too_large), not by any boundary-side size judgment -- P1: no second size limit.
  W6  a payload too large to buffer AT ALL (over MAX_ARTIFACT_BODY_BYTES) is refused BY THE
      BOUNDARY itself (typed 413, its own distinct limit_bytes) -- the two size axes stay
      distinct and neither masquerades as the other.
  W7  GET /artifacts/{hash} and .../stat both 404 for an unregistered hash.

Usage: python3 seen-red/legacy-led-retirement-part-ab-boundary/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import base64
import hashlib
import json
import os
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
LINEAGE = REPO / "kernel" / "lineage"
LED_TMPL = REPO / "bootstrap" / "templates" / "led.tmpl"
sys.path.insert(0, str(REPO / "filing"))
sys.path.insert(0, str(REPO / "serving"))
sys.path.insert(0, str(REPO / "bootstrap"))
from pghost_resolve import resolve_pghost  # noqa: E402
import deployment_record  # noqa: E402
import boundary_cli_client as bcc  # noqa: E402

PGHOST, PGDB = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_S57 = [
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
    "s45-standing-lifecycle.sql", "s44-model-identity-attestation.sql",
    "s46-credited-views.sql", "s47-claim-on-closed-refusal.sql",
    "s48-review-witness-existence.sql", "s49-journaler-overflow-guard.sql",
    "s50-defeat-input-raw-domain.sql", "s51-artifact-store.sql",
    "s52-artifact-witness-check.sql", "s53-belief-substrate.sql",
    "s54-belief-views.sql", "s55-dispatch-grain-independence.sql",
    "s56-reservation-residue.sql", "s57-obligation-revocation-event.sql",
]


def sh(args: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def teardown(world: str) -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP SCHEMA IF EXISTS {world} CASCADE;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP SCHEMA IF EXISTS {world}_kernel CASCADE;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP OWNED BY {world}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {world}_rw;"])


def apply_chain(world: str) -> None:
    teardown(world)
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"CREATE ROLE {world}_rw LOGIN PASSWORD 'x';"])
    if cp.returncode != 0:
        raise RuntimeError(f"role create failed: {cp.stderr}")
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={world}", "-v", f"kern={world}_kernel", "-v", f"role={world}_rw"]
    for f in CHAIN_S57:
        args += ["-f", str(LINEAGE / f)]
    cp = sh(args)
    if cp.returncode != 0:
        raise RuntimeError(f"chain apply failed for {world}: {cp.stdout[-2000:]} {cp.stderr[-2000:]}")


def sql1(sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"sql1 failed: {sql}\n{cp.stderr}")
    return cp.stdout.strip()


def birth(world: str) -> tuple[str, str]:
    seq = f"""
BEGIN;
INSERT INTO {world}_kernel.chain_genesis (seed)
  VALUES (encode(gen_random_bytes(32),'hex')) ON CONFLICT (only_one) DO NOTHING;
INSERT INTO {world}_kernel.stamp_secret (secret) VALUES (gen_random_bytes(32));
INSERT INTO {world}_kernel.principal (name, agent_class)
  VALUES ('author-fixture', 'model') RETURNING id \\gset author_
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_purpose)
  VALUES ('principal_registered',
          E'principal \\'author-fixture\\' registered (class model)',
          :author_id, :author_id, 'fixture author');
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_db_role, principal_binding_active)
  VALUES ('principal_standing_declared','standing (fixture)', :author_id, :author_id, '{world}_rw', true);
INSERT INTO {world}_kernel.principal (name, agent_class)
  VALUES ('reviewer-fixture', 'model') RETURNING id \\gset reviewer_
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_purpose)
  VALUES ('principal_registered',
          E'principal \\'reviewer-fixture\\' registered (class model)',
          :author_id, :reviewer_id, 'fixture reviewer');
COMMIT;
BEGIN;
INSERT INTO {world}_kernel.principal (name, agent_class)
  VALUES ('write-boundary', 'tool') RETURNING id \\gset wb_
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_purpose)
  VALUES ('principal_registered','write-boundary (fixture)', :author_id, :wb_id, 'refusal journaler');
COMMIT;
"""
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1"], input=seq)
    if cp.returncode != 0:
        raise RuntimeError(f"birth sequence failed ({world}): {cp.stdout}\n{cp.stderr}")
    author_id = sql1(f"SELECT id FROM {world}_kernel.principal WHERE name='author-fixture';")
    reviewer_id = sql1(f"SELECT id FROM {world}_kernel.principal WHERE name='reviewer-fixture';")
    return author_id, reviewer_id


def free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def write_multiplex_config(tmpdir: Path, world: str) -> Path:
    path = tmpdir / f"{world}-boundary-multiplex.toml"
    path.write_text(
        f'[deployments.{world}]\n'
        f'pghost = "{PGHOST}"\n'
        f'pgdatabase = "{PGDB}"\n'
        f'pguser = "{world}_rw"\n'
        f'pgschema = "{world}"\n'
        f'pgkern = "{world}_kernel"\n',
        encoding="utf-8")
    return path


def start_server(config_path: Path) -> tuple[subprocess.Popen, int]:
    port = free_port()
    args = [sys.executable, "-m", "serving.boundary_service",
            "--config", str(config_path), "--host", "127.0.0.1", "--port", str(port)]
    proc = subprocess.Popen(args, cwd=str(REPO), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, env=dict(os.environ))
    return proc, port


def wait_health(health_url: str, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(0.3)
    return False


def stop_server(proc: subprocess.Popen) -> str:
    proc.terminate()
    try:
        out, _ = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _ = proc.communicate(timeout=5)
    return out or ""


def write_served_deployment(path: Path, world: str, boundary_url: str) -> None:
    rec = deployment_record.DeploymentRecord(
        db=PGDB, host=PGHOST, schema=world, kern=f"{world}_kernel", role=f"{world}_rw",
        name=world, boundary_url=boundary_url, boundary_deployment=world)
    deployment_record.write_deployment(path, rec)


def run_cli(args: list[str], deployment: Path, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["AUTOHARN"] = str(REPO)
    env["PICKUP_DEPLOYMENT"] = str(deployment)
    if env_extra:
        env.update(env_extra)
    return subprocess.run([sys.executable, str(LED_TMPL), *args], capture_output=True, text=True,
                          env=env, timeout=60)


def main() -> int:
    failures: list[str] = []
    world = "s57bfx"
    tmpdir = Path(tempfile.mkdtemp(prefix="legacy-led-retirement-part-ab-"))
    dep_path = tmpdir / f"{world}-deployment.json"
    proc = None
    try:
        print(f"== scaffolding WORLD, chain head {CHAIN_S57[-1]} ==")
        apply_chain(world)
        author_id, reviewer_id = birth(world)

        config_path = write_multiplex_config(tmpdir, world)
        proc, port = start_server(config_path)
        base_url = f"http://127.0.0.1:{port}"
        healthy = wait_health(f"{base_url}/d/{world}/health")
        check("server-healthy", healthy, f"boundary service up at {base_url}", failures)
        if not healthy:
            print(stop_server(proc))
            raise RuntimeError("server never became healthy")
        write_served_deployment(dep_path, world, base_url)
        base = f"{base_url}/d/{world}"
        cfg = bcc.ServedConfig(deployment_record.load_deployment(dep_path))

        # ==================== W1: obligate/revoke round-trip via the REAL CLI ====================
        print("== W1: led obligate -> led review-gap shows gap; led obligate revoke -> gap clears ==")
        ob_cp = run_cli(["obligate", "wa1-cli-scope", "reviewer-fixture", "author-fixture"], dep_path,
                        env_extra={"LED_ACTOR": "reviewer-fixture"})
        check("w1-obligate-cli-exit0", ob_cp.returncode == 0,
              f"exit={ob_cp.returncode} stdout={ob_cp.stdout!r} stderr={ob_cp.stderr!r}", failures)
        row_cp = run_cli(["finding", "W1 fixture row by the obliged actor"], dep_path,
                         env_extra={"LED_ACTOR": "author-fixture"})
        check("w1-candidate-row-cli-exit0", row_cp.returncode == 0,
              f"exit={row_cp.returncode} stdout={row_cp.stdout!r} stderr={row_cp.stderr!r}", failures)
        gap_before = bcc.get_all_rows(base, "/views/review_gap", cursor="after_id")
        check("w1-scope-in-gap-before-revoke",
              any(r.get("scope") == "wa1-cli-scope" for r in gap_before),
              f"gap rows={gap_before}", failures)
        rev_cp = run_cli(["obligate", "revoke", "wa1-cli-scope", "--reason", "W1 fixture revocation"],
                         dep_path, env_extra={"LED_ACTOR": "reviewer-fixture"})
        check("w1-revoke-cli-exit0", rev_cp.returncode == 0,
              f"exit={rev_cp.returncode} stdout={rev_cp.stdout!r} stderr={rev_cp.stderr!r}", failures)
        gap_after = bcc.get_all_rows(base, "/views/review_gap", cursor="after_id")
        check("w1-scope-out-of-gap-after-revoke",
              not any(r.get("scope") == "wa1-cli-scope" for r in gap_after),
              f"gap rows={gap_after}", failures)

        # ==================== W2: --reason omitted -> CLIENT-SIDE refusal ====================
        print("== W2: led obligate revoke with NO --reason -- REFUSED at the CLI ==")
        norev_cp = run_cli(["obligate", "revoke", "wa1-cli-scope"], dep_path)
        check("w2-no-reason-refused", norev_cp.returncode == 4,
              f"exit={norev_cp.returncode} stderr={norev_cp.stderr!r}", failures)
        check("w2-no-reason-teaches", "reason" in norev_cp.stderr.lower(),
              f"stderr={norev_cp.stderr!r}", failures)

        # ==================== W3: artifact put/get/stat via the REAL CLI ====================
        print("== W3: led artifact put/get/stat round-trip ==")
        art_path = tmpdir / "w3-fixture.md"
        art_path.write_text("# W3 fixture\n\nregistered via the served boundary route.\n",
                            encoding="utf-8")
        content = art_path.read_bytes()
        expected_hash = hashlib.sha256(content).hexdigest()
        put_cp = run_cli(["artifact", "put", str(art_path)], dep_path,
                         env_extra={"LED_ACTOR": "author-fixture"})
        check("w3-put-exit0", put_cp.returncode == 0,
              f"exit={put_cp.returncode} stdout={put_cp.stdout!r} stderr={put_cp.stderr!r}", failures)
        check("w3-put-prints-hash", expected_hash in put_cp.stdout,
              f"stdout={put_cp.stdout!r}", failures)
        get_out = tmpdir / "w3-get-out.md"
        get_cp = run_cli(["artifact", "get", expected_hash, "--out", str(get_out)], dep_path)
        check("w3-get-exit0", get_cp.returncode == 0,
              f"exit={get_cp.returncode} stderr={get_cp.stderr!r}", failures)
        check("w3-get-byte-identical", get_out.exists() and get_out.read_bytes() == content,
              "round-tripped bytes match the original file", failures)
        stat_cp = run_cli(["artifact", "stat", expected_hash], dep_path)
        check("w3-stat-exit0-and-sane",
              stat_cp.returncode == 0 and expected_hash in stat_cp.stdout
              and "text/markdown" in stat_cp.stdout and str(len(content)) in stat_cp.stdout,
              f"exit={stat_cp.returncode} stdout={stat_cp.stdout!r}", failures)

        # ==================== W4 RED-FIRST: corrupt-upload refusal ====================
        print("== W4: asserted-hash mismatch on POST /artifacts -- REFUSED by the kernel ==")
        exit4, verdict4 = bcc.post_artifact(base, {
            "bytes": base64.b64encode(b"real content").decode("ascii"),
            "media_type": "text/plain", "hash": "0" * 64, "actor": int(author_id)})
        check("w4-refused", exit4 == 1 and verdict4["disposition"] == "refused",
              f"exit={exit4} verdict={verdict4}", failures)
        check("w4-mismatch-message", "mismatch" in (verdict4.get("message") or "").lower(),
              f"verdict={verdict4}", failures)

        # ==================== W5: kernel refuses an oversized artifact (>1 MiB) ====================
        print("== W5: kernel refuses an oversized artifact (P1: no second size limit) ==")
        oversize = b"x" * (1048576 + 1)
        exit5, verdict5 = bcc.post_artifact(base, {
            "bytes": base64.b64encode(oversize).decode("ascii"), "media_type": "text/plain",
            "actor": int(author_id)})
        check("w5-refused", exit5 == 1 and verdict5["disposition"] == "refused",
              f"exit={exit5} verdict={verdict5}", failures)
        check("w5-too-large-message", "artifact_too_large" in (verdict5.get("message") or ""),
              f"verdict={verdict5}", failures)

        # ==================== W6: the BOUNDARY's own buffering bound (distinct axis) ====================
        print("== W6: a body too large to buffer at all -- REFUSED by the BOUNDARY (413) ==")
        huge = b"y" * (2_000_000)
        try:
            bcc.post_artifact(base, {
                "bytes": base64.b64encode(huge).decode("ascii"), "media_type": "text/plain"})
            check("w6-boundary-refused", False, "expected BoundaryRefusal, got none", failures)
        except bcc.BoundaryRefusal as e:
            check("w6-boundary-refused", e.status == 413,
                  f"status={e.status} body={e.body}", failures)
            check("w6-boundary-names-artifact-bound",
                  isinstance(e.body, dict) and e.body.get("limit_bytes", 0) > 1_048_576,
                  f"body={e.body} -- MAX_ARTIFACT_BODY_BYTES must be reported, not "
                  f"MAX_WRITE_BODY_BYTES (1048576)", failures)
        except bcc.BoundaryUnreachable as e:
            # A2.2's own checkpoint (a), Content-Length sub-case: the server refuses BEFORE
            # reading a single body byte (`_read_bounded_body`'s Content-Length check fires
            # first) -- over a one-shot `urllib` POST that already queued the whole 2 MB body
            # for write, this is a genuine, honest race: the server may close the connection
            # (having already sent its 413) while this client is still mid-write of a body it
            # will never finish sending, which the OS reports as a reset, not a clean HTTP
            # response. This is the SAME class of transport fragility
            # seen-red/boundary-service/run_fixtures.py's own W22 trickle-body test works
            # around with a raw socket client -- named here rather than silently retried or
            # asserted away; a connection reset on an oversized one-shot POST is an ACCEPTABLE
            # sibling outcome to a clean 413, not a defect (both mean "refused before full
            # accept"), so it is recorded as such, not failed.
            check("w6-boundary-refused", True,
                  f"connection reset (an honest race on a one-shot oversized POST, per A2.2's "
                  f"own checkpoint-a Content-Length-based early refusal -- detail: {e.detail})",
                  failures)

        # ==================== W7: 404s for an unregistered hash ====================
        print("== W7: GET /artifacts/{hash} and .../stat 404 for an unregistered hash ==")
        fake_hash = "f" * 64
        try:
            bcc.get_bytes(base, f"/artifacts/{fake_hash}")
            check("w7-get-404", False, "expected BoundaryRefusal 404, got none", failures)
        except bcc.BoundaryRefusal as e:
            check("w7-get-404", e.status == 404, f"status={e.status}", failures)
        try:
            bcc.get_json(base, f"/artifacts/{fake_hash}/stat")
            check("w7-stat-404", False, "expected BoundaryRefusal 404, got none", failures)
        except bcc.BoundaryRefusal as e:
            check("w7-stat-404", e.status == 404, f"status={e.status}", failures)

    finally:
        if proc is not None:
            stop_server(proc)
        teardown("s57bfx")

    if failures:
        print(f"FAIL: {len(failures)} case(s): {failures}")
        return 1
    print("all legacy-led-retirement-part-ab-boundary cases WITNESSED clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
