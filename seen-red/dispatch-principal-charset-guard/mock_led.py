#!/usr/bin/env python3
"""mock_led.py -- fixture `led` for seen-red/dispatch-principal-charset-guard.

Serves exactly the `current <N>` shape tools/dispatch_principal.py's own
`principal_is_registered` reads (served_shapes.parse_current_line: `[id] kind: statement`,
bootstrap/templates/led.tmpl's own `cmd_recent`) -- nothing else this fixture needs is invoked
through `led`, so every other subcommand is a harmless no-op.

MOCK_LED_SCENARIO env var selects what `current <N>` reports as registered:
  hostile-registered -- a `principal_registered` event for the literal shell-hostile name this
                         fixture's own R1/R2 pair uses (`builder$(touch PWNED)`), so the PRE-FIX
                         code's `principal_is_registered` check (which runs BEFORE any charset
                         test existed) finds it registered and reaches its own vulnerable
                         `print(f"export LED_ACTOR={name}")` line -- reproducing the exact
                         pre-fix vulnerability this fixture's R1 pins.
  clean-registered    -- a `principal_registered` event for an ordinary, charset-clean name
                         (`builder-ok`), the GREEN path both pre-fix and post-fix code handle
                         identically -- confirms the fix does not disturb a legitimate dispatch.
  empty               -- no `principal_registered` events at all (NOT-REGISTERED path).

This mock never writes anything; `register-principal`/any other subcommand just exits 0 doing
nothing, since no case in this fixture exercises them.
"""
from __future__ import annotations

import os
import sys

HOSTILE_NAME = "builder$(touch PWNED)"
CLEAN_NAME = "builder-ok"


def main(argv: list[str]) -> int:
    scenario = os.environ.get("MOCK_LED_SCENARIO", "empty")
    if argv[:1] == ["current"]:
        if scenario == "hostile-registered":
            print(f"[3] principal_registered: principal '{HOSTILE_NAME}' registered as subagent")
        elif scenario == "clean-registered":
            print(f"[3] principal_registered: principal '{CLEAN_NAME}' registered as subagent")
        elif scenario == "empty":
            pass
        else:
            print(f"mock_led: unknown MOCK_LED_SCENARIO {scenario!r}", file=sys.stderr)
            return 2
        return 0
    # every other subcommand: harmless no-op, nothing in this fixture calls it.
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
