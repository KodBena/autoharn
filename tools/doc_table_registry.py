#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-19T01:59:45Z
#   last-change: 2026-07-19T01:59:45Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""doc_table_registry — the CONTENT half of `tools/doc_table_generation.py`'s registry (that
module owns the mechanism: anchor location, drift check, write; this file owns the one thing
that actually varies per table — which builder produces which doc's region, per ADR-0012 P1's
"one home" split already modeled by `gates/doc_tables.py`/`tools/markdown_tables.py`: mechanism
and content kept in separate, separately-reviewable files rather than one growing module).

Each builder is a zero-argument callable returning a `tools.experiments.typed_table.Table`
(preferred — the `inhabits=` articulation for every row lives right here, at the one point a
reviewer needs it) or a pre-rendered string. `REGISTRY[table_id]["doc"]` is the REPO-ROOT-
RELATIVE path of the doc carrying the `<!-- typed-table:BEGIN id=<table_id> -->` /
`... END ...` anchor pair this table's region lives inside.

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import sys
from pathlib import Path

_EXPERIMENTS_DIR = str(Path(__file__).resolve().parent / "experiments")
if _EXPERIMENTS_DIR not in sys.path:
    sys.path.insert(0, _EXPERIMENTS_DIR)
from typed_table import Table  # noqa: E402


def user_guide_mechanism_kinds() -> Table:
    """user-guide/USER-GUIDE.md §4 ("Turning mechanisms on or off") — the two-row table
    distinguishing a FREE mechanism (no external call, on by default) from a COSTED one (one
    billed call per use, off by default). Type former: "kind of mechanism" (the header's own
    words) — the table's two rows are the two members of that closed, binary partition every
    apparatus.json mechanism falls into (BUILD-BRIEF / ORCH-AUTOMATION-ENVELOPE's own free-vs-
    costed split), so the `inhabits=` sentence for each is close to tautological — the honest,
    unglamorous case the experiment note's own ergonomics section names (an already-uniform
    table pays authoring cost for near-zero new information). Registered here as the first real,
    live-doc integration for work item `typed-table-ssot-integration` (2026-07-19); table id
    `user-guide-mechanism-kinds`.
    """
    t = Table(
        type_former="kind of mechanism",
        columns=["kind of mechanism", "default", "example"],
    )
    t.row(
        "free (no external call)",
        "on",
        "refusing an edit with no ledger entry behind it",
        inhabits="'free (no external call)' is a kind of mechanism — the partition member "
                 "whose check runs locally, costs nothing per invocation, and is therefore "
                 "shipped on by default.",
    )
    t.row(
        "costed (one billed call per use)",
        "off, and says so next to the switch",
        "reading a document for legibility with an LLM",
        inhabits="'costed (one billed call per use)' is a kind of mechanism — the partition "
                 "member whose check spends real money per invocation (an external LLM call), "
                 "and is therefore shipped off by default with that cost stated next to its "
                 "switch.",
    )
    return t


REGISTRY = {
    "user-guide-mechanism-kinds": {
        "doc": "user-guide/USER-GUIDE.md",
        "builder": user_guide_mechanism_kinds,
    },
}
