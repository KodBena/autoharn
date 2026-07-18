# Idris model refinement consultation — record (2026-07-15, late night)

Point-in-time consultation record, banked verbatim below the rule. Provenance: a fourth
fresh-context Fable-eyes pass, commissioned by the maintainer on his own hunch that
[Autoharn.idr](../../design/Autoharn.idr) could be stricter/more polymorphic and that a refined model
might lower back into a cleaner implementation; the categorical consult was supplied as
context WITH NO WEIGHT per his instruction. All refinement fragments were machine-checked
(Idris 2 v0.7.0, %default total): [RefKernel.idr](../../design/RefKernel.idr) (R1-R9 + Refl semantic
witnesses) and [RefUniverse.idr](../../design/RefUniverse.idr) (kind-universe pattern), banked beside
this record. Verdict: REFINE-AND-LOWER, weight on refining the model; the implementation's
own same-day trajectory (s31 + three gates) had already absorbed most of the lowering.

---

All evidence is in. The lowering landscape check shows `gates/kind_shape_manifest_gate.py`, `gates/column_complete_gate.py`, and `gates/ledger_reader_allowlist.py` already landed today — several candidate lowering channels are pre-occupied by shipped mechanisms. The report follows.

---

# Fresh-context review: can Autoharn.idr be refined, and does a refined model lower?

**Checked artifacts** (all elaborate under `%default total`, Idris 2 v0.7.0, zero errors/warnings, fresh build):
- Baseline re-witnessed: `/home/bork/w/vdc/1/autoharn/design/Autoharn.idr` checks clean (copied and re-run).
- `/tmp/claude-1000/-home-bork-w-vdc-1-autoharn/a857c93d-d154-4d01-b726-122ec07401fc/scratchpad/refine/RefKernel.idr` (520 lines) — refinements R1–R9, with green fixtures, `failing`-block red polarities, and **Refl semantic witnesses** (readers evaluated at compile time on concrete worlds).
- `.../scratchpad/refine/RefUniverse.idr` (166 lines) — the universe/description pattern for the kind family.

## Q1 — Is the model amenable to refinement? YES, materially — and the maintainer's hunch about tackiness is correct in specific, nameable places.

**Finding 0 (fidelity, the most important thing I found — CHECKED).** The shipped model is **one delta stale**. Its §4 deliberately transcribes the raw-read "blind spot" ("the s29 `closes` CTE's supersession-BLINDNESS ... the named blind spot of composite-spec §3b") — but `kernel/lineage/s31-supersession-uniform-retraction.sql` (ratified 2026-07-15, in lineage) re-issued exactly those `edges`/`closes` CTEs to read `ledger_current`. The blind spot the model preserves as "the finding" is no longer the substrate's behavior. RefKernel R7 renders the s31 semantics and proves the divergence at elaboration time: on a world where a deferred close is retracted, `hasCloseRaw = True` while `hasCloseCur = False` (fixtures r7b1/r7b2, Refl). Any refinement pass should start here; polishing anything else first would beautify a stale transcription.

**R8 — the write boundary under-transcribes the trigger (CHECKED).** `ValidAppend`'s own §3 comment enumerates the s28/s29/s30 refusals, but the type carries only three (fresh-open, opened-slug, prose). The comment and the type disagree — precisely the "comment says more than the type" tackiness. RefKernel's `ValidPayload` carries the full set: blocks-close self-edge, dangling blocks-close antecedent, blocks-close cycle (raw walk, as s30's `would_cycle` really is), strict+deferred contradiction, strict-with-blockers — each witnessed refusing in a `failing` block (r8b/r8c/r8d), with the informs-edge laxity preserved as a green fixture (r8a: dangling informs antecedent constructs, exactly s22's posture).

