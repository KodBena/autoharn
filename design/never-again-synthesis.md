# Never-again mechanism — synthesis of two independent Fable shapes (2026-07-07 ~02:50)

Provenance: the maintainer proposed a shape (separate tracked-objects DB, maturity
auto-rendered, meta-law "properly discharged only when evidence AT THAT TIME points at
maturity") and flagged his own anchoring risk. Main-loop Fable wrote its shape FIRST
(never-again-mechanism-fable-main.md, commit 3a42c91), THEN a second Fable was consulted
blind — facts and need only, neither prior shape (never-again-mechanism-fable-consult.md,
verbatim). Synthesis written with both on the table.

## Convergent (independently derived by both — treat as settled)

1. **Debt is DERIVED, never maintained.** Both shapes reject a hand-maintained mirror
   store outright (the maintainer's separate-DB instinct survives as a derived view/
   registry, not a second bookkeeping surface): a `foreclosure_debt` view over the
   findings ledger IS the automatic backlog; it cannot go stale because nothing maintains it.
2. **ADR-0011 in the schema, not the discipline**: discharge of the never-again
   obligation requires a banked SEEN-RED artifact — main shape as condition, consult
   shape stronger: NOT-NULL trigger-enforced columns (red_artifact + sha).
3. **Enforcement only at the two unskippable choke points** — DB triggers + registered
   close-manifest lines. Nothing that must be remembered.
4. **Registry + conformance line is the canonical foreclosure shape** for the dominant
   sub-class (hand-copy drifting from a source of truth: the typo, the forgotten DDL,
   the dropped mandate — ledger_target.py is the existing model).
5. **The mechanism forecloses its own class**: "the ADR-0000 conversion was forgotten"
   is itself the lapse the debt view kills.

## Where the consult's shape WINS (adopt)

- **A dedicated append-only `class_foreclosure` table** beats main-shape's repo-marker
  convention + scanner: trigger enforcement can't lapse; a docstring convention can —
  the very class under repair. Adopt the consult's schema as drafted.
- **`foreclosure-integrity` manifest line (rot detection)** — main shape missed it
  entirely: a foreclosure whose gate was later deleted or whose seen-red artifact
  drifted reverts to RED instead of decaying into a checkbox. Adopt.
- **No lapse-classifier**: EVERY `fixed` finding owes a foreclosure by default, waiver
  path for trivia (ruling-ref'd, queryable rate). A classifier would be a new silent
  surface. Adopt.
- The five concrete foreclosure shapes (coordinate lint, schema-conformance line,
  packet clause registry, adapter fail-loud + fixture-freshness, destructive-DDL guard)
  — adopt as the work unit's seed content.

## The ONE genuine tradeoff — maintainer ruling requested

WHEN is the evidence owed? Main shape: at DISPOSITION time (`fixed` refuses without a
foreclosure ref — closest to the maintainer's meta-law verbatim: evidence at that time).
Consult shape: at CLOSE time (fixed opens a debt row; the close gates) — avoids forcing
gate-design in the heat of the fix, at the cost of debt-at-close pressure (its own named
failure mode). PROPOSED HYBRID for ratification: disposition stays `fixed` but must NAME
the intended foreclosure in its ref (intent recorded hot, one sentence); the
class_foreclosure row with seen-red evidence is owed by CLOSE (the debt view gates).
Intent-at-disposition-time + evidence-by-close: both meta-law readings satisfied, neither
failure mode fully priced in.

## Residuals both shapes accept (pre-registered, not solved)

The filing lapse (a hazard never filed never enters the system) — out of scope, said
loudly. Checkbox foreclosures (Goodhart) — seen-red raises the floor; the adversarial
pass samples foreclosure rows; largest residual. Gate-body drift past the integrity
line — re-bank seen-red on substantial gate edits as the manual counterpart.

## Next step
A work unit in the established hand-over shape (schema 00X, triggers, the two manifest
lines, seen-red banking convention, back-fill-or-waive pass over existing fixed findings,
fixtures with mutation flips) — writable on the maintainer's ratification of the hybrid
(or either pole).

## RATIFIED (maintainer, 2026-07-07, verbatim): "Let's apply the hybrid."
(Context quoted in full for honesty: "I'm state plainly and without ceremony that I'm not
really competent to judge on this matter, but we have to go with something, so...")
The hybrid binds: intent named at disposition time (`fixed` requires a ref naming the
intended foreclosure), evidence owed by close (class_foreclosure row + seen-red artifact,
gated by the foreclosure-debt manifest line). Work unit: docs/work-units/WORK-UNIT-foreclosure-debt.md.
