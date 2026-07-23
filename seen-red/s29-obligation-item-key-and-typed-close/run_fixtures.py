#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for kernel/lineage/s29-obligation-item-key-and-typed-
close.sql + bootstrap/templates/led.tmpl's `work close` two-constructor change + `work review-gap`
(design/MAINT-COUNTERSIGN-CLOSE-SEMANTICS-SPEC.md, Fable-authored spec, RATIFIED 2026-07-14).
Real infra, no mocks: a throwaway `--new-world` scaffold in the toy db, with s29 GUARANTEED
present on the resulting schema/kern -- via s29's own `.detect.sql` (the same live-catalog check
`./migrate` itself uses, kernel/lineage/s29-obligation-item-key-and-typed-close.detect.sql), never
via a hardcoded assumption about which head `--new-world` stops at. History (ledger finding row
1143, s31 builder, dispatched by decision row 1151): a first draft of this file assumed
`--new-world` stopped at s28 and unconditionally re-applied s29 itself; once new-project.sh's own
LINEAGE_CHAIN grew past s29 (first s30, then s31), that unconditional re-apply started failing at
s29's ledger_current re-issue ("cannot drop columns from view") because s29 was already live.
Fixed here to be robust to FUTURE chain growth too: after scaffolding, this file runs s29's
`.detect.sql` against the live schema/kern and only issues the explicit `psql -f` apply when
detect says s29 is NOT yet present -- so this fixture keeps working whether `--new-world` stops
short of s29 (apply happens explicitly, as originally written) or already carries s29 and
everything past it (s30/s31/... -- the apply is skipped, no re-issue collision) -- torn down
before AND after this file runs so re-running it never leaves residue.

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
  j-pre-s29-led-close-unaffected    -- RETIRED (cli-rebase-fixture-repairs, ledger row 1170):
                                        used to prove `led work close` with no review flags at
                                        all still succeeds against a kernel that predates s29
                                        (has_review_disposition_col's FALSE branch), on a
                                        SEPARATE classic scaffold applying s15..s28 only (no
                                        s29, and -- an accident of that list's own age, not this
                                        delta's doing -- no s40..s43 either). The served `led` is
                                        now s43-ONLY: there is no code path left, direct-INSERT
                                        or otherwise, that can write through a kernel lacking
                                        kernel.ledger_write, so this case's own world can no
                                        longer produce ANY led write to observe, success or
                                        refusal -- retired rather than reshaped into a case that
                                        would actually be testing something else (the generic
                                        pre-s43 capability_absent refusal every other pre-s43
                                        world already gets, unrelated to s29's own has_review_
                                        disposition_col branch this case existed to prove).
                                        Extending the classic list to s15..s28+s30..s43 (skipping
                                        ONLY s29) was considered and rejected here: verifying s30
                                        onward tolerates s29's absence is a real kernel-lineage
                                        question, out of scope for a fixture-transport migration
                                        (CLAUDE.md: kernel/lineage changes need a ratified spec).
  l-close-bad-resolution-refused-client-side -- item led-work-close-resolution-teaching (row
                                        1613): a non-enum resolution is refused CLIENT-SIDE,
                                        naming the closed vocabulary, never surfacing the raw
                                        postgres work_resolution_check constraint-violation text.
  m-close-shipped-no-witness-refused-client-side -- resolution=shipped with no --witness is
                                        refused CLIENT-SIDE, naming the requirement, never the
                                        raw work_shipped_requires_witness constraint text.
  n-close-shipped-with-witness-accepted -- the SAME shipped act WITH --witness succeeds --
                                        the two new refusals above are teaching, not a new gate.

Usage: python3 seen-red/s29-obligation-item-key-and-typed-close/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import importlib.util
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
S29_DETECT = REPO / "kernel" / "lineage" / "s29-obligation-item-key-and-typed-close.detect.sql"
WORK_REVIEW_LP = REPO / "engine" / "lp" / "work_review.lp"

sys.path.insert(0, str(REPO / "engine"))
import clingo_run  # noqa: E402  (engine/clingo_run.py, via the sys.path bridge above)
import ledger_floor  # noqa: E402  (engine/ledger_floor.py -- work_review_floor_atoms, WORK_REVIEW_PREDS)

sys.path.insert(0, str(REPO / "seen-red"))  # for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402

# cli-rebase-fixture-repairs (ledger row 1170): REUSE (ADR-0012 P1) serve_existing_world from
# seen-red/boundary-service/run_fixtures.py -- the served `led` shim refuses every write until
# this deployment.json gains boundary_url/boundary_deployment.
_BS_SPEC = importlib.util.spec_from_file_location(
    "boundary_service_fixtures", REPO / "seen-red" / "boundary-service" / "run_fixtures.py")
assert _BS_SPEC is not None and _BS_SPEC.loader is not None
bs_fixtures = importlib.util.module_from_spec(_BS_SPEC)
sys.modules["boundary_service_fixtures"] = bs_fixtures
_BS_SPEC.loader.exec_module(bs_fixtures)

# a hardcoded host literal is exactly the hazard seen-red/_fixture_env.py exists to close (found
# in reach while migrating this fixture onto the served path, fixed here per CLAUDE.md's
# engineering-responsibility clause rather than left for the next caller to trip on).
PGHOST, PGDB = fixture_pghost(), "toy"
WORLD = "s29fxprobe"


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


def led(world_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return sh(["bash", str(world_dir / "led"), *args], cwd=str(world_dir))


def psql_tuples(sql: str) -> subprocess.CompletedProcess[str]:
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])


def s29_already_applied(schema: str, kern: str, role: str) -> bool:
    """Runs s29's own `.detect.sql` (the same live-catalog check `./migrate` uses via
    bootstrap/migrate_core.py::_run_detect) against schema/kern/role and returns whether it
    reports s29's objects already present -- `-tA` so the one boolean `applied` column prints as
    a bare `t`/`f`. This is the single source of truth for whether `scaffold()`'s `--new-world`
    run already carried s29 (true today, since new-project.sh's LINEAGE_CHAIN runs s15..s31) or
    needs it applied explicitly (true if that chain ever regresses to stop short of s29 again)."""
    proc = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tA", "-v", "ON_ERROR_STOP=1",
               "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}",
               "-f", str(S29_DETECT)])
    if proc.returncode != 0:
        raise RuntimeError(f"s29 DETECT FAILED ({schema}): {proc.stdout[-1500:]} {proc.stderr[-1500:]}")
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip() != ""]
    return bool(lines) and all(ln == "t" for ln in lines)


