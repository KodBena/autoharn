#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T17:33:19Z
#   last-change: 2026-07-18T17:33:46Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity witness for kernel/lineage/s50-defeat-input-raw-domain.sql
(design/FABLE-S46-DEFEAT-INPUT-DOMAIN-SPEC.md, ledger row 1647). Real infra, no mocks: scratch
schema pairs in the toy db, torn down before and after. Never touches kernel/, bootstrap/, or any
live world.

WORLDS:
  WORLD DIVERGE (s50fx_diverge) -- chain ends at s46 (no s50), then s50 is applied IN PLACE on
    the SAME schema (a scratch-only CREATE OR REPLACE VIEW re-issue, never a live-world apply --
    this is exactly what the delta's own file does, exercised here for a single-world
    before/after comparison instead of two separately-birthed schemas, so WS46-a and WS46-c can
    both read "on WS46-a's world" literally, per the spec's own wording). Constructs the exact
    divergence shape s46's own header names: a model_identity_attested row (R) later superseded
    by a different-kind row, then a second attestation (A2) naming R as its own attest_row_id --
    i.e. R is simultaneously the machinery-input row AND the defeated-candidate row.
      BEFORE (pre-fix, s46-only): .detect.sql reads f; the KERNEL VIEW (model_defeated_rows)
        wrongly shows R as defeated (ledger_current-only exclusion misses R once superseded);
        the SQL FLOOR (engine/ledger_floor.py::defeat_floor_atoms, one of the two independent
        `./judge --layer defeat` producers, which reads raw history unconditionally) already
        excludes R -- the view/engine DISAGREEMENT this delta exists to close.
      AFTER (post-fix, s50 applied in place): .detect.sql reads t; the view now AGREES with the
        SQL floor (both exclude R) and with `./judge --layer defeat` (both producers, unaffected
        by this delta since neither ever read the kernel view, still AGREE -- reconfirmed, not a
        new claim).
  WORLD PLAIN (s50fx_plain) -- chain ends at s46 (no s50), a PLAIN scenario with attestation
    mismatches and NO kind-changing supersession chain (mirrors s46's own W1 fixture exactly):
    credited_current and model_defeated_rows output captured BEFORE, s50 applied in place,
    captured AFTER -- byte-for-byte identical (WS46-b, no regression).

Usage: python3 seen-red/s50-defeat-input-raw-domain/run_fixtures.py
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
sys.path.insert(0, str(REPO / "engine"))
from pghost_resolve import resolve_pghost  # noqa: E402

PGHOST, PGDB = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_S46 = [
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
    "s46-credited-views.sql",
]
S50_FILE = "s50-defeat-input-raw-domain.sql"


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


def apply_s50(world: str) -> None:
    """Re-issues model_defeated_rows IN PLACE on an already-s46-applied schema (the delta's own
    idempotent CREATE OR REPLACE VIEW, exercised as a scratch-only before/after probe -- never a
    live-world apply, matching runs-are-strictly-linear's own scratch-witness carve-out)."""
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
             "-v", f"schema={world}", "-v", f"kern={world}_kernel", "-v", f"role={world}_rw",
             "-f", str(LINEAGE / S50_FILE)])
    if cp.returncode != 0:
        raise RuntimeError(f"s50 apply failed for {world}: {cp.stdout[-2000:]} {cp.stderr[-2000:]}")


def detect(world: str, sibling: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1",
             "-v", f"schema={world}", "-f", str(LINEAGE / sibling)])
    if cp.returncode != 0:
        raise RuntimeError(f"detect failed: {cp.stderr}")
    return cp.stdout.strip()


def sql1(sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"sql1 failed: {sql}\n{cp.stderr}")
    return cp.stdout.strip()


def sqlrows(sql: str) -> list[str]:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"sqlrows failed: {sql}\n{cp.stderr}")
    return [l for l in cp.stdout.splitlines() if l.strip()]


def kernel_write(world: str, payload: dict) -> dict:
    pj = json.dumps(payload)
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-v", f"payload={pj}"],
            input=f"SET ROLE {world}_rw;\nSET search_path = {world}, {world}_kernel;\n"
                  f"SELECT to_jsonb(v) FROM {world}_kernel.ledger_write(:'payload'::jsonb) v;\n")
    if cp.returncode != 0:
        raise RuntimeError(f"kernel_write plumbing failed: {cp.stderr}")
    return json.loads(cp.stdout.strip())


