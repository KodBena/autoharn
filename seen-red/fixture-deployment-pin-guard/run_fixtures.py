#!/usr/bin/env python3
"""Both-polarity fixture for gates/fixture_deployment_pin_guard.py (fixture-scratch-pinning-
guard, ledger row 1249 — generalizing beyond serve_existing_world's own tempdir/repo-disjoint
refusal, seen-red/boundary-service/run_fixtures.py).

GREEN: this repo's own current fixture tree (seen-red/, instruments/, kernel/fixtures/) passes
-- no fixture invokes this checkout's own operator verbs directly, and none mutates
os.environ["PICKUP_DEPLOYMENT"] globally.

RED (repo-root verb invocation, the row-1237-1244/1248 leak class): a synthetic fixture file
that builds a subprocess argv from `REPO / "led"` (REPO bound to this checkout's own root, the
same top-of-file convention every real seen-red driver uses) -- refused, naming the offending
line and verb.

RED (repo-root verb invocation via legacy/ path): the same shape, one level deeper --
`REPO / "legacy" / "pickup"` -- also refused.

RED (os.environ global mutation): a synthetic fixture file that does
`os.environ["PICKUP_DEPLOYMENT"] = "/some/path"` directly -- refused, naming the "pin
per-subprocess, never inherited" violation.

GREEN (scratch-scoped invocation stays clean): a synthetic fixture that invokes
`dest / "led"` (dest a tempfile.mkdtemp()-derived scratch path, NOT one of the REPO-like names)
-- the safe, existing convention -- must NOT be flagged.

GREEN (local env dict stays clean): a synthetic fixture that builds
`env = {**os.environ, "PICKUP_DEPLOYMENT": str(p)}` and passes it via a subprocess call's own
`env=` kwarg -- the safe, existing convention -- must NOT be flagged.

FRESH-CONTEXT STRENGTHENED-TIER REVIEW ROUND (BLOCKS MERGE on the prior version of this gate,
this same commit's fix-round) demonstrated five LIVE evasions of the checks above -- each is now
its own RED specimen, banked here so they can never silently regress:

RED (os.system shell string): `os.system(f"{REPO/'led'} status")` -- refused outright regardless
of content (finding 1).

RED (subprocess shell=True string command): `subprocess.run(f"{REPO/'led'} status", shell=True)`
-- refused outright, same reason (finding 1).

RED (libexec/autoharn/<verb> path, the umbrella-CLI relocation target): `subprocess.run([str(REPO
/ "libexec" / "autoharn" / "led"), "status"])` -- refused, same leak class as the pre-umbrella
`REPO / "led"` shape (finding 2).

RED (os.environ.update carrying PICKUP_DEPLOYMENT): `os.environ.update({"PICKUP_DEPLOYMENT":
"/tmp/whatever"})` -- refused (finding 3).

RED (os.environ alias mutation): `d = os.environ; d["PICKUP_DEPLOYMENT"] = "/tmp/whatever"` --
refused (finding 3).

RED (wrapper-indirected argv, the finding-4 dominant real shape): a module constant
`LED = REPO / "led"` referenced only via `str(LED)` inside a pre-built `cmd = [...]` variable
passed to a wrapper function (never subprocess.* directly, never an inline literal at the call
site) -- refused (this fix-round's own CHECK 1 broadening: callee-agnostic, one hop of
argv-list-variable AND verb-path-constant resolution).

GREEN (waived invocation stays clean): the SAME `REPO / "led"` shape as the first RED case, but
with a `# fixture-scratch-pinning-guard-waiver: <reason>` comment on the CALL's own line (round-2
review fix: a waiver on the binding's own line no longer counts at all -- see RED_WAIVER_BLANKET
below for exactly why) -- must NOT be flagged (the escape hatch this fix-round's POSTURE section
commits to).

FIX-ROUND 2 (fresh-context strengthened-tier review BLOCKED commit 26c7c48; this run_fixtures.py
update is that round's own red-first bank -- every reviewer-verified evasion below reproduces red
against the PRIOR gate version were it re-run, and green against the current one):

RED (waiver-blanket, THE BLOCKER): a waiver comment sitting on a constant's BINDING line
(`AUTOHARN = REPO / "autoharn"  # waiver: ...`) used to silence EVERY later use of that constant,
including a separate, never-reviewed real verb invocation lower in the same file. Refused now:
the waiver only counts on the Call's own line, so the unrelated second call is still flagged.

RED (post-binding subscript-mutation): `cmd = [str(AUTOHARN), "--help"]` (safe on its own, per
`dispatcher_invocation_is_safe`) followed by `cmd[1] = "led"` then `subprocess.run(cmd)` -- the
prior gate judged the ORIGINAL literal safe and never saw the mutation; refused now (argv-list
simulation replays the subscript-assignment before judging).

RED (append-built argv from an empty list): `cmd = []; cmd.append(str(AUTOHARN));
cmd.append("led"); subprocess.run(cmd)` -- the prior gate's `_bound_list_literals` only ever saw
the initial (empty) literal; refused now (same simulation).

RED (os.path.join / PurePath.joinpath): `os.path.join(REPO, "led")` and `(REPO).joinpath("led")`
-- this repo's OWN idiom in ~15 real non-verb-path files, invisible to the prior gate's
BinOp/f-string-only matcher; both refused now.

RED (functools.partial argv as a non-first positional arg): `functools.partial(subprocess.run,
[str(AUTOHARN), "led"])` -- the argv list is `partial`'s SECOND positional argument, never
`args[0]` of any call the prior gate inspected; refused now (CHECK 1 scans every positional arg
of every Call, not only the first).

RED (semicolon-shared waiver line): `_x = 1; subprocess.run([str(AUTOHARN), "led"])  # waiver:
...` -- a waiver comment on a line hosting two statements no longer counts (a future edit could
otherwise slip an unrelated second statement onto an already-waived line and inherit its cover).

FIX-ROUND 3 (fresh-context strengthened-tier review BLOCKED 8821dff, the round-2 replay engine;
PROVE-OR-REFUSE inversion, see gates/fixture_deployment_pin_guard.py's own POSTURE section for
the full account). Three EXPECTATION CHANGES on existing specimens above -- each still refuses
(still RED), only the REASON changes, tracing directly to the inversion, never to convenience:
RED_WRAPPER_INDIRECTED, RED_SUBSCRIPT_MUTATION, and RED_APPEND_BUILT_ARGV now report "argv
dataflow not statically provable" (an UNPROVEN Name-bound argv) instead of naming a specific
resolved verb -- the round-2 replay engine used to trust its own reconstruction of these three
shapes' final contents; round 3 refuses them outright instead of reconstructing, which is the
more honest verdict for a wrapper-indirected or post-binding-mutated argv. No existing GREEN
case changes.

New RED-first specimens, one per commission finding (A, B) plus a demonstration that findings
C/D DISSOLVE rather than get patched (see gate docstring):

RED (finding A, opaque-before-sensitive): `cmd = []; cmd[i] = "x"` (dynamic-index subscript
assign) BEFORE `cmd.append(str(REPO / "led"))` -- the round-2 replay engine's `opaque` flag was
set at the FIRST event regardless of sensitivity, and once opaque, LATER appends were silently
skipped (never marked sensitive, never returned at all): the whole name vanished from the
gate's view. Refused now: this gate no longer tracks a "final contents" reconstruction to skip
appends into, so there is nothing to silently drop -- any qualifying event on a name that is
EVER sensitive makes it unproven, unconditionally.

RED (finding B, one-hop alias append): `b = cmd; b.append(str(REPO / "led"))` -- the round-2
replay engine read `b = cmd` as an "unbind" event for `b` (since the RHS wasn't a list literal),
discarding `b` entirely without ever recording the alias; `b.append(...)` was then invisible
(no tracked state for `b`), and `cmd`'s own separately-tracked state was checked as if the
append had never happened. Refused now: an alias assign (`x = y`) is tracked and CONTAMINATES
both names -- if either is ever sensitive, both come back unproven.

RED (findings C/D dissolve, branch + textual order no longer matter): `cmd = ["status"]`
followed by `if flag: cmd.append(str(REPO / "led"))` -- under the round-2 replay engine this
needed a control-flow judgment (did this arm run?) that a textual-order replay could not make
soundly (finding D), and a helper defined above but called later would have replayed its
mutation out of true execution order (finding C). Round 3 needs no such judgment: refused
unconditionally, because ANY qualifying event anywhere in the file counts, branch or no branch,
above or below, and it is exactly as much a REFUSAL as if the append always ran -- the safe
(fail-closed) side of the ambiguity coincides with the flagged side, for every case, by
construction.

FIX-ROUND 4 (fresh-context strengthened-tier review of round 3; CENSUS FAIL-CLOSED, see
gates/fixture_deployment_pin_guard.py's own POSTURE section for the full account, including the
MEASUREMENT record for why this round does NOT implement the brief's rule B/C in their full
sensitivity-independent form). Every specimen below is one lap-4 finding, banked so it can never
silently regress again:

RED (finding 1, chained assign): `x = y = [str(REPO / "led"), "status"]` then `subprocess.run(y)`
-- `analyze_names`' own Assign case required `len(targets) == 1`, so BOTH names were invisible;
refused now (census sweep contaminates every target of a chained assign).

RED (finding 2, tuple-unpack): `cmd, other = str(REPO / "led"), "status"` then
`subprocess.run(cmd)` -- only a bare `Name`/`Subscript(Name)` target was ever modeled; refused now.

RED (finding 2, for-loop target): `for cmd in (str(REPO / "led"), "status"): pass` then
`subprocess.run(cmd)` -- refused now (census sweep's for-target contamination).

RED (finding 2, tuple-swap): `a = ["status"]; b = [str(REPO / "led")]; a, b = b, a` then
`subprocess.run(a)` -- `a`'s OWN literal binding (`["status"]`) was, and remains, innocuous; the
swap is what makes `a` unprovable (it may now hold what `b` held). The census sweep records the
swap as a mutual ALIAS (not a payload copy -- a bare Name isn't itself verb-shaped), and the
existing union-find alias step does the rest: `a`'s component merges with `b`'s, which IS
sensitive, so both come back UNPROVEN together.

RED (finding 3, walrus): `if (cmd := [str(REPO / "led"), "status"]): subprocess.run(cmd)` --
`ast.NamedExpr` was swept by no prior round at all; refused now.

RED (finding 4, bare verb literal, no REPO join): `subprocess.run(["led", "status"])` -- the
leak class's most literal spelling, invisible to every prior round (all of which only ever looked
for a REPO-ROOTED PATH); refused now, naming the bare literal directly.

RED (finding 4, bare verb literal with a leading `./`): `subprocess.run(["./led", "status"])` --
same shape, `./`-prefixed; refused now.

RED (finding 5, getattr-based mutation): `cmd = ["status"]; getattr(cmd, "append")(str(REPO /
"led")); subprocess.run(cmd)` -- `getattr(cmd, "append")(...)` never spells `cmd.append(...)`, so
the mutator-method sweep never saw it, and the append's own argument was never captured as a
payload element (some OTHER, unrelated event may have fired against `cmd`, but the appended
element itself was dropped before the provable/unproven branch ever looked at it); refused now
(the census sweep's own getattr-based-mutation detector, keyed by the exact same construct).

RED (finding 5, globals()-based mutation): `cmd = ["status"]` at module level,
`globals()["cmd"].append(str(REPO / "led"))` inside a function -- no `Name` node spells `cmd` at
the mutation site at all, so no event of any kind ever touched `cmd`'s facts; refused now (the
census sweep's globals()-based-mutation detector, keyed by the string literal).

RED (finding 6, Starred unpacking a literal list carrying the verb): `subprocess.run([*[str(REPO
/ "led")], "status"])` -- the `Starred` element wraps its OWN inline List literal, invisible to a
matcher that only ever looked at each element directly; refused now (CHECK 1 unpacks a
`Starred(List/Tuple literal)` in place before inspecting elements -- a `Starred` wrapping anything
else, e.g. `*args`, is untouched, see MEASUREMENT for why).

RED (finding 6, IfExp on a join's tail): `subprocess.run([str(REPO / ("led" if flag else
"pickup")), "status"])` -- the join chain's RIGHTMOST hop is an `IfExp`, not a plain constant;
refused now (every candidate string at the tail hop is tried against the verb roster).

RED (finding 6, f-string with a nested `str(REPO)` call): `subprocess.run([f"{str(REPO)}/led",
"status"])` -- only a bare `{REPO}` FormattedValue was recognized before; refused now (the
FormattedValue's own value is unwrapped through `str(...)` first, same as every other shape here).

GREEN (round-3 deliberate-pass case, RECONFIRMED, not flipped): a Name-bound argv mutated with an
ordinary, non-sensitive event and never touching a repo verb (`cmd = ["git", "status"]; cmd +=
["-v"]; subprocess.run(cmd)`) stays GREEN under this round too -- this is the brief's own rule B
asking for a sensitivity-independent refusal here (the mutation alone, with no verb ever in
sight, would refuse), which this round's MEASUREMENT section declines to implement (measured
~75 real files using this exact non-sensitive-mutation/wrapper-parameter idiom, the corpus's
dominant convention -- see gates/fixture_deployment_pin_guard.py's own docstring). Kept GREEN
here, deliberately, rather than silently narrowing the brief without saying so.

FINAL ROUND (maintainer disposition 2026-07-26, ledger row 1316, on the row-1315 non-converging-
review-loop escalation after a FIFTH fresh-context lap found new false-clean ordinary idioms):
STOP closing holes, DEMOTE the gate's claims to what it demonstrably is (a best-effort DETECTOR
of enumerated accident idioms, not a soundness guarantee -- see gate module docstring's FINAL
ROUND section for the full inventory). Two of the lap-5 findings turned out to be genuine
one-line widenings of existing scan loops/rosters -- no new analysis machinery -- and are closed
here, each banked as its own RED specimen:

RED (keyword-arg argv): `subprocess.run(args=[str(REPO / "led"), ...])` -- CHECK 1 used to walk
only `node.args` (positional), so an argv passed as the `args=` keyword was invisible regardless
of content; refused now (the walk widened to `node.args` PLUS every keyword value, one line, no
new logic).

RED (functools.partial with a keyword-arg argv): `functools.partial(subprocess.run,
args=[str(REPO / "led"), ...])` -- the same keyword-argv blind spot, demonstrated on the shape the
prior rounds' docstring falsely claimed was specially recognized (it was not -- no partial-aware
code existed anywhere in this gate; the claim is deleted, not implemented, in this round's
docstring). Caught for free by the same CHECK 1 widening above, since CHECK 1 has always been
callee-agnostic (walks every Call node, not just recognized spawn-callees).

RED (bare `legacy/<verb>` literal, no REPO join): `subprocess.run(["legacy/pickup", "status"])` --
`bare_verb_literal`'s regex only ever accepted an optional leading `.`/`/`, never a `legacy/`
prefix, even though the REPO-joined form of this exact shape (`REPO / "legacy" / "pickup"`) was
already recognized; refused now (one more roster alternative in the same regex, no new matching
logic).

Three other lap-5 findings (ast.Match capture patterns, attribute-typed argv `K.cmd`/`self.cmd`,
a one-hop bare-verb Name) were measured against the "pure widening, no new machinery" bar and
found to need genuinely new analysis code (a pattern-name walker for ast.Match's own node
hierarchy is not expressible via the existing Tuple/List/Starred target walker; attribute-typed
argv and a bare-verb-string Name binding both need a new tracked-binding class this gate does not
carry). Named as known-uncaught, disclosed rather than silently narrowed -- see the gate module
docstring's FINAL ROUND section for the full, current claim inventory.

Runs against throwaway tempfile copies; zero residue in the repo itself."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
GATE = REPO / "gates" / "fixture_deployment_pin_guard.py"

RED_REPO_LED = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it():
    return subprocess.run([str(REPO / "led"), "finding", "hello"], capture_output=True, text=True)
'''

RED_REPO_LEGACY_PICKUP = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it():
    return subprocess.run([str(REPO / "legacy" / "pickup")], capture_output=True, text=True)
'''

RED_ENVIRON_MUTATION = '''\
import os
import subprocess

os.environ["PICKUP_DEPLOYMENT"] = "/tmp/whatever/deployment.json"


def run_it():
    return subprocess.run(["true"], capture_output=True, text=True)
'''

GREEN_SCRATCH_SCOPED = '''\
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it(dest: Path):
    return subprocess.run([str(dest / "led"), "finding", "hello"], capture_output=True, text=True)
'''

GREEN_LOCAL_ENV_DICT = '''\
import os
import subprocess
from pathlib import Path


def run_it(p: Path):
    env = {**os.environ, "PICKUP_DEPLOYMENT": str(p)}
    return subprocess.run(["some-verb"], capture_output=True, text=True, env=env)
'''

# --- the five reviewer-demonstrated evasions (fresh-context strengthened-tier review round,
# this same commit's fix-round) -- each now its own RED specimen, see module docstring above.

RED_OS_SYSTEM = '''\
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it():
    return os.system(f"{REPO / 'led'} status")
'''

RED_SHELL_TRUE = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it():
    return subprocess.run(f"{REPO / 'led'} status", shell=True, capture_output=True, text=True)
'''

RED_LIBEXEC_LED = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it():
    return subprocess.run([str(REPO / "libexec" / "autoharn" / "led"), "status"],
                          capture_output=True, text=True)
'''

RED_ENVIRON_UPDATE = '''\
import os
import subprocess

os.environ.update({"PICKUP_DEPLOYMENT": "/tmp/whatever/deployment.json"})


def run_it():
    return subprocess.run(["true"], capture_output=True, text=True)
'''

RED_ENVIRON_ALIAS = '''\
import os
import subprocess

d = os.environ
d["PICKUP_DEPLOYMENT"] = "/tmp/whatever/deployment.json"


def run_it():
    return subprocess.run(["true"], capture_output=True, text=True)
'''

RED_WRAPPER_INDIRECTED = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LED = REPO / "led"


def _sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def run_it():
    cmd = [str(LED), "finding", "hello"]
    return _sh(cmd)
'''

GREEN_WAIVED_LED = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LED = REPO / "led"


def run_it():
    # Waiver sits on the CALL's own line below, not on LED's binding above (round-2 review fix,
    # finding 1: a binding-line waiver used to blanket every use).
    return subprocess.run([str(LED), "finding", "hello"], capture_output=True, text=True)  # fixture-scratch-pinning-guard-waiver: synthetic GREEN specimen, proven safe by construction (test-only)
'''

# --- fix-round-2 RED specimens (fresh-context strengthened-tier review that BLOCKED 26c7c48) --

RED_WAIVER_BLANKET = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUTOHARN = REPO / "autoharn"  # fixture-scratch-pinning-guard-waiver: dispatcher, --help only, safe


def run_it_help():
    return subprocess.run([str(AUTOHARN), "--help"], capture_output=True, text=True)


def run_it_close_ledger_work():
    # NOT waived, and not a dispatcher-safe --help/-h/service/unknown-verb call: this used to
    # slip through under the binding's own waiver above (the blanket-exemption bug).
    return subprocess.run([str(AUTOHARN), "led", "work", "close", "--force"],
                          capture_output=True, text=True)
'''

RED_SUBSCRIPT_MUTATION = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUTOHARN = REPO / "autoharn"


def run_it():
    cmd = [str(AUTOHARN), "--help"]
    cmd[1] = "led"
    return subprocess.run(cmd, capture_output=True, text=True)
'''

RED_APPEND_BUILT_ARGV = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUTOHARN = REPO / "autoharn"


def run_it():
    cmd = []
    cmd.append(str(AUTOHARN))
    cmd.append("led")
    return subprocess.run(cmd, capture_output=True, text=True)
'''

RED_OS_PATH_JOIN = '''\
import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it():
    return subprocess.run([os.path.join(REPO, "led"), "finding", "hello"],
                          capture_output=True, text=True)
'''

RED_JOINPATH = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it():
    return subprocess.run([str(REPO.joinpath("led")), "finding", "hello"],
                          capture_output=True, text=True)
'''

RED_PARTIAL_ARGV = '''\
import functools
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUTOHARN = REPO / "autoharn"


def run_it():
    runner = functools.partial(subprocess.run, [str(AUTOHARN), "led"],
                                capture_output=True, text=True)
    return runner()
'''

RED_SEMICOLON_SHARED_WAIVER = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUTOHARN = REPO / "autoharn"


def run_it():
    _x = 1; return subprocess.run([str(AUTOHARN), "led"], capture_output=True, text=True)  # fixture-scratch-pinning-guard-waiver: bogus, shares this line with an unrelated statement
'''

# --- fix-round-3 RED specimens (fresh-context strengthened-tier review that BLOCKED 8821dff,
# the round-2 replay engine) -- each is one commission finding, see module docstring above.

RED_OPAQUE_BEFORE_SENSITIVE = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it(i):
    cmd = []
    cmd[i] = "placeholder"
    cmd.append(str(REPO / "led"))
    return subprocess.run(cmd, capture_output=True, text=True)
'''

RED_ALIAS_APPEND = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it():
    cmd = ["status"]
    b = cmd
    b.append(str(REPO / "led"))
    return subprocess.run(cmd, capture_output=True, text=True)
'''

RED_BRANCH_ORDER_DISSOLVED = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it(flag):
    cmd = ["status"]
    if flag:
        cmd.append(str(REPO / "led"))
    return subprocess.run(cmd, capture_output=True, text=True)
'''


# --- fix-round-4 RED specimens (fresh-context strengthened-tier review of round 3; census
# fail-closed, see gate module docstring's POSTURE section) -- one per lap-4 finding. -----------

RED_CHAINED_ASSIGN = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it():
    x = y = [str(REPO / "led"), "status"]
    return subprocess.run(y, capture_output=True, text=True)
'''

RED_TUPLE_UNPACK = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it():
    cmd, other = str(REPO / "led"), "status"
    return subprocess.run(cmd, capture_output=True, text=True)
'''

RED_FOR_TARGET = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it():
    cmd = "unused"
    for cmd in (str(REPO / "led"), "status"):
        pass
    return subprocess.run(cmd, capture_output=True, text=True)
'''

RED_TUPLE_SWAP = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it():
    a = ["status"]
    b = [str(REPO / "led")]
    a, b = b, a
    return subprocess.run(a, capture_output=True, text=True)
'''

RED_WALRUS = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it():
    if (cmd := [str(REPO / "led"), "status"]):
        return subprocess.run(cmd, capture_output=True, text=True)
    return None
'''

RED_BARE_LED = '''\
import subprocess


def run_it():
    return subprocess.run(["led", "status"], capture_output=True, text=True)
'''

RED_BARE_DOT_LED = '''\
import subprocess


def run_it():
    return subprocess.run(["./led", "status"], capture_output=True, text=True)
'''

RED_GETATTR_APPEND = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it():
    cmd = ["status"]
    getattr(cmd, "append")(str(REPO / "led"))
    return subprocess.run(cmd, capture_output=True, text=True)
'''

RED_GLOBALS_APPEND = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

cmd = ["status"]


def run_it():
    globals()["cmd"].append(str(REPO / "led"))
    return subprocess.run(cmd, capture_output=True, text=True)
'''

RED_STARRED_LITERAL = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it():
    return subprocess.run([*[str(REPO / "led")], "status"], capture_output=True, text=True)
'''

RED_IFEXP_JOIN = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it(flag=True):
    return subprocess.run([str(REPO / ("led" if flag else "pickup")), "status"],
                          capture_output=True, text=True)
'''

RED_FSTRING_STR_CALL = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it():
    return subprocess.run([f"{str(REPO)}/led", "status"], capture_output=True, text=True)
'''

GREEN_MUTATED_NON_SENSITIVE = '''\
import subprocess


def run_it():
    cmd = ["git", "status"]
    cmd += ["-v"]
    return subprocess.run(cmd, capture_output=True, text=True)
'''

# --- FINAL ROUND specimens (maintainer disposition, ledger row 1316: DEMOTE the gate's claims,
# fix cheap findings that are a genuine scan-loop widening, disclose the rest). Each below is a
# lap-5 finding closed as a one-line widening -- see gate module docstring's FINAL ROUND section
# for the honest inventory of what stays disclosed instead. -----------------------------------

RED_KWARG_ARGV = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it():
    return subprocess.run(args=[str(REPO / "led"), "finding", "hello"],
                          capture_output=True, text=True)
'''

RED_PARTIAL_KWARG_ARGV = '''\
import functools
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it():
    runner = functools.partial(subprocess.run, args=[str(REPO / "led"), "finding"],
                                capture_output=True, text=True)
    return runner()
'''

RED_BARE_LEGACY_PICKUP = '''\
import subprocess


def run_it():
    return subprocess.run(["legacy/pickup", "status"], capture_output=True, text=True)
'''


def _run_gate(*paths: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(GATE), *[str(p) for p in paths]],
                           capture_output=True, text=True)


def main() -> int:
    failures: list[str] = []

    # --- GREEN: the real fixture tree -------------------------------------------------------
    r = _run_gate()
    ok = r.returncode == 0
    check("GREEN-real-tree", ok, f"exit={r.returncode}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}",
          failures)

    with tempfile.TemporaryDirectory(prefix="fixture-deployment-pin-guard-") as tmp:
        tmp_path = Path(tmp)

        specimens = {
            "red-repo-led.py": (RED_REPO_LED, True, "led"),
            "red-repo-legacy-pickup.py": (RED_REPO_LEGACY_PICKUP, True, "pickup"),
            "red-environ-mutation.py": (RED_ENVIRON_MUTATION, True, None),
            "green-scratch-scoped.py": (GREEN_SCRATCH_SCOPED, False, None),
            "green-local-env-dict.py": (GREEN_LOCAL_ENV_DICT, False, None),
            # --- reviewer-demonstrated evasions, this fix-round -----------------------------
            "red-os-system.py": (RED_OS_SYSTEM, True, None),
            "red-shell-true.py": (RED_SHELL_TRUE, True, None),
            "red-libexec-led.py": (RED_LIBEXEC_LED, True, "led"),
            "red-environ-update.py": (RED_ENVIRON_UPDATE, True, None),
            "red-environ-alias.py": (RED_ENVIRON_ALIAS, True, None),
            "red-wrapper-indirected.py": (RED_WRAPPER_INDIRECTED, True, "led"),
            "green-waived-led.py": (GREEN_WAIVED_LED, False, None),
            # --- fix-round-2 evasions (fresh-context strengthened-tier review, BLOCKED 26c7c48) -
            "red-waiver-blanket.py": (RED_WAIVER_BLANKET, True, "led"),
            "red-subscript-mutation.py": (RED_SUBSCRIPT_MUTATION, True, "led"),
            "red-append-built-argv.py": (RED_APPEND_BUILT_ARGV, True, "led"),
            "red-os-path-join.py": (RED_OS_PATH_JOIN, True, "led"),
            "red-joinpath.py": (RED_JOINPATH, True, "led"),
            "red-partial-argv.py": (RED_PARTIAL_ARGV, True, "led"),
            "red-semicolon-shared-waiver.py": (RED_SEMICOLON_SHARED_WAIVER, True, "led"),
            # --- fix-round-3 specimens (fresh-context strengthened-tier review, BLOCKED 8821dff) -
            "red-opaque-before-sensitive.py": (RED_OPAQUE_BEFORE_SENSITIVE, True, "provable"),
            "red-alias-append.py": (RED_ALIAS_APPEND, True, "provable"),
            "red-branch-order-dissolved.py": (RED_BRANCH_ORDER_DISSOLVED, True, "provable"),
            # --- fix-round-4 specimens (fresh-context strengthened-tier review of round 3;
            # census fail-closed) -- one per lap-4 finding, see module docstring above. ----------
            "red-chained-assign.py": (RED_CHAINED_ASSIGN, True, "provable"),
            "red-tuple-unpack.py": (RED_TUPLE_UNPACK, True, "provable"),
            "red-for-target.py": (RED_FOR_TARGET, True, "provable"),
            "red-tuple-swap.py": (RED_TUPLE_SWAP, True, "provable"),
            "red-walrus.py": (RED_WALRUS, True, "provable"),
            "red-bare-led.py": (RED_BARE_LED, True, "led"),
            "red-bare-dot-led.py": (RED_BARE_DOT_LED, True, "led"),
            "red-getattr-append.py": (RED_GETATTR_APPEND, True, "provable"),
            "red-globals-append.py": (RED_GLOBALS_APPEND, True, "provable"),
            "red-starred-literal.py": (RED_STARRED_LITERAL, True, "led"),
            "red-ifexp-join.py": (RED_IFEXP_JOIN, True, "led"),
            "red-fstring-str-call.py": (RED_FSTRING_STR_CALL, True, "led"),
            "green-mutated-non-sensitive.py": (GREEN_MUTATED_NON_SENSITIVE, False, None),
            # --- FINAL ROUND (demotion, ledger row 1316): lap-5 findings closed as pure
            # scan-loop/roster widenings, no new analysis machinery. ---------------------------
            "red-kwarg-argv.py": (RED_KWARG_ARGV, True, "led"),
            "red-partial-kwarg-argv.py": (RED_PARTIAL_KWARG_ARGV, True, "led"),
            "red-bare-legacy-pickup.py": (RED_BARE_LEGACY_PICKUP, True, "pickup"),
        }
        for fname, (content, should_be_bad, verb) in specimens.items():
            spath = tmp_path / fname
            spath.write_text(content, encoding="utf-8")
            r = _run_gate(spath)
            is_bad = r.returncode != 0
            label = fname.rsplit(".", 1)[0].upper().replace("-", "_")
            ok = is_bad == should_be_bad
            detail = f"exit={r.returncode}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"
            if should_be_bad and verb:
                ok = ok and (verb in r.stdout)
            check(label, ok, detail, failures)
            if should_be_bad and ok:
                print("  " + r.stdout.strip().splitlines()[-1])

    print()
    if failures:
        print(f"FAILURES ({len(failures)}):")
        for f in failures:
            print(f"\n!! {f}")
        return 1
    print("ALL CASES OK -- fixture-deployment-pin-guard both polarities, zero residue")
    return 0


def check(label: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"{'GREEN' if ok else 'RED  '} {'ok' if ok else 'FAIL'}: {label}")
    if not ok:
        failures.append(f"{label}:\n{detail}")


if __name__ == "__main__":
    raise SystemExit(main())
