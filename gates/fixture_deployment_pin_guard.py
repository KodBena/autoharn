#!/usr/bin/env python3
"""fixture_deployment_pin_guard.py -- mechanical sweep for ledger work item
fixture-scratch-pinning-guard (row 1249, generalizing beyond `serve_existing_world`'s own
tempdir/repo-disjoint refusal in seen-red/boundary-service/run_fixtures.py).

THE LEAK (rows 1237-1244/1248): a seen-red fixture resolved a REAL deployment.json and stood a
served `led` against the LIVE kernel, writing garbage rows. Three doors, all guarded here:
  (a) invoking this CHECKOUT's own operator verb directly (`REPO / "led"`, its umbrella-CLI
      successor `REPO / "libexec" / "autoharn" / "led"`, the `autoharn` dispatcher, or (fix-round
      4) a BARE literal naming one of those verbs with no path join at all) instead of a
      scaffolded scratch copy -- each resolves deployment.json from `dirname($0)`/`cwd`, ignoring
      any inherited PICKUP_DEPLOYMENT override. A direct `bootstrap/templates/*.tmpl` invocation
      is DIFFERENT and SAFE (env-driven via `os.environ.get("PICKUP_DEPLOYMENT", ...)`) -- not
      flagged.
  (b) mutating `os.environ["PICKUP_DEPLOYMENT"]` globally (direct, aliased, or via
      `.update()`/`.setdefault()`) instead of a per-call `env` dict via one subprocess call's
      `env=` kwarg -- a global mutation leaks into every later subprocess this process spawns.
  (c) spawning via a shell string (`os.system(...)`, `shell=True`) instead of an argv list --
      sidesteps (a)/(b) entirely: a shell string's repo-path spelling is unenumerable.

Grep/AST CENSUS gate (gates/no_lazy_imports.py's own family), not a dataflow prover. Binding/
argv-provability helpers live in `gates/_pin_guard_argv.py`, the CENSUS sweep that widens what
those helpers ever see a facts entry for lives in `gates/_pin_guard_census.py`, pure verb-path
grammar recognition lives in `gates/_pin_guard_resolve.py`, and the per-file walk plus every
verdict/waiver string live in `gates/_pin_guard_checks.py` (four-way split, fix-round 4, to keep
every file well under ADR-0007's 400-line ceiling once this round's findings -- and this
docstring's own MEASUREMENT section -- added real content, not just code); this file is just the
entry point: resolve the verb rosters, iterate target files, print.

POSTURE, ROUND 3 (kept for context; unchanged by round 4 except where noted) -- A SHAPE CHANGE
(fresh-context strengthened-tier review BLOCKED 8821dff, round 2's `simulate_list_states` replay
engine): static analysis of arbitrary Python dataflow always loses one rung up to the next live
evasion, so round 3 stopped shipping replay refinements and instead PROVES safety only for argv
shapes it can fully see, refusing everything else that is ever "sensitive" (an element resolves to
a repo-verb path) as UNPROVEN, with a waiver escape hatch:
  1. A direct inline literal (List/Tuple) argv AT THE CALL SITE -- provable.
  2. A Name-bound argv whose binding is a literal AND which has ZERO other qualifying events
     anywhere in the file -- provable, use the binding literal.
  3. EVERYTHING ELSE that is ever sensitive -- UNPROVEN, refused outright, waivable at the call
     site.

POSTURE, ROUND 4 (this round) -- CENSUS FAIL-CLOSED, not another enumeration widening. A
fresh-context strengthened-tier review of round 3 demonstrated, for the FOURTH time running
across this arc, the same underlying lesson: wherever this gate's analysis ENUMERATES grammar
shapes, the unenumerated remainder passes silently. Seven findings, each closed below:
  1. Chained assign (`x = y = [...]`) -- `analyze_names`' own Assign case required
     `len(node.targets) == 1`, so a chained assign's targets were skipped entirely: no facts
     entry for EITHER name, sensitivity un-checkable, PASSED CLEAN.
  2. Tuple/list-unpacking targets (`a, b = ...`, a `for` target, a tuple-swap `a, b = b, a`) --
     same root cause, a different unhandled target shape: only a bare `Name` or a
     `Subscript(Name)` target was ever modeled.
  3. Walrus (`:=`, `ast.NamedExpr`) -- not swept by any prior round at all.
  4. BARE VERB LITERALS (`["led", "status"]`, `["./led", ...]`) as argv[0], never joined to a
     `REPO`-like path at all -- every prior round only ever looked for a repo-ROOTED PATH; a bare
     name relying on `cwd`/`PATH` resolution was invisible by construction, arguably the leak
     class's MOST literal spelling.
  5. Dynamic mutation that never spells `Name.method(...)`: `getattr(cmd, "append")(x)` fired
     some OTHER generic event against `cmd` (the bare-Name-argument sweep) but never recorded the
     appended element, silently dropping it before the provable/unproven branch ever saw it;
     `globals()["cmd"].append(x)` recorded no event on any tracked Name at all (no `Name` node
     spells `cmd` at the mutation site).
  6. Inline-literal element misses: an f-string with a `str(REPO)` call nested inside a
     `FormattedValue` (only a bare `{REPO}` was recognized); an `IfExp`/`+`-concat on a join's
     RIGHT side (`REPO / (a if flag else "led")`) instead of a plain constant; a `Starred`
     element unpacking a literal list that itself carries the verb
     (`[*[str(REPO / "led")], "status"]`).
  7. None of 1-6 disclosed anywhere -- the module docstrings claimed a scope narrower than the
     code actually covered.

THE RULE THIS ROUND (rule A, findings 1-3 and half of 5): "no enumeration survives unless its
complement is handled fail-closed" -- CENSUS FAIL-CLOSED. `gates/_pin_guard_census.py` sweeps
every binding-like construct `analyze_names` does not itself model precisely (chained assign,
tuple/list-unpack including a swap, a `for` target, walrus, `with ... as`, `except ... as`, an
annotated assign, a comprehension target) and CONTAMINATES every Name it binds: an event is always
recorded (so the name can never again be silently PROVABLE by omission) and whatever the
construct's own value/iterable/context-expression spells is captured as payload -- a bare Name
among those candidates is recorded as an ALIAS (not a payload element), which is what makes a
tuple-swap sound: `a`'s own analysis must account for `a` now possibly holding whatever `b` could
hold, and only the union-find alias step can express that. The two dynamic-mutator shapes from
finding 5 get the identical treatment via their own two-pattern detector. "Unknown never means
invisible; unknown means unproven" (this round's own words) -- but this is NOT a sensitivity-
independent gate: a name touched by one of these shapes that never actually carries a verb path
stays exactly as unflagged as it always was. See below (MEASUREMENT) for why this round stops
there and does NOT also make the refusal decision itself sensitivity-independent at every spawn
call site, despite the brief that opened this round asking for exactly that (rule B).

Finding 4 (bare verb literals) is closed as a NEW verb-detection case, `bare_verb_literal` in
`_pin_guard_resolve.py`: a bare string constant at argv[0] matching this repo's own root-shim/
dispatcher roster (with an optional leading `./` or `/`) is now sensitive, with NO `REPO`-path
join required at all. Deliberately does not look at, or try to prove/disprove, any `cwd=` kwarg
on the call -- see MEASUREMENT below for the one real, legitimate collision this produced against
the real tree, waived at its own call site rather than redesigned around.

Finding 6 is closed as three narrow verb-DETECTION extensions in `_pin_guard_resolve.py` (an
f-string's nested `str(REPO)` unwrap; an `IfExp`/`+`-concat accepted at a join chain's TAIL hop
only, every candidate string tried against the roster; a `Starred` element that wraps an inline
List/Tuple literal has ITS OWN elements inspected in place) -- NOT a blanket "every `Starred`/
`IfExp`/unrecognized `Call`/`BinOp` inside an argv literal is unproven" rule. See MEASUREMENT: the
blanket form was measured and rejected for the same reason rule B was.

Finding 7 (non-disclosure) is closed by this section itself, and by MEASUREMENT below being a
verbatim, numbers-carrying record rather than a prose claim.

MEASUREMENT -- WHY THIS ROUND DOES NOT IMPLEMENT A SENSITIVITY-INDEPENDENT REFUSAL AT EVERY SPAWN
CALL SITE (the brief's rule B), NOR A BLANKET PER-ELEMENT CLASSIFICATION INSIDE EVERY INLINE ARGV
LITERAL (the brief's rule C), even though both were requested. The brief's own instruction was:
measure the real-tree false-positive surface first, and if it exceeds ~10 files, STOP AND REPORT
rather than push the rule through or blanket-waive around it. Both measurements came back far
past that line:
  - Rule B (every spawn call's argv must be an inline literal or a Name proven clean, regardless
    of sensitivity): of ~203 in-scope files, roughly 75 pass a bare Name as argv to a real
    `subprocess.*`/`os.system` call. Of those, only 1 file's Name-argv is a clean single-literal-
    binding-zero-events case; the other ~74 either bind the Name from a bare function PARAMETER
    (the dominant, entirely benign `def sh(args): return subprocess.run(args, ...)` /
    `def run(cwd, *a): return subprocess.run(a, cwd=cwd, ...)` wrapper idiom -- an abstraction
    boundary this single-file AST census cannot and should not try to see through) or mutate the
    argv locally with an ordinary, non-sensitive event (`cmd += ["-v", f"{k}={v}"]` building a
    psql flag list, `cmd.append(extra)`) that has nothing to do with any repo verb. Making the
    refusal decision sensitivity-independent would newly refuse ALL of these -- not a hypothetical
    ~10 files, a measured ~75, essentially this test corpus's dominant wrapper convention.
  - Rule C (every element of an inline-literal argv must positively classify SAFE or the whole
    call is unproven, regardless of sensitivity): the same real tree carries 58 `Starred` elements
    inside spawn-call argv literals across ~35 files, EVERY one of them `*args`/`*extra` splatting
    a bare parameter (never a literal list) in the equally dominant
    `def _psql(*args): return subprocess.run(["psql", ..., *args], ...)` idiom. Blanket-refusing
    any `Starred` element (the natural reading of "one rule, no per-shape enumeration" applied to
    an unrecognized-shape element) would newly refuse essentially the same ~35 files.
Both numbers were produced by running the recognizer/tracker actually shipped in this commit
against the real `seen-red/**`, `instruments/**`, `kernel/fixtures/**` tree (measurement scripts
were throwaway, not committed; the counts above are the observed output, reproducible by anyone
who re-runs the same recognizer). Per the brief's own escape hatch, this is a STOP AND REPORT, not
a blanket waiver: rules A (census) and the narrow, verb-DETECTION halves of findings 4/5/6 above
are implemented in full; the sensitivity-INDEPENDENT form of B/C is NOT implemented this round,
named here as the honest, deliberately-declined remainder rather than silently narrowed to fit.

WHAT THIS GATE NOW CLAIMS, AND DOES NOT CLAIM (round 4's honest inventory, superseding round 3's):
CLAIMS -- an argv is proven safe only when (1) it is a literal at the call site (every element
checked against the full verb grammar, including this round's bare-literal/f-string/IfExp-concat/
Starred-of-literal extensions), or (2) a Name with exactly one literal binding and zero other
qualifying events ANYWHERE in the file, where "qualifying event" now also includes every binding
shape `_pin_guard_census.py` sweeps (chained assign, tuple/list-unpack, a swap, a `for` target,
walrus, `with`/`except ... as`, annotated assign, comprehension target) and the two dynamic-
mutator shapes from finding 5. Every other argv that is ever found sensitive is REFUSED-AS-
UNPROVEN. DOES NOT CLAIM (the honestly-scoped remainder, unchanged in kind from round 3, now
precisely three items, per the brief's own rule D):
  - Spawn-CALLEE recognition: only `subprocess.run/Popen/check_call/check_output/call` (attribute
    form, or `functools.partial` over one of those as its own first positional arg) and
    `os.system` are recognized as spawn-like. `exec`/`eval`, `ctypes`, `os.posix_spawn`, a bare
    `from subprocess import run; run(...)` call, and any OTHER spawn mechanism are simply not on
    this gate's roster -- out of scope, not silently approximated.
  - Cross-module constant import (`from helper import LED`): single-file AST census, stops at the
    file boundary by construction.
  - Sensitivity-independent argv-fail-closed at every spawn call site (rules B/C in their full,
    requested form): named above (MEASUREMENT) as a deliberate, measured non-implementation, not
    a silent gap -- the one remaining item that is NOT merely a scope boundary but an explicit
    stop-and-report against this round's own brief.
A `Starred` element wrapping anything OTHER than an inline List/Tuple literal (a bare parameter,
a comprehension, a Subscript), an `IfExp`/unrecognized `Call`/`BinOp` argv ELEMENT that is not one
of the verb-grammar shapes above, and a plain, well-behaved Name-argv with a local, non-sensitive
mutation event (the psql/git-flag-building idiom) all stay OUT OF SCOPE, unflagged -- exactly as
every prior round, and now explicitly named rather than left to be rediscovered by a fifth lap.

WHAT THIS DOES NOT CLAIM (mechanical detail, carried forward from round 3):
  - A NAME-LIST census over each file's own REPO/REPO_ROOT/AUTOHARN_ROOT/EXEC_ROOT convention,
    not alias/call-graph analysis.
  - Verb vocabulary: shim-verbs.sh's SHIM_VERBS_ALL (root shims/scaffold set) + literal
    "autoharn", sourced live -- DIFFERENT roster from libexec/autoharn/'s own live directory
    listing (carries attest-tags/migrate, omits verify-commission/attest-doc) -- each shape
    checked against its own authoritative roster. The bare-verb-literal check (finding 4) is
    checked ONLY against the shim/dispatcher roster (never `libexec_verbs` -- a
    `libexec/autoharn/<verb>` path is never invoked bare).
  - `.update(opaque_dict_variable)` is not traced to its own construction; only an inline dict
    literal or a PICKUP_DEPLOYMENT= keyword is recognized. `os.system` under an import alias is
    not recognized.
  - The fourth leak kind -- reading whatever deployment.json sits in os.getcwd() -- is
    `serve_existing_world`'s own job (this gate's complement, not its duplicate).
  - WAIVER_TOKEN is presence-only; it cannot judge whether the stated reason is sound.

ROUND 1/2 findings, disposition unchanged, kept for context (see git history for the full text of
each round's own POSTURE section): round 1 rejected a full-scope inversion (refusing every
subprocess-spawning file outright) as measured overkill (~150/203 files are plain git/psql calls);
round 2 closed the waiver-scoping/os.path.join/functools.partial/semicolon-sharing findings.

SCOPE: seen-red/**/*.py, instruments/**/*.py, kernel/fixtures/**/*.py (submodules excluded).
Exit 0 clean (or every match waived); exit 1 naming every offending line otherwise.

Usage: python3 gates/fixture_deployment_pin_guard.py [path ...]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling _pin_guard_*.py, same dir
from _pin_guard_checks import (  # noqa: E402  (path insert above must run first)
    _iter_target_files,
    _libexec_verb_names,
    _shim_verb_names,
    violations_in,
)

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
