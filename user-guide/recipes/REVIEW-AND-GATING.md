# Review and gating — recipes

*Factored out of [`user-guide/USER-RECIPES-FAQ.md`](../USER-RECIPES-FAQ.md) at commit
`178ec789439044bebb664e7374c2be757d064d11`, sections "Review discipline", "Classifying audit/diagnostic findings", "The
findings-ledger / mined-checklist / +A:B:C pattern", and "Documentation quality";
byte-preserving (mechanical `../` depth repairs only). This file also carries M1, an inline
`doc-attest-exempt` marker inherited from the original page, reworded in place to name its new,
smaller file scope (see the marker itself, ahead of the "I countersigned with a concern..."
Q&A) — the only textual edit inside a marker this split makes beyond mechanical link repair.*

**Charter:** obligations to review, and the gates that hold work until they are discharged.
Belongs: review content checks, reservations, `decomposition_review` arming, per-changeset
review, precondition composition, finding atomization, the findings-ledger/+A:B:C pattern, the
doc review loop. Does not belong: who is entitled to review (see IDENTITY-AND-AUTHORITY.md in
this directory), or the verbs that verify attestations (see EVIDENCE-AND-TRUST.md).

---

## Review discipline

**Is a review's content ever checked, or does any countersign discharge the obligation?**
Partly. [`review_gap`](../../GLOSSARY.md#review_gap)'s own discharge test never looks at what a
review says — any unsuperseded, distinct-actor `attest` clears the obligation regardless of
content, by design. A separate, layered check DOES inspect the discharging review's own
statement: `./audit --review-gap` flags a discharge whose whitespace-normalized statement is
shorter than `CONTENT_FREE_STATEMENT_THRESHOLD` (40 chars,
[engine/review_gap_thresholds.py](../../engine/review_gap_thresholds.py)) — the case this check
answers to was a real 4-char `"test"` review that silently discharged a genuine obligation.
Honest limit, in the check's own vocabulary: it is a length heuristic, so its verdict is
`FLAGGED`, never `VIOLATED` — a genuine terse review passes ("Confirmed, matches row 4's stated
criteria exactly." is 51 chars) and hollow-but-plausible prose of ordinary length ("Reviewed and
everything looks correct, no issues found, approved for merge.") is NOT caught; the check catches
the "test"-shaped instance, not the class, and never substitutes for a human reading the review.
This exit code (6) is reachable only through `--review-gap`, and only when nothing earlier
already raised the exit and at least one review is flagged. Witnessed both polarities:
[seen-red/content-free-review-audit/](../../seen-red/content-free-review-audit).

**Does `led review-gap` (bare) surface every kind of review debt, or just some of it? And can I
tell a defect that was reviewed-and-refused from one nobody has looked at yet?**
As of `led-review-gap-false-clean`/`refuse-verdict-legibility` (`design/
BRIEF-LED-ERGONOMICS-BUNDLE-2026-08-06.md` items 2/3, rows 1087/1102 family; delivery record:
[orchlog.d/led-ergonomics-bundle.md](../../orchlog.d/led-ergonomics-bundle.md)) — yes to both.

Before this delta, bare `led review-gap` read ONLY the actor-keyed `/views/review_gap`, silently
empty while real work-item review debt sat in `/views/work_review_gap` — a hazard-class
false-clean read. It now reads BOTH sources and labels every row `gap_kind` (`"actor"` |
`"work_item"`), so the two debt shapes are never merged into one indistinguishable read.
Fixture-shape evidence (`seen-red/led-review-gap-false-clean/`, a scratch throwaway world):
```
{"_page_tie": "c6e64535...", "close_id": 16, "closer": 1, "gap_kind": "work_item",
 "review_status": "never-reviewed", "slug": "seen-red-led-review-gap-false-clean-...-slug"}
```

Every review-gap row (bare `led review-gap`, or `led work review-gap`) also carries
`review_status` — `"never-reviewed"` (no unsuperseded review row regards this row at all) or
`"reviewed-not-discharging"` (a review row EXISTS but still fails the discharge test — covering
every way a review can fail to clear the debt), the latter with `reviewing_verdicts` naming
who/what/independence. Built entirely from the already-served `/views/review_verdicts` —
CLI-presentation layer only, no kernel/serving change. Fixture-shape evidence for the contrast
(`seen-red/refuse-verdict-legibility/`, same scratch world, two close rows — one never reviewed,
one reviewed and refused):
```
{"close_id": 16, "review_status": "never-reviewed", "slug": "...-a"}
{"close_id": 20, "review_status": "reviewed-not-discharging",
 "reviewing_verdicts": [{"independence": "self-review", "reviewer": 6, "verdict": "refuse"}],
 "slug": "...-b"}
```
WITNESSED, live against this checkout (`autoharn3`) — both `led review-gap` and `led work
review-gap` returned empty (no outstanding review debt on this world right now), consistent with
an honest read rather than an untested one; the populated shape above is cited from the
delta's own banked fixture rather than fabricated against a debt-free world.

**I countersigned with a concern instead of a clean pass — does that discharge the review
obligation, or does it leave the gate stuck open?** It discharges (kernel/lineage/
s56-reservation-residue.sql, design/FABLE-RESERVATION-RESIDUE-SPEC.md, maintainer-ratified
2026-07-22): `./led review <close-row-id> attest_with_reservations <independence> <your
concern...>` clears `review_gap`/`work_review_gap`/`work_item_strict_blockers` exactly as a plain
`attest` does — the verdict is final the moment it is recorded. The reservation itself does not
vanish: it lands on [`reservations_outstanding`](../../GLOSSARY.md#reservations_outstanding) and
stays there until it is itself dispositioned — either supersede the reservation-carrying review
row, or have a DIFFERENT actor write a plain `attest` review *regarding the reservation review's
own row id*. (The original reviewer withdrawing their own concern is a real path too, but it
goes through the supersession leg, not this one: writing a fresh review *regarding their own
prior review* is refused as self-review — the standing segregation-of-duties check,
`kernel/lineage/s21-session-aware-distinctness.sql`, untouched by this delta — applies to a
review of a review exactly as it does to a review of anything else. Witnessed live,
[seen-red/reservation-residue/](../../seen-red/reservation-residue).) Before this delta a
reservation-carrying countersign left the item indistinguishable from one nobody reviewed at
all, which rewarded fabricating a clean `attest` to satisfy the gate rather than recording the
honest concern — this closes that incentive while keeping the concern visible.
[`review_verdicts`](../../GLOSSARY.md#review-verdicts) is the general read path for "what did this
review actually say" (verdict, independence, basis, antecedent, and whether it was later
superseded) when `review_gap`'s own pass/fail view isn't enough.

**How do I make an implementation step mechanically wait on a review step, instead of relying on
remembered discipline?** Arm `decomposition_review` — a third, independent PreToolUse mechanism in
[hooks/pretooluse_change_gate.py](../../hooks/pretooluse_change_gate.py), alongside `change_gate`
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
[`countersign_obligation`](../../GLOSSARY.md#obligation): the same [`review_gap`](../../GLOSSARY.md#review_gap)
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
   [bootstrap/templates/APPARATUS.md](../../bootstrap/templates/APPARATUS.md) for the full switchboard.
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
decision row 1295 (2026-07-17 "two-spy synthesis" — one ledger row combining two independent
observer sessions' findings, "Spy A" and "Spy B" in the row's own text, into a single record
rather than filing each separately); the underlying session transcripts remain local
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

**A close's review debt is undischarged because the close itself was WRONG, not merely
un-reviewed — do I review it, or is there a way to annul the debt?**
That is a different act from anything on this page — reviewing a wrong close would just mint a
countersign on bad data. The recipe is **supersession-as-annulment** (`led work reclose`,
[ADR-0012](../../law/adr/0012-compositional-and-structural-hygiene.md)
one-home rule: full recipe, the `--review-annulled` disposition constructor, and both-polarity
witnessed transcripts live in
[THE-RECORD.md's "Correcting the record" section](THE-RECORD.md#correcting-the-record--supersession-and-what-to-do-about-its-fallout),
not duplicated here).

## Classifying audit/diagnostic findings

**I have a batch of findings from a code audit or review, and sorting them into categories
keeps producing overlapping or incomplete buckets — is there a standard way to do this?** Yes —
split every narrative finding (one that bundles more than one bug or observation) into single-
actionable-unit atoms first, with a provenance link back to where each atom came from, THEN
classify; once every unit is atomic, "did we cover everything" and "does nothing overlap" become
a one-line mechanical check instead of a manual sweep. A second pass then re-clusters the atoms
into
[fix-authorship blocks](../ORCH-FINDING-ATOMIZATION-RECIPE.md#stage-2--reconstitute-atoms-into-blocks-author-fixes-at-the-block-grain-not-the-atomic-grain)
by shared invariant, so one typed fix forecloses a whole class of bugs
rather than patching each atom instance-by-instance. Full method, its adjudication against this
corpus, and its relation to
[ADR-0000's typed-fix discipline](../../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md):
[ORCH-FINDING-ATOMIZATION-RECIPE.md](../ORCH-FINDING-ATOMIZATION-RECIPE.md).

## The findings-ledger / mined-checklist / +A:B:C pattern

**Every review pass we run — documentation, code, whatever — rediscovers the same handful of
defect shapes from scratch. Is there a generic pattern for making review passes get cheaper
over time instead of re-learning the same lessons forever?** Yes — this repository just ran
the pattern on itself for documentation review, and the maintainer asked for it to be written
up here as a generic recipe (his commissioning words are quoted verbatim in the honest-limits
paragraph below, alongside the caveat he attached to the same request). "+A:B:C" in this
section's title names the whole
pattern: **A:B:C** is this project's own name for its fresh-context audit loop — one build (or
draft) pass, then two independent, fresh-context blind review rounds checked against each other
(the full grammar and its own worked examples: the
[A:B:C fresh-context audit loop recipe](../ORCH-ABC-AUDIT-LOOP-RECIPE.md)) — and the leading "+"
names the one thing new here: a checklist-driven find-AND-fix pre-review bolted on in front of
those blind rounds (move 3 below). It is four moves, each depending on the one before it, and
it applies to any review discipline, not just this project's own ADR-0017 doc passes — that
pass is only this entry's worked, witnessed example.

1. **The findings-ledger move.** Every review pass, of any kind, appends its findings to one
   append-only JSONL corpus — forward-only from the day you adopt this, never back-mined from
   git history (mining history is a separate, larger, and noisier project than starting a
   ledger). Each line names, at minimum: a grade, a free-form class slug (not a fixed taxonomy
   — you don't know your own defect classes yet), the file/location, the discovering ROLE (see
   move 4), and a disposition (fixed now, fixed later, filed, accepted). This project's own
   two corpora are the worked shape:
   [attestations/doc-legibility-attestations.jsonl](../../attestations/doc-legibility-attestations.jsonl)
   (documentation, running since 2026-07-11) and
   [attestations/code-review-findings.jsonl](../../attestations/code-review-findings.jsonl)
   (code, started 2026-07-27 — its schema and rationale live in
   [attestations/CODE-REVIEW-FINDINGS-README.md](../../attestations/CODE-REVIEW-FINDINGS-README.md),
   cited rather than duplicated here).
2. **The mining move.** Once the corpus has accumulated enough rows to be worth reading, run
   ONE model pass over it that clusters the free-form classes empirically — not against a
   taxonomy anyone guessed in advance — and emits a ranked checklist: each class named, counted,
   given a plain-language definition, and paired with a cheap detection hint (a grep pattern or
   a one-line reading rule) a reviewer can apply without re-deriving the class from scratch.
   This project's own witnessed instance:
   [attestations/COMMON-DEFECT-CLASSES.md](../../attestations/COMMON-DEFECT-CLASSES.md), mined from
   418 records / 1683 findings in the documentation corpus, ranked class 1 ("dangling
   referent" — a coined term, code, or "the X" cited without ever being defined) at ≈818
   findings, roughly 49% of the whole corpus by itself. **Honest limit, stated in the mined
   file's own method note:** the clustering is keyword-based hand-sampled confirmation, not an
   exhaustive per-finding hand read — treat the ranked counts as good-confidence estimates, not
   exact tallies.
3. **The +A:B:C move** (the maintainer's own coinage for the composite, 2026-07-27). Once a
   mined checklist exists, a reviewer runs an **A-side find-AND-fix pre-review** against it
   BEFORE any of the blind, fresh-context "B" rounds this project's
   [A:B:C fresh-context audit loop](../ORCH-ABC-AUDIT-LOOP-RECIPE.md) already ran — a find-only
   pre-review pass would be waste, since these are exactly the classes that are both cheapest
   to spot and cheapest to repair once spotted. The pre-review logs one JSONL line per document
   pre-reviewed
   ([attestations/pre-review-log.jsonl](../../attestations/pre-review-log.jsonl): doc path,
   before/after content hash, which model swept it, and a per-class fixed-count map), so the
   efficiency question — did the pre-review actually earn its keep — reads later as a join
   against the same corpus move 1 built, no new machinery. **The blind B rounds are never shown
   the checklist** — showing it would anchor the "fresh eyes" round on the pre-reviewer's own
   list and defeat the point of running a fresh-context round at all. This project's own first
   full +A:B:C run
   ([design/LOGGING-DIRECTION-SURVEY-2026-07-27.md](../../design/LOGGING-DIRECTION-SURVEY-2026-07-27.md),
   pre-reviewed 2026-07-27T13:39:13Z per its own
   [attestations/pre-review-log.jsonl](../../attestations/pre-review-log.jsonl) entry) absorbed 36
   defects across 7 classes in the A-side pre-review, and left the two subsequent blind rounds
   only 5 findings between them (2 in round 1, 3 in round 2, one of those three against the
   pre-reviewer's OWN repair prose — the same discipline applies recursively) — against the
   commissioning brief's own stated baseline of 9 blind-round findings (5 in round 1, 4 in
   round 2, per its own attestation record) on a comparable document that had no pre-review
   pass run against it first —
   [design/PANEL-GXP-SURFACE-KICKSTART-2026-07-26.md](../../design/PANEL-GXP-SURFACE-KICKSTART-2026-07-26.md),
   traced to its record in the attestation ledger at adjudication time. **Report this kind of number honestly as a single datum, the way this
   entry just did, never as a proven law**: one comparison is a data point, not a calibrated
   rate, and the honest-limits paragraph below narrows what this specific datum does and does
   not license you to assume.
4. **Role tracking.** Name the discovering role on every finding, not just the finding itself —
   `builder`, `builder-self`, `fresh-context-reviewer`, `attestor-B`, `pre-reviewer-A`,
   `diagnostician`, `verifier`, `orchestrator`, `maintainer`, and `gate:<name>` for a mechanical
   discovery, are this project's own operational vocabulary; its single home, not duplicated
   here, is
   [attestations/CODE-REVIEW-FINDINGS-README.md](../../attestations/CODE-REVIEW-FINDINGS-README.md#role-vocabulary-discovered_by--the-operational-roles-this-project-runs).
   The rationale an adopter needs for bothering with this field at all: per-role discovery data
   is what eventually tells you which review tiers are earning their cost and which defect
   classes deserve a mechanical gate instead of a recurring model pass — a question move 1's
   corpus cannot answer if every row just says "found it" with no attribution of who or what
   found it.

**Honest limits — read this before assuming the doc-side efficiency gain transfers to code
review.** First, the commissioning words this entry exists to answer, verbatim: *"This review
findings thing is something autoharn projects probably will want generally, can we add it do
USER-RECIPES-FAQ along with rationale?"* — and, attached to that same request, the maintainer's
own caveat, carried verbatim because its consequence matters more
than any paraphrase of it would: *"I'll note a kind of caveat of my own: that the documentation
reviews were done against ADR-0017 which is, in some sense, strongly specified."* Spelled out:
the +A:B:C efficiency numbers above come from documentation reviews judged against
[ADR-0017](../../law/adr/0017-the-zero-context-reader.md) — a deliberately strongly-specified
standard with enumerable rules (Rule 1(a) through Rule 2(c), each with a named failure shape).
Code review has no equivalently crisp specification: "is this SQL injection-safe" or "does this
handle the race correctly" does not decompose into ten enumerable, keyword-greppable rules the
way "does every coined term get a gloss" does. The transfer of the pre-review gain from
documentation to code is therefore a **HYPOTHESIS the code-findings corpus exists to test, not
a demonstrated result** — `attestations/code-review-findings.jsonl` started 2026-07-27
specifically to accumulate the data that would confirm or refute it. An adopter building this
pattern for their own project should expect the documentation-side gain (it has a corpus and a
ranked class list behind it) and treat any code-side gain as unproven until their own corpus,
mined the same way, says otherwise.

**The adoption gate, before you start a ledger at all: can you name your consumer?** Per the
[named-consumer test](../../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md#anecdote--2026-07-22-a-rule-2b-answer-for-the-cargo-cult-class-the-named-consumer-question)
— every record kept names the specific reader, process, or investigation that will open it and
the decision it will inform when they do; a record whose consumer cannot be honestly named is
ritual, and ritual gets deleted, not kept. This pattern's own two named consumers, stated
plainly rather than left as "for the audit trail": the future mining pass (move 2 above, which
only exists to consume move 1's corpus) and per-role efficiency (move 4, which only exists to
consume the `discovered_by` field). If you cannot name who reads your findings ledger and what
they decide from it, do not start one — a findings ledger nobody mines and nobody uses to
decide anything is exactly the cargo-cult shape the named-consumer test was built to catch.


## Documentation quality

**Can my project use the fresh-context documentation review loop autoharn uses on itself?**
Yes — this was asked as "is there a reason we can't?", and the answer was no: the reviewer
is an ordinary fresh-context subagent. Scaffolded projects get `./attest-doc`
(`record`/`check`), a project-local attestations ledger, and an opt-in DOC-ATTESTATION
section in `distance-to-clean` (the scaffold's own operator-facing report that prints how far
the deployment sits from a clean governance state; apparatus switch `doc_attestation`, default
off).
Walkthrough: [USER-DOC-AUDIT-LOOP.md](../USER-DOC-AUDIT-LOOP.md); the loop's rules:
[ORCH-ABC-AUDIT-LOOP-RECIPE.md](../ORCH-ABC-AUDIT-LOOP-RECIPE.md).

**I have known findings to verify AND I want a fresh legibility sweep — can one reviewer do
both?**
No — and this was learned the hard way (a real, dated 2026-07-13 anchoring defect in a live
deployment, not a hypothetical). A reviewer briefed with a known findings list *and* asked to also
sweep fresh anchors on the list — the sweep silently degrades into a second verification pass. Run
two separate reviewers: a targeted verifier (front-loaded with the list — correct there) and a
genuinely blind B (artifact + commission only, no findings, no mention a correction pass
happened). The same rule governs a co-signer/countersign briefing. Full account, with the
witnessed 0-versus-4-and-7 findings gap between confirmation-mode and adversarial-fresh reviews:
[USER-DOC-AUDIT-LOOP.md](../USER-DOC-AUDIT-LOOP.md)'s "Briefing your reviewer" section.

