#!/bin/sh
# arm.sh — the run arming checklist (consult 37 §4), RENDERED CHECKABLE, PARAMETERIZED FOR REUSE
# [manifest C13 / BUILD-BRIEF Step 8]. This is the generic instrument: it was a verbatim copy of
# arm_e18.sh (the one-off e18 script, hardcoded to db qbx / role qbx_rw / label jm7 / harness/e18-build)
# until this pass turned every run-specific literal into a `launch.conf` input (drive/launch.conf.template)
# while PRESERVING the mechanical check structure intact — every §4 check that existed still runs, just
# reading its target names from config instead of the source. `--verify` runs every check that can run
# before the subject db exists (the DDL stack applies to a throwaway incl. the reviewer principals +
# negative control, the frozen texts match their shas, the hook idiom is interceptable, the fixtures pass,
# the ambiguity pre-test is banked and TWO-CONSECUTIVE-EMPTY, both oracle cells are written); the `--arm`
# actions that need the real subject db (pg_hba, host-side — the maintainer's step) are printed as an
# ordered checklist. NOTHING here arms by itself; arming is the maintainer's, gated by this checklist.
#
# Usage: arm.sh <build-dir> --verify | --arm | --delivery-set
#   <build-dir>  the PER-RUN directory holding this run's launch.conf, packet/, ambiguity-pretest/,
#                oracle.md, criterion-brief-*.md (e.g. runs/<label>-build/ — see runs/README.md). In the
#                old layout this script AND that content shared one directory (harness/e18-build/); now
#                the script is shared machinery (drive/) and the content is per-run (mirrors how
#                drive/launch_subject.sh already took <build-dir> as an argument pre-migration).
#
# Config is sourced from <build-dir>/launch.conf if present; every variable below falls back to its
# original e18/qbx value if launch.conf omits it (so this script reproduces the e18 arming behavior
# byte-for-effect with no config at all). See drive/launch.conf.template for the full var list + comments.
# Vars already established by launch_subject.sh's template (FENCED = subject sandbox dir, DB = subject
# ledger db) are REUSED here, not duplicated under a second name — arm_e18.sh's own `SUBJDIR` collapses
# into `FENCED`, matching the concept launch_subject.sh already names.
set -u
DRIVE_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$DRIVE_DIR/.." && pwd)"
INSTR="$REPO_ROOT/instruments"
KERNEL_DIR="$REPO_ROOT/kernel/lineage"
HOOKS_DIR="$REPO_ROOT/hooks"
PGHOST=192.168.122.1

BUILD_DIR="${1:?usage: arm.sh <build-dir> --verify|--arm|--delivery-set}"; shift
BUILD_DIR="$(cd "$BUILD_DIR" 2>/dev/null && pwd || echo "$BUILD_DIR")"
# shellcheck disable=SC1091
[ -f "$BUILD_DIR/launch.conf" ] && . "$BUILD_DIR/launch.conf"

# ---- config, with the original e18/qbx literals as defaults (launch.conf overrides per run) ----------
RUN_LABEL="${RUN_LABEL:-e18}"                 # internal engineering label (finding/consult numbering)
DB="${DB:-qbx}"                                # subject ledger db — shared name with launch.conf.template
RUN_ROLE="${RUN_ROLE:-qbx_rw}"                 # author role that owns/writes the ledger in $DB
RUN_REV1="${RUN_REV1:-${RUN_ROLE%_rw}_rev1}"   # criterion-reviewer role 1 (INSERT-only negative control)
RUN_REV2="${RUN_REV2:-${RUN_ROLE%_rw}_rev2}"   # criterion-reviewer role 2 (INSERT-only negative control)
FENCED="${FENCED:-$HOME/jm7-build}"            # the subject's sandbox working dir (arm_e18.sh's SUBJDIR;
                                                # reconciled onto launch_subject.sh's FENCED name — MUST be
                                                # an opaque token distinct from RUN_LABEL for the subject blind)
