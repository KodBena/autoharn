# Setup TUI — the Textual shell: the wizard gets its real face

<!-- doc-attest-exempt: build-basis spec; attestation rides witnessed delivery -->

**Status: Fable-authored 2026-07-19, build basis. Commission: ledger row 1818
(maintainer, verbatim there). Extends [FABLE-SETUP-TUI-SPEC.md](../../design/FABLE-SETUP-TUI-SPEC.md)
— all posture rules and the `--dry-run`/out-of-sequence amendments bind unchanged —
and SUPERSEDES that spec's v1 UI-substrate clause (marked at its site). The v1 build
was conformant: the clause said "textual/urwid ONLY if already installed," the build
interpreter had neither, so only the numbered-menu fallback exists and installing
textual afterward activates nothing — there is no textual code path to activate.
That is the gap this spec closes. The prepared seam makes this a renderer swap, not
a rework: every screen already talks through `tools/setup_tui/ui.py`'s one-home `Ui`
(ADR-0012 P1 held), `feature_facts` already carries `ui_backend_textual`, and
preflight already probes for the library.**

## 1. What changes, what must not

**Unchanged, and the build fails if any of it changes:** the eleven screen functions'
flow semantics; the three `runner.py` choke points' act semantics (`run_command` /
`start_background` / `write_file`, incl. dry-run and atomicity contracts); the
checklist vocabulary; the registries; the `--scripted`, `--dry-run`, `--start-at`
contracts; `ScriptedUi` and every existing seen-red fixture, green UNMODIFIED (a
needed contract extension is a NEW fixture, census-registered — never an edit that
re-witnesses an old one into agreement). The TUI remains a driver of existing verbs;
no kernel, law, serving, hooks, or bootstrap-script edits.

**What changes:** the interactive face becomes a real Textual application. The
conversion lives at the `Ui` seam — a third backend, `TextualUi`, in a new module
`tools/setup_tui/ui_textual.py` whose top-of-file imports name `textual` honestly
(the lazy-import ban governs; no function-body imports anywhere, no allowlist).

## 2. Architecture (binding shape; mechanism choices marked as the builder's, with verification)

1. **The imperative loop survives.** `app.py`'s screen loop runs unchanged inside a
   Textual worker (thread); the App renders. Screens never learn textual exists —
   they keep calling `banner`/`say`/`ask_text`/`ask_choice`/`confirm`/`pause`.
   `TextualUi` bridges each call to the App thread-safely and blocks the worker
   until the operator answers.
2. **Layout, v1:** Header (title + the derived "N/11 Screen" ordinal — SCREEN_NUMBER
   stays the one home); a sidebar listing the eleven screens with
   pending/current/done state; a main transcript pane (RichLog-class) carrying
   EVERYTHING the flow says — banners, lesson lines, `$ argv` echoes, streamed real
   command output; a docked prompt area rendering the active ask (Input for text
   with default shown; an option list for choices, number keys still accepted; Y/n
   with stated default for confirm; a continue control for pause); Footer with key
   bindings. `--dry-run` shows a persistent banner; the closing checklist renders as
   a table. No decorative animation; the transcript is the product.
3. **Output routing.** `runner.py` and `app.py` write to bare stdout/stderr today;
   under terminal application mode those writes would corrupt the display. All of it
   must land in the transcript pane. Builder's choice of mechanism, verified not
   assumed: Textual's own print/stdout capture (verify it captures
   `sys.stdout.write` from a worker thread, not only `print`) or an explicit sink
   threaded through the choke points. Whichever: the `$ `-prefixed lines in the
   transcript must remain text-identical to the plain backend's for the same journey
   (the WDR2-style parity discipline extends to this face).
