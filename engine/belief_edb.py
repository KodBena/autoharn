#!/usr/bin/env python3
"""belief_edb -- the belief-substrate EDB producer (design/FABLE-BELIEF-SUBSTRATE-SPEC.md §2/§3,
ratified ledger rows 1914/1919; v2 typed arm split into engine/belief_edb_typed.py, same reason
below). A SEPARATE sibling module rather than folded into engine/ledger_edb.py -- the ADR-0007
max_lines gate's ratchet baseline on ledger_edb.py (729 lines) has no headroom for this
producer, and every other EDB producer this tree has grown since ledger_edb.py's own defeat-arm
precedent already lives in its own sibling file. Reported (ADR-0013 renegotiation-upward), never
silent: see the build report.

Exports export_belief() -- belief/1, belief_polarity/2, belief_basis/2, belief_has_universe/1,
belief_has_witness/1, belief_edge/3 (premise|source|contests|concurs), belief_subject/2 -- for
engine/lp/ledger_belief.lp and its SQL twin (engine/belief_floor.py). row_actor/2 and
agent_class/2 are DELIBERATELY NOT re-emitted here (reused from export_defeat, spec §2.2) --
every belief row is an ordinary actor-bearing ledger row, so
ledger_edb.export_defeat()'s row_actor/2 loop already covers it; LAYERS["belief"] stacks the
defeat layer underneath for this reason.

Lazy imports are banned (CLAUDE.md)."""
from __future__ import annotations

import re

from belief_edb_typed import typed_belief_facts
from ledger_edb import Capability, EdbExport, Target, _atom, resolve

# ===========================================================================
# THE BELIEF-SUBSTRATE v1 EDB (design/FABLE-BELIEF-SUBSTRATE-SPEC.md §2, ratified ledger rows
# 1914/1919). Exports belief/1, belief_polarity/2, belief_basis/2, belief_has_universe/1,
# belief_has_witness/1, belief_edge/3 (premise|source|contests|concurs), belief_subject/2 for
# engine/lp/ledger_belief.lp and its SQL twin (engine/belief_floor.py). row_actor/2 and
# agent_class/2 are DELIBERATELY NOT re-emitted here (spec §2.2's own fact-family table marks
# them "reused from export_defeat") -- every belief row is an ordinary actor-bearing ledger row,
# so export_defeat()'s existing row_actor/2 loop already covers it; LAYERS["belief"] stacks the
# defeat layer underneath for exactly this reason (§2.2 item 3).
#
# THE V1 GRAMMAR (spec §2.1). A v1 belief is a `kind='decision'` row (written through the
# standing write path, `led decision ...`) whose trimmed statement starts with the literal
# `belief[`. Grammar:
#
#   belief[<polarity>] basis=<basis> [universe={<surface>; <surface>; ...}]
#       [witness=<token>[,<token>...]] [source=row:<id>]
#       [premises=row:<id>[,row:<id>...]] [subject=row:<id>]
#       [contests=row:<id>] [concurs=row:<id>]
#       :: <proposition text, free prose, to end of statement>
#
# AMBIGUITY RESOLVED, REPORTED (never silently chosen -- CLAUDE.md engineering-responsibility
# corollary + this commission's own instruction): the spec's bracket notation does not itself
# pin down whether the optional fields may appear in ANY order or must appear in the CANONICAL
# order the grammar block lists them in. This builder reads the grammar as FIXED-ORDER --
# exactly the "s44 model-attestation idiom" the spec's own §2.1 header cites, which is itself a
# fixed positional segment grammar -- because (a) `universe={...}` may itself contain embedded
# whitespace/semicolons, so a free-reordering tokenizer would need brace-tracking AND a
# then-genuinely-ambiguous "where does the field section end and the free-prose proposition
# begin" scan, while a single fixed-order left-to-right consumption resolves both together with
# one pass and no backtracking; and (b) it is the ONLY reading both this Python parser and the
# independent SQL floor twin (engine/belief_floor.py, per ADR-0000 I6 -- no shared code path
# with the ASP producer, and no shared code path with THIS parser either, the export_defeat
# precedent) can implement byte-identically without secretly agreeing on a shared tokenizer.
# An out-of-canonical-order field (e.g. `contests=` before `witness=`) is REFUSED as malformed
# (falls through to the "no `::` separator found" branch below, since the out-of-order token is
# never consumed) -- named here so a reader can see exactly what "malformed" catches.
#
# `<polarity>` in {universal, existential}, `<basis>` in {observed, derived, testimony, assumed},
# closed, exact lowercase (the s44 casing posture -- never case-folded). The obligation truth
# table below is IDENTICAL to the one §3.1 freezes for the v2 CHECKs -- this is the "v1's honest
# weakness ... bind at parse time, not write time" spec names (§2.1): a malformed v1 belief can
# exist in the ledger and is refused only when this exporter reads it, never silently.
BELIEF_FAMILIES = ("belief",)

