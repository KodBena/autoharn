#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T20:53:36Z
#   last-change: 2026-07-15T20:54:15Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for engine/lp_registry.py + the generalized "work"-layer
differential (design/ORCH-CATEGORICAL-REFACTOR-CONSULT-2026-07-15.md F7 / plan step 8; ledger item
`lp-module-registry`). Closes the two named judge-wiring gaps: ledger_edb.py exported no work_*
fact family (fixed: `ledger_edb.export_work`) and ledger_differential.py was single-program-typed
with TNOW_LP hardcoded (fixed: `ledger_differential.run_layer_differential` + `--layer` flag,
consuming engine/lp_registry.py's declared "work" LAYER = [ledger_tnow.lp, work_items.lp,
work_review.lp]).

Real infra, no mocks: a CLASSIC-mode scaffold (s31's own idiom, one delta later) + manual s15..s31
apply in the TOY db, torn down before AND after so re-running leaves no residue.

Cases:
  red-mis-stacked-refused   -- lp_registry.require_layer_stack('work', <incomplete list>) raises
                               RegistryError with teach-text naming the missing module and the
                               vacuous-pass hazard a silent grounding would produce -- BEFORE any
                               clingo invocation (never a silent empty grounding, the F7 fix).
  red-unknown-layer-refused -- require_layer_stack('nonexistent-layer', [...]) is refused too
                               (a second, cheaper mis-use shape the same function forecloses).
  green-full-stack-agrees   -- the FULL layer stack (program_names=None, the registry's own
                               declared member list) grounds cleanly and
                               ledger_differential.run_layer_differential('work') on this probe's
                               live facts (containing an s28 parent edge, an s30 typed dependency,
                               and an s31 retraction so every composed judgment has a live
                               specimen) returns AGREE.
  green-cli-layer-flag      -- `python3 ledger_differential.py --layer work <schema>` (the exact
                               invocation `./judge --layer work` reaches, since judge.tmpl forwards
                               every extra flag through unchanged -- no template edit was needed,
                               named in the ledger item's own closure) exits 0 and prints AGREE.
  green-export-work-degrades -- ledger_edb.export_work on a pre-s22 schema (the bare `toy` db
                               itself, before any work_* column exists) returns an EMPTY,
                               capability-EXCLUDED export -- never a silent-wrong-empty a caller
                               could misread as "no work items exist here" (I12).

Usage: python3 seen-red/lp-module-registry/run_fixtures.py
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

import ledger_differential as D  # noqa: E402  (via the sys.path bridge above)
import ledger_edb  # noqa: E402
import lp_registry  # noqa: E402
import pghost_resolve  # noqa: E402

PGHOST, PGDB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"
WORLD = "lpregprobe"

CHAIN = [
    "s15-schema.sql", "s17-stamp-mechanism.sql", "s17-independence-vocabulary.sql",
    "s19-trigger-search-path.sql", "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
    "s25-commission-kind.sql", "s26-row-hash-chain.sql", "s28-work-parent-edge.sql",
    "s29-obligation-item-key-and-typed-close.sql", "s30-typed-dependency-edges.sql",
    "s31-supersession-uniform-retraction.sql",
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
        f"DROP SCHEMA IF EXISTS {WORLD} CASCADE; DROP SCHEMA IF EXISTS {WORLD}_kernel CASCADE; "  # declared-drop: lpregprobe (declared scratch/test reset)
        f"DROP OWNED BY {WORLD}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {WORLD}_rw;"])


def led(world_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return sh(["bash", str(world_dir / "led"), *args], cwd=str(world_dir))


def scaffold_classic(world: str) -> tuple[Path, dict]:
    """CLASSIC MODE + manual s15..s31 apply (s31 fixture's own idiom, one delta later -- see
    that file's own docstring for why classic: --new-world would auto-apply s29/s31 via
    LINEAGE_CHAIN and this probe wants explicit control over the exact chain applied)."""
    tmp = Path(tempfile.mkdtemp(prefix=f"{world}-seenred-"))
    world_dir = tmp / world
    schema, kern, role = world, f"{world}_kernel", f"{world}_rw"
    r = sh(["bash", str(NEW_PROJECT), str(world_dir),
            "--db", PGDB, "--host", PGHOST,
            "--schema", schema, "--kern", kern, "--role", role])
    if r.returncode != 0:
        raise RuntimeError(f"CLASSIC SCAFFOLD FAILED ({world}): {r.stdout[-1500:]} {r.stderr[-1500:]}")
    for verb in ("led", "judge", "pickup"):
        p = world_dir / verb
        if p.exists():
            p.chmod(0o755)
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}"]
    for name in CHAIN:
        args += ["-f", str(LINEAGE / name)]
    ra = sh(args)
    if ra.returncode != 0:
        raise RuntimeError(f"CLASSIC s15..s31 APPLY FAILED ({world}): {ra.stdout[-1500:]} {ra.stderr[-1500:]}")
    secret_dir = world_dir / ".claude" / "secrets"
    secret_dir.mkdir(parents=True, exist_ok=True)
    hexsecret = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    (secret_dir / "stamp_secret.hex").write_text(hexsecret + "\n", encoding="utf-8")
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
        "-c", f"TRUNCATE {kern}.stamp_secret;",
        "-c", f"INSERT INTO {kern}.stamp_secret (secret) VALUES (decode('{hexsecret}','hex'));"])
    genesis_hex = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
        "-c", f"INSERT INTO {kern}.chain_genesis (seed) VALUES ('{genesis_hex}') "
              f"ON CONFLICT (only_one) DO NOTHING;"])
    dep = json.loads((world_dir / "deployment.json").read_text(encoding="utf-8"))
    return world_dir, dep


