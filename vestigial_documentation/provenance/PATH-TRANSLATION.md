# PATH-TRANSLATION — old-repo path prefixes → autoharn locations

Migrated documents quote paths in the old repos (`claude_harness/…`, `epistemic-operator/…`).
**Quoted evidence is never rewritten** (BUILD-BRIEF §3 risk 3): a citation inside a consult, a
brief, an ADR, or a finding keeps its original path, and the two old repos stay as read-only
archives so every cited path remains valid forever. This table lets a reader map an old-repo path
to its autoharn home when the file was MIGRATED; a path NOT listed here (banked evidence, the NLP
attic, run records) stays in the archive and is read there.

The `provenance/MIGRATION.tsv` is the authoritative per-file record (source repo + commit + sha256
+ dest); this note is the human-readable prefix summary.

| Old-repo prefix | autoharn home | Notes |
|---|---|---|
| `claude_harness/docs/adr/` | `law/adr/` | the ADR corpus 0000–0016, verbatim |
| `claude_harness/docs/adr-evidence/seen-red/` | `seen-red/` | both-polarity gate proofs |
| `claude_harness/docs/design-notes/` | `design/` | design & pattern notes |
| `claude_harness/docs/research/2026-06-27-foundational-map/` | `research/foundational-map/` | dir renamed |
| `claude_harness/docs/research/2026-06-27-logic-investigation/` | `research/logic-investigation/` | dir renamed |
| `claude_harness/docs/research/2026-06-27-logic-fair-trials/` | `research/logic-fair-trials/` | dir renamed |
| `claude_harness/docs/research/2026-06-27-obligations-formalisms-survey/` | `research/obligations-formalisms-survey/` | dir renamed |
| `claude_harness/docs/research/2026-07-02-nlp-logic-interface/` | `research/nlp-logic-interface/` | dir renamed |
| `claude_harness/db/harness/` | `stores/` | single-occupant parent flattened [C13] |
| `claude_harness/tools/` (gates) | `gates/` | staging_guard, no_lazy_imports, no_destructive_ddl, append_only_integrity, findings_gate(+fixture), doc-legibility/ |
| `claude_harness/tools/` (filing) | `filing/` | file_finding/foreclosure/resolution/rationalization, persist_claude_ephemera |
| `claude_harness/tools/hooks/` | `hooks/` | pre-commit (rewritten), stamp_provenance |
| `claude_harness/experiments/fact-mining/` (engine) | `engine/` (+ `engine/lp/`, `engine/tests/`) | the deductive-engine surface [A8] |
| `claude_harness/experiments/fact-mining/{row_performed_by,verify_binder,verify_operator_turns,verify_relevant_act}.py` | `instruments/` | the 4 harness verifiers [C16] |
| `claude_harness/experiments/fact-mining/docs/{LEDGER-LOGIC-MARRIAGE,LOGIC-LAYER-*,HOOK-DESIGN,DEPLOYMENT-ROADMAP}.md` | `design/` | the engine/hook theses [C11] |
| `claude_harness/experiments/fact-mining/docs/safety-critical-logging-standards/` | `law/briefs/safety-critical-logging/` | THE authoritative BRIEF + sources [C10] |
| `claude_harness/experiments/fact-mining/docs/incomplete-evidence-standards/` | `law/briefs/incomplete-evidence/` | sibling BRIEF + sources [C10] |
| `epistemic-operator/instruments/` | `instruments/` | close-time instruments [B2] |
| `epistemic-operator/tools/act_stream/` | `instruments/act_stream/` | the acts adapter (Port/ACL) [C17] |
| `epistemic-operator/harness/e*-build/` (DDL) | `kernel/lineage/` | s10–s18 + nla + remediation [B4] |
| `epistemic-operator/harness/e*-build/` (machinery) | `drive/`, `hooks/` | launch/arm/drill/probe/change-gate/stamp [B4] |
| `epistemic-operator/consults/` (GOVERNS) | `judgment/engine/`, `judgment/e-series/` | seeds, panel, analyses [B5/C3] |
| `epistemic-operator/POST-FABLE-OPERATING-BRIEF.md` | `judgment/POST-FABLE-OPERATING-BRIEF.md` | |
| `epistemic-operator/FINDINGS.md` | `FINDINGS.md` (root) | live F-series ledger [C4] |
| `epistemic-operator/BRIEF-CONFORMANCE-MAP.md` | `law/briefs/BRIEF-CONFORMANCE-MAP.md` | |

**What is NOT here (stays in the archive, cited at its old path):** banked e-series evidence,
consults classified RECORD, session ephemera, the recidivism study, the NLP lane (attic), witness
logs, and every run record. After the HOME-FLIP the archives are read-only and these paths are
permanent.
