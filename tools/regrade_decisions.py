#!/usr/bin/env python3
"""regrade_decisions -- interactive, one-row-at-a-time retro-grading of every IN-FORCE ledger
decision row that has no `decision_grade` yet (kernel/lineage/s36-decision-grade.sql, design/
FABLE-GRADED-DECISIONS-SPEC.md). Maintainer-commissioned 2026-07-16 (ledger item
`regrade-decisions-tool`) so a non-programmer operator can, once, after their deployment migrates
to s36, walk their existing standing decisions and mark the ones that must survive context loss.

DELIBERATELY DUMB (the commission's own word): one row at a time, three real choices (durable /
a custom grade word / skip), a fourth to stop, and a summary at the end. No batch mode, no
"grade all", no undo beyond re-running `led --supersedes` by hand -- the maintainer reads and
decides on every single row, on purpose.

===============================================================================================
OPERATOR WALKTHROUGH -- what you type, what you should see
===============================================================================================

  $ cd <your-deployment-directory>          # the directory holding your own ./led and
                                             # deployment.json (the scaffold's own layout)
  $ python3 /path/to/autoharn/tools/regrade_decisions.py

  If your kernel predates s36, you will see and nothing more is written:

    regrade_decisions: REFUSED -- <schema>.ledger has no decision_grade column ...

  If you pipe this tool's input/output (a script, `| cat`, a CI job), you will see:

    regrade_decisions: REFUSED -- stdin is not a TTY ...

  Otherwise, for each ungraded decision, oldest first, you will see something like:

    ------------------------------------------------------------------------------------------
    decision id=42  ts=2026-07-01 10:03:00+00:00
      "consults MUST land in docs/consults, forever" -- ratified after the docs/ reorg,
      2026-06-30 (Fable + maintainer).

    [d]urable / [g]rade <word> / [s]kip / [q]uit:

  Typing `d` re-issues the row with grade "durable" and prints a one-line confirmation:

    confirmed: decision 42 -> 87 (grade=durable) is in-force; original row 42 is no
      longer in ledger_current.

  Typing `g important` (or just `g`, then answering a follow-up "grade word:" prompt)
  re-issues it with grade "important" instead. If "important" is not in this deployment's
  configured grade vocabulary (apparatus.json mechanisms.standing_decisions.grades) you will
  see a WARNING first -- the row is still graded and written, just not yet surfaced by the
  SessionStart hook / `./pickup` / `./led standing` until that config is updated.

  Typing `s` leaves the row ungraded and moves to the next one. Typing `q` stops immediately
  (no further rows are touched) and prints a summary:

    ============================================================
    regrade_decisions summary:
      bumped:    1
      skipped:   1
      failed:    0
      remaining: 1 (stopped by quit)

  Nothing here is ever a raw database write: every accepted grade re-issues the decision
  THROUGH `./led` -- `./led --supersedes <id> [--refs <refs>] decision --grade <word>
  "<statement>"` -- so every one of led's own validations, stamping, and hash-chain machinery
  runs exactly as it would for a hand-typed command. The original statement text travels
  byte-verbatim; this tool never edits prose.

===============================================================================================

DEPLOYMENT RESOLUTION -- filing/deployment_resolve.py, the ONE home for this (shared with
tools/export_precedence.py, the idiom's original source -- read that module's docstring for the
full rationale, ledger item deployment-resolution-cwd-first): PICKUP_DEPLOYMENT env var, else
LEDGER_DEPLOYMENT, else `$PWD/deployment.json` (the CALLER's own cwd -- the primary use case, an
operator running this tool from their own project directory), else `<repo-root>/deployment.json`
next to this checkout (preserves in-checkout use). The deployment's own `./led` shim is expected
to sit in the SAME directory as its deployment.json (bootstrap/new-project.sh's own scaffold
layout) -- this tool refuses loudly if it is not there rather than guessing a path or falling
back to a raw INSERT.

Stdlib-only, top-of-file imports (gates/no_lazy_imports.py; CLAUDE.md, "Lazy imports are BANNED").
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent
sys.path.insert(0, str(_REPO_ROOT / "filing"))

import deployment_record  # noqa: E402  (filing/deployment_record.py, the ONE home for the deployment.json shape)
import deployment_resolve  # noqa: E402  (filing/deployment_resolve.py, the ONE home for CWD-FIRST
                            # deployment.json resolution -- ledger item deployment-resolution-cwd-first)
import standing_decisions_config  # noqa: E402  (filing/standing_decisions_config.py, the ONE home
                                   # for the grades/byte_cap defaulting logic)

_LED_TMPL = _REPO_ROOT / "bootstrap" / "templates" / "led.tmpl"

# Field / record separators for psql -tA output -- the SAME ASCII US/RS convention
# hooks/sessionstart_durable_decisions.py's own _fetch_standing_decisions() uses, so a decision
# statement containing a tab or newline cannot corrupt row parsing.
FS = "\x1f"
RS = "\x1e"


def _refuse(message: str) -> None:
    print(f"regrade_decisions: REFUSED -- {message}", file=sys.stderr)
    raise SystemExit(1)


def _load_deployment() -> tuple[deployment_record.DeploymentRecord, Path]:
    """Resolve this project's deployment.json via filing/deployment_resolve.py (the ONE home,
    shared with tools/export_precedence.py): PICKUP_DEPLOYMENT, then LEDGER_DEPLOYMENT, then
    $PWD/deployment.json (the caller's own cwd), then this checkout's own repo-root default.
    Returns (record, resolved path) -- the path's own parent directory is where this tool expects
    to find the deployment's own `./led` shim (the scaffold's layout: deployment.json and led sit
    side by side)."""
    try:
        dep, resolved = deployment_resolve.resolve_deployment(_REPO_ROOT)
    except deployment_record.DeploymentError as e:
        _refuse(str(e))
    return dep, resolved


def _psql_scalar(dep: deployment_record.DeploymentRecord, sql: str) -> str:
    result = subprocess.run(
        ["psql", "-h", dep.host, "-d", dep.db, "-v", "ON_ERROR_STOP=1", "-tAc", sql],
        capture_output=True, text=True, check=True)
    return result.stdout.strip()


def _has_column(dep: deployment_record.DeploymentRecord, schema: str, table: str, column: str) -> bool:
    return _psql_scalar(dep, f"""
        SELECT EXISTS (
          SELECT 1 FROM information_schema.columns
          WHERE table_schema = '{schema}' AND table_name = '{table}' AND column_name = '{column}'
        );""") == "t"


def _psql_records(dep: deployment_record.DeploymentRecord, sql: str) -> list[list[str]]:
    """Runs `sql` (which may open with a `SET ROLE ...;` statement, the same convention
    hooks/sessionstart_durable_decisions.py's own _fetch_standing_decisions() uses) framed with
    FS/RS, fed via stdin (psql's `:'var'` interpolation only applies to a script read from
    stdin/-f, never a `-c` argument -- this file's own recurring note). Returns one list of
    field strings per non-empty record."""
    result = subprocess.run(
        ["psql", "-h", dep.host, "-d", dep.db, "-tA", "-F", FS, "-R", RS, "-v", "ON_ERROR_STOP=1"],
        input=sql, capture_output=True, text=True, check=True)
    stdout = result.stdout
    # -t -A echoes one leading "SET\n" line for a preceding `SET ROLE` statement, glued directly
    # onto the first row with no RS separator before it (the same wart hooks/
    # sessionstart_durable_decisions.py's own _fetch_standing_decisions() already works around).
    if stdout.startswith("SET\n"):
        stdout = stdout[len("SET\n"):]
    records = []
    for rec in stdout.split(RS):
        if not rec.strip():
            continue
        records.append(rec.split(FS))
    return records


def fetch_ungraded_decisions(dep: deployment_record.DeploymentRecord) -> list[tuple[str, str, str, str]]:
    """Every IN-FORCE (ledger_current-factored, s31/s32 posture -- never raw `ledger`) kind=decision
    row with decision_grade IS NULL, oldest first. Returns (id, ts, statement, refs) tuples --
    refs is '' when NULL."""
    sql = (
        f"SET ROLE {dep.role};\n"
        f"SELECT id, ts, statement, COALESCE(refs, '') FROM {dep.schema}.ledger_current\n"
        f"WHERE kind = 'decision' AND decision_grade IS NULL ORDER BY id;\n"
    )
    rows = []
    for parts in _psql_records(dep, sql):
        if len(parts) != 4:
            continue  # malformed record (should not happen with FS/RS framing) -- skip, don't crash
        rows.append((parts[0].strip(), parts[1].strip(), parts[2], parts[3]))
    return rows


def confirm_bump(dep: deployment_record.DeploymentRecord, old_id: str) -> tuple[str, str, bool] | None:
    """Read-back confirmation for one accepted bump (spec step 5): the row superseding `old_id`
    is in-force (ledger_current) and carries the grade; `old_id` itself is no longer in
    ledger_current. Returns (new_id, new_grade, old_still_in_force) or None if no superseding row
    is found at all (led reported success but the read-back disagrees -- a caller-visible
    anomaly, never silently swallowed)."""
    oid = int(old_id)  # validate/narrow before splicing -- these ids are our own query's output,
                        # never untrusted input, but int() is the cheap boundary check anyway
    sql = (
        f"SET ROLE {dep.role};\n"
        f"SELECT new.id, new.decision_grade,\n"
        f"       EXISTS(SELECT 1 FROM {dep.schema}.ledger_current WHERE id = {oid})\n"
        f"FROM {dep.schema}.ledger_current new\n"
        f"WHERE new.supersedes = {oid}\n"
        f"ORDER BY new.id DESC LIMIT 1;\n"
    )
    records = _psql_records(dep, sql)
    if not records or len(records[0]) != 3:
        return None
    new_id, new_grade, old_still = records[0]
    return new_id.strip(), new_grade.strip(), old_still.strip() == "t"


def _led_supports_refs() -> bool:
    """Runtime check (never hardcoded) of whether the led CLI this checkout ships accepts a
    top-of-file `--refs` flag -- read from bootstrap/templates/led.tmpl's own LED_FLAG_VOCAB
    line, the ONE place that vocabulary is declared. If this checkout's led predates --refs (or
    the template cannot be read at all), the tool falls back to NOT carrying refs, printing a
    per-row note rather than dropping them silently (spec step 4)."""
    try:
        text = _LED_TMPL.read_text(encoding="utf-8")
    except OSError:
        return False
    for line in text.splitlines():
        if line.startswith("LED_FLAG_VOCAB="):
            return "--refs" in line
    return False


def _load_standing_decisions_grades(project_dir: Path) -> list[str]:
    """apparatus.json -> mechanisms.standing_decisions.grades, defaulted/validated via
    filing/standing_decisions_config.py (the ONE home for that shape) -- same extraction pattern
    hooks/sessionstart_durable_decisions.py's own _resolve_standing_decisions_config() uses.
    Missing/malformed apparatus.json degrades to the documented default, same as every other
    reader of this shape -- never a hard failure for a tool whose primary job is unrelated."""
    apparatus_path = project_dir / ".claude" / "apparatus.json"
    try:
        with open(apparatus_path, encoding="utf-8") as f:
            apparatus = json.load(f)
    except Exception:
        apparatus = {}
    mechs = apparatus.get("mechanisms") if isinstance(apparatus, dict) else None
    entry = mechs.get("standing_decisions") if isinstance(mechs, dict) else None
    grades, _byte_cap, _max_items = standing_decisions_config.resolve_standing_decisions_config(entry)
    return grades


def _wrap(statement: str) -> str:
    width = 92
    try:
        width = max(40, shutil.get_terminal_size(fallback=(92, 24)).columns - 2)
    except Exception:
        pass
    return textwrap.fill(statement, width=width, initial_indent="  ", subsequent_indent="  ")


def main() -> int:
    # Highest-priority gate, checked before ANY database touch: this tool must never run
    # unattended (spec commission's own wording) -- a batch/piped invocation could re-issue a
    # decision under the wrong grade with no human confirming each one.
    if not sys.stdin.isatty():
        _refuse(
            "stdin is not a TTY. regrade_decisions is an INTERACTIVE, one-row-at-a-time tool "
            "(ledger item regrade-decisions-tool) -- it must never run unattended from a script, "
            "a pipe, or CI: every accepted grade re-issues a decision row, and this tool's whole "
            "safety property is a human reading and deciding on EACH one. Run it directly in a "
            "real terminal.")

    dep, dep_path = _load_deployment()
    project_dir = dep_path.parent
    led_path = project_dir / "led"
    if not led_path.is_file() or not os.access(led_path, os.X_OK):
        _refuse(
            f"no executable './led' found at {led_path}. Every accepted bump in this tool re-issues "
            f"THROUGH the led CLI (never a raw INSERT -- the stamp/validation machinery lives "
            f"there); the deployment's own led shim must sit next to its deployment.json (the "
            f"bootstrap/new-project.sh scaffold's own layout). Scaffold this project first, or "
            f"point PICKUP_DEPLOYMENT/LEDGER_DEPLOYMENT at the right deployment.json.")

    if not _has_column(dep, dep.schema, "ledger", "decision_grade"):
        _refuse(
            f"{dep.schema}.ledger has no decision_grade column -- this world predates "
            f"kernel/lineage/s36-decision-grade.sql (design/FABLE-GRADED-DECISIONS-SPEC.md). "
            f"Apply s36 to this project's schema as a maintainer act (user-guide/ORCH-OPERATING-CARD.md's "
            f"kernel-delta decision tree) before any decision row can carry a grade at all.")

    rows = fetch_ungraded_decisions(dep)
    if not rows:
        print("regrade_decisions: no in-force, ungraded decision rows found -- nothing to do.")
        return 0

    grades_cfg = _load_standing_decisions_grades(project_dir)
    refs_supported = _led_supports_refs()

    print(f"regrade_decisions: {len(rows)} in-force decision row(s) carry no grade yet (oldest first).")
    print(f"Configured grade vocabulary (apparatus.json mechanisms.standing_decisions.grades): {grades_cfg}")
    print()

    bumped = skipped = failed = 0
    total = len(rows)
    idx = 0
    quit_early = False

    while idx < total:
        row_id, ts, statement, refs = rows[idx]
        print("-" * 94)
        print(f"decision id={row_id}  ts={ts}")
        print(_wrap(statement))
        if refs:
            print(f"  refs: {refs}")
        print()

        grade: str | None = None
        quit_now = False
        while True:
            try:
                answer = input("[d]urable / [g]rade <word> / [s]kip / [q]uit: ").strip()
            except EOFError:
                answer = "q"
            if not answer:
                continue
            parts = answer.split(None, 1)
            verb = parts[0].lower()
            rest = parts[1].strip() if len(parts) > 1 else ""
            if verb in ("d", "durable"):
                grade = "durable"
                break
            if verb in ("g", "grade"):
                word = rest
                if not word:
                    try:
                        word = input("  grade word: ").strip()
                    except EOFError:
                        word = ""
                if not word:
                    print("  no grade word given -- try again.")
                    continue
                grade = word
                break
            if verb in ("s", "skip"):
                grade = None
                break
            if verb in ("q", "quit"):
                quit_now = True
                break
            print(f"  unrecognized input '{answer}' -- type d, g <word>, s, or q.")

        if quit_now:
            quit_early = True
            break

        if grade is None:
            print(f"  skipped decision {row_id}.\n")
            skipped += 1
            idx += 1
            continue

        if grade not in grades_cfg:
            print(f"  WARNING: grade '{grade}' is not in this deployment's configured "
                  f"mechanisms.standing_decisions.grades list {grades_cfg} -- it will still be "
                  f"recorded, but the SessionStart hook / ./pickup / ./led standing will not "
                  f"surface it until apparatus.json's grade list is updated to include it.")

        cmd = [str(led_path), "--supersedes", row_id]
        if refs:
            if refs_supported:
                cmd += ["--refs", refs]
            else:
                print(f"  NOTE: original refs ({refs!r}) were NOT carried onto the re-issue -- "
                      f"this checkout's led CLI does not accept --refs on a generic re-issue.")
        cmd += ["decision", "--grade", grade, statement]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  FAILED to re-issue decision {row_id} (led exit {result.returncode}):")
            print(textwrap.indent(result.stderr.strip(), "    "))
            failed += 1
            idx += 1
            print()
            continue

        confirmation = confirm_bump(dep, row_id)
        if confirmation is None:
            print(f"  led reported success for decision {row_id}, but the confirmation read-back "
                  f"found no superseding row in ledger_current -- check manually via "
                  f"'./led show {row_id}'.")
            failed += 1
            idx += 1
            print()
            continue

        new_id, new_grade, old_still_current = confirmation
        if new_grade == grade and not old_still_current:
            print(f"  confirmed: decision {row_id} -> {new_id} (grade={new_grade}) is in-force; "
                  f"original row {row_id} is no longer in ledger_current.")
            bumped += 1
        else:
            print(f"  UNEXPECTED STATE after re-issuing decision {row_id}: new row {new_id} has "
                  f"grade={new_grade!r} (expected {grade!r}), old row still in ledger_current: "
                  f"{old_still_current}. Check manually via './led show {row_id}' / "
                  f"'./led show {new_id}'.")
            failed += 1
        idx += 1
        print()

    remaining = total - idx
    print("=" * 60)
    print("regrade_decisions summary:")
    print(f"  bumped:    {bumped}")
    print(f"  skipped:   {skipped}")
    print(f"  failed:    {failed}")
    suffix = " (stopped by quit)" if quit_early else ""
    print(f"  remaining: {remaining}{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
