#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity witness for kernel/lineage/s44-model-identity-attestation.sql
(design/FABLE-OTEL-SENTRY-SPEC.md §8's scratch-schema ceremony, §8.4's witness plan). Real infra,
no mocks: scratch schema pairs in the toy db, torn down before and after. Never touches
kernel/, bootstrap/, or any live world.

WORLDS:
  WORLD PRE  -- chain ends at s45 (no s44): the .detect.sql negative polarity.
  WORLD S44  -- chain ends at s44 (on top of s45, the real lineage head at authoring time):
                the .detect.sql positive polarity, every CHECK's positive/negative leg, the FK,
                supersession, and the three affected gates run against this head.

Usage: python3 seen-red/s44-model-identity-attestation/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LINEAGE = REPO / "kernel" / "lineage"
sys.path.insert(0, str(REPO / "filing"))
from pghost_resolve import resolve_pghost  # noqa: E402

PGHOST, PGDB = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_PRE = [
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
    "s45-standing-lifecycle.sql",
]
CHAIN_S44 = CHAIN_PRE + ["s44-model-identity-attestation.sql"]


def sh(args: list[str], **kw) -> subprocess.CompletedProcess:
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


def apply_chain(world: str, chain: list[str]) -> None:
    teardown(world)
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"CREATE ROLE {world}_rw LOGIN PASSWORD 'x';"])
    if cp.returncode != 0:
        raise RuntimeError(f"role create failed: {cp.stderr}")
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={world}", "-v", f"kern={world}_kernel", "-v", f"role={world}_rw"]
    for f in chain:
        args += ["-f", str(LINEAGE / f)]
    cp = sh(args)
    if cp.returncode != 0:
        raise RuntimeError(f"chain apply failed for {world}: {cp.stdout[-2000:]} {cp.stderr[-2000:]}")


def detect(world: str, sibling: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1",
             "-v", f"schema={world}", "-f", str(LINEAGE / sibling)])
    if cp.returncode != 0:
        raise RuntimeError(f"detect failed: {cp.stderr}")
    return cp.stdout.strip()


def sql1(world: str, sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"sql1 failed ({world}): {sql}\n{cp.stderr}")
    return cp.stdout.strip()


def kernel_write(world: str, payload: dict) -> dict:
    pj = json.dumps(payload)
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-v", f"payload={pj}"],
            input=f"SET ROLE {world}_rw;\nSET search_path = {world}, {world}_kernel;\n"
                  f"SELECT to_jsonb(v) FROM {world}_kernel.ledger_write(:'payload'::jsonb) v;\n")
    if cp.returncode != 0:
        raise RuntimeError(f"kernel_write plumbing failed: {cp.stderr}")
    return json.loads(cp.stdout.strip())


