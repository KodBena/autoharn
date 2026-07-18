# WALKTHROUGH — a decision ledger for your own project

<!-- doc-attest-exempt: doc-tree relocation mechanical edit (work item doc-tree-reorg-user-guide, ledger row 1620, 2026-07-18) -- relative link path(s) repointed to a sibling file's new location after a git-mv relocation elsewhere in the tree; no prose rewrite, same disposition as the v1.1.2 release-cut's own markers (commit 543a389). Removal condition: strike this marker and run the real A:B:C loop next time this file is touched for content, not just link repair. -->


Audience: adopter

In about ten minutes, this page walks you through standing up an append-only decision ledger
for a project of yours, filing a decision, reading it back, and tearing it down. Its worked
example is `../toy-project` (terminal-color optimization). Everything else in this repository —
the experiment apparatus in `drive/`, `seen-red/`, and the e-series (this project's own
run-numbered experiment logs) — is this project studying *itself*; you need none of it for this.

What you get, concretely: decisions are recorded as rows that cannot be edited or deleted
(append-only, trigger-enforced), are attributed to the connecting role — the database role your
session actually authenticates as, never a self-declared name — and are superseded only by
appending a new row, never by rewriting an old one.

## 0. Prerequisites

- `psql` on your PATH; the DB host reachable (`sh bootstrap/bootstrap.sh` checks this — its only
  DB access is a read-only `SELECT 1`).
- A throwaway database. The host's `pg_hba.conf` only admits registered databases, so run this **on
  the DB host itself**, not from your workstation:

  ```sh
  createdb toy
  ```

## 1. Apply the kernel

One file chains the frozen DDL lineage (s15 → s17-stamp → s17-independence → s19) with
`ON_ERROR_STOP` on, and creates nothing outside the schemas and role you name:

```sh
cd autoharn
psql -h <host> -d toy \
     -v schema=toycolors -v kern=toycolors_kernel -v role=toycolors_rw \
     -f kernel/lineage/high_watermark_1.sql
```

Pass all three `-v` vars, always — the underlying files have defaults that point at the project's
own deployment. (Status: executed green end-to-end 2026-07-09 on a fresh `toy` db. The
`NOTICE: trigger … does not exist, skipping` lines on a first apply are normal — that is the
re-runnable `DROP TRIGGER IF EXISTS` idiom finding nothing to drop.)

## 2. File a decision, read it back

One row per INSERT — a bulk multi-row INSERT is refused by design (each decision is logged at the
time of the event it records). Table names are written fully qualified (`toycolors.ledger`), so
nothing depends on ambient name resolution — with one exception: the `SET search_path` line is
**required, not convenience**. The kernel's validation triggers (the ones that check `enacts`,
`amends`, `answers`, and `review` links) resolve the ledger through the session's search_path;
without it, any row that *links* to another row fails with `relation "ledger" does not exist`.
(Plain unlinked decisions would work without it — but set it always, so the failure mode never
exists.)

```sh
psql -h <host> -d toy -c "
  SET ROLE toycolors_rw; SET search_path = toycolors, toycolors_kernel;
  INSERT INTO toycolors.ledger (kind, statement) VALUES ('decision','perceptual distance = CIEDE2000, not RGB Euclidean');
  INSERT INTO toycolors.ledger (kind, statement) VALUES ('assumption','output constrained to the 16 ANSI slots');"
```

```sh
psql -h <host> -d toy -tAc "
  SELECT l.id, l.kind, l.statement, p.name
  FROM toycolors.ledger l JOIN toycolors_kernel.principal p ON p.id = l.actor;"
```

The `actor` came from your connection, not from anything you typed. To change your mind later,
INSERT a new row with `supersedes = <old id>`; UPDATE and DELETE are refused by trigger.

The habit this buys: decision lands in the ledger, *then* the code gets written.

## 3. Tear down

Two commands undo everything section 1 created: drop the schema-bearing database, then drop
the cluster-global role.

