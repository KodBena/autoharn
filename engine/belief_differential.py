#!/usr/bin/env python3
"""belief_differential -- the 'belief' layer's differential glue (design/
FABLE-BELIEF-SUBSTRATE-SPEC.md §2.2/§3.4, ratified ledger rows 1914/1919), split out of
engine/ledger_differential.py into its own sibling module SOLELY because that file's
ADR-0007 max_lines ratchet baseline (529 lines) had no headroom for a third full layer's worth
of glue -- reported as a spec-conformance/idiom deviation (ADR-0013 renegotiation-upward), not
a silent choice: see the build report. `run_sql_belief`/`belief_layer_capability`/
`belief_edb_text` are called from ledger_differential.py's own layer_capability()/
run_layer_differential()/main(), mirroring the 'work'/'defeat' layers' inline shape there as
closely as the line budget allows.

CIRCULAR IMPORT, RESOLVED BY ORDERING (not a lazy import -- CLAUDE.md's ban is about
function-body-deferred imports, not module-level placement): this module imports several names
FROM ledger_differential (ProducerRun, DerivationRecord, the two hash/version helpers, HERE);
ledger_differential imports THIS module back. Both imports are module-level and unconditional;
the cycle resolves because ledger_differential's own `import belief_differential` statement is
placed AFTER the names this module needs are already defined in ledger_differential's body
(Python registers a module in sys.modules before executing its body, so a partial module with
those attributes already set is what this module's `from ledger_differential import ...` sees).

Lazy imports are banned (CLAUDE.md)."""
from __future__ import annotations

import ledger_differential as ld
from belief_edb import BeliefParseError, export_belief
from belief_floor import BELIEF_PREDS, belief_capable, belief_floor_atoms
from ledger_edb import DefeatParseError, export, export_defeat


def belief_edb_text(name: str) -> str:
    """The combined EDB text for the belief layer: export() + export_defeat() (row_actor/
    agent_class/model_defeated inputs, spec §2.2's "reused from export_defeat") +
    export_belief(). Raises BeliefParseError/DefeatParseError on a malformed row."""
    return (export(name).edb_text() + "\n" + export_defeat(name).edb_text()
            + "\n" + export_belief(name).edb_text())


def belief_layer_capability(t) -> tuple[bool, str]:
    if not belief_capable(t):
        return False, ("target has no `statement` column, or `actor` is not integer-typed -- "
                       "the 'belief' layer has no substrate here, capability absent, "
                       "not record-empty")
    return True, ""


def run_sql_belief(name: str, edb_text: str) -> "ld.ProducerRun":
    """The SQL floor for the 'belief' layer: belief_floor_atoms, restricted to BELIEF_PREDS.
    QUARANTINES on a capability-absent target (F49) and on a malformed v1 belief statement (the
    SQL-side raise, caught here, never a silent skip)."""
    t = ld.resolve(name)
    if not belief_capable(t):
        return ld.ProducerRun("sql:floor(belief)",
                              quarantine="target has no `statement` column, or `actor` is not "
                                          "integer-typed -- the 'belief' layer has no substrate "
                                          "here, capability absent, not record-empty")
    try:
        atoms = belief_floor_atoms(name)
        atoms = {a for a in atoms if a.split("(", 1)[0] in BELIEF_PREDS}
    except Exception as e:  # noqa: BLE001 -- a malformed v1 belief (spec §2.1) raises SQL-side
        return ld.ProducerRun("sql:floor(belief)", quarantine=f"SQL belief floor failed: {type(e).__name__}: {e}")
    rec = ld.DerivationRecord(
        engine="postgres", version=ld._pg_version(t.db),
        config=["belief_floor.py::belief_floor_atoms"],
        input_basis=f"live-db rows read directly ({t.db}.{t.schema}.ledger)",
        input_hash=ld._ledger_snapshot_hash(name),
        program_hash=ld._sha((ld.HERE / "belief_floor.py").read_text(encoding="utf-8")),
        output_hash=ld._sha("\n".join(sorted(atoms))), target=name, ts=ld._now())
    return ld.ProducerRun("sql:floor(belief)", atoms=atoms, record=rec)


def run_belief_layer(name: str, paths: list, preds: frozenset) -> tuple:
    """The whole 'belief' layer differential leg (both producers), called from
    ledger_differential.run_layer_differential's belief branch -- kept here, not inline there,
    for the SAME max_lines headroom reason this module exists at all. Returns (asp, sql)
    ProducerRuns, both quarantined identically on a malformed row or capability-absent target
    (never a partial result -- P-5's "both producers fail identically")."""
    try:
        edb_text = belief_edb_text(name)
    except Exception as e:  # noqa: BLE001 -- BeliefParseError/DefeatParseError (P-5) or capability-absent
        qr = (f"malformed v1 belief/attestation statement: {e}"
             if isinstance(e, (BeliefParseError, DefeatParseError))
             else f"EDB export failed: {type(e).__name__}: {e}")
        return (ld.ProducerRun("asp:clingo", quarantine=qr),
               ld.ProducerRun("sql:floor(belief)", quarantine=qr))
    asp = ld.run_asp(name, edb_text, programs=paths)
    if asp.quarantine is None:
        asp.atoms = {a for a in asp.atoms if a.split("(", 1)[0] in preds}
    return asp, run_sql_belief(name, edb_text)
