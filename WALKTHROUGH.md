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

## What is NOT in this walkthrough, and why

- **The refuse-and-teach change gate** (an edit to a source file is refused unless a ledger entry
  declares it): the hook exists (`hooks/pretooluse_change_gate.py`) but is currently wired to the
  experiment's schema — pointing it at yours is a small adaptation job, not a command. Ask for it.
- **The close instruments and the formal conformance layer**: the regulatory-grade end of the
  project. Nothing above depends on them.
- **s18-criterion-principals**: reviewer machinery the project uses on itself; not part of a user
  kernel (deliberately excluded from `high_watermark_1.sql`).
