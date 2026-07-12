# ORCH-SPEC-TASK-TAXONOMY — declared taxonomies and taxon-scoped task policy

Audience: orchestrator (design spec; implementation stages are Sonnet-executable per §7).
Status: Fable-authored 2026-07-12, from the maintainer's same-afternoon ask (tracker
work item `task-taxonomy-spec` — run `./led show <id>` at the repository root to read
it). The ask is structural support for a decomposition discipline settled at the
outset: boundary identification required, work split along boundaries, and no agent
codes across a boundary. This spec generalizes that discipline so the framework is
*polymorphic in taxonomy* — the policing machinery never knows what a boundary means,
only that one was declared. This is a
companion to [ORCH-SPEC-DECOMPOSITION-POLICY.md](ORCH-SPEC-DECOMPOSITION-POLICY.md)
(which deliberately left its one-boundary-per-task splitting criterion at
reviewer-judgment grade) and reuses that spec's declaration pattern and the deontic
register of [ORCH-SPEC-RESOURCE-ACCOUNTING.md](ORCH-SPEC-RESOURCE-ACCOUNTING.md) §3.

## 1. The problem, and the worked specimen the maintainer already owns

A boundary discipline enforced by prose is enforced by hope. The living specimen is in
the maintainer's own omega project: `backend/qeubo/`'s README declares that
public-domain code MUST consume the MIT-derivative package through its documented API
and MUST-NOT read its `vendor/`/`runtime/` sources (a licensing boundary with a
declared crossing interface) — policed today by a README paragraph. The same *shape*
recurs under different meanings: architectural layers (omega's own import-direction
rule), assurance levels, data-sensitivity zones. Human organizations enforce such
boundaries socially (module ownership, review approvals); an agent workforce has no
social layer, so the discipline must be structural or it is absent.

## 2. Standards ancestry, stated honestly

The artifact-level half of this discipline is established certification substance
under other names: ISO 26262-9's ASIL decomposition (decompose onto elements, justify
their independence, analyze freedom from interference), DO-178C robust partitioning
and DO-297's module boundaries, IEC 61508's non-interference between elements of
different integrity levels, Common Criteria's TSF boundary as the first evaluation
act, and interface control documents as managed configuration items. The
worker-binding half — no *agent* may code across a boundary — appears in no
certification standard this spec's author knows of; it lives in industrial practice
(code ownership, approval domains). This spec mechanizes it anyway, for the stated
reason above: the social enforcement the standards silently assume does not exist
here. A deployment citing this spec to a regulator should present §'s 3–5 as an
implementation of the decomposition/partitioning expectations and the worker-binding
rule as a conservatism beyond them.

## 3. Declaring a taxonomy — rows, like everything else

A taxonomy is declared where everything attributable lives: ledger rows on the
deployment, one row per taxon, statement-prefix convention (version 1, no kernel
change — the registry's stage-1 precedent):

```
taxon: <TAXONOMY> | <TAXON> | <PATTERNS> | <GLOSS>
interface: <TAXONOMY> | <ARTIFACT-PATTERN> | <GLOSS>
```

- TAXONOMY — the scheme's name (`license`, `arch-layer`, `sensitivity`); a deployment
  may declare several, and one artifact may carry a taxon in each.
- TAXON — the class within it (`pd`, `mit-derivative`; `domain`, `api`).
- PATTERNS — path globs assigning artifacts to the taxon, the same assignment
  mechanism `governed_files.json` already uses for the change gate's subject scope.
- `interface:` rows declare the sanctioned crossing points (the ICD analog): artifacts
  that MAY be referenced from outside the taxon that contains them — for the omega
  specimen, the documented API module but never `vendor/**`.

Intake validation clones the `resource:` validator's structure (field count,
whitespace normalization, refusal that teaches); `./pickup` gains a TAXONOMIES
section; superseding a row is the ordinary edge. The omega specimen, transcribed:
`taxon: license | mit-derivative | backend/qeubo/** | upstream qEUBO derivative` plus
`interface: license | backend/qeubo/__init__.py | the documented public surface`.

## 4. The polymorphic predicates — what the engine checks without knowing why

Policies attach to taxonomies through [ORCH-SPEC-DECOMPOSITION-POLICY.md](ORCH-SPEC-DECOMPOSITION-POLICY.md)'s
existing `task-policy:` grammar, with criteria that name a predicate and a taxonomy
parameter. Version 1 defines three predicates, each purely structural:

- `single-taxon-task(T)` — a work item's touched-artifact set (from the invocation
  journal and mutation observer, the action-stream basis) maps into at most one taxon
  of T, interfaces excepted. The maintainer's "work split according to boundaries."
