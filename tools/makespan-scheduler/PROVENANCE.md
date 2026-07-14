# PROVENANCE — this directory is a vendored copy, not an autoharn-authored tool

This directory (`tools/makespan-scheduler/`) is a **verbatim vendor** of an external side
project, brought in whole per maintainer directive (2026-07-14, dictated pre-sleep; ledger
work item `makespan-scheduler-vendoring`). The maintainer created the source project
separately and asked that it be vendored into autoharn and recommended as a standing practice
for large-scale agentic workflows — see the standing recommendation in
[design/USER-RECIPES-FAQ.md](../../design/USER-RECIPES-FAQ.md) ("Workflow patterns") and the
guarantee-formalization design note,
[design/ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md](../../design/ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md).

- **Source repository:** `/home/bork/w/vdc/1/makespan-scheduler` (a local sibling project;
  not published elsewhere at the time of vendoring).
- **Source commit:** `bd03c8d3c8e46c5281480992be30dcf9ff6668b5` (`master`, working tree clean
  at copy time).
- **Vendored:** 2026-07-14.
- **What was copied:** every tracked file except `.git/` itself — `README.md`,
  `requirements.txt`, `scheduler.py`, `.gitignore`, `makespan_scheduler/__init__.py`,
  `makespan_scheduler/model.py`, `tests/test_scheduler.py` — copied byte-for-byte (verified
  by `diff -q` against the source at copy time; no content edited).
- **What was NOT copied:** build/cache artifacts present in the source working tree at copy
  time (`__pycache__/`, `.pytest_cache/`) — neither is source, both are already covered by
  this vendored copy's own `.gitignore`.

## The read-only-source rule ([ADR-0004](../../law/adr/0004-minimal-touch-edits-to-partially-visible-files.md) / this commission's own constraint)

The source repository above is **read-only material for this vendoring** — it is never
edited as a side effect of work on the vendored copy, per this task's own commission. A fix,
improvement, or upstream change to the scheduler happens in the source repository first (the
maintainer's own project) and is **re-vendored** here as a fresh copy (repeat this
provenance record with the new source commit), never patched independently in place — this
directory is not a fork with its own diverging history, it is a snapshot. If autoharn ever
needs a change the upstream source does not have, that need is filed as an entry in this
repository's own append-only decision ledger (read via `./led` at the repository root, not a
markdown file), not silently patched into this copy — per
[ADR-0012](../../law/adr/0012-compositional-and-structural-hygiene.md) P1 (a fact has one
home; the upstream repository is that home).

## Verified at vendoring time

`~/w/vdc/venvs/generic/bin/python -m pytest tests/ -v` run from this directory: **73 passed**
(the source project's full test suite, unmodified, run in place against the vendored copy —
proves the copy is not just byte-identical but functionally live in its new home, using the
same shared venv the rest of this repository's Python tooling uses). `ortools` (the one
runtime dependency, `requirements.txt`) was already present in that shared venv; no new
environment provisioning was needed.

## License

The source project carries no `LICENSE` file of its own at the vendored commit. Not
resolved here — filed as an open question on the ledger for the maintainer
(`./led show 616` at the repository root; this repository's work tracking lives in its
append-only Postgres ledger, not in a markdown file), since this vendoring commission did
not include a licensing decision and one should not be assumed silently.
