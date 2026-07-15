#!/usr/bin/env python3
"""readiness_vs_close_fixture — the both-directions fixture for the oracle §9 close-line gating split.

Applies (does not re-decide) the maintainer's ratified ruling (oracle §9, 2026-07-07; finding 11):
close-line gating follows the run's oracle — for e15 the acts stream is REQUIRED, and its ABSENCE at
close is RED, while pre-run READINESS legitimately DEFERS on the empty substrate. The substrate is
byte-identical in both modes (an empty acts stream); the mode is the caller's DECLARED claim about
whether a run has occurred and cannot be inferred from the substrate. This fixture nails both
directions of that split so no future edit can silently collapse close-mode back into a deferred pass
(the F49 vacuous-pass class).

Hermetic: it monkeypatches the stream-presence probe and the deriver subprocess, so it does not touch
the harness DB — the ONLY thing under test is close_manifest's mode branch, exercised on both an empty
and a present stream. (The present-stream deriver itself is proven green/red by the Increment-5
rehearsal; here it is a stub, only to prove the mode does not change the present-stream path.)

PRE-REGISTERED expectation matrix (hand-stated before reading the run; the ruling, not a new semantics):

    stream    mode        -> status           gating?   direction
    --------  ----------     ----------------  -------   ---------
    empty     readiness   -> DEFERRED          no        SEEN GREEN  (pre-run; no run yet)
    empty     close       -> REQUIRED-ABSENT   YES-RED   SEEN RED    (a close with no acts is red)
    present   readiness   -> OK (deriver ran)  no        mode-invariant when a stream exists
    present   close       -> OK (deriver ran)  no        mode-invariant when a stream exists

Exit 0 iff every cell matches; non-zero (loud) otherwise.
"""
from __future__ import annotations

import os
import subprocess
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
INSTRUMENTS = os.path.abspath(os.path.join(HERE, "..", "..", "instruments"))
sys.path.insert(0, INSTRUMENTS)

import close_manifest as cm  # noqa: E402 — path set above; this is the module under test

TARGET = "e15"  # the standing consumer-bearing target (in cm.ACTS_CONSUMER_TARGETS)

# The pre-registered matrix: (stream_present, mode) -> (expected_status, expected_gating_red).
EXPECT = {
    (False, "readiness"): ("DEFERRED", False),
    (False, "close"): ("REQUIRED-ABSENT", True),
    (True, "readiness"): ("OK", False),
    (True, "close"): ("OK", False),
}


def _fake_present(present: bool):
    return lambda run_id: present


def _fake_deriver_ok(argv, **kw):
    """Stand in for the acts_join deriver: report every consumer OK (RAN clean), exit 0. Only reached
    on the present-stream cases; proves the mode does not perturb the present-stream path."""
    out = "\n".join(f"acts:{c} OK 0 atoms (fixture stub)" for c in cm.ACTS_CONSUMERS) + "\n"
    return types.SimpleNamespace(returncode=0, stdout=out, stderr="")


def run_case(present: bool, mode: str) -> tuple[str, bool]:
    """Return (status, gating_red) for the three consumers under one (stream, mode) cell. All three
    consumers share a cell's fate, so the first is representative; we also assert they agree."""
    orig_present = cm._acts_stream_present
    orig_run = subprocess.run
    cm._acts_stream_present = _fake_present(present)
    if present:
        # patch the module's subprocess handle so the deriver call is the stub (os.path.exists(ACTS_JOIN)
        # is real; if the deriver file is absent the honest status is QUARANTINED, which would FAIL the
        # fixture loudly rather than silently — the correct direction).
        cm.subprocess.run = _fake_deriver_ok
    try:
        rows = cm.run_acts_consumers(TARGET, mode)
    finally:
        cm._acts_stream_present = orig_present
        cm.subprocess.run = orig_run
    statuses = {st for _, st, _ in rows}
    assert len(statuses) == 1, f"consumers disagreed within a cell: {statuses}"
    status = statuses.pop()
    gating_red = status in ("QUARANTINED", "REQUIRED-ABSENT")
    return status, gating_red


def main() -> int:
    print("# readiness-vs-close fixture — oracle §9 close-line gating split (both directions)")
    print(f"# target={TARGET}  consumers={cm.ACTS_CONSUMERS}\n")
    ok = True
    for (present, mode), (exp_status, exp_gating) in EXPECT.items():
        status, gating = run_case(present, mode)
        hit = status == exp_status and gating == exp_gating
        ok &= hit
        stream = "present" if present else "empty  "
        arrow = "RED " if gating else "green"
        print(f"  [{'OK ' if hit else '!! '}] stream={stream} mode={mode:9} -> {status:16} "
              f"gating={arrow}   expect=({exp_status}, {exp_gating})")
    # The load-bearing assertion, stated plainly: the SAME empty substrate is green in readiness and RED
    # in close. If those two ever coincide, the split has collapsed (the vacuous-pass regression).
    empty_ready, _ = run_case(False, "readiness")
    empty_close, empty_close_gates = run_case(False, "close")
    split_holds = empty_ready == "DEFERRED" and empty_close == "REQUIRED-ABSENT" and empty_close_gates
    ok &= split_holds
    print(f"\n  [{'OK ' if split_holds else '!! '}] SPLIT HOLDS: empty substrate is DEFERRED(green) in "
          f"readiness AND REQUIRED-ABSENT(red) in close — the mode, not the substrate, decides.")
    print(f"\n# FIXTURE {'GREEN — the readiness-vs-close split is proven both directions' if ok else 'RED — a cell diverged from the pre-registered matrix'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
