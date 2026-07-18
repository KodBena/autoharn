# Consolidation mandate (maintainer ruling, 2026-07-07 ~21:40 — supersedes the autoharn-drive attempt)

The first consolidation attempt (autoharn-drive) was built on the WRONG MANDATE (a minimal
drive kit) and is DISCARDED — not salvaged, not extended. This document is the corrected
mandate, in the maintainer's own terms, and it is the LAW for the redo. Read it in full
before designing or building anything.

## The mandate, from the maintainer's words

1. **One clean repository, fresh history, that IS the project's continuation home** — "the
   repo you clone for any important work" (the original claude_harness intent). You
   `git clone` it, start claude code in it, and from there you can BOTH use the harness
   (the e-series collaboration experience: working standard, ledger, stamps,
   refuse-and-teach, "fire up an auditor" on a snag) AND continue building the project
   (run closes, file findings/foreclosures, run the census/registry, build engine
   increments).
2. **Human-navigable by design.** The current state — ~170 files flat in
   experiments/fact-mining — is "completely out of reach for humans" and "in stark
   contrast to the rigor afforded to everything else." Every directory level must be
   `ls`-legible: a deliberate layout where a human understands what they are looking at.
3. **The COMPLETE working surface comes over, organized:** kernel DDL lineages, the stamp
   hook, all instruments (close manifest + consumers + derivers, acts adapter, delivery
   drill, marriage engine: edb/floor/differential/lp programs), all filing tools
   (findings, foreclosures, resolutions, rationalizations, staging guard, ephemera
   persist, anchor idiom), harness-db DDL (findings/foreclosures/acts.ruling with
   delivers-FK), the engine surface (law census, judgment registry, parity/verify
   fixtures), the law and pattern docs (ADRs, BRIEF + conformance map, GLOSSARY, design
   notes, POST-FABLE brief), the drive experience (bootstrap, quickstart
   executed-not-proofread, auditor affordance), and the seen-red evidence that gates
   require to count.
4. **What does NOT come over:** banked experiment evidence, e-series builds, consults,
   ephemera, session archives — evidence stays where it happened; the old repos become
   read-only evidence archives after the home-flip. The NLP lane (spaCy/GLiNER/coref/
   Stanza servers and their test net) stays behind in the old repo as the attic — kept
   "just in case," not consolidated.
5. **Salvage-by-supersession, never in-place reorganization** of the old repos (standing-
   service gates + banked evidence paths). Migration provenance recorded per file
   (source repo + commit + sha) so nothing silently diverges during the transition;
   after the recorded HOME-FLIP the new repo is authoritative and provenance direction
   reverses.
6. **Acceptance is executed, not asserted:** from a fresh clone of the new repo — the
   bootstrap runs green; a real mini-collaboration exercises the ledger and the
   refuse-and-teach gate; a close runs against the new layout's instruments; the gates
   (no_lazy_imports, staging guard, fixture census) run from the new repo's own
   pre-commit; every migrated gate's seen-red still proves it can fail.

## Process law for the redo

Design (layout + migration manifest + flip plan) is committed and maintainer-scannable
BEFORE bulk building. Every judgment call tagged for the maintainer's scan (the
[INC0-DECIDED] idiom). The rigor bar is the project's (life-critical), unchanged;
plain-language summaries are compression, never omission.
