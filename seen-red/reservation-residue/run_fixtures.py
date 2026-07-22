#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity witness for kernel/lineage/s56-reservation-residue.sql
(design/FABLE-RESERVATION-RESIDUE-SPEC.md, maintainer-ratified 2026-07-22). Real infra, no
mocks: CLASSIC-mode scaffolds (explicit --schema/--kern/--role, no automatic kernel apply --
s30/s31/.../s48's own scaffold_classic idiom) followed by a MANUAL lineage apply in the TOY db,
torn down before AND after so re-running leaves no residue.

WORLDS, deliberately two:
  WORLD PRE -- chain ends at s55 (s56 NOT applied). Reproduces the experience2-shaped defect
               LIVE, before s56 exists: a distinct-actor, deferred-close countersign carrying
               verdict=attest_with_reservations leaves work_review_gap non-empty -- the gate
               cannot tell "reviewed with a concern" from "never reviewed at all" (RED, the
               spec's own section 6(iii) "red first" instruction).
  WORLD S56  -- chain ends at s56. Every leg of the spec's section 6 witness plan:
    (ii)  a deferred close countersigned plain `attest` discharges -- unchanged behavior.
    (iii) a deferred close countersigned `attest_with_reservations` discharges AND appears on
          reservations_outstanding (the SAME act WORLD PRE just proved leaves the gap open).
    (iv)  `refuse` does not discharge and does not appear on the residue view.
    (v)   disposition leg (b): an `attest` review regarding the reservation review, written by a
          DIFFERENT actor, clears it from reservations_outstanding. A companion probe confirms
          the ORIGINAL reviewer cannot self-disposition via this SAME leg -- validate_review's
          standing self-review refusal (s21, untouched by s56) fires, a genuine tension with the
          spec's own prose ("by any actor including the original reviewer withdrawing their own
          concern") named explicitly in this fixture's own report, not silently patched around.
    (vi)  supersession leg (a): superseding the reservation-carrying review row likewise clears
          it from reservations_outstanding.
    (vii) review_verdicts returns the verdict for every case above, with the superseded flag
          correct on the one row this fixture supersedes.
  Both worlds also run a companion detect.sql check (positive on S56, negative on PRE) and, on
  WORLD S56 only, a `./judge --layer work` differential AGREE check (s56 ships no ASP-modeled
  predicate of its own; this is the honest "witnessed for agreement, not claimed closed by
  construction" leg the kernel file's own header names).

Usage: python3 seen-red/reservation-residue/run_fixtures.py
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
sys.path.insert(0, str(REPO / "filing"))
sys.path.insert(0, str(REPO / "engine"))
from pghost_resolve import resolve_pghost  # noqa: E402
import ledger_differential  # noqa: E402

PGHOST, PGDB = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_S55 = [
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
]
CHAIN_S56 = CHAIN_S55 + ["s56-reservation-residue.sql"]


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def teardown(world: str) -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {world} CASCADE; DROP SCHEMA IF EXISTS {world}_kernel CASCADE; "  # declared-drop: scratch reset
        f"DROP OWNED BY {world}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {world}_rw;"])


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


def kernel_write(world: str, fn: str, payload: dict, actor_name: str | None = None) -> dict:
    """SET ROLE + a direct call to the named SECURITY DEFINER boundary function (the s48/
    belief-substrate-v2 kernel_write precedent) -- used for the ONE act (case vi's generic
    kind='review' supersession row) `led`/`legacy/led` has no verb for."""
    p = dict(payload)
    if actor_name is not None:
        p["actor"] = principal_id(world, actor_name)
    pj = json.dumps(p)
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-v", f"payload={pj}"],
            input=f"SET ROLE {world}_rw;\nSET search_path = {world}, {world}_kernel;\n"
                  f"SELECT to_jsonb(v) FROM {world}_kernel.{fn}(:'payload'::jsonb) v;\n")
    if cp.returncode != 0:
        raise RuntimeError(f"kernel_write plumbing failed: {cp.stderr}")
    return json.loads(cp.stdout.strip())


def principal_id(world: str, name: str) -> int:
    return int(sql1(f"SELECT id FROM {world}_kernel.principal WHERE name = '{name}';"))


