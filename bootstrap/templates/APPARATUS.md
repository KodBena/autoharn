# Apparatus config — the per-world mechanism switchboard

This document is for anyone configuring or auditing a project scaffolded from this repository:
it explains how to turn each safety mechanism on, off, or into observe-only mode, and what
changes when you do. `apparatus.json` is this project's per-instance choice surface: the
deny-hint text a refused edit is taught, plus a **`mechanisms`** object — one entry per
mechanism this project ships, each independently switched **`"off"` | `"observe"` |
`"enforce"`** (maintainer mandate, 2026-07-10) — with ONE named exception,
`demurral_detect`'s additional `"static"` value (maintainer design, 2026-07-17; see its own
row in the table below and its dedicated note). Unlike the OLD `assurance` block this file used
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
    "bash_completion":  {"mode": "observe"},
    "doc_attestation":  {"mode": "off", "note": "..."}
  }
}
```

## The three modes, binding for every mechanism (one named exception below)

- **`"off"`** — the mechanism's own deny/warn paths are skipped entirely: no journal entry, no
  state file touched, exactly as if that mechanism's code did not exist for this call.
- **`"observe"`** — the SAME checks run (a ticket lookup, a work-item query, a debt collection —
  whatever the mechanism does) so its own state stays live and current, but a would-have-denied
  outcome is turned into an **ALLOW** carrying a loud, non-blocking `additionalContext` warning
  (the agent sees it on its own next turn) plus a journal record. Observe mode **never** denies,
  blocks, or asks.
- **`"enforce"`** — the mechanism runs its full, original behavior: a refusal really refuses.

**The one named exception:** `demurral_detect` alone also accepts **`"static"`**, a fourth,
zero-cost, observer-only tier that never calls the classifier and never blocks — see its table
row and dedicated note below for the full shape (what it matches, how it composes with
`"observe"`'s fallback, and why this one mechanism departs from the three-mode convention every
other mechanism in this project holds to).

**Missing file, missing `mechanisms` key, or a missing per-mechanism entry** resolves to that
mechanism's own **stated default** (next section) — never an error.

**An unrecognized mode string** (anything other than the mechanism's own valid set — the three
above, or `demurral_detect`'s four) never widens permissions: every hook falls back to its own
default with a loud stderr warning naming the exact bad value and the file it came from. A typo
in this file can only make a mechanism MORE conservative than intended, never less.

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

## The thirteen mechanisms and their defaults

The table below lists every mechanism this project ships, the file that implements it (a hook,
for twelve of the thirteen; a `.tmpl` operator verb for the thirteenth, `doc_attestation` — its
own row says so explicitly), its shipped default mode, and why that default was chosen — the
per-mechanism detail behind the switchboard example above.

| mechanism            | implementing file                             | default   | why |
|----------------------|------------------------------------------------|-----------|-----|
| `change_gate`         | `hooks/pretooluse_change_gate.py`               | `enforce` | free per call — defaults to its current strength |
| `permit_to_work`      | `hooks/pretooluse_change_gate.py` (same file, independent switch) | `enforce` | free per call |
| `decomposition_review`| `hooks/pretooluse_change_gate.py` (same file, independent switch) | `observe` | free per call, but this mechanism is NEW and changes what an already-running world's writes are gated on the moment its `hooks/` is updated — defaults to `observe` (journals the would-be denial) rather than retroactively blocking a live world with no operator opt-in; `enforce` is the intended steady state once a world has adopted `countersign_obligation` rows (the ledger table naming which claimed work items require an outside reviewer's countersign before their writes unblock — see the named nuance below) for its work items |
| `stamp_intercept`      | `hooks/stamp_intercept.py`                      | `enforce` | free per call — injection itself is free/harmless in EVERY mode; only the broken-secret DENY is mode-gated |
| `clean_exit`           | `hooks/stop_clean_exit.py`                      | `enforce` | free per call |
| `demurral_detect`      | `hooks/demurral_detect.py`                      | **`off`** | **spends a real `claude -p` classifier call per invocation, in `"observe"` only** — "no world may silently bill its operator" (maintainer mandate, verbatim); the `cost_note` field sits next to this switch on purpose. Accepts a FOURTH value, `"static"` (2026-07-17), which spends nothing — see the dedicated note below |
| `mutation_observer`    | `hooks/posttooluse_mutation_observer.py`        | `observe` | `enforce` is **impossible** for this mechanism (a PostToolUse observation fires after the mutation already happened — there is no "deny" available); if apparatus.json ever names `enforce` here, the hook warns loudly and behaves as `observe` |
| `delegation_observer`  | `hooks/pretooluse_delegation_observer.py`       | `observe` | `enforce` is **not yet sanctioned** for this mechanism (a PreToolUse deny on a subagent dispatch is possible in principle, unlike `mutation_observer`'s genuine PostToolUse impossibility, but has not been maintainer-ratified — [BACKLOG.md](../../BACKLOG.md) "Run-8 mid-run forensics", 2026-07-11); if apparatus.json ever names `enforce` here, the hook warns loudly and behaves as `observe` |
| `doc_shapes_gate`      | `hooks/pretooluse_doc_shapes_gate.py`           | `observe` | **free per call** (pure text scanning, no subprocess) — `observe`, not `enforce`, because this is the FIRST live deployment of this check as a write-time blocking gate anywhere in this project (see the hook's own module docstring for the full reasoning); **the one-line flip to `enforce` for a given scaffolded project** is `"doc_shapes_gate": {"mode": "enforce"}` in that project's own `.claude/apparatus.json` — no code change, live on the next `Write`/`Edit` |
| `doc_legibility_critic`| `hooks/doc_legibility_critic.py`                | **`off`** | **spends a real `claude -p` classifier call per `.md` Write/Edit** — same "no world may silently bill its operator" mandate as `demurral_detect`; the zero-context-reader documentation discipline's (`law/adr/0017-the-zero-context-reader.md`) lightweight, portable transport, delivered UNWIRED into any hook chain — this entry only takes effect once a project wires the PostToolUse attachment documented in the hook's own module docstring |
| `read_observer`        | `hooks/pretooluse_read_observer.py`             | `observe` | **free per call** (one journal line, no subprocess, no LLM call) — defaults `observe` like `mutation_observer`/`delegation_observer`, the house convention that a costless observer starts ON rather than OFF; `enforce` is **not sanctioned** (reading a file is not a refusable act under this project's law) — if apparatus.json ever names `enforce` here, the hook warns loudly and behaves as `observe` |
| `bash_completion`      | `hooks/posttooluse_bash_completion.py`          | `observe` | **free per call** (one journal line, no subprocess, no LLM call) — same costless-observer convention as `mutation_observer`/`read_observer`; journals a Bash call's completion timestamp beside `stamp_intercept`'s existing pre-call token, correlated by the harness-assigned `tool_use_id` at READ TIME (a consumer join, e.g. `engine/contemp_edb.py`'s `dispatch_token_by_tool_use_id()`/`join_bash_completions()`) — CORRECTED 2026-07-14 (design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md): the original command-text-hash correlation was dead at birth (`stamp_intercept` rewrites every command between the two hashes), so this hook now stores no pairing verdict at all, only event-local facts (`ts`, `session_id`, `tool_use_id?`, `duration_ms?`, `command_sha256`, `command_head`). `enforce` is **impossible** (a PostToolUse leg fires after the command already finished — no "deny" available), same shape as `mutation_observer`; the hook warns loudly and behaves as `observe` if apparatus.json ever names it. Added 2026-07-12 ("Small-follow-ups commission") — this row and the shipped `apparatus.json` default were briefly out of sync with the mechanism actually shipping in `hooks/`, found and fixed by the configuration-surface-survey commission's own unknown-key sweep work ([BACKLOG.md](../../BACKLOG.md) "Configuration-surface survey, adopter's eyes", 2026-07-11 entry, gap 1) — the worked example of exactly the drift `filing/apparatus_registry.py`'s derive-don't-hand-list design exists to foreclose |
| `doc_attestation`      | `bootstrap/templates/distance-to-clean.tmpl` (NOT a hook — see the named nuance below) | **`off`** | **free per call** (pure hashing, no LLM call, no network) — OFF anyway, because this switch is not about cost: it gates whether `./distance-to-clean` (the operator verb that reads a deployment's outstanding closure debt — unreviewed decisions, open questions, work-item violations — in one pass; `bootstrap/templates/distance-to-clean.tmpl`) counts a DOC-ATTESTATION section's debt for the ADR-0017 A:B:C fresh-context audit loop, a workflow a deployment adopts by choice (`design/ORCH-SPEC-ABC-OFFERING.md` §4). `enforce` is **not applicable** (this section only ever reports, it has no deny path) — degrades to `observe` with a warning, same shape as `mutation_observer`/`bash_completion`. Added 2026-07-12 (tracker item `abc-loop-offering`) |

The table above states each mechanism's default and the one-line reason for it; the notes below
add per-mechanism detail a table cell is too narrow to carry.

- **`decomposition_review`** (historical record — BACKLOG.md is retired as a live document; the
  dated entry "decomposition-review-blocker" that named this ruling is preserved in git history,
  `git show d6f64ee:BACKLOG.md`, maintainer ruling 2026-07-12) denies a substantive
  `Write`/`Edit`/`NotebookEdit` anywhere under `SUBJECT_ROOT`
  (the scaffolded project's own root directory, wired via `deployment.json` or an explicit env
  var — see this file's own `change_gate`/`permit_to_work` rows) — deliberately NOT restricted
  to `permit_to_work`'s `*.py`-pattern governed set, since a bad decomposition threatens every
  artifact a claimed work item touches — or a governed-file-mutating `Bash` command, unless the
  CLAIMED work item's own opening ledger row has been countersigned (an unsuperseded `attest`
  review from a distinct actor). This is the exact discharge test the ledger's `review_gap` SQL
  view already computes for any obligated row (see `hooks/pretooluse_change_gate.py`'s own module
  docstring for the full mechanics), applied here to that one row. This mechanism is VACUOUS, by
  construction, in a world whose `countersign_obligation` table carries no rows at all — such a
  world never adopted the review-obligation regime, so this mechanism adds nothing,
  automatically, with no separate "table is empty" branch. Worlds scaffolded before the s22
  kernel-lineage delta (`kernel/lineage/s22-work-item-ledger.sql`, the additive schema change
  that adds each project's own per-project work-item ledger) carry no per-project work-item
  ledger view (`work_item_current`) at all and skip it entirely, same as `permit_to_work`. The
  motivating specimen: in a prior run of this project's
  own operator loop, a claimed work item's implementation began six seconds after it was claimed,
  ~2.5 minutes ahead of the decomposition's own countersign verdict.
- **`clean_exit`**'s circuit breaker can fire repeatedly, in the SAME session, under a
  deliberately WIDE decomposition (many parallel open work items, sized for resumability) --
  this is the mechanism working as designed, not breakage (witnessed in the ent-observatory
  series — read-only audit cycles over the `~/ent` deployment, this repo's first scaffolded
  subject — cycle-001, [observatory/ent/cycle-001.md](../../observatory/ent/cycle-001.md);
  tracker `stop-clean-exit-wide-decomposition-doc`). A session carrying 16-17 open work items
  can trip the 3-strike breaker (`DEBT_REPEAT_LIMIT`, `hooks/stop_clean_exit.py`) several times
  in one sustained run: closing one item shrinks the debt set but, with that many items still
  open, the remaining set is still non-empty and still blocks. A separate fix
  (`stop-breaker-progress-reset-defect`, see `hooks/stop_clean_exit.py`'s own "BREAKER
  TRANSITION" module-docstring section) makes the breaker INHERIT its count across a
  strict-subset debt-set shrink (closing an item) instead of resetting to 1 -- so ordinary
  progress no longer pays for two fresh blocks per closed item -- but a wide-enough
  decomposition can still exhaust the breaker on its own terms (the open count never drops to
  zero across three consecutive stops) and fail open with the loud
  "CIRCUIT BREAKER FIRED" banner. Read repeated fail-opens under a wide decomposition as the
  designed trade named in the hook's own module docstring ("never let an unclosable-debt
  session become un-endable"), not as a broken gate -- the fix above narrows how often it
  fires, it does not (and is not meant to) eliminate legitimate firing under a genuinely wide,
  still-open debt set.
- **`stamp_intercept`** treats injection and denial separately: `"observe"` still injects the
  HMAC stamp on a healthy secret (identical to `"enforce"` — injection is free and harmless), but
  the one thing it never does is DENY: an explicitly-configured-but-broken `STAMP_SECRET` passes
  the command through **unstamped**, loudly flagged, instead of refusing it. `"off"` means no
  injection at all — the command passes through completely untouched.
- **`demurral_detect`** also carries per-mechanism SETTINGS next to its mode: `classifier_command`
  (a JSON list of argv strings overriding the default `claude -p --model ...` invocation),
  `timeout_s` (the classifier's hard per-call timeout), and `cost_note` (free text for a human
  reading this file — never acted on by code). **Its mode accepts a FOURTH value, `"static"`**
  (maintainer design, 2026-07-17, `hooks/demurral_detect.py`'s own module docstring "STATIC
  TIER" section) — the one mechanism in this project that departs from the project-wide
  off/observe/enforce convention, because the static tier is a genuinely distinct detection
  strength, not a variant of an existing one:
    - `"static"` runs ONLY a case-insensitive, word-boundary match against a phrase list rooted
      in [ADR-0013](../../law/adr/0013-execution-integrity.md) Rule 3's own canonical demurral
      vocabulary — no subprocess, no `claude -p` call, ever, at this mode value. It misses every
      paraphrase by construction (enumeration fails open, per
      [ADR-0011](../../law/adr/0011-mechanization-discipline.md) Rule 4's "a net quantifies over
      the class, not the instance") and is offered anyway because the honest alternative —
      `"off"` (nothing) or `"observe"` (a real, billed call) — left most worlds with no
      detection running at all.
    - `"observe"` is unchanged: the costed classifier runs, and its verdict (POSITIVE or
      NEGATIVE) governs outright — the static tier is not consulted when the classifier answers.
      `"observe"` falls back to the static tier ONLY when the classifier is unavailable this
      turn (timeout, subprocess failure, unparsed reply), and journals that fallback honestly
      (`tier: "static_fallback"`), never presenting a static hit as a classifier verdict.
    - `"enforce"` is unaffected by this addition — still not implemented for this mechanism,
      still degrades to `"observe"` with a warning.
    - **The phrase list is DATA, not a code constant** (ADR-0012's data/code-separation
      discipline, applied here 2026-07-17 on the maintainer's explicit instruction): the
      shipped default lives at
      [`instruments/demurral_phrases.default.json`](../../instruments/demurral_phrases.default.json)
      — a plain JSON file (`{"phrases": [...], ...}`) with its own header fields explaining what
      it is and how to change it, so an operator edits the vocabulary without touching any code.
      A deployment that wants its own words entirely replaces the effective list — not merged,
      full replacement — by copying that file to
      `<world-root>/.claude/demurral_phrases.json` and editing it; a present-but-malformed
      override degrades loudly (one stderr warning) back to the shipped default, never to a
      silently empty list, and a missing override simply uses the shipped default. See
      `hooks/demurral_detect.py`'s `_resolve_static_phrases` for the exact resolution order
      (override, then shipped default, then a tiny hardcoded emergency floor if even the
      shipped file is unreadable — a broken-checkout case, not an ordinary one).
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
  to this project's own repository only (it is not part of the scaffold a new project gets, and
  this repo's own `.claude/apparatus.json` carries no entry for it either: a free deterministic
  gate, like `gates/doc_shapes.py`/`gates/link_integrity.py` before it, is not switchboard-gated
  at all). A scaffolded project DOES get a related, distinct capability — a `doc_attestation`
  switchboard entry of its own (this table's last row) governing whether `./distance-to-clean`
  counts A:B:C debt, plus a per-deployment `./attest-doc` verb that reads/writes THAT
  deployment's own attestation ledger by importing this repo's gate module directly, live, the
  same "verbs are shims into the autoharn checkout" pattern the scaffold's three operator
  commands `led`/`judge`/`pickup` already use (each is a thin per-deployment script that `exec`s
  the corresponding `bootstrap/templates/*.tmpl` out of the autoharn checkout on every
  invocation, never a frozen copy)
  (`design/ORCH-SPEC-ABC-OFFERING.md`, tracker item `abc-loop-offering`) — never a copy of the
  gate script itself, and never wired as that deployment's own commit-time hook (most scaffolds
  are not even guaranteed to be a git repository).
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
  (`.claude/logs/bash_completions.jsonl`) carrying its own `tool_use_id` — the harness-assigned
  identity present on both the PreToolUse and PostToolUse legs of one Bash call — so a consumer
  can JOIN it at read time against `stamp_intercept`'s own dispatch journal, which carries the
  same identity. CORRECTED 2026-07-14 (design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md): this hook
  used to compute and store a FIFO-by-command-hash pairing verdict itself; that mechanism was
  dead at birth (`stamp_intercept` rewrites the command between the two hashes) and is gone —
  the hook now stores no pairing verdict at all, only facts local to its own event. The value is
  still the pairing's duration for a non-trivial call (a build, a test suite), not the common ~0s
  call. It has no deny path, for the same reason as `read_observer`.
- **`doc_attestation`** is read by `bootstrap/templates/distance-to-clean.tmpl`, not by any file
  under `hooks/` — the first mechanism in this project's history for which that is true.
  `filing/apparatus_registry.py`'s known-mechanism sweep (the same one `gates/
  apparatus_unknown_keys.py` and `hooks/pretooluse_change_gate.py`'s own `_warn_unknown_mechanisms`
  use) was widened the same day to scan `bootstrap/templates/*.tmpl` alongside `hooks/*.py`, so
  this key is recognized by construction rather than needing a one-off carve-out (see that
  module's own "WHERE IT SCANS" docstring section) — a real hazard caught and closed in the same
  change that introduced the need for it (CLAUDE.md's hazard-in-reach-of-the-work duty), not a
  gap left for the next reader to trip on. `mode` is `"off"` or `"observe"` only (see the table
  row above for why `"enforce"` degrades rather than applies); `./distance-to-clean`'s
  DOC-ATTESTATION section and `./attest-doc check` read the identical classification
  (`gates/doc_attestation_presence.py`'s `classify()`), so the two never disagree about which
  documents are debt.

## The apparatus-flip watcher — deliberately NOT in the switchboard above

`hooks/posttooluse_apparatus_flip.py` (tracker item `apparatus-flip-witnessing`, 2026-07-12) journals a
typed event every time `.claude/apparatus.json` itself changes — content hashes before/after, and
which mechanisms' `mode` values changed, when the content parses. It closes a real gap the twelve hook-implemented
mechanisms above left open (twelve, not thirteen: `doc_attestation` is read by a `.tmpl` verb, not
by any hook, so it never watches anything): none of them unconditionally watches an edit to THIS file —
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