_BELIEF_POLARITY_VOCAB = frozenset({"universal", "existential"})
_BELIEF_BASIS_VOCAB = frozenset({"observed", "derived", "testimony", "assumed"})
_BELIEF_PREFIX = "belief["
_BELIEF_HEADER_RE = re.compile(r"^belief\[([^\]]*)\]\s*(.*)$", re.DOTALL)
_BELIEF_BASIS_RE = re.compile(r"^basis=(\S+)\s*(.*)$", re.DOTALL)
# Canonical field order (the resolved ambiguity above); each entry (key, pattern) is tried
# EXACTLY ONCE, in this order, against the progressively-consumed remainder -- a field that
# never matches its slot (because it is absent, or because it appears out of order) is simply
# not collected, and any leftover token that was never consumed fails the final `::` check.
_BELIEF_OPTIONAL_FIELDS = [
    ("universe", re.compile(r"^universe=\{([^}]*)\}\s*(.*)$", re.DOTALL)),
    ("witness", re.compile(r"^witness=(\S+)\s*(.*)$", re.DOTALL)),
    ("source", re.compile(r"^source=(\S+)\s*(.*)$", re.DOTALL)),
    ("premises", re.compile(r"^premises=(\S+)\s*(.*)$", re.DOTALL)),
    ("subject", re.compile(r"^subject=(\S+)\s*(.*)$", re.DOTALL)),
    ("contests", re.compile(r"^contests=(\S+)\s*(.*)$", re.DOTALL)),
    ("concurs", re.compile(r"^concurs=(\S+)\s*(.*)$", re.DOTALL)),
]
_BELIEF_SEPARATOR_RE = re.compile(r"^::\s*(.*)$", re.DOTALL)
_BELIEF_LEADING_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=")
_ROW_TOKEN_RE = re.compile(r"^row:(\d+)$")
_ARTIFACT_TOKEN_RE = re.compile(r"^artifact:([0-9a-f]{64})$")


class BeliefParseError(RuntimeError):
    """Raised on a malformed v1 belief statement (spec §2.1) -- a loud refusal of the WHOLE
    export, never a skip-and-continue (ADR-0002), naming the row id and the violated
    obligation -- the exact DefeatParseError discipline this class mirrors."""


