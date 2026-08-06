# Setup and scaffold — recipes

*Factored out of [`user-guide/USER-RECIPES-FAQ.md`](../USER-RECIPES-FAQ.md) at commit
`178ec789439044bebb664e7374c2be757d064d11`, sections "Getting started: the guided setup TUI" and "Deployments can self-serve the
harness changelog (`orchlog` wrapper at scaffold)"; byte-preserving (mechanical `../` depth
repairs and named cross-file link rewrites only).*

**Charter:** what you do to stand a world up, and what the scaffold puts inside it. Belongs:
anything performed at or before birth, and any shim/template the scaffold writes. Does not
belong: anything an operator does to a running world's record (see the other seven recipe
files in this directory, and the [index](../USER-RECIPES-FAQ.md)).

---

## Getting started: the guided setup TUI (`python3 -m tools.setup_tui`)

**Is there a guided path from nothing to a running [world](../../GLOSSARY.md#world) (this project's
term for one scaffolded, database-backed deployment), instead of typing the scaffold commands by
hand?** Yes — `python3 -m tools.setup_tui.app`, run from your autoharn checkout (the bare
`python3 -m tools.setup_tui` this section's own heading uses is equivalent — `tools/setup_tui/
__main__.py` is a thin redirect to the same `app.py`'s `main`; this doc uses the explicit
`.app` form throughout for clarity).
It is a **driver of the existing verbs, never a second implementation**: every screen shows
the exact command it is about to run (`bootstrap/new-project.sh`, `bootstrap/teardown-world.sh`,
`boundary_service`, `led`) and streams that command's real output, so if the process dies
mid-flow you can finish by hand from what was already printed. Full spec:
[FABLE-SETUP-TUI-SPEC.md](../../design/FABLE-SETUP-TUI-SPEC.md); commission ledger row 1656
("so much to remember ... too much when you want to *just get started but still have a
seriously robust experience*").

**The interactive face is a real Textual application — a hierarchical configuration tree, not a
sequence of numbered prompts.** The pre-2026-07-22 build described in
[design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md — now archived under vestigial_documentation/](../../vestigial_documentation/design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md)
(a linear "N/11 Screen" flow, one screen at a time) was deleted wholesale and replaced by the
configtree rebuild,
[design/FABLE-SETUP-TUI-REBUILD-SPEC.md](../../design/FABLE-SETUP-TUI-REBUILD-SPEC.md) — this
paragraph describes the CURRENT rebuild, corrected 2026-07-23 (usability review, ledger row
1180, the "teletype-as-current" hazard the 2026-07-23 doc sweep flagged but did not fix). The
maintainer's own words commissioning the rebuild: *"I tried to run the setup TUI after
installing 'textual' into a venv and I'm not really happy with how it looks -- in fact, textual
is not used, at all, it is not a TUI, it is just a collection of prompts no matter how clean the
code is... Could we make it into a real 'textual' app?"* It now is: a generic library,
`tools/configtree` (`ConfigTreeApp`), driving a **sidebar `Tree` of every configuration
section** (not a linear sequence — the operator opens and fills sections in any order the tree
allows), a form pane per section, a docked prompt area, dependency-as-data blocking (a section
that needs another section's answer first is shown but not enterable until that dependency is
met), and one terminal **commit node** that renders the full plan and asks for one explicit
confirmation before anything is applied. `tools/setup_tui/tui_app.py` — genuinely thin, the
package's only `import textual` — builds a `ConfigTreeApp` from `tools/setup_tui/steps.py`'s
`SECTIONS` tuple and `COMMIT` spec; all Tree/pane rendering lives in the `tools/configtree`
library itself, not in autoharn-specific code. `textual` not being importable is a hard REFUSAL
naming the install command (`tools/setup_tui/app.py`'s own docstring: *"there is no fallback UI
to maintain"*) — there is no numbered-menu or zero-dependency fallback mode left; `--from-config`
is the one no-TUI path, for scripted/CI use, not an interactive substitute. `textual` itself
remains a declared external cost of THIS TOOL's interactive face only — never of the harness, a
born world, or the witnessing path — install it into a venv if you don't already have it:
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
seen-red/setup-tui-textual-shell (deleted 2026-07-22, design/FABLE-SETUP-TUI-REBUILD-SPEC.md wholesale rebuild).

**The ten sections, plus the commit checklist** (every section skippable where the section
itself allows it, the skip recorded — never silent; `--start-at <slug>` below jumps straight to
any one of them — the slug, never a hand-typed number, is the only stable pointer: section
identity is derived from `tools/setup_tui/steps.py`'s own `SECTIONS` tuple, one home, precisely
so a doc pointer never drifts the way a hardcoded ordinal would the moment a section is
inserted). `SECTIONS` is a plain tuple with **no implied visiting order** — the sidebar tree
lets you open any section any time its own dependencies are met; the list below is `SECTIONS`'
registration order, which doubles as the commit-time execution order (`commit_pane.py`'s own
`_run_submit_sweep` runs every section's `submit` "exactly once, in registry order"), grouped by
the sidebar's own groups (`Substrate & target`, `World lifecycle`, `Runtime`, `Authority &
trust`):

1. **Preflight** (`--start-at preflight`, group *Substrate & target*) — repo commit, submodules
   populated, `idris2`/`clingo`/`python3`/`psql` found (clingo non-fatal, matching
   `bootstrap/bootstrap.sh`'s own posture), whether `HARNESS_PGHOST`/`EPISTEMIC_PGHOST`
   resolves to a reachable host; each check green/red with a fix command.
2. **Substrate** (`--start-at substrate`, group *Substrate & target*) — pick an existing
   database (zero manual steps) or a dedicated one (generates the confined `pg_hba` block in
   your *actual* file's own idiom, plus the createdb/copy/reload block, then probes until the
   connection genuinely works).
3. **Fork/target** (`--start-at fork-target`, group *Substrate & target*) — destination
   directory: a fresh directory, or a fork-copy of an existing project (with the `CLAUDE.md` →
   `CLAUDE.project.md` preservation move, so a fork's own governance prose survives the
   scaffold's unconditional `CLAUDE.md` write) — plus the governed-files pattern prompt
   described below.
4. **Rehearsal** (`--start-at rehearsal`, group *World lifecycle*) — a scratch-name birth +
   teardown + zero-residue check, streamed; the real birth is gated on a green rehearsal (a
   ratified discipline, not a suggestion — the Birth section refuses without one unless you
   explicitly override).
5. **Birth** (`--start-at birth`, group *World lifecycle*) — `new-project.sh --new-world`,
   streamed; the maintainer copy-paste signing line is surfaced prominently at the end,
   delimited by `BEGIN`/`END` markers.
6. **Boundary** (`--start-at boundary`, group *Runtime*) — writes the multiplex TOML (the
   config file letting one boundary service process serve several deployments/worlds side by
   side) and the two `deployment.json` boundary keys, picks a free port, starts the service (or
   emits the systemd-style unit text as a copy-paste block when this process doesn't keep it
   alive itself), probes `/health` and `/meta`. Runs BEFORE Principals & authority / Signed
   genesis below (moved ahead of them, legacy-led-retirement Part C completion, ledger row
   1158/1159) so those two sections' own writes already go through the served `led`, never the
   retired direct-psql shim.
7. **Principals & authority** (`--start-at principals-authority`, group *Authority & trust*) —
   registers additional principals, grants [s41](IDENTITY-AND-AUTHORITY.md#granting-and-revoking-a-principals-authority-s40s41) competences
   (recorded beliefs about who is trusted to do what, at what confidence band, on what basis)
   and typed relations (e.g. acts-for, dispatched-by), and registers role charters (a written
   statement of what a role is for and what it may do, filed against a registered principal via
   `tools/role_charter.py`) in-flow; skipping it is legitimate (the scaffold's own three
   principals already make a complete world).
8. **Signed genesis** (`--start-at signed-genesis`, group *Authority & trust*) — the
   GPG-signing ceremony for the world's founding commission, on by default; full operator
   walkthrough (four visible commands, the VERIFIED gate, the skip path, rotation) in
   [USER-GPG-TRUST-LAYER-FAQ.md §5a](../USER-GPG-TRUST-LAYER-FAQ.md#5a-the-setup-tuis-own-signed-genesis-screen--the-same-ceremony-automated).
9. **Observability** (`--start-at observability`, group *Runtime*) — the `otelcol` start line
   (localhost-only), the OTel model-provenance watchdog start line (`./otel-watch --daemon`,
   a background process that checks the OTel telemetry stream for the model-identity/
   provenance fields this project's OTel-attestation discipline requires and flags gaps loudly),
   and the Claude launch line with the right env vars, as copy-paste blocks with a
   what-you-should-see line each.
10. **Hydration** (`--start-at hydration`, group *Runtime*) — free-text prompts for fork
    provenance and role charters to register, plus two curated catalogs described below
    (feature-facts, durable-decisions), and an ADR-adoption submenu derived from `law/adr/*.md`
    at runtime (never a hand list).

**Checklist / commit** (`--start-at checklist`) is not one of the ten sections above — it is the
separate terminal **commit node** (`steps.py`'s `COMMIT`, a `CommitSpec`) the tree's sidebar
shows alongside them: a per-item WITNESSED/SKIPPED/REFUSED/PREPARED
    table of everything the flow touched, offered for saving into the new world as a dated
    file.

**The feature-facts column** ([design/FABLE-SETUP-TUI-FEATURE-FACTS-SPEC.md](../../design/FABLE-SETUP-TUI-FEATURE-FACTS-SPEC.md), ledger row 1714)
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
([SONNET-CATALOG-GENERICITY-CRITIQUE-2026-07-19.md](../../design/SONNET-CATALOG-GENERICITY-CRITIQUE-2026-07-19.md)):
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
the driver logic; `tools/setup_tui/steps_fork_target.py` wires it into the Fork/target section.
WITNESSED
this session (`python3 -m tools.setup_tui.app --dry-run --scripted <answers>
--start-at fork-target`, declining the extension):
```
facts [governed-files pattern exposure] -- aspiration: [F33](../../FINDINGS.md) (governance keyed to WHAT THE THING
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

**Principals & authority** ([design/FABLE-SETUP-TUI-PRINCIPALS-AUTHORITY-SPEC.md](../../design/FABLE-SETUP-TUI-PRINCIPALS-AUTHORITY-SPEC.md), ledger rows
1727/1728) **is built and merged**, sitting between Birth and Signed genesis
(`--start-at principals-authority`). It registers additional principals, grants s41
competences, asserts typed relations, and registers role charters in-flow, showing a short
teaching line before each act explaining what it does and why, binding on every act, not
merely offered as optional help text (`tools/setup_tui/principals_authority.py` carries the
driver logic). Declining is legitimate and legible — every world already has
`author`/`reviewer`/`commissioner` from the scaffold (see ["Granting and revoking a
principal's authority (s40/s41)"](IDENTITY-AND-AUTHORITY.md#granting-and-revoking-a-principals-authority-s40s41)), so skipping this screen leaves a complete
world; the screen's own value is propaedeutic, walking the ceremony once rather than a
prerequisite for a working world.

**Signed genesis** ([design/FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md](../../design/FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md), ledger rows 1724–1726)
**is built and merged**, sitting between Principals & authority and Boundary
(`--start-at signed-genesis`). It is an optional, on-by-default, no-quiz keygen riding the existing
GPG web-of-trust machinery (no new crypto stack — the existing GPG trust layer this project
already ships) that generates a keypair, exports the public half into
the world's `keys/`, signs the world's founding commission, and verifies it against your own
key — one-time, no ongoing signing burden afterward. `tools/setup_tui/signed_genesis.py`
carries the driver logic. The full operator walkthrough — what you type, what you should see,
the four visible commands, the VERIFIED gate, the skip path, and key rotation via re-run —
lives in
[USER-GPG-TRUST-LAYER-FAQ.md §5a](../USER-GPG-TRUST-LAYER-FAQ.md#5a-the-setup-tuis-own-signed-genesis-screen--the-same-ceremony-automated),
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
  seen-red/setup-tui-dry-run-parity (deleted 2026-07-22, design/FABLE-SETUP-TUI-REBUILD-SPEC.md wholesale rebuild)
  (degrades to UNEXERCISED, exit 0, without a reachable Postgres host and the boundary
  service's venv — same honest-degrade posture as this doc pass hit live). This particular
  table predates [design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md](../../vestigial_documentation/design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md)'s Textual-face build and was captured
  against an interpreter without `textual` installed — kept verbatim as a historical witness,
  per this doc's own no-retro-edit discipline. Where `textual` IS importable that row instead
  reads `available`, and the interactive face above the table becomes the real Textual
  application, not the numbered-menu fallback; see
  seen-red/setup-tui-textual-shell (deleted 2026-07-22, design/FABLE-SETUP-TUI-REBUILD-SPEC.md wholesale rebuild) for
  that build's own live witnesses.

**What does the wizard actually guarantee if I kill it, or my machine dies, partway through?**
([design/FABLE-SETUP-TUI-PURE-CORE-SPEC.md](../../design/FABLE-SETUP-TUI-PURE-CORE-SPEC.md) §2.6,
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
  [gates/setup_tui_purity_gate.py](../../gates/setup_tui_purity_gate.py) asserts this mechanically,
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
["Drift backstops"](METHODS.md#drift-backstops-one-generic-method-for-anything-that-goes-quietly-stale):
seen-red/setup-tui-scripted-smoke (deleted 2026-07-22, design/FABLE-SETUP-TUI-REBUILD-SPEC.md wholesale rebuild) (the
setup surface's own scripted smoke fixture, hostile/malformed inputs),
[seen-red/setup-tui-feature-facts-drift](../../seen-red/setup-tui-feature-facts-drift/run_fixtures.py)
(the feature-facts registry vs. what the screens actually expose), and
seen-red/setup-tui-dry-run-parity (deleted 2026-07-22, design/FABLE-SETUP-TUI-REBUILD-SPEC.md wholesale rebuild) (WDR1
byte-identical tree/ledger, WDR2 argv parity dry-vs-live, both needing real infra).

<!-- doc-attest-exempt: this whole "Exporting the setup TUI's config schema" section is new
prose, Sonnet-authored 2026-08-06 under work item setup-schema-consumption-channel (ledger
rows 1031/1063/1068, brief design/BRIEF-B1-SETUP-SCHEMA-VERB-2026-08-04.md). Every example
output is real, witnessed this session against this checkout; no live A:B:C loop has run on
this section yet and this marker does not claim one did. Removal condition: strike this
marker and run the real A:B:C loop next time this section is touched for its own prose
content, not just a byte-preserving move. -->

## Exporting the setup TUI's config schema for external consumers (`./autoharn setup-schema`)

**I want to build `--from-config`/`--initial-config` TOML for the setup TUI from outside this
checkout (a sibling project doing local dev, or a CI/build pipeline that only has a pinned
autoharn commit) — where do I get the schema, and how do I know I got the right one?**
`tools/setup_tui/data/config_schema.toml` (loaded by `tools/setup_tui/config_file.py`) is the
single authority for that schema (work item setup-schema-consumption-channel, ledger rows
1031/1063/1068) — never copy it by hand or reconstruct it from the screens' own field lists,
since a hand-copy or reconstruction drifts from the authority the moment either side changes.
`./autoharn setup-schema` is the sanctioned, layout-independent access point: run it against a
sibling checkout for local dev, or against a pinned commit of this repo for CI/build — the
verb's own contract, not this repo's tree layout, is what an external consumer depends on
(ledger row 1063's own channel decision). **Format/path changes to the schema file itself are
announced by missive before landing**; this verb's contract (below) is the stable surface.

Two modes, so the byte-verbatim export is never polluted by the provenance obligation:

- **Default** — the schema file's bytes, byte-verbatim, on stdout: `./autoharn setup-schema >
  config_schema.toml` gives you an exact copy of the authority file, nothing injected. A
  provenance line (source path, sha256, repo HEAD commit) still prints to **stderr**,
  unconditionally, so you see what you got even while redirecting stdout to a file.
- **`--provenance`** — a separate sidecar mode: a small JSON object (`source_path`, `sha256`,
  `repo_commit`, `read_at`) on stdout, no schema bytes at all — the machine-readable channel for
  a CI/build consumer checking a pinned checkout's schema for drift.

A missing or unreadable schema file refuses loudly on stderr with a nonzero exit — never empty
stdout with exit 0.

WITNESSED this session, against this checkout:
```
$ ./autoharn setup-schema > /tmp/setup-schema-out.toml
setup-schema: source=tools/setup_tui/data/config_schema.toml sha256=b0bb1c8a46aa6de79a94927a8c1d26debe39f6772321335c0c744a7733c362a6 repo_commit=97efb7d8aad344ff42f16a8d90d89cc7e3ea8569 read_at=2026-08-06T04:32:58Z
$ diff -q /tmp/setup-schema-out.toml tools/setup_tui/data/config_schema.toml
(no output -- byte-identical)
$ sha256sum tools/setup_tui/data/config_schema.toml
b0bb1c8a46aa6de79a94927a8c1d26debe39f6772321335c0c744a7733c362a6  tools/setup_tui/data/config_schema.toml
$ ./autoharn setup-schema --provenance
{
  "source_path": "tools/setup_tui/data/config_schema.toml",
  "sha256": "b0bb1c8a46aa6de79a94927a8c1d26debe39f6772321335c0c744a7733c362a6",
  "repo_commit": "97efb7d8aad344ff42f16a8d90d89cc7e3ea8569",
  "read_at": "2026-08-06T04:32:59Z"
}
```
And the refusal path, witnessed by temporarily renaming the authority file out of the way and
restoring it immediately after (`git status --porcelain` confirmed clean before and after):
```
$ mv tools/setup_tui/data/config_schema.toml /tmp/config_schema.toml.bak
$ ./autoharn setup-schema; echo "exit=$?"
setup-schema: REFUSED -- schema file not found at /home/bork/w/vdc/1/autoharn/tools/setup_tui/data/config_schema.toml (expected relative path: tools/setup_tui/data/config_schema.toml). The setup TUI's config_schema.toml is the single authority (ledger row 1063); if this checkout is missing it, the checkout itself is broken -- nothing was printed to stdout.
exit=1
$ mv /tmp/config_schema.toml.bak tools/setup_tui/data/config_schema.toml
```
Full usage: `./autoharn setup-schema --help`.

## Deployments can self-serve the harness changelog (`orchlog` wrapper at scaffold)

This section is for operators of scaffolded deployments: new scaffolds now include an
`./orchlog` shim beside `led`/`pickup`, so a deployment session can read the harness
changelog without leaving its own directory. Ledger item `deployment-orchlog-surfacing`,
half (b) (half (a) — `./autoharn migrate` printing
`./orchlog since <pre-migration-head>` at the end of a run — belongs to the separate,
not-yet-approved migrate-verb item and is untouched here). Merge `bd949af`, delivery
record: ledger row 1585. This is a different thing from the `./orchlog` verb itself (that
landed separately as `orchlog-changelog-verb` and already reads
[orchlog.d/](../../orchlog.d/README.md) notes in commit order) — this item is only about
**getting the wrapper into a scaffolded deployment** so a session working there can run it
without hand-relaying anything.

**My deployment isn't the autoharn checkout — can a session working there still read
autoharn's own changelog, to learn what changed since it was last paying attention?** Yes,
if it was scaffolded from commit `bd949af` or later (or has picked the wrapper up by hand,
see below): `bootstrap/new-project.sh` now writes an `./orchlog` shim beside `led`/`judge`/
`pickup`/`audit` in every new [world](../../GLOSSARY.md#world), pointed at the harness's own
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
