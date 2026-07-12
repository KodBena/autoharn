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
    "decomposition_review": {"mode": "observe"},
    "stamp_intercept":  {"mode": "enforce"},
    "clean_exit":       {"mode": "enforce"},
    "demurral_detect":  {"mode": "off", "cost_note": "...", "classifier_command": [...], "timeout_s": 10},
    "mutation_observer":{"mode": "observe"},
    "delegation_observer":{"mode": "observe"},
    "doc_shapes_gate":  {"mode": "observe"},
    "doc_legibility_critic":{"mode": "off", "cost_note": "...", "classifier_command": [...], "timeout_s": 10},
    "read_observer":    {"mode": "observe"},
    "bash_completion":  {"mode": "observe"}
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
- **`"enforce"`** — the mechanism runs its full, original behavior: a refusal really refuses.

**Missing file, missing `mechanisms` key, or a missing per-mechanism entry** resolves to that
mechanism's own **stated default** (next section) — never an error.

**An unrecognized mode string** (anything other than the three above) never widens permissions:
every hook falls back to its own default with a loud stderr warning naming the exact bad value
and the file it came from. A typo in this file can only make a mechanism MORE conservative than
intended, never less.

**An unrecognized mechanism NAME** — a typo'd key under `mechanisms` itself, e.g.
`"doc_shapse_gate"` — is a DIFFERENT defect from a bad mode value, caught a different way
([BACKLOG.md](../../BACKLOG.md) "Configuration-surface survey, adopter's eyes", 2026-07-11, gap 1: mode values were
always validated loudly; nothing swept the keys, so a typo'd mechanism name configured nothing
and warned no one). `hooks/pretooluse_change_gate.py` sweeps the WHOLE `mechanisms` object — not
only its own two keys — against `filing/apparatus_registry.py`'s known-mechanism set (derived
live from `hooks/*.py`'s own source, never a hand-typed list) on every invocation, so it fires on
virtually the next governed `Write`/`Edit`; `gates/apparatus_unknown_keys.py` runs the identical
check on demand against any named `apparatus.json` or world directory. Same never-widens posture
as a bad mode value: an unrecognized key is never treated as configuring anything, and the
warning names both the bad key and the full valid set.

## The twelve mechanisms and their defaults

The table below lists every mechanism this project ships, the hook file that implements it, its
shipped default mode, and why that default was chosen — the per-mechanism detail behind the
switchboard example above.

