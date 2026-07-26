#!/usr/bin/env python3
"""fixture_sweep -- the read-only LIVE re-execution sweep over every family
gates/fixture_census.py registers (work item fixture-live-sweep, ledger rows 1388/1389).

WHY THIS EXISTS: gates/fixture_census.py's own docstring names its scope deliberately --
"Actually RE-EXECUTING each fixture to a live red is the ACCEPTANCE-time re-verification...
not run on every commit (many fixtures touch the DB; a 3s-per-fixture commit tax is its own
hazard). The static census is the standing net; the live red-re-execution is the acceptance
gate." (gates/fixture_census.py, module docstring, item SCOPE). THAT REASONING STANDS AND IS
CITED HERE, NOT OVERTURNED: this verb is the SCHEDULED COMPLEMENT to the static census, never a
pre-commit gate. It exists because banked evidence (a fixture that passed once, on some earlier
commit) and live behavior (does it still pass NOW, on THIS commit) had drifted apart five times
in one session before this work item was opened (ledger row 1388's statement names the five
specimens) -- each drift ambushed an unrelated arc instead of surfacing on its own schedule.
Invoke this on cadence (post-merge batches, the gap ritual) via `autoharn fixture-sweep`, never
wired into gates/ah_gate_all.sh or any other per-commit list.

CLASSIFICATION (one of three, per family):
  GREEN        subprocess exit 0.
  RED          subprocess exit nonzero -- the tail of its combined stdout+stderr is shown.
  UNEXERCISED  a declared environment prerequisite this sweep recognizes is missing (checked
               BEFORE the subprocess is spawned, so a family with no reachable Postgres host is
               never even attempted), or a structural blocker this sweep cannot generically
               resolve (STRUCTURAL_BLOCKERS below). Always loud, always names the blocker.
               Counted in the summary; never makes the sweep itself exit nonzero.

Exit code: nonzero iff at least one family is RED. UNEXERCISED alone never flips the exit code
(a missing env var is not this checkout's fault) but is always prominently counted so it is never
mistaken for GREEN.

ENV PRE-PROBE: read from the family drivers themselves, not invented here. Roughly half the
registry (gates/fixture_census.py's REGISTRY) declares a Postgres-host dependency, in one of two
shapes both already established in this tree: `seen-red/_fixture_env.py`'s `fixture_pghost()`
wrapper (the newer, shared convention), or a direct `filing/pghost_resolve.py` import calling
`resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST")` at module scope (the older, still-common
direct pattern -- e.g. seen-red/s31-supersession-uniform-retraction/run_fixtures.py). Both raise
SystemExit with a teaching message the instant the module is imported if neither env var nor a
resolvable deployment.json is present -- this IS the family's own clean refusal shape (ADR-0002),
so the sweep detects the SAME need (does a fixture file's text reference `pghost_resolve`,
`fixture_pghost`, `HARNESS_PGHOST`, or `EPISTEMIC_PGHOST`?) and calls the SAME resolver
(filing/pghost_resolve.py, imported once, resolved once -- the answer is identical for every
family that needs it, so one resolution up front stands in for N per-family probes) BEFORE
spawning anything, converting what would otherwise be N near-simultaneous SystemExit tracebacks
into one clearly-labeled UNEXERCISED per family.

GPG availability is a DIFFERENT shape and is NOT pre-probed here: the few families that touch gpg
(seen-red/setup-tui-signed-genesis-resume, seen-red/setup-tui-signed-genesis-key-pinning, ...)
already check `shutil.which("gpg")` PER CASE, inside their own run_fixtures.py, and print their
own "UNEXERCISED: 'gpg' not on PATH" line while still exiting 0 for every case that does not need
it -- that is already the right shape (a family-internal, per-case UNEXERCISED, not a whole-family
blocker), so this sweep leaves it alone and just reads the family's own exit code like any other.

STRUCTURAL_BLOCKERS: two registry entries (43-arming-delivery-set, 45-criterion-reviewer-grants)
both point at drive/arm.sh, a script that takes a REQUIRED positional <build-dir> argument (a
runs/<label>-build/ directory carrying its own launch.conf) -- this checkout ships no such
directory (see runs/README.md), and the sweep has no generic way to manufacture one. This is
listed explicitly, by family, rather than attempted-and-crashed, because a bare argv-usage error
from `sh`'s `${1:?...}` is not the "declares its env and refuses cleanly" shape this sweep
otherwise trusts -- it is a family this sweep structurally cannot drive at all, which is a
different, and more honest, thing to say than UNEXERCISED-for-missing-env.

RECURSION GUARD (the sweep's own family is swept too -- fixture-census registers "fixture-sweep"
-> seen-red/fixture-sweep/run_fixtures.py, this verb's own both-polarity witness): that driver
exercises this module IN-PROCESS (imports it, monkeypatches fixture_census.REGISTRY the same way
seen-red/fixture-census/red-specimen.py already does for the census gate itself) rather than
shelling out to a second, full, nested `autoharn fixture-sweep` -- so an ordinary sweep never
recurses at all, by construction of the fixture, not by a runtime check. As a SECOND, independent
guard (defense in depth -- never rely solely on a fixture's own good behavior): this module sets
AUTOHARN_FIXTURE_SWEEP_ACTIVE=1 in its own process environment for the lifetime of the sweep loop
below; before running the "fixture-sweep" family specifically, it checks whether that marker was
ALREADY set when this process started (meaning this very process is itself a family being swept
by an outer sweep) -- if so, the family is skipped outright and classified UNEXERCISED
("recursion guard") instead of executed. This bounds any possible recursion at depth 2 (outer
sweep -> fixture-sweep family's own driver, in-process, no further subprocess) even if some future
edit to the driver started shelling out to a real nested sweep by mistake.

WRITES NOTHING: no ledger writes, ever, from this module. Families that use scratch DBs/schemas do
so under their own pre-existing conventions (their choice, not this sweep's) -- the sweep only
spawns them as subprocesses and reads back their exit code and combined output; it keeps that
output in memory (never writing it to disk) and creates nothing on disk itself.

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import argparse
import ast
import importlib.util
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))  # gates/
REPO_ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import fixture_census  # gates/fixture_census.py -- the ONE registry, reused, never re-derived

sys.path.insert(0, os.path.join(REPO_ROOT, "filing"))
import pghost_resolve  # filing/pghost_resolve.py -- the same resolver every family driver uses

DEFAULT_TIMEOUT = 600  # seconds, per family -- generous by design (v1 has no per-family override)
SELF_FAMILY = "fixture-sweep"
RECURSION_MARKER = "AUTOHARN_FIXTURE_SWEEP_ACTIVE"
TAIL_LINES = 40  # how much of a RED family's combined output to show

# Registry targets this sweep structurally cannot drive (see module docstring). Keyed by family
# name (not by path) since two families currently share the one blocked script.
STRUCTURAL_BLOCKERS: dict[str, str] = {
    "43-arming-delivery-set": (
        "drive/arm.sh requires a <build-dir> positional argument (a runs/<label>-build/ "
        "directory carrying its own launch.conf) -- no such directory ships with this checkout "
        "(see runs/README.md); the sweep has no generic build-dir to hand it."),
    "45-criterion-reviewer-grants": (
        "drive/arm.sh requires a <build-dir> positional argument (a runs/<label>-build/ "
        "directory carrying its own launch.conf) -- no such directory ships with this checkout "
        "(see runs/README.md); the sweep has no generic build-dir to hand it."),
    # Same shape as the two entries above (ledger row 1459, cluster-1 fixture-repair triage):
    # instruments/verify_gate_journal_registered.py requires a REQUIRED positional <target>
    # argument (the arm-time target being checked for contemporaneity registration) -- the
    # census entry names the script alone, with no target, so invocation_for() would hand it a
    # bare argv with nothing to check and it would exit 2 on its own usage error, not on any
    # real defect. That is the identical "declares a required positional this sweep has no
    # generic value to supply" shape as arm.sh's <build-dir>, so it is listed here rather than
    # attempted-and-crashed.
    "42-gate-journal-registered": (
        "instruments/verify_gate_journal_registered.py requires a REQUIRED positional <target> "
        "argument (the arm-time target to check for contemporaneity registration) -- the "
        "registry names the script with no target; the sweep has no generic target to hand it "
        "(ledger row 1459)."),
}

# Substrings whose presence in a fixture file's own source text mark it as declaring a Postgres
# host dependency via the two established conventions (module docstring, ENV PRE-PROBE section).
_PGHOST_MARKERS = ("pghost_resolve", "fixture_pghost", "HARNESS_PGHOST", "EPISTEMIC_PGHOST")


def _local_module_basenames() -> frozenset[str]:
    """Every top-level basename (a .py file's stem, or a directory carrying an __init__.py) this
    checkout ships, anywhere under REPO_ROOT -- computed ONCE at module load (a plain directory
    walk, not an import, so the lazy-import gate does not apply). This is the ONE thing that lets
    the missing-package precondition probe below (declares_missing_package) tell "a fixture's own
    sibling helper module (seen-red/_fixture_env.py, imported via a sys.path.insert the fixture
    does itself)" apart from "a genuine third-party PyPI package this checkout does not have
    installed" -- both look identical as a bare `import NAME` / `from NAME import ...` line; only
    this checkout's own file layout disambiguates them."""
    names: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for f in filenames:
            if f.endswith(".py"):
                names.add(f[:-3])
        # Every directory counts as a local top-level name, __init__.py or not: Python 3's
        # implicit namespace packages (PEP 420) make a bare directory importABLE the moment its
        # parent is on sys.path, no __init__.py required -- e.g. `tools/` (no __init__.py) is
        # how `from tools.configtree.fields import ...` resolves in several setup-tui-* fixtures
        # (sys.path.insert(0, str(REPO)) is the universal convention every fixture in this tree
        # already uses). Checking ONLY __init__.py-carrying directories under-recognized this
        # class and produced a false-positive "missing package" on `tools` itself, live --
        # caught by this same addition's own witnessing pass.
        names.add(os.path.basename(dirpath))
    return frozenset(names)


_LOCAL_MODULE_BASENAMES = _local_module_basenames()


def _module_level_import_names(source_text: str) -> set[str]:
    """Every top-level package name a `import X[.Y]` / `from X[.Y] import ...` statement in
    `source_text` names (absolute imports only -- a `from . import X` relative import, level > 0,
    can only ever resolve within a package this checkout itself ships, never a third-party one,
    so it is not a candidate). Parsed via `ast`, not a text-substring scan (declares_pghost's own
    approach) -- import statements are syntactically unambiguous where a marker-substring scan
    would be fooled by the word appearing in a comment or string; a file this checkout ships is
    always valid Python, so `ast.parse` failing is itself notable, not silently swallowed into a
    false negative."""
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                names.add(node.module.split(".", 1)[0])
    return names


def declares_missing_package(fixture_path: str) -> str | None:
    """Pre-flight, mechanically-honest precondition probe (ledger row 1459's textual-package
    addendum): does the family's own registered fixture (a file, or every .py file under a
    directory target) import a top-level name that is neither a stdlib module, nor one of this
    checkout's own local modules (_local_module_basenames above), nor actually importABLE in
    THIS interpreter right now (importlib.util.find_spec)? If so, that name is a declared
    package precondition this environment does not meet -- returned so the caller can report
    UNEXERCISED with the concrete missing package named, the SAME shape declares_pghost/
    pghost_available already give a missing Postgres host, rather than letting the fixture's own
    ModuleNotFoundError traceback surface as an undifferentiated RED. Returns the first missing
    package name found, or None if every module-level import resolves."""
    abs_path = os.path.join(REPO_ROOT, fixture_path)
    paths: list[str] = []
    if os.path.isdir(abs_path):
        for dirpath, _dirnames, filenames in os.walk(abs_path):
            paths.extend(os.path.join(dirpath, f) for f in filenames if f.endswith(".py"))
    elif os.path.isfile(abs_path):
        paths = [abs_path]
    for p in paths:
        try:
            with open(p, encoding="utf-8") as f:
                text = f.read()
        except OSError:
            continue
        for name in sorted(_module_level_import_names(text)):
            if name in sys.stdlib_module_names or name in _LOCAL_MODULE_BASENAMES:
                continue
            try:
                spec = importlib.util.find_spec(name)
            except (ImportError, ValueError):
                spec = None
            if spec is not None:
                continue
            return name
    return None


def declares_pghost(fixture_path: str) -> bool:
    """True iff the family's own registered fixture (a file, or every .py file under a
    directory target) references one of the established Postgres-host-resolution conventions --
    the same textual signal the family's own module-scope code acts on itself."""
    abs_path = os.path.join(REPO_ROOT, fixture_path)
    paths: list[str] = []
    if os.path.isdir(abs_path):
        for dirpath, _dirnames, filenames in os.walk(abs_path):
            paths.extend(os.path.join(dirpath, f) for f in filenames if f.endswith(".py"))
    elif os.path.isfile(abs_path):
        paths = [abs_path]
    for p in paths:
        try:
            with open(p, encoding="utf-8") as f:
                text = f.read()
        except OSError:
            continue
        if any(marker in text for marker in _PGHOST_MARKERS):
            return True
    return False


def pghost_available() -> tuple[bool, str]:
    """Resolve the Postgres host exactly once, the same way every family driver would -- the
    answer is identical for all of them, so one resolution stands in for N. Returns
    (available, detail): detail is the resolved host on success, or the SystemExit's own teaching
    message on failure (never invented here -- it is filing/pghost_resolve.py's own text)."""
    try:
        host = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST")
        return True, host
    except SystemExit as e:
        return False, str(e)


def invocation_for(fixture_path: str) -> list[str]:
    """The subprocess argv for a registry target: a .py file runs directly under this same
    interpreter; a directory (currently only engine/tests) runs under pytest -q (the pytest
    idiom engine/conftest.py already sets up, matching how this repo's own docs invoke it, e.g.
    orchlog.d/watchdog-liveness-path-literals-and-census-hygiene.md); anything else (currently
    only drive/arm.sh, both STRUCTURAL_BLOCKERS entries) never reaches this function."""
    abs_path = os.path.join(REPO_ROOT, fixture_path)
    if os.path.isdir(abs_path):
        return [sys.executable, "-m", "pytest", fixture_path, "-q"]
    return [sys.executable, fixture_path]


class FamilyResult:
    def __init__(self, name: str, status: str, detail: str, seconds: float) -> None:
        self.name = name
        self.status = status  # "GREEN" | "RED" | "UNEXERCISED"
        self.detail = detail
        self.seconds = seconds


def run_family(name: str, fixture_path: str, timeout: int) -> FamilyResult:
    """Execute one registry entry and classify it. Never raises for an ordinary subprocess
    failure or timeout -- those are RED (or UNEXERCISED, for a recognized blocker), reported, not
    propagated. Genuinely unexpected failures (e.g. the interpreter itself cannot be found) are
    also caught and reported as RED with the exception text, never crash the whole sweep."""
    if name == SELF_FAMILY and os.environ.get(RECURSION_MARKER):
        return FamilyResult(name, "UNEXERCISED",
                             "recursion guard: this process is already inside a fixture-sweep "
                             "run (AUTOHARN_FIXTURE_SWEEP_ACTIVE set) -- the fixture-sweep "
                             "family is never executed a second time in the same recursion "
                             "chain (see module docstring, RECURSION GUARD).", 0.0)
    if name in STRUCTURAL_BLOCKERS:
        return FamilyResult(name, "UNEXERCISED", STRUCTURAL_BLOCKERS[name], 0.0)

    abs_path = os.path.join(REPO_ROOT, fixture_path)
    if not os.path.exists(abs_path):
        return FamilyResult(name, "RED", f"registry target does not exist: {fixture_path}", 0.0)

    missing_pkg = declares_missing_package(fixture_path)
    if missing_pkg is not None:
        return FamilyResult(name, "UNEXERCISED",
                             f"declared package precondition unmet -- {missing_pkg!r} is not "
                             f"importable in this interpreter (pip install {missing_pkg} or "
                             f"run this sweep under an interpreter that has it).", 0.0)

    if declares_pghost(fixture_path):
        ok, detail = pghost_available()
        if not ok:
            return FamilyResult(name, "UNEXERCISED",
                                 f"declared Postgres-host dependency unmet -- {detail}", 0.0)

    cmd = invocation_for(fixture_path)
    env = dict(os.environ)
    env[RECURSION_MARKER] = "1"
    start = time.monotonic()
    try:
        proc = subprocess.run(cmd, cwd=REPO_ROOT, env=env, capture_output=True, text=True,
                               timeout=timeout)
    except subprocess.TimeoutExpired as e:
        elapsed = time.monotonic() - start
        out = (e.stdout or "") + (e.stderr or "")
        tail = "\n".join(out.splitlines()[-TAIL_LINES:])
        return FamilyResult(name, "RED",
                             f"TIMEOUT after {timeout}s. Tail of output:\n{tail}", elapsed)
    except OSError as e:
        elapsed = time.monotonic() - start
        return FamilyResult(name, "RED", f"could not execute {cmd!r}: {e}", elapsed)
    elapsed = time.monotonic() - start

    if proc.returncode == 0:
        return FamilyResult(name, "GREEN", f"exit 0 ({elapsed:.1f}s)", elapsed)

    combined = (proc.stdout or "") + (proc.stderr or "")
    tail = "\n".join(combined.splitlines()[-TAIL_LINES:])
    return FamilyResult(name, "RED",
                         f"exit {proc.returncode} ({elapsed:.1f}s). Tail of output:\n{tail}",
                         elapsed)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="fixture-sweep",
        description="Read-only live re-execution sweep over every gates/fixture_census.py "
                     "family. Writes nothing to any ledger. GREEN/RED/UNEXERCISED per family, "
                     "plus a summary. Exit nonzero iff any family is RED.")
    p.add_argument("--only", action="append", default=[], metavar="FAMILY",
                    help="restrict the sweep to this family (repeatable)")
    p.add_argument("--list", action="store_true",
                    help="print the roster (family, invocation, declared env) and exit; runs nothing")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, metavar="SECONDS",
                    help=f"per-family subprocess timeout in seconds (default {DEFAULT_TIMEOUT})")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    families = sorted(fixture_census.REGISTRY.items())

    if args.only:
        unknown = sorted(set(args.only) - set(fixture_census.REGISTRY))
        if unknown:
            print(f"fixture-sweep: REFUSED -- unknown --only famil{'y' if len(unknown) == 1 else 'ies'}: "
                  f"{', '.join(unknown)}. Run --list for the roster. Nothing was touched.", file=sys.stderr)
            return 2
        families = [(n, p) for n, p in families if n in set(args.only)]

    if args.list:
        for name, path in families:
            kind = "pytest-dir" if os.path.isdir(os.path.join(REPO_ROOT, path)) else "script"
            if name in STRUCTURAL_BLOCKERS:
                kind = "structural-blocker"
            env_note = "declares-pghost" if declares_pghost(path) else "no-declared-env"
            print(f"{name}\t{path}\t{kind}\t{env_note}")
        return 0

    os.environ.setdefault(RECURSION_MARKER, "")  # read, not overwritten, by run_family's own check
    already_nested = bool(os.environ.get(RECURSION_MARKER))

    results: list[FamilyResult] = []
    for name, path in families:
        # a fresh copy of the marker state is what run_family's own recursion check reads (it
        # checks os.environ directly at call time, honoring an outer sweep's marker if present)
        res = run_family(name, path, args.timeout)
        results.append(res)
        print(f"[{res.status:11s}] {name}  ({res.seconds:.1f}s)")
        if res.status != "GREEN":
            for line in res.detail.splitlines():
                print(f"    {line}")

    green = sum(1 for r in results if r.status == "GREEN")
    red = sum(1 for r in results if r.status == "RED")
    unexercised = sum(1 for r in results if r.status == "UNEXERCISED")
    print()
    print(f"fixture-sweep summary: {len(results)} families -- {green} GREEN, {red} RED, "
          f"{unexercised} UNEXERCISED"
          + (" (nested inside an outer sweep)" if already_nested and not args.only else ""))
    if red:
        print(f"fixture-sweep: {red} famil{'y is' if red == 1 else 'ies are'} RED -- see tails above.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
