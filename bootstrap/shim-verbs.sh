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
# SHIM_VERBS: the nine verbs every scaffolding path below writes UNCONDITIONALLY, always has,
# for a world born today.
SHIM_VERBS="led judge pickup audit distance-to-clean verify-commission verify-chain attest-doc asof-export"
# SHIM_VERBS_OPTIONAL: 'doctor' only -- the newest of the ten (ledger rows 1147/1148), added
# after some already-scaffolded deployments existed. A deployment scaffolded BEFORE doctor
# existed legitimately has no such shim; a script that DISCOVERS/converts an EXISTING deployment
# (bootstrap/convert-to-submodule.sh) must treat it as optional rather than refusing every
# pre-existing deployment on this one verb's account. A script that WRITES a fresh scaffold
# (bootstrap/new-project.sh, track-work.sh, freeze-at-stamp.sh) or that only re-verifies a
# freshly-fetched autoharn tree's own templates (bootstrap/upgrade-submodule.sh) has no such
# excuse -- doctor is not optional for those, so they use SHIM_VERBS_ALL, never SHIM_VERBS alone.
SHIM_VERBS_OPTIONAL="doctor"
SHIM_VERBS_ALL="$SHIM_VERBS $SHIM_VERBS_OPTIONAL"
