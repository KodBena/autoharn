#!/usr/bin/env bash
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-10T19:33:06Z
#   last-change: 2026-07-10T19:33:06Z
#   contributors: be693afb/main
# <<< PROVENANCE-STAMP <<<

# Drops the scratch schema/kernel/role setup.sh created -- zero DB residue between runs.
psql -h 192.168.122.1 -d toy -c \
  "DROP SCHEMA IF EXISTS hookprobe_ptw_f CASCADE; DROP SCHEMA IF EXISTS hookprobe_ptw_f_kernel CASCADE; DROP OWNED BY hookprobe_ptw_f_rw; DROP ROLE IF EXISTS hookprobe_ptw_f_rw;" \
  >/dev/null 2>&1 || true
