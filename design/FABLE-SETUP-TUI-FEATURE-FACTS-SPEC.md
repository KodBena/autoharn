# Setup TUI — feature facts and the durable-decisions catalog

<!-- doc-attest-exempt: build-basis spec; attestation rides witnessed delivery -->

**Status: Fable-authored 2026-07-19, build basis. Commission: ledger row 1714
(maintainer, verbatim there). Extends [FABLE-SETUP-TUI-SPEC.md](FABLE-SETUP-TUI-SPEC.md),
whose three posture rules and 2026-07-19 out-of-sequence amendment bind everything
here unchanged. A `tools/` product: no kernel/law/serving contact; the one scaffold
touch (CLAUDE.md compilation, §3) rides the TUI's existing driver role over
`new-project.sh`'s outputs, not an edit to the scaffold itself.**

## The two features, in the maintainer's own frame

1. When the operator selects features, a **facts column** states, per feature, the
   standards-conformance aspiration it serves and whether it carries external costs
   or dependencies. (The maintainer recalls four features carrying external
   costs/deps and allows there may be more — §2's enumeration rule treats his
   count as a hypothesis to check, never a spec.)
2. A **small-ish curated catalog of durable decisions at world-creation time**,
   born of witnessed painful experience, selectable at hydration — each selection
   writing real ledger rows through `led` and compiling into the new world's
   CLAUDE.md, so a fresh world's first session starts with the right rules already
   standing rather than re-learned.

## 1. One home for each fact set (ADR-0012 P1; the drift-backstop method applies to itself)

Both features are fact collections that will silently rot if hand-scattered into
screen code. Each gets ONE home module under `tools/setup_tui/`, and each gets a
drift backstop per the FAQ's own five-move method
(user-guide/USER-RECIPES-FAQ.md, "Drift backstops" — this spec is that section's
first deliberate consumer, and the builder cites it in the module headers):

- `feature_facts.py` — the feature-facts registry (§2). Screens render FROM it;
  no screen carries a facts string of its own.
- `durable_decisions.py` — the durable-decisions catalog (§3). The hydration
  screen renders FROM it; CLAUDE.md compilation reads FROM it; no second copy of
  any rule text anywhere.

Backstop shape, per module: where a fact is mechanically derivable (which screens
exist, which ADR files exist, which preflight probes exist), the registry is
CHECKED against the derivation by a census-registered fixture — a registry key
with no live counterpart, or a live counterpart with no registry entry, reads
red. Where a fact is aspirational and not derivable (which standard a feature
serves), the banked-manifest variant applies: the entry carries its citation
(spec file or ADR that names the standard) and the fixture existence-checks the
citation target. No hand list without a backstop; that is the whole method.

## 2. The feature-facts column

Every selectable act the flow offers — the dedicated-db substrate path, the
boundary service, observability (otelcol + watchdog), each hydration item, and
the preflight-probed toolchains (idris2, clingo/ASP, textual/urwid if present) —
gets a registry entry:

- **`aspiration`**: the standards-conformance aim, one line, with citation.
  Known anchors the builder verifies and extends by READING the corpus (specs
  under design/, ORCH-CAPABILITIES.md, the ADRs), not by trusting this list:
  NIST SP 800-63 (principal surface, per FABLE-PRINCIPAL-IDENTITY-SPEC),
  NIST AU-family audit-supporting evidence at diagnostics tier (OTel sentry,
  per FABLE-OTEL-SENTRY-SPEC), ARMA/ISO 15489 essential-records
  (artifact store, per FABLE-ARTIFACT-STORE-SPEC), and the project-wide
  NRC-grade-product posture. A feature with no named aspiration says so
  honestly ("none named; house discipline only") rather than inventing one.
- **`external`**: external costs/dependencies, enumerated concretely: external
  binaries (otelcol, idris2, clingo), Python packages beyond stdlib (fastapi/
  uvicorn for the boundary), network ports, cluster-host operator acts (pg_hba,
  createdb), recurring operator processes (a daemon to keep alive). Features
  with none state `none` explicitly — absence of the fact and absence of the
  entry must be distinguishable.
- **Enumeration rule**: the builder reports the ACTUAL count of features
  carrying external costs/deps, each with its evidence (the import, the probe,
  the spec line). The maintainer's "4, there may be more" is checked against
  that enumeration in the report — WITNESSED per feature, no umbrella.

Rendering: in the numbered-menu fallback the "column" is a facts line under each
item (`aspiration: ... | external: ...`), shown at the point of selection —
substrate choice, boundary/observability screen entry, hydration checkboxes.
The screen shows facts BEFORE the operator commits the act, since the whole
point is informed selection.

## 3. The durable-decisions catalog

Each catalog entry is a struct with five fields, all mandatory:

- **`slug`** — stable identifier.
- **`rule`** — the standing-rule text, written to survive a fresh reader
  (ADR-0017 bar), since it becomes both a ledger row and CLAUDE.md prose.
- **`why`** — the painful specimen, cited (ledger row id and/or incident,
  e.g. the obligate amplification incident, the Block D undocumented-merge
  precedent). An entry without a witnessed specimen does not enter the catalog —
  "borne out of our painful experience" is the admission criterion, verbatim.
- **`hydrates`** — the exact `led` verb + statement the selection writes
  (decision rows; the statement embeds the rule text and its why-citation).
- **`claude_md`** — the fragment compiled into the new world's CLAUDE.md.

