#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T09:31:45Z
#   last-change: 2026-07-14T09:31:45Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""scan2_firing_schema — mechanizes the shape claim of tools/experiments/scan2_firings.py
(ledger row 337, "detector-firing-telemetry"): a firing/disposition record is a CHECKED
property, not just an asserted convention (ADR-0012 cancer G — load-bearing knowledge left in
unenforceable prose). Every line of tools/experiments/results/scan2-firings.jsonl, if the file
exists, is parsed as JSON and validated against `scan2_firings.validate_record` — imported,
never re-derived (ADR-0012 P1/P7: one schema, one owner; this gate is not a second hand-written
copy of the rules that could drift from the module that actually writes the file).

Two additional cross-line checks beyond the per-record schema: (a) no two `firing` records
share the same `run_id`+`finding_key` (the recorder writes each surfaced finding once per run
by construction; a duplicate is evidence of a doubled write), (b) a `disposition` record's
`run_id`, when non-null, names a `run_id` that appears on at least one `firing` record with a
matching `finding_key` (a disposition scoped to a run that never fired that finding is a typo,
not a triage).

An empty or absent jsonl is CLEAN (nothing shipped yet is not a violation).

Exit 0 clean, exit 1 listing every violation as `<path>:<line>: <message>`. Lazy imports
banned (CLAUDE.md, 2026-07-02): everything below imports at module load.

Run (from the repo root): python3 gates/scan2_firing_schema.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools" / "experiments"))
from scan2_firings import FIRINGS_PATH, validate_record  # noqa: E402


def check(path: Path) -> list:
    if not path.exists():
        return []
    violations = []
    firing_runs_findings = set()  # (run_id, finding_key) seen on a firing record
    firing_run_ids = set()
    disposition_lines = []  # (lineno, rec) deferred until firing_run_ids is fully known
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            rec = json.loads(raw)
        except json.JSONDecodeError as e:
            violations.append(f"{path}:{lineno}: not valid JSON ({e})")
            continue
        for err in validate_record(rec):
            violations.append(f"{path}:{lineno}: {err}")
        if rec.get("kind") == "firing":
            key = (rec.get("run_id"), rec.get("finding_key"))
            if key in firing_runs_findings:
                violations.append(f"{path}:{lineno}: duplicate firing for run_id="
                                  f"{rec.get('run_id')!r} finding_key={rec.get('finding_key')!r}")
            firing_runs_findings.add(key)
            if rec.get("run_id"):
                firing_run_ids.add(rec["run_id"])
        elif rec.get("kind") == "disposition":
            disposition_lines.append((lineno, rec))
    for lineno, rec in disposition_lines:
        run_id = rec.get("run_id")
        if run_id is not None and run_id not in firing_run_ids:
            violations.append(f"{path}:{lineno}: disposition names run_id={run_id!r}, which no "
                              "firing record in this file carries")
    return violations


def main() -> int:
    violations = check(FIRINGS_PATH)
    if violations:
        for v in violations:
            print(v)
        print(f"# scan2-firing-schema FAIL — {len(violations)} violation(s) in {FIRINGS_PATH}")
        return 1
    print(f"scan2-firing-schema: clean ({FIRINGS_PATH} — every record well-formed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
