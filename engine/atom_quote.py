#!/usr/bin/env python3
"""atom_quote -- THE single shared home for the bare-vs-quoted clingo-term rendering rule used by
BOTH producers of the entitlement-scope floor (design/FABLE-ENGINE-ENTITLEMENT-SCOPE-ASP-TWIN-
SPEC.md §1a: "the text terms (Surface, Mode) MUST be rendered through a floor twin of _atom()'s
bare-vs-quoted branch ... the quote logic is factored to ONE shared home both producers import
rather than duplicated"). engine/ledger_edb.py's export_entitlement() (its s70 addition) and
engine/ledger_floor.py's entitlement_floor_atoms() both import THIS module for their Surface/Mode
text arguments (scope_bound/2, may_read_surface/2, scope_disclosure/2) -- never a second,
hand-kept copy of the character-class rule.

WHY A SHARED HOME HERE, WHEN EVERY OTHER PRODUCER PAIR IN THIS CODEBASE DELIBERATELY DUPLICATES
(I6, ADR-0000 INDEP -- see engine/ledger_floor.py's own `_wi_quote` docstring for the general
rule and its stated reason): the `_wi_quote` INCIDENT is the named hazard this spec's own text
cites -- one prior asymmetry between two independently-authored copies of the identical
bare-vs-quoted decision (`ledger_edb._atom` vs `ledger_floor._wi_quote`) left the 'work' layer
unable to AGREE on ANY world, for ANY target, for an entire lineage window, before it was caught.
That was a real, live-witnessed failure of the "trivial helper, safe to duplicate" argument for
THIS SPECIFIC rule (a character-class test, not the derivation logic under test). Rather than risk
authoring a THIRD hand-kept copy of the same rule for the s70 scope predicates, this spec's own
text asks for the one deliberate exception: an ENCODING rule (never the differential's own
derivation logic) both new-family producers import from one place, so the two can never drift
apart on this one decision again.

Does NOT touch or replace `ledger_edb._atom` / `ledger_floor._wi_quote` (or the three sibling
`_atom_quote`/`_quote` copies in ordering_floor.py/preamble_floor.py/contemp_floor.py) -- those
existing, independently-authored mirror pairs are UNCHANGED; each one's own precedent stands for
its own EDB family. This module is imported ONLY for the s70 scope-binding families this spec
adds.

Lazy imports banned (CLAUDE.md); this module has none."""
from __future__ import annotations

import re

_BARE_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def is_bare_safe(v: str) -> bool:
    """True iff `v` is a safe bare clingo constant: non-empty, starts with a lowercase letter, and
    contains only lowercase letters/digits/underscores -- the ONE rule both renderers below apply
    identically (matches `ledger_edb._atom`'s own bare-identifier test byte-for-byte)."""
    return bool(v) and _BARE_RE.match(v) is not None


def atom_term(v: str) -> str:
    """A clingo term for `v`: a bare constant when `is_bare_safe`, else a quoted string
    (backslash-then-quote escaping, matching `ledger_edb._atom`'s own order); empty/None/blank
    renders as the bare constant `none` -- `ledger_edb._atom`'s own empty-string case, reproduced
    here so export_entitlement's s70 additions and entitlement_floor_atoms share ONE encoding
    decision rather than two independently-authored copies of it."""
    v = (v or "").strip()
    if v == "":
        return "none"
    if is_bare_safe(v):
        return v
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def sql_quote_expr(col: str) -> str:
    """A SQL expression rendering `col` (a text-typed SQL expression -- a column reference or
    unnest()'d element) as a clingo term string, matching `atom_term()`'s decision byte-for-byte:
    bare when safe, quoted-string (same escaping order: backslash then quote) otherwise, the bare
    constant `none` when NULL/empty -- the SQL-side twin `entitlement_floor_atoms` uses for its
    Surface/Mode arguments, sharing this module's ONE character-class rule with `atom_term`
    rather than re-deriving it (the `_wi_quote`-incident lesson, this module's own docstring)."""
    quoted = "('\"' || replace(replace(" + col + ", '\\', '\\\\'), '\"', '\\\"') || '\"')"
    return (
        "(CASE WHEN " + col + " IS NULL OR " + col + " = '' THEN 'none' "
        "WHEN " + col + " ~ '^[a-z][a-z0-9_]*$' THEN " + col + " "
        "ELSE " + quoted + " END)"
    )