def birth(world: str, author_name: str) -> None:
    """The s40/s43 birth ceremony (s48's own precedent, adapted): registers `author_name` and
    the write-boundary's own recording identity, declares standing for the ACTUAL connecting
    login role (session_user -- s43 Element 8: set_actor resolves on session_user, unaffected
    by SET ROLE/SECURITY DEFINER, so standing binds the login the psql process authenticates
    as, exactly new-project.sh's own birth sequence -- `LOGIN_ROLE=$(psql ... 'SELECT
    session_user;')` -- NOT the granted `{world}_rw` role SET ROLE later switches into)."""
    script = f"""
SELECT session_user AS su \\gset login_
BEGIN;
INSERT INTO {world}_kernel.chain_genesis (seed)
  VALUES (encode(gen_random_bytes(32),'hex')) ON CONFLICT (only_one) DO NOTHING;
INSERT INTO {world}_kernel.stamp_secret (secret) VALUES (gen_random_bytes(32));
INSERT INTO {world}_kernel.principal (name, agent_class)
  VALUES ('{author_name}', 'model') RETURNING id \\gset author_
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_purpose)
  VALUES ('principal_registered','author (fixture)', :author_id, :author_id, 'fixture author');
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_db_role, principal_binding_active)
  VALUES ('principal_standing_declared','standing (fixture)', :author_id, :author_id, :'login_su', true);
COMMIT;
BEGIN;
-- s43 Element 6: the write-boundary's OWN recording identity.
INSERT INTO {world}_kernel.principal (name, agent_class)
  VALUES ('write-boundary', 'tool') RETURNING id \\gset wb_
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_purpose)
  VALUES ('principal_registered','write-boundary (fixture)', :author_id, :wb_id, 'the kernel write boundary''s own recording identity');
COMMIT;
"""
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1"], input=script)
    if cp.returncode != 0:
        raise RuntimeError(f"birth sequence failed: {cp.stdout}\n{cp.stderr}")


def legacy_led(world_dir: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    e = dict(os.environ)
    if env:
        e.update(env)
    return sh(["bash", str(world_dir / "legacy" / "led"), *args], cwd=str(world_dir), env=e)


def scaffold_classic(world: str, chain: list[str]) -> Path:
    """CLASSIC MODE (explicit --schema/--kern/--role, no automatic kernel apply) + a MANUAL
    apply of `chain` (the s30/s31/.../s48 scaffold_classic idiom) -- s56 is deliberately NOT
    wired into new-project.sh's LINEAGE_CHAIN by this build (the s34/s48 "do not wire
    LINEAGE_CHAIN" precedent for a delta not itself commissioned to land the chain wiring), so
    classic+manual is the honest wiring for both worlds this fixture builds."""
    tmp = Path(tempfile.mkdtemp(prefix=f"{world}-seenred-"))
    world_dir = tmp / world
    schema, kern, role = world, f"{world}_kernel", f"{world}_rw"
    teardown(world)
    r = sh(["bash", str(REPO / "bootstrap" / "new-project.sh"), str(world_dir),
            "--db", PGDB, "--host", PGHOST,
            "--schema", schema, "--kern", kern, "--role", role])
    if r.returncode != 0:
        raise RuntimeError(f"CLASSIC SCAFFOLD FAILED ({world}): {r.stdout[-2000:]} {r.stderr[-1500:]}")
    for verb_dir in (world_dir, world_dir / "legacy"):
        for verb in ("led", "judge", "pickup"):
            p = verb_dir / verb
            if p.exists():
                p.chmod(0o755)
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}"]
    for name in chain:
        args += ["-f", str(LINEAGE / name)]
    ra = sh(args)
    if ra.returncode != 0:
        raise RuntimeError(f"CLASSIC apply FAILED ({world}, chain ends {chain[-1]}): "
                           f"{ra.stdout[-2000:]} {ra.stderr[-2000:]}")
    birth(world, "author-fixture")
    return world_dir