```sh
dropdb toy        # on the DB host — removes schemas, tables, the pgcrypto extension
psql -h <host> -d postgres -c "DROP ROLE IF EXISTS toycolors_rw;"   # roles are cluster-global
```

## 4. Opening a new world (one world per run)

Sections 1-3 above stand up ONE schema by hand. If you are about to run an actual subject/agent
against the ledger — not just try the mechanism — use this instead, every time you start a new run.

**Why:** a run's subject must not see a sibling run's ledger history. `ledger_current`/T_now
computed over a mixed ledger reads as "in force" ACROSS runs that never happened together —
cribbing, bias, cross-run leakage into whatever the subject does next. Branches share only the
branch point (the kernel apply — schema, triggers, secret, roles); they never share each other's
rows. (Maintainer ruling, "one world per run," 2026-07-09 — see [BACKLOG.md](../BACKLOG.md).) The old habit of
reusing one schema across runs (`toycolors` across runs 0-2) is exactly the mistake this fixes:
run 2 is recorded as contaminated by run-1 visibility; a fresh world does not carry that risk.

**What you type** — one command stands up a whole portable project directory (ledger schema,
kernel, stamp secret, and the `led`/`judge`/`pickup` verbs), not just a bare schema:

```sh
bootstrap/new-project.sh <dest-dir> --new-world <world-name> --db <db> --host <host> [--name <name>]
```

- `<dest-dir>` — where the new project lives, e.g. `../run4` (a sibling of `autoharn`, never
  inside it). Pick the FINAL location up front — the scaffold bakes `<dest-dir>`'s absolute path
  into `.claude/settings.json` and `.claude/HOOKS.md` at this moment; moving the directory
  afterward leaves those files pointing at the old path (a real hazard — see the box below).
- `--new-world <world-name>` — derives the ledger schema, kernel schema, and role from ONE name
  (`<world-name>`, `<world-name>_kernel`, `<world-name>_rw`) so you never have to keep three
  strings in agreement by hand. Applies the current kernel lineage (s15 → s17-stamp →
  s17-independence → s19 → s20 → s21-session-aware-distinctness — s20 and s21 included by
  construction, never the pre-s20 shape (which left the `countersign_obligation` review-debt
  table ungranted to the roles that needed to read it — the "grants gap" s20 closed) nor
  s21's pre-fix shape (session-blind distinctness, which falsely refused an honest
  cross-session review; and the s19 residue, four `validate_*` functions that resolved the
  ledger via session `search_path` in a way `SET ROLE` could break — both closed by s21) and
  seeds a fresh stamp secret, both in one call.
- `--name <name>` — this project's own identifier for `judge`'s target-name argument. Defaults to
  `<dest-dir>`'s basename; give it explicitly if that basename would collide with autoharn's
  curated target names (`toy`, `nla`, `e15`-`e18`) or its scratch-naming conventions
  (`^s\d+[a-z]*$`, `*_scratch`).

