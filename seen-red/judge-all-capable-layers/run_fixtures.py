#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity witness for ledger row 1516 (judge-all-capable-layers):
bare `./judge`/`ledger_differential.py` (no --layer) auto-detects each known layer's capability
on the target and runs EVERY capable layer, one verdict line per layer; an incapable layer
prints a declared one-line reason and is NOT run and does NOT turn the run red. Explicit
`--layer <x>` keeps its unchanged single-layer meaning (proven already by
seen-red/defeat-pipeline/run_fixtures.py's W9 -- an explicit `--layer defeat` on a pre-s41
target REFUSES loudly (QUARANTINED); this fixture is scoped to the NEW bare-invocation
auto-detect path that item added, engine/ledger_differential.py's `layer_capability` +
`main`'s no-`--layer` branch).

Real infra, no mocks: CLASSIC scaffolds + manual chain applies in the TOY db, the SAME
house scratch ceremony seen-red/defeat-pipeline/run_fixtures.py already banks (scaffold_classic,
CHAIN_COMMON/CHAIN_A/CHAIN_B, teardown before and after). Never touches kernel/, bootstrap/, or
any live world -- scratch schema pairs only.

WORLDS:
  WORLD ALL  -- chain ends s41 (CHAIN_B): every layer (tnow/work/defeat) is capable. Bare
                `main()` must run all three and print an AGREE (or at least non-INCAPABLE) line
                for each, exit 0.
  WORLD PRE  -- chain ends s40 (CHAIN_A, no s41): tnow/work are capable (work substrate is s22,
                inside CHAIN_COMMON), defeat is NOT. Bare `main()` must print tnow AGREE, work
                AGREE, and a declared INCAPABLE line for defeat (never QUARANTINED, never
                silently skipped) -- and the run must stay GREEN (exit 0): absence of a layer is
                not a defect.
  RED DEMO   -- reruns WORLD ALL's target with `--drop-record` (the standing negative control:
                drop the ASP derivation witness -- see ledger_differential.py's own --drop-record
                flag docstring), which forces every RUN layer QUARANTINED. Proves the OTHER half
                of the exit-code rule this item specifies: a genuinely RED run layer (as opposed
                to a declared-incapable one) DOES turn the bare-invocation exit code red, even
                though the incapable-declared case above does not -- the two must not be
                conflated by any future edit.

Usage: python3 seen-red/judge-all-capable-layers/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import contextlib
import io
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

import ledger_differential  # noqa: E402
import pghost_resolve  # noqa: E402

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own
# environment before any subprocess is spawned -- inherited by the whole process tree
# this fixture starts, so every repo-root verb invocation anywhere downstream carries it.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

PGHOST, PGDB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

# The SAME chains seen-red/defeat-pipeline/run_fixtures.py uses (CHAIN_A = pre-s41 head, CHAIN_B =
# s41 head) -- s22-work-item-ledger.sql sits inside CHAIN_COMMON, so CHAIN_A is already "work"-
# capable and only "defeat"-incapable; CHAIN_B is capable on every layer this build wires up.
CHAIN_COMMON = [
    "s15-schema.sql", "s17-stamp-mechanism.sql", "s17-independence-vocabulary.sql",
    "s19-trigger-search-path.sql", "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
    "s25-commission-kind.sql", "s26-row-hash-chain.sql", "s27-chain-high-water.sql",
    "s28-work-parent-edge.sql", "s29-obligation-item-key-and-typed-close.sql",
    "s30-typed-dependency-edges.sql", "s31-supersession-uniform-retraction.sql",
    "s32-edge-views-single-home.sql", "s33-composite-discharge.sql",
    "s34-computed-grade-refusal.sql", "s35-validation-decomposition.sql",
    "s36-decision-grade.sql", "s37-violation-disposition.sql",
    "s38-bookkeeping-close.sql", "s39-blocks-start.sql",
    "s40-principal-identity-events.sql",
]
CHAIN_A = CHAIN_COMMON  # s40 head -- pre-s41 (WORLD PRE)
CHAIN_B = CHAIN_COMMON + ["s41-principal-bindings-and-relations.sql"]  # s41 head (WORLD ALL)