**Initial catalog — 7 to 15 entries, distilled from the prior art of BOTH
projects (amendment per commission row 1716, superseding this spec's original
three-plus-proposals shape):** the maintainer's directive is that the catalog
recover and distill the durable decisions "we've had most success with in this
project and autoharn-panel." The builder therefore MINES two evidence sources,
read-only: this repo's ledger (standing-rule decision rows via `./led`) and the
autoharn-panel submodule's record (`tools/autoharn-panel` — its CLAUDE.md,
ledger exports, and docs; READ-ONLY, the never-touch-the-panel rule covers
writes, not evidence reading). Every entry still meets the admission criterion
(a witnessed painful-or-successful specimen, cited); the distillation picks the
rules whose adoption demonstrably changed outcomes, not everything ever ruled.
The maintainer-named anchors below come first; the report lists every mined
entry with its specimen so the maintainer can prune — 15 is a hard ceiling,
small-ish remains the design property.

1. `makespan-scheduling-by-mandate` — logistics/makespan scheduling is used by
   mandate; the session orchestrator can see the overarching goal and ensures
   the right rules are hydrated on first session start (the maintainer's own
   wording, row 1714). Per row 1716's clarification, the mandate's substance is
   the autoharn-panel form: a robust-though-soft specification **requiring
   cosigned decomposition of the task** — the builder reads the panel's actual
   mandate text (read-only) and carries its cosigned-decomposition requirement
   into this entry's `rule`/`claude_md` verbatim-in-substance, not from memory.
2. `drift-backstops` — the orchestrator is softly obligated to follow the FAQ's
   drift-backstop method for anything that goes quietly stale (why: the FAQ
   section's own fourteen-instance evidence base).
3. `adr-adoption` — NOT one entry but a submenu: the ADR list is DERIVED from
   `law/adr/*.md` at runtime (title line read from each file), never a hand
   list; the operator selects which ADRs the new world adopts; each selection
   hydrates one row naming the ADR by number and title. (This absorbs and
   supersedes the current free-text `adr_corpus` hydration item.)

**"Obligates (softly)" is defined, not vibes:** a selected entry writes decision
rows and compiles CLAUDE.md prose — standing guidance a session reads and the
record shows it adopted. It does NOT write kernel `obligate` rows in v1: the
obligate amplification footgun (led.tmpl's own teaching, row 1640) is exactly
the painful experience this catalog exists to encode, and an idiot-proofing
surface must not hand a fresh operator a loaded obligation trigger at birth.
Kernel-obligation hydration, if ever wanted, is a later maintainer-ratified
extension; named out of v1.

**Relation to the existing screen-8 items:** `adr_corpus` and `makespan_pointer`
are absorbed into catalog entries (their free-text prompts retired);
`fork_provenance` and `role_charters` remain as-is — they are per-world facts,
not durable decisions, and stay outside the catalog.

## 4. CLAUDE.md compilation

The selected entries' `claude_md` fragments are compiled into the new world's
CLAUDE.md between explicit generated-section markers
(`<!-- BEGIN COMPILED DURABLE DECISIONS (setup_tui) -->` / matching END), with a
header line naming the catalog module as the source and the regeneration path.
Rules: the compilation NEVER touches text outside its markers; on a fork-copy
destination (the CLAUDE.project.md preservation move) the compiled section is
appended without disturbing the preserved content; running the screen again
replaces only the marked section (idempotent). The catalog is the one home —
CLAUDE.md's section is derived output, and its header says so, so no future
reader hand-edits generated text (the two-home hazard, named and refused).

## 5. Witnesses

- **WF1** feature-facts rendering: a scripted run shows the facts line for at
  least the substrate, boundary, observability, and two hydration items —
  including every feature the enumeration found to carry external costs/deps,
  each with its citation intact (link/existence-checked).
- **WF2** facts-registry drift backstop red leg: a synthetic registry with a
  key for a nonexistent feature (and, separately, a live feature stripped from
  a synthetic registry) reads red in the census fixture.
- **WD1** catalog end-to-end on a scratch world: scripted selection of
  makespan + drift-backstops + two ADRs → real `led` rows written (ids echoed,
  content checked), CLAUDE.md compiled section present with exactly the
  selected fragments, torn down zero-residue.
- **WD2** declined entries: SKIPPED in the checklist, zero rows, zero
  fragments — absence witnessed, not assumed.
- **WD3** ADR-menu derivation: the rendered ADR submenu equals the live
  `law/adr/*.md` glob (count and titles compared mechanically in the fixture).
- **WD4** CLAUDE.md idempotence + preservation: re-running hydration replaces
  only the marked section; a fork-destination's preserved CLAUDE content is
  byte-identical outside the markers.
- **WD5** out-of-sequence entry (the parent spec's amendment binds): hydration
  entered via `--start-at hydration` against a destination lacking `./led`
  refuses legibly (existing behavior — re-witnessed, since this build touches
  that screen).

## 6. Build conditions

All new/changed code under `tools/setup_tui/` plus the census fixture under
seen-red/; the existing scripted smoke fixture extended, not forked. No edits
to bootstrap scripts, kernel, law, serving, hooks. Python, top-of-file imports;
gates apply (incl. the interpreter-boundary lint: catalog/registry values that
reach `led` argv or CLAUDE.md text cross as argv-list elements / plain writes,
and anything operator-typed passes the package's existing closed-alphabet
validators). Doc-currency at the seam (row 1699): the FAQ's setup-TUI entry (or
its named deferral) and FABLE-SETUP-TUI-SPEC's flow section get the two
features reflected in the same work item. Per-claim witnessing; zero residue.
