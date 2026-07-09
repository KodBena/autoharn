# DIRCLASS — top-level directory classification

One axis: **is this directory needed for a functioning autoharn?**

- **CORE** — necessary for having a functioning autoharn.
- **DOC** — documentation; can be explicitly excluded from a functioning autoharn.
- **RESEARCH** — research corpora / experiments-on-the-harness; can be explicitly excluded.
- **OTHER** — anything else.

A directory that does not cleanly fit exactly one class is flagged in its basis line rather than
forced into the closest fit (ADR-0008).

| Directory | Class | Basis |
|---|---|---|
| `bootstrap` | CORE | `bootstrap.sh`/`QUICKSTART.md`/`AUDITOR.md`: the clone→collaborating stand-up a fresh clone runs first; without it there is no entry into the harness. |
| `engine` | CORE | The deductive engine (ledger⇄logic marriage, ASP programs, judgment registry) — the project's build front, executed at close time. |
| `filing` | CORE | `file_finding.py`/`file_foreclosure.py`/`persist_claude_ephemera.py` — the record-writing machinery every finding/foreclosure goes through. |
| `gates` | CORE | Commit-time refusal machinery (staging guard, lazy-import gate, census/findings gates) — removing it means nothing refuses at commit. |
| `hooks` | CORE | Run-time interception (git `pre-commit`, `stamp_intercept.py`, `pretooluse_change_gate.py`) — the harness's live enforcement at the moment of action. |
| `instruments` | CORE | Close-time instruments (manifest, consumers, derivers, verifiers, `act_stream` adapter) that a close is actually built from. |
| `kernel` | CORE | The subject decision-ledger's schema lineage (`lineage/` DDL in order) + both-polarity fixtures that `stores/` builds against. |
| `stores` | CORE | Harness-db operational-store DDL (findings/foreclosures/rulings/acts ledgers) + fixtures — "the data stores" the harness runs on. |
| `design` | DOC | Pattern/architecture prose (ARCHITECTURE.md, roadmaps, seam designs); README labels it explicitly "not law, not run evidence." |
| `judgment` | DOC | Banked design-basis prose (engine seeds, e-series analyses, ratified rulings); confirmed no running code opens these files — engine's `judgment_registry.py` hand-encodes the taxonomy itself (also normative/binding in spirit per CLAUDE.md, unlike ordinary design notes — a straddle worth naming). |
| `law` | DOC | ADR corpus + external-standards briefs: binding-in-spirit prose read before work, but confirmed never opened by running gates/engine (only filename shape is census-checked, never content) — (also straddles: CLAUDE.md treats it as normative, not merely descriptive, unlike ordinary docs). |
| `drive` | RESEARCH | Study-mode experiment *apparatus* (`arm.sh`, `launch_subject.sh`, `launch.conf`, `delivery_drill.py`, `rehearsal/`) — runs the epistemic experiments *on* the harness; not needed for a functioning (Use-mode) autoharn. Straddle: it is tooling, not corpus/evidence — classed RESEARCH by purpose; a couple of probes (`gate_probe.py`) double as Use-mode demo helpers. |
| `research` | RESEARCH | Sourced research corpora (logic-fair-trials, logic-investigation, obligations-formalisms-survey, foundational-map) — literature surveys, excludable without breaking the harness. |
| `seen-red` | RESEARCH | Per-gate both-polarity evidence directories — the literal "both-polarity gate evidence" example named in the RESEARCH definition. |
| `provenance` | OTHER | Migration manifest, path-translation, HOME-FLIP transition scaffolding from the two-repo consolidation — explicitly "migration/transition scaffolding" (also holds prose mandate docs like BUILD-BRIEF.md/CONSOLIDATION-MANDATE.md). |
| `runs` | OTHER | NEW run/close records accrue here (acceptance run, findings-gate-fixture) — explicitly "accrued run records" in the OTHER definition. |
| `ephemera` | OTHER | Whole-session Claude Code ephemera snapshots, README states local-only/untracked — explicitly "session ephemera" in the OTHER definition. |
| `.claude` | OTHER | Local Claude-Code tool settings (`settings.json` PostToolUse hook wiring) — a session/IDE convenience, not part of the harness a non-Claude-Code clone needs to run gates/close. |
| `.git` | OTHER | VCS internals — explicitly named in the OTHER definition. |
| `.pytest_cache` | OTHER | Regenerated pytest cache (gitignored within), rebuilt on next test run — explicitly "regenerated caches" in the OTHER definition. |
