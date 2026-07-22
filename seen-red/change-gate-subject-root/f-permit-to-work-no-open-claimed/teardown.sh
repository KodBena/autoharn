#!/usr/bin/env bash
# Drops the scratch schema/kernel/role setup.sh created -- zero DB residue between runs.
psql -h "${PGHOST:?PGHOST not set -- run this fixture via run_fixtures.py, never a literal host default}" -d toy -c \
  "DROP SCHEMA IF EXISTS hookprobe_ptw_f CASCADE; DROP SCHEMA IF EXISTS hookprobe_ptw_f_kernel CASCADE; DROP OWNED BY hookprobe_ptw_f_rw; DROP ROLE IF EXISTS hookprobe_ptw_f_rw;" \
  >/dev/null 2>&1 || true
