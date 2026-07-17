#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T18:57:55Z
#   last-change: 2026-07-15T18:57:55Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity live proof for ledger item
`led-work-depends-default-type-advisory` (gates/fixture_census.py REGISTRY entry
"led-work-depends-default-type-advisory").

THE DEFECT (root cause named in the commissioning brief): a live deployment session
systematically recorded every genuine precedence constraint ("X must finish before Y may
close") as `edge_type` 'informs' -- the fail-safe default `led work depends` writes when
`--type` is omitted -- and never once used `--type blocks-close`, so nothing mechanical could
ever refuse a close-out-of-order. The CLI silently defaulted to the unenforced type at exactly
the moment the operator was declaring a constraint, with no teach at the point of the omission.

THE FIX (bootstrap/templates/led.tmpl, `work depends` verb): when the caller omits --type, the
row is STILL written exactly as before (informs by omission, or -- on a pre-s30 kernel, no
edge_type column at all) -- this is a WARN-ONLY advisory, never a refusal -- but a one-line
STDERR advisory now fires at the exact point of the omission: "recorded as informs (advisory
only -- never enforced at close); if <on-slug> must be finished before <slug> may close, use
--type blocks-close." An explicit --type (either value) suppresses the advisory -- the operator
already made the typed choice, nothing to teach.

CASES (all live subprocess runs of the real `./led` against real scratch deployments):

  ADOPT-FULL           -- bootstrap/new-project.sh --new-world stands up a scratch deployment
                           carrying the full s15..s30 birth chain (edge_type column present).
  ADOPT-PRE-S30         -- bootstrap/track-work.sh stands up a scratch deployment on the s15..s25
                           chain only (edge_type column ABSENT) -- proves the advisory fires on
                           BOTH kernel shapes, not just the s30-carrying one.
  GREEN-OMITTED-ADVISORY (full-s30 world) -- `led work depends a b` (no --type): the advisory
                           text appears on stderr AND the row still lands (edge_type informs by
                           omission, unchanged write behavior).
  GREEN-OMITTED-ADVISORY (pre-s30 world)  -- same shape on the pre-s30 world: advisory appears
                           on stderr, row still lands (no edge_type column at all -- unaffected).
  GREEN-EXPLICIT-BLOCKS-CLOSE-NO-ADVISORY -- `led work depends c d --type blocks-close`: no
                           advisory text on stderr, row lands with edge_type='blocks-close'.
  GREEN-EXPLICIT-INFORMS-NO-ADVISORY      -- `led work depends e f --type informs`: no advisory
                           text on stderr, row lands with edge_type='informs' (the explicit
                           choice, distinguishable from the omitted-default case above only by
                           the stored column, not by any behavioral difference -- the advisory is
                           the only thing that changes when --type is supplied).

RED evidence for this item (banked in red.txt) is the PRE-FIX led.tmpl (obtained via
`git stash push -- bootstrap/templates/led.tmpl` immediately before this fixture's own commit
lands, then `git stash pop` to restore the fix): the two GREEN-OMITTED-ADVISORY cases FAIL to
find the advisory text (the row still lands identically -- pre-fix and post-fix write behavior
is byte-identical, only the STDERR teach differs), reproducing the reported defect (nothing
mechanical or textual ever taught the operator that the default silently means "never
enforced").

Usage: python3 seen-red/led-work-depends-default-type-advisory/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
TRACK_WORK = REPO / "bootstrap" / "track-work.sh"

PGHOST, PGDB = "192.168.122.1", "toy"
WORLD_FULL = "ldadvfxfull"
WORLD_PRE = "ldadvfxpre"
TAG = f"led-work-depends-default-type-advisory-{int(time.time())}"

ADVISORY_MARKER = "recorded as informs (advisory only -- never enforced at close or claim)"


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def teardown_full() -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {WORLD_FULL} CASCADE; "
        f"DROP SCHEMA IF EXISTS {WORLD_FULL}_kernel CASCADE; DROP OWNED BY {WORLD_FULL}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {WORLD_FULL}_rw;"])


def teardown_pre() -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=0", "-q",
        "-c", f"DROP SCHEMA IF EXISTS {WORLD_PRE} CASCADE;",
        "-c", f"DROP SCHEMA IF EXISTS {WORLD_PRE}_kernel CASCADE;",
        "-c", f"DROP ROLE IF EXISTS {WORLD_PRE}_rw;"])


def teardown_all() -> None:
    teardown_full()
    teardown_pre()


