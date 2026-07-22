#!/usr/bin/env python3
"""run_fixtures.py — both-polarity proof for hooks/stop_clean_exit.py (the clean-exit Stop-hook
gate, BACKLOG "Run-5 forensics" family, 2026-07-10 -- CLAUDE.md point 5, "done means clean",
mechanized as a hook instead of left as advice).

QUEUE SEMANTICS EXTENSION (2026-07-15, design/FABLE-STOP-GATE-QUEUE-SEMANTICS-SPEC.md, ratified by
the maintainer 2026-07-15): the work-item leg's predicate narrowed from "any state='open' item is
debt" to "an item THIS session still holds a claim on, undischarged and unbequeathed, is debt" --
unclaimed open items (the PLANNED queue every deployment preamble's point 1 pre-ledgers) never
block; a `stopping:`-disposition row naming a claimed slug in its `remains:` clause bequeaths it.
Every DEBT-bearing case below (c/d/g/h/i/j) therefore now uses a work item CLAIMED BY THE STOPPING
SESSION (a REAL stamped `work_claimed` row, `stamp_session` = the session the hook input itself
carries -- the only thing that proves a claim is "this session's") as its debt substrate, in place
of the pre-this-pass unclaimed items those same cases used to lean on; four NEW cases (k/l/m/n)
both-polarity-prove the narrowing itself (spec §4's acceptance list).

Unlike seen-red/change-gate-subject-root/run_fixtures.py (whose five cases are each fully
independent -- any order, any subset), most of this gate's named cases are a single STATEFUL
sequence against one throwaway probe world (the circuit breaker's whole point is state across
repeated Stop events), so this driver runs them in a fixed, documented order rather than iterating
case directories generically. Each case still keeps its inputs/expectations in its own directory
(stdin.json / env.json / expected_exit.txt / expect.txt), the same per-case-dir convention every
seen-red/ gate uses -- only the EXECUTION ORDER is bespoke here, not the case shape.

Sequence (real infra, no mocks -- a throwaway probe world at /home/bork/w/vdc/1/.stopprobe, toy
db, torn down before AND after):
  1. a-unwired            -- no DB touched at all; proves zero interference for an un-opted-in
                             session (no env var, no deployment.json at cwd).
  2. [setup] bootstrap/new-project.sh --new-world stopprobe --db toy --host 192.168.122.1
             --name stopprobe  -> a fresh, CLEAN world (s22 applied automatically, per
             new-project.sh's own --new-world lineage chain).
  2.5 [seed] a REAL stamped `decision` row ("stopping: fixture baseline ...") for the shared
             `seenred` session every OTHER case's stdin.json carries -- pre-seeded so the
             STOP-DISPOSITION WARNING (an orthogonal, non-blocking check) never fires as a
             side-effect of these debt-focused cases. Stamped via a real HMAC computed the same
             way hooks/stamp_intercept.py computes it (session|agent|ts over the world's own
             provisioned secret) -- not a raw unstamped INSERT -- because both this check AND the
             new queue-semantics narrowing key on `stamp_session`, the interception-injected
             column, never a writer-supplied one.
  3. b-clean-world        -- the freshly-scaffolded world has nothing open at all, AND (since step
                             2.5) a stamped stop-disposition row for THIS session. Expect allow,
                             silently -- unchanged from before this pass.
  4. [debt] ./led work open probe-item-1 "..." + a REAL stamped `led work claim probe-item-1` for
             the `seenred` session -- a work item this session itself holds, still open: exactly
             run-5's original defect, and exactly the ONLY shape the new predicate still refuses.
  5. c-dirty-world        -- call #1 against that debt: expect BLOCK (exit 2), the debt named as
             "claimed by THIS session", both discharge paths taught (close it, or bequeath it via
             a stopping-disposition row), and the pre-this-pass false "cannot end" phrasing GONE.
  6. [unasserted] a second identical call, run inline (not its own case directory) purely to
             advance the circuit-breaker's internal counter from 1 to 2 -- still a real
             assertion (checked inline below), just not one of the named fixture cases.
  7. d-circuit-breaker-third-repeat -- call #3 against the SAME unchanged debt: the breaker
             fires -- expect ALLOW (exit 0) with the loud warning banner, not a block.
  8. [cleanup] ./led work close probe-item-1 dropped; verify one more call returns a silent
             allow AND the state file is gone (progress resets the breaker / clean clears it) --
             a bonus sanity check, reported but not one of the named cases.
  9. e-stop-disposition-warn -- STOP-DISPOSITION WARNING, both-polarity case 1 (Part 1): a
             DIFFERENT session, never stamped with a 'stopping:' row -- an otherwise-clean world
             (no debt at all) still gets a loud, non-blocking warning (exit 0) teaching
             `./led decision "stopping: ..."`. Proves the check fires on its own, independent of
             the debt-collection machinery above.
  10. [seed] a REAL stamped 'stopping:' row for a THIRD, distinct session.
  11. f-stop-disposition-silent -- both-polarity case 2: the identical shape as case 9, but THIS
             session now carries a stamped disposition row -- SILENT (no warning), proving the
             check is keyed on presence/absence, not a blanket always-warn.
  12. k-unclaimed-open-only -- QUEUE SEMANTICS acceptance #1 (spec §4 bullet 1): `./led work open
             probe-item-2` left deliberately UNCLAIMED -- expect ALLOW (exit 0), an informational
             "N open unclaimed item(s) remain -- the successor's queue" line naming probe-item-2,
             no block, no breaker banner. [cleanup] claim + close probe-item-2 afterward.
  13. l-bequeathed-allow -- QUEUE SEMANTICS acceptance #3 (spec §4 bullet 3, first half):
             `probe-item-3` claimed by `seenred` (stamped), then a stamped 'stopping: ...;
             remains: probe-item-3' row for the SAME session -- expect ALLOW (exit 0), the item
             listed on the allow path as bequeathed, no block. [cleanup] close probe-item-3.
  14. m-bequest-wrong-session-still-blocks -- QUEUE SEMANTICS acceptance #3 (second half, "bequest
             cannot be borrowed"): `probe-item-4` claimed by `seenred` (stamped), then a stamped
             'stopping: ...; remains: probe-item-4' row for a DIFFERENT session
             (`otherbequest-session`) -- expect BLOCK (exit 2): a disposition not stamped to the
             stopping session does not discharge its claim. [cleanup] close probe-item-4; verify a
             silent allow + cleared state file (bonus sanity check).
  15-19. BREAKER TRANSITION sequence (`stop-breaker-progress-reset-defect` /
             `stop-breaker-state-type-guard`, ENT TESTBED FINDING 5), now on SESSION-CLAIMED debt
             (the queue-semantics narrowing means unclaimed items can no longer stand in for
             breaker debt): claim `probe-item-5`/`probe-item-6` (stamped `seenred`);
             g-subset-progress-block-1 blocks at count 1; close probe-item-5 (progress, a strict
             subset of the debt survives); h-subset-progress-block-2 blocks at count 2 -- the
             fix's whole point: the breaker did NOT reset to 1 just because the debt set shrank.
             Then claim probe-item-7 (stamped `seenred`) alongside the still-open probe-item-6 (a
             genuinely NEW entry, not a subset); i-added-entry-resets-block blocks at count 1 --
             proves the fix narrows the reset condition rather than removing it.
  20. [corrupt] hand-write a wrong-typed state file (entries=null, count="two") -- the exact
             on-disk corruption/hand-edit shape `stop-breaker-state-type-guard` defends against.
  21. j-corrupted-state-degrades-safely -- call against the unchanged {probe-item-6, probe-item-7}
             debt with the corrupted state file in place: MUST still block cleanly (exit 2, no
             traceback), proving the guarded accessors degrade the corruption to "treat as a
             fresh signature" instead of raising an uncaught TypeError out of `_breaker_transition`.
  21.5 [unasserted, inline] a SECOND, more severe corruption shape (top-level-non-dict state file)
             degrades safely too -- same as before this pass.
  22. [cleanup] close probe-item-6/probe-item-7; verify a final clean allow and a cleared state
             file -- a bonus sanity check, same shape as step 8.
  23. n-experience-replay -- QUEUE SEMANTICS acceptance #5 (spec §4 last bullet, "the experience-
             world scenario replayed end-to-end fires NO breaker"): probe-item-8/probe-item-9
             opened UNCLAIMED (the planned queue), probe-item-10 claimed by `seenred` (stamped)
             and bequeathed via a stamped 'stopping: ...; remains: probe-item-10' row -- the exact
             mixed shape (queue + a claimed-and-handed-off parent) that tripped the OLD predicate
             into blocked/blocked/fail-open in the experience world. Expect ALLOW (exit 0), the
             unclaimed queue count AND the bequeathed line both present, and -- the whole point --
             NO "CIRCUIT BREAKER" banner anywhere in the output: this shape never blocks even
             once under the new predicate. [cleanup] close probe-item-8/9/10.
  24. [teardown] drop the probe schemas/role/directory.

Usage: python3 seen-red/stop-clean-exit/run_fixtures.py
Exit 0 if every case matches (including the unasserted/bonus inline checks); 1 otherwise.
Lazy imports banned.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402 (filing/pghost_resolve.py via seen-red/_fixture_env.py -- never a literal host default)


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
HOOK = REPO / "hooks" / "stop_clean_exit.py"
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"

PROBE_DIR = Path("/home/bork/w/vdc/1/.stopprobe")
PGHOST, PGDB = fixture_pghost(), "toy"
SCHEMA, KERN, ROLE = "stopprobe", "stopprobe_kernel", "stopprobe_rw"
SEENRED_SESSION = "seenred"           # the session id every ORIGINAL case's stdin.json carries
E_SESSION = "stopdisp-warn-session"   # case 9: deliberately never stamped
F_SESSION = "stopdisp-silent-session" # case 11: stamped in step 10, right before the case runs
OTHER_SESSION = "otherbequest-session"  # case m: a bequest stamped to a DIFFERENT session


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def _stamped_env(session: str, agent: str = "main") -> dict[str, str]:
    """A real interception stamp for ONE psql call, computed the same way
    hooks/stamp_intercept.py computes it (HMAC-SHA256 over `session|agent|ts`, keyed on the
    world's own provisioned apparatus secret) -- carried via PGOPTIONS exactly like the hook's
    own `export PGOPTIONS=...` rewrite, so `led`'s own psql call inherits it and the kernel's
    set_stamp trigger lands `stamp_session=<session>` on the row it produces. Computed directly
    here (stdlib hmac, the secret `--new-world` already provisioned at
    PROBE_DIR/.claude/secrets/stamp_secret.hex) rather than shelling out to the hook itself --
    this fixture needs exactly one stamped row per call, not the hook's full matcherless-rewrite
    machinery."""
    secret = bytes.fromhex(
        (PROBE_DIR / ".claude" / "secrets" / "stamp_secret.hex").read_text(encoding="utf-8").strip())
    ts = int(time.time())
    mac = hmac.new(secret, f"{session}|{agent}|{ts}".encode(), hashlib.sha256).hexdigest()
    pgopts = (f"-c app.vendor_session={session} -c app.vendor_agent={agent} "
              f"-c app.vendor_ts={ts} -c app.vendor_hmac={mac}")
    env = dict(os.environ)
    env["PGOPTIONS"] = pgopts
    return env


def led_stamped(session: str, *args: str) -> subprocess.CompletedProcess[str]:
    """Like `led()` below, but the psql call it shells out to carries a REAL interception stamp
    for `session` (see `_stamped_env`) -- the only way to land a `stamp_session`-bearing row
    outside a live Claude Code session, which is exactly what the queue-semantics narrowing AND
    the stop-disposition check both key on (claim ownership and disposition stamping alike)."""
    return sh([str(PROBE_DIR / "led"), *args], cwd=str(PROBE_DIR), env=_stamped_env(session))


def teardown_probe() -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE; DROP SCHEMA IF EXISTS {KERN} CASCADE; "  # declared-drop: stopprobe (declared scratch/test reset)
        f"DROP OWNED BY {ROLE};"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {ROLE};"])
    shutil.rmtree(PROBE_DIR, ignore_errors=True)


def setup_probe() -> bool:
    r = sh([str(NEW_PROJECT), str(PROBE_DIR), "--new-world", SCHEMA,
            "--db", PGDB, "--host", PGHOST, "--name", SCHEMA])
    if r.returncode != 0:
        print("setup_probe FAILED:")
        print(r.stdout[-2000:])
        print(r.stderr[-2000:])
        return False
    return True


def led(*args: str, actor: str | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    if actor:
        env["LED_ACTOR"] = actor
    return sh([str(PROBE_DIR / "led"), *args], cwd=str(PROBE_DIR), env=env)


def build_env(case: Path) -> dict[str, str]:
    env = dict(os.environ)
    spec_path = case / "env.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8")) if spec_path.exists() else {}
    for var in spec.get("unset", []):
        env.pop(var, None)
    for var, val in spec.get("set", {}).items():
        env[var] = val
    return env


def run_hook(case: Path) -> subprocess.CompletedProcess[str]:
    stdin_text = (case / "stdin.json").read_text(encoding="utf-8")
    return subprocess.run([sys.executable, str(HOOK)], input=stdin_text,
                           capture_output=True, text=True, env=build_env(case))


def check(result: subprocess.CompletedProcess[str], case: Path) -> tuple[bool, str]:
    expected = int((case / "expected_exit.txt").read_text(encoding="utf-8").strip())
    expect_file = case / "expect.txt"
    assertions = expect_file.read_text(encoding="utf-8").splitlines() if expect_file.exists() else []
    combined = result.stdout + result.stderr
    lines = [f"exit={result.returncode} (expect {expected})"]
    ok = result.returncode == expected
    if not ok:
        lines.append("  ^^ FAIL exit code")
    for a in assertions:
        a = a.strip()
        if not a:
            continue
        polarity, substr = a[0], a[1:]
        present = substr in combined
        good = present if polarity == "+" else not present
        lines.append(f"  [{'ok' if good else 'FAIL'}] {a}")
        ok = ok and good
    lines.append(f"  stdout[:200]: {result.stdout.strip()[:200]!r}")
    lines.append(f"  stderr[:200]: {result.stderr.strip()[:200]!r}")
    return ok, "\n".join(lines)


def run_named_case(name: str, failures: list[str]) -> None:
    case = HERE / name
    print(f"=== {name} ===")
    result = run_hook(case)
    ok, report = check(result, case)
    print(report)
    print()
    if not ok:
        failures.append(name)


def main() -> int:
    failures: list[str] = []

    print("-- teardown (pre, idempotent) --")
    teardown_probe()

    # 1. unwired -- no DB dependency, runs standalone.
    run_named_case("a-unwired", failures)

    # 2. setup a fresh, clean probe world.
    print("-- setup probe world --")
    if not setup_probe():
        failures.append("setup_probe")
        print(f"run_fixtures: ABORTING -- setup failed. FAILURE(S): {', '.join(failures)}")
        return 1

    try:
        # 2.5. seed a REAL stamped stop-disposition row for the SHARED 'seenred' session every
        # original case's stdin.json carries -- so the (orthogonal) stop-disposition check stays
        # silent for the debt-focused cases below.
        print("-- seeding a stamped 'stopping:' decision row for the shared 'seenred' session --")
        r = led_stamped(SEENRED_SESSION, "decision",
                         "stopping: fixture baseline -- pre-seeded so the debt-focused cases stay "
                         "silent under the stop-disposition check; stands: nothing; remains: nothing")
        print(r.stdout.strip(), r.stderr.strip())
        if r.returncode != 0:
            failures.append("stop_disposition_baseline_seed")

        # 3. clean-world: freshly scaffolded, nothing open yet.
        run_named_case("b-clean-world", failures)

        # 4. create real debt: a work item claimed by THIS session, never closed (the run-5 shape,
        # narrowed by the queue-semantics predicate: UNCLAIMED alone no longer qualifies).
        print("-- creating debt: probe-item-1 opened + claimed (stamped seenred), never closed --")
        r = led("work", "open", "probe-item-1", "a test work item that is never closed")
        print(r.stdout.strip(), r.stderr.strip())
        if r.returncode != 0:
            failures.append("debt_setup_open")
        r = led_stamped(SEENRED_SESSION, "work", "claim", "probe-item-1")
        print(r.stdout.strip(), r.stderr.strip())
        if r.returncode != 0:
            failures.append("debt_setup_claim")

        # 5. dirty-world: call #1 against that debt -- expect BLOCK, count -> 1.
        run_named_case("c-dirty-world", failures)

        # 6. unasserted call #2 -- same identical debt, advances the breaker counter to 2.
        print("=== (unasserted) second identical block, advancing breaker to 2/3 ===")
        case = HERE / "c-dirty-world"
        r2 = run_hook(case)
        ok2 = r2.returncode == 2 and "seen 2/3 times" in (r2.stdout + r2.stderr)
        print(f"  [{'ok' if ok2 else 'FAIL'}] exit={r2.returncode}, contains 'seen 2/3 times'")
        print()
        if not ok2:
            failures.append("unasserted-second-block")

        # 7. circuit-breaker third repeat: call #3, same debt -- expect ALLOW-with-warning.
        run_named_case("d-circuit-breaker-third-repeat", failures)

        # 8. cleanup + bonus sanity: close the debt item (already claimed), verify a clean allow
        # and state-file reset.
        print("-- cleanup: close probe-item-1 --")
        r = led("work", "close", "probe-item-1", "dropped", "--review-witness", "fixture-cleanup", actor="reviewer")
        print(r.stdout.strip(), r.stderr.strip())
        case = HERE / "b-clean-world"  # same stdin/env as the original clean case
        r3 = run_hook(case)
        state_file = PROBE_DIR / ".claude" / "stop_clean_exit_state.json"
        ok3 = r3.returncode == 0 and not r3.stdout.strip() and not r3.stderr.strip() and not state_file.exists()
        print(f"=== (bonus) post-cleanup clean allow + state file cleared ===")
        print(f"  [{'ok' if ok3 else 'FAIL'}] exit={r3.returncode}, no output, state file absent")
        print()
        if not ok3:
            failures.append("post-cleanup-clean-and-reset")

        # 9. STOP-DISPOSITION WARNING, polarity 1 (Part 1, BACKLOG "Run-8 mid-run forensics",
        # 2026-07-11): a DIFFERENT session, never stamped with a 'stopping:' row, against this
        # SAME now-clean world (no debt at all) -- expect ALLOW (exit 0) with a loud warning.
        run_named_case("e-stop-disposition-warn", failures)

        # 10. seed a REAL stamped 'stopping:' row for a THIRD, distinct session.
        print("-- seeding a stamped 'stopping:' decision row for the disposition-silent case --")
        r = led_stamped(F_SESSION, "decision",
                         "stopping: fixture disposition test; stands: nothing; remains: nothing")
        print(r.stdout.strip(), r.stderr.strip())
        if r.returncode != 0:
            failures.append("stop_disposition_silent_seed")

        # 11. STOP-DISPOSITION WARNING, polarity 2: the identical shape as case 9, but THIS
        # session now carries a stamped disposition row -- SILENT (exit 0, no warning).
        run_named_case("f-stop-disposition-silent", failures)

        # 12. QUEUE SEMANTICS acceptance #1 (spec §4 bullet 1): an open, UNCLAIMED item never
        # blocks -- expect ALLOW with the informational "successor's queue" line.
        print("-- QUEUE SEMANTICS: opening probe-item-2, deliberately UNCLAIMED --")
        r = led("work", "open", "probe-item-2", "queue-semantics fixture: unclaimed, open")
        print(r.stdout.strip(), r.stderr.strip())
        if r.returncode != 0:
            failures.append("queue_semantics_unclaimed_setup")
        run_named_case("k-unclaimed-open-only", failures)
        print("-- QUEUE SEMANTICS: cleanup -- claim + close probe-item-2 --")
        led("work", "claim", "probe-item-2")
        r = led("work", "close", "probe-item-2", "dropped", "--review-witness", "fixture-cleanup", actor="reviewer")
        print(r.stdout.strip(), r.stderr.strip())

        # 13. QUEUE SEMANTICS acceptance #3, first half (spec §4 bullet 3): a claimed-by-this-
        # session item, bequeathed via a 'stopping: ...; remains: <slug>' row stamped to the SAME
        # session -- expect ALLOW, listed as bequeathed.
        print("-- QUEUE SEMANTICS: opening + claiming (stamped seenred) probe-item-3 --")
        r = led("work", "open", "probe-item-3", "queue-semantics fixture: bequeathed")
        print(r.stdout.strip(), r.stderr.strip())
        r = led_stamped(SEENRED_SESSION, "work", "claim", "probe-item-3")
        print(r.stdout.strip(), r.stderr.strip())
        if r.returncode != 0:
            failures.append("queue_semantics_bequeathed_setup")
        print("-- QUEUE SEMANTICS: stamping the bequeathing disposition for probe-item-3 --")
        r = led_stamped(SEENRED_SESSION, "decision",
                         "stopping: fixture bequest test; stands: nothing; remains: probe-item-3")
        print(r.stdout.strip(), r.stderr.strip())
        if r.returncode != 0:
            failures.append("queue_semantics_bequest_seed")
        run_named_case("l-bequeathed-allow", failures)
        print("-- QUEUE SEMANTICS: cleanup -- close probe-item-3 --")
        r = led("work", "close", "probe-item-3", "dropped", "--review-witness", "fixture-cleanup", actor="reviewer")
        print(r.stdout.strip(), r.stderr.strip())

        # 14. QUEUE SEMANTICS acceptance #3, second half ("bequest cannot be borrowed"): the SAME
        # shape, but the bequeathing disposition is stamped to a DIFFERENT session -- expect
        # BLOCK, unchanged.
        print("-- QUEUE SEMANTICS: opening + claiming (stamped seenred) probe-item-4 --")
        r = led("work", "open", "probe-item-4", "queue-semantics fixture: wrong-session bequest")
        print(r.stdout.strip(), r.stderr.strip())
        r = led_stamped(SEENRED_SESSION, "work", "claim", "probe-item-4")
        print(r.stdout.strip(), r.stderr.strip())
        if r.returncode != 0:
            failures.append("queue_semantics_wrong_session_setup")
        print("-- QUEUE SEMANTICS: stamping a disposition for probe-item-4 to a DIFFERENT session --")
        r = led_stamped(OTHER_SESSION, "decision",
                         "stopping: someone else's disposition; stands: nothing; remains: probe-item-4")
        print(r.stdout.strip(), r.stderr.strip())
        if r.returncode != 0:
            failures.append("queue_semantics_wrong_session_bequest_seed")
        run_named_case("m-bequest-wrong-session-still-blocks", failures)
        print("-- QUEUE SEMANTICS: cleanup -- close probe-item-4; verify clean allow + state reset --")
        r = led("work", "close", "probe-item-4", "dropped", "--review-witness", "fixture-cleanup", actor="reviewer")
        print(r.stdout.strip(), r.stderr.strip())
        case = HERE / "b-clean-world"
        r6 = run_hook(case)
        ok6 = r6.returncode == 0 and not r6.stdout.strip() and not r6.stderr.strip() and not state_file.exists()
        print("=== (bonus) queue-semantics cleanup: clean allow + state file cleared ===")
        print(f"  [{'ok' if ok6 else 'FAIL'}] exit={r6.returncode}, no output, state file absent")
        print()
        if not ok6:
            failures.append("queue-semantics-post-cleanup")

        # 15-19. BREAKER TRANSITION sequence (`stop-breaker-progress-reset-defect` /
        # `stop-breaker-state-type-guard`) -- both-polarity proof that a debt-set change which is
        # a strict SUBSET of the prior entries INHERITS the open breaker count instead of
        # resetting (progress does not re-arm), that a genuinely NEW entry still resets as before,
        # and that a corrupted/wrong-typed on-disk state file degrades safely (no traceback)
        # rather than raising. Debt substrate is now SESSION-CLAIMED items (queue-semantics
        # narrowing means unclaimed items can no longer stand in for breaker debt).
        print("-- BREAKER TRANSITION: claiming (stamped seenred) probe-item-5, probe-item-6 --")
        r = led("work", "open", "probe-item-5", "breaker-transition fixture item 5")
        print(r.stdout.strip(), r.stderr.strip())
        r = led_stamped(SEENRED_SESSION, "work", "claim", "probe-item-5")
        print(r.stdout.strip(), r.stderr.strip())
        r = led("work", "open", "probe-item-6", "breaker-transition fixture item 6")
        print(r.stdout.strip(), r.stderr.strip())
        r = led_stamped(SEENRED_SESSION, "work", "claim", "probe-item-6")
        print(r.stdout.strip(), r.stderr.strip())
        if r.returncode != 0:
            failures.append("breaker_transition_debt_setup")

        # g: call #1 against {probe-item-5, probe-item-6} -- BLOCK, count -> 1 (fresh signature).
        run_named_case("g-subset-progress-block-1", failures)

        # [progress] close probe-item-5 -- the remaining debt {probe-item-6} is a STRICT SUBSET of
        # {probe-item-5, probe-item-6}: nothing was added, one item left.
        print("-- BREAKER TRANSITION: closing probe-item-5 (progress, not new debt) --")
        r = led("work", "close", "probe-item-5", "dropped", "--review-witness", "fixture-cleanup", actor="reviewer")
        print(r.stdout.strip(), r.stderr.strip())
        if r.returncode != 0:
            failures.append("breaker_transition_progress_close")

        # h: call #2 against the now-smaller {probe-item-6} debt -- MUST still BLOCK, and the
        # count MUST be 2 (INHERITED), never reset to 1 -- this is the defect fix's whole point.
        run_named_case("h-subset-progress-block-2", failures)

        # [new debt] claim probe-item-7 alongside the still-open probe-item-6 -- the resulting set
        # {probe-item-6, probe-item-7} is NOT a subset of the prior {probe-item-6} (something was
        # ADDED), so the breaker MUST reset to 1 -- proves the fix narrows the reset condition, it
        # does not remove it.
        print("-- BREAKER TRANSITION: claiming (stamped seenred) probe-item-7 (genuinely NEW debt) --")
        r = led("work", "open", "probe-item-7", "breaker-transition fixture item 7 (new debt)")
        print(r.stdout.strip(), r.stderr.strip())
        r = led_stamped(SEENRED_SESSION, "work", "claim", "probe-item-7")
        print(r.stdout.strip(), r.stderr.strip())
        if r.returncode != 0:
            failures.append("breaker_transition_new_debt_setup")

        # i: call #3 against {probe-item-6, probe-item-7} -- BLOCK, count resets to 1.
        run_named_case("i-added-entry-resets-block", failures)

        # [corrupt] hand-write a wrong-typed state file (`stop-breaker-state-type-guard`):
        # entries=null, count="two" -- exactly the corruption/hand-edit shape the guard defends
        # against (this hook itself only ever writes a list/int there). The debt is UNCHANGED
        # ({probe-item-6, probe-item-7}) so this proves the corrupted PRIOR state degrades to
        # "treat as absent" rather than raising an uncaught TypeError out of `_breaker_transition`.
        print("-- BREAKER TRANSITION: corrupting the on-disk state file (wrong-typed fields) --")
        state_path = PROBE_DIR / ".claude" / "stop_clean_exit_state.json"
        state_path.write_text(json.dumps({"debt_hash": "corrupt-marker", "count": "two", "entries": None}),
                               encoding="utf-8")
        print(f"  wrote corrupted state to {state_path}")

        # j: call #4 against the SAME {probe-item-6, probe-item-7} debt, with the corrupted
        # state file in place -- MUST still BLOCK cleanly (exit 2, no traceback), count resets to 1
        # (the corrupted debt_hash/entries cannot match, so this degrades to a fresh signature).
        run_named_case("j-corrupted-state-degrades-safely", failures)

        # [unasserted, inline] a SECOND, more severe corruption shape: the state file's TOP LEVEL
        # is not even a dict (a bare JSON int). Proves `_load_state()`'s own isinstance(dict)
        # guard, not just the two field-level accessors, degrades safely.
        print("=== (unasserted) top-level-non-dict state file degrades safely ===")
        state_path.write_text("42", encoding="utf-8")
        r5 = run_hook(HERE / "j-corrupted-state-degrades-safely")
        ok5 = (r5.returncode == 2 and "Traceback" not in (r5.stdout + r5.stderr)
               and "seen 1/3 times" in (r5.stdout + r5.stderr))
        print(f"  [{'ok' if ok5 else 'FAIL'}] exit={r5.returncode}, no traceback, seen 1/3 times")
        print()
        if not ok5:
            failures.append("top-level-non-dict-state-degrades")

        # [cleanup] close the remaining breaker-transition debt items; verify a final clean allow
        # and that the state file is cleared (same bonus-sanity shape as step 8).
        print("-- BREAKER TRANSITION: cleanup -- closing probe-item-6, probe-item-7 --")
        led("work", "close", "probe-item-6", "dropped", "--review-witness", "fixture-cleanup", actor="reviewer")
        led("work", "close", "probe-item-7", "dropped", "--review-witness", "fixture-cleanup", actor="reviewer")
        case = HERE / "b-clean-world"
        r4 = run_hook(case)
        ok4 = r4.returncode == 0 and not r4.stdout.strip() and not r4.stderr.strip() and not state_path.exists()
        print("=== (bonus) breaker-transition cleanup: clean allow + state file cleared ===")
        print(f"  [{'ok' if ok4 else 'FAIL'}] exit={r4.returncode}, no output, state file absent")
        print()
        if not ok4:
            failures.append("breaker-transition-post-cleanup")

        # 23. QUEUE SEMANTICS acceptance #5 (spec §4 last bullet): the experience-world scenario
        # replayed end-to-end -- a mix of unclaimed queue items and one claimed-and-bequeathed
        # parent -- must fire NO breaker at all (the shape that, under the OLD predicate, drove
        # blocked/blocked/fail-open on the routine happy path).
        print("-- EXPERIENCE REPLAY: opening probe-item-8, probe-item-9 (UNCLAIMED queue) --")
        r = led("work", "open", "probe-item-8", "experience-replay fixture: queue item 1")
        print(r.stdout.strip(), r.stderr.strip())
        r = led("work", "open", "probe-item-9", "experience-replay fixture: queue item 2")
        print(r.stdout.strip(), r.stderr.strip())
        print("-- EXPERIENCE REPLAY: claiming (stamped seenred) + bequeathing probe-item-10 --")
        r = led("work", "open", "probe-item-10", "experience-replay fixture: claimed parent")
        print(r.stdout.strip(), r.stderr.strip())
        r = led_stamped(SEENRED_SESSION, "work", "claim", "probe-item-10")
        print(r.stdout.strip(), r.stderr.strip())
        if r.returncode != 0:
            failures.append("experience_replay_setup")
        r = led_stamped(SEENRED_SESSION, "decision",
                         "stopping: experience replay handoff; stands: queue decomposed per "
                         "preamble point 1; remains: probe-item-10")
        print(r.stdout.strip(), r.stderr.strip())
        if r.returncode != 0:
            failures.append("experience_replay_bequest_seed")
        run_named_case("n-experience-replay", failures)
        print("-- EXPERIENCE REPLAY: cleanup -- closing probe-item-8/9/10 --")
        led("work", "claim", "probe-item-8")
        led("work", "close", "probe-item-8", "dropped", "--review-witness", "fixture-cleanup", actor="reviewer")
        led("work", "claim", "probe-item-9")
        led("work", "close", "probe-item-9", "dropped", "--review-witness", "fixture-cleanup", actor="reviewer")
        led("work", "close", "probe-item-10", "dropped", "--review-witness", "fixture-cleanup", actor="reviewer")
    finally:
        print("-- teardown (post) --")
        teardown_probe()

    if failures:
        print(f"run_fixtures: {len(failures)} FAILURE(S): {', '.join(failures)}")
        return 1
    print("run_fixtures: all cases passed (14 named + 4 inline sanity checks).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
