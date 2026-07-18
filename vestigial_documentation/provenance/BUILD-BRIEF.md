# BUILD BRIEF — the executable consolidation increment (for an Opus builder)

- **Served model of the designer (self-report):** claude-fable-5 (no introspective
  channel could detect a silent substitution). The builder records ITS actual served
  model at the top of its run record — degraded models are never relabeled.
- **Status:** DESIGN. Nothing runs until the maintainer has scanned LAYOUT.md +
  MIGRATION-MANIFEST.md + this brief and said go (mandate process law).
- **Read first, in full, in this order:** `docs/CONSOLIDATION-MANDATE.md`;
  `docs/consolidation/LAYOUT.md`; `docs/consolidation/MIGRATION-MANIFEST.md`; the four
  LAW files named in `CLAUDE.md` (ADR-0000/0012/0013/0014) **plus ADR-0008**;
  `epistemic-operator/POST-FABLE-OPERATING-BRIEF.md`. The spirit governs over the
  letter; a hazard met in passing is fixed or flagged loudly, never routed around.

## 0. Standing constraints on the builder (non-negotiable)

Commit, never push. Public-repo identity `bork <you@example.com>`. Every commit
declares `CLAUDE_COMMIT_PATHS` (staging guard); never `git add -A`. Ephemera persisted
whole-session after any agent activity — into the NEW repo's `ephemera/` once it
exists, and per current law in the source repos. No Fable sub-spawns; dense psql goes
through Sonnet relays; a relay's description is a claim — spot-check load-bearing rows.
Evidence ledgers strictly read-only; `tainted/` never read; **NEVER run
`ledger_dto_scratch.py` against the live scratch** (it would erase the maintainer's
authentic attestation act). No new rulings; anything ruling-shaped routes to the
maintainer. No paid services. The old repos are never reorganized in place (mandate
§5): this increment only COPIES out of them; the single sanctioned old-repo edits are
(a) this design's own commits and (b) the post-flip archive banners, which are a
separate, maintainer-triggered daylight step.

**Recorded-adaptation rule.** A migrated file is byte-identical to its source except
for entries on this closed list, each flagged `adapted` in `provenance/MIGRATION.tsv`
with the diff recorded: `CLAUDE.md`/`README.md`/`.gitignore`/`.claude/settings.json`
(new-repo paths), `hooks/pre-commit` (repo-relative gate invocation),
`filing/persist_claude_ephemera.py` (target `ephemera/`), `instruments/ledger_target.py`
(registry entries for autoharn substrates), import-path fixes in `engine/`,
`instruments/`, `stores/` (the old flat-directory imports like `import clingo_run`
become the new layout's imports), `drive/arm.sh` + `drive/launch.conf.template`
(parameterization of e18/e17 specifics), `design/ARCHITECTURE.md` (STALE banner + a
BACKLOG entry), `gates/doc-legibility/check.py` (scope widened to all tracked `*.md` —
maintainer ruling 2026-07-07, finding 48). Any edit outside this list is a scope
defect: stop and renegotiate (ADR-0013 Rule 1).

## 1. Ordered steps

**Step 1 — init.** Create `~/w/vdc/1/autoharn`, fresh history. Write `.gitignore`,
root doc skeletons (README.md pointing at the tree; CLAUDE.md adapted), the empty
`runs/` and `ephemera/` homes (each with a two-line README naming its currency — no
bare `.gitkeep`). `git config core.hooksPath hooks`. First commit.

**Step 2 — gates first.** Migrate `gates/` + `filing/` + `hooks/` per manifest A3,
wire `hooks/pre-commit` (staging guard + no_lazy_imports immediately; census gates
join as they are minted below). Every subsequent migration commit runs under the new
repo's own gates — the migration itself is the gates' first live exercise.

**Step 3 — provenance machinery.** A small copy tool that, for each manifest row,
copies the file and appends `source_repo, source_path, dest_path, source_commit,
sha256, adapted?` to `provenance/MIGRATION.tsv`. It refuses a copy not present in the
manifest (both polarities: prove the refusal). Reconciliation check: TSV ↔ manifest
1:1, run as part of Step 9's acceptance.

**Step 4 — law, judgment, evidence-that-migrates, design, research.** Migrate manifest
sections A4–A6, A11 (MIGRATE rows), B1, B5 (MIGRATE rows), and `seen-red/` verbatim.
Nothing here needs adaptation except the ARCHITECTURE banner.

**Step 5 — stores + kernel.** Migrate A2 and B4's DDL in lineage order (`stores/`
001→007; `kernel/lineage/` s10→s18 + nla + remediation). Apply and prove on THROWAWAY
schemas/databases only (the arm-script idiom), via Sonnet relay for psql; the fixtures
(`stores/*_fixture.py`, `kernel/fixtures/*`) must run green from the new repo. A
`kernel/lineage/README.md` states the idiom switch (s10–s15 standalone generations;
s17+ additive deltas chained on s15).

