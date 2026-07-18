subject: row 1518
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

**AUDIENCE: this note is addressed to the autoharn-panel deployment's own orchestrator** — the
session (or its successor) that plans and builds the panel SPA/service, not to autoharn's own
maintainer-facing docs readers. It is the **follow-up** to
[orchlog.d/panel-single-boundary-direction.md](panel-single-boundary-direction.md); read that
note first — it lays out the direction (row 1471) and the layering in full. This note exists
so the next panel session plans against the maintainer's 2026-07-18 commission on top of that
direction, instead of discovering it mid-build.

**What changed since the prior note: the maintainer commissioned the work, not merely endorsed
the direction.** Ledger row 1518 (autoharn's own ledger — `./led show 1518` from an autoharn
checkout), the maintainer verbatim, quoted for the sentence that matters most here (his own
punctuation and trail-off preserved): *"I think implementation of the FastAPI as the only
remaining sanctioned surface into the ledger (expect for backwards-compatibility,
*deprecation-marked* ADR-0002 compliant, with a pointer to the Fable-commissioned context
migration doc -- which by the way needs an A:B:C pass that additionally attempts to generalize
it and add an FAQ/Walkthrough for people not familiar with the autoharn-panel project), since
I'm guessing some items (judge? row 1516) will be superseded by it's implementation."* Row 1518
is a **commission** (kind `commission` in the ledger), not itself the architecture — it
instructs an A:B:C workflow over row 1472's open items and, inside that instruction, states the
FastAPI-only-surface expectation as the shape any surviving legacy path must take. It also
flags that some other open items (it names `judge` and row 1516 by way of example) may turn out
superseded once the FastAPI surface actually exists — that is the commissioning session's own
open question, not something this note resolves. Nothing about the FastAPI service's own build
has landed as a result of row 1518 yet; see "not yet built," below.

**DECIDED, carried forward unchanged from the prior note (row 1471, endorsed direction) and now
reinforced by commission (row 1518):**

- FastAPI is the sole declared boundary Port (this project's
  [ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md) P2 sense of "Port") into
  the ledger for UI-class consumers. Translate-and-validate, refuse what it cannot honor, never
  coerce — P2's own words, verbatim, because they are the exact discipline this consolidation
  asks FastAPI to hold.
- The Vue app is a pure consumer: no direct database coupling of any kind. Every read and
  write the SPA performs goes through FastAPI's declared surface.
- Raw SQL access is **structurally closed**, not merely discouraged, on any world born
  post-s43: the granted role holds no `INSERT` privilege on any kernel-governed table, and the
  four SECURITY DEFINER boundary functions (`kernel.ledger_write`, `review_write`,
  `registration_write`, `obligation_write`) are the only write path that exists. This is the
  "write boundary" row 1518 refers to when it names what a legacy direct-SQL path must be
  marked as bypassing.
- Refusals from those boundary functions are typed verdicts
  (`kernel.write_verdict`: `disposition`, `row_id`, `refusal_id`, `sqlstate`, `message`), not
  thrown exceptions — a genuine synergy worth designing for from day one, per the prior note:
  FastAPI gets the refusal's own kernel-authored teach-text for free and can render it directly
  in the UI as first-class explanatory text, instead of manufacturing its own error copy or
  leaking a database error to the browser.

