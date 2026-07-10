# Apparatus config — the per-world mechanism switchboard

`apparatus.json` is this project's per-instance choice surface: the deny-hint text a refused
edit is taught, plus a **`mechanisms`** object — one entry per mechanism this project ships,
each independently switched **`"off"` | `"observe"` | `"enforce"`** (maintainer mandate,
2026-07-10). Unlike the OLD `assurance` block this file used to carry (a forward declaration
that neither hook actually read), **every hook below reads its own mode live, at invocation
time** — editing this file changes real behavior on the very next tool call, no re-scaffold
needed. Format:

```json
{
  "deny_hint": "Run:  ./led -f <file> decision \"<why>\"   then re-issue the SAME edit -- ...",
  "mechanisms": {
    "change_gate":      {"mode": "enforce"},
    "permit_to_work":   {"mode": "enforce"},
    "stamp_intercept":  {"mode": "enforce"},
    "clean_exit":       {"mode": "enforce"},
    "demurral_detect":  {"mode": "off", "cost_note": "...", "classifier_command": [...], "timeout_s": 10},
    "mutation_observer":{"mode": "observe"}
  }
}
```

## The three modes, binding for every mechanism

- **`"off"`** — the mechanism's own deny/warn paths are skipped entirely: no journal entry, no
  state file touched, exactly as if that mechanism's code did not exist for this call.
- **`"observe"`** — the SAME checks run (a ticket lookup, a work-item query, a debt collection —
  whatever the mechanism does) so its own state stays live and current, but a would-have-denied
  outcome is turned into an **ALLOW** carrying a loud, non-blocking `additionalContext` warning
  (the agent sees it on its own next turn) plus a journal record. Observe mode **never** denies,
  blocks, or asks.
- **`"enforce"`** — the mechanism's full, original behavior (a refusal really refuses).

**Missing file, missing `mechanisms` key, or a missing per-mechanism entry** resolves to that
mechanism's own **stated default** (next section) — never an error.

**An unrecognized mode string** (anything other than the three above) never widens permissions:
every hook falls back to its own default with a loud stderr warning naming the exact bad value
and the file it came from. A typo in this file can only make a mechanism MORE conservative than
intended, never less.

## The six mechanisms and their defaults

| mechanism            | hook                                          | default   | why |
|----------------------|------------------------------------------------|-----------|-----|
| `change_gate`         | `hooks/pretooluse_change_gate.py`               | `enforce` | free per call — defaults to its current strength |
| `permit_to_work`      | `hooks/pretooluse_change_gate.py` (same file, independent switch) | `enforce` | free per call |
| `stamp_intercept`      | `hooks/stamp_intercept.py`                      | `enforce` | free per call — injection itself is free/harmless in EVERY mode; only the broken-secret DENY is mode-gated |
| `clean_exit`           | `hooks/stop_clean_exit.py`                      | `enforce` | free per call |
| `demurral_detect`      | `hooks/demurral_detect.py`                      | **`off`** | **spends a real `claude -p` classifier call per invocation** — "no world may silently bill its operator" (maintainer mandate, verbatim); the `cost_note` field sits next to this switch on purpose |
| `mutation_observer`    | `hooks/posttooluse_mutation_observer.py`        | `observe` | `enforce` is **impossible** for this mechanism (a PostToolUse observation fires after the mutation already happened — there is no "deny" available); if apparatus.json ever names `enforce` here, the hook warns loudly and behaves as `observe` |

Named nuances:

- **`stamp_intercept`** treats injection and denial separately: `"observe"` still injects the
  HMAC stamp on a healthy secret (identical to `"enforce"` — injection is free and harmless), but
  the one thing it never does is DENY: an explicitly-configured-but-broken `STAMP_SECRET` passes
  the command through **unstamped**, loudly flagged, instead of refusing it. `"off"` means no
  injection at all — the command passes through completely untouched.
- **`demurral_detect`** also carries per-mechanism SETTINGS next to its mode: `classifier_command`
  (a JSON list of argv strings overriding the default `claude -p --model ...` invocation),
  `timeout_s` (the classifier's hard per-call timeout), and `cost_note` (free text for a human
  reading this file — never acted on by code).
- **`mutation_observer`** has no enforce state at all (see table) — it can only warn, never deny,
  by the nature of its PostToolUse attachment point.

## Honest limit (ADR-0011 Rule 1's declared-enforcement-surface obligation)

Every mode above is now **live-read**, not a forward declaration — this is the change from the
prior `assurance` block, which this project's own APPARATUS.md used to warn "neither hook reads
this file." Editing `apparatus.json` today changes real behavior on the very next tool call; no
re-scaffold, no settings.json regeneration needed. `deny_hint`, by contrast, is still baked into
`.claude/settings.json`'s `DENY_HINT` env var at scaffold time (unchanged from before this pass) —
editing it here does **not** retroactively update an already-scaffolded `settings.json`; re-run
the settings-generation step of `bootstrap/new-project.sh`, or hand-edit both files together.
