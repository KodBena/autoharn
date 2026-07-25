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
"Guarded" below means: caught for every ENUMERATED spelling this gate's 35 banked specimens
witness, not proven closed against every possible one -- see the FINAL ROUND section (below,
after the round-by-round history) for the honest, demoted claim and the forward pointer to the
runtime-foreclosure mechanism that is the actual guarantee.

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

FINAL ROUND (maintainer disposition 2026-07-26, ledger row 1316, on the row-1315 escalation) --
THIS GATE IS DEMOTED. Five fresh-context strengthened-tier review laps in a row (rounds 1, 3, 4,
and two more beyond round 4 not separately numbered above) each genuinely closed the prior round's
findings, and each NEXT lap witnessed new false-clean results on ordinary, non-adversarial Python
idioms it had never occurred to the previous lap to try. That is not noise: it is the structural
signature of a static AST census trying to enumerate an open grammar. The maintainer's ruling
(row 1316, verbatim: "I'll take your recommendation") is to STOP re-dispatching this loop and
instead say plainly what five rounds of evidence show this gate to be:

THIS GATE IS A BEST-EFFORT DETECTOR OF THE ENUMERATED ACCIDENT IDIOMS ITS SPECIMENS WITNESS -- IT
IS NOT, AND HAS NEVER BEEN, A SOUNDNESS GUARANTEE AGAINST A DELIBERATE, UNUSUAL, OR MERELY
UNENUMERATED SPELLING OF THE SAME LEAK. Every accident this gate catches is one that also shows up
as a RED specimen in `seen-red/fixture-deployment-pin-guard/run_fixtures.py` (35 banked specimens
as of this round) -- the specimen list IS the coverage claim, not a sample of it. Anything not
shaped like one of those specimens is, by construction, not provably caught, whether or not this
docstring happens to name it. The class-CLOSING mechanism -- the one meant to actually foreclose
the leak rather than detect its known shapes -- is commissioned separately: RUNTIME FORECLOSURE
(rows 1315/1316), a Fable spec pending the maintainer's yes/no, which moves enforcement from
"recognize the call" (what this gate does, and what a fresh mind keeps finding new ways around) to
"the called thing refuses" (the fixture runner marks its environment; this repo's own verbs refuse
under that marker, waivable explicitly, foreclosing every argv spelling at once because none of
them matter once the callee itself won't cooperate). Until that spec lands, this gate remains
useful as FAST FEEDBACK in front of it -- a pre-commit signal that catches the common-case mistake
cheaply -- never cite it as the guarantee.

WHAT THIS GATE CLAIMS, AND DOES NOT CLAIM (this round's honest inventory, superseding round 4's):
CLAIMS -- an argv is proven safe only when (1) it is a literal at the call site (every element
checked against the full verb grammar, including round 4's bare-literal/f-string/IfExp-concat/
Starred-of-literal extensions), or (2) a Name with exactly one literal binding and zero other
qualifying events ANYWHERE in the file, where "qualifying event" includes every binding shape
`_pin_guard_census.py` sweeps (chained assign, tuple/list-unpack, a swap, a `for` target, walrus,
`with`/`except ... as`, annotated assign, comprehension target) and the two dynamic-mutator shapes
from round 4's finding 5. Every other argv that is ever found sensitive is REFUSED-AS-UNPROVEN.
This round widened two things, each a plain widening of an existing scan loop or roster, no new
analysis machinery, each re-measured against the real tree with zero new false positives (see
MEASUREMENT above, unchanged by this round, and the fresh confirmation in `red.txt`'s final-round
appendix): CHECK 1 now scans every Call's KEYWORD argument values too, not only `node.args`
(closes `subprocess.run(args=[...])` and, for free, since CHECK 1 has always been callee-agnostic,
`functools.partial(subprocess.run, args=[...])`); `bare_verb_literal` now also accepts a
`legacy/<verb>` prefix (one more roster alternative in the same regex, matching the REPO-joined
form's existing `legacy/<verb>` recognition).

KNOWN-UNCAUGHT (named here as what a fifth fresh-context lap found, not silently narrowed around --
DELIBERATELY NOT FIXED this round because each needs genuinely new analysis machinery, not a
widening of an existing loop/roster, which is the line this round holds):
  - `ast.Match` capture patterns (`match cmd: case [x, *rest]: ...`) are not swept by
    `_pin_guard_census.py` at all -- a name bound inside a `case` pattern gets no facts entry,
    same blind spot round 4 closed for every OTHER binding construct, just not this one. Not
    symmetrical with the existing For/With sweep (which reuses the plain Tuple/List/Starred
    target walker `_names_in_target`): `ast.Match`'s own pattern node hierarchy (`MatchAs`,
    `MatchStar`, `MatchMapping`'s `rest`, `MatchClass`'s nested/keyword patterns, `MatchOr`) needs
    its own recursive walker, which is new code, not a one-line addition to an existing one.
  - Attribute-typed argv (`self.cmd`, `k.cmd`) is invisible: every binding/event/sensitivity
    path in `_pin_guard_argv.py`/`_pin_guard_census.py` is keyed by bare `Name` id; an
    `ast.Attribute` target or read is never tracked as anything, so `self.cmd = [str(REPO /
    "led")]; subprocess.run(self.cmd)` passes clean. Needs a second tracked-key shape (object +
    attribute name) alongside the existing bare-Name one -- new state, not a widened loop.
  - A one-hop Name bound to a BARE VERB STRING (`x = "led"; subprocess.run([x, "status"])`) is
    invisible: `bare_verb_literal` only inspects the literal AT the call site, and
    `verb_path_bindings`/`resolve_verb_element` only resolve a Name bound to a REPO-JOIN
    expression, never a Name bound to a plain string constant. Closing it needs a parallel
    binding-tracking table for bare-string-literal assigns, not a regex tweak.
  - `vars()`-based mutation (`vars()["cmd"].append(...)`), `methodcaller`-driven mutation
    (`operator.methodcaller("append", x)(cmd)`), and `__iadd__` invoked directly
    (`cmd.__iadd__([...])`) are not swept by `sweep_dynamic_mutators` -- that sweep recognizes
    exactly two named shapes (`getattr(...)`, `globals()[...]`); each additional shape found is
    its own new pattern-detector function, the same shape of work finding 5 already showed does
    not generalize by widening.
  - Spawn-CALLEE recognition: only `subprocess.run/Popen/check_call/check_output/call` (attribute
    or bare-Name form) and `os.system` are recognized as spawn-like for CHECK 1b (shell-string
    refusal) and `is_argv_sink_call`. `functools.partial(subprocess.run, ...)` is CAUGHT when its
    argv is a literal/keyword argument (CHECK 1 is callee-agnostic, walks every Call regardless of
    func) but is NOT itself recognized as a spawn-like callee anywhere else in this gate -- an
    earlier round's docstring claimed a "functools.partial special-casing" that does not and never
    did exist in the code; that false claim is deleted here, not implemented, per the maintainer's
    disposition to correct rather than chase every falsified claim into new code. `exec`/`eval`,
    `ctypes`, `os.posix_spawn`, a bare `from subprocess import run; run(...)` call, and any OTHER
    spawn mechanism are simply not on this gate's roster -- out of scope, not silently
    approximated.
  - Cross-module constant import (`from helper import LED`): single-file AST census, stops at the
    file boundary by construction.
  - Sensitivity-independent argv-fail-closed at every spawn call site (rules B/C in their full,
    requested form, round 4's brief): named above (MEASUREMENT) as a deliberate, measured
    non-implementation, not a silent gap.
A `Starred` element wrapping anything OTHER than an inline List/Tuple literal (a bare parameter,
a comprehension, a Subscript), an `IfExp`/unrecognized `Call`/`BinOp` argv ELEMENT that is not one
of the verb-grammar shapes above, and a plain, well-behaved Name-argv with a local, non-sensitive
mutation event (the psql/git-flag-building idiom) all stay OUT OF SCOPE, unflagged -- exactly as
every prior round.

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
round 2 closed the waiver-scoping/os.path.join/semicolon-sharing findings (round 2's own
"functools.partial" finding closed only the ARGV-AS-NON-FIRST-POSITIONAL-ARG shape, via CHECK 1's
pre-existing callee-agnostic scan -- never a partial-aware spawn-callee recognizer; see
KNOWN-UNCAUGHT above for the claim that conflated the two and is now corrected).

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
