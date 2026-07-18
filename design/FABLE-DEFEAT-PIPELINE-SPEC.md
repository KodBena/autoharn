<!-- doc-attest-exempt: RATIFIED build basis authored at birth 2026-07-18 under the Fable freeze plan (ledger row 1455 posture); the ADR-0017 fresh-context attestation is deferred until the Sonnet build lands and the content stabilizes against built reality -- attesting a basis the build's own witness round may amend would go stale by design. -->

# FABLE-DEFEAT-PIPELINE-SPEC — the minimal model-defeat pipeline: EDB export bill, the defeat rule pair, the judge pairing, and the credited read surface

**Status:** RATIFIED BUILD BASIS at birth — authorized by the maintainer's batch ruling,
ledger row 1481 (2026-07-18), conversion (b) of that ruling's two authorized Fable passes.
Fable-authored, a conversion of the note-grade constructions in
[design/FABLE-DEFEASIBILITY-ENVELOPE-2026-07-18.md](../vestigial_documentation/design/FABLE-DEFEASIBILITY-ENVELOPE-2026-07-18.md)
(its §3 defeat rule with interaction-projection correction I1 applied, its §9 serving
recommendation (c), its §5 stratification discipline as binding builder law, and the
ratified cascade direction) to build grade. A **Sonnet builder** executes this document
after Fable authoring ends (2026-07-19); every forkable choice is fixed herein, because
`engine/lp/` semantics require a Fable-authored spec and no Fable will be available to
consult. Cost attribution: ledger estimate row 1483. Nothing in this document is applied by
its authoring; no commit, no ledger write, no kernel or engine edit accompanies it.

**What this document is, in plain words.** The project's ledger derives "what currently
stands" two independent ways — SQL recursive views/queries and an ASP logic program — and
requires the two to agree bit-identically (`./judge`). A separate ratified design (the OTel
sentry, [design/FABLE-OTEL-SENTRY-SPEC.md](FABLE-OTEL-SENTRY-SPEC.md)) writes *model-identity
attestations*: ledger rows asserting which model actually served the session that wrote some
other row, including *mismatch* verdicts when the observed model contradicts the declared
one. This spec builds the minimal pipeline that lets a mismatch attestation, backed by an
in-force trust grant, **defeat** the attested row in derived views — excluded from a
`credited` reading, its dependents flagged for human re-examination — with the whole
machinery governed by ordinary retractable ledger rows and computed fresh on every
derivation pass (nothing stored, nothing edited, the record untouched).

**Primary inputs, all read in full at authoring:** the envelope (above) including its
2026-07-18 interaction-projection section;
[engine/ledger_edb.py](../engine/ledger_edb.py),
[engine/ledger_floor.py](../engine/ledger_floor.py),
[engine/ledger_differential.py](../engine/ledger_differential.py),
[engine/lp_registry.py](../engine/lp_registry.py),
[engine/lp/ledger_tnow.lp](../engine/lp/ledger_tnow.lp),
[engine/lp/ledger_support.lp](../engine/lp/ledger_support.lp);
[kernel/lineage/s41-principal-bindings-and-relations.sql](../kernel/lineage/s41-principal-bindings-and-relations.sql);
the sentry spec's §5 (the v1 statement convention this pipeline parses) and §8 (the s44
typed kind); ledger rows 1467, 1481 (read via `./led show`); CLAUDE.md and the six
mandatory ADRs
([0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md),
[0011](../law/adr/0011-mechanization-discipline.md),
[0012](../law/adr/0012-compositional-and-structural-hygiene.md),
[0013](../law/adr/0013-execution-integrity.md),
[0017](../law/adr/0017-the-zero-context-reader.md),
[0018](../law/adr/0018-consults-are-not-front-loaded.md)).

---

## 0. Executive summary

Five deliverables, in build order:

1. **The EDB export bill paid** (§4): `engine/ledger_edb.py` gains `export_defeat(name)` —
   a capability-gated fact-family export in the exact mold of the existing `export_work()`
   — emitting `row_actor/2`, `attest_row/1`, `mismatch_attest/3`, `trust_grant/3`,
   `grant_row/1`, and `agent_class/2`. Attestations are read from **both** sources the
   sentry design defines: v1 convention rows (statement-parsed under the pinned contract of
   §3) and, where the world carries them, s44 typed columns.
2. **The rule pair** (§5): a new `engine/lp/ledger_defeat.lp` deriving
   `model_defeated(R,A,G)`, `credited(R)`, `exposure_model(F,D)`,
   `exposure_model_undischarged(F,D)` — the envelope's §3.2 rule with the I1 two-conjunct
   correction applied at the export boundary, the ratified cascade direction (e) as a join
   onto the *existing* support-exposure machinery, and the ratified I5 rule (standing never
   conditions defeat) honored by construction.
3. **The SQL twin** (§6): `defeat_floor_atoms()` in `engine/ledger_floor.py`, independently
   derived (no shared code path with clingo), emitting the same four judgment families.
4. **The judge pairing** (§7): a `"defeat"` layer in `engine/lp_registry.py` and a defeat
   arm in `run_layer_differential` — `./judge --layer defeat` — with AGREE the authority
   and any undeclared divergence red. The differential doubles as the mechanization of the
   stratification law (§10).
5. **The credited read surface** (§8): the envelope's serving option (c) — a kernel delta
   (working name `s46-credited-views.sql`, **view-only, zero new columns**) defining
   `credited_current` and `model_defeated_rows`, prerequisite s44, entering the same
   evidence-triggered birth chain RD-2 governs; until that world exists, the engine floor
   is the interim credited computation. The SPA display contract (§9) binds any consumer.

Deliberately OUT (§13, each with its ratified or reserved ground): grade-conditioned
defeat, s44 chain entry itself, any daemon or materialized cache, defeat-of-defeat
semantics beyond what supersession already gives, the conflict rule, heavy-grade
countersign and the review/countersign EDB families, and standing-conditioned defeat
(ratified NO — stated in-scope as a decided rule, §5.3).

