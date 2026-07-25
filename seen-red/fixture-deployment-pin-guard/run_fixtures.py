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
