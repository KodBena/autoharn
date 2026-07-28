# Methods — recipes

<!-- doc-attest-exempt: relocation-class mechanical move (work item faq-refactor-by-concern, ledger row 185 adjudication, 2026-07-28) -- the content below is byte-preserved prose moved verbatim out of user-guide/USER-RECIPES-FAQ.md (commit `178ec789439044bebb664e7374c2be757d064d11`; sections named in the provenance line above), plus mechanical `../` link-depth repairs and named cross-file link/anchor rewrites for content that relocated to a sibling factor file; no other prose was reworded (ADR-0020's clause 1: a residue disposition and a link gate are the mechanical floor, never a substitute for a cold meaning-preservation read -- that read DID run, by a fresh-context Agent invocation distinct from the session that performed the move; see this work item's execution report for the per-file outcome). The ADR-0017 A:B:C legibility loop is a SEPARATE read this session did not run: the coordinator schedules it after merge, per this work item's adjudication conditions (ledger row 185). Waived here only to unblock this commit. Removal condition: strike this marker and run the real ADR-0017 A:B:C loop next time this file is touched for content, not just link repair. -->

*Factored out of [`user-guide/USER-RECIPES-FAQ.md`](../USER-RECIPES-FAQ.md) at commit
`178ec789439044bebb664e7374c2be757d064d11`, sections "Workflow patterns", "Capturing errors so they cannot quietly recur (ADR-0000
/ ADR-0011)", "Drift backstops (one generic method for anything that goes quietly stale)",
"Operating rhythm", and "Recusal and independent RCA (a conflict-of-interest method harvested
downstream)"; byte-preserving (mechanical `../` depth repairs and named cross-file link
rewrites only).*

