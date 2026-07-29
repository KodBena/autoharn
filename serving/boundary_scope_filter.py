#!/usr/bin/env python3
"""boundary_scope_filter -- the boundary-side scope enforcement filter, design/
FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md §1b/§1c/§2/§4, work item
ac-boundary-scope-filter. This is the serving-side follow-on kernel/lineage/s70-scope-
binding.sql's own header flagged loudly as NOT built by that delta ("RECORDABLE HERE; NOT
YET ENFORCED AT ANY BOUNDARY ROUTE") -- this module is that enforcement.

THE ONE SEAM (spec §2, "the SAME seam get_all_rows/the registry wrapper already funnels
through"): `serving/boundary_service.py`'s `_json_read_response` is the server-side analogue
of the client's `get_all_rows` -- every GET route that returns row-shaped content (a bare
list, a single dict, or `None`) passes through it exactly once, immediately before the
response is constructed. `apply_scope` is called from THERE, and nowhere else, so a route
gains scope enforcement by threading `cfg`/`view`/`id_field` through its own existing call
to `_json_read_response`, never by duplicating filtering logic per route.

IDENTITY -> SCOPE RESOLUTION, THE ROW-812 IDENTITY-CONTINUITY DESIGN POINT (REQUIRED by this
work item's own commission): resolve_scope resolves a scope by querying
`{schema}.principal_scopes` (kernel/lineage/s70-scope-binding.sql Element 5) keyed on the
CURRENT REQUEST's own resolved principal id -- one query, one row, no history. There is no
kernel-side identity-continuity guard across a scope's own supersession (row 812's own MINOR,
accepted-disclosed at the kernel layer, carried here as a REQUIRED design point): a principal
whose scope binding is superseded (rotated to a narrower scope, widened, or WITHDRAWN
entirely -- principal_binding_active=false, dropping the subject from principal_scopes by
construction, s70 Element 5's own COMMENT) is, from the very next request onward, governed
SOLELY by whatever `principal_scopes` returns for that principal id AT READ TIME. This
resolver never consults `ledger`/`ledger_current` directly for a scope's own history and never
caches a scope across requests -- "current in-force binding of the RESOLVED principal only,
never scope history" is therefore not a discipline this module could violate even by accident:
there is no code path here that COULD read an older scope than the view's own present answer.

REASONED THROUGH, THE ONE RESIDUE NAMED HONESTLY (the commission's own instruction: "reason
it through honestly and write down the result, including any residue"): could a
SUBJECT-SWITCHING rotation -- the SAME principal_scope_bound row's own `principal_subject`
column can never change post-write (s70 has no UPDATE path, only fresh assertion/
supersession rows, s41's own uniform-retraction discipline) -- widen anyone's visibility?
The only rotation shape that exists is (a) a fresh principal_scope_bound row for subject P,
narrowing/widening/re-shaping P's OWN scope, or (b) a withdrawal (principal_binding_active=
false) for subject P, returning P to the FAIL-SAFE OPEN SCOPE (s70 Element 5's own COMMENT:
"a withdrawal... drops the subject from this view... returning them to the open-scope
default"). Case (b) is the one place open-scope is not merely the ABSENCE of a scope but the
DELIBERATE RESULT of a rotation -- and it IS a widening, but ONLY FOR THE SEVERED SUBJECT
THEMSELVES, never for anyone else (subject P's own withdrawal cannot alter what subject Q's
`principal_scopes` row says; the view's own WHERE clause is `principal_subject`-keyed, one
row per subject, no cross-subject read). This is the exact fail-safe DIRECTION the kernel
delta's own header already commits to (s60's entitlement machinery: absence reads as
vacuously satisfied, never vacuously refused) applied one layer up: a scope withdrawal is a
widening of the withdrawn principal's OWN future visibility, disclosed here as the real,
accepted residue (identical in shape to every other standing-lifecycle severance in this
project being PROSPECTIVE-ONLY, s45's own I5 asymmetry) -- never a widening that reaches a
DIFFERENT principal's visibility, which no code path in `principal_scopes` or this module can
construct (there is no join, no fan-out, no cross-subject predicate anywhere in the Element 5
view or in `resolve_scope` below).

WHICH IDENTITIES CAN CARRY A SCOPE AT ALL: `principal_scopes.subject` is a bigint ledger row
id (a real, registered principal). Of the THREE identity channels this boundary resolves
(design/FABLE-DISPATCH-MECHANICS-SPEC.md §2: minted / vendor / anonymous), only "minted"
carries a service-verified bigint principal id AT THIS LAYER (`ctx.principal`, the
X-Autoharn-Minted-Principal header's own validated integer) -- a vendor stamp names an AGENT
STRING, and this service deliberately never verifies the HMAC itself (the conduit invariant,
spec §1), so mapping a vendor agent name to a principal ROW id would require a second,
unverified kernel round-trip this module does not perform. "vendor" and "anonymous" callers
therefore always resolve to the OPEN SCOPE here -- not because they are trusted more, but
because there is no principal id this layer can safely bind a scope query to; a deployment
wanting scoped vendor-stamped agents needs S3 stamp-binding (spec §5 roster item 5, a
SEPARATE, not-yet-built mechanism this module does not anticipate). This is the SAME
conservative posture the AC spec's own §1a text already committed to for read identity
generally ("anonymous... resolves to the world's open scope").

DISCLOSURE-MODE DEFAULT (a NAMED LIMIT, s70's own header: "which tiers a boundary filter
actually HONORS... is a serving-layer fact... this delta does not pick one"): a scope binding
carrying no explicit `scope_disclosure_mode` (NULL) is treated as `marked` here -- the
MOST-disclosing of the three tiers (existence + typed marker, content withheld) -- rather than
silently assuming a stricter tier the binder never asked for. A deployment wanting hash_stub
or full defaults must bind them explicitly (spec §1c: all three tiers are representable from
the kernel's own first build).

EXCLUSION-FAMILY MATCHING (spec §4 denomination check: "kinds, threads, work-item lineage,
registry surface names... never row-id arithmetic"), applied per served ROW, against exactly
the four families `scope_exclusions_shape_ok` (kernel/lineage/s70-scope-binding.sql) admits:
  - kind-class:        row['kind'] == value                  (ledger-shaped rows only)
  - thread:             row['missive_thread'] == value         (missive-shaped rows only)
  - work-item-lineage: row['work_slug'] or row['slug'] == value (DIRECT slug match only -- see
                        the NAMED LIMIT below; `slug` is `work_item_current`'s own alias for
                        the SAME fact, kernel/lineage/s22-work-item-ledger.sql's CREATE VIEW)
  - rows:              str(row[id_field]) in the explicit id set
A row lacking the relevant column for a given family (e.g. a non-ledger registry view has no
`kind` column) simply cannot match that family -- absence of the matched column is NOT itself
exclusion-worthy; only a positive value match excludes.

NAMED LIMIT (work-item-lineage is NOT a tree walk): "lineage" in the spec's own vocabulary
plausibly reads as "this slug and its descendants", but this module matches ONLY the exact
`work_slug` named by the exclusion entry -- it does not walk `work_item_descendants` (a
recursive view VIEW_REGISTRY itself excludes from pagination, see `boundary_service.py`'s own
leading comment on that exclusion) to widen the match to a whole subtree. Widening to a true
subtree walk is a real, disclosed follow-on (it would need a recursive kernel query per
distinct work-item-lineage exclusion, a cost/shape question this build does not size), not a
silent narrowing: the reviewer-blindness worked example (spec §3) itself excludes "the work
item's opener/decision rows... expressed by lineage predicate" naming ONE slug, which this
exact-match semantics already serves correctly for the single-slug case the spec's own worked
example describes.

REDACTION MARKER SHAPE: `{id_field: <value>, "redacted": true, "scope": {"family": ...,
"value": ...}}` -- the spec's own `{id, redacted: true, scope}` shape (§1b), generalized to
each view's own key-column NAME (VIEW_REGISTRY already keys views on `id`/`row_id`/`slug`/
`scope`/etc, never uniformly "id") rather than inventing a second key-naming convention this
build does not need. `hash_stub` additionally carries `row_hash` when the underlying row
itself has one (raw ledger-shaped reads only -- `/rows/current`, `/rows/{id}`,
`/rows/{id}/history`, `/rows/asof/{ts}`); a registry-derived view with no `row_hash` column
degrades hash_stub to the SAME marker shape as `marked` (never fabricates a hash it does not
have) -- a named, disclosed limit, not a silent capability lie.

FULL TIER: the row is dropped from the served content entirely -- no marker, existence itself
withheld (spec §1c: "the row does not cross at all"). For a LIST route this means the row is
simply absent from the array (the count the caller sees is scope-relative, honestly smaller,
never a client-visible global count the full tier would falsify -- spec §1c's own standing
obligation). For a SINGLE-ROW route (`/rows/{id}`, `/artifacts/{hash}/stat`) this means the
route answers as though the row does not exist -- `apply_scope` signals this back to its
caller via `omit_singleton=True` rather than returning `None` (which some routes already use
to mean "genuinely absent from storage" and 404 on) so the caller can choose its own message
text; either way the HTTP shape is the SAME typed 404 family every not-found already uses,
never a NEW, scope-specific status code that itself would leak "this exists but you may not
see it".

FAIL-SAFE / BYTE-IDENTICAL REGRESSION BAR: `apply_scope` returns `content` completely
UNCHANGED (same value, same order, no wrapping) whenever ANY of -- `cfg` is `None` (a direct/
unit-shaped caller, this project's own fixture bank), the resolved identity is not "minted",
`principal_scopes` does not exist on this world (a pre-s70 kernel), or the resolved principal
has no row in `principal_scopes` at all (the fail-safe open-scope default, s70 Element 5's own
COMMENT) -- so an unarmed world, or any caller this module cannot attribute a scope to, serves
BYTE-IDENTICALLY to a world with no scope filter at all, the regression bar this work item's
own commission states verbatim.

Stdlib only, top-of-file imports (the lazy-import gate, gates/no_lazy_imports.py, applies).
Dependency-injected (`query_json_fn`, `regclass_exists_fn`) rather than importing
`serving/boundary_service.py` -- that module already imports THIS one (`_json_read_response`
calls `apply_scope`), and a back-import would be a cycle; the two callables this module needs
are passed in by its one caller instead, the same DI shape this project's fixture bank already
expects of `boundary_service._query_json`/`_regclass_exists`.
"""
from __future__ import annotations

