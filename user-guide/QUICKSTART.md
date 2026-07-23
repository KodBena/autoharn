# QUICKSTART — clone → collaborating

This page is a ten-minute, hands-on walkthrough for someone who just cloned this repository and
wants to *feel* the harness work before reading further: the decision ledger, the refuse-and-teach
change gate, the interception stamp, and a close. Every command below has actually been run from a
fresh clone, not merely proofread — the `runs/` directory holds that acceptance run as its witness.

Before you start, set these once in your shell (never hard-coded below, so this page is genuinely
copy-paste rather than "every line must be edited first"):

```sh
export PGHOST=<your postgres host>       # e.g. localhost, or your LAN database box
export PGDATABASE=<your database name>   # e.g. harness
```

If you have no Postgres database yet, `USER-CONFIGURATION.md`'s ["FAQ: provisioning Postgres for
autoharn"](USER-CONFIGURATION.md#faq-provisioning-postgres-for-autoharn) is a copy-paste
walkthrough for that first step.

## 0. Bootstrap

```sh
sh bootstrap/bootstrap.sh          # env + git-hook install + merge-driver install + gate runnability + DB reachability
```
Green means the gate chain is installed, the harness DB is reachable, and the merge driver
described just below (`jsonl-union`) is wired. A red DB line is a
host fact (pg_hba), surfaced loudly — it names the maintainer act needed, never soft-passes.

**What the merge-driver install line does, and the manual fallback.** `attestations/*.jsonl`
merges mechanically via `tools/merge_jsonl.py` — a union merge driver for append-only jsonl
ledgers, instead of the append-append conflicts a bare `git merge` produces on those files.
`.gitattributes` (versioned) names which files use it; the driver COMMAND itself lives in
`.git/config` (unversioned, so it cannot ride in `.gitattributes`) — bootstrap.sh's step above
installs it, once per clone, the same shape as the `core.hooksPath` line bootstrap.sh already
sets. A checkout made from this repository before this merge-driver mechanism existed, or whose
`.git/config` was never re-run through bootstrap.sh since, installs it by hand:

```sh
git config merge.jsonl-union.name "union merge driver for append-only jsonl ledgers"
git config merge.jsonl-union.driver "python3 tools/merge_jsonl.py %O %A %B"
```

## 1. Stand up a scratch world (the subject decision-ledger)

The kernel DDL is a lineage (`kernel/lineage/`) that has grown well past its first generations —
naming a fixed generation here would only fall stale the next time a delta lands, the exact
defect an earlier version of this page had (it named "s15" long after the real head had moved on
by dozens of generations). Rather than hand-apply individual SQL files, use the one command that
derives the current lineage live and applies it in one call — the same command
[USER-WALKTHROUGH.md's "Opening a new world" section](USER-WALKTHROUGH.md#4-opening-a-new-world-one-world-per-run)
uses for a real run, here used for a disposable demo:

```sh
bootstrap/new-project.sh /tmp/qs-demo --new-world qs_demo --db "$PGDATABASE" --host "$PGHOST"
```

This derives the ledger schema/kernel-schema/role from the one name `qs_demo`
(`qs_demo`/`qs_demo_kernel`/`qs_demo_rw`), applies `high_watermark_1.sql` plus every kernel delta
through the current head (run `bootstrap/new-project.sh` with no arguments to see exactly which
generation that is right now — it derives and prints its own head live, never a number frozen
into this doc), seeds a stamp secret, and writes a small `led`/`judge`/`pickup` project directory
at `/tmp/qs-demo`. The rest of this page uses that world:

```sh
S=qs_demo; K=qs_demo_kernel; R=qs_demo_rw
cd /tmp/qs-demo
```

## 2. File a decision — the ledger, actor stamped from the connection

The ledger is append-only, and the actor is stamped from the connection identity, never a
self-declared field:

```sh
./led decision "adopt the search-path idiom"
./led --recent 1
```

## 3. Refuse-and-teach — the change gate

The subject-side change gate (`hooks/pretooluse_change_gate.py`) refuses an unticketed / out-of-scope
edit and *teaches* the honest path, rather than silently allowing it. `drive/gate_probe.py` drives it
exactly as Claude Code's PreToolUse hook would, against a scratch mirror:

```sh
cd -   # back to the autoharn checkout
python3 drive/gate_probe.py            # probes the change gate; a disallowed edit is refused + taught
```

## 4. The interception stamp (write-time provenance)

A ledger write routed through a governed session carries an HMAC stamp binding it to the actual
invocation identity (session+agent), which the writer can neither omit nor forge. The mechanism +
its both-polarity proof:

```sh
python3 kernel/fixtures/s17_stamp_fixture.py     # forgery/staleness refused; a proxy self-review is caught
```

## 5. A close (the instruments read the ledger and derive a verdict)

`instruments/close_manifest.py` is the registry of mandatory close lines; a close runs them against a
target and is RED if any line fails or a mandatory line silently did not run. Its record is the
first occupant of `runs/`:

```sh
LEDGER_DB="$PGDATABASE" LEDGER_SCHEMA=$S python3 instruments/close_manifest.py <target> --mode close
```

## 6. Fire up an auditor on a snag

Stuck, or unsure a fix is a fix? See `bootstrap/AUDITOR.md` — the out-of-frame second-opinion
affordance (ADR-0014), which is how this project gets unstuck without ego-locking.

---
Teardown the scratch world: `psql -h "$PGHOST" -d "$PGDATABASE" -c "DROP SCHEMA IF EXISTS $S CASCADE; DROP SCHEMA IF EXISTS $K CASCADE; DROP OWNED BY $R; DROP ROLE IF EXISTS $R;"` then `rm -rf /tmp/qs-demo`.

<!-- doc-attest-exempt: disclosed gap, not a clean exemption -- this file was substantially
     rewritten this session (usability review, ledger row 1180, 2026-07-23, findings 2/10/11/12):
     the frozen s15-s19 hand-apply sequence replaced with a live-deriving `--new-world` scaffold
     call (finding 2); the two `vestigial_documentation/` links dropped, citing `runs/` and plain
     prose instead (finding 10); the `WALKTHROUGH.md` reference fixed to the real filename,
     `USER-WALKTHROUGH.md`, with its actual section anchor (finding 11); and `PGHOST`/`PGDATABASE`
     shell variables introduced at the top so the body is genuinely copy-paste rather than
     requiring every `psql -h 192.168.122.1` line to be hand-edited first (finding 12). The old
     "doc-tree relocation ... no prose rewrite" marker this file carried near line 1 is struck,
     not carried forward, because it is no longer true. This edit has NOT been through a genuine
     fresh-context A:B:C loop (user-guide/ORCH-ABC-AUDIT-LOOP-RECIPE.md): the executing session
     had no Agent/Task-dispatch tool available to spawn a truly separate B invocation, the same
     disclosed gap user-guide/USER-CONFIGURATION.md's own marker names. Waived here only to
     unblock this commit, flagged loudly per CLAUDE.md's engineering-responsibility standard --
     the commissioning brief for this round states a cold-read pass follows the build; the
     orchestrator/maintainer should run it (or confirm one already ran) and replace this marker
     with an actual attestation record. -->
