<!-- doc-attest-exempt: point-in-time triage record (ledger rows 1184-1216); every open item's visible rationale per the maintainer's standing rule. -->

# Backlog triage 2026-07-23 — every open item's visible rationale

# Backlog Triage Report — autoharn (ledger row 1184)

Method: read every open `led work list` row (63 items) plus row 1184 itself, then verified each against the current tree (git log, grep, file reads, live fixture runs) rather than trusting the item's own text. Findings below are grounded in what I actually observed this session — cited inline.

## Key cross-cutting finding

Several items assume the **runs-are-linear** ruling (CLAUDE.md, 2026-07-11) forecloses in-place migration — it doesn't, fully: `bootstrap/migrate.sh`/`migrate_core.py` **already shipped** (commit `159284b`, 2026-07-14, registered root verb `./migrate`, confirmed executable and `--help`-responsive) as the stable migration surface for **real deployments** (ent), distinct from autoharn's own throwaway experiment worlds. This resolves item 31 outright and reframes 16/50/53.

Also: this repo's own `deployment.json` names it **`autoharn2`** — a fresh reborn world already at lineage head (s57), not a patched autoharn1. That explains why several "migrate autoharn1" items are moot: autoharn1 is dust (runs-are-linear), superseded by rebirth, not by in-place migration.

## Full table

