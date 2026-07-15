# kernel/lineage/ — the subject decision-ledger DDL lineage

This directory holds the SQL files that build autoharn's decision-ledger database (the
append-only `ledger` table plus its supporting views/triggers every governed world runs on —
"world" names one deployed instance of this kernel, e.g. a scaffolded project or a throwaway
scratch deployment; "governed" means its edits are policed by the pre-commit change gate this
project ships), in the exact order a maintainer or scaffold script applies them. Read this file if you are
provisioning a new kernel by hand, or trying to work out which SQL file added a given column,
view, or refusal. For the first time this lineage is `ls`-legible AS a lineage: in an earlier,
predecessor codebase (a repository this project's own history traces back to, referenced here
only as "the old repos" because no further detail survives in this document) the same pieces
were scattered across a directory named `epistemic-operator/harness/e*-build/`, invisible as
one connected thing.

## The idiom switch — standalone generations, then additive deltas

- **s10 … s15 are STANDALONE full-schema generations.** Each `sNN-schema.sql` recreates
  the whole kernel from scratch at that generation (its own `principal`/`ledger`/triggers).
  You apply exactly ONE of them to stand up a kernel of that generation. s15 is the
  current generation: the s13 kernel, plus one ratified addition this lineage calls
  "Ruling A" — a typed `antecedent` column on the ledger's review-detail table, recorded
  inline in `s15-schema.sql`'s own header comment (search that file for "Ruling A" to read
  the ruling's exact words) — applied in a scratch database used only for that ruling's own
  proof, never a live deployment's kernel.
