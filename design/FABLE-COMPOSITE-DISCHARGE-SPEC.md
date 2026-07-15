# Composite work items — derived discharge (AWAITING RATIFICATION)

Date: 2026-07-15, late evening. Author: the orchestrating Fable session. Status: DRAFT
awaiting the maintainer's yes/no. Motivating evidence: the maintainer's own commission to
the experience-world deployment asked for a parent task "automatically discharged when the
precedence constraint on tasks 1 and 2 have been fulfilled ... and when 1 and 2 have been
discharged"; that session, following the commission's own contingency clause, invoked
ADR-0014 (a second pair of eyes) on the assertion that autoharn lacks the capability,
countersigned it, filed the maintainer obligation, and emulated the semantics by hand.
Witness chain in the experience world's ledger (spy-retrieved 2026-07-15, read-only):
row 48 the verbatim commission; row 51 the independent ADR-0014 investigation dispatched
with the question only, not the session's own reading; row 52 the capability-gap finding
(cites s28's own "WHAT THIS DELTA DOES NOT DO" — no close-triggered mechanism — and
characterizes s29's strict blocker as running the OPPOSITE direction); row 54 the
second-pair-of-eyes write-dispatch; row 60 a further from-scratch countersign that
re-verified both kernel-file claims independently; row 53 the maintainer-obligation
filing; rows 128/129 the manual emulation (parent closed by hand, disposition naming it
an emulation of semantics the kernel does not provide). Two independent countersigns, no
dissent recorded.

## 1. The gap, stated once

The kernel can already say everything EXCEPT the discharge rule:

- s28 types the parent edge (`work_parent`, set once at the child's opening act; dangling
  and cyclic parents refused at construction; transitive closure derived in
  `work_item_descendants`).
- s30 types precedence (`blocks-close` edges, conjoined at strict close; `informs` never
  gates).
- But a parent item's `state` in `work_item_current` is derived ONLY from its own
  `work_closed` rows. A parent whose entire deliverable IS its children must today be
  closed by a hand-written act that restates what the ledger already knows — or sits open
  forever, polluting the queue with an item nobody can "do". Both shapes are the same
  defect: a derivable fact maintained by convention (ADR-0000 Rule 2(a) — the fix is a
  type, not a discipline).

## 2. Principle

**A composite item's discharge is a DERIVED fact, never an authored act.** The ledger is
append-only and every row carries an actor's stamp; a trigger that writes close rows
nobody authored would forge agency (rejected below). So "automatically discharged" means:
the item's effective state is COMPUTED from its children's closes, visible the instant the
last child closes, with no ceremony row required — and the states a hand-written act could
lie about are refused at construction.

## 3. Mechanism (s31, additive delta)

- **Composite-ness is declared at the opening act, typed.** New nullable column
  `work_discharge`, legal only on `work_opened` rows (one-way shape CHECK, the
  s28/s30 idiom), closed vocabulary: `composite` is its one legal value. CLI:
  `./led work open <slug> "<title>" --discharge composite`. An ordinary item (NULL) behaves
  byte-for-byte as before this delta.
- **Derived state.** `work_item_current` gains an appended column `effective_state`
  (the s20 column-complete lesson): for a composite item with at least one child (direct
  children via `work_parent`), `discharged-by-children` when every child's own
  effective state is closed-or-discharged; `open` otherwise. Recursive (a composite child
  discharges its composite parent), depth-capped like its s28/s30 siblings. For every
  non-composite item, `effective_state` = `state`, unconditionally.
- **The vacuous-truth hazard is foreclosed.** A composite item with ZERO children is
  `open`, never vacuously discharged — the parent opened before its decomposition exists
  must wait for it. The residual race (all currently-open children close before a sibling
  is opened) is not mechanically closable in an append-only ledger and is named as a
  LIMIT, not hidden: the standing preamble discipline (decompose the ENTIRE commission
  into items BEFORE implementing) is exactly the operating rule that keeps the window
  empty, and the teach-text on the open constructor says so.
- **The lying close is refused.** A `work_closed` row on a composite slug is REFUSED while
  any direct child is not closed-or-discharged (validate_work_item, extended — the same
  function every prior refusal lives in), with teach-text naming the open children. This
  is s29's existing strict-close blocker made UNCONDITIONAL for declared composites: s29
  guards only a `--strict` close (opt-in at the moment of closing, exactly the moment a
  hurried closer skips it); declaring `--discharge composite` at the OPENING act moves
  that protection to the item's type, where no later actor can forget it (the experience
  world's own row-52 finding characterized s29 as running "the opposite direction" from
  auto-discharge — this delta supplies the missing direction and hardens the existing one). Once
  all children are discharged, a hand-written close remains LEGAL and optional — it adds a
  witness/resolution on top of the derived fact (useful for `shipped --witness`), it never
  substitutes for it.
- **Precedence composes, unchanged.** Children ordered among themselves use s30
  `blocks-close` edges exactly as today; this delta adds no second precedence mechanism.
  The commission's full shape — "parent discharges when children are done AND their
  precedence held" — is the composition of s30 (order among children, enforced at strict
  close) with this delta (parent state derived from children), not a new monolith.
- **Read surfaces follow.** `./pickup` and the stop gate's informational open-items line
  read `effective_state`, so a discharged-by-children composite leaves the queue with no
  act. The stop gate's DEBT predicate is unaffected (it reads claims, not open items,
  post-queue-semantics fix).
- **Rejected: trigger-authored close rows** — a row nobody stamped is forged agency, and
  the interception-stamp model (the action stream as evidentiary basis) has no honest
  stamp to put on it. Rejected: composite-ness inferred from having children — implicit
  typing changes the semantics of every EXISTING parent item retroactively, the opposite
  of fail-safe.

## 4. Fail-safe classification

Adds one nullable shape-checked column, one refusal (scoped entirely to the new opt-in
`composite` type — no existing item's behavior changes), one derived column on an existing
view (appended), and read-surface display. Nothing existing is relaxed. On the letter of
the 2026-07-09 class ruling this is class-ratified once scratch-witnessed on both
polarities with the SQL/ASP differential in AGREE; it is nonetheless presented for a
maintainer yes/no because it mints new discharge SEMANTICS (a new way for an item to leave
the queue), and doubt about the side of the line IS the routing.

## 5. Acceptance (both polarities, scratch schema)

- Composite with zero children: `effective_state` = open (vacuous discharge witnessed
  ABSENT).
- Composite with two children, one closed: open; second closes: `discharged-by-children`
  with no further act, WITNESSED in the same read that shows the closes.
- Hand close of a composite with an open child: REFUSED, teach-text names the child.
- Hand close after all children closed: accepted; `state` and `effective_state` agree.
- Non-composite items: `effective_state` identical to `state` across the whole fixture
  world (byte-identical behavior witnessed, not asserted).
- Nested composites: grandparent discharges when the middle composite derives discharged.
- `./judge` SQL/ASP differential: AGREE on a world containing all shapes above.

## 6. Migration posture

Reaches reality in the next scaffolded world's birth chain (runs-are-linear ruling);
existing worlds receive it via `./migrate`'s accommodation machinery like s29/s30 — no
live-world patching. The experience world picks it up at its next quiesced migrate.

<!-- doc-attest-exempt: DRAFT constitutional spec awaiting maintainer ratification. -->