## 1. The ratified rulings, verbatim (ledger row 1481)

The commissioning ruling, quoted in the parts this spec executes or leans on (full row via
`./led show 1481`; the ratifying act was the maintainer's, exercised as a single batch):

> *"I5 YES standing-never-conditions-defeat as a decided rule for the future defeat spec;
> CASCADE YES the envelope's option (e) direction (hard defeat + typed exposure of
> dependents discharged by clean re-affirmation)."*

> *"RD-1 NO cross-trust-domain tool-key exception for v1 (host-side detached signatures
> deliver the evidentiary value; D-3 stands unamended; reversible); RD-2 s44 enters the
> first birth chain AFTER v1 attestation rows have run live and the maintainer has
> reviewed them (evidence-triggered, no calendar)."*

> *"ALSO AUTHORIZED: both Fable conversion passes tonight -- ... (b) the minimal
> defeat-pipeline spec (I10 EDB export bill + attestation facts + model_defeated/credited
> rule pair with judge pairing) -- after which NOTHING in the project queue requires Fable
> authoring. Build split per his direction: Sonnet builds every component post-conversion."*

Q3's band-architecture YES is direction-only ("construction still awaiting deployment
data"), which is why grade-conditioned defeat stays OUT (§13).

## 2. Scope, prerequisites, and the two world classes

**Engine changes** (items 1–4) are ordinary repo work on `engine/` — the sensitive surface
this spec exists to fix completely; they touch no kernel, no `law/`, no hooks. **The kernel
delta** (item 5) is authored here as spec text and reaches reality only via a future birth
chain (runs-are-strictly-linear); the builder authors the `.sql` + `.detect.sql` files and
scratch-witnesses them, never applies them to a live world.

Two world classes exist for this pipeline, and the design serves both without forking:

- **Pre-s41 worlds** (including the current live world): no typed competence grants exist,
  so the `trust_grant` family is capability-EXCLUDED with reason and **no defeat is
  derivable** — the pipeline's derivation legs QUARANTINE/refuse loudly there (§4.3), never
  AGREE-on-empty. The current world is watch-and-attest only (sentry v0/v1); this is the
  disclosed interim, mirroring the sentry spec's own §4 sequencing honesty.
- **s41+ worlds** (any world born with s41 in its chain, with or without s44): grants are
  typed; attestations arrive as v1 convention rows (pre-s44) or typed rows (s44+); the
  full pipeline derives. The scratch witness chain (§12) is an s41+ chain on the toy db.

## 3. The attestation parse contract (v1 convention rows)

The sentry spec §5 fixes the v1 statement convention; it is the parse contract and is
quoted here verbatim as that spec renders it (one written line, displayed wrapped):

```
model-attestation v1 | row=<ledger id> | model=<model string, verbatim from the event>
  | grade=<exact-command|turn-bracketed|session-scoped|ambiguous>
  | expected=<declared model or "undeclared"> | verdict=<match|MISMATCH|unevaluated>
  | session=<OTel session.id> | basis=<join keys used, comma-separated>
  | rebuttals=design/FABLE-OTEL-SENTRY-SPEC.md#7-the-standing-rebuttals
```

with its own rules: "One line, `|`-separated `key=value` fields, order fixed, `v1` bumped
on any field change ... a version mismatch is treated as no attestation by any future
parser."

**Pinned clarifications, binding on BOTH this pipeline's parsers and the sentry verb's
builder** (clarifications of the convention, not changes to it — the verb is also unbuilt,
so the two builders read one contract):

- **P-1 Split.** Fields are obtained by splitting the statement on the `|` character and
  trimming ASCII whitespace from each segment. Whitespace around `|` is therefore
  insignificant; both producers parse identically regardless of spacing.
- **P-2 Position.** Parsing is **positional** ("order fixed" is the convention's own
  rule): segment 1 (1-based) is the version header, segment 2 `row=`, 3 `model=`, 4
  `grade=`, 5 `expected=`, 6 `verdict=`, 7 `session=`, 8 `basis=`, 9 `rebuttals=`. Each
  segment 2–9 must begin with exactly its expected `key=` prefix; the value is the
  remainder of the segment.
- **P-3 Candidate detection.** A candidate row is any ledger row, **of any kind** (the
  sentry spec permits a `note` fallback beside `verification`), whose trimmed statement
  begins with the literal prefix `model-attestation ` (trailing space included).