- **s17+ are ADDITIVE DELTAS chained on s15.** Each is an `ALTER`/`CREATE OR REPLACE`
  increment applied ON TOP of an s15 base. This keeps the kernel body itself — roughly 342
  lines as of s15 — in exactly one place rather than hand-copied into every later file
  (the single-source-of-truth principle [ADR-0012](../../law/adr/0012-compositional-and-structural-hygiene.md)
  P1 states generally). The apply order for the kernel as it stood through s19:

  ```
  s15-schema.sql
    → s17-stamp-mechanism.sql          (stamp_secret + HMAC stamp columns + set_stamp)
    → s17-independence-vocabulary.sql  (self-review vocab + stamp-distinctness)
    → s18-criterion-principals.sql     (INSERT-only criterion-reviewer principals)
    → s19-trigger-search-path.sql      (forecloses the set_actor schema-literal class — findings 16/37/45)
  ```

  **This list has not been kept current past s19** — a known, named gap this note narrows
  but does not fully close (see the next paragraph for the honest current source).
  `bootstrap/new-project.sh`'s own `LINEAGE_CHAIN` variable is the CURRENT, authoritative
  apply order for a freshly-scaffolded world, re-derived live at every scaffold rather than
  hand-copied into this file. This README deliberately does NOT restate that chain
  entry-by-entry: an enumerated copy here drifted stale twice in one day (first silent on
  s26, then wrong about s28's wiring status — the second staleness was caught by a
  fresh-context review of this very paragraph), so the durable instruction is: read it at
  the source, `grep LINEAGE_CHAIN bootstrap/new-project.sh`, which as of 2026-07-12 runs
  from s15 to `s28-work-parent-edge.sql` (s18 excepted — deliberately excluded, see the
  `high_watermark_1.sql` bullet below), every entry applied automatically by a
  `--new-world` scaffold.

  **`high_watermark_1.sql` is NOT "the current user-facing kernel" — it is the s19-era
  BASE.** An earlier version of this file called it "the current user-facing kernel" and a
  stranger following the main [`README.md`](../../README.md)'s deploy walkthrough would
  land there and stop, under-deployed by the nine deltas this lineage has shipped since s19
  (s20 through s28 as of this writing): a Postgres-permissions fix (s20), a fix to who counts
  as a genuinely independent reviewer (s21, see above), a work-item tracking mechanism (s22),
  a per-write identity token (s23), a caller-declared event timestamp separate from the
  database's own write time (s24), a `'commission'` value added to the ledger's `kind`
  vocabulary — this project's own term for a maintainer's initial ask, recorded as its own
  row type (s25), a tamper-evident row-hash chain (s26, s27), and a typed parent-item edge for
  work items (s28, "work-parent edge" below). `high_watermark_1.sql` is exactly what its own
  header says and no
  more: the one-shot apply script for `s15 → s17-stamp → s17-independence → s19`. The
  CURRENT chain, for any purpose, is always the live one defined by `LINEAGE_CHAIN` above —
  never a single generation named "current" in this file. **The supported way to reach the
  actual head on an existing or partial deployment is `./migrate <deployment-dir>`** (the
  repo-root verb, run from this autoharn checkout): it re-derives the same live manifest,
  detects which deltas your deployment's schema is missing via each delta's `.detect.sql`
  sibling (see `bootstrap/migrate_core.py`'s module docstring, "PER-DELTA VERIFICATION
  CONVENTION"), rehearses the missing chain against a scratch restore of a real backup, and
  asks exactly one typed confirmation before touching live. A brand-new deployment's route
  is therefore: apply `high_watermark_1.sql` for the base (this file, the bullet below, or
  `bootstrap/new-project.sh --new-world` for a from-scratch throwaway world, which applies
  the WHOLE current chain in one call), then run `./migrate <deployment-dir>` to carry that
  base to head — never reverse-engineer `bootstrap/new-project.sh`'s shell variables to
  guess the chain by hand.

  The two newest deltas both live beside this README in this same directory:
  `s27-chain-high-water.sql` (a table + trigger that record the ledger's current tail row,
  so a later reader can WITNESS — detect, not merely trust — that no row was ever deleted off
  the end of the append-only chain; tracker item `s26-tail-deletion-witness`) and
  `s28-work-parent-edge.sql` (a new, CHECK-typed `work_parent` column linking a work-item row
  to the parent work item it decomposes from; tracker item `work-tree-rollup` — "tracker item"
  names a work item in this project's own Postgres ledger, and the slug is the short
  identifier that ledger tracks it by). Each was authored and scratch-witnessed independently
  (both-polarity proofs at [`seen-red/s27-chain-high-water/`](../../seen-red/s27-chain-high-water/)
  and [`seen-red/s28-work-parent-edge/`](../../seen-red/s28-work-parent-edge/) in the
  repository root), then wired into `LINEAGE_CHAIN` by
  one integrator merging both authored deltas into the shared `bootstrap/new-project.sh`
  script — deliberately left to one person so two concurrent builders never raced edits to the
  same shared file. s28 does not depend on s27, which
  was checked directly by applying s28 on top of only s15 through s26 and confirming it
  still works (see s28's own file header, its "PARAMETERIZATION" section, for the exact
  command).

- **Side entries.** `nla-schema.sql` is a catalog-isolated re-instantiation of the same kernel
  design under a different, parallel subject-matter profile named `nla` — a separate domain
  this project also studies, distinct from and never merged with the `s`-numbered generation
  line above (not a generation in the s-line). `s13-remediation-review-detail-
  truncate-guard.sql` is a targeted remediation delta on the s13 generation.
- `high_watermark_1.sql` is the derived one-shot apply script for the s19-era BASE kernel
  (see the "NOT the current user-facing kernel" paragraph above — it is a starting point,
  not a destination): it chains `s15 → s17-stamp → s17-independence → s19` for you in one
  `\ir`-based psql script that owns no DDL of its own. It deliberately excludes
  `s18-criterion-principals.sql`, which is this project's own internal experiment apparatus
  (a separate study harness applies s18 explicitly on top, when it needs it). A future
  kernel delta lands as a new `sNN` file plus a new `high_watermark_N.sql`.

## Never retro-edit an `sNN` record ([ADR-0005](../../law/adr/0005-documentation-discipline.md) Rule 8)

Each `sNN-schema.sql` is a point-in-time record. A defect discovered in a shipped
generation is foreclosed by a NEW dated increment (the s19 pattern), never by editing the
frozen file. That is why s13/s14/s15 still carry the historical `set_actor` `kernel.`
hardcode: they are frozen records; the live deployment applies s15 **plus s19**, and s19
is the structural foreclosure of that class.
