# Apparatus config — the per-world mechanism switchboard

This document is for anyone configuring or auditing a project scaffolded from this repository:
it explains how to turn each safety mechanism on, off, or into observe-only mode, and what
changes when you do. `apparatus.json` is this project's per-instance choice surface: the
deny-hint text a refused edit is taught, plus a **`mechanisms`** object — one entry per
mechanism this project ships, each independently switched **`"off"` | `"observe"` |
`"enforce"`** (maintainer mandate, 2026-07-10). Unlike the OLD `assurance` block this file used
to carry (a forward declaration that no hook actually read), **every hook below reads its
own mode live, at invocation time** — editing this file changes real behavior on the very next
tool call, no re-scaffold needed. Format:

```json
{
  "deny_hint": "Run:  ./led -f <file> decision \"<why>\"   then re-issue the SAME edit -- ...",
  "mechanisms": {
    "change_gate":      {"mode": "enforce"},
    "permit_to_work":   {"mode": "enforce"},
    "stamp_intercept":  {"mode": "enforce"},
    "clean_exit":       {"mode": "enforce"},
    "demurral_detect":  {"mode": "off", "cost_note": "...", "classifier_command": [...], "timeout_s": 10},
    "mutation_observer":{"mode": "observe"},
    "delegation_observer":{"mode": "observe"},
    "doc_shapes_gate":  {"mode": "observe"},
    "doc_legibility_critic":{"mode": "off", "cost_note": "...", "classifier_command": [...], "timeout_s": 10}
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

## The nine mechanisms and their defaults

| mechanism            | hook                                          | default   | why |
|----------------------|------------------------------------------------|-----------|-----|
| `change_gate`         | `hooks/pretooluse_change_gate.py`               | `enforce` | free per call — defaults to its current strength |
| `permit_to_work`      | `hooks/pretooluse_change_gate.py` (same file, independent switch) | `enforce` | free per call |
| `stamp_intercept`      | `hooks/stamp_intercept.py`                      | `enforce` | free per call — injection itself is free/harmless in EVERY mode; only the broken-secret DENY is mode-gated |
| `clean_exit`           | `hooks/stop_clean_exit.py`                      | `enforce` | free per call |
| `demurral_detect`      | `hooks/demurral_detect.py`                      | **`off`** | **spends a real `claude -p` classifier call per invocation** — "no world may silently bill its operator" (maintainer mandate, verbatim); the `cost_note` field sits next to this switch on purpose |
| `mutation_observer`    | `hooks/posttooluse_mutation_observer.py`        | `observe` | `enforce` is **impossible** for this mechanism (a PostToolUse observation fires after the mutation already happened — there is no "deny" available); if apparatus.json ever names `enforce` here, the hook warns loudly and behaves as `observe` |
| `delegation_observer`  | `hooks/pretooluse_delegation_observer.py`       | `observe` | `enforce` is **not yet sanctioned** for this mechanism (a PreToolUse deny on a subagent dispatch is possible in principle, unlike `mutation_observer`'s genuine PostToolUse impossibility, but has not been maintainer-ratified — BACKLOG "Run-8 mid-run forensics", 2026-07-11); if apparatus.json ever names `enforce` here, the hook warns loudly and behaves as `observe` |
| `doc_shapes_gate`      | `hooks/pretooluse_doc_shapes_gate.py`           | `observe` | **free per call** (pure text scanning, no subprocess) — `observe`, not `enforce`, because this is the FIRST live deployment of this check as a write-time blocking gate anywhere in this project (see the hook's own module docstring for the full reasoning); **the one-line flip to `enforce` for a given scaffolded project** is `"doc_shapes_gate": {"mode": "enforce"}` in that project's own `.claude/apparatus.json` — no code change, live on the next `Write`/`Edit` |
| `doc_legibility_critic`| `hooks/doc_legibility_critic.py`                | **`off`** | **spends a real `claude -p` classifier call per `.md` Write/Edit** — same "no world may silently bill its operator" mandate as `demurral_detect`; the zero-context-reader documentation discipline's (`law/adr/0017-the-zero-context-reader.md`) lightweight, portable transport, delivered UNWIRED into any hook chain — this entry only takes effect once a project wires the PostToolUse attachment documented in the hook's own module docstring |

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
- **`delegation_observer`** watches `PreToolUse(Task/Agent)` — every subagent dispatch is
  journaled unconditionally (session id, the dispatch's `description`, and its `prompt` reduced
  to a sha256 + 200-char excerpt); a loud, non-blocking warning fires only when this world carries
  the s22 work-item layer (a per-project work-item ledger some scaffolded worlds carry and
  others don't) and no work item is currently open+claimed, teaching the operator to
  ledger the delegation itself as a `decision` row (CLAUDE.md preamble point 7) — an `enforce`
  deny path here is architecturally possible but deliberately unbuilt (see the table entry above).
- **`doc_shapes_gate`** is the PreToolUse, write-time cousin of `gates/doc_shapes.py` (this
  project's own repo-side, deterministic pre-commit check for two measured zero-context-reader
  defect shapes): it checks a `.md` file's FULL proposed content — reconstructed from
  `old_string`/`new_string` for an `Edit`, taken directly for a `Write` — the moment before it
  is written, inside a scaffolded project that is not yet even a git repository (so a
  pre-commit hook has nothing to attach to). Unlike `doc_legibility_critic`, it spends nothing
  (no `claude -p` call): a free check with nothing to hide costs nothing to expose, so unlike
  `demurral_detect` it is not `"off"` by default. It defaults to `"observe"` because this is
  its first live deployment as a blocking gate anywhere; see the table row above for the
  one-line flip to `"enforce"`.
- **`doc_legibility_critic`** carries the same settings shape as `demurral_detect`
  (`classifier_command`, `timeout_s`, `cost_note`) and the same `"off"` default for the same
  reason. It is the lightweight half of a documentation-legibility discipline defined in
  `law/adr/0017-the-zero-context-reader.md` ("ADR-0017"). That same discipline's primary
  transport is a three-role review workflow it calls A:B:C — one agent writes a document (A),
  a second agent that has seen only the document and the discipline itself reviews it fresh
  (B), and a third repairs whatever B found (C) — with a sign-off record (an "attestation":
  which document version was reviewed, by whom, and with what result) checked for presence at
  commit time. That commit-time presence check — `gates/doc_attestation_presence.py` — belongs
  to this project's own repository only (it is not part of the scaffold a new project gets)
  and carries no apparatus.json entry: nothing in a freshly scaffolded project reads one, and per
  this file's own convention a free deterministic gate (like `gates/doc_shapes.py` and
  `gates/link_integrity.py` before it) is not switchboard-gated at all.

## Honest limit (`law/adr/0011-mechanization-discipline.md` Rule 1's declared-enforcement-surface obligation)

Every mode above is now **live-read**, not a forward declaration — this is the change from the
prior `assurance` block, which this project's own APPARATUS.md used to warn "neither hook reads
this file." Editing `apparatus.json` today changes real behavior on the very next tool call; no
re-scaffold, no settings.json regeneration needed. `deny_hint`, by contrast, is still baked into
`.claude/settings.json`'s `DENY_HINT` env var at scaffold time (unchanged from before this pass) —
editing it here does **not** retroactively update an already-scaffolded `settings.json`; re-run
the settings-generation step of `bootstrap/new-project.sh`, or hand-edit both files together.
