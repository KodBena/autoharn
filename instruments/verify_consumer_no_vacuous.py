#!/usr/bin/env python3
"""verify_consumer_no_vacuous — the standing fixture for the acts-consumers' no-silent-vacuous-pass
guard (forecloses finding 4: the acts.act<->s15 MATCHING was unbuilt, yet the consumers reported GREEN
— certifying an arithmetic no-op as if the differential had run; a vacuous pass on an empty substrate).
The fix (a) landed the real deriver and (b) split readiness-vs-close so an EMPTY stream at CLOSE is
REQUIRED-ABSENT (RED), never a deferred/silent green. This pins the contract without needing a live
stream: with no stream present, mode='close' must be REQUIRED-ABSENT and mode='readiness' DEFERRED —
neither is OK. Registered close/lint line id: `consumer-no-vacuous-pass`. Lazy imports banned.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import close_manifest as cm  # noqa: E402

TARGET = next(iter(cm.ACTS_CONSUMER_TARGETS))   # a real consumer target


def check() -> list[str]:
    bad: list[str] = []
    orig = cm._acts_stream_present
    cm._acts_stream_present = lambda run_id: False    # force the EMPTY-stream substrate
    try:
        close = cm.run_acts_consumers(TARGET, "close")
        ready = cm.run_acts_consumers(TARGET, "readiness")
    finally:
        cm._acts_stream_present = orig
    if not all(st == "REQUIRED-ABSENT" for _, st, _ in close):
        bad.append(f"CLOSE on an empty stream did not go REQUIRED-ABSENT (got {[s for _, s, _ in close]}) "
                   f"— a vacuous green would re-launder finding 4")
    if not all(st == "DEFERRED" for _, st, _ in ready):
        bad.append(f"READINESS on an empty stream did not DEFER (got {[s for _, s, _ in ready]})")
    if any(st == "OK" for _, st, _ in close + ready):
        bad.append("a consumer reported OK on an empty stream — the exact silent-vacuous-pass")
    return bad


def main() -> int:
    bad = check()
    for b in bad:
        print(f"CONSUMER VACUOUS-PASS: {b}")
    if bad:
        print(f"# consumer-no-vacuous-pass FAIL — {len(bad)} defect(s): consumers greened an empty "
              f"substrate.")
        return 1
    print("# consumer-no-vacuous-pass PASS — empty stream: CLOSE is REQUIRED-ABSENT (RED), READINESS "
          "DEFERS; no consumer greens a no-op.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