def main() -> int:
    teardown()
    failures: list[str] = []
    tmps: list[Path] = []
    try:
        # ---- red-mis-stacked-refused ------------------------------------------------------
        try:
            lp_registry.require_layer_stack("work", ["work_items.lp", "work_review.lp"])
            ok_red1, detail1 = False, "did not raise -- BUG"
        except lp_registry.RegistryError as e:
            msg = str(e)
            ok_red1 = ("ledger_tnow.lp" in msg and "vacuous-pass" in msg and "REFUSED" in msg)
            detail1 = f"raised RegistryError naming ledger_tnow.lp + vacuous-pass hazard: {msg[:160]!r}..."
        check("red-mis-stacked-refused", ok_red1, detail1, failures)

        # ---- red-unknown-layer-refused -----------------------------------------------------
        try:
            lp_registry.require_layer_stack("no-such-layer", [])
            ok_red2, detail2 = False, "did not raise -- BUG"
        except lp_registry.RegistryError as e:
            ok_red2, detail2 = True, f"raised RegistryError: {str(e)[:120]!r}"
        check("red-unknown-layer-refused", ok_red2, detail2, failures)

        # ---- green-export-work-degrades (bare toy db, no probe needed) ---------------------
        exp0 = ledger_edb.export_work("toy")
        excl = {c.family: c for c in exp0.exclusions()}
        ok_deg = (not exp0.facts and "work_base" in excl and not excl["work_base"].capable
                 and "capability absent" in excl["work_base"].reason)
        check("green-export-work-degrades", ok_deg,
              f"pre-s22 'toy' target: facts={exp0.facts!r} exclusions={list(excl)} "
              f"work_base={excl.get('work_base')!r}", failures)

        # ---- scaffold the probe for the live-substrate cases --------------------------------
        print(f"== scaffolding classic world {WORLD} + manual s15..s31 apply ==")
        world_dir, dep = scaffold_classic(WORLD)
        tmps.append(world_dir.parent)
        schema = dep["schema"]
        print(f"  scaffold OK (schema={schema}).\n")

        led(world_dir, "work", "open", "root-item", "RootItem")
        led(world_dir, "work", "open", "child-item", "ChildItem", "--parent", "root-item")
        led(world_dir, "work", "claim", "root-item")
        led(world_dir, "work", "close", "child-item", "shipped", "--review-witness", "ref-child")
        led(world_dir, "work", "open", "dep-item", "DepItem")
        led(world_dir, "work", "depends", "dep-item", "root-item")
        led(world_dir, "work", "open", "retract-me", "RetractMe")
        retract_row = subprocess.run(
            ["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c",
             f"SELECT id FROM {schema}.ledger WHERE kind='work_opened' AND work_slug='retract-me';"],
            capture_output=True, text=True).stdout.strip()
        led(world_dir, "--supersedes", retract_row, "revision", f"retract row {retract_row} for the probe")

        # ---- green-full-stack-agrees ---------------------------------------------------------
        os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"] = \
            PGDB, schema, f"{schema}_kernel"
        try:
            res = D.run_layer_differential(schema, "work")
        finally:
            del os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"]
        ok_green = (res.verdict() == D.AGREE and len(res.asp.atoms) > 0)
        check("green-full-stack-agrees", ok_green,
              f"verdict={res.verdict()} asp={len(res.asp.atoms)} sql={len(res.sql.atoms)} atoms "
              f"only_asp={sorted(res.only_asp)[:6]} only_sql={sorted(res.only_sql)[:6]}", failures)

        # ---- green-cli-layer-flag -------------------------------------------------------------
        env = dict(os.environ)
        env["LEDGER_DB"], env["LEDGER_SCHEMA"], env["LEDGER_KERN"] = PGDB, schema, f"{schema}_kernel"
        env["EPISTEMIC_PGHOST"] = PGHOST
        cli = sh([sys.executable, str(ENGINE / "ledger_differential.py"), "--layer", "work", schema],
                cwd=str(ENGINE), env=env)
        out = cli.stdout + cli.stderr
        ok_cli = cli.returncode == 0 and "DIFFERENTIAL GREEN" in out and "layer='work'" in out
        check("green-cli-layer-flag", ok_cli,
              f"exit={cli.returncode} excerpt={out.strip()[-300:]!r}", failures)

    finally:
        teardown()
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- engine/lp_registry.py's require_layer_stack refuses a mis-stacked "
          "'work' layer invocation (missing ledger_tnow.lp) AND an unknown-layer request, both "
          "BEFORE any clingo call; ledger_edb.export_work degrades honestly on a pre-s22 target; "
          "the full registry-declared stack grounds and ledger_differential.run_layer_differential "
          "('work') AGREEs on a live probe carrying an s28 parent edge, an s30 dependency, and an "
          "s31 retraction; the `--layer work` CLI flag (the exact path `./judge --layer work` "
          "reaches through judge.tmpl's existing generic passthrough) exits 0 GREEN.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
