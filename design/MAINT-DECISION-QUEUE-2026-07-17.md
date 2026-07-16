# Maintainer decision queue — 2026-07-17 (two-spy pass over the panel's backflow)

Status: OPEN — four questions, each independent. Context for each is one
paragraph; the full evidence trail is the two spy reports summarized in the
ledger (2026-07-17 synthesis decision row) and the current
`autoharn-panel/AUTOHARN_BACKFLOW.md`. Everything NOT listed here was either
already decided (breaker fail-open, ruled 2026-07-16) or is fail-safe-additive
and already queued/dispatched without a question, per the class ruling of
2026-07-09.

## Q1 — bookkeeping-close constructor (backflow Finding 3)

The panel's git-transaction pairing convention manufactures work items whose
close is pure bookkeeping ("the commit landed, here is its hash"), yet s29
Element B refuses any close without `--review-witness`/`--review-deferred` —
forcing either review-gap debt with nothing to review, or rubber-stamp
countersigns (the exact "content-free review" failure shape the FAQ already
names). A third constructor would LOOSEN the "review-silent close is
unrepresentable" refusal — outside the fail-safe class, and squarely the shape
ADR-0013 Rule 3 warns is presumptively demurral. Your options:

- **(a) Decline.** Keep the ceremony; `--review-deferred` remains the answer for
  bookkeeping closes. Cost: standing low-grade rubber-stamp pressure on every
  paired close, forever.
- **(b) Narrow machine-verified constructor.** e.g. `--review-bookkeeping`,
  legal ONLY when the close's resolution is mechanically re-derivable from an
  already-attested fact (a commit hash that verifiably exists and is reachable;
  a countersigned row being referenced) — the "nothing to review" claim is
  machine-checked at construction, never operator-asserted. This is the only
  shape the reviewing spy judged could survive Rule 3 scrutiny.
- Related, same ruling session ideally: the pairing convention itself (panel
  ledger rows 407/408) was recommended upstream by the panel's own orchestrator
  but never reached the backflow file. If (b), the convention could become a
  first-class recipe; if (a), it should probably be discouraged instead, since
  it manufactures exactly the closes (a) taxes.

## Q2 — decomposition_review arming posture (backflow Suggestion 2)

Settled by evidence: PreToolUse hooks DO see dispatched subagents' tool calls
(24 witnessed specimens), so the existing mechanism reaches the racing incidents
that motivated the suggestion — no new dispatch-boundary mechanism needed. But
the mechanism is doubly disarmed everywhere today: `countersign_obligation`
empty (nobody knew to run `led obligate`) AND shipped default mode `observe`.

- **(a) Docs only (recommended).** Ship the FAQ recipe + the
  `decomposition-review-status` verb (both already queued, fail-safe); leave the
  shipped default at `observe`; each world's operator opts into `enforce`
  deliberately. Conservative; matches "what the system may PERMIT" being where
  your bandwidth goes.
- **(b) Flip the shipped default to `enforce`** for new worlds
  (`bootstrap/templates/apparatus.json`). A live-semantics change for every
  future world birth; existing worlds untouched. Stronger by default, but a
  world that never populates obligations still gets vacuous enforcement, so (b)
  without the recipe changes little in practice.

## Q3 — agent-start rules briefing shape (backflow Suggestion 1)

Valid, verified, and deliberately parked: you said you have candidate shapes in
mind and have not settled. Filed as `agent-start-rules-briefing`,
MAINTAINER-BANDWIDTH-GATED, never dispatched autonomously. No answer needed now;
this entry exists so the queue is the single place you look.

## Q4 — panel raw-SQL prohibition: norm or gate?

Spy A confirmed the panel's no-raw-writes standing instruction held (the one
temptation was refused before execution) — but it holds by norm + append-only
trigger only: the panel's `sql_block` mechanism is `mode: off`. If you want the
prohibition to be a hard PreToolUse gate on the panel, that is one apparatus.json
line on their side (plus `session_model` set honestly). Their world, your call
to relay or not; upstream needs no change either way.

- **(a) Leave as norm** — it demonstrably held under live temptation.
- **(b) Suggest the panel arm `sql_block`** — defense in depth for a
  non-expert-operated world.

## FYI, no decision needed

- Panel repo is 94 commits ahead of its origin, uncommitted 0 — flagging purely
  for backup/continuity awareness on your side.
- s37 witnessed working in production on the panel: all six violations lapsed
  correctly, live debt 0, `distance-to-clean` TOTAL 0.
- SessionStart durable-decisions hook witnessed firing on five real
  compact/resume events on the panel; the byte-cap truncation fired once with
  the loud ACTION-REQUIRED tail (24 shown + 4 omitted = 28). What remains
  UNEXERCISED is only the before/after comparison against the original incident:
  no post-fix compaction has yet been followed by a situation where the old
  session would have violated a standing decision, so "the hook fires" is
  witnessed but "the hook prevents the violation" is not yet.
