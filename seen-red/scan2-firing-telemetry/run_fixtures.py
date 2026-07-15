#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T09:32:19Z
#   last-change: 2026-07-14T09:32:45Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""Both-polarity proof for the detector-firing-telemetry build (ledger row 337): the recorder
(tools/experiments/scan2_firings.py) and the schema gate (gates/scan2_firing_schema.py).

Four cases, all against a throwaway jsonl under /tmp (never the real
tools/experiments/results/scan2-firings.jsonl -- an intentionally-malformed fixture line
committed to the real file would itself trip the gate's real run):

  RED 1  -- a firing record missing `git_hash` is flagged by `gates.scan2_firing_schema.check`.
  RED 2  -- a disposition record with `disposition="MAYBE"` (not in TP/FP/house-term) is flagged.
  RED 3  -- FiringRecord construction itself REFUSES a malformed record (rank=0) at the type
             boundary (ADR-0012 P2 -- translate-and-validate, never coerce) -- proves the defect
             class is foreclosed at construction, not merely caught by the downstream gate.
  GREEN  -- a real end-to-end run: record_class1_run() over two synthetic ranked findings, a
             triage disposition appended, the gate's own check() over the result is clean.

Usage: python3 seen-red/scan2-firing-telemetry/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "tools" / "experiments"))
sys.path.insert(0, str(REPO / "gates"))
import scan2_firings as sf  # noqa: E402
import scan2_firing_schema as gate  # noqa: E402


def main() -> int:
    ok = True

    # RED 1 -- missing git_hash on an otherwise-plausible firing record
    bad1 = {"kind": "firing", "schema_version": sf.SCHEMA_VERSION, "detector": "compound_nominal_scan2",
            "defect_class": "class1", "run_id": "r1", "run_ts": "2026-07-14T00:00:00Z",
            "git_dirty": False, "finding_key": "class1:x y", "rule": "A", "rank": 1, "score": 1.0,
            "sites": [], "disposition": None}
    errs1 = sf.validate_record(bad1)
    if any("git_hash" in e for e in errs1):
        print("RED 1  ok: firing record missing git_hash is flagged")
    else:
        print(f"RED 1  FAIL: expected a git_hash violation, got {errs1}")
        ok = False

    # RED 2 -- disposition with an out-of-enum verdict
    bad2 = {"kind": "disposition", "schema_version": sf.SCHEMA_VERSION, "detector": "compound_nominal_scan2",
            "finding_key": "class1:x y", "disposition": "MAYBE"}
    errs2 = sf.validate_record(bad2)
    if any("MAYBE" in e for e in errs2):
        print("RED 2  ok: disposition with an out-of-enum verdict is flagged")
    else:
        print(f"RED 2  FAIL: expected a disposition-enum violation, got {errs2}")
        ok = False

    # RED 3 -- construction-time refusal, not a downstream catch
    try:
        sf.FiringRecord(run_id="r", run_ts="t", git_hash="h", git_dirty=False,
                        defect_class="class1", mode="ABC", finding_key="class1:x y",
                        rule="A", rank=0, score=1.0)
        print("RED 3  FAIL: FiringRecord(rank=0) was NOT refused at construction")
        ok = False
    except sf.RecordError as e:
        print(f"RED 3  ok: FiringRecord refused a malformed record at construction ({e})")

    # GREEN -- a real end-to-end run against a throwaway jsonl
    tmp = Path(tempfile.mkdtemp(prefix="scan2-firings-seenred-"))
    scratch = tmp / "scan2-firings.jsonl"
    orig_path = sf.FIRINGS_PATH
    sf.FIRINGS_PATH = scratch
    gate.FIRINGS_PATH = scratch  # the gate reads the module attribute the recorder set
    try:
        ranked = [
            {"pair": "seenred story", "count": 3, "docs": 2, "score": 42.0,
             "angles": {"A": 3.0}, "sites": ["fixture/doc.md:1"]},
            {"pair": "seenred posture", "count": 1, "docs": 1, "score": 10.0,
             "angles": {"B": 2.0}, "sites": []},
        ]
        n = sf.record_class1_run(ranked, "ABC")
        if n != 2:
            print(f"GREEN FAIL: expected 2 records written, got {n}")
            ok = False
        lines = scratch.read_text(encoding="utf-8").splitlines()
        if len(lines) != 2:
            print(f"GREEN FAIL: expected 2 jsonl lines on disk, found {len(lines)}")
            ok = False
        first = json.loads(lines[0])
        if first["disposition"] is not None:
            print(f"GREEN FAIL: a fresh firing record must carry disposition=null, "
                  f"got {first['disposition']!r}")
            ok = False
        run_id = first["run_id"]
        # append the disposition directly (cmd_triage is argparse-shaped; exercise the record
        # type it builds instead of re-parsing argv here)
        sf.append_records([sf.DispositionRecord(finding_key="class1:seenred story",
                                                disposition="TP", run_id=run_id,
                                                note="seen-red synthetic specimen")])
        violations = gate.check(scratch)
        if violations:
            print(f"GREEN FAIL: gate found violations over a real recorder run: {violations}")
            ok = False
        else:
            print("GREEN ok: record_class1_run + triage disposition + schema gate, end-to-end clean")
    finally:
        sf.FIRINGS_PATH = orig_path
        gate.FIRINGS_PATH = orig_path
        shutil.rmtree(tmp, ignore_errors=True)

    if not ok:
        print("SPECIMEN FAIL -- see above")
        return 1
    print("ALL CASES OK -- scan2-firing-telemetry construction-refusal, schema-gate, and "
          "end-to-end recorder run, zero residue")
    return 0


if __name__ == "__main__":
    sys.exit(main())
