#!/bin/sh
# convert-to-submodule.sh -- the CONVERSION path for an EXISTING live-exec-coupled deployment
# (tracker item deployment-live-exec-coupling, design/ORCH-DEPLOYMENT-PINNING.md's "Migration path
# for EXISTING deployments"; maintainer commission 2026-07-14 late: "git submodule DEPLOYMENT must
# be IDIOT-PROOF"). ~/ent is the motivating case named in that design note, but this script is NOT
# run against ~/ent by this build -- ~/ent carries a live session (CLAUDE.md: "Never modify hooks/
# or a user project while a live session runs there"), and its own conversion is the maintainer's
# act, later, once that session ends.
#
# What this does, in one command: takes a deployment directory scaffolded by
# bootstrap/new-project.sh (or bootstrap/track-work.sh -- same shim shape) that today `exec`s
# autoharn's operator-verb templates and hooks LIVE out of a shared checkout, and converts it to
# the pinned shape (design/ORCH-DEPLOYMENT-PINNING.md's "submodule-as-default"): adds autoharn as
# a git submodule at <deployment>/.autoharn pinned to the EXACT commit the deployment was already
# running (never autoharn's current tip -- conversion is not conflated with an upgrade), repoints
# the operator-verb shims (SHIM_VERBS_ALL, bootstrap/shim-verbs.sh) AND the hook wiring in .claude/settings.json at that pinned copy,
# verifies every verb still answers, and records the act.
#
# Usage:
#   bootstrap/convert-to-submodule.sh <deployment-dir> [--pin-url <url>] [--yes]
#
#   <deployment-dir>  the existing scaffolded deployment to convert (must already have a
#                     deployment.json and the operator-verb shims, live-exec today).
#   --pin-url <url>   the submodule remote (default: THIS autoharn checkout's own on-disk path --
#                     works with no network access, portable on this machine only; pass a real git
#                     remote for a submodule another machine can also fetch).
#   --yes             skip the typed confirmation prompt (for scripted/CI use; the confirmation
#                     exists so an interactive operator sees exactly what will change before it
#                     does -- see the printed summary below).
#
# REFUSES LOUDLY, and touches NOTHING, on any of:
#   - <deployment-dir> missing deployment.json, or it fails to parse (filing/deployment_record.py).
#   - the required operator-verb shims (SHIM_VERBS) are missing, malformed, already pinned (already has .autoharn), or
#     DISAGREE with each other about which autoharn checkout they exec (a pre-existing hazard this
#     script will not paper over by picking one arbitrarily).
#   - the discovered autoharn checkout is dirty or its commit cannot be determined (nothing
#     reproducible to pin to).
#   - a LIVE CLAUDE CODE SESSION appears to be running against <deployment-dir> (bootstrap/
#     live_session_check.py, a best-effort /proc scan -- CLAUDE.md's standing rule, restated by
#     this design note's own migration section: "migrating a deployment mid-session is itself an
#     act that needs to not race a live operator"). Other processes merely residing in the
#     directory (a shell, an editor) are listed as informational, non-blocking output only
#     (2026-07-15 maintainer-ratified narrowing, ledger row 1055 -- see live_session_check.py's
#     module docstring for the REFUSE-class/WARN-class matching rule).
#   - the typed confirmation is not given (unless --yes).
#
# Prints exactly what you should see after each step; every refusal names the fix.
set -eu

usage() {
    echo "usage: $0 <deployment-dir> [--pin-url <url>] [--yes]" >&2
    exit 2
}

[ $# -ge 1 ] || usage
DEST="$1"; shift
PIN_URL=""
YES=0
while [ $# -gt 0 ]; do
    case "$1" in
        --pin-url) PIN_URL="$2"; shift 2 ;;
        --yes) YES=1; shift ;;
        *) echo "unrecognized argument: $1" >&2; usage ;;
    esac
done

SELF_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$HOME/w/vdc/venvs/generic/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"

# The single-home shim verb set (tracker item submodule-shim-set-drift, ledger row 1182) --
# this script used to hand-maintain its own 8-verb list (9 with doctor conditionalized),
# independently drifted from new-project.sh's own scaffold loop (the authority) and silently
# missing asof-export entirely. Sourced here instead.
. "$SELF_ROOT/bootstrap/shim-verbs.sh"

if [ ! -d "$DEST" ]; then
    echo "convert-to-submodule.sh: $DEST is not a directory" >&2
    exit 1
fi
DEST="$(cd "$DEST" && pwd)"

echo "== convert-to-submodule: $DEST =="

