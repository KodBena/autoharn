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
# PGHOST: env override, else this checkout's own deployment.json 'host' field, else UNSET --
# never a silent literal default (the maintainer's own LAN host is not a fresh clone's fact).
PGHOST="${HARNESS_PGHOST:-${EPISTEMIC_PGHOST:-}}"
DEP="${LEDGER_DEPLOYMENT:-$REPO_ROOT/deployment.json}"
if [ -z "$PGHOST" ] && [ -f "$DEP" ] && [ -n "$PY" ]; then
    PGHOST="$("$PY" -c "
import json, sys
try:
    with open(sys.argv[1]) as f:
        print(json.load(f).get('host') or '')
except Exception:
    print('')
" "$DEP" 2>/dev/null)"
fi
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

echo "-- git merge driver (union merge for append-only jsonl ledgers) --"
# vestigial_documentation/design/ORCH-WORKTREE-LEDGERING.md 3a: .gitattributes (versioned) names WHICH files use this
# driver; the driver COMMAND itself must live in .git/config (unversioned), so every clone/worktree
# installs it once here -- the same one-time-per-clone shape as core.hooksPath above.
# (A sibling BACKLOG.md dated-section driver was retired with that file on 2026-07-12,
# tracker ledger row 137; tools/merge_backlog_sections.py remains in-tree as history.)
git config merge.jsonl-union.name "union merge driver for append-only jsonl ledgers" \
    && git config merge.jsonl-union.driver "$PY tools/merge_jsonl.py %O %A %B" \
    && ok "merge driver installed (jsonl-union)" \
    || no "could not install the merge driver (attestations/*.jsonl would conflict by hand on a worktree merge)"

echo "-- gates runnable (import smoke: any module with NO test coverage is checked here) --"
for g in gates/no_lazy_imports.py gates/staging_guard.py gates/fixture_census.py gates/layout_census.py gates/doc-legibility/check.py; do
    "$PY" -c "import ast,sys; ast.parse(open('$g').read())" 2>/dev/null \
        && ok "parses: $g" || no "does not parse: $g"
done
# the two census gates must actually pass on a fresh clone (they are cheap + DB-free)
"$PY" gates/layout_census.py  >/dev/null 2>&1 && ok "layout-census GREEN"  || no "layout-census RED on a fresh clone"
"$PY" gates/fixture_census.py >/dev/null 2>&1 && ok "fixture-census GREEN" || no "fixture-census RED on a fresh clone"

echo "-- DB reachability (the ledger/kernel substrate) --"
if [ -z "$PGHOST" ]; then
    no "no Postgres host resolved (checked HARNESS_PGHOST, EPISTEMIC_PGHOST, and $DEP's 'host' field)"
    echo "     Never defaulting to any host: set HARNESS_PGHOST or EPISTEMIC_PGHOST, or place a" >&2
    echo "     deployment.json with a 'host' field at $DEP (copy deployment.json.example and fill" >&2
    echo "     in your own values; see README.md 'Configuration')." >&2
elif command -v psql >/dev/null 2>&1 && [ "$(psql -h "$PGHOST" -d "$DB" -tAc 'SELECT 1;' 2>/dev/null)" = "1" ]; then
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
    echo "bootstrap GREEN. Next: read user-guide/QUICKSTART.md and run the mini-collaboration."
else
    echo "bootstrap RED — resolve the [!!] lines above before collaborating (nothing soft-passed)."
fi
exit "$rc"
