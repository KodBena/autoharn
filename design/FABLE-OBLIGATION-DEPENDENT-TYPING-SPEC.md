# Typed obligation dependents — spec (AWAITING RATIFICATION)

Date: 2026-07-15, night. Author — TRUE PROVENANCE (corrected 2026-07-15 afternoon): this
draft was written and committed (1599b7f, 14:43) by this session AFTER an unrequested
platform-side demotion of the session model from Fable to Opus, hours after the demotion
event; the original header's claim of Fable authorship was false. The succession rule's
MAXIMUM ceremony for Opus authorship was not performed. On the session's restoration to
Fable, the document was reviewed in full by Fable (review recorded in the
typing-spec-provenance-correction work item): the design is ADOPTED as sound — edge-typed
vocabulary, fail-safe `informs` default, refusals and derived resolution are all consistent
with Element C and the pairing-RCA invariant — with one review note for the maintainer:
§2 names `supersedes` in the edge vocabulary while calling it "already modeled for rows";
whether it is a legal `edge_type` value or a reserved word is unstated and §4's CHECK
needs the answer. Constitutional standing: Fable-reviewed-and-adopted, offered to the
maintainer with true provenance; the maintainer's yes/no decides whether adoption-after-
review satisfies the Fable-authored route or the spec must be re-authored fresh. Status:
DRAFT awaiting the maintainer's yes/no. Motivating requirement (maintainer, 2026-07-15 pre-sleep): "the
typing of obligation dependents (related to and necessary for the obligation AND-tree to
make sense as a projection of SSOT)." Factual basis: the s22/s28/s29 scout brief banked
in the night-shift workflow journal (cited inline as SCOUT with file:line where it gave
one).

## 1. The gap, stated once

The obligation AND-tree (ratified close-semantics, Element C) resolves interior nodes by
conjunction over child obligations. But the EDGE that makes one item a child of another —
`work_parent` / `work_depends_on` (s28, s22:163) — carries **no type**. SCOUT confirms:
nothing today distinguishes "X must be resolved for Y to close" (a *close-blocking*
dependency, the only kind the AND-tree may conjoin) from "X is merely related to Y"
(context, see-also, informational). Nothing forbids a cycle, a self-parent, or a
cross-kind edge. So an AND-tree drawn from these edges is a projection of an
under-specified relation: the graph view must GUESS which edges are load-bearing, and a
guess in a projection of the SSOT is exactly the class this project forecloses (ADR-0000:
make the defect unrepresentable; ADR-0012 P1: one home per fact — here the fact "is this
edge close-blocking" has no home at all).

## 2. Principle

- **The edge carries its type; the tree reads it, never infers it.** A dependency edge is
  typed at write time from a closed vocabulary. The AND-tree conjoins EXACTLY the
  close-blocking edges and no others; every other edge type is visible in the graph but
  never gates a close. No projection ever computes edge semantics — it reads them.
- **Closed vocabulary, fail-safe default.** Edge types (initial, extensible only by
  ratified amendment): `blocks-close` (X must reach a resolved state before Y may close —
  the only type the AND-tree conjoins), `informs` (X is context for Y; never gates),
  `supersedes` (already modeled for rows; named here so it is not re-invented as a
  dependency). Default on an untyped/legacy edge is **`informs`** — fail-safe: an
  unclassified dependency must not silently block or silently satisfy a close; it is shown,
  not conjoined, until a human types it.
- **Structural refusals (ADR-0000 shape checks, construction-time).** A `blocks-close`
  edge is refused if it would create a cycle (the AND-tree must be a DAG or conjunction
  has no fixpoint), if it is a self-edge, or if its endpoints are not both close-tracked
  work items. `informs` edges may be laxer (cross-kind allowed) since they never gate.
- **Resolution stays derived, never stored (the pairing-RCA invariant, inherited).** An
  interior node's resolved/undischarged state is computed at read time by conjunction over
  its `blocks-close` children's recorded resolutions — no stored verdict on the edge or
  the node, exactly as Element C already does; this spec only types WHICH edges enter that
  conjunction.

## 3. The typed-actor question (interface only, not resolved here)

SCOUT flags sec-9's typed-actor rider (only certain actors may close certain items — the
NRC-certified-signer analogy). That is a property of the NODE (who may discharge it), not
the EDGE (what depends on what); this spec is deliberately edge-only so the two compose
rather than entangle. The interface this spec must leave open for it: a node's resolution
predicate is pluggable — today "a recorded close act exists," tomorrow "a recorded close
act BY a qualified actor exists." The AND-tree conjoins node-resolutions regardless of how
each node computes its own; typing the actor is a later amendment to the node predicate,
and this edge-typing spec neither blocks nor presumes it. (The parked
`obligation-actor-type-system` item holds that thread.)

## 4. Kernel shape (on ratification — Sonnet-buildable, birth-chain delivery)

A lineage delta on the s29 successor scaffold (NEVER applied to a live world without the
migration-accommodations spec's epoch machinery — this composes with that spec):
- `work_depends_on` rows (s22) gain an `edge_type` column, closed-vocabulary CHECK, default
  `informs`; the two-way shape CHECKs follow s22's own idiom (SCOUT: s22:203-205).
- Element C's conjunction query filters to `edge_type = 'blocks-close'`.
- Cycle/self/endpoint refusals in the `validate_*` trigger family (SCOUT notes s29 already
  moved cross-table invariants into `validate_work_item()` because a CHECK cannot reference
  another table — the same home receives these).
- `.detect.sql`/`.verify.sql` siblings by the behavior-fingerprint convention (rows
  781/782 lesson).

## 5. Acceptance (witnessed, both polarities)

- A `blocks-close` cycle is refused at write time; an `informs` cycle is allowed (it never
  gates).
- An interior item with one unresolved `blocks-close` child cannot strict-close (Element C
  refusal fires); the same item with that child re-typed `informs` CAN close — proving the
  type, not the mere edge, gates.
- The panel graph view, fed only the typed edges, colors and conjoins without a single
  inference: red/green derive from node resolution, edge rendering from `edge_type`, and a
  reviewer reading the SSOT reaches the identical tree the view draws (the projection-
  faithfulness test — this is the whole point of the spec).
- Legacy untyped edges read as `informs`: no historical close is retroactively blocked
  (fail-safe), and none is retroactively satisfied.

## 6. What this does not do

No live apply (maintainer's typed act, composes with the migration-accommodations spec);
no change to Element C's opt-in nature (strict close stays opt-in); no resolution of the
actor-typing question (interface left open, §3); the maintainer may narrow the edge
vocabulary or reject the default before any build.

<!-- doc-attest-exempt: DRAFT constitutional spec awaiting maintainer ratification. -->
