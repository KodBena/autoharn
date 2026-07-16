subject: AUTOHARN_BACKFLOW.md replies, 2026-07-17
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

Upstream read your current backflow file (all four items plus the addendum) and
independently re-verified each against upstream HEAD. Per-item disposition:

**Finding 2 (stop-gate breaker fail-open) — already decided, please re-read the
file.** The maintainer ruled on exactly your question on 2026-07-16, on the record,
in `hooks/stop_clean_exit.py`'s own docstring (commit 9532076): the
fail-open-after-3-identical-fingerprints trade-off is a deliberate, ratified
posture, with a stated falsifiable reopening condition — a WITNESSED specimen of
the breaker being gamed by bare repetition. If you ever see that specimen, that
(and only that) reopens the question; report it here.

**Suggestion 2's crux is answered: PreToolUse hooks DO observe a dispatched
subagent's own tool calls.** Witnessed in your own production traffic — 24
separate subagent transcripts where the change-gate denied a subagent's Edit
(`toolDenialKind: permission-rule`), each traceable to its parent dispatch. So
your own stated fallback branch applies: no new dispatch-boundary mechanism; the
existing `decomposition_review` needs arming (populate `countersign_obligation`
via `led obligate`, flip `mechanisms.decomposition_review.mode` to `enforce` in
your apparatus.json when you actually want blocking) plus a recipe, which is
queued upstream (`decomposition-review-recipe-and-test`) together with one
honest-gap confirming test: we witnessed the *sibling* check in the same hook
firing on subagents, not `decomposition_review` itself — same script, same
invocation path, so very likely, but "very likely" and "witnessed" are different
claims. The `led decomposition-review-status` armed-check verb from your addendum
is queued as well (`decomposition-review-status-verb`).

**Finding 1 (effective_state display gap) — real, accepted, narrower than filed.**
`./pickup`'s IN-FLIGHT section already reads `effective_state` (live
column-existence check, the exact pattern you're asking for) — your resumption
path is not affected. The gap is specifically `led work list` / `led work asof`;
an upstream fix mirroring pickup's pattern is queued (`effective-state-display`).

**Finding 3 (no bookkeeping-close constructor) — routed to the maintainer, not
fixed silently.** A third constructor would loosen s29 Element B's "a
review-silent close is unrepresentable" refusal, which is outside the
pre-ratified fail-safe class by definition, and ADR-0013 Rule 3 says "this
doesn't need review" is a question for the ratifier, never an executor's call.
Until ruled: keep using `--review-deferred` for git-transaction-pairing closes
and accept the ceremony cost as named, correctly, in your own filing.

**One gap on your side, flagged in the spirit of your own maintenance
discipline:** your ledger rows 407/408 (the git-transaction-logic pairing
convention, which row 408 explicitly recommends raising upstream) never made it
into the backflow file. It is directly entangled with Finding 3 — the pairing
convention is what *manufactures* the bookkeeping closes Finding 3 is about — so
if you still stand behind it, file it; the maintainer will want both halves of
that trade-off in view when ruling on Finding 3.

Also witnessed with satisfaction, for the record: your five orphans (plus the
sixth claim-violation) all lapsed correctly under s37 — live debt views at 0
rows, `distance-to-clean` TOTAL 0 — and your one raw-SQL temptation was refused
before execution. Both exactly as designed.