from typing import Any, Protocol

# The closed, four-member exclusion-family vocabulary kernel/lineage/s70-scope-binding.sql's
# own `scope_exclusions_shape_ok` CHECK admits -- quoted here so a typo'd family name in this
# module fails loudly (ValueError-shaped, in `_row_matches_exclusion` below) rather than
# silently never matching.
_FAMILY_KIND_CLASS = "kind-class"
_FAMILY_THREAD = "thread"
_FAMILY_WORK_ITEM_LINEAGE = "work-item-lineage"
_FAMILY_ROWS = "rows"

_KNOWN_FAMILIES = frozenset({
    _FAMILY_KIND_CLASS, _FAMILY_THREAD, _FAMILY_WORK_ITEM_LINEAGE, _FAMILY_ROWS,
})

# The three-tier disclosure vocabulary kernel/lineage/s70-scope-binding.sql's own
# `scope_disclosure_mode_vocabulary` CHECK admits (spec §1c).
DISCLOSURE_MARKED = "marked"
DISCLOSURE_HASH_STUB = "hash_stub"
DISCLOSURE_FULL = "full"

# This module's OWN default when a scope binding carries no explicit tier -- see module
# docstring's "DISCLOSURE-MODE DEFAULT" section.
_DEFAULT_DISCLOSURE_MODE = DISCLOSURE_MARKED


