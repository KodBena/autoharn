#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-19T20:10:34Z
#   last-change: 2026-07-22T02:00:42Z
#   contributors: ab5d5bab/main, 1fa3ab69/main
# <<< PROVENANCE-STAMP <<<

"""gates/setup_tui_purity_gate.py -- the §2.8 AST purity gate (design/FABLE-SETUP-TUI-PURE-CORE-
SPEC.md §2.8, commission ledger rows 1823 point 2 / 1825 / 1835): "a census-registered gate
asserts, at the AST level over tools/setup_tui/, that calls to the three runner choke points
(run_command, start_background, write_file) appear ONLY in the commit-executor module and the
rehearsal module's declared exception -- a screen that acquires a direct effect call fails the
gate."

CLASS FIX (fresh-context review of b565db1): the gate's field of view used to match ONLY the
three named choke points -- narrower than the claim made for it, since a decision-phase module
could still perform a real effect by reaching UNDER those choke points (a bare `open(path, "w")`,
`os.mkdir`, `tempfile.mkdtemp`, a direct `subprocess.run`) without ever calling
`run_command`/`write_file`/`start_background` by name, invisible to the original detector. Two
independent real instances of exactly this were found live (FINDING 2: a scratch-GNUPGHOME
`mkdtemp` + batch-file write at decision time; FINDING 3: `checklist.py`'s own bare
`open(path, "w")`, both since fixed). `check_tree`/`check_extra_effects` below are two SEPARATE
detectors over the SAME AST walk, because they answer two different questions with two different
honest exemption sets (see each detector's own docstring).

WHAT COUNTS AS THE DECLARED EXCEPTION SITE, detector 1 (the three choke points, unchanged):
`tools/setup_tui/commit_executor.py` may call all three choke points anywhere (it IS the one
commit boundary). `tools/setup_tui/screens.py`'s `screen_rehearsal` function -- and ONLY that
function -- may call them too (the P9-rule-4-shaped Workspace exception, spec §2.5/§3). Every
OTHER function in EVERY OTHER module under `tools/setup_tui/` is checked and must be clean.
`checklist.py`'s `save` method is a THIRD, narrower, explicitly-documented exception (FINDING 3's
own fix): it calls `write_file` directly because it is structurally POST-commit machinery (the
checklist's own final content, including every entry's real commit-time status, is not known
until the commit boundary has already finished -- it cannot itself be a plan entry executed
DURING the commit) -- see `checklist.Checklist.save`'s own docstring.

DETECTION 1 (AST, not text-grep -- a grep would false-positive on the docstrings/comments this
very module and screens.py itself carry, which mention "run_command" and "write_file" by name in
prose): walks every `ast.Call` node, matching either a bare-name call (`run_command(...)`) or an
attribute call (`runner.run_command(...)`) whose function name is one of the three. Each match is
attributed to its ENCLOSING function via a one-pass parent map -- a call at module level is always
a violation, never exempt.

DETECTION 2 (CLASS FIX): the SAME walk, matching a wider, still-precise set of direct-effect
shapes: `open(...)` calls whose mode argument (positional 2nd arg, or `mode=` keyword) contains
any of `w`/`a`/`x`/`+` (a WRITING mode -- the default, no mode arg at all, is `"r"`, read-only,
never flagged); `os.<name>(...)` where `<name>` is one of a closed mutation-verb set (`mkdir`,
`makedirs`, `chmod`, `replace`, `remove`, `rmdir`, `unlink`); `shutil.rmtree`/`shutil.copytree`/
`shutil.move`; any `tempfile.<name>(...)` call (the whole module is scratch-file creation by
definition); any `subprocess.<name>(...)` call (module-qualified only -- see LIMITATIONS). Each
match is attributed to its enclosing function exactly as detection 1 does, checked against
`EXTRA_EFFECT_EXEMPT` (a SEPARATE table from `EXEMPT`, since the legitimate exemption set differs:
`runner.py`/`commit_executor.py` are exempt wholesale, being the mechanism layer itself;
`probes.py`/`pghba.py` are exempt wholesale as the spec's own declared "read-only probes stay
live" sites (every `subprocess.run` call in them is a read -- `pg_isready`, a `SELECT 1` probe, a
`SELECT pg_read_file(...)`, `git rev-parse`/`submodule status` -- never a write); a small, named
set of individual read-only helper functions in `signed_genesis.py`/`principals_authority.py`
(their own `_psql_json_rows`/`_psql_rows` SELECT helpers); and `signed_genesis.py`'s three
FINDING-2-created scratch-GNUPGHOME functions, which perform a real effect but ONLY via
`plan.CallableAct`'s closure, i.e. only ever at commit time (see EXTRA_EFFECT_EXEMPT's own
per-entry comments for the individual justification).

DETECTION 3 (design/FABLE-SETUP-TUI-TYPED-UI-SPEC.md §1's closure statement): "no module in
tools/setup_tui except ui.py/ui_textual.py may call print( or .say(" -- the typed-UI content
vocabulary's own enforcement surface (`elements.py`'s six closed element types, `Ui.emit`). Walks
the SAME AST for a bare `print(...)` call, OR an attribute call whose method name is `say`
(the old, now-removed `Ui.say`/`ScriptedUi`/`InteractiveUi` shape -- kept as a detected shape so a
reintroduced compatibility shim would still be caught, not only a literal `print`). Checked
against `PRINT_EXEMPT`, a THIRD exemption table (module docstring's own "two different honest
exemption sets" pattern, extended to three): `ui.py` and `ui_textual.py` are exempt wholesale
(they ARE the rendering seam `render_text`/`emit` are defined in -- the spec's own two named
exceptions); `runner.py` is exempt wholesale (the spec's own closure statement: "excluding ...
runner.py subprocess passthrough of child output" -- the `$ argv`/dry-run-notice prints there are
the choke points' own child-process-output passthrough, never operator content routed through
`Ui`); `app.py` gets a NARROW, function-named exemption for diagnostics that fire OUTSIDE the
normal `Ui`-mediated screen flow -- before any `Ui` exists (`_select_backend`'s "textual not
installed" notice, printed before backend selection has even happened), or from a signal handler
/exception path where crossing back into a `Ui` call (especially `TextualUi`'s worker-thread
bridge) would be unsafe or could itself hang (`_drive_screens`'s `ScriptExhausted`/
`KeyboardInterrupt` stderr lines, both `_handle_sigterm` closures, `_run_textual`'s uncaught-error
report, `_terminate_boundary_proc`'s cleanup notice) -- these are the logic's own error/log
diagnostics (ADR-0002 rung 3/4), P10's own discriminator for what legitimately stays a literal.

LIMITATIONS, STATED HONESTLY (per the review's own instruction -- "keep the gate honest about
what it still cannot see"):
  - DETECTION 3 shares detection 1/2's method-call blind spot: `self.say(...)`/`obj.say(...)` IS
    caught (any attribute call named `say`), but a `print` reached through a rebound name
    (`p = print; p(...)`) is not -- an honest false-negative, matching this gate's existing
    posture elsewhere.
  - This is a SYNTACTIC check. It cannot verify that an exempted function is ACTUALLY only ever
    invoked from the context its exemption claims (e.g. that `_prepare_scratch_gnupghome_raw` is
    truly reachable only from a commit-time `CallableAct` closure, or that a `subprocess.run` call
    in an exempted read-only-probe function truly never mutates anything) -- each exemption is a
    REVIEWED CLAIM about the call site's actual usage, not a property this gate proves. Widening
    an exempted function's own body, or calling it from a new site, does not re-trigger review.
  - Method calls on an already-constructed object (`proc.terminate()`, `proc.wait()`,
    `f.write(...)` on an already-open file handle) are NOT detected -- only calls where the
    callee is syntactically `open`, `os.<verb>`, `shutil.<verb>`, `tempfile.<verb>`, or
    `subprocess.<verb>`. A write reached through an intermediate variable or a re-imported alias
    (`from os import mkdir as _m; _m(...)`, `sub = subprocess; sub.run(...)`) is invisible to this
    detector.
  - `open()` calls whose mode is a variable, not a literal string, cannot be classified and are
    conservatively treated as NON-writing (an honest false-negative, not a false-positive) --
    every actual call site in this package uses a literal mode string today.

Exit 0 clean; exit 1 listing every violation (either detector) as `path:line: <call text>
(inside <function or module-level>)`. The negative self-check (a synthetic violation of EACH
detector must fail red) lives in seen-red/setup-tui-purity-gate/run_fixtures.py, which imports and
calls this module's own `scan_file`/`check_tree`/`check_extra_effects` directly against synthetic
source text -- never touching the real tree.

Usage: python3 gates/setup_tui_purity_gate.py
Lazy imports banned."""
from __future__ import annotations

