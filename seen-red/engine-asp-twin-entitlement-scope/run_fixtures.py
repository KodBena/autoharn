#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity witness for design/FABLE-ENGINE-ENTITLEMENT-SCOPE-ASP-TWIN-
SPEC.md §4's witness plan (ratified ledger rows 822/838/839): the entitlement/scope SQL floor
(engine/ledger_floor.py::entitlement_floor_atoms, the s70 addition to engine/ledger_edb.py's
export_entitlement, and the s70 scope predicates in engine/lp/ledger_entitlement.lp) -- the gap
`./judge --layer entitlement` had (LAYERS['entitlement'].floor was NoFloor, rows 802/803) is
closed by this commission; this fixture is the RED-then-GREEN proof of it, on a real s70-bearing
scratch birth (real infra, no mocks).

Real infra pattern borrowed VERBATIM from seen-red/s70-scope-binding/run_fixtures.py (CHAIN_S70,
scaffold_classic, bw_call/birth_via_boundary/register, teardown before and after) -- the kernel
has NO served write route for principal_scope_bound yet (s70 is authored/scratch-witnessed only,
not in any birth chain), so this fixture writes through the SAME kernel.ledger_write()/
registration_write() functions directly, exactly as the s70 kernel delta's own fixture does.

WORLD MAIN (s70 head, CHAIN_S70):
  BOUND-SCOPED-EXACT-SURFACES-NO-OPEN-SCOPE   -- a principal bound to two named surfaces derives
                                    may_read_surface for EXACTLY those two and no open_scope.
  UNBOUND-OPEN-SCOPE-FULL-VOCABULARY          -- a never-bound principal derives open_scope and
                                    may_read_surface over the FULL injected surface vocabulary.
  BOUND-NO-SURFACES-FAIL-CLOSED               -- a binding row with NULL scope_surfaces (and NULL
                                    disclosure mode) arms (no open_scope) but derives NO
                                    may_read_surface at all -- grants nothing, not everything.
  NULL-DISCLOSURE-MODE-NO-FACT                -- the same no-surfaces binding's NULL disclosure
                                    mode emits no scope_disclosure/2 fact on either producer.
  DISCLOSURE-MODE-SET-EMITS-FACT              -- contrast case: an explicit disclosure mode DOES
                                    emit the fact, on both producers.
  ENTITLEMENT-DIFFERENTIAL-AGREE              -- the whole accumulated world's 'entitlement' layer
                                    differential reads AGREE.
  RETAIN-BANKS-NONEMPTY-EDB                   -- `ledger_differential.main` with
                                    ['--layer','entitlement','--retain'] (the THIRD named consumer
                                    surface, main()'s edb_text if-chain) banks a NON-EMPTY edb.lp
                                    carrying the scope facts -- before this build the if-chain had
                                    no 'entitlement' branch at all, so this would have silently
                                    banked an EMPTY file for a now-non-refusing layer.

WORLD PRE (s69 head, no s70, but s60-capable): PRE-S70-EVERYONE-OPEN-DEGRADE-AGREE -- adjudicated
  (not skipped) under the "one semantics" everyone-open degrade, AGREE.

RED (no fresh world needed for either leg):
  RED-BROKEN-FLOOR-DIVERGES        -- a deliberately-broken open_scope reading (every principal
                                    open regardless of scope_binding_row, the "one predicate's SQL
                                    edited in a scratch copy" leg) diverges from the real ASP
                                    atoms on WORLD MAIN's own live data -- proves the differential
                                    would read DIVERGE_DEFECT.
  RED-MALFORMED-EXCLUSIONS-QUARANTINED -- scope_exclusions_shape dropped on a THROWAWAY world,
                                    a kernel-impossible payload inserted directly, then
                                    run_layer_differential(..., 'entitlement') reads QUARANTINED
                                    with the SAME parse-refusal reason on both producers (the
                                    typed ScopeExclusionParseError, never a generic except).

Usage: python3 seen-red/engine-asp-twin-entitlement-scope/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

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
sys.path.insert(0, str(ENGINE))
sys.path.insert(0, str(REPO / "filing"))
sys.path.insert(0, str(REPO / "serving"))

import ledger_differential  # noqa: E402
import ledger_edb  # noqa: E402
import ledger_floor  # noqa: E402
import lp_registry  # noqa: E402
import pghost_resolve  # noqa: E402

os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

PGHOST, PGDB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_S69 = [
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
    "s44-model-identity-attestation.sql", "s45-standing-lifecycle.sql",
    "s46-credited-views.sql", "s47-claim-on-closed-refusal.sql",
    "s48-review-witness-existence.sql", "s49-journaler-overflow-guard.sql",
    "s50-defeat-input-raw-domain.sql", "s51-artifact-store.sql",
    "s52-artifact-witness-check.sql", "s53-belief-substrate.sql",
    "s54-belief-views.sql", "s55-dispatch-grain-independence.sql",
    "s56-reservation-residue.sql", "s57-obligation-revocation-event.sql",
    "s58-missive-substrate.sql", "s59-missive-views.sql",
    "s60-entitlement-enforcement.sql", "s61-signature-symmetry-and-key-binding.sql",
    "s62-delegation-lifecycle-gating.sql", "s63-supersession-body-restoration.sql",
    "s64-principal-stamps-delegation-conditions.sql",
    "s65-refusal-attempted-kind.sql",
    "s66-forged-stamp-journal-totality.sql",
    "s67-refusal-digest-bound.sql",
    "s68-typed-absence-dispositions.sql",
    "s69-role-coherence-refusals.sql",
]
CHAIN_S70 = CHAIN_S69 + ["s70-scope-binding.sql"]


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    # PGOPTIONS stripped for every subprocess -- see seen-red/s70-scope-binding/run_fixtures.py's
    # own `sh()` docstring for the full reason (this agent's shell injects app.vendor_* GUCs valid
    # only against THIS project's own deployment, present-but-invalid against a fresh scratch
    # world's freshly-random stamp secret).
    env = dict(kw.pop("env", os.environ))
    env.pop("PGOPTIONS", None)
    return subprocess.run(args, capture_output=True, text=True, env=env, **kw)


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


def psql_tuples(sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"psql failed: {cp.stdout[-500:]} {cp.stderr[-500:]}")
    return cp.stdout.strip()


def scaffold_classic(world: str, chain: list[str]) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix=f"{world}-seenred-"))
    world_dir = tmp / world
    schema, kern, role = world, f"{world}_kernel", f"{world}_rw"
    r = sh(["bash", str(NEW_PROJECT), str(world_dir),
            "--db", PGDB, "--host", PGHOST,
            "--schema", schema, "--kern", kern, "--role", role])
    if r.returncode != 0:
        raise RuntimeError(f"CLASSIC SCAFFOLD FAILED ({world}): {r.stdout[-1500:]} {r.stderr[-1500:]}")
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}"]
    for name in chain:
        args += ["-f", str(LINEAGE / name)]
    ra = sh(args)
    if ra.returncode != 0:
        raise RuntimeError(f"CLASSIC apply FAILED ({world}): {ra.stdout[-1500:]} {ra.stderr[-1500:]}")
    genesis_hex = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
        "-c", f"INSERT INTO {kern}.chain_genesis (seed) VALUES ('{genesis_hex}') "
              f"ON CONFLICT (only_one) DO NOTHING;"])
    return world_dir


