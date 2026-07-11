# Glossary — autoharn's coined vocabulary

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
The project. A deliberately **neutral** name for a [metaproject](#metaproject): a harness that
formalizes an AI-collaborator workflow into queryable tools so an AI engineer can *pull* what it
needs to do the right thing, instead of the maintainer re-explaining it each session. Repo:
`github.com/KodBena/autoharn`. (Working tree is currently the `claude_harness` directory.)

### metaproject
autoharn itself: a harness for a **class** of projects, not for any one project. Its subject is
"doing the right thing, and documenting how," for concrete projects — including ones not yet
conceived. It is *fuzzy by intent*: the moment it hard-codes one project's specifics it stops
serving the next. The class it serves: projects with needs of **extreme auditability and
deductive maintenance**.

### extreme auditability / deductive maintenance
The maintainer's framing of the problem genus autoharn addresses. *Auditability*: every claim
(a benchmark result, a status, a belief) is attributable and checkable, not asserted. *Deductive
maintenance*: the project's invariants and the supersession of its decisions are maintained by
**deduction over a source of truth**, not by one person's memory.

---

## Architecture — the three Pillars

### Pillar
One of the three load-bearing components of autoharn's design ([Pillar 1](#pillar-1),
[Pillar 2](#pillar-2), [Pillar 3](#pillar-3)). A working coinage — rename here if you prefer
another word (e.g. "leg", "column", "subsystem").

### Pillar 1
**Capability Registry** (a.k.a. the [intent SSOT](#intent-ssot)). A queryable store the agent
**[pulls](#pull-not-push)** at point-of-need, listing every tool / service / venv / blessed
method and — crucially — *what each one proves*, so the agent reaches for the provable tool by
reflex (the [eliciting mechanism](#eliciting-mechanism)). Solves: "the maintainer keeps having
to tell the agent what's available."

### Pillar 2
**Provenance / Accountability Ledger.** Attributable, queryable links between a git commit, a
benchmark reading, its environment, the hypothesis it tested, and the session that authored it —
so a perf claim is a checkable fact and a regression is traceable to the change (and session)
that introduced it. Built on [measurement ⊥ interpretation](#measurement--interpretation) and
the [Witness → Correction](#witness--correction) chain.

### Pillar 3
**Logic Safety Net.** The programmatic enforcement of disciplines that today live only as prose:
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

---

## Logic & gates

<a id="violations-gate"></a>
### `*_violations` gate
A SQL view (per store) whose **non-empty result fails CI**: *empty ⇒ clean*. The "logic-gate as a
query" idiom, prototyped by omega's `work_status_violations` (Postgres `WITH RECURSIVE`). The
basic unit of [Pillar 3](#pillar-3).

### meta-sweep
The check that **every discipline-stating rule declares an [enforcement surface](#enforcement-surface)**
and that every *named mechanism* it cites still resolves on disk. autoharn's first self-applied
gate: it proves the disciplines are mechanized rather than merely asserted.

### enforcement surface
The closed-vocabulary classification of **how** a rule is enforced: e.g. compile/construction-time,
CI gate, write-time data constraint, runtime invariant, or *review-only* (declared
"presumptively decaying"). From the source projects' "Mechanization Discipline" (ADR-0011).

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
The north star (from the source projects' ADR-0011): **convert every executive lapse into a
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

### anti-corruption layer
A structured store that **replaces a hand-edited file** as the source of truth, allowing access
only through validated operations (the term is from Domain-Driven Design). The precedent:
omega's `work-status` Postgres store, which replaced a hand-edited `work-status.json`.

### paraconsistency
A logic that does **not** explode (derive everything) from a contradiction, letting conflicting
records coexist. Underwrites the [suspect](#suspect) third value and "conflicting advisories
coexist without the gate failing."

## Operating-era terms (worlds and runs, added 2026-07-11)

The terms below entered the vocabulary with the world/run operating model (2026-07-09
onward) and were previously defined nowhere — an Opus fresh-context probe (2026-07-11)
found this file's own Stand-Alone Principle violated by their absence. Operational detail
lives in [OPERATING-CARD.md](OPERATING-CARD.md); these are the definitions.

### world
One isolated experiment habitat: a subject schema + kernel schema pair in Postgres plus a
project directory carrying the operator verbs, `deployment.json`, `.claude/apparatus.json`,
and an auto-loaded governance preamble. One world per run; a run's subject never sees a
sibling world's ledger (maintainer ruling, 2026-07-09).

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

### scratch schema
A throwaway schema pair in the toy db used to witness a delta or fixture both polarities,
torn down to zero residue afterward (empty `information_schema.schemata` check).

### stamp
The HMAC binding a ledger row to the actual Claude session/agent that wrote it, injected
into every Bash command in a wired world by `hooks/stamp_intercept.py`. Unforgeable without
a secret the writer's role cannot read; a bypass write lands visibly unstamped. A tripwire,
not authentication (see CAPABILITIES "Honest limits").

### principal
A registered identity (`author`, `reviewer`) that ledger rows are attributed to;
`LED_ACTOR=reviewer` selects one for a command. **SoD** (separation of duties) is the
requirement that review comes from a provably different invocation than the work.

### obligation
A `countersign_obligation` row: the obliged [principal](#principal)'s EVERY row (any kind)
shows in `review_gap` until a distinct actor attests it. Scope is a label, not a filter.
Oblige the WORKER, never the reviewer (see `led obligate` teach-text) — an obligation is
standing operator-owned policy config, not a role self-service capability (`led obligate
revoke` refuses a role's own attempt to lift it).

### permit-to-work
The rule that a Write/Edit to a governed file is refused unless the world's ledger shows an
open AND claimed s22 work item — a ledger entry is not a permit; an open+claimed work item
is (CAPABILITIES item 18).

### seen-red
Banked evidence that a gate has actually REFUSED at least once (a dated fixture directory
under `seen-red/`). A gate never seen red is a claim, not a guarantee.

### ephemera
Local session transcripts and snapshots (`ephemera/session-<id>/`, gitignored). Never
committed — upstream is public, transcripts are private (maintainer ruling 2026-07-09).
