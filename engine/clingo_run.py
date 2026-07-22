"""clingo_run — the shared clingo-CLI subprocess runner (one home, framework-free).

The clingo binding is NOT in the venv (B-autoharn-fit s.0: "subprocess-from-Python today"),
so every ASP consumer shells out to the `clingo` CLI and parses its JSON. That runner is a
cross-cutting fact with ONE home here (ADR-0012 P1/P3): ``contra_asp`` (the R-NEG/R-FUNC/R-NUM
logic layer over the spaCy ``Claim`` substrate) and ``kb_why`` (the R-WHY WHY-ledger over the
KB rows) both import it — and crucially ``kb_why`` must NOT reach it THROUGH ``contra_asp``,
because ``contra_asp`` imports the spaCy extraction stack at module top (``extract`` /
``contra_detect``): a KB-only module pulling spaCy would be a lying dependency footprint
(CLAUDE.md's honest-footprint rule). Splitting the runner out is the ``span_store`` idiom — a
framework-free leaf so each importer's top-of-file imports stay honest.

IMPORT-LIGHT: stdlib only (``shutil`` / ``subprocess`` / ``json`` / ``pathlib``). No spaCy,
no z3, no psycopg — the runner is a pure shell over the CLI.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Final

# The default subprocess wall-clock bound, denominated in seconds. Kept as the ONE named
# constant (ADR-0012 P1/F: no bare literal strewn at the call site) rather than a magic 120
# inline; INTERFACE §7 flags that the eventual budget-carried form derives this from the
# caller's deadline. `run_clingo(..., timeout=None)` selects it, so the default path is
# bit-identical to the pre-extraction `timeout=120` literal it replaces.
DEFAULT_TIMEOUT_S: Final[float] = 120.0

# The CLOSED vocabulary of clingo `Result` values that mean the solver ran to a DEFINITE
# verdict (ADR-0008 classification / ADR-0012 P8 illegal-states-unrepresentable at the
# runner boundary). Membership -- not the exit code -- is the success gate:
#   - SATISFIABLE / UNSATISFIABLE  : a genuine verdict. UNSAT is an empty MODEL SET, which
#                                    is categorically different from a solver that could not run.
#   - "OPTIMUM FOUND"              : clingo's success verdict under --opt-mode=opt (the
#                                    `opt=True` path, contra_asp's R-NEG repair). It is NOT
#                                    "SATISFIABLE", so a literal SAT/UNSAT-only guard would
#                                    wrongly reject every optimisation run -- verified against
#                                    clingo 5.8.0. This is where the fidelity review's
#                                    "not SATISFIABLE/UNSATISFIABLE" wording is read for its
#                                    SPIRIT (reject the non-run), not its letter (which omits
#                                    the opt verdict and would break a live consumer).
# Anything ELSE -- notably "UNKNOWN", which clingo emits as VALID JSON with an empty model on
# a GROUNDING/PARSE error or an interrupted search -- is NO RESULT: returning [] for it would
# bank a broken run as an empty derivation (the silent-non-run hazard F49 / ADR-0015 Rule 3).
_SOLVED_RESULTS: Final[frozenset[str]] = frozenset(
    {"SATISFIABLE", "UNSATISFIABLE", "OPTIMUM FOUND"}
)


def quote_term(s: str) -> str:
    r"""A clingo double-quoted string term, escaping the only two metacharacters (\\ and ")
    so any slug/key is a legal term regardless of content. The framework-free home for clingo
    term formatting (contra_asp keeps its own spaCy-side ``_quote``; this is kb_why's)."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def clingo_bin() -> str:
    exe = shutil.which("clingo")
    if exe is None:  # ADR-0002: fail loud, never silently no-op
        raise RuntimeError("clingo CLI not found on PATH (need clingo 5.8.x)")
    return exe


def run_clingo(
    program_files: list[Path],
    edb_text: str,
    opt: bool = False,
    *,
    timeout: "float | None" = None,
) -> list[str]:
    """Run clingo over ``program_files`` + the EDB (fed on stdin) and return the shown atoms
    of the relevant model as strings. For a stratified program (exactly one stable model) that
    is ``Witnesses[0]``; for the optimisation (``opt=True``) the OPTIMUM is clingo's LAST
    reported witness. JSON output (``--outf=2``) is parsed — no brittle text scraping.

    ``timeout`` (seconds) bounds the subprocess; ``None`` ⇒ ``DEFAULT_TIMEOUT_S`` (the
    behaviour of the bare ``timeout=120`` literal this runner replaces, now a named lever)."""
    tmo = DEFAULT_TIMEOUT_S if timeout is None else timeout
    cmd = [clingo_bin(), *[str(p) for p in program_files], "-", "--outf=2"]
    if opt:
        # enumerate to the optimum; clingo prints improving models, last is optimal.
        cmd += ["--opt-mode=opt"]
    proc = subprocess.run(
        cmd, input=edb_text, capture_output=True, text=True, timeout=tmo
    )
    # clingo exit codes are a bitmask (10=SAT, 20=UNSAT, 30=SAT+INTERRUPT...); a non-zero
    # code is NORMAL. A parse/grounding error prints to stderr with code 1/65.
    try:
        out = json.loads(proc.stdout)
    except json.JSONDecodeError as e:  # ADR-0002: surface the real clingo error
        raise RuntimeError(
            f"clingo produced no JSON (exit {proc.returncode}): {proc.stderr.strip()}"
        ) from e
    result = out.get("Result", "")
    # DURABLE FIX (clingo-fidelity review F/§0, item 5): a grounding or parse error emits
    # VALID JSON with an empty "UNKNOWN" model, so the witness-walk below would return [] --
    # indistinguishable from a legitimately empty finding set, banking a broken run as a
    # derivation. Gate on the CLOSED success vocabulary, not on the (bitmask) exit code:
    # anything outside _SOLVED_RESULTS is NO RESULT and RAISES (ADR-0002 fail-loud /
    # ADR-0015 Rule 3), so every consumer (kb_why, contra_asp, the scratch runners, the
    # marriage differential) is protected, and the empty-EDB hole closes in the same guard.
    if result not in _SOLVED_RESULTS:
        raise RuntimeError(
            f"clingo did not reach a definite result (Result={result!r}, exit "
            f"{proc.returncode}) -- a grounding/parse error emits valid JSON with an empty "
            f"UNKNOWN model, which is NO RESULT, not an empty derivation (ADR-0015 Rule 3). "
            f"stderr: {proc.stderr.strip()}"
        )
    if result == "UNSATISFIABLE":
        return []
    calls = out.get("Call", [])
    if not calls:
        return []
    witnesses = calls[-1].get("Witnesses", [])
    if not witnesses:
        return []
    return list(witnesses[-1].get("Value", []))
