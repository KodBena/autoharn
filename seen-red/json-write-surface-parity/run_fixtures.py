#!/usr/bin/env python3
"""run_fixtures -- both-polarity live proof for ledger item `json-write-surface-parity`
(gates/fixture_census.py REGISTRY entry "json-write-surface-parity", design/
BRIEF-LED-ERGONOMICS-BUNDLE-2026-08-06.md item 4, ledger rows 1087/1102 family).

THE ITEM: `led --json` (the agent/programmatic-facing write mode, `seen-red/
led-json-payload-mode/run_fixtures.py`'s own item) reached `ledger`/`review`/`registration`/
`obligation` but NOT `obligation_revoke` or `missive_dispose`, though BOTH already exist as
live boundary write surfaces (`serving/boundary_service.py`'s own `WRITE_SURFACES`/
`WRITE_SURFACE_INT_FIELDS` dicts already carry them, exercised today by the PROSE verbs `led
obligate revoke`/`led missive dispose`, each already calling `bcc.write_and_report(cfg.base,
"obligation_revoke"/"missive_dispose", payload)`) -- the ONLY gap was `cmd_json`'s own
`_JSON_SURFACES` allowlist in bootstrap/templates/led.tmpl never naming them.

THE FIX: `_JSON_SURFACES` widened from 4 to 6 members. No new route, no kernel change, no second
validator (P2) -- `led --json <surface> <file|->` now hands the payload to the SAME
`bcc.write_and_report` call the prose verb already makes for that surface.

CASES (all live subprocess runs against one real scratch deployment):

  ADOPT                          -- bootstrap/new-project.sh --profile tracker.
  SEED                           -- two principals registered, one obligation written (assigner
                                     -> obliged-actor over a scope) for the obligation_revoke
                                     case.
  GREEN-OBLIGATION-REVOKE-JSON   -- `led --json obligation_revoke <file>` with a well-formed
                                     {"scope", "reason"} payload: exit 0, "row N written.", and
                                     `led show <N>` confirms kind=obligation_revoked,
                                     obligation_revoked_scope/obligation_revoke_reason match the
                                     payload byte-exact.
  GREEN-MISSIVE-DISPOSE-JSON-PARITY -- the SAME invalid receipt id, dispatched once through the
                                     PROSE verb (`led missive dispose <id> consumed`) and once
                                     through `--json missive_dispose`: both REFUSED, with the
                                     SAME kernel refusal text -- proving `--json` reaches the
                                     IDENTICAL route/surface the prose verb already exercises
                                     (full courier plumbing to mint a genuine undisposed missive
                                     is out of this fixture's own scope; the route-identity proof
                                     does not need a successful disposition to be conclusive).
  RED-BAD-SURFACE                -- `led --json bogus_surface <file>`: REFUSED, usage naming ALL
                                     SIX valid surfaces (proving the widened allowlist, not just
                                     the original four).
  RED-MALFORMED-JSON-NEW-SURFACE -- `led --json obligation_revoke <file>` with non-JSON content:
                                     REFUSED at the CLI, before any kernel call.
  RED-KERNEL-CATCHES-MISSING-REASON -- `led --json obligation_revoke <file>` with a payload
                                     carrying `scope` but NO `reason` key: `--json`'s own
                                     validation is well-formedness-only (P2 -- "must not grow a
                                     second validator that could disagree with the authority",
                                     this file's own module docstring) -- CLI-level pre-checks
                                     like the prose verb's mandatory-`--reason` refusal are
                                     DELIBERATELY not reproduced here; the KERNEL's own CHECK
                                     constraint (obligation_revoke_reason_kind_shape) is what
                                     actually refuses, witnessed on stderr.

Usage: python3 seen-red/json-write-surface-parity/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own environment
# before any subprocess is spawned -- inherited by the whole process tree this fixture starts.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

# Claude Code's own stamp_intercept.py PreToolUse hook rewrites the Bash-tool command that
# LAUNCHES this fixture to carry a PGOPTIONS export for the CALLING session's OWN wired
# deployment -- inherited by every subprocess here, which would otherwise stamp a scratch
# world's writes with the wrong secret. Stripped at module scope, before any subprocess spawns.
os.environ.pop("PGOPTIONS", None)

REPO = Path(__file__).resolve().parents[2]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
PGHOST, DB = fixture_pghost(), "toy"
WORLD = "jwspfixture"
TAG = f"seen-red-json-write-surface-parity-{int(time.time())}"


def _drop(name: str) -> None:
    subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-v", "ON_ERROR_STOP=0", "-q",
                     "-c", f"DROP SCHEMA IF EXISTS {name} CASCADE;",
                     "-c", f"DROP SCHEMA IF EXISTS {name}_kernel CASCADE;",
                     "-c", f"DROP ROLE IF EXISTS {name}_rw;",
                     "-c", f"DROP ROLE IF EXISTS {name}_owner;"],
                    capture_output=True, text=True)


def _run(dest: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(dest / "autoharn"), *args], capture_output=True, text=True,
                           cwd=str(dest))


def _kill_boundary(dest: Path) -> None:
    """See seen-red/led-read-projection-flags/run_fixtures.py's own docstring for the full
    rationale -- same helper, kept per-driver (a shared-file edit two other builders may also be
    touching this same session is a collision risk out of proportion to this small duplication)."""
    pidfile = dest / ".autoharn-service.pid"
    if not pidfile.exists():
        return
    try:
        pid = int(pidfile.read_text().strip())
    except (ValueError, OSError):
        return
    try:
        os.kill(pid, 15)
    except OSError:
        return
    for _ in range(20):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.25)
    try:
        os.kill(pid, 9)
    except OSError:
        pass


class _Abort(Exception):
    """Local control-flow only (never escapes `main`) -- see the sibling fixtures' identical
    class for the full rationale (avoids the bare-`SystemExit`-escapes-try/finally defect)."""


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    _drop(WORLD)
    try:
        # --------------------------------------------------------------------------------- ADOPT
        tmp = Path(tempfile.mkdtemp(prefix=f"{WORLD}-seenred-"))
        tmps.append(tmp)
        dest = tmp / WORLD
        r = subprocess.run(["bash", str(NEW_PROJECT), str(dest), "--profile", "tracker",
                             "--name", WORLD, "--db", DB, "--host", PGHOST],
                            capture_output=True, text=True)
        ok = r.returncode == 0 and (dest / "deployment.json").exists()
        if not ok:
            failures.append(f"ADOPT: exit={r.returncode}\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")
        print(f"ADOPT: new-project.sh --profile tracker exit={r.returncode} "
              f"deployment.json={(dest / 'deployment.json').exists()} -- {'PASS' if ok else 'FAIL'}")
        if not ok:
            raise _Abort

        # ---------------------------------------------------------------------------------- SEED
        assigner, obliged = f"{WORLD}-assigner", f"{WORLD}-obliged"
        r1 = _run(dest, "led", "register-principal", assigner, "human")
        r2 = _run(dest, "led", "register-principal", obliged, "human")
        scope = f"{TAG}-scope"
        r3 = _run(dest, "led", "obligate", scope, assigner, obliged)
        ok = all(rr.returncode == 0 for rr in (r1, r2, r3))
        if not ok:
            failures.append(f"SEED: {r1.stderr}\n{r2.stderr}\n{r3.stderr}")
        print(f"SEED: register x2 + obligate ok={ok} -- {'PASS' if ok else 'FAIL'}")
        if not ok:
            raise _Abort

        # ------------------------------------------------------------- GREEN-OBLIGATION-REVOKE-JSON
        payload_file = tmp / "obligation_revoke.json"
        reason = f"{TAG}: revoked via --json for this fixture's own parity proof"
        payload_file.write_text(json.dumps({"scope": scope, "reason": reason}))
        r = _run(dest, "led", "--json", "obligation_revoke", str(payload_file))
        accepted = r.returncode == 0 and "written." in r.stdout
        row_id = None
        if accepted:
            for tok in r.stdout.split():
                if tok.isdigit():
                    row_id = int(tok)
        stored_ok = False
        if row_id is not None:
            r_show = _run(dest, "led", "show", str(row_id))
            stored_ok = (f"kind" in r_show.stdout and "obligation_revoked" in r_show.stdout
                         and scope in r_show.stdout and reason in r_show.stdout)
        ok = accepted and row_id is not None and stored_ok
        if not ok:
            failures.append(f"GREEN-OBLIGATION-REVOKE-JSON: exit={r.returncode} "
                             f"accepted={accepted} row_id={row_id} stored_ok={stored_ok}\n"
                             f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
        print(f"GREEN-OBLIGATION-REVOKE-JSON: exit={r.returncode} accepted={accepted} "
              f"row_id={row_id} stored_ok={stored_ok} -- {'PASS' if ok else 'FAIL'}")

        # --------------------------------------------------------------- GREEN-MISSIVE-DISPOSE-JSON-PARITY
        bogus_receipt = 999999
        r_prose = _run(dest, "led", "missive", "dispose", str(bogus_receipt), "consumed")
        dispose_payload = tmp / "missive_dispose.json"
        dispose_payload.write_text(json.dumps({"receipt": bogus_receipt, "disposition": "consumed"}))
        r_json = _run(dest, "led", "--json", "missive_dispose", str(dispose_payload))
        both_refused = r_prose.returncode != 0 and r_json.returncode != 0
        # both reach the SAME kernel refusal -- compared on the REFUSED message line content
        # (the kernel's own text), not the surrounding CLI decoration (row ids/journal ids in
        # the "journaled as write_refused row N" preamble legitimately differ per invocation).
        prose_msg = r_prose.stderr.strip().splitlines()[-1] if r_prose.stderr.strip() else ""
        json_msg = r_json.stderr.strip().splitlines()[-1] if r_json.stderr.strip() else ""
        same_kernel_text = bool(prose_msg) and prose_msg == json_msg
        ok = both_refused and same_kernel_text
        if not ok:
            failures.append(f"GREEN-MISSIVE-DISPOSE-JSON-PARITY: prose_exit={r_prose.returncode} "
                             f"json_exit={r_json.returncode} prose_msg={prose_msg!r} "
                             f"json_msg={json_msg!r}\nPROSE STDERR:\n{r_prose.stderr}\n"
                             f"JSON STDERR:\n{r_json.stderr}")
        print(f"GREEN-MISSIVE-DISPOSE-JSON-PARITY: both_refused={both_refused} "
              f"same_kernel_text={same_kernel_text} -- {'PASS' if ok else 'FAIL'}")

        # --------------------------------------------------------------------------- RED-BAD-SURFACE
        r = _run(dest, "led", "--json", "bogus_surface", str(payload_file))
        refused = r.returncode == 4
        names_all_six = all(s in r.stderr for s in
                             ("ledger", "review", "registration", "obligation",
                              "obligation_revoke", "missive_dispose"))
        ok = refused and names_all_six
        if not ok:
            failures.append(f"RED-BAD-SURFACE: exit={r.returncode} refused={refused} "
                             f"names_all_six={names_all_six}\nSTDERR:\n{r.stderr}")
        print(f"RED-BAD-SURFACE: exit={r.returncode} refused={refused} "
              f"names_all_six={names_all_six} -- {'PASS' if ok else 'FAIL'}")

        # ------------------------------------------------------------- RED-MALFORMED-JSON-NEW-SURFACE
        malformed_file = tmp / "malformed.json"
        malformed_file.write_text("this is not json")
        r = _run(dest, "led", "--json", "obligation_revoke", str(malformed_file))
        refused = r.returncode == 4
        teaches = "not valid JSON" in r.stderr
        ok = refused and teaches
        if not ok:
            failures.append(f"RED-MALFORMED-JSON-NEW-SURFACE: exit={r.returncode} "
                             f"refused={refused} teaches={teaches}\nSTDERR:\n{r.stderr}")
        print(f"RED-MALFORMED-JSON-NEW-SURFACE: exit={r.returncode} refused={refused} "
              f"teaches={teaches} -- {'PASS' if ok else 'FAIL'}")

        # ---------------------------------------------------------- RED-KERNEL-CATCHES-MISSING-REASON
        no_reason_file = tmp / "no_reason.json"
        no_reason_file.write_text(json.dumps({"scope": f"{TAG}-scope-2"}))
        r = _run(dest, "led", "--json", "obligation_revoke", str(no_reason_file))
        refused = r.returncode != 0
        kernel_level = "REFUSED by the kernel write boundary" in r.stderr
        no_cli_precheck_text = "MANDATORY" not in r.stderr
        ok = refused and kernel_level and no_cli_precheck_text
        if not ok:
            failures.append(f"RED-KERNEL-CATCHES-MISSING-REASON: exit={r.returncode} "
                             f"refused={refused} kernel_level={kernel_level} "
                             f"no_cli_precheck_text={no_cli_precheck_text}\nSTDERR:\n{r.stderr}")
        print(f"RED-KERNEL-CATCHES-MISSING-REASON: exit={r.returncode} refused={refused} "
              f"kernel_level={kernel_level} no_cli_precheck_text={no_cli_precheck_text} -- "
              f"{'PASS' if ok else 'FAIL'}")

    except _Abort:
        pass
    finally:
        if "dest" in locals():
            _kill_boundary(dest)
        _drop(WORLD)
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print(f"\njson-write-surface-parity fixture: {len(failures)} FAILURE(S)")
        for f in failures:
            print(f"\n!! {f}")
        return 1
    print("\njson-write-surface-parity fixture: all cases PASS, scratch substrate torn down to "
          "zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
