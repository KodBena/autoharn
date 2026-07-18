#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-13T12:32:12Z
#   last-change: 2026-07-13T12:32:12Z
#   contributors: 3c50e030/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures — both-polarity live proof for the `review:`/`review-done:` intake-validation
feature (tracker item `maintainer-review-queue`, 2026-07-13; gates/fixture_census.py REGISTRY
entry "review-queue-intake"). Mirrors seen-red/actual-intake-validation/run_fixtures.py's and
seen-red/taxonomy-intake-validation/run_fixtures.py's scratch-and-drop pattern exactly: a
throwaway project directory (via bootstrap/track-work.sh) plus a throwaway schema pair in the
TOY db, torn down after unless a case fails (left standing as evidence, matching the
standing-probe convention every other run_fixtures.py in this repo uses). Both grammars are
exercised in ONE fixture file because they are one feature (one tracker item, one `./pickup`
MAINTAINER-REVIEW-QUEUE section, one documented grammar home) -- the same granularity choice
seen-red/taxonomy-intake-validation/ already makes for its own `taxon:`/`interface:` pair.

WHAT THIS PROVES: `bootstrap/templates/led.tmpl` validates a `review:`-prefixed decision
statement (four fields: SLUG | RANK | WHAT | POINTER) and a `review-done:`-prefixed decision
statement (two fields: SLUG | DISPOSITION) -- both against a whitespace-normalized copy -- BEFORE
the INSERT, refusing loudly (exit nonzero, nothing written, teach-text naming the grammar and
user-guide/USER-RECIPES-FAQ.md's "Your review queue" section) on any single-field defect, and
accepting a well-formed statement byte-exact. `bootstrap/templates/pickup.tmpl`'s review_queue()
reader renders the MAINTAINER-REVIEW-QUEUE section by DERIVING each SLUG's current state from the
highest-ledger-row-id row among BOTH prefixes -- proving, live, the three state-transition rules
the grammar's "Semantics" paragraph states: a same-SLUG `review:` row RE-RANKS (supersedes the
prior rendering), a `review-done:` row REMOVES the SLUG from the rendered queue, and a later
`review:` row RE-OPENS it.

