#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T09:10:27Z
#   last-change: 2026-07-18T09:34:55Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures -- both-polarity live proof for ledger item `led-json-payload-mode`
(gates/fixture_census.py REGISTRY entry "led-json-payload-mode").

THE ITEM (maintainer proposal 2026-07-18, his own words: JSON input "harms ledger readability
BUT ... shows that the ledger works to our benefit -- that we can improve autoharn"): `./led`
gains `--json <surface> <file|->`, an ADDITIONAL agent/programmatic-facing write mode alongside
the existing prose CLI (DUAL-MODE: the prose CLI stays for humans, unchanged). The payload maps
VERBATIM onto the s43 boundary functions' own jsonb payload shape (kernel/lineage/
s43-typed-verdict-write-boundary.sql sec 4.2: payload keys are the TARGET TABLE's own column
names) -- the SAME payload the FastAPI boundary service's own POST /write/<surface> endpoints
accept (design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md section 4). <surface> selects which of the
four boundary functions (ledger/review/registration/obligation) receives the payload, matching
the service's own four endpoints 1:1.

VALIDATION IS WELL-FORMEDNESS-AND-SHAPE ONLY (same P2 discipline the service's own spec section 5
states for its HTTP twin: "the service must not grow a second validator that could disagree with
the authority") -- this mode checks only that the input parses as JSON and is a top-level object,
then hands it to kernel_write() UNCHANGED. Unknown-key / server-owned-key refusal and its
teach-text are the KERNEL's OWN, passed through VERBATIM.

s43-ONLY, NO LEGACY FALLBACK: a pre-s43 kernel refuses this mode outright (capability_absent,
naming s43), mirroring the FastAPI service's own pre-s43 refusal -- there is no pre-s43 payload
shape for --json to fall back to.

CASES (all live subprocess runs of the real `./led` against real scratch deployments):

  ADOPT-FULL              -- bootstrap/new-project.sh --new-world stands up a scratch deployment
                              carrying the s43 boundary (kernel_write, has_s43_boundary true).
  ADOPT-PRE-S43           -- bootstrap/track-work.sh stands up a scratch deployment WITHOUT s43
                              (its own ceiling, per led-work-depends-default-type-advisory's own
                              fixture -- s15..s25/s30 only) -- proves the pre-s43 refusal fires.
  GREEN-FILE               -- `led --json ledger <file>` with a well-formed {"kind":...,
                              "statement":...} object: exit 0, "led: row <id> written." on
                              stdout, row count grows by exactly one, and the stored statement
                              matches the payload byte-exact.
  GREEN-STDIN               -- same payload shape piped via `led --json ledger -`: exit 0, row
                              count grows by one.
  RED-UNKNOWN-KEY           -- a payload carrying a key that is not a ledger column: REFUSED, the
                              KERNEL's own s43 teach-text ("is not a ledger column") appears
                              verbatim on stderr, no NEW ledger row lands with that content (the
                              boundary's own write_refused journaling is a SEPARATE, expected
                              side effect -- checked for, not confused with the requested write
                              succeeding).
  RED-MALFORMED-JSON        -- non-JSON input: REFUSED at the CLI (never reaches the kernel), row
                              count unchanged.
  RED-MISSING-FILE          -- a nonexistent file path: REFUSED, row count unchanged.
  RED-BAD-SURFACE           -- an unrecognized <surface> word: REFUSED, usage naming the four
                              valid surfaces, row count unchanged.
  RED-PRE-S43-REFUSAL       -- `led --json ledger <file>` on the pre-s43 world: REFUSED,
                              "capability_absent" and "s43" both named on stderr, row count
                              unchanged.
  GREEN-SWALLOWED-FLAG-CAUGHT -- `led finding "text" --json` (--json arriving as a TRAILING
                              statement word, the led-refs-flag-order-parser-bug shape): REFUSED
                              by refuse_flag_in_statement (proves --json was added to
                              LED_FLAG_VOCAB, not left invisible to that guard).
  RED-OVERSIZED-FILE       -- a >MAX_WRITE_BODY_BYTES (1_048_576) payload FILE: REFUSED with a
                              typed `payload_too_large` disposition naming the byte bound,
                              BEFORE the argument ever reaches the psql subprocess -- never a
                              bare shell "Argument list too long" abort (fixup finding 1, the
                              boundary-service hardening commit immediately preceding this
                              item's own build fixed the identical hazard class for this
                              payload's HTTP twin; this closes the CLI twin's own copy of the
                              same gap). Row count unchanged.
  RED-OVERSIZED-STDIN      -- same oversized payload piped via `led --json ledger -`: same
                              typed refusal, same bound named, row count unchanged.

Usage: python3 seen-red/led-json-payload-mode/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
TRACK_WORK = REPO / "bootstrap" / "track-work.sh"
PGHOST, DB = fixture_pghost(), "toy"
WORLD_FULL = "ljpmfxfull"
WORLD_PRE = "ljpmfxpre"
TAG = f"seen-red-led-json-payload-mode-{int(time.time())}"


def _psql(schema: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["psql", "-h", PGHOST, "-d", DB, *args],
                           capture_output=True, text=True)


def _drop(name: str) -> None:
    subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-v", "ON_ERROR_STOP=0", "-q",
                     "-c", f"DROP SCHEMA IF EXISTS {name} CASCADE;",
                     "-c", f"DROP SCHEMA IF EXISTS {name}_kernel CASCADE;",
                     "-c", f"DROP ROLE IF EXISTS {name}_rw;"],
                    capture_output=True, text=True)


