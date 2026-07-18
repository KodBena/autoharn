#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T16:15:17Z
#   last-change: 2026-07-18T16:15:17Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures -- both-polarity live proof for ledger item `resolve-violation-class-ambiguity`
(gates/fixture_census.py REGISTRY entry "resolve-violation-class-ambiguity").

THE DEFECT (pre-existing CLI gap flagged by the v3 amendment builder, pre-dates s37's own v3
amendment -- same target_id computation in v2): a target can match MORE THAN ONE
work_item_violations class at once -- concretely, kernel/lineage/s37-violation-disposition.sql's
own view computes 'dependency_cycle' and 'blocks_close_cycle' from the SAME underlying blocks-
close edges (work_edge_blocks_close), with the SAME target_id formula (the current work_opened
row of the cycle-root slug) -- so a live blocks-close cycle produces BOTH labels for the same
target_id. `led work resolve-violation <target> ...` used to refuse this shape with "matches more
than one class... write the work_violation_disposition row directly via SQL, naming the intended
class explicitly" -- no way forward through the sanctioned CLI at all (the commissioning brief's
own words: "supersede-cascade's own internal call hits it, so the cascade cannot complete through
the CLI on that shape").

THE FIX (bootstrap/templates/led.tmpl, `work resolve-violation`): a new `--class <name>` flag
disambiguates -- the ambiguity refusal now NAMES the matched classes and the corrective form; a
--class matching one of them is used directly (validated against the actual matched set, never a
blind pass-through); a --class that does not match, or that is combined with --supersedes (whose
own branch derives class deterministically and would silently ignore --class), is refused
teaching why.

