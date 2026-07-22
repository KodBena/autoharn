#!/usr/bin/env python3
"""hash_coverage_gate -- the s42 standing mechanical net: compute_row_hash's serialized-column
set equals the ledger's live column set, minus row_hash, forever
(design/FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md §3.2, RATIFIED R1/R2 ledger row 1460;
kernel/lineage/s42-row-hash-full-coverage.sql).

THE CLASS IT CLOSES: *a tamper-evidence serialization whose column enumeration is open at every
subsequent delta, silently* (spec §1.2). Thirteen deltas (s28..s41) each added ledger columns
and each -- correctly, under the not-class-ratifiable rule -- left compute_row_hash alone, so
twenty-two columns (including all twelve principal-identity columns) sat outside the hash chain
with no mechanism ever forcing the question (witnessed hazard, ledger row 1449). Per ADR-0011's
2026-07-02 amendment the mechanism ships WITH the first fix: this gate lands in the same commit
as s42, and from that commit on, a delta that adds a ledger column without re-issuing
compute_row_hash in the same delta turns this gate red in the offending commit -- the net
quantifies over the CLASS (any future column, any delta), never today's instance (ADR-0011
Rule 4).

MECHANISM (both sides mechanically derived -- never a hand-maintained manifest, which would be
the ADR-0012 P1 two-writers cancer this gate exists to prevent):
  side (i)  the ledger's live column set, from information_schema.columns on a scratch apply of
            the FULL current birth chain (high_watermark_1.sql + every primary s20+ delta,
            derived from kernel/lineage/*.sql filenames mechanically -- a future sNN cannot
            outrun this gate by being forgotten in a hardcoded list; .detect/.verify/
            .accommodate siblings carry >=2 dots and are excluded, the
            gates/idris_model_freshness.py head-derivation precedent), minus `row_hash` (the
            one deliberate exclusion: the hash cannot include itself -- spec §5 names it).
  side (ii) the columns compute_row_hash actually serializes, from the FUNCTION'S OWN SOURCE
            via pg_get_functiondef, regex over `r.<name>` field references -- the one home of
            the serialization, read live, never a transcription of it.
Set inequality in EITHER direction is red, naming every missing/extra column with the per-delta
teach-text. SURFACE CHOICE (the ledger_reader_allowlist precedent, same words): a gates/ member
ON A SCRATCH APPLY -- the .detect sibling fingerprints one delta's presence, it cannot quantify
over the column universe; the live catalog is the only honest enumerator of what fifteen-plus
layered CREATE OR REPLACE deltas actually produced. Cost: one scratch apply (~seconds); this is
a DB-dependent gate and says so (run at delta-authoring/acceptance time and by the s42 seen-red
fixture, not wired into a per-commit file hook).

NEGATIVE CONTROL (a gate never seen red is a claim -- ADR-0011's 2026-07-02 Rule 3 amendment):
  --inject-column NAME   after the real chain applies, ALSO `ALTER TABLE ledger ADD COLUMN NAME
                         text` (no serializer re-issue) before asserting -- the exact defect
                         shape of the s28..s41 silence, synthesized. The gate MUST go red naming
                         that column. Banked: seen-red/s42-row-hash-full-coverage/, registered
                         in gates/fixture_census.py.

HONEST LIMITS: the regex reads `r\\.(\\w+)` from the function source, so a serialized column is
"covered" iff the source REFERENCES it -- a pathological body that references a column inside a
dead branch would read as covered (no such branch exists; the body is a single ARRAY literal,
and a reviewer reads the delta). The gate binds this repository's delta discipline; it is not a
kernel-side refusal (spec §3.2's own scope).

Usage:
    python3 gates/hash_coverage_gate.py [--keep-scratch] [--inject-column NAME]
Exit 0 clean; 1 violations (listed, taught); 2 usage/psql error. Run from repo root.
Lazy imports banned (CLAUDE.md, 2026-07-02).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LINEAGE = REPO / "kernel" / "lineage"
sys.path.insert(0, str(REPO / "filing"))
from pghost_resolve import resolve_pghost  # noqa: E402  (the ONE host home -- never a literal default)

PGHOST, PGDB = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"
SCHEMA, KERN, ROLE = "hcov_scratch", "hcov_scratch_kernel", "hcov_scratch_rw"

# `r.<field>` references in compute_row_hash's own source. \w+ stops at `::` casts and `)`,
# so `r.stamp_ts::text` yields `stamp_ts` and `array_to_string(r.enacts, ',')` yields `enacts`.
FIELD_REF = re.compile(r"\br\.(\w+)")

TEACH = (
    "REFUSED -- compute_row_hash's serialized-column set disagrees with the ledger's live\n"
    "column set (s42 law, design/FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md §3.2):\n"
    "a delta that adds a ledger column RE-ISSUES compute_row_hash in the same delta, covering\n"
    "every column except row_hash itself. A column outside the serialization is outside the\n"
    "tamper-evidence chain -- a schema-owner rewrite of it changes no hash (the ledger-row-1449\n"
    "hazard class this gate closes). Fix: re-issue compute_row_hash in the SAME delta that\n"
    "changes the column set, then re-run this gate."
)


def chain_files() -> list[str]:
    """The full current birth chain, mechanically derived (idris_model_freshness's
    head-derivation precedent): high_watermark_1.sql (which \\ir-chains s15..s19 in its own
    frozen order, s18 deliberately excluded per its header) followed by every PRIMARY sNN delta
    with NN >= 20, numerically sorted. A primary delta file has exactly one dot (`.sql`);
    .detect/.verify/.accommodate siblings carry >=2 and are companion probes, not deltas."""
    primaries: list[tuple[int, str]] = []
    for p in sorted(LINEAGE.glob("s*.sql")):
        if p.name.count(".") != 1:
            continue
        m = re.match(r"^s(\d+)-", p.name)
        if m and int(m.group(1)) >= 20:
            primaries.append((int(m.group(1)), p.name))
    primaries.sort()
    return ["high_watermark_1.sql"] + [name for _, name in primaries]


def psql(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", *args],
                        capture_output=True, text=True)
    if check and cp.returncode != 0:
        raise RuntimeError(f"psql failed: {cp.stdout[-800:]} {cp.stderr[-800:]}")
    return cp


def teardown() -> None:
    subprocess.run(["psql", "-h", PGHOST, "-d", PGDB, "-c",
                    f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE; DROP SCHEMA IF EXISTS {KERN} CASCADE; "  # declared-drop: hcov scratch reset
                    f"DROP OWNED BY {ROLE}; DROP ROLE IF EXISTS {ROLE};"],
                   capture_output=True, text=True)


def scratch_apply() -> None:
    args: list[str] = ["-v", f"schema={SCHEMA}", "-v", f"kern={KERN}", "-v", f"role={ROLE}"]
    for f in chain_files():
        args += ["-f", str(LINEAGE / f)]
    psql(*args)


def ledger_columns() -> set[str]:
    out = psql("-tA", "-c",
               f"SELECT column_name FROM information_schema.columns "
               f"WHERE table_schema = '{SCHEMA}' AND table_name = 'ledger';").stdout
    return {ln.strip() for ln in out.splitlines() if ln.strip()}


def serialized_columns() -> set[str]:
    out = psql("-tA", "-c",
               f"SELECT pg_get_functiondef(p.oid) FROM pg_proc p "
               f"JOIN pg_namespace n ON n.oid = p.pronamespace "
               f"WHERE n.nspname = '{SCHEMA}' AND p.proname = 'compute_row_hash' "
               f"AND p.prokind = 'f';").stdout
    if not out.strip():
        raise RuntimeError(f"compute_row_hash not found in scratch schema {SCHEMA} -- "
                           f"the chain apply did not produce the serializer at all")
    return set(FIELD_REF.findall(out))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-scratch", action="store_true",
                    help="leave the scratch schema/kernel/role standing (debug only)")
    ap.add_argument("--inject-column", default=None,
                    help="seen-red negative control: after the real chain applies, add this "
                         "column to ledger (no serializer re-issue) -- the gate must go red")
    a = ap.parse_args(argv)

    teardown()   # pre-clean: never trust residue from a prior interrupted run
    try:
        scratch_apply()
        if a.inject_column:
            psql("-c", f"ALTER TABLE {SCHEMA}.ledger ADD COLUMN {a.inject_column} text;")
        table_side = ledger_columns() - {"row_hash"}
        fn_side = serialized_columns()
    except RuntimeError as exc:
        print(f"hash-coverage-gate: SCRATCH ERROR -- {exc}")
        return 2
    finally:
        if not a.keep_scratch:
            teardown()
        else:
            print(f"hash-coverage-gate: --keep-scratch -- schema={SCHEMA} kern={KERN} "
                  f"role={ROLE} left standing, teardown it yourself when done")

    missing = sorted(table_side - fn_side)   # in the table, NOT serialized: outside the chain
    extra = sorted(fn_side - table_side)     # serialized, NOT in the table: a stale reference

    if missing or extra:
        print(f"hash-coverage-gate: RED\n\n{TEACH}\n")
        for c in missing:
            print(f"  !! MISSING from the serialization: ledger column {c!r} is OUTSIDE the "
                  f"hash chain -- a schema-owner tamper of it changes no hash")
        for c in extra:
            print(f"  !! STALE in the serialization: compute_row_hash references {c!r} which "
                  f"is not a ledger column -- the function would error at first INSERT")
        return 1
    print(f"hash-coverage-gate: clean -- compute_row_hash serializes all "
          f"{len(table_side)} ledger columns (everything except row_hash, the one named "
          f"exclusion); chain head {chain_files()[-1]}. A future column-adding delta must "
          f"re-issue the serializer in the same delta or this gate goes red.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
