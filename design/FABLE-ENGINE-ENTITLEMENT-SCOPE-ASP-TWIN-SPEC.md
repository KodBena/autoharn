# FABLE-ENGINE-ENTITLEMENT-SCOPE-ASP-TWIN-SPEC — the deductive twin for scopes, and the floor the entitlement layer never had

<!-- doc-attest-exempt: Fable-authored spec 2026-07-29, status=ratified (maintainer, ledger row
822: "you're good to go", with the confer option exercised) -- REVISED 2026-07-29 same day per
the fresh-context Fable confer pass (BUILD-WITH-AMENDMENTS; all seven amendments applied in
place, the pass's report is the amendment provenance). Originally triggered by the witnessed
engine gap of ledger rows 802/803. Removal condition: the build's merge record supersedes this
exemption. -->
<!-- design-currency: status=ratified depends-on=FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md depends-on=FABLE-PRINCIPAL-STAMPS-SPEC.md depends-on=FABLE-JUDGE-LAYER-CAPABILITY-CLOSURE-SPEC.md -->

The deductive engine is this project's reason for existing: a guarantee whose only witness is
a test is weaker than a guarantee re-derived by two independent producers that must agree.
Today the entitlement layer — authority chains, delegation, and (since s70) scopes — is the
ONE registered layer with no SQL floor: `./judge --layer entitlement` on a capable target
REFUSES with a typed no-floor error (witnessed, rows 802/803), and s70's scratch witness had
to leave its ASP leg UNEXERCISED. This spec closes that gap and extends the twin to s70's
scope semantics, so the access-control batch's correctness claim is carried by the
differential, not by fixtures alone.

## 1. What is built (three parts, one commission)

**1a. The entitlement SQL floor** (`engine/ledger_floor.py`, new
`entitlement_floor_atoms(name, surfaces, now_epoch) -> set[str]`): re-derives, in pure SQL
sharing no code path with clingo (the I6 independence law as practiced by the existing four
floors), the atom sets of §1c's predicate roster. The two injected parameters are
single-home cursors, both with established precedent: `now_epoch` is the shared wall-clock
for the s64 expiry filter — BOTH producers must compare `delegation_expiry` against the SAME
epoch value or an edge expiring between the two runs manufactures a false DIVERGE_DEFECT
(the exact class `support_floor_atoms(name, now_epoch)` already fixed; the exporter's s64
block gains the same parameter in place of its export-time `now()`); `surfaces` is the
closed surface vocabulary (see 1b — it lives in serving code, not in any database, so the
floor cannot read it and must be handed it through the same single home the exporter uses).
`reaches_genesis/1` and `reaches_genesis_scoped/2` recurse over the (principal, act_class)
pair domain seeded from genesis plus the no-genesis exception; `open_scope/1` is NOT EXISTS
over in-force binding rows; the text terms (Surface, Mode) MUST be rendered through a floor
twin of `_atom()`'s bare-vs-quoted branch — the `_wi_quote` incident (one prior asymmetry
made the work layer unable to AGREE on any world) is the named hazard, and the quote logic
is factored to one shared home both producers import rather than duplicated. The registry
flip: `LAYERS["entitlement"].floor` from `NoFloor(...)` to the frozen predicate set of §1c,
and `run_layer_differential` gains the entitlement branch on the work/belief/defeat pattern
— INCLUDING the third, easily-missed layer-name consumer: `main()`'s `--retain` edb_text
if-chain, which today would silently bank an empty `edb.lp` for an unlisted layer; it gains
its entitlement branch in the same commit. The s64 twin's named deferred limits
(depth budget, must-countersign) STAY deferred and disclosed — the floor mirrors what the
ASP derives, never more.

**1b. s70 scope facts** (`engine/ledger_edb.py`, extending `export_entitlement` additively,
gated on the three s70 columns via the has_col capability idiom, degrading to
absent-with-reason on a pre-s70 kernel). The emitted families, exhaustively:

- `scope_binding_row(P).` — one fact per principal holding a current in-force
  `principal_scope_bound` act per the `principal_scopes` view (supersession-aware,
  exporter-filtered exactly as `acts_for_edge/2` already arrives). This fact — row
  existence, not surface count — is what arms a scope (see 1c's fail-closed rule and the
  representable state that forces the distinction).
- `scope_bound(P, Surface).` — one fact per element of the binding's `scope_surfaces`
  array; `text[]` parsed Python-side, never spliced as program text (ADR-0000's
  value/program amendment).
