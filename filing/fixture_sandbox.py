"""fixture_sandbox -- the Python-side twin of libexec/autoharn/_fixture_sandbox_preamble.sh
(design/FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §2/§3, ledger rows 1237-1248/1315/
1316/1325). The repo-root verb surface mixes shell entry points (led/judge/pickup/audit/
distance-to-clean/doctor/asof-export/verify-chain/migrate, plus ./autoharn itself) and Python
ones (attest-tags, autoharn-service) -- a POSIX-sh script cannot source a Python module and a
Python module cannot be `.`-sourced by sh, so "one shared preamble" is necessarily TWO files, one
per language, kept behaviorally identical (same env vars, same exit code, same teaching text
shape) rather than one script every entry point can literally share. This module is that Python
half; every Python repo-root verb entry point calls `check()` at the top of `main()`, before
doing anything else.

THE GUARANTEE (unchanged from the sh sibling): enforcement does not depend on recognizing a
fixture's call shape -- it depends on the called thing (this repo's own root verbs) refusing
whenever AUTOHARN_FIXTURE_SANDBOX is set in its own environment. Environment inheritance
propagates the marker through any process tree a fixture starts, however indirectly spawned.

SCOPE: this module is imported by libexec/autoharn/attest-tags, libexec/autoharn-service, and
(added 2026-07-26, work item courier-umbrella-rebase, ledger rows 1369/1370 -- ADR-0005 Rule 8,
appended rather than rewritten) libexec/autoharn/courier -- never by anything under
bootstrap/templates/ (spec §5: "not a change to any world's verbs"). A scratch world's own shim
execs a *.tmpl file directly and never imports this module at all, so it structurally cannot
refuse under the marker -- the same choke-point argument the sh preamble's own header makes.

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import os
import sys

# Distinct, documented exit code -- byte-identical to the sh preamble's own
# FIXTURE_SANDBOX_REFUSED_EXIT, kept as one canonical value referenced from both language halves.
FIXTURE_SANDBOX_REFUSED_EXIT = 21


def check(what: str) -> None:
    """Call at the top of a repo-root Python verb's main(), before any other work. Exits the
    process (never returns) if the marker is set with no non-empty waiver reason; prints the
    waiver's reason and returns normally if a non-empty waiver is present; is a silent no-op if
    the marker is not set at all (the overwhelmingly common case -- an ordinary operator
    invocation, or this builder's own read-only reads, never carries this env var)."""
    if not os.environ.get("AUTOHARN_FIXTURE_SANDBOX"):
        return

    waiver = os.environ.get("AUTOHARN_FIXTURE_SANDBOX_WAIVER", "")
    if not waiver:
        print(
            f"autoharn: REFUSED -- fixture sandbox marker set (AUTOHARN_FIXTURE_SANDBOX=1) and "
            f"{what} just attempted this repo's OWN root verb surface against the REAL "
            f"deployment (design/FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md, ledger rows "
            f"1237-1248: a fixture reaching a live deployment.json this way is the leak class "
            f"this refusal forecloses -- every argv spelling, not just the ones a static census "
            f"happens to enumerate).\n\n"
            f"  Two sanctioned exits:\n"
            f"    1. Drive a SCRATCH world instead (bootstrap/new-project.sh --new-world, or any "
            f"other scaffolded deployment) -- its own ./led/./judge/etc. never reach this check "
            f"(they exec bootstrap/templates/*.tmpl directly, never this repo's ./autoharn "
            f"dispatcher or libexec/autoharn/*), so nothing here blocks it.\n"
            f"    2. If this call site has a REVIEWED, use-site reason to touch a repo-root verb "
            f"directly, set AUTOHARN_FIXTURE_SANDBOX_WAIVER=\"<reason>\" (a non-empty string) in "
            f"this call's own environment. The reason is echoed into this verb's output, so the "
            f"run's transcript carries the justification at the use site -- an EMPTY reason is "
            f"refused exactly like no waiver at all.\n\n"
            f"  Nothing was touched. Exit code {FIXTURE_SANDBOX_REFUSED_EXIT} (distinct, documented).",
            file=sys.stderr,
        )
        sys.exit(FIXTURE_SANDBOX_REFUSED_EXIT)

    print(f"autoharn: fixture-sandbox WAIVER in effect for {what} -- reason:", file=sys.stderr)
    print(f"  {waiver}", file=sys.stderr)