def birth(world: str) -> tuple[str, str]:
    """Genesis + stamp secret + author + a 'tool' sentry principal, same-transaction anchor-
    coupling as s44's/s46's own fixtures. Returns (author_id, sentry_id)."""
    seq = f"""
BEGIN;
INSERT INTO {world}_kernel.chain_genesis (seed)
  VALUES (encode(gen_random_bytes(32),'hex')) ON CONFLICT (only_one) DO NOTHING;
INSERT INTO {world}_kernel.stamp_secret (secret) VALUES (gen_random_bytes(32));
INSERT INTO {world}_kernel.principal (name, agent_class)
  VALUES ('author-fixture', 'model') RETURNING id \\gset author_
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_purpose)
  VALUES ('principal_registered','author (fixture)', :author_id, :author_id, 'fixture author');
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_db_role, principal_binding_active)
  VALUES ('principal_standing_declared','standing (fixture)', :author_id, :author_id, '{world}_rw', true);
COMMIT;
BEGIN;
INSERT INTO {world}_kernel.principal (name, agent_class)
  VALUES ('sentry-fixture', 'tool') RETURNING id \\gset sentry_
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_purpose)
  VALUES ('principal_registered','sentry (fixture)', :author_id, :sentry_id, 'fixture sentry');
COMMIT;
"""
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1"], input=seq)
    if cp.returncode != 0:
        raise RuntimeError(f"birth sequence failed ({world}): {cp.stdout}\n{cp.stderr}")
    author_id = sql1(f"SELECT id FROM {world}_kernel.principal WHERE name='author-fixture';")
    sentry_id = sql1(f"SELECT id FROM {world}_kernel.principal WHERE name='sentry-fixture';")
    return author_id, sentry_id


def grant_competence(world: str, author_id: str, sentry_id: str) -> str:
    grant = kernel_write(world, {
        "kind": "principal_competence_granted", "statement": "fixture grant",
        "actor": int(author_id), "principal_subject": int(sentry_id),
        "principal_competence_activity": "model-identity-attestation",
        "principal_binding_active": True,
        "principal_competence_band": "high", "principal_competence_basis": "fixture",
    })
    if grant["disposition"] != "accepted":
        raise RuntimeError(f"grant not accepted: {grant}")
    return grant["row_id"]


def defeat_floor_model_defeated_row_ids(world: str) -> set[str]:
    """The row-ids the SQL FLOOR (one of the two independent `./judge --layer defeat` producers)
    considers defeated, read via engine/ledger_floor.py::defeat_floor_atoms -- NEVER the kernel
    view, so this is the independent cross-check WS46-a's own wording names ("both engine
    producers")."""
    env = dict(os.environ)
    env["HARNESS_PGHOST"] = PGHOST
    env["EPISTEMIC_PGHOST"] = PGHOST
    env["LEDGER_DB"] = PGDB
    env["LEDGER_SCHEMA"] = world
    env["LEDGER_KERN"] = f"{world}_kernel"
    env["PYTHONPATH"] = f"{REPO / 'engine'}:{REPO / 'filing'}"
    cp = sh(["python3", "-c",
             "import ledger_floor; "
             "atoms = ledger_floor.defeat_floor_atoms('anyname'); "
             "print('\\n'.join(sorted(atoms)))"],
            env=env, cwd=str(REPO))
    if cp.returncode != 0:
        raise RuntimeError(f"floor atoms failed: {cp.stderr}")
    ids: set[str] = set()
    for line in cp.stdout.strip().splitlines():
        line = line.strip()
        if line.startswith("model_defeated("):
            inner = line[len("model_defeated("):-1]
            ids.add(inner.split(",")[0])
    return ids


def judge_defeat_agree(world: str) -> tuple[bool, list[str]]:
    env = dict(os.environ)
    env["HARNESS_PGHOST"] = PGHOST
    env["EPISTEMIC_PGHOST"] = PGHOST
    env["LEDGER_DB"] = PGDB
    env["LEDGER_SCHEMA"] = world
    env["LEDGER_KERN"] = f"{world}_kernel"
    env["PYTHONPATH"] = f"{REPO / 'engine'}:{REPO / 'filing'}"
    cp = sh(["python3", "-c",
             "import ledger_differential as ld\n"
             "r = ld.run_layer_differential('anyname', layer='defeat')\n"
             "print(r.verdict())\n"
             "print('asp', sorted(r.asp.atoms))\n"
             "print('sql', sorted(r.sql.atoms))\n"],
            env=env, cwd=str(REPO))
    if cp.returncode != 0:
        raise RuntimeError(f"judge programmatic call failed: {cp.stderr}")
    out = cp.stdout.strip().splitlines()
    return (bool(out) and out[0] == "AGREE"), out


