# Supersession = uniform retraction — the closure spec (AWAITING RATIFICATION)

Date: 2026-07-15, night. Author: the orchestrating Fable session. Status: DRAFT awaiting
the maintainer's yes/no on THIS document; the two load-bearing forks inside it were
already put to the maintainer as prepared questions and answered (ledgered the same
evening): uniform retraction over refuse-on-work-kinds, and slug-burned over
slug-re-openable. Lineage of the shape: the maintainer challenged a readers×kinds matrix
as pointful patchwork (ADR-0000 2(a)); a fresh-context second-Fable-eyes review
(commissioned with the maintainer's four questions verbatim, ADR-0000 and ADR-0012 read
in full) returned REFUTED-IN-PART and the factorization shape below; a mechanical
enumeration of every ledger reader (SQL and non-SQL) supplied the closure universe. The
matrix survives ONLY as this spec's quantification universe — migration evidence, not a
design object.

## 1. The semantics sentence (the whole spec in one line)

**Superseding a row of ANY kind means exactly one thing: the event is retracted from
current truth. Reinstatement-free. No kind carries its own defeat semantics, because
current state is a pure fold over in-force events only.**

Consequences, uniform and derived, never assigned per kind: a retracted close re-opens
the item (and every derived composite ancestor with it — the composite-discharge spec's
defeasibility bound resolves fully the moment this lands); a retracted claim reads
unclaimed; a retracted `blocks-close` edge stops gating; a retracted open retracts the
item, and its surviving child events become a NEW derived violations member
(`orphaned_by_retraction`), surfaced, never silently tolerated.

Named choice (the fork where SQL and ASP would stop being interchangeable): the
semantics is REINSTATEMENT-FREE — a defeated defeater does not revive its victim; undoing
a defeat means re-issuing the content as a new row. Genuine reinstatement is recursion
through negation (stable-model territory, not expressible as a plain SQL anti-join); if
it is ever wanted, the ASP side becomes load-bearing rather than second-producer, and
that is a new spec, not a patch to this one.

## 2. The reader type (what was actually missing)

Every reader of the ledger is exactly one of two types, declared, never inferred:

- **Current-truth reader**: consumes the in-force projection ONLY (SQL: `ledger_current`
  or an equivalent in-force factoring; ASP: composition with `ledger_tnow.lp`'s
  `in_force/1`). It never touches raw `ledger`.
- **History/forensic reader**: consumes raw `ledger` and is NAMED on a closed allowlist
  with its reason. Existing worked examples: the row-hash chain (every row must chain,
  superseded or not), `led --recent` (displays, and MARKS superseded rows rather than
  hiding them), `work_item_violations`' duplicate-open arm (see §3), write-boundary
  triggers where insert-time checks cannot read a view excluding the row being inserted.

`work_item_current` and `work_item_strict_blockers`' tree/closes CTEs are current-truth
readers accidentally built as history readers; they are re-issued to factor through the
in-force reading. The five inline `NOT EXISTS (supersedes)` copies scattered across views
are the ADR-0012 P1 two-writers drift and collapse into the one factoring.

## 3. The ratified forks

- **Uniform retraction over refuse-on-work-kinds** (maintainer, 2026-07-15). The kernel's
  current posture — silently ACCEPTING a supersedes on a work row and universally
  IGNORING it — is the lying-signature shape and survives under neither fork; the
  maintainer chose meaning over refusal. `engine/lp/work_items.lp`'s "never whole-row
  superseded by design" premise is superseded on the record by this spec.
- **Slug burned over slug re-openable** (maintainer, 2026-07-15). `duplicate_open` (and
  the trigger's duplicate-open refusal) remain HISTORY readers by declared type: a
  retracted `work_opened` permanently burns its slug; a genuine redo opens a NEW slug
  citing the old (`--refs`). Grounds: s28's cycle-impossibility induction PROVES its own
  vacuity from "a slug is opened exactly once, parent fixed at birth" — re-openable slugs
  would silently reopen that proof's hole, and slug identity (the lineage's identity
  primitive, s22) would fork from history. The violations view gains no false positives
  because the raw reading stays raw.

