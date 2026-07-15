#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T18:49:07Z
#   last-change: 2026-07-15T18:49:07Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures — both-polarity live proof for ledger item `led-refs-flag-order-parser-bug`
(gates/fixture_census.py REGISTRY entry "led-refs-flag-order-parser-bug").

THE DEFECT: `./led`'s generic `<kind> <statement...>` path (and `led review`'s own
`<statement...>` tail) captures the variadic statement greedily. A flag placed AFTER the
statement -- e.g. `./led decision "some text" --refs row:16` -- arrives as ordinary trailing
shell words, which the top-of-file flag loop (consumed BEFORE the kind/statement dispatch) never
sees. The trailing `--refs row:16` tokens were silently swallowed INTO the statement's own prose
instead of being parsed as a flag, so the typed `refs` column landed NULL with no error. This bit
the orchestrator (autoharn1 ledger rows 1053/1054) and an experience-world reviewer twice in one
day (rows 65/66/71, again at 87), each costing a superseding rewrite -- a silent mis-parse that
corrupts the record, ADR-0000's lying-signature class.

THE FIX (bootstrap/templates/led.tmpl): a WARN-ONLY tripwire (warn_flag_in_statement) already
existed for this exact shape (BACKLOG run7 row 71) but proved insufficient -- a warning easy to
miss in scrollback did not stop the defect from recurring twice more. It is replaced with
refuse_flag_in_statement(), called immediately after `kind`/`statement` (and `led review`'s own
regards/verdict/independence) are peeled off argv, BEFORE any DB write. It scans the ORIGINAL,
UNJOINED shell argv words that make up the statement (never a re-split of the joined "$*" string)
and REFUSES, loudly, with teach-text showing the corrected invocation, iff one of those words is
an EXACT, WHOLE match for a known led flag token (LED_FLAG_VOCAB). This is the principled
boundary against false positives: a statement that legitimately QUOTES a flag-like token inside
ONE shell argument (e.g. `"this references --refs flag in prose"`, one argv word, "--refs" only
a substring of it) is never refused -- only a flag arriving as its OWN separate shell argument
matches.

CASES (all live subprocess runs of the real `./led` against a real scratch deployment, following
seen-red/actual-intake-validation/run_fixtures.py's own scratch-and-drop pattern):

  ADOPT                    -- bootstrap/track-work.sh stands up the scratch deployment.
  RED-TRAILING-REFS        -- `./led decision "<text>" --refs row:1` is REFUSED (nonzero exit),
                               teach-text names the trap and shows the corrected invocation, row
                               count witnessed UNCHANGED before/after.
  RED-TRAILING-SUPERSEDES  -- same shape with --supersedes <id>, REFUSED, row count unchanged
                               (proves the check is not --refs-specific -- LED_FLAG_VOCAB-wide).
  GREEN-FLAGS-BEFORE       -- `./led --refs row:1 decision "<text>"` (flags-before-statement,
                               the documented/correct order) is ACCEPTED, a real row lands, and
                               the refs column is stored byte-exact via `led show`.
  GREEN-QUOTED-MENTION     -- a statement that legitimately QUOTES "--refs" inside one shell
                               argument (never its own separate argv word) is ACCEPTED unchanged
                               -- the false-positive case this item's boundary must not trip.

Usage: python3 seen-red/led-refs-flag-order-parser-bug/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
TRACK_WORK = REPO / "bootstrap" / "track-work.sh"
PGHOST, DB = fixture_pghost(), "toy"
SCRATCH_NAME = "lrfopfixture"
SCHEMA, KERN, ROLE = SCRATCH_NAME, f"{SCRATCH_NAME}_kernel", f"{SCRATCH_NAME}_rw"
TAG = f"seen-red-led-refs-flag-order-{int(time.time())}"


def _psql(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["psql", "-h", PGHOST, "-d", DB, *args],
                           capture_output=True, text=True)


def _drop_scratch() -> None:
    _psql("-v", "ON_ERROR_STOP=0", "-q",
          "-c", f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE;",
          "-c", f"DROP SCHEMA IF EXISTS {KERN} CASCADE;",
          "-c", f"DROP ROLE IF EXISTS {ROLE};")


def _run(dest: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(dest / args[0]), *args[1:]],
                           capture_output=True, text=True, cwd=str(dest))


def _ledger_row_count(dest: Path) -> int:
    r = _psql("-tAc", f"SET ROLE {ROLE}; SELECT count(*) FROM {SCHEMA}.ledger;")
    return int(r.stdout.strip().splitlines()[-1])


