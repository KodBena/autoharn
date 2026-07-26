# FABLE-S63-SUPERSESSION-BODY-RESTORATION-SPEC — restore the four refusal branches s61 silently dropped

<!-- doc-attest-exempt: Fable-authored spec 2026-07-26; §5 routing resolved same day
(rides the fail-safe-additive class, maintainer-delegated call, ledger row 1434); the
delta merges once witnessed both polarities with AGREE and reviewed at the strengthened
tier. Removal condition: superseded by the merge record of the s63 delta. -->

- **Status:** ROUTING RESOLVED (§5, 2026-07-26): s63 rides the fail-safe-additive class.
  The merge is unblocked once the build lands witnessed both polarities with AGREE and
  passes its strengthened-tier fresh-context review.
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

**Reconciliation answer (build finding, ledger row 1435; independently re-derived by the
fresh-context review — the two analyses match):** NEITHER disjunct. The differential is
blind to this defect class BY CONSTRUCTION: the ASP twin derives `superseded/1` from
already-accepted `supersedes` facts and has no INSERT-time concept, while per-kind
supersession REFUSAL logic lives only in the SQL write trigger — a refused write never
becomes a row, so it never reaches the EDB the differential compares. No corpus of
accepted-row scenarios could expose a dropped write refusal. Consequence, stated as an
honest limit: the differential's guarantee perimeter EXCLUDES write-boundary refusal
drift and always has; the §3 gate and the body-census instrument (ledger row 1433,
Tier A) are the coverage for that perimeter. This paragraph is the committed home of
the answer the spec demanded in the build report.

## 3. Mechanical guard against recurrence (generic, non-kernel, ships with the delta)

A new gate `gates/lineage_reissue_lineage.py`, two mechanical checks per re-issued
function name across `kernel/lineage/s[0-9]*-*.sql` (numeric order):

1. **Citation:** each later re-issue must name the file of the immediately-prior
   re-issue in its header comment. Anchored whole-line regex, same idiom as
   `gates/lineage_chain_coverage.py`.
2. **Prior-body hash binding (amendment, maintainer-approved 2026-07-26):** each
   re-issue must carry a `-- prior-body-sha256: <hex> (<file>)` line; the gate extracts
   the prior definer's `CREATE OR REPLACE FUNCTION <name> ... $$...$$;` statement text
   from the cited file and recomputes the hash. A stale base is then unrepresentable,
   not merely un-citable: s61's "base = s45" would have failed because the hash of
   s45's body is not the hash of s58's. The extraction is mechanical (anchored on the
   function name and dollar-quote delimiters); a file the extractor cannot parse is a
   gate FAILURE, never a skip.

s61's own header is grandfathered by an explicit dated waiver entry inside the gate for
BOTH checks (the defect is already on the record as row 1430; rewriting frozen history
is not the remedy). s63 itself is the first conforming instance: it cites s61 Element 7
and embeds the hash of s61's deployed body — the base it textually replaces — while the
restored branches are byte-diffed from s58 per §2.

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

## 5. Routing — RESOLVED 2026-07-26 (maintainer delegated the call to Fable's recommendation)

The fail-safe-additive class is the maintainer ruling of 2026-07-09 in
[CLAUDE.md](../CLAUDE.md) ("Class-ratified fail-safe deltas"): a kernel lineage delta
that only ADDS refusals, vocabulary, or derived views — nothing existing relaxed, no
existing semantics changed — witnessed on a scratch schema on both polarities with the
SQL/ASP differential in AGREE, is pre-ratified as a class and enters the birth chain
without a per-delta question; doubt about which side a delta falls on IS the routing.

The doubt here: s63 strictly adds refusals relative to head (letter satisfied), but
those refusals exist because s61 dropped them by an unratified accident — a
correction-of-accident shape the 2026-07-09 ruling never contemplated. Asked; the
maintainer delegated the call. **Resolution: s63 rides the class**, on the reasoning
that it permits nothing new (it returns the kernel to what s53/s58 already ratified)
and the class reserves maintainer attention for new permissions. Precedent cabined:
restoration rides the class only when the drop itself is on the record as an accident
(here, row 1430); a contested drop's "restoration" does not inherit this path.

### FYI — the doctrine behind the question (archaeology note, maintainer-requested 2026-07-26)

Why this was a question at all, when "re-add the accidentally-deleted refusals" reads
as obvious: the shape has legalistic prior art, and the doctrine is what made the
routing non-trivial.

- **Casus omissus** (a case the rule's author never contemplated): the 2026-07-09
  ruling classifies deltas by what they DO (add vs relax), silently assuming the head
  they act on is itself ratified. s61 broke that assumption, so s63 fell outside the
  ruling's contemplated universe — and the ruling's own doubt clause ("doubt about
  which side IS the routing: ask") functions as what courts call a certified question:
  the interpreter refers the unprovided-for case to the rule's author rather than
  extending the rule by analogy on their own authority.
- **Revival of repealed law**: real legal systems faced exactly this. At common law,
  repealing a repealing statute automatically revived the original; modern
  interpretation acts reversed that default — nothing revives without EXPRESS
  re-enactment. This kernel is structurally on the modern side, by construction rather
  than by choice: lineage files are frozen history and worlds are born, not patched
  (runs-are-linear ruling, 2026-07-11), so there is no mechanism by which declaring
  s61's re-issue defective could void it retroactively and "revive" s58's body.
  Restoration MUST be a new forward delta — an express re-enactment — and the open
  question was only how that re-enactment classifies.
- **The cabining** is ordinary precedent hygiene (holding limited to its facts): the
  resolution's ratio is "restoration of an ON-THE-RECORD-accidental drop permits
  nothing new," not "anything labeled restoration rides the class." A future contested
  drop is distinguishable on exactly that fact and routes per-delta.

These are analogies, not citations of project law; the in-project prior art proper is
the 2026-07-09 ruling's own s21/s22 note (asked-then-classed) and its doubt clause,
which this section is now the second recorded exercise of.

## 6. Closure statement

Quantification universe, per ADR-0000 Rule 2(a): the four branches enumerated in §1 are
exactly the refusal branches present in s58 Element 5's body and absent from s61
Element 7's body — the universe is the byte-diff of those two function bodies, closed by
construction. §3's gate quantifies over all multiply-defined function names in the
lineage glob, closure checked by the gate's own census output. Nothing beyond
`validate_supersession_target` and the new gate is claimed.

## License

Public Domain (The Unlicense).
