# PROVENANCE — `tools/makespan-scheduler/` is a git submodule, not autoharn-authored code

This file used to live at `tools/makespan-scheduler/PROVENANCE.md`. It moved here, one
directory level up, because that path is now the working tree of an externally-owned git
submodule — autoharn does not own that tree and does not add files to it as a side effect of
housekeeping here. This file is the sibling record of the same facts.

## History

1. **2026-07-14 — vendored as a verbatim copy.** Per maintainer directive (dictated
   pre-sleep; ledger work item `makespan-scheduler-vendoring`), every tracked file of the
   maintainer's local side project at `/home/bork/w/vdc/1/makespan-scheduler` (source commit
   `bd03c8d3c8e46c5281480992be30dcf9ff6668b5`, `master`, working tree clean at copy time) was
   copied byte-for-byte into `tools/makespan-scheduler/` as a plain vendored directory (not a
   submodule). See the standing recommendation in
   [design/USER-RECIPES-FAQ.md](../design/USER-RECIPES-FAQ.md) ("Workflow patterns") and the
   guarantee-formalization design note,
   [design/ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md](../design/ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md).
   Verified at vendoring time: `~/w/vdc/venvs/generic/bin/python -m pytest tests/ -v` run from
   that directory — 73 passed, the source project's full test suite, unmodified, run in place.

2. **2026-07-15 — source published standalone; vendored copy replaced by a submodule.** Per
   maintainer directive, the source project was published as its own standalone public GitHub
   repository, **https://github.com/KodBena/makespan-scheduler**, at commit
   `f8d522b6a50f6bcd712f2d781e874761069be338` (`master` — this commit added the source
   repo's own `BACKLOG.md` recording maintainer-directed future extensions; no other change
   from the 2026-07-14 vendoring commit `bd03c8d3c8e46c5281480992be30dcf9ff6668b5`, confirmed
   by `diff -r` against the vendored copy immediately before the split, excluding
   `.git/`/`PROVENANCE.md`/`.pytest_cache`, which was empty). autoharn's
   `tools/makespan-scheduler/` was converted from a vendored copy to a **git submodule**
   pinned to that same commit, `.gitmodules` pointing at
   `https://github.com/KodBena/makespan-scheduler.git`. Going forward, an upstream change to
   the scheduler happens in that repository first and reaches autoharn by bumping the
   submodule pin (`git -C tools/makespan-scheduler fetch && git -C tools/makespan-scheduler
   checkout <new-sha>`, then commit the updated gitlink) — never by editing files inside
   `tools/makespan-scheduler/` directly, since that tree belongs to the submodule's own
   repository, not to autoharn.

## The read-only-source rule ([ADR-0004](../law/adr/0004-minimal-touch-edits-to-partially-visible-files.md) / this commission's own constraint)

The source repository is **read-only material as far as autoharn is concerned** — autoharn
never edits it as a side effect of work here. A fix, improvement, or upstream change to the
scheduler happens in `https://github.com/KodBena/makespan-scheduler` first, and reaches
autoharn by bumping the submodule pin to the new commit — never by patching
`tools/makespan-scheduler/` in place from this side. If autoharn ever needs a change the
upstream source does not have, that need is filed as an entry in this repository's own
append-only decision ledger (`./led` at the repository root, not a markdown file), not
silently patched into the submodule — per
[ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md) P1 (a fact has one home;
the upstream repository is that home).

## License

The source project carries no `LICENSE` file of its own as of the 2026-07-15 publication.
Not resolved here — this was the open question on `./led show 616` at the repository root.
Per the maintainer's 2026-07-15 ruling (recorded in that row and in a decision-ledger entry
alongside this split): the project is now its own standalone repository under the
maintainer's own GitHub account, and the license choice is the maintainer's, scoped to that
repository alone — it is no longer an autoharn open question, only a `makespan-scheduler`
open question.
