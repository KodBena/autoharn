#!/usr/bin/env bash
# run-core-a.sh — the Core-A k-phase sweep (consult 17 §5.2), the standing check behind the two s13
# waiver rows' evidence. Prints SATISFIABLE/UNSATISFIABLE per phase; read-only (no DB, no side effects).
#
# ENGINE INC 1 NAIL FIX (ruling 110 §5 rider; refute-evaluation flaw 1(b)): the previous form was
#   clingo "$LP" "$@" 2>/dev/null | grep -E 'SATISFIABLE' | head -1
# — stderr silenced entirely (a grounding error printed NOTHING and read as a clean empty), and the
# grep matched UNSATISFIABLE as SATISFIABLE-containing text. A live F49-class silent-non-run inside
# the perimeter. Fixed: stderr is SURFACED, the verdict is an EXACT line match, and any run that
# yields neither exact verdict (syntax error, missing file, empty output) is a loud ERROR that fails
# the sweep (exit 1). The broken-program fixture (fixtures/core-a-broken.lp) + --negative-control
# prove the loud failure — a gate never seen red is a claim (ADR-0011).
set -u
HERE="$(dirname "$0")"
LP_DEFAULT="$HERE/core_a.lp"
FAIL=0

run() {
  local label="$1" lp="$2"; shift 2
  printf '  %-22s -> ' "$label"
  local out err verdict
  err="$(mktemp)"
  out="$(clingo "$lp" "$@" 2>"$err")"
  # exact-line verdict parse: SATISFIABLE and UNSATISFIABLE are distinct whole lines in clingo
  # output; a substring grep conflates them (the fixed defect).
  verdict="$(printf '%s\n' "$out" | grep -Ex 'SATISFIABLE|UNSATISFIABLE' | head -1)"
  if [ -n "$verdict" ]; then
    echo "$verdict"
  else
    echo "ERROR — no exact SATISFIABLE/UNSATISFIABLE verdict line (stderr follows)"
    sed 's/^/      ! /' "$err"
    printf '%s\n' "$out" | sed 's/^/      | /'
    FAIL=1
  fi
  rm -f "$err"
}

if [ "${1:-}" = "--negative-control" ]; then
  echo "# negative control: the broken-program fixture must FAIL LOUDLY (never a silent empty)"
  run "broken fixture" "$HERE/fixtures/core-a-broken.lp" -c k=1
  if [ "$FAIL" -eq 1 ]; then
    echo "# negative-control PASS — the broken program failed loudly (stderr surfaced, sweep red)"
    exit 0
  fi
  echo "# negative-control FAIL — the broken program did NOT trip the loud-failure path"
  exit 1
fi

echo "# Core-A k-phase sweep (corpus-consistency; waiver-row evidence)"
run "k=1"                 "$LP_DEFAULT" -c k=1
run "k=2"                 "$LP_DEFAULT" -c k=2
run "k=2 sod=1"           "$LP_DEFAULT" -c k=2 -c sod=1
run "k=3 sod=1"           "$LP_DEFAULT" -c k=3 -c sod=1
run "k=2 fin=1 orgs=1"    "$LP_DEFAULT" -c k=2 -c fin=1 -c orgs=1
run "k=2 fin=1 orgs=2"    "$LP_DEFAULT" -c k=2 -c fin=1 -c orgs=2
exit "$FAIL"
