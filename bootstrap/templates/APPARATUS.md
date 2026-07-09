# Apparatus config — deny-hint text and assurance levels

`apparatus.json` is this project's per-instance choice surface for two things
`governed_files.json` does not carry (design/OPUS-READINESS.md move 2): the deny-hint text a
refused edit is taught, and an **assurance level** per gate family — the DO-178C-DAL-style move
named in the design doc: a level selects whether a gate family *enforces* (refuses) or merely
*observes* (records, never blocks) in THIS project. Format:

```json
{
  "deny_hint": "Run:  ./led -f <file> decision \"<why>\"   then re-issue the SAME edit -- ...",
  "assurance": {
    "change_gate": "enforce",
    "stamp_intercept": "enforce"
  }
}
```

- **`deny_hint`** — free text appended to the change gate's refusal message, naming the exact
  next command (fix-point ergonomics: the refusal is the loop's only feedback channel, so it
  should name the command, not just the policy).
- **`assurance`** — one entry per gate family this instance wires, each `"observe"` or
  `"enforce"`. The two families a scaffolded instance carries today mirror the two hooks
  `bootstrap/new-project.sh` wires in `.claude/settings.json`:
  - **`change_gate`** — `hooks/pretooluse_change_gate.py`. `"enforce"` (the shipped default)
    refuses an edit to a governed file with no preceding ledger entry; a future `"observe"`
    level would journal the same event without denying it (a lighter posture for an
    exploratory/low-assurance instance).
  - **`stamp_intercept`** — `hooks/stamp_intercept.py`. `"enforce"` (the shipped default) is
    the hook's only mode today — it always stamps a matching `psql` call; `"observe"` is named
    here for forward-compatibility with a future mode, not a distinction the hook currently draws.

**Honest limit, stated plainly (ADR-0011 Rule 1's declared-enforcement-surface obligation):**
neither hook reads this file. `assurance` is a **forward declaration** — the same status
`deployment.json` has with respect to `led`/the hooks (design/OPUS-READINESS.md move 1): the
value here documents the CHOSEN level for a human or a future gate to read, but changing it
today does not change what either hook actually does. Wiring the hooks to read `apparatus.json`
(and to honor `"observe"` by degrading a deny to a journal-only record) is named, deferred future
work, not silently promised. Likewise, editing `deny_hint` here after scaffolding does **not**
retroactively update the `DENY_HINT` value baked into `.claude/settings.json`'s PreToolUse
command at scaffold time — re-run the settings-generation step of `bootstrap/new-project.sh`, or
hand-edit both files together, until that rewiring lands.
