# Declaring and queues — recipes

<!-- doc-attest-exempt: relocation-class mechanical move (work item faq-refactor-by-concern, ledger row 185 adjudication, 2026-07-28) -- the content below is byte-preserved prose moved verbatim out of user-guide/USER-RECIPES-FAQ.md (commit `178ec789439044bebb664e7374c2be757d064d11`; sections named in the provenance line above), plus mechanical `../` link-depth repairs and named cross-file link/anchor rewrites for content that relocated to a sibling factor file; no other prose was reworded (ADR-0020's clause 1: a residue disposition and a link gate are the mechanical floor, never a substitute for a cold meaning-preservation read -- that read DID run, by a fresh-context Agent invocation distinct from the session that performed the move; see this work item's execution report for the per-file outcome). The ADR-0017 A:B:C legibility loop is a SEPARATE read this session did not run: the coordinator schedules it after merge, per this work item's adjudication conditions (ledger row 185). Waived here only to unblock this commit. Removal condition: strike this marker and run the real ADR-0017 A:B:C loop next time this file is touched for content, not just link repair. -->

*Factored out of [`user-guide/USER-RECIPES-FAQ.md`](../USER-RECIPES-FAQ.md) at commit
`178ec789439044bebb664e7374c2be757d064d11`, sections "Planning and retrospectives", "Declaring things on the ledger", and "Your
review queue"; byte-preserving (mechanical `../` depth repairs only).*

**Charter:** rows you write to declare intent, policy, or a plan. Belongs: `resource:`/
`taxon:`/`interface:`/`task-policy:`/`estimate:`/`review:` conventions and what they do and do
not enforce. Does not belong: the grammar homes those entries point at (they live in
`USER-BLESSED-TABLE-TEMPLATE.md`, `USER-TAXONOMY-DECLARATION.md`,
`USER-RETROSPECTIVE-RECIPE.md`) — pointers only, per this suite's own convention.

---

## Planning and retrospectives

**Can agents estimate a task's cost before doing it, and can I see how the estimates did?**
Yes — ledger an `estimate:` row per task at decomposition time; `./pickup` prints all of
them under its ESTIMATES section, and the retrospective recipe has an estimate-vs-actual
section for reading them against what happened. The standing invariant, enforced by
design rather than by accident: a missed estimate is retrospective data, never a
violation — nothing gates, audits, or refuses on estimate accuracy, and nothing will.
Grammar and comparison recipe: [USER-RETROSPECTIVE-RECIPE.md](../USER-RETROSPECTIVE-RECIPE.md) §6.

**Can I get cost/usage figures I can rely on?**
Partly, and the line matters: raw hook-witnessed event counts are evidentiary; anything
priced or derived from them (token totals, money) is diagnostic-grade permanently — useful
for a sanity check, never sound enough to bill against. Headline statement:
[USER-GUIDE.md](../USER-GUIDE.md) §5; the design boundary:
[ORCH-SPEC-RESOURCE-ACCOUNTING.md](../../design/ORCH-SPEC-RESOURCE-ACCOUNTING.md) §6.

**Can work form a deep task tree without deep subagent nesting?**
Yes — the tree lives in ledger rows, not process nesting: an interior task's children are
OPENED as work items citing the parent, dispatched flat, each closeable with its own
witness. Execution stays one or two levels deep; the logical tree is unbounded and every
interior node is auditable. The work verbs' home is
[ORCH-OPERATING-CARD.md](../ORCH-OPERATING-CARD.md). Per-node estimate-vs-actual rollups
are a designed follow-up, not yet built — the design lives on the deployment's own tracker
as work item `work-tree-rollup` (a ledger row, not a committed page: read it with
`./autoharn led show work-tree-rollup` at the repository root, the same live-lookup convention the sibling
specs use for tracker items).

## Declaring things on the ledger

