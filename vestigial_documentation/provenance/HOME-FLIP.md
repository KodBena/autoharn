# HOME-FLIP — the transition record (PREPARED; the maintainer performs the flip)

The consolidation mandate (§5) records a HOME-FLIP: the moment autoharn becomes the
**authoritative** home and the two old repos become **read-only evidence archives**. Before the
flip, the old repos are authoritative and autoharn holds migrated COPIES (the transient two-writer
window the mandate accepts, §3 risk 4). After the flip, **provenance direction reverses**: autoharn
is the source of truth, and `MIGRATION.tsv` reads as "where each file CAME FROM" rather than "where
the authoritative copy still lives."

**This is a maintainer act.** The builder prepares this record and verifies the preconditions; the
builder does **not** flip. Filing a flip the maintainer did not make would be the forged-authority
failure the POST-FABLE brief names. The maintainer ratifies the flip by recording it (an
`acts.ruling` row or an equivalent attributed act), and — as a separate daylight step — schedules
the old-repo archive banners.

## Preconditions (builder-verified before handing this over)

- [x] The 253-target migration (mechanical census: **347 tracked files** — the manifest's ≈253
  headline counted research as corpora; see the reconciliation in the handback) landed with
  per-file provenance in `MIGRATION.tsv`, reconciled 1:1 against `migration_manifest.tsv`.
- [x] Every recorded adaptation is on BUILD-BRIEF §0's closed list (plus the flagged extensions:
  the import-path-fix class occurred in `filing/`, `kernel/fixtures/`, `drive/` — locations §0's
  enumeration did not name; extended by the same principle, each recorded with its diff in
  `provenance/adaptations/`).
- [x] The s19 increment forecloses the set_actor schema-literal class (findings 16/37/45),
  both-polarity proven on a non-default-schema kernel.
- [x] The mandate-§6 acceptance ran from a fresh clone (record in `runs/`).
- [ ] **Two-writer sha re-verification (the maintainer's confirmation gate).** Immediately before
  the flip, re-verify the whole `MIGRATION.tsv` against BOTH sides: each migrated file's source
  sha256 must still match `git show <source_commit>:<source_path>` in the old repo (proving the
  archive did not drift), and any autoharn divergence beyond a recorded adaptation is a FINDING,
  not a merge. (The old repos were never written by this build — only read via `git show` — so this
  should be clean; the check is the control, §3 risk 4.)

## The two acts that are the maintainer's (prepared, not performed)

1. **Ratify this HOME-FLIP** — record the attributed act that makes autoharn authoritative and
   reverses provenance direction. From here on, a change lands in autoharn; the old repos are frozen.
2. **Schedule the old-repo archive banners** — a separate daylight step that marks
   `claude_harness` and `epistemic-operator` read-only-archive at their heads (standing services and
   banked evidence untouched; the NLP attic keeps running where it runs).

Until both acts exist, autoharn is the migrated candidate home and the old repos remain
authoritative.
