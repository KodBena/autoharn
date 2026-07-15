#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T20:53:30Z
#   last-change: 2026-07-15T20:56:11Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for kernel/lineage/s32-edge-views-single-home.sql
(design/ORCH-CATEGORICAL-REFACTOR-CONSULT-2026-07-15.md, F3/F6 + plan step 3; ledger item
edge-views-single-home). Real infra, no mocks: a CLASSIC-mode scaffold (explicit --schema/--kern/
--role, no automatic kernel apply -- s30/s31's own scaffold_classic idiom) followed by a MANUAL
s15..s31 apply, in the TOY db, torn down before AND after so re-running leaves no residue.

Cases:
  a-before-after-output-equality -- the load-bearing case. A varied fixture world is built on the
                                     s15..s31 kernel (multiple work items, a parent tree, blocks-
                                     close AND informs edges, a retracted parent open, a retracted
                                     blocks-close edge, reviews with same- and distinct-actor
                                     attest verdicts, deferred and witnessed closes, a strict
                                     close). Every re-issued object's OUTPUT is captured (review_gap,
                                     countersigned_in_force, work_review_gap, work_item_violations,
                                     work_item_strict_blockers() for every open work-item slug, and
                                     work_parent_would_cycle()/work_depends_on_would_cycle() over
                                     every slug pair actually present). s32 is then applied ON THE
                                     SAME SCHEMA and every capture is re-run byte-for-byte. Diff is
                                     asserted EMPTY.
  b-refusal-polarities-unchanged -- every pre-existing refusal this delta's re-issued functions
                                     participate in (dangling parent, self-parent, parent cycle,
                                     blocks-close self-edge/dangling-antecedent/cycle, strict-close
                                     naming an unresolved leaf) is re-witnessed on a FULL s15..s32
                                     birth chain, exit code and message TEXT unchanged from the
                                     s28/s29/s30 fixtures' own banked expectations.
  c-allowlist-gate-both-polarities -- gates/ledger_reader_allowlist.py (extended in this same
                                     commit to chain through s32 and declare the two new raw edge
                                     views) exits 0 green on the real chain AND refuses a
                                     deliberately misfactored scratch view under --red.
  d-judge-agree-unaffected        -- the standing ./judge SQL/ASP differential still verdicts
                                     AGREE on a full s15..s32 birth-chain world (s32 touches no
                                     kind/status/supersedes fact judge derives T_now from).

Usage: python3 seen-red/s32-edge-views-single-home/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
LINEAGE = REPO / "kernel" / "lineage"
GATE = REPO / "gates" / "ledger_reader_allowlist.py"

PGHOST = fixture_pghost()
PGDB = "toy"

CHAIN_S31 = [
    "s15-schema.sql", "s17-stamp-mechanism.sql", "s17-independence-vocabulary.sql",
    "s19-trigger-search-path.sql", "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
    "s25-commission-kind.sql", "s26-row-hash-chain.sql", "s28-work-parent-edge.sql",
    "s29-obligation-item-key-and-typed-close.sql", "s30-typed-dependency-edges.sql",
    "s31-supersession-uniform-retraction.sql",
]
S32 = "s32-edge-views-single-home.sql"


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
        f"DROP SCHEMA IF EXISTS {world} CASCADE; DROP SCHEMA IF EXISTS {world}_kernel CASCADE; "  # declared-drop: s32 fixture scratch reset
        f"DROP OWNED BY {world}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {world}_rw;"])


def led(world_dir: Path, *args: str, actor: str | None = None) -> subprocess.CompletedProcess[str]:
    env = None
    if actor is not None:
        env = dict(os.environ)
        env["LED_ACTOR"] = actor
    return sh(["bash", str(world_dir / "led"), *args], cwd=str(world_dir), env=env)


def psql_tuples(sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"psql failed: {cp.stdout[-500:]} {cp.stderr[-500:]}")
    return cp.stdout


