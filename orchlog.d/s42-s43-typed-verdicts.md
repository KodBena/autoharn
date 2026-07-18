subject: 1fc4e8c
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

s42 (`1fc4e8c`) and s43 (`84729de`) landed, plus a corrections commit (`59da06d`). Together they
are the biggest operator-visible change the kernel has had: **a refused write is no longer a
transaction that vanishes** — it is a committed, attributed, chained ledger row you can read.
Full spec: [design/FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md](../design/FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md)
(§0 has the executive summary); orchestrator-verified delivery record: ledger row 1476.

**Read this before assuming your world has any of it: EXISTING worlds gain NOTHING here.** Runs
are strictly linear — s42/s43 apply only at a *future* world's birth. A world scaffolded before
these commits keeps its old thirty-column hash chain and its raw-INSERT write path forever;
nothing here is retrofitted onto it.

**What a refused write looks like now.** Before this delta, every kernel policy refusal was a
`RAISE EXCEPTION` that aborted the transaction — the attempt itself left no trace anywhere but a
server log. After s43, the granted role holds NO INSERT privilege on any kernel-governed table;
four SECURITY DEFINER functions (`kernel.ledger_write`, `review_write`, `registration_write`,
`obligation_write`) are the only write path, and a refusal caught inside one of them is committed
as an ordinary `write_refused` ledger row and returned to the caller as a typed verdict —
never an abort. Witnessed (`seen-red/s43-typed-verdict-write-boundary/red.txt`, case 1): a write
attempted under a revoked principal returns

```
disposition=refused, sqlstate=P0001, refusal_id=<row id>
message: "Ledger policy: strict attribution (s40) — actor principal N is revoked ..."
```

and the ledger holds a COMMITTED `write_refused` row carrying `refusal_sqlstate=P0001`,
`refusal_surface='ledger'`, `refusal_attempted_actor=<the revoked principal's id>`,
`refusal_attempted_role='bork'` (session_user, server-witnessed — never client-asserted),
`actor=<the write-boundary tool principal>` (never the attempted actor — a refused principal
cannot honestly author the record of its own refusal), and a 64-hex `refusal_payload_digest`
(SHA-256 of the attempted payload, digest only — the payload's content is never stored
verbatim, R4 ratified). The refused row itself never lands. **Probing attempts now leave
traces**: an agent (or a person) trying a write it isn't permitted to make no longer disappears
into a rolled-back transaction — it becomes a permanent, attributed, countersignable row on the
record, same as everything else the kernel keeps.

**Raw INSERT is structurally dead.** After s43, a raw `INSERT` on `ledger` (or `review_detail`,
`kernel.principal`, `countersign_obligation`) from the granted role fails at the privilege layer
(`permission denied for table ledger`, SQLSTATE 42501) before any kernel semantics run at all —
there is no bypass path left to accidentally take. That specific refusal class is NOT
kernel-journaled (its residual home is the server log, named composition rather than a
discovered gap) — the journal only covers attempts that reach the boundary functions and get
refused there.

**`./verify-chain`'s new legs.** Three additions, all exercised in this delta's own harness:

1. **Full-column coverage.** `compute_row_hash` (the one function the tamper-evidence chain
   rests on) now serializes every ledger column except `row_hash` itself — 52 at the s42 head,
   58 once s43's six new `write_refused` columns land — instead of the thirty columns it covered
   before. Before this fix, a schema-owner tamper of any column added since s28 (work-tree
   parentage, violation dispositions, all twelve principal-identity columns) changed no hash and
   `./verify-chain` reported `INTACT` over the rewrite (witnessed live,
   `seen-red/s42-row-hash-full-coverage/red.txt` case 1). After the fix, tampering any one of
   the 52 serialized columns is caught (witnessed per-column, all 52, case 2):
   ```
   verify-chain: BROKEN -- first break at row id 19:
       stored:   <64-hex, the pre-tamper hash>
       expected: <64-hex, recomputed over the tampered content>
     (1 of 20 row(s) mismatch total. ...)
   (exit 1)
   ```
