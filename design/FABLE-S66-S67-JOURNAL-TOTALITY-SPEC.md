# FABLE-S66-S67-JOURNAL-TOTALITY-SPEC — the refusal journal survives a forged stamp, and bounds what it digests

<!-- doc-attest-exempt: Fable-authored spec 2026-07-27, maintainer-ratified the same day
(row 1519's fix: "it's yes of course"; row 1514's items: "The ratified-but-not-yet-built
all should go in"). The A:B:C loop runs on the build, not the proposal text. Removal
condition: superseded by the build's merge record. -->
<!-- design-currency: status=ratified depends-on=FABLE-S65-REFUSAL-ATTEMPTED-KIND-SPEC.md -->

Two kernel lineage deltas, both members of the s49 totality family: the refusal journal
must record refusals under hostile conditions, because the refusal path is exactly where
hostile input arrives (the s65 lesson, restated once more). Both enter the birth chain
for the NEXT world (runs-are-linear); no live world changes.

- **Status:** RATIFIED 2026-07-27 (maintainer, verbatim: row 1519's fix "yes of course";
  the row-1514 ratified items "all should go in"). Ledger rows 1514/1519 are the basis;
  this spec is their build form.
- **Prior heads (head-body rule):** `kernel.set_stamp`'s current body is
  [`s23-per-invocation-stamp-token.sql`](../kernel/lineage/s23-per-invocation-stamp-token.sql)'s
  re-issue; `kernel.journal_write_refusal`'s is
  [`s65-refusal-attempted-kind.sql`](../kernel/lineage/s65-refusal-attempted-kind.sql)'s.
  Each re-issue cites its true immediately-prior file and carries `-- prior-body-sha256`
  (the s63 false-stale-base lesson; `gates/lineage_reissue_lineage.py` enforces both
  checks).

## 1. s66 — a forged-but-complete stamp draws a typed refusal, journaled (row 1519)

**The witnessed gap (fixture w36f, ledger row 1519):** a structurally-valid but
cryptographically-wrong vendor HMAC currently surfaces to the caller as a 500
`unclassified_failure` — a genuine uncaught kernel exception — instead of a typed
`refused` verdict with a journaled `write_refused` row.

**Diagnosis, stated as a HYPOTHESIS the builder witnesses BEFORE fixing:** s17's
`set_stamp` raises with no `ERRCODE`, so its SQLSTATE is P0001 — which IS inside s43's
caught class (`P0%`). The escape is therefore NOT a missing SQLSTATE class (round 1's
disclosure guessed wrong there): the likely mechanism is that `journal_write_refusal`'s
own INSERT into the ledger fires `set_stamp` AGAIN on the same session — the forged
GUCs are still set — so the journaler itself raises, and THAT second exception escapes
the `BEGIN..EXCEPTION` block mid-handler. The builder reproduces this on scratch first
(witness the double-raise, e.g. via the exception context/stack or a targeted probe)
and reports the ACTUAL mechanism; if it differs from this hypothesis, the fix below is
re-derived from the witnessed mechanism and the divergence is surfaced, not silently
absorbed.

**The delta (one file, `kernel/lineage/s66-forged-stamp-journal-totality.sql`):**

1. **`kernel.set_stamp` re-issued** (citing s23, prior-body-sha256): the
   forged-complete-stamp branch gains ONE guard — when the row being inserted is the
   journaler's own `write_refused` row, a forged-complete stamp records
   `stamp_verified := false` instead of raising (the refusal record must land; a
   journal row is not authority-bearing, and s21's NULL-never-distinct discipline
   already makes an unverified stamp claim-inert). Every other kind's behavior is
   BYTE-IDENTICAL, including the raise text. Nothing about verification, the HMAC, or
   the stamp columns changes.
2. **No change to `ledger_write` or its siblings:** once the journal INSERT survives,
   s43's existing `P0%` catch does the rest — the forged-stamp refusal journals (with
   s65's `refusal_attempted_kind` extracted as for any refusal) and returns a typed
   `refused` verdict. If the witnessed mechanism shows this is insufficient, the
   builder stops and reports rather than widening the caught-class set on their own
   authority (widening what 40/53/57/XX re-raise means is NOT in this ratification).
3. **Effect, stated plainly:** a forged writer's attempted row is still refused —
   nothing lands for them, nothing is newly permitted — but the refusal is now
   RECORDED (one more journaled refusal, the s49 direction exactly) and the caller
   sees the typed verdict instead of a 500.

## 2. s67 — the journaler's payload digest is bounded (row 1514 item 1)

`journal_write_refusal` digests the refused payload whole, whatever its size. The
service caps write bodies at 1 MiB (`MAX_WRITE_BODY_BYTES`), but direct psql callers
bypass the service entirely — the kernel journaler is the only backstop on that path,
and today it has none.

**The delta (one file, `kernel/lineage/s67-refusal-digest-bound.sql`):**
`kernel.journal_write_refusal` re-issued (citing s66's re-issue — these two deltas
sequence s66-then-s67, so s67's citation target is s66 if s66 touches the journaler,
else s65; the builder states which and the gate checks it): when
`octet_length(p_payload::text)` exceeds **1,048,576 bytes** (the s51
`artifact_too_large` precedent, and the same figure the service already enforces),
`refusal_payload_digest` is recorded NULL — the same "not extractable" meaning s65
gave `refusal_attempted_kind` beyond its own bound — and the refusal journals exactly
as before in every other respect. The digest is a grep handle, never a join key (the
row-1498 witness: joins anchor on `refusal_id`); losing it beyond the bound costs an
attacker-sized payload its vanity hash, nothing else. Below the bound, byte-identical.

### §2 AMENDMENT 2026-07-27 — NULL may not carry the meaning (maintainer ruling at merge-hold)

The maintainer, reviewing the built delta's one-way CHECK widening, ruled (near-verbatim):
NULL as an implicit sentinel/meaning-carrier is not condonable here regardless of the
no-consumer argument — it is a drift hazard. This lands squarely on the house's own law
(ADR-0000's unrepresentable-illegal-states; the standing no-bare-types rule, autoharn2
row 1105): the reason for an absence must be a representable, typed value, never an
inference from a comment. s67 is therefore re-shaped:

1. **One new column**: `refusal_digest_disposition text`, kind-scoped to `write_refused`
   by the house two-way kind-shape idiom, closed vocabulary CHECK
   (`'computed'`, `'payload_over_bound'`) — extend ONLY by future delta.
2. **The coupling CHECK, two-way, table-level**:
   `(refusal_digest_disposition = 'computed') = (refusal_payload_digest IS NOT NULL)`.
   This RESTORES a two-way table constraint (the original widening dissolves): a digest
   NULL row must declare `payload_over_bound`; a populated digest must declare
   `computed`. An accidental future re-issue that drops the digest computation without
   also declaring the disposition is table-caught — the realistic bug the maintainer's
   drift concern names. (A deliberately lying re-issue can still lie in lockstep; that
   is function-trust for TRUTHFULNESS, which no self-reported column escapes and which
   the old presence-only CHECK never provided either — stated, not hidden.)
3. `compute_row_hash` re-issued for the new column under the s42 law;
   `gates/hash_coverage_gate.py`, kind-shape manifest, and the fixture family extended
   accordingly. `journal_write_refusal` writes the disposition in the same statement
   that writes (or NULLs) the digest — one writer, one home.
4. **Precedent columns flagged, not touched:** `refusal_attempted_kind` (s65) and the
   s43/s49 attempted-actor NULLs carry the SAME implicit-sentinel shape this ruling
   condemns. Whether the ruling extends to them (a disposition column each, or a
   consolidated one) is a separate maintainer decision, named here so it is a visible
   gap (ADR-0008 Rule 3), not silently absorbed.

Both deltas are the s49 class — totalizing the refusal journaler, more refusals
recorded, nothing newly permitted, no existing CHECK relaxed — and s49 shipped as
fail-safe-additive. But the class rule is not leaned on here: the maintainer ratified
both changes specifically (rows 1514/1519 and his 2026-07-27 words quoted in the
header), so the routing question is already answered by his own act. s66 does alter
one branch of an existing trigger's behavior (write_refused rows only); that is
exactly why it ships under this explicit ratification rather than the class.

## 4. Witness plan (scratch, both polarities, red first)

RED (pre-delta baseline re-witnessed): forged-complete stamp through the boundary →
the current escape shape (500/exit-3, no journal row) — the w36f observation
reproduced, plus the diagnosis witness of §1. A >1 MiB refused payload journals today
with a full digest (the unbounded baseline). GREEN (post-delta): forged-complete stamp
→ typed `refused` verdict, `write_refused` row journaled with `stamp_verified=false`
and `refusal_attempted_kind` populated; the attempted row itself absent; an ordinary
valid-stamp write byte-identical pre/post; an ordinary forged-stamp-with-missing-GUC
(unstamped) write byte-identical pre/post; >1 MiB refused payload journals with digest
NULL, refusal recorded; ≤1 MiB payload digest byte-identical pre/post. Chain: full
newborn birth through s67; `./judge` AGREE; `verify-chain` INTACT with the refusal
oracle reconciling; `gates/hash_coverage_gate.py`, `gates/lineage_reissue_lineage.py`,
`gates/kernel_function_census.py` (bank updated same commit),
`gates/kind_shape_manifest_gate.py` (CHAIN extended through s67) all clean.
seen-red/boundary-service W36f is left UNTOUCHED (it witnesses the LIVE world's s43
shape, which does not change — runs are linear); the builder adds the new-shape
witness to the delta's own fixture family instead, and states this split explicitly.

## 5. Closure statement

Quantification universe, per
[ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md) Rule 2(a):
the write paths that can meet a forged-complete stamp are exactly the INSERTs on the
ledger table (single table, single trigger — `set_stamp` fires on all of them), split
into (a) caller-attempted rows via the six s43-family boundary functions, refused as
before, and (b) the journaler's own `write_refused` rows, the one branch s66 changes.
The payloads s67 bounds are exactly those reaching `journal_write_refusal` — every
boundary function's refusal leg, enumerated by grep in the build report. Not covered,
stated honestly: live worlds keep the old shape until the next birth (runs-are-linear);
refusals that never reach the kernel journal nothing, before and after; the
forged-stamp 500 remains the LIVE deployment's behavior and the service's w36f fixture
still witnesses it there.

## License

Public Domain (The Unlicense).
