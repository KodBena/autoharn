subject: faddbb1c
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

`kernel/lineage/s73-typed-annulment-disposition.sql` (design/FABLE-TYPED-ANNULMENT-DISPOSITION-SPEC.md,
maintainer-ratified 2026-08-06, row 1087) gives `work_review_disposition` a fourth constructor,
`annulled` — a review obligation an authority distinct from the obligor considered and
DECLINED, for a recorded reason, as opposed to `witnessed` (a real countersign) or `deferred`
(the debt stays open). Scoped to `kind='work_closed'` alone (the same partial-value idiom s38's
`bookkeeping` value already established).

**What a restarting orchestrator needs to know:** three construction-time refusals guard it —
`work_review_ref` is MANDATORY when disposition is `annulled` (cites the authority row); no
self-annulment (the authority row's actor AND its `(stamp_session, stamp_agent)` pair must both
differ from the obligor's — the same distinctness test an independence-claiming review
countersign already uses, s21); and it is legal only where `deferred` would have been (a
`--strict` close of disposition `annulled` is refused, same footing as `deferred`/`bookkeeping`).
`work_review_gap` treats an in-force `annulled` close as discharged with zero code change (its
existing exact-equality filter on `'deferred'` already excludes it).

**NOT applied to autoharn3 or any other already-born world — runs are linear.** `annulled` rides
the NEXT `--new-world` birth's `LINEAGE_CHAIN`. On a pre-s73 world (today's autoharn3 included),
attempting it — via `led work reclose <slug> <resolution> --review-annulled <ref>` (see the
`work-reclose-and-annulment-passthrough` note) — is refused by the kernel's own
`work_review_disposition_check` CHECK constraint, byte-verbatim, never faked client-side. If you
see that refusal, the world predates s73; this is expected, not a bug to chase.

Scratch-witnessed only (`seen-red/s73-typed-annulment-disposition/`), both polarities, `./judge
--layer work` AGREE on both worlds, 27 cases green (recounted against the fixture's own
`red.txt`, which carries 27 `[ok]` lines).
