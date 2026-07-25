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

Grep/AST CENSUS gate (gates/no_lazy_imports.py's own family), not a dataflow prover.

POSTURE (fresh-context strengthened-tier review, this fix-round -- BLOCKS MERGE on the prior
version; full reasoning and the false-positive measurement live in this fix's commit report, not
duplicated here). Finding 4: the prior CHECK 1 (subprocess.{run,...}, inline List/Tuple first
arg) under-delivers -- the real corpus's dominant shape is a WRAPPER call or a module CONSTANT
bound once (`LED_TMPL`, `ATTEST_TAGS`, `AUTOHARN`) and referenced by name, essentially never an
inline literal. FULL INVERSION (refuse any subprocess-spawning file outright absent a waiver) was
measured against the real tree and rejected: ~150 of 203 in-scope files make a direct subprocess
call, overwhelmingly git/psql/ls with nothing to do with this repo's own verbs -- inversion would
force waivers onto ~50 files for unrelated reasons. Shape shipped, the HONEST MIDDLE:
  - CHECK 1 stays scoped to this repo's own operator-verb shapes (now incl. libexec/autoharn/
    <verb> and the bare `autoharn` dispatcher), CALLEE-AGNOSTIC, resolving ONE hop of Name-binding
    indirection (argv list AND verb-path constant) -- closes finding 4 without a call-graph.
  - os.system/shell=True (finding 1) is DEFAULT-DENIED OUTRIGHT rather than pattern-matched
    inside the string (would recreate finding 4's own gap one level down) -- zero existing
    occurrences in the corpus, so a zero-false-positive ban.
  - Every refusal carries a per-line/per-binding WAIVER_TOKEN escape hatch (textual presence,
    same convention as gates/deep_walk_recursion_guard.py) -- PER-LINE, not per-file, so a waiver
    never blesses an unrelated future line. Exactly TWO real files needed one under this shape.

WHAT THIS DOES NOT CLAIM:
  - A NAME-LIST census over each file's own REPO/REPO_ROOT/AUTOHARN_ROOT/EXEC_ROOT convention, not
    alias/call-graph analysis. One hop of Name-binding resolved (argv list, verb-path constant); a
    path/argv behind TWO+ hops, a function parameter, a dict value, or piecemeal string concat
    stays invisible.
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
    is a claim reviewed like any other, never a silent bypass.

SCOPE: seen-red/**/*.py, instruments/**/*.py, kernel/fixtures/**/*.py (submodules excluded).
Exit 0 clean (or every match waived); exit 1 naming every offending line otherwise.

Usage: python3 gates/fixture_deployment_pin_guard.py [path ...]
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCAN_DIRS = ("seen-red", "instruments", "kernel/fixtures")
REPO_LIKE_NAMES = {"REPO", "AUTOHARN_ROOT", "EXEC_ROOT", "REPO_ROOT"}
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

def _repo_join_targets(tree: ast.Module) -> set[str]:  # top-level names bound to a REPO-like Path
    bound: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) and node.targets[0].id in REPO_LIKE_NAMES:
            bound.add(node.targets[0].id)
    return bound

def _repo_like_or_default(tree: ast.Module) -> set[str]:
    return _repo_join_targets(tree) or set(REPO_LIKE_NAMES)

def _const_str(node: ast.expr | None) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None

def _unwrap_str_call(node: ast.expr) -> ast.expr:  # `str(X)` -> `X`
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "str" \
            and len(node.args) == 1:
        return node.args[0]
    return node

def _peel_join_chain(node: ast.expr, repo_names: set[str]) -> list[str] | None:
    """Peels a `<expr> / "<component>"` BinOp chain to its ordered components iff the base is a bare Name in `repo_names` and every right side is a string constant; None otherwise."""
    parts: list[str] = []
    cur = node
    while isinstance(cur, ast.BinOp) and isinstance(cur.op, ast.Div):
        right = _const_str(cur.right)
        if right is None:
            return None
        parts.append(right)
        cur = cur.left
    if isinstance(cur, ast.Name) and cur.id in repo_names:
        parts.reverse()
        return parts
    return None

