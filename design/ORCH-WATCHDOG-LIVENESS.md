# ORCH-WATCHDOG-LIVENESS: a protective watchdog against unattended zero-progress

<!-- doc-attest-exempt: disclosed gap, not a clean exemption -- this file's prior fresh-context
     A:B:C attestation (recorded when this note shipped alongside the watchdog-liveness-harness
     build, 2026-07-18) covered THAT content's legibility; this commit's edit is a narrow
     factual correction (Class 1's pairing description, and the demonstrated-run note) to keep
     the doc truthful against tools/watchdog_liveness.py's tool_use_id-join fix
     (design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md), not a rewrite of the note's content or
     legibility. The gate hashes the whole document, so the prior record no longer matches by
     construction. Waived here only to unblock this fixup commit, flagged loudly per CLAUDE.md's
     engineering-responsibility standard rather than silently routed around -- a maintainer/
     reviewer should confirm the correction reads clean and, if desired, run a fresh A:B:C pass
     to replace this marker with an actual attestation record. -->

This note is for a maintainer or implementer deciding whether, and how, this project's harness
should notice that a dispatched piece of work has gone quiet for longer than expected. It answers
one question: what can this harness's own hooks-and-journal position honestly detect and recover
about a workflow, subagent, or Bash call that may be stuck, and what does it do about the parts it
genuinely cannot reach? **In one paragraph:** this is a SAFETY feature against unattended
zero-progress, not an ergonomics nicety and explicitly not a cost-policing mechanism. The
maintainer's scenario: he leaves the terminal expecting a workflow to finish, a tool bug hangs
it at minute three, he returns two hours later to nothing — an operational hazard, his words,
"especially in a medical setting." Design bar: fail-safe, at the "recovery is the point, not
observation" standard the maintainer's correcting ledger row states (`./led show 436`, cited again
in the Commission bullet below) — and where recovery is genuinely out of reach from this harness's
own position, say so honestly and name the next-best, never fake an enforce this project cannot
honor.

- **Status:** Draft, smallest-honest-slice built alongside this note.
- **Commission:** tracker work item `watchdog-liveness-harness`, read via `./led show 433`
  (`led` is this project's tracker-ledger verb; `led show <id>` prints one ledger row in full by
  its numeric id), CORRECTED by a maintainer decision row superseding the opened framing
  (`./led show 436`), further scoped by a live-evidence follow-up mid-build (`./led show 439`).
  All three are read in full before this note was drafted; where they differ, the correction and
  the follow-up govern, per this project's own reading-the-law discipline.

## 0. The false-positive class this note leads with (row 439, read before anything below)

A session of "ent" (a separate, concurrently-run deployment of this same harness, unrelated to
the watchdog work itself — named here only because its session produced the incident that
motivated this commission) sat idle for 9m41s; that idle window is what opened this commission
(§1, Class 1). Mid-build, it was explained by ent's own session orchestrator as **not a hang**
— one very large input (a 93-finding JSON backlog) fed
to a single splitter agent, driving one long, legitimate generation between tool calls. The
maintainer relays that explanation with **stated doubt** — it is not certified fact, and this
note does not treat it as such. But the *class* it names is real regardless of whether it is the
true explanation of that specific incident, and it is this design's **principal false-positive
mode**, so it leads the note rather than trailing it as a caveat:

**Large-payload single-generation work is invisible to action-stream observation.** Every
detection position this harness has (§2 below) is a hook: PreToolUse, PostToolUse, Stop. Hooks
fire at tool-call boundaries. A long model generation *between* tool calls — reasoning over a
large pasted backlog, drafting a long document, thinking through a hard decomposition — emits
**no hook event at all** while it runs. The action stream sees the tool call that preceded it and
the tool call that follows it (if any), and nothing in between. So: **no observable activity
since expected-time-plus-slack does NOT entail no progress.** It entails exactly what it says —
nothing was observed — and a harness that cannot see between-call generation cannot honestly
tell "thinking hard" apart from "dead" from its own vantage point.

Three consequences this note and its slice hold to throughout, not as an afterthought:

