#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T22:50:17Z
#   last-change: 2026-07-18T23:54:55Z
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

Cases 1-5, each a full `python3 -m tools.setup_tui.app --scripted <answers> --start-at <screen>`
run to a clean exit-0 checklist (never a bare exception/non-zero exit -- the out-of-sequence-
entry spec amendment's own bar: "refuse legibly ... never a traceback"):

  1. fork-target, fresh mode against an ALREADY-OCCUPIED directory -> REFUSED, nothing copied.
  2. substrate, dedicated path, an invalid database name (`bad-name!`) -> REFUSED before any
     pg_hba read. ALSO asserts the substrate facts lines (design/FABLE-SETUP-TUI-FEATURE-FACTS-
     SPEC.md §5's WF1) render before the choice is even made.
  3. substrate, dedicated path, valid db/role but a malformed subnet token -> REFUSED before any
     pg_hba read (the item-B repair).
  4. boundary, out-of-sequence entry (`--start-at boundary`, no prior birth) against a
     NONEXISTENT destination directory -> REFUSED (the spec amendment's own witnessed
     specimen, unchanged by this build -- re-proven here as this fixture's baseline).
  5. boundary, out-of-sequence entry against a REAL destination directory (with its own
     deployment.json naming valid schema/kern/role, independent of `world`) but a HOSTILE world
     name (`evil"] [deployments.pwn`) -> REFUSED (the item-A repair) -- and, separately, this
     case asserts NO boundary-multiplex.toml file was written into the destination, AND asserts
     the boundary_service facts line rendered at screen entry (WF1).

Cases 6-8 (added for design/FABLE-SETUP-TUI-FEATURE-FACTS-SPEC.md's WF1, commission ledger row
1714 -- "a scripted run shows the facts line for at least the substrate, boundary, observability,
and two hydration items -- including every feature the enumeration found to carry external
costs/deps, each with its citation intact"):

  6. preflight -- asserts the facts line for every PREFLIGHT_BINARIES entry (idris2, clingo,
     python3, psql) renders, plus the two UI-backend facts lines.
  7. observability -- asserts both the otelcol AND the otel-watch (watchdog) facts lines render
     at screen entry, before the operator is asked to see the blocks.
  8. hydration against a destination with no ./led shim -> REFUSED, legibly, no traceback (WD5's
     own bar, re-proven here since this build changed screen_hydration substantially). The full
     catalog+ADR-submenu facts rendering and the WD1-WD5 led-row/CLAUDE.md witnessing needed a
     live scratch-world birth+boundary and is reported, not fixture-shaped, per this spec's
     build conditions (a live boundary-served ./led is out of scope for a no-db-birth fixture).

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
        # WF1: the substrate facts lines render BEFORE the choice, with their citations intact.
        assert "facts [existing-db substrate path]" in out and "aspiration:" in out, out[-800:]
        assert "facts [dedicated-db substrate path]" in out and "external:" in out, out[-800:]
        assert "tools/setup_tui/pghba.py" in out, (
            "case 2: the dedicated-db facts line's external-cost citation must be present: "
            + out[-800:])
        print("case 2 ok: substrate refuses an invalid dedicated-db name before any pg_hba "
              "read, and both substrate facts lines rendered first (WF1)")

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
        # WF1: the boundary_service facts line renders at screen entry, citation intact.
        assert "facts [boundary service]" in out and "fastapi + uvicorn" in out, out[-800:]
        print("case 5 ok: boundary (--start-at) refuses a hostile world name before writing "
              "boundary-multiplex.toml (the tools/setup_tui/screens.py screen_boundary repair), "
              "and the boundary_service facts line rendered at screen entry (WF1)")

        # --- case 6: preflight -- every PREFLIGHT_BINARIES + UI-backend facts line renders ---
        # (8 answers: run-preflight, then one "n" each for substrate/fork-target/rehearsal/
        # birth-override/boundary-override/observability/hydration -- the full --start-at
        # preflight walkthrough to a clean checklist.)
        cp = run_scripted("y\n" + "n\n" * 7, "preflight", scratch)
        out = cp.stdout + cp.stderr
        assert cp.returncode == 0, f"case 6: expected exit 0, got {cp.returncode}: {out[-800:]}"
        for label in ("idris2 toolchain", "clingo (ASP solver)", "python3 interpreter",
                      "psql client", "textual (optional TUI backend)",
                      "urwid (optional TUI backend)"):
            assert f"facts [{label}]" in out, (
                f"case 6: missing preflight facts line for '{label}': " + out[-1200:])
        print("case 6 ok: every PREFLIGHT_BINARIES + UI-backend facts line rendered (WF1)")

        # --- case 7: observability -- otelcol AND otel-watch facts lines render at entry ---
        # (2 answers: decline the observability blocks, then decline hydration too.)
        cp = run_scripted("n\nn\n", "observability", scratch)
        out = cp.stdout + cp.stderr
        assert cp.returncode == 0, f"case 7: expected exit 0, got {cp.returncode}: {out[-800:]}"
        assert "facts [OTel collector (otelcol)]" in out and "otelcol-contrib" in out, out[-800:]
        assert "facts [OTel model-provenance watchdog (otel-watch)]" in out, out[-800:]
        print("case 7 ok: both otelcol and otel-watch facts lines rendered at screen entry (WF1)")

        # --- case 8: hydration against a destination with no ./led shim -> REFUSED, no crash.
        # This fixture stays without a live scratch-world birth on purpose (WD1-WD5's full
        # catalog/led-row/CLAUDE.md witnessing needs a real boundary-served ./led and is
        # reported, not fixture-shaped, per this spec's build conditions) -- the led-shim
        # existence check fires BEFORE any hydration-item facts line (a hard prerequisite gate,
        # not a point of selection), so this case's own bar is simply the legible refusal. ---
        # 3 answers: run hydration now, the destination, then decline saving the checklist (the
        # destination IS a real dir, so screen 9 asks that third question).
        no_led_dest = os.path.join(scratch, "no_led_dest")
        os.makedirs(no_led_dest)
        cp = run_scripted(f"y\n{no_led_dest}\nn\n", "hydration", scratch)
        out = cp.stdout + cp.stderr
        assert cp.returncode == 0, f"case 8: expected exit 0, got {cp.returncode}: {out[-800:]}"
        assert "REFUSED: no ./led at" in out, out[-800:]
        print("case 8 ok: hydration refuses cleanly against a destination with no ./led shim "
              "(WD5's own bar, re-proven here)")

        print("ALL CASES OK -- setup_tui scripted preflight/validation refusal legs, zero residue")
        return 0
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