| slug | bucket | rationale |
|---|---|---|
| abc-wallclock-dominance-maintainer-callback | MAINTAINER | Explicit standing parking row: prod him at pickups until he retires/acts/commissions; no agent may propose solutions. |
| belief-doubt-tier | BLOCKED | Staged obligation opened at v1 belief-substrate merge (rows 1914/1919); s53-55 (belief substrate) confirmed shipped in LINEAGE_CHAIN, so prerequisite is satisfied — ready to design against v2 typed columns. Reclassify as SONNET-EXECUTABLE if picked up (design against s53-55 columns now live). |
| belief-review-bridge | SONNET-EXECUTABLE NOW | Same prerequisite (v1 belief merge) now satisfied per s53-55 being live; design against v2 typed columns as instructed. |
| boundary-recursion-net-single-invariant | SONNET-EXECUTABLE NOW | Code-health item (guarded-traversal helper), no `engine/lp/` matches found for existing consolidation — gap confirmed still open, small and self-contained. |
| branch-divergence-damage-scout | SONNET-EXECUTABLE NOW | Read-only scout, no writes; nothing found in tree suggesting this was already run. |
| change-gate-foreign-defaults | OBSOLETE | Confirmed fixed: `hooks/pretooluse_change_gate.py` comment (line ~240) reads "NO _DEFAULT_SUBJECT_ROOT / _DEFAULT_STATE / _DEFAULT_JOURNAL (removed 2026-07-17, work item...)" — exact fix landed. |
| cli-rebase-fixture-repairs | SONNET-EXECUTABLE NOW (serialized behind CLI surface) | Verified LIVE by running the fixtures: `led-help-token-closure`, `resource/estimate/taxonomy-intake-validation` all fail today with "missing required-for-the-served-shim field(s): boundary_url, boundary_deployment"; `track-work` and `actual-intake-validation` fail on their own GREEN assertions. Still genuinely broken — confirmed red, not stale. |
| countersign-scoping-actor-not-item | FABLE-SPEC | Kernel/lineage scoping fix (actor-id -> work-item key); explicitly routes through Fable-authored + maintainer-ratified spec per its own text. |
| defeasible-maintainer-decision-model | MAINTAINER-BANDWIDTH-GATED / FABLE-SPEC (parked, not dispatched) | Awaits philosopher-Fable consult bandwidth; no urgency stated. |
| delegation-observer-workflow-tool-coverage | SONNET-EXECUTABLE NOW, hooks/ surface (worktree build, merge gated) | Verified: `hooks/pretooluse_delegation_observer.py` matches only `Task`/`Agent` (confirmed by grep), zero mentions of "Workflow" tool — gap still real. |
| deploy-time-feature-selection | BLOCKED on setup-tui-rebuild | The TUI rebuild (item 54) is the natural home for the checkbox feature-selection flow; dispatching this before the rebuild lands risks building into the condemned teletype shell. |
| deployment-makespan-offering | BLOCKED on deploy-time-feature-selection | Explicitly "folds into deploy-time-feature-selection as a manifest checkbox" per its own text. |
| derive-docs-verb-experiment | MAINTAINER | Explicitly "parked, not dispatched" pending maintainer green-light. |
| dispatch-principal-wiring | SONNET-EXECUTABLE NOW | Only one `LED_ACTOR` hit in hooks/ (a teach-text example, not real wiring) — the ask (wire registered principals into every dispatch preamble) is unaddressed. |
| doc-tree-reorg-user-guide | OBSOLETE (Phase 1 shipped) | `user-guide/` directory now exists with the full canonical set (README.md, USER-GUIDE.md, QUICKSTART.md, FAQ family) — confirmed by directory listing and matching commits (`2fe5322`, `c8f61d7`, `c520303`). Relocation-only phase 1 is done. |
| ent-inplace-migration | BLOCKED | Prerequisite tool now exists (`./migrate`, shipped 2026-07-14) — mechanism is no longer the blocker. Still blocked on a **witnessed ent session gap** (no-modify-during-live-session rule) that only the maintainer/operator can confirm. |
| ent-observatory | BLOCKED on maintainer re-ask | Scope was explicitly "first audit cycle only... RECURRENCE: re-run on maintainer ask." Four cycles already banked (`observatory/ent/cycle-001..004.md`, latest 2026-07-14) — awaiting his next ask, not idle neglect. |
| experience-secret-gitignore-hazard | split: MAINTAINER (panel fix) + SONNET-EXECUTABLE NOW (scaffold generalization) | Verified live: `.claude/secrets/stamp_secret.hex` still untracked and un-gitignored in `experience/autoharn-panel` (maintainer's own act, must not touch per live-session rule). But the GENERALIZE ask is unmet: `bootstrap/new-project.sh`'s scaffold-owned `.gitignore` block writes only `.claude/logs/`, never `.claude/secrets/` — confirmed by reading the block directly. That piece is Sonnet-executable now. |
| experience-spy-report-01 | MAINTAINER (verify done) | No artifact found under a plausible report path; needs the maintainer/orchestrator to confirm whether this was ever delivered before re-dispatching (avoid duplicate spy pass on a live session). |
| formula-declaration-path | FABLE-SPEC / MAINTAINER-BANDWIDTH-GATED | Explicitly "Fable spec + ratification when picked up," own text says pick up "when I've more executive bandwidth." |
| fuse-vfs-knowledge-hydration | FABLE-SPEC (parked) | Explicit candidate experiment, philosopher-Fable consult already commissioned; no further Sonnet action defined. |
| human-countersign-stamp-path | MAINTAINER | "Design decision needed" — whether shell+secret-possession authenticates a human principal is squarely his call. |
| item-bracketed-work-discipline | MAINTAINER | Orchestrator refinement explicit "pending maintainer review... he flagged himself delirious; veto freely." |
| led-json-payload-argstrlen-wall | OBSOLETE | Superseded by the CLI rebase: `led.tmpl`'s write path is now the HTTP boundary service (`serving/boundary_service.py`, `MAX_WRITE_BODY_BYTES`/`MAX_ARTIFACT_BODY_BYTES`), not a `psql -v` argument — the ARG_MAX/E2BIG failure mode this item describes cannot occur on the current path. The cited fixture (`seen-red/led-json-payload-mode`) itself needs migrating/retiring to match, folded into cli-rebase-fixture-repairs rather than standing alone. |
| led-review-bare-help-exit-code | OBSOLETE | Superseded by the CLI rebase: `led review` is now argparse-based (verified: `led review --help` exits 0 via a direct test of the current parser construction), not the old bash `$#-lt 4` guard the item describes. |
| led-work-close-resolution-teaching | OBSOLETE | Confirmed fixed: `led.tmpl` lines ~1893-1895 already reject non-enum resolutions client-side with a teaching message naming the closed vocabulary. |
| ledger-kind-resource-semantics | MAINTAINER | Explicit "design question, not foreclosed here" — typed actionability classification is a values question for him. |
| ledger-tag-folksonomy | BLOCKED | Own gating: "start only after the boundary review loop settles AND the legacy/ CLI-rebase work is underway." Legacy-led retirement has now landed (see below) — worth a status check with the maintainer on whether the boundary review loop condition is also now met, but I did not find evidence it's explicitly declared "settled." |
| legacy-led-retirement | OBSOLETE (shipped) | Confirmed comprehensively done: all three phases landed — commit `93affa0` "the deletion — legacy-led.tmpl git rm'd", `a943d46` "mark all three parts ratified and complete", `800f27f` "Parts A+B: obligation revocation as a typed event; boundary artifact routes", `ea41423`/`56259a3` extending boundary coverage to work verbs/decomposition-review-status/briefing/grammar preflight. This is the maintainer's own row 29 in today's directive text and it's already closed by events — should be `led work close ... shipped`. |
| maintainer-key-generation | MAINTAINER | His own act (generate keypair); nothing for an agent to do. |
| migration-script-stable-interface | OBSOLETE (shipped) | Confirmed: `./migrate` exists, executable, registered root verb, backed by `bootstrap/migrate_core.py` (1055 lines) — commit `159284b` plus fixes (`0da91d7`, `d698ca7`). Exactly what was asked for. |
| nbdr-defect2-adv-probe | MAINTAINER (clarify or drop) | Statement is bare ("adversarial probe item") with zero substantive content — unnameable-consumer shape (named-consumer-test memory). Recommend he confirm whether this is a stub artifact to drop or has real content elsewhere. |
| nlp-epistemic-readings-prod | MAINTAINER-BANDWIDTH-GATED | Explicit standing prod, retire only on his word. |
| obligation-actor-type-system | FABLE-SPEC (parked) | Explicit "Fable-tier design exploration when scheduled," "no urgency." |
| otel-model-attestation | BLOCKED → now partially unblocked | Explicitly sequenced "after s40/s41" — both confirmed shipped in LINEAGE_CHAIN. A kernel-free prototype "may precede" per its own text — that slice is SONNET-EXECUTABLE NOW; the kernel-touching slice stays FABLE-SPEC. Still MAINTAINER-BANDWIDTH-GATED per its own marking. |
| overnight-batch-doc-backfill | SONNET-EXECUTABLE NOW | No matching backfill entries found in `orchlog.d/` (only 1 file present, unrelated) — gap still open. |
| pipeline-dsl-exploration | FABLE-SPEC | Explicit "Fable-authored spec, maintainer ratifies." |
| post-freeze-documentation-debt | SONNET-EXECUTABLE NOW (sub-item 4 only) | Sub-item (4) is explicitly "WRITABLE NOW"; others are post-build sequenced (s42/s43 docs partially present in `user-guide/USER-RECIPES-FAQ.md` per grep, but no dedicated orchlog.d entry found — worth a fresh sweep). Overall MAINTAINER-BANDWIDTH-GATED for sequencing per its own text. |
| principal-logic-research-prod | MAINTAINER-BANDWIDTH-GATED | Explicit standing prod. |
| rdf-jsonld-derived-export | BLOCKED | Explicitly held until `fact:` schema stabilizes — no evidence that has happened. |
| reasoning-beyond-obligations | FABLE-SPEC | Explicit "Fable spec + ratification when picked up." |
| recovery-mode-signed-authority | split: SONNET-EXECUTABLE NOW (design note) + FABLE-SPEC (constitutional pieces) | Item's own text: "Design note first... may be drafted... constitutional pieces route to Fable+maintainer." No design note found under `design/` yet. |
| refusal-recording-diagnostics-tier | SONNET-EXECUTABLE NOW | Explicitly "offered as a separate, optionally-immediate item," not routed to maintainer for permission — cheap and immediate per its own text. |
| refuse-verdict-legibility | MAINTAINER | "Routes to the maintainer for the semantics call before any kernel change" — explicit. |
| registry-audit-backup-retention-policy | MAINTAINER | His own word: absence is "organizational negligence" — needs him to actually write/ratify the policy, not an agent to infer one. |
| registry-audit-sql-dumps-github-incomplete | SONNET-EXECUTABLE NOW | "approved if size permits" — an executable build task with a known, named gap (no pgAudit read-log data), not blocked. |
| resolve-violation-class-ambiguity | OBSOLETE | Confirmed fixed: `led work resolve-violation` now has a `--class` disambiguator flag with full refusal teaching text (verified in `led.tmpl` ~2117-2210). |
| s15-birth-onconflict | SONNET-EXECUTABLE NOW | Investigation task, kernel-adjacent but explicitly "reproduce on a scratch schema first" before any fix routes to ceremony — the investigation itself is Sonnet work. |
| s29-epoch-amend-and-apply | OBSOLETE | The epoch amendment shipped in-file (`f56e271`, confirmed live in current `s29-obligation-item-key-and-typed-close.sql` per LINEAGE_CHAIN text). The "apply to the live world" clause targeted **autoharn1**, which is now dust — this world (`autoharn2`) was born fresh at full lineage instead of migrated in place, consistent with runs-are-linear. Overtaken by the rebirth event. |
| s43-refusal-journal-bigint-overflow | OBSOLETE | Resolved by s49 ("journaler overflow guard," confirmed shipped in LINEAGE_CHAIN: "totalizes the attempted-identity resolution... journaled with attempted-id NULL instead of aborting") — an exact match for this item's requested fix shape. |
| s56-s57-chain-wiring | OBSOLETE | Confirmed shipped: `bootstrap/new-project.sh`'s `LINEAGE_CHAIN` includes s56/s57 (commit `58b7991`), verified by direct grep of the live chain string. |
| self-deployment-migrate-s36plus | OBSOLETE | Targeted migrating autoharn1 to s37+; superseded by this world's rebirth as `autoharn2` already at s57 (runs-are-linear — autoharn1 stays dust, never patched). |
| setup-tui-rebuild | SONNET-EXECUTABLE NOW, IN-PROGRESS (continue, don't re-dispatch fresh) | Confirmed substantial build already underway: `tui_app.py`, `durable_decisions.py`, `feature_facts.py`, `principals_authority.py`, `signed_genesis.py` etc. all present in `tools/setup_tui/`, plus multiple sub-specs (`FABLE-SETUP-TUI-*-SPEC.md`) and recent commits continuing it. Dispatch as a continuation, not a new commission. |
| spa-capability-introspection | BLOCKED | "belongs to autoharn-panel repo, parked" — wrong repo for this triage/build surface. |
| sql-acl-thinking-layer | FABLE-SPEC (parked) | Explicit "Fable-tier exploration when scheduled." |
| srs-trivia-capture-meta-goal | MAINTAINER | Explicit meta-goal parking row, hold until he acts or retires. |
| standing-injection-budget-asymmetry | SONNET-EXECUTABLE NOW | Confirmed still live: `hooks/sessionstart_durable_decisions.py` subtracts header bytes from budget before the row loop; `bootstrap/templates/pickup.tmpl` starts from raw `byte_cap` — verified both lines directly. |
| stop-breaker-docstring-inherit-divergence | OBSOLETE (moderate confidence) | Grep for `breaker_inherit`/`inherited_count` in `hooks/stop_clean_exit.py` returns zero hits anywhere, including as claimed outcome strings — only `clean_allow`/`breaker_fail_open`/`blocked`/`observed_would_block` exist. The docstring's "inherits breaker state" language now reads as an honest description of internal count-continuity mechanics, not a claim of a third emitted outcome. Recommend a quick maintainer/reviewer double-check given only moderate confidence, but no live divergence found. |
| submodule-shim-set-drift | SONNET-EXECUTABLE NOW | Confirmed still live: `upgrade-submodule.sh` VERBS list and `convert-to-submodule.sh` VERBS list both omit `asof-export` while the scaffold ships it — verified directly. |
| substitution-of-authority-prod | MAINTAINER-BANDWIDTH-GATED | Explicit standing prod, retire only on his word. |
| track-work-boundary-story | MAINTAINER | The script's own comment block explicitly states this is "A NAMED, FLAGGED GAP, not a fix... until a maintainer decision resolves it" — self-declared, not an oversight. |
| umbrella-cli | MAINTAINER (ratify the spec) | Fable-authored spec now exists (`design/FABLE-AUTOHARN-UMBRELLA-CLI-SPEC.md`, "Status: Fable-authored 2026-07-23; awaits maintainer ratification"). Prerequisite (legacy-led retirement) is done, so this is now squarely ready for his ratification, then Sonnet build — not further Sonnet-executable pre-ratification. |

## Counts

- SONNET-EXECUTABLE NOW: **21** (including split items counted once)
- OBSOLETE: **13**
- BLOCKED: **9**
- MAINTAINER: **16**
- FABLE-SPEC: **9** (some overlapping with MAINTAINER/BLOCKED tags above where both apply — counted by primary bucket)

(63 rows total, some carry a secondary split noted in the rationale column.)

## Suggested dispatch grouping for the SONNET-EXECUTABLE set

**Batch 1 — hooks/ live-exec surface** (worktree build, merge gated on next session gap; touch disjoint files, could go to one builder or split):
- delegation-observer-workflow-tool-coverage (`hooks/pretooluse_delegation_observer.py`)
- dispatch-principal-wiring (dispatch preamble wiring — likely touches orchestration scripts, not hooks/ directly — verify surface before batching)

**Batch 2 — bootstrap scaffold + CLI-adjacent surface** (umbrella-CLI conflict: these touch `bootstrap/`, not root executables directly, so likely NOT serialized behind the umbrella build, but confirm before dispatch):
- submodule-shim-set-drift (`convert-to-submodule.sh`, `upgrade-submodule.sh`, derive from `new-project.sh`'s own loop)
- experience-secret-gitignore-hazard, scaffold half only (`bootstrap/new-project.sh` gitignore block)
- standing-injection-budget-asymmetry (`hooks/sessionstart_durable_decisions.py` + `bootstrap/templates/pickup.tmpl`)

These three could reasonably go to **one builder** — same general bootstrap-scaffold neighborhood, small independent diffs, low collision risk.

**Batch 3 — cli-rebase-fixture-repairs** — dispatch alone: nontrivial (≈15 fixtures across three families, live-verified red), deserves its own builder and its own review pass; also naturally absorbs the led-json-payload-argstrlen-wall fixture retirement/migration since that fixture needs the same served-path treatment.

**Batch 4 — belief-review-bridge (+ belief-doubt-tier if picked up together)** — both now unblocked by s53-55 landing; same surface (belief kind / v2 typed columns), natural single commission.

**Batch 5 — setup-tui-rebuild** — continuation of in-flight work; keep with whichever builder/session already has context, don't re-dispatch as fresh.

**Standalone singles** (small, no natural batch-mate, dispatch independently): boundary-recursion-net-single-invariant, branch-divergence-damage-scout, overnight-batch-doc-backfill, s15-birth-onconflict, registry-audit-sql-dumps-github-incomplete, refusal-recording-diagnostics-tier, recovery-mode-signed-authority (design-note slice only), otel-model-attestation (kernel-free prototype slice only), post-freeze-documentation-debt sub-item 4.

**Not touching CLI dispatch/root executables/scaffold shims** in this SONNET-EXECUTABLE set except the umbrella-cli item itself (which is MAINTAINER, not executable) — so none of the above conflict with the in-flight umbrella build; no serialization needed for this batch.

One process note worth flagging to the orchestrator directly: **legacy-led-retirement (today's directive's own row 29) is already shipped** — recommend closing it (`shipped`) before dispatching anything else, since its "still open" status is itself exactly the kind of invisible-rationale defect row 1184 exists to eliminate.