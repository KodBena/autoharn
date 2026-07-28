# The record — recipes

<!-- doc-attest-exempt: relocation-class mechanical move (work item faq-refactor-by-concern, ledger row 185 adjudication, 2026-07-28) -- the content below is byte-preserved prose moved verbatim out of user-guide/USER-RECIPES-FAQ.md (commit `178ec789439044bebb664e7374c2be757d064d11`; sections named in the provenance line above), plus mechanical `../` link-depth repairs and named cross-file link/anchor rewrites for content that relocated to a sibling factor file; no other prose was reworded (ADR-0020's clause 1: a residue disposition and a link gate are the mechanical floor, never a substitute for a cold meaning-preservation read -- that read DID run, by a fresh-context Agent invocation distinct from the session that performed the move; see this work item's execution report for the per-file outcome). The ADR-0017 A:B:C legibility loop is a SEPARATE read this session did not run: the coordinator schedules it after merge, per this work item's adjudication conditions (ledger row 185). Waived here only to unblock this commit. Removal condition: strike this marker and run the real ADR-0017 A:B:C loop next time this file is touched for content, not just link repair. -->

*Factored out of [`user-guide/USER-RECIPES-FAQ.md`](../USER-RECIPES-FAQ.md) at commit
`178ec789439044bebb664e7374c2be757d064d11`, sections "Correcting the record — supersession, and what to do about its fallout" and
"Ledger-wide as-of read and inspection-copy export (`asof-export`)"; byte-preserving (mechanical
`../` depth repairs only).*

**Charter:** the life of a row after it is written. Belongs: supersession, edge correction,
orphan disposition, cascade, as-of reading and inspection-copy export. Does not belong: whether
a row is believable (see EVIDENCE-AND-TRUST.md in this directory).

---

## Correcting the record — supersession, and what to do about its fallout

**I encoded a row wrong (wrong flag, missing refs, bad wording) — how do I fix it?**
Supersede it: write the corrected row with `--supersedes <old-row-id>` (for work items,
`led work open <new-slug> ... --supersedes <old-open-row-id>`). The ledger is append-only,
so a correction is always a new, linked row — the old one leaves current truth but stays
in history, never obscured. This is the default answer to every "I wrote it wrong"
situation; nothing is ever edited in place, and raw SQL against the ledger is never the
answer to a missing verb. Honest limit: superseding a work item's OPEN row permanently
burns its slug (a deliberate, ratified choice) — the replacement needs a new slug, and
surviving claims/edges that named the old slug must be re-issued. Grammar:
`./led work open` usage; semantics:
[FABLE-SUPERSESSION-UNIFORM-RETRACTION-SPEC.md](../../design/FABLE-SUPERSESSION-UNIFORM-RETRACTION-SPEC.md).

**I recorded a `work_depends_on` edge wrong (wrong `--type`, wrong endpoints) — how do I fix
it?** Same primitive, one kind over: `./led work depends <slug> <on-slug> [--type
blocks-close|blocks-start|informs] --supersedes <old-edge-row-id>`. This writes a NEW
work_depends_on row that both carries the corrected edge (a different `--type`, or different
`<slug>`/`<on-slug>` endpoints — re-pointing a mistaken edge entirely is legal) and retracts
the old row from current truth in the same act (`ledger.supersedes`, s31 — uniform across
every kind, reinstatement-free). Reach for this specifically when: the edge was typed wrong
(e.g. recorded `informs` when it should have been `blocks-close`, or vice versa); the edge
pointed at the wrong antecedent or dependent slug; or the mixed-deadlock case that s39's
claim-time refusal teach-text and its LIMITS section both name explicitly: a `blocks-close`
edge and a `blocks-start` edge between the
SAME two items in OPPOSITE directions produced a genuine mutual claim/close deadlock (neither
edge type's own construction-time cycle check catches this, because each is scoped to its own
edge type only): supersede ONE of the two edges to break the deadlock. Refused at construction
if `<old-edge-row-id>` does not exist, is not itself a `work_depends_on` row (a different kind
is corrected via its OWN verb's `--supersedes`, e.g. `led work open --supersedes` for a
`work_opened` row, `led work resolve-violation --supersedes` for a disposition row — one
column, three typed entry points, never a raw-SQL fourth), or is already superseded (the row
that superseded it is named, so you can inspect or correct THAT one instead). Re-issuing the
exact same edge shape that a supersession just retired is NOT refused as a duplicate — there
is no uniqueness check on `work_depends_on` rows at all (unlike `work_opened`'s permanent
slug-burn). When the new edge's slug or type differs from the old one, the CLI prints an
advisory naming both the old and new endpoints, so the correction stays legible without
digging through raw history. History stays: the superseded edge remains visible in
`work_violation_history`/raw ledger reads; current truth (`work_edge_blocks_close`,
`work_edge_blocks_start`, `work_item_blocks_start_blockers`, and the claim-time/strict-close
refusals that read them) moves on to the new edge only. Grammar: `./led work depends` usage;
kernel semantics: kernel/lineage/s39-blocks-start.sql (blocks-start),
kernel/lineage/s30-typed-dependency-edges.sql (blocks-close),
[FABLE-SUPERSESSION-UNIFORM-RETRACTION-SPEC.md](../../design/FABLE-SUPERSESSION-UNIFORM-RETRACTION-SPEC.md)
(the shared supersession mechanics).

