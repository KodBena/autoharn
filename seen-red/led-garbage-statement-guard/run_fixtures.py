#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity witness for the garbage-statement guard in
bootstrap/templates/led.tmpl's generic write path (ledger row 1159, maintainer testimony:
"fumbled agent invocations have WRITTEN CLI usage text into a ledger as permanent rows" --
class-ratified fail-safe additive-refusal lane, 2026-07-23 Part C completion).

WITNESSES:
  R1  RED-FIRST: a statement that is literally captured `--help`-shaped usage text is REFUSED,
      nothing written.
  R2  a statement containing a `usage:` line is REFUSED, nothing written.
  R3  a statement containing a run of 3+ option-flag-shaped tokens is REFUSED, nothing written.
  R4  the SAME statement, with --statement-really-contains-cli-text, WRITES successfully.
  R5  an ordinary statement (including one mentioning a single `--flag` in passing prose) is
      UNAFFECTED.
  R6  `led work open`'s own typed-field path does NOT run this guard (by design -- it never
      carries raw free text under this preflight) -- a title containing CLI-usage-shaped text
      still writes.

Real infra, no mocks: a real boundary_service subprocess + a real scratch schema pair in the
toy db, torn down before and after. Usage: python3 seen-red/led-garbage-statement-guard/
run_fixtures.py. Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

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
from pghost_resolve import resolve_pghost  # noqa: E402
import deployment_record  # noqa: E402

