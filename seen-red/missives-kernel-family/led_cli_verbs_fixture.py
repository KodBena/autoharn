#!/usr/bin/env python3
"""Seen-red specimen for work item led-missive-verbs-gap (autoharn3 rows 118/119): `led missive
list` and `led missive dispose <receipt-row-id> <disposition> [statement...]`
(bootstrap/templates/led.tmpl, the shared home `libexec/autoharn/led`'s own served shim execs
unchanged -- see that file's own header). CLI-SURFACE witness (the family's existing
run_fixtures.py/concurrent_race_fixtures.py/amendment2_transport_fixture.py cases all exercise
`kernel.missive_dispose`/the missive views directly via psql; NONE drove the CLI an operator
actually types) -- the same real-infra discipline `seen-red/boundary-cli-rebase/run_fixtures.py`
established for the rebased `led` CLI in general, applied here to the missive verb family
specifically: a REAL scratch schema (this family's own CHAIN, through s59), a REAL
`serving.boundary_service` subprocess, and `bootstrap/templates/led.tmpl` run as an actual
subprocess (never imported and called in-process).

RED (both polarities, live):
  1. `led missive dispose <receipt> <bad-word>` -- the closed vocabulary
     (consumed/declined/superseded-unread/escalated) is NOT re-validated client-side (ADR-0012
     P1); a bad word reaches `missive_disposition_check` and refuses, taught, exit 1.
  2. `led missive dispose <nonexistent-row-id> consumed` -- refused with the kernel's OWN text
     ("no in-force missive_received row exists with that id"), exit 1.

GREEN:
  3. `led missive list` on a seeded, undisposed `missive_received` row shows it (receipt id,
     author world, thread, seq, act, truncated statement).
  4. `led missive dispose <receipt> consumed "<statement>"` accepts (exit 0); BOTH rows land --
     the `missive_disposed` row (verified directly against the scratch schema) AND the
     acknowledgment `missive_sent` row (`missive_outbound`, act=acknowledgment,
     disposition=consumed) -- the two-row ceremony design/FABLE-MISSIVES-KERNEL-SPEC.md §2.7
     describes, never reimplemented here, only observed.
  5. `led missive list` afterward is empty, and says so plainly.

Zero residue: schema/kernel-schema/role dropped in `finally`, whichever branch exits.

Usage: python3 seen-red/missives-kernel-family/led_cli_verbs_fixture.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned (CLAUDE.md, 2026-07-02)."""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own environment
# before any subprocess is spawned -- inherited by the whole process tree this fixture starts.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

PGHOST = os.environ.get("HARNESS_PGHOST") or os.environ.get("EPISTEMIC_PGHOST") or "192.168.122.1"
PGDB = os.environ.get("HARNESS_PGDB", "toy")
REPO = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LINEAGE = REPO / "kernel" / "lineage"
SERVING = REPO / "serving"
LED_TMPL = REPO / "bootstrap" / "templates" / "led.tmpl"

sys.path.insert(0, str(REPO / "filing"))
sys.path.insert(0, str(SERVING))
import deployment_record  # noqa: E402

# Same chain this family's own run_fixtures.py uses (through s59-missive-views.sql) -- copied,
# not imported, matching this directory's own established per-file convention (each fixture
# module here is independently runnable; see courier_witness_fixtures.py/
# concurrent_race_fixtures.py, which each carry their own copy too).
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


def _check(label: str, cond: bool, detail: str = "") -> None:
    print(f"  [{'ok' if cond else 'FAIL'}] {label}" + (f" -- {detail}" if detail and not cond else ""))
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
        args += ["-f", str(LINEAGE / f)]
    cp = sh(args)
    if cp.returncode != 0:
        raise RuntimeError(f"chain apply FAILED:\n{cp.stdout[-2000:]}\n{cp.stderr[-2000:]}")


