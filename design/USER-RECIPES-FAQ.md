# Can I do that? — recipes FAQ for operators

This page is written for an operator of a scaffolded project who wants to know whether the
harness supports a thing they have in mind, and what to actually type if it does. Every
entry below began life as a real operator question ("can we use X for end users?", "can I
track Y?") asked of this project's orchestrator during 2026-07; the answers were built,
witnessed, and then condensed here. This page deliberately restates NO grammar and NO
ceremony in full — each recipe names the intent, the one-line shape, the honest limit, and
the ONE page where the full truth lives (this project's single-source-of-truth discipline:
a grammar documented twice drifts). The dense per-mechanism inventory this page complements
is [ORCH-CAPABILITIES.md](../ORCH-CAPABILITIES.md); the front door for first-time setup is
[USER-GUIDE.md](../USER-GUIDE.md).

## Planning and retrospectives

**Can agents estimate a task's cost before doing it, and can I see how the estimates did?**
Yes — ledger an `estimate:` row per task at decomposition time; `./pickup` prints all of
them under its ESTIMATES section, and the retrospective recipe has an estimate-vs-actual
section for reading them against what happened. The standing invariant, enforced by
design rather than by accident: a missed estimate is retrospective data, never a
violation — nothing gates, audits, or refuses on estimate accuracy, and nothing will.
Grammar and comparison recipe: [USER-RETROSPECTIVE-RECIPE.md](USER-RETROSPECTIVE-RECIPE.md) §6.

**Can I get cost/usage figures I can rely on?**
Partly, and the line matters: raw hook-witnessed event counts are evidentiary; anything
priced or derived from them (token totals, money) is diagnostic-grade permanently — useful
for a sanity check, never sound enough to bill against. Headline statement:
[USER-GUIDE.md](../USER-GUIDE.md) §5; the design boundary:
[ORCH-SPEC-RESOURCE-ACCOUNTING.md](ORCH-SPEC-RESOURCE-ACCOUNTING.md) §6.

**Can work form a deep task tree without deep subagent nesting?**
Yes — the tree lives in ledger rows, not process nesting: an interior task's children are
OPENED as work items citing the parent, dispatched flat, each closeable with its own
witness. Execution stays one or two levels deep; the logical tree is unbounded and every
interior node is auditable. The work verbs' home is
[ORCH-OPERATING-CARD.md](../ORCH-OPERATING-CARD.md). Per-node estimate-vs-actual rollups
are a designed follow-up, not yet built — the design lives on the deployment's own tracker
as work item `work-tree-rollup` (a ledger row, not a committed page: read it with
`./led show work-tree-rollup` at the repository root, the same live-lookup convention the sibling
specs use for tracker items).

## Workflow patterns

**I want a workflow to iterate until clean — can an agent spawn sub-agents and loop on its
own output until a defect list comes up empty?**
Yes, natively, and both halves of that question have a plain answer. The looping half: a
"fix-point" here means a script keeps calling an agent, feeding it the artifact or defect
list as it currently stands, until a round finds nothing new to fix — and that loop lives in
the workflow **script's own deterministic control flow** (an ordinary `while` loop wrapping
repeated agent invocations — whether that is the `Agent` tool from an orchestrating session
or a standalone driver script built on the Claude Agent SDK), never in any one agent's own
sense that it is "done." Terminate on **loop-until-dry**: keep looping until K *consecutive*
rounds each report zero new findings, not just one empty round — a defect population of
unknown size can have a long tail a single-round counter misses. (This project uses the
identical criterion in its own fix-point loops:
[design/ORCH-AGENTIC-PATTERNS.md](ORCH-AGENTIC-PATTERNS.md) §3's "adversary files zero new
rows for K consecutive rounds", and the two-role audit loop below.) The spawning half: yes,
an agent your workflow dispatches can itself dispatch further sub-agents — nesting is not
disabled — with a fuller, more capable agent type (e.g. `general-purpose`) available to use
where the workflow's own default agent type is a leaner, narrower one.

The load-bearing caveat, stated because it was caught failing in practice: **each round of
the loop must spawn a genuinely fresh agent, never resume one long-lived agent across
rounds.** An agent that carries its own prior round's context into the next round is not
actually re-examining the current state with open eyes — it already committed to a verdict
in an earlier turn, and tends to re-assert that verdict even when the bytes in front of it
have since changed underneath it. This is not a hypothetical risk: on 2026-07-13, in this
project's own two-role fix-point loop (the A:B:C fresh-context documentation-review loop,
[ORCH-ABC-AUDIT-LOOP-RECIPE.md](ORCH-ABC-AUDIT-LOOP-RECIPE.md)'s round-2 discipline), a
reviewer agent resumed via a follow-up message — rather than spawned fresh — repeated its
first round's verdict *verbatim* against on-disk content that directly contradicted it. Spawn
round N+1 as a brand-new agent invocation with no memory of round N, every round, no
exceptions.

Termination discipline is the other half worth naming up front, not discovering by billing
surprise: a dry-count guard (K consecutive empty rounds) belongs alongside a hard budget
guard (a round cap, a cost or token ceiling) — a workflow script is ordinary deterministic
code, so a fix-point loop with a broken or too-loose termination condition runs to whatever
cap you built in, burning real, billed tokens the whole way there; nothing backstops a
runaway loop before that cap except the cap itself. No single page owns this pattern end to
end yet; [design/ORCH-AGENTIC-PATTERNS.md](ORCH-AGENTIC-PATTERNS.md) works out the
loop-until-dry criterion in more depth, and
[ORCH-ABC-AUDIT-LOOP-RECIPE.md](ORCH-ABC-AUDIT-LOOP-RECIPE.md) is a complete worked example of
exactly this shape — two agent roles, fresh-fork-per-round, a two-round cap, and a named
escalation path for when the loop does not converge.

**My workflow script just crashed / hung / did something baffling — is this a known
shape?** Maybe — check first. Five gotchas have each bitten this project's own
workflow scripts more than once (args arriving as an already-parsed JSON value rather
than a string needing a parse, model-pinning on every dispatch call, the ban on
calling `Date.now()`/`Math.random()` inside a script a durable workflow runtime may
resume or replay from a checkpoint — either call can return a different value on
resume and silently steer the script down a different path than it took the first
time, stall-vs-crash as opposite-cause failure shapes needing opposite diagnoses, and
a workflow run's own journal (its append-only `.jsonl` log of what each round did)
carrying `result` fields that are repr-strings, not nested JSON) — four with a dated
incident on record, one (the Date.now()/Math.random() ban) stated as a general hazard
with no located incident yet — each with a stated fix regardless. Read
[ORCH-WORKFLOW-SCRIPT-GOTCHAS-RECIPE.md](ORCH-WORKFLOW-SCRIPT-GOTCHAS-RECIPE.md)
before writing a new workflow script, or when one fails in an unfamiliar way.

**I have a large batch of independent work units to dispatch — is there a standing
recommendation for how to parallelize them instead of just running them one after another?**
Yes — **standing recommendation** (maintainer directive, 2026-07-14): use
`tools/makespan-scheduler/` (vendored 2026-07-14, split into its own published repository and
converted to a git submodule 2026-07-15) for any large-scale batch of jobs that conflict only
over shared
resources (e.g. two edits touching the same file), rather than defaulting to a hand-picked
sequential order. Claude Code is, functionally, an infinite-server model of work — parallel
agent capacity is cheap to spin up — but the default LLM inclination is still to serialize
work that could safely overlap, which wastes exactly the capacity that is available. Feed the
batch's jobs (id + the resources each one touches + an optional duration) to the scheduler; it
returns a schedule computed by CP-SAT (a constraint-programming solver, OR-Tools' `cp_model`) —
either proven optimal or honestly labeled not — and a
`batches` field — ordered waves of job ids safe to dispatch together — and that dispatch order
is what you actually run, not a re-guess. **The guarantee is conditional, and the condition
matters more than the tool**: the scheduler can only be as correct as the job list it is given,
and it has NO notion of one job's output feeding another job as input (the vendored tool's own
"independent-tasks" scope) — a batch with a real, hidden data dependency fed into it as if it
were a mere resource conflict produces a schedule that looks authoritative and is wrong. Before
treating a batch as ready to schedule, therefore, an independent countersign of the job list
itself (not self-review) is the recommended discipline, not an optional nicety — full
treatment, including exactly how that countersign rides this project's own `led
review`/`led obligate` machinery and what remains unbuilt today: read
[ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md](ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md) in full before
adopting this for anything you'd actually rely on. Tool docs and vendoring/split provenance:
[`tools/makespan-scheduler/README.md`](../tools/makespan-scheduler/README.md) /
[`tools/makespan-scheduler-PROVENANCE.md`](../tools/makespan-scheduler-PROVENANCE.md).

**How do I prove two phases ran in the right order, instead of trusting an agent's
say-so?**
Split the work into two separately-dispatched agents and let the ledger's append-only row ids
do the proving, rather than trusting either agent's narrative about which one went first. The
pattern: dispatch a document-only agent whose sole output is the docs describing what changed
and why; the orchestrator itself then writes a ledger row citing those produced docs, once it
has read them; only after that row lands, in a wholly separate dispatch, is a fix-only agent
created — an agent that, by construction, did not exist yet at the moment the documentation
row landed. Because ledger rows are append-only and numbered in issuance order, a reader who
was never in the room can verify the same three facts a live witness saw: the docs landed, the
orchestrator's row citing them landed next, and the fix agent's own row landed only after
that — order as a structural fact about row ids, never a self-report from either agent
claiming it went first.

Honest limit: this proves the ORDER in which the ledgered acts happened, not that the fix
agent actually read the documents it was dispatched after — a fix-only agent created after a
documentation row could still ignore it. Pair the sequencing with an ordinary review step that
checks the fix's content against the docs it was supposed to follow; sequencing alone answers
"did this happen in the right order", not "was the later act actually informed by the earlier
one".

Invented downstream, not here: this shape was invented by the autoharn-panel deployment's own
orchestrator, in its own ledger (rows 401, 415, and 1144 there, named here only as history),
and is carried upstream into this project's record via decision row 1295 (2026-07-17 two-spy
synthesis) — the underlying panel session transcripts remain local evidence per this project's
auditability ruling; the ledger row is the citable record.

**How do I record, defeasibly, that a close's promised commit actually landed in the tree?**
Pair the work item with a second one. Whenever closing a work item necessarily modifies the
tracked source tree, open a companion item at the same time whose entire resolution IS the
git commit that captures the promised tree state. The first item closes on its own merits,
with one of the two review-bearing constructors (`--review-witness` or `--review-deferred`),
because it carries judgment. The companion closes only after the commit exists, with the
third constructor built for exactly this shape (s38):

    ./led work close <slug>-commit shipped --review-bookkeeping --witness commit:<sha>

The CLI machine-checks the claim at construction: the witness must be commit-shaped, and the
commit must actually exist in this world's repository (`git cat-file` is run for you — a
nonexistent or non-commit object refuses with a teach-text). The pairing gives you a
defeasible, queryable record that the promised commit landed, without manufacturing a review
obligation that has nothing in it to review.

Honest limits, stated so the pattern is not over-trusted: a bookkeeping close claims ONLY
"this commit exists" — nothing about its content, correctness, or completeness; the paired
JUDGMENT item's own review is where content is vouched for. And the constructor is
deliberately a closed category: if you find yourself reaching for `--review-bookkeeping` on
a close that carries any judgment at all, that is category creep — the exact drift the
`work_bookkeeping_closes` view exists to make visible (every bookkeeping close, forever, one
query; a growing view full of judgment-bearing closes is a finding to report upstream, never
a local norm to settle into).

Invented downstream, not here: the pairing convention comes from the autoharn-panel
deployment's own orchestrator (its ledger rows 407 and 408, named here only as history),
carried upstream via decision row 1295 (2026-07-17 two-spy synthesis); the s38 constructor
(`design/FABLE-BOOKKEEPING-CLOSE-SPEC.md`, maintainer-ratified) is what made the convention's
closes representable honestly instead of forcing rubber-stamp countersigns.

## Declaring things on the ledger

**Can I declare which tools/services/agents this project may, should, must, or must not
use?**
Yes — one `resource:` row per resource, whose TIER field carries the deontic force:
`available` (MAY), `blessed:` (SHOULD), `mandated:` (MUST), `forbidden:` (MUST-NOT).
`./pickup` renders them tier-sorted, prohibitions first. Honest limit, tier by tier (not one
blanket answer — the two owning specs, [USER-BLESSED-TABLE-TEMPLATE.md](USER-BLESSED-TABLE-TEMPLATE.md)
and [ORCH-SPEC-RESOURCE-ACCOUNTING.md](ORCH-SPEC-RESOURCE-ACCOUNTING.md), drifted on exactly this
in mid-2026-07-12 and were
reconciled 2026-07-13, tracker row 223 — a ledger row, not a committed page: `./led show 223` at
the repository root reads it in full): `mandated`'s close-review convention already shipped and
surfaces an undischarged close as [`review_gap`](../GLOSSARY.md#review_gap) debt — never a
refusal of the close itself;
`forbidden` is declaration + display only today, with no mechanism yet refusing an invocation
that reaches it (that audit is spec'd, unbuilt — the spec's own §7 says so). The reconciled,
owning statement of what is and is not enforced per tier lives at
[ORCH-SPEC-RESOURCE-ACCOUNTING.md §4.1](ORCH-SPEC-RESOURCE-ACCOUNTING.md#41--the-mandated-tiers-enforcement-status-reconciled-dated-correction-2026-07-13-tracker-row-223).
Grammar home: [USER-BLESSED-TABLE-TEMPLATE.md](USER-BLESSED-TABLE-TEMPLATE.md); design:
[ORCH-SPEC-RESOURCE-ACCOUNTING.md](ORCH-SPEC-RESOURCE-ACCOUNTING.md).

**Can I declare an architectural or licensing boundary and split work along it?**
Yes, declare it today; enforcement is staged. `taxon:` rows assign path patterns to named
classes, `interface:` rows name the sanctioned crossing points; `./pickup` renders a
TAXONOMIES section. The worked example is a real one (an MIT-derivative package inside a
public-domain codebase). What does NOT exist yet: the audit family and the write-time gate
that would police cross-boundary writes (Stages B–D of the spec). Declaring no taxonomy
declares no obligation. Grammar home and example:
[USER-TAXONOMY-DECLARATION.md](USER-TAXONOMY-DECLARATION.md); design:
[ORCH-SPEC-TASK-TAXONOMY.md](ORCH-SPEC-TASK-TAXONOMY.md).

**Can I encode how tasks should be split, so I don't have to micromanage decomposition?**
Yes as declared policy: `task-policy:` rows carry splitting criteria (one acceptance
criterion per task, one boundary per task, estimate-before-execution, …) with MUST/SHOULD
force, and reviewer countersigns cite the criteria they checked. The policing column is
derived from what mechanisms actually exist — a criterion never claims more enforcement
than is built. Design and criteria table:
[ORCH-SPEC-DECOMPOSITION-POLICY.md](ORCH-SPEC-DECOMPOSITION-POLICY.md) §3.

## Principal identity (s40/s41)

These two entries deviate from this page's usual point-elsewhere convention (full command
sequences with quoted witnessed output, not a one-liner plus a pointer) because the surface is
new and unfamiliar: `principal` went from four flat columns with no history to an event-sourced
identity model (registration, standing, role/key bindings, competence, relationships) in kernel
deltas s40/s41. Delivery record: [orchlog.d/s40-s41-principal-identity.md](../orchlog.d/s40-s41-principal-identity.md);
full spec: [design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md](FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md).

**Prominent caveat, read before typing anything below:** these `led principal ...` verbs exist
only in a world whose [birth chain](../GLOSSARY.md#birth-chain) carries commit `87f00b4` (s41)
and, for the identity-events half alone, `39480ec` (s40) — runs are strictly linear, so an
already-scaffolded world gains none of this. If you want to try these commands today without
waiting for your next real world, scaffold a disposable one first —
[USER-GUIDE.md](../USER-GUIDE.md) §3b has the `bootstrap/new-project.sh --new-world`
walkthrough — and play there; tear it down when done.

**Does MY world actually have s40/s41?** Run `./migrate <deployment-dir> --dry-run` from your
autoharn checkout (`<deployment-dir>` is the path to your scaffolded world). Per its own
documented behavior ([README.md §4](../README.md#4-bring-a-deployments-database-up-to-date-with-a-newer-kernel)):
it prints the resolved db/host/schema, then reports which deltas — by name — your world's
database is missing, by running each birth-chain entry's own `.detect.sql` check against your
live schema and stopping at the first one that reads false; nothing is applied under
`--dry-run`. Read straight from the verb's own source
(`bootstrap/migrate_core.py`): the two shapes you will actually see are `migrate: current
lineage head = <name>` followed by `migrate: '<deployment-name>' is already at the lineage
head. Nothing to migrate.` if s41 (or later) is already applied, or `migrate: missing (<n>):
s40-principal-identity-events, s41-principal-bindings-and-relations[, ...]` naming exactly
what your world lacks. There is no lighter-weight check than this — `distance-to-clean` does
not report lineage position — so this is the one command to run.

**How do I set up the principals in a new world?**
You mostly don't have to — a world born on this commit or later starts with a WORKING set of
principals, not an empty registry. Here is exactly what the scaffold already did for you, and
what to type for anything beyond that.

*What birth already gave you.* The scaffold's birth sequence, run once at `--new-world` time,
is three explicit, attributed acts, in order: (1) the connection principal `author` is
registered through the full s40 ceremony (self-attributed — the one genesis exception, since
nothing else exists yet to attribute it to) and its `principal_registered` event lands; (2) a
`principal_standing_declared` event binds the world's database role to `author` — this is the
"declared, not silent" default: it is why your very first `./led` write, with no
[`LED_ACTOR`](../GLOSSARY.md#principal) (the environment variable that names which registered
principal a `led` write is attributed to) set, just works; (3) `reviewer` and `commissioner`
are registered the same way, each with a stated purpose. Witnessed on a real `--new-world` scaffold run
(`seen-red/s40-principal-identity-events/red.txt`, case `new-world-birth-sequence`): *"scaffold
exit=0; registration events=3 (author, reviewer, commissioner), standing declarations=1; first
no-LED_ACTOR write exit=0, attributed 'author|declared-default'"*. If all you need is the
baseline three principals a solo operator's world already assumes, you are done — no further
setup required.

*Registering an additional principal.* `--purpose` is mandatory on an s40+ kernel; omit it and
you are refused, not silently ignored. The refusal below cites "AC-2," NIST 800-53's
Account Management control (the standard the registration ceremony's mandatory-purpose
requirement is grounded in — quoted verbatim below, not paraphrased). Witnessed
(`seen-red/s40-principal-identity-events/red.txt`, case `purpose-mandatory`, and the exact
refusal text from `bootstrap/templates/led.tmpl`'s own source):

```sh
$ ./led register-principal nopurpose model
```
```
led register-principal: REFUSED -- --purpose is mandatory on an s40 kernel: a
  registration is a recorded, attributed event with a stated purpose (AC-2's
  'account with a stated purpose'; kernel/lineage/s40-principal-identity-events.sql).
usage: led register-principal <name> <human|model|subagent|tool> --purpose "<why this identity exists>"
```
(exit 1). Supply `--purpose` and it constructs:
```sh
$ ./led register-principal reviewer2 model --purpose "second-tier model reviewer"
```
Re-registering the same name is never a silent no-op — both class polarities refuse loudly
(`seen-red/s40-principal-identity-events/red.txt`, cases `register-duplicate-same-class` and
`register-duplicate-class-mismatch`). Same class, same name again:
```
led register-principal: REFUSED -- principal 'reviewer2' is already registered
  (id <id>, class model, purpose: <purpose>). Re-registration is never a silent no-op
  (s40 §3.7 -- the panel's silent ON CONFLICT DO NOTHING class, closed): if you meant
  this existing principal, just use it (LED_ACTOR=reviewer2); if you meant a NEW
  identity, pick a new name.
```
A different class under the same name refuses too, naming the mismatch and pointing at
`./led principal relate <new> succeeds <old>` (once s41 has landed) as the way to record a
genuine identity succession rather than a rename — names are immutable by rule, and a class
change is a new identity, never an edit to the old one.

*Declaring standing* — binding a database role's default attribution to a registered principal,
the same declared-not-silent act the scaffold performed for `author`. `--db-role` is optional
and defaults to your own world's connection role (read directly from `bootstrap/templates/led.tmpl`'s
source: `db_role="$ROLE"` unless overridden) — the same `role` value your deployment's own
`deployment.json` already carries (README.md's configuration table names this field; run `cat
<world-dir>/deployment.json` and look at `"role"` if you've forgotten it). For the common case
— rotating which principal your world's OWN connection role speaks for — you never need to
pass `--db-role` at all:
```sh
$ ./led principal declare-standing reviewer2
```
Only pass `--db-role <name>` explicitly when declaring standing for a DIFFERENT Postgres role
than the one your `deployment.json` already names — e.g. a second writer role your world's
kernel DDL granted separately (`\du` in `psql` lists every role that exists on the database if
you need to find one by hand). Re-declaring for the same role auto-supersedes the prior
declaration (this is how you rotate which principal a role speaks for).

*Binding a role* — free non-empty organizational-role text, not a closed vocabulary (ratified
§9(c) — role naming is organizational configuration, not the harness's to impose):
```sh
$ ./led principal bind-role reviewer2 --role "sql-review"
```

*Granting competence* — the [safety-critical-logging BRIEF](../law/briefs/safety-critical-logging/BRIEF.md)'s
**G13 record** (that document's required-work-product entry for "who is believed competent for
what safety activity, at what band, on what basis" — a competence assignment or its change),
recordable but NOT gating (nothing in v1 refuses an act for lack of a matching grant):
```sh
$ ./led principal grant-competence reviewer2 --activity "sql-review" --band "B" --basis "track record on s37-s39"
```
Witnessed lifecycle (`seen-red/s41-principal-bindings-and-relations/red.txt`, case
`competence-lifecycle`): *"grant OK (view: 'sql-review|B'); duplicate refused; empty band
refused (1); re-band via --supersedes replaced (band now 'A'); stray --band on withdrawal
refused; STALE supersession target refused; withdrawal OK (view 0 rows, raw 3 rows -- grant+
re-band+terminal withdrawal); raw inactive-from-birth refused by the kernel CHECK"*. The band
and basis fields are free text — the spec's own ratification (§9(g)) calls this a **placeholder
architecture only, not a considered final design**; do not read the free-text shape as a
settled judgment that a closed band vocabulary (ASIL/SIL/DAL-style) is never coming.

*Relating two principals* — the closed vocabulary is `acts-for`, `dispatched-by`,
`same-natural-person`, `succeeds`:
```sh
$ ./led principal relate reviewer2 acts-for reviewer3
```
Self-edges refuse at the kernel, both via the CLI and via a raw direct write
(`seen-red/s41-principal-bindings-and-relations/red.txt`, case `self-edges-refused`: *"all
four CLI self-edges refused=True; raw kernel-trigger self-edge exit=3 with the taught
text"*). `same-natural-person` is symmetric and canonicalized (stored lower-`id`-first
regardless of the order you type it), witnessed both orderings in case `snp-canonicalization`.

*Looking at what exists.* No dedicated `led principal list`/`show` verb ships in v1 — this is a
genuine gap, not a hidden feature (UNEXERCISED beyond the derived views themselves). The
sanctioned way to look today is the same "query the view directly" pattern the CLI already uses
internally for its own convenience reads (e.g. `led standing`'s own implementation is a plain
`SELECT * FROM standing_decisions`, per `bootstrap/templates/led.tmpl`): the human-readable
surface is the `principal_standing_current` view (name, class, standing, registered_at,
registrar, purpose — one row per principal); the binding surfaces are `principal_relations`,
`principal_role_bindings` (deliberately not `principal_roles` — that name is reserved for the
unrelated db-role↔principal binding view, `principal_role`), `principal_keys`, and
`principal_competences`. All four binding views show only currently-active, unsuperseded rows;
every retraction stays visible in the raw ledger history regardless.

*Suspending or revoking* — and the honest limit on getting back:
```sh
$ ./led principal suspend reviewer2 "on leave"
$ ./led principal revoke reviewer2 "compromised"
```
Writes under a suspended-or-revoked principal then refuse at the kernel (witnessed,
`seen-red/s40-principal-identity-events/red.txt`, case `revoke-refuses-writes /
successor-passes`: revoked write exit=3, successor registration exit=0, successor write
exit=0). **No v1 verb lifts a suspension or a revocation, for either kind, and if both are
ever written for the same principal, `revoked` always wins the reported standing regardless of
which order they landed in** (case `precedence-both-orders`: *"suspend-then-revoke reads
'revoked', revoke-then-suspend reads 'revoked'"*). The only way back to an active identity is
registering a fresh successor principal and recording the succession:
```sh
$ ./led register-principal reviewer2-successor model --purpose "reviewer2's replacement identity"
$ ./led principal relate reviewer2-successor succeeds reviewer2
```
This is a new identity, not a reinstated old one — a real, if heavier, escape hatch, disclosed
as a deliberate v1 limit rather than an oversight.

**Can I use GPG to sign roles / authenticate myself as a principal?**
Answering exactly what was asked, in three honest parts — this is not a recommendation to go
generate a key; the standing deferral on key generation ("key generation/signing deferred until
all else banked; never re-raise as recommendation") is the maintainer's own ruling to lift, not
this page's to nudge him toward.

*(1) What exists now.* `led principal bind-key <name> --fingerprint "<fp>"` records an OpenPGP
v4 fingerprint against a HUMAN principal — a typed, dated, countersignable ledger row (a
`principal_key_bound` event), refused outright on any non-human subject
(`seen-red/s41-principal-bindings-and-relations/red.txt`, case `key-binding-polarity`: *"model
bind exit=3 (taught); human bind exit=0, view rows=1; malformed fingerprint exit=3 (kernel shape
CHECK named)"*). That is the whole of what's built: an empty-until-ceremony slot. **Nothing
anywhere verifies a signature against it.** "Signing a role," as a cryptographically verified
act, does not exist in v1 — a role binding (`led principal bind-role`) is an attributed,
countersignable ledger row, exactly like every other kind this project records; it is never a
signed object, and `bind-key` does not change that for any other kind.

*(2) What actually exercising this for real would require.* No maintainer keypair exists
anywhere in this project today —
[law/keys/README.md](../law/keys/README.md) states its directory's state plainly:
`AWAITING-KEY`, "no real maintainer keypair has been generated as of this writing." Rung 1 (the
signed-tag mechanism this directory backs) is built; it has never been armed. Exercising
`bind-key` for real, rather than against a throwaway test key, needs the one-time key generation
the maintainer's own standing ruling has deferred. If he chooses to lift that deferral, the
recipe is [design/MAINT-GPG-TRUST-LAYER.md](MAINT-GPG-TRUST-LAYER.md) §7 (`gpg
--full-generate-key`, hardware-backed preferred so each signature costs a physical touch), then
`led principal bind-key <name> --fingerprint "<the generated fingerprint>"`. The ceremony shape
that DOES already exist today, on top of that binding, is an ordinary countersign — a review row
regarding the binding event, using the same verb every other ledger row is countersigned with:
```sh
$ ./led review <bind-key-row-id> attest technical "fingerprint verified against a witnessed key-signing party"
```
(`led review`'s independence argument requires a stamp-distinct invocation for anything above
`self-review` — see the verb's own usage text in `bootstrap/templates/led.tmpl`.) This closes
the loop the panel deployment's own invented proposal→countersign ceremony needed, with zero new
review machinery — the binding event is just another countersignable ledger row.

*(3) The honest limit.* Binding a fingerprint records custody of a key against an identity — it
does not authenticate sessions, and it does not make `bind-key` a login mechanism. The HMAC
stamp (`kernel/lineage/s17-stamp-mechanism.sql`) remains the tripwire that answers "which live
invocation wrote this row"; the key slot answers a different, narrower question ("who does this
fingerprint belong to"), and answers it only once someone actually signs something and a
verifier checks that signature — which nothing in this project does yet for a role or a
principal binding. Signature-*verified* acts are a future rung, not this one.

## Typed verdicts and refusal recording (s42/s43)

Like the principal-identity entries above, these three entries deviate from this page's usual
point-elsewhere convention (full witnessed output, not a one-liner plus a pointer) because the
surface is new: kernel deltas s42/s43 turn a refused write from a transaction that leaves no
trace into a committed, attributed ledger row, and widen the tamper-evidence hash chain to cover
every column instead of thirty. Delivery record:
[orchlog.d/s42-s43-typed-verdicts.md](../orchlog.d/s42-s43-typed-verdicts.md); full spec:
[FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md](FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md).

**Prominent caveat, read before typing anything below:** none of this exists in a world whose
[birth chain](../GLOSSARY.md#birth-chain) predates commits `1fc4e8c` (s42) and `84729de` (s43) —
runs are strictly linear, so an already-scaffolded world gains nothing here. Run `./migrate
<deployment-dir> --dry-run` to see whether your world has s42/s43; if it names them as missing,
everything below is unavailable until your next real world is born on a checkout that carries
these commits.

**What happens now when a write is refused?**
Before s42/s43, a refused write was a `RAISE EXCEPTION` that aborted the transaction — the
attempt itself left no trace anywhere but a server log. After s43, the granted database role
holds NO `INSERT` privilege on any kernel-governed table at all; every write goes through one of
four functions (`kernel.ledger_write`, `review_write`, `registration_write`,
`obligation_write`), and a refusal caught inside one of them is committed as an ordinary
`write_refused` ledger row and handed back to the caller as a typed verdict — never a silent
abort. Witnessed (`seen-red/s43-typed-verdict-write-boundary/red.txt`, case 1): a write attempted
under a revoked principal returns

```
disposition=refused, sqlstate=P0001, refusal_id=<row id>
message: "Ledger policy: strict attribution (s40) — actor principal N is revoked ..."
```

and the ledger holds a COMMITTED `write_refused` row you can look at like any other row —
`refusal_sqlstate=P0001`, `refusal_surface='ledger'`, `refusal_attempted_actor=<the revoked
principal's id>`, `refusal_attempted_role='bork'` (the server-witnessed `session_user`, never
something the client asserted), `actor=<the write-boundary tool principal>` (never the attempted
actor itself — a refused principal cannot honestly author the record of its own refusal), and a
64-hex `refusal_payload_digest` (a SHA-256 of the attempted payload — the payload's actual
content is never stored, digest only, R4 ratified for poison/privacy reasons). The row that was
attempted never lands; only the record that it was attempted, and refused, does.

**To look at `write_refused` rows directly:** they are ordinary ledger rows like any other, so
the same `psql`/`led show`/`./led` reading tools that work on any other row work here —
`kind = 'write_refused'` is the row to filter on, and the six `refusal_*` columns above are
where the detail lives. There is no dedicated `led` verb for this in v1 (a genuine gap, not a
hidden feature), so reading them today means a direct query or `./led show <row-id>` once you
have an id — e.g. from `./verify-chain`'s own reconciliation output (next entry) or from
scanning recent rows.

**The plain point worth internalizing: probing attempts leave traces now.** An agent (or a
person) trying a write it is not permitted to make — writing under a revoked identity, attempting
a malformed payload, retrying a refused registration — used to vanish into a rolled-back
transaction with nothing durable behind it but a server log line. After s42/s43 it does not
vanish: it becomes a permanent, attributed, hash-chained, countersignable row, exactly as durable
as a row that succeeded. This is true of ceremony refusals too, not just plain ledger writes —
review-ceremony refusals, registration-ceremony refusals (a duplicate name, a missing
`--purpose`), and malformed-payload refusals (an unknown key, a server-owned key, a bad value
cast) all journal the same way, as one `write_refused` row per refused attempt
(`seen-red/s43-typed-verdict-write-boundary/red.txt`, case 1).

**Two things this does NOT do, stated so the guarantee is not over-read.** A raw `INSERT`
attempted directly against `ledger` by the granted role never reaches the boundary at all — it
fails at the database privilege layer first (`permission denied for table ledger`, SQLSTATE
42501, witnessed case 2) and is NOT journaled as a `write_refused` row; its only residual trace
is the Postgres server log, which rotates. And a database superuser or schema owner can always
bypass every trigger and privilege check here — that bound is unchanged by this delta, and the
closing move against it remains a GPG-signed chain head (`verify-chain --head`), covered in
"Trust ceremonies" below.

**What does `verify-chain` check now?**
Two things changed, and a third check is new.

*Full coverage.* The one function the whole tamper-evidence chain rests on,
`compute_row_hash`, used to serialize only thirty of the ledger's columns (the set as of
2026-early kernel deltas) — every column added since then, twenty-two of them including all
twelve principal-identity columns, sat OUTSIDE the hash chain: a schema-owner tamper of, say,
which principal a revocation regards changed no hash, and `./verify-chain` reported the chain
`INTACT` right over the rewrite. Witnessed live, this exact scenario
(`seen-red/s42-row-hash-full-coverage/red.txt`, case 1):

