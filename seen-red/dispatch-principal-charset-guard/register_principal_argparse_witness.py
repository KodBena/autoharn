#!/usr/bin/env python3
"""register_principal_argparse_witness.py -- isolates ONLY `led register-principal`'s own
argument-parsing step (`bootstrap/templates/led.tmpl`, the `if argv and argv[0] ==
'register-principal':` branch, byte-identical `argparse.ArgumentParser` setup and `try/except
SystemExit` shape reproduced here verbatim) so this fixture can witness whether a taught
`led register-principal <name> <class> [--purpose "..."]` command PARSES, without needing a
live served backend (`cmd_register_principal` -- the kernel write past this parse step -- is
never reached by this witness; it is out of scope for what's under test here, which is only
"does the taught command line even get past argument parsing").

Used by run_fixtures.py's R6 (moderate finding, confirming review round): a leading-hyphen
principal name (`-foo`) is charset-legal under the PRE-FIX pattern, so pre-fix `cmd_preamble`
taught `led register-principal -foo subagent --purpose "..."` as the remediation for an
unregistered name -- but that exact command line fails this identical argparse shape, because
argparse treats a leading-`-` positional as an unrecognized option. This script reproduces
`led`'s own exit code for that failure (4, `bootstrap/templates/led.tmpl`'s own
`return 4` on `except SystemExit`) so the fixture's RED witness is the SAME failure mode a
caller pasting the taught command into a real `./led` would actually hit, not a re-derivation.

Usage: python3 register_principal_argparse_witness.py <name> <agent_class> [--purpose PURPOSE]
Exit 0 if the arguments parse (mirrors led.tmpl's own success path, no kernel write attempted);
4 if they do not (mirrors led.tmpl's own `return 4`). Lazy imports banned; stdlib only.
"""
from __future__ import annotations

import argparse
import sys


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="led register-principal", add_help=False)
    p.add_argument("name")
    p.add_argument("agent_class")
    p.add_argument("--purpose", default=None)
    try:
        p.parse_args(argv)
    except SystemExit:
        print("usage: led register-principal <name> <class> [--purpose \"<why>\"]", file=sys.stderr)
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
