# Worktree ledgering — branch/merge semantics for the harness's records

Audience: orchestrator

This document designs how the harness — autoharn's governance apparatus: the append-only
Postgres decision ledger, the refuse-and-teach hooks, and the operator verbs — handles
concurrent work in git worktrees: which of its records already merge soundly, which
merge by hand today (and have failed doing so), and what becomes mechanism. It is
written for the executor who builds from it. The maintainer posed the question
mid-flight ("does our harness support work-tree ledgering (e.g. git branch-merge
semantics)?") while seven agents worked in parallel worktrees — and the gaps bit three
times before the day ended.

STATUS: Fable-authored design memo, 2026-07-12, discharging the tracker item
worktree-ledgering-design. Every claim below cites a witnessed specimen from the same
day's record.

## 1. The architecture fact that solves half the problem

The decision ledger lives in Postgres, not in git. Every worktree's verbs point at the
same database, so parallel agents produce ONE linear ledger, interleaved in true
wall-clock order — there is no database-side fork to merge; the row-hash chain stays
single (lineage step s26 gave every row a hash of its predecessor, so a fork would
break the chain — the shared database is what makes a single chain possible); and the
interleaving is *stronger* contemporaneity evidence than per-branch ledgers merged
later would be (those would arrive batch-shaped, the exact pattern the `./audit` verb
exists to flag). This was luck-shaped design; this memo makes it declared design.

## 2. The three witnessed gaps

1. FILE-BASED ledgers branch and merge by hand. `attestations/*.jsonl` and `BACKLOG.md`
   took append-append conflicts on essentially every worktree merge of 2026-07-11/12,
   resolved keep-both by an orchestrator running an ad-hoc regex. Specimen of the
   failure mode: merge commit b25272f landed raw git conflict markers inside
   `BACKLOG.md` when that ad-hoc resolution silently mis-sequenced — caught by a
   downstream agent, fixed in commit 1eb0750, and the deterministic guard
   (`gates/no_conflict_markers.py`) exists because of it. An operator step that is
   ritual rather than mechanism, failing in the orchestrator's own hands: the
   maintainer's runs-are-linear ruling (transcribed in [CLAUDE.md](../CLAUDE.md)'s
   ORCHESTRATION section) says exactly what happens to such steps — they are
   mechanized or deleted, never documented as ritual.
2. Rows carry no BRANCH ATTRIBUTION. Which checkout produced a ledger row is
   forensically inferable (invocation journal plus git), never first-class.
3. No typed MERGE EVENT. The ledger never records that a line of work joined mainline
   at commit X; the join is invisible to every deductive query. The regulator-adoption
   assessment ([MAINT-REGULATOR-ADOPTION-ASSESSMENT.md](MAINT-REGULATOR-ADOPTION-ASSESSMENT.md))
   independently flagged the static half of this through its aviation-standards lens
   (no configuration index recording which apparatus version governed which world); the
   dynamic half — concurrent-change integration — appeared in none of its four lenses
   despite biting three times in practice during that assessment's own authoring
   window. That asymmetry is itself a ledgered finding: standards-lens sweeps find what
   their corpus names; operational gaps surface from the findings journal.

## 3. The design, smallest-first

