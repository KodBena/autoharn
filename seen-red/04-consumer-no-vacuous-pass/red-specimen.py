#!/usr/bin/env python3
"""Seen-red specimen for the consumer-no-vacuous-pass gate (forecloses finding 4). Reproduces the
pre-fix consumer: on an empty acts stream it reported GREEN (OK), certifying an unbuilt matching as a
clean arithmetic no-op. The naive consumer below returns OK regardless of substrate; the gate's check
then sees a consumer greening an empty CLOSE and flags it. Banked as red.txt. Run from harness root."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path("/home/bork/w/vdc/1/epistemic-operator/instruments")))
import close_manifest as cm  # noqa: E402
from verify_consumer_no_vacuous import check  # noqa: E402  (reads cm.run_acts_consumers at CALL time)


def _naive_vacuous_consumers(target: str, mode: str):
    """The finding-4 defect: report OK without running (or requiring) the real differential."""
    return [(c, "OK", "0 rows differ (vacuous — no matching was actually built)") for c in cm.ACTS_CONSUMERS]


def main() -> int:
    orig_present = cm._acts_stream_present
    orig_run = cm.run_acts_consumers
    cm._acts_stream_present = lambda run_id: False
    cm.run_acts_consumers = _naive_vacuous_consumers
    try:
        bad = check()
    finally:
        cm._acts_stream_present = orig_present
        cm.run_acts_consumers = orig_run
    if not bad:
        print("SPECIMEN INERT — the vacuous consumer did not trip the guard (unexpected).")
        return 1
    for b in bad:
        print(f"CONSUMER VACUOUS-PASS: {b}")
    print(f"# consumer-no-vacuous-pass FAIL — {len(bad)} defect(s): consumers greened an empty substrate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
