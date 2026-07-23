# bootstrap/shim-verbs.sh -- the ONE home for the operator-verb shim set every bootstrap script
# that writes or discovers those shims must agree on (tracker item submodule-shim-set-drift,
# ledger row 1182). Before this file existed, bootstrap/new-project.sh's own scaffold loop (the
# authority: it is what actually stamps a fresh deployment) hand-listed the ten verbs, and THREE
# other scripts each hand-maintained their OWN, independently-drifted copy of that same list:
# bootstrap/convert-to-submodule.sh checked only 8 (9 with `doctor` conditionalized) and
# bootstrap/upgrade-submodule.sh checked 9 -- both silently missing `asof-export` -- while
# bootstrap/freeze-at-stamp.sh (found in reach while fixing this, same hazard class, not the
# originally-named two scripts but the identical bug) also silently missed `asof-export`. Every
# one of those four scripts now sources THIS file instead of spelling the list out itself
# (ADR-0012 P1: one mechanism, not four that must be kept in sync by hand and inevitably aren't).
# Add a new verb to a scaffold exactly once, here, and every consumer picks it up automatically.
#
# This is intentionally a plain sourced shell fragment, not a script new-project.sh's loop is
# parsed OUT of -- the loop line in new-project.sh remains the readable, obviously-correct source
# of truth for what a fresh scaffold writes; this file is that same list, lifted out so it has
# exactly one written form instead of the loop's own text being re-derived by sed/awk (fragile,
# and harder for a human to verify at a glance than a second variable assignment sourced
# alongside it).
#
# CHRONOLOGY (this is why the vocabulary below has three tiers, not two):
#   - SHIM_VERBS_ORIGINAL_EIGHT: the eight verbs every scaffold has written since before either
#     `asof-export` or `doctor` existed. A real deployment scaffolded early (e.g. ~/ent, stamped
#     2026-07-13) has exactly these eight and nothing more -- legitimately, not as a defect.
#   - `asof-export` was added 2026-07-18 (commit badc51c), AFTER ~/ent and any other
#     already-running deployment was scaffolded.
#   - `doctor` was added later still (ledger rows 1147/1148).
#   - SHIM_VERBS: the nine verbs every scaffolding path below writes UNCONDITIONALLY, always has,
#     for a world born TODAY (the original eight + asof-export -- doctor is not in this set).
#   - SHIM_VERBS_OPTIONAL: 'doctor' only.
#   - SHIM_VERBS_ALL: all ten. Scaffold-WRITING scripts (bootstrap/new-project.sh,
#     bootstrap/track-work.sh, bootstrap/freeze-at-stamp.sh) and template-verifying scripts
#     (bootstrap/upgrade-submodule.sh, which only re-verifies a freshly-fetched autoharn tree's
#     own templates, never an existing deployment's shims) use SHIM_VERBS_ALL unconditionally --
#     a fresh scaffold or a fresh template tree has every verb today's autoharn ships, no excuse
#     for optionality there.
#   - SHIM_VERBS_OPTIONAL_DISCOVERY: 'asof-export' and 'doctor' together -- the two verbs a
#     script that DISCOVERS/converts an EXISTING, possibly pre-dating deployment
#     (bootstrap/convert-to-submodule.sh) must treat as optional rather than refusing every
#     pre-existing deployment on either verb's account. `doctor` already had this carve-out
#     (rows 1147/1148); `asof-export` was missed when it was added -- and because
#     convert-to-submodule.sh's own discovery loop was hard-requiring $SHIM_VERBS (all nine,
#     including asof-export) unconditionally, conversion of a genuinely pre-2026-07-18
#     deployment like ~/ent started refusing with a misleading "not a live-exec scaffold this
#     script recognizes", even though nothing about that deployment is actually wrong -- it is
#     simply older than the verb. Fixed here: convert-to-submodule.sh's REQUIRED set is
#     SHIM_VERBS_ORIGINAL_EIGHT; it folds in each of SHIM_VERBS_OPTIONAL_DISCOVERY's members
#     when present, skips them when absent, same posture on both verbs, not just `doctor`.
SHIM_VERBS_ORIGINAL_EIGHT="led judge pickup audit distance-to-clean verify-commission verify-chain attest-doc"
SHIM_VERBS="$SHIM_VERBS_ORIGINAL_EIGHT asof-export"
SHIM_VERBS_OPTIONAL="doctor"
SHIM_VERBS_OPTIONAL_DISCOVERY="asof-export doctor"
SHIM_VERBS_ALL="$SHIM_VERBS $SHIM_VERBS_OPTIONAL"
