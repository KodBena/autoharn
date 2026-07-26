# FABLE-S63-SUPERSESSION-BODY-RESTORATION-SPEC — restore the four refusal branches s61 silently dropped

<!-- doc-attest-exempt: Fable-authored spec 2026-07-26, awaiting maintainer ratification of
the routing question in §5; the delta is built and scratch-witnessed on a branch but does
not enter the birth chain until that answer. Removal condition: superseded by the merge
record of the s63 delta. -->

- **Status:** AUTHORED. The delta may be built and scratch-witnessed immediately; MERGE to
  `kernel/lineage/` waits on the maintainer's §5 answer.
- **Basis:** ledger row 1430 (the witnessed finding), row 1429 (the sweep that surfaced
  it via `belief-substrate-v2` `NEG-cross-principal-supersession-refused`), and the
  investigation transcript (scratch world `s61probe1`, bisect-by-function-swap closing on
  s61 Element 7).

## 1. Defect being repaired

`kernel/lineage/s61-signature-symmetry-and-key-binding.sql` Element 7 re-issued
`validate_supersession_target` claiming "Base body = s45's (UNCHANGED by s60)". The claim
was stale by two re-issues: s53 had added the belief branch and s58 Element 5 (its
explicitly-marked FOURTH re-issue) had re-issued the body with the belief branch plus
three missive branches. s61's `CREATE OR REPLACE` therefore silently DELETED four refusal
branches while adding its (correct, wanted) symmetry block. At current head, every
newborn world accepts:

1. supersession of a `belief` by a different principal, or by a row of a different kind
   (the s53 §3.3 holder-only self-revision discipline — live-witnessed relaxed);
2. supersession of `missive_sent` by anything other than a same-thread successor;
3. supersession of `missive_received` at all (was unconditionally refused — receipts
   were unretractable history);
4. supersession of `missive_disposed` by a different-kind or different-regards row.

Legs 2–4 are established textually (the branches are absent from the deployed body);
leg 1 is live-witnessed both polarities (accepted at head; refused byte-identically with
s58's body swapped in).

## 2. The delta (s63, one file, one function re-issue)

`kernel/lineage/s63-supersession-body-restoration.sql` re-issues
`validate_supersession_target` with the UNION body: s58 Element 5's four branches
restored VERBATIM (byte-diffed against `s58-missive-substrate.sql:783-867`, not retyped)
plus s61's symmetry block retained VERBATIM (byte-diffed against
`s61-signature-symmetry-and-key-binding.sql` Element 7's addition). The file's header
states, per the head-body rule: the immediately-prior re-issue is s61 Element 7, the
prior-prior is s58 Element 5, and this delta exists because s61's base claim was false.
No other semantics change; no other function is touched. The ASP twin gains (or is
confirmed to already carry) the corresponding four refusal rules in its stratified
closure; the builder must reconcile WHY the SQL/ASP differential did not flag the drift
at s61 time (either the twin dropped the rules in the same act, or the differential's
probe corpus never exercised these branches — whichever it is, state it in the build
report; if it is a probe-coverage gap, file it, do not silently widen scope).

## 3. Mechanical guard against recurrence (generic, non-kernel, ships with the delta)

A new gate `gates/lineage_reissue_lineage.py`: for every function name defined more than
once across `kernel/lineage/s[0-9]*-*.sql` (in numeric order), each later re-issue must
name the file of the immediately-prior re-issue in its header comment. Anchored
whole-line regex, same idiom as `gates/lineage_chain_coverage.py`. This makes the false
"base = s45" claim class mechanically impossible to repeat: a re-issue citing a stale
base fails the gate because the cited file is not the actual prior definer. s61's own
header is grandfathered by an explicit dated waiver entry inside the gate (the defect is
already on the record as row 1430; rewriting frozen history is not the remedy).

## 4. Witness plan (scratch, both polarities, red first)

RED (post-delta): cross-principal belief supersession refused with the s58 byte-identical
message; cross-kind belief supersession refused; each missive leg refused where
exercisable — the builder attempts to seed `kernel.world_identity` on the scratch world
to unblock missive writes; any leg still blocked is reported UNEXERCISED with the
concrete blocker, never claimed.
GREEN (post-delta): ordinary same-holder belief self-revision accepted; the s61 symmetry
refusal still fires (its block survived the union); the `belief-substrate-v2` fixture
family goes GREEN end-to-end; a full newborn witness through the generated chain
s20..s63 births clean. SQL/ASP differential in AGREE via `./judge`.

## 5. Routing question for the maintainer (the one yes/no this spec needs)

The delta strictly ADDS refusals relative to current head — read literally, it rides the
class-ratified fail-safe-additive family and enters the birth chain without a per-delta
question. But the refusals it adds were DROPPED by an unratified accident, and the class
ruling says doubt about which side a delta falls on IS the routing. Question: **may s63
enter the birth chain under the fail-safe-additive class (yes), or does restoration of
accidentally-dropped semantics need your per-delta ratification (no → ratify this spec
explicitly)?** Either answer unblocks the merge; the build and witness happen before the
answer either way.

## 6. Closure statement

Quantification universe, per ADR-0000 Rule 2(a): the four branches enumerated in §1 are
exactly the refusal branches present in s58 Element 5's body and absent from s61
Element 7's body — the universe is the byte-diff of those two function bodies, closed by
construction. §3's gate quantifies over all multiply-defined function names in the
lineage glob, closure checked by the gate's own census output. Nothing beyond
`validate_supersession_target` and the new gate is claimed.

## License

Public Domain (The Unlicense).
