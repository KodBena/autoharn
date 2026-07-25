#!/usr/bin/env python3
"""mock_led.py -- fixture `led` for seen-red/role-charter-current-line-shape-drift.

tools/role_charter.py's OWN parse_current_line carried the identical silent-misparse shape
tools/role_brief.py's 417b200 fix round killed (row 1295, flagged by that fix's own commit as
out of its scope): returned None on a non-matching non-blank `led current` line, and BOTH call
sites (find_current_registrations, principal_is_registered) silently `continue`d past it.

CONSEQUENCE HERE, role_charter's own shape of the same defect (distinct from role_brief's
SUSPENDED->ACTIVE flip, since role_charter carries no standing/suspension concept): a corrupted
`current` line sitting where a role's real in-force charter-registration `decision` row belongs
made that registration invisible to `find_current_registrations` -- so `cmd_register` believed
NO registration existed and silently wrote a SECOND, conflicting registration event with exit
0, bypassing this tool's own JC4 double-registration refusal (its stated invariant: "register on
a role that already carries an in-force registration is REFUSED, teaching amend instead").

REAL INFRA NOT USED HERE, disclosed rather than silently substituted -- same blocker as
seen-red/role-brief-current-line-shape-drift/mock_led.py's own note: no pgcrypto, no root/
package-manager access in this sandbox (confirmed by standing up a throwaway local Postgres
cluster and hitting `CREATE EXTENSION pgcrypto: extension is not available`). This mock serves
the BYTE-IDENTICAL served shapes tools/role_charter.py's own header documents (`led current <N>`:
`[id] kind: statement`; `led show <id>`: `f"{k:28s}: {v}"` per non-null field; `led decision ...`:
`led: row <id> written.` on success, serving/boundary_cli_client.py's own write_and_report()
convention) so the parser under test sees exactly what a real served `led` would print.

Two scenarios, MOCK_LED_SCENARIO env var:
  corrupt -- role 'editor' is registered as a principal (row 1); row 7 is the role's real
             in-force charter-registration `decision`, but row 7's OWN `current` line is
             corrupted -- rewritten with no leading `[id] kind: ` shape at all.
  clean   -- the same row 7, NOT corrupted -- the fixed parser's ordinary path, confirming the
             fix still lets `register` see the existing row and correctly REFUSE (JC4),
             undisturbed by the fix.
"""
import os
import sys

SCENARIO = os.environ.get("MOCK_LED_SCENARIO", "clean")

REG_LINE = "[1] principal_registered: principal 'editor' registered (class human)"
CHARTER_LINE_CLEAN = ("[7] decision: role-charter registered: role=editor "
                       "path=roles/editor/CHARTER.md sha256=" + "a" * 64)
CHARTER_LINE_CORRUPT = ("role-charter role=editor path=roles/editor/CHARTER.md sha256=" +
                         "a" * 64 + " -- TRUNCATED ROW, MISSING [id] kind: PREFIX")

SHOW_ROWS = {
    "1": "id                          : 1\n"
         "kind                        : principal_registered\n"
         "statement                   : principal 'editor' registered (class human)\n",
    "7": "id                          : 7\n"
         "kind                        : decision\n"
         "statement                   : role-charter registered: role=editor "
         "path=roles/editor/CHARTER.md sha256=" + "a" * 64 + "\n"
         "actor                       : 1\n",
}


def main(argv):
    if argv[:1] == ["current"]:
        print(REG_LINE)
        print(CHARTER_LINE_CORRUPT if SCENARIO == "corrupt" else CHARTER_LINE_CLEAN)
        return 0
    if argv[:1] == ["show"] and len(argv) == 2 and argv[1] in SHOW_ROWS:
        print(SHOW_ROWS[argv[1]], end="")
        return 0
    if argv[:1] == ["decision"]:
        print("led: row 9 written.")
        return 0
    print(f"mock_led: unhandled args {argv}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
