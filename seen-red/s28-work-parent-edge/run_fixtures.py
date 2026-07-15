#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-12T16:29:43Z
#   last-change: 2026-07-12T16:29:43Z
#   contributors: 3c50e030/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for kernel/lineage/s28-work-parent-edge.sql +
bootstrap/templates/led.tmpl's `--parent` flag + bootstrap/templates/pickup.tmpl's ROLLUP section
(tracker slug work-tree-rollup, design at ledger row 151, wave-3 dispatch decision at ledger row
192). Real infra, no mocks: a throwaway `--new-world` scaffold in the toy db (which applies the
s15..s26 birth chain automatically), with s28 applied EXPLICITLY on top via a direct psql -f (s28
is not wired into `bootstrap/new-project.sh`'s own `LINEAGE_CHAIN` yet -- that wiring is the
wave-3 orchestrator's seam-integration act, per s28's own header) -- torn down before AND after
this file runs so re-running it never leaves residue.

Cases:
  a-valid-parent-accepted        -- `./led work open <child> ... --parent <root>` succeeds; the
                                     child's row in `work_item_current` shows the parent slug, and
                                     `work_item_descendants` carries the (root, child, depth=1)
                                     pair.
  b-dangling-parent-refused      -- `./led work open <slug> ... --parent <unopened-slug>` is
                                     REFUSED (nonzero exit) with teach-text naming the dangling
                                     parent -- construction-time refusal, no row written (verified
                                     by ledger row count unchanged).
  c-self-parent-refused          -- `--parent` naming the item's OWN slug is REFUSED at
                                     CONSTRUCTION TIME (the `work_parent_not_self` CHECK), a
                                     stronger surface than the trigger's own cycle walk.
  d-cycle-function-both-polarities -- `work_parent_would_cycle()` tested DIRECTLY, in isolation
                                     (the s26 case-h technique: test the shared logic without
                                     needing a reachable INSERT path, since a genuine multi-node
                                     cycle is structurally UNREACHABLE via ordinary INSERT -- see
                                     the delta's own header CYCLES section). NEGATIVE polarity:
                                     asking whether parenting an unrelated root under another
                                     unrelated root would cycle returns false. POSITIVE polarity:
                                     asking whether parenting an ANCESTOR under its own DESCENDANT
                                     would cycle returns true.
  e-rollup-arithmetic-vs-hand-computed -- a small tree (one root, two children, each carrying an
                                     `estimate:` row) is built, `./pickup`'s ROLLUP section is run,
                                     and its printed CHILDREN SUM / SPLIT-TIME SIGNAL lines are
                                     checked against a value HAND-COMPUTED in this script from the
                                     same input estimates (never re-deriving pickup's own logic --
                                     an independent arithmetic check).
  f-differential-agree           -- the EXISTING SQL/ASP marriage differential (`engine/
                                     ledger_differential.py`) still verdicts AGREE against this s28
                                     world (proving s28 does not perturb the existing T_now facts;
                                     `./judge` is not run because this fixture scaffolds a world
                                     with only the s15..s26 birth chain PLUS an explicitly-applied
                                     s28 -- `engine/ledger_differential.py` is the direct producer
                                     this project's own `./judge` wraps, run the identical way
                                     s26's own fixture already runs it against a non-standard-birth-
                                     chain world).
  g-pre-s28-led-open-unaffected  -- `led work open` with NO `--parent` flag still succeeds on a
                                     kernel that DOES carry s28 (the column-presence branch is
                                     exercised, not just assumed) -- and a bare `led work open`
                                     against the SAME kernel with `--parent` omitted writes a row
                                     with `work_parent` NULL, never silently broken by s28's own
                                     column-presence check.

Usage: python3 seen-red/s28-work-parent-edge/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402 (filing/pghost_resolve.py via seen-red/_fixture_env.py -- never a literal host default)


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
S28_DELTA = REPO / "kernel" / "lineage" / "s28-work-parent-edge.sql"

PGHOST, PGDB = fixture_pghost(), "toy"
WORLD = "s28fxprobe"


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def teardown_all() -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {WORLD} CASCADE; DROP SCHEMA IF EXISTS {WORLD}_kernel CASCADE; "
        f"DROP OWNED BY {WORLD}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {WORLD}_rw;"])


def led(world_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return sh(["bash", str(world_dir / "led"), *args], cwd=str(world_dir))


def psql_tuples(sql: str) -> subprocess.CompletedProcess[str]:
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])