def bw_call(world: str, fn: str, payload: dict) -> dict:
    S, K, R = world, f"{world}_kernel", f"{world}_rw"
    pj = json.dumps(payload).replace("'", "''")
    r = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-f", "/dev/stdin"],
           input=f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
                 f"SELECT to_jsonb(v) FROM {K}.{fn}('{pj}'::jsonb) v;\n")
    if r.returncode != 0:
        raise RuntimeError(f"NON-VERDICT: {r.stderr.strip()[-800:]}")
    lines = [ln for ln in r.stdout.splitlines() if ln.strip().startswith("{")]
    if not lines:
        raise RuntimeError(f"NO VERDICT LINE: stdout={r.stdout!r} stderr={r.stderr!r}")
    return json.loads(lines[-1])


def birth_via_boundary(world: str) -> str:
    K = f"{world}_kernel"
    author = psql_tuples(f"SELECT id FROM {K}.principal WHERE name='author';")
    login_role = psql_tuples("SELECT session_user;")
    for fn, payload in [
        ("ledger_write", {"kind": "principal_registered",
                          "statement": "author registered (fixture genesis exception)",
                          "actor": author, "principal_subject": author,
                          "principal_purpose": "fixture connection principal"}),
        ("ledger_write", {"kind": "principal_standing_declared",
                          "statement": f"role {world}_rw -> author", "actor": author,
                          "principal_subject": author, "principal_db_role": f"{world}_rw",
                          "principal_binding_active": "true"}),
        ("ledger_write", {"kind": "principal_standing_declared",
                          "statement": f"login role {login_role} -> author (dual declaration)",
                          "actor": author, "principal_subject": author,
                          "principal_db_role": login_role,
                          "principal_binding_active": "true"}),
        ("registration_write", {"name": "write-boundary", "agent_class": "tool",
                                "actor": author,
                                "purpose": "engine-asp-twin-entitlement-scope fixture's own "
                                          "write-boundary registration"}),
    ]:
        v = bw_call(world, fn, payload)
        if v["disposition"] != "accepted":
            raise RuntimeError(f"birth act refused: {v}")
    return author