CONSTRUCTING A LIVE AMBIGUOUS TARGET: the kernel's own construction-time trigger
(validate_work_item) refuses a blocks-close cycle at INSERT time (s30's own cycle-refusal), so
the SECOND edge of a 2-cycle cannot be written through the ordinary CLI/boundary path at all --
exactly the shape the commissioning brief's own builder hit ("the builder finished the scratch
witness via raw SQL, fine for witnessing, but an operator would be stuck"). This fixture follows
the SAME precedent for its own SETUP only (never for the assertions under test): the second edge
is inserted directly as the postgres superuser with ONLY the `validate_work_item` trigger
disabled for that one INSERT (re-enabled immediately after) -- every OTHER trigger (row-hash,
append-only, actor resolution, ...) stays live, so the seeded row is otherwise indistinguishable
from an ordinary one. This is setup-only scaffolding to reach a real, kernel-representable state
that the CLI's own OTHER construction-time refusal (not the one under test here) currently
forecloses -- the ambiguity itself, once reached, is exactly what a live world could carry if two
blocks-close edges landed in an order the trigger did not catch (e.g. a future migration, or a
kernel predating s30's cycle check).

CASES (all live subprocess/psql runs against one real scratch --new-world deployment):

  ADOPT                        -- bootstrap/new-project.sh --new-world stands up a full-chain
                                   scratch deployment (s37 present).
  SETUP-AMBIGUOUS-TARGET       -- two work items, a blocks-close cycle between them (second edge
                                   seeded via the documented trigger-disable precedent above);
                                   `led work violations` confirms ONE target_id carries BOTH
                                   'dependency_cycle' and 'blocks_close_cycle'.
  RED-NO-CLASS-NO-WAY-FORWARD  -- (banked in red.txt, not re-run here) the PRE-FIX refusal names
                                   no classes and no --class flag exists at all.
  GREEN-AMBIGUOUS-NO-CLASS-TEACHES -- resolve-violation on the ambiguous target, no --class:
                                   REFUSED, naming BOTH matched classes and the --class flag as
                                   the way forward -- never a bare "cannot disambiguate".
  GREEN-CLASS-DISAMBIGUATES    -- the SAME target with --class <one of the matched classes>:
                                   succeeds, the written row's own work_violation_class matches
                                   exactly what was asked.
  RED-WRONG-CLASS-REFUSED      -- --class naming a class NOT among the matches: REFUSED, naming
                                   the actual matched classes.
  RED-CLASS-PLUS-SUPERSEDES-REFUSED -- --class combined with --supersedes: REFUSED (the
                                   correction path derives class deterministically; --class
                                   would be silently ignored there -- refused instead).
  GREEN-SINGLE-MATCH-UNCHANGED -- an ORDINARY, non-ambiguous target (one class only) is
                                   UNCHANGED by this item: no --class needed, the write succeeds
                                   exactly as before.
  RED-SINGLE-MATCH-WRONG-CLASS -- the SAME single-match target with a --class that does NOT
                                   match its one class: REFUSED, naming the actual class.

Usage: python3 seen-red/resolve-violation-class-ambiguity/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
PGHOST, DB = fixture_pghost(), "toy"
WORLD = "rvcafixture"
TAG = f"seen-red-resolve-violation-class-ambiguity-{int(time.time())}"


def _psql(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["psql", "-h", PGHOST, "-d", DB, *args], capture_output=True, text=True)


def _psql_tuples(sql: str) -> str:
    r = _psql("-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql)
    if r.returncode != 0:
        raise RuntimeError(f"psql failed: {sql!r}\n{r.stdout}\n{r.stderr}")
    return r.stdout.strip()


def _drop_scratch() -> None:
    _psql("-v", "ON_ERROR_STOP=0", "-q",
          "-c", f"DROP SCHEMA IF EXISTS {WORLD} CASCADE;",
          "-c", f"DROP SCHEMA IF EXISTS {WORLD}_kernel CASCADE;",
          "-c", f"DROP ROLE IF EXISTS {WORLD}_rw;")


def _run(dest: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(dest / args[0]), *args[1:]], capture_output=True, text=True, cwd=str(dest))


def main() -> int:
    failures: list[str] = []

    _drop_scratch()
    tmpdir = Path(tempfile.mkdtemp(prefix="resolve-violation-class-ambiguity-fixture-"))
    dest = tmpdir / WORLD

    # --------------------------------------------------------------------------------- ADOPT
    r = subprocess.run(["bash", str(NEW_PROJECT), str(dest), "--new-world", WORLD,
                         "--db", DB, "--host", PGHOST], capture_output=True, text=True, cwd=str(REPO))
    for verb in ("led", "judge", "pickup"):
        p = dest / verb
        if p.exists():
            p.chmod(0o755)
    ok = r.returncode == 0 and (dest / "deployment.json").exists()
    if not ok:
        failures.append(f"ADOPT: exit={r.returncode}\nSTDOUT:\n{r.stdout[-1500:]}\nSTDERR:\n{r.stderr[-1500:]}")
    print(f"ADOPT: new-project.sh --new-world exit={r.returncode} "
          f"deployment.json={(dest / 'deployment.json').exists()} -- {'PASS' if ok else 'FAIL'}")
    if not ok:
        print(f"\nADOPT FAILED, aborting -- scratch left standing:\n  tempdir: {tmpdir}")
        for f in failures:
            print(f"\n!! {f}")
        return 1

    try:
        # ---------------------------------------------------------- SETUP-AMBIGUOUS-TARGET
        cyclea, cycleb = f"{TAG}-cyclea", f"{TAG}-cycleb"
        _run(dest, "led", "work", "open", cyclea, "cycle item a")
        _run(dest, "led", "work", "open", cycleb, "cycle item b")
        r1 = _run(dest, "led", "work", "depends", cyclea, cycleb, "--type", "blocks-close")
        # the SECOND edge of the cycle is refused at construction (s30's own cycle-check,
        # kernel/lineage/s30-typed-dependency-edges.sql) through the sanctioned CLI/boundary
        # path -- confirmed here, not assumed, before falling back to the documented setup-only
        # trigger-disable precedent (this file's own module docstring).
        r2_refused = _run(dest, "led", "work", "depends", cycleb, cyclea, "--type", "blocks-close")
        cycle_refused_at_construction = r2_refused.returncode != 0 and "cycle" in r2_refused.stderr
        # SETUP-ONLY raw seed (module docstring's own documented precedent): disable
        # validate_work_item for exactly ONE insert, re-enable immediately after. Every other
        # trigger (row-hash, append-only, actor, ...) stays live for this row.
        _psql("-v", "ON_ERROR_STOP=1", "-c",
              f"ALTER TABLE {WORLD}.ledger DISABLE TRIGGER validate_work_item;")
        seed = _psql(
            "-v", "ON_ERROR_STOP=1", "-c",
            f"INSERT INTO {WORLD}.ledger (kind, statement, work_slug, work_depends_on, edge_type, actor) "
            f"VALUES ('work_depends_on', 'work_depends_on: {cycleb} depends on {cyclea} "
            f"(seen-red setup-only seed, trigger disabled for this ONE insert)', "
            f"'{cycleb}', '{cyclea}', 'blocks-close', 1);")
        _psql("-v", "ON_ERROR_STOP=1", "-c",
              f"ALTER TABLE {WORLD}.ledger ENABLE TRIGGER validate_work_item;")
        seed_ok = seed.returncode == 0

        violations = _run(dest, "led", "work", "violations")
        target_row = _psql_tuples(
            f"SELECT target_id FROM {WORLD}.work_item_violations "
            f"WHERE slug = '{cyclea}' GROUP BY target_id "
            f"HAVING count(DISTINCT violation) > 1 LIMIT 1;")
        ambiguous_target = target_row if target_row else None
        matched_classes = ""
        if ambiguous_target:
            matched_classes = _psql_tuples(
                f"SELECT string_agg(DISTINCT violation, ',' ORDER BY violation) "
                f"FROM {WORLD}.work_item_violations WHERE target_id = {ambiguous_target};")
        ok_setup = (r1.returncode == 0 and cycle_refused_at_construction and seed_ok
                    and ambiguous_target is not None and "," in matched_classes)
        if not ok_setup:
            failures.append(f"SETUP-AMBIGUOUS-TARGET: first_edge_exit={r1.returncode} "
                             f"cycle_refused_at_construction={cycle_refused_at_construction} "
                             f"seed_ok={seed_ok} ambiguous_target={ambiguous_target!r} "
                             f"matched_classes={matched_classes!r}\n"
                             f"violations output:\n{violations.stdout}")
        print(f"SETUP-AMBIGUOUS-TARGET: first_edge_exit={r1.returncode} "
              f"cycle_refused_at_construction={cycle_refused_at_construction} seed_ok={seed_ok} "
              f"ambiguous_target={ambiguous_target} matched_classes={matched_classes!r} -- "
              f"{'PASS' if ok_setup else 'FAIL'}")
        if not ok_setup:
            print(f"\nSETUP FAILED, aborting -- scratch left standing:\n  tempdir: {tmpdir}")
            for f in failures:
                print(f"\n!! {f}")
            return 1

        classes_list = sorted(matched_classes.split(","))

        # ------------------------------------------------------- GREEN-AMBIGUOUS-NO-CLASS-TEACHES
        before = _psql_tuples(f"SELECT count(*) FROM {WORLD}.ledger;")
        r = _run(dest, "led", "work", "resolve-violation", ambiguous_target, "retired",
                 f"{TAG}: ambiguous target, no --class", "--review-deferred")
        after = _psql_tuples(f"SELECT count(*) FROM {WORLD}.ledger;")
        refused = r.returncode != 0
        names_both = all(c in r.stderr for c in classes_list)
        teaches_class_flag = "--class" in r.stderr
        unchanged = before == after
        ok = refused and names_both and teaches_class_flag and unchanged
        if not ok:
            failures.append(f"GREEN-AMBIGUOUS-NO-CLASS-TEACHES: exit={r.returncode} "
                             f"refused={refused} names_both={names_both} "
                             f"teaches_class_flag={teaches_class_flag} before={before} "
                             f"after={after}\nSTDERR:\n{r.stderr}")
        print(f"GREEN-AMBIGUOUS-NO-CLASS-TEACHES: exit={r.returncode} refused={refused} "
              f"names_both_classes={names_both} teaches_class_flag={teaches_class_flag} "
              f"row-count before={before} after={after} (unchanged={unchanged}) -- "
              f"{'PASS' if ok else 'FAIL'}")

        # ------------------------------------------------------------- GREEN-CLASS-DISAMBIGUATES
        chosen_class = classes_list[0]
        before = _psql_tuples(f"SELECT count(*) FROM {WORLD}.ledger;")
        r = _run(dest, "led", "work", "resolve-violation", ambiguous_target, "retired",
                 f"{TAG}: disambiguated via --class", "--review-deferred", "--class", chosen_class)
        after = _psql_tuples(f"SELECT count(*) FROM {WORLD}.ledger;")
        accepted = r.returncode == 0
        grew = after == str(int(before) + 1)
        written_class = ""
        if accepted:
            written_class = _psql_tuples(
                f"SELECT work_violation_class FROM {WORLD}.ledger "
                f"WHERE kind='work_violation_disposition' AND work_violation_target_id = {ambiguous_target} "
                f"ORDER BY id DESC LIMIT 1;")
        ok = accepted and grew and written_class == chosen_class
        if not ok:
            failures.append(f"GREEN-CLASS-DISAMBIGUATES: exit={r.returncode} accepted={accepted} "
                             f"grew={grew} chosen_class={chosen_class!r} "
                             f"written_class={written_class!r}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
        print(f"GREEN-CLASS-DISAMBIGUATES: exit={r.returncode} accepted={accepted} "
              f"chosen_class={chosen_class} written_class={written_class} row-count "
              f"before={before} after={after} (grew-by-one={grew}) -- {'PASS' if ok else 'FAIL'}")

        # ------------------------------------------------------------------ RED-WRONG-CLASS-REFUSED
        before = _psql_tuples(f"SELECT count(*) FROM {WORLD}.ledger;")
        r = _run(dest, "led", "work", "resolve-violation", ambiguous_target, "retired",
                 f"{TAG}: wrong --class", "--review-deferred", "--class", "bogus_class_name")
        after = _psql_tuples(f"SELECT count(*) FROM {WORLD}.ledger;")
        refused = r.returncode != 0
        names_actual = all(c in r.stderr for c in classes_list)
        unchanged = before == after
        ok = refused and names_actual and unchanged
        if not ok:
            failures.append(f"RED-WRONG-CLASS-REFUSED: exit={r.returncode} refused={refused} "
                             f"names_actual={names_actual} before={before} after={after}\n"
                             f"STDERR:\n{r.stderr}")
        print(f"RED-WRONG-CLASS-REFUSED: exit={r.returncode} refused={refused} "
              f"names_actual_classes={names_actual} row-count before={before} after={after} "
              f"(unchanged={unchanged}) -- {'PASS' if ok else 'FAIL'}")

        # ------------------------------------------------------ RED-CLASS-PLUS-SUPERSEDES-REFUSED
        # the second matched class is still unresolved (only the first was disposed of above) --
        # use it as a fresh, still-ambiguous-eligible target for this combination probe (the
        # combination is refused regardless of whether --supersedes names a real row: the check
        # fires on flag PRESENCE, before either flag's own value is dereferenced).
        second_class = classes_list[1] if len(classes_list) > 1 else classes_list[0]
        before = _psql_tuples(f"SELECT count(*) FROM {WORLD}.ledger;")
        r = _run(dest, "led", "work", "resolve-violation", ambiguous_target, "retired",
                 f"{TAG}: class+supersedes contradiction", "--review-deferred",
                 "--class", second_class, "--supersedes", "1")
        after = _psql_tuples(f"SELECT count(*) FROM {WORLD}.ledger;")
        refused = r.returncode != 0
        teaches = "--class" in r.stderr and "--supersedes" in r.stderr
        unchanged = before == after
        ok = refused and teaches and unchanged
        if not ok:
            failures.append(f"RED-CLASS-PLUS-SUPERSEDES-REFUSED: exit={r.returncode} "
                             f"refused={refused} teaches={teaches} before={before} after={after}\n"
                             f"STDERR:\n{r.stderr}")
        print(f"RED-CLASS-PLUS-SUPERSEDES-REFUSED: exit={r.returncode} refused={refused} "
              f"teaches={teaches} row-count before={before} after={after} "
              f"(unchanged={unchanged}) -- {'PASS' if ok else 'FAIL'}")

        # ------------------------------------------------------------ GREEN-SINGLE-MATCH-UNCHANGED
        # an ORDINARY orphaned_by_retraction target (one class only): a fresh item, opened then
        # its own opening act retracted, leaving its claim as a single-class orphan.
        single_slug = f"{TAG}-single"
        _run(dest, "led", "work", "open", single_slug, "single-class probe")
        _run(dest, "led", "work", "claim", single_slug)
        open_id = _psql_tuples(
            f"SELECT id FROM {WORLD}.ledger_current WHERE kind='work_opened' AND work_slug='{single_slug}';")
        _run(dest, "led", "work", "open", f"{single_slug}-redo", "single-class probe redo",
             "--supersedes", open_id, "--refs", f"row:{open_id}")
        single_target = _psql_tuples(
            f"SELECT target_id FROM {WORLD}.work_item_violations WHERE slug='{single_slug}' LIMIT 1;")
        single_class = _psql_tuples(
            f"SELECT violation FROM {WORLD}.work_item_violations WHERE slug='{single_slug}' LIMIT 1;")
        before = _psql_tuples(f"SELECT count(*) FROM {WORLD}.ledger;")
        r = _run(dest, "led", "work", "resolve-violation", single_target, "retired",
                 f"{TAG}: single-match, no --class needed", "--review-deferred")
        after = _psql_tuples(f"SELECT count(*) FROM {WORLD}.ledger;")
        accepted = r.returncode == 0
        grew = after == str(int(before) + 1)
        ok = accepted and grew and single_target and single_class
        if not ok:
            failures.append(f"GREEN-SINGLE-MATCH-UNCHANGED: exit={r.returncode} accepted={accepted} "
                             f"grew={grew} single_target={single_target!r} "
                             f"single_class={single_class!r}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
        print(f"GREEN-SINGLE-MATCH-UNCHANGED: exit={r.returncode} accepted={accepted} "
              f"single_target={single_target} single_class={single_class} row-count "
              f"before={before} after={after} (grew-by-one={grew}) -- {'PASS' if ok else 'FAIL'}")

        # ------------------------------------------------------------ RED-SINGLE-MATCH-WRONG-CLASS
        single_slug2 = f"{TAG}-single2"
        _run(dest, "led", "work", "open", single_slug2, "single-class probe 2")
        _run(dest, "led", "work", "claim", single_slug2)
        open_id2 = _psql_tuples(
            f"SELECT id FROM {WORLD}.ledger_current WHERE kind='work_opened' AND work_slug='{single_slug2}';")
        _run(dest, "led", "work", "open", f"{single_slug2}-redo", "single-class probe 2 redo",
             "--supersedes", open_id2, "--refs", f"row:{open_id2}")
        single_target2 = _psql_tuples(
            f"SELECT target_id FROM {WORLD}.work_item_violations WHERE slug='{single_slug2}' LIMIT 1;")
        single_class2 = _psql_tuples(
            f"SELECT violation FROM {WORLD}.work_item_violations WHERE slug='{single_slug2}' LIMIT 1;")
        before = _psql_tuples(f"SELECT count(*) FROM {WORLD}.ledger;")
        r = _run(dest, "led", "work", "resolve-violation", single_target2, "retired",
                 f"{TAG}: single-match, wrong --class", "--review-deferred",
                 "--class", "definitely_not_the_real_class")
        after = _psql_tuples(f"SELECT count(*) FROM {WORLD}.ledger;")
        refused = r.returncode != 0
        names_actual2 = single_class2 in r.stderr
        unchanged = before == after
        ok = refused and names_actual2 and unchanged and single_target2 and single_class2
        if not ok:
            failures.append(f"RED-SINGLE-MATCH-WRONG-CLASS: exit={r.returncode} refused={refused} "
                             f"names_actual2={names_actual2} single_target2={single_target2!r} "
                             f"single_class2={single_class2!r} before={before} after={after}\n"
                             f"STDERR:\n{r.stderr}")
        print(f"RED-SINGLE-MATCH-WRONG-CLASS: exit={r.returncode} refused={refused} "
              f"names_actual_class={names_actual2} row-count before={before} after={after} "
              f"(unchanged={unchanged}) -- {'PASS' if ok else 'FAIL'}")

    finally:
        _drop_scratch()
        shutil.rmtree(tmpdir, ignore_errors=True)

    if failures:
        print(f"\nresolve-violation-class-ambiguity fixture: {len(failures)} FAILURE(S)")
        for f in failures:
            print(f"\n!! {f}")
        return 1
    print("\nresolve-violation-class-ambiguity fixture: all cases PASS, scratch substrate torn "
          "down to zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
