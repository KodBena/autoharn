#!/usr/bin/env python3
"""interpreter_boundary_lint.py — mechanical lint for law/adr/0012's 2026-07-18 amendment,
"The interpreter boundary — a value never crosses as program text" (ADR-0011 Rule-2 trigger
declared met at ledger row 1701: four independent authoring events rediscovered the missing
guard within ~6 hours of the amendment's ratification — row 1637, TUI round-1 finding 7, TUI
round-2 finding 10, and the named-open world-name splice — and the amendment itself pre-named
this exact mechanism: "a lint over verb/scaffold sources that flags expansion or concatenation
inside evaluator-bound text absent an adjacent closed-alphabet validation or carrier call").

WHAT THIS CHECKS. An interpreter boundary is any point where this codebase constructs TEXT a
second evaluator will parse and execute — a shell command line, SQL text, a config file
(.toml/.sql/.conf) a later parser reads. The rule: data crosses that boundary as a VALUE, via
the evaluator's own typed carrier (an argv list, a bound placeholder), never spliced into the
text by string interpolation/concatenation/%%-formatting/.format() — UNLESS a recognized
closed-alphabet guard call (valid_*/..._validate*/validate_*/allowlist*, case-insensitive — see
GUARD_RE below) appears in the same function, which is this codebase's own witnessed shape for
"where no carrier exists, a strict validation to a closed alphabet at the Port" (probes.py's
valid_identifier/valid_hostname, screens.py's per-value validation loop).

SINKS DETECTED (v1):
  1. subprocess/os.system shell sinks — subprocess.run/Popen/call/check_call/check_output with
     shell=True, or os.system(...), whose command text is a single dynamically-built string
     (f-string with interpolation, string concatenation, %%-format, or .format()) rather than a
     plain literal. An argv LIST (the carrier subprocess itself provides) is never flagged, even
     if its individual elements are dynamic — that is exactly P2's typed value-carrier, the
     shape probes.py's own pg_connect/pg_reachable use throughout.
  2. SQL text sinks — a variable named like `sql`/`query` (case-insensitive substring) assigned
     or augmented with a dynamically-built string, or a `.execute(...)` call whose first argument
     is dynamically built.
  3. Evaluator-bound file writes — `<handle>.write(...)` / `Path(...).write_text(...)` with
     dynamically-built content, where the target path's literal suffix (resolved through a
     preceding `open(...)`/`Path(...)` call in the same function, including through
     `os.path.join`'s last literal argument or an f-string's trailing literal segment) is
     .toml, .sql, or .conf — config/query text a second evaluator parses.

SCOPE (v1, deliberately bounded): Python sources under tools/, serving/, gates/, hooks/,
filing/. Shell scripts (bootstrap/*.sh etc.) are OUT of v1 — the shell-side idiom is already
witnessed guarded (bootstrap/teardown-world.sh's allowlist case-statement + `psql -v` carrier,
bootstrap/new-project.sh's parallel shape) and a *shell* parser is a different instrument than
this AST-over-Python lint; a POSIX-sh-AST (or shellcheck-style) successor is named and deferred,
not silently skipped.

SCOPE AMENDMENT — 2026-07-19 (ledger row 1799 finding 4, docstring-only, no detector logic
changed): a witnessed blind spot named honestly rather than left silently absent. SINK 3 above
(evaluator-bound file writes) only matches a `.write(...)`/`.write_text(...)` call whose target
path carries a .toml/.sql/.conf suffix — it does NOT match a config fragment that is *constructed*
by splicing (an f-string over `db`/`role`/`subnets` building a pg_hba.conf-shaped block, e.g.
tools/setup_tui/pghba.py's `generate_block`) and then only ever PRINTED to stdout for an operator
to paste by hand, never passed to `.write(...)`/`.write_text(...)` inside this codebase itself.
That shape is real config text a second evaluator (postgresql's own pg_hba.conf parser, once
pasted) will later parse and execute against — the exact class this amendment's rule covers — but
it matches none of the three v1 sink shapes, so this lint reports zero hits on it regardless of
whether the splice site is guarded. The witnessed instance (pghba.py) was closed by moving its
own validation inside the boundary function directly (`generate_block` now refuses via
`PgHbaValidationError`, ledger row 1799 finding 4) rather than by this lint catching it — this
lint did not catch it, and this amendment says so rather than implying coverage it does not have.
A named successor (SINK 4, deferred, not built here): a print/`ui.say`-rendered evaluator-bound
config fragment, recognized by a call to a print-shaped sink (`print`, a UI-`say`-named method)
whose argument is dynamically built AND whose content is recognizable as evaluator-bound config
text (a heuristic beyond this lint's current structural-suffix-on-a-write-target approach, since
there is no target path to inspect a suffix on) — left unbuilt until a second witnessed instance
of this exact shape justifies the broader recognizer (this docstring's own KNOWN LIMITATIONS
section states the same discipline: a corpus convention is witnessed before it is generalized,
never guessed at).

AST-based (ast.parse + a tree walk), matching gates/no_lazy_imports.py's own instrument choice
and CLI/reporting conventions — not a regex-over-lines, because "expansion or concatenation
inside evaluator-bound text" is a structural property of the parse tree (JoinedStr/BinOp/Call
nodes reaching a sink call), not a lexical one.

KNOWN LIMITATIONS (named from the full-corpus calibration pass, not guessed — every one below
was a real false positive this pass triaged by hand and left unfixed, on purpose, rather than
tuned away by pattern-matching a single file's shape into the general recognizer):
  - Guard detection is SAME-FUNCTION only. A value validated once at a different scope and then
    carried as an already-validated field (serving/boundary_service.py's `BoundaryConfig` —
    `cfg.schema`/`cfg.kern`/`cfg.role` are regex-checked once at construction, in `__init__`,
    then read as a frozen field at ~16 splice sites spread across other functions) reads as
    unguarded to this lint even though it is, arguably, guarded MORE strongly than the adjacent-
    call idiom (validated exactly once, un-bypassable thereafter) — a cross-function/parse-
    don't-validate successor is named, not built, for v1.
  - GUARD_RE recognizes the valid_*/..._validate*/validate_*/allowlist* naming idiom only.
    A dict-membership closed-set check (`VIEW_REGISTRY.get(view)`, same file, same function as
    its splice site) and a numeric range guard (`_out_of_range_id(...)`) are functionally
    equivalent closed-alphabet refusals but carry neither name pattern, so both read as
    unguarded here. Broadening GUARD_RE to catch every closed-set idiom by guesswork (rather
    than a second, third witnessed corpus convention) would be exactly the kind of premature
    generalization ADR-0012's own P7/P9 warn against — named as a tuning item, not guessed at.
  - An f-string interpolating a closed, hardcoded ternary (`where = "WHERE ..." if a.increment
    else ""`, filing/file_finding.py) reads as "dynamic" even though every value the
    interpolated expression can ever hold is a compile-time literal — this lint does no
    constant-propagation/value-range reasoning, only syntactic shape.
These are documented, not silently patched around: the corresponding hit sites are triaged by
hand in this commission's report, and each limitation is a stated successor item.

REPORT-ONLY BY DEFAULT (mirrors no_lazy_imports.py's exit-code convention but adds the toggle
this amendment's review-only status requires): exit 0 always unless --gate is given, in which
case a nonzero hit count exits 1. This lint enters pre-commit only by a later maintainer act
(CLAUDE.md: never edit hooks/ or arm a live gate from inside this pass) — running with --gate
today would be a self-appointed escalation this commission was not asked to make.

Usage:
    python3 gates/interpreter_boundary_lint.py [root] [--gate]
"""
from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# v1 scope: Python sources under these five trees only (see module docstring for why shell is
# excluded). Matches git ls-files pathspecs, so vendored submodules (tools/autoharn-panel,
# tools/makespan-scheduler — gitlinks, not directories `git ls-files` descends into from the
# superproject) are excluded for free, same mechanism no_lazy_imports.py relies on.
SCOPE_PATHSPECS = ("tools/*.py", "tools/**/*.py", "serving/*.py", "serving/**/*.py",
                    "gates/*.py", "gates/**/*.py", "hooks/*.py", "hooks/**/*.py",
                    "filing/*.py", "filing/**/*.py")

