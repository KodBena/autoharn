#!/usr/bin/env python3
"""verify_gate_journal_registered — the arm-time gate-journal registration check (forecloses finding 42,
consult 35 (e): the e17 gate-journal was never registered, so `contemporaneity` silently read N/A at
close — a MANDATORY close line rendered inapplicable because an arming step was skipped, and no mechanism
caught it). The arming-checklist line 'contemporaneity registration' was prose; this makes it a check.

THE RULE. Before a target is armed, it MUST be registered in contemporaneity's two registries — `SESSIONS`
(relation + audit-session id) AND `GATE_JOURNALS` (journal + label) — so contemporaneity RUNS on it at
close rather than degrading to N/A. A target missing from either is REFUSED (exit 1), loudly naming which.

Registered close/lint line id: `gate-journal-registered`. Lazy imports banned.

  verify_gate_journal_registered.py <target>      # exit 1 if the target is not registered for contemporaneity
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contemporaneity import GATE_JOURNALS, SESSIONS  # noqa: E402


def missing(target: str) -> list[str]:
    """Which registries the target is absent from (empty = fully registered)."""
    gaps = []
    if target not in SESSIONS:
        gaps.append("contemporaneity.SESSIONS (relation + audit-session id)")
    if target not in GATE_JOURNALS:
        gaps.append("contemporaneity.GATE_JOURNALS (journal path + label)")
    return gaps


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("usage: verify_gate_journal_registered.py <target>", file=sys.stderr)
        return 2
    target = args[0]
    gaps = missing(target)
    if gaps:
        print(f"GATE-JOURNAL UNREGISTERED: target '{target}' is absent from: {gaps}")
        print(f"# gate-journal-registered FAIL — arming '{target}' would leave contemporaneity N/A at close "
              f"(finding 42). Register it in contemporaneity's SESSIONS + GATE_JOURNALS before arming.")
        return 1
    print(f"# gate-journal-registered PASS — '{target}' is registered in contemporaneity SESSIONS + "
          f"GATE_JOURNALS; contemporaneity will run at close, not N/A.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
