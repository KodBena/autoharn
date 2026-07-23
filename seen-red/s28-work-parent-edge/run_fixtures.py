#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for kernel/lineage/s28-work-parent-edge.sql +
bootstrap/templates/led.tmpl's `--parent` flag + bootstrap/templates/pickup.tmpl's ROLLUP section
(tracker slug work-tree-rollup, design at ledger row 151, wave-3 dispatch decision at ledger row
192). Real infra, no mocks: a throwaway `--new-world` scaffold in the toy db -- torn down before
AND after this file runs so re-running it never leaves residue.

DRIFT NOTE (ledger row 1367, diagnosed 2026-07-18): this fixture originally applied s28
EXPLICITLY on top of the scaffold via a direct `psql -f kernel/lineage/s28-work-parent-edge.sql`,
because at authoring time s28 was not yet wired into `bootstrap/new-project.sh`'s own
`LINEAGE_CHAIN`. That wiring has since landed: `--new-world` now applies the FULL chain through
s45 automatically, s28 included (`bootstrap/new-project.sh`'s `LINEAGE_CHAIN` variable lists s28
between s27 and s29, and its own `-f` invocation sequence applies
`kernel/lineage/s28-work-parent-edge.sql` directly). Re-applying s28's
`CREATE OR REPLACE VIEW ledger_current` a SECOND time, after the chain has already carried
`ledger_current` forward through a dozen later deltas that each append MORE columns (s29, s36,
s37, s38, s42, s43, s45...), asks Postgres to replace a view with FEWER columns than it already
has -- forbidden (`ERROR: cannot drop columns from view`, witnessed verbatim against a scratch
`--new-world` world before this fix). This is a FIXTURE bug, not a birth-chain defect: a plain
`--new-world` scaffold with no extra apply step already carries every s28 object end to end
(`work_parent` column, `work_item_current`, `work_item_descendants`,
`work_parent_would_cycle()` all present and queryable), witnessed directly against a second
scratch world scaffolded with no s28 re-apply at all. The explicit re-apply step below is
therefore removed; the scaffold alone is s28's proof substrate now, same as every later lineage
delta's own fixture.

