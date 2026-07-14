# makespan-scheduler

A minimum-makespan scheduler for bulk "job" operations where jobs conflict
whenever they touch overlapping resources — e.g. two edits that touch the same
file, two processes contending for the same lock, two commits touching the
same lines. It answers: "what's the fastest valid order/overlap of these jobs,
given which ones can't run at the same time, and (optionally) a cap on how many
can run at once?"

It is intentionally generic: "resources" are just opaque hashable scalars
(strings or ints). File paths are the expected common case, but nothing in
the model assumes files, a particular VCS, or any particular orchestration
system.

## The problem, precisely

- **Input**: a list of jobs. Each job has:
  - `id` (string or int, unique) — not a bool, list, or object.
  - `resources` (list of strings or ints) — the resources this job touches.
    Two jobs that share at least one resource cannot run at overlapping times.
  - `duration` (optional positive number, default `1`) — a relative cost, in
    abstract integer units (not necessarily wall-clock seconds).
- **Optional global parameter**: `max_parallel` — a positive integer capacity:
  the maximum number of jobs that may be running at any single instant,
  modeling a worker-pool/concurrency limit. If omitted, only the
  resource-conflict constraints apply (unbounded concurrency otherwise).
- **Hard constraint 1 (resource conflicts)**: for every resource touched by
  two or more jobs, those jobs' time intervals must not overlap. Each resource
  is a classical "unary resource" in scheduling theory — at most one job may
  hold it at any instant.
- **Hard constraint 2 (concurrency cap, if `max_parallel` given)**: at every
  instant, the number of jobs running simultaneously must not exceed
  `max_parallel` — regardless of whether those jobs share any resources.
- **Objective**: minimize the **makespan** — the completion time (end) of the
  last-finishing job. This is the standard scheduling-theory definition. It is
  *not* the same as "minimize the number of rounds"; that objective only
  coincides with makespan when every job has identical duration. This tool
  handles the general, variable-duration case directly — uniform durations are
  just a special case of the same model, not a separate code path.

The tool correctly handles:
- Jobs with no shared resources with any other job — free to start at time 0
  (if capacity allows).
- A job that conflicts with every other job — it serializes with all of them.
- Multiple disconnected components of the resource-conflict graph — they
  schedule independently/concurrently where capacity allows, rather than being
  forced to wait on each other.

## The CP-SAT model

Built with [OR-Tools](https://developers.google.com/optimization) CP-SAT
(`ortools.sat.python.cp_model`).

- **Variables**: one interval variable per job — `(start, duration, end)` —
  with `start` and `end` ranging over `[0, horizon]`, where `horizon` is the
  sum of all job durations (a safe upper bound: fully serializing every job is
  always feasible). `duration` is fixed to the job's own (rounded-to-integer)
  duration.
- **Resource-conflict constraint**: jobs are grouped by resource. For every
  resource touched by 2+ jobs, one `AddNoOverlap` constraint is added over
  those jobs' interval variables — CP-SAT's standard encoding for "these
  intervals must be pairwise non-overlapping" on a unary resource. A job
  touching N resources participates in N such constraints (one per resource),
  which is exactly what couples it to every other job it conflicts with,
  without requiring an explicit pairwise conflict graph.
- **Concurrency-cap constraint** (only if `max_parallel` is given): one
  `AddCumulative` constraint over *every* job's interval, each with demand 1
  and total capacity `max_parallel` — the standard encoding of a worker-pool
  capacity limit.
- **Objective**: a `makespan` variable is tied to the max of all job end times
  via `AddMaxEquality`, and minimized.

CP-SAT is integer-only. Durations are rounded to the nearest positive integer
(minimum 1) before the model is built. If you need sub-integer precision,
pre-scale your own durations (e.g. multiply every duration by 1000) before
calling — the library does not silently rescale on your behalf, since a hidden
scale factor would make the "integer output units" ambiguous. Whatever units
your input durations use, output start/end times are in those same
(post-rounding) units.

### Solver time limits

Pass `--time-limit SECONDS` (CLI) or `time_limit=` (library) to cap solver
wall-clock time. If the solver proves the returned makespan is minimal within
that time, the output's `"optimal"` field is `true`. If the time limit expires
first, the solver's best feasible schedule so far is returned instead, with
`"optimal": false` — this is always a valid schedule (every hard constraint
is satisfied), just not proven minimal. The tool never presents a non-optimal
result as optimal. Omit `--time-limit`/`time_limit` to let the solver run
until it proves optimality.

## The "batches" output — what it is and its limits

Alongside the exact per-job `start`/`end` times, the tool derives a `batches`
field: an ordered list of "waves", where each wave is the list of job ids that
share an identical computed start time. This is the practical artifact an
orchestrator uses to actually dispatch work: "wave 1: launch these N jobs in
parallel; once they're done (or once you're ready), launch wave 2; ...".

**How it's derived**: group scheduled jobs by their `start` value, and order
the groups by increasing start time. That's it — no clustering heuristics, no
tolerance windows.

**Why this is correct**: every job in a batch is, by construction, safe to
launch together — the CP-SAT constraints already guarantee no two conflicting
jobs are ever both "running" at the same instant, so two jobs sharing a start
time cannot conflict (if they did, `NoOverlap` would have forced them apart).

