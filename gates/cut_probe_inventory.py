#!/usr/bin/env python3
"""cut_probe_inventory — the regression-probe list for a cut candidate.

Item `external-rehearsal-register-gate`, RCA row 909 (same-host-illusion / c4923ae-class
regressions). This module is the ONE HOME for the regression-probe registry the rehearse
script (`bootstrap/rehearse-from-origin.sh`) wires in after its live rehearsal: every SHIPPED
FIX class that a past incident recovered from gets one probe line here, so a future revert of
that same class fails LOUDLY at cut time instead of surfacing at the maintainer's chair (the
literal debacle row 909/928 trace: a repair landed on `next`, silently reverted before a public
push, and no mechanized check re-derived "does the shipped fix still hold" against the tree
that was about to go out).

RUN AGAINST A NAMED TREE, never the live checkout implicitly:

    python3 gates/cut_probe_inventory.py <tree-path> [--json]

<tree-path> is any directory containing an autoharn tree — a fresh clone of origin, a git
worktree checked out at a candidate commit, or (for self-test) this very checkout. The script
never assumes it is running from inside the tree it is grading; every probe takes tree-path as
an explicit argument and dereferences paths under it only.

EXIT CODE is the gate contract every gates/*.py file in this repo shares: 0 = every probe
passed, 1 = at least one probe failed (each failure printed with the offending path/line so the
failure is legible without re-deriving the check by hand).

REGISTRY CONVENTION (read this before adding a fifth probe). Each entry in PROBES is a 3-tuple
`(name, fixed_by, check)`:
  - `name`      short, stable, kebab-case; becomes this probe's line in `--json` output and any
                gate/CI log that greps for it by name — do not rename an existing probe once it
                ships, add a new one instead (a renamed probe silently breaks anyone who greps
                the old name).
  - `fixed_by`  a short citation of the shipped fix this probe stands guard for (a commit hash,
                a ledger row id, or both) — so a future reader can find out WHY the probe exists
                without ledger archaeology.
  - `check`     a callable `(tree: Path) -> ProbeResult` — pure, read-only, no writes to
                `tree`, no network, no reliance on anything outside `tree` itself (a probe that
                reads ambient state defeats the whole point: it would pass against a broken tree
                just because the operator's own machine happens to still be correct).
Append to PROBES; never delete or reorder an existing entry (order is the audit trail of when
each regression class got a probe). One line per shipped-fix class — resist bundling two
unrelated regressions into one probe just because they were fixed in the same commit.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Operator-verb shim names this repo scaffolds (bootstrap/new-project.sh's own list) --
# duplicated here deliberately as a short, stable literal rather than importing new-project.sh
# (a shell script, not an importable module); if the scaffolded shim set changes, update this
# tuple in the same change.
_SHIM_NAMES = (
    "led", "judge", "pickup", "audit", "distance-to-clean",
    "verify-commission", "verify-chain", "attest-doc", "attest-tags", "migrate", "doctor",
)

# A hardcoded real-host path a portable shim must never carry (cf63e40's regression class: a
# shim that `exec`s a literal /home/<user>/... path instead of resolving $HERE at invocation
# time breaks for every user who is not that one operator, on every machine that is not this
# one). Matches /home/<name>/... but not the word "home" alone.
_HOME_PATH = re.compile(r"/home/[A-Za-z0-9_.-]+")

# The LAN-literal IP autoharn's own instruments/ used to hardcode instead of resolving through
# pghost_resolve.py (3af7d88's regression class, RCA row 909's "instrument literal" leg).
_LAN_IP = re.compile(r"\b192\.168\.122\.1\b")


@dataclass
class ProbeResult:
    passed: bool
    detail: list[str] = field(default_factory=list)


def probe_shim_hardcode(tree: Path) -> ProbeResult:
    """No operator-verb shim at <tree>'s root hardcodes a real host path -- every shim must
    resolve its own directory ($HERE / $(dirname "$0")) at invocation time instead. Regression
    class: cf63e40 (shim $HERE portability)."""
    offenders: list[str] = []
    for name in _SHIM_NAMES:
        p = tree / name
        if not p.is_file():
            continue  # this tree's scaffold may not carry every shim (e.g. a bare autoharn
            # checkout has none at all) -- absence is not this probe's concern, a hardcoded
            # literal INSIDE a present shim is
        try:
            text = p.read_text(errors="replace")
        except OSError as e:
            offenders.append(f"{p}: unreadable ({e})")
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _HOME_PATH.search(line):
                offenders.append(f"{p}:{lineno}: {line.strip()}")
    return ProbeResult(passed=not offenders, detail=offenders)


def probe_instrument_literal(tree: Path) -> ProbeResult:
    """No file under <tree>/instruments/ hardcodes the LAN-literal Postgres host IP instead of
    resolving it through pghost_resolve.py. pghost_resolve.py itself is exempt -- the literal
    legitimately appears in ITS OWN docstring/examples, the one place that names what it
    resolves away from. Regression class: 3af7d88 (pghost_resolve wiring across 10 call
    sites)."""
    offenders: list[str] = []
    instruments_dir = tree / "instruments"
    if instruments_dir.is_dir():
        for p in sorted(instruments_dir.rglob("*.py")):
            if p.name == "pghost_resolve.py":
                continue
            try:
                text = p.read_text(errors="replace")
            except OSError as e:
                offenders.append(f"{p}: unreadable ({e})")
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if _LAN_IP.search(line):
                    offenders.append(f"{p}:{lineno}: {line.strip()}")
    return ProbeResult(passed=not offenders, detail=offenders)


def probe_gitignore_deployment_json(tree: Path) -> ProbeResult:
    """<tree>/.gitignore carries a '/deployment.json' line -- a per-deployment secret-adjacent
    config file must never be tracked. Regression class: 2bf0eb7 (/deployment.json gitignore
    rule)."""
    gi = tree / ".gitignore"
    if not gi.is_file():
        return ProbeResult(passed=False, detail=[f"{gi}: missing"])
    lines = [line.strip() for line in gi.read_text(errors="replace").splitlines()]
    if "/deployment.json" in lines:
        return ProbeResult(passed=True, detail=[])
    return ProbeResult(
        passed=False,
        detail=[f"{gi}: no exact '/deployment.json' line found (a looser pattern like "
                 f"'deployment.json' or a trailing-slash variant does not count -- the shipped "
                 f"fix added this exact line)"],
    )


def probe_deployment_json_example_present(tree: Path) -> ProbeResult:
    """<tree>/deployment.json.example exists -- the placeholder-values template a stranger's
    first README walkthrough (Configuration section) points them at. This is the specific file
    the row-909/928 debacle silently dropped from a tracked tree (c4923ae) while every
    same-host rehearsal in the chain kept passing, because the working directory's untracked
    disk copy was still present to read."""
    p = tree / "deployment.json.example"
    if p.is_file():
        return ProbeResult(passed=True, detail=[])
    return ProbeResult(passed=False, detail=[f"{p}: missing"])


# Registry. Append-only -- see the module docstring's REGISTRY CONVENTION before adding here.
PROBES: list[tuple[str, str, "callable[[Path], ProbeResult]"]] = [
    ("shim-hardcode", "cf63e40 / row 928", probe_shim_hardcode),
    ("instrument-literal", "3af7d88 / row 928", probe_instrument_literal),
    ("gitignore-deployment-json", "2bf0eb7 / row 928", probe_gitignore_deployment_json),
    ("deployment-json-example-present", "row 909 / row 928 (the debacle's own specimen)",
     probe_deployment_json_example_present),
]


def run_all(tree: Path) -> dict[str, ProbeResult]:
    return {name: check(tree) for name, _fixed_by, check in PROBES}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("tree", help="path to the tree to probe (a clone, a worktree, a checkout)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    tree = Path(args.tree).resolve()
    if not tree.is_dir():
        print(f"cut_probe_inventory: REFUSED -- {tree} is not a directory. Nothing probed.",
              file=sys.stderr)
        return 2

    results = run_all(tree)
    all_pass = all(r.passed for r in results.values())

    if args.json:
        out = {
            "tree": str(tree),
            "all_pass": all_pass,
            "probes": {
                name: {"passed": r.passed, "detail": r.detail, "fixed_by": fixed_by}
                for (name, fixed_by, _check), r in zip(PROBES, results.values())
            },
        }
        print(json.dumps(out, indent=2))
        return 0 if all_pass else 1

    print(f"cut_probe_inventory: probing {tree}")
    for name, fixed_by, _check in PROBES:
        r = results[name]
        status = "PASS" if r.passed else "FAIL"
        print(f"  [{status}] {name}  (regression class: {fixed_by})")
        for line in r.detail:
            print(f"           {line}")
    print()
    if all_pass:
        print(f"cut_probe_inventory: ALL {len(PROBES)} PROBES PASS against {tree}")
        return 0
    failed = [name for name, _f, _c in PROBES if not results[name].passed]
    print(f"cut_probe_inventory: FAILED ({len(failed)}/{len(PROBES)}): {', '.join(failed)}",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