1. **A breach is a liveness QUESTION, never a death verdict.** Every finding this checker emits
   is phrased as "no observable activity for Xm against an expected Ym — look here," never
   "HUNG," "DEAD," or "STALE" as a bare assertion. The checker's own output strings (§4) are
   written this way; a [`distance-to-clean`](../GLOSSARY.md#distance-to-clean) section (this
   project's operator verb for one composed read of all closure-debt dimensions) built on this
   slice later (§5) inherits the same wording discipline, not a stronger one.
2. **Recovery must weigh a real asymmetry, not just act on a threshold breach.** Killing a
   subagent or workflow that is legitimately mid-generation destroys its entire context and the
   cost already sunk into it — the whole point of a subagent's contribution can vanish. Waiting
   longer on a genuinely-hung process only loses time. The costs are **not symmetric**: a
   wrongly-killed agent loses context + cost; a wrongly-waited hang loses only wall-clock. This
   is why §3's recovery ladder never auto-kills on this checker's say-so alone (more below), and
   why every threshold in this design is an operator-configurable slack, not a fixed cutoff — the
   slack ratio is exactly the knob that encodes where a given operator wants to sit on that
   asymmetry (tight for cheap, fast, mechanical work; loose for expensive, generation-heavy work).
3. **The taxonomy below (§1) carries this class as its own named entry (class 5)**, with the ent
   incident as its worked example, doubt disclosed, not resolved — because resolving it is not
   this note's job and asserting it either way would be a claim without a witness (ADR-0013
   Rule 5).

## 1. The stall taxonomy, from tonight's real evidence

Five classes, each with: what happened, what harness position can **detect** it, and what
position can **recover** it — reach-limits stated honestly per class, not just in aggregate (§3).

### Class 1 — hung command riding the Bash timeout ceiling