**I superseded a parent item and `work violations` now shows orphan rows that nothing can
clear — did I break the world?**
No, and this exact situation happened in a real deployment (a composite parent superseded
while five children — three already closed — still hung under it; every child's parent-edge
became an `orphaned_by_retraction` violation with no discharge path, permanent blocking
debt). Nothing was lost: the children's own rows, closes, and reviews are all intact; the
violations are the record correctly describing dangling linkage. The gap was ours — a
violation an operator can legally cause must have an answering act, and orphans had none.
The fix is the s37 violation-disposition mechanism
([FABLE-ORPHAN-DISPOSITION-SPEC.md](../../design/FABLE-ORPHAN-DISPOSITION-SPEC.md)):
`led work resolve-violation <violating-act-id> <reissued|retired> "<basis>"` answers any
in-force violation with a reviewed, attributable row, and `led work supersede-cascade` handles the
live-descendants ripple in one witnessed pass. Until your world has s37: take no further
supersession, let the stop-gate (`hooks/stop_clean_exit.py`, the Stop hook that blocks a
session from ending while governance debt is open) handle stops via its loud fail-open
(that valve exists for exactly this — structurally unclosable debt), and migrate when the
delta reaches you.
**When do I reach for `resolve-violation`, and when for `supersede-cascade`?**
They are not alternatives at the same level: `resolve-violation` is the primitive and
`supersede-cascade` is a convenience built entirely out of it — nothing the cascade does
is impossible by hand, and the cascade writes no special rows. Reach for
`resolve-violation` when violations ALREADY EXIST (you are cleaning up after a
supersession, yours or an inherited one), and always for a superseded parent's
closed/settled children — their edges get `retired` dispositions and the children
themselves are never touched. Reach for `supersede-cascade` when you are ABOUT TO
supersede an item that still has live (open) descendants: it performs the whole ripple —
re-open each live child under a new slug citing its predecessor, re-issue claims and
edges, write each resulting orphan's `reissued` disposition — in one witnessed pass, in
dependency order. The order is the point: done by hand, each step of the ripple mints new
orphans one level down (by design — the mechanism is closed under that recursion), and a
mis-ordered hand-walk leaves you resolving violations you created two steps earlier.
Honest limit: the cascade only handles the subtree below the item you name; edges INTO
the subtree from elsewhere still surface as orphans afterward and are yours to
`resolve-violation` individually, because no tool can know whether an outside edge should
follow the successor or die with the predecessor.

**Why is the fix a disposition act, not "supersede the whole subtree"?**
A subtree is not closed under reference, and a settled review cannot be honestly
re-issued (a new review row in the reviewer's name would forge their agency) — the full
reasoning, with the witnessed evidence, is the ADR-0014 consultation record at
[ORCH-ADR14-ORPHAN-DISPOSITION-CONSULT-2026-07-16.md](../../vestigial_documentation/design/ORCH-ADR14-ORPHAN-DISPOSITION-CONSULT-2026-07-16.md).

**Why does the harness insist closed and reviewed items stay correctable at all?**
Because the record model this project imports requires it, independent of anyone's
preference: [the safety-critical-logging BRIEF](../../law/briefs/safety-critical-logging/BRIEF.md)'s
invariant I3 (a correction is a new, linked entry that never obscures the prior state),
I7 (every discharged obligation carries the conditions under which it ceases to hold),
and the nuclear/aviation clusters' change-through-re-verification linkage (IEC 60880,
DO-178C) all demand that a close — and the reviews that discharged it — can be superseded
or lapse when their basis is defeated, append-only, with the defeat linked. The kernel
already delivers the core of this (superseding a close re-opens the item and re-surfaces
its review debt, witnessed in the consult above); s37's validity-bounded dispositions
extend the same discipline to violation answers themselves.

## Ledger-wide as-of read and inspection-copy export (`asof-export`)