- `scope_exclusion(P, Family, Key).` — decomposed from the `scope_exclusions` jsonb.
  Family tokens are the KERNEL CHECK's literal vocabulary, pinned as a STANDARDS-REGISTRY
  tuple in the exporter: `kind-class`, `thread`, `work-item-lineage`, `rows` (the kernel's
  own spellings, never prose renames). Decomposition contract: one fact per entry for the
  scalar families; for `rows` (whose admitted value is an ARRAY of numeral ids), one fact
  per (entry, member). Anything outside the CHECK's admitted shapes refuses loudly at
  export via the established parse-refusal shape (the `DefeatParseError`-style typed error,
  surfacing as QUARANTINED through the differential's existing producer-crash path) —
  named deliberately, never the accidental generic-except path.
- `scope_disclosure(P, Mode).` — the categorical `scope_disclosure_mode` through
  `_atom()`. All three tier values exported; the fourth representable state, NULL mode
  (which s70 explicitly licenses and refuses to default), emits NO fact — absence of a
  declared tier is absence, mirroring the kernel's own no-implicit-default stance; the
  floor mirrors the same rule.
- `surface(S).` — the closed route/view vocabulary, which lives in the SERVING layer's
  registry module (s70's own LIMITS: the kernel does not carry it). ONE home: the exporter
  imports the serving registry's vocabulary and emits it; the floor receives the SAME list
  via its `surfaces` parameter, sourced by the differential from that same one import.
  On a scratch fixture world the vocabulary is therefore the repo's registry, identical
  for both producers by construction. Disclosed consequence, stated so nobody over-reads:
  because the vocabulary is injected from one home into both producers, the open-scope
  `may_read_surface` comparison verifies join/encoding correctness over that shared
  universe, not the universe's own truth — the vocabulary's fidelity to the actual served
  routes is the serving layer's own fixture obligation, named in §3 as not covered here.

**1c. The scope predicates** (`engine/lp/ledger_entitlement.lp`, BESIDE the existing rules,
never into them — the stratification law both prior extensions of this file obeyed):

- `scope_armed(P) :- scope_binding_row(P).` — FAIL-CLOSED arming: a principal with an
  in-force binding is scoped even when the binding's `scope_surfaces` is NULL/empty (a
  representable s70 state: binding row present, zero surfaces, exclusions present). Such
  a binding grants nothing rather than everything — armed-with-no-surfaces derives no
  `may_read_surface` at all. This choice is deliberate and its consequence is stated: the
  serving filter MUST key on the same row-existence predicate, and the closure statement
  carries the state explicitly.
- `open_scope(P) :- principal(P), not scope_armed(P).` — the fail-safe default as a rule:
  on any world with zero scope facts (including every pre-s70 world), every principal
  derives `open_scope` — the unarmed-world-byte-identical guarantee as a one-line
  consequence of negation-as-failure.
- `may_read_surface(P, S) :- open_scope(P), surface(S).` and
  `may_read_surface(P, S) :- scope_bound(P, S).` — named at its honest granularity:
  SURFACE visibility. Row-level exclusion behavior is deliberately not derived in this
  increment (see the deferral below), and the name says so.
- `#show` exactly: `open_scope/1`, `may_read_surface/2`, `scope_disclosure/2` (alongside
  the existing `reaches_genesis/1`, `reaches_genesis_scoped/2`). The floor mirrors all
  five. `MODULES["ledger_entitlement.lp"].provides` is updated to the full five-predicate
  #show list — INCLUDING repairing the pre-existing drift (it still reads
  `("reaches_genesis/1",)`, omitting s64's `reaches_genesis_scoped/2` — a hazard in reach,
  fixed in this commission).

