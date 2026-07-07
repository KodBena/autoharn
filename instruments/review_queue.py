#!/usr/bin/env python3
"""review_queue — the materialized review queue (consult 11 §4.5, the fourth enforcement shape).

Flag-and-journal is only an ENFORCEMENT shape if something CONSUMES the flags — otherwise it is a
shrug. This instrument is that consumer: it aggregates, as first-class audit records, every
anomaly the de-priced gate and the derived-validity semantics surface for a run:

  (1) ticket_flags telemetry from the gate journal — counts per class and the per-act records
      (enactment_no_enacts / enacts_nondesign_target / enacts_stale_antecedent /
      window_redundant_entry). Guest-side, invisible to the subject → no incentive gradient → the
      labels stay measurements (the same argument that kept the gate off `concern`, now applied to
      its own §4.4 rule).
  (2) unsound derivations + launder proof (soundness.py) — gate-derivable, sound-invalid edges,
      and what auto-resolve-to-head would falsely rewrite them to.
  (3) alias surface (soundness.py) — enacts targets that are not decisions (reference-domain
      hygiene; each is a REVIEW item, not an auto-fix — a deny/auto-resolve would adjudicate
      blindly and, per §4.2, wrongly).
  (4) stale-enactment debt (stale_enactment_debt.py) — files carrying work under a later-retired
      antecedent.

This is the deployment anomaly log the safety register mandates (every anomaly logged with a
disposition). Read-only; consumes the gate journal and {session}.ledger.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

import soundness
import stale_enactment_debt as sed

DEPLOYED_JOURNAL = os.path.expanduser(
    "~/w/vdc/1/epistemic-audit/logs/change_gate.journal.jsonl")


def _flag_records(journal_path: str) -> list[dict]:
    out = []
    try:
        for line in open(journal_path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("outcome") == "allowed" and r.get("ticket_flags"):
                out.append(r)
    except FileNotFoundError:
        pass
    return out


def report(session: str, journal_path: str = DEPLOYED_JOURNAL) -> None:
    print(f"# REVIEW QUEUE — {session}.ledger × {os.path.basename(journal_path)}")
    print(f"# (standing derived audit artifact; every item is a review record, not an auto-fix)\n")

    print("== 1. ticket_flags telemetry (from the gate journal) ==")
    recs = _flag_records(journal_path)
    counts: Counter = Counter()
    for r in recs:
        counts.update(r.get("ticket_flags") or [])
    if not counts:
        print("  (no flagged tickets — every unlock was a resolving, in-force, non-redundant edge)")
    else:
        for cls, n in sorted(counts.items()):
            print(f"  {cls}: {n}")
        for r in recs:
            print(f"    entry #{r.get('unlocked_by_entry')} -> {r.get('file')}: "
                  f"{sorted(r.get('ticket_flags') or [])}")

    print("\n== 2/3. derived-validity anomalies (soundness §4.2) ==")
    soundness.report(session)

    print("\n== 4. stale-enactment debt (§5.4) ==")
    sed.report(session, journal_path)


if __name__ == "__main__":
    jp = DEPLOYED_JOURNAL
    args = sys.argv[1:]
    if args and args[0].startswith("--journal="):
        jp = os.path.expanduser(args[0].split("=", 1)[1]); args = args[1:]
    for s in (args or ["s11"]):
        report(s, jp)
