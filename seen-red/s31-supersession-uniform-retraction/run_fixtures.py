#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T20:21:09Z
#   last-change: 2026-07-18T16:13:01Z
#   contributors: a857c93d/main, ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for kernel/lineage/s31-supersession-uniform-retraction.sql
(design/FABLE-SUPERSESSION-UNIFORM-RETRACTION-SPEC.md, Fable-authored, RATIFIED 2026-07-15;
ledger item supersession-semantics-closure) + gates/ledger_reader_allowlist.py (the standing
allowlist detect) + the engine companion (work_items.lp / work_review.lp composed with
ledger_tnow.lp's supersession closure; ledger_floor.py's matching floor updates).

Real infra, no mocks: a CLASSIC-mode scaffold (explicit --schema/--kern/--role, no automatic
kernel apply -- s30's own scaffold_classic idiom, one delta later) followed by a MANUAL
s15..s31 apply, in the TOY db, torn down before AND after so re-running leaves no residue.
s31 is deliberately NOT in new-project.sh's LINEAGE_CHAIN yet (the orchestrator lands that at
the seam, per the s28 precedent), so classic+manual is the honest wiring for this witness.

Cases (the ratified spec's sec-5 acceptance list, every polarity):
  a-retracted-close-reopens         -- superseding a work_closed row makes the item read OPEN
                                       again in work_item_current (resolution/witness gone).
  a2-composite-ancestor             -- UNEXERCISED, concrete blocker: the composite-discharge
                                       mechanism (FABLE-COMPOSITE-DISCHARGE-SPEC) is DRAFT,
                                       unratified, unbuilt -- no work_discharge/effective_state
                                       exists in any kernel; the polarity has no substrate.
  b-retracted-claim-unclaims        -- superseding a work_claimed row reads claimant NULL.
  c-retracted-edge-stops-gating     -- a blocks-close edge blocks a strict close (refusal names
                                       the antecedent); superseding the EDGE row makes the SAME
                                       strict close succeed; the edge row + its superseder stay
                                       visible in raw history.
  d-retracted-open-burns-slug       -- superseding a work_opened row: the item leaves
                                       work_item_current; its surviving claim surfaces as
                                       orphaned_by_retraction; re-opening the SAME slug is
                                       REFUSED (duplicate-open, slug burned) with teach-text
                                       naming the new-slug-citing-old redo idiom.
  e-reinstatement-free              -- superseding the SUPERSEDER does NOT revive the victim
                                       (case a's item still reads open).
  e2/e3-close-supersedes-wired      -- item led-work-close-supersedes-swallowed (row 1601):
                                       `led work close --supersedes <id>` used to SILENTLY
                                       SWALLOW the flag (case a's own retract() helper only ever
                                       proved a SEPARATE unrelated-kind row could retract a
                                       close, never that the correction itself could be a NEW
                                       work_closed row). e2: the flag before 'work' (the shared
                                       top-of-file position, the exact shape row 1601 used) --
                                       the supersedes column actually lands, the first close
                                       retracts, work_item_current reads the second close. e3:
                                       the SAME flag after 'close' (this item's own added case
                                       arm, mirroring `work open`/`work resolve-violation`'s own
                                       --supersedes position).
  f-history-readers-unchanged       -- the s26 row-hash chain RECOMPUTES clean across every row
                                       including retracted ones + their retractors; led --recent
                                       still SHOWS retracted rows, MARKED 'SUPERSEDED', never
                                       hidden.
  g-allowlist-gate-both-polarities  -- gates/ledger_reader_allowlist.py exits 0 green on the
                                       real chain AND refuses a deliberately misfactored scratch
                                       view under --red, teach-text naming both discharge paths.
  h-differential-agree              -- SQL floor (work_item_floor_atoms + work_review_floor_atoms)
                                       vs ASP (ledger_tnow.lp + work_items.lp + work_review.lp
                                       composed over ONE shared EDB) AGREE bit-identically on
                                       THIS world's facts -- a world containing every shape
                                       above (retracted open/claim/close/edge, a superseded
                                       superseder, surviving orphans). The STANDING ./judge
                                       differential is NOT wired to the work layer (ledger_edb's
                                       export carries no work_* family; ledger_differential's
                                       pipeline is single-program-typed) -- this bespoke
                                       differential is the same established idiom
                                       s22_work_item_fixture.py banked, extended to the s31
                                       composition; the standing wiring is a named separate seam.

Usage: python3 seen-red/s31-supersession-uniform-retraction/run_fixtures.py
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
GATE = REPO / "gates" / "ledger_reader_allowlist.py"
sys.path.insert(0, str(ENGINE))
sys.path.insert(0, str(REPO / "filing"))

import clingo_run  # noqa: E402  (engine/clingo_run.py, via the sys.path bridge above)
import ledger_floor  # noqa: E402  (engine/ledger_floor.py -- the SQL floor, producer one)
import pghost_resolve  # noqa: E402 (filing/pghost_resolve.py -- never a literal host default)

PGHOST, PGDB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"
WORLD = "s31fxprobe"

TNOW_LP = ENGINE / "lp" / "ledger_tnow.lp"
WORK_ITEMS_LP = ENGINE / "lp" / "work_items.lp"
WORK_REVIEW_LP = ENGINE / "lp" / "work_review.lp"

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
        f"DROP SCHEMA IF EXISTS {WORLD} CASCADE; DROP SCHEMA IF EXISTS {WORLD}_kernel CASCADE; "  # declared-drop: s31fxprobe (declared scratch/test reset)
        f"DROP OWNED BY {WORLD}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {WORLD}_rw;"])


