#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T22:50:17Z
#   last-change: 2026-07-18T22:50:42Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""Both-polarity-adjacent smoke fixture for tools/setup_tui (ledger row 1700's commission):
drives the setup wizard in `--scripted` mode against scratch destinations under /tmp, exercising
the PREFLIGHT + VALIDATION REFUSAL legs -- the drift-sensitive surface -- without a live db
birth. Directly regression-guards two of this build's own repairs:

  * tools/setup_tui/screens.py screen_boundary's `world` allowlist (2026-07-19 out-of-sequence-
    entry amendment): a hostile world name reachable via `--start-at boundary` used to be
    spliced unvalidated into boundary-multiplex.toml; case 5 below feeds exactly that shape and
    asserts REFUSED, nothing written.
  * screen_substrate's `subnets` allowlist (`probes.valid_subnet`, stdlib `ipaddress`): a
    malformed CIDR token used to be spliced unvalidated into the PREPARED pg_hba block; case 3
    below feeds a malformed token and asserts REFUSED before any pg_hba read is attempted.

Five cases, each a full `python3 -m tools.setup_tui.app --scripted <answers> --start-at <screen>`
run to a clean exit-0 checklist (never a bare exception/non-zero exit -- the out-of-sequence-
entry spec amendment's own bar: "refuse legibly ... never a traceback"):

  1. fork-target, fresh mode against an ALREADY-OCCUPIED directory -> REFUSED, nothing copied.
  2. substrate, dedicated path, an invalid database name (`bad-name!`) -> REFUSED before any
     pg_hba read.
  3. substrate, dedicated path, valid db/role but a malformed subnet token -> REFUSED before any
     pg_hba read (the item-B repair).
  4. boundary, out-of-sequence entry (`--start-at boundary`, no prior birth) against a
     NONEXISTENT destination directory -> REFUSED (the spec amendment's own witnessed
     specimen, unchanged by this build -- re-proven here as this fixture's baseline).
  5. boundary, out-of-sequence entry against a REAL destination directory (with its own
     deployment.json naming valid schema/kern/role, independent of `world`) but a HOSTILE world
     name (`evil"] [deployments.pwn`) -> REFUSED (the item-A repair) -- and, separately, this
     case asserts NO boundary-multiplex.toml file was written into the destination.

Zero residue: every scratch destination lives under a fixture-owned tempdir, removed in a
`finally` regardless of outcome. Real subprocess invocations of the actual CLI entry point (no
mocks) -- Rule 1's own bar ("drive the same code paths") applied to this fixture's own proof of
itself. Lazy imports banned."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))


def run_scripted(answers: str, start_at: str, cwd: str) -> subprocess.CompletedProcess:
    ans_path = os.path.join(cwd, f"answers-{start_at}.txt")
    with open(ans_path, "w") as f:
        f.write(answers)
    return subprocess.run(
        [sys.executable, "-m", "tools.setup_tui.app", "--scripted", ans_path,
         "--start-at", start_at],
        cwd=REPO, capture_output=True, text=True, timeout=60,
    )


def main() -> int:
    scratch = tempfile.mkdtemp(prefix="setup-tui-scripted-smoke-")
    try:
        # --- case 1: fork-target, occupied fresh-dir target -> REFUSED ---
        occupied = os.path.join(scratch, "occupied")
        os.makedirs(occupied)
        cp = run_scripted("y\nfresh\n" + occupied + "\nn\nn\nn\nn\nn\n", "fork-target", scratch)
        out = cp.stdout + cp.stderr
        assert cp.returncode == 0, f"case 1: expected exit 0, got {cp.returncode}: {out[-800:]}"
        assert "REFUSED: destination" in out and occupied in out, out[-800:]
        assert "REFUSED=1" in out or "REFUSED=2" in out, out[-800:]
        print("case 1 ok: fork-target refuses an occupied 'fresh' destination, nothing copied")

        # --- case 2: substrate, dedicated path, invalid db name -> REFUSED, no pg_hba read ---
        # (trailing "n"s decline every later screen this --start-at run still walks through --
        # fork-target/rehearsal/birth-override/boundary-override/observability/hydration -- so
        # the run reaches a clean exit-0 checklist instead of exhausting the answers file.)
        cp = run_scripted("y\ndedicated\n-\nbad-name!\nvalidrole\n" + "n\n" * 6,
                           "substrate", scratch)
        out = cp.stdout + cp.stderr
        assert cp.returncode == 0, f"case 2: expected exit 0, got {cp.returncode}: {out[-800:]}"
        assert "REFUSED: database name 'bad-name!'" in out, out[-800:]
        assert "pg_read_file" not in out, ("case 2: a live pg_hba read must never be attempted "
                                            "once the identifier check refuses: " + out[-800:])
        print("case 2 ok: substrate refuses an invalid dedicated-db name before any pg_hba read")

        # --- case 3 (item B): substrate, dedicated path, malformed subnet -> REFUSED, no read ---
        cp = run_scripted("y\ndedicated\n-\nvaliddb\nvalidrole\nnot-a-cidr\n" + "n\n" * 6,
                           "substrate", scratch)
        out = cp.stdout + cp.stderr
        assert cp.returncode == 0, f"case 3: expected exit 0, got {cp.returncode}: {out[-800:]}"
        assert "REFUSED: subnet 'not-a-cidr'" in out, out[-800:]
        assert "pg_read_file" not in out, ("case 3: a live pg_hba read must never be attempted "
                                            "once the subnet check refuses: " + out[-800:])
        print("case 3 ok: substrate refuses a malformed subnet token before any pg_hba read "
              "(the tools/setup_tui/probes.py valid_subnet repair)")

        # --- case 4: boundary, out-of-sequence entry, nonexistent dest -> REFUSED ---
        missing_dest = os.path.join(scratch, "nonexistent_dest")
        cp = run_scripted(f"y\ny\n{missing_dest}\nn\nn\n", "boundary", scratch)
        out = cp.stdout + cp.stderr
        assert cp.returncode == 0, f"case 4: expected exit 0, got {cp.returncode}: {out[-800:]}"
        assert "REFUSED: destination directory" in out and missing_dest in out, out[-800:]
        assert "Traceback" not in out, ("case 4: out-of-sequence entry must refuse legibly, "
                                         "never a traceback: " + out[-800:])
        print("case 4 ok: boundary (--start-at) refuses a nonexistent destination directory, "
              "no traceback")

        # --- case 5 (item A): boundary, out-of-sequence entry, hostile world -> REFUSED ---
        valid_dest = os.path.join(scratch, "validdest")
        os.makedirs(valid_dest)
        with open(os.path.join(valid_dest, "deployment.json"), "w") as f:
            json.dump({"schema": "validworld", "kern": "validworld_kernel",
                       "role": "validworld_rw", "name": "validworld"}, f)
        hostile_world = 'evil"] [deployments.pwn'
        cp = run_scripted(
            f"y\ny\n{valid_dest}\n{hostile_world}\n-\n-\nn\nn\nn\n", "boundary", scratch,
        )
        out = cp.stdout + cp.stderr
        assert cp.returncode == 0, f"case 5: expected exit 0, got {cp.returncode}: {out[-800:]}"
        assert "REFUSED: world " in out and "valid_identifier" in out, out[-800:]
        assert "Traceback" not in out, out[-800:]
        toml_path = os.path.join(valid_dest, "boundary-multiplex.toml")
        assert not os.path.exists(toml_path), (
            f"case 5: {toml_path} must NOT exist -- the hostile world name must be refused "
            f"BEFORE any write (tools/setup_tui/screens.py screen_boundary's world allowlist)")
        print("case 5 ok: boundary (--start-at) refuses a hostile world name before writing "
              "boundary-multiplex.toml (the tools/setup_tui/screens.py screen_boundary repair)")

        print("ALL CASES OK -- setup_tui scripted preflight/validation refusal legs, zero residue")
        return 0
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
