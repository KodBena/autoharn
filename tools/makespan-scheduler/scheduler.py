#!/usr/bin/env python3
"""
scheduler.py — CLI front-end for makespan_scheduler.

Usage:
    scheduler.py --input jobs.json --output schedule.json [--max-parallel N] [--time-limit SECONDS]

Input JSON shape:
    {
      "jobs": [
        {"id": "job1", "resources": ["fileA", "fileB"], "duration": 2},
        {"id": "job2", "resources": ["fileB"]}
      ],
      "max_parallel": 3
    }

  - "duration" is optional (defaults to 1).
  - "max_parallel" is optional at the top level; --max-parallel on the command
    line overrides it if both are given.

Output JSON shape:
    {
      "makespan": 5,
      "optimal": true,
      "jobs": [{"id": "job1", "start": 0, "end": 2}, ...],
      "batches": [["job1", "job2"], ...]
    }

See README.md for the full problem model and the batches-derivation caveat.
"""

import argparse
import json
import sys

from makespan_scheduler import job_from_dict, schedule


def _load_jobs(data: dict):
    return [job_from_dict(entry, i) for i, entry in enumerate(data.get("jobs", []))]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Minimum-makespan scheduler for resource-conflicting jobs (CP-SAT based)."
    )
    parser.add_argument("--input", required=True, help="Path to input JSON file (see module docstring for shape).")
    parser.add_argument("--output", required=True, help="Path to write output JSON to.")
    parser.add_argument(
        "--max-parallel",
        type=int,
        default=None,
        help="Maximum number of jobs running simultaneously. Overrides the input file's "
        "max_parallel if both are given. Omit for unbounded (resource conflicts only).",
    )
    parser.add_argument(
        "--time-limit",
        type=float,
        default=None,
        help="Wall-clock seconds to allow the solver. If exceeded before optimality is "
        "proven, the best schedule found so far is returned with optimal=false. "
        "Omit to run until optimality is proven.",
    )
    args = parser.parse_args(argv)

    # The whole dispatch below -- reading the input, validating it, running the
    # solver, and writing the output -- is wrapped in one try/except so that
    # NOTHING escapes as a raw traceback: (ValueError, RuntimeError) are the
    # tool's own explicitly-validated, expected failure modes (bad input shape,
    # solver-reported infeasibility); the bare `except Exception` below it is a
    # deliberate DEFENSE-IN-DEPTH last-resort net, not a substitute for that
    # explicit validation -- see its own comment for why.
    try:
        with open(args.input, encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError(
                "input JSON must be a top-level object (dict) with a 'jobs' field, "
                f"got {data!r} (type {type(data).__name__})"
            )

        jobs = _load_jobs(data)
        max_parallel = args.max_parallel if args.max_parallel is not None else data.get("max_parallel")
        result = schedule(jobs, max_parallel=max_parallel, time_limit=args.time_limit)

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2)
            f.write("\n")
    except (ValueError, RuntimeError) as exc:
        print(f"scheduler.py: error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        # Last-resort net: converts ANY exception shape nobody enumerated above
        # (a malformed input this tool's authors didn't imagine, a library
        # upgrade that raises a new exception type, etc.) into the tool's clean
        # error convention instead of a raw traceback -- but still prints the
        # real exception type and message, rather than hiding it behind a generic
        # "something went wrong". This should rarely if ever fire: it is a safety
        # net behind the explicit validation above (job_from_dict, the top-level
        # shape check, schedule()'s own parameter checks), not a replacement for
        # it -- silently swallowing an unenumerated case here would just trade a
        # visible bug for an invisible one.
        print(f"scheduler.py: error: unexpected {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
