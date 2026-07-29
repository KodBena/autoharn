#!/usr/bin/env python3
"""boundary_diagnostic_log -- the DIAGNOSTIC-grade, jq-queryable JSON-lines log layer for
serving/boundary_service.py (design/FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md, RATIFIED IN FULL
2026-07-27, ledger row 1500 -- read that spec in full before touching this module).

STANDING LINE (spec, verbatim): this layer is DIAGNOSTIC-grade, never evidentiary. No fact may
live only here. The kernel's own s43 refusal journal, through the ledger, is the evidentiary
basis (maintainer principle 2026-07-11) -- this module adds provenance breadcrumbs a human or
`jq` can reconstruct a request from, nothing a guarantee is allowed to depend on.

L1 -- ONE PER-REQUEST CONTEXT OBJECT (spec §2 L1). `RequestContext` is minted ONCE per request
by `serving/boundary_service.py`'s own ASYNC middleware (never a plain-`def` dependency -- see
below) and held in `REQUEST_CONTEXT`, a single `contextvars.ContextVar`. This is deliberately
the SAME object row 1471's identity-plumbing work will extend (principal/session) rather than
mint its own -- built once here (ADR-0012 P1), not re-derived by that later build.

THE WITNESSED CONSTRAINT THIS MODULE IS BUILT AROUND (spec §1 point 2, ledger row 1498,
witnessed 20/20 on the installed stack -- Python 3.13.13, fastapi 0.139.2, starlette 1.3.1,
uvicorn 0.51.0, anyio 4.14.1): contextvars propagate from an ASYNC frame INTO a plain-`def`
handler dispatched to Starlette's threadpool (`run_in_threadpool` copies the CURRENT context
into the worker thread) -- reading, and mutating an ALREADY-BOUND object's own attribute,
both work correctly across that boundary. What does NOT propagate is a plain-`def`
DEPENDENCY's own `ContextVar.set()` call made INSIDE the threadpool -- each dispatch copies the
context outward, but a child's `.set()` never flows back to the parent (witnessed as the
negative control: silently lost). This module never calls `.set()` from inside a route
handler or from `_psql` -- `bind_deployment` below MUTATES THE SAME OBJECT's `deployment`
attribute instead, which needs no context write-back at all (every thread holding a reference
to the one `RequestContext` instance sees the same mutation, by ordinary Python object
semantics, independent of the ContextVar machinery). THEREFORE: L1 is async middleware (this
module's own contract), never a plain-`def` dependency for context-SETTING.

L2 -- A CLOSED EVENT VOCABULARY, EIGHT MEMBERS (spec §2 L2, §5 closure statement). `Event`
names them; `EVENT_REQUIRED_FIELDS` is the per-event required-field contract, checked in
`log_event` BEFORE any level filter (spec, and the proxy survey's own witnessed lesson: a
validation whose result depends on the level filter is a trap -- design/
LOGGING-DIRECTION-SURVEY-2026-07-27.md §2 item 3). Emitting an unknown event, or omitting a
required field, raises `LogContractError` -- ADR-0002 applied to the log's own contract.
REQUIRED FIELDS ARE DELIBERATELY NEVER `request_id`/`route` alone: those two are auto-enriched
from `REQUEST_CONTEXT` when one exists (with an honest sentinel when it does not -- see
`log_event`'s own body) so that a caller OUTSIDE any live request (this project's own fixture
bank calls `_psql`/`_query_json` directly, unit-style, with no HTTP request in flight at all --
`seen-red/boundary-service/run_fixtures.py`'s W28/W30 legs, for one) never trips the contract
merely for lacking a request to be part of; what IS required, per event, is the STRUCTURAL
information only the call site itself can supply (a disposition, a surface, a status, a
duration) -- never something this module already guarantees to backfill.

THE REFUSAL EVENT'S DISPOSITION VALUE IS DERIVED, NOT A SECOND LIST (spec §2 L2, verbatim:
"derived from the disposition enumeration the service already computes -- one enumeration").
Every `serving/boundary_models.py` response model that carries a `disposition: str = "..."`
class-level default IS that enumeration; `known_boundary_model_dispositions()` below reads it
by introspection for the witness suite's own use (asserting the derivation claim mechanically,
not by hand-inspection) -- but the ACTUAL logging call sites (`serving/boundary_service.py`'s
`capability_absent`/`payload_too_large`/`server_saturated`/`deployment_saturated`/
`unknown_deployment`/`unknown_view`, plus the `_BodyReadTimeout` exception handler) each pass
`body.disposition` -- the model instance's OWN field -- as the `refusal` event's `disposition`
value, never a second hardcoded string. A disposition added to `boundary_models.py` later gets
its log call automatically wherever its own builder function already runs; nothing here needs
a parallel edit. `infra_failure`/`unclassified_failure` are excluded from this derivation on
purpose -- both already carry a `disposition` field in `boundary_models.py`, but the spec names
them as their OWN dedicated top-level events (L4: they migrate the service's pre-existing
`_log_infra_failure`/`_log_unclassified_failure` call sites), not instances of `refusal`.

L3 -- ONE RENDERING: JSON LINES, THE RATIFIED FLOOR (spec §2 L3). `log_event` renders one JSON
object per line via `sys.stderr.write` -- the SAME house channel `serving/boundary_service.py`'s
own `_log_infra_failure`/`_log_unclassified_failure` already use, captured by
`serving/ensure_running.py`'s existing `<world>/service.log` redirect (destination, rotation,
and how the service is OPERATED are all UNCHANGED -- this module never opens a file, never
picks a path, never touches `ensure_running.py`). The existing human stderr lines (uvicorn's own
access/error lines, and this service's own pre-existing diagnostic writes) stay exactly as they
were, beside these new lines -- no console/logfmt renderer is added (survey §3.3: "one machine
rendering ... a second renderer is cheap to add later and a surface to keep honest now").

THE FAIL-LOUD/NEVER-500-A-REQUEST TENSION, RESOLVED (the commission's own question, answered
here on the record): a MIS-AUTHORED CALL SITE -- an unknown event name, a missing required
field -- is a DEFECT IN THIS SERVICE'S OWN CODE, not a fact about the request being served; it
is deterministic per code path (it either always fires for that call site or never does), so it
is exactly the class ADR-0002 says to raise loudly for, and it will be caught at review/CI/the
first exercise of that code path, never silently at 3am against production traffic. Once past
that contract check, RENDERING AND WRITING THE LINE -- `json.dumps` (guarded by `default=str`
so no field value this module ever populates can realistically defeat it) and the `sys.stderr`
write itself (which CAN fail for reasons entirely external to this code's correctness -- a full
disk, a closed fd) -- run inside ONE broad `try/except Exception: pass`. This is the layer the
spec's own line governs ("the logging layer must never make a request fail"): a log line is
diagnostic-grade, by the standing rule at the top of this docstring, so a defect or environment
failure IN EMITTING IT must never become the reason the request it was merely describing fails.
The two halves are deliberately different in strictness for exactly this reason -- one raises
because it is a correctness signal about THIS SERVICE'S OWN CODE; the other swallows because it
is downstream I/O about a description of a request that has, structurally, already happened.

CONFIG (spec §2, "Config"): the log level is the ONE new field in the existing multiplex TOML
(`serving/boundary_multiplex_config.py`'s own `log_level` key, optional, default `INFO`),
validated whole-file before the socket ever binds -- `LEVELS` below is the ONE home for the
valid-level set (ADR-0012 P1); `boundary_multiplex_config.py` imports it rather than carrying
its own copy. No env var -- the multiplex TOML is this project's one config channel for this
service (survey §3.3, "a parallel env namespace would be a second config channel for the same
process").

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import is top-of-file.
"""
from __future__ import annotations

