#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T07:01:00Z
#   last-change: 2026-07-15T07:01:28Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for the sec-10 amendment of
kernel/lineage/s29-obligation-item-key-and-typed-close.sql (design/MAINT-COUNTERSIGN-CLOSE-
SEMANTICS-SPEC.md sec-10, "the pre-migration epoch"; ratified conditionally, ledger decision row
935). Companion to seen-red/s29-obligation-item-key-and-typed-close/run_fixtures.py (Element A/B/C
proper, unaffected by this amendment except where its own case j needed updating for s29 now
being wired into --new-world -- see that file's own scaffold_classic_s28_only()).

Real infra, no mocks: a throwaway scratch schema pair in the toy db (s15..s28 applied manually,
mirroring the ent rehearsal's own shape -- historical work_closed rows inserted BEFORE s29 is
applied, exactly the "157 pre-existing rows" scenario that falsified sec-7's original claim),
torn down before AND after this file runs.

Cases:
  pre-epoch-exempt            -- a work_closed row that predates s29 (inserted before the file was
                                  ever applied, carrying no disposition -- structurally impossible
                                  to have one) is NOT retroactively refused by the apply itself
                                  (ADD CONSTRAINT does not scan it -- there is no CONSTRAINT left
                                  to scan with) and remains queryable with disposition NULL.
  post-epoch-review-silent-refused -- a NEW work_closed row (id > epoch) with no disposition is
                                  REFUSED, teach-text naming the epoch and both constructors.
  post-epoch-witnessed-accepted -- a NEW work_closed row past the epoch WITH a disposition
                                  succeeds exactly as Element B always intended.
  idempotent-reapply           -- re-running s29's own file a second time, against a schema whose
                                  ledger has grown since the first apply, does NOT widen (or
                                  otherwise touch) the already-fixed epoch value.
  epoch-zero-fresh-world       -- a --new-world birth-chain scaffold (s29 now wired into
                                  new-project.sh's own LINEAGE_CHAIN, this session) yields
                                  migration_epoch.epoch = 0, and a review-silent close is refused
                                  on THAT world's very first work_closed row (id=... > 0 =
                                  governed) -- "birth-chain worlds get epoch 0 -- all rows
                                  governed, semantics unchanged", verified, not merely asserted.

Usage: python3 seen-red/s29-migration-epoch/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
S29 = REPO / "kernel" / "lineage" / "s29-obligation-item-key-and-typed-close.sql"
S15_TO_S28 = [
    "s15-schema.sql", "s17-stamp-mechanism.sql", "s17-independence-vocabulary.sql",
    "s19-trigger-search-path.sql", "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
    "s25-commission-kind.sql", "s26-row-hash-chain.sql", "s28-work-parent-edge.sql",
]

PGHOST, PGDB = "192.168.122.1", "toy"
WORLD = "s29epprobe"
FRESH_WORLD = "s29epfresh"


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
                 f"DROP SCHEMA IF EXISTS {world}_kernel CASCADE; "
                 f"DROP OWNED BY {world}_rw;"])
    psql(["-c", f"DROP ROLE IF EXISTS {world}_rw;"])


def teardown_all() -> None:
    teardown(WORLD)
    teardown(FRESH_WORLD)