CASES (all live subprocess runs of the real `led`/`pickup` verbs against a real scratch
deployment -- never a mock):

  ADOPT                          -- bootstrap/track-work.sh stands up the scratch deployment.

  -- `review:` grammar, RED --
  RED-REVIEW-FIELDCOUNT          -- a 3-field `review:` statement (missing POINTER) is REFUSED,
                                     row count witnessed UNCHANGED before/after (atomicity by
                                     refusal-before-write).
  RED-REVIEW-BAD-SLUG            -- a 4-field statement whose SLUG is not a bare slug
                                     (uppercase/space) is REFUSED, row count unchanged.
  RED-REVIEW-NON-INTEGER-RANK    -- a 4-field statement whose RANK is not a positive integer
                                     ("first") is REFUSED, row count unchanged.
  RED-REVIEW-ZERO-RANK           -- a 4-field statement whose RANK is "0" (not positive) is
                                     REFUSED, row count unchanged.
  RED-REVIEW-EMPTY-WHAT          -- a 4-field statement whose WHAT field is empty (whitespace
                                     only) is REFUSED, row count unchanged.
  RED-REVIEW-EMPTY-POINTER       -- a 4-field statement whose POINTER field is empty is REFUSED,
                                     row count unchanged.

  -- `review-done:` grammar, RED --
  RED-REVIEW-DONE-FIELDCOUNT     -- a 1-field `review-done:` statement (missing DISPOSITION) is
                                     REFUSED, row count unchanged.
  RED-REVIEW-DONE-BAD-SLUG       -- a 2-field `review-done:` statement whose SLUG is not a bare
                                     slug shape (uppercase/space) is REFUSED, row count unchanged.

  -- GREEN, both grammars plus the derived-state rendering --
  GREEN-OPEN                     -- a well-formed `review:` statement is ACCEPTED, stored
                                     byte-exact, and renders in `./pickup`'s
                                     MAINTAINER-REVIEW-QUEUE section at its declared rank.
  GREEN-RERANK                   -- a second well-formed `review:` statement for the SAME SLUG,
                                     a different RANK/WHAT/POINTER, is ACCEPTED; the rendered
                                     queue shows ONLY the new rank/what/pointer for that SLUG
                                     (the prior row's fields no longer appear) -- re-ranking
                                     supersedes by latest-row-wins, no `--supersedes` flag used.
  GREEN-TICK                     -- a well-formed `review-done:` statement for that SLUG is
                                     ACCEPTED; the SLUG disappears from the rendered open queue
                                     entirely.
  GREEN-REOPEN                   -- a further `review:` statement for the SAME SLUG is ACCEPTED;
                                     the SLUG reappears in the rendered open queue -- re-opening
                                     after a tick, proven live.
  GREEN-TICK-COMMAND              -- the rendered queue's printed tick one-liner for an open
                                     entry is the EXACT `./led decision "review-done: ..."`
                                     command shape (copy-paste correctness).
  GREEN-EMPTY-QUEUE                -- a virgin deployment with NO review:/review-done: rows on
                                     record renders the section's own explicit
                                     "(no open review-queue entries on record)" line, never
                                     silence.

Scratch-only: schema/kern/role derived from a throwaway name (`SCRATCH_NAME` below, distinct
from every other fixture's own scratch name in this repo) in the TOY db (192.168.122.1) plus a
throwaway tempdir -- both dropped/removed after, UNLESS a case FAILS (left standing as evidence).

Usage: python3 seen-red/review-queue-intake/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402 (filing/pghost_resolve.py via seen-red/_fixture_env.py -- never a literal host default)


REPO = Path(__file__).resolve().parents[2]
TRACK_WORK = REPO / "bootstrap" / "track-work.sh"
PGHOST, DB = fixture_pghost(), "toy"
SCRATCH_NAME = "rqfixture"
SCHEMA, KERN, ROLE = SCRATCH_NAME, f"{SCRATCH_NAME}_kernel", f"{SCRATCH_NAME}_rw"

REVIEW_FIELDCOUNT = "review: key-generation | 1 | decide the signing-key ceremony"
REVIEW_BAD_SLUG = "review: Key Generation | 1 | decide the signing-key ceremony | vestigial_documentation/design/MAINT-MAINTAINER-DECISION-BRIEF.md"
REVIEW_NON_INTEGER_RANK = "review: key-generation | first | decide the signing-key ceremony | vestigial_documentation/design/MAINT-MAINTAINER-DECISION-BRIEF.md"
REVIEW_ZERO_RANK = "review: key-generation | 0 | decide the signing-key ceremony | vestigial_documentation/design/MAINT-MAINTAINER-DECISION-BRIEF.md"
REVIEW_EMPTY_WHAT = "review: key-generation | 1 |    | vestigial_documentation/design/MAINT-MAINTAINER-DECISION-BRIEF.md"
REVIEW_EMPTY_POINTER = "review: key-generation | 1 | decide the signing-key ceremony |    "

REVIEW_DONE_FIELDCOUNT = "review-done: key-generation"
REVIEW_DONE_BAD_SLUG = "review-done: Key Generation | approved as written"

REVIEW_OPEN = "review: key-generation | 1 | decide the signing-key generation ceremony | vestigial_documentation/design/MAINT-MAINTAINER-DECISION-BRIEF.md"
REVIEW_RERANK = "review: key-generation | 3 | re-ranked -- deprioritized behind the trust-domain decision | vestigial_documentation/design/MAINT-MAINTAINER-DECISION-BRIEF.md"
REVIEW_TICK = "review-done: key-generation | approved the brief's proposed ceremony as written"
REVIEW_REOPEN = "review: key-generation | 2 | reopened -- ceremony needs a second look after the signed-chain-head question | vestigial_documentation/design/MAINT-MAINTAINER-DECISION-BRIEF.md"


def _psql(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["psql", "-h", PGHOST, "-d", DB, *args],
                           capture_output=True, text=True)


def _drop_scratch() -> None:
    _psql("-v", "ON_ERROR_STOP=0", "-q",
          "-c", f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE;",
          "-c", f"DROP SCHEMA IF EXISTS {KERN} CASCADE;",
          "-c", f"DROP ROLE IF EXISTS {ROLE};")


def _run(dest: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    return subprocess.run([str(dest / args[0]), *args[1:]],
                           capture_output=True, text=True, cwd=str(dest), env=full_env)


def _ledger_row_count(dest: Path) -> int:
    r = _psql("-tAc", f"SET ROLE {ROLE}; SELECT count(*) FROM {SCHEMA}.ledger;")
    return int(r.stdout.strip().splitlines()[-1])


def _review_queue_section(dest: Path) -> str:
    r_pickup = _run(dest, "pickup")
    out = r_pickup.stdout
    start = out.find("### SECTION: MAINTAINER-REVIEW-QUEUE")
    end = out.find("### SECTION:", start + 1)
    return out[start:end if end != -1 else None].strip() if start != -1 else ""


def main() -> int:
    failures: list[str] = []
    transcript: list[str] = []

    def log(line: str) -> None:
        print(line)
        transcript.append(line)

    def red_case(name: str, statement: str, expect_substr: str) -> None:
        before = _ledger_row_count(dest)
        r = _run(dest, "led", "decision", statement)
        after = _ledger_row_count(dest)
        refused = r.returncode != 0 and "REFUSED" in r.stderr and expect_substr in r.stderr
        unchanged = before == after
        ok = refused and unchanged
        if not ok:
            failures.append(f"{name}: exit={r.returncode} refused={refused} before={before} "
                             f"after={after}\nSTDERR:\n{r.stderr}")
        log(f"{name}: exit={r.returncode} refused={refused} row-count before={before} "
            f"after={after} (unchanged={unchanged}) -- {'PASS' if ok else 'FAIL'}")

    def green_case(name: str, statement: str) -> None:
        before = _ledger_row_count(dest)
        r = _run(dest, "led", "decision", statement)
        after = _ledger_row_count(dest)
        accepted = r.returncode == 0
        grew = after == before + 1
        ok = accepted and grew
        if not ok:
            failures.append(f"{name}: exit={r.returncode} accepted={accepted} before={before} "
                             f"after={after}\nSTDERR:\n{r.stderr}")
        log(f"{name}: exit={r.returncode} accepted={accepted} row-count before={before} "
            f"after={after} (grew-by-one={grew}) -- {'PASS' if ok else 'FAIL'}")
        r_stmt = _psql("-tAc", f"SET ROLE {ROLE}; SELECT statement FROM {SCHEMA}.ledger "
                                f"WHERE kind = 'decision' ORDER BY id DESC LIMIT 1;")
        stored_lines = [ln for ln in r_stmt.stdout.splitlines() if ln.strip()]
        stored_last = stored_lines[-1] if stored_lines else ""
        byte_exact = statement.strip() == stored_last
        if not byte_exact:
            failures.append(f"{name}: stored statement is not byte-exact\n"
                             f"EXPECTED:\n{statement!r}\nSTORED:\n{stored_last!r}")
        log(f"{name}: stored statement is byte-exact -- {'PASS' if byte_exact else 'FAIL'}")

    _drop_scratch()
    tmpdir = Path(tempfile.mkdtemp(prefix="review-queue-intake-fixture-"))
    dest = tmpdir / "project"

    # --------------------------------------------------------------------------------- ADOPT
    r = subprocess.run([str(TRACK_WORK), str(dest), "--name", SCRATCH_NAME, "--db", DB,
                        "--host", PGHOST, "--schema", SCHEMA, "--kern", KERN, "--role", ROLE],
                        capture_output=True, text=True, cwd=str(REPO))
    ok = r.returncode == 0 and (dest / "deployment.json").exists()
    if not ok:
        failures.append(f"ADOPT: exit={r.returncode}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
    log(f"ADOPT: track-work.sh exit={r.returncode} deployment.json="
        f"{(dest / 'deployment.json').exists()} -- {'PASS' if ok else 'FAIL'}")

    # ------------------------------------------------------------------- GREEN-EMPTY-QUEUE
    # Read the section BEFORE any review:/review-done: row exists on this virgin deployment.
    section = _review_queue_section(dest)
    empty_ok = "(no open review-queue entries on record)" in section
    if not empty_ok:
        failures.append(f"GREEN-EMPTY-QUEUE: expected the honest empty-queue line, got:\n{section}")
    log(f"GREEN-EMPTY-QUEUE: virgin deployment renders the explicit empty-queue line -- "
        f"{'PASS' if empty_ok else 'FAIL'}")

    # ---------------------------------------------------------------------------- RED cases
    red_case("RED-REVIEW-FIELDCOUNT", REVIEW_FIELDCOUNT, "got 3")
    red_case("RED-REVIEW-BAD-SLUG", REVIEW_BAD_SLUG, "SLUG")
    red_case("RED-REVIEW-NON-INTEGER-RANK", REVIEW_NON_INTEGER_RANK, "RANK")
    red_case("RED-REVIEW-ZERO-RANK", REVIEW_ZERO_RANK, "RANK")
    red_case("RED-REVIEW-EMPTY-WHAT", REVIEW_EMPTY_WHAT, "WHAT")
    red_case("RED-REVIEW-EMPTY-POINTER", REVIEW_EMPTY_POINTER, "POINTER")
    red_case("RED-REVIEW-DONE-FIELDCOUNT", REVIEW_DONE_FIELDCOUNT, "got 1")
    red_case("RED-REVIEW-DONE-BAD-SLUG", REVIEW_DONE_BAD_SLUG, "SLUG")

    # --------------------------------------------------------------------------- GREEN-OPEN
    green_case("GREEN-OPEN", REVIEW_OPEN)
    section = _review_queue_section(dest)
    open_ok = ("[1] key-generation" in section
               and "decide the signing-key generation ceremony" in section
               and "vestigial_documentation/design/MAINT-MAINTAINER-DECISION-BRIEF.md" in section)
    if not open_ok:
        failures.append(f"GREEN-OPEN: expected rank-1 key-generation entry, got:\n{section}")
    log(f"GREEN-OPEN: queue renders the open entry at rank 1 -- {'PASS' if open_ok else 'FAIL'}")

    tick_cmd_ok = 'tick:    ./led decision "review-done: key-generation | <disposition>"' in section
    if not tick_cmd_ok:
        failures.append(f"GREEN-TICK-COMMAND: expected exact tick one-liner, got:\n{section}")
    log(f"GREEN-TICK-COMMAND: printed tick command is the exact copy-paste shape -- "
        f"{'PASS' if tick_cmd_ok else 'FAIL'}")

    # ------------------------------------------------------------------------- GREEN-RERANK
    green_case("GREEN-RERANK", REVIEW_RERANK)
    section = _review_queue_section(dest)
    rerank_ok = ("[3] key-generation" in section
                 and "re-ranked -- deprioritized behind the trust-domain decision" in section
                 and "[1] key-generation" not in section
                 and "decide the signing-key generation ceremony" not in section)
    if not rerank_ok:
        failures.append(f"GREEN-RERANK: expected ONLY the re-ranked fields to render, got:\n{section}")
    log(f"GREEN-RERANK: latest review: row supersedes the prior rank/what/pointer -- "
        f"{'PASS' if rerank_ok else 'FAIL'}")

    # --------------------------------------------------------------------------- GREEN-TICK
    green_case("GREEN-TICK", REVIEW_TICK)
    section = _review_queue_section(dest)
    tick_ok = "key-generation" not in section
    if not tick_ok:
        failures.append(f"GREEN-TICK: expected key-generation removed from the open queue, got:\n{section}")
    log(f"GREEN-TICK: ticked SLUG disappears from the rendered open queue -- "
        f"{'PASS' if tick_ok else 'FAIL'}")

    # ------------------------------------------------------------------------- GREEN-REOPEN
    green_case("GREEN-REOPEN", REVIEW_REOPEN)
    section = _review_queue_section(dest)
    reopen_ok = ("[2] key-generation" in section
                 and "reopened -- ceremony needs a second look" in section)
    if not reopen_ok:
        failures.append(f"GREEN-REOPEN: expected key-generation reopened at rank 2, got:\n{section}")
    log(f"GREEN-REOPEN: a review: row filed after review-done: re-opens the SLUG -- "
        f"{'PASS' if reopen_ok else 'FAIL'}")
    log("--- pickup MAINTAINER-REVIEW-QUEUE section after re-open (verbatim) ---")
    log(section)
    transcript.append(section)
    log("--- end pickup MAINTAINER-REVIEW-QUEUE section ---")

    if failures:
        print(f"\nreview-queue-intake fixture: {len(failures)} FAILURE(S) -- scratch substrate "
              f"left standing as evidence:\n  tempdir: {tmpdir}\n  schema:  {SCHEMA} / {KERN} / "
              f"{ROLE} (db {DB}@{PGHOST})")
        for f in failures:
            print(f"\n!! {f}")
        return 1

    _drop_scratch()
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\nreview-queue-intake fixture: all cases PASS, scratch substrate torn down to zero "
          f"residue (tempdir removed, schema {SCHEMA}/{KERN}/role {ROLE} dropped).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
