# ORCH-RCA-PAIRING-KEY-DIVERGENCE — why Bash dispatch/completion pairing never once succeeded

- **Status:** Root-cause analysis (RCA) + buildable recommendation. This document diagnoses; it deliberately does NOT
  ship the fix. A builder executes §6 in a worktree afterward.
- **Commission:** maintainer-granted Fable consult (a named, rare exception to the standing
  "Fable is off limits" policy, 2026-07-13), commissioned after `tools/watchdog_liveness.py`
  (branch `watchdog-liveness-harness`, commit f382b63) was run for the first time against the
  `~/ent` deployment's real journals and produced roughly two thousand false "still open"
  liveness questions. Mid-commission the maintainer added one instruction, honored in §8: run
  the hack-rationalization detector on this document's own recommendation, with ADR-0000 as the
  lens, and hold the (a) answer to "impossible to construct," not "less likely to diverge."
- **Discipline applied:** this RCA is itself an instance of
  [law/adr/0000-the-alpha-and-the-omega-type-driven-design.md](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)
  Rule 2 — the two questions ((a) what type forecloses the class, (b) what operational lapse let
  it recur) are answered in §4 and §5 *before* any fix is specified, and the class is named with
  the closure statement the 2026-07-02 amendment requires.
- **Evidence sources (all read-only, per the commission's hard constraint):**
  `hooks/stamp_intercept.py` and `hooks/posttooluse_bash_completion.py` (read in full, untouched);
  `~/ent/.claude/logs/invocations.jsonl`, `bash_completions.jsonl`, and
  `mutation_observer.journal.jsonl` (read-only; a live session may run there — nothing under
  `~/ent` was written); a live payload capture in this session's scratchpad (§3); the official
  Claude Code hooks reference (§3); `seen-red/bash-completion/` and the journal consumers under
  `engine/` and `tools/` (as of worktree base fca1100).

## 0. What the two hooks are, for a reader who has seen neither

Claude Code fires a **PreToolUse** hook just before a tool call runs and a **PostToolUse** hook
just after it completes. In this project:

- `hooks/stamp_intercept.py` (PreToolUse on Bash) mints a per-invocation UUID ("token") and
  journals one dispatch line per stamped Bash call to `<world>/.claude/logs/invocations.jsonl`:
  `{token, wall_clock, session_id, command_sha256, command_head, tool_use_id?, cwd}`. It ALSO
  rewrites the command itself (details in §2 — this is the crux).
- `hooks/posttooluse_bash_completion.py` (PostToolUse on Bash) journals one completion line per
  Bash call to `<world>/.claude/logs/bash_completions.jsonl` and tries to pair it back to its
  dispatch line. Its documented PAIRING RULE: compute `command_sha256` of the command text the
  PostToolUse payload carries, FIFO-match the earliest unpaired dispatch line with the same hash;
  a match yields `pairing: "token"`, a miss falls back to `pairing: "ts-only"` (`token: null`).

Downstream consumers of the pairing: `tools/watchdog_liveness.py` (dispatch lines with no paired
completion read as "possibly still open"), and `engine/contemp_edb.py`'s E5 family
(`invocation_completed(Token,T)` is emitted **only** from `pairing == "token"` records —
`contemp_edb.py:164-168`).

## 1. The symptom, witnessed

Recounted directly from `~/ent`'s journals during this consult (2026-07-14). The commissioning
session — the orchestrating Claude session driving this repository's work, whose commission text
opened this consult — had measured 1944/2054/zero on 2026-07-13; the deployment had grown
slightly by the time of this recount, same shape:

| Measure | Value |
| --- | --- |
| dispatch lines in `invocations.jsonl` | 2056 (1977 unique `command_sha256`) |
| completion lines in `bash_completions.jsonl` | 2093 (2093 unique `command_sha256` — every completion hash globally unique) |
| hash overlap between the two sides | **0** |
| completion lines with `pairing: "token"` | **0** of 2093 |
| completion `command_head`s beginning `export PGOPTIONS` | 2093 of 2093 |
| dispatch lines carrying `tool_use_id` | 2056 of 2056 |

So: the FIFO-by-hash match has never succeeded once in this deployment's entire history. Every
completion ever journaled is the "honest fallback." Consequences already landed before anyone
noticed: `watchdog_liveness.py` raised ~2000 false liveness questions on its first real run, and
`contemp_edb.py`'s E5 fact family has been **empty in every deployment since the hook shipped**
(its capability line reads "wired" while producing zero facts, so nothing downstream flagged it).
`ORCH-CAPABILITIES.md:863-871` describes the pairing as working ("`pairing: \"token\"`,
`duration_ms` included") — a doc claim that was never witnessed against a live deployment.

## 2. Root cause, in the code

Three facts compose; each is quoted from the current source.

**Fact 1 — the dispatch side hashes the ORIGINAL command text.**
`hooks/stamp_intercept.py:437-444`:

```python
    command_bytes = command.encode("utf-8", "surrogatepass")
    inv_rec = {
        "token": invocation,
        ...
        "command_sha256": hashlib.sha256(command_bytes).hexdigest(),
```

where `command` is the model-authored text straight from the PreToolUse payload (line 390).

**Fact 2 — the same hook then REWRITES the command the harness actually runs.**
`hooks/stamp_intercept.py:464-468`:

```python
    new_command = f"export PGOPTIONS={shlex.quote(pgopts)}; {_neutralize_pgoptions(command)}"
    out = {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "updatedInput": {**(data.get("tool_input") or {}), "command": new_command},
```

and `pgopts` (lines 430-432) embeds the per-session id, a per-second `ts`, the per-session HMAC,
and — decisively — the freshly minted per-invocation `uuid4`.

**Fact 3 — the PostToolUse payload carries the REWRITTEN command, and the completion hook hashes
that.** Witnessed twice: (i) `~/ent/.claude/logs/mutation_observer.journal.jsonl` (a PostToolUse
sibling hook that journals the command verbatim) records commands beginning
`export PGOPTIONS='-c app.vendor_session=... -c app.vendor_invocation=...'; cd /home/bork/ent && ...`;
(ii) all 2093 completion `command_head`s begin `export PGOPTIONS` (§1). The completion hook then
hashes exactly what it was handed — `hooks/posttooluse_bash_completion.py:224-226`:

```python
        command = str((data.get("tool_input") or {}).get("command", ""))
        command_bytes = command.encode("utf-8", "surrogatepass")
        command_sha256 = hashlib.sha256(command_bytes).hexdigest()
```

**Composition.** In a wired world, PreToolUse hashes pre-rewrite text; PostToolUse hashes
post-rewrite text; the two are never equal for any command. Worse than "sometimes misses": the
injected prefix embeds a fresh `uuid4` per invocation, so every completion hash is globally
unique (2093 of 2093, §1) — the match probability is exactly zero **by construction**, not
degraded. And in an *unwired* world, `stamp_intercept` journals nothing, so there are no
dispatch records to pair against at all. There exists no world in which the documented pairing
can succeed. The mechanism was dead at birth.

The completion hook's own docstring states the false premise verbatim (lines 68-72):

> PostToolUse's own `tool_input.command` is ASSUMED to echo the same text stamp_intercept's
> PreToolUse leg saw (both hash the command BEFORE any hook-side modification) — if a future
> Claude Code version diverges on this, the sha256 match degrades gracefully...

The assumption was not broken by "a future Claude Code version"; it was false on day one, and
the modifier is not some third party — it is **the very hook whose journal this one pairs
against**. The author of the pairing rule read `stamp_intercept.py` closely enough to cite its
docstring, and that file's most prominent feature — it rewrites every Bash command — is the
mechanism that defeats the pairing.

Two secondary defects ride along: the completion-side `command_head` (first 120 chars) lies
entirely inside the injected prefix, so it identifies nothing; and the graceful-degradation
claim above is only half true — the fallback IS honest per line, but "gracefully" concealed a
100% failure rate for the mechanism's whole life (§5, lapse 3).

## 3. Is `tool_use_id` actually available to both hooks? Checked, not assumed

The completion hook declined to use `tool_use_id` on the strength of this (its lines 37-39,
citing `stamp_intercept.py`'s prose, which `pretooluse_delegation_observer.py:93` repeats):

> Claude Code's own hook-input contract has never been observed to carry a `tool_use_id` this
> project could rely on either

That claim was false at the moment it was written (the hook shipped 2026-07-11; provenance stamp
lines 3-5). Three independent witnesses:

1. **Production, PreToolUse:** all 2056 of 2056 dispatch lines in `~/ent`'s `invocations.jsonl`
   carry `tool_use_id` (e.g. the very first line, 2026-07-13T13:55:37Z:
   `"tool_use_id": "toolu_01NPGzw8VqvkQ1U2LWTvchL7"`). `stamp_intercept.py:445-447` reads it
   defensively and it has been present every single time. The refuting evidence sat in the exact
   file the completion hook reads on every invocation.
2. **Live capture, both events (this consult, 2026-07-14):** a scratch project wiring a
   dump-to-file hook on PreToolUse and PostToolUse, exercised via a headless `claude -p` run.
   Observed payload keys —
   PreToolUse: `cwd, hook_event_name, permission_mode, prompt_id, session_id, tool_input,
   tool_name, tool_use_id, transcript_path`;
   PostToolUse: the same **plus `tool_response` and `duration_ms`**. The `tool_use_id` value was
   byte-identical across the pair (`toolu_0196VvcMSrebTaQBuH7PkpYe` in both).
3. **Official documentation** (https://code.claude.com/docs/en/hooks, fetched this consult):
   both events carry `tool_use_id`; the PostToolUse field is documented as "The same ID used in
   the corresponding PreToolUse event" — i.e. the harness assigns this identity **for exactly
   the correlation purpose these two hooks re-derived a hash for**.

So: **yes, the harness-assigned identity is available to both hooks**, in the same payloads they
already parse, with the pairing semantics guaranteed by the harness rather than reconstructed
from content. Bonus finding from witness 2: PostToolUse natively carries `duration_ms`, the very
quantity (start-to-finish duration of the non-null tail) the completion hook's commission named
as its reason to exist.

One honest residual: witnesses 1 and 2 observed main-thread sessions and one dispatch journal;
subagent-side PostToolUse payloads are UNWITNESSED here (the docs draw no distinction, and
subagent PreToolUse lines in ent's journal do carry `tool_use_id`, but §6 requires the fixture
to keep the absent-`tool_use_id` fallback path anyway — degrade honestly, never crash).

## 4. ADR-0000 question (a): what type forecloses the class?

**The class, named generally** (per Rule 2(a) and the 2026-07-02 closure-statement amendment —
and presumed too narrow as first named, so widened before answering): *two or more code paths
independently derive a value that is REQUIRED to agree for correlation to work, with nothing
structural preventing silent divergence.* This is
[ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md) P1 (every fact has one home;
derived quantities are computed from their source, never re-authored) violated at the level of
a **correlation key** — and it is P7's "two writers of one cross-boundary truth" with the
boundary being *time* (two observation points of one tool call) rather than language.

**Why "one shared hashing function" — the centralization answer — does NOT foreclose this
class.** It is the natural P1 reflex and it is insufficient here, which is worth recording
because it is the patch a competent contributor would reach for: both hooks already compute
byte-identical `sha256(command.encode("utf-8", "surrogatepass"))`. The implementations never
diverged — **the inputs did**. A shared function closes the implementation-drift axis and leaves
the input-drift axis (what text each observation point is handed, at what moment, after whose
mutations) fully open; the defect lived entirely on that axis. A closure statement whose
quantification universe enumerates only "the code that computes the key" and not "the input each
site observes" is the class-named-at-the-scope-of-the-fix failure the 2026-07-02 amendment
documents. Any content-derived key recomputed at two times has this hole structurally.

**The foreclosing answer is identity elimination, not derivation hygiene.** The harness — the
single authority that knows two hook firings belong to one tool call — already assigns that fact
a name: `tool_use_id`, present in both payloads, documented for exactly this purpose (§3). Key
the correlation on it. Then there are **zero derivations**: neither hook computes anything; both
transport an identity minted once by the one party positioned to mint it. Nothing is derived, so
nothing can disagree — the illegal state "the two sides computed different keys for one call" is
not caught, not guarded against, but **unrepresentable**: there is no longer a sentence in which
two keys for one call can be written. (This is the derive-from-the-one-meaningful-source
move of ADR-0000's Specimen 3, the byte-budgeted queue bound: the "resource that actually
detonates" here is *call identity*, and a content hash is a proxy currency for it — the denomination check fails for any content hash and passes only for
the harness's own identity.)

**And the stored verdict goes too.** The current completion record *stores* a pairing claim
(`pairing: "token"/"ts-only"`, `token`, `dispatch_wall_clock`) computed at write time — a cached
join result, which is precisely the second copy of a derivable fact P1 forbids, and it is how
2093 records came to assert "no dispatch matches" while 2056 matching dispatches sat in the
sibling file. The maintainer's bar for this consult — *an inconsistent database should not even
be constructable* — is met by removing the stored claim, not hardening it: each journal records
only facts local to its own event (**the completion line carries `tool_use_id` and stops
carrying `token`/`pairing`/`dispatch_wall_clock` entirely**), and pairing becomes a **derived
view** — a join on `tool_use_id` computed by whoever reads (watchdog, contemp_edb). A join
cannot be inconsistent with its inputs; a stored verdict can. There is then no write anyone can
perform, buggy or adversarial, that constructs a false pairing record, because pairing records
no longer exist as writes.

**Closure statement** (invariant / universe / denomination, per the amendment):

1. **Invariant:** any two records claiming to describe the same tool call are keyed by the
   harness-assigned `tool_use_id` transported from that call's own hook payloads; no correlation
   key in this project is re-derived from observed content at more than one observation point,
   and no pairing verdict is stored where it can instead be derived by join.
2. **Quantification universe — axes:** implementation drift (two hash functions), input drift
   (same function, different observed text — the axis this defect lived on: hook-side
   `updatedInput` rewriting, encoding, whitespace, truncation), time-of-observation, and
   concurrency (duplicate command text in flight defeats ANY content key — the FIFO "named
   residual gap" dissolves under an identity key rather than being disclosed).
   **Universe — sibling surfaces**, checked outward before writing this: (i)
   `hooks/pretooluse_delegation_observer.py` pairs subagent dispatch/return lines by its own
   content-hash FIFO heuristic and repeats the same false `tool_use_id` prose at its line 93 —
   same class, second live instance, named here as IN the class; its failure SHAPE differs and
   the difference is stated so severities are not conflated (out-of-frame audit finding,
   2026-07-14): its pairing is a live, partially-working heuristic (witnessed 51 of 103
   `fifo_prompt_sha256` pairings succeeding in `~/ent`'s journal) with a statistical collision
   risk, NOT the dead-by-construction 0% this RCA diagnoses — no command rewrite defeats it.
   Lower urgency, same class, filed per §6.6; (ii)
   `stamp_invocation` (ledger) ↔ `token` (journal) correlate by transporting one minted UUID
   through PGOPTIONS — that one is already identity-shaped, not re-derived: compliant; (iii)
   `engine/contemp_edb.py` E4/E5 and `tools/watchdog_liveness.py` are consumers of these keys,
   covered by §6; (iv) any FUTURE pairing convention — covered by mechanism M1/M3 in §5, since a
   type cannot bind files not yet written.
3. **Denomination check:** the key is denominated in the harness's own call identity — the one
   currency that actually individuates a tool call — never a proxy for it (a hash of command
   text is a proxy that collides on repeats and diverges on rewrites; a wall-clock window is a
   proxy that fails under concurrency).

## 5. ADR-0000 question (b): the operational lapse, and the mechanisms

Question (b) is aimed at the executive, not the implementer (Rule 2(b) verbatim), and this
project's law had, remarkably, already codified the exact rules whose absence-in-practice let
this ship — the 2026-07-02 amendments of
[ADR-0011 (mechanization discipline)](../law/adr/0011-mechanization-discipline.md) predate the
hook by nine days. The lapse is that
they were not applied to this fix, and nothing mechanical made them apply. Three strands:

**Lapse 1 — the two-party contract was witnessed single-party (a shipped-binding violation,
ADR-0011 Rule 3 as amended).** A both-polarity fixture exists and passes:
`seen-red/bash-completion/run_fixtures.py`, whose case `a-token-pairing` is green in
`seen-red/bash-completion/red.txt`. But the fixture *authors the dispatch side by hand* from the
completion hook's own assumption — its `append_invocation()` (lines 67-73) hashes raw command
text into a synthetic dispatch record, and `run_hook()` feeds the same raw text to the
completion hook. The real dispatcher, `stamp_intercept.py`, is never executed; its command
rewrite therefore never enters the test. The docstring says "Real infra, no mocks" — and the
counterparty of the contract under test is a mock in the one respect that matters. This is
exactly the shape of CB-33 — a canonical bug from the fact-mining recidivism study, quoted and
sourced in the provenance note of ADR-0011's 2026-07-02 Rule-3 amendment, where a gate sat
"green while measuring a NON-SHIPPED encode backend... worse than no gate: it launders the
claim" — the gate here likewise was green on a configuration production never runs. A pairing
contract's positive case proves nothing unless **every producer in the pair is the real shipped
code, run in its real sequence** (the Pre hook's actual `updatedInput` output becoming the Post
hook's actual input, as the harness would wire them).

**Lapse 2 — an environment fact was cached as prose, propagated, and never re-verified against
the evidence at hand.** "The hook contract has never been observed to carry a `tool_use_id`"
was written into `stamp_intercept.py`, copied into `posttooluse_bash_completion.py` and
`pretooluse_delegation_observer.py`, and used as the load-bearing reason to reject the identity
key — while every line of the journal the completion hook reads on every invocation refuted it
(§3, witness 1). This is ADR-0012 cancer G (load-bearing knowledge in unenforceable prose) plus
B (the same claimed fact re-authored in three files), applied to facts about the harness rather
than facts in the code. Prose cannot be re-verified; a fixture can.

**Lapse 3 — per-event honesty aggregated into silent total failure, and nothing watched the
aggregate.** Each `ts-only` line is individually honest — the design praised itself for exactly
that, correctly. But a fallback that is honest per event carries no signal about its own rate,
and a 100% fallback rate is not a degraded mechanism, it is a dead one wearing an honest label.
No tripwire existed on "the primary path has never once fired." The failure was discovered only
when a NEW consumer (the watchdog) tripped over its consequences — the
invisible-at-authoring, visible-only-in-aggregate defect ADR-0011's Context names, in the
project's own instrumentation.

**Mechanisms** (ADR-0000 Rule 2(b) discharges through ADR-0011 Rule 2: a recurrence converts to
a mechanism, not more prose — and per ADR-0011's
2026-07-02 "mechanism ships WITH the first fix" tightening, §6 makes M1 and M2 part of the fix's
definition of done, not follow-ups):

- **M1 — the counterparty rule for pairing fixtures (test/CI gate).** M1 is a grep-able
  convention, stated in the fixture template and enforced by review plus the fixture itself: *a
  fixture whose
  subject is a correlation/pairing contract between N producers executes all N real producers in
  their real sequence for its positive case; a hand-authored stand-in for a counterparty is
  permitted only in negative/fallback cases.* Concretely here: the rewritten fixture (§6.4)
  runs the real `stamp_intercept.py`, captures its actual `updatedInput` and journal line, and
  feeds them onward — so the defect class this RCA names turns the fixture red on the pre-fix
  tree (the negative-control leg ADR-0011 already mandates: §6.4 requires witnessing that red).
- **M2 — a dead-mechanism tripwire (run-time diagnostic, watchdog-side).** Any mechanism with a
  named "honest fallback" declares its expected primary-path band; `tools/watchdog_liveness.py`
  — the tool that found this — gains one check: a journal whose primary pairing path has fired
  0 times against N ≥ threshold eligible events raises ONE typed finding
  ("pairing mechanism has never succeeded — mechanism-level question"), not N per-event
  questions. This quantifies over the class (any paired-journal mechanism, current and future),
  not this instance.
- **M3 — harness-contract facts live in a captured fixture, not prose (test/CI gate).** One
  small committed artifact (a captured real PreToolUse+PostToolUse payload pair, secrets/none
  present, refreshed deliberately on Claude Code version bumps) becomes the single home for
  "what the hook payload carries"; hook docstrings cite it instead of asserting contract facts
  freehand. A claim like lapse 2's would then be checkable — and would have failed — at
  authoring time. (This composes with ADR-0000 Revisit #4's registry lesson: the set of facts
  you hold yourself to must be discoverable somewhere a fresh audit actually looks.)

## 6. The buildable recommendation (for a Sonnet builder, in a worktree)

Scope discipline: items 1-5 are one commission; item 6 is the named sibling, separately
dispatchable. Nothing here touches kernel/lineage, law/, or engine/lp semantics. Do not run
against `~/ent`; all witnessing happens in scratch worlds/fixtures. Historical journals are
never rewritten (runs-are-linear: existing `ts-only` lines are settled evidence of the pre-fix
era, not data to repair).

**6.1 `hooks/posttooluse_bash_completion.py` — key on `tool_use_id`; stop storing verdicts.**
- Read `tool_use_id` from the payload (`data.get("tool_use_id")`, defensively, same posture as
  `stamp_intercept.py:445-447`).
- The completion record becomes facts-local-to-this-event only:
  `{ts, session_id, tool_use_id, duration_ms?, command_sha256, command_head}` — where
  `duration_ms` is copied from the payload when present (§3 witness 2; omit when absent), and
  `command_sha256`/`command_head` are RETAINED but re-documented honestly as "of the
  as-executed (post-rewrite) text this payload carried" — they are event facts, no longer
  correlation keys. **Drop `token`, `pairing`, and `dispatch_wall_clock` from new lines**; the
  whole `_find_pairing()` read-back of both journals goes with them (the hook stops reading
  anything — cheaper AND correct).
- When the payload carries no `tool_use_id`: journal the line without it. No guessed pairing,
  ever. (The one behavior preserved from the old design is its honesty about absence.)
- Rewrite the module docstring's PAIRING RULE and NAMED RESIDUAL GAPS sections: pairing is now a
  read-time join on `tool_use_id`; delete the false "never been observed to carry a
  tool_use_id" claim and the false "both hash the command BEFORE any hook-side modification"
  premise; cite the M3 fixture. The concurrent-identical-command residual gap is deleted — it
  does not exist under an identity key.

**6.2 `hooks/stamp_intercept.py` — near-null change.** It already journals `tool_use_id` on
every dispatch line. Only its docstring's "the parsed stdin contract has never carried one"
sentence (lines 87-89, 435-436) is corrected to cite the M3 fixture. (Its own hash of the
pre-rewrite text stays: on the dispatch side, `command_sha256`/`command_head` describe what the
model authored — a useful event fact with one writer and no agreement obligation.)

**6.3 Consumers.**
- `engine/contemp_edb.py` E5: `invocation_completed` currently keys on the completion line's
  `token`. New derivation: join completion `tool_use_id` → dispatch line's `tool_use_id` → that
  dispatch's `token` (the ledger-side correlate, `stamp_invocation`, is unchanged). Old-era
  lines (token-less, `pairing: "ts-only"`) contribute nothing, exactly as today. Keep the
  capability line, but its `produced` flag now actually goes true in wired worlds — witness
  that in the fixture.
- `tools/watchdog_liveness.py`: pair dispatch↔completion on `tool_use_id`; implement M2 (one
  typed mechanism-dead finding at zero pairing rate over threshold N, replacing per-event noise);
  treat pre-fix-era journal lines (no `tool_use_id` on the completion side) as a named era, not
  as open questions.
- Update `ORCH-CAPABILITIES.md:862-871` to describe the identity join, removing the FIFO/hash
  description and its "duration_ms included" claim in favor of what a witnessed run actually
  shows. Check `design/ORCH-CONTEMPORANEITY-PART3-SPEC.md`'s E5 row and
  `bootstrap/templates/APPARATUS.md` for the same stale description.

**6.4 `seen-red/bash-completion/run_fixtures.py` — the M1 counterparty rewrite.** The positive
case becomes a real two-party sequence: build a scratch wired world (deployment.json + seeded
scratch secret, as `seen-red/31-interception-stamp` already does for stamp_intercept), run the
REAL `stamp_intercept.py` on a PreToolUse payload carrying a `tool_use_id`, take the
`updatedInput.command` from its stdout and the dispatch line it journaled, then feed the REAL
completion hook a PostToolUse payload carrying that rewritten command and the same
`tool_use_id`; assert the read-time join (run the actual consumer-join code, not a reimplemented
join) yields exactly one pair with the dispatch's token. Negative controls, both mandatory:
(i) the same two-party positive case run against the PRE-FIX completion hook must go red
(witness the red — this is the negative-control leg that proves the fixture would have caught
this defect); (ii) a completion payload with no `tool_use_id` journals a line and pairs to
nothing. Keep the existing off/enforce-downgrade/non-bash/unwired cases.

**6.5 M3 fixture.** Commit the captured payload-pair artifact (from a scratch headless run, as
performed in this consult; scrub `transcript_path`/user-identifying paths) under
`seen-red/hook-payload-contract/` with a tiny checker asserting the fields hooks rely on
(`tool_use_id` in both events, `tool_input.command`, `duration_ms` in Post) are present; wire it
beside the other seen-red fixtures.

**6.6 Named sibling (separate dispatch, same class, MUST be ledger-filed):**
`hooks/pretooluse_delegation_observer.py` pairs delegation dispatch/return with its own
content-hash heuristic (live but partial — 51/103 witnessed pairings, see §4) and repeats the
false `tool_use_id` claim at line 93. Apply the same two-question treatment there before
touching code; do not fold it into this build silently. **A prose deferral in this document is
not a filed deferral** (BACKLOG.md is retired; deferred work lives in the tracker ledger —
`led` is this project's tracker-ledger operator verb, documented in `ORCH-CAPABILITIES.md`, and
`./led work open` files a new deferred work item as a queryable row): a
`./led work open` row for this sibling is part of THIS recommendation's definition of done, so
the deferral is discoverable by someone who never reads this file. The out-of-frame audit
(companion file, §8) confirmed no such row existed as of 2026-07-14.

**Definition of done** (per ADR-0011's mechanism-ships-with-first-fix): 6.1-6.5 land together;
the fixture's negative control was seen red against the pre-fix hook; a scratch wired world
shows `pairing rate > 0` end-to-end via the real consumer join; every claim in the builder's
report is WITNESSED / REFUSED-AS-EXPECTED / UNEXERCISED-with-blocker.

## 7. Hazards and ambiguities surfaced, not resolved here

1. **The ent deployment's ~2000-line pre-fix journal era.** Settled evidence, never patched.
   Whether the watchdog should report that era as one named "pre-identity-key era" line or stay
   silent about it is a small judgment call left to the builder's commission (6.3 assumes the
   named-era reading).
2. **Subagent-side PostToolUse payloads are UNWITNESSED** for `tool_use_id` (§3). The fallback
   path (6.1) makes this safe either way; the M3 fixture should add a subagent capture when one
   is conveniently obtainable.
3. **Completion/dispatch count asymmetry (2093 vs 2056)** persists by design: the completion
   hook journals every Bash call, the dispatch hook only stamped ones. M2's rate must be
   computed against *eligible* (dispatch-carrying) events, or it will false-alarm on
   lightly-wired worlds.
4. **This worktree's base is stale** (fca1100; does not contain `next`'s tip ce1f501, nor the
   watchdog branch f382b63 — read via the object store). This document is a new standalone file
   and merges cleanly, but §6's line references to `watchdog_liveness.py` describe f382b63 and
   should be re-verified against wherever that branch has landed by build time.
5. **ADR-0000's own Exceptions clause cites a retired artifact.** Exception #2 ("filed where
   deferrals live (`BACKLOG.md`)") points at BACKLOG.md, retired 2026-07-12 in favor of the
   tracker ledger — so the law's letter currently names a dead filing target (out-of-frame
   audit finding, 2026-07-14). law/ changes are maintainer-ratified only; flagged here, not
   fixed.
6. **`ORCH-CAPABILITIES.md` carried an unwitnessed working-as-designed description** of this
   mechanism (§1). That is a doc-discipline miss adjacent to, but distinct from, lapse 1; it is
   fixed by 6.3's doc update, and it is worth the maintainer knowing the "claims carry
   witnesses" rule was the last net that could have caught this and didn't — the doc's claim was
   copied from the design, not from an observed run.

## 8. Adversarial self-check (maintainer's mid-commission instruction)

The hack-rationalization detector was run OUT OF FRAME (a fresh auditor subagent that had not
seen this document's authoring context) over this document's own recommendation with ADR-0000 as
the lens before it was finalized. Per that skill's return-path rule the auditor's artifact
travels verbatim, never summarized: it is committed beside this file as
[ORCH-RCA-PAIRING-KEY-DIVERGENCE.audit.md](ORCH-RCA-PAIRING-KEY-DIVERGENCE.audit.md) —
verdict `narrower-but-justified` with one undischarged residual (the §6.6 deferral was
prose-only, i.e. narrated rather than filed), all four findings accepted and folded back into
§4, §6.6, and §7 before this document was finalized. The two questions the pass held the
recommendation to:
does §4 foreclose the class or merely relocate the derivation (answer: forecloses — zero
derivations remain, and the stored-verdict removal makes a false pairing record unwritable, the
maintainer's own bar); and does §6 quietly narrow the class back to these two files (answer:
M1/M2/M3 quantify over pairing contracts as a class, and §4's universe names the one known
sibling instance rather than absorbing or ignoring it).
