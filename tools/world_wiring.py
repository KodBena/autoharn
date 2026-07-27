#!/usr/bin/env python3
"""tools/world_wiring.py -- backup/restore for a scaffolded world's MACHINE-LOCAL WIRING set
(maintainer commission 2026-07-27, verbatim: "back up all relevant files with a manifest, put in
a tar.gz, clone your upstream repository, then ../autoharn/tools/whatever_well_call_it.sh
backup_scaffold.tar.gz or something like that"). Named `world_wiring`, not `backup_scaffold`:
the artifact this tool moves is not the whole scaffold (source code, docs, the git tree cross via
the clone itself) -- it is specifically the WIRING a scaffolded world's operator surface needs to
run at all on a NEW clone/host: deployment.json, the served-boundary dispatcher, GPG keys, the ADR
corpus copy, `.claude/` config. WORLD-REBIRTH-RUNBOOK.md's re-attach procedure is the sibling for
"same world, new BIRTH"; this tool is the sibling for "same world, new clone/host" -- no birth, no
kernel write, purely a file-level snapshot-and-restore of what already exists on disk.

THIS FILE IS A THIN DISPATCHER (ADR-0007 file-size discipline; ADR-0012 P3 one-owner
collaborators): the two subcommands' real logic lives in tools/world_wiring_backup.py and
tools/world_wiring_restore.py, sharing tools/world_wiring_shared.py's plumbing (AUTOHARN
resolution, filing/deployment_record.py import, the manifest constants, the sha256 helper). This
docstring is nonetheless the tool's ONE authoritative contract -- read it here, not scattered
across the three files.

Two subcommands:

  backup <world-dir> [--out PATH]
      Read-only against <world-dir>. Enumerates the CLOSED wiring set below, hashes every
      included file, and writes ONE tar.gz whose first member is manifest.json.

  restore <archive.tar.gz> [--dest DIR] [--force]
      Verifies the manifest and EVERY member's sha256 before writing anything -- refuses
      wholesale (nothing written) on any defect -- then restores files and their modes into DIR
      (default: the current directory, matching the commission's own "clone your upstream repo,
      then run this" sequencing: DIR is normally the freshly cloned project's own root).

THE CLOSED WIRING SET (derived by walking, not a hand-typed file list, wherever the source is
itself a variable-content directory -- .claude/, law/, keys/, attestations/, legacy/ are walked
and every file under them crosses except the two named .claude/ exclusions; deployment.*.json.dust
is a glob because a world may carry zero, one, or several preserved predecessor records depending
on how many rebirths it has been through, WORLD-REBIRTH-RUNBOOK.md Step 1):

  deployment.json            required; also this tool's own source for world name/schema/kern/
                              role (filing/deployment_record.py's shape) -- backup refuses loudly
                              if it is missing or fails that module's own validation.
  deployment.*.json.dust     glob; zero or more preserved predecessor deployment records.
  autoharn                   the world-local ONE dispatcher (design/FABLE-AUTOHARN-UMBRELLA-CLI-
                              SPEC.md \xa76) -- optional; a world scaffolded before that migration
                              carries its ten bare per-verb shims instead and has none of this
                              file (not an error; CLAUDE.md: "a world scaffolded before this
                              migration keeps its ten shims untouched").
  .autoharn-world.json       the scaffold's own born-sentinel (design/FABLE-SETUP-TUI-DESTINATION
                              -STATE-SPEC.md \xa72).
  features.json               the durable feature-manifest record of the birth run.
  legacy/                     whole directory: the direct-psql originals (pickup/asof-export/
                              distance-to-clean) + the retired `led` teaching-stub.
  .claude/                    whole directory EXCLUDING .claude/secrets/ and .claude/logs/ (see
                              SECRETS below; logs/ is session/runtime churn, not wiring -- the
                              same line the autoharn-panel repo's own committed .gitignore draws
                              in its "scaffold-owned churn" block).
  law/                        whole directory: this project's own ADR corpus copy.
  keys/                       whole directory: GPG trust-layer keys (design/MAINT-GPG-TRUST-
                              LAYER.md).
  attestations/                whole directory: doc-legibility attestation records.
  boundary-multiplex.toml     single file, IF PRESENT -- a world not yet wired to a served
                              multiplex hub has none; absence is not an error.

Every one of the above is optional EXCEPT deployment.json (backup cannot build a manifest without
it) -- an absent optional member is neither included nor excluded, it is simply not present, and
is reported as such (distinct from an EXCLUDED member, which exists on disk but is deliberately
left out).

NAMED GAP, NOT SILENTLY DROPPED (v1 scope): a world scaffolded BEFORE the umbrella-CLI migration
(CLAUDE.md: "a world scaffolded before this migration keeps its ten shims untouched") carries ten
bare per-verb shims (led, judge, pickup, audit, distance-to-clean, verify-commission, verify-chain,
attest-doc, asof-export, doctor) INSTEAD of the single `autoharn` dispatcher -- those ten files are
NOT in the closed set above, so backing up a pre-migration world with this tool captures its
config/keys/law/.claude but not its own dispatch surface. Flagged here rather than silently
producing an incomplete backup for that world shape; v1 targets a post-migration (single-
dispatcher) world, matching every currently-scaffolded world this tool was built against.

SECRETS ARE EXCLUDED BY DEFAULT, AND THE EXCLUSION IS LOUD. `.claude/secrets/` file NAMES are
listed (so the exclusion print can name each one) but their BYTES are never read -- no hash, no
tar member, no --include-secrets flag exists in v1. A secret's transport is the operator's own
explicit act (scp, a password manager, a sealed channel) -- never something a backup tool defaults
into doing for you. This is the same posture ADR-0002 Rule 2 states for a boundary that must
reject what it cannot honor ("validate at boundaries; do not coerce"), applied here to what this
tool will not even attempt to carry.

RESTORE refuses WHOLESALE -- nothing written -- on (ADR-0012 P2: a boundary translates-and-
validates, it never coerces a malformed input into a plausible one; mirrors bootstrap/
extract_context.py's own manifest-refusal posture):
  * a missing or unparseable manifest.json (must be the archive's first member);
  * any archive member whose path is absolute, contains a `..` component, or is not a manifest-
    listed path;
  * any archive member that is not a regular file (a symlink/hardlink/device member is refused --
    the classic tar-extraction path-escape vector, closed here even though the commission did not
    name it, per CLAUDE.md's engineering-responsibility bullet: a hazard in reach of this tool's
    own extraction path is fixed here, not routed around);
  * any member whose sha256 disagrees with the manifest's recorded hash for that path;
  * any manifest mode carrying setuid/setgid/sticky bits (restore never mints privileged
    binaries from an archive -- no wiring file legitimately needs them);
  * any destination path component that is already a SYMLINK on disk (writing through it would
    land bytes outside --dest -- the on-disk twin of the in-archive symlink refusal above;
    found by the 2026-07-27 orchestrator inline pass after the maintainer waived the
    fresh-context review, and closed per the same engineering-responsibility bullet);
  * an existing destination file that differs from the incoming one -- UNLESS --force, which
    overwrites and prints every such overwrite by name.

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import below is top-of-file.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from world_wiring_backup import cmd_backup  # noqa: E402
from world_wiring_restore import cmd_restore  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(prog="world_wiring", description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    pb = sub.add_parser("backup", help="read-only: snapshot a world's wiring set into a tar.gz")
    pb.add_argument("world_dir", help="path to the scaffolded world's project directory")
    pb.add_argument("--out", default=None,
                     help="output tar.gz path (default: ./<world-dir-basename>-wiring.tar.gz)")
    pb.set_defaults(func=cmd_backup)

    pr = sub.add_parser("restore", help="verify-then-restore a wiring tar.gz into a directory")
    pr.add_argument("archive", help="path to a wiring tar.gz produced by 'backup'")
    pr.add_argument("--dest", default=".", help="destination directory (default: cwd -- normally "
                                                  "the freshly cloned project's own root)")
    pr.add_argument("--force", action="store_true",
                     help="overwrite differing existing destination files (each overwrite is "
                          "printed by name)")
    pr.set_defaults(func=cmd_restore)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
