# FABLE-SETUP-TUI-FIELD-STRATEGY — disposition of the 2026-07-19 field test

This document is the repair strategy for autoharn's setup TUI (the terminal wizard,
`tools/setup_tui/`, that walks an operator through creating a new autoharn
deployment). The maintainer field-tested the wizard by creating a real deployment,
found it badly lacking, and filed eight observations; a downstream agent filed eight
more. This document answers one question, for the maintainer and for whoever builds
the fixes: why does each defect exist, and what sequence of work closes them all?

- **Status:** Proposed (Fable-authored strategy, awaiting maintainer reading; the two
  constitutional items inside it additionally require maintainer ratification per the
  standing orchestration contract).
- **Date:** 2026-07-21
- **Inputs:** the maintainer's eight verbatim field observations (a–h, quoted in full
  below), the downstream [world](../GLOSSARY.md#world)'s `AUTOHARN_BACKFLOW.md` (8
  findings, triaged), and four read-only investigator reports — Sonnet agents
  dispatched to diagnose before any strategy was written (ledger rows 1848–1849
  record the dispatch's predicted tool-call/time/token cost and the measured actuals,
  the project's standing estimate-vs-actual retrospective practice).
- **Law read in full before authoring:** ADR-0000, ADR-0002, ADR-0007, ADR-0012.
  Per ADR-0000 Rule 2, every item below carries its two-question answer (the type that
  forecloses the class; the operational lapse that admitted it) *before* any fix shape.

## 0. The maintainer's commission, verbatim

```
    a. walls of text make reading super-hard; should have a limit on sub-element text width and clearly deliminate distinct semantic elements (e.g. column headers etc)
    b. file size violation; factor out the configuration content from code #governance
        1. (ADR-0012 extension: data is not code; factor out the prompts)
    c. TUI fails if dest-dir exists (add a sentinel to target directory and create a function that tests whether it is compatible with autoharn)
    d. quit doesn't work (spurious?)
    e. no way to navigate back and forth in the TUI, so if you change your mind you have to start over
    f. after finally answering all questions, seems that PTY control is not released to the user
    g. had to manually start boundary-multiplex
        1. on that note: should create a daemon collection script depending on selected options that start all relevant daemons and stores into the project folder.
    h. crash on running rehearsal test
```

## 1. Root-cause synthesis: four classes cover nearly everything

The investigation's individual mechanisms (§3, §4) collapse into four defect classes.
This is the ADR-0000 overview the commission asked for — the reasons these sharp edges
exist, stated at class level so the fixes foreclose classes, not instances.

**Class I — structure erased into `str` / prose embedded in code.** The whole UI
content surface is `Ui.say(text: str)`: banner, paragraph, table row, status, and prompt
are all the same type by the time a renderer sees them, so no renderer can bound a
paragraph's width or style a header (observation a). The same erasure one level up:
~40–60% of several modules is prose/config living *as code* (observation b) — the
"kind" of content (copy to be edited as writing vs. logic to be reviewed as code) is
not represented anywhere. One class, two registers. The foreclosing type is a typed
content vocabulary: UI emission becomes typed elements (heading / paragraph / table /
status), and authored copy becomes data the code loads, not literals the code contains.

**Class II — a boundary fact probed ad hoc instead of owned once.** "What is the
destination's relationship to autoharn" is answered by five independent, disagreeing
checks — one screen refuses any existing path, one screen checks nothing at all, three
re-implement their own probe (observation c). The identical shape in the hooks:
`stamp_provenance.py` derives its subject root from its own file location while 15
sibling hooks take `GATE_SUBJECT_ROOT` (backflow 2). Foreclosing type: one
`DestinationState` classification (FRESH | AUTOHARN_WORLD(complete|partial) |
FOREIGN_CONTENT) computed at one Port — an explicit boundary function every consumer
calls and none re-implements, [ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md)
P2's term (P2 is that ADR's second numbered principle; P-numbers below all cite its
nine) — and consulted everywhere, backed by the sentinel the maintainer named; and
the outlier hook joins the existing subject-root discipline.

