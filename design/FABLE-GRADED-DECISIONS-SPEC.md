# FABLE-GRADED-DECISIONS-SPEC — standing decisions that survive context loss

This spec proposes a durability grade for ledger decision rows, plus the machinery
(a hook, a `./pickup` section, a reader verb) that re-asserts high-grade decisions
into every rebuilt context — so that a decision the maintainer marked as standing
can no longer be lost to context compaction. It is written for the maintainer (to
ratify) and for the Sonnet builder (to implement).

Status: RATIFIED 2026-07-16 by the maintainer.
Provenance: maintainer proposal 2026-07-16 ("graded decisions" + "a hook that always
reads high-priority decisions"), sharpened the same date by a root-cause analysis of
an incident in the panel (the `autoharn-panel` deployment at
`~/w/vdc/1/experience/autoharn-panel`, a downstream adoption of this harness). The
analysis was performed by a spy — this project's name for a report-only investigation
agent sent into a deployment's session transcripts and ledger — over session
889df121-8ea9-49ca-a224-bad131076799. What it found: a standing decision (panel
ledger rows 193/200, the docs/consults filing home) was violated ~34 minutes after a
context-compaction event, AND `./pickup` could not have surfaced it. `./pickup` is
the verb this project's resumption doctrine (the standing rule that a fresh session
rehydrates from the ledger rather than replaying conversation context) designates as
the anti-compaction memory — yet its IN-FORCE-DECISIONS section is `ORDER BY id DESC
LIMIT 10` (pickup.tmpl:272, default at :1081) while the ledger stood at row ~370.
The verb reproduces the failure mode it exists to prevent: old standing decisions
scroll out of its window exactly as they scroll out of a context.

## The problem, typed

A decision row today has exactly one durability: none. Every decision competes for
the same recency window, so "we use spaces not tabs, this week" and "consults MUST
land in docs/consults, forever" age out identically. Context compaction has the same
flat model. Nothing in the system distinguishes a decision that must be re-asserted
into every future context from one that was only ever conversational.

## Elements

### 1. Kernel delta `s36-decision-grade` (lineage; ratification required)

- `ALTER TABLE ledger ADD COLUMN decision_grade text` — nullable, NO default.
- `CHECK (decision_grade IS NULL OR kind = 'decision')` — grade is decision
  vocabulary only, for now; widening to other kinds later is a strictly additive
  follow-up delta, not this one.
- NO enum, NO CHECK on the value: the kernel stores a word; which words matter is
  deployment policy (element 4). Starter vocabulary by convention: `durable`
  (must survive any context loss). Others may emerge; the maintainer's own framing
  ("or something more flexible, who knows") is the design.
- View `standing_decisions`: the in-force decision rows with `decision_grade IS
  NOT NULL`, ordered by id. "In-force" means factored through the `ledger_current`
  projection that
  [kernel/lineage/s31-supersession-uniform-retraction.sql](../kernel/lineage/s31-supersession-uniform-retraction.sql)
  established as the single home of current truth — so a superseded standing
  decision drops out automatically and is never re-injected.
- The delta's header carries `HISTORY: safe` — the formal migration-header
  convention of [MAINT-MIGRATION-ACCOMMODATIONS-SPEC](MAINT-MIGRATION-ACCOMMODATIONS-SPEC.md)
  §3, asserting the delta can be applied over an existing world's history — on
  these grounds: nullable column, no default, no existing semantics changed;
  additive view. This is the shape of the class-ratified fail-safe delta rule
  ([CLAUDE.md](../CLAUDE.md), "Class-ratified fail-safe deltas", 2026-07-09), but
  the delta is routed for ratification as part of this spec rather than claimed
  under that class.

### 2. `led decision --grade <word>` (CLI layer)

Parsed in the decision subcommand's own arg loop (lesson of ledger item
`led-work-open-refs-swallowed`, found the same day: a flag the subcommand loop
does not parse is silently swallowed into statement prose — this spec's flag MUST
NOT repeat that shape). The parser performs a live column-existence check, the
same convention `work open --parent` uses, so the verb still works against
pre-s36 worlds (the flag is refused with a teach-text there, never silently
dropped).

### 3. Hook `hooks/sessionstart_durable_decisions.py`

- Wired on `SessionStart` with matchers `compact` and `resume` (a `startup`
  session is expected to run `./pickup` per the resumption doctrine; `compact`
  is the witnessed failure surface; `resume` shares its shape).
- Reads `standing_decisions` filtered to the configured grade set; prints each
  row (`id  grade  statement`) to stdout for context injection.
- BYTE-CAPPED (default 4000 bytes, configurable): compaction happens because
  context is tight; an unbounded re-injection is self-defeating. Truncation is
  LOUD: "N more standing decisions not shown — run `./led standing`" — never
  silent (no-silent-caps rule).
- Fails open with a one-line stderr note if the ledger is unreachable — a
  context-hydration aid must never block session start.

### 4. Deployment policy knob

`apparatus.json` → `mechanisms.standing_decisions`:
`{ "grades": ["durable"], "byte_cap": 4000 }`. The hook and pickup both read
this; the kernel knows nothing of it.

### 5. `./pickup`: STANDING-DECISIONS section

This new section prints all rows of `standing_decisions` in the configured
grade set, BEFORE the recency-windowed IN-FORCE-DECISIONS section, with no
recency limit and no `-n` interaction. It applies the same
byte-cap-with-loud-truncation as the hook. This closes the witnessed pickup
gap independently of whether a session's hooks are wired.

### 6. `./led standing` (read verb)

`./led standing` is a trivial reader over `standing_decisions`; it is the escape
hatch both truncation messages point at.

## What this spec does NOT claim

The panel incident's primary failure was the model's, not the harness's: the rule
was in CLAUDE.md every turn and the orchestrator had just done the same class of
reasoning on an adjacent artifact. This spec absorbs the mechanical share — a
declared obligation that today lives only as prose gets an execution path into
every rebuilt context — and no more. The complementary enforcement absorption
(typed consult/audit closes refusing without a filing-home witness) is a separate
ledger item (`consult-close-artifact-gate`), deliberately not bundled here: this
spec is fail-safe-additive end to end; that one adds a refusal at close time and
should be judged on its own.

## Closure ([ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md) 2(a) posture)

There are four ways a standing decision can reach a post-context-loss orchestrator:
(i) survives inside the compaction summary — unreliable, witnessed dropping the
procedural half of a rule while keeping its letter; (ii) standing instruction
files (CLAUDE.md) — witnessed present-and-not-applied, and not every decision
belongs in CLAUDE.md; (iii) ledger via `./pickup` — witnessed structurally unable
(recency window); (iv) ledger via mechanical re-injection — did not exist. This
spec makes (iii) sound and creates (iv); it deliberately does not touch (i)/(ii),
which are not harness surfaces. Grades other than `durable` are left to
deployment vocabulary by design and excluded from this closure.
