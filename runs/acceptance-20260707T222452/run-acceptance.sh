#!/bin/sh
# mandate-§6 acceptance — EXECUTED from a FRESH CLONE of autoharn. One section per criterion.
# Usage: sh run-acceptance.sh <clone-root> <scratch-dir>
set -u
CLONE="${1:?clone root}"; SCRATCH="${2:?scratch dir}"; cd "$CLONE" || exit 2
PGHOST=192.168.122.1; DB=harness
S=acc_demo; K=acc_demo_kernel; R=acc_demo_rw
PY="$HOME/w/vdc/venvs/generic/bin/python"; [ -x "$PY" ] || PY=python3
line() { printf '\n===== %s =====\n' "$1"; }
teardown() { psql -h $PGHOST -d $DB -c "DROP SCHEMA IF EXISTS $S CASCADE; DROP SCHEMA IF EXISTS $K CASCADE; DROP OWNED BY $R; DROP ROLE IF EXISTS $R;" >/dev/null 2>&1; }

line "(a) bootstrap.sh runs green from the fresh clone"
sh bootstrap/bootstrap.sh; echo "CRITERION-a bootstrap exit=$?"

line "(b) REAL MINI-COLLABORATION"
echo "--- (b1) stand up a scratch kernel: s15 + s17-stamp + s17-independence + s18 + s19 ---"
teardown
psql -h $PGHOST -d $DB -v schema=$S -v kern=$K -v role=$R \
  -f kernel/lineage/s15-schema.sql -f kernel/lineage/s17-stamp-mechanism.sql \
  -f kernel/lineage/s17-independence-vocabulary.sql -f kernel/lineage/s18-criterion-principals.sql \
  -f kernel/lineage/s19-trigger-search-path.sql >/dev/null 2>&1 && echo "kernel stood up OK (5-file stack incl. s19)"

echo "--- (b2) the decision ledger EXERCISED: actor-omitted INSERT resolves via s19 on a NON-default schema ---"
psql -h $PGHOST -d $DB -tAc "SET ROLE $R; SET search_path=$S,$K; INSERT INTO $S.ledger (kind, statement) VALUES ('decision','acceptance: adopt the search-path idiom') RETURNING id;"
psql -h $PGHOST -d $DB -tAc "SELECT 'ledger row '||l.id||' kind='||l.kind||' actor='||p.name FROM $S.ledger l JOIN $K.principal p ON p.id=l.actor;"

echo "--- (b3) REFUSE-AND-TEACH proven LIVE: the change gate denies an unticketed edit and TEACHES ---"
SUBJ="$SCRATCH/subject"; mkdir -p "$SUBJ"; echo "x = 1" > "$SUBJ/module.py"
echo '{"tool_name":"Edit","tool_input":{"file_path":"'"$SUBJ"'/module.py"}}' \
  | env E13_GATE_DB=$DB E13_GATE_LEDGER=$S.ledger E13_SUBJECT_ROOT="$SUBJ" \
        E13_GATE_STATE="$SCRATCH/gate_state.json" E13_GATE_JOURNAL="$SCRATCH/gate_journal.jsonl" \
        "$PY" hooks/pretooluse_change_gate.py; RC1=$?
echo "gate exit on UNTICKETED edit = $RC1 (expect 2: DENY + the teaching message above)"
echo "--- (b3b) the taught path COMPLIED WITH: ledger the change, re-issue, gate ALLOWS ---"
psql -h $PGHOST -d $DB -tAc "SET ROLE $R; SET search_path=$S,$K; INSERT INTO $S.ledger (kind, statement, refs) VALUES ('decision','change module.py: set x=2 for the acceptance demo','$SUBJ/module.py') RETURNING id;"
echo '{"tool_name":"Edit","tool_input":{"file_path":"'"$SUBJ"'/module.py"}}' \
  | env E13_GATE_DB=$DB E13_GATE_LEDGER=$S.ledger E13_SUBJECT_ROOT="$SUBJ" \
        E13_GATE_STATE="$SCRATCH/gate_state.json" E13_GATE_JOURNAL="$SCRATCH/gate_journal.jsonl" \
        "$PY" hooks/pretooluse_change_gate.py; RC2=$?
echo "gate exit on LEDGERED edit = $RC2 (expect 0: allowed — the refuse-and-teach arc closed)"
echo "gate journal:"; cat "$SCRATCH/gate_journal.jsonl" 2>/dev/null

echo "--- (b4) the kernel STAMP path exercised (forgery/staleness refused; proxy self-review caught) ---"
"$PY" kernel/fixtures/s17_stamp_fixture.py; echo "stamp fixture exit=$?"

