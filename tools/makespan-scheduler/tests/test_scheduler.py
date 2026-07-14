import decimal
import fractions
import json
import os
import random
import subprocess
import sys

import numpy
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from makespan_scheduler import Job, schedule
from makespan_scheduler.model import (
    _MAX_SAFE_DOMAIN,
    _MAX_SAFE_MAX_PARALLEL,
    _validate_duration_value,
    _validate_numeric_param,
    derive_batches,
    job_from_dict,
    JobResult,
)

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
SCHEDULER_PY = os.path.join(REPO_ROOT, "scheduler.py")


def _overlaps(a, b):
    return a.start < b.end and b.start < a.end


def test_independent_jobs_run_fully_in_parallel():
    jobs = [Job(id=f"j{i}", resources=[f"r{i}"], duration=3) for i in range(5)]
    result = schedule(jobs)
    assert result.optimal is True
    # No shared resources at all -> every job can start at time 0.
    assert all(j.start == 0 for j in result.jobs)
    assert result.makespan == 3
    assert len(result.batches) == 1
    assert set(result.batches[0]) == {j.id for j in jobs}


def test_chain_sharing_one_resource_fully_serializes():
    # All jobs touch the same single resource -> pairwise conflict for all,
    # so they must run one after another with no overlap.
    jobs = [Job(id=f"j{i}", resources=["shared"], duration=2) for i in range(4)]
    result = schedule(jobs)
    assert result.optimal is True
    assert result.makespan == 8  # 4 jobs * duration 2, fully serial

    by_id = {j.id: j for j in result.jobs}
    scheduled = list(by_id.values())
    for i in range(len(scheduled)):
        for k in range(i + 1, len(scheduled)):
            assert not _overlaps(scheduled[i], scheduled[k])

    # Fully serial also means every job lands in its own batch.
    assert len(result.batches) == 4


def test_max_parallel_cap_respected_beyond_resource_constraints():
    # 6 totally independent jobs (no shared resources at all) would love to
    # all run at t=0, but max_parallel=2 must still cap concurrency.
    jobs = [Job(id=f"j{i}", resources=[f"r{i}"], duration=1) for i in range(6)]
    result = schedule(jobs, max_parallel=2)
    assert result.optimal is True

    # At every integer instant in [0, makespan), no more than 2 jobs may be
    # running concurrently.
    for t in range(result.makespan):
        running = sum(1 for j in result.jobs if j.start <= t < j.end)
        assert running <= 2

    # With 6 unit jobs and capacity 2, minimum makespan is 3.
    assert result.makespan == 3


def test_disconnected_components_schedule_independently():
    # Two separate conflict-chains (A-B share a resource; C-D share a
    # different resource) with no cross-links and no max_parallel: the two
    # chains should schedule concurrently, not wait on each other.
    jobs = [
        Job(id="a", resources=["res1"], duration=2),
        Job(id="b", resources=["res1"], duration=3),
        Job(id="c", resources=["res2"], duration=4),
        Job(id="d", resources=["res2"], duration=1),
    ]
    result = schedule(jobs)
    assert result.optimal is True

    by_id = {j.id: j for j in result.jobs}
    # Within each component, the pair must not overlap.
    assert not _overlaps(by_id["a"], by_id["b"])
    assert not _overlaps(by_id["c"], by_id["d"])

    # The two components are independent: the makespan should be the max of
    # each component's own serial time (5 and 5), not their sum (10).
    assert result.makespan == 5


def test_batches_internally_consistent_with_start_end_times():
    jobs = [
        Job(id="a", resources=["r1"], duration=2),
        Job(id="b", resources=["r1"], duration=1),
        Job(id="c", resources=["r2"], duration=5),
    ]
    result = schedule(jobs)

    # Reconstruct batches independently from the ground-truth start/end times
    # and check it matches what schedule() returned.
    recomputed = derive_batches(result.jobs)
    assert recomputed == result.batches

    # Every job id appears in exactly one batch.
    all_ids_in_batches = [jid for batch in result.batches for jid in batch]
    assert sorted(all_ids_in_batches) == sorted(j.id for j in result.jobs)

    # Every job within a batch genuinely starts at the same instant.
    by_id = {j.id: j for j in result.jobs}
    for batch in result.batches:
        starts = {by_id[jid].start for jid in batch}
        assert len(starts) == 1

    # Batches are ordered by increasing start time.
    batch_starts = [by_id[batch[0]].start for batch in result.batches]
    assert batch_starts == sorted(batch_starts)
    assert len(set(batch_starts)) == len(batch_starts)


