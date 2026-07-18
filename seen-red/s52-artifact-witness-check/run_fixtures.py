#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T21:43:53Z
#   last-change: 2026-07-18T21:43:53Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity witness for kernel/lineage/s52-artifact-witness-check.sql
(design/FABLE-ARTIFACT-WITNESS-CHECK-SPEC.md, ledger row 1673 item 2). Real infra, no mocks:
scratch schema pairs in the toy db, torn down before and after. Never touches kernel/,
bootstrap/, or any live world (and never omega1 or any other existing world).

WORLDS:
  WORLD PRE -- chain ends at s51 (no s52): the .detect.sql negative polarity.
  WORLD S52 -- chain ends at s52 (on top of s51): the .detect.sql positive polarity, plus every
               live leg below (WX1-WX4), each cross-checked against `./judge --layer work` for
               row-for-row AGREE (the same mechanism the s48 precedent exercises -- this trigger,
               like s48's own sibling, is a PURE construction-time refusal on already-covered
               work-layer kinds, so a real AGREE is the honest result, not a vacuous one; had the
               surface been uncovered the spec's own honesty rule calls for
               UNEXERCISED-with-reason instead, the s51 precedent for that posture).

Usage: python3 seen-red/s52-artifact-witness-check/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LINEAGE = REPO / "kernel" / "lineage"
sys.path.insert(0, str(REPO / "filing"))
sys.path.insert(0, str(REPO / "engine"))
from pghost_resolve import resolve_pghost  # noqa: E402

PGHOST, PGDB = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_S51 = [
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
]
S52_FILE = "s52-artifact-witness-check.sql"
S52_DETECT = "s52-artifact-witness-check.detect.sql"


def sh(args: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def teardown(world: str) -> None:
    # FOUR SEPARATE psql -c invocations (row 1669's own witnessed hazard: a single multi-
    # statement `-c "stmt1; stmt2; stmt3"` runs as ONE implicit transaction, so a LATER
    # statement's failure -- e.g. `DROP OWNED BY <role>` when the role does not exist yet on a
    # first-ever teardown call -- rolls back the EARLIER statements too, silently undoing a
    # `DROP SCHEMA` that ran just before it in the same batch. Each statement in its own
    # invocation means a failure in one never rolls back another -- the s51-fixture fix, applied
    # here from the start rather than inherited broken.
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP SCHEMA IF EXISTS {world} CASCADE;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP SCHEMA IF EXISTS {world}_kernel CASCADE;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP OWNED BY {world}_rw;"])
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


def apply_s52(world: str) -> None:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
             "-v", f"schema={world}", "-v", f"kern={world}_kernel", "-v", f"role={world}_rw",
             "-f", str(LINEAGE / S52_FILE)])
    if cp.returncode != 0:
        raise RuntimeError(f"s52 apply failed for {world}: {cp.stdout[-2000:]} {cp.stderr[-2000:]}")


def detect(world: str, sibling: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1",
             "-v", f"schema={world}", "-v", f"kern={world}_kernel", "-f", str(LINEAGE / sibling)])
    if cp.returncode != 0:
        raise RuntimeError(f"detect failed: {cp.stderr}")
    return cp.stdout.strip()


def sql1(world: str, sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"sql1 failed ({world}): {sql}\n{cp.stderr}")
    return cp.stdout.strip()


def kernel_write(world: str, fn: str, payload: dict) -> dict:
    pj = json.dumps(payload)
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-v", f"payload={pj}"],
            input=f"SET ROLE {world}_rw;\nSET search_path = {world}, {world}_kernel;\n"
                  f"SELECT to_jsonb(v) FROM {world}_kernel.{fn}(:'payload'::jsonb) v;\n")
    if cp.returncode != 0:
        raise RuntimeError(f"kernel_write plumbing failed: {cp.stderr}")
    return json.loads(cp.stdout.strip())