def register(world: str, author: str, name: str, agent_class: str = "human") -> str:
    v = bw_call(world, "registration_write",
                {"name": name, "agent_class": agent_class, "actor": author,
                 "purpose": f"fixture principal {name}"})
    if v["disposition"] != "accepted":
        raise RuntimeError(f"registration of {name} refused: {v}")
    K = f"{world}_kernel"
    return psql_tuples(f"SELECT id FROM {K}.principal WHERE name='{name}';")


def bind_scope(world: str, author: str, subject: str, **fields) -> dict:
    """Write a principal_scope_bound row: author (genesis-chained, so its own authority-chain
    conjunct is trivially satisfied) asserts a scope binding ABOUT `subject` -- conjunct (b)'s
    entitlement check keys on the WRITER's (actor's) chain, never the subject's, so author may
    bind a scope onto any registered principal, exactly as s70's own fixture already established
    (HAPPY-SCOPE-REBIND-BY-ENTITLED etc.)."""
    payload = {"kind": "principal_scope_bound",
              "statement": f"scope binding for subject {subject} (fixture)",
              "actor": author, "principal_subject": subject, "principal_binding_active": "true"}
    payload.update(fields)
    v = bw_call(world, "ledger_write", payload)
    if v["disposition"] != "accepted":
        raise RuntimeError(f"scope bind for {subject} refused: {v}")
    return v


def run_ent(world: str):
    """run_layer_differential('entitlement') in-process against `world` via the LEDGER_* target
    env vars ledger_edb.resolve() reads -- the same targeting seam every other in-repo scratch
    differential caller (ledger_support_scratch.py, the belief/s70 fixtures' judge_agree) uses."""
    os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"] = \
        PGDB, world, f"{world}_kernel"
    try:
        return ledger_differential.run_layer_differential(world, "entitlement")
    finally:
        for k in ("LEDGER_DB", "LEDGER_SCHEMA", "LEDGER_KERN"):
            os.environ.pop(k, None)