RELBASE="${RELBASE:-harness/${RUN_LABEL}-build}"   # anchor-manifest path prefix recorded into acts.ruling
SECRET_FILE="${STAMP_SECRET_FILE:-${SECRET_FILE:-$HOME/.config/epistemic/${RUN_LABEL}-stamp-secret.hex}}"
# Optional override: space-separated absolute paths, IN ORDER, replacing the default kernel DDL stack
# below. Empty = use the default. kernel/lineage/README.md names s15+s17-stamp+s17-independence+
# s18-principals+s19-trigger-search-path as "the current kernel" apply order (s19 forecloses the
# set_actor schema-literal class — findings 16/37/45 — and was ADDED to the default here, not just
# flagged: it applies clean on top of s18 on a throwaway, proven by re-running this exact stack before
# the change shipped; arm_e18.sh predates s19, so this default now certifies MORE than the e18-era
# script did, on purpose — the BUILD-BRIEF Step-6 precedent for exactly this class of migration-touch
# discovery: fix it in scope, don't carry a known defect into the fresh home untouched).
KERNEL_STACK="${KERNEL_STACK:-}"
if [ -z "$KERNEL_STACK" ]; then
  KERNEL_STACK="$KERNEL_DIR/s15-schema.sql $KERNEL_DIR/s17-stamp-mechanism.sql $KERNEL_DIR/s17-independence-vocabulary.sql $KERNEL_DIR/s18-criterion-principals.sql $KERNEL_DIR/s19-trigger-search-path.sql"
fi
PREV_LABEL="${PREV_LABEL:-e17}"                # the predecessor run this one's packet is byte-lineage-derived from (§4k, printed only)
TOKEN_MAP="${TOKEN_MAP:-kt3->jm7, wmb->qbx, wmb_rw->qbx_rw}"   # the predecessor's token map (§4k, printed only)

PRETEST="$BUILD_DIR/ambiguity-pretest"
PY="$HOME/w/vdc/venvs/generic/bin/python"; [ -x "$PY" ] || PY="$(command -v python3)"
FAIL=0
ok(){ printf '  [OK ] %s\n' "$1"; }
no(){ printf '  [!! ] %s\n' "$1"; FAIL=1; }

