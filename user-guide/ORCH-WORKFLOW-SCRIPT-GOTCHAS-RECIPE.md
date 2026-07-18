# Workflow script gotchas — five witnessed failure shapes and how to avoid them

<!-- doc-attest-exempt: doc-tree relocation mechanical edit (work item doc-tree-reorg-user-guide, ledger row 1620, 2026-07-18) -- relative link path(s) repointed to a sibling file's new location after a git-mv relocation elsewhere in the tree; no prose rewrite, same disposition as the v1.1.2 release-cut's own markers (commit 543a389). Removal condition: strike this marker and run the real A:B:C loop next time this file is touched for content, not just link repair. -->


Audience: whoever is about to write or launch a workflow script — an orchestrating
session dispatching the `Agent` tool in a loop, or a standalone driver script built on
the Claude Agent SDK (the "Workflow tool" or an in-session equivalent this project
also calls a fix-point loop). This page answers one question: **what has already gone
wrong, more than once, in this project's own workflow scripts, and what do you do
instead?** It is the fix-point FAQ entry's sibling
([USER-RECIPES-FAQ.md](USER-RECIPES-FAQ.md)'s "Workflow patterns" section covers *how
a fix-point loop is shaped*; this page covers *the concrete bugs that shape has
produced in practice*). Read this before writing a new workflow script, and re-read it
if one crashes or stalls in a way that looks unfamiliar.

Every entry below is a class this project or its deployments hit more than once, or
that carries enough downstream risk to flag on a single dated hit. Each is dated and
sourced so a later reader can verify the claim rather than take it on faith.

## 1. Args arrive as JSON VALUES, not JSON strings — a live array/object, already parsed

**The gotcha:** a workflow script that receives `args` should expect an already-parsed
JSON value — an array or object your language can index directly — not a string that
still needs `JSON.parse`/`json.loads`. Code that unconditionally calls a parse function
on `args` breaks the moment the runtime hands it a live value instead of a string; code
that unconditionally indexes into `args` as if it were already parsed breaks the moment
the runtime hands it a raw JSON string instead. Both directions have been witnessed.

**Witnessed 2026-07-13 (this repository, the `ent` deployment — a downstream project
this repository's own harness scaffolds and observes, hardening the compositor
`picom` — a separate open-source project ent's own work targets, not part of this
repository — as its test subject;
see [observatory/ent/cycle-003.md](../observatory/ent/cycle-003.md) for the report this
witness is drawn from — observatory cycle-003):** the
real (non-emulated) Phase 2/3 Workflow was launched and **crashed in 31 milliseconds**
on exactly this mismatch — "the tool passed `args` as a JSON string rather than a live
array, compounded by a script-side field-name mismatch"
([observatory/ent/cycle-003.md](../observatory/ent/cycle-003.md), §"DIFF-VS-PRIOR" and
line 238). The orchestrator running that cycle caught its own near-miss explicitly: it
had been about to report the workflow as silently stalled again, and instead checked
for a failure notification first, found the crash, fixed both bugs defensively, and
relaunched (same source). This is the third independent witness of the
**workflow-args class** — this recipe's own name for the general failure shape "a
workflow runtime and the script it calls disagree about whether `args` is a string or
an already-parsed value" — on record for this project: this orchestrator itself hit an
args-as-file-path failure and, separately, an args-as-JSON-string failure on
2026-07-12 (both banked as standing operator memory) before the `ent` deployment hit
the same class blind on 2026-07-13.

**The fix, stated as a standing idiom:** treat `args` as arriving pre-parsed — pass
arrays and objects through raw, do not call a JSON-parse function on something that may
already be a value — but guard defensively at the point of use, because the shape has
already been observed to vary:

```js
// belt-and-braces idiom: accept either shape, never assume
const parsedArgs = (typeof args === "string") ? JSON.parse(args) : args;
```

A script that only handles one shape crashes instantly and silently on the other — the
31ms crash above produced no visible symptom except "the workflow ended" until someone
went looking for a failure notification (see item 4 below, which is exactly that
lesson).

## 2. Pin the model on every `agent()` call — the workflow runtime otherwise inherits the SESSION model

