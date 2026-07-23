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
    check("WORLD-ALL-every-layer-detected-and-run",
          layers_run == {"tnow", "work", "defeat", "belief"} and not incapable_lines and exit_code == 0,
          f"exit={exit_code}; layers_run={sorted(layers_run)}; incapable_lines={incapable_lines}",
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


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    try:
        world_all_capable_check(failures, tmps)
        world_pre_s41_check(failures, tmps)
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
