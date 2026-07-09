# WALKTHROUGH — a decision ledger for your own project

Ten minutes: stand up an append-only decision ledger for a project of yours, file a decision,
read it back, tear it down. Worked example: `../toy-project` (terminal-color optimization).
Everything else in this repo — the experiment apparatus in `drive/`, `seen-red/`, the e-series —
is the project studying *itself*; you need none of it for this.

What you get, concretely: decisions recorded as rows that cannot be edited or deleted (append-only,
trigger-enforced), attributed to the connecting role (not self-declared), superseded by appending —
never by rewriting.

## 0. Prerequisites

- `psql` on your PATH; the DB host reachable (`sh bootstrap/bootstrap.sh` checks this — its only
  DB access is a read-only `SELECT 1`).
- A throwaway database. The host's `pg_hba.conf` only admits registered databases, so run this **on
  the DB host itself**, not from your workstation:

  ```sh
  createdb toy
  ```

## 1. Apply the kernel

One file. It chains the frozen DDL lineage (s15 → s17-stamp → s17-independence → s19) with
`ON_ERROR_STOP` on, and creates nothing outside the schemas and role you name:

```sh
cd autoharn
psql -h 192.168.122.1 -d toy \
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
psql -h 192.168.122.1 -d toy -c "
  SET ROLE toycolors_rw; SET search_path = toycolors, toycolors_kernel;
  INSERT INTO toycolors.ledger (kind, statement) VALUES ('decision','perceptual distance = CIEDE2000, not RGB Euclidean');
  INSERT INTO toycolors.ledger (kind, statement) VALUES ('assumption','output constrained to the 16 ANSI slots');"
```

```sh
psql -h 192.168.122.1 -d toy -tAc "
  SELECT l.id, l.kind, l.statement, p.name
  FROM toycolors.ledger l JOIN toycolors_kernel.principal p ON p.id = l.actor;"
```

The `actor` came from your connection, not from anything you typed. To change your mind later,
INSERT a new row with `supersedes = <old id>`; UPDATE and DELETE are refused by trigger.

The habit this buys: decision lands in the ledger, *then* the code gets written.

## 3. Tear down

```sh
dropdb toy        # on the DB host — removes schemas, tables, the pgcrypto extension
psql -h 192.168.122.1 -d postgres -c "DROP ROLE IF EXISTS toycolors_rw;"   # roles are cluster-global
```

## 4. Opening a new world (one world per run)

Sections 1-3 above stand up ONE schema by hand. If you are about to run an actual subject/agent
against the ledger — not just try the mechanism — use this instead, every time you start a new run.

**Why:** a run's subject must not see a sibling run's ledger history. `ledger_current`/T_now
computed over a mixed ledger reads as "in force" ACROSS runs that never happened together —
cribbing, bias, cross-run leakage into whatever the subject does next. Branches share only the
branch point (the kernel apply — schema, triggers, secret, roles); they never share each other's
rows. (Maintainer ruling, "one world per run," 2026-07-09 — see `BACKLOG.md`.) The old habit of
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
  s17-independence → s19 → s20 — s20 included by construction, never the pre-s20 grants-gap shape)
  and seeds a fresh stamp secret, both in one call.
- `--name <name>` — this project's own identifier for `judge`'s target-name argument. Defaults to
  `<dest-dir>`'s basename; give it explicitly if that basename would collide with autoharn's
  curated target names (`toy`, `nla`, `e15`-`e18`) or its scratch-naming conventions
  (`^s\d+[a-z]*$`, `*_scratch`).

**What you should see** (abbreviated real capture, witnessed against a throwaway world
`docprobe`/`docprobe_kernel`/`docprobe_rw` on the same `toy` db, then torn down — the mechanism
witnessed here is identical to what a real run gets; only the schema name differs):

```
== stamping instance at /home/bork/.../.docprobe (name=docprobe) ==
-- new-world 'docprobe': applying high_watermark_1.sql + s20 to toy (schema=docprobe kern=docprobe_kernel role=docprobe_rw) --
CREATE SCHEMA
CREATE TABLE
...
   kernel applied (schema docprobe + kernel schema docprobe_kernel + role docprobe_rw, s20 included)
-- new-world 'docprobe': seeding the stamp secret (idempotent, mirrors drive/arm.sh ruling 43) --
   one fresh secret provisioned (.../.claude/secrets/stamp_secret.hex [chmod 600]; DB docprobe_kernel.stamp_secret)
-- deployment.json --
wrote /home/bork/.../.docprobe/deployment.json
-- .claude/ wiring --
wrote .claude/settings.json, governed_files.json, GOVERNED_FILES.md, apparatus.json, APPARATUS.md, HOOKS.md
-- the three verbs (led, judge, pickup) --
wrote led (executable)
wrote judge (executable)
wrote pickup (executable)
== done ==
```

**Success looks like:** the block above ending in `== done ==` with no `psql` error lines
(a `NOTICE: ... does not exist, skipping` is normal — see section 1), `deployment.json` present at
the dest root, and `./led`/`./judge`/`./pickup` all executable there. A quick sanity check:

```sh
cd <dest-dir> && ./led decision "world opened" && ./led --recent 1 && ./judge && ./pickup
```

`./judge` should print `AGREE` (the engine and the SQL floor agree on an empty-but-consistent
ledger); `./pickup` prints a live resume brief in five sections (in-force decisions, open
questions, review debt, recent changes, git state) — this IS the "orienting in any world" verb;
run it any time, in any world, to get your bearings without trusting a stale stored handoff.

**Beyond the chain — s21 and future deltas are an operator act, not automatic.** `--new-world`
applies the lineage current AS OF the scaffold's own header comment (s15 through s20 today); a
lineage delta ratified AFTER that — e.g. `s21-session-aware-distinctness.sql`, ratified but not
yet applied anywhere — is never bundled in silently. Applying one to an already-open world is a
separate, explicit act, with every `-v` var spelled out by hand:

```sh
psql -h <host> -d <db> -v schema=<world> -v kern=<world>_kernel -f kernel/lineage/sNN-....sql
```

(never bare — a lineage apply against the wrong schema by omission is exactly the class this
spells-it-out convention forecloses). Check `BACKLOG.md` for a delta's ratification/witness status
before applying it to a world that matters.

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