line "(c) A CLOSE runs against the new layout's instruments (close_manifest from the clone)"
echo "--- readiness mode on the scratch target (empty substrate must DEFER loudly, not silently pass) ---"
LEDGER_DB=$DB LEDGER_SCHEMA=$S "$PY" instruments/close_manifest.py $S --mode readiness 2>&1; echo "close(readiness) exit=$?"
echo "--- close mode (honest gating: REQUIRED-ABSENT/RED where substrate or findings demand it) ---"
LEDGER_DB=$DB LEDGER_SCHEMA=$S "$PY" instruments/close_manifest.py $S --mode close 2>&1; echo "close(close) exit=$?"

line "(d) the gates run from the clone's OWN pre-commit on a REAL commit"
git config core.hooksPath hooks
mkdir -p runs/acceptance-clone-witness
echo "clone-side commit witness for the mandate-§6 acceptance ($(date -Is))" > runs/acceptance-clone-witness/witness.txt
git add runs/acceptance-clone-witness/witness.txt
echo "--- (d1) NEGATIVE first: an UNDECLARED commit is REFUSED by the clone's staging guard (live red) ---"
env -u CLAUDE_COMMIT_PATHS git -c user.name=bork -c user.email=you@example.com commit -m "acceptance witness (undeclared - must be REFUSED)" 2>&1 | tail -4
echo "undeclared commit exit=$? (expect 1)"
echo "--- (d2) the DECLARED commit passes the full gate chain ---"
CLAUDE_COMMIT_PATHS="runs/acceptance-clone-witness/witness.txt" git -c user.name=bork -c user.email=you@example.com commit -m "acceptance: clone-side witness commit (gates live)" 2>&1 | grep -vE '^  [A-Za-z]+ +×' | tail -8
echo "declared commit exit=$?"
git log --oneline -1

line "(e) fixture census green + ONE LIVE RED PER MIGRATED GATE CLASS, re-executed from the clone"
"$PY" gates/fixture_census.py; echo "fixture_census exit=$?"
"$PY" gates/layout_census.py; echo "layout_census exit=$?"
echo "--- live red: kernel s19 class (pre-fix set_actor refusal reproduced) ---"
"$PY" seen-red/s19-trigger-search-path/red-specimen.py 2>&1 | tail -2; echo "exit=$?"
echo "--- live red: layout-census (emptied registry) ---"
"$PY" seen-red/layout-census/red-specimen.py >/dev/null 2>&1; echo "exit=$? (expect 0 = red proven)"
echo "--- live red: fixture-census (emptied registry) ---"
"$PY" seen-red/fixture-census/red-specimen.py >/dev/null 2>&1; echo "exit=$? (expect 0 = red proven)"
echo "--- live red: no_lazy_imports (a lazy import planted in a temp tree) ---"
LAZY="$SCRATCH/lazyrepo"; mkdir -p "$LAZY"; cd "$LAZY"; git init -q .; printf 'def f():\n    import os\n    return os.name\n' > lazy.py; git add lazy.py
"$PY" "$CLONE/gates/no_lazy_imports.py" "$LAZY"; echo "no_lazy on planted violation exit=$? (expect 1)"; cd "$CLONE"
echo "--- live red: staging guard — proven at (d1) above (undeclared commit refused) ---"
echo "--- live red: destructive-DDL class (seen-red 24 specimen) ---"
"$PY" seen-red/24-destructive-ddl-guard/red-specimen.py >/dev/null 2>&1; echo "exit=$? (expect 0 = red proven)"
echo "--- live red: append-only class (seen-red 06 specimen) ---"
"$PY" seen-red/06-append-only-integrity/red-specimen.py >/dev/null 2>&1; echo "exit=$? (expect 0 = red proven)"
echo "--- live red+green: findings gate (both polarities via its fixture) ---"
"$PY" gates/findings_gate_fixture.py 2>&1 | tail -2; echo "exit=$?"
echo "--- live red: doc-legibility (currently RED-reporting over the corpus — a live red by construction) ---"
"$PY" gates/doc-legibility/check.py >/dev/null 2>&1; echo "exit=$? (expect 1 = live red; wired report-only)"
echo "--- live red: instrument/close-line classes (mutation flips inside each verifier; + core-a negative control) ---"
"$PY" instruments/act_stream/verify_adapter.py 2>&1 | tail -1
"$PY" instruments/verify_substrate_required.py 2>&1 | tail -1
"$PY" instruments/verify_consumer_no_vacuous.py 2>&1 | tail -1
bash instruments/run-core-a.sh >/dev/null 2>&1; echo "run-core-a GREEN exit=$? (expect 0)"
bash instruments/run-core-a.sh --negative-control >/dev/null 2>&1; echo "run-core-a --negative-control exit=$? (expect 0 = its convention: 0 means the broken fixture FAILED LOUDLY, the red proven)"
echo "--- live red: stamp class (s17 fixture includes forgery/stale REFUSALS — proven at b4) ---"

teardown
line "ACCEPTANCE SCRIPT DONE"
