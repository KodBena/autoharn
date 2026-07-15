#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-12T07:53:01Z
#   last-change: 2026-07-12T07:53:01Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""ordering_edb -- the ASP-producer EDB exporter for engine/lp/ordering_violations.lp
(design/ORCH-SPEC-RESOURCE-REGISTRY.md §5 stage 2). A SEPARATE, ledger-only EDB from
engine/contemp_edb.py's (Part 3's): this checker reasons over pure id-order plus the
`constraint:` convention text, never a journal or an invocation token, so it needs none of
contemp_edb.py's anchor/window machinery -- pulling that in just to reach three of its facts
would tie a pure-id-order checker to an unrelated capability surface (ADR-0012 P2/P3: a port
takes only what it needs, not the whole neighbor's internals).

FACT FAMILIES EMITTED:
  work_opened(Slug,RowId).                s22 raw ledger rows (kind='work_opened'). Read from
  work_closed(Slug,Resolution,RowId).      the RAW `<schema>.ledger` table, never `ledger_current`
  work_depends(Dependent,Antecedent,RowId) -- work_items.lp's own header: these kinds are NEVER
                                             whole-row superseded/amended by design.
  constraint_precedes(SlugA,SlugB,RowId)   parsed from `kind='decision'` rows whose statement
                                            matches the already-shipped `constraint: precedes
                                            <slug>...` grammar (design/USER-BLESSED-TABLE-
                                            TEMPLATE.md). Read from `ledger_current` (the
                                            supersession-filtered view) -- UNLIKE the work_*
                                            families above, §5's own text says a constraint: row
                                            is "supersedable" via the ordinary supersedes edge.
                                            A `precedes A B C` row is expanded PAIRWISE into a
                                            chain: (A,B,RowId), (B,C,RowId), ... -- see
                                            engine/lp/ordering_violations.lp's header for why a
                                            chain is the executor's scope decision here.
  constraint_precedes_unparsed(RowId)      a `constraint:` row that does not parse as the
                                            documented grammar (bad relation word, or fewer than
                                            two slugs) -- never silently dropped.
  constraint_excludes_deferred(RowId)      a well-formed `constraint: excludes ...` row --
                                            RECOGNIZED, not checked this pass (named residue).
  capable(work_items)                      emitted iff this target's schema carries the s22
                                            work_* columns (`work_slug` present) -- the SAME
                                            capability gate engine/lp/preamble_ordering.lp's own
                                            F4-F7/F10 `pre_s22` reason uses.
  any_row(RowId)                           every ledger row's own id, regardless of kind -- the
                                            "some activity is on record at all" grounding fact
                                            the forced-undecidable escape hatch needs (mirrors
                                            engine/lp/preamble_ordering.lp's own row_id/1).

TEXT STAYS HOME (design rule, ledger_edb.py rule 1 / work_items.lp's own header): the raw
`statement` text of a `constraint:` row is parsed HERE, in Python, before it ever reaches the
EDB -- only the parsed SlugA/SlugB/RowId (or the unparsed/deferred flag) cross into the .lp text,
exactly as `refs` is parsed into `row_refs_row/2` before crossing in engine/contemp_edb.py.

Read-only. Lazy imports banned (top-of-file only)."""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field

from ledger_edb import Target, resolve

_CONSTRAINT_RE = re.compile(r"^\s*constraint:\s*(\S+)\s+(.*)$")
_RELATIONS = ("precedes", "excludes")


def _quote(s: str) -> str:
    """A clingo double-quoted string term -- local, standalone (see this module's own docstring:
    an independent copy is cheap and keeps this producer's code path genuinely separate from the
    SQL floor's, matching engine/ledger_edb.py's own `_atom()` precedent of NOT importing
    engine/clingo_run.quote_term here)."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def parse_constraint(statement: str) -> tuple[str, list[str]] | None:
    """Parse one `constraint:`-prefixed decision statement per design/USER-BLESSED-TABLE-
    TEMPLATE.md's already-shipped grammar (`constraint: <RELATION> <slug-1> <slug-2>
    [<slug-n>...]`, RELATION in {precedes, excludes}, >=2 slugs). Returns (relation, [slug,...])
    for a well-formed row, else None (malformed -- the caller flags this loudly, never drops it).
    Exposed at module level (not a nested closure) so engine/ordering_floor.py's SQL-side
    parser -- a SEPARATE, independent re-implementation in SQL regex -- can be tested against
    this one's fixtures without the two ever sharing a code path at RUN time."""
    m = _CONSTRAINT_RE.match(statement)
    if not m:
        return None
    relation, rest = m.group(1), m.group(2)
    if relation not in _RELATIONS:
        return None
    slugs = rest.split()
    if len(slugs) < 2:
        return None
    return relation, slugs


@dataclass
class OrderingEdbExport:
    target: Target
    facts: list[str] = field(default_factory=list)
    capable_work_items: bool = False
    counts: dict[str, int] = field(default_factory=dict)

    def edb_text(self) -> str:
        head = [f"% ==== ordering EDB: target '{self.target.name}' -> {self.target.db}.{self.target.rel()}",
                f"% ==== capable(work_items): {self.capable_work_items}",
                f"% ==== counts: {self.counts}"]
        return "\n".join(head) + "\n" + "\n".join(self.facts) + "\n"


def export(target_name: str) -> OrderingEdbExport:
    """Export the ordering-violations EDB for `target_name` (read-only)."""
    t = resolve(target_name)
    rel = t.rel()
    exp = OrderingEdbExport(target=t)

    has_work_cols = t.has_col("work_slug")
    exp.capable_work_items = has_work_cols
    if has_work_cols:
        exp.facts.append("capable(work_items).")

    n_any = 0
    for (rid,) in t.rows(f"SELECT id FROM {rel} ORDER BY id;"):
        exp.facts.append(f"any_row({int(rid)}).")
        n_any += 1
    exp.counts["any_row"] = n_any

    if has_work_cols:
        n = 0
        for slug, rid in t.rows(
                f"SELECT work_slug, id FROM {rel} WHERE kind='work_opened' ORDER BY id;"):
            exp.facts.append(f"work_opened({_quote(slug)},{int(rid)}).")
            n += 1
        exp.counts["work_opened"] = n

        n = 0
        for slug, resolution, rid in t.rows(
                f"SELECT work_slug, work_resolution, id FROM {rel} "
                f"WHERE kind='work_closed' ORDER BY id;"):
            exp.facts.append(f"work_closed({_quote(slug)},{_quote(resolution)},{int(rid)}).")
            n += 1
        exp.counts["work_closed"] = n

        n = 0
        for dependent, antecedent, rid in t.rows(
                f"SELECT work_slug, work_depends_on, id FROM {rel} "
                f"WHERE kind='work_depends_on' ORDER BY id;"):
            exp.facts.append(f"work_depends({_quote(dependent)},{_quote(antecedent)},{int(rid)}).")
            n += 1
        exp.counts["work_depends"] = n

    # constraint: rows -- read from the supersession-filtered view (§5: "supersedable"), never
    # the raw table these five families above deliberately use (work_items.lp's own header: those
    # kinds are NEVER whole-row superseded by design -- the two families obey different
    # supersession semantics, so they are read from different relations, honestly).
    has_current = t.has_relation(f"{t.schema}.ledger_current")
    n_prec = n_unparsed = n_excl = 0
    if has_current:
        curr_rel = f"{t.schema}.ledger_current"
        for rid, statement in t.rows(
                f"SELECT id, statement FROM {curr_rel} WHERE kind='decision' "
                f"AND statement ~ '^[[:space:]]*constraint:' ORDER BY id;"):
            parsed = parse_constraint(statement)
            if parsed is None:
                exp.facts.append(f"constraint_precedes_unparsed({int(rid)}).")
                n_unparsed += 1
                continue
            relation, slugs = parsed
            if relation == "precedes":
                for a, b in zip(slugs, slugs[1:]):
                    exp.facts.append(f"constraint_precedes({_quote(a)},{_quote(b)},{int(rid)}).")
                    n_prec += 1
            else:  # excludes -- recognized, NOT checked this pass (named residue, see header)
                exp.facts.append(f"constraint_excludes_deferred({int(rid)}).")
                n_excl += 1
    exp.counts["constraint_precedes_edges"] = n_prec
    exp.counts["constraint_precedes_unparsed"] = n_unparsed
    exp.counts["constraint_excludes_deferred"] = n_excl

    return exp


def main(argv: list[str] | None = None) -> int:
    names = (argv if argv is not None else sys.argv[1:]) or ["toy"]
    for name in names:
        exp = export(name)
        print(exp.edb_text())
        print(f"% counts: {exp.counts}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