def led(world_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return sh(["bash", str(world_dir / "led"), *args], cwd=str(world_dir))


def psql_tuples(sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"psql failed: {cp.stdout[-500:]} {cp.stderr[-500:]}")
    return cp.stdout.strip()


def scaffold_classic_s31(world: str) -> tuple[Path, dict]:
    """CLASSIC MODE + manual s15..s31 apply (s30's scaffold_classic idiom, one delta later)."""
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


def retract(world_dir: Path, row_id: str, why: str) -> subprocess.CompletedProcess[str]:
    """A retraction is an ordinary ledger row whose `supersedes` names its victim -- ANY kind may
    retract ANY kind (the ratified uniform-retraction fork: no kind-compatibility refusal).
    Flags go FIRST, before the kind (led.tmpl's top-of-file flag parser; a trailing flag is
    refused loudly, ledger item led-refs-flag-order-parser-bug)."""
    return led(world_dir, "--supersedes", row_id, "revision", why)


def quote(s: str) -> str:
    return clingo_run.quote_term(s)


def build_edb(schema: str) -> str:
    """The ONE shared EDB for the composed ASP run: ledger_tnow.lp's entry/supersedes families +
    work_items.lp's raw work families (row-id-carrying) + work_review.lp's s31 row-id families.
    Read from RAW ledger (both programs do their own in-force filtering via superseded/1 -- that
    is the composition under test; a pre-filtered export would hide it)."""
    lines: list[str] = []
    for row in psql_tuples(f"SELECT id, kind FROM {schema}.ledger ORDER BY id;").splitlines():
        rid, kind = row.split("|")
        lines.append(f"entry({rid},0,{kind},none,none,none).")
    for row in psql_tuples(
            f"SELECT id, supersedes FROM {schema}.ledger WHERE supersedes IS NOT NULL ORDER BY id;").splitlines():
        a, b = row.split("|")
        lines.append(f"supersedes({a},{b}).")
    for row in psql_tuples(
            f"SELECT work_slug, id FROM {schema}.ledger WHERE kind='work_opened' ORDER BY id;").splitlines():
        slug, rid = row.split("|")
        lines.append(f"work_opened({quote(slug)},{rid}).")
        lines.append(f"w_open({quote(slug)},{rid}).")
    for row in psql_tuples(
            f"SELECT work_slug, work_parent, id FROM {schema}.ledger "
            f"WHERE kind='work_opened' AND work_parent IS NOT NULL ORDER BY id;").splitlines():
        child, parent, rid = row.split("|")
        lines.append(f"work_parent_edge({quote(child)},{quote(parent)},{rid}).")
        lines.append(f"w_parent_e({quote(child)},{quote(parent)},{rid}).")
    for row in psql_tuples(
            f"SELECT work_slug, id FROM {schema}.ledger WHERE kind='work_claimed' ORDER BY id;").splitlines():
        slug, rid = row.split("|")
        lines.append(f"work_claimed({quote(slug)},{rid}).")
    for row in psql_tuples(
            f"SELECT work_slug, work_resolution, id, COALESCE(actor::text,'0'), "
            f"COALESCE(work_review_disposition,'') FROM {schema}.ledger "
            f"WHERE kind='work_closed' ORDER BY id;").splitlines():
        slug, resolution, rid, closer, disp = row.split("|")
        lines.append(f"work_closed({quote(slug)},{resolution},{rid}).")
        lines.append(f"w_closed({quote(slug)},{rid},{closer}).")
        if disp:
            lines.append(f"w_disposition({rid},{disp}).")
    for row in psql_tuples(
            f"SELECT id FROM {schema}.ledger WHERE kind='work_closed' "
            f"AND work_witness IS NOT NULL AND btrim(work_witness) <> '' ORDER BY id;").splitlines():
        lines.append(f"work_witness_present({row}).")
    for row in psql_tuples(
            f"SELECT work_slug, work_depends_on, id FROM {schema}.ledger "
            f"WHERE kind='work_depends_on' ORDER BY id;").splitlines():
        dep, ant, rid = row.split("|")
        lines.append(f"work_depends({quote(dep)},{quote(ant)},{rid}).")
        lines.append(f"w_dep_e({quote(dep)},{quote(ant)},{rid}).")
    # w_discharged: the SAME join shape the SQL floor's discharged CTE uses (verdict=attest,
    # distinct actor, review row not superseded) -- the already-filtered leg, both producers.
    for row in psql_tuples(
            f"SELECT c.id FROM {schema}.ledger c WHERE c.kind='work_closed' AND EXISTS ("
            f"  SELECT 1 FROM {schema}.ledger r JOIN {schema}.review_detail d ON d.ledger_id = r.id"
            f"  WHERE r.kind='review' AND r.regards = c.id AND d.verdict='attest' AND r.actor <> c.actor"
            f"    AND NOT EXISTS (SELECT 1 FROM {schema}.ledger s2 WHERE s2.supersedes = r.id));").splitlines():
        lines.append(f"w_discharged({row}).")
    return "\n".join(lines) + "\n"


def main() -> int:
    teardown()
    failures: list[str] = []
    tmps: list[Path] = []
    try:
        print(f"== scaffolding classic world {WORLD} + manual s15..s31 apply (see docstring for why classic) ==")
        world_dir, dep = scaffold_classic_s31(WORLD)
        tmps.append(world_dir.parent)
        schema = dep["schema"]
        print(f"  scaffold OK (schema={schema}).\n")

        # --- a: retracted close re-opens --------------------------------------------------------
        led(world_dir, "work", "open", "item-a", "ItemA")
        led(world_dir, "work", "claim", "item-a")
        led(world_dir, "work", "close", "item-a", "dropped", "--review-witness", "ref-a")
        st0 = psql_tuples(f"SELECT state, resolution FROM {schema}.work_item_current WHERE slug='item-a';")
        close_a = psql_tuples(f"SELECT id FROM {schema}.ledger WHERE kind='work_closed' AND work_slug='item-a';")
        ra = retract(world_dir, close_a, f"retract close of item-a (row {close_a})")
        st1 = psql_tuples(f"SELECT state, resolution, witness FROM {schema}.work_item_current WHERE slug='item-a';")
        ok_a = st0 == "closed|dropped" and ra.returncode == 0 and st1 == "open||"
        check("a-retracted-close-reopens", ok_a,
              f"before={st0!r} retract_exit={ra.returncode} after={st1!r} (open, resolution+witness gone)",
              failures)

        # --- a2: composite ancestor re-open -- UNEXERCISED, concrete blocker --------------------
        check("a2-composite-ancestor-reopen", True,
              "UNEXERCISED -- concrete blocker: design/FABLE-COMPOSITE-DISCHARGE-SPEC.md is DRAFT/"
              "unratified/unbuilt; no work_discharge/effective_state column exists in any kernel, so "
              "the polarity has no substrate. The composite spec's own sec-3b names how it inherits "
              "this delta's fix in the same read once built. Filed, not silently claimed.", failures)

        # --- b: retracted claim unclaims --------------------------------------------------------
        led(world_dir, "work", "open", "item-b", "ItemB")
        led(world_dir, "work", "claim", "item-b")
        cl0 = psql_tuples(f"SELECT claimant IS NOT NULL FROM {schema}.work_item_current WHERE slug='item-b';")
        claim_b = psql_tuples(f"SELECT id FROM {schema}.ledger WHERE kind='work_claimed' AND work_slug='item-b';")
        rb = retract(world_dir, claim_b, f"retract claim of item-b (row {claim_b})")
        cl1 = psql_tuples(f"SELECT claimant IS NULL, state FROM {schema}.work_item_current WHERE slug='item-b';")
        ok_b = cl0 == "t" and rb.returncode == 0 and cl1 == "t|open"
        check("b-retracted-claim-unclaims", ok_b,
              f"claimed_before={cl0} retract_exit={rb.returncode} after(claimant NULL, still open)={cl1!r}",
              failures)

        # --- c: retracted blocks-close edge stops gating ----------------------------------------
        led(world_dir, "work", "open", "item-c", "ItemC")
        led(world_dir, "work", "open", "item-c-ant", "ItemCAnt")
        led(world_dir, "work", "claim", "item-c")
        led(world_dir, "work", "depends", "item-c", "item-c-ant", "--type", "blocks-close")
        rc0 = led(world_dir, "work", "close", "item-c", "dropped", "--review-witness", "ref-c", "--strict")
        out_c0 = rc0.stdout + rc0.stderr
        blocked = rc0.returncode != 0 and "item-c-ant" in out_c0
        edge_c = psql_tuples(f"SELECT id FROM {schema}.ledger WHERE kind='work_depends_on' AND work_slug='item-c';")
        rce = retract(world_dir, edge_c, f"retract blocks-close edge item-c->item-c-ant (row {edge_c})")
        rc1 = led(world_dir, "work", "close", "item-c", "dropped", "--review-witness", "ref-c", "--strict")
        hist = psql_tuples(f"SELECT count(*) FROM {schema}.ledger WHERE id = {edge_c} "
                           f"OR supersedes = {edge_c};")
        ok_c = blocked and rce.returncode == 0 and rc1.returncode == 0 and hist == "2"
        check("c-retracted-edge-stops-gating", ok_c,
              f"strict_close_blocked_first={blocked} (excerpt={out_c0.strip()[-200:]!r}) "
              f"retract_exit={rce.returncode} strict_close_after_exit={rc1.returncode} "
              f"edge+retractor_rows_in_history={hist}", failures)

        # --- d: retracted open burns slug; orphans surface; redo idiom taught -------------------
        led(world_dir, "work", "open", "item-d", "ItemD")
        led(world_dir, "work", "claim", "item-d")
        open_d = psql_tuples(f"SELECT id FROM {schema}.ledger WHERE kind='work_opened' AND work_slug='item-d';")
        rd = retract(world_dir, open_d, f"retract opening act of item-d (row {open_d})")
        gone = psql_tuples(f"SELECT count(*) FROM {schema}.work_item_current WHERE slug='item-d';")
        orphans = psql_tuples(f"SELECT violation || '~' || slug || '~' || detail FROM {schema}.work_item_violations "
                              f"WHERE violation='orphaned_by_retraction' ORDER BY detail;")
        rd2 = led(world_dir, "work", "open", "item-d", "ItemD reborn attempt")
        out_d2 = rd2.stdout + rd2.stderr
        burned = rd2.returncode != 0 and "already has an opening act" in out_d2
        teaches = "RETRACTED" in out_d2 and "--refs row:" in out_d2
        ok_d = (rd.returncode == 0 and gone == "0"
                and "orphaned_by_retraction~item-d~surviving work_claimed row" in orphans
                and burned and teaches)
        check("d-retracted-open-burns-slug", ok_d,
              f"retract_exit={rd.returncode} in_current={gone} orphans={orphans!r} "
              f"reopen_refused={burned} teach_text_names_redo_idiom={teaches} "
              f"excerpt={out_d2.strip()[-320:]!r}", failures)

        # --- e: reinstatement-free (supersede the superseder; victim stays retracted) -----------
        retractor_a = psql_tuples(f"SELECT id FROM {schema}.ledger WHERE supersedes = {close_a};")
        re_ = retract(world_dir, retractor_a, f"retract the retractor of item-a's close (row {retractor_a})")
        st2 = psql_tuples(f"SELECT state, resolution FROM {schema}.work_item_current WHERE slug='item-a';")
        ok_e = re_.returncode == 0 and st2 == "open|"
        check("e-reinstatement-free", ok_e,
              f"retract_retractor_exit={re_.returncode} item-a after={st2!r} "
              "(still open -- the defeated defeater does NOT revive the close)", failures)

        # --- e2: item led-work-close-supersedes-swallowed (ledger row 1601, witnessed
        # 2026-07-18): `led work close --supersedes <id>` used to SILENTLY SWALLOW the flag --
        # the shared top-of-file parser sets $supersedes, but `work close`'s own code never read
        # it, so no `supersedes` column ever landed on a work_closed row through the CLI (case
        # a's own retract() above proves ONLY that a SEPARATE, unrelated-kind row -- a bare
        # `revision` entry -- can retract a close; it was never able to prove the close's OWN
        # CORRECTION is itself a NEW work_closed row, because the flag had no wiring). Now:
        # closing item-e2 again, citing --supersedes <the first close's row id>, lands the
        # `supersedes` column on the SECOND work_closed row directly, and s31's OWN uniform-
        # retraction machinery (unchanged, this item touches no kernel semantics) does the rest
        # -- the FIRST close is retracted, work_item_current re-reads the SECOND close's own
        # resolution. Exercised in BOTH supported positions: before 'work' (the shared top-of-
        # file flag, the exact shape row 1601 used) and after 'close' (this item's own added
        # case arm).
        led(world_dir, "work", "open", "item-e2", "ItemE2")
        led(world_dir, "work", "claim", "item-e2")
        led(world_dir, "work", "close", "item-e2", "dropped", "--review-witness", "ref-e2-first")
        close_e2_first = psql_tuples(
            f"SELECT id FROM {schema}.ledger WHERE kind='work_closed' AND work_slug='item-e2' "
            f"ORDER BY id LIMIT 1;")
        st_before_e2 = psql_tuples(
            f"SELECT state, resolution FROM {schema}.work_item_current WHERE slug='item-e2';")
        # position 1: before 'work' (led's own shared top-of-file flag parser).
        re2_ = led(world_dir, "--supersedes", close_e2_first, "work", "close", "item-e2",
                   "shipped", "--witness", "commit-e2fix", "--review-witness", "ref-e2-second")
        out_e2 = re2_.stdout + re2_.stderr
        close_e2_second = psql_tuples(
            f"SELECT id FROM {schema}.ledger WHERE kind='work_closed' AND work_slug='item-e2' "
            f"ORDER BY id DESC LIMIT 1;")
        supersedes_col = psql_tuples(
            f"SELECT supersedes FROM {schema}.ledger WHERE id = {close_e2_second};")
        st_after_e2 = psql_tuples(
            f"SELECT state, resolution FROM {schema}.work_item_current WHERE slug='item-e2';")
        ok_e2 = (re2_.returncode == 0
                 and supersedes_col == close_e2_first  # the column ACTUALLY LANDED -- not
                                                         # silently swallowed
                 and st_before_e2 == "closed|dropped"
                 and st_after_e2 == "closed|shipped"  # the SECOND close is now what reads
                 and "--supersedes" in out_e2)  # the advisory teaches what happened
        check("e2-close-supersedes-wired-not-swallowed", ok_e2,
              f"exit={re2_.returncode} first_close_id={close_e2_first} "
              f"second_close_id={close_e2_second} supersedes_col={supersedes_col!r} "
              f"(expect == first_close_id, i.e. the flag actually landed) "
              f"state_before={st_before_e2!r} state_after={st_after_e2!r} "
              f"advisory_present={'--supersedes' in out_e2}", failures)

        # e3: the SAME flag, given AFTER 'close' instead of before 'work' -- the second position
        # this item's own case arm adds, mirroring `work open`/`work resolve-violation`'s own
        # --supersedes position.
        led(world_dir, "work", "open", "item-e3", "ItemE3")
        led(world_dir, "work", "claim", "item-e3")
        led(world_dir, "work", "close", "item-e3", "dropped", "--review-witness", "ref-e3-first")
        close_e3_first = psql_tuples(
            f"SELECT id FROM {schema}.ledger WHERE kind='work_closed' AND work_slug='item-e3' "
            f"ORDER BY id LIMIT 1;")
        re3_ = led(world_dir, "work", "close", "item-e3", "shipped", "--witness", "commit-e3fix",
                   "--review-witness", "ref-e3-second", "--supersedes", close_e3_first)
        close_e3_second = psql_tuples(
            f"SELECT id FROM {schema}.ledger WHERE kind='work_closed' AND work_slug='item-e3' "
            f"ORDER BY id DESC LIMIT 1;")
        supersedes_col_e3 = psql_tuples(
            f"SELECT supersedes FROM {schema}.ledger WHERE id = {close_e3_second};")
        ok_e3 = re3_.returncode == 0 and supersedes_col_e3 == close_e3_first
        check("e3-close-supersedes-after-close-position", ok_e3,
              f"exit={re3_.returncode} first_close_id={close_e3_first} "
              f"second_close_id={close_e3_second} supersedes_col={supersedes_col_e3!r}", failures)

        # --- f: history readers unchanged -------------------------------------------------------
        chain_ok = psql_tuples(
            f"SELECT bool_and(l.row_hash = {schema}.compute_row_hash(l, "
            f"  COALESCE(prev.row_hash, (SELECT seed FROM {schema}_kernel.chain_genesis)))) "
            f"FROM {schema}.ledger l "
            f"LEFT JOIN {schema}.ledger prev ON prev.id = "
            f"  (SELECT max(p.id) FROM {schema}.ledger p WHERE p.id < l.id);")
        n_retracted = psql_tuples(f"SELECT count(*) FROM {schema}.ledger l WHERE EXISTS "
                                  f"(SELECT 1 FROM {schema}.ledger s WHERE s.supersedes = l.id);")
        recent = led(world_dir, "--recent", "50").stdout
        marks = recent.count("SUPERSEDED")
        ok_f = chain_ok == "t" and int(n_retracted) >= 4 and marks >= 4
        check("f-history-readers-unchanged", ok_f,
              f"row-hash chain recomputes clean across ALL rows incl. {n_retracted} retracted: {chain_ok}; "
              f"led --recent shows retracted rows MARKED (SUPERSEDED x{marks}), never hidden", failures)

        # --- g: allowlist gate, both polarities --------------------------------------------------
        gg = sh([sys.executable, str(GATE)])
        gr = sh([sys.executable, str(GATE), "--red"])
        red_out = gr.stdout + gr.stderr
        ok_g = (gg.returncode == 0 and gr.returncode == 0
                and "REFUSED" in red_out and "FACTOR THROUGH THE IN-FORCE PROJECTION" in red_out
                and "CLAIM THE HISTORY ALLOWLIST" in red_out)
        check("g-allowlist-gate-both-polarities", ok_g,
              f"green_exit={gg.returncode} red_exit={gr.returncode} "
              f"teach_names_both_paths={'FACTOR THROUGH' in red_out and 'CLAIM THE HISTORY' in red_out} "
              f"red_tail={red_out.strip()[-220:]!r}", failures)

        # --- h: bespoke SQL/ASP differential AGREE on this whole world --------------------------
        edb = build_edb(schema)
        asp_atoms = {a for a in clingo_run.run_clingo([TNOW_LP, WORK_ITEMS_LP, WORK_REVIEW_LP], edb)
                     if "(" in a}
        preds = set(ledger_floor.WORK_ITEM_PREDS) | set(ledger_floor.WORK_REVIEW_PREDS)
        asp_atoms = {a for a in asp_atoms if a.split("(", 1)[0] in preds}
        os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"] = \
            PGDB, schema, f"{schema}_kernel"
        try:
            sql_atoms = ledger_floor.work_item_floor_atoms(schema) | ledger_floor.work_review_floor_atoms(schema)
        finally:
            del os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"]
        only_asp, only_sql = asp_atoms - sql_atoms, sql_atoms - asp_atoms
        verdict = "AGREE" if not only_asp and not only_sql else "DIVERGE_DEFECT"
        orphan_witnessed = any(a.startswith("work_orphaned_by_retraction(") for a in asp_atoms)
        ok_h = verdict == "AGREE" and len(asp_atoms) > 0 and orphan_witnessed
        check("h-differential-agree", ok_h,
              f"verdict={verdict} asp={len(asp_atoms)} sql={len(sql_atoms)} atoms "
              f"orphan_atom_in_set={orphan_witnessed} "
              f"only_asp={sorted(only_asp)[:6]} only_sql={sorted(only_sql)[:6]} -- "
              "ledger_tnow.lp+work_items.lp+work_review.lp composed over ONE EDB vs the SQL floor, "
              "on a world containing every s31 shape (standing ./judge wiring: named separate seam, "
              "see docstring)", failures)

    finally:
        teardown()
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- s31 uniform retraction both-polarity proof (retracted close re-opens / "
          "claim unclaims / blocks-close edge stops gating / open burns slug + orphans surface + "
          "redo idiom taught / reinstatement-free / hash chain + led --recent history reads "
          "unchanged / allowlist gate green+red / composed SQL-ASP differential AGREE), zero residue. "
          "a2 (composite ancestor) UNEXERCISED with its named blocker.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