def test_low_time_limit_on_large_instance_returns_valid_nonoptimal_schedule():
    # Build a large, hard instance: many jobs (150), each touching 2-4
    # resources drawn from a small pool of 21 possible resource names, and
    # variable durations (1-15). The dense overlap (many jobs per resource,
    # many resources per job) makes proving the *optimal* makespan
    # combinatorially hard, while a tight (but low) time limit still leaves
    # the solver enough time to find *a* feasible schedule. This deterministic
    # seed/shape combination was empirically checked to reliably still be
    # unproven (optimal=False) at time_limit=0.1s on this machine, while
    # comfortably finding a feasible solution (not raising RuntimeError).
    random.seed(1)
    n = 150
    jobs = []
    for i in range(n):
        k = random.randint(2, 4)
        resources = list({f"r{random.randint(0, 20)}" for _ in range(k)})
        jobs.append(Job(id=f"j{i}", resources=resources, duration=random.randint(1, 15)))

    result = schedule(jobs, time_limit=0.1)

    assert result.optimal is False

    # Even though it's not proven optimal, it must still be a *valid*
    # schedule: no two jobs sharing a resource may overlap.
    by_id = {j.id: j for j in result.jobs}
    resource_to_jobs = {}
    for j in jobs:
        for r in j.resources:
            resource_to_jobs.setdefault(r, []).append(j.id)
    for r, job_ids in resource_to_jobs.items():
        if len(job_ids) < 2:
            continue
        for a in range(len(job_ids)):
            for b in range(a + 1, len(job_ids)):
                assert not _overlaps(by_id[job_ids[a]], by_id[job_ids[b]])

    assert result.makespan >= max(j.end for j in result.jobs)


def test_duplicate_resource_within_a_single_job_does_not_break_feasibility():
    # A job listing the same resource twice must not make its own interval
    # collide with itself in a NoOverlap constraint (regression test for a
    # bug found during development: this made otherwise-trivial instances
    # spuriously INFEASIBLE).
    jobs = [
        Job(id="a", resources=["r1", "r1", "r2"], duration=2),
        Job(id="b", resources=["r2"], duration=1),
    ]
    result = schedule(jobs)
    assert result.optimal is True
    by_id = {j.id: j for j in result.jobs}
    assert not _overlaps(by_id["a"], by_id["b"])


def test_duplicate_job_id_rejected():
    with pytest.raises(ValueError):
        schedule([Job(id="x", resources=[]), Job(id="x", resources=[])])


def test_invalid_max_parallel_rejected():
    with pytest.raises(ValueError):
        schedule([Job(id="x", resources=[])], max_parallel=0)


def test_empty_job_list():
    result = schedule([])
    assert result.makespan == 0
    assert result.optimal is True
    assert result.jobs == []
    assert result.batches == []


def test_job_with_none_resources_rejected_cleanly():
    # Regression: a job dict with "resources": null (JSON null -> Python
    # None) used to crash deep inside schedule()'s constraint construction
    # with an unhandled TypeError ('NoneType' object is not iterable)
    # instead of a clean ValueError.
    with pytest.raises(ValueError, match="resources"):
        Job(id="x", resources=None)


# --- Duration upper-bound regression tests -----------------------------
#
# Regression coverage for two bugs found via astronomically large durations:
#
#   - duration=4_000_000_000_000_000_000 (~4e18) caused CP-SAT solver status
#     MODEL_INVALID (the domain was too large for the solver to actually use,
#     despite being under raw int64 max), which schedule() misreported as
#     RuntimeError("no feasible schedule found within the given time limit
#     ... try increasing --time-limit") -- misleading, since no time limit
#     fixes an invalid model.
#   - duration=1e300 escaped entirely as a raw, undocumented TypeError from
#     ortools' own Domain constructor (rejecting an out-of-range int), which
#     violates the library's documented "raises ValueError or RuntimeError"
#     contract.
#
# Both are now caught by an explicit upper-bound check in
# _validate_duration_value (per-job) and in schedule() itself (summed
# horizon), against `_MAX_SAFE_DOMAIN` -- see the derivation comment on that
# constant in makespan_scheduler/model.py.


def test_duration_just_under_the_limit_still_schedules():
    # A single job at exactly _MAX_SAFE_DOMAIN must still produce a real,
    # valid, optimal schedule -- the boundary itself is inside the safe
    # range, not excluded by an off-by-one in the check.
    result = schedule([Job(id="a", resources=[], duration=_MAX_SAFE_DOMAIN)])
    assert result.optimal is True
    assert result.makespan == _MAX_SAFE_DOMAIN
    assert result.jobs[0].start == 0
    assert result.jobs[0].end == _MAX_SAFE_DOMAIN


def test_duration_just_over_the_limit_raises_clean_value_error():
    # One unit past the limit must raise a clean ValueError attributing the
    # problem to the job and naming the limit -- never MODEL_INVALID
    # (surfaced as a misleading RuntimeError) and never a raw TypeError.
    with pytest.raises(ValueError, match="exceeds the maximum duration"):
        schedule([Job(id="a", resources=[], duration=_MAX_SAFE_DOMAIN + 1)])


def test_duration_4e18_raises_value_error_not_misleading_runtime_error():
    # The exact value from the original bug report: previously misreported
    # as RuntimeError("no feasible schedule found ... try increasing
    # --time-limit"), which is actively misleading since no time limit fixes
    # an invalid model.
    with pytest.raises(ValueError, match="exceeds the maximum duration"):
        schedule([Job(id="a", resources=[], duration=4_000_000_000_000_000_000)])


