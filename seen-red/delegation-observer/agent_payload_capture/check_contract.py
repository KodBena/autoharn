#!/usr/bin/env python3
"""check_contract.py -- the M3-shaped fixture for the delegation-observer pairing-key review
(ledger row 582, vestigial_documentation/design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md sec-3/sec-6.6). This directory holds a
REAL captured PreToolUse+PostToolUse payload pair for the `Agent` tool (Task's current name),
taken from a scratch headless `claude -p` run that dispatched a subagent via the Task tool
(2026-07-14, this build) -- `transcript_path`/`cwd`/`session_id` scrubbed of user-identifying
content, every other key byte-preserved.

This is the harness-contract fact the hook's own docstring used to assert freehand (and got
wrong, per the RCA's lapse 2: "an environment fact was cached as prose ... never re-verified").
It replaces prose with a checkable artifact: run this file, it asserts what the captured payloads
actually contain. If a future Claude Code version changes the contract, re-capture and this
checker will start failing loudly instead of the hook silently trusting stale prose again.

Usage: python3 seen-red/delegation-observer/agent_payload_capture/check_contract.py
Exit 0 if the contract holds; 1 otherwise.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    pre = json.loads((HERE / "PreToolUse_Agent.json").read_text(encoding="utf-8"))
    post = json.loads((HERE / "PostToolUse_Agent.json").read_text(encoding="utf-8"))
    failures: list[str] = []

    if pre.get("hook_event_name") != "PreToolUse":
        failures.append("PreToolUse_Agent.json is not a PreToolUse capture")
    if post.get("hook_event_name") != "PostToolUse":
        failures.append("PostToolUse_Agent.json is not a PostToolUse capture")
    if pre.get("tool_name") not in ("Agent", "Task"):
        failures.append("PreToolUse capture is not a Task/Agent dispatch")

    pre_id = pre.get("tool_use_id")
    post_id = post.get("tool_use_id")
    if not pre_id:
        failures.append("PreToolUse payload carries no tool_use_id -- the RCA sec-3 claim does "
                         "not hold for this capture")
    if not post_id:
        failures.append("PostToolUse payload carries no tool_use_id -- the RCA sec-3 §7 item 2 "
                         "residual (UNWITNESSED for Task/Agent's PostToolUse leg) would NOT be "
                         "settled by this capture")
    if pre_id and post_id and pre_id != post_id:
        failures.append(f"tool_use_id diverges between legs: PreToolUse={pre_id!r} "
                         f"PostToolUse={post_id!r} (the identity-elimination fix REQUIRES these "
                         f"to agree)")
    if "duration_ms" not in post:
        failures.append("PostToolUse payload carries no duration_ms")

    if failures:
        print("check_contract: CONTRACT VIOLATION(S):")
        for f in failures:
            print(f"  - {f}")
        return 1

    print(f"check_contract: OK -- tool_use_id={pre_id!r} present and byte-identical across "
          f"PreToolUse and PostToolUse for Agent/Task; duration_ms={post.get('duration_ms')!r} "
          f"present on PostToolUse.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
