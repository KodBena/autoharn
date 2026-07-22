#!/usr/bin/env python3
"""Seen-red specimen for night-build-defect-repair DEFECT 2 (bootstrap/templates/led.tmpl's
--evidence path-dereference guard, item artifact-claim-dereference-guard).

RCA (fresh-context verifier, this session's parent decision row): the guard shipped in b77ee7a
only inspected --evidence, never $statement, so the literal ledger rows 896-897 specimen (a path
embedded in STATEMENT PROSE, not passed via --evidence at all) still escapes; and it accepted a
directory because `test -e` is true for a directory too, even though row 898's own remediation is
explicitly "ls/wc of a FILE". b77ee7a shipped as one-off live writes with no re-runnable suite --
that absence is itself named as part of the gap this fixture closes.

This fixture drives the REAL `./led` shim (repo-root, house convention) against the LIVE
deployment (deployment.json) -- exactly the register b77ee7a's own witness used, but now banked
as a re-runnable both-polarity suite instead of one-off manual invocations. Every write lands a
real ledger row (never mocked); each is uniquely tagged (fixture id + timestamp) so it is
identifiable in `led --recent` after the fact, and the round-trip is independently verified via a
real `led show <id>` read-back, not just the write's own exit code.

RED (must REFUSE, no row written):
  - a dead --evidence path (artifact-claim-without-dereference, unchanged behavior)
  - an --evidence path that is a real, EXISTING directory but NOT explicitly cited as one
    (night-build-defect-repair's directory-acceptance gap)

GREEN (must ACCEPT, a real row lands, round-trip verified):
  - a live --evidence FILE
  - an --evidence directory explicitly cited via a trailing "/"
  - a statement containing a dead path-shaped token -- WARNS (stderr) but still writes (the
    declared asymmetry: --evidence asserts existence NOW, a statement may narrate the future)
  - a statement containing THREE dead path-shaped tokens -- WARNS ONCE (one preamble paragraph),
    followed by a 3-item list of the flagged tokens, still writes (AUTOHARN_BACKFLOW finding 5:
    pre-fix, warn_path_shaped_in_statement() printed the whole six-line explanation paragraph
    once PER flagged token -- three tokens meant the paragraph three times over in one command's
    stderr; post-fix it hoists the boilerplate out of the loop, so the paragraph prints once
    regardless of token count and the tokens themselves become a trailing list)
  - a statement containing a row:<id> citation -- untouched, no warning, writes clean
  - a statement containing a URL -- untouched, no warning, writes clean
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LED = str(ROOT / "led")
STAMP = str(int(time.time()))
TAG = f"seen-red-artifact-claim-dereference-guard-{STAMP}"

FAILURES: list[str] = []


def _check(label: str, cond: bool) -> None:
    print(f"  [{'ok' if cond else 'FAIL'}] {label}")
    if not cond:
        FAILURES.append(label)


def _run_led(*args: str) -> tuple[int, str, str]:
    cp = subprocess.run([LED, *args], cwd=ROOT, capture_output=True, text=True)
    return cp.returncode, cp.stdout, cp.stderr


def _current_max_id() -> int:
    rc, out, _ = _run_led("--recent", "1")
    if rc != 0 or not out.strip():
        return -1
    return int(out.split("|", 1)[0].strip())


def red_dead_evidence_path() -> None:
    print("# RED — dead --evidence path: MUST REFUSE, no row written")
    before = _current_max_id()
    rc, out, err = _run_led("--evidence", "/tmp/does-not-exist-nbdr-fixture-xyz",
                            "decision", f"{TAG}: dead evidence path probe")
    after = _current_max_id()
    _check("guard REFUSES (nonzero exit)", rc != 0)
    _check("teach-text cites the specimen class (896-899)", "896-899" in err)
    _check("no row written (max id unchanged)", after == before)


def red_bare_directory_evidence() -> None:
    print("# RED — bare directory --evidence (no trailing slash): MUST REFUSE, no row written")
    before = _current_max_id()
    rc, out, err = _run_led("--evidence", "bootstrap/templates",
                            "decision", f"{TAG}: bare directory evidence probe")
    after = _current_max_id()
    _check("guard REFUSES the bare directory (nonzero exit)", rc != 0)
    _check("teach-text names it a DIRECTORY, not a file", "DIRECTORY" in err)
    _check("teach-text points at the trailing-slash opt-in", "trailing slash" in err)
    _check("no row written (max id unchanged)", after == before)


def green_live_file_evidence() -> None:
    print("# GREEN — a live --evidence FILE: MUST ACCEPT, real row lands, round-trip verified")
    rc, out, err = _run_led("--evidence", "bootstrap/templates/led.tmpl",
                            "decision", f"{TAG}: live file evidence probe")
    _check("guard ACCEPTS (exit 0)", rc == 0)
    new_id = _current_max_id()
    rc2, out2, _ = _run_led("show", str(new_id))
    _check("real led round-trip: led show <id> reads the row back", rc2 == 0 and TAG in out2)


def green_explicit_directory_evidence() -> None:
    print("# GREEN — --evidence directory cited via trailing slash: MUST ACCEPT")
    rc, out, err = _run_led("--evidence", "bootstrap/templates/",
                            "decision", f"{TAG}: explicit trailing-slash directory probe")
    _check("guard ACCEPTS the explicitly-cited directory (exit 0)", rc == 0)
    new_id = _current_max_id()
    rc2, out2, _ = _run_led("show", str(new_id))
    _check("round-trip verified", rc2 == 0 and TAG in out2)


def green_statement_path_warns_but_writes() -> None:
    print("# GREEN — dead path-shaped token in STATEMENT prose: WARN-ONLY, still writes")
    rc, out, err = _run_led("decision",
                            f"{TAG}: about to write /tmp/does-not-exist-nbdr-statement-probe next")
    _check("write still succeeds (exit 0, warn-only, not a refusal)", rc == 0)
    _check("a WARNING is printed naming the path-shaped token", "WARNING" in err
           and "/tmp/does-not-exist-nbdr-statement-probe" in err)
    _check("warning states the warn-only/refuse asymmetry", "WARN-ONLY" in err)
    new_id = _current_max_id()
    rc2, out2, _ = _run_led("show", str(new_id))
    _check("round-trip verified", rc2 == 0 and TAG in out2)


def green_statement_multiple_path_tokens_single_preamble() -> None:
    print("# GREEN — THREE dead path-shaped tokens in one STATEMENT: ONE preamble, one list, "
          "still writes (AUTOHARN_BACKFLOW finding 5)")
    tok_a = "/tmp/does-not-exist-nbdr-multi-a"
    tok_b = "/tmp/does-not-exist-nbdr-multi-b"
    tok_c = "./tmp/does-not-exist-nbdr-multi-c"
    rc, out, err = _run_led(
        "decision",
        f"{TAG}: about to write {tok_a} and {tok_b} then {tok_c} across three separate files",
    )
    _check("write still succeeds (exit 0, warn-only, not a refusal)", rc == 0)
    preamble_count = err.count("led: WARNING -- the statement contains")
    _check("the explanation preamble prints EXACTLY ONCE, not once per token",
           preamble_count == 1)
    _check("all three flagged tokens are listed", tok_a in err and tok_b in err and tok_c in err)
    _check("warning states the warn-only/refuse asymmetry (once)", err.count("WARN-ONLY") == 1)
    new_id = _current_max_id()
    rc2, out2, _ = _run_led("show", str(new_id))
    _check("round-trip verified", rc2 == 0 and TAG in out2)


def green_row_citation_untouched() -> None:
    print("# GREEN — row:<id> citation in statement: untouched, no warning, writes clean")
    rc, out, err = _run_led("decision", f"{TAG}: row:1 citation untouched probe")
    _check("write succeeds (exit 0)", rc == 0)
    _check("no path-shape WARNING fires for a row: citation", "WARNING" not in err)


def green_url_untouched() -> None:
    print("# GREEN — URL in statement: untouched, no warning, writes clean")
    rc, out, err = _run_led("decision", f"{TAG}: https://example.com/nbdr-probe untouched")
    _check("write succeeds (exit 0)", rc == 0)
    _check("no path-shape WARNING fires for a URL", "WARNING" not in err)


def main() -> int:
    if not os.path.exists(LED) or not os.path.exists(str(ROOT / "deployment.json")):
        print("SPECIMEN UNEXERCISED — no ./led shim / deployment.json in this checkout; this "
              "fixture requires a live deployed project (the same requirement b77ee7a's own "
              "witness carried).")
        return 1
    red_dead_evidence_path()
    red_bare_directory_evidence()
    green_live_file_evidence()
    green_explicit_directory_evidence()
    green_statement_path_warns_but_writes()
    green_statement_multiple_path_tokens_single_preamble()
    green_row_citation_untouched()
    green_url_untouched()
    if FAILURES:
        print(f"\nSPECIMEN INERT — {len(FAILURES)} check(s) failed: {FAILURES}")
        return 1
    print(f"\n# artifact-claim-dereference-guard: RED (dead path, bare directory) refused with no "
          f"row written; GREEN (live file, explicit directory, statement-path warn, row:/URL "
          f"untouched) all accept with a real led round-trip. Tag: {TAG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