import contextvars
import dataclasses
import datetime
import json
import sys
from typing import Any

import boundary_models  # noqa: E402  (serving/boundary_models.py -- see module docstring, "the disposition enumeration")


@dataclasses.dataclass
class RequestContext:
    """L1's one per-request context object (spec §2 L1). Mutable by design -- `bind_deployment`
    below mutates `deployment` in place once a route handler resolves its `{deployment}` path
    segment (`serving/boundary_service.py`'s `_resolve_deployment`, the ONE chokepoint every
    route already calls), rather than re-`.set()`-ing the ContextVar from inside a threadpool
    worker (the witnessed trap this module's docstring names). `principal` is a reserved,
    always-`None`-today field for ledger row 1471's identity-plumbing work to fill in later --
    named here, once, so that build extends this object rather than minting its own (spec §2
    L1, verbatim: "this is deliberately the same object the identity work needs")."""

    request_id: str
    route: str
    method: str
    client_addr: str | None
    deployment: str | None = None
    principal: str | None = None
    # design/FABLE-DISPATCH-MECHANICS-SPEC.md §2 (ledger row 1471's dispatch-mechanics build):
    # the identity resolution case this request settled on, recorded so the diagnostic log's L1
    # context carries "which §2 resolution case fired" (the spec's own words) -- one of
    # "minted", "vendor", or "anonymous" (see `bind_identity` below); `None` before identity
    # parsing has run (never observed on a completed request -- `_diagnostic_logging_middleware`
    # calls `bind_identity` unconditionally, on every request, before `call_next`).
    resolution_case: str | None = None
    # The vendor stamp's own five GUC values (app.vendor_session/agent/ts/hmac/invocation),
    # forwarded to `_psql`'s per-request preamble when present -- `None` when this request
    # carried no (or an incomplete) vendor stamp. Kept as a single dict rather than five
    # top-level fields: `_psql` only ever needs "is there a vendor stamp, and if so its whole
    # value set", never a single GUC in isolation.
    vendor_stamp: dict[str, str] | None = None
    # design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md sec1a (work item ac-read-identity):
    # a bare row count for the read journal (serving/boundary_read_journal.py), bound by a GET
    # route handler at the one place it still holds the real Python value (a list/dict/None)
    # BEFORE that value is serialized into a response body -- never re-derived by re-parsing an
    # already-rendered response downstream, which is not even possible for every route past this
    # module's own middleware boundary (`call_next`'s BaseHTTPMiddleware wrapping always returns
    # a StreamingResponse with no static `.body` attribute; only `bind_read_row_count`, called
    # from inside the handler, ever sees the real value). `None` for a route this build does not
    # instrument (an SSE stream, a capability-metadata route with no row concept) -- never a
    # fabricated number. NOT part of `EVENT_REQUIRED_FIELDS`/`log_event`'s own merged record
    # (this diagnostic log's closed 8-event vocabulary is unchanged by this field's addition) --
    # `serving/boundary_service.py`'s own read-journal middleware code is this field's ONLY
    # reader.
    read_row_count: int | None = None
    # design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md sec1b/1c (work item
    # ac-boundary-scope-filter): a SUMMARY of the scope redactions this request's own read
    # applied -- `[{family, value, disclosure_mode, count}, ...]` -- bound by
    # `serving/boundary_service.py`'s `_json_read_response` at the SAME place it binds
    # `read_row_count` above, immediately after `boundary_scope_filter.apply_scope` returns.
    # NEVER row content (the read journal's own "must never become a second copy of scoped
    # data" invariant, `boundary_read_journal`'s module docstring, applies here identically).
    # `None`/empty for every request this build's own filter left unfiltered (an unarmed
    # world, an unattributable identity, or a route this build does not scope) -- NOT part of
    # `EVENT_REQUIRED_FIELDS`/`log_event`'s own closed 8-event vocabulary, the SAME posture
    # `read_row_count` above already holds (a context field the read journal alone reads, not
    # a diagnostic-log event of its own).
    scope_redactions: list[dict[str, Any]] | None = None


