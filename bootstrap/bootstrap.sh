#!/bin/sh
# bootstrap.sh — clone → collaborating. Idempotent: env check, git-hook install, gate
# runnability, DB reachability. It is EXECUTED, not proofread (mandate §6): a DB-reachability
# failure prints the pg_hba/host facts loudly and exits non-zero — it never soft-passes.
#
#   Run once per fresh clone:  sh bootstrap/bootstrap.sh
#
# What it does NOT do: create databases, change pg_hba, or provision secrets — those are the
# maintainer's host-side acts (named at the end if the DB is unreachable). Lazy nothing.
set -u
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT" || exit 2
PY="$HOME/w/vdc/venvs/generic/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"
PGHOST="${HARNESS_PGHOST:-${EPISTEMIC_PGHOST:-192.168.122.1}}"
DB="${HARNESS_DB:-harness}"
rc=0
ok()   { printf '  [OK ] %s\n' "$1"; }
no()   { printf '  [!! ] %s\n' "$1"; rc=1; }

echo "== autoharn bootstrap =="
echo "-- environment --"
if [ -n "$PY" ] && "$PY" -c 'import sys; assert sys.version_info[:2] >= (3, 10)' 2>/dev/null; then
    ok "python: $("$PY" --version 2>&1) ($PY)"
else
    no "no python >= 3.10 found (expected the generic venv at ~/w/vdc/venvs/generic or a system python3)"
fi
command -v psql >/dev/null 2>&1 && ok "psql present ($(psql --version 2>&1 | head -1))" \
    || no "psql not on PATH — the ledger/kernel proofs need it"
command -v clingo >/dev/null 2>&1 && ok "clingo present ($(clingo --version 2>&1 | head -1))" \
    || printf '  [.. ] clingo not found — the engine differential proofs need it (not fatal to bootstrap)\n'

echo "-- git hook (the pre-commit gate chain) --"
git config core.hooksPath hooks && [ -x hooks/pre-commit ] \
    && ok "core.hooksPath=hooks installed; pre-commit executable" \
    || no "could not install the git hook (staging_guard/no_lazy/census gates would not run)"

echo "-- gates runnable (import smoke: any module with NO test coverage is checked here) --"
for g in gates/no_lazy_imports.py gates/staging_guard.py gates/fixture_census.py gates/layout_census.py gates/doc-legibility/check.py; do
    "$PY" -c "import ast,sys; ast.parse(open('$g').read())" 2>/dev/null \
        && ok "parses: $g" || no "does not parse: $g"
done
# the two census gates must actually pass on a fresh clone (they are cheap + DB-free)
"$PY" gates/layout_census.py  >/dev/null 2>&1 && ok "layout-census GREEN"  || no "layout-census RED on a fresh clone"
"$PY" gates/fixture_census.py >/dev/null 2>&1 && ok "fixture-census GREEN" || no "fixture-census RED on a fresh clone"

echo "-- DB reachability (the ledger/kernel substrate) --"
if command -v psql >/dev/null 2>&1 && [ "$(psql -h "$PGHOST" -d "$DB" -tAc 'SELECT 1;' 2>/dev/null)" = "1" ]; then
    ok "harness DB reachable at $PGHOST/$DB"
else
    no "harness DB NOT reachable at $PGHOST/$DB"
    echo "     This is (almost always) a HOST fact, not a code fact — surfaced, never soft-passed:" >&2
    echo "       * the DB server at $PGHOST must be up and accept this host/user in pg_hba.conf;" >&2
    echo "       * from a NEW host/user the maintainer must add a pg_hba entry (a maintainer act," >&2
    echo "         never a credential in the repo);" >&2
    echo "       * override host/db via HARNESS_PGHOST / HARNESS_DB if they differ here." >&2
fi

echo "-- result --"
if [ "$rc" -eq 0 ]; then
    echo "bootstrap GREEN. Next: read bootstrap/QUICKSTART.md and run the mini-collaboration."
else
    echo "bootstrap RED — resolve the [!!] lines above before collaborating (nothing soft-passed)."
fi
exit "$rc"
