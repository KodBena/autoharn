#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity witness for design/FABLE-BELIEF-SUBSTRATE-SPEC.md's v1
belief substrate (§2, §7.1's witness plan; ratified ledger rows 1914/1919). Real infra, no
mocks: CLASSIC scaffolds + `led decision`-written v1 belief rows in the TOY db (the exact
pattern seen-red/defeat-pipeline/run_fixtures.py already banks), torn down before and after.
Never touches kernel/, bootstrap/, or any live world -- scratch schema pairs only.

WORLDS:
  WORLD BS   -- chain to today's head (s52): the main positive witness -- one legal row per
                polarity/basis cell, contest resolution (tied and evidence-class-resolved),
                concurrence/corroboration (cross-class and same-class), a five-belief shared-
                ancestor chain, and the full `./judge --layer belief` differential in AGREE.
  WORLD MAL-<n> -- chain to s52, used ONCE each: one malformation class per world (a malformed
                v1 belief statement poisons every LATER belief-layer read on the SAME target --
                export_belief()'s candidate query reads every row regardless of supersession,
                the exact defeat-pipeline precedent -- so each malformation is isolated on its
                own throwaway world, never mixed into WORLD BS's other checks).
W-REG (registry negative control) and W-NEG (the ADR-0011 Rule 3 negative control: a
deliberately broken ASP twin proving the differential goes RED) need NO fresh database world --
pure clingo / pure Python against this repo's engine/ modules and a small scratch EDB.

Usage: python3 seen-red/belief-substrate-v1/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import hashlib
import importlib.util
import json
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
ENGINE = REPO / "engine"
LED_TMPL = REPO / "bootstrap" / "templates" / "led.tmpl"
PYVENV = Path.home() / "w" / "vdc" / "venvs" / "generic" / "bin" / "python"
sys.path.insert(0, str(ENGINE))
sys.path.insert(0, str(REPO / "filing"))
sys.path.insert(0, str(REPO / "serving"))

import ledger_differential  # noqa: E402
import ledger_edb  # noqa: E402
import lp_registry  # noqa: E402
import pghost_resolve  # noqa: E402
import deployment_record  # noqa: E402

# legacy-led-retirement inventory pass (ledger row 1149), part 2(b): reuses seen-red/
# boundary-service/run_fixtures.py's own scratch-server-standing helpers (ADR-0012 P1) rather
# than re-deriving them, the SAME reuse seen-red/reservation-residue/run_fixtures.py's own
# migration this same pass uses.
_BS_SPEC = importlib.util.spec_from_file_location(
    "boundary_service_fixtures", REPO / "seen-red" / "boundary-service" / "run_fixtures.py")
assert _BS_SPEC is not None and _BS_SPEC.loader is not None
bs_fixtures = importlib.util.module_from_spec(_BS_SPEC)
sys.modules["boundary_service_fixtures"] = bs_fixtures
_BS_SPEC.loader.exec_module(bs_fixtures)

PGHOST, PGDB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

# CHAIN_HEAD is no longer a hand-maintained file list (see scaffold_classic()'s own docstring):
# `new-project.sh --new-world` applies TODAY's full lineage head itself.


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def teardown(world: str) -> None:
    # legacy-led-retirement inventory pass (ledger row 1149): stop this world's own
    # boundary_service FIRST, if scaffold_classic ever stood one (it may not have, for a world
    # torn down pre-emptively before scaffolding -- `_SERVED.pop` with a default handles both).
    served = _SERVED.pop(world, None)
    if served is not None:
        bs_fixtures.stop_server(served[0])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {world} CASCADE; DROP SCHEMA IF EXISTS {world}_kernel CASCADE; "
        f"DROP OWNED BY {world}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {world}_rw;"])


