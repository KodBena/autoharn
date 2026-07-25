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
and argv resolution AST helpers live in gates/_pin_guard_resolve.py (split to keep both files
well under ADR-0007's 400-line ceiling); this file owns the entry point, the checks that walk
each file, and every verdict/waiver string.

POSTURE, ROUND 3 -- A SHAPE CHANGE (fresh-context strengthened-tier review BLOCKED 8821dff,
round 2's `simulate_list_states` replay engine, with two HIGH SILENT holes: (A) a name made
opaque by a dynamic-index/slice assign or non-literal `.extend` BEFORE it ever carried a
sensitive element silently dropped every LATER sensitive append -- excluded from the final dict,
no flag; (B) a one-hop alias (`b = cmd; b.append(str(REPO/'led'))`) was read as an "unbind" event
for `b`, silently discarded, while `cmd`'s own stale state kept being checked as if the append
had never happened. Plus two disclosed-but-real approximations: (C) the replay's line-number sort
had zero scope awareness, so a helper defined above and called later replayed its mutation BEFORE
the binding it poisons; (D) branch/loop textual-order under-approximation.

THE ORCHESTRATOR'S RULING, proven out over three rounds by three successive reviewers: static
analysis of arbitrary Python dataflow always loses one rung up to the next live evasion -- every
additional replay rule is just the next silent hole waiting to be found. So this round INVERTS
the posture instead of shipping a fourth replay refinement. This gate now PROVES safety only for
argv shapes it can fully see, and refuses everything else that ever touches this repo's own verb
vocabulary as UNPROVEN, with a waiver escape hatch:
  1. A direct inline literal (List/Tuple) argv AT THE CALL SITE -- provable, analyzed exactly as
     every prior round did (no Name involved at all).
  2. A Name-bound argv whose binding is a literal AND which has ZERO other qualifying events
     anywhere in the file (any `.append`/`.extend`/`.insert`/subscript/slice/`del`/`+=`/alias-
     assign/pass-to-another-call -- scope-blind, conservative: if it can't be ruled out, it
     counts) -- provable, use the binding literal.
  3. EVERYTHING ELSE that is ever "sensitive" (an element anywhere resolves to one of this
     repo's own operator-verb paths) -- UNPROVEN. Refused outright, naming the call line, the
     reason ("argv dataflow not statically provable"), and the waiver instruction.
`simulate_list_states` and its line-order replay are DELETED (gates/_pin_guard_resolve.py's
`analyze_names` / `resolve_tracked_names` replace it) -- there is no more "final contents" to
reconstruct, so there is no more order to get wrong: this is what DISSOLVES round-2's findings C
and D and this round's findings A and B, rather than patching around them. Aliasing (`x = y`)
does not get followed -- it CONTAMINATES: if either name is ever sensitive, BOTH are unproven,
regardless of either one's own local event count (closes finding B directly).

MEASURED against the real tree (this fix-round): the inversion's false-positive surface --
Name-bound argv lists that are sensitive but fail the "exactly one literal binding, zero other
events" test -- was ONE file, `seen-red/fixture-deployment-pin-guard/run_fixtures.py`'s own
`RED_WRAPPER_INDIRECTED`/`RED_SUBSCRIPT_MUTATION`/`RED_APPEND_BUILT_ARGV` synthetic RED fixtures
(they are SUPPOSED to refuse now -- that is the honest verdict for a wrapper-indirected or
post-binding-mutated argv, not a false positive against real code). No REAL file under
seen-red/**, instruments/**, or kernel/fixtures/** newly refuses under the inversion; every real
driver in this corpus invokes its argv as a direct inline literal at the subprocess call site
(CHECK 1's original, always-provable shape), never through a tracked Name with a disqualifying
event. Below ~10 files by a wide margin -- no blanket-waiving or refactor was needed this round.

ROUND 1/2 findings, disposition unchanged by this round except where noted:
  1. (round 2) Waiver span is the USE site (the Call's own line/lines) only, never a constant's
     binding line -- unaffected by this round's inversion.
  2/4. (round 2, SUPERSEDED this round) Post-binding argv mutation used to be "fixed" by
     replaying the mutation; round 3 instead refuses these shapes outright as UNPROVEN -- see
     POSTURE above. The replay is deleted, not patched.
  3. (round 2) `os.path.join`/`.joinpath` recognized alongside `/`-BinOp and f-string shapes --
     unaffected, still lives in `names_repo_verb_join`.
  5. (round 2) CHECK 1 scans every positional Call argument, not only `args[0]` -- unaffected.
  6. DISCLOSED, not fixed: a verb-path constant imported from another module is invisible --
     single-file AST census, stops at the file boundary by construction (still true).
  7. (round 2) A waiver on a semicolon-sharing line never counts -- unaffected.

ROUND 1 POSTURE (unchanged, kept for context): FULL INVERSION OF SCOPE (refuse any subprocess-
spawning file outright absent a waiver) was measured against the real tree and rejected: ~150 of
203 in-scope files make a direct subprocess call, overwhelmingly git/psql/ls with nothing to do
with this repo's own verbs. CHECK 1 stays scoped to this repo's own operator-verb shapes,
CALLEE-AGNOSTIC. `os.system`/`shell=True` is DEFAULT-DENIED OUTRIGHT (zero existing occurrences,
zero-false-positive ban). Every refusal carries a per-line WAIVER_TOKEN escape hatch. (Round 3's
inversion is a NARROWER, different move: it does not refuse every subprocess-spawning file, only
the Name-bound argv shapes this gate cannot prove safe for its own verb vocabulary.)

WHAT THIS GATE NOW CLAIMS, AND DOES NOT CLAIM (the honest summary this round's commission asked
for): it PROVES a call is safe only when its argv is a literal at the call site or a Name with
exactly one literal binding and no other event touching it anywhere in the file; every other
argv that ever carries one of this repo's own verb paths is REFUSED-AS-UNPROVEN, never
approximated -- there is no code path left in this gate that trusts a partial, stale, or
best-effort reconstruction of a mutable list's contents. A waiver at the refusing call site is
the only way past a such a refusal, and it is a reviewed claim, not a silent bypass. What it does
NOT claim: safety for argv that never appears as a literal or tracked Name in this file at all
(a function parameter, a dict value, ad hoc string formatting), or for a verb-path constant
imported from another module -- both are disclosed blind spots, not silently-passed cases, and an
argv this gate has no repo-verb interest in at all (an ordinary git/psql invocation) stays out of
scope exactly as before.

WHAT THIS DOES NOT CLAIM (mechanical detail, carried forward):
  - A NAME-LIST census over each file's own REPO/REPO_ROOT/AUTOHARN_ROOT/EXEC_ROOT convention,
    not alias/call-graph analysis. See gates/_pin_guard_resolve.py's own docstring for the exact
    provable-vs-unproven contract and the full list of qualifying events.
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
    is a claim reviewed like any other, never a silent bypass, and never one that can leak from
    a binding line to every use, or from one statement to a semicolon-sharing neighbor.

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
    SUBPROCESS_CALL_ATTRS,
    argv_provenance,
    dispatcher_invocation_is_safe,
    repo_like_or_default,
    resolve_tracked_names,
    resolve_verb_element,
    verb_path_bindings,
)

REPO = Path(__file__).resolve().parents[1]
SCAN_DIRS = ("seen-red", "instruments", "kernel/fixtures")
DISPATCHER_NAME = "autoharn"  # execs into libexec/autoharn/<verb>; same hazard, one hop removed
WAIVER_TOKEN = "fixture-scratch-pinning-guard-waiver:"

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
    tracked = resolve_tracked_names(tree, repo_names, shim_verbs, libexec_verbs, verb_bindings)
    environ_aliases = _environ_aliases(tree)
    ambiguous_lines = _ambiguous_statement_lines(tree)
    out: list[str] = []
    display = str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)

    def _flag(lineno: int, msg: str) -> None:
        out.append(f"{display}:{lineno}: {msg} Waive with `{WAIVER_TOKEN} <reason>` if proven safe.")

    # CHECK 1 (leak class a): argv names a REPO-rooted verb path (root shim, libexec/autoharn/
    # <verb>, or the autoharn dispatcher) instead of a scaffolded scratch copy. Callee-agnostic,
    # scans EVERY positional Call argument (not just args[0], so `functools.partial(subprocess.run,
    # argv)` is covered). PROVE-OR-REFUSE (fix-round 3, see POSTURE): an argv is analyzed only when
    # it is a direct inline literal at the call site, or a Name proven safe by
    # `resolve_tracked_names` (exactly one literal binding, zero other events anywhere in the
    # file); every other argv that ever carried one of this repo's own verb paths is refused
    # outright as UNPROVEN, never approximated from a partial or stale reconstruction.
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if _span_has_waiver(node, lines, ambiguous_lines):
            continue
        for arg in node.args:
            elts, unproven = argv_provenance(arg, tracked)
            if unproven:
                name = arg.id if isinstance(arg, ast.Name) else "?"
                _flag(node.lineno,
                      f"argv `{name}` is repo-verb-bearing (resolves to one of this repo's own "
                      f"operator-verb paths at some point) but its dataflow is not statically "
                      f"provable -- rebound more than once, mutated (`.append`/`.extend`/"
                      f"`.insert`/subscript/slice/`del`/`+=`/`.remove`/`.pop`/`.sort`/`.reverse`/"
                      f"`.clear`), aliased (`x = y`), or passed as a bare argument to another "
                      f"call anywhere in this file -- argv dataflow not statically provable, so "
                      f"this gate refuses rather than trust a partial or stale reconstruction "
                      f"(row 1249 fix-round 3: PROVE-OR-REFUSE, not better simulation). Use a "
                      f"direct inline literal argv at this call site, or waive here naming the "
                      f"reviewed invariant that makes it safe.")
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