def world_main(failures: list[str], tmps: list[Path]) -> None:
    world = "eatsmain"
    teardown(world)
    print(f"== scaffolding classic world {world} (chain ends {CHAIN_S70[-1]}) -- WORLD MAIN ==")
    wdir = scaffold_classic(world, CHAIN_S70)
    tmps.append(wdir.parent)
    author = birth_via_boundary(world)

    p_scoped = register(world, author, "scoped1")
    p_unbound = register(world, author, "unbound1")
    p_nosurf = register(world, author, "nosurf1")
    p_disclosed = register(world, author, "disclosed1")

    surfs = sorted(ledger_edb.SURFACE_VOCABULARY)
    s1, s2 = surfs[0], surfs[1]
    bind_scope(world, author, p_scoped, scope_surfaces=[s1, s2], scope_disclosure_mode="marked")
    bind_scope(world, author, p_nosurf)  # no scope_surfaces, no scope_disclosure_mode key at all
    bind_scope(world, author, p_disclosed, scope_disclosure_mode="hash_stub")

    res = run_ent(world)
    check("ENTITLEMENT-DIFFERENTIAL-AGREE",
          res.verdict() == "AGREE",
          f"verdict={res.verdict()}; only_asp={sorted(res.only_asp)}; "
          f"only_sql={sorted(res.only_sql)}; asp={len(res.asp.atoms)} sql={len(res.sql.atoms)} "
          f"atoms",
          failures)
    atoms = res.asp.atoms  # AGREE just asserted -- asp/sql atoms are set-equal here

    scoped_reads = {a for a in atoms if a.startswith(f"may_read_surface({p_scoped},")}
    check("BOUND-SCOPED-EXACT-SURFACES-NO-OPEN-SCOPE",
          f"open_scope({p_scoped})" not in atoms
          and scoped_reads == {f'may_read_surface({p_scoped},{s1})',
                               f'may_read_surface({p_scoped},{s2})'},
          f"open_scope present={f'open_scope({p_scoped})' in atoms}; "
          f"may_read_surface atoms for {p_scoped}={sorted(scoped_reads)} "
          f"(expected exactly {{{s1},{s2}}})",
          failures)

    unbound_reads = {a for a in atoms if a.startswith(f"may_read_surface({p_unbound},")}
    check("UNBOUND-OPEN-SCOPE-FULL-VOCABULARY",
          f"open_scope({p_unbound})" in atoms and len(unbound_reads) == len(surfs),
          f"open_scope present={f'open_scope({p_unbound})' in atoms}; "
          f"may_read_surface count for {p_unbound}={len(unbound_reads)} (expected {len(surfs)})",
          failures)

    nosurf_reads = {a for a in atoms if a.startswith(f"may_read_surface({p_nosurf},")}
    check("BOUND-NO-SURFACES-FAIL-CLOSED",
          f"open_scope({p_nosurf})" not in atoms and not nosurf_reads,
          f"open_scope present={f'open_scope({p_nosurf})' in atoms}; "
          f"may_read_surface atoms for {p_nosurf}={sorted(nosurf_reads)} (expected none -- "
          f"armed-with-no-surfaces grants nothing, fail-closed)",
          failures)

    check("NULL-DISCLOSURE-MODE-NO-FACT",
          not any(a.startswith(f"scope_disclosure({p_nosurf},") for a in atoms),
          f"scope_disclosure atoms for {p_nosurf}="
          f"{sorted(a for a in atoms if a.startswith(f'scope_disclosure({p_nosurf},'))} "
          f"(expected none -- NULL disclosure mode, no explicit tier set)",
          failures)
    check("DISCLOSURE-MODE-SET-EMITS-FACT",
          f'scope_disclosure({p_disclosed},hash_stub)' in atoms,
          f"scope_disclosure atoms for {p_disclosed}="
          f"{sorted(a for a in atoms if a.startswith(f'scope_disclosure({p_disclosed},'))} "
          f"(expected scope_disclosure({p_disclosed},hash_stub) -- 'hash_stub' is bare-safe per "
          f"atom_quote, matching both producers)",
          failures)

    # ---- RETAIN-BANKS-NONEMPTY-EDB: the THIRD named consumer surface (main()'s --retain
    # edb_text if-chain) -- run the REAL main() entry point, not run_layer_differential directly.
    os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"] = \
        PGDB, world, f"{world}_kernel"
    try:
        before = set((ledger_differential.RETENTION / world).glob("*")) \
            if (ledger_differential.RETENTION / world).exists() else set()
        exit_code = ledger_differential.main([world, "--layer", "entitlement", "--retain"])
    finally:
        for k in ("LEDGER_DB", "LEDGER_SCHEMA", "LEDGER_KERN"):
            os.environ.pop(k, None)
    after = set((ledger_differential.RETENTION / world).glob("*"))
    new_dirs = sorted(after - before)
    edb_ok, edb_detail = False, "no new retention dir found"
    if new_dirs:
        edb_path = new_dirs[-1] / "edb.lp"
        edb_text = edb_path.read_text(encoding="utf-8") if edb_path.exists() else ""
        edb_ok = bool(edb_text.strip()) and "scope_binding_row(" in edb_text
        edb_detail = f"{edb_path}: {len(edb_text)} bytes, contains scope_binding_row(={('scope_binding_row(' in edb_text)}"
    check("RETAIN-BANKS-NONEMPTY-EDB",
          exit_code == 0 and edb_ok,
          f"exit={exit_code}; new_dirs={[str(d) for d in new_dirs]}; {edb_detail}",
          failures)
    for d in new_dirs:  # scratch-fixture retention artifacts are not repo evidence -- clean up
        shutil.rmtree(d, ignore_errors=True)

    # ---- RED-BROKEN-FLOOR-DIVERGES: a deliberately-broken open_scope reading, independence
    # witnessed by breaking each side once (spec §4) -- this is the SQL-side break, mirrored
    # against the SAME world's real ASP atoms (run_asp, not run_layer_differential, so only the
    # SQL half is mutated).
    broken_rows = psql_tuples(f"SELECT id FROM {world}_kernel.principal ORDER BY id;")
    broken_open = {f"open_scope({r})" for r in broken_rows.splitlines() if r.strip()}
    real_open = {a for a in atoms if a.startswith("open_scope(")}
    check("RED-BROKEN-FLOOR-DIVERGES",
          broken_open != real_open and f"open_scope({p_scoped})" in broken_open
          and f"open_scope({p_scoped})" not in real_open,
          f"broken (everyone-open) atoms={sorted(broken_open)}; real (correct) atoms="
          f"{sorted(real_open)} -- broken WRONGLY includes the scoped/no-surf principals; "
          f"the differential this proves would read DIVERGE_DEFECT on a real target",
          failures)

    teardown(world)


