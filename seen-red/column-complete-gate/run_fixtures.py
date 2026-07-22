#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for gates/column_complete_gate.py + tools/column_complete.py
(work item column-complete-gate, vestigial_documentation/design/ORCH-CATEGORICAL-REFACTOR-CONSULT-2026-07-15.md F2 / plan
step 5). Real infra, no mocks: a throwaway `--new-world` scaffold in the toy db (full s15..s30 birth
chain, mirroring seen-red/s30-typed-dependency-edges/run_fixtures.py's own scaffold idiom exactly),
torn down before AND after this file runs so re-running it never leaves residue.

Cases:
  a-real-chain-green            -- gates/column_complete_gate.py PASSES against the real, freshly-
                                    scaffolded s15..s30 chain's ledger_current + countersigned_in_force
                                    (the mechanism's green polarity on the actual kernel, not a toy).
  b-generator-matches-live-s30  -- tools/column_complete.generate_ddl()'s column list, for both
                                    registered views, is BYTE-IDENTICAL (column-for-column, in order)
                                    to the hand-authored list kernel/lineage/s30-typed-dependency-
                                    edges.sql itself ships (frozen text, read directly, never re-typed
                                    by this fixture) -- proves the generator's catalog-computed output
                                    would have produced exactly what s30's author hand-typed.
  c-synthetic-missing-column-red -- a synthetic table+view registered as column-complete, with the
                                    view missing one table column and NO declared exclusion for it,
                                    is REFUSED by the gate (exit 1), naming the missing column.
  d-declared-exclusion-green    -- the SAME synthetic shape as (c), but with the missing column
                                    declared as an exclusion (with a reason) in the ViewSpec passed to
                                    the gate, PASSES -- proving the exclusion manifest is honored, not
                                    merely accepted syntactically.
  e-extra-column-red            -- a synthetic view carrying a column the source table does NOT have
                                    is REFUSED, naming it as an EXTRA column.

Usage: python3 seen-red/column-complete-gate/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
S30_DELTA = REPO / "kernel" / "lineage" / "s30-typed-dependency-edges.sql"
GATE = REPO / "gates" / "column_complete_gate.py"

sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "gates"))
import column_complete as cc  # noqa: E402
import column_complete_gate as ccgate  # noqa: E402

PGHOST, PGDB = "192.168.122.1", "toy"
WORLD = "ccgatefxprobe"


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
        f"DROP SCHEMA IF EXISTS {WORLD} CASCADE; DROP SCHEMA IF EXISTS {WORLD}_kernel CASCADE; "
        f"DROP OWNED BY {WORLD}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {WORLD}_rw;"])


def scaffold(world: str) -> str:
    tmp = Path(tempfile.mkdtemp(prefix=f"{world}-seenred-"))
    world_dir = tmp / world
    r = sh(["bash", str(NEW_PROJECT), str(world_dir), "--new-world", world,
            "--db", PGDB, "--host", PGHOST])
    if r.returncode != 0:
        raise RuntimeError(f"SCAFFOLD FAILED ({world}): {r.stdout[-1500:]} {r.stderr[-1500:]}")
    return str(tmp)