def scaffold(world: str) -> tuple[Path, dict, subprocess.Popen]:
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
    proc = bs_fixtures.serve_existing_world(world_dir / "deployment.json", tmp)
    dep = json.loads((world_dir / "deployment.json").read_text(encoding="utf-8"))
    return world_dir, dep, proc


def main() -> int:
    teardown_all()
    failures: list[str] = []
    tmps: list[Path] = []

    try:
        # --- scaffold via --new-world (whatever head new-project.sh's LINEAGE_CHAIN currently
        # reaches), then apply s29 explicitly ONLY IF s29's own .detect.sql says it isn't already
        # live -- robust to the chain's head moving in either direction over time -------------
        print(f"== scaffolding throwaway --new-world {WORLD} ==")
        world_dir, dep, proc = scaffold(WORLD)
        tmps.append(world_dir.parent)
        schema, kern, role = dep["schema"], dep["kern"], dep["role"]
        print(f"  scaffold OK (schema={schema} kern={kern} role={role}).\n")

        if s29_already_applied(schema, kern, role):
            print(f"== s29's own .detect.sql reports it is ALREADY LIVE on {schema}/{kern}/{role} "
                  f"(--new-world's chain reached past s29) -- skipping the explicit re-apply ==\n")
        else:
            print(f"== s29 not yet present on {schema}/{kern}/{role} -- applying "
                  f"s29-obligation-item-key-and-typed-close.sql explicitly ==")
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
        # --type blocks-close (kernel/lineage/s30-typed-dependency-edges.sql, typed dependency
        # edges): as of the s30 delta now permanently wired into --new-world's own
        # chain (LINEAGE_CHAIN), an UNTYPED `work depends` edge is "informs by omission" and no
        # longer gates a strict close on its own -- only `--type blocks-close` is conjoined into
        # the obligation AND-tree. k1/k2's own intent (an unresolved DEPENDENCY, not an s28
        # parent edge, blocks strict close) is unchanged; expressing "this edge is load-bearing"
        # now requires the explicit type this world's kernel (s30-and-later) provides.
        led(world_dir, "work", "depends", "dep-k-a", "dep-k-b", "--type", "blocks-close")
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

        # --- j: RETIRED, see this file's own module docstring for the named reason (cli-rebase-
        # fixture-repairs, ledger row 1170) -----------------------------------------------------

        # --- l/m/n: item led-work-close-resolution-teaching (ledger row 1613, witnessed
        # 2026-07-18: a non-enum resolution / a shipped resolution with no witness used to
        # surface a RAW postgres CHECK-violation error -- work_resolution_check / work_shipped_
        # requires_witness, both kernel/lineage/s22-work-item-ledger.sql -- instead of a verb-
        # level refusal naming the closed vocabulary). New client-side checks in `work close`,
        # BEFORE any DB round trip: (l) a non-enum resolution is refused naming the vocabulary;
        # (m) resolution=shipped with no --witness is refused naming the requirement; (n) the
        # SAME shipped act with --witness succeeds -- the two refusals are teaching, not a new
        # gate, so the legal case is unaffected. Exercised on the SAME s29 world, a fresh item
        # so it does not interact with root-a's own state above.
        led(world_dir, "work", "open", "resw-item", "Resolution-witness teaching probe")
        led(world_dir, "work", "claim", "resw-item")

        rl_ = led(world_dir, "work", "close", "resw-item", "bogus-resolution", "--review-deferred")
        out_l = rl_.stdout + rl_.stderr
        ok_l = (rl_.returncode != 0
                and "shipped, superseded" in out_l
                and "bogus-resolution" in out_l
                # the RAW postgres error shape (a bare "ERROR: new row for relation ... violates
                # check constraint" with no teach-text) must NOT be what the caller sees -- the
                # CLI's own client-side refusal fires BEFORE any DB round trip, so this never
                # reaches psql at all. The constraint's NAME legitimately appears in the CLI's own
                # teach-text (cited as the authority this is a transcription of, ADR-0012 P1) --
                # it is the RAW psql/postgres framing that must be absent, not the bare name.
                and "violates check constraint" not in out_l
                and "ERROR:" not in out_l)
        check("l-close-bad-resolution-refused-client-side", ok_l,
              f"exit={rl_.returncode} excerpt={out_l.strip()[-400:]!r}", failures)

        rm_ = led(world_dir, "work", "close", "resw-item", "shipped", "--review-deferred")
        out_m = rm_.stdout + rm_.stderr
        # cli-rebase-fixture-repairs (row 1170): the client-side teach-text no longer cites the
        # kernel constraint's NAME literally ("resolution=shipped REQUIRES a non-blank --witness
        # <ref>" -- plain English, the same requirement) -- wording drift, not a functional
        # regression (still a client-side refusal, before any DB round trip, still names
        # --witness); the exact-string check is updated to match, the underlying behavior it was
        # written to prove (refused, client-side, naming the requirement) is unchanged.
        ok_m = (rm_.returncode != 0
                and "REQUIRES a non-blank --witness" in out_m
                and "--witness" in out_m
                and "violates check constraint" not in out_m)
        check("m-close-shipped-no-witness-refused-client-side", ok_m,
              f"exit={rm_.returncode} excerpt={out_m.strip()[-400:]!r}", failures)

        rn_ = led(world_dir, "work", "close", "resw-item", "shipped", "--witness", "commit-resw1",
                  "--review-deferred")
        wic_n = psql_tuples(
            f"SET ROLE {role}; SET search_path = {schema}, {kern}; "
            f"SELECT state, resolution FROM work_item_current WHERE slug='resw-item';")
        ok_n = rn_.returncode == 0 and "closed|shipped" in wic_n.stdout
        check("n-close-shipped-with-witness-accepted", ok_n,
              f"exit={rn_.returncode} work_item_current={wic_n.stdout.strip()!r} "
              f"excerpt={(rn_.stdout + rn_.stderr).strip()[-200:]!r}", failures)

    finally:
        try:
            bs_fixtures.stop_server(proc)
        except NameError:
            pass  # scaffold itself failed before `proc` was ever assigned
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
          "differential AGREE; j-pre-s29-led-close-unaffected RETIRED, see module docstring), "
          "zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
