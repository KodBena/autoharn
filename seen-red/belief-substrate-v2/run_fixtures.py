#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity witness for design/FABLE-BELIEF-SUBSTRATE-SPEC.md's v2
belief substrate (kernel deltas B1/B2/B3 = kernel/lineage/s53-belief-substrate.sql,
s54-belief-views.sql, s55-dispatch-grain-independence.sql; ratified ledger rows 1914/1919).
Real infra, no mocks: CLASSIC scaffolds via bootstrap/new-project.sh --new-world (which, as of
this build, carries s53/s54/s55 in its LINEAGE_CHAIN) + direct kernel.ledger_write(jsonb) calls
(the s51 kernel_write() plumbing precedent -- no `led belief` CLI verb exists this delta, named
in s53's own LIMITS), torn down before and after. Never touches kernel/, bootstrap/, or any live
world -- scratch schema pairs only.

MIGRATED off legacy/led onto the served path (closing-batch build, ledger rows 1176/1178, found
gap row 1175): this file's own `led()` helper used to exec `world_dir/legacy/led` directly --
now a one-line teaching-refusal stub (design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md), never a
working CLI -- which would refuse every register-principal/decision/grant-competence call below.
Migrated onto sibling belief-substrate-v1's own already-migrated precedent (this same closing
batch's sibling task): `scaffold_classic` now ALSO stands a real `serving.boundary_service`
instance per world (reusing seen-red/boundary-service/run_fixtures.py's scratch-server-standing
helpers, ADR-0012 P1) and writes a served-shape deployment.json; `led()` runs the served
`bootstrap/templates/led.tmpl` against it (`PICKUP_DEPLOYMENT` pointing at the served record)
instead of the retired stub. Red/green semantics preserved exactly -- only the write TRANSPORT
for the CLI-shaped calls (register-principal, decision, grant-competence) changed; the raw
`kernel_write()` calls for belief/review rows (the s51 plumbing precedent, unaffected by the
retirement -- there never was a `led belief` verb to retire) are untouched.

WORLDS:
  WORLD BV -- chain to today's head (s55): the main positive witness -- one legal typed row per
              polarity/basis cell, contest resolution (tied and evidence-class-resolved),
              concurrence/corroboration (cross-class and same-class), a derived chain composing
              model-identity defeat (s46), the full `./judge --layer belief` differential in
              AGREE on the TYPED arm, and the kernel view (credited_beliefs/contested_beliefs/
              corroboration/shared_premise) read directly and cross-checked against the engine
              differential's own atoms.
  WORLD NEG-<n> -- one CHECK/trigger refusal class per world (each a fresh throwaway world):
              malformed polarity/basis couplings, dangling witness/universe/premises tokens,
              self-contest, contest of superseded, cross-principal supersession attempt (refused
              in favor of a CONTEST), and the B3 independence-vocabulary widening (accepted +
              a sixth bogus value refused).

Usage: python3 seen-red/belief-substrate-v2/run_fixtures.py
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
ENGINE = REPO / "engine"
LED_TMPL = REPO / "bootstrap" / "templates" / "led.tmpl"
PYVENV = Path.home() / "w" / "vdc" / "venvs" / "generic" / "bin" / "python"
sys.path.insert(0, str(ENGINE))
sys.path.insert(0, str(REPO / "filing"))
sys.path.insert(0, str(REPO / "serving"))

import ledger_differential  # noqa: E402
import pghost_resolve  # noqa: E402
import deployment_record  # noqa: E402

# legacy-led-retirement migration (closing-batch build, ledger rows 1176/1178): reuses seen-red/
# boundary-service/run_fixtures.py's own scratch-server-standing helpers (ADR-0012 P1) rather
# than re-deriving them -- the SAME reuse belief-substrate-v1/run_fixtures.py's own sibling
# migration uses.
_BS_SPEC = importlib.util.spec_from_file_location(
    "boundary_service_fixtures", REPO / "seen-red" / "boundary-service" / "run_fixtures.py")
assert _BS_SPEC is not None and _BS_SPEC.loader is not None
bs_fixtures = importlib.util.module_from_spec(_BS_SPEC)
sys.modules["boundary_service_fixtures"] = bs_fixtures
_BS_SPEC.loader.exec_module(bs_fixtures)

PGHOST, PGDB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

# world name -> (Popen, served-deployment.json path) -- populated by scaffold_classic, consulted
# by led() below (same shape as belief-substrate-v1/run_fixtures.py's own _SERVED).
_SERVED: dict[str, tuple[subprocess.Popen, Path]] = {}


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def teardown(world: str) -> None:
    # stop this world's own boundary_service FIRST, if scaffold_classic ever stood one (it may
    # not have, for a world torn down pre-emptively before scaffolding -- `_SERVED.pop` with a
    # default handles both; belief-substrate-v1/run_fixtures.py's own teardown() precedent).
    served = _SERVED.pop(world, None)
    if served is not None:
        bs_fixtures.stop_server(served[0])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {world} CASCADE; DROP SCHEMA IF EXISTS {world}_kernel CASCADE; "
        f"DROP OWNED BY {world}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {world}_rw;"])