def gate(schema: str, extra_args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    return sh(["python3", str(GATE), "--host", PGHOST, "--db", PGDB, "--schema", schema]
              + (extra_args or []))


def _s30_hand_authored_lists() -> dict[str, list[str]]:
    """Parse the two hand-authored column lists straight out of the frozen s30 file text (never
    re-typed here) -- the same text case (b) below diffs the generator's output against."""
    text = S30_DELTA.read_text(encoding="utf-8")
    out: dict[str, list[str]] = {}
    for view in ("ledger_current", "countersigned_in_force"):
        marker = f'CREATE OR REPLACE VIEW :"schema".{view}'
        i = text.index(marker)
        select_i = text.index("SELECT", i)
        from_i = text.index("\nFROM", select_i)
        block = text[select_i + len("SELECT"):from_i]
        cols = [c.strip().split(".", 1)[1] for c in block.replace("\n", " ").split(",") if c.strip()]
        out[view] = cols
    return out


def main() -> int:
    teardown()
    failures: list[str] = []
    tmps: list[str] = []

    try:
        print(f"== scaffolding throwaway --new-world {WORLD} (full s15..s30 birth chain) ==")
        tmp = scaffold(WORLD)
        tmps.append(tmp)
        schema = WORLD
        print(f"  scaffold OK (schema={schema}).\n")

        # --- a: gate PASSES against the real chain ------------------------------------------
        ra = gate(schema)
        out_a = ra.stdout + ra.stderr
        ok_a = ra.returncode == 0 and "PASS" in out_a
        check("a-real-chain-green", ok_a, f"exit={ra.returncode} out={out_a.strip()!r}", failures)

        # --- b: generator output byte-matches s30's own hand-authored column lists ----------
        hand = _s30_hand_authored_lists()
        tcols = cc.table_columns(PGHOST, PGDB, schema, "ledger")
        mismatches = []
        for view, hand_cols in hand.items():
            computed = cc.expected_columns(tcols, cc.REGISTRY[view])
            if computed != hand_cols:
                mismatches.append((view, computed, hand_cols))
        ok_b = not mismatches
        check("b-generator-matches-live-s30", ok_b,
              f"registered views' computed column lists == s30's own hand-authored lists "
              f"(mismatches={mismatches!r})", failures)

        # --- c/d/e: synthetic table+view, red/green/red on missing/declared/extra columns ---
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
            f"CREATE TABLE {schema}.synth_src (a int, b int, c int);"
            f"CREATE VIEW {schema}.synth_view AS SELECT a, c FROM {schema}.synth_src;"
            f"CREATE TABLE {schema}.synth_src2 (x int, y int);"
            f"CREATE VIEW {schema}.synth_view2 AS SELECT x, y, 999 AS z FROM {schema}.synth_src2;"])

        spec_no_excl = cc.ViewSpec(source_table="synth_src", alias="s", exclusions={}, tail_template="")
        diff_c = cc.diff_view(PGHOST, PGDB, schema, "synth_view", spec_no_excl)
        ok_c = (not diff_c.ok) and diff_c.missing == ["b"] and not diff_c.extra
        check("c-synthetic-missing-column-red", ok_c,
              f"diff={diff_c!r} -- 'b' missing, undeclared, refused", failures)

        spec_excl = cc.ViewSpec(source_table="synth_src", alias="s",
                                 exclusions={"b": "seen-red fixture: deliberately dropped, test case d"},
                                 tail_template="")
        diff_d = cc.diff_view(PGHOST, PGDB, schema, "synth_view", spec_excl)
        ok_d = diff_d.ok
        check("d-declared-exclusion-green", ok_d,
              f"diff={diff_d!r} -- same shape as (c), 'b' now declared excluded, passes", failures)

        spec_extra = cc.ViewSpec(source_table="synth_src2", alias="s", exclusions={}, tail_template="")
        diff_e = cc.diff_view(PGHOST, PGDB, schema, "synth_view2", spec_extra)
        ok_e = (not diff_e.ok) and diff_e.extra == ["z"] and not diff_e.missing
        check("e-extra-column-red", ok_e,
              f"diff={diff_e!r} -- 'z' extra, undeclared, refused", failures)

        # Also drive case c through the ACTUAL gate module's own check_registry()/_teach()
        # functions (in-process import, not a re-implementation), via a synthetic registry, to
        # prove the real gate's teach-text names the column -- this is the literal text banked
        # as red.txt evidence. (In-process rather than the CLI subprocess: the CLI process would
        # re-import tools/column_complete.py fresh and never see a registry this process
        # monkeypatches -- check_registry()'s own `registry` PARAMETER exists for exactly this.)
        synth_registry = {"synth_view": spec_no_excl}
        bad = ccgate.check_registry(PGHOST, PGDB, schema, synth_registry)
        teach_lines = [ccgate._teach(d) for d in bad]
        out_cli = "\n".join(f"COLUMN-INCOMPLETE VIEW: {t}" for t in teach_lines)
        ok_cli = len(bad) == 1 and "MISSING column(s) ['b']" in out_cli
        check("c2-real-gate-teach-text-names-missing-column", ok_cli,
              f"bad={bad!r} out={out_cli!r}", failures)

        with open(HERE / "red.txt", "w", encoding="utf-8") as f:
            f.write("column-complete-gate -- banked RED evidence (synthetic missing/extra column "
                    "cases; gates/column_complete_gate.py's teach-text)\n\n")
            f.write(f"case c (missing column, undeclared): {diff_c!r}\n")
            f.write(f"case e (extra column, undeclared): {diff_e!r}\n\n")
            f.write("gates/column_complete_gate.py's own check_registry()/_teach() output for the "
                     "missing-column case (registry containing ONLY the synthetic broken view):\n")
            f.write(out_cli)

        sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
            f"DROP VIEW {schema}.synth_view; DROP TABLE {schema}.synth_src; "
            f"DROP VIEW {schema}.synth_view2; DROP TABLE {schema}.synth_src2;"])

    finally:
        teardown()
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- column-complete-gate both-polarity proof (real s15..s30 chain green, "
          "generator byte-matches s30's own hand-authored column lists, synthetic missing/extra "
          "column red, declared-exclusion green on the identical shape), zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