**NEW in this commission, the piece the prior note did not yet state: legacy direct-access
paths survive, but only deprecation-marked.** Row 1518 licenses backwards-compatibility paths
that still reach the ledger directly (panel's current architecture, per the maintainer's own
characterization quoted in the prior note: *"autoharn-panel writes SQL directly which is just
bad"*) to keep functioning through a transition, on two conditions stated in the commission
itself: each surviving path is **deprecation-marked**, and each mark points at the migration
consult document. Concretely, per the commission's own compliance reference:

- **"ADR-0002 compliant"** names
  [law/adr/0002-fail-loudly.md](../law/adr/0002-fail-loudly.md) — specifically its "Bounded,
  scheduled-for-removal compat shims" exception (under "Exceptions," this project's fail-loudly
  tenet): *"A defensive fallback during a bounded transition is acceptable **if** the
  alternative would produce a failure the operator cannot action, and **if** it is commented as
  bounded and scheduled."* Read that whole ADR before marking anything — it is short and its
  hierarchy of loudness governs how the mark itself should read, not just that a mark exists.
  In this instance the practical shape is: a legacy direct-SQL code path (or its call sites)
  carries a comment naming it bounded and scheduled for removal, not merely "deprecated" as an
  unadorned label — a bare label without a removal condition is exactly the silent-fallback
  failure ADR-0002 forbids elsewhere in the same document.
- **"a pointer to the Fable-commissioned context migration doc"** names
  [design/FABLE-WORLD-CONTEXT-MIGRATION-CONSULT-2026-07-19.md](../vestigial_documentation/design/FABLE-WORLD-CONTEXT-MIGRATION-CONSULT-2026-07-19.md)
  — each deprecation mark on a legacy path should link there. Read it before writing the
  pointer text: it is a **banked investigation, non-binding, awaiting a future commissioning
  act** (its own status line), not a spec — it answers what accumulated deployment context
  (principals, standing decisions, open work, the resources registry, and more) IS and how it
  should cross a world boundary when panel's own world eventually succeeds to a new one, not
  how to wire FastAPI. It is the right pointer for a deprecation mark because the reason a
  legacy direct-SQL path is being retired is bound up with the same world-boundary discipline
  this document works out in full: raw SQL against one world's kernel is exactly the kind of
  access this consult treats as non-transportable, non-authoritative evidence once a world
  succeeds. Row 1518 also separately commissions an A:B:C pass on this same consult doc, to
  generalize it and add an FAQ/Walkthrough for readers unfamiliar with autoharn-panel — that
  pass is a different piece of work than the deprecation-marking task and not a prerequisite
  for it; the document is readable and citable today as banked, before that pass lands.

**NOT YET BUILT — plan against this, do not invent details:** the FastAPI service itself does
not exist yet as the sole boundary. Its Fable-authored build-basis spec is being authored **in
parallel, this same day (2026-07-18)** — this note does not know that spec's contents and does
not guess at them; a panel session picking this note up should check for that spec's landing
(search `design/` for a FastAPI build-basis document dated on or after 2026-07-18, or ask) before
assuming any concrete shape — endpoint layout, auth model, the credited-view read contract —
beyond what row 1471 and the prior note already state. The prior note's own "not yet built"
section still applies unchanged: the `credited`-style view row 1471 references does not exist
yet in autoharn's kernel as of this writing either; confirm via a fresh `./migrate --dry-run`
or by reading autoharn's own current `kernel/lineage/` directory whether it has landed on the
commit panel is building against, rather than assume it from either note.

**Citations, for a panel session picking this note up cold:** autoharn ledger rows 1471 (the
ratified serving-boundary consolidation), 1481 (batch ratification), and 1518 (this note's
subject — the maintainer's 2026-07-18 commission instructing the A:B:C workflow and stating the
FastAPI-only-surface, deprecation-marked-legacy expectation);
[orchlog.d/panel-single-boundary-direction.md](panel-single-boundary-direction.md) (the note
this one follows up on, with the full architecture layering and the credited-view read-contract
discussion this note does not repeat);
[law/adr/0002-fail-loudly.md](../law/adr/0002-fail-loudly.md) (the deprecation-marking
discipline, "Bounded, scheduled-for-removal compat shims");
[design/FABLE-WORLD-CONTEXT-MIGRATION-CONSULT-2026-07-19.md](../vestigial_documentation/design/FABLE-WORLD-CONTEXT-MIGRATION-CONSULT-2026-07-19.md)
(the migration-consult document every deprecation mark should point at).