def world_pre(failures: list[str], tmps: list[Path]) -> None:
    world = "eatspre"
    teardown(world)
    print(f"== scaffolding classic world {world} (chain ends {CHAIN_S69[-1]}, NO s70) "
          f"-- WORLD PRE ==")
    wdir = scaffold_classic(world, CHAIN_S69)
    tmps.append(wdir.parent)
    author = birth_via_boundary(world)
    register(world, author, "unbound_pre")

    res = run_ent(world)
    check("PRE-S70-EVERYONE-OPEN-DEGRADE-AGREE",
          res.verdict() == "AGREE",
          f"verdict={res.verdict()}; only_asp={sorted(res.only_asp)}; "
          f"only_sql={sorted(res.only_sql)}; asp={len(res.asp.atoms)} sql={len(res.sql.atoms)} "
          f"atoms (pre-s70-but-s60-capable target -- adjudicated under the everyone-open degrade, "
          f"not skipped)",
          failures)
    teardown(world)


def world_malformed_exclusions(failures: list[str], tmps: list[Path]) -> None:
    world = "eatsmal"
    teardown(world)
    print(f"== scaffolding classic world {world} (chain ends {CHAIN_S70[-1]}) "
          f"-- RED-MALFORMED-EXCLUSIONS ==")
    wdir = scaffold_classic(world, CHAIN_S70)
    tmps.append(wdir.parent)
    author = birth_via_boundary(world)
    subj = register(world, author, "malprobe")

    # spec §4's own staging instruction: drop scope_exclusions_shape on the SCRATCH schema first
    # ("the CHECK binds superusers too; the drop is the disclosed price of staging kernel-
    # impossible bytes, on scratch only") -- then insert directly, bypassing kernel.ledger_write
    # (which would refuse elsewhere first for an unrelated reason) and the CHECK alike.
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
        f"ALTER TABLE {world}.ledger DROP CONSTRAINT scope_exclusions_shape;"])
    malformed = json.dumps([{"family": "not-a-real-family", "value": "x"}]).replace("'", "''")
    ins = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
             f"INSERT INTO {world}.ledger "
             f"(kind, statement, actor, principal_subject, principal_binding_active, "
             f"scope_exclusions) VALUES ('principal_scope_bound', 'malformed exclusions probe', "
             f"{author}, {subj}, true, '{malformed}'::jsonb);"])
    if ins.returncode != 0:
        raise RuntimeError(f"staging insert failed: {ins.stderr[-800:]}")

    res = run_ent(world)
    check("RED-MALFORMED-EXCLUSIONS-QUARANTINED",
          res.verdict() == ledger_differential.QUARANTINED
          and res.asp.quarantine is not None and res.sql.quarantine is not None
          and "scope_exclusions" in (res.asp.quarantine or ""),
          f"verdict={res.verdict()}; asp.q={res.asp.quarantine!r}; sql.q={res.sql.quarantine!r}",
          failures)
    teardown(world)


def w_reg_registry_agree(failures: list[str]) -> None:
    """Registry sanity: the 'entitlement' layer's floor is now a real predicate set (not NoFloor),
    and its MODULES entry carries the full five-predicate #show list (the pre-existing drift
    repair, spec §1c)."""
    floor = lp_registry.LAYERS["entitlement"].floor
    check("REGISTRY-ENTITLEMENT-FLOOR-IS-PREDICATE-SET",
          isinstance(floor, frozenset) and floor == frozenset(ledger_floor.ENTITLEMENT_PREDS),
          f"floor={floor!r}", failures)
    provides = lp_registry.MODULES["ledger_entitlement.lp"].provides
    check("REGISTRY-MODULES-PROVIDES-REPAIRED",
          set(provides) == {"reaches_genesis/1", "reaches_genesis_scoped/2", "open_scope/1",
                            "may_read_surface/2", "scope_disclosure/2"},
          f"provides={provides!r}", failures)


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    try:
        w_reg_registry_agree(failures)
        world_main(failures, tmps)
        world_pre(failures, tmps)
        world_malformed_exclusions(failures, tmps)
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
