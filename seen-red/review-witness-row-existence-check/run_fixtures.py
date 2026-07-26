#!/usr/bin/env python3
"""run_fixtures -- both-polarity live proof for ledger item `review-witness-row-existence-check`
(ledger row 1600's CLI-side sibling; the kernel-side existence refusal itself is
kernel/lineage/s48-review-witness-existence.sql, design/FABLE-KERNEL-INTAKE-PAIR-SPEC.md Delta 1,
already built and wired into every `--new-world` birth chain, with its OWN witnessed fixture
family, seen-red/s48-review-witness-existence/run_fixtures.py -- that family proves the KERNEL
trigger; THIS family proves the served CLI (bootstrap/templates/led.tmpl) itself, end to end
through `./led work close`/`./led work resolve-violation`, one hop earlier).

THE INCIDENT (witnessed 2026-07-18): `led work close` accepted `--review-witness row:1594` when
no row 1594 existed -- the orchestrator guessed its own not-yet-assigned row id, a witness
citation naming a nonexistent row (a claim with a dangling evidence pointer, in the one place
evidence pointers are load-bearing). s48's own kernel trigger now refuses this at INSERT time,
but there was no CLI-SIDE pre-flight of any kind: an operator or agent misusing --review-witness
found out only after a full round trip to the boundary, with the kernel's own (correct, but
generic) SQLSTATE-wrapped message, not a friendly CLI-side teach.

THE FIX (this session): `bootstrap/templates/led.tmpl`'s new `_review_witness_violation(cfg,
review_ref)` helper, wired into both `cmd_work_close` and `cmd_work_resolve_violation` (the two
verbs whose `--review-witness` flag can carry a `row:<id>` token, s29's own kind-shape CHECK).
TWO checks, for each `row:<id>` token found (the SAME `row:(\\d+)` pattern s48's own trigger
matches, deliberately -- a citation this CLI check accepts is one s48 would also accept, and
vice versa):
  (1) EXISTENCE -- read via `GET /rows/{id}` (the RAW ledger table, matching s48's own
      EXISTENCE-not-IN-FORCE denomination).
  (2) SANITY -- a NEW, CLI-side-only heuristic layer s48 itself deliberately does NOT provide
      (s48's own header: "this delta narrows WHICH OF THOSE ROWS are admitted, it does not widen
      which kinds may carry the column" -- i.e. it never asks whether the cited row IS a
      review): the cited row's own `kind` must be `'review'` -- this flag's own contract (this
      file's usage text) is "a review already exists; cite it", so citing an unrelated row's id
      (a typo'd decision/finding/etc.) reads as satisfying that contract without actually doing
      so.
A `review_ref` with no `row:<id>` token (prose, `commit:<sha>`, `artifact:<hash>`) is untouched
by this check -- exactly s48's own disclosed scope boundary (WK1-c's sibling): commit/artifact
witnesses have their own existence checks elsewhere (this file's own `--review-bookkeeping`
git-cat-file check; kernel/lineage/s52-artifact-witness-check.sql), and free prose citing a
review context by name is a disclosed, non-goal form neither s48 nor this CLI check claims to
verify.

CASES (all live subprocess runs of the real `./led` against a real scratch deployment, ADOPT via
`bootstrap/new-project.sh --new-world`, full birth chain through s57 -- the served `led` is
s43-ONLY, no direct-INSERT fallback survives the CLI rewrite, exactly the same reason every
sibling fixture in this class already migrated off track-work.sh):

  ADOPT                          -- bootstrap/new-project.sh --new-world stands up the scratch
                                     deployment.
  CLI-EXISTENCE-REFUSE           -- `led work close <slug> shipped --witness ... --review-witness
                                     row:<nonexistent>`: REFUSED, no row written, teach-text
                                     names the missing id and cites s48/row 1600.
  CLI-SANITY-WRONG-KIND-REFUSE   -- `--review-witness row:<id>` citing an EXISTING row whose kind
                                     is NOT 'review' (a `work_opened` row, here): REFUSED, no row
                                     written, teach-text names the actual kind.
  CLI-GREEN-VALID-REVIEW         -- `--review-witness row:<id>` citing a real, existing `review`
                                     row (written by a distinct registered principal, so the
                                     kernel's own segregation-of-duties refusal does not
                                     interfere): ACCEPTED, row written.
  CLI-GREEN-FREE-PROSE-UNTOUCHED -- `--review-witness "self:free prose, no row: token"`: ACCEPTED
                                     untouched -- the scope boundary (s48's own WK1-c sibling):
                                     prose citation is never dereferenced by this check either.
  RESOLVE-VIOLATION-EXISTENCE-REFUSE -- the SAME existence check, exercised through `led work
                                     resolve-violation`'s own `--review-witness` (a genuine
                                     depends_on_unknown_slug violation constructed live, then
                                     answered with a nonexistent row:<id> citation): REFUSED, no
                                     row written.
  RESOLVE-VIOLATION-GREEN-VALID  -- the same violation answered with the real review row's id:
                                     ACCEPTED, row written.

Usage: python3 seen-red/review-witness-row-existence-check/run_fixtures.py
Exit 0 if every case matches expected (guard-holds) behavior; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"

sys.path.insert(0, str(REPO / "seen-red"))  # for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own
# environment before any subprocess is spawned -- inherited by the whole process tree
# this fixture starts, so every repo-root verb invocation anywhere downstream carries it.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

# REUSE (ADR-0012 P1): serve_existing_world from seen-red/boundary-service/run_fixtures.py -- the
# ONE shared home every migrated fixture in this class already imports.
_BS_SPEC = importlib.util.spec_from_file_location(
    "boundary_service_fixtures", REPO / "seen-red" / "boundary-service" / "run_fixtures.py")
assert _BS_SPEC is not None and _BS_SPEC.loader is not None
bs_fixtures = importlib.util.module_from_spec(_BS_SPEC)
sys.modules["boundary_service_fixtures"] = bs_fixtures
_BS_SPEC.loader.exec_module(bs_fixtures)

PGHOST, PGDB = fixture_pghost(), "toy"
SCRATCH_NAME = "rwrecfixture"
SCHEMA, KERN, ROLE = SCRATCH_NAME, f"{SCRATCH_NAME}_kernel", f"{SCRATCH_NAME}_rw"
TAG = f"seen-red-review-witness-row-existence-check-{int(time.time())}"

FAILURES: list[str] = []


def _check(label: str, cond: bool) -> None:
    print(f"  [{'ok' if cond else 'FAIL'}] {label}")
    if not cond:
        FAILURES.append(label)


def _psql(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["psql", "-h", PGHOST, "-d", PGDB, *args],
                           capture_output=True, text=True)


def _drop_scratch() -> None:
    _psql("-v", "ON_ERROR_STOP=0", "-q",
          "-c", f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE;",
          "-c", f"DROP SCHEMA IF EXISTS {KERN} CASCADE;",
          "-c", f"DROP ROLE IF EXISTS {ROLE};")


def _run_led(dest: Path, *args: str, env: dict | None = None) -> tuple[int, str, str]:
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    cp = subprocess.run([str(dest / "led"), *args], cwd=str(dest), capture_output=True, text=True,
                        env=full_env)
    return cp.returncode, cp.stdout, cp.stderr


def _current_max_id(dest: Path) -> int:
    rc, out, _ = _run_led(dest, "--recent", "1")
    if rc != 0 or not out.strip():
        return -1
    m = re.match(r"^\[(\d+)\]", out.strip().splitlines()[0])
    if not m:
        raise RuntimeError(f"could not parse a row id from `led --recent 1` output: {out!r}")
    return int(m.group(1))


def _last_written_id(rc: int, out: str) -> str | None:
    toks = out.split()
    return toks[-2] if rc == 0 and len(toks) >= 2 and toks[-2].isdigit() else None


DEST: Path


def cli_existence_refuse() -> None:
    print("# CLI-EXISTENCE-REFUSE -- --review-witness citing a NONEXISTENT row:<id> "
          "(the exact 2026-07-18 incident shape) MUST REFUSE, before any write is attempted.")
    # open + claim the slug FIRST -- cmd_work_close's own pre-existing claim-before-close gate
    # (`_slug_claimant`) refuses an unclaimed slug for an UNRELATED reason before the
    # review-witness check is even reached; skipping this setup would make this case pass for
    # the wrong reason (caught while banking this fixture's own red-first capture).
    rc0, out0, err0 = _run_led(DEST, "work", "open", "cli-existence-slug", f"{TAG}: existence-refuse target")
    assert rc0 == 0, f"could not open cli-existence-slug: {out0!r} {err0!r}"
    rc0b, out0b, err0b = _run_led(DEST, "work", "claim", "cli-existence-slug")
    assert rc0b == 0, f"could not claim cli-existence-slug: {out0b!r} {err0b!r}"
    before = _current_max_id(DEST)
    rc, out, err = _run_led(DEST, "work", "close", "cli-existence-slug", "shipped",
                             "--witness", "note:test", "--review-witness", "row:999999")
    after = _current_max_id(DEST)
    _check("REFUSED (nonzero exit)", rc != 0)
    _check("no row written at all (max id unchanged -- refused CLI-side, before the kernel is "
           "ever reached, unlike a kernel-level refusal which still journals a write_refused "
           "row and DOES advance the max id)", after == before)
    _check("teach-text cites the missing id", "row 999999" in err or "999999" in err)
    _check("teach-text cites s48/row 1600", "s48" in err or "1600" in err)


def cli_sanity_wrong_kind_refuse() -> None:
    print("# CLI-SANITY-WRONG-KIND-REFUSE -- --review-witness citing an EXISTING row that is NOT "
          "a 'review' row (a work_opened row, here) MUST REFUSE -- the sanity leg s48 itself "
          "does not provide.")
    rc0, out0, _ = _run_led(DEST, "work", "open", "sanity-target", f"{TAG}: sanity target")
    target_id = _last_written_id(rc0, out0)
    assert target_id is not None, f"could not seed a work_opened row: {out0!r}"
    # open + claim the slug being CLOSED (distinct from sanity-target, the row cited) -- same
    # claim-before-close reasoning as cli_existence_refuse above.
    rc0b, out0b, err0b = _run_led(DEST, "work", "open", "cli-sanity-slug", f"{TAG}: sanity-refuse target")
    assert rc0b == 0, f"could not open cli-sanity-slug: {out0b!r} {err0b!r}"
    rc0c, out0c, err0c = _run_led(DEST, "work", "claim", "cli-sanity-slug")
    assert rc0c == 0, f"could not claim cli-sanity-slug: {out0c!r} {err0c!r}"
    before = _current_max_id(DEST)
    rc, out, err = _run_led(DEST, "work", "close", "cli-sanity-slug", "shipped",
                             "--witness", "note:test", "--review-witness", f"row:{target_id}")
    after = _current_max_id(DEST)
    _check("REFUSED (nonzero exit)", rc != 0)
    _check("no row written at all (max id unchanged)", after == before)
    _check("teach-text names the actual (wrong) kind", "work_opened" in err)


def cli_green_valid_review() -> None:
    print("# CLI-GREEN-VALID-REVIEW -- --review-witness citing a REAL, EXISTING 'review' row "
          "MUST ACCEPT.")
    rc0, out0, _ = _run_led(DEST, "work", "open", "green-target", f"{TAG}: green target")
    target_id = _last_written_id(rc0, out0)
    assert target_id is not None, f"could not seed a work_opened row: {out0!r}"
    # A distinct, registered principal reviews it (segregation-of-duties: the default connection
    # principal cannot countersign its own row).
    rc1, out1, err1 = _run_led(DEST, "register-principal", "rwrec-reviewer", "model",
                                "--purpose", "review-witness-row-existence-check fixture")
    assert rc1 == 0, f"could not register reviewer principal: {out1!r} {err1!r}"
    rc2, out2, err2 = _run_led(
        DEST, "review", target_id, "attest", "self-review",
        f"{TAG}: distinct-principal review of green-target", env={"LED_ACTOR": "rwrec-reviewer"})
    review_id = _last_written_id(rc2, out2)
    assert rc2 == 0 and review_id is not None, f"could not write review row: {out2!r} {err2!r}"
    rc3, out3, _ = _run_led(DEST, "work", "claim", "green-target")
    assert rc3 == 0, f"could not claim green-target: {out3!r}"
    before = _current_max_id(DEST)
    rc, out, err = _run_led(DEST, "work", "close", "green-target", "shipped",
                             "--witness", "note:test", "--review-witness", f"row:{review_id}")
    after = _current_max_id(DEST)
    _check("ACCEPTED (exit 0)", rc == 0)
    _check("a row WAS written (max id advanced)", after == before + 1)


def cli_green_free_prose_untouched() -> None:
    print("# CLI-GREEN-FREE-PROSE-UNTOUCHED -- --review-witness with NO row:<id> token (free "
          "prose) MUST ACCEPT, untouched -- the scope boundary (s48's own WK1-c sibling).")
    rc0, out0, _ = _run_led(DEST, "work", "open", "prose-target", f"{TAG}: prose target")
    target_id = _last_written_id(rc0, out0)
    assert target_id is not None, f"could not seed a work_opened row: {out0!r}"
    rc1, out1, _ = _run_led(DEST, "work", "claim", "prose-target")
    assert rc1 == 0, f"could not claim prose-target: {out1!r}"
    before = _current_max_id(DEST)
    rc, out, err = _run_led(DEST, "work", "close", "prose-target", "shipped",
                             "--witness", "note:test",
                             "--review-witness", "self:free prose, no row token at all")
    after = _current_max_id(DEST)
    _check("ACCEPTED (exit 0)", rc == 0)
    _check("a row WAS written (max id advanced)", after == before + 1)


def resolve_violation_existence_refuse() -> str:
    print("# RESOLVE-VIOLATION-EXISTENCE-REFUSE -- the SAME existence check via `led work "
          "resolve-violation`'s own --review-witness (a genuine depends_on_unknown_slug "
          "violation, answered with a nonexistent row:<id>) MUST REFUSE.")
    rc0, out0, err0 = _run_led(DEST, "work", "open", "rv-slug", f"{TAG}: resolve-violation target")
    assert rc0 == 0, f"could not open rv-slug: {out0!r} {err0!r}"
    # `led work resolve-violation <violating-act-id> ...`'s first positional is the VIOLATING
    # ACT's own ledger row id (the work_depends_on edge's own id, matching work_item_violations'
    # `target_id` column) -- NOT the work item's slug (a distinct earlier mis-write in this same
    # fixture-authoring pass, caught before banking: passing the slug there derives ZERO classes,
    # since work_item_violations is keyed by the violating act's id, not by slug).
    rc1, out1, err1 = _run_led(DEST, "work", "depends", "rv-slug", "nonexistent-antecedent-xyz")
    depends_edge_id = _last_written_id(rc1, out1)
    assert rc1 == 0 and depends_edge_id is not None, f"could not record depends edge: {out1!r} {err1!r}"
    rc_v, out_v, _ = _run_led(DEST, "work", "violations")
    assert "depends_on_unknown_slug" in out_v, f"violation did not surface: {out_v!r}"
    before = _current_max_id(DEST)
    rc, out, err = _run_led(DEST, "work", "resolve-violation", depends_edge_id, "retired",
                             f"{TAG}: answering the depends_on_unknown_slug violation",
                             "--review-witness", "row:999998")
    after = _current_max_id(DEST)
    _check("REFUSED (nonzero exit)", rc != 0)
    _check("no row written (max id unchanged)", after == before)
    _check("teach-text cites the missing id", "999998" in err)
    return depends_edge_id


def resolve_violation_green_valid(depends_edge_id: str) -> None:
    print("# RESOLVE-VIOLATION-GREEN-VALID -- the same violation, answered with a REAL existing "
          "review row's id, MUST ACCEPT.")
    rc0, out0, _ = _run_led(DEST, "work", "open", "green-target-2", f"{TAG}: rv green target")
    target_id = _last_written_id(rc0, out0)
    assert target_id is not None, f"could not seed a work_opened row: {out0!r}"
    rc1, out1, err1 = _run_led(
        DEST, "review", target_id, "attest", "self-review",
        f"{TAG}: distinct-principal review of rv green target",
        env={"LED_ACTOR": "rwrec-reviewer"})
    review_id = _last_written_id(rc1, out1)
    assert rc1 == 0 and review_id is not None, f"could not write review row: {out1!r} {err1!r}"
    before = _current_max_id(DEST)
    rc, out, err = _run_led(DEST, "work", "resolve-violation", depends_edge_id, "retired",
                             f"{TAG}: answering rv-slug's violation with a real review",
                             "--review-witness", f"row:{review_id}")
    after = _current_max_id(DEST)
    _check("ACCEPTED (exit 0)", rc == 0)
    _check("a row WAS written (max id advanced)", after == before + 1)
    if rc != 0:
        print(f"  (unexpected refusal stderr: {err})")


def main() -> int:
    global DEST
    _drop_scratch()
    tmpdir = Path(tempfile.mkdtemp(prefix="review-witness-row-existence-check-fixture-"))
    DEST = tmpdir / "project"

    r = subprocess.run([str(NEW_PROJECT), str(DEST), "--new-world", SCRATCH_NAME,
                        "--db", PGDB, "--host", PGHOST], capture_output=True, text=True, cwd=str(REPO))
    ok = r.returncode == 0 and (DEST / "deployment.json").exists()
    print(f"ADOPT: new-project.sh --new-world exit={r.returncode} deployment.json="
          f"{(DEST / 'deployment.json').exists()} -- {'PASS' if ok else 'FAIL'}")
    if not ok:
        print(f"\nADOPT FAILED, aborting -- scratch left standing:\n  tempdir: {tmpdir}\n"
              f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
        return 1

    proc: subprocess.Popen | None = None
    crashed_with: BaseException | None = None
    try:
        proc = bs_fixtures.serve_existing_world(DEST / "deployment.json", tmpdir)
        cli_existence_refuse()
        cli_sanity_wrong_kind_refuse()
        cli_green_valid_review()
        cli_green_free_prose_untouched()
        _depends_edge_id = resolve_violation_existence_refuse()
        resolve_violation_green_valid(_depends_edge_id)
    except BaseException as exc:  # noqa: BLE001 -- last-resort net, see this fixture class's
        # siblings (artifact-claim-dereference-guard, led-help-token-closure) for the same
        # reasoning: an uncaught exception here must not leak the boundary_service subprocess or
        # the scratch schema/kern/role.
        crashed_with = exc
        FAILURES.append(f"UNCAUGHT EXCEPTION mid-fixture: {exc!r}")
        print(f"\n!! UNCAUGHT EXCEPTION mid-fixture -- {exc!r} -- reaping server and dropping "
              f"scratch before re-raising")
    finally:
        if proc is not None:
            bs_fixtures.stop_server(proc)

    if crashed_with is not None:
        _drop_scratch()
        shutil.rmtree(tmpdir, ignore_errors=True)
        print("review-witness-row-existence-check fixture: crashed -- server reaped, scratch "
              "dropped")
        raise crashed_with

    if FAILURES:
        print(f"\nSPECIMEN RED -- {len(FAILURES)} check(s) failed: {FAILURES}\nscratch left "
              f"standing as evidence:\n  tempdir: {tmpdir}\n  schema: {SCHEMA}/{KERN}/role "
              f"{ROLE} (db {PGDB}@{PGHOST})")
        return 1

    _drop_scratch()
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\n# review-witness-row-existence-check: all cases PASS -- the CLI-side "
          f"existence+sanity pre-flight over --review-witness holds in both `led work close` "
          f"and `led work resolve-violation`, s48's own kernel-side existence refusal untouched "
          f"as the load-bearing invariant beneath it. Scratch torn down to zero residue. "
          f"Tag: {TAG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