# design/FABLE-ENGINE-ENTITLEMENT-SCOPE-ASP-TWIN-SPEC.md: the entitlement layer's floor is no
# longer NoFloor (rows 802/803 closed) -- WORLD ENT below needs a chain reaching s60 (the layer's
# OWN capability probe) so the bare auto-detect path's "NO-FLOOR" skip line (this fixture's own
# pre-existing assertions never exercised, since WORLD ALL stops at s41, pre-s60) is replaced by a
# REAL verdict line. Past s43 (this chain crosses it), the direct-INSERT `birth_acts()` this file's
# other two worlds use is refused (s43 revokes raw INSERT) -- this world instead uses the
# kernel.ledger_write()/registration_write() call pattern seen-red/s70-scope-binding/
# run_fixtures.py's own `bw_call`/`birth_via_boundary` already establish, duplicated here (the
# SAME per-fixture chain-list duplication convention CHAIN_A/CHAIN_B/CHAIN_COMMON above already
# use, not a shared import -- each seen-red fixture is its own standalone witness).
CHAIN_ENT = CHAIN_B + [
    "s42-row-hash-full-coverage.sql", "s43-typed-verdict-write-boundary.sql",
    "s44-model-identity-attestation.sql", "s45-standing-lifecycle.sql",
    "s46-credited-views.sql", "s47-claim-on-closed-refusal.sql",
    "s48-review-witness-existence.sql", "s49-journaler-overflow-guard.sql",
    "s50-defeat-input-raw-domain.sql", "s51-artifact-store.sql",
    "s52-artifact-witness-check.sql", "s53-belief-substrate.sql",
    "s54-belief-views.sql", "s55-dispatch-grain-independence.sql",
    "s56-reservation-residue.sql", "s57-obligation-revocation-event.sql",
    "s58-missive-substrate.sql", "s59-missive-views.sql",
    "s60-entitlement-enforcement.sql",
]


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
        f"DROP SCHEMA IF EXISTS {world} CASCADE; DROP SCHEMA IF EXISTS {world}_kernel CASCADE; "
        f"DROP OWNED BY {world}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {world}_rw;"])


def psql_tuples(sql: str) -> str:
    """Read-only tuples-only psql, used by `birth_via_boundary` (WORLD ENT) -- the SAME helper
    seen-red/s70-scope-binding/run_fixtures.py's own `psql_tuples` duplicates per this fixture's
    own per-file convention."""
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
    hexsecret = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
        "-c", f"TRUNCATE {kern}.stamp_secret;",
        "-c", f"INSERT INTO {kern}.stamp_secret (secret) VALUES (decode('{hexsecret}','hex'));"])
    genesis_hex = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
        "-c", f"INSERT INTO {kern}.chain_genesis (seed) VALUES ('{genesis_hex}') "
              f"ON CONFLICT (only_one) DO NOTHING;"])
    return world_dir


def bw_call(world: str, fn: str, payload: dict) -> dict:
    """Call a kernel write-boundary function directly via psql (bypassing the served
    boundary_service, which this lightweight fixture never stands up) -- the SAME helper seen-red/
    s70-scope-binding/run_fixtures.py's own `bw_call` uses, duplicated per this fixture's own
    per-file convention (see CHAIN_ENT's own comment)."""
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
    """A post-s43 world's birth sequence, routed through the write boundary (s43 revokes raw
    INSERT) -- byte-identical in shape to seen-red/s70-scope-binding/run_fixtures.py's own
    `birth_via_boundary`."""
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
                                "purpose": "judge-all-capable-layers WORLD ENT birth"}),
    ]:
        v = bw_call(world, fn, payload)
        if v["disposition"] != "accepted":
            raise RuntimeError(f"birth act refused: {v}")
    return author


def birth_acts(world: str) -> None:
    S, K, R = world, f"{world}_kernel", f"{world}_rw"
    script = (
        f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
        f"INSERT INTO ledger (kind, statement, actor, principal_subject, principal_purpose)\n"
        f"VALUES ('principal_registered', 'author registered (fixture genesis exception)',\n"
        f"        (SELECT id FROM principal WHERE name='author'),\n"
        f"        (SELECT id FROM principal WHERE name='author'), 'fixture connection principal');\n"
        f"INSERT INTO ledger (kind, statement, actor, principal_subject, principal_db_role)\n"
        f"VALUES ('principal_standing_declared', 'role {R} -> author',\n"
        f"        (SELECT id FROM principal WHERE name='author'),\n"
        f"        (SELECT id FROM principal WHERE name='author'), '{R}');\n")
    r = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-f", "/dev/stdin"], input=script)
    if r.returncode != 0:
        raise RuntimeError(f"birth acts failed ({world}): {r.stderr[-600:]}")


