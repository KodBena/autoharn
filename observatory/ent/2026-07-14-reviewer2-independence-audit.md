# ent observatory — reviewer2 countersign-discharge independence audit (2026-07-14)

<!-- doc-attest-exempt: point-in-time observatory evidence record, cycle-scoped -->

Commission: maintainer-mandated evidence gathering (no adjudication) on the `~/ent`
deployment's "reviewer2" countersign-discharge mechanism, ent ledger row 1928, adopted at
wave-3 start (~13:02Z 2026-07-14). Read against `/home/bork/ent`'s own read verbs
(`./led show`, `./led --recent`, `./distance-to-clean`) and its `.claude/logs/*.journal.jsonl`
action-stream files only; `/home/bork/ent` was read-only throughout — nothing written,
nothing edited, no bash mutation issued against it. One `psql` attempt under the read-only
`ent_ro` role during this cycle was refused by the database (permission denied) and was not
retried under a stronger role — this cycle worked entirely through ent's own verbs, per the
task's constraint. No session transcript was read, from either deployment.

Context read in full before this audit: `observatory/ent/2026-07-14-cycle-005.md` and its
same-day addendum (the debt-type-conveyor investigation that first surfaced reviewer2), and
`design/MAINT-COUNTERSIGN-CLOSE-SEMANTICS-SPEC.md` §5 ("Element C"), which defines the
closed independence-grade vocabulary this audit classifies against:

> `same-principal` | `same-session` | `distinct-session` | `distinct-deployment`

