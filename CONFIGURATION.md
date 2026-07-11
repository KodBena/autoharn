# CONFIGURATION — the adopter-facing surface

This page answers one question: **if you are adopting autoharn into your own project — cloning
it, or adding it as a submodule — what do you actually get, where does each piece of state live,
what can you turn on or off, and what does each choice cost?** It is written for someone who has
never seen this repository's internal history: no prior BACKLOG entry, no ADR, no session context
assumed. If you only read one section, read ["autoharn as a library"](#autoharn-as-a-library) and
["what state lands where"](#what-state-lands-where) — the rest is reference detail for when you
need it. Operator-facing procedure for people already running this harness (the `led`/`judge`/
`pickup` verbs, the kernel-delta decision tree) lives in [OPERATING-CARD.md](OPERATING-CARD.md);
this page is upstream of that — it is about *getting to* a working project, not *operating* one
you already have.

Coined terms below link to their definitions in [GLOSSARY.md](GLOSSARY.md) on first use, per this
project's own [Stand-Alone Principle](GLOSSARY.md#project) — you should never have to grep the
repository to know what a word means here.

## autoharn as a library

autoharn is not a service you point your project at, and it is not a framework you inherit code
from. It is a **library of mechanism plus a stamping tool**: you clone or submodule this
repository somewhere on disk once, and one scaffold command writes a small, self-contained set of
files into *your own* project directory — the [world](GLOSSARY.md#world) or standing deployment
this page calls "your project" throughout. From that moment, your project's `./led`, `./judge`,
and `./pickup` are three-line shims that `exec` straight out of the autoharn checkout (the
"live verbs" design — see [the install-path contract](#the-install-path-contract--read-this-before-you-move-anything)
below for what this means and what it costs), but every piece of **your** state — your ledger's
connection facts, your per-project switches, your secrets, your work log — lives in **your**
directory, never in autoharn's.

This is a deliberate boundary, not an accident of how the scaffold happened to be written: **an
adopter's project owns all of its own state; autoharn owns none of it.** Concretely, and checked
against the actual scaffold code (`bootstrap/new-project.sh`, `bootstrap/track-work.sh`) rather
than asserted:

- Your database connection facts (`deployment.json`), your per-mechanism switchboard
  (`.claude/apparatus.json`), your governed-file patterns (`.claude/governed_files.json`), your
  [stamp](GLOSSARY.md#stamp) secret, your `keys/` directory (below), and your journals all get
  written into **your** project directory by the scaffold — nothing about a specific adopter's
  project is ever written back into the autoharn checkout.
- autoharn's own `law/`, its git history, and its own configuration are untouched by scaffolding
  a hundred different adopters from the same checkout — the checkout is read from, never written
  to, by any of the scaffold's per-project output. This extends to signing keys specifically: a
  **SIGNED-mode** commission (the optional GPG-backed ceremony documented in
  `design/GPG-TRUST-LAYER-FAQ.md`) verifies against a public key committed at **your own**
  project's `keys/` directory, never at autoharn's `law/keys/` (which is scoped exclusively to
  autoharn's own law-signing and reads nothing about any adopter's deployment) — the two
  signing domains are kept structurally apart, not merely by convention.

**What one command gives you**, witnessed against real runs (OPERATING-CARD.md, "Start a run"):

```
cd /path/to/your/autoharn-checkout
bootstrap/new-project.sh /path/to/your/project --new-world <name> --db <db> --host <host>
cd /path/to/your/project && claude
```

That single scaffold call: applies this project's **kernel lineage** — the ordered SQL migrations
that give a fresh Postgres schema pair its append-only, obligation-aware ledger shape; see
GLOSSARY.md's [birth chain](GLOSSARY.md#birth-chain) entry for the exact chain applied — to a
fresh schema pair you name, provisions a stamp secret, registers the standard principals, writes
`deployment.json` + `.claude/apparatus.json` + `.claude/governed_files.json` + a governance
preamble `CLAUDE.md`, and writes `led`/`judge`/`pickup`/`audit`/`distance-to-clean`/
`verify-commission`/`verify-chain` as thin shims. Nothing is pasted into the first chat message —
the governance preamble auto-loads. If you already have a project and only want the
[permit-to-work](GLOSSARY.md#permit-to-work)-free, non-governed cousin of this — a standing work
tracker with no hooks, no kernel-delta regime, usable by a script or an occasional session — see
[`bootstrap/track-work.sh`](#bootstraptrack-worksh--a-standing-work-tracker-not-a-governed-world) below
instead; the two scaffolds are deliberately different tools for different commitments.

## What state lands where

Every file the scaffold writes, where it lands, and whether it is meant to be committed to
**your** project's own version control (never to autoharn's):

| what | lands in | owner | commit it? |
|---|---|---|---|
| `deployment.json` | your project root | your project | yes — it names no secret, only db/host/schema/kern/role/name |
| `.claude/apparatus.json` | your project root | your project | yes — your mechanism switchboard is a project decision |
| `.claude/governed_files.json` | your project root | your project | yes — which files the change gate protects is a project decision |
| `.claude/settings.json` | your project root | your project | yes — but see [the install-path contract](#the-install-path-contract--read-this-before-you-move-anything): it bakes in an absolute path to *this* autoharn checkout |
| `.claude/secrets/stamp_secret.hex` | your project root, `chmod 600` | your project | **no** — this is the HMAC secret every [stamp](GLOSSARY.md#stamp) is keyed on; committing it defeats the stamp's whole point |
| `keys/` (your own signing-key directory) | your project root | your project | your call — the scaffold writes a `README.md` stub and leaves the directory otherwise empty (a state this project's tooling calls "AWAITING-KEY": no public key committed yet) until you opt into SIGNED-mode commissions; a committed public key here is the point, a private key never belongs here |
| `.claude/logs/*.journal.jsonl` | your project root | your project | your call — these are observation journals (mutation, delegation, read, bash-completion), not secrets, but they grow unboundedly |
| `CLAUDE.md` (the governance preamble) | your project root | your project | yes |
| `led` / `judge` / `pickup` / `audit` / `distance-to-clean` / `verify-commission` / `verify-chain` | your project root | your project | yes — they are 3-line shims, not copies of the logic (see below) |
| kernel lineage SQL, `hooks/*.py`, `bootstrap/templates/*.tmpl` | **autoharn's checkout only** | autoharn | n/a — never copied into your project; every world's shims `exec` these live |

The last row is the one adopters most often expect to be copied and is not: your project's `led`
is not a standalone program, it is `exec env PICKUP_DEPLOYMENT=<your-project>/deployment.json
<autoharn-checkout>/bootstrap/templates/led.tmpl "$@"` — three lines, committed, but pointing back
at the autoharn checkout by absolute path. This is why the next section matters before you
reorganize anything.

## The install-path contract — read this before you move anything

**Every scaffolded project's `.claude/settings.json` and verb shims bake in the absolute
filesystem path of the autoharn checkout that scaffolded them**, captured once at scaffold time
(`bootstrap/new-project.sh`: `AUTOHARN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"`). This is not an
oversight — it is the deliberate "live verbs" design (maintainer ruling 2026-07-11): a hook fix or
a template fix in the autoharn checkout takes effect in *every* already-scaffolded project on its
very next invocation, with no re-scaffold needed, because every project's tooling really does
execute the autoharn checkout's own files, live, every time.

The honest cost of that design, stated plainly rather than left for you to discover the hard way:
**this project has no relocation story today.** If you move, rename, or delete the autoharn
checkout after scaffolding one or more projects from it, every one of those projects' hooks and
verb shims silently point at a path that no longer resolves — `led`/`judge`/`pickup` fail, and
Claude Code's own hook invocations (`.claude/settings.json`'s `command` lines) fail the same way.
The current, honest contract is: **pick a path for your autoharn checkout and keep it** for as
long as any project scaffolded from it is in use.

**If you must move it anyway**, the remedy is re-scaffolding, not a live-patch: run
`bootstrap/new-project.sh <same-project-dir> ... --force` again from the checkout's *new* location
— it regenerates `.claude/settings.json` and every verb shim against the new
`AUTOHARN_ROOT`, in place, without touching your `deployment.json`, your Postgres schema, or your
ledger history. (`--force` only permits overwriting the scaffold-owned files this page's table
lists as "your project" above; it never touches your database.) There is no narrower one-line fix
today — flagged here as an honest gap, not quietly worked around, per this project's own
engineering-responsibility standard.

## Every configurable surface

### The apparatus.json mechanism switchboard

`.claude/apparatus.json` is your project's one switchboard: a `deny_hint` string plus a
`mechanisms` object, one entry per safety mechanism this project ships, each independently set to
`"off"` | `"observe"` | `"enforce"`. Every hook reads its own mode **live, at invocation time** —
editing this file changes real behavior on your very next tool call, no re-scaffold needed. The
full reference — every mechanism, its default, why that default, and the `"off"`/`"observe"`/
`"enforce"` semantics in detail — lives in your scaffolded project's own
`.claude/APPARATUS.md` (`bootstrap/templates/APPARATUS.md` is its source); condensed here:

| mechanism | default | costs money? | what it does |
|---|---|---|---|
| `change_gate` | `enforce` | no | refuses a source-file edit with no preceding ledger entry naming it |
| `permit_to_work` | `enforce` | no | refuses an edit when no [work item](GLOSSARY.md#permit-to-work) is open+claimed |
| `stamp_intercept` | `enforce` | no | injects the HMAC [stamp](GLOSSARY.md#stamp) into every `Bash` call |
| `clean_exit` | `enforce` | no | blocks a session `Stop` while review debt / open work is outstanding |
| `demurral_detect` | **`off`** | **yes — one `claude -p` call per `AskUserQuestion`/`Stop`** | classifies whether a stop looks like an unjustified demurral |
| `mutation_observer` | `observe` | no | warns (never denies — technically cannot) on an unledgered file mutation |
| `delegation_observer` | `observe` | no | journals every subagent dispatch; warns if none is ledgered as a decision |
| `doc_shapes_gate` | `observe` | no | write-time check for two measured documentation-legibility defect shapes |
| `read_observer` | `observe` | no | journals every file read (for reviewer-independence evidence) |
| `bash_completion` | `observe` | no | journals a Bash call's completion timestamp, paired to its dispatch |
| `doc_legibility_critic` | **`off`** | **yes — one `claude -p` call per `.md` write/edit** | the lightweight LLM half of [ADR-0017](law/adr/0017-the-zero-context-reader.md)'s legibility discipline |

The two costed mechanisms carry their own `cost_note` field **in the config itself**, next to the
switch — you read what flipping it on will bill you for at the exact place you flip it, not in a
separate document you might not find. Both default `off` under a standing maintainer mandate: "no
world silently bills its operator."

**Unknown mechanism names are swept loudly, not silently ignored.** A typo'd key —
`"doc_shapse_gate"` instead of `"doc_shapes_gate"` — used to configure nothing and warn no one
(mode *values* were always validated; nothing checked the *keys*). As of this page,
`hooks/pretooluse_change_gate.py` sweeps your project's **entire** `mechanisms` object against the
live known-mechanism set on every invocation (it fires on nearly every governed edit, so a typo
surfaces on your very next tool call), and `python3 gates/apparatus_unknown_keys.py
<your-project-dir>` runs the identical check on demand. The known set is *derived* from
`hooks/*.py`'s own source (`filing/apparatus_registry.py`) — never a hand-typed list that could go
stale the way the shipped `apparatus.json` default itself briefly did (see that module's own
docstring for the worked example). Both report the exact bad key and the full valid set; neither
ever treats an unrecognized key as widening a permission.

### `bootstrap/new-project.sh` — the governed-world scaffold

The full command shape, in its two forms — explicit schema names, or the one-name `--new-world`
shorthand the quick-start above uses:

```
bootstrap/new-project.sh <dest-dir> --db <db> --host <host> --schema <schema> \
    --kern <kern> --role <role> [--name <project-name>] [--force]

bootstrap/new-project.sh <dest-dir> --new-world <world> --db <db> --host <host> \
    [--name <name>] [--force]
```

- `<dest-dir>` — where to stamp the project (created if missing).
- `--db` / `--host` — the Postgres database and host your ledger lives on (see the
  [Postgres FAQ](#faq-provisioning-postgres-for-autoharn) below if you have not set this up yet).
- `--schema` / `--kern` / `--role` — the ledger schema, kernel schema, and granted subject role
  your project's tools connect as, OR:
- `--new-world <world>` — derives all three from one name (`--new-world run3` → schema `run3`,
  kernel `run3_kernel`, role `run3_rw`), applies the full kernel lineage, provisions the stamp
  secret, and registers the standard principals (`reviewer`, `commissioner`) automatically — the
  one-command path the quick-start above uses. An explicit `--schema`/`--kern`/`--role` still wins
  if given (e.g. the derived name collides with something that already exists).
- `--name` — your project's own label, written into `deployment.json` and used by the scaffolded
  `judge` shim as the target name for autoharn's own derivation-banking subdirectory — the
  directory `engine/ledger_differential.py` files each `./judge` run's evidence under, inside
  the autoharn checkout, keyed by this name. Pick something that will not collide with
  autoharn's own curated target names (`toy`, `nla`,
  `e15`–`e18`) or its scratch-naming conventions (`^s\d+[a-z]*$`, `*_scratch`) — default is your
  `<dest-dir>`'s basename.
- `--force` — overwrite an existing scaffold at `<dest-dir>` (default: refuse). Never touches your
  database; only regenerates the scaffold-owned files this page's ["what state lands
  where"](#what-state-lands-where) table names.

Classic mode (no `--new-world`) applies **no kernel DDL at all** — you apply a kernel lineage to
your own schema/kern/role yourself first (`kernel/lineage/`, see `kernel/lineage/README.md`), then
scaffold. `--new-world` is the one-command path; classic mode is for a schema you are managing by
hand for another reason.

### `bootstrap/track-work.sh` — a standing work tracker, not a governed world

The command shape — deliberately shorter than `new-project.sh`'s, because this scaffold applies
no kernel lineage and wires no hooks at all (see below):

```
bootstrap/track-work.sh <project-dir> --name <name> --db <db> --host <host> \
    [--schema <schema>] [--kern <kern>] [--role <role>] [--force]
```

Gives **any** directory — it need not be a git repository, need not be a Claude Code project, need
not ever run a governed Claude Code session — a standing, indefinite-lifetime work-tracking
deployment: `deployment.json` plus five read/write verb shims (`led`, `pickup`,
`distance-to-clean`, `judge`, `audit`) and the three standard principals, with **no hooks wired,
no kernel-delta regime, no [runs-are-linear](GLOSSARY.md#run) posture**. Where
`bootstrap/new-project.sh --new-world` stands up a habitat for *one governed run*,
`track-work.sh` stands up a Postgres-backed replacement for a hand-edited `TODO.md` — usable by a
human, a script, or an occasionally-governed agent, for a project's whole lifetime. `--name` is
required (unlike `new-project.sh`'s optional `--name`): it derives `--schema`/`--kern`/`--role`
from one value the same way `new-project.sh --new-world` does, so the three names that must agree
stay in agreement by construction.

### Environment variable overrides

Most values a scaffolded project's hooks need resolve automatically from your `deployment.json` —
you should rarely need any of the variables below. When you do (a one-off override, a debugging
session, a non-standard layout), the precedence is always **env var > `deployment.json` >
byte-held default**:

| value | env var | reads from `deployment.json`'s |
|---|---|---|
| Postgres host | `LEDGER_HOST` | `host` |
| Postgres database | `LEDGER_DB` | `db` |
| ledger relation | `GATE_LEDGER` | `<schema>.ledger` |
| your project's root | `GATE_SUBJECT_ROOT` | (the `deployment.json`'s own directory) |
| change-gate state file | `GATE_STATE` | `<root>/.claude/change_gate_state.json` |
| change-gate journal | `GATE_JOURNAL` | `<root>/.claude/logs/change_gate.journal.jsonl` |
| stamp secret path | `STAMP_SECRET` | (no default fallback — must resolve to a real file) |

**A note on names you may see in an older scaffolded project.** Projects scaffolded before this
page carry an older, era-coded environment-variable family (`E13_GATE_DB`, `E13_GATE_LEDGER`,
`E13_SUBJECT_ROOT`, `E13_GATE_STATE`, `E13_GATE_JOURNAL` — "E13" names a since-retired internal
experiment, meaningless to an adopter reading their own `settings.json` cold). Those names still
work — every hook accepts them as silent, deprecated aliases for the neutral names in the table
above, so an already-scaffolded project is never broken by this change — but the scaffold no
longer *writes* them: every project scaffolded from this checkout onward gets the neutral names
directly. If your own `.claude/settings.json` still shows `E13_GATE_*`, it works exactly as
before; re-scaffolding with `--force` (see [the install-path
contract](#the-install-path-contract--read-this-before-you-move-anything) above) is the only way to
pick up the newer names, and there is no need to unless you want your own settings file to read
more plainly.

### `governed_files.json`

`.claude/governed_files.json` — `{"patterns": ["*.py"]}` — chooses which files the change gate
protects, matched with `fnmatch` against the path relative to your project root and against the
bare filename (`"*.py"` reaches nested files; no `"**"` needed). Missing, unreadable, or malformed
falls back to the same default it ships with (every `*.py` file) — a project that has not yet
configured this is never silently ungoverned. Add `"*.sql"` to also govern migrations, or narrow
to `"src/*.py"` to leave a scratch-scripts directory ungoverned; no code change, no allowlist
elsewhere.

## FAQ: provisioning Postgres for autoharn

Every governed project needs a Postgres database it can reach, and a role scoped to it. If you
already have one, skip to [the pg_hba hardening
question](#faq-the-pg_hba-network-rule-you-may-want-to-add) below. If not, here is the minimum
that gets you scaffolding-ready — copy-paste steps, with what you should see at each one.

**Step 1 — create a database and a role**, from a `psql` session with superuser access to your
cluster:

```sql
CREATE ROLE myproject_rw LOGIN PASSWORD 'choose-a-real-password';
CREATE DATABASE myproject OWNER myproject_rw;
```

*What you should see:* `CREATE ROLE` then `CREATE DATABASE`, no error. If you plan to run several
projects against one shared database (autoharn's own convention — see `toy`, `nla` in this
repository's own use), create the role once and reuse the database, letting each project claim its
own schema pair instead (the `--schema`/`--kern` scaffold flags above) — you do not need a new
database per project.

**Step 2 — grant the role what the kernel lineage needs.** `bootstrap/new-project.sh
--new-world` applies the kernel lineage AS the role you name in `--role`, via `SET ROLE`, not as
the connecting superuser bypassing grants (this project's own ADR-0012 P1 posture: one mechanism,
never a bypass) — so that role needs `CREATE` on the target database before you scaffold:

```sql
GRANT CREATE ON DATABASE myproject TO myproject_rw;
```

*What you should see:* `GRANT`, no error. Now `bootstrap/new-project.sh <dir> --db myproject --host
<your-host> --new-world <name>` (or classic mode with explicit `--schema`/`--kern`/`--role`) can
apply the kernel lineage and scaffold your project.

**Step 3 — confirm you can reach it** from the host where you will actually run Claude Code:

```
$ psql -h <your-host> -U myproject_rw -d myproject -c "SELECT current_user;"
```

*What you should see:* either a password prompt (if you set one) or an immediate `current_user`
row — either way, no connection-refused or authentication error. If this fails, the next question
is almost always `pg_hba.conf`, not Postgres itself.

## FAQ: the pg_hba network rule you may want to add

This section documents a specific, investigated hardening step for one real deployment shape —
Postgres reachable over a private subnet, one cluster-wide superuser role, `trust` authentication
for every database — condensed from the full investigation in
[`design/PG-HBA-HARDENING.md`](design/PG-HBA-HARDENING.md) (every fact there is witnessed against
a real cluster; read it in full before applying anything non-trivial). **This page documents; it
does not apply anything for you** — editing `pg_hba.conf` and reloading Postgres on a database
that matters is your own act, on your own schedule, with your own rollback plan. Skip this section
entirely if your Postgres already requires a password for every role, including its superuser.

**The question this answers:** if your cluster's superuser (commonly `postgres`, or — as in this
project's own deployment — a role named for the operator) can connect from the network with **no
password at all**, anyone who can reach that address on the network can become that superuser and
bypass every grant-level protection this project's append-only ledger design otherwise relies on.
Closing that one hole, without touching anything else, looks like this:

**1. Find out if you have the hole.** From `psql`, as your superuser:

```sql
SELECT rolname FROM pg_roles WHERE rolsuper;
SHOW hba_file;
```

*What you should see:* the exact name(s) of your superuser role(s), and the path to your live
`pg_hba.conf` (which may be on a different host than the one you are running `psql` from — check
`SHOW listen_addresses` if you are not sure). If every rule in that file governing your superuser
role says `trust`, you have the hole.

**2. Set a password for the superuser**, from an *already-connected* session you leave open for
the rest of this procedure (the lockout guard — do not skip this):

```
psql=# \password <your-superuser-role>
```

Use `\password`, not a literal `ALTER ROLE ... PASSWORD` string — the meta-command prompts without
echoing and is never written to `.psql_history`.

**3. Insert one new rule block**, on the database host, *before* every existing rule in
`pg_hba.conf` (back up the file first: `cp pg_hba.conf pg_hba.conf.bak-$(date +%Y%m%d)`):

```
# superuser network hardening — <your-superuser-role> is this cluster's ONLY superuser role
host  all  <your-superuser-role>  <your-client-subnet>/32  scram-sha-256
```

One rule, placed first, matches your superuser against *every* database before any later
`host <db> all ... trust` catch-all can admit it — closing the hole everywhere at once rather than
patching each database's block separately. Nothing else in the file changes: every non-superuser
role's `trust` rules (the ones your scaffolded projects actually connect as) are untouched.

**4. Reload, then verify both witnesses**, from the still-open session:

```sql
SELECT pg_reload_conf();
```

Then, from a **fresh** terminal:

*Witness A — the hole is closed:* `psql -h <host> -U <superuser> -d <db>` now prompts for a
password (or refuses without one) — never a bare prompt.

*Witness B — your projects still work:* `./led ...` (or whatever your project's own role
connects as) behaves exactly as before — no new prompt, no new failure. **Both are required** —
one without the other is either an unfixed hole or a new outage, not "done."

If either witness fails, restore from the backup (`cp pg_hba.conf.bak-<date> pg_hba.conf` then
`SELECT pg_reload_conf();`) and re-diagnose before retrying. Full detail, including the exact
column-aligned rule block, the second (local Unix-socket) hole this pass deliberately leaves open
and why, and the honest limits of what a password requirement does and does not protect against,
is in [`design/PG-HBA-HARDENING.md`](design/PG-HBA-HARDENING.md) §2–§5.

## Related

- [OPERATING-CARD.md](OPERATING-CARD.md) — the operator-facing card for someone already running a
  scaffolded project: the verbs, the resumption doctrine, the kernel-delta decision tree.
- [GLOSSARY.md](GLOSSARY.md) — every coined term this page uses, defined once.
- [`design/PG-HBA-HARDENING.md`](design/PG-HBA-HARDENING.md) — the full pg_hba investigation this
  page's FAQ condenses; read it in full before applying anything to a database that matters.
- [`law/adr/0017-the-zero-context-reader.md`](law/adr/0017-the-zero-context-reader.md) — the
  documentation-legibility discipline this page is written to, and the source of
  `doc_legibility_critic`'s design.
- `bootstrap/templates/APPARATUS.md` — your scaffolded project's own copy of the full mechanism
  reference this page's switchboard table condenses (identical content, written into every
  project by the scaffold so it travels with the project, not only with this repository).
- `filing/apparatus_registry.py` — the derived known-mechanism set the unknown-key sweep uses; its
  own docstring is the fuller account of why a hand-maintained list was rejected.
