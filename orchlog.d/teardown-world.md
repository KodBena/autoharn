subject: bf46599
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

**New operator verb: `bootstrap/teardown-world.sh <world> --db <db> --host <host> [...]`
— the scripted, witnessed teardown for a `--new-world` scratch scaffold (merged `bf46599`,
2026-07-18).** Filed because a prior session correctly REFUSED to hand-author `DROP SCHEMA
... CASCADE`/`DROP ROLE` prose-SQL against the shared toy host (no sanctioned verb existed
for it), leaving a throwaway world's schema/kernel/role behind for the maintainer to clean
up by hand — the gap this script closes. It mirrors `bootstrap/new-project.sh`'s
`--new-world` derivation exactly (`schema=<world>`, `kern=<world>_kernel`,
`role=<world>_rw`, with the same `--schema`/`--kern`/`--role` override flags for a
non-default scaffold), resolves what actually exists via catalog queries, prints the exact
drop plan before touching anything, and requires a typed world-name confirmation before
executing — deliberately a heavier ceremony than the retired `apply-delta.sh` typed
confirmation (CLAUDE.md's "runs are strictly linear" ruling killed that one for guarding an
action that could not actually go wrong; this one guards `DROP SCHEMA ... CASCADE`/`DROP
ROLE`, which is irreversible with no undo, so the ceremony here is load-bearing rather than
cargo-cult). Refuses `autoharn1` unconditionally (no flag overrides it) and refuses a
non-scratch-safe world name without `--force-non-scratch`. Verifies zero residue after
tearing down.

**If you are picking up a world scaffolded before this commit:** there was no sanctioned
teardown path at all — a scratch world's cleanup meant either living with the residue or
hand-typing the DROP statements this script exists specifically to make unnecessary.

Where the operator-facing detail lives: `user-guide/USER-RECIPES-FAQ.md` names
`bootstrap/teardown-world.sh` alongside `bootstrap/new-project.sh` in its guided-setup
walkthrough section; the script's own header comment carries the full rationale (including
why this ceremony was kept when the delta-apply one was deleted) and usage grammar.
