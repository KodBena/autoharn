#!/usr/bin/env bash
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T07:10:40Z
#   last-change: 2026-07-18T16:50:00Z
#   contributors: a857c93d/main, ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

# rehearse-from-origin.sh -- the external-rehearsal-register-gate mechanization (RCA row 909's
# rule; ledger item `external-rehearsal-register-gate`; row 928's repair this rehearsal exists to
# keep proven). Answers ONE question a same-host rehearsal structurally cannot: "does a REAL
# STRANGER, with nothing but a fresh clone of the PUBLIC URL and a database they name themselves,
# get a working first walkthrough?" -- not "does it work on this machine, which still holds
# leftover config/checkouts from before the defect this rehearsal is guarding against."
#
# THE SAME-HOST ILLUSION IT KILLS (row 909's own words): every verifying agent in the debacle
# chain ran on the SAME machine whose disk still held a file (deployment.json.example) the git
# tree had already lost. A naive presence check returns true regardless of git-tracking state.
# This script's env jail makes that structurally impossible: nothing is readable except what the
# fresh clone itself contains, the system toolchain, and the one scratch database the operator
# names -- no $HOME config, no ambient deployment.json, no host-resident autoharn checkout on any
# exec path.
#
# USAGE:
#   bootstrap/rehearse-from-origin.sh <repo-url> [--keep] [--schema-suffix <name>]
#
#   <repo-url>        the PUBLIC clone URL to rehearse (e.g. https://github.com/KodBena/autoharn.git).
#                      Cloned FRESH into a scratch dir -- never a local path, never this checkout.
#   --keep             do not tear down the scratch dir or drop the scratch schema/kern/role
#                      afterward (for post-mortem inspection). Default: always tears down.
#   --schema-suffix     override the scratch-name suffix (default: a timestamp) used to derive
#                      schema/kern/role names, all of which end in `_scratch` per this project's
#                      own scratch-naming convention (README.md's Configuration table) so they
#                      can never collide with a curated target name.
#
# REQUIRED OPERATOR-SUPPLIED ENVIRONMENT (the walkthrough's own PG* vars -- read from the CALLING
# environment, never guessed, never defaulted to a literal host/IP; this is the "operator NAMES
# the scratch db" half of the env jail -- ADR-0002's standing rule against guessed defaults):
#   PGHOST        the Postgres host the scratch db is reachable on.
#   PGDATABASE    the scratch database (must already exist and be reachable -- this script never
#                 runs CREATE DATABASE, same posture as the README's own step 1: "None of the
#                 four commands does any of this for you").
# OPTIONAL, passed through the jail unchanged if set: PGUSER, PGPASSWORD, PGPORT.
#
# WHAT THIS DOES, in order, entirely inside an env-jailed subshell (see run_jailed() below --
# the jail is now constructed BEFORE anything touches the network, night-build-defect-repair
# DEFECT 3: the clone used to run untraced, before the jail existed, letting an ambient
# ~/.gitconfig url.insteadOf rewrite substitute a local decoy for the public repo unwitnessed):
#   1. Fresh `git clone <repo-url>` into a scratch dir, INSIDE the jail (HOME=throwaway,
#      GIT_CONFIG_GLOBAL/SYSTEM=/dev/null, traced), immediately followed by an ASSERTION that the
#      cloned remote's resolved origin URL equals the requested <repo-url> exactly -- itself
#      checked under the same neutralized config, so the check cannot be fooled by what it is
#      checking for. A mismatch REFUSES loudly; nothing further runs.
#   2. bootstrap/new-project.sh --pin submodule --pin-url <repo-url> (README section 1, step 1)
#      -- deliberately --pin-url <repo-url>, NOT the default on-disk path, so the submodule this
#      creates is fetched from the real remote, exactly what a real stranger would get.
#   3. Apply kernel/lineage/high_watermark_1.sql (README section 1's "two manual steps", #1a).
#   4. `./migrate` to carry the base to the current lineage head (README section 1's #1b).
#   5. Provision the stamp secret (README section 1's "two manual steps", #2; commands verbatim
#      from bootstrap/templates/HOOKS.md.tmpl's own copy-paste block).
#   6. A REAL LEDGER WRITE (`./led decision ...`) inside the freshly deployed project -- the
#      walkthrough is not "witnessed" until it produces a real row, not just a scaffold.
#   7. gates/cut_probe_inventory.py run against the CLONE (step 1's tree) -- the regression-probe
#      leg (RCA row 909's "propagation" half): every shipped-fix class gets one probe line there;
#      this call is that inventory's standing wire-in for a rehearsal/cut context.
#   8. An exec-trace assertion over the WHOLE jailed subshell (steps 1-6, the clone now included):
#      refuses loudly if any traced path escaped the clone/scratch-HOME/system-toolchain/named-
#      scratch-db envelope.
#   9. Teardown (schema/kern/role dropped, scratch dir removed) unless --keep.
#
# EXIT: 0 only if every step above passed AND the trace assertion found no escape AND the probe
# inventory passed. Non-zero and loud otherwise -- this script's whole purpose is to refuse
# instead of rounding a partial pass up to "rehearsal green" (row 909's own diagnosis of how the
# debacle's reports went wrong).
set -euo pipefail

SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTOHARN_ROOT="$(cd "$SELF/.." && pwd)"

# ------------------------------------------------------------------------------------------------
# 0. ARGS
# ------------------------------------------------------------------------------------------------
REPO_URL=""
KEEP=0
SUFFIX="$(date -u +%Y%m%d%H%M%S)"
while [ $# -gt 0 ]; do
    case "$1" in
        --keep) KEEP=1; shift ;;
        --schema-suffix) SUFFIX="$2"; shift 2 ;;
        -h|--help)
            sed -n '2,73p' "$0" | sed 's/^# \{0,1\}//'
            exit 0 ;;
        -*)
            echo "rehearse-from-origin.sh: unrecognized flag $1. Nothing was touched." >&2
            exit 2 ;;
        *)
            if [ -n "$REPO_URL" ]; then
                echo "rehearse-from-origin.sh: one positional <repo-url> only, got a second: $1. Nothing was touched." >&2
                exit 2
            fi
            REPO_URL="$1"; shift ;;
    esac
done
if [ -z "$REPO_URL" ]; then
    echo "usage: bootstrap/rehearse-from-origin.sh <repo-url> [--keep] [--schema-suffix <name>]" >&2
    exit 2
fi
case "$REPO_URL" in
    /*|.*|~*)
        echo "rehearse-from-origin.sh: REFUSED -- <repo-url> ($REPO_URL) looks like a local path," >&2
        echo "  not a fetchable remote. This script exists precisely to defeat the local-path" >&2
        echo "  same-host illusion (RCA row 909/903) -- pass a real https://... or git@... URL." >&2
        exit 1 ;;
esac

if [ -z "${PGHOST:-}" ] || [ -z "${PGDATABASE:-}" ]; then
    echo "rehearse-from-origin.sh: REFUSED -- PGHOST and PGDATABASE must both be set in the" >&2
    echo "  calling environment (the operator NAMES the scratch db; this script never guesses" >&2
    echo "  or defaults one -- ADR-0002). PGUSER/PGPASSWORD/PGPORT are passed through if set." >&2
    exit 2
fi

# ------------------------------------------------------------------------------------------------
# 1. SCRATCH LAYOUT
# ------------------------------------------------------------------------------------------------
SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/rehearse-from-origin.XXXXXX")"
CLONE="$SCRATCH/clone"
DEST="$SCRATCH/deployed"
JAILHOME="$SCRATCH/home"
TRACE_LOG="$SCRATCH/xtrace.log"
mkdir -p "$JAILHOME"

# scratch names -- all end in "_scratch" (README.md Configuration table's own carve-out pattern),
# so they can never collide with a curated target name (toy, nla, e15-e18) or the s\d+ convention.
SCHEMA="rehearse_${SUFFIX}_scratch"
KERN="rehearse_${SUFFIX}_kernel_scratch"
ROLE="rehearse_${SUFFIX}_rw"

# --- STRICT CHARACTER ALLOWLIST on every name that becomes SQL text ----------------------------
# ADR-0012's 2026-07-18 amendment ("The interpreter boundary -- a value never spliced into program
# text") + ADR-0000's same-day Rule 2(a) amendment (ledger row 1637, fixed first in
# bootstrap/teardown-world.sh commit 0ce5055): SUFFIX is operator-supplied (--schema-suffix), and
# SCHEMA/KERN/ROLE below are built from it and spliced into psql SQL text (cleanup()'s DROP
# statements). Checked on the DERIVED names, not just SUFFIX, since that is what actually reaches
# SQL text and is the honest, checkable invariant (mirrors teardown-world.sh's own posture).
for _name in "$SCHEMA" "$KERN" "$ROLE"; do
    case "$_name" in
        ''|*[!A-Za-z0-9_]*)
            echo "rehearse-from-origin.sh: REFUSED -- '$_name' contains characters outside the" >&2
            echo "  allowlist for a schema/kernel/role name (letters, digits, underscore only)." >&2
            echo "  --schema-suffix '$SUFFIX' produced this. Nothing was touched." >&2
            exit 2
            ;;
    esac
done
unset _name

echo "== rehearse-from-origin: scratch dir $SCRATCH =="
echo "   clone <- $REPO_URL"
echo "   schema=$SCHEMA kern=$KERN role=$ROLE (db=$PGDATABASE host=$PGHOST)"

cleanup() {
    if [ "$KEEP" = 1 ]; then
        echo "== rehearse-from-origin: --keep given, leaving $SCRATCH and scratch schema/kern/role in place =="
        return
    fi
    echo "== rehearse-from-origin: tearing down =="
    # SQL text fed on stdin, never via -c (psql's :"var" identifier-bind substitution is a silent
    # no-op under -c, verified live -- same fix shape as bootstrap/teardown-world.sh commit 0ce5055).
    # One psql invocation, all three statements piped in together, ON_ERROR_STOP=0 preserved --
    # same best-effort semantics the original three -c flags on one invocation had.
    printf '%s\n' \
        'DROP SCHEMA IF EXISTS :"schema" CASCADE;' \
        'DROP SCHEMA IF EXISTS :"kern" CASCADE;' \
        'DROP ROLE IF EXISTS :"role";' \
        | PGPASSWORD="${PGPASSWORD:-}" psql -h "$PGHOST" -d "$PGDATABASE" ${PGUSER:+-U "$PGUSER"} \
            -v ON_ERROR_STOP=0 -q -v schema="$SCHEMA" -v kern="$KERN" -v role="$ROLE" \
        >/dev/null 2>&1 || echo "   (teardown SQL best-effort -- schema/kern/role may already be gone)"
    rm -rf "$SCRATCH"
    echo "   scratch dir removed."
}
trap cleanup EXIT

# ------------------------------------------------------------------------------------------------
# 2. THE ENV JAIL, defined FIRST (night-build-defect-repair DEFECT 3, fresh-context verifier
#    finding: the clone used to run BEFORE this jail existed, untraced -- an ambient
#    ~/.gitconfig url.insteadOf rewrite could substitute a local decoy for the public repo, and
#    the clone step itself was invisible to the trace assertion in step 5 below, since it ran
#    before TRACE_LOG had anything appended to it. The verifier proved this live. The jail must
#    exist before ANYTHING touches the network, not just before the walkthrough steps.)
#
#    env -i with a MINIMAL allowlist:
#      PATH                 -- the system toolchain only (git/psql/python3/openssl), never this
#                              operator's full PATH (which could resolve a shadowing binary).
#      PG{HOST,DATABASE,USER,PASSWORD,PORT} -- the walkthrough's own connection target, exactly
#                              as the operator named it, nothing more.
#      HOME=$JAILHOME       -- a throwaway dir inside the scratch tree, empty at start; no
#                              ambient ~/.pgpass, ~/.gitconfig, ~/.claude/, etc. is readable
#                              unless THIS script itself puts something there.
#      GIT_CONFIG_GLOBAL=/dev/null / GIT_CONFIG_SYSTEM=/dev/null -- defense in depth alongside
#                              HOME=$JAILHOME: even if this host's git were built to consult a
#                              config path outside $HOME (or GIT_CONFIG_GLOBAL/SYSTEM somehow
#                              survived from the calling shell -- env -i already wipes it, this
#                              is belt-and-braces), a url.insteadOf rewrite has nowhere left to
#                              live that this jail would read.
#      GIT_AUTHOR_*/GIT_COMMITTER_* -- new-project.sh's --pin submodule step commits inside
#                              <dest-dir>; a throwaway git identity avoids depending on this
#                              operator's real ~/.gitconfig (which HOME=$JAILHOME already hides).
#    Every command in the walkthrough runs inside this jail, INCLUDING the initial clone (step 3
#    below, now moved inside). `sh -x` traces every command to TRACE_LOG (the same evidentiary
#    convention row 928's own from-origin witness used: "sh -x ... traced entirely inside the
#    clone path, zero <host-path> occurrences") -- the clone is no longer exempt from that trace.
# ------------------------------------------------------------------------------------------------
SYSTEM_PATH="/usr/local/bin:/usr/bin:/bin"