def _parse_v1_belief_fields(rid: int, stmt: str) -> dict[str, str] | None:
    """Parse ONE candidate row's statement, TEXT-LEVEL ONLY (no DB access -- existence/edge
    checks are export_belief()'s job, since they need the target). Returns a fields dict
    (keys: polarity, basis, and any present optional field's raw value; 'proposition_len' for
    the P-7-shaped text-stays-home rule) for a well-formed v1 candidate, or None if `stmt` is
    not a belief candidate at all (does not start with `belief[` -- not malformed, just a
    different kind of row, counted by the caller as a non-candidate). Raises BeliefParseError
    on any malformation of a genuine candidate."""
    s = stmt.strip()
    if not s.startswith(_BELIEF_PREFIX):
        return None
    m = _BELIEF_HEADER_RE.match(s)
    if not m:
        raise BeliefParseError(
            f"row {rid}: belief policy: 'belief[' has no closing ']' -- malformed header: {s[:80]!r}")
    polarity, rest = m.group(1), m.group(2)
    if polarity not in _BELIEF_POLARITY_VOCAB:
        raise BeliefParseError(
            f"row {rid}: belief policy: belief_polarity {polarity!r} outside "
            f"{sorted(_BELIEF_POLARITY_VOCAB)} (exact lowercase, never case-folded)")
    bm = _BELIEF_BASIS_RE.match(rest)
    if not bm:
        raise BeliefParseError(
            f"row {rid}: belief policy: expected 'basis=<value>' immediately after "
            f"'belief[{polarity}]' (mandatory, always the first field): {rest[:60]!r}")
    fields: dict[str, str] = {"polarity": polarity, "basis": bm.group(1)}
    rest = bm.group(2)
    if fields["basis"] not in _BELIEF_BASIS_VOCAB:
        raise BeliefParseError(
            f"row {rid}: belief policy: belief_basis {fields['basis']!r} outside "
            f"{sorted(_BELIEF_BASIS_VOCAB)} (exact lowercase, never case-folded)")
    for key, pattern in _BELIEF_OPTIONAL_FIELDS:
        mm = pattern.match(rest)
        if mm:
            fields[key], rest = mm.group(1), mm.group(2)
    sm = _BELIEF_SEPARATOR_RE.match(rest)
    if not sm:
        km = _BELIEF_LEADING_KEY_RE.match(rest)
        if km:
            raise BeliefParseError(
                f"row {rid}: belief policy: field {km.group(1)!r} is unrecognized, duplicated, "
                f"or out of the canonical field order (universe, witness, source, premises, "
                f"subject, contests, concurs) -- garbled grammar: {rest[:80]!r}")
        raise BeliefParseError(
            f"row {rid}: belief policy: no ' :: <proposition>' separator found after the field "
            f"section -- garbled grammar: {rest[:80]!r}")
    proposition = sm.group(1).strip()
    if not proposition:
        raise BeliefParseError(f"row {rid}: belief policy: empty proposition after '::'")
    fields["proposition_len"] = str(len(proposition))

    # ---- obligation truth table (spec §2.1 / §3.1's CHECK spellings, mirrored at parse time) --
    has_universe, has_witness = "universe" in fields, "witness" in fields
    has_source, has_premises = "source" in fields, "premises" in fields
    if polarity == "universal":
        if not has_universe or not fields["universe"].strip():
            raise BeliefParseError(
                f"row {rid}: belief policy: belief[universal] requires a non-empty "
                f"universe={{...}} (the enumerated quantification universe is the claim's own "
                f"evidence, ledger row 1887 rule 1) -- missing")
        if has_witness:
            raise BeliefParseError(
                f"row {rid}: belief policy: witness= is forbidden on belief[universal] "
                f"(a universal claim is grounded by its universe, never a witness)")
    else:  # existential
        if has_universe:
            raise BeliefParseError(
                f"row {rid}: belief policy: universe= is forbidden on belief[existential] "
                f"(the universe obligation belongs to universal claims only)")
        if fields["basis"] == "observed" and (not has_witness or not fields["witness"].strip()):
            raise BeliefParseError(
                f"row {rid}: belief policy: witness token resolves to nothing -- a finding "
                f"without its witness is treated exactly as ADR-0005 Rule 9 treats a verdict "
                f"without its artifact: as nothing. belief[existential] basis=observed requires "
                f"a non-empty witness=... -- missing")
    if fields["basis"] == "testimony":
        if not has_source or not fields["source"].strip():
            raise BeliefParseError(
                f"row {rid}: belief policy: basis=testimony requires source=row:<id> (the "
                f"source record the testimony relays) -- missing")
    elif has_source:
        raise BeliefParseError(
            f"row {rid}: belief policy: source= is forbidden except on basis=testimony "
            f"(relaying another's verdict as one's own observation is unrepresentable by "
            f"construction -- testimony is the only basis with a source edge)")
    if fields["basis"] == "derived":
        if not has_premises or not [p for p in fields["premises"].split(",") if p.strip()]:
            raise BeliefParseError(
                f"row {rid}: belief policy: basis=derived requires a non-empty "
                f"premises=row:<id>[,row:<id>...] -- missing")
    elif has_premises:
        raise BeliefParseError(
            f"row {rid}: belief policy: premises= is forbidden except on basis=derived")
    return fields