def set_target(name: str) -> None:
    os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"] = \
        PGDB, name, f"{name}_kernel"


def clear_target() -> None:
    for k in ("LEDGER_DB", "LEDGER_SCHEMA", "LEDGER_KERN"):
        os.environ.pop(k, None)


def run_bare_judge(name: str, extra: list[str] | None = None) -> tuple[int, str]:
    """Invoke ledger_differential.main() exactly as bare `./judge` reaches it -- no --layer, a
    single target -- against a scratch world, capturing stdout the way an operator would read it.
    IN-PROCESS (not a subprocess), so the exact `layer_capability`/`main` code under test runs;
    the same real-DB, real-clingo invocation `./judge` itself makes, just addressed at a scratch
    schema instead of this project's own deployment.json target."""
    set_target(name)
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exit_code = ledger_differential.main([name, *(extra or [])])
        return exit_code, buf.getvalue()
    finally:
        clear_target()


def world_all_capable_check(failures: list[str], tmps: list[Path]) -> None:
    world = "s41jacl"
    teardown(world)
    print(f"== scaffolding classic world {world} (chain ends {CHAIN_B[-1]}) -- WORLD ALL ==")
    wdir = scaffold_classic(world, CHAIN_B)
    tmps.append(wdir.parent)
    birth_acts(world)

    exit_code, out = run_bare_judge(world)
    print(out)
    layers_run = {ln.split("layer=", 1)[1].strip("'") for ln in out.splitlines()
                  if ln.startswith("## layer=")}
    incapable_lines = [ln for ln in out.splitlines() if "INCAPABLE" in ln]
    # cli-rebase-fixture-repairs (row 1170): "belief" is a fourth capable layer now (s53's belief
    # substrate, shipped after this fixture was authored) -- it runs vacuously AGREE (0/0 atoms)
    # on ANY schema, including this pre-s53 one, since its own capability check apparently needs
    # no belief-specific column (unlike tnow/work/defeat). Included in the expected set rather
    # than hardcoding the three-layer roster this fixture predates.
    #
    # design/FABLE-JUDGE-LAYER-CAPABILITY-CLOSURE-SPEC.md (RATIFIED 2026-07-27, ledger row 1459's
    # fix): "entitlement" is a FIFTH registered layer now, and (unlike belief) its capability
    # check IS gated on a real column (the s60 entitlement_act_class marker) -- CHAIN_B ends at
    # s41, so this WORLD-ALL world is genuinely pre-s60 and 'entitlement' is declared INCAPABLE
    # here. Its `## layer='entitlement'` header still prints (the header print is unconditional,
    # not gated on capability -- main()'s own shape, untouched by this build), so `layers_run`
    # now includes it too; and its ONE incapable line is now an EXPECTED member of
    # `incapable_lines`, not an absence -- the assertion below names exactly that one line rather
    # than requiring `incapable_lines` to be empty (which predates entitlement's registration).
    entitlement_incapable = [ln for ln in incapable_lines if "layer='entitlement'" in ln]
    other_incapable = [ln for ln in incapable_lines if "layer='entitlement'" not in ln]
    check("WORLD-ALL-every-layer-detected-and-run",
          layers_run == {"tnow", "work", "defeat", "belief", "entitlement"}
          and len(entitlement_incapable) == 1 and "pre-s60 lineage" in entitlement_incapable[0]
          and not other_incapable and exit_code == 0,
          f"exit={exit_code}; layers_run={sorted(layers_run)}; "
          f"entitlement_incapable={entitlement_incapable}; other_incapable={other_incapable}",
          failures)
    check("WORLD-ALL-tnow-AGREE",
          "  [OK ] " in out and "tnow" in out.split("## layer='work'")[0],
          "tnow section printed an AGREE ('OK') line before the work-layer header",
          failures)

    # ---- RED DEMO: --drop-record forces every RUN layer QUARANTINED; the bare-invocation exit
    # code MUST go red here -- proving the incapable-declared case above (exit 0) and a
    # genuinely-red run layer (exit 1) are NOT conflated by this item's change.
    red_exit, red_out = run_bare_judge(world, extra=["--drop-record"])
    print(red_out)
    check("RED-DEMO-drop-record-turns-bare-run-red",
          red_exit == 1 and "QUARANTINED" in red_out and "DIFFERENTIAL RED" in red_out,
          f"exit={red_exit}; contains QUARANTINED={('QUARANTINED' in red_out)}; "
          f"contains 'DIFFERENTIAL RED'={('DIFFERENTIAL RED' in red_out)}",
          failures)

    teardown(world)