class QueryJsonFn(Protocol):
    def __call__(self, cfg: Any, sql: str, extra_v: dict[str, str] | None = None) -> Any: ...


class RegclassExistsFn(Protocol):
    def __call__(self, cfg: Any, qualified_name: str) -> bool: ...


def resolve_scope(
    query_json_fn: QueryJsonFn,
    regclass_exists_fn: RegclassExistsFn,
    cfg: Any,
    principal_id: int,
) -> dict[str, Any] | None:
    """The ONE query this module ever issues to resolve a scope: `{schema}.principal_scopes`
    (kernel/lineage/s70-scope-binding.sql Element 5), keyed on `principal_id`, LIMIT 1 (the
    view is already supersession/active-filtered to at most one current row per subject --
    LIMIT 1 is belt-and-braces, never load-bearing). Returns `None` for a pre-s70 kernel (the
    view does not exist -- capability-absent, degrades to open scope, never an error), for a
    principal with no bound scope (the fail-safe default), or for a genuinely NULL result;
    otherwise the row's own `{scope_surfaces, scope_exclusions, scope_disclosure_mode}` dict."""
    schema = cfg.schema
    if not regclass_exists_fn(cfg, f"{schema}.principal_scopes"):
        return None
    return query_json_fn(
        cfg,
        f"SELECT to_jsonb(t) FROM (SELECT scope_surfaces, scope_exclusions, "
        f"scope_disclosure_mode FROM {schema}.principal_scopes "
        f"WHERE subject = {int(principal_id)} LIMIT 1) t;",
    )


