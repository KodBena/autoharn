#!/usr/bin/env python3
"""Migration copy tool (BUILD-BRIEF §3).

For each row of provenance/migration_manifest.tsv it resolves the source at the
recorded source commit via `git show <commit>:<path>` (pinning provenance to the
tracked bytes, immune to any dirty/untracked working state), writes it to the
destination inside autoharn, computes the source sha256, and appends a row to
provenance/MIGRATION.tsv:

    source_repo  source_path  dest_path  source_commit  source_sha256  sanctioned_adapt  adapted_now

`adapted_now` is written `no` at copy time; the adaptation pass flips it to `yes`
for a dest it actually edits (and records the diff under provenance/adaptations/).
`sanctioned_adapt` is the manifest's closed-list authorization (1 = this dest MAY
be adapted per BUILD-BRIEF §0's recorded-adaptation rule); a dest with 0 must stay
byte-identical to source.

A copy whose (source_repo, source_path, dest_path) is NOT a manifest row is
REFUSED (both polarities proven by tools' self-test). Source repos are never
written — this tool only reads them (via git) and writes into autoharn.
"""
import hashlib
import os
import subprocess
import sys

AUTOHARN = "/home/bork/w/vdc/1/autoharn"
REPOS = {
    "CH": ("/home/bork/w/vdc/1/claude_harness",
           "87e1bcc3e03bdc3fed1924219c8e181dcf8646e7"),
    "EO": ("/home/bork/w/vdc/1/epistemic-operator",
           "e34759885879a4bcb7878bef6d08eb400885c155"),
}
MANIFEST = os.path.join(AUTOHARN, "provenance", "migration_manifest.tsv")
RECORD = os.path.join(AUTOHARN, "provenance", "MIGRATION.tsv")


def load_manifest() -> dict:
    rows = {}
    with open(MANIFEST) as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                continue
            repo, src, dest, sanctioned = line.split("\t")
            rows[(repo, src, dest)] = int(sanctioned)
    return rows


def git_show(repo_path: str, commit: str, src: str) -> bytes:
    return subprocess.run(
        ["git", "-C", repo_path, "show", f"{commit}:{src}"],
        capture_output=True, check=True,
    ).stdout


def copy_one(repo: str, src: str, dest: str, sanctioned: int) -> str:
    repo_path, commit = REPOS[repo]
    data = git_show(repo_path, commit, src)
    sha = hashlib.sha256(data).hexdigest()
    out = os.path.join(AUTOHARN, dest)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as fh:
        fh.write(data)
    with open(RECORD, "a") as fh:
        fh.write(f"{repo}\t{src}\t{dest}\t{commit}\t{sha}\t{sanctioned}\tno\n")
    return sha


def main(argv: list) -> int:
    manifest = load_manifest()
    if len(argv) >= 4 and argv[1] == "--one":
        # single-copy mode used to PROVE the refusal both-polarity
        repo, src, dest = argv[2], argv[3], argv[4]
        key = (repo, src, dest)
        if key not in manifest:
            print(f"REFUSED: ({repo}, {src}, {dest}) is not a manifest row",
                  file=sys.stderr)
            return 2
        sha = copy_one(repo, src, dest, manifest[key])
        print(f"COPIED {dest}  {sha[:12]}")
        return 0
    # full run: header then every manifest row, in file order
    with open(RECORD, "w") as fh:
        fh.write("source_repo\tsource_path\tdest_path\tsource_commit"
                 "\tsource_sha256\tsanctioned_adapt\tadapted_now\n")
    n = 0
    for (repo, src, dest), sanctioned in manifest.items():
        copy_one(repo, src, dest, sanctioned)
        n += 1
    print(f"migrated {n} files -> {RECORD}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
