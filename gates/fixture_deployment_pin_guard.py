#!/usr/bin/env python3
"""fixture_deployment_pin_guard.py -- mechanical sweep for ledger work item
fixture-scratch-pinning-guard (row 1249, generalizing beyond `serve_existing_world`'s own
tempdir/repo-disjoint refusal in seen-red/boundary-service/run_fixtures.py).

THE LEAK (rows 1237-1244/1248): a seen-red fixture resolved a REAL deployment.json and stood a
served `led` against the LIVE kernel, writing garbage rows. Three doors, all guarded here:
  (a) invoking this CHECKOUT's own operator verb directly (`REPO / "led"`, its umbrella-CLI
      successor `REPO / "libexec" / "autoharn" / "led"`, or the `autoharn` dispatcher) instead of
      a scaffolded scratch copy -- each resolves deployment.json from `dirname($0)`, ignoring any
      inherited PICKUP_DEPLOYMENT override. A direct `bootstrap/templates/*.tmpl` invocation is
      DIFFERENT and SAFE (env-driven via `os.environ.get("PICKUP_DEPLOYMENT", ...)`) -- not
      flagged.
  (b) mutating `os.environ["PICKUP_DEPLOYMENT"]` globally (direct, aliased, or via
      `.update()`/`.setdefault()`) instead of a per-call `env` dict via one subprocess call's
      `env=` kwarg -- a global mutation leaks into every later subprocess this process spawns.
  (c) spawning via a shell string (`os.system(...)`, `shell=True`) instead of an argv list --
      sidesteps (a)/(b) entirely: a shell string's repo-path spelling is unenumerable.

Grep/AST CENSUS gate (gates/no_lazy_imports.py's own family), not a dataflow prover. Binding
and argv resolution AST helpers live in gates/_pin_guard_resolve.py (split this fix-round to
keep both files well under ADR-0007's 400-line ceiling with room for full disclosure -- see
POSTURE below); this file owns the entry point, the checks that walk each file, and every
verdict/waiver string.

POSTURE, ROUND 2 (fresh-context strengthened-tier re-lap BLOCKED 26c7c48; this commit is that
fix-round). Round 1 shipped a per-line waiver and a one-hop constant/argv-list resolver; round
2's reviewer showed the waiver span was wrong (attached to a BINDING, blanketing every later use)
and three further live evasions. Per finding, fixed vs. disclosed:
  1. FIXED (the blocker): waiver span is now the USE site (the Call's own line/lines) only,
     never a constant's binding line -- gates/_pin_guard_resolve.py's `resolve_verb_element` /
     `verb_path_bindings` return verb NAMES, never an Assign node, so there is nothing left to
     mis-waive at the binding.
  2. FIXED: post-binding argv mutation (`cmd[1] = "led"` after `cmd = [str(AUTOHARN), "--help"]`)
     is caught by `_pin_guard_resolve.simulate_list_states`, which replays subscript-assignment,
     `.append`/`.insert`/`.extend`, `del`, and `+=` in source order to reconstruct the argv
     list's final contents rather than trusting the original literal.
  3. FIXED: `os.path.join(REPO, "led")` and `REPO.joinpath("led")` (this corpus's OWN idiom in
     ~15 real non-verb-path files) are now recognized alongside the `/`-BinOp and f-string
     shapes.
  4. FIXED (same mechanism as #2): argv built via `.append()` from an empty-list binding is
     reconstructed by the same simulation, not just the initial (empty) literal.
  5. FIXED: CHECK 1 now scans every positional arg of a Call, not only `args[0]` -- closes
     `functools.partial(subprocess.run, argv)` (argv is `args[1]` of the `partial(...)` call
     itself) without hand-listing `functools.partial` as a special case.
  6. DISCLOSED, not fixed: a verb-path constant imported from another module
     (`from helper import LED`) is invisible -- this is a single-file AST census, not a
     cross-module resolver, and stops at the file boundary by construction (restated in
     gates/_pin_guard_resolve.py's own docstring, the module that would have to grow a resolver
     to close this).
  7. FIXED: a waiver comment on a line that hosts more than one statement (`x = 1;
     subprocess.run(...)  # waiver: ...`) no longer silences anything on that line -- see
     `_ambiguous_statement_lines` / `_span_has_waiver` below. A waiver must sit on a line with
     exactly one statement, so it can never bless a second, unrelated one sharing the line.

ROUND 1 POSTURE (unchanged, kept for context): FULL INVERSION (refuse any subprocess-spawning
file outright absent a waiver) was measured against the real tree and rejected: ~150 of 203
in-scope files make a direct subprocess call, overwhelmingly git/psql/ls with nothing to do with
this repo's own verbs. CHECK 1 stays scoped to this repo's own operator-verb shapes,
CALLEE-AGNOSTIC. `os.system`/`shell=True` is DEFAULT-DENIED OUTRIGHT (zero existing occurrences,
zero-false-positive ban). Every refusal carries a per-line WAIVER_TOKEN escape hatch.

WHAT THIS DOES NOT CLAIM:
  - A NAME-LIST census over each file's own REPO/REPO_ROOT/AUTOHARN_ROOT/EXEC_ROOT convention,
    not alias/call-graph analysis. `simulate_list_states` (round 2) follows append/insert/
    extend/subscript-assign/del/+=  for ONE Name at a time, in LINE ORDER ONLY -- no
    control-flow awareness (a branch/loop is read as if every arm always ran in textual order;
    see gates/_pin_guard_resolve.py's own docstring). A path/argv behind a function parameter,
    a dict value, piecemeal string concat this module doesn't recognize, or a name that is
    reassigned inside a branch this gate reads straight through, stays invisible or
    approximated, never silently trusted past the point this module can no longer follow it
    (an unfollowable mutation on a name that was ever repo-verb-bearing is flagged, not ignored).
  - Cross-module constant import (finding 6 above) -- named, not fixed.
  - Verb vocabulary: shim-verbs.sh's SHIM_VERBS_ALL (root shims/scaffold set) + literal
    "autoharn", sourced live -- DIFFERENT roster from libexec/autoharn/'s own live directory
    listing (carries attest-tags/migrate, omits verify-commission/attest-doc) -- each shape
    checked against its own authoritative roster.
  - `.update(opaque_dict_variable)` is not traced to its own construction; only an inline dict
    literal or a PICKUP_DEPLOYMENT= keyword is recognized. `os.system` under an import alias is
    not recognized.
  - The fourth leak kind -- reading whatever deployment.json sits in os.getcwd() -- is
    `serve_existing_world`'s own job (this gate's complement, not its duplicate).
  - WAIVER_TOKEN is presence-only; it cannot judge whether the stated reason is sound. A waiver
    is a claim reviewed like any other, never a silent bypass -- and (round 2) never one that
    can leak from a binding line to every use, or from one statement to a semicolon-sharing
    neighbor.

SCOPE: seen-red/**/*.py, instruments/**/*.py, kernel/fixtures/**/*.py (submodules excluded).
Exit 0 clean (or every match waived); exit 1 naming every offending line otherwise.

Usage: python3 gates/fixture_deployment_pin_guard.py [path ...]
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # gates/_pin_guard_resolve.py, same dir
from _pin_guard_resolve import (  # noqa: E402  (path insert above must run first)
    argv_elements,
    dispatcher_invocation_is_safe,
    repo_like_or_default,
    resolve_verb_element,
    simulate_list_states,
    verb_path_bindings,
)

REPO = Path(__file__).resolve().parents[1]
SCAN_DIRS = ("seen-red", "instruments", "kernel/fixtures")
DISPATCHER_NAME = "autoharn"  # execs into libexec/autoharn/<verb>; same hazard, one hop removed
WAIVER_TOKEN = "fixture-scratch-pinning-guard-waiver:"
SUBPROCESS_CALL_ATTRS = {"run", "Popen", "check_call", "check_output", "call"}

def _shim_verb_names() -> set[str]:
    """Root-shim/scaffold verb roster (shim-verbs.sh SHIM_VERBS_ALL + dispatcher name) -- a DIFFERENT roster from `_libexec_verb_names()` (see module docstring)."""
    out = subprocess.run(
        ["sh", "-c", f". {REPO / 'bootstrap' / 'shim-verbs.sh'} && printf '%s' \"$SHIM_VERBS_ALL\""],
        capture_output=True, text=True, check=True)
    return set(out.stdout.split()) | {DISPATCHER_NAME}

def _libexec_verb_names() -> set[str]:
    """The `libexec/autoharn/<verb>` roster, sourced LIVE from the real directory listing."""
    d = REPO / "libexec" / "autoharn"
    return {p.name for p in d.iterdir() if p.is_file()} if d.is_dir() else set()

def _iter_target_files() -> list[Path]:
    files: list[Path] = []
    for d in SCAN_DIRS:
        base = REPO / d
        if base.is_dir():
            files.extend(sorted(base.rglob("*.py")))
    return files

def _read_source(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

def _ambiguous_statement_lines(tree: ast.Module) -> set[int]:
    """Linenos hosting MORE THAN ONE top-level statement (semicolon-sharing, finding 7) -- a
    waiver comment on such a line is refused (see `_span_has_waiver`): it can't be trusted to
    describe only the statement it looks like it sits next to."""
    counts: dict[int, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.stmt):
            counts[node.lineno] = counts.get(node.lineno, 0) + 1
    return {ln for ln, n in counts.items() if n > 1}

def _span_has_waiver(node: ast.AST, lines: list[str], ambiguous_lines: set[int]) -> bool:
    """WAIVER_TOKEN presence anywhere from `node`'s first to last line inclusive -- but a token
    sitting on an AMBIGUOUS (semicolon-sharing) line never counts (finding 7)."""
    start = node.lineno
    end = getattr(node, "end_lineno", None) or start
    for n in range(start, end + 1):
        if 1 <= n <= len(lines) and WAIVER_TOKEN in lines[n - 1] and n not in ambiguous_lines:
            return True
    return False

def _is_environ_attr(node: ast.expr, environ_aliases: set[str]) -> bool:
    """Whether `node` denotes the LIVE os.environ mapping -- bare attribute or tracked alias (NOT `.copy()`, an independent dict, the sanctioned pattern)."""
    if isinstance(node, ast.Attribute) and node.attr == "environ" \
            and isinstance(node.value, ast.Name) and node.value.id == "os":
        return True
    return isinstance(node, ast.Name) and node.id in environ_aliases

def _environ_aliases(tree: ast.Module) -> set[str]:
    """Names bound directly to the LIVE os.environ object (`d = os.environ`, NOT `.copy()`) -- mutating through the alias still hits the same process-global mapping."""
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) \
                and isinstance(node.value, ast.Attribute) and node.value.attr == "environ" \
                and isinstance(node.value.value, ast.Name) and node.value.value.id == "os":
            out.add(node.targets[0].id)
    return out

def _const_str(node: ast.expr | None) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None

def _is_environ_pickup_deployment_subscript_assign(node: ast.Assign, environ_aliases: set[str]) -> bool:
    """`os.environ["PICKUP_DEPLOYMENT"] = ...` (direct or via a tracked alias)."""
    if len(node.targets) != 1:
        return False
    t = node.targets[0]
    if not isinstance(t, ast.Subscript):
        return False
    return _const_str(t.slice) == "PICKUP_DEPLOYMENT" and _is_environ_attr(t.value, environ_aliases)

def _dict_has_pickup_deployment_key(node: ast.expr) -> bool:
    return isinstance(node, ast.Dict) and any(_const_str(k) == "PICKUP_DEPLOYMENT" for k in node.keys)

def _environ_mutation_call_kind(node: ast.Call, environ_aliases: set[str]) -> str | None:
    """`.update(...)` (dict-literal/keyword) or `.setdefault(...)` carrying PICKUP_DEPLOYMENT --
    same violation as subscript-assign. `.update(opaque_dict_var)` is not traced (blind spot)."""
    f = node.func
    if not (isinstance(f, ast.Attribute) and _is_environ_attr(f.value, environ_aliases)):
        return None
    if f.attr == "update":
        if any(kw.arg == "PICKUP_DEPLOYMENT" for kw in node.keywords):
            return "update"
        if any(_dict_has_pickup_deployment_key(a) for a in node.args):
            return "update"
        return None
    if f.attr == "setdefault" and node.args and _const_str(node.args[0]) == "PICKUP_DEPLOYMENT":
        return "setdefault"
    return None

def _is_subprocess_like_call(node: ast.Call) -> bool:
    f = node.func
    return (isinstance(f, ast.Attribute) and f.attr in SUBPROCESS_CALL_ATTRS) \
        or (isinstance(f, ast.Name) and f.id in SUBPROCESS_CALL_ATTRS)

def _is_os_system_call(node: ast.Call) -> bool:
    f = node.func
    return isinstance(f, ast.Attribute) and f.attr == "system" \
        and isinstance(f.value, ast.Name) and f.value.id == "os"

def _has_shell_true(node: ast.Call) -> bool:
    return any(kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True
               for kw in node.keywords)

def violations_in(path: Path, shim_verbs: set[str], libexec_verbs: set[str]) -> list[str]:
    src = _read_source(path)
    if src is None:
        return []
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError:
        return []
    lines = src.splitlines()
    repo_names = repo_like_or_default(tree)
    verb_bindings = verb_path_bindings(tree, repo_names, shim_verbs, libexec_verbs)
    list_states = simulate_list_states(tree, repo_names, shim_verbs, libexec_verbs, verb_bindings)
    environ_aliases = _environ_aliases(tree)
    ambiguous_lines = _ambiguous_statement_lines(tree)
    out: list[str] = []
    display = str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)

    def _flag(lineno: int, msg: str) -> None:
        out.append(f"{display}:{lineno}: {msg} Waive with `{WAIVER_TOKEN} <reason>` if proven safe.")

    # CHECK 1 (leak class a): argv names a REPO-rooted verb path (root shim, libexec/autoharn/
    # <verb>, or the autoharn dispatcher) instead of a scaffolded scratch copy. Callee-agnostic,
    # scans EVERY positional Call argument (round 2, finding 5 -- not just args[0], so
    # `functools.partial(subprocess.run, argv)` is covered), resolving one hop of argv-list-Name
    # AND verb-path-constant indirection, with post-binding mutation replayed (round 2, findings
    # 2/4) rather than trusted from the original literal.
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if _span_has_waiver(node, lines, ambiguous_lines):
            continue
        for arg in node.args:
            elts, opaque_sensitive = argv_elements(arg, list_states)
            if opaque_sensitive:
                name = arg.id if isinstance(arg, ast.Name) else "?"
                _flag(node.lineno,
                      f"argv list `{name}` carried a repo-rooted verb element at some point but "
                      f"was later mutated (subscript-assign/`.insert`/non-literal `.extend`/`del` "
                      f"with a non-constant index, or a non-list `+=`) in a way this gate cannot "
                      f"statically verify -- static safety proof voided (row 1249 fix-round 2, "
                      f"finding 2/4). Use a direct inline literal or waive at this call site.")
                continue
            if elts is None:
                continue
            for i, elt in enumerate(elts):
                verb = resolve_verb_element(elt, repo_names, shim_verbs, libexec_verbs, verb_bindings)
                if verb is None:
                    continue
                if verb == DISPATCHER_NAME and dispatcher_invocation_is_safe(elts, i, libexec_verbs):
                    continue
                _flag(node.lineno,
                      f"call invokes THIS CHECKOUT'S OWN `{verb}` (a REPO-rooted path, or a "
                      f"constant bound to one) instead of a scaffolded scratch copy -- root-level "
                      f"verb shims and libexec/autoharn/<verb> resolve deployment from their own "
                      f"file location, never a caller's env override (row 1249; the row-1237-1244/"
                      f"1248 leak class).")

    # CHECK 1b (leak class c): os.system(...)/shell=True sidesteps CHECK 1's argv-shape matching
    # entirely; DEFAULT-DENIED, not pattern-matched (see POSTURE).
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or _span_has_waiver(node, lines, ambiguous_lines):
            continue
        if _is_os_system_call(node):
            _flag(node.lineno, "`os.system(...)` spawns via a shell string, never an argv list -- "
                  "refused outright (unenumerable repo-path spelling; use subprocess.run([...])).")
        elif _is_subprocess_like_call(node) and _has_shell_true(node):
            _flag(node.lineno, "subprocess call with shell=True spawns via a shell string -- "
                  "refused outright, same reason as os.system(...) above.")

    # CHECK 2 (leak class b): os.environ["PICKUP_DEPLOYMENT"] mutation -- direct, aliased, or via
    # .update()/.setdefault() -- never per-subprocess.
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) \
                and _is_environ_pickup_deployment_subscript_assign(node, environ_aliases) \
                and not _span_has_waiver(node, lines, ambiguous_lines):
            _flag(node.lineno,
                  "`os.environ[\"PICKUP_DEPLOYMENT\"] = ...` (directly or aliased) mutates the "
                  "PROCESS-GLOBAL environment instead of pinning per-subprocess (build a local "
                  "`env = {**os.environ, \"PICKUP_DEPLOYMENT\": ...}` dict, pass via each call's "
                  "own `env=` kwarg -- row 1249).")
        elif isinstance(node, ast.Call):
            kind = _environ_mutation_call_kind(node, environ_aliases)
            if kind and not _span_has_waiver(node, lines, ambiguous_lines):
                _flag(node.lineno,
                      f"`os.environ.{kind}(...)` (directly or aliased) merges PICKUP_DEPLOYMENT "
                      f"into the PROCESS-GLOBAL environment -- same violation as a direct "
                      f"subscript assign (row 1249).")

    return out

def main(argv: list[str]) -> int:
    shim_verbs = _shim_verb_names()
    libexec_verbs = _libexec_verb_names()
    targets = [Path(a).resolve() for a in argv] if argv else _iter_target_files()
    bad: list[str] = []
    for t in targets:
        bad.extend(violations_in(t, shim_verbs, libexec_verbs))
    if bad:
        print(f"FIXTURE DEPLOYMENT PIN GUARD VIOLATIONS ({len(bad)}) -- "
              f"fixture-scratch-pinning-guard (ledger row 1249):")
        print("\n".join(bad))
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
