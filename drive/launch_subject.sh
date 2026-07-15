#!/usr/bin/env bash
# launch_subject.sh — mechanize the fragile subject-launch SETUP (the "80%"): stage the packet, archive+
# truncate the run journal (R1), leak-check, substrate-check, and print the TWO irreducible human
# touchpoints (web-off launch; paste the directive). It does NOT start the session and does NOT deliver.
#
# Why those two stay human: the block-and-ask lever measures whether the subject asks a HUMAN OPERATOR —
# an AI operator would be inside the apparatus (knows the blind) and would change what is measured. And
# "paste, don't cat" is the F40 discipline the human owns (a future deliver.sh can ENFORCE byte-exactness
# via tmux paste-buffer, but that is a hardening of the mechanic, not a removal of the human).
#
# Run AFTER `arm_<run>.sh --verify` is GREEN. Usage: launch_subject.sh <build-dir> [--dry-run]
# --dry-run mutates NOTHING (prints what it would stage/truncate) — safe to inspect before the real run.
set -u
BUILD="${1:?usage: launch_subject.sh <build-dir> [--dry-run]}"
DRY=0; [ "${2:-}" = "--dry-run" ] && DRY=1
[ -f "$BUILD/launch.conf" ] || { echo "no launch.conf in $BUILD"; exit 2; }
BUILD="$(cd "$BUILD" && pwd)"
OP="$(cd "$BUILD/../.." && pwd)"
PACKET="$BUILD/packet"
PGHOST=192.168.122.1
# shellcheck disable=SC1091
source "$BUILD/launch.conf"
say(){ echo "  $*"; }
run(){ if [ $DRY -eq 1 ]; then echo "  [dry-run] $*"; else eval "$*"; fi; }

echo "== 1. Stage the packet into the sandbox (the ONLY files the subject sees) =="
run "mkdir -p '$FENCED'"
for f in $STAGE; do
  [ -e "$PACKET/$f" ] && run "cp -r '$PACKET/$f' '$FENCED/'" || say "!! missing packet file: $f"
done
say "staged [$STAGE] -> $FENCED   (NOT staged: [$DELIVER] pasted; oracle/arm/pretest apparatus-side)"

echo "== 2. Archive + truncate the run journal (R1 — the run starts on a clean single-run journal) =="
ts=$(date +%Y%m%dT%H%M%S)
run "mkdir -p '$OP/witness'"
run "cp '$JOURNAL' '$OP/witness/$(basename "$BUILD")-launch-$ts.journal.bak' 2>/dev/null || true"
run ": > '$JOURNAL'"

echo "== 3. Leak-check — no stray CLAUDE.md above the sandbox pulls apparatus rules in =="
leak=$(ls "$HOME/CLAUDE.md" "$HOME/.claude/CLAUDE.md" 2>/dev/null || true)
[ -z "$leak" ] && say "OK — no parent/global CLAUDE.md; the subject sees only the packet CLAUDE.md" \
  || say "!! stray CLAUDE.md ($leak) — move it aside for the run or confirm it is harmless"

echo "== 4. Substrate check — the subject-kernel is present in the ledger db =="
if psql -h $PGHOST -d "$DB" -tAc "SELECT to_regclass('public.ledger') IS NOT NULL;" 2>/dev/null | grep -q t; then
  say "OK — public.ledger present in $DB"
else say "!! $DB kernel not applied — run arm_<run>.sh --arm (createdb + the s-kernel DDL) first"; fi

echo
echo "== THE TWO HUMAN TOUCHPOINTS (irreducible — the lever measures a HUMAN operator) =="
echo "  (a) START the subject with WEB TOOLS OFF, then CONFIRM (ask it to list its tools; none web-capable):"
echo "        cd $FENCED && $WEBOFF"
echo "  (b) PASTE the following as your first message(s) — never 'cat'/'!'/any shell in the subject session:"
for f in $DELIVER; do
  echo "      ---------- $f ----------"
  sed 's/^/        /' "$PACKET/$f"
done
echo
echo "  (If the subject FIRES: deliver the pre-ratified answer, then file it from the OPERATOR window via"
echo "   tools/file_resolution.py — the oracle §4 freight; do not improvise the answer.)"
[ $DRY -eq 1 ] && echo "# DRY-RUN — nothing was staged or truncated."
