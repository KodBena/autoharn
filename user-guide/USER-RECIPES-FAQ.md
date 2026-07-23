# Can I do that? — recipes FAQ for operators

This page is written for an operator of a scaffolded project who wants to know whether the
harness supports a thing they have in mind, and what to actually type if it does. Every
entry below began life as a real operator question ("can we use X for end users?", "can I
track Y?") asked of this project's orchestrator during 2026-07; the answers were built,
witnessed, and then condensed here. This page deliberately restates NO grammar and NO
ceremony in full — each recipe names the intent, the one-line shape, the honest limit, and
the ONE page where the full truth lives (this project's single-source-of-truth discipline:
a grammar documented twice drifts). The dense per-mechanism inventory this page complements
is [ORCH-CAPABILITIES.md](../ORCH-CAPABILITIES.md); the front door for first-time setup is
[USER-GUIDE.md](USER-GUIDE.md).

## Contents

The sections below, in page order — each link jumps to that section's own
question-and-recipe entries.

- [Planning and retrospectives](#planning-and-retrospectives)
- [Workflow patterns](#workflow-patterns)
- [Getting started: the guided setup TUI (`python3 -m tools.setup_tui`)](#getting-started-the-guided-setup-tui-python3--m-toolssetup_tui)
- [Declaring things on the ledger](#declaring-things-on-the-ledger)
- [Principal identity (s40/s41)](#principal-identity-s40s41)
- [Typed verdicts and refusal recording (s42/s43)](#typed-verdicts-and-refusal-recording-s42s43)
- [Standing lifecycle (s45)](#standing-lifecycle-s45)
- [Model identity: watchdog, attestation, defeat](#model-identity-watchdog-attestation-defeat)
- [Trust ceremonies](#trust-ceremonies)
- [Review discipline](#review-discipline)
- [Classifying audit/diagnostic findings](#classifying-auditdiagnostic-findings)
- [Capturing errors so they cannot quietly recur (ADR-0000 / ADR-0011)](#capturing-errors-so-they-cannot-quietly-recur-adr-0000--adr-0011)
- [Drift backstops (one generic method for anything that goes quietly stale)](#drift-backstops-one-generic-method-for-anything-that-goes-quietly-stale)
- [Documentation quality](#documentation-quality)
- [Operating rhythm](#operating-rhythm)
- [Your review queue](#your-review-queue)
- [Correcting the record — supersession, and what to do about its fallout](#correcting-the-record--supersession-and-what-to-do-about-its-fallout)
- [The ledger boundary service (`serving/`)](#the-ledger-boundary-service-serving)
- [Boundary multiplex, CLI rebase, and the workflow-unit compiler (2026-07-18)](#boundary-multiplex-cli-rebase-and-the-workflow-unit-compiler-2026-07-18)
- [Role charters and briefs (`tools/role_charter.py`, `tools/role_brief.py`)](#role-charters-and-briefs-toolsrole_charterpy-toolsrole_briefpy)
- [CLI quality-of-life: row-id echo and `judge` auto-layer detection](#cli-quality-of-life-row-id-echo-and-judge-auto-layer-detection)
- [`led` help tokens, `--json` payload mode, and `work list`'s default filter (led.tmpl trio)](#led-help-tokens---json-payload-mode-and-work-lists-default-filter-ledtmpl-trio)
- [Ledger-wide as-of read and inspection-copy export (`asof-export`)](#ledger-wide-as-of-read-and-inspection-copy-export-asof-export)
- [Deployments can self-serve the harness changelog (`orchlog` wrapper at scaffold)](#deployments-can-self-serve-the-harness-changelog-orchlog-wrapper-at-scaffold)
- [Verifying tags, signed commissions, and documentation debt (`attest-tags`, `verify-commission`, `attest-doc`, `distance-to-clean`)](#verifying-tags-signed-commissions-and-documentation-debt-attest-tags-verify-commission-attest-doc-distance-to-clean)
- [Recusal and independent RCA (a conflict-of-interest method harvested downstream)](#recusal-and-independent-rca-a-conflict-of-interest-method-harvested-downstream)
- [What this page is not](#what-this-page-is-not)


## Planning and retrospectives

**Can agents estimate a task's cost before doing it, and can I see how the estimates did?**
Yes — ledger an `estimate:` row per task at decomposition time; `./pickup` prints all of
them under its ESTIMATES section, and the retrospective recipe has an estimate-vs-actual
section for reading them against what happened. The standing invariant, enforced by
design rather than by accident: a missed estimate is retrospective data, never a
violation — nothing gates, audits, or refuses on estimate accuracy, and nothing will.
Grammar and comparison recipe: [USER-RETROSPECTIVE-RECIPE.md](USER-RETROSPECTIVE-RECIPE.md) §6.

**Can I get cost/usage figures I can rely on?**
Partly, and the line matters: raw hook-witnessed event counts are evidentiary; anything
priced or derived from them (token totals, money) is diagnostic-grade permanently — useful
for a sanity check, never sound enough to bill against. Headline statement:
[USER-GUIDE.md](USER-GUIDE.md) §5; the design boundary:
[ORCH-SPEC-RESOURCE-ACCOUNTING.md](../design/ORCH-SPEC-RESOURCE-ACCOUNTING.md) §6.

**Can work form a deep task tree without deep subagent nesting?**
Yes — the tree lives in ledger rows, not process nesting: an interior task's children are
OPENED as work items citing the parent, dispatched flat, each closeable with its own
witness. Execution stays one or two levels deep; the logical tree is unbounded and every
interior node is auditable. The work verbs' home is
[ORCH-OPERATING-CARD.md](ORCH-OPERATING-CARD.md). Per-node estimate-vs-actual rollups
are a designed follow-up, not yet built — the design lives on the deployment's own tracker
as work item `work-tree-rollup` (a ledger row, not a committed page: read it with
`./led show work-tree-rollup` at the repository root, the same live-lookup convention the sibling
specs use for tracker items).

## Workflow patterns

**I want a workflow to iterate until clean — can an agent spawn sub-agents and loop on its
own output until a defect list comes up empty?**
This recipe now has a formal shape too — both live in
[USER-SHAPED-RECIPES-FAQ.md](USER-SHAPED-RECIPES-FAQ.md#the-abc-fresh-context-fix-point-loop)
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
[ORCH-WORKFLOW-SCRIPT-GOTCHAS-RECIPE.md](ORCH-WORKFLOW-SCRIPT-GOTCHAS-RECIPE.md)
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
[ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md](../design/ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md) in full before
adopting this for anything you'd actually rely on. Tool docs and vendoring/split provenance:
[`tools/makespan-scheduler/README.md`](../tools/makespan-scheduler/README.md) /
[`tools/makespan-scheduler-PROVENANCE.md`](../tools/makespan-scheduler-PROVENANCE.md).

**How do I prove two phases ran in the right order, instead of trusting an agent's
say-so?**
This recipe now has a formal shape too — both live in
[USER-SHAPED-RECIPES-FAQ.md](USER-SHAPED-RECIPES-FAQ.md#the-doc-then-fix-ordering-proof)
(`design/workflows/faq-doc-then-fix-sequencing.toml`).

**How do I record, defeasibly, that a close's promised commit actually landed in the tree?**
This recipe now has a formal shape too — both live in
[USER-SHAPED-RECIPES-FAQ.md](USER-SHAPED-RECIPES-FAQ.md#the-bookkeeping-close-pairing-convention)
(`design/workflows/faq-bookkeeping-close-pairing.toml`), including the WITNESSED live transcript
that used to live here.

## Getting started: the guided setup TUI (`python3 -m tools.setup_tui`)

**Is there a guided path from nothing to a running [world](../GLOSSARY.md#world) (this project's
term for one scaffolded, database-backed deployment), instead of typing the scaffold commands by
hand?** Yes — `python3 -m tools.setup_tui.app`, run from your autoharn checkout (the bare
`python3 -m tools.setup_tui` this section's own heading uses is equivalent — `tools/setup_tui/
__main__.py` is a thin redirect to the same `app.py`'s `main`; this doc uses the explicit
`.app` form throughout for clarity).
It is a **driver of the existing verbs, never a second implementation**: every screen shows
the exact command it is about to run (`bootstrap/new-project.sh`, `bootstrap/teardown-world.sh`,
`boundary_service`, `led`) and streams that command's real output, so if the process dies
mid-flow you can finish by hand from what was already printed. Full spec:
[FABLE-SETUP-TUI-SPEC.md](../design/FABLE-SETUP-TUI-SPEC.md); commission ledger row 1656
("so much to remember ... too much when you want to *just get started but still have a
seriously robust experience*").

**The interactive face is a real Textual application**
([design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md](../design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md),
commission ledger row 1818), superseding [FABLE-SETUP-TUI-SPEC.md](../design/FABLE-SETUP-TUI-SPEC.md)'s
original v1 "library ONLY if already installed" clause. The maintainer's own words commissioning this: "I tried to run the setup TUI
after installing
'textual' into a venv and I'm not really happy with how it looks -- in fact, textual is not
used, at all, it is not a TUI, it is just a collection of prompts no matter how clean the code
is... Could we make it into a real 'textual' app?" It now is: Header (with the derived "N/11
Screen" ordinal), a sidebar of the eleven screens with pending/current/done state, a scrolling
transcript pane carrying everything the flow says (banners, `$ argv` echoes, streamed real
command output), a docked prompt area for the active question, and a Footer — the SAME eleven
`screen_*` functions and the SAME `Ui` call sites (`tools/setup_tui/ui.py`) drive it, running
unchanged in a Textual worker thread while `tools/setup_tui/ui_textual.py`'s `TextualUi`/
`SetupWizardApp` render it. Selection is automatic: interactive runs get the real Textual face
when `textual` is importable; otherwise ONE teaching line naming the exact venv/pip command,
then the zero-dependency numbered-menu fallback proceeds ("degraded-but-possible beats
frozen"). `--plain` forces the numbered-menu interface explicitly, even with `textual`
installed. `--scripted` NEVER touches `textual` — headless witnessing stays dependency-free, as
it always has. `textual` itself remains a declared external cost of THIS TOOL's interactive
face only — never of the harness, a born world, or the witnessing path — install it into a venv
if you don't already have it:
```
python3 -m venv .venv && .venv/bin/pip install textual
.venv/bin/python -m tools.setup_tui.app
```
(or, inside an already-active venv, `pip install textual`). WITNESSED this build against a
scratch venv (`textual` 8.2.8, since the build interpreter itself did not have it installed):
the headless Textual journey (WX1), transcript parity with the plain backend for the same
`$ `-prefixed lines (WX2), the fallback teaching line (WX3), the `Ui.suspend()` bridge that
hands the real terminal to an interactive child process (gpg's own passphrase prompt during
Signed genesis) reaching the real `App.suspend()` (WX4), abnormal-exit cleanup under a real
SIGTERM (WX5), and `--dry-run` under the shell (WX6) — see
[seen-red/setup-tui-textual-shell](../seen-red/setup-tui-textual-shell/run_fixtures.py).

**The eleven screens, in order** (every screen skippable, the skip recorded — never silent;
`--start-at <slug>` below jumps straight to any one of them — the slug, never a hand-typed
number, is the only stable pointer: screen numbering is derived from
`tools/setup_tui/screens.py`'s own `SCREENS` list order, one home, precisely so a doc pointer
never drifts the way a hardcoded ordinal would the moment a screen is inserted):

1. **Preflight** (`--start-at preflight`) — repo commit, submodules populated,
   `idris2`/`clingo`/`python3`/`psql` found (clingo non-fatal, matching
   `bootstrap/bootstrap.sh`'s own posture), whether `HARNESS_PGHOST`/`EPISTEMIC_PGHOST`
   resolves to a reachable host; each check green/red with a fix command.
2. **Substrate** (`--start-at substrate`) — pick an existing database (zero manual steps) or
   a dedicated one (generates the confined `pg_hba` block in your *actual* file's own idiom,
   plus the createdb/copy/reload block, then probes until the connection genuinely works).
3. **Fork/target** (`--start-at fork-target`) — destination directory: a fresh directory, or
   a fork-copy of an existing project (with the `CLAUDE.md` → `CLAUDE.project.md`
   preservation move, so a fork's own governance prose survives the scaffold's unconditional
   `CLAUDE.md` write) — plus the governed-files pattern prompt described below.
4. **Rehearsal** (`--start-at rehearsal`) — a scratch-name birth + teardown + zero-residue
   check, streamed; the real birth is gated on a green rehearsal (a ratified discipline, not
   a suggestion — the Birth screen refuses without one unless you explicitly override).
5. **Birth** (`--start-at birth`) — `new-project.sh --new-world`, streamed; the maintainer
   copy-paste signing line is surfaced prominently at the end, delimited by `BEGIN`/`END`
   markers.
6. **Principals & authority** (`--start-at principals-authority`) — registers additional
   principals, grants [s41](#principal-identity-s40s41) competences (recorded beliefs about who
   is trusted to do what, at what confidence band, on what basis) and typed relations (e.g.
   acts-for, dispatched-by), and registers role charters (a written statement of what a role is
   for and what it may do, filed against a registered principal via `tools/role_charter.py`)
   in-flow; skipping it
   is legitimate (the scaffold's own three principals already make a complete world).
7. **Signed genesis** (`--start-at signed-genesis`) — the GPG-signing ceremony for the
   world's founding commission, on by default; full operator walkthrough (four visible
   commands, the VERIFIED gate, the skip path, rotation) in
   [USER-GPG-TRUST-LAYER-FAQ.md §5a](USER-GPG-TRUST-LAYER-FAQ.md#5a-the-setup-tuis-own-signed-genesis-screen--the-same-ceremony-automated).
8. **Boundary** (`--start-at boundary`) — writes the multiplex TOML (the config file letting
   one boundary service process serve several deployments/worlds side by side) and the two
   `deployment.json` boundary keys, picks a free port, starts the service (or emits the
   systemd-style unit text as a copy-paste block when this process doesn't keep it alive
   itself), probes `/health` and `/meta`.
9. **Observability** (`--start-at observability`) — the `otelcol` start line
   (localhost-only), the OTel model-provenance watchdog start line (`./otel-watch --daemon`,
   a background process that checks the OTel telemetry stream for the model-identity/
   provenance fields this project's OTel-attestation discipline requires and flags gaps loudly),
   and the Claude launch line with the right env vars, as copy-paste blocks with a
   what-you-should-see line each.
10. **Hydration** (`--start-at hydration`) — free-text prompts for fork provenance and role
    charters to register, plus two curated catalogs described below (feature-facts,
    durable-decisions), and an ADR-adoption submenu derived from `law/adr/*.md` at runtime
    (never a hand list).
11. **Checklist** (`--start-at checklist`) — a per-item WITNESSED/SKIPPED/REFUSED/PREPARED
    table of everything the flow touched, offered for saving into the new world as a dated
    file.

**The feature-facts column** ([design/FABLE-SETUP-TUI-FEATURE-FACTS-SPEC.md](../design/FABLE-SETUP-TUI-FEATURE-FACTS-SPEC.md), ledger row 1714)
**was built 2026-07-19.** Every selectable act on every screen above now prints a facts line
*before* you commit to it: the standards-conformance aspiration it serves (with a citation,
or an honest "none named") and its external costs/dependencies (with an honest "none") —
read from `tools/setup_tui/feature_facts.py`'s one-home registry (29 entries at this
writing; the maintainer's own recollection at commissioning was 4, treated as a hypothesis
the registry's enumeration checked, not a ceiling). WITNESSED live, this session, against
the preflight screen (`python3 -m tools.setup_tui.app --dry-run --scripted <answers>
--start-at preflight`):
```
facts [idris2 toolchain] -- aspiration: none named; house discipline only -- backs the
  categorical-kernel-model freshness cross-check (gates/idris_model_freshness.py), not a
  named external standards-conformance aim. | external: external binary: idris2
  (github.com/idris-lang/Idris2#installation); not on PATH reads RED with an install pointer.
idris2: RED -- not found on PATH
  fix: install idris2 (...) and ensure it is on PATH
```

**This is the durable-decisions catalog** (same spec §3, ledger rows 1714/1716/1718/1721/1722).
The Hydration screen (`--start-at hydration`) offers a curated, 12-entry catalog of standing
rules distilled from this project's own ledger and the autoharn-panel deployment's (a separate
operator-dashboard product — a Vue front end over a FastAPI service — that consumes this
project's ledger through the boundary service, vendored under `tools/autoharn-panel/`), each
entry admitted only on a witnessed painful (or successful) specimen — not a generic
best-practice list. It went through a dedicated genericity critique before merge
([SONNET-CATALOG-GENERICITY-CRITIQUE-2026-07-19.md](../design/SONNET-CATALOG-GENERICITY-CRITIQUE-2026-07-19.md)):
one entry judged bespoke to this project's own contributors was cut, four were rewritten to
remove autoharn-specific ("first-project") voice, and three generic entries the mining pass had missed (including the
claims-carry-witnesses taxonomy — WITNESSED/REFUSED-AS-EXPECTED/UNEXERCISED) were added.
Selecting an entry writes a real `led decision` row AND compiles a fragment into the new
world's `CLAUDE.md` between generated-section markers (idempotent, fork-destination-safe —
never touches bytes outside the markers). Kernel `obligate` rows are deliberately out of v1:
the catalog encodes the obligate-amplification footgun (ledger row 1640 — obligating a
principal makes every row that principal later writes count as new review debt, not just the
rows that existed at obligation time) as one of its own entries, rather than handing a fresh
operator a loaded trigger at birth.

**Governed-files exposure is built and merged, and is live on the Fork/target screen.** "Governed
files" are the files whose edits `hooks/pretooluse_change_gate.py` gates by pattern, keyed to
what a file *is* rather than an enumerated list (F33, cited in the facts line below). A 2026-07-19
spec amendment (commission ledger row 1730: the maintainer's own painful specimen — the
autoharn-panel deployment started `.claude/governed_files.json` at `*.py`-only and needed
`.ts`/`.vue`/`.html` added by hand) adds a governed-files prompt to the Fork/target screen,
surfacing the default pattern set plus that teaching specimen and letting the operator confirm
or extend it for their project's real languages. `tools/setup_tui/governed_files.py` carries
the driver logic; `screens.py`'s `_governed_files_step` wires it into Fork/target. WITNESSED
this session (`python3 -m tools.setup_tui.app --dry-run --scripted <answers>
--start-at fork-target`, declining the extension):
```
facts [governed-files pattern exposure] -- aspiration: F33 (governance keyed to WHAT THE THING
  IS, not an enumerated file list) -- house discipline, not an external standard
  (hooks/pretooluse_change_gate.py's own _load_governed_patterns). | external: none -- writes
  one JSON file inside the target directory (<dest>/.claude/governed_files.json), no new
  binary or package. Commission row 1730: the autoharn-panel deployment started .py-only and
  needed .ts/.vue/.html added by hand after the fact.
  default pattern set: ['*.py']
Extend the governed-files pattern set beyond the default (*.py) for the other languages this
  project contains?: no   [scripted]
  --- PREVIEW: <dest>/.claude/governed_files.json (written by new-project.sh --governed at
  birth, and again at any later scaffold re-run this flow performs -- never by this screen
  directly) ---
  {
    "patterns": [
      "*.py"
    ]
  }
```
The screen never writes the file itself (ONE writer discipline) — it collects the pattern set
and passes it through to `bootstrap/new-project.sh`'s own `--governed
<comma-separated-fnmatch-patterns>` flag at birth, the same flag that was already live and
usable directly (without the TUI) before this screen existed; omit it entirely (declining
here, or scaffolding by hand) and you get the historical `*.py`-only default plus a loud,
refusal-grade notice naming the exact one-line widening act
(`.claude/governed_files.json`'s `patterns` array; fnmatch semantics, no restart needed —
`.claude/GOVERNED_FILES.md` in any scaffolded world).

**Principals & authority** ([design/FABLE-SETUP-TUI-PRINCIPALS-AUTHORITY-SPEC.md](../design/FABLE-SETUP-TUI-PRINCIPALS-AUTHORITY-SPEC.md), ledger rows
1727/1728) **is built and merged**, sitting between Birth and Signed genesis
(`--start-at principals-authority`). It registers additional principals, grants s41
competences, asserts typed relations, and registers role charters in-flow, showing a short
teaching line before each act explaining what it does and why, binding on every act, not
merely offered as optional help text (`tools/setup_tui/principals_authority.py` carries the
driver logic). Declining is legitimate and legible — every world already has
`author`/`reviewer`/`commissioner` from the scaffold (see ["Principal identity
(s40/s41)"](#principal-identity-s40s41) below), so skipping this screen leaves a complete
world; the screen's own value is propaedeutic, walking the ceremony once rather than a
prerequisite for a working world.

**Signed genesis** ([design/FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md](../design/FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md), ledger rows 1724–1726)
**is built and merged**, sitting between Principals & authority and Boundary
(`--start-at signed-genesis`). It is an optional, on-by-default, no-quiz keygen riding the existing
GPG web-of-trust machinery (no new crypto stack — the existing GPG trust layer this project
already ships) that generates a keypair, exports the public half into
the world's `keys/`, signs the world's founding commission, and verifies it against your own
key — one-time, no ongoing signing burden afterward. `tools/setup_tui/signed_genesis.py`
carries the driver logic. The full operator walkthrough — what you type, what you should see,
the four visible commands, the VERIFIED gate, the skip path, and key rotation via re-run —
lives in
[USER-GPG-TRUST-LAYER-FAQ.md §5a](USER-GPG-TRUST-LAYER-FAQ.md#5a-the-setup-tuis-own-signed-genesis-screen--the-same-ceremony-automated),
not duplicated here.

**`--dry-run` is the nondestructive whole-flow rehearsal** (2026-07-19 amendment, commission row
1719: "so I don't mess up any directory by mistake"). Add `--dry-run` to run the identical
eleven screens with NO destructive or externally visible act: no file written outside the
process's own temp space, no database act, no `led` write, no process started, no port bound.
Read-only probes (preflight, connection checks, reading your real `pg_hba` copy, the ADR
glob) stay live — a rehearsal that fakes its reads is a lie, not a rehearsal. Every screen
still computes and shows its would-be exact command/paths/ledger-rows; the closing checklist
renders `WOULD-DO` instead of `WITNESSED` and `DRY-SKIPPED` instead of a verified `PREPARED`
gate. Composes with `--scripted` and `--start-at` unchanged. WITNESSED both ways this
session:
- `--dry-run --start-at preflight`, no answers beyond preflight itself, produces the facts
  line quoted above (a live, real preflight probe) with no ledger or filesystem effect.
- A full skip-everything `--dry-run --scripted` run to the end reaches the Checklist screen
  and prints a real checklist table:
  ```
  SCREEN         ITEM                                   STATUS     DETAIL
  preflight      repo commit                            WITNESSED  82e8a81ca10f57cad8b33b39e73dbe7d0db81470
  preflight      submodules populated                   WITNESSED  no '-' prefixed entries
  preflight      idris2 found                           WITNESSED  RED: not on PATH -- install idris2 (...)
  preflight      clingo found                           WITNESSED  /usr/bin/clingo
  preflight      python3 found                          WITNESSED  /usr/bin/python3
  preflight      psql found                              WITNESSED  /usr/bin/psql
  preflight      HARNESS_PGHOST reachable               WITNESSED  RED: HARNESS_PGHOST/EPISTEMIC_PGHOST unset
  preflight      textual available                      WITNESSED  not installed
  preflight      urwid available                        WITNESSED  not installed
  substrate      path chosen                            SKIPPED    operator skipped screen 2
  fork-target    destination                            SKIPPED    operator skipped screen 3
  rehearsal      rehearsal                              SKIPPED    operator skipped screen 4
  birth          world birth                            SKIPPED    refused: rehearsal not green
  principals-authority screen                                 SKIPPED    operator skipped (declared-not-silent default=yes) -- legitimate and legible
  signed-genesis ceremony                               SKIPPED    operator skipped (declared-not-silent default=yes, ledger row 1725) -- legitimate and legible, never nagged again this run
  boundary       boundary                               REFUSED    refused: birth_ok not truthy
  observability  observability                          SKIPPED    operator skipped screen 9
  hydration      hydration                              SKIPPED    operator skipped screen 10
  ----------------------------------------------------------------------------------------------------
  totals: REFUSED=1, SKIPPED=8, WITNESSED=9
  ```
  (`REFUSED` here is the out-of-sequence-precondition discipline working as designed — the
  Boundary screen correctly refused to configure a boundary for a world that was never born,
  rather than building on nothing. The uneven column alignment on the principals-authority/
  signed-genesis rows above is quoted byte-for-byte from the real run, not a transcription
  artifact.) Note preflight itself read `HARNESS_PGHOST` as genuinely unset in this
  environment — an honest RED, not a fabricated pass; the fixture-backed WDR1 (byte-identical
  tree/ledger before vs. after) and WDR2 (argv parity, dry-run vs. live) witnesses against real
  infra live in
  [seen-red/setup-tui-dry-run-parity](../seen-red/setup-tui-dry-run-parity/run_fixtures.py)
  (degrades to UNEXERCISED, exit 0, without a reachable Postgres host and the boundary
  service's venv — same honest-degrade posture as this doc pass hit live). This particular
  table predates [design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md](../design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md)'s Textual-face build and was captured
  against an interpreter without `textual` installed — kept verbatim as a historical witness,
  per this doc's own no-retro-edit discipline. Where `textual` IS importable that row instead
  reads `available`, and the interactive face above the table becomes the real Textual
  application, not the numbered-menu fallback; see
  [seen-red/setup-tui-textual-shell](../seen-red/setup-tui-textual-shell/run_fixtures.py) for
  that build's own live witnesses.

**What does the wizard actually guarantee if I kill it, or my machine dies, partway through?**
([design/FABLE-SETUP-TUI-PURE-CORE-SPEC.md](../design/FABLE-SETUP-TUI-PURE-CORE-SPEC.md) §2.6,
commission ledger rows 1823 point 2 / 1825 — Phase 2 of the pure-core restructure, built on top
of everything above.) Every screen through Hydration is now a **pure decider**: it only
computes, displays, and appends to an in-memory plan — it performs no world-effect. All ten
screens' worth of decisions are executed at **one commit boundary**, the Checklist screen, which
renders the full plan (the same WOULD-DO table `--dry-run` already showed you, now literally the
SAME rendering) and asks ONE final confirm before touching anything. The guarantee, stated in
capability terms, not aspiration:
- **BEFORE that final confirm: nothing to clean up.** Kill the process at any point during the
  ten decision screens and the destination directory, your keyring, and every ledger are
  untouched — a structural property of the rewrite: no screen function may call `run_command`,
  `start_background`, or `write_file` (`tools/setup_tui/runner.py`'s three functions that
  actually touch the world) any more except the one commit step below, and
  [gates/setup_tui_purity_gate.py](../gates/setup_tui_purity_gate.py) asserts this mechanically,
  at the AST level, over every screen — not a discipline anyone has to remember.
- **DURING commit: per-act atomicity plus a durable resume.** Each write/command/background-
  start either fully happens or fully doesn't (the same atomic temp-file-then-rename write
  `tools/setup_tui/runner.py`'s `write_file` already used before this restructure), and a
  commit journal in the destination directory names exactly which step runs next — a mid-commit
  death resumes cleanly on re-invocation (no double `led decision` write, no second keygen) or
  finishes by hand from the streamed output above it.
- **NOT claimed: whole-flow atomicity** across Postgres, the filesystem, GPG, and a background
  process together. Decide-then-commit shrinks the exposure window from the whole session to the
  commit phase; it does not make the commit phase itself a single indivisible transaction.

Rehearsal (screen 4) is the one declared exception: it performs a real, scratch-target birth +
teardown mid-flow (its evidence gates the real birth), with witnessed zero-residue teardown —
named explicitly, not hidden.

**A minimal operator walkthrough register — what you do at each step, and what you should see:**

| Step (what you do) | What you should see |
|---|---|
| Type `python3 -m tools.setup_tui.app --dry-run` | The real Textual application if `textual` is importable (Header/sidebar/transcript/docked prompt, banner then `1/11 Preflight`) — or, absent it, one teaching line naming the venv/pip command then interactive numbered prompts (`--plain` chooses the numbered interface explicitly either way); or a refusal naming `--scripted` if stdin isn't a terminal at all — WITNESSED this session: `setup_tui: stdin is not a terminal and --scripted was not given -- refusing to run an interactive flow`. |
| Answer `yes` to preflight | Each prerequisite line green/red with a fix command; `HARNESS_PGHOST` red with `export HARNESS_PGHOST=<your postgres host>` if unset. |
| Walk screens 2–10, answering as prompted (or skip any with `no`) | Each screen prints its exact command/argv before running it (or, under `--dry-run`, before *not* running it); a skipped screen records `SKIPPED`, not silence. |
| Reach screen 11 (Checklist) | A per-item table, `WITNESSED`/`SKIPPED`/`REFUSED`/`PREPARED` (or the `--dry-run` counterparts), then an offer to save it into the new world. |
| Drop `--dry-run` and repeat for real | The same eleven screens perform the acts for real; a green Rehearsal (`--start-at rehearsal`) is required before Birth (`--start-at birth`) proceeds. |

Full command-line usage (`--help`, WITNESSED this session, byte-for-byte):
```
usage: setup_tui [-h] [--scripted ANSWERS_FILE] [--start-at SCREEN]
                 [--dry-run] [--plain]
```
`--start-at <screen>` (preflight, substrate, fork-target, rehearsal, birth,
principals-authority, signed-genesis, boundary, observability, hydration, checklist) jumps
straight to one screen — a screen entered out of its normal sequence independently validates
every precondition the normal sequence would have established, refusing legibly (never a
traceback) when one is missing (the 2026-07-19 out-of-sequence amendment, same spec).

**This closes with one line each on the setup TUI's own drift backstops**, cross-referenced in full under
["Drift backstops" below](#drift-backstops-one-generic-method-for-anything-that-goes-quietly-stale):
[seen-red/setup-tui-scripted-smoke](../seen-red/setup-tui-scripted-smoke/run_fixtures.py) (the
setup surface's own scripted smoke fixture, hostile/malformed inputs),
[seen-red/setup-tui-feature-facts-drift](../seen-red/setup-tui-feature-facts-drift/run_fixtures.py)
(the feature-facts registry vs. what the screens actually expose), and
[seen-red/setup-tui-dry-run-parity](../seen-red/setup-tui-dry-run-parity/run_fixtures.py) (WDR1
byte-identical tree/ledger, WDR2 argv parity dry-vs-live, both needing real infra).

## Declaring things on the ledger

**Can I declare which tools/services/agents this project may, should, must, or must not
use?**
Yes — one `resource:` row per resource, whose TIER field carries the deontic force:
`available` (MAY), `blessed:` (SHOULD), `mandated:` (MUST), `forbidden:` (MUST-NOT).
`./pickup` renders them tier-sorted, prohibitions first. Honest limit, tier by tier (not one
blanket answer — the two owning specs, [USER-BLESSED-TABLE-TEMPLATE.md](USER-BLESSED-TABLE-TEMPLATE.md)
and [ORCH-SPEC-RESOURCE-ACCOUNTING.md](../design/ORCH-SPEC-RESOURCE-ACCOUNTING.md), drifted on exactly this
in mid-2026-07-12 and were
reconciled 2026-07-13, tracker row 223 — a ledger row, not a committed page: `./led show 223` at
the repository root reads it in full): `mandated`'s close-review convention already shipped and
surfaces an undischarged close as [`review_gap`](../GLOSSARY.md#review_gap) debt — never a
refusal of the close itself;
`forbidden` is declaration + display only today, with no mechanism yet refusing an invocation
that reaches it (that audit is spec'd, unbuilt — the spec's own §7 says so). The reconciled,
owning statement of what is and is not enforced per tier lives at
[ORCH-SPEC-RESOURCE-ACCOUNTING.md §4.1](../design/ORCH-SPEC-RESOURCE-ACCOUNTING.md#41--the-mandated-tiers-enforcement-status-reconciled-dated-correction-2026-07-13-tracker-row-223).
Grammar home: [USER-BLESSED-TABLE-TEMPLATE.md](USER-BLESSED-TABLE-TEMPLATE.md); design:
[ORCH-SPEC-RESOURCE-ACCOUNTING.md](../design/ORCH-SPEC-RESOURCE-ACCOUNTING.md).

**Can I declare an architectural or licensing boundary and split work along it?**
Yes, declare it today; enforcement is staged. `taxon:` rows assign path patterns to named
classes, `interface:` rows name the sanctioned crossing points; `./pickup` renders a
TAXONOMIES section. The worked example is a real one (an MIT-derivative package inside a
public-domain codebase). What does NOT exist yet: the audit family and the write-time gate
that would police cross-boundary writes (Stages B–D of the spec). Declaring no taxonomy
declares no obligation. Grammar home and example:
[USER-TAXONOMY-DECLARATION.md](USER-TAXONOMY-DECLARATION.md); design:
[ORCH-SPEC-TASK-TAXONOMY.md](../design/ORCH-SPEC-TASK-TAXONOMY.md).

**Can I encode how tasks should be split, so I don't have to micromanage decomposition?**
Yes as declared policy: `task-policy:` rows carry splitting criteria (one acceptance
criterion per task, one boundary per task, estimate-before-execution, …) with MUST/SHOULD
force, and reviewer countersigns cite the criteria they checked. The policing column is
derived from what mechanisms actually exist — a criterion never claims more enforcement
than is built. Design and criteria table:
[ORCH-SPEC-DECOMPOSITION-POLICY.md](../design/ORCH-SPEC-DECOMPOSITION-POLICY.md) §3.

## Principal identity (s40/s41)

These two entries deviate from this page's usual point-elsewhere convention (full command
sequences with quoted witnessed output, not a one-liner plus a pointer) because the surface is
new and unfamiliar: `principal` went from four flat columns with no history to an event-sourced
identity model (registration, standing, role/key bindings, competence, relationships) in kernel
deltas s40/s41. Delivery record: [orchlog.d/s40-s41-principal-identity.md](../orchlog.d/s40-s41-principal-identity.md);
full spec: [design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md](../design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md).

**Prominent caveat, read before typing anything below:** these `led principal ...` verbs exist
only in a world whose [birth chain](../GLOSSARY.md#birth-chain) carries commit `87f00b4` (s41)
and, for the identity-events half alone, `39480ec` (s40) — runs are strictly linear, so an
already-scaffolded world gains none of this. If you want to try these commands today without
waiting for your next real world, scaffold a disposable one first —
[USER-GUIDE.md](USER-GUIDE.md) §3b has the `bootstrap/new-project.sh --new-world`
walkthrough — and play there; tear it down when done.

**Does MY world actually have s40/s41?** Run `./migrate <deployment-dir> --dry-run` from your
autoharn checkout (`<deployment-dir>` is the path to your scaffolded world). Per its own
documented behavior ([README.md §4](../README.md#4-bring-a-deployments-database-up-to-date-with-a-newer-kernel)):
it prints the resolved db/host/schema, then reports which deltas — by name — your world's
database is missing, by running each birth-chain entry's own `.detect.sql` check against your
live schema and stopping at the first one that reads false; nothing is applied under
`--dry-run`. Read straight from the verb's own source
(`bootstrap/migrate_core.py`): the two shapes you will actually see are `migrate: current
lineage head = <name>` followed by `migrate: '<deployment-name>' is already at the lineage
head. Nothing to migrate.` if s41 (or later) is already applied, or `migrate: missing (<n>):
s40-principal-identity-events, s41-principal-bindings-and-relations[, ...]` naming exactly
what your world lacks. There is no lighter-weight check than this — `distance-to-clean` does
not report lineage position — so this is the one command to run.

**How do I set up the principals in a new world?**
You mostly don't have to — a world born on this commit or later starts with a WORKING set of
principals, not an empty registry. Here is exactly what the scaffold already did for you, and
what to type for anything beyond that.

*What birth already gave you.* The scaffold's birth sequence, run once at `--new-world` time,
is three explicit, attributed acts, in order: (1) the connection principal `author` is
registered through the full s40 ceremony (self-attributed — the one genesis exception, since
nothing else exists yet to attribute it to) and its `principal_registered` event lands; (2) a
`principal_standing_declared` event binds the world's database role to `author` — this is the
"declared, not silent" default: it is why your very first `./led` write, with no
[`LED_ACTOR`](../GLOSSARY.md#principal) (the environment variable that names which registered
principal a `led` write is attributed to) set, just works; (3) `reviewer` and `commissioner`
are registered the same way, each with a stated purpose. Witnessed on a real `--new-world` scaffold run
(`seen-red/s40-principal-identity-events/red.txt`, case `new-world-birth-sequence`): *"scaffold
exit=0; registration events=3 (author, reviewer, commissioner), standing declarations=1; first
no-LED_ACTOR write exit=0, attributed 'author|declared-default'"*. If all you need is the
baseline three principals a solo operator's world already assumes, you are done — no further
setup required.

*Registering an additional principal.* `--purpose` is mandatory on an s40+ kernel; omit it and
you are refused, not silently ignored. The refusal below cites "AC-2," NIST 800-53's
Account Management control (the standard the registration ceremony's mandatory-purpose
requirement is grounded in — quoted verbatim below, not paraphrased). Witnessed
(`seen-red/s40-principal-identity-events/red.txt`, case `purpose-mandatory`, and the exact
refusal text from `bootstrap/templates/led.tmpl`'s own source):

```sh
$ ./led register-principal nopurpose model
```
```
led register-principal: REFUSED -- --purpose is mandatory on an s40 kernel: a
  registration is a recorded, attributed event with a stated purpose (AC-2's
  'account with a stated purpose'; kernel/lineage/s40-principal-identity-events.sql).
usage: led register-principal <name> <human|model|subagent|tool> --purpose "<why this identity exists>"
```
(exit 1). Supply `--purpose` and it constructs:
```sh
$ ./led register-principal reviewer2 model --purpose "second-tier model reviewer"
```
Re-registering the same name is never a silent no-op — both class polarities refuse loudly
(`seen-red/s40-principal-identity-events/red.txt`, cases `register-duplicate-same-class` and
`register-duplicate-class-mismatch`). Same class, same name again:
```
led register-principal: REFUSED -- principal 'reviewer2' is already registered
  (id <id>, class model, purpose: <purpose>). Re-registration is never a silent no-op
  (s40 §3.7 -- the panel's silent ON CONFLICT DO NOTHING class, closed): if you meant
  this existing principal, just use it (LED_ACTOR=reviewer2); if you meant a NEW
  identity, pick a new name.
```
A different class under the same name refuses too, naming the mismatch and pointing at
`./led principal relate <new> succeeds <old>` (once s41 has landed) as the way to record a
genuine identity succession rather than a rename — names are immutable by rule, and a class
change is a new identity, never an edit to the old one.

*Declaring standing.* This binds a database role's default attribution to a registered
principal — the same declared-not-silent act the scaffold performed for `author`. `--db-role` is optional
and defaults to your own world's connection role (read directly from `bootstrap/templates/led.tmpl`'s
source: `db_role="$ROLE"` unless overridden) — the same `role` value your deployment's own
`deployment.json` already carries (README.md's configuration table names this field; run `cat
<world-dir>/deployment.json` and look at `"role"` if you've forgotten it). For the common case
— rotating which principal your world's OWN connection role speaks for — you never need to
pass `--db-role` at all:
```sh
$ ./led principal declare-standing reviewer2
```
Only pass `--db-role <name>` explicitly when declaring standing for a DIFFERENT Postgres role
than the one your `deployment.json` already names — e.g. a second writer role your world's
kernel DDL granted separately (`\du` in `psql` lists every role that exists on the database if
you need to find one by hand). Re-declaring for the same role auto-supersedes the prior
declaration (this is how you rotate which principal a role speaks for).

*Binding a role.* Role text is free, non-empty, organizational text, not a closed vocabulary
(ratified §9(c) — role naming is organizational configuration, not the harness's to impose):
```sh
$ ./led principal bind-role reviewer2 --role "sql-review"
```

*Granting competence* — the [safety-critical-logging BRIEF](../law/briefs/safety-critical-logging/BRIEF.md)'s
**G13 record** (that document's required-work-product entry for "who is believed competent for
what safety activity, at what band, on what basis" — a competence assignment or its change),
recordable but NOT gating (nothing in v1 refuses an act for lack of a matching grant):
```sh
$ ./led principal grant-competence reviewer2 --activity "sql-review" --band "B" --basis "track record on s37-s39"
```
Witnessed lifecycle (`seen-red/s41-principal-bindings-and-relations/red.txt`, case
`competence-lifecycle`): *"grant OK (view: 'sql-review|B'); duplicate refused; empty band
refused (1); re-band via --supersedes replaced (band now 'A'); stray --band on withdrawal
refused; STALE supersession target refused; withdrawal OK (view 0 rows, raw 3 rows -- grant+
re-band+terminal withdrawal); raw inactive-from-birth refused by the kernel CHECK"*. The band
and basis fields are free text — the spec's own ratification (§9(g)) calls this a **placeholder
architecture only, not a considered final design**; do not read the free-text shape as a
settled judgment that a closed band vocabulary (ASIL/SIL/DAL-style) is never coming.

*Relating two principals* — the closed vocabulary is `acts-for`, `dispatched-by`,
`same-natural-person`, `succeeds`:
```sh
$ ./led principal relate reviewer2 acts-for reviewer3
```
Self-edges refuse at the kernel, both via the CLI and via a raw direct write
(`seen-red/s41-principal-bindings-and-relations/red.txt`, case `self-edges-refused`: *"all
four CLI self-edges refused=True; raw kernel-trigger self-edge exit=3 with the taught
text"*). `same-natural-person` is symmetric and canonicalized (stored lower-`id`-first
regardless of the order you type it), witnessed both orderings in case `snp-canonicalization`.

*Looking at what exists.* No dedicated `led principal list`/`show` verb ships in v1 — this is a
genuine gap, not a hidden feature (UNEXERCISED beyond the derived views themselves). The
sanctioned way to look today is the same "query the view directly" pattern the CLI already uses
internally for its own convenience reads (e.g. `led standing`'s own implementation is a plain
`SELECT * FROM standing_decisions`, per `bootstrap/templates/led.tmpl`): the human-readable
surface is the `principal_standing_current` view (name, class, standing, registered_at,
registrar, purpose — one row per principal); the binding surfaces are `principal_relations`,
`principal_role_bindings` (deliberately not `principal_roles` — that name is reserved for the
unrelated db-role↔principal binding view, `principal_role`), `principal_keys`, and
`principal_competences`. All four binding views show only currently-active, unsuperseded rows;
every retraction stays visible in the raw ledger history regardless.

*Suspending or revoking a principal, and the honest limit on getting back.*
```sh
$ ./led principal suspend reviewer2 "on leave"
$ ./led principal revoke reviewer2 "compromised"
```
Writes under a suspended-or-revoked principal then refuse at the kernel (witnessed,
`seen-red/s40-principal-identity-events/red.txt`, case `revoke-refuses-writes /
successor-passes`: revoked write exit=3, successor registration exit=0, successor write
exit=0). **No v1 verb lifts a suspension or a revocation, for either kind, and if both are
ever written for the same principal, `revoked` always wins the reported standing regardless of
which order they landed in** (case `precedence-both-orders`: *"suspend-then-revoke reads
'revoked', revoke-then-suspend reads 'revoked'"*). The only way back to an active identity is
registering a fresh successor principal and recording the succession:
```sh
$ ./led register-principal reviewer2-successor model --purpose "reviewer2's replacement identity"
$ ./led principal relate reviewer2-successor succeeds reviewer2
```
This is a new identity, not a reinstated old one — a real, if heavier, escape hatch, disclosed
as a deliberate v1 limit rather than an oversight.

**Can I use GPG to sign roles / authenticate myself as a principal?**
Answering exactly what was asked, in three honest parts — this is not a recommendation to go
generate a key; the standing deferral on key generation ("key generation/signing deferred until
all else banked; never re-raise as recommendation") is the maintainer's own ruling to lift, not
this page's to nudge him toward.

*(1) What exists now.* `led principal bind-key <name> --fingerprint "<fp>"` records an OpenPGP
v4 fingerprint against a HUMAN principal — a typed, dated, countersignable ledger row (a
`principal_key_bound` event), refused outright on any non-human subject
(`seen-red/s41-principal-bindings-and-relations/red.txt`, case `key-binding-polarity`: *"model
bind exit=3 (taught); human bind exit=0, view rows=1; malformed fingerprint exit=3 (kernel shape
CHECK named)"*). That is the whole of what's built: an empty-until-ceremony slot. **Nothing
anywhere verifies a signature against it.** "Signing a role," as a cryptographically verified
act, does not exist in v1 — a role binding (`led principal bind-role`) is an attributed,
countersignable ledger row, exactly like every other kind this project records; it is never a
signed object, and `bind-key` does not change that for any other kind.

*(2) What actually exercising this for real would require.* No maintainer keypair exists
anywhere in this project today —
[law/keys/README.md](../law/keys/README.md) states its directory's state plainly:
`AWAITING-KEY`, "no real maintainer keypair has been generated as of this writing." Rung 1 (the
signed-tag mechanism this directory backs) is built; it has never been armed. Exercising
`bind-key` for real, rather than against a throwaway test key, needs the one-time key generation
the maintainer's own standing ruling has deferred. If he chooses to lift that deferral, the
recipe is [design/MAINT-GPG-TRUST-LAYER.md](../design/MAINT-GPG-TRUST-LAYER.md) §7 (`gpg
--full-generate-key`, hardware-backed preferred so each signature costs a physical touch), then
`led principal bind-key <name> --fingerprint "<the generated fingerprint>"`. The ceremony shape
that DOES already exist today, on top of that binding, is an ordinary countersign — a review row
regarding the binding event, using the same verb every other ledger row is countersigned with:
```sh
$ ./led review <bind-key-row-id> attest technical "fingerprint verified against a witnessed key-signing party"
```
(`led review`'s independence argument requires a stamp-distinct invocation — one whose HMAC
stamp (the session-identifying tripwire described just below) differs from the row being
reviewed's own — for anything above `self-review`; see the verb's own usage text in
`bootstrap/templates/led.tmpl`.) A key-binding
proposal followed by a countersign on that same binding row therefore needs zero new review
machinery to close the loop — the binding event is just another countersignable ledger row, like
any other.

*(3) The honest limit.* Binding a fingerprint records custody of a key against an identity — it
does not authenticate sessions, and it does not make `bind-key` a login mechanism. The HMAC
stamp (`kernel/lineage/s17-stamp-mechanism.sql`) remains the tripwire that answers "which live
invocation wrote this row"; the key slot answers a different, narrower question ("who does this
fingerprint belong to"), and answers it only once someone actually signs something and a
verifier checks that signature — which nothing in this project does yet for a role or a
principal binding. Signature-*verified* acts are a future rung, not this one.

## Typed verdicts and refusal recording (s42/s43)

Like the principal-identity entries above, these three entries deviate from this page's usual
point-elsewhere convention (full witnessed output, not a one-liner plus a pointer) because the
surface is new: kernel deltas s42/s43 turn a refused write from a transaction that leaves no
trace into a committed, attributed ledger row, and widen the tamper-evidence hash chain to cover
every column instead of thirty. Delivery record:
[orchlog.d/s42-s43-typed-verdicts.md](../orchlog.d/s42-s43-typed-verdicts.md); full spec:
[FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md](../design/FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md).

**Prominent caveat, read before typing anything below:** none of this exists in a world whose
[birth chain](../GLOSSARY.md#birth-chain) predates commits `1fc4e8c` (s42) and `84729de` (s43) —
runs are strictly linear, so an already-scaffolded world gains nothing here. Run `./migrate
<deployment-dir> --dry-run` to see whether your world has s42/s43; if it names them as missing,
everything below is unavailable until your next real world is born on a checkout that carries
these commits.

**What happens now when a write is refused?**
Before s42/s43, a refused write was a `RAISE EXCEPTION` that aborted the transaction — the
attempt itself left no trace anywhere but a server log. After s43, the granted database role
holds NO `INSERT` privilege on any kernel-governed table at all; every write goes through one of
four functions (`kernel.ledger_write`, `review_write`, `registration_write`,
`obligation_write`), and a refusal caught inside one of them is committed as an ordinary
`write_refused` ledger row and handed back to the caller as a typed verdict — never a silent
abort. Witnessed (`seen-red/s43-typed-verdict-write-boundary/red.txt`, case 1): a write attempted
under a revoked principal returns

```
disposition=refused, sqlstate=P0001, refusal_id=<row id>
message: "Ledger policy: strict attribution (s40) — actor principal N is revoked ..."
```

and the ledger holds a COMMITTED `write_refused` row you can look at like any other row —
`refusal_sqlstate=P0001`, `refusal_surface='ledger'`, `refusal_attempted_actor=<the revoked
principal's id>`, `refusal_attempted_role='bork'` (the server-witnessed `session_user`, never
something the client asserted), `actor=<the write-boundary tool principal>` (never the attempted
actor itself — a refused principal cannot honestly author the record of its own refusal), and a
64-hex `refusal_payload_digest` (a SHA-256 of the attempted payload — the payload's actual
content is never stored, digest only —
[FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md](../design/FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md)'s
own rule R4, ratified for poison/privacy reasons: committing a refused payload verbatim would
hand an adversary a permanent, hash-chained storage channel). The row that was
attempted never lands; only the record that it was attempted, and refused, does.

**To look at `write_refused` rows directly:** they are ordinary ledger rows like any other, so
the same `psql`/`led show`/`./led` reading tools that work on any other row work here —
`kind = 'write_refused'` is the row to filter on, and the six `refusal_*` columns above are
where the detail lives. There is no dedicated `led` verb for this in v1 (a genuine gap, not a
hidden feature), so reading them today means a direct query or `./led show <row-id>` once you
have an id — e.g. from `./verify-chain`'s own reconciliation output (next entry) or from
scanning recent rows.

**The plain point worth internalizing: probing attempts leave traces now.** An agent (or a
person) trying a write it is not permitted to make — writing under a revoked identity, attempting
a malformed payload, retrying a refused registration — used to vanish into a rolled-back
transaction with nothing durable behind it but a server log line. After s42/s43 it does not
vanish: it becomes a permanent, attributed, hash-chained, countersignable row, exactly as durable
as a row that succeeded. This is true of ceremony refusals too, not just plain ledger writes —
review-ceremony refusals, registration-ceremony refusals (a duplicate name, a missing
`--purpose`), and malformed-payload refusals (an unknown key, a server-owned key, a bad value
cast) all journal the same way, as one `write_refused` row per refused attempt
(`seen-red/s43-typed-verdict-write-boundary/red.txt`, case 1).

**Two things this does NOT do, stated so the guarantee is not over-read.** A raw `INSERT`
attempted directly against `ledger` by the granted role never reaches the boundary at all — it
fails at the database privilege layer first (`permission denied for table ledger`, SQLSTATE
42501, witnessed case 2) and is NOT journaled as a `write_refused` row; its only residual trace
is the Postgres server log, which rotates. And a database superuser or schema owner can always
bypass every trigger and privilege check here — that bound is unchanged by this delta, and the
closing move against it remains a GPG-signed chain head (`verify-chain --head`), covered in
"Trust ceremonies" below.

**What does `verify-chain` check now?**
Two things changed, and a third check is new.

*Full coverage.* The one function the whole tamper-evidence chain rests on,
`compute_row_hash`, used to serialize only thirty of the ledger's columns (the set as of
2026-early kernel deltas) — every column added since then, twenty-two of them including all
twelve principal-identity columns, sat OUTSIDE the hash chain: a schema-owner tamper of, say,
which principal a revocation regards changed no hash, and `./verify-chain` reported the chain
`INTACT` right over the rewrite. Witnessed live, this exact scenario
(`seen-red/s42-row-hash-full-coverage/red.txt`, case 1):

```
verify-chain: INTACT -- 4 row(s) walked, head id=4 hash=<64-hex>
(exit 0)
```

— reported clean, immediately after an owner tampered `work_parent` on a committed row with
triggers disabled. After s42, `compute_row_hash` covers every ledger column except `row_hash`
itself (52 at the s42 head, 58 once s43's own six new columns are included), and the same class
of tamper is now caught (case 2, witnessed on all 52 columns individually, not sampled):

```
verify-chain: BROKEN -- first break at row id 19:
    stored:   <64-hex, the pre-tamper hash>
    expected: <64-hex, recomputed over the tampered content>
  (1 of 20 row(s) mismatch total. ...)
(exit 1)
```

*The completeness oracle — the `refusal_seq` reconciliation.* A non-transactional sequence
(`kernel.refusal_seq`) is bumped immediately before every `write_refused` row is journaled;
because a Postgres sequence's `nextval` is never rolled back, it counts every refusal attempt
that reached the boundary regardless of what happened to the surrounding transaction.
`./verify-chain` now compares the count of committed `write_refused` rows against this sequence.

*What `BROKEN` vs `FORGERY-SUSPECT` mean, and what to do on each* — drawn from the delta's own
guidance, stated plainly where the header gives no further operator action:

- **`BROKEN`** (a row's stored hash disagrees with a fresh recomputation over its own content,
  the ordinary chain-tamper report shown above): a row's content was altered after the fact.
  The delta's own header gives no remediation beyond the standing chain-integrity posture — this
  is a serious finding. **The disposition is: stop and consult, not improvise.** Do not attempt
  to "fix" a broken chain by editing rows or regenerating hashes yourself; treat it as evidence
  and escalate to whoever owns the world's integrity posture.
- **`FORGERY-SUSPECT`** (`REFUSAL-ORACLE-FORGERY-SUSPECT`, when the count of `write_refused`
  rows EXCEEDS what the sequence counted): only the boundary functions can mint a
  `write_refused` row through the sanctioned path — a payload that tries to claim
  `kind = 'write_refused'` directly is refused with a forgery-channel teach-text. This verdict
  means a `write_refused` row exists that the counting mechanism never saw mint — i.e. it was
  forged outside the sanctioned path (an owner-side direct INSERT bypassing the boundary
  entirely). Witnessed (`seen-red/s43-typed-verdict-write-boundary/red.txt`, case 3):
  ```
  verify-chain: REFUSAL-ORACLE-FORGERY-SUSPECT -- N journaled write_refused row(s) but
  the sequence only counted N-1 ... (exit 6; --head REFUSES)
  ```
  Same disposition as `BROKEN`: **stop and consult** — this is not a state to self-remediate,
  and `--head` itself refuses to sign over it. The opposite inequality (sequence count HIGHER
  than the row count) is NOT this failure — it is EXPLAIN-grade, with legitimate named causes
  (a client-side transaction that wrapped the boundary call and rolled it back; a journal-insert
  double failure) and does not, by itself, indicate tampering.
- `write_refused` rows are also unretractable by rule: nothing may supersede one
  ([FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md](../design/FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md)'s
  own rule R6, ratified).
  If you see a row attempting to supersede a `write_refused` row, that attempt is itself refused
  and journaled — it is not a state `verify-chain` needs a separate disposition for, because it
  cannot succeed in the first place.

## Standing lifecycle (s45)

Like the two sections above, this one deviates from the page's usual point-elsewhere
convention because the surface is new: kernel delta s45 gives two governance states — a
db_role's standing declaration, and a principal's suspension — a sanctioned way OUT, where
before s40/s41 there was only a way in. Delivery record:
[orchlog.d/s45-standing-lifecycle.md](../orchlog.d/s45-standing-lifecycle.md); full spec:
[design/FABLE-STANDING-LIFECYCLE-SPEC.md](../design/FABLE-STANDING-LIFECYCLE-SPEC.md).

**Prominent caveat, read before typing anything below:** none of this exists in a world whose
[birth chain](../GLOSSARY.md#birth-chain) predates commit `94f5b7a` — runs are strictly linear,
so an already-scaffolded world gains nothing here. Run `./migrate <deployment-dir> --dry-run`
to see whether your world has s45; if it names it as missing, the two verbs below are
unavailable until your next real world is born on a checkout that carries this commit.

**What does "unbind" mean, and what do I type?** A db_role's standing declaration (the
"anonymous writes on this connection count as principal X" default that
`./led principal declare-standing` sets) can be repointed to a different principal any number
of times, but before s45 it could never be turned OFF — the only escapes were suspending the
bound principal (which blocks that identity on every channel, not just this role) or pointing
the role at a fabricated tombstone principal (a real misattribution risk). s45 adds a
sanctioned third way:

```sh
$ ./led principal undeclare-standing
```

(`--db-role <role>` is only needed if you are unbinding a role other than your own
deployment's connection role — the common case needs no flag.) After this, an anonymous write
on that role (no `LED_ACTOR` set) refuses again, exactly as it would on a role that was never
declared for — a fresh `./led principal declare-standing <name>` re-binds it. **This is
forward-only**: rows already written under the old declaration keep their old attribution
forever. If the reason for unbinding is that past rows were misattributed, that is a job for
the defeat pipeline below (a mismatch attestation, not a retroactive rewrite) — nothing in
s45 touches history.

**What does "suspension is liftable" mean, and what do I type?** Before s45, `./led principal
suspend` had no reverse — suspension degenerated into a soft, permanent revocation in
practice, even though the vocabulary implied it was temporary. s45 makes it genuinely
reversible:

```sh
$ ./led principal suspend reviewer2 "on leave"
$ ./led principal lift-suspension reviewer2
```

Once lifted, `reviewer2`'s writes are accepted again. **Revocation stays terminal by type —
this is the other half of the same delta: it was always a disclosed design limit, and it is
now enforced by the kernel itself, not merely unbuilt.** There is no verb, in this or any prior version, that reverses a
revocation: a lift-shaped revocation row is structurally unrepresentable (the same
`principal_binding_active` flag that suspension uses is refused outright on the revoked kind),
and a kernel-level supersession rule refuses any attempt to hide a revocation behind an
unrelated superseding row. `lift-suspension` on a principal that is both suspended and revoked
still writes the lift (and warns that standing stays `revoked`, because revocation dominates
suspension in the reported standing) — it changes nothing about the revocation. The only way
back from a revocation remains what s40/s41 already gave you: register a fresh successor
principal and record `./led principal relate <new> succeeds <old>`.

**Does lifting a suspension restore credit for what the principal wrote while suspended?**
No, and this is worth internalizing before it looks like a bug: standing (suspended, revoked,
active) never conditions defeat. Suspending or revoking a principal gates its *future* writes
only; it never withdraws or discounts anything that principal already wrote, and lifting a
suspension changes nothing about which of its past rows are credited. The only sanctioned
lever over whether a specific row is credited is a mismatch attestation under the defeat
pipeline, covered in the next section. This was a maintainer ruling (ledger row 1481,
2026-07-18), named here because a future reader who notices a suspended principal's old work
still counting is looking at the design, not a defect.

**EXISTING WORLDS GAIN NOTHING HERE, restated because it matters most.** Both mechanisms above
are authored, scratch-witnessed, and wired into the scaffold's lineage chain only — they reach
reality solely at a *future* world's birth. If your world predates `94f5b7a`, `undeclare-standing`
and `lift-suspension` are not verbs your `led` script has; `./migrate --dry-run` will name
`s45-standing-lifecycle` among the missing deltas.

**Honest limits.** A schema owner/superuser can bypass every trigger this delta adds, the
standing disclosed bound every kernel delta carries. The duplicate-active suspension guard is
CLI-side, so a direct (non-CLI) writer can still stack multiple suspensions on one principal,
each then needing its own lift. And in a solo world whose only active principal is suspended,
lifting that suspension needs a *second* active principal to write it — s45 narrows this
dead-end from "impossible" to "needs one more registered principal," but does not close it; a
truly solo, fully-suspended world still needs a schema-owner act to recover.

## Model identity: watchdog, attestation, defeat

Three pieces landed together as one arc, answering "if a session's serving model gets silently
substituted, how would I know, and what happens to what it already wrote?" Delivery record:
[orchlog.d/defeat-pipeline-and-otel-identity.md](../orchlog.d/defeat-pipeline-and-otel-identity.md);
full specs:
[design/FABLE-OTEL-SENTRY-SPEC.md](../design/FABLE-OTEL-SENTRY-SPEC.md) (including its dated A1/A2
amendments) and
[design/FABLE-DEFEAT-PIPELINE-SPEC.md](../design/FABLE-DEFEAT-PIPELINE-SPEC.md) (including its dated A1
amendment).

**Read this once, before anything else on this topic: none of it is a guarantee.** Every layer
below — the watchdog, the attestations, the defeat derivation — authenticates a *pipe* (a
process, a channel, a database write path); nothing anywhere authenticates the emitter's
honesty, because the model-identity string originates inside the unauthenticated CLI process
itself. This is stated plainly in the sentry spec's own §7 standing rebuttals and carried
forward here rather than oversold: everything on this page is audit-supporting
evidence, never authentication (in NIST 800-53 terms, for readers who want the mapping: the
AU control family, never IA-2). A dishonest or silent session is observed as nothing and
defeats nothing — absence of telemetry proves nothing, permanently, in either direction.

**How would I actually notice a model substitution as it happens?** The watchdog
(`otel-watch`) is a small always-on process that tails the local OTel collector's export and
compares each request's observed model against the session's declared expected model; on a
mismatch it calls a mail-notification script (on this host, the maintainer's own
`notify.py`, the one that already makes his phone beep on turn completion — if you are not
him, wire your own notifier there; the watchdog just executes the configured script), so a
substitution surfaces within seconds rather than at the next audit. It writes nothing to the ledger — it is notification, not evidence. A session with no
declared expectation is reported as *unwatched*, loudly, so you can never mistake silence for
"watched and clean." **UNWITNESSED for this page:** the watchdog's own witness legs were not
re-run to produce this entry; treat its behavior as spec'd, not freshly observed here.

**How do I get a post-hoc, ledger-recorded answer for rows already written?** `./otel-attest`
is a batch verb (not a daemon) that correlates ledger rows against the collector's export and
writes one defeasible attestation row per attributable row, at one of four closed confidence
grades naming the strength of the join that earned it:

- `exact-command` — the row's own command is tied to one specific, bracketing request.
- `turn-bracketed` — command detail unavailable, but every request in the row's turn window
  agrees on one model.
- `session-scoped` — bracketing is ambiguous, but every request in the session's covering
  window still names one model.
- `ambiguous` — the window shows more than one model, or a load-bearing join failed. **As of a
  2026-07-18 spec amendment, an ambiguous attestation always writes `model=unresolved`** — never
  a fabricated single model, never an invented multi-model packing. The conflicting models are
  named in the row's `basis=` field instead. If every candidate in the window contradicts the
  declared expectation, the verdict is still `MISMATCH` (which model is unclear, but the
  substitution is not); if at least one candidate matches, the verdict is `unevaluated`; an
  ambiguous row is never written `match`. Two edge cases (the spec's A1 addendum): an
  *empty* candidate window — ambiguity via join failure, nothing in evidence at all — is
  `unevaluated`, never MISMATCH (zero evidence proves nothing); and a session with no
  declared expected model is also `unevaluated` — there is nothing to contradict.

No row is written at all when no correlated telemetry exists — absence of events is never
treated as evidence.

**A MISMATCH or ambiguous attestation is easy to miss if you only look at attestation rows —
does it surface anywhere else?** Yes: any attestation whose verdict is `MISMATCH` (including an
`ambiguous` row whose verdict resolves to `MISMATCH` per the rule above) additionally writes a
companion `finding` ledger row, so it lands in ordinary review flow instead of sitting quietly
in attestation bulk.

**What happened to `./otel-attest`'s first build, and is it safe to use now?** It was
adversarially reviewed (ledger row 1505) and found to silently fold every `ambiguous` case into
the write-nothing path — the opposite of the spec's own rule. The verb was held out of service
until the fix landed (commit `c3301e5`) and is back in service now, with the `model=unresolved`
behavior above, plus a write-time refusal on any field value containing a `|` or newline (an
unauthenticated model string could otherwise corrupt the row's later parse).

**How do I see what a MISMATCH actually does to derived standing?** `./judge --layer defeat`
derives it: a ledger row backed by an unsuperseded mismatch attestation, written by a principal
holding an unsuperseded, active competence grant for `model-identity-attestation`, is excluded
from the `credited` reading, computed fresh by two independent producers (a SQL twin and an ASP
program) required to agree bit-for-bit. Nothing is edited or deleted — a defeated row stays
fully visible in raw history, always shown together with its cause. **WITNESSED**, run
read-only against this repository's own live world (2026-07-18):

```sh
$ ./judge --layer defeat
```
```
# marriage differential -- layer='defeat'
#   closed verdict vocabulary: ['AGREE', 'DIVERGE_BY_DESIGN', 'DIVERGE_DEFECT', 'QUARANTINED']; RED = ['DIVERGE_DEFECT', 'QUARANTINED']

  [!! ] autoharn1 QUARANTINED        asp=0 sql=0 atoms; Δasp=[] Δsql=[]
          asp QUARANTINED: EDB export failed: CapabilityError: target 'autoharn1' did not emit trust_grant/n (capability absent): no principal_binding_active/principal_competence_activity columns on this schema (pre-s41 lineage) -- capability absent, not record-empty. A silent empty here would be the F49 vacuous-pass; refusing loudly.
          sql QUARANTINED: EDB export failed: CapabilityError: target 'autoharn1' did not emit trust_grant/n (capability absent): no principal_binding_active/principal_competence_activity columns on this schema (pre-s41 lineage) -- capability absent, not record-empty. A silent empty here would be the F49 vacuous-pass; refusing loudly.

# DIFFERENTIAL RED -- a target diverged/quarantined (NO RESULT)
```

This is a QUARANTINE, not a bug: the defeat pipeline needs typed competence grants (s41) to
derive anything, and this repository's own live world predates s41, so both producers refuse
loudly with the same named reason rather than silently reading an empty derivation as "nothing
is defeated" — the exact vacuous-pass mistake this design forecloses on purpose. A world whose
birth chain carries s41 or later will derive real `credited`/`model_defeated` results here
instead of this refusal.

**Does suspending or revoking the attesting principal change what it already defeated?** No —
see "Standing lifecycle (s45)" above: standing never conditions defeat, by ratified rule. A
suspended or revoked principal's past mismatch attestations, under a still-in-force competence
grant, keep defeating exactly as before; only superseding the grant or the attestation itself
changes what is credited.

**Honest limits, carried forward rather than oversold:**

- The ceiling is permanent, not a v1 gap: nothing here can ever prove which model served a
  request, only observe and record what the emitting process claimed. The sentry spec names the
  one thing that would close this — provider-side response signing — and it does not exist.
- The watchdog fails silent on its own death or a mail failure; a `--heartbeat` option is an
  opt-in mitigation, not a default.
- The typed kernel form of an attestation (kernel delta `s44`) and its dedicated credited-read
  views are authored in the specs above but not yet in any birth chain; until an s44+ world
  exists, `./otel-attest`'s rows are ordinary `verification` rows, and the engine-side
  computation shown above is the only way to see `credited`/`model_defeated` at all.
- A malformed attestation row halts derivation for its whole target until it is superseded —
  deliberate (fail loud beats skip silent), but a real operational cost if it happens.

## Trust ceremonies

**Can I prove a commission really came from me?** (a "commission" here is a ledgered
instruction attributed to a principal — the maintainer or an agent acting for them — and the
question is how strongly that attribution can be trusted). Full grammar and worked walkthrough:
[USER-GPG-TRUST-LAYER-FAQ.md](USER-GPG-TRUST-LAYER-FAQ.md) §5–§7.
Yes, and it comes in three increasing strengths: **LAZY** (the row's stated actor is taken on
its word, no cryptographic or structural check), **FULL** (the right actor recorded on the row,
plus the absence of the interception stamp a hook adds only when an agent — not the maintainer
directly — wrote the row: a rebuttable presumption, not proof), and **SIGNED** (a detached GPG
signature over the row, checked against a known key — the only strength that survives a
dispute). The standing rule is that a **CONTESTED** commission (one whose attributed actor is
disputed after the fact) must be SIGNED to stand. You can rehearse every ceremony with a
throwaway key before any real key exists.

**Can I anchor the ledger so later tampering is provable?**
Yes — sign the chain head at run close (`verify-chain --head`, then a detached signature).
Any retroactive row alteration then breaks provably against a head your key vouches for;
the head also carries the apparatus-config hash, so a mechanism flipped off between two
signed heads is provable by comparing them. Known honest limits: the chain-hash mechanism proves
tampering with rows *between* two signed heads, but a deleted row at the very tail of the chain
(the newest end, appended after the last signature) is invisible to the chain alone — nothing
has signed over it yet (tracker item `s26-tail-deletion-witness` holds the designed fix — a
ledger row, not a committed page: `./led show s26-tail-deletion-witness` at the repository root
reads it), and the
apparatus comparison is manual, not auto-flagged.
Walkthrough: [USER-GPG-TRUST-LAYER-FAQ.md](USER-GPG-TRUST-LAYER-FAQ.md) §6.

## Review discipline

**Is a review's content ever checked, or does any countersign discharge the obligation?**
Partly. [`review_gap`](../GLOSSARY.md#review_gap)'s own discharge test never looks at what a
review says — any unsuperseded, distinct-actor `attest` clears the obligation regardless of
content, by design. A separate, layered check DOES inspect the discharging review's own
statement: `./audit --review-gap` flags a discharge whose whitespace-normalized statement is
shorter than `CONTENT_FREE_STATEMENT_THRESHOLD` (40 chars,
[engine/review_gap_thresholds.py](../engine/review_gap_thresholds.py)) — the case this check
answers to was a real 4-char `"test"` review that silently discharged a genuine obligation.
Honest limit, in the check's own vocabulary: it is a length heuristic, so its verdict is
`FLAGGED`, never `VIOLATED` — a genuine terse review passes ("Confirmed, matches row 4's stated
criteria exactly." is 51 chars) and hollow-but-plausible prose of ordinary length ("Reviewed and
everything looks correct, no issues found, approved for merge.") is NOT caught; the check catches
the "test"-shaped instance, not the class, and never substitutes for a human reading the review.
This exit code (6) is reachable only through `--review-gap`, and only when nothing earlier
already raised the exit and at least one review is flagged. Witnessed both polarities:
[seen-red/content-free-review-audit/](../seen-red/content-free-review-audit).

<!-- doc-attest-exempt: this single Q&A entry (kernel/lineage/s56-reservation-residue.sql,
design/FABLE-RESERVATION-RESIDUE-SPEC.md) is new prose added by a single-session Sonnet builder;
no live A:B:C loop was run (this session cannot fork a genuinely fresh reviewer, the same limit
named at ADR-0012's own doc-attest-exempt marker) and this marker does not claim one did. Content
is witnessed against a live fixture (seen-red/reservation-residue/), not merely asserted. Flagged
to the maintainer as a standing exemption on this entry rather than a wholesale one -- a genuine
A:B:C pass over this page should still happen, and this marker's scope is exactly the one
paragraph immediately below, not the rest of the file (which the gate's per-file-not-per-
paragraph mechanics cannot express more narrowly than this). Removal condition: strike when a
real A:B:C attestation covers this page. -->

**I countersigned with a concern instead of a clean pass — does that discharge the review
obligation, or does it leave the gate stuck open?** It discharges (kernel/lineage/
s56-reservation-residue.sql, design/FABLE-RESERVATION-RESIDUE-SPEC.md, maintainer-ratified
2026-07-22): `./led review <close-row-id> attest_with_reservations <independence> <your
concern...>` clears `review_gap`/`work_review_gap`/`work_item_strict_blockers` exactly as a plain
`attest` does — the verdict is final the moment it is recorded. The reservation itself does not
vanish: it lands on [`reservations_outstanding`](../GLOSSARY.md#reservations_outstanding) and
stays there until it is itself dispositioned — either supersede the reservation-carrying review
row, or have a DIFFERENT actor write a plain `attest` review *regarding the reservation review's
own row id*. (The original reviewer withdrawing their own concern is a real path too, but it
goes through the supersession leg, not this one: writing a fresh review *regarding their own
prior review* is refused as self-review — the standing segregation-of-duties check,
`kernel/lineage/s21-session-aware-distinctness.sql`, untouched by this delta — applies to a
review of a review exactly as it does to a review of anything else. Witnessed live,
[seen-red/reservation-residue/](../seen-red/reservation-residue).) Before this delta a
reservation-carrying countersign left the item indistinguishable from one nobody reviewed at
all, which rewarded fabricating a clean `attest` to satisfy the gate rather than recording the
honest concern — this closes that incentive while keeping the concern visible.
[`review_verdicts`](../GLOSSARY.md#review-verdicts) is the general read path for "what did this
review actually say" (verdict, independence, basis, antecedent, and whether it was later
superseded) when `review_gap`'s own pass/fail view isn't enough.

**How do I make an implementation step mechanically wait on a review step, instead of relying on
remembered discipline?** Arm `decomposition_review` — a third, independent PreToolUse mechanism in
[hooks/pretooluse_change_gate.py](../hooks/pretooluse_change_gate.py), alongside `change_gate`
(the ticket/window check) and `permit_to_work` (the open-claim check). It exists because a claimed,
open work item proves *permission* to work, never that the item's own decomposition — its plan, its
acceptance criteria — was ever looked at by anyone but its author: on this project's own record, a
claimed task's implementation began six seconds after claim, roughly 2.5 minutes ahead of the
countersign verdict that was supposed to gate it (the run12 specimen, named in the hook's own
docstring). A serious adopting organization should read that specimen as a *class*, not a one-off:
any harness that lets an agent dispatch straight from "plan accepted in principle" to "editing files"
carries the same race, and self-disclosed recurrences of exactly this shape are on record upstream
too, filed as [anthropics/claude-code#77900](https://github.com/anthropics/claude-code/issues/77900).
`decomposition_review` closes it by refusing a substantive `Write`/`Edit`/`NotebookEdit` — or a
governed-file-mutating `Bash` command — anywhere under the world's root while the claimed work
item's own opening act (`work_opened`) carries an undischarged
[`countersign_obligation`](../GLOSSARY.md#obligation): the same [`review_gap`](../GLOSSARY.md#review_gap)
discharge test every other obligated row already uses, not a second hand-rolled predicate.

Arming it is three steps, and none of them is optional-by-omission — a world that skips any one of
the three is unarmed, silently:

1. **Obligate the actor whose decompositions need outside eyes:**
   `./led obligate decomposition-review <reviewer-principal> <worker-principal>` (the worker is the
   *obliged* actor — get the direction backwards and you obligate the reviewer instead, a mistake
   this project's own `led obligate` usage text calls out by name because it has happened twice).
   **Second warning, repeated here at the copy point because the CLI's usage text carries it and
   this recipe previously did not** (a downstream deployment caught the omission before arming,
   2026-07-17): the `decomposition-review` word above is a free-text LABEL, not a filter —
   `review_gap` joins on actor identity alone, so once a principal is obliged, EVERY
   uncountersigned row that principal writes, of any kind, accumulates review-gap debt until a
   distinct actor countersigns it. Obliging a session's general working identity (the `author`
   that writes every `decision`/`finding` row) makes nearly every row that session writes need a
   countersign — an operational cost far larger than the label suggests. The narrower recipe that
   bounds the blast radius: register a dedicated principal used EXCLUSIVELY to open
   decompositions (`LED_ACTOR=<dedicated-name> ./led work open ...`), and obligate that. The
   bound holds only as long as the dedicated principal is never reused for other writes — the
   over-catch returns the moment it is.
2. **Flip the mode to `enforce`** in `.claude/apparatus.json`:
   `"mechanisms": {"decomposition_review": {"mode": "enforce"}}` — see
   [bootstrap/templates/APPARATUS.md](../bootstrap/templates/APPARATUS.md) for the full switchboard.
3. **Verify it is actually armed before trusting it.** `led decomposition-review-status` is the
   purpose-built verb for this — it prints the resolved mode, the obligation-table row counts, and a
   one-line verdict (`ARMED-ENFORCING` / `ARMED-OBSERVING` / `VACUOUS` / `OFF`) — but as of this
   writing it exists only on the unmerged `build/effective-state-display` branch, not yet on this
   page's own base; check its own repository state before assuming it is present in yours. Until it
   lands, or if it has not landed in your checkout, read the same two raw facts by hand: (a) `cat
   .claude/apparatus.json` for `mechanisms.decomposition_review.mode` (missing entirely means the
   mechanism's own default, `observe`, applies — see below); (b) `./led review-gap`, cross-read
   against `./led work list` for which slug is currently open and claimed — if that slug's
   `work_opened` row appears in the `review-gap` output, the obligation is live and undischarged.

**The shipped default is `observe`, not `enforce` — deliberately, and unlike its two sibling
mechanisms.** `change_gate` and `permit_to_work` both default to `enforce` because they are free per
call and were already the project's steady state before per-mechanism modes existed.
`decomposition_review` is new machinery: an already-running, already-scaffolded world would find its
writes newly gated the moment `hooks/` is updated, with no operator opt-in — so this one mechanism
defaults to the weaker mode on purpose, and arming it to `enforce` is a one-line, per-world decision
an operator makes deliberately (see the module docstring's own "DECOMPOSITION-REVIEW BLOCKER"
section for the reasoning in full). A serious adopting organization should read this the same way:
the mechanism ships inert everywhere, and an unarmed world is not a bug, it is the honest starting
state — arming it is a policy choice belonging to whoever owns the world, not something a scaffold
should spring on a project mid-flight.

**What is, and is not, witnessed for this mechanism specifically.** PreToolUse hooks demonstrably
fire on a dispatched subagent's own tool calls — 24 specimens of `change_gate` (this same script,
this same invocation path) denying a subagent's edit are recorded in the upstream autoharn ledger,
decision row 1295 (2026-07-17 "two-spy synthesis" — one ledger row combining two independent
observer sessions' findings, "Spy A" and "Spy B" in the row's own text, into a single record
rather than filing each separately); the underlying session transcripts remain local
evidence per the project's auditability ruling — the ledger row is the citable record. What had
NOT been separately witnessed, because every previously-observed world carried zero
`countersign_obligation` rows under the shipped `observe` default, is `decomposition_review` itself
actually blocking anything. A scratch world (`decompprobe`, scaffolded via
`bootstrap/new-project.sh --new-world`, torn down completely afterward) closes that gap directly:
with a claimed work item's decomposition obligated and the mode flipped to `enforce`, invoking
`hooks/pretooluse_change_gate.py` with a real `PreToolUse` `Write` event on stdin produced

```
Ledger policy (decomposition-review-blocker): work item 'probe-task' (work_opened row 2) carries an
undischarged decomposition-review obligation — executing a claimed work item before its OWN
decomposition is countersigned makes every subtask a bet on an unreviewed plan (the run12 specimen:
task 1's implementation began 6 seconds after claim, ~2.5 minutes ahead of the countersign verdict
that was supposed to gate it). Discharge it, THEN retry the same edit: ...
```

(exit code 2, `permissionDecision: "deny"`). Discharging the obligation — a distinct-actor
`self-review` countersign, disclosed as such (the solo-world fallback this project's own scaffolded
`CLAUDE.md` documents) — and re-issuing the byte-identical event then produced exit code 0 with no
deny output at all: the same claimed item, the same edit, only the obligation's discharge state
changed. Flipping the mode back to `observe` and re-issuing the same event against a fresh
undischarged obligation produced `permissionDecision: "allow"` with an `additionalContext` field
opening `[apparatus observe-mode WARNING — would DENY under enforce] Ledger policy
(decomposition-review-blocker): ...` — the warn-not-block contrast, same check, same undischarged
state, only the mode differed. **What closes the crux is the composition of these two witnesses, not
either alone**: the ledger-recorded subagent specimens (decision row 1295) establish that this hook
script fires on a dispatched subagent's own tool calls at all; this scratch-world test establishes that
`decomposition_review`'s own deny path, once armed, actually fires for an undischarged obligation.
Neither witness alone would close it — the subagent specimens never exercised `decomposition_review`
armed, and this test never dispatched through a subagent.

**Should compliance review run per-commit or per-changeset?**
Per-changeset, at minimum — one reviewer reading the entire multi-commit changeset against the
LAW together, rather than one reviewer per commit checking each commit in isolation. The
reason is not caution for its own sake: a defect can live entirely in the INTERACTION of two
individually-correct commits, and no per-commit review ever sees that interaction, because
each commit, read alone, is fine.

The witnessed specimen (via decision row 1295's two-spy synthesis, citing the autoharn-panel
deployment's own row 590, named here only as history): a backend commit that validated
`limit=0` as a rejected input, and a frontend commit that messaged that same `limit=0` case to
the end user, landed about a minute apart as two separate commits. Each commit was correct in
isolation — the backend validation was sound on its own, the frontend messaging was sound on
its own — and the pairing was a regression, caught only because the review that found it
spanned both commits together, not because either commit's own review flagged anything.

Honest trade-off, stated plainly rather than left implicit: a whole-changeset review costs more
context per review round (the reviewer holds every commit in the set at once, not one at a
time) and arrives later than a per-commit review would (it waits for the changeset to close
rather than firing on each commit as it lands). The recipe is span-at-least-the-changeset for
LAW/compliance review — not never-review-early; a fast per-commit pass can still run as a first
filter, but it is not a substitute for the changeset-spanning pass, which is the only one
positioned to catch an interaction defect between two commits that are each correct alone.

**How do I make sure an item can't be started before its preconditions are met?** The maintainer's
own question, verbatim: "do we have some kind of way to ensure that items ... are not 'opened' or
'started' until preconditions are met? So that a hook can tell the agent 'don't do that, do the
right thing instead'?" Three separate mechanisms answer three separate moments in a work item's
life — none of them alone is the whole answer, and knowing which moment each one guards is the
point of this entry.

1. **`--type blocks-start` (claim-time, kernel/lineage/s39-blocks-start.sql).** `./led work depends
   <slug> <on-slug> --type blocks-start` records that `<slug>` may not be CLAIMED until `<on-slug>`
   reaches CLOSED. `./led work claim <slug>` is refused at construction while any direct,
   in-force blocks-start antecedent is unresolved, naming every unresolved antecedent by slug —
   the exact "don't do that" refusal the maintainer's question asks for, fired at the moment work
   would actually begin. `./led work startable` lists every open, unclaimed item with no such
   refusal pending right now — the "what can I legitimately start" query. Honest limits: direct
   antecedents only, not a transitive walk (an item three hops upstream of an unresolved
   precondition is not itself refused — widen `work_item_blocks_start_blockers` if you need that);
   and it binds only the ledger's OWN claim path — an agent that edits files without ever running
   `./led work claim` never trips this refusal at all (see point 3).
2. **`decomposition_review` (write-time, the armed mechanism).** Already covered in full under
   "Review discipline" above — a *claimed, open* work item only proves permission to work, never
   that its own decomposition (the plan, the acceptance criteria) was ever reviewed.
   `decomposition_review` closes that different gap: it refuses a substantive `Write`/`Edit`/
   `NotebookEdit` (or a governed-file-mutating `Bash` command) while the claimed item's own opening
   act carries an undischarged `countersign_obligation`. This is a PreToolUse hook, not a ledger
   refusal — it fires on the *tool call*, not the claim.
3. **`--type blocks-close` (close-time, kernel/lineage/s30-typed-dependency-edges.sql).** The
   oldest of the three: `--type blocks-close` refuses a `--strict` close (or the strict-by-type
   discharge of a composite item) while the antecedent is unresolved. It guards the *end* of the
   work, not the start — an item can be opened, claimed, and worked on with a blocks-close
   antecedent still unresolved; only its own strict close is refused.

**The composition point, stated plainly because no single mechanism above is complete on its
own.** Full structural foreclosure of "started before its precondition" is TWO gates together, not
one: **claim-gating** (point 1) for any work that goes through the ledgered `./led work claim` path,
**PLUS** the write-gate (point 2) for an agent that skips claiming and edits files directly. Neither
alone closes the class — a `blocks-start` edge with no `decomposition_review` armed cannot stop an
agent that never claims the item and edits anyway; `decomposition_review` armed with no
`blocks-start` edge recorded has no *precondition* fact to check at all, only a review-obligation
one. `--type blocks-close` (point 3) is a THIRD, later gate — closing time, not starting time — and
is not a substitute for either of the first two, though all three commonly apply to the same item
(an antecedent that must be finished before X starts is very often also load-bearing for X's own
strict close).

## Classifying audit/diagnostic findings

**I have a batch of findings from a code audit or review, and sorting them into categories
keeps producing overlapping or incomplete buckets — is there a standard way to do this?** Yes —
split every narrative finding (one that bundles more than one bug or observation) into single-
actionable-unit atoms first, with a provenance link back to where each atom came from, THEN
classify; once every unit is atomic, "did we cover everything" and "does nothing overlap" become
a one-line mechanical check instead of a manual sweep. A second pass then re-clusters the atoms
into
[fix-authorship blocks](ORCH-FINDING-ATOMIZATION-RECIPE.md#stage-2--reconstitute-atoms-into-blocks-author-fixes-at-the-block-grain-not-the-atomic-grain)
by shared invariant, so one typed fix forecloses a whole class of bugs
rather than patching each atom instance-by-instance. Full method, its adjudication against this
corpus, and its relation to
[ADR-0000's typed-fix discipline](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md):
[ORCH-FINDING-ATOMIZATION-RECIPE.md](ORCH-FINDING-ATOMIZATION-RECIPE.md).

## Capturing errors so they cannot quietly recur (ADR-0000 / ADR-0011)

**Can I leverage autoharn to automate the process of capturing errors before they happen
again, à la ADRs 0000 and 0011?** Yes — the discipline exists, it is mostly typing rather
than tooling, and it ran end-to-end on a live specimen on 2026-07-18 (the SQL-injection
class: captured as ledger row 1637, named as a class in the same day's
[ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md) and
[ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md) amendments, swept
across every sibling script under row 1643, and banked as re-runnable red fixtures). The
recipe, in the order the ADRs bind it:

1. **Type the error as a CLASS, not an anecdote.** When a defect surfaces, write a ledger
   row that names the class it instantiates — firmer vocabulary than a prose "snag". The
   suggested shape is a sibling statement grammar to `estimate:`/`actual:`
   ([USER-RETROSPECTIVE-RECIPE.md](USER-RETROSPECTIVE-RECIPE.md)'s convention family):
   `defect: <CLASS-SLUG> | <SPECIMEN> | <FORECLOSING-FIX> | <REFS>` — one row per
   class, the specimen quoted, the refs pointing at the incident, and the
   foreclosing-fix field holding the fix once typed, or the literal word `open` while
   it is still outstanding. This is a CONVENTION in
   v1, deliberately unvalidated: per [ADR-0011](../law/adr/0011-mechanization-discipline.md),
   an intake validator is minted when a malformed row is witnessed recurring, not before.
2. **Ask ADR-0000's Rule 2 pair before authoring any fix**: (a) what type forecloses the
   whole class, and (b) what operational lapse let it recur — the answers belong in the
   same row's foreclosing-fix field or its follow-up.
3. **Bank the red.** A closed defect gets a `seen-red/` fixture registered in the
   fixture census ([gates/fixture_census.py](../gates/fixture_census.py)) — after that,
   silent reintroduction is mechanically impossible: the fixture is a standing
   re-executable witness, which is the reintroduction-blocking half, already built.
4. **Cross-check on the next incident.** Before fixing anything new, query the ledger for
   the class (`./led` search over `defect:` rows); a hit converts "fix this bug" into
   "this class RECURRED", which is exactly ADR-0011's trigger to mint a mechanical check.
   The A:B:C loop's named defect catalogue
   ([ORCH-ABC-AUDIT-LOOP-RECIPE.md](ORCH-ABC-AUDIT-LOOP-RECIPE.md)) is this same pattern
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
([ADR-0011](../law/adr/0011-mechanization-discipline.md)'s Context): *"a design document that
quietly goes stale while the code it describes moves on, a duplicated fact whose two copies
drift apart one edit at a time"* — the invisible-at-authoring, visible-only-in-aggregate defect.
**Drift** is what happens to any DEPENDENT artifact that claims to reflect an AUTHORITY: the
authority moves, the dependent stays, and nothing notices until a reader trusts the stale copy.
A **drift backstop** is a mechanical comparator over one such declared pair, and every instance
in this repository is the same five moves with different types plugged in:

1. **Name the pair.** One side is the authority (the single source of truth —
   [ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md)'s Principle 1, one owner
   per fact); the other is the
   dependent that claims to correspond to it. If you cannot say which side is authoritative,
   that ambiguity is the defect to fix before any checker is worth building.
2. **Derive both sides mechanically at check time** — from filenames, the live database catalog,
   `git ls-files`, the file's own bytes — never from a hand-maintained second list. A hand list
   is itself a dependent that drifts: [filing/apparatus_registry.py](../filing/apparatus_registry.py)'s
   own docstring records that a hand-typed mechanism-name list HAD already drifted, silently
   (a real, wired-in mechanism was absent from it), before the derived set replaced it.
3. **Compare with a comparator that quantifies over the class**
   ([ADR-0011](../law/adr/0011-mechanization-discipline.md) Rule 4): any future column, delta,
   link, or key is in scope by construction. An enumeration of today's instances fails open at
   the next instance — which is drift's own front door.
4. **Refuse loud, teaching the honest discharge paths**: refresh the dependent, or DECLARE the
   divergence explicitly (an honest lag note, a `--declare-change` naming what moved). Silence
   never discharges; a declared lag is a recorded fact, not a pass.
5. **Backstop the backstop.** The comparator gets its own both-polarity
   [seen-red](../GLOSSARY.md#seen-red) proof and a
   [fixture-census](../GLOSSARY.md#fixture-census) registration, ships WITH the fix that closes
   the first witnessed drift (ADR-0011's 2026-07-02 amendment: the mechanism is minted with the
   first fix, not after a recurrence), and runs on a declared rhythm — per-commit, at
   acceptance, at cut time, or as an on-demand verb.

When the authority side has no independent derivation (a function's canonical text has no
second source to recompute it from), the fallback is a **banked manifest plus a declared-change
ceremony**: bank the current truth's bytes or hash, and the drift check becomes "changed without
declaring" — [gates/validation_leaf_manifest_gate.py](../gates/validation_leaf_manifest_gate.py)
(banked function text, `--declare-change`) and [tools/role_charter.py](../tools/role_charter.py)
(ledger-registered charter sha256, a loud `DRIFT` warning when on-disk bytes diverge) are the
two built instances of that variant.

**Which backstops already exist that I can crib from?** Each of these was verified in the corpus
for this entry (file named; read its docstring for the full truth — the per-instance docstring
is each one's owning page):

- [gates/idris_model_freshness.py](../gates/idris_model_freshness.py) — the categorical kernel
  model's declared `AS-OF` head vs the actual lineage head, both derived from
  `kernel/lineage/*.sql` filenames; its teach-text names both discharge paths (refresh, or an
  honest lag note).
- [gates/hash_coverage_gate.py](../gates/hash_coverage_gate.py) — `compute_row_hash`'s
  serialized-column enumeration vs the ledger's live column set on a scratch apply. The
  witnessed drift it closes is this page's best cautionary specimen: thirteen deltas each added
  columns, none re-issued the hash function, and twenty-two columns sat outside the
  tamper-evidence chain (ledger row 1449) until caught by eye.
- [gates/link_integrity.py](../gates/link_integrity.py) — every relative markdown link target
  vs the file tree (files move; links dangle).
- [gates/layout_census.py](../gates/layout_census.py) — [provenance/LAYOUT.md](../provenance/LAYOUT.md)'s
  designed tree vs the tracked tree ("ls-legibility asserted once and never re-checked would
  rot exactly as the old repos did" — its own motivating line).
- [gates/fixture_census.py](../gates/fixture_census.py) — `seen-red/` evidence dirs vs the
  fixture registry vs what git actually tracks, both directions.
- [gates/apparatus_unknown_keys.py](../gates/apparatus_unknown_keys.py) — `apparatus.json` keys
  vs the mechanism set derived from `hooks/`, `bootstrap/templates/`, and `tools/` source.
- [gates/column_complete_gate.py](../gates/column_complete_gate.py) — each registered view's
  live columns vs its source table's, minus declared exclusions.
- [gates/kind_shape_manifest_gate.py](../gates/kind_shape_manifest_gate.py) — the
  (kind, column, arity) manifest vs the live kernel catalog's actual constraints.
- [gates/ledger_reader_allowlist.py](../gates/ledger_reader_allowlist.py) — every view/function
  that reads the ledger vs the closed allowlist of declared reader types.
- [gates/validation_leaf_manifest_gate.py](../gates/validation_leaf_manifest_gate.py) and
  [tools/role_charter.py](../tools/role_charter.py) — the banked-manifest variant, described
  above.
- [gates/cut_probe_inventory.py](../gates/cut_probe_inventory.py) — a release-candidate tree vs
  the registry of shipped fix classes: drift backwards (a silent revert) caught at cut time.
- [gates/doc_attestation_presence.py](../gates/doc_attestation_presence.py) (and its
  per-deployment sibling `attest-doc`, whose witnessed `STALE` verdict appears in
  [the "Verifying tags, signed commissions, and documentation debt" section below](#verifying-tags-signed-commissions-and-documentation-debt-attest-tags-verify-commission-attest-doc-distance-to-clean))
  — a doc's current bytes vs the content hash its last fresh-context read attested.
- [./migrate](../migrate) `--dry-run` ([bootstrap/migrate_core.py](../bootstrap/migrate_core.py)) —
  a deployment's live schema vs the kernel lineage chain, one `.detect.sql` probe per delta,
  reporting exactly which deltas the world lacks.

- [seen-red/setup-tui-scripted-smoke](../seen-red/setup-tui-scripted-smoke/run_fixtures.py) —
  the setup surface's own backstop, commissioned under the maintainer's 2026-07-19 standing
  rule ("the setup surface itself ... will drift unless maintained", ledger row 1700: `./led
  show 1700` at the repository root): a scripted TUI smoke fixture, census-registered, driving
  `python3 -m tools.setup_tui.app --scripted ... --start-at <screen>` against real hostile/
  malformed inputs and asserting the same REFUSED-no-traceback outcome the mechanism itself is
  supposed to produce, plus (added for the feature-facts column, ledger row 1714) asserting the
  facts lines documented just below actually render at preflight/substrate/boundary/
  observability/hydration screen entry.
- [seen-red/setup-tui-feature-facts-drift](../seen-red/setup-tui-feature-facts-drift/run_fixtures.py)
  — `tools/setup_tui/feature_facts.py`'s own registry vs. the live preflight-binary/substrate-
  choice/hydration-catalog set `screens.py` and `durable_decisions.py` actually expose,
  compared both directions (the class this whole section describes, applied to the feature-
  facts column itself — this spec's own first deliberate consumer of the method,
  design/FABLE-SETUP-TUI-FEATURE-FACTS-SPEC.md §1).
- [seen-red/setup-tui-dry-run-parity](../seen-red/setup-tui-dry-run-parity/run_fixtures.py) —
  the `--dry-run` amendment's own two real-infra witnesses (design/FABLE-SETUP-TUI-SPEC.md
  2026-07-19 amendment, ledger row 1719): WDR1 (a full dry-run flow against a real
  destination leaves the filesystem byte-identical before/after and writes zero ledger rows)
  and WDR2 (the WOULD-DO table's argv list equals a real scratch run's argv list, byte-for-
  byte, order included); needs a reachable Postgres host and the boundary service's venv,
  degrading honestly to `UNEXERCISED` (exit 0) without either, rather than failing the build
  on missing optional local infra.
- [seen-red/setup-tui-textual-shell](../seen-red/setup-tui-textual-shell/run_fixtures.py) —
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
(`python3 -m tools.setup_tui.app`, [FABLE-SETUP-TUI-SPEC.md](../design/FABLE-SETUP-TUI-SPEC.md))
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
themselves ([gates/layout_census.py](../gates/layout_census.py) checks the tree's registered
shape mechanically but declares "does this new file actually belong in this directory" a human
judgment, review-only, rather than pretending a regex can make it). Nothing sweeps for pairs
nobody declared: naming the pair is judgment, and both witnessed drift hazards above (the
22-column hash gap, the apparatus hand-list) were first caught by eye, with the class closed
after — the method forecloses recurrence, not first occurrence. A backstop is only as current
as its declared rhythm — an acceptance-time or on-demand check catches nothing between runs.
And one boundary kept deliberately, per [ADR-0008](../law/adr/0008-classification-discipline.md)'s
refuse-to-force-a-category discipline: the differential twins
([`./judge`](../GLOSSARY.md#judge)'s SQL-vs-ASP marriage, `serving/audit_served.py`'s
served-vs-kernel byte-compare) are a sibling shape — two independent LIVE derivations required
to agree now — not a stale-copy-vs-authority check, so they are named here as relatives and
excluded from the class rather than fuzzy-matched into it.

## Documentation quality

**Can my project use the fresh-context documentation review loop autoharn uses on itself?**
Yes — this was asked as "is there a reason we can't?", and the answer was no: the reviewer
is an ordinary fresh-context subagent. Scaffolded projects get `./attest-doc`
(`record`/`check`), a project-local attestations ledger, and an opt-in DOC-ATTESTATION
section in `distance-to-clean` (the scaffold's own operator-facing report that prints how far
the deployment sits from a clean governance state; apparatus switch `doc_attestation`, default
off).
Walkthrough: [USER-DOC-AUDIT-LOOP.md](USER-DOC-AUDIT-LOOP.md); the loop's rules:
[ORCH-ABC-AUDIT-LOOP-RECIPE.md](ORCH-ABC-AUDIT-LOOP-RECIPE.md).

**I have known findings to verify AND I want a fresh legibility sweep — can one reviewer do
both?**
No — and this was learned the hard way (a real, dated 2026-07-13 anchoring defect in a live
deployment, not a hypothetical). A reviewer briefed with a known findings list *and* asked to also
sweep fresh anchors on the list — the sweep silently degrades into a second verification pass. Run
two separate reviewers: a targeted verifier (front-loaded with the list — correct there) and a
genuinely blind B (artifact + commission only, no findings, no mention a correction pass
happened). The same rule governs a co-signer/countersign briefing. Full account, with the
witnessed 0-versus-4-and-7 findings gap between confirmation-mode and adversarial-fresh reviews:
[USER-DOC-AUDIT-LOOP.md](USER-DOC-AUDIT-LOOP.md)'s "Briefing your reviewer" section.

## Operating rhythm

**How do I pick up work after a break?**
Start a fresh session and run `./pickup` — never resume or continue an existing one. The brief is derived
at pickup time from live ledger state; a stored handoff decays and replayed context is
the quadratic cost the ledger exists to replace. Card:
[ORCH-OPERATING-CARD.md](ORCH-OPERATING-CARD.md).

**Can I turn a safety mechanism off, or make it observe-only? Will that be visible?**
Yes and yes — every mechanism is independently `off`/`observe`/`enforce` in
`.claude/apparatus.json`, live on the next tool call; and since 2026-07-12 every mutation
of that file is itself journaled (hashes, which modes changed), so a flip is witnessed
rather than silent. Full switchboard, per-mechanism defaults and costs:
[bootstrap/templates/APPARATUS.md](../bootstrap/templates/APPARATUS.md).

**A finished run's world turns out to have a defect. Can I patch it?**
No — runs are strictly linear; a superseded world is settled, read-only evidence. The fix
enters the next world via the scaffold (it usually already has), and the finding goes on
the ledger. This is a ruling, not a limitation looking for a workaround. Ruling text:
[../CLAUDE.md](../CLAUDE.md), ORCHESTRATION section.

## Your review queue

**Can I keep a ranked "things I need to personally look at" queue, and tick items off as I go?**
Yes — a `review:`/`review-done:` ledger row pair does this; it renders at every `./pickup`
under a `MAINTAINER-REVIEW-QUEUE` section. Unlike the `resource:`/`estimate:` grammars
elsewhere on this page, the grammar is written out here **in full**, not merely pointed at —
this recipe is its one documented home
([ADR-0005 Rule 1](../law/adr/0005-documentation-discipline.md), single source of truth per
fact), and it deviates from this page's usual "point elsewhere" convention on purpose so an
executive queue has a self-contained page to hand a first-time reader.

A queue entry is a `decision`-kind ledger row (the same kind `resource:`/`estimate:` ride, run
via `./led decision "..."`), validated at write time by
[`bootstrap/templates/led.tmpl`](../bootstrap/templates/led.tmpl) and rendered at pickup time
by the `MAINTAINER-REVIEW-QUEUE` section of
[`bootstrap/templates/pickup.tmpl`](../bootstrap/templates/pickup.tmpl) — both cite this
subsection by name rather than restating the grammar a second time
([ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md) P1).

**Opening or re-ranking an item:**

```
review: <SLUG> | <RANK> | <WHAT> | <POINTER>
```

The four fields, in order, separated by ` | ` (space-pipe-space):

- **SLUG** — a bare slug matching `^[a-z0-9][a-z0-9-]*$` (no spaces), the same shape
  `estimate:`'s TASK-SLUG field already uses. Identifies the item across its whole lifetime —
  opened, re-ranked, ticked off, and (if it recurs) re-opened.
- **RANK** — a positive integer (`1`, `2`, `3`, …), where `1` is the MOST important item —
  the queue's own sort key.
- **WHAT** — non-empty plain words: what you are reviewing, in a phrase a cold reader
  understands without opening the pointer.
- **POINTER** — non-empty: where to look. A repository path, a live-lookup command
  (`./led show 214`, run at the repository root), or a URL — whichever actually resolves for
  this item.

**Ticking an item off:**

```
review-done: <SLUG> | <DISPOSITION>
```

- **SLUG** — must match the same slug grammar `review:` uses (a `review-done:` for a
  slug-shaped-wrong SLUG is refused — there being nothing on record it could sensibly close).
- **DISPOSITION** — non-empty free text: what you decided, or what happened.

**Semantics — latest row per SLUG wins, append-only.** Nothing here is mutated or deleted; the
queue's state is *derived* from whichever row for a given SLUG has the highest ledger row id:

- The **latest `review:` row** for a SLUG is the one whose RANK/WHAT/POINTER render — so
  filing a new `review:` row with the same SLUG and a different RANK is how you re-rank an
  item (no supersedes flag needed; this is a simpler rule than `resource:`'s, deliberately,
  because a queue's whole point is a fast one-liner).
- A **`review-done:` row for a SLUG removes it** from the rendered queue — it is still on the
  ledger (append-only, nothing is ever deleted), just no longer printed as open.
- A **`review:` row filed AFTER a `review-done:` for the same SLUG re-opens it** — the same
  latest-row-wins rule applied uniformly, so reopening needs no special-cased verb.

Copy-paste examples:

```sh
./led decision "review: key-generation | 1 | decide the signing-key generation ceremony | design/MAINT-MAINTAINER-DECISION-BRIEF.md"
./led decision "review-done: key-generation | approved the brief's proposed ceremony as written"
```

`./pickup`'s `MAINTAINER-REVIEW-QUEUE` section prints every open entry rank-ascending, each with
the exact `./led decision "review-done: <slug> | <disposition>"` one-liner to tick it —
copy-paste, no grammar to recall. An empty queue prints a short, explicit line, never silence
(the same never-silent convention `resources()`/`estimates()` already keep). A malformed
`review:`/`review-done:` row is refused loudly at write time (see `led.tmpl`'s own teach-text);
nothing here is a gate on WHAT you decide, only on the shape of the row that records it.

## Correcting the record — supersession, and what to do about its fallout

**I encoded a row wrong (wrong flag, missing refs, bad wording) — how do I fix it?**
Supersede it: write the corrected row with `--supersedes <old-row-id>` (for work items,
`led work open <new-slug> ... --supersedes <old-open-row-id>`). The ledger is append-only,
so a correction is always a new, linked row — the old one leaves current truth but stays
in history, never obscured. This is the default answer to every "I wrote it wrong"
situation; nothing is ever edited in place, and raw SQL against the ledger is never the
answer to a missing verb. Honest limit: superseding a work item's OPEN row permanently
burns its slug (a deliberate, ratified choice) — the replacement needs a new slug, and
surviving claims/edges that named the old slug must be re-issued. Grammar:
`./led work open` usage; semantics:
[FABLE-SUPERSESSION-UNIFORM-RETRACTION-SPEC.md](../design/FABLE-SUPERSESSION-UNIFORM-RETRACTION-SPEC.md).

**I recorded a `work_depends_on` edge wrong (wrong `--type`, wrong endpoints) — how do I fix
it?** Same primitive, one kind over: `./led work depends <slug> <on-slug> [--type
blocks-close|blocks-start|informs] --supersedes <old-edge-row-id>`. This writes a NEW
work_depends_on row that both carries the corrected edge (a different `--type`, or different
`<slug>`/`<on-slug>` endpoints — re-pointing a mistaken edge entirely is legal) and retracts
the old row from current truth in the same act (`ledger.supersedes`, s31 — uniform across
every kind, reinstatement-free). Reach for this specifically when: the edge was typed wrong
(e.g. recorded `informs` when it should have been `blocks-close`, or vice versa); the edge
pointed at the wrong antecedent or dependent slug; or the mixed-deadlock case that s39's
claim-time refusal teach-text and its LIMITS section both name explicitly: a `blocks-close`
edge and a `blocks-start` edge between the
SAME two items in OPPOSITE directions produced a genuine mutual claim/close deadlock (neither
edge type's own construction-time cycle check catches this, because each is scoped to its own
edge type only): supersede ONE of the two edges to break the deadlock. Refused at construction
if `<old-edge-row-id>` does not exist, is not itself a `work_depends_on` row (a different kind
is corrected via its OWN verb's `--supersedes`, e.g. `led work open --supersedes` for a
`work_opened` row, `led work resolve-violation --supersedes` for a disposition row — one
column, three typed entry points, never a raw-SQL fourth), or is already superseded (the row
that superseded it is named, so you can inspect or correct THAT one instead). Re-issuing the
exact same edge shape that a supersession just retired is NOT refused as a duplicate — there
is no uniqueness check on `work_depends_on` rows at all (unlike `work_opened`'s permanent
slug-burn). When the new edge's slug or type differs from the old one, the CLI prints an
advisory naming both the old and new endpoints, so the correction stays legible without
digging through raw history. History stays: the superseded edge remains visible in
`work_violation_history`/raw ledger reads; current truth (`work_edge_blocks_close`,
`work_edge_blocks_start`, `work_item_blocks_start_blockers`, and the claim-time/strict-close
refusals that read them) moves on to the new edge only. Grammar: `./led work depends` usage;
kernel semantics: kernel/lineage/s39-blocks-start.sql (blocks-start),
kernel/lineage/s30-typed-dependency-edges.sql (blocks-close),
[FABLE-SUPERSESSION-UNIFORM-RETRACTION-SPEC.md](../design/FABLE-SUPERSESSION-UNIFORM-RETRACTION-SPEC.md)
(the shared supersession mechanics).

**I superseded a parent item and `work violations` now shows orphan rows that nothing can
clear — did I break the world?**
No, and this exact situation happened in a real deployment (a composite parent superseded
while five children — three already closed — still hung under it; every child's parent-edge
became an `orphaned_by_retraction` violation with no discharge path, permanent blocking
debt). Nothing was lost: the children's own rows, closes, and reviews are all intact; the
violations are the record correctly describing dangling linkage. The gap was ours — a
violation an operator can legally cause must have an answering act, and orphans had none.
The fix is the s37 violation-disposition mechanism
([FABLE-ORPHAN-DISPOSITION-SPEC.md](../design/FABLE-ORPHAN-DISPOSITION-SPEC.md)):
`led work resolve-violation <violating-act-id> <reissued|retired> "<basis>"` answers any
in-force violation with a reviewed, attributable row, and `led work supersede-cascade` handles the
live-descendants ripple in one witnessed pass. Until your world has s37: take no further
supersession, let the stop-gate (`hooks/stop_clean_exit.py`, the Stop hook that blocks a
session from ending while governance debt is open) handle stops via its loud fail-open
(that valve exists for exactly this — structurally unclosable debt), and migrate when the
delta reaches you.
**When do I reach for `resolve-violation`, and when for `supersede-cascade`?**
They are not alternatives at the same level: `resolve-violation` is the primitive and
`supersede-cascade` is a convenience built entirely out of it — nothing the cascade does
is impossible by hand, and the cascade writes no special rows. Reach for
`resolve-violation` when violations ALREADY EXIST (you are cleaning up after a
supersession, yours or an inherited one), and always for a superseded parent's
closed/settled children — their edges get `retired` dispositions and the children
themselves are never touched. Reach for `supersede-cascade` when you are ABOUT TO
supersede an item that still has live (open) descendants: it performs the whole ripple —
re-open each live child under a new slug citing its predecessor, re-issue claims and
edges, write each resulting orphan's `reissued` disposition — in one witnessed pass, in
dependency order. The order is the point: done by hand, each step of the ripple mints new
orphans one level down (by design — the mechanism is closed under that recursion), and a
mis-ordered hand-walk leaves you resolving violations you created two steps earlier.
Honest limit: the cascade only handles the subtree below the item you name; edges INTO
the subtree from elsewhere still surface as orphans afterward and are yours to
`resolve-violation` individually, because no tool can know whether an outside edge should
follow the successor or die with the predecessor.

**Why is the fix a disposition act, not "supersede the whole subtree"?**
A subtree is not closed under reference, and a settled review cannot be honestly
re-issued (a new review row in the reviewer's name would forge their agency) — the full
reasoning, with the witnessed evidence, is the ADR-0014 consultation record at
[ORCH-ADR14-ORPHAN-DISPOSITION-CONSULT-2026-07-16.md](../vestigial_documentation/design/ORCH-ADR14-ORPHAN-DISPOSITION-CONSULT-2026-07-16.md).

**Why does the harness insist closed and reviewed items stay correctable at all?**
Because the record model this project imports requires it, independent of anyone's
preference: [the safety-critical-logging BRIEF](../law/briefs/safety-critical-logging/BRIEF.md)'s
invariant I3 (a correction is a new, linked entry that never obscures the prior state),
I7 (every discharged obligation carries the conditions under which it ceases to hold),
and the nuclear/aviation clusters' change-through-re-verification linkage (IEC 60880,
DO-178C) all demand that a close — and the reviews that discharged it — can be superseded
or lapse when their basis is defeated, append-only, with the defeat linked. The kernel
already delivers the core of this (superseding a close re-opens the item and re-surfaces
its review debt, witnessed in the consult above); s37's validity-bounded dispositions
extend the same discipline to violation answers themselves.

## The ledger boundary service (`serving/`)

**Can I get an HTTP API onto a ledger instead of shelling out to `led`?**
Yes — `serving/boundary_service.py` is a FastAPI service that is the one declared **Port**
([ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md) P2) into an autoharn-managed ledger for UI-class and programmatic consumers, the
autoharn-panel Vue SPA first. Full spec:
[FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md](../design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md) (read it in full,
including its amendments, before touching the directory); operator pointer:
[serving/README.md](../serving/README.md). The service adds **no truth of its own** — it
translates and validates transport-level shape only, refuses what it cannot honor, and never
coerces. The kernel's own **inner** boundary (the [write boundary](../GLOSSARY.md#write-boundary)
s43's four `SECURITY DEFINER` functions, plus the derived views) stays the sole authority.

**UPDATED 2026-07-18 — the repo-root operator verbs are no longer a separate, un-served
surface.** The paragraph above once said `led`/`judge`/`pickup` were "explicitly NOT
deprecated by this — routing them through the service is a reserved v2 question." That v2
question is now answered and built: `led`, `pickup`, `asof-export`, and `distance-to-clean`
became thin HTTP clients of this service (the "boundary multiplex and CLI rebase, and the
workflow-unit compiler" section below has the full story, including the two new
`deployment.json` keys this rebase needs and what happens when they're missing). `judge` and
`audit` do **not** rebase — they drive `clingo` plus a differential against the world directly,
"not a ledger client in the boundary's sense" (the rebase spec's own words) — and neither does
the scaffolding itself.

**How do I launch it, and what does it actually say?** The service used to take a single
`--deployment deployment.json` file; **as of the 2026-07-18 multiplex build it takes
`--config <path-to-boundary-multiplex.toml>` instead** and can serve more than one deployment
from one process (see "How do I serve more than one project from one boundary?" below for the
config shape and the `/d/{deployment}` routing this changes). The single-file `--deployment`
launch form below is UNWITNESSED against the current build — retained here as history of what
this section originally verified, not as a current invocation to copy:
```
$HOME/w/vdc/venvs/generic/bin/python -m serving.boundary_service --deployment deployment.json --port 18421
```
(the example above ran on port 18421 rather than the default 8420 because another project's dev
server already held 8420 on this host — an ordinary `--port` override, not part of the feature).
WITNESSED, `GET /health` against this repo's own `autoharn1` world:
```
{"world":"autoharn1","service_principal":null,"capabilities":{"s22_work":true,"s41_identity":false,"s43_boundary":false,"credited_view":false}}
```
That capability manifest is not a fixed feature list — it is DETECTED per request against the
connected world's actual schema (object existence, never a version literal), which is why
`autoharn1` — a world older than s40/s41/s43 — shows three of the four capabilities absent
while still serving [`s22`](../kernel/lineage/s22-work-item-ledger.sql) (the kernel-lineage
delta that adds the per-project work-item ledger) work items fine.

**What do the read endpoints look like, and what happens when a world lacks a capability
a read endpoint needs?**
`GET /rows/current` serves `ledger_current` (id-paginated, `?after_id=&limit=`, `1 ≤ limit ≤
1000`, `after_id ≥ 0`); `GET /rows/{id}` and `GET /rows/{id}/history` serve one row and its
supersession chain. `GET /credited`, `GET /standing/principals`, and `GET /work/items` are
**capability-gated** — on a world that lacks the underlying view, the endpoint refuses with a
typed `capability_absent` response rather than silently falling back to a weaker read (that
fallback is exactly the vacuous-pass class this project's [F49 finding](../FINDINGS.md) named:
a close instrument that silently no-ops instead of visibly refusing when its assumed
environment isn't met, so the missing check reads as a pass). WITNESSED, all
three gates against `autoharn1` (which lacks s41 identity and the s44 credited view, but carries
s22 work):
```
GET /credited            -> HTTP 409 {"disposition":"capability_absent","capability":"s44-credited-view", ...}
GET /standing/principals -> HTTP 409 {"disposition":"capability_absent","capability":"s40-identity", ...}
GET /work/items          -> 200, real work_item_current rows
```

**What does a write look like, and what happens to a refused one?**
Four endpoints, one per s43 [write boundary](../GLOSSARY.md#write-boundary) function:
`POST /write/ledger`, `/write/review`, `/write/registration`, `/write/obligation`. **A kernel
refusal is HTTP 200** carrying the kernel's own [typed verdict](../GLOSSARY.md#typed-verdict)
verbatim (`disposition: "refused"`, `refusal_id`, `sqlstate`, kernel-authored teach-text) — a
refusal is a first-class domain result, not a transport error. Transport-level failures
(malformed JSON, an oversized body) are typed and loud instead: a body over 1 MiB is HTTP 413
with `{"disposition":"payload_too_large", ...}`, checked before JSON parsing and again before
the value reaches the database. **On a world that predates s43, every write endpoint refuses
entirely** rather than falling back to a raw `INSERT` — there is no code path in the service
that writes SQL DML. WITNESSED against `autoharn1` (pre-s43):
```
POST /write/ledger -> HTTP 409 {"disposition":"capability_absent","capability":"s43-boundary",
  "message":"This world carries no s43 write boundary ... refuses entirely rather than
  falling back to a raw INSERT ..."}
```
The 413 oversized-body and malformed-JSON write-path checks are **UNWITNESSED here** — on
`autoharn1` the s43 capability gate short-circuits before those checks run at all, since the
world has no write boundary to reach; they would need an s43-carrying world to observe.

**Does it bind to the network, or only to this machine?**
Loopback only by default (`127.0.0.1:8420`); any other host is refused at startup unless you
pass `--i-understand-this-exposes-the-ledger` — the ledger carries operator-real content.
WITNESSED:
```
$ python -m serving.boundary_service --deployment deployment.json --host 0.0.0.0 --port 18422
boundary_service: REFUSED -- --host '0.0.0.0' is not a loopback address ... refused unless
you pass --i-understand-this-exposes-the-ledger explicitly ...
```

**Is there a way to check the service is actually telling the truth about what the kernel
holds?** Yes — `serving/audit_served.py` fetches a served page over HTTP, reads the same view
directly with a read-only `psql`, and byte-compares the row sets; it ships WITH the service —
sentry-class treatment, this page's term for a built-in independent verifier shipped alongside
the primary tool rather than bolted on afterward, the same posture the OTel watchdog/sentry
mechanism in "Model identity: watchdog, attestation, defeat" above uses for a different
surface — not as an afterthought. WITNESSED:
```
$ python serving/audit_served.py --base-url http://127.0.0.1:18421 --deployment deployment.json
audit_served: AGREE -- /rows/current matches autoharn1.ledger_current byte-for-byte over the
compared page.
```

**What about the panel's existing direct-psql access — does this retire it?**
That is the deprecation duty the spec's §6 names: every legacy direct-psql consumer path (the
autoharn-panel's own FastAPI-side SQL, concretely) gets a mark that is loud at every invocation,
names the replacement endpoint, and points at the world-context migration consult — but stays
functional (backwards compatibility is the commission's own carve-out; nothing is silently
tolerated, nothing is silently broken). That marking is panel-repo work, out of scope for this
autoharn checkout and UNEXERCISED from here — the spec is explicit that the panel-side session
runs it, citing this spec, never a session running against a live panel checkout from here.

## Boundary multiplex, CLI rebase, and the workflow-unit compiler (2026-07-18)

The four recipes below cover the same day's landed work: the operator verbs `led`/`pickup`/
`asof-export`/`distance-to-clean` became HTTP clients of the boundary service above rather than
direct `psql` callers, the service itself learned to serve more than one deployment from one
process, and a new compiler turns a fixed-shape workflow TOML into something the kernel actually
drives. Specs: [FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md](../design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md)
(ratified, ledger row 1631), [FABLE-BOUNDARY-READ-SURFACE-SPEC.md](../design/FABLE-BOUNDARY-READ-SURFACE-SPEC.md)
(ratified, ledger row 1652 — the amendment that grew the route table from eleven to fourteen so
the CLI rebase had a read surface to land on), and
[FABLE-WORKFLOW-UNIT-COMPILER-SPEC.md](../design/FABLE-WORKFLOW-UNIT-COMPILER-SPEC.md) (commission
ledger row 1658, ratified rows 1659/1660). Operator pointer for the served side:
[serving/README.md](../serving/README.md).

**My `./led` says the boundary is unreachable, or that `deployment.json` is missing keys — what
do I do?**
As of this rebase, `./led`/`./pickup`/`./asof-export`/`./distance-to-clean` are thin HTTP clients
of the boundary service, not direct `psql` callers — and every rebased shim needs two new
**optional** `deployment.json` keys to find that service: `boundary_url` (the served boundary's
own base URL, no trailing slash, no `/d/{deployment}` segment) and `boundary_deployment` (the
`/d/{name}` path segment this project answers under on the served side — deliberately a
*different* field from `deployment.json`'s pre-existing `name`, so the two don't collide on one
meaning). Read `serving/boundary_cli_client.py`'s own module docstring for the exact shape. Three
distinct failure shapes, and they carry three distinct exit codes so you never mistake one for
another:
- **Exit 4 — boundary unreachable / `deployment.json` missing the two keys.** WITNESSED against a
  fresh `bootstrap/track-work.sh` deployment (a standing work tracker, which runs no boundary
  service of its own by design, so it never gets these keys):
  ```
  $ ./led --recent 3
  led: deployment record at .../deployment.json is missing required-for-the-served-shim
  field(s): boundary_url, boundary_deployment (... refused-if-absent, never guessed. Add both
  keys to .../deployment.json, or run the ./legacy/ original instead.
  ```
  (exit 4). The same exit code covers a genuinely unreachable service (both keys present, but
  nothing is listening at `boundary_url`) — `boundary_cli_client.py`'s own convention: "this shim
  never had a response to classify."
- **Exit 3 — the boundary itself refused** (a typed HTTP 4xx/408/413/422/429/503/409 shape FROM
  the service — `payload_too_large`, `server_saturated`, `deployment_saturated`,
  `unknown_deployment`, `unknown_view`, `capability_absent`, and the like). There was no kernel
  `write_verdict` at all for this call — a boundary-level refusal is never dressed as a kernel
  one.
- **Exit 1 — the kernel itself refused** (a genuine s43 `write_verdict` with
  `disposition: "refused"`) — byte-identical to what the direct-`psql` `led` always exited for
  exactly this case. Exit 0 is the kernel-accepted case, likewise byte-identical to the legacy
  exit.

**`./legacy/` was the recovery path for `pickup`/`asof-export`/`distance-to-clean` — `led` is the
one exception now.** legacy-led-retirement (design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md, ledger
row 1149/1150) DELETED `bootstrap/templates/legacy-led.tmpl` outright, once the served path grew
full coverage (below) — `./legacy/led` is now a one-line teaching refusal, never a working CLI.
`./legacy/pickup`/`./legacy/asof-export`/`./legacy/distance-to-clean` are unaffected: demoted by
placement, still executable, unchanged in capability, written automatically by
`bootstrap/new-project.sh --new-world`.

**A genuine, still-OPEN hazard this retirement found in reach but did not unilaterally fix:**
`bootstrap/track-work.sh` (the *other* scaffold — see
[USER-GUIDE.md §3a](USER-GUIDE.md#3a-just-track-your-work-bootstracktrack-worksh)) deliberately
writes NO `boundary_url`/`boundary_deployment` at all ("a standing work tracker runs no boundary
service by design") — its own `./legacy/led` used to be the ONE working `led` such a deployment
had. With `legacy-led.tmpl` deleted, a `track-work.sh`-scaffolded deployment has NO working `led`
verb at all right now: `./led` refuses (no boundary, by design) and `./legacy/led` is the retired
stub. Giving `track-work.sh` its own standing boundary service is a real architecture question
outside this retirement's own mandate (the setup_tui/screen_boundary flow) — named and flagged,
not silently patched. Use `./pickup` (read) and direct `psql` (write) for such a deployment's
ledger until a maintainer decision resolves this.

**How do I serve more than one project from one boundary?**
`serving/boundary_service.py` used to take `--deployment deployment.json` (one process per
deployment); it now takes `--config <path-to-boundary-multiplex.toml>` and serves every
deployment the TOML names from one process — "I don't want to have to start one FastAPI server
for every deployment," the maintainer's own framing for the commission. Shape
(`serving/boundary_multiplex_config.py`'s own module docstring has the authoritative version;
note it needs two more `pg`-prefixed keys than the design spec's own illustrative example, named
there as a flagged, smallest-honest-choice addition):
```toml
[deployments.autoharn1]
pghost = "192.168.122.1"
pgdatabase = "autoharn1"
pguser = "led_writer"
pgschema = "autoharn1"
pgkern = "autoharn1_kernel"

[deployments.omega]
pghost = "192.168.122.1"
pgdatabase = "omega"
pguser = "led_writer"
pgschema = "omega"
pgkern = "omega_kernel"
```
The WHOLE file validates before the socket binds — an unknown key, a missing required key, or
zero deployments all refuse startup by name; per-deployment reachability is *not* probed at
startup (a deployment whose database is down is a per-request typed 503, exactly as before).
Every route in the endpoint table gains a mandatory leading `/d/{deployment}` segment —
`GET /rows/current` is actually `GET /d/{deployment}/rows/current` — and `{deployment}` is valid
iff it's a key of the loaded config; anything else is a typed 404 `unknown_deployment` naming the
known set. This holds even for a config with exactly one deployment (the mandatory discriminator
is one route shape, not two dialects — [serving/README.md](../serving/README.md)'s own
"Multiplexing" section has the admission-bound details: `MAX_INFLIGHT_KERNEL_CALLS` stays the
global bound, and a new per-deployment sub-bound stops one stalled deployment from starving its
siblings). UNWITNESSED in this pass — launching a live two-deployment multiplexed server was out
of scope for a documentation-only session; `seen-red/boundary-multiplex/run_fixtures.py` — its own
four numbered witness cases WM1 through WM4, covering cross-deployment write isolation, the
unknown-deployment refusal, malformed-config refusal, and per-deployment admission saturation
respectively (the multiplex spec's own §7 names each in full) — is the project's own live witness
suite for this mechanism, cited rather than re-run here.

**Which `led` subcommands go over the boundary?** As of legacy-led-retirement (ledger row
1149/1150), ALL of them — read `bootstrap/templates/led.tmpl`'s own module docstring (its "SCOPE,
HONESTLY NAMED" section) for the authoritative, self-updating coverage table. In brief: `led
--recent`/`current`/`show`; every read view (`question-status`/`review-gap`/`stamp-distinctness`/
`standing`); `led --json`; the generic write path with its full flag set and statement-grammar
pre-flight (all eight prefixes); `register-principal`; `obligate` and `obligate revoke` (a typed
kernel event now, kernel/lineage/s57-obligation-revocation-event.sql — the raw `DELETE` this used
to be is retired); `review`; `decomposition-review-status`; `briefing`; the entire `led work *`
family, all eleven sub-verbs; `led artifact put|get|stat`; and `led principal *`, all thirteen
sub-verbs (`declare-standing`/`undeclare-standing`/`suspend`/`lift-suspension`/`revoke`/`relate`/
`unrelate`/`bind-role`/`release-role`/`bind-key`/`revoke-key`/`grant-competence`/
`withdraw-competence`) — the one family this inventory pass's own mechanical dispatch-diff found
still missing, now closed. `./legacy/led` served none of this specially — it is deleted outright,
a one-line teaching refusal in its place. The two disclosed read-shape divergences named
throughout `led.tmpl`'s own SCOPE section (JSON-per-line listing for `led work list`; the
supersession-aware `led work asof`) are the only remaining behavior differences from the
(now-historical) direct-psql original.

**How do I turn a fixed-shape workflow TOML into something that actually runs?**
`tools/workflow_compile.py` reads one `design/workflows/*.toml` (the pipeline-dsl-v0 grammar —
`[[phases]]` with `name`/`depends_on`, `[roles.<phase>]` with `authors`/`implements`/`reviews`
prose) and emits two artifacts: a **hydration script** (`hydrate.sh` — one `led work open` per
phase, one `led work depends ... blocks-start` per `depends_on` edge, and an obligation act where
a phase's `reviews` clause reads as an independent countersign) and a **driver script**
(`drive.py` — claims each phase, prints its brief for the caller's own agent dispatch, then
closes it). Usage: `python3 tools/workflow_compile.py <path-to.toml> [--out-dir DIR]`, then
`bash <out-dir>/<stem>/hydrate.sh --instance <token> [--yes]` and
`python3 <out-dir>/<stem>/drive.py --instance <token>` — the `--instance` token is **mandatory**
on both (a TOML is a reusable shape; an instance is one engagement of it — slugs are
`<stem>-<instance>-<phase>`, so two different tokens are two independently claimable waves of the
same TOML, and re-hydrating the SAME instance is idempotent by refusal: an already-open slug
refuses loudly and the script treats that as "already hydrated," never as an error).

**The one design commitment that makes this safe to trust: the compiler adds no enforcement
machinery of its own.** Every blocking mechanism the driver obeys is a kernel fact it discovers by
*attempting the act and reading the kernel's own refusal* — never precomputed. A dependency
blocker is the s39 `blocks-start` claim-time refusal; an obligation blocker is countersign debt
visible in `review_gap`; a role constraint is whatever the claiming principal's own standing
permits. WITNESSED, both polarities, compiled from `design/workflows/faq-abc-fixpoint-loop.toml`
and hydrated/driven against a scratch `--new-world` scaffold (`faqwit0718wc` on the toy database,
torn down with zero residue afterward) — claiming a dependent phase before its antecedent closed
(HISTORICAL transcript, captured via `./legacy/led` back when `led work *` ran through it; the
generated driver's own default now runs the served `./led` instead, per legacy-led-retirement,
ledger row 1149/1150 — the kernel-refusal TEXT below is unchanged either way, it is the SAME s43
`write_verdict`):
```
$ ./legacy/led work claim faq-abc-fixpoint-loop-demo2-fresh-context-review
led: REFUSED by the kernel write boundary (SQLSTATE P0001; journaled as write_refused row 24 ...):
  Ledger policy: claim of work item '...fresh-context-review' refused — its blocks-start
  antecedent(s) are not yet resolved: ...author-draft (item is not yet closed). Claim and finish
  each named antecedent first ...
```
and the identical claim accepted once the antecedent was genuinely closed:
```
$ ./legacy/led work claim faq-abc-fixpoint-loop-demo2-fresh-context-review
led: row 31 written.
```
**Suspension halts a wave; lifting it resumes the wave — this is the same kernel-refusal-is-the-
gate posture, not a special case the driver codes for.** Suspend the claiming principal (the s45
standing act) mid-wave and the driver's next claim/write on that principal's behalf is refused by
the kernel with its own teach-text, never simulated by the driver; lift the suspension and the
same act is accepted. The compiler spec names a standing rule for this witness (its own "WC7,"
the seventh named witness case in
[FABLE-WORKFLOW-UNIT-COMPILER-SPEC.md](../design/FABLE-WORKFLOW-UNIT-COMPILER-SPEC.md)): if any
kernel act the driver relies on turns out NOT to gate on the actor's standing, that must be
reported loudly as a candidate kernel-lineage gap for the maintainer to rule on, never patched
over by having the driver simulate the halt itself. This project's own build witness (ledger row
1661) ran WC7 both polarities and reported **no such gap** — every write gates on the actor's
standing universally, so there was nothing for the driver to route around even by accident.
UNWITNESSED in *this* documentation pass (re-running WC7 was out of scope here) — cited from the
build's own witness record rather than re-driven.

**Named seams, honestly, if you're deciding whether to lean on this compiler for something load-
bearing:** the driver's own phase-count tally undercounts cosmetically (a display bug, not a
correctness one — the kernel's own claim/close verdicts are still what gates everything); the
compiler's own **J2** heuristic (named for its position in `tools/workflow_compile.py`'s own
"JUDGMENT CALLS THIS TOOL MAKES" list — J1 is the principal-identity default, J2 the one named
here, J3/J4 cover obligation-act deduplication and close-disposition defaults) that decides "does
this phase's `reviews` clause want an independent obligation act" is fit to the vocabulary of the
four workflow specimens on file today, not a formal grammar — a future
specimen it misjudges is a real gap to bring back to the compiler spec, not a silent miss. (The
driver used to route every `led work` call through `./legacy/led`, back when the served boundary
did not yet cover `led work *` — that gap closed at legacy-led-retirement phase 1/1B, and
`hydrate.sh`'s own generated default now runs the served `./led` instead, ledger row 1149/1150;
`drive.py`'s own default is unchanged for a separate, still-open reason — see that generator's own
comment, `tools/workflow_compile.py`.)

## Role charters and briefs (`tools/role_charter.py`, `tools/role_brief.py`)

**What are a "charter" and a "brief," and when do I use them?** They are the assembly wiring
for durable roles — the CLI-side half of the s40/s41 identity model above, commissioned to
close the gap between "a principal is registered" and "an instance dispatched under that
role actually knows what it is and what it faces." Full spec:
[FABLE-ROLE-CHARTERS-AND-BRIEFS-SPEC.md](../design/FABLE-ROLE-CHARTERS-AND-BRIEFS-SPEC.md)
(commission ledger row 1663; built commit `822c2cc`). Two halves, named once:
- **Charter** — the static half: what a role IS. A per-role markdown file (typically
  `roles/<role>/CHARTER.md` in a scaffolded world — `bootstrap/new-project.sh` ships an
  empty `roles/` plus a README stating the register-before-binding rule). It binds only
  when REGISTERED: a `decision` ledger row naming the role's principal, the file's
  repo-relative path, and its sha256 (computed from the on-disk bytes by the tool itself,
  never caller-supplied — ADR-0002's class of bug foreclosed by construction). A drifting
  loose file with no registration row is UNREGISTERED, and the tooling says so rather than
  guessing.
- **Brief** — the derived half: what a role FACES right now. Never authored, always
  computed at instantiation time, scoped to the role's principal: its in-force decisions,
  its obligation debt (`review_gap`/`work_review_gap`), open questions in its concerns, its
  claimable work, and its standing (an s45 suspension is surfaced LOUDLY at the top — an
  instance must learn it is suspended from its own brief, not from its first refusal).

**When would I actually reach for these, as opposed to just talking to an agent?** When you
want a role's context to be a derived, auditable fact rather than whatever prose happened to
be pasted into a prompt — most concretely, the workflow-unit compiler's dispatch step
(["Boundary multiplex ... workflow-unit compiler" above](#boundary-multiplex-cli-rebase-and-the-workflow-unit-compiler-2026-07-18))
hands a driven phase's agent `charter + brief` for its role via `--role-map <toml-role>=<
principal>`, refusing (with teaching) a mapping to an uncharted principal unless
`--allow-uncharted` is passed explicitly (a loud escape hatch, not a silent default). Outside
the compiler, register a charter for any durable role the moment its responsibilities stop
fitting in a sentence you're willing to retype every session.

**Commands, no raw SQL anywhere — `led` is the only write surface.** WITNESSED this session
(`--help`, byte-for-byte):
```
$ python3 tools/role_charter.py
usage: python3 tools/role_charter.py register <role> <path> [--led PATH] [--scan-limit N]
       python3 tools/role_charter.py show <role>           [--led PATH] [--scan-limit N]
       python3 tools/role_charter.py amend <role> <path>   [--led PATH] [--scan-limit N]
$ python3 tools/role_brief.py
usage: python3 tools/role_brief.py brief <role> [--led PATH] [--scan-limit N]
```
`register` writes the fixed-shape row (`role-charter registered: role=<role>
path=<repo-relative-path> sha256=<64-hex-digest>`) via `led decision`; `show` reports the
in-force registration and whether the file's current bytes still match the registered
hash — a mismatch is a loud `DRIFT` warning, not a silent pass-through; `amend` writes a new
row with `--supersedes <old-row-id>` (the ledger's own s31 uniform-retraction mechanism —
the old registration drops out of `ledger_current` exactly like any other superseded row).
`role_brief.py brief <role>` prints one clearly-headed section per source, each section
naming its own provenance (which view, which filter); work-family sections go via `--led`
exactly as the compiler does, so the served-boundary gap on those views (named elsewhere on
this page) stays visible rather than papered over.

**Honest limits, and what an operator will actually see with no charter registered yet.**
WITNESSED this session, against a real scaffolded world with no registered charter for
`author`:
```
$ python3 tools/role_charter.py show author
role_charter: REFUSED -- role 'author' has no registered charter (scanned the last 100000
  ledger_current rows; see this tool's own JC1 note if the real registration is older than
  that). Register one:
  python3 tools/role_charter.py register author <path>
```
and `role_brief.py brief <role>` needs the work-family views' `work_startable` (kernel s39)
present in the target world's schema; a pre-s39 world refuses legibly rather than printing a
partial or wrong brief — WITNESSED against a world one delta short:
```
$ python3 tools/role_brief.py brief author --led ./led
role_brief: REFUSED -- './led work startable' failed:
led work startable: REFUSED -- requires kernel/lineage/s39-blocks-start.sql applied
  to this project's schema (work_startable view not found ...)
```
A charter registration row is a convention over ordinary `decision` rows, not a minted
kernel kind (the spec's own "Honest limits" section, by design — the ADR-0011 conversion to
a typed kind is deferred until the convention is witnessed recurring); a malformed
hand-written registration is caught by `show`'s hash check, not refused at write time. Role
proliferation stays the operator's own judgment — the tool grants nothing; authority remains
entirely the kernel's standing/binding facts. Full witness record (WB1–WB6, both polarities,
scratch world, zero residue) is in the build commit (`822c2cc`)'s own message, covering
register/show/DRIFT/amend, empty-vs-populated brief sections against their direct view
queries, an obligation appearing then discharging in the next brief, percolation across two
roles, compiler wiring with the uncharted-refusal and `--allow-uncharted` legs, and an s45
suspension surfaced then lifted.

## CLI quality-of-life: row-id echo and `judge` auto-layer detection

**Does `led` tell me the id of the row it just wrote?**
Yes, as of `6677b2d` — every `led` write path prints `row <id> written.` on success (e.g. `led
review: row 42 written.`, `led register-principal: row 7 written.`), instead of leaving you to
go find the id with a follow-up query. WITNESSED, against `autoharn1`:
```
$ ./led decision "documentation witness probe (orchlog.d / FAQ authoring task): confirming the
  row-id echo on a live write path; no operational effect intended"
SET
SET
INSERT 0 1
led decision: row 1553 written.
```
**The one disclosed exception:** `led obligate` writes into `countersign_obligation`, whose
primary key is the scope text, not a bigint id — there is nothing to echo, so that one path
stays silent by the same documented convention rather than printing something misleading.

**Does `./judge` still need `--layer` spelled out, or can I just run it?**
As of `f550e54`, bare `./judge` (no `--layer`) auto-detects which of `engine/lp_registry.py`'s
layers the world's schema can actually support and runs every capable one — printing a plain
`INCAPABLE` line (not a red failure) for a layer the world's lineage cannot support, rather than
either crashing on it or silently skipping it. Passing `--layer <name>` explicitly is unchanged:
an incapable target asked for BY NAME still refuses loudly (`QUARANTINED`). WITNESSED, both
forms against `autoharn1` (a world with `s22` work but no `s41` identity, so the `defeat` layer
has no grant substrate here):
```
$ ./judge
# marriage differential -- layer=None (auto-detect capable layers: ['tnow', 'work', 'defeat'])
## layer='tnow'
  [OK ] autoharn1 AGREE              asp=2991 sql=2991 atoms; Δasp=[] Δsql=[]
## layer='work'
  [OK ] autoharn1 AGREE              asp=364 sql=364 atoms; Δasp=[] Δsql=[]
## layer='defeat'
  [--] autoharn1 INCAPABLE          layer='defeat' declared: target has no
       principal_binding_active/principal_competence_activity columns (pre-s41 lineage) --
       the 'defeat' layer has no grant substrate here, capability absent, not record-empty
# DIFFERENTIAL GREEN -- every target bit-identical to the SQL floor

$ ./judge --layer defeat
  [!! ] autoharn1 QUARANTINED        asp=0 sql=0 atoms; Δasp=[] Δsql=[]
          asp QUARANTINED: EDB export failed: CapabilityError: target 'autoharn1' did not
          emit trust_grant/n (capability absent): no principal_binding_active/
          principal_competence_activity columns on this schema (pre-s41 lineage) ...
# DIFFERENTIAL RED -- a target diverged/quarantined (NO RESULT)
```
Exit is red only when a layer that actually RAN [`judge`](../GLOSSARY.md#judge)s
`DIVERGE_DEFECT`/`QUARANTINED`; a declared-incapable layer never contributes to the exit code
(the same "absence is not a defect" rule the work-item-violations check already applied).

## `led` help tokens, `--json` payload mode, and `work list`'s default filter (led.tmpl trio)

Three small `led` changes landed together at commit `abba0dd` (build `a2c2a5f`, fixup `cf51542`,
delivery record: ledger row 1562). None of them touch the kernel — all three live entirely in
`bootstrap/templates/led.tmpl`, so (unlike the s40/s41/s42/s43 entries above) they are available
to **any** world scaffolded from this commit or later, including this checkout's own `autoharn1`.

**Can I ask `led` for usage without accidentally writing a row?**
Yes. `'help'`, `'-h'`, or `'--help'` as the FIRST word of the statement prints usage to stderr and
writes nothing on every writing subcommand — but the exit code is 0 only once each subcommand's
own arg-count guard has already been satisfied; see the `led review --help` item just below for
the one case where that guard fires first. This includes `led decision --help` specifically (the
one case a prior pass had missed: `--help` used to fall into the
generic unrecognized-flag refusal instead of the same usage-and-exit-0 teach every other
subcommand's `--help` gets). WITNESSED, `autoharn1`, row count unchanged across all three forms
(`--recent 1`'s leading id was `1567` before and after):
```
$ ./led decision --help
usage: led [flags] <kind> <statement...>   (see top-of-file comment for the full flag list: ...)
       led --recent [N] | led current [N] | led show <id> | led question-status | ...
       ...
       '--help'/'-h'/'help' as the FIRST word of <statement...> prints this usage and writes nothing
$ echo $?
0
```
(`led decision help` and `led decision -h` were run the same way — same zero-write result, same
exit 0.)

**Does the same closure cover `led review --help`?** Only once `review`'s three required
positionals are already present ahead of the token. WITNESSED, `autoharn1`, row count unchanged
(`1567` before and after):
```
$ ./led review --help
usage: led review <entry-id> <verdict> <independence> [--antecedent id] <statement...>
       verdict: attest|attest_with_reservations|refuse
       independence: self-review|technical|managerial|financial
       set LED_ACTOR=<principal-name> to countersign as a registered principal
$ echo $?
1
```
A bare `led review --help` (or `-h`/`help`) hits `review`'s pre-existing `$# -lt 4` arg-count
guard (`bootstrap/templates/led.tmpl` ~line 2501) before `check_help_or_dash_first_word` (line
2506) is ever reached — `--help` alone leaves only 1 positional, short of the 4 the guard wants
(entry-id, verdict, independence, statement). It is zero-write either way (usage on stderr, row
count unchanged), but the exit code is **1**, not 0. The exit-0 path only fires once the three
positionals precede the token:
```
$ ./led review 1 attest self-review --help
usage: led review <entry-id> <verdict> <independence> [--antecedent id] <statement...>
       verdict: attest|attest_with_reservations|refuse
       independence: self-review|technical|managerial|financial
       set LED_ACTOR=<principal-name> to countersign as a registered principal
$ echo $?
0
```
So the help-token closure is complete for `decision` and the other pure-help-anywhere
subcommands, but not yet for `review`'s bare `--help`/`-h`/`help` form — a genuine gap in
`led.tmpl`, not a doc error to paper over.

**What if the first word is dash-leading but not actually a help token?**
It REFUSES, teaching, rather than silently committing the word as statement prose — the same
closure this item's title names. WITNESSED, `autoharn1`, row count unchanged (`1567` before and
after):
```
$ ./led note -weirdflag "rest of statement"
led: REFUSED -- the statement's first word '-weirdflag' is dash-leading, which reads as
  a misplaced or mistyped flag rather than intended statement prose (item
  led-help-token-closure -- the same shape refuse_flag_in_statement forecloses for
  KNOWN led flag tokens anywhere in the statement; this closes the gap for an
  UNKNOWN dash-leading FIRST word, which used to sail through and commit a garbage
  row). NOTHING was written. ...
$ echo $?
1
```
Only the FIRST word is checked (the same first-word/whole-word bound `refuse_flag_in_statement`
already uses elsewhere) — a dash-leading word later in the statement is untouched; reword or
quote it if it is genuinely intended prose.

**Can I write ledger rows as JSON instead of a prose statement?**
`led --json <ledger|review|registration|obligation> <file|->` routes a JSON object straight to
the matching s43 [write boundary](../GLOSSARY.md#write-boundary) function
(`ledger_write`/`review_write`/`registration_write`/`obligation_write`) — the exact same four
functions "The ledger boundary service (`serving/`)" section below documents for its own HTTP
endpoints, so the payload shape is the one documented there (payload keys are the target table's own
column names, verbatim, no second vocabulary). Validation at this layer is well-formedness and
top-level-shape only (parses as JSON, is an object) — everything else is the kernel's own
judgment, and its refusal or acceptance comes back as a [typed verdict](../GLOSSARY.md#typed-verdict),
surfaced verbatim, never paraphrased. The raw payload is size-bounded at 1 MiB
(`MAX_WRITE_BODY_BYTES`, the same bound the HTTP boundary service enforces on its own body), 
checked twice — once on the raw bytes before JSON parsing, once on the re-serialized (compacted)
form before it reaches `psql` — so a payload that only grows past the bound on reserialization is
still caught.

**Prominent caveat, same shape as the s42/s43 entry above:** `--json` maps onto the s43 boundary
functions with deliberately NO pre-s43 fallback — a world whose
[birth chain](../GLOSSARY.md#birth-chain) predates commits `1fc4e8c` (s42) / `84729de` (s43)
refuses `--json` outright, `capability_absent`, before ever reaching the size bound or the
kernel. `autoharn1` (this checkout's own live world) is itself pre-s43, so everything below the
line is what this world can actually show; the size-bound checkpoints and a live typed-verdict
round trip are UNWITNESSED here for that reason and are covered instead by
`seen-red/led-json-payload-mode/run_fixtures.py`'s banked evidence and
[orchlog.d/s42-s43-typed-verdicts.md](../orchlog.d/s42-s43-typed-verdicts.md).

WITNESSED, `autoharn1`, all zero-write (row count `1567` before and after every case below —
argument validation and the capability check both run before `kernel_write` is ever called, so
none of these reach a place that could write):
```
$ ./led --json bogus /tmp/whatever.json
led --json: REFUSED -- usage: led --json <ledger|review|registration|obligation> <file|->
  '<surface>' selects which s43 boundary function ... Got: 'bogus'.

$ ./led --json ledger /tmp/does-not-exist.json
led --json: REFUSED (capability_absent, naming s43) -- this world's kernel does not
  carry kernel/lineage/s43-typed-verdict-write-boundary.sql, mirroring the FastAPI
  boundary service's own pre-s43 refusal ... Use the ordinary prose CLI on this world instead.
```
The same `capability_absent` refusal fires regardless of what the file contains or how large it
is (missing file, malformed JSON, a JSON array instead of an object, and a 1.2 MB oversized
payload were all tried live and all produced the identical capability check, before file
existence or size is ever inspected) — on this world, `--json`'s refusal surface reduces to two
cases: bad `<surface>` word, or `capability_absent`. A world carrying s43 sees the fuller surface
(size-bound refusals, kernel-level unknown-key refusals, and a real accepted write echoing its
row id) — that is the surface `run_fixtures.py` and the boundary-service spec document.

**Does `led work list` show me everything, or just what's live right now?**
By default, just what is open or claimed — closed items are hidden, not deleted; nothing about
the ledger itself changes. `--all` restores the full historical view. WITNESSED, `autoharn1`:
```
$ ./led work list | tail -1
(56 rows)
$ ./led work list | grep -c '| closed'
0
$ ./led work list --all | tail -1
(242 rows)
$ ./led work list --all | grep -c '| closed'
186
```
56 + 186 = 242: `--all` adds exactly the closed rows back, nothing else changes. The choice is
taught in the usage text itself (`led work list [--all]  (work_item_current; default open/claimed
only, --all for the full history including closed)`), and this is a read-verb default only — `led
work asof <timestamp>` and the raw ledger rows remain the complete, unfiltered record regardless
of which view `work list` shows you. An unrecognized flag refuses rather than silently falling
through:
```
$ ./led work list --bogus
usage: led work list [--all]
$ echo $?
1
```
Delivery record for all three items: [orchlog.d/led-tmpl-trio.md](../orchlog.d/led-tmpl-trio.md).

## Ledger-wide as-of read and inspection-copy export (`asof-export`)

This section covers `./asof-export`, the verb that reconstructs the whole ledger's in-force
reading at a past moment and can export that reading as a portable, hash-checkable copy; it
is written as full transcripts because the surface is new and unfamiliar. Ledger item
`asof-export-inspection-copy` (maintainer sign-off 2026-07-18, overnight batch item 1:
"the as-of is basically necessary — I thought that was done by like s5 or something, if we
don't have it then we need it"), merge `1449e0c`, delivery record: ledger row 1585.

**Can I see the whole ledger's in-force reading at some point in the past, not just work
items?** Yes — `./asof-export read --asof <ts>` prints every kind of row (decisions,
reviews, work items, obligations, everything), filtered to what was
[in force](../GLOSSARY.md#supersession) as of that timestamp, not just the three `work_*`
kinds `led work asof <ts>` already covered. It generalizes `led work asof` by one query
shape (every row, not three kinds) rather than replacing it — `led work asof` stays the
right tool when you specifically want work-item state and its derived
open/claimed/closed view. WITNESSED, this checkout's own world, a real supersession pair
(row 1583 written 13:15:43, voided by row 1584 at 13:23:43) shown both-polarity — a moment
before the supersession still shows the superseded row in force, a moment after shows the
superseding row instead, same row count either side:
```
$ ./asof-export read --asof "2026-07-18 13:20:00" | grep -E "ledger id=158[34]|Row count"
Row count    : 1501
--- row 1501/1501 (ledger id=1583) ---
$ ./asof-export read --asof "2026-07-18 13:25:00" | grep -E "ledger id=158[34]|Row count"
Row count    : 1501
--- row 1501/1501 (ledger id=1584) ---
```
The as-of filter is the row's own `ts` (system insert time, never writer-supplied) — never
`event_declared_ts`, which is honest only as far as the declaring writer is honest. A bad
`--asof` value REFUSES loudly rather than returning an empty read, WITNESSED (exit 2):
```
$ ./asof-export read --asof bogus-not-a-timestamp
asof-export read: REFUSED -- as-of query failed: ERROR:  invalid input syntax for type timestamp with time zone: "bogus-not-a-timestamp"
LINE 5:   WHERE l.ts <= 'bogus-not-a-timestamp'::timestamptz
                        ^
```

**Can I get that same reading as a portable, checkable copy — for an inspector, an audit,
or just to keep?** Yes — `./asof-export export --asof <ts> --out <dir>` writes
`ledger-asof.txt` (human-readable, every column of every in-force row, in full),
`ledger-asof.json` (the same rows, machine-readable), and `manifest.sha256`, a standard
`sha256sum -c`-checkable manifest over the two. WITNESSED (scratch directory, not the
ledger — `export` is read-only against the ledger itself, its only writes are the three
named files under the `--out` directory you give it):
```
$ ./asof-export export --asof "2026-07-18 13:25:00" --out /tmp/asof-demo
asof-export export: wrote /tmp/asof-demo/ledger-asof.txt, /tmp/asof-demo/ledger-asof.json, /tmp/asof-demo/manifest.sha256 (1501 row(s) as of 2026-07-18 13:25:00).
  Verify with: (cd /tmp/asof-demo && sha256sum -c manifest.sha256)
  Signing is DEFERRED (standing maintainer crypto ruling) -- this manifest is an UNSIGNED sha256 content hash only. It lets a copy be checked against the bytes it left as; it proves neither who exported it nor that a differently-regenerated copy wasn't substituted for it. No inert --sign flag is offered by this verb.
$ (cd /tmp/asof-demo && sha256sum -c manifest.sha256)
ledger-asof.txt: OK
ledger-asof.json: OK
```
Re-running `export` at the same `--out` REFUSES rather than silently clobbering an existing
inspection copy — an evidentiary export is not overwritten by accident. WITNESSED:
```
$ ./asof-export export --asof "2026-07-18 13:25:00" --out /tmp/asof-demo
asof-export export: REFUSED -- 3 output file(s) already exist under /tmp/asof-demo: ['/tmp/asof-demo/ledger-asof.txt', '/tmp/asof-demo/ledger-asof.json', '/tmp/asof-demo/manifest.sha256']
  An inspection copy is not silently overwritten (ADR-0002). Pass --force to replace it deliberately, or choose a different --out.
$ echo $?
1
```
`--force` replaces it deliberately. The whole loop above ran against this checkout's own
live ledger and left `./led --recent 1` reporting the same leading row id (1592) before and
after every command shown — zero writes to the ledger from either subcommand.

**Is the manifest signed?** No, on purpose, and the verb says so out loud rather than
offering a flag that quietly does nothing. `manifest.sha256` is an unsigned content hash: it
proves a copy's bytes match what left this act; it proves neither who ran the export nor
that a differently-regenerated copy wasn't substituted for it later. Signing stays deferred
under the standing crypto ruling — no `--sign` flag exists at all (an inert flag that looked
armed but wasn't would be its own lie), and both the `.txt` and the `.json` name this limit
in their own header/`signing` field, so a reader of the inspection copy itself sees the same
honest boundary the CLI output does.

## Deployments can self-serve the harness changelog (`orchlog` wrapper at scaffold)

This section is for operators of scaffolded deployments: new scaffolds now include an
`./orchlog` shim beside `led`/`pickup`, so a deployment session can read the harness
changelog without leaving its own directory. Ledger item `deployment-orchlog-surfacing`,
half (b) (half (a) — `./migrate` printing
`./orchlog since <pre-migration-head>` at the end of a run — belongs to the separate,
not-yet-approved migrate-verb item and is untouched here). Merge `bd949af`, delivery
record: ledger row 1585. This is a different thing from the `./orchlog` verb itself (that
landed separately as `orchlog-changelog-verb` and already reads
[orchlog.d/](../orchlog.d/README.md) notes in commit order) — this item is only about
**getting the wrapper into a scaffolded deployment** so a session working there can run it
without hand-relaying anything.

**My deployment isn't the autoharn checkout — can a session working there still read
autoharn's own changelog, to learn what changed since it was last paying attention?** Yes,
if it was scaffolded from commit `bd949af` or later (or has picked the wrapper up by hand,
see below): `bootstrap/new-project.sh` now writes an `./orchlog` shim beside `led`/`judge`/
`pickup`/`audit` in every new [world](../GLOSSARY.md#world), pointed at the harness's own
`orchlog` verb and repo root — no `deployment.json` or ledger connection involved, since the
changelog it reads is autoharn's git history, not the deployment's own ledger. WITNESSED, a
real scaffold run against this checkout, in full:
```
$ ./bootstrap/new-project.sh /tmp/orchlog-demo --db toy --host 192.168.122.1 \
    --schema doctest_orchlog_demo --kern doctest_orchlog_demo_kern --role autoharn_rw \
    --name doctest-orchlog-demo
...
-- orchlog wrapper (self-serve harness changelog, beside led/judge/pickup): exec's autoharn's own orchlog verb against /home/bork/w/vdc/1/autoharn, no deployment.json involved --
wrote orchlog (wrapper -> /home/bork/w/vdc/1/autoharn/orchlog --repo /home/bork/w/vdc/1/autoharn)
$ cat /tmp/orchlog-demo/orchlog
#!/bin/sh
exec /home/bork/w/vdc/1/autoharn/orchlog --repo /home/bork/w/vdc/1/autoharn "$@"
$ /tmp/orchlog-demo/orchlog | head -1
2bc47c539484  2026-07-18  orchlog.d/led-tmpl-trio.md -- docs: led.tmpl trio (help tokens, --json payload mode, work-list filter) — FAQ section + orchlog.d entry, A:B:C attested (B1 DEFECT x2 repaired, B2 CLEAN)
$ /tmp/orchlog-demo/orchlog since abba0dd | head -1
2bc47c539484  2026-07-18  orchlog.d/led-tmpl-trio.md -- docs: led.tmpl trio (help tokens, --json payload mode, work-list filter) — FAQ section + orchlog.d entry, A:B:C attested (B1 DEFECT x2 repaired, B2 CLEAN)
```
The scratch scaffold directory was torn down after this run (it exists only to demonstrate
the shim; it is not a real deployment). No `deployment.json` was needed for the wrapper
itself to work, and this checkout's own live ledger (`./led --recent 1`) was untouched by
the whole exercise.

**My deployment already exists, scaffolded before `bd949af` — do I lose out?** You don't get
the wrapper automatically; there is no scripted refresh verb for it yet (the item's own text
says "at next scaffold-refresh or by hand" — the "or by hand" branch is the honest current
state, not a hedge). By hand, the wrapper is exactly the two lines shown above — the
`#!/bin/sh` line and the `exec` line from the quoted `cat` output (NOT the `$ cat ...`
command line itself), with `EXEC_ROOT` set to your harness checkout's own path — copy them
into a file named `orchlog` beside your `led`/`judge`/`pickup` shims, then `chmod +x` it as
a separate step. The memo-row channel (a plain
ledger `decision` row) stays the way to relay a world-specific note that isn't a general
harness-changelog entry.

## Verifying tags, signed commissions, and documentation debt (`attest-tags`, `verify-commission`, `attest-doc`, `distance-to-clean`)

This section covers four related, but separately-invoked, operator verbs that all answer some
version of "is this claim on the record actually checkable, or only asserted?": `attest-tags`
(are the commit tags claiming ratification really signed by a committed key?),
`verify-commission` (does a signed commission's banked signature actually match the ledger
row's current bytes?), `attest-doc` (has a document been through a fresh-context read at its
CURRENT bytes, per [ADR-0017](../law/adr/0017-the-zero-context-reader.md)'s zero-context-reader
test?), and `distance-to-clean`'s composed DOC-ATTESTATION section (which reads the identical
classification `attest-doc check` reads, folded into one debt total alongside review-gap,
question-status, and work-item debt). This work traces to the maintainer's 2026-07-18 overnight
batch, item 11 ("attest-tags (zero mentions) ... A:B:C with live transcripts"), tracked as
ledger item `overnight-batch-doc-backfill` (claimed row 1606, parent
`post-freeze-documentation-debt` — a ledger row, not a committed page: `./led show 1606` at the
repository root reads it in full).

**Can I check whether this repository's own `ratified/*` git tags are honestly signed?**
Yes — `attest-tags` is a repo-root operator verb ([MAINT-GPG-TRUST-LAYER.md](../design/MAINT-GPG-TRUST-LAYER.md)
§2's "Rung 1"; it verifies THIS repo's own tags, so unlike `led`/`judge`/`pickup` it is never scaffolded into a
deployment) that enumerates every `ratified/*` tag, verifies each one with `git verify-tag`
against ONLY the committed public key(s) in `--keys-dir` (default `law/keys/*.asc`) — built as a
throwaway `GNUPGHOME` per invocation, never the operator's ambient keyring — and separately
flags any commit whose message contains a standalone "RATIFIED" marker but is not the exact
target of a tag that verified GOOD. It reports three per-tag verdicts, all printed, none silent:
`GOOD` (verified against a committed key), `BAD` (a real cryptographic mismatch — tampered,
unsigned, or signed by an uncommitted key), and `UNVERIFIABLE` (no public key is committed at
all — this repository's own honest state today under the standing crypto-generation deferral,
named so it is never mistaken for a pass). Exit 0 only if every enumerated tag verified GOOD and
every RATIFIED-marked commit is covered by one.

Run bare against this checkout (`./attest-tags`, no flags), the tool reports its own honest
starting state — every tag UNVERIFIABLE because `law/keys/` carries no committed key yet, plus a
list of RATIFIED-marked commits with no covering tag (this checkout's own commit history is long
and largely off-topic for this FAQ entry, so only the header is quoted here; the finding-by-
finding detail below exercises every verdict shape instead). This WITNESSED run's header lines
show `./attest-tags` against this checkout:
```sh
$ ./attest-tags
```
```
attest-tags: /home/bork/w/vdc/1/autoharn
  keys committed in /home/bork/w/vdc/1/autoharn/law/keys: 0  (AWAITING-KEY — see law/keys/README.md; every tag below is UNVERIFIABLE until a key lands)
  ratified/* tags: 0

  29 commit(s) claim ratification with no verifying ratified/* tag:
  ...
```
(exit 1). To see every verdict shape (`GOOD`, `BAD`, and the exit-0 all-covered case, not only
`UNVERIFIABLE`), the verb's own `--repo`/`--keys-dir` overrides — documented in its own usage
text as "the witness harness's own use: a scratch repo + a scratch keys dir carrying a THROWAWAY
test key" — point it at a small scratch git repository built for exactly this purpose, with a
throwaway GPG key generated under a scratch `GNUPGHOME` (never the operator's own keyring), one
commit claiming ratification with no tag at all, one whose tag is genuinely signed and covers it,
and one whose tag was tampered after signing. That scratch repo, with the throwaway key
committed, WITNESSED all three non-clean verdicts in one run:
```sh
$ ./attest-tags --repo /tmp/.../repo --keys-dir /tmp/.../keys-real
```
```
attest-tags: /tmp/.../repo
  keys committed in /tmp/.../keys-real: 1
  ratified/* tags: 2
  [!!] ratified/bad-case -> 4dbfc127374d65f9343195a172d1a9ac77bd483c: BAD
        error: ratified/bad-case: cannot verify a non-tag object of type commit.
  [OK] ratified/good-case -> a050bf2d4c6465a3d07c1f16e88750c3c8d6cf26: GOOD

  2 commit(s) claim ratification with no verifying ratified/* tag:
    !! 9ee65db42b4a RATIFIED: a claim whose tag will be tampered/BAD
    !! 16fec35929eb RATIFIED: a claim with no tag at all (uncovered case)

attest-tags: FINDINGS ABOVE — see marks (exit 1)
```
A second scratch repo, with a single RATIFIED-marked commit whose tag is real and covering,
WITNESSED the clean, exit-0 case:
```sh
$ ./attest-tags --repo /tmp/.../repo-clean --keys-dir /tmp/.../keys-real
```
```
attest-tags: /tmp/.../repo-clean
  keys committed in /tmp/.../keys-real: 1
  ratified/* tags: 1
  [OK] ratified/only-case -> d20638cf8a5f9dd6c8fabc7fa0efeb0f973ee4a0: GOOD

  every RATIFIED-marked commit is covered by a GOOD tag (or none exist to claim).

attest-tags: clean (exit 0)
```
`--json` prints the same three verdicts machine-readably (`tags`, `uncovered_ratification_claims`,
`ok`); run WITNESSED against the same key-and-tag scratch repo above, it printed `"ok": false`
with the `BAD` tag's detail and both uncovered SHAs enumerated by field (exit 1).

**Can I check that a specific ledger commission row's banked GPG signature is actually genuine
and current?** Yes — `verify-commission` ([MAINT-GPG-TRUST-LAYER.md](../design/MAINT-GPG-TRUST-LAYER.md) §3's "Rung 2") reads
one `commission`-kind ledger row (most recent by default, or `--id N`), recomputes the
statement's SHA-256 digest from the row's OWN current bytes (never a caller-supplied digest),
and — if a `.claude/commission-<id>.asc` is banked — checks it against ONLY this deployment's own
`keys/*.asc` (a sibling of its `deployment.json`; never autoharn's `law/keys/`, a deliberate
split named in its own module docstring's "KEY-RESIDENCE REVISION" note). It reaches one of five
closed determinations, journaled to `.claude/logs/verify_commission.jsonl` on every run
regardless of which one fires: three verdicts — `VERIFIED` (0, a signed statement whose current
bytes match a
checkable signature), `UNSIGNED` (0, a legitimate weaker claim — LAZY or FULL mode, no `.asc`
banked at all, never a defect), `FORGED-OR-CORRUPT` (1, a real cryptographic mismatch) — plus two
typed refusals distinct from all three, because neither leaves any verdict decidable:
`GPG-UNAVAILABLE` (2, `gpg` itself missing) and `NO-COMMITTED-KEY` (3, a signature is banked but
this deployment's own `keys/` is empty — distinct from `FORGED-OR-CORRUPT`, mirroring
`attest-tags`'s own `UNVERIFIABLE`, per the module docstring's dated REVISION NOTE explaining why
an earlier version wrongly folded the two together).

All five were WITNESSED on a scratch deployment (`bootstrap/new-project.sh --new-world`, torn
down after). The first case shows what happens with no commission row at all:
```sh
$ ./verify-commission
```
```
verify-commission: no commission row found (any commission row) in faq11probe.ledger
```
(exit 2). Writing a LAZY-mode commission (`./led commission "..."`, no `.asc` banked) and
checking it produces:
```
verify-commission: row 7 (actor=author, signing_mode=LAZY)
  statement: 'probe commission, LAZY mode (vicarious transcription), for FAQ item 11 witnessing'
  [..] UNSIGNED
        no .claude/commission-7.asc found — legitimate LAZY-mode commission, not a defect (spec §3: UNSIGNED is a weaker claim, never a failure)
```
(exit 0). Writing a FULL-mode commission (`LED_ACTOR=commissioner ./led commission "..."`) and
banking a real signature over it, while this deployment's own `keys/` is still empty, produces:
```
verify-commission: row 8 (actor=commissioner, signing_mode=FULL)
  statement: 'probe commission, FULL mode, for FAQ item 11 witnessing'
  [!!] NO-COMMITTED-KEY -- a signature is banked (commission-8.asc) but /tmp/faq11-scratch/keys carries NO committed public key (AWAITING-KEY) — nothing exists to check the claimed signature against
```
(exit 3). Committing a throwaway key to this deployment's own `keys/` and re-checking the same
row produces:
```
verify-commission: row 8 (actor=commissioner, signing_mode=FULL)
  statement: 'probe commission, FULL mode, for FAQ item 11 witnessing'
  [OK] VERIFIED
        statement sha256=95582fe15d486f11a596427016b65225496cb199dda6542203a103507ba17f83. gpg: Signature made Sat Jul 18 16:20:12 2026 CEST
gpg:                using EDDSA key 10BC2094D89C920FDE920382B0FCF425E8145063
gpg: Good signature from "attest-tags-probe <probe@example.invalid>" [unknown]
gpg: WARNING: This key is not certified with a trusted signature!
gpg:          There is no indication that the signature belongs to the owner.
      10BC2094D89C920FDE920382B0FCF425E8145063
```
(exit 0). Corrupting one byte of the banked `.asc` after signing, then re-checking the same row,
produces:
```
verify-commission: row 8 (actor=commissioner, signing_mode=FULL)
  statement: 'probe commission, FULL mode, for FAQ item 11 witnessing'
  [!!] FORGED-OR-CORRUPT
        statement sha256=95582fe15d486f11a596427016b65225496cb199dda6542203a103507ba17f83. gpg: CRC error; 753034 - 555B53
gpg: no signature found
gpg: the signature could not be verified.
```
(exit 1). The run's own event journal confirms all six determinations across this session
landed (`GPG-UNAVAILABLE` never fired — `gpg` was present throughout):
```
{"ts": "2026-07-18T14:19:56.247Z", "verdict": "UNSIGNED"}
{"ts": "2026-07-18T14:20:04.173Z", "verdict": "UNSIGNED"}
{"ts": "2026-07-18T14:20:12.346Z", "verdict": "NO-COMMITTED-KEY"}
{"ts": "2026-07-18T14:20:17.509Z", "verdict": "VERIFIED"}
{"ts": "2026-07-18T14:20:31.064Z", "verdict": "FORGED-OR-CORRUPT"}
{"ts": "2026-07-18T14:20:36.196Z", "verdict": "VERIFIED"}
```

**Can I record and check whether a document has actually been through the ADR-0017 fresh-context
loop, at its CURRENT bytes, from inside a scaffolded deployment?** Yes — `attest-doc` is the
per-deployment verb answering the maintainer's own question, "is there a reason we can't [use the
fresh-context audit loop] for end users?" (already answered "no" for `USER-DOC-AUDIT-LOOP.md`
above; this is the verb that question built). `./attest-doc check [PATH...]` classifies every
in-scope `*.md` (default: every one under this deployment, minus scaffold-owned docs — attested
upstream in autoharn itself, not this deployment's to re-attest — and inline-waived ones) as
`ATTESTED` (a fresh-context record exists for this file's EXACT current bytes), `STALE` (a record
exists for this path, but at different bytes — the loop ran once, the file changed since), or
`NO-ATTESTATION` (no record at all); exit 0 iff every in-scope doc is ATTESTED. `./attest-doc
record <json-file>` validates and appends one attestation record — the same schema, same
refusals, as the upstream gate's own `--record` — to THIS deployment's own
`attestations/doc-legibility-attestations.jsonl` (seeded empty at scaffold time), never
autoharn's own ledger of that name.

All three classification states were WITNESSED on a scratch deployment (torn down after).
Checking a freshly scaffolded world's own docs, before any attestation exists, produces:
```sh
$ ./attest-doc check
```
```
attest-doc check: 4 doc(s) in scope, 6 scaffold-owned excluded, 0 waived.
  scaffold-owned (autoharn's own docs, attested upstream -- not yours to re-attest):
    .claude/APPARATUS.md
    .claude/GOVERNED_FILES.md
    .claude/HOOKS.md
    CLAUDE.md
    attestations/README.md
    keys/README.md
  NO-ATTESTATION  .claude/skills/hack-rationalization-detector/PROVENANCE.md
  NO-ATTESTATION  .claude/skills/hack-rationalization-detector/SKILL.md
  NO-ATTESTATION  .claude/skills/hack-rationalization-detector/olds.md
  NO-ATTESTATION  .claude/skills/hack-rationalization-detector/references/known-cases.md
attest-doc check: 0 ATTESTED, 0 STALE, 4 NO-ATTESTATION
```
(exit 1). Recording a throwaway probe document with a well-shaped `doc-attestation/1` JSON body
(`schema`, `doc`, `content_sha256` matching the file's exact bytes, `b_id` — free text naming
which B-round wrote the record — one CLEAN round
enumerating all four Rule-1 clauses, `escalated: false`) produces:
```sh
$ ./attest-doc record /tmp/probe-attestation.json
```
```
doc_attestation_presence --record: appended attestation for probe-doc.md (schema doc-attestation/2, content_sha256 0c5669e635c1..., 1 round(s), escalated=False)
```
(exit 0; the printed schema reads `/2` — the record was accepted and upgraded on write, the
gate's own `doc-attestation/1`-and-`/2` dual-acceptance noted in its module docstring). Checking
that same file again immediately afterward produces:
```
attest-doc check: 1 doc(s) in scope, 0 scaffold-owned excluded, 0 waived.
  ATTESTED        probe-doc.md
attest-doc check: 1 ATTESTED, 0 STALE, 0 NO-ATTESTATION  (0 debt = clean)
```
(exit 0). Appending one more sentence to the same file, so its bytes diverge from what was
attested, then produces:
```
attest-doc check: 1 doc(s) in scope, 0 scaffold-owned excluded, 0 waived.
  STALE           probe-doc.md
attest-doc check: 0 ATTESTED, 1 STALE, 0 NO-ATTESTATION
```
(exit 1) — the classification is purely content-hash-keyed, never path-keyed: the SAME path,
edited, reads STALE, not ATTESTED-for-the-old-content.

**Does this join `distance-to-clean`'s composed debt total?** Yes, opt-in only — the
DOC-ATTESTATION section reads the identical `classify()`/`discover_md()` `attest-doc check`
reads (ADR-0012 P1: one classifier, two callers), but only counts toward TOTAL debt once
`mechanisms.doc_attestation.mode` is `"observe"` in this deployment's `.claude/apparatus.json`
(default `"off"` — a deployment that never adopted the A:B:C loop should see no debt for a
discipline it never opted into; a bad mode value never widens, same convention every mechanism
in this project's apparatus switchboard already follows). Both polarities were WITNESSED on the
same scratch deployment. With the default `"off"`, `distance-to-clean` prints:
```
doc-attestation   : off (opt-in -- set mechanisms.doc_attestation.mode to 'observe' in .claude/apparatus.json once you're running the ADR-0017 A:B:C loop, so debt here reflects a discipline you actually adopted)

TOTAL debt: 0  (0 = clean)
```
Flipping the mode to `observe` (with the STALE probe-doc.md and four scaffold-skill
NO-ATTESTATION docs from above still in place, plus one open+claimed work item added to also
exercise the WORK-ITEMS line in the same pass) then produces:
```sh
$ ./distance-to-clean
```
```
### SECTION: DISTANCE-TO-CLEAN

(reads the SAME views `led review-gap` / `led question-status` / `led work violations` already expose, PLUS the two categories the stop-gate hook (hooks/stop_clean_exit.py) also checks that those three commands don't -- computes nothing new; those three commands remain the disaggregated default, unchanged by this verb)

review-gap        : 0 row(s)
question-status   : 0 open of 0 total
work-violations   : 0 violation(s)
work-items        : 1 open+claimed item(s) [CAVEAT: this tool has no session identity, unlike the stop-gate hook -- it cannot narrow to only THIS session's claims, so it counts every claimed-open item, matching the hook's own DEGRADE fallback for when session ownership can't be proven] -- slugs: ['probe-work']
work-review-gap   : 0 deferred-review item(s)
doc-attestation   : 5 debt (4 NO-ATTESTATION, 1 STALE, 0 ATTESTED) -- ['.claude/skills/hack-rationalization-detector/PROVENANCE.md (NO-ATTESTATION)', '.claude/skills/hack-rationalization-detector/SKILL.md (NO-ATTESTATION)', '.claude/skills/hack-rationalization-detector/olds.md (NO-ATTESTATION)', '.claude/skills/hack-rationalization-detector/references/known-cases.md (NO-ATTESTATION)', 'probe-doc.md (STALE)']

TOTAL debt: 6
```
(exit 1). This is the same composed verb the "Documentation quality" section above already
introduces via `USER-DOC-AUDIT-LOOP.md`; this entry is the witnessed transcript that section
points at rather than restates.

**A note on `settings.json.tmpl`.** This is not a verb — it is the hook-wiring template
`bootstrap/new-project.sh` fills in (`__PROJECT_ROOT__`, `__AUTOHARN_ROOT__`, `__DB__`, `__HOST__`,
`__SCHEMA__`) and writes to every scaffolded deployment's own `.claude/settings.json`, the file
Claude Code itself reads at session start to learn which hooks fire on which tool events. Reading
its own source (`bootstrap/templates/settings.json.tmpl`) rather than a description of it: it
wires nine hook attachments across five lifecycle points — `PreToolUse` (the change gate, stamp
interception, the SQL-write block, and the doc-shapes gate, matched to `Write`/`Edit`/`Bash`/
`AskUserQuestion`/`Read`/`Task|Agent` respectively), `PostToolUse` (the mutation observer twice,
bash completion, the apparatus-flip journal, the delegation observer), a single `Stop` entry
(the stop-gate plus demurral detection), and a `SessionStart` entry scoped to `compact|resume`
(durable-decision replay). Every hook is invoked as `env <VARS> python3
__AUTOHARN_ROOT__/hooks/<script>.py`, so each one reads its own connection/path parameters from
its own named environment variables rather than a shared config object — the same "no shared
mutable config" posture the rest of this project's verb surface follows. This file is the ONE
home of that wiring (ADR-0012 P1): a scaffolded deployment's `.claude/HOOKS.md` documents what
each hook does in prose, but the template above is what actually arms them, and the two are kept
in sync by the scaffold writing both from the same run. UNWITNESSED beyond what a scaffold run
already demonstrates elsewhere on this page (the `--new-world` scaffold transcript under
"Deployments can self-serve the harness changelog" above shows the scaffold writing this file's
filled-in sibling among its output, but a session-start hook-firing trace was not separately
re-captured for this entry) — the concrete blocker is that observing every one of the nine
attachments actually fire would need a live Claude Code session inside a scaffolded deployment
exercising every matched tool type in turn, which this documentation pass did not run.

## Recusal and independent RCA (a conflict-of-interest method harvested downstream)

This section covers a five-step method for what an orchestrator should do when the thing it
would need to judge is a decision it made itself — recuse from the judgment, then dispatch an
independent, evidence-only investigation rather than adjudicate its own work. It is a documented
practice (a discipline to follow by hand), not a mechanism that refuses anything; nothing here
gates a write. Provenance: harvested from the autoharn-panel deployment's own orchestrator
behavior, reconstructed and generalized in this project's own ledger, `recusal-rca-recipe` (row
1358, still open at the time of this writing — a ledger row, not a committed page: `./led show
1358` at the repository root reads it in full).

**What actually happened, the specimen this method generalizes.** WITNESSED — read directly from
this repository's own live ledger this session (`./led show 1364`, kind `finding`, dated
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

**The five steps**, reconstructed from the specimen above and from the same "two-spy synthesis"
practice's own harvest of this method (WITNESSED, `./led show 1357`, kind `decision`, 2026-07-17
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
   [ADR-0018](../law/adr/0018-consults-are-not-front-loaded.md)'s discipline: the witnessed
   problem, the raw evidence, and the governing LAW — never the recusing party's own candidate
   diagnosis, suspect list, or leaning (a front-loaded brief collapses the independence the whole
   method exists to buy). The dispatch itself is the same **out-of-frame second opinion**
   [ADR-0014](../law/adr/0014-executor-second-opinion.md) licenses for a stalled line of
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
section](USER-SHAPED-RECIPES-FAQ.md#the-bookkeeping-close-pairing-convention) for the scaffold
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

**Honest limits.** This is a documented practice, not a mechanized one: no gate checks that a
conflicted orchestrator actually recused, that a dispatched RCA was actually briefed
evidence-only, or that a systemic finding actually got filed separately rather than folded in —
all four are review-only, exactly as [ADR-0014](../law/adr/0014-executor-second-opinion.md) and
[ADR-0018](../law/adr/0018-consults-are-not-front-loaded.md) themselves disclose for their own
enforcement surface. A maintainer ratification (WITNESSED, `./led show 1366`, read this session)
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

## What this page is not

This page is not an inventory (that is [ORCH-CAPABILITIES.md](../ORCH-CAPABILITIES.md), where every
mechanism carries witnessed output or an honest UNWITNESSED mark), it is not a setup guide
([USER-GUIDE.md](USER-GUIDE.md)), and it is not a promise that a recipe listed here is
enforced — where an entry says "declaration only," the enforcement genuinely does not
exist yet, and the cited spec names the stage that would build it.
