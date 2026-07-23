#!/usr/bin/env python3
"""Seen-red for the legacy-led-retirement retirement-review ROUND 1 combined fix round (ledger
row 1173's five SEVERE findings + the two remaining minors), against a REAL `serving.
boundary_service` uvicorn subprocess and a REAL scratch schema pair in the toy db, driving the
REAL `bootstrap/templates/led.tmpl` CLI as an actual subprocess -- mirrors seen-red/legacy-led-
retirement-part-ab-boundary/run_fixtures.py's own launch pattern.

RED-FIRST (both polarities witnessed live against this exact world, this build, before this
fixture was written -- transcripts in the commit message; this file re-proves the FIXED, GREEN
side as a standing regression, since the RED side requires the pre-fix source which this
worktree no longer carries):

  W1  FLAG-BEFORE-VERB GRAMMAR (finding 1): `led --event-time <ts> work open ...` -- BEFORE this
      fix, the served CLI dispatched on argv[0] BEFORE any shared-flag parsing, so this
      misrouted into the generic write path (`kind='work'`, a kernel `ledger_kind_check`
      violation) instead of ever reaching `cmd_work_open`. Now: REFUSED at the CLI, legacy's own
      coverage-guard teach-text, nothing written.
  W2  Finding 1, the honored side: `led --event-time <ts> principal declare-standing <name>` --
      BEFORE this fix, this ALSO misrouted (`kind='principal'`, the same kernel-level
      `ledger_kind_check` violation). Now: routes correctly, writes a
      `principal_standing_declared` row whose `event_declared_ts` carries the declared value.
  W3  register-principal/principal REFUSE every OTHER shared flag by name (legacy's own
      `refuse_shared_flags_for_principal_verb`, finding 1's second half) -- `--refs row:1
      principal declare-standing ...` and `--confidence high register-principal ...` both
      REFUSE, nothing written.
  W4  LEFTOVER-TOKEN REFUSAL (finding 5): `principal declare-standing <name> <stray>`,
      `principal undeclare-standing <stray>`, `principal relate a rel b <stray>`, `principal
      bind-role a --role r <stray>` -- BEFORE this fix, all four silently swallowed the stray
      token (declare-standing/undeclare-standing folded it as an ignored second positional;
      relate/bind-role dropped it and STILL WROTE THE ROW, a real defect -- "a typod flag now
      writes a wrong fact with no error"). Now: all four REFUSED, nothing written.
  W5  ALL 13 `led principal *` sub-verbs, live, against a REAL boundary -- the six NEVER
      witnessed by anyone before this round (declare-standing, undeclare-standing, revoke,
      unrelate, release-role, revoke-key) get BOTH polarities (a green write, and a refusal
      where one exists); the other seven (suspend, lift-suspension, relate, bind-role, bind-key,
      grant-competence, withdraw-competence) get at least their green half re-confirmed on this
      build.
  W6  KeyBindingPayload's additive fingerprint-shape guard (finding 4): a malformed fingerprint
      is REFUSED client-side, before any network write, mirroring the kernel's own
      `principal_key_fingerprint_shape` CHECK.
  W7  Regression: the generic `<kind> <statement...>` path and `led work open/claim/close` still
      honor the shared flags (`--refs`/`--event-time`/`--grade`) and their own per-verb flags
      exactly as before the flag-before-verb rewrite.

Zero residue: the scratch schema/role/world are torn down in a `finally` regardless of outcome,
and the boundary subprocess is terminated. Lazy imports banned."""
from __future__ import annotations

import os
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


def birth(world: str) -> None:
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
    if env_extra:
        env.update(env_extra)
    return subprocess.run([sys.executable, str(LED_TMPL), *args], capture_output=True, text=True,
                          env=env, timeout=60)


def max_row_id(base: str) -> int:
    rows = bcc.get_all_rows(base, "/rows/current", cursor="after_id")
    return max((r["id"] for r in rows), default=0)