verify() {
  echo "== §4 [$RUN_LABEL] arming checklist — VERIFY (pre-arm readiness) =="

  echo "(a) substrate registration line ready (fenced dir + subject session dir -> ledger_target):"
  grep -q "$RUN_LABEL\|$DB" "$INSTR/ledger_target.py" 2>/dev/null \
    && ok "ledger_target knows $RUN_LABEL/$DB" \
    || no "$RUN_LABEL/$DB NOT yet registered in ledger_target (arm step a) — the finding-36 gate REDs a bare close without it"

  echo "(b) DDL stack instantiates on a throwaway (s15 + s17-stamp + s17-independence + s18-principals + s19-trigger-search-path, or \$KERNEL_STACK override):"
  S="${RUN_LABEL}arm"; K="${RUN_LABEL}arm_k"; R="${RUN_LABEL}arm_rw"; R1="${RUN_LABEL}arm_rev1"; R2="${RUN_LABEL}arm_rev2"
  psql -h $PGHOST -d harness -q -c "DROP SCHEMA IF EXISTS $S CASCADE; DROP SCHEMA IF EXISTS $K CASCADE; DROP OWNED BY $R1; DROP ROLE IF EXISTS $R1; DROP OWNED BY $R2; DROP ROLE IF EXISTS $R2;" >/dev/null 2>&1
  ddl_f_args=""; for f in $KERNEL_STACK; do ddl_f_args="$ddl_f_args -f $f"; done
  if psql -h $PGHOST -d harness -q -v ON_ERROR_STOP=1 -v schema=$S -v kern=$K -v role=$R -v rev1=$R1 -v rev2=$R2 \
       $ddl_f_args >/dev/null 2>&1; then
    ok "full DDL stack applies clean incl. reviewer principals (fresh instantiation)"
  else no "the DDL stack does NOT apply clean — instantiation broken"; fi

  echo "(c) reviewer-principal NEGATIVE CONTROL on the throwaway (rev1/rev2 INSERT, NOT SELECT, on ledger):"
  NC=$(psql -h $PGHOST -d harness -tA -v ON_ERROR_STOP=1 -c \
    "SELECT bool_and(NOT has_table_privilege(r,'$S.ledger','SELECT') AND has_table_privilege(r,'$S.ledger','INSERT')) FROM (VALUES ('$R1'),('$R2')) v(r);" 2>/dev/null)
  [ "$NC" = "t" ] && ok "negative control holds: rev1/rev2 INSERT-only, no SELECT on unit ledger" \
                  || no "negative control FAILED (got '$NC') — first-contact fence not enforced by privilege"
  psql -h $PGHOST -d harness -q -c "DROP SCHEMA IF EXISTS $S CASCADE; DROP SCHEMA IF EXISTS $K CASCADE; DROP OWNED BY $R1; DROP ROLE IF EXISTS $R1; DROP OWNED BY $R2; DROP ROLE IF EXISTS $R2;" >/dev/null 2>&1

  echo "(d) hook-coverage: stamp_intercept injects UNCONDITIONALLY when wired (MATCHERLESS contract, BACKLOG"
  echo "    'Run-5 forensics' 2026-07-10 -- the old _is_ledger_psql/_is_led_invocation matchers are DELETED,"
  echo "    so this check no longer imports a private matcher function; it drives the real hook end-to-end"
  echo "    and asserts an ARBITRARY, non-psql-shaped command still gets stamped when a secret is wired):"
  ARMCHECK_SECRET=$(mktemp)
  ( umask 077; openssl rand -hex 32 > "$ARMCHECK_SECRET" )
  "$PY" - <<PYEOF && ok "stamp_intercept injects PGOPTIONS unconditionally for an arbitrary command (matcherless, wired)" \
                  || no "stamp_intercept did NOT inject -- matcherless contract broken, fix before freeze (§4d)"
import json, os, subprocess, sys
env = dict(os.environ); env["STAMP_SECRET"] = "$ARMCHECK_SECRET"
payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "echo not-a-psql-call"},
                       "session_id": "armcheck", "cwd": "/tmp"})
cp = subprocess.run(["python3", "$HOOKS_DIR/stamp_intercept.py"], input=payload,
                     capture_output=True, text=True, env=env, timeout=10)