def bind_identity(resolution_case: str, *, principal: str | None = None,
                   vendor_stamp: dict[str, str] | None = None) -> None:
    """Mutates the CURRENT request's own `RequestContext` in place (the SAME `bind_deployment`
    pattern this module already established -- see its own docstring for why mutating the
    shared object, never `REQUEST_CONTEXT.set()` from inside a threadpool, is the safe way to
    extend context after the async middleware has already minted it). Called from
    `serving/boundary_service.py`'s identity-parsing pass, itself called from the SAME async
    middleware that mints `RequestContext` -- before `call_next`, so every downstream route
    handler and every `_psql` call sees the resolved identity. A no-op when no request context
    is bound (a direct, non-HTTP call site)."""
    ctx = REQUEST_CONTEXT.get()
    if ctx is not None:
        ctx.resolution_case = resolution_case
        ctx.principal = principal
        ctx.vendor_stamp = vendor_stamp


REQUEST_CONTEXT: contextvars.ContextVar[RequestContext | None] = contextvars.ContextVar(
    "boundary_diagnostic_log_request_context", default=None
)


def bind_deployment(deployment: str) -> None:
    """Mutates the CURRENT request's own `RequestContext.deployment` in place -- called from
    `serving/boundary_service.py`'s `_resolve_deployment`, the single chokepoint every route
    handler already calls to resolve its `{deployment}` path segment (ADR-0012 P1: one call
    site, not one per route). Never calls `REQUEST_CONTEXT.set()` -- see this module's own
    docstring for why a plain-`def` handler's `.set()` would be silently lost, and why mutating
    the shared object instead sidesteps that trap entirely. A no-op when no request context is
    bound (a direct, non-HTTP call site -- e.g. this project's own fixture bank calling
    `boundary_service._psql`/`_query_json` directly)."""
    ctx = REQUEST_CONTEXT.get()
    if ctx is not None:
        ctx.deployment = deployment