def open_claim_close_deferred(world_dir: Path, world: str, slug: str, title: str) -> int:
    """Open, claim, close --review-deferred a work item as `author` -- returns the work_closed
    row's own ledger id (the review's `regards`)."""
    r = legacy_led(world_dir, "work", "open", slug, title)
    assert r.returncode == 0, f"work open {slug} failed: {r.stdout}{r.stderr}"
    r = legacy_led(world_dir, "work", "claim", slug)
    assert r.returncode == 0, f"work claim {slug} failed: {r.stdout}{r.stderr}"
    r = legacy_led(world_dir, "work", "close", slug, "dropped", "--review-deferred")
    assert r.returncode == 0, f"work close {slug} failed: {r.stdout}{r.stderr}"
    return int(sql1(f"SELECT id FROM {world}.ledger WHERE kind='work_closed' AND work_slug='{slug}' "
                    f"ORDER BY id DESC LIMIT 1;"))


def review(world_dir: Path, world: str, regards: int, verdict: str, actor_name: str,
          statement: str) -> tuple[int | None, subprocess.CompletedProcess[str]]:
    r = legacy_led(world_dir, "review", str(regards), verdict, "self-review", statement,
                   env={"LED_ACTOR": actor_name})
    row_id = None
    if r.returncode == 0:
        row_id = int(sql1(f"SELECT id FROM {world}.ledger WHERE kind='review' AND regards={regards} "
                          f"AND statement = '{statement}' ORDER BY id DESC LIMIT 1;"))
    return row_id, r


def review_gap_has(world: str, slug: str) -> bool:
    return sql1(f"SELECT count(*) FROM {world}.work_review_gap WHERE slug='{slug}';") != "0"


def in_reservations(world: str, review_id: int) -> bool:
    return sql1(f"SELECT count(*) FROM {world}.reservations_outstanding "
               f"WHERE review_id={review_id};") != "0"


def verdict_row(world: str, review_id: int) -> tuple[str, bool] | None:
    row = sql1(f"SELECT verdict, superseded FROM {world}.review_verdicts WHERE review_id={review_id};")
    if not row:
        return None
    parts = row.split("|")
    return parts[0], parts[1] == "t"


def old_floor_says_unresolved(world: str, slug: str) -> bool:
    """A hand-reconstruction of the PRE-§7 `work_review_floor_atoms`' `own_unresolved` leg
    (engine/ledger_floor.py, before this same commission's amendment) restricted to `slug`'s own
    close row: `discharged` gated on `verdict = 'attest'` ONLY, exactly the predicate this
    fixture's own s56-resv item's countersign (attest_with_reservations) can never satisfy. This
    is the RED-FIRST reconstruction (spec §7's "the exact case the two layers would have
    disagreed on") -- not a live revert of the real module (nothing on disk is mutated), a direct
    query of the same SQL shape the pre-amendment floor ran, byte-for-byte the same WHERE clause
    a `git show` of the pre-amendment `engine/ledger_floor.py` would print."""
    out = sql1(f"""
      SELECT NOT EXISTS (
        SELECT 1 FROM {world}.ledger c
        WHERE c.kind = 'work_closed' AND c.work_slug = '{slug}' AND c.work_review_disposition = 'deferred'
          AND EXISTS (
            SELECT 1 FROM {world}.ledger r JOIN {world}.review_detail rd ON rd.ledger_id = r.id
            WHERE r.kind = 'review' AND r.regards = c.id AND rd.verdict = 'attest' AND r.actor <> c.actor
              AND NOT EXISTS (SELECT 1 FROM {world}.ledger s2 WHERE s2.supersedes = r.id)
          )
      );""")
    return out == "t"