**Can I declare which tools/services/agents this project may, should, must, or must not
use?**
Yes — one `resource:` row per resource, whose TIER field carries the deontic force:
`available` (MAY), `blessed:` (SHOULD), `mandated:` (MUST), `forbidden:` (MUST-NOT).
`./pickup` renders them tier-sorted, prohibitions first. Honest limit, tier by tier (not one
blanket answer — the two owning specs, [USER-BLESSED-TABLE-TEMPLATE.md](../USER-BLESSED-TABLE-TEMPLATE.md)
and [ORCH-SPEC-RESOURCE-ACCOUNTING.md](../../design/ORCH-SPEC-RESOURCE-ACCOUNTING.md), drifted on exactly this
in mid-2026-07-12 and were
reconciled 2026-07-13, tracker row 223 — a ledger row, not a committed page: `./autoharn led show 223` at
the repository root reads it in full): `mandated`'s close-review convention already shipped and
surfaces an undischarged close as [`review_gap`](../../GLOSSARY.md#review_gap) debt — never a
refusal of the close itself;
`forbidden` is declaration + display only today, with no mechanism yet refusing an invocation
that reaches it (that audit is spec'd, unbuilt — the spec's own §7 says so). The reconciled,
owning statement of what is and is not enforced per tier lives at
[ORCH-SPEC-RESOURCE-ACCOUNTING.md §4.1](../../design/ORCH-SPEC-RESOURCE-ACCOUNTING.md#41--the-mandated-tiers-enforcement-status-reconciled-dated-correction-2026-07-13-tracker-row-223).
Grammar home: [USER-BLESSED-TABLE-TEMPLATE.md](../USER-BLESSED-TABLE-TEMPLATE.md); design:
[ORCH-SPEC-RESOURCE-ACCOUNTING.md](../../design/ORCH-SPEC-RESOURCE-ACCOUNTING.md).

**Can I declare an architectural or licensing boundary and split work along it?**
Yes, declare it today; enforcement is staged. `taxon:` rows assign path patterns to named
classes, `interface:` rows name the sanctioned crossing points; `./pickup` renders a
TAXONOMIES section. The worked example is a real one (an MIT-derivative package inside a
public-domain codebase). What does NOT exist yet: the audit family and the write-time gate
that would police cross-boundary writes (Stages B–D of the spec). Declaring no taxonomy
declares no obligation. Grammar home and example:
[USER-TAXONOMY-DECLARATION.md](../USER-TAXONOMY-DECLARATION.md); design:
[ORCH-SPEC-TASK-TAXONOMY.md](../../design/ORCH-SPEC-TASK-TAXONOMY.md).

**Can I encode how tasks should be split, so I don't have to micromanage decomposition?**
Yes as declared policy: `task-policy:` rows carry splitting criteria (one acceptance
criterion per task, one boundary per task, estimate-before-execution, …) with MUST/SHOULD
force, and reviewer countersigns cite the criteria they checked. The policing column is
derived from what mechanisms actually exist — a criterion never claims more enforcement
than is built. Design and criteria table:
[ORCH-SPEC-DECOMPOSITION-POLICY.md](../../design/ORCH-SPEC-DECOMPOSITION-POLICY.md) §3.

## Your review queue

**Can I keep a ranked "things I need to personally look at" queue, and tick items off as I go?**
Yes — a `review:`/`review-done:` ledger row pair does this; it renders at every `./pickup`
under a `MAINTAINER-REVIEW-QUEUE` section. Unlike the `resource:`/`estimate:` grammars
elsewhere on this page, the grammar is written out here **in full**, not merely pointed at —
this recipe is its one documented home
([ADR-0005 Rule 1](../../law/adr/0005-documentation-discipline.md), single source of truth per
fact), and it deviates from this page's usual "point elsewhere" convention on purpose so an
executive queue has a self-contained page to hand a first-time reader.

A queue entry is a `decision`-kind ledger row (the same kind `resource:`/`estimate:` ride, run
via `./led decision "..."`), validated at write time by
[`bootstrap/templates/led.tmpl`](../../bootstrap/templates/led.tmpl) and rendered at pickup time
by the `MAINTAINER-REVIEW-QUEUE` section of
[`bootstrap/templates/pickup.tmpl`](../../bootstrap/templates/pickup.tmpl) — both cite this
subsection by name rather than restating the grammar a second time
([ADR-0012](../../law/adr/0012-compositional-and-structural-hygiene.md) P1).

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
./autoharn led decision "review: key-generation | 1 | decide the signing-key generation ceremony | design/MAINT-MAINTAINER-DECISION-BRIEF.md"
./autoharn led decision "review-done: key-generation | approved the brief's proposed ceremony as written"
```

`./pickup`'s `MAINTAINER-REVIEW-QUEUE` section prints every open entry rank-ascending, each with
the exact `./led decision "review-done: <slug> | <disposition>"` one-liner to tick it —
copy-paste, no grammar to recall. An empty queue prints a short, explicit line, never silence
(the same never-silent convention `resources()`/`estimates()` already keep). A malformed
`review:`/`review-done:` row is refused loudly at write time (see `led.tmpl`'s own teach-text);
nothing here is a gate on WHAT you decide, only on the shape of the row that records it.