import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE_DIR = os.path.join(ROOT, "tools", "setup_tui")

FORBIDDEN_NAMES = {"run_command", "start_background", "write_file"}

# (relative filename under tools/setup_tui/) -> set of function qualnames permitted to call a
# choke point directly, OR the sentinel "*" meaning "the whole module is exempt". A module/
# function NOT listed here gets NO exemption at all.
EXEMPT: dict[str, set[str]] = {
    "commit_executor.py": {"*"},
    "screens.py": {"screen_rehearsal"},
    "checklist.py": {"save"},  # FINDING 3: write_file called here, the checklist-save's own
                                # declared, narrower, post-commit exception (see module docstring
                                # above and Checklist.save's own docstring for the full reasoning).
    "config_seam.py": {"save_world_config"},  # design/FABLE-SETUP-TUI-CONFIG-FILE-SPEC.md §4's
                                # self-save -- the SAME declared, post-commit exception shape as
                                # checklist.py's save (see config_seam.save_world_config's own
                                # docstring): the resolved decision set is not complete until the
                                # commit itself has run (or been rendered, under --dry-run).
}

# DETECTION 2's own exemption table (CLASS FIX) -- deliberately SEPARATE from EXEMPT: the
# legitimate exemption set for "a direct file-write/os-mutation/tempfile/subprocess call" is not
# the same set as "a runner choke-point call" (read-only probe modules belong here but NOT in
# EXEMPT, since they never call a choke point at all).
EXTRA_EFFECT_EXEMPT: dict[str, set[str]] = {
    "runner.py": {"*"},          # the choke points' OWN implementation -- this IS the mechanism
                                  # layer every direct-effect call in this package is supposed to
                                  # route through; it necessarily contains the real subprocess/
                                  # tempfile/os calls.
    "commit_executor.py": {"*"}, # the one commit boundary -- CommitJournal._persist's own
                                  # atomic-write (tempfile.NamedTemporaryFile/os.fsync/os.chmod/
                                  # os.replace) and CommitJournal.remove's os.remove.
    "screens.py": {"screen_rehearsal"},  # the same declared Workspace exception as detection 1.
    "probes.py": {"*"},          # the read-only-probes module BY DESIGN (module's own docstring:
                                  # "Every probe here re-checks reality; none of them trust an
                                  # operator's say-so") -- every subprocess.run call here is a
                                  # read (pg_isready, a SELECT 1 probe, git rev-parse/submodule
                                  # status), the spec's own declared "read-only probes stay live"
                                  # exception, never a write.
    "pghba.py": {"*"},           # reads the live pg_hba.conf via `SELECT pg_read_file(...)` --
                                  # read-only; module's own docstring: "This module NEVER applies
                                  # anything ... It only reads ... and prints."
    "signed_genesis.py": {
        "_psql_json_rows",                # read-only SELECT helper (list_commissions/
                                           # fetch_commission_statement) -- the spec's declared
                                           # read-only-probe exception, same as probes.py.
        "_prepare_scratch_gnupghome_raw", # FINDING 2: a real effect (mkdtemp+chmod), but called
        "_write_scratch_batch_file_raw",  # ONLY from prepare_scratch_gnupghome_act's own
                                           # CallableAct.fn closure -- i.e. only ever at commit
                                           # time, never at decision time. See LIMITATIONS: this
                                           # gate cannot itself verify that claim; it is reviewed.
        "teardown_scratch",               # zero-residue cleanup (shutil.rmtree) -- called from
                                           # screen_checklist's own _teardown_scratch_gnupghomes,
                                           # structurally POST-commit (after _execute_commit has
                                           # already run, same reasoning as checklist.py's save).
    },
    "principals_authority.py": {"_psql_rows"},  # read-only SELECT helper (list_principals/
                                                  # s41_status) -- same reasoning as probes.py.
    "config_seam.py": {"scripted_answers_file"},  # design/FABLE-SETUP-TUI-CONFIG-FILE-SPEC.md
                                                  # §2's --from-config: a real tempfile write,
                                                  # but ORCHESTRATION-level (runs before any
                                                  # screen/Ui/Plan exists) -- see the function's
                                                  # own docstring for the full reasoning.
}

