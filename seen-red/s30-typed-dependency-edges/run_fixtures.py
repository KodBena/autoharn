#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T13:57:47Z
#   last-change: 2026-07-15T13:59:56Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for kernel/lineage/s30-typed-dependency-edges.sql
(design/FABLE-OBLIGATION-DEPENDENT-TYPING-SPEC.md, Fable-reviewed-and-adopted, RATIFIED
2026-07-15, ledger decision row 1018) + bootstrap/templates/led.tmpl's `work depends --type`
flag. Real infra, no mocks: a throwaway `--new-world` scaffold in the toy db, which now applies
the FULL s15..s30 birth chain automatically (s30 wired into new-project.sh's own LINEAGE_CHAIN by
this same commission) -- torn down before AND after this file runs so re-running it never leaves
residue. A second, SEPARATE scaffold pinned to s15..s29 (s30 deliberately NOT in its birth chain)
proves the legacy/migration case (case i below), with s30 applied on top afterward, mirroring a
real `./migrate` step by hand.

Cases (spec sec-5's four acceptance bullets, plus the structural refusals sec-2/sec-4 name):
  a-blocks-close-self-edge-refused    -- a blocks-close self-edge is refused at construction.
  b-informs-self-edge-allowed         -- an informs self-edge is allowed (s22's original, byte-
                                          identical unrefined posture -- unchanged by this delta).
  c-blocks-close-dangling-refused     -- a blocks-close edge naming an unopened antecedent is
                                          refused (both endpoints must be close-tracked items).
  d-informs-dangling-allowed          -- an informs edge naming an unopened antecedent is allowed
                                          (s22's original posture, unchanged).
  e-blocks-close-cycle-refused        -- sec-5 bullet 1, first half: a blocks-close cycle (X->Y,
                                          Y->X) is refused at write time, naming the would-be cycle.
  f-informs-cycle-allowed             -- sec-5 bullet 1, second half: the SAME shape as (e), typed
                                          informs instead, is allowed (informs never gates, so a
                                          cycle in it is not a structural hazard).
  g-blocks-close-child-blocks-strict  -- sec-5 bullet 2, first half: an interior item with one
                                          unresolved blocks-close child cannot strict-close (Element
                                          C refusal fires, naming the leaf).
  h-informs-child-does-not-block      -- sec-5 bullet 2, second half: the IDENTICAL structural setup
                                          (an unresolved child dependency), typed informs instead of
                                          blocks-close, lets the SAME strict close SUCCEED -- proving
                                          the TYPE, not the mere edge, gates.
  i-legacy-edge-reads-informs         -- sec-5 bullet 4: a work_depends_on edge authored on a
                                          PRE-s30 kernel (edge_type column does not exist yet)
                                          stays edge_type IS NULL forever once s30 is migrated on
                                          top (append-only makes it unwritable -- no backfill), and
                                          reads as informs BY OMISSION (NULL never satisfies
                                          edge_type='blocks-close') -- it does NOT retroactively
                                          block a strict close that depends on it (fail-safe: no
                                          historical close is retroactively blocked).
  j-reserved-word-supersedes-refused  -- `led work depends ... --type supersedes` is refused at the
                                          `led` boundary (the REVIEW NOTE DISPOSITION: supersedes is
                                          a reserved word, not a legal edge_type value).

Usage: python3 seen-red/s30-typed-dependency-edges/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
S30_DELTA = REPO / "kernel" / "lineage" / "s30-typed-dependency-edges.sql"

PGHOST, PGDB = "192.168.122.1", "toy"
WORLD = "s30fxprobe"
WORLD_PRE = "s30fxprobe_pre"

S15_TO_S29 = [
    "high_watermark_1.sql", "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
    "s25-commission-kind.sql", "s26-row-hash-chain.sql", "s28-work-parent-edge.sql",
    "s29-obligation-item-key-and-typed-close.sql",
]


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


def scaffold_classic_s29_only(world: str) -> tuple[Path, dict]:
    """CLASSIC MODE (explicit --schema/--kern/--role, no automatic kernel apply), followed by a
    MANUAL s15..s29 apply -- one delta short of the full birth chain, on purpose, mirrors
    s29's own scaffold_classic_s28_only precedent one delta later."""
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
    for name in S15_TO_S29:
        args += ["-f", str(REPO / "kernel" / "lineage" / name)]
    ra = sh(args)
    if ra.returncode != 0:
        raise RuntimeError(f"CLASSIC s15..s29 APPLY FAILED ({world}): {ra.stdout[-1500:]} {ra.stderr[-1500:]}")
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
    teardown_all()
    failures: list[str] = []
    tmps: list[Path] = []

    try:
        print(f"== scaffolding throwaway --new-world {WORLD} (full s15..s30 birth chain) ==")
        world_dir, dep = scaffold(WORLD)
        tmps.append(world_dir.parent)
        schema, kern, role = dep["schema"], dep["kern"], dep["role"]
        print(f"  scaffold OK (schema={schema} kern={kern} role={role}).\n")

        # --- a/b: self-edge, blocks-close refused / informs allowed ----------------------------
        led(world_dir, "work", "open", "self-a", "SelfA")
        ra_ = led(world_dir, "work", "depends", "self-a", "self-a", "--type", "blocks-close")
        out_a = ra_.stdout + ra_.stderr
        ok_a = ra_.returncode != 0 and "self-edge" in out_a
        check("a-blocks-close-self-edge-refused", ok_a,
              f"exit={ra_.returncode} excerpt={out_a.strip()[-300:]!r}", failures)

        led(world_dir, "work", "open", "self-b", "SelfB")
        rb_ = led(world_dir, "work", "depends", "self-b", "self-b", "--type", "informs")
        ok_b = rb_.returncode == 0
        check("b-informs-self-edge-allowed", ok_b,
              f"exit={rb_.returncode} stderr_tail={(rb_.stdout + rb_.stderr).strip()[-200:]!r}", failures)

        # --- c/d: dangling antecedent, blocks-close refused / informs allowed ------------------
        led(world_dir, "work", "open", "dangle-c", "DangleC")
        rc_ = led(world_dir, "work", "depends", "dangle-c", "never-opened-c", "--type", "blocks-close")
        out_c = rc_.stdout + rc_.stderr
        ok_c = rc_.returncode != 0 and "no opening act" in out_c
        check("c-blocks-close-dangling-refused", ok_c,
              f"exit={rc_.returncode} excerpt={out_c.strip()[-300:]!r}", failures)

        led(world_dir, "work", "open", "dangle-d", "DangleD")
        rd_ = led(world_dir, "work", "depends", "dangle-d", "never-opened-d", "--type", "informs")
        ok_d = rd_.returncode == 0
        check("d-informs-dangling-allowed", ok_d,
              f"exit={rd_.returncode} stderr_tail={(rd_.stdout + rd_.stderr).strip()[-200:]!r}", failures)

        # --- e/f: cycle, blocks-close refused / informs allowed (sec-5 bullet 1) ---------------
        led(world_dir, "work", "open", "cyc-e-x", "CycEX")
        led(world_dir, "work", "open", "cyc-e-y", "CycEY")
        led(world_dir, "work", "depends", "cyc-e-x", "cyc-e-y", "--type", "blocks-close")
        re_ = led(world_dir, "work", "depends", "cyc-e-y", "cyc-e-x", "--type", "blocks-close")
        out_e = re_.stdout + re_.stderr
        ok_e = re_.returncode != 0 and "cycle" in out_e
        check("e-blocks-close-cycle-refused", ok_e,
              f"exit={re_.returncode} excerpt={out_e.strip()[-350:]!r}", failures)

        led(world_dir, "work", "open", "cyc-f-x", "CycFX")
        led(world_dir, "work", "open", "cyc-f-y", "CycFY")
        led(world_dir, "work", "depends", "cyc-f-x", "cyc-f-y", "--type", "informs")
        rf_ = led(world_dir, "work", "depends", "cyc-f-y", "cyc-f-x", "--type", "informs")
        ok_f = rf_.returncode == 0
        check("f-informs-cycle-allowed", ok_f,
              f"exit={rf_.returncode} stderr_tail={(rf_.stdout + rf_.stderr).strip()[-200:]!r}", failures)

        # --- g/h: an unresolved child blocks strict close when blocks-close, does NOT when
        # informs -- the SAME structural shape, only the type differs (sec-5 bullet 2) -----------
        led(world_dir, "work", "open", "root-g", "RootG")
        led(world_dir, "work", "claim", "root-g")
        led(world_dir, "work", "open", "leaf-g", "LeafG")   # left open+unclaimed+unclosed
        led(world_dir, "work", "depends", "root-g", "leaf-g", "--type", "blocks-close")
        rg_ = led(world_dir, "work", "close", "root-g", "dropped", "--review-witness", "refg", "--strict")
        out_g = rg_.stdout + rg_.stderr
        ok_g = rg_.returncode != 0 and "leaf-g" in out_g and "not yet closed" in out_g
        check("g-blocks-close-child-blocks-strict", ok_g,
              f"exit={rg_.returncode} names_leaf={'leaf-g' in out_g} excerpt={out_g.strip()[-400:]!r}", failures)

        led(world_dir, "work", "open", "root-h", "RootH")
        led(world_dir, "work", "claim", "root-h")
        led(world_dir, "work", "open", "leaf-h", "LeafH")   # left open+unclaimed+unclosed, SAME shape as g
        led(world_dir, "work", "depends", "root-h", "leaf-h", "--type", "informs")
        rh_ = led(world_dir, "work", "close", "root-h", "dropped", "--review-witness", "refh", "--strict")
        ok_h = rh_.returncode == 0
        check("h-informs-child-does-not-block", ok_h,
              f"exit={rh_.returncode} stderr_tail={(rh_.stdout + rh_.stderr).strip()[-250:]!r} "
              "-- proves the TYPE, not the mere edge, gates (identical structural shape as case g)",
              failures)

        # --- j: --type supersedes refused at the led boundary (reserved word) ------------------
        led(world_dir, "work", "open", "resv-j", "ResvJ")
        rj_ = led(world_dir, "work", "depends", "resv-j", "resv-j-target", "--type", "supersedes")
        out_j = rj_.stdout + rj_.stderr
        ok_j = rj_.returncode != 0 and "RESERVED WORD" in out_j
        check("j-reserved-word-supersedes-refused", ok_j,
              f"exit={rj_.returncode} excerpt={out_j.strip()[-300:]!r}", failures)

        # --- i: legacy (pre-s30) edge backfills to informs, does not retroactively block --------
        print(f"== scaffolding a SEPARATE s15..s29 world {WORLD_PRE} (s30 deliberately NOT in its birth chain) ==")
        world_dir_pre, dep_pre = scaffold_classic_s29_only(WORLD_PRE)
        tmps.append(world_dir_pre.parent)
        schema_pre, kern_pre, role_pre = dep_pre["schema"], dep_pre["kern"], dep_pre["role"]

        led(world_dir_pre, "work", "open", "root-i", "RootI")
        led(world_dir_pre, "work", "claim", "root-i")
        led(world_dir_pre, "work", "open", "leaf-i", "LeafI")   # left open -- would-be blocker
        pre_dep = led(world_dir_pre, "work", "depends", "root-i", "leaf-i")   # NO --type: column absent pre-s30
        ok_pre_dep = pre_dep.returncode == 0
        check("i0-pre-s30-depends-edge-authored-with-no-edge-type-column", ok_pre_dep,
              f"exit={pre_dep.returncode} stderr_tail={(pre_dep.stdout + pre_dep.stderr).strip()[-200:]!r}",
              failures)

        print(f"== applying s30-typed-dependency-edges.sql to {schema_pre}/{kern_pre}/{role_pre} "
              "(mirrors a real ./migrate step by hand) ==")
        ra_mig = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
                     "-v", f"schema={schema_pre}", "-v", f"kern={kern_pre}", "-v", f"role={role_pre}",
                     "-f", str(S30_DELTA)])
        if ra_mig.returncode != 0:
            print("s30 MIGRATE-ON-TOP APPLY FAILED:", ra_mig.stdout[-1500:], ra_mig.stderr[-1500:])
            return 1
        print("  s30 applied on top of the s15..s29 world.\n")

        legacy_type = psql_tuples(
            f"SELECT edge_type FROM {schema_pre}.ledger WHERE kind='work_depends_on' AND work_slug='root-i';")
        ok_i1 = legacy_type.stdout.strip() == ""   # psql -tAq prints NULL as empty string
        check("i1-legacy-edge-stays-null-unwritable-reads-informs-by-omission", ok_i1,
              f"edge_type={legacy_type.stdout.strip()!r} (empty = SQL NULL -- append-only makes this "
              "unwritable forever; case i2 below proves it reads as informs)", failures)

        ri_ = led(world_dir_pre, "work", "close", "root-i", "dropped", "--review-witness", "refi", "--strict")
        ok_i2 = ri_.returncode == 0
        check("i2-legacy-edge-does-not-retroactively-block-strict-close", ok_i2,
              f"exit={ri_.returncode} stderr_tail={(ri_.stdout + ri_.stderr).strip()[-250:]!r} "
              "-- leaf-i is still open+unclosed; the legacy edge reads informs, so it does NOT gate",
              failures)

    finally:
        teardown_all()
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- s30 typed dependency edges both-polarity proof (self-edge/dangling/"
          "cycle refused for blocks-close, allowed for informs / an unresolved blocks-close child "
          "blocks strict close, the SAME shape typed informs does not / supersedes refused as a "
          "reserved word / a legacy pre-s30 edge stays NULL forever (unwritable) and reads as "
          "informs by omission, not retroactively blocking a strict close), zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
