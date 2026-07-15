#!/usr/bin/env python3
"""delivery_drill — the F40 delivery-touchpoint drill (consult 17 §1.4 item 3, launch-packet §4).

Two modes:

  (default) SIMULATE: drive the repaired delivery protocol (launch-packet-template §2) against a
  MOCK subject-session channel, exercising the REAL tmux buffer mechanism the operator uses
  (load-buffer -> show-buffer|sha256 -> paste-buffer), and assert the channel received ONLY the
  ruling bytes (byte-exact) with ZERO command splices. This proves the delivery MECHANISM is
  splice-free BY CONSTRUCTION: the bytes reach the subject via a tmux bracketed paste, so the
  operator's only in-session act is a paste event; there is no code path in which a `cat`/`!`/bash
  reaches the session. tmux needs no display, so the buffer round-trip is exercised for real; the
  subject PANE is modeled (a live pane would need an interactive TUI), and paste-buffer's payload is
  captured from `show-buffer` — the exact bytes tmux would deliver. If tmux is unavailable the drill
  falls back to a file transport with the same assertions (the property under test — the
  operator->session channel carries no command — is preserved either way).

  --check <transcript>: the SPLICE CHECK the launch-packet §4 gate runs on a real throwaway-session
  transcript — scan the operator-authored turns for any command splice (`<bash-input>`, a leading
  `!`, `cat `, a redirection). ZERO splices passes; any splice FAILS (the F40 signature: the e12
  operator ran `! cat <repo>/ruling.text` inside the session).

The LIVE human rehearsal on a real interactive Claude Code session is an e14 launch prerequisite
(it needs a TUI + a human operator); this drill proves the mechanism and provides the gate's checker.
Read-only except the transcript artifact it writes. NEVER touches an exhibit dir or a session.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

# the F40 splice signature — any of these in an OPERATOR turn is a blind breach.
SPLICE_RES = [
    re.compile(r"<bash-input>", re.IGNORECASE),   # a bash tool-call rendered in the transcript
    re.compile(r"^\s*!"),                          # a `!`-shell escape as the message
    re.compile(r"\bcat\s+\S"),                     # cat <path>
    re.compile(r"[<>]\s*\S+\.\w+"),                # a redirection into/out of a file
    re.compile(r"\b(psql|bash|sh|python3?)\b\s"),  # a bare command invocation
]


def splices(text: str) -> list[str]:
    hits = []
    for line in text.splitlines():
        for r in SPLICE_RES:
            if r.search(line):
                hits.append(line.strip())
                break
    return hits


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def simulate() -> int:
    """Drive T1-T4 against a mock session channel; assert byte-exact, splice-free delivery."""
    tmp = tempfile.mkdtemp(prefix="e14-delivery-drill-")
    ruling = os.path.join(tmp, "ruling.text")
    ruling_bytes = (b"On the question you raised: read the spec's requirement as written. "
                    b"Please revise the pilot to conform.\n")  # a stand-in; the real run pins its own
    open(ruling, "wb").write(ruling_bytes)
    reg_sha = _sha(ruling_bytes)

    # ENGINEER STEP (§2), in a SEPARATE pane — the REAL tmux buffer path when tmux is present:
    #   tmux load-buffer -b <name> <file>   (byte-exact, no shell interpolation)
    #   tmux show-buffer -b <name> | sha256 (verify the BUFFER vs the pre-registration)
    # paste_bytes is what `paste-buffer -p` would deliver — captured from show-buffer.
    buf = "e14-delivery-drill"
    mechanism = "file-fallback"
    paste_bytes = ruling_bytes
    if shutil.which("tmux"):
        try:
            subprocess.run(["tmux", "load-buffer", "-b", buf, ruling], check=True,
                           capture_output=True)
            show = subprocess.run(["tmux", "show-buffer", "-b", buf], check=True,
                                  capture_output=True)
            paste_bytes = show.stdout
            subprocess.run(["tmux", "delete-buffer", "-b", buf], capture_output=True)
            mechanism = "tmux-buffer"
        except Exception:  # noqa: BLE001
            paste_bytes = ruling_bytes
    clip_ok = _sha(paste_bytes) == reg_sha  # the BUFFER (what paste delivers) matches the registration

    # THE SUBJECT-SESSION CHANNEL — everything the subject receives. The operator writes to it ONLY
    # via paste (T2/T4 = clipboard bytes) and typed control (T3 = "continue"). There is NO code path
    # that runs a command in the session: the operator never holds the path or a shell.
    channel: list[tuple[str, str]] = []  # (turn_kind, payload)

    def T2_paste():   # deliver the ruling: tmux paste-buffer -p delivers the buffer bytes as a paste
        channel.append(("operator-message", paste_bytes.decode()))

    def T3_continue():
        channel.append(("operator-message", "continue"))

    T2_paste()
    T3_continue()

    # ASSERT: the first operator message equals the pre-registered bytes, byte-exact.
    delivered = channel[0][1].encode()
    byte_exact = _sha(delivered) == reg_sha
    # ASSERT: no operator turn carries a command splice.
    all_splices = [s for _, p in channel for s in splices(p)]

    transcript = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "delivery-drill-transcript.txt")
    with open(transcript, "w") as f:
        f.write("# e14 delivery drill transcript (SIMULATED — mechanism proof; F40 repair)\n")
        f.write(f"# delivery mechanism exercised: {mechanism}\n")
        f.write(f"# ruling.text sha256 (pre-registered analogue): {reg_sha}\n")
        f.write(f"# engineer buffer-load + show-buffer|sha256 (§2, OUTSIDE any session): "
                f"BUFFER-MATCHES-REGISTRATION={clip_ok}\n\n")
        f.write("## subject-session channel (everything the subject received):\n")
        for i, (k, p) in enumerate(channel, 1):
            f.write(f"  turn {i} [{k}]: {p!r}\n")
        f.write(f"\n## delivery byte-exact vs pre-registered: {byte_exact} "
                f"(received sha256 {_sha(delivered)})\n")
        f.write(f"## command splices in operator turns: {len(all_splices)} {all_splices}\n")
        f.write("\n## NOTE: this proves the MECHANISM (clipboard->paste carries no in-session "
                "command). The LIVE human rehearsal on a real throwaway Claude Code session is an "
                "e14 launch prerequisite (interactive TUI + human operator), flagged in the build "
                "consult — not dischargeable from the build.\n")

    ok = clip_ok and byte_exact and not all_splices
    print(f"# delivery drill (SIMULATE, mechanism={mechanism}): buffer_matches_registration={clip_ok} "
          f"byte_exact={byte_exact} splices={len(all_splices)} -> {'PASS' if ok else 'FAIL'}")
    print(f"# transcript filed: {transcript}")
    # self-check the checker: a KNOWN-BAD transcript (the F40 splice) must be caught.
    bad = "operator-message: ! cat /home/.../harness/e12-build/ruling.text"
    caught = bool(splices(bad))
    print(f"# checker self-test on the F40 splice line -> {'CAUGHT' if caught else 'MISSED (BUG)'}")
    return 0 if (ok and caught) else 1


def _operator_turns(path: str) -> str:
    """Extract ONLY operator-authored (user-role) turn text from a Claude Code JSONL transcript.

    The F40 signature is an operator splice (`! cat`, a fetched path) in an OPERATOR turn.
    The SUBJECT's own Bash/psql tool calls are assistant turns and MUST NOT be scanned — the
    subject runs commands constantly, so scanning them would fail every real run (the bug this
    fixes). A non-JSONL transcript falls back to whole-text (best effort)."""
    out, any_json = [], False
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        any_json = True
        msg = rec.get("message") or {}
        if msg.get("role") != "user":
            continue  # assistant turns (incl. the subject's own tool_use) are not operator input

        def _op_text(s: str) -> None:
            # skip HARNESS-INJECTED user-role content: a <task-notification> envelope (background-agent
            # completion) is system-injected, never an operator paste — its <output-file>/tmp/…/<id>.output
            # tag would otherwise trip the redirection signature and falsely FAIL a clean run that used
            # background agents (finding 25). Real operator-typed delivery splices are unaffected.
            if "<task-notification>" in s:
                return
            out.append(s)

        content = msg.get("content")
        if isinstance(content, str):
            _op_text(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    _op_text(part["text"])
    if not any_json:
        return open(path, encoding="utf-8", errors="replace").read()
    return "\n".join(out)


def check(path: str) -> int:
    text = _operator_turns(path)
    hits = splices(text)
    print(f"# delivery splice check on {path}: {len(hits)} splice(s)")
    for h in hits:
        print(f"  SPLICE: {h}")
    print("# " + ("PASS (splice-free)" if not hits else "FAIL (blind breach — a splice reached the session)"))
    return 0 if not hits else 1


def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == "--check":
        return check(sys.argv[2])
    return simulate()


if __name__ == "__main__":
    sys.exit(main())
