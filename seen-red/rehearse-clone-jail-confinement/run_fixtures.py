#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T12:58:21Z
#   last-change: 2026-07-15T12:58:53Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""Seen-red specimen for night-build-defect-repair DEFECT 3 (bootstrap/rehearse-from-origin.sh's
initial clone running outside the env jail and outside the trace, letting a `~/.gitconfig`
url.insteadOf rewrite substitute a local decoy for the public repo -- the same-host illusion
re-entering through the guard's own clone step, verifier-proven live this session).

Two checks, cheap-static first, live-network second (mirrors gates/fixture_census.py's own
"static census is the standing net, live re-execution is the acceptance gate" split, and this
project's own rehearse-from-origin.sh already requires live network+DB by its own docstring, so
gating a heavier live check behind reachability is not a new posture here):

STATIC (always runs, no network/DB needed) -- structural confinement: the script's `git clone`
invocation must appear textually AFTER run_jailed() is defined, and must be issued THROUGH
run_jailed (never a bare top-level `git clone` before the jail exists). RED against the pre-fix
shape (clone before the jail, untraced); GREEN against the current shape.

LIVE (network + PGHOST/PGDATABASE reachable) -- the actual adversarial reproduction: a decoy
local repo + a polluted throwaway HOME carrying a `~/.gitconfig` url.insteadOf rewrite for the
real public URL. Runs bootstrap/rehearse-from-origin.sh for real, with that polluted HOME as the
CALLING environment's HOME. GREEN means the clone still resolves to the real remote's HEAD (the
attack is defeated) -- checked by (a) the resolved SHA equal to a fresh `git ls-remote` of the
real URL and (b) the DECOY.txt marker file never appearing anywhere the script touches. If
network/DB is unreachable this leg reports UNEXERCISED (not a failure) rather than a false pass.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "bootstrap" / "rehearse-from-origin.sh"
REPO_URL = "https://github.com/KodBena/autoharn.git"

FAILURES: list[str] = []


def _check(label: str, cond: bool) -> None:
    print(f"  [{'ok' if cond else 'FAIL'}] {label}")
    if not cond:
        FAILURES.append(label)


def _code_lines(text: str) -> list[tuple[int, str]]:
    """(1-based line number, line text) pairs for every NON-comment, NON-blank line -- a `#`
    anywhere before the first non-whitespace char, or a bare blank line, is skipped. This is a
    deliberately cheap textual filter (not a real shell parser), sufficient to keep a doc-comment
    that merely MENTIONS `git clone` in prose (this script's own header, "Fresh `git clone
    <repo-url>`...") from being mistaken for an executable invocation."""
    out = []
    for i, ln in enumerate(text.splitlines(), start=1):
        stripped = ln.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        out.append((i, ln))
    return out


def static_clone_is_jailed() -> None:
    print("# STATIC — the clone must run textually AFTER run_jailed() is defined, and THROUGH it")
    text = SCRIPT.read_text()
    def_match = re.search(r"^run_jailed\(\)\s*\{", text, re.MULTILINE)
    _check("run_jailed() is defined in the script", def_match is not None)
    if def_match is None:
        return
    jail_def_line = text[:def_match.start()].count("\n") + 1
    code = _code_lines(text)
    # every EXECUTABLE (non-comment) line containing a literal `git clone` invocation
    clone_lines = [(ln, txt) for ln, txt in code if "git clone" in txt]
    _check("at least one executable `git clone` invocation exists", len(clone_lines) > 0)
    bare_clones_before_jail = [(ln, txt) for ln, txt in clone_lines if ln < jail_def_line]
    _check("no executable `git clone` appears BEFORE run_jailed() is defined "
           "(the pre-fix shape)", len(bare_clones_before_jail) == 0)
    for ln, txt in clone_lines:
        if ln < jail_def_line:
            continue
        _check(f"post-jail clone on line {ln} is wrapped in run_jailed(...)",
               "run_jailed" in txt)


def _real_remote_head(repo_url: str) -> str | None:
    cp = subprocess.run(["git", "ls-remote", repo_url, "HEAD"],
                        capture_output=True, text=True, timeout=20)
    if cp.returncode != 0 or not cp.stdout.strip():
        return None
    return cp.stdout.split()[0]


def live_negative_control_pollution_defeated() -> None:
    print("# LIVE — a polluted HOME (~/.gitconfig url.insteadOf) must NOT redirect the clone")
    pghost = os.environ.get("PGHOST")
    pgdatabase = os.environ.get("PGDATABASE")
    if not pghost or not pgdatabase:
        print("  UNEXERCISED — PGHOST/PGDATABASE not set in this environment; this leg requires "
              "a live scratch database (the same requirement rehearse-from-origin.sh's own "
              "docstring states) and is skipped rather than falsely reported.")
        return
    real_head = _real_remote_head(REPO_URL)
    if real_head is None:
        print("  UNEXERCISED — could not reach the real public remote (no network); skipped "
              "rather than falsely reported.")
        return
    with tempfile.TemporaryDirectory() as td:
        scratch = Path(td)
        decoy = scratch / "decoy"
        pollutedhome = scratch / "pollutedhome"
        decoy.mkdir()
        pollutedhome.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=decoy, check=True)
        subprocess.run(["git", "config", "user.email", "decoy@example.com"], cwd=decoy, check=True)
        subprocess.run(["git", "config", "user.name", "decoy"], cwd=decoy, check=True)
        (decoy / "DECOY.txt").write_text("DECOY REPO -- not the real public autoharn\n")
        subprocess.run(["git", "add", "DECOY.txt"], cwd=decoy, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "decoy"], cwd=decoy, check=True)
        (pollutedhome / ".gitconfig").write_text(
            f'[url "file://{decoy}"]\n\tinsteadOf = {REPO_URL}\n'
            f'[user]\n\temail = decoy@example.com\n\tname = decoy\n'
        )
        env = dict(os.environ)
        env["HOME"] = str(pollutedhome)
        env["PGHOST"] = pghost
        env["PGDATABASE"] = pgdatabase
        cp = subprocess.run(
            ["bash", str(SCRIPT), REPO_URL, "--schema-suffix", "fixturenegctl"],
            cwd=ROOT, env=env, capture_output=True, text=True, timeout=300,
        )
        combined = cp.stdout + cp.stderr
        cloned_line = next((ln for ln in combined.splitlines() if ln.strip().startswith("cloned ")), "")
        _check("script produced a 'cloned ...' line", cloned_line != "")
        _check(f"cloned SHA matches the real remote HEAD ({real_head[:12]}...), not the decoy",
               real_head in cloned_line)
        _check("the decoy's own content never appears in the script's output",
               "DECOY" not in combined)
        _check("either the run succeeded outright, or it refused loudly (never a silent decoy "
               "pass)", cp.returncode == 0 or "REFUSED" in combined)


def main() -> int:
    static_clone_is_jailed()
    live_negative_control_pollution_defeated()
    if FAILURES:
        print(f"\nSPECIMEN INERT — {len(FAILURES)} check(s) failed: {FAILURES}")
        return 1
    print("\n# rehearse-clone-jail-confinement: clone is textually confined inside run_jailed(); "
          "live negative control (polluted HOME url.insteadOf) is defeated -- the clone reaches "
          "the real remote's HEAD, never the decoy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