**The gotcha:** a `Workflow`/`Agent` runtime's dispatch call defaults its `model`
parameter to whatever model is running the *session* that launched it, not to any
project-level default. In a project whose standing delegation contract reserves the
most capable model for orchestration/ratification and executes ordinary work on a
cheaper model (this project's own contract: "Sonnet executes by default" — see
[CLAUDE.md](../CLAUDE.md), ORCHESTRATION section), that default is exactly backwards
for a Sonnet-shaped workflow launched from an orchestrating session running the
project's most capable model.

**Witnessed 2026-07-12 (this project, maintainer-caught, run killed mid-flight):** a
workflow script's `agent()` calls carried no `model` option, so every fan-out agent
inherited the session's own model for a commission that specified a Sonnet-based
workflow. Roughly four agents on the more expensive model started before the
maintainer caught it and killed the run, burning scarce quota on work that should have
run at Sonnet cost. (This incident is recorded under the label
"pin-model-in-workflow-scripts" in this project's *operator-side* memory — the
per-session notes an orchestrating agent carries forward between sessions, stored
outside this git repository and therefore not a link this document can resolve to; it
is cited here as a dated fact the operator record carries, not as a repository
artifact. The number of agents started before the kill — roughly four — is the only
figure that record states; this page reports only that figure rather than a larger one
mentioned informally elsewhere, per the "no umbrella claims" rule in
[CLAUDE.md](../CLAUDE.md)'s ORCHESTRATION section — "Claims carry witnesses... No
umbrella claims.")

**The fix:** every `agent()` (or equivalent dispatch) call in every workflow script
this project writes pins `model` explicitly — normally `'sonnet'` — checked at
script-authoring time, the same way a dispatch prompt already names the model it
expects to run under. Never rely on the runtime's own default; the default tracks the
*orchestrating* session, which is deliberately not the model doing the work.

## 3. The Date.now()/Math.random() resume ban

**The gotcha:** a durable workflow runtime that can pause and later resume or replay a
script from a checkpoint re-executes the script's code on resume — and any call whose
return value differs between the original run and the resumed run (`Date.now()`,
`Math.random()`, or any other wall-clock- or entropy-derived value consulted for
control flow — which branch to take, which item to process next, what to name a file)
will diverge the resumed execution from the original one. The failure is silent and
structural: nothing errors, the script simply takes a different path the second time
through, and the two executions' outputs disagree with no exception raised anywhere.

**Standing status of this entry:** this is stated here as a general durable-execution
hazard — the same determinism requirement any resume/replay-capable workflow substrate
imposes — because the instruction that asked for this recipe to be written named it
explicitly as a required entry, alongside the other four items on this page. This
author could not locate a dated, repository-local incident record for it during this
pass (unlike items 1, 2, 4, and 5 below, each of which cites a real dated hit). Recording that absence rather than inventing a witness is the honest
disclosure this project's own zero-context-reader discipline requires
([ADR-0017](../law/adr/0017-the-zero-context-reader.md) Rule 1: the mandate is judgment
checked honestly, not confidence dressed as a citation). If a future workflow script
hits this class, the incident belongs in this entry, dated, alongside the others.

**The fix, stated as a standing idiom regardless:** never call `Date.now()`,
`Math.random()`, or any other non-deterministic primitive to decide what a workflow
script does next. If a script needs a timestamp or a random value, generate it once at
the point of a durable side-effect (write it to the same store the workflow itself
checkpoints against) and read it back on resume rather than re-deriving it; if a script
needs an identifier, accept one as an input parameter rather than minting one from
`Math.random()` inside the resumable body.

## 4. Stall vs. crash are opposite-cause failure shapes — check for the failure notification before diagnosing either

**The gotcha:** "the workflow produced no output" has (at least) two causes that look
identical from the outside and demand opposite responses. A genuine **stall** is a
live process making no progress — the fix is to look at what it's stuck on and reshape
the workload (smaller batches, fewer concurrent heavy agents, a narrower single-shot
job). A **crash** is a process that already ended, near-instantly, before doing any
work — the fix is to read the failure output and correct the bug that killed it. Report
a crash as a stall and you'll spend the diagnosis budget on workload-reshaping that
does nothing, because the process isn't running at all.

**Witnessed 2026-07-13 (this repository, the `ent` deployment — glossed at its first
use in item 1 above — observatory cycle-003):**
this cycle surfaced both shapes back to back on the same Workflow tool.
A genuine multi-minute silent hang on a lone heavy-generation agent (a single Opus
agent choking on a 189KB single-shot classification job — one agent asked to classify
all 93 findings from a prior audit pass in one shot) was a real stall, correctly
diagnosed and fixed by reshaping that same job: giving each finding a short integer
index instead of repeating its full text, replacing the full finding list with a
shorter summary view for the classifying agent to work from, and splitting the single
classification pass into two smaller stages. Immediately after, the real Phase 2/3 Workflow crashed in 31
milliseconds on the args-parsing bug (item 1 above) — and the orchestrator running the
cycle **caught itself about to misclassify the second failure as a repeat of the
first**: "this, not any silent hang, is the actual answer... I had not checked for a
failure notification before reporting it as running," recorded as an explicit
self-correction on the ledger
([observatory/ent/cycle-003.md](../observatory/ent/cycle-003.md) lines 58–61 and the
METHOD CANDIDATES section, item 3, which names this exact pair as "odd-but-recurring,
not yet classified" — flagged by that observer as a durable lesson even though its own
evidence base was, by its own account, still thin).

**The fix:** before reporting a workflow run as "silently stalled," check for a
failure/crash notification first — most workflow and agent-dispatch tooling surfaces
one distinctly from "still running." Only diagnose a stall (workload reshaping) once
you've confirmed the process is actually still alive; only diagnose a crash (fix the
bug, relaunch) once you've confirmed it already ended. Treating "no output yet" as
self-evidently one or the other is the mistake this entry exists to head off.

