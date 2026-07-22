#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-22T01:49:01Z
#   last-change: 2026-07-22T01:49:01Z
#   contributors: 1fa3ab69/main
# <<< PROVENANCE-STAMP <<<

"""tools/setup_tui/content/config_file_data.py -- the DATA half of the config-file feature
(design/FABLE-SETUP-TUI-CONFIG-FILE-SPEC.md, ledger row 1944; law/adr/0012 P10 "data is not
code"). This module holds ONLY the closed schema table `tools/setup_tui/config_file.py` loads
and validates against -- no parsing/validation LOGIC, no I/O, so a reviewer can read "what keys
does a config file carry" as a table, not by tracing control flow.

SCHEMA maps `"<section>.<key>"` (the exact dotted path a TOML config uses -- `[section]` table,
`key = ...` inside it) to its declared TYPE:
  "bool"        -- true/false
  "str"         -- a string (may be the empty string, meaning "not set")
  "list_str"    -- an array of strings
  "list_table"  -- an array of inline tables ({name=..., ...} rows); the per-row field names
                   are documented at each entry's own comment (config_seam.py is the ONE place
                   that reads/writes those row shapes -- ADR-0012 P1).

Grouped by SECTION, in flow order (spec §1: "grouped by screen section"). Every key here is a
DECISION identifier the wizard's own screens produce -- never a world name, a destination path,
or anything machine-/instance-specific (spec §1's exclusion clause); there is no key in this
table for "world" or "dest" AT ALL, by construction, so the general unknown-key refusal already
covers someone trying to sneak either into a config file.
"""
from __future__ import annotations

HEADER_KEYS = {"config_format", "produced_by", "source"}

SCHEMA: dict[str, str] = {
    # --- substrate (screen_substrate) ---------------------------------------------------------
    "substrate.run": "bool",
    "substrate.path": "str",          # "existing" | "dedicated"
    "substrate.host": "str",
    "substrate.db": "str",
    "substrate.role": "str",          # dedicated path only
    "substrate.subnets": "str",       # dedicated path only, comma-separated CIDR

    # --- fork_target (screen_fork_target) -----------------------------------------------------
    "fork_target.governed_extend": "bool",
    "fork_target.governed_extensions": "str",

    # --- rehearsal (screen_rehearsal) ----------------------------------------------------------
    "rehearsal.run": "bool",

    # --- birth (screen_birth) -------------------------------------------------------------------
    "birth.run": "bool",
    "birth.project_name": "str",      # blank = defaults to the --world value

    # --- principals_authority (screen_principals_authority) -------------------------------------
    "principals_authority.run": "bool",
    # register: [{name, agent_class, purpose}, ...]
    "principals_authority.register": "list_table",
    # competences: [{name, activity, band, basis}, ...]
    "principals_authority.competences": "list_table",
    # relations: [{subject, relation, object}, ...]
    "principals_authority.relations": "list_table",

    # --- signed_genesis (screen_signed_genesis) --------------------------------------------------
    "signed_genesis.run": "bool",
    "signed_genesis.commission_statement": "str",

    # --- boundary (screen_boundary) ---------------------------------------------------------------
    "boundary.configure": "bool",
    "boundary.start_now": "bool",

    # --- observability (screen_observability) -------------------------------------------------------
    "observability.run": "bool",
    "observability.otelcol": "bool",
    "observability.otel_watch": "bool",

    # --- hydration (screen_hydration) -----------------------------------------------------------------
    "hydration.run": "bool",
    "hydration.fork_provenance": "bool",
    "hydration.fork_provenance_statement": "str",
    "hydration.role_charters": "bool",
    "hydration.durable_decisions": "list_str",   # slugs from durable_decisions.CATALOG to adopt
    "hydration.adopt_adrs": "list_str",          # ADR numbers ("0001", ...) to adopt

    # --- explicitly excluded (documented here, never a real key -- ADR-0002 rule 4, the
    # negative-space table): "world" and "dest"/"destination" never appear at any level -- they
    # are the wizard's CLI parameters (--world / <dest-dir>), not config content (spec §1).
}

# Every "*.run"/"*.configure" gate key that governs whether its whole section is even asked --
# used by config_seam.py's synthesizer to decide whether to walk a section at all. Data, not
# logic: the actual walk order lives in config_seam.py, which mirrors screens.py's own sequence.
SECTION_GATE_KEY = {
    "substrate": "substrate.run",
    "fork_target": None,  # always walked -- the destination itself is a CLI parameter
    "rehearsal": "rehearsal.run",
    "birth": "birth.run",
    "principals_authority": "principals_authority.run",
    "signed_genesis": "signed_genesis.run",
    "boundary": "boundary.configure",
    "observability": "observability.run",
    "hydration": "hydration.run",
}
