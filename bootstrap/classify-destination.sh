#!/bin/sh
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-21T21:44:24Z
#   last-change: 2026-07-21T22:00:25Z
#   contributors: 43f77bff/main
# <<< PROVENANCE-STAMP <<<

# bootstrap/classify-destination.sh -- shell reproduction of tools/setup_tui/destination.py's
# classify_destination (design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md §3's cross-language
# floor, ADR-0012 P7: "generate-or-compile-from-one-source > build-time lint > runtime parity",
# and P7's own permitted exception -- "codegen when disproportionate": three JSON keys and a
# three-marker existence check do not earn a code generator). THE PYTHON MODULE IS THE
# AUTHORITY; this is a MINIMAL shell re-derivation -- markers only, no JSON parsing beyond
# existence plus a plain grep for the two `world`/`name` string fields the contradiction check
# needs (never a full JSON parse -- this script has no JSON parser and does not grow one).
# Drift between the two implementations is caught by the parity fixture
# (seen-red/setup-tui-destination-state-parity/run_fixtures.py), not by codegen.
#
# Prints one of: fresh / autoharn-complete / autoharn-partial / foreign -- the same four
# DestKind values tools/setup_tui/destination.py's DestKind enum names (its own `.value` strings,
# so a caller comparing this script's stdout against `DestKind(...).value` never needs a second
# vocabulary). Known, named weaker-than-Python spots (never silently claimed equivalent):
#   - an UNPARSEABLE sentinel (spec's AUTOHARN_PARTIAL red flag) is not detected here -- this
#     script has no JSON validator, so a corrupt-but-present sentinel is treated the same as a
#     well-formed one for the marker count. The parity fixture's five witnessed shapes do not
#     include a corrupt sentinel for exactly this reason (named, not silently dropped).
#   - a NON-DIRECTORY existing path (a plain file at $DEST) is reported "foreign" here, matching
#     the Python module's own DestKind.FOREIGN for the same case.
#
# Usage:
#   . bootstrap/classify-destination.sh   -- sources classify_destination() into the caller
#   bootstrap/classify-destination.sh <path>   -- prints the kind directly, exits 0

classify_destination() {
    _cd_path="$1"
    if [ ! -e "$_cd_path" ]; then
        echo "fresh"
        return 0
    fi
    if [ ! -d "$_cd_path" ]; then
        echo "foreign"
        return 0
    fi
    # Excludes the wizard's OWN pre-birth commit journal (tools/setup_tui/commit_executor.py's
    # JOURNAL_FILENAME) from the occupancy question -- a live commit `os.makedirs(dest)`s and
    # opens this journal INSIDE dest before the first plan entry (often birth's own
    # new-project.sh call) ever runs; without this exclusion a genuinely fresh destination would
    # misclassify FOREIGN the instant the journal exists (found live, WDR1 fixture regression --
    # see tools/setup_tui/destination.py's own _IGNORED_ENTRIES for the Python-side fix this
    # mirrors). Literal filename, not sourced from Python (this script has no import mechanism);
    # the parity fixture catches drift if the two names ever disagree.
    _cd_nonjournal_count=$(ls -A "$_cd_path" 2>/dev/null \
        | grep -v -x '.setup-tui-commit-journal.json' | wc -l)
    if [ "$_cd_nonjournal_count" -eq 0 ]; then
        echo "fresh"
        return 0
    fi

    _cd_sentinel="$_cd_path/.autoharn-world.json"
    _cd_deployment="$_cd_path/deployment.json"
    _cd_led="$_cd_path/legacy/led"

    _cd_sentinel_present=0
    [ -f "$_cd_sentinel" ] && _cd_sentinel_present=1
    _cd_deployment_present=0
    [ -f "$_cd_deployment" ] && _cd_deployment_present=1
    _cd_led_present=0
    [ -f "$_cd_led" ] && _cd_led_present=1

    if [ "$_cd_sentinel_present" -eq 1 ] && [ "$_cd_deployment_present" -eq 1 ] \
       && [ "$_cd_led_present" -eq 1 ]; then
        # world-name grep (spec §3's minimal shell floor), not a JSON parse.
        _cd_sentinel_world="$(grep -o '"world"[[:space:]]*:[[:space:]]*"[^"]*"' "$_cd_sentinel" 2>/dev/null \
            | sed -E 's/.*:[[:space:]]*"([^"]*)"/\1/' | head -n1)"
        _cd_deployment_name="$(grep -o '"name"[[:space:]]*:[[:space:]]*"[^"]*"' "$_cd_deployment" 2>/dev/null \
            | sed -E 's/.*:[[:space:]]*"([^"]*)"/\1/' | head -n1)"
        if [ -n "$_cd_sentinel_world" ] && [ -n "$_cd_deployment_name" ] \
           && [ "$_cd_sentinel_world" != "$_cd_deployment_name" ]; then
            echo "autoharn-partial"
            return 0
        fi
        echo "autoharn-complete"
        return 0
    fi
    if [ "$_cd_sentinel_present" -eq 0 ] && [ "$_cd_deployment_present" -eq 1 ] \
       && [ "$_cd_led_present" -eq 1 ]; then
        # Pre-sentinel legacy world (spec §2) -- behavioral evidence alone, no retro-stamping.
        echo "autoharn-complete"
        return 0
    fi

    _cd_count=$((_cd_sentinel_present + _cd_deployment_present + _cd_led_present))
    if [ "$_cd_count" -gt 0 ]; then
        echo "autoharn-partial"
        return 0
    fi
    echo "foreign"
    return 0
}

# Directly executable (the parity fixture's own shell-side invocation) as well as sourceable
# (new-project.sh's own use) -- `case` on $0's basename rather than `[ "$0" = "$BASH_SOURCE" ]`,
# which is a bashism this /bin/sh script does not otherwise depend on.
case "$(basename "$0" 2>/dev/null)" in
    classify-destination.sh)
        [ $# -ge 1 ] || { echo "usage: $0 <path>" >&2; exit 2; }
        classify_destination "$1"
        ;;
esac