def birth(world: str, author_name: str) -> str:
    script = f"""
BEGIN;
INSERT INTO {world}_kernel.chain_genesis (seed)
  VALUES (encode(gen_random_bytes(32),'hex')) ON CONFLICT (only_one) DO NOTHING;
INSERT INTO {world}_kernel.stamp_secret (secret) VALUES (gen_random_bytes(32));
INSERT INTO {world}_kernel.principal (name, agent_class)
  VALUES ('{author_name}', 'model') RETURNING id \\gset author_
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_purpose)
  VALUES ('principal_registered','author (fixture)', :author_id, :author_id, 'fixture author');
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_db_role, principal_binding_active)
  VALUES ('principal_standing_declared','standing (fixture)', :author_id, :author_id, '{world}_rw', true);
COMMIT;
BEGIN;
-- s43 Element 6: the write-boundary's OWN recording identity (needed by the SAME journaler this
-- trigger's refusals flow through, unchanged -- s43/s48/s51's own fixture precedent).
INSERT INTO {world}_kernel.principal (name, agent_class)
  VALUES ('write-boundary', 'tool') RETURNING id \\gset wb_
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_purpose)
  VALUES ('principal_registered','write-boundary (fixture)', :author_id, :wb_id, 'the kernel write boundary''s own recording identity');
COMMIT;
"""
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1"], input=script)
    if cp.returncode != 0:
        raise RuntimeError(f"birth sequence failed ({world}): {cp.stdout}\n{cp.stderr}")
    return sql1(world, f"SELECT id FROM {world}_kernel.principal WHERE name='{author_name}';")


def judge_agree(world: str, failures: list[str], label: str) -> None:
    env = dict(os.environ)
    env["HARNESS_PGHOST"] = PGHOST
    env["EPISTEMIC_PGHOST"] = PGHOST
    env["LEDGER_DB"] = PGDB
    env["LEDGER_SCHEMA"] = world
    env["LEDGER_KERN"] = f"{world}_kernel"
    env["PYTHONPATH"] = f"{REPO / 'engine'}:{REPO / 'filing'}"
    cp = sh(["python3", "-c",
             "import ledger_differential as ld\n"
             "r = ld.run_layer_differential('anyname', layer='work')\n"
             "print(r.verdict())\n"
             "print('asp', sorted(r.asp.atoms))\n"
             "print('sql', sorted(r.sql.atoms))\n"],
            env=env, cwd=str(REPO))
    if cp.returncode != 0:
        raise RuntimeError(f"judge programmatic call failed ({world}): {cp.stderr}")
    out = cp.stdout.strip().splitlines()
    check(label, out and out[0] == "AGREE", f"judge output ({world}): {out}", failures)


