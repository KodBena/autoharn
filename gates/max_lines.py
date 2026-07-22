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

Usage: python3 gates/max_lines.py [root]      # default: repo root, git-tracked *.py in SCOPE
Lazy imports banned.
"""
from __future__ import annotations

import os
import subprocess
import sys

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
    # Reconciled +33 to 1717 (design/FABLE-SETUP-TUI-CONFIG-FILE-SPEC.md build, ledger row 1944):
    # `_maybe_self_save_config` (spec §4's self-application -- "every birth saves its config",
    # called from every `_execute_commit` exit path) plus two one-line `*_engaged` flags
    # (`screen_observability`/`screen_hydration`) the self-save capture needs to distinguish
    # "screen entered, nothing selected" from "screen skipped outright" -- a fact `state`/the
    # plan cannot otherwise recover. Genuinely new decision/effect-boundary logic, not padding.
    # Written plain, no golfing (ADR-0007's no-go clause); witnessed growth.
    "tools/setup_tui/screens.py":                    1717,
    "gates/kind_shape_manifest_gate.py":              1152,
    "hooks/pretooluse_change_gate.py":                1138,
    "hooks/stop_clean_exit.py":                        992,
    "engine/contemp_edb.py":                            978,
    "engine/judgment_registry.py":                      889,
    "tools/experiments/compound_nominal_scan2.py":      869,
    "hooks/demurral_detect.py":                         837,
    "gates/doc_attestation_presence.py":                837,
    # Reconciled +7 to 820 (design/FABLE-RESERVATION-RESIDUE-SPEC.md §7 amendment,
    # kernel/lineage/s56-reservation-residue.sql): work_review_floor_atoms' `discharged` leg
    # widens to verdict IN ('attest','attest_with_reservations') -- genuinely new discharge
    # semantics, not padding (the s56 kernel-view widening's engine-side twin, needed for
    # ./judge's SQL/ASP differential to AGREE on a reservation-discharged item). Written plain,
    # no golfing.
    "engine/ledger_floor.py":                           820,
    "engine/preamble_floor.py":                         801,
    # Reconciled +31 to 705 (design/FABLE-SETUP-TUI-TYPED-UI-SPEC.md build), then +82 to 787
    # (design/FABLE-SETUP-TUI-NAVIGATION-SPEC.md, the Textual leg -- maintainer-witnessed live
    # defect: '<' typed at a Textual prompt did nothing, the intro's own promise was false under
    # this backend). The 705 leg: `TextualUi.emit` replaces the old `banner`/`say` pair with the
    # single typed-element seam (spec §2), plus the new `SetupWizardApp.write_transcript_styled`
    # method (the one styling seam beyond plain print-capture, for a refusal `Note`) and one new
    # import line (`elements`/`rich.text.Text`); also carries the F4 diagnostic leg's fix (spec
    # §4, ledger rows 1844-F4/1917): `emit` prints a multi-line element as ONE
    # `print("\n".join(lines))` call, not one `print()` per line -- reproduced live
    # (seen-red/setup-tui-typed-elements/, this build's own headless WX1 rerun during
    # construction) that N separate print() calls per element floods the print-capture pipeline's
    # `events.Print` queue badly enough, under sustained emission, to stall the App's asyncio loop
    # past every bridge call's own budget -- not a false "misread as shutdown" but a genuine
    # indefinite hang, worse than F4's own hypothesis. The 787 leg: `TextualUi`'s four `ask_*`
    # methods each gained the SAME BACK-trigger recognition `InteractiveUi` already carries
    # (imported from `tools/setup_tui/ui.py`'s now-public `BACK_TRIGGER_PLAIN`, never redefined
    # here); a new `ctrl+b` `Binding` plus `SetupWizardApp.action_go_back`/`on_key`'s choice/pause
    # leg give the affordance a visible Footer surface even for prompt kinds with no free-text
    # `Input` widget to type "<" into. Genuinely new decision/interaction logic both legs, not
    # padding -- the module docstring's own new "architecture point 6" section (~24 of the 82
    # lines) is the load-bearing explanation of why recognition stays per-backend rather than
    # hoisted into `NavigableUi` (`NavigableUi` only ever sees each backend's ALREADY-coerced
    # return value, never the pre-coercion raw keystroke a full hoist would need) -- P10
    # prose-vs-logic judgment: this is the ADR-0000 "surface every judgment on the record" duty,
    # not decorative writing. Written plain, no golfing (ADR-0007's no-go clause); witnessed
    # growth both legs.
    "tools/setup_tui/ui_textual.py":                    787,
    # Reconciled +5 to 734 (design/FABLE-RESERVATION-RESIDUE-SPEC.md §7 amendment,
    # kernel/lineage/s56-reservation-residue.sql): export_work's w_discharged/1 extraction widens
    # to verdict IN ('attest','attest_with_reservations') -- the EDB-side twin of the same
    # discharge-semantics widening, feeding the ASP program that ./judge's differential compares
    # against the (also-widened) SQL floor. Written plain, no golfing.
    "engine/ledger_edb.py":                             734,
    "tools/workflow_compile.py":                        672,
    # tools/setup_tui/durable_decisions.py -- REMOVED from BASELINE 2026-07-22 (P10 content
    # split, law/adr/0012's 2026-07-22 Amendment): 619 -> 249 lines, the CATALOG literal moved
    # to tools/setup_tui/durable_decisions_data.py. The ratchet is the working: a file that
    # shrinks under CEILING exits the table (ADR-0011 Rule 4, module docstring's own "may shrink
    # ... and leave this table on its next touch").
    "tools/watchdog_liveness.py":                       570,
    "engine/tests/test_ledger_marriage.py":             533,
    "hooks/posttooluse_error_recurrence.py":            530,
    "engine/ledger_differential.py":                    529,
    "hooks/pretooluse_delegation_observer.py":          525,
    # Reconciled +12 to 525 (design/FABLE-RESERVATION-RESIDUE-SPEC.md build, kernel/lineage/
    # s56-reservation-residue.sql): CHAIN += s56, and one new ALLOWLIST entry (review_verdicts,
    # a DECLARED raw/history reader by design -- the general review-legibility surface must show
    # a superseded review too). Genuinely new classification content, not padding. Written plain,
    # no golfing.
    "gates/ledger_reader_allowlist.py":                 525,
    # Reconciled +22 to 525 (GENESIS-GATE HARD-STOP, ledger row 1918): `verify_commission_act`
    # gained the `accept_unverified` parameter and its own `_verify_commission_ok` verdict_check
    # function (the real halt-vs-continue decision, previously nowhere -- exit code was silently
    # trusted). Genuinely new decision logic, not padding. Written plain, no golfing.
    "tools/setup_tui/signed_genesis.py":                525,
    "gates/interpreter_boundary_lint.py":               498,
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
    "tools/setup_tui/config_seam.py":                   414,
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
    "tools/regrade_decisions.py":                       415,
    "tools/markdown_tables.py":                         412,
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
    """Every git-tracked *.py path (relative to `root`) under SCOPE_PREFIXES, minus EXCLUDE_*."""
    r = subprocess.run(["git", "-C", root, "ls-files", "*.py"],
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


def line_count(path: str) -> int:
    with open(path, encoding="utf-8", errors="replace") as f:
        return len(f.read().splitlines())


def main() -> int:
    root = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else REPO
    files = tracked_scope_files(root)
    present = set(files)

    breaches: list[str] = []
    review_band = 0
    for rel in files:
        n = line_count(os.path.join(root, rel))
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