# DETECTION 3's own exemption table (design/FABLE-SETUP-TUI-TYPED-UI-SPEC.md §1) -- a THIRD,
# separate table (module docstring's DETECTION 3 section explains why each entry is here).
PRINT_EXEMPT: dict[str, set[str]] = {
    "ui.py": {"*"},          # the rendering seam ITSELF -- `Ui.emit` calls `print` on
                              # `elements.render_text`'s lines; `InteractiveUi`/`ScriptedUi`'s
                              # own prompt/answer echoes are the spec's two named exceptions.
    "ui_textual.py": {"*"},  # `TextualUi.emit`'s print (captured into the transcript,
                              # module docstring architecture point 2) and its one styled-write
                              # bypass (`write_transcript_styled`) -- the spec's other named
                              # exception.
    "runner.py": {"*"},      # the spec's own closure statement: "excluding ... runner.py
                              # subprocess passthrough of child output" -- the `$ argv`/
                              # dry-run-notice prints are the choke points' own mechanism, never
                              # operator content routed through `Ui`.
    "app.py": {
        "_select_backend",         # fires BEFORE any `Ui` exists (backend selection itself).
        "_drive_screens",          # `ScriptExhausted`/`KeyboardInterrupt` stderr diagnostics --
                                    # an abnormal-exit report, not operator content.
        "_handle_sigterm",         # both `_run_plain`/`_run_textual`'s nested SIGTERM handlers
                                    # share this name (`_ParentFinder` attributes each to itself);
                                    # a signal handler must not risk a `Ui`/worker-thread bridge
                                    # call (module docstring: "freezes the App's own asyncio
                                    # loop" -- ui_textual.py's own SIGTERM-ordering comment).
        "_run_textual",            # the uncaught-Textual-error report (a crash diagnostic,
                                    # printed AFTER the App has already exited).
        "_terminate_boundary_proc", # abnormal-exit cleanup notice -- may run from the SIGTERM
                                    # path above, same constraint.
        "_run_from_config",        # design/FABLE-SETUP-TUI-CONFIG-FILE-SPEC.md §2/§3's own
                                    # refuse-before-any-act diagnostics -- fire BEFORE any `Ui`
                                    # is selected, same shape as `_select_backend` above.
        "main",                    # the --initial-config load-refusal print -- same "before any
                                    # Ui exists" reasoning, one call site.
    },
    "feature_facts.py": {"<module level>"},  # the `if __name__ == "__main__":` standalone
                                              # drift-check entry point (`python3 -m tools.
                                              # setup_tui.feature_facts`) -- a CLI self-check in
                                              # the shape of a gate, never reached by the wizard's
                                              # own Ui-mediated screen flow; the SAME class of
                                              # diagnostic gates/ itself prints outside this
                                              # package's own scope.
}