| mechanism            | hook                                          | default   | why |
|----------------------|------------------------------------------------|-----------|-----|
| `change_gate`         | `hooks/pretooluse_change_gate.py`               | `enforce` | free per call — defaults to its current strength |
| `permit_to_work`      | `hooks/pretooluse_change_gate.py` (same file, independent switch) | `enforce` | free per call |
| `decomposition_review`| `hooks/pretooluse_change_gate.py` (same file, independent switch) | `observe` | free per call, but this mechanism is NEW and changes what an already-running world's writes are gated on the moment its `hooks/` is updated — defaults to `observe` (journals the would-be denial) rather than retroactively blocking a live world with no operator opt-in; `enforce` is the intended steady state once a world has adopted `countersign_obligation` rows for its work items |
| `stamp_intercept`      | `hooks/stamp_intercept.py`                      | `enforce` | free per call — injection itself is free/harmless in EVERY mode; only the broken-secret DENY is mode-gated |
| `clean_exit`           | `hooks/stop_clean_exit.py`                      | `enforce` | free per call |
| `demurral_detect`      | `hooks/demurral_detect.py`                      | **`off`** | **spends a real `claude -p` classifier call per invocation** — "no world may silently bill its operator" (maintainer mandate, verbatim); the `cost_note` field sits next to this switch on purpose |
| `mutation_observer`    | `hooks/posttooluse_mutation_observer.py`        | `observe` | `enforce` is **impossible** for this mechanism (a PostToolUse observation fires after the mutation already happened — there is no "deny" available); if apparatus.json ever names `enforce` here, the hook warns loudly and behaves as `observe` |
| `delegation_observer`  | `hooks/pretooluse_delegation_observer.py`       | `observe` | `enforce` is **not yet sanctioned** for this mechanism (a PreToolUse deny on a subagent dispatch is possible in principle, unlike `mutation_observer`'s genuine PostToolUse impossibility, but has not been maintainer-ratified — [BACKLOG.md](../../BACKLOG.md) "Run-8 mid-run forensics", 2026-07-11); if apparatus.json ever names `enforce` here, the hook warns loudly and behaves as `observe` |
| `doc_shapes_gate`      | `hooks/pretooluse_doc_shapes_gate.py`           | `observe` | **free per call** (pure text scanning, no subprocess) — `observe`, not `enforce`, because this is the FIRST live deployment of this check as a write-time blocking gate anywhere in this project (see the hook's own module docstring for the full reasoning); **the one-line flip to `enforce` for a given scaffolded project** is `"doc_shapes_gate": {"mode": "enforce"}` in that project's own `.claude/apparatus.json` — no code change, live on the next `Write`/`Edit` |
| `doc_legibility_critic`| `hooks/doc_legibility_critic.py`                | **`off`** | **spends a real `claude -p` classifier call per `.md` Write/Edit** — same "no world may silently bill its operator" mandate as `demurral_detect`; the zero-context-reader documentation discipline's (`law/adr/0017-the-zero-context-reader.md`) lightweight, portable transport, delivered UNWIRED into any hook chain — this entry only takes effect once a project wires the PostToolUse attachment documented in the hook's own module docstring |
| `read_observer`        | `hooks/pretooluse_read_observer.py`             | `observe` | **free per call** (one journal line, no subprocess, no LLM call) — defaults `observe` like `mutation_observer`/`delegation_observer`, the house convention that a costless observer starts ON rather than OFF; `enforce` is **not sanctioned** (reading a file is not a refusable act under this project's law) — if apparatus.json ever names `enforce` here, the hook warns loudly and behaves as `observe` |
| `bash_completion`      | `hooks/posttooluse_bash_completion.py`          | `observe` | **free per call** (one journal line, no subprocess, no LLM call) — same costless-observer convention as `mutation_observer`/`read_observer`; journals a Bash call's completion timestamp beside `stamp_intercept`'s existing pre-call token, correlated by command-text hash (module docstring: "the non-null tail — builds, test suites, dispatches"). `enforce` is **impossible** (a PostToolUse leg fires after the command already finished — no "deny" available), same shape as `mutation_observer`; the hook warns loudly and behaves as `observe` if apparatus.json ever names it. Added 2026-07-12 ("Small-follow-ups commission") — this row and the shipped `apparatus.json` default were briefly out of sync with the mechanism actually shipping in `hooks/`, found and fixed by the configuration-surface-survey commission's own unknown-key sweep work ([BACKLOG.md](../../BACKLOG.md) "Configuration-surface survey, adopter's eyes", 2026-07-11 entry, gap 1) — the worked example of exactly the drift `filing/apparatus_registry.py`'s derive-don't-hand-list design exists to foreclose |

Named nuances:

- **`decomposition_review`** (BACKLOG "decomposition-review-blocker", maintainer ruling
  2026-07-12) denies a substantive `Write`/`Edit`/`NotebookEdit` anywhere under `SUBJECT_ROOT`
  (the scaffolded project's own root directory, wired via `deployment.json` or an explicit env
  var — see this file's own `change_gate`/`permit_to_work` rows) — deliberately NOT restricted
  to `permit_to_work`'s `*.py`-pattern governed set, since a bad decomposition threatens every
  artifact a claimed work item touches — or a governed-file-mutating `Bash` command, unless the
  CLAIMED work item's own opening ledger row has been countersigned (an unsuperseded `attest`
  review from a distinct actor). This is the exact discharge test the ledger's `review_gap` SQL
  view already computes for any obligated row (see `hooks/pretooluse_change_gate.py`'s own module
  docstring for the full mechanics), applied here to that one row. VACUOUS, by construction, in a
  world whose `countersign_obligation` table carries no rows at all — such a world never adopted
  the review-obligation regime, so this mechanism adds nothing, automatically, with no separate
  "table is empty" branch. Pre-s22 worlds — scaffolded before the s22 kernel-lineage delta, so
  they carry no per-project work-item ledger view (`work_item_current`) at all — skip it
  entirely, same as `permit_to_work`. The motivating specimen: in a prior run of this project's
  own operator loop, a claimed work item's implementation began six seconds after it was claimed,
  ~2.5 minutes ahead of the decomposition's own countersign verdict.
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
  ledger the delegation itself as a `decision` row (CLAUDE.md's governance preamble, the rule
  "investigation and delegation are work: ledger them BEFORE doing them") — an `enforce`
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
- **`read_observer`** watches `PreToolUse(Read)` and journals every file read (session id,
  UTC-Z timestamp, file path) to `.claude/logs/read_observer.journal.jsonl` — nothing else
  (no file content, no excerpt). It answers a question the run10 retrospective named as
  UNDECIDABLE from the existing record (`design/RETROSPECTIVE-RUN10.md`): whether a reviewer
  who claims "I independently read file X" actually did — the invocation log this project
  already keeps captures only `Bash` calls, so a `Read`-tool inspection previously left no
  trace at all. This mechanism has no warning and no deny path (unlike `delegation_observer`,
  it has nothing to teach): reading a file is never itself a policy violation under this
  project's law, so there is no enforce state to sanction.
- **`bash_completion`** watches `PostToolUse(Bash)` and journals a completion record
  (`.claude/logs/bash_completions.jsonl`) FIFO-paired by command-text hash to
  `stamp_intercept`'s own dispatch journal — the value is the pairing's duration for a
  non-trivial call (a build, a test suite), not the common ~0s call. No deny path, same
  reasoning as `read_observer`.

## The apparatus-flip watcher — deliberately NOT in the switchboard above

`hooks/posttooluse_apparatus_flip.py` (tracker item `apparatus-flip-witnessing`, 2026-07-12) journals a
typed event every time `.claude/apparatus.json` itself changes — content hashes before/after, and
which mechanisms' `mode` values changed, when the content parses. It closes a real gap the twelve
mechanisms above left open: none of them unconditionally watches an edit to THIS file —
`posttooluse_mutation_observer.py`'s Bash-driven sweep can catch an apparatus.json mutation, but
only for Bash writes and only when no work item is open+claimed — so a `Write`-tool flip of a
mechanism to `"off"` mid-session (or a Bash flip during claimed work) previously left no refusal,
no journal line, and no ledger row: the flip was simply invisible. It attaches at `PostToolUse(*)` (every tool, not an enumerated
list — a future tool that can write a file is covered without a code change) and writes to
`.claude/logs/apparatus_flip.journal.jsonl`.

This mechanism does **not** appear in the `mechanisms` table above and reads no
`mechanisms.apparatus_flip` key, on purpose: it is the one thing in this file that watches
`apparatus.json` itself, so if it took its own on/off switch FROM that file, the single most
dangerous edit — flipping this watcher off in the same `Write` that flips something else — would
silence its own witness before journaling it. It runs unconditionally whenever this project is
wired (a `SUBJECT_ROOT`, via env or `deployment.json`), the same "never itself a mode-gated
decision" posture `hooks/pretooluse_change_gate.py`'s own module docstring already establishes for
`is_governed()`. If a `"apparatus_flip"` key is ever added under `mechanisms` here expecting it to
configure something, the existing unknown-mechanism-name sweep (`filing/apparatus_registry.py`,
run from `hooks/pretooluse_change_gate.py` on every governed edit) will flag it, correctly, as a
key no hook reads — that is the honest outcome, not a bug.

Like `mutation_observer`, this hook can only warn, never deny — a `PostToolUse` leg fires after
the change already happened. Missing or malformed `apparatus.json` is handled fail-safe: content is
hashed over raw bytes regardless of whether it parses as JSON, so a flip is still detected and
journaled even when the file is broken; only the bonus per-mechanism mode breakdown degrades to
empty when either side does not parse as an object.

The world's very FIRST-ever observation is compared against `bootstrap/templates/apparatus.json`
(the shipped scaffold default) rather than trusted blindly — an out-of-frame audit caught an
earlier version of this hook silently absorbing a flip that occurred before it had ever run once,
the single highest-value blind spot for the threat it exists to close (see the hook's own module
docstring, "BASELINE"). This closes the gap for a genuine fresh scaffold; a world whose scaffold
default is unreachable still establishes its baseline silently at first observation, a disclosed
residual, not a hidden one. And, stated plainly rather than implied: this hook watches
`apparatus.json`'s bytes, never the machinery that decides whether it (or any other hook) runs at
all — rewriting `.claude/settings.json` to remove its wiring, or deleting the hook file, is
unwatched by anything in this project today. That is a hook-integrity question general to every
mechanism this document describes, not specific to this one, and is out of this watcher's scope.

## Honest limit (`law/adr/0011-mechanization-discipline.md` Rule 1's declared-enforcement-surface obligation)

Every mode above is now **live-read**, not a forward declaration — this is the change from the
prior `assurance` block, which this project's own APPARATUS.md used to warn "neither hook reads
this file." Editing `apparatus.json` today changes real behavior on the very next tool call; no
re-scaffold, no settings.json regeneration needed. `deny_hint`, by contrast, is still baked into
`.claude/settings.json`'s `DENY_HINT` env var at scaffold time (unchanged by the live-read
switchboard work described above) — editing it here does **not** retroactively update an
already-scaffolded `settings.json`; re-run the settings-generation step of
`bootstrap/new-project.sh`, or hand-edit both files together.
