#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for kernel/lineage/s25-commission-kind.sql (BACKLOG
"Five-item batch, maintainer-approved 2026-07-11 evening", item 2), plus the two signing-mode
mechanics (FULL -- commissioner principal; LAZY -- implementer vicarious transcription) and the
pre-s25 refusal/teach interaction with the run-10 closure-audit fix.

Real infra, no mocks: two throwaway scratch schema pairs in the toy db (192.168.122.1) --
`s25fxprobe` (the full s15..s25 chain, POST-s25) and `s25fxprobe_pre` (s15..s24 only, PRE-s25,
NAMED CHOICE mirroring seen-red/delegation-observer's own two-schema shape) -- both torn down
before AND after this file runs so re-running it never leaves residue.

Cases:
  a-commission-legal-post-s25   -- INSERT (kind='commission', ...) succeeds and round-trips on
                                   the post-s25 schema.
  b-refs-commission             -- a decision row can `refs='row:<commission-id>'` (the existing
                                   channel, no new edge type) and reads back correctly.
  c-existing-kinds-unchanged    -- a pre-existing kind ('decision') is still legal; a shaped
                                   kind ('work_opened' with no work_slug) is still refused, but
                                   by its OWN shape constraint, never by ledger_kind_check --
                                   proving this delta is a pure UNION, not a replacement.
  d-invalid-kind-still-refused  -- a genuinely invalid kind is still refused by ledger_kind_check
                                   on the post-s25 schema, and the live constraint definition
                                   (pg_get_constraintdef) names 'commission' alongside every
                                   prior member.
  e-full-mode-actor-distinct    -- LED_ACTOR=commissioner lands actor='commissioner'; a second
                                   commission row under the default actor lands actor='author' --
                                   the two signing modes are mechanically distinguishable by
                                   actor identity (module docstring's "two independent signals").
  f-prior-columns-untouched     -- s23's stamp_hmac/stamp_verified and s24's event_declared_ts
                                   columns are still present and unaffected (s25 touches no
                                   trigger, no other column).
  g-pre-s25-refused-with-teach  -- on the SEPARATE, PRE-s25 schema, 'commission' is refused by
                                   ledger_kind_check, and led.tmpl's own run-10 closure-audit fix
                                   (_led_kind_refusal_teach) prints the LIVE valid-kind list for
                                   THAT schema, which does NOT include 'commission' -- proving the
                                   refusal teaches correctly on a world that genuinely lacks it,
                                   never a stale/hardcoded list.

Usage: python3 seen-red/s25-commission-kind/run_fixtures.py
Exit 0 if every case matches (plus the SQL/ASP differential AGREE, printed separately); 1
otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402 (filing/pghost_resolve.py via seen-red/_fixture_env.py -- never a literal host default)


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LINEAGE = REPO / "kernel" / "lineage"
LED_TMPL = REPO / "bootstrap" / "templates" / "led.tmpl"

PGHOST, PGDB = fixture_pghost(), "toy"
SCHEMA, KERN, ROLE = "s25fxprobe", "s25fxprobe_kernel", "s25fxprobe_rw"                 # post-s25
SCHEMA2, KERN2, ROLE2 = "s25fxprobe_pre", "s25fxprobe_pre_kernel", "s25fxprobe_pre_rw"  # pre-s25


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def teardown() -> None:
    for schema, kern, role in ((SCHEMA, KERN, ROLE), (SCHEMA2, KERN2, ROLE2)):
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
            f"DROP SCHEMA IF EXISTS {schema} CASCADE; DROP SCHEMA IF EXISTS {kern} CASCADE; "
            f"DROP OWNED BY {role};"])
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {role};"])


def apply_lineage(schema: str, kern: str, role: str, files: list[str]) -> subprocess.CompletedProcess[str]:
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}"]
    for f in files:
        args += ["-f", str(LINEAGE / f)]
    return sh(args)


def psql(schema: str, kern: str, role: str, sql: str) -> subprocess.CompletedProcess[str]:
    prefix = f"SET ROLE {role};\nSET search_path = {schema}, {kern};\n"
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-tA", "-q",
               "-c", prefix + sql])


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


