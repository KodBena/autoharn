#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T19:09:31Z
#   last-change: 2026-07-14T19:29:19Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for kernel/lineage/s29-obligation-item-key-and-typed-
close.sql + bootstrap/templates/led.tmpl's `work close` two-constructor change + `work review-gap`
(design/MAINT-COUNTERSIGN-CLOSE-SEMANTICS-SPEC.md, Fable-authored spec, RATIFIED 2026-07-14).
Real infra, no mocks: a throwaway `--new-world` scaffold in the toy db (which applies the s15..s28
birth chain automatically, s28 included per bootstrap/new-project.sh's own LINEAGE_CHAIN), with
s29 applied EXPLICITLY on top via a direct psql -f (s29 is not wired into LINEAGE_CHAIN yet --
that wiring is a maintainer/orchestrator seam-integration act, per s29's own header, mirroring
s28's own deferral) -- torn down before AND after this file runs so re-running it never leaves
residue.

Cases (spec sec-7's own negative controls, plus the positive path each is paired against):
  a-review-silent-close-refused     -- `led work close` with NEITHER --review-witness NOR
                                        --review-deferred is REFUSED, teach-text naming BOTH
                                        constructors (spec sec-7's first negative control).
  b-both-constructors-refused       -- `led work close` with BOTH --review-witness AND
                                        --review-deferred is REFUSED (exactly one, never both).
  c-witnessed-without-ref-refused   -- --review-witness with an EMPTY ref is REFUSED at
                                        construction (work_review_witnessed_requires_ref CHECK).
  d-witnessed-with-ref-accepted     -- --review-witness <ref> succeeds; work_item_current shows
                                        the disposition/ref.
  e-deferred-creates-item-keyed-obligation -- --review-deferred succeeds; `led work review-gap`
                                        shows the item; a SAME-actor review does NOT discharge it
                                        (segregation of duties refuses it outright, an EXISTING
                                        kernel rule); a DISTINCT-actor attest review DOES discharge
                                        it (work_review_gap empties) -- Element A's item-keyed
                                        obligation, discharged exactly like the legacy actor-keyed
                                        review_gap's own join shape, one column over.
  f-strict-plus-deferred-refused    -- --review-deferred --strict is REFUSED directly (a
                                        just-deferred obligation cannot satisfy strict mode's
                                        immediate requirement) -- spec sec-7's second negative
                                        control, the "contradiction in terms" case.
  g-strict-over-unresolved-tree-refused -- --review-witness --strict over a root whose s28 CHILD
                                        is still open is REFUSED, NAMING THE UNRESOLVED LEAF (spec
                                        sec-7's second negative control, the general case: "a
                                        strict-mode close over an unresolved tree is refused
                                        naming the unresolved leaves").
  h-strict-succeeds-once-resolved   -- once the child is closed (witnessed), the SAME strict close
                                        of the root SUCCEEDS -- no stored verdict anywhere, this is
                                        a pure re-query (spec sec-7's third negative control's
                                        positive twin: "a false parent-resolution is demonstrated
                                        unwritable" -- there is no column to write a false
                                        resolution INTO; re-running the same query after the real
                                        state changes is the only way the answer changes).
  k1/k2-strict-over-unresolved-dependency -- REGRESSION case for a real defect an out-of-frame
                                        hack-rationalization audit caught in this same session,
                                        before this file's first commit (not shipped): a first
                                        draft's dependency-leaf check treated an antecedent as
                                        resolved once it had ANY close row, never checking that
                                        the antecedent's OWN review obligation was itself resolved
                                        -- so `A --depends-on B`, B closed --review-deferred
                                        (undischarged), `A --strict` WRONGLY SUCCEEDED (witnessed
                                        directly against the fixed kernel BEFORE this fixture
                                        existed; the attack scenario is quoted verbatim in
                                        kernel/lineage/s29-...sql's own CORRECTED comment). k1:
                                        strict close of dep-k-a refused, naming dep-k-b's own
                                        undischarged obligation, with NO s28 parent edge involved
                                        at all (a pure work_depends_on chain). k2: once dep-k-b's
                                        obligation is discharged (distinct actor), the identical
                                        strict close of dep-k-a succeeds.
  i-differential-agree              -- SQL floor (`engine/ledger_floor.py::work_review_floor_atoms`)
                                        vs ASP (`engine/lp/work_review.lp`) AGREE on this world's
                                        live facts (both an UNRESOLVED and a RESOLVED tree present).
  j-pre-s29-led-close-unaffected    -- `led work close` with NO review flags at all, against a
                                        kernel that predates s29 (the has_review_disposition_col
                                        live-check's FALSE branch), still succeeds exactly as
                                        before this delta -- exercised on a SEPARATE, s28-only
                                        scaffold (no s29 applied), not just assumed.

Usage: python3 seen-red/s29-obligation-item-key-and-typed-close/run_fixtures.py
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
S29_DELTA = REPO / "kernel" / "lineage" / "s29-obligation-item-key-and-typed-close.sql"
WORK_REVIEW_LP = REPO / "engine" / "lp" / "work_review.lp"

sys.path.insert(0, str(REPO / "engine"))
import clingo_run  # noqa: E402  (engine/clingo_run.py, via the sys.path bridge above)
import ledger_floor  # noqa: E402  (engine/ledger_floor.py -- work_review_floor_atoms, WORK_REVIEW_PREDS)

PGHOST, PGDB = "192.168.122.1", "toy"
WORLD = "s29fxprobe"
WORLD_PRE = "s29fxprobe_pre"


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


def teardown_all() -> None:
    teardown(WORLD)
    teardown(WORLD_PRE)


def led(world_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return sh(["bash", str(world_dir / "led"), *args], cwd=str(world_dir))


def psql_tuples(sql: str) -> subprocess.CompletedProcess[str]:
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])


def scaffold(world: str) -> tuple[Path, dict]:
    tmp = Path(tempfile.mkdtemp(prefix=f"{world}-seenred-"))
    world_dir = tmp / world
    r = sh(["bash", str(NEW_PROJECT), str(world_dir), "--new-world", world,
            "--db", PGDB, "--host", PGHOST])
    if r.returncode != 0:
        raise RuntimeError(f"SCAFFOLD FAILED ({world}): {r.stdout[-1500:]} {r.stderr[-1500:]}")
    for verb in ("led", "judge", "pickup"):
        p = world_dir / verb
        if p.exists():
            p.chmod(0o755)
    dep = json.loads((world_dir / "deployment.json").read_text(encoding="utf-8"))
    return world_dir, dep


def main() -> int:
    teardown_all()
    failures: list[str] = []
    tmps: list[Path] = []

    try:
        # --- scaffold the s15..s28 birth chain, then apply s29 explicitly on top ----------------
        print(f"== scaffolding throwaway --new-world {WORLD} (s15..s28 birth chain) ==")
        world_dir, dep = scaffold(WORLD)
        tmps.append(world_dir.parent)
        schema, kern, role = dep["schema"], dep["kern"], dep["role"]
        print(f"  scaffold OK (schema={schema} kern={kern} role={role}).\n")

        print(f"== applying s29-obligation-item-key-and-typed-close.sql to {schema}/{kern}/{role} ==")
        ra = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
                 "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}",
                 "-f", str(S29_DELTA)])
        if ra.returncode != 0:
            print("s29 APPLY FAILED:", ra.stdout[-1500:], ra.stderr[-1500:])
            return 1
        print("  s29 applied.\n")

        # register a second principal for distinct-actor discharge cases
        led(world_dir, "register-principal", "reviewer2", "model")

        # --- setup: open+claim root-a, and an s28 child child-a --------------------------------
        led(world_dir, "work", "open", "root-a", "Root", "A")
        led(world_dir, "work", "claim", "root-a")
        led(world_dir, "work", "open", "child-a", "Child", "A", "--parent", "root-a")
        led(world_dir, "work", "claim", "child-a")

        # --- a: review-silent close refused, naming BOTH constructors --------------------------
        ra_ = led(world_dir, "work", "close", "root-a", "dropped")
        out_a = ra_.stdout + ra_.stderr
        ok_a = (ra_.returncode != 0 and "--review-witness" in out_a and "--review-deferred" in out_a
                and "unrepresentable" in out_a)
        check("a-review-silent-close-refused", ok_a,
              f"exit={ra_.returncode} names_both_constructors={'--review-witness' in out_a and '--review-deferred' in out_a} "
              f"excerpt={out_a.strip()[-300:]!r}", failures)

        # --- b: both constructors together refused ----------------------------------------------
        rb_ = led(world_dir, "work", "close", "root-a", "dropped", "--review-witness", "ref1", "--review-deferred")
        out_b = rb_.stdout + rb_.stderr
        ok_b = rb_.returncode != 0 and "exactly ONE" in out_b
        check("b-both-constructors-refused", ok_b,
              f"exit={rb_.returncode} excerpt={out_b.strip()[-300:]!r}", failures)

        # --- c: --review-witness with an EMPTY ref refused at construction ---------------------
        rc_ = led(world_dir, "work", "close", "root-a", "dropped", "--review-witness", "")
        out_c = rc_.stdout + rc_.stderr
        ok_c = rc_.returncode != 0 and (
            "work_review_witnessed_requires_ref" in out_c or "unrepresentable" in out_c)
        check("c-witnessed-without-ref-refused", ok_c,
              f"exit={rc_.returncode} excerpt={out_c.strip()[-300:]!r}", failures)

        # --- d: --review-witness <ref> accepted; work_item_current shows disposition/ref -------
        rd_ = led(world_dir, "work", "close", "root-a", "dropped", "--review-witness", "commit-abc123")
        wic = psql_tuples(
            f"SET ROLE {role}; SET search_path = {schema}, {kern}; "
            f"SELECT state, review_disposition, review_ref FROM work_item_current WHERE slug='root-a';")
        ok_d = (rd_.returncode == 0
                and "closed|witnessed|commit-abc123" in wic.stdout)
        check("d-witnessed-with-ref-accepted", ok_d,
              f"exit={rd_.returncode} work_item_current={wic.stdout.strip()!r}", failures)

        # --- e: --review-deferred creates the item-keyed obligation; same-actor does NOT
        # discharge it (SoD refuses outright); distinct-actor attest DOES discharge it ----------
        led(world_dir, "work", "open", "item-e", "E")
        led(world_dir, "work", "claim", "item-e")
        re_ = led(world_dir, "work", "close", "item-e", "dropped", "--review-deferred")
        gap1 = led(world_dir, "work", "review-gap")
        ok_e1 = re_.returncode == 0 and "item-e" in gap1.stdout
        close_row = psql_tuples(
            f"SELECT id FROM {schema}.ledger WHERE kind='work_closed' AND work_slug='item-e';").stdout.strip()
        same_actor = led(world_dir, "review", close_row, "attest", "self-review", "same-actor attempt")
        gap2 = led(world_dir, "work", "review-gap")
        ok_e2 = same_actor.returncode != 0 and "item-e" in gap2.stdout
        os.environ["LED_ACTOR"] = "reviewer2"
        distinct_actor = led(world_dir, "review", close_row, "attest", "self-review", "distinct-actor discharge")
        del os.environ["LED_ACTOR"]
        gap3 = led(world_dir, "work", "review-gap")
        ok_e3 = distinct_actor.returncode == 0 and "item-e" not in gap3.stdout
        ok_e = ok_e1 and ok_e2 and ok_e3
        check("e-deferred-creates-item-keyed-obligation", ok_e,
              f"deferred_close_ok={re_.returncode == 0} gap_after_deferred={gap1.stdout.strip()!r} "
              f"same_actor_refused={same_actor.returncode != 0} gap_after_same_actor={gap2.stdout.strip()!r} "
              f"distinct_actor_ok={distinct_actor.returncode == 0} gap_after_distinct_actor={gap3.stdout.strip()!r}",
              failures)

        # --- f: --review-deferred + --strict refused directly (contradiction in terms) ---------
        led(world_dir, "work", "open", "item-f", "F")
        led(world_dir, "work", "claim", "item-f")
        rf_ = led(world_dir, "work", "close", "item-f", "dropped", "--review-deferred", "--strict")
        out_f = rf_.stdout + rf_.stderr
        ok_f = rf_.returncode != 0 and "contradiction in terms" in out_f
        check("f-strict-plus-deferred-refused", ok_f,
              f"exit={rf_.returncode} excerpt={out_f.strip()[-300:]!r}", failures)

        # --- g: strict close over an UNRESOLVED tree refused, naming the unresolved leaf -------
        led(world_dir, "work", "open", "root-g", "RootG")
        led(world_dir, "work", "claim", "root-g")
        led(world_dir, "work", "open", "child-g", "ChildG", "--parent", "root-g")
        # child-g left OPEN (unclaimed, unclosed) -- the unresolved leaf
        rg_ = led(world_dir, "work", "close", "root-g", "dropped", "--review-witness", "refg", "--strict")
        out_g = rg_.stdout + rg_.stderr
        ok_g = rg_.returncode != 0 and "child-g" in out_g and "not yet closed" in out_g
        check("g-strict-over-unresolved-tree-refused", ok_g,
              f"exit={rg_.returncode} names_child_g={'child-g' in out_g} excerpt={out_g.strip()[-400:]!r}",
              failures)

        # --- h: same strict close SUCCEEDS once the child is resolved (pure re-query, no stored
        # verdict -- close child-g witnessed, then retry root-g's strict close unchanged) -------
        led(world_dir, "work", "claim", "child-g")
        led(world_dir, "work", "close", "child-g", "dropped", "--review-witness", "refchildg")
        rh_ = led(world_dir, "work", "close", "root-g", "dropped", "--review-witness", "refg2", "--strict")
        ok_h = rh_.returncode == 0
        check("h-strict-succeeds-once-resolved", ok_h,
              f"exit={rh_.returncode} stderr_tail={(rh_.stdout + rh_.stderr).strip()[-200:]!r}", failures)

        # --- k: REGRESSION CASE for the out-of-frame hack-rationalization audit's finding (same
        # session, caught before this file's first commit): a first draft's dependency-leaf check
        # treated an antecedent as resolved once it had ANY close row, not once its OWN review
        # obligation was itself resolved -- so `A --depends-on B`, B closed --review-deferred
        # (undischarged), `A --strict` WRONGLY SUCCEEDED. This case pins the fix: B's own
        # outstanding obligation must be named as a blocker on A's strict close, with NO s28
        # parent edge involved at all (a pure work_depends_on chain) -----------------------------
        led(world_dir, "work", "open", "dep-k-b", "DepKB")
        led(world_dir, "work", "claim", "dep-k-b")
        led(world_dir, "work", "close", "dep-k-b", "dropped", "--review-deferred")
        led(world_dir, "work", "open", "dep-k-a", "DepKA")
        led(world_dir, "work", "claim", "dep-k-a")
        led(world_dir, "work", "depends", "dep-k-a", "dep-k-b")
        rk1_ = led(world_dir, "work", "close", "dep-k-a", "dropped", "--review-witness", "refka", "--strict")
        out_k1 = rk1_.stdout + rk1_.stderr
        ok_k1 = rk1_.returncode != 0 and "dep-k-b" in out_k1 and "deferred and undischarged" in out_k1
        check("k1-strict-over-unresolved-dependency-refused", ok_k1,
              f"exit={rk1_.returncode} names_antecedent={'dep-k-b' in out_k1} excerpt={out_k1.strip()[-350:]!r}",
              failures)
        # discharge dep-k-b's obligation (distinct actor), then retry -- must now succeed
        dep_k_b_close_id = psql_tuples(
            f"SELECT id FROM {schema}.ledger WHERE kind='work_closed' AND work_slug='dep-k-b';").stdout.strip()
        os.environ["LED_ACTOR"] = "reviewer2"
        led(world_dir, "review", dep_k_b_close_id, "attest", "self-review", "discharge dep-k-b for case k2")
        del os.environ["LED_ACTOR"]
        rk2_ = led(world_dir, "work", "close", "dep-k-a", "dropped", "--review-witness", "refka2", "--strict")
        ok_k2 = rk2_.returncode == 0
        check("k2-strict-over-dependency-succeeds-once-discharged", ok_k2,
              f"exit={rk2_.returncode} stderr_tail={(rk2_.stdout + rk2_.stderr).strip()[-200:]!r}", failures)

        # --- i: SQL floor vs ASP differential AGREE, on THIS world's live facts (both an
        # unresolved item (item-f is open+unclosed) and resolved trees (root-a, root-g) present) --
        # (clingo_run / ledger_floor imported at module top, per the lazy-import ban -- CLAUDE.md)

        def build_edb() -> str:
            def rows(sql: str) -> list[list[str]]:
                cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tA", "-c", sql])
                if cp.returncode != 0:
                    raise RuntimeError(cp.stdout + cp.stderr)
                return [r.split("|") for r in cp.stdout.splitlines() if r.strip()]

            lines = []
            for (s,) in rows(f"SELECT work_slug FROM {schema}.ledger WHERE kind='work_opened' ORDER BY id;"):
                lines.append(f"w_opened({clingo_run.quote_term(s)}).")
            for c, p in rows(f"SELECT work_slug, work_parent FROM {schema}.ledger WHERE kind='work_opened' AND work_parent IS NOT NULL ORDER BY id;"):
                lines.append(f"w_parent({clingo_run.quote_term(c)},{clingo_run.quote_term(p)}).")
            for s, rid, closer in rows(f"SELECT work_slug, id, actor FROM {schema}.ledger WHERE kind='work_closed' ORDER BY id;"):
                lines.append(f"w_closed({clingo_run.quote_term(s)},{int(rid)},{int(closer)}).")
            for (rid,) in rows(f"SELECT id FROM {schema}.ledger WHERE kind='work_closed' AND work_review_disposition='witnessed' ORDER BY id;"):
                lines.append(f"w_disposition({int(rid)},witnessed).")
            for (rid,) in rows(f"SELECT id FROM {schema}.ledger WHERE kind='work_closed' AND work_review_disposition='deferred' ORDER BY id;"):
                lines.append(f"w_disposition({int(rid)},deferred).")
            for (rid,) in rows(
                f"SELECT DISTINCT c.id FROM {schema}.ledger c "
                f"JOIN {schema}.ledger r ON r.regards = c.id "
                f"JOIN {schema}.review_detail rd ON rd.ledger_id = r.id "
                f"WHERE c.kind='work_closed' AND r.kind='review' AND rd.verdict='attest' AND r.actor <> c.actor "
                f"AND NOT EXISTS (SELECT 1 FROM {schema}.ledger s2 WHERE s2.supersedes = r.id) ORDER BY c.id;"
            ):
                lines.append(f"w_discharged({int(rid)}).")
            for d, a in rows(f"SELECT work_slug, work_depends_on FROM {schema}.ledger WHERE kind='work_depends_on' ORDER BY id;"):
                lines.append(f"w_dep({clingo_run.quote_term(d)},{clingo_run.quote_term(a)}).")
            return "\n".join(lines) + "\n"

        edb = build_edb()
        lp = WORK_REVIEW_LP
        asp_atoms = {a for a in clingo_run.run_clingo([lp], edb) if "(" in a}
        asp_atoms = {a for a in asp_atoms if a.split("(", 1)[0] in ledger_floor.WORK_REVIEW_PREDS}
        os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"] = PGDB, schema, kern
        try:
            sql_atoms = ledger_floor.work_review_floor_atoms(schema)
        finally:
            del os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"]
        only_asp, only_sql = asp_atoms - sql_atoms, sql_atoms - asp_atoms
        verdict = "AGREE" if not only_asp and not only_sql else "DIVERGE_DEFECT"
        has_unresolved = any(a.startswith("w_tree_unresolved(") for a in asp_atoms)
        ok_i = verdict == "AGREE" and len(asp_atoms) > 0 and has_unresolved
        check("i-differential-agree", ok_i,
              f"verdict={verdict} asp_n={len(asp_atoms)} sql_n={len(sql_atoms)} "
              f"has_unresolved_present={has_unresolved} "
              f"only_asp={sorted(only_asp)} only_sql={sorted(only_sql)}", failures)

        # --- j: `led work close` with NO review flags, against an s28-ONLY kernel (s29 not
        # applied), still succeeds exactly as before this delta -- a SEPARATE scaffold ----------
        print(f"== scaffolding a SEPARATE s28-only world {WORLD_PRE} (s29 deliberately NOT applied) ==")
        world_dir_pre, dep_pre = scaffold(WORLD_PRE)
        tmps.append(world_dir_pre.parent)
        led(world_dir_pre, "work", "open", "pre-item", "Pre")
        led(world_dir_pre, "work", "claim", "pre-item")
        rj_ = led(world_dir_pre, "work", "close", "pre-item", "dropped", "--witness", "shipwit")
        ok_j = rj_.returncode == 0
        check("j-pre-s29-led-close-unaffected", ok_j,
              f"exit={rj_.returncode} stderr_tail={(rj_.stdout + rj_.stderr).strip()[-200:]!r}", failures)

    finally:
        teardown_all()
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- s29 obligation item-key + typed close + obligation-tree guarantee "
          "both-polarity proof (review-silent close refused / both-constructors refused / "
          "witnessed-without-ref refused / witnessed-with-ref accepted / deferred creates and "
          "discharges the item-keyed obligation / strict+deferred refused / strict-over-"
          "unresolved-tree refused naming the leaf / strict succeeds once resolved / strict-over-"
          "unresolved-DEPENDENCY refused+succeeds (the audit-caught regression case) / SQL-ASP "
          "differential AGREE / pre-s29 led close unaffected), zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
