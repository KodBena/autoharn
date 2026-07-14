#!/bin/sh
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T21:20:21Z
#   last-change: 2026-07-14T21:21:54Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

# upgrade-submodule.sh -- the UPGRADE verb for a PINNED deployment (tracker item
# deployment-live-exec-coupling, design/ORCH-DEPLOYMENT-PINNING.md: "Upgrading an adopter to a
# newer autoharn becomes the explicit, recorded act the maintainer asked for"). A pinned
# deployment (bootstrap/new-project.sh --pin submodule, or bootstrap/convert-to-submodule.sh)
# NEVER changes behavior except at THIS moment, and never as a side effect of someone else's
# unrelated merge to autoharn's working branch.
#
# Usage:
#   bootstrap/upgrade-submodule.sh <deployment-dir> <new-sha> [--yes]
#
#   <deployment-dir>  a deployment already pinned (has a <deployment-dir>/.autoharn submodule --
#                     run bootstrap/convert-to-submodule.sh first if it is not).
#   <new-sha>         the EXACT commit to bump the pin to -- deliberate, never a branch name, never
#                     "latest"/"tip"/omitted. This is the one-line requirement design/ORCH-
#                     DEPLOYMENT-PINNING.md names: an upgrade is a recorded, chosen act, not a
#                     silent float to wherever autoharn's working branch happens to be today.
#   --yes             skip the typed confirmation prompt (scripted/CI use).
#
# What this does: fetches the pinned submodule's remote, checks out <new-sha> (refusing loudly if
# it does not exist there), commits the new pin in the deployment's OWN git history (never
# autoharn's), verifies every verb still answers, and prints the exact ./led decision line to
# record the upgrade -- in BOTH autoharn's own ledger (self-application, CLAUDE.md) and the
# deployment's own ledger if it carries one.
#
# REFUSES LOUDLY, and touches NOTHING, on any of:
#   - <deployment-dir> is not pinned yet (no .autoharn submodule -- convert it first).
#   - <new-sha> is not resolvable after a fetch (typo, or a commit that was never pushed anywhere
#     this submodule's remote can reach).
#   - a LIVE SESSION appears to be running against <deployment-dir> (same hazard as conversion --
#     bumping the pin under a live session defeats the entire point of pinning, mid-session, just
#     like the live-exec coupling this whole design retires).
#   - the typed confirmation is not given (unless --yes).
set -eu

usage() {
    echo "usage: $0 <deployment-dir> <new-sha> [--yes]" >&2
    exit 2
}

[ $# -ge 2 ] || usage
DEST="$1"; NEW_SHA="$2"; shift 2
YES=0
while [ $# -gt 0 ]; do
    case "$1" in
        --yes) YES=1; shift ;;
        *) echo "unrecognized argument: $1" >&2; usage ;;
    esac
done

SELF_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$HOME/w/vdc/venvs/generic/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"

if [ ! -d "$DEST" ]; then
    echo "upgrade-submodule.sh: $DEST is not a directory" >&2
    exit 1
fi
DEST="$(cd "$DEST" && pwd)"

echo "== upgrade-submodule: $DEST -> $NEW_SHA =="

# --- 1. must already be pinned ------------------------------------------------------------------
if [ ! -d "$DEST/.autoharn" ]; then
    echo "upgrade-submodule.sh: $DEST/.autoharn does not exist -- this deployment is not pinned" >&2
    echo "                      yet. Run bootstrap/convert-to-submodule.sh $DEST first (or" >&2
    echo "                      bootstrap/new-project.sh --pin submodule for a brand-new one)." >&2
    exit 1
fi
if ! (cd "$DEST/.autoharn" && git rev-parse --is-inside-work-tree >/dev/null 2>&1); then
    echo "upgrade-submodule.sh: $DEST/.autoharn exists but is not a git checkout -- this" >&2
    echo "                      deployment's pin is broken; not something this script repairs." >&2
    exit 1
fi
OLD_SHA="$(cd "$DEST/.autoharn" && git rev-parse HEAD)"
if [ "$OLD_SHA" = "$NEW_SHA" ]; then
    echo "upgrade-submodule.sh: already pinned to $NEW_SHA -- nothing to do." >&2
    exit 1
fi