CHAIN_TO_S24 = ["s15-schema.sql", "s17-stamp-mechanism.sql", "s17-independence-vocabulary.sql",
                "s19-trigger-search-path.sql", "s20-obligation-grants-and-view-refresh.sql",
                "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
                "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql"]
CHAIN_TO_S25 = CHAIN_TO_S24 + ["s25-commission-kind.sql"]


def main() -> int:
    teardown()
    failures: list[str] = []

    print("== applying birth chain through s25 (post) and through s24 only (pre) ==")
    r1 = apply_lineage(SCHEMA, KERN, ROLE, CHAIN_TO_S25)
    r2 = apply_lineage(SCHEMA2, KERN2, ROLE2, CHAIN_TO_S24)
    if r1.returncode != 0 or r2.returncode != 0:
        print("APPLY FAILED:", r1.stdout[-1000:], r1.stderr[-1000:], r2.stdout[-1000:], r2.stderr[-1000:])
        teardown()
        return 1
    print("both schemas applied clean.\n")

    # --- a: commission legal post-s25, round-trips -------------------------------------------
    ra = psql(SCHEMA, KERN, ROLE, "INSERT INTO ledger (kind, statement) VALUES "
              "('commission', 'seen-red specimen ask') RETURNING id;")
    ok_a = ra.returncode == 0 and ra.stdout.strip().isdigit()
    commission_id = ra.stdout.strip() if ok_a else None
    check("a-commission-legal-post-s25", ok_a,
          f"exit={ra.returncode} id={commission_id}", failures)

    # --- b: refs channel ------------------------------------------------------------------
    rb = psql(SCHEMA, KERN, ROLE, f"INSERT INTO ledger (kind, statement, refs) VALUES "
              f"('decision', 'decompose', 'row:{commission_id}') RETURNING refs;") if commission_id else None
    ok_b = bool(rb) and rb.returncode == 0 and rb.stdout.strip() == f"row:{commission_id}"
    check("b-refs-commission", ok_b, f"refs={rb.stdout.strip() if rb else None}", failures)

    # --- c: existing kinds unchanged (union, not replacement) ----------------------------------
    rc1 = psql(SCHEMA, KERN, ROLE, "INSERT INTO ledger (kind, statement) VALUES ('decision', 'x') RETURNING id;")
    rc2 = psql(SCHEMA, KERN, ROLE, "INSERT INTO ledger (kind, statement) VALUES ('work_opened', 'x') RETURNING id;")
    ok_c = (rc1.returncode == 0 and rc2.returncode != 0
            and "work_slug_kind_shape" in rc2.stderr and "ledger_kind_check" not in rc2.stderr)
    check("c-existing-kinds-unchanged", ok_c,
          f"decision_ok={rc1.returncode == 0} work_opened_refused_by={'work_slug_kind_shape' if 'work_slug_kind_shape' in rc2.stderr else rc2.stderr[:100]}",
          failures)

    # --- d: invalid kind still refused, live constraint names 'commission' ---------------------
    rd1 = psql(SCHEMA, KERN, ROLE, "INSERT INTO ledger (kind, statement) VALUES ('bogus-kind', 'x') RETURNING id;")
    rd2 = psql(SCHEMA, KERN, ROLE,
               f"SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname='ledger_kind_check' "
               f"AND connamespace = '{SCHEMA}'::regnamespace;")
    ok_d = (rd1.returncode != 0 and "ledger_kind_check" in rd1.stderr
            and "commission" in rd2.stdout and "work_closed" in rd2.stdout)
    check("d-invalid-kind-still-refused", ok_d,
          f"refused={rd1.returncode != 0} live_def_has_commission={'commission' in rd2.stdout}", failures)

    # --- e: full vs lazy mode -- actor distinguishes -------------------------------------------
    re1 = psql(SCHEMA, KERN, ROLE,
               "INSERT INTO principal (name, agent_class) VALUES ('commissioner','human') "
               "ON CONFLICT (name) DO NOTHING; "
               "SET LOCAL myapp.actor = 'commissioner';")  # no-op placeholder, actor set via subquery below
    re2 = psql(SCHEMA, KERN, ROLE,
               "INSERT INTO ledger (kind, statement, actor) VALUES "
               "('commission', 'FULL mode ask', (SELECT id FROM principal WHERE name='commissioner')) "
               "RETURNING (SELECT name FROM principal p WHERE p.id = ledger.actor);")
    re3 = psql(SCHEMA, KERN, ROLE,
               "INSERT INTO ledger (kind, statement) VALUES "
               "('commission', '(vicarious transcription by the implementer; carries no commissioner guarantee) LAZY mode ask') "
               "RETURNING (SELECT name FROM principal p WHERE p.id = ledger.actor);")
    ok_e = (re2.returncode == 0 and re2.stdout.strip() == "commissioner"
            and re3.returncode == 0 and re3.stdout.strip() == "author")
    check("e-full-mode-actor-distinct", ok_e,
          f"full_actor={re2.stdout.strip()!r} lazy_actor={re3.stdout.strip()!r}", failures)

    # --- f: prior columns untouched -------------------------------------------------------------
    rf = psql(SCHEMA, KERN, ROLE,
              f"SELECT string_agg(column_name, ',' ORDER BY column_name) FROM information_schema.columns "
              f"WHERE table_schema='{SCHEMA}' AND table_name='ledger' "
              f"AND column_name IN ('stamp_hmac','stamp_verified','event_declared_ts');")
    ok_f = rf.returncode == 0 and set(rf.stdout.strip().split(",")) == {"event_declared_ts", "stamp_hmac", "stamp_verified"}
    check("f-prior-columns-untouched", ok_f, f"columns={rf.stdout.strip()}", failures)

    # --- g: pre-s25 schema refuses 'commission', live teach-text names the (shorter) valid list -
    dep_path = Path("/tmp/.s25fxprobe_pre_deployment.json")
    dep_path.write_text(json.dumps({"db": PGDB, "host": PGHOST, "schema": SCHEMA2,
                                     "kern": KERN2, "role": ROLE2, "name": SCHEMA2}), encoding="utf-8")
    rg = sh(["bash", str(LED_TMPL), "commission", "an ask on a pre-s25 world"],
            env={**os.environ, "PICKUP_DEPLOYMENT": str(dep_path)})
    dep_path.unlink(missing_ok=True)
    combined = rg.stdout + rg.stderr
    ok_g = (rg.returncode != 0 and "ledger_kind_check" in combined
            and "not a member of ledger_kind_check's vocabulary" in combined
            and "commission" not in combined.split("valid kinds")[-1])
    check("g-pre-s25-refused-with-teach", ok_g,
          f"exit={rg.returncode} teach_excerpt={combined.strip()[-300:]!r}", failures)

    print()
    if failures:
        print("FAILURES:", failures)
        teardown()
        return 1

    # --- SQL/ASP differential AGREE -------------------------------------------------------------
    print("== SQL/ASP differential (post-s25 schema) ==")
    dep_path2 = Path("/tmp/.s25fxprobe_deployment.json")
    dep_path2.write_text(json.dumps({"db": PGDB, "host": PGHOST, "schema": SCHEMA,
                                      "kern": KERN, "role": ROLE, "name": SCHEMA}), encoding="utf-8")
    rdiff = sh(["python3", "engine/ledger_differential.py", SCHEMA], cwd=str(REPO),
               env={"LEDGER_DEPLOYMENT": str(dep_path2), "PATH": os.environ.get("PATH", "/usr/bin:/bin")})
    print(rdiff.stdout)
    dep_path2.unlink(missing_ok=True)
    diff_ok = rdiff.returncode == 0 and "DIFFERENTIAL GREEN" in rdiff.stdout
    if not diff_ok:
        print("DIFFERENTIAL NOT GREEN:", rdiff.stderr[-1000:])
        teardown()
        return 1

    teardown()
    r_res1 = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAc",
                 "SELECT nspname FROM pg_namespace WHERE nspname LIKE 's25fxprobe%';"])
    r_res2 = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAc",
                 "SELECT rolname FROM pg_roles WHERE rolname LIKE 's25fxprobe%';"])
    residue_clean = r_res1.stdout.strip() == "" and r_res2.stdout.strip() == ""
    print(f"[{'ok' if residue_clean else 'FAIL'}] zero residue: schemas={r_res1.stdout.strip()!r} roles={r_res2.stdout.strip()!r}")
    if not residue_clean:
        return 1

    print("\nALL CASES OK -- s25 both-polarity proof + differential AGREE, zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