**R4 — the §4 oracle stub was elidable, not essential (CHECKED).** The stub's excuse ("needs absolute row ids threaded through the fold") dissolves: prefix position in the `Ledger n` index *is* the absolute id. One total lookup (`entryAt : Ledger n -> Fin n -> (m ** Entry Recorded m)`) de-stubs `deferredUndischargedIn` completely; both discharge polarities plus the retraction polarity are Refl-witnessed (r4a1–r4a3). The refined `strictBlockers` therefore runs the whole s31-era calculus with no oracle.

**R2 — trigger-computed fields as a Stage index (CHECKED; the strongest pure-typing refinement).** One index, `Draft`/`Recorded`, unifies two real substrate mechanisms: s29's `discharge_grade` (computed by `validate_independence()`, never writer-asserted) and s30's `edge_type` (trigger-defaulted `NULL -> informs`). `GradeF Draft = ()` makes a writer-supplied grade *unrepresentable* (red fixture r2a) — upgrading what the transcription consult honestly called "convention in a one-file sketch" to a type fact. The recording arrow `append` also carries a checked transcription of s29's grade ladder including the fail-safe same-principal default (r9a1–r9a3), where the shipped model only carried the enum.

**R5/R5b — Fin-typed projection, theorem preserved (CHECKED).** `supersededIn : ... -> Nat -> Bool` lets the model ask about rows that don't exist; the substrate's FK (`supersedes -> ledger.id`) is stronger than the model here, so Fin-typing is the model catching *up*, not gold-plating. The file's one theorem survives the refinement: `supersededStable` restated over `weaken`, proved in three lines with one `strong (weaken t) = Just t` cancellation lemma.

**R6 — proof-carrying Projection (CHECKED).** "liveIds ... in-force, ascending" was a comment; now `Projection l` carries an erased `All (\t => inForce l t = True)` and out-of-range ids are unrepresentable. (Ascending-order invariant: **paper-only** — carriable via a sortedness proof, omitted as low value.)

**R1, R3, U1/U2 — the smaller polish (CHECKED).** `Gated : Bool -> Type -> Type` names the mandatory-iff idiom once (s29's own comment admits the SQL pattern is a copy "one column over"); the eight nullary prose constructors collapse to `PProse : ProseKind -> ...`; and RefUniverse renders the kind family as a universe: `Kind` as first-class data (exactly `ledger_kind_check`'s list) plus `PayloadTy : Kind -> Nat -> Type` as the single-homed shape manifest, with shipped-without-witness and payload-smuggling both refused (failing fixtures). The universe form matches the substrate's actual architecture (kind column + shape-CHECK manifest) better than the fused GADT, and softens (does not eliminate — stated, not oversold) the lineage-evolution friction the transcription consult named.

**Paper-only, with reasons:** the GADT-universe isomorphism (mechanical, low information); the per-sNN "lineage of models" module chain (real friction, big build, no new insight expected); `HistoryLicense`'s String index replaced by a reason enum (trivial).

**Where refinement would be dishonest — checked against the substrate, kept tacky on purpose:**
- The **epoch gate** stays out (steady-state rendering); it is operator state, not ledger shape.
- The **raw write-boundary reads** (`everOpened` slug-burning; the raw `would_cycle` walk) must NOT be uniformized into the projection — s31's own closed allowlist licenses them (`LWriteBoundary`, `LDuplicateOpen`), and my `ValidPayload` deliberately quantifies them raw while `strictPremise` quantifies in-force. The two domains coexisting in one family is now the *faithful* rendering.
- The **informs-edge Slug-typed dangling antecedent** stays weakly typed (s22/s30 deliberately leave it visible-only).
- **Dual producers stay black boxes** — untouched.
- `EdgeF Recorded = EdgeType` is honest only for birth-chain worlds; a migrated world carries legacy NULL edges. Named in the file.