def scaffold_classic(world: str, chain: list[str]) -> Path:
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
    for name in chain:
        args += ["-f", str(LINEAGE / name)]
    ra = sh(args)
    if ra.returncode != 0:
        raise RuntimeError(f"MANUAL APPLY FAILED ({world}): {ra.stdout[-1500:]} {ra.stderr[-1500:]}")
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
    return world_dir


def apply_s32(schema: str, kern: str, role: str) -> None:
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}",
            "-f", str(LINEAGE / S32)]
    r = sh(args)
    if r.returncode != 0:
        raise RuntimeError(f"s32 APPLY FAILED: {r.stdout[-1500:]} {r.stderr[-1500:]}")


# ---------------------------------------------------------------------------------------------
# CASE a -- before/after output equality snapshot queries. Every query is a plain, deterministic
# ORDER BY so a byte-diff is meaningful (no unordered-set ambiguity).
# ---------------------------------------------------------------------------------------------
def snapshot(schema: str) -> dict[str, str]:
    out: dict[str, str] = {}
    out["review_gap"] = psql_tuples(
        f"SELECT id, actor, scope, assigned_by FROM {schema}.review_gap ORDER BY id, actor, scope;")
    out["countersigned_in_force"] = psql_tuples(
        f"SELECT id, kind, work_slug, work_review_disposition, edge_type "
        f"FROM {schema}.countersigned_in_force ORDER BY id;")
    out["work_review_gap"] = psql_tuples(
        f"SELECT slug, close_id, closer FROM {schema}.work_review_gap ORDER BY slug, close_id;")
    out["work_item_violations"] = psql_tuples(
        f"SELECT violation, slug, detail FROM {schema}.work_item_violations "
        f"ORDER BY violation, slug, detail;")
    slugs = [s for s in psql_tuples(
        f"SELECT DISTINCT work_slug FROM {schema}.ledger WHERE kind='work_opened' ORDER BY 1;"
    ).splitlines() if s.strip()]
    blockers = []
    for slug in slugs:
        rows = psql_tuples(
            f"SELECT blocking_slug, reason FROM {schema}.work_item_strict_blockers('{slug}') "
            f"ORDER BY blocking_slug, reason;")
        blockers.append(f"{slug}::\n{rows}")
    out["work_item_strict_blockers"] = "\n".join(blockers)
    pairs = []
    for a in slugs:
        for b in slugs:
            if a == b:
                continue
            wp = psql_tuples(f"SELECT {schema}.work_parent_would_cycle('{a}','{b}');").strip()
            wd = psql_tuples(f"SELECT {schema}.work_depends_on_would_cycle('{a}','{b}');").strip()
            pairs.append(f"parent({a},{b})={wp} depends({a},{b})={wd}")
    out["would_cycle_matrix"] = "\n".join(pairs)
    return out