_OS_MUTATION_VERBS = {"mkdir", "makedirs", "chmod", "replace", "remove", "rmdir", "unlink"}
_SHUTIL_MUTATION_VERBS = {"rmtree", "copytree", "move"}


class _ParentFinder(ast.NodeVisitor):
    """Builds `node -> nearest enclosing FunctionDef/AsyncFunctionDef (or None for module-level)`
    for every node in a tree, in one pass -- the mechanism both detectors use to attribute a call
    to the function it lexically sits inside, regardless of nesting depth (a call inside a nested
    closure, a comprehension, a `with`/`try` block, etc. -- all of those still resolve to their
    nearest enclosing `def`, not a synthetic new scope this gate would have to special-case)."""

    def __init__(self) -> None:
        self.owner: dict[ast.AST, "ast.FunctionDef | ast.AsyncFunctionDef | None"] = {}

    def visit(self, node: ast.AST, current: "ast.FunctionDef | ast.AsyncFunctionDef | None" = None) -> None:
        self.owner[node] = current
        next_current = current
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            next_current = node
        for child in ast.iter_child_nodes(node):
            self.visit(child, next_current)


def _call_name(node: ast.Call) -> str | None:
    """The forbidden-set-comparable name of a call's function, or None if it does not match the
    shape of either call style detection 1 checks (bare name, or `<anything>.name`)."""
    fn = node.func
    if isinstance(fn, ast.Name):
        return fn.id
    if isinstance(fn, ast.Attribute):
        return fn.attr
    return None


