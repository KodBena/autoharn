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
# the operator-verb shims discovered present (SHIM_VERBS_ORIGINAL_EIGHT required, asof-export/
# doctor folded in when present -- bootstrap/shim-verbs.sh) AND the hook wiring in .claude/settings.json at that pinned copy,
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
#   - <deployment-dir> has BOTH the post-§6 ./autoharn dispatcher AND a stray legacy per-verb
#     shim (e.g. ./led) -- a real scaffold has one shape or the other, NEVER both; a hybrid mix
#     is a sign something half-migrated, so this is refused rather than silently preferring the
#     dispatcher and ignoring the stray file (fix round, 2026-07-26, strengthened-review finding
#     2 -- the PRIOR behavior here, before this fix).
#   - the required operator-verb shims (SHIM_VERBS_ORIGINAL_EIGHT; asof-export/doctor are
#     discovery-optional, see bootstrap/shim-verbs.sh) are missing, malformed, already pinned (already has .autoharn), or
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

# --- 3. discover the CURRENT live-exec AUTOHARN_ROOT, and confirm agreement -------------------
# §6 amendment (2026-07-26, rows 1357/1365/1366/1367 -- design/FABLE-AUTOHARN-UMBRELLA-CLI-
# SPEC.md's scaffold clause executes): a deployment scaffolded by TODAY's new-project.sh has ONE
# dispatcher, `<dest>/autoharn`, not ten per-verb shims -- but "existing worlds untouched"
# (runs-are-linear) means a deployment scaffolded BEFORE this migration still legitimately has
# the old ten-shim shape, and this conversion script must serve BOTH: it never assumes which
# shape a real, already-scaffolded deployment carries.
if [ -x "$DEST/autoharn" ]; then
    echo "-- $DEST/autoharn dispatcher found -- new (post-§6) scaffold shape --"
    # HYBRID-SHAPE REFUSAL (fix round, 2026-07-26, strengthened-review finding 2): a deployment
    # legitimately has EITHER the one dispatcher (post-§6) OR the ten bare per-verb shims
    # (pre-§6, runs-are-linear -- "existing worlds untouched") -- never both. A dispatcher
    # coexisting with a STRAY bare shim (e.g. $DEST/led alongside $DEST/autoharn) is not a third
    # legitimate shape: it means something half-migrated (a hand-run new-project.sh --force that
    # didn't clean up an old shim, a partial manual edit, or a bug) -- a hazard, not a
    # convenience to route around by silently preferring the dispatcher, which is what this
    # script used to do (the `else` branch below was simply never reached, so a stray shim went
    # unmentioned, unconverted, and untouched). Refused loudly here instead, naming every stray
    # shim found and how to resolve it, before this script commits to either code path.
    STRAY_SHIMS=""
    for v in $SHIM_VERBS_ALL; do
        [ -e "$DEST/$v" ] && STRAY_SHIMS="$STRAY_SHIMS $v"
    done
    if [ -n "$STRAY_SHIMS" ]; then
        echo "convert-to-submodule.sh: REFUSED -- $DEST has BOTH the $DEST/autoharn dispatcher" >&2
        echo "                         (post-§6 scaffold shape) AND a stray legacy per-verb shim" >&2
        echo "                         at:$STRAY_SHIMS" >&2
        echo "                         This is not a recognized deployment shape -- a real" >&2
        echo "                         scaffold has EITHER the one dispatcher OR the ten bare" >&2
        echo "                         shims, never both. A hybrid mix is a sign something" >&2
        echo "                         half-migrated (a partial re-scaffold, a hand-added shim," >&2
        echo "                         or a bug), and this script will not silently pick the" >&2
        echo "                         dispatcher and ignore the rest. To resolve: if the stray" >&2
        echo "                         shim(s) are vestigial (the dispatcher is what this" >&2
        echo "                         deployment actually uses), remove them by hand and re-run;" >&2
        echo "                         if this deployment is actually still on the pre-§6 shim" >&2
        echo "                         shape and $DEST/autoharn is the stray file instead, remove" >&2
        echo "                         IT and re-run. Nothing touched." >&2
        exit 1
    fi
    DISCOVERED="$(sed -n 's|.*exec env PICKUP_DEPLOYMENT="[^"]*" \(.*\)/bootstrap/templates/"\$VERB"\.tmpl.*|\1|p' "$DEST/autoharn" | head -1)"
    if [ -z "$DISCOVERED" ]; then
        echo "convert-to-submodule.sh: $DEST/autoharn does not match the expected dispatcher shape" >&2
        echo "                         (exec ...)/bootstrap/templates/\"\$VERB\".tmpl ...) --" >&2
        echo "                         refusing to guess. Nothing touched." >&2
        exit 1
    fi
    VERBS="autoharn"
else
    echo "-- no $DEST/autoharn dispatcher -- falling back to the pre-§6 ten-shim discovery --"
    # REQUIRED here is SHIM_VERBS_ORIGINAL_EIGHT only -- the verbs every scaffold has written
    # since before either `asof-export` (added 2026-07-18, commit badc51c) or `doctor` (ledger
    # rows 1147/1148) existed. Both of those are DISCOVERY-OPTIONAL (SHIM_VERBS_OPTIONAL_DISCOVERY,
    # bootstrap/shim-verbs.sh): a deployment scaffolded before either verb existed legitimately
    # has no such shim, and hard-requiring either would refuse conversion for every pre-existing
    # deployment on that one verb's account -- exactly the bug this fix retires (~/ent, scaffolded
    # 2026-07-13, has the original eight and neither newer verb; it is this script's own named
    # motivating case, and used to be refused by the asof-export omission alone). Each optional
    # verb is folded into $VERBS below when its shim is present, so it gets discovered/
    # repointed/committed exactly like the required set; absent, it is silently skipped.
    VERBS="$SHIM_VERBS_ORIGINAL_EIGHT"
    for _opt in $SHIM_VERBS_OPTIONAL_DISCOVERY; do
        [ -f "$DEST/$_opt" ] && VERBS="$VERBS $_opt"
    done
    DISCOVERED=""
    for v in $VERBS; do
        shim="$DEST/$v"
        if [ ! -f "$shim" ]; then
            echo "convert-to-submodule.sh: $shim not found -- this deployment is missing the" >&2
            echo "                         operator-verb shim '$v', which is REQUIRED for conversion." >&2
            echo "                         If this deployment was scaffolded before '$v' existed, add" >&2
            echo "                         the shim by hand (it is just this 3-line shape, matching" >&2
            echo "                         every other shim in $DEST):" >&2
            echo "                           #!/bin/sh" >&2
            echo "                           HERE=\"\$(cd \"\$(dirname \"\$0\")\" && pwd)\"" >&2
            echo "                           exec env PICKUP_DEPLOYMENT=\"\$HERE/deployment.json\" <AUTOHARN_ROOT>/bootstrap/templates/$v.tmpl \"\$@\"" >&2
            echo "                         (then chmod +x it), or re-run bootstrap/new-project.sh" >&2
            echo "                         --force against $DEST to have the scaffold write it for" >&2
            echo "                         you. Nothing touched." >&2
            exit 1
        fi
        # Every shim is `exec env PICKUP_DEPLOYMENT=... <ROOT>/bootstrap/templates/<verb>.tmpl "$@"`
        # (bootstrap/new-project.sh's own shim-writing loop, pre-§6) -- extract <ROOT>.
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
fi
if [ ! -d "$DISCOVERED" ]; then
    echo "convert-to-submodule.sh: the discovered autoharn checkout '$DISCOVERED' does not exist" >&2
    echo "                         on this machine -- cannot determine what commit to pin to." >&2
    echo "                         Nothing touched." >&2
    exit 1
fi
if [ "$VERBS" = "autoharn" ]; then
    echo "-- the dispatcher currently exec's $DISCOVERED live --"
else
    echo "-- all $(set -- $VERBS; echo $#) operator-verb shims agree: currently exec'ing $DISCOVERED live --"
fi

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

if [ "$VERBS" = "autoharn" ]; then
    # §6 amendment: the ONE dispatcher, repointed IN PLACE -- a blanket string replacement of
    # the old EXEC_ROOT prefix (every mention in the file, comments included), the exact same
    # mechanism already used below for .claude/settings.json and .claude/HOOKS.md (ADR-0012 P1:
    # one mechanism, not a special dispatcher-rewriting parser grown here). Never regenerated
    # from scratch -- the roster/refusal-text/help logic new-project.sh wrote is untouched,
    # only the exec-root path changes.
    echo "-- repointing the ./autoharn dispatcher --"
    sed -i "s|$DISCOVERED|$DEST/.autoharn|g" "$DEST/autoharn"
    echo "   autoharn -> $DEST/.autoharn/bootstrap/templates/<verb>.tmpl"
else
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
fi

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
if [ "$VERBS" = "autoharn" ]; then
    target="$(sed -n 's|.*exec env PICKUP_DEPLOYMENT="[^"]*" \(.*\)/bootstrap/templates/"\$VERB"\.tmpl.*|\1|p' "$DEST/autoharn" | head -1)"
    if [ "$target" != "$DEST/.autoharn" ]; then
        echo "   !! autoharn: expected to resolve into $DEST/.autoharn, got '$target'" >&2
        FAIL=1
    elif [ ! -d "$DEST/.autoharn/bootstrap/templates" ]; then
        echo "   !! autoharn: $DEST/.autoharn/bootstrap/templates is missing" >&2
        FAIL=1
    else
        echo "   autoharn: resolves into the pin -- OK"
    fi
else
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
fi
if [ "$FAIL" -ne 0 ]; then
    echo "convert-to-submodule.sh: one or more verbs failed verification above -- the conversion" >&2
    echo "                         COMMIT WAS ALREADY MADE (see the git log line above); fix the" >&2
    echo "                         reported verb(s) by hand, or 'git revert' the commit in $DEST." >&2
    exit 1
fi
if [ "$VERBS" = "autoharn" ]; then
    echo "-- smoke test: ./autoharn led (read-only, --recent 1) --"
    if (cd "$DEST" && ./autoharn led --recent 1); then
        echo "   ./autoharn led answered (see output above) -- the pinned copy is genuinely executing"
    else
        echo "   NOTE: ./autoharn led exited non-zero above -- this is EXPECTED if this deployment's" >&2
        echo "   DB role/schema is unreachable from here, and is NOT itself evidence the pin is" >&2
        echo "   wrong (a 'file not found' / 'exec format error' would be; a DB connection error" >&2
        echo "   is not -- check the error text above)." >&2
    fi
else
    echo "-- smoke test: ./led (read-only, --recent 1) --"
    if (cd "$DEST" && ./led --recent 1); then
        echo "   ./led answered (see output above) -- the pinned copy is genuinely executing"
    else
        echo "   NOTE: ./led exited non-zero above -- this is EXPECTED if this deployment's DB role/" >&2
        echo "   schema is unreachable from here, and is NOT itself evidence the pin is wrong (a" >&2
        echo "   'file not found' / 'exec format error' would be; a DB connection error is not --" >&2
        echo "   check the error text above)." >&2
    fi
fi

echo "== done =="
echo "Record this migration in autoharn's OWN ledger (self-application, CLAUDE.md):"
echo "  cd $SELF_ROOT && ./autoharn led decision \"migrate: $(basename "$DEST") pinned to autoharn@$DISCOVERED_SHA (deployment-live-exec-coupling migration)\""
if [ -x "$DEST/autoharn" ]; then
    echo "This deployment carries its own ledger too -- record it there as well, in its own voice:"
    echo "  cd $DEST && ./autoharn led decision \"migrated: pinned to autoharn@$DISCOVERED_SHA via .autoharn submodule (deployment-live-exec-coupling conversion)\""
elif [ -x "$DEST/led" ]; then
    echo "This deployment carries its own ledger too -- record it there as well, in its own voice:"
    echo "  cd $DEST && ./led decision \"migrated: pinned to autoharn@$DISCOVERED_SHA via .autoharn submodule (deployment-live-exec-coupling conversion)\""
fi
echo "To take a newer autoharn later (deliberate, never a side effect of a merge):"
echo "  bootstrap/upgrade-submodule.sh $DEST <new-sha>"