run_jailed() {
    env -i \
        PATH="$SYSTEM_PATH" \
        HOME="$JAILHOME" \
        GIT_CONFIG_GLOBAL=/dev/null \
        GIT_CONFIG_SYSTEM=/dev/null \
        PGHOST="$PGHOST" \
        PGDATABASE="$PGDATABASE" \
        ${PGUSER:+PGUSER="$PGUSER"} \
        ${PGPASSWORD:+PGPASSWORD="$PGPASSWORD"} \
        ${PGPORT:+PGPORT="$PGPORT"} \
        GIT_AUTHOR_NAME="rehearse-from-origin" GIT_AUTHOR_EMAIL="rehearse@localhost" \
        GIT_COMMITTER_NAME="rehearse-from-origin" GIT_COMMITTER_EMAIL="rehearse@localhost" \
        bash -x -c "$1" 2>>"$TRACE_LOG"
}

# run_jailed_file: same jail as run_jailed(), but executes a SCRIPT FILE rather than a -c string --
# used exactly once, for step 4 below, so KERN (an allowlist-validated but still operator-derived
# name) reaches its SQL text as a bound psql -v identifier rather than via nested shell-string
# splicing through run_jailed's own "$1" (ADR-0012's 2026-07-18 amendment: the value crosses as
# data, via KERN/DEST/HEX exported as plain jail env vars, never spliced into the -c argument
# text). PGHOST/PGDATABASE are already in the base env -i list above.
run_jailed_file() {
    env -i \
        PATH="$SYSTEM_PATH" \
        HOME="$JAILHOME" \
        GIT_CONFIG_GLOBAL=/dev/null \
        GIT_CONFIG_SYSTEM=/dev/null \
        PGHOST="$PGHOST" \
        PGDATABASE="$PGDATABASE" \
        ${PGUSER:+PGUSER="$PGUSER"} \
        ${PGPASSWORD:+PGPASSWORD="$PGPASSWORD"} \
        ${PGPORT:+PGPORT="$PGPORT"} \
        KERN="$KERN" \
        DEST="$DEST" \
        bash -x "$1" 2>>"$TRACE_LOG"
}

