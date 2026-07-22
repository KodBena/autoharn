# FABLE-SETUP-TUI-REBUILD-SPEC — delete the teletype, build a real Textual wizard

<!-- doc-attest-exempt: commissioned build basis, frozen 2026-07-22 (maintainer commission,
verbatim seed below). Construction reads from this file as-frozen. Removal condition: strike
when a polished live edition supersedes this. -->

- **Status:** Fable-authored 2026-07-22, maintainer-commissioned.
- **Commission, the maintainer's verbatim words:**

```
fix it. Delete everything except the non-UI logic and rebuild the TUI, textual-only,
or the --from-config. Delete it whole-sale so that nobody mistakenly implements
something that is this cursed.
```

and, asked what navigation must mean: "everything that you would expect from a TUI not
built by a 3-year-old" (all options selected: move around the screen, move between
screens, both).

## 0. The indictment this spec answers (read before designing)

The current wizard is a **teletype emulated inside Textual**: a print-stream transcript
plus one docked input field, with every prompt funneled through a bespoke Ui seam
(`ask_text`/`ask_choice`/`confirm`), a hand-rolled back-stack (`flow_position.py`), and a
hand-rolled navigation trigger (typed `<` / ctrl+b). Nothing else on screen is
focusable, scrollable, or selectable. Two full build cycles "fixed navigation" inside
that model without noticing the model IS the defect: a form wizard where you cannot move
around a form. The fix is not another affordance bolted onto the teletype; it is the
teletype's deletion.

## 1. What survives (the non-UI logic) — and only this

- `tools/setup_tui/content/` — the P10 data package (all prose/tables), unchanged.
- The decision/action layer inside `screens.py`: validation, `classify_destination`
  (the Port), the genesis-gate hard-stop, the commit executor, the boundary-service
  start/stop logic, daemon selection logic. The builder extracts these into a pure
  module (working name `tools/setup_tui/core.py` or a small package) with NO import of
  anything UI — each wizard step becomes data (its fields, defaults, validators) plus
  an apply function over `state`.
- `checklist.py` — status model only; rendering moves to the new app.
- The config seam: `--from-config` (complete-or-refuse), `--initial-config`
  (pre-loaded defaults), `world-config.toml` self-save — the whole
  FABLE-SETUP-TUI-CONFIG-FILE-SPEC contract, unchanged in behavior.
- CLI surface: `--dry-run`, `--accept-unverified-genesis`, exit codes (0/2/3/130),
  SIGTERM handling, the journal/checklist artifacts written at commit.

## 2. What is deleted wholesale — `git rm`, no shims, no deprecation period

- `ui.py` (`Ui`, `InteractiveUi`, `ScriptedUi`, `NavigableUi`, `BACK`, the trigger
  strings), `ui_textual.py` (the teletype shell), `flow_position.py` (the hand-rolled
  back-stack), `elements.py` and `render_text` (the typed-teletype vocabulary — the
  content it carried lives on in `content/`; Textual widgets render it directly).
- The `--plain` and `--scripted` modes and every answers-file under fixtures.
- Fixtures built around the deleted surfaces: `setup-tui-scripted-smoke`,
  `setup-tui-navigation`, `setup-tui-textual-shell`'s teletype-shape cases, and the
  scripted legs of every other setup-tui fixture — **removed from
  `gates/fixture_census.py` in the same commit** (a census entry pointing at a deleted
  fixture is a red gate, correctly).
- `gates/setup_tui_purity_gate.py` is REWRITTEN, not deleted: new invariant — under
  `tools/setup_tui/`, no `print(`/`input(` and no stdin/stdout access anywhere except
  (a) the Textual app package and (b) the headless `--from-config` reporter; and the
  core module imports nothing from the app package (one-way dependency, mechanical).
- Git history preserves every deleted line; nothing is archived in-tree. The point of
  wholesale deletion, per the commission, is that no future reader mistakes the
  teletype for a pattern.

## 3. What is built: an idiomatic Textual application

Interactive mode = Textual, full stop. If `textual` is not importable, the wizard
REFUSES with the install command — there is no fallback UI to maintain
(`--from-config` is the no-TUI path). Design by normal Textual idiom, not invention:

- **One Textual `Screen` per wizard step, real form widgets**: `Input` for text,
  `Select`/`RadioSet` for choices, `Checkbox`/`Switch` for booleans, `Button`s for
  Back/Next/Quit. Values live in the widgets; going Back is `pop_screen` — the
  previous form still holds its values (prior-answer memory falls out of the
  architecture instead of being simulated). `--initial-config` pre-populates widget
  values.
- **Navigation is Textual's own**: Tab/shift-Tab and arrows move focus (free, from
  `Screen`+widgets), Enter activates, PageUp/Down and mouse wheel scroll any
  scrollable container, Escape = Back binding, plus visible Footer bindings. NO
  bespoke key protocol, NO `<` trigger, and no ctrl+b (tmux prefix — witnessed
  collision). A sidebar/header shows step N of M with step names — where you are and
  where you can go.
- **Long output** (preflight results, commit transcript) renders in a scrollable,
  focusable container on the relevant screen — not a global teletype log.
- **Validation** runs on the screen's own submit; a refusal renders inline on the
  form (field-level where the validator names a field), never as a scrollback line.
- The final review screen shows the full resolved decision set (the same data
  `world-config.toml` saves) before the one commit confirmation; the genesis-gate
  hard-stop and `--dry-run` banner keep their exact semantics on this surface.

## 4. Witnessing (delete-and-replace, not port)

- **Headless-first**: `--from-config` exercises the ENTIRE core (every validator, the
  commit path, dry-run, refusals) with zero UI — `seen-red/setup-tui-config-file`
  stays the core witness, adapted to the new module layout.
- **TUI witness via Textual Pilot** (`App.run_test`), the harness the WX cases
  proved: one fixture drives the REAL screen list end-to-end — fill fields, Next
  through every screen, Back twice with value-retention asserted, arrow-select a
  choice, scroll a long output pane, Escape-back, final commit confirm under
  `--dry-run`. Red-first where a case witnesses a refusal.
- The acceptance bar for "navigation", from the commission: on the real journey,
  focus movement, scrolling, arrow selection, and back/forward across screens all
  WITNESSED in the Pilot transcript — no synthetic screen lists. A leg only a live
  terminal can witness is named UNEXERCISED with what the operator should try.

## 5. Discipline

- ADR-0007: no new file over 400 lines — the screen-per-step layout composes
  naturally; do not ratchet.
- ADR-0012 P10: content stays in `content/`; new screens import it, never inline
  prose.
- Cost: this rebuild DELETES more than it adds. No speculative features, no theming,
  no animation work, no abstraction for hypothetical third backends — the commission
  is a competent ordinary TUI, delivered once.