Cases:
  a-valid-parent-accepted        -- `./led work open <child> ... --parent <root>` succeeds; the
                                     child's row in `work_item_current` shows the parent slug, and
                                     `work_item_descendants` carries the (root, child, depth=1)
                                     pair.
  b-dangling-parent-refused      -- `./led work open <slug> ... --parent <unopened-slug>` is
                                     REFUSED (nonzero exit) with teach-text naming the dangling
                                     parent -- construction-time refusal, no `work_opened` row for
                                     the refused slug ever lands (verified by absence of a
                                     `work_opened` ledger row for it, before AND after). NOTE
                                     (diagnosed alongside row 1367): under the full chain the s43
                                     write boundary journals every refusal as its OWN committed
                                     `write_refused` audit row (ratified behaviour, not a defect --
                                     s43's own header, R6) -- so the ledger's TOTAL row count does
                                     grow by one on a refusal now; what must never happen is the
                                     refused work item's own opening row landing. Also asserts
                                     EXACTLY ONE `write_refused` row lands (not merely that
                                     `work_opened` is absent), so a hypothetical double-journaling
                                     defect would not slip past unnoticed.
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
                                     ledger_differential.py`) still verdicts AGREE against this
                                     world (proving s28 does not perturb the existing T_now facts)
                                     -- run directly rather than via the scaffolded world's own
                                     `./judge` shim, the same way s26's own fixture already runs
                                     it (`engine/ledger_differential.py` is the direct producer
                                     `./judge` wraps).
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

import importlib.util
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

# cli-rebase-fixture-repairs (ledger row 1170): REUSE (ADR-0012 P1) serve_existing_world from
# seen-red/boundary-service/run_fixtures.py -- the served `led` shim refuses every write until
# this deployment.json gains boundary_url/boundary_deployment.
_BS_SPEC = importlib.util.spec_from_file_location(
    "boundary_service_fixtures", REPO / "seen-red" / "boundary-service" / "run_fixtures.py")
assert _BS_SPEC is not None and _BS_SPEC.loader is not None
bs_fixtures = importlib.util.module_from_spec(_BS_SPEC)
sys.modules["boundary_service_fixtures"] = bs_fixtures
_BS_SPEC.loader.exec_module(bs_fixtures)

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
        # --- scaffold the FULL --new-world birth chain (s28 is wired into it already; no ------
        # --- explicit re-apply -- see the DRIFT NOTE in this file's own module docstring) -----
        print(f"== scaffolding throwaway --new-world {WORLD} (full birth chain, s28 included) ==")
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
        print(f"  scaffold OK (schema={schema} kern={kern} role={role}, s28 objects carried by "
              f"the standard chain).\n")

        # Stand a REAL boundary_service against this exact schema and add boundary_url/
        # boundary_deployment to deployment.json IN PLACE -- the served `led` shim refuses every
        # write otherwise (cli-rebase-fixture-repairs, ledger row 1170).
        proc = bs_fixtures.serve_existing_world(world_dir / "deployment.json", tmp)

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

        # --- b: dangling parent refused, at construction (no work_opened row for the refused ----
        # --- slug ever lands -- the s43 write boundary journals the refusal ITSELF as its own ---
        # --- write_refused audit row, ratified behaviour, so total ledger row count is NOT the --
        # --- right absence-witness on the full chain; the refused item's own opening row is).---
        # --- Strengthened per out-of-frame hack-rationalization audit (2026-07-18, rows -----------
        # --- 1367/1368): also asserts EXACTLY ONE write_refused row lands (not merely that the ---
        # --- work_opened row is absent), so a hypothetical double-journaling defect would not ----
        # --- slip past this fixture unnoticed. ---------------------------------------------------
        def kind_count(kind: str, slug: str | None = None) -> str:
            clause = f"AND work_slug='{slug}' " if slug else ""
            return psql_tuples(
                f"SELECT count(*) FROM {schema}.ledger WHERE kind='{kind}' {clause};").stdout.strip()

        opened_before = kind_count("work_opened", "orphan-y")
        refused_before = kind_count("write_refused")
        rb = led(world_dir, "work", "open", "orphan-y", "Orphan", "--parent", "no-such-slug")
        opened_after = kind_count("work_opened", "orphan-y")
        refused_after = kind_count("write_refused")
        ok_b = (rb.returncode != 0
                and "no opening act" in (rb.stdout + rb.stderr)
                and opened_before == "0" and opened_after == "0"
                and int(refused_after) == int(refused_before) + 1)
        check("b-dangling-parent-refused", ok_b,
              f"exit={rb.returncode} orphan-y work_opened rows before/after="
              f"{opened_before}/{opened_after} (expect 0/0 -- no forbidden row landed); "
              f"write_refused rows before/after={refused_before}/{refused_after} "
              f"(expect exactly +1 -- the refusal itself IS the journaled audit row) "
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
        # cli-rebase-fixture-repairs (ledger row 1170): the REBASED `./pickup` names ROLLUP
        # (alongside RESOURCES/ESTIMATES/TAXONOMIES/MAINTAINER-REVIEW-QUEUE/RECENT-CHANGES/
        # GIT-STATE/IN-FLIGHT) as explicitly UNEXERCISED/NOT-REBASED -- design/FABLE-BOUNDARY-
        # MULTIPLEX-AND-CLI-REBASE-SPEC.md §5's own stated scope, not a regression this pass
        # introduced -- and points the operator at `./legacy/pickup` for that section. This case's
        # actual subject is the ROLLUP arithmetic itself (still a real, direct-psql feature, not
        # retired), so it runs against `./legacy/pickup`, the same direct-psql original the
        # rebased shim's own teach-text names, rather than the served (ROLLUP-less) `./pickup`.
        rp = sh(["bash", str(world_dir / "legacy" / "pickup")], cwd=str(world_dir))
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
        try:
            bs_fixtures.stop_server(proc)
        except NameError:
            pass  # scaffold itself failed before `proc` was ever assigned
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
