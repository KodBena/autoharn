subject: write-path-actor-completion (ledger decision row 1377)
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

Panel-facing: the ceiling you hit on closes is gone. `LED_ACTOR=item-countersign
./led work close <item> shipped --review-deferred` now lands `actor=item-countersign`
on the `work_closed` row — the exact case that failed five times (your rows 1710,
1716, 1719, 1732, 1746) now works, on every close constructor (`--review-witness`,
`--review-deferred`, and `--review-bookkeeping` all attribute identically) and on
both `led work close` INSERT branches (pre-s29 and s29+/s38). `led work depends`
(both edge_type branches, plus a `--supersedes` correction row) and `led work
resolve-violation` are wired the same way. Unset `LED_ACTOR` is byte-identical to
before — nothing you weren't already doing changes. An unregistered `LED_ACTOR`
name is refused before any write, same as the four paths that were already wired.

A consequence worth knowing before you rely on it, not a defect: **a close now
attributable to item-countersign changes who may countersign that close.**
`validate_review` (s21) checks a review's actor against the TARGET row's actor —
same actor, refused (segregation of duties: an author may not countersign their
own row). Before this fix, every close silently landed as `author`, so this rule
was effectively never live for closes done under a named LED_ACTOR — you were
countersigning rows that only *looked* like item-countersign's but the ledger
recorded as author's. Now that the close is genuinely item-countersign's, a
countersign attempted by item-countersign itself is REFUSED; a countersign by a
DIFFERENT registered principal (a third principal, or `author`) is accepted, same
as it always was for any other actor-attributed row. Witnessed both polarities on
a probe world: `LED_ACTOR=item-countersign ./led review <close-row> attest
self-review "..."` → refused (`a row's author may not countersign it`);
`LED_ACTOR=<third-principal> ./led review <close-row> attest self-review "..."` →
accepted.

If item-countersign carries a `countersign_obligation` (`led obligate`), its closes
now correctly accrue `review_gap` debt (they didn't before — the debt was silently
mis-keyed to `author`), and a distinct-actor countersign discharges it, witnessed
end-to-end on the probe world.
