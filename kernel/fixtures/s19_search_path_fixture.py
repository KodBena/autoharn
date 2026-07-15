#!/usr/bin/env python3
"""s19_search_path_fixture — proves the set_actor search-path foreclosure
(s19-trigger-search-path.sql) on a THROWAWAY kernel deployed to a NON-DEFAULT schema
(schema=s19val, kern=s19val_kernel — deliberately NOT the literal `kernel` the frozen s15
hardcodes), BOTH polarities in one run:

  RED  (pre-fix): with ONLY s15 applied, an actor-OMITTED insert by the subject role is
       REFUSED — s15's set_actor reads the hardcoded `kernel.principal_role`, which on a
       non-default-schema kernel resolves nothing (or the wrong kernel with no mapping for
       this role), so NEW.actor stays NULL and `actor NOT NULL` refuses the write. This is
       findings 16/37/45 reproduced.
  GREEN (post-fix): after applying s19, the SAME actor-omitted insert SUCCEEDS and the row
       carries the correct author principal — set_actor now resolves principal_role via the
       function's SET search_path (:schema, :kern), no schema literal.

The non-default schema is load-bearing: it is the exact condition the frozen hardcode
fails under. Run at real apply (kern='kernel') the pre-fix path would spuriously pass, so
the RED half MUST use a non-default kern — which it does.

Scratch-only (schemas s19val*, dropped after). Lazy imports banned.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "filing"))
import pghost_resolve  # noqa: E402 (filing/pghost_resolve.py -- never a literal host default)

PGHOST, DB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "harness"
SCHEMA, KERN, ROLE = "s19val", "s19val_kernel", "s19val_rw"
HERE = Path(__file__).resolve().parent
LINEAGE = HERE.parent / "lineage"


def psql(sql: str) -> tuple[bool, str]:
    cp = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-tA", "-v", "ON_ERROR_STOP=1", "-c", sql],
                        capture_output=True, text=True)
    return cp.returncode == 0, (cp.stdout + cp.stderr).strip()


def apply_ddl(fname: str) -> tuple[bool, str]:
    cp = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-v", "ON_ERROR_STOP=1",
                         "-v", f"schema={SCHEMA}", "-v", f"kern={KERN}", "-v", f"role={ROLE}",
                         "-f", str(LINEAGE / fname)], capture_output=True, text=True)
    return cp.returncode == 0, (cp.stdout + cp.stderr).strip()


def actor_omitted_insert(statement: str) -> tuple[bool, str]:
    # subject role, login-time search_path replicated; NO actor column supplied — set_actor must fill it.
    sql = (f"SET ROLE {ROLE}; SET search_path = {SCHEMA}, {KERN}; "
           f"INSERT INTO {SCHEMA}.ledger (kind, statement) VALUES ('decision', '{statement}');")
    return psql(sql)


def teardown() -> None:
    subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-c",
                    f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE; DROP SCHEMA IF EXISTS {KERN} CASCADE; "  # declared-drop: s19val (declared scratch/test reset)
                    f"DROP OWNED BY {ROLE}; DROP ROLE IF EXISTS {ROLE};"], capture_output=True, text=True)


def main() -> int:
    fails: list[str] = []
    ck = lambda cond, msg: fails.append(msg) if not cond else None  # noqa: E731

    teardown()
    ok, out = apply_ddl("s15-schema.sql")
    if not ok:
        print(f"# S19 FIXTURE SETUP FAILED (s15 apply): {out[-300:]}")
        return 1

    # --- RED: pre-fix, an actor-omitted write on a non-default-schema kernel is REFUSED ---
    red_ok, red_out = actor_omitted_insert("actor-omitted write (pre-s19)")
    ck(not red_ok,
       f"RED expected: pre-s19 actor-omitted write must be REFUSED on a non-default kern "
       f"(got ok={red_ok}: {red_out[-160:]})")
    print(f"# RED  witnessed (pre-s19): actor-omitted write refused -> {red_out.splitlines()[-1][:140] if red_out else '(no msg)'}")

    # --- apply the foreclosure ---
    ok, out = apply_ddl("s19-trigger-search-path.sql")
    if not ok:
        print(f"# S19 FIXTURE SETUP FAILED (s19 apply): {out[-300:]}")
        teardown()
        return 1

    # --- GREEN: post-fix, the SAME actor-omitted write SUCCEEDS and carries the author principal ---
    green_ok, green_out = actor_omitted_insert("actor-omitted write (post-s19)")
    ck(green_ok,
       f"GREEN expected: post-s19 actor-omitted write must SUCCEED (got ok={green_ok}: {green_out[-160:]})")
    if green_ok:
        actor_name = psql(
            f"SELECT p.name FROM {SCHEMA}.ledger l JOIN {KERN}.principal p ON p.id = l.actor "
            f"WHERE l.statement = 'actor-omitted write (post-s19)';")[1]
        ck(actor_name == "author",
           f"GREEN: the stamped actor must resolve to the 'author' principal via search_path "
           f"(got {actor_name!r})")
        print(f"# GREEN witnessed (post-s19): actor-omitted write accepted; actor resolved -> {actor_name!r}")

    teardown()

    if fails:
        print("# S19 SEARCH-PATH FIXTURE RED:")
        for f in fails:
            print(f"  !! {f}")
        return 1
    print("# S19 SEARCH-PATH FIXTURE GREEN — set_actor schema-literal class foreclosed: "
          "actor-omitted write refused pre-fix (findings 16/37/45 reproduced), accepted post-fix, "
          "on a NON-default-schema kernel.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