# --- 1. deployment.json must exist and parse -------------------------------------------------
if [ ! -f "$DEST/deployment.json" ]; then
    echo "convert-to-submodule.sh: $DEST/deployment.json not found -- this does not look like a" >&2
    echo "                         bootstrap/new-project.sh (or track-work.sh) deployment. Nothing" >&2
    echo "                         touched." >&2
    exit 1
fi
if ! "$PY" - "$SELF_ROOT" "$DEST/deployment.json" <<'PYEOF' >/dev/null
import sys
sys.path.insert(0, sys.argv[1] + "/filing")
from deployment_record import load_deployment
load_deployment(sys.argv[2])
PYEOF
then
    echo "convert-to-submodule.sh: $DEST/deployment.json failed to parse (see error above) --" >&2
    echo "                         nothing touched." >&2
    exit 1
fi
echo "-- deployment.json: OK --"

# --- 2. already pinned? ------------------------------------------------------------------------
if [ -e "$DEST/.autoharn" ]; then
    echo "convert-to-submodule.sh: $DEST/.autoharn already exists -- this deployment looks ALREADY" >&2
    echo "                         PINNED. If you meant to take a newer autoharn, use" >&2
    echo "                         bootstrap/upgrade-submodule.sh $DEST <new-sha> instead." >&2
    exit 1
fi

# --- 3. discover the CURRENT live-exec AUTOHARN_ROOT from the shims, and confirm agreement ---
# `doctor` (SHIM_VERBS_OPTIONAL, bootstrap/shim-verbs.sh -- added after this script's original
# nine) is deliberately OPTIONAL here, never REQUIRED: a deployment scaffolded before `./doctor`
# existed legitimately has no such shim, and hard-requiring it would refuse conversion for every
# pre-existing deployment on this fix's account. When present, it is folded into $VERBS below so
# it gets discovered/repointed/committed exactly like the required set -- absent, it is silently
# skipped, same posture as everywhere else in this repo that treats `doctor` as
# additive-and-optional to already-scaffolded worlds. Every OTHER verb in SHIM_VERBS is required
# (unlike before this fix, this now includes asof-export -- see bootstrap/shim-verbs.sh's header).
VERBS="$SHIM_VERBS"
[ -f "$DEST/doctor" ] && VERBS="$VERBS doctor"
DISCOVERED=""
for v in $VERBS; do
    shim="$DEST/$v"
    if [ ! -f "$shim" ]; then
        echo "convert-to-submodule.sh: $shim not found -- this deployment is missing an expected" >&2
        echo "                         operator-verb shim; not a live-exec scaffold this script" >&2
        echo "                         recognizes. Nothing touched." >&2
        exit 1
    fi
    # Every shim is `exec env PICKUP_DEPLOYMENT=... <ROOT>/bootstrap/templates/<verb>.tmpl "$@"`
    # (bootstrap/new-project.sh's own shim-writing loop) -- extract <ROOT>.
    root="$(sed -n "s|.*exec env PICKUP_DEPLOYMENT=\"[^\"]*\" \(.*\)/bootstrap/templates/$v\.tmpl.*|\1|p" "$shim" | head -1)"
    if [ -z "$root" ]; then
        echo "convert-to-submodule.sh: $shim does not match the expected shim shape (exec ...)/" >&2
        echo "                         bootstrap/templates/$v.tmpl ...) -- refusing to guess." >&2
        echo "                         Nothing touched." >&2
        exit 1
    fi
    if [ -z "$DISCOVERED" ]; then
        DISCOVERED="$root"
    elif [ "$root" != "$DISCOVERED" ]; then
        echo "convert-to-submodule.sh: the operator-verb shims DISAGREE about which autoharn" >&2
        echo "                         checkout they exec -- '$v' points at '$root' but an earlier" >&2
        echo "                         verb pointed at '$DISCOVERED'. This is a pre-existing hazard" >&2
        echo "                         in $DEST that predates this script; fix it by hand (make" >&2
        echo "                         every shim agree) before converting. Nothing touched." >&2
        exit 1
    fi
done
if [ ! -d "$DISCOVERED" ]; then
    echo "convert-to-submodule.sh: the discovered autoharn checkout '$DISCOVERED' does not exist" >&2
    echo "                         on this machine -- cannot determine what commit to pin to." >&2
    echo "                         Nothing touched." >&2
    exit 1
fi
echo "-- all $(set -- $VERBS; echo $#) operator-verb shims agree: currently exec'ing $DISCOVERED live --"