4. **Interactive children.** Any child that needs the terminal itself — the known
   case is gpg's pinentry in the signed-genesis ceremony — runs under the App's
   suspend context: the TUI yields the terminal, the child runs for real, output is
   still banked, then the App resumes. `Ui` grows a `suspend()` context manager
   (no-op in the plain and scripted backends) so screens stay backend-blind. The
   passphrase remains gpg's own interactive affair — never captured, scripted, or
   scraped by the TUI (parent ceremony spec's rule, unchanged).
5. **Cleanup guarantees survive the shell.** The SIGTERM handler, the
   KeyboardInterrupt path, and the try/finally boundary-proc termination (`app.py`'s
   `_terminate_boundary_proc` discipline) hold under the Textual face for every
   abnormal exit, including quitting the App mid-flow. A worker exception must
   surface legibly (the transcript or a plain post-exit message), never vanish into
   a blank alternate screen — a traceback the operator cannot see is hidden state.

## 3. Dependency posture and backend selection

- `textual` is a declared external cost of the SETUP TOOL's interactive face only —
  never of the harness, a born world, or the witnessing path. Update the existing
  `ui_backend_textual` feature_facts entry to the real state (in use for the
  interactive face; version recorded in the build report); the preflight probe stays
  informational.
- Selection: interactive runs get `TextualUi` when the library is importable;
  when it is not, ONE teaching line naming the exact venv/pip command, then the
  numbered-menu fallback proceeds (degraded-but-possible beats frozen). A new
  `--plain` flag forces the fallback explicitly. `--scripted` runs NEVER touch
  textual — headless witnessing must not grow a dependency.
- Import factoring must pass `gates/no_lazy_imports.py` and its spirit: `ui_textual.py`
  imports textual unconditionally at top; the selection point declares its optional
  use at module top (top-level try/except import or a selector module — whatever the
  gate and honesty both accept), never inside a function body.
- The `ui.py` docstring's transcript-parity claim is restated, not silently
  falsified: parity is of screen functions, `Ui` call sites, and transcript content
  — not of pixels.

## 4. Witnesses (WX; scratch worlds + scratch GNUPGHOME only, as ever)

- **WX1** headless Textual journey: Textual's own test harness (`run_test`/Pilot)
  drives a full pass on a scratch destination — same journey as the smoke fixture's
  full-flow case — verified by checklist content and `led` rows; teardown zero
  residue. Requires textual in the witness interpreter: when absent, the fixture
  REFUSES legibly naming the blocker (never a vacuous pass).
- **WX2** transcript parity: the `$ `-prefixed lines rendered under the Textual face
  equal the plain backend's for the same journey.
- **WX3** fallback teaching: textual-absent interpreter → one teaching line, plain
  flow proceeds; and the entire existing fixture suite green, unmodified.
- **WX4** suspend path: the ceremony's gpg acts complete under the Textual shell
  with the scratch-GNUPGHOME loopback mechanics; the suspend context's entry/exit
  observed. If the headless harness cannot host a real suspend, witness the wiring
  and mark the interactive leg UNEXERCISED with the concrete blocker — honesty over
  theater.
- **WX5** abnormal-exit cleanup under the shell: boundary proc terminated, nothing
  orphaned (extends the boundary-proc-cleanup contract as a new fixture case).
- **WX6** dry-run under the shell: zero acts (mechanical before/after), WOULD-DO
  checklist rendered.

## 5. Build conditions

Changes under `tools/setup_tui/` + `seen-red/` (new fixtures census-registered) +
the FAQ seam (the getting-started entry gains the Textual face and the venv note, or
the deferral is named). Python, top-of-file imports, all gates incl. the
interpreter-boundary lint. If textual is missing from the build interpreter, the
builder creates a scratch venv for witnessing (recording the version); if that is
impossible in the build environment, WX1/WX2/WX4/WX6 are reported UNEXERCISED with
the concrete blocker — never simulated. If Textual's harness cannot honestly witness
a leg, STOP and report (escalation shape), never work around. Per-claim witnessing;
zero residue. Single builder, worktree isolation.