- **3a. The jsonl merge driver (mechanize the ritual).** Append-only JSONL files have a
  sound canonical merge: union of lines, order preserved per side, identity being the
  line's own bytes (records are self-contained JSON; a duplicate is only possible for
  byte-identical records, which union collapses harmlessly). Ship `tools/merge_jsonl.py`
  — per-file and independently invocable, the composability ADR-0012
  ([law/adr/0012](../law/adr/0012-compositional-and-structural-hygiene.md)) demands —
  and register it as a git merge driver (`.gitattributes`:
  `attestations/*.jsonl merge=jsonl-union`) so `git merge` resolves these files
  mechanically, correctly, every time. `BACKLOG.md` (a prose journal of dated `##`
  sections) gets the same treatment one level up: a section-union driver keyed on the
  dated heading line — sections are append-only point-in-time records by the journal's
  own charter, so union is semantically exact. Both drivers carry
  [seen-red](../GLOSSARY.md#seen-red) fixtures both ways: a manufactured append-append
  conflict resolves to the correct union; a NON-appendable conflict (the same section
  edited on both sides) must FAIL LOUDLY to human resolution, never silently union.
- **3b. Branch attribution as derivation, not schema.** The invocation journal (the
  per-command log the stamping hook already writes) records session ids; the worktree
  path is knowable at journal-write time. One added journal field — the working
  directory at invocation, written by the hook that already writes the line — plus a
  derived view that joins each ledger row to its invocation token and that token's
  journal line, yields "which checkout wrote this row" with zero kernel change. The
  maintainer's action-stream principle holds (his 2026-07-12 ruling, recorded in
  BACKLOG.md: harness guarantees rest on what the hooks observe, never on session
  internals): hooks are the evidence surface.
- **3c. The typed merge event (convention first).** At each worktree merge, the
  integrator ledgers one row (`decision` kind, `merge:`-prefixed statement convention)
  naming the merged branch, the merge commit, and the work-item slugs whose work rode
  it. Cheap, attributable, and it makes the join queryable. A first-class kernel kind
  for merge events waits for witnessed need — the same defer-until-earned rule every
  schema candidate in this repo follows.
- **3d. The attestation merge-seam rule (codify the precedent).** A git merge can
  produce a document byte-state no fresh-context reviewer ever read; the
  attestation-presence gate (`gates/doc_attestation_presence.py`) already refuses such
  a commit — witnessed 2026-07-12, when a merged state of the capabilities document was
  refused until reviewed. The remedy is already precedent: a synchronous fresh-context
  reviewer (the B role of the audit loop defined in
  [ORCH-ABC-AUDIT-LOOP-RECIPE.md](ORCH-ABC-AUDIT-LOOP-RECIPE.md)) reads the merged
  state, scoped to the changed sections plus the merge seam. This memo writes that rule
  down in the recipe document itself, so the next integrator inherits it instead of
  rediscovering it.

## 4. Honest limits

- The union drivers make FILE merges mechanical; they do not make concurrent SEMANTIC
  edits safe (two agents rewording one section still needs a human or an orchestrator).
  The driver's loud-failure polarity is the boundary marker.
