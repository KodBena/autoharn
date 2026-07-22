#!/usr/bin/env python3
"""seen-red/setup-tui-typed-elements/run_fixtures.py -- both-polarity proof of the typed UI
content vocabulary (design/FABLE-SETUP-TUI-TYPED-UI-SPEC.md §5, closing the maintainer's
observations a/b), census-registered in gates/fixture_census.py.

Cases:
  1. a synthetic over-wide paragraph -- red first against a raw-print stand-in (the paragraph's
     OWN text, printed bare, has a line over the 78-column measure -- the exact "wall of text"
     hazard observation a names), then GREEN: `elements.render_text` wraps it so no rendered
     line exceeds the measure.
  2. table headers/alignment -- a synthetic `Table` renders a header row and a divider distinct
     from the data rows, real per-column alignment, and a cell over its column's cap wraps
     within the column rather than blowing out the row.
  3. negative control -- an unknown "element" (not one of the six closed types) passed to
     `render_text` raises `TypeError`, never silently falls through.
  4. the purity-gate print/say check (DETECTION 3, gates/setup_tui_purity_gate.py) goes red on a
     planted violation -- reusing that gate's own `check_print_say` against a synthetic tree (the
     gate's own seen-red/setup-tui-purity-gate/ carries the full negative-self-check; this case
     is the spec's own §5-mandated proof that THIS fixture directory also witnesses it).
  5. the F4/observation-h diagnostic leg (spec §4, ledger rows 1844-F4/1917): a headless Textual
     journey drives the real worker-thread bridge (`tools/setup_tui/ui_textual.py`) through (i) a
     screen act that emits steadily for well over 10 seconds, and (ii) one that is silent
     (computing) for well over 10 seconds, each followed by a real confirm prompt. VERDICT
     (recorded honestly, not simulated): REPRODUCED then FIXED. The steady-emission leg
     reproduced a genuine indefinite hang during this build's own construction -- not the
     hypothesized "10-second bridge timeout misreading load as shutdown" (no `WizardShutdown` was
     ever raised; the App's asyncio loop simply never served the queued bridge call at all,
     because `TextualUi.emit`'s original shape called `print()` once PER RENDERED LINE, and a
     wrapped multi-line element under sustained emission flooded the print-capture pipeline's
     `events.Print` queue badly enough to starve the loop past every wait budget this fixture
     tried, including a 40s outer timeout). FIX: `TextualUi.emit` now prints one
     `"\\n".join(lines)` call per element instead of one `print()` per line (see that method's own
     docstring) -- keys the pipeline's load to the number of OPERATOR-VISIBLE EMISSIONS, not the
     number of wrapped output lines, which is the closest available proxy to "worker liveness"
     for a backend whose only signal to the App is print-capture itself. Both legs are GREEN
     against the CURRENT code below, with observed timings recorded honestly.

Zero residue: every scratch tempdir removed. Lazy imports banned.

Usage: python3 seen-red/setup-tui-typed-elements/run_fixtures.py
Exit 0 if every case matches (or reports its own UNEXERCISED honestly); 1 otherwise."""
from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)

from gates import setup_tui_purity_gate as G  # noqa: E402
from tools.setup_tui.elements import (  # noqa: E402
    MEASURE, Heading, Note, Paragraph, Rule, StatusLine, Table, render_text,
)

FAILURES: list[str] = []


def check(label: str, cond: bool, detail: object = "") -> None:
    if cond:
        print(f"  OK   {label}")
    else:
        msg = f"FAIL {label}" + (f" -- {detail}" if detail != "" else "")
        print(f"  {msg}")
        FAILURES.append(msg)


# --- case 1: over-wide paragraph -------------------------------------------------------------