def main() -> int:
    failures: list[str] = []
    world_pre, world_s44 = "s44fx_pre", "s44fx_s44"
    try:
        print(f"== scaffolding WORLD PRE (chain ends {CHAIN_PRE[-1]}) ==")
        apply_chain(world_pre, CHAIN_PRE)
        check("detect-negative-pre-s44", detect(world_pre, "s44-model-identity-attestation.detect.sql") == "f",
              "s44 .detect.sql reads f on the pre-s44 (s45-head) chain", failures)

        print(f"== scaffolding WORLD S44 (chain ends {CHAIN_S44[-1]}) ==")
        apply_chain(world_s44, CHAIN_S44)
        check("detect-positive-s44", detect(world_s44, "s44-model-identity-attestation.detect.sql") == "t",
              "s44 .detect.sql reads t on the s44-applied chain", failures)

        # minimal birth: the row_hash chain genesis seed + stamp secret (s26/s17, required
        # before ANY ledger write -- the boundary's own journal_write_refusal needs a working
        # row_hash trigger to record even a refusal) + two principals (author, write-boundary --
        # the write-boundary tool principal is the journaler's own authoring identity, s43
        # Element 6). s40's anchor-coupling deferred trigger requires the anchor INSERT and its
        # principal_registered ledger event in the SAME transaction (Element 3) -- run as one
        # script via stdin, never split across separate psql -c invocations (each of which is
        # its own implicit transaction). No scaffold birth ceremony needed for this narrow
        # kernel-shape witness.
        birth = f"""
BEGIN;
INSERT INTO {world_s44}_kernel.chain_genesis (seed)
  VALUES (encode(gen_random_bytes(32),'hex')) ON CONFLICT (only_one) DO NOTHING;
INSERT INTO {world_s44}_kernel.stamp_secret (secret) VALUES (gen_random_bytes(32));
INSERT INTO {world_s44}_kernel.principal (name, agent_class)
  VALUES ('author-fixture', 'model') RETURNING id \\gset author_
INSERT INTO {world_s44}.ledger (kind, statement, actor, principal_subject, principal_purpose)
  VALUES ('principal_registered','author (fixture)', :author_id, :author_id, 'fixture author');
INSERT INTO {world_s44}.ledger (kind, statement, actor, principal_subject, principal_db_role, principal_binding_active)
  VALUES ('principal_standing_declared','standing (fixture)', :author_id, :author_id, '{world_s44}_rw', true);
COMMIT;
BEGIN;
INSERT INTO {world_s44}_kernel.principal (name, agent_class)
  VALUES ('write-boundary', 'tool') RETURNING id \\gset wb_
INSERT INTO {world_s44}.ledger (kind, statement, actor, principal_subject, principal_purpose)
  VALUES ('principal_registered','write-boundary (fixture)', :author_id, :wb_id, 'fixture write-boundary');
COMMIT;
"""
        cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1"], input=birth)
        if cp.returncode != 0:
            raise RuntimeError(f"birth sequence failed: {cp.stdout}\n{cp.stderr}")
        author_id = sql1(world_s44, f"SELECT id FROM {world_s44}_kernel.principal "
                                     f"WHERE name='author-fixture';")
        wb_id = sql1(world_s44, f"SELECT id FROM {world_s44}_kernel.principal "
                                 f"WHERE name='write-boundary';")

        # ---- ELEMENT: a well-formed attestation is ACCEPTED --------------------------------
        target = kernel_write(world_s44, {"kind": "decision", "statement": "target row",
                                           "actor": int(author_id)})
        check("target-row-accepted", target["disposition"] == "accepted", f"target={target}", failures)
        target_id = target["row_id"]

        good = kernel_write(world_s44, {
            "kind": "model_identity_attested", "statement": "wellformed attestation",
            "actor": int(author_id), "attest_row_id": target_id,
            "attest_model": "m1", "attest_grade": "exact-command", "attest_verdict": "mismatch",
            "attest_expected": "m0", "attest_session": "sess1", "attest_basis": "command",
        })
        check("well-formed-accepted", good["disposition"] == "accepted", f"good={good}", failures)
        good_id = good["row_id"]

        # ---- NEGATIVE CONTROLS: each CHECK violation class refused --------------------------
        cases = {
            "missing-target": {"attest_model": "m1", "attest_grade": "exact-command",
                                "attest_verdict": "unevaluated", "attest_session": "s", "attest_basis": "b"},
            "empty-model": {"attest_row_id": target_id, "attest_model": "", "attest_grade": "exact-command",
                             "attest_verdict": "unevaluated", "attest_session": "s", "attest_basis": "b"},
            "bad-grade-vocab": {"attest_row_id": target_id, "attest_model": "m", "attest_grade": "bogus",
                                 "attest_verdict": "unevaluated", "attest_session": "s", "attest_basis": "b"},
            "bad-verdict-vocab": {"attest_row_id": target_id, "attest_model": "m", "attest_grade": "exact-command",
                                   "attest_verdict": "bogus", "attest_session": "s", "attest_basis": "b"},
            "expected-verdict-decoupled": {"attest_row_id": target_id, "attest_model": "m",
                                            "attest_grade": "exact-command", "attest_verdict": "unevaluated",
                                            "attest_expected": "m0", "attest_session": "s", "attest_basis": "b"},
            "fk-nonexistent-target": {"attest_row_id": 999999999, "attest_model": "m",
                                       "attest_grade": "exact-command", "attest_verdict": "unevaluated",
                                       "attest_session": "s", "attest_basis": "b"},
        }
        for name, extra in cases.items():
            payload = {"kind": "model_identity_attested", "statement": f"malformed: {name}",
                       "actor": int(author_id), **extra}
            r = kernel_write(world_s44, payload)
            check(f"refused-{name}", r["disposition"] == "refused",
                  f"{name}: {r.get('sqlstate')} {r.get('message')!r}", failures)

        # non-kind row carrying an attest column: forbidden via kind-shape CHECK
        r = kernel_write(world_s44, {"kind": "decision", "statement": "non-kind carrying attest col",
                                      "actor": int(author_id), "attest_row_id": target_id})
        check("refused-non-kind-carries-attest-col", r["disposition"] == "refused", f"{r}", failures)

        # ---- SUPERSESSION: a correction supersedes; model_attestations shows the successor ---
        corrected = kernel_write(world_s44, {
            "kind": "model_identity_attested", "statement": "corrected attestation",
            "actor": int(author_id), "attest_row_id": target_id, "supersedes": good_id,
            "attest_model": "m1-corrected", "attest_grade": "session-scoped",
            "attest_verdict": "unevaluated", "attest_session": "sess1", "attest_basis": "session",
        })
        check("supersession-accepted", corrected["disposition"] == "accepted", f"{corrected}", failures)
        rows = sql1(world_s44, f"SELECT row_id, model FROM {world_s44}.model_attestations "
                                f"WHERE attested_row_id = {target_id};")
        check("model_attestations-shows-successor-only",
              rows == f"{corrected['row_id']}|m1-corrected", f"model_attestations rows: {rows!r}", failures)

        # ---- hash_coverage_gate green on this head, red on --inject-column ------------------
        env = dict(os.environ)
        env["HARNESS_PGHOST"] = PGHOST
        cp = sh(["python3", str(REPO / "gates" / "hash_coverage_gate.py")], env=env, cwd=str(REPO))
        check("hash-coverage-gate-green", cp.returncode == 0, cp.stdout.strip()[-300:], failures)
        cp = sh(["python3", str(REPO / "gates" / "hash_coverage_gate.py"), "--inject-column", "zzz_s44fx"],
                env=env, cwd=str(REPO))
        check("hash-coverage-gate-red-on-inject", cp.returncode == 1, cp.stdout.strip()[-300:], failures)

        # ---- kind_shape_manifest_gate green, red on --inject-column -------------------------
        cp = sh(["python3", str(REPO / "gates" / "kind_shape_manifest_gate.py")], env=env, cwd=str(REPO))
        check("kind-shape-manifest-gate-green", cp.returncode == 0, cp.stdout.strip()[-300:], failures)
        cp = sh(["python3", str(REPO / "gates" / "kind_shape_manifest_gate.py"), "--inject-column", "zzz_s44fx2"],
                env=env, cwd=str(REPO))
        check("kind-shape-manifest-gate-red-on-inject", cp.returncode == 1, cp.stdout.strip()[-300:], failures)

        # ---- ledger_reader_allowlist clean, model_attestations needs no new entry -----------
        cp = sh(["python3", str(REPO / "gates" / "ledger_reader_allowlist.py")], env=env, cwd=str(REPO))
        check("ledger-reader-allowlist-clean", cp.returncode == 0 and "clean" in cp.stdout,
              cp.stdout.strip()[-300:], failures)
        check("model-attestations-classifies-clean-no-entry", "model_attestations" in cp.stdout,
              "model_attestations appears in the classified output, with no ALLOWLIST reason", failures)

    finally:
        teardown(world_pre)
        teardown(world_s44)

    if failures:
        print(f"FAIL: {len(failures)} case(s): {failures}")
        return 1
    print("all s44-model-identity-attestation cases WITNESSED clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
