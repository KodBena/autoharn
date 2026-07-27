# FABLE-S68-TYPED-ABSENCE-DISPOSITIONS-SPEC — the journaler's remaining implicit NULLs gain typed reasons

<!-- doc-attest-exempt: Fable-authored spec 2026-07-27, maintainer-ratified the same day
(verbatim: "As for the NUL sentinel, that shoulde be fixed" — answering the open question
ledger row 1541 parked, in the direction row 1542's audit item anticipates). The A:B:C loop
runs on the build, not the proposal text. Removal condition: superseded by the build's
merge record. -->
<!-- design-currency: status=discharged discharged-by=7451f63 depends-on=FABLE-S66-S67-JOURNAL-TOTALITY-SPEC.md -->

(Header corrected 2026-07-28, autoharn3 design-drift-triage sweep, ledger row 90:
`status=ratified` stood stale — the delta shipped and merged (`7451f63`, "review CLEARS
at strengthened tier"), and a follow-up merge (`8cb2b85`) even refreshed the Idris model
through it. Historical prose below kept verbatim.)

One kernel lineage delta, `kernel/lineage/s68-typed-absence-dispositions.sql`, extending
the s67 §2-AMENDMENT discipline (ADR-0012 P11: absence carries a typed reason; ADR-0008's
2026-07-27 twin: NULL is not a vocabulary member) to the two remaining implicit-sentinel
columns the amendment's item 4 named as a visible gap: `refusal_attempted_kind` (s65) and
`refusal_attempted_actor` (s43/s49). Enters the birth chain for the NEXT world
(runs-are-linear); no live world changes.

- **Status:** RATIFIED 2026-07-27 (maintainer, verbatim above; ledger rows 1541/1542 are
  the question this answers and the audit that will police the wider class).
- **Prior head (head-body rule):** `kernel.journal_write_refusal`'s current body is
  s67's re-issue (`kernel/lineage/s67-refusal-digest-bound.sql`); s68 cites it and
  carries its `-- prior-body-sha256`, computed by the builder against the merged main
  (`gates/lineage_reissue_lineage.py` enforces both checks). `compute_row_hash`'s head
  is likewise s67's (99 columns).

## 1. The witnessed shapes being retired (read the s67 head before designing)

From s67's journaler body, verbatim mechanics:

- **attempted kind**: one boolean collapse — `v_attempted_kind` is NULL when the payload's
  `kind` key is ABSENT, when it is NOT A STRING, or when it exceeds the 256-byte bound.
  Three different payload defects, one silent NULL.
- **attempted actor**: a two-stage resolution — the explicit payload actor when it
  resolves to a registered id (with s49's over-bigint guard), else the session role's
  standing-declaration default, else NULL. Today a POPULATED value does not even record
  which stage produced it: a payload's own claim and the session fallback are
  indistinguishable in the record, and the final NULL conflates "no resolvable claim AND
  no standing default" into an inference from a comment.
- **attempted role** (`refusal_attempted_role` = `session_user`): never NULL by
  construction — named here so the enumeration is visibly total, and deliberately given
  NO disposition column (a column that cannot be absent needs no absence reason; a
  vacuous disposition would fail the named-consumer test, row 1906).

## 2. The delta

1. **Two new columns**, both text, both kind-scoped to `write_refused` by the two-way
   kind-shape idiom (mandatory on `write_refused`, forbidden elsewhere — the
   `refusal_digest_disposition` twin s67 just shipped):
   - `refusal_attempted_kind_disposition`, closed vocabulary CHECK
     `('extracted','absent','not_a_string','over_bound')` — one member per witnessed
     branch of §1, extend ONLY by future delta. Consumer, named (row 1906): refusal
     forensics — a client bug omitting `kind` and an attacker shipping a 10-KiB `kind`
     are different events, and the row now says which happened.
   - `refusal_attempted_actor_disposition`, closed vocabulary CHECK
     `('resolved_explicit','resolved_session_default','unresolvable')`. Consumer, named:
     the same forensics — a populated attempted-actor now records WHOSE claim it is
     (the payload's own, or the session's standing default), which the 2026-07-26
     principal-stamps work already treats as a load-bearing distinction.
2. **Coupling CHECKs, kind-guarded** — use the s44 `attest_verdict` idiom EXACTLY as the
   s67 fix round transcribed it, NOT a bare biconditional: the s67 build witnessed live
   that the bare form `(a) = (b)` is NULL-satisfied on every non-`write_refused` row
   (three-valued logic) and closes nothing there. Table-level:
   - `CHECK (kind <> 'write_refused' OR ((refusal_attempted_kind IS NULL) = (refusal_attempted_kind_disposition <> 'extracted')))`
   - `CHECK (kind <> 'write_refused' OR ((refusal_attempted_actor IS NULL) = (refusal_attempted_actor_disposition = 'unresolvable')))`
   The existing one-way kind-shape CHECKs on the two carried columns stay UNTOUCHED
   (the s67 fix round's retained-sibling precedent: dropping them reopens the
   off-kind hazard the coupling alone does not close).
3. **`kernel.journal_write_refusal` re-issued** (citing s67, prior-body-sha256): each
   disposition is assigned IN THE SAME branch that assigns (or NULLs) its column — the
   kind extraction's single IF splits into the three witnessed failure arms; the actor
   resolution records which stage won. One writer, one home (amendment item 3's rule);
   every other line byte-identical, including s66's stamp branch, the oracle bump, and
   the s67 digest/disposition block.
4. **`compute_row_hash` re-issued** to 101 columns under the s42 law;
   `gates/hash_coverage_gate.py`, `gates/kind_shape_manifest_gate.py` (two new MANIFEST
   rows + two CROSS_COLUMN_COUPLING_MANIFEST rows), `gates/kernel_function_census.py`
   bank, and the fixture family extended in the same commit.
5. **Per-column, not consolidated** (the amendment left this open): a single
   consolidated disposition would itself be a fuzzy vocabulary spanning two value
   domains (ADR-0008's positive register — refuse the inadequate shared bucket), and
   the two columns' absence causes share no member.

## 3. Witness plan (scratch, both polarities, red first)

RED (pre-delta baseline): a refused payload with no `kind` key, one with a non-string
`kind`, one with an over-256-byte `kind`, one with an unresolvable actor — each journals
today with the bare NULLs (witness the conflation). GREEN (post-delta, same probes):
each journals with its exact disposition member; an ordinary refusal (extractable kind,
explicit resolving actor) carries `('extracted','resolved_explicit')` and is otherwise
byte-identical; a session-default resolution carries `'resolved_session_default'`;
direct INSERTs violating each coupling CHECK refuse naming the constraint; an off-kind
row carrying either disposition refuses (kind-shape); the retained one-way CHECKs
witnessed still load-bearing (the s67 fix-round leg, repeated). Chain: full newborn
birth through s68; `./judge` AGREE; `verify-chain` INTACT with the refusal oracle
reconciling; all lineage/hash/kind-shape/census gates clean, banks updated same commit.
Autoharn.idr: if the model refresh (in flight this same day) has merged by build time,
extend its AS-OF to s68 or leave the LAGGING suffix honestly in place — state which.

## 4. Closure statement (ADR-0000 Rule 2(a))

Quantification universe: the nullable self-describing columns of the `write_refused`
row shape as of s67 — `refusal_attempted_kind` (dispositioned HERE),
`refusal_attempted_actor` (dispositioned HERE), `refusal_attempted_role` (never NULL by
construction, no disposition, stated in §1), `refusal_payload_digest` (already
dispositioned by s67), `refusal_sqlstate`/`refusal_message`/`refusal_surface`
(mandatory-populated by the journaler's own INSERT, absence unrepresentable on the
happy path). Not covered, stated honestly: every OTHER implicit-NULL in kernel and
service code is ledger row 1542's audit, not this delta; live worlds keep the s67
shape until their next birth (runs-are-linear).

## License

Public Domain (The Unlicense).