def world_pre_s41_check(failures: list[str], tmps: list[Path]) -> None:
    world = "s40jacl"
    teardown(world)
    print(f"== scaffolding classic world {world} (chain ends {CHAIN_A[-1]}) -- WORLD PRE ==")
    wdir = scaffold_classic(world, CHAIN_A)
    tmps.append(wdir.parent)
    birth_acts(world)

    exit_code, out = run_bare_judge(world)
    print(out)
    defeat_lines = [ln for ln in out.splitlines() if world in ln and "defeat" in out]
    incapable_line = next((ln for ln in out.splitlines()
                           if "INCAPABLE" in ln and "layer='defeat'" in ln), None)
    check("WORLD-PRE-defeat-declared-incapable-not-run",
          incapable_line is not None and "pre-s41 lineage" in (incapable_line or ""),
          f"incapable_line={incapable_line!r}",
          failures)
    quarantine_result_lines = [ln for ln in out.splitlines() if "] " in ln and "QUARANTINED" in ln
                               and ln.strip().startswith("[")]
    check("WORLD-PRE-tnow-and-work-still-run-AGREE",
          out.count("AGREE") >= 2 and not quarantine_result_lines,
          f"AGREE count={out.count('AGREE')}; quarantine_result_lines={quarantine_result_lines}",
          failures)
    check("WORLD-PRE-absence-of-layer-does-not-turn-run-red",
          exit_code == 0,
          f"exit={exit_code} (a declared-incapable layer must NOT contribute to the exit code)",
          failures)

    teardown(world)


def world_entitlement_capable_check(failures: list[str], tmps: list[Path]) -> None:
    """design/FABLE-ENGINE-ENTITLEMENT-SCOPE-ASP-TWIN-SPEC.md: the layer's NEW non-refusing path
    -- a target capable of 'entitlement' (the s60 marker column) now gets a REAL verdict line on
    the bare auto-detect path, never the pre-this-build 'NO-FLOOR' skip (which this fixture's
    OTHER two worlds could never exercise, since WORLD ALL stops at s41, pre-s60)."""
    world = "s60jaclent"
    teardown(world)
    print(f"== scaffolding classic world {world} (chain ends {CHAIN_ENT[-1]}) -- WORLD ENT ==")
    wdir = scaffold_classic(world, CHAIN_ENT)
    tmps.append(wdir.parent)
    birth_via_boundary(world)

    exit_code, out = run_bare_judge(world)
    print(out)
    no_floor_lines = [ln for ln in out.splitlines()
                      if "layer='entitlement'" in ln and "NO-FLOOR" in ln]
    # the per-target result line for a RUN layer looks like "  [OK ] <name> AGREE ..." and sits
    # inside the '## layer=...' section for that layer -- slice between the entitlement header
    # and the next header (or EOF) rather than guessing from bare substring membership.
    lines = out.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln == "## layer='entitlement'")
    section = []
    for ln in lines[start + 1:]:
        if ln.startswith("## layer="):
            break
        section.append(ln)
    section_result = [ln for ln in section if ln.strip().startswith("[") and world in ln]
    check("WORLD-ENT-entitlement-no-longer-no-floor",
          not no_floor_lines and len(section_result) == 1 and "AGREE" in section_result[0],
          f"no_floor_lines={no_floor_lines}; section_result={section_result}",
          failures)
    check("WORLD-ENT-bare-run-stays-green",
          exit_code == 0,
          f"exit={exit_code} (a real AGREE on the entitlement layer must not turn the bare run red)",
          failures)

    teardown(world)


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    try:
        world_all_capable_check(failures, tmps)
        world_pre_s41_check(failures, tmps)
        world_entitlement_capable_check(failures, tmps)
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
