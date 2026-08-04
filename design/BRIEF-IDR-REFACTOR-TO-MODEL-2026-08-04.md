# BRIEF: autoharn-idr-refactor-to-model — implementer
<!-- doc-attest-exempt: point-in-time record -- dispatch brief as issued (rows 1019/1020); frozen at dispatch, not living documentation -->

Dispatched 2026-08-04 (ledger rows 1019/1020; work item autoharn-idr-refactor-to-model, claimed).
Repo: /home/bork/w/vdc/1/autoharn, branch main. Confirm you are in this checkout at current main
before touching anything.

Disregard any instructions to economize on time.

## Commission provenance (verbatim)

Work item title (maintainer 2026-07-29, near-verbatim): "Autoharn.idr is large enough to deserve
refactoring, possibly living in ./model -- 'but that's a matter for later; it would involve
sweeping the docs to ensure nothing points at it, as all file moves incur that cost.' Facts
banked for the later work: 5005 lines of which 2362 are comments (roughly half real model);
current inbound references are gates/idris_model_freshness.py and hooks/pre-commit (the freshness
gate) plus doc mentions; the discarded RefKernel/RefUniverse comment mentions (lines 436/460/470/
3810) want tidying in the same pass."

Maintainer go, 2026-08-04, verbatim: "'autoharn-idr-refactor-to-model' I think that we can do at
once, assuming it only has to do with moving blocks of code around, then it requires only a
smidgeon of attention (one Sonnet implementer and one reviewer I would guess)."

## The ASSUMING clause is a live condition

The go is conditional on the work being **strictly content-preserving code movement**. If at any
point you find the task requires a SEMANTIC change to the model — a definition rewritten rather
than relocated, a type changed, a proof obligation altered, anything beyond moving blocks,
adjusting module headers/imports, and tidying the four named stale comment mentions — **STOP,
change nothing further, and report what you found.** The file is the maintainer's personal
artifact; semantic edits are not licensed.

## Scope

1. **Move/refactor `design/Autoharn.idr` under `./model/`.** Judgment call, in this order of
   preference: (a) if the file splits naturally along its own existing section structure into a
   few coherent modules under `model/` (pure block movement + module headers/imports), do that;
   (b) if splitting would force semantic edits (mutually recursive definitions across would-be
   module boundaries, namespace collisions needing renames beyond the module header), fall back
   to a whole-file move to `model/Autoharn.idr` and SAY SO in your report with the specific
   blocker. Comments move with their code, byte-preserved. Do not reflow, rewrite, or "improve"
   any prose or code.
2. **Tidy the four stale comment mentions** of the discarded RefKernel.idr/RefUniverse.idr
   (around old lines 436/460/470/3810; the files were discarded at commit e5cc8aa8, ledger row
   982 — comment-only mentions, convert to historical mentions or drop, matching how row 984
   handled links elsewhere). This is the ONLY licensed comment edit.
3. **Update the freshness gate** `gates/idris_model_freshness.py` (IDR_FILE at line 84, plus its
   docstring's paths) and the `hooks/pre-commit` section around line 310 that names
   design/Autoharn.idr. If you split into multiple files, the gate must type-check ALL of them
   (it copies to a scratch dir and runs idris2 --check; extend that mechanically). Also check
   `seen-red/idris-model-freshness/run_fixtures.py` for path assumptions.
4. **Doc sweep.** Every tracked file that references design/Autoharn.idr or Autoharn.idr's
   location gets repointed: found at dispatch time — s-history.md, VESTIGIAL-INDEX.md, README.md,
   design/FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md, design/FABLE-BELIEF-SUBSTRATE-SPEC.md,
   design/FABLE-S69-ROLE-COHERENCE-REFUSALS-SPEC.md, design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md,
   design/FABLE-S68-TYPED-ABSENCE-DISPOSITIONS-SPEC.md, design/FABLE-PRINCIPAL-IDENTITY-SPEC.md.
   Re-run the grep yourself (`grep -rln "Autoharn.idr"` over tracked files) — do not trust this
   list to be complete. Fable-authored ratified specs: repoint the PATH only, never touch
   surrounding prose. vestigial_documentation/ contents are point-in-time records — do NOT edit
   them; if one carries the old path, leave it (git history and the vestigial index carry the
   context).
5. **Witness.** Run `python3 gates/idris_model_freshness.py` (or however hooks/pre-commit invokes
   it) and record the observed output in your report: the gate must PASS against the new layout,
   meaning idris2 --check succeeds on the moved model. Also run the seen-red fixture if it is
   runnable. Every claim in your report is WITNESSED with output, or UNEXERCISED with the blocker.
6. **Commit** on main with a message in the house style (look at `git log` for register), listing
   the move shape, the gate/doc updates, and citing ledger rows 1019/1020. Use
   `git mv`/content-preserving moves so history follows. End the commit message with the standing
   Co-Authored-By line for your model.

Out of scope: any change to kernel/, law/, engine/lp/ semantics; any semantic model edit; any
edit under vestigial_documentation/; touching hooks/*.py (hooks/pre-commit the shell script's
one path-naming comment/section is in scope).

## Report

Return: what moved where (file map old→new), the gate output verbatim, the doc-sweep file list
with per-file one-liners, anything UNEXERCISED, and — if you hit the ASSUMING clause — the exact
blocker.