**Charter:** disciplines with no mechanism behind them — every section here states its own
review-only status in its own text ("nothing gates, audits, or refuses on ... and nothing
will"; "the discipline exists, it is mostly typing rather than tooling"; "a backstop checks the
DECLARED correspondence dimension only ... review-only"; "no gate checks that a conflicted
orchestrator actually recused"). Does not belong: anything a gate, hook, or kernel trigger
enforces. **Note on the duplicate paragraph (residue, filed not fixed):** lines duplicating the
setup-TUI feature-facts/durable-decisions facts already stated in SETUP-AND-SCAFFOLD.md survive
verbatim inside this file's "Drift backstops" section, exactly as they stood duplicated in the
original page — see this work item's execution report, and the proposal's own §4 item 5, for
the disposition (a follow-on fix, not this move's to make).

---

## Workflow patterns

**I want a workflow to iterate until clean — can an agent spawn sub-agents and loop on its
own output until a defect list comes up empty?**
This recipe now has a formal shape too — both live in
[USER-SHAPED-RECIPES-FAQ.md](../USER-SHAPED-RECIPES-FAQ.md#the-abc-fresh-context-fix-point-loop)
(`design/workflows/faq-abc-fixpoint-loop.toml`, the first factored specimen).

**My workflow script just crashed / hung / did something baffling — is this a known
shape?** Maybe — check first. Five gotchas have each bitten this project's own
workflow scripts more than once (args arriving as an already-parsed JSON value rather
than a string needing a parse, model-pinning on every dispatch call, the ban on
calling `Date.now()`/`Math.random()` inside a script a durable workflow runtime may
resume or replay from a checkpoint — either call can return a different value on
resume and silently steer the script down a different path than it took the first
time, stall-vs-crash as opposite-cause failure shapes needing opposite diagnoses, and
a workflow run's own journal (its append-only `.jsonl` log of what each round did)
carrying `result` fields that are repr-strings, not nested JSON) — four with a dated
incident on record, one (the Date.now()/Math.random() ban) stated as a general hazard
with no located incident yet — each with a stated fix regardless. Read
[ORCH-WORKFLOW-SCRIPT-GOTCHAS-RECIPE.md](../ORCH-WORKFLOW-SCRIPT-GOTCHAS-RECIPE.md)
before writing a new workflow script, or when one fails in an unfamiliar way.

**I have a large batch of independent work units to dispatch — is there a standing
recommendation for how to parallelize them instead of just running them one after another?**
Yes — **standing recommendation** (maintainer directive, 2026-07-14): use
`tools/makespan-scheduler/` (makespan = the total time to finish an entire batch of jobs, the
quantity the scheduler minimizes; vendored 2026-07-14, split into its own published repository
and converted to a git submodule 2026-07-15) for any large-scale batch of jobs that conflict
only over shared
resources (e.g. two edits touching the same file), rather than defaulting to a hand-picked
sequential order. Claude Code is, functionally, an infinite-server model of work — parallel
agent capacity is cheap to spin up — but the default LLM inclination is still to serialize
work that could safely overlap, which wastes exactly the capacity that is available. Feed the
batch's jobs (id + the resources each one touches + an optional duration) to the scheduler; it
returns a schedule computed by CP-SAT (a constraint-programming solver, OR-Tools' `cp_model`) —
either proven optimal or honestly labeled not — and a
`batches` field — ordered waves of job ids safe to dispatch together — and that dispatch order
is what you actually run, not a re-guess. **The guarantee is conditional, and the condition
matters more than the tool**: the scheduler can only be as correct as the job list it is given,
and it has NO notion of one job's output feeding another job as input (the vendored tool's own
"independent-tasks" scope) — a batch with a real, hidden data dependency fed into it as if it
were a mere resource conflict produces a schedule that looks authoritative and is wrong. Before
treating a batch as ready to schedule, therefore, an independent countersign of the job list
itself (not self-review) is the recommended discipline, not an optional nicety — full
treatment, including exactly how that countersign rides this project's own `led
review`/`led obligate` machinery and what remains unbuilt today: read
[ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md](../../design/ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md) in full before
adopting this for anything you'd actually rely on. Tool docs and vendoring/split provenance:
[`tools/makespan-scheduler/README.md`](../../tools/makespan-scheduler/README.md) /
[`tools/makespan-scheduler-PROVENANCE.md`](../../tools/makespan-scheduler-PROVENANCE.md).

**How do I prove two phases ran in the right order, instead of trusting an agent's
say-so?**
This recipe now has a formal shape too — both live in
[USER-SHAPED-RECIPES-FAQ.md](../USER-SHAPED-RECIPES-FAQ.md#the-doc-then-fix-ordering-proof)
(`design/workflows/faq-doc-then-fix-sequencing.toml`).

**How do I record, defeasibly, that a close's promised commit actually landed in the tree?**
This recipe now has a formal shape too — both live in
[USER-SHAPED-RECIPES-FAQ.md](../USER-SHAPED-RECIPES-FAQ.md#the-bookkeeping-close-pairing-convention)
(`design/workflows/faq-bookkeeping-close-pairing.toml`), including the WITNESSED live transcript
that used to live here.

## Capturing errors so they cannot quietly recur (ADR-0000 / ADR-0011)

**Can I leverage autoharn to automate the process of capturing errors before they happen
again, à la ADRs 0000 and 0011?** Yes — the discipline exists, it is mostly typing rather
than tooling, and it ran end-to-end on a live specimen on 2026-07-18 (the SQL-injection
class: captured as ledger row 1637, named as a class in the same day's
[ADR-0000](../../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md) and
[ADR-0012](../../law/adr/0012-compositional-and-structural-hygiene.md) amendments, swept
across every sibling script under row 1643, and banked as re-runnable red fixtures). The
recipe, in the order the ADRs bind it:

1. **Type the error as a CLASS, not an anecdote.** When a defect surfaces, write a ledger
   row that names the class it instantiates — firmer vocabulary than a prose "snag". The
   suggested shape is a sibling statement grammar to `estimate:`/`actual:`
   ([USER-RETROSPECTIVE-RECIPE.md](../USER-RETROSPECTIVE-RECIPE.md)'s convention family):
   `defect: <CLASS-SLUG> | <SPECIMEN> | <FORECLOSING-FIX> | <REFS>` — one row per
   class, the specimen quoted, the refs pointing at the incident, and the
   foreclosing-fix field holding the fix once typed, or the literal word `open` while
   it is still outstanding. This is a CONVENTION in
   v1, deliberately unvalidated: per [ADR-0011](../../law/adr/0011-mechanization-discipline.md),
   an intake validator is minted when a malformed row is witnessed recurring, not before.
2. **Ask ADR-0000's Rule 2 pair before authoring any fix**: (a) what type forecloses the
   whole class, and (b) what operational lapse let it recur — the answers belong in the
   same row's foreclosing-fix field or its follow-up.
3. **Bank the red.** A closed defect gets a `seen-red/` fixture registered in the
   fixture census ([gates/fixture_census.py](../../gates/fixture_census.py)) — after that,
   silent reintroduction is mechanically impossible: the fixture is a standing
   re-executable witness, which is the reintroduction-blocking half, already built.
4. **Cross-check on the next incident.** Before fixing anything new, query the ledger for
   the class (`./led` search over `defect:` rows); a hit converts "fix this bug" into
   "this class RECURRED", which is exactly ADR-0011's trigger to mint a mechanical check.
   The A:B:C loop's named defect catalogue
   ([ORCH-ABC-AUDIT-LOOP-RECIPE.md](../ORCH-ABC-AUDIT-LOOP-RECIPE.md)) is this same pattern
   already running for documentation defects.
Named honestly, what is NOT built: the self-triggering half — a Claude Code hook that
observes an error signal and itself runs the cross-check (or inserts an obligation
binding someone to run it) — does not exist. It is filed on the ledger as a candidate detective-control
mechanism (ledger row 1696), to be built when the manual cross-check step is witnessed
lapsing — the same evidence bar the estimates discipline's own recording lapse met on
2026-07-18 (ledger row 1695: four days of estimates written with no recorded outcomes,
caught by a maintainer-commissioned calibration study) — never by anticipation.
**UNWITNESSED beyond that filing:** no cross-check lapse has yet been observed to test
the trigger.

## Drift backstops (one generic method for anything that goes quietly stale)

**Half my project is artifacts that describe or derive from other artifacts — docs from code, a
hash function from a table's columns, a config from the mechanisms it configures, a deployment
from the kernel it was born with. Each pair rots in the same way: the authority moves and the
copy silently doesn't. Is there one method for this, or do I invent a checker each time?**

One method, and it was derived from this project's own built instances rather than invented for
this page — fourteen independently-built mechanisms here turn out to share one shape, and the
shape is worth having as a named reach. First the class, in the LAW's own words
([ADR-0011](../../law/adr/0011-mechanization-discipline.md)'s Context): *"a design document that
quietly goes stale while the code it describes moves on, a duplicated fact whose two copies
drift apart one edit at a time"* — the invisible-at-authoring, visible-only-in-aggregate defect.
**Drift** is what happens to any DEPENDENT artifact that claims to reflect an AUTHORITY: the
authority moves, the dependent stays, and nothing notices until a reader trusts the stale copy.
A **drift backstop** is a mechanical comparator over one such declared pair, and every instance
in this repository is the same five moves with different types plugged in:

1. **Name the pair.** One side is the authority (the single source of truth —
   [ADR-0012](../../law/adr/0012-compositional-and-structural-hygiene.md)'s Principle 1, one owner
   per fact); the other is the
   dependent that claims to correspond to it. If you cannot say which side is authoritative,
   that ambiguity is the defect to fix before any checker is worth building.
2. **Derive both sides mechanically at check time** — from filenames, the live database catalog,
   `git ls-files`, the file's own bytes — never from a hand-maintained second list. A hand list
   is itself a dependent that drifts: [filing/apparatus_registry.py](../../filing/apparatus_registry.py)'s
   own docstring records that a hand-typed mechanism-name list HAD already drifted, silently
   (a real, wired-in mechanism was absent from it), before the derived set replaced it.
3. **Compare with a comparator that quantifies over the class**
   ([ADR-0011](../../law/adr/0011-mechanization-discipline.md) Rule 4): any future column, delta,
   link, or key is in scope by construction. An enumeration of today's instances fails open at
   the next instance — which is drift's own front door.
4. **Refuse loud, teaching the honest discharge paths**: refresh the dependent, or DECLARE the
   divergence explicitly (an honest lag note, a `--declare-change` naming what moved). Silence
   never discharges; a declared lag is a recorded fact, not a pass.
5. **Backstop the backstop.** The comparator gets its own both-polarity
   [seen-red](../../GLOSSARY.md#seen-red) proof and a
   [fixture-census](../../GLOSSARY.md#fixture-census) registration, ships WITH the fix that closes
   the first witnessed drift (ADR-0011's 2026-07-02 amendment: the mechanism is minted with the
   first fix, not after a recurrence), and runs on a declared rhythm — per-commit, at
   acceptance, at cut time, or as an on-demand verb.

When the authority side has no independent derivation (a function's canonical text has no
second source to recompute it from), the fallback is a **banked manifest plus a declared-change
ceremony**: bank the current truth's bytes or hash, and the drift check becomes "changed without
declaring" — [gates/validation_leaf_manifest_gate.py](../../gates/validation_leaf_manifest_gate.py)
(banked function text, `--declare-change`) and [tools/role_charter.py](../../tools/role_charter.py)
(ledger-registered charter sha256, a loud `DRIFT` warning when on-disk bytes diverge) are the
two built instances of that variant.

**Which backstops already exist that I can crib from?** Each of these was verified in the corpus
for this entry (file named; read its docstring for the full truth — the per-instance docstring
is each one's owning page):

- [gates/idris_model_freshness.py](../../gates/idris_model_freshness.py) — the categorical kernel
  model's declared `AS-OF` head vs the actual lineage head, both derived from
  `kernel/lineage/*.sql` filenames; its teach-text names both discharge paths (refresh, or an
  honest lag note).
- [gates/hash_coverage_gate.py](../../gates/hash_coverage_gate.py) — `compute_row_hash`'s
  serialized-column enumeration vs the ledger's live column set on a scratch apply. The
  witnessed drift it closes is this page's best cautionary specimen: thirteen deltas each added
  columns, none re-issued the hash function, and twenty-two columns sat outside the
  tamper-evidence chain (ledger row 1449) until caught by eye.
- [gates/link_integrity.py](../../gates/link_integrity.py) — every relative markdown link target
  vs the file tree (files move; links dangle).
- [gates/layout_census.py](../../gates/layout_census.py) — [provenance/LAYOUT.md](../../provenance/LAYOUT.md)'s
  designed tree vs the tracked tree ("ls-legibility asserted once and never re-checked would
  rot exactly as the old repos did" — its own motivating line).
- [gates/fixture_census.py](../../gates/fixture_census.py) — `seen-red/` evidence dirs vs the
  fixture registry vs what git actually tracks, both directions.
- [gates/apparatus_unknown_keys.py](../../gates/apparatus_unknown_keys.py) — `apparatus.json` keys
  vs the mechanism set derived from `hooks/`, `bootstrap/templates/`, and `tools/` source.
- [gates/column_complete_gate.py](../../gates/column_complete_gate.py) — each registered view's
  live columns vs its source table's, minus declared exclusions.
- [gates/kind_shape_manifest_gate.py](../../gates/kind_shape_manifest_gate.py) — the
  (kind, column, arity) manifest vs the live kernel catalog's actual constraints.
- [gates/ledger_reader_allowlist.py](../../gates/ledger_reader_allowlist.py) — every view/function
  that reads the ledger vs the closed allowlist of declared reader types.
- [gates/validation_leaf_manifest_gate.py](../../gates/validation_leaf_manifest_gate.py) and
  [tools/role_charter.py](../../tools/role_charter.py) — the banked-manifest variant, described
  above.
- [gates/cut_probe_inventory.py](../../gates/cut_probe_inventory.py) — a release-candidate tree vs
  the registry of shipped fix classes: drift backwards (a silent revert) caught at cut time.
- [gates/doc_attestation_presence.py](../../gates/doc_attestation_presence.py) (and its
  per-deployment sibling `attest-doc`, whose witnessed `STALE` verdict appears in
  [the "Verifying tags, signed commissions, and documentation debt" section](EVIDENCE-AND-TRUST.md#verifying-tags-signed-commissions-and-documentation-debt-attest-tags-verify-commission-attest-doc-distance-to-clean))
  — a doc's current bytes vs the content hash its last fresh-context read attested.
- [./autoharn migrate](../../libexec/autoharn/migrate) `--dry-run` ([bootstrap/migrate_core.py](../../bootstrap/migrate_core.py)) —
  a deployment's live schema vs the kernel lineage chain, one `.detect.sql` probe per delta,
  reporting exactly which deltas the world lacks.

- seen-red/setup-tui-scripted-smoke (deleted 2026-07-22, design/FABLE-SETUP-TUI-REBUILD-SPEC.md wholesale rebuild) —
  the setup surface's own backstop, commissioned under the maintainer's 2026-07-19 standing
  rule ("the setup surface itself ... will drift unless maintained", ledger row 1700: `./autoharn led
  show 1700` at the repository root): a scripted TUI smoke fixture, census-registered, driving
  `python3 -m tools.setup_tui.app --scripted ... --start-at <screen>` against real hostile/
  malformed inputs and asserting the same REFUSED-no-traceback outcome the mechanism itself is
  supposed to produce, plus (added for the feature-facts column, ledger row 1714) asserting the
  facts lines documented just below actually render at preflight/substrate/boundary/
  observability/hydration screen entry.
- [seen-red/setup-tui-feature-facts-drift](../../seen-red/setup-tui-feature-facts-drift/run_fixtures.py)
  — `tools/setup_tui/feature_facts.py`'s own registry vs. the live preflight-binary/substrate-
  choice/hydration-catalog set `tools/setup_tui/steps.py` (the post-rebuild `SECTIONS` registry,
  `screens.py`'s successor) and `durable_decisions.py` actually expose,
  compared both directions (the class this whole section describes, applied to the feature-
  facts column itself — this spec's own first deliberate consumer of the method,
  design/FABLE-SETUP-TUI-FEATURE-FACTS-SPEC.md §1).
- seen-red/setup-tui-dry-run-parity (deleted 2026-07-22, design/FABLE-SETUP-TUI-REBUILD-SPEC.md wholesale rebuild) —
  the `--dry-run` amendment's own two real-infra witnesses (design/FABLE-SETUP-TUI-SPEC.md
  2026-07-19 amendment, ledger row 1719): WDR1 (a full dry-run flow against a real
  destination leaves the filesystem byte-identical before/after and writes zero ledger rows)
  and WDR2 (the WOULD-DO table's argv list equals a real scratch run's argv list, byte-for-
  byte, order included); needs a reachable Postgres host and the boundary service's venv,
  degrading honestly to `UNEXERCISED` (exit 0) without either, rather than failing the build
  on missing optional local infra.
- seen-red/setup-tui-textual-shell (deleted 2026-07-22, design/FABLE-SETUP-TUI-REBUILD-SPEC.md wholesale rebuild) —
  the Textual-face build's own WX1-WX6 witnesses (design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md §4,
  commission ledger row 1818): a headless Textual journey through all eleven screens (WX1),
  transcript parity with the plain backend's `$ `-prefixed lines (WX2), the textual-absent
  fallback teaching line and `--plain`'s override (WX3), the `Ui.suspend()` bridge reaching the
  real `App.suspend()` (WX4, wiring), abnormal-exit cleanup under a real SIGTERM delivered to a
  real process (WX5), and `--dry-run` under the shell (WX6) — against the real
  `tools/setup_tui/ui_textual.py` classes, no mocks. Runs under whichever interpreter this
  fixture finds `textual` importable in (`SETUP_TUI_TEXTUAL_PYTHON`, or the ambient one),
  degrading the textual-dependent cases honestly to `UNEXERCISED` with the exact pip/venv
  pointer when none is found.

**The setup TUI's own two durable-decisions features (design/FABLE-SETUP-TUI-FEATURE-FACTS-
SPEC.md, ledger rows 1714/1716):** every selectable act the guided wizard
(`python3 -m tools.setup_tui.app`, [FABLE-SETUP-TUI-SPEC.md](../../design/FABLE-SETUP-TUI-SPEC.md))
offers now shows a facts line — the standards-conformance aspiration it serves (with citation,
or an honest "none named") and its external costs/dependencies (with an honest "none") — at the
point of selection, from `tools/setup_tui/feature_facts.py`'s one-home registry. Separately, the
Hydration screen (`--start-at hydration`) offers a small, curated catalog of durable decisions born of
witnessed painful (or successful) experience from this project's own ledger AND the
autoharn-panel deployment's — `tools/setup_tui/durable_decisions.py` — each selection writing a
real `led decision` row and compiling into the new world's CLAUDE.md between generated-section
markers (idempotent, never touching bytes outside them); an ADR-adoption submenu is DERIVED from
`law/adr/*.md` at runtime, never a hand list. Kernel `obligate` rows are explicitly out of v1 —
the catalog exists partly to encode the obligate-amplification footgun (obligating a principal
makes every row that principal later writes count as new review debt too, not just the rows
that existed at obligation time — ledger row 1640) as one of its own entries, not to hand a
fresh operator a loaded trigger at birth.

**Honest limits, so the method is not oversold.** A backstop checks the DECLARED correspondence
dimension only — semantic fidelity beyond it stays review-only, and the honest instances say so
themselves ([gates/layout_census.py](../../gates/layout_census.py) checks the tree's registered
shape mechanically but declares "does this new file actually belong in this directory" a human
judgment, review-only, rather than pretending a regex can make it). Nothing sweeps for pairs
nobody declared: naming the pair is judgment, and both witnessed drift hazards above (the
22-column hash gap, the apparatus hand-list) were first caught by eye, with the class closed
after — the method forecloses recurrence, not first occurrence. A backstop is only as current
as its declared rhythm — an acceptance-time or on-demand check catches nothing between runs.
And one boundary kept deliberately, per [ADR-0008](../../law/adr/0008-classification-discipline.md)'s
refuse-to-force-a-category discipline: the differential twins
([`./judge`](../../GLOSSARY.md#judge)'s SQL-vs-ASP marriage, `serving/audit_served.py`'s
served-vs-kernel byte-compare) are a sibling shape — two independent LIVE derivations required
to agree now — not a stale-copy-vs-authority check, so they are named here as relatives and
excluded from the class rather than fuzzy-matched into it.

## Operating rhythm

**How do I pick up work after a break?**
Start a fresh session and run `./pickup` — never resume or continue an existing one. The brief is derived
at pickup time from live ledger state; a stored handoff decays and replayed context is
the quadratic cost the ledger exists to replace. Card:
[ORCH-OPERATING-CARD.md](../ORCH-OPERATING-CARD.md).

**Can I turn a safety mechanism off, or make it observe-only? Will that be visible?**
Yes and yes — every mechanism is independently `off`/`observe`/`enforce` in
`.claude/apparatus.json`, live on the next tool call; and since 2026-07-12 every mutation
of that file is itself journaled (hashes, which modes changed), so a flip is witnessed
rather than silent. Full switchboard, per-mechanism defaults and costs:
[bootstrap/templates/APPARATUS.md](../../bootstrap/templates/APPARATUS.md).

**A finished run's world turns out to have a defect. Can I patch it?**
No — runs are strictly linear; a superseded world is settled, read-only evidence. The fix
enters the next world via the scaffold (it usually already has), and the finding goes on
the ledger. This is a ruling, not a limitation looking for a workaround. Ruling text:
[../CLAUDE.md](../../CLAUDE.md), ORCHESTRATION section.

## Recusal and independent RCA — root cause analysis (a conflict-of-interest method harvested downstream)

This section covers a five-step method for what an orchestrator should do when the thing it
would need to judge is a decision it made itself — recuse from the judgment, then dispatch an
independent, evidence-only investigation rather than adjudicate its own work. It is a documented
practice (a discipline to follow by hand), not a mechanism that refuses anything; nothing here
gates a write. Provenance: harvested from the autoharn-panel deployment's own orchestrator
behavior, reconstructed and generalized in this project's own ledger, `recusal-rca-recipe` (row
1358, still open at the time of this writing — a ledger row, not a committed page: `./autoharn led show
1358` at the repository root reads it in full).

**What actually happened, the specimen this method generalizes.** WITNESSED — read directly from
this repository's own live ledger this session (`./autoharn led show 1364`, kind `finding`, dated
2026-07-17), quoting the maintainer's own framing of why it mattered: *"This is literally the
first time I have ever seen a formal RCA taken up on their own. I feel like a child again."* The
downstream (panel) orchestrator, unprompted, recognized that a security warning it was about to
adjudicate targeted its **own** dispatch design — the same design decision it would have to judge
if it kept going — recused itself, pulled raw evidence only (principal registrations, actor ids,
stamps — no narrative, no leaning), dispatched an independent fact-finding-only RCA, and on
return filed the incident's own verdict separately from the systemic policy question the incident
raised, routing the systemic question to the maintainer rather than answering it itself. That
downstream session's own ledger rows (its "row 1341" for the incident verdict, "row 1343" for the
systemic question) are cited in row 1364's text as history; they live in the panel deployment's
own database, which this session has no credentials or access path to from this worktree —
**UNWITNESSED here, concrete blocker: no reachable connection to that separate deployment's
ledger** — the autoharn-side row (1364) that reports them, by contrast, was read live, this
session, and is WITNESSED.

**The five steps**, reconstructed from the specimen above and from the same "two-spy synthesis" (one ledger row combining two independent observer sessions' findings; the worked example lives in [REVIEW-AND-GATING.md](REVIEW-AND-GATING.md))
practice's own harvest of this method (WITNESSED, `./autoharn led show 1357`, kind `decision`, 2026-07-17
evening, read this session):

1. **Recognize the conflict of interest.** The question on the table is, in whole or in part,
   about a decision the orchestrator itself made (its own dispatch design, its own prior
   judgment) — not a third party's work.
2. **Recuse.** State the conflict on the record and decline to adjudicate it directly, rather
   than judging your own work under the belief that self-awareness of the conflict is enough
   correction on its own.
3. **Pull raw evidence only.** Gather the primary facts a judgment would need — registrations,
   ids, stamps, timestamps, the ledger rows themselves — with no narrative gloss layered on top.
4. **Dispatch an independent, fact-finding-only investigation.** Brief it under
   [ADR-0018](../../law/adr/0018-consults-are-not-front-loaded.md)'s discipline: the witnessed
   problem, the raw evidence, and the governing LAW — never the recusing party's own candidate
   diagnosis, suspect list, or leaning (a front-loaded brief collapses the independence the whole
   method exists to buy). The dispatch itself is the same **out-of-frame second opinion**
   [ADR-0014](../../law/adr/0014-executor-second-opinion.md) licenses for a stalled line of
   reasoning, applied here to a *structural* conflict of interest rather than a *stalled*
   diagnosis — same remedy (a fresh, unled frame), different trigger.
5. **File the incident and the systemic question separately.** The RCA's fact-finding answers
   the immediate incident; if it also surfaces a broader policy question (should the underlying
   design change, not just this one instance), that question is filed as its own record and
   routed to the party who owns that decision — never folded into, or silently settled by, the
   incident verdict.

**Why this is a method to imitate, not a one-off** (the causal case, WITNESSED from row 1364's own
text, read this session): four traceable harness mechanisms made it possible, not luck alone —
the recusal rule existed beforehand as a ledgered standing decision the recusing session could
cite ("per my own standing rule"); the raw-evidence-only briefing shape is ADR-0018 itself,
already part of that downstream deployment's own law snapshot; the independent-dispatch habit had
ledgered precedent in that same world — **the second witness this recipe's own ledger row names**:
"their rows 51/52 via ADR-0014" (row 1358's own text) — i.e. a prior, independent instance of the
same fetch-a-fresh-frame move, recorded in the panel deployment's own ledger under ADR-0014's
second-opinion license, making this the *second* time the shape was used rather than a first,
un-repeatable accident; and the cost asymmetry favors the disciplined path (one cheap dispatch
plus ledger queries the system already answers). **UNWITNESSED here, same blocker as above:**
rows 51/52 live in the panel deployment's own ledger, unreachable from this session — cited as
provenance per row 1364's own text, not independently re-derived.

**A mechanical illustration of step 5** (the split-filing act itself — NOT a re-enactment of the
real specimen, which this session cannot reach), WITNESSED on a disposable scratch world of the
same `faqwit0718` family this page's scratch demonstrations use (torn down after — see
[USER-SHAPED-RECIPES-FAQ.md's bookkeeping-close-pairing-convention
section](../USER-SHAPED-RECIPES-FAQ.md#the-bookkeeping-close-pairing-convention) for the scaffold
command this family of worlds is built with):
```
$ ./led decision "FAQ-DEMO incident verdict: illustrative fact-finding-only record for the recusal-then-independent-RCA recipe transcript -- this specific scratch-world act, no systemic claim."
led: row 18 written.
$ ./led decision "FAQ-DEMO systemic question: illustrative record showing the split -- a policy question this incident surfaces, filed as its own row rather than folded into the incident verdict above, and routed to the owning authority rather than self-adjudicated."
led: row 19 written.
```
Two separate, independently-citable rows — nothing here forces the split; it is the discipline
described above, exercised by hand as ordinary `led decision` writes, not a distinct verb or
constructor.

(2026-07-27 correction, root-shim-pruning residue sweep, ledger row 1357: the two-row transcript
above is a WITNESSED scratch-world act, `faqwit0718` family, with real row ids 18/19, predating
the umbrella-CLI scaffold migration, rows 1365/1366/1367, 2026-07-26, which retired the bare
`./led` shim it typed — left as the dated record it is; the current equivalent invocation is
`./autoharn led decision "..."`.)

**Honest limits.** This is a documented practice, not a mechanized one: no gate checks that a
conflicted orchestrator actually recused, that a dispatched RCA was actually briefed
evidence-only, or that a systemic finding actually got filed separately rather than folded in —
all four are review-only, exactly as [ADR-0014](../../law/adr/0014-executor-second-opinion.md) and
[ADR-0018](../../law/adr/0018-consults-are-not-front-loaded.md) themselves disclose for their own
enforcement surface. A maintainer ratification (WITNESSED, `./autoharn led show 1366`, read this session)
fixed a v1 DESIGN for shipping one seeded standing decision row — the recusal-on-conflict-of-
interest rule itself — at every new world's birth, default ON, declinable by an explicit scaffold
flag: *"The shipping-at-birth is a cool idea of course, but needs to be configurable ... given the
goal of the project, I cannot see why anybody would ever choose not to."* That seeding is a
**ratified design, not yet built** — checked this session: `bootstrap/new-project.sh` carries no
mention of "recusal" today (`grep -i recusal bootstrap/new-project.sh` returns nothing), so a
freshly scaffolded world does not yet start with this rule pre-seeded; until it lands, adopting
this method means citing it and following it by hand, the same way this section documents it.
Residual honesty from the specimen itself, carried forward rather than oversold: n=2 specimens in
one downstream world, and model disposition is a live confound — the falsifiable test named in
row 1364 is whether the *next* fresh world, carrying only the harness and no accumulated
panel-specific history, reproduces the shape on its own first conflict-of-interest event.