def engine_coherence_case(world: str, slug: str, failures: list[str]) -> None:
    """spec §7 amendment witness: the SQL/ASP `./judge --layer work` differential must AGREE on a
    reservation-discharged item -- 's56-resv' (case iii above), still cleanly discharged by its
    attest_with_reservations countersign, never disposed/superseded. RED-FIRST reconstruction
    first (the pre-amendment floor's own predicate, hand-run -- see old_floor_says_unresolved's
    own docstring for why this is a reconstruction, not a live revert), THEN the real, current
    (both files fixed) differential."""
    old_unresolved = old_floor_says_unresolved(world, slug)
    # in-process call (unlike judge_agree's subprocess) -- resolve() needs these set (the same
    # target-resolution env judge_agree sets for its own subprocess, engine/targets.py's home).
    os.environ["HARNESS_PGHOST"] = PGHOST
    os.environ["EPISTEMIC_PGHOST"] = PGHOST
    os.environ["LEDGER_DB"] = PGDB
    os.environ["LEDGER_SCHEMA"] = world
    os.environ["LEDGER_KERN"] = f"{world}_kernel"
    res = ledger_differential.run_layer_differential(world, layer="work")
    # atoms carry the clingo-quoted term (ledger_edb._atom/ledger_floor._wi_quote both quote a
    # hyphenated slug like this one) -- match that shape exactly, not a bare identifier.
    asp_atom_own = f'w_own_leaf_unresolved("{slug}")'
    asp_atom_tree = f'w_tree_unresolved("{slug}")'
    asp_says_resolved = (asp_atom_own not in res.asp.atoms) and (asp_atom_tree not in res.asp.atoms)
    check("engine-red-first-pre-amendment-floor-disagreed",
          old_unresolved and asp_says_resolved,
          f"pre-amendment floor reconstruction: own_unresolved({slug})={old_unresolved} "
          f"(expected True -- the stale, attest-only predicate this amendment fixes); "
          f"CURRENT (fixed) ASP output already resolves it: {asp_atom_own} in atoms="
          f"{asp_atom_own in res.asp.atoms}, {asp_atom_tree} in atoms="
          f"{asp_atom_tree in res.asp.atoms} (both expected False) -- the two would have "
          f"DISAGREED on this exact atom before engine/ledger_floor.py's own §7 fix landed "
          f"beside engine/ledger_edb.py's.", failures)
    check("engine-green-judge-work-layer-agree-on-reservation-item",
          res.verdict() == "AGREE"
          and asp_atom_own not in res.sql.atoms and asp_atom_tree not in res.sql.atoms,
          f"./judge --layer work verdict={res.verdict()} (expected AGREE); "
          f"{asp_atom_own} in SQL atoms={asp_atom_own in res.sql.atoms}, "
          f"{asp_atom_tree} in SQL atoms={asp_atom_tree in res.sql.atoms} (both expected False -- "
          f"the FIXED SQL floor, engine/ledger_floor.py::work_review_floor_atoms, now agrees "
          f"with the FIXED ASP-feeding EDB, engine/ledger_edb.py::export_work, on the SAME "
          f"reservation-discharged item)", failures)


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
             "print(r.verdict())\n"],
            env=env, cwd=str(REPO))
    if cp.returncode != 0:
        raise RuntimeError(f"judge programmatic call failed ({world}): {cp.stderr}")
    out = cp.stdout.strip().splitlines()
    check(label, bool(out) and out[0] == "AGREE", f"judge output ({world}): {out}", failures)