**One substrate observation met in passing (WARN, not my commission):** s29's `validate_independence()` silently *overwrites* a writer-supplied `discharge_grade` rather than refusing it (`review_detail` has INSERT granted to `:role` since s15, and the column is writable at INSERT). Silent coercion where the lineage's own idiom is loud refusal. A refuse-if-supplied clause would be a fail-safe, additive, class-ratified-shaped delta. Flagged, not built.

## Q2 — Does the refined model lower? The channel is narrower than it looked this morning, because three of the natural targets landed as gates today.

| Refinement | Channel | Gain or DOES-NOT-LOWER |
|---|---|---|
| R7 s31 alignment | none needed — substrate is *ahead* of the model | Lowers in reverse: the **model** must be refreshed |
| U1/U2 kind universe / shape manifest | `gates/kind_shape_manifest_gate.py` | **RESTATES — gate already shipped** (2026-07-15). Residual: keep PayloadTy and the gate's MANIFEST in visible correspondence (documentation-grade) |
| R6 proof-carrying projection / reader typing | `gates/ledger_reader_allowlist.py` (shipped with s31) | RESTATES a landed mechanism |
| R4 discharge-join single-homing | **live-definition delta: one derived view** (`discharging_attest(regards_id, reviewer)`) that `countersigned_in_force`, `work_review_gap`, and `strict_blockers.review_unresolved` all join | **REAL GAIN, not yet built** — the join is hand-copied in at least three live homes (s29's own header: "mirrors review_gap's own join shape exactly"); one home forecloses semantic drift of "discharged" |
| R2 stage index (computed fields) | additive trigger refusal: refuse non-NULL writer-supplied `discharge_grade` | **Small real gain** — a refused defect class (silent grade assertion), fail-safe-shaped |
| R8 full premise family | authoring-time manifest of `validate_work_item()` branches + byte-identity check on re-issues | **Real hazard, unbuilt**: s28→s29→s30→s31 each re-copy every prior branch with only prose "UNCHANGED byte-for-byte"; one silent mutation would ship. The typed premise list is the natural manifest source |
| R1 `Gated` combinator | authoring idiom only (next mandatory-iff column) | Marginal; the manifest gate mostly covers it |
| R3 ProseKind collapse | — | DOES-NOT-LOWER (SQL kind list already single-homed) |
| R5 Fin ids, R5b theorem, R9 grade ladder | — | DOES-NOT-LOWER (FK already stronger; theorem and ladder are model-side assurance) |

## Verdict: REFINE-AND-LOWER — but with the weight on REFINE-the-model and a deliberately short lowering list.

The model is genuinely amenable: every refinement above elaborated, nothing needed postulates, and the refined form is both prettier *and* more faithful (R7, R5, R8 close gaps where the shipped model is weaker or staler than the substrate). The maintainer's instinct that a refactored model could clean the implementation is half-confirmed: the implementation's own trajectory (s31 + the three gates landed today) has already absorbed most of what a lowering would deliver, independently. What remains and pays: **(1)** refresh/supersede Autoharn.idr against s31 with R2/R4/R8 folded in; **(2)** the `discharging_attest` derived view; **(3)** the writer-supplied-grade refusal; **(4)** a branch-manifest/byte-identity mechanism for `validate_work_item()` re-issues. Everything else on the beauty side is model-only, and saying so plainly is the honest disposition.

**Uncertainties:** (a) I read the two Fable specs only as reflected in Autoharn.idr, the lineage headers, and s31 — if the composite-discharge spec has moved since, the `composite : Bool` field's status (modeling an unratified, unbuilt mechanism per s31's own header) needs the orchestrator's confirmation; (b) whether the alphabetical/idempotence constraints on trigger re-issue make the R8 branch-manifest gate awkward is untested here; (c) one toolchain fact worth recording: `Data.Fin.strengthen` is `export`, not `public export`, so Refl proofs through it stick — my probes carry a local `strong`; a refreshed model doing compile-time semantic witnesses will hit the same wall.

<!-- doc-attest-exempt: point-in-time consultation record, banked verbatim. -->
