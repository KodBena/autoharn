# FABLE-LEGACY-LED-RETIREMENT-SPEC — the last two surfaces, then the deletion

<!-- doc-attest-exempt: commissioned build basis (maintainer priority, ledger row 1149:
"that's a maintenance-tax and therefore priority"), frozen 2026-07-23 pending
ratification of parts A and B below. Removal condition: superseded by a polished live
edition or by the retirement's completion record. -->

- **Status:** Fable-authored 2026-07-23; parts A and B await maintainer ratification.
- **State of play:** phase 1/1b (commits ea41423/56259a3) rebased every `led` surface
  onto the boundary except two: `obligate revoke` and `artifact put|get|stat`. Both are
  spec-gated, not effort-gated. This spec is those two gates, plus the retirement act.

## Part A — obligation revocation becomes a typed kernel event (kernel delta, next slot)

**Today:** `legacy led obligate revoke` performs a raw, privilege-gated `DELETE` on the
obligation table. This is the kernel's only destructive operator verb: the revocation
leaves NO record — an auditor cannot distinguish "never obligated" from "obligated,
then revoked" — and a raw-DML path is structurally unservable by the boundary, whose
charter (FABLE-LEDGER-BOUNDARY-SERVICE-SPEC §4) forbids any DML code path.

**Proposed:** a new lineage delta in the s43 pattern: a SECURITY-DEFINER write function
`obligation_revoke(scope, actor, reason)` writing a typed revocation EVENT row; the
obligation-consuming views (`review_gap` and the `countersign_obligation` family)
compose to treat a revoked obligation as not-in-force from the event's moment; `DELETE`
on the obligation table is REVOKEd from operator roles (the destructive path dies at
the grant layer, not by convention); the boundary gains a `/write/` surface for it; the
rebased `led obligate revoke` targets that surface with unchanged CLI grammar.

**Closure statement (ADR-0000, 2026-07-02 form).** *Invariant:* no operator verb
destroys kernel history; every state retraction is an append-only typed event, and
"in force" is always a derivation over events. *Quantification universe:* the
obligation table's DELETE was the LAST destructive operator path — enumerated by
sweeping legacy-led.tmpl for DML verbs (the builder's phase-1 sweep found no other) and
the kernel's grants for operator-role DELETE/UPDATE privileges; named as not covered:
administrative acts outside the operator surface (schema teardown, migration repair)
which are deliberately not operator verbs. *Denomination check:* no numeric bounds;
vacuous, named as such.

**History note:** `-- HISTORY: safe` — additive event kind + view re-issue + a grant
REVOKE; zero stored rows change. Existing worlds' past deletions remain what they are:
absences without record (stated, not repaired — history cannot be reconstructed).

**Witness plan:** scratch schema, both polarities — obligate, revoke via the function,
gap views show not-in-force from the event; the raw DELETE refused at the grant layer
(red); un-revoked obligations unaffected; boundary round-trip through the new surface;
SQL/ASP differential in AGREE if the engine models obligations (builder verifies which
engine relations read the obligation table and extends mirrors per the s56 §7
precedent if they encode in-force semantics).

## Part B — boundary artifact routes (serving amendment, no kernel change)

**Today:** the artifact store (s51) is deliberately unrouted ("NOT routed in v1", its
own spec), so `led artifact put|get|stat` is legacy-only. **Proposed:** three routes
under the read-surface spec's own re-ratification discipline — `GET /artifacts/{hash}`
(content, streamed), `GET /artifacts/{hash}/stat` (metadata), `POST /artifacts` (put;
the kernel's own hash-verification refuses corrupt uploads, journaled per s43's
conventions). The rebased `led artifact` targets them with unchanged grammar. Size
bound: the existing artifact-store size discipline governs; the routes add no second
limit (P1 — one home for the bound).

## Part C — the retirement act (fires only after A and B are witnessed)

1. `legacy-led.tmpl` leaves the repo; the `./legacy/led` shim (which resolves live
   from the checkout, so this reaches every world at once) is replaced by a one-line
   refusal teaching "retired 2026-07; every surface now serves through ./led".
2. **Coupling, stated for eyes-open ratification:** after retirement, `./led` requires
   a reachable boundary service — a world without one has no ledger CLI. The TUI
   already defaults boundary auto-start at birth; retirement makes the boundary
   every world's standing service in fact, which is the multiplexer end-state the
   maintainer has already commissioned. Worlds that predate boundary configuration
   must gain it before their operators lose legacy (./doctor's boundary line is the
   check; the panel deployment already runs one).
3. The rebased CLI's SCOPE section collapses to "everything"; the two disclosed
   read-shape divergences from phase 1 (JSON-per-line listing; supersession-aware
   asof) become the documented behavior.

## Witness for the whole

The retirement commit lands only with: A and B's fixtures green both polarities; a
full-surface differential run (every led subcommand exercised through the boundary on
a scratch world, zero legacy invocations); ./doctor all-PASS on a world served only by
the boundary; the panel deployment confirmed off its legacy fallback for work verbs.
