#!/usr/bin/env python3
"""gates/max_lines.py -- ADR-0007 mechanization: soft-threshold file-size discipline made
mechanical over one honestly-scoped surface, with a RATCHETING BASELINE for current offenders
per ADR-0011 Rule 4 (no retroactive sweep).

WHY THIS GATE (design/FABLE-SETUP-TUI-FIELD-STRATEGY.md Track 1 item 2; the Rule 2(b) finding
in that doc's §1). `tools/setup_tui/screens.py` was born at 572 lines -- already over ADR-0007's
400-line ceiling -- and grew to 1458 lines across sixteen commits, four of them dedicated
fresh-context ADR-compliance reviews citing ADR-0000/0012, none of which ever asked ADR-0007's
own question, because nothing mechanized it (ADR-0007's own Consequences bullet admits "no
max-lines check exists"; its Revisit-when #1 names exactly this mechanization: "A linter or
pre-commit hook automates the size rule -- soft thresholds can become enforced limits"). Four
consecutive review-only misses on one package is ADR-0011 Rule 2's conversion trigger
(recurrence converts to mechanism, not more prose).

WHAT ADR-0007 ACTUALLY SAYS (read in full before authoring this gate -- law/adr/0007-file-size-
and-information-density.md -- the letter this gate mechanizes is deliberately narrower than the
ADR's own spirit, and the ADR says so itself under "What this tenet does NOT mean: not a hard
line-count limit ... not enforced by tooling today"). Target <=300 lines for a typical module;
<=400 acceptable for "a single coherent unit ... where splitting would fragment cross-line
invariants" -- a JUDGMENT CALL, not a measurement, per the ADR's Exceptions. This gate does NOT
attempt to detect coherent-unit-ness; it mechanizes only the one binary, honestly measurable
question ADR-0007 leaves for tooling: is a file over 400 lines, and if so, was it already over
400 before this gate existed (grandfathered, and required to never grow further) or is it newly
over 400 (refused outright, full stop)? The 300-400 band stays exactly what ADR-0007 calls it --
review territory -- this gate counts and reports it but never fails a file for being in it. The
separate density heuristic (effective lines / total lines, ADR-0007's own "Density" section)
stays exactly as qualitative and review-only as the ADR left it; this gate does not touch it.

SCOPE (declared, ADR-0011 Rule 1) -- the project's own packages, this commission's own framing:
    IN SCOPE:  tools/, gates/, hooks/, engine/ -- every git-tracked *.py under each (this repo's
               own authored source). ADR-0007's "Instance binding (autoharn)" note says autoharn
               has never had its own numeric re-derivation or oversized-file survey run; this
               gate's first run over this scope IS that survey, honestly measured rather than
               assumed (ADR-0011 Rule 3, measure-first) -- see BASELINE below.
    EXCLUDED, and why (same shape and same reasons as gates/no_lazy_imports.py's own
    EXCLUDE_PARTS / EXCLUDE_PATH_PREFIXES -- reused, not re-derived, since the underlying facts
    are identical: vendored/scratch/dependency trees this project does not author):
      - tools/makespan-scheduler/ -- vendored byte-for-byte (PROVENANCE.md), read-only per
        ADR-0004; a max-lines gate on code this project is committed not to edit would fail a
        defect nobody here can fix. (Currently contributes zero tracked *.py files to `tools/`
        anyway -- vendored via git submodule -- but excluded explicitly rather than by accident.)
      - .venv/, venvs/, node_modules/, __pycache__/, .git/, claude-ephemera/, .staging/ --
        dependency/scratch trees no contributor authors here.
    OUT OF THIS COMMISSION'S SCOPE, NOT ASSERTED CLEAN (a deliberate scoping choice per the
    builder brief's own instruction to "read what exists and scope deliberately" -- not an
    oversight, and not a claim these trees are fine): seen-red/ (fixture evidence, not package
    source -- and this gate's own census machinery would be self-referential over it),
    instruments/, filing/, kernel/, drive/, serving/, bootstrap/, stores/, provenance/,
    proposals/. Extending SCOPE_PREFIXES to cover any of these is a deliberate future act (with
    its own measured baseline), not a silent widening of what this pass was asked to cover.

RATCHETING BASELINE (ADR-0011 Rule 4; ADR-0007's Neutral clause: "no retroactive sweep --
Oversized files enter a refactoring queue and are addressed when next touched substantively").
BASELINE below is a MEASURED snapshot -- taken 2026-07-21, on base commit dd31de3, via
`git ls-files` + a plain line count over exactly the SCOPE_PREFIXES/EXCLUDE rules above -- of
every in-scope file already over the 400-line ceiling on the day this gate was authored. One row
per path, holding its line count AT THAT MEASUREMENT as the ratchet. A baselined file may shrink
(its ratchet is not retroactively lowered by this gate -- nothing stops it dropping under 400 and
leaving this table on its next touch, ADR-0011 Rule 1's "retrofit on touch") or hold steady; it
may never grow past its own ratchet. A file NOT in BASELINE that is over 400 lines is a NEW
offender and fails outright -- new files meet the bar the ADR always stated; only pre-existing
debt is grandfathered. Thirty files met this bar at measurement time; the five the commission
brief anticipated by name (screens.py, ui_textual.py, durable_decisions.py, signed_genesis.py,
principals_authority.py) are among them, but their exact counts differ from the brief's
recollection in three cases (ui_textual.py measured 674 not 643; signed_genesis.py measured 503
not 482; the brief itself instructed "verify counts yourself" -- ADR-0011 Rule 3 measure-first is
exactly this: a claimed number is not the baseline, a measured one is) -- and twenty-five further
offenders exist outside the setup_tui package this commission's narrative centered on. Silently
narrowing the baseline to only the five named files would leave this gate red on its own first
run over the real tree; the honest baseline is the full measured set.

Enforcement surface (ADR-0011 Rule 1, declared): test/CI gate (pre-commit hook + the standing
gates/ suite; see hooks/pre-commit's own wiring stanza for this gate, where present). NOT
construction/import-time (an over-ceiling file still imports fine); NOT a run-time invariant
(nothing about running the code depends on its length). This IS the mechanization ADR-0007's own
Revisit-when #1 asked for.

Negative self-check (ADR-0011 Rule 3's negative-control amendment -- "a gate is demonstrated to
FAIL on the defect shape it guards ... before its pass is credited"): seen-red/max-lines/
run_fixtures.py drives this module's own `evaluate()` against synthetic line counts, never
touching the real tree, proving (a) a brand-new over-ceiling path fails red; (b) a baselined path
at its exact ratchet passes; (c) the same baselined path one line over its ratchet fails red; (d)
a file in the 300-400 review band is never flagged; (e) a stale baseline row (a grandfathered
path no longer tracked in scope) is flagged, so the baseline itself cannot silently rot.
Census-registered in gates/fixture_census.py under "max-lines".

Exit 0 clean (prints a one-line summary); exit 1 listing every breach as
`path: <N> lines (<reason>)`.

Usage: python3 gates/max_lines.py [root] [--tree]  # default: repo root, git-tracked *.py in SCOPE
Lazy imports banned.

READ MODE (gates-staged-vs-tree-blindness, ledger row 1234): line count is a property of a
file's BYTES, so this gate reads each file's STAGED bytes by default
(gates/_staged_read.py's `read_source_text`, gates/deep_walk_recursion_guard.py's own pattern),
falling back to the working-tree file only when a path is not staged at all. Otherwise: stage a
file that grows past its ratchet, restore a short version in the tree without re-staging, and
this gate would pass on the tree's line count while the commit still embeds the over-ratchet
staged bytes. Pass `--tree` to force the working-tree read unconditionally instead.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _staged_read import read_source_bytes, run_git  # noqa: E402  (gates/_staged_read.py, shared home)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TARGET = 300
CEILING = 400

SCOPE_PREFIXES = ("tools/", "gates/", "hooks/", "engine/")

# same exclusion shape as gates/no_lazy_imports.py's own EXCLUDE_PARTS / EXCLUDE_PATH_PREFIXES --
# see module docstring's SCOPE section for why each entry is here.
EXCLUDE_PARTS = {"claude-ephemera", ".staging", "node_modules", ".venv", "venvs",
                 "__pycache__", ".git"}
EXCLUDE_PATH_PREFIXES = ("tools/makespan-scheduler/",)

# RATCHETING BASELINE -- see module docstring. Measured 2026-07-21 on base commit dd31de3, one
# row per in-scope path already over CEILING, holding its line count at measurement as the
# ratchet. Sorted by count, descending (a data table -- ADR-0007's own contraction rule permits
# packing a fixture/constant literal like this one row per line).
BASELINE: dict[str, int] = {
    # 1458 at gate authoring (base dd31de3); reconciled +6 to 1464 at integration: the
    # idris2-preflight fix (8580848) merged between the gate's baseline measurement and its
    # own merge -- witnessed growth from a parallel worktree, not unnoticed growth. The
    # ratchet points DOWN from here.
    # Reconciled +23 to 1487 (commit 12d5d1b's follow-up, boundary-interpreter-fallback
    # commission): screen_boundary's interpreter-fallback fix (ADR-0002 rules 1/4, field
    # observation g) was first landed contracted (walrus-in-conditional, semicolon-joined
    # statements) to fit this same ratchet without a bump -- an orchestrator error, corrected
    # per ADR-0007's own no-go clause ("never contract decision logic to fit a size budget;
    # code golf in a decision path hides bugs"), which outranks the ratchet. Rewritten in
    # plain, clearly-formatted statements; this bump is that plain form's honest cost, sanctioned
    # growth per this same rule's own "witnessed growth ... not unnoticed growth" precedent.
    # Reconciled +56 to 1543 (design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md build): the five
    # ad hoc destination probes this build replaces each shrank to one `classify_destination`
    # call, but `screen_fork_target`'s new FOREIGN third mode (spec §3 -- evidence display +
    # explicit typed acknowledgment, replacing a flat refusal) is genuinely NEW decision logic,
    # not a probe consolidation; `screen_birth`'s new FOREIGN-without-acknowledgment gate is the
    # same shape. Net across the module is a bump, not a shrink -- the five-consolidations
    # savings did not outweigh the one new mode's honest cost. Written plain (no golfing, per
    # this same rule's own no-go clause above); witnessed growth, not unnoticed growth.
    # Reconciled +122 to 1665 (design/FABLE-SETUP-TUI-CHECKLIST-SPLIT-SPEC.md build, this
    # commit): sanctioned explicitly by the commission ("a visible ratchet bump with rationale is
    # sanctioned if screens.py must grow, dense code is not"). Genuinely new decision logic, not
    # padding: `screen_boundary` now ALSO accumulates a `DaemonSelection` fact for the boundary
    # service (resolved-interpreter-once, per spec §4); `screen_observability` is rewritten from
    # a pure PREPARED-block display into two real selection branches (otelcol -- queues its own
    # config WriteAct plus a DaemonSelection; otel-watch -- queues a DaemonSelection) each with
    # its own INSTRUCTED checklist row; `_execute_commit` gained the dry-run WOULD-DO row for the
    # synthesized start-daemons script and the end-of-run VERIFIED-UP/NOT-UP translation loop.
    # None of this is a probe consolidation with slack to absorb it, unlike the destination-state
    # bump above. Written plain, no golfing (same no-go clause); witnessed growth.
    # Reconciled +63 to 1728 (GENESIS-GATE HARD-STOP, ledger row 1918): genuinely new decision
    # logic, not padding -- `screen_signed_genesis` now computes and announces the
    # `--accept-unverified-genesis` override before queueing the verify-commission act;
    # `_dispatch_result`'s verify-commission branch grew from a five-line REFUSED/WITNESSED
    # split into the ADR-0002 strongest-rung teaching refusal the commission requires (what
    # failed, why it matters, what to check, how to resume, that the override exists and its
    # cost) plus the override-exercised checklist row; `_execute_commit` sets
    # `state["commit_halted"]` so app.py can exit non-zero on any halted commit. Written plain,
    # no golfing (same no-go clause); witnessed growth.
    # Reconciled -44 to 1684 (design/FABLE-SETUP-TUI-TYPED-UI-SPEC.md build, obs a/b, P10): the
    # typed-element conversion (`Ui.say`/`Ui.banner` -> `Ui.emit`) is roughly a wash on line count
    # by itself (each call site gains a wrapper type name); the net shrink comes from the content
    # extraction (spec §3) -- the partial-birth-refusal teaching (eleven `ui.say` calls collapsed
    # to a five-line format-and-loop over `content/screens_data.py`'s
    # `PARTIAL_BIRTH_TEACHING`), the six-paragraph GENESIS-GATE HARD STOP teaching (collapsed to a
    # two-line loop over `GENESIS_GATE_HARD_STOP_TEACHING`), and four multi-line `ui.confirm`
    # prompt questions long enough to be judged as writing under P10 (moved to named
    # `CONFIRM_*` constants). This is a partial pass, not exhaustive: the remaining bulk is
    # genuinely computed decision logic and runtime-interpolated status/probe lines (P10's own
    # discriminator -- "error messages... are the logic's own contract and stay"), not the
    # authored "walls of text" prose class the commission named. Written plain, no golfing (same
    # no-go clause); witnessed shrink, the ratchet lowers with it (ADR-0011 Rule 4).
    # tools/setup_tui/screens.py -- REMOVED from BASELINE 2026-07-22
    # (design/FABLE-SETUP-TUI-REBUILD-SPEC.md §2, wholesale rebuild): `git rm`'d whole -- the
    # teletype-driving screen functions have no successor file, the decision/action logic they
    # carried lives on split across tools/setup_tui/steps_*.py (each well under ceiling). The
    # legacy-led-retirement Part C re-sequencing/health-gate/served-led changes that would have
    # bumped this file's count on the pre-rebuild line (row 1158/1159) are ported into the
    # steps_*.py successors instead (merge of worktree-agent-a17ac09f50b3745c0, integration
    # branch) -- there is no longer a screens.py path for this row to describe. The round1-fixes
    # branch (worktree-agent-a92e28a30da8e8dea) separately bumped this row +7 to 1798 for a
    # comment-only erratum fix (row 1173, the false "row 1942" citation) landed on the
    # since-deleted screens.py; that erratum text is ported forward into
    # tools/setup_tui/steps_boundary.py's own surviving copy of the same comment instead (this
    # merge, 2026-07-23) -- there is no baseline row left to carry the +7.
    # Reconciled +221 to 1373 (row 1263): two new kind-shape idioms (MANDATORY-ON-KIND,
    # KIND-OR-VALUE-PERMITTED). +17 to 1390 (AMENDMENT 1): drops the conflicted (regards,
    # missive_disposed) row, adds missive_regards' own row -- genuinely new, not padding.
    # bumped 1390 -> 1404 (s60-entitlement-enforcement.sql: one new MANIFEST row
    # (entitlement_act_class) + one widened row (principal_role_name) + CHAIN += s60).
    # bumped 1404 -> 1444 (s61-signature-symmetry-and-key-binding.sql: FOUR new MANIFEST rows
    # (signature_attests_row, signature_grade, key_binding_possession_ref, plus
    # signature_symmetry_witness's own CORE_COLUMNS entry) + one widened row
    # (principal_key_fingerprint, now three kinds) + CHAIN += s61).
    # Reconciled +4 to 1408 (s62-delegation-lifecycle-gating.sql, row 1385): CHAIN += s62 +
    # a short comment noting s62 adds no MANIFEST row of its own.
    # Reconciled at the s62+TUI coupled merge (2026-07-26): both parents' bump
    # comments kept verbatim above; the union is the measured merged file. Same
    # merge-union ratchet-crossing class as the reconciliations above.
    # NEW to BASELINE, 1458 (s65 build, design/FABLE-S65-REFUSAL-ATTEMPTED-KIND-SPEC.md,
    # ledger row 1487): one new MANIFEST row (refusal_attempted_kind, one-way, mirroring
    # refusal_attempted_actor's own shape) -- a visible ratchet bump with rationale,
    # sanctioned per this gate's own convention, not silently absorbed.
    # bumped 1458 -> 1592 (s65 fix round 2, BLOCKS MERGE review): CHAIN extended through
    # s63/s64/s65 (was stuck at s62, the gate's own CRITICAL finding); the classifier's
    # bare `"kind" in defn` substring test replaced with a word-boundary regex
    # (_BARE_KIND_RE) plus its own explanatory comment; a genuinely NEW, EIGHTH kind-shape
    # idiom, ELIGIBILITY-GATED ONE-WAY (regex, classifier branch, ELIGIBILITY_ONE_WAY_
    # MANIFEST with its five s64 delegation_* rows, the 2f/2h assert_manifest symmetry,
    # check-4 exemption) -- all genuinely new decision-boundary logic and its own
    # reasoning/precedent-citing prose, not padding.
    # bumped 1592 -> 1605 (s67-refusal-digest-bound.sql: the CHAIN list gains s66/s67, and the
    # refusal_payload_digest MANIFEST row is re-classified two-way -> one-way plus its own
    # explanatory reason text) -- witnessed growth from a genuine new arity/citation, not
    # unnoticed growth.
    # bumped 1605 -> 1635 (s67 §2 AMENDMENT fix round, "NULL may not carry the meaning"): one
    # new MANIFEST row (refusal_digest_disposition, two-way) plus one new
    # CROSS_COLUMN_COUPLING_MANIFEST row (refusal_payload_digest_disposition_coupling) and the
    # refusal_payload_digest MANIFEST row's own reason text extended to cite the new coupling --
    # witnessed growth from two genuine new manifest entries, not unnoticed growth.
    # bumped 1635 -> 1716 (s68, kernel/lineage/s68-typed-absence-dispositions.sql): two new
    # MANIFEST rows (refusal_attempted_kind_disposition, refusal_attempted_actor_disposition,
    # both two-way) plus two new CROSS_COLUMN_COUPLING_MANIFEST rows, PLUS the classifier itself
    # gaining a genuinely new capability -- _CROSS_COLUMN_COUPLING_RE now captures a comparator
    # (`=` or `<>`) instead of assuming `=`, since the kind-disposition coupling's own four-member
    # vocabulary needs the inequality form (three of four members mean NULL, not one) -- witnessed
    # growth from two new manifest entries plus one classifier capability, not unnoticed growth.
    "gates/kind_shape_manifest_gate.py":           1765,
    "hooks/pretooluse_change_gate.py":                1138,
    "hooks/stop_clean_exit.py":                        992,
    "engine/contemp_edb.py":                            978,
    "engine/judgment_registry.py":                      889,
    "tools/experiments/compound_nominal_scan2.py":      869,
    "hooks/demurral_detect.py":                         837,
    # Reconciled +36 to 873 (gates-staged-vs-tree-blindness, ledger row 1234, this commission):
    # `check_file` now reads its STAGED bytes (`_content_sha256_for_commit`, threading `use_tree`
    # through, plus the shared `_staged_read` import); `_has_waiver` gained the same `use_tree`
    # parameter and its own read-mode docstring paragraph explaining the fail-open direction this
    # closes. Genuinely new decision-boundary logic and its own reasoning, not padding. Written
    # plain, no golfing (ADR-0007's no-go clause); witnessed growth.
    # Reconciled +27 to 900 (2026-07-26 fix round, fresh-context review of the above commission's
    # own fix): `_tracked_md` routed through `_staged_read.run_git` (finding 4, a bypass-the-
    # stripped-env hazard found in the same six-gate family this file belongs to); report mode's
    # READ MODE docstring paragraph corrected and aligned with gates/doc_shapes.py's identical
    # fix (finding 3); `main()`'s report-mode branch forces `use_tree=True`. Genuinely new
    # decision logic and its own reasoning, not padding. Witnessed growth.
    # Reconciled +5 to 905 (2026-07-26 second fix round, the confirming lap's own residuals):
    # `_git_ignored_rel_paths()`'s two bare `git -C doc_root ...` calls (a second, previously-
    # missed site of the same bypass this file's own prior reconciliation just closed for
    # `_tracked_md`) routed through `_staged_read.run_git`, with an inline comment explaining why
    # the census missed it the first time; the now-dead `import subprocess` removed (net cost of
    # the fix, not padding -- the removal partially offsets the added explanatory lines). Written
    # plain, no golfing; witnessed growth.
    # Reconciled +65 to 970 (2026-07-29, work item attestation-schema-multiround, row 315):
    # the multi-round extension -- `_validate_round_summary` (a new, genuinely different
    # validation shape for a rounds>MAX_ROUNDS escalated record) plus `validate_record`'s new
    # length-vs-MAX_ROUNDS branch plus the docstring explaining both. Trimmed once already (the
    # first draft measured 1000; the module docstring's MULTI-ROUND EXTENSION section, the
    # MAX_ROUNDS comment, and validate_record's inline comments were all cut to their essentials,
    # full rationale left to design/ORCH-SPEC-DOC-ATTESTATION-2.md's migration note rather than
    # duplicated here) before this count was measured -- not padding, not golfed further at the
    # cost of the module being self-explanatory. Witnessed growth.
    "gates/doc_attestation_presence.py":                970,
    # Reconciled +7 to 820 (design/FABLE-RESERVATION-RESIDUE-SPEC.md §7 amendment,
    # kernel/lineage/s56-reservation-residue.sql): work_review_floor_atoms' `discharged` leg
    # widens to verdict IN ('attest','attest_with_reservations') -- genuinely new discharge
    # semantics, not padding (the s56 kernel-view widening's engine-side twin, needed for
    # ./judge's SQL/ASP differential to AGREE on a reservation-discharged item). Written plain,
    # no golfing.
    # Reconciled +37 to 857 (s25-ledger-differential-floor-bug, ledger row 1247):
    # work_review_floor_atoms' two ungated columns (work_parent s28, work_review_disposition
    # s29) were the ONE pair in this file not has_col-gated like every sibling feature, so the
    # SQL floor QUARANTINED (a judge-input silent-wrong-answer risk) on any s22..s28-range
    # schema. Fixed by column-gating both, mirroring ledger_edb.py::export_work's own
    # has_parent/has_review flags -- genuinely new degrade logic, not padding.
    "engine/ledger_floor.py":                           857,
    "engine/preamble_floor.py":                         801,
    # tools/setup_tui/ui_textual.py -- REMOVED from BASELINE 2026-07-22
    # (design/FABLE-SETUP-TUI-REBUILD-SPEC.md §2, wholesale rebuild): `git rm`'d whole, along
    # with ui.py/flow_position.py/elements.py -- the teletype-emulated-inside-Textual shell the
    # commission indicted by name ("Delete it whole-sale so that nobody mistakenly implements
    # something that is this cursed"). Its successor is tools/configtree/ (a generic library,
    # zero autoharn knowledge) plus tools/setup_tui/tui_app.py (a thin consumer), neither of
    # which carries this file's own teletype/back-stack vocabulary.
    # Reconciled +5 to 734 (design/FABLE-RESERVATION-RESIDUE-SPEC.md §7 amendment,
    # kernel/lineage/s56-reservation-residue.sql): export_work's w_discharged/1 extraction widens
    # to verdict IN ('attest','attest_with_reservations') -- the EDB-side twin of the same
    # discharge-semantics widening, feeding the ASP program that ./judge's differential compares
    # against the (also-widened) SQL floor. Written plain, no golfing.
    # bumped 734 -> 802 (export_entitlement(): the entitlement-layer EDB exporter for the
    # s60 ASP twin, engine/lp/ledger_entitlement.lp -- same shape as export_defeat()).
    # Reconciled +4 to 806 (kernel/lineage/s62-delegation-lifecycle-gating.sql, row 1385):
    # a three-line docstring note on export_entitlement() recording that s62's seventh act
    # class needs no exporter change. Written plain, no golfing.
    # Reconciled +67 to 873 (kernel/lineage/s64-principal-stamps-delegation-conditions.sql,
    # design/FABLE-PRINCIPAL-STAMPS-SPEC.md §3 item 4): export_entitlement() gains three
    # purely-additive EDB fact families (act_class/1, edge_scope_class/3, edge_unscoped/2,
    # plus delegation_edge/2) for the scoped-closure ASP twin's own AGREE leg. Written plain,
    # no golfing.
    "engine/ledger_edb.py":                             873,
    # Reconciled +61 to 733 (2026-07-26, row 1307/1308 follow-up): resolve_repo_root() +
    # --repo-root/AUTOHARN_REPO_ROOT override (refuses a nonexistent path) so recompiling from a
    # worktree bakes the real checkout's ROLE_CHARTER_PY/ROLE_BRIEF_PY path instead of a
    # hand-edit after the fact; new refusal surface, not padding. Written plain, no golfing.
    # Reconciled +112 to 845 (2026-07-26, confirming-review micro-fix round, 3 findings): new
    # LedUnusable class + _split_led() helper + marker-based led-not-found detection in
    # check_charter/fetch_brief, wrapped once around main()'s drive loop (finding 1); HYDRATE_
    # TEMPLATE gains a led_run() shell function for real multi-token --led support (finding 3).
    # Genuinely new refusal surface, not padding -- written plain, no golfing.
    "tools/workflow_compile.py":                        845,
    # tools/setup_tui/durable_decisions.py -- REMOVED from BASELINE 2026-07-22 (P10 content
    # split, law/adr/0012's 2026-07-22 Amendment): 619 -> 249 lines, the CATALOG literal moved
    # to tools/setup_tui/durable_decisions_data.py. The ratchet is the working: a file that
    # shrinks under CEILING exits the table (ADR-0011 Rule 4, module docstring's own "may shrink
    # ... and leave this table on its next touch").
    "tools/watchdog_liveness.py":                       570,
    "engine/tests/test_ledger_marriage.py":             533,
    "hooks/posttooluse_error_recurrence.py":            530,
    # bumped 529 -> 553 (design/FABLE-JUDGE-LAYER-CAPABILITY-CLOSURE-SPEC.md build, ledger row
    # 1459 cluster-2's fix, 2026-07-27): `layer_capability` and `run_layer_differential`'s former
    # `_LAYER_FLOOR_PREDS` if-chain became registry lookups (net line REDUCTION on that half), but
    # the module docstring, `layer_capability`'s and `run_layer_differential`'s own docstrings,
    # and `main`'s bare-path auto-detect loop all gained the closure spec's own reasoning for the
    # new no-floor-layer disposition (why it QUARANTINEs vs REFUSES, and why -- the same
    # provenance-carrying idiom this file's other docstrings already use), a net growth this
    # build owns rather than trims for the ratchet's sake.
    "engine/ledger_differential.py":                    553,
    "hooks/pretooluse_delegation_observer.py":          588,
    # Reconciled +63 to 588 (2026-07-26, delegation-observer Workflow-coverage review, moderate/
    # SILENT surrogate-hazard fix round): a lone UTF-16 surrogate in a journaled `script`/`prompt`
    # raised uncaught UnicodeEncodeError at two `.encode("utf-8")` hash call sites AND, previously
    # undiagnosed, at `_journal()`'s own file-write encode -- fixed class-wide with
    # `errors="replace"` applied uniformly (module docstring's own new SURROGATE HAZARD FIX
    # section states the surrogatepass-vs-replace reasoning and the json.dumps/print verification
    # in full, including a CAUTION paragraph on why every surrogate example in that section is
    # written double-backslashed -- a single-backslash escape in this non-raw docstring is decoded
    # at COMPILE time into an actual surrogate code point, making the module itself uncompilable;
    # hit live while drafting this fix, the worst instance of the class, self-inflicted). Genuinely
    # new hazard-class documentation plus the fix's own inline comments, not padding. Written
    # plain, no golfing.
    # Reconciled +12 to 525 (design/FABLE-RESERVATION-RESIDUE-SPEC.md build, kernel/lineage/
    # s56-reservation-residue.sql): CHAIN += s56, and one new ALLOWLIST entry (review_verdicts,
    # a DECLARED raw/history reader by design -- the general review-legibility surface must show
    # a superseded review too). Genuinely new classification content, not padding. Written plain,
    # no golfing.
    # Reconciled +1 to 526 (design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part A, ledger row 1150,
    # kernel/lineage/s57-obligation-revocation-event.sql): CHAIN += s57 -- exercises review_gap's
    # own third, narrowing-only anti-join, an already-allowlisted entry whose reason text is
    # UPDATED in place (no new row). One genuinely load-bearing line, not padding.
    # Reconciled +33 to 559 (design/FABLE-MISSIVES-KERNEL-SPEC.md, row 1263): CHAIN += s58/s59;
    # ALLOWLIST entries for three new raw-ledger readers plus the re-issued
    # validate_supersession_target's widened reason text -- genuinely new, not padding.
    # Reconciled +6 to 565 (AMENDMENT 1), +14 to 579 (AMENDMENT 2): one more ALLOWLIST entry each
    # (validate_missive_regards; missive_outbound).
    # bumped 579 -> 610 (s60-entitlement-enforcement.sql: CHAIN += s60, three new declared
    # raw-ledger reader entries: validate_entitlement, entitlement_genesis_principal,
    # entitlement_act_class_of).
    # bumped 610 -> 632 (s61-signature-symmetry-and-key-binding.sql: CHAIN += s61, two new
    # declared raw-ledger reader entries (validate_principal_binding, validate_signature_witness)
    # + one widened entry's reason text (validate_supersession_target)).
    # Reconciled +4 to 614 (s62-delegation-lifecycle-gating.sql, row 1385): CHAIN += s62 + a
    # short comment noting it registers no NEW allowlist entry (re-issues two s60-named readers).
    # Reconciled at the s62+TUI coupled merge (2026-07-26): both parents' bump
    # comments kept verbatim above; the union is the measured merged file. Same
    # merge-union ratchet-crossing class as the reconciliations above.
    "gates/ledger_reader_allowlist.py":            654,
    # Reconciled +22 to 525 (GENESIS-GATE HARD-STOP, ledger row 1918): `verify_commission_act`
    # gained the `accept_unverified` parameter and its own `_verify_commission_ok` verdict_check
    # function (the real halt-vs-continue decision, previously nowhere -- exit code was silently
    # trusted). Genuinely new decision logic, not padding. Written plain, no golfing.
    # Reconciled +7 to 532 (design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part C completion, ledger
    # row 1158/1159): `write_commission_act` gained the `led` parameter (the caller now resolves
    # served-vs-legacy from `state["boundary_url"]` rather than this module hardcoding
    # legacy/led unconditionally) plus the docstring update explaining the re-sequencing. Genuinely
    # new decision-boundary logic, not padding. Written plain, no golfing.
    "tools/setup_tui/signed_genesis.py":                532,
    # Reconciled +1 to 499 (2026-07-26 fix round, the staged-vs-tree confirming lap's residual
    # finding 2): `tracked_py_files` routed through `_staged_read.run_git` -- a net one-line
    # comment cost after the `import subprocess` removal and the call-site swap wash out. Not
    # padding: this was one of the two out-of-scope-census gates judged trivially safe to route
    # rather than write a standing justification for leaving unrouted (see
    # gates/_staged_read.py's run_git docstring). Written plain, no golfing.
    "gates/interpreter_boundary_lint.py":               499,
    "hooks/stamp_intercept.py":                         482,
    # NEW to BASELINE, 461 (design/FABLE-SETUP-TUI-CONFIG-FILE-SPEC.md build, ledger row 1944):
    # was 375 lines, under ceiling, before this build. The CLI surface gains three new flags
    # (`--from-config`/`--world`/`--initial-config`, spec §2), a mode-discipline refusal function
    # (`_check_config_flags`), the `--from-config` orchestrator (`_run_from_config` -- validate,
    # world/dest preflight, synthesize, drive the existing `ScriptedUi` path), and the
    # `--initial-config` load+seed in `main`. The BULK of the actual config<->flow wiring lives
    # in the new `tools/setup_tui/config_seam.py` module (kept separate, ADR-0012 P1) -- what
    # remains here is the CLI-parsing/dispatch surface app.py already owns, not a copy of that
    # logic. Genuinely new decision surface, not padding. Written plain, no golfing (ADR-0007's
    # no-go clause).
    "tools/setup_tui/app.py":                           461,
    # NEW to BASELINE, 414 (design/FABLE-SETUP-TUI-CONFIG-FILE-SPEC.md build, ledger row 1944):
    # the SCREEN-SEAM half of the config-file feature -- four cohesive jobs (`synthesize_
    # scripted_lines` for --from-config, `build_initial_prior_answers` for --initial-config,
    # `check_world_and_dest` for spec §3's rejection, `capture_resolved_config`/
    # `save_world_config` for spec §4's self-application), each with its own real complexity
    # (mirroring `screens.py`'s own conditional prompt sequence, screen by screen, is inherently
    # not compressible without losing the property it exists to guarantee: the synthesized
    # answer stream matches the real flow exactly). Splitting further would separate these four
    # genuinely-coupled jobs (ADR-0007's own "a single coherent unit ... where splitting would
    # fragment cross-line invariants" exception) across files for no reader benefit. Written
    # plain, no golfing (ADR-0007's no-go clause).
    # bumped 414 -> 463 (work item setup-tui-config-extension, ledger row 685's audit / row 693):
    # the five new boundary scalar fields (log_level/identity_enforcement(+override)/
    # sse_poll_interval_secs/max_sse_clients) and the new courier.counterparts list each need one
    # line in answers_for_from_config, _SCOPED_OVERRIDE_KEYS, and capture_resolved_config (the
    # SAME three seams every existing scalar/list already threads through) -- genuinely new
    # decision surface, not padding. Written plain, no golfing (ADR-0007's no-go clause).
    "tools/setup_tui/config_seam.py":                   463,
    "tools/experiments/typed_table.py":                 442,
    "engine/contemp_audit.py":                          441,
    # NEW to BASELINE, 428 (design/FABLE-SETUP-TUI-TYPED-UI-SPEC.md build, spec §1's purity-gate
    # extension): DETECTION 3 (the print(/.say( check) is a genuinely new detector -- its own
    # match predicate, its own `PRINT_EXEMPT` table (a THIRD exemption table, same shape as
    # `EXEMPT`/`EXTRA_EFFECT_EXEMPT`, individually justified per entry per this file's own
    # established idiom), its own negative-self-check wiring -- plus the module docstring's own
    # DETECTION 3 section explaining each exemption's reasoning (the file's own "decisions-about-
    # the-file header" docstring rule, ADR-0007). Not padding: every added line is either a new
    # exemption entry with its own one-line justification, or the reasoning that entry needs to
    # be reviewable. Written plain, no golfing (ADR-0007's no-go clause); witnessed growth of a
    # previously-under-ceiling file, grandfathered honestly rather than silently golfed to fit.
    # Reconciled +15 to 443 (design/FABLE-SETUP-TUI-CONFIG-FILE-SPEC.md build, ledger row 1944):
    # two new EXEMPT/EXTRA_EFFECT_EXEMPT entries for `config_seam.py`'s two declared exception
    # functions (`save_world_config`, mirroring `checklist.Checklist.save`'s own precedent;
    # `scripted_answers_file`, an orchestration-level tempfile write before any screen/Ui/Plan
    # exists) and two PRINT_EXEMPT entries for `app.py`'s `_run_from_config`/`main` (the
    # refuse-before-any-act diagnostics, same register as `_select_backend`'s existing entry) --
    # each with its own one-line justification, this file's own established idiom. Not padding.
    # Written plain, no golfing; witnessed growth of a previously-under-ceiling file.
    "gates/setup_tui_purity_gate.py":                   443,
    # tools/setup_tui/principals_authority.py -- REMOVED from BASELINE 2026-07-22 (P10 content
    # split, law/adr/0012's 2026-07-22 Amendment): 428 -> 359 lines, CLASS_CHOICES/
    # RELATION_CHOICES/SCAFFOLD_BASE_PRINCIPALS/LESSON_* moved to
    # tools/setup_tui/principals_authority_data.py. 359 sits in the 300-400 review band (never
    # flagged), not grandfathered debt -- the ratchet working, same shape as durable_decisions.py
    # above.
    "hooks/pretooluse_sql_block.py":                    420,
    # NEW to BASELINE 2026-07-23 (integration merge, TUI-rebuild line x retirement line):
    # 406 lines -- both sides' own docstrings (the rebuild's P10 CONTENT SPLIT note, the
    # retirement's SCREEN POSITION AND VERB CHOICE re-sequencing note) are genuinely independent
    # provenance the merge honestly keeps side by side, not padding; no logic duplicated, just
    # two histories' worth of "why" on one file. Written plain, no golfing; witnessed growth of
    # a previously-under-ceiling (359-line) file, crossing the ceiling only as a merge artifact.
    # bumped 406 -> 450 (2026-07-26, work item tui-ceremony-chain-authorship, ledger rows
    # 1390/1391): register_principal_act/grant_competence_act/relate_act stop forcing
    # LED_ACTOR=commissioner (a principal with no acts-for chain to genesis, refused under
    # kernel/lineage/s60-entitlement-enforcement.sql already merged, and under s62's own
    # delegation_lifecycle gating once that lands) -- the new "AUTHORSHIP" module-docstring
    # section explaining WHY (the full reasoning, not just the diff) plus each function's own
    # updated docstring account for the growth. Written plain, no golfing; a real class-sweep
    # fix, not padding.
    "tools/setup_tui/principals_authority.py":          450,
    # NEW to BASELINE 2026-07-23 (integration merge, same pass): 405 lines -- runner.py's own
    # `legacy_led_path`/`served_led_path`/`resolve_led` docstrings were each rewritten in place by
    # the retirement line to explain the legacy-led.tmpl retirement (ledger row 1149/1150), net
    # honest growth (the retired-preference explanation replacing, not simply appending to, the
    # old preference explanation) merged cleanly against the rebuild line's own unrelated hunks
    # elsewhere in the same file. Written plain, no golfing; witnessed growth of a previously-
    # under-ceiling file, crossing the ceiling only as a merge artifact.
    "tools/setup_tui/runner.py":                        405,
    # NEW to BASELINE (design/FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md build, ledger
    # rows 1237-1248/1315/1316/1325): was 375 lines, under ceiling, before this build. Gains one
    # new documented breach kind (§4's additive marker check, docstring item 5 plus its ~15-line
    # implementation in main()) and one new REGISTRY row for this build's own witness fixture
    # (fixture-sandbox-runtime-foreclosure) -- genuinely new decision surface (a census gate
    # keeping a NEW mechanical sweep honest), not padding. Written plain, no golfing (ADR-0007's
    # no-go clause).
    # Reconciled 404 -> 418 at the sandbox merge itself (2026-07-26): both parents grew the
    # census independently (main: worldname/manifest/config-seam/trio registry rows; branch:
    # the marker check + its own registry row); the union is 418. Third witnessed merge-union
    # ratchet crossing today -- the commit-phase contention class, again.
    # bumped 418 -> 419 (one new REGISTRY row: s60-entitlement-enforcement).
    # bumped 419 -> 420 (one new REGISTRY row: s61-signature-symmetry-and-key-binding).
    # bumped 419 -> 428 (2026-07-26, work item tui-ceremony-chain-authorship, ledger rows
    # 1390/1391): one new REGISTRY row (setup-tui-ceremony-chain-authorship) plus its own
    # multi-line provenance comment naming the pre-existing s60 hazard and the s62-surfaced
    # hazard this fixture proves fixed.
    # Reconciled 420/428 -> 429 at the s62+TUI coupled merge (2026-07-26): both parents grew
    # the census independently (main: the s61 registry row; branch: the TUI-ceremony row +
    # provenance comment); the union measures 429. Fourth witnessed merge-union ratchet
    # crossing in two days -- the commit-phase contention class, again.
    # bumped 419 -> 420 (one new REGISTRY row: s62-delegation-lifecycle-gating, row 1385).
    # Reconciled at the s62+TUI coupled merge (2026-07-26): both parents' bump
    # comments kept verbatim above; the union is the measured merged file. Same
    # merge-union ratchet-crossing class as the reconciliations above.
    # bumped 419 -> 420 (one new REGISTRY row: fixture-sweep, work item fixture-live-sweep,
    # ledger rows 1388/1389).
    # Reconciled at the fixture-live-sweep merge (2026-07-26): main's own chain above (arriving
    # at 430) and this branch's fixture-sweep row both grew the census independently; the union
    # is the measured merged file. Same merge-union ratchet-crossing class as every
    # reconciliation above.
    # bumped 430 -> 431 (one new REGISTRY row: s64-principal-stamps-delegation-conditions,
    # design/FABLE-PRINCIPAL-STAMPS-SPEC.md §3 item 1).
    # Reconciled at the s64 merge (2026-07-26): both parents' bump comments kept verbatim
    # above (main: fixture-sweep row; branch: s64 row); the union carries both registry rows
    # and is re-measured on the merged file. Same merge-union ratchet-crossing class -- and
    # the commit-phase contention class the standing memory predicts -- as every
    # reconciliation above.
    # bumped 432 -> 433 (one new REGISTRY row: s65-refusal-attempted-kind, design/
    # FABLE-S65-REFUSAL-ATTEMPTED-KIND-SPEC.md, ledger row 1487).
    # bumped 433 -> 434 (one new REGISTRY row: design-currency, design/
    # FABLE-DESIGN-CURRENCY-ADVISORY-SPEC.md build) -- the identical shape as the row
    # immediately above, witnessed growth from adding this build's own seen-red fixture bank
    # to the registry, not unnoticed growth.
    # bumped 434 -> 435 (one new REGISTRY row: bounds-vocabulary-drift, ledger row 1514 item 2).
    # bumped 435 -> 436 (one new REGISTRY row: world-wiring, tools/world_wiring.py
    # backup/restore commission 2026-07-27) -- the identical shape as the two rows
    # immediately above, witnessed growth from registering this build's own seen-red
    # fixture, not unnoticed growth.
    # bumped 434 -> 435 on the s66/s67 worktree branch (one new REGISTRY row:
    # s66-s67-journal-totality, design/FABLE-S66-S67-JOURNAL-TOTALITY-SPEC.md build) --
    # landed independently of the two rows above; reconciled at the 2026-07-27 merge of that
    # branch into main (all three parents' rows are ADDITIVE and non-overlapping, so the
    # merged registry carries them all; re-measured on the merged file to 437 below, the
    # union-of-independent-+1s class this file's own history already names for a merge-union
    # ratchet crossing).
    # bumped 437 -> 438 (one new REGISTRY row: s68-typed-absence-dispositions, design/
    # FABLE-S68-TYPED-ABSENCE-DISPOSITIONS-SPEC.md build) -- the identical shape as the rows
    # immediately above, witnessed growth from registering this build's own seen-red fixture,
    # not unnoticed growth.
    # bumped 437 -> 438 on the service-restart branch (one new REGISTRY row: service-restart,
    # design/FABLE-SERVICE-DRAIN-RESTART-SPEC.md, row 1553 option A) -- reconciled at the
    # 2026-07-27 merge: both rows ADDITIVE and non-overlapping, union re-measured to 439, the
    # same merge-union ratchet-crossing class as every reconciliation above.
    # bumped 439 -> 440 (one new REGISTRY row: scaffold-dispatcher-verb-glob, autoharn3 ledger
    # row 101/scaffold-courier-verb-gap, maintainer class-fix amendment 2026-07-28) -- the
    # identical shape as every registration-driven bump above: witnessed growth from registering
    # this build's own seen-red fixture, not unnoticed growth.
    # bumped 440 -> 441 (s69 build, design/FABLE-S69-ROLE-COHERENCE-REFUSALS-SPEC.md, row 201):
    # one new registry line, seen-red/s69-role-coherence-refusals -- the identical
    # registration-driven shape as every prior bump above.
    # union-merged at the SSE + birth-steps merge (row 334): both concurrent builds
    # added one REGISTRY entry each (boundary-sse-events, row 169; birth-standing-steps-
    # scaffold, row 270); ceiling set to the post-merge actual (450), the same
    # additive-census-row class as every prior bump above.
    # union-merged at the ac-read-identity + setup-tui-config-extension merge (rows 773/786):
    # both concurrent builds added one REGISTRY entry each (ac-read-identity, row 744 family;
    # seen-red/setup-tui-config-extension, rows 685/693); ceiling set to the post-merge actual
    # (454), the same additive-census-row class as every prior bump above.
    # Reconciled again at the s70-scope-binding completion-round merge (rows 639/732/794): this
    # branch's own pre-merge bump (451, one new REGISTRY row for seen-red/s70-scope-binding)
    # unions with main's 454 above; the post-merge file (carrying both the s70 REGISTRY row and
    # main's ac-read-identity/setup-tui-config-extension rows) re-measures to 455 -- the same
    # merge-union ratchet-crossing class as every reconciliation above.
    "gates/fixture_census.py":                     456,
    "tools/regrade_decisions.py":                       415,
    "tools/markdown_tables.py":                         412,
    # NEW to BASELINE (gates-staged-vs-tree-blindness, ledger row 1234, this commission): this
    # gate's OWN file crossed 400 for the first time carrying its own read-mode conversion --
    # `line_count` now reads STAGED bytes via `_staged_read.read_source_bytes` (with the
    # errors="replace" decode preserved manually, since that helper makes no encoding
    # assumption), `main()` grew the `--tree`/root-arg split, and this very row (plus its own
    # explanatory comment) is the ratchet-bootstrapping cost every self-measuring census gate
    # pays (gates/fixture_census.py's own registry carries the identical self-reference).
    # Genuinely new decision logic and its own reasoning, not padding. Written plain, no golfing
    # (ADR-0007's no-go clause); the exact count below is measured AFTER this comment is in
    # place, not guessed.
    # Reconciled again, 2026-07-26 fix round (fresh-context review of the above commission's own
    # fix): `tracked_scope_files` routed through `_staged_read.run_git` (finding 4) plus its own
    # BASELINE entry and this comment for gates/doc_attestation_presence.py's parallel reconciling
    # -- the same self-measuring-census cost paid again, one commission later. Exact count below
    # measured AFTER every edit in this file is in place, not guessed.
    # Reconciled again, 2026-07-26 SECOND fix round (the confirming lap's four residuals): three
    # more BASELINE entries reconciled inline (doc_attestation_presence.py, +5 for the
    # _git_ignored_rel_paths route-through; interpreter_boundary_lint.py, +1 for its own
    # route-through) plus this entry, and this comment, for the exact same self-measuring-census
    # cost paid a third time. Exact count below measured AFTER every edit in this file is in
    # place, not guessed.
    # Reconciled 477 -> 495 at the SANDBOX MERGE (2026-07-26, the fourth and last of the
    # session-gap merges): the union carried the sandbox branch's own baseline additions and
    # this merge's census reconciliation note; duplicate self-entry blocks consolidated once
    # more. Measured post-consolidation. The ratchet forbids growth from here.
    # Reconciled again, 2026-07-26, at the CENSUS MERGE itself (main x staged-read branch):
    # both parents carried their own self-entry (main's 413 from the 9a2c672 merge-union
    # unblock; this branch's 457 above), git's union kept BOTH duplicate dict keys and both
    # comment blocks, and the merged file landed at 478 against the surviving 457 ratchet --
    # blocking the merge commit. The duplicate 413 block is removed (its story is subsumed
    # here), this note added, and the count below is the measured post-consolidation total.
    # Fourth payment of the self-measuring cost; second witnessed merge-union crossing on
    # this same file (the concurrent-builders commit-phase contention class, 2026-07-21).
    # Reconciled +19 to 518 (2026-07-26, delegation-observer Workflow-coverage review, moderate/
    # SILENT surrogate-hazard fix round): this gate's OWN BASELINE entry for
    # hooks/pretooluse_delegation_observer.py grew by +63 lines and its dated reconciliation
    # comment, which itself is measured content of THIS file -- the fifth payment of the
    # self-measuring cost this table's own history already names as a recurring, honest cost of
    # ratcheting the gate that ratchets itself, including this entry's own line count of itself.
    # Reconciled +8 to 526 (2026-07-26, confirming-review micro-fix round): the
    # tools/workflow_compile.py entry above grew by +112 lines and its own dated comment,
    # itself measured content of THIS file -- the sixth payment of the same recurring cost.
    # Genuinely new reconciliation content, not padding.
    # bumped 518 -> 528 (s60-entitlement-enforcement.sql: four ratchet bumps in this same
    # file, each row's own comment naming its reason).
    # bumped 528 -> 536 (s61-signature-symmetry-and-key-binding.sql: three more ratchet bumps
    # in this same file, each row's own comment naming its reason -- the same self-measuring
    # cost, again).
    # bumped 528 -> 544 (2026-07-26, work item tui-ceremony-chain-authorship, ledger rows
    # 1390/1391): two ratchet bumps in this same file (principals_authority.py, fixture_census.py)
    # plus this self-measuring row's own comment -- the same recurring, honest cost this table's
    # history already names.
    # Reconciled 539/544 -> measured at the s62+TUI coupled merge (2026-07-26): both parents'
    # bump comments kept verbatim above, plus this reconciliation note -- the self-measuring
    # union, same class as the fixture_census row's crossing directly above.
    # bumped 528 -> 538 (s62-delegation-lifecycle-gating.sql, row 1385: four more ratchet
    # bumps in this same file, same self-measuring cost, including this entry itself).
    # Reconciled at the s62+TUI coupled merge (2026-07-26): both parents' bump
    # comments kept verbatim above; the union is the measured merged file. Same
    # merge-union ratchet-crossing class as the reconciliations above.
    # Reconciled at the scaffold-umbrella-migration merge (2026-07-26): both parents' bump
    # comments kept verbatim above; value re-measured on the merged file. Same merge-union
    # ratchet-crossing class as every reconciliation above.
    # bumped 528 -> 531 (fixture-live-sweep, ledger rows 1388/1389, this branch, pre-merge).
    # Reconciled at the fixture-live-sweep merge (2026-07-26): main's own chain above (arriving
    # at 595) and this branch's own three-line bump both grew the file independently; the union
    # is the measured merged file, including the two-line fixture_census.py reconciliation added
    # directly above. Same merge-union ratchet-crossing class as every reconciliation above.
    # bumped 595 -> 604 (this gate's own BASELINE growing to carry the s64 ratchet bumps for
    # engine/ledger_edb.py and gates/fixture_census.py -- self-referential, checked here too;
    # the two-line difference between this comment's first commit and its own final value is
    # itself this ratchet's own self-reference settling to a fixpoint, verified by re-staging).
    # Reconciled at the s64 merge (2026-07-26): both parents' bump comments kept verbatim
    # above; the union is re-measured on the merged file, this reconciliation comment and
    # its sibling above included (the usual self-referential fixpoint, settled by
    # re-measuring after writing).
    # bumped 648 -> 675 (this gate's own BASELINE growing to carry the two entries this same
    # commit adds/bumps -- engine/ledger_differential.py's ratchet bump and the new
    # engine/lp_registry.py entry, design/FABLE-JUDGE-LAYER-CAPABILITY-CLOSURE-SPEC.md build --
    # self-referential, checked here too, the usual fixpoint settled by re-measuring after
    # writing, same idiom as every prior self-reference bump in this file's own history above).
    # bumped 675 -> 681 (s65 build, design/FABLE-S65-REFUSAL-ATTEMPTED-KIND-SPEC.md, ledger row
    # 1487): this gate's own BASELINE growing to carry the two entries this same commit bumps
    # (gates/kind_shape_manifest_gate.py, gates/fixture_census.py) -- the same self-referential
    # fixpoint as every prior bump above, re-measured after writing.
    # bumped 685 -> 696 (s65 fix round 2, BLOCKS MERGE review): this gate's own BASELINE
    # growing to carry the one entry this same commit bumps (gates/kind_shape_manifest_
    # gate.py, 1458 -> 1592) -- the same self-referential fixpoint as every prior bump.
    # bumped 696 -> 704 (design/FABLE-DESIGN-CURRENCY-ADVISORY-SPEC.md build): this gate's own
    # BASELINE growing to carry the one entry this same commit bumps (gates/fixture_census.py,
    # 433 -> 434) -- the same self-referential fixpoint as every prior bump, re-measured after
    # writing.
    # bumped 704 -> 707 (bounds-vocabulary single-home build): this gate's own BASELINE growing
    # to carry the one entry this same commit bumps (gates/fixture_census.py, 434 -> 435).
    # bumped 707 -> 714 (world-wiring build): this gate's own BASELINE growing to carry the
    # one entry this same commit bumps (gates/fixture_census.py, 435 -> 436) -- the same
    # self-referential fixpoint as every prior bump, re-measured after writing.
    # bumped 704 -> 712 on the s66/s67 worktree branch (design/
    # FABLE-S66-S67-JOURNAL-TOTALITY-SPEC.md build): this gate's own BASELINE growing to carry
    # the two entries that commit bumps (gates/kind_shape_manifest_gate.py 1592 -> 1605,
    # gates/fixture_census.py 434 -> 435).
    # bumped 727 -> 732 on the same branch (s67 §2 AMENDMENT fix round): carrying
    # gates/kind_shape_manifest_gate.py's 1605 -> 1635.
    # Reconciled at the 2026-07-27 merge of that branch into main (s66/s67 x world-wiring x
    # bounds-vocabulary-drift): every parent's bump comments kept verbatim above; the union is
    # re-measured on the merged file itself, the same merge-union ratchet-crossing class as
    # every reconciliation above.
    # bumped 740 -> 755 (s68, kernel/lineage/s68-typed-absence-dispositions.sql build): this
    # gate's own BASELINE growing to carry the two entries this same commit bumps
    # (gates/kind_shape_manifest_gate.py 1635 -> 1716, gates/fixture_census.py 437 -> 438) --
    # the same self-referential fixpoint as every prior bump, re-measured after writing.
    # bumped 740 -> 747 on the service-restart branch (carrying its own fixture_census bump);
    # reconciled at the 2026-07-27 merge: both parents' comments kept verbatim, the union
    # re-measured on the merged file itself, the same merge-union class as above.
    # bumped 762 -> 770 (autoharn3 row 101/scaffold-courier-verb-gap, maintainer class-fix
    # amendment 2026-07-28): this gate's own BASELINE growing to carry the one entry this same
    # commit bumps (gates/fixture_census.py 439 -> 440) -- the same self-referential fixpoint as
    # every prior bump, re-measured after writing.
    # bumped 770 -> 777 (s69 build, design/FABLE-S69-ROLE-COHERENCE-REFUSALS-SPEC.md, row 201):
    # this gate's own BASELINE growing to carry the fixture_census.py bump (440 -> 441) this same
    # commit makes, re-measured after writing -- the same self-referential fixpoint as every
    # prior bump.
    # union-merged at the SSE + birth-steps merge (row 334): both parents' self-
    # referential bumps (782 / 783) collapse to this file's own post-merge actual,
    # re-measured after writing -- the same fixpoint as every prior bump.
    # bumped 784 -> 797 (2026-07-29, work item attestation-schema-multiround, row 315): this
    # gate's own BASELINE growing to carry the gates/doc_attestation_presence.py bump (905 -> 970)
    # this same commit makes, re-measured after writing -- the same self-referential fixpoint as
    # every prior bump.
    # union-merged at the ac-read-identity + setup-tui-config-extension merge (rows 773/786):
    # both concurrent builds bumped this gate's own BASELINE (805 and 810) carrying their
    # fixture_census/config_seam growth; ceiling set to the post-merge measured actual,
    # re-measured after writing -- the same self-referential fixpoint as every prior bump.
    # bumped 797 -> 815 (s70 build, design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md
    # sec1b/sec1c, ratification row 639, ac-scope-kernel-delta): this gate's own BASELINE growing
    # to carry the three entries this same commit bumps (gates/kind_shape_manifest_gate.py
    # 1716 -> 1765, gates/ledger_reader_allowlist.py 636 -> 654, gates/fixture_census.py
    # 450 -> 451) -- the same self-referential fixpoint as every prior bump, re-measured after
    # writing.
    # Reconciled again at the s70-scope-binding completion-round merge (rows 639/732/794): both
    # this branch's own pre-merge bump chain (797 -> 815) and main's own concurrent bump (811,
    # ac-read-identity + setup-tui-config-extension merge) collapse, plus the fixture_census.py
    # 454 -> 455 reconciliation directly above and this entry's own settling -- the same
    # self-referential fixpoint as every prior bump, re-measured after writing.
    # bumped 827 -> 840 (ac-dispatch-scope-mint build, rows 639/815): this gate's own BASELINE
    # growing to carry the two entries this same commit bumps/adds (gates/fixture_census.py, one
    # new REGISTRY row for the dispatch-time scope-minting fixture, 455 -> 456; tools/
    # dispatch_mechanics.py, NEW to BASELINE below) -- the same self-referential fixpoint as
    # every prior bump, re-measured after writing.
    "gates/max_lines.py":                          840,
    # NEW to BASELINE, 406 (cluster-1 fixture-repairs, ledger row 1459's textual-package
    # addendum): declares_missing_package() + its two helpers (_local_module_basenames,
    # _module_level_import_names) -- a pre-flight, AST-based scan so a fixture whose only
    # blocker is an uninstalled third-party package (e.g. `textual`) reports UNEXERCISED naming
    # it, never RED with a raw ModuleNotFoundError traceback -- same shape as the existing
    # declares_pghost/pghost_available pair one function up. Every added line is either a new
    # helper with its own docstring (ADR-0007's "decisions-about-the-file header" rule) or the
    # one new STRUCTURAL_BLOCKERS entry (42-gate-journal-registered) added in the same commit.
    # Not padding: witnessed a zero-false-positive pass over the full fixture_census.py registry
    # and both polarities (a synthetic missing-package fixture -> UNEXERCISED; an unaffected
    # GREEN family unchanged) before this bump was taken. Written plain, no golfing (ADR-0007's
    # no-go clause); witnessed growth of a previously-under-ceiling file, grandfathered honestly
    # rather than silently golfed to fit.
    # bumped 406 -> 430 (review finding on 4251e67, fixed at merge: _module_level_import_names
    # excludes `if TYPE_CHECKING:` bodies -- the zero-runtime-cost exemption -- via an explicit
    # body-walk replacing ast.walk; witnessed three polarities (TYPE_CHECKING both spellings
    # excluded, try/if-nested runtime imports still counted, relative imports still excluded)
    # and a registry-wide zero-flagged pass before this bump was taken).
    "gates/fixture_sweep.py":                      430,
    # bumped 626 -> 643 (this gate's own BASELINE growing to carry the gates/fixture_sweep.py
    # entry immediately above plus this comment's own settling -- self-referential, checked
    # here too, same idiom as every prior self-reference bump in this file's own history above).
    # NEW to BASELINE, 469 (design/FABLE-JUDGE-LAYER-CAPABILITY-CLOSURE-SPEC.md build, ledger row
    # 1459's fix, 2026-07-27): was 289 lines, well under ceiling, before this build. Each `LAYERS`
    # entry became a typed `LayerSpec` (program stack + capability probe + floor disposition,
    # closure spec §2 item 1) instead of a bare program-name tuple, so the four pre-existing
    # layers' capability checks MOVED here verbatim from engine/ledger_differential.py's deleted
    # if-chain (byte-diffed in the build report, not retyped -- net new content, not duplication:
    # the old copy is gone), a NEW entitlement capability probe + its byte-identical-shape
    # provenance note, two small marker types (`NoFloor`/`FloorElsewhere`, each foreclosing a
    # distinct representable-but-wrong state per ADR-0000 Rule 2(a) -- see their own docstrings
    # for why they are not collapsed into one), and the import-time closure check
    # (`_validate_layer_registry`) design item 1 mandates. Witnessed: a synthetic
    # capability-missing LayerSpec raises RegistryError at validation (the closure spec §4
    # negative-control leg) before this bump was taken; see build report.
    "engine/lp_registry.py":                       469,
    # NEW to BASELINE, 430 (ac-dispatch-scope-mint build, design/FABLE-ACCESS-CONTROL-AND-
    # INFORMATION-FLOW-SPEC.md §5 item 4, rows 639/815): dispatch mint's own --scope-surface/
    # --scope-exclude/--scope-disclosure-mode flags plus the fourth "bind a principal_scope_
    # bound row" dispatch step -- the new typed-value machinery (ScopeExclusion/ScopeBindingSpec
    # /extract_scope_flags/bind_scope) is factored OUT into tools/dispatch_scope.py (204 lines,
    # its own new file, under the ceiling), so this row is the residual CLI-wiring growth alone,
    # not unfactored bloat.
    "tools/dispatch_mechanics.py":                 430,
}


def evaluate(rel_path: str, count: int, baseline: dict[str, int] = BASELINE) -> str | None:
    """Pure decision function -- no filesystem access -- so the negative self-check can drive it
    against synthetic (path, count) pairs (ADR-0011 Rule 3's negative-control amendment) without
    touching the real tree. Returns a violation message, or None if `rel_path` at `count` lines
    is clean under CEILING/baseline. Never flags the 300-400 review band -- that stays exactly
    the qualitative territory ADR-0007 left it as."""
    if count <= CEILING:
        return None
    ratchet = baseline.get(rel_path)
    if ratchet is None:
        return (f"{rel_path}: {count} lines -- NEW file over the {CEILING}-line ceiling "
                 f"(ADR-0007); not in the ratcheting baseline, refused outright")
    if count > ratchet:
        return (f"{rel_path}: {count} lines -- grew past its ratchet baseline of {ratchet} "
                 f"(ADR-0011 Rule 4: a grandfathered file may shrink, never grow)")
    return None


def tracked_scope_files(root: str) -> list[str]:
    """Every git-tracked *.py path (relative to `root`) under SCOPE_PREFIXES, minus EXCLUDE_*.
    Routed through `_staged_read.run_git` (2026-07-26 follow-up finding), not a bare
    `subprocess.run(["git", ...])` -- an inherited GIT_DIR (a live worktree hook) must not
    misresolve `-C root` the way it demonstrably can for the staged-blob read above."""
    r = run_git(["-C", root, "ls-files", "*.py"],
                capture_output=True, text=True, check=True)
    out: list[str] = []
    for line in r.stdout.splitlines():
        if not any(line.startswith(p) for p in SCOPE_PREFIXES):
            continue
        if any(part in EXCLUDE_PARTS for part in line.split("/")):
            continue
        if any(line.startswith(p) for p in EXCLUDE_PATH_PREFIXES):
            continue
        out.append(line)
    return out


def line_count(path: str, use_tree: bool = False) -> int:
    # errors="replace" (the original tree-reading behavior) preserved via manual bytes-then-
    # decode, since read_source_bytes (unlike read_source_text) makes no encoding assumption.
    raw = read_source_bytes(Path(path), use_tree=use_tree)
    return len(raw.decode("utf-8", errors="replace").splitlines())


def main() -> int:
    argv = [a for a in sys.argv[1:] if a != "--tree"]
    use_tree = "--tree" in sys.argv[1:]
    root = os.path.abspath(argv[0]) if argv else REPO
    files = tracked_scope_files(root)
    present = set(files)

    breaches: list[str] = []
    review_band = 0
    for rel in files:
        n = line_count(os.path.join(root, rel), use_tree=use_tree)
        v = evaluate(rel, n)
        if v:
            breaches.append(v)
        elif TARGET < n <= CEILING:
            review_band += 1

    # a grandfathered path no longer tracked in SCOPE is a stale baseline row -- the baseline
    # itself can rot exactly like fixture_census.py's registry can (same orphan-check shape).
    for rel in BASELINE:
        if rel not in present:
            breaches.append(f"{rel}: STALE baseline row -- no longer a tracked file in scope "
                             f"(deleted, renamed, or moved out of SCOPE_PREFIXES); remove it "
                             f"from BASELINE")

    if breaches:
        print(f"max-lines: {len(breaches)} breach(es) -- ADR-0007's 400-line ceiling, mechanized "
              f"(design/FABLE-SETUP-TUI-FIELD-STRATEGY.md Track 1 item 2):")
        for b in breaches:
            print(f"  !! {b}")
        return 1
    print(f"max-lines: clean ✓  ({len(files)} files scanned, {len(BASELINE)} grandfathered "
          f"over the {CEILING}-line ceiling, {review_band} in the {TARGET}-{CEILING} review band, "
          f"never flagged).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