# Same exclusion class as no_lazy_imports.py: trees never subject to source gates.
EXCLUDE_PARTS = {"claude-ephemera", ".staging", "node_modules", ".venv", "venvs",
                  "__pycache__", ".git"}
EXCLUDE_PATH_PREFIXES = ("tools/makespan-scheduler/", "tools/autoharn-panel/")

# The recognized closed-alphabet-guard idiom, derived from the real corpus (probes.py's
# valid_identifier/valid_hostname, screens.py's per-value validation loop referencing them, and
# the wider validate_*/allowlist naming this repo already uses for structural — not
# character-alphabet — validation, e.g. gates/doc_attestation_presence.py's validate_record,
# gates/ledger_reader_allowlist.py's ALLOWLIST dict/validate_independence). Deliberately
# permissive on the allowlist/validate_* side: a false-guard match (an unrelated validate_
# helper happening to share a function with a real violation) suppresses a hit, which is the
# safe direction for a review-only lint — false negatives here are named in the report, never
# silently eaten, and the corrective-diff clause still binds every fix that touches such a site
# regardless of what this lint flags.
GUARD_RE = re.compile(r"(?i)^valid_|_validate|^validate_|allowlist")

SUBPROC_ATTRS = {"run", "Popen", "call", "check_call", "check_output"}
TEXT_EVAL_SUFFIXES = (".toml", ".sql", ".conf")