def run_world_diverge(failures: list[str]) -> None:
    world = "s50fx_diverge"
    print(f"== scaffolding WORLD DIVERGE (chain ends s46, s50 applied in place after) ==")
    apply_chain(world, CHAIN_S46)
    check("detect-negative-pre-s50", detect(world, "s50-defeat-input-raw-domain.detect.sql") == "f",
          "s50 .detect.sql reads f on the s46-only (pre-s50) chain", failures)

    author_id, sentry_id = birth(world)
    grant_competence(world, author_id, sentry_id)

    # target0: an arbitrary decision row the FIRST attestation (R) will attest as a mismatch.
    target0 = kernel_write(world, {"kind": "decision", "statement": "target0", "actor": int(author_id)})
    target0_id = target0["row_id"]

    # R: a model_identity_attested row -- itself a defeat-machinery INPUT row (attest_row/1 EDB).
    r_att = kernel_write(world, {
        "kind": "model_identity_attested", "statement": "R -- the machinery-input row",
        "actor": int(sentry_id), "attest_row_id": int(target0_id),
        "attest_model": "observed-model-r", "attest_grade": "exact-command",
        "attest_verdict": "mismatch", "attest_expected": "declared-model-r",
        "attest_session": "sess-diverge-r", "attest_basis": "command,session",
    })
    check("R-attestation-accepted", r_att["disposition"] == "accepted", f"{r_att}", failures)
    r_id = str(r_att["row_id"])

    # S: a row of a DIFFERENT kind superseding R -- the "kind CHANGE across a supersession chain"
    # s46's own header names as the divergence's precondition. No kind-restriction applies to
    # model_identity_attested targets (only the three s45 standing-lifecycle kinds are
    # kind-locked) -- verified against s45's own validate_supersession_target text before relying
    # on this write succeeding.
    s_row = kernel_write(world, {
        "kind": "decision", "statement": "S -- supersedes R with a different kind",
        "actor": int(author_id), "supersedes": int(r_id),
    })
    check("S-supersession-accepted", s_row["disposition"] == "accepted", f"{s_row}", failures)

    # A2: a SECOND attestation naming R itself as its attest_row_id -- R is now BOTH the
    # machinery-input row and the defeated-candidate row, the exact divergence shape.
    a2_att = kernel_write(world, {
        "kind": "model_identity_attested", "statement": "A2 -- claims R itself is a mismatch",
        "actor": int(sentry_id), "attest_row_id": int(r_id),
        "attest_model": "observed-model-a2", "attest_grade": "exact-command",
        "attest_verdict": "mismatch", "attest_expected": "declared-model-a2",
        "attest_session": "sess-diverge-a2", "attest_basis": "command,session",
    })
    check("A2-attestation-accepted", a2_att["disposition"] == "accepted", f"{a2_att}", failures)

    # ---- BEFORE (pre-fix, s46-only): reproduce the disagreement ----
    view_before = set(sqlrows(f"SELECT row_id FROM {world}.model_defeated_rows;"))
    floor_before = defeat_floor_model_defeated_row_ids(world)
    check("WS46a-before-view-wrongly-defeats-R", r_id in view_before,
          f"model_defeated_rows (pre-fix) row_ids: {sorted(view_before)} -- expected {r_id} present", failures)
    check("WS46a-before-floor-never-defeats-R", r_id not in floor_before,
          f"SQL floor (raw-history, always correct) row_ids: {sorted(floor_before)} -- expected {r_id} absent",
          failures)
    check("WS46a-before-view-engine-DISAGREE", r_id in view_before and r_id not in floor_before,
          "the pre-fix polarity: kernel view and SQL floor disagree on row " + str(r_id), failures)
    judge_before_ok, judge_before_out = judge_defeat_agree(world)
    check("WS46a-before-judge-defeat-AGREE-unaffected",
          judge_before_ok,
          f"judge --layer defeat (SQL-floor vs ASP, neither reads the kernel view -- unaffected by "
          f"this delta either side of the fix): {judge_before_out}", failures)

    # ---- apply s50 IN PLACE on this SAME schema/world ----
    apply_s50(world)
    check("detect-positive-post-s50", detect(world, "s50-defeat-input-raw-domain.detect.sql") == "t",
          "s50 .detect.sql reads t once s50 is applied on top of s46", failures)

    # ---- AFTER (post-fix): view now AGREES with the SQL floor and with judge ----
    view_after = set(sqlrows(f"SELECT row_id FROM {world}.model_defeated_rows;"))
    floor_after = defeat_floor_model_defeated_row_ids(world)
    check("WS46a-after-view-excludes-R", r_id not in view_after,
          f"model_defeated_rows (post-fix) row_ids: {sorted(view_after)} -- expected {r_id} absent", failures)
    check("WS46a-after-view-AGREES-with-floor", view_after == floor_after,
          f"view row_ids {sorted(view_after)} vs SQL floor row_ids {sorted(floor_after)}", failures)
    judge_after_ok, judge_after_out = judge_defeat_agree(world)
    check("WS46a-after-judge-defeat-AGREE", judge_after_ok, f"judge output: {judge_after_out}", failures)

    # ---- WS46-c: fail-safe direction -- the fix only SHRINKS the defeated set ----
    newly_defeatable = view_after - view_before
    check("WS46c-fail-safe-shrink-only-empty-newly-defeatable", newly_defeatable == set(),
          f"view_after \\ view_before (the newly-defeatable direction) = {sorted(newly_defeatable)} "
          f"-- must be empty; view_before \\ view_after = {sorted(view_before - view_after)} "
          f"(the shrinkage, expected non-empty, containing {r_id})", failures)
    check("WS46c-shrinkage-contains-R", r_id in (view_before - view_after),
          f"view_before \\ view_after = {sorted(view_before - view_after)} -- expected to contain {r_id}",
          failures)

    teardown(world)