# --- 2. LIVE SESSION CHECK -- bumping the pin mid-session defeats pinning's whole point ---------
echo "-- checking for a live session against $DEST (best-effort /proc scan; run THIS command"
echo "   from a SEPARATE terminal, never from inside a session sitting in $DEST -- the scan"
echo "   cannot see its own caller's session, see bootstrap/live_session_check.py's docstring) --"
if ! "$PY" "$SELF_ROOT/bootstrap/live_session_check.py" "$DEST"; then
    echo "" >&2
    echo "upgrade-submodule.sh: REFUSING -- see the process list above. Bumping the pin under a" >&2
    echo "                      live session changes that session's behavior mid-stream, exactly" >&2
    echo "                      the hazard pinning exists to retire. End the session, then" >&2
    echo "                      re-run. Nothing touched." >&2
    exit 1
fi

# --- 3. fetch + resolve the target commit --------------------------------------------------------
echo "-- fetching --"
(cd "$DEST/.autoharn" && git fetch --quiet)
if ! (cd "$DEST/.autoharn" && git cat-file -e "$NEW_SHA^{commit}" 2>/dev/null); then
    echo "upgrade-submodule.sh: '$NEW_SHA' does not resolve to a commit in $DEST/.autoharn after" >&2
    echo "                      fetching -- typo, or a commit not reachable from this submodule's" >&2
    echo "                      remote (git -C $DEST/.autoharn remote -v). Nothing touched." >&2
    exit 1
fi
RESOLVED_SHA="$(cd "$DEST/.autoharn" && git rev-parse "$NEW_SHA^{commit}")"

# --- 4. typed confirmation ------------------------------------------------------------------------
echo ""
echo "ABOUT TO UPGRADE $DEST:"
echo "  autoharn pin: $OLD_SHA -> $RESOLVED_SHA"
echo "  every operator verb + hook in this deployment picks up the new bytes on its NEXT"
echo "  invocation after this commits -- no other change."
if [ "$YES" -ne 1 ]; then
    printf "Type UPGRADE to proceed: "
    read -r ans
    if [ "$ans" != "UPGRADE" ]; then
        echo "upgrade-submodule.sh: confirmation not given -- nothing touched." >&2
        exit 1
    fi
fi

# --- 5. do it ---------------------------------------------------------------------------------
(cd "$DEST/.autoharn" && git checkout --quiet "$RESOLVED_SHA")
(cd "$DEST" && git add .autoharn)
(cd "$DEST" && git commit --quiet -m "upgrade: autoharn .autoharn submodule $OLD_SHA -> $RESOLVED_SHA")
echo "-- pin bumped and committed: $(cd "$DEST" && git log -1 --oneline) --"

# --- 6. verify every verb still answers ------------------------------------------------------
echo "-- verifying every operator verb resolves into the new pin --"
VERBS="led judge pickup audit distance-to-clean verify-commission verify-chain attest-doc"
FAIL=0
for v in $VERBS; do
    if [ ! -x "$DEST/.autoharn/bootstrap/templates/$v.tmpl" ]; then
        echo "   !! $v: $DEST/.autoharn/bootstrap/templates/$v.tmpl is missing or not executable" >&2
        FAIL=1
        continue
    fi
    echo "   $v: target executable at the new pin -- OK"
done
if [ "$FAIL" -ne 0 ]; then
    echo "upgrade-submodule.sh: one or more verbs failed verification above -- the pin bump WAS" >&2
    echo "                      ALREADY COMMITTED (see the git log line above); 'git revert' the" >&2
    echo "                      commit in $DEST if you need to roll back." >&2
    exit 1
fi
echo "-- smoke test: ./led (read-only, --recent 1) --"
if (cd "$DEST" && ./led --recent 1); then
    echo "   ./led answered (see output above) -- the new pin is genuinely executing"
else
    echo "   NOTE: ./led exited non-zero above -- expected if this deployment's DB is unreachable" >&2
    echo "   from here, not itself evidence the pin is wrong (check the error text above)." >&2
fi

echo "== done =="
echo "Record this upgrade in autoharn's OWN ledger (self-application, CLAUDE.md):"
echo "  cd $SELF_ROOT && ./led decision \"upgrade: $(basename "$DEST") autoharn .autoharn submodule $OLD_SHA -> $RESOLVED_SHA\""
if [ -x "$DEST/led" ]; then
    echo "This deployment carries its own ledger too -- record it there as well, in its own voice:"
    echo "  cd $DEST && ./led decision \"upgrade: autoharn .autoharn submodule $OLD_SHA -> $RESOLVED_SHA\""
fi