def _belief_check_row_tokens(rid: int, field: str, raw: str, existing_ids: set[int],
                             allow_artifact: bool, artifact_hashes: set[str]) -> list[int]:
    """Validate a comma-separated token list (witness/premises/source/subject/contests/concurs
    all share this shape) against the closed row:/artifact: token grammar + existence (the s48
    extraction/verification mechanism's v1 mirror), returning the resolved row: ids (artifact:
    tokens carry no row id). Raises BeliefParseError naming the row and the dangling token,
    teach-text fixed in substance per spec §3.2 (the write-time trigger's own wording, mirrored
    here at parse time)."""
    ids: list[int] = []
    for tok in (t.strip() for t in raw.split(",")):
        if not tok:
            continue
        rm = _ROW_TOKEN_RE.match(tok)
        if rm:
            rowid = int(rm.group(1))
            if rowid not in existing_ids:
                raise BeliefParseError(
                    f"row {rid}: belief policy: {field} token {tok!r} names no existing ledger "
                    f"row -- a finding without its witness is treated exactly as ADR-0005 Rule 9 "
                    f"treats a verdict without its artifact: as nothing. Record the evidence "
                    f"first, then the belief.")
            ids.append(rowid)
            continue
        am = _ARTIFACT_TOKEN_RE.match(tok) if allow_artifact else None
        if am:
            if am.group(1) not in artifact_hashes:
                raise BeliefParseError(
                    f"row {rid}: belief policy: {field} token {tok!r} resolves to no artifact in "
                    f"the s51 store -- record the evidence first (led artifact put), then the "
                    f"belief.")
            continue
        raise BeliefParseError(
            f"row {rid}: belief policy: {field} token {tok!r} is neither row:<digits> nor "
            f"artifact:<64-hex> -- bad token, garbled grammar")
    return ids


def _belief_universe_tokens_check(rid: int, raw: str, existing_ids: set[int],
                                  artifact_hashes: set[str]) -> None:
    """universe={...} tokens are semicolon-separated; a row:/artifact: SHAPED token inside it is
    existence-checked exactly like witness (a universe token is the claim's own evidence);
    free-text surface names are legal and uninspected (spec §2.1 -- "a universe names territory,
    not only rows")."""
    for tok in (t.strip() for t in raw.split(";")):
        if not tok:
            continue
        rm = _ROW_TOKEN_RE.match(tok)
        if rm and int(rm.group(1)) not in existing_ids:
            raise BeliefParseError(
                f"row {rid}: belief policy: universe token {tok!r} names no existing row -- an "
                f"enumerated universe is the claim's own evidence (ledger row 1887 rule 1: the "
                f"surface list derives from where the system PRODUCES artifacts of that kind, "
                f"not from where the auditor happens to stand); cite rows/artifacts that exist, "
                f"or name the surface in prose.")
            continue
        am = _ARTIFACT_TOKEN_RE.match(tok)
        if am and am.group(1) not in artifact_hashes:
            raise BeliefParseError(
                f"row {rid}: belief policy: universe token {tok!r} names no existing artifact -- "
                f"an enumerated universe is the claim's own evidence; cite rows/artifacts that "
                f"exist, or name the surface in prose.")


