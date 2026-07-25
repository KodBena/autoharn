#!/usr/bin/env python3
"""corrupt_led_proxy.py -- a real-`led`-backed proxy used ONLY by run_fixtures_real.py's
corrupted-current-line leg. Forwards every argv to the REAL served `led` shim named by the
REAL_LED env var, byte-identical, EXCEPT: on a `current <N>` call, one line -- the one
containing the substring named by CORRUPT_MATCH -- is rewritten to strip its `[id] kind: `
prefix (the exact TRUNCATED-ROW shape seen-red/role-brief-current-line-shape-drift/mock_led.py's
own `corrupt` scenario already uses), simulating a corrupted row on top of a REAL served ledger
line, rather than fabricating the whole `current` output as the mock does. Every other served
command (`show`, etc.) passes through untouched -- this proxy corrupts exactly one line of one
command, nothing else about the real substrate is altered.

Why a proxy rather than tampering the real row in the database: `current`'s served text is
derived server-side from real columns; there is no `led` write path that produces a
`[id] kind: statement` line missing its own `[id] kind: ` prefix (that shape can only arise from
a genuinely garbled write, s52-worthy corruption, or a wire-level truncation) -- the same
reasoning seen-red/s51-artifact-store/run_fixtures.py's own WA6 corruption drill uses when it
tampers stored bytes directly to test a real refusal path against real infra.
"""
import os
import subprocess
import sys

REAL_LED = os.environ["REAL_LED"]
CORRUPT_MATCH = os.environ["CORRUPT_MATCH"]


def main(argv: list[str]) -> int:
    proc = subprocess.run([REAL_LED] + argv, capture_output=True, text=True)
    if argv[:1] != ["current"]:
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        return proc.returncode
    out_lines = []
    for line in proc.stdout.splitlines():
        if CORRUPT_MATCH in line:
            # Strip the leading `[id] kind: ` shape entirely -- the exact corruption shape this
            # family's mock fixture uses, now applied to a REAL served line.
            parts = line.split(": ", 1)
            rest = parts[1] if len(parts) == 2 else line
            out_lines.append(rest + " -- TRUNCATED ROW, MISSING [id] kind: PREFIX")
        else:
            out_lines.append(line)
    sys.stdout.write("\n".join(out_lines) + ("\n" if proc.stdout.endswith("\n") else ""))
    sys.stderr.write(proc.stderr)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