2. **The refusal_seq reconciliation.** A non-transactional sequence, `kernel.refusal_seq`, is
   bumped immediately before every `write_refused` row is journaled — `nextval` survives
   rollback, so it counts every refusal attempt regardless of what happens to the surrounding
   transaction. `./verify-chain` now compares the count of committed `write_refused` rows
   against this sequence. `sequence > count` is EXPLAIN-grade (named legitimate causes: a
   client-side rollback around the boundary function, or a journal-insert double failure) —
   not a failure. `count > sequence` can never happen through the sanctioned path; if it does,
   it means rows exist that the counting mechanism never saw — see forgery-suspect below.
3. **Forgery-suspect.** Only the boundary functions may mint a `write_refused` row through the
   sanctioned path; a payload naming `kind = 'write_refused'` directly is refused with a
   forgery-channel teach-text. If a schema owner forges one anyway (bypassing the boundary
   entirely), `./verify-chain` reports it (witnessed,
   `seen-red/s43-typed-verdict-write-boundary/red.txt` case 3):
   ```
   verify-chain: REFUSAL-ORACLE-FORGERY-SUSPECT -- N journaled write_refused row(s) but
   the sequence only counted N-1 ... (exit 6; --head REFUSES)
   ```
   `write_refused` rows are also unretractable by rule (R6, ratified): no row may supersede one,
   enforced both by a same-row CHECK and (the letter/spirit correction in amendment B2) a
   cross-row trigger that refuses any row whose `supersedes` NAMES a `write_refused` row.

**The hash-coverage gate's teach-rule for future deltas.** `gates/hash_coverage_gate.py` (new in
this same commit) derives both sides mechanically — never a hand-kept list: the ledger's live
column set from `information_schema.columns` on a scratch apply of the full birth chain, and the
columns `compute_row_hash` actually serializes, read straight from the function's own source. Any
future delta that adds a ledger column without re-issuing `compute_row_hash` in the same delta
turns this gate red, naming the missing column by name — the exact silent drift that happened
thirteen times running (s28 through s41) before this gate existed (ledger row 1449 named the
hazard; the gate is the fix that ships in the same commit, per ADR-0011's "the mechanism ships
with the first fix" rule). s43 itself is the gate's first live exercise: it adds six columns and
re-issues the serializer to 58 in the same commit, witnessed red on a scratch schema that skipped
the re-issue and green on the real s43 head.

**Honest limits, from the deltas' own LIMITS blocks — read before relying on any of this
operationally.**

- A database superuser or schema owner can always bypass every trigger and privilege check here;
  the closing move against that adversary remains the externally-held GPG-signed chain head
  (`verify-chain --head`), unchanged by this delta.
- Privilege-layer refusals (raw INSERT denied, SQLSTATE 42501) are NOT kernel-journaled — their
  residual home is the server log, which rotates. Named composition, not a gap discovered later.
- The refusal-payload digest is deterministic on a given Postgres server but not guaranteed
  stable across a major-version change — a digest recomputed from a re-supplied payload on a
  different server could differ. This does not break the chain (the digest is content, hashed
  once at write time); it only means the digest is not a portable verification path across
  server versions.
- Refused-payload *content* is never reconstructable from the ledger — digest only, by design
  (R4, ratified, poison/privacy). Forensic recovery of what was actually attempted needs the
  server log, within its retention window.
- Suspending or revoking the `write-boundary` principal (the one that authors every refusal row)
  bricks refusal recording entirely. Guarded only at the CLI (`led principal suspend|revoke
  write-boundary` is itself refused with teach-text) — an owner-side direct path could still do
  it; disclosed, not fixed.
- In a solo-operator world, the entire refusal record is written by machinery that one operator
  controls — complete and attributed, but not adversarially independent (the same honesty s17's
  stamp mechanism already carries).
- Sibling tables (`review_detail`, `countersign_obligation`, `kernel.principal`,
  `chain_high_water`) have no hash chain of their own, before or after this delta — s42 widens
  only the ledger's own chain (R3, ratified as a deferred follow-on family, not smuggled in
  here).

**Runs are strictly linear, restated because it matters most here.** Both deltas are authored and
scratch-witnessed only — this delivery does not, and structurally cannot, apply either one to any
existing world. They reach reality only at a future world's birth, wired into
`bootstrap/new-project.sh`'s lineage chain in the same commits. If your world predates
`1fc4e8c`/`84729de`, none of the above is available to you; `./migrate --dry-run` will name s42
and s43 among the missing deltas.

Migration: the usual recipe — end the session, maintainer pulls the checkout, runs `./migrate`
against a *future* world only (never an existing one), restart, `./pickup`.