def run_world_plain(failures: list[str]) -> None:
    world = "s50fx_plain"
    print(f"== scaffolding WORLD PLAIN (chain ends s46, s50 applied in place after; no "
          f"kind-changing supersession) ==")
    apply_chain(world, CHAIN_S46)
    author_id, sentry_id = birth(world)
    grant_competence(world, author_id, sentry_id)

    target = kernel_write(world, {"kind": "decision", "statement": "plain target row",
                                   "actor": int(author_id)})
    target_id = target["row_id"]
    attest = kernel_write(world, {
        "kind": "model_identity_attested", "statement": "plain mismatch attestation",
        "actor": int(sentry_id), "attest_row_id": int(target_id),
        "attest_model": "observed-model-plain", "attest_grade": "exact-command",
        "attest_verdict": "mismatch", "attest_expected": "declared-model-plain",
        "attest_session": "sess-plain", "attest_basis": "command,session",
    })
    check("plain-attestation-accepted", attest["disposition"] == "accepted", f"{attest}", failures)

    mdr_before = sqlrows(f"SELECT row_id, attest_id, grant_id, model, grade FROM {world}.model_defeated_rows ORDER BY row_id;")
    cc_before = sqlrows(f"SELECT id FROM {world}.credited_current ORDER BY id;")

    apply_s50(world)

    mdr_after = sqlrows(f"SELECT row_id, attest_id, grant_id, model, grade FROM {world}.model_defeated_rows ORDER BY row_id;")
    cc_after = sqlrows(f"SELECT id FROM {world}.credited_current ORDER BY id;")

    check("WS46b-model-defeated-rows-byte-identical", mdr_before == mdr_after,
          f"before={mdr_before!r} after={mdr_after!r}", failures)
    check("WS46b-credited-current-byte-identical", cc_before == cc_after,
          f"before={cc_before!r} after={cc_after!r}", failures)

    teardown(world)


def main() -> int:
    failures: list[str] = []
    try:
        run_world_diverge(failures)
        run_world_plain(failures)
    finally:
        teardown("s50fx_diverge")
        teardown("s50fx_plain")

    if failures:
        print(f"FAIL: {len(failures)} case(s): {failures}")
        return 1
    print("all s50-defeat-input-raw-domain cases WITNESSED clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
