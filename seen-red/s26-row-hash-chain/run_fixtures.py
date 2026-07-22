#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for kernel/lineage/s26-row-hash-chain.sql +
bootstrap/templates/verify-chain.tmpl (design/MAINT-GPG-TRUST-LAYER.md §4, Rung 3). Real infra, no
mocks: a throwaway `--new-world` scaffold in the toy db (which applies s26 as part of its birth
chain and auto-provisions the genesis seed), torn down before AND after this file runs so
re-running it never leaves residue.

Cases:
  a-genesis-refusal          -- an INSERT attempted before the genesis seed exists is refused
                                 loudly (proven on a SEPARATE scratch schema pair with the seed
                                 deliberately withheld -- the --new-world scaffold always
                                 provisions one, so this polarity needs its own substrate).
  b-chain-builds-and-verifies -- three real rows written via `led`, `./verify-chain` reports
                                 INTACT.
  c-head-json-shape           -- `./verify-chain --head` emits exactly the spec's
                                 {world, max_id, head_hash, utc, apparatus_hash} shape, nothing
                                 else on stdout (`apparatus_hash` added 2026-07-12, BACKLOG
                                 "apparatus-flip-witnessing" -- additive to the original four-key
                                 shape, see verify-chain.tmpl's own module docstring).
  i-apparatus-hash-detects-flip -- a mechanism's mode in `.claude/apparatus.json` is edited with NO
                                 ledger row written at all: a second `--head` snapshot shows
                                 `apparatus_hash` CHANGED while `head_hash`/`max_id` stayed
                                 IDENTICAL (no ledger activity occurred) -- proving a flip between
                                 two signed heads is detectable purely from the apparatus_hash
                                 field, independent of the ledger chain it rides alongside.
  d-tamper-stale-hash-breaks-at-altered-row -- a historical row's CONTENT is altered directly
                                 (trigger bypassed, mirrors a schema-owner-level tamper) while its
                                 OWN row_hash is left stale: ./verify-chain reports BROKEN with
                                 first_break_id equal to the ALTERED row -- "breaks AT THE ALTERED
                                 ROW", the spec's own words, verified literally.
  e-tamper-fixed-hash-breaks-downstream -- the sophisticated variant: the tamperer ALSO rewrites
                                 the altered row's own row_hash to match its new content. The break
                                 then surfaces at the NEXT row instead (its predecessor-hash
                                 reference was computed against the row's OLD, honest hash) --
                                 still no later than immediately after the true alteration point.
  f-head-refuses-on-broken-chain -- `./verify-chain --head` against the broken chain from case d
                                 exits 1 with EMPTY stdout (never signs a head over a non-verified
                                 chain).
  g-differential-agree        -- the EXISTING SQL/ASP marriage differential (`engine/
                                 ledger_differential.py`) still verdicts AGREE against this s26
                                 world (proving s26 does not perturb the existing T_now facts),
                                 run against the INTACT (pre-tamper) state.
  h-null-vs-empty-string-collision-closed -- an out-of-frame hack-rationalization audit found
                                 that an EARLIER version of compute_row_hash() coalesced SQL NULL
                                 and '' to the identical serialized token, so tampering a row's
                                 `rationale` from NULL to '' would have produced NO detectable
                                 break anywhere in the chain -- a real collision, not merely an
                                 adversarial-hardening gap. Closed via a length-prefixed encoding
                                 (compute_row_hash()'s own header explains the fix); this case
                                 proves the specific collision no longer holds, in isolation (a
                                 direct SQL recomputation, not a full chain walk, so it does not
                                 entangle with cases d/e/f's own breaks), then restores the row
                                 so d/e/f below still start from a genuinely INTACT chain.

Usage: python3 seen-red/s26-row-hash-chain/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import os
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
VERIFY_CHAIN_TMPL = REPO / "bootstrap" / "templates" / "verify-chain.tmpl"
LINEAGE = REPO / "kernel" / "lineage"

PGHOST, PGDB = fixture_pghost(), "toy"
WORLD = "s26fxprobe"
GENESIS_WORLD_SCHEMA, GENESIS_WORLD_KERN, GENESIS_WORLD_ROLE = (
    "s26fxnogenesis", "s26fxnogenesis_kernel", "s26fxnogenesis_rw")

CHAIN_TO_S26 = ["s15-schema.sql", "s17-stamp-mechanism.sql", "s17-independence-vocabulary.sql",
                "s19-trigger-search-path.sql", "s20-obligation-grants-and-view-refresh.sql",
                "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
                "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
                "s25-commission-kind.sql", "s26-row-hash-chain.sql"]


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def teardown_all() -> None:
    for schema, kern, role in ((WORLD, f"{WORLD}_kernel", f"{WORLD}_rw"),
                                (GENESIS_WORLD_SCHEMA, GENESIS_WORLD_KERN, GENESIS_WORLD_ROLE)):
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
            f"DROP SCHEMA IF EXISTS {schema} CASCADE; DROP SCHEMA IF EXISTS {kern} CASCADE; "
            f"DROP OWNED BY {role};"])
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {role};"])


def apply_lineage(schema: str, kern: str, role: str) -> subprocess.CompletedProcess[str]:
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}"]
    for f in CHAIN_TO_S26:
        args += ["-f", str(LINEAGE / f)]
    return sh(args)


def psql_as(schema: str, role: str, sql: str) -> subprocess.CompletedProcess[str]:
    prefix = f"SET ROLE {role};\nSET search_path = {schema};\n"
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-tA", "-q",
               "-c", prefix + sql])


