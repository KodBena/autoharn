# LAYOUT — the designed directory tree of the consolidation home

- **Served model (self-report):** claude-fable-5. Standing caveat: there is no
  introspective channel that could detect a silent substitution; this is the session's
  own system-context report.
- **Status:** DESIGN, committed for the maintainer's scan BEFORE any bulk building
  (CONSOLIDATION-MANDATE.md, "Process law for the redo"). Nothing described here exists
  yet; the target repo `~/w/vdc/1/autoharn` is deliberately NOT created by this design.
- **Companions:** `MIGRATION-MANIFEST.md` (file-by-file dispositions),
  `BUILD-BRIEF.md` (the executable increment).
- **Law this design discharges:** CONSOLIDATION-MANDATE.md §1–§6; ADR-0012 and ADR-0008
  applied to the meta-project itself (maintainer ruling, 2026-07-07, verbatim: "the ADRs
  apply as much to us (the meta project) as the projects it's supposed to serve. Just the
  fact-mining directory is already a violation-in-spirit of ADR-0012 and ADR-0008 at the
  same time"); ADR-0013 (complete working surface, no self-authorized narrowing);
  ADR-0005 Rule 5 (file location reflects content).
- **Vocabulary** (doc-legibility, per the maintainer's 2026-07-07 ruling that the gate
  ought to cover any documentation a human might read; terms per `GLOSSARY.md`):
  ADR = architecture decision record (the project LAW). DDL = data-definition SQL, the
  schema-creating files. EDB = extensional database, the fact export the ASP engine
  grounds over. ASP = answer-set programming (clingo); `.lp` files are its programs.
  DTO = decompose-then-overrule, the clause-defeat discipline. kernel = the subject-side
  decision-ledger schema family (s10…s18). harness-db / stores = the operator-side
  operational stores (findings, foreclosures, rulings, acts, rationalizations).
  seen-red = the both-polarity proof that a gate can actually fail (ADR-0011).
  arm/drive = the pre-run mechanical checklist and launch machinery for a collaboration.

## 0. The design rule this tree is built from

Every directory in this tree makes two claims, and LAYOUT review checks both:

1. **A single-home claim (ADR-0012 P1).** The directory is the ONE authoritative place
   for its kind of thing. No hand-synced mirror of its contents exists anywhere else in
   the repo; anything derived from its contents is computed, not re-typed.
2. **A single-currency claim (ADR-0008).** Everything in the directory is the same kind
   of thing — one currency. A directory that mixes kinds that read as one (code with run
   evidence, law with churn, engine with daemon) is the three-currencies-read-as-one
   category error ADR-0000 Specimen 2 names, at directory scale.

**The named negative specimen** is the current state this design supersedes:
`claude_harness/experiments/fact-mining/` — 354 tracked files flat in one directory,
mixing at least six currencies that a reader cannot tell apart from `ls`: the ASP
marriage engine (`ledger_edb.py`, `ledger_acts.lp`), NLP daemon runtime
(`coref_decode_server.py`, `nlp_server.py`), harness-ledger verifiers
(`verify_binder.py`), tests of three different systems (`test_ledger_marriage.py` beside
`test_gliner_wire_boundary.py`), a numerics lab (`nla_lab/`), and — buried under an
*experiment's* docs directory — the authoritative external-standards BRIEF the whole
harness answers to (`docs/safety-critical-logging-standards/BRIEF.md`). That last one is
the sharpest ADR-0008 violation: LAW filed as experiment ephemera, so its authority is
invisible exactly where a reader would look for it. The maintainer's verdict stands:
"completely out of reach for humans." Every rule below is the inversion of one of these
mixings.

Two corollaries applied throughout:

- **Default to flat (ADR-0008 negative register).** The top level is flat, single-word,
  single-currency directories — no synthetic parents. A parent directory earns its place
  only by a real shared characteristic, never by absorbing a misfit. (The old repo's
  `experiments/` parent is the cautionary instance: it absorbed the project's core engine
  because the engine happened to be born inside an experiment.)
- **Renames are sanctioned and recorded.** This is a fresh-history repo: clarity beats
  diff-friendliness. Where an existing name is cryptic or carries a fossil context
  (`pretooluse_change_policy.py` living under `harness/e14-build/`), the migration
  renames/re-homes it, and every rename is a recorded `old → new` row in
  MIGRATION-MANIFEST.md, with per-file provenance (source repo + commit + sha256) so
  nothing silently diverges (mandate §5).

## 1. The tree

Target: `~/w/vdc/1/autoharn` (fresh history; NOT created by this design).

```
autoharn/
├── README.md                  # orientation: the two uses (collaborate / build), map of this tree
├── CLAUDE.md                  # the working standard every session in this repo runs under
├── GLOSSARY.md                # coined-term SSOT (the doc-legibility gate's definition surface)
├── BACKLOG.md                 # the ONE home for filed deferrals (ADR-0013 Rule 4)
├── FINDINGS.md                # the live F-series findings ledger (F1–F53; maintainer pass owed)
├── .claude/settings.json      # Claude Code hook wiring (stamp hook; paths inside THIS repo)
├── .gitignore
│
├── bootstrap/                 # clone → collaborating: executed entry path, never proofread-only
│   ├── bootstrap.sh           #   idempotent environment/gate/DB-reachability check + hook install
│   ├── QUICKSTART.md          #   the mini-collaboration walkthrough (mandate §6 exercises it)
│   └── AUDITOR.md             #   the "fire up an auditor on a snag" affordance
│
├── law/                       # what BINDS — read in full before work that invokes it
│   ├── adr/                   #   the ADR corpus 0000–0016, verbatim
│   └── briefs/                #   authoritative external-standards briefs + conformance
│       ├── safety-critical-logging/    # BRIEF.md (authoritative over our own runs' absences) + intermediate/ + sources/
│       ├── incomplete-evidence/        # BRIEF.md + sources/
│       └── BRIEF-CONFORMANCE-MAP.md    # harness-surface ↔ BRIEF clause map
│
├── judgment/                  # pre-banked odd-link judgment: apply, never weaken (POST-FABLE law)
│   ├── POST-FABLE-OPERATING-BRIEF.md
│   ├── engine/                #   engine seeds + panel verbatim + increment-0 (the live design basis)
│   ├── e-series/              #   the governing analyses (consults 27/31/35/39) + e19 seed
│   │                          #   + the pending FINDINGS-ratification packages (maintainer pass owed)
│   └── rulings/               #   ratified deliberation records (e.g. clause-defeat decompose-then-overrule)
│
├── kernel/                    # the subject decision-ledger kernel — DDL lineage + its fixtures
│   ├── lineage/               #   s10 … s18 (+ nla, + remediations) in order; new increments append
│   └── fixtures/              #   both-polarity kernel fixtures (stamp, independence, readiness-vs-close)
│
├── stores/                    # harness-db operational stores — DDL + their fixtures (one lineage each)
│                              #   001 research ledger · 002 rationalization · 003 acts stream
│                              #   004 rulings (+007 delivers-FK) · 005 findings · 006 foreclosure debt
│
├── instruments/               # close-time instruments: manifest, consumers, derivers, verifiers
│   ├── act_stream/            #   the acts adapter (session JSONL → acts EDB) + its fixtures — the Port/ACL
│   └── fixtures/              #   instrument-level broken/synthetic fixtures
│
├── engine/                    # the deductive engine (ledger⇄logic marriage) — the project's build front
│   ├── lp/                    #   the ASP programs (ledger_acts/assumes/dto/support/tnow, core-a, soundness)
│   ├── tests/                 #   engine tests (pure-logic + parity)
│   └── *.py                   #   edb/floor/differential builders, clingo runner, law census,
│                              #   judgment registry + baseline, parity verifiers, scratch builders
│
├── gates/                     # what REFUSES at commit/CI: staging guard, lazy-import, destructive-DDL,
│   │                          #   append-only integrity, findings gate, fixture census, layout census
│   └── doc-legibility/        #   the coined-term legibility gate
│
├── filing/                    # what WRITES records: file_finding / file_foreclosure / file_resolution /
│                              #   file_rationalization / persist_claude_ephemera
│
├── hooks/                     # what INTERCEPTS at run time: git pre-commit, stamp_provenance (PostToolUse),
│                              #   pretooluse_change_gate (the subject-side change gate), stamp_intercept
│
├── drive/                     # run machinery for a collaboration/experiment: launch_subject.sh,
│                              #   the arm-script template + freeze_manifest.sh, delivery_drill.py,
│                              #   gate_probe.py, packet template
│
├── seen-red/                  # both-polarity gate evidence — a gate never seen red is a claim (ADR-0011)
│                              #   one subdirectory per gate/close-line, migrated verbatim, census-gated
│
├── design/                    # pattern & design documents (not law, not run evidence): architecture,
│                              #   north star (PROPOSAL), review-fixpoint protocol, never-again trio,
│                              #   policy-authoring seam, engine main shape, ledger-logic marriage,
│                              #   logic-layer seam/ASP, hook design, deployment roadmap, publishing posture
│
├── research/                  # sourced research corpora (formalisms survey, logic trials, foundational map)
│
├── runs/                      # NEW run/close records accrue here — first occupant: the mandate-§6
│                              #   acceptance run; old-run evidence stays in the archives, permanently
│
├── ephemera/                  # whole-session Claude Code ephemera snapshots (the auditability law's home)
│
└── provenance/                # the transition record: per-file migration manifest (source repo+commit+sha),
                               #   path-translation note for archived citations, and the HOME-FLIP record
```

## 2. Per-directory justification — the single-home and single-currency claims

Each row states: what ONE kind of thing lives here (0008), why this is its ONE home
(0012), and what it must never absorb.

| Directory | Single-currency claim (ADR-0008) | Single-home claim (ADR-0012 P1) | Must never absorb |
|---|---|---|---|
| root files | repo-wide standing documents a session loads first (standard, glossary, deferrals, orientation) | each is the one home for its register: CLAUDE.md = conduct, GLOSSARY.md = vocabulary, BACKLOG.md = deferrals | design notes, run records, law texts |
| `bootstrap/` | the executed clone-to-collaborating path | the one entry point; nothing else may describe setup steps (README points here, never re-types them) | experiment machinery, per-run config |
| `law/adr/` | maintainer-ratified tenets, verbatim, append-amended | the one authoritative ADR corpus (the archives keep historical copies as evidence, with provenance recording which is authoritative after the flip) | proposals, design notes, consults |
| `law/briefs/` | authoritative external-standards briefs + their sources + the conformance map | the one place harness-must-support authority lives — un-buries the BRIEF from `experiments/fact-mining/docs/` (the negative specimen's sharpest instance) | our own run evidence (the BRIEF outranks it by standing rule) |
| `judgment/` | pre-banked odd-link judgment: the operating brief and the governing consults current work is read against | the one place a stand-in looks for banked judgment; POST-FABLE's "judgment moved from run-time to disk" made a directory | historical/superseded consults (those are evidence and stay archived) |
| `kernel/lineage/` | subject-side decision-ledger DDL, in lineage order, append-only | the one DDL lineage; today it is scattered across `epistemic-operator/harness/e*-build/` where `ls` cannot see it is one lineage | store DDL (different substrate, different trust role), fixtures |
| `kernel/fixtures/` | both-polarity fixtures proving kernel DDL properties | one home per lineage's proof; pairs with `seen-red/` entries | run evidence |
| `stores/` | harness-db operational-store DDL + the fixture that proves each (the numbered-pair idiom `006_*.sql` + `006_*_fixture.py` is kept: DDL and its proof are one lineage entry) | the one home of the findings/foreclosures/rulings/acts/rationalization/research-ledger shape | kernel DDL, queries, reports |
| `instruments/` | programs that READ the ledgers/acts at close time and derive verdicts | the one home of close semantics; `close_manifest.py` stays the registry the mandatory-lines discipline (F49) hangs off | gates (refuse at commit — different intervention point), filing tools (write — different direction) |
| `instruments/act_stream/` | the session-transcript→acts-EDB adapter + contract + fixtures | the one Port/ACL for transcript ingestion (P2: translates-and-validates) | analysis logic |
| `engine/` | the deductive-engine build front: ASP programs, EDB builders, census/registry, parity | the one home of the marriage engine — extracted whole from the negative specimen; `lp/` splits the ASP law programs (a distinct language and register) from their Python builders | NLP code of any kind (the lane stays in the attic), instruments (close consumers live one level up) |
| `gates/` | mechanized refusals wired into pre-commit/CI | the one place a contributor looks to answer "what will refuse my commit"; the pre-commit hook INVOKES from here, never re-implements | filing tools, hooks (interception ≠ refusal logic; hooks call gates) |
| `filing/` | record-writing CLIs (findings, foreclosures, resolutions, rationalizations, ephemera persist) | the one place to answer "how do I file X"; the standing "findings are FILED, not narrated" clause points here | gates, ad-hoc scripts |
| `hooks/` | interception surfaces registered with git / Claude Code | the one home of intercept code; `.claude/settings.json` and `core.hooksPath` point ONLY here | the gate logic they invoke (lives in `gates/`), run configs |
| `drive/` | reusable run machinery for arming/launching/drilling a collaboration | the one template home; per-run INSTANCES go to `runs/<id>/`, never back-edited into templates | run outputs, frozen per-run texts |
| `seen-red/` | both-polarity proof artifacts (red + green) per gate/close-line | the one evidence home the fixture-census gate enumerates against; migrated verbatim because gates without their seen-red do not count (mandate §3/§6) | narrative docs, new-run evidence |
| `design/` | settled/living design & pattern documents — proposals marked as proposals | the one design-note home (merges `claude_harness/docs/design-notes/` with the engine/hook design docs buried in the negative specimen) | law (binds — `law/`), analyses of runs (evidence), churn notes |
| `research/` | sourced research corpora (surveys with per-source files) | the one research library; engine formal-systems work reads against the obligations survey without a cross-repo reach | run evidence, design decisions |
| `runs/` | records of collaborations/closes executed FROM this repo, one subdirectory per run | the one place new evidence accrues — the mandate's evidence-stays-where-it-happened rule, forward-applied: after the flip, "where it happens" is here | old-repo evidence (never moves), templates |
| `ephemera/` | whole-session Claude Code ephemera snapshots, never cherry-picked | the auditability law's home in the new repo; `persist_claude_ephemera.py` targets it | hand-authored documents |
| `provenance/` | the migration/transition record: manifest, path-translation note, HOME-FLIP record | the one place "where did this file come from / which repo is authoritative" is answered (mandate §5) | anything else |

## 3. ls-legibility, argued level by level

- **Top level (21 entries: 6 root files + 15 directories).** One screen. Every directory
  is a single word (or hyphenated coined term) naming its currency; a newcomer running
  `ls` can answer the two mandate questions unaided — *"how do I collaborate here?"*
  (`README.md → bootstrap/`, standard in `CLAUDE.md`, what binds in `law/`) and *"how do
  I build here?"* (`engine/`, `kernel/`, `stores/`, `instruments/`, with `judgment/`
  holding the banked design basis). The verbs are separated on sight: `gates/` refuse,
  `filing/` writes, `hooks/` intercept, `instruments/` read, `drive/` runs. This is
  deliberately flat rather than nested under a `tools/` or `docs/` parent: ADR-0008's
  default-to-flat, and the observed failure of both parents in the old repos
  (`experiments/` swallowed the engine; `docs/` swallowed the LAW briefs).
- **Second level.** No directory holds more than ~35 files, and none mixes registers:
  `law/adr/` is 17 numbered tenets; `kernel/lineage/` is a visibly ordered sNN sequence
  (the lineage is legible AS a lineage for the first time); `engine/` separates `lp/`
  (ASP) from Python from `tests/`; `seen-red/` is one subdirectory per gate, named for
  the gate. The largest flat directory is `instruments/` (~30 files), all one currency
  (close-time readers), with names that state their verdict (`verify_*`, `*_currency`,
  `close_*`).
- **Third level and below.** Only evidence-shaped trees (`seen-red/<gate>/`,
  `runs/<run-id>/`, `research/<survey>/`) and source sets (`law/briefs/*/sources/`) go
  deeper, and each is uniform inside — the depth encodes identity (which gate, which
  run, which survey), never a second taxonomy to learn.
- **The census keeps it true (maintainer ruling #3).** ls-legibility asserted once and
  never re-checked would rot exactly as the old repos did; BUILD-BRIEF §7 specifies the
  layout-census gate (top-level registry + per-directory currency patterns, both
  polarities) plus the honest review-only residue, so the conformance claimed here stays
  a checked property, not a founding legend.

## 4. What is deliberately NOT in this tree

- **The NLP lane** (spaCy/Stanza/GLiNER/coref daemons, their wire, their hardening test
  net, `nla_lab/`, `parse_seam/`, the adjudication widget, the impedance library) —
  stays in `claude_harness` as the attic (mandate §4), kept operational there: the
  ADR-0016 standing services keep running where they run today, and the old repo's
  path-gated standing-service gate stays with them. ATTIC-STAYS in the manifest.
- **Banked evidence** — e-series builds/packets/closes/transcripts, witness logs,
  consult records, deliberations, session ephemera, the recidivism study, hook trials,
  the ledger-marriage derivations, the two old repos' histories. Evidence stays where it
  happened (mandate §4); the old repos become read-only evidence archives at the
  HOME-FLIP. EVIDENCE-STAYS in the manifest.
- **The discarded first attempt** (`~/w/vdc/1/autoharn-drive`) — built on the wrong
  mandate, DISCARDED by the maintainer's ruling; not salvaged, not extended. Its CENSUS's
  honest findings (the set_actor defect note) are cited in BUILD-BRIEF §8 as risk input;
  its layout and kit are not reused. Deletion of the directory is the maintainer's call,
  never ours (manifest lists it DEAD with the ruling as the evidence of deadness).
- **A `docs/` directory.** Deliberate: "docs" is not a currency — it is where three
  different currencies (law, design, evidence) went to become indistinguishable in both
  old repos. Each former docs resident lands in the directory named for what it IS.

## 5. Naming decisions a reviewer may want to challenge

- `stores/` (not `db/harness/`): the old path nested a single-occupant parent (`db/`
  containing only `harness/`) — the ADR-0008 single-occupant-synthetic-parent shape;
  flattened, renamed for the coined term ("operational stores as one claim-ledger
  shape"). Recorded rename.
- `judgment/` beside `law/`: kept apart deliberately — ratified tenets/briefs BIND;
  pre-banked consults GOVERN their areas but carry proposal-status findings inside them.
  One directory would read two authority levels as one (the 0008 error). The split makes
  authority level legible from the path.
- `seen-red/` at top level (not under `gates/`): its evidence covers instrument close
  lines and kernel triggers too, not just pre-commit gates; homing it under any one
  consumer would misstate its scope. The coined term is already the project's name for
  this currency.
- `ephemera/` (not `docs/claude-ephemera/`): same content, one level, named for the
  currency; the persist tool's target updates once (it is the single writer — P1).