def _render(node: ast.Call) -> str:
    try:
        return ast.unparse(node)
    except Exception:  # noqa: BLE001 -- unparse is best-effort for the message only
        return _call_name(node) or "<call>"


def _mode_arg(node: ast.Call) -> str | None:
    """The literal string value of `open()`'s `mode` argument (positional 2nd arg, or `mode=`
    keyword) -- `None` if there is none (the default, read-only, mode) OR if it is not a literal
    string (a variable -- see module docstring's own LIMITATIONS note: conservatively treated as
    non-writing, an honest false-negative)."""
    if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str):
        return node.args[1].value
    for kw in node.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            return kw.value.value
    return None


def _is_extra_effect_call(node: ast.Call) -> bool:
    """DETECTION 2's own match predicate -- see module docstring for the exact shapes."""
    fn = node.func
    if isinstance(fn, ast.Name) and fn.id == "open":
        mode = _mode_arg(node)
        return bool(mode) and any(c in mode for c in "wax+")
    if isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name):
        base = fn.value.id
        if base == "os" and fn.attr in _OS_MUTATION_VERBS:
            return True
        if base == "shutil" and fn.attr in _SHUTIL_MUTATION_VERBS:
            return True
        if base == "tempfile":
            return True
        if base == "subprocess":
            return True
    return False


def check_tree(tree: ast.AST, filename: str) -> list[str]:
    """DETECTION 1: returns violation strings for `tree`, applying `EXEMPT`'s per-file/per-
    function allowance. `filename` is the base name used to look up `EXEMPT` -- callers pass
    whatever key they want checked against, so a fixture can probe a SYNTHETIC tree under a
    chosen filename without touching the real files."""
    exempt_functions = EXEMPT.get(filename, set())
    if "*" in exempt_functions:
        return []

    finder = _ParentFinder()
    finder.visit(tree)

    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        if name not in FORBIDDEN_NAMES:
            continue
        owner = finder.owner.get(node)
        qualname = owner.name if owner is not None else "<module level>"
        if qualname in exempt_functions:
            continue
        line = getattr(node, "lineno", "?")
        violations.append(f"{filename}:{line}: {_render(node)}  (inside {qualname})")
    return violations


def check_extra_effects(tree: ast.AST, filename: str) -> list[str]:
    """DETECTION 2 (CLASS FIX): returns violation strings for `tree`, applying
    `EXTRA_EFFECT_EXEMPT`'s per-file/per-function allowance -- a direct file-write/os-mutation/
    tempfile/subprocess call outside a reviewed exemption. Same per-file/per-function/`"*"`
    lookup shape as `check_tree`, over a DIFFERENT match predicate (`_is_extra_effect_call`) and a
    DIFFERENT exemption table (see module docstring for why the two tables differ)."""
    exempt_functions = EXTRA_EFFECT_EXEMPT.get(filename, set())
    if "*" in exempt_functions:
        return []

    finder = _ParentFinder()
    finder.visit(tree)

    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _is_extra_effect_call(node):
            continue
        owner = finder.owner.get(node)
        qualname = owner.name if owner is not None else "<module level>"
        if qualname in exempt_functions:
            continue
        line = getattr(node, "lineno", "?")
        violations.append(f"{filename}:{line}: {_render(node)}  (inside {qualname})")
    return violations