def bind_read_row_count(n: int | None) -> None:
    """design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md sec1a: mutates the CURRENT
    request's own `RequestContext.read_row_count` in place -- the SAME `bind_deployment`/
    `bind_identity` pattern above (mutate the shared object, never `REQUEST_CONTEXT.set()` from
    inside a threadpool worker). Called from `serving/boundary_service.py`'s own
    `_json_read_response` helper, itself called from every GET route handler that returns a
    row-shaped JSON body. A no-op when no request context is bound (a direct, non-HTTP call
    site -- this project's own fixture bank calling route-adjacent helpers directly)."""
    ctx = REQUEST_CONTEXT.get()
    if ctx is not None:
        ctx.read_row_count = n


def bind_scope_redactions(redactions: list[dict[str, Any]] | None) -> None:
    """design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md sec1b/1c: mutates the CURRENT
    request's own `RequestContext.scope_redactions` in place -- the SAME `bind_read_row_count`
    pattern above. Called from `serving/boundary_service.py`'s `_json_read_response`, right
    beside its existing `bind_read_row_count` call. A no-op when no request context is bound
    (a direct, non-HTTP call site)."""
    ctx = REQUEST_CONTEXT.get()
    if ctx is not None:
        ctx.scope_redactions = redactions


def current_route() -> str | None:
    """The current request's own `route` field, or `None` outside any request context (a
    direct, non-HTTP call site) -- `serving/boundary_service.py`'s `_psql` uses this to label
    the `kernel_call` event's `surface` field without threading a new parameter through every
    one of its callers (reads/writes/`/health`'s own kernel probes alike)."""
    ctx = REQUEST_CONTEXT.get()
    return ctx.route if ctx is not None else None


class Event:
    """The closed, EIGHT-member event vocabulary (spec §2 L2, §5 closure statement). Plain
    string constants, deliberately NOT an `enum.Enum` -- `log_event`'s own contract check must
    accept an arbitrary CALL-SITE string (including one a future edit typos) and refuse it by
    name; comparing a raw string against `MEMBERS` below states that refusal more plainly than
    coercing an arbitrary string into an `Enum` member would."""

    REQUEST_START = "request_start"
    REQUEST_END = "request_end"
    KERNEL_CALL = "kernel_call"
    WRITE_VERDICT = "write_verdict"
    REFUSAL = "refusal"
    INFRA_FAILURE = "infra_failure"
    UNCLASSIFIED_FAILURE = "unclassified_failure"
    STARTUP = "startup"


MEMBERS: frozenset[str] = frozenset({
    Event.REQUEST_START, Event.REQUEST_END, Event.KERNEL_CALL, Event.WRITE_VERDICT,
    Event.REFUSAL, Event.INFRA_FAILURE, Event.UNCLASSIFIED_FAILURE, Event.STARTUP,
})