def build_dataset(world_dir: Path) -> None:
    """A varied world: a parent tree, blocks-close + informs edges, a retracted parent open, a
    retracted blocks-close edge, same- and distinct-actor attest reviews, deferred + witnessed
    closes, and one strict close -- enough shape to exercise every re-issued object's every leg."""
    led(world_dir, "work", "open", "root-a", "RootA")
    led(world_dir, "work", "open", "child-a1", "ChildA1", "--parent", "root-a")
    led(world_dir, "work", "open", "child-a2", "ChildA2", "--parent", "root-a")
    led(world_dir, "work", "open", "root-b", "RootB")
    led(world_dir, "work", "open", "root-c", "RootC")
    led(world_dir, "work", "claim", "child-a1")
    led(world_dir, "work", "claim", "root-b")
    led(world_dir, "work", "claim", "root-c")
    led(world_dir, "work", "depends", "child-a2", "root-b", "--type", "informs")
    led(world_dir, "work", "depends", "root-b", "root-c", "--type", "blocks-close")
    # deferred close on root-c (an open item-keyed obligation, undischarged) -- exercises
    # work_review_gap and strict_blockers' review_unresolved leg.
    led(world_dir, "work", "close", "root-c", "dropped", "--review-deferred")
    # a distinct-actor attest review discharging root-c's deferred obligation.
    led(world_dir, "register-principal", "reviewer-x", "human")
    close_c = psql_tuples(
        f"SELECT id FROM {world_dir.name}.ledger WHERE kind='work_closed' AND work_slug='root-c';"
    ).strip()
    led(world_dir, "review", close_c, "attest", "self-review", "looks fine", actor="reviewer-x")
    # child-a1: witnessed close, discharged by a review from the SAME actor as the closer (exercises
    # countersigned_in_force's no-distinct-actor-filter leg differing from review_gap's own filter).
    led(world_dir, "work", "close", "child-a1", "dropped", "--review-witness", "ref-a1")
    close_a1 = psql_tuples(
        f"SELECT id FROM {world_dir.name}.ledger WHERE kind='work_closed' AND work_slug='child-a1';"
    ).strip()
    led(world_dir, "review", close_a1, "attest", "self-review", "self-attest, same actor as closer")
    # a strict close on root-b (its own blocks-close antecedent root-c is closed+discharged by now).
    led(world_dir, "work", "claim", "child-a2")  # ensure tree membership captured before strict close
    rs = led(world_dir, "work", "close", "root-b", "dropped", "--review-witness", "ref-b", "--strict")
    if rs.returncode != 0:
        raise RuntimeError(f"expected strict close of root-b to succeed once root-c is resolved: "
                            f"{rs.stdout} {rs.stderr}")
    # a retracted parent open (child-a2's parent stays root-a; retract root-a itself is too
    # disruptive to the rest of the dataset -- instead retract a FRESH throwaway parent/child pair
    # so the retraction shape is exercised without perturbing the other captures).
    led(world_dir, "work", "open", "throwaway-root", "ThrowawayRoot")
    led(world_dir, "work", "open", "throwaway-child", "ThrowawayChild", "--parent", "throwaway-root")
    led(world_dir, "work", "claim", "throwaway-child")
    open_tr = psql_tuples(
        f"SELECT id FROM {world_dir.name}.ledger WHERE kind='work_opened' "
        f"AND work_slug='throwaway-root';").strip()
    led(world_dir, "--supersedes", open_tr, "revision", "retract throwaway-root's opening act")
    # a retracted blocks-close edge (independent of the root-b/root-c one already resolved).
    led(world_dir, "work", "open", "edge-x", "EdgeX")
    led(world_dir, "work", "open", "edge-y", "EdgeY")
    led(world_dir, "work", "depends", "edge-x", "edge-y", "--type", "blocks-close")
    edge_xy = psql_tuples(
        f"SELECT id FROM {world_dir.name}.ledger WHERE kind='work_depends_on' "
        f"AND work_slug='edge-x' AND work_depends_on='edge-y';").strip()
    led(world_dir, "--supersedes", edge_xy, "revision", "retract edge-x's blocks-close edge on edge-y")


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    world_a = "s32fxa"
    world_b = "s32fxb"
    world_j = "s32fxj"
    teardown(world_a)
    teardown(world_b)
    teardown(world_j)
    try:
        # --- a: before/after output equality ------------------------------------------------
        print(f"== case a: scaffolding classic world {world_a}, manual s15..s31 apply ==")
        world_dir = scaffold_classic(world_a, CHAIN_S31)
        tmps.append(world_dir.parent)
        world_dir = world_dir.with_name(world_a)  # world_dir already == .../world_a; kept explicit
        build_dataset(world_dir)
        before = snapshot(world_a)
        print(f"== applying s32 on top of the SAME schema {world_a} ==")
        apply_s32(world_a, f"{world_a}_kernel", f"{world_a}_rw")
        after = snapshot(world_a)
        diffs = {k: (before[k], after[k]) for k in before if before[k] != after[k]}
        ok_a = not diffs
        detail = "every capture byte-identical before/after s32" if ok_a else \
            "DIFFERED: " + "; ".join(f"{k}" for k in diffs)
        check("a-before-after-output-equality", ok_a, detail, failures)
        if diffs:
            for k, (b, a) in diffs.items():
                print(f"  --- {k} BEFORE ---\n{b}\n  --- {k} AFTER ---\n{a}\n")

        # --- b: refusal polarities re-witnessed, unchanged text, on a FULL s15..s32 chain ----
        print(f"== case b: scaffolding classic world {world_b}, manual s15..s32 apply ==")
        chain_full = CHAIN_S31 + [S32]
        wb = scaffold_classic(world_b, chain_full)
        tmps.append(wb.parent)

        led(wb, "work", "open", "bp-root", "BPRoot")
        r_self = led(wb, "work", "open", "bp-self", "BPSelf", "--parent", "bp-self")
        # A self-parent on `led work open` always hits the DANGLING-parent branch first (the
        # trigger's own EXISTS check runs before the row's own work_parent_not_self CHECK is
        # evaluated, and a slug being opened this same INSERT cannot yet EXIST as its own parent) --
        # s28's own header names work_parent_not_self as belt-and-braces defense in depth for
        # exactly this reason, not the path a self-parent open takes in practice. Untouched by s32
        # (validate_work_item is not re-issued here) -- assert refusal fires, text unchanged.
        ok_self = r_self.returncode != 0 and "which has no opening act" in (r_self.stdout + r_self.stderr)
        check("b1-self-parent-refused", ok_self,
              f"exit={r_self.returncode} excerpt={(r_self.stdout+r_self.stderr).strip()[-200:]!r}", failures)

        r_dangling = led(wb, "work", "open", "bp-child", "BPChild", "--parent", "bp-ghost")
        ok_dangling = r_dangling.returncode != 0 and "which has no opening act" in (r_dangling.stdout + r_dangling.stderr)
        check("b2-dangling-parent-refused", ok_dangling,
              f"exit={r_dangling.returncode} excerpt={(r_dangling.stdout+r_dangling.stderr).strip()[-200:]!r}", failures)

        led(wb, "work", "open", "bp-c1", "BPC1", "--parent", "bp-root")
        led(wb, "work", "open", "bp-c2", "BPC2", "--parent", "bp-c1")
        r_cycle = led(wb, "work", "open", "bp-cycle-attempt", "BPCycleAttempt", "--parent", "bp-c2")
        # bp-cycle-attempt --parent bp-c2 is legal (extends the tree); a genuine cycle is
        # structurally unreachable via ordinary INSERT (s28's own header proof) -- so test the
        # would_cycle FUNCTION directly instead, in isolation, the s28 fixture's own technique.
        cyc_true = psql_tuples(
            f"SELECT {world_b}.work_parent_would_cycle('bp-c2','bp-root');").strip()
        cyc_false = psql_tuples(
            f"SELECT {world_b}.work_parent_would_cycle('bp-root','bp-c1');").strip()
        ok_cycle_fn = cyc_true == "t" and cyc_false == "f" and r_cycle.returncode == 0
        check("b3-parent-cycle-function-both-polarities", ok_cycle_fn,
              f"would_cycle(ancestor-under-descendant)={cyc_true} (expect t) "
              f"would_cycle(unrelated)={cyc_false} (expect f) extend_ok={r_cycle.returncode}", failures)

        led(wb, "work", "open", "bc-a", "BCA")
        r_self_bc = led(wb, "work", "depends", "bc-a", "bc-a", "--type", "blocks-close")
        ok_self_bc = r_self_bc.returncode != 0 and "cannot have a blocks-close dependency on itself" in \
            (r_self_bc.stdout + r_self_bc.stderr)
        check("b4-blocks-close-self-edge-refused", ok_self_bc,
              f"exit={r_self_bc.returncode} excerpt={(r_self_bc.stdout+r_self_bc.stderr).strip()[-200:]!r}", failures)

        r_dangling_bc = led(wb, "work", "depends", "bc-a", "bc-ghost", "--type", "blocks-close")
        ok_dangling_bc = r_dangling_bc.returncode != 0 and "which has no opening act" in \
            (r_dangling_bc.stdout + r_dangling_bc.stderr)
        check("b5-blocks-close-dangling-antecedent-refused", ok_dangling_bc,
              f"exit={r_dangling_bc.returncode} excerpt={(r_dangling_bc.stdout+r_dangling_bc.stderr).strip()[-200:]!r}", failures)

        led(wb, "work", "open", "bc-x", "BCX")
        led(wb, "work", "open", "bc-y", "BCY")
        led(wb, "work", "depends", "bc-x", "bc-y", "--type", "blocks-close")
        r_cycle_bc = led(wb, "work", "depends", "bc-y", "bc-x", "--type", "blocks-close")
        ok_cycle_bc = r_cycle_bc.returncode != 0 and "would create a cycle" in \
            (r_cycle_bc.stdout + r_cycle_bc.stderr)
        check("b6-blocks-close-cycle-refused", ok_cycle_bc,
              f"exit={r_cycle_bc.returncode} excerpt={(r_cycle_bc.stdout+r_cycle_bc.stderr).strip()[-200:]!r}", failures)

        led(wb, "work", "open", "sc-root", "SCRoot")
        led(wb, "work", "open", "sc-dep", "SCDep")
        led(wb, "work", "claim", "sc-root")
        led(wb, "work", "depends", "sc-root", "sc-dep", "--type", "blocks-close")
        r_strict = led(wb, "work", "close", "sc-root", "dropped", "--review-witness", "ref-sc", "--strict")
        ok_strict = r_strict.returncode != 0 and "sc-dep" in (r_strict.stdout + r_strict.stderr) \
            and "obligation tree is unresolved" in (r_strict.stdout + r_strict.stderr)
        check("b7-strict-close-names-unresolved-leaf", ok_strict,
              f"exit={r_strict.returncode} excerpt={(r_strict.stdout+r_strict.stderr).strip()[-260:]!r}", failures)

        # --- c: allowlist gate, both polarities -----------------------------------------------
        gg = sh([sys.executable, str(GATE)])
        gr = sh([sys.executable, str(GATE), "--red"])
        red_out = gr.stdout + gr.stderr
        ok_c = (gg.returncode == 0 and gr.returncode == 0
                and "REFUSED" in red_out and "FACTOR THROUGH THE IN-FORCE PROJECTION" in red_out
                and "CLAIM THE HISTORY ALLOWLIST" in red_out)
        check("c-allowlist-gate-both-polarities", ok_c,
              f"green_exit={gg.returncode} red_exit={gr.returncode} "
              f"teach_names_both_paths={'FACTOR THROUGH' in red_out and 'CLAIM THE HISTORY' in red_out}",
              failures)

        # --- d: ./judge AGREE, unaffected on a full s15..s32 birth-chain world -----------------
        print(f"== case d: scaffolding classic world {world_j}, manual s15..s32 apply, running ./judge ==")
        wj = scaffold_classic(world_j, chain_full)
        tmps.append(wj.parent)
        led(wj, "work", "open", "j-item", "JItem")
        led(wj, "decision", "record a decision so judge has T_now facts to derive")
        rj = sh(["bash", str(wj / "judge")], cwd=str(wj))
        out_j = rj.stdout + rj.stderr
        ok_d = rj.returncode == 0 and ("AGREE" in out_j or "agree" in out_j.lower())
        check("d-judge-agree-unaffected", ok_d,
              f"exit={rj.returncode} tail={out_j.strip()[-300:]!r}", failures)

    finally:
        teardown(world_a)
        teardown(world_b)
        teardown(world_j)
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- s32 edge-views-single-home: before/after output equality on every "
          "re-issued view/function, every pre-existing refusal polarity re-witnessed with "
          "unchanged text, allowlist gate green+red, ./judge AGREE unaffected. Zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