## 5. Post-mortem from the journal — `journal.jsonl` results are repr-strings, not structured data

**The gotcha:** a workflow's own journal (the append-only `.jsonl` record of what each
round did) is the right place to reconstruct what happened after the fact — but the
`result` field of a workflow-round journal entry is typically a **repr-string**: the
target language's human-readable representation of an object (Python's `repr()`, or an
equivalent stringified dump), not a nested JSON object you can index into directly.
Code that does `json.loads(entry["result"])["some_field"]` on a raw journal line will
fail or silently misparse, because the field is already a string that happens to
*look* structured, not structured data itself.

**How to read it correctly:** parse the outer line as JSON (the journal itself is
valid JSONL), then treat the `result` field's *contents* as a display string to read by
eye or by targeted regex/substring search — not as a second layer of JSON to decode.
When a post-mortem needs a specific fact out of a repr-string result (a row count, a
verdict, a file path), search for the label that fact is printed under rather than
assuming a parseable structure underneath.

## Related

- [USER-RECIPES-FAQ.md](USER-RECIPES-FAQ.md), "Workflow patterns" section — the
  fix-point loop's own shape (loop-until-dry, fresh-agent-per-round, the termination
  discipline) and this page's sibling entry.
- [observatory/ent/cycle-003.md](../observatory/ent/cycle-003.md) — the dated source
  for items 1 and 4, including the METHOD CANDIDATES section that first flagged the
  stall-vs-crash pair as a durable, not-yet-fully-classified shape.
- [design/ORCH-HARNESS-FAILURE-LEDGER.md](../vestigial_documentation/design/ORCH-HARNESS-FAILURE-LEDGER.md) — the
  standing store this and future workflow-tooling incidents are meant to accumulate in;
  harness-failure record 11 (the `ent` deployment's fix-workflow 31ms crash) is filed against this
  recipe as the work item that served it.
- [design/ORCH-AGENTIC-PATTERNS.md](../vestigial_documentation/design/ORCH-AGENTIC-PATTERNS.md) §3 — the loop-until-dry
  criterion this page's sibling FAQ entry cites, for the deeper design behind why a
  fix-point loop is shaped the way it is.
- [design/ORCH-ABC-AUDIT-LOOP-RECIPE.md](ORCH-ABC-AUDIT-LOOP-RECIPE.md) — the fresh-fork
  discipline (never resume an agent across rounds) that this page's workflow-scripting
  concerns are a sibling case of: a resumed agent's stale context is the same class of
  hazard as a resumed workflow's replayed nondeterminism (item 3 above), one level down
  the stack.