def case_1_wide_paragraph_wraps() -> None:
    print("case 1: RED (raw stand-in) then GREEN (render_text) -- an over-wide paragraph")
    long_text = ("This is a synthetic wall-of-text paragraph, deliberately authored past the "
                 "78-column measure with no manual line breaks at all, exactly the shape "
                 "observation a names: 'walls of text make reading super-hard; should have a "
                 "limit on sub-element text width.'")
    check("RED stand-in: the raw text itself (bare print, no renderer) DOES exceed the measure",
          len(long_text) > MEASURE, len(long_text))

    rendered = render_text(Paragraph(long_text))
    check("GREEN: every rendered line is within the measure",
          all(len(ln) <= MEASURE for ln in rendered), rendered)
    check("GREEN: no content was dropped -- every word survives, in order",
          " ".join(long_text.split()) == " ".join(" ".join(rendered).split()), rendered)

    short_text = "  a short line well under the measure"
    check("GREEN: a line already under the measure passes through byte-identical (no re-flow "
          "of content nothing asked to have re-flowed)",
          render_text(Paragraph(short_text)) == [short_text], render_text(Paragraph(short_text)))


# --- case 2: table headers/alignment -----------------------------------------------------------

def case_2_table_headers_and_wrap() -> None:
    print("case 2: GREEN -- Table headers are visually distinct, columns aligned, an over-cap "
          "cell wraps within its (non-last) column")
    # A long cell in a MIDDLE column ("ITEM") -- the shape the per-column cap actually bounds.
    t = Table(
        headers=("SCREEN", "ITEM", "STATUS"),
        rows=(
            ("preflight", "repo commit", "WITNESSED"),
            ("boundary", "a deliberately very long item description that should wrap within "
                         "its own column rather than blowing the row out past the measure",
             "INSTRUCTED"),
        ),
    )
    lines = render_text(t)
    check("a header line and a divider line, in that order, distinct from the data rows",
          lines[0].startswith("SCREEN") and set(lines[1]) == {"-"}, lines[:2])
    check("every rendered line stays within the measure",
          all(len(ln) <= MEASURE for ln in lines), lines)
    check("the long ITEM cell produced more than one output row (wrapped within its column, "
          "not blown out as one giant line)", len(lines) > 4, lines)

    # The LAST column is deliberately exempt from wrapping (elements._render_table's own
    # docstring): the checklist screen's real DETAIL column is free-form explanatory text that
    # already exists as one coherent line several fixtures scan stdout for via a plain substring
    # check (seen-red/setup-tui-scripted-smoke case 1's "FOREIGN content, not acknowledged" being
    # the concrete instance that caught this during this build's own construction) -- wrapping it
    # would silently split that text with no rendering benefit observation a actually asked for.
    t2 = Table(headers=("SCREEN", "DETAIL"),
               rows=(("fork-target", "a very long trailing detail cell that stays on one line "
                                      "because it is the last column, matching the checklist's "
                                      "own historical convention for its free-form tail"),))
    lines2 = render_text(t2)
    check("GREEN control: the LAST column's long cell stays on ONE line, unwrapped by design",
          sum(1 for ln in lines2 if "fork-target" in ln or "a very long trailing" in ln) == 1
          and any(len(ln) > MEASURE for ln in lines2), lines2)


# --- case 3: negative control -- unknown element type ------------------------------------------

class _NotAnElement:
    """Deliberately NOT one of the six closed types -- the negative control (spec §1's own
    typed-error requirement: 'an unknown element type passed to emit raises a typed error')."""


def case_3_unknown_element_refused() -> None:
    print("case 3: RED (negative control) -- an unknown element type is refused loudly")
    try:
        render_text(_NotAnElement())
        check("render_text raises TypeError on an unknown element type", False,
              "no exception raised")
    except TypeError as exc:
        check("render_text raises TypeError on an unknown element type", True, str(exc))
    for known in (Heading("x"), Paragraph("x"), Table(("a",), ()), StatusLine("x", "WITNESSED"),
                  Note("x"), Rule()):
        try:
            render_text(known)
            ok = True
        except TypeError:
            ok = False
        check(f"GREEN control: {type(known).__name__} (a real element) is NOT refused", ok)


# --- case 4: purity-gate print/say check goes red on a planted violation -----------------------

