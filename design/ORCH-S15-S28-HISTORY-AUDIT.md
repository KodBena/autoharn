# s15–s28 history-validation class audit

Built under design/MAINT-MIGRATION-ACCOMMODATIONS-SPEC.md section 3, item 2 (ledger work item
`s26-accommodation-build`). Every history-validating statement (`ADD CONSTRAINT` without `NOT
VALID`, `ALTER COLUMN ... SET NOT NULL`, a two-way `CHECK`, any statement that VALIDATES
pre-existing rows at apply time — spec sec-1's own class definition) in every frozen kernel
lineage delta from `high_watermark_1.sql`/`s15-schema.sql` through `s28-work-parent-edge.sql`,
enumerated and dispositioned SAFE-OVER-HISTORY or NEEDS-ACCOMMODATION. This table is the
deliverable even where the answer is "safe" (spec sec-3, item 2's own instruction) — it is also
the external record `bootstrap/migrate_core.py`'s forward-binding HISTORY: header rule (sec-3,
item 3) points to for why this fixed set is exempt from carrying the header itself (ADR-0005
Rule 8 — a frozen file is never edited to add one).

Method: every `ALTER TABLE`/`ADD CONSTRAINT`/`SET NOT NULL`/`ADD COLUMN` statement in each file
was enumerated by direct grep (`grep -niE 'ALTER (TABLE|COLUMN)|ADD CONSTRAINT|SET NOT NULL|ADD
COLUMN|CHECK \('`), then each one read in full and dispositioned by one of three arguments:
(a) the table it touches is CREATED in the same file (no history can exist for it at apply
time — a birth-of-table statement, not a migration-over-history one); (b) the statement's own
CHECK predicate is provably VACUOUS on every historical row (a brand-new nullable column with
no prior rows ever populating it, or a `kind`/enum widening that is a strict superset of the
prior vocabulary, so every historical value that satisfied the OLD check automatically satisfies
the NEW one); (c) NEEDS-ACCOMMODATION — an unconditional statement that validates ALL rows
without regard to when they were written. Disposition (a)/(b) is additionally WITNESSED, not
merely reasoned, on a byte-faithful rehearsal clone of the real `autoharn1` deployment (997
pre-existing rows, head `s25-commission-kind.sql` as of this build) — see the WITNESS section
below.

## Audit table

| Delta | History-validating statement(s) | Disposition | Argument |
|---|---|---|---|
| `high_watermark_1.sql` | none found | SAFE (vacuous) | No `ALTER`/`ADD CONSTRAINT`/`SET NOT NULL` in the file at all. |
| `s15-schema.sql` | `ledger.kind`/`status`/`confidence`/`concern` `CHECK`s; `review_detail.verdict`/`independence` `CHECK`s; `countersign_obligation` ADD CONSTRAINT `obligation_not_self_assigned` | SAFE (a) | Every one of these is inside the `CREATE TABLE` that defines the table, or (for `countersign_obligation`'s constraint) immediately follows that table's own `CREATE TABLE IF NOT EXISTS` in the same file — no history can predate a table's own creation. |
| `s17-stamp-mechanism.sql` | `ADD COLUMN stamp_session/stamp_agent/stamp_ts/stamp_hmac` (nullable); `ADD COLUMN stamp_verified boolean NOT NULL DEFAULT false` | SAFE (b) | The four nullable columns admit any historical row trivially. `stamp_verified`'s `NOT NULL DEFAULT false` is a single `ADD COLUMN ... DEFAULT` statement — PostgreSQL ≥11 backfills a non-volatile default for existing rows as a metadata-only operation, never a per-row validation scan; witnessed directly (this build's own rehearsal clone carries this column from its s25 head with no failure at this line). |
| `s17-independence-vocabulary.sql` | `review_detail` DROP+ADD CONSTRAINT `review_detail_independence_check` (widens `('technical','managerial','financial')` to `('self-review','technical','managerial','financial')`) | SAFE (b) | Strict superset of the prior allowed set — any row satisfying the old CHECK satisfies the new one by set inclusion, independent of what the table actually contains. |
| `s18-criterion-principals.sql` | none found (INSERT-only criterion-reviewer principals, per kernel/lineage/README.md) | SAFE (vacuous) | No `ALTER TABLE`/`ADD CONSTRAINT` in the file. |
| `s19-trigger-search-path.sql` | none found | SAFE (vacuous) | Trigger-body fix only (forecloses a schema-literal class); no DDL that validates rows. |
| `s20-obligation-grants-and-view-refresh.sql` | none found | SAFE (vacuous) | GRANT + `CREATE OR REPLACE VIEW` only. |
| `s21-session-aware-distinctness.sql` | none found | SAFE (vacuous) | View/trigger-body fix only. |
| `s22-work-item-ledger.sql` | `ledger` DROP+ADD CONSTRAINT `ledger_kind_check` (widens the `kind` vocabulary to add `work_opened`/`work_claimed`/`work_depends_on`/`work_closed`); `ADD COLUMN work_slug/work_title/work_depends_on/work_resolution/work_witness` (all nullable); `work_slug_kind_shape`/`work_title_kind_shape`/`work_depends_on_kind_shape`/`work_resolution_kind_shape`/`work_witness_kind_shape` (two-way CHECKs correlating `kind` with the new columns); `work_resolution_check`; `work_shipped_requires_witness` | SAFE (b) | `ledger_kind_check` is a strict superset (see s17-independence-vocabulary's own argument, same shape). Every shape CHECK is of the form `(kind IN (new-kind-set)) = (col IS NOT NULL)` or `col IS NULL OR ...` — for every historical row, `col IS NULL` (the column is brand new) and `kind` cannot be one of the new kind values (they did not exist in the vocabulary until THIS file's own `ledger_kind_check` widening, applied first in the same statement sequence), so both sides of every correlation are false/vacuous simultaneously. `work_resolution_check`/`work_shipped_requires_witness` are `work_resolution IS NULL OR ...` — vacuous for every historical row (`work_resolution` is new and NULL throughout). |
| `s23-per-invocation-stamp-token.sql` | `ADD COLUMN stamp_invocation` (nullable) | SAFE (b) | Nullable, no CHECK. |
| `s24-declared-event-time.sql` | `ADD COLUMN event_declared_ts timestamptz` (nullable) | SAFE (b) | Nullable, no CHECK. |
| `s25-commission-kind.sql` | `ledger` DROP+ADD CONSTRAINT `ledger_kind_check` (widens to add `'commission'`) | SAFE (b) | Strict superset of s22's own widened list — same argument, one generation later. |
| `s26-row-hash-chain.sql` | `ADD COLUMN row_hash` (nullable); **`ALTER COLUMN row_hash SET NOT NULL`** | `ADD COLUMN`: SAFE (b). **`SET NOT NULL`: NEEDS-ACCOMMODATION** | `ADD COLUMN row_hash text` (no default, nullable) is inert against history. The unconditional `SET NOT NULL` VALIDATES every existing row's `row_hash IS NOT NULL` — false for every pre-existing row (the column did not exist before this file). This is the row-972 blocker (ledger finding row 972); cured by `kernel/lineage/s26-row-hash-chain.accommodate.sql`, this build. |
| `s27-chain-high-water.sql` | `CHECK (only_one)` on the new `:kern.chain_high_water` table | SAFE (a) | The table is created in the same file; no `ledger`-level `ALTER`/`ADD CONSTRAINT` at all. |
| `s28-work-parent-edge.sql` | `ADD COLUMN work_parent` (nullable); `work_parent_kind_shape` (`work_parent IS NULL OR kind = 'work_opened'`); `work_parent_not_self` (`work_parent IS NULL OR work_parent IS DISTINCT FROM work_slug`) | SAFE (b) | `work_parent` is new and NULL on every historical row, satisfying both `OR`-guarded CHECKs unconditionally on the `IS NULL` branch. |

**Result: exactly one NEEDS-ACCOMMODATION statement in the entire s15–s28 range** — s26's
`ALTER COLUMN row_hash SET NOT NULL`. Every other history-validating statement in this range is
SAFE-OVER-HISTORY by construction (same-file table birth, or a check vacuous/superset over
brand-new-and-NULL or widened-vocabulary content).

`s29-obligation-item-key-and-typed-close.sql` is OUT OF SCOPE for this table (the spec's own
audit boundary is s15 through s28) and is separately exempted from the forward-binding HISTORY:
header rule in `bootstrap/migrate_core.py` because it already resolved its own history posture
inline, substantively, via its sec-10 `migration_epoch` amendment
(design/MAINT-COUNTERSIGN-CLOSE-SEMANTICS-SPEC.md) — the same shape this spec generalizes, ahead
of this spec's own ratification.

## Witness (WP: rehearsal clone of real `autoharn1` history)

- `pg_dump -h 192.168.122.1 -d toy -n autoharn1 -n autoharn1_kernel` → restored into scratch
  schemas `s26clone`/`s26clone_kernel` in the same `toy` database, via
  `bootstrap/migrate_core.py`'s own (fixed, this build) `_rename_identifiers_outside_copy_data`
  — byte-faithful: row content mentioning "autoharn1" in prose is preserved verbatim; only
  catalog identifiers are renamed. 997 rows, max id 1026, head `s25-commission-kind.sql`
  confirmed (no `row_hash`/`work_parent` columns, no `chain_high_water` relation).
- `./bootstrap/migrate.sh <clone-deployment-dir> --dry-run`, BEFORE this build's accommodation
  existed (accommodate.sql temporarily absent from the working state during this specific probe):
  REHEARSAL APPLY FAILED at exactly `kernel/lineage/s26-row-hash-chain.sql:353` —
  `ERROR: column "row_hash" of relation "ledger" contains null values` — the row-972 blocker,
  reproduced directly against real history, confirming every OTHER delta in the missing chain
  (s27, s28, s29) is reached with no failure of its own once s26 is passed.
- Same rehearsal, WITH `kernel/lineage/s26-row-hash-chain.accommodate.sql` present: REHEARSAL
  PASS end-to-end (HISTORY BYTE-IDENTITY PASSED 997 rows unchanged; PER-DELTA DETECT PASSED 4/4;
  PER-DELTA VERIFY PASSED 2/4 with a `.verify.sql`; CHAIN CHECK TAIL-COVERAGE-CONFIRMED). Full
  (non-dry-run) apply to the clone (never to real `autoharn1`) also PASSED end-to-end.
- Confirms s27/s28's own SAFE dispositions above hold over REAL history, not merely a
  synthetic toy world: both applied cleanly as part of the same 4-delta chain, no separate
  failure of their own.

Mechanized, reproducible both-polarity proof (a synthetic pre-s26 history, so this is not
dependent on any specific real deployment being reachable in the future): `python3
seen-red/s26-accommodate/run_fixtures.py`; registered in `gates/fixture_census.py`.

<!-- doc-attest-exempt: point-in-time build audit table (ADR-0017 Exceptions class), transcribes
a specific commission's grep+read enumeration and a specific rehearsal run; not living prose a
later touch should re-trigger legibility review for. -->
