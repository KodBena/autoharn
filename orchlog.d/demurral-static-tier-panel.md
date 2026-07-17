subject: demurral detector, free static tier
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

The ADR-0013 Rule 3 demurral detector gained a third usable mode on 2026-07-17:
`"static"` — a zero-cost tier that never invokes a model. Until now your choices
were off (the shipped default) or `"observe"`, which spends a real `claude -p`
call per event; in practice that meant no detection at all. Static matches a
phrase list rooted in Rule 3's own vocabulary ("overkill", "over-engineering",
"YAGNI", "gold-plating", ...) and, on a hit, injects a BENIGN nudge into the
agent's own context: be mindful of Rule 3 and reconsider — and if this is a
neutral scope question, a fair-dealing renegotiation, or a genuine external
bound, disregard the note. The agent judges its own false positives; nothing
blocks, ever.

To arm it on your world (born before this feature, so two steps):

1. Copy the two `demurral_detect.py` hook entries from the current
   `bootstrap/templates/settings.json.tmpl` (PreToolUse/AskUserQuestion and
   Stop) into your `.claude/settings.json`, with the autoharn-root path your
   other hooks already use.
2. In your `.claude/apparatus.json`: `"demurral_detect": {"mode": "static"}`.

To customize the phrases: copy `instruments/demurral_phrases.default.json` to
your world's `.claude/demurral_phrases.json` and edit — your file wholesale
replaces the default (missing file falls back to the default; a malformed file
warns loudly and falls back, never silently empty). The list is operator data
by design; no code surgery.

Honest numbers, so the tier is not over-trusted: against the upstream eval
corpus it catches roughly one in six demurrals (paraphrases evade it by
construction) with about one benign false nudge per sixty clean texts. It is a
free floor, not a detector of record; `"observe"` (costed) remains the real
classifier and, when on, its verdict governs — static then only covers turns
where the classifier call itself fails.

Full documentation: `bootstrap/templates/APPARATUS.md` (the switchboard doc),
the `cost_note` beside the switch in `bootstrap/templates/apparatus.json`, and
`hooks/demurral_detect.py`'s own docstring.