**Step 6 — the set_actor foreclosure (ADR-0000 Rule 2, not a patch).** The migrated
s15 carries `set_actor()` reading `kernel.principal_role` literally while the table
lives in the parameterized `:kern` schema; the sibling `set_stamp()` resolves via
`SET search_path`. Findings 16, 37, and 45 are three instances of ONE class: *a
schema-parameterized kernel with an un-parameterized reader somewhere in the write's
whole invocation chain*. Closure statement: **invariant** — every kernel trigger/
function resolves kernel objects via the search_path mechanism, never a hardcoded
schema literal; **universe** — the full trigger/function family across all lineage
generations and the SECURITY-INVOKER chain behind every INSERT (the finding-45 axis),
enumerated by grep over `kernel/lineage/`; **denomination** — the resolution mechanism
itself (search_path), not a copied schema name. Ship it as a NEW dated lineage
increment `kernel/lineage/s19-trigger-search-path.sql` (never retro-edit sNN records —
ADR-0005 Rule 8 applies to lineage files), with a both-polarity fixture on a
NON-default-schema kernel (an actor-omitted write succeeds; the pre-fix shape provably
fails) and a `seen-red/` entry. This is in scope because the migration is the touch:
carrying a known, thrice-filed defect into the fresh home untouched would be
narrated-and-left (ADR-0013 Rule 4).

**Step 7 — instruments + engine.** Migrate B2, B3, A8 with import-path fixes.
`ledger_target.py` keeps its SSOT mechanism; its `_SPECIAL` registry entries that pin
fenced-dir/session-dir paths are re-verified resolvable from autoharn (the
instance-pinned-substrate class, finding 36/fc18 — no silent fallbacks; unresolvable →
loud). Then prove: all `instruments/verify_*.py` fixtures green; `soundness_twin`
differential green; `run-core-a.sh` green AND its `--negative-control` red;
`engine/tests/` green against a scratch substrate; `verify_registry_parity.py` green
against `registry_baseline.json`.

**Step 8 — drive.** Migrate B4's drive set. Parameterize `drive/arm.sh` from
`arm_e18.sh` (run-specifics become `launch.conf` inputs; the mechanical check
structure — DDL-on-throwaway, frozen-text sha, hook interceptability, fixtures,
delivery-set emission — is preserved intact). Run `delivery_drill.py --check` and the
`drive/rehearsal/` mock-close toolchain end-to-end: the mock close must be provably
distinguishable from a real one (the negative-control-on-the-meta-toolchain
discipline).

**Step 9 — mint the two census gates, complete the pre-commit.**
- `gates/fixture_census.py` [manifest C20]: registry of every gate/close-line ↔ its
  `seen-red/<gate>/` entry (red + green present) ↔ its runnable fixture. RED on: a
  gate without both-polarity proof, an orphaned seen-red dir, a registry entry whose
  fixture cannot run. Mechanizes mandate §6's "every migrated gate's seen-red still
  proves it can fail".
- `gates/layout_census.py` [manifest C21]: LAYOUT.md's tree as a machine-readable
  registry — top-level allowlist + per-directory content patterns (`stores/` only
  `NNN_*.sql`/`*_fixture.py`/`test_*.py`; `law/adr/` only `NNNN-*.md`;
  `kernel/lineage/` only `*.sql` + README; `seen-red/` only per-gate dirs; `runs/`
  only run-id dirs; …). RED on an unregistered top-level entry or a pattern breach.
  The single-currency JUDGMENT for new files inside a directory is review-only and
  declared so (ADR-0011 Rule 1).
Both gates ship with their own seen-red entries (a census gate never seen red is the
joke that writes itself). Final pre-commit: staging guard → no_lazy_imports →
fixture census → layout census → doc-legibility (widened scope).