# --- 4. that checkout must be clean, and its commit determinable ------------------------------
DISCOVERED_SHA="$(cd "$DISCOVERED" && git rev-parse HEAD 2>/dev/null || true)"
if [ -z "$DISCOVERED_SHA" ]; then
    echo "convert-to-submodule.sh: $DISCOVERED is not a git checkout (or git is not on PATH) --" >&2
    echo "                         cannot determine the commit this deployment has been running." >&2
    echo "                         Nothing touched." >&2
    exit 1
fi
if ! (cd "$DISCOVERED" && git diff --quiet && git diff --cached --quiet) 2>/dev/null; then
    echo "convert-to-submodule.sh: $DISCOVERED has UNCOMMITTED CHANGES -- refusing to pin this" >&2
    echo "                         deployment to a commit that would not reproduce what it is" >&2
    echo "                         ACTUALLY running right now. Commit or stash the changes in" >&2
    echo "                         $DISCOVERED, then re-run. Nothing touched." >&2
    exit 1
fi
echo "-- $DISCOVERED is a clean git checkout at $DISCOVERED_SHA -- this is the commit this"
echo "   deployment has actually been running, and the one it will be pinned to (NOT autoharn's"
echo "   current tip -- conversion is not conflated with an upgrade, per design/ORCH-DEPLOYMENT-"
echo "   PINNING.md)."

# --- 5. LIVE SESSION CHECK -- never run against a deployment with a live session ---------------
echo "-- checking for a live session against $DEST (best-effort /proc scan; run THIS command"
echo "   from a SEPARATE terminal, never from inside a session sitting in $DEST -- the scan"
echo "   cannot see its own caller's session, see bootstrap/live_session_check.py's docstring) --"
if ! "$PY" "$SELF_ROOT/bootstrap/live_session_check.py" "$DEST"; then
    echo "" >&2
    echo "convert-to-submodule.sh: REFUSING -- see the process list above. Converting a deployment" >&2
    echo "                         out from under a live session is exactly the hazard pinning" >&2
    echo "                         exists to retire, not a new way to reintroduce it (CLAUDE.md," >&2
    echo "                         'Never modify hooks/ or a user project while a live session" >&2
    echo "                         runs there'). End the session, then re-run. Nothing touched." >&2
    exit 1
fi

# --- 6. typed confirmation ----------------------------------------------------------------------
SUBMODULE_URL="${PIN_URL:-$DISCOVERED}"
echo ""
echo "ABOUT TO CONVERT $DEST:"
echo "  - add autoharn as a git submodule at $DEST/.autoharn, pinned to $DISCOVERED_SHA"
echo "    (submodule remote: $SUBMODULE_URL)"
echo "  - repoint $VERBS, and every hook command in .claude/settings.json at that pinned copy"
echo "  - commit the change in $DEST's own git history"
echo "  - after this, a merge to autoharn's working branch will NEVER change this deployment's"
echo "    behavior again -- the next intentional autoharn version needs"
echo "    bootstrap/upgrade-submodule.sh $DEST <new-sha>"
if [ "$YES" -ne 1 ]; then
    printf "Type CONVERT to proceed: "
    read -r ans
    if [ "$ans" != "CONVERT" ]; then
        echo "convert-to-submodule.sh: confirmation not given -- nothing touched." >&2
        exit 1
    fi
fi

# --- 7. do it -------------------------------------------------------------------------------
if (cd "$DEST" && git rev-parse --is-inside-work-tree >/dev/null 2>&1); then
    echo "-- $DEST is already a git repository -- using it --"
else
    echo "-- $DEST is not yet a git repository -- running git init --"
    (cd "$DEST" && git init --quiet)
fi

_submodule_add_opts=""
case "$SUBMODULE_URL" in
    *://*) ;;
    *) _submodule_add_opts="-c protocol.file.allow=always" ;;
esac
echo "-- adding submodule --"
(cd "$DEST" && git $_submodule_add_opts submodule add --quiet "$SUBMODULE_URL" .autoharn)
(cd "$DEST/.autoharn" && git checkout --quiet "$DISCOVERED_SHA")
echo "   .autoharn added, pinned to $DISCOVERED_SHA"

echo "-- repointing the operator-verb shims --"
for v in $VERBS; do
    shim="$DEST/$v"
    cat > "$shim" <<SHIM
#!/bin/sh
HERE="\$(cd "\$(dirname "\$0")" && pwd)"
exec env PICKUP_DEPLOYMENT="\$HERE/deployment.json" $DEST/.autoharn/bootstrap/templates/$v.tmpl "\$@"
SHIM
    chmod +x "$shim"
    echo "   $v -> $DEST/.autoharn/bootstrap/templates/$v.tmpl"
done