# ---------------------------------------------------------------------------------------------
# Dynamic-string-construction detector: is `node` a value built by interpolation/concatenation/
# %-format/.format() rather than a plain literal or an opaque single value?
# ---------------------------------------------------------------------------------------------

def _is_dynamic_string(node: ast.expr | None) -> bool:
    if node is None:
        return False
    if isinstance(node, ast.JoinedStr):
        # An f-string with at least one {expr} substitution -- a bare f"literal text" with no
        # FormattedValue is equivalent to a plain literal and is not flagged.
        return any(isinstance(v, ast.FormattedValue) for v in node.values)
    if isinstance(node, ast.BinOp):
        if isinstance(node.op, ast.Mod):
            return True  # "%s" % value -- classic %-interpolation into text
        if isinstance(node.op, ast.Add):
            # String concatenation, NOT list/tuple concatenation (`FF + list(args)` is a real
            # corpus shape -- gates/findings_gate_fixture.py's `ff()` -- and is the safe argv-
            # list carrier, not text-building; flagging it was this lint's own first false
            # positive during calibration). Require PROOF of string-ness: at least one operand
            # is directly a string literal or f-string. Python disallows `str + list` (a
            # TypeError at runtime), so one confirmed-string side is enough to know the whole
            # expression is string concatenation, not container concatenation.
            return _has_string_evidence(node.left) or _has_string_evidence(node.right)
        return False
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Attribute) and node.func.attr == "format":
            return True  # "...{}...".format(x)
        return False
    return False


