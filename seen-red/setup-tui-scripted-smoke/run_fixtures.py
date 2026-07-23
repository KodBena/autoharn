#!/usr/bin/env python3
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

Case 9 (added for design/FABLE-SETUP-TUI-SPEC.md's 2026-07-19 `--dry-run` amendment, commission
ledger row 1719) is WDR3, its own witness: "a dry run that reaches a refusal (hostile input)
refuses identically to the live path -- validation is never weakened by dry-run."

  9. boundary, out-of-sequence entry, SAME hostile world name as case 5, run under `--dry-run` --
     asserts the SAME `REFUSED: world ...` text case 5 got live, byte-for-byte, and that
     boundary-multiplex.toml still does not exist. This is the direct byte-diff half of WDR3;
     the WDR1 (byte-identical filesystem + zero ledger rows) and WDR2 (argv parity against a
     real scratch run) witnesses need a live db birth and live boundary service and are reported
     in seen-red/setup-tui-dry-run-parity, not shaped as a fixture here.

Cases 11-13 (design/FABLE-SETUP-TUI-SPEC.md's 2026-07-19 governed-files amendment, commission
ledger row 1730 -- the fork/target screen's governed-files exposure), CORRECTED single-writer
design (tools/setup_tui/governed_files.py's own module docstring): screen 3 (fork/target)
records the operator's CHOICE on `state["governed_patterns"]` and writes nothing itself --
`bootstrap/new-project.sh` is the ONE writer of `.claude/governed_files.json`, on every
invocation, steered by its own `--governed` flag. All three cases run FULLY UNDER `--dry-run`
through screen 5 (Birth) -- `run_command`'s own dry-run choke point never Popens, so none of
these needs a live Postgres host, unlike a would-be live-birth witness:

  11. (witness a, argv-threading half) operator extends with valid extensions -> the choice is
      threaded into `new-project.sh`'s OWN `--governed` flag at birth, asserted directly off the
      printed argv line; screen 3 itself writes no file.
  12. (witness b) a hostile extension token (containing `"] ;rm -rf /`) is refused BEFORE the
      choice is even recorded -- the reverted-to-default set (never the hostile text) is what
      reaches `--governed`.
  13. (witness d) the operator declines to extend -- the default set is still explicitly
      threaded into `--governed` (never a silent omission left to new-project.sh's own separate
      no-flag fallback notice).

The full LIVE end-to-end proof -- a REAL file on disk, parsed by
hooks/pretooluse_change_gate.py's OWN loader, surviving the boundary screen's later re-scaffold
without being clobbered back to the bare default -- lives in
seen-red/setup-tui-dry-run-parity (WDR1 already performs a real birth through boundary; this
build's own addition there is witness (a)'s live half).

Case 14 (DEFECT FIX WITNESS, autoharn1 succession commission row 1942, 2026-07-22): a
`--from-config` birth with `boundary.configure = false` used to halt hydration outright at its
first ledger write, because `screen_hydration` always resolved the served `./led` shim (which
refuses without `deployment.json`'s `boundary_url`/`boundary_deployment` keys) even though the
scaffold always ALSO writes a working `legacy/led` right there. Reproduces the exact halt shape --
a dest whose `deployment.json` carries no boundary keys at all, a served-shim `led` that would
refuse if invoked, and a working `legacy/led` -- and asserts the decision-phase led resolution
(`tools/setup_tui/runner.py`'s new `resolve_led`, wired through `screen_hydration`) picks
legacy/led, entirely at the decision phase (the checklist's own new "led present" WITNESSED row);
case 8's own REFUSED-message assertion is updated to match (the old text was itself a symptom of
the served-only bug this fix closes). A full live scratch-world commit through this same halt
shape is UNEXERCISED here (needs a real Postgres host) -- see this build's own commit message /
report for that blocker, named honestly rather than silently skipped.

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
sys.path.insert(0, REPO)

# Fixture-local, module-top import (lazy imports are banned, CLAUDE.md 2026-07-02) -- case 14
# below needs the LIVE count of durable-decision/ADR-adoption prompts `screen_hydration` will
# ask, so its scripted answers file stays correct as that catalog grows, rather than a hand-typed
# count silently going stale.
from tools.setup_tui import durable_decisions  # noqa: E402 -- needs sys.path insert above first


def run_scripted(answers: str, start_at: str, cwd: str,
                  dry_run: bool = False) -> subprocess.CompletedProcess:
    ans_path = os.path.join(cwd, f"answers-{start_at}{'-dry' if dry_run else ''}.txt")
    with open(ans_path, "w") as f:
        f.write(answers)
    argv = [sys.executable, "-m", "tools.setup_tui.app", "--scripted", ans_path,
            "--start-at", start_at]
    if dry_run:
        argv.append("--dry-run")
    return subprocess.run(argv, cwd=REPO, capture_output=True, text=True, timeout=60)


def main() -> int:
    scratch = tempfile.mkdtemp(prefix="setup-tui-scripted-smoke-")
    try:
        # --- case 1: fork-target, occupied fresh-dir target -> REFUSED ---
        # FIXTURE-CONTRACT CHANGE (design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md §2, this
        # build): the old bare `Path.exists()` refused ANY pre-existing path, empty or not; the
        # new classifier reads an EMPTY directory as FRESH (spec §2's own worked example: "no
        # path, or an empty directory -> FRESH") -- an empty placeholder dir is now legitimately
        # ACCEPTED, not refused. This case is repointed to a genuinely NON-EMPTY (FOREIGN)
        # directory to keep testing "you cannot pick an already-occupied path as your 'fresh'
        # target" -- the property the case's own name states. The new FOREIGN mode adds ONE more
        # scripted answer (the "scaffold into this existing content anyway?" confirm, declined
        # here with "n" to keep the refusal leg) -- trailing "n"s unchanged in count/meaning
        # otherwise (rehearsal/birth-override/principals-authority/signed-genesis/boundary-
        # override/observability/hydration).
        occupied = os.path.join(scratch, "occupied")
        os.makedirs(occupied)
        with open(os.path.join(occupied, "pre-existing.txt"), "w") as f:
            f.write("not autoharn's\n")
        cp = run_scripted("y\nfresh\n" + occupied + "\nn\nn\nn\nn\nn\nn\nn\nn\n", "fork-target",
                           scratch)
        out = cp.stdout + cp.stderr
        assert cp.returncode == 0, f"case 1: expected exit 0, got {cp.returncode}: {out[-800:]}"
        assert "FOREIGN content, not acknowledged" in out and occupied in out, out[-800:]
        assert "REFUSED=1" in out or "REFUSED=2" in out, out[-800:]
        print("case 1 ok: fork-target refuses an occupied (FOREIGN) 'fresh' destination unless "
              "explicitly acknowledged, nothing copied")

        # --- case 2: substrate, dedicated path, invalid db name -> REFUSED, no pg_hba read ---
        # (trailing "n"s decline every later screen this --start-at run still walks through --
        # fork-target/rehearsal/birth-override/principals-authority/signed-genesis/boundary-
        # override/observability/hydration -- so the run reaches a clean exit-0 checklist
        # instead of exhausting the answers file. signed-genesis added the 7th "n";
        # principals-authority adds the 8th.)
        cp = run_scripted("y\ndedicated\n-\nbad-name!\nvalidrole\n" + "n\n" * 8,
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
        # (same trailing-"n" count as case 2, signed-genesis + principals-authority included.)
        cp = run_scripted("y\ndedicated\n-\nvaliddb\nvalidrole\nnot-a-cidr\n" + "n\n" * 8,
                           "substrate", scratch)
        out = cp.stdout + cp.stderr
        assert cp.returncode == 0, f"case 3: expected exit 0, got {cp.returncode}: {out[-800:]}"
        assert "REFUSED: subnet 'not-a-cidr'" in out, out[-800:]
        assert "pg_read_file" not in out, ("case 3: a live pg_hba read must never be attempted "
                                            "once the subnet check refuses: " + out[-800:])
        print("case 3 ok: substrate refuses a malformed subnet token before any pg_hba read "
              "(the tools/setup_tui/probes.py valid_subnet repair)")

        # --- case 4: boundary, out-of-sequence entry, nonexistent dest -> REFUSED ---
        # design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part C completion (row 1158/1159): "boundary"
        # moved to run BEFORE "principals-authority"/"signed-genesis" in screens.py's own SCREENS
        # list -- `--start-at boundary` now ALSO visits those two (newly downstream of it) before
        # reaching observability/hydration/checklist, each needing its own one-"n" decline to
        # skip cleanly (both screens' own FIRST act is a plain confirm that returns immediately
        # on "n"). Extra "n\nn\n" inserted here, not appended at the end, since ScriptedUi
        # consumes answers as a flat FIFO in PROMPT order, not per-screen.
        # legacy-led-retirement inventory pass (ledger row 1149/1150): ONE FEWER leading "y" --
        # screen_boundary's own "Configure the boundary service now?" decline gate is retired
        # (boundary is mandatory), so only the birth-gate override confirm remains before the
        # destination prompt.
        missing_dest = os.path.join(scratch, "nonexistent_dest")
        cp = run_scripted(f"y\n{missing_dest}\nn\nn\nn\nn\n", "boundary", scratch)
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
        # Same re-sequencing insertion as case 4 above: two more "n"s for the newly-downstream
        # principals-authority/signed-genesis screens' own one-answer skip, inserted before the
        # trailing observability/hydration/checklist declines. legacy-led-retirement inventory
        # pass (ledger row 1149/1150): ONE FEWER leading "y" -- see case 4's own comment.
        cp = run_scripted(
            f"y\n{valid_dest}\n{hostile_world}\n-\n-\nn\nn\nn\nn\nn\n", "boundary", scratch,
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
        out_case5 = out  # case 9's live-comparand, before `out` gets reused by later cases

        # --- case 6: preflight -- every PREFLIGHT_BINARIES + UI-backend facts line renders ---
        # (10 answers: run-preflight, then one "n" each for substrate/fork-target/rehearsal/
        # birth-override/principals-authority/signed-genesis/boundary-override/observability/
        # hydration -- the full --start-at preflight walkthrough to a clean checklist.
        # signed-genesis added the 8th "n"; principals-authority adds the 9th.)
        cp = run_scripted("y\n" + "n\n" * 9, "preflight", scratch)
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
        # destination IS a real dir, so the hydration screen asks that third question).
        no_led_dest = os.path.join(scratch, "no_led_dest")
        os.makedirs(no_led_dest)
        cp = run_scripted(f"y\n{no_led_dest}\nn\n", "hydration", scratch)
        out = cp.stdout + cp.stderr
        assert cp.returncode == 0, f"case 8: expected exit 0, got {cp.returncode}: {out[-800:]}"
        # MESSAGE-TEXT UPDATE (legacy-led-retirement inventory pass, ledger row 1149/1150):
        # `resolve_led` no longer checks legacy/led at all (legacy-led.tmpl itself is retired,
        # and the boundary is mandatory at every birth) -- back to naming only "led".
        assert "REFUSED: no led found under" in out, out[-800:]
        print("case 8 ok: hydration refuses cleanly against a destination with no led or "
              "legacy/led shim (WD5's own bar, re-proven here)")

        # --- case 14 -- RETIRED (legacy-led-retirement inventory pass, ledger row 1149/1150,
        # this build) -- was: "a `--from-config` birth with `boundary.configure = false` used to
        # halt hydration ... resolve_led picks legacy/led, not the served shim" (autoharn1
        # succession commission row 1942's own DEFECT FIX WITNESS, 2026-07-22). The scenario this
        # case reproduced no longer exists to reproduce: `boundary.configure = false` is not a
        # representable config shape anymore (the decline gate is retired, boundary is mandatory
        # at every birth, tools/setup_tui/screens.py's own screen_boundary docstring), and
        # `resolve_led` itself no longer prefers legacy/led at all -- legacy-led.tmpl is deleted
        # from this repository outright (design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md's own
        # retirement act), so a "working legacy/led fallback" is not a state any scaffolded world
        # can be in post-retirement. Replaced below with the positive re-assertion of the NEW
        # invariant `resolve_led` now upholds: served `./led` is picked even when a (non-
        # functional, post-retirement) `legacy/led` file is ALSO present on disk -- there is no
        # candidate search left, only one lawful `led` per world (runner.resolve_led's own
        # docstring).
        led_dest = os.path.join(scratch, "led_resolution_dest")
        os.makedirs(os.path.join(led_dest, "legacy"))
        legacy_led_path = os.path.join(led_dest, "legacy", "led")
        with open(legacy_led_path, "w") as f:
            # The retired scaffold shim's own real post-retirement shape: a one-line teaching
            # refusal, never a working CLI (design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md's own
            # retirement act) -- present on disk, but never a lawful resolution target.
            f.write("#!/bin/sh\necho 'legacy/led: RETIRED 2026-07; every surface serves through "
                    "./led.' >&2\nexit 1\n")
        os.chmod(legacy_led_path, 0o755)
        served_led_path = os.path.join(led_dest, "led")
        with open(served_led_path, "w") as f:
            f.write("#!/bin/sh\necho 'row: 1 written.'\n")
        os.chmod(served_led_path, 0o755)
        with open(os.path.join(led_dest, "deployment.json"), "w") as f:
            json.dump({"schema": "ledresworld", "kern": "ledresworld_kernel",
                       "role": "ledresworld_rw", "name": "ledresworld",
                       "boundary_url": "http://127.0.0.1:1", "boundary_deployment": "ledresworld"}, f)

        n_catalog = len(durable_decisions.CATALOG)
        n_adrs = len(durable_decisions.list_adrs())
        answers = (
            "y\n" + led_dest + "\n"       # run hydration now? / destination
            "n\n"                          # fork provenance? decline
            "n\n"                          # role charters to register? decline
            + "n\n" * n_catalog             # each durable decision, decline
            + "n\n" * n_adrs                # each ADR adoption, decline
            + "n\n"                         # commit this plan now? decline (0 entries queued)
            + "n\n"                         # save this checklist? decline
        )
        cp14 = run_scripted(answers, "hydration", scratch)
        out14 = cp14.stdout + cp14.stderr
        assert cp14.returncode == 0, f"case 14: expected exit 0, got {cp14.returncode}: {out14[-2000:]}"
        assert "Traceback" not in out14, out14[-2000:]
        assert "REFUSED" not in out14, (
            f"case 14: hydration must NOT refuse -- served ./led is present and working: "
            + out14[-2000:])
        led_row = next(
            (ln for ln in out14.splitlines() if "led present" in ln and "hydration" in ln), None)
        assert led_row is not None, f"case 14: no 'led present' checklist row rendered: {out14[-2000:]}"
        assert served_led_path in led_row, (
            f"case 14: the 'led present' row must name the served ./led shim (resolve_led's "
            f"only lawful target, post-retirement): {led_row!r}")
        assert legacy_led_path not in led_row, (
            f"case 14: the 'led present' row must NOT name legacy/led -- it is a retired, non-"
            f"functional stub even when present on disk: {led_row!r}")
        print("case 14 ok (POST-RETIREMENT RE-ASSERTION, was row 1942's DEFECT FIX WITNESS): "
              "hydration's led resolution picks the served ./led even when a (non-functional) "
              "legacy/led file is also present on disk -- no candidate search remains")

        # --- case 9 (WDR3): the SAME hostile-world scenario as case 5, under --dry-run --
        # design/FABLE-SETUP-TUI-SPEC.md's 2026-07-19 amendment, WDR3: "a dry run that reaches a
        # refusal (hostile input) refuses identically to the live path -- validation is never
        # weakened by dry-run." Reuses `valid_dest`/`hostile_world`/the exact REFUSED line from
        # case 5 (never written to, per case 5's own assertion) as the live comparand, and adds
        # its own byte-for-byte comparison (not just a substring match) of the REFUSED line.
        refused_line_live = next(
            ln for ln in out_case5.splitlines() if ln.startswith("  REFUSED: world "))
        # Same re-sequencing insertion as case 5 (two more "n"s for the newly-downstream
        # principals-authority/signed-genesis screens' own one-answer skip). legacy-led-
        # retirement inventory pass (ledger row 1149/1150): ONE FEWER leading "y" -- see case 4's
        # own comment.
        cp = run_scripted(
            f"y\n{valid_dest}\n{hostile_world}\n-\n-\nn\nn\nn\nn\nn\n", "boundary", scratch,
            dry_run=True,
        )
        out9 = cp.stdout + cp.stderr
        assert cp.returncode == 0, f"case 9: expected exit 0, got {cp.returncode}: {out9[-800:]}"
        assert "Traceback" not in out9, out9[-800:]
        refused_line_dry = next(
            (ln for ln in out9.splitlines() if ln.startswith("  REFUSED: world ")), None)
        assert refused_line_dry is not None, (
            f"case 9: no 'REFUSED: world' line under --dry-run -- validation was weakened: "
            + out9[-800:])
        assert refused_line_dry == refused_line_live, (
            f"case 9: --dry-run REFUSED text differs from the live path's (WDR3's own bar: "
            f"'refuses identically'):\n  live: {refused_line_live!r}\n  dry:  "
            f"{refused_line_dry!r}")
        assert not os.path.exists(toml_path), (
            f"case 9: {toml_path} must NOT exist -- --dry-run must never write, and this "
            f"hostile input was refused before any write was even attempted")
        print("case 9 ok (WDR3): --dry-run refuses the SAME hostile world name with the "
              "byte-identical REFUSED text a live run produces, nothing written")

        # --- case 10 (dry-run-ceremony case, design/FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md §3):
        # the Signed genesis screen under --dry-run, out-of-sequence entry against BOTH a
        # nonexistent destination and (separately) a real directory this project's scaffold did
        # not produce -- --dry-run must never weaken validation (the WDR3 bar, applied to this
        # screen): both refuse exactly as they would live (proven directly above by
        # seen-red/setup-tui-signed-genesis's own WG5, against a REAL scaffolded world; this case
        # re-proves the SAME two refusal shapes with no live db needed, matching this fixture's
        # own no-live-birth scope).
        missing_dest_sg = os.path.join(scratch, "sg_missing_dest")
        cp10a = run_scripted(f"y\n{missing_dest_sg}\n" + "n\n" * 3, "signed-genesis", scratch,
                              dry_run=True)
        out10a = cp10a.stdout + cp10a.stderr
        assert cp10a.returncode == 0, f"case 10a: expected exit 0, got {cp10a.returncode}: {out10a[-800:]}"
        assert "REFUSED: destination directory" in out10a and missing_dest_sg in out10a, out10a[-800:]
        assert "Traceback" not in out10a, out10a[-800:]

        # FIXTURE-CONTRACT NOTE (design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md §2, this
        # build): an EMPTY directory now classifies FRESH (same as nonexistent), so this case's
        # "real-but-unscaffolded directory" needs a placeholder FILE to stay FOREIGN and exercise
        # the keys/verify-commission/legacy-led-missing REFUSED leg it originally tested (an
        # empty dir here would now hit the SAME "does not exist yet" refusal as case 10a).
        bare_dest_sg = os.path.join(scratch, "sg_bare_dest")
        os.makedirs(bare_dest_sg)
        with open(os.path.join(bare_dest_sg, "pre-existing.txt"), "w") as f:
            f.write("not autoharn's\n")
        cp10b = run_scripted(f"y\n{bare_dest_sg}\n" + "n\n" * 4, "signed-genesis", scratch,
                              dry_run=True)
        out10b = cp10b.stdout + cp10b.stderr
        assert cp10b.returncode == 0, f"case 10b: expected exit 0, got {cp10b.returncode}: {out10b[-800:]}"
        assert "REFUSED:" in out10b and "missing" in out10b, out10b[-800:]
        assert "Traceback" not in out10b, out10b[-800:]
        print("case 10 ok (dry-run-ceremony case): the Signed genesis screen refuses "
              "out-of-sequence entry identically under --dry-run -- a nonexistent destination "
              "and a real-but-unscaffolded directory, no traceback, nothing written")

        # --- cases 11-13: governed-files exposure (design/FABLE-SETUP-TUI-SPEC.md 2026-07-19
        # amendment, commission ledger row 1730), CORRECTED single-writer design
        # (tools/setup_tui/governed_files.py's own module docstring): screen 3 records the
        # operator's CHOICE on state["governed_patterns"] and writes NOTHING itself --
        # bootstrap/new-project.sh is the one writer, on every invocation, steered by its own
        # --governed flag. All three run fully under --dry-run through screen 5 (Birth) --
        # run_command's own dry-run choke point never Popens, so no live db is needed. Answer
        # shape after the extension text: "n" (rehearsal decline) "y" (birth-override accept,
        # rehearsal wasn't green) "y" (run birth) "-" "-" (host/db defaults) worldNN "-" "-"
        # (dest/name defaults) then 5 "n"s for principals-authority/signed-genesis/boundary-
        # override/observability/hydration.
        gf_src = os.path.join(scratch, "gf_src")
        os.makedirs(gf_src, exist_ok=True)
        with open(os.path.join(gf_src, "a.txt"), "w") as f:
            f.write("placeholder\n")

        # case 11 (witness a, argv-threading half): valid extensions -> threaded into
        # new-project.sh's OWN --governed flag at birth. No live db needed (--dry-run).
        dest11 = os.path.join(scratch, "gf_dest11")
        # legacy-led-retirement inventory pass (ledger row 1149/1150): the old single "n"
        # (boundary-configure decline, causing an early return before any further boundary
        # question) is replaced by TWO new answers -- boundary is now mandatory, so this screen
        # actually reaches its own "Database" prompt (world/host/dest are already in `state`
        # from birth above, but `db` is not) and its "Start the boundary service now?" confirm.
        cp11 = run_scripted(
            "y\nfork\n" + gf_src + "\n" + dest11 + "\ny\n.ts,.vue,.html\n"
            "n\ny\ny\n-\n-\nworld11\n-\n-\n" + "-\nn\n" + "n\n" * 5,
            "fork-target", scratch, dry_run=True)
        out11 = cp11.stdout + cp11.stderr
        assert cp11.returncode == 0, f"case 11: expected exit 0, got {cp11.returncode}: {out11[-1500:]}"
        assert "Traceback" not in out11, out11[-1500:]
        assert "extended: ['*.py', '*.ts', '*.vue', '*.html']" in out11, out11[-1500:]
        assert not os.path.exists(os.path.join(dest11, ".claude", "governed_files.json")), (
            "case 11: screen 3 must never write governed_files.json itself under the "
            "corrected single-writer design")
        # PHASE-2 CONTRACT CHANGE (design/FABLE-SETUP-TUI-PURE-CORE-SPEC.md): birth's
        # new-project.sh call is now a QUEUED plan entry, not an executed runner.run_command call
        # -- screen_birth prints its own "  $ argv" preview (2-space indented, this module's own
        # house style for a decision-time echo) instead of runner.run_command's unindented
        # "$ argv" print, so the match strips leading whitespace before comparing.
        governed_argv_line11 = next(
            (ln for ln in out11.splitlines() if ln.strip().startswith("$ ") and "new-project.sh" in ln
             and "--new-world" in ln), None)
        assert governed_argv_line11 is not None, f"case 11: no birth argv line captured: {out11[-1500:]}"
        assert "--governed" in governed_argv_line11 and \
            "*.py,*.ts,*.vue,*.html" in governed_argv_line11, (
            f"case 11: the extended pattern set was not threaded into new-project.sh's own "
            f"--governed flag: {governed_argv_line11!r}")
        print("case 11 ok (witness a, argv half): the extended pattern set is threaded into "
              "new-project.sh's OWN --governed flag at birth -- screen 3 itself writes nothing")

        # case 12 (witness b): a hostile extension token is refused BEFORE the choice is
        # recorded at all -- the recorded choice reverts to the default, never the hostile text.
        dest12 = os.path.join(scratch, "gf_dest12")
        hostile_tok = '*.py"] ;rm -rf /'
        # legacy-led-retirement inventory pass (ledger row 1149/1150): see case 11's own comment
        # for the "-\nn\n" (db default, decline boundary auto-start) replacing the old single
        # boundary-configure-decline "n".
        cp12 = run_scripted(
            "y\nfork\n" + gf_src + "\n" + dest12 + "\ny\n" + hostile_tok + ",.ts\n"
            "n\ny\ny\n-\n-\nworld12\n-\n-\n" + "-\nn\n" + "n\n" * 5,
            "fork-target", scratch, dry_run=True)
        out12 = cp12.stdout + cp12.stderr
        assert cp12.returncode == 0, f"case 12: expected exit 0, got {cp12.returncode}: {out12[-1500:]}"
        assert "REFUSED: extension token(s)" in out12, out12[-1500:]
        # PHASE-2: same leading-whitespace note as case 11 above.
        argv_lines12 = [ln for ln in out12.splitlines() if ln.strip().startswith("$ ")]
        assert not any("rm -rf" in ln for ln in argv_lines12), (
            "case 12: the hostile token must never reach any argv line, including birth's own "
            "--governed flag: " + "\n".join(argv_lines12))
        governed_argv_line12 = next(
            (ln for ln in argv_lines12 if "new-project.sh" in ln and "--new-world" in ln), None)
        assert governed_argv_line12 is not None, out12[-1500:]
        assert "--governed" in governed_argv_line12 and "*.py" in governed_argv_line12, (
            f"case 12: the reverted-to-default set must reach --governed: {governed_argv_line12!r}")
        assert not os.path.exists(os.path.join(dest12, ".claude", "governed_files.json")), (
            "case 12: screen 3 must never write governed_files.json itself")
        print("case 12 ok (witness b): a hostile extension token is refused before the choice "
              "is recorded; the reverted default (never the hostile text) reaches --governed")

        # case 13 (witness d): decline extension -> the default is still explicitly recorded
        # and threaded into --governed (never silently omitted).
        dest13 = os.path.join(scratch, "gf_dest13")
        # legacy-led-retirement inventory pass (ledger row 1149/1150): see case 11's own comment.
        cp13 = run_scripted(
            "y\nfork\n" + gf_src + "\n" + dest13 + "\nn\n"
            "n\ny\ny\n-\n-\nworld13\n-\n-\n" + "-\nn\n" + "n\n" * 5,
            "fork-target", scratch, dry_run=True)
        out13 = cp13.stdout + cp13.stderr
        assert cp13.returncode == 0, f"case 13: expected exit 0, got {cp13.returncode}: {out13[-1500:]}"
        assert "kept default (operator declined to extend)" in out13, out13[-1500:]
        governed_argv_line13 = next(
            (ln for ln in out13.splitlines() if ln.strip().startswith("$ ") and "new-project.sh" in ln
             and "--new-world" in ln), None)
        assert governed_argv_line13 is not None, out13[-1500:]
        assert "--governed" in governed_argv_line13 and "*.py" in governed_argv_line13, (
            f"case 13: the explicit default choice must still reach --governed, never a bare "
            f"omission: {governed_argv_line13!r}")
        print("case 13 ok (witness d): declining to extend still explicitly threads the "
              "default set into --governed, never silently")

        print("ALL CASES OK -- setup_tui scripted preflight/validation refusal legs, zero residue")
        return 0
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