echo "-- repointing .claude/settings.json hook wiring --"
if [ -f "$DEST/.claude/settings.json" ]; then
    # Every hook command in settings.json bakes an ABSOLUTE $DISCOVERED path (bootstrap/
    # new-project.sh's sedsubst __AUTOHARN_ROOT__ substitution) -- a plain, exact string
    # replacement of that one known prefix is the whole fix (ADR-0012 P1: one mechanism, no
    # second JSON-hook-path parser grown here).
    sed -i "s|$DISCOVERED/hooks/|$DEST/.autoharn/hooks/|g" "$DEST/.claude/settings.json"
    echo "   .claude/settings.json: $DISCOVERED/hooks/ -> $DEST/.autoharn/hooks/"
else
    echo "   NOTE: $DEST/.claude/settings.json not found -- no hook wiring to repoint (unusual for" >&2
    echo "   a bootstrap/new-project.sh scaffold; proceeding, but this deployment's hooks may not" >&2
    echo "   have been wired the standard way)." >&2
fi
if [ -f "$DEST/.claude/HOOKS.md" ]; then
    sed -i "s|$DISCOVERED|$DEST/.autoharn|g" "$DEST/.claude/HOOKS.md"
    echo "   .claude/HOOKS.md: cosmetic text updated to name the pinned root"
fi

echo "-- committing in $DEST's own git history --"
(cd "$DEST" && git add \
    .gitmodules .autoharn \
    $VERBS \
    .claude/settings.json .claude/HOOKS.md 2>/dev/null || true)
if (cd "$DEST" && git diff --cached --quiet) 2>/dev/null; then
    echo "   nothing to commit (unexpected -- check $DEST's git status by hand)"
else
    (cd "$DEST" && git commit --quiet -m "migrate: pin autoharn@$DISCOVERED_SHA via .autoharn submodule (deployment-live-exec-coupling conversion, bootstrap/convert-to-submodule.sh)")
    echo "   committed: $(cd "$DEST" && git log -1 --oneline)"
fi

# --- 8. verify every verb still answers ---------------------------------------------------------
echo "-- verifying every operator verb resolves into the pin --"
FAIL=0
for v in $VERBS; do
    target="$(sed -n "s|.*exec env PICKUP_DEPLOYMENT=\"[^\"]*\" \(.*\)/bootstrap/templates/$v\.tmpl.*|\1|p" "$DEST/$v" | head -1)"
    if [ "$target" != "$DEST/.autoharn" ]; then
        echo "   !! $v: expected to resolve into $DEST/.autoharn, got '$target'" >&2
        FAIL=1
        continue
    fi
    if [ ! -x "$DEST/.autoharn/bootstrap/templates/$v.tmpl" ]; then
        echo "   !! $v: $DEST/.autoharn/bootstrap/templates/$v.tmpl is missing or not executable" >&2
        FAIL=1
        continue
    fi
    echo "   $v: resolves into the pin, target executable -- OK"
done
if [ "$FAIL" -ne 0 ]; then
    echo "convert-to-submodule.sh: one or more verbs failed verification above -- the conversion" >&2
    echo "                         COMMIT WAS ALREADY MADE (see the git log line above); fix the" >&2
    echo "                         reported verb(s) by hand, or 'git revert' the commit in $DEST." >&2
    exit 1
fi
echo "-- smoke test: ./led (read-only, --recent 1) --"
if (cd "$DEST" && ./led --recent 1); then
    echo "   ./led answered (see output above) -- the pinned copy is genuinely executing"
else
    echo "   NOTE: ./led exited non-zero above -- this is EXPECTED if this deployment's DB role/" >&2
    echo "   schema is unreachable from here, and is NOT itself evidence the pin is wrong (a" >&2
    echo "   'file not found' / 'exec format error' would be; a DB connection error is not --" >&2
    echo "   check the error text above)." >&2
fi

echo "== done =="
echo "Record this migration in autoharn's OWN ledger (self-application, CLAUDE.md):"
echo "  cd $SELF_ROOT && ./led decision \"migrate: $(basename "$DEST") pinned to autoharn@$DISCOVERED_SHA (deployment-live-exec-coupling migration)\""
if [ -x "$DEST/led" ]; then
    echo "This deployment carries its own ledger too -- record it there as well, in its own voice:"
    echo "  cd $DEST && ./led decision \"migrated: pinned to autoharn@$DISCOVERED_SHA via .autoharn submodule (deployment-live-exec-coupling conversion)\""
fi
echo "To take a newer autoharn later (deliberate, never a side effect of a merge):"
echo "  bootstrap/upgrade-submodule.sh $DEST <new-sha>"
