#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity witness for kernel/lineage/s57-obligation-revocation-event.sql
(design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part A, maintainer-ratified ledger row 1150). Real
infra, no mocks: scratch schema pairs in the toy db, torn down before and after. Never touches
kernel/, bootstrap/ (beyond reading the templates as fixtures), or any live world.

WITNESSES (per the spec's own Part A "Witness plan"):
  WA1  obligate, then revoke via kernel.obligation_revoke -- review_gap shows not-in-force from
       the event (the obliged actor's un-countersigned rows leave the gap view).
  WA2  the raw DELETE on countersign_obligation is refused AT THE GRANT LAYER (SQLSTATE 42501)
       for the granted role -- RED-FIRST: witnessed failing (the actual refusal) before any
       accept-path assertion, exactly the spec's own "red-first" plan order.
  WA3  an un-revoked obligation is UNAFFECTED -- a second, distinct scope stays in review_gap.
  WA4  refusal case: revoking an unknown scope is refused, journaled, nothing recorded.
  WA5  refusal case: revoking an already-revoked scope a second time is refused (duplicate),
       journaled, nothing recorded twice.
  WA6  boundary round-trip: the SAME obligate/revoke ceremony through the served boundary's
       /write/obligation and /write/obligation_revoke routes (serving/boundary_service.py,
       in-process TestClient-free -- a real uvicorn-less ASGI call via httpx's ASGITransport
       would add a dependency this project does not carry; this fixture instead calls the route
       HANDLER functions' own underlying kernel-call path the same way the boundary-cli-rebase
       fixture's own `run_cli` precedent exercises a real subprocess -- see WA6 below for the
       exact mechanism chosen and why).
  WA7  SQL/ASP differential (engine/review_gap_differential.py) AGREEs on this fixture's own
       schema, both with and without the revocation applied (two separate scratch schemas so the
       "before" and "after" states are both independently witnessed, never inferred).

Usage: python3 seen-red/s57-obligation-revocation-event/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LINEAGE = REPO / "kernel" / "lineage"
LED_TMPL = REPO / "bootstrap" / "templates" / "led.tmpl"
sys.path.insert(0, str(REPO / "filing"))
sys.path.insert(0, str(REPO / "serving"))
sys.path.insert(0, str(REPO / "engine"))
sys.path.insert(0, str(REPO / "bootstrap"))
from pghost_resolve import resolve_pghost  # noqa: E402
import deployment_record  # noqa: E402
import review_gap_edb  # noqa: E402
import review_gap_floor  # noqa: E402

PGHOST, PGDB = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_S56 = [
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
    "s56-reservation-residue.sql",
]
S57_FILE = "s57-obligation-revocation-event.sql"
S57_DETECT = "s57-obligation-revocation-event.detect.sql"


def sh(args: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def teardown(world: str) -> None:
    # Three separate invocations (the s51 fixture's own lesson, restated): a single batched -c
    # string rolls a later statement's failure back over an earlier one.
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


def apply_s57(world: str) -> None:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
             "-v", f"schema={world}", "-v", f"kern={world}_kernel", "-v", f"role={world}_rw",
             "-f", str(LINEAGE / S57_FILE)])
    if cp.returncode != 0:
        raise RuntimeError(f"s57 apply failed for {world}: {cp.stdout[-2000:]} {cp.stderr[-2000:]}")


def detect(world: str, sibling: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1",
             "-v", f"schema={world}", "-v", f"kern={world}_kernel", "-f", str(LINEAGE / sibling)])
    if cp.returncode != 0:
        raise RuntimeError(f"detect failed: {cp.stderr}")
    return cp.stdout.strip()


def sql1(world: str, sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"sql1 failed: {sql}\n{cp.stderr}")
    return cp.stdout.strip()


def kernel_write(world: str, fn: str, payload: dict) -> dict:
    pj = json.dumps(payload)
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-v", f"payload={pj}"],
            input=f"SET ROLE {world}_rw;\nSET search_path = {world}, {world}_kernel;\n"
                  f"SELECT to_jsonb(v) FROM {world}_kernel.{fn}(:'payload'::jsonb) v;\n")
    if cp.returncode != 0:
        raise RuntimeError(f"kernel_write plumbing failed: {cp.stderr}")
    return json.loads(cp.stdout.strip())