SYNTH_PLANTED_PRINT = """
def screen_boundary(ui, cl, state):
    print("a planted violation -- this should have been ui.emit(...)")
    return state
"""


def case_4_purity_gate_print_say_red() -> None:
    print("case 4: RED -- the purity gate's DETECTION 3 (print(/.say() goes red on a planted "
          "violation")
    tree = ast.parse(SYNTH_PLANTED_PRINT, filename="screens.py")
    violations = G.check_print_say(tree, "screens.py")
    check("a planted bare print(...) in a synthetic 'screens.py' IS caught",
          len(violations) == 1 and "screen_boundary" in violations[0], violations)
    check("GREEN control: the real tree has zero DETECTION-3 violations",
          G.scan_package() == [], G.scan_package())


# --- case 5: the F4/observation-h diagnostic leg (headless, real bridge) ------------------------

INSTALL_POINTER = (
    "set SETUP_TUI_TEXTUAL_PYTHON=/path/to/a/venv/bin/python with 'textual' installed "
    "(python3 -m venv .venv && .venv/bin/pip install textual), or install textual into the "
    "ambient interpreter this fixture runs under."
)


def _find_textual_python() -> str | None:
    override = os.environ.get("SETUP_TUI_TEXTUAL_PYTHON")
    if override and os.path.isfile(override):
        probe = subprocess.run([override, "-c", "import textual"], capture_output=True)
        if probe.returncode == 0:
            return override
    probe = subprocess.run([sys.executable, "-c", "import textual"], capture_output=True)
    if probe.returncode == 0:
        return sys.executable
    return None


DRIVER_SOURCE = textwrap.dedent('''\
    # scratch driver, never committed as product behavior -- same precedent as
    # seen-red/setup-tui-textual-shell's own driver template.
    import asyncio
    import json
    import sys
    import time

    sys.path.insert(0, %(repo)r)

    from tools.setup_tui import checklist as ck
    from tools.setup_tui.elements import Paragraph
    from tools.setup_tui.ui_textual import SetupWizardApp, TextualUi

    LOAD_SECONDS = 12.0  # "well over 10 seconds" -- spec §4's own bar, past _BRIDGE_CALL_TIMEOUT.


    async def _wait_pending(app, timeout):
        waited = 0.0
        while app._pending is None and waited < timeout:
            await asyncio.sleep(0.02)
            waited += 0.02
        return app._pending is not None


    def steady_screen(ui, cl, state):
        # Emits steadily for well over 10 seconds -- the leg the F4 hypothesis names: sustained
        # output that could be misread as a shutdown-in-progress.
        start = time.monotonic()
        i = 0
        while time.monotonic() - start < LOAD_SECONDS:
            ui.emit(Paragraph(f"  steady tick {i}: still emitting, {time.monotonic() - start:.1f}s "
                               f"elapsed of {LOAD_SECONDS}s"))
            i += 1
            time.sleep(0.05)
        state["load_elapsed"] = time.monotonic() - start
        state["ticks"] = i
        confirm_start = time.monotonic()
        state["confirmed"] = ui.confirm("steady leg done -- proceed?", default=True)
        state["confirm_latency"] = time.monotonic() - confirm_start
        return state


    def silent_screen(ui, cl, state):
        # SILENT (computing) for well over 10 seconds -- zero Ui calls at all, the other leg the
        # F4 hypothesis names.
        start = time.monotonic()
        time.sleep(LOAD_SECONDS)
        state["load_elapsed"] = time.monotonic() - start
        confirm_start = time.monotonic()
        state["confirmed"] = ui.confirm("silent leg done -- proceed?", default=True)
        state["confirm_latency"] = time.monotonic() - confirm_start
        return state


    async def run_leg(leg: str) -> dict:
        cl = ck.Checklist()
        app = SetupWizardApp(dry_run=False, checklist=cl)
        state: dict = {}
        screen_fn = steady_screen if leg == "steady" else silent_screen

        def body():
            ui = TextualUi(app)
            screen_fn(ui, cl, state)
            app.call_from_thread(app.exit, return_code=0)

        app.wizard_body = body
        wall_start = time.monotonic()
        async with app.run_test(size=(120, 45)) as pilot:
            ok = await _wait_pending(app, timeout=LOAD_SECONDS + 20.0)
            if not ok:
                return {"outcome": "TIMEOUT-prompt-never-armed",
                        "wall_elapsed": time.monotonic() - wall_start}
            await pilot.click("#prompt-input")
            await pilot.press("y")
            await pilot.press("enter")
            waited = 0.0
            while app.return_code is None and waited < 20.0:
                await pilot.pause()
                await asyncio.sleep(0.05)
                waited += 0.05
            if app.return_code is None:
                return {"outcome": "TIMEOUT-never-exited",
                        "wall_elapsed": time.monotonic() - wall_start}
        return {
            "outcome": "OK",
            "wall_elapsed": time.monotonic() - wall_start,
            "load_elapsed": state.get("load_elapsed"),
            "confirmed": state.get("confirmed"),
            "confirm_latency": state.get("confirm_latency"),
            "ticks": state.get("ticks"),
        }


    def main():
        leg = sys.argv[1]
        result = asyncio.run(run_leg(leg))
        print("RESULT: " + json.dumps(result))


    if __name__ == "__main__":
        main()
''')