def test_duration_1e300_raises_value_error_not_raw_type_error():
    # The exact value from the original bug report: previously escaped as an
    # undocumented, raw TypeError straight out of ortools' Domain
    # constructor, violating schedule()'s documented ValueError/RuntimeError
    # contract.
    with pytest.raises(ValueError, match="exceeds the maximum duration"):
        schedule([Job(id="a", resources=[], duration=1e300)])


def test_numpy_int64_duration_at_the_limit_schedules_successfully():
    # Regression test for the narrow-enumeration bug: the original fix for
    # the float-53-bit-mantissa rounding issue special-cased
    # `isinstance(duration, int)`, so any OTHER exact-integer-like type --
    # e.g. numpy.int64 -- fell through to the lossy `float(duration)`
    # branch and reproduced the exact bug the fix claimed to close: a
    # duration that is exactly at `_MAX_SAFE_DOMAIN` (and so must schedule)
    # was wrongly REJECTED as "exceeds maximum duration" because
    # float(_MAX_SAFE_DOMAIN) rounds up past the true value. numpy.int64
    # implements `__index__` (same as plain `int`), so it must be treated
    # as an exact integer, not routed through `float()`.
    result = schedule([Job(id="a", resources=[], duration=numpy.int64(_MAX_SAFE_DOMAIN))])
    assert result.optimal is True
    assert result.makespan == _MAX_SAFE_DOMAIN
    assert result.jobs[0].start == 0
    assert result.jobs[0].end == _MAX_SAFE_DOMAIN


def test_numpy_int64_duration_one_over_the_limit_still_raises_value_error():
    # The other side of the same boundary: one past the limit must still be
    # rejected, exactly as it is for a plain int -- the fix must not
    # accidentally widen the accepted range for __index__ types either.
    with pytest.raises(ValueError, match="exceeds the maximum duration"):
        schedule([Job(id="a", resources=[], duration=numpy.int64(_MAX_SAFE_DOMAIN + 1))])


def test_custom_int_subclass_duration_at_the_limit_schedules_successfully():
    # Any int subclass someone might define (e.g. to attach extra metadata
    # to a duration value) must be treated as an exact integer too --
    # `_is_exact_integer` tests the `__index__` protocol generally rather
    # than enumerating specific types, and a plain `int` subclass inherits
    # `__index__` from `int`, so this must work the same as a plain int.
    class MyIntDuration(int):
        pass

    result = schedule([Job(id="a", resources=[], duration=MyIntDuration(_MAX_SAFE_DOMAIN))])
    assert result.optimal is True
    assert result.makespan == _MAX_SAFE_DOMAIN


def test_decimal_duration_at_the_limit_is_rejected_not_silently_wrong():
    # Documented decision: unlike numpy.int64 or an int subclass,
    # decimal.Decimal and fractions.Fraction do NOT implement `__index__`,
    # even though a given instance may hold an exact integral value -- both
    # types can ALSO hold genuinely non-integer values (Decimal("3.5"),
    # Fraction(1, 3)), so "is a Decimal" is not equivalent to "is an
    # integer" the way __index__ support is. Supporting them as exact
    # integers would need an extra "is this instance whole-valued" check,
    # a larger, separate feature this fix deliberately does not add (see
    # `_is_exact_integer`'s docstring in makespan_scheduler/model.py).
    #
    # The consequence, verified here, is that a Decimal held at exactly
    # `_MAX_SAFE_DOMAIN` -- which schedules fine as a plain int or as
    # numpy.int64 -- goes through the same lossy `float()` conversion as
    # any other non-integer numeric type and is rejected by the per-job
    # bound check with a clear, attributed ValueError, never a silent
    # wrong answer or a raw crash.
    with pytest.raises(ValueError, match="exceeds the maximum duration"):
        schedule([Job(id="a", resources=[], duration=decimal.Decimal(_MAX_SAFE_DOMAIN))])


def test_fraction_duration_at_the_limit_is_rejected_not_silently_wrong():
    # Same documented decision as the Decimal case above, for
    # fractions.Fraction.
    with pytest.raises(ValueError, match="exceeds the maximum duration"):
        schedule([Job(id="a", resources=[], duration=fractions.Fraction(_MAX_SAFE_DOMAIN, 1))])


def test_decimal_duration_well_under_the_limit_still_schedules():
    # Decimal/Fraction are not rejected outright -- only the lossy float
    # conversion near the domain boundary is a known, documented limitation.
    # A comfortably-sized Decimal duration must still schedule normally.
    result = schedule([Job(id="a", resources=[], duration=decimal.Decimal(7))])
    assert result.optimal is True
    assert result.makespan == 7


def test_individually_valid_durations_whose_sum_overflows_the_horizon():
    # Distinct code path from the per-job check above: each job's own
    # duration is comfortably under _MAX_SAFE_DOMAIN on its own, but the
    # *horizon* (sum of all durations, which becomes every job's start/end
    # upper bound and the makespan variable's own bound) overflows once both
    # are added together. Neither individual duration triggers the per-job
    # check; only the summed-horizon check in schedule() catches this.
    half_plus_margin = _MAX_SAFE_DOMAIN // 2 + 1000
    assert half_plus_margin <= _MAX_SAFE_DOMAIN  # sanity: each job is valid alone

    with pytest.raises(ValueError, match="total scheduling horizon"):
        schedule(
            [
                Job(id="a", resources=[], duration=half_plus_margin),
                Job(id="b", resources=[], duration=half_plus_margin),
            ]
        )