**What you should see** (abbreviated real capture, witnessed against a throwaway world
`runverbprobe`/`runverbprobe_kernel`/`runverbprobe_rw` on the same `toy` db, then torn down
(`DROP SCHEMA ... CASCADE` ×2 + `DROP OWNED BY`/`DROP ROLE` + `rm -rf`) — the mechanism witnessed
here is identical to what a real run gets; only the schema name differs. This capture post-dates
the scaffold folding in reviewer-principal registration and the `CLAUDE.md` governance
preamble — [BACKLOG.md](../BACKLOG.md), "Maintainer ruling: self-application", 2026-07-09, "starting a run
becomes a verb"):

```
== stamping instance at /home/bork/w/vdc/1/.runverbprobe (name=runverbprobe) ==
-- new-world 'runverbprobe': applying high_watermark_1.sql + s20 + s21 to toy (schema=runverbprobe kern=runverbprobe_kernel role=runverbprobe_rw) --
CREATE SCHEMA
CREATE TABLE
...
   kernel applied (schema runverbprobe + kernel schema runverbprobe_kernel + role runverbprobe_rw, s20 + s21 included)
-- new-world 'runverbprobe': seeding the stamp secret (idempotent, mirrors drive/arm.sh ruling 43) --
   one fresh secret provisioned (.../.claude/secrets/stamp_secret.hex [chmod 600]; DB runverbprobe_kernel.stamp_secret)
-- new-world 'runverbprobe': registering standard principals (reviewer) --
SET
SET
INSERT 0 1
   'reviewer' principal registered (class subagent; 'author' was already seeded by s15-schema.sql)
-- deployment.json --
wrote /home/bork/w/vdc/1/.runverbprobe/deployment.json
-- .claude/ wiring --
wrote .claude/settings.json, governed_files.json, GOVERNED_FILES.md, apparatus.json, APPARATUS.md, HOOKS.md
wrote CLAUDE.md (governance preamble, auto-loaded at session start)
-- the three verbs (led, judge, pickup) --
wrote led (executable)
wrote judge (executable)
wrote pickup (executable)
== done ==
```

A quick live check that the pair-keyed distinctness objects genuinely landed (also witnessed,
real output): `psql -h <host> -d toy -c '\df runverbprobe.validate_independence'` shows the
function present, and `SELECT column_name FROM information_schema.columns WHERE
table_schema='runverbprobe' AND table_name='review_stamp_distinctness'` lists
`review_stamp_session`/`regards_stamp_session` alongside the original `stamp_agent` columns —
the s21 pair-keyed distinctness columns, present from birth. A second live check that the
principals genuinely landed (also witnessed, real output): `SELECT id, name, agent_class FROM
runverbprobe_kernel.principal ORDER BY id` returns exactly `(1, author, model)` and
`(2, reviewer, subagent)` — the world is born with both the principals a run needs, not just
the connection principal.

**Success looks like:** the block above ending in `== done ==` with no `psql` error lines
(a `NOTICE: ... does not exist, skipping` is normal — see section 1), `deployment.json` and a
rendered `CLAUDE.md` present at the dest root, and `./led`/`./judge`/`./pickup` all executable
there. A quick sanity check:

```sh
cd <dest-dir> && ./led decision "world opened" && ./led --recent 1 && ./judge && ./pickup
```

`./judge` should print `AGREE` (the engine and the SQL floor agree on an empty-but-consistent
ledger); `./pickup` prints a live resume brief in five sections (in-force decisions, open
questions, review debt, recent changes, git state) — this IS the "orienting in any world" verb;
run it any time, in any world, to get your bearings without trusting a stale stored handoff.
Both were witnessed clean against `runverbprobe`: `judge` printed `AGREE`; `pickup` printed all
five sections, including `REVIEW-DEBT` and `OPEN-QUESTIONS` both empty (the "done" state the
governance preamble below names).

**Starting the run — no more hand-register, no more hand-paste.** Until this session, opening a
world left two things for the operator to do by hand before the first real session: register a
`reviewer` principal (`./led register-principal reviewer subagent`), and paste a six-point
governance prompt into the Claude session. Both are now done AT SCAFFOLD TIME — the transcript
above already shows the `reviewer` registration; the `.claude/` wiring step now also writes a
`CLAUDE.md` at the world's root carrying that six-point prompt verbatim (rendered with this
world's own paths — see `bootstrap/templates/CLAUDE.md.tmpl`). Claude Code auto-loads a
project's `CLAUDE.md` at session start, so the ceremony for actually starting a governed run is
now exactly the three lines the scaffold itself prints at the end (real witnessed capture,
`runverbprobe`):

```
  bootstrap/new-project.sh /home/bork/w/vdc/1/.runverbprobe --new-world runverbprobe --db toy --host 192.168.122.1 --name runverbprobe
  cd /home/bork/w/vdc/1/.runverbprobe
  claude   # then type your task as your first message -- CLAUDE.md auto-loads the
           # governance preamble (author + reviewer principals, both already
           # registered above); nothing to paste.
```

Starting a run now takes one scaffold command, one `cd`, and one `claude` invocation where
you type the task — there is no file to paste and no prompt to retype from memory
(ratifier's acceptance bar, 2026-07-09). This is gated to `--new-world`
mode only: classic `--schema/--kern/--role` mode applies no kernel lineage at all (see item 1
above), so it has no principal table to register into yet and writes no `CLAUDE.md` — a file
claiming "a reviewer principal exists" would be false there until the operator applies a kernel
lineage by hand.

**Beyond the chain — a lineage delta is never applied to an already-open world.** `--new-world`
applies the birth chain current as of the scaffold's own header comment. The birth chain is the
ordered sequence of individually-named database migrations ("lineage steps," each one an
`sNN`-numbered SQL file under `kernel/lineage/`) a new world receives at the moment it is
created; today that sequence is `high_watermark_1.sql` (itself bundling the four earliest steps,
s15 → s17-stamp → s17-independence → s19), then s20 → s21 → s22 → s23 → s24 → s25 — see
[GLOSSARY.md's birth-chain entry](../GLOSSARY.md#birth-chain) for the live, current list (a later
delta can extend it further than this page says) and
[kernel/lineage/README.md](../kernel/lineage/README.md) for what each step added. A lineage delta
ratified
after your world was scaffolded is never bundled in silently, and — per the runs-are-strictly-
linear ruling ([CLAUDE.md ORCHESTRATION](../CLAUDE.md#orchestration--the-standing-delegation-contract-2026-07-09),
2026-07-11) — it is also never *applied* to your already-open world: "run M > N means run N's
world is dust and settled: read-only evidence, never patched, never refreshed, never delta'd."
An earlier version of this walkthrough pointed at `bootstrap/apply-delta.sh` for that; that
script, and the apply-to-existing-world ceremony it guarded, are retired
([ORCH-OPERATING-CARD.md](ORCH-OPERATING-CARD.md#kernel-deltas--the-decision-tree-claudemd-orchestration-is-the-ssot):
"There is NO apply-to-existing-world step, for anyone"). If a lineage delta lands after you
opened a world and you need what it adds, the honest path is a fresh world: scaffold a new one
with `--new-world` once the delta has entered the birth chain, and treat the old world as
settled evidence, not a thing to patch.

> **A hazard this section's own witnessing turned up, so it does not bite the next operator:**
> the scaffold bakes `<dest-dir>`'s path into `.claude/settings.json` (the change-gate and
> stamp-interceptor hook commands) and `.claude/HOOKS.md` at the moment it runs. If you relocate
> the directory afterward (as `run3` was — scaffolded at a throwaway path, then moved to its
> final home), those baked paths go stale silently: the change gate's `SUBJECT_ROOT` no longer
> matches any file under the real project, so it stops governing anything at all — no error,
> just silent non-enforcement — and the stamp interceptor looks for the secret at a path that no
> longer exists, so writes pass through unstamped. **Scaffold at the final destination path**, or
> re-run `bootstrap/new-project.sh <final-dest> --new-world <world-name> --force` from the final
> location afterward (the kernel/secret steps are idempotent — see the script's own header
> comment — so this is safe to repeat). Every world's `.claude/HOOKS.md` now opens with a
> PROVENANCE header (created-at, exact command, lineage applied) precisely so this kind of drift
> is visible on inspection instead of discovered the hard way.

## What is NOT in this walkthrough, and why

- **The refuse-and-teach change gate** (an edit to a source file is refused unless a ledger entry
  declares it): the hook exists (`hooks/pretooluse_change_gate.py`) but is currently wired to the
  experiment's schema — pointing it at yours is a small adaptation job, not a command. Ask for it.
- **The close instruments and the formal conformance layer**: the regulatory-grade end of the
  project. Nothing above depends on them.
- **s18-criterion-principals**: reviewer machinery the project uses on itself; not part of a user
  kernel (deliberately excluded from `high_watermark_1.sql`).