def _row_matches_exclusion(row: dict[str, Any], family: str, value: Any, id_field: str) -> bool:
    if family == _FAMILY_KIND_CLASS:
        return "kind" in row and row["kind"] == value
    if family == _FAMILY_THREAD:
        return "missive_thread" in row and row["missive_thread"] == value
    if family == _FAMILY_WORK_ITEM_LINEAGE:
        # A raw ledger-shaped row (`/rows/current`, `/rows/{id}`, ...) carries the work-item
        # column under its OWN name, `work_slug` (kernel/lineage/s22-work-item-ledger.sql);
        # `work_item_current` (VIEW_REGISTRY, `GET /work/items`) aliases the SAME fact to
        # `slug` (that view's own CREATE VIEW: `work_slug AS slug`) -- both are checked so this
        # ONE exclusion family matches on whichever of the two a given served row actually
        # carries, never silently missing the view whose own column the spec's reviewer-
        # blindness worked example (§3) most directly targets.
        if "work_slug" in row and row["work_slug"] == value:
            return True
        return "slug" in row and row["slug"] == value
    if family == _FAMILY_ROWS:
        if id_field not in row or row[id_field] is None:
            return False
        wanted = {str(v) for v in value} if isinstance(value, list) else {str(value)}
        return str(row[id_field]) in wanted
    # An exclusion entry outside the closed vocabulary cannot reach here in practice --
    # `scope_exclusions_shape_ok` (kernel-side) already refuses it at write time -- but a
    # row-level match function must never silently treat an unrecognized family as "no
    # match" (that would be a silent narrowing of the exclusion the binder actually wrote);
    # refuse loudly instead, the same "unknown vocabulary member is loud, not silently
    # ignored" discipline the ASP-twin spec's own exporter states for the identical closed
    # family set (design/FABLE-ENGINE-ENTITLEMENT-SCOPE-ASP-TWIN-SPEC.md §1b).
    raise ValueError(
        f"boundary_scope_filter: scope_exclusions entry names family {family!r}, outside the "
        f"closed four-member vocabulary {sorted(_KNOWN_FAMILIES)} -- this should be "
        f"impossible past kernel/lineage/s70-scope-binding.sql's own scope_exclusions_shape_ok "
        f"CHECK; refusing rather than silently passing the row through unfiltered.")


def _matching_exclusion(
    exclusions: list[dict[str, Any]], row: dict[str, Any], id_field: str,
) -> dict[str, Any] | None:
    for entry in exclusions:
        family = entry.get("family")
        value = entry.get("value")
        if _row_matches_exclusion(row, family, value, id_field):
            return entry
    return None


def _redact_row(
    row: dict[str, Any], entry: dict[str, Any], disclosure_mode: str, id_field: str,
) -> dict[str, Any]:
    marker: dict[str, Any] = {
        id_field: row.get(id_field),
        "redacted": True,
        "scope": {"family": entry.get("family"), "value": entry.get("value")},
    }
    if disclosure_mode == DISCLOSURE_HASH_STUB and row.get("row_hash") is not None:
        marker["row_hash"] = row["row_hash"]
    return marker