# ------------------------------------------------------------------------------------------------
# 3. FRESH CLONE OF THE PUBLIC URL, INSIDE THE JAIL (never a local path, never ambient config --
#    the same-host-illusion killer, now closed at the clone step itself).
# ------------------------------------------------------------------------------------------------
echo "== rehearse-from-origin: cloning $REPO_URL inside the env jail =="
run_jailed "git clone --quiet '$REPO_URL' '$CLONE'"
CLONE_SHA="$(git -C "$CLONE" rev-parse HEAD)"
echo "   cloned $REPO_URL @ $CLONE_SHA into $CLONE"

# ASSERTION: the cloned remote's resolved origin URL equals the requested public URL, EXACTLY --
# checked with the identical jail neutralization (GIT_CONFIG_GLOBAL/SYSTEM=/dev/null, HOME=
# $JAILHOME) the clone itself ran under, so this check cannot be fooled by the same mechanism it
# is verifying against. If a url.insteadOf rewrite (or any other config substitution) got through
# anyway, this refuses loudly instead of silently proceeding against a decoy.
RESOLVED_URL="$(env -i PATH="$SYSTEM_PATH" HOME="$JAILHOME" \
    GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null \
    git -C "$CLONE" remote get-url origin)"
if [ "$RESOLVED_URL" != "$REPO_URL" ]; then
    echo "rehearse-from-origin: REFUSED -- the cloned remote's resolved origin URL" >&2
    echo "  ('$RESOLVED_URL') does not match the requested public URL ('$REPO_URL')." >&2
    echo "  This is exactly the same-host illusion RCA rows 909/928 name: a url.insteadOf" >&2
    echo "  rewrite (or similar git config substitution) can swap a local decoy in for the" >&2
    echo "  public repo. Nothing further was touched -- the clone is in the scratch dir, about" >&2
    echo "  to be torn down by this script's own cleanup trap." >&2
    exit 1
