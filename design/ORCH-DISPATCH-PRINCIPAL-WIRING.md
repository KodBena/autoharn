# Dispatch-principal wiring — the LED_ACTOR convention for builder identity

This note is for an orchestrator (human or agent) that dispatches a builder — via Claude
Code's Agent/Task tool — to work on one item from this project's ledger (its append-only
decision/audit log, read via the `./led` command-line tool). It answers one question: how does
a dispatched builder's own ledger writes get attributed to THAT builder specifically, rather
than to the shared default identity every session writes as unless told otherwise, so that a
segregation-of-duties check (a rule requiring a review to come from someone other than the
writer) has a real distinct actor to check against?

**Status: Sonnet-built 2026-07-26, work item `dispatch-principal-wiring` (ledger row 1356
claim). Investigate-then-build item; no kernel/lineage, law/, or serving-layer change made or
needed — this note plus `tools/dispatch_principal.py` are the whole deliverable. Amended
2026-07-26 by a documented FIX ROUND: an independent code review of the first version of this
note and `tools/dispatch_principal.py` reported a **BLOCKS-MERGE verdict** — this repository's
label for a review finding severe enough that the change may not be merged until every finding
is addressed — with four fixable findings and one process note; every occurrence of "this fix
round" below refers to the revisions made in direct response to that review, and each is tied
to the specific finding number that motivated it.**

## The commission, restated

> Wire LED_ACTOR registered principals into every agent dispatch preamble so builder identity
> is kernel-visible and segregation-of-duties checks run on real principals, not the shared
> default author.

## Investigation finding: the mechanism already exists, in full, at the CLI/kernel layer

`LED_ACTOR` is not aspirational and not a stub — it is a live, exercised env-var convention:

- `bootstrap/templates/led.tmpl`'s `_resolve_actor()` (led.tmpl:112-126) reads `LED_ACTOR`
  from the environment. Unset: returns `None`, the payload omits `actor` entirely and the
  kernel's own default resolution applies. Set to a name that resolves against
  `GET /standing/principals` (the registered-principal machinery `kernel/lineage/
  s41-principal-bindings-and-relations.sql` added, called "s41" after that file's own numbered
  place in the kernel's ordered sequence of schema deltas): that principal's id is threaded onto the
  write's `actor` field. Set to a name that does **not** resolve: `led` REFUSES immediately
  (exit 1) with `LED_ACTOR='<name>' is not a registered principal`, teaching
  `./led register-principal <name> <class>` — never a silent fallback to the default author.
- `kernel/lineage/s40-principal-identity-events.sql`'s `set_actor()` trigger (lines 551-573)
  is the enforcing home: when a write supplies no `actor`, it resolves the connection's
  `current_user` against the `principal_role` view (the DB-role → principal binding from
  `principal_standing_declared`) and marks the row `principal_actor_resolution =
  'declared-default'`. When a write DOES supply an explicit `actor` (which is exactly what an
  `LED_ACTOR`-set `led` invocation does), the row is marked `principal_actor_resolution =
  'explicit'`. Both values are visible in every `led show`.
- `led register-principal <name> <class>` and `led principal declare-standing <name>
  [--db-role <role>]` are the two existing, working registration surfaces (no missing
  `led principal` sub-verb needed).

So: **the write path was never the gap.** `GLOSSARY.md`'s own `### principal` entry already
documents `LED_ACTOR=reviewer` as the standing selection mechanism.

## The actual gap

Nothing generates the `export LED_ACTOR=<name>` line a dispatch preamble needs, and nothing
checks — before a builder is dispatched and spends a turn on it — that the name about to be
handed to it is actually registered. `design/BACKLOG-TRIAGE-2026-07-23.md`'s own triage found
exactly one `LED_ACTOR` mention in `hooks/` (a teach-text example inside
`hooks/pretooluse_change_gate.py`'s review-debt refusal, not real dispatch wiring) and
concluded the ask was unaddressed.

Two existing precedents already wire `LED_ACTOR` into their own dispatch step, but neither
covers the general case:

- `tools/workflow_compile.py` / `tools/workflow_units/*/drive.py` set
  `env={**os.environ, "LED_ACTOR": actor}` when they subprocess-invoke `led` for a *compiled
  workflow-unit phase* — real wiring, but scoped to the workflow-unit compiler's own TOML-driven
  role map, not to an ad hoc builder dispatched via the Agent/Task tool for a single work-item
  row (the shape this ledger row itself was dispatched under).
- `design/FABLE-ROLE-CHARTERS-AND-BRIEFS-SPEC.md` describes the same idea for its own
  "compiler integration" deliverable (`--role-map`), again scoped to the compiler.

An orchestrator dispatching a one-off builder via the Agent/Task tool has no subprocess env
channel to the dispatched session at all — the "dispatch preamble" for that shape is the
**prompt text** the orchestrator writes, not an OS environment. The convention this note
establishes is for exactly that case.

## The convention

1. A dispatched builder gets its **own** registered principal, distinct from the shared
   `author` default — e.g. `builder-<work-item-slug>`, class `subagent`. Naming is the
   orchestrator's call (this note does not mint a scheme); the point is that two different
   builders dispatched to two different work items are two different principals, so
   `review_gap` (the kernel-derived SQL view `led review-gap` reads: every ledger row an
   obliged principal wrote with no distinct-actor countersign yet, GLOSSARY.md's own
   `### review_gap` entry) is checking something real instead of two sessions that both write
   as `author`.
2. Before dispatch, the orchestrator runs
   `python3 tools/dispatch_principal.py preamble builder-<slug>` from the target deployment's
   own directory. If the name is already registered, it prints
   `export LED_ACTOR=builder-<slug>` — paste that line verbatim into the dispatch
   brief/preamble as the first instruction for the builder's own shell. If not registered, the
   tool REFUSES (exit 1) and prints the exact
   `./led register-principal builder-<slug> subagent --purpose "..."` command to run first —
   registration is a real ledger write and stays the orchestrator's own deliberate act; this
   tool never performs it on the caller's behalf.
3. The dispatched builder's own `led` invocations then attribute `explicit`/`builder-<slug>`
   automatically — no further code path change, because the CLI already does this (see above).
   An unregistered or mistyped `LED_ACTOR` refuses loudly at write time exactly as it always
   did; this tool's `preamble`/`check` subcommands are a preflight in front of that refusal,
   not a second authority that could disagree with it.

## Mechanical support delivered

`tools/dispatch_principal.py` (this fix round) does the checking, CLI-side, over `./led` (or
`--led PATH`, its sole read surface, no raw SQL, same idiom as `tools/role_charter.py`) and
exposes two subcommands:

- `preamble <name>` — registered: prints `export LED_ACTOR=<name>` (shell-quoted via
  `shlex.quote`, belt-and-suspenders), exit 0. Not registered: REFUSED with the exact
  registration command, exit 1. Both subcommands first REFUSE any `<name>` outside
  `[A-Za-z0-9_-]+` (fix round finding 1, this document's own attestation history: an unquoted
  paste line built from an unconstrained name was a shell-injection hazard, e.g.
  `builder$(touch PWNED)`) before doing anything else, including talking to `led` at all.
- `check <name>` — same test, machine-readable `REGISTERED:`/`NOT-REGISTERED:` output by
  default (using Python `repr()` for the name, not hand-rolled quotes — fix round finding 4)
  or, with `--json`, one `{"name": ..., "registered": true|false}` object — for a batch
  preflight over several builder names before a wave of dispatches, or a brief-generator that
  wants to parse the result.

## Witnesses (scratch world, both polarities; see this fix round's ledger writeup for the full
transcript)

A "scratch world" is a throwaway, fully-functional deployment of this project's own ledger
machinery — a disposable copy used to test a real write/refusal without touching the actual
project ledger, torn down afterward with a verified-empty check. This one was created with
`bootstrap/new-project.sh --new-world` (the scaffolding command that births a fresh deployment
already carrying `author`/`reviewer`/`commissioner` principals and the project's current
kernel schema, "current lineage head"):

- **RED** — `LED_ACTOR=builder-nonexistent ./led decision "..."` → exit 1, `REFUSED --
  LED_ACTOR='builder-nonexistent' is not a registered principal`, teaching text naming the
  exact registration command. No row written.
- **GREEN** — after `./led register-principal builder-dispatch-principal-wiring subagent
  --purpose "..."`, `LED_ACTOR=builder-dispatch-principal-wiring ./led decision "..."` → row
  written, `led show` reports `actor: 5` (the new principal's id) and
  `principal_actor_resolution: explicit`.
- **Default-path-unchanged** — a plain `./led decision "..."` with `LED_ACTOR` unset, run both
  BEFORE and AFTER the registration above, both land as `actor: 1` (`author`),
  `principal_actor_resolution: declared-default` — byte-identical, unaffected by the
  intervening registration.
- `tools/dispatch_principal.py preamble/check` exercised against the same scratch world:
  refuses on the unregistered name, teaches the registration command; succeeds on the
  registered name, printing the exact `export LED_ACTOR=...` line; `check` reports
  `REGISTERED`/`NOT-REGISTERED` with matching exit codes.

## Composes-with, named not built

The parked `obligation-actor-type-system` item
(`design/FABLE-OBLIGATION-DEPENDENT-TYPING-SPEC.md` sec-3, "the typed-actor question... a later
amendment to the node predicate") is the natural next step once dispatched builders carry
distinct registered principals: a future Fable-authored kernel delta could type WHICH
principal/class may discharge WHICH obligation — the "NRC-certified-signer analogy": the idea,
by loose analogy to the US Nuclear Regulatory Commission's rule that only a specifically
certified individual may sign off on certain regulated actions, that only a principal of the
right TYPE should be able to discharge a given obligation, rather than any registered
principal at all. That spec's own reviewer pass — labeled "SCOUT" in that document's own
text — flagged the analogy as an open question, not yet a decided design.
This work item is what gives that future amendment real per-builder
identities to type against — it does not attempt the typing itself, which is kernel-touching
and stays Fable-spec/maintainer-ratified.

## Honest limits

- `tools/dispatch_principal.py` tests REGISTRATION only — an ANALOGOUS, BOUNDED APPROXIMATION
  of the test `led`'s own `_resolve_actor` performs server-side (corrected this fix round,
  review finding 3: an earlier draft of this note overclaimed "the SAME test"). `_resolve_actor`
  answers "does a `principal_registered` event for this name exist" against
  `GET /standing/principals`, a served, indexed, UNBOUNDED view; `tools/dispatch_principal.py`
  answers the identical QUESTION by scanning at most the most recent `--scan-limit` (default
  100000) rows of `led current N` client-side. The two views diverge exactly at scale: on a
  ledger with more than `scan_limit` rows, a registration event older than the scan window
  reads NOT-REGISTERED here while `led`'s own indexed lookup still finds it — a false-refusal
  on this preflight only, never a false-pass, and never load-bearing for correctness (the real
  write still resolves correctly either way; see `tools/dispatch_principal.py`'s own
  `principal_is_registered` docstring for the full statement). It does not duplicate the
  kernel's live suspended/revoked standing check
  (`law/adr/0012-compositional-and-structural-hygiene.md`'s principle P1,
  "single source of truth": one home for that fact, and it is the kernel's `set_actor`
  trigger). A name registered now and suspended later still passes this preflight and then
  correctly refuses at the real write.
- **Per-builder principal ACCUMULATION, undocumented until this fix round (review finding 2).**
  Every successful `./led register-principal builder-<slug> subagent` this convention drives
  is an append-only ledger write, forever — there is no retirement/supersession step in this
  convention or in `tools/dispatch_principal.py`, and neither invents one. The registry grows
  by one principal per dispatched builder, unconditionally; nothing here ever revisits or
  prunes it. When a builder's work item is done and an orchestrator wants that principal off
  its own routine attention, the SEAM is the standing-lifecycle machinery already shipped for
  every other principal: `kernel/lineage/s45-standing-lifecycle.sql`'s typed standing events,
  driven by `./led principal suspend builder-<slug> "<reason>"`. That is the existing event an
  orchestrator uses — not a new mechanism minted by this item, and not automated by
  `tools/dispatch_principal.py`, which never calls it on the caller's behalf (same posture as
  registration itself: a real ledger write stays the orchestrator's own deliberate act).
- This note documents a convention, not a kernel kind — a hand-typed `LED_ACTOR` that skips
  the preflight is caught by `led`'s own refusal regardless, so nothing here is load-bearing
  for correctness; the preflight only saves a wasted dispatch turn.
- Not (yet) wired into the workflow-unit compiler's own `--role-map` or into any hook —
  scoped to the ad hoc Agent/Task-tool dispatch shape this ledger row itself was commissioned
  under. `hooks/pretooluse_delegation_observer.py` still journals every dispatch's `tool_use_id`
  but does not itself check or inject `LED_ACTOR` — that would be a hooks/ change and is out of
  scope for this item (and hooks/ is never touched during a live session per CLAUDE.md).

## Attestation note (added this fix round, review finding 5 — no code change, honesty only)

Every maintainer-facing document in this repository is required to pass a **fresh-context
audit loop** before it counts as finished
([law/adr/0017-the-zero-context-reader.md](../law/adr/0017-the-zero-context-reader.md), "the
A:B:C loop" it defines): **A** is whoever wrote the document; **B** is a separately forked
reviewer given only the document and that ADR, never A's own conversation, whose job is to
check that a reader with none of A's context can actually parse it; **C** repairs whatever B
found, and — when B still finds something after two rounds — **adjudicates** the escalation,
which the ADR's own design assumes is someone other than A, for the same reason A cannot judge
their own document's legibility.

The escalated round of this document's own A:B:C loop
(`attestations/doc-legibility-attestations.jsonl`, the record for this file's pre-fix-round
content hash) was adjudicated by "row-1356 builder (Sonnet, acting as C in the absence of a
separate orchestrator mid-task)" — i.e. self-adjudicated by the same builder who authored the
document, not by an independent maintainer/orchestrator recipient. The BLOCKS-MERGE review this
fix round responds to flagged that as a real gap in the escalation discipline (the A:B:C loop
assumes C is someone other than the author for exactly this reason): the disposition applied
was mechanical (unglossed cross-references given file-path citations, one sentence's grammar
fixed, no content claims changed), so the risk this particular instance carried was low, but the
PROCESS gap — author and adjudicator being the same actor — stands as reviewed and is recorded
here rather than left silent. No code change follows from it; a future escalation on this
document should route to an actual second party where one is available.