def main() -> int:
    failures: list[str] = []
    transcript: list[str] = []

    def log(line: str) -> None:
        print(line)
        transcript.append(line)

    _drop_scratch()
    tmpdir = Path(tempfile.mkdtemp(prefix="led-refs-flag-order-parser-bug-fixture-"))
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
    if not ok:
        print(f"\nADOPT FAILED, aborting -- scratch left standing:\n  tempdir: {tmpdir}")
        for f in failures:
            print(f"\n!! {f}")
        return 1

    # ------------------------------------------------------------------------- RED-TRAILING-REFS
    before = _ledger_row_count(dest)
    r = _run(dest, "led", "decision", f"{TAG}: trailing --refs probe", "--refs", "row:1")
    after = _ledger_row_count(dest)
    refused = r.returncode != 0
    teaches_trap = "REFUSED" in r.stderr and "--refs" in r.stderr
    teaches_correction = "led-refs-flag-order-parser-bug" in r.stderr and "BEFORE the statement" in r.stderr
    shows_corrected_invocation = "./led [flags] decision --refs row:1" in r.stderr
    unchanged = before == after
    ok = refused and teaches_trap and teaches_correction and shows_corrected_invocation and unchanged
    if not ok:
        failures.append(f"RED-TRAILING-REFS: exit={r.returncode} refused={refused} "
                         f"teaches_trap={teaches_trap} teaches_correction={teaches_correction} "
                         f"shows_corrected_invocation={shows_corrected_invocation} "
                         f"before={before} after={after}\nSTDERR:\n{r.stderr}")
    log(f"RED-TRAILING-REFS: exit={r.returncode} refused={refused} teaches_trap={teaches_trap} "
        f"teaches_correction={teaches_correction} shows_corrected_invocation={shows_corrected_invocation} "
        f"row-count before={before} after={after} (unchanged={unchanged}) -- "
        f"{'PASS' if ok else 'FAIL'}")

    # ------------------------------------------------------------------- RED-TRAILING-SUPERSEDES
    before = _ledger_row_count(dest)
    r = _run(dest, "led", "decision", f"{TAG}: trailing --supersedes probe", "--supersedes", "1")
    after = _ledger_row_count(dest)
    refused = r.returncode != 0
    teaches_trap = "REFUSED" in r.stderr and "--supersedes" in r.stderr
    unchanged = before == after
    ok = refused and teaches_trap and unchanged
    if not ok:
        failures.append(f"RED-TRAILING-SUPERSEDES: exit={r.returncode} refused={refused} "
                         f"teaches_trap={teaches_trap} before={before} after={after}\n"
                         f"STDERR:\n{r.stderr}")
    log(f"RED-TRAILING-SUPERSEDES: exit={r.returncode} refused={refused} "
        f"teaches_trap={teaches_trap} row-count before={before} after={after} "
        f"(unchanged={unchanged}) -- {'PASS' if ok else 'FAIL'}")

    # --------------------------------------------------------------------- GREEN-FLAGS-BEFORE
    r = _run(dest, "led", "--refs", "row:1", "decision", f"{TAG}: flags-before-statement probe")
    accepted = r.returncode == 0
    if not accepted:
        failures.append(f"GREEN-FLAGS-BEFORE: exit={r.returncode}\nSTDERR:\n{r.stderr}")
    log(f"GREEN-FLAGS-BEFORE: exit={r.returncode} accepted={accepted} -- "
        f"{'PASS' if accepted else 'FAIL'}")
    if accepted:
        r_row = _psql("-tAc", f"SET ROLE {ROLE}; SELECT statement, refs FROM {SCHEMA}.ledger "
                               f"WHERE kind = 'decision' ORDER BY id DESC LIMIT 1;")
        line = [ln for ln in r_row.stdout.splitlines() if ln.strip()][-1]
        stmt_col, _, refs_col = line.partition("|")
        stmt_ok = stmt_col.strip() == f"{TAG}: flags-before-statement probe"
        refs_ok = refs_col.strip() == "row:1"
        if not (stmt_ok and refs_ok):
            failures.append(f"GREEN-FLAGS-BEFORE: stored row mismatch -- statement_ok={stmt_ok} "
                             f"refs_ok={refs_ok}\nROW: {line!r}")
        log(f"GREEN-FLAGS-BEFORE: statement byte-exact={stmt_ok}, refs column stored "
            f"byte-exact='row:1'={refs_ok} -- {'PASS' if stmt_ok and refs_ok else 'FAIL'}")

    # --------------------------------------------------------------------- GREEN-QUOTED-MENTION
    # "--refs" appears here, but as a SUBSTRING of ONE shell argument (the whole sentence is a
    # single argv word) -- never its own separate argv token. Must NOT be refused.
    quoted_statement = f"{TAG}: reporting someone else's command verbatim, it used --refs row:99 in it"
    before = _ledger_row_count(dest)
    r = _run(dest, "led", "decision", quoted_statement)
    after = _ledger_row_count(dest)
    accepted = r.returncode == 0
    grew = after == before + 1
    ok = accepted and grew
    if not ok:
        failures.append(f"GREEN-QUOTED-MENTION: exit={r.returncode} accepted={accepted} "
                         f"before={before} after={after}\nSTDERR:\n{r.stderr}")
    log(f"GREEN-QUOTED-MENTION: exit={r.returncode} accepted={accepted} row-count before={before} "
        f"after={after} (grew-by-one={grew}) -- {'PASS' if ok else 'FAIL'}")
    if accepted:
        r_row = _psql("-tAc", f"SET ROLE {ROLE}; SELECT statement FROM {SCHEMA}.ledger "
                               f"WHERE kind = 'decision' ORDER BY id DESC LIMIT 1;")
        stored = [ln for ln in r_row.stdout.splitlines() if ln.strip()][-1].strip()
        byte_exact = stored == quoted_statement
        if not byte_exact:
            failures.append(f"GREEN-QUOTED-MENTION: stored statement is not byte-exact\n"
                             f"EXPECTED:\n{quoted_statement!r}\nSTORED:\n{stored!r}")
        log(f"GREEN-QUOTED-MENTION: stored statement is byte-exact (the quoted '--refs' mention "
            f"survived, unrefused) -- {'PASS' if byte_exact else 'FAIL'}")

    if failures:
        print(f"\nled-refs-flag-order-parser-bug fixture: {len(failures)} FAILURE(S) -- scratch "
              f"substrate left standing as evidence:\n  tempdir: {tmpdir}\n  schema:  {SCHEMA} / "
              f"{KERN} / {ROLE} (db {DB}@{PGHOST})")
        for f in failures:
            print(f"\n!! {f}")
        return 1

    _drop_scratch()
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\nled-refs-flag-order-parser-bug fixture: all cases PASS, scratch substrate torn "
          f"down to zero residue (tempdir removed, schema {SCHEMA}/{KERN}/role {ROLE} dropped).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
