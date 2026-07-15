# Stop-gate queue semantics — spec (AWAITING RATIFICATION)

Date: 2026-07-15, evening. Author: the orchestrating Fable session (restored; the prior
turn's lower-urgency classification was written under a demoted model and is retracted on
the ledger — this spec is the release-blocker response). Status: DRAFT awaiting the
maintainer's yes/no. Motivating evidence: witnessed live in the experience world today —
`hooks/stop_clean_exit.py` blocked a stop over `state='open'` work items that were (a) the
planned queue point 1 of the deployment preamble itself mandates, and (b) mid-implementation
by a live background workflow; the session, misled further by the gate's own overstated
teach-text ("the turn cannot end until it is clean" — false against the file's own
3-strike fail-open breaker), manufactured a wait/conflict dilemma for the maintainer.

## 1. The contradiction, stated once

Two shipped rules are jointly unsatisfiable:

- **Preamble point 1** (every scaffolded deployment): decompose the ENTIRE commission into
  ledgered work items BEFORE implementing, "including ones you will not start this
  session." The open, unclaimed item is the PLANNED QUEUE — the resumption doctrine's own
  substrate (`./pickup` hydrates successors from it; items are SUPPOSED to persist open
  across sessions).
- **The stop gate's work-item predicate**: any `state='open'` item is stop-blocking debt.

An adopter following the documented method on any multi-session or background-workflow
commission therefore ends every turn in blocked → blocked → breaker-fail-open — and the
fail-open path prints the harness's loudest banner ("A HUMAN MUST REVIEW THIS WORLD'S
LEDGER"), designed as a rare last resort, on the routine happy path. Alarm fatigue then
destroys the banner's evidentiary meaning. Under the NRC-grade bar this is a release
blocker: a safety signal whose designed use-pattern routinely drives it into its emergency
state certifies nothing.

The gate's motivating defect (run-5: a session handed off with a never-closed item) is
real and stays defended — the fix below narrows the predicate to that defect instead of
sweeping the healthy queue into it.

## 2. Principle

**A stop is dirty when THIS session abandons something it holds — never because the world
contains planned work.** The debt is the abandoned CLAIM, not the open item.

## 3. Mechanism (the work-item leg only; review_gap / question_status / violations legs
unchanged)

- **Unclaimed open items never block.** They are the queue. They remain visible: on every
  allow path the gate MAY append a one-line informational count ("N open unclaimed items
  remain — the successor's queue"), never a block.
- **Items claimed by THIS session block, unless bequeathed.** "This session" is
  kernel-visible: the claim row's `stamp_session` equals the Stop hook input's own
  `session_id` (the interception stamp, not a writer-supplied value — the same field the
  stop-disposition check already reads). A claimed-and-still-open item is exactly run-5's
  defect and still refuses the stop.
- **The point-9 disposition row becomes load-bearing (this is the unification).** A
  `decision` row stamped to this session whose statement begins `stopping:` and whose
  `remains:` clause names a claimed item's slug BEQUEATHS it: the item stops blocking, the
  handoff is a typed, stamped, on-ledger act instead of archaeology. Slug matching is
  literal (token equality against the `remains:` text) — no inference. An item claimed by
  this session, still open, and NOT named in a disposition row: blocks, teach-text names
  both discharge paths (close it, or write the disposition that bequeaths it).
- **Background-workflow-held work is covered by the same rule, no special case.** The
  overseeing session bequeaths in-flight slugs via `remains:`; workflow agents' own claims
  carry their own stamps and are not "this session's" claims in the first place. No
  liveness probing, no process inspection — the ledger stays the only truth the gate reads.
- **Teach-text tells the truth.** The block message's opening clause is reworded to state
  the fail-open bound inline: "…until it is clean, until the named items are bequeathed via
  a stopping-disposition row, or until this gate fails open after 3 identical attempts as a
  last resort." (Row 1094's finding, folded in.)
- **Claims orphaned by dead sessions** (claimed, never closed, never bequeathed, claimant
  session gone) are out of this spec's scope: they never block a DIFFERENT session's stop
  under the new predicate, so they need a home in `work_item_violations` or an audit view
  instead — named here so the gap is visible, deliberately not solved here.

## 4. Acceptance (both polarities, real hook invocations against a scratch world)

- Open unclaimed items only → stop ALLOWED, informational line present, breaker state
  untouched.
- Item claimed by the stopping session, no disposition → BLOCKED, teach-text names both
  discharge paths, truthful fail-open clause present.
- Same item, `stopping: …; remains: <slug>` row stamped to the session → stop ALLOWED;
  the same row NOT stamped to this session (another session's disposition) → still
  BLOCKED (bequest cannot be borrowed).
- Pre-s17 world (no `stamp_session` column): the work-item leg degrades to the CURRENT
  behavior (documented, not silent) — narrowing needs the stamp; where it cannot be
  proven, the conservative predicate stands.
- Breaker: with the new predicate, the experience-world scenario replayed end-to-end
  fires NO breaker — the fail-open banner is witnessed absent on the happy path.

## 5. What this does not do

No hook file is edited while any live session runs against a checkout serving it — build
on ratification, apply at a witnessed-quiescent moment (the maintainer's own live-session
check, now narrowed to real Claude sessions, is the quiescence witness). No change to the
review_gap/question/violation legs, the breaker's existence, observe/off modes, or the
disposition warning's never-blocks nature on allow paths. The maintainer may narrow the
bequest rule (e.g. require `--witness` on bequeathing dispositions) before any build.

<!-- doc-attest-exempt: DRAFT constitutional spec awaiting maintainer ratification. -->