## 4. Mechanism (one delta + engine companion + gate)

1. **One sNN delta** re-issues every misfactored current-truth reader found in the
   closure universe (§6) to read in-force rows only — known members:
   `work_item_current`'s opened/claimed/closed CTEs, `work_item_strict_blockers`'
   edges/closes CTEs, `question_status`'s question-row side, `work_review_gap`'s
   close-row side — and adds `orphaned_by_retraction` to `work_item_violations`. The
   write side gains NO kind-compatibility refusal on `supersedes` (under uniform
   retraction every target is meaningful); the FK stays the one write constraint.
2. **Engine companion**: `work_items.lp` / `work_review.lp` compose with
   `ledger_tnow.lp`'s supersession closure (`work_closed_in_force(...) :-
   work_closed(...), not superseded(R)` and siblings); the work layer joins `./judge`'s
   standing SQL/ASP AGREE differential — the differential IS the standing mechanical
   detect that the two producers cannot drift.
3. **The allowlist gate** (the delta's `.detect` sibling or a `gates/` member):
   mechanically enumerate every view/function reading `ledger` on a scratch apply;
   REFUSE any reader that neither factors through the in-force projection nor sits on
   the named history allowlist with a reason. This is what forecloses the CLASS — the
   next reader, not today's cells (ADR-0011 Rule 4). Full raw-table revoke (GRANT-level
   unrepresentability) is the stronger surface and is assessed during the build; the
   allowlist gate is the honest floor if the revoke proves disruptive to the legitimate
   history readers.
4. **Non-SQL readers**: pickup/led/stop-hook already factor through the views and
   inherit the fix; `led --recent` keeps its declared history posture (marks, not
   hides). The enumerator's two unswept corners (`./distance-to-clean`'s indirect path,
   `engine/*.py` beyond `ledger_floor.py`) are swept during the build and their rows
   appended to the closure universe before the delta ships.

## 5. Acceptance (both polarities, scratch schema, and the standing gate)

- Retracted close: item reads open again in `work_item_current` AND a discharged
  composite ancestor re-opens in the same read (the composite spec's DEFEAT REPLAY
  polarity, now exercisable end to end).
- Retracted claim: item reads unclaimed; the stop gate's claim-debt leg no longer
  counts it against the retracting session.
- Retracted `blocks-close` edge: a formerly-blocked strict close succeeds; the edge's
  retraction is visible in history reads.
- Retracted open: slug burned (re-open REFUSED with teach-text pointing at the
  new-slug-citing-old idiom); surviving children surface as `orphaned_by_retraction`.
- Reinstatement-free witnessed: superseding the superseder does NOT revive the victim.
- History readers unchanged byte-for-byte: hash chain verifies across retracted rows;
  `led --recent` still shows and marks them; `duplicate_open` still fires on a burned
  slug's re-open attempt.
- Allowlist gate red polarity: a deliberately misfactored scratch view is REFUSED with
  teach-text naming both discharge paths (factor through in-force, or claim the history
  allowlist with a reason).
- `./judge` SQL/ASP differential AGREE on a world containing every shape above — the
  work layer's first run under the standing gate.

## 6. Closure statement (ADR-0000 Rule 2(a))

INVARIANT: "in force" has one home per producer (SQL: the in-force projection; ASP:
`in_force/1`), every current-truth object is a function of the in-force subledger only,
and every raw-`ledger` reader is a declared history reader on the closed allowlist.

QUANTIFICATION UNIVERSE: the 2026-07-15 mechanical enumeration (every live view/function
across kernel/lineage s10→s30 with file:line evidence; the write-side FK-only finding;
pickup/led/stop-hook/judge-floor/engine-lp readers; the per-kind meaning-assignment
survey), carried into the delta's own header as its enumerated universe and extended by
the two named unswept corners before ship. The enumeration is evidence FOR this closure,
consumed once — the allowlist gate, not the enumeration, is what keeps the universe
closed thereafter.

<!-- doc-attest-exempt: DRAFT constitutional spec awaiting maintainer ratification. -->