def test_job_with_non_list_resources_rejected_cleanly():
    # A string or number for "resources" must also be rejected, not just
    # None -- a bare string is iterable (per-character) but never what a
    # caller means by a resource list.
    with pytest.raises(ValueError, match="resources"):
        Job(id="x", resources="not-a-list")
    with pytest.raises(ValueError, match="resources"):
        Job(id="x", resources=5)


def test_job_from_dict_missing_id_rejected_cleanly():
    # Regression: a job entry missing the required "id" key used to crash
    # the CLI with an unhandled KeyError instead of a clean ValueError.
    from makespan_scheduler import job_from_dict

    with pytest.raises(ValueError, match="id"):
        job_from_dict({"resources": ["r1"]}, 0)


def test_job_from_dict_none_resources_rejected_cleanly():
    from makespan_scheduler import job_from_dict

    with pytest.raises(ValueError, match="resources"):
        job_from_dict({"id": "a", "resources": None}, 0)


def test_negative_time_limit_rejected_cleanly():
    # Regression: schedule(jobs, time_limit=-1) used to hand -1 straight to
    # solver.parameters.max_time_in_seconds, producing solver status
    # MODEL_INVALID, which was then misreported as the generic "no feasible
    # schedule found ... try increasing --time-limit" message -- misleading,
    # since the actual problem is an invalid parameter, not a timeout or
    # infeasibility.
    with pytest.raises(ValueError, match="time_limit"):
        schedule([Job(id="x", resources=["r"])], time_limit=-1)


def test_zero_time_limit_rejected_cleanly():
    with pytest.raises(ValueError, match="time_limit"):
        schedule([Job(id="x", resources=["r"])], time_limit=0)


def test_nan_time_limit_rejected_cleanly():
    # Regression: unlike `duration`, `time_limit` had no `math.isfinite`
    # check of its own -- `time_limit=float('nan')` reached CP-SAT directly,
    # producing solver status MODEL_INVALID, which schedule() misreported as
    # RuntimeError("no feasible schedule found ... try increasing
    # --time-limit") -- misleading, since the actual problem is an invalid
    # parameter, not infeasibility. Fixed by routing `time_limit` through the
    # same `_validate_numeric_param` gate `duration`'s finite check already
    # used, rather than adding a fifth hand-written NaN check.
    with pytest.raises(ValueError, match="finite"):
        schedule([Job(id="x", resources=["r"])], time_limit=float("nan"))


def test_infinite_time_limit_rejected_cleanly():
    # Same regression class as the NaN case above, for +/-Infinity.
    with pytest.raises(ValueError, match="finite"):
        schedule([Job(id="x", resources=["r"])], time_limit=float("inf"))
    with pytest.raises(ValueError, match="finite"):
        schedule([Job(id="x", resources=["r"])], time_limit=float("-inf"))


def test_cli_rejects_nan_time_limit_cleanly(tmp_path):
    # CLI-level regression test for the exact bug report this fix addresses:
    # `--time-limit nan` used to reach the solver and get misreported as
    # infeasibility instead of a clean, immediate ValueError.
    proc = _run_cli(
        tmp_path,
        {"jobs": [{"id": "a", "resources": ["r1"]}]},
        extra_args=["--time-limit", "nan"],
    )
    assert proc.returncode == 1
    assert "Traceback" not in proc.stderr
    assert proc.stderr.startswith("scheduler.py: error:")
    assert "time_limit" in proc.stderr
    assert "finite" in proc.stderr
    assert "no feasible schedule" not in proc.stderr


def test_infinite_duration_rejected_cleanly():
    # Regression (round-2 class): duration=Infinity used to reach round()
    # unchecked, raising a bare OverflowError instead of a clean ValueError.
    with pytest.raises(ValueError, match="finite"):
        job_from_dict({"id": "a", "duration": float("inf")}, 0)
    with pytest.raises(ValueError, match="finite"):
        Job(id="a", duration=float("inf"))


def test_nan_duration_rejected_cleanly():
    # Regression (round-2 class): duration=NaN used to reach round() unchecked,
    # raising a generic, job-less ValueError ("cannot convert float NaN to
    # integer") instead of this library's own clearly-worded message.
    with pytest.raises(ValueError, match="finite"):
        job_from_dict({"id": "a", "duration": float("nan")}, 0)
    with pytest.raises(ValueError, match="finite"):
        Job(id="a", duration=float("nan"))


@pytest.mark.parametrize("bad_entry", [1, "not-a-job", None, [1, 2]])
def test_job_from_dict_non_dict_entry_rejected_cleanly(bad_entry):
    # Regression (round-2 class): a job entry that isn't a dict at all (an
    # int, a string, null, a list) used to crash with an uncaught
    # AttributeError/TypeError from `.get`/`in` on a non-dict.
    with pytest.raises(ValueError, match="index 0"):
        job_from_dict(bad_entry, 0)


