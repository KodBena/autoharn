#!/usr/bin/env python3
"""
enumerate_writers.py — independently list who writes a given state symbol.

The documented failures were failures to GENERALIZE across producers: a
per-writer gate added when N writers existed and only some were enumerated
(the slot had three writers; the fix assumed two). The fix inherited the
implementer's count. This script refuses that — it re-derives candidate
write-sites from the source so the count comes from the CODE, not from memory.

It is grep with assignment-aware patterns, NOT a type-checker. It will
over-include (a name used as a local) and under-include (writes through an
alias or a mutator it doesn't recognize). That is fine: read the hits, don't
just count them. Its job is to make you compare an independently-derived writer
set against the one the change assumed, and notice a mismatch — the missed
producer is where the bug survives.

Usage:
    python enumerate_writers.py <symbol> <source-root> [--ext .ts,.tsx,.vue,.js]

<symbol> is the field/slot/state name written to, e.g. cardTree, selection,
store.boards. Use the leaf name for broad nets, the dotted path for precision.

Prints write-sites grouped by file, then a tally and the comparison prompt.
"""

import os
import re
import sys

DEFAULT_EXTS = [".ts", ".tsx", ".vue", ".js", ".jsx", ".mjs", ".py"]

SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "coverage",
             "__pycache__", ".venv", "venv"}


def write_patterns(symbol):
    """Patterns that indicate a WRITE to `symbol` (not merely a read)."""
    s = re.escape(symbol)
    leaf = re.escape(symbol.split(".")[-1])
    pats = [
        # direct assignment:  symbol = ... / a.symbol = ... / symbol.x = ...
        (rf"(?<![=!<>])\b{s}\b\s*=(?!=)", "assign"),
        (rf"\.{leaf}\b\s*=(?!=)", "prop-assign"),
        # compound assignment: symbol += , symbol ||= , symbol ??=
        (rf"\b{leaf}\b\s*(?:\+|\-|\*|\|\||\?\?|&&)=", "compound-assign"),
        # object-literal key write:  symbol: <value>   (e.g. in a patch object)
        (rf"\b{leaf}\b\s*:\s*[^,\n}}]", "object-key"),
        # mutator conventions common in this codebase / Vue / stores
        (rf"\b(?:set|mutate|update|seed|load|populate|clear|reset|stamp)"
         rf"[A-Za-z]*\([^)]*\b{leaf}\b", "mutator-call"),
        (rf"\.value\b\s*=(?!=).*\b{leaf}\b", "ref-write"),
        # Vue reactive set / $set / Object.assign onto symbol
        (rf"Object\.assign\(\s*[^,]*\b{leaf}\b", "object-assign"),
    ]
    return [(re.compile(p), kind) for p, kind in pats]


def iter_files(root, exts):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if any(fn.endswith(e) for e in exts):
                yield os.path.join(dirpath, fn)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = [a for a in sys.argv[1:] if a.startswith("--")]
    if len(args) != 2:
        print(__doc__)
        sys.exit(2)
    symbol, root = args
    exts = DEFAULT_EXTS
    for o in opts:
        if o.startswith("--ext"):
            exts = [e if e.startswith(".") else "." + e
                    for e in o.split("=", 1)[-1].split(",")]

    pats = write_patterns(symbol)
    by_file = {}
    total = 0
    for path in iter_files(root, exts):
        try:
            lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
        except OSError:
            continue
        for n, line in enumerate(lines, 1):
            for rx, kind in pats:
                if rx.search(line):
                    by_file.setdefault(path, []).append((n, kind, line.strip()))
                    total += 1
                    break  # one hit per line is enough

    print("=" * 72)
    print(f"enumerate_writers: symbol='{symbol}'  root='{root}'")
    print("=" * 72)
    if not by_file:
        print("No candidate write-sites found. Check the symbol name (try the")
        print("leaf name alone), the --ext list, and the root path. Absence here")
        print("is itself a finding: if the change claims to gate writers to this")
        print("symbol but none are visible, the change may be touching the wrong")
        print("seam.")
    else:
        files = sorted(by_file)
        for path in files:
            print(f"\n{path}")
            for (n, kind, src) in by_file[path]:
                src = (src[:100] + "…") if len(src) > 100 else src
                print(f"  {n:>5}  [{kind}]  {src}")
        print("\n" + "-" * 72)
        print(f"{total} candidate write-site(s) across {len(files)} file(s).")

    print("-" * 72)
    print("COMPARE THIS against the writers the change assumed.")
    print("  • More sites here than the change handled?  -> a producer was missed;")
    print("    a per-writer fix leaves the bug alive at the missed site.")
    print("  • Multiple writers + a per-writer gate (not one invariant over all)?")
    print("    -> UNDISCHARGED-HACK signal even if every KNOWN writer is handled,")
    print("    because the next writer added reopens it.")
    print("Grep over/under-includes — read the hits, then fill the WRITER DELTA line.")


if __name__ == "__main__":
    main()