class ScopeFilterResult:
    """The return shape of `apply_scope` -- `content` is the (possibly filtered) value to
    serve; `omit_singleton` is `True` only when `content` was a single dict (not a list) and a
    `full`-tier exclusion matched it, meaning the caller must answer as though the row does
    not exist at all (module docstring, "FULL TIER"); `redactions` is a SUMMARY (family,
    value, disclosure_mode, count) suitable for the read journal's own typed redaction event
    -- never row content, matching `boundary_read_journal`'s own "never a second copy of
    scoped data" invariant."""

    __slots__ = ("content", "omit_singleton", "redactions")

    def __init__(self, content: Any, omit_singleton: bool, redactions: list[dict[str, Any]]) -> None:
        self.content = content
        self.omit_singleton = omit_singleton
        self.redactions = redactions


def apply_scope(
    content: Any,
    *,
    cfg: Any | None,
    view: str | None,
    id_field: str,
    resolution_case: str | None,
    principal: str | None,
    query_json_fn: QueryJsonFn,
    regclass_exists_fn: RegclassExistsFn,
) -> ScopeFilterResult:
    """The one entry point `serving/boundary_service.py`'s `_json_read_response` calls. See
    module docstring's "FAIL-SAFE / BYTE-IDENTICAL REGRESSION BAR" for the exact passthrough
    conditions. `view`/`id_field` name the surface being read (VIEW_REGISTRY's own key-column
    choice, or the literal view name for the fixed routes -- `ledger`/`ledger_current` for the
    raw/current row routes); both are used ONLY to select which column each exclusion family
    reads off a served row, never as a scope-surfaces allow-list (scope_surfaces enforcement --
    denying an entire ungranted SURFACE, as opposed to excluding individual ROWS within a
    granted one -- is NAMED, NOT built by this increment; see this work item's own commission,
    which enumerates exclusion semantics and the three disclosure tiers, not surface gating)."""
    no_op = ScopeFilterResult(content, False, [])
    if cfg is None or resolution_case != "minted" or principal is None:
        return no_op
    try:
        principal_id = int(principal)
    except (TypeError, ValueError):
        return no_op
    scope_row = resolve_scope(query_json_fn, regclass_exists_fn, cfg, principal_id)
    if not scope_row:
        return no_op  # fail-safe default: no bound scope == open scope.
    exclusions = scope_row.get("scope_exclusions") or []
    if not exclusions:
        return no_op  # a binding that grants/excludes nothing is a no-op here too.
    disclosure_mode = scope_row.get("scope_disclosure_mode") or _DEFAULT_DISCLOSURE_MODE

    redaction_tally: dict[tuple[str, str], int] = {}

    def _tally(entry: dict[str, Any]) -> None:
        key = (str(entry.get("family")), str(entry.get("value")))
        redaction_tally[key] = redaction_tally.get(key, 0) + 1

    if isinstance(content, list):
        out: list[Any] = []
        for row in content:
            if not isinstance(row, dict):
                out.append(row)
                continue
            entry = _matching_exclusion(exclusions, row, id_field)
            if entry is None:
                out.append(row)
                continue
            _tally(entry)
            if disclosure_mode == DISCLOSURE_FULL:
                continue  # full tier: the row does not cross at all -- dropped, no marker.
            out.append(_redact_row(row, entry, disclosure_mode, id_field))
        content_out: Any = out
        omit = False
    elif isinstance(content, dict):
        entry = _matching_exclusion(exclusions, content, id_field)
        if entry is None:
            content_out = content
            omit = False
        else:
            _tally(entry)
            if disclosure_mode == DISCLOSURE_FULL:
                content_out = None
                omit = True
            else:
                content_out = _redact_row(content, entry, disclosure_mode, id_field)
                omit = False
    else:
        content_out = content
        omit = False

    redactions = [
        {"family": family, "value": value, "disclosure_mode": disclosure_mode, "count": count}
        for (family, value), count in redaction_tally.items()
    ]
    return ScopeFilterResult(content_out, omit, redactions)
