# Deploying autoharn to your project (git submodule)

This page is only about deployment: getting autoharn wired into a project of your own as a
pinned git submodule, and keeping it that way. It assumes you have `psql` and `git` on your
`PATH` and a Postgres database you can reach, and it tells you exactly what to type and what
you should see.

If you want to know what autoharn *is*, or how to collaborate/build inside the autoharn repo
itself, that content now lives in [`docs/PROJECT-OVERVIEW.md`](docs/PROJECT-OVERVIEW.md) — not
here.

### Before you start

Everything below assumes three things are already true. None of the four commands does any of
this for you:

1. **You have cloned autoharn itself somewhere** (`git clone <autoharn's repo URL>`) — that
   clone is "this autoharn checkout" every command below is run from.
2. **A Postgres database, and a role that can log into it, already exist.** None of the four
   commands below runs `CREATE DATABASE` or `CREATE ROLE`, and step 1 does not apply the ledger's
   own SQL either — that's a separate manual step, spelled out in step 1's "Two manual steps
   remain" note below. If you don't have a database/role yet, see USER-CONFIGURATION.md's
   ["FAQ: provisioning Postgres for
   autoharn"](USER-CONFIGURATION.md#faq-provisioning-postgres-for-autoharn) for a copy-paste
   walkthrough. `psql` authentication (passwords, `.pgpass`, `PGPASSWORD`, `pg_hba.conf` rules)
   is your normal Postgres client setup, not something any command below configures — the same
   FAQ page covers it.
3. **You'll want [Claude Code](https://claude.com/product/claude-code) installed** before you
   actually start working inside the deployed project — the scaffold wires up `.claude/`
   settings for it, but installing Claude Code itself is outside this page's scope.

### Two words this page uses constantly

- **The ledger** is the append-only record autoharn gives your project — a Postgres table plus
  supporting views/triggers that every command below reads from or writes to. `schema` and
  `kern` in [Configuration](#configuration) are the two Postgres schemas that hold it.
- **Operator verbs** are the small command-line tools (`led`, `judge`, `pickup`, `audit`,
  `distance-to-clean`, `verify-commission`, `verify-chain`, `attest-doc`) that a deployment gets
  scaffolded with, to read and write that ledger day to day. This page does not explain what
  each one does individually — once a deployment exists, run any of them with no arguments for
  its own usage text, or see [`docs/PROJECT-OVERVIEW.md`](docs/PROJECT-OVERVIEW.md) and
  [`USER-GUIDE.md`](USER-GUIDE.md) for the fuller tour.

There are four things you can do. Pick the one that matches your situation:

1. [Deploy autoharn to a brand-new project](#1-deploy-autoharn-to-a-brand-new-project) —
   `bootstrap/new-project.sh ... --pin submodule`
2. [Convert an existing (unpinned) deployment to a submodule](#2-convert-an-existing-deployment-to-a-submodule) —
   `bootstrap/convert-to-submodule.sh`
3. [Upgrade a pinned deployment to a newer autoharn](#3-upgrade-a-pinned-deployment-to-a-newer-autoharn) —
   `bootstrap/upgrade-submodule.sh`
4. [Bring a deployment's database up to date with a newer kernel](#4-bring-a-deployments-database-up-to-date-with-a-newer-kernel) —
   `./migrate`

Each step below links back to [Configuration](#configuration) for the settings it needs — read
that section alongside, or first if you'd rather see every setting up front before typing
anything.

All four commands are run from inside **this** autoharn checkout (the one you cloned to build
from), and they act on a separate directory — your project — that either does not exist yet or
already exists as a deployment. None of them touch this checkout itself.

---

## 1. Deploy autoharn to a brand-new project

Use this the first time you wire autoharn into a project that has never had it before.

**What you type**, from inside this autoharn checkout:

```
bootstrap/new-project.sh <dest-dir> --db <db> --host <host> --schema <schema> \
    --kern <kern> --role <role> --pin submodule [--pin-url <remote>]
```

Replace `<dest-dir>` with the path to your project (created if it doesn't exist yet), and see
[Configuration](#configuration) below for `--db`/`--host`/`--schema`/`--kern`/`--role`. `--pin
submodule` is what makes this a pinned deployment instead of the older "live checkout" shape —
always pass it. `--pin-url` is optional; see its own entry in Configuration.

**What you should see.** This is the script's own `--help` text (run with no arguments, so
nothing was touched):

```
usage: bootstrap/new-project.sh <dest-dir> --db <db> --host <host> --schema <schema> --kern <kern> --role <role> [--name <name>] [--governed <patterns>] [--force]
       bootstrap/new-project.sh <dest-dir> --new-world <world> --db <db> --host <host> [--name <name>] [--governed <patterns>] [--force]
         (--new-world derives --schema/--kern/--role from <world> unless given explicitly;
          also applies high_watermark_1.sql + s20 through s28 and seeds the stamp secret -- see
          the --new-world block in this script's own header comment)
         (--governed <comma-separated-fnmatch-patterns> sets .claude/governed_files.json;
          omit it and the *.py-only default is used, with a loud post-scaffold notice)
         (--pin submodule adds autoharn as a git submodule at <dest-dir>/.autoharn, pinned
          to THIS checkout's current commit, and points every operator verb + hook at that
          pinned copy instead of this live checkout -- design/ORCH-DEPLOYMENT-PINNING.md,
          NOT combinable with --new-world. --pin-url <url> overrides the submodule remote
          (default: this checkout's own on-disk path -- portable only on this machine;
          pass a real git remote URL for a submodule another machine can also fetch))
```

The command's own help text above covers more than this guide does: **ignore the second usage
line** (the one starting `--new-world`) **and the `--governed` parenthetical** — both describe
autoharn's own internal disposable test instances (this project's own "run" scaffolds, unrelated
to deploying autoharn anywhere), not a deployment to your project. Only the first
usage line, plus the `--pin`/`--pin-url` parenthetical, apply here.

With real arguments, the command does the following, in order (read plainly, not witnessed with
live output in this document — running it needs a real Postgres target):

- If `<dest-dir>` is not already a git repository, runs `git init` there for you — you do not
  need to create it as a repo yourself first.
- Adds autoharn as a git submodule at `<dest-dir>/.autoharn`, pinned to this checkout's exact
  current commit (it refuses if this checkout has uncommitted changes — a pin has to name a
  commit that can actually be reproduced).
- Writes `<dest-dir>/deployment.json` (see [Configuration](#configuration)).
- Writes `<dest-dir>/.claude/` wiring (hook settings; `governed_files.json`, the pattern list the
  pre-commit change gate — the hook that refuses an edit to a file no open ticket has declared —
  checks edits against; and supporting docs).
- Writes eight thin shim scripts at the top of `<dest-dir>` — `led`, `judge`, `pickup`, `audit`,
  `distance-to-clean`, `verify-commission`, `verify-chain`, `attest-doc` — each one `exec`s the
  matching template out of `<dest-dir>/.autoharn/bootstrap/templates/`, i.e. out of the pinned
  submodule, never out of this live checkout.
- Commits the submodule and the shims/hook-wiring it points at, in `<dest-dir>`'s own git
  history.
- Prints a closing block telling you to `cd <dest-dir>` and then run `claude` to start a session
  there (its exact wording is not quoted here — quoting it would need a real run against a real
  Postgres target, which this document cannot fabricate).

It refuses (and touches nothing) if `<dest-dir>/deployment.json` already exists (pass `--force`
to overwrite) or if this autoharn checkout is dirty.

**Two manual steps remain after the command finishes, and this command does not do them for
you** (the command's own closing output names both, but read them here too so you don't miss
them):

1. **Apply a kernel lineage** — the actual SQL that creates the ledger tables — to
   `<db>/<schema>/<kern>/<role>`. This is not part of `new-project.sh`; read
   [`kernel/lineage/README.md`](kernel/lineage/README.md) in this checkout for the current
   apply order and the `psql` invocation.
2. **Provision the stamp secret.** `<dest-dir>/.claude/HOOKS.md`, written by the scaffold, has
   the exact copy-paste commands for this (search it for "stamp secret") — do this once, and do
   not repeat it later: re-running it rotates the secret and invalidates every ledger entry
   already stamped under the old one.

Only once both are done do the operator verbs (`led`, `judge`, `pickup`, …) actually work.

**After this**, a `git pull` / merge on this autoharn checkout will never change your project's
behavior — the deployment only moves when you deliberately run
[`bootstrap/upgrade-submodule.sh`](#3-upgrade-a-pinned-deployment-to-a-newer-autoharn).

---

## 2. Convert an existing deployment to a submodule

Use this if you already have a project deployed against a live, un-pinned autoharn checkout
(the older shape, where your project's `led`/`judge`/`pickup` scripts `exec` straight out of a
mutable autoharn checkout on disk) and you want to freeze it to a pinned commit instead.

**What you type**, from inside this autoharn checkout:

```
bootstrap/convert-to-submodule.sh <deployment-dir> [--pin-url <url>] [--yes]
```

`<deployment-dir>` is your existing deployment (must already have a `deployment.json` and the
eight operator-verb shims, still live-exec today). `--pin-url` is the same setting as in step 1
— see [Configuration](#configuration). `--yes` skips the typed `CONVERT` confirmation prompt (for
scripted use only — leave it off the first time so you see exactly what will change).

**What you should see** with no arguments (its own `--help`-equivalent, run with nothing touched):

```
usage: bootstrap/convert-to-submodule.sh <deployment-dir> [--pin-url <url>] [--yes]
```

With a real `<deployment-dir>`, the script, in order:

1. Checks `<deployment-dir>/deployment.json` exists and parses. Refuses and stops if not.
2. Checks the deployment isn't already pinned (no `.autoharn` present already). If it is, it
   tells you to use `bootstrap/upgrade-submodule.sh` instead.
3. Reads all eight operator-verb shims and confirms they all agree on which autoharn checkout
   they currently `exec` out of. Refuses if any shim is missing, malformed, or they disagree with
   each other.
4. Confirms that discovered autoharn checkout is a clean git repository (no uncommitted changes)
   and reads its current commit — that is the commit your deployment gets pinned to (**not**
   autoharn's current tip; converting is not the same act as upgrading).
5. Runs a best-effort scan for a live Claude Code session running against `<deployment-dir>` and
   refuses if it finds one — never convert a deployment out from under a session that's using it.
   Run this command from a separate terminal, not from inside a session sitting in
   `<deployment-dir>`.
6. Prints exactly what it is about to do and asks you to type `CONVERT` to proceed (unless
   `--yes`).
7. Adds the `.autoharn` submodule pinned to that commit, repoints all eight shims and the hook
   wiring in `<deployment-dir>/.claude/settings.json` at the pinned copy, and commits the change
   in `<deployment-dir>`'s own git history.
8. Verifies every verb resolves into the new pin, then runs `./led --recent 1` inside
   `<deployment-dir>` as a smoke test.
9. Prints the exact `./led decision "..."` lines to record the conversion, both in this autoharn
   checkout's own ledger and (if `<deployment-dir>` has one) in the deployment's own ledger.

If verification fails after the commit, the script says so explicitly — the commit has already
happened at that point, and the message tells you to fix the named verb by hand or `git revert`
the commit inside `<deployment-dir>`.

---

## 3. Upgrade a pinned deployment to a newer autoharn

Use this once a deployment is already pinned (via step 1 or step 2) and you deliberately want it
to start running a newer autoharn commit. This never happens automatically — a plain `git merge`
on this checkout does not change any already-pinned deployment's behavior; only this command
does.

**What you type**, from inside this autoharn checkout:

```
bootstrap/upgrade-submodule.sh <deployment-dir> <new-sha> [--yes]
```

`<new-sha>` must be an exact commit — never a branch name, never "latest". To find one, look at
this autoharn checkout's own history (`git log --oneline` from inside it, after a `git pull` to
get the commits you want to offer) and pick the commit you deliberately want your deployment to
run — the script fetches it from the pinned submodule's remote, so it must be a commit that
remote can actually reach. `--yes` skips the typed `UPGRADE` confirmation prompt.

**What you should see** with no arguments:

```
usage: bootstrap/upgrade-submodule.sh <deployment-dir> <new-sha> [--yes]
```

With real arguments, the script:

1. Checks `<deployment-dir>/.autoharn` exists and is a git checkout. Refuses (and tells you to
   run `convert-to-submodule.sh` first) if the deployment isn't pinned yet.
2. Runs the same live-session scan as step 2 and refuses if a session is running against
   `<deployment-dir>` — bumping the pin mid-session would change that session's behavior out from
   under it.
3. Fetches the submodule's remote and resolves `<new-sha>` to a real commit. Refuses if it can't
   be resolved (typo, or a commit the remote can't reach).
4. Prints the old and new pin and asks you to type `UPGRADE` (unless `--yes`).
5. Checks out `<new-sha>` inside `<deployment-dir>/.autoharn` and commits the pin bump in
   `<deployment-dir>`'s own git history.
6. Verifies every operator verb still resolves to an executable file at the new pin, then runs
   `./led --recent 1` as a smoke test.
7. Prints the exact `./led decision "..."` lines to record the upgrade, in both ledgers as in
   step 2.

Every operator verb and hook in the deployment picks up the new bytes on its very next
invocation after the commit — nothing else changes.

---

## 4. Bring a deployment's database up to date with a newer kernel

An upgraded autoharn checkout (step 3) can carry newer kernel SQL (`kernel/lineage/`) than a
deployment's database has actually applied. `./migrate` is the one command that closes that gap,
for any deployment, regardless of which kernel generation it's currently on.

**Its interface is deliberately, permanently stable** — the script itself says so: it takes no
new flags as the kernel grows, because the list of SQL deltas it needs is read live out of
`bootstrap/new-project.sh`'s own manifest rather than hard-coded here.

Unlike the eight operator verbs (`led`, `judge`, `pickup`, …), `./migrate` is **not** scaffolded
into your deployment directory — there is only one copy, at the root of this autoharn checkout,
and it takes the deployment directory as an argument.

**What you type**, from inside this autoharn checkout:

```
./migrate <deployment-dir>            # rehearse, ask ONE typed confirmation, then apply
./migrate <deployment-dir> --dry-run  # rehearse and print evidence; never applies anything
```

**What you should see** if you get the arguments wrong (its own usage line, witnessed by calling
it with an unrecognized deployment path — nothing is touched):

```
usage: migrate <deployment-dir> [--dry-run]
```

With a real, already-scaffolded `<deployment-dir>`, in order:

1. Loads `<deployment-dir>/deployment.json` and prints the resolved db/host/schema/kern/role.
   Refuses loudly if the deployment record is missing or malformed.
2. Checks for a live session running against `<deployment-dir>` and refuses if it finds one.
3. Reads the delta manifest (parsed live from `bootstrap/new-project.sh`) and figures out which
   deltas this deployment's database is missing.
4. If nothing is missing, it says so and stops — nothing to do.
5. Otherwise, it takes a `pg_dump` backup first and prints its path — this is your rollback
   artifact if anything goes wrong.
6. It restores that backup into a scratch schema and rehearses every missing delta there first,
   checking that ledger history comes out byte-identical and that each delta's own
   detect/verify checks pass — all before touching your live database.
7. It prints a full evidence summary (backup path, missing deltas, rehearsal results).
8. With `--dry-run`, it stops here — nothing live is touched.
9. Without `--dry-run`, it asks for one typed confirmation, then applies the same deltas to your
   live database, re-verifies history byte-identity afterward, and records the migration as a
   decision row in the deployment's own ledger.

If the rehearsal (step 6) fails, nothing has been applied to your live database yet — the
backup and the printed evidence are what you'd use to investigate.

---

## Configuration

Every field below either lives in a deployment's `deployment.json` (written by
`bootstrap/new-project.sh`, read by every operator verb and by `./migrate`) or is a flag one of
the four pinning/migration scripts above reads directly.

### `deployment.json` fields

| Field | Meaning | What a sane value looks like | What breaks if it's wrong |
|---|---|---|---|
| `db` | The Postgres **database name** the ledger lives in. | A database that already exists on `host`, reachable by the role you'll connect as. | Every verb (`led`, `judge`, `pickup`, `./migrate`, …) fails to connect; you'll see a plain Postgres "database ... does not exist" or connection error. |
| `host` | The Postgres **host** to connect to. | A hostname or IP your machine can actually reach on the Postgres port (usually 5432), e.g. `localhost` or your LAN database box. | Connection refused / timeout / DNS failure on every verb — nothing ledger-related will work until this is fixed. |
| `schema` | The **ledger schema** — the Postgres schema holding the `ledger` table and its supporting views/triggers, applied by one of the `kernel/lineage/sNN-schema.sql` generations. | A short, project-specific name, e.g. your project's own name (`toycolors`). Must not collide with autoharn's own curated target names (`toy`, `nla`, `e15`–`e18`) or its scratch-naming conventions (matching `^s\d+[a-z]*$`, or ending in `_scratch`) — a distinctive, project-specific name (your project's own name is usually safe) avoids all of these. | If it doesn't match the schema the kernel DDL was actually applied into, every ledger read/write fails or silently targets the wrong tables. |
| `kern` | The **kernel schema** — holds `principal` and the stamp/chain machinery, separate from `schema` so ledger content and kernel plumbing don't share one namespace. | Conventionally `<schema>_kernel`, e.g. `toycolors_kernel`. | Same failure mode as a wrong `schema`: verbs that need `principal` (registering agents, stamping) fail or hit the wrong schema. |
| `role` | The Postgres **role** every verb connects as (`led`, `judge`, `pickup`, hooks, `./migrate`). | A role granted exactly the privileges `kernel/lineage/sNN-schema.sql`'s own GRANT block gives it (USAGE on `schema`/`kern`, INSERT+SELECT on `ledger`, etc.) — never a superuser. | Permission-denied errors on every write; a role with *more* than the granted privileges is a security posture problem even if things "work." |
| `name` | This deployment's own label (optional; defaults to the destination directory's basename). Used live by the `judge` shim as the target name it passes to autoharn's ledger-differential engine (the tool behind `./judge` that diffs two ledgers against each other), and hence which `derivations/<name>/` subdirectory inside *this autoharn checkout* your comparisons get filed under. | Something short and specific to your project, and — same constraint as `schema` above — not one of autoharn's own curated target names or scratch-naming patterns (`^s\d+[a-z]*$`, `*_scratch`), or `./judge` resolves to the wrong target. | `./judge` compares against, or files derivations under, the wrong target — confusing, not catastrophic, but worth getting right at scaffold time since renaming later means re-scaffolding. |

### Flags the pinning/migration scripts read (not stored in `deployment.json`)

| Setting | Where | Meaning | Sane value / what breaks if wrong |
|---|---|---|---|
| `<dest-dir>` / `<deployment-dir>` | all four commands | The path to your project, existing or to be created. | Any writable directory path. Getting it wrong means the tooling either can't find your deployment (`deployment.json not found`) or scaffolds/converts the wrong directory — always double-check the path before typing a confirmation. |
| `--pin submodule` | `new-project.sh` | Opts into the pinned-submodule deployment shape instead of the older live-exec shape. This is the shape this whole guide is about — always pass it for a new deployment. | Only `submodule` is accepted; anything else is refused. Omitting it entirely gives you the older, unpinned shape (out of scope for this guide, and not idiot-proof against an unrelated `git pull` on this checkout changing your project's behavior). |
| `--pin-url <remote>` | `new-project.sh`, `convert-to-submodule.sh` | The git remote the `.autoharn` submodule points at. | Default: this checkout's own on-disk filesystem path — works with no network, but only reproducible on this one machine. Pass a real `https://`/`ssh://` git remote if anyone else (or any other machine) needs to clone this deployment and fetch the same submodule. Omitting it when portability matters means a clone on another machine can't resolve the submodule. |
| `<new-sha>` | `upgrade-submodule.sh` | The exact commit to move a pinned deployment's `.autoharn` submodule to. | Must be a real, resolvable commit — never a branch name, never "latest"/"tip"/omitted; the script refuses anything it can't resolve after fetching. Picking the wrong commit pins your deployment to the wrong autoharn version, same as any other git checkout to the wrong SHA. |
| `--yes` | `convert-to-submodule.sh`, `upgrade-submodule.sh` | Skips the typed confirmation prompt. | Fine for scripted/CI use once you trust the printed summary; leave it off for a first, manual run so you actually read what's about to change. |
| `--force` | `new-project.sh` | Overwrites an existing `deployment.json`/scaffold at `<dest-dir>` instead of refusing. | Only pass this if you mean to re-scaffold over an existing deployment — it can replace an existing `.autoharn` pin (after deinit-ing the old submodule) and existing shims. |
| `--dry-run` | `./migrate` | Rehearses a migration and prints evidence without ever touching the live database. | No downside to always trying this first — nothing is applied. |

Settings you will see in a scaffolded deployment's `.claude/` directory (`governed_files.json`,
`settings.json`, etc.) are hook/editor wiring, not part of the deployment/pinning surface this
guide covers — see the docs written into that same `.claude/` directory by the scaffold itself
(`GOVERNED_FILES.md`, `HOOKS.md`) for what those mean.
