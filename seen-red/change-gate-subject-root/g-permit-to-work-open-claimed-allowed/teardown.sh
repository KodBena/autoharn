#!/usr/bin/env bash
psql -h "${PGHOST:?PGHOST not set -- run this fixture via run_fixtures.py, never a literal host default}" -d toy -c \
  "DROP SCHEMA IF EXISTS hookprobe_ptw_g CASCADE; DROP SCHEMA IF EXISTS hookprobe_ptw_g_kernel CASCADE; DROP OWNED BY hookprobe_ptw_g_rw; DROP ROLE IF EXISTS hookprobe_ptw_g_rw;" \
  >/dev/null 2>&1 || true