def test_job_from_dict_non_hashable_id_rejected_cleanly():
    # Regression (round-2 class): a list (or dict) for 'id' used to bypass
    # validation and crash deep inside schedule()'s set/dict bookkeeping with
    # an uncaught TypeError ('unhashable type: list').
    with pytest.raises(ValueError, match="id"):
        job_from_dict({"id": ["not", "hashable"]}, 0)
    with pytest.raises(ValueError, match="id"):
        Job(id=["not", "hashable"])


def test_job_from_dict_bool_id_rejected_cleanly():
    with pytest.raises(ValueError, match="id"):
        job_from_dict({"id": True}, 0)


def test_job_from_dict_non_hashable_resource_element_rejected_cleanly():
    # Regression (round-2 class): a nested list inside 'resources' used to
    # bypass the list/tuple-shape check and crash later with an uncaught
    # TypeError ('unhashable type: list') once used as a dict key / set member.
    with pytest.raises(ValueError, match="resource"):
        job_from_dict({"id": "a", "resources": [["nested"]]}, 0)
    with pytest.raises(ValueError, match="resource"):
        Job(id="a", resources=[["nested"]])


def test_job_from_dict_int_id_and_resource_accepted():
    # Ints are a legitimate scalar id/resource type (docs and code now agree
    # on this) -- only bool/list/dict/None are rejected, not every non-string.
    job = job_from_dict({"id": 1, "resources": [2, "r3"]}, 0)
    assert job.id == 1
    # `resources` is snapshotted into a tuple by `__post_init__` (see the
    # Job-aliasing regression test below) -- compare as a tuple, not the list
    # shape the caller happened to pass in.
    assert job.resources == (2, "r3")


def test_max_parallel_bool_rejected_cleanly():
    # Regression (round-2 class): bool is an int subclass in Python, so
    # max_parallel=True silently passed the old `isinstance(x, int)` check
    # (as capacity 1) instead of being rejected like a stray JSON true/false
    # almost certainly is -- time_limit already excluded bool this way.
    with pytest.raises(ValueError, match="max_parallel"):
        schedule([Job(id="x", resources=["r"])], max_parallel=True)


def test_numpy_int64_max_parallel_accepted():
    # Regression (round-3 class): `max_parallel` used
    # `isinstance(max_parallel, int)`, the exact same narrow-enumeration bug
    # `duration` was fixed for in round 2 (`_is_exact_integer`/`__index__`)
    # -- `numpy.int64` supports `__index__` and IS conceptually an integer,
    # but is not an `int` instance, so it used to be rejected outright with
    # "must be a positive integer".
    jobs = [Job(id="a", resources=[]), Job(id="b", resources=[]), Job(id="c", resources=[])]
    result = schedule(jobs, max_parallel=numpy.int64(2))
    assert result.optimal
    assert result.makespan == 2  # 3 jobs, cap 2 -> two waves


def test_numpy_int64_time_limit_accepted():
    # Regression (round-3 class): same bug as max_parallel above, but for
    # `time_limit`'s old `isinstance(time_limit, (int, float))` check.
    result = schedule([Job(id="a", resources=[])], time_limit=numpy.int64(5))
    assert result.optimal


def test_numpy_float64_time_limit_accepted():
    # `time_limit` may legitimately be non-integer (fractional seconds), so
    # unlike `max_parallel` it must also accept float-like types --
    # `numpy.float64` supports `__float__` and IS conceptually a real number,
    # but is neither an `int` nor a plain `float` instance.
    result = schedule([Job(id="a", resources=[])], time_limit=numpy.float64(2.5))
    assert result.optimal


def test_job_resources_list_aliasing_does_not_leak_into_schedule():
    # Regression: `Job` is `@dataclass(frozen=True)`, but before this fix
    # `__post_init__` never copied a `list` `resources` argument into an
    # immutable snapshot -- it just stored the caller's list object by
    # reference. So mutating the caller's list AFTER construction silently
    # changed the "frozen" Job's resources too, since both names pointed at
    # the same list. Two jobs disjoint at construction time could therefore
    # wrongly end up sharing a resource (and serializing) purely because of
    # what the caller did to their own list afterward -- exactly the kind of
    # action-at-a-distance a `frozen=True` dataclass is supposed to rule out.
    shared = ["r1"]
    a = Job(id="a", resources=shared, duration=1)
    b = Job(id="b", resources=["r2"], duration=1)
    shared.append("r2")  # mutate the caller's list AFTER both Jobs exist

    # `a.resources` must be an immutable snapshot taken at construction time,
    # unaffected by the later mutation of `shared`.
    assert a.resources == ("r1",)

    result = schedule([a, b])
    # a and b share no resource (a: r1 only, as snapshotted; b: r2 only) and
    # there is no max_parallel cap, so both should run fully in PARALLEL
    # (same start time, makespan 1) -- NOT serialize (makespan 2) the way the
    # aliasing bug would force, since the bug made both jobs appear to touch
    # r1 AND r2.
    assert result.jobs[0].start == 0
    assert result.jobs[1].start == 0
    assert result.makespan == 1