# world name -> (Popen, served-deployment.json path) -- populated by scaffold_classic, consulted
# by led() below (legacy-led-retirement inventory pass, ledger row 1149, part 2(b): migrated off
# `legacy/led` onto the served path -- see reservation-residue's own sibling migration this same
# pass for the identical shape).
_SERVED: dict[str, tuple[subprocess.Popen, Path]] = {}


def led(world_dir: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    """Runs the served `bootstrap/templates/led.tmpl` against a REAL `serving.boundary_service`
    instance `scaffold_classic` now stands per world (`_SERVED` above) -- replaces the retired
    direct call to `world_dir/legacy/led`. Every verb this fixture calls (register-principal,
    decision writes with --supersedes) is on the served path's generic write surface."""
    world = world_dir.name
    _proc, dep_path = _SERVED[world]
    e = dict(os.environ)
    if env:
        e.update(env)
    e["AUTOHARN"] = str(REPO)
    e["PICKUP_DEPLOYMENT"] = str(dep_path)
    return sh([str(PYVENV), str(LED_TMPL), *args], cwd=str(world_dir), env=e)


def psql_tuples(sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"psql failed: {cp.stdout[-500:]} {cp.stderr[-500:]}")
    return cp.stdout.strip()


def scaffold_classic(world: str) -> Path:
    """Scaffold a fresh CLASSIC world at TODAY's full lineage head via `new-project.sh
    --new-world` -- which, as of s43, applies the ENTIRE kernel chain (through s52 on this
    repo's head) AND runs the s40/s43 birth sequence (author registration event, standing
    declaration, reviewer/commissioner/write-boundary ceremony) itself, routed through the
    write boundary. This build's first draft hand-applied a chain file list + a raw-INSERT
    birth_acts() (the seen-red/defeat-pipeline/run_fixtures.py precedent, written when that
    fixture's own head predated s43's write-boundary REVOKE) -- witnessed live failing here
    ("permission denied for table ledger": s43 revokes the granted role's direct INSERT
    everywhere, so a raw INSERT birth act is refused on any post-s43 world) and fixed by using
    --new-world's own current, complete scaffold instead of re-deriving a stale chain list."""
    tmp = Path(tempfile.mkdtemp(prefix=f"{world}-seenred-"))
    world_dir = tmp / world
    r = sh(["bash", str(NEW_PROJECT), str(world_dir), "--new-world", world,
            "--db", PGDB, "--host", PGHOST])
    if r.returncode != 0:
        raise RuntimeError(f"CLASSIC SCAFFOLD FAILED ({world}): {r.stdout[-2500:]} {r.stderr[-1500:]}")

    # legacy-led-retirement inventory pass (ledger row 1149): stand a REAL boundary_service
    # against this exact world (today's full lineage head always carries s43) and write a
    # served-shape deployment.json beside the classic one led() above resolves by world name.
    cfg_path = bs_fixtures.write_scratch_multiplex_config(tmp, world)
    proc, port = bs_fixtures.start_server(cfg_path)
    base = f"http://127.0.0.1:{port}/d/{world}"
    if not bs_fixtures.wait_health(base):
        tail = bs_fixtures.stop_server(proc)
        raise RuntimeError(f"boundary_service for {world} never became healthy: {tail[-1500:]}")
    served_dep = tmp / f"{world}-served-deployment.json"
    rec = deployment_record.DeploymentRecord(
        db=PGDB, host=PGHOST, schema=world, kern=f"{world}_kernel", role=f"{world}_rw",
        name=world, boundary_url=f"http://127.0.0.1:{port}", boundary_deployment=world)
    deployment_record.write_deployment(served_dep, rec)
    _SERVED[world] = (proc, served_dep)
    return world_dir


def row_id_last(world: str, kind: str, statement: str) -> int:
    out = psql_tuples(
        f"SELECT id FROM {world}.ledger WHERE kind='{kind}' AND statement = $stmt${statement}$stmt$ "
        f"ORDER BY id DESC LIMIT 1;")
    return int(out)


def set_target(name: str, schema: str, kern: str) -> None:
    os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"] = PGDB, schema, kern


def clear_target() -> None:
    for k in ("LEDGER_DB", "LEDGER_SCHEMA", "LEDGER_KERN"):
        os.environ.pop(k, None)


def run_belief(name: str):
    set_target(name, name, f"{name}_kernel")
    try:
        return ledger_differential.run_layer_differential(name, "belief")
    finally:
        clear_target()


def decide(wdir: Path, actor: str, stmt: str) -> int:
    r = led(wdir, "decision", stmt, env={"LED_ACTOR": actor})
    assert r.returncode == 0, f"led decision failed ({actor!r}): {r.stdout}{r.stderr}"
    world = wdir.name
    return row_id_last(world, "decision", stmt)


def world_bs(failures: list[str], tmps: list[Path]) -> None:
    world = "bsv1w"
    teardown(world)
    print(f"== scaffolding classic world {world} (new-project.sh --new-world, today's full head) ==")
    wdir = scaffold_classic(world)
    tmps.append(wdir.parent)

    for name, cls in (("toolbot", "tool"), ("toolbot2", "tool"),
                     ("modelbot2", "model"), ("personx", "human")):
        r = led(wdir, "register-principal", name, cls, "--purpose", f"belief-substrate-v1 fixture ({cls})",
                env={"LED_ACTOR": "author"})
        assert r.returncode == 0, r.stdout + r.stderr

    d0 = decide(wdir, "author", "D0: an ordinary non-belief ledger row (the grounding base case)")

    # ---- one legal row per polarity x basis cell (all 8 -- see build report's ambiguity note
    # on the spec's "6 legal cells; 2 illegal" wording, which this build could not resolve from
    # the text alone and so tests the full cross product instead) --------------------------
    row_a = decide(wdir, "author",
                   f"belief[universal] basis=observed universe={{all rows as of this write}} "
                   f":: A: universal-observed, grounded by its own universe")
    row_b = decide(wdir, "author",
                   f"belief[universal] basis=derived universe={{derived from row A}} premises=row:{row_a} "
                   f":: B: universal-derived, resting on A")
    row_c = decide(wdir, "author",
                   f"belief[universal] basis=testimony universe={{relayed from D0}} source=row:{d0} "
                   f":: C: universal-testimony, relaying D0")
    row_d = decide(wdir, "author",
                   f"belief[universal] basis=assumed universe={{an assumed scope}} "
                   f":: D: universal-assumed, never credited")
    row_e = decide(wdir, "author",
                   f"belief[existential] basis=observed witness=row:{d0} "
                   f":: E: existential-observed, witnessed by D0")
    row_f = decide(wdir, "author",
                   f"belief[existential] basis=derived premises=row:{d0} "
                   f":: F: existential-derived, resting on D0")
    row_g = decide(wdir, "author",
                   f"belief[existential] basis=testimony source=row:{d0} "
                   f":: G: existential-testimony, relaying D0")
    row_h = decide(wdir, "author",
                   f"belief[existential] basis=assumed "
                   f":: H: existential-assumed, never credited")

    res = run_belief(world)
    credited = {a for a in res.asp.atoms if a.startswith("credited_belief(")}
    check("BS-cell-matrix-all-eight-parse-AGREE",
          res.verdict() == "AGREE",
          f"verdict={res.verdict()}; only_asp={sorted(res.only_asp)}; only_sql={sorted(res.only_sql)}",
          failures)
    for label, rid, expect_credited in (
            ("A-universal-observed", row_a, True), ("B-universal-derived", row_b, True),
            ("C-universal-testimony", row_c, True), ("D-universal-assumed", row_d, False),
            ("E-existential-observed", row_e, True), ("F-existential-derived", row_f, True),
            ("G-existential-testimony", row_g, True), ("H-existential-assumed", row_h, False)):
        is_credited = f"credited_belief({rid})" in credited
        check(f"BS-{label}-credited={expect_credited}",
              is_credited == expect_credited,
              f"row {rid}: credited_belief present={is_credited}, expected={expect_credited}",
              failures)

    # ---- contest, evidence-class-resolved (observed beats testimony) -----------------------
    row_i = decide(wdir, "author", f"belief[existential] basis=observed witness=row:{d0} :: I: contested, observed")
    row_j = decide(wdir, "toolbot",
                   f"belief[existential] basis=testimony source=row:{d0} contests=row:{row_i} "
                   f":: J: contests I with a weaker (testimony) basis")
    res = run_belief(world)
    contested = {a for a in res.asp.atoms if a.startswith("contested_belief(")}
    resolved = {a for a in res.asp.atoms if a.startswith("contest_resolved(")}
    credited = {a for a in res.asp.atoms if a.startswith("credited_belief(")}
    check("BS-contest-resolved-observed-beats-testimony",
          res.verdict() == "AGREE"
          and f"contested_belief({row_j},{row_i})" in contested
          and f"contest_resolved({row_i},{row_j})" in resolved
          and f"credited_belief({row_i})" in credited
          and f"credited_belief({row_j})" not in credited,
          f"verdict={res.verdict()}; contested={sorted(contested)}; resolved={sorted(resolved)}; "
          f"I credited={f'credited_belief({row_i})' in credited}; "
          f"J credited={f'credited_belief({row_j})' in credited}",
          failures)

    # ---- contest, TIED basis -- both sides demoted to doubt, neither credited --------------
    row_l = decide(wdir, "author", f"belief[existential] basis=observed witness=row:{d0} :: L: tied contest side 1")
    row_m = decide(wdir, "toolbot",
                   f"belief[existential] basis=observed witness=row:{d0} contests=row:{row_l} "
                   f":: M: contests L with the SAME (observed) basis -- a tie")
    res = run_belief(world)
    resolved = {a for a in res.asp.atoms if a.startswith("contest_resolved(")}
    credited = {a for a in res.asp.atoms if a.startswith("credited_belief(")}
    check("BS-contest-tie-both-demoted",
          res.verdict() == "AGREE"
          and not any(a.startswith(f"contest_resolved({row_l},") or a.startswith(f"contest_resolved({row_m},")
                     for a in resolved)
          and f"credited_belief({row_l})" not in credited
          and f"credited_belief({row_m})" not in credited,
          f"verdict={res.verdict()}; resolved={sorted(resolved)}; "
          f"L credited={f'credited_belief({row_l})' in credited}; "
          f"M credited={f'credited_belief({row_m})' in credited}",
          failures)

    # ---- concurrence / corroboration: cross-class (3 holders, 2 classes) -------------------
    row_n = decide(wdir, "author", f"belief[existential] basis=observed witness=row:{d0} :: N: corroborated cross-class")
    row_o = decide(wdir, "modelbot2",
                   f"belief[existential] basis=observed witness=row:{d0} concurs=row:{row_n} "
                   f":: O: concurs with N (same class as N -- model)")
    row_p = decide(wdir, "toolbot",
                   f"belief[existential] basis=observed witness=row:{d0} concurs=row:{row_n} "
                   f":: P: concurs with N (different class -- tool)")
    res = run_belief(world)
    grade = {a for a in res.asp.atoms if a.startswith("corroboration_grade(")}
    check("BS-corroboration-cross-class",
          res.verdict() == "AGREE"
          and f'corroboration_grade({row_n},"corroborated-cross-class")' in grade,
          f"verdict={res.verdict()}; grade atoms for N={sorted(a for a in grade if a.startswith(f'corroboration_grade({row_n},'))}",
          failures)

    # ---- concurrence / corroboration: same-class pair, never higher ------------------------
    row_q = decide(wdir, "toolbot", f"belief[existential] basis=observed witness=row:{d0} :: Q: corroborated same-class")
    row_r = decide(wdir, "toolbot2",
                   f"belief[existential] basis=observed witness=row:{d0} concurs=row:{row_q} "
                   f":: R: concurs with Q (same class -- tool)")
    res = run_belief(world)
    grade = {a for a in res.asp.atoms if a.startswith("corroboration_grade(")}
    check("BS-corroboration-same-class-never-higher",
          res.verdict() == "AGREE"
          and f'corroboration_grade({row_q},"corroborated-same-class")' in grade
          and f'corroboration_grade({row_q},"corroborated-cross-class")' not in grade,
          f"verdict={res.verdict()}; grade atoms for Q={sorted(a for a in grade if a.startswith(f'corroboration_grade({row_q},'))}",
          failures)

    # ---- five-belief derivation chain sharing one ancestor (D0) -- shared_ancestor non-empty
    s1a = decide(wdir, "author", f"belief[existential] basis=derived premises=row:{d0} :: S1a: chain-1 depth1")
    s1b = decide(wdir, "author", f"belief[existential] basis=derived premises=row:{s1a} :: S1b: chain-1 depth2")
    s1c = decide(wdir, "author", f"belief[existential] basis=derived premises=row:{s1b} :: S1c: chain-1 depth3")
    s2a = decide(wdir, "toolbot", f"belief[existential] basis=derived premises=row:{d0} :: S2a: chain-2 depth1")
    s2b = decide(wdir, "toolbot",
                f"belief[existential] basis=derived premises=row:{s2a} concurs=row:{s1c} "
                f":: S2b: chain-2 depth2, concurs with S1c")
    res = run_belief(world)
    shared = {a for a in res.asp.atoms if a.startswith("shared_ancestor(")}
    lo, hi = sorted((s1c, s2b))
    check("BS-five-belief-shared-ancestor-non-empty",
          res.verdict() == "AGREE" and f"shared_ancestor({lo},{hi},{d0})" in shared,
          f"verdict={res.verdict()}; shared_ancestor atoms={sorted(shared)}",
          failures)

    # ---- the full differential, one more time, over the WHOLE accumulated world -------------
    check("BS-full-differential-AGREE",
          res.verdict() == "AGREE",
          f"verdict={res.verdict()}; asp={len(res.asp.atoms)} sql={len(res.sql.atoms)} atoms; "
          f"only_asp={sorted(res.only_asp)}; only_sql={sorted(res.only_sql)}",
          failures)

    teardown(world)


def _malformed_world(label: str, failures: list[str], tmps: list[Path],
                     build_and_check) -> None:
    world = "bsm" + hashlib.sha256(label.encode()).hexdigest()[:5]
    teardown(world)
    print(f"== scaffolding classic world {world} for malformation class {label!r} ==")
    wdir = scaffold_classic(world)
    tmps.append(wdir.parent)
    r = led(wdir, "register-principal", "toolbot", "tool", "--purpose", "belief-substrate-v1 malformed fixture",
            env={"LED_ACTOR": "author"})
    assert r.returncode == 0, r.stdout + r.stderr
    build_and_check(wdir, world, failures)
    teardown(world)


def malformed_universal_missing_universe(failures, tmps):
    def build(wdir, world, failures):
        decide(wdir, "author", "belief[universal] basis=observed :: missing universe on universal")
        res = run_belief(world)
        check("MAL-universal-missing-universe",
              res.verdict() == ledger_differential.QUARANTINED
              and res.asp.quarantine is not None and res.sql.quarantine is not None,
              f"verdict={res.verdict()}; asp.q={res.asp.quarantine!r}; sql.q={res.sql.quarantine!r}",
              failures)
    _malformed_world("universal-missing-universe", failures, tmps, build)


def malformed_existential_observed_missing_witness(failures, tmps):
    def build(wdir, world, failures):
        decide(wdir, "author", "belief[existential] basis=observed :: missing witness on observed existential")
        res = run_belief(world)
        check("MAL-existential-observed-missing-witness",
              res.verdict() == ledger_differential.QUARANTINED
              and res.asp.quarantine is not None and res.sql.quarantine is not None,
              f"verdict={res.verdict()}; asp.q={res.asp.quarantine!r}; sql.q={res.sql.quarantine!r}",
              failures)
    _malformed_world("existential-observed-missing-witness", failures, tmps, build)


def malformed_testimony_missing_source(failures, tmps):
    def build(wdir, world, failures):
        decide(wdir, "author", "belief[existential] basis=testimony :: missing source on testimony")
        res = run_belief(world)
        check("MAL-testimony-missing-source",
              res.verdict() == ledger_differential.QUARANTINED
              and res.asp.quarantine is not None and res.sql.quarantine is not None,
              f"verdict={res.verdict()}; asp.q={res.asp.quarantine!r}; sql.q={res.sql.quarantine!r}",
              failures)
    _malformed_world("testimony-missing-source", failures, tmps, build)


def malformed_derived_missing_premises(failures, tmps):
    def build(wdir, world, failures):
        decide(wdir, "author", "belief[existential] basis=derived :: missing premises on derived")
        res = run_belief(world)
        check("MAL-derived-missing-premises",
              res.verdict() == ledger_differential.QUARANTINED
              and res.asp.quarantine is not None and res.sql.quarantine is not None,
              f"verdict={res.verdict()}; asp.q={res.asp.quarantine!r}; sql.q={res.sql.quarantine!r}",
              failures)
    _malformed_world("derived-missing-premises", failures, tmps, build)


def malformed_dangling_row_token(failures, tmps):
    def build(wdir, world, failures):
        decide(wdir, "author",
              "belief[existential] basis=observed witness=row:999999999 :: dangling witness token")
        res = run_belief(world)
        check("MAL-dangling-row-token",
              res.verdict() == ledger_differential.QUARANTINED
              and res.asp.quarantine is not None and res.sql.quarantine is not None,
              f"verdict={res.verdict()}; asp.q={res.asp.quarantine!r}; sql.q={res.sql.quarantine!r}",
              failures)
    _malformed_world("dangling-row-token", failures, tmps, build)


def malformed_self_contest(failures, tmps):
    def build(wdir, world, failures):
        d0 = decide(wdir, "author", "D0 (self-contest fixture)")
        z = decide(wdir, "author", f"belief[existential] basis=observed witness=row:{d0} :: Z: self-contest target")
        decide(wdir, "author", f"belief[existential] basis=observed witness=row:{d0} contests=row:{z} "
                              f":: W: same-actor contest against own belief Z")
        res = run_belief(world)
        check("MAL-self-contest",
              res.verdict() == ledger_differential.QUARANTINED
              and res.asp.quarantine is not None and res.sql.quarantine is not None,
              f"verdict={res.verdict()}; asp.q={res.asp.quarantine!r}; sql.q={res.sql.quarantine!r}",
              failures)
    _malformed_world("self-contest", failures, tmps, build)


def malformed_contest_of_superseded(failures, tmps):
    def build(wdir, world, failures):
        d0 = decide(wdir, "author", "D0 (contest-of-superseded fixture)")
        x = decide(wdir, "author", f"belief[existential] basis=observed witness=row:{d0} :: X: to be revised")
        r = led(wdir, "--supersedes", str(x), "decision",
               f"belief[existential] basis=observed witness=row:{d0} :: X2: author's revision of X",
               env={"LED_ACTOR": "author"})
        assert r.returncode == 0, r.stdout + r.stderr
        decide(wdir, "toolbot",
              f"belief[existential] basis=observed witness=row:{d0} contests=row:{x} "
              f":: Y: contests the now-superseded X (settled history)")
        res = run_belief(world)
        check("MAL-contest-of-superseded",
              res.verdict() == ledger_differential.QUARANTINED
              and res.asp.quarantine is not None and res.sql.quarantine is not None,
              f"verdict={res.verdict()}; asp.q={res.asp.quarantine!r}; sql.q={res.sql.quarantine!r}",
              failures)
    _malformed_world("contest-of-superseded", failures, tmps, build)


def w_reg_registry_red(failures: list[str]) -> None:
    """Negative control: grounding the 'belief' layer with ledger_defeat.lp omitted from the
    program list -> RegistryError BEFORE any clingo run (the F7 hazard lp_registry forecloses)."""
    raised = False
    detail = ""
    try:
        lp_registry.require_layer_stack(
            "belief", ["ledger_tnow.lp", "ledger_support.lp", "ledger_belief.lp"])
    except lp_registry.RegistryError as e:
        raised = True
        detail = str(e)
    check("W-REG-registry-red", raised, f"RegistryError raised: {detail[:200]}", failures)


def w_neg_broken_twin_diverges(failures: list[str]) -> None:
    """ADR-0011 Rule 3's negative control: a DELIBERATELY BROKEN ASP twin (this file's own
    broken_credited_negative_control.lp -- a copy of ledger_belief.lp with the assumed-basis
    exclusion REMOVED, so an assumed belief is wrongly credited) proves the differential goes
    RED against the correct SQL floor. Pure clingo/Python -- no database."""
    broken = HERE / "broken_credited_negative_control.lp"
    tnow, support, defeat = (ENGINE / "lp" / n for n in
                            ("ledger_tnow.lp", "ledger_support.lp", "ledger_defeat.lp"))
    edb = (
        'entry(1,0,decision,none,none,none).\n'
        'entry(2,0,decision,none,none,none).\n'
        'belief(2).\n'
        'belief_polarity(2,existential).\n'
        'belief_basis(2,assumed).\n'
    )
    edb_path = HERE / "_w_neg_scratch_edb.lp"
    edb_path.write_text(edb, encoding="utf-8")
    try:
        cp = subprocess.run(
            ["clingo", "--outf=2", "-n", "1", str(tnow), str(support), str(defeat), str(broken), str(edb_path)],
            capture_output=True, text=True)
        j = json.loads(cp.stdout)
        atoms = set(j.get("Call", [{}])[0].get("Witnesses", [{}])[0].get("Value", []))
        broken_asp_atoms = {a for a in atoms if a.split("(", 1)[0] in ledger_differential.BELIEF_PREDS}
        # The CORRECT reading (matching belief_floor.py / the real ledger_belief.lp): row 2 is
        # existential+assumed, NEVER credited. The broken twin wrongly credits it.
        correct_sql_atoms: set[str] = set()  # an assumed-only world credits nothing
        diverged = broken_asp_atoms != correct_sql_atoms
        check("W-NEG-broken-twin-diverges",
              diverged and "credited_belief(2)" in broken_asp_atoms,
              f"broken twin's atoms={sorted(broken_asp_atoms)} (expected to WRONGLY include "
              f"credited_belief(2)); correct reading={sorted(correct_sql_atoms)} -- the "
              f"differential this proves would read DIVERGE_DEFECT on a real target",
              failures)
    finally:
        edb_path.unlink(missing_ok=True)


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    try:
        w_reg_registry_red(failures)
        w_neg_broken_twin_diverges(failures)
        world_bs(failures, tmps)
        malformed_universal_missing_universe(failures, tmps)
        malformed_existential_observed_missing_witness(failures, tmps)
        malformed_testimony_missing_source(failures, tmps)
        malformed_derived_missing_premises(failures, tmps)
        malformed_dangling_row_token(failures, tmps)
        malformed_self_contest(failures, tmps)
        malformed_contest_of_superseded(failures, tmps)
    finally:
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print(f"FAILURES: {failures}")
        return 1
    print("ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