def _verb_from_join_parts(parts: list[str], shim_verbs: set[str], libexec_verbs: set[str]
                           ) -> str | None:
    """Which operator-verb shape `parts` spells: `<verb>`/`legacy/<verb>` (vs `shim_verbs`) or `libexec/autoharn/<verb>` (vs `libexec_verbs`) -- None otherwise (e.g. the SAFE `.tmpl` shape)."""
    if len(parts) == 1 and parts[0] in shim_verbs:
        return parts[0]
    if len(parts) == 2 and parts[0] == "legacy" and parts[1] in shim_verbs:
        return parts[1]
    if len(parts) == 3 and parts[0] == "libexec" and parts[1] == "autoharn" and parts[2] in libexec_verbs:
        return parts[2]
    return None

def _names_repo_verb_join(node: ast.expr, repo_names: set[str], shim_verbs: set[str],
                           libexec_verbs: set[str]) -> str | None:
    """The offending verb if `node` spells one of this repo's operator-verb paths, optionally `str(...)`-wrapped, or via f-string/`+`-concat."""
    node = _unwrap_str_call(node)
    all_verbs = shim_verbs | libexec_verbs
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        parts = _peel_join_chain(node, repo_names)
        return _verb_from_join_parts(parts, shim_verbs, libexec_verbs) if parts is not None else None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = node.left, node.right
        right_s = _const_str(right)
        if right_s and isinstance(left, ast.Call) and isinstance(left.func, ast.Name) \
                and left.func.id == "str" and len(left.args) == 1 \
                and isinstance(left.args[0], ast.Name) and left.args[0].id in repo_names:
            tail = right_s.strip("/")
            for v in all_verbs:
                if (v in shim_verbs and (tail == v or tail.endswith(f"legacy/{v}"))) \
                        or (v in libexec_verbs and tail.endswith(f"libexec/autoharn/{v}")):
                    return v
        return None
    if isinstance(node, ast.JoinedStr):
        for i, part in enumerate(node.values):
            if isinstance(part, ast.FormattedValue) and isinstance(part.value, ast.Name) \
                    and part.value.id in repo_names and i + 1 < len(node.values):
                nxt = node.values[i + 1]
                if isinstance(nxt, ast.Constant) and isinstance(nxt.value, str):
                    tail = nxt.value.lstrip("/")
                    for v in all_verbs:
                        if v in shim_verbs and (tail == v or tail.startswith(f"{v}/")
                                                 or tail.startswith(f"{v} ")
                                                 or tail.startswith(f"legacy/{v}")):
                            return v
                        if v in libexec_verbs and tail.startswith(f"libexec/autoharn/{v}"):
                            return v
        return None
    return None

def _verb_path_bindings(tree: ast.Module, repo_names: set[str], shim_verbs: set[str],
                         libexec_verbs: set[str]) -> dict[str, tuple[str, ast.Assign]]:
    """Name -> (verb, defining-Assign) per top-level `NAME = <repo-verb-join-expr>` binding (the DOMINANT convention: LED_TMPL/ATTEST_TAGS/AUTOHARN) -- closes finding 4, one hop."""
    out: dict[str, tuple[str, ast.Assign]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            verb = _names_repo_verb_join(node.value, repo_names, shim_verbs, libexec_verbs)
            if verb:
                out[node.targets[0].id] = (verb, node)
    return out

def _bound_list_literals(tree: ast.Module) -> dict[str, ast.List | ast.Tuple]:
    """Name -> last List/Tuple literal assigned to it anywhere (pre-built-argv: `cmd = [...]; subprocess.run(cmd)`). Last-assignment-wins, module-wide -- a census simplification."""
    out: dict[str, ast.List | ast.Tuple] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) \
                and isinstance(node.value, (ast.List, ast.Tuple)):
            out[node.targets[0].id] = node.value
    return out

def _span_has_waiver(node: ast.AST, lines: list[str]) -> bool:
    """WAIVER_TOKEN presence anywhere from `node`'s first to last line inclusive."""
    start = node.lineno
    end = getattr(node, "end_lineno", None) or start
    return any(1 <= n <= len(lines) and WAIVER_TOKEN in lines[n - 1] for n in range(start, end + 1))

