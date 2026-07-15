#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-09T14:31:47Z
#   last-change: 2026-07-09T14:31:47Z
#   contributors: be693afb/main
# <<< PROVENANCE-STAMP <<<

"""s22_work_item_fixture -- proves the s22 work-item-ledger delta (s22-work-item-ledger.sql;
design/ORCH-S22-WORK-ITEM-LEDGER.md, Fable-authored spec, session be693afb, 2026-07-09) on a THROWAWAY
schema pair in the TOY db (design/ORCH-S22-WORK-ITEM-LEDGER.md's own witness protocol, items 1-6, run
in order):

  1. open -> claim -> close(shipped, witness) round trip; work_item_current shows each state.
  2. shipped WITHOUT witness REFUSED (work_shipped_requires_witness CHECK -- the negative control).
  3. duplicate open on one slug REFUSED (validate_work_item() -- the Q5 witness).
  4. a depends_on CYCLE appears in work_item_violations (+ engine/lp/work_items.lp); an ACYCLIC
     chain and a dangling (unopened-antecedent) dependency are also exercised -- the cycle fires,
     the acyclic chain does not, the dangling reference is flagged distinctly.
  5. SQL floor (engine/ledger_floor.py::work_item_floor_atoms) vs ASP (engine/lp/work_items.lp)
     differential runs AGREE on THIS SAME probe's live facts (not a separate scratch mirror).
  6. Coverage via `led`: reported, not executed -- `led`'s generic `<kind> <statement...>` INSERT
     path (bootstrap/templates/led.tmpl) has no flag for work_slug/work_title/work_depends_on/
     work_resolution/work_witness, so it CANNOT author a work_* row today. This is named as the
     follow-up verb list (`led work open|claim|depends|close ...`), not silently routed around --
     extending `led` is a bootstrap/ change, outside this mandate's touch-list. Items 1-5 above are
     therefore exercised via raw psql throughout (WITNESSED); item 6 is UNEXERCISED-via-led with
     this concrete blocker.

CROSSES kernel/fixtures/ <-> engine/ ON PURPOSE (named, not silent): items 1-4+6 are a DDL write-
boundary witness (the kernel/fixtures/sNN_*_fixture.py idiom -- s17_stamp_fixture.py,
s19_search_path_fixture.py, s21_session_aware_fixture.py); item 5 is an engine-layer differential
(the engine/*_scratch.py idiom -- ledger_dto_scratch.py, ledger_support_scratch.py). The spec's own
six-item protocol interleaves both concerns over ONE probe ("SQL floor vs .lp differential runs
AGREE on the probe's facts"), so this script bridges engine/ onto sys.path (mirroring
engine/conftest.py's own bridge in the opposite direction) rather than splitting the live rows
across two schemas that could drift out of sync mid-witness.

Scratch-only: schema s22probe / s22probe_kernel, role s22probe_rw -- dropped after, UNLESS an item
FAILS (left standing as evidence per the standing probe pattern; never applied to toycolors, run3,
run4, or any live schema). Run in the TOY db (192.168.122.1), per this delta's own scratch-witness
instructions. Lazy imports banned."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

SCHEMA, KERN, ROLE = "s22probe", "s22probe_kernel", "s22probe_rw"
HERE = Path(__file__).resolve().parent
LINEAGE = HERE.parent / "lineage"
ENGINE = HERE.parent.parent / "engine"
sys.path.insert(0, str(ENGINE))  # bridge for item 5 (clingo_run / ledger_floor) -- see docstring
sys.path.insert(0, str(HERE.parent.parent / "filing"))

import clingo_run  # noqa: E402  (engine/clingo_run.py, via the sys.path bridge above)
import ledger_floor  # noqa: E402  (engine/ledger_floor.py -- work_item_floor_atoms, WORK_ITEM_PREDS)
import pghost_resolve  # noqa: E402 (filing/pghost_resolve.py -- never a literal host default)

PGHOST, DB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

WORK_ITEMS_LP = ENGINE / "lp" / "work_items.lp"


def psql(sql: str) -> tuple[bool, str]:
    cp = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-tA", "-v", "ON_ERROR_STOP=1", "-c", sql],
                        capture_output=True, text=True)
    return cp.returncode == 0, (cp.stdout + cp.stderr).strip()


def psql_rows(sql: str) -> list[list[str]]:
    ok, out = psql(sql)
    if not ok:
        raise RuntimeError(f"psql_rows failed: {out}")
    return [r.split("|") for r in out.splitlines() if r.strip()]


def apply_ddl(fname: str) -> tuple[bool, str]:
    cp = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-v", "ON_ERROR_STOP=1",
                         "-v", f"schema={SCHEMA}", "-v", f"kern={KERN}", "-v", f"role={ROLE}",
                         "-f", str(LINEAGE / fname)], capture_output=True, text=True)
    return cp.returncode == 0, (cp.stdout + cp.stderr).strip()


def ins_work(kind: str, slug: str, *, title: str | None = None, depends_on: str | None = None,
            resolution: str | None = None, witness: str | None = None) -> tuple[bool, str]:
    cols = ["kind", "work_slug", "statement"]
    vals = [f"'{kind}'", f"'{slug}'", f"'{kind}:{slug}'"]
    if title is not None:
        cols.append("work_title"); vals.append(f"'{title}'")
    if depends_on is not None:
        cols.append("work_depends_on"); vals.append(f"'{depends_on}'")
    if resolution is not None:
        cols.append("work_resolution"); vals.append(f"'{resolution}'")
    if witness is not None:
        cols.append("work_witness"); vals.append(f"'{witness}'")
    return psql(f"SET ROLE {ROLE}; INSERT INTO {SCHEMA}.ledger({','.join(cols)}) "
               f"VALUES({','.join(vals)});")


def teardown() -> None:
    subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-c",
                    f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE; DROP SCHEMA IF EXISTS {KERN} CASCADE; "  # declared-drop: s22probe (declared scratch/test reset)
                    f"DROP OWNED BY {ROLE}; DROP ROLE IF EXISTS {ROLE};"], capture_output=True, text=True)


def work_item_edb() -> str:
    """The engine/lp/work_items.lp EDB, read directly off the probe's `ledger` rows (this program
    stands alone -- no ledger_tnow.lp base EDB needed, see work_items.lp's own header)."""
    lines: list[str] = []
    for slug, rid in psql_rows(f"SELECT work_slug, id FROM {SCHEMA}.ledger WHERE kind='work_opened' ORDER BY id;"):
        lines.append(f"work_opened({clingo_run.quote_term(slug)},{int(rid)}).")
    for slug, resolution, rid in psql_rows(
            f"SELECT work_slug, work_resolution, id FROM {SCHEMA}.ledger WHERE kind='work_closed' ORDER BY id;"):
        lines.append(f"work_closed({clingo_run.quote_term(slug)},{resolution},{int(rid)}).")
    for (rid,) in psql_rows(
            f"SELECT id FROM {SCHEMA}.ledger WHERE kind='work_closed' "
            f"AND work_witness IS NOT NULL AND btrim(work_witness) <> '' ORDER BY id;"):
        lines.append(f"work_witness_present({int(rid)}).")
    for dep, ant, rid in psql_rows(
            f"SELECT work_slug, work_depends_on, id FROM {SCHEMA}.ledger WHERE kind='work_depends_on' ORDER BY id;"):
        lines.append(f"work_depends({clingo_run.quote_term(dep)},{clingo_run.quote_term(ant)},{int(rid)}).")
    return "\n".join(lines) + "\n"


