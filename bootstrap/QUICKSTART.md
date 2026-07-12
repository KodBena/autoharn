# QUICKSTART — clone → collaborating

This page is a ten-minute, hands-on walkthrough for someone who just cloned this repository and
wants to *feel* the harness work before reading further: the decision ledger, the refuse-and-teach
change gate, the interception stamp, and a close. Every command below has actually been run from a
fresh clone, not merely proofread — the acceptance criteria this claim is checked against are
[`provenance/CONSOLIDATION-MANDATE.md`](../provenance/CONSOLIDATION-MANDATE.md)'s §6 ("executed, not
proofread"), and the `runs/` directory holds that acceptance run as its witness.

## 0. Bootstrap

```sh
sh bootstrap/bootstrap.sh          # env + git-hook install + merge-driver install + gate runnability + DB reachability
```
Green means the gate chain is installed, the harness DB is reachable, and the two merge drivers
described just below (`jsonl-union` and `backlog-section-union`) are wired. A red DB line is a
host fact (pg_hba), surfaced loudly — it names the maintainer act needed, never soft-passes.

**What the merge-driver install line does, and the manual fallback.** `attestations/*.jsonl` and
`BACKLOG.md`'s dated sections merge mechanically via two drivers, `tools/merge_jsonl.py` and
`tools/merge_backlog_sections.py` (design's own name:
[design/ORCH-WORKTREE-LEDGERING.md](../design/ORCH-WORKTREE-LEDGERING.md), "3a. The jsonl merge
driver" and its sibling BACKLOG driver), instead of the append-append conflicts a bare `git merge`
produces on those files. `.gitattributes` (versioned) names which files use them; the driver
COMMAND itself lives in `.git/config` (unversioned, so it cannot ride in `.gitattributes`) —
bootstrap.sh's step above installs it, once per clone, the same shape as the `core.hooksPath` line
bootstrap.sh already sets. A checkout made from this repository before this merge-driver mechanism existed, or
whose `.git/config` was never re-run through bootstrap.sh since, installs it by hand:

```sh
git config merge.jsonl-union.name "union merge driver for append-only jsonl ledgers"
git config merge.jsonl-union.driver "python3 tools/merge_jsonl.py %O %A %B"
git config merge.backlog-section-union.name "dated-section union merge driver for BACKLOG.md"
git config merge.backlog-section-union.driver "python3 tools/merge_backlog_sections.py %O %A %B"
```

## 1. Stand up a scratch kernel (the subject decision-ledger)

The kernel DDL is a lineage (`kernel/lineage/`); apply it to a THROWAWAY schema (never an evidence
ledger). s15 is the current generation; the deltas add stamps, independence vocabulary, criterion
principals, and the s19 search-path foreclosure:

```sh
S=qs_demo; K=qs_demo_kernel; R=qs_demo_rw
psql -h 192.168.122.1 -d harness -v schema=$S -v kern=$K -v role=$R \
     -f kernel/lineage/s15-schema.sql \
     -f kernel/lineage/s17-stamp-mechanism.sql \
     -f kernel/lineage/s17-independence-vocabulary.sql \
     -f kernel/lineage/s18-criterion-principals.sql \
     -f kernel/lineage/s19-trigger-search-path.sql
```

## 2. File a decision — the ledger, actor stamped from the connection

The ledger is append-only; the actor is stamped from the connection identity (not a self-declared
field), and — thanks to s19 — an actor-omitted write resolves correctly even on this NON-default
schema (the exact class findings 16/37/45 named):

```sh
psql -h 192.168.122.1 -d harness -c \
  "SET ROLE $R; SET search_path=$S,$K; \
   INSERT INTO $S.ledger (kind, statement) VALUES ('decision','adopt the search-path idiom');"
psql -h 192.168.122.1 -d harness -tAc \
  "SELECT l.id, l.kind, p.name FROM $S.ledger l JOIN $K.principal p ON p.id=l.actor;"
```

## 3. Refuse-and-teach — the change gate

The subject-side change gate (`hooks/pretooluse_change_gate.py`) refuses an unticketed / out-of-scope
edit and *teaches* the honest path, rather than silently allowing it. `drive/gate_probe.py` drives it
exactly as Claude Code's PreToolUse hook would, against a scratch mirror:

```sh
python3 drive/gate_probe.py            # probes the change gate; a disallowed edit is refused + taught
```

## 4. The interception stamp (write-time provenance)

A ledger write routed through the intercepted psql path carries an HMAC stamp binding it to the
actual invocation identity (session+agent), which the writer can neither omit nor forge. The
mechanism + its both-polarity proof:

```sh
python3 kernel/fixtures/s17_stamp_fixture.py     # forgery/staleness refused; a proxy self-review is caught
```

## 5. A close (the instruments read the ledger and derive a verdict)

`instruments/close_manifest.py` is the registry of mandatory close lines; a close runs them against a
target and is RED if any line fails or a mandatory line silently did not run (F49). Its record is the
first occupant of `runs/`:

```sh
LEDGER_DB=harness LEDGER_SCHEMA=$S python3 instruments/close_manifest.py <target> --mode close
```

## 6. Fire up an auditor on a snag

Stuck, or unsure a fix is a fix? See `bootstrap/AUDITOR.md` — the out-of-frame second-opinion
affordance (ADR-0014), which is how this project gets unstuck without ego-locking.

## Starting an actual run, not a demo

Everything above is a scratch/demo kernel by hand. To open a real, isolated world for a run — its
own schema, its own ledger history, never mixed with a sibling run's — use
`bootstrap/new-project.sh --new-world`; see WALKTHROUGH.md's "Opening a new world (one world per
run)" section for the exact command, witnessed output, and what to watch for.

---
Teardown a scratch kernel: `psql -h 192.168.122.1 -d harness -c "DROP SCHEMA IF EXISTS $S CASCADE; DROP SCHEMA IF EXISTS $K CASCADE; DROP OWNED BY $R; DROP ROLE IF EXISTS $R;"`