**What:** a Bash tool call that never returns, riding all the way to the tool's own timeout
ceiling (up to 600s in this harness) before the caller even learns something is wrong — the
literal ent incident that opened this commission (`./led show 433`: "workflow agent idle 9m41s
— likely a hung command riding the 600s Bash ceiling"), now understood (§0) as *possibly*
something else, but the class itself — a Bash call that genuinely never returns — is real and
distinct from class 5.

**Detect:** `hooks/stamp_intercept.py` journals a dispatch token to `invocations.jsonl` at
PreToolUse; `hooks/posttooluse_bash_completion.py` journals a completion to
`bash_completions.jsonl` at PostToolUse. Pairing is a READ-TIME JOIN on the harness-assigned
`tool_use_id` (corrected 2026-07-18, `design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md`; the original
design here described FIFO-pairing by `command_sha256`, which that RCA found dead at birth —
`stamp_intercept.py` rewrites every Bash command after hashing the pre-rewrite text, injecting a
fresh per-call uuid4 before the command runs, so the two hashes could never agree; 0 of 2093
completions ever paired in the deployment that surfaced this). `tools/watchdog_liveness.py`
performs this join itself, never a stored verdict — neither hook computes or caches a pairing
result. A dispatch with **no paired completion**, whose dispatch wall-clock is already older than
expected-duration-for-this-command-class × slack, is directly observable — this is the one class
in this taxonomy the harness can point at with the least ambiguity, because a Bash command is
itself the harness's own tool-call boundary (not a black-box generation): the command is either
still running (no completion journaled) or it finished (one was). This is the slice's primary
mechanism (§4). A named degenerate case: if the pairing mechanism itself has fired zero times
across a large-enough sample of eligible (`tool_use_id`-carrying) dispatches, the checker raises
ONE typed mechanism-level finding instead of one per-event question per still-open dispatch (RCA
§5's M2 mechanism, implemented in `tools/watchdog_liveness.py`'s `_MECHANISM_DEAD_MIN_ELIGIBLE`
tripwire) — the shape that would otherwise flood an operator with ~2000 false questions if the
join itself silently broke again.

**Recover:** from the harness's own position, **not at all, today.** A PreToolUse hook cannot
reach into a Bash call already in flight and kill it; a PostToolUse hook only fires after the
call already returned (or the ceiling already killed it). The honest next-best (§3): tighten the
**dispatch-time** Bash timeout itself, so a command classed as "should take ~0.1s" is dispatched
with an actual timeout of a few seconds, not the 600s ceiling — the hang then dies loud in
seconds, converting an indefinite silent wait into a typed, bounded failure the workflow's own
control flow can route around (a `subprocess.TimeoutExpired`/non-zero exit, not a black hole).
This is a **dispatch-time** decision (the caller choosing a tighter timeout up front), not
anything a hook does after the fact — named because it is easy to conflate the two.

### Class 2 — API-side mid-response death

**What:** the model-provider connection itself dies mid-response (witnessed twice today, per the
commission's own framing) — not a tool hanging, the underlying generation stream terminating
abnormally.

**Detect:** this harness's hooks attach to Claude Code tool events, not to the token stream
between the orchestrator and the model provider — there is **no hook attachment point on this
harness's own surface for this class at all.** The only detection signal visible from a hook's
position is the *absence* of any subsequent tool call for longer than expected — indistinguishable,
from the journal alone, from class 5 (long legitimate generation) or class 4 (idle agent). Named
honestly: this class collapses into the same generic "no observable activity" signal (§4's
surface-recency check) as its weaker siblings; nothing in this harness's own reach detects it
*as this specific class*.

**Recover:** not from a hook position — a dead API connection is Claude Code's own client-runtime
concern, entirely outside this project's harness. The honest next-best: session-level supervision
sits with the orchestrator, not the harness — a human, or an orchestrating agent, watching the
session from OUTSIDE it (the `Monitor` tool this harness's orchestrator side already has for
streaming a background process's events, paired with a fallback-wakeup discipline: a standing
habit of the orchestrator polling or waking on a timer to check a session it dispatched, rather
than assuming a dispatched session will always report back on its own) is the only position that
can act on "the session appears to have gone silent," by ending the session and re-dispatching.
§3 restates this as "orchestrator-side Monitor/fallback-wakeup discipline" without redefining it.

### Class 3 — background child (subagent) that never notifies

**What:** a dispatched subagent (Task/Agent tool) that never returns — the parent orchestrator
waiting on a child that is itself wedged, crashed, or silently discarded.

**Detect:** `hooks/pretooluse_delegation_observer.py` already journals BOTH legs of a subagent
call to `delegation_observer.journal.jsonl` — a dispatch line at PreToolUse (no `kind` field) and
a `kind: "return"` line at PostToolUse, paired by `tool_use_id` (that hook's own module docstring:
"the identity the return leg now keys on" — a prior correlation shape, FIFO-by-`session_id` +
`prompt_sha256`/`dispatch_ts`, is not what the hook writes today; a checker built against that
older shape would silently never match a single pair). A dispatch record whose `tool_use_id`
never appears as some later return's own `tool_use_id`, held open longer than expected-for-class ×
slack, is directly observable from this journal alone — the second mechanism this slice
implements (§4). Honest limits: the journal carries no task-slug, so a specific dispatch cannot be
matched against a specific `estimate:` row's WALL-CLOCK field — only a configured class-default
expectation applies (§4), not a per-task one; deeper linkage (e.g. a delegation prompt tagged with
its covering work-item slug) is a named future extension, not built here (ADR-0013 Rule 4: filed,
not silently glossed). And `tool_use_id` is written defensively on both legs (`if tool_use_id:`),
so a record missing it entirely cannot be paired either way — it is skipped from detection rather
than guessed at, named the same way in the checker's own docstring (§4).

**Recover:** a PreToolUse hook on Task/Agent COULD in principle deny/intervene at dispatch time
(`pretooluse_delegation_observer.py`'s own module docstring already states this — "a deny is
technically available but NOT YET SANCTIONED"), but nothing in this harness reaches *into* an
already-dispatched subagent to kill or resume it — the parent orchestrator's own Task-tool
handling is Claude Code's own runtime, not this project's code. Honest next-best: the parent
agent's own control flow (a workflow script, or the orchestrating human) is the one position that
can act — re-dispatch the same delegation fresh, ledgering the retry, once the liveness question
is raised.

### Class 4 — workflow agent idle between tool calls (generic)

**What:** the general "nothing has happened in a while" signal, with no more specific class
attached — the shape the ent incident presented as, before class 5's explanation surfaced.

**Detect:** the most recent timestamp across every journal this deployment's hooks write (§2) is
this harness's only generic pulse. "Time since the most recent hook-observed event, of any kind,
for this session" is directly computable and is this slice's third mechanism (§4's surface-recency
sweep) — cheap, always available once any hook is wired, and the honest ceiling of what this
harness can see: it is a pulse across *all* surfaces, not a diagnosis of *which* surface stalled.

**Recover:** same reach limit as class 2 — nothing at the harness/hook position can act on "the
session looks idle" from inside the session itself (a hook cannot summon a keystroke). The
honest next-best is session-level: an **orchestrator-side** Monitor/fallback-wakeup discipline
(§3) — a supervising process (or a human) polling for exactly this pulse and acting from outside
the stalled session, which is the only position with the standing to end or resume it.

### Class 5 — large-payload single-generation work, invisible to the action stream (§0)

**What:** a long, *legitimate* generation between tool calls — a big pasted input driving one
hard reasoning/drafting pass with no intervening tool call — presenting identically, from a
journal's point of view, to classes 2 and 4. Worked example: the ent 9m41s idle window itself,
per its session orchestrator's own explanation (a 93-finding JSON backlog fed to one splitter
agent) — the maintainer's own stated doubt about that explanation is preserved here rather than
resolved, because this note has no independent way to confirm it and should not pretend to.

**Detect:** structurally **not distinguishable from class 4 by anything this harness observes.**
This is not a gap to be filled by a cleverer heuristic — the reasoning happens inside the model,
between hook attachment points, by construction. Naming it as its own class exists to change what
a breach *means*, not to add a detector: every finding this checker or a future distance-to-clean
section emits is worded as a liveness question (§0), and this class is the reason why.

**Recover:** the same reach limit as class 4, with the added, load-bearing caution from §0: any
recovery action reachable at all (dispatch-time timeout tightening, kill-and-retry) must weigh
the kill-vs-wait asymmetry before acting, because this is precisely the class where killing is
most likely to be the wrong call — an operator (or an orchestrator-side policy) sets the slack
loose enough for this class's known-expensive tasks specifically so a genuine long generation is
not mistaken for a stall by a rule that only ever watched the clock.

## 2. Detection positions available to this harness, honestly enumerated

- **PreToolUse hooks** (`stamp_intercept.py`, `pretooluse_delegation_observer.py`, others) —
  fire *before* a tool call starts. They can journal "this is about to run" and, in principle,
  deny the call outright (not sanctioned for delegation yet) — they cannot see or act on
  anything that happens *during* the call.
- **PostToolUse hooks** (`posttooluse_bash_completion.py`, the delegation observer's return leg,
  `posttooluse_mutation_observer.py`) — fire *after* a tool call has already finished. They can
  journal "this just finished, here is how long it took" — they structurally cannot deny or
  intervene in a call whose result already landed (`posttooluse_mutation_observer.py`'s own module
  docstring already states this "OBSERVER ONLY, NOT A TECHNICAL IMPOSSIBILITY... PostToolUse fires
  after the mutation already happened" for its own class; the same physics applies here).
- **Stop hooks** (`stop_clean_exit.py`) — fire when an agent turn is about to end. They can block
  or warn on ledger state at that moment — they never fire *during* a stalled tool call or a long
  generation, because the turn that would trigger Stop is exactly the thing that has not ended.
- **What no hook position reaches, at all:** the token stream between the orchestrator and the
  model provider (class 2); the internals of an already-dispatched subagent (class 3, once
  dispatched); the reasoning happening inside a single long generation (class 5). **Hooks cannot
  kill Claude Code tasks.** This is stated once, plainly, because every recovery proposal in §3
  is shaped by it.

## 3. Recovery, honestly bounded — and the next-best where the harness's own reach ends

Per row 436's design bar ("recovery is the point... where recovery is genuinely impossible from
hook/harness position, say so honestly AND say what the next-best is"):

| Class | Recovery reachable from hook/harness position? | Next-best |
|---|---|---|
| 1 (Bash hang) | No (a hook cannot kill an in-flight Bash call) | **Dispatch-time** Bash timeout tightened from the default 600s ceiling toward expected-duration × slack, so the hang dies in seconds as a typed failure, not silently at the ceiling. |
| 2 (API death) | No (outside this harness's surface entirely) | Orchestrator-side session-level supervision (Monitor / a fallback-wakeup discipline) watching for the same "no activity" pulse from *outside* the stalled session. |
| 3 (subagent never returns) | No (nothing reaches into an already-dispatched Task/Agent call) | The parent's own control flow — a workflow resumes from its own journal/ledger state and re-dispatches the delegation fresh, once a liveness question is raised; this is a workflow-authoring discipline this note recommends, not a mechanism this slice builds. |
| 4 (generic idle) | No (a hook cannot summon activity in a session that has gone quiet) | Same orchestrator-side Monitor/fallback-wakeup discipline as class 2. |
| 5 (legit long generation) | Deliberately **not** auto-recovered — see §0's asymmetry | Surface the liveness question, then a HUMAN (or a policy that has explicitly accepted the kill-vs-wait tradeoff for this class) decides — never an automatic kill. |

**What this harness can honestly convert a stall into, everywhere:** a stall the harness cannot
kill it can still convert from an *indefinite silent hang* into a *typed, bounded, loud signal* —
a dispatch-time timeout that fires in seconds instead of at the 600s ceiling; a journal-computed
liveness question an operator or a supervising process can read. That conversion — "silent hang"
to "loud, typed, bounded failure the workflow's control flow can route around" — is exactly
ADR-0002's fail-loud tenet applied to this failure family, and it is the honest ceiling of what a
hook-and-journal harness can do without reaching into a running model call it has no handle on.

## 4. The slice: `tools/watchdog_liveness.py`

**Why `tools/`, not `gates/`:** every file in `gates/` is a merge-time enforcement gate (exit
non-zero fails a commit); this checker is a **diagnostic** an operator runs, or a future
distance-to-clean section consumes as a read-only reporting surface — nothing here ever refuses
a commit or blocks a hook. `tools/` already holds this project's non-gate utility scripts
(`branch_attribution.py`, `merge_backlog_sections.py`, `rename_doc.py`); this fits that shelf, not
the gate one.

**What it reads, read-only, no writes anywhere:**

1. `<root>/.claude/logs/invocations.jsonl` + `bash_completions.jsonl` — Class 1.
2. `<root>/.claude/logs/delegation_observer.journal.jsonl` — Class 3.
3. Every `.claude/logs/*.journal.jsonl` (+ the two files above) present under the root — the
   generic recency pulse, Class 4/2/5 (indistinguishably, by design, per §0/§1).
4. The deployment's own ledger (`estimate:` rows + `work_item_current` — the kernel's derived
   view of each work item's live state, one of the closure-debt dimensions
   [`distance-to-clean`](../GLOSSARY.md#distance-to-clean) also reads — + the `work_claimed`
   row's own `ts`, the ledger entry the `./led work claim <slug>` operator verb writes when a
   principal claims an open work item), when a deployment (`deployment.json`) is resolvable and
   the DB is reachable — the
   **first in-flight consumer** of the `estimate:`/`actual:` WALL-CLOCK fields the commission
   named as already existing (row 433, design constraint 1): an open+claimed work item whose
   `work_claimed` row is older than its own `estimate:` row's WALL-CLOCK upper bound × slack is a
   whole-task liveness question, orthogonal to the per-dispatch checks above. **Best-effort**: a
   DB-unreachable/absent-deployment condition degrades to "SKIPPED (no deployment/DB)" — the same
   fail-soft-but-honest posture `hooks/stop_clean_exit.py` uses for its own optional checks, never
   pretended to be clean.

**Config — the `watchdog` apparatus mechanism (observe-only slice, PROPOSAL, not applied here):**
this deployment's own `.claude/apparatus.json` (never the shipped `bootstrap/templates/`
original — a concurrent merge-gated pass owns that file and this build does not touch it) is read
for `mechanisms.watchdog`, with an all-defaults-if-absent posture (this checker never refuses to
run for want of config):

```json
"watchdog": {
  "mode": "observe",
  "default_slack_ratio": 10.0,
  "default_slack_absolute_s": 1.0,
  "idle_warn_s": 300,
  "classes": {
    "bash":     {"expected_s": 0.1,  "slack_ratio": 10.0, "slack_absolute_s": 1.0},
    "subagent": {"expected_s": 60.0, "slack_ratio": 3.0,  "slack_absolute_s": 30.0}
  }
}
```

This mirrors the maintainer's own worked example exactly (row 433: "a 0.1s-class command gets
~1s leeway") — `expected_s * slack_ratio + slack_absolute_s` for the bash default is
`0.1 * 10 + 1 = 2s`, a few-second leeway on a sub-second command, not the 600s ceiling. Every
number is end-user configurable, per the commission's own hard constraint; `slack_ratio` and
`slack_absolute_s` both apply (additively) rather than forcing a choice between ratio-only and
absolute-only framing, per row 433's "slack as ratio or absolute, per the maintainer's example" —
an operator who only cares about one sets the other to 0.

**The `mode` field is presently INERT — stated plainly, not left as a silent lying signature
(tracker item `watchdog-mode-field-inert`, read via `./led show 503`; ADR-0002 Rule 4).** The example block above carries
`"mode": "observe"` because that is the only rung the escalation ladder (design constraint 4,
row 433) names that this build actually implements — `load_watchdog_config()` in
`tools/watchdog_liveness.py` does not read a `mode` key at all, and the checker always runs its
full observe-rung sweep regardless of what (if anything) `mode` is set to. This is honest, not an
oversight left unnamed: this commission is scoped to the observe rung only (`./led show 433`'s
own deliverable, "the smallest honest implementable slice"); a `warn` rung (surfacing a liveness
question at the next hook event / `pickup`, design constraint 4's second ladder step) and an
`enforce` rung do not exist yet, so there is nothing for `mode` to meaningfully select between —
wiring it now would mean validating a field with exactly one live value, which is over-machinery
for what the field currently is. When a `warn` rung is built, `mode` gains real read/dispatch
logic and this paragraph is superseded by dated amendment, not silently dropped. Until then, an
operator who sets `mode` to anything else sees no different behavior — this is the fact this
paragraph exists to name plainly, per the tracker item's own two disposition options (`./led show
503`: "wire mode up when the warn rung is built, or amend sec-4 to state plainly that mode is
presently inert") — this paragraph takes the second option.

**Output wording, load-bearing (§0):** every per-class and per-surface finding prints as
`LIVENESS QUESTION: <surface> has shown no observable activity for <elapsed> against an expected
<expected>x<slack> -- look here.` -- never `STALE`, `HUNG`, or `DEAD` as a bare verdict. A quiet
surface prints `quiet` with the same elapsed-vs-expected numbers shown, so an operator can see the
margin, not just a boolean.

**Exit code:** `0` if nothing crosses its threshold, `1` if at least one liveness question is
raised — scriptable for an operator's own polling loop, but this is a diagnostic exit code, not a
gate: nothing in this project's commit/merge path calls this file, and nothing here ever prints
`decision: block` the way a Stop hook would.

**Demonstrated run** (WITNESSED — real output, reproduced verbatim 2026-07-18 from the fixtures
the commit carries at `seen-red/watchdog-liveness/fixtures/`, re-captured after the subagent
detector's `tool_use_id`-pairing fix and the per-class-slack-default fix, both described in
`seen-red/watchdog-liveness/run_fixtures.py`'s own docstring; see §6). The transcript below is
unchanged by the later `tool_use_id`-join fix to the Bash side (this same date, per
`design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md`) — `quiet`/`stale` now also carry a `tool_use_id` on
their existing Bash dispatch lines and `stale` gained one additional, PAIRED Bash
dispatch+completion (`tu-stale-bash-paired-1`) proving the fix directly: a completed Bash
dispatch now reads quiet (absent from output entirely) rather than perpetually open. Two more
fixture roots (`mechanism-dead-fires`, `mechanism-dead-below-threshold`) cover the M2 tripwire
both-polarity; see §6:

```
$ python3 tools/watchdog_liveness.py --root seen-red/watchdog-liveness/fixtures/quiet --now 2026-07-13T12:00:10Z
=== BASH DISPATCHES ===
quiet: 1 open dispatch(es), 0 liveness question(s)
  - a1b2c3d4: elapsed 1.5s vs expected 0.1s x10.0 +1.0s -- within slack, quiet
=== SUBAGENT DISPATCHES ===
quiet: 1 open dispatch(es), 0 liveness question(s)
  - sess-qui: elapsed 5.0s vs expected 60.0s x3.0 +30.0s -- within slack, quiet
=== SURFACE RECENCY (all journals) ===
quiet: most recent event 1.5s ago (warn at 300s)
=== WORK ITEMS (ledger, best-effort) ===
SKIPPED (no deployment.json under --root; ledger check not run)
--- verdict: 0 liveness question(s) raised ---
$ echo $?
0

$ python3 tools/watchdog_liveness.py --root seen-red/watchdog-liveness/fixtures/stale --now 2026-07-13T12:10:00Z
=== BASH DISPATCHES ===
LIVENESS QUESTIONS RAISED: 1 open dispatch(es), 1 liveness question(s)
LIVENESS QUESTION: bash dispatch b2c3d4e5 has shown no observable activity for 596.0s against an
  expected 0.1s x10.0 +1.0s -- look here.
=== SUBAGENT DISPATCHES ===
LIVENESS QUESTIONS RAISED: 1 open dispatch(es), 1 liveness question(s)
LIVENESS QUESTION: subagent dispatch sess-sta has shown no observable activity for 600.0s against
  an expected 60.0s x3.0 +30.0s -- look here.
=== SURFACE RECENCY (all journals) ===
LIVENESS QUESTION: no journal in this deployment has recorded an event for 570.0s (warn at 300s)
  -- look here.
=== WORK ITEMS (ledger, best-effort) ===
SKIPPED (no deployment.json under --root; ledger check not run)
--- verdict: 3 liveness question(s) raised ---
$ echo $?
1
```

(The stale fixture's `SURFACE RECENCY` elapsed, 570.0s, differs from the `BASH DISPATCHES` elapsed,
596.0s, because the two surfaces now genuinely disagree on "most recent event" — the subagent
journal's own most recent timestamp, `2026-07-13T12:00:30Z` on the paired return line, is 30s
later than the stale bash dispatch's `2026-07-13T12:00:04Z`, so the whole-deployment recency pulse
correctly reports the LATER of the two, not a single surface's own number. This is the intended
behavior of §1 Class 4's "generic pulse across every journal," not a discrepancy.)

## 5. Template wiring — PROPOSAL only, not built here

`bootstrap/templates/` is under a concurrent merge-gated pass (this commission's own "do not
touch" list) — nothing below is applied; it is left here as a reviewable proposal for that pass
or a follow-up:

- **`pickup.tmpl`**: a `### SECTION: WATCHDOG` following the existing `ESTIMATES` section,
  calling `tools/watchdog_liveness.py --root <dep root> --json` (a `--json` output mode this
  slice does not yet build, named honestly as the one gap between "operator-runnable today" and
  "distance-to-clean-consumable tomorrow") and rendering its liveness questions the same
  never-silently-dropped way `resources()`/`estimates()` already do.
- **`distance-to-clean.tmpl`**: a `WATCHDOG` section mirroring the existing `DOC-ATTESTATION`
  section's own apparatus-gated posture exactly — `DOC-ATTESTATION` is `distance-to-clean.tmpl`'s
  existing section that counts a document's ADR-0017 A:B:C attestation as debt only when its
  own switchboard entry is turned on (design/ORCH-SPEC-ABC-OFFERING.md §4 is where that posture
  is specified). This proposal counts a `WATCHDOG` finding only when `mechanisms.watchdog.mode`
  is `"observe"` (never `"off"` by default, the same adoption-not-cost reasoning `DOC-ATTESTATION`
  already established under its own `mechanisms.doc_attestation` apparatus-config key — the same
  section, `doc_attestation` its config-key spelling, `DOC-ATTESTATION` its section-heading
  spelling), contributing its liveness-question count to the section's own subtotal,
  never to the existing `TOTAL` line without an explicit maintainer decision to fold a genuinely
  different kind of debt (a liveness question, not a governance-cleanliness debt) into the same
  number.
- **`apparatus.json`** (the shipped template default): add the `watchdog` block above, `mode:
  "off"` by default — same "a workflow you adopt by choice" reasoning `DOC-ATTESTATION`
  (`mechanisms.doc_attestation`) already uses, since a deployment that has not opted into this
  discipline should see no new debt for it.

## 6. Fixture and gate registration

`seen-red/watchdog-liveness/` carries `run_fixtures.py`, both polarities, against synthetic
journal files (no DB, no real Claude Code session) — registered in `gates/fixture_census.py`'s
`REGISTRY` as `"watchdog-liveness": "seen-red/watchdog-liveness/run_fixtures.py"`, with a banked
`red.txt` (a captured run of the checker's own output BEFORE `tools/watchdog_liveness.py` existed
— i.e. before this pass, nothing at all would have flagged the stale fixture; that absence, and
the checker's own current output on the same fixture, are both captured in `red.txt` as the
before/after pair) satisfying `fixture_census.py`'s presence check.

## 7. The policing boundary — one line, not a section (row 436's correction)

A watchdog breach is a liveness signal — a look-here — never an estimate violation; the
`estimate:`/`actual:` never-cost-policing invariant (design/USER-RETROSPECTIVE-RECIPE.md §6)
stands completely untouched by this note, which is why this is one line and not its own section —
row 436 corrected exactly the over-building of this boundary as the note's frame, and this note
does not repeat that mistake.

## Related

(This note's house convention: every law/ADR and design-doc citation used inline by number or
name — e.g. "ADR-0013 Rule 5", "ADR-0002's fail-loud tenet" — is linked exactly once, here.)

- `./led show 433` / `436` / `439` — the opening commission, its correction, and the mid-build
  false-positive scope addition, all read in full before this note.
- [law/adr/0002-fail-loudly.md](../law/adr/0002-fail-loudly.md) — the loudness hierarchy this
  note's "convert a silent hang into a typed, bounded failure" move instantiates.
- [law/adr/0013-execution-integrity.md](../law/adr/0013-execution-integrity.md) —
  Rule 5 (verify the artifact) governs this note's own worked-run demonstrations (§4): the
  commands shown were actually executed, not narrated.
- [law/adr/0017-the-zero-context-reader.md](../law/adr/0017-the-zero-context-reader.md) —
  names the A:B:C attestation §5's `DOC-ATTESTATION` proposal counts as debt, and is the
  discipline this note itself is written to (a fresh-context A:B:C attestation for this note's
  own content is recorded in
  [attestations/doc-legibility-attestations.jsonl](../attestations/doc-legibility-attestations.jsonl)).
- [design/USER-RETROSPECTIVE-RECIPE.md](USER-RETROSPECTIVE-RECIPE.md) §6 — the `estimate:`/
  `actual:` grammars this checker's whole-task check (§4 item 4) consumes, and the
  never-policing invariant §7 restates in one line.
- [design/ORCH-SPEC-ABC-OFFERING.md](ORCH-SPEC-ABC-OFFERING.md) §4 — specifies the
  apparatus-gated, adoption-not-cost posture `DOC-ATTESTATION` uses, which §5's `WATCHDOG`
  proposal mirrors.
- `hooks/stamp_intercept.py`, `hooks/posttooluse_bash_completion.py`,
  `hooks/pretooluse_delegation_observer.py`, `hooks/stop_clean_exit.py` — the detection positions
  §2 enumerates and §4's checker reads the journals of, unmodified.