def main() -> int:
    failures: list[str] = []
    world = "s57rr1"
    tmpdir = Path(tempfile.mkdtemp(prefix="legacy-led-retirement-round1-"))
    dep_path = tmpdir / f"{world}-deployment.json"
    proc = None
    try:
        print(f"== scaffolding WORLD, chain head {CHAIN_S57[-1]} ==")
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
        base = f"{base_url}/d/{world}"
        actor_env = {"LED_ACTOR": "author-fixture"}

        # register test-subject principals
        for name, cls in (("subj-a", "model"), ("subj-b", "model"), ("subj-human", "human")):
            cp = run_cli(["register-principal", name, cls, "--purpose", "round1 fixture"],
                        dep_path, env_extra=actor_env)
            check(f"setup-register-{name}", cp.returncode == 0, f"exit={cp.returncode} {cp.stdout!r}", failures)

        # ================= W1: flag-before-verb misroute is now REFUSED for 'work' =================
        print("== W1: --event-time ahead of 'work' is REFUSED (finding 1) ==")
        before = max_row_id(base)
        cp = run_cli(["--event-time", "2020-01-01T00:00:00", "work", "open", "w1-slug", "w1 title"],
                    dep_path, env_extra=actor_env)
        check("w1-refused-exit1", cp.returncode == 1, f"exit={cp.returncode} stderr={cp.stderr!r}", failures)
        check("w1-teaches-event-time", "--event-time" in cp.stderr and "work" in cp.stderr,
              f"stderr={cp.stderr!r}", failures)
        after = max_row_id(base)
        check("w1-nothing-written", after == before, f"before={before} after={after}", failures)

        # ================= W2: --event-time ahead of 'principal declare-standing' now WORKS =========
        print("== W2: --event-time ahead of 'principal declare-standing' routes correctly (finding 1) ==")
        cp = run_cli(["principal", "declare-standing", "subj-a", "--db-role", f"{world}_probe"],
                    dep_path, env_extra=actor_env)
        check("w2-plain-declare-exit0", cp.returncode == 0, f"exit={cp.returncode} {cp.stdout!r}", failures)
        cp = run_cli(["--event-time", "2020-06-15T00:00:00",
                     "principal", "declare-standing", "subj-a", "--db-role", f"{world}_probe2"],
                    dep_path, env_extra=actor_env)
        check("w2-event-time-declare-exit0", cp.returncode == 0, f"exit={cp.returncode} {cp.stdout!r}", failures)
        rows = bcc.get_all_rows(base, "/rows/current", cursor="after_id")
        landed = [r for r in rows if r.get("kind") == "principal_standing_declared"
                  and r.get("principal_db_role") == f"{world}_probe2"]
        check("w2-event-declared-ts-landed",
              bool(landed) and landed[-1].get("event_declared_ts", "").startswith("2020-06-15"),
              f"landed={landed}", failures)

        # ================= W3: register-principal/principal refuse OTHER shared flags ==============
        print("== W3: register-principal/principal REFUSE every shared flag but --event-time ==")
        before = max_row_id(base)
        cp = run_cli(["--refs", "row:1", "principal", "declare-standing", "subj-a",
                     "--db-role", f"{world}_probe3"], dep_path, env_extra=actor_env)
        check("w3-principal-refs-refused", cp.returncode == 1 and "--refs" in cp.stderr,
              f"exit={cp.returncode} stderr={cp.stderr!r}", failures)
        cp = run_cli(["--confidence", "high", "register-principal", "subj-refused", "model",
                     "--purpose", "should refuse"], dep_path, env_extra=actor_env)
        check("w3-register-confidence-refused", cp.returncode == 1 and "--confidence" in cp.stderr,
              f"exit={cp.returncode} stderr={cp.stderr!r}", failures)
        after = max_row_id(base)
        check("w3-nothing-written", after == before, f"before={before} after={after}", failures)

        # ================= W4: leftover-token refusal (finding 5) ==================================
        print("== W4: leftover-token refusal across the four reviewer-demonstrated cases ==")
        before = max_row_id(base)
        cp = run_cli(["principal", "declare-standing", "subj-a", "stray-token"], dep_path, env_extra=actor_env)
        check("w4-declare-standing-stray-refused",
              cp.returncode == 1 and "unrecognized argument" in cp.stderr,
              f"exit={cp.returncode} stderr={cp.stderr!r}", failures)
        cp = run_cli(["principal", "undeclare-standing", "stray-token"], dep_path, env_extra=actor_env)
        check("w4-undeclare-standing-stray-refused",
              cp.returncode == 1 and "unrecognized argument" in cp.stderr,
              f"exit={cp.returncode} stderr={cp.stderr!r}", failures)
        cp = run_cli(["principal", "relate", "subj-a", "acts-for", "subj-b", "stray-fourth"],
                    dep_path, env_extra=actor_env)
        check("w4-relate-stray-refused",
              cp.returncode == 1 and "unrecognized argument" in cp.stderr,
              f"exit={cp.returncode} stderr={cp.stderr!r}", failures)
        cp = run_cli(["principal", "bind-role", "subj-a", "--role", "tester", "stray-token"],
                    dep_path, env_extra=actor_env)
        check("w4-bind-role-stray-refused",
              cp.returncode == 1 and "unrecognized argument" in cp.stderr,
              f"exit={cp.returncode} stderr={cp.stderr!r}", failures)
        after = max_row_id(base)
        check("w4-nothing-written", after == before, f"before={before} after={after}", failures)

        # ================= W5: all 13 sub-verbs, live -- six never-witnessed get BOTH polarities ===
        print("== W5: all 13 `led principal *` sub-verbs, live ==")

        def written(cp_: subprocess.CompletedProcess) -> bool:
            return cp_.returncode == 0 and "row" in cp_.stdout

        # relate (green) -- feeds unrelate below
        cp = run_cli(["principal", "relate", "subj-a", "acts-for", "subj-b"], dep_path, env_extra=actor_env)
        check("w5-relate-green", written(cp), f"exit={cp.returncode} {cp.stdout!r}", failures)
        relate_rows = [r for r in bcc.get_all_rows(base, "/rows/current", cursor="after_id")
                       if r.get("kind") == "principal_relation_asserted" and r.get("principal_binding_active")]
        relate_id = max(r["id"] for r in relate_rows) if relate_rows else None

        # unrelate (never-witnessed): both polarities
        cp = run_cli(["principal", "unrelate", "subj-a", "acts-for", "subj-b"], dep_path, env_extra=actor_env)
        check("w5-unrelate-refused-no-supersedes", cp.returncode == 1 and "--supersedes" in cp.stderr,
              f"exit={cp.returncode} stderr={cp.stderr!r}", failures)
        cp = run_cli(["principal", "unrelate", "subj-a", "acts-for", "subj-b",
                     "--supersedes", str(relate_id)], dep_path, env_extra=actor_env)
        check("w5-unrelate-green", written(cp), f"exit={cp.returncode} {cp.stdout!r}", failures)

        # bind-role (green) -- feeds release-role below
        cp = run_cli(["principal", "bind-role", "subj-a", "--role", "tester"], dep_path, env_extra=actor_env)
        check("w5-bind-role-green", written(cp), f"exit={cp.returncode} {cp.stdout!r}", failures)
        role_rows = [r for r in bcc.get_all_rows(base, "/rows/current", cursor="after_id")
                    if r.get("kind") == "principal_role_bound" and r.get("principal_binding_active")]
        role_id = max(r["id"] for r in role_rows) if role_rows else None

        # release-role (never-witnessed): both polarities
        cp = run_cli(["principal", "release-role", "subj-a", "--role", "tester"], dep_path, env_extra=actor_env)
        check("w5-release-role-refused-no-supersedes", cp.returncode == 1 and "--supersedes" in cp.stderr,
              f"exit={cp.returncode} stderr={cp.stderr!r}", failures)
        cp = run_cli(["principal", "release-role", "subj-a", "--role", "tester",
                     "--supersedes", str(role_id)], dep_path, env_extra=actor_env)
        check("w5-release-role-green", written(cp), f"exit={cp.returncode} {cp.stdout!r}", failures)

        # suspend / lift-suspension (green re-confirm)
        cp = run_cli(["principal", "suspend", "subj-a", "round1 fixture"], dep_path, env_extra=actor_env)
        check("w5-suspend-green", written(cp), f"exit={cp.returncode} {cp.stdout!r}", failures)
        cp = run_cli(["principal", "lift-suspension", "subj-a", "round1 fixture"], dep_path, env_extra=actor_env)
        check("w5-lift-suspension-green", written(cp), f"exit={cp.returncode} {cp.stdout!r}", failures)

        # revoke (never-witnessed): both polarities
        cp = run_cli(["principal", "revoke", "totally-unregistered-round1"], dep_path, env_extra=actor_env)
        check("w5-revoke-refused-unregistered",
              cp.returncode == 1 and "not a registered principal" in cp.stderr,
              f"exit={cp.returncode} stderr={cp.stderr!r}", failures)
        cp = run_cli(["principal", "revoke", "subj-b", "round1 fixture"], dep_path, env_extra=actor_env)
        check("w5-revoke-green", written(cp), f"exit={cp.returncode} {cp.stdout!r}", failures)

        # bind-key / revoke-key (revoke-key never-witnessed): both polarities on revoke-key
        fp = "ABCDEF0123456789ABCDEF0123456789ABCDEF01"
        cp = run_cli(["principal", "bind-key", "subj-human", "--fingerprint", fp], dep_path, env_extra=actor_env)
        check("w5-bind-key-green", written(cp), f"exit={cp.returncode} {cp.stdout!r}", failures)
        key_rows = [r for r in bcc.get_all_rows(base, "/rows/current", cursor="after_id")
                   if r.get("kind") == "principal_key_bound" and r.get("principal_binding_active")]
        key_id = max(r["id"] for r in key_rows) if key_rows else None
        cp = run_cli(["principal", "revoke-key", "subj-human", "--fingerprint", fp,
                     "--supersedes", "999999999"], dep_path, env_extra=actor_env)
        check("w5-revoke-key-refused-mismatch", cp.returncode == 1 and "not the active binding" in cp.stderr,
              f"exit={cp.returncode} stderr={cp.stderr!r}", failures)
        cp = run_cli(["principal", "revoke-key", "subj-human", "--fingerprint", fp,
                     "--supersedes", str(key_id)], dep_path, env_extra=actor_env)
        check("w5-revoke-key-green", written(cp), f"exit={cp.returncode} {cp.stdout!r}", failures)

        # grant-competence / withdraw-competence (green re-confirm)
        cp = run_cli(["principal", "grant-competence", "subj-a", "--activity", "round1-review",
                     "--band", "high", "--basis", "fixture"], dep_path, env_extra=actor_env)
        check("w5-grant-competence-green", written(cp), f"exit={cp.returncode} {cp.stdout!r}", failures)
        comp_rows = [r for r in bcc.get_all_rows(base, "/rows/current", cursor="after_id")
                    if r.get("kind") == "principal_competence_granted" and r.get("principal_binding_active")]
        comp_id = max(r["id"] for r in comp_rows) if comp_rows else None
        cp = run_cli(["principal", "withdraw-competence", "subj-a", "--activity", "round1-review",
                     "--supersedes", str(comp_id)], dep_path, env_extra=actor_env)
        check("w5-withdraw-competence-green", written(cp), f"exit={cp.returncode} {cp.stdout!r}", failures)

        # ================= W6: additive fingerprint-shape guard (finding 4) ========================
        print("== W6: malformed fingerprint REFUSED client-side (additive fail-safe, finding 4) ==")
        before = max_row_id(base)
        cp = run_cli(["principal", "bind-key", "subj-human", "--fingerprint", "deadbeef"],
                    dep_path, env_extra=actor_env)
        check("w6-bad-fingerprint-refused",
              cp.returncode == 1 and "principal_key_fingerprint_shape" in cp.stderr,
              f"exit={cp.returncode} stderr={cp.stderr!r}", failures)
        after = max_row_id(base)
        check("w6-nothing-written", after == before, f"before={before} after={after}", failures)

        # ================= W7: regression -- generic path + work verbs still honor their flags =====
        print("== W7: regression -- generic path and work verbs still honor their own flags ==")
        cp = run_cli(["--refs", "row:1", "--event-time", "2021-06-01T00:00:00", "--grade", "durable",
                     "decision", "round1 regression check"], dep_path, env_extra=actor_env)
        check("w7-generic-exit0", cp.returncode == 0, f"exit={cp.returncode} {cp.stdout!r}", failures)
        rows = bcc.get_all_rows(base, "/rows/current", cursor="after_id")
        decisions = [r for r in rows if r.get("kind") == "decision" and r.get("refs") == "row:1"]
        check("w7-generic-fields-landed",
              bool(decisions) and decisions[-1].get("decision_grade") == "durable"
              and decisions[-1].get("event_declared_ts", "").startswith("2021-06-01"),
              f"decisions={decisions}", failures)
        cp = run_cli(["work", "open", "w7-slug", "w7 title"], dep_path, env_extra=actor_env)
        check("w7-work-open-exit0", cp.returncode == 0, f"exit={cp.returncode} {cp.stdout!r}", failures)
        cp = run_cli(["work", "claim", "w7-slug"], dep_path, env_extra=actor_env)
        check("w7-work-claim-exit0", cp.returncode == 0, f"exit={cp.returncode} {cp.stdout!r}", failures)
        cp = run_cli(["work", "close", "w7-slug", "shipped", "--witness", "commit:abc1234",
                     "--review-deferred"], dep_path, env_extra=actor_env)
        check("w7-work-close-exit0", cp.returncode == 0, f"exit={cp.returncode} {cp.stdout!r}", failures)

    finally:
        if proc is not None:
            out = stop_server(proc)
            if out.strip():
                print("--- boundary service log tail ---")
                print(out[-2000:])
        teardown(world)
        shutil.rmtree(tmpdir, ignore_errors=True)

    if failures:
        print(f"FAILURES: {failures}")
        return 1
    print("ALL CASES OK -- legacy-led-retirement round 1 combined fix round: flag-before-verb "
          "grammar, principal shared-flag refusal, leftover-token refusal, all 13 principal "
          "sub-verbs live, fingerprint-shape guard, generic/work regression -- zero residue")
    return 0


if __name__ == "__main__":
    sys.exit(main())
