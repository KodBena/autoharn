#!/usr/bin/env python3
"""tools/configtree/filter_threshold.py -- ONE home for the filter-above-threshold numeric bar
`MultiChoiceFieldWidget` (checkbox catalogs, ledger row 1130's own sibling audit) and
`ChoiceFieldWidget` (RadioSet pickers, cycle-2 AUDIT.md finding #3: "a growing principal roster
renders as an ever-longer unfiltered RadioSet, unlike MultiChoiceField's own filter") BOTH share --
a single number, previously only `widgets.MULTICHOICE_FILTER_THRESHOLD`, now split out so a second
field kind can reuse the SAME constant instead of re-deriving/duplicating it (ADR-0012 P1).

Miller (1968)/Nielsen's own working-set heuristic puts a single glanceable list at roughly 7 (+-2)
items (the SAME pedigree ADR-0019's C7/C28 already cite) -- past that, a catalog stops being a
single glance and becomes a search task, the point at which a filter earns its own keep (VS Code
settings search / Group Policy editor idiom: the filter Input appears only once the list is long
enough to need one, never above a short list where it would be one more control for nothing)."""
from __future__ import annotations

FILTER_THRESHOLD = 9
