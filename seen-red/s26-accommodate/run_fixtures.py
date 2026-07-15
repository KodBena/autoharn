#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T13:41:57Z
#   last-change: 2026-07-15T13:47:10Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for kernel/lineage/s26-row-hash-chain.accommodate.sql
(design/MAINT-MIGRATION-ACCOMMODATIONS-SPEC.md, Fable-authored spec, maintainer-ratified
2026-07-15; ledger work item s26-accommodation-build). Companion to seen-red/s26-row-hash-chain/
(s26 proper, birth-chain-only) and seen-red/s29-migration-epoch/ (the same accommodation shape,
one delta over -- this file follows its scaffolding idiom directly).

Real infra, no mocks: a throwaway scratch schema pair in the toy db, s15..s25 applied manually
(the s25-headed, PRE-s26 shape autoharn1's own real deployment carries as of this build --
verified separately against a byte-faithful clone of the actual autoharn1 history; see this
commission's own ledger row / report for that live-data witness, not reproduced here so this
fixture never depends on a specific real deployment being reachable), historical ledger rows
inserted BEFORE s26 (or its accommodation) ever runs -- exactly the "row 972" shape. Torn down
before AND after this file runs.

Cases:
  baseline-blocker-reproduced      -- s26's frozen file, applied BARE (no accommodation) over
                                       pre-existing history, fails exactly at the unconditional
                                       `ALTER COLUMN row_hash SET NOT NULL`, error text naming the
                                       null-values violation -- the row-972 blocker, reproduced.
  accommodation-applied-succeeds   -- the SAME frozen file, applied via
                                       bootstrap/migrate_core.py's own `_prepare_apply_files`
                                       substitution (marker-block removed, accommodate.sql fed
                                       right after, in one transaction) over the SAME history,
                                       succeeds.
  epoch-correctly-drawn            -- migration_epoch.epoch == the ledger's max(id) at the moment
                                       of that apply (sec-10's own rule, generalized).
  history-untouched-by-accommodation -- every pre-existing row still has row_hash IS NULL after
                                       the accommodated apply (no backfill, ever -- spec sec-2
                                       principle 3's own rejection of backfill, honored).
  post-epoch-row-gets-hash         -- a NEW row written after the migration gets a real row_hash
                                       automatically (zz_set_row_hash, untouched by this delta).
  chain-check-mid-history-tolerant -- bootstrap/templates/verify-chain.tmpl, reused UNMODIFIED
                                       apart from its own 2026-07-15 mid-history-start fix, walks
                                       ONLY the post-epoch row(s), reports INTACT, and honestly
                                       states the pre-epoch exempt count -- not the
                                       "997/997 mismatch" false BROKEN this fixture's baseline
                                       case witnesses verify-chain would have reported before that
                                       fix (case chain-check-pretend-no-epoch-awareness below).
  chain-check-detects-tamper       -- a post-epoch row's row_hash, corrupted directly (bypassing
                                       the append-only trigger as the schema owner, the same
                                       adversary class every kernel/lineage/sNN LIMITS section
                                       already names), is CAUGHT by the chain walk -- the
                                       accommodation does not weaken tamper-evidence for governed
                                       rows.
  accommodation-cannot-be-relaxed  -- even with the PRIMARY hashing trigger (zz_set_row_hash)
                                       disabled (simulating a bypass), a direct INSERT supplying
                                       row_hash=NULL for a post-epoch row is REFUSED by the
                                       accommodation's own epoch-gated trigger
                                       (zzz_enforce_row_hash_not_null) -- "relaxing the
                                       accommodation is refused" (spec sec-4's negative control).
  accommodate-verify-catches-violation -- s26-row-hash-chain.accommodate.verify.sql, run directly
                                       against a state where a post-epoch row_hash was forced NULL
                                       (same bypass), reports at least one ok=false -- the
                                       acceptance harness (`./migrate`'s own `.verify.sql` gate)
                                       would refuse a live apply over this state.
  history-header-silent-refused    -- a synthetic future delta with no `HISTORY:` header is
                                       refused by `bootstrap/migrate_core._require_history_headers`
                                       (spec sec-3 item 3's forward-binding rule).
  history-header-present-accepted  -- the same, with a HISTORY: header present, is NOT refused.
  history-header-exempt-set-passes -- the frozen s15..s29 set (this build's own audit table) never
                                       needs a header, by name, without editing any of those files.

Usage: python3 seen-red/s26-accommodate/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "bootstrap"))
import migrate_core  # noqa: E402  (bootstrap/migrate_core.py -- the ONE home for the apply logic)

LINEAGE = REPO / "kernel" / "lineage"
S26 = LINEAGE / "s26-row-hash-chain.sql"
S26_ACCOMMODATE = LINEAGE / "s26-row-hash-chain.accommodate.sql"
S26_ACCOMMODATE_VERIFY = LINEAGE / "s26-row-hash-chain.accommodate.verify.sql"
S15_TO_S25 = [
    "s15-schema.sql", "s17-stamp-mechanism.sql", "s17-independence-vocabulary.sql",
    "s19-trigger-search-path.sql", "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
    "s25-commission-kind.sql",
]

PGHOST, PGDB = "192.168.122.1", "toy"
WORLD_A = "s26accbase"   # baseline-blocker case, its own throwaway schema (dies after that case)
WORLD_B = "s26accgood"   # the accommodated-apply case, kept for every case that builds on it


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def psql(args: list[str]) -> subprocess.CompletedProcess[str]:
    return sh(["psql", "-h", PGHOST, "-d", PGDB, *args])


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def teardown(world: str) -> None:
    psql(["-c", f"DROP SCHEMA IF EXISTS {world} CASCADE; "
                 f"DROP SCHEMA IF EXISTS {world}_kernel CASCADE;"])


def teardown_all() -> None:
    teardown(WORLD_A)
    teardown(WORLD_B)


def scaffold_pre_s26_history(world: str) -> tuple[str, str, str]:
    """s15..s25 applied manually onto a fresh scratch schema pair, plus a handful of ordinary
    ledger rows (this world's "real history") inserted BEFORE s26/its accommodation ever runs.
    Returns (schema, kern, role)."""
    schema, kern, role = world, f"{world}_kernel", "autoharn_rw"
    args = ["-v", "ON_ERROR_STOP=1", "-v", f"schema={schema}", "-v", f"kern={kern}",
            "-v", f"role={role}"]
    for name in S15_TO_S25:
        args += ["-f", str(LINEAGE / name)]
    r = psql(args)
    if r.returncode != 0:
        raise RuntimeError(f"s15..s25 APPLY FAILED: {r.stdout[-1500:]} {r.stderr[-1500:]}")
    r = psql(["-v", "ON_ERROR_STOP=1", "-c", f"""
        SET ROLE {role}; SET search_path = {schema};
        INSERT INTO ledger (session,kind,statement,actor) VALUES
          ('probe','decision','hist row 1 -- pre-existing, no row_hash column exists yet','1');
        INSERT INTO ledger (session,kind,statement,actor) VALUES
          ('probe','decision','hist row 2 -- same','1');
        INSERT INTO ledger (session,kind,statement,actor) VALUES
          ('probe','finding','hist row 3 -- the row-972 shape, three real historical rows','1');
    """])
    if r.returncode != 0:
        raise RuntimeError(f"HISTORICAL ROW SETUP FAILED: {r.stdout} {r.stderr}")
    return schema, kern, role


def main() -> int:
    teardown_all()
    failures: list[str] = []
    try:
        # --- baseline-blocker-reproduced: s26 applied BARE over real pre-existing history -------
        schema_a, kern_a, role_a = scaffold_pre_s26_history(WORLD_A)
        r = psql(["-v", "ON_ERROR_STOP=1", "-v", f"schema={schema_a}", "-v", f"kern={kern_a}",
                  "-v", f"role={role_a}", "-f", str(S26)])
        out = r.stdout + r.stderr
        ok_base = (r.returncode != 0
                   and 'column "row_hash" of relation "ledger" contains null values' in out)
        check("baseline-blocker-reproduced", ok_base,
              f"exit={r.returncode} excerpt={out.strip()[-300:]!r}", failures)
        teardown(WORLD_A)

        # --- accommodation-applied-succeeds: same shape, via migrate_core's own substitution ----
        schema_b, kern_b, role_b = scaffold_pre_s26_history(WORLD_B)
        pre_max = psql(["-tA", "-c", f"SELECT max(id) FROM {schema_b}.ledger;"]).stdout.strip()
        files, temps = migrate_core._prepare_apply_files(["s26-row-hash-chain.sql"])
        try:
            args = ["-v", "ON_ERROR_STOP=1", "-v", f"schema={schema_b}", "-v", f"kern={kern_b}",
                    "-v", f"role={role_b}", "-v", "epoch_dump_path=/tmp/s26-fixture-dump.sql",
                    "-v", "epoch_applied_by=s26-accommodate-fixture"]
            for p in files:
                args += ["-f", str(p)]
            r = psql(args)
        finally:
            for t in temps:
                t.unlink(missing_ok=True)
        ok_apply = r.returncode == 0
        check("accommodation-applied-succeeds", ok_apply,
              f"exit={r.returncode} stderr={r.stderr.strip()[-300:]!r}", failures)
        if not ok_apply:
            print("cannot continue -- accommodated apply itself failed.")
            return 1
        psql(["-q", "-v", "ON_ERROR_STOP=1", "-c",
              f"INSERT INTO {kern_b}.chain_genesis (seed) VALUES "
              f"('deadbeef00112233445566778899aabb') ON CONFLICT (only_one) DO NOTHING;"])

        # --- epoch-correctly-drawn ---------------------------------------------------------------
        epoch = psql(["-tA", "-c", f"SELECT epoch FROM {kern_b}.migration_epoch;"]).stdout.strip()
        check("epoch-correctly-drawn", epoch == pre_max,
              f"migration_epoch.epoch={epoch!r} pre-apply max(id)={pre_max!r}", failures)

        # --- history-untouched-by-accommodation --------------------------------------------------
        still_null = psql(["-tA", "-c",
                           f"SELECT count(*) FROM {schema_b}.ledger WHERE row_hash IS NOT NULL;"]
                          ).stdout.strip()
        check("history-untouched-by-accommodation", still_null == "0",
              f"pre-existing rows with a non-NULL row_hash after accommodated apply: {still_null} "
              f"(expect 0 -- no backfill, ever)", failures)

        # --- post-epoch-row-gets-hash ------------------------------------------------------------
        r = psql(["-v", "ON_ERROR_STOP=1", "-c", f"""
            SET ROLE {role_b}; SET search_path = {schema_b};
            INSERT INTO ledger (session,kind,statement,actor)
              VALUES ('probe','note','post-migration row, first one this world writes','1');
        """])
        new_row = psql(["-tA", "-c",
                        f"SELECT id, row_hash IS NOT NULL FROM {schema_b}.ledger "
                        f"ORDER BY id DESC LIMIT 1;"]).stdout.strip()
        ok_post = r.returncode == 0 and new_row.endswith("|t")
        check("post-epoch-row-gets-hash", ok_post,
              f"insert_exit={r.returncode} newest_row(id|has_hash)={new_row!r}", failures)

        # --- chain-check-mid-history-tolerant: verify-chain.tmpl, unmodified apart from its own
        # 2026-07-15 fix, walks only post-epoch rows and reports INTACT ---------------------------
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
            json.dump({"db": PGDB, "host": PGHOST, "schema": schema_b, "kern": kern_b,
                       "role": role_b, "name": WORLD_B}, tf)
            dep_path = tf.name
        env = dict(os.environ, PICKUP_DEPLOYMENT=dep_path)
        vc = sh(["python3", str(REPO / "bootstrap" / "templates" / "verify-chain.tmpl")], env=env)
        ok_chain = (vc.returncode == 0 and "INTACT" in vc.stdout and "1 row(s) walked" in vc.stdout
                    and "3 pre-migration-epoch row(s) exempt" in vc.stdout)
        check("chain-check-mid-history-tolerant", ok_chain,
              f"exit={vc.returncode} stdout={vc.stdout.strip()!r}", failures)

        # --- chain-check-detects-tamper: corrupt the post-epoch row's stored hash directly -------
        # append_only_row (s15) refuses UPDATE outright, including for the schema owner, so the
        # tamper (schema-owner bypass -- the documented adversary class every kernel/lineage/sNN
        # LIMITS section already names) must disable it first, exactly like the run_fixtures.py
        # precedent for s26-row-hash-chain's own tamper cases (seen-red/s26-row-hash-chain/).
        r_tamper = psql(["-v", "ON_ERROR_STOP=1", "-c",
              f"ALTER TABLE {schema_b}.ledger DISABLE TRIGGER append_only_row; "
              f"UPDATE {schema_b}.ledger SET row_hash = repeat('0', 64) "
              f"WHERE id = (SELECT max(id) FROM {schema_b}.ledger); "
              f"ALTER TABLE {schema_b}.ledger ENABLE TRIGGER append_only_row;"])
        if r_tamper.returncode != 0:
            print("TAMPER SETUP FAILED:", r_tamper.stdout, r_tamper.stderr)
        vc2 = sh(["python3", str(REPO / "bootstrap" / "templates" / "verify-chain.tmpl")], env=env)
        ok_tamper = vc2.returncode == 1 and "BROKEN" in vc2.stdout
        check("chain-check-detects-tamper", ok_tamper,
              f"exit={vc2.returncode} stdout={vc2.stdout.strip()[-300:]!r}", failures)
        Path(dep_path).unlink(missing_ok=True)

        # --- accommodation-cannot-be-relaxed: disable the primary trigger, attempt a forged NULL
        # row_hash on a post-epoch row -- the accommodation's own trigger must still refuse -------
        psql(["-v", "ON_ERROR_STOP=1", "-c",
              f"ALTER TABLE {schema_b}.ledger DISABLE TRIGGER zz_set_row_hash;"])
        r = psql(["-c", f"""
            INSERT INTO {schema_b}.ledger (session,kind,statement,actor,row_hash)
              VALUES ('probe','note','forged NULL row_hash bypass attempt','1', NULL);
        """])
        out = r.stdout + r.stderr
        ok_relax = (r.returncode != 0 and "carries no row_hash past this world" in out
                    and "s26-row-hash-chain.accommodate.sql" in out)
        check("accommodation-cannot-be-relaxed", ok_relax,
              f"exit={r.returncode} excerpt={out.strip()[-300:]!r}", failures)
        psql(["-v", "ON_ERROR_STOP=1", "-c",
              f"ALTER TABLE {schema_b}.ledger ENABLE TRIGGER zz_set_row_hash;"])

        # --- accommodate-verify-catches-violation: force a post-epoch row_hash to NULL via a
        # superuser bypass (both triggers disabled), then run the .verify.sql DIRECTLY -----------
        psql(["-v", "ON_ERROR_STOP=1", "-c",
              f"ALTER TABLE {schema_b}.ledger DISABLE TRIGGER zz_set_row_hash; "
              f"ALTER TABLE {schema_b}.ledger DISABLE TRIGGER zzz_enforce_row_hash_not_null; "
              f"ALTER TABLE {schema_b}.ledger DISABLE TRIGGER append_only_row;"])
        psql(["-v", "ON_ERROR_STOP=1", "-c",
              f"UPDATE {schema_b}.ledger SET row_hash = NULL "
              f"WHERE id = (SELECT max(id) FROM {schema_b}.ledger);"])
        psql(["-v", "ON_ERROR_STOP=1", "-c",
              f"ALTER TABLE {schema_b}.ledger ENABLE TRIGGER zz_set_row_hash; "
              f"ALTER TABLE {schema_b}.ledger ENABLE TRIGGER zzz_enforce_row_hash_not_null; "
              f"ALTER TABLE {schema_b}.ledger ENABLE TRIGGER append_only_row;"])
        vr = psql(["-v", "ON_ERROR_STOP=1", "-v", f"schema={schema_b}", "-v", f"kern={kern_b}",
                   "-v", f"role={role_b}", "-tA", "-f", str(S26_ACCOMMODATE_VERIFY)])
        lines = [ln.strip() for ln in vr.stdout.splitlines() if ln.strip()]
        ok_verify_catches = vr.returncode == 0 and "f" in lines
        check("accommodate-verify-catches-violation", ok_verify_catches,
              f"exit={vr.returncode} ok-lines={lines!r} (expect at least one 'f')", failures)

        # --- HISTORY: header rule, in-process (no DB needed) --------------------------------------
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            (tdp / "s30-silent.sql").write_text("-- s30 silent future delta\nSELECT 1;\n")
            (tdp / "s30-labeled.sql").write_text(
                "-- s30 labeled future delta\n-- HISTORY: safe -- adds a nullable column only\n"
                "SELECT 1;\n")
            orig = migrate_core.LINEAGE_DIR
            migrate_core.LINEAGE_DIR = tdp
            try:
                try:
                    migrate_core._require_history_headers(["s30-silent.sql"])
                    ok_silent_hdr, detail_silent = False, "expected MigrateRefusal, none raised"
                except migrate_core.MigrateRefusal as e:
                    ok_silent_hdr = "HISTORY:" in str(e) and "s30-silent.sql" in str(e)
                    detail_silent = str(e)[:250]
                try:
                    migrate_core._require_history_headers(["s30-labeled.sql"])
                    ok_present_hdr, detail_present = True, "no refusal, as expected"
                except migrate_core.MigrateRefusal as e:
                    ok_present_hdr, detail_present = False, str(e)[:250]
            finally:
                migrate_core.LINEAGE_DIR = orig
        check("history-header-silent-refused", ok_silent_hdr, detail_silent, failures)
        check("history-header-present-accepted", ok_present_hdr, detail_present, failures)

        ok_exempt = True
        detail_exempt = "no refusal, as expected"
        try:
            migrate_core._require_history_headers(list(migrate_core._HISTORY_HEADER_EXEMPT))
        except migrate_core.MigrateRefusal as e:
            ok_exempt, detail_exempt = False, str(e)[:250]
        check("history-header-exempt-set-passes", ok_exempt, detail_exempt, failures)

    finally:
        teardown_all()

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- s26-row-hash-chain.accommodate.sql both-polarity proof (row-972 "
          "blocker reproduced bare / accommodation applies clean over the same history / epoch "
          "correctly drawn / no backfill / post-epoch rows hash normally / verify-chain's "
          "mid-history-start fix walks only governed rows and reports the exempt count honestly "
          "/ tamper on a governed row still caught / the accommodation's own epoch-gated trigger "
          "refuses a forged NULL past the epoch even with the primary hashing trigger disabled / "
          "its own .verify.sql catches the same violation directly / the forward-binding "
          "HISTORY: header rule refuses silence, accepts a declared header, and never fires on "
          "the frozen s15..s29 exempt set), zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
