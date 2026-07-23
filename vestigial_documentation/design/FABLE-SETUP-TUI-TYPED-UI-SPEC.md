# FABLE-SETUP-TUI-TYPED-UI-SPEC — typed UI content vocabulary (Track 2.1 + 2.2)

<!-- doc-attest-exempt: commissioned build basis, frozen 2026-07-22 (field strategy Track
2.1/2.2, already maintainer-read; obs a+b are his verbatim commission). Construction reads
from this file as-frozen; the ADR-0017 A:B:C prose-polish runs separately against a live
edition per the FABLE-PRINCIPAL-IDENTITY-SPEC / FABLE-BELIEF-SUBSTRATE-SPEC build-basis
precedent. Removal condition: strike when the polished live edition supersedes this. -->

- **Status:** Commissioned build basis (Fable-authored 2026-07-22, under the field
  strategy the maintainer has read: `design/FABLE-SETUP-TUI-FIELD-STRATEGY.md` Track
  2.1/2.2, closing observations **a** and **b** and carrying the F4/obs-h diagnostic
  leg from ledger row 1917).
- **Law read before authoring:** ADR-0000, ADR-0002, ADR-0007, ADR-0012 (P1, P2, P10).
- **Commission seeds, verbatim (the maintainer's observations this spec closes):**

```
a. walls of text make reading super-hard; should have a limit on sub-element text width
   and clearly deliminate distinct semantic elements (e.g. column headers etc)
b. file size violation; factor out the configuration content from code #governance
   1. (ADR-0012 extension: data is not code; factor out the prompts)
```

## 1. The foreclosing type: a closed element vocabulary

New module `tools/setup_tui/elements.py`: a closed set of frozen dataclasses. Every
piece of content the wizard shows an operator is exactly one of:

- `Heading(text, level: int = 1)` — section/banner. Replaces `Ui.banner`.
- `Paragraph(text)` — running prose. Renderers wrap it to the measure (§2); a
  paragraph may never be emitted pre-wrapped with embedded newlines doing layout work.
- `Table(headers: tuple[str, ...], rows: tuple[tuple[str, ...], ...], caption: str | None = None)`
  — real columns, aligned by the renderer, headers visually distinct.
- `StatusLine(label, status, detail: str | None = None)` — one checklist/progress row;
  `status` stays the existing checklist vocabulary (INSTRUCTED / PREPARED /
  VERIFIED_UP / NOT_UP / WITNESSED / REFUSED / SKIPPED / DRY-SKIPPED), never free text.
- `Note(text, tone: Literal["info", "warn", "refusal"])` — tone maps onto ADR-0002's
  loudness hierarchy; `refusal` renders unmissably in every backend.
- `Rule()` — a separator. The only element with no content.

`Ui.say(str)` and `Ui.banner(str)` are **removed**, replaced by `Ui.emit(element)`.
No compatibility shim: a shim would let the old `str` register persist indefinitely
(the same silent-fallback class the field strategy condemns). All call sites convert
in this build.

**Closure statement.** Quantified over: every stdout/transcript emission in
`tools/setup_tui/*.py` (the module glob at the commit that lands this spec, excluding
`ui.py`/`ui_textual.py` render internals and `runner.py` subprocess passthrough of
child output). Every such emission is constructed as one of the six element types
above and reaches the operator only via `Ui.emit`. Enforced mechanically: the purity
gate (`gates/setup_tui_purity_gate.py`) gains a check that no module in the glob
except the two renderer files calls `print(` or `.say(`; an unknown element type
passed to `emit` raises a typed error (negative control: the fixture proves it).

## 2. Renderers (the two backends, one canonical text form)

- **One canonical text renderer** (P1: one home): a pure function
  `render_text(element) -> list[str]` in `elements.py` (or a sibling `render_text.py`
  if size demands), used verbatim by the plain/scripted backend AND by the Textual
  transcript pane's `$ `-prefixed lines — the existing text-parity property of
  `ui.py`'s docstring is preserved by construction, not by duplication.
- **Measure:** 78 columns for prose (`Paragraph`, `Note`), matching the existing
  banner width. `textwrap` with hanging indents for `StatusLine.detail`. `Table`
  columns are width-fitted with a per-column cap; a cell over cap wraps within its
  column rather than blowing out the row.
- **Textual backend:** `Heading` → styled static, `Table` → the existing `DataTable`
  precedent (the field strategy names it the one good precedent), `Note(refusal)` →
  the loud style already used for refusals. The Textual renderer may style beyond
  the canonical text form but never add or drop content relative to it.

## 3. Content becomes data (extraction phase 2, through the types)

- New package `tools/setup_tui/content/` — data modules only (P10), one per screen
  (`content/screen_<name>.py`), each exporting keyed content: dict of slot-key →
  element or tuple of elements. Authored copy is edited as writing there; logic in
  `screens.py` references keys and interpolates runtime values via explicit
  `format`-style fields, never by rebuilding prose inline.
- `screens.py`'s interleaved copy migrates slot by slot. Literal strings remaining in
  logic modules after this build: only identifiers, format keys, refusal-condition
  one-liners under ~2 lines, and log strings. The three already-extracted data
  modules (`feature_facts_data.py` etc.) move under `content/` unchanged in content
  (byte-identical values, AST-verified, same discipline as phase 1).
- ADR-0007 effect: `screens.py` must exit the `gates/max_lines.py` BASELINE table or
  ratchet materially downward; the build states the before/after line counts in its
  report. New `content/` modules are data and enter the gate's baseline honestly if
  over the ceiling (data files: the gate's existing posture governs; do not golf copy
  to fit a code ceiling).

## 4. The F4 / observation-h diagnostic leg (ledger rows 1844-F4, 1917)

The maintainer's evidence: the wizard "works in CLI, breaks in textual" on the
rehearsal test. Prime suspect on record: the textual shell's 10-second bridge timeout
can misread sustained load as shutdown (F4). This build carries the diagnostic:

- A headless fixture drives the Textual bridge (the same worker-thread bridge the
  real backend uses, no live terminal needed) through a sustained, rehearsal-length
  synthetic load — a screen act that emits steadily for well over 10 seconds, and one
  that is *silent* (computing) for well over 10 seconds. Reproduce or exonerate: if
  the bridge kills or misreads either leg, that is the crash mechanism — fix by
  keying the timeout to liveness (the worker making progress) rather than wall-clock
  silence, red-then-green. If both legs survive, record the exoneration with the
  observed timings; obs-h then genuinely needs the maintainer's repro and says so.

## 5. Witness plan

- Existing harnesses stay green: `seen-red/setup-tui-scripted-smoke` (13 cases,
  answers-file line counts unchanged — element conversion must not add prompts),
  dry-run parity, all four gates.
- New fixture `seen-red/setup-tui-typed-elements/`: (i) a synthetic over-wide
  paragraph renders with no line over measure (red first against a raw-print
  stand-in); (ii) table headers/alignment; (iii) negative control — unknown element
  refused loudly; (iv) the purity-gate print/say check goes red on a planted
  violation; (v) the §4 bridge-load legs.
- Report per item WITNESSED / REFUSED-AS-EXPECTED / UNEXERCISED with blocker named;
  the live-terminal look of the Textual styling remains the maintainer's witness leg.
