"""
Core CP-SAT model for the minimum-makespan resource-conflict scheduling problem.

Problem
-------
Given a set of jobs, each touching a set of "resources" (e.g. file paths, but the
model treats them as opaque hashable scalars -- strings or ints), find a start
time for every job such that:

  1. Two jobs that share at least one resource never run at overlapping times
     (a resource is a "unary" resource in scheduling-theory terms: at most one
     job may hold it at any instant).
  2. If a global ``max_parallel`` capacity is given, no more than that many jobs
     are running at any single instant, regardless of whether they share resources.

...while minimizing the *makespan*: the completion time (end) of the
last-finishing job. This is the classical minimum-makespan scheduling objective,
not a proxy for it (e.g. it is NOT "minimize the number of rounds", which only
coincides with makespan when every job has the same duration — the general,
variable-duration case is handled directly by this same model).

CP-SAT model
------------
- One interval variable per job: ``(start, duration, end)`` with
  ``start in [0, horizon]`` and ``duration`` fixed to the job's (rounded-to-integer)
  duration. ``horizon`` is the sum of all durations — a safe upper bound, since
  fully serializing every job is always a feasible schedule.
- For each resource touched by 2+ jobs, one ``NoOverlap`` constraint over the
  interval variables of the jobs touching it. This is the standard CP-SAT
  encoding of "these intervals must not overlap in pairs" for a unary resource,
  applied once per resource (a job touching N resources participates in N such
  constraints, one per resource, which is exactly what couples it to every other
  job it conflicts with).
- If ``max_parallel`` is given: one ``AddCumulative`` constraint over *all* job
  intervals, each with demand 1, and total capacity ``max_parallel``. This bounds
  concurrent job count at every instant regardless of resource overlap.
- Objective: a ``makespan`` variable equal (via ``AddMaxEquality``) to the max of
  all job end times, minimized.

CP-SAT is integer-only. Durations are rounded to the nearest positive integer
before building the model (see ``Job.duration`` and ``_to_int_duration``). If a
caller needs sub-integer precision, they should pre-scale all durations (e.g.
multiply every duration by 1000 before calling) and interpret the resulting
integer start/end times in those scaled units themselves — this library does not
silently rescale on the caller's behalf, since that would make the "integer
units" output ambiguous without also returning the scale factor used.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Union

from ortools.sat.python import cp_model

# A JSON-scalar type reasonable for an id or a resource element: a plain
# string or a plain int. Both must be hashable (they end up as dict keys /
# set members -- see `resource_to_indices` in schedule() below and the
# duplicate-id check), which rules out list/dict/None outright, and both must
# be a genuine scalar, which is why `bool` is excluded explicitly even though
# it is technically an `int` subclass in Python: a JSON `true`/`false` landing
# in an `id` or `resources` slot is essentially always a mistake, not a
# deliberate scalar -- the same reasoning `schedule()` already applies to
# `max_parallel` and `time_limit`.
_SCALAR_TYPES = (str, int)
IdType = Union[str, int]


def _is_hashable_scalar(value: object) -> bool:
    return isinstance(value, _SCALAR_TYPES) and not isinstance(value, bool)


def _is_exact_integer(value: object) -> bool:
    """True iff `value` is losslessly convertible to a Python int via the
    `__index__` protocol -- i.e. it IS, conceptually, an integer, not merely
    a number that happens to hold an integral value right now.

    This is deliberately NOT an enumeration of specific types (a plain
    `int`, `numpy.int64`, an `IntEnum`, someone's own `int` subclass, ...):
    naming types one at a time is exactly how the bug this function fixes
    got introduced in the first place (the previous code special-cased
    `isinstance(duration, int)`, so numpy.int64 -- and every other
    __index__-supporting integer type nobody had thought to name -- fell
    through to the lossy `float(duration)` branch below, reproducing the
    float-53-bit-mantissa rounding this module's docstring/comments
    elsewhere describe in detail). `__index__` is Python's own protocol for
    "this object has an exact integer value" (it backs `operator.index`,
    slice indexing, `bin()`/`hex()`, etc.), and every genuine integer type,
    including third-party ones, is expected to implement it -- so testing
    for the protocol handles today's types and tomorrow's alike.

    `decimal.Decimal` and `fractions.Fraction` deliberately do NOT implement
    `__index__`, even though a given instance may hold an exact integral
    value (`Decimal(5)`, `Fraction(10, 2)`): both types can ALSO hold
    genuinely non-integer values (`Decimal("3.5")`, `Fraction(1, 3)`), so
    "is a Decimal/Fraction" is not equivalent to "is an integer" the way
    `__index__` support is for the types that implement it. Treating them as
    exact integers here would require an extra, ad hoc "and is this
    particular instance whole-valued" check, which is a different and
    larger feature (exact-rational duration support) than this function's
    job of testing "is this value an integer". We do not implement that:
    Decimal/Fraction durations fall through to the `float()` conversion
    below, same as any other non-integer numeric type -- which is a
    conscious, documented choice, not an oversight, and is covered by
    `test_decimal_duration_at_the_limit_is_rejected_not_silently_wrong` in
    tests/test_scheduler.py.
    """
    return hasattr(value, "__index__")


def _is_real_number(value: object) -> bool:
    """True iff `value` is a genuine real number -- i.e. supports the
    `__float__` protocol Python itself uses to convert something to a float
    (it backs the `float(x)` builtin). Sibling of `_is_exact_integer` above,
    for parameters (like `time_limit`) that may legitimately be non-integer,
    not just parameters that must be exact integers.

    Deliberately protocol-based (duck typing on `__float__`), NOT
    `isinstance(value, (int, float))` and NOT `isinstance(value,
    numbers.Real)`:

    - `isinstance(value, (int, float))` is exactly the bug class this sweep
      exists to eliminate: it rejects `numpy.float64`/`numpy.int64` and any
      other genuine number type nobody enumerated by name, the same way the
      old `isinstance(duration, int)` rejected `numpy.int64` before
      `_is_exact_integer` replaced it.
    - `numbers.Real`/`numbers.Integral` (the `numbers` module's ABCs) were
      considered and rejected as the general test here, even though they are
      the more "textbook" idiom for "is this a number": those ABCs only
      recognize a type as a real number if that type (or something in its
      MRO) has explicitly registered with the ABC -- `int`, `float`, and
      `numpy`'s scalar types all do this, so they pass either way, but a
      third-party class that implements `__float__`/`__index__` on its own
      merits without bothering to register with `numbers` would silently
      fail an ABC-based `isinstance` check while passing a protocol-based
      one. That is the SAME failure mode the duration fix was written to
      close (a type that IS conceptually a number, just not one anybody
      remembered to enumerate/register) -- so `_is_exact_integer` above
      stays on `__index__`, and this function mirrors it with `__float__`,
      rather than mixing two different "is this a number" idioms in the same
      module.
    """
    return hasattr(value, "__float__")


def _describe(value: object) -> str:
    return f"{value!r} (type {type(value).__name__})"


# Upper bound on any single duration (and, separately, on the summed horizon
# -- see the horizon check in schedule() below) that this library will hand
# to CP-SAT.
#
# CP-SAT's domains are documented as 64-bit integers, and `cp_model.INT_MAX`
# (== 2**63 - 1, i.e. INT64_MAX) is the literal ceiling the Python binding's
# `Domain`/`NewIntVar` will accept without raising -- but accepting a bound is
# not the same as the *solver* handling it correctly. Empirically bisecting
# against this exact ortools build (a trivial one-job model: NewIntVar(0, v),
# an interval of duration v, AddMaxEquality + Minimize, then solver.Solve),
# solves go OPTIMAL up to v == 2305843008682131765 and flip to status
# MODEL_INVALID by v == 2305843009380623696 -- a boundary that straddles
# exactly `cp_model.INT_MAX // 4` (== 2**61 - 1 == 2305843009213693951).
# That is consistent with CP-SAT reserving the top two bits of its int64
# domains as headroom so its internal presolve/propagators (which sum and
# compare variable bounds, e.g. via AddMaxEquality/AddCumulative) can't
# silently overflow even when two near-maximal bounds are combined.
#
# We therefore use `cp_model.INT_MAX // 4` -- derived from the library's own
# published constant rather than a hardcoded literal, so this tracks any
# future ortools build that changes INT_MAX -- as the safe ceiling. It sits
# comfortably inside the empirically-solvable region above (not merely below
# the raw int64 ceiling that only Domain's constructor cares about), with the
# same margin CP-SAT's own internals rely on.
_MAX_SAFE_DOMAIN = cp_model.INT_MAX // 4


# Upper bound this library will pass as `max_parallel` (the capacity argument
# of the single, model-wide `AddCumulative` constraint -- see the module
# docstring). This is NOT the same bound as `_MAX_SAFE_DOMAIN` above, and
# deliberately not reused blindly: `_MAX_SAFE_DOMAIN` bounds a value that
# becomes (or is derived by summing/comparing) an interval/domain bound --
# `duration`, and transitively the `horizon` used for every start/end IntVar
# and the makespan IntVar. `max_parallel` is a different kind of quantity: a
# single scalar capacity that CP-SAT's cumulative propagator compares against
# the SUM of concurrently-running jobs' demands (each demand is 1 here, and
# that sum is bounded by the job count, never by `horizon`) -- so there is no
# a priori reason the two bounds should coincide, and they in fact do not.
#
# Empirically bisected against this exact ortools build with a minimal
# 3-interval, all-demand-1 `AddCumulative` model (capacity `v`, otherwise
# unconstrained -- see the derivation script this comment describes, not
# checked in, since it is a one-time probe rather than a test the library
# needs to keep re-running): solves go OPTIMAL up to
# v == 4611686018427387903 and flip to solver status MODEL_INVALID at
# v == 4611686018427387904 (== 2**62) -- an exact, non-straddling boundary
# (unlike `_MAX_SAFE_DOMAIN`'s, which straddled a region rather than landing
# on a single value), and one that lands exactly on `cp_model.INT_MAX // 2`.
# That is consistent with a cumulative capacity needing only ONE bit of
# headroom against int64 overflow (a scalar compared against a demand-sum),
# versus the two bits duration/horizon values reserve for the additive
# combinations `_MAX_SAFE_DOMAIN`'s derivation describes. Above that, ortools'
# own argument marshalling raises a raw, undocumented pybind11 RuntimeError
# once `v` no longer fits in an int64 at all (v >= 2**63) -- caught by this
# same upper-bound check either way, so callers never see that raw exception.
#
# We considered, and rejected, a tighter "practical" bound derived from
# `len(jobs)` (a `max_parallel` far beyond the job count can never actually
# constrain anything, since no more than `len(jobs)` jobs can ever run
# concurrently regardless of the capacity given). We do NOT enforce that: a
# caller legitimately may not know (or care) how many jobs a given call has
# -- e.g. a fixed worker-pool-size config reused across many differently
# sized job batches -- and such a `max_parallel` is harmless, not an error,
# for any batch smaller than it. Rejecting it would turn a no-op value into a
# spurious ValueError. The bound below exists solely to keep `max_parallel`
# inside the region CP-SAT itself can actually solve correctly.
_MAX_SAFE_MAX_PARALLEL = cp_model.INT_MAX // 2


def _validate_numeric_param(
    value: object,
    *,
    name: str,
    kind_noun: str,
    integral: bool,
    positive_desc: str,
    prefix: str = "",
    upper_bound: Optional[int] = None,
    upper_bound_message: Optional[Callable[[object], str]] = None,
) -> float:
    """Single shared gate for EVERY numeric parameter this library accepts
    (``duration``, ``max_parallel``, ``time_limit``) -- the structural fix for
    a defect shape that recurred four review rounds running: a validation
    property (most recently ``math.isfinite``) got added for one numeric
    parameter and never swept to its siblings, because each parameter had its
    own hand-written, independently-evolving validation code. Routing all
    three through this one function means a future property added HERE
    applies to all three simultaneously, by construction -- there is no
    longer a sibling left to forget.

    Checks, in this order, each raising a clear ``ValueError`` naming
    ``name`` and the ill-formed value (never a raw ``TypeError``/
    ``OverflowError``/generic message escaping from deep inside ``round()``,
    ortools' own argument marshalling, or CP-SAT's solver):

      1. Not a ``bool`` -- ``bool`` is an ``int`` subclass in Python, so a
         stray JSON ``true``/``false`` landing in a numeric field would
         otherwise silently pass as 0/1, which is essentially always a
         mistake, not a deliberate value.
      2. Is the right general KIND of number, via the ``__index__``
         (``integral=True``, exact-integer types) or ``__float__``
         (``integral=False``, real/float-like types) protocol --
         `_is_exact_integer`/`_is_real_number`. Deliberately protocol-based,
         not an enumeration of specific types: see those two functions'
         docstrings for why (the exact bug class this consolidation exists
         to stop recurring).
      3. Finite: `math.isfinite` on the value's float representation, BEFORE
         any round()/comparison logic runs on it. This is the property that
         was missing for ``time_limit`` (a NaN/Infinity `--time-limit` used
         to reach CP-SAT directly, producing solver status ``MODEL_INVALID``
         misreported as "no feasible schedule found ... try increasing
         --time-limit") -- it is now checked HERE, once, for every numeric
         parameter, rather than per-parameter.
      4. Positive (``value > 0``): correct for all three current callers --
         duration must be >0, time_limit must be >0, and max_parallel being
         integral makes ">=1" and ">0" equivalent, so no separate threshold
         parameter is needed.
      5. Optional upper bound, compared via the ORIGINAL value's exact
         `__index__` value when it is integer-like rather than its `float()`
         conversion -- see the comment at the call site in
         `_validate_duration_value` for why (float's 53-bit mantissa can
         silently round a huge int near the boundary).

    Args:
        value: The raw, untrusted value to validate.
        name: The parameter's name, used in every error message (e.g.
            ``"duration"``, ``"max_parallel"``, ``"time_limit"``).
        kind_noun: How to describe the expected general kind in the
            wrong-kind message (e.g. ``"a number"``, ``"an integer"``).
        integral: True to require the `__index__` protocol (exact integers);
            False to require the `__float__` protocol (real numbers,
            including integers).
        positive_desc: How to describe the positivity requirement in the
            not-positive message (e.g. ``"positive"``, ``"a positive
            integer"``, ``"a positive number of seconds"``).
        prefix: Optional message prefix (e.g. ``f"job {job_id!r}: "`` for
            duration, which is per-job; empty for the schedule()-level
            max_parallel/time_limit parameters, which are not).
        upper_bound: Optional inclusive upper bound; omitted/None to skip
            the check entirely (max_parallel and time_limit have none today).
        upper_bound_message: Required iff `upper_bound` is given -- a
            callable from the original `value` to the exact ValueError
            message to raise when it is exceeded (lets each caller keep its
            own wording/context, e.g. duration's job id and _MAX_SAFE_DOMAIN
            derivation).

    Returns:
        The value's float representation, once fully validated.
    """
    if isinstance(value, bool):
        raise ValueError(f"{prefix}{name} must be {kind_noun}, got {_describe(value)}")

    is_right_kind = _is_exact_integer(value) if integral else _is_real_number(value)
    if not is_right_kind:
        raise ValueError(f"{prefix}{name} must be {kind_noun}, got {_describe(value)}")

    try:
        float_value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{prefix}{name} must be {kind_noun}, got {_describe(value)}") from exc

    if not math.isfinite(float_value):
        raise ValueError(f"{prefix}{name} must be a finite number, got {_describe(value)}")

    if float_value <= 0:
        raise ValueError(f"{prefix}{name} must be {positive_desc}, got {_describe(value)}")

    if upper_bound is not None:
        # Compare the ORIGINAL `value` against the (int) bound via its exact
        # `__index__` value when it is an integer-like type (see
        # `_is_exact_integer` above for why that is the right test, rather
        # than the `float_value` computed above: Python ints have arbitrary
        # precision, but `float()` only has 53 bits of mantissa, so
        # converting a large int to float first can silently round it --
        # e.g. float(_MAX_SAFE_DOMAIN) is already itself rounded UP past the
        # true integer value, which would make an exactly-at-the-limit
        # integer duration compare as "too large" when it is not. This
        # applies to ANY __index__-supporting type (plain int, numpy.int64,
        # an IntEnum, a custom int subclass, ...), not just `int` itself --
        # comparing the exact `__index__()` value directly against another
        # int is exact; comparing an original float `value` against the int
        # bound is also exact (CPython's cross-type int/float rich
        # comparisons are precision-safe), so only the "integer-like value
        # laundered through `float_value`" case needed avoiding.
        magnitude = value.__index__() if _is_exact_integer(value) else float_value
        if magnitude > upper_bound:
            raise ValueError(upper_bound_message(value))

    return float_value


def _validate_duration_value(duration: object, job_id: object) -> float:
    """Validate a raw duration value and return it as a float. Raises a clear
    ValueError naming the job for anything that is not a real, finite,
    positive number representable in CP-SAT's usable domain.

    Thin, duration-specific wrapper around the shared
    `_validate_numeric_param` gate (kind/finite/positive checks -- the
    consolidation that ensures a property added there, like the
    `math.isfinite` check, automatically applies to `max_parallel` and
    `time_limit` too, not just `duration`), adding only what is genuinely
    duration-specific: the per-job message prefix and the upper-bound check
    against `_MAX_SAFE_DOMAIN`.

    The upper-bound check below is a *per-job* guard only: it catches any
    single duration too large for CP-SAT's domain (whether that surfaces as
    an outright TypeError from ortools' Domain constructor for astronomically
    large values, or a silently-wrong MODEL_INVALID solver status for values
    that fit int64 but not CP-SAT's real usable range -- see
    `_MAX_SAFE_DOMAIN` above). It does NOT catch many valid-individually
    durations whose *sum* (the scheduling horizon -- see schedule()'s own
    horizon computation) overflows; that is a separate check made once all
    of a call's durations are known, in schedule() itself.
    """

    def _upper_bound_message(value: object) -> str:
        return (
            f"job {job_id!r}: duration {_describe(value)} exceeds the maximum duration this "
            f"library will pass to the CP-SAT solver ({_MAX_SAFE_DOMAIN}, derived from "
            "cp_model.INT_MAX // 4 -- see _MAX_SAFE_DOMAIN in makespan_scheduler/model.py); "
            "values beyond this either overflow CP-SAT's usable domain (solver status "
            "MODEL_INVALID) or are rejected outright by ortools itself"
        )

    return _validate_numeric_param(
        duration,
        name="duration",
        kind_noun="a number",
        integral=False,
        positive_desc="positive",
        prefix=f"job {job_id!r}: ",
        upper_bound=_MAX_SAFE_DOMAIN,
        upper_bound_message=_upper_bound_message,
    )


@dataclass(frozen=True)
class Job:
    """A single unit of work.

    Attributes:
        id: Unique identifier for the job -- a hashable JSON scalar: a string
            or an int (not a bool, list, dict, or None).
        resources: The resources this job touches. Two jobs that share at least
            one resource cannot run concurrently. Typically file paths, but any
            hashable JSON scalar identifying a mutually-exclusive resource works
            (a lock name, a database row id, etc) -- a string or an int, same
            rule as `id`.
        duration: Positive relative cost/time for this job, in abstract integer
            units (not necessarily wall-clock seconds). Defaults to 1. Must be
            a real, finite, positive number (NaN/Infinity are rejected);
            non-integers are rounded to the nearest integer (minimum 1) when
            the model is built — see the module docstring for how to handle
            sub-integer precision.
    """

    id: IdType
    resources: Sequence[IdType] = field(default_factory=tuple)
    duration: float = 1

    def __post_init__(self) -> None:
        # This runs on every Job construction regardless of caller -- both the
        # job_from_dict() JSON boundary below and any direct library use of
        # Job(...) -- so it is the true single validating gate for the class,
        # not just an adjunct to job_from_dict's own checks.
        if not _is_hashable_scalar(self.id):
            raise ValueError(f"job id must be a string or int, got {_describe(self.id)}")

        # A bare string is technically a Sequence[str] too, but iterating it
        # per-character is never what a caller means by "resources" -- reject
        # it alongside the other non-list/tuple shapes (None, a number, etc.)
        # that would otherwise crash deep inside schedule()'s constraint
        # construction with an opaque TypeError instead of a clear message.
        if not isinstance(self.resources, (list, tuple)):
            raise ValueError(
                f"job {self.id!r}: resources must be a list of resource names, "
                f"got {_describe(self.resources)}"
            )
        for r in self.resources:
            if not _is_hashable_scalar(r):
                raise ValueError(
                    f"job {self.id!r}: each resource must be a string or int, got {_describe(r)}"
                )

        # Snapshot into an immutable tuple. `self.resources` may have been
        # handed in as a caller-owned `list` -- without this, the Job would
        # store a live reference to that list, so a caller mutating it AFTER
        # construction (e.g. `shared = ['r1']; Job(..., resources=shared);
        # shared.append('r2')`) would silently change this "frozen" Job's
        # resources out from under it, defeating both the immutability the
        # `frozen=True` dataclass promises and the resource-conflict model
        # built from it. `object.__setattr__` is required here because the
        # dataclass is frozen (plain attribute assignment is disallowed after
        # `__init__`, `__post_init__` included).
        if not isinstance(self.resources, tuple):
            object.__setattr__(self, "resources", tuple(self.resources))

        if self.duration is None:
            # Historical leniency preserved: an explicit JSON "duration": null
            # (or Job(..., duration=None) from direct library use) means "use
            # the default", same as omitting the field entirely.
            object.__setattr__(self, "duration", 1)
        else:
            _validate_duration_value(self.duration, self.id)


@dataclass(frozen=True)
class JobResult:
    """Computed schedule for a single job."""

    id: str
    start: int
    end: int


@dataclass(frozen=True)
class ScheduleResult:
    """The full output of a schedule() call.

    Attributes:
        makespan: The completion time (end) of the last-finishing job.
        optimal: True iff the solver proved this makespan is minimal within the
            given time limit. False means this is the best feasible schedule
            found before the time limit expired, with no optimality guarantee.
        jobs: Per-job start/end times, in the order the input jobs were given.
        batches: Ordered "waves" of job ids that share an identical start time
            — see the module-level ``derive_batches`` docstring for exactly how
            these are computed and what caveats apply when durations vary.
    """

    makespan: int
    optimal: bool
    jobs: List[JobResult]
    batches: List[List[str]]

    def to_dict(self) -> dict:
        return {
            "makespan": self.makespan,
            "optimal": self.optimal,
            "jobs": [{"id": j.id, "start": j.start, "end": j.end} for j in self.jobs],
            "batches": [list(b) for b in self.batches],
        }


def job_from_dict(entry: object, index: int) -> Job:
    """Build a ``Job`` from a raw, UNTRUSTED value (e.g. one entry of a parsed
    JSON ``"jobs"`` array) -- the single, comprehensive boundary a raw job
    dict must pass through before a ``Job`` can ever be constructed. Validates
    every field explicitly and in order, each with its own clear
    ``ValueError``, so a malformed entry of ANY shape (not just the specific
    shapes anyone has thought to enumerate) can never reach a raw
    ``KeyError``/``TypeError``/``AttributeError``/``OverflowError`` escaping
    from deep inside dict access, `Job` construction, or CP-SAT model
    construction. ``Job.__post_init__`` re-validates id/resources/duration
    once more when constructed below -- deliberate layered defense, not
    duplication for its own sake, since it also protects any caller who
    constructs a ``Job`` directly rather than through this function.

    Args:
        entry: The raw job entry (must be a dict containing at least 'id').
        index: The entry's position in the input array, used to identify it
            in error messages before 'id' itself is known to be usable.
    """
    if not isinstance(entry, dict):
        raise ValueError(
            f"job at index {index}: expected a JSON object for a job entry, got {_describe(entry)}"
        )
    if "id" not in entry:
        raise ValueError(f"job at index {index}: missing required 'id' field")
    job_id = entry["id"]
    if not _is_hashable_scalar(job_id):
        raise ValueError(f"job at index {index}: 'id' must be a string or int, got {_describe(job_id)}")

    resources = entry.get("resources", [])
    if not isinstance(resources, (list, tuple)):
        raise ValueError(
            f"job {job_id!r}: resources must be a list of resource names, got {_describe(resources)}"
        )
    for r in resources:
        if not _is_hashable_scalar(r):
            raise ValueError(f"job {job_id!r}: each resource must be a string or int, got {_describe(r)}")

    duration = entry.get("duration", 1)
    if duration is not None:
        _validate_duration_value(duration, job_id)

    return Job(id=job_id, resources=resources, duration=duration)


def _to_int_duration(duration: float, job_id: object) -> int:
    # By the time schedule() reaches this point every Job in play has already
    # passed Job.__post_init__'s own duration validation (job_from_dict's
    # early check is an additional, earlier-firing layer on top of that same
    # gate) -- so this re-validates as cheap defense in depth, not as the
    # primary enforcement point.
    value = _validate_duration_value(duration, job_id)
    # Take the ORIGINAL `duration`'s exact `__index__()` value when it is
    # integer-like (see `_is_exact_integer` above), not the
    # `value = float(duration)` computed above: for durations near
    # `_MAX_SAFE_DOMAIN` (~2**61), float's 53-bit mantissa can't represent
    # the integer exactly, so `round(float(duration))` can silently return a
    # different (and, near the ceiling, LARGER) int than the one that was
    # actually validated -- which would let a duration that passed the
    # `_validate_duration_value` bound check re-emerge here a few hundred
    # units past `_MAX_SAFE_DOMAIN` and defeat the very check meant to keep
    # it out. This applies to any __index__-supporting type, not just plain
    # `int` -- `__index__()` is already exact and loses no precision, so use
    # it directly rather than routing through `float()`/`round()`.
    rounded = duration.__index__() if _is_exact_integer(duration) else round(value)
    return max(1, int(rounded))


def derive_batches(jobs: List[JobResult]) -> List[List[str]]:
    """Group scheduled jobs into ordered "waves" by identical start time.

    A batch is the set of job ids that all start at the same instant — the
    practical artifact an orchestrator uses to actually dispatch work ("wave 1:
    launch these N jobs in parallel; wait for the wave's dependents; wave 2: ...").

    This is exact when every job in the input has the same duration (or when
    the caller only cares about *launch* order): every job in a batch is,
    by construction, safe to start together, since the CP-SAT constraints
    guarantee no two conflicting jobs share a start-inclusive/end-exclusive
    interval, and grouping by start time never merges two jobs whose
    intervals overlap without one containing the other's start (NoOverlap
    forbids that overlap outright).

    Caveat for variable-duration schedules: jobs in the same batch may finish
    at different times (e.g. batch = [A (duration 1), B (duration 5)], both
    starting at t=0). The batch says "these can be *launched* together", not
    "these all finish together" — for exact per-job completion, use the
    start/end fields, which are ground truth. Batches are an orchestration
    convenience/approximation on top of that ground truth, not a replacement
    for it.
    """

    by_start: Dict[int, List[str]] = {}
    for j in jobs:
        by_start.setdefault(j.start, []).append(j.id)
    return [by_start[t] for t in sorted(by_start.keys())]


def schedule(
    jobs: Sequence[Job],
    max_parallel: Optional[int] = None,
    time_limit: Optional[float] = None,
) -> ScheduleResult:
    """Compute a minimum-makespan schedule for ``jobs``.

    Args:
        jobs: The jobs to schedule. Job ids must be unique.
        max_parallel: If given, the maximum number of jobs that may run
            simultaneously at any instant (a worker-pool concurrency cap).
            Must be a positive integer. If omitted, only the resource-conflict
            constraints apply (unbounded concurrency, aside from resource
            conflicts).
        time_limit: Wall-clock seconds to allow the CP-SAT solver. If the
            solver does not prove optimality within this limit, the best
            feasible schedule found so far is returned with
            ``ScheduleResult.optimal = False``. If omitted, the solver runs
            until it proves optimality (no artificial cap).

    Returns:
        A ScheduleResult with the computed schedule.

    Raises:
        ValueError: on invalid input (duplicate job ids, non-positive
            duration, non-positive max_parallel, non-positive time_limit).
        RuntimeError: if the solver could not find any feasible schedule at
            all within the time limit (distinct from "found a schedule but
            couldn't prove it optimal" — that case is returned normally with
            ``optimal=False``).
    """

    jobs = list(jobs)

    seen_ids = set()
    for j in jobs:
        if j.id in seen_ids:
            raise ValueError(f"duplicate job id: {j.id!r}")
        seen_ids.add(j.id)

    if max_parallel is not None:
        # Routed through the shared `_validate_numeric_param` gate (see its
        # docstring) rather than a hand-written check of its own -- this is
        # the consolidation point: any validation property added to that one
        # function (e.g. the `math.isfinite` check that `time_limit` below
        # was, until this change, missing) now applies to `max_parallel` too,
        # automatically, with no separate call site to remember to update.
        #
        # `upper_bound=_MAX_SAFE_MAX_PARALLEL` closes the gap `duration`'s
        # call site (see `_validate_duration_value`) already had and this one
        # did not: without it, a `max_parallel` in
        # [2**61, cp_model.INT_MAX] reached `AddCumulative` and came back
        # solver status MODEL_INVALID, misreported below as "no feasible
        # schedule found ... try increasing --time-limit"; a `max_parallel`
        # >= 2**63 crashed with a raw, undocumented pybind11 RuntimeError
        # instead. See `_MAX_SAFE_MAX_PARALLEL`'s own comment for the
        # empirical derivation of this bound (deliberately NOT the same
        # value as duration's `_MAX_SAFE_DOMAIN` -- the two guard different
        # kinds of CP-SAT quantities).
        def _max_parallel_upper_bound_message(value: object) -> str:
            return (
                f"max_parallel {_describe(value)} exceeds the maximum this library will pass "
                f"to the CP-SAT solver ({_MAX_SAFE_MAX_PARALLEL}, derived from "
                "cp_model.INT_MAX // 2 -- see _MAX_SAFE_MAX_PARALLEL in "
                "makespan_scheduler/model.py); values beyond this either overflow CP-SAT's "
                "usable domain (solver status MODEL_INVALID) or are rejected outright by "
                "ortools itself"
            )

        _validate_numeric_param(
            max_parallel,
            name="max_parallel",
            kind_noun="an integer",
            integral=True,
            positive_desc="a positive integer",
            upper_bound=_MAX_SAFE_MAX_PARALLEL,
            upper_bound_message=_max_parallel_upper_bound_message,
        )

    if time_limit is not None:
        # Same shared gate as `max_parallel` above. This is the fix for the
        # bug this change set out to close: `time_limit=float('nan')` (or
        # `float('inf')`) used to reach CP-SAT directly (only `duration` had
        # an explicit `math.isfinite` check), producing solver status
        # MODEL_INVALID misreported as "no feasible schedule found ... try
        # increasing --time-limit". Routing through `_validate_numeric_param`
        # -- the same function `duration`'s finite check now also runs
        # through -- closes it for `time_limit` and `max_parallel` at once,
        # and for any future numeric parameter this library adds.
        #
        # No `upper_bound` here, unlike `duration`/`max_parallel`, and this
        # is a deliberate finding, not an oversight: `time_limit` never
        # becomes a CP-SAT model variable/domain value at all -- it only
        # ever reaches `solver.parameters.max_time_in_seconds`, a solver
        # *parameter* ortools sets directly on its C++ SolverParameters proto
        # (a plain double field), not a value CP-SAT's presolve/propagators
        # combine with other model bounds the way duration and max_parallel
        # are. Empirically probing this exact ortools build by setting
        # `max_time_in_seconds` to 1e6, 1e18, 1e300, 1e308, and
        # `float('inf')` against a trivial solvable model: every one of
        # those assignments succeeds and the model still solves to OPTIMAL,
        # with no MODEL_INVALID and no raw exception at any magnitude tried
        # (the `math.isfinite` check above already rules out the one value,
        # `inf`, that would otherwise turn "run until proven optimal" into
        # "run forever" -- a real but distinct failure mode from the
        # MODEL_INVALID-misreport/crash this comment is about). So an
        # absurdly large `time_limit` is handled safely regardless of
        # magnitude; no upper bound is needed here.
        _validate_numeric_param(
            time_limit,
            name="time_limit",
            kind_noun="a number",
            integral=False,
            positive_desc="a positive number of seconds",
        )

    if not jobs:
        return ScheduleResult(makespan=0, optimal=True, jobs=[], batches=[])

    durations = [_to_int_duration(j.duration, j.id) for j in jobs]
    horizon = sum(durations)

    # Distinct from _validate_duration_value's per-job upper-bound check: each
    # individual duration can be well within `_MAX_SAFE_DOMAIN` and still have
    # the *sum* (the scheduling horizon -- the upper bound this function gives
    # every job's start/end IntVar and the makespan variable itself, since a
    # fully-serial schedule is always feasible) overflow it once enough jobs
    # accumulate. Checked here, once every job's duration is known, rather
    # than per-job, because no single job's value is at fault -- it's the
    # combination.
    if horizon > _MAX_SAFE_DOMAIN:
        raise ValueError(
            f"total scheduling horizon (sum of all {len(jobs)} job durations) is {horizon}, "
            f"which exceeds the maximum this library will pass to the CP-SAT solver "
            f"({_MAX_SAFE_DOMAIN}, derived from cp_model.INT_MAX // 4 -- see _MAX_SAFE_DOMAIN "
            "in makespan_scheduler/model.py); reduce durations or split the job set into "
            "smaller batches"
        )

    model = cp_model.CpModel()

    starts = []
    ends = []
    intervals = []
    for i, (j, dur) in enumerate(zip(jobs, durations)):
        start = model.NewIntVar(0, horizon, f"start_{i}")
        end = model.NewIntVar(0, horizon, f"end_{i}")
        interval = model.NewIntervalVar(start, dur, end, f"interval_{i}_{j.id}")
        starts.append(start)
        ends.append(end)
        intervals.append(interval)

    # Per-resource NoOverlap: group job indices by resource, one NoOverlap
    # constraint per resource touched by 2+ jobs.
    resource_to_indices: Dict[IdType, List[int]] = {}
    for i, j in enumerate(jobs):
        # A job listing the same resource twice must not make its own interval
        # appear twice in a single NoOverlap constraint (an interval can never
        # be non-overlapping with itself) — dedupe per job.
        for r in set(j.resources):
            resource_to_indices.setdefault(r, []).append(i)

    for resource, indices in resource_to_indices.items():
        if len(indices) < 2:
            continue
        model.AddNoOverlap([intervals[i] for i in indices])

    # Global concurrency cap via cumulative: every job consumes 1 unit of a
    # capacity-max_parallel "worker pool" resource for its whole duration.
    if max_parallel is not None:
        demands = [1] * len(jobs)
        # Coerce to a plain `int` via `__index__` (through the `int()`
        # builtin) before handing it to ortools: `max_parallel` has already
        # been validated as integer-LIKE (see `_is_exact_integer` above,
        # which accepts `numpy.int64` etc, not just plain `int`), but the
        # ortools Python binding's own argument marshalling is not guaranteed
        # to accept every `__index__`-supporting type the way this library's
        # own validation does -- so normalize to `int` here, the same way
        # `_to_int_duration` normalizes `duration` before it reaches any
        # CP-SAT call.
        model.AddCumulative(intervals, demands, int(max_parallel))

    makespan = model.NewIntVar(0, horizon, "makespan")
    model.AddMaxEquality(makespan, ends)
    model.Minimize(makespan)

    solver = cp_model.CpSolver()
    if time_limit is not None:
        solver.parameters.max_time_in_seconds = float(time_limit)
    solver.parameters.num_search_workers = 8

    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(
            "no feasible schedule found within the given time limit "
            f"(solver status: {solver.StatusName(status)}); "
            "try increasing --time-limit"
        )

    optimal = status == cp_model.OPTIMAL

    job_results = [
        JobResult(id=j.id, start=solver.Value(starts[i]), end=solver.Value(ends[i]))
        for i, j in enumerate(jobs)
    ]
    batches = derive_batches(job_results)

    return ScheduleResult(
        makespan=solver.Value(makespan),
        optimal=optimal,
        jobs=job_results,
        batches=batches,
    )
