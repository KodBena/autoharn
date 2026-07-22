#!/usr/bin/env python3
"""Seen-red specimen for the operator-turn-extraction gate (forecloses finding 25). Reproduces the
pre-fix _operator_turns: it scanned ALL user-role turns, including harness-injected
`<task-notification>` envelopes. A background-agent completion carries an
`<output-file>/tmp/…/<id>.output</output-file>` tag whose redirection shape trips the F40 splice
signature — falsely FAILING a clean run that used background agents. The naive extractor below omits
the skip; splices() then fires on the notification's output-file tag. Banked as red.txt."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path("/home/bork/w/vdc/1/epistemic-operator/harness/e14-build")))
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "experiments" / "fact-mining"))
from delivery_drill import splices  # noqa: E402

from verify_operator_turns import TRANSCRIPT  # noqa: E402


def _naive_operator_turns(path: str) -> str:
    """The finding-25 defect: every user-role turn is scanned, task-notifications included."""
    out = []
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        msg = rec.get("message") or {}
        if msg.get("role") == "user" and isinstance(msg.get("content"), str):
            out.append(msg["content"])   # NO task-notification skip
    return "\n".join(out)


def main() -> int:
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as fh:
        for rec in TRANSCRIPT:
            fh.write(json.dumps(rec) + "\n")
        path = fh.name
    text = _naive_operator_turns(path)
    Path(path).unlink(missing_ok=True)
    hits = splices(text)
    notif_hits = [h for h in hits if ".output" in h or "output-file" in h]
    if not notif_hits:
        print(f"SPECIMEN INERT — the task-notification tag did not trip the splice signature "
              f"(all hits: {hits}).")
        return 1
    print(f"# operator-turn-extraction FAIL — a harness-injected <task-notification> tripped the "
          f"F40 splice signature ({len(notif_hits)} false hit(s)): {notif_hits}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