# Per-event required fields (spec §2 L2) -- checked against the MERGED record (explicit
# call-site fields; `request_id`/`deployment`/`client_addr` are enriched from REQUEST_CONTEXT
# separately and are NEVER themselves a required key here, precisely so a direct, non-HTTP
# call site -- this project's own fixture bank, `boundary_service._psql`'s own unit-shaped
# callers -- never trips the contract merely for lacking a live request; what a call site MUST
# supply is the structural fact only it can know (a disposition, a surface, an exit class, a
# status, a duration).
#
# ONE SHAPE PER FIELD NAME, EVERYWHERE (fresh-context review finding (a), post-f450019): a jq
# query grouping or filtering on a field name must see the SAME kind of value under that name
# on every event that carries it -- a name that means one thing on one event and a different
# thing on a sibling event silently splits what should be one coherent series. Two corollaries,
# both load-bearing here:
#   1. `route` is ALWAYS the bare request path (`request.url.path`), on every event that
#      carries it (`request_start`/`request_end`/`kernel_call`/`infra_failure`/
#      `unclassified_failure`) -- never method-prefixed. An event that also needs the HTTP
#      method carries it under its OWN field, `method` (request_start/request_end already did;
#      infra_failure/unclassified_failure now do too, splitting what used to be one combined
#      "METHOD /path" string under `route` into two fields).
#   2. `surface` is ALWAYS the short write-surface label the kernel's own boundary functions
#      use (`ledger`/`review`/`registration`/`obligation`/`obligation_revoke`/
#      `missive_dispose`/`artifact` -- `write_verdict`'s own vocabulary, matching
#      `WRITE_SURFACES`'s keys in boundary_service.py) -- never a route path. `kernel_call`
#      used to overload `surface` with the FULL route path; it now carries that same fact
#      under `route` instead (the identical value `request_start`/`request_end` already log
#      for the same request, via REQUEST_CONTEXT's own auto-enrichment when a request context
#      exists; a direct, non-HTTP call site with no context still gets an explicit "unknown"
#      fallback, same as before this fix, just under the correctly-shared field name).
EVENT_REQUIRED_FIELDS: dict[str, frozenset[str]] = {
    Event.REQUEST_START: frozenset({"route", "method"}),
    Event.REQUEST_END: frozenset({"route", "status", "duration_ms"}),
    Event.KERNEL_CALL: frozenset({"route", "exit_class", "duration_ms"}),
    Event.WRITE_VERDICT: frozenset({"surface", "disposition"}),
    Event.REFUSAL: frozenset({"disposition"}),
    Event.INFRA_FAILURE: frozenset({"route", "method"}),
    Event.UNCLASSIFIED_FAILURE: frozenset({"route", "method"}),
    Event.STARTUP: frozenset({"deployments", "max_inflight_kernel_calls"}),
}
# MINOR (fresh-context review, carried as a comment per the coordinator's own instruction): the
# check below is PRESENCE-only, not type-checked -- a required field supplied as `None` (e.g.
# `disposition=None`, which `make_write_route`'s handler passes deliberately when a kernel verdict
# shape drifts and no longer carries a `disposition` key at all) satisfies `required - merged.keys()`
# and is NOT caught here. This is a deliberate choice, not an oversight: the proxy survey's own
# design (design/LOGGING-DIRECTION-SURVEY-2026-07-27.md §2 item 2) is presence-only too, and a
# stricter non-None check would make this log's OWN contract a second, independent judge of
# kernel-shape validity -- exactly the "second validator that could disagree with the authority"
# class serving/boundary_models.py's own docstring already forbids for the write path. A `None`
# under a required key is still visible to `jq` (`select(.disposition == null)`), which is the
# honest signal a kernel-shape drift produces here, not a silently absent field.


class LogContractError(Exception):
    """ADR-0002 applied to the log's own contract (spec §2 L2) -- raised by `log_event` for
    exactly two shapes: an event name outside `MEMBERS` (a call-site typo, or a genuinely new
    event authored without joining the closed vocabulary above), or a known event missing one
    of its own `EVENT_REQUIRED_FIELDS`. The message teaches: the event, the full required set,
    what was missing, and what WAS provided (the proxy survey's own `LogContractError` shape,
    design/LOGGING-DIRECTION-SURVEY-2026-07-27.md §2 item 2) -- never a bare `KeyError` or
    `AssertionError` a reader would have to go spelunking to explain."""

    def __init__(
        self, *, event: str, required: frozenset[str], missing: frozenset[str],
        provided: frozenset[str],
    ) -> None:
        if event not in MEMBERS:
            message = (
                f"boundary_diagnostic_log: REFUSED -- log_event({event!r}, ...) names an "
                f"event outside the closed {len(MEMBERS)}-member vocabulary (design/"
                f"FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md §2 L2): known events are "
                f"{sorted(MEMBERS)}."
            )
        else:
            message = (
                f"boundary_diagnostic_log: REFUSED -- log_event({event!r}, ...) is missing "
                f"required field(s) {sorted(missing)} (design/"
                f"FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md §2 L2): {event!r} requires "
                f"{sorted(required)}; provided {sorted(provided)}."
            )
        super().__init__(message)
        self.event = event
        self.required = required
        self.missing = missing
        self.provided = provided


def known_boundary_model_dispositions() -> frozenset[str]:
    """The `refusal` event's disposition vocabulary, DERIVED by introspection (spec §2 L2:
    "derived from the disposition enumeration the service already computes -- one
    enumeration") -- every `boundary_models.BaseModel` subclass carrying a class-level
    `disposition: str = "..."` default. Exists for the witness suite's own use, to assert the
    derivation claim mechanically rather than by hand-inspection; the ACTUAL logging call
    sites never consult this function themselves -- each passes its own model instance's
    `.disposition` field directly (see this module's own docstring)."""
    dispositions: set[str] = set()
    for name in dir(boundary_models):
        obj = getattr(boundary_models, name)
        if isinstance(obj, type) and issubclass(obj, boundary_models.BaseModel) and obj is not boundary_models.BaseModel:
            default = obj.model_fields.get("disposition")
            if default is not None and isinstance(default.default, str):
                dispositions.add(default.default)
    return frozenset(dispositions)


