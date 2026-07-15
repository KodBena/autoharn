#!/usr/bin/env python3
"""Seen-red specimen for the s19 set_actor search-path foreclosure (findings 16/37/45).

Reproduces the PRE-FIX red: with ONLY s15 applied to a kernel in a NON-DEFAULT schema
(kern=s19red_kernel, NOT the literal `kernel` s15's set_actor hardcodes), an actor-OMITTED
insert by the subject role is REFUSED — s15's set_actor reads `kernel.principal_role`, which
resolves nothing on this kernel, so NEW.actor stays NULL and `actor NOT NULL` refuses the
write (or the qualified read errors outright). This is the exact class s19 forecloses; the
GREEN half (post-s19 the same write succeeds) is proven by kernel/fixtures/s19_search_path_fixture.py.

Scratch-only (schemas s19red*, dropped after). Run from anywhere. Lazy imports banned.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402 (filing/pghost_resolve.py via seen-red/_fixture_env.py -- never a literal host default)


PGHOST, DB = fixture_pghost(), "harness"
SCHEMA, KERN, ROLE = "s19red", "s19red_kernel", "s19red_rw"
LINEAGE = Path(__file__).resolve().parents[2] / "kernel" / "lineage"


def sh(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True)


def teardown() -> None:
    sh(["psql", "-h", PGHOST, "-d", DB, "-c",
        f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE; DROP SCHEMA IF EXISTS {KERN} CASCADE; "  # declared-drop: s19red (declared scratch/test reset)
        f"DROP OWNED BY {ROLE}; DROP ROLE IF EXISTS {ROLE};"])


def main() -> int:
    teardown()
    ddl = sh(["psql", "-h", PGHOST, "-d", DB, "-v", "ON_ERROR_STOP=1",
              "-v", f"schema={SCHEMA}", "-v", f"kern={KERN}", "-v", f"role={ROLE}",
              "-f", str(LINEAGE / "s15-schema.sql")])
    if ddl.returncode != 0:
        print(f"setup failed: {ddl.stderr[-300:]}")
        return 1
    # actor-OMITTED insert as the subject role on a non-default-schema kernel (NO s19 applied)
    ins = sh(["psql", "-h", PGHOST, "-d", DB, "-tA", "-v", "ON_ERROR_STOP=1", "-c",
              f"SET ROLE {ROLE}; SET search_path = {SCHEMA}, {KERN}; "
              f"INSERT INTO {SCHEMA}.ledger (kind, statement) VALUES ('decision', 'actor-omitted (pre-s19)');"])
    refused = ins.returncode != 0
    print("# s19 SEEN-RED — pre-fix set_actor on a NON-default-schema kernel:")
    print((ins.stdout + ins.stderr).strip())
    if refused:
        print("# RED CONFIRMED — the actor-omitted write was REFUSED (findings 16/37/45 reproduced); "
              "s19 forecloses this. GREEN half: kernel/fixtures/s19_search_path_fixture.py.")
    else:
        print("# !! NOT RED — the write unexpectedly succeeded; the specimen did not reproduce the defect.")
    teardown()
    return 0 if refused else 1


if __name__ == "__main__":
    raise SystemExit(main())