- Branch attribution via the journal's working-directory field is evidence-grade, not
  proof-grade: a journal is hook-written and host-local, the same trust domain as every
  journal. If branch attribution ever needs to survive a hostile host, the escalation
  path is the signing layer's anchored chain heads
  ([MAINT-GPG-TRUST-LAYER.md](MAINT-GPG-TRUST-LAYER.md) §4: the maintainer GPG-signs
  the ledger's hash-chain head, making later tampering provable).
- The runs-are-linear ruling is untouched: [worlds](../GLOSSARY.md#world) still never
  see sibling ledgers. This memo is about the HARNESS's own concurrent development —
  and any adopter project that works in worktrees.

## 5. Implementation routing and witness plan

One Sonnet commission: 3a (both drivers + `.gitattributes` + seen-red both polarities,
including the loud-failure case), 3b (the journal field + derived view; the hook edit
observes the standing rule that hooks are never edited while a wired session is live),
3c and 3d (the convention line and the merge-seam rule added to
[ORCH-ABC-AUDIT-LOOP-RECIPE.md](ORCH-ABC-AUDIT-LOOP-RECIPE.md)'s integrator guidance).
Witness: a scripted two-worktree scenario — parallel attestation appends and BACKLOG
sections merge mechanically green; a same-section double-edit fails loudly; the merge
row lands and is queryable.

## Closure statement (per [ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)'s closure form)

Admits: union merge drivers for append-only jsonl and dated-section journals with loud
failure outside the append-only case; branch attribution as a derived view over one
added journal field; merge events as convention rows; the merge-seam attestation rule
codified in the recipe. Refuses: forked database ledgers (the shared-linear
architecture is the design), silent union of non-append conflicts, schema changes ahead
of witnessed need. Out of scope: multi-host ledger federation (no second host exists);
adopter-facing multi-repo topologies (no second adopter exists).

## Implementation status (2026-07-12, Sonnet, tracker item `worktree-ledgering-implementation`)

This section records what §5's Sonnet commission actually built, dated and appended per this
project's amend-by-append convention — the design above is unchanged; this is the "what landed"
answer laid next to the "what was designed" one.

**§3a — both merge drivers, wired and witnessed.**
Both drivers this memo's §3a called for now exist.
[`tools/merge_jsonl.py`](../tools/merge_jsonl.py) implements the line-union merge — always clean by
construction, since an append-only file's lines cannot conflict. And
[`tools/merge_backlog_sections.py`](../tools/merge_backlog_sections.py) implements the dated-`## `-
section union, keyed on the heading line, carrying the loud-failure polarity this memo requires: a
section edited on both sides since the common ancestor refuses the merge and leaves real conflict
markers, catchable by [`gates/no_conflict_markers.py`](../gates/no_conflict_markers.py). Both are
wired via [`.gitattributes`](../.gitattributes) (`attestations/*.jsonl merge=jsonl-union`,
`BACKLOG.md merge=backlog-section-union`). Naming the files in `.gitattributes` is only half the
wiring: the driver COMMAND itself must live in `.git/config`, which is unversioned and so cannot
ride in `.gitattributes`, meaning every clone installs it once. [`bootstrap/bootstrap.sh`](../bootstrap/bootstrap.sh)
now installs it automatically, mirroring its existing `git config core.hooksPath hooks` step. The
same one-time install line is also documented in
[`bootstrap/QUICKSTART.md`](../bootstrap/QUICKSTART.md) for a checkout made before this mechanism
existed. `bootstrap/QUICKSTART.md` was chosen over the adopter-facing
[`USER-CONFIGURATION.md`](../USER-CONFIGURATION.md) because `attestations/*.jsonl` and `BACKLOG.md`
are autoharn's OWN repo files, never scaffolded into an adopter's project — `USER-CONFIGURATION.md`
documents what an adopter's SCAFFOLDED project gets, which these two files are not part of. The
install line also lives in each driver's own module docstring, so it is never more than one file
away from the code it configures:

```
git config merge.jsonl-union.name "union merge driver for append-only jsonl ledgers"
git config merge.jsonl-union.driver "python3 tools/merge_jsonl.py %O %A %B"
git config merge.backlog-section-union.name "dated-section union merge driver for BACKLOG.md"
git config merge.backlog-section-union.driver "python3 tools/merge_backlog_sections.py %O %A %B"
```

WITNESSED: [`seen-red/worktree-ledgering/run_fixtures.py`](../seen-red/worktree-ledgering/run_fixtures.py)
(registered in [`gates/fixture_census.py`](../gates/fixture_census.py)) drives real `git merge` in a
throwaway repo through both drivers — parallel jsonl appends and parallel BACKLOG dated-section
appends each merge clean with the correct union content; a same-section double-edit refuses the merge,
leaves markers, and `gates/no_conflict_markers.py` independently catches them in the staged diff (its
captured output is banked at `seen-red/worktree-ledgering/red.txt`). WITNESSED a second, independent
way: a fresh throwaway clone run through [`bootstrap/bootstrap.sh`](../bootstrap/bootstrap.sh) (the
scripted install path, relative `tools/...` paths, no absolute-path shortcut) merged two branches that
each appended a distinct jsonl line with no manual driver invocation — `git`'s own "Auto-merging ...
Merge made by the 'ort' strategy" output, the ordinary merge UX, now silently correct for this file
class instead of conflicting.

**§3b — the journal field and the branch-attribution reader, both witnessed against a real world.**
[`hooks/stamp_intercept.py`](../hooks/stamp_intercept.py)'s per-invocation journal line gained one
field, `cwd`, appended after every existing field (`token`, `wall_clock`, `session_id`,
`command_sha256`, `command_head`, and the conditional `tool_use_id`) — additive, no reordering,
matching the memo's own instruction. [`tools/branch_attribution.py`](../tools/branch_attribution.py) is
the observer-grade, read-only derived-view reader: it joins a ledger row's `stamp_invocation` token
(the correlation column [`kernel/lineage/s23-per-invocation-stamp-token.sql`](../kernel/lineage/s23-per-invocation-stamp-token.sql)
adds — an existing kernel delta this memo builds on, not a new one) to the matching
`invocations.jsonl` line and reports that line's `cwd` (and, best-effort, the git branch checked out
there right now) — zero kernel change, exactly as designed. WITNESSED end-to-end, live, against a real
scaffolded world (`bootstrap/new-project.sh --new-world`, full kernel lineage through s26): a genuine
subprocess invocation of `hooks/stamp_intercept.py` minted a real HMAC stamp and invocation token, the
returned stamped command was actually executed (`./led decision ...`), the resulting ledger row and
journal line were read back for real, and `tools/branch_attribution.py` reported that row `ATTRIBUTED`
with the correct `cwd`. The reusable form of this witness is
[`instruments/verify_branch_attribution.py`](../instruments/verify_branch_attribution.py) (self-
contained, zero residue — it scaffolds its own throwaway world and drops the schema and role on the
way out); it is NOT registered in `gates/fixture_census.py` because `tools/branch_attribution.py` is
an observer-grade reporting tool with nothing to refuse, not a gate — the same posture
[`engine/contemp_edb.py`](../engine/contemp_edb.py) and [`engine/contemp_audit.py`](../engine/contemp_audit.py)
already have in that registry (neither is listed there either). A row predating this change (no `cwd`
in its journal line) reports honestly as `JOURNALED-NO-CWD`, never guessed or backfilled — witnessed
directly: the same throwaway world's very first row, written before the code change landed, reports
exactly that.

**§3c and §3d — the merge convention row and the merge-seam attestation rule, codified in the recipe.**
Both are now written into
[design/ORCH-ABC-AUDIT-LOOP-RECIPE.md](ORCH-ABC-AUDIT-LOOP-RECIPE.md)'s new "Merging: the integrator's
checklist" section: the `merge:`-prefixed `decision`-row convention (§3c, no kernel change, a first-
class typed merge-event kind still waiting on witnessed need per this memo's own closure statement),
and the merge-seam synchronous-B scope (§3d, reusing this recipe's own A:B:C loop rather than minting a
second review mechanism). This edit, and this status section's own edit to this memo, each carry a
`doc-attestation/2` record — [ADR-0017](../law/adr/0017-the-zero-context-reader.md)'s fresh-context
attestation schema, version 2 (see
[`gates/doc_attestation_presence.py`](../gates/doc_attestation_presence.py)'s module docstring for the
schema itself). The specific attestation record ids and the A:B:C loop's B-verdicts for THIS
implementation pass are named in the `worktree-ledgering-implementation` tracker item's own ledger
entries (`./led show <id>` against the rows this work claimed and closed) and this project's
[BACKLOG.md](../BACKLOG.md) dated entry for the same tracker item — not duplicated here, since both are
already the stable, lookup-able home for that record.

**Deferred, honestly.** The `.git/config` line is documented and scripted (`bootstrap/bootstrap.sh`)
but not applied to this worktree's own shared `.git/config` by this commission — a linked worktree
shares its `.git/config` with every sibling checkout of the same clone, and mutating shared state while
sibling worktrees may be live is exactly the hazard this project's orchestration contract exists to
avoid; the one-time install line is real and tested (both via the seen-red fixture's own throwaway
`git config` calls and via a full fresh-clone `bootstrap.sh` run in `/tmp`), just not self-applied here.
The typed merge-event kernel kind (§3c's own deferral) and multi-host federation (§4's own out-of-scope
line) remain exactly as designed: unbuilt, on purpose, pending witnessed need.