**Pre-s70 targets — one semantics, not a capability split (revised per the confer pass,
which refuted the earlier per-family-INCAPABLE design as unbuildable against LayerSpec's
one-probe shape and contradicted by the degrade idiom itself):** the layer keeps its ONE
existing capability probe (the s60 marker column). On a pre-s70-but-s60-capable target,
BOTH producers degrade identically — zero scope facts, everyone derives `open_scope`,
`may_read_surface` spans the injected vocabulary — and the predicates are ADJUDICATED,
expecting AGREE, because everyone-open IS the true semantics of a scope-less world (it is
exactly what the AC spec's fail-safe default says such a world means). The
pre-s70-vs-s70-unarmed indistinguishability is a feature of the semantics, not a blind
spot, and the per-family emission story lives where it already lives: the exporter's
Capability records, disclosed in the EDB header. `LayerSpec` needs no change.

**Deferred derivation, named:** row-level exclusion denial. `scope_exclusion/3` facts are
exported from day one, but no derived per-row denial predicate: deriving it deductively
requires exporting the row universe per principal, a differential that scales with ledger
size rather than principal count — a sizing commitment that deserves its own decision, not
a smuggled O(rows) default. Until lifted, the boundary filter's row-level behavior is
witnessed by its own fixture family, and the twin binds surface granularity only.

## 2. What this makes true (the consumer, named)

`./judge --layer entitlement` on any capable world stops refusing and starts adjudicating:
AGREE means the SQL kernel's view of authority, arming, and surface visibility and the ASP
derivation from first principles coincide exactly over the five floor predicates; a defect
in either producer surfaces as DIVERGE_DEFECT, a red exit, at every judge run — standing
verification, not a test someone must remember to run. (For `scope_disclosure/2`, stated
honestly: both producers read the same kernel view, so the comparison certifies the
encoding/rendering agreement of the two independent readers — the `_wi_quote` defect class
— not an independent re-derivation; the derivation-grade claims live on the other four.)
The serving-layer boundary filter gains a deductive reference model AT SURFACE GRANULARITY:
its fixture family asserts the filter's allow/deny agrees with `may_read_surface/2` on the
same scratch world, while exclusion (row-level) behavior remains fixture-witnessed until
the deferred derivation lands — both clauses stated so neither is over-read. And s70's
UNEXERCISED leg (rows 802/803) closes: the fail-safe-delta class rule's SQL/ASP-AGREE
precondition becomes satisfiable for the entitlement family, s60 through s70.

## 3. Closure statement (ADR-0000 Rule 2(a))

**Invariant:** for every target world on which the entitlement layer is capable, the
differential's two producers derive identical atom sets over the declared floor predicates
{reaches_genesis/1, reaches_genesis_scoped/2, open_scope/1, may_read_surface/2,
scope_disclosure/2}, or the run exits red with a typed verdict; no capable target passes
without the comparison actually running.

**Quantification universe:** targets — every deployment the judge template resolves plus
every scratch world a fixture births; capability — the layer's one existing probe (s60
marker column); pre-s70-capable targets are adjudicated under the degrade semantics of §1c
(everyone-open, AGREE expected), with per-family emission disclosed by the exporter's
Capability records. Fact families — exactly 1b's enumeration: `scope_binding_row/1`,
`scope_bound/2`, `scope_exclusion/3`, `scope_disclosure/2`, `surface/1`, each gated and
reasoned. Exclusion families — exactly the kernel CHECK's literal vocabulary
(`kind-class`, `thread`, `work-item-lineage`, `rows`), refuse-on-unknown at export.
Representable states carried explicitly: NULL disclosure mode (no fact, both producers);
binding-with-no-surfaces (armed, grants nothing — fail-closed). Shared cursors: one
`now_epoch`, one `surfaces` list, each injected from a single home into both producers.
Verdict vocabulary — unchanged (AGREE, DIVERGE_BY_DESIGN, DIVERGE_DEFECT, QUARANTINED;
RED unchanged).

**Named as not covered, deliberately:** per-row exclusion denial as a derived predicate
(§1's sizing note); the surface vocabulary's fidelity to the actually-served routes (the
injection makes both producers share it; whether it matches reality is the serving layer's
own fixture obligation); the s64 depth-budget and must-countersign conjuncts (unchanged
deferred limits); the boundary filter itself (its own commission; this spec provides its
surface-granular reference model); any kernel change (engine/ only; s70 is frozen).

## 4. Witness plan (both polarities, scratch, red first)

On an s70-bearing scratch birth: a scoped principal derives `may_read_surface` for exactly
its bound surfaces and no `open_scope`; an unbound principal derives `open_scope` and
`may_read_surface` over the injected vocabulary; a binding-row-with-no-surfaces principal
derives `scope_armed`-side behavior (no open_scope, no may_read_surface — the fail-closed
state witnessed explicitly); NULL disclosure mode emits no fact on either producer;
differential AGREE on all of it. RED, each side broken once for independence: a
deliberately-broken floor (one predicate's SQL edited in a scratch copy) produces
DIVERGE_DEFECT; a malformed exclusions value produces the typed parse-refusal → QUARANTINED
— staged by dropping the `scope_exclusions_shape` constraint on the scratch schema first
and then inserting (the CHECK binds superusers too; the drop is the disclosed price of
staging kernel-impossible bytes, on scratch only, and the leg's claim is exporter-refusal,
not kernel-refusal). Pre-s70 target: adjudicated AGREE under everyone-open degrade,
witnessed. `--retain` on the entitlement layer banks a non-empty edb.lp (the F7 branch
witnessed). The judge-all-capable-layers fixture extended for the layer's new non-refusing
path.

## 5. Execution

Sonnet builds from this spec (the standing delegation contract; this document is the
Fable-authored basis, revised per the confer pass before any builder saw it), fresh-context
strengthened review before merge, engine/ only, mergeable without a birth. Sequenced after
s70's merge (done, 5c580ef0) so fixtures can birth s70-bearing scratch worlds from main.

## License

Public Domain (The Unlicense).