def export_belief(name: str) -> EdbExport:
    """Export the belief-substrate EDB (design/FABLE-BELIEF-SUBSTRATE-SPEC.md §2/§3, ledger rows
    1914/1919), capability-gated (I12). BOTH arms harvested where present (export_defeat()'s
    v1/s44 has_typed dual-arm precedent): v1 statement-prefix rows and, where the world carries
    s53, typed kind='belief' rows (engine/belief_edb_typed.py) -- both feed the SAME fact
    families, so ledger_belief.lp needs no edit for an s53 world. Actor-typed same as
    row_actor (contests/concurs need a real principal id)."""
    t = resolve(name)
    exp = EdbExport(target=t)
    rel = t.rel()

    has_statement = t.has_col("statement")
    has_actor = t.has_col("actor") and t.scalar(
        f"SELECT data_type FROM information_schema.columns WHERE table_schema='{t.schema}' "
        f"AND table_name='ledger' AND column_name='actor';") in ("bigint", "integer", "smallint")
    has_typed = t.has_col("belief_polarity")
    belief_capable = (has_statement or has_typed) and has_actor
    reason = ("statement/belief_polarity + integer-typed actor -- emitted" if belief_capable else
             "no statement/belief_polarity column, or actor not integer-typed -- capability absent")
    exp.capabilities.append(Capability("belief", produced=belief_capable, capable=belief_capable, reason=reason))
    if not belief_capable:
        return exp
    if has_typed:
        typed_facts, n_typed = typed_belief_facts(t, rel)
        exp.facts.extend(typed_facts)
        exp.counts["belief(typed-arm)"] = n_typed
    has_artifact = t.has_relation(f"{t.kern}.artifact")
    artifact_hashes: set[str] = set()
    if has_artifact:
        artifact_hashes = {h for (h,) in t.rows(f"SELECT hash FROM {t.kern}.artifact ORDER BY hash;")}
    existing_ids = {int(i) for (i,) in t.rows(f"SELECT id FROM {rel} ORDER BY id;")}
    actor_of: dict[int, int] = {}
    for i, a in t.rows(f"SELECT id, actor FROM {rel} WHERE actor IS NOT NULL ORDER BY id;"):
        actor_of[int(i)] = int(a)
    sup_pairs = [(int(a), int(b)) for a, b in t.rows(
        f"SELECT id, supersedes FROM {rel} WHERE supersedes IS NOT NULL ORDER BY id;")]
    # transitive supersession closure (the sup_star/superseded reading ledger_tnow.lp/
    # ledger_floor.py's _base_ctes already compute in SQL; small-ledger Python closure here is
    # the same math, needed at PARSE time for the contest/concurs target-currency checks).
    direct: dict[int, set[int]] = {}
    for a, b in sup_pairs:
        direct.setdefault(a, set()).add(b)
    reach: dict[int, set[int]] = {a: set(bs) for a, bs in direct.items()}
    changed = True
    while changed:
        changed = False
        for a, bs in list(reach.items()):
            add: set[int] = set()
            for b in bs:
                add |= reach.get(b, set())
            if not add <= bs:
                reach[a] = bs | add
                changed = True
    superseded: set[int] = set()
    for bs in reach.values():
        superseded |= bs
    belief_candidate_ids = {int(i) for (i,) in t.rows(
        f"SELECT id FROM {rel} WHERE btrim(statement) LIKE 'belief[%' ORDER BY id;")}

    n_candidates = n_parsed = 0
    for rid_s, stmt in t.rows(
            f"SELECT id, statement FROM {rel} WHERE btrim(statement) LIKE 'belief[%' ORDER BY id;"):
        rid = int(rid_s)
        n_candidates += 1
        fields = _parse_v1_belief_fields(rid, stmt)  # raises BeliefParseError; never None here
        assert fields is not None                    # (the candidate query already filtered)
        n_parsed += 1
        exp.facts.append(f"belief({rid}).")
        exp.facts.append(f"belief_polarity({rid},{_atom(fields['polarity'])}).")
        exp.facts.append(f"belief_basis({rid},{_atom(fields['basis'])}).")
        if "universe" in fields:
            _belief_universe_tokens_check(rid, fields["universe"], existing_ids, artifact_hashes)
            exp.facts.append(f"belief_has_universe({rid}).")
        if "witness" in fields and fields["witness"].strip():
            _belief_check_row_tokens(rid, "witness", fields["witness"], existing_ids,
                                     allow_artifact=True, artifact_hashes=artifact_hashes)
            exp.facts.append(f"belief_has_witness({rid}).")
        if "premises" in fields:
            for pid in _belief_check_row_tokens(rid, "premises", fields["premises"], existing_ids,
                                                allow_artifact=False, artifact_hashes=artifact_hashes):
                exp.facts.append(f"belief_edge({rid},premise,{pid}).")
        if "source" in fields:
            sids = _belief_check_row_tokens(rid, "source", fields["source"], existing_ids,
                                            allow_artifact=False, artifact_hashes=artifact_hashes)
            if len(sids) != 1:
                raise BeliefParseError(
                    f"row {rid}: belief policy: source= names a SINGLE row:<id> "
                    f"(grammar: 'source=row:<id>'), got {len(sids)} tokens -- bad token, "
                    f"garbled grammar")
            exp.facts.append(f"belief_edge({rid},source,{sids[0]}).")
        if "subject" in fields:
            sjids = _belief_check_row_tokens(rid, "subject", fields["subject"], existing_ids,
                                             allow_artifact=False, artifact_hashes=artifact_hashes)
            if len(sjids) != 1:
                raise BeliefParseError(
                    f"row {rid}: belief policy: subject= names a SINGLE row:<id> "
                    f"(grammar: 'subject=row:<id>'), got {len(sjids)} tokens -- bad token, "
                    f"garbled grammar")
            exp.facts.append(f"belief_subject({rid},{sjids[0]}).")
        for edge_name, teach_self, teach_stale in (
                ("contests",
                 "belief policy: contest is the cross-principal doubt act -- you cannot contest "
                 "your own belief (revise it instead: supersede it with your new position, s31). "
                 "A contest against its own holder is a revision wearing a challenge's clothes.",
                 "is no longer in force; contesting settled history defeats nothing (the "
                 "record beats memory -- contest the current belief, or write your own)."),
                ("concurs",
                 "belief policy: self-concurrence is not corroboration -- s17's honesty, one "
                 "edge over.",
                 "is no longer in force; concurring with settled history corroborates "
                 "nothing (write against the current belief).")):
            if edge_name not in fields:
                continue
            targets = _belief_check_row_tokens(rid, edge_name, fields[edge_name], existing_ids,
                                               allow_artifact=False, artifact_hashes=artifact_hashes)
            if len(targets) != 1:
                raise BeliefParseError(
                    f"row {rid}: belief policy: {edge_name}= names a SINGLE row:<id> "
                    f"(grammar: '{edge_name}=row:<id>'), got {len(targets)} tokens -- bad token, "
                    f"garbled grammar")
            for tgt in targets:
                if tgt not in belief_candidate_ids:
                    raise BeliefParseError(
                        f"row {rid}: belief policy: {edge_name} target row {tgt} is not itself a "
                        f"v1 belief (no 'belief[' prefix) -- {edge_name} must name a belief.")
                if tgt in superseded:
                    raise BeliefParseError(
                        f"row {rid}: belief policy: row {tgt} {teach_stale}")
                tgt_actor, this_actor = actor_of.get(tgt), actor_of.get(rid)
                if tgt_actor is not None and this_actor is not None and tgt_actor == this_actor:
                    raise BeliefParseError(f"row {rid}: {teach_self}")
                exp.facts.append(f"belief_edge({rid},{edge_name},{tgt}).")
    exp.counts["belief(v1-candidates)"] = n_candidates
    exp.counts["belief(v1-parsed)"] = n_parsed
    return exp

