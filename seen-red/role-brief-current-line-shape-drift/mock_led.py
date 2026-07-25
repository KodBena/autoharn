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

Four scenarios, MOCK_LED_SCENARIO env var:
  corrupt      -- role 's45' is registered (row 1); row 7 is `principal_suspended` naming 's45',
                  but row 7's OWN `current` line is corrupted -- rewritten with no leading
                  `[id] kind: ` shape at all (a truncated/garbled write). This is the reviewer's
                  own named consequence, reproduced directly.
  clean        -- the same row 7, NOT corrupted -- the fixed parser's ordinary path, confirming
                  the fix didn't disturb the legitimate SUSPENDED render (and that it still
                  renders at the TOP of the brief, since build_standing_section runs first in
                  cmd_brief).
  show_corrupt -- re-lap review addendum (branch tip cc12b46, parse_served_show finding): row 1
                  and row 7 are clean; a THIRD row, [2] decision (role 's45' handles onboarding
                  queue triage), is added to `current`, and its OWN `led show 2` output carries
                  an 'actor' field ONE COLUMN NARROWER than cmd_show's real `f"{k:28s}: {v}"`
                  shape -- a wire-level width drift, not a hypothetical: cmd_show's format-spec
                  width is a MINIMUM, so any transport-layer byte drop that clips one padding
                  space produces exactly this. Pre-fix (cc12b46, before this addendum's own fix):
                  parse_served_show silently drops the 'actor' line, _actor_id_from_show reads
                  it as "no actor column at all" (None), the row fails the actor-id match, and
                  IN-FORCE DECISIONS renders WITHOUT row 2 -- an emptier-but-exit-0 brief, exactly
                  the silent-drop class this branch's earlier fixes killed in parse_current_line,
                  now caught in parse_served_show too.
  show_clean   -- the same row 2, actor field at the correct width -- confirms the fix does not
                  disturb the legitimate path: row 2 renders in IN-FORCE DECISIONS.
"""
import os
import sys

SCENARIO = os.environ.get("MOCK_LED_SCENARIO", "clean")

REG_LINE = "[1] principal_registered: principal 's45' registered (class subagent)"
SUSPEND_LINE_CLEAN = "[7] principal_suspended: principal 's45' suspended (reason: scratch fixture)"
SUSPEND_LINE_CORRUPT = "s45 suspended (reason: scratch fixture) -- TRUNCATED ROW, MISSING [id] kind: PREFIX"
DECISION_LINE = "[2] decision: role 's45' handles onboarding queue triage"

# cmd_show's own `f"{k:28s}: {v}"` shape for key 'actor': correctly padded to 28 columns is
# "actor" + 23 spaces + ": " + value. The drifted line drops ONE of those padding spaces (27
# columns, not 28) -- a plausible wire-level truncation, not a fabricated shape.
_ACTOR_LINE_CORRECT = "actor" + " " * 23 + ": 42\n"
_ACTOR_LINE_DRIFT = "actor" + " " * 22 + ": 42\n"

SHOW_ROWS = {
    "1": "id                          : 1\n"
         "kind                        : principal_registered\n"
         "statement                   : principal 's45' registered (class subagent)\n"
         "principal_subject           : 42\n",
    "7": "id                          : 7\n"
         "kind                        : principal_suspended\n"
         "statement                   : principal 's45' suspended (reason: scratch fixture)\n"
         "actor                       : 1\n",
    "2": ("id                          : 2\n"
          "kind                        : decision\n"
          "statement                   : role 's45' handles onboarding queue triage\n"
          + (_ACTOR_LINE_DRIFT if SCENARIO == "show_corrupt" else _ACTOR_LINE_CORRECT)),
}


def main(argv):
    if argv[:1] == ["current"]:
        print(REG_LINE)
        print(SUSPEND_LINE_CORRUPT if SCENARIO == "corrupt" else SUSPEND_LINE_CLEAN)
        if SCENARIO in ("show_corrupt", "show_clean"):
            print(DECISION_LINE)
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