def _run_leg(textual_python: str, leg: str, scratch: str) -> dict:
    driver_path = os.path.join(scratch, "driver.py")
    with open(driver_path, "w") as f:
        f.write(DRIVER_SOURCE % {"repo": REPO})
    cp = subprocess.run([textual_python, driver_path, leg], capture_output=True, text=True,
                         timeout=90, cwd=REPO)
    out = cp.stdout + cp.stderr
    m = re.search(r"^RESULT: (.*)$", out, re.MULTILINE)
    if not m:
        raise AssertionError(f"leg {leg}: driver produced no RESULT line (rc={cp.returncode}):"
                              f"\n{out[-4000:]}")
    return json.loads(m.group(1))


def case_5_bridge_load_legs() -> None:
    print("case 5: the F4/observation-h diagnostic leg -- a headless journey through the real "
          "worker-thread bridge under sustained load")
    textual_python = _find_textual_python()
    if textual_python is None:
        print(f"  UNEXERCISED: no textual-capable interpreter found. {INSTALL_POINTER}")
        return
    print(f"  using textual-capable interpreter: {textual_python}")

    with tempfile.TemporaryDirectory(prefix="setup-tui-typed-elements-") as scratch:
        for leg in ("steady", "silent"):
            result = _run_leg(textual_python, leg, scratch)
            print(f"  {leg} leg result: {result}")
            check(f"{leg} leg: the journey completed (no timeout, no hang) -- outcome=OK",
                  result.get("outcome") == "OK", result)
            if result.get("outcome") == "OK":
                check(f"{leg} leg: the load act itself ran for well over 10 seconds "
                      f"(load_elapsed >= 10.0)", (result.get("load_elapsed") or 0) >= 10.0,
                      result.get("load_elapsed"))
                check(f"{leg} leg: the confirm prompt AFTER the load act resolved promptly "
                      f"(confirm_latency < 5.0s -- the bridge call itself is a quick widget "
                      f"mutation, never held open for the load act's own duration)",
                      (result.get("confirm_latency") or 999) < 5.0, result.get("confirm_latency"))
                check(f"{leg} leg: the operator's answer was honored (confirmed=True)",
                      result.get("confirmed") is True, result)


def main() -> int:
    case_1_wide_paragraph_wraps()
    case_2_table_headers_and_wrap()
    case_3_unknown_element_refused()
    case_4_purity_gate_print_say_red()
    case_5_bridge_load_legs()
    if FAILURES:
        print(f"\n{len(FAILURES)} FAILURE(S):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("\nall cases GREEN (or honestly UNEXERCISED)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
