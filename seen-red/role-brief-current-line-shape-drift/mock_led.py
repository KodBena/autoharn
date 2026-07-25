#!/usr/bin/env python3
"""mock_led.py -- fixture `led` for seen-red/role-brief-current-line-shape-drift.

tools/role_brief.py's fix round (commit a2750f6 fresh-context review, BLOCKS MERGE, SEVERE):
parse_current_line returned None on a non-matching non-blank `led current` line, and all three
call sites silently `continue`d past it -- a corrupted or reshaped line simply vanished from
every section that scans `current`, INCLUDING build_standing_section, so a corrupted line
sitting where a real SUSPENDED row belongs could flip a suspended role's brief to render ACTIVE
with exit 0 (the F49 silent vacuous-pass class this rewrite exists to kill).

REAL INFRA NOT USED HERE, disclosed rather than silently substituted: the house convention for
a seen-red fixture (see seen-red/led-garbage-statement-guard/run_fixtures.py) drives a real
boundary_service + a real scratch schema pair. This sandbox cannot: the pgcrypto extension
(kernel/lineage/s17-stamp-mechanism.sql's own dependency, required before the s40-s57 chain that
reaches s45 standing-lifecycle can even apply) is not installed on this machine, and there is no
root/package-manager access to install it (verified: no apt/dnf/yum, sudo -n refuses). A fresh
local scratch Postgres cluster (initdb, non-default port, non-default socket dir, torn down
after) was stood up and reached exactly this wall -- `CREATE EXTENSION pgcrypto` errors
"extension is not available" -- confirmed blocked, not merely assumed. This mock serves the
BYTE-IDENTICAL served shapes tools/role_brief.py's own header documents (`led current <N>`:
`[id] kind: statement`; `led show <id>`: `f"{k:28s}: {v}"` per non-null field) so the parser
under test sees exactly what a real served `led` would print for this scenario; the kernel/DB
layer itself is not exercised. Flagged, not hidden -- see this fixture's own README note in
run_fixtures.py's docstring.

Two scenarios, MOCK_LED_SCENARIO env var:
  corrupt -- role 's45' is registered (row 1); row 7 is `principal_suspended` naming 's45', but
             row 7's OWN `current` line is corrupted -- rewritten with no leading `[id] kind: `
             shape at all (a truncated/garbled write). This is the reviewer's own named
             consequence, reproduced directly.
  clean   -- the same row 7, NOT corrupted -- the fixed parser's ordinary path, confirming the
             fix didn't disturb the legitimate SUSPENDED render (and that it still renders at
             the TOP of the brief, since build_standing_section runs first in cmd_brief).
"""
import os
import sys

SCENARIO = os.environ.get("MOCK_LED_SCENARIO", "clean")

REG_LINE = "[1] principal_registered: principal 's45' registered (class subagent)"
SUSPEND_LINE_CLEAN = "[7] principal_suspended: principal 's45' suspended (reason: scratch fixture)"
SUSPEND_LINE_CORRUPT = "s45 suspended (reason: scratch fixture) -- TRUNCATED ROW, MISSING [id] kind: PREFIX"

SHOW_ROWS = {
    "1": "id                          : 1\n"
         "kind                        : principal_registered\n"
         "statement                   : principal 's45' registered (class subagent)\n"
         "principal_subject           : 42\n",
    "7": "id                          : 7\n"
         "kind                        : principal_suspended\n"
         "statement                   : principal 's45' suspended (reason: scratch fixture)\n"
         "actor                       : 1\n",
}


def main(argv):
    if argv[:1] == ["current"]:
        print(REG_LINE)
        print(SUSPEND_LINE_CORRUPT if SCENARIO == "corrupt" else SUSPEND_LINE_CLEAN)
        return 0
    if argv[:1] == ["show"] and len(argv) == 2 and argv[1] in SHOW_ROWS:
        print(SHOW_ROWS[argv[1]], end="")
        return 0
    # review-gap / work review-gap / question-status / work startable: no rows -- served as
    # empty output (a valid, empty JSON-lines section per role_brief.py's own parse_json_lines).
    if argv[:1] in (["review-gap"], ["question-status"]) or argv[:2] in (["work", "review-gap"], ["work", "startable"]):
        return 0
    print(f"mock_led: unhandled args {argv}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