**Step 10 — the executed acceptance run (mandate §6, from a FRESH CLONE).** Clone
`~/w/vdc/1/autoharn` to a scratch path, and from the clone: (a) `bootstrap/bootstrap.sh`
runs green (env, gates, hook install, DB reachability — reachability failure prints
the pg_hba/host facts, it does not soft-pass); (b) a real mini-collaboration exercises
the decision ledger and the refuse-and-teach gate (the change gate refuses an
unticketed edit and teaches; the kernel stamp path exercised); (c) a close runs
against the new layout's instruments via `close_manifest.py` — its record is the first
occupant of `runs/`; a "(none)" from any instrument must be provably distinct from
"did not run" (F49); (d) the gates run from the new repo's OWN pre-commit on a real
commit; (e) fixture census green — and for each migrated gate class, one live red
re-executed from the clone, not cited from the archive. Acceptance is executed, not
asserted; the run record + outputs are committed under `runs/`.

**Step 11 — hand back for the HOME-FLIP.** Persist ephemera (both repos + autoharn),
commit everything, and deliver the maintainer a plain-language checklist: what was
verified, the TSV↔manifest reconciliation result, the open risks below, and the two
acts that are HIS — ratifying the HOME-FLIP record (`provenance/HOME-FLIP.md`:
provenance direction reverses; autoharn becomes authoritative) and scheduling the
old-repo archive banners as a daylight step (standing services untouched). The builder
prepares both texts; the builder performs neither act.

## 2. Acceptance criteria (verbatim, CONSOLIDATION-MANDATE.md §6)

> **Acceptance is executed, not asserted:** from a fresh clone of the new repo — the
> bootstrap runs green; a real mini-collaboration exercises the ledger and the
> refuse-and-teach gate; a close runs against the new layout's instruments; the gates
> (no_lazy_imports, staging guard, fixture census) run from the new repo's own
> pre-commit; every migrated gate's seen-red still proves it can fail.

## 3. Honest risks (surfaced, not shrugged)

1. **The pg_hba bound.** Every DB-touching proof assumes host-based auth as configured
   today (harness DB at `192.168.122.1`; kernel substrates per `ledger_target`). From
   this guest the fresh clone works; from any other host/user it will not until the
   maintainer changes pg_hba — a maintainer act, named in the Step-11 checklist, never
   worked around with credentials in the repo. Corollary (finding 45): privilege
   verification covers the WHOLE invocation chain a write triggers (SECURITY-INVOKER
   trigger reads), not the table ACL — re-run the grant fixtures from the new repo,
   don't inherit green.
2. **The set_actor class.** Three findings (16/37/45), one class; the discarded
   attempt's CENSUS documented the s15 instance precisely and correctly declined to
   patch a byte-pinned copy. Step 6 forecloses it structurally in the authoritative
   home. Risk if skipped: every non-default-schema deployment refuses actor-omitted
   writes — the acceptance clone would hit it on its first sandboxed kernel.
3. **Cross-repo paths in migrated documents.** Governing consults and briefs cite
   `claude_harness/…` and `epistemic-operator/…` paths. Quoted evidence is NEVER
   rewritten; `provenance/PATH-TRANSLATION.md` maps path prefixes old→new, and the
   archives keep every cited path valid forever. New documents cite new paths.
4. **The two-writer window.** Between first copy and HOME-FLIP, both repos hold copies
   of the migrated surface — the transient P1 violation the mandate accepts. Control:
   sha re-verification of the whole TSV against both sides immediately before the flip;
   any divergence is a finding, not a merge.
5. **Instance-pinned substrate residue.** `ledger_target`'s `_SPECIAL` registry and any
   instrument path constants are exactly the finding-36 class; Step 7's re-verification
   is the control. Watch for it in `drive/` too (arm/launch paths).
6. **Ephemera capture across the move.** Claude Code keys ephemera by working-directory
   slug; sessions run from autoharn write a NEW slug. `persist_claude_ephemera.py`'s
   adaptation must be verified against a real session before the acceptance run's
   ephemera are trusted to it (never assert loss without searching every slug).
7. **Standing services.** The attic keeps the NLP daemons and their umbrella gate;
   nothing in this increment may touch them. Do not run the ~3.25 GB standing-service
   net from the new repo; it has no services there to gate (a vacuous pass, F49 class).
8. **Import-path fixes are the largest hand-edit surface.** The old flat directory let
   modules import each other bare; the new layout makes those imports explicit. Every
   fix is mechanical, gated by `no_lazy_imports` + the migrated test suites — but a
   missed one fails at import time only where a test imports it; the engine test run in
   Step 7 is the net, and any module with NO test coverage gets an import smoke check
   in `bootstrap.sh`.
9. **Builder tier.** This brief is sized for an Opus builder: every step has a
   mechanical proof and no step requires new odd-link judgment. Where judgment gaps
   appear anyway, the POST-FABLE partition applies — park it as a filed finding or
   route it to the maintainer; never improvise law.
