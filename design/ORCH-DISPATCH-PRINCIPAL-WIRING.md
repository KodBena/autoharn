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
needed — this note plus `tools/dispatch_principal.py` are the whole deliverable.**

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

- `preamble <name>` — registered: prints `export LED_ACTOR=<name>`, exit 0. Not registered:
  REFUSED with the exact registration command, exit 1.
- `check <name>` — same test, machine-readable `REGISTERED:`/`NOT-REGISTERED:` output, for a
  batch preflight over several builder names before a wave of dispatches.

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
principal/class may discharge WHICH obligation (the "NRC-certified-signer analogy" that spec's
own reviewer pass — labeled "SCOUT" in that document's own text — flagged as an open question).
This work item is what gives that future amendment real per-builder
identities to type against — it does not attempt the typing itself, which is kernel-touching
and stays Fable-spec/maintainer-ratified.

## Honest limits

- `tools/dispatch_principal.py` tests REGISTRATION only, the same test `led`'s own
  `_resolve_actor` performs — it does not duplicate the kernel's live suspended/revoked
  standing check (`law/adr/0012-compositional-and-structural-hygiene.md`'s principle P1,
  "single source of truth": one home for that fact, and it is the kernel's `set_actor`
  trigger). A name registered now and suspended later still passes this preflight and then
  correctly refuses at the real write.
- This note documents a convention, not a kernel kind — a hand-typed `LED_ACTOR` that skips
  the preflight is caught by `led`'s own refusal regardless, so nothing here is load-bearing
  for correctness; the preflight only saves a wasted dispatch turn.
- Not (yet) wired into the workflow-unit compiler's own `--role-map` or into any hook —
  scoped to the ad hoc Agent/Task-tool dispatch shape this ledger row itself was commissioned
  under. `hooks/pretooluse_delegation_observer.py` still journals every dispatch's `tool_use_id`
  but does not itself check or inject `LED_ACTOR` — that would be a hooks/ change and is out of
  scope for this item (and hooks/ is never touched during a live session per CLAUDE.md).
