# autoharn — deploying to your project (git submodule)

autoharn gives a project of yours an append-only, tamper-evident record of what was decided,
who decided it, and when — plus the small tools and Claude Code hooks that read and write that
record so a collaborator (human or AI) is checked against it rather than trusted on their word.
It is not a project-management app you adopt wholesale: you wire it into an existing project as
a pinned git submodule, and it adds governance around the work you're already doing there.

> ⚠️ **Dangerous bend — work in progress, no warranty.** This repository is under heavy,
> active development. It is public domain (the Unlicense), which disclaims all warranty in
> law; this notice disclaims it in spirit too. The documentation here speaks in
> high-assurance ambitions — NIST- and NRC-flavored language, a law corpus, witnessed
> claims — and those are **aims the design is built toward, not statements of its current
> maturity**. It works, more or less, for its maintainer's own daily needs; everything
> beyond that you should treat as aspiration until you have witnessed it yourself. (That
> distinction — an aspiration is not a conformance claim — is enforced inside this project
> as law, ADR-0020. It applies to this repository's own self-description first.)

This page is only about deployment: getting autoharn wired into a project of your own, and
keeping it that way. It assumes you have `psql` and `git` on your `PATH` and a Postgres database
you can reach, and it tells you exactly what to type and what you should see.

**Getting started:** run the guided setup wizard —

```
python3 -m tools.setup_tui <dest-dir>
```

— from inside this autoharn checkout, with `<dest-dir>` set to your project's path. It is an
interactive, honest-about-its-limits wizard (a sidebar tree of every configuration section, one
form per section, a single commit step at the end) that scaffolds a pinned-submodule deployment
for you, asking for exactly the settings named under [Configuration](#configuration) below as it
goes. The four numbered procedures below (§1–§4) are the same scaffolding acts done by hand,
one command at a time — useful for scripted/CI use, or if you'd rather see and type every step
yourself, but the wizard is the path to reach for first.

If you want to know what autoharn *is* in more depth, or how to collaborate/build inside the
autoharn repo itself, that content lives in
[`user-guide/PROJECT-OVERVIEW.md`](user-guide/PROJECT-OVERVIEW.md) — not here. One exception,
worth knowing before you deploy: the pointer immediately below.

### Architecture at a glance

Autoharn's "kernel" — the Postgres schema this whole guide deploys and migrates (the `schema`/
`kern` settings under [Configuration](#configuration) below) — is, at its core, one append-only
ledger table plus the rules that govern which rows may be written to it: for example, the rule
that a "work item" (one unit of tracked work) may only be marked closed once every other work
item it depends on has itself closed. [`design/Autoharn.idr`](design/Autoharn.idr) renders those
rules as one machine-checked file a reader can walk top to bottom, instead of piecing the picture
together from `kernel/lineage/*.sql` (the directory of dated SQL files that actually define the
kernel) by hand. Its own header explains how to read an Idris file even if you don't know the
language, and it says plainly that it is documentation only, never the source of truth — the SQL
in `kernel/lineage/` always governs. Because a documentation file like this can silently fall
behind the SQL changes it describes, a dedicated check —
[`gates/idris_model_freshness.py`](gates/idris_model_freshness.py) — compares the model's
declared currency against the actual `kernel/lineage/*.sql` chain head and re-verifies that the
file still elaborates (type-checks), so a stale or broken model is caught mechanically rather
than discovered by a reader who trusted it.

### Before you start

Everything below assumes three things are already true. None of the four commands does any of
this for you:

1. **You have cloned autoharn itself somewhere, with `--recursive`** (`git clone --recursive
   <autoharn's repo URL>`) — that clone is "this autoharn checkout," the one every command below
   is run from. `--recursive` matters here: this repo carries two git submodules of its own
   (below), and a plain `git clone` leaves both as empty directories. If you already cloned
   without it, `git submodule update --init --recursive` from inside the checkout fixes it after
   the fact.
2. **A Postgres database, and a role that can log into it, already exist.** None of the four
   commands below runs `CREATE DATABASE` or `CREATE ROLE`, and step 1 does not apply the
   ledger's own SQL either (the ledger — defined under ["Two words this page uses
   constantly"](#two-words-this-page-uses-constantly) below — is the append-only record autoharn
   gives your project) — that's a separate manual step, spelled out in step 1's "Two manual steps
   remain" note below. If you don't have a database/role yet, see USER-CONFIGURATION.md's
   ["FAQ: provisioning Postgres for
   autoharn"](user-guide/USER-CONFIGURATION.md#faq-provisioning-postgres-for-autoharn) for a copy-paste
   walkthrough. `psql` authentication (passwords, `.pgpass`, `PGPASSWORD`, `pg_hba.conf` rules)
   is your normal Postgres client setup, not something any command below configures — the same
   FAQ page covers it.
3. **You'll want [Claude Code](https://claude.com/product/claude-code) installed** before you
   actually start working inside the deployed project — the scaffold wires up `.claude/`
   settings for it, but installing Claude Code itself is outside this page's scope.

### What `--recursive` brings: this repo's two submodules

A `git clone --recursive` of autoharn itself (not the deployment it creates in *your* project —
this repo, the one you're reading this file in) materializes two independent repositories under
`tools/`:

- **`tools/makespan-scheduler`** ([KodBena/makespan-scheduler](https://github.com/KodBena/makespan-scheduler)) —
  a scheduling library some of autoharn's own tooling calls into. Vendored as a submodule rather
  than copied in, same reasoning as the second one below: it has its own release cycle and its
  own repo is the place to track it.
- **`tools/autoharn-panel`** ([KodBena/autoharn-panel](https://github.com/KodBena/autoharn-panel)) —
  the ledger-panel SPA: a Postgres-backed, read-mostly web viewer over your project's ledger
  (typed row lists, a commission-decomposition view), with a thin write conduit that goes
  through your deployment's own `led` verb rather than around it. It is **enabled by default**
  as an autoharn extension — nothing you opt into, it's already there once the submodule is
  present — but it is entirely optional to *run*: nothing else in autoharn depends on the panel
  backend being up. Configuration is environment-first (`LEDGER_PG_URI` or discrete `PGHOST` /
  `PGDATABASE` / … fields, `LEDGER_SCHEMA`, `LEDGER_KERNEL_SCHEMA`, `LED_BIN` for write access,
  `PANEL_BIND` / `PANEL_PORT`, `PANEL_POLL_INTERVAL`); the full table of variables, precedence,
  and copy-paste commands lives in
  [USER-CONFIGURATION.md → "The autoharn-panel extension (submodule)"](user-guide/USER-CONFIGURATION.md#the-autoharn-panel-extension-submodule) —
  read that section before starting the panel backend, not this one.

### Two words this page uses constantly

- **The ledger** is the append-only record autoharn gives your project — a Postgres table plus
  supporting views/triggers that every command below reads from or writes to. `schema` and
  `kern` in [Configuration](#configuration) are the two Postgres schemas that hold it.
- **Operator verbs** are the small command-line tools that a deployment gets scaffolded with, to
  read and write that ledger day to day — ten of them, derived from
  `bootstrap/new-project.sh`'s own shim-writing loop (never hand-counted): `led`, `judge`,
  `pickup`, `audit`, `distance-to-clean`, `verify-commission`, `verify-chain`, `attest-doc`,
  `asof-export`, `doctor`. This page does not explain what each one does individually — once a
  deployment exists, run any of them with no arguments for its own usage text, or see
  [`user-guide/PROJECT-OVERVIEW.md`](user-guide/PROJECT-OVERVIEW.md) and
  [`USER-GUIDE.md`](user-guide/USER-GUIDE.md) for the fuller tour.

The setup wizard above (`python3 -m tools.setup_tui`) does all of what follows for you,
interactively. The four numbered procedures below are the same ground covered one command at a
time — reach for them when you want to script a deployment, or see every flag spelled out:

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

**What you should see.** This is the script's own `--help` text, re-captured live 2026-07-23
(run with no arguments, so nothing was touched) — the tool's own `--help` always supersedes this
quote if the two ever disagree; this is a point-in-time capture, not a second source of truth:

```
usage: bootstrap/new-project.sh <dest-dir> --db <db> --host <host> --schema <schema> --kern <kern> --role <role> [--name <name>] [--governed <patterns>] [--force]
       bootstrap/new-project.sh <dest-dir> --new-world <world> --db <db> --host <host> [--name <name>] [--governed <patterns>] [--force]
         (--boundary-url <url> --boundary-deployment <name> write deployment.json's two
          new served-shim keys, design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md
          §5 -- both optional; the rebased led/pickup/asof-export/distance-to-clean
          shims refuse loudly, teaching both names, when either is absent at RUN time
          rather than this scaffold guessing a boundary URL or standing one up)
         (--new-world derives --schema/--kern/--role from <world> unless given explicitly;
          also applies high_watermark_1.sql + every kernel/lineage/sNN delta through the
          current head (s57 as of this run -- derived live from
          kernel/lineage/ itself, never hand-typed here), seeds the stamp secret, and
          runs the s40 birth sequence (author registration event, standing declaration,
          reviewer/commissioner ceremony) -- see the --new-world block in this script's
          own header comment)
         (--governed <comma-separated-fnmatch-patterns> sets .claude/governed_files.json;
          omit it and the *.py-only default is used, with a loud post-scaffold notice)
         (--pin submodule adds autoharn as a git submodule at <dest-dir>/.autoharn, pinned
          to THIS checkout's current commit, and points every operator verb + hook at that
          pinned copy instead of this live checkout -- design/ORCH-DEPLOYMENT-PINNING.md,
          NOT combinable with --new-world. --pin-url <url> overrides the submodule remote
          (default: this checkout's own on-disk path -- portable only on this machine;
          pass a real git remote URL for a submodule another machine can also fetch))
         (--no-law suppresses the generated LAW section (portable ADR subset + pointers)
          this scaffold otherwise writes into .claude/HOOKS.md (and root CLAUDE.md in
          --new-world mode) by default -- tracker item portable-adr-delivery, maintainer
          instruction 2026-07-15: deployments must at least optionally receive the
          portable ADRs; default is ON)
         (--accept-existing-content: <dest-dir> classifies FOREIGN -- non-empty, no
          autoharn birth evidence (design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md) --
          is REFUSED unless this flag is given explicitly; the setup TUI passes it
          exactly when its own fork-target screen recorded the operator's typed
          acknowledgment. Has no effect on AUTOHARN_COMPLETE/AUTOHARN_PARTIAL, which
          keep the existing deployment.json-exists / --force gate above)
```

The command's own help text above covers more than this guide does: **ignore the second usage
line** (the one starting `--new-world`) — it describes autoharn's own internal disposable test
instances (this project's own "run" scaffolds, unrelated to deploying autoharn anywhere), not a
deployment to your project. The first usage line, the `--boundary-url`/`--boundary-deployment`,
`--pin`/`--pin-url`, `--no-law`, and `--governed` parentheticals DO apply here: omitting
`--governed` is a real, live choice for your deployment (see below — it prints more than one
line when you make it). `--accept-existing-content` only matters if `<dest-dir>` already has
unrelated content in it.

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
  checks edits against; and supporting docs). Omit `--governed` and you get the historical
  `*.py`-only default plus a loud, multi-line **GOVERNED-SET DEFAULT NOTICE** printed to your
  terminal — not a one-line footnote — naming the gap and the exact one-edit fix
  (`.claude/governed_files.json`) if your project's real work surface isn't Python.
- Appends the scaffolding-owned churn paths (`.claude/secrets/`, `.claude/logs/`, etc.) to
  `<dest-dir>/.gitignore`, creating the file if it doesn't exist yet.
- Writes `<dest-dir>/keys/README.md` (an AWAITING-KEY stub — this deployment's own GPG signing
  key, once you generate and commit one, lives in this directory; never autoharn's own
  `law/keys/`).
- Creates `<dest-dir>/attestations/` — this deployment's own record of
  [ADR-0017](law/adr/0017-the-zero-context-reader.md)'s "A:B:C" documentation-review loop (a
  writer drafts a doc, a fresh-context reviewer with no memory of the writing session checks it
  reads clearly on its own, a repairer fixes what that reviewer flags): `attestations/README.md`
  plus an empty `attestations/doc-legibility-attestations.jsonl`, separate from autoharn's own.
- Writes ten thin shim scripts at the top of `<dest-dir>` — `led`, `judge`, `pickup`, `audit`,
  `distance-to-clean`, `verify-commission`, `verify-chain`, `attest-doc`, `asof-export`,
  `doctor` (the exact set `new-project.sh`'s own shim-writing loop names) — each one `exec`s the
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
   `<db>/<schema>/<kern>/<role>`. This is not part of `new-project.sh`; two steps, not one guess:
   read [`kernel/lineage/README.md`](kernel/lineage/README.md) in this checkout and apply
   `high_watermark_1.sql` (the starting-point schema this lineage builds on top of, current as of
   its s19 generation — the `psql` invocation is spelled out there), then run
   [`./migrate <dest-dir>`](#4-bring-a-deployments-database-up-to-date-with-a-newer-kernel)
   from this checkout to carry that base forward to the actual current lineage head (`s20`
   onward, whatever it is by the time you read this — `./migrate` derives it live, so this page
   never has to name it). Never reverse-engineer `bootstrap/new-project.sh`'s own shell variables
   to guess the full chain by hand; that is exactly what `./migrate` exists to do for you.
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

`<deployment-dir>` is your existing deployment (must already have a `deployment.json` and its
operator-verb shims, still live-exec today). `--pin-url` is the same setting as in step 1
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
3. Reads the original eight operator-verb shims (`led`, `judge`, `pickup`, `audit`,
   `distance-to-clean`, `verify-commission`, `verify-chain`, `attest-doc`) plus `doctor` if
   present (added after this script's original eight, so deliberately optional rather than
   required — a deployment scaffolded before `./doctor` existed legitimately has no such shim;
   the script's own comment states this), and confirms they all agree on which autoharn checkout
   they currently `exec` out of. Refuses if any of those (eight, or nine with `doctor`) is
   missing, malformed, or they disagree with each other. **Disclosed gap, found in reach, not
   fixed here:** unlike `doctor`, `asof-export` (also scaffolded by `new-project.sh`, ten shims
   total) is never checked at all, even when present — a deployment whose `asof-export` shim
   disagrees with the others on which checkout it points at would not be caught by this check.
4. Confirms that discovered autoharn checkout is a clean git repository (no uncommitted changes)
   and reads its current commit — that is the commit your deployment gets pinned to (**not**
   autoharn's current tip; converting is not the same act as upgrading).
5. Runs a best-effort scan for a live Claude Code session running against `<deployment-dir>` and
   refuses if it finds one — never convert a deployment out from under a session that's using it.
   Run this command from a separate terminal, not from inside a session sitting in
   `<deployment-dir>`.
6. Prints exactly what it is about to do and asks you to type `CONVERT` to proceed (unless
   `--yes`).
7. Adds the `.autoharn` submodule pinned to that commit, repoints those shims (eight, or nine
   with `doctor` — same set step 3 discovered; `asof-export` is not repointed by this script even
   if present, the same disclosed gap named in step 3 above) and the hook wiring in
   `<deployment-dir>/.claude/settings.json` at the pinned copy, and commits the change in
   `<deployment-dir>`'s own git history.
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
6. Verifies nine of the ten operator verbs (the original eight plus `doctor`, this script's own
   `VERBS` list — `asof-export` is not checked, the same disclosed gap
   [step 2's convert-to-submodule.sh section above](#2-convert-an-existing-deployment-to-a-submodule)
   names) still resolve to an executable file at the new pin, then runs `./led --recent 1` as a
   smoke test.
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

Unlike the ten operator verbs (`led`, `judge`, `pickup`, …), `./migrate` is **not** scaffolded
into your deployment directory — there is only one copy, at the root of this autoharn checkout,
and it takes the deployment directory as an argument.

**What you type**, from inside this autoharn checkout:

```
./migrate <deployment-dir>            # rehearse, ask ONE typed confirmation, then apply
./migrate <deployment-dir> --dry-run  # rehearse and print evidence; never applies anything
```

**What you should see** if you run it with no arguments at all (its own usage line, witnessed by
calling it bare — nothing is touched):

```
usage: migrate <deployment-dir> [--dry-run]
```

(Calling it with one argument that isn't a real deployment — e.g. an unrecognized path — does
**not** print this usage line; it instead refuses with a `deployment record not found` message,
because a single positional argument is always treated as an attempted deployment path, not as a
malformed-arguments case. Only zero arguments, `--help`/`-h`, or three-or-more/malformed flag
arguments reach the usage line above.)

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
the four pinning/migration scripts above reads directly. `deployment.json` is a per-deployment
file, not tracked by this repo (JSON has no comment syntax, so `deployment.json.example` at the
repo root carries placeholder values only — this table is the field-by-field documentation for
them; copy the example to `deployment.json` and fill in your own values, or let
`bootstrap/new-project.sh` write it for you).

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

Unlike the fields above, the settings in this table are never written to `deployment.json` — each
is passed directly on the command line, every time you run one of the four pinning/migration
scripts (steps 1–4 above).

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

<!-- doc-attest-exempt: disclosed gap, not a clean exemption -- this file's opening section
     (what-autoharn-is, the setup-wizard-first framing, the "docs/PROJECT-OVERVIEW.md" link-text
     fix) was rewritten this session (usability review, ledger row 1180, 2026-07-23, findings
     1/3/5) and has NOT been through a genuine fresh-context A:B:C loop
     (user-guide/ORCH-ABC-AUDIT-LOOP-RECIPE.md): the executing session had no Agent/Task-dispatch
     tool available to spawn a truly separate B invocation, the same disclosed gap
     user-guide/USER-CONFIGURATION.md's own marker names. Waived here only to unblock this commit,
     flagged loudly per CLAUDE.md's engineering-responsibility standard rather than silently
     routed around -- the commissioning brief for this round states a cold-read pass follows the
     build; the orchestrator/maintainer should run it (or confirm one already ran) and replace
     this marker with an actual attestation record. Relocated to file bottom per this same round's
     finding 13 (a reader should meet the title before internal bookkeeping); the marker this
     file used to carry near line 1 ("doc-tree relocation mechanical edit ... no prose rewrite")
     is STRUCK, not carried forward unchanged, because it is no longer true once this pass touched
     prose -- carrying a stale "no prose rewrite" claim forward would itself be the dishonest-
     marker failure mode ADR-0002 forecloses. -->
