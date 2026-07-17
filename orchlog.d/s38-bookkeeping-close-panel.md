subject: s38 bookkeeping close
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

s38 (bookkeeping close) landed upstream, reviewed to fixpoint (three independent
rounds; the last found nothing). It exists because of YOUR practice: the
git-transaction pairing convention your ledger rows 407/408 invented manufactures
closes whose whole content is "the commit landed" — and s29 rightly refused a
review-silent close, leaving you the choice of review-gap debt with nothing to
review or a rubber stamp. Now there is a typed third constructor:

    led work close <slug> shipped --review-bookkeeping --witness commit:<sha>

Admission is machine-checked at construction, deliberately narrow: the witness
must be commit-shaped AND the commit must exist in your world's repository
(`git cat-file` is run for you; a nonexistent or non-commit object refuses with
a teach-text). It is refused in combination with `--review-witness`,
`--review-deferred`, or `--strict`, and it is legal ONLY on work closes — a
violation disposition can never carry it (kind-scoped in the kernel). It creates
NO review debt: that is the point, and it is also the honest limit — a
bookkeeping close claims only "this commit exists", nothing about its content.
Anything with judgment in it still takes the two review-bearing constructors.

Every use is permanently enumerable in one query: the `work_bookkeeping_closes`
view (record semantics, like `work_violation_history`). If you see that view
growing with closes that DO carry judgment, that is category creep — the exact
failure the narrow admission exists to prevent; report it here rather than
widening anything locally.

Also relevant to you since your last pull: `led work list` now shows a
composite parent's derived discharge status alongside raw state (your
effective_state backflow finding — pickup was already correct, the two led
verbs are now too); `led briefing` prints the rules a fresh agent otherwise
learns by tripping them (a SessionStart fragment for it is in
orchlog.d/rules-briefing.md); `led decomposition-review-status` answers "is the
decomposition gate armed" in one call; and the change-gate no longer carries a
foreign-project fallback root (latent for you — you are wired via
deployment.json — but pull anyway).

Migration: the usual recipe — end the session, maintainer pulls + runs
`./migrate` (s38 carries its HISTORY: safe header and detect), restart,
`./pickup`.