def main() -> int:
    failures: list[str] = []
    world_pre, world_s56 = "s56fx_pre", "s56fx_s56"
    try:
        # =========================================================================================
        # DETECT SIBLING, negative polarity (pre-s56); reproduce the defect LIVE.
        # =========================================================================================
        print(f"== scaffolding WORLD PRE (chain ends {CHAIN_S55[-1]}, s56 NOT applied) ==")
        world_dir_pre = scaffold_classic(world_pre, CHAIN_S55)
        d_pre = detect(world_pre, "s56-reservation-residue.detect.sql")
        check("detect-negative-pre-s56", d_pre == "f", f"detect.sql on WORLD PRE: {d_pre!r} (expected f)", failures)

        legacy_led(world_dir_pre, "register-principal", "closer", "model", "--purpose", "fixture closer",
                  env={"LED_ACTOR": "author-fixture"})
        legacy_led(world_dir_pre, "register-principal", "reviewer", "model", "--purpose", "fixture reviewer",
                  env={"LED_ACTOR": "author-fixture"})

        # --- red-first: reproduce the defect LIVE on a pre-s56 world (spec section 6(iii)) ------
        close_id = open_claim_close_deferred(world_dir_pre, world_pre, "pre-resv", "Pre-s56 reservation item")
        rid, rc = review(world_dir_pre, world_pre, close_id, "attest_with_reservations", "reviewer",
                         "concern noted, discharging with reservation (pre-s56 red-first probe)")
        gap_open_pre = review_gap_has(world_pre, "pre-resv")
        check("red-first-defect-reproduced", rc.returncode == 0 and gap_open_pre,
              f"pre-s56: review write exit={rc.returncode}, work_review_gap still lists "
              f"'pre-resv': {gap_open_pre} (expected True -- the defect this delta forecloses, "
              f"witnessed live BEFORE s56 exists, spec section 6's own 'red first' instruction)",
              failures)

        # =========================================================================================
        # WORLD S56 -- every leg of the spec's section 6 witness plan.
        # =========================================================================================
        print(f"== scaffolding WORLD S56 (chain ends {CHAIN_S56[-1]}) ==")
        world_dir = scaffold_classic(world_s56, CHAIN_S56)
        d_s56 = detect(world_s56, "s56-reservation-residue.detect.sql")
        check("detect-positive-s56", d_s56 == "t", f"detect.sql on WORLD S56: {d_s56!r} (expected t)", failures)

        legacy_led(world_dir, "register-principal", "closer", "model", "--purpose", "fixture closer",
                  env={"LED_ACTOR": "author-fixture"})
        legacy_led(world_dir, "register-principal", "reviewer", "model", "--purpose", "fixture reviewer",
                  env={"LED_ACTOR": "author-fixture"})
        legacy_led(world_dir, "register-principal", "reviewer3", "model", "--purpose", "fixture reviewer3",
                  env={"LED_ACTOR": "author-fixture"})

        # --- (ii) plain attest discharges, unchanged --------------------------------------------
        close_a = open_claim_close_deferred(world_dir, world_s56, "s56-plain", "Plain-attest item")
        rid_a, rc_a = review(world_dir, world_s56, close_a, "attest", "reviewer",
                            "clean countersign, no concerns (case ii)")
        gap_a = review_gap_has(world_s56, "s56-plain")
        vr_a = verdict_row(world_s56, rid_a)
        check("ii-plain-attest-discharges", rc_a.returncode == 0 and not gap_a and vr_a == ("attest", False),
              f"review exit={rc_a.returncode}, work_review_gap('s56-plain')={gap_a} (expected "
              f"False), review_verdicts row={vr_a} (expected ('attest', False))", failures)

        # --- (iii) attest_with_reservations discharges AND surfaces on reservations_outstanding -
        close_b = open_claim_close_deferred(world_dir, world_s56, "s56-resv", "Reservation item")
        rid_b, rc_b = review(world_dir, world_s56, close_b, "attest_with_reservations", "reviewer",
                            "concern: the retry path is untested (case iii)")
        gap_b = review_gap_has(world_s56, "s56-resv")
        resv_b = in_reservations(world_s56, rid_b)
        vr_b = verdict_row(world_s56, rid_b)
        check("iii-reservation-discharges-and-tracked",
              rc_b.returncode == 0 and not gap_b and resv_b and vr_b == ("attest_with_reservations", False),
              f"review exit={rc_b.returncode}, work_review_gap('s56-resv')={gap_b} (expected "
              f"False -- discharged), reservations_outstanding has review_id={rid_b}: {resv_b} "
              f"(expected True), review_verdicts row={vr_b} (expected "
              f"('attest_with_reservations', False)) -- the SAME act WORLD PRE just proved "
              f"leaves the gap open", failures)

        # --- (iv) refuse does not discharge and never appears on the residue view ---------------
        close_c = open_claim_close_deferred(world_dir, world_s56, "s56-refuse", "Refused item")
        rid_c, rc_c = review(world_dir, world_s56, close_c, "refuse", "reviewer",
                            "refused: does not meet criteria (case iv)")
        gap_c = review_gap_has(world_s56, "s56-refuse")
        resv_c = in_reservations(world_s56, rid_c)
        vr_c = verdict_row(world_s56, rid_c)
        check("iv-refuse-stays-open-and-untracked",
              rc_c.returncode == 0 and gap_c and not resv_c and vr_c == ("refuse", False),
              f"review exit={rc_c.returncode}, work_review_gap('s56-refuse')={gap_c} (expected "
              f"True -- refuse never discharges), reservations_outstanding has "
              f"review_id={rid_c}: {resv_c} (expected False), review_verdicts row={vr_c} "
              f"(expected ('refuse', False))", failures)

        # --- (v) disposition leg (b): a DIFFERENT actor's attest, regarding the reservation ----
        # review's own row, clears it.
        rid_d, rc_d = review(world_dir, world_s56, rid_b, "attest", "reviewer3",
                            "reservation dispositioned: retry path now covered (case v)")
        resv_b_after = in_reservations(world_s56, rid_b)
        check("v-disposition-by-different-actor-clears",
              rc_d.returncode == 0 and not resv_b_after,
              f"disposition review exit={rc_d.returncode}, reservations_outstanding still has "
              f"review_id={rid_b} after disposition: {resv_b_after} (expected False)", failures)

        # -- companion probe (named, not silently patched around): the spec's own prose says
        # disposition leg (b) is available "by any actor including the original reviewer
        # withdrawing their own concern" -- tested literally (reviewer self-dispositions their
        # OWN reservation review), this is REFUSED by validate_review's standing self-review
        # check (s21, untouched by s56: `target_actor = NEW.actor` when regards names a row the
        # SAME actor authored) -- a genuine tension between the spec's prose and the pre-existing
        # kernel refusal this delta correctly does not relax. The original reviewer's actual path
        # to self-withdrawal is leg (a), supersession (case vi below), not leg (b).
        _, rc_self = review(world_dir, world_s56, rid_c, "attest", "reviewer",
                            "self-disposition probe: should be REFUSED (self-review, s21)")
        check("v2-self-disposition-refused-by-standing-self-review-check",
              rc_self.returncode == 1,
              f"reviewer self-dispositioning a row they themselves authored: exit="
              f"{rc_self.returncode} (expected 1, REFUSED by validate_review's s21 self-review "
              f"check -- named tension with the spec's own 'including the original reviewer' "
              f"prose, not a bug in this delta)", failures)

        # --- (vi) supersession leg (a): superseding the reservation review clears it too --------
        close_d = open_claim_close_deferred(world_dir, world_s56, "s56-resv2", "Second reservation item")
        rid_e, rc_e = review(world_dir, world_s56, close_d, "attest_with_reservations", "reviewer",
                            "concern: needs a follow-up ticket (case vi)")
        resv_e_before = in_reservations(world_s56, rid_e)
        sup = kernel_write(world_s56, "ledger_write",
                           {"kind": "review", "regards": close_d, "supersedes": rid_e,
                            "statement": "retracting this reservation (case vi, leg a)"},
                           actor_name="reviewer")
        resv_e_after = in_reservations(world_s56, rid_e)
        vr_e = verdict_row(world_s56, rid_e)
        check("vi-supersession-clears-reservation",
              rc_e.returncode == 0 and resv_e_before and sup.get("disposition") == "accepted"
              and not resv_e_after and vr_e == ("attest_with_reservations", True),
              f"reservation review exit={rc_e.returncode}, in reservations_outstanding before "
              f"supersession: {resv_e_before} (expected True), supersession write verdict="
              f"{sup!r}, in reservations_outstanding after: {resv_e_after} (expected False), "
              f"review_verdicts row after={vr_e} (expected ('attest_with_reservations', True) "
              f"-- superseded flag correct)", failures)

        judge_agree(world_s56, failures, "vii-judge-work-layer-agree")

        # =====================================================================================
        # design/FABLE-RESERVATION-RESIDUE-SPEC.md §7 amendment: engine/ledger_floor.py's SQL
        # floor + engine/ledger_edb.py's ASP-feeding EDB extractor both carry the SAME widened
        # discharge predicate the kernel view does. Reuses close_b/s56-resv (case iii) -- still
        # cleanly discharged by its reservation countersign, never disposed or superseded.
        # =====================================================================================
        engine_coherence_case(world_s56, "s56-resv", failures)

    finally:
        teardown(world_pre)
        teardown(world_s56)

    if failures:
        print(f"FAILURES: {failures}")
        return 1
    print("ALL CASES PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
