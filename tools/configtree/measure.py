#!/usr/bin/env python3
"""tools/configtree/measure.py -- the ONE readable-prose-measure constant this library enforces
everywhere prose can render (maintainer round 4, 2026-07-22): "unbounded text measure -- prose
width bound to terminal width instead of to a readable measure", found live in the principals-
registration modal (a field label measured 394/613 characters, rendered as one unwrapped-feeling
line stretching the full width of a wide terminal). The bug's CLASS, not just that instance: any
Textual `Static`/`Label` mounted inside a container that stretches to its parent's width will
wrap its text at THAT width, not at a readable one -- on a very wide terminal (measured
empirically: a bare `Static` in a 400-column test harness renders its content as ONE line, height
1, width 400) this makes an ordinary sentence-length label read as a wall of text.

`MEASURE = 78` matches the deleted `tools/setup_tui/elements.py`'s own historical convention
(`MEASURE = 78`, itself matching the even older `"=" * 78` rule `Ui.banner`/`Heading` used) --
the same number, not a coincidence: `textwrap`'s own suggested default and a measure comfortably
inside the classic 80-column terminal, keeping every prose line readable regardless of how wide
the actual terminal is. Every Static-rendered prose class in `tools.configtree.app`'s CSS caps
its own `max-width` at this ONE constant (verified empirically: a `Static` given `max-width: 78`
in CSS wraps a 400-character string into 6 lines of <=78 columns each, instead of one 400-column
line) -- there is exactly one number to change if this measure is ever revisited."""
from __future__ import annotations

MEASURE = 78
