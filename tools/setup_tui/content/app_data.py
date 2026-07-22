#!/usr/bin/env python3
"""tools/setup_tui/content/app_data.py -- the DATA half of `tools/setup_tui/app.py`'s intro
banner + guarantee-envelope + dry-run-notice copy (design/FABLE-SETUP-TUI-TYPED-UI-SPEC.md §3,
law/adr/0012 P10). `app.py`'s `_intro` references these by name; nothing here is computed from
runtime state (the whole block is fixed, static teaching copy shown identically every run)."""
from __future__ import annotations

INTRO_HEADING = "autoharn setup — guided wizard (tools/setup_tui)"

INTRO_DRIVER_LINE = (
    "Driver of existing verbs only: every action below shows the exact command it runs and "
    "streams that command's real output. If this process dies mid-flow, you can finish by hand "
    "from what was printed."
)

# The guarantee envelope (design/FABLE-SETUP-TUI-PURE-CORE-SPEC.md §2.6, commission ledger rows
# 1823 point 2 / 1825): stated here in the SAME capability terms the spec itself uses -- a
# structural property of the pure-core restructure, not an aspiration. Restated (not duplicated --
# ADR-0012 P1) in user-guide/USER-GPG-TRUST-LAYER-FAQ.md's setup entry and in
# user-guide/USER-RECIPES-FAQ.md's setup entry, both citing this same spec section as the one home
# for the claim's substance.
GUARANTEE_ENVELOPE_HEADING = (
    "Guarantee envelope (structural, per design/FABLE-SETUP-TUI-PURE-CORE-SPEC.md §2.6):"
)
GUARANTEE_ENVELOPE_PARAGRAPHS: tuple[str, ...] = (
    "  BEFORE commit: nothing to clean up. Every screen only decides and queues -- kill this "
    "process at any point before the final confirm and the destination, your keyring, and every "
    "ledger are untouched (verified before/after, WPC1/WPC3).",
    "  DURING commit: per-act atomicity (each write/command/background-start either fully "
    "happens or fully doesn't) plus a durable commit journal in the destination naming which "
    "step runs next -- a mid-commit death resumes cleanly on re-entry, or finishes by hand from "
    "the journal and the streamed output above it (WPC4).",
    "  NOT claimed: whole-flow atomicity across Postgres + filesystem + GPG + a background "
    "process. Decide-then-commit shrinks the exposure window from the whole session to the "
    "commit phase; it does not eliminate it.",
)

DRY_RUN_NOTICE = (
    "*** --dry-run: NOTHING below is destructive or externally visible. Every act is computed "
    "and shown (exact argv, exact file paths + a content summary, exact led rows) but NOT "
    "performed -- no file written outside this process, no database act, no led write, no "
    "process started, no port bound. Read-only probes (preflight, connection checks, the "
    "pg_hba read) stay live. The closing checklist renders these as WOULD-DO. ***"
)

# Backward-navigation hint (design/FABLE-SETUP-TUI-NAVIGATION-SPEC.md, observation (e)) --
# stated once at the intro, per that spec's §3.
NAV_HINT = (
    "Type '<' at any prompt (scripted answers file: '<BACK>') to go back to the previous "
    "screen -- your answers there are offered again. Available until the closing "
    "checklist screen's own commit confirm."
)