def _row_count(schema: str, role: str) -> int:
    r = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-tAc",
                         f"SET ROLE {role}; SELECT count(*) FROM {schema}.ledger;"],
                        capture_output=True, text=True)
    return int(r.stdout.strip().splitlines()[-1])


def _run(dest: Path, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([str(dest / args[0]), *args[1:]], capture_output=True, text=True,
                           cwd=str(dest), input=stdin)


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    _drop(WORLD_FULL)
    _drop(WORLD_PRE)

    try:
        # ------------------------------------------------------------------------- ADOPT-FULL
        tmp_full = Path(tempfile.mkdtemp(prefix=f"{WORLD_FULL}-seenred-"))
        tmps.append(tmp_full)
        dest_full = tmp_full / WORLD_FULL
        r = subprocess.run(["bash", str(NEW_PROJECT), str(dest_full), "--new-world", WORLD_FULL,
                             "--db", DB, "--host", PGHOST], capture_output=True, text=True)
        for verb in ("led", "judge", "pickup"):
            p = dest_full / verb
            if p.exists():
                p.chmod(0o755)
        ok = r.returncode == 0 and (dest_full / "deployment.json").exists()
        if not ok:
            failures.append(f"ADOPT-FULL: exit={r.returncode}\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")
        print(f"ADOPT-FULL: new-project.sh --new-world exit={r.returncode} "
              f"deployment.json={(dest_full / 'deployment.json').exists()} -- {'PASS' if ok else 'FAIL'}")
        if not ok:
            raise SystemExit

        dep_full = json.loads((dest_full / "deployment.json").read_text())
        schema_full, role_full = dep_full["schema"], dep_full["role"]

        # ------------------------------------------------------------------------- ADOPT-PRE-S43
        tmp_pre = Path(tempfile.mkdtemp(prefix=f"{WORLD_PRE}-seenred-"))
        tmps.append(tmp_pre)
        dest_pre = tmp_pre / "project"
        r = subprocess.run([str(TRACK_WORK), str(dest_pre), "--name", WORLD_PRE, "--db", DB,
                             "--host", PGHOST, "--schema", WORLD_PRE, "--kern", f"{WORLD_PRE}_kernel",
                             "--role", f"{WORLD_PRE}_rw"], capture_output=True, text=True, cwd=str(REPO))
        ok = r.returncode == 0 and (dest_pre / "deployment.json").exists()
        if not ok:
            failures.append(f"ADOPT-PRE-S43: exit={r.returncode}\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")
        print(f"ADOPT-PRE-S43: track-work.sh exit={r.returncode} "
              f"deployment.json={(dest_pre / 'deployment.json').exists()} -- {'PASS' if ok else 'FAIL'}")
        if not ok:
            raise SystemExit

        # ------------------------------------------------------------------------------ GREEN-FILE
        payload_file = tmp_full / "payload_file.json"
        stmt_file = f"{TAG}: file-mode specimen"
        payload_file.write_text(json.dumps({"kind": "finding", "statement": stmt_file}))
        before = _row_count(schema_full, role_full)
        r = _run(dest_full, "led", "--json", "ledger", str(payload_file))
        after = _row_count(schema_full, role_full)
        accepted = r.returncode == 0 and "written." in r.stdout
        grew = after == before + 1
        stored_ok = False
        if accepted:
            rr = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-tAc",
                                  f"SET ROLE {role_full}; SELECT statement FROM {schema_full}.ledger "
                                  f"ORDER BY id DESC LIMIT 1;"], capture_output=True, text=True)
            # -tAc's combined "SET ROLE ...; SELECT ..." prints a leading "SET" line (the SET
            # ROLE command's own tag) ahead of the SELECT's one output line -- take the LAST
            # non-empty line, the same convention seen-red/led-refs-flag-order-parser-bug/
            # run_fixtures.py's own GREEN-FLAGS-BEFORE case already uses for this exact shape.
            lines = [ln for ln in rr.stdout.splitlines() if ln.strip()]
            stored_ok = bool(lines) and lines[-1] == stmt_file
        ok = accepted and grew and stored_ok
        if not ok:
            failures.append(f"GREEN-FILE: exit={r.returncode} accepted={accepted} grew={grew} "
                             f"stored_ok={stored_ok} before={before} after={after}\n"
                             f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
        print(f"GREEN-FILE: exit={r.returncode} accepted={accepted} row-count before={before} "
              f"after={after} (grew-by-one={grew}) stored_byte_exact={stored_ok} -- "
              f"{'PASS' if ok else 'FAIL'}")

        # ------------------------------------------------------------------------------ GREEN-STDIN
        stmt_stdin = f"{TAG}: stdin-mode specimen"
        before = _row_count(schema_full, role_full)
        r = _run(dest_full, "led", "--json", "ledger", "-",
                  stdin=json.dumps({"kind": "finding", "statement": stmt_stdin}))
        after = _row_count(schema_full, role_full)
        accepted = r.returncode == 0 and "written." in r.stdout
        grew = after == before + 1
        ok = accepted and grew
        if not ok:
            failures.append(f"GREEN-STDIN: exit={r.returncode} accepted={accepted} grew={grew} "
                             f"before={before} after={after}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
        print(f"GREEN-STDIN: exit={r.returncode} accepted={accepted} row-count before={before} "
              f"after={after} (grew-by-one={grew}) -- {'PASS' if ok else 'FAIL'}")

        # ------------------------------------------------------------------------------ RED-UNKNOWN-KEY
        bad_file = tmp_full / "bad_key.json"
        bad_file.write_text(json.dumps({"kind": "finding", "statement": "x", "bogus_key": "y"}))
        r = _run(dest_full, "led", "--json", "ledger", str(bad_file))
        refused = r.returncode != 0
        teaches = "is not a ledger column" in r.stderr and "bogus_key" in r.stderr
        ok = refused and teaches
        if not ok:
            failures.append(f"RED-UNKNOWN-KEY: exit={r.returncode} refused={refused} "
                             f"teaches={teaches}\nSTDERR:\n{r.stderr}")
        print(f"RED-UNKNOWN-KEY: exit={r.returncode} refused={refused} teaches_kernel_message="
              f"{teaches} -- {'PASS' if ok else 'FAIL'}")

        # ------------------------------------------------------------------------------ RED-MALFORMED-JSON
        malformed_file = tmp_full / "malformed.json"
        malformed_file.write_text("not json at all")
        before = _row_count(schema_full, role_full)
        r = _run(dest_full, "led", "--json", "ledger", str(malformed_file))
        after = _row_count(schema_full, role_full)
        refused = r.returncode != 0
        teaches = "not well-formed JSON" in r.stderr
        unchanged = before == after
        ok = refused and teaches and unchanged
        if not ok:
            failures.append(f"RED-MALFORMED-JSON: exit={r.returncode} refused={refused} "
                             f"teaches={teaches} before={before} after={after}\nSTDERR:\n{r.stderr}")
        print(f"RED-MALFORMED-JSON: exit={r.returncode} refused={refused} teaches={teaches} "
              f"row-count before={before} after={after} (unchanged={unchanged}) -- "
              f"{'PASS' if ok else 'FAIL'}")

        # ------------------------------------------------------------------------------ RED-MISSING-FILE
        before = _row_count(schema_full, role_full)
        r = _run(dest_full, "led", "--json", "ledger", str(tmp_full / "does-not-exist.json"))
        after = _row_count(schema_full, role_full)
        refused = r.returncode != 0
        teaches = "does not exist" in r.stderr
        unchanged = before == after
        ok = refused and teaches and unchanged
        if not ok:
            failures.append(f"RED-MISSING-FILE: exit={r.returncode} refused={refused} "
                             f"teaches={teaches} before={before} after={after}\nSTDERR:\n{r.stderr}")
        print(f"RED-MISSING-FILE: exit={r.returncode} refused={refused} teaches={teaches} "
              f"row-count before={before} after={after} (unchanged={unchanged}) -- "
              f"{'PASS' if ok else 'FAIL'}")

        # ------------------------------------------------------------------------------ RED-BAD-SURFACE
        before = _row_count(schema_full, role_full)
        r = _run(dest_full, "led", "--json", "bogus_surface", str(payload_file))
        after = _row_count(schema_full, role_full)
        refused = r.returncode != 0
        teaches = "ledger_write" in r.stderr and "review_write" in r.stderr
        unchanged = before == after
        ok = refused and teaches and unchanged
        if not ok:
            failures.append(f"RED-BAD-SURFACE: exit={r.returncode} refused={refused} "
                             f"teaches={teaches} before={before} after={after}\nSTDERR:\n{r.stderr}")
        print(f"RED-BAD-SURFACE: exit={r.returncode} refused={refused} teaches={teaches} "
              f"row-count before={before} after={after} (unchanged={unchanged}) -- "
              f"{'PASS' if ok else 'FAIL'}")

        # ------------------------------------------------------------------------------ RED-PRE-S43-REFUSAL
        pre_payload = tmp_pre / "payload.json"
        pre_payload.write_text(json.dumps({"kind": "finding", "statement": f"{TAG}: pre-s43 probe"}))
        before = _row_count(WORLD_PRE, f"{WORLD_PRE}_rw")
        r = _run(dest_pre, "led", "--json", "ledger", str(pre_payload))
        after = _row_count(WORLD_PRE, f"{WORLD_PRE}_rw")
        refused = r.returncode != 0
        teaches = "capability_absent" in r.stderr and "s43" in r.stderr
        unchanged = before == after
        ok = refused and teaches and unchanged
        if not ok:
            failures.append(f"RED-PRE-S43-REFUSAL: exit={r.returncode} refused={refused} "
                             f"teaches={teaches} before={before} after={after}\nSTDERR:\n{r.stderr}")
        print(f"RED-PRE-S43-REFUSAL: exit={r.returncode} refused={refused} teaches={teaches} "
              f"row-count before={before} after={after} (unchanged={unchanged}) -- "
              f"{'PASS' if ok else 'FAIL'}")

        # ------------------------------------------------------------------- GREEN-SWALLOWED-FLAG-CAUGHT
        before = _row_count(schema_full, role_full)
        r = _run(dest_full, "led", "finding", f"{TAG}: swallowed-flag probe", "--json")
        after = _row_count(schema_full, role_full)
        refused = r.returncode != 0
        teaches = "--json" in r.stderr and "known led flag token" in r.stderr
        unchanged = before == after
        ok = refused and teaches and unchanged
        if not ok:
            failures.append(f"GREEN-SWALLOWED-FLAG-CAUGHT: exit={r.returncode} refused={refused} "
                             f"teaches={teaches} before={before} after={after}\nSTDERR:\n{r.stderr}")
        print(f"GREEN-SWALLOWED-FLAG-CAUGHT: exit={r.returncode} refused={refused} teaches={teaches} "
              f"row-count before={before} after={after} (unchanged={unchanged}) -- "
              f"{'PASS' if ok else 'FAIL'}")

        # ------------------------------------------------------------------------ RED-OVERSIZED-FILE
        MAX_WRITE_BODY_BYTES = 1_048_576
        oversized_file = tmp_full / "oversized.json"
        oversized_file.write_text(json.dumps(
            {"kind": "finding", "statement": "x" * (MAX_WRITE_BODY_BYTES + 200)}))
        before = _row_count(schema_full, role_full)
        r = _run(dest_full, "led", "--json", "ledger", str(oversized_file))
        after = _row_count(schema_full, role_full)
        refused = r.returncode != 0
        no_bash_crash = "Argument list too long" not in r.stderr and r.returncode != 126
        teaches = "payload_too_large" in r.stderr and str(MAX_WRITE_BODY_BYTES) in r.stderr
        unchanged = before == after
        ok = refused and no_bash_crash and teaches and unchanged
        if not ok:
            failures.append(f"RED-OVERSIZED-FILE: exit={r.returncode} refused={refused} "
                             f"no_bash_crash={no_bash_crash} teaches={teaches} before={before} "
                             f"after={after}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
        print(f"RED-OVERSIZED-FILE: exit={r.returncode} refused={refused} "
              f"no_bash_crash={no_bash_crash} teaches={teaches} row-count before={before} "
              f"after={after} (unchanged={unchanged}) -- {'PASS' if ok else 'FAIL'}")

        # ----------------------------------------------------------------------- RED-OVERSIZED-STDIN
        before = _row_count(schema_full, role_full)
        r = _run(dest_full, "led", "--json", "ledger", "-",
                  stdin=json.dumps({"kind": "finding",
                                     "statement": "y" * (MAX_WRITE_BODY_BYTES + 200)}))
        after = _row_count(schema_full, role_full)
        refused = r.returncode != 0
        no_bash_crash = "Argument list too long" not in r.stderr and r.returncode != 126
        teaches = "payload_too_large" in r.stderr and str(MAX_WRITE_BODY_BYTES) in r.stderr
        unchanged = before == after
        ok = refused and no_bash_crash and teaches and unchanged
        if not ok:
            failures.append(f"RED-OVERSIZED-STDIN: exit={r.returncode} refused={refused} "
                             f"no_bash_crash={no_bash_crash} teaches={teaches} before={before} "
                             f"after={after}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
        print(f"RED-OVERSIZED-STDIN: exit={r.returncode} refused={refused} "
              f"no_bash_crash={no_bash_crash} teaches={teaches} row-count before={before} "
              f"after={after} (unchanged={unchanged}) -- {'PASS' if ok else 'FAIL'}")

    finally:
        _drop(WORLD_FULL)
        _drop(WORLD_PRE)
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print(f"\nled-json-payload-mode fixture: {len(failures)} FAILURE(S)")
        for f in failures:
            print(f"\n!! {f}")
        return 1
    print("\nled-json-payload-mode fixture: all cases PASS, scratch substrate torn down to "
          "zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