def test_job_resources_is_immutable_tuple():
    # Direct check that `resources` is coerced to a tuple regardless of
    # whether the caller passed a list or a tuple -- the snapshot, not just
    # "happens to not alias", is the guarantee `frozen=True` is meant to give.
    job = Job(id="a", resources=["r1", "r2"], duration=1)
    assert isinstance(job.resources, tuple)
    assert job.resources == ("r1", "r2")


def _run_cli(tmp_path, jobs_payload, extra_args=None):
    input_path = tmp_path / "jobs.json"
    output_path = tmp_path / "schedule.json"
    input_path.write_text(json.dumps(jobs_payload))
    proc = subprocess.run(
        [sys.executable, SCHEDULER_PY, "--input", str(input_path), "--output", str(output_path)]
        + (extra_args or []),
        capture_output=True,
        text=True,
    )
    return proc


def test_cli_rejects_none_resources_cleanly(tmp_path):
    proc = _run_cli(tmp_path, {"jobs": [{"id": "a", "resources": None}]})
    assert proc.returncode == 1
    assert "Traceback" not in proc.stderr
    assert proc.stderr.startswith("scheduler.py: error:")
    assert "resources" in proc.stderr


def test_cli_rejects_missing_id_cleanly(tmp_path):
    proc = _run_cli(tmp_path, {"jobs": [{"resources": ["r1"]}]})
    assert proc.returncode == 1
    assert "Traceback" not in proc.stderr
    assert proc.stderr.startswith("scheduler.py: error:")
    assert "id" in proc.stderr


def test_cli_rejects_negative_time_limit_cleanly(tmp_path):
    proc = _run_cli(
        tmp_path,
        {"jobs": [{"id": "a", "resources": ["r1"]}]},
        extra_args=["--time-limit", "-1"],
    )
    assert proc.returncode == 1
    assert "Traceback" not in proc.stderr
    assert proc.stderr.startswith("scheduler.py: error:")
    assert "time_limit" in proc.stderr