fi
echo "   origin URL verified: $RESOLVED_URL (matches the requested URL exactly, jail-checked)"

echo "== rehearse-from-origin: walkthrough (README.md section 1) inside env jail =="

echo "-- step 1: new-project.sh --pin submodule --pin-url $REPO_URL --"
run_jailed "cd '$CLONE' && bootstrap/new-project.sh '$DEST' --db '$PGDATABASE' --host '$PGHOST' \
    --schema '$SCHEMA' --kern '$KERN' --role '$ROLE' --pin submodule --pin-url '$REPO_URL'"

echo "-- step 2: apply kernel/lineage/high_watermark_1.sql --"
run_jailed "psql -h '$PGHOST' -d '$PGDATABASE' -v ON_ERROR_STOP=1 \
    -v schema='$SCHEMA' -v kern='$KERN' -v role='$ROLE' \
    -f '$CLONE/kernel/lineage/high_watermark_1.sql'"

echo "-- step 3: ./migrate to lineage head (typed confirmation piped: MIGRATE $SCHEMA) --"
run_jailed "cd '$CLONE' && printf 'MIGRATE %s\n' '$SCHEMA' | ./migrate '$DEST'"

echo "-- step 4: provision the stamp secret (bootstrap/templates/HOOKS.md.tmpl's own commands) --"
# Written to a FILE with a quoted heredoc (no expansion at write time) so KERN reaches psql as a
# bound -v identifier (:"kern") rather than being spliced by THIS script's own shell into a -c/-x
# string -- SQL text is fed on stdin, never -c (psql's :"var" substitution is a silent no-op under
# -c, verified live -- same fix shape as bootstrap/teardown-world.sh commit 0ce5055). KERN/DEST
# reach the jail as plain env vars (run_jailed_file's own env -i list above), never as text baked
# into the script by this outer shell.
STEP4_SCRIPT="$SCRATCH/step4-stamp-secret.sh"
cat > "$STEP4_SCRIPT" <<'INNERSCRIPT'
set -e
mkdir -p "$DEST/.claude/secrets"
HEX=$(openssl rand -hex 32)
printf '%s\n' 'TRUNCATE :"kern".stamp_secret;' \
    | psql -h "$PGHOST" -d "$PGDATABASE" -q -v ON_ERROR_STOP=1 -v kern="$KERN"
printf '%s\n' "INSERT INTO :\"kern\".stamp_secret (secret) VALUES (decode(:'hex','hex'));" \
    | psql -h "$PGHOST" -d "$PGDATABASE" -q -v ON_ERROR_STOP=1 -v kern="$KERN" -v hex="$HEX"
printf '%s\n' "SELECT encode(secret,'hex') FROM :\"kern\".stamp_secret;" \
    | psql -h "$PGHOST" -d "$PGDATABASE" -tA -v kern="$KERN" \
    > "$DEST/.claude/secrets/stamp_secret.hex"
chmod 600 "$DEST/.claude/secrets/stamp_secret.hex"
INNERSCRIPT
run_jailed_file "$STEP4_SCRIPT"

echo "-- step 5: a REAL ledger write, then read it back --"
STAMP_TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
run_jailed "cd '$DEST' && ./led decision \"external-rehearsal-register-gate: fresh-origin rehearsal of $REPO_URL @ $CLONE_SHA, env-jailed, reached a real ledger write at $STAMP_TS\""
run_jailed "cd '$DEST' && ./led --recent 1"

echo "== rehearse-from-origin: walkthrough complete -- real ledger write witnessed =="

