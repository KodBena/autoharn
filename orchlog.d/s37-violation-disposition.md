subject: d691880
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

s37 (violation disposition) landed. This is the delta your orphaned-children incident
commissioned, and its final semantics make most of your cleanup already done:

**Debt now quantifies over in-force rows.** After migration, a violation whose target
row has been superseded lapses from `work violations` automatically — the retraction IS
the answer. Your five orphan rows: the ones whose situation you already repaired by
supersession clear on their own; run `./led work violations` after migrating and expect
a much shorter (likely empty) list. The complete record — every defect, what answered
it (a disposition, a retraction, or still open) — lives in the new
`work_violation_history` view, forever.

**For anything still standing in debt:** `led work resolve-violation <target-id>
<reissued|retired> "<basis>" (--review-witness <ref> | --review-deferred)
[--witness <successor-ref>] [--supersedes <old-disposition-id>]` — one reviewed,
attributable act per violation. Wrong disposition? Correct it with `--supersedes`.
Plain duplicates are refused with a teach-text. Deferred-review dispositions land in
your ordinary review-gap queue.

**Planning to supersede a parent that still has live children?** `led work
supersede-cascade` walks the whole ripple in dependency order (re-opens live children
under new slugs, re-edges, writes the dispositions). Closed children stay put.

**Also fixed in the same wave:** informs-type dependency cycles no longer surface as
violations (advisory edges never gated anything; a mutual informs citation is
legitimate); the stop-gate's orphan debt lines now name the discharge path instead of
calling legal orphans a "kernel anomaly"; and `work violations` output names the
resolving command per row.

Known CLI gap, tracked upstream (`resolve-violation-class-ambiguity`): a target
matching two violation classes at once refuses with "matches more than one class" —
if you hit it, report which classes; do NOT work around it with raw SQL (standing
instruction: a missing verb is a backflow note, never an UPDATE).

Migration: the usual recipe — end the session, maintainer pulls + runs `./migrate`
(s37 carries its HISTORY: safe header and detect), restart, `./pickup`.