**Class III — "told" conflated with "verified" in the checklist's own vocabulary.**
`PREPARED` means "instructions were printed," but reads as assurance; a REFUSED
signed-genesis gate records a row and the ceremony completes anyway. Result: an
opted-in monitoring feature with zero coverage and no end-of-run signal (observation g
/ backflow 3), and a [birth](../GLOSSARY.md#birth-chain) that completed with a
permanently-unverifiable genesis commission — the gpg-signed founding instruction
every deployment's audit trail is supposed to be verifiable back to (backflow 1). The
checklist status enum is one value doing two jobs — an
ADR-0000 type gap in the instrument whose entire purpose is honest witness. Foreclosing
type: split the status vocabulary (instructions-printed vs. prerequisite-confirmed vs.
verified-running), and make gate-severity a typed property a REFUSED row can carry
(advisory vs. ceremony-blocking).

**Class IV — silent fallback at the softest rung (ADR-0002 rung 5).** The operator's
explicit "yes, start the boundary service" (the maintainer's "boundary-multiplex" in
observation g — same standing daemon, called the boundary service in the code) is
silently downgraded to manual
instructions when a hardcoded venv path is absent (observation g); `ctrl+c` silently
does nothing (observation d); `stamp_provenance.py` silently `return 0`s out of scope
(backflow 2); gpg signing silently resolves to the ambient default key (backflow 1).
Four instances, one tenet violation. These get loud refusals or honest messages at the
right rung — each is individually small, and the class is the point.

**The Rule 2(b) finding (the executive lapse), stated plainly.** `screens.py` was born
at 572 lines — already over ADR-0007's ceiling — and grew to 1458 across sixteen
commits, four of which were dedicated fresh-context ADR-compliance reviews citing
ADR-0000/0012. None asked ADR-0007's own trigger question, because nothing mechanized
it and the review briefs aimed attention elsewhere (WITNESSED, governance report §4–5).
That is ADR-0007 Revisit-when #1's mechanization trigger firing for real: the
review-only surface failed four consecutive times on one package. The net to mint is a
file-size gate. Same lapse-family, second instance: the pure-core spec and its reviews
never carried a UX/operator-experience lens at all — every review dimension was
correctness-shaped, so the a/d/e/f class had no reviewer whose job it was to see it.

## 2. Strategy shape: three tracks

**Track 1 — constitutional (Fable authors, maintainer ratifies).** Two amendments, one
gate:
1. **ADR-0012 amendment — "data is not code."** New anti-pattern row + principle:
   authored content (prompts, teaching copy, feature descriptions, catalog prose) and
   configuration tables live as *data* with one home, loaded by code, never embedded as
   literals interleaved with logic. The governance report confirms no existing ADR owns
   data-vs-logic *location* (ADR-0007 owns size, P1 owns duplication) — this is
   genuinely new law, not restatement. Drafted per
   [ADR-0018](../law/adr/0018-consults-are-not-front-loaded.md) discipline; it can
   share a Fable session with a second, separate ADR-0012 amendment already ratified
   in principle (ledger row 1826): extending that ADR's ninth principle, P9 — stated
   today for compiled components only — to cover the setup wizard's class of
   progressive per-screen effects ("the P9 lift"). The two amendments stay separate
   acts.
2. **ADR-0007 mechanization — a `max_lines` gate** (`gates/` + pre-commit wiring
   alongside the already-queued purity-gate wiring), ratcheting baseline over current
   offenders per the ADR's own no-retroactive-sweep posture. New files meet the bar;
   the five offenders enter the queue and shrink via Track 2's extractions.
3. **Gate-severity policy question for the maintainer (not Fable's to decide):** should
   a REFUSED signed-genesis verification gate *block* ceremony completion? Backflow 1
   makes the case that a permanently-unverifiable genesis is not a checklist footnote.
   Queued as a prepared yes/no.

**Track 2 — class fixes in the TUI (Sonnet builds against Fable specs).**
1. **Typed UI content vocabulary** (Class I, register 1): extend the `Ui` interface
   from `say(str)` to typed elements; renderers apply per-kind treatment (bounded prose
   measure, real headers, aligned tables — the `DataTable` checklist view is the
   existing good precedent). Closes observation a by construction.
2. **Prompt/content extraction** (Class I, register 2): the three block-structured
   files (`feature_facts.py` 62% data, `durable_decisions.py` 63%,
   `principals_authority.py` 44%) extract cleanly to data modules/assets; `screens.py`'s
   interleaved copy extracts *through* the typed-element rework (each screen's copy
   becomes keyed content data), not as a separate cut-paste pass. Together with 3 below
   this is what actually shrinks the ADR-0007 offenders.
3. **`DestinationState` + sentinel** (Class II): one classification function, a
   sentinel marker written at birth, `screen_fork_target` gains the missing third mode
   (pre-populated destination — the blank world proves operators need it),
   `screen_birth` stops trusting `state["dest"]` unchecked, `new-project.sh` refuses
   FOREIGN_CONTENT instead of merging into it.
4. **Checklist status split + daemon reification** (Class III): split
   `PREPARED`; generate a per-world `start-daemons` script from the same plan-entry
   data that already knows every selected daemon (the maintainer's g.1, and the
   mechanism already half-exists — `BackgroundAct`/PREPARED lines are data); actually
   scaffold `otelcol-config.yaml` when the feature is selected; end-of-run
   verification pass over operator-selected features (the substrate screen's
   probe-after-PREPARED pattern, applied uniformly).
5. **Wizard navigation** (observation e): position + answer history become typed,
   navigable state over the screen list. This is the one item needing genuine design
   work (it interacts with the pure-core plan/journal machinery); Fable writes a short
   spec before any build. Until it lands, the screen copy saying "go back" gets
   corrected — prose must not promise a capability the code lacks.

**Track 3 — local fixes (small, witnessed, mostly one-liners; Sonnet batch).**
- f: `stdin=subprocess.DEVNULL` in `runner.start_background` (runner.py:147) + route
  the never-drained `stdout=PIPE` to a log file (both hazards at the one choke point).
- d: bind `ctrl+c` to quit-or-hint (it is currently shadowed by Textual 8's
  `Screen.copy_text` and silently no-ops); align the quit action name so the base
  help-hint can fire. The designed `ctrl+q` path provably works (WITNESSED, headless
  harness) — this half of d was spurious, the silent-no-op half is real.
- g: boundary-service interpreter falls back to `python3` on PATH (the pattern
  `new-project.sh` already uses) and *says so loudly* when the preferred venv is absent.
- Backflow 1: pin `sign_statement_act` to the just-generated fingerprint (`-u`), the
  same hole `export_public_key_act` already threads; fix the raw multi-key dump in
  `keys/README.md`.
- Backflow 2: `stamp_provenance.py` takes `GATE_SUBJECT_ROOT` like its 15 siblings;
  whether it *ships* to scaffolded worlds is a separate maintainer scope decision —
  until made, its dev-only scope gets documented where a downstream reader looks.
- Backflow 5: hoist the path-token warning boilerplate out of the per-token loop
  (independently WITNESSED live this session — row 1849's write printed it four times).
- Backflow 7a: one sentence in `resolve-violation` usage text naming the closed-state
  precondition for `retired` dispositions on `work_opened` targets.
- Backflow 8: idris2 preflight gets clingo's non-fatal wording, or repo-context scoping.
- Backflow 4: the birth output names the concrete consequence of deferring `git init`
  (while a deployment has no git repository, the ceremony-free "bookkeeping" way of
  closing a work item — which must cite a commit — is unusable, so every close accrues
  review debt).

## 3. Non-issues and open evidence gaps (named, not buried)

- **h (rehearsal crash): UNEXERCISED.** The captured world's own transcript shows its
  one rehearsal run completing GREEN end-to-end; no traceback exists anywhere in the
  world's logs, and `setup_log.txt` cuts off mid-gpg (~line 2400), so the evidence does
  not cover every attempt made that day. No mechanism is asserted. **Needs the
  maintainer:** roughly when/how it crashed, or one re-run with the transcript kept.
  Filed, not guessed at.
- **d, half of it:** "quit doesn't work" is spurious for `ctrl+q` (witnessed working);
  real for `ctrl+c` (witnessed silent no-op). Fix covers both readings.
- **Backflow 6 (subagent review independence): downstream education, not a defect.**
  The kernel already supports the case — a dispatched subagent's *own* tool-call
  context lands a distinct `stamp_agent` and passes s21. The refusal fired because the
  orchestrator transcribed the verdict itself, which the kernel is *right* to refuse
  (nothing distinguishes a relayed verdict from an invented one). Upstream residue: the
  refusal's teach-text and docs should state the "subagent writes its own review"
  pattern; that doc fix is in Track 3's spirit and queued with it.
- **Backflow 7b (`--supersedes` kind-validation): already-ratified tradeoff** (s31,
  "ratified fork 1", spec on record 2026-07-15) — not reopened. At most a future
  context-sensitive advisory when a composite parent with live children is targeted.
- **Backflow 3, one half:** the otel-sentry (the model-provenance watchdog daemon,
  `design/FABLE-OTEL-SENTRY-SPEC.md`) honestly reporting the session UNWATCHED — its
  journal status for "no coverage claimed" — and the PREPARED-only v1 scope were
  documented, ratified design; the *un*-designed part (config file never
  scaffolded; no end-of-run feature verification) is in Track 2.4.
- **One minor residue from the previous review cycle** (ledger row 1844's finding F4:
  the textual shell's 10-second bridge timeout can misread sustained load as
  shutdown) stands banked as noted-not-actionable, unchanged by this pass.

## 4. Sequencing and dispatch posture

1. Track 3 first (small, independent, immediately witnessable; backflow 1 leads on
   severity), then Track 2.3/2.4 (flow correctness), then 2.1/2.2 (the content/UI
   restructure — largest, and it wants the ADR-0012 amendment ratified first so the
   extraction lands under law, not ahead of it), then 2.5 (navigation, after its spec).
2. Track 1's amendments are Fable-authored; scheduling honors the Fable-availability
   constraint on record. The P9-lift consult (row 1826) and the data-is-not-code
   amendment can share a session; ADR-0018 governs both briefs.
3. Every builder brief carries the standing rules: verbatim commission seeds, worktree
   isolation or serial dispatch on overlapping surfaces, report with witness marks,
   post-merge live re-witness from the main checkout (the practice row 1841 ratified).
4. The textual live legs (real terminal, real pinentry) remain the maintainer's witness
   path; Track 3's d/f fixes should be on that same live pass.

## 5. Witness plan

Each track closes only on witnessed evidence: Track 3 items get red-then-green fixtures
where a fixture can express the defect (f and backflow 1/5/7a/8 can; d needs the live
terminal leg); Track 2 items land under the existing scripted-smoke + dry-run-parity
harness plus new fixtures per class; the ADR-0007 gate ships with a negative self-check
(an over-limit synthetic file must go red). Umbrella claims are refused per the
standing contract — per-item WITNESSED / REFUSED-AS-EXPECTED / UNEXERCISED with the
blocker named.
