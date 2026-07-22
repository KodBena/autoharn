#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for gates/apparatus_unknown_keys.py (BACKLOG
"Configuration-surface survey, adopter's eyes", 2026-07-11, gap 1). Pure filesystem, no
database -- the gate's only inputs are JSON files on disk and its own derived registry
(filing/apparatus_registry.py, itself derived from hooks/*.py) -- so this fixture mirrors
seen-red/bash-completion/run_fixtures.py's shape: a throwaway scratch directory under /tmp,
torn down before AND after this file runs, the gate invoked as a real subprocess (never
imported and called in-process) so the fixture proves the actual CLI contract, not an internal
function's behavior.

Cases:

  a-report-mode-default    -- no args: sweeps this repo's own shipped
                              bootstrap/templates/apparatus.json. Exit 0 (that file carries no
                              unrecognized KEY today -- a missing/undocumented mechanism, like
                              the bash_completion gap this gate's own commission found and fixed
                              elsewhere, is a different class this gate does not flag).
  b-gate-clean              -- a scratch apparatus.json naming only real mechanism keys. Exit 0.
  c-gate-unknown-key (RED)  -- a scratch apparatus.json with one typo'd key
                              ("doc_shapse_gate"). Exit 1; output names the exact bad key AND
                              the full valid set (the teach-text obligation).
  d-gate-unresolvable (RED)-- a target naming no apparatus.json at all (direct path or
                              <dir>/.claude/apparatus.json). Exit 2 -- a bad PATH is a louder,
                              distinct failure from a bad KEY, never conflated.
  e-world-dir-resolution    -- the SAME scratch file as (b)/(c), addressed by its WORLD ROOT
                              directory rather than the file path directly -- both resolution
                              forms produce identical verdicts.
  f-multiple-targets-mixed  -- one clean target + one bad target in the same invocation. Exit 1,
                              only the bad target's finding printed.

Usage: python3 seen-red/apparatus-unknown-keys/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
GATE = REPO / "gates" / "apparatus_unknown_keys.py"

sys.path.insert(0, str(REPO / "filing"))
import apparatus_registry  # noqa: E402  (filing/apparatus_registry.py, the module case g exercises directly)

PROBE_DIR = Path("/tmp/.apparatusunknownkeysprobe")


def teardown() -> None:
    shutil.rmtree(PROBE_DIR, ignore_errors=True)


def write_world(name: str, mechanisms: dict) -> Path:
    """Writes <PROBE_DIR>/<name>/.claude/apparatus.json and returns the WORLD ROOT dir (not the
    file) -- callers choose which of the two forms to pass to the gate."""
    root = PROBE_DIR / name
    (root / ".claude").mkdir(parents=True, exist_ok=True)
    (root / ".claude" / "apparatus.json").write_text(
        json.dumps({"mechanisms": mechanisms}), encoding="utf-8")
    return root


def run_gate(*targets: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(GATE), *targets],
                           capture_output=True, text=True, cwd=str(REPO), timeout=15)


def main() -> int:
    teardown()
    failures: list[str] = []

    try:
        # ---- a: report mode, default target (this repo's own shipped template) ----
        cp = run_gate()
        if cp.returncode != 0:
            failures.append(f"a-report-mode-default: expected exit 0, got {cp.returncode}\n{cp.stdout}{cp.stderr}")
        elif "0 unrecognized mechanism key(s)" not in cp.stdout:
            failures.append(f"a-report-mode-default: expected a clean verdict in stdout, got:\n{cp.stdout}")

        # ---- b: gate mode, clean scratch apparatus.json (file path form) ----
        clean_root = write_world("clean", {"change_gate": {"mode": "enforce"},
                                            "stamp_intercept": {"mode": "enforce"}})
        clean_file = clean_root / ".claude" / "apparatus.json"
        cp = run_gate(str(clean_file))
        if cp.returncode != 0:
            failures.append(f"b-gate-clean: expected exit 0, got {cp.returncode}\n{cp.stdout}{cp.stderr}")

        # ---- c: gate mode, one typo'd key (RED) ----
        bad_root = write_world("bad", {"change_gate": {"mode": "enforce"},
                                        "doc_shapse_gate": {"mode": "enforce"}})
        bad_file = bad_root / ".claude" / "apparatus.json"
        cp = run_gate(str(bad_file))
        if cp.returncode != 1:
            failures.append(f"c-gate-unknown-key: expected exit 1, got {cp.returncode}\n{cp.stdout}{cp.stderr}")
        if "doc_shapse_gate" not in cp.stdout:
            failures.append(f"c-gate-unknown-key: expected the bad key named in stdout, got:\n{cp.stdout}")
        if "change_gate" not in cp.stdout or "bash_completion" not in cp.stdout:
            failures.append(f"c-gate-unknown-key: expected the full valid set named in stdout, got:\n{cp.stdout}")

        # ---- d: unresolvable target (RED) ----
        cp = run_gate(str(PROBE_DIR / "does-not-exist-anywhere"))
        if cp.returncode != 2:
            failures.append(f"d-gate-unresolvable: expected exit 2, got {cp.returncode}\n{cp.stdout}{cp.stderr}")

        # ---- e: world-dir resolution form (same bad file, addressed by directory) ----
        cp = run_gate(str(bad_root))
        if cp.returncode != 1:
            failures.append(f"e-world-dir-resolution: expected exit 1, got {cp.returncode}\n{cp.stdout}{cp.stderr}")
        if "doc_shapse_gate" not in cp.stdout:
            failures.append(f"e-world-dir-resolution: expected the bad key named in stdout, got:\n{cp.stdout}")

        # ---- f: mixed targets, one clean + one bad ----
        cp = run_gate(str(clean_file), str(bad_file))
        if cp.returncode != 1:
            failures.append(f"f-multiple-targets-mixed: expected exit 1, got {cp.returncode}\n{cp.stdout}{cp.stderr}")
        if "doc_shapse_gate" not in cp.stdout:
            failures.append(f"f-multiple-targets-mixed: expected the bad key named in stdout, got:\n{cp.stdout}")

        # ---- g: the widened scan itself (tracker item `abc-loop-offering`) ------------
        # known_mechanisms() was widened 2026-07-12 to scan bootstrap/templates/*.tmpl
        # alongside hooks/*.py (the doc_attestation mechanism, read by distance-to-clean.tmpl,
        # is the first apparatus-reading file that is not a hook -- see filing/
        # apparatus_registry.py's own "WHERE IT SCANS" docstring section). This case proves the
        # GENERAL mechanism directly (an isolated scratch hooks_dir/templates_dir pair, not this
        # repo's own real files), both polarities: a mechanism named ONLY in a *.tmpl file is
        # recognized (g1); a name that appears in neither scanned source, or only under a
        # non-matching extension, is still correctly reported unknown (g2) -- the widening adds
        # a source, it does not loosen the match.
        scratch_hooks = PROBE_DIR / "scratch-hooks"
        scratch_templates = PROBE_DIR / "scratch-templates"
        scratch_hooks.mkdir(parents=True)
        scratch_templates.mkdir(parents=True)
        (scratch_hooks / "some_hook.py").write_text(
            'MECHANISM_KEY = "hook_only_mechanism"\n', encoding="utf-8")
        (scratch_templates / "some_verb.tmpl").write_text(
            'MECHANISM_KEY = "doc_attestation"\nmechs.get(MECHANISM_KEY)\n', encoding="utf-8")
        # A same-shaped constant in a NON-.tmpl file under templates_dir must NOT be picked up --
        # proves the scan is glob-scoped (*.tmpl), not "every file in the directory".
        (scratch_templates / "not_a_template.txt").write_text(
            'MECHANISM_KEY = "should_not_be_found"\n', encoding="utf-8")

        known = apparatus_registry.known_mechanisms(hooks_dir=scratch_hooks,
                                                     templates_dir=scratch_templates)
        print(f"CASE g1 (templates_dir scan, *.tmpl only): known={sorted(known)}")
        if "doc_attestation" not in known:
            failures.append(f"g1: expected 'doc_attestation' (declared only in a .tmpl file) in "
                            f"known_mechanisms(), got {sorted(known)}")
        if "hook_only_mechanism" not in known:
            failures.append(f"g1: expected 'hook_only_mechanism' (declared only in the scratch "
                            f"hooks_dir) in known_mechanisms(), got {sorted(known)}")
        if "should_not_be_found" in known:
            failures.append(f"g1: a MECHANISM_KEY inside a NON-.tmpl file under templates_dir "
                            f"must not be picked up -- the scan is glob-scoped, got {sorted(known)}")

        # g2: a genuinely unknown key, checked against the SAME scratch registry, is still
        # correctly flagged -- the widening adds a source, it never widens the MATCH itself.
        unknown = apparatus_registry.unknown_mechanism_keys(
            {"mechanisms": {"doc_attestation": {"mode": "off"}, "totally_made_up": {"mode": "off"}}},
            known=known)
        print(f"CASE g2 (genuine unknown key still flagged against the widened registry): "
              f"unknown={unknown}")
        if unknown != ["totally_made_up"]:
            failures.append(f"g2: expected exactly ['totally_made_up'] unknown (doc_attestation "
                            f"recognized, the made-up key flagged), got {unknown}")
    finally:
        teardown()

    if failures:
        print(f"seen-red/apparatus-unknown-keys/run_fixtures.py: {len(failures)} FAILURE(S):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("seen-red/apparatus-unknown-keys/run_fixtures.py: all 7 cases PASS "
          "(a-report-mode-default, b-gate-clean, c-gate-unknown-key, d-gate-unresolvable, "
          "e-world-dir-resolution, f-multiple-targets-mixed, g-templates-dir-scan)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