def run_verify_chain(world_dir: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PICKUP_DEPLOYMENT"] = str(world_dir / "deployment.json")
    return sh(["python3", str(VERIFY_CHAIN_TMPL), *extra], env=env)


def main() -> int:
    teardown_all()
    tmp = Path(tempfile.mkdtemp(prefix="s26-seenred-"))
    world_dir = tmp / WORLD
    failures: list[str] = []

    try:
        # --- a: genesis refusal, on a SEPARATE schema with the seed withheld ---------------------
        print(f"== a: applying s26 birth chain to {GENESIS_WORLD_SCHEMA}, WITHOUT seeding genesis ==")
        ra = apply_lineage(GENESIS_WORLD_SCHEMA, GENESIS_WORLD_KERN, GENESIS_WORLD_ROLE)
        if ra.returncode != 0:
            print("APPLY FAILED:", ra.stdout[-1500:], ra.stderr[-1500:])
            return 1
        ra2 = psql_as(GENESIS_WORLD_SCHEMA, GENESIS_WORLD_ROLE,
                      "INSERT INTO ledger (kind, statement) VALUES ('decision', 'no genesis yet');")
        ok_a = ra2.returncode != 0 and "no world-birth seed" in (ra2.stdout + ra2.stderr)
        check("a-genesis-refusal", ok_a,
              f"exit={ra2.returncode} stderr={(ra2.stdout + ra2.stderr).strip()[-200:]!r}", failures)

        # --- scaffold the real --new-world (provisions genesis automatically) -------------------
        print(f"== scaffolding throwaway --new-world {WORLD} (provisions genesis automatically) ==")
        r = sh(["bash", str(NEW_PROJECT), str(world_dir), "--new-world", WORLD,
                "--db", PGDB, "--host", PGHOST])
        if r.returncode != 0:
            print("SCAFFOLD FAILED:", r.stdout[-1500:], r.stderr[-1500:])
            return 1
        for verb in ("led", "verify-chain"):
            (world_dir / verb).chmod(0o755)
        genesis_ok = "one fresh genesis seed provisioned" in r.stdout
        print(f"  scaffold OK (genesis auto-provisioned: {genesis_ok}).\n")

        # --- b: three real rows via led, chain builds and verifies intact -----------------------
        for stmt in ("row one, via led", "row two, via led", "row three, via led"):
            rl = sh(["bash", str(world_dir / "led"), "decision", stmt], cwd=str(world_dir))
            if rl.returncode != 0:
                print("led write FAILED:", rl.stdout, rl.stderr)
                return 1
        rb = run_verify_chain(world_dir)
        ok_b = rb.returncode == 0 and rb.stdout.startswith("verify-chain: INTACT -- 3 row(s)")
        check("b-chain-builds-and-verifies", ok_b, rb.stdout.strip(), failures)

        # --- c: --head shape -----------------------------------------------------------------
        rc = run_verify_chain(world_dir, "--head")
        head_body = {}
        try:
            head_body = json.loads(rc.stdout.strip())
        except json.JSONDecodeError:
            pass
        apparatus_hash_c = head_body.get("apparatus_hash")
        ok_c = (rc.returncode == 0
                and set(head_body.keys()) == {"world", "max_id", "head_hash", "utc", "apparatus_hash"}
                and head_body.get("world") == WORLD
                and isinstance(apparatus_hash_c, str) and len(apparatus_hash_c) == 64)
        check("c-head-json-shape", ok_c, f"stdout={rc.stdout.strip()!r}", failures)

        # --- i: apparatus.json flip detected via apparatus_hash, with NO ledger activity ---------
        apparatus_path = world_dir / ".claude" / "apparatus.json"
        before_text = apparatus_path.read_text(encoding="utf-8")
        before_apparatus = json.loads(before_text)
        before_apparatus.setdefault("mechanisms", {})["mutation_observer"] = {"mode": "off"}
        apparatus_path.write_text(json.dumps(before_apparatus), encoding="utf-8")
        ri = run_verify_chain(world_dir, "--head")
        head_body_i = {}
        try:
            head_body_i = json.loads(ri.stdout.strip())
        except json.JSONDecodeError:
            pass
        ok_i = (ri.returncode == 0
                and head_body_i.get("apparatus_hash") != apparatus_hash_c
                and head_body_i.get("head_hash") == head_body.get("head_hash")
                and head_body_i.get("max_id") == head_body.get("max_id"))
        check("i-apparatus-hash-detects-flip", ok_i,
              f"before_apparatus_hash={apparatus_hash_c!r} after_apparatus_hash="
              f"{head_body_i.get('apparatus_hash')!r} head_hash_unchanged="
              f"{head_body_i.get('head_hash') == head_body.get('head_hash')}", failures)
        apparatus_path.write_text(before_text, encoding="utf-8")  # restore, so later cases are unaffected

        # --- g: the EXISTING SQL/ASP marriage differential still AGREEs on an s26 world (run
        # BEFORE any tampering below -- this case's job is proving s26 does not perturb the
        # existing T_now facts on a genuinely clean chain, not re-deriving a post-tamper state) --
        rg = sh(["python3", "engine/ledger_differential.py", WORLD], cwd=str(REPO),
                 env={**os.environ, "LEDGER_DEPLOYMENT": str(world_dir / "deployment.json")})
        ok_g = rg.returncode == 0 and "DIFFERENTIAL GREEN" in rg.stdout
        check("g-differential-agree", ok_g, f"diff_ok={'DIFFERENTIAL GREEN' in rg.stdout}", failures)

        # --- h: the NULL-vs-empty-string collision (found by an out-of-frame hack-rationalization
        # audit, closed in compute_row_hash() before this shipped -- see that function's own
        # header note). An EARLIER version of compute_row_hash() coalesced `rationale IS NULL` and
        # `rationale = ''` to the identical serialized token, so tampering one into the other left
        # the stored row_hash matching the ALTERED content -- a silent, undetectable collision.
        # Tested in ISOLATION here via a direct SQL recomputation (not a full verify-chain walk,
        # which would entangle this case's break with cases d/e/f's unrelated ones below): tamper
        # the last row's `rationale` from NULL to '' directly (trigger bypassed), then assert the
        # row's OWN stored hash no longer matches a fresh recomputation of its (now-altered)
        # content -- exactly the comparison ./verify-chain's walk performs per row.
        last_id_sql = f"SELECT id FROM {WORLD}.ledger ORDER BY id DESC LIMIT 1;"
        last_id = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAc", last_id_sql]).stdout.strip()
        rationale_before = psql_as(WORLD, f"{WORLD}_rw",
                                    f"SELECT rationale IS NULL FROM ledger WHERE id = {last_id};").stdout.strip()
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
            f"ALTER TABLE {WORLD}.ledger DISABLE TRIGGER append_only_row;"])
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
            f"UPDATE {WORLD}.ledger SET rationale = '' WHERE id = {last_id} AND rationale IS NULL;"])
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
            f"ALTER TABLE {WORLD}.ledger ENABLE TRIGGER append_only_row;"])
        rh_check = psql_as(WORLD, f"{WORLD}_rw",
            f"SELECT row_hash = {WORLD}.compute_row_hash(l, COALESCE("
            f"(SELECT p.row_hash FROM ledger p WHERE p.id < l.id ORDER BY p.id DESC LIMIT 1), "
            f"(SELECT seed FROM {WORLD}_kernel.chain_genesis LIMIT 1))) "
            f"FROM ledger l WHERE l.id = {last_id};")
        ok_h = rationale_before == "t" and rh_check.stdout.strip() == "f"
        check("h-null-vs-empty-string-collision-closed", ok_h,
              f"rationale_was_null={rationale_before == 't'} stored_hash_now_matches_altered_content="
              f"{rh_check.stdout.strip()} (expect 'f' -- the tamper must be DETECTABLE)", failures)
        # revert the tamper, so cases d/e/f below start from a genuinely clean, INTACT chain --
        # a fresh INSERT-free UPDATE back to NULL restores the ORIGINAL row_hash the trigger
        # already computed and stored before this case ran (never touched by this case), since
        # only `rationale` was changed above and row_hash was deliberately left untouched here too.
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
            f"ALTER TABLE {WORLD}.ledger DISABLE TRIGGER append_only_row;"])
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
            f"UPDATE {WORLD}.ledger SET rationale = NULL WHERE id = {last_id};"])
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
            f"ALTER TABLE {WORLD}.ledger ENABLE TRIGGER append_only_row;"])
        rh_restored = run_verify_chain(world_dir)
        if not rh_restored.stdout.startswith("verify-chain: INTACT"):
            check("h-restore-to-intact", False, rh_restored.stdout.strip(), failures)

        # --- d: tamper CONTENT only (stale row_hash) -> breaks AT the altered row ----------------
        target_row_sql = f"SELECT id FROM {WORLD}.ledger ORDER BY id LIMIT 1;"
        first_id = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAc", target_row_sql]).stdout.strip()
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
            f"ALTER TABLE {WORLD}.ledger DISABLE TRIGGER append_only_row;"])
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
            f"UPDATE {WORLD}.ledger SET statement = 'RETROACTIVE TAMPER (seen-red specimen)' "
            f"WHERE id = {first_id};"])
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
            f"ALTER TABLE {WORLD}.ledger ENABLE TRIGGER append_only_row;"])
        rd = run_verify_chain(world_dir)
        ok_d = (rd.returncode == 1 and f"first break at row id {first_id}" in rd.stdout)
        check("d-tamper-stale-hash-breaks-at-altered-row", ok_d, rd.stdout.strip(), failures)

        # --- f: --head refuses on the broken chain, empty stdout --------------------------------
        rf = run_verify_chain(world_dir, "--head")
        ok_f = rf.returncode == 1 and rf.stdout.strip() == "" and "not INTACT" in rf.stderr
        check("f-head-refuses-on-broken-chain", ok_f,
              f"exit={rf.returncode} stdout={rf.stdout!r} stderr_excerpt={rf.stderr.strip()[:120]!r}",
              failures)

        # --- e: tamperer ALSO fixes the row's own hash -> break moves downstream ----------------
        expected_hash = None
        for line in rd.stdout.splitlines():
            if "expected:" in line:
                expected_hash = line.split("expected:")[1].strip()
        ok_e = False
        detail_e = "could not extract expected hash from case d output"
        if expected_hash:
            sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
                f"ALTER TABLE {WORLD}.ledger DISABLE TRIGGER append_only_row;"])
            sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
                f"UPDATE {WORLD}.ledger SET row_hash = '{expected_hash}' WHERE id = {first_id};"])
            sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
                f"ALTER TABLE {WORLD}.ledger ENABLE TRIGGER append_only_row;"])
            re_ = run_verify_chain(world_dir)
            next_id = str(int(first_id) + 1)
            ok_e = re_.returncode == 1 and f"first break at row id {next_id}" in re_.stdout
            detail_e = re_.stdout.strip()
        check("e-tamper-fixed-hash-breaks-downstream", ok_e, detail_e, failures)

    finally:
        teardown_all()
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- s26 row_hash chain both-polarity proof (genesis refusal / builds+"
          "verifies / --head shape / apparatus_hash flip detection / differential AGREE / "
          "NULL-vs-empty-string collision closed / breaks-at-altered-row / breaks-downstream-if-"
          "hash-also-faked / --head refuses-on-broken), zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