PGHOST, PGDB = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_S43 = [
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
    for f in CHAIN_S43:
        args += ["-f", str(LINEAGE / f)]
    cp = sh(args)
    if cp.returncode != 0:
        raise RuntimeError(f"chain apply failed for {world}: {cp.stdout[-2000:]} {cp.stderr[-2000:]}")


def sql1(sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"sql1 failed: {sql}\n{cp.stderr}")
    return cp.stdout.strip()


def birth(world: str) -> None:
    """s15's own 'author' anchor row is the pre-seeded principal every birth chain carries
    (kernel/lineage/high_watermark_1.sql) -- this fixture declares its standing and registers
    the write-boundary tool principal, mirroring every other fixture's own minimal shape."""
    seq = f"""
BEGIN;
INSERT INTO {world}_kernel.chain_genesis (seed)
  VALUES (encode(gen_random_bytes(32),'hex')) ON CONFLICT (only_one) DO NOTHING;
INSERT INTO {world}_kernel.stamp_secret (secret) VALUES (gen_random_bytes(32));
SELECT id AS author_id FROM {world}_kernel.principal WHERE name = 'author' \\gset
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_db_role)
  VALUES ('principal_standing_declared','standing (fixture)', :author_id, :author_id, '{world}_rw');
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
    env["LED_ACTOR"] = "author"
    if env_extra:
        env.update(env_extra)
    return subprocess.run([sys.executable, str(LED_TMPL), *args], capture_output=True, text=True,
                          env=env, timeout=60)


def main() -> int:
    failures: list[str] = []
    world = "gsgfx2"
    tmpdir = Path(tempfile.mkdtemp(prefix="led-garbage-statement-guard-"))
    dep_path = tmpdir / f"{world}-deployment.json"
    proc = None
    try:
        apply_chain(world)
        birth(world)
        config_path = write_multiplex_config(tmpdir, world)
        proc, port = start_server(config_path)
        base_url = f"http://127.0.0.1:{port}"
        healthy = wait_health(f"{base_url}/d/{world}/health")
        check("server-healthy", healthy, f"boundary service up at {base_url}", failures)
        if not healthy:
            print(stop_server(proc))
            raise RuntimeError("server never became healthy")
        write_served_deployment(dep_path, world, base_url)

        count_before = sql1(f"SET ROLE {world}_rw; SELECT count(*) FROM {world}.ledger;")

        # ==================== R1: RED-FIRST -- bare --help token ====================
        print("== R1: a bare --help token -- REFUSED, nothing written ==")
        r1 = run_cli(["finding", "usage: led [flags] <kind> <statement...> --help"], dep_path)
        check("r1-refused", r1.returncode == 1, f"exit={r1.returncode} stderr={r1.stderr!r}", failures)
        check("r1-names-row-1159", "1159" in r1.stderr, f"stderr={r1.stderr!r}", failures)
        check("r1-names-override-flag", "--statement-really-contains-cli-text" in r1.stderr,
              f"stderr={r1.stderr!r}", failures)
        count_after_r1 = sql1(f"SET ROLE {world}_rw; SELECT count(*) FROM {world}.ledger;")
        check("r1-nothing-written", count_after_r1 == count_before,
              f"before={count_before} after={count_after_r1}", failures)

        # ==================== R2: a usage: line ====================
        print("== R2: a 'usage:' line -- REFUSED, nothing written ==")
        r2 = run_cli(["finding", "usage: led work open <slug> <title...> [--parent p]"], dep_path)
        check("r2-refused", r2.returncode == 1, f"exit={r2.returncode} stderr={r2.stderr!r}", failures)
        count_after_r2 = sql1(f"SET ROLE {world}_rw; SELECT count(*) FROM {world}.ledger;")
        check("r2-nothing-written", count_after_r2 == count_before,
              f"before={count_before} after={count_after_r2}", failures)

        # ==================== R3: a run of 3+ option-flag tokens ====================
        print("== R3: a run of 3+ option-flag tokens -- REFUSED, nothing written ==")
        r3 = run_cli(["finding", "flag dump --supersedes --amends --answers --refs captured by accident"], dep_path)
        check("r3-refused", r3.returncode == 1, f"exit={r3.returncode} stderr={r3.stderr!r}", failures)
        count_after_r3 = sql1(f"SET ROLE {world}_rw; SELECT count(*) FROM {world}.ledger;")
        check("r3-nothing-written", count_after_r3 == count_before,
              f"before={count_before} after={count_after_r3}", failures)

        # ==================== R4: the override writes ====================
        print("== R4: --statement-really-contains-cli-text overrides -- WRITES ==")
        r4 = run_cli(["finding", "usage: led [flags] <kind> <statement...> --help",
                     "--statement-really-contains-cli-text"], dep_path)
        check("r4-accepted", r4.returncode == 0, f"exit={r4.returncode} stdout={r4.stdout!r} stderr={r4.stderr!r}", failures)
        count_after_r4 = sql1(f"SET ROLE {world}_rw; SELECT count(*) FROM {world}.ledger;")
        check("r4-one-row-written", int(count_after_r4) == int(count_before) + 1,
              f"before={count_before} after={count_after_r4}", failures)

        # ==================== R5: ordinary statements are UNAFFECTED ====================
        print("== R5: ordinary statements, including a single --flag mention, are UNAFFECTED ==")
        r5a = run_cli(["finding", "an ordinary finding about the guard witness, no CLI artifacts here"], dep_path)
        check("r5a-accepted", r5a.returncode == 0, f"exit={r5a.returncode} stderr={r5a.stderr!r}", failures)
        r5b = run_cli(["finding", "consider using --supersedes on the next revision to retract a row"], dep_path)
        check("r5b-accepted", r5b.returncode == 0, f"exit={r5b.returncode} stderr={r5b.stderr!r}", failures)

        # ==================== R6: led work open's typed-field path is UNAFFECTED ====================
        print("== R6: led work open's typed-field path does NOT run this guard (by design) ==")
        r6 = run_cli(["work", "open", "guard-witness-item",
                     "usage: --help --foo --bar --baz title text, unaffected on purpose"], dep_path)
        check("r6-accepted", r6.returncode == 0, f"exit={r6.returncode} stderr={r6.stderr!r}", failures)

    finally:
        if proc is not None:
            stop_server(proc)
        teardown("gsgfx2")

    if failures:
        print(f"FAIL: {len(failures)} case(s): {failures}")
        return 1
    print("all led-garbage-statement-guard cases WITNESSED clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
