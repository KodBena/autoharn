#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-22T01:37:10Z
#   last-change: 2026-07-22T01:37:10Z
#   contributors: 1fa3ab69/main
# <<< PROVENANCE-STAMP <<<

"""belief_floor_typed -- the s53 TYPED-ARM SQL-floor reader for the belief substrate (design/
FABLE-BELIEF-SUBSTRATE-SPEC.md v2 Delta B1, ledger rows 1914/1919). Split out of
engine/belief_floor.py into its own sibling module for the SAME ADR-0007 max_lines headroom
reason engine/belief_edb_typed.py exists beside engine/belief_edb.py (that file's own docstring
gives the full reasoning) -- reported as a spec-conformance/idiom deviation (ADR-0013
renegotiation-upward), not a silent choice: see the build report.

Lazy imports are banned (CLAUDE.md)."""
from __future__ import annotations

from ledger_edb import Target


def typed_arm_rows(t: Target) -> list[tuple]:
    """The s53 TYPED-ARM rows, in the SAME tuple shape engine/belief_floor.py's
    `_parse_and_validate` returns (id, actor, polarity, basis, has_universe, has_witness,
    premises_raw, source_raw, subject_raw, contests_raw, concurs_raw) -- so the caller can simply
    CONCATENATE both arms' row lists and reuse every downstream assembly line unchanged (the
    v1/s44 dual-arm precedent: both arms feed the SAME shape). No parse-time validation is needed
    here -- s53's CHECKs/triggers already refused a malformed row at WRITE time, so every
    kind='belief' row read here is well-formed by construction."""
    rel = t.rel()
    rows = t.rows(
        f"SELECT id, actor, belief_polarity, belief_basis, "
        f"(belief_universe IS NOT NULL AND btrim(belief_universe) <> ''), "
        f"(belief_witness IS NOT NULL AND btrim(belief_witness) <> ''), "
        f"coalesce((SELECT array_to_string(array_agg('row:' || p), ',') "
        f"           FROM unnest(belief_premises) p), ''), "
        f"coalesce('row:' || belief_source::text, ''), "
        f"coalesce('row:' || belief_subject::text, ''), "
        f"coalesce('row:' || belief_contests::text, ''), "
        f"coalesce('row:' || belief_concurs::text, '') "
        f"FROM {rel} WHERE kind = 'belief' ORDER BY id;")
    out: list[tuple] = []
    for (rid, actor, polarity, basis, has_u, has_w, prem, src, subj, cont, conc) in rows:
        out.append((int(rid), int(actor) if actor else None, polarity, basis,
                   has_u == "t", has_w == "t", prem, src, subj, cont, conc))
    return out
