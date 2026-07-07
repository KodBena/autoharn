#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-07T01:58:44Z
#   last-change: 2026-07-07T01:58:44Z
#   contributors: 37017f46/main
# <<< PROVENANCE-STAMP <<<

"""verify_operator_turns — the standing fixture for delivery_drill's operator-turn extraction
(forecloses finding 25: `_operator_turns` must SKIP harness-injected `<task-notification>` envelopes.
A background-agent completion notification carries an `<output-file>/tmp/…/<id>.output` tag whose
redirection shape trips the F40 splice signature; scanning it falsely FAILS a clean run that used
background agents. The fix skips those envelopes while still scanning real operator-typed turns).

This pins the behavior on a synthetic transcript: a genuine operator splice IS detected, and a
task-notification envelope is NOT. Registered close/lint line id: `operator-turn-extraction`.
Lazy imports banned.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "drive"))   # autoharn: delivery_drill now in drive/
from delivery_drill import _operator_turns, splices  # noqa: E402

# a synthetic transcript: (1) an assistant turn (ignored), (2) a real operator splice `! cat …`,
# (3) a harness-injected task-notification whose output-file tag must NOT trip the signature.
TRANSCRIPT = [
    {"message": {"role": "assistant", "content": "running the build now"}},
    {"message": {"role": "user", "content": "here is the answer: ! cat /tmp/leak/answer.txt"}},
    {"message": {"role": "user", "content":
        "<task-notification>agent 5ffc done <output-file>/tmp/claude/abc.output</output-file></task-notification>"}},
]


def check() -> list[str]:
    bad: list[str] = []
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as fh:
        for rec in TRANSCRIPT:
            fh.write(json.dumps(rec) + "\n")
        path = fh.name
    text = _operator_turns(path)
    Path(path).unlink(missing_ok=True)
    # the task-notification envelope must be excluded from the scanned operator text
    if "task-notification" in text or ".output" in text:
        bad.append("a <task-notification> envelope leaked into the scanned operator text (finding 25)")
    # the real operator splice must survive and be detected
    hits = splices(text)
    if not hits:
        bad.append("the genuine operator splice `! cat /tmp/leak/answer.txt` was NOT detected")
    return bad


def main() -> int:
    bad = check()
    for b in bad:
        print(f"OPERATOR-TURN EXTRACTION WRONG: {b}")
    if bad:
        print(f"# operator-turn-extraction FAIL — {len(bad)} defect(s) (a task-notification scanned as "
              f"operator input, or a real splice missed).")
        return 1
    print("# operator-turn-extraction PASS — task-notification envelopes skipped; real operator "
          "splices still detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