@pytest.mark.parametrize("bad_top_level", [[{"id": "a"}], "not-an-object", 5, None])
def test_cli_rejects_non_object_top_level_json_cleanly(tmp_path, bad_top_level):
    # Regression (round-2 class): a top-level JSON value that isn't an object
    # (a list, a bare string, a number, null) used to crash with an uncaught
    # AttributeError from `.get("jobs", ...)` called on a non-dict.
    input_path = tmp_path / "jobs.json"
    output_path = tmp_path / "schedule.json"
    input_path.write_text(json.dumps(bad_top_level))
    proc = subprocess.run(
        [sys.executable, SCHEDULER_PY, "--input", str(input_path), "--output", str(output_path)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    assert "Traceback" not in proc.stderr
    assert proc.stderr.startswith("scheduler.py: error:")


def test_cli_defense_in_depth_net_catches_unanticipated_shape(tmp_path):
    # Not one of the enumerated malformed-input shapes above: point the CLI at
    # an --input path that doesn't exist at all. Nothing in job_from_dict,
    # Job, or schedule() validates "does this file exist" -- that's `open()`'s
    # job, and a missing file raises FileNotFoundError, which is neither
    # ValueError nor RuntimeError. This exercises the CLI's broad
    # defense-in-depth net (scheduler.py's outer `except Exception`), not the
    # explicit validation layer, confirming an un-enumerated failure still
    # produces a clean error instead of a raw traceback.
    output_path = tmp_path / "schedule.json"
    proc = subprocess.run(
        [
            sys.executable,
            SCHEDULER_PY,
            "--input",
            str(tmp_path / "does-not-exist.json"),
            "--output",
            str(output_path),
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    assert "Traceback" not in proc.stderr
    assert proc.stderr.startswith("scheduler.py: error:")
    assert "unexpected" in proc.stderr
    assert "FileNotFoundError" in proc.stderr


def test_cli_round_trip(tmp_path):
    input_path = tmp_path / "jobs.json"
    output_path = tmp_path / "schedule.json"
    input_path.write_text(
        json.dumps(
            {
                "jobs": [
                    {"id": "a", "resources": ["f1"], "duration": 2},
                    {"id": "b", "resources": ["f1"]},
                    {"id": "c", "resources": ["f2"]},
                ],
                "max_parallel": 1,
            }
        )
    )

    proc = subprocess.run(
        [sys.executable, SCHEDULER_PY, "--input", str(input_path), "--output", str(output_path)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr

    out = json.loads(output_path.read_text())
    assert "makespan" in out
    assert "optimal" in out
    assert "jobs" in out
    assert "batches" in out
    assert {j["id"] for j in out["jobs"]} == {"a", "b", "c"}


# --- Structural regression coverage: one shared numeric validator ------
#
# Four review rounds found the same recurring defect shape: a validation
# property (most recently `math.isfinite`) got added for one numeric
# parameter (duration) and never swept to its siblings (max_parallel,
# time_limit), because each had its own hand-written, independently
# evolving validation code. `duration`/`max_parallel`/`time_limit` now all
# route through one shared `_validate_numeric_param` gate in
# makespan_scheduler/model.py. The tests below prove that consolidation
# actually holds, not just that the immediate NaN/Infinity bug happens to
# be fixed for time_limit today.


def test_duration_validation_is_a_thin_wrapper_around_the_shared_validator():
    # `_validate_duration_value` (duration's own entry point) must itself
    # delegate to `_validate_numeric_param` rather than reimplementing the
    # kind/finite/positive checks -- this is what makes a future property
    # added to the shared function apply to duration too, not just to
    # max_parallel/time_limit which call `_validate_numeric_param` directly.
    import dis

    instructions = list(dis.get_instructions(_validate_duration_value))
    referenced_names = {
        instr.argval for instr in instructions if instr.opname in ("LOAD_GLOBAL", "LOAD_DEREF")
    }
    assert "_validate_numeric_param" in referenced_names


def test_duration_max_parallel_time_limit_all_invoke_the_shared_validator(monkeypatch):
    # Structural guarantee, exercised at runtime (rather than only by static
    # bytecode inspection above): actually schedule a call that supplies all
    # three parameters, with `_validate_numeric_param` wrapped by a spy, and
    # confirm each of the three parameter names passes through it exactly
    # once. If a future change reverted one of the three back to a private,
    # hand-written check, this test would catch it even though that
    # regressed parameter might still individually validate correctly.
    import makespan_scheduler.model as model_module

    calls = []
    real_validator = model_module._validate_numeric_param

    def spy(value, **kwargs):
        calls.append(kwargs.get("name"))
        return real_validator(value, **kwargs)

    monkeypatch.setattr(model_module, "_validate_numeric_param", spy)

    schedule(
        [Job(id="a", resources=[], duration=2), Job(id="b", resources=[])],
        max_parallel=1,
        time_limit=5,
    )

    assert calls.count("duration") >= 1
    assert calls.count("max_parallel") == 1
    assert calls.count("time_limit") == 1


# Bad shapes every numeric parameter must reject, regardless of whether it
# is integral (max_parallel) or a general real number (duration, time_limit):
# wrong general type, bool (an int subclass, but never a legitimate numeric
# parameter here), zero, and a negative value.
_BAD_NUMERIC_SHAPES = [
    pytest.param("not-a-number", id="wrong_type"),
    pytest.param(True, id="bool_true"),
    pytest.param(False, id="bool_false"),
    pytest.param(0, id="zero"),
    pytest.param(-1, id="negative"),
]


@pytest.mark.parametrize("bad_value", _BAD_NUMERIC_SHAPES)
def test_all_three_numeric_params_reject_the_same_bad_shapes(bad_value):
    # None of duration/max_parallel/time_limit is missing a check the others
    # have: run the same set of "should be rejected" inputs against all
    # three uniformly.
    with pytest.raises(ValueError):
        Job(id="x", resources=[], duration=bad_value)

    with pytest.raises(ValueError):
        schedule([Job(id="x", resources=[])], max_parallel=bad_value)

    with pytest.raises(ValueError):
        schedule([Job(id="x", resources=[])], time_limit=bad_value)


@pytest.mark.parametrize("non_finite", [float("nan"), float("inf"), float("-inf")])
def test_duration_and_time_limit_both_reject_non_finite_values(non_finite):
    # duration and time_limit are both real-valued (non-integral) numeric
    # parameters, so both must reject NaN/Infinity via the SAME `finite`
    # check in the shared validator -- this is the exact property that was
    # missing for time_limit before this consolidation (the bug this whole
    # change set exists to fix), demonstrated here directly against
    # `_validate_numeric_param` plus both real call sites.
    with pytest.raises(ValueError, match="finite"):
        Job(id="x", resources=[], duration=non_finite)

    with pytest.raises(ValueError, match="finite"):
        schedule([Job(id="x", resources=["r"])], time_limit=non_finite)

    # max_parallel is integral -- a float (finite or not) is never a valid
    # max_parallel at all, so it is rejected earlier as the wrong KIND of
    # value, not specifically for non-finiteness. Still must be a clean
    # ValueError, never reach the solver.
    with pytest.raises(ValueError, match="max_parallel"):
        schedule([Job(id="x", resources=["r"])], max_parallel=non_finite)


@pytest.mark.parametrize("non_finite", [float("nan"), float("inf"), float("-inf")])
def test_shared_validator_directly_rejects_non_finite_for_any_caller(non_finite):
    # Direct unit test of `_validate_numeric_param` itself: any future
    # numeric parameter this library adds gets the finite check for free
    # simply by calling this one function, without writing its own
    # `math.isfinite` guard.
    with pytest.raises(ValueError, match="finite"):
        _validate_numeric_param(
            non_finite,
            name="some_future_param",
            kind_noun="a number",
            integral=False,
            positive_desc="positive",
        )


# --- max_parallel upper-bound regression tests -------------------------
#
# Regression coverage for the gap the duration upper-bound fix (above) did
# NOT close: `_validate_numeric_param`'s `upper_bound` mechanism was only
# ever wired up at `duration`'s call site. `max_parallel`'s call site never
# passed `upper_bound`, so a `max_parallel` in [2**61, cp_model.INT_MAX]
# reached `AddCumulative` and came back solver status MODEL_INVALID,
# misreported as RuntimeError("no feasible schedule found ... try increasing
# --time-limit"); a `max_parallel` >= 2**63 crashed with a raw, undocumented
# pybind11 RuntimeError instead. Both are now caught by an explicit
# `upper_bound=_MAX_SAFE_MAX_PARALLEL` at max_parallel's call site in
# schedule() -- see that constant's derivation comment in
# makespan_scheduler/model.py (empirically bisected specifically for
# `AddCumulative`'s capacity argument, NOT reused from `_MAX_SAFE_DOMAIN`).


def test_max_parallel_just_under_the_limit_still_schedules():
    # At exactly _MAX_SAFE_MAX_PARALLEL, max_parallel is a no-op cap (far
    # larger than the job count) but must still be ACCEPTED and produce a
    # real, valid, optimal schedule -- the boundary itself is inside the
    # safe range, not excluded by an off-by-one in the check.
    jobs = [Job(id=f"j{i}", resources=[f"r{i}"]) for i in range(3)]
    result = schedule(jobs, max_parallel=_MAX_SAFE_MAX_PARALLEL)
    assert result.optimal is True
    assert result.makespan == 1  # no shared resources, cap far above job count


def test_max_parallel_just_over_the_limit_raises_clean_value_error():
    # One unit past the limit must raise a clean ValueError naming
    # max_parallel and the limit -- never MODEL_INVALID (surfaced as a
    # misleading RuntimeError) and never a raw pybind11 crash.
    jobs = [Job(id=f"j{i}", resources=[f"r{i}"]) for i in range(3)]
    with pytest.raises(ValueError, match="exceeds the maximum"):
        schedule(jobs, max_parallel=_MAX_SAFE_MAX_PARALLEL + 1)


def test_max_parallel_way_over_the_limit_raises_clean_value_error_not_raw_crash():
    # Regression: max_parallel=2**64 (comfortably past even raw int64) used
    # to crash with an undocumented pybind11 RuntimeError ("Unable to cast
    # Python instance ... to C++ type") straight out of ortools' own argument
    # marshalling for AddCumulative -- indistinguishable from a genuine bug,
    # since scheduler.py's outer except Exception bucket catches it under
    # the same "unexpected" label as a real internal error. Must now be
    # caught before ever reaching ortools, as a clean ValueError.
    jobs = [Job(id=f"j{i}", resources=[f"r{i}"]) for i in range(3)]
    with pytest.raises(ValueError, match="exceeds the maximum"):
        schedule(jobs, max_parallel=2**64)


def test_cli_rejects_astronomically_large_max_parallel_cleanly(tmp_path):
    # CLI-level regression test for the exact bug report this fix addresses:
    # a jobs.json with a max_parallel of this magnitude used to either
    # misreport MODEL_INVALID as infeasibility or crash with a raw pybind11
    # RuntimeError, surfacing under scheduler.py's generic "unexpected error"
    # bucket instead of a clean, attributable ValueError.
    proc = _run_cli(
        tmp_path,
        {
            "jobs": [{"id": "a", "resources": ["r1"]}, {"id": "b", "resources": ["r2"]}],
            "max_parallel": 2**64,
        },
    )
    assert proc.returncode == 1
    assert "Traceback" not in proc.stderr
    assert proc.stderr.startswith("scheduler.py: error:")
    assert "max_parallel" in proc.stderr
    assert "unexpected" not in proc.stderr
    assert "no feasible schedule" not in proc.stderr


# --- UTF-8 encoding regression test -------------------------------------


def test_cli_round_trip_with_non_ascii_resource_and_id(tmp_path):
    # Regression: scheduler.py's open(args.input)/open(args.output, "w")
    # relied on the platform locale's default encoding rather than an
    # explicit UTF-8, so a non-ASCII job id/resource (e.g. a real, non-ASCII
    # file path -- the README positions file paths as the common case for
    # `resources`) could round-trip incorrectly, or fail outright, on a
    # system whose locale default encoding isn't UTF-8. JSON is UTF-8-native,
    # so the tool should always read/write it as UTF-8 regardless of locale.
    input_path = tmp_path / "jobs.json"
    output_path = tmp_path / "schedule.json"
    non_ascii_id = "résumé-​日本語-job"
    non_ascii_resource = "/tmp/café/文件.txt"
    input_path.write_text(
        json.dumps(
            {"jobs": [{"id": non_ascii_id, "resources": [non_ascii_resource]}]},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [sys.executable, SCHEDULER_PY, "--input", str(input_path), "--output", str(output_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, proc.stderr

    out = json.loads(output_path.read_text(encoding="utf-8"))
    assert out["jobs"][0]["id"] == non_ascii_id
