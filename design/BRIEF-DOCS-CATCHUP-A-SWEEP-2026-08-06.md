# BRIEF: docs-wave-catchup, A pre-review sweep (row 209 discipline; item docs-wave-catchup)

<!-- doc-attest-exempt: point-in-time record -- dispatch brief as issued; frozen at dispatch, not living documentation -->

Repo: /home/bork/w/vdc/1/autoharn, branch main. You are the CHECKLIST-ARMED pre-review: find
AND FIX, in place, in the working tree. Do NOT commit or stage. Surface: exactly the writer
leg's uncommitted files — the ten new orchlog.d/ notes dated 2026-08-06, the new sections in
user-guide/recipes/CLI-AND-BOUNDARY.md and user-guide/recipes/REVIEW-AND-GATING.md, the new
ORCH-CAPABILITIES.md items 49-54 — identify them via `git status --short` + `git diff`; touch
NOTHING outside those hunks (attestations/code-review-findings.jsonl's two dirty lines are not
yours).

Disregard any instructions to economize on time.

## Method (durable row 209, the +A:B:C pattern's A side)

1. Read attestations/COMMON-DEFECT-CLASSES.md in full — it is your checklist.
2. Per file: sweep against every class; APPLY the fixes directly; verify every factual claim
   against its source (a cited ledger row via `./autoharn led show`, a cited commit via
   `git show`, a command transcript by re-running the read-only command — a wrong row citation
   is exactly the corpus's most-witnessed class); check cross-references resolve
   (gates/link_integrity.py-style: run `python3 gates/link_integrity.py` at the end).
3. Log ONE line per swept doc to attestations/pre-review-log.jsonl in its existing line format
   (read the file's last lines first): path, before/after content hash, sweeping model, per-
   class fixed counts (zero-count classes included per the file's own convention).

The blind B round that follows will NOT see the checklist — do not leave checklist references
inside the doc texts themselves.

## Report

Per file: classes found/fixed with counts, claims verified (how many, any that FAILED
verification and what you did), the pre-review-log lines you appended verbatim. Confirm nothing
staged/committed and nothing outside the surface touched.