def main() -> int:
    fails: list[str] = []
    ck = lambda cond, msg: fails.append(msg) if not cond else None  # noqa: E731
    log: list[str] = []

    teardown()
    for f in ("high_watermark_1.sql", "s20-obligation-grants-and-view-refresh.sql",
             "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql"):
        ok, out = apply_ddl(f)
        if not ok:
            print(f"# S22 FIXTURE SETUP FAILED ({f}): {out[-400:]}")
            return 1
    log.append(f"setup: high_watermark_1.sql + s20 + s21 + s22 applied clean to {DB}.{SCHEMA}/{KERN} (role {ROLE})")

    # ---- ITEM 1: open -> claim -> close(shipped, witness) round trip -------------------------
    ok, out = ins_work("work_opened", "item-1", title="First work item")
    ck(ok, f"ITEM 1: open item-1 must succeed: {out[-200:]}")
    st = psql_rows(f"SELECT state, title, claimant FROM {SCHEMA}.work_item_current WHERE slug='item-1';")
    ck(st and st[0][0] == "open" and st[0][1] == "First work item" and st[0][2] == "",
       f"ITEM 1: after open, work_item_current must show state=open, title, claimant=NULL: {st}")
    log.append(f"ITEM 1a (open):  work_item_current(item-1) = {st}")

    ok, out = ins_work("work_claimed", "item-1")
    ck(ok, f"ITEM 1: claim item-1 must succeed: {out[-200:]}")
    author_id = psql(f"SELECT id FROM {KERN}.principal WHERE name='author';")[1]
    st = psql_rows(f"SELECT state, claimant FROM {SCHEMA}.work_item_current WHERE slug='item-1';")
    ck(st and st[0][0] == "open" and st[0][1] == author_id,
       f"ITEM 1: after claim, state still open, claimant={author_id!r}: {st}")
    log.append(f"ITEM 1b (claim): work_item_current(item-1) state/claimant = {st}  (author principal id={author_id})")

    ok, out = ins_work("work_closed", "item-1", resolution="shipped", witness="commit deadbeef")
    ck(ok, f"ITEM 1: close(shipped, witness) item-1 must succeed: {out[-200:]}")
    st = psql_rows(f"SELECT state, resolution, witness FROM {SCHEMA}.work_item_current WHERE slug='item-1';")
    ck(st and st[0] == ["closed", "shipped", "commit deadbeef"],
       f"ITEM 1: after close, work_item_current must show closed/shipped/witness: {st}")
    log.append(f"ITEM 1c (close): work_item_current(item-1) = {st}")

    # ---- ITEM 2: shipped WITHOUT witness -- REFUSED (negative control) -----------------------
    ins_work("work_opened", "item-2", title="Second work item")
    ok, out = ins_work("work_closed", "item-2", resolution="shipped")
    ck(not ok and "work_shipped_requires_witness" in out,
       f"ITEM 2: shipped-without-witness must be REFUSED by work_shipped_requires_witness: ok={ok} {out[-250:]}")
    log.append(f"ITEM 2 (shipped w/o witness): ok={ok}\n    {out.splitlines()[-1] if out else ''}")

    # ---- ITEM 3: duplicate open on one slug -- REFUSED (the Q5 witness) ----------------------
    ok, out = ins_work("work_opened", "item-1", title="duplicate open attempt")
    ck(not ok and "already has an opening act" in out,
       f"ITEM 3: duplicate open on item-1 must be REFUSED by validate_work_item(): ok={ok} {out[-250:]}")
    log.append(f"ITEM 3 (duplicate open): ok={ok}\n    {out.splitlines()[-1] if out else ''}")

    # a companion corollary check (invariant 2's own text, applied -- see s22 header): an event on
    # a slug that was NEVER opened is refused too.
    ok, out = ins_work("work_claimed", "never-opened-slug")
    ck(not ok and "no opening act" in out,
       f"ITEM 3 corollary: an event on an unopened slug must be REFUSED: ok={ok} {out[-250:]}")
    log.append(f"ITEM 3 corollary (event on unopened slug): ok={ok}\n    {out.splitlines()[-1] if out else ''}")

    # ---- ITEM 4: dependency cycle visible; acyclic chain is not; dangling dep is flagged -----
    for slug in ("item-4a", "item-4b", "item-4c"):
        ins_work("work_opened", slug, title=slug)
    ins_work("work_depends_on", "item-4a", depends_on="item-4b")
    ins_work("work_depends_on", "item-4b", depends_on="item-4c")   # acyclic chain 4a->4b->4c

    for slug in ("item-5a", "item-5b"):
        ins_work("work_opened", slug, title=slug)
    ins_work("work_depends_on", "item-5a", depends_on="item-5b")
    ins_work("work_depends_on", "item-5b", depends_on="item-5a")   # cycle 5a<->5b

    ins_work("work_opened", "item-6", title="dangling-dep item")
    ins_work("work_depends_on", "item-6", depends_on="never-existed-slug")   # dangling antecedent

    viol = psql_rows(f"SELECT violation, slug, detail FROM {SCHEMA}.work_item_violations ORDER BY violation, slug;")
    cyc_slugs = {row[1] for row in viol if row[0] == "dependency_cycle"}
    dangling = {row[1] for row in viol if row[0] == "depends_on_unknown_slug"}
    ck({"item-5a", "item-5b"} <= cyc_slugs, f"ITEM 4: cycle must flag item-5a/item-5b: {viol}")
    ck(not ({"item-4a", "item-4b", "item-4c"} & cyc_slugs),
       f"ITEM 4: the ACYCLIC chain 4a->4b->4c must NOT appear in dependency_cycle: {viol}")
    ck("item-6" in dangling, f"ITEM 4: item-6's dangling dependency must appear in depends_on_unknown_slug: {viol}")
    log.append(f"ITEM 4 (work_item_violations): {viol}")

    # ---- ITEM 5: SQL floor vs ASP (.lp) differential -- AGREE, on THIS SAME probe's facts ----
    edb = work_item_edb()
    asp_atoms = {a for a in clingo_run.run_clingo([WORK_ITEMS_LP], edb) if "(" in a}
    asp_atoms = {a for a in asp_atoms if a.split("(", 1)[0] in ledger_floor.WORK_ITEM_PREDS}
    os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"] = DB, SCHEMA, KERN
    try:
        sql_atoms = ledger_floor.work_item_floor_atoms(SCHEMA)
    finally:
        del os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"]
    only_asp, only_sql = asp_atoms - sql_atoms, sql_atoms - asp_atoms
    verdict = "AGREE" if not only_asp and not only_sql else "DIVERGE_DEFECT"
    ck(verdict == "AGREE", f"ITEM 5: SQL floor vs ASP must AGREE: only_asp={sorted(only_asp)} only_sql={sorted(only_sql)}")
    log.append(f"ITEM 5 (differential): verdict={verdict}  asp={len(asp_atoms)} sql={len(sql_atoms)} atoms")
    if only_asp or only_sql:
        log.append(f"    only_asp={sorted(only_asp)}\n    only_sql={sorted(only_sql)}")

    # ---- ITEM 6: `led` coverage -- REPORTED, not executed (see docstring) ---------------------
    log.append("ITEM 6 (led coverage): UNEXERCISED via led -- bootstrap/templates/led.tmpl's generic "
               "`<kind> <statement...>` path has no flag for work_slug/work_title/work_depends_on/"
               "work_resolution/work_witness, so it cannot author a work_* row today (verified by "
               "reading led.tmpl's fixed INSERT column list). Follow-up verb list (not silently "
               "wrapped): `led work open <slug> <title>`, `led work claim <slug>`, "
               "`led work depends <slug> <on-slug>`, `led work close <slug> <resolution> [--witness ..]` "
               "-- a bootstrap/ change, outside this mandate's touch-list. Items 1-5 above were all "
               "exercised via raw psql.")

    if fails:
        print("# S22 WORK-ITEM FIXTURE -- witness log (FAILURES PRESENT, probe LEFT STANDING as evidence):")
        for line in log:
            print(f"  {line}")
        print("# S22 FIXTURE RED:")
        for f in fails:
            print(f"  !! {f}")
        print(f"# probe left standing: {DB}.{SCHEMA} / {DB}.{KERN} / role {ROLE} -- NOT torn down (a FAILED item)")
        return 1

    teardown()
    print("# S22 WORK-ITEM FIXTURE -- witness log:")
    for line in log:
        print(f"  {line}")
    print("# S22 FIXTURE GREEN -- all 6 witness-protocol items disposed (5 WITNESSED, 1 UNEXERCISED-via-led "
          "with a named blocker); probe torn down.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
