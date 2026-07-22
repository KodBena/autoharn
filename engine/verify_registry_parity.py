#!/usr/bin/env python3
"""verify_registry_parity — two-way parity between judgment_registry.SPECS and the LIVE surface
(engine INC 1; ruling 110 §5 INC 1 + D2). Both directions, loud (F49/ADR-0002):

  direction 1 — implementation with NO registry row FAILS (an unregistered judgment is apocryphal);
  direction 2 — registry row whose implementation does NOT exist is RED-undischarged (unless the
                spec carries a declared exclusion).

Plus the D2 append-only check: `registry_baseline.json` banks (judgment_id -> content-hash) for
every row ever registered. A banked row whose hash CHANGED without a superseding row (a newer spec
with supersedes=<id>) FAILS — spec changes are new rows, never edits. `--rebaseline` appends new
rows to the baseline (and REFUSES to launder a hash change: the failing row must first gain its
supersession).

The live surface enumerated (the ruling's own list: ledger_tnow.lp/floor #shows, the instruments,
every close line, the e17 triggers):
  close lines    — introspected from epistemic-operator/instruments/close_manifest.py (imported,
                   never hand-copied: MANDATORY + DECLARED_OBSERVERS + ACTS_CONSUMERS +
                   PERF_CONSUMERS + the run_* line functions)
  instruments    — epistemic-operator/instruments/*.py (+ .sh/.lp files there)
  lp judgments   — every `#show name/arity.` in this repo's fact-mining *.lp files
  kernel triggers— CREATE TRIGGER names parsed from the s15/s17 DDL (the e17 kernel)

Negative control (--negative-control; the F49 seen-red for THIS gate): synthetically (a) drop one
lp file's atoms from the enumeration — the registry rows owning them must go RED-undischarged; and
(b) inject one unregistered close line — direction 1 must FAIL. The control PASSES (exit 0) iff
both synthetic defects are caught. A gate never seen red is a claim (ADR-0011).

Exit: 0 parity green (or control fired both ways) · 1 parity red / control failed · 2 substrate
missing (QUARANTINE — never a silent green). Lazy imports banned. Read-only.
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)   # autoharn root
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO_ROOT, "instruments"))   # autoharn: repo-local instruments/ (was the cross-repo reach)

import close_manifest  # noqa: E402  (autoharn: repo-local; parity verifies THIS home's surface)
from judgment_registry import DECLARED_EXCLUSIONS, IMPL_INDEX, SPECS  # noqa: E402

INSTR = os.path.join(REPO_ROOT, "instruments")
DDL_FILES = [
    os.path.join(REPO_ROOT, "kernel", "lineage", "s15-schema.sql"),
    os.path.join(REPO_ROOT, "kernel", "lineage", "s17-stamp-mechanism.sql"),
    os.path.join(REPO_ROOT, "kernel", "lineage", "s17-independence-vocabulary.sql"),
]
BASELINE = os.path.join(HERE, "registry_baseline.json")

# The judgment_registry SPECS carry APPEND-ONLY tool identifiers baked into each row's content_hash
# (D2); they name the OLD-repo paths and MUST NOT change (a hash edit is forbidden). autoharn dissolves
# the cross-repo reach (C18) by TRANSLATING those historical identifiers to their autoharn locations for
# the existence check — the spec identifier is immutable, the resolution adapts.
_TOOL_TRANSLATE = {
    "claude_harness/tools/findings_gate.py": "gates/findings_gate.py",
    "claude_harness/experiments/fact-mining/row_performed_by.py": "instruments/row_performed_by.py",
    "claude_harness/experiments/fact-mining/ledger_differential.py": "engine/ledger_differential.py",
}

_SHOW_RE = re.compile(r"^\s*#show\s+([a-z_][A-Za-z0-9_]*/\d+)\s*\.", re.M)
_TRIGGER_RE = re.compile(r"^CREATE (?:CONSTRAINT )?TRIGGER\s+(\w+)", re.M)
# run_* functions that are infrastructure runners, not close lines of their own
_RUNNER_INFRA = {"line", "acts_consumers", "perf_consumers"}


def enumerate_close_lines() -> set[str]:
    lines: set[str] = set()
    lines |= set(close_manifest.MANDATORY)
    lines |= set(close_manifest.DECLARED_OBSERVERS)
    lines |= set(close_manifest.ACTS_CONSUMERS)
    lines |= set(close_manifest.PERF_CONSUMERS)
    for name in dir(close_manifest):
        if name.startswith("run_") and callable(getattr(close_manifest, name)):
            short = name[len("run_"):]
            if short not in _RUNNER_INFRA:
                lines.add(short)
    return {f"close:{ln}" for ln in lines}


LP_DIR = os.path.join(HERE, "lp")   # autoharn: the engine ASP programs live in engine/lp/ (LAYOUT split)
# [C16]: these 4 fact-mining verifiers now live in instruments/. They are seen-red FIXTURES (findings
# 39/25/09/28), not registered close-instruments, so they are excluded from the instrument enumeration
# (in the old topology they lived in fact-mining and were never enumerated — the split surfaced them).
_RELOCATED_VERIFIERS = {"row_performed_by.py", "verify_binder.py",
                        "verify_operator_turns.py", "verify_relevant_act.py"}
# The NLP kb-logic-layer / why-orphan judgment classes' .lp implementations stayed in the fact-mining
# ATTIC (mandate §4). Their registry rows (append-only, judgment_registry verbatim) legitimately have no
# implementation in autoharn; parity excludes them here rather than by editing the frozen registry.
_ATTIC_LP = {"logic_layer.lp", "logic_repair.lp", "why_layer.lp"}


def enumerate_instruments() -> set[str]:
    keys: set[str] = set()
    for f in sorted(os.listdir(INSTR)):
        if f in _RELOCATED_VERIFIERS:
            continue
        if f.endswith(".py"):
            keys.add(f"instrument:{f}")
        elif f.endswith(".sh"):
            keys.add(f"tool:instruments/{f}")
        elif f.endswith(".lp"):
            atoms = _SHOW_RE.findall(open(os.path.join(INSTR, f), encoding="utf-8").read())
            keys |= ({f"lp:instruments/{f}#{a}" for a in atoms} if atoms else {f"lp:instruments/{f}"})
    return keys


def enumerate_lp_atoms(skip_file: str | None = None) -> set[str]:
    keys: set[str] = set()
    if not os.path.isdir(LP_DIR):
        return keys
    for f in sorted(os.listdir(LP_DIR)):
        if not f.endswith(".lp") or f == skip_file:
            continue
        atoms = _SHOW_RE.findall(open(os.path.join(LP_DIR, f), encoding="utf-8").read())
        keys |= {f"lp:{f}#{a}" for a in atoms}  # zero-#show files emit no judgment outputs
    return keys


def enumerate_triggers() -> set[str]:
    names: set[str] = set()
    for p in DDL_FILES:
        if not os.path.exists(p):
            raise FileNotFoundError(p)
        names |= set(_TRIGGER_RE.findall(open(p, encoding="utf-8").read()))
    return {f"trigger:{n}" for n in names}


def live_surface(skip_lp: str | None = None, inject: str | None = None) -> set[str]:
    s = enumerate_close_lines() | enumerate_instruments() | enumerate_lp_atoms(skip_lp) | enumerate_triggers()
    if inject:
        s.add(inject)
    return s


def check(surface: set[str], quiet: bool = False) -> tuple[list[str], list[str]]:
    """Returns (direction1_failures, direction2_failures)."""
    covered = set(IMPL_INDEX) | set(DECLARED_EXCLUSIONS)
    d1 = sorted(surface - covered)  # implementation with no row
    enumerable = {k for k in IMPL_INDEX
                  if k.split(":", 1)[0] in ("close", "instrument", "trigger") or k.startswith("lp:")}
    d2 = []
    excl_by_id = {s.judgment_id: s.exclusion for s in SPECS}
    for k in sorted(enumerable):
        if k.startswith("lp:") and any(k.startswith(f"lp:{a}") for a in _ATTIC_LP):
            continue   # implementation stayed in the fact-mining attic (mandate §4)
        if k not in surface and not excl_by_id.get(IMPL_INDEX[k]):
            d2.append(k)
    for k in sorted(set(IMPL_INDEX) - enumerable):  # tool: keys — resolved repo-locally in autoharn
        path = k.split(":", 1)[1]
        path = _TOOL_TRANSLATE.get(path, path)   # translate historical old-repo identifiers -> autoharn (C18)
        roots = (REPO_ROOT,)                     # autoharn only — no cross-repo archive reach
        if not any(os.path.exists(os.path.join(r, path)) for r in roots):
            if not excl_by_id.get(IMPL_INDEX[k]):
                d2.append(k)
    if not quiet:
        for k in d1:
            print(f"  RED  direction-1 (implementation without registry row): {k}")
        for k in d2:
            print(f"  RED  direction-2 (registry row without implementation, undischarged): {k} "
                  f"[{IMPL_INDEX.get(k, '?')}]")
    return d1, d2


def check_baseline(rebaseline: bool) -> list[str]:
    """D2 append-only: banked hashes must persist unchanged unless superseded."""
    current = {s.judgment_id: s.content_hash() for s in SPECS}
    superseded_ids = {s.supersedes for s in SPECS if s.supersedes}
    if not os.path.exists(BASELINE):
        if rebaseline:
            json.dump(current, open(BASELINE, "w", encoding="utf-8"), indent=1, sort_keys=True)
            print(f"  baseline CREATED: {len(current)} rows -> {BASELINE}")
            return []
        return [f"registry_baseline.json missing — run --rebaseline once to bank the initial rows ({len(current)} specs)"]
    banked = json.load(open(BASELINE, encoding="utf-8"))
    fails = []
    for jid, h in banked.items():
        if jid not in current:
            fails.append(f"banked row {jid!r} VANISHED from SPECS — append-only forbids removal (D2)")
        elif current[jid] != h and jid not in superseded_ids:
            fails.append(f"banked row {jid!r} hash CHANGED without a superseding row — a spec change "
                         "is a NEW row with supersedes set, never an edit (D2)")
    if rebaseline:
        if fails:
            print("  --rebaseline REFUSED: resolve the append-only failures first (no hash laundering)")
        else:
            new = {j: h for j, h in current.items() if j not in banked}
            if new:
                banked.update(new)
                json.dump(banked, open(BASELINE, "w", encoding="utf-8"), indent=1, sort_keys=True)
                print(f"  baseline APPENDED: {len(new)} new row(s)")
            else:
                print("  baseline unchanged (no new rows)")
    return fails


def negative_control() -> int:
    """The F49 seen-red for this gate: both synthetic defects must be CAUGHT."""
    print("# negative control (a): drop ledger_acts.lp atoms from the surface -> direction-2 must fire")
    d1a, d2a = check(live_surface(skip_lp="ledger_acts.lp"), quiet=True)
    a_fired = any(k.startswith("lp:ledger_acts.lp#") for k in d2a)
    print(f"  {'FIRED' if a_fired else 'DID NOT FIRE — CONTROL FAILED'} "
          f"({len([k for k in d2a if k.startswith('lp:ledger_acts.lp#')])} rows RED-undischarged)")
    print("# negative control (b): inject an unregistered close line -> direction-1 must fire")
    d1b, _ = check(live_surface(inject="close:synthetic_unregistered_line"), quiet=True)
    b_fired = "close:synthetic_unregistered_line" in d1b
    print(f"  {'FIRED' if b_fired else 'DID NOT FIRE — CONTROL FAILED'}")
    ok = a_fired and b_fired
    print(f"# negative-control {'PASS — both polarities caught' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    if "--negative-control" in argv:
        return negative_control()
    rebaseline = "--rebaseline" in argv
    print("# registry parity — judgment_registry.SPECS vs the live surface")
    try:
        surface = live_surface()
    except FileNotFoundError as e:
        print(f"  QUARANTINED: substrate missing: {e} — a parity check that cannot enumerate is NO "
              "RESULT, never a silent green")
        return 2
    d1, d2 = check(surface)
    base_fails = check_baseline(rebaseline)
    for f in base_fails:
        print(f"  RED  append-only: {f}")
    n_ok = len(surface & (set(IMPL_INDEX) | set(DECLARED_EXCLUSIONS)))
    print(f"# surface={len(surface)} keys; covered={n_ok}; direction-1 RED={len(d1)}; "
          f"direction-2 RED={len(d2)}; append-only RED={len(base_fails)}")
    if d1 or d2 or base_fails:
        print("# parity RED")
        return 1
    print("# parity GREEN — every implementation registered, every row discharged, baseline intact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
