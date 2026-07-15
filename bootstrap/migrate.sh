#!/bin/sh
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T21:20:52Z
#   last-change: 2026-07-14T21:20:52Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

# migrate.sh -- thin sh entry point for the STABLE user surface (tracker item
# migration-script-stable-interface):
#
#   bootstrap/migrate.sh <deployment-dir>              -- rehearse, ask ONE typed confirmation, apply
#   bootstrap/migrate.sh <deployment-dir> --dry-run     -- rehearse and print evidence; never applies
#
# (the root `./migrate` shim in this checkout execs this file unchanged -- same shim pattern as
# `./led`/`./pickup`, ADR-0012 P1: one resolution mechanism, not a per-verb hand copy.)
#
# All the actual logic (manifest parsing, process check, backup, rehearsal, per-delta
# verification, the one typed confirmation, live apply, re-verify, ledger recording) lives in
# bootstrap/migrate_core.py -- see that file's own module docstring for the full design. This
# shim's only jobs: resolve a python interpreter (same lookup new-project.sh already uses, so
# there is exactly one "how do we find python" convention in this tree) and pass argv through
# unmodified.
set -eu

HERE="$(cd "$(dirname "$0")" && pwd)"

PY="$HOME/w/vdc/venvs/generic/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"
if [ -z "$PY" ]; then
    echo "migrate: no python interpreter found (tried $HOME/w/vdc/venvs/generic/bin/python and python3 on PATH). Nothing was touched." >&2
    exit 1
fi

exec "$PY" "$HERE/migrate_core.py" "$@"
