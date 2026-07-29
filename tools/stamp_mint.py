#!/usr/bin/env python3
"""stamp_mint -- the ONE shared implementation of the interception-stamp minting algorithm
(work item human-countersign-stamp-path, ledger rows 619/667/672). Extracted so `autoharn
stamp-run` (tools/stamp_run.py) does not re-implement the HMAC scheme hooks/stamp_intercept.py
already carries -- ADR-0012 P1, "one home per mechanism".

TWO-HOME INTERIM, DISCLOSED HONESTLY (not swept under the rug): hooks/stamp_intercept.py is,
as of this file's creation, the CURRENT second home of this exact algorithm (secret load +
`HMAC(secret, session|agent|ts)` over SHA-256 + the per-invocation correlation UUID + the
PGOPTIONS GUC assembly). CLAUDE.md's standing rule -- "never modify hooks/ or a user project
while a live session runs there" -- forbids touching that live-exec'd hook in this pass, so this
module is a BYTE-FAITHFUL copy of the minting core (`_load_secret`, the `hmac.new(...)` call,
the `uuid.uuid4()` mint, the `-c app.vendor_*` GUC string), not yet a shared import the hook
itself uses. THE FOLD-IN -- hooks/stamp_intercept.py deletes its own copy of this logic and
imports this module instead, becoming the single real home -- is this build's disclosed NEXT
TOUCH on the hook stack, filed as follow-up work, not attempted here. Whoever does that fold-in:
this docstring is the marker to update once it lands (the "second home" framing above becomes
stale the moment the hook actually imports this file).

WHY A SHARED MODULE AT ALL, RATHER THAN LIVING INSIDE tools/stamp_run.py: hooks/
stamp_intercept.py's own eventual fold-in needs an import target that carries ONLY the pure
minting primitives (no argv parsing, no deployment/secret-path resolution, no os.exec -- none of
that is meaningful inside a PreToolUse hook, which mints into a PGOPTIONS string it splices into
someone else's command text rather than exec'ing anything itself). Keeping this module minimal
and side-effect-free (no filesystem/network beyond `load_secret`'s own file read, no argv, no
process control) means both consumers -- the hook's eventual import and stamp_run.py's own
`os.execvpe` path -- can share it without either dragging in machinery the other does not need.

Stdlib-only, top-of-file imports (gates/no_lazy_imports.py, the lazy-import gate, applies).
"""
from __future__ import annotations

import hashlib
import hmac
import time
import uuid
from pathlib import Path


def load_secret(path: str) -> bytes | None:
    """Byte-identical to hooks/stamp_intercept.py's own `_load_secret`: None for ANY invalid
    condition -- missing, unreadable, empty, or non-hex content -- never raises. An empty-but-
    present file is treated the SAME as missing (never silently accepted as a valid zero-length
    HMAC key)."""
    if not path or not Path(path).is_file():
        return None
    try:
        text = Path(path).read_text().strip()
        if not text:
            return None
        return bytes.fromhex(text)
    except (ValueError, OSError):
        # OSError: an existing-but-unreadable secret file (perms, I/O). ValueError: malformed hex.
        return None


def mint(secret: bytes, session: str, agent: str, ts: int | None = None) -> dict[str, object]:
    """Compute one vendor-stamp, byte-identical to hooks/stamp_intercept.py's own `main()`:
    `HMAC(secret, f"{session}|{agent}|{ts}")` over SHA-256 (hex digest -- matches the kernel's
    `stamp_valid()` SQL side, which recomputes the same `hmac(convert_to(session||'|'||agent||
    '|'||ts::text,'utf8'), secret, 'sha256')` and requires the presented ts be within +-300s of
    `now()`, kernel/lineage/s17-stamp-mechanism.sql's own freshness window), plus a fresh
    `uuid4()` per-invocation correlation token (app.vendor_invocation -- captured by the s23
    kernel column, verification-inert, never part of the HMAC). `ts` defaults to the current
    wall clock; a caller never needs to pass it except in a fixture that wants a fixed,
    reproducible stamp."""
    if ts is None:
        ts = int(time.time())
    mac = hmac.new(secret, f"{session}|{agent}|{ts}".encode(), hashlib.sha256).hexdigest()
    invocation = str(uuid.uuid4())
    return {"session": session, "agent": agent, "ts": ts, "hmac": mac, "invocation": invocation}


def pgoptions(stamp: dict[str, object]) -> str:
    """Format a minted stamp into the PGOPTIONS value hooks/stamp_intercept.py exports --
    byte-identical GUC names, in the same order, so a caller of this function produces a stamp
    a live-deployed kernel (which only knows about these five GUC names) validates identically
    regardless of which of the two current homes minted it."""
    return (f"-c app.vendor_session={stamp['session']} -c app.vendor_agent={stamp['agent']} "
            f"-c app.vendor_ts={stamp['ts']} -c app.vendor_hmac={stamp['hmac']} "
            f"-c app.vendor_invocation={stamp['invocation']}")