def led(world_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return sh([str(world_dir / "led"), *args], cwd=str(world_dir))


def scaffold_full() -> tuple[Path, dict]:
    """Full s15..s30 birth chain (edge_type column present)."""
    tmp = Path(tempfile.mkdtemp(prefix=f"{WORLD_FULL}-seenred-"))
    world_dir = tmp / WORLD_FULL
    r = sh(["bash", str(NEW_PROJECT), str(world_dir), "--new-world", WORLD_FULL,
            "--db", PGDB, "--host", PGHOST])
    if r.returncode != 0:
        raise RuntimeError(f"SCAFFOLD-FULL FAILED: {r.stdout[-1500:]} {r.stderr[-1500:]}")
    for verb in ("led", "judge", "pickup"):
        p = world_dir / verb
        if p.exists():
            p.chmod(0o755)
    dep = json.loads((world_dir / "deployment.json").read_text(encoding="utf-8"))
    return world_dir, dep


def scaffold_pre(dest: Path) -> None:
    """s15..s25 chain only (track-work.sh's own ceiling -- edge_type column absent)."""
    r = sh([str(TRACK_WORK), str(dest), "--name", WORLD_PRE, "--db", PGDB,
            "--host", PGHOST, "--schema", WORLD_PRE, "--kern", f"{WORLD_PRE}_kernel",
            "--role", f"{WORLD_PRE}_rw"], cwd=str(REPO))
    if r.returncode != 0 or not (dest / "deployment.json").exists():
        raise RuntimeError(f"SCAFFOLD-PRE FAILED: exit={r.returncode}\n"
                            f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")


def main() -> int:
    teardown_all()
    failures: list[str] = []
    tmps: list[Path] = []

    try:
        # ------------------------------------------------------------------------ ADOPT-FULL
        print(f"== scaffolding throwaway --new-world {WORLD_FULL} (full s15..s30 birth chain) ==")
        world_full, dep_full = scaffold_full()
        tmps.append(world_full.parent)
        print(f"  scaffold OK (schema={dep_full['schema']}).\n")

        # ------------------------------------------------------------------------ ADOPT-PRE-S30
        print(f"== scaffolding throwaway {WORLD_PRE} via track-work.sh (s15..s25 only) ==")
        tmp_pre = Path(tempfile.mkdtemp(prefix=f"{WORLD_PRE}-seenred-"))
        tmps.append(tmp_pre)
        world_pre = tmp_pre / "project"
        scaffold_pre(world_pre)
        print("  scaffold OK.\n")

        # --------------------------------------------------------- GREEN-OMITTED-ADVISORY (full)
        led(world_full, "work", "open", f"{TAG}-a", "A")
        led(world_full, "work", "open", f"{TAG}-b", "B")
        r_full_omit = led(world_full, "work", "depends", f"{TAG}-a", f"{TAG}-b")
        stderr_full_omit = r_full_omit.stderr
        advisory_present = ADVISORY_MARKER in stderr_full_omit
        mentions_slugs = f"{TAG}-b" in stderr_full_omit and f"{TAG}-a" in stderr_full_omit
        row_landed = r_full_omit.returncode == 0
        ok = advisory_present and mentions_slugs and row_landed
        check("omitted-advisory-full-s30-world", ok,
              f"exit={r_full_omit.returncode} advisory_present={advisory_present} "
              f"mentions_slugs={mentions_slugs} row_landed={row_landed}\n"
              f"STDERR:\n{stderr_full_omit}", failures)

        # ------------------------------------------------------ GREEN-OMITTED-ADVISORY (pre-s30)
        led(world_pre, "work", "open", f"{TAG}-c", "C")
        led(world_pre, "work", "open", f"{TAG}-d", "D")
        r_pre_omit = led(world_pre, "work", "depends", f"{TAG}-c", f"{TAG}-d")
        stderr_pre_omit = r_pre_omit.stderr
        advisory_present_pre = ADVISORY_MARKER in stderr_pre_omit
        row_landed_pre = r_pre_omit.returncode == 0
        ok = advisory_present_pre and row_landed_pre
        check("omitted-advisory-pre-s30-world", ok,
              f"exit={r_pre_omit.returncode} advisory_present={advisory_present_pre} "
              f"row_landed={row_landed_pre}\nSTDERR:\n{stderr_pre_omit}", failures)

        # ---------------------------------------------------- GREEN-EXPLICIT-BLOCKS-CLOSE (full)
        led(world_full, "work", "open", f"{TAG}-e", "E")
        led(world_full, "work", "open", f"{TAG}-f", "F")
        r_bc = led(world_full, "work", "depends", f"{TAG}-e", f"{TAG}-f", "--type", "blocks-close")
        advisory_absent_bc = ADVISORY_MARKER not in r_bc.stderr
        ok = r_bc.returncode == 0 and advisory_absent_bc
        check("explicit-blocks-close-no-advisory", ok,
              f"exit={r_bc.returncode} advisory_absent={advisory_absent_bc}\nSTDERR:\n{r_bc.stderr}",
              failures)

        # ---------------------------------------------------------- GREEN-EXPLICIT-INFORMS (full)
        led(world_full, "work", "open", f"{TAG}-g", "G")
        led(world_full, "work", "open", f"{TAG}-h", "H")
        r_in = led(world_full, "work", "depends", f"{TAG}-g", f"{TAG}-h", "--type", "informs")
        advisory_absent_in = ADVISORY_MARKER not in r_in.stderr
        ok = r_in.returncode == 0 and advisory_absent_in
        check("explicit-informs-no-advisory", ok,
              f"exit={r_in.returncode} advisory_absent={advisory_absent_in}\nSTDERR:\n{r_in.stderr}",
              failures)

    finally:
        teardown_all()
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- led work depends default-type advisory both-polarity proof "
          "(advisory fires on omission on both a full-s30 and a pre-s30 world, row-write "
          "behavior unchanged either way; an explicit --type of either value suppresses the "
          "advisory), zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
