# WORLD-REBIRTH-RUNBOOK — birthing a successor world and carrying its context

<!-- design-currency: status=evergreen -->
<!-- doc-attest-exempt: operator/orchestrator runbook distilled from the EXECUTED
experience2->experience3 rebirth of 2026-07-27 (autoharn ledger records that arc); every
step below was witnessed in that run or is marked otherwise. Removal condition: superseded
by a scripted single-verb rebirth, if one is ever commissioned. -->

**Who this is for.** The ORCHESTRATOR of any session the maintainer asks to "re-birth
world N as N+1" — deliberately written so a standard (Sonnet-grade) orchestrator can
execute it mechanically. The maintainer's own two acts are marked **MAINTAINER**; every
other step is the orchestrator's. The predecessor of this document,
[FOSSIL-EXPERIENCE-REBIRTH-RUNBOOK.md](FOSSIL-EXPERIENCE-REBIRTH-RUNBOOK.md), is the
worked 2026-07-22 example from before the tooling existed; this one is current procedure.

**Doctrine in one line (runs-are-linear, maintainer-ratified 2026-07-11):** worlds are
born, not upgraded. Never delta-patch a populated world's kernel; the successor is a
fresh birth on the current full chain, the predecessor's operative context crosses via
the manifest tool, and the predecessor becomes dust (its disposal is Step 7, the
maintainer's call).

**The one standing hazard:** `bootstrap/teardown-world.sh` reaches live Postgres schemas.
Never point it (or any DROP) at the predecessor before Step 7's explicit maintainer act,
and never at anything you did not just birth yourself.

---

## Step 1 — EXTRACT, read-only, BEFORE anything else touches the project dir

The birth (Step 3) overwrites the project's `deployment.json` — extract first, and
preserve the old record:

    cd <autoharn checkout>
    cp <project-dir>/deployment.json <project-dir>/deployment.<oldworld>.json.dust
    HARNESS_PGHOST=<db host> python3 bootstrap/extract_context.py extract \
        --deployment <project-dir>/deployment.json \
        --out ~/<oldworld>-extract.jsonl --principal author

You should see per-class counts and then, loudly:
`MANIFEST IS UNREVIEWED ... ingest refuses it wholesale`. That refusal is correct — it is
the maintainer's veto surface. Extraction is pure SELECTs; it needs no running boundary.

**Step 1b — the STANDING-FORCE SURVIVAL AUDIT (generalized 2026-07-28 from the
never-graded-rules sweep, after the maintainer's ADR-0000 direction: "the class as
first named is presumed too narrow" — it was; the enumerated universe and its
per-kind classification live in
[design/PHOENIX-SURVIVAL-UNIVERSE-2026-07-28.md](../design/PHOENIX-SURVIVAL-UNIVERSE-2026-07-28.md),
read it before running a phoenix).**

**Closure statement (ADR-0000 Rule 2(a)).** Quantification universe: every datum with
FUTURE FORCE — anything that binds or informs behavior after the old world dies —
enumerated from the system itself in the matrix above: the 33 ledger kinds (each
classified historical vs standing-force), the 8 statement grammars (all riding
`kind=decision`, so carried ONLY when graded durable), the kernel side-tables
(principal registry and its suspension/revocation/standing/relation/binding/
competence/entitlement families), the config surfaces (courier.toml, features.json,
governed_files.json, world_identity, keys/), and cross-world state (open missive
threads, counterpart courier address books). Deliberately mortal, and correctly so:
historical records die with their world — runs-are-linear working as designed; the
audit's job is to make that boundary CHOSEN, never accidental. Known gaps at this
writing, ranked in the matrix and tracked as autoharn3 work items: principal
revocations/suspensions carried by NOTHING (the top hazard — a revoked principal
could be re-admitted post-phoenix), ungraded `resource:` deontic tiers, the courier
principal and world_identity birth steps, the courier.toml counterpart handover.

Before the maintainer reviews the manifest, run BOTH sweeps against the OLD world and
disposition every hit:

1. Never-graded process rules (the original sweep — anything binding future process
   gets re-ledgered `--grade durable` in the old world so the extract carries it):

       psql -h <db host> -U <you> -d <db> -c "
         SELECT id, left(statement,160) FROM <oldworld>.ledger
         WHERE kind='decision' AND decision_grade IS NULL
           AND statement ~* '(ruling|standing|pattern|from now on|always|never|every)'
         ORDER BY id"

2. Standing-force rows the extract structurally ignores (until the extract itself
   carries them — work item extract-standing-force-classes): principal suspensions/
   revocations/standing declarations/relations/bindings/competences, entitlement
   config, ungraded statement-grammar rows (especially `resource:` tiers), and any
   in-force `missive_undisposed` entries (an open thread at cut time must be
   dispositioned or explicitly handed to the successor via the counterpart's
   courier):

       psql -h <db host> -U <you> -d <db> -c "
         SELECT kind, count(*) FROM <oldworld>.ledger l
         WHERE kind IN ('principal_suspended','principal_revoked',
           'principal_standing_declared','principal_relation_asserted',
           'principal_role_bound','principal_key_bound',
           'principal_competence_granted','entitlement_class_configured')
           AND NOT EXISTS (SELECT 1 FROM <oldworld>.ledger s WHERE s.supersedes=l.id)
         GROUP BY kind"

   Any nonzero count is a maintainer decision at the manifest: re-assert in the
   successor, or record the deliberate drop with its reason. REVOCATIONS ARE NEVER
   SILENTLY DROPPED.

## Step 2 — **MAINTAINER**: review and countersign the manifest

The maintainer reads the manifest (the `carry-verbatim` statements are the part worth
actual reading), then appends the review line themselves — a reviewer DISTINCT from the
extracting principal; the orchestrator never appends it:

    echo '{"record":"review","reviewed":true,"reviewer":"<name>","ts":"'$(date -Is)'"}' \
        >> ~/<oldworld>-extract.jsonl

## Step 3 — birth the successor into the SAME project directory

    HARNESS_PGHOST=<db host> bash bootstrap/new-project.sh <project-dir> \
        --new-world <newworld> --db <db> --host <db host> --force

`--force` is required because `deployment.json` exists (you preserved it in Step 1).
`rc=0` and the maintainer signing block ending the output = born. The newborn registers
exactly four principals (author/reviewer/commissioner/write-boundary) and, under s60,
binds ONLY `author` to the `authority` role — this fact decides Step 5's `--actor`.

## Step 4 — serve it through the ONE hub (consolidated 2026-07-27; no second service)

There is one boundary process for all worlds: the autoharn checkout's own
ensure-running-managed instance (port 8433, config `<autoharn checkout>/
boundary-multiplex.toml`). Do NOT stand up a per-project service; that shape is retired.

1. Append a `[deployments.<newworld>]` table to the hub's `boundary-multiplex.toml`
   (copy an existing table's five keys; match the file's house idiom, add a dated note).
2. `./autoharn service stop && ./autoharn service start`
3. `curl -s http://127.0.0.1:8433/d/<newworld>/health` → a JSON body naming the world.
4. Add the two served-shim keys to the project's `deployment.json`:
   `"boundary_url": "http://127.0.0.1:8433"`, `"boundary_deployment": "<newworld>"`.
5. `cd <project-dir> && ./autoharn doctor` → expect `TOTAL: 0 FAIL`.

## Step 5 — INGEST, exactly once

    HARNESS_PGHOST=<db host> python3 bootstrap/extract_context.py ingest \
        --manifest ~/<oldworld>-extract.jsonl \
        --deployment <project-dir>/deployment.json \
        --actor author

- `--actor author`, NOT commissioner: a newborn's s60 entitlement map gives the
  `authority` role (which `principal_registered` acts require) to `author` alone —
  witnessed 2026-07-27: a commissioner-actored ingest had every principal registration
  refused with the entitlement teach-text.
- **`rc=1` does NOT mean nothing landed.** The tool emits one JSON outcome line per
  item — `RE-ASSERTED` / `RE-ENACTED` / `DROPPED` — and exits nonzero when anything
  dropped. EXPECTED drops, every run: the four birth principals (SQLSTATE 23505
  duplicates — they already exist by birth) and every never-class/drop-with-reason item.
  Read the outcome lines; count them; judge from them, never from rc alone.
- **NEVER re-run ingest wholesale.** Witnessed cost of exactly that mistake 2026-07-27:
  a second full run re-asserted all standing decisions (duplicates in an append-only
  ledger, curable only by supersession) while every re-opened work item refused
  (s31: a slug's opening act permanently burns the slug). If a run partially failed,
  fix the cause, then carry ONLY the items whose outcome line says DROPPED-for-that-cause
  — by hand through `led`, or by a manifest copy pruned to those items (it needs a fresh
  review line; pruning is a content change).
- **Hand-carries must carry the grade.** The tool passes `--grade` on its own
  re-asserts; a hand-carried decision without `--grade <its manifest grade>` lands
  OUTSIDE the standing view (witnessed 2026-07-27). Likewise expect the
  garbage-statement guard to refuse statements that deliberately quote CLI flags —
  that is its false-positive shape; the override is
  `--statement-really-contains-cli-text`, used per-row, never wholesale.

## Step 6 — verify what landed

    cd <project-dir>
    ./autoharn led standing | head        # the re-asserted decisions, each once
    ./autoharn led work list              # re-opened items, unclaimed
    ./autoharn doctor                     # still 0 FAIL

Then report to the maintainer, per class: carried counts, expected-drop counts, and any
drop that was NOT expected, quoted with its refusal text. No umbrella claims.

## Step 7 — **MAINTAINER**: dust disposal (destructive; operator-authority by design)

Default doctrine keeps dust worlds queryable read-only forever. If the maintainer
instead rules them defunct (drift risk), the evidence is preserved FIRST — and its
capture is VERIFIED before any drop — then the schemas go. The drops are the
maintainer's own commands (permission classifiers correctly refuse them to an agent);
the capture is the orchestrator's, being read-only.

**Never `pg_dump | gzip` straight into a drop.** A pipe reports gzip's exit status,
not pg_dump's — a failed dump yields a valid-gzip EMPTY file and a green `gzip -t`.
Witnessed cost, 2026-07-27: the `experience` world's schemas were dropped against a
20-byte empty dump; that evidence is unrecoverable outside host-level DB backups.
The same incident's second lesson: a stray catalog orphan (a `pg_proc` row whose
schema was dropped — leftover of some earlier interrupted CASCADE) makes `pg_dump`
of the WHOLE database fail with `schema with OID <n> does not exist`, so pg_dump's
success is never assumable on this database class. Capture accordingly:

    # dump to a FILE with an explicit rc check -- no pipe:
    pg_dump -h <db host> -d <db> -n <oldworld> -n <oldworld>_kernel \
        -f <durable>/dust/<oldworld>-dust-$(date -I).sql \
        && echo DUMP-RC-OK || echo DUMP-FAILED
    grep -cE '^COPY|^CREATE TABLE' <durable>/dust/<oldworld>-dust-*.sql   # nonzero or it is NOT a dump

    # if pg_dump fails (the catalog-orphan class): fall back to per-table \copy --
    # the schema DDL is fully reproducible from kernel/lineage in git, so DATA is the
    # evidence; export every base table EXCEPT stamp_secret (secrets never cross):
    psql -h <db host> -d <db> -c "\copy (SELECT * FROM <schema>.<table>) TO
        '<durable>/dust/<oldworld>-data/<schema>.<table>.csv' WITH (FORMAT csv, HEADER)"
    # ...then cross-check: SELECT count(*) per table vs the COPY N output. Only after
    # the counts agree does anything drop.

    echo '<oldworld>' | bash bootstrap/teardown-world.sh <oldworld> \
        --db <db> --host <db host> --force-non-scratch

If the role drop refuses with "privileges for database <db> depend on it", the
leftover is database-level grants: `DROP OWNED BY <oldworld>_rw;` (as a role with
authority over them, usually the superuser) then `DROP ROLE <oldworld>_rw;`.

After a drop: remove the world's table from the hub's `boundary-multiplex.toml` (restart
the service), and note that any manifest/ledger text saying "the dust world remains
queryable forever" now resolves to the dump artifact instead — cite the artifact path
when it matters.

## What the manifest tool decides for you (so you don't re-litigate it)

Class defaults are the consult's ratified taxonomy
(vestigial_documentation/design/FABLE-WORLD-CONTEXT-MIGRATION-CONSULT-2026-07-19.md):
standing decisions carry verbatim; principals, open work, open questions carry as fresh
typed acts; commissions, refusals, review discharges, estimates never cross (commissions
and refusals are structurally payload-free in the manifest). The judgment that remains
genuinely human: WHICH re-opened principals/items still deserve to exist in the
successor — the maintainer prunes at Step 2 by editing dispositions before signing,
which is exactly what the review line attests.

## License

Public Domain (The Unlicense).
