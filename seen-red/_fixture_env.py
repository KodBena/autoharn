#!/usr/bin/env python3
"""_fixture_env -- the ONE home for "which Postgres host does a seen-red fixture driver connect
to," shared by every seen-red/*/run_fixtures.py (and sibling driver, e.g. red-specimen.py) so the
resolution logic exists once, not once per driver (~35 hand-copies of the same
`PGHOST = "192.168.122.1"` literal, found via a whole-tree grep after the product surface itself
was fixed the same way in filing/pghost_resolve.py).

Before this module, every seen-red driver baked the maintainer's own LAN host in as an executable
default. A fresh checkout with no env var and no deployment.json would silently try to connect to
someone else's machine, or (worse, for a *fixture* whose job is to prove a claim) silently report a
false pass/fail instead of loudly refusing to run at all.

This module is a thin, fixture-scoped wrapper over filing/pghost_resolve.py (the product surface's
own resolver): same precedence (HARNESS_PGHOST, then EPISTEMIC_PGHOST, then this checkout's
deployment.json, else a loud SystemExit naming both), reused rather than reimplemented -- ONE
resolver, not two that could drift. filing/ is this repo's established shared lower layer (the same
one engine/targets.py and instruments/ledger_target.py already reach via a file-relative sys.path
insert); this module lives in seen-red/ itself, one directory above every driver that imports it
(`from _fixture_env import fixture_pghost` works unmodified for every `seen-red/<case>/run_fixtures.py`
once seen-red/ is on sys.path -- each driver adds its own parent's parent, i.e. seen-red/, the same
file-relative insert pattern, so no driver needs its own copy of the filing/ hookup either).

Refusal is loud and names the fix (ADR-0002): SystemExit's message, raised from
filing/pghost_resolve.py, names EPISTEMIC_PGHOST/HARNESS_PGHOST AND deployment.json explicitly, and
exits nonzero. A driver that calls fixture_pghost() at module scope (matching every driver's own
existing PGHOST = "..." top-of-file pattern) turns "no host resolved" into an immediate, teaching,
nonzero-exit SKIP for that fixture -- never a silent pass, never psycopg's own cryptic
connection-refused text.

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent  # seen-red/
_REPO_ROOT = _HERE.parent
sys.path.insert(0, str(_REPO_ROOT / "filing"))

import pghost_resolve  # filing/pghost_resolve.py, the ONE home -- never a literal host default


def fixture_pghost() -> str:
    """Resolve the Postgres host for a seen-red fixture driver. Same precedence every driver
    already used for its OWN env-var checks where it had any (HARNESS_PGHOST, then
    EPISTEMIC_PGHOST), then this checkout's deployment.json, else a loud SystemExit (nonzero exit,
    names both) -- never a silent default, never a bare connection error."""
    return pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST")
