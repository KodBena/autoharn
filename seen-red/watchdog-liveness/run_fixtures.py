#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T10:54:11Z
#   last-change: 2026-07-18T10:54:11Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for tools/watchdog_liveness.py (tracker items
`watchdog-liveness-harness` + `watchdog-mode-field-inert`; design/ORCH-WATCHDOG-LIVENESS.md
Section 6).

No database, no real Claude Code session: this checker's whole surface (short of the
best-effort ledger check, which degrades to SKIPPED with no deployment.json present, exactly as
exercised here) is synthetic JSONL journals under `fixtures/<name>/.claude/logs/`, checked in
beside this file. Two fixture roots, each covering BOTH the Class 1 (Bash) and Class 3 (subagent)
detectors together:

  quiet  -- a Bash dispatch 1.5s old against the default bash-class threshold (0.1s x10 +1s =
            2.0s), and a subagent dispatch 5.0s old against the subagent-class threshold
            (60.0s x3.0 +30.0s = 210.0s) -- both inside slack: exit 0, no `LIVENESS QUESTION`
            anywhere in stdout.
  stale  -- a Bash dispatch 596s old against the same 2.0s threshold, and a subagent dispatch
            600.0s old against the same 210.0s threshold -- both past slack: exit 1, at least one
            `LIVENESS QUESTION` line per surface naming the elapsed-vs-expected delta. The stale
            subagent fixture also carries a PAIRED dispatch+return (same `tool_use_id`, so it must
            be reported quiet regardless of age) and a dispatch with NO `tool_use_id` at all (so
            it must be skipped from detection entirely, per the checker's own honest-limit
            docstring) -- both are negative-space assertions: neither may appear in a
            `LIVENESS QUESTION` line.

The subagent fixtures also stand as the regression proof for two hazards found and fixed while
building this coverage (CLAUDE.md engineering-responsibility clause):
  1. `subagent_dispatch_status()` used to pair on a `dispatch_ts` field
     `hooks/pretooluse_delegation_observer.py` no longer writes (that hook's own correlation field
     is `tool_use_id`) -- the old pairing logic would have silently never matched a single
     dispatch/return pair, misreporting every completed subagent call as perpetually open.
  2. `load_watchdog_config()` used to fall back to the GENERIC global slack defaults
     (10.0x/+1.0s) for every built-in class when no apparatus.json override was present, making
     the `subagent` class's own distinct byte-held defaults (3.0x/+30.0s) dead code. The
     210.0s threshold asserted below (`60.0*3.0+30.0`, not `60.0*10.0+1.0=601.0s`) is the
     regression proof for this fix.

Usage: python3 seen-red/watchdog-liveness/run_fixtures.py
Exit 0 if both cases match; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CHECKER = REPO / "tools" / "watchdog_liveness.py"


def run(fixture: str, now: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(HERE / "fixtures" / fixture), "--now", now],
        capture_output=True, text=True, timeout=30,
    )


def main() -> int:
    ok = True
    report: list[str] = []

    r = run("quiet", "2026-07-13T12:00:10Z")
    quiet_pass = (
        r.returncode == 0
        and "LIVENESS QUESTION" not in r.stdout
        and "sess-qui" in r.stdout  # the open-but-fresh subagent dispatch is reported, not hidden
    )
    report.append(f"=== quiet ===\n  [{'ok' if quiet_pass else 'FAIL'}] exit={r.returncode} "
                  f"has_question={'LIVENESS QUESTION' in r.stdout} "
                  f"subagent_reported={'sess-qui' in r.stdout}\n{r.stdout}")
    ok &= quiet_pass

    r = run("stale", "2026-07-13T12:10:00Z")
    stale_pass = (
        r.returncode == 1
        and "LIVENESS QUESTION" in r.stdout
        and "596.0s" in r.stdout  # bash class, class-owned 2.0s threshold (0.1s x10 +1.0s)
        and "600.0s" in r.stdout  # subagent class breach
        and "x3.0 +30.0s" in r.stdout  # regression proof: subagent's OWN slack, not the generic 10.0x/+1.0s
        and "tu-stale-paired" not in r.stdout  # paired dispatch/return must never surface as a finding
    )
    report.append(f"=== stale ===\n  [{'ok' if stale_pass else 'FAIL'}] exit={r.returncode} "
                  f"has_question={'LIVENESS QUESTION' in r.stdout} "
                  f"has_596s_bash_delta={'596.0s' in r.stdout} "
                  f"has_600s_subagent_delta={'600.0s' in r.stdout} "
                  f"has_subagent_own_slack={'x3.0 +30.0s' in r.stdout} "
                  f"paired_dispatch_absent={'tu-stale-paired' not in r.stdout}\n{r.stdout}")
    ok &= stale_pass

    print("\n".join(report))
    if ok:
        print("ALL CASES OK -- watchdog-liveness both-polarity proof clean (quiet fixture stays "
              "silent within slack on both the Bash and subagent surfaces, stale fixture raises a "
              "liveness question per surface naming the elapsed-vs-expected delta -- never a bare "
              "STALE/HUNG/DEAD verdict -- and the paired/unpairable subagent dispatches are "
              "correctly excluded from the finding).")
        return 0
    print("FAILURE -- see [FAIL] case(s) above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
