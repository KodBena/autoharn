#!/usr/bin/env python3
"""_pin_guard_checks.py -- the per-file walk and every verdict/waiver string for
gates/fixture_deployment_pin_guard.py (ledger row 1249; split out in fix-round 4 to keep the
entry-point file's docstring room under ADR-0007's 400-line ceiling once round 4's MEASUREMENT
section made that docstring long -- see that file's own module docstring for the full narrative,
`_pin_guard_argv.py`/`_pin_guard_resolve.py`/`_pin_guard_census.py` for the analysis this module
calls into). `violations_in` is the whole per-file check; `main()` in the entry-point file just
resolves the verb rosters, iterates target files, and prints."""
from __future__ import annotations

import ast
import subprocess
from pathlib import Path

from _pin_guard_argv import SUBPROCESS_CALL_ATTRS, argv_provenance, resolve_tracked_names
from _pin_guard_resolve import (
    bare_verb_literal,
    dispatcher_invocation_is_safe,
    repo_like_or_default,
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

def _flatten_argv_elements(elts: list[ast.expr]) -> list[ast.expr]:
    """Finding 6c: a `Starred` element that itself wraps an inline List/Tuple literal
    (`[*[str(REPO / "led")], "status"]`) has its OWN elements inspected in place, recursively. A
    `Starred` wrapping anything else (`*args`, a Subscript, a comprehension -- the real corpus's
    only observed Starred shape, measured zero collisions against the verb grammar) is left as an
    opaque, unclassified element: neither flagged nor specially recognized, same as any other
    expression this gate has no verb-shape interest in (see MEASUREMENT in the module docstring
    for why this stops short of a blanket per-element classification)."""
    flat: list[ast.expr] = []
    for e in elts:
        if isinstance(e, ast.Starred) and isinstance(e.value, (ast.List, ast.Tuple)):
            flat.extend(_flatten_argv_elements(e.value.elts))
        else:
            flat.append(e)
    return flat

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
    # <verb>, the autoharn dispatcher, or (round 4) a BARE literal naming one of those verbs with
    # no path join at all) instead of a scaffolded scratch copy. Callee-agnostic, scans EVERY
    # positional AND keyword Call argument (final round, one-line widening: a keyword-passed argv
    # -- `subprocess.run(args=[...])`, `functools.partial(subprocess.run, args=[...])` -- used to
    # be invisible because only `node.args` was ever walked; disclosed as a known-uncaught idiom
    # through fix-round 4, closed here as a pure widening of this same loop, no new analysis
    # machinery -- see the gate module docstring's FINAL ROUND section). PROVE-OR-REFUSE (round 3):
    # an argv is analyzed only when it is a direct inline literal at the call site, or a Name
    # proven safe by `resolve_tracked_names` (exactly one literal binding, zero other events
    # anywhere in the file, now including every census-swept binding shape -- round 4, see module
    # docstring); every other argv that ever carried one of this repo's own verb paths is refused
    # outright as UNPROVEN.
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if _span_has_waiver(node, lines, ambiguous_lines):
            continue
        for arg in list(node.args) + [kw.value for kw in node.keywords]:
            elts, unproven, kinds = argv_provenance(arg, tracked)
            if unproven:
                name = arg.id if isinstance(arg, ast.Name) else "?"
                kind_note = (f" This name was also touched by a round-4 census-swept binding "
                             f"construct this gate cannot model precisely: "
                             f"{', '.join(sorted(kinds))}.") if kinds else ""
                _flag(node.lineno,
                      f"argv `{name}` is repo-verb-bearing (resolves to one of this repo's own "
                      f"operator-verb paths at some point) but its dataflow is not statically "
                      f"provable -- rebound more than once, mutated (`.append`/`.extend`/"
                      f"`.insert`/subscript/slice/`del`/`+=`/`.remove`/`.pop`/`.sort`/`.reverse`/"
                      f"`.clear`), aliased (`x = y`, including a tuple-swap), or passed as a bare "
                      f"argument to another call anywhere in this file -- argv dataflow not "
                      f"statically provable, so this gate refuses rather than trust a partial or "
                      f"stale reconstruction (row 1249 fix-round 3/4: PROVE-OR-REFUSE, not better "
                      f"simulation).{kind_note} Use a direct inline literal argv at this call "
                      f"site, or waive here naming the reviewed invariant that makes it safe.")
                continue
            if elts is None:
                continue
            flat = _flatten_argv_elements(elts)
            for i, elt in enumerate(flat):
                verb = resolve_verb_element(elt, repo_names, shim_verbs, libexec_verbs, verb_bindings)
                if verb is not None:
                    if verb == DISPATCHER_NAME and dispatcher_invocation_is_safe(flat, i, libexec_verbs):
                        continue
                    _flag(node.lineno,
                          f"call invokes THIS CHECKOUT'S OWN `{verb}` (a REPO-rooted path, or a "
                          f"constant bound to one) instead of a scaffolded scratch copy -- root-level "
                          f"verb shims and libexec/autoharn/<verb> resolve deployment from their own "
                          f"file location, never a caller's env override (row 1249; the row-1237-1244/"
                          f"1248 leak class).")
                    continue
                bare = bare_verb_literal(elt, i, shim_verbs)
                if bare is not None:
                    if bare == DISPATCHER_NAME and dispatcher_invocation_is_safe(flat, i, libexec_verbs):
                        continue
                    _flag(node.lineno,
                          f"argv[0] is the BARE literal `{elt.value!r}` naming this checkout's own "
                          f"`{bare}` verb with NO REPO-path join at all (row 1249 fix-round 4, "
                          f"finding 4 -- the leak class's most literal spelling: relies on `cwd`/"
                          f"`PATH` resolution, which this gate does not attempt to prove or "
                          f"disprove). If `cwd` genuinely points at a scaffolded scratch copy, "
                          f"waive here naming that invariant.")

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