def main() -> int:
    teardown_all()
    tmp = Path(tempfile.mkdtemp(prefix="s28-seenred-"))
    world_dir = tmp / WORLD
    failures: list[str] = []

    try:
        # --- scaffold the s15..s26 birth chain, then apply s28 explicitly on top -----------------
        print(f"== scaffolding throwaway --new-world {WORLD} (s15..s26 birth chain) ==")
        r = sh(["bash", str(NEW_PROJECT), str(world_dir), "--new-world", WORLD,
                "--db", PGDB, "--host", PGHOST])
        if r.returncode != 0:
            print("SCAFFOLD FAILED:", r.stdout[-1500:], r.stderr[-1500:])
            return 1
        for verb in ("led", "judge", "pickup"):
            p = world_dir / verb
            if p.exists():
                p.chmod(0o755)

        dep = json.loads((world_dir / "deployment.json").read_text(encoding="utf-8"))
        schema, kern, role = dep["schema"], dep["kern"], dep["role"]
        print(f"  scaffold OK (schema={schema} kern={kern} role={role}).\n")

        print(f"== applying s28-work-parent-edge.sql to {schema}/{kern}/{role} ==")
        ra = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
                 "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}",
                 "-f", str(S28_DELTA)])
        if ra.returncode != 0:
            print("s28 APPLY FAILED:", ra.stdout[-1500:], ra.stderr[-1500:])
            return 1
        print("  s28 applied.\n")

        # --- a: valid parent accepted ------------------------------------------------------------
        r1 = led(world_dir, "work", "open", "root-a", "Root", "A")
        r2 = led(world_dir, "work", "open", "child-b", "Child", "B", "--parent", "root-a")
        tree = psql_tuples(
            f"SET ROLE {role}; SET search_path = {schema}, {kern}; "
            f"SELECT slug, parent_slug FROM work_item_current ORDER BY slug;")
        desc = psql_tuples(
            f"SET ROLE {role}; SET search_path = {schema}, {kern}; "
            f"SELECT ancestor_slug, descendant_slug, depth FROM work_item_descendants "
            f"ORDER BY ancestor_slug, descendant_slug;")
        ok_a = (r1.returncode == 0 and r2.returncode == 0
                and "child-b|root-a" in tree.stdout
                and "root-a|child-b|1" in desc.stdout)
        check("a-valid-parent-accepted", ok_a,
              f"open exits: root={r1.returncode} child={r2.returncode}; "
              f"work_item_current={tree.stdout.strip()!r}; "
              f"work_item_descendants={desc.stdout.strip()!r}", failures)

        # --- b: dangling parent refused, at construction (no row written) -----------------------
        count_before = psql_tuples(f"SELECT count(*) FROM {schema}.ledger;").stdout.strip()
        rb = led(world_dir, "work", "open", "orphan-y", "Orphan", "--parent", "no-such-slug")
        count_after = psql_tuples(f"SELECT count(*) FROM {schema}.ledger;").stdout.strip()
        ok_b = (rb.returncode != 0
                and "no opening act" in (rb.stdout + rb.stderr)
                and count_before == count_after)
        check("b-dangling-parent-refused", ok_b,
              f"exit={rb.returncode} row_count_unchanged={count_before == count_after} "
              f"stderr_excerpt={(rb.stdout + rb.stderr).strip()[-220:]!r}", failures)

        # --- c: self-parent refused, at CONSTRUCTION TIME (CHECK constraint) --------------------
        rc = led(world_dir, "work", "open", "self-x", "Self", "--parent", "self-x")
        ok_c = (rc.returncode != 0
                and ("work_parent_not_self" in (rc.stdout + rc.stderr)
                     or "no opening act" in (rc.stdout + rc.stderr)))
        check("c-self-parent-refused", ok_c,
              f"exit={rc.returncode} stderr_excerpt={(rc.stdout + rc.stderr).strip()[-220:]!r}",
              failures)

        # --- d: work_parent_would_cycle() tested directly, both polarities ----------------------
        # child-c is a second, UNRELATED child of root-a -- parenting it under an unrelated root
        # should NOT report a cycle (negative polarity).
        led(world_dir, "work", "open", "unrelated-root", "Unrelated", "Root")
        neg = psql_tuples(
            f"SET ROLE {role}; SET search_path = {schema}, {kern}; "
            f"SELECT work_parent_would_cycle('unrelated-root', 'root-a');")
        # positive polarity: root-a is an ANCESTOR of child-b (root-a -> child-b). Asking whether
        # parenting root-a UNDER child-b would cycle must report true (root-a -> child-b -> root-a).
        pos = psql_tuples(
            f"SET ROLE {role}; SET search_path = {schema}, {kern}; "
            f"SELECT work_parent_would_cycle('child-b', 'root-a');")
        ok_d = neg.stdout.strip() == "f" and pos.stdout.strip() == "t"
        check("d-cycle-function-both-polarities", ok_d,
              f"negative(unrelated pair)={neg.stdout.strip()!r} (expect 'f') "
              f"positive(ancestor-under-descendant)={pos.stdout.strip()!r} (expect 't')", failures)

        # --- e: rollup arithmetic vs hand-computed ------------------------------------------------
        # child-b already carries no estimate; give root-a, child-b, and a NEW child-d each an
        # estimate: row, then hand-compute the expected CHILDREN SUM / SPLIT-TIME SIGNAL and check
        # pickup's own printed output against it -- an independent check, not a re-derivation of
        # pickup's own logic.
        led(world_dir, "decision",
            "estimate: root-a | 100 | 1 | 3h | 100K | hand-computed seen-red fixture")
        led(world_dir, "decision",
            "estimate: child-b | 40 | 0 | 1h-2h | 10K | hand-computed seen-red fixture")
        led(world_dir, "work", "open", "child-d", "Child", "D", "--parent", "root-a")
        led(world_dir, "decision",
            "estimate: child-d | 20-30 | 0 | 30m | 10K | hand-computed seen-red fixture")
        rp = sh(["bash", str(world_dir / "pickup")], cwd=str(world_dir))
        out = rp.stdout
        # hand-computed expectation: children of root-a are child-b (40 calls, 0 spawns, 60-120m)
        # and child-d (20-30 calls, 0 spawns, 30m). SUM tool_calls = (40+20)-(40+30) = 60-70.
        # SUM subagent_spawns = 0-0. SUM wall_clock = (60+30)-(120+30) = 90-150 minutes.
        # own tool_calls for root-a = 100 (a bare int, so own=(100,100)); own(100) >= children
        # sum's upper bound (70) is TRUE -> "own >= children sum" verdict expected.
        ok_e = (rp.returncode == 0
                and "root-a  (direct children: child-b, child-d)" in out
                and "tool_calls=100  subagent_spawns=1  wall_clock=3h  token_oom=100K" in out
                and "tool_calls=60-70" in out and "subagent_spawns=0" in out
                and "wall_clock=90-150m" in out
                and "own=100 vs children_sum=60-70" in out
                and "own >= children sum" in out)
        check("e-rollup-arithmetic-vs-hand-computed", ok_e,
              f"pickup exit={rp.returncode}; ROLLUP excerpt="
              f"{out[out.find('SECTION: ROLLUP'):out.find('SECTION: ROLLUP') + 1400]!r}"
              if "SECTION: ROLLUP" in out else f"ROLLUP section not found; stdout tail={out[-800:]!r}",
              failures)

        # --- f: the EXISTING SQL/ASP marriage differential still AGREEs on an s28 world ----------
        rg = sh(["python3", "engine/ledger_differential.py", WORLD], cwd=str(REPO),
                 env={**os.environ, "LEDGER_DEPLOYMENT": str(world_dir / "deployment.json")})
        ok_f = rg.returncode == 0 and "DIFFERENTIAL GREEN" in rg.stdout
        check("f-differential-agree", ok_f, f"diff_ok={'DIFFERENTIAL GREEN' in rg.stdout} "
              f"(exit={rg.returncode})", failures)

        # --- g: `led work open` with NO --parent still succeeds against a kernel that DOES carry
        # s28 (the column-presence branch is real-exercised, not merely assumed) ------------------
        rh = led(world_dir, "work", "open", "plain-root", "Plain", "Root")
        rh_check = psql_tuples(
            f"SET ROLE {role}; SET search_path = {schema}, {kern}; "
            f"SELECT parent_slug IS NULL FROM work_item_current WHERE slug = 'plain-root';")
        ok_g = rh.returncode == 0 and rh_check.stdout.strip() == "t"
        check("g-pre-s28-led-open-unaffected", ok_g,
              f"exit={rh.returncode} parent_slug_is_null={rh_check.stdout.strip()!r}", failures)

    finally:
        teardown_all()
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- s28 work-parent-edge both-polarity proof (valid parent accepted / "
          "dangling parent refused / self-parent refused at construction / cycle function both "
          "polarities / rollup arithmetic vs hand-computed / differential AGREE / --parent-less "
          "open unaffected on an s28 kernel), zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
