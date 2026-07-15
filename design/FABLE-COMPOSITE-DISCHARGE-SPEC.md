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

## 2. Principle (v2 — revised after the maintainer's isomorphism question, 2026-07-15)

**A composite item's discharge is a DERIVED fact, never an authored act — and the
derivation is the obligation calculus the kernel ALREADY owns, not a sibling of it.** The
maintainer asked whether work-item discharge should be modelled as an obligation, and
whether this spec was about to duplicate the AND-tree the SPA commission's obligation work
produced. Checked against the kernel: yes, and yes. `work_item_strict_blockers()`
(s29, narrowed by s30) is already the one home of "is this item's obligation tree
resolved" — recursive over s28 children and `blocks-close` antecedents, leaf condition
"closed AND review debt discharged", empty iff resolved, conjunction-derived with no
stored verdict. A first draft of this spec defined a SECOND recursive walker with a
WEAKER leaf ("closed", ignoring review debt) — two homes for one truth, disagreeing
exactly where it matters (ADR-0012 P1; the weaker leaf would have auto-discharged a
parent over a child's outstanding review debt). v2 deletes that walker: composite
discharge is a READ of the existing conjunction. The ledger is append-only and every row
carries an actor's stamp; a trigger that writes close rows nobody authored would forge
agency (rejected below). So "automatically discharged" means: the item's effective state
is COMPUTED — blockers-empty, visible the instant the last leaf resolves, no ceremony row.

## 3. Mechanism (s31, additive delta)

- **Composite-ness is declared at the opening act, typed — and it means STRICT-BY-TYPE.**
  New nullable column `work_discharge`, legal only on `work_opened` rows (one-way shape
  CHECK, the s28/s30 idiom), closed vocabulary: `composite` is its one legal value. CLI:
  `./led work open <slug> "<title>" --discharge composite`. Semantics: every future close
  of a composite slug is a strict close — s29's `--strict` guarantee moves from opt-in at
  the moment of closing (exactly the moment a hurried closer skips it) into the item's
  type, where no later actor can forget it. No new enforcement mechanism exists: the
  trigger treats a composite close as if `work_strict_close` were set, byte-for-byte the
  s29 path. An ordinary item (NULL) behaves byte-for-byte as before this delta.
- **Derived state — a read of the ONE conjunction.** `work_item_current` gains an
  appended column `effective_state` (the s20 column-complete lesson): for a composite
  item with at least one direct child, `discharged-by-obligations` when
  `work_item_strict_blockers(slug)` returns empty; `open` otherwise. No second tree
  walker is minted — the view calls the same STABLE function the strict-close trigger
  already conjoins, so enforcement, derived state, and (downstream) the SPA's AND-tree
  visualization are three readers of one calculus and CANNOT drift. Note this is the
  STRONGER leaf than a bare "children closed": a child closed `--review-deferred` with
  its review undischarged keeps the parent open — the fail-safe direction, inherited
  rather than invented. For every non-composite item, `effective_state` = `state`,
  unconditionally.
- **The vacuous-truth hazard is foreclosed.** A composite item with ZERO children is
  `open`, never vacuously discharged — the parent opened before its decomposition exists
  must wait for it. The residual race (all currently-open children close before a sibling
  is opened) is not mechanically closable in an append-only ledger and is named as a
  LIMIT, not hidden: the standing preamble discipline (decompose the ENTIRE commission
  into items BEFORE implementing) is exactly the operating rule that keeps the window
  empty, and the teach-text on the open constructor says so.
- **The lying close is refused — by the strict path that already exists.** Because a
  composite close IS a strict close (strict-by-type, above), a `work_closed` row on a
  composite slug with any blocker outstanding is refused by s29's existing trigger branch,
  teach-text naming the blocking leaves — no new refusal code, only the type routing into
  it (the experience world's own row-52 finding characterized s29 as running "the opposite
  direction" from auto-discharge — this delta supplies the missing direction and hardens
  the existing one). Once the tree is resolved, a hand-written close remains LEGAL and
  optional — it adds a witness/resolution on top of the derived fact (useful for
  `shipped --witness`), it never substitutes for it.
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

## 3b. Defeasibility (added on the maintainer's question, 2026-07-15)

The maintainer asked: if a later review defeats an interior or leaf node's validity, does
the whole tree re-surface as open, as it should? Answer, made binding here:

- **Review defeat propagates by construction.** `work_item_strict_blockers` stores no
  verdict; its review leaf requires an UN-SUPERSEDED attest by a distinct actor. A later
  supersession of that attest un-discharges the leaf on the next read, and every derived
  ancestor re-opens with it — no propagation machinery, no stored state to invalidate.
  This is not a feature added by this spec; it is why the spec refuses to mint any stored
  discharge verdict anywhere.
- **Derived state ALWAYS wins over a hand-close.** A composite's `effective_state` is the
  blockers reading unconditionally — the optional hand-close row is a point-in-time
  witness, never an override. A tree defeated AFTER a hand-close re-surfaces the composite
  as open (`effective_state`), while the raw close row stands as history; the divergence
  is surfaced as a new `work_item_violations` member (`closed_but_tree_defeated`), never
  silently reconciled in either direction.
- **The close leaf is NOT supersession-aware today — a shared blind spot this spec fixes
  in the one home.** The `closes` CTE inside `work_item_strict_blockers` (and
  `work_item_current`'s closed leg) counts a `work_closed` row regardless of whether a
  later row superseded it: a defeated CLOSE still reads as closed. The review path is
  defeasance-aware; the close path is not — asymmetric for no stated reason. Element:
  filter superseded rows from the closes CTE (both readers, same fix). Fail-safe
  direction (a strict close now requires MORE to be resolved, never less), but it
  tightens the EXISTING strict-close semantics for non-composite items too, so it is
  named as the one element of this spec that is not a pure addition — it is inside what
  this ratification decides, not smuggled under the class ruling.
- **The ASP twin carries the same semantics.** The ledger's defeasible reasoning is the
  deductive layer's whole point; the discharge/defeat rules above get their `engine/lp/`
  counterpart, and `./judge`'s SQL/ASP differential in AGREE — on fixtures that include
  a post-discharge defeat — is the acceptance witness that the two readings cannot drift.

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
- Composite with two children, one closed: open; second closes: `discharged-by-obligations`
  with no further act, WITNESSED in the same read that shows the closes.
- Composite with all children CLOSED but one closed `--review-deferred`, review
  undischarged: parent stays open (the stronger leaf WITNESSED, not asserted); the review
  lands: parent derives discharged in the same read.
- Hand close of a composite with an open child: REFUSED via the s29 strict branch without
  `--strict` being passed (strict-by-type witnessed), teach-text names the child.
- Hand close after the tree resolves: accepted; `state` and `effective_state` agree.
- Non-composite items: `effective_state` identical to `state` across the whole fixture
  world (byte-identical behavior witnessed, not asserted).
- Nested composites: grandparent discharges when the middle composite derives discharged.
- DEFEAT REPLAY: discharged composite; the attest review that discharged a child's
  deferred close is superseded → `effective_state` returns open in the SAME read, and a
  grandparent composite re-opens with it (propagation witnessed, not asserted).
- DEFEAT PAST A HAND-CLOSE: hand-closed composite; a descendant leaf defeated →
  `effective_state` open, `closed_but_tree_defeated` present in `work_item_violations`.
- SUPERSEDED CLOSE: an antecedent's close row superseded → the antecedent re-appears in
  `work_item_strict_blockers` output (the closes-CTE fix witnessed on both readers).
- `./judge` SQL/ASP differential: AGREE on a world containing all shapes above,
  including the post-discharge defeat fixtures.

## 6. Migration posture

Reaches reality in the next scaffolded world's birth chain (runs-are-linear ruling);
existing worlds receive it via `./migrate`'s accommodation machinery like s29/s30 — no
live-world patching. The experience world picks it up at its next quiesced migrate.

<!-- doc-attest-exempt: DRAFT constitutional spec awaiting maintainer ratification. -->