This section covers `./asof-export`, the verb that reconstructs the whole ledger's in-force
reading at a past moment and can export that reading as a portable, hash-checkable copy; it
is written as full transcripts because the surface is new and unfamiliar. Ledger item
`asof-export-inspection-copy` (maintainer sign-off 2026-07-18, overnight batch item 1:
"the as-of is basically necessary — I thought that was done by like s5 or something, if we
don't have it then we need it"), merge `1449e0c`, delivery record: ledger row 1585.

**Can I see the whole ledger's in-force reading at some point in the past, not just work
items?** Yes — `./asof-export read --asof <ts>` prints every kind of row (decisions,
reviews, work items, obligations, everything), filtered to what was
[in force](../../GLOSSARY.md#supersession) as of that timestamp, not just the three `work_*`
kinds `led work asof <ts>` already covered. It generalizes `led work asof` by one query
shape (every row, not three kinds) rather than replacing it — `led work asof` stays the
right tool when you specifically want work-item state and its derived
open/claimed/closed view. WITNESSED, this checkout's own world, a real supersession pair
(row 1583 written 13:15:43, voided by row 1584 at 13:23:43) shown both-polarity — a moment
before the supersession still shows the superseded row in force, a moment after shows the
superseding row instead, same row count either side:
```
$ ./asof-export read --asof "2026-07-18 13:20:00" | grep -E "ledger id=158[34]|Row count"
Row count    : 1501
--- row 1501/1501 (ledger id=1583) ---
$ ./asof-export read --asof "2026-07-18 13:25:00" | grep -E "ledger id=158[34]|Row count"
Row count    : 1501
--- row 1501/1501 (ledger id=1584) ---
```
The as-of filter is the row's own `ts` (system insert time, never writer-supplied) — never
`event_declared_ts`, which is honest only as far as the declaring writer is honest. A bad
`--asof` value REFUSES loudly rather than returning an empty read, WITNESSED (exit 2):
```
$ ./asof-export read --asof bogus-not-a-timestamp
asof-export read: REFUSED -- as-of query failed: ERROR:  invalid input syntax for type timestamp with time zone: "bogus-not-a-timestamp"
LINE 5:   WHERE l.ts <= 'bogus-not-a-timestamp'::timestamptz
                        ^
```

**Can I get that same reading as a portable, checkable copy — for an inspector, an audit,
or just to keep?** Yes — `./asof-export export --asof <ts> --out <dir>` writes
`ledger-asof.txt` (human-readable, every column of every in-force row, in full),
`ledger-asof.json` (the same rows, machine-readable), and `manifest.sha256`, a standard
`sha256sum -c`-checkable manifest over the two. WITNESSED (scratch directory, not the
ledger — `export` is read-only against the ledger itself, its only writes are the three
named files under the `--out` directory you give it):
```
$ ./asof-export export --asof "2026-07-18 13:25:00" --out /tmp/asof-demo
asof-export export: wrote /tmp/asof-demo/ledger-asof.txt, /tmp/asof-demo/ledger-asof.json, /tmp/asof-demo/manifest.sha256 (1501 row(s) as of 2026-07-18 13:25:00).
  Verify with: (cd /tmp/asof-demo && sha256sum -c manifest.sha256)
  Signing is DEFERRED (standing maintainer crypto ruling) -- this manifest is an UNSIGNED sha256 content hash only. It lets a copy be checked against the bytes it left as; it proves neither who exported it nor that a differently-regenerated copy wasn't substituted for it. No inert --sign flag is offered by this verb.
$ (cd /tmp/asof-demo && sha256sum -c manifest.sha256)
ledger-asof.txt: OK
ledger-asof.json: OK
```
Re-running `export` at the same `--out` REFUSES rather than silently clobbering an existing
inspection copy — an evidentiary export is not overwritten by accident. WITNESSED:
```
$ ./asof-export export --asof "2026-07-18 13:25:00" --out /tmp/asof-demo
asof-export export: REFUSED -- 3 output file(s) already exist under /tmp/asof-demo: ['/tmp/asof-demo/ledger-asof.txt', '/tmp/asof-demo/ledger-asof.json', '/tmp/asof-demo/manifest.sha256']
  An inspection copy is not silently overwritten (ADR-0002). Pass --force to replace it deliberately, or choose a different --out.
$ echo $?
1
```
`--force` replaces it deliberately. The whole loop above ran against this checkout's own
live ledger and left `./led --recent 1` reporting the same leading row id (1592) before and
after every command shown — zero writes to the ledger from either subcommand.

**Is the manifest signed?** No, on purpose, and the verb says so out loud rather than
offering a flag that quietly does nothing. `manifest.sha256` is an unsigned content hash: it
proves a copy's bytes match what left this act; it proves neither who ran the export nor
that a differently-regenerated copy wasn't substituted for it later. Signing stays deferred
under the standing crypto ruling — no `--sign` flag exists at all (an inert flag that looked
armed but wasn't would be its own lie), and both the `.txt` and the `.json` name this limit
in their own header/`signing` field, so a reader of the inspection copy itself sees the same
honest boundary the CLI output does.

(2026-07-27 correction, root-shim-pruning residue sweep, ledger row 1357: every WITNESSED
transcript in this section cites merge `1449e0c`/row 1585 and real 2026-07-18 row ids/
timestamps (1583/1584/1592, 13:15:43-13:25:43) captured before the umbrella-CLI scaffold
migration, rows 1365/1366/1367, 2026-07-26, which retired the bare `./asof-export` shim these
transcripts typed — left as the dated record they are; the current equivalent invocation is
`./autoharn asof-export ...` for every command shown above.)