def main() -> int:
    teardown_all()
    failures: list[str] = []
    tmps: list[Path] = []
    try:
        # --- s15..s28 onto a scratch pair, mirroring this file's own VALIDATE recipe ------------
        schema, kern, role = WORLD, f"{WORLD}_kernel", f"{WORLD}_rw"
        args = ["-v", "ON_ERROR_STOP=1", "-v", f"schema={schema}", "-v", f"kern={kern}",
                "-v", f"role={role}"]
        for name in S15_TO_S28:
            args += ["-f", str(REPO / "kernel" / "lineage" / name)]
        r = psql(args)
        if r.returncode != 0:
            print("s15..s28 APPLY FAILED:", r.stdout[-1500:], r.stderr[-1500:])
            return 1
        psql(["-q", "-v", "ON_ERROR_STOP=1", "-c",
              f"INSERT INTO {kern}.chain_genesis (seed) VALUES ('deadbeef00112233445566778899aabb') "
              f"ON CONFLICT (only_one) DO NOTHING;"])

        # --- insert TWO historical rows BEFORE s29 exists on this schema (ent's own shape: a
        # work_closed row with no disposition column, because the column did not exist yet) -----
        r = psql(["-v", "ON_ERROR_STOP=1", "-c", f"""
            SET ROLE {role}; SET search_path = {schema};
            INSERT INTO ledger (session,kind,statement,actor,work_slug,work_title)
              VALUES ('probe','work_opened','open hist','1','item-hist','Hist');
            INSERT INTO ledger (session,kind,statement,actor,work_slug,work_resolution,work_witness)
              VALUES ('probe','work_closed','close hist','1','item-hist','shipped','commit-hist');
        """])
        if r.returncode != 0:
            print("HISTORICAL ROW SETUP FAILED:", r.stdout, r.stderr)
            return 1

        # --- apply s29 IN PLACE on top of this pre-existing history (the ent scenario) ----------
        r = psql(["-v", "ON_ERROR_STOP=1", "-v", f"schema={schema}", "-v", f"kern={kern}",
                  "-v", f"role={role}", "-v", "epoch_dump_path=/tmp/probe-dump-1.sql",
                  "-v", "epoch_applied_by=fixture-first-apply", "-f", str(S29)])
        if r.returncode != 0:
            print("s29 IN-PLACE APPLY FAILED (this IS the ent falsification if it happens):",
                  r.stdout[-2000:], r.stderr[-2000:])
            return 1
        epoch1 = psql(["-tA", "-c", f"SELECT epoch FROM {kern}.migration_epoch;"]).stdout.strip()

        # --- pre-epoch-exempt: the historical row survives, disposition still NULL, queryable ---
        hist = psql(["-tA", "-c",
                     f"SELECT id, work_review_disposition IS NULL FROM {schema}.ledger "
                     f"WHERE kind='work_closed' AND work_slug='item-hist';"]).stdout.strip()
        ok_pre = hist.endswith("|t") and int(hist.split("|")[0]) <= int(epoch1)
        check("pre-epoch-exempt", ok_pre,
              f"epoch={epoch1} historical_row(id|disposition_is_null)={hist!r}", failures)

        # --- open item-new as its OWN committed statement (a separate psql -c call): the silent
        # close attempt below MUST fail and roll back on its OWN, without also erasing the open --
        # a single `-c` string sends every statement in it as ONE implicit transaction, so the
        # open has to be independently committed first or its own rollback would falsely blame
        # the NEXT case (witnessed-acceptance) for "item-new has no opening act" -- witnessed
        # directly authoring this fixture (first draft combined them, both cases below failed for
        # exactly this reason, not the epoch logic).
        r = psql(["-v", "ON_ERROR_STOP=1", "-c", f"""
            SET ROLE {role}; SET search_path = {schema};
            INSERT INTO ledger (session,kind,statement,actor,work_slug,work_title)
              VALUES ('probe','work_opened','open new','1','item-new','New');
        """])
        if r.returncode != 0:
            print("item-new OPEN FAILED:", r.stdout, r.stderr)
            return 1

        # --- post-epoch-review-silent-refused ----------------------------------------------------
        r = psql(["-v", "ON_ERROR_STOP=1", "-c", f"""
            SET ROLE {role}; SET search_path = {schema};
            INSERT INTO ledger (session,kind,statement,actor,work_slug,work_resolution)
              VALUES ('probe','work_closed','close new silent','1','item-new','dropped');
        """])
        out = r.stdout + r.stderr
        ok_silent = (r.returncode != 0 and "carries no review disposition" in out
                     and "sec-10 epoch amendment" in out and f"(id {epoch1}" in out)
        check("post-epoch-review-silent-refused", ok_silent,
              f"exit={r.returncode} excerpt={out.strip()[-400:]!r}", failures)

        # --- post-epoch-witnessed-accepted -------------------------------------------------------
        r = psql(["-v", "ON_ERROR_STOP=1", "-c", f"""
            SET ROLE {role}; SET search_path = {schema};
            INSERT INTO ledger (session,kind,statement,actor,work_slug,work_resolution,
                                 work_review_disposition,work_review_ref)
              VALUES ('probe','work_closed','close new witnessed','1','item-new','dropped',
                      'witnessed','ref-new-1');
        """])
        ok_witnessed = r.returncode == 0
        check("post-epoch-witnessed-accepted", ok_witnessed,
              f"exit={r.returncode} stderr={r.stderr.strip()[-200:]!r}", failures)

        # --- idempotent-reapply: ledger has grown (item-new's rows exist now); re-running s29
        # must NOT move the epoch, and must not error ---------------------------------------------
        r = psql(["-v", "ON_ERROR_STOP=1", "-v", f"schema={schema}", "-v", f"kern={kern}",
                  "-v", f"role={role}", "-v", "epoch_dump_path=/tmp/probe-dump-2-SHOULD-BE-IGNORED.sql",
                  "-v", "epoch_applied_by=fixture-second-apply-SHOULD-BE-IGNORED", "-f", str(S29)])
        epoch2_row = psql(["-tA", "-c",
                           f"SELECT epoch, dump_path, applied_by FROM {kern}.migration_epoch;"]).stdout.strip()
        ok_idem = (r.returncode == 0
                   and epoch2_row == f"{epoch1}|/tmp/probe-dump-1.sql|fixture-first-apply")
        check("idempotent-reapply", ok_idem,
              f"reapply_exit={r.returncode} migration_epoch_row_after_reapply={epoch2_row!r} "
              f"(expected epoch UNCHANGED at {epoch1}, provenance UNCHANGED from the FIRST apply)",
              failures)

        # --- epoch-zero-fresh-world: a birth-chain --new-world scaffold now applies s29
        # automatically (this session's new-project.sh wiring) and must self-seed epoch=0 --------
        tmp = Path(tempfile.mkdtemp(prefix=f"{FRESH_WORLD}-seenred-"))
        tmps.append(tmp)
        world_dir = tmp / FRESH_WORLD
        r = sh(["bash", str(NEW_PROJECT), str(world_dir), "--new-world", FRESH_WORLD,
                "--db", PGDB, "--host", PGHOST])
        if r.returncode != 0:
            print("FRESH --new-world SCAFFOLD FAILED:", r.stdout[-1500:], r.stderr[-1500:])
            return 1
        for verb in ("led", "judge", "pickup"):
            p = world_dir / verb
            if p.exists():
                p.chmod(0o755)
        dep = json.loads((world_dir / "deployment.json").read_text(encoding="utf-8"))
        fschema, fkern = dep["schema"], dep["kern"]
        fresh_epoch = psql(["-tA", "-c", f"SELECT epoch FROM {fkern}.migration_epoch;"]).stdout.strip()
        led = world_dir / "led"
        sh(["bash", str(led), "work", "open", "fresh-item", "Fresh"], cwd=str(world_dir))
        sh(["bash", str(led), "work", "claim", "fresh-item"], cwd=str(world_dir))
        rj = sh(["bash", str(led), "work", "close", "fresh-item", "dropped"], cwd=str(world_dir))
        out_j = rj.stdout + rj.stderr
        ok_fresh = (fresh_epoch == "0" and rj.returncode != 0
                    and "unrepresentable" in out_j)
        check("epoch-zero-fresh-world", ok_fresh,
              f"migration_epoch.epoch={fresh_epoch!r} (expect '0') "
              f"review_silent_close_on_fresh_world_refused={rj.returncode != 0} "
              f"excerpt={out_j.strip()[-250:]!r}", failures)

    finally:
        teardown_all()
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- s29 sec-10 migration-epoch amendment both-polarity proof "
          "(pre-epoch historical close exempt by type / post-epoch review-silent close refused, "
          "teach-text naming the epoch / post-epoch witnessed close accepted / idempotent "
          "re-apply never widens or re-provenances an already-fixed epoch / birth-chain world "
          "self-seeds epoch=0 and governs its very first close), zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
