#!/usr/bin/env python3
"""Seen-red specimen for work item courier-ack-disposition-drop (autoharn3 row 131,
design/FABLE-MISSIVES-KERNEL-SPEC.md §2.7 + §5): the FULL ack ROUND TRIP between two REAL
scratch worlds -- never a single-schema self-send, never a mocked counterpart. Every prior
courier fixture in this directory (`courier_witness_fixtures.py`) mocks the counterpart with a
stdlib `http.server` handler; the defect row 131 names lives entirely in what the counterpart's
OWN `missive_outbound` view serves and what the real courier forwards from it, so this leg spins
up TWO real `serving.boundary_service` instances, each fronting its own real scratch schema/
kernel pair through the family's own CHAIN (s58/s59), and drives the real `courier` binary
against both.

THE DEFECT (row 131, witnessed live 2026-07-28): `missive_disposition` rides ONLY on the
acknowledgment missive (spec §2.3 note ² -- one of exactly two licensed homes) and is MANDATORY
there (`missive_disposition_mandatory_on_ack`). Pre-fix, `libexec/autoharn/courier`'s payload
block forwarded `missive_responds_to`/`missive_cites` as optional envelope columns but omitted
`missive_disposition` -- so every ack crossing a real boundary arrived stripped, and the
addressee kernel correctly refused it. The live incident recorded 0 of 4 acks; this fixture
reproduces the SAME shape at the scale of one ack: 0 recorded pre-fix, 1 recorded post-fix.

SCENE: world A (`ackworlda`) sends a `request` missive addressed to world B (`ackworldb`). B's
courier pulls it (ordinary receive leg, already covered elsewhere -- exercised here only as the
necessary setup for what follows). B dispositions the receipt via `kernel.missive_dispose`,
which mints B's acknowledgment `missive_sent` row carrying `missive_disposition` (§2.7 step 3).
A's courier then pulls B's outbound feed, which now contains that acknowledgment.

RED: A's courier AS COMMITTED AT 0429c6c (the fix's own pre-fix parent, `git show
0429c6c:libexec/autoharn/courier` -- byte-identical, never hand-reconstructed) pulls the
acknowledgment and POSTs it stripped of `missive_disposition`; the real kernel refuses on
`missive_disposition_mandatory_on_ack`; A's `missive_receipts` view stays at zero rows for this
ack -- the live specimen's own shape, scaled down from 4.

GREEN: A's courier AS COMMITTED IN THIS TREE (real `libexec/autoharn/courier`, no throwaway
copy) re-pulls the SAME still-unrecorded ack (idempotent retry, exactly what an operator would
do) and records it: (a) the pull's own report shows one new/one recorded, not zero; (b) the
recorded `missive_received` row on A's OWN scratch schema (queried directly, never taken on
courier's say-so) carries `missive_disposition` intact, matching what B actually dispositioned
it as.

Both boundary_service instances are real subprocesses on scratch loopback ports (never
8433/8422); both schema/kernel-schema/role pairs are dropped in `finally`, whichever branch
exits -- zero residue.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own environment
# before any subprocess is spawned -- inherited by the whole process tree this fixture starts.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

PGHOST = os.environ.get("HARNESS_PGHOST") or os.environ.get("EPISTEMIC_PGHOST") or "192.168.122.1"
PGDB = os.environ.get("HARNESS_PGDB", "toy")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LINEAGE = os.path.join(REPO, "kernel", "lineage")
COURIER = os.path.join(REPO, "libexec", "autoharn", "courier")
SERVING = os.path.join(REPO, "serving")
FILING = os.path.join(REPO, "filing")

PRE_FIX_REV = "0429c6c"  # the fix commit 86cb5c4's own parent -- named in row 131's own item.

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
        args += ["-f", os.path.join(LINEAGE, f)]
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
    'principal_purpose', 'ack-crossing fixture'));
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
    'purpose', 'ack-crossing fixture', 'statement', 'registered',
    'actor', (SELECT id FROM principal WHERE name = 'author')));
  IF v.disposition <> 'accepted' THEN RAISE EXCEPTION '% registration refused: %', current_setting('birth.pname'), v.message; END IF;
END $bw$;
""")
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
        f"INSERT INTO {kern}.world_identity (world_name) VALUES ('{wname}') "
        f"ON CONFLICT (one_row) DO NOTHING;"])