# LEVEL FILTER (spec §2, "Config") -- the ONE home for the valid-level set (ADR-0012 P1);
# `serving/boundary_multiplex_config.py` imports LEVELS rather than carrying its own copy, so
# an unknown TOML `log_level` value is refused, at config-validation time, against the SAME
# set this module itself filters against -- never two independently-maintained vocabularies
# that could drift.
LEVELS: dict[str, int] = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}
DEFAULT_LEVEL = "INFO"

_configured_level = DEFAULT_LEVEL


def configure_level(level: str) -> None:
    """Sets the process-wide level filter -- called ONCE, at startup, from
    `serving/boundary_service.py`'s `main()`, after `boundary_multiplex_config.py` has already
    validated the level against `LEVELS` (whole-file, before the socket binds). Refuses an
    unrecognized value here too (construction-time, ADR-0002 rung 1) -- defense in depth, not
    the primary mechanism: a caller that reaches this function with a bad value bypassed the
    config loader entirely, which this project's own house style treats as worth a loud
    refusal in its own right, not a silent no-op."""
    global _configured_level
    if level not in LEVELS:
        raise ValueError(
            f"boundary_diagnostic_log: REFUSED -- configure_level({level!r}) is not one of "
            f"{sorted(LEVELS)}."
        )
    _configured_level = level


def _level_enabled(level: str) -> bool:
    return LEVELS.get(level, LEVELS[DEFAULT_LEVEL]) >= LEVELS[_configured_level]


def _iso_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds")


def log_event(event: str, *, level: str = "INFO", **fields: Any) -> None:
    """THE one emission chokepoint (ADR-0012 P1) -- every one of this module's own docstring's
    named call sites routes through here, never constructing a JSON line by hand. Order,
    exactly per spec §2 L2: (1) event-membership + required-field CONTRACT VALIDATION, which
    RAISES `LogContractError` on failure -- BEFORE the level filter (a validation whose result
    depended on the level filter is the proxy survey's own witnessed trap, §2 item 3); (2) the
    LEVEL FILTER, which may simply return without emitting anything; (3) RENDER + WRITE, which
    can never raise past this function (see this module's own docstring, "THE FAIL-LOUD/
    NEVER-500-A-REQUEST TENSION, RESOLVED")."""
    if event not in MEMBERS:
        raise LogContractError(event=event, required=frozenset(), missing=frozenset(), provided=frozenset(fields))
    ctx = REQUEST_CONTEXT.get()
    merged: dict[str, Any] = {
        "request_id": ctx.request_id if ctx is not None else "no-request-context",
    }
    if ctx is not None:
        merged["route"] = ctx.route
        merged["method"] = ctx.method
        if ctx.client_addr is not None:
            merged["client_addr"] = ctx.client_addr
        if ctx.deployment is not None:
            merged["deployment"] = ctx.deployment
        if ctx.principal is not None:
            merged["principal"] = ctx.principal
        # Which spec-§2 identity resolution case fired (fresh-context review MODERATE, ledger
        # row 1525: the field was set on the context but never landed in any record) --
        # enriched here, the one home, so every event a bound-identity request emits carries it
        # and `jq 'select(.resolution_case=="minted")'` works across the whole series.
        if ctx.resolution_case is not None:
            merged["resolution_case"] = ctx.resolution_case
    merged.update(fields)  # explicit call-site fields always win over context enrichment

    required = EVENT_REQUIRED_FIELDS[event]
    missing = required - merged.keys()
    if missing:
        raise LogContractError(
            event=event, required=required, missing=frozenset(missing),
            provided=frozenset(merged.keys()),
        )

    if not _level_enabled(level):
        return

    record = {"ts": _iso_now(), "event": event, "level": level, **merged}
    try:
        line = json.dumps(record, default=str)
        sys.stderr.write(line + "\n")
    except Exception:
        # I/O (a full disk, a closed fd) or an exotic rendering failure past `default=str`'s
        # own fallback -- either way, this is diagnostic-grade output describing a request
        # that has, structurally, already happened; it must never become the reason that
        # request fails (spec, verbatim). See this module's own docstring for the full
        # resolution of this tension; nothing above this line is caught this loosely.
        pass