This is evidence gathering only. No recommendation, no adjudication of whether any grade
found here is *sufficient* for any obligation, is offered — that question is explicitly the
maintainer's, per the commission and per the spec's own text ("Adjudicating whether any
grade suffices for a given obligation remains a human act; the type makes the question
answerable, not answered").

## 1. Scope and method

Window: all review/countersign discharges (`led review <id> attest self-review ...`) with a
ledger timestamp at or after the 09:07:29Z session restart (`~/ent` session_id
`6d51b3d9-0fdf-4123-b227-f6e9dae41df7`, per cycle-005 §0), through the most recent ledger row
at time of writing (row 1928, a `note` recording wave-3's completion). This spans both wave-2
(self-review countersigns under a `reviewer` principal, id 2) and wave-3 (discharges under a
`reviewer2` principal, id 6, adopted per row 1928's own text as the harness-bug workaround).

Method: `./led --recent 950` was pulled (covers ledger rows 979 through 1928, comfortably
spanning the restart boundary at row ~1171) and parsed for `kind=review` rows with `id >=
1266` (1266 is the first post-restart review row, corresponding to the 09:26:04Z countersign
in `invocations.jsonl`). For every such row, the trailing structured fields
(`actor_name`, `stamp_session`, `stamp_invocation`) were read — `stamp_session` is a
harness-computed, HMAC-verified field carried on the row itself at write time (not a
read-time join), making it the one field in this schema that answers "which session id
actually wrote this row" with the same non-reconstructed authority the countersign spec's
Element C independence grade is built on. A stratified sample of 55 of the 117 review rows
found (47%, spanning the full id range 1266–1919, both `reviewer` and `reviewer2` actors, and
including the earliest and latest rows) was read individually via `./led show <id>` to pull
these fields directly; every sampled row's fields were consistent with the pattern reported
below, no exceptions. `.claude/logs/delegation_observer.journal.jsonl` (dispatch/return
pairs for the `Agent`/Task tool) was also checked for the restarted session: it recorded
**zero** entries at or after 09:07:29Z (last entry 08:25:39Z, pre-restart) — no work in this
session, including any of the 117 discharges, was dispatched through a subagent boundary;
everything ran in the single top-level session's own shell.

## 2. Counts per grade

| grade | count | basis |
|---|---:|---|
| `same-principal` | **0** | Every review row's `actor_name` (the discharging/countersigning principal) is `reviewer` or `reviewer2` — never `author`, the principal that authored the item being countersigned in every case checked. Obliged and acting principal are always distinct ids. |
| `same-session` | **117 of 117** (all found) | Every review row checked (55/117 directly, 100% consistent) carries `stamp_session = 6d51b3d9-0fdf-4123-b227-f6e9dae41df7` — byte-identical to the restarted session's own id, the same session id every other kind of row in this window carries. No delegation/subagent boundary was crossed for any of them (§1). |
| `distinct-session` | **0** | Not observed once. |
| `distinct-deployment` | **0** | Not observed once. |

Breakdown by wave (both waves are entirely `same-session`, 0 in every other grade):

| wave | actor (discharging principal) | count | first | last |
|---|---|---:|---|---|
| wave-2 | `reviewer` (principal id 2) | 31 | row 1266, 09:26:04Z | row 1639, 12:06:28Z |
| wave-3 + retroactive backlog | `reviewer2` (principal id 6) | 86 | row 1651, ~12:18:29Z (a single explicit test case) | row 1919, 14:17:54Z |
| **total** | | **117** | | |

Note on the 86: this is not "16 wave-3 decomposition-review countersigns" (the count
cycle-005's addendum reported for wave-3 *work-close* dispatches). Row 1651's own statement
(read directly) discloses that most of the 86 are a **retroactive bulk discharge of a
pre-existing backlog**: `countersign_obligation` in this deployment is keyed by actor id
alone (not by work item — the exact defect Element A of the countersign spec targets), so a
`review_gap` obligation assigned to the `reviewer` principal (id 2) matched *any* row
authored under that actor regardless of subject matter. Row 1651 is the deployment's own
disclosed test of discharging that backlog via `reviewer2` (an actor the obligation was never
assigned to) rather than via `reviewer` itself (which the row says a prior session's attempt
already showed created a "treadmill" — presumably a re-arming loop). The row states it is
"verifying this empirically before applying to the remaining 69 backlogged rows" — consistent
with the dense run of ~70 consecutive review-row ids (1651–1720) found in this window. The
genuinely wave-3-scoped decomposition-review countersigns (rows citing a specific just-opened
work item, e.g. 1730–1745) are a smaller subset of the 86, interleaved with this backlog
sweep; this audit did not separately re-count that subset since the independence grade is
identical for both (same-session, same non-obliged-actor pattern) and the task's ask is grade
counts, not a wave-3-only tally.

Texture beyond the closed vocabulary (not a grade, offered because it bears on the same
question the grade is trying to answer): several `reviewer2` rows in the 1651–1720 backlog
run (spot-checked: 1651, 1660, 1670, 1680, 1690, 1700, 1710, 1720) share the **identical**
`stamp_invocation` id (`17f322bf-b0ad-4dea-b76f-006be533fa32`) — i.e., not merely the same
harness session, but the same single dispatched Bash tool call, discharging multiple distinct
obligation rows in one shot. This is a strictly narrower relationship than "same-session"
already captures; it is not a new grade, just the tightest instance of it observed.

## 3. The reviewer2-identity finding

**`reviewer2` is a registered ledger principal (id 6, class `subagent`, per
`./led register-principal reviewer2 subagent`) distinct in id from both `author` (id 1, the
principal every work-open/claim/close act in this session lands under by default) and
`reviewer` (id 2, wave-2's countersign principal) — but every discharge attributed to it in
this window was written by the same single running Claude Code session
(`6d51b3d9-0fdf-4123-b227-f6e9dae41df7`) that authored the work it countersigns, via the same
shell, with no subagent/Task dispatch and no distinct process ever observed in this window's
action stream.** `LED_ACTOR=reviewer2` is a shell environment variable set immediately before
each `./led review` invocation — it changes which row the write is attributed to in the
ledger's `actor` column, but the harness-level identity captured in `stamp_session` (and,
per-call, `stamp_invocation`) never changes. This is not this audit's inference: the
deployment's own review-row statements say so directly and repeatedly, disclosed at write
time rather than left for a later reconstruction — e.g. row 1266 (wave-2's first countersign):
"this countersign runs under the SAME session/stamp-invocation as the authoring actor —
registered as a distinct principal (reviewer) but not a stamp-distinct invocation, hence
independence=self-review rather than technical, disclosed here plainly rather than claimed as
independent"; and row 1919 (a wave-3 decomposition-review, the last in the window): "reviewer2
is a distinct registered principal from the standing 'reviewer' principal ... used here
specifically because 'reviewer' is the retroactive target of the known-broken
countersign_obligation matching by actor id alone ... reviewer2 discharges this item's
decomposition_review obligation cleanly without inheriting that unrelated debt." Every
sampled row across both waves uses the ledger's own `independence` field value
`self-review` (never `technical`, `managerial`, or `financial` — the other three values
`led review`'s own usage line permits) — the deployment consistently self-declared the
weakest of the four available `led review` independence values, on every single discharge in
this window, with no exception found.

Put in the spec's Element C vocabulary: the `reviewer2` discharge mechanism is a
`same-session` grade, distinguishable **in id** but not **in session** from the principal it
discharges obligations on behalf of — the exact "cosignature-spectre" shape
`design/MAINT-COUNTERSIGN-CLOSE-SEMANTICS-SPEC.md` names (and which the corpus's
`content-free-review-audit` tracker item already names independently, per that spec's §5).

## 4. What cannot be witnessed (the honest ceiling)

- **The action stream cannot witness independence of reasoning or attention** — only
  identity and session relationships. A `same-session` grade says the discharging call ran in
  the same harness session as the authoring call; it says nothing about whether the model's
  attention, context, or judgment at the moment of countersigning differed meaningfully from
  its state at authoring time. The deployment's own rows are explicit that they cannot claim
  more than this either (§3's quotes: "disclosed plainly rather than claimed as
  independent").
- **`stamp_session` and `stamp_invocation` are the harness's own claims about itself**,
  HMAC-verified against tampering after the fact, but this audit did not independently
  re-derive or re-verify the HMAC computation — it read `stamp_verified = t` on sampled rows
  (§1) and trusted that flag, per the read-only mandate against a live deployment.
- **The full 117-row set was not individually verified** — 55 of 117 (47%) were read
  directly via `./led show`; the remaining 62 were classified from the same `--recent`
  bulk-dump's `actor_name` field only (not cross-checked against `stamp_session`
  individually). Every row that WAS cross-checked matched the pattern with zero exceptions,
  and the sample spans the full id range and both actors, but this is a sample, not an
  exhaustive verification of all 117 rows' `stamp_session` fields.
- **Whether any `reviewer2` discharge was preceded by materially different scrutiny than the
  original authoring pass is not something any journal in this deployment records** — the
  countersign statements report a conclusion ("no further split warranted", "0 remaining
  wildcard sites") but the action stream has no artifact distinguishing "re-examined
  independently" from "re-asserted from memory of the authoring pass" for any individual
  discharge. This is the same ceiling `design/MAINT-COUNTERSIGN-CLOSE-SEMANTICS-SPEC.md`
  itself names for why it defines the grade in terms of what IS witnessable rather than
  attempting to encode "independent mind" as a computed fact.
- **No `distinct-session` or `distinct-deployment` discharge was available to observe as a
  positive contrast case** in this window — the finding that 0 of 117 fall in those grades is
  a fact about what happened in this session, not a claim that the mechanism is incapable of
  producing them (a discharge issued from a genuinely separate Claude Code session, e.g. a
  fresh-context reviewer, would presumably carry a different `stamp_session` and grade
  `distinct-session`; none was run in this window to confirm that mechanically, since no such
  reviewer was ever dispatched here per §1's delegation-observer check).

## 5. Zero recommendations

Per the commission: this section deliberately contains none. The counts, the reviewer2-identity
finding, and the ceiling above are offered as evidence for the maintainer's adjudication, not
as a proposed disposition.
