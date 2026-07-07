#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-07T01:47:28Z
#   last-change: 2026-07-07T01:47:28Z
#   contributors: 37017f46/main
# <<< PROVENANCE-STAMP <<<

"""append_only_integrity — the append-only-trigger guard (forecloses the finding-6/15 class: an
attestation/ledger table that lacks its append-only UPDATE+DELETE trigger, so rows can be silently
rewritten and the ledger's tamper-evidence quietly dies). ADR-0000 never-again for the "append-only
table shipped without its guard" class.

THE HAZARD. The audit spine — harness.finding / finding_disposition / class_foreclosure and
acts.ruling / act / stream — is trustworthy ONLY because each table refuses UPDATE and DELETE. That
refusal is a trigger. A trigger can be dropped by a migration, a schema rebuild, or a CASCADE, and
NOTHING today would notice: the ledger keeps accepting appends while silently permitting rewrites.
Findings 6 and 15 were exactly this shape (review_detail shipped with no append-only trigger). This
gate is the standing check that closes the class for the durable spine.

THE RULE. For every table in REQUIRED_APPEND_ONLY, an UPDATE+DELETE-guarding trigger must be present.
Missing one → exit 1, loud, naming the table. The acts.* rows are checked only when the acts schema is
present (it is experiment-created); their absence is not a failure, a present-but-unguarded table is.

Registered close/lint line id: `append-only-integrity`. Lazy imports banned.

  append_only_integrity.py [--host H] [--db D]      # exit 1 if any required guard is missing
"""
from __future__ import annotations

import argparse
import subprocess
import sys

# (schema, table): the guard is any trigger on the table firing for BOTH update and delete. We match on
# coverage, not on a trigger name, so a rename does not read as rot — only a real loss of the guard does.
REQUIRED_APPEND_ONLY = [
    ("harness", "finding"),
    ("harness", "finding_disposition"),
    ("harness", "class_foreclosure"),
    ("harness", "rationalization_finding"),
    ("harness", "rationalization_disposition"),
]
# checked only if the schema exists (acts is instantiated per experiment, not always present)
OPTIONAL_APPEND_ONLY = [
    ("acts", "act"),
    ("acts", "ruling"),
    ("acts", "stream"),
]


def _guard_coverage(host: str, db: str, schema: str, table: str) -> tuple[bool, bool, bool]:
    """(table_exists, guards_update, guards_delete) for the append-only triggers on schema.table."""
    sql = (
        "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
        f"WHERE table_schema='{schema}' AND table_name='{table}'), "
        "COALESCE(bool_or(event_manipulation='UPDATE'),false), "
        "COALESCE(bool_or(event_manipulation='DELETE'),false) "
        "FROM information_schema.triggers "
        f"WHERE event_object_schema='{schema}' AND event_object_table='{table}';"
    )
    cp = subprocess.run(["psql", "-h", host, "-d", db, "-tA", "-F", "|", "-c", sql],
                        capture_output=True, text=True, timeout=30)
    if cp.returncode != 0:
        raise RuntimeError(f"{schema}.{table}: {cp.stderr.strip()[-160:]}")
    exists, upd, dele = (cp.stdout.strip().split("|") + ["f", "f", "f"])[:3]
    return exists == "t", upd == "t", dele == "t"


def missing_guards(host: str, db: str, required, optional) -> list[str]:
    """Names of tables whose append-only guard is missing. A REQUIRED table absent, or present without
    both an UPDATE and a DELETE guard, is a violation; an OPTIONAL (acts.*) table is only a violation
    when it exists but is unguarded."""
    bad: list[str] = []
    for schema, table in required:
        exists, upd, dele = _guard_coverage(host, db, schema, table)
        if not exists:
            bad.append(f"{schema}.{table}: REQUIRED append-only table is ABSENT")
        elif not (upd and dele):
            bad.append(f"{schema}.{table}: append-only guard missing (update={upd} delete={dele})")
    for schema, table in optional:
        exists, upd, dele = _guard_coverage(host, db, schema, table)
        if exists and not (upd and dele):
            bad.append(f"{schema}.{table}: present but UNGUARDED (update={upd} delete={dele})")
    return bad


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="192.168.122.1")
    ap.add_argument("--db", default="harness")
    a = ap.parse_args(argv)
    try:
        bad = missing_guards(a.host, a.db, REQUIRED_APPEND_ONLY, OPTIONAL_APPEND_ONLY)
    except RuntimeError as e:
        print(f"# append-only-integrity ERROR — {e}")
        return 2
    if bad:
        for b in bad:
            print(f"UNGUARDED APPEND-ONLY TABLE: {b}")
        print(f"# append-only-integrity FAIL — {len(bad)} audit-spine table(s) lack their append-only "
              f"guard. The ledger's tamper-evidence is not intact.")
        return 1
    print(f"# append-only-integrity PASS — all {len(REQUIRED_APPEND_ONLY)} required audit-spine tables "
          f"(+ present acts.*) refuse UPDATE and DELETE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
