#!/usr/bin/env python3
"""Record a recorded-adaptation (BUILD-BRIEF §0).

An adapted migrated file is byte-identical to its source EXCEPT for edits on §0's
closed list. This tool makes each such adaptation auditable: for a dest it
(1) confirms the dest's manifest row authorized adaptation (sanctioned_adapt=1),
(2) writes the unified diff (source-at-commit -> current dest) to
    provenance/adaptations/<flat-dest>.diff, and
(3) flips adapted_now to `yes` in provenance/MIGRATION.tsv.

The source sha256 in MIGRATION.tsv is left untouched — it is the provenance of what
was COPIED. A reader verifies provenance with `git show <commit>:<src> | sha256sum`
and verifies the adaptation is exactly the recorded diff.

Usage: record_adaptation.py <dest_path> [<dest_path> ...]
"""
import difflib
import os
import subprocess
import sys

AUTOHARN = "/home/bork/w/vdc/1/autoharn"
REPOS = {
    "CH": "/home/bork/w/vdc/1/claude_harness",
    "EO": "/home/bork/w/vdc/1/epistemic-operator",
}
RECORD = os.path.join(AUTOHARN, "provenance", "MIGRATION.tsv")
ADAPT_DIR = os.path.join(AUTOHARN, "provenance", "adaptations")


def load_rows() -> list:
    with open(RECORD) as fh:
        return [ln.rstrip("\n") for ln in fh]


def main(argv: list) -> int:
    os.makedirs(ADAPT_DIR, exist_ok=True)
    rows = load_rows()
    header, body = rows[0], rows[1:]
    index = {}
    for i, ln in enumerate(body):
        cols = ln.split("\t")
        index[cols[2]] = (i, cols)  # keyed by dest_path
    for dest in argv[1:]:
        if dest not in index:
            print(f"NOT A MIGRATED DEST: {dest}", file=sys.stderr)
            return 2
        i, cols = index[dest]
        repo, src, _dest, commit, src_sha, sanctioned, _adapted = cols
        if sanctioned != "1":
            print(f"REFUSED: {dest} is not sanctioned-adaptable (closed list, §0)",
                  file=sys.stderr)
            return 3
        source = subprocess.run(
            ["git", "-C", REPOS[repo], "show", f"{commit}:{src}"],
            capture_output=True, check=True,
        ).stdout.decode("utf-8", errors="replace").splitlines(keepends=True)
        with open(os.path.join(AUTOHARN, dest), encoding="utf-8", errors="replace") as fh:
            current = fh.readlines()
        diff = "".join(difflib.unified_diff(
            source, current,
            fromfile=f"{repo}:{src}@{commit[:12]}", tofile=f"autoharn/{dest}"))
        if not diff:
            print(f"WARNING: {dest} has no diff from source — not actually adapted",
                  file=sys.stderr)
            continue
        flat = dest.replace("/", "__") + ".diff"
        with open(os.path.join(ADAPT_DIR, flat), "w") as fh:
            fh.write(diff)
        cols[6] = "yes"
        body[i] = "\t".join(cols)
        print(f"recorded adaptation: {dest} -> adaptations/{flat}")
    with open(RECORD, "w") as fh:
        fh.write("\n".join([header] + body) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