**The caveat**: when durations vary, jobs in the same batch may *finish* at
different times. E.g. batch `["A", "B"]` where `A` has duration 1 and `B` has
duration 5, both starting at `t=0`: they can be launched together, but `A`
finishes long before `B`. The batches view answers "what can I launch
together right now?", not "what all finishes at the same time?" — for exact
completion times, use the `jobs[].end` field, which is ground truth. Treat
`batches` as an orchestration convenience/approximation layered on top of the
exact schedule, not a replacement for it. If your jobs have uniform duration,
this distinction disappears and batches exactly partition the schedule into
synchronized rounds.

## CLI usage

Requires the `ortools` package. The already-provisioned venv at
`~/w/vdc/venvs/generic` has it:

```sh
~/w/vdc/venvs/generic/bin/python scheduler.py \
    --input jobs.json \
    --output schedule.json \
    [--max-parallel N] \
    [--time-limit SECONDS]
```

Any other Python 3.8+ interpreter with `pip install ortools` works too.

**Input JSON** (`jobs.json`):

```json
{
  "jobs": [
    {"id": "edit-a", "resources": ["src/foo.py"], "duration": 2},
    {"id": "edit-b", "resources": ["src/foo.py", "src/bar.py"]},
    {"id": "edit-c", "resources": ["src/baz.py"]}
  ],
  "max_parallel": 4
}
```

- `duration` is optional (defaults to `1`).
- `max_parallel` is optional. A `--max-parallel` CLI flag overrides the
  in-file value if both are given.

**Output JSON** (`schedule.json`):

```json
{
  "makespan": 3,
  "optimal": true,
  "jobs": [
    {"id": "edit-a", "start": 0, "end": 2},
    {"id": "edit-b", "start": 2, "end": 3},
    {"id": "edit-c", "start": 0, "end": 1}
  ],
  "batches": [["edit-a", "edit-c"], ["edit-b"]]
}
```

## Library usage

```python
from makespan_scheduler import Job, schedule

jobs = [
    Job(id="edit-a", resources=["src/foo.py"], duration=2),
    Job(id="edit-b", resources=["src/foo.py", "src/bar.py"]),
    Job(id="edit-c", resources=["src/baz.py"]),
]

result = schedule(jobs, max_parallel=4, time_limit=10)

print(result.makespan)   # e.g. 3
print(result.optimal)    # True or False
for j in result.jobs:
    print(j.id, j.start, j.end)
for wave in result.batches:
    print(wave)

result.to_dict()  # JSON-serializable dict, same shape as the CLI output
```

`schedule()` raises `ValueError` on malformed input (duplicate job ids,
non-positive `duration`/`max_parallel`, or a `duration` — either a single
job's or the summed horizon across all jobs — too large for CP-SAT's usable
domain; see "Duration limits" below) and `RuntimeError` if the solver cannot
find *any* feasible schedule within the time limit (distinct from finding one
but not proving it optimal, which is returned normally with `optimal=False`).

### Duration limits

CP-SAT domains are 64-bit integers, but the solver only behaves correctly
well inside that raw range — not right up to it. This library validates every
duration (and the summed horizon across all jobs — see the CP-SAT model
section above) against `cp_model.INT_MAX // 4`, a bound derived from and
tracking OR-Tools' own published `INT_MAX` constant rather than a hardcoded
number. Both an individual job's duration and the total horizon (since
`horizon = sum(durations)` becomes every job's own start/end upper bound) are
checked, because enough individually-valid durations can still sum past the
limit even when no single one does. Anything over the limit is rejected with
a `ValueError` before it ever reaches the solver — previously this could
either silently misreport as "no feasible schedule found ... try increasing
--time-limit" (no time limit fixes an invalid model) or escape as a raw,
undocumented `TypeError` from inside ortools.

### A note on scale (not a bug)

This is CP-SAT's actual behavior at scale, not a defect: on a dense instance
(many jobs, many resources shared per job) with ~5,000 jobs, the solver
reliably proves optimality in a couple of seconds. Push the same density to
roughly 20,000 jobs, though, and the solver may fail to find *any* feasible
schedule within a modest time limit — even though a trivial fully-serial
schedule is always feasible. This is inherent to how CP-SAT's disjunctive
scheduling search scales on large, dense `NoOverlap`/`AddCumulative` models,
not a logic bug in this tool. If you're scheduling very large job sets,
expect to need a longer `--time-limit`, and don't be surprised by
`optimal: false` (or, on the largest/densest instances, a `RuntimeError` if
even a feasible schedule isn't found in time) — increasing `--time-limit` is
the right lever, same as any other CP-SAT search-space issue.

## Running the tests

```sh
~/w/vdc/venvs/generic/bin/python -m pytest tests/ -v
```

Covers: fully independent jobs scheduling entirely in parallel; a resource
chain forcing full serialization; a `max_parallel` cap being respected even
when resource conflicts alone would allow more concurrency; disconnected
conflict-graph components scheduling independently; internal consistency of
the `batches` output against `start`/`end`; and a deliberately tiny
`--time-limit` on a large instance still returning a valid (if non-optimal,
`optimal: false`) schedule — plus a few input-validation and CLI-round-trip
checks.
