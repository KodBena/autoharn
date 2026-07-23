#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for kernel/lineage/s33-composite-discharge.sql
(design/FABLE-COMPOSITE-DISCHARGE-SPEC.md, Fable-authored spec, RATIFIED 2026-07-15; ledger item
composite-parent-autodischarge, claimed by the orchestrator) + bootstrap/templates/led.tmpl's
`work open --discharge composite` flag + `hooks/stop_clean_exit.py`/`bootstrap/templates/
pickup.tmpl`'s effective_state read surfaces + gates/ledger_reader_allowlist.py (the standing
allowlist detect, re-scoped to s33's CHAIN) + the engine companion (work_review.lp's
w_composite/w_composite_with_children extension; engine/ledger_floor.py's matching
work_review_floor_atoms extension; engine/ledger_edb.py's export_work w_composite emission).

Real infra, no mocks: a `bootstrap/new-project.sh --new-world` scaffold in the TOY db, torn down
before AND after so re-running leaves no residue. cli-rebase-fixture-repairs (ledger row 1170):
this used to be a CLASSIC-mode scaffold + a manual s15..s33 apply (this commission's own original
instruction was "Do NOT wire LINEAGE_CHAIN" for s33) -- that instruction has since been
superseded (s33 IS wired into new-project.sh's LINEAGE_CHAIN now), and classic+manual was never
an isolated-delta requirement in this file (no before/after two-chain comparison exists here), so
it moved onto `--new-world` for the working s43 boundary the served `led` this fixture drives
throughout now unconditionally requires.

Cases (the ratified spec's sec-5 acceptance list, every polarity):
  a-zero-children-open              -- a composite with ZERO children never vacuously discharges;
                                        effective_state = open (spec sec-3's own named LIMIT).
  b-two-children-derive             -- open, one child closed; second closes ->
                                        discharged-by-obligations with NO further act, in the SAME
                                        read that shows the closes.
  c-stronger-leaf                   -- a child closed --review-deferred (undischarged) keeps the
                                        parent open even though the child's own `state` reads
                                        closed (the STRONGER leaf, witnessed not asserted); a
                                        DISTINCT-actor attest review lands -> parent derives
                                        discharged in the same read.
  d-hand-close-open-child-refused   -- a hand close of a composite with an open child is REFUSED
                                        via the s29 strict branch WITHOUT --strict ever being
                                        passed (strict-by-type witnessed), teach-text names the
                                        child.
  e-hand-close-after-resolution     -- once the tree resolves, a hand close is ACCEPTED; state and
                                        effective_state AGREE ('closed').
  f-nested-composites               -- a middle composite, itself resolved purely by derivation
                                        (no hand-close row of its own), discharges the grandparent
                                        too -- proving Element 3's read-conjunction extension (no
                                        second tree walker) actually composes.
  g-defeat-replay                   -- a discharged composite (via a distinct-actor attest that
                                        discharged a deferred child close); superseding that
                                        attest -> effective_state returns OPEN in the SAME read for
                                        BOTH the middle composite AND the grandparent (propagation
                                        witnessed, not asserted) -- this ALSO discharges s31's own
                                        UNEXERCISED composite-ancestor-reopen polarity (that
                                        fixture's own case a2), now exercised for the first time.
  h-defeat-past-hand-close          -- a hand-closed composite; the descendant leaf that resolved
                                        it is later defeated -> effective_state reads open,
                                        closed_but_tree_defeated is present in
                                        work_item_violations, the raw work_closed row stands as
                                        history.
  i-non-composite-byte-identity     -- for EVERY non-composite item in this whole fixture world,
                                        effective_state = state, byte-identical, unconditionally.
  j-allowlist-gate-both-polarities  -- gates/ledger_reader_allowlist.py (CHAIN extended to s33)
                                        exits 0 green on the real chain AND refuses a deliberately
                                        misfactored scratch view under --red.
  k-differential-agree              -- the STANDING `./judge --layer work` pipeline
                                        (engine/ledger_differential.run_layer_differential, the
                                        SAME code `./judge --layer work` runs) AGREEs on this whole
                                        world (SQL floor vs ASP, over ledger_edb's real export,
                                        composite fixtures included).

Usage: python3 seen-red/s33-composite-discharge/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
LINEAGE = REPO / "kernel" / "lineage"

# cli-rebase-fixture-repairs (ledger row 1170): REUSE (ADR-0012 P1) serve_existing_world from
# seen-red/boundary-service/run_fixtures.py -- the served `led` shim refuses every write until
# this deployment.json gains boundary_url/boundary_deployment.
_BS_SPEC = importlib.util.spec_from_file_location(
    "boundary_service_fixtures", REPO / "seen-red" / "boundary-service" / "run_fixtures.py")
assert _BS_SPEC is not None and _BS_SPEC.loader is not None
bs_fixtures = importlib.util.module_from_spec(_BS_SPEC)
sys.modules["boundary_service_fixtures"] = bs_fixtures
_BS_SPEC.loader.exec_module(bs_fixtures)
ENGINE = REPO / "engine"
GATE = REPO / "gates" / "ledger_reader_allowlist.py"
sys.path.insert(0, str(ENGINE))
sys.path.insert(0, str(REPO / "filing"))

import ledger_differential  # noqa: E402  (engine/ledger_differential.py -- run_layer_differential)
import ledger_floor  # noqa: E402  (engine/ledger_floor.py -- WORK_REVIEW_PREDS, for reporting only)
import pghost_resolve  # noqa: E402 (filing/pghost_resolve.py -- never a literal host default)

PGHOST, PGDB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"
WORLD = "s33fxprobe"

CHAIN = [
    "s15-schema.sql", "s17-stamp-mechanism.sql", "s17-independence-vocabulary.sql",
    "s19-trigger-search-path.sql", "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
    "s25-commission-kind.sql", "s26-row-hash-chain.sql", "s28-work-parent-edge.sql",
    "s29-obligation-item-key-and-typed-close.sql", "s30-typed-dependency-edges.sql",
    "s31-supersession-uniform-retraction.sql", "s32-edge-views-single-home.sql",
    "s33-composite-discharge.sql",
]


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def teardown() -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {WORLD} CASCADE; DROP SCHEMA IF EXISTS {WORLD}_kernel CASCADE; "  # declared-drop: s33fxprobe (declared scratch/test reset)
        f"DROP OWNED BY {WORLD}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {WORLD}_rw;"])


def led(world_dir: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    e = dict(os.environ)
    if env:
        e.update(env)
    return sh(["bash", str(world_dir / "led"), *args], cwd=str(world_dir), env=e)


def psql_tuples(sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"psql failed: {cp.stdout[-500:]} {cp.stderr[-500:]}")
    return cp.stdout.strip()


def scaffold_classic_s33(world: str) -> tuple[Path, subprocess.Popen]:
    """cli-rebase-fixture-repairs (ledger row 1170): moved off CLASSIC MODE + a manual s15..s33
    apply onto `--new-world`. This fixture's own docstring note ("s33 is deliberately NOT in
    new-project.sh's LINEAGE_CHAIN") is stale -- s33 has since been wired into that chain (no
    before/after two-chain comparison exists in this file; classic+manual was only ever a
    lighter-weight scaffold choice, same situation as s31's identical stale note) -- switched to
    `--new-world` for the working s43 boundary the served `led` this fixture drives now requires."""
    tmp = Path(tempfile.mkdtemp(prefix=f"{world}-seenred-"))
    world_dir = tmp / world
    r = sh(["bash", str(NEW_PROJECT), str(world_dir), "--new-world", world,
            "--db", PGDB, "--host", PGHOST])
    if r.returncode != 0:
        raise RuntimeError(f"SCAFFOLD FAILED ({world}): {r.stdout[-1500:]} {r.stderr[-1500:]}")
    for verb in ("led", "judge", "pickup"):
        p = world_dir / verb
        if p.exists():
            p.chmod(0o755)
    proc = bs_fixtures.serve_existing_world(world_dir / "deployment.json", tmp)
    return world_dir, proc


def eff_state(schema: str, slug: str) -> str:
    return psql_tuples(f"SELECT effective_state FROM {schema}.work_item_current WHERE slug='{slug}';")


def state_of(schema: str, slug: str) -> str:
    return psql_tuples(f"SELECT state FROM {schema}.work_item_current WHERE slug='{slug}';")


def row_id(schema: str, where: str) -> str:
    return psql_tuples(f"SELECT id FROM {schema}.ledger WHERE {where};")


def main() -> int:
    teardown()
    failures: list[str] = []
    tmps: list[Path] = []
    try:
        print(f"== scaffolding --new-world {WORLD} ==")
        world_dir, proc = scaffold_classic_s33(WORLD)
        tmps.append(world_dir.parent)
        schema = WORLD
        print(f"  scaffold OK (schema={schema}).\n")

        led(world_dir, "register-principal", "reviewer2", "model")

        # --- a: zero children never vacuously discharges ----------------------------------------
        led(world_dir, "work", "open", "a-root", "RootA", "--discharge", "composite")
        st_a = eff_state(schema, "a-root")
        ok_a = st_a == "open"
        check("a-zero-children-open", ok_a, f"effective_state(a-root)={st_a!r} (expected open)", failures)

        # --- b: two children, one then both closed -----------------------------------------------
        led(world_dir, "work", "open", "b-root", "RootB", "--discharge", "composite")
        led(world_dir, "work", "open", "b-c1", "ChildB1", "--parent", "b-root")
        led(world_dir, "work", "open", "b-c2", "ChildB2", "--parent", "b-root")
        st_b0 = eff_state(schema, "b-root")
        led(world_dir, "work", "claim", "b-c1")
        led(world_dir, "work", "close", "b-c1", "dropped", "--review-witness", "ref-b1")
        st_b1 = eff_state(schema, "b-root")
        led(world_dir, "work", "claim", "b-c2")
        led(world_dir, "work", "close", "b-c2", "dropped", "--review-witness", "ref-b2")
        st_b2 = eff_state(schema, "b-root")
        ok_b = st_b0 == "open" and st_b1 == "open" and st_b2 == "discharged-by-obligations"
        check("b-two-children-derive", ok_b,
              f"before={st_b0!r} one-closed={st_b1!r} both-closed={st_b2!r}", failures)

        # --- c: stronger leaf (review-deferred blocks; distinct-actor attest discharges) --------
        led(world_dir, "work", "open", "c-root", "RootC", "--discharge", "composite")
        led(world_dir, "work", "open", "c-c1", "ChildC1", "--parent", "c-root")
        led(world_dir, "work", "claim", "c-c1")
        led(world_dir, "work", "close", "c-c1", "dropped", "--review-deferred")
        st_c0 = eff_state(schema, "c-root")
        child_state_c0 = state_of(schema, "c-c1")
        close_c1 = row_id(schema, "kind='work_closed' AND work_slug='c-c1'")
        rc = led(world_dir, "review", close_c1, "attest", "self-review", "distinct-actor discharge for the fixture, no interception stamp available here",
                 env={"LED_ACTOR": "reviewer2"})
        st_c1 = eff_state(schema, "c-root")
        ok_c = (st_c0 == "open" and child_state_c0 == "closed" and rc.returncode == 0
                and st_c1 == "discharged-by-obligations")
        check("c-stronger-leaf", ok_c,
              f"before(child closed, deferred undischarged)={st_c0!r} child_state={child_state_c0!r} "
              f"review_exit={rc.returncode} after(distinct-actor attest)={st_c1!r}", failures)

        # --- d: hand close with an open child REFUSED, strict-by-type, no --strict passed --------
        led(world_dir, "work", "open", "d-root", "RootD", "--discharge", "composite")
        led(world_dir, "work", "open", "d-c1", "ChildD1", "--parent", "d-root")
        led(world_dir, "work", "claim", "d-root")
        rd = led(world_dir, "work", "close", "d-root", "dropped", "--review-witness", "ref-d")
        out_d = rd.stdout + rd.stderr
        ok_d = rd.returncode != 0 and "d-c1" in out_d and "obligation tree is unresolved" in out_d
        check("d-hand-close-open-child-refused", ok_d,
              f"exit={rd.returncode} names_child={('d-c1' in out_d)} "
              f"excerpt={out_d.strip()[-260:]!r}", failures)

        # --- e: hand close after resolution accepted, state/effective_state agree ----------------
        led(world_dir, "work", "open", "e-root", "RootE", "--discharge", "composite")
        led(world_dir, "work", "open", "e-c1", "ChildE1", "--parent", "e-root")
        led(world_dir, "work", "claim", "e-c1")
        led(world_dir, "work", "close", "e-c1", "dropped", "--review-witness", "ref-e1")
        led(world_dir, "work", "claim", "e-root")
        re_ = led(world_dir, "work", "close", "e-root", "shipped",
                  "--review-witness", "ref-e", "--witness", "commit-e")
        state_e, eff_e = state_of(schema, "e-root"), eff_state(schema, "e-root")
        ok_e = re_.returncode == 0 and state_e == "closed" and eff_e == "closed"
        check("e-hand-close-after-resolution", ok_e,
              f"close_exit={re_.returncode} state={state_e!r} effective_state={eff_e!r} (agree)", failures)

        # --- f: nested composites -- middle discharges purely by derivation, grandparent follows -
        led(world_dir, "work", "open", "f-gp", "GrandparentF", "--discharge", "composite")
        led(world_dir, "work", "open", "f-mid", "MiddleF", "--parent", "f-gp", "--discharge", "composite")
        led(world_dir, "work", "open", "f-leaf", "LeafF", "--parent", "f-mid")
        st_f0 = eff_state(schema, "f-gp")
        led(world_dir, "work", "claim", "f-leaf")
        led(world_dir, "work", "close", "f-leaf", "dropped", "--review-witness", "ref-f")
        st_fmid = eff_state(schema, "f-mid")
        st_fgp = eff_state(schema, "f-gp")
        mid_has_close = psql_tuples(
            f"SELECT EXISTS (SELECT 1 FROM {schema}.ledger WHERE kind='work_closed' AND work_slug='f-mid');")
        ok_f = (st_f0 == "open" and st_fmid == "discharged-by-obligations"
                and st_fgp == "discharged-by-obligations" and mid_has_close == "f")
        check("f-nested-composites", ok_f,
              f"before={st_f0!r} middle_after_leaf_closed={st_fmid!r} (no close row of its own: "
              f"{mid_has_close!r}) grandparent={st_fgp!r}", failures)

        # --- g: defeat replay -- supersede the discharging attest, BOTH ancestors re-open --------
        led(world_dir, "work", "open", "g-gp", "GrandparentG", "--discharge", "composite")
        led(world_dir, "work", "open", "g-mid", "MiddleG", "--parent", "g-gp", "--discharge", "composite")
        led(world_dir, "work", "open", "g-leaf", "LeafG", "--parent", "g-mid")
        led(world_dir, "work", "claim", "g-leaf")
        led(world_dir, "work", "close", "g-leaf", "dropped", "--review-deferred")
        close_g = row_id(schema, "kind='work_closed' AND work_slug='g-leaf'")
        led(world_dir, "review", close_g, "attest", "self-review", "distinct-actor discharge for the fixture, no interception stamp available here",
            env={"LED_ACTOR": "reviewer2"})
        review_g = row_id(schema, f"kind='review' AND regards={close_g}")
        st_gmid0, st_ggp0 = eff_state(schema, "g-mid"), eff_state(schema, "g-gp")
        rg = led(world_dir, "--supersedes", review_g, "revision", "retract the discharging attest")
        st_gmid1, st_ggp1 = eff_state(schema, "g-mid"), eff_state(schema, "g-gp")
        ok_g = (st_gmid0 == "discharged-by-obligations" and st_ggp0 == "discharged-by-obligations"
                and rg.returncode == 0 and st_gmid1 == "open" and st_ggp1 == "open")
        check("g-defeat-replay", ok_g,
              f"before_supersede middle={st_gmid0!r} grandparent={st_ggp0!r} "
              f"supersede_exit={rg.returncode} after middle={st_gmid1!r} grandparent={st_ggp1!r} -- "
              "this ALSO discharges s31's own UNEXERCISED composite-ancestor-reopen polarity "
              "(seen-red/s31-supersession-uniform-retraction/run_fixtures.py's case a2), now "
              "exercised for the first time.", failures)

        # --- h: defeat past a hand close -----------------------------------------------------------
        led(world_dir, "work", "open", "h-root", "RootH", "--discharge", "composite")
        led(world_dir, "work", "open", "h-c1", "ChildH1", "--parent", "h-root")
        led(world_dir, "work", "claim", "h-c1")
        led(world_dir, "work", "close", "h-c1", "dropped", "--review-deferred")
        close_h1 = row_id(schema, "kind='work_closed' AND work_slug='h-c1'")
        led(world_dir, "review", close_h1, "attest", "self-review", "distinct-actor discharge for the fixture, no interception stamp available here",
            env={"LED_ACTOR": "reviewer2"})
        review_h1 = row_id(schema, f"kind='review' AND regards={close_h1}")
        led(world_dir, "work", "claim", "h-root")
        led(world_dir, "work", "close", "h-root", "shipped", "--review-witness", "ref-h", "--witness", "commit-h")
        state_h0, eff_h0 = state_of(schema, "h-root"), eff_state(schema, "h-root")
        rh = led(world_dir, "--supersedes", review_h1, "revision", "retract h-c1's discharging attest")
        state_h1, eff_h1 = state_of(schema, "h-root"), eff_state(schema, "h-root")
        defeated_rows = psql_tuples(
            f"SELECT slug || '~' || detail FROM {schema}.work_item_violations "
            f"WHERE violation='closed_but_tree_defeated' ORDER BY slug;")
        ok_h = (state_h0 == "closed" and eff_h0 == "closed" and rh.returncode == 0
                and state_h1 == "closed" and eff_h1 == "open"
                and defeated_rows.startswith("h-root~"))
        check("h-defeat-past-hand-close", ok_h,
              f"before_supersede state={state_h0!r} effective_state={eff_h0!r} "
              f"supersede_exit={rh.returncode} after state(raw, unchanged)={state_h1!r} "
              f"effective_state={eff_h1!r} closed_but_tree_defeated={defeated_rows!r}", failures)

        # --- i: non-composite byte-identity across the whole fixture world -----------------------
        led(world_dir, "work", "open", "i-plain", "PlainI")
        mismatches = psql_tuples(
            f"SELECT w.slug || ':' || w.state || '/' || w.effective_state "
            f"FROM {schema}.work_item_current w "
            f"JOIN {schema}.ledger o ON o.kind='work_opened' AND o.work_slug=w.slug "
            f"WHERE o.work_discharge IS DISTINCT FROM 'composite' AND w.state <> w.effective_state;")
        n_plain = psql_tuples(
            f"SELECT count(*) FROM {schema}.ledger o "
            f"WHERE o.kind='work_opened' AND o.work_discharge IS DISTINCT FROM 'composite';")
        ok_i = mismatches == "" and int(n_plain) > 0
        check("i-non-composite-byte-identity", ok_i,
              f"non-composite items checked={n_plain} mismatches={mismatches!r} (empty = byte-identical)",
              failures)

        # --- j: allowlist gate, both polarities ---------------------------------------------------
        gg = sh([sys.executable, str(GATE)])
        gr = sh([sys.executable, str(GATE), "--red"])
        red_out = gr.stdout + gr.stderr
        ok_j = (gg.returncode == 0 and gr.returncode == 0
                and "REFUSED" in red_out and "FACTOR THROUGH THE IN-FORCE PROJECTION" in red_out
                and "CLAIM THE HISTORY ALLOWLIST" in red_out)
        check("j-allowlist-gate-both-polarities", ok_j,
              f"green_exit={gg.returncode} red_exit={gr.returncode} "
              f"teach_names_both_paths={'FACTOR THROUGH' in red_out and 'CLAIM THE HISTORY' in red_out}",
              failures)

        # --- k: STANDING ./judge --layer work differential AGREE, over the real export -----------
        os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"] = \
            PGDB, schema, f"{schema}_kernel"
        try:
            res = ledger_differential.run_layer_differential(schema, "work")
        finally:
            del os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"]
        verdict = res.verdict()
        ok_k = verdict == "AGREE"
        check("k-differential-agree", ok_k,
              f"verdict={verdict} asp_atoms={len(res.asp.atoms)} sql_atoms={len(res.sql.atoms)} "
              f"only_asp={sorted(res.asp.atoms - res.sql.atoms)[:8]} "
              f"only_sql={sorted(res.sql.atoms - res.asp.atoms)[:8]} -- "
              "engine/ledger_differential.run_layer_differential('work'), the SAME code "
              "`./judge --layer work` runs, over ledger_edb's real export (export()+export_work(), "
              "including w_composite) vs the SQL floor (work_item_floor_atoms|work_review_floor_atoms, "
              "restricted to WORK_LAYER_PREDS), on this whole world (nested composites, defeat "
              "replay, defeat-past-hand-close all present).", failures)

    finally:
        try:
            bs_fixtures.stop_server(proc)
        except NameError:
            pass  # scaffold itself failed before `proc` was ever assigned
        teardown()
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- s33 composite discharge both-polarity proof (zero-children never "
          "vacuous / two-children derive / stronger review leaf + distinct-actor discharge / "
          "hand-close-with-open-child strict-by-type refusal / hand-close-after-resolution "
          "agreement / nested composites / defeat replay across two ancestor levels (also "
          "exercising s31's own a2 UNEXERCISED polarity) / defeat past a hand close -> "
          "closed_but_tree_defeated / non-composite byte-identity / allowlist gate green+red / "
          "standing ./judge --layer work differential AGREE), zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