def _is_print_or_say_call(node: ast.Call) -> bool:
    """DETECTION 3's own match predicate (module docstring): a bare `print(...)` call, or an
    attribute call whose method name is `say` (the old, removed `Ui.say` shape -- see module
    docstring for why this shape stays detected even though nothing currently defines it)."""
    fn = node.func
    if isinstance(fn, ast.Name) and fn.id == "print":
        return True
    if isinstance(fn, ast.Attribute) and fn.attr == "say":
        return True
    return False


def check_print_say(tree: ast.AST, filename: str) -> list[str]:
    """DETECTION 3 (design/FABLE-SETUP-TUI-TYPED-UI-SPEC.md §1's closure statement): returns
    violation strings for `tree`, applying `PRINT_EXEMPT`'s per-file/per-function allowance. Same
    per-file/per-function/`"*"` lookup shape as the other two detectors, over `_is_print_or_say_
    call` and its own exemption table."""
    exempt_functions = PRINT_EXEMPT.get(filename, set())
    if "*" in exempt_functions:
        return []

    finder = _ParentFinder()
    finder.visit(tree)

    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _is_print_or_say_call(node):
            continue
        owner = finder.owner.get(node)
        qualname = owner.name if owner is not None else "<module level>"
        if qualname in exempt_functions:
            continue
        line = getattr(node, "lineno", "?")
        violations.append(f"{filename}:{line}: {_render(node)}  (inside {qualname})")
    return violations


def scan_file(path: str) -> list[str]:
    """Reads and AST-parses the REAL file at `path`, running ALL THREE detectors, checked against
    their own tables keyed by its base filename. A syntax error in the file is itself reported as
    a violation line (never silently skipped -- an unparseable module cannot be honestly
    certified clean)."""
    filename = os.path.basename(path)
    with open(path, encoding="utf-8") as f:
        source = f.read()
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as exc:
        return [f"{filename}: SyntaxError, cannot check purity: {exc}"]
    return (check_tree(tree, filename) + check_extra_effects(tree, filename)
            + check_print_say(tree, filename))


def scan_package(package_dir: str = PACKAGE_DIR) -> list[str]:
    """Walks `package_dir` RECURSIVELY (design/FABLE-SETUP-TUI-TYPED-UI-SPEC.md §1's closure
    statement covers every module under `tools/setup_tui/`, not only its top level -- the new
    `content/` sub-package included) -- `__pycache__` is the one directory skipped, same as every
    other tree-walking gate in this project. Each file is still checked against the exemption
    tables by its BASE filename (unchanged), which stays unambiguous: every filename under this
    package, top-level or in `content/`, is unique today."""
    violations: list[str] = []
    for dirpath, dirnames, filenames in os.walk(package_dir):
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        for name in sorted(filenames):
            if not name.endswith(".py"):
                continue
            violations.extend(scan_file(os.path.join(dirpath, name)))
    return violations


def main() -> int:
    violations = scan_package()
    if violations:
        print(f"setup_tui_purity_gate: {len(violations)} violation(s) -- a runner choke point "
              f"(run_command/start_background/write_file), a direct file-write/os-mutation/"
              f"tempfile/subprocess call, or a bare print(/.say( call was found outside its "
              f"declared exception site:")
        for v in violations:
            print(f"  {v}")
        return 1
    print("setup_tui_purity_gate: clean ✓ -- every runner choke-point call, every direct "
          "file-write/os-mutation/tempfile/subprocess call, and every print(/.say( call, under "
          "tools/setup_tui/ is confined to a declared exception site (design/FABLE-SETUP-TUI-"
          "PURE-CORE-SPEC.md §2.8, design/FABLE-SETUP-TUI-TYPED-UI-SPEC.md §1)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