out = json.loads(cp.stdout) if cp.stdout.strip() else {}
cmd = out.get("hookSpecificOutput", {}).get("updatedInput", {}).get("command", "")
sys.exit(0 if "PGOPTIONS" in cmd and "app.vendor_hmac" in cmd else 1)
PYEOF
  rm -f "$ARMCHECK_SECRET"

  echo "(e) MANDATORY ambiguity pre-test banked, TWO CONSECUTIVE empty rounds (finding 41):"
  if [ -d "$PRETEST" ]; then
    # STRICT machine token: each round VERDICT.md's FIRST non-blank line is exactly
    #   'VERDICT: EMPTY'  or  'VERDICT: NON-EMPTY'  (anything else = malformed, treated as NON-EMPTY).
    # The streak counts TRAILING consecutive rounds whose token is exactly EMPTY. Prose in the body
    # (which discusses "empty" and "divergence" as concepts) can never satisfy this — only the token can.
    ROUNDS=$(ls -d "$PRETEST"/round-* 2>/dev/null | sort -V)
    [ -n "$ROUNDS" ] || no "no round-* dirs under ambiguity-pretest/"
    STREAK=0
    for rd in $ROUNDS; do
      TOK=$(grep -m1 -E '^VERDICT: (EMPTY|NON-EMPTY)$' "$rd/VERDICT.md" 2>/dev/null)
      if [ "$TOK" = "VERDICT: EMPTY" ]; then STREAK=$((STREAK+1)); else STREAK=0; fi
      [ -n "$TOK" ] || no "round $(basename "$rd") VERDICT.md lacks a strict 'VERDICT: EMPTY|NON-EMPTY' token"
    done
    [ "$STREAK" -ge 2 ] && ok "pre-test met: last two rounds carry 'VERDICT: EMPTY' (streak=$STREAK)" \
                        || no "pre-test NOT met: trailing empty-round streak=$STREAK (<2) — DO NOT FREEZE (finding 41)"
    # every round must have both finder transcripts banked
    for rd in $ROUNDS; do
      N=$(ls "$rd"/*.jsonl 2>/dev/null | wc -l)
      [ "$N" -ge 2 ] || no "round $(basename "$rd") has <2 banked finder transcripts (N=$N)"
    done
  else no "no ambiguity-pretest/ dir under $BUILD_DIR — the mandatory pre-test has not run"; fi

  echo "(f) criterion briefs frozen + sha-anchorable (both lenses, anchored BEFORE packet hashes):"
  for b in criterion-brief-correctness.md criterion-brief-conformance.md; do
    [ -f "$BUILD_DIR/$b" ] && ok "$b frozen ($(sha256sum "$BUILD_DIR/$b" | cut -c1-16)…)" || no "$b missing"
  done

  echo "(g) review_fixpoint fixture GREEN (the line that arms the run) + review_without_detail + binder:"
  "$PY" "$INSTR/verify_review_fixpoint.py"     >/dev/null 2>&1 && ok "review_fixpoint fixture GREEN" || no "review_fixpoint fixture RED"
  "$PY" "$INSTR/verify_review_without_detail.py" >/dev/null 2>&1 && ok "review_without_detail fixture GREEN (Addendum A, finding 38)" || no "review_without_detail fixture RED"

  echo "(h) both oracle cells written BEFORE the run (close-1 + close-2; three cells):"
  { grep -q "close-1" "$BUILD_DIR/oracle.md" && grep -q "close-2" "$BUILD_DIR/oracle.md" \
      && grep -q "FIXED-POINT-HOLDS" "$BUILD_DIR/oracle.md" && grep -q "RESIDUAL-REAL" "$BUILD_DIR/oracle.md" \
      && grep -q "NOISE-TAIL" "$BUILD_DIR/oracle.md"; } \
    && ok "oracle.md carries both closes + all three cells" || no "oracle.md incomplete or missing under $BUILD_DIR"

  echo "(i) repro-adjudication harness present (runs each criterion finding's recipe; real vs noise banked):"
  [ -f "$DRIVE_DIR/adjudicate_repro.py" ] && "$PY" -c "import ast,sys; ast.parse(open('$DRIVE_DIR/adjudicate_repro.py').read())" 2>/dev/null \
    && ok "adjudicate_repro.py present and parses" || no "adjudicate_repro.py missing or unparseable"

  echo "(j) gate-journal registration check ready (fc22; verify_gate_journal_registered.py present):"
  [ -f "$INSTR/verify_gate_journal_registered.py" ] && ok "gate-journal-registered check present" || no "fc22 check missing"

  echo "(k) packet byte-lineage from the predecessor run (CLAUDE.md/ledger_helper/kickoff byte-held modulo tokens):"
  echo "       [manual/arm] diff each against its $PREV_LABEL origin modulo the token map ($TOKEN_MAP)"

  echo "(l) MANDATORY: subject + reviewer sessions have NO web-capable tools (verified at arm on settings):"
  echo "       [manual/arm] confirm subject AND both reviewer .claude/settings.json enable no WebFetch/WebSearch/MCP-net"

  echo "(m) machinery inherited from the prior generation (checked at arm): fresh opaque db+label, R1-R3,"
  echo "       journal archive+truncate, contemporaneity registration, close readiness, delivery drill."

  [ $FAIL -eq 0 ] && echo "== VERIFY GREEN — every checkable §4 line ready; arm actions below are the maintainer's ==" \
                  || echo "== VERIFY RED — a §4 line is not ready (above); DO NOT FREEZE/ARM =="
  return $FAIL
}

# The apparatus secret lives OUTSIDE the repo (never committed), chmod 600. The hook reads the hex here;
# the trigger reads the same bytes from kernel.stamp_secret. ONE fresh secret per run (ruling 43).
WITNESS="$BUILD_DIR/arm-witness"   # negative-control evidence (committed; contains NO secret)

anchor_freeze() {
  HEAD=$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)
  # psql -c does NOT interpolate -v vars; verbatims carry no '$' so inline dollar-quoting ($V$..$V$) is
  # safe and unambiguous. The existence check must return "0" (a real count) to insert — an empty/errored
  # result is treated as FAILURE (not "exists"), so a broken query can never masquerade as idempotent skip.
  _anchor() { # $1=label $2=repo-relative-path $3=absolute-file
    sha=$(sha256sum "$3" | cut -d' ' -f1)
    verb="$1: path=$2 sha256=$sha commit=$HEAD"
    # idempotency keys on the anchor's CONTENT (label+path+sha) — NOT the commit suffix. HEAD moves with
    # every repo commit, so keying the full verbatim re-anchored all rows on a re-run after an unrelated
    # commit (observed on e18: 30 -> 60). The duplicate set is left in place (acts.ruling is append-only;
    # same path+sha content, differing only in commit=) and disclosed in the arm commit.
    exists=$(psql -h $PGHOST -d harness -tAc "SELECT count(*) FROM acts.ruling WHERE verbatim LIKE \$V\$$1: path=$2 sha256=$sha%\$V\$;" 2>/dev/null)
    if [ "$exists" = "0" ]; then
      psql -h $PGHOST -d harness -q -v ON_ERROR_STOP=1 \
        -c "INSERT INTO acts.ruling (actor, verbatim, verbatim_sha256, binding_grade, regards, ts) VALUES ('apparatus:engineer', \$V\$$verb\$V\$, encode(digest(\$V\$$verb\$V\$,'sha256'),'hex'), 'informational', '$RUN_LABEL pre-registration', now());" >/dev/null 2>&1 \
        && printf '      anchored: %s\n' "$verb" || printf '      [!!] anchor INSERT FAILED: %s\n' "$verb"
    elif [ -n "$exists" ]; then
      printf '      (exists) %s\n' "$verb"
    else
      printf '      [!!] anchor CHECK FAILED (no count returned): %s\n' "$verb"
    fi
  }
  # id order: (1) pre-test verdicts, (2)(3) criterion briefs, (4) packet files + symlink — verdicts/briefs
  # BEFORE the packet hashes, so the record proves the spec froze only after two consecutive empty rounds.
  for rd in $(ls -d "$PRETEST"/round-* 2>/dev/null | sort -V); do
    n=$(basename "$rd"); _anchor "$RUN_LABEL PRE-TEST VERDICT ANCHOR (informational)" "$RELBASE/ambiguity-pretest/$n/VERDICT.md" "$rd/VERDICT.md"
  done
  _anchor "$RUN_LABEL CRITERION-BRIEF ANCHOR (informational)" "$RELBASE/criterion-brief-correctness.md" "$BUILD_DIR/criterion-brief-correctness.md"
  _anchor "$RUN_LABEL CRITERION-BRIEF ANCHOR (informational)" "$RELBASE/criterion-brief-conformance.md" "$BUILD_DIR/criterion-brief-conformance.md"
  find "$BUILD_DIR/packet" -type f | LC_ALL=C sort | while IFS= read -r f; do
    _anchor "$RUN_LABEL PACKET-FREEZE ANCHOR" "$RELBASE/${f#"$BUILD_DIR/"}" "$f"
  done
  # symlinks: find -type l are skipped by the -type f loop; anchor each by its TARGET path's sha (the link
  # carries no file bytes of its own). Uses the same inline dollar-quoting + fail-loud existence check.
  find "$BUILD_DIR/packet" -type l | LC_ALL=C sort | while IFS= read -r f; do
    tgt=$(readlink "$f"); tsha=$(printf '%s' "$tgt" | sha256sum | cut -d' ' -f1)
    verb="$RUN_LABEL PACKET-FREEZE ANCHOR (symlink): path=$RELBASE/${f#"$BUILD_DIR/"} target=$tgt target_sha256=$tsha commit=$HEAD"
    ex=$(psql -h $PGHOST -d harness -tAc "SELECT count(*) FROM acts.ruling WHERE verbatim LIKE \$V\$$RUN_LABEL PACKET-FREEZE ANCHOR (symlink): path=$RELBASE/${f#"$BUILD_DIR/"} target=$tgt target_sha256=$tsha%\$V\$;" 2>/dev/null)
    if [ "$ex" = "0" ]; then
      psql -h $PGHOST -d harness -q -v ON_ERROR_STOP=1 \
        -c "INSERT INTO acts.ruling (actor, verbatim, verbatim_sha256, binding_grade, regards, ts) VALUES ('apparatus:engineer', \$V\$$verb\$V\$, encode(digest(\$V\$$verb\$V\$,'sha256'),'hex'), 'informational', '$RUN_LABEL pre-registration', now());" >/dev/null 2>&1 \
        && printf '      anchored: %s\n' "$verb" || printf '      [!!] anchor INSERT FAILED: %s\n' "$verb"
    elif [ -n "$ex" ]; then printf '      (exists) %s\n' "$verb"
    else printf '      [!!] anchor CHECK FAILED: %s\n' "$verb"; fi
  done
}

arm() {
  echo "== §4 [$RUN_LABEL] ARM — EXECUTING (db $DB + pg_hba done by the maintainer; the rest is scriptable) =="
  mkdir -p "$WITNESS"; rc=0

  echo "-- (a) apply the kernel stack to $DB AS OWNER (idempotent) --"
  ddl_f_args=""; for f in $KERNEL_STACK; do ddl_f_args="$ddl_f_args -f $f"; done
  if psql -h $PGHOST -d $DB -q -v ON_ERROR_STOP=1 -v schema=public -v kern=kernel -v role=$RUN_ROLE -v rev1=$RUN_REV1 -v rev2=$RUN_REV2 \
       $ddl_f_args \
       > "$WITNESS/a-ddl-apply.log" 2>&1; then ok "kernel stack applied to $DB (arm-witness/a-ddl-apply.log)"
  else no "DDL apply FAILED — see arm-witness/a-ddl-apply.log"; rc=1; fi

  echo "-- (e) gate-journal registration check (fc22, finding 42) --"
  "$PY" "$INSTR/verify_gate_journal_registered.py" "$RUN_LABEL" >/dev/null 2>&1 \
    && ok "$RUN_LABEL registered in contemporaneity SESSIONS+GATE_JOURNALS (runs at close, not N/A)" \
    || { no "$RUN_LABEL NOT registered for contemporaneity"; rc=1; }

  echo "-- (b) provision ONE fresh apparatus secret (ruling 43: one fresh secret per run) --"
  # ONE shared secret for every intercepted writer; distinctness is per-invocation session/agent id in the
  # HMAC, NOT per-reviewer secrets (the trigger validates against the single kernel.stamp_secret row).
  have=$(psql -h $PGHOST -d $DB -tAc "SELECT count(*) FROM kernel.stamp_secret;" 2>/dev/null)
  if [ "$have" = "1" ] && [ "${ROTATE:-0}" != "1" ]; then
    ok "a secret is already provisioned for this run (kernel.stamp_secret: 1 row); not rotating (ROTATE=1 forces)"
  else
    mkdir -p "$(dirname "$SECRET_FILE")"; ( umask 077; openssl rand -hex 32 > "$SECRET_FILE" ); chmod 600 "$SECRET_FILE"
    # psql -c does NOT interpolate -v vars; the hex is [0-9a-f] so it inlines safely (no injection surface).
    HEX=$(cat "$SECRET_FILE")
    if psql -h $PGHOST -d $DB -q -v ON_ERROR_STOP=1 \
         -c "TRUNCATE kernel.stamp_secret;" \
         -c "INSERT INTO kernel.stamp_secret (secret) VALUES (decode('$HEX','hex'));" >/dev/null 2>&1; then
      ok "one fresh secret provisioned (file $SECRET_FILE [chmod 600, OUTSIDE repo]; DB kernel.stamp_secret)"
    else no "secret INSERT failed"; rc=1; fi
  fi

  echo "-- (b-neg) negative controls (banked to arm-witness/) --"
  psql -h $PGHOST -d $DB -c "SET ROLE $RUN_ROLE; SELECT secret FROM kernel.stamp_secret;" > "$WITNESS/b-neg-author-secret.log" 2>&1
  grep -qi "permission denied" "$WITNESS/b-neg-author-secret.log" \
    && ok "author $RUN_ROLE CANNOT read the secret (permission denied — banked)" \
    || { no "author secret negative-control did NOT deny"; rc=1; }
  for r in $RUN_REV1 $RUN_REV2; do
    psql -h $PGHOST -d $DB -c "SET ROLE $r; SELECT * FROM ledger LIMIT 1;" > "$WITNESS/b-neg-$r-ledger.log" 2>&1
    grep -qi "permission denied" "$WITNESS/b-neg-$r-ledger.log" \
      && ok "reviewer $r CANNOT SELECT ledger (permission denied — banked)" \
      || { no "reviewer $r ledger negative-control did NOT deny"; rc=1; }
  done

  echo "-- (c) wire the interception hook into the SUBJECT working-dir settings --"
  mkdir -p "$FENCED/.claude"; SUBJ_SET="$FENCED/.claude/settings.json"
  cat > "$SUBJ_SET" <<JSON
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [ { "type": "command",
          "command": "STAMP_SECRET=$SECRET_FILE python3 $HOOKS_DIR/stamp_intercept.py" } ] }
    ]
  }
}
JSON
  ok "subject hook wired: $SUBJ_SET"
  grep -qiE "WebFetch|WebSearch|mcp__" "$SUBJ_SET" && { no "subject settings names a web/mcp tool"; rc=1; } \
    || ok "subject settings enables no web-capable tool (§4f)"

  echo "-- (c2) deploy the SUBJECT-VISIBLE packet bytes into $FENCED (layout: CLAUDE.md, spec.md, --"
  echo "--      ledger_helper.md, fixtures/; kickoff.md + directive.txt are PASTED at kickoff, never placed) --"
  for f in CLAUDE.md spec.md ledger_helper.md; do
    cp "$BUILD_DIR/packet/$f" "$FENCED/$f"
    src=$(sha256sum "$BUILD_DIR/packet/$f" | cut -d' ' -f1); dst=$(sha256sum "$FENCED/$f" | cut -d' ' -f1)
    [ "$src" = "$dst" ] && ok "deployed $f (sha ${dst%????????????????????????????????????????????????} == frozen packet)" \
                        || { no "$f sha MISMATCH after deploy"; rc=1; }
  done
  rm -rf "$FENCED/fixtures"; cp -a "$BUILD_DIR/packet/fixtures" "$FENCED/fixtures"
  # verify every regular file byte-for-byte and the symlink's target against the frozen packet
  FIXBAD=0
  ( cd "$BUILD_DIR/packet/fixtures" && find . -type f -exec sha256sum {} + | LC_ALL=C sort ) > /tmp/arm-fix-src.$$
  ( cd "$FENCED/fixtures"           && find . -type f -exec sha256sum {} + | LC_ALL=C sort ) > /tmp/arm-fix-dst.$$
  diff -q /tmp/arm-fix-src.$$ /tmp/arm-fix-dst.$$ >/dev/null 2>&1 || FIXBAD=1
  [ "$(readlink "$FENCED/fixtures/sample/link-to-a")" = "$(readlink "$BUILD_DIR/packet/fixtures/sample/link-to-a")" ] || FIXBAD=1
  rm -f /tmp/arm-fix-src.$$ /tmp/arm-fix-dst.$$
  [ $FIXBAD -eq 0 ] && ok "fixtures/ deployed (every file sha + the symlink target match the frozen packet)" \
                    || { no "fixtures/ deploy diverges from the frozen packet"; rc=1; }
  # the fenced dir must contain NOTHING beyond the deployed packet + .claude (a stray byte = unfrozen subject-visible surface)
  STRAY=$(cd "$FENCED" && find . -mindepth 1 \
            -not -path './.claude*' -not -name CLAUDE.md -not -name spec.md -not -name ledger_helper.md \
            -not -path './fixtures*' | head -5)
  [ -z "$STRAY" ] && ok "no stray bytes in $FENCED beyond the packet + .claude" \
                  || { no "STRAY subject-visible bytes present: $STRAY"; rc=1; }

  echo "-- (d) anchor the freeze into acts.ruling (e16 pattern; id order; idempotent) --"
  anchor_freeze

  echo
  echo "-- (f) THE DELIVERY SET (final output; finding 43 foreclosure) --"
  delivery_set || rc=1

  echo
  echo "== EXECUTED (rc=$rc). Residual steps that are NOT mine to run: =="
  echo "  [FRAME]    Subject kickoff — the SUBJECT session is HUMAN-operated (the auditor is not the subject,"
  echo "             consult-27 FRAME). Launch a fresh Claude Code session in cwd $FENCED and paste the"
  echo "             DELIVERY SET printed above — the whole block between the BEGIN/END markers, byte-frozen"
  echo "             from the packet. Do not retype or trim it. Schema + secret + hook + anchors are in place."
  echo "  [POST-RUN] close-1 (e17-style) after the subject is done; spawn K=2 fresh criterion reviewers"
  echo "             (distinct invocations -> distinct stamp_agent) as $RUN_REV1/$RUN_REV2 with the hook wired, each"
  echo "             handed ONLY its lens brief + final artifact + spec + fixtures; adjudicate every finding"
  echo "             (adjudicate_repro.py); then close-2 (review_fixpoint active) and record the flip."
  echo "  [RULING43] retain this run's secret in the sealed store (G12-logged access, I12 declaration) AFTER"
  echo "             the run — the sealed-store mechanism is still under design in the engine increment (OQ6);"
  echo "             not improvised here."
  return $rc
}

# THE DELIVERY SET (finding 43 foreclosure; check-line id `arming-delivery-set`). The arming automation's
# FINAL output: the exact message(s) the human pastes to the subject, in order, byte-frozen from the
# packet — never described in prose, never retyped. The e18 run's set was ONE message: kickoff.md then
# directive.txt (kickoff's own frame text says "the directive that follows this frame", so the directive
# follows IN THE SAME PASTE) — this generic emitter still assumes that two-item shape (kickoff.md,
# directive.txt); a future run with a different delivery shape is a script change, not a config knob (the
# task scope here is parameterizing e18/qbx tokens, not the delivery-set item list). The e18 run's own
# deviation (finding 43): three prose tellings of what to paste disagreed and the run got kickoff-only —
# this emitter replaces every prose telling. Both-polarity: green emits the byte-frozen block + per-item
# shas; a packet missing a frozen delivery item REFUSES (exit 1) naming it — never a silent partial set.
delivery_set() {
  _fail=0
  for item in kickoff.md directive.txt; do
    if [ ! -s "$BUILD_DIR/packet/$item" ]; then
      printf '  [!! ] DELIVERY SET REFUSED: frozen delivery item %s is missing or empty in the packet\n' "$item"
      _fail=1
    fi
  done
  [ $_fail -eq 0 ] || return 1
  echo "  paste the following as ONE message to the fresh subject session (kickoff frame + directive):"
  for item in kickoff.md directive.txt; do
    printf '  item %-14s sha256=%s bytes=%s\n' "$item" "$(sha256sum "$BUILD_DIR/packet/$item" | cut -c1-16)" "$(wc -c < "$BUILD_DIR/packet/$item")"
  done
  echo "----8<---- DELIVERY SET BEGIN (message 1 of 1) ----8<----"
  cat "$BUILD_DIR/packet/kickoff.md"
  echo
  cat "$BUILD_DIR/packet/directive.txt"
  echo "----8<---- DELIVERY SET END ----8<----"
  return 0
}

case "${1:-}" in
  --verify)       verify ;;
  --arm)          arm ;;
  --delivery-set) delivery_set ;;
  *) echo "usage: arm.sh <build-dir> --verify | --arm | --delivery-set"; exit 2 ;;
esac