# ------------------------------------------------------------------------------------------------
# 4. REGRESSION-PROBE INVENTORY, wired in against the CLONE (the origin tree this rehearsal just
#    proved deployable) -- gates/cut_probe_inventory.py, item external-rehearsal-register-gate's
#    other declared artifact.
# ------------------------------------------------------------------------------------------------
echo "== rehearse-from-origin: regression-probe inventory against the clone =="
PROBE_STATUS=0
python3 "$AUTOHARN_ROOT/gates/cut_probe_inventory.py" "$CLONE" || PROBE_STATUS=$?

# ------------------------------------------------------------------------------------------------
# 5. EXEC-TRACE ASSERTION -- no traced path escapes the clone/scratch envelope except the system
#    toolchain and the named scratch db. The `sh -x` log lines every command with its expanded
#    arguments; a real escape shows up as an absolute path outside SCRATCH that is not one of the
#    system toolchain directories. This is the same convention row 928's own from-origin witness
#    used ("sh -x ... traced entirely inside the clone path, zero <host-path> occurrences") --
#    made mechanical and refusing here instead of a one-off eyeball grep.
# ------------------------------------------------------------------------------------------------
echo "== rehearse-from-origin: exec-trace assertion =="
TRACE_STATUS=0
if [ -s "$TRACE_LOG" ]; then
    # Extract every absolute path literal appearing in the trace, then flag any that is outside
    # SCRATCH and outside the system toolchain dirs. This host's own real HOME and this rehearsal
    # script's own AUTOHARN_ROOT are the two concrete escape hazards RCA row 909/903 named by
    # name -- checked for explicitly, in addition to the general sweep.
    ESCAPES="$(grep -oE '(/[A-Za-z0-9_.@:+-]+)+' "$TRACE_LOG" \
        | grep -v "^$SCRATCH" \
        | grep -vE '^(/usr(/local)?|/bin|/sbin|/lib(64)?|/etc|/proc|/dev|/tmp)(/|$)' \
        || true)"
    if echo "$ESCAPES" | grep -qF "$AUTOHARN_ROOT"; then
        echo "  ESCAPE: the trace references this rehearsal's OWN checkout ($AUTOHARN_ROOT)" >&2
        echo "$ESCAPES" | grep -F "$AUTOHARN_ROOT" >&2
        TRACE_STATUS=1
    fi
    if [ -n "${HOME:-}" ] && echo "$ESCAPES" | grep -qF "$HOME"; then
        echo "  ESCAPE: the trace references the real operator HOME ($HOME)" >&2
        echo "$ESCAPES" | grep -F "$HOME" >&2
        TRACE_STATUS=1
    fi
    OTHER_ESCAPES="$(echo "$ESCAPES" | grep -vF "$AUTOHARN_ROOT" | grep -vF "${HOME:-\x00}" || true)"
    if [ -n "$OTHER_ESCAPES" ]; then
        echo "  NOTE: other absolute-path literals outside the toolchain/scratch envelope (review" >&2
        echo "  by hand -- may be benign, e.g. a URL or a hostname that happens to look path-shaped):" >&2
        echo "$OTHER_ESCAPES" | sort -u | sed 's/^/    /' >&2
    fi
    if [ "$TRACE_STATUS" = 0 ]; then
        echo "   trace clean: no reference to $AUTOHARN_ROOT or the real operator HOME in $(wc -l < "$TRACE_LOG") traced lines."
    fi
else
    echo "  REFUSED -- the trace log is empty; the jailed walkthrough produced no trace, which" >&2
    echo "  means this assertion cannot be made at all -- treated as a failure, never as a pass" >&2
    echo "  by omission." >&2
    TRACE_STATUS=1
fi

# ------------------------------------------------------------------------------------------------
# 6. VERDICT
# ------------------------------------------------------------------------------------------------
echo
echo "== rehearse-from-origin: SUMMARY =="
echo "   walkthrough (steps 1-5): WITNESSED (real ledger write above)"
echo "   probe inventory vs clone: $([ "$PROBE_STATUS" = 0 ] && echo PASS || echo FAIL)"
echo "   exec-trace assertion: $([ "$TRACE_STATUS" = 0 ] && echo PASS || echo FAIL)"

if [ "$PROBE_STATUS" != 0 ] || [ "$TRACE_STATUS" != 0 ]; then
    echo "rehearse-from-origin: FAILED -- see PROBE and/or TRACE detail above." >&2
    exit 1
fi
echo "rehearse-from-origin: ALL CHECKS PASS."
exit 0