def led(world_dir: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    """Runs the served `bootstrap/templates/led.tmpl` against a REAL `serving.boundary_service`
    instance `scaffold_classic` now stands per world (`_SERVED` above) -- replaces the retired
    direct call to `world_dir/legacy/led` (legacy-led-retirement migration, ledger rows 1176/
    1178; belief-substrate-v1/run_fixtures.py's own `led()` precedent, identical shape)."""
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
    --new-world`, THEN stand a REAL `serving.boundary_service` against it and write a
    served-shape deployment.json beside the classic one `led()` above resolves by world name
    (legacy-led-retirement migration, ledger rows 1176/1178 -- belief-substrate-v1/
    run_fixtures.py's own `scaffold_classic()` precedent, identical shape)."""
    tmp = Path(tempfile.mkdtemp(prefix=f"{world}-seenred-"))
    world_dir = tmp / world
    r = sh(["bash", str(NEW_PROJECT), str(world_dir), "--new-world", world,
            "--db", PGDB, "--host", PGHOST])
    if r.returncode != 0:
        raise RuntimeError(f"CLASSIC SCAFFOLD FAILED ({world}): {r.stdout[-2500:]} {r.stderr[-1500:]}")

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


def kernel_write(world: str, fn: str, payload: dict) -> dict:
    """The s51 plumbing precedent (seen-red/s51-artifact-store/run_fixtures.py::kernel_write):
    SET ROLE to the world's granted role, call the named SECURITY DEFINER boundary function
    directly, return its typed write_verdict as a dict."""
    pj = json.dumps(payload)
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-v", f"payload={pj}"],
            input=f"SET ROLE {world}_rw;\nSET search_path = {world}, {world}_kernel;\n"
                  f"SELECT to_jsonb(v) FROM {world}_kernel.{fn}(:'payload'::jsonb) v;\n")
    if cp.returncode != 0:
        raise RuntimeError(f"kernel_write plumbing failed: {cp.stderr}")
    return json.loads(cp.stdout.strip())


def principal_id(world: str, name: str) -> int:
    return int(psql_tuples(f"SELECT id FROM {world}_kernel.principal WHERE name = '{name}';"))


def belief(world: str, actor: int, polarity: str, basis: str, proposition: str, **fields) -> int:
    payload: dict = {"kind": "belief", "actor": actor, "statement": proposition,
                     "belief_polarity": polarity, "belief_basis": basis}
    payload.update(fields)
    v = kernel_write(world, "ledger_write", payload)
    assert v["disposition"] == "accepted", f"expected accepted, got {v}"
    return int(v["row_id"])


def belief_refused(world: str, actor: int, polarity: str | None, basis: str | None,
                   proposition: str, **fields) -> dict:
    payload: dict = {"kind": "belief", "actor": actor, "statement": proposition}
    if polarity is not None:
        payload["belief_polarity"] = polarity
    if basis is not None:
        payload["belief_basis"] = basis
    payload.update(fields)
    return kernel_write(world, "ledger_write", payload)


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


def world_bv(failures: list[str], tmps: list[Path]) -> None:
    world = "bv2w"
    teardown(world)
    print(f"== scaffolding classic world {world} (new-project.sh --new-world, today's full head incl. s53/s54/s55) ==")
    wdir = scaffold_classic(world)
    tmps.append(wdir.parent)

    for name, cls in (("toolbot", "tool"), ("toolbot2", "tool"),
                     ("modelbot2", "model"), ("personx", "human")):
        r = led(wdir, "register-principal", name, cls, "--purpose", f"belief-substrate-v2 fixture ({cls})",
               env={"LED_ACTOR": "author"})
        assert r.returncode == 0, r.stdout + r.stderr

    author = principal_id(world, "author")
    toolbot = principal_id(world, "toolbot")
    toolbot2 = principal_id(world, "toolbot2")
    modelbot2 = principal_id(world, "modelbot2")

    # ---- confirm s53/s54/s55 actually landed on this scaffold (the load-bearing precondition
    # every check below assumes) ----------------------------------------------------------
    has_typed = psql_tuples(
        f"SELECT 1 FROM information_schema.columns WHERE table_schema='{world}' "
        f"AND table_name='ledger' AND column_name='belief_polarity';") == "1"
    check("BV-scaffold-carries-s53-typed-columns", has_typed,
          f"belief_polarity column present on {world}.ledger: {has_typed}", failures)

    # D0: a plain non-belief grounding row (exactly v1's D0 precedent).
    r = led(wdir, "decision", "D0: an ordinary non-belief ledger row (the grounding base case)",
           env={"LED_ACTOR": "author"})
    assert r.returncode == 0, r.stdout + r.stderr
    d0 = int(psql_tuples(
        f"SELECT id FROM {world}.ledger WHERE kind='decision' AND "
        f"statement = 'D0: an ordinary non-belief ledger row (the grounding base case)' "
        f"ORDER BY id DESC LIMIT 1;"))

    row_a = belief(world, author, "universal", "observed", "A: typed universal-observed",
                   belief_universe="all rows as of this write")
    row_b = belief(world, author, "universal", "derived", "B: typed universal-derived, resting on A",
                   belief_universe="derived from row A", belief_premises=[row_a])
    row_c = belief(world, author, "universal", "testimony", "C: typed universal-testimony, relaying D0",
                   belief_universe="relayed from D0", belief_source=d0)
    row_d = belief(world, author, "universal", "assumed", "D: typed universal-assumed, never credited",
                   belief_universe="an assumed scope")
    row_e = belief(world, author, "existential", "observed", "E: typed existential-observed, witnessed by D0",
                   belief_witness=f"row:{d0}")
    row_f = belief(world, author, "existential", "derived", "F: typed existential-derived, resting on D0",
                   belief_premises=[d0])
    row_g = belief(world, author, "existential", "testimony", "G: typed existential-testimony, relaying D0",
                   belief_source=d0)
    row_h = belief(world, author, "existential", "assumed", "H: typed existential-assumed, never credited")

    res = run_belief(world)
    check("BV-cell-matrix-all-eight-parse-AGREE", res.verdict() == "AGREE",
          f"verdict={res.verdict()}; only_asp={sorted(res.only_asp)}; only_sql={sorted(res.only_sql)}",
          failures)
    credited = {a for a in res.asp.atoms if a.startswith("credited_belief(")}
    for label, rid, expect in (("A", row_a, True), ("B", row_b, True), ("C", row_c, True),
                              ("D", row_d, False), ("E", row_e, True), ("F", row_f, True),
                              ("G", row_g, True), ("H", row_h, False)):
        is_credited = f"credited_belief({rid})" in credited
        check(f"BV-{label}-credited={expect}", is_credited == expect,
              f"row {rid}: credited_belief present={is_credited}, expected={expect}", failures)

    # cross-check the KERNEL VIEW (s54's credited_beliefs) against the engine differential's own
    # typed-arm reading -- both must agree on the SAME 8-row world (the closure statement's own
    # invariant, live).
    view_credited = {int(x) for x in psql_tuples(
        f"SELECT belief_id FROM {world}.credited_beliefs ORDER BY belief_id;").splitlines() if x}
    engine_credited_typed = {int(a[len("credited_belief("):-1]) for a in credited}
    check("BV-kernel-view-credited-beliefs-matches-engine",
          view_credited == engine_credited_typed,
          f"kernel view={sorted(view_credited)}; engine typed-arm={sorted(engine_credited_typed)}",
          failures)

    # ---- contest, evidence-class-resolved (observed beats testimony) -----------------------
    row_i = belief(world, author, "existential", "observed", "I: contested, observed", belief_witness=f"row:{d0}")
    row_j = belief(world, toolbot, "existential", "testimony", "J: contests I with a weaker (testimony) basis",
                   belief_source=d0, belief_contests=row_i)
    res = run_belief(world)
    contested = {a for a in res.asp.atoms if a.startswith("contested_belief(")}
    resolved = {a for a in res.asp.atoms if a.startswith("contest_resolved(")}
    credited = {a for a in res.asp.atoms if a.startswith("credited_belief(")}
    check("BV-contest-resolved-observed-beats-testimony",
          res.verdict() == "AGREE"
          and f"contested_belief({row_j},{row_i})" in contested
          and f"contest_resolved({row_i},{row_j})" in resolved
          and f"credited_belief({row_i})" in credited
          and f"credited_belief({row_j})" not in credited,
          f"verdict={res.verdict()}; contested={sorted(contested)}; resolved={sorted(resolved)}",
          failures)
    kernel_contested = psql_tuples(
        f"SELECT resolved_survivor FROM {world}.contested_beliefs "
        f"WHERE belief_id={row_j} AND contested_by={row_i};")
    check("BV-kernel-view-contested-beliefs-names-survivor",
          kernel_contested == str(row_i),
          f"contested_beliefs.resolved_survivor for (J,I) = {kernel_contested!r}, expected {row_i}",
          failures)

    # ---- concurrence / corroboration: cross-class ------------------------------------------
    row_n = belief(world, author, "existential", "observed", "N: corroborated cross-class", belief_witness=f"row:{d0}")
    belief(world, modelbot2, "existential", "observed", "O: concurs with N (same class as N -- model)",
          belief_witness=f"row:{d0}", belief_concurs=row_n)
    belief(world, toolbot, "existential", "observed", "P: concurs with N (different class -- tool)",
          belief_witness=f"row:{d0}", belief_concurs=row_n)
    res = run_belief(world)
    grade = {a for a in res.asp.atoms if a.startswith("corroboration_grade(")}
    check("BV-corroboration-cross-class",
          res.verdict() == "AGREE" and f'corroboration_grade({row_n},"corroborated-cross-class")' in grade,
          f"verdict={res.verdict()}; grade atoms for N={sorted(a for a in grade if a.startswith(f'corroboration_grade({row_n},'))}",
          failures)
    kernel_grade = psql_tuples(f"SELECT grade FROM {world}.corroboration WHERE belief_id={row_n};")
    check("BV-kernel-view-corroboration-matches-engine", kernel_grade == "corroborated-cross-class",
          f"corroboration.grade for N = {kernel_grade!r}", failures)

    # ---- same-class pair, never higher -------------------------------------------------------
    row_q = belief(world, toolbot, "existential", "observed", "Q: corroborated same-class", belief_witness=f"row:{d0}")
    belief(world, toolbot2, "existential", "observed", "R: concurs with Q (same class -- tool)",
          belief_witness=f"row:{d0}", belief_concurs=row_q)
    res = run_belief(world)
    grade = {a for a in res.asp.atoms if a.startswith("corroboration_grade(")}
    check("BV-corroboration-same-class-never-higher",
          res.verdict() == "AGREE"
          and f'corroboration_grade({row_q},"corroborated-same-class")' in grade
          and f'corroboration_grade({row_q},"corroborated-cross-class")' not in grade,
          f"grade atoms for Q={sorted(a for a in grade if a.startswith(f'corroboration_grade({row_q},'))}",
          failures)

    # ---- shared-premise chain sharing one ancestor -------------------------------------------
    s1a = belief(world, author, "existential", "derived", "S1a: chain-1 depth1", belief_premises=[d0])
    s1c = belief(world, author, "existential", "derived", "S1c: chain-1 depth2", belief_premises=[s1a])
    s2a = belief(world, toolbot, "existential", "derived", "S2a: chain-2 depth1", belief_premises=[d0])
    s2b = belief(world, toolbot, "existential", "derived", "S2b: chain-2 depth2, concurs with S1c",
                belief_premises=[s2a], belief_concurs=s1c)
    res = run_belief(world)
    shared = {a for a in res.asp.atoms if a.startswith("shared_ancestor(")}
    lo, hi = sorted((s1c, s2b))
    check("BV-shared-ancestor-non-empty",
          res.verdict() == "AGREE" and f"shared_ancestor({lo},{hi},{d0})" in shared,
          f"shared_ancestor atoms={sorted(shared)}", failures)
    kernel_shared = psql_tuples(
        f"SELECT shared_ancestor FROM {world}.shared_premise "
        f"WHERE belief_a={lo} AND belief_b={hi} AND shared_ancestor={d0};")
    check("BV-kernel-view-shared-premise-matches-engine", kernel_shared == str(d0),
          f"shared_premise row for ({lo},{hi},{d0}) = {kernel_shared!r}", failures)

    # ---- model-identity defeat composition: a mismatch attestation on a GROUNDING row
    # un-founds a belief resting on it, in BOTH the engine differential and the kernel view -----
    r = led(wdir, "register-principal", "attestbot", "tool", "--purpose", "defeat-composition fixture",
           env={"LED_ACTOR": "author"})
    assert r.returncode == 0, r.stdout + r.stderr
    r = led(wdir, "principal", "grant-competence", "attestbot", "--activity", "model-identity-attestation",
           "--band", "n/a", "--basis", "belief-substrate-v2 fixture", env={"LED_ACTOR": "author"})
    assert r.returncode == 0, r.stdout + r.stderr
    r = led(wdir, "decision", "K0: a row that will be attested mismatched", env={"LED_ACTOR": "author"})
    assert r.returncode == 0, r.stdout + r.stderr
    k0 = int(psql_tuples(
        f"SELECT id FROM {world}.ledger WHERE kind='decision' AND "
        f"statement='K0: a row that will be attested mismatched' ORDER BY id DESC LIMIT 1;"))
    # NAMED, per spec §3.4: basis=observed's well-foundedness reads ONLY belief_has_witness
    # (existence-checked at write time) -- it does NOT route through belief_grounded/defeat, by
    # the shipped v1 design (ledger_belief.lp's own rule has no model_defeated_row test on the
    # witness edge). Defeat composition propagates through PREMISE/SOURCE edges only (the
    # derived/testimony rules' belief_founded_node/belief_grounded chain) -- so this fixture
    # exercises the composition with a DERIVED-basis belief citing the defeated row as a premise.
    row_kb = belief(world, author, "existential", "derived", "KB: rests on K0 as a premise", belief_premises=[k0])
    v = kernel_write(world, "ledger_write", {
        "kind": "model_identity_attested", "actor": principal_id(world, "attestbot"),
        "statement": "attestation: K0 model-identity mismatch",
        "attest_row_id": k0, "attest_model": "claude-opus-4", "attest_grade": "exact-command",
        "attest_verdict": "mismatch", "attest_expected": "claude-sonnet-5",
        "attest_session": "s-fixture", "attest_basis": "session.id"})
    assert v["disposition"] == "accepted", v
    res = run_belief(world)
    credited = {a for a in res.asp.atoms if a.startswith("credited_belief(")}
    check("BV-defeat-composition-uncredits-dependent-belief",
          res.verdict() == "AGREE" and f"credited_belief({row_kb})" not in credited,
          f"verdict={res.verdict()}; KB credited={f'credited_belief({row_kb})' in credited}",
          failures)
    kernel_kb_credited = psql_tuples(f"SELECT 1 FROM {world}.credited_beliefs WHERE belief_id={row_kb};")
    check("BV-kernel-view-defeat-composition-matches-engine", kernel_kb_credited == "",
          f"credited_beliefs row for KB present={kernel_kb_credited!r}, expected absent", failures)

    check("BV-full-differential-AGREE", res.verdict() == "AGREE",
          f"verdict={res.verdict()}; asp={len(res.asp.atoms)} sql={len(res.sql.atoms)} atoms; "
          f"only_asp={sorted(res.only_asp)}; only_sql={sorted(res.only_sql)}", failures)

    teardown(world)


def _neg_world(label: str, failures: list[str], tmps: list[Path], build) -> None:
    world = "bv2n" + hashlib.sha256(label.encode()).hexdigest()[:5]
    teardown(world)
    print(f"== scaffolding classic world {world} for negative-control class {label!r} ==")
    wdir = scaffold_classic(world)
    tmps.append(wdir.parent)
    r = led(wdir, "register-principal", "toolbot", "tool", "--purpose", "belief-substrate-v2 negative fixture",
           env={"LED_ACTOR": "author"})
    assert r.returncode == 0, r.stdout + r.stderr
    author = principal_id(world, "author")
    toolbot = principal_id(world, "toolbot")
    build(world, author, toolbot, failures)
    teardown(world)


def neg_universal_missing_universe(failures, tmps):
    def build(world, author, toolbot, failures):
        v = belief_refused(world, author, "universal", "observed", "missing universe on universal")
        check("NEG-universal-missing-universe", v["disposition"] == "refused",
              f"verdict={v}", failures)
    _neg_world("universal-missing-universe", failures, tmps, build)


def neg_existential_observed_missing_witness(failures, tmps):
    def build(world, author, toolbot, failures):
        v = belief_refused(world, author, "existential", "observed", "missing witness on observed existential")
        check("NEG-existential-observed-missing-witness", v["disposition"] == "refused", f"verdict={v}", failures)
    _neg_world("existential-observed-missing-witness", failures, tmps, build)


def neg_testimony_missing_source(failures, tmps):
    def build(world, author, toolbot, failures):
        v = belief_refused(world, author, "existential", "testimony", "missing source on testimony")
        check("NEG-testimony-missing-source", v["disposition"] == "refused", f"verdict={v}", failures)
    _neg_world("testimony-missing-source", failures, tmps, build)


def neg_derived_missing_premises(failures, tmps):
    def build(world, author, toolbot, failures):
        v = belief_refused(world, author, "existential", "derived", "missing premises on derived")
        check("NEG-derived-missing-premises", v["disposition"] == "refused", f"verdict={v}", failures)
    _neg_world("derived-missing-premises", failures, tmps, build)


def neg_dangling_witness_token(failures, tmps):
    def build(world, author, toolbot, failures):
        v = belief_refused(world, author, "existential", "observed", "dangling witness token",
                           belief_witness="row:999999999")
        check("NEG-dangling-witness-token", v["disposition"] == "refused", f"verdict={v}", failures)
    _neg_world("dangling-witness-token", failures, tmps, build)


def neg_dangling_premises_token(failures, tmps):
    def build(world, author, toolbot, failures):
        v = kernel_write(world, "ledger_write", {
            "kind": "belief", "actor": author, "statement": "dangling premises token",
            "belief_polarity": "existential", "belief_basis": "derived",
            "belief_premises": [999999999]})
        check("NEG-dangling-premises-token", v["disposition"] == "refused", f"verdict={v}", failures)
    _neg_world("dangling-premises-token", failures, tmps, build)


def neg_self_contest(failures, tmps):
    def build(world, author, toolbot, failures):
        z = belief(world, author, "existential", "observed", "Z: self-contest target",
                  belief_witness="row:1")  # row 1 is the birth-chain's own genesis; exists on every world
        v = belief_refused(world, author, "existential", "observed", "W: same-actor contest against own belief Z",
                           belief_witness="row:1", belief_contests=z)
        check("NEG-self-contest", v["disposition"] == "refused", f"verdict={v}", failures)
    _neg_world("self-contest", failures, tmps, build)


def neg_contest_of_superseded(failures, tmps):
    def build(world, author, toolbot, failures):
        x = belief(world, author, "existential", "observed", "X: to be revised", belief_witness="row:1")
        v = kernel_write(world, "ledger_write", {
            "kind": "belief", "actor": author, "statement": "X2: author's revision of X",
            "belief_polarity": "existential", "belief_basis": "observed",
            "belief_witness": "row:1", "supersedes": x})
        assert v["disposition"] == "accepted", v
        v2 = belief_refused(world, toolbot, "existential", "observed",
                            "Y: contests the now-superseded X (settled history)",
                            belief_witness="row:1", belief_contests=x)
        check("NEG-contest-of-superseded", v2["disposition"] == "refused", f"verdict={v2}", failures)
    _neg_world("contest-of-superseded", failures, tmps, build)


def neg_cross_principal_supersession(failures, tmps):
    """The R2-resolved refusal (spec §3.2 item 4 / §3.3): a belief is superseded only by its own
    holder -- a different principal's attempted supersession is REFUSED, the correct act being a
    CONTEST instead."""
    def build(world, author, toolbot, failures):
        x = belief(world, author, "existential", "observed", "X: author's belief", belief_witness="row:1")
        v = belief_refused(world, toolbot, "existential", "observed",
                           "attempted cross-principal supersession of X",
                           belief_witness="row:1", supersedes=x)
        check("NEG-cross-principal-supersession-refused", v["disposition"] == "refused", f"verdict={v}", failures)
        # POSITIVE control alongside: the SAME holder MAY supersede (revision).
        v2 = kernel_write(world, "ledger_write", {
            "kind": "belief", "actor": author, "statement": "X revised by its own holder",
            "belief_polarity": "existential", "belief_basis": "observed",
            "belief_witness": "row:1", "supersedes": x})
        check("NEG-same-holder-supersession-accepted", v2["disposition"] == "accepted", f"verdict={v2}", failures)
    _neg_world("cross-principal-supersession", failures, tmps, build)


def neg_dispatch_grain_independence(failures, tmps):
    """B3 (s55): the fifth independence value is accepted without a stamp-distinctness gate; a
    sixth bogus value is refused (the CHECK's own negative control)."""
    def build(world, author, toolbot, failures):
        v0 = kernel_write(world, "ledger_write", {
            "kind": "decision", "actor": author,
            "statement": "target row for the B3 independence fixture"})
        assert v0["disposition"] == "accepted", v0
        target = int(v0["row_id"])
        # reviewed by TOOLBOT (not author -- s21's SoD self-countersign refusal is a DIFFERENT,
        # pre-existing concern this fixture must avoid tripping to isolate the B3 CHECK itself).
        v = kernel_write(world, "review_write", {
            "regards": target, "statement": "isolated-dispatch verdict, relayed",
            "verdict": "attest", "independence": "disclosed-isolated-dispatch", "basis": "spot-check",
            "actor": toolbot})
        check("NEG-b3-disclosed-isolated-dispatch-accepted", v["disposition"] == "accepted", f"verdict={v}", failures)
        v2 = kernel_write(world, "review_write", {
            "regards": target, "statement": "bogus sixth independence value",
            "verdict": "attest", "independence": "not-a-real-value", "basis": "spot-check",
            "actor": toolbot})
        check("NEG-b3-sixth-value-refused", v2["disposition"] == "refused", f"verdict={v2}", failures)
    _neg_world("dispatch-grain-independence", failures, tmps, build)


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    try:
        world_bv(failures, tmps)
        neg_universal_missing_universe(failures, tmps)
        neg_existential_observed_missing_witness(failures, tmps)
        neg_testimony_missing_source(failures, tmps)
        neg_derived_missing_premises(failures, tmps)
        neg_dangling_witness_token(failures, tmps)
        neg_dangling_premises_token(failures, tmps)
        neg_self_contest(failures, tmps)
        neg_contest_of_superseded(failures, tmps)
        neg_cross_principal_supersession(failures, tmps)
        neg_dispatch_grain_independence(failures, tmps)
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
