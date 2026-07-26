# _fixture_sandbox_preamble.sh -- design/FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md
# (ledger rows 1237-1248 the class, 1315/1316/1325 the ratification). THE GUARANTEE this build
# adds: enforcement stops depending on recognizing a fixture's CALL (what the now-demoted
# gates/fixture_deployment_pin_guard.py tried, and five fresh-context review laps kept finding new
# ordinary-Python spellings around) and starts depending on the CALLED THING refusing. Every
# spelling -- os.system, keyword argv, match/case, an alias chain, anything nobody has invented
# yet -- hits this same runtime check, because it runs in the verb, not in a parser looking for
# the verb.
#
# SOURCED (". ", never exec'd) by BOTH choke points named in spec §2: the ./autoharn dispatcher
# itself, and every libexec/autoharn/<verb> shell entry point -- "one shared preamble" means one
# FILE, sourced from every place a repo-root verb can actually be reached, so a fixture that skips
# ./autoharn entirely and invokes libexec/autoharn/<verb> directly (an "alias chain" evasion, the
# same shape the pin-guard arc's lap-5 findings kept turning up) refuses identically to the normal
# dispatch path. The caller sets _FSB_WHAT (a short description of the attempted verb+args) BEFORE
# sourcing this file.
#
# LIVES IN filing/, NOT libexec/autoharn/ (moved here during the build, not a first-draft
# choice): seen-red/umbrella-cli-dispatch-parity's own case a mechanically asserts
# `ls libexec/autoharn/` == the ./autoharn dispatch table's roster, one file per real verb --
# a shared, non-verb helper physically living in that same directory is roster drift by that
# fixture's own (correct) definition. filing/ is already the project's one home for cross-verb
# shared mechanics (gpg_trust.py, deployment_record.py, ...); this file and its Python twin
# filing/fixture_sandbox.py both live there for the same reason, not because either is a verb.
#
# SCOPE (spec §5: "not a change to any world's verbs"): this file is sourced ONLY from ./autoharn
# and libexec/autoharn/* -- never from bootstrap/templates/*.tmpl. A scratch world's own shim
# (bootstrap/new-project.sh, or freeze-at-stamp.sh's frozen-dest shim rewrite) execs a *.tmpl file
# DIRECTLY, never ./autoharn or libexec/autoharn/* -- it never sources this file at all, so it
# structurally cannot refuse under the marker. This is deliberate and is the whole answer to the
# subtle part of this build: no cwd/PICKUP_DEPLOYMENT/"am I a scratch world" runtime discriminator
# is needed, because the CHOKE POINT CHOICE itself is the discriminator -- a scratch world's own
# verbs never execute this code path, full stop, regardless of what env vars or cwd they carry
# (see the build report for why this can't misfire: bootstrap/new-project.sh's scaffold loop
# writes `exec env PICKUP_DEPLOYMENT=... $EXEC_ROOT/bootstrap/templates/$verb.tmpl "$@"` --
# straight to the template, never through this repo's dispatcher; bootstrap/freeze-at-stamp.sh's
# frozen destination goes further and OVERWRITES the git-archived copy of ./led/./verify-chain/etc
# with the identical direct-to-template shape before it is ever used).
#
# EXIT CODE 21 -- distinct, documented, never reused by any other refusal in this dispatch chain.
FIXTURE_SANDBOX_REFUSED_EXIT=21

if [ -n "${AUTOHARN_FIXTURE_SANDBOX:-}" ]; then
    if [ -z "${AUTOHARN_FIXTURE_SANDBOX_WAIVER:-}" ]; then
        echo "autoharn: REFUSED -- fixture sandbox marker set (AUTOHARN_FIXTURE_SANDBOX=1) and" >&2
        echo "  ${_FSB_WHAT:-this invocation} just attempted this repo's OWN root verb surface" >&2
        echo "  against the REAL deployment (design/FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-" >&2
        echo "  SPEC.md, ledger rows 1237-1248: a fixture reaching a live deployment.json this" >&2
        echo "  way is the leak class this refusal forecloses -- every argv spelling, not just" >&2
        echo "  the ones a static census happens to enumerate)." >&2
        echo "" >&2
        echo "  Two sanctioned exits:" >&2
        echo "    1. Drive a SCRATCH world instead (bootstrap/new-project.sh --new-world, or any" >&2
        echo "       other scaffolded deployment) -- its own ./led/./judge/etc. never reach this" >&2
        echo "       check (they exec bootstrap/templates/*.tmpl directly, never this repo's" >&2
        echo "       ./autoharn dispatcher or libexec/autoharn/*), so nothing here blocks it." >&2
        echo "    2. If this call site has a REVIEWED, use-site reason to touch a repo-root verb" >&2
        echo "       directly, set AUTOHARN_FIXTURE_SANDBOX_WAIVER=\"<reason>\" (a non-empty" >&2
        echo "       string) in this call's own environment. The reason is echoed into this" >&2
        echo "       verb's output, so the run's transcript carries the justification at the use" >&2
        echo "       site -- an EMPTY reason is refused exactly like no waiver at all." >&2
        echo "" >&2
        echo "  Nothing was touched. Exit code $FIXTURE_SANDBOX_REFUSED_EXIT (distinct, documented)." >&2
        exit "$FIXTURE_SANDBOX_REFUSED_EXIT"
    fi
    echo "autoharn: fixture-sandbox WAIVER in effect for ${_FSB_WHAT:-this invocation} -- reason:" >&2
    echo "  $AUTOHARN_FIXTURE_SANDBOX_WAIVER" >&2
fi
