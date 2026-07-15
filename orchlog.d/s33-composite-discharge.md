subject: 0799637

Composite work items exist (ratified spec, s33). Open a parent whose deliverable IS its
children with `./led work open <slug> "<title>" --discharge composite`: every close of
that slug is then a strict close by type (no --strict to remember), a hand-close with
unresolved children is refused, and the parent's `effective_state` in work_item_current
reads `discharged-by-obligations` BY ITSELF the moment its obligation tree resolves --
no closing act needed; it leaves the pickup queue and the stop gate's informational
line automatically. Defeat propagates: a superseded review or close re-opens the whole
ancestor chain in the same read, and a hand-closed composite whose tree was later
defeated surfaces in work_item_violations as closed_but_tree_defeated.

<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->
