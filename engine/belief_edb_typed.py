#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-22T01:36:42Z
#   last-change: 2026-07-22T01:36:42Z
#   contributors: 1fa3ab69/main
# <<< PROVENANCE-STAMP <<<

"""belief_edb_typed -- the s53 TYPED-ARM EDB reader for the belief substrate (design/
FABLE-BELIEF-SUBSTRATE-SPEC.md v2 Delta B1, ledger rows 1914/1919). Split out of
engine/belief_edb.py into its own sibling module SOLELY because that file's ADR-0007 max_lines
ratchet baseline (394 lines pre-v2, under the 400-line ceiling so it carried no grandfathered
headroom) had no room for a second arm's worth of code -- the SAME "split, never grow past the
ceiling" idiom belief_edb.py's own docstring already documents for its own split out of
engine/ledger_edb.py. Reported as a spec-conformance/idiom deviation (ADR-0013 renegotiation-
upward), not a silent choice: see the build report.

Exports `typed_belief_facts(t, rel) -> list[str]`, called from belief_edb.py::export_belief()'s
`has_typed` branch and appended to its own EdbExport.facts -- both arms feed the SAME fact
families (belief/1, belief_polarity/2, belief_basis/2, belief_has_universe/1, belief_has_witness/1,
belief_edge/3, belief_subject/2), so engine/lp/ledger_belief.lp needs no edit of its own.

No parse-time validation is needed here -- s53's kernel CHECKs/triggers already refused a
malformed row at WRITE time, so every kind='belief' row read here is well-formed by construction
(the s44 model_identity_attested typed-arm precedent, engine/ledger_edb.py::export_defeat()'s
own `has_typed` block, which performs the identical "just read and emit" posture).

Lazy imports are banned (CLAUDE.md)."""
from __future__ import annotations

from ledger_edb import Target, _atom


def typed_belief_facts(t: Target, rel: str) -> tuple[list[str], int]:
    """Read every kind='belief' row on `t` and return (facts, count) in the belief_edb.py fact
    vocabulary. `belief_premises` (bigint[]) is read via a SEPARATE unnest() query -- never a raw
    array-literal parse (the psql -tA rendering of an array is a second text convention this
    module refuses to grow a second parser for)."""
    facts: list[str] = []
    n_typed = 0
    for rid_s, polarity, basis, universe, witness, source_s, subject_s, contests_s, concurs_s in t.rows(
            f"SELECT id, belief_polarity, belief_basis, belief_universe, belief_witness, "
            f"belief_source, belief_subject, belief_contests, belief_concurs "
            f"FROM {rel} WHERE kind = 'belief' ORDER BY id;"):
        rid = int(rid_s)
        n_typed += 1
        facts.append(f"belief({rid}).")
        facts.append(f"belief_polarity({rid},{_atom(polarity)}).")
        facts.append(f"belief_basis({rid},{_atom(basis)}).")
        if universe is not None and universe.strip():
            facts.append(f"belief_has_universe({rid}).")
        if witness is not None and witness.strip():
            facts.append(f"belief_has_witness({rid}).")
        if source_s:
            facts.append(f"belief_edge({rid},source,{int(source_s)}).")
        if subject_s:
            facts.append(f"belief_subject({rid},{int(subject_s)}).")
        if contests_s:
            facts.append(f"belief_edge({rid},contests,{int(contests_s)}).")
        if concurs_s:
            facts.append(f"belief_edge({rid},concurs,{int(concurs_s)}).")
    for rid_s, pid_s in t.rows(
            f"SELECT id, unnest(belief_premises) FROM {rel} "
            f"WHERE kind = 'belief' AND belief_premises IS NOT NULL ORDER BY id;"):
        facts.append(f"belief_edge({int(rid_s)},premise,{int(pid_s)}).")
    return facts, n_typed
