# FABLE-SETUP-TUI-NAVIGATION-SPEC — the operator's position is state, and it can move backward

This spec adds backward navigation to autoharn's setup TUI — the terminal wizard
under `tools/setup_tui/` that walks an operator through a fixed sequence of screens
to create a new autoharn deployment. Today an operator who changes their mind about
an earlier answer can only kill the wizard and start over. This document is for
whoever builds or reviews that change.

- **Status:** Proposed (Fable-authored; Track 2.5 of
  [FABLE-SETUP-TUI-FIELD-STRATEGY.md](FABLE-SETUP-TUI-FIELD-STRATEGY.md), which
  also carries the maintainer's full lettered observation list this spec's
  commission quotes from). Build deliberately LAST in the track: it
  restructures the driver loop the other Track-2 builds pass through, and it wants
  the strategy's Track 2.1 (replacing the wizard's string-only output calls with
  typed UI elements) in place first so re-rendering a revisited screen is cheap.
- **Date:** 2026-07-21
- **Commission (verbatim, maintainer observation e):** "no way to navigate back and
  forth in the TUI, so if you change your mind you have to start over"

## 1. The defect class (ADR-0000 Rule 2)

**(a) The type that is missing.** The wizard's driver, `_drive_screens`, is `for _,
fn in screens: state = fn(ui, cl, state)` — the operator's position exists only as
the loop's program counter, and a
screen's answers exist only as their side effects on one accumulating `state` dict.
Neither is a value, so neither can move backward; `--start-at` restarts the process
with empty state, and the screen copy says "go back" in two places
(`screens.py:534,984`) about a capability that has never existed. The foreclosing
type: a **cursor over the screen list** plus **per-screen answer records**, both
first-class:

```python
@dataclass(frozen=True)
class ScreenVisit:
    screen: str                  # SCREENS key
    answers: dict[str, Answer]   # every prompt this visit answered, keyed by prompt id
    facts: dict[str, object]     # the state keys this visit wrote (its footprint)

@dataclass
class FlowPosition:
    visits: list[ScreenVisit]    # completed screens, in order — the back stack
    cursor: int                  # index into SCREENS of the screen now live
```

A screen returns its `ScreenVisit` (pure data) instead of mutating `state` opaquely;
the driver derives `state` at any cursor as the fold of `visits[:cursor]` footprints.
"Go back" = truncate-and-refold: pop visits to the target, re-derive state, re-enter
the screen with its previous `answers` offered as defaults. Nothing is patched in
place; a revisit *replaces* the visit record (copy-on-write over the visit list,
ADR-0001), so downstream screens whose inputs changed are re-entered rather than
left stale — invalidation is structural, not tracked by hand.

**(b) How the lapse happened.** The flat loop was the founding shape of the wizard and every
review inherited it; the prose promising "go back" shipped because no review checks
copy against capability. Net: the fixture in §5 that greps screen copy for
navigation verbs and fails when the verb has no binding.

## 2. Semantics — decision phase only

Navigation exists **only in the decision phase**. The commit boundary is unchanged
(one commit, journal-backed, resume as built in d8a375e): once the operator confirms
the final review screen, the plan freezes and navigation ends. Going back never
un-executes anything because nothing has executed. (The pure-core restructure —
prior work, [FABLE-SETUP-TUI-PURE-CORE-SPEC.md](FABLE-SETUP-TUI-PURE-CORE-SPEC.md),
that made every screen's decision logic a pure function queueing effects for a
single later commit phase — is what makes this spec cheap: moving the cursor is
position math over those pure functions, with no effects to undo.) Interaction with
`--start-at`: subsumed but kept as the documented re-entry flag for *completed*
worlds; inside a session it becomes cursor movement.

Blocked-backward edges: none. Any completed screen is a legal target. Forward
movement past an unvisited screen stays impossible (the cursor only advances through
a completing visit). The two "go back and get X first" copy sites become actual
offers (a keybinding the copy names).

## 3. Surface

- `ui.py` / `ui_textual.py`: one new prompt affordance — every screen-level prompt
  accepts a `BACK` sentinel (plain UI: a `<` input; textual: a bound key shown in
  the footer). The `Ui` interface gains `offer_back: bool` on ask-methods; ScriptedUi
  answers files may script `<BACK>` (fixtures need it).
- `app.py`: `_drive_screens` becomes the cursor loop over `FlowPosition`; the
  banner names the binding ("^B back — revisits an earlier screen; answers you
  gave are offered again").
- Screens: mechanical migration — each `screen_*` already computes what it writes;
  the migration makes the footprint explicit in its returned `ScreenVisit`. No
  screen logic changes; screens that probe live substrate (preflight, boundary)
  re-probe on revisit by construction (they re-run).

## 4. What this spec refuses

No partial-answer editing UI (revisit re-asks the screen with defaults — simpler,
and honest about re-validation); no persistence of `FlowPosition` across process
death (the journal owns commit-phase resume; decision-phase restart is cheap by
design); no skip-forward. Each is a scope cut named here per ADR-0013 Rule 4, not a
silent absence.

## 5. Witness set

- Unit: fold/refold determinism (state at cursor N equals state from replaying
  visits 1..N); revisit-replaces-visit; downstream re-entry on changed input.
- Scripted: an answers file that walks forward to screen k, backs up to j, changes
  one answer, walks forward again — final plan reflects the changed answer and no
  stale fact (red leg: the pre-fix driver cannot express this file at all).
- Copy-vs-capability: the grep fixture from §1(b) — navigation verbs in screen copy
  must name a live binding.
- Regression: scripted-smoke, dry-run-parity, and the resume fixtures unchanged
  (navigation is decision-phase; the journal path must be byte-identical).