- `no-cross-taxon-write(T)` — a session whose claimed work item sits in taxon X of T
  does not Write/Edit artifacts assigned to a different taxon of T. The maintainer's
  "no agent may code across boundaries."
- `crossing-via-declared-interface(T)` — an artifact in one taxon that references an
  artifact in another (version 1: an import line or path literal, textually matched —
  the same honestly-denominated matching the accounting spec uses for REACH) hits only
  `interface:`-declared artifacts.

The predicates quantify over declared taxonomies: adding a taxonomy is a ledger act,
never an engine change — the polymorphism the maintainer asked for. In the ASP half
the whole mechanism is a handful of rules over `assign(Artifact, Taxon, Taxonomy)`
facts; the SQL floor re-derives independently; the differential must AGREE
(marriage-grade, Part 3's conventions wholesale).

## 5. Enforcement grades — the policing-column ratchet, exercised

- **Write-time (gate)**: `no-cross-taxon-write` extends the change gate exactly the
  way the [`decomposition_review`](../GLOSSARY.md#decomposition-review-blocker) mechanism
  (`hooks/pretooluse_change_gate.py`) did — a taxon-scoped permit-to-work: DENY (enforce) or
  journal (observe, default) a Write outside the claimed item's taxon, teach-text
  naming the taxonomy row and the declared interfaces. Additive refusal, fail-safe
  class, apparatus-switched per world.
- **Audit (post-hoc)**: all three predicates as an `./audit` family over the journal —
  catches what the gate's attachment points cannot see (bash-mediated writes are
  visible via the mutation observer with its own disclosed residues).
- **Reviewer judgment, irreducibly**: whether the taxonomy itself is *well-drawn* — no
  machine knows if the boundary is in the right place. The decomposition countersign
  cites the taxonomy rows it checked the split against, the same criterion-citing
  trail as the policy spec's §6.

The payoff the policy spec anticipated: `one-boundary-per-task` upgrades from
`REVIEWER-JUDGMENT` to `POLICED (gate)`/`POLICED (audit)` **exactly when a deployment
declares a taxonomy** — the derived policing column moving because reality moved,
never by decree.

## 6. Honest limits

- Path-glob assignment is textual, like REACH matching: a file moved without its
  taxon row updated is misassigned until the audit's unassigned-artifact report (every
  governed artifact matching no taxon of a declared taxonomy is listed, never silently
  ignored) surfaces it.
- `crossing-via-declared-interface`'s reference detection is textual in version 1
  (imports and path literals); dynamic dispatch and data-plane coupling are invisible
  and named so.
- A well-formed taxonomy can still be a *wrong* taxonomy; §5's third grade is
  load-bearing, not decorative.
- Declaring no taxonomy declares no obligation: every predicate is VACUOUS on a
  deployment with zero `taxon:` rows — adoption is opt-in, per the house rule that an
  empty registry is honest.

## 7. Implementation routing (all stages Sonnet-executable from this spec)

- **Stage A** — `taxon:`/`interface:` intake validation + pickup TAXONOMIES section +
  a USER- template page with the omega licensing specimen as the worked example
  (marked as one maintainer's example, per the blessed-table convention). Seen-red
  both polarities; census.
- **Stage B** — the audit family: ASP + SQL floor + differential + `./audit` flag
  (next free exit code; note the exit-6/7 collision precedent — one exit, one owner,
  checked at authoring). Includes the unassigned-artifact report.
- **Stage C** — the write-time gate extension (change gate, taxon-scoped permits),
  observe default, both polarities witnessed, apparatus-registered.
- **Stage D** — `task-policy:` criteria wiring: the predicate-parameterized criteria
  land in the policy template; the policing column's derivation learns the new
  mechanism names.

## Closure statement (in the spirit of [ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)'s closure discipline — the universe-and-deliberate-absences parts; its denomination-check field concerns defect-class foreclosures and does not apply to a design scope)

The universe is the maintainer's ask: outset-settled boundary discipline, generalized
to taxonomic task policing, polymorphic in taxonomy. Declaration is closed by §3;
polymorphism by §4 (predicates quantify over taxonomies; new taxonomy = ledger act,
zero engine change); the three named clauses of his discipline map one-to-one onto
the three predicates; enforcement and its honest grades by §5; the standards question
he asked is answered in §2 with the correction he invited. Deliberately absent, named
where they fall: semantic understanding of any taxonomy (§4), non-textual reference
detection (§6), any judgment that a declared taxonomy is well-drawn (§5, §6), and
kernel columns before the deferred `resource` kernel step (s27; see
[ORCH-SPEC-RESOURCE-REGISTRY.md](ORCH-SPEC-RESOURCE-REGISTRY.md) §2) every sibling
spec defers to. No obligation
exists for deployments that declare nothing (§6).