def _argv_elements(first_arg: ast.expr, bound_lists: dict[str, ast.List | ast.Tuple]
                    ) -> list[ast.expr]:
    """`first_arg` itself if inline List/Tuple, or (one hop) the List/Tuple bound to it if a bare Name in `bound_lists`. Empty otherwise."""
    if isinstance(first_arg, (ast.List, ast.Tuple)):
        return list(first_arg.elts)
    if isinstance(first_arg, ast.Name) and first_arg.id in bound_lists:
        return list(bound_lists[first_arg.id].elts)
    return []

def _resolve_verb_element(elt: ast.expr, repo_names: set[str], shim_verbs: set[str],
                           libexec_verbs: set[str],
                           verb_bindings: dict[str, tuple[str, ast.Assign]]
                           ) -> tuple[str, ast.AST] | None:
    """Whether `elt` names this repo's own operator-verb path, direct or one hop of the module-constant convention. Returns (verb, waiver-node): the call site, or the binding's own Assign."""
    direct = _names_repo_verb_join(elt, repo_names, shim_verbs, libexec_verbs)
    if direct:
        return direct, elt
    unwrapped = _unwrap_str_call(elt)
    if isinstance(unwrapped, ast.Name) and unwrapped.id in verb_bindings:
        return verb_bindings[unwrapped.id]
    return None

def _dispatcher_invocation_is_safe(elts: list[ast.expr], i: int, libexec_verbs: set[str]) -> bool:
    """Safe by the dispatcher's OWN branching: bare `autoharn`, `--help`/`-h`/`help` (returns
    before LIBEXEC), `service` (env-parameterized libexec/autoharn-service), or any non-relocated
    constant (refused before touching anything). Only a REAL verb constant, or a non-constant
    (a loop variable), is dangerous -- fail-safe: unknown stays flagged."""
    if i + 1 >= len(elts):
        return True
    s = _const_str(elts[i + 1])
    if s is None:
        return False
    if s in {"--help", "-h", "help", "service"}:
        return True
    return s not in libexec_verbs

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
    repo_names = _repo_like_or_default(tree)
    verb_bindings = _verb_path_bindings(tree, repo_names, shim_verbs, libexec_verbs)
    bound_lists = _bound_list_literals(tree)
    environ_aliases = _environ_aliases(tree)
    out: list[str] = []
    display = str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)

    def _flag(lineno: int, msg: str) -> None:
        out.append(f"{display}:{lineno}: {msg} Waive with `{WAIVER_TOKEN} <reason>` if proven safe.")

    # CHECK 1 (leak class a): argv names a REPO-rooted verb path (root shim, libexec/autoharn/
    # <verb>, or the autoharn dispatcher) instead of a scaffolded scratch copy. Callee-agnostic,
    # resolves one hop of argv-list AND verb-path-constant indirection.
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and node.args:
            elts = _argv_elements(node.args[0], bound_lists)
            for i, elt in enumerate(elts):
                resolved = _resolve_verb_element(elt, repo_names, shim_verbs, libexec_verbs,
                                                  verb_bindings)
                if resolved is None:
                    continue
                verb, waiver_node = resolved
                if verb == DISPATCHER_NAME and _dispatcher_invocation_is_safe(elts, i, libexec_verbs):
                    continue
                if _span_has_waiver(waiver_node, lines) or _span_has_waiver(node, lines):
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
        if not isinstance(node, ast.Call) or _span_has_waiver(node, lines):
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
                and not _span_has_waiver(node, lines):
            _flag(node.lineno,
                  "`os.environ[\"PICKUP_DEPLOYMENT\"] = ...` (directly or aliased) mutates the "
                  "PROCESS-GLOBAL environment instead of pinning per-subprocess (build a local "
                  "`env = {**os.environ, \"PICKUP_DEPLOYMENT\": ...}` dict, pass via each call's "
                  "own `env=` kwarg -- row 1249).")
        elif isinstance(node, ast.Call):
            kind = _environ_mutation_call_kind(node, environ_aliases)
            if kind and not _span_has_waiver(node, lines):
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