def birth(schema: str, kern: str, role: str, wname: str) -> None:
    genesis = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
        f"INSERT INTO {kern}.chain_genesis (seed) VALUES ('{genesis}') "
        f"ON CONFLICT (only_one) DO NOTHING;"])
    login_role = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAc", "SELECT session_user;"]).stdout.strip()

    def do(body: str) -> subprocess.CompletedProcess:
        script = f"SET ROLE {role};\nSET search_path = {schema}, {kern};\n{body}"
        return sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1"], input=script)

    do(f"""
DO $bw$
DECLARE v {kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {kern}.ledger_write(jsonb_build_object(
    'kind', 'principal_registered', 'statement', 'author self-attributed',
    'actor', (SELECT id FROM principal WHERE name = 'author'),
    'principal_subject', (SELECT id FROM principal WHERE name = 'author'),
    'principal_purpose', 'seen-red led-cli fixture'));
  IF v.disposition <> 'accepted' THEN RAISE EXCEPTION 'refused: %', v.message; END IF;
END $bw$;
""")
    for drole in (role, login_role):
        do(f"""
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
        do(f"""
SELECT set_config('birth.pname', '{pname}', false), set_config('birth.pclass', '{pclass}', false);
DO $bw$
DECLARE v {kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {kern}.registration_write(jsonb_build_object(
    'name', current_setting('birth.pname'), 'agent_class', current_setting('birth.pclass'),
    'purpose', 'seen-red led-cli fixture', 'statement', 'registered',
    'actor', (SELECT id FROM principal WHERE name = 'author')));
  IF v.disposition <> 'accepted' THEN RAISE EXCEPTION 'refused: %', v.message; END IF;
END $bw$;
""")
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
        f"INSERT INTO {kern}.world_identity (world_name) VALUES ('{wname}') "
        f"ON CONFLICT (one_row) DO NOTHING;"])


def dowrite(schema: str, kern: str, role: str, sql: str) -> str:
    script = f"SET ROLE {role};\nSET search_path = {schema}, {kern};\n{sql}"
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=0"], input=script)
    return cp.stdout + cp.stderr


def doquery(schema: str, kern: str, role: str, sql: str) -> str:
    script = f"SET ROLE {role};\nSET search_path = {schema}, {kern};\n{sql}"
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1"], input=script)
    return cp.stdout.strip()


def _wait_up(port: int, path: str) -> None:
    for _ in range(100):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=0.2)
            return
        except Exception:
            time.sleep(0.05)
    raise RuntimeError(f"boundary service on port {port} never came up")


def run_led(args: list[str], deployment: Path) -> subprocess.CompletedProcess[str]:
    """`bootstrap/templates/led.tmpl` run as an actual subprocess against the served boundary
    this fixture spawns -- the shared home (ADR-0012 P1) `libexec/autoharn/led` execs unchanged
    (see that file's own header); driving the template directly is byte-equivalent CLI coverage
    without a second bash-shim hop."""
    env = dict(os.environ)
    env["AUTOHARN"] = str(REPO)
    env["PICKUP_DEPLOYMENT"] = str(deployment)
    return subprocess.run(["python3", str(LED_TMPL), *args], capture_output=True, text=True,
                           env=env, cwd=REPO, timeout=30)


def main() -> int:
    suffix = "mkfledcli"
    world = "seenredworldcli"
    schema, kern, role = f"{suffix}_scratch", f"{suffix}_scratch_kernel", f"{suffix}_scratch_rw"
    teardown(schema, kern, role)
    boundary_proc = None
    tmp_files: list[Path] = []
    try:
        apply_chain(schema, kern, role)
        birth(schema, kern, role, world)

        # Seed one undisposed missive_received row directly (the family's own convention, see
        # run_fixtures.py's "LIFECYCLE receive" step) -- a courier-actored write, real shape
        # (missive_provenance's own regex, s58: 'xrow:<world>:<id>:<64-hex>'), no real peer
        # schema needed (provenance existence is never checked at write time, only its SHAPE).
        fake_hash = "a" * 64
        out = dowrite(schema, kern, role, f"""
DO $$
DECLARE v {kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {kern}.ledger_write(jsonb_build_object(
    'kind','missive_received','statement','led-cli witness: please look at this',
    'actor',(SELECT id FROM principal WHERE name='courier'),
    'missive_protocol',1,'missive_author_world','peerworld',
    'missive_addressee_world','{world}',
    'missive_thread','{world}/clitest','missive_seq',1,'missive_act','assertion',
    'missive_provenance','xrow:peerworld:1:{fake_hash}'));
  RAISE NOTICE 'SEED: % / row=%', v.disposition, v.row_id;
END $$;
""")
        _check("seed: missive_received accepted", "SEED: accepted" in out, out)

        receipt_id = doquery(schema, kern, role,
            f"SELECT id FROM ledger_current WHERE kind='missive_received' "
            f"AND missive_thread='{world}/clitest' AND missive_seq=1;")
        _check("seed: receipt row id resolved", receipt_id.isdigit(), receipt_id)

        # Real serving.boundary_service subprocess, scratch port.
        toml_path = Path(f"/tmp/{suffix}_multiplex.toml")
        tmp_files.append(toml_path)
        toml_path.write_text(f"""[deployments.{world}]
pghost = "{PGHOST}"
pgdatabase = "{PGDB}"
pguser = "{role}"
pgschema = "{schema}"
pgkern = "{kern}"
""")
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        boundary_proc = subprocess.Popen(
            ["python3", "boundary_service.py", "--config", str(toml_path), "--port", str(port)],
            cwd=SERVING, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        _wait_up(port, f"/d/{world}/health")

        dep_path = Path(f"/tmp/{suffix}_deployment.json")
        tmp_files.append(dep_path)
        rec = deployment_record.DeploymentRecord(
            db=PGDB, host=PGHOST, schema=schema, kern=kern, role=role, name=world,
            boundary_url=f"http://127.0.0.1:{port}", boundary_deployment=world)
        deployment_record.write_deployment(dep_path, rec)

        # GREEN 1: `led missive list` shows the seeded, undisposed missive.
        print("== led missive list (seeded) ==")
        cp = run_led(["missive", "list"], dep_path)
        _check("list: exit 0", cp.returncode == 0, f"exit={cp.returncode} stderr={cp.stderr!r}")
        _check("list: shows the receipt id", f"[{receipt_id}]" in cp.stdout, cp.stdout)
        _check("list: shows author world", "from=peerworld" in cp.stdout, cp.stdout)
        _check("list: shows thread", f"thread={world}/clitest" in cp.stdout, cp.stdout)
        _check("list: shows seq", "seq=1" in cp.stdout, cp.stdout)
        _check("list: shows act", "act=assertion" in cp.stdout, cp.stdout)
        _check("list: shows (truncated) statement",
               "statement: led-cli witness: please look at this" in cp.stdout, cp.stdout)

        # RED 1: a bad disposition vocabulary word -- refused, taught, exit 1. NOT re-validated
        # client-side (ADR-0012 P1) -- the kernel's own missive_disposition_check CHECK refuses.
        print("== led missive dispose <receipt> bogus-word (RED: bad vocabulary) ==")
        cp = run_led(["missive", "dispose", receipt_id, "bogus-word"], dep_path)
        _check("bad-vocab: exit 1", cp.returncode == 1, f"exit={cp.returncode} stderr={cp.stderr!r}")
        _check("bad-vocab: REFUSED by the kernel write boundary teach-text",
               "REFUSED by the kernel write boundary" in cp.stderr, cp.stderr)
        _check("bad-vocab: names the kernel's own missive_disposition_check constraint",
               "missive_disposition_check" in cp.stderr, cp.stderr)
        _check("bad-vocab: SQLSTATE surfaced", "SQLSTATE" in cp.stderr, cp.stderr)

        # RED 2: a bad row id -- refused with the kernel's own text, exit 1.
        print("== led missive dispose 999999999 consumed (RED: bad row id) ==")
        cp = run_led(["missive", "dispose", "999999999", "consumed"], dep_path)
        _check("bad-row-id: exit 1", cp.returncode == 1, f"exit={cp.returncode} stderr={cp.stderr!r}")
        _check("bad-row-id: kernel's own no-in-force-row text",
               "no in-force missive_received row exists with that id" in cp.stderr, cp.stderr)

        # GREEN 2: a valid dispose lands BOTH rows -- the disposition AND the acknowledgment.
        print("== led missive dispose <receipt> consumed \"...\" (GREEN: valid) ==")
        cp = run_led(["missive", "dispose", receipt_id, "consumed", "closing", "the", "loop"],
                     dep_path)
        _check("dispose: exit 0", cp.returncode == 0, f"exit={cp.returncode} stderr={cp.stderr!r}")
        _check("dispose: row-written confirmation", "written" in cp.stdout, cp.stdout)

        disp_count = doquery(schema, kern, role,
            f"SELECT count(*) FROM ledger_current WHERE kind='missive_disposed' "
            f"AND missive_regards={receipt_id} AND missive_disposition='consumed';")
        _check("dispose: missive_disposed row landed (witnessed against the scratch schema)",
               disp_count == "1", disp_count)

        ack_count = doquery(schema, kern, role,
            f"SELECT count(*) FROM missive_outbound WHERE missive_thread='{world}/clitest' "
            f"AND missive_act='acknowledgment' AND missive_disposition='consumed';")
        _check("dispose: acknowledgment missive_sent row landed on missive_outbound "
               "(witnessed against the scratch schema)", ack_count == "1", ack_count)

        # list is empty afterward, and says so plainly.
        print("== led missive list (after dispose) ==")
        cp = run_led(["missive", "list"], dep_path)
        _check("list-after: exit 0", cp.returncode == 0, f"exit={cp.returncode} stderr={cp.stderr!r}")
        _check("list-after: empty, plainly stated",
               cp.stdout.strip() == "led missive list: no undisposed missives.", cp.stdout)
    finally:
        if boundary_proc is not None:
            boundary_proc.terminate()
            try:
                boundary_proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                boundary_proc.kill()
                boundary_proc.wait(timeout=10)
        teardown(schema, kern, role)
        for p in tmp_files:
            p.unlink(missing_ok=True)

    if FAILURES:
        print(f"\nled_cli_verbs_fixture: {len(FAILURES)} FAILURE(S): {FAILURES}")
        return 1
    print("\nled_cli_verbs_fixture: all cases behaved as expected. ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