def _has_string_evidence(node: ast.expr) -> bool:
    """True only where `node` is DIRECT static proof of string-ness: a string constant, an
    f-string, or a nested `+`/BinOp chain bottoming out in one. A bare Name/Attribute/Call is
    NOT proof either way -- deliberately not assumed textual, to avoid flagging list/tuple
    concatenation built from opaque values (the findings_gate_fixture.py false positive this
    calibration pass found and corrected)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return True
    if isinstance(node, ast.JoinedStr):
        return True
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _has_string_evidence(node.left) or _has_string_evidence(node.right)
    return False


def _literal_suffix(node: ast.expr | None) -> str | None:
    """Best-effort static resolution of the trailing literal text of a path expression, enough
    to recognize a .toml/.sql/.conf suffix. Handles: a plain string constant; an f-string whose
    LAST value is a literal Constant segment; `os.path.join(..., "last.ext")` (the last
    positional arg, if a string constant). Returns None (undetermined) rather than guessing --
    an undetermined suffix is never flagged, the safe direction for a review-only lint (a
    genuine site is at worst under-reported here, never fabricated)."""
    if node is None:
        return None
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr) and node.values:
        last = node.values[-1]
        if isinstance(last, ast.Constant) and isinstance(last.value, str):
            return last.value
    if isinstance(node, ast.Call):
        func = node.func
        is_join = (isinstance(func, ast.Attribute) and func.attr == "join") or \
                  (isinstance(func, ast.Name) and func.id == "join")
        if is_join and node.args:
            return _literal_suffix(node.args[-1])
    return None


def _has_eval_suffix(node: ast.expr | None) -> bool:
    suf = _literal_suffix(node)
    return bool(suf) and suf.endswith(TEXT_EVAL_SUFFIXES)


# ---------------------------------------------------------------------------------------------
# Guard-call detection: does a recognized valid_*/..._validate*/validate_*/allowlist* call
# appear anywhere in the given scope (a function body, or module-level statements outside any
# function)?
# ---------------------------------------------------------------------------------------------

def _call_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


def _scope_has_guard(scope_nodes: list[ast.AST]) -> bool:
    """True if a recognized guard idiom appears anywhere in this scope. Deliberately not
    limited to `guard_fn(x)` call sites: the witnessed screens.py specimen stores the guard as
    a tuple element (`("host", host, probes.valid_hostname)`) and invokes it through a loop
    variable (`_checker(_val)`), so the literal call-site name is `_checker`, not `valid_*` --
    the GUARD_RE-matching name only appears as a plain reference (an Attribute/Name node, not a
    Call.func). Matching any Attribute/Name reference, not only Call.func, covers that
    witnessed-clean shape; the tradeoff (a guard merely imported-and-never-used would also
    count) is the same false-negative-favoring direction as the rest of this lint's guard
    logic -- documented, not silently chosen."""
    for stmt in scope_nodes:
        for sub in ast.walk(stmt):
            name = None
            if isinstance(sub, ast.Attribute):
                name = sub.attr
            elif isinstance(sub, ast.Name):
                name = sub.id
            if name and GUARD_RE.search(name):
                return True
    return False


# ---------------------------------------------------------------------------------------------
# Main tree walk: one pass per function (and one for module-level top-level statements),
# collecting sink hits, then suppressing all hits in a scope if that scope's guard check fires.
# ---------------------------------------------------------------------------------------------

_FUNCS = (ast.FunctionDef, ast.AsyncFunctionDef)


class _Hit:
    __slots__ = ("lineno", "kind", "detail")

    def __init__(self, lineno: int, kind: str, detail: str) -> None:
        self.lineno = lineno
        self.kind = kind
        self.detail = detail


def _is_subproc_call(node: ast.Call) -> tuple[bool, bool]:
    """Returns (is_subprocess_or_system_call, is_os_system)."""
    func = node.func
    if isinstance(func, ast.Attribute):
        if func.attr in SUBPROC_ATTRS:
            return True, False
        if func.attr == "system" and isinstance(func.value, ast.Name) and func.value.id == "os":
            return True, True
    if isinstance(func, ast.Name) and func.id in SUBPROC_ATTRS:
        return True, False
    return False, False


def _kwval(node: ast.Call, name: str) -> ast.expr | None:
    for kw in node.keywords:
        if kw.arg == name:
            return kw.value
    return None


def _first_arg(node: ast.Call, kwname: str) -> ast.expr | None:
    if node.args:
        return node.args[0]
    return _kwval(node, kwname)


def _resolve_name(name: str, assigns: dict[str, ast.expr]) -> ast.expr | None:
    return assigns.get(name)


def _scan_scope(stmts: list[ast.AST], qualname: str) -> list[_Hit]:
    hits: list[_Hit] = []
    # last-assignment tracking within this scope (non-flow-sensitive, last-wins -- same
    # simplifying choice no_lazy_imports.py makes by walking the whole subtree unconditionally).
    assigns: dict[str, ast.expr] = {}
    open_vars: dict[str, ast.expr] = {}  # file-handle var -> path expr, for write() sinks

    def note_assign(target: ast.expr, value: ast.expr) -> None:
        if isinstance(target, ast.Name):
            assigns[target.id] = value

    for stmt in stmts:
        for node in ast.walk(stmt):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    note_assign(t, node.value)
                # SQL-text sink: a sql/query-named variable assigned a dynamically-built string.
                for t in node.targets:
                    if isinstance(t, ast.Name) and re.search(r"(?i)sql|query", t.id) \
                            and _is_dynamic_string(node.value):
                        hits.append(_Hit(node.lineno, "sql-text-assign",
                                          f"{t.id} = <dynamic string>"))
            elif isinstance(node, ast.AugAssign):
                if isinstance(node.target, ast.Name):
                    prior = assigns.get(node.target.id)
                    combined = ast.BinOp(left=prior or ast.Constant(value=""),
                                          op=ast.Add(), right=node.value)
                    if re.search(r"(?i)sql|query", node.target.id) and \
                            (_is_dynamic_string(node.value) or
                             (prior is not None and _is_dynamic_string(combined))):
                        hits.append(_Hit(node.lineno, "sql-text-assign",
                                          f"{node.target.id} += <dynamic string>"))
                    assigns[node.target.id] = combined
            elif isinstance(node, ast.withitem) and isinstance(node.context_expr, ast.Call):
                call = node.context_expr
                if isinstance(call.func, ast.Name) and call.func.id == "open" and \
                        isinstance(node.optional_vars, ast.Name):
                    path_arg = call.args[0] if call.args else _kwval(call, "file")
                    open_vars[node.optional_vars.id] = path_arg
            elif isinstance(node, ast.Call):
                is_sp, is_system = _is_subproc_call(node)
                if is_sp:
                    shell_true = False
                    st = _kwval(node, "shell")
                    if isinstance(st, ast.Constant) and st.value is True:
                        shell_true = True
                    cmd = _first_arg(node, "args") if not is_system else \
                        (node.args[0] if node.args else None)
                    if cmd is not None and isinstance(cmd, ast.Name):
                        cmd = _resolve_name(cmd.id, assigns) or cmd
                    is_list_carrier = isinstance(cmd, (ast.List, ast.Tuple))
                    if not is_list_carrier:
                        dynamic = _is_dynamic_string(cmd) if cmd is not None else False
                        if is_system and dynamic:
                            hits.append(_Hit(node.lineno, "shell-sink",
                                              "os.system(<dynamic string>)"))
                        elif shell_true and (dynamic or cmd is None or
                                              not isinstance(cmd, ast.Constant)):
                            hits.append(_Hit(node.lineno, "shell-sink",
                                              "subprocess ...(shell=True, <non-literal command>)"))
                        elif dynamic and not shell_true and not is_system:
                            # a single interpolated string handed as `args` with no argv list
                            # and no shell=True -- still the "assembled as a single string"
                            # antipattern this amendment names, even though it will usually just
                            # fail to exec rather than inject; flagged as the same class.
                            hits.append(_Hit(node.lineno, "subproc-single-string",
                                              "subprocess ...(<dynamic single-string command>)"))
                # SQL-transport-call sink: `.execute(...)`, OR a call to a function/method whose
                # OWN name marks it as a SQL/psql transport (`_psql(...)`, `psql(...)`, a
                # `*_query`/`query_*` helper -- filing/record_reading.py's `_psql(f'INSERT INTO
                # "{core_schema}"...' , ...)` is the witnessed real-corpus shape this generalizes
                # from: the dynamic SQL text is built INLINE as a call argument, never assigned
                # to a `sql`/`query`-named variable first, so the assignment-based check above
                # alone missed it during calibration). Any positional argument that is a
                # dynamically-built string trips this, not only the first -- SQL text is not
                # always arg0 (e.g. a `(host, db, sql)`-shaped transport helper).
                fname = _call_name(node.func) or ""
                if fname == "execute" or re.search(r"(?i)(^|_)(sql|psql|query)(_|$)", fname):
                    for arg in node.args:
                        a = arg
                        if isinstance(a, ast.Name):
                            a = _resolve_name(a.id, assigns) or a
                        if _is_dynamic_string(a):
                            hits.append(_Hit(node.lineno, "sql-text-call",
                                              f"{fname}(..., <dynamic string>, ...)"))
                            break
                # Evaluator-bound file-write sink: <handle>.write(...) / Path(...).write_text(...)
                if isinstance(node.func, ast.Attribute) and node.func.attr in ("write", "write_text"):
                    content = node.args[0] if node.args else None
                    if isinstance(content, ast.Name):
                        content = _resolve_name(content.id, assigns) or content
                    if _is_dynamic_string(content):
                        path_expr = None
                        recv = node.func.value
                        if isinstance(recv, ast.Name) and recv.id in open_vars:
                            path_expr = open_vars[recv.id]
                        elif isinstance(recv, ast.Call) and isinstance(recv.func, ast.Name) \
                                and recv.func.id == "Path":
                            path_expr = recv.args[0] if recv.args else None
                        if path_expr is not None and isinstance(path_expr, ast.Name):
                            path_expr = _resolve_name(path_expr.id, assigns) or path_expr
                        if _has_eval_suffix(path_expr):
                            hits.append(_Hit(node.lineno, "config-text-write",
                                              f"{node.func.attr}(<dynamic string>) -> "
                                              f"*{_literal_suffix(path_expr)}"))
    return hits


def violations_in(path: Path, base: Path = REPO) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as e:
        return [f"{path}:0: UNPARSEABLE ({e.__class__.__name__}) — lint cannot certify this file"]

    try:
        display = path.relative_to(base)
    except ValueError:
        display = path

    out: list[str] = []

    def walk_scopes(node: ast.AST, qualname: str) -> None:
        body_stmts: list[ast.AST] = []
        for child in ast.iter_child_nodes(node):
            if isinstance(child, _FUNCS):
                # recurse into the nested function as its own scope first
                walk_scopes(child, f"{qualname}.{child.name}" if qualname else child.name)
            else:
                body_stmts.append(child)
        # scan THIS scope's own direct+nested-non-function statements (module level or one
        # function body), excluding nested function bodies (handled by their own recursive call
        # above -- ast.walk inside _scan_scope still descends into a nested function's non-def
        # children if we pass full subtrees, so instead pass only the non-FunctionDef children,
        # each walked individually; nested defs are excluded by walk_scopes' own split above,
        # but ast.walk(stmt) on a non-def statement can still reach an inner lambda/comprehension
        # -- acceptable, those share the enclosing scope's guard visibility in practice).
        label = qualname or "<module>"
        hits = _scan_scope(body_stmts, label)
        if hits:
            if not _scope_has_guard(body_stmts):
                for h in hits:
                    out.append(f"{display}:{h.lineno}: {h.kind} — {h.detail}  (inside {label})")

    walk_scopes(tree, "")
    return out


def tracked_py_files(root: Path) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for spec in SCOPE_PATHSPECS:
        r = subprocess.run(["git", "-C", str(root), "ls-files", spec],
                            capture_output=True, text=True, check=True)
        for line in r.stdout.splitlines():
            p = root / line
            if p in seen:
                continue
            if any(part in EXCLUDE_PARTS for part in p.parts):
                continue
            if any(line.startswith(prefix) for prefix in EXCLUDE_PATH_PREFIXES):
                continue
            seen.add(p)
            files.append(p)
    return sorted(files)


def main() -> int:
    argv = sys.argv[1:]
    gate = "--gate" in argv
    positional = [a for a in argv if a != "--gate"]
    root = Path(positional[0]).resolve() if positional else REPO

    bad: list[str] = []
    for f in tracked_py_files(root):
        bad.extend(violations_in(f, base=root))

    if bad:
        mode = "GATE MODE" if gate else "REPORT-ONLY"
        print(f"INTERPRETER-BOUNDARY LINT HITS ({len(bad)}) — {mode}, law/adr/0012's "
              f"2026-07-18 amendment (ledger row 1701 trigger):")
        print("\n".join(bad))
        if gate:
            return 1
        print("\n(report-only: exiting 0. Pass --gate to enforce nonzero exit on a hit. This "
              "lint is not wired into pre-commit -- that is a later maintainer act.)")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