```
verify-chain: INTACT -- 4 row(s) walked, head id=4 hash=<64-hex>
(exit 0)
```

— reported clean, immediately after an owner tampered `work_parent` on a committed row with
triggers disabled. After s42, `compute_row_hash` covers every ledger column except `row_hash`
itself (52 at the s42 head, 58 once s43's own six new columns are included), and the same class
of tamper is now caught (case 2, witnessed on all 52 columns individually, not sampled):

```
verify-chain: BROKEN -- first break at row id 19:
    stored:   <64-hex, the pre-tamper hash>
    expected: <64-hex, recomputed over the tampered content>
  (1 of 20 row(s) mismatch total. ...)
(exit 1)
```

*The completeness oracle — the `refusal_seq` reconciliation.* A non-transactional sequence
(`kernel.refusal_seq`) is bumped immediately before every `write_refused` row is journaled;
because a Postgres sequence's `nextval` is never rolled back, it counts every refusal attempt
that reached the boundary regardless of what happened to the surrounding transaction.
`./verify-chain` now compares the count of committed `write_refused` rows against this sequence.

*What `BROKEN` vs `FORGERY-SUSPECT` mean, and what to do on each* — drawn from the delta's own
guidance, stated plainly where the header gives no further operator action:

- **`BROKEN`** (a row's stored hash disagrees with a fresh recomputation over its own content,
  the ordinary chain-tamper report shown above): a row's content was altered after the fact.
  The delta's own header gives no remediation beyond the standing chain-integrity posture — this
  is a serious finding. **The disposition is: stop and consult, not improvise.** Do not attempt
  to "fix" a broken chain by editing rows or regenerating hashes yourself; treat it as evidence
  and escalate to whoever owns the world's integrity posture.
- **`FORGERY-SUSPECT`** (`REFUSAL-ORACLE-FORGERY-SUSPECT`, when the count of `write_refused`
  rows EXCEEDS what the sequence counted): only the boundary functions can mint a
  `write_refused` row through the sanctioned path — a payload that tries to claim
  `kind = 'write_refused'` directly is refused with a forgery-channel teach-text. This verdict
  means a `write_refused` row exists that the counting mechanism never saw mint — i.e. it was
  forged outside the sanctioned path (an owner-side direct INSERT bypassing the boundary
  entirely). Witnessed (`seen-red/s43-typed-verdict-write-boundary/red.txt`, case 3):
  ```
  verify-chain: REFUSAL-ORACLE-FORGERY-SUSPECT -- N journaled write_refused row(s) but
  the sequence only counted N-1 ... (exit 6; --head REFUSES)
  ```
  Same disposition as `BROKEN`: **stop and consult** — this is not a state to self-remediate,
  and `--head` itself refuses to sign over it. The opposite inequality (sequence count HIGHER
  than the row count) is NOT this failure — it is EXPLAIN-grade, with legitimate named causes
  (a client-side transaction that wrapped the boundary call and rolled it back; a journal-insert
  double failure) and does not, by itself, indicate tampering.
- `write_refused` rows are also unretractable by rule: nothing may supersede one (R6, ratified).
  If you see a row attempting to supersede a `write_refused` row, that attempt is itself refused
  and journaled — it is not a state `verify-chain` needs a separate disposition for, because it
  cannot succeed in the first place.

## Standing lifecycle (s45)

Like the two sections above, this one deviates from the page's usual point-elsewhere
convention because the surface is new: kernel delta s45 gives two governance states — a
db_role's standing declaration, and a principal's suspension — a sanctioned way OUT, where
before s40/s41 there was only a way in. Delivery record:
[orchlog.d/s45-standing-lifecycle.md](../orchlog.d/s45-standing-lifecycle.md); full spec:
[design/FABLE-STANDING-LIFECYCLE-SPEC.md](FABLE-STANDING-LIFECYCLE-SPEC.md).

**Prominent caveat, read before typing anything below:** none of this exists in a world whose
[birth chain](../GLOSSARY.md#birth-chain) predates commit `94f5b7a` — runs are strictly linear,
so an already-scaffolded world gains nothing here. Run `./migrate <deployment-dir> --dry-run`
to see whether your world has s45; if it names it as missing, the two verbs below are
unavailable until your next real world is born on a checkout that carries this commit.

**What does "unbind" mean, and what do I type?** A db_role's standing declaration (the
"anonymous writes on this connection count as principal X" default that
`./led principal declare-standing` sets) can be repointed to a different principal any number
of times, but before s45 it could never be turned OFF — the only escapes were suspending the
bound principal (which blocks that identity on every channel, not just this role) or pointing
the role at a fabricated tombstone principal (a real misattribution risk). s45 adds a
sanctioned third way:

```sh
$ ./led principal undeclare-standing
```

(`--db-role <role>` is only needed if you are unbinding a role other than your own
deployment's connection role — the common case needs no flag.) After this, an anonymous write
on that role (no `LED_ACTOR` set) refuses again, exactly as it would on a role that was never
declared for — a fresh `./led principal declare-standing <name>` re-binds it. **This is
forward-only**: rows already written under the old declaration keep their old attribution
forever. If the reason for unbinding is that past rows were misattributed, that is a job for
the defeat pipeline below (a mismatch attestation, not a retroactive rewrite) — nothing in
s45 touches history.

**What does "suspension is liftable" mean, and what do I type?** Before s45, `./led principal
suspend` had no reverse — suspension degenerated into a soft, permanent revocation in
practice, even though the vocabulary implied it was temporary. s45 makes it genuinely
reversible:

```sh
$ ./led principal suspend reviewer2 "on leave"
$ ./led principal lift-suspension reviewer2
```

Once lifted, `reviewer2`'s writes are accepted again. **Revocation stays terminal by type —
this is the other half of the same delta: it was always a disclosed design limit, and it is
now enforced by the kernel itself, not merely unbuilt.** There is no verb, in this or any prior version, that reverses a
revocation: a lift-shaped revocation row is structurally unrepresentable (the same
`principal_binding_active` flag that suspension uses is refused outright on the revoked kind),
and a kernel-level supersession rule refuses any attempt to hide a revocation behind an
unrelated superseding row. `lift-suspension` on a principal that is both suspended and revoked
still writes the lift (and warns that standing stays `revoked`, because revocation dominates
suspension in the reported standing) — it changes nothing about the revocation. The only way
back from a revocation remains what s40/s41 already gave you: register a fresh successor
principal and record `./led principal relate <new> succeeds <old>`.

**Does lifting a suspension restore credit for what the principal wrote while suspended?**
No, and this is worth internalizing before it looks like a bug: standing (suspended, revoked,
active) never conditions defeat. Suspending or revoking a principal gates its *future* writes
only; it never withdraws or discounts anything that principal already wrote, and lifting a
suspension changes nothing about which of its past rows are credited. The only sanctioned
lever over whether a specific row is credited is a mismatch attestation under the defeat
pipeline, covered in the next section. This was a maintainer ruling (ledger row 1481,
2026-07-18), named here because a future reader who notices a suspended principal's old work
still counting is looking at the design, not a defect.

**EXISTING WORLDS GAIN NOTHING HERE, restated because it matters most.** Both mechanisms above
are authored, scratch-witnessed, and wired into the scaffold's lineage chain only — they reach
reality solely at a *future* world's birth. If your world predates `94f5b7a`, `undeclare-standing`
and `lift-suspension` are not verbs your `led` script has; `./migrate --dry-run` will name
`s45-standing-lifecycle` among the missing deltas.

**Honest limits.** A schema owner/superuser can bypass every trigger this delta adds, the
standing disclosed bound every kernel delta carries. The duplicate-active suspension guard is
CLI-side, so a direct (non-CLI) writer can still stack multiple suspensions on one principal,
each then needing its own lift. And in a solo world whose only active principal is suspended,
lifting that suspension needs a *second* active principal to write it — s45 narrows this
dead-end from "impossible" to "needs one more registered principal," but does not close it; a
truly solo, fully-suspended world still needs a schema-owner act to recover.

## Model identity: watchdog, attestation, defeat

Three pieces landed together as one arc, answering "if a session's serving model gets silently
substituted, how would I know, and what happens to what it already wrote?" Delivery record:
[orchlog.d/defeat-pipeline-and-otel-identity.md](../orchlog.d/defeat-pipeline-and-otel-identity.md);
full specs:
[design/FABLE-OTEL-SENTRY-SPEC.md](FABLE-OTEL-SENTRY-SPEC.md) (including its dated A1/A2
amendments) and
[design/FABLE-DEFEAT-PIPELINE-SPEC.md](FABLE-DEFEAT-PIPELINE-SPEC.md) (including its dated A1
amendment).

**Read this once, before anything else on this topic: none of it is a guarantee.** Every layer
below — the watchdog, the attestations, the defeat derivation — authenticates a *pipe* (a
process, a channel, a database write path); nothing anywhere authenticates the emitter's
honesty, because the model-identity string originates inside the unauthenticated CLI process
itself. This is stated plainly in the sentry spec's own §7 standing rebuttals and carried
forward here rather than oversold: everything on this page is audit-supporting
evidence, never authentication (in NIST 800-53 terms, for readers who want the mapping: the
AU control family, never IA-2). A dishonest or silent session is observed as nothing and
defeats nothing — absence of telemetry proves nothing, permanently, in either direction.

**How would I actually notice a model substitution as it happens?** The watchdog
(`otel-watch`) is a small always-on process that tails the local OTel collector's export and
compares each request's observed model against the session's declared expected model; on a
mismatch it calls a mail-notification script (on this host, the maintainer's own
`notify.py`, the one that already makes his phone beep on turn completion — if you are not
him, wire your own notifier there; the watchdog just executes the configured script), so a
substitution surfaces within seconds rather than at the next audit. It writes nothing to the ledger — it is notification, not evidence. A session with no
declared expectation is reported as *unwatched*, loudly, so you can never mistake silence for
"watched and clean." **UNWITNESSED for this page:** the watchdog's own witness legs were not
re-run to produce this entry; treat its behavior as spec'd, not freshly observed here.

**How do I get a post-hoc, ledger-recorded answer for rows already written?** `./otel-attest`
is a batch verb (not a daemon) that correlates ledger rows against the collector's export and
writes one defeasible attestation row per attributable row, at one of four closed confidence
grades naming the strength of the join that earned it:

- `exact-command` — the row's own command is tied to one specific, bracketing request.
- `turn-bracketed` — command detail unavailable, but every request in the row's turn window
  agrees on one model.
- `session-scoped` — bracketing is ambiguous, but every request in the session's covering
  window still names one model.
- `ambiguous` — the window shows more than one model, or a load-bearing join failed. **As of a
  2026-07-18 spec amendment, an ambiguous attestation always writes `model=unresolved`** — never
  a fabricated single model, never an invented multi-model packing. The conflicting models are
  named in the row's `basis=` field instead. If every candidate in the window contradicts the
  declared expectation, the verdict is still `MISMATCH` (which model is unclear, but the
  substitution is not); if at least one candidate matches, the verdict is `unevaluated`; an
  ambiguous row is never written `match`. Two edge cases (the spec's A1 addendum): an
  *empty* candidate window — ambiguity via join failure, nothing in evidence at all — is
  `unevaluated`, never MISMATCH (zero evidence proves nothing); and a session with no
  declared expected model is also `unevaluated` — there is nothing to contradict.

No row is written at all when no correlated telemetry exists — absence of events is never
treated as evidence.

**A MISMATCH or ambiguous attestation is easy to miss if you only look at attestation rows —
does it surface anywhere else?** Yes: any attestation whose verdict is `MISMATCH` (including an
`ambiguous` row whose verdict resolves to `MISMATCH` per the rule above) additionally writes a
companion `finding` ledger row, so it lands in ordinary review flow instead of sitting quietly
in attestation bulk.

**What happened to `./otel-attest`'s first build, and is it safe to use now?** It was
adversarially reviewed (ledger row 1505) and found to silently fold every `ambiguous` case into
the write-nothing path — the opposite of the spec's own rule. The verb was held out of service
until the fix landed (commit `c3301e5`) and is back in service now, with the `model=unresolved`
behavior above, plus a write-time refusal on any field value containing a `|` or newline (an
unauthenticated model string could otherwise corrupt the row's later parse).

**How do I see what a MISMATCH actually does to derived standing?** `./judge --layer defeat`
derives it: a ledger row backed by an unsuperseded mismatch attestation, written by a principal
holding an unsuperseded, active competence grant for `model-identity-attestation`, is excluded
from the `credited` reading, computed fresh by two independent producers (a SQL twin and an ASP
program) required to agree bit-for-bit. Nothing is edited or deleted — a defeated row stays
fully visible in raw history, always shown together with its cause. **WITNESSED**, run
read-only against this repository's own live world (2026-07-18):

```sh
$ ./judge --layer defeat
```
```
# marriage differential -- layer='defeat'
#   closed verdict vocabulary: ['AGREE', 'DIVERGE_BY_DESIGN', 'DIVERGE_DEFECT', 'QUARANTINED']; RED = ['DIVERGE_DEFECT', 'QUARANTINED']

  [!! ] autoharn1 QUARANTINED        asp=0 sql=0 atoms; Δasp=[] Δsql=[]
          asp QUARANTINED: EDB export failed: CapabilityError: target 'autoharn1' did not emit trust_grant/n (capability absent): no principal_binding_active/principal_competence_activity columns on this schema (pre-s41 lineage) -- capability absent, not record-empty. A silent empty here would be the F49 vacuous-pass; refusing loudly.
          sql QUARANTINED: EDB export failed: CapabilityError: target 'autoharn1' did not emit trust_grant/n (capability absent): no principal_binding_active/principal_competence_activity columns on this schema (pre-s41 lineage) -- capability absent, not record-empty. A silent empty here would be the F49 vacuous-pass; refusing loudly.

# DIFFERENTIAL RED -- a target diverged/quarantined (NO RESULT)
```

This is a QUARANTINE, not a bug: the defeat pipeline needs typed competence grants (s41) to
derive anything, and this repository's own live world predates s41, so both producers refuse
loudly with the same named reason rather than silently reading an empty derivation as "nothing
is defeated" — the exact vacuous-pass mistake this design forecloses on purpose. A world whose
birth chain carries s41 or later will derive real `credited`/`model_defeated` results here
instead of this refusal.

**Does suspending or revoking the attesting principal change what it already defeated?** No —
see "Standing lifecycle (s45)" above: standing never conditions defeat, by ratified rule. A
suspended or revoked principal's past mismatch attestations, under a still-in-force competence
grant, keep defeating exactly as before; only superseding the grant or the attestation itself
changes what is credited.

**Honest limits, carried forward rather than oversold:**

- The ceiling is permanent, not a v1 gap: nothing here can ever prove which model served a
  request, only observe and record what the emitting process claimed. The sentry spec names the
  one thing that would close this — provider-side response signing — and it does not exist.
- The watchdog fails silent on its own death or a mail failure; a `--heartbeat` option is an
  opt-in mitigation, not a default.
- The typed kernel form of an attestation (kernel delta `s44`) and its dedicated credited-read
  views are authored in the specs above but not yet in any birth chain; until an s44+ world
  exists, `./otel-attest`'s rows are ordinary `verification` rows, and the engine-side
  computation shown above is the only way to see `credited`/`model_defeated` at all.
- A malformed attestation row halts derivation for its whole target until it is superseded —
  deliberate (fail loud beats skip silent), but a real operational cost if it happens.

## Trust ceremonies

**Can I prove a commission really came from me?** (a "commission" here is a ledgered
instruction attributed to a principal — the maintainer or an agent acting for them — and the
question is how strongly that attribution can be trusted). Full grammar and worked walkthrough:
[USER-GPG-TRUST-LAYER-FAQ.md](USER-GPG-TRUST-LAYER-FAQ.md) §5–§7.
Yes, and it comes in three increasing strengths: **LAZY** (the row's stated actor is taken on
its word, no cryptographic or structural check), **FULL** (the right actor recorded on the row,
plus the absence of the interception stamp a hook adds only when an agent — not the maintainer
directly — wrote the row: a rebuttable presumption, not proof), and **SIGNED** (a detached GPG
signature over the row, checked against a known key — the only strength that survives a
dispute). The standing rule is that a **CONTESTED** commission (one whose attributed actor is
disputed after the fact) must be SIGNED to stand. You can rehearse every ceremony with a
throwaway key before any real key exists.

**Can I anchor the ledger so later tampering is provable?**
Yes — sign the chain head at run close (`verify-chain --head`, then a detached signature).
Any retroactive row alteration then breaks provably against a head your key vouches for;
the head also carries the apparatus-config hash, so a mechanism flipped off between two
signed heads is provable by comparing them. Known honest limits: the chain-hash mechanism proves
tampering with rows *between* two signed heads, but a deleted row at the very tail of the chain
(the newest end, appended after the last signature) is invisible to the chain alone — nothing
has signed over it yet (tracker item `s26-tail-deletion-witness` holds the designed fix — a
ledger row, not a committed page: `./led show s26-tail-deletion-witness` at the repository root
reads it), and the
apparatus comparison is manual, not auto-flagged.
Walkthrough: [USER-GPG-TRUST-LAYER-FAQ.md](USER-GPG-TRUST-LAYER-FAQ.md) §6.

## Review discipline

**Is a review's content ever checked, or does any countersign discharge the obligation?**
Partly. [`review_gap`](../GLOSSARY.md#review_gap)'s own discharge test never looks at what a
review says — any unsuperseded, distinct-actor `attest` clears the obligation regardless of
content, by design. A separate, layered check DOES inspect the discharging review's own
statement: `./audit --review-gap` flags a discharge whose whitespace-normalized statement is
shorter than `CONTENT_FREE_STATEMENT_THRESHOLD` (40 chars,
[engine/review_gap_thresholds.py](../engine/review_gap_thresholds.py)) — the case this check
answers to was a real 4-char `"test"` review that silently discharged a genuine obligation.
Honest limit, in the check's own vocabulary: it is a length heuristic, so its verdict is
`FLAGGED`, never `VIOLATED` — a genuine terse review passes ("Confirmed, matches row 4's stated
criteria exactly." is 51 chars) and hollow-but-plausible prose of ordinary length ("Reviewed and
everything looks correct, no issues found, approved for merge.") is NOT caught; the check catches
the "test"-shaped instance, not the class, and never substitutes for a human reading the review.
This exit code (6) is reachable only through `--review-gap`, and only when nothing earlier
already raised the exit and at least one review is flagged. Witnessed both polarities:
[seen-red/content-free-review-audit/](../seen-red/content-free-review-audit/).

**How do I make an implementation step mechanically wait on a review step, instead of relying on
remembered discipline?** Arm `decomposition_review` — a third, independent PreToolUse mechanism in
[hooks/pretooluse_change_gate.py](../hooks/pretooluse_change_gate.py), alongside `change_gate`
(the ticket/window check) and `permit_to_work` (the open-claim check). It exists because a claimed,
open work item proves *permission* to work, never that the item's own decomposition — its plan, its
acceptance criteria — was ever looked at by anyone but its author: on this project's own record, a
claimed task's implementation began six seconds after claim, roughly 2.5 minutes ahead of the
countersign verdict that was supposed to gate it (the run12 specimen, named in the hook's own
docstring). A serious adopting organization should read that specimen as a *class*, not a one-off:
any harness that lets an agent dispatch straight from "plan accepted in principle" to "editing files"
carries the same race, and self-disclosed recurrences of exactly this shape are on record upstream
too, filed as [anthropics/claude-code#77900](https://github.com/anthropics/claude-code/issues/77900).
`decomposition_review` closes it by refusing a substantive `Write`/`Edit`/`NotebookEdit` — or a
governed-file-mutating `Bash` command — anywhere under the world's root while the claimed work
item's own opening act (`work_opened`) carries an undischarged
[`countersign_obligation`](../GLOSSARY.md#obligation): the same [`review_gap`](../GLOSSARY.md#review_gap)
discharge test every other obligated row already uses, not a second hand-rolled predicate.

Arming it is three steps, and none of them is optional-by-omission — a world that skips any one of
the three is unarmed, silently:

1. **Obligate the actor whose decompositions need outside eyes:**
   `./led obligate decomposition-review <reviewer-principal> <worker-principal>` (the worker is the
   *obliged* actor — get the direction backwards and you obligate the reviewer instead, a mistake
   this project's own `led obligate` usage text calls out by name because it has happened twice).
   **Second warning, repeated here at the copy point because the CLI's usage text carries it and
   this recipe previously did not** (a downstream deployment caught the omission before arming,
   2026-07-17): the `decomposition-review` word above is a free-text LABEL, not a filter —
   `review_gap` joins on actor identity alone, so once a principal is obliged, EVERY
   uncountersigned row that principal writes, of any kind, accumulates review-gap debt until a
   distinct actor countersigns it. Obliging a session's general working identity (the `author`
   that writes every `decision`/`finding` row) makes nearly every row that session writes need a
   countersign — an operational cost far larger than the label suggests. The narrower recipe that
   bounds the blast radius: register a dedicated principal used EXCLUSIVELY to open
   decompositions (`LED_ACTOR=<dedicated-name> ./led work open ...`), and obligate that. The
   bound holds only as long as the dedicated principal is never reused for other writes — the
   over-catch returns the moment it is.
2. **Flip the mode to `enforce`** in `.claude/apparatus.json`:
   `"mechanisms": {"decomposition_review": {"mode": "enforce"}}` — see
   [bootstrap/templates/APPARATUS.md](../bootstrap/templates/APPARATUS.md) for the full switchboard.
3. **Verify it is actually armed before trusting it.** `led decomposition-review-status` is the
   purpose-built verb for this — it prints the resolved mode, the obligation-table row counts, and a
   one-line verdict (`ARMED-ENFORCING` / `ARMED-OBSERVING` / `VACUOUS` / `OFF`) — but as of this
   writing it exists only on the unmerged `build/effective-state-display` branch, not yet on this
   page's own base; check its own repository state before assuming it is present in yours. Until it
   lands, or if it has not landed in your checkout, read the same two raw facts by hand: (a) `cat
   .claude/apparatus.json` for `mechanisms.decomposition_review.mode` (missing entirely means the
   mechanism's own default, `observe`, applies — see below); (b) `./led review-gap`, cross-read
   against `./led work list` for which slug is currently open and claimed — if that slug's
   `work_opened` row appears in the `review-gap` output, the obligation is live and undischarged.

**The shipped default is `observe`, not `enforce` — deliberately, and unlike its two sibling
mechanisms.** `change_gate` and `permit_to_work` both default to `enforce` because they are free per
call and were already the project's steady state before per-mechanism modes existed.
`decomposition_review` is new machinery: an already-running, already-scaffolded world would find its
writes newly gated the moment `hooks/` is updated, with no operator opt-in — so this one mechanism
defaults to the weaker mode on purpose, and arming it to `enforce` is a one-line, per-world decision
an operator makes deliberately (see the module docstring's own "DECOMPOSITION-REVIEW BLOCKER"
section for the reasoning in full). A serious adopting organization should read this the same way:
the mechanism ships inert everywhere, and an unarmed world is not a bug, it is the honest starting
state — arming it is a policy choice belonging to whoever owns the world, not something a scaffold
should spring on a project mid-flight.

**What is, and is not, witnessed for this mechanism specifically.** PreToolUse hooks demonstrably
fire on a dispatched subagent's own tool calls — 24 specimens of `change_gate` (this same script,
this same invocation path) denying a subagent's edit are recorded in the upstream autoharn ledger,
decision row 1295 (2026-07-17 two-spy synthesis); the underlying session transcripts remain local
evidence per the project's auditability ruling — the ledger row is the citable record. What had
NOT been separately witnessed, because every previously-observed world carried zero
`countersign_obligation` rows under the shipped `observe` default, is `decomposition_review` itself
actually blocking anything. A scratch world (`decompprobe`, scaffolded via
`bootstrap/new-project.sh --new-world`, torn down completely afterward) closes that gap directly:
with a claimed work item's decomposition obligated and the mode flipped to `enforce`, invoking
`hooks/pretooluse_change_gate.py` with a real `PreToolUse` `Write` event on stdin produced

```
Ledger policy (decomposition-review-blocker): work item 'probe-task' (work_opened row 2) carries an
undischarged decomposition-review obligation — executing a claimed work item before its OWN
decomposition is countersigned makes every subtask a bet on an unreviewed plan (the run12 specimen:
task 1's implementation began 6 seconds after claim, ~2.5 minutes ahead of the countersign verdict
that was supposed to gate it). Discharge it, THEN retry the same edit: ...
```

(exit code 2, `permissionDecision: "deny"`). Discharging the obligation — a distinct-actor
`self-review` countersign, disclosed as such (the solo-world fallback this project's own scaffolded
`CLAUDE.md` documents) — and re-issuing the byte-identical event then produced exit code 0 with no
deny output at all: the same claimed item, the same edit, only the obligation's discharge state
changed. Flipping the mode back to `observe` and re-issuing the same event against a fresh
undischarged obligation produced `permissionDecision: "allow"` with an `additionalContext` field
opening `[apparatus observe-mode WARNING — would DENY under enforce] Ledger policy
(decomposition-review-blocker): ...` — the warn-not-block contrast, same check, same undischarged
state, only the mode differed. **What closes the crux is the composition of these two witnesses, not
either alone**: the ledger-recorded subagent specimens (decision row 1295) establish that this hook
script fires on a dispatched subagent's own tool calls at all; this scratch-world test establishes that
`decomposition_review`'s own deny path, once armed, actually fires for an undischarged obligation.
Neither witness alone would close it — the subagent specimens never exercised `decomposition_review`
armed, and this test never dispatched through a subagent.

**Should compliance review run per-commit or per-changeset?**
Per-changeset, at minimum — one reviewer reading the entire multi-commit changeset against the
LAW together, rather than one reviewer per commit checking each commit in isolation. The
reason is not caution for its own sake: a defect can live entirely in the INTERACTION of two
individually-correct commits, and no per-commit review ever sees that interaction, because
each commit, read alone, is fine.

The witnessed specimen (via decision row 1295's two-spy synthesis, citing the autoharn-panel
deployment's own row 590, named here only as history): a backend commit that validated
`limit=0` as a rejected input, and a frontend commit that messaged that same `limit=0` case to
the end user, landed about a minute apart as two separate commits. Each commit was correct in
isolation — the backend validation was sound on its own, the frontend messaging was sound on
its own — and the pairing was a regression, caught only because the review that found it
spanned both commits together, not because either commit's own review flagged anything.

Honest trade-off, stated plainly rather than left implicit: a whole-changeset review costs more
context per review round (the reviewer holds every commit in the set at once, not one at a
time) and arrives later than a per-commit review would (it waits for the changeset to close
rather than firing on each commit as it lands). The recipe is span-at-least-the-changeset for
LAW/compliance review — not never-review-early; a fast per-commit pass can still run as a first
filter, but it is not a substitute for the changeset-spanning pass, which is the only one
positioned to catch an interaction defect between two commits that are each correct alone.

**How do I make sure an item can't be started before its preconditions are met?** The maintainer's
own question, verbatim: "do we have some kind of way to ensure that items ... are not 'opened' or
'started' until preconditions are met? So that a hook can tell the agent 'don't do that, do the
right thing instead'?" Three separate mechanisms answer three separate moments in a work item's
life — none of them alone is the whole answer, and knowing which moment each one guards is the
point of this entry.

1. **`--type blocks-start` (claim-time, kernel/lineage/s39-blocks-start.sql).** `./led work depends
   <slug> <on-slug> --type blocks-start` records that `<slug>` may not be CLAIMED until `<on-slug>`
   reaches CLOSED. `./led work claim <slug>` is refused at construction while any direct,
   in-force blocks-start antecedent is unresolved, naming every unresolved antecedent by slug —
   the exact "don't do that" refusal the maintainer's question asks for, fired at the moment work
   would actually begin. `./led work startable` lists every open, unclaimed item with no such
   refusal pending right now — the "what can I legitimately start" query. Honest limits: direct
   antecedents only, not a transitive walk (an item three hops upstream of an unresolved
   precondition is not itself refused — widen `work_item_blocks_start_blockers` if you need that);
   and it binds only the ledger's OWN claim path — an agent that edits files without ever running
   `./led work claim` never trips this refusal at all (see point 3).
2. **`decomposition_review` (write-time, the armed mechanism).** Already covered in full under
   "Review discipline" above — a *claimed, open* work item only proves permission to work, never
   that its own decomposition (the plan, the acceptance criteria) was ever reviewed.
   `decomposition_review` closes that different gap: it refuses a substantive `Write`/`Edit`/
   `NotebookEdit` (or a governed-file-mutating `Bash` command) while the claimed item's own opening
   act carries an undischarged `countersign_obligation`. This is a PreToolUse hook, not a ledger
   refusal — it fires on the *tool call*, not the claim.
3. **`--type blocks-close` (close-time, kernel/lineage/s30-typed-dependency-edges.sql).** The
   oldest of the three: `--type blocks-close` refuses a `--strict` close (or the strict-by-type
   discharge of a composite item) while the antecedent is unresolved. It guards the *end* of the
   work, not the start — an item can be opened, claimed, and worked on with a blocks-close
   antecedent still unresolved; only its own strict close is refused.

**The composition point, stated plainly because no single mechanism above is complete on its
own.** Full structural foreclosure of "started before its precondition" is TWO gates together, not
one: **claim-gating** (point 1) for any work that goes through the ledgered `./led work claim` path,
**PLUS** the write-gate (point 2) for an agent that skips claiming and edits files directly. Neither
alone closes the class — a `blocks-start` edge with no `decomposition_review` armed cannot stop an
agent that never claims the item and edits anyway; `decomposition_review` armed with no
`blocks-start` edge recorded has no *precondition* fact to check at all, only a review-obligation
one. `--type blocks-close` (point 3) is a THIRD, later gate — closing time, not starting time — and
is not a substitute for either of the first two, though all three commonly apply to the same item
(an antecedent that must be finished before X starts is very often also load-bearing for X's own
strict close).

## Classifying audit/diagnostic findings

**I have a batch of findings from a code audit or review, and sorting them into categories
keeps producing overlapping or incomplete buckets — is there a standard way to do this?** Yes —
split every narrative finding (one that bundles more than one bug or observation) into single-
actionable-unit atoms first, with a provenance link back to where each atom came from, THEN
classify; once every unit is atomic, "did we cover everything" and "does nothing overlap" become
a one-line mechanical check instead of a manual sweep. A second pass then re-clusters the atoms
into
[fix-authorship blocks](ORCH-FINDING-ATOMIZATION-RECIPE.md#stage-2--reconstitute-atoms-into-blocks-author-fixes-at-the-block-grain-not-the-atomic-grain)
by shared invariant, so one typed fix forecloses a whole class of bugs
rather than patching each atom instance-by-instance. Full method, its adjudication against this
corpus, and its relation to
[ADR-0000's typed-fix discipline](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md):
[ORCH-FINDING-ATOMIZATION-RECIPE.md](ORCH-FINDING-ATOMIZATION-RECIPE.md).

## Documentation quality

**Can my project use the fresh-context documentation review loop autoharn uses on itself?**
Yes — this was asked as "is there a reason we can't?", and the answer was no: the reviewer
is an ordinary fresh-context subagent. Scaffolded projects get `./attest-doc`
(`record`/`check`), a project-local attestations ledger, and an opt-in DOC-ATTESTATION
section in `distance-to-clean` (the scaffold's own operator-facing report that prints how far
the deployment sits from a clean governance state; apparatus switch `doc_attestation`, default
off).
Walkthrough: [USER-DOC-AUDIT-LOOP.md](USER-DOC-AUDIT-LOOP.md); the loop's rules:
[ORCH-ABC-AUDIT-LOOP-RECIPE.md](ORCH-ABC-AUDIT-LOOP-RECIPE.md).

**I have known findings to verify AND I want a fresh legibility sweep — can one reviewer do
both?**
No — and this was learned the hard way (a real, dated 2026-07-13 anchoring defect in a live
deployment, not a hypothetical). A reviewer briefed with a known findings list *and* asked to also
sweep fresh anchors on the list — the sweep silently degrades into a second verification pass. Run
two separate reviewers: a targeted verifier (front-loaded with the list — correct there) and a
genuinely blind B (artifact + commission only, no findings, no mention a correction pass
happened). The same rule governs a co-signer/countersign briefing. Full account, with the
witnessed 0-versus-4-and-7 findings gap between confirmation-mode and adversarial-fresh reviews:
[USER-DOC-AUDIT-LOOP.md](USER-DOC-AUDIT-LOOP.md)'s "Briefing your reviewer" section.

## Operating rhythm

**How do I pick up work after a break?**
Start a fresh session and run `./pickup` — never resume or continue an existing one. The brief is derived
at pickup time from live ledger state; a stored handoff decays and replayed context is
the quadratic cost the ledger exists to replace. Card:
[ORCH-OPERATING-CARD.md](../ORCH-OPERATING-CARD.md).

**Can I turn a safety mechanism off, or make it observe-only? Will that be visible?**
Yes and yes — every mechanism is independently `off`/`observe`/`enforce` in
`.claude/apparatus.json`, live on the next tool call; and since 2026-07-12 every mutation
of that file is itself journaled (hashes, which modes changed), so a flip is witnessed
rather than silent. Full switchboard, per-mechanism defaults and costs:
[bootstrap/templates/APPARATUS.md](../bootstrap/templates/APPARATUS.md).

**A finished run's world turns out to have a defect. Can I patch it?**
No — runs are strictly linear; a superseded world is settled, read-only evidence. The fix
enters the next world via the scaffold (it usually already has), and the finding goes on
the ledger. This is a ruling, not a limitation looking for a workaround. Ruling text:
[../CLAUDE.md](../CLAUDE.md), ORCHESTRATION section.

## Your review queue

**Can I keep a ranked "things I need to personally look at" queue, and tick items off as I go?**
Yes — a `review:`/`review-done:` ledger row pair does this; it renders at every `./pickup`
under a `MAINTAINER-REVIEW-QUEUE` section. Unlike the `resource:`/`estimate:` grammars
elsewhere on this page, the grammar is written out here **in full**, not merely pointed at —
this recipe is its one documented home
([ADR-0005 Rule 1](../law/adr/0005-documentation-discipline.md), single source of truth per
fact), and it deviates from this page's usual "point elsewhere" convention on purpose so an
executive queue has a self-contained page to hand a first-time reader.

A queue entry is a `decision`-kind ledger row (the same kind `resource:`/`estimate:` ride, run
via `./led decision "..."`), validated at write time by
[`bootstrap/templates/led.tmpl`](../bootstrap/templates/led.tmpl) and rendered at pickup time
by the `MAINTAINER-REVIEW-QUEUE` section of
[`bootstrap/templates/pickup.tmpl`](../bootstrap/templates/pickup.tmpl) — both cite this
subsection by name rather than restating the grammar a second time
([ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md) P1).

**Opening or re-ranking an item:**

```
review: <SLUG> | <RANK> | <WHAT> | <POINTER>
```

The four fields, in order, separated by ` | ` (space-pipe-space):

- **SLUG** — a bare slug matching `^[a-z0-9][a-z0-9-]*$` (no spaces), the same shape
  `estimate:`'s TASK-SLUG field already uses. Identifies the item across its whole lifetime —
  opened, re-ranked, ticked off, and (if it recurs) re-opened.
- **RANK** — a positive integer (`1`, `2`, `3`, …), where `1` is the MOST important item —
  the queue's own sort key.
- **WHAT** — non-empty plain words: what you are reviewing, in a phrase a cold reader
  understands without opening the pointer.
- **POINTER** — non-empty: where to look. A repository path, a live-lookup command
  (`./led show 214`, run at the repository root), or a URL — whichever actually resolves for
  this item.

**Ticking an item off:**

```
review-done: <SLUG> | <DISPOSITION>
```

- **SLUG** — must match the same slug grammar `review:` uses (a `review-done:` for a
  slug-shaped-wrong SLUG is refused — there being nothing on record it could sensibly close).
- **DISPOSITION** — non-empty free text: what you decided, or what happened.

**Semantics — latest row per SLUG wins, append-only.** Nothing here is mutated or deleted; the
queue's state is *derived* from whichever row for a given SLUG has the highest ledger row id:

- The **latest `review:` row** for a SLUG is the one whose RANK/WHAT/POINTER render — so
  filing a new `review:` row with the same SLUG and a different RANK is how you re-rank an
  item (no supersedes flag needed; this is a simpler rule than `resource:`'s, deliberately,
  because a queue's whole point is a fast one-liner).
- A **`review-done:` row for a SLUG removes it** from the rendered queue — it is still on the
  ledger (append-only, nothing is ever deleted), just no longer printed as open.
- A **`review:` row filed AFTER a `review-done:` for the same SLUG re-opens it** — the same
  latest-row-wins rule applied uniformly, so reopening needs no special-cased verb.

Copy-paste examples:

```sh
./led decision "review: key-generation | 1 | decide the signing-key generation ceremony | design/MAINT-MAINTAINER-DECISION-BRIEF.md"
./led decision "review-done: key-generation | approved the brief's proposed ceremony as written"
```

`./pickup`'s `MAINTAINER-REVIEW-QUEUE` section prints every open entry rank-ascending, each with
the exact `./led decision "review-done: <slug> | <disposition>"` one-liner to tick it —
copy-paste, no grammar to recall. An empty queue prints a short, explicit line, never silence
(the same never-silent convention `resources()`/`estimates()` already keep). A malformed
`review:`/`review-done:` row is refused loudly at write time (see `led.tmpl`'s own teach-text);
nothing here is a gate on WHAT you decide, only on the shape of the row that records it.

## Correcting the record — supersession, and what to do about its fallout

**I encoded a row wrong (wrong flag, missing refs, bad wording) — how do I fix it?**
Supersede it: write the corrected row with `--supersedes <old-row-id>` (for work items,
`led work open <new-slug> ... --supersedes <old-open-row-id>`). The ledger is append-only,
so a correction is always a new, linked row — the old one leaves current truth but stays
in history, never obscured. This is the default answer to every "I wrote it wrong"
situation; nothing is ever edited in place, and raw SQL against the ledger is never the
answer to a missing verb. Honest limit: superseding a work item's OPEN row permanently
burns its slug (a deliberate, ratified choice) — the replacement needs a new slug, and
surviving claims/edges that named the old slug must be re-issued. Grammar:
`./led work open` usage; semantics:
[FABLE-SUPERSESSION-UNIFORM-RETRACTION-SPEC.md](FABLE-SUPERSESSION-UNIFORM-RETRACTION-SPEC.md).

**I recorded a `work_depends_on` edge wrong (wrong `--type`, wrong endpoints) — how do I fix
it?** Same primitive, one kind over: `./led work depends <slug> <on-slug> [--type
blocks-close|blocks-start|informs] --supersedes <old-edge-row-id>`. This writes a NEW
work_depends_on row that both carries the corrected edge (a different `--type`, or different
`<slug>`/`<on-slug>` endpoints — re-pointing a mistaken edge entirely is legal) and retracts
the old row from current truth in the same act (`ledger.supersedes`, s31 — uniform across
every kind, reinstatement-free). Reach for this specifically when: the edge was typed wrong
(e.g. recorded `informs` when it should have been `blocks-close`, or vice versa); the edge
pointed at the wrong antecedent or dependent slug; or the mixed-deadlock case that s39's
claim-time refusal teach-text and its LIMITS section both name explicitly: a `blocks-close`
edge and a `blocks-start` edge between the
SAME two items in OPPOSITE directions produced a genuine mutual claim/close deadlock (neither
edge type's own construction-time cycle check catches this, because each is scoped to its own
edge type only): supersede ONE of the two edges to break the deadlock. Refused at construction
if `<old-edge-row-id>` does not exist, is not itself a `work_depends_on` row (a different kind
is corrected via its OWN verb's `--supersedes`, e.g. `led work open --supersedes` for a
`work_opened` row, `led work resolve-violation --supersedes` for a disposition row — one
column, three typed entry points, never a raw-SQL fourth), or is already superseded (the row
that superseded it is named, so you can inspect or correct THAT one instead). Re-issuing the
exact same edge shape that a supersession just retired is NOT refused as a duplicate — there
is no uniqueness check on `work_depends_on` rows at all (unlike `work_opened`'s permanent
slug-burn). When the new edge's slug or type differs from the old one, the CLI prints an
advisory naming both the old and new endpoints, so the correction stays legible without
digging through raw history. History stays: the superseded edge remains visible in
`work_violation_history`/raw ledger reads; current truth (`work_edge_blocks_close`,
`work_edge_blocks_start`, `work_item_blocks_start_blockers`, and the claim-time/strict-close
refusals that read them) moves on to the new edge only. Grammar: `./led work depends` usage;
kernel semantics: kernel/lineage/s39-blocks-start.sql (blocks-start),
kernel/lineage/s30-typed-dependency-edges.sql (blocks-close),
[FABLE-SUPERSESSION-UNIFORM-RETRACTION-SPEC.md](FABLE-SUPERSESSION-UNIFORM-RETRACTION-SPEC.md)
(the shared supersession mechanics).

**I superseded a parent item and `work violations` now shows orphan rows that nothing can
clear — did I break the world?**
No, and this exact situation happened in a real deployment (a composite parent superseded
while five children — three already closed — still hung under it; every child's parent-edge
became an `orphaned_by_retraction` violation with no discharge path, permanent blocking
debt). Nothing was lost: the children's own rows, closes, and reviews are all intact; the
violations are the record correctly describing dangling linkage. The gap was ours — a
violation an operator can legally cause must have an answering act, and orphans had none.
The fix is the s37 violation-disposition mechanism
([FABLE-ORPHAN-DISPOSITION-SPEC.md](FABLE-ORPHAN-DISPOSITION-SPEC.md)):
`led work resolve-violation <violating-act-id> <reissued|retired> "<basis>"` answers any
in-force violation with a reviewed, attributable row, and `led work supersede-cascade` handles the
live-descendants ripple in one witnessed pass. Until your world has s37: take no further
supersession, let the stop-gate (`hooks/stop_clean_exit.py`, the Stop hook that blocks a
session from ending while governance debt is open) handle stops via its loud fail-open
(that valve exists for exactly this — structurally unclosable debt), and migrate when the
delta reaches you.
**When do I reach for `resolve-violation`, and when for `supersede-cascade`?**
They are not alternatives at the same level: `resolve-violation` is the primitive and
`supersede-cascade` is a convenience built entirely out of it — nothing the cascade does
is impossible by hand, and the cascade writes no special rows. Reach for
`resolve-violation` when violations ALREADY EXIST (you are cleaning up after a
supersession, yours or an inherited one), and always for a superseded parent's
closed/settled children — their edges get `retired` dispositions and the children
themselves are never touched. Reach for `supersede-cascade` when you are ABOUT TO
supersede an item that still has live (open) descendants: it performs the whole ripple —
re-open each live child under a new slug citing its predecessor, re-issue claims and
edges, write each resulting orphan's `reissued` disposition — in one witnessed pass, in
dependency order. The order is the point: done by hand, each step of the ripple mints new
orphans one level down (by design — the mechanism is closed under that recursion), and a
mis-ordered hand-walk leaves you resolving violations you created two steps earlier.
Honest limit: the cascade only handles the subtree below the item you name; edges INTO
the subtree from elsewhere still surface as orphans afterward and are yours to
`resolve-violation` individually, because no tool can know whether an outside edge should
follow the successor or die with the predecessor.

**Why is the fix a disposition act, not "supersede the whole subtree"?**
A subtree is not closed under reference, and a settled review cannot be honestly
re-issued (a new review row in the reviewer's name would forge their agency) — the full
reasoning, with the witnessed evidence, is the ADR-0014 consultation record at
[ORCH-ADR14-ORPHAN-DISPOSITION-CONSULT-2026-07-16.md](ORCH-ADR14-ORPHAN-DISPOSITION-CONSULT-2026-07-16.md).

**Why does the harness insist closed and reviewed items stay correctable at all?**
Because the record model this project imports requires it, independent of anyone's
preference: [the safety-critical-logging BRIEF](../law/briefs/safety-critical-logging/BRIEF.md)'s
invariant I3 (a correction is a new, linked entry that never obscures the prior state),
I7 (every discharged obligation carries the conditions under which it ceases to hold),
and the nuclear/aviation clusters' change-through-re-verification linkage (IEC 60880,
DO-178C) all demand that a close — and the reviews that discharged it — can be superseded
or lapse when their basis is defeated, append-only, with the defeat linked. The kernel
already delivers the core of this (superseding a close re-opens the item and re-surfaces
its review debt, witnessed in the consult above); s37's validity-bounded dispositions
extend the same discipline to violation answers themselves.

## The ledger boundary service (`serving/`)

**Can I get an HTTP API onto a ledger instead of shelling out to `led`?**
Yes — `serving/boundary_service.py` is a FastAPI service that is the one declared **Port**
([ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md) P2) into an autoharn-managed ledger for UI-class and programmatic consumers, the
autoharn-panel Vue SPA first. Full spec:
[FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md](FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md) (read it in full,
including Amendments A1 and A2, before touching the directory); operator pointer:
[serving/README.md](../serving/README.md). The service adds **no truth of its own** — it
translates and validates transport-level shape only, refuses what it cannot honor, and never
coerces. The kernel's own **inner** boundary (the [write boundary](../GLOSSARY.md#write-boundary)
s43's four `SECURITY DEFINER` functions, plus the derived views) stays the sole authority; the
repo-root operator verbs (`led`, [`judge`](../GLOSSARY.md#judge), `pickup`, …) are explicitly NOT
deprecated by this — they remain the sanctioned non-service surface, routing them through the
service is a reserved v2 question.

**How do I launch it, and what does it actually say?**
```
$HOME/w/vdc/venvs/generic/bin/python -m serving.boundary_service --deployment deployment.json --port 18421
```
(the example above ran on port 18421 rather than the default 8420 because another project's dev
server already held 8420 on this host — an ordinary `--port` override, not part of the feature).
WITNESSED, `GET /health` against this repo's own `autoharn1` world:
```
{"world":"autoharn1","service_principal":null,"capabilities":{"s22_work":true,"s41_identity":false,"s43_boundary":false,"credited_view":false}}
```
That capability manifest is not a fixed feature list — it is DETECTED per request against the
connected world's actual schema (object existence, never a version literal), which is why
`autoharn1` — a world older than s40/s41/s43 — shows three of the four capabilities absent
while still serving [`s22`](../kernel/lineage/s22-work-item-ledger.sql) (the kernel-lineage
delta that adds the per-project work-item ledger) work items fine.

**What do the read endpoints look like, and what happens when a world lacks a capability
a read endpoint needs?**
`GET /rows/current` serves `ledger_current` (id-paginated, `?after_id=&limit=`, `1 ≤ limit ≤
1000`, `after_id ≥ 0`); `GET /rows/{id}` and `GET /rows/{id}/history` serve one row and its
supersession chain. `GET /credited`, `GET /standing/principals`, and `GET /work/items` are
**capability-gated** — on a world that lacks the underlying view, the endpoint refuses with a
typed `capability_absent` response rather than silently falling back to a weaker read (that
fallback is exactly the vacuous-pass class this project's [F49 finding](../FINDINGS.md) named:
a close instrument that silently no-ops instead of visibly refusing when its assumed
environment isn't met, so the missing check reads as a pass). WITNESSED, all
three gates against `autoharn1` (which lacks s41 identity and the s44 credited view, but carries
s22 work):
```
GET /credited            -> HTTP 409 {"disposition":"capability_absent","capability":"s44-credited-view", ...}
GET /standing/principals -> HTTP 409 {"disposition":"capability_absent","capability":"s41-identity", ...}
GET /work/items          -> 200, real work_item_current rows
```

**What does a write look like, and what happens to a refused one?**
Four endpoints, one per s43 [write boundary](../GLOSSARY.md#write-boundary) function:
`POST /write/ledger`, `/write/review`, `/write/registration`, `/write/obligation`. **A kernel
refusal is HTTP 200** carrying the kernel's own [typed verdict](../GLOSSARY.md#typed-verdict)
verbatim (`disposition: "refused"`, `refusal_id`, `sqlstate`, kernel-authored teach-text) — a
refusal is a first-class domain result, not a transport error. Transport-level failures
(malformed JSON, an oversized body) are typed and loud instead: a body over 1 MiB is HTTP 413
with `{"disposition":"payload_too_large", ...}`, checked before JSON parsing and again before
the value reaches the database. **On a world that predates s43, every write endpoint refuses
entirely** rather than falling back to a raw `INSERT` — there is no code path in the service
that writes SQL DML. WITNESSED against `autoharn1` (pre-s43):
```
POST /write/ledger -> HTTP 409 {"disposition":"capability_absent","capability":"s43-boundary",
  "message":"This world carries no s43 write boundary ... refuses entirely rather than
  falling back to a raw INSERT ..."}
```
The 413 oversized-body and malformed-JSON write-path checks are **UNWITNESSED here** — on
`autoharn1` the s43 capability gate short-circuits before those checks run at all, since the
world has no write boundary to reach; they would need an s43-carrying world to observe.

**Does it bind to the network, or only to this machine?**
Loopback only by default (`127.0.0.1:8420`); any other host is refused at startup unless you
pass `--i-understand-this-exposes-the-ledger` — the ledger carries operator-real content.
WITNESSED:
```
$ python -m serving.boundary_service --deployment deployment.json --host 0.0.0.0 --port 18422
boundary_service: REFUSED -- --host '0.0.0.0' is not a loopback address ... refused unless
you pass --i-understand-this-exposes-the-ledger explicitly ...
```

**Is there a way to check the service is actually telling the truth about what the kernel
holds?** Yes — `serving/audit_served.py` fetches a served page over HTTP, reads the same view
directly with a read-only `psql`, and byte-compares the row sets; it ships WITH the service
(sentry-class treatment), not as an afterthought. WITNESSED:
```
$ python serving/audit_served.py --base-url http://127.0.0.1:18421 --deployment deployment.json
audit_served: AGREE -- /rows/current matches autoharn1.ledger_current byte-for-byte over the
compared page.
```

**What about the panel's existing direct-psql access — does this retire it?**
That is the deprecation duty the spec's §6 names: every legacy direct-psql consumer path (the
autoharn-panel's own FastAPI-side SQL, concretely) gets a mark that is loud at every invocation,
names the replacement endpoint, and points at the world-context migration consult — but stays
functional (backwards compatibility is the commission's own carve-out; nothing is silently
tolerated, nothing is silently broken). That marking is panel-repo work, out of scope for this
autoharn checkout and UNEXERCISED from here — the spec is explicit that the panel-side session
runs it, citing this spec, never a session running against a live panel checkout from here.

## CLI quality-of-life: row-id echo and `judge` auto-layer detection

**Does `led` tell me the id of the row it just wrote?**
Yes, as of `6677b2d` — every `led` write path prints `row <id> written.` on success (e.g. `led
review: row 42 written.`, `led register-principal: row 7 written.`), instead of leaving you to
go find the id with a follow-up query. WITNESSED, against `autoharn1`:
```
$ ./led decision "documentation witness probe (orchlog.d / FAQ authoring task): confirming the
  row-id echo on a live write path; no operational effect intended"
SET
SET
INSERT 0 1
led decision: row 1553 written.
```
**The one disclosed exception:** `led obligate` writes into `countersign_obligation`, whose
primary key is the scope text, not a bigint id — there is nothing to echo, so that one path
stays silent by the same documented convention rather than printing something misleading.

**Does `./judge` still need `--layer` spelled out, or can I just run it?**
As of `f550e54`, bare `./judge` (no `--layer`) auto-detects which of `engine/lp_registry.py`'s
layers the world's schema can actually support and runs every capable one — printing a plain
`INCAPABLE` line (not a red failure) for a layer the world's lineage cannot support, rather than
either crashing on it or silently skipping it. Passing `--layer <name>` explicitly is unchanged:
an incapable target asked for BY NAME still refuses loudly (`QUARANTINED`). WITNESSED, both
forms against `autoharn1` (a world with `s22` work but no `s41` identity, so the `defeat` layer
has no grant substrate here):
```
$ ./judge
# marriage differential -- layer=None (auto-detect capable layers: ['tnow', 'work', 'defeat'])
## layer='tnow'
  [OK ] autoharn1 AGREE              asp=2991 sql=2991 atoms; Δasp=[] Δsql=[]
## layer='work'
  [OK ] autoharn1 AGREE              asp=364 sql=364 atoms; Δasp=[] Δsql=[]
## layer='defeat'
  [--] autoharn1 INCAPABLE          layer='defeat' declared: target has no
       principal_binding_active/principal_competence_activity columns (pre-s41 lineage) --
       the 'defeat' layer has no grant substrate here, capability absent, not record-empty
# DIFFERENTIAL GREEN -- every target bit-identical to the SQL floor

$ ./judge --layer defeat
  [!! ] autoharn1 QUARANTINED        asp=0 sql=0 atoms; Δasp=[] Δsql=[]
          asp QUARANTINED: EDB export failed: CapabilityError: target 'autoharn1' did not
          emit trust_grant/n (capability absent): no principal_binding_active/
          principal_competence_activity columns on this schema (pre-s41 lineage) ...
# DIFFERENTIAL RED -- a target diverged/quarantined (NO RESULT)
```
Exit is red only when a layer that actually RAN [`judge`](../GLOSSARY.md#judge)s
`DIVERGE_DEFECT`/`QUARANTINED`; a declared-incapable layer never contributes to the exit code
(the same "absence is not a defect" rule the work-item-violations check already applied).

## `led` help tokens, `--json` payload mode, and `work list`'s default filter (led.tmpl trio)

Three small `led` changes landed together at commit `abba0dd` (build `a2c2a5f`, fixup `cf51542`,
delivery record: ledger row 1562). None of them touch the kernel — all three live entirely in
`bootstrap/templates/led.tmpl`, so (unlike the s40/s41/s42/s43 entries above) they are available
to **any** world scaffolded from this commit or later, including this checkout's own `autoharn1`.

**Can I ask `led` for usage without accidentally writing a row?**
Yes. `'help'`, `'-h'`, or `'--help'` as the FIRST word of the statement prints usage to stderr and
writes nothing on every writing subcommand — but the exit code is 0 only once each subcommand's
own arg-count guard has already been satisfied; see the `led review --help` item just below for
the one case where that guard fires first. This includes `led decision --help` specifically (the
one case a prior pass had missed: `--help` used to fall into the
generic unrecognized-flag refusal instead of the same usage-and-exit-0 teach every other
subcommand's `--help` gets). WITNESSED, `autoharn1`, row count unchanged across all three forms
(`--recent 1`'s leading id was `1567` before and after):
```
$ ./led decision --help
usage: led [flags] <kind> <statement...>   (see top-of-file comment for the full flag list: ...)
       led --recent [N] | led current [N] | led show <id> | led question-status | ...
       ...
       '--help'/'-h'/'help' as the FIRST word of <statement...> prints this usage and writes nothing
$ echo $?
0
```
(`led decision help` and `led decision -h` were run the same way — same zero-write result, same
exit 0.)

**Does the same closure cover `led review --help`?** Only once `review`'s three required
positionals are already present ahead of the token. WITNESSED, `autoharn1`, row count unchanged
(`1567` before and after):
```
$ ./led review --help
usage: led review <entry-id> <verdict> <independence> [--antecedent id] <statement...>
       verdict: attest|attest_with_reservations|refuse
       independence: self-review|technical|managerial|financial
       set LED_ACTOR=<principal-name> to countersign as a registered principal
$ echo $?
1
```
A bare `led review --help` (or `-h`/`help`) hits `review`'s pre-existing `$# -lt 4` arg-count
guard (`bootstrap/templates/led.tmpl` ~line 2501) before `check_help_or_dash_first_word` (line
2506) is ever reached — `--help` alone leaves only 1 positional, short of the 4 the guard wants
(entry-id, verdict, independence, statement). It is zero-write either way (usage on stderr, row
count unchanged), but the exit code is **1**, not 0. The exit-0 path only fires once the three
positionals precede the token:
```
$ ./led review 1 attest self-review --help
usage: led review <entry-id> <verdict> <independence> [--antecedent id] <statement...>
       verdict: attest|attest_with_reservations|refuse
       independence: self-review|technical|managerial|financial
       set LED_ACTOR=<principal-name> to countersign as a registered principal
$ echo $?
0
```
So the help-token closure is complete for `decision` and the other pure-help-anywhere
subcommands, but not yet for `review`'s bare `--help`/`-h`/`help` form — a genuine gap in
`led.tmpl`, not a doc error to paper over.

**What if the first word is dash-leading but not actually a help token?**
It REFUSES, teaching, rather than silently committing the word as statement prose — the same
closure this item's title names. WITNESSED, `autoharn1`, row count unchanged (`1567` before and
after):
```
$ ./led note -weirdflag "rest of statement"
led: REFUSED -- the statement's first word '-weirdflag' is dash-leading, which reads as
  a misplaced or mistyped flag rather than intended statement prose (item
  led-help-token-closure -- the same shape refuse_flag_in_statement forecloses for
  KNOWN led flag tokens anywhere in the statement; this closes the gap for an
  UNKNOWN dash-leading FIRST word, which used to sail through and commit a garbage
  row). NOTHING was written. ...
$ echo $?
1
```
Only the FIRST word is checked (the same first-word/whole-word bound `refuse_flag_in_statement`
already uses elsewhere) — a dash-leading word later in the statement is untouched; reword or
quote it if it is genuinely intended prose.

**Can I write ledger rows as JSON instead of a prose statement?**
`led --json <ledger|review|registration|obligation> <file|->` routes a JSON object straight to
the matching s43 [write boundary](../GLOSSARY.md#write-boundary) function
(`ledger_write`/`review_write`/`registration_write`/`obligation_write`) — the exact same four
functions "The ledger boundary service (`serving/`)" section below documents for its own HTTP
endpoints, so the payload shape is the one documented there (payload keys are the target table's own
column names, verbatim, no second vocabulary). Validation at this layer is well-formedness and
top-level-shape only (parses as JSON, is an object) — everything else is the kernel's own
judgment, and its refusal or acceptance comes back as a [typed verdict](../GLOSSARY.md#typed-verdict),
surfaced verbatim, never paraphrased. The raw payload is size-bounded at 1 MiB
(`MAX_WRITE_BODY_BYTES`, the same bound the HTTP boundary service enforces on its own body), 
checked twice — once on the raw bytes before JSON parsing, once on the re-serialized (compacted)
form before it reaches `psql` — so a payload that only grows past the bound on reserialization is
still caught.

**Prominent caveat, same shape as the s42/s43 entry above:** `--json` maps onto the s43 boundary
functions with deliberately NO pre-s43 fallback — a world whose
[birth chain](../GLOSSARY.md#birth-chain) predates commits `1fc4e8c` (s42) / `84729de` (s43)
refuses `--json` outright, `capability_absent`, before ever reaching the size bound or the
kernel. `autoharn1` (this checkout's own live world) is itself pre-s43, so everything below the
line is what this world can actually show; the size-bound checkpoints and a live typed-verdict
round trip are UNWITNESSED here for that reason and are covered instead by
`seen-red/led-json-payload-mode/run_fixtures.py`'s banked evidence and
[orchlog.d/s42-s43-typed-verdicts.md](../orchlog.d/s42-s43-typed-verdicts.md).

WITNESSED, `autoharn1`, all zero-write (row count `1567` before and after every case below —
argument validation and the capability check both run before `kernel_write` is ever called, so
none of these reach a place that could write):
```
$ ./led --json bogus /tmp/whatever.json
led --json: REFUSED -- usage: led --json <ledger|review|registration|obligation> <file|->
  '<surface>' selects which s43 boundary function ... Got: 'bogus'.

$ ./led --json ledger /tmp/does-not-exist.json
led --json: REFUSED (capability_absent, naming s43) -- this world's kernel does not
  carry kernel/lineage/s43-typed-verdict-write-boundary.sql, mirroring the FastAPI
  boundary service's own pre-s43 refusal ... Use the ordinary prose CLI on this world instead.
```
The same `capability_absent` refusal fires regardless of what the file contains or how large it
is (missing file, malformed JSON, a JSON array instead of an object, and a 1.2 MB oversized
payload were all tried live and all produced the identical capability check, before file
existence or size is ever inspected) — on this world, `--json`'s refusal surface reduces to two
cases: bad `<surface>` word, or `capability_absent`. A world carrying s43 sees the fuller surface
(size-bound refusals, kernel-level unknown-key refusals, and a real accepted write echoing its
row id) — that is the surface `run_fixtures.py` and the boundary-service spec document.

**Does `led work list` show me everything, or just what's live right now?**
By default, just what is open or claimed — closed items are hidden, not deleted; nothing about
the ledger itself changes. `--all` restores the full historical view. WITNESSED, `autoharn1`:
```
$ ./led work list | tail -1
(56 rows)
$ ./led work list | grep -c '| closed'
0
$ ./led work list --all | tail -1
(242 rows)
$ ./led work list --all | grep -c '| closed'
186
```
56 + 186 = 242: `--all` adds exactly the closed rows back, nothing else changes. The choice is
taught in the usage text itself (`led work list [--all]  (work_item_current; default open/claimed
only, --all for the full history including closed)`), and this is a read-verb default only — `led
work asof <timestamp>` and the raw ledger rows remain the complete, unfiltered record regardless
of which view `work list` shows you. An unrecognized flag refuses rather than silently falling
through:
```
$ ./led work list --bogus
usage: led work list [--all]
$ echo $?
1
```
Delivery record for all three items: [orchlog.d/led-tmpl-trio.md](../orchlog.d/led-tmpl-trio.md).

## What this page is not

This page is not an inventory (that is [ORCH-CAPABILITIES.md](../ORCH-CAPABILITIES.md), where every
mechanism carries witnessed output or an honest UNWITNESSED mark), it is not a setup guide
([USER-GUIDE.md](../USER-GUIDE.md)), and it is not a promise that a recipe listed here is
enforced — where an entry says "declaration only," the enforcement genuinely does not
exist yet, and the cited spec names the stage that would build it.
