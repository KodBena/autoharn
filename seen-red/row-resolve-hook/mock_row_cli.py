#!/usr/bin/env python3
"""mock_row_cli.py -- fixture stand-in for `./autoharn led show <id>`, for
seen-red/row-resolve-hook. Real infra not used here, disclosed rather than silently
substituted (this worktree carries no deployment.json / served boundary, and the house rule
is read-only ./led anyway -- never a live 8433/8422 service stood up for a fixture). This mock
serves the BYTE-IDENTICAL shapes `bootstrap/templates/led.tmpl`'s own `cmd_show` documents:
found -> `f"{k:28s}: {v}"` per field on stdout, exit 0; unknown row -> "led show: REFUSED --
no row <id>." on stderr plus a one-line pointer, exit 1 (verbatim from cmd_show's own text,
read at this build's own commission time).

Invoked exactly the way the hook invokes the real CLI: `mock_row_cli.py led show <id>` (argv
mirrors `<autoharn> led show <id>` one-for-one, so the hook's own argv-building code is
unchanged between the real CLI and this mock).

MOCK_ROW_SCENARIO env var:
  found     -- row exists; prints two fields, byte-shaped like cmd_show's own output, exit 0.
  not_found -- row does not exist; cmd_show's own REFUSED text verbatim, exit 1.
  slow      -- sleeps MOCK_ROW_SLEEP_S seconds (default 3.0) before answering "found" --
               exercises the hook's own per-call/budget timeout paths deterministically fast,
               without a real multi-second CLI call.
  crash     -- exits 3 with an unrelated stderr line -- a CLI that ran but failed in a way that
               is neither cmd_show's own 404 shape nor a clean 0 -- combined stdout+stderr is
               still shown verbatim, no special-casing.

Lazy imports are banned (CLAUDE.md, 2026-07-02).
"""
from __future__ import annotations

import os
import sys
import time

SCENARIO = os.environ.get("MOCK_ROW_SCENARIO", "found")


def main() -> int:
    argv = sys.argv[1:]  # ["led", "show", "<id>"]
    row_id = argv[2] if len(argv) >= 3 else "?"

    if SCENARIO == "found":
        print(f"{'id':28s}: {row_id}")
        print(f"{'kind':28s}: decision")
        print(f"{'statement':28s}: mock row {row_id} statement text")
        return 0

    if SCENARIO == "not_found":
        print(f"led show: REFUSED -- no row {row_id}.", file=sys.stderr)
        print("  See 'led --recent [N]' or 'led current [N]' for ids that actually exist.",
              file=sys.stderr)
        return 1

    if SCENARIO == "slow":
        sleep_s = float(os.environ.get("MOCK_ROW_SLEEP_S", "3.0"))
        time.sleep(sleep_s)
        print(f"{'id':28s}: {row_id}")
        return 0

    if SCENARIO == "crash":
        print("mock_row_cli: simulated unexpected failure", file=sys.stderr)
        return 3

    print(f"mock_row_cli: unrecognized MOCK_ROW_SCENARIO={SCENARIO!r}", file=sys.stderr)
    return 4


if __name__ == "__main__":
    sys.exit(main())
