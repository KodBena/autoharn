#!/usr/bin/env python3
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
            `LIVENESS QUESTION` line. The stale fixture's BASH journals ALSO carry the Class-1
            analogue: a Bash dispatch (`tu-stale-bash-paired-1`) with a matching, 599s-old
            completion in `bash_completions.jsonl`, joined on `tool_use_id` -- it must never
            surface as a finding either, and its absence is the WITNESSED regression proof for
            vestigial_documentation/design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md: under the pre-fix `token`/`pairing` join
            (fields `hooks/posttooluse_bash_completion.py` no longer writes at all), this exact
            dispatch would have read as perpetually open.

  mechanism-dead-fires / mechanism-dead-below-threshold -- both-polarity proof for M2 (RCA
            sec-5): a pairing mechanism that has fired zero times across >= 20 eligible
            (`tool_use_id`-carrying) Bash dispatches is reported as ONE typed mechanism-level
            finding, never N per-event `LIVENESS QUESTION`s. `mechanism-dead-fires` carries 22
            such dispatches and zero matching completions (three completions ARE present but
            carry unrelated `tool_use_id`s, proving the join is a real equality check, not mere
            completion-file presence) -- the tripwire must fire: exactly one mechanism-level
            finding, and none of the per-dispatch `bash dispatch <key>` lines the old path would
            have printed 22 times over. `mechanism-dead-below-threshold` carries only 3 such
            dispatches, also zero paired -- below the 20-eligible floor, so the tripwire must NOT
            fire, and the checker must fall through to ordinary per-dispatch reporting (3
            individual liveness questions) instead.

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
  3. `bash_dispatch_status()` used to join on `c.get("pairing") == "token"` and `c.get("token")`
     -- fields `bash_completions.jsonl` never carries (the hook journals only `{ts, session_id,
     tool_use_id, duration_ms?, command_sha256, command_head}`) -- so `paired_tokens` was always
     empty and every completed Bash dispatch read as perpetually open (the exact failure
     vestigial_documentation/design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md documents, ~2000 false liveness questions in a
     real run). Fixed to join on `tool_use_id`, per the stale fixture's new paired-bash case
     above; M2's mechanism-dead tripwire (module docstring hazard-shape above) ships with this
     same fix per ADR-0011's mechanism-ships-with-first-fix tightening.

Usage: python3 seen-red/watchdog-liveness/run_fixtures.py
Exit 0 if all cases match; 1 otherwise. Lazy imports banned.
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
        # Class-1 analogue (this pass's fix): a Bash dispatch with a matching, past-threshold-age
        # completion, joined on tool_use_id, must never surface as a finding either -- the
        # WITNESSED regression proof that a completed Bash dispatch now reads quiet instead of
        # perpetually open (vestigial_documentation/design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md). Neither its token-prefix
        # display key nor its tool_use_id may appear anywhere in stdout.
        and "c3d4e5f6" not in r.stdout
        and "tu-stale-bash-paired-1" not in r.stdout
    )
    report.append(f"=== stale ===\n  [{'ok' if stale_pass else 'FAIL'}] exit={r.returncode} "
                  f"has_question={'LIVENESS QUESTION' in r.stdout} "
                  f"has_596s_bash_delta={'596.0s' in r.stdout} "
                  f"has_600s_subagent_delta={'600.0s' in r.stdout} "
                  f"has_subagent_own_slack={'x3.0 +30.0s' in r.stdout} "
                  f"paired_dispatch_absent={'tu-stale-paired' not in r.stdout} "
                  f"paired_bash_absent={'c3d4e5f6' not in r.stdout and 'tu-stale-bash-paired-1' not in r.stdout}"
                  f"\n{r.stdout}")
    ok &= stale_pass

    r = run("mechanism-dead-fires", "2026-07-15T00:05:00Z")
    md_fires_pass = (
        r.returncode == 1
        and "LIVENESS QUESTION" in r.stdout
        and "mechanism-level question" in r.stdout  # the M2 typed finding, not per-event noise
        and "22 eligible dispatch(es)" in r.stdout
        # the tripwire REPLACES the per-dispatch sweep -- none of the 22 individual "bash
        # dispatch <key>" lines the old per-event path would have printed may appear.
        and "bash dispatch md" not in r.stdout
        and r.stdout.count("LIVENESS QUESTION") == 1  # exactly one finding, not 22
    )
    report.append(f"=== mechanism-dead-fires ===\n  [{'ok' if md_fires_pass else 'FAIL'}] "
                  f"exit={r.returncode} "
                  f"has_mechanism_finding={'mechanism-level question' in r.stdout} "
                  f"eligible_count_shown={'22 eligible dispatch(es)' in r.stdout} "
                  f"no_per_dispatch_noise={'bash dispatch md' not in r.stdout} "
                  f"question_count={r.stdout.count('LIVENESS QUESTION')}\n{r.stdout}")
    ok &= md_fires_pass

    r = run("mechanism-dead-below-threshold", "2026-07-15T00:05:00Z")
    md_below_pass = (
        r.returncode == 1
        and "mechanism-level question" not in r.stdout  # below the 20-eligible floor: no tripwire
        and "LIVENESS QUESTIONS RAISED: 3 open dispatch(es), 3 liveness question(s)" in r.stdout
        and "bash dispatch bt0000bb" in r.stdout  # ordinary per-dispatch reporting resumes
    )
    report.append(f"=== mechanism-dead-below-threshold ===\n  "
                  f"[{'ok' if md_below_pass else 'FAIL'}] exit={r.returncode} "
                  f"no_mechanism_finding={'mechanism-level question' not in r.stdout} "
                  f"per_dispatch_reporting="
                  f"{'LIVENESS QUESTIONS RAISED: 3 open dispatch(es), 3 liveness question(s)' in r.stdout}"
                  f"\n{r.stdout}")
    ok &= md_below_pass

    print("\n".join(report))
    if ok:
        print("ALL CASES OK -- watchdog-liveness both-polarity proof clean (quiet fixture stays "
              "silent within slack on both the Bash and subagent surfaces, stale fixture raises a "
              "liveness question per surface naming the elapsed-vs-expected delta -- never a bare "
              "STALE/HUNG/DEAD verdict -- the paired/unpairable subagent AND bash dispatches are "
              "correctly excluded from the finding, and M2's mechanism-dead tripwire fires as one "
              "typed finding at/above the eligible-dispatch floor and stays silent below it).")
        return 0
    print("FAILURE -- see [FAIL] case(s) above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
