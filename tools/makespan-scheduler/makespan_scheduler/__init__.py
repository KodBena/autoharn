"""
makespan_scheduler
===================

A minimum-makespan scheduler for bulk "job" operations where jobs conflict when
they touch overlapping resources.

See README.md at the project root for the full problem statement and model
documentation. The two public entry points are:

- ``schedule(jobs, max_parallel=None, time_limit=None)`` — the library API.
- the ``scheduler.py`` CLI script, which wraps ``schedule`` for JSON-in/JSON-out use.
"""

from .model import Job, ScheduleResult, job_from_dict, schedule

__all__ = ["Job", "ScheduleResult", "job_from_dict", "schedule"]
