#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T01:12:19Z
#   last-change: 2026-07-14T01:12:19Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""seen-red/hook-payload-contract/check_contract.py -- M3 (vestigial_documentation/design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md
sec-6.5): the "harness-contract facts live in a captured fixture, not prose" mechanism. The two
sibling JSON files in this directory are a REAL, LIVE-CAPTURED PreToolUse+PostToolUse payload pair
for one Bash tool call, captured 2026-07-14 during this fix's own build (a scratch project under
/tmp with dump-to-file hooks on both events, driven by a headless `claude -p` run -- the same method
vestigial_documentation/design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md's own consult used, per its §3 witness 2). `transcript_path`
is scrubbed (`"<scrubbed>"`); every other field is the harness's own, unedited output.

WHY THIS EXISTS: the defect this fix repairs (sec-2, lapse 2) was an environment fact --
"Claude Code's hook-input contract has never been observed to carry a tool_use_id" -- cached as
PROSE in three hook docstrings, copied between them, and never re-verified against the evidence
already on disk. Prose cannot be re-verified; a fixture can. This checker is the fixture's own
assertion: it fails loudly if a field a hook's fix RELIES ON is ever absent from a fresh capture,
so a future Claude Code version that drops a field is caught here first, not discovered by a hook
silently reverting to its honest-but-degraded fallback.

Refresh policy: deliberately, on a Claude Code version bump -- not on a schedule. A stale capture is
still evidence of what the contract WAS; it is superseded by re-running the capture procedure in
this docstring, never hand-edited.

Usage: python3 seen-red/hook-payload-contract/check_contract.py
Exit 0 if every asserted field is present in both captures; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str) -> dict:
    with open(HERE / name, encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    pre = _load("captured_pretooluse_bash.json")
    post = _load("captured_posttooluse_bash.json")
    failures: list[str] = []

    def require(rec: dict, label: str, *keys: str) -> None:
        for k in keys:
            if k not in rec or rec[k] in (None, ""):
                failures.append(f"{label}: missing or empty {k!r}")

    require(pre, "PreToolUse", "tool_use_id", "tool_name", "session_id", "hook_event_name")
    require(post, "PostToolUse", "tool_use_id", "tool_name", "session_id", "hook_event_name",
            "duration_ms", "tool_response")

    if pre.get("hook_event_name") != "PreToolUse":
        failures.append(f"PreToolUse capture's own hook_event_name is {pre.get('hook_event_name')!r}")
    if post.get("hook_event_name") != "PostToolUse":
        failures.append(f"PostToolUse capture's own hook_event_name is {post.get('hook_event_name')!r}")
    if pre.get("tool_name") != "Bash" or post.get("tool_name") != "Bash":
        failures.append("one leg is not a Bash capture")

    # THE load-bearing assertion this whole mechanism exists for (RCA sec-3): the SAME identity
    # on both legs of ONE tool call.
    if pre.get("tool_use_id") != post.get("tool_use_id"):
        failures.append(
            f"tool_use_id diverges across legs: PreToolUse={pre.get('tool_use_id')!r} "
            f"PostToolUse={post.get('tool_use_id')!r} -- if this ever fires, the identity-elimination "
            f"fix's own foundation (vestigial_documentation/design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md sec-3) no longer holds")

    if failures:
        print(f"FAILURES ({len(failures)}):")
        for f in failures:
            print(f"  !! {f}")
        return 1
    print(f"OK -- both legs carry tool_use_id={pre['tool_use_id']!r}, PostToolUse carries "
          f"duration_ms={post.get('duration_ms')!r}. Hook-payload contract fixture intact.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