def dowrite(schema: str, kern: str, role: str, sql: str) -> str:
    """Returns stdout+stderr combined -- psql's RAISE NOTICE output goes to stderr."""
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


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _start_boundary(schema: str, kern: str, role: str, world: str, toml_path: str,
                     port: int) -> subprocess.Popen:
    with open(toml_path, "w") as f:
        f.write(f"""[deployments.{world}]
pghost = "{PGHOST}"
pgdatabase = "{PGDB}"
pguser = "{role}"
pgschema = "{schema}"
pgkern = "{kern}"
""")
    proc = subprocess.Popen(
        ["python3", "boundary_service.py", "--config", toml_path, "--port", str(port)],
        cwd=SERVING, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    _wait_up(port, f"/d/{world}/health")
    return proc


def _write_courier_toml(path: str, self_world: str, self_base: str,
                         counterpart_world: str, counterpart_base: str) -> None:
    with open(path, "w") as f:
        f.write(f"""[courier]
authn = "single-operator"
self = "{self_world}"
self_base = "{self_base}"

[courier.counterparts]
{counterpart_world} = "{counterpart_base}"
""")


def _run_courier(courier_path: str, toml_path: str, *, extra_pythonpath: str | None = None
                  ) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["AUTOHARN_FIXTURE_SANDBOX_WAIVER"] = (
        "ack_crossing_fixture.py: courier-toml points only at scratch 127.0.0.1 boundary_service "
        "instances this same fixture spawns and tears down, never the real deployment.json")
    if extra_pythonpath:
        env["PYTHONPATH"] = extra_pythonpath + os.pathsep + env.get("PYTHONPATH", "")
    return sh(["python3", courier_path, "--courier-toml", toml_path], env=env, cwd=REPO)


def _pre_fix_courier_copy(tmp_path: str) -> None:
    """`libexec/autoharn/courier` BYTE-IDENTICAL to commit 0429c6c (fetched via `git show`,
    never hand-reconstructed) -- the fix commit 86cb5c4's own parent, named verbatim in row
    131's own item and this build's brief. Missing the two-line `missive_disposition` forward
    added by 86cb5c4; every other line is the current, already-rebased-into-libexec shape (the
    rebase, commit 167aedb, landed BEFORE 0429c6c). Never committed to this checkout; discarded
    after use."""
    cp = subprocess.run(["git", "show", f"{PRE_FIX_REV}:libexec/autoharn/courier"],
                        capture_output=True, text=True, cwd=REPO, check=True)
    if not cp.stdout.strip():
        raise RuntimeError(f"RED REPRO SETUP FAILED: `git show {PRE_FIX_REV}:libexec/autoharn/"
                           f"courier` returned nothing -- this checkout's history does not "
                           f"contain that commit/path.")
    if "missive_disposition" in cp.stdout and 'payload["missive_disposition"]' in cp.stdout:
        raise RuntimeError(f"RED REPRO SETUP FAILED: {PRE_FIX_REV}'s courier already forwards "
                           f"missive_disposition -- wrong revision named, or the fix predates it.")
    with open(tmp_path, "w") as f:
        f.write(cp.stdout)


def main() -> int:
    suffix = "mkfack"
    a_schema, a_kern, a_role = f"{suffix}a_scratch", f"{suffix}a_scratch_kernel", f"{suffix}a_scratch_rw"
    b_schema, b_kern, b_role = f"{suffix}b_scratch", f"{suffix}b_scratch_kernel", f"{suffix}b_scratch_rw"
    world_a, world_b = "ackworlda", "ackworldb"
    teardown(a_schema, a_kern, a_role)
    teardown(b_schema, b_kern, b_role)

    proc_a = None
    proc_b = None
    tmp_files: list[str] = []
    try:
        apply_chain(a_schema, a_kern, a_role)
        birth(a_schema, a_kern, a_role, world_a)
        apply_chain(b_schema, b_kern, b_role)
        birth(b_schema, b_kern, b_role, world_b)

        port_a, port_b = _free_port(), _free_port()
        toml_a_multiplex = f"/tmp/{suffix}_a_multiplex.toml"
        toml_b_multiplex = f"/tmp/{suffix}_b_multiplex.toml"
        tmp_files += [toml_a_multiplex, toml_b_multiplex]
        proc_a = _start_boundary(a_schema, a_kern, a_role, world_a, toml_a_multiplex, port_a)
        proc_b = _start_boundary(b_schema, b_kern, b_role, world_b, toml_b_multiplex, port_b)
        base_a, base_b = f"http://127.0.0.1:{port_a}", f"http://127.0.0.1:{port_b}"

        # STEP 1: A sends a request to B (a real, local, non-courier-actored missive_sent write
        # -- the ordinary author-side act, spec §2.2; this leg's own necessary setup, not itself
        # under test).
        out = dowrite(a_schema, a_kern, a_role, f"""
DO $$
DECLARE v {a_kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {a_kern}.ledger_write(jsonb_build_object(
    'kind','missive_sent','statement','ack-crossing: please look at this',
    'actor',(SELECT id FROM principal WHERE name='author'),
    'missive_protocol',1,'missive_author_world','{world_a}','missive_addressee_world','{world_b}',
    'missive_thread','{world_a}/ack-crossing','missive_seq',1,'missive_act','request'));
  RAISE NOTICE 'SEND: % / row=%', v.disposition, v.row_id;
END $$;
""")
        _check("setup: A's missive_sent accepted", "SEND: accepted" in out, out)

        # STEP 2: B's courier pulls A's outbound (ordinary receive leg, real current courier --
        # exercised here only because dispositioning needs a real receipt row to regard).
        toml_b_courier = f"/tmp/{suffix}_b_courier.toml"
        tmp_files.append(toml_b_courier)
        _write_courier_toml(toml_b_courier, world_b, base_b, world_a, base_a)
        cp = _run_courier(COURIER, toml_b_courier)
        print("== B's courier pulls A's request ==")
        print("  " + (cp.stdout + cp.stderr).replace("\n", "\n  "))
        _check("setup: B's courier pull of A's request exits 0", cp.returncode == 0,
               f"exit={cp.returncode}")
        _check("setup: B's courier recorded the request",
               "pulled=1 new=1" in cp.stdout and "recorded=[" in cp.stdout, cp.stdout)

        receipt_id = doquery(b_schema, b_kern, b_role,
            f"SELECT id FROM ledger_current WHERE kind='missive_received' "
            f"AND missive_thread='{world_a}/ack-crossing' AND missive_seq=1;")
        _check("setup: B's receipt row id resolved", receipt_id.isdigit(), receipt_id)

        # STEP 3: B dispositions the receipt via kernel.missive_dispose -- the two-row ceremony
        # (spec §2.7): the missive_disposed close, THEN the acknowledgment missive_sent row
        # carrying missive_disposition typed (never prose-only).
        disposition_word = "escalated"
        out = dowrite(b_schema, b_kern, b_role, f"""
DO $$
DECLARE v {b_kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {b_kern}.missive_dispose(jsonb_build_object(
    'receipt', {receipt_id}, 'disposition', '{disposition_word}',
    'actor', (SELECT id FROM principal WHERE name='author')));
  RAISE NOTICE 'DISPOSE: % / row=%', v.disposition, v.row_id;
END $$;
""")
        _check(f"setup: B's missive_dispose({disposition_word!r}) accepted, minting the ack",
               "DISPOSE: accepted" in out, out)

        ack_on_b = doquery(b_schema, b_kern, b_role,
            f"SELECT count(*) FROM missive_outbound WHERE missive_thread='{world_a}/ack-crossing' "
            f"AND missive_act='acknowledgment' AND missive_disposition='{disposition_word}';")
        _check("setup: B's own outbound view carries the acknowledgment, disposition intact "
               "(the row A's courier is about to pull)", ack_on_b == "1", ack_on_b)

        # STEP 4 (RED): A's courier AS COMMITTED AT 0429c6c pulls B's outbound -- the ack arrives
        # but the payload block never forwards missive_disposition, so the real kernel refuses on
        # missive_disposition_mandatory_on_ack. The live specimen recorded 0 of 4 acks; here, 0
        # of 1.
        toml_a_courier = f"/tmp/{suffix}_a_courier.toml"
        tmp_files.append(toml_a_courier)
        _write_courier_toml(toml_a_courier, world_a, base_a, world_b, base_b)

        pre_fix_path = f"/tmp/{suffix}_courier_prefix.py"
        tmp_files.append(pre_fix_path)
        _pre_fix_courier_copy(pre_fix_path)
        cp = _run_courier(pre_fix_path, toml_a_courier,
                          extra_pythonpath=SERVING + os.pathsep + FILING)
        red_out = cp.stdout + cp.stderr
        print("== RED: A's courier at 0429c6c pulls B's acknowledgment (stripped payload) ==")
        print("  " + red_out.replace("\n", "\n  "))
        _check("RED: A's pull of the ack is NOT recorded (0/1, stripped-payload refusal, "
               "matching row 131's own 0/4 live specimen)",
               "pulled=1 new=1" in red_out and "recorded=[]" in red_out, red_out)
        _check("RED: refused NOT as a dedup race -- the kernel names the mandatory-on-ack CHECK",
               "missive_disposition_mandatory_on_ack" in red_out, red_out)
        _check("RED: the run fails loudly (nonzero exit) rather than silently dropping the ack",
               cp.returncode != 0, cp.returncode)

        received_count_pre = doquery(a_schema, a_kern, a_role,
            f"SELECT count(*) FROM ledger_current WHERE kind='missive_received' "
            f"AND missive_author_world='{world_b}' AND missive_act='acknowledgment';")
        _check("RED: A's own schema confirms zero acknowledgment receipts landed",
               received_count_pre == "0", received_count_pre)

        # STEP 5 (GREEN): A's courier AS COMMITTED IN THIS TREE re-pulls the SAME still-unrecorded
        # ack (an idempotent retry, exactly what row 131's own live fix witnessed) and records it.
        cp = _run_courier(COURIER, toml_a_courier)
        green_out = cp.stdout + cp.stderr
        print("== GREEN: A's real courier (this tree) pulls B's acknowledgment ==")
        print("  " + green_out.replace("\n", "\n  "))
        _check("GREEN: exit 0", cp.returncode == 0, cp.returncode)
        _check("GREEN: A's pull RECORDS the ack (1/1, where the RED leg above recorded 0/1)",
               "pulled=1 new=1" in green_out and "recorded=[" in green_out
               and "recorded=[]" not in green_out, green_out)

        # (b) the recorded missive_received row on A's OWN schema carries missive_disposition
        # intact -- queried directly against the scratch schema, never taken on courier's own
        # stdout say-so.
        recorded_disposition = doquery(a_schema, a_kern, a_role,
            f"SELECT missive_disposition FROM ledger_current WHERE kind='missive_received' "
            f"AND missive_author_world='{world_b}' AND missive_thread='{world_a}/ack-crossing' "
            f"AND missive_act='acknowledgment';")
        _check(f"GREEN: the recorded ack's missive_disposition is intact ({disposition_word!r}, "
               f"exactly what B dispositioned it as)",
               recorded_disposition == disposition_word, recorded_disposition)

        received_count_post = doquery(a_schema, a_kern, a_role,
            f"SELECT count(*) FROM ledger_current WHERE kind='missive_received' "
            f"AND missive_author_world='{world_b}' AND missive_act='acknowledgment';")
        _check("GREEN: exactly one acknowledgment receipt now on A's own schema (not a "
               "duplicate, not still zero)", received_count_post == "1", received_count_post)
    finally:
        for proc in (proc_a, proc_b):
            if proc is not None:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=10)
        teardown(a_schema, a_kern, a_role)
        teardown(b_schema, b_kern, b_role)
        for p in tmp_files:
            if p.endswith(".py"):
                try:
                    os.remove(p)
                except FileNotFoundError:
                    pass
            # .toml scratch files under /tmp are left behind, matching this directory's existing
            # (pre-existing, unchanged) convention for every other courier fixture here.

    if FAILURES:
        print(f"\nack_crossing_fixture: {len(FAILURES)} FAILURE(S): {FAILURES}")
        return 1
    print("\nack_crossing_fixture: all cases behaved as expected. ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