def main() -> int:
    failures: list[str] = []
    world_pre, world_s52 = "s52fx_pre", "s52fx_s52"
    try:
        print(f"== scaffolding WORLD PRE (chain ends {CHAIN_S51[-1]}, s52 NOT yet applied) ==")
        apply_chain(world_pre, CHAIN_S51)
        check("detect-negative-pre-s52", detect(world_pre, S52_DETECT) == "f",
              "s52 .detect.sql reads f on the pre-s52 (s51-head) chain", failures)

        print(f"== scaffolding WORLD S52 (chain ends {CHAIN_S51[-1]}, then s52 applied) ==")
        apply_chain(world_s52, CHAIN_S51)
        apply_s52(world_s52)
        check("detect-positive-post-s52", detect(world_s52, S52_DETECT) == "t",
              "s52 .detect.sql reads t once s52 is applied on top of s51", failures)

        author_id = birth(world_s52, "author-fixture")
        birth(world_pre, "author-fixture")  # so the pre-world's own AGREE run has a valid actor too

        # A real artifact, stored via s51's artifact_write, so WX1 has a genuinely-present hash
        # to cite (never a fixture that merely LOOKS like a hash).
        content = b"# s52 fixture artifact\n\nregistered so WX1 can cite a REAL hash.\n"
        valid_hash = hashlib.sha256(content).hexdigest()
        art = kernel_write(world_s52, "artifact_write",
                            {"bytes": base64.b64encode(content).decode("ascii"),
                             "media_type": "text/markdown", "actor": int(author_id)})
        check("fixture-artifact-registered", art["disposition"] == "accepted", f"{art}", failures)
        check("fixture-artifact-hash-matches", valid_hash in (art.get("message") or ""),
              f"message={art.get('message')!r} expected {valid_hash}", failures)

        # A pre-existing, citable ledger row for WX4b's row: sibling-arm probe.
        witness_row = kernel_write(world_s52, "ledger_write",
                                    {"kind": "decision", "statement": "a decision to cite as row: witness",
                                     "actor": int(author_id)})
        check("witness-row-decision-accepted", witness_row["disposition"] == "accepted",
              f"{witness_row}", failures)
        witness_id = witness_row["row_id"]

        # --- WX1: close citing artifact:<hash-of-stored-bytes> -> accepted.
        o1 = kernel_write(world_s52, "ledger_write",
                           {"kind": "work_opened", "work_slug": "wx1-item", "work_title": "wx1 item",
                            "statement": "open wx1-item", "actor": int(author_id)})
        check("wx1-open-accepted", o1["disposition"] == "accepted", f"{o1}", failures)
        c1 = kernel_write(world_s52, "ledger_write",
                           {"kind": "work_closed", "work_slug": "wx1-item", "work_resolution": "dropped",
                            "work_review_disposition": "witnessed",
                            "work_review_ref": f"artifact:{valid_hash}",
                            "statement": "close wx1-item, citing a stored artifact",
                            "actor": int(author_id)})
        check("wx1-close-citing-stored-artifact-accepted", c1["disposition"] == "accepted", f"{c1}", failures)

        # --- WX2: close citing artifact:<absent 64-hex> -> refused; teaching names the hash and
        # the put-first corrective; nothing written; refusal journaled.
        absent_hash = "f" * 64
        refusal_count_before = sql1(world_s52,
            f"SET search_path = {world_s52}; "
            f"SELECT count(*) FROM {world_s52}.ledger WHERE kind='write_refused';")
        o2 = kernel_write(world_s52, "ledger_write",
                           {"kind": "work_opened", "work_slug": "wx2-item", "work_title": "wx2 item",
                            "statement": "open wx2-item", "actor": int(author_id)})
        check("wx2-open-accepted", o2["disposition"] == "accepted", f"{o2}", failures)
        c2 = kernel_write(world_s52, "ledger_write",
                           {"kind": "work_closed", "work_slug": "wx2-item", "work_resolution": "dropped",
                            "work_review_disposition": "witnessed",
                            "work_review_ref": f"artifact:{absent_hash}",
                            "statement": "close wx2-item, citing an absent artifact hash",
                            "actor": int(author_id)})
        check("wx2-close-citing-absent-artifact-refused", c2["disposition"] == "refused", f"{c2}", failures)
        check("wx2-teach-text-names-hash-and-put-first",
              c2.get("message") is not None
              and absent_hash in c2["message"]
              and "dangling evidence pointer" in c2["message"]
              and "led artifact put" in c2["message"],
              f"message: {c2.get('message')!r}", failures)
        wx2_closed_rows = sql1(world_s52,
            f"SET search_path = {world_s52}; "
            f"SELECT count(*) FROM {world_s52}.ledger WHERE kind='work_closed' AND work_slug='wx2-item';")
        check("wx2-zero-work-closed-rows", wx2_closed_rows == "0",
              f"work_closed row count for wx2-item: {wx2_closed_rows!r}", failures)
        refusal_count_after_wx2 = sql1(world_s52,
            f"SET search_path = {world_s52}; "
            f"SELECT count(*) FROM {world_s52}.ledger WHERE kind='write_refused';")
        check("wx2-refusal-journaled",
              int(refusal_count_after_wx2) == int(refusal_count_before) + 1,
              f"write_refused count before={refusal_count_before} after={refusal_count_after_wx2}", failures)

        # --- WX3: close citing a malformed artifact:zz... token -> refused, same shape.
        o3 = kernel_write(world_s52, "ledger_write",
                           {"kind": "work_opened", "work_slug": "wx3-item", "work_title": "wx3 item",
                            "statement": "open wx3-item", "actor": int(author_id)})
        check("wx3-open-accepted", o3["disposition"] == "accepted", f"{o3}", failures)
        malformed = "zz" + "0" * 62  # 64 chars, but not [0-9a-f] -- shape-invalid, not merely absent
        c3 = kernel_write(world_s52, "ledger_write",
                           {"kind": "work_closed", "work_slug": "wx3-item", "work_resolution": "dropped",
                            "work_review_disposition": "witnessed",
                            "work_review_ref": f"artifact:{malformed}",
                            "statement": "close wx3-item, citing a malformed artifact token",
                            "actor": int(author_id)})
        check("wx3-close-citing-malformed-token-refused", c3["disposition"] == "refused", f"{c3}", failures)
        check("wx3-teach-text-names-malformed-shape",
              c3.get("message") is not None
              and malformed in c3["message"]
              and "not a well-formed" in c3["message"],
              f"message: {c3.get('message')!r}", failures)
        wx3_closed_rows = sql1(world_s52,
            f"SET search_path = {world_s52}; "
            f"SELECT count(*) FROM {world_s52}.ledger WHERE kind='work_closed' AND work_slug='wx3-item';")
        check("wx3-zero-work-closed-rows", wx3_closed_rows == "0",
              f"work_closed row count for wx3-item: {wx3_closed_rows!r}", failures)

        # Also probe a truncated (too-short) hex token and an empty token (prefix with nothing
        # after it) -- both are "malformed hex after the prefix", the same refusal shape, and
        # both exercise the GREEDY-extraction design note (a hex-anchored pattern would have
        # silently skipped these instead of refusing).
        o3b = kernel_write(world_s52, "ledger_write",
                            {"kind": "work_opened", "work_slug": "wx3b-item", "work_title": "wx3b item",
                             "statement": "open wx3b-item", "actor": int(author_id)})
        check("wx3b-open-accepted", o3b["disposition"] == "accepted", f"{o3b}", failures)
        c3b = kernel_write(world_s52, "ledger_write",
                            {"kind": "work_closed", "work_slug": "wx3b-item", "work_resolution": "dropped",
                             "work_review_disposition": "witnessed",
                             "work_review_ref": "artifact:deadbeef",
                             "statement": "close wx3b-item, citing a truncated artifact token",
                             "actor": int(author_id)})
        check("wx3b-truncated-token-refused", c3b["disposition"] == "refused", f"{c3b}", failures)
        check("wx3b-teach-text-names-malformed-shape",
              c3b.get("message") is not None and "not a well-formed" in c3b["message"],
              f"message: {c3b.get('message')!r}", failures)

        # --- WX4a: a non-close kind (decision) whose refs prose mentions artifact:<absent> ->
        # accepted (prose untouched, the WK1-c/scope-boundary precedent one arm over).
        wx4a = kernel_write(world_s52, "ledger_write",
                             {"kind": "decision", "statement": "prose citation of an absent artifact hash",
                              "refs": f"artifact:{absent_hash}", "actor": int(author_id)})
        check("wx4a-decision-refs-absent-artifact-accepted", wx4a["disposition"] == "accepted",
              f"{wx4a}", failures)

        # --- WX4b: a close citing row:<existing> + a commit arm -> accepted (sibling arms
        # unregressed -- s48's own row: check and s38's commit-arm non-goal both still legal).
        o4b = kernel_write(world_s52, "ledger_write",
                            {"kind": "work_opened", "work_slug": "wx4b-item", "work_title": "wx4b item",
                             "statement": "open wx4b-item", "actor": int(author_id)})
        check("wx4b-open-accepted", o4b["disposition"] == "accepted", f"{o4b}", failures)
        c4b = kernel_write(world_s52, "ledger_write",
                            {"kind": "work_closed", "work_slug": "wx4b-item", "work_resolution": "dropped",
                             "work_review_disposition": "witnessed",
                             "work_review_ref": f"row:{witness_id} commit:deadbeefcafefeed",
                             "statement": "close wx4b-item, citing an existing row + a commit arm",
                             "actor": int(author_id)})
        check("wx4b-close-citing-row-and-commit-arms-accepted", c4b["disposition"] == "accepted",
              f"{c4b}", failures)

        # ./judge --layer work AGREE on both polarities (the spec's own honesty rule: this
        # trigger's surface IS covered -- work_closed/work_violation_disposition are existing,
        # differential-tracked kinds -- so a real AGREE is exercised here, not claimed vacuously).
        judge_agree(world_pre, failures, "judge-work-AGREE-world-pre")
        judge_agree(world_s52, failures, "judge-work-AGREE-world-s52")

    finally:
        teardown(world_pre)
        teardown(world_s52)

    if failures:
        print(f"FAIL: {len(failures)} case(s): {failures}")
        return 1
    print("all s52-artifact-witness-check cases WITNESSED clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
