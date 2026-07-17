<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

A fresh agent no longer has to trip over the three sharpest house rules to learn them: `led
briefing` (`bootstrap/templates/led.tmpl`) is a new READ-ONLY verb that prints the ledger
change-gate, the flag-order asymmetry, and the same-session-countersign refusal — each with the
rule and the fix-shape its teach-text would give — plus a pointer to
`design/USER-RECIPES-FAQ.md`. It also reads `<world-root>/.claude/apparatus.json`'s
`mechanisms.rules_briefing.extra_items` (a JSON array of strings) and prints each verbatim under
an "additional world-specific rules" line — the extension point a more serious project can use
to layer its own project-specific onboarding rules onto the same mechanism, without editing this
project's own source. Malformed `extra_items` degrades loudly (one stderr warning naming the file
and the bad value) and never crashes or silently drops the core briefing.

`hooks/sessionstart_rules_briefing.py` is the SessionStart transport: it resolves the
deployment exactly as `hooks/sessionstart_durable_decisions.py` already does, shells to the
world's own `./led briefing` (the scaffolded shim next to `deployment.json`, which execs the
recorded autoharn checkout's `bootstrap/templates/led.tmpl`), and forwards its stdout as
`additionalContext`. It carries no copy of the briefing text itself — if the verb's wording
changes, the hook's output changes with it for free. Unwired (no `deployment.json` findable)
means silence, same as its sibling; WIRED-but-broken (missing `./led`, a non-zero exit, a
timeout) means one loud line saying the briefing was unavailable and why, never a blocked
session and never a silent skip.

**Matcher: `startup|compact|resume`, not `compact|resume` alone** — unlike the durable-decisions
hook, whose narrower matcher answers a specific witnessed compaction failure, a rules briefing is
useful at the start of any session an agent has not just lived through, and compaction loses it
exactly like it loses everything else in context. The settings.json fragment (this project's own
absolute-path idiom, following the durable-decisions hook's own precedent verbatim):

```json
"SessionStart": [
  {
    "matcher": "startup|compact|resume",
    "hooks": [
      {
        "type": "command",
        "command": "env LEDGER_DEPLOYMENT=/home/bork/w/vdc/1/experience/autoharn-panel/deployment.json python3 /home/bork/w/vdc/1/experience/autoharn/hooks/sessionstart_rules_briefing.py",
        "timeout": 15
      }
    ]
  }
]
```

Adding this hook alongside `hooks/sessionstart_durable_decisions.py`'s own `SessionStart` entry
means two separate `"matcher"` objects under the same `"SessionStart"` array key — one narrower
(`compact|resume`, that hook's own) and one broader (`startup|compact|resume`, this one); both
fire independently on an overlapping event, which is the intended composition, not a conflict.