def birth(world: str) -> tuple[str, str]:
    """Genesis + stamp secret + author + reviewer + write-boundary tool principal + standing
    declaration -- the s51 fixture's own shape. Returns (author_id, reviewer_id)."""
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
    author_id = sql1(world, f"SELECT id FROM {world}_kernel.principal WHERE name='author-fixture';")
    reviewer_id = sql1(world, f"SELECT id FROM {world}_kernel.principal WHERE name='reviewer-fixture';")
    return author_id, reviewer_id


def run_cli(args: list[str], deployment: Path, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["AUTOHARN"] = str(REPO)
    env["PICKUP_DEPLOYMENT"] = str(deployment)
    if env_extra:
        env.update(env_extra)
    return subprocess.run([sys.executable, str(LED_TMPL), *args], capture_output=True, text=True,
                          env=env, timeout=60)


def write_served_deployment(path: Path, world: str, boundary_url: str, boundary_deployment: str) -> None:
    rec = deployment_record.DeploymentRecord(
        db=PGDB, host=PGHOST, schema=world, kern=f"{world}_kernel", role=f"{world}_rw",
        name=world, boundary_url=boundary_url, boundary_deployment=boundary_deployment)
    deployment_record.write_deployment(path, rec)


def differential_env(world: str) -> dict:
    env = dict(os.environ)
    env["LEDGER_DB"] = PGDB
    env["LEDGER_SCHEMA"] = world
    env["LEDGER_KERN"] = f"{world}_kernel"
    return env


def run_differential(world: str) -> subprocess.CompletedProcess:
    return sh([sys.executable, str(REPO / "engine" / "review_gap_differential.py"), world],
              env=differential_env(world))


class _EnvTarget:
    """Context manager: point engine/targets.py's env-override resolution (LEDGER_DB/
    LEDGER_SCHEMA/LEDGER_KERN) at `world` for the duration of the block, restoring whatever was
    there before on exit -- this fixture's OWN process calls review_gap_edb.export()/
    review_gap_floor.floor_atoms() in-process (not via subprocess) for atom-level assertions the
    differential CLI's AGREE/DISAGREE verdict alone does not expose."""

    def __init__(self, world: str) -> None:
        self.world = world
        self._saved: dict[str, str | None] = {}

    def __enter__(self) -> str:
        for k, v in (("LEDGER_DB", PGDB), ("LEDGER_SCHEMA", self.world),
                     ("LEDGER_KERN", f"{self.world}_kernel")):
            self._saved[k] = os.environ.get(k)
            os.environ[k] = v
        return self.world

    def __exit__(self, *exc) -> None:
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def main() -> int:
    failures: list[str] = []
    world = "s57fx"
    tmpdir = tempfile.mkdtemp(prefix="s57-obligation-revocation-")
    dep_path = Path(tmpdir) / f"{world}-legacy-deployment.json"
    try:
        print(f"== scaffolding WORLD (chain ends {CHAIN_S56[-1]}, s57 NOT yet applied) ==")
        apply_chain(world, CHAIN_S56)
        check("detect-negative-pre-s57", detect(world, S57_DETECT) == "f",
              "s57 .detect.sql reads f on the s56-headed (pre-s57) chain", failures)

        author_id, reviewer_id = birth(world)

        # ==================== WA2 RED-FIRST: raw DELETE refused, PRE-s57 already ====================
        # s20 never granted DELETE on countersign_obligation to the role in the first place --
        # witnessed HERE, before s57 lands, so the "red" half of this witness plan is the
        # PRE-EXISTING refusal (s57 does not newly create it, it makes it explicit/defense-in-depth
        # via a belt-and-braces REVOKE). First: obligate a scope so there is a row to attempt
        # deleting.
        # obliges the REVIEWER (not the author) -- WA1 below checks obliged(author) in isolation;
        # this probe's own obligation must not silently keep author obliged through an unrelated,
        # never-revoked scope.
        v_ob0 = kernel_write(world, "obligation_write",
                              {"scope": "wa2-pre-check", "assigned_by": int(author_id),
                               "obliges_actor": int(reviewer_id)})
        check("wa2-setup-obligate-accepted", v_ob0["disposition"] == "accepted", f"{v_ob0}", failures)
        del_cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1"],
                    input=f"SET ROLE {world}_rw;\nSET search_path = {world}, {world}_kernel;\n"
                          f"DELETE FROM countersign_obligation WHERE scope = 'wa2-pre-check';\n")
        check("wa2-raw-delete-refused-pre-s57", del_cp.returncode != 0 and "permission denied" in del_cp.stderr.lower(),
              f"exit={del_cp.returncode} stderr={del_cp.stderr!r} -- expected a permission-denied "
              f"failure (s20 never granted DELETE to the role at all)", failures)

        print("== applying s57 in place ==")
        apply_s57(world)
        check("detect-positive-post-s57", detect(world, S57_DETECT) == "t",
              "s57 .detect.sql reads t once s57 is applied on top of s56", failures)

        # WA2, again, post-s57: the SAME raw DELETE, now ALSO belt-and-braces REVOKEd explicitly.
        del_cp2 = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1"],
                     input=f"SET ROLE {world}_rw;\nSET search_path = {world}, {world}_kernel;\n"
                           f"DELETE FROM countersign_obligation WHERE scope = 'wa2-pre-check';\n")
        check("wa2-raw-delete-refused-post-s57", del_cp2.returncode != 0 and "permission denied" in del_cp2.stderr.lower(),
              f"exit={del_cp2.returncode} stderr={del_cp2.stderr!r}", failures)
        still_there = sql1(world, f"SET ROLE {world}_rw; SET search_path={world},{world}_kernel; "
                                  f"SELECT count(*) FROM countersign_obligation WHERE scope='wa2-pre-check';")
        check("wa2-row-still-present", still_there == "1", f"count={still_there}", failures)

        # ==================== WA1: obligate, revoke, review_gap reflects not-in-force ====================
        print("== WA1: obligate -> un-countersigned row appears in review_gap; revoke -> it leaves ==")
        v_ob1 = kernel_write(world, "obligation_write",
                              {"scope": "wa1-scope", "assigned_by": int(reviewer_id),
                               "obliges_actor": int(author_id)})
        check("wa1-obligate-accepted", v_ob1["disposition"] == "accepted", f"{v_ob1}", failures)
        v_row = kernel_write(world, "ledger_write",
                              {"kind": "finding", "statement": "WA1 fixture row by the obliged actor",
                               "actor": int(author_id)})
        check("wa1-candidate-row-accepted", v_row["disposition"] == "accepted", f"{v_row}", failures)
        gap_before = sql1(world, f"SET ROLE {world}_rw; SET search_path={world},{world}_kernel; "
                                 f"SELECT count(*) FROM review_gap WHERE id = {v_row['row_id']} "
                                 f"AND scope = 'wa1-scope';")
        check("wa1-row-in-gap-before-revoke", gap_before == "1", f"count={gap_before}", failures)

        # A GENUINE content-free review (the run12-specimen shape review_gap_audit.lp exists to
        # flag) discharging the SAME candidate row, by a DIFFERENT actor (reviewer) -- this is
        # what makes engine/review_gap_edb.py's/engine/review_gap_floor.py's own obliged/1
        # extension load-bearing: discharges(R,L)/flagged(R) can ONLY be derived while
        # obliged(author) holds. Written BEFORE the revoke below.
        v_review1 = kernel_write(world, "review_write",
                                  {"regards": int(v_row["row_id"]), "statement": "ok",
                                   "verdict": "attest", "independence": "disclosed-isolated-dispatch",
                                   "basis": "ok", "actor": int(reviewer_id)})
        check("wa1-content-free-review-accepted", v_review1["disposition"] == "accepted",
              f"{v_review1}", failures)
        r_id = v_review1["row_id"]
        with _EnvTarget(world):
            pre_floor = review_gap_floor.floor_atoms(world)
            pre_asp = review_gap_edb.export(world)
        check("wa1-pre-revoke-discharges-present",
              f"discharges({r_id},{v_row['row_id']})" in pre_floor,
              f"floor atoms={sorted(pre_floor)}", failures)
        check("wa1-pre-revoke-flagged-present", f"flagged({r_id})" in pre_floor,
              f"floor atoms={sorted(pre_floor)}", failures)
        check("wa1-pre-revoke-asp-obliged-fact-present",
              f"obliged({int(author_id)})." in pre_asp.facts,
              f"asp facts={pre_asp.facts}", failures)
        diff_pre = run_differential(world)
        check("wa1-pre-revoke-differential-green",
              diff_pre.returncode == 0 and "DIFFERENTIAL GREEN" in diff_pre.stdout,
              f"stdout_tail={diff_pre.stdout[-1500:]}", failures)

        v_rev1 = kernel_write(world, "obligation_revoke",
                               {"scope": "wa1-scope", "reason": "WA1 fixture revocation",
                                "actor": int(reviewer_id)})
        check("wa1-revoke-accepted", v_rev1["disposition"] == "accepted", f"{v_rev1}", failures)
        event_row = sql1(world, f"SET ROLE {world}_rw; SET search_path={world},{world}_kernel; "
                                f"SELECT kind, obligation_revoked_scope, obligation_revoke_reason "
                                f"FROM ledger WHERE id = {v_rev1['row_id']};")
        check("wa1-event-shape",
              event_row == "obligation_revoked|wa1-scope|WA1 fixture revocation",
              f"row={event_row!r}", failures)
        gap_after = sql1(world, f"SET ROLE {world}_rw; SET search_path={world},{world}_kernel; "
                                f"SELECT count(*) FROM review_gap WHERE id = {v_row['row_id']} "
                                f"AND scope = 'wa1-scope';")
        check("wa1-row-out-of-gap-after-revoke", gap_after == "0", f"count={gap_after}", failures)
        obligation_row_still_present = sql1(world,
            f"SET ROLE {world}_rw; SET search_path={world},{world}_kernel; "
            f"SELECT count(*) FROM countersign_obligation WHERE scope = 'wa1-scope';")
        check("wa1-obligation-row-never-deleted", obligation_row_still_present == "1",
              f"count={obligation_row_still_present} -- the countersign_obligation row must stand "
              f"forever; revocation is an ADDITIVE event, never a DELETE", failures)

        # POST-revoke: author carries NO other obligation yet (WA3's second obligation is created
        # further below) -- discharges/flagged for the SAME review must now be ABSENT on BOTH
        # producers, and obliged(author) must be ABSENT from the ASP EDB entirely.
        with _EnvTarget(world):
            post_floor = review_gap_floor.floor_atoms(world)
            post_asp = review_gap_edb.export(world)
        check("wa1-post-revoke-discharges-absent",
              f"discharges({r_id},{v_row['row_id']})" not in post_floor,
              f"floor atoms={sorted(post_floor)}", failures)
        check("wa1-post-revoke-flagged-absent", f"flagged({r_id})" not in post_floor,
              f"floor atoms={sorted(post_floor)}", failures)
        check("wa1-post-revoke-asp-obliged-fact-absent",
              f"obliged({int(author_id)})." not in post_asp.facts,
              f"asp facts={post_asp.facts}", failures)
        diff_post = run_differential(world)
        check("wa1-post-revoke-differential-green",
              diff_post.returncode == 0 and "DIFFERENTIAL GREEN" in diff_post.stdout,
              f"stdout_tail={diff_post.stdout[-1500:]}", failures)

        # ==================== WA3: un-revoked obligation is UNAFFECTED ====================
        print("== WA3: a second, un-revoked obligation stays in review_gap ==")
        v_ob2 = kernel_write(world, "obligation_write",
                              {"scope": "wa3-scope-unrevoked", "assigned_by": int(reviewer_id),
                               "obliges_actor": int(author_id)})
        check("wa3-obligate-accepted", v_ob2["disposition"] == "accepted", f"{v_ob2}", failures)
        v_row3 = kernel_write(world, "ledger_write",
                               {"kind": "finding", "statement": "WA3 fixture row, obligation never revoked",
                                "actor": int(author_id)})
        check("wa3-candidate-row-accepted", v_row3["disposition"] == "accepted", f"{v_row3}", failures)
        gap3 = sql1(world, f"SET ROLE {world}_rw; SET search_path={world},{world}_kernel; "
                           f"SELECT count(*) FROM review_gap WHERE id = {v_row3['row_id']} "
                           f"AND scope = 'wa3-scope-unrevoked';")
        check("wa3-unrevoked-still-in-gap", gap3 == "1", f"count={gap3}", failures)

        # ==================== WA4: revoking an unknown scope refuses ====================
        print("== WA4: revoking an unknown scope -> refused ==")
        v_wa4 = kernel_write(world, "obligation_revoke",
                              {"scope": "no-such-scope-ever", "reason": "WA4 probe"})
        check("wa4-refused", v_wa4["disposition"] == "refused", f"{v_wa4}", failures)
        check("wa4-message-names-unknown-scope",
              "no-such-scope-ever" in (v_wa4.get("message") or ""), f"message={v_wa4.get('message')!r}",
              failures)

        # ==================== WA5: revoking an already-revoked scope refuses (duplicate) ========
        print("== WA5: revoking wa1-scope a SECOND time -> refused (duplicate) ==")
        v_wa5 = kernel_write(world, "obligation_revoke",
                              {"scope": "wa1-scope", "reason": "WA5 duplicate probe"})
        check("wa5-refused", v_wa5["disposition"] == "refused", f"{v_wa5}", failures)
        check("wa5-message-names-already-revoked",
              "ALREADY" in (v_wa5.get("message") or "") or "already" in (v_wa5.get("message") or ""),
              f"message={v_wa5.get('message')!r}", failures)
        event_count = sql1(world, f"SET ROLE {world}_rw; SET search_path={world},{world}_kernel; "
                                  f"SELECT count(*) FROM ledger WHERE kind='obligation_revoked' "
                                  f"AND obligation_revoked_scope='wa1-scope';")
        check("wa5-still-only-one-revocation-event", event_count == "1", f"count={event_count}", failures)

        # ==================== WA7a: differential AGREE, revoked state ====================
        print("== WA7a: SQL/ASP differential AGREE on the post-revocation state ==")
        diff_cp = run_differential(world)
        check("wa7a-differential-exit0", diff_cp.returncode == 0,
              f"exit={diff_cp.returncode}\nstdout_tail={diff_cp.stdout[-2000:]}\nstderr_tail={diff_cp.stderr[-1000:]}",
              failures)
        check("wa7a-differential-green", "DIFFERENTIAL GREEN" in diff_cp.stdout,
              f"stdout_tail={diff_cp.stdout[-2000:]}", failures)

        # ==================== WA7b: differential AGREE, a SEPARATE never-revoked-anything world ===
        print("== WA7b: SQL/ASP differential AGREE on a world that never revokes anything (s56-headed) ==")
        world_norevoke = "s57fxnorv"
        apply_chain(world_norevoke, CHAIN_S56)
        author2, reviewer2 = birth(world_norevoke)
        kernel_write(world_norevoke, "obligation_write",
                     {"scope": "unrevoked-only", "assigned_by": int(reviewer2),
                      "obliges_actor": int(author2)})
        kernel_write(world_norevoke, "ledger_write",
                     {"kind": "finding", "statement": "WA7b fixture row", "actor": int(author2)})
        diff_cp_norv = run_differential(world_norevoke)
        check("wa7b-differential-exit0", diff_cp_norv.returncode == 0,
              f"exit={diff_cp_norv.returncode}\nstdout_tail={diff_cp_norv.stdout[-2000:]}", failures)
        check("wa7b-differential-green", "DIFFERENTIAL GREEN" in diff_cp_norv.stdout,
              f"stdout_tail={diff_cp_norv.stdout[-2000:]}", failures)
        teardown(world_norevoke)

    finally:
        teardown("s57fx")
        teardown("s57fxnorv")

    if failures:
        print(f"FAIL: {len(failures)} case(s): {failures}")
        return 1
    print("all s57-obligation-revocation-event cases WITNESSED clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
