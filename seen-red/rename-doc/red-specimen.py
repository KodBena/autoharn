#!/usr/bin/env python3
"""Seen-red specimen for tools/rename_doc.py (gates/fixture_census.py REGISTRY entry
"rename-doc"). Proves, both polarities, on live subprocess runs against a throwaway temp git
repo (never against the real tracked corpus — a fixture must not write a fake attestation or a
mangled link into this repo's own audit trail):

  GREEN — a real rename_doc.py invocation (git mv + corpus-wide link rewrite + Audience header +
          link_integrity check) leaves every referencing file's link resolving to the new path,
          and the tool's own final link_integrity.py run exits 0.
  RED   — a document with a deliberately-missed reference (one referencing file's link is put
          back to the now-nonexistent OLD path, simulating a rewrite step that missed one
          occurrence) makes link_integrity.py exit 1, naming the broken link — the exact signal
          this tool's own final gate-check step relies on to refuse "safe to commit."

No network, no DB, no cost. Usage: python3 seen-red/rename-doc/red-specimen.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "rename_doc.py"
GATE = REPO / "gates" / "link_integrity.py"
ATTEST_GATE = REPO / "gates" / "doc_attestation_presence.py"
LINK_LIB = REPO / "gates" / "link_integrity.py"


def _mkrepo() -> Path:
    d = Path(tempfile.mkdtemp(prefix="rename_doc_seenred_"))
    subprocess.run(["git", "init", "-q"], cwd=d, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=d, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=d, check=True)
    (d / "design").mkdir()
    (d / "gates").mkdir()
    shutil.copy(LINK_LIB, d / "gates" / "link_integrity.py")
    shutil.copy(ATTEST_GATE, d / "gates" / "doc_attestation_presence.py")
    (d / "design" / "OLD-DOC.md").write_text(
        "# Old Doc Title\n\nProse here.\n", encoding="utf-8")
    (d / "REFERRER.md").write_text(
        "# Referrer\n\nSee [Old Doc](design/OLD-DOC.md) for detail.\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=d, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=d, check=True)
    return d


def _run_gate(cwd: Path) -> subprocess.CompletedProcess:
    """Run the FIXTURE REPO's own copy of the gate, not the real repo's — link_integrity.py
    derives its ROOT from its own file path (`os.path.dirname(os.path.dirname(__file__))`), not
    from cwd, so invoking the outer repo's copy would silently scan the outer repo instead of
    the throwaway temp tree."""
    return subprocess.run([sys.executable, str(cwd / "gates" / "link_integrity.py")], cwd=cwd,
                           capture_output=True, text=True)


def case_green() -> bool:
    d = _mkrepo()
    try:
        r = subprocess.run(
            [sys.executable, str(TOOL), "design/OLD-DOC.md", "design/ORCH-NEW-DOC.md",
             "--audience", "orchestrator"],
            cwd=d, capture_output=True, text=True)
        if r.returncode != 0:
            print("GREEN case: rename_doc.py itself failed:\n", r.stdout, r.stderr)
            return False
        referrer = (d / "REFERRER.md").read_text(encoding="utf-8")
        if "design/ORCH-NEW-DOC.md" not in referrer or "design/OLD-DOC.md" in referrer:
            print("GREEN case: REFERRER.md was not correctly relinked:\n", referrer)
            return False
        gate = _run_gate(d)
        if gate.returncode != 0:
            print("GREEN case: link_integrity not clean after a correct rename:\n", gate.stdout)
            return False
        return True
    finally:
        shutil.rmtree(d, ignore_errors=True)


def case_red_missed_reference() -> bool:
    """Simulate a rewrite step that missed one occurrence — the class this tool's own final
    link_integrity.py call exists to catch before anything is committed."""
    d = _mkrepo()
    try:
        r = subprocess.run(
            [sys.executable, str(TOOL), "design/OLD-DOC.md", "design/ORCH-NEW-DOC.md",
             "--audience", "orchestrator"],
            cwd=d, capture_output=True, text=True)
        if r.returncode != 0:
            print("RED case setup: rename_doc.py failed unexpectedly:\n", r.stdout, r.stderr)
            return False
        # Deliberately re-introduce a reference to the now-nonexistent OLD path — the miss.
        (d / "REFERRER.md").write_text(
            "# Referrer\n\nSee [Old Doc](design/OLD-DOC.md) for detail (missed rewrite).\n",
            encoding="utf-8")
        gate = _run_gate(d)
        if gate.returncode == 0:
            print("RED case: link_integrity stayed GREEN despite a missed reference — "
                  "the class this fixture exists to catch is not being caught")
            return False
        if "design/OLD-DOC.md" not in gate.stdout:
            print("RED case: link_integrity failed, but not for the expected broken target:\n",
                  gate.stdout)
            return False
        return True
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main() -> int:
    results = {
        "GREEN (clean rename, corpus relinked, gate clean)": case_green(),
        "RED (deliberately-missed reference caught by link_integrity)": case_red_missed_reference(),
    }
    ok = True
    for name, passed in results.items():
        print(f"{'PASS' if passed else 'FAIL'}: {name}")
        ok = ok and passed
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