- **P-4 Version gate.** Segment 1 must be exactly `model-attestation v1` after trimming.
  A candidate with any other version token is **skipped and counted** (reported in the
  export manifest/stdout as version-skipped, per the convention's own no-attestation rule)
  — never parsed, never silently dropped uncounted.
- **P-5 Malformedness is loud.** A `v1` candidate whose segments violate P-2, whose `row=`
  value is not an integer, whose `grade=` value is outside the four-member vocabulary, or
  whose `verdict=` value is outside `{match, MISMATCH, unevaluated}` (exact case — the
  convention's uppercase `MISMATCH` is deliberate) causes a **loud refusal of the export**
  (raise; the differential reads QUARANTINED). Both producers fail identically (§6). Never
  skip-and-continue: a malformed attestation is a defect to surface (ADR-0002).
- **P-6 Mismatch detection.** Only `verdict=MISMATCH` (exact) yields a `mismatch_attest`
  fact. `match` and `unevaluated` rows yield `attest_row/1` only (§4.2) — no match-side
  fact family exists in this increment (the conflict rule is reserved, §13).
- **P-7 Text stays home.** No statement text, model string, session id, or basis crosses
  into the EDB — ids and closed-vocabulary atoms only (the ids-are-the-interchange rule,
  `ledger_edb.py`'s own header). The grade crosses as an atom rendered by the existing
  `_atom()` helper (hyphens make all four grades quoted strings: `"exact-command"` etc.).

**The s44 typed arm** (worlds whose lineage carries the sentry spec §8 delta): candidate
rows are `kind = 'model_identity_attested'`; no parsing — `attest_row_id`,
`attest_verdict` (closed lowercase `mismatch` there, per s44's CHECK), `attest_grade` are
read as columns. Capability detection: presence of the `attest_row_id` column. Both arms
may coexist in one world (v1 rows written before its s44 verbs existed); both are
harvested; a row is one arm's or the other's by its shape, never both.

## 4. The EDB export bill (`export_defeat` in `engine/ledger_edb.py`)

### 4.1 Shape and conventions

A new function `export_defeat(name) -> EdbExport`, in the exact mold of the existing
`export_work()`: its own `EdbExport` with a capability manifest, every non-produced family
a **declared exclusion with reason** (the F49 posture), `require()` refusing loudly, ids
only, `ORDER BY id` on every query, read-only psql via the existing `Target` plumbing. The
defeat layer's differential grounds the composed EDB `export(name).edb_text() + "\n" +
export_defeat(name).edb_text()` exactly as the work layer composes `export` + `export_work`.
`entry/6` is **not** widened (banked derivations stay byte-identical; the additive-proof
idiom); the actor arrives as its own family.

### 4.2 The families, exactly

| Fact | Source | Capability gate | Notes |
| --- | --- | --- | --- |
| `row_actor(Id,P).` | every ledger row with `actor IS NOT NULL`: `(id, actor)` | `actor` column present | the scratch-only `row_actor/2` of `ledger_support.lp`'s §3 stand-in, now emitted by the standing exporter; P is the principal id (bigint) |
| `attest_row(A).` | every valid attestation row, **any verdict**, both arms (§3) | v1 arm: always capable (statement+kind are core columns); typed arm: `attest_row_id` column | the structural basis of the §5 target-domain guard; emitted even for match/unevaluated rows |
| `mismatch_attest(A,R,Grade).` | attestation rows with mismatch verdict (P-6; s44 `attest_verdict='mismatch'`): A = attestation row id, R = attested row id (v1 `row=` field; s44 `attest_row_id`), Grade = grade atom | same as `attest_row` | Grade is carried for forward-compatibility (grade-conditioned defeat is OUT); the rule reads it anonymously |
| `trust_grant(G,P,Activity).` | rows with `kind='principal_competence_granted' AND principal_binding_active` (s41): `(id, principal_subject, principal_competence_activity)` | `principal_binding_active` AND `principal_competence_activity` columns present | **the I1 two-conjunct correction, applied at the honest boundary**: `principal_binding_active` is a same-row attribute (like `kind`), so filtering on it is attribute projection, NOT a derived in-force judgment — the *in-force* half (`not superseded(G)`) stays in the rules where the discipline puts it (§10 law 1). A withdrawal row (`active=false`) is not a grant assertion and never emits this fact. Activity crosses via `_atom()` (hyphens → quoted string) |
| `grant_row(G).` | EVERY row of `kind='principal_competence_granted'`, active or not | same as `trust_grant` | the guard basis (§5.2): grant-kind rows are outside the defeat target domain regardless of their active flag |
| `agent_class(P,Class).` | `kern.principal`: `(id, agent_class)` | the `<kern>.principal` relation present | **emitted, consumed by no rule in this spec** — the I10 bill paid once, declared in the manifest as "emitted for future countersign-conditioned consumers (reserved, this spec §13); no rule reads it this increment". Class is one of the s13 closed vocabulary (`human`/`model`/`subagent`/`tool`), all `_atom()`-safe bare constants |

The v1-arm counts (candidates, version-skipped, parsed, mismatches) are reported in the
manifest header comments, so a zero-fact export is legible as "no attestations exist"
versus "arm not capable" versus "rows skipped by version".

### 4.3 Capability semantics (which worlds refuse)

Following the `KERNEL_SHAPE` precedent exactly: on a pre-s41 target, `trust_grant`/
`grant_row` are `Capability(produced=False, capable=False, reason="no
principal_binding_active/principal_competence_activity columns (pre-s41 lineage) --
capability absent, not record-empty")`; `require("trust_grant")` refuses loudly. On an
s41+ target with zero grant rows, the family is `produced=True` with zero facts — a
legitimate empty (no grants means no defeat force, correctly). The defeat differential
(§7) calls `require()` on `trust_grant`, `attest_row`, `mismatch_attest`, and `row_actor`
before grounding, so a pre-s41 target QUARANTINES with the capability reason instead of
reading AGREE over a vacuously empty derivation — the F49 class, foreclosed the same way
`run_sql_work` already forecloses pre-s22 targets.

## 5. The ASP program — `engine/lp/ledger_defeat.lp`, complete text

### 5.1 The program (normative — the builder transcribes, not adapts)

The file's header comment follows the house form (what it is, load order, the registry
citation, this spec as provenance); the rules are these, exactly:

```
% Declared-optional EDB families (empty extension = silence, the house #defined idiom):
#defined mismatch_attest/3.
#defined attest_row/1.
#defined grant_row/1.
#defined trust_grant/3.
#defined row_actor/2.
#defined agent_class/2.
% Consumed from ledger_tnow.lp / ledger_support.lp when stacked (LAYERS "defeat"):
#defined superseded/1.
#defined in_force/1.
#defined support_star/2.
#defined affirmed/2.

% The defeat machinery's own input kinds are outside its target domain (spec §10 law 2):
defeat_input(X) :- attest_row(X).
defeat_input(X) :- grant_row(X).

% THE DEFEAT RULE (envelope §3.2, I1-corrected; row-1481 rulings honored by construction).
% Every in-force test is `not superseded/1` -- the supersession layer, never this layer
% (§10 law 1). Grade is carried, deliberately unread (grade-conditioned defeat is OUT).
model_defeated(R,A,G) :-
    mismatch_attest(A,R,_),
    not superseded(A),
    row_actor(A,P),
    trust_grant(G,P,"model-identity-attestation"),
    not superseded(G),
    not defeat_input(R).

model_defeated_row(R) :- model_defeated(R,_,_).

% The credited reading: beside in_force, never inside it (§10 law 3).
credited(R) :- in_force(R), not model_defeated_row(R).

% CASCADE, the ratified direction (e): hard defeat above; dependents FLAGGED over the
% EXISTING support closure, discharged by the EXISTING SoD-gated affirmation -- a join,
% not new machinery (ledger_support.lp is byte-untouched; this program only reads it).
exposure_model(F,D) :- in_force(F), support_star(F,D), model_defeated_row(D).
exposure_model_undischarged(F,D) :- exposure_model(F,D), not affirmed(F,D).

#show model_defeated/3.
#show credited/1.
#show exposure_model/2.
#show exposure_model_undischarged/2.
```

Zero `:-` integrity constraints (the corpus's paraconsistent idiom); every judgment
descriptive; `model_defeated/3` carries its warrant (A, G) per the envelope's
flag-with-cause discipline — a consumer can always answer "defeated by which attestation
under which grant".

### 5.2 Design facts the builder must not re-derive

- **The activity literal** is exactly `"model-identity-attestation"` (quoted-string atom —
  hyphens make it unsafe as a bare constant under `_atom()`'s branch), matching the sentry
  spec §4's grant activity. The SQL twin compares the text literal
  `model-identity-attestation`.
- **`not defeat_input(R)`** makes §10 law 2 structural: an attestation row (any verdict)
  or a grant row (any flag) can never be a defeat target. The sentry verb's own
  no-self-attestation hygiene is the write-side half; this is the derivation-side half.
- **`model_defeated` deliberately does not test `in_force(R)`.** Defeat is a fact about
  the attestation-and-grant standing; a row both superseded and model-defeated is simply
  absent from `credited` (which requires `in_force`) — no double-filtering, no hidden
  coupling.
- **Multiple in-force grants** for one (P, activity) are possible (the s41 CLI dedupe is
  CLI-side, disclosed there); the rule then derives one `model_defeated(R,A,G)` per grant
  — harmless multiplicity, both producers derive it identically, `model_defeated_row/1`
  collapses it for the credited reading. Named, not patched.
- **Affirmation reuse is cause-agnostic, named:** `affirmed(F,D)` records "F was
  re-examined and survives D's defeat" keyed on (F,D) — `ledger_support.lp`'s existing
  semantics, cause-blind by its own construction (its attestation-currency rule
  distinguishes fresh *antecedents*, not fresh *causes* on one antecedent). An affirmation
  recorded against D's supersession-defeat therefore also discharges D's model-defeat
  exposure. This inherits existing semantics unchanged; sharpening currency to
  (F,D,cause) would be new machinery and is OUT (§13).

### 5.3 The ratified I5 rule, stated as decided law

**Standing never conditions defeat** (row 1481, verbatim ruling quoted in §1). The rule
body reads no lifecycle facts — no `principal_suspended`, no `principal_revoked`, no
standing predicate exists in this layer's vocabulary — **by decision, not omission**. A
suspended or revoked attester's past attestations, under a still-in-force grant, continue
to defeat; the sanctioned levers over defeat force are the grant (supersede/withdraw →
wholesale lapse) and the attestation (supersede → targeted resurrection). A future author
who "notices" a suspended sentry still defeating and reaches to patch it is contradicting
a maintainer ruling; this paragraph exists so they find the ruling before the patch.

## 6. The SQL twin — `defeat_floor_atoms` in `engine/ledger_floor.py`

**Independence posture unchanged and mandatory:** no shared code path with clingo or with
`export_defeat` — the floor re-reads the database directly and re-derives everything,
including its own v1 statement parse in SQL (the same deliberate duplication
`work_item_floor_atoms`' `_wi_quote` documents). Bit-identity between producers is the
gate; a shared parser would launder it.

Normative construction (the builder writes the SQL; these clauses fix its semantics —
every judgment must land atom-identical with §5.1 or the differential is red, which is the
enforcement):

1. `DEFEAT_PREDS = ("model_defeated", "credited", "exposure_model",
   "exposure_model_undischarged")` — the compared set, mirroring `WORK_ITEM_PREDS`'s role.
2. Reuse `_base_ctes` (the one SQL home of the supersession/in-force closure — P1;
   `sup_star`/`superseded`/`in_force` are NOT re-authored).
3. **v1 parse in SQL**, per §3's pins: candidates
   `btrim(statement) LIKE 'model-attestation %'`; version gate
   `btrim(split_part(statement,'|',1)) = 'model-attestation v1'`; positional fields via
   `btrim(split_part(statement,'|',N))` with the `key=` prefix checked
   (`left(seg, length('key='))='key='`) and stripped; a violated pin **raises** (the
   builder implements P-5 as a SQL-side check that surfaces as an exception → the
   producer QUARANTINES — e.g. a strict `::bigint` cast on the row value plus explicit
   `CASE ... ELSE <raise via a division-guard or a dedicated plpgsql DO check>`; the exact
   raising mechanism is the builder's, the *behavior* — loud failure, never a skipped row —
   is not). Version-skipped candidates are excluded by the version gate (correct and
   count-reported on the Python side; the floor needs no counter).
4. **Typed arm** where `attest_row_id` exists: rows of `kind='model_identity_attested'`,
   mismatch iff `attest_verdict='mismatch'`; both arms UNIONed into one
   `attest(a_id, r_id, grade)`-shaped CTE plus an `attest_any(a_id)` CTE (all verdicts).
5. **Grants:** `grants AS (SELECT id AS g, principal_subject AS p FROM {rel} WHERE
   kind='principal_competence_granted' AND principal_binding_active AND
   principal_competence_activity = 'model-identity-attestation')`, and `grant_any(g)`
   over the kind unfiltered — column-gated exactly like the s37 arms (a pre-s41 target
   returns a QUARANTINE from the defeat producer before this SQL runs; §7).
6. **The rule:** `defeated AS (SELECT DISTINCT a.r_id, a.a_id, g.g FROM attest a JOIN
   {rel} ar ON ar.id = a.a_id JOIN grants g ON g.p = ar.actor WHERE a.a_id NOT IN
   (SELECT id FROM superseded) AND g.g NOT IN (SELECT id FROM superseded) AND a.r_id NOT
   IN (SELECT a_id FROM attest_any) AND a.r_id NOT IN (SELECT g FROM grant_any))` —
   note `ar.actor` is `row_actor` on the floor side.
7. **Credited:** `SELECT id FROM in_force WHERE id NOT IN (SELECT r_id FROM defeated)`.
8. **Cascade:** reuse the support closure exactly as `support_floor_atoms` builds it
   (`support_edge`/`support_star` over enacts/answers/assumes with the same set-UNION
   pair recursion — the cycle-safe form that agrees with ASP); `exposure_model` =
   in-force F whose `support_star` reaches a defeated `r_id`; the discharge join mirrors
   `support_floor_atoms`' `affirmed` CTE (SoD-gated, `support_affirm` side table where
   present, DEFERRED in the manifest where absent — never a silent empty).
9. **Atom rendering:** every shown atom is all-integer (`model_defeated(R,A,G)`,
   `credited(R)`, `exposure_model(F,D)`, `exposure_model_undischarged(F,D)`) — no text
   crosses, so no quoting branch exists to diverge (the `_wi_quote` hazard class is
   structurally absent; say so in the function docstring).

## 7. Registry and judge wiring

- `engine/lp_registry.py`: a `MODULES["ledger_defeat.lp"]` entry (provides the four shown
  predicates plus `model_defeated_row/1`, `defeat_input/1`; requires `ledger_tnow.lp`,
  `ledger_support.lp`; `stands_alone=True` — the `#defined` idiom holds — with the note
  that meaningfulness, not groundability, is what the layer stack protects, per
  `work_items.lp`'s own precedent note). `LAYERS` gains
  `"defeat": ("ledger_tnow.lp", "ledger_support.lp", "ledger_defeat.lp")`.
- `engine/ledger_differential.py`: `run_sql_defeat(name, ...)` (QUARANTINE on a pre-s41
  target with the capability reason, mirroring `run_sql_work`'s pre-s22 refusal) and a
  `layer == "defeat"` arm in `run_layer_differential` (the current `NotImplementedError`
  branch is replaced by explicit per-layer dispatch; the work arm is untouched). EDB =
  `export(name).edb_text() + export_defeat(name).edb_text()`; ASP atoms filtered to
  `DEFEAT_PREDS`; derivation records banked per the existing retention scheme.
  `./judge --layer defeat` reaches it through the existing `"$@"` passthrough — no
  template edit.
- **Authority:** neither producer wins; **agreement is the authority** — AGREE /
  DIVERGE_BY_DESIGN (none declared this increment) / DIVERGE_DEFECT / QUARANTINED, red on
  the last two, exactly the standing closed vocabulary. Every rule addition to this layer,
  forever, ships as a pair or goes red — that is not a convention, it is what the
  differential mechanically enforces.
- `engine/registry_baseline.json` / `verify_registry_parity.py`: updated in the same
  commit per that gate's own procedure (run the engine test suite; the parity test is the
  witness that the registry and the real files agree).

## 8. The credited read surface — kernel delta `s46-credited-views.sql` (authored for a future chain)

The envelope's serving option (c), ratified direction: an ordinary SQL view read the way
`ledger_current` is. **View-only, zero new ledger columns, zero new kinds — therefore
`compute_row_hash` is untouched and `gates/hash_coverage_gate.py` stays green trivially;
the builder states this in the delta header rather than leaving it inferred.** Writes are
unaffected (the s43 boundary continues to own them; this delta touches no INSERT path).

- **Prerequisite: s44** (and transitively s43/s42/s41). The kernel views read the *typed*
  attestation columns only — a kernel view parsing the v1 statement convention would be
  load-bearing knowledge in an unenforceable convention inside the kernel (cancer G),
  refused here explicitly. Consequence, named: `s45` enters the same evidence-triggered
  chain as s44 (RD-2's trigger, the maintainer's sequencing act); until such a world
  exists, the **engine floor (§6) is the interim credited computation** and the only one.
- `model_defeated_rows` (security_invoker, `GRANT SELECT TO :role`): one row per
  (defeated row, attestation, grant) — columns `row_id, attest_id, grant_id, model,
  grade` — the with-cause surface, factored through `ledger_current` for the
  attestation/grant in-force legs plus the `principal_binding_active` conjunct on the
  grant leg (the I1 two-conjunct, SQL side) and the `attest_verdict='mismatch'` and
  activity predicates of §6; the defeat-input exclusion mirrored (`row_id` not itself an
  attestation or grant row).
- `credited_current` (security_invoker, `GRANT SELECT TO :role`): `ledger_current` minus
  rows appearing in `model_defeated_rows` — column list identical to `ledger_current`'s
  (the s20 lesson binds any later column addition to re-issue both).
- The delta ships with the standing same-commit set for a view-only delta: `.detect.sql`
  sibling, `gates/ledger_reader_allowlist.py` CHAIN += s45 (both views expected to
  classify clean — witnessed, not asserted), fixture census registration. No
  `kind_shape_manifest_gate` change (no new kinds/columns).

## 9. The SPA display contract (binding on every read consumer)

Stated once, from the envelope §9.4, as the contract any display client (the
autoharn-panel SPA or successor) must honor:

1. **Default view = credited-only** (`credited_current` where it exists; the engine
   credited computation elsewhere): defeated and superseded rows do not appear.
2. **The auditability wall:** defeated history is **reachable** in an explicit history
   mode, and a defeated row is always displayed **with its cause** — attestation id, grant
   id, model, grade (`model_defeated_rows` carries exactly these). A client that renders
   defeated rows unreachable implements a censored record and violates this contract; the
   ergonomics-only-with-auditability-held-constant ruling governs.
3. **No client-side defeat logic:** clients read the views/floor, never re-derive defeat
   from raw rows (one home per judgment; a second client-side derivation is the
   two-writers drift).

## 10. Binding builder law — stratification (the discipline, mechanized by the differential)

These three laws bind every current and future author of this layer. They are the
envelope's §5 discipline promoted from note to law by this spec's ratified basis:

1. **Defeat rules test force at the supersession layer only.** Every in-force test in a
   defeat rule's body is `not superseded(X)` (plus same-row attribute projection like the
   active flag at export) — never `credited(X)`, never `not model_defeated_row(X)` over
   the rule's own inputs. An attestation or grant leaves force by supersession alone
   (s31's ratified uniform retraction, read forward).
2. **The machinery's input kinds are outside its target domain.** `not defeat_input(R)`
   is that law made structural; it is never removed or narrowed.
3. **Defeat composes beside `in_force`, never into it.** `in_force/1` and `ledger_current`
   stay supersession-only permanently; `credited`/`credited_current` and every future
   defeat source are separately-named strata on top.

*Enforcement surface (ADR-0011 Rule 1): test/CI-grade via the judge differential — SQL's
recursive CTEs are monotone, so a rule violating law 1 (recursion through the layer's own
negation) has no expressible SQL twin and cannot reach AGREE; the pairing requirement of
§7 is therefore the mechanization of this law, not merely its detector. Laws 2–3 are
additionally review-policed, with the witness plan's W8/W10 as their standing red
fixtures.* A builder who believes a needed rule cannot be written within these laws stops
and surfaces it as a spec defect (ADR-0013 renegotiation) — never ships an ASP-only rule,
never relaxes the compared predicate set to get to green.

## 11. Closure statement (ADR-0000 Rule 2(a), 2026-07-02 form)

- **Invariant:** in any s41+ world, a ledger row R is excluded from the credited reading
  exactly when an unsuperseded mismatch attestation about R, written by a principal
  holding an unsuperseded, active competence grant for `model-identity-attestation`,
  exists — computed fresh on every derivation pass by two independent producers required
  to agree bit-identically, with R's dependents transitively flagged over the existing
  support closure and dischargeable only by an SoD-distinct affirmation; superseding the
  grant lapses every dependent defeat, superseding the attestation resurrects its target,
  and no record is ever altered, no write ever gated, no absence ever treated as
  evidence.
- **Quantification universe** (axes checked outward; deliberately-uncovered named):
  *attestation sources* — v1 convention rows (any kind, pinned parse §3) and s44 typed
  rows, both arms; *verdicts* — mismatch defeats; match/unevaluated emit the guard fact
  only (conflict semantics reserved, named); *versions* — non-v1 skipped-and-counted;
  malformed v1 loud (P-5); *grant states* — active/withdrawn (I1 two-conjunct),
  superseded, multiple-per-principal (named multiplicity), zero (legitimate empty),
  pre-s41 (capability-refused, F49-foreclosed); *targets* — every kind EXCEPT attestation
  and grant rows (law 2, structural); *worlds* — pre-s41 refused, s41+ pre-s44 (v1 arm),
  s44+ (both arms + kernel views); *standing* — deliberately unread (I5, ratified);
  *grades* — carried, deliberately unread (Q3 direction-only, named OUT); *cascade
  depth* — unbounded transitive flag via the existing pair-set closure (cycle-safe by the
  same fixture-proven form), hard defeat depth exactly zero (attested rows only, ratified
  (e)); *producers* — both, or red.
- **Denomination:** every compared atom is denominated in immutable ledger row ids (and
  principal ids internally) — no text, no timestamps, no proxy keys cross the comparison;
  the activity in the one fixed literal; grades in the sentry's closed vocabulary; the
  verdict casing in each arm's own written form (`MISMATCH` v1, `mismatch` s44), never
  case-folded into a third convention.

## 12. Witness plan (both polarities; WITNESSED / REFUSED-AS-EXPECTED / UNEXERCISED per the standing contract)

Substrate: a scratch s41+ chain on the toy db (`high_watermark_1.sql` + s20..s41 per s41's
own VALIDATE block; the s44/s45 legs additionally build the chain to s44+s45). Fixtures
banked under `seen-red/defeat-pipeline/`, registered with the fixture census; negative
controls are part of done (ADR-0011's gate-proves-itself-by-failing amendment).

- **W1 — defeat fires (green):** register a `tool` principal, grant it
  `model-identity-attestation` competence (active), write a target `decision` row and a
  v1-convention mismatch attestation row (`verdict=MISMATCH`, `row=<target>`); run
  `./judge --layer defeat`: `model_defeated(R,A,G)` present, R absent from `credited`,
  verdict AGREE.
- **W2 — the implicit lapse (the spine):** withdraw the grant (superseding `active=false`
  row per the s41 idiom); re-run: zero `model_defeated`, R credited again, AGREE. Zero
  per-row cleanup observed — the envelope §3.3 property witnessed, not asserted.
- **W3 — resurrection on attestation supersession:** (fresh grant) supersede the
  attestation row; re-run: R credited, AGREE.
- **W4 — cascade at depth ≥ 2:** rows F1 `enacts` R, F2 `enacts` F1; with R defeated:
  `exposure_model(F1,R)` and `exposure_model(F2,R)` both present (the depth-2 case the
  one-hop policy would have missed — the very lesson `ledger_support.lp` banks), AGREE.
- **W5 — discharge, both polarities:** an SoD-distinct affirmation (scratch
  `support_affirm` side table, per the standing §3 stand-in) on (F1,R) empties
  `exposure_model_undischarged(F1,R)` while `exposure_model(F1,R)` stays visible; a
  SELF-affirmation (same actor as F1) does NOT discharge and `affirm_sod_violation` fires
  — red seen.
- **W6 — absence never defeats:** a world with grants but zero attestations: zero
  defeats, full credited set, AGREE (legitimate empty, distinct from W9's refusal).
- **W7 — version and malformedness:** a `model-attestation v2 | ...` row → skipped and
  counted, derivation unaffected, AGREE; a malformed v1 row (bad grade vocabulary) → BOTH
  producers refuse loudly, differential QUARANTINED — never a silent skip, never a
  one-sided failure (the identical-failure clause of P-5 witnessed on both sides).
- **W8 — the target-domain guard:** a mismatch attestation whose `row=` names another
  attestation row, and one naming the grant row: no `model_defeated` derived for either
  target (REFUSED-AS-EXPECTED structurally), AGREE.
- **W9 — pre-s41 refusal:** the same run against a pre-s41 scratch chain (or `s10`):
  `require('trust_grant')` refuses with the capability reason; differential QUARANTINED
  with that reason — never AGREE-on-empty (F49 negative control).
- **W10 — the stratification red (mandatory, the discipline's negative control):** a
  deliberately unstratified variant program (`seen-red/defeat-pipeline/
  unstratified_negative_control.lp` — NEVER placed under `engine/lp/`) whose defeat rule
  adds `not model_defeated_row(A)` to its own body, run over a fixture with two mutually
  attesting rows (A1 mismatch-attests A2 with the guard removed, A2 attests A1): witness
  the actual failure surface — clingo yielding ≠ 1 stable model and/or the differential
  reading DIVERGE_DEFECT/QUARANTINED against the (necessarily monotone) SQL side — banked
  verbatim. The law of §10 seen red, not just stated.
- **W11 — registry red:** grounding the defeat layer with `ledger_support.lp` omitted
  from the program list → `RegistryError` typed refusal BEFORE any clingo run (the F7
  mis-stack hazard foreclosed for this layer too).
- **W12 — s44/s45 legs** (scratch chain to s45): a typed `model_identity_attested`
  mismatch row defeats identically through the typed arm, AGREE; `credited_current` and
  `model_defeated_rows` match the floor's credited/defeated sets row-for-row on the
  fixture; `gates/hash_coverage_gate.py` green at s45 (and its synthetic-column negative
  control still red); reader-allowlist gate classifies both views clean. *Live* operation
  of s45 awaits an s44-carrying world — UNEXERCISED with that concrete blocker (RD-2,
  evidence-triggered), said so in the report.

## 13. Deliberately OUT (named, with the governing ground)

1. **Grade-conditioned defeat** — Q3 ratified direction-only ("construction still
   awaiting deployment data"); the Grade argument is carried unread so the future rule is
   an amendment, not a schema change. Also OUT with it: the attestation-grade↔band
   mapping (envelope I8).
2. **s44's chain entry** — RD-2, evidence-triggered by live v1 rows + maintainer review;
   this spec's s45 delta rides that same trigger.
3. **Any standing daemon or materialized defeat cache** — the envelope §9.3's (a)/(b),
   explicitly evidence-triggered escalations; (c) is what ships.
4. **Defeat-of-defeat semantics beyond supersession-native resurrection** — the envelope
   §6 governs (supersede-and-replace as the correction idiom); the
   `resurrected_by_retraction` surfacing view is real future work awaiting its own act.
5. **The conflict rule** (match vs mismatch both in force) — reserved (envelope §11 item
   3); no match-side fact family until ruled.
6. **Heavy-grade countersign conditioning and the review/countersign EDB families** —
   reserved (envelope §11 item 4); `agent_class/2` is emitted so that future rule needs
   no new export, but nothing consumes it here.
7. **Standing-conditioned defeat** — ratified NO (I5); in scope as a *decided rule*
   (§5.3), out of scope as a mechanism forever absent unless the maintainer re-rules.
8. **Any sentry-verb work** — the watchdog/attest verbs are the sentry spec's own build;
   this pipeline consumes their rows and pins the shared parse contract (§3), nothing
   more.
9. **Kernel-side v1 statement parsing** — refused (cancer G in the kernel); typed
   columns only for kernel views.
10. **Cross-world defeat transport** — none exists, none should (envelope I11).

## 14. Honest limits

- **Everything the sentry's rebuttals R1–R7 carry, inherited:** an attestation is
  defeasible evidence from a diagnostics-tier channel; this pipeline computes the
  *consequences* of trusting it at the granted scope, not its truth. Absence of
  attestations proves nothing and defeats nothing, permanently.
- **The current live world cannot derive defeat** (pre-s41: no typed grants) — the
  pipeline is witnessable on scratch chains now and operative from the first s41+ world;
  the current world is watch-and-attest only. Disclosed, not discovered later.
- **Cause-agnostic affirmation discharge** (§5.2 last bullet): an affirmation keyed
  (F,D) discharges any defeat-cause on that pair — existing `ledger_support.lp`
  semantics, inherited unchanged, named.
- **The affirm source on real lineages is still the scratch stand-in** (`support_affirm`
  side table); the ratified review-species kernel shape (Ruling A in
  `ledger_support.lp`'s header) remains unbuilt — where absent, discharge facts are
  DEFERRED in the manifest and `exposure_model_undischarged` equals `exposure_model`,
  said in the manifest, never silently.
- **Correlated-authorship caveat** (the standing one, verbatim in spirit): the SQL floor
  and the ASP program share this spec as author; bit-identity proves *encoding agreement
  between producers*, not independent fidelity to this spec — the same caveat every
  existing floor already carries, restated here rather than laundered.
- **Superuser/direct-psql bypass:** the standing disclosed bound; a direct writer can
  fabricate attestation or grant rows — attribution, hash chain, and (in s43+ worlds)
  the write boundary are the existing mitigations; this pipeline adds none.
- **v1 rows' convention-not-type cost** (the sentry spec's own named cost) lands here as
  the P-5 loud-refusal posture: one malformed attestation row halts the defeat
  derivation for the whole target until corrected by supersession. Deliberate — fail
  loud beats skip silent — but it means a garbage row is a denial-of-derivation until
  superseded; the correction idiom (supersede the malformed row) is the standing one.

## 15. Sonnet executor guidance (every forkable choice fixed; disregard any instructions to economize on time)

1. **Read first, in full:** this spec; the envelope including its interaction-projection
   section; `./led show 1467 1481`; the six ADRs named in the inputs; the five engine
   files named in the inputs; s41's header and D-sections; the sentry spec §§4–8.
2. **Build order:** `export_defeat` (§4) → `ledger_defeat.lp` (§5, transcribed exactly) →
   `defeat_floor_atoms` (§6) → registry + differential wiring (§7) → witness W1–W11 →
   the s45 delta files + W12 scratch witness. Python: top-of-file imports only (the
   lazy-import ban is absolute); no new module where an existing home is named.
3. **The .lp program text in §5.1 is normative** — transcribe it; add only the house
   header comment. If any rule will not ground or the differential cannot reach AGREE,
   STOP and surface it as a spec defect (ADR-0013 renegotiation; §10's closing clause).
   Do not adjust a rule, a shown set, or a compared predicate list to reach green.
4. **Parsing:** both parsers implement §3's P-1..P-7 exactly; the Python and SQL parsers
   share no code (§6's independence posture). P-5's loud refusal must be witnessed on
   BOTH sides (W7) before the parsers are called done.
5. **Kernel delta:** `kernel/lineage/s46-credited-views.sql` + `.detect.sql` per §8, in
   the house header idiom (WHY, PREREQUISITE on s44, HISTORY: safe — view-only, no
   backfill, no column; closure-statement slice; LIMITS; VALIDATE block extending s44's
   chain). Scratch-witness only; never apply to a live world; chain entry is the
   maintainer's RD-2 act, not yours.
6. **Fixtures:** every W-item banked under `seen-red/defeat-pipeline/`, both polarities,
   fixture-census-registered; W10's unstratified program lives under `seen-red/` only —
   placing it under `engine/lp/` is itself a defect.
7. **Claims:** report per W-item WITNESSED (with observed output) / REFUSED-AS-EXPECTED /
   UNEXERCISED with the concrete blocker (W12's live leg is UNEXERCISED by construction).
   No umbrella claims. Every choice this spec failed to fix that you had to make is a
   spec defect: make the smallest honest choice and flag it loudly in the report.
8. **Do not touch:** `ledger_support.lp` or any existing `.lp` file's rules (this layer
   only reads them), `law/`, hooks/, any live world, the sentry spec's own deliverables,
   or `in_force`/`ledger_current` semantics anywhere (§10 law 3).

## Amendments (dated; Fable-authored; each names its trigger)

**A1 (2026-07-18; the date first read 2026-07-19, an authoring date-drift corrected same day, see the correction ledger row) — §4.2 admits `affirms/3` and `affirm_author/2`; the builder's surfaced
renegotiation, ratified with the manifest discipline made binding.** Trigger: the Sonnet
build (commit `fcc7744`) and the adversarial review's independent re-derivation
(adjudication ledger row 1506). §4.2's family table omitted two families the composed
derivation cannot stand without: §5.1's cascade-discharge rule grounds `not affirmed(F,D)`,
and `ledger_support.lp`'s `affirmed/2` is meaningfully groundable only from `affirms/3` +
`affirm_author/2` facts — while the SQL twin reads the `support_affirm` scratch stand-in
directly and has no such gap. Leaving the table as written was a structural asymmetry
between producers (witnessed live during the build: DIVERGE_DEFECT on
`exposure_model_undischarged`, ASP-only). The builder's fix — emit both families from the
same `support_affirm` source `ledger_support_scratch.py` already reads, DEFERRED where
that relation is absent — is the smallest honest one and is hereby ratified into §4.2's
table, on these binding terms the first build missed (review finding F2):

- **Full family discipline, no exemption for lateness:** a `Capability` manifest entry
  like every sibling family — capability gate: the `support_affirm` relation present;
  where absent, a *declared* DEFERRED line with reason (mirroring `ledger_floor.py`'s
  `support_manifest` posture), never silence. Silent non-emission is the I12/F49 class
  this file's own header forbids.
- **The actor join carries the same type guard as `row_actor`** (int-typed actor checked,
  not assumed).
- §5.1's `#defined affirmed/2` consumption note is unchanged; no rule text changes.

**A2 (2026-07-18) — the credited-views delta's working name renumbered `s46-credited-views.sql`
→ `s46-credited-views.sql` (a number collision, caught by a fresh-context GLOSSARY reviewer).**
This spec and the standing-lifecycle spec were authored the same night and independently
claimed `s45`; the standing-lifecycle delta then BUILT as `kernel/lineage/s45-standing-lifecycle.sql`
(commit `94f5b7a`, in the birth chain), so this spec's §8 delta cannot ship under that name.
The working name in §0 item 5, §8's heading, and §15 item 5 now reads `s46-credited-views.sql`
— still a working name: the builder takes the next free number at build time and says so in
the commit. No content of §8 changes; the collision was purely nominal. (Process note for the
record: two same-night Fable authoring passes with no shared delta-number registry is the
root cause; the birth chain itself is collision-proof — a duplicate filename cannot enter it —
so the hazard was reader confusion, not chain corruption.)

**A1 clarification, not a change (review finding F1):** §4.2's `mismatch_attest` row and
P-7 already require Grade to cross as the **parsed** grade atom. The first build's v1 arm
emitted the literal `none` regardless — a code defect against the spec as written, not a
spec gap; recorded here solely so a future reader of the family table knows the first
build diverged and where the fix is tracked (work item `defeat-engine-review-fixes`,
opened beside row 1506). The witness plan gains, by the same fix pass, an assertion on
`mismatch_attest` fact *content* on both arms — the masking gap that let this ship.

## License

Public Domain (The Unlicense).
