# Glossary — autoharn's coined vocabulary

This is autoharn's glossary: definitions for every word this project uses with a meaning you
could not infer from plain English, for any reader — human or agent — who hits one of those
words in an autoharn document and needs to know what it means without asking anyone.

<a id="stand-alone-principle"></a>
**Wiki posture (the documentation discipline this file enforces).** Any *coined term* — a
word that means something specific **here** that you could not infer from plain English — is
defined in this file under a short `###` heading and **linked on first use** in every document,
as `[term](GLOSSARY.md#anchor)` (adjust the relative path by the doc's depth). A reader — human
or agent — should never have to `grep` the repo to learn what a term means. When a doc
introduces a new coined term, it adds the definition here in the **same change** (the term and
its home land together). This is the *Stand-Alone Principle*, coined in the maintainer's
prior source project chocofarm (its `leaf_eval_bound/GLOSSARY.md`), applied repo-wide.

**Coinages are provisional.** Several terms below (notably [Pillar](#pillar)) were coined by an
AI collaborator during design, not by the maintainer. This file is the **one place** to rename
them: change the heading here and the links follow. If a name annoys you, it is a bug filed
against this file, not a fact to live with.

---

## Project

### autoharn
autoharn is the project — a deliberately **neutral** name for a [metaproject](#metaproject): a harness that
formalizes an AI-collaborator workflow into queryable tools so an AI engineer can *pull* what it
needs to do the right thing, instead of the maintainer re-explaining it each session. Repo:
`github.com/KodBena/autoharn`. (Working tree is currently the `claude_harness` directory.)

### metaproject
autoharn itself: a harness for a **class** of projects, not for any one project. Its subject is
"doing the right thing, and documenting how," for concrete projects — including ones not yet
conceived. It is *fuzzy by intent*: the moment it hard-codes one project's specifics it stops
serving the next. The class it serves: projects with needs of **extreme auditability and
deductive maintenance**.

<a id="omega-and-chocofarm"></a>
### omega and chocofarm
The maintainer's two prior, sibling software projects — not part of this repository — that
autoharn's disciplines are generalized FROM. Both independently forked the same ADR-0011
"Mechanization Discipline" tenet this glossary's [Mechanization
Discipline](#mechanization-discipline) entry cites, and each contributed a concrete precedent
autoharn's own design reuses (e.g. omega's `work_status_violations` view is the origin of the
[`*_violations` gate](#violations-gate) idiom; chocofarm's `leaf_eval_bound/GLOSSARY.md` is the
origin of this file's own [Stand-Alone Principle](#stand-alone-principle), named in this file's
own opening paragraphs above). Neither project's own source lives in this repository; where
cited here, the citation is provenance, not a resolvable path.

### extreme auditability / deductive maintenance
This is the maintainer's framing of the problem genus autoharn addresses. *Auditability*: every claim
(a benchmark result, a status, a belief) is attributable and checkable, not asserted. *Deductive
maintenance*: the project's invariants and the supersession of its decisions are maintained by
**deduction over a source of truth**, not by one person's memory.

---

## Architecture — the three Pillars

### Pillar
A Pillar is one of the three load-bearing components of autoharn's design ([Pillar 1](#pillar-1),
[Pillar 2](#pillar-2), [Pillar 3](#pillar-3)). A working coinage — rename here if you prefer
another word (e.g. "leg", "column", "subsystem").

### Pillar 1
Pillar 1 is the **Capability Registry** (a.k.a. the [intent SSOT](#intent-ssot)): a queryable store the agent
**[pulls](#pull-not-push)** at point-of-need, listing every tool / service / venv / blessed
method and — crucially — *what each one proves*, so the agent reaches for the provable tool by
reflex (the [eliciting mechanism](#eliciting-mechanism)). Solves: "the maintainer keeps having
to tell the agent what's available."

### Pillar 2
Pillar 2 is the **Provenance / Accountability Ledger**: attributable, queryable links between a git commit, a
benchmark reading, its environment, the hypothesis it tested, and the session that authored it —
so a perf claim is a checkable fact and a regression is traceable to the change (and session)
that introduced it. Built on [measurement ⊥ interpretation](#measurement--interpretation) and
the [Witness → Correction](#witness--correction) chain.

### Pillar 3
Pillar 3 is the **Logic Safety Net**: the programmatic enforcement of disciplines that today live only as prose:
per-store [`*_violations` gates](#violations-gate) backed by real engines — *classical* logic
(recursive SQL, Z3, OR-Tools) for provable invariants, *non-classical* logic for
[supersession](#supersession), provisional records, and conflicting advisories. The embodiment
of [Mechanization Discipline](#mechanization-discipline).

---

## Provenance & ledger

### SSOT
Single Source Of Truth. The one authoritative home for a fact; everything else *derives* from it
and may not contradict it.

### intent SSOT
The [SSOT](#ssot) for the maintainer's **intent**, as opposed to a mere *projection* of it. The
canonical example: the venv is a projection of the intent "use automated reasoning / optimization
where apt" — [Pillar 1](#pillar-1) captures the intent itself, plus the blessed instances, plus
the open invitation to bless more.

### pull-not-push
The agent **queries** the registry on demand (pull), rather than relying on passively-injected
memory (push). Motivation: memory is leaned on hardest exactly when context is thinnest — the
opposite of the intended effect — so the authoritative facts must be query-time, not cached.

<a id="measurement--interpretation"></a>
### measurement ⊥ interpretation
Readings (measurements) are kept **structurally separate** from interpretations of them, so "a
reading-*of* the data recorded *as* the data" is unrepresentable. (`⊥` = "is independent of /
orthogonal to".)

### pre-registration (prereg)
A criterion or hypothesis is declared **and committed before** the result it judges — an
ordering (temporal) invariant that prevents post-hoc rationalization.

### DIRTY tree
A benchmark or reading produced against an **uncommitted** git working tree (`tree = DIRTY`),
hence non-reproducible. A DIRTY reading must not be promoted to `confirmed` — see
[suspect](#suspect).

### suspect
A third truth-value ("unknown / not-yet-corroborated"), distinct from true and false, that the
gate must **not explode on** (see [paraconsistency](#paraconsistency)). [DIRTY](#dirty-tree)
readings and conflicting advisories live here without forcing a true/false collapse; the point of
the tag is that it *blocks promotion to confirmed*, not merely records.

<a id="home-flip"></a>
### HOME-FLIP
The maintainer-performed cutover recorded in `provenance/HOME-FLIP.md`: before the flip, the
two source repos this project consolidates (`claude_harness`, `epistemic-operator`) are
authoritative and this repo holds migrated copies; after the flip, provenance direction
reverses — this repo becomes the source of truth and the two source repos become read-only
evidence archives. A builder — an implementing agent or contributor carrying out a work item,
as opposed to the maintainer who alone may rule on it — prepares the record and verifies its
preconditions; only the maintainer performs the flip itself.

---

## Logic & gates

<a id="violations-gate"></a>
### `*_violations` gate
A SQL view (per store) whose **non-empty result fails CI**: *empty ⇒ clean*. The "logic-gate as a
query" idiom, prototyped by [omega](#omega-and-chocofarm)'s `work_status_violations` (Postgres
`WITH RECURSIVE`). The basic unit of [Pillar 3](#pillar-3).

### meta-sweep
The check that **every discipline-stating rule declares an [enforcement surface](#enforcement-surface)**
and that every *named mechanism* it cites still resolves on disk. autoharn's first self-applied
gate: it proves the disciplines are mechanized rather than merely asserted.

### enforcement surface
The closed-vocabulary classification of **how** a rule is enforced: e.g. compile/construction-time,
CI gate, write-time data constraint, runtime invariant, or *review-only* (declared
"presumptively decaying"). From the [source projects'](#omega-and-chocofarm) "Mechanization
Discipline" (ADR-0011).

### class-not-instance net
A gate that keys on the **class** of a defect — a structural slot, a name/shape predicate, or a
derived-from-one-source invariant — never an *enumeration* of known instances (which "fail open
at the next instance"). The standard for a sound [`*_violations` gate](#violations-gate).

### supersession
An append-only override: a later record **supersedes** an earlier one, and "the current belief on
scope S = the node that nothing supersedes." Non-monotonic / defeasible: adding a record can
retract a prior conclusion without rewriting it. See [Witness → Correction](#witness--correction).

<a id="witness--correction"></a>
### Witness → Correction
The append-only [supersession](#supersession) pattern: the prior record (the *witness*) is
**never rewritten**; a *correction* is appended that supersedes it. Preserves the audit trail of
what was believed and when.

---

## Process & discipline

### Mechanization Discipline
The north star (from the [source projects'](#omega-and-chocofarm) ADR-0011): **convert every executive lapse into a
mechanism**, so the same error is never seen twice. A recurrence that was never mechanized is a
guard the *executive* (maintainer) failed to build — structurally theirs to own, not the
implementer's.

### eliciting mechanism
The [Pillar 1](#pillar-1) feature that makes the agent **ask** "is there a blessed tool for this
task?" rather than wait to be told. Realized by the *what-it-proves* column keyed by task-shape
(feasibility → SMT, finite enumeration → CP-SAT, convex allocation → cvxpy, …).

### blessed
Endorsed by the maintainer for a class of task. A *blessed tool/method* is one the
[Capability Registry](#pillar-1) advertises as the right reach for that task — not merely
something that happens to be installed.

### mandated (tier)
One notch stronger than [blessed](#blessed): the [Capability Registry](#pillar-1) entry for this
task-shape is not merely endorsed but REQUIRED, and its use is checked, not just advertised. A
mandated declaration names an EVIDENCE SHAPE — the checkable artifact that proves the discipline
was followed (a committed declarative model file; matching keys in a store; a solver-run
provenance record) — and the work item for a mandated-shape task carries a review obligation by
convention: its close is countersigned by a distinct [principal](#principal) whose review cites
that evidence shape, present or absent
([ORCH-SPEC-RESOURCE-REGISTRY.md](design/ORCH-SPEC-RESOURCE-REGISTRY.md)
§4 — self-reports are not trusted, per the maintainer's own witnessed reason: implementers "take
undue license and lie about what they have done"). `TIER` is one of four values on a [resource
declaration](#resource-declaration): `available` (on record, no endorsement), `blessed:
<task-shape>` (the recommended reach for that shape), `mandated: <task-shape>` (required, and
countersign-checked, for that shape), `forbidden: <task-shape>` (see [forbidden
(tier)](#forbidden-tier) below).

### forbidden (tier)
The fourth [`TIER`](#mandated-tier) value on a [resource declaration](#resource-declaration),
added by [ORCH-SPEC-RESOURCE-ACCOUNTING.md](design/ORCH-SPEC-RESOURCE-ACCOUNTING.md) §3 (tracker
item `accounting-stage-a`) to complete the MAY/SHOULD/MUST/MUST-NOT deontic register the other
three tiers already three-quarters covered: `forbidden: <task-shape>` says this resource MUST NOT
be reached for, for that task shape. `./pickup`'s RESOURCES section sorts a `forbidden` entry
first — ahead of `mandated` — because a prohibition outranks a mandate for a reader's attention.
Version 1 is **audit-policed, not write-time-enforced**: nothing today refuses the INVOCATION of a
forbidden resource as it happens; the `./audit --resources` surface (unbuilt as of this tier's
addition — [ORCH-SPEC-RESOURCE-ACCOUNTING.md](design/ORCH-SPEC-RESOURCE-ACCOUNTING.md) §5/§8 stage
C) is where a witnessed use against a `forbidden` entry becomes a checked violation. Saying so
here is the honest declaration the tier's own spec makes (§7): a write-time refusal is a possible
later mechanism, not this one.

### resource declaration
A `kind=decision` ledger row carrying the `resource:` statement-prefix convention (stage 1;
[ORCH-SPEC-RESOURCE-REGISTRY.md](design/ORCH-SPEC-RESOURCE-REGISTRY.md) §2) that declares one
[Capability Registry](#pillar-1) resident: a solver, service, backend, binary, or library, what
it proves, when to reach for it, and its [tier](#mandated-tier). [`./pickup`](#led-and-pickup)'s
RESOURCES section is the pull surface a session reads it from;
[USER-BLESSED-TABLE-TEMPLATE.md](design/USER-BLESSED-TABLE-TEMPLATE.md) is the adopter-facing
template that fills these in and states the exact statement grammar.

### anti-corruption layer
A structured store that **replaces a hand-edited file** as the source of truth, allowing access
only through validated operations (the term is from Domain-Driven Design). The precedent:
[omega](#omega-and-chocofarm)'s `work-status` Postgres store, which replaced a hand-edited
`work-status.json`.

### paraconsistency
A logic that does **not** explode (derive everything) from a contradiction, letting conflicting
records coexist. Underwrites the [suspect](#suspect) third value and "conflicting advisories
coexist without the gate failing."

<a id="both-polarity"></a>
### both-polarity
A gate or an invariant it enforces is proven **both-polarity** when its evidence includes a
case that fires red (the check catching a real violation) as well as a case that passes clean
— "a gate never seen red is a claim," not a demonstrated one. `seen-red/` is the standing home
for this evidence.

<a id="refuse-and-teach"></a>
### refuse-and-teach
The design principle behind every mechanized guardrail in this project: a refusal is never a
bare error. When a hook or gate blocks an action that would break a guarantee, its message
names what was missing and what to do next, so the refusal itself is the instruction
([USER-GUIDE.md §6](USER-GUIDE.md#6-when-something-refuses) works through a live example).

<a id="post-fable-law"></a>
### POST-FABLE (law)
The operating posture adopted after Fable — the maintainer's primary AI-collaborator authoring
model — withdrew from a session: judgment for known work is pre-banked to disk in `judgment/`
rather than re-derived at run time. Apply it; never re-derive or weaken it; a misfit against
the banked judgment is filed as a **FRAME-GAP finding** — a recorded mismatch between the
banked judgment's frame and what the new case actually needed — rather than silently
reinterpreted to make it fit. Named for and set out in
`vestigial_documentation/judgment/POST-FABLE-OPERATING-BRIEF.md`.

## Operating-era terms (worlds and runs, added 2026-07-11)

The terms below entered the vocabulary with the world/run operating model (2026-07-09
onward) and were previously defined nowhere — an Opus fresh-context probe (2026-07-11)
found this file's own Stand-Alone Principle violated by their absence. Operational detail
lives in [OPERATING-CARD.md](ORCH-OPERATING-CARD.md); these are the definitions.

### world
One isolated experiment habitat: a subject schema + kernel schema pair in Postgres plus a
project directory carrying the operator verbs (`led`, [`judge`](#judge), `pickup`,
[`distance-to-clean`](#distance-to-clean), [`audit`](#audit), the [scaffold](#the-scaffold) —
see [`led`/`pickup`](#led-and-pickup) below for the two most-cited),
`deployment.json`, `.claude/apparatus.json`, and an auto-loaded governance preamble. One world
per run; a run's subject never sees a sibling world's ledger (maintainer ruling, 2026-07-09).

### run
One governed Claude Code session (or resumed chain of sessions) executing a task inside one
world. Runs are numbered; their worlds are named for them (`run5`, `run7`).

### birth chain
The ordered kernel SQL a new world receives at scaffold time: `high_watermark_1.sql`
(bundling s15 → s17-stamp → s17-independence → s19) → s20 → s21 → s22 → s23 → s24 → s25.
There is no s16; s18 is deliberately excluded (experiment apparatus, not kernel). SSOT:
`kernel/lineage/README.md` + `bootstrap/new-project.sh`.

### delta (kernel lineage delta)
One additive lineage step. Authoring may be class-ratified (strictly fail-safe
additions); it reaches reality by entering the birth chain, carried by the NEXT world's
scaffold. Never applied to an existing world — runs are strictly linear and older worlds
are settled evidence (maintainer ruling 2026-07-11; `bootstrap/apply-delta.sh` is
demoted to history).

<a id="toy-db"></a>
### the toy db
The shared, non-production Postgres database (host `192.168.122.1`, database name `toy`) this
project's own witness work runs against — as opposed to a scaffolded deployment's real subject
database. Individual scratch/fixture schema pairs (e.g. `toycolors` / `toycolors_kernel`) live
inside it; see [`ORCH-USE-MODE-ENGINE-WIRING.md`](design/ORCH-USE-MODE-ENGINE-WIRING.md)'s
target-info table for a worked example.

### scratch schema
A throwaway schema pair in [the toy db](#toy-db) used to witness a delta or fixture both
polarities, torn down to zero residue afterward (empty `information_schema.schemata` check).

<a id="wired"></a>
### wired
A world or project directory is **wired** when it is scaffolded with this repo's hooks
registered in its own `.claude/settings.json`, so a Claude session running there executes
under the governance apparatus (PreToolUse/PostToolUse hooks, the change gate, the stamp) —
as opposed to an unwired directory, where no hook intercepts anything
([ORCH-OPERATING-CARD.md](ORCH-OPERATING-CARD.md), "The two-cwd model").

### stamp
The HMAC binding a ledger row to the actual Claude session/agent that wrote it, injected
into every Bash command in a [wired](#wired) world by `hooks/stamp_intercept.py`. Unforgeable without
a secret the writer's role cannot read; a bypass write lands visibly unstamped. A tripwire,
not authentication (see [ORCH-CAPABILITIES.md, "Honest limits"](ORCH-CAPABILITIES.md#honest-limits-so-the-guarantees-arent-oversold)).

<a id="led-and-pickup"></a>
### `led` and `pickup`
Two of the project's [operator verbs](#world) (thin shell shims that `exec` autoharn's own
live templates — see `bootstrap/templates/led.tmpl` / `pickup.tmpl`), the two an agent uses
most. **`led`** appends one entry to a world's ledger per invocation (`./led decision "..."`,
`./led work open <slug> ...`, `./led review <id> ...`, etc. — its own `--help`-style header
comment is the canonical vocabulary). **`pickup`** is the session-start resume command: it
reads the ledger LIVE and prints a fresh status brief (open work items, review debt, recent
changes, and — since this session — the RESOURCES section), never a cached or stored one
([design/ORCH-OPUS-READINESS.md](design/ORCH-OPUS-READINESS.md)'s "derived at pickup time, never stored" rule).

<a id="judge"></a>
### `judge`
The operator verb `./judge`: runs `engine/ledger_differential.py` against the world's own
ledger, deriving the same verdict independently in SQL and in ASP (Answer Set Programming, the
`clingo` logic engine) and comparing them. Closed verdicts: `AGREE` (green) |
`DIVERGE_BY_DESIGN` | `DIVERGE_DEFECT` | `QUARANTINED` — the latter two are TYPED escalation
events (non-zero exit) that route upward rather than being self-adjudicated. Diagnosis
walkthrough: `engine/docs/JUDGE-READING.md`. Source: `bootstrap/templates/judge.tmpl`.

<a id="audit"></a>
### `audit`
The operator verb `./audit`: the contemporaneity check (`design/ORCH-CONTEMPORANEITY-AUDIT.md`
Part 2) that joins every ledger row to the invocation that wrote it and the wall-clock journals,
reporting per-row event-vs-record deltas. Closed verdicts: `CONTEMPORANEOUS` |
`BATCHED_DECLARED` | `LATE_DECLARED` | `BACKFILL_SUSPECT` (non-zero exit only on the last).
Read-only; safe to run mid-run or after. Not to be confused with the differently-scoped
`./audit --review-gap` surface cited under [`review_gap`](#review_gap). Source:
`bootstrap/templates/audit.tmpl`.

<a id="distance-to-clean"></a>
### `distance-to-clean`
The operator verb `./distance-to-clean`: one composed read of all closure-debt dimensions
(`review_gap`, `question_status`, `work_item_violations`) with counts and ids, computing
nothing the three underlying views do not already compute. Strictly additive convenience —
`led review-gap`, `led question-status`, and `led work violations` remain the documented
default, disaggregated way to read closure debt (maintainer condition, 2026-07-11). Source:
`bootstrap/templates/distance-to-clean.tmpl`.

<a id="the-scaffold"></a>
### the scaffold
`bootstrap/new-project.sh`, run from the autoharn checkout: creates a fresh [world](#world)
directory plus its Postgres schema pair, applies the [birth chain](#birth-chain),
writes the per-world `deployment.json` and `.claude/` wiring, and wires the operator verbs as
thin shims that `exec` autoharn's own templates live (see [`led`/`pickup`](#led-and-pickup)).

### principal
A registered identity (`author`, `reviewer`) that ledger rows are attributed to;
`LED_ACTOR=reviewer` selects one for a command. **SoD** (separation of duties) is the
requirement that review comes from a provably different invocation than the work.

### `review_gap`
The SQL view (`led review-gap`; also [`./pickup`](#led-and-pickup)'s REVIEW-DEBT section) that
lists every ledger row an [obliged](#obligation) [principal](#principal) wrote with no
distinct-actor countersign yet — an empty result is clean, any row listed is outstanding debt.
Not to be confused with the content-free-review-discharge **audit** (`./audit --review-gap`,
[engine/review_gap_thresholds.py](engine/review_gap_thresholds.py)) — a distinct,
differently-scoped check over this same view's discharges, inspecting whether a discharging
review's own statement is content-free; this view's discharge test itself never examines content
(see [USER-RECIPES-FAQ.md](design/USER-RECIPES-FAQ.md) for the full answer).

### obligation
A `countersign_obligation` row: the obliged [principal](#principal)'s EVERY row (any kind)
shows in [`review_gap`](#review_gap) until a distinct actor attests it. The row's `scope` column
is a free-text label for a human reader, never a filter on which rows count — an obligation
covers every row the obliged principal writes, regardless of scope. Oblige the WORKER (this
entry's shorthand for the `<obliged-actor-principal>` argument to `led obligate` — the
[principal](#principal) whose rows need outside eyes, typically `author`), never the
reviewer/countersigner itself (see `bootstrap/templates/led.tmpl`'s `led obligate` teach-text,
which spells out the direction because getting it backwards was a repeated mistake) — an
obligation is standing operator-owned policy config, not a role self-service capability (`led
obligate revoke` refuses a role's own attempt to lift it).

<a id="governed-file"></a>
### governed file
A file `hooks/pretooluse_change_gate.py` protects — matched, by pattern (`*.py` by default; a
project's own `.claude/governed_files.json` may widen or narrow the set), against
[SUBJECT_ROOT](#subject-root). A Write/Edit to a governed file is what [permit-to-work](#permit-to-work)
and the base `change_gate` mechanism gate on; [decomposition-review-blocker](#decomposition-review-blocker)
deliberately governs a WIDER set (see its own entry).

<a id="subject-root"></a>
### SUBJECT_ROOT
The scaffolded project's own root directory, as the `hooks/pretooluse_change_gate.py` hook
resolves it for the current invocation — from an explicit env var, or from a located
`deployment.json`, or (unwired) a byte-held default. Every path-scoped mechanism in that hook
([governed file](#governed-file) matching, [permit-to-work](#permit-to-work),
[decomposition-review-blocker](#decomposition-review-blocker)) is scoped to files under it.

### permit-to-work
The rule that a Write/Edit to a [governed file](#governed-file) is refused unless the world's
ledger shows an open AND claimed s22 work item (s22: the kernel-lineage delta that adds a
per-project work-item ledger, `kernel/lineage/s22-work-item-ledger.sql`) — a ledger entry is not
a permit; an open+claimed work item is ([ORCH-CAPABILITIES.md](ORCH-CAPABILITIES.md), numbered
item 18 — cited by number, not a stable anchor, because that document's numbered items carry
none yet; a known, filed gap, not a resolved reference).

### decomposition-review-blocker
The `decomposition_review` mechanism in `hooks/pretooluse_change_gate.py`: a substantive
Write/Edit/NotebookEdit anywhere under a [wired](#wired) [SUBJECT_ROOT](#subject-root), or a
[governed-file](#governed-file)-mutating Bash command, is refused unless the CLAIMED work item's
OWN opening (`work_opened`) ledger row has been countersigned — the same
[`review_gap`](#review_gap) discharge test applied to that one row. [Permit-to-work](#permit-to-work)
proves an open+claimed item exists; this mechanism proves that item's plan was reviewed before
its subtasks were executed (maintainer ruling 2026-07-12, [BACKLOG.md](BACKLOG.md)
"decomposition-review-blocker — shipped" — the run12 specimen: a work item's implementation
began six seconds after claim, ~2.5 minutes ahead of its own countersign verdict). This
mechanism is vacuous in a world whose
`countersign_obligation` table carries no rows at all. Its default mode is `observe`, not
`enforce` — see `hooks/pretooluse_change_gate.py`'s module docstring.

### seen-red
Banked evidence that a gate has actually REFUSED at least once (a dated fixture directory
under `seen-red/`). A gate never seen red is a claim, not a guarantee.

### ephemera
Local session transcripts and snapshots (`ephemera/session-<id>/`, gitignored). Never
committed — upstream is public, transcripts are private (maintainer ruling 2026-07-09).
