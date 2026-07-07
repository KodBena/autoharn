#!/usr/bin/env python3
"""verify_substrate_required — the standing fixture for the consumer-substrate-required guard (forecloses
finding 36: close_manifest.py hardcoded e15-pinned module-global defaults for the acts `--fenced` dir and
the row_performed_by `--session-dir`, so a bare `close_manifest.py e16 --mode close` measured e15's fence +
e15's transcript against e16's ledger and every acts/perf consumer returned a VACUOUS 0/all-unbound — a
silent wrong-substrate pass, F49 class; run B = close-e16-post-disposition.txt is the banked live specimen).

The fix: the two substrate pointers are TARGET-RESOLVED from the ledger_target SSOT (exactly like db/schema/
actor), and a consumer-bearing target with NO registered substrate (and no ACTS_FENCED / PERF_SESSION_DIR
override) renders its acts/perf lines REQUIRED-ABSENT (RED) at CLOSE / DEFERRED at readiness — never a
silent empty. This pins that contract WITHOUT a live substrate: with an unregistered consumer target,
mode='close' must be REQUIRED-ABSENT and mode='readiness' DEFERRED — neither is OK. Registered close/lint
line id: `consumer-substrate-required`. Lazy imports banned (top-of-file only)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import close_manifest as cm  # noqa: E402

# A consumer-bearing target with NO registered substrate: not in ledger_target._SPECIAL, so resolve()
# returns fenced_dir=None + subject_session_dir=None. We add it to the consumer-target set for the check.
FAKE_TARGET = "unregistered_substrate_demo"


def check() -> list[str]:
    """Read cm.run_acts_consumers / cm.run_perf_consumers at CALL time (so a specimen may monkeypatch the
    pre-fix defect in). Returns the list of contract violations (empty == pass)."""
    bad: list[str] = []
    orig_targets = cm.ACTS_CONSUMER_TARGETS
    cm.ACTS_CONSUMER_TARGETS = orig_targets | {FAKE_TARGET}
    # Ensure no env override masks the unregistered substrate (the override is the LOUD escape hatch; here
    # we are proving the NO-substrate path, so it must be absent).
    saved = {k: os.environ.pop(k, None) for k in ("ACTS_FENCED", "PERF_SESSION_DIR")}
    try:
        ac = cm.run_acts_consumers(FAKE_TARGET, "close")
        ar = cm.run_acts_consumers(FAKE_TARGET, "readiness")
        pc = cm.run_perf_consumers(FAKE_TARGET, "close")
        pr = cm.run_perf_consumers(FAKE_TARGET, "readiness")
    finally:
        cm.ACTS_CONSUMER_TARGETS = orig_targets
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v
    if not all(st == "REQUIRED-ABSENT" for _, st, _ in ac + pc):
        bad.append(f"CLOSE on an UNREGISTERED-substrate target did not go REQUIRED-ABSENT "
                   f"(acts={[s for _, s, _ in ac]} perf={[s for _, s, _ in pc]}) — a silent vacuous pass "
                   f"would re-launder finding 36 (an e15 default read against another run's ledger)")
    if not all(st == "DEFERRED" for _, st, _ in ar + pr):
        bad.append(f"READINESS on an UNREGISTERED-substrate target did not DEFER "
                   f"(acts={[s for _, s, _ in ar]} perf={[s for _, s, _ in pr]})")
    if any(st == "OK" for _, st, _ in ac + ar + pc + pr):
        bad.append("a consumer reported OK on an UNREGISTERED substrate — the exact finding-36 silent "
                   "wrong-substrate vacuous pass")
    return bad


def main() -> int:
    bad = check()
    for b in bad:
        print(f"SUBSTRATE VACUOUS-PASS: {b}")
    if bad:
        print(f"# consumer-substrate-required FAIL — {len(bad)} defect(s): a consumer measured an "
              f"unregistered substrate instead of refusing it.")
        return 1
    print("# consumer-substrate-required PASS — an unregistered consumer substrate is REQUIRED-ABSENT (RED) "
          "at CLOSE and DEFERRED at readiness; no consumer greens a wrong/absent substrate (finding 36).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
