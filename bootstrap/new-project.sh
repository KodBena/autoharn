#!/bin/sh
# new-project.sh — stamp a new instance directory: deployment.json, .claude/ wiring
# (settings.json, governed_files.json, apparatus.json, HOOKS.md), and the three verbs (led, judge,
# pickup) as thin shims exec'ing bootstrap/templates/*.tmpl LIVE out of this autoharn checkout
# (vestigial_documentation/design/ORCH-OPUS-READINESS.md move 2's template/instance split, then BACKLOG maintainer ruling
# 2026-07-11 "runs are strictly linear" disposition 6 "live verbs": the verbs stopped being
# sed-substituted frozen copies — a template fix here now reaches every already-scaffolded world
# instantly, matching how the two PreToolUse hooks already execute live per invocation). Only
# deployment.json and the .claude/ wiring stay scaffold-written, per-world config.
#
# Usage:
#   bootstrap/new-project.sh <dest-dir> --db <db> --host <host> --schema <schema> \
#       --kern <kern> --role <role> [--name <project-name>] [--governed <patterns>] [--force]
#
#   <dest-dir>   where to stamp the new instance (created if missing).
#   --db         the ledger's database name.
#   --host       the postgres host this project's ledger lives on.
#   --schema     the ledger schema (e.g. "toycolors").
#   --kern       the kernel schema (e.g. "toycolors_kernel").
#   --role       the granted subject role led/judge/pickup connect as (e.g. "toycolors_rw").
#   --name       this project's own identifier, written into deployment.json's `name` field and
#                read live from there by the scaffolded `./judge` shim as the target-name argument
#                to autoharn's engine/ledger_differential.py (and hence the derivations/ banking
#                subdirectory under autoharn's own tree) — default: <dest-dir>'s basename. Pick
#                something that will NOT collide with autoharn engine/targets.py's curated
#                registry names (toy, nla, e15-e18) or its scratch-naming conventions
#                (^s\d+[a-z]*$, *_scratch), or `judge` will resolve to the WRONG target.
#   --governed   comma-separated fnmatch patterns for `.claude/governed_files.json` (e.g.
#                "*.py,*.sql,*.tf") -- what the change gate protects in THIS deployment (tracker
#                item `scaffold-governed-set-language-default`, ent testbed finding 4, 2026-07-13:
#                the scaffold used to write ['*.py'] unconditionally, so any non-Python deployment
#                was born with its real work surfaces silently ungoverned). Omit it and the
#                scaffold falls back to the historical `*.py`-only default -- but then prints a
#                LOUD post-scaffold notice naming that default and the one-line widening act, so
#                the gap is never silent again.
#   --force      overwrite an existing deployment.json/scaffold at <dest-dir> (default: refuse).
#
# CONTRACT, named explicitly (findings-RCA, DRIVEN-INTERFACE fix): <dest-dir> is created with
# `mkdir -p`, so an OCCUPIED directory that does not already contain a deployment.json is
# permitted and MERGED into silently -- the refusal above fires ONLY on an existing
# deployment.json (or, under --pin submodule, an existing .autoharn), never on an occupied
# directory in general. A caller that wants a guaranteed-fresh directory must check for that
# itself before invoking this script; this script does not and will not make that check for you.
#
# --new-world <world> mode (BACKLOG "Ruling: one world per run", 2026-07-09; this session's
# batch item 7): a run's subject must not see a sibling run's ledger history (the many-worlds
# argument -- branches share only the branch point, never each other's ledgers). This mode
# stands up exactly that branch point in an EXISTING db, in one call: applies
# kernel/lineage/high_watermark_1.sql THEN kernel/lineage/s20-obligation-grants-and-view-
# refresh.sql THEN kernel/lineage/s21-session-aware-distinctness.sql (RATIFIED, BACKLOG.md
# 2026-07-09 -- so every new world is born on the current kernel, s20 AND s21 included, never
# the pre-s20 grants-gap shape the toy pilot found the hard way, and never the session-blind
# distinctness s21 fixes) into fresh schemas derived from <world> (e.g. --new-world run3 ->
# schema=run3, kern=run3_kernel, role=run3_rw -- override any
# of the three with an explicit --schema/--kern/--role if the naming convention does not fit),
# seeds the stamp secret (openssl rand -hex 32, mirroring drive/arm.sh ruling 43's own idempotent
# pattern -- skipped if a secret already exists, never silently rotated), and writes the matching
# deployment.json -- the operator step HOOKS.md documents as a manual "one manual step remains"
# for a HAND-scaffolded project is fully automated here for a probe/run world. EVERY -v var is
# still spelled out explicitly to psql (standing rule: never apply bare against a deployment that
# matters) -- --new-world does not relax that, it only derives the VALUES from one name instead
# of requiring the caller to keep schema/kern/role in agreement by hand (ADR-0012 P1). The
# 'author' principal is seeded automatically by s15-schema.sql itself (INSERT ... ON CONFLICT DO
# NOTHING, mapped to the connecting role) -- no separate registration step is needed here; it
# mirrors the toy WALKTHROUGH's own kernel-apply step exactly, nothing new to invoke.
#
# --new-world ALSO registers the 'reviewer' principal (subagent class, ON CONFLICT DO NOTHING)
# and writes the world's root CLAUDE.md (the templated governance preamble, auto-loaded by
# Claude Code at session start -- no separate read-me-first or paste step) -- BACKLOG
# "Maintainer ruling: self-application" (2026-07-09) named BOTH the hand-registered reviewer
# principal and the hand-pasted six-point governance prompt as the ceremony "starting a run
# becomes a verb" is meant to close; this closes it, so a --new-world scaffold is run-ready at
# birth instead of needing two more hand steps before the first real session (ratifier's
# acceptance bar, same date: at most one scaffold command, one `cd`, one `claude`, no paste).
#
# What this does NOT do: apply any kernel DDL to a deployment that is NOT a --new-world target (a
# separate, explicit -v-vars operator act). (Historical note: an earlier version of this comment
# named "rewire led to read deployment.json live" as future work — that landed 2026-07-11, "live
# verbs" above; led/judge/pickup all read deployment.json live now, same as the PreToolUse hooks
# always have.)
#
# --profile tracker mode (FABLE-TRACK-WORK-RETIREMENT-SPEC.md, ledger row 1271, retiring
# `bootstrap/track-work.sh`): a THIRD mode on this ONE scaffold, alongside classic
# --schema/--kern/--role and --new-world, for the case track-work.sh used to serve — "give ANY
# directory a STANDING, indefinite-lifetime work tracker" — modernized rather than reproduced
# byte-for-byte. Usage:
#   bootstrap/new-project.sh <dest-dir> --profile tracker --name <name> --db <db> --host <host> \
#       [--schema <schema>] [--kern <kern>] [--role <role>] [--force]
# `--name` is REQUIRED in this mode (mirrors track-work.sh's own one derivation input) and derives
# --schema/--kern/--role the same way --new-world derives them from a world name, unless an
# explicit override is given. This mode:
#   - applies the FULL CURRENT kernel lineage (identical apply list --new-world uses below, always
#     through the current head — never a frozen-at-birth-era cap: track-work.sh's own s25 cap was
#     an artifact of the era it was written in, not a deliberate ceiling this mode inherits) to a
#     fresh schema pair, including the stamp-secret/genesis-seed/s40-s43 birth sequence — the same
#     code path --new-world uses (ADR-0012 P1: one birth sequence, not two drifting copies). The
#     stamp secret ends up provisioned-but-unread here exactly as it is for the kernel's own inert
#     subsystems more generally: harmless, not a defect (see "Why the full chain, unwired" in
#     user-guide/USER-WORK-STATUS-OFFERING.md, generalized here to the stamp secret specifically).
#   - writes deployment.json + this deployment's OWN keys/ (its GPG keyring, never autoharn's own
#     law/keys/), attestations/, roles/, the ./autoharn dispatcher (verb roster derived live from
#     the bootstrap/templates/*.tmpl glob, see _write_world_dispatcher() near this script's own
#     top -- bootstrap/shim-verbs.sh's SHIM_VERBS_ALL still governs the separate legacy/ loop and
#     the pre-migration ten-shim scripts), legacy/, and orchlog -- the SAME unconditional
#     scaffold-writing code every mode already runs below.
#   - configures the boundary to be SERVED VIA ensure-running rather than a standing daemon: picks
#     a free port, writes boundary-multiplex.toml, and writes boundary_url/boundary_deployment
#     into deployment.json -- but does NOT start the service now. serving/ensure_running.py's
#     `ensure_running_or_leave_unreachable` (already wired into every served shim template) spawns
#     it as a detached child on this deployment's FIRST `./led`/`./pickup`/etc. call. This is what
#     dissolved track-work.sh's own "a standing tracker runs no boundary service by design"
#     rationale (BACKLOG-era `legacy/led` gap) -- the boundary is no longer a thing that must be
#     stood up by hand or wired into a hook; it is a thing that appears the moment it is needed.
#   - wires **NO hooks and NO governance preamble** -- deliberately, in track-work.sh's own words,
#     preserved verbatim: **"a standing project is not a governed world."** No `.claude/`
#     settings.json/governed_files.json/apparatus.json/HOOKS.md, no root CLAUDE.md, no portable-
#     ADR LAW section. Every row this deployment's `./led` writes lands unstamped
#     (stamp_agent/stamp_session/stamp_hmac all NULL, stamp_verified=false) -- visible in
#     `./led --recent`, not hidden -- exactly track-work.sh's own honest-unwired-store posture,
#     now on the full current lineage instead of a capped one.
#   - refuses combined with --new-world (a deployment is either a governed world or a standing
#     tracker, never both at once), with --pin (track-work.sh never supported pinning; out of
#     scope for this mode), and with --governed (nothing to govern -- no change-gate is wired).
set -eu

# Captured BEFORE any argument parsing consumes "$@", so the PROVENANCE header this script writes
# into .claude/HOOKS.md (below) records the operator's ACTUAL invocation, not a reconstruction —
# closing exactly the gap the maintainer flagged for run3 ("an operator cannot create world N
# without reading script source" / "how was run3 created? that of course needs to be documented",
# 2026-07-09): no future world should be born without this line writing itself (ADR-0012 P1 --
# one source, the real argv, not a hand-typed guess reconstructed after the fact).
CREATE_CMD="$0"
for _a in "$@"; do
    case "$_a" in
        *[\ \	]*) CREATE_CMD="$CREATE_CMD '$_a'" ;;
        *) CREATE_CMD="$CREATE_CMD $_a" ;;
    esac
done
CREATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# ---------------------------------------------------------------------------------------------
# _write_world_dispatcher() -- THE ONE HOME for a world's ./autoharn dispatcher generation
# (autoharn3 work item scaffold-courier-verb-gap, ledger row 101; maintainer ruling 2026-07-28
# amending the original brief: "the world-dispatcher generation ... derives its verb table from
# the bootstrap/templates/*.tmpl directory glob -- a template that exists IS a verb; the
# hardcoded ten-entry table is deleted, not extended"). Defined here, near the top of the file,
# so BOTH call sites below -- the ordinary --new-world/--profile scaffold flow (further down,
# where PROJECT_ROOT/EXEC_ROOT/TEMPLATES are already resolved) and the --refresh-dispatcher
# early-exit mode (immediately after usage(), before any of that resolution) -- share the exact
# same generation logic (ADR-0012 P1: one mechanism, not two that drift). Requires PROJECT_ROOT,
# EXEC_ROOT, TEMPLATES already set by the caller; writes ONLY $PROJECT_ROOT/autoharn.
#
# CLASS FIX, superseding the prior SHIM_VERBS_ALL-driven table (bootstrap/shim-verbs.sh is
# UNCHANGED and still governs the ./legacy/ recovery-original loop and the pre-migration
# ten-shim scripts -- convert-to-submodule.sh/upgrade-submodule.sh/freeze-at-stamp.sh -- this
# fix touches ONLY the world-dispatcher table a fresh --new-world/--profile/--refresh-dispatcher
# run writes): the old table was a SECOND, hand-maintained home for "which .tmpl file is a
# verb" -- exactly the drift class lineage-chain-lags-directory (ledger rows 1392/1393) closed
# for the kernel chain, reopened here for the verb roster (found live: courier.tmpl did not
# exist and the hardcoded table could not have noticed even if it had).
#
# ADR-0000 RULE 2(a) CLOSURE STATEMENT: the quantification universe is EXACTLY the set of
# basenames matching bootstrap/templates/*.tmpl, MINUS the enumerated NON_VERB_TEMPLATES
# exclusion list immediately below -- every OTHER *.tmpl file in that directory IS a dispatched
# verb, by construction. A future verb template landing in bootstrap/templates/ cannot be
# forgotten from a freshly-generated world's roster: forgetting it is unrepresentable, because
# shipping the template IS shipping the verb (this generation's own read of the directory,
# every time it runs, never a frozen snapshot). The one way a template can legitimately sit in
# this directory without becoming a verb is to be named, with a reason, in the exclusion list
# below -- silence is never a valid way to exclude one.
#
# NON_VERB_TEMPLATES -- the loud, enumerated, commented exclusion list Rule 2(a) demands. Every
# member is either a config/doc scaffold-time template (sedsubst'd or copied into a plain file
# at birth, never exec'd as an operator verb) or a legacy/ recovery original (routed through
# $PROJECT_ROOT/legacy/<verb> by this script's own separate loop elsewhere, sourced from
# bootstrap/shim-verbs.sh, never through ./autoharn) -- named here rather than silently dropped:
#   CLAUDE.md.tmpl                 -- sedsubst'd into $PROJECT_ROOT/CLAUDE.md, a doc, not a verb
#   HOOKS.md.tmpl                  -- sedsubst'd into .claude/HOOKS.md, a doc, not a verb
#   settings.json.tmpl             -- sedsubst'd into .claude/settings.json, config, not a verb
#   attestations-README.md.tmpl    -- sedsubst'd into attestations/README.md, a doc, not a verb
#   keys-README.md.tmpl            -- sedsubst'd into keys/README.md, a doc, not a verb
#   roles-README.md.tmpl           -- sedsubst'd into roles/README.md, a doc, not a verb
#   legacy-pickup.tmpl             -- the direct-psql original, reached via ./legacy/pickup only
#   legacy-distance-to-clean.tmpl  -- the direct-psql original, reached via ./legacy/distance-to-clean only
#   legacy-asof-export.tmpl        -- the direct-psql original, reached via ./legacy/asof-export only
NON_VERB_TEMPLATES="CLAUDE.md.tmpl HOOKS.md.tmpl settings.json.tmpl attestations-README.md.tmpl keys-README.md.tmpl roles-README.md.tmpl legacy-pickup.tmpl legacy-distance-to-clean.tmpl legacy-asof-export.tmpl"

_is_non_verb_template() {
    _nvt_target="$1"
    for _nvt in $NON_VERB_TEMPLATES; do
        [ "$_nvt_target" = "$_nvt" ] && return 0
    done
    return 1
}

_scan_verb_templates() {
    # WRITES NOTHING (fix-round finding 1, autoharn3 row 101 re-review, 2026-07-28): the glob +
    # header-validation pass, factored out of _write_world_dispatcher() below so it can be run as
    # a PRE-WRITE gate, before any scaffold file exists on disk, on every path that reaches this
    # dispatcher generation (--new-world/classic/--profile all resolve TEMPLATES at one shared
    # point in this script, immediately followed by a call to this function -- see that call
    # site's own comment). A header-less template refusing generation used to be true only when
    # DISCOVERED by _write_world_dispatcher() itself, which runs near the END of the scaffold
    # sequence -- by then deployment.json/.autoharn-world.json/.gitignore/.claude/*/keys/
    # attestations/roles/ were already written, so that refusal's own "Nothing was touched" text
    # was FALSE on that one path (of 14 such messages in this script) -- the ONE deviation from
    # this script's own refuse-before-touching invariant. Fixing the WORDING would have left the
    # invariant broken; this fixes the CLASS instead -- the validation itself moved earlier, so
    # nothing before it can have run yet on any code path that calls it before its own first
    # write. _write_world_dispatcher() below still calls this (a cheap, already-validated
    # re-check on the ordinary scaffold flow; the ONLY validation on --refresh-dispatcher, which
    # never had the ordering hazard to begin with -- it writes nothing else before or after
    # ./autoharn) -- it is simply no longer positioned to be the FIRST place a broken template is
    # discovered on the ordinary flow.
    #
    # Sets DISPATCH_TABLE (tab-separated verb\tdesc lines, sorted) and VERB_ROSTER (space-joined
    # verb names) as a side effect; refuses loudly and exits 2, writing nothing, on a
    # non-excluded template with no '# autoharn-verb-desc: ...' header.
    _svt_table=""
    for _svt_file in "$TEMPLATES"/*.tmpl; do
        [ -e "$_svt_file" ] || continue  # literal, never-matched glob guard (POSIX sh fallback)
        _svt_base="$(basename "$_svt_file")"
        if _is_non_verb_template "$_svt_base"; then
            continue
        fi
        _svt_verb="${_svt_base%.tmpl}"
        # Header-line convention (this class fix's chosen single home for help-text descriptions,
        # applied to every dispatched verb template in the same commit): the FIRST line matching
        # '^# autoharn-verb-desc: ' anywhere in the file, grep -m1 so a template is free to place
        # it wherever its own header comment block reads best (line 2, typically, right after the
        # shebang). A template that lacks it refuses generation LOUDLY -- never a silent blank
        # description -- naming exactly what to add or, if the file genuinely isn't a verb, that
        # it belongs in NON_VERB_TEMPLATES above instead.
        _svt_desc="$(grep -m1 '^# autoharn-verb-desc: ' "$_svt_file" | sed 's/^# autoharn-verb-desc: //')"
        if [ -z "$_svt_desc" ]; then
            echo "new-project.sh: REFUSED -- $_svt_file carries no '# autoharn-verb-desc: ...' header line." >&2
            echo "                bootstrap/new-project.sh's dispatcher generation derives the verb roster" >&2
            echo "                from the bootstrap/templates/*.tmpl glob (autoharn3 ledger row 101's class" >&2
            echo "                fix) -- every dispatched verb template must carry this header, or be added" >&2
            echo "                to _scan_verb_templates()'s own NON_VERB_TEMPLATES exclusion list in this" >&2
            echo "                script if it genuinely is not a verb. Nothing was touched." >&2
            exit 2
        fi
        _svt_line="$(printf '%s\t%s' "$_svt_verb" "$_svt_desc")"
        if [ -z "$_svt_table" ]; then
            _svt_table="$_svt_line"
        else
            _svt_table="$_svt_table
$_svt_line"
        fi
    done
    # Stable, deterministic order regardless of the filesystem's own glob enumeration order.
    DISPATCH_TABLE="$(printf '%s\n' "$_svt_table" | sort)"
    VERB_ROSTER="$(printf '%s\n' "$DISPATCH_TABLE" | cut -f1 | tr '\n' ' ')"
}

_write_world_dispatcher() {
    _scan_verb_templates  # cheap, already-validated re-check on the ordinary flow -- see its own comment

    # NEVER OVERWRITE A DIFFERING FILE BLIND (fix-round finding 2, autoharn3 row 101 re-review,
    # 2026-07-28): --refresh-dispatcher (and any --force re-scaffold of an existing world, which
    # shares this same function) used to `cat >` straight over $PROJECT_ROOT/autoharn -- an
    # operator's own hand-edit there (a local patch, an experiment, a manual fix ahead of this
    # generator catching up) was silently discarded with no trace. Write the NEW content to a
    # scratch file on the SAME filesystem first (mktemp under $PROJECT_ROOT itself -- portable
    # `mv` afterward, never a cross-device copy), THEN decide, by comparing bytes, which of
    # exactly three things this run does -- never a fourth, unnamed one:
    #   SKIPPED-IDENTICAL  the existing file already matches byte-for-byte -- nothing written,
    #                      nothing backed up (there is nothing to lose).
    #   REPLACED           the existing file differs -- moved aside to $PROJECT_ROOT/autoharn.
    #                      pre-refresh (overwriting any EARLIER backup of that exact name --
    #                      disclosed below, not hidden) BEFORE the new file lands, so the prior
    #                      content survives on disk under a named, discoverable path rather than
    #                      being silently lost.
    #                      fresh-write     no prior $PROJECT_ROOT/autoharn existed at all (the
    #                      ordinary --new-world/classic/--profile birth path, every time).
    # Every one of the three is printed, by name, in this function's own success line -- a caller
    # reading stdout always knows which one happened, never has to guess or diff by hand.
    _wwd_target="$PROJECT_ROOT/autoharn"
    _wwd_new="$(mktemp "$PROJECT_ROOT/.autoharn-dispatcher-new.XXXXXX")"
    cat > "$_wwd_new" <<DISPATCHEREOF
#!/bin/sh
# autoharn -- this world's ONE operator-surface dispatcher (design/FABLE-AUTOHARN-UMBRELLA-CLI-
# SPEC.md §6 amendment, ledger rows 1357/1365/1366/1367; verb-roster generation CLASS-FIXED
# 2026-07-28, autoharn3 row 101/scaffold-courier-verb-gap -- see bootstrap/new-project.sh's own
# _write_world_dispatcher() for the full closure statement). Routes \`autoharn <verb> [args...]\`
# to $EXEC_ROOT/bootstrap/templates/<verb>.tmpl with THIS world's own deployment.json
# (PICKUP_DEPLOYMENT) -- byte-identical routing/env to what each retired per-verb shim did.
#
# ADR-0000 RULE 2(a) CLOSURE STATEMENT: the verb roster below is EXACTLY the set of
# bootstrap/templates/*.tmpl basenames (minus that checkout's own enumerated NON_VERB_TEMPLATES
# exclusion list) at the moment THIS dispatcher was generated -- a template that exists IS a
# verb; there is no second, hand-maintained list this roster could have drifted from. Re-run
# this world's own scaffold generation (bootstrap/new-project.sh --refresh-dispatcher $PROJECT_ROOT)
# to pick up a verb template added to the checkout after this world was born.
set -eu

HERE="\$(cd "\$(dirname "\$0")" && pwd)"

_dispatch_table() {
    cat <<'DISPATCHVERBS'
$DISPATCH_TABLE
DISPATCHVERBS
}

_print_help() {
    echo "usage: autoharn <verb> [args...]"
    echo
    echo "Each verb below is a thin dispatch to $EXEC_ROOT/bootstrap/templates/<verb>.tmpl with"
    echo "this world's own deployment.json -- semantics, refusal texts and exit codes are"
    echo "unchanged from the per-verb shims this dispatcher replaces."
    echo
    echo "verbs:"
    _dispatch_table | awk -F'\t' '{printf "  %-20s %s\n", \$1, \$2}'
    echo
    echo "For a verb's own full usage, run 'autoharn <verb> --help'."
}

if [ \$# -eq 0 ] || [ "\$1" = "--help" ] || [ "\$1" = "-h" ] || [ "\$1" = "help" ]; then
    _print_help
    exit 0
fi

VERB="\$1"; shift

if ! _dispatch_table | cut -f1 | grep -qx "\$VERB"; then
    echo "autoharn: REFUSED -- unrecognized verb '\$VERB'." >&2
    echo >&2
    echo "Known verbs:" >&2
    _dispatch_table | awk -F'\t' '{printf "  %-20s %s\n", \$1, \$2}' >&2
    echo >&2
    echo "Run 'autoharn --help' for the full roster. Nothing was touched." >&2
    exit 2
fi

exec env PICKUP_DEPLOYMENT="\$HERE/deployment.json" $EXEC_ROOT/bootstrap/templates/"\$VERB".tmpl "\$@"
DISPATCHEREOF
    chmod +x "$_wwd_new"

    if [ -f "$_wwd_target" ] && cmp -s "$_wwd_target" "$_wwd_new"; then
        rm -f "$_wwd_new"
        echo "autoharn dispatcher: SKIPPED-IDENTICAL -- $_wwd_target already matches the current bootstrap/templates/*.tmpl roster byte-for-byte; nothing written."
    elif [ -f "$_wwd_target" ]; then
        _wwd_backup="$PROJECT_ROOT/autoharn.pre-refresh"
        if [ -e "$_wwd_backup" ]; then
            echo "autoharn dispatcher: NOTE -- an earlier $_wwd_backup already existed; it is being overwritten by the file replaced THIS run (only the most recent pre-refresh copy is kept)."
        fi
        mv -f "$_wwd_target" "$_wwd_backup"
        mv -f "$_wwd_new" "$_wwd_target"
        chmod +x "$_wwd_target"
        echo "autoharn dispatcher: REPLACED -- prior $_wwd_target differed from the current roster; its content was moved to $_wwd_backup (byte-identical backup) before the new one was written -- it was never discarded."
        echo "wrote autoharn (dispatcher -> $EXEC_ROOT/bootstrap/templates/<verb>.tmpl, roster: $VERB_ROSTER)"
    else
        mv -f "$_wwd_new" "$_wwd_target"
        chmod +x "$_wwd_target"
        echo "autoharn dispatcher: fresh-write -- no prior $_wwd_target existed."
        echo "wrote autoharn (dispatcher -> $EXEC_ROOT/bootstrap/templates/<verb>.tmpl, roster: $VERB_ROSTER)"
    fi
}
# ---------------------------------------------------------------------------------------------

# LINEAGE HEAD, derived live from kernel/lineage/*.sql itself (never hand-typed) -- usability
# review finding 14 (ledger row 1180): this usage text used to name a fixed generation ("s20
# through s43 + s45") that fell 12 generations stale the moment a later delta landed and nobody
# remembered to edit this string. Deriving it here means it cannot drift from the code beneath
# it -- the SAME "derive, don't freeze" discipline kernel/lineage/README.md already applies to
# its own "current generation" claim.
_LINEAGE_DIR="$(cd "$(dirname "$0")/../kernel/lineage" && pwd)"
LINEAGE_HEAD="$(cd "$_LINEAGE_DIR" && ls s*.sql 2>/dev/null | grep -v '\.detect\.sql$' \
    | sed -E 's/^s([0-9]+).*/\1/' | sort -n | tail -1)"
[ -n "$LINEAGE_HEAD" ] || LINEAGE_HEAD="?"  # never silently blank if the directory is ever empty

usage() {
    echo "usage: $0 <dest-dir> --db <db> --host <host> --schema <schema> --kern <kern> --role <role> [--name <name>] [--governed <patterns>] [--force]" >&2
    echo "       $0 <dest-dir> --new-world <world> --db <db> --host <host> [--name <name>] [--governed <patterns>] [--force]" >&2
    echo "       $0 --refresh-dispatcher <world-dir>" >&2
    echo "         (rewrites ONLY <world-dir>/autoharn from the CURRENT bootstrap/templates/*.tmpl" >&2
    echo "          verb roster against that world's OWN existing deployment.json -- touches" >&2
    echo "          nothing else in that world; refuses if <world-dir>/deployment.json is absent." >&2
    echo "          autoharn3 ledger row 101 item 4: a world's operator wiring is updatable in" >&2
    echo "          place -- runs-are-linear governs the kernel/record, not this wiring file.)" >&2
    echo "       $0 <dest-dir> --profile tracker --name <name> --db <db> --host <host> [--schema <schema>]" >&2
    echo "           [--kern <kern>] [--role <role>] [--force]" >&2
    echo "         (--profile tracker: a STANDING work tracker, not a governed world -- retires" >&2
    echo "          bootstrap/track-work.sh, modernized. --name is REQUIRED (derives --schema/" >&2
    echo "          --kern/--role from it unless given explicitly). Applies the FULL CURRENT" >&2
    echo "          kernel lineage (s\${LINEAGE_HEAD} as of this run, never a frozen-era cap)," >&2
    echo "          configures the boundary via ensure-running (auto-spawns on first ./led/etc" >&2
    echo "          call -- no standing daemon started at scaffold time), and wires NO hooks and" >&2
    echo "          NO governance CLAUDE.md preamble -- 'a standing project is not a governed" >&2
    echo "          world' (track-work.sh's own words, preserved). Refused combined with" >&2
    echo "          --new-world, --pin, or --governed.)" >&2
    echo "         (--boundary-url <url> --boundary-deployment <name> write deployment.json's two" >&2
    echo "          new served-shim keys, design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md" >&2
    echo "          §5 -- both optional; the rebased led/pickup/asof-export/distance-to-clean" >&2
    echo "          shims refuse loudly, teaching both names, when either is absent at RUN time" >&2
    echo "          rather than this scaffold guessing a boundary URL or standing one up)" >&2
    echo "         (--new-world derives --schema/--kern/--role from <world> unless given explicitly;" >&2
    echo "          also applies high_watermark_1.sql + every kernel/lineage/sNN delta through the" >&2
    echo "          current head (s${LINEAGE_HEAD} as of this run -- derived live from" >&2
    echo "          kernel/lineage/ itself, never hand-typed here), seeds the stamp secret, and" >&2
    echo "          runs the s40 birth sequence (author registration event, standing declaration," >&2
    echo "          reviewer/commissioner ceremony) -- see the --new-world block in this script's" >&2
    echo "          own header comment)" >&2
    echo "         (--governed <comma-separated-fnmatch-patterns> sets .claude/governed_files.json;" >&2
    echo "          omit it and the *.py-only default is used, with a loud post-scaffold notice)" >&2
    echo "         (--pin submodule adds autoharn as a git submodule at <dest-dir>/.autoharn, pinned" >&2
    echo "          to THIS checkout's current commit, and points every operator verb + hook at that" >&2
    echo "          pinned copy instead of this live checkout -- design/ORCH-DEPLOYMENT-PINNING.md," >&2
    echo "          NOT combinable with --new-world. --pin-url <url> overrides the submodule remote" >&2
    echo "          (default: this checkout's own on-disk path -- portable only on this machine;" >&2
    echo "          pass a real git remote URL for a submodule another machine can also fetch))" >&2
    echo "         (--no-law suppresses the generated LAW section (portable ADR subset + pointers)" >&2
    echo "          this scaffold otherwise writes into .claude/HOOKS.md (and root CLAUDE.md in" >&2
    echo "          --new-world mode) by default -- tracker item portable-adr-delivery, maintainer" >&2
    echo "          instruction 2026-07-15: deployments must at least optionally receive the" >&2
    echo "          portable ADRs; default is ON)" >&2
    echo "         (--features-file <path> reads a JSON feature manifest (deploy-feature-manifest," >&2
    echo "          ledger row 1274/1322) and applies it -- portable_adrs/vendored_skills/" >&2
    echo "          panel_extension/makespan_scheduler_tier/principal_set; writes the canonical" >&2
    echo "          <dest-dir>/features.json durable record. --no-vendored-skills/" >&2
    echo "          --panel-extension/--makespan-tier <tier> are the same three decisions as" >&2
    echo "          discrete flags for scriptability -- REFUSED if BOTH a discrete flag and" >&2
    echo "          --features-file set the same decision, never silently resolved one way)" >&2
    echo "         (--accept-existing-content: <dest-dir> classifies FOREIGN -- non-empty, no" >&2
    echo "          autoharn birth evidence (design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md) --" >&2
    echo "          is REFUSED unless this flag is given explicitly; the setup TUI passes it" >&2
    echo "          exactly when its own fork-target screen recorded the operator's typed" >&2
    echo "          acknowledgment. Has no effect on AUTOHARN_COMPLETE/AUTOHARN_PARTIAL, which" >&2
    echo "          keep the existing deployment.json-exists / --force gate above)" >&2
    exit 2
}

# --refresh-dispatcher <world-dir> (autoharn3 ledger row 101 amendment, item 4: "worlds' operator
# wiring IS updatable in place -- runs-are-linear governs the kernel/record, not wiring files").
# A SELF-CONTAINED early exit, intercepted before any of the --new-world/--profile machinery
# below (which needs a whole DDL-apply/deployment.json-write ceremony this mode must NOT run) --
# rewrites ONLY $WORLD_DIR/autoharn from the CURRENT bootstrap/templates/*.tmpl roster (the same
# _write_world_dispatcher() the ordinary scaffold flow calls further down, ADR-0012 P1), touching
# nothing else in that world. Refuses on anything that is not a recognizable, already-scaffolded
# world (no deployment.json) -- never guesses, never creates one.
if [ "${1:-}" = "--refresh-dispatcher" ]; then
    shift
    if [ $# -lt 1 ] || [ -z "$1" ]; then
        echo "usage: $0 --refresh-dispatcher <world-dir>" >&2
        echo "       rewrites ONLY <world-dir>/autoharn from the current bootstrap/templates/*.tmpl" >&2
        echo "       roster against that world's OWN existing deployment.json -- refuses if" >&2
        echo "       <world-dir>/deployment.json is absent (not a recognizable scaffolded world)." >&2
        exit 2
    fi
    _RD_WORLD_DIR="$1"
    if [ ! -f "$_RD_WORLD_DIR/deployment.json" ]; then
        echo "new-project.sh --refresh-dispatcher: REFUSED -- no deployment.json at $_RD_WORLD_DIR" >&2
        echo "                                       (not a recognizable scaffolded world). Nothing touched." >&2
        exit 1
    fi
    PROJECT_ROOT="$(cd "$_RD_WORLD_DIR" && pwd)"
    AUTOHARN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
    TEMPLATES="$AUTOHARN_ROOT/bootstrap/templates"
    # Same EXEC_ROOT heuristic the --pin submodule scaffold path uses at birth (this script's own
    # EXEC_ROOT block, further down): a world pinned via --pin submodule carries its own
    # $PROJECT_ROOT/.autoharn checkout and every verb (including ./autoharn itself) points at
    # THAT copy, never this live one -- a refresh must route the same way or it would silently
    # re-point a pinned world at this live checkout, exactly the coupling design/ORCH-DEPLOYMENT-
    # PINNING.md exists to prevent. An unpinned world (the common case) has no .autoharn/ and
    # keeps routing at this live checkout, same as it did at birth.
    EXEC_ROOT="$AUTOHARN_ROOT"
    if [ -d "$PROJECT_ROOT/.autoharn" ]; then
        EXEC_ROOT="$PROJECT_ROOT/.autoharn"
    fi
    echo "-- --refresh-dispatcher: rewriting $PROJECT_ROOT/autoharn from the current bootstrap/templates/*.tmpl roster (EXEC_ROOT=$EXEC_ROOT) --"
    _write_world_dispatcher
    echo "refresh-dispatcher: done -- only $PROJECT_ROOT/autoharn was touched."
    exit 0
fi

[ $# -ge 1 ] || usage
DEST="$1"; shift
NAME=""
FORCE=0
NEW_WORLD=""
PROFILE=""
GOVERNED=""
DB=""; HOST=""; SCHEMA=""; KERN=""; ROLE=""
# design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md §5 (ledger decision row 1631):
# deployment.json's two new OPTIONAL keys the REBASED shims (led/pickup/asof-export/
# distance-to-clean, now served-HTTP clients by default) need -- refused-if-absent BY THE SHIMS
# THEMSELVES, never by this scaffold (no search-path magic, no auto-launched boundary process:
# standing one up is a separate operator act, spec §3's own "no defaults file" posture extended
# here). Both default empty (unset in the written deployment.json, exactly like `name` above when
# --name is omitted) -- a scaffolded world with neither flag gets the new shims in
# REFUSAL-TEACHING mode until its operator supplies both, which is the correct default (a
# just-scaffolded world has no boundary process running yet either).
BOUNDARY_URL=""
BOUNDARY_DEPLOYMENT=""
# --pin submodule (tracker item deployment-live-exec-coupling, design/ORCH-DEPLOYMENT-PINNING.md,
# maintainer commission 2026-07-14 late "submodule deployment must be IDIOT-PROOF"): an OPT-IN
# scaffold-time flag, default UNSET so every existing caller (every --new-world run world, every
# seen-red/instruments fixture that scaffolds a classic deployment without this flag) keeps
# TODAY'S live-exec shape byte-for-byte -- this design's own text scopes the submodule shape to
# "an adopter", never to autoharn's own run* worlds, so the flag is refused in combination with
# --new-world below rather than silently accepted and ignored (ADR-0002: a refusal that teaches,
# not a caveat buried in a comment nobody reads).
PIN=""
PIN_URL=""
# LAW section (tracker item portable-adr-delivery, maintainer instruction 2026-07-15:
# deployments must at least optionally receive the portable ADRs). Default ON -- opt out with
# --no-law -- so a scaffold never silently withholds the LAW delivery the maintainer asked for;
# an adopter who genuinely wants no ADR pointers says so explicitly, once, rather than the
# scaffold defaulting to silence (mirrors this script's own --governed default-notice posture:
# the safe default is loud, not absent).
LAW_SECTION=1
# design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md §3: opt-in, default UNSET so every existing
# caller keeps today's shape -- a FOREIGN <dest-dir> (non-empty, no autoharn birth evidence) is
# now REFUSED (see the classify_destination gate below, right before mkdir -p) unless this flag
# says so explicitly.
ACCEPT_EXISTING_CONTENT=0
# deploy-feature-manifest (ledger row 1274/1322, work item deploy-feature-manifest): the
# DECLARATIVE FEATURE MANIFEST this scaffold reads and applies. Every default below reproduces
# TODAY'S exact behavior byte-for-byte (portable ADRs on via LAW_SECTION above, skills vendored
# unconditionally, no panel, no makespan declaration, no extra principals) -- a scaffold given
# NONE of these flags/--features-file writes NO new file and changes NO other file; the ONLY
# observable difference vs. a pre-manifest scaffold is the new, additive `features.json` durable
# record itself, and ONLY when --features-file is actually given (fail-safe additive, ADR-0004).
FEATURES_FILE=""
VENDOR_SKILLS=1
PANEL_EXTENSION=0
MAKESPAN_TIER="off"
# "was this discrete flag actually typed" trackers -- distinct from the flag's own value (whose
# default already equals "not given"), needed so a --features-file that ALSO sets the same
# decision can be refused as ambiguous (never silently resolved one way, ADR-0002) rather than
# only detectable by accident when the two happen to disagree.
_VENDOR_SKILLS_GIVEN=0
_PANEL_EXTENSION_GIVEN=0
_MAKESPAN_TIER_GIVEN=0
while [ $# -gt 0 ]; do
    case "$1" in
        --db) DB="$2"; shift 2 ;;
        --host) HOST="$2"; shift 2 ;;
        --schema) SCHEMA="$2"; shift 2 ;;
        --kern) KERN="$2"; shift 2 ;;
        --role) ROLE="$2"; shift 2 ;;
        --name) NAME="$2"; shift 2 ;;
        --boundary-url) BOUNDARY_URL="$2"; shift 2 ;;
        --boundary-deployment) BOUNDARY_DEPLOYMENT="$2"; shift 2 ;;
        --new-world) NEW_WORLD="$2"; shift 2 ;;
        --profile) PROFILE="$2"; shift 2 ;;
        --governed) GOVERNED="$2"; shift 2 ;;
        --pin) PIN="$2"; shift 2 ;;
        --pin-url) PIN_URL="$2"; shift 2 ;;
        --no-law) LAW_SECTION=0; shift ;;
        --force) FORCE=1; shift ;;
        --accept-existing-content) ACCEPT_EXISTING_CONTENT=1; shift ;;
        --features-file) FEATURES_FILE="$2"; shift 2 ;;
        --no-vendored-skills) VENDOR_SKILLS=0; _VENDOR_SKILLS_GIVEN=1; shift ;;
        --panel-extension) PANEL_EXTENSION=1; _PANEL_EXTENSION_GIVEN=1; shift ;;
        --makespan-tier) MAKESPAN_TIER="$2"; _MAKESPAN_TIER_GIVEN=1; shift 2 ;;
        *) echo "unrecognized argument: $1" >&2; usage ;;
    esac
done
if [ -n "$PIN" ] && [ "$PIN" != "submodule" ]; then
    echo "new-project.sh: --pin '$PIN' is not a recognized value -- only 'submodule' is supported" >&2
    echo "                today (the copy-at-scaffold fallback design/ORCH-DEPLOYMENT-PINNING.md" >&2
    echo "                names is deliberately out of scope for this build; the 2026-07-14" >&2
    echo "                maintainer commission asked for the submodule path specifically)." >&2
    exit 2
fi
if [ -n "$PIN" ] && [ -n "$NEW_WORLD" ]; then
    echo "new-project.sh: --pin submodule cannot be combined with --new-world -- autoharn's own" >&2
    echo "                run*-style throwaway worlds are DELIBERATELY scoped OUT of pinning" >&2
    echo "                (design/ORCH-DEPLOYMENT-PINNING.md: \"autoharn's own run* worlds keep" >&2
    echo "                the live-exec shape; that ruling was correctly scoped to them\"). Drop" >&2
    echo "                --pin for a --new-world scaffold, or drop --new-world for a pinned" >&2
    echo "                adopter deployment." >&2
    exit 2
fi
if [ -n "$PIN_URL" ] && [ -z "$PIN" ]; then
    echo "new-project.sh: --pin-url given without --pin submodule -- it has nothing to apply to." >&2
    exit 2
fi
# --profile tracker: validated BEFORE derivation, same posture as the --pin/--new-world checks
# above -- doubt about a flag combination's legality is refused loudly, not guessed at.
if [ -n "$PROFILE" ] && [ "$PROFILE" != "tracker" ]; then
    echo "new-project.sh: --profile '$PROFILE' is not a recognized value -- only 'tracker' is" >&2
    echo "                supported today (bootstrap/track-work.sh's retirement target)." >&2
    exit 2
fi
if [ -n "$PROFILE" ] && [ -n "$NEW_WORLD" ]; then
    echo "new-project.sh: --profile cannot be combined with --new-world -- a deployment is either" >&2
    echo "                a governed WORLD or a standing work tracker, never both at once (see" >&2
    echo "                this script's own header comment, 'a standing project is not a" >&2
    echo "                governed world'). Drop one or the other." >&2
    exit 2
fi
if [ "$PROFILE" = "tracker" ] && [ -n "$PIN" ]; then
    echo "new-project.sh: --profile tracker cannot be combined with --pin -- out of scope for" >&2
    echo "                this mode (bootstrap/track-work.sh never supported pinning either)." >&2
    exit 2
fi
if [ "$PROFILE" = "tracker" ] && [ -n "$GOVERNED" ]; then
    echo "new-project.sh: --profile tracker wires NO change-gate at all (no hooks are wired in" >&2
    echo "                this mode) -- --governed has nothing to apply to. Drop it, or drop" >&2
    echo "                --profile tracker for a governed --new-world scaffold." >&2
    exit 2
fi
if [ "$PROFILE" = "tracker" ] && [ -z "$NAME" ]; then
    echo "new-project.sh: --profile tracker requires --name -- it derives --schema/--kern/--role" >&2
    echo "                from it (mirrors bootstrap/track-work.sh's own one derivation input)." >&2
    usage
fi
# HAZARD FOUND IN REACH, FIXED HERE (CLAUDE.md's hazard-flagging duty), checked BEFORE any DB
# work below: --name feeds TWO independent, INCOMPATIBLE allowlists in this mode --
# serving/boundary_multiplex_config.py's own deployment-name contract, `[a-z0-9-]{1,64}` (spec
# §2, no underscores/uppercase), for boundary_deployment; and the SQL-identifier allowlist
# checked further below, `[A-Za-z0-9_]+` (no hyphens), for the derived SCHEMA/KERN/ROLE. Their
# INTERSECTION is `[a-z0-9]+` -- checked here, once, for a single clear rule instead of letting
# --name pass this check with a hyphen only to refuse two allowlist-checks later citing SCHEMA
# (confusing two-step diagnostic). Discovered live during this build: an unchecked derivation
# silently wrote a boundary-multiplex.toml the boundary service refuses to load at start-up
# (service.log: "deployment name '...' does not match ^[a-z0-9-]{1,64}$") against a scratch name
# that was perfectly legal SQL-identifier-wise. Refused here, loudly, before any schema/kernel DDL
# runs -- rather than silently lowercasing/stripping characters (a silent transform risks a
# collision the operator never asked for). CROSS-REFERENCE (work item
# setup-tui-worldname-boundary-allowlist, row 1317 arc): this same INCOMPATIBILITY is
# independently reachable through tools/setup_tui/idtypes.py's `WorldName`, feeding
# `steps_boundary.py`'s `boundary_deployment = world` -- a DIFFERENT screen/call path with no
# shared code to this shell script (a Python SSOT a `sh` script cannot import without a
# shell/Python contortion neither side's build wants). `WorldName.__post_init__` now enforces the
# SAME `[a-z0-9]{1,64}$` intersection this check derives below, independently, in its own home --
# the two homes MUST agree if either allowlist ever changes; this comment and that module's own
# docstring name each other for exactly that reason. This check's own `case` pattern below tests
# only the character class, not the length cap -- the omission this cross-reference flags and
# fixes below (an over-64-char --name would otherwise pass this gate and only break at boundary
# service start-up, the identical silent-downstream-break class this whole check exists to close).
if [ "$PROFILE" = "tracker" ] && [ -z "$BOUNDARY_URL" ] && [ -z "$BOUNDARY_DEPLOYMENT" ]; then
    case "$NAME" in
        *[!a-z0-9]*|"") _tracker_name_bad=1 ;;
        *) _tracker_name_bad=0 ;;
    esac
    if [ "$_tracker_name_bad" -eq 0 ] && [ "${#NAME}" -gt 64 ]; then
        _tracker_name_bad=1
    fi
    if [ "$_tracker_name_bad" -eq 1 ]; then
        echo "new-project.sh: REFUSED -- --profile tracker's --name ('$NAME') must match" >&2
        echo "                [a-z0-9]{1,64} (lowercase letters and digits only, at most 64" >&2
        echo "                characters) -- the intersection of the boundary service's own" >&2
        echo "                deployment-name contract ([a-z0-9-]{1,64}, no underscores/" >&2
        echo "                uppercase -- serving/boundary_multiplex_config.py spec §2) and" >&2
        echo "                the SQL-identifier allowlist ([A-Za-z0-9_]+, no hyphens) --name" >&2
        echo "                also derives --schema/--kern/--role from. Pick a compliant" >&2
        echo "                --name, or supply --boundary-url/--boundary-deployment" >&2
        echo "                explicitly with a compliant label (and --schema/--kern/--role" >&2
        echo "                explicitly too, if --name itself must stay outside" >&2
        echo "                [a-z0-9]{1,64}). Nothing was touched." >&2
        exit 1
    fi
    unset _tracker_name_bad
fi
# HAZARD FOUND IN REACH, FIXED HERE (CLAUDE.md's hazard-flagging duty; work item
# new-world-name-unchecked, row 1324): --new-world's own NEW_WORLD had NO charclass/length check
# at all before this fix -- the identical unchecked-name-reaches-boundary_deployment hazard class
# the --profile tracker --name check above (this same file) and tools/setup_tui/idtypes.py's
# WorldName now both refuse (merge 94325e7, row 1317 arc). NEW_WORLD feeds SCHEMA (below, when
# --schema is not given explicitly) into the SQL-identifier allowlist checked further down
# ([A-Za-z0-9_]+, no hyphens -- looser than lowercase-only, so an uppercase or hyphenated world
# name would otherwise sail through THAT gate) and is the human-readable world label a caller may
# later feed straight back into steps_boundary.py's own WorldName-gated boundary_deployment
# splice (serving/boundary_multiplex_config.py spec §2, `[a-z0-9-]{1,64}`) -- the same silent-
# downstream-break class this whole check exists to close, refused here, loudly, before any
# schema/kernel DDL runs, rather than silently lowercasing/truncating (a silent transform risks a
# collision the operator never asked for). CROSS-REFERENCE, same three tethered homes as the
# --profile tracker check above: this script's own --name check (immediately above), tools/
# setup_tui/idtypes.py's WorldName.__post_init__, and serving/boundary_multiplex_config.py's spec
# §2 -- all three enforce this SAME `[a-z0-9]{1,64}$` intersection independently, in their own
# homes, because no shared importable code crosses the shell/Python boundary; each cites the
# others so the allowlists stay in agreement if any one of them ever changes.
if [ -n "$NEW_WORLD" ]; then
    case "$NEW_WORLD" in
        *[!a-z0-9]*|"") _new_world_bad=1 ;;
        *) _new_world_bad=0 ;;
    esac
    if [ "$_new_world_bad" -eq 0 ] && [ "${#NEW_WORLD}" -gt 64 ]; then
        _new_world_bad=1
    fi
    if [ "$_new_world_bad" -eq 1 ]; then
        echo "new-project.sh: REFUSED -- --new-world's world name ('$NEW_WORLD') must match" >&2
        echo "                [a-z0-9]{1,64} (lowercase letters and digits only, at most 64" >&2
        echo "                characters) -- the intersection of the boundary service's own" >&2
        echo "                deployment-name contract ([a-z0-9-]{1,64}, no underscores/" >&2
        echo "                uppercase -- serving/boundary_multiplex_config.py spec §2) and" >&2
        echo "                the SQL-identifier allowlist ([A-Za-z0-9_]+, no hyphens) --new-world" >&2
        echo "                also derives --schema/--kern/--role from (same intersection this" >&2
        echo "                script's own --profile tracker --name check and tools/setup_tui/" >&2
        echo "                idtypes.py's WorldName enforce). Pick a compliant world name --" >&2
        echo "                there is deliberately no override: the name reaches WORLD_LABEL" >&2
        echo "                and .autoharn-world.json regardless of --schema/--kern/--role," >&2
        echo "                so no flag combination makes a non-compliant name safe." >&2
        echo "                Nothing was touched." >&2
        exit 1
    fi
    unset _new_world_bad
fi
if [ -n "$NEW_WORLD" ]; then
    # Derive, never require, the three names that must agree (P1: one source -- the world name --
    # not three hand-typed strings the caller must keep in sync). An explicit --schema/--kern/--role
    # still wins if the caller passed one (e.g. the world name collides with an existing schema).
    [ -n "$SCHEMA" ] || SCHEMA="$NEW_WORLD"
    [ -n "$KERN" ] || KERN="${NEW_WORLD}_kernel"
    [ -n "$ROLE" ] || ROLE="${NEW_WORLD}_rw"
elif [ "$PROFILE" = "tracker" ]; then
    # Identical derivation, from --name instead of a world name -- track-work.sh's own contract,
    # unchanged (an explicit --schema/--kern/--role override still wins).
    [ -n "$SCHEMA" ] || SCHEMA="$NAME"
    [ -n "$KERN" ] || KERN="${NAME}_kernel"
    [ -n "$ROLE" ] || ROLE="${NAME}_rw"
fi
[ -n "$DB" ] && [ -n "$HOST" ] && [ -n "$SCHEMA" ] && [ -n "$KERN" ] && [ -n "$ROLE" ] || usage

# OWNER: the S2b three-identity split's non-login owner role (design/FABLE-ACCESS-CONTROL-AND-
# INFORMATION-FLOW-SPEC.md §2; ledger row 600, work item ac-scaffold-identity-split). Derived from
# SCHEMA -- never SCHEMA itself, never ROLE -- the same "derive, never require" posture as SCHEMA/
# KERN/ROLE above; no override flag exists for it (nothing yet needs to name it independently, and
# adding an unused knob is its own hazard). Only meaningful when a FULL kernel birth actually runs
# below (FULL_LINEAGE, decided further down) -- this variable is otherwise unused.
OWNER="${SCHEMA}_owner"

# --- STRICT CHARACTER ALLOWLIST on every name that becomes SQL text ----------------------------
# ADR-0012's 2026-07-18 amendment ("The interpreter boundary -- a value never crosses as program
# text") + ADR-0000's same-day Rule 2(a) amendment (ledger row 1637: this exact raw-interpolation-
# into-psql shape, fixed first in bootstrap/teardown-world.sh, commit 0ce5055): SCHEMA/KERN/ROLE
# reach SQL text below (as psql -v bind identifiers where a carrier exists, and directly spliced
# into PL/pgSQL DO-block bodies where a carrier genuinely does not -- psql's :"var" substitution is
# plain client-side text substitution and does NOT reach inside a dollar-quoted DO $bw$...$bw$ body,
# verified live against 192.168.122.1 db toy before this fix was written) -- this scaffold had NO
# validation on these names at all before this fix, unlike teardown-world.sh's sibling check. This
# is the SAME allowlist, checked before ANY SQL is built, covering both --new-world's own derivation
# and a hand-picked --schema/--kern/--role override alike (a caller can pass either, and both reach
# the identical downstream SQL sites).
for _name in "$SCHEMA" "$KERN" "$ROLE" "$OWNER"; do
    case "$_name" in
        ''|*[!A-Za-z0-9_]*)
            echo "new-project.sh: REFUSED -- '$_name' contains characters outside the allowlist" >&2
            echo "                for a schema/kernel/role/owner name (letters, digits, underscore" >&2
            echo "                only). This applies to --new-world-derived names and to --schema/" >&2
            echo "                --kern/--role overrides alike (OWNER is itself derived from SCHEMA," >&2
            echo "                never separately supplied). Nothing was touched." >&2
            exit 1
            ;;
    esac
done
unset _name

# FULL_LINEAGE: the ONE gate that decides whether this run applies the full kernel birth chain
# (preflight guard, DDL apply, stamp secret, genesis seed, s40/s43 birth sequence) -- true for
# BOTH --new-world and --profile tracker, which now share this exact code path (ADR-0012 P1: one
# birth sequence, not two drifting copies of stamp-secret/genesis-seed/principal-registration
# logic). WORLD_LABEL is the human-readable name used in this run's own echo lines below, since
# $NEW_WORLD is empty in tracker mode.
FULL_LINEAGE=0
[ -n "$NEW_WORLD" ] && FULL_LINEAGE=1
[ "$PROFILE" = "tracker" ] && FULL_LINEAGE=1
# Top-level default (set -u is active below) -- classic --schema/--kern/--role mode never enters
# the FULL_LINEAGE branch that would otherwise set this, but the unconditional deployment.json
# write further down reads it regardless of mode; a classic-mode scaffold applies no kernel DDL
# at all, so the S2b split plainly does not apply and this stays false for it.
OWNER_ACCESS_SPLIT=false
if [ -n "$NEW_WORLD" ]; then
    WORLD_LABEL="$NEW_WORLD"
else
    WORLD_LABEL="$NAME (--profile tracker)"
fi
# The scratch-naming test below (used to decide whether the printed teardown-world.sh recovery
# command needs --force-non-scratch) applies to --new-world's own $NEW_WORLD name when present,
# and to --name otherwise (tracker mode has no separate world name).
SCRATCH_NAME_CHECK="${NEW_WORLD:-$NAME}"

# LINEAGE_CHAIN: what kernel DDL THIS scaffold run applied (or didn't), for the PROVENANCE header
# below -- the honest record of which sNN deltas this world was born on, so a future reader never
# has to reconstruct it from source the way run3's own history had to be reconstructed.
#
# FORMAT (usability review finding 18, ledger row 1180): one line per generation, not the single
# ~9,000-character run-on paragraph this used to be. Each bullet below is separated by a literal
# `\n` (two characters, not a newline byte) -- `sedsubst`'s `s|__LINEAGE_CHAIN__|$LINEAGE_CHAIN|g`
# is fed as a single `-e` argument, and this sed does not accept a real embedded newline there
# (tested: "unterminated `s' command"), but DOES expand a literal `\n` in the replacement text to
# a real newline in its output -- so HOOKS.md itself renders as an actual multi-line list; only
# this shell variable's own source representation uses the two-character escape. No prose below
# was altered from the paragraph it replaces (ADR-0020) -- every clause, ratification reference,
# and HISTORY-safe note is byte-identical, split at each generation's own existing sentence
# boundary rather than reworded.
if [ -n "$NEW_WORLD" ]; then
    LINEAGE_CHAIN="s15 -> s17-stamp-mechanism -> s17-independence-vocabulary -> s19 -> s20 -> s21-session-aware-distinctness -> s22-work-item-ledger -> s23-per-invocation-stamp-token -> s24-declared-event-time -> s25-commission-kind -> s26-row-hash-chain -> s27-chain-high-water -> s28-work-parent-edge -> s29-obligation-item-key-and-typed-close -> s30-typed-dependency-edges -> s31-supersession-uniform-retraction -> s32-edge-views-single-home -> s33-composite-discharge -> s34-computed-grade-refusal -> s35-validation-decomposition -> s36-decision-grade -> s37-violation-disposition -> s38-bookkeeping-close -> s39-blocks-start -> s40-principal-identity-events -> s41-principal-bindings-and-relations -> s42-row-hash-full-coverage -> s43-typed-verdict-write-boundary -> s44-model-identity-attestation -> s45-standing-lifecycle -> s46-credited-views -> s47-claim-on-closed-refusal -> s48-review-witness-existence -> s49-journaler-overflow-guard -> s50-defeat-input-raw-domain -> s51-artifact-store -> s52-artifact-witness-check -> s53-belief-substrate -> s54-belief-views -> s55-dispatch-grain-independence -> s56-reservation-residue -> s57-obligation-revocation-event -> s58-missive-substrate -> s59-missive-views -> s60-entitlement-enforcement -> s61-signature-symmetry-and-key-binding -> s62-delegation-lifecycle-gating -> s63-supersession-body-restoration -> s64-principal-stamps-delegation-conditions -> s65-refusal-attempted-kind -> s66-forged-stamp-journal-totality -> s67-refusal-digest-bound -> s68-typed-absence-dispositions -> s69-role-coherence-refusals -> s70-scope-binding (via kernel/lineage/high_watermark_1.sql + kernel/lineage/s20-obligation-grants-and-view-refresh.sql + kernel/lineage/s21-session-aware-distinctness.sql + kernel/lineage/s22-work-item-ledger.sql + kernel/lineage/s23-per-invocation-stamp-token.sql + kernel/lineage/s24-declared-event-time.sql + kernel/lineage/s25-commission-kind.sql + kernel/lineage/s26-row-hash-chain.sql + kernel/lineage/s27-chain-high-water.sql + kernel/lineage/s28-work-parent-edge.sql + kernel/lineage/s29-obligation-item-key-and-typed-close.sql + kernel/lineage/s30-typed-dependency-edges.sql + kernel/lineage/s31-supersession-uniform-retraction.sql + kernel/lineage/s32-edge-views-single-home.sql + kernel/lineage/s33-composite-discharge.sql + kernel/lineage/s34-computed-grade-refusal.sql + kernel/lineage/s35-validation-decomposition.sql + kernel/lineage/s36-decision-grade.sql + kernel/lineage/s37-violation-disposition.sql + kernel/lineage/s38-bookkeeping-close.sql + kernel/lineage/s39-blocks-start.sql + kernel/lineage/s40-principal-identity-events.sql + kernel/lineage/s41-principal-bindings-and-relations.sql + kernel/lineage/s42-row-hash-full-coverage.sql + kernel/lineage/s43-typed-verdict-write-boundary.sql + kernel/lineage/s44-model-identity-attestation.sql + kernel/lineage/s45-standing-lifecycle.sql + kernel/lineage/s46-credited-views.sql + kernel/lineage/s47-claim-on-closed-refusal.sql + kernel/lineage/s48-review-witness-existence.sql + kernel/lineage/s49-journaler-overflow-guard.sql + kernel/lineage/s50-defeat-input-raw-domain.sql + kernel/lineage/s51-artifact-store.sql + kernel/lineage/s52-artifact-witness-check.sql + kernel/lineage/s53-belief-substrate.sql + kernel/lineage/s54-belief-views.sql + kernel/lineage/s55-dispatch-grain-independence.sql + kernel/lineage/s56-reservation-residue.sql + kernel/lineage/s57-obligation-revocation-event.sql + kernel/lineage/s58-missive-substrate.sql + kernel/lineage/s59-missive-views.sql + kernel/lineage/s60-entitlement-enforcement.sql + kernel/lineage/s61-signature-symmetry-and-key-binding.sql + kernel/lineage/s62-delegation-lifecycle-gating.sql + kernel/lineage/s63-supersession-body-restoration.sql + kernel/lineage/s64-principal-stamps-delegation-conditions.sql + kernel/lineage/s65-refusal-attempted-kind.sql + kernel/lineage/s66-forged-stamp-journal-totality.sql + kernel/lineage/s67-refusal-digest-bound.sql + kernel/lineage/s68-typed-absence-dispositions.sql + kernel/lineage/s69-role-coherence-refusals.sql + kernel/lineage/s70-scope-binding.sql), applied automatically by this --new-world run, delta by delta:\n- s29 wired in via its sec-10 migration-epoch amendment (ledger decision row 935's conditional ratification), which yields epoch=0 on this empty, freshly-scaffolded ledger (see that file's own AMENDMENT header for why)\n- s30 (typed dependency edges, ledger decision row 1018) needs no epoch machinery of its own -- HISTORY: safe, see that file's own header\n- s31 (supersession uniform retraction, ratified spec design/FABLE-SUPERSESSION-UNIFORM-RETRACTION-SPEC.md) re-issues readers only, no epoch, HISTORY: safe per its own header\n- s32 (edge-views-single-home) is a pure refactor, output-equality witnessed, HISTORY: safe per its own header\n- s33 (composite-discharge, ratified spec design/FABLE-COMPOSITE-DISCHARGE-SPEC.md) adds an opt-in typed column + refusals, nothing relaxed, HISTORY: safe per its own header\n- s34 (computed-grade refusal) adds one refusal, class-ratified fail-safe, HISTORY: safe per its own header\n- s35 (validation decomposition) is a pure refactor -- every refusal text byte-identical, leaf byte-identity gate polices future re-issues -- HISTORY: safe per its own header\n- s36 (decision grade, ratified spec design/FABLE-GRADED-DECISIONS-SPEC.md) adds a nullable writer-supplied column + one derived view, nothing relaxed, HISTORY: safe per its own header\n- s37 (violation disposition, ratified spec design/FABLE-ORPHAN-DISPOSITION-SPEC.md v3) adds one kind + validator and re-issues the violations/history views, nothing relaxed, HISTORY: safe per its own header\n- s38 (bookkeeping close, ratified spec design/FABLE-BOOKKEEPING-CLOSE-SPEC.md) widens the review-disposition vocabulary to a third, machine-verified value (a git-commit witness, existence-checked CLI-side) plus one new narrowing CHECK and one new audit view, re-issue-only / additive-vocabulary, HISTORY: safe per its own header\n- s39 (blocks-start, the maintainer's claim-time precondition-foreclosure commission) widens the edge_type vocabulary to a third value (blocks-start), adds a claim-time refusal (a new validate_work_item_claim leaf) and two new derived views (work_edge_blocks_start, work_startable), nothing existing relaxed, HISTORY: safe per its own header\n- s40 (principal identity events, ratified spec design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md, first of the s40/s41 family) makes identity facts append-only attributed ledger events (four new kinds), derives standing (kernel.principal_standing), converts kernel.principal_role from table to derived view, re-issues set_actor as strict-declared-default attribution, and couples the anchor to its registration event -- NOT class-ratified fail-safe (table->view + live trigger re-issue), ships under its own ratified spec; HISTORY: safe per its own header, and this scaffold's own birth sequence below discharges the three explicit s40 birth acts (author registration event, standing declaration, reviewer/commissioner ceremony)\n- s41 (principal bindings and relations, second of the same ratified family) adds the four binding/relation event kinds (typed acts-for/dispatched-by/same-natural-person/succeeds edges, role bindings, human-only key-binding slots, G13 competence grants), the human-attested managerial/financial independence scoping (D-6), and retires the anchor's acts_for column by CHECK -- NOT class-ratified fail-safe, ships under the same ratified spec; HISTORY: safe per its own header, no birth act of its own\n- s42 (row-hash full coverage, ratified spec design/FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md, first of the s42/s43 family) re-issues compute_row_hash so the tamper-evidence chain serializes EVERY ledger column except row_hash itself (52 at this head; the 22 post-s26 columns were outside the chain, ledger row 1449), held complete forever by gates/hash_coverage_gate.py -- NOT class-ratified fail-safe (it changes what row_hash MEANS), ships under its own ratified spec; HISTORY: safe per its own header (function/view re-issues and brand-new objects only, no history-validating statement over pre-existing rows -- true of any deployment this delta reaches, not merely a fresh scaffold), no birth act of its own\n- s43 (typed-verdict write boundary, second of the same ratified s42/s43 family) REVOKES the granted role's INSERT on every kernel-governed table and makes four SECURITY DEFINER jsonb-payload functions (ledger_write/review_write/registration_write/obligation_write) the only write path -- a refusal is caught inside them, journaled as a committed write_refused ledger row (attributed to the write-boundary tool principal, digest-only payload, R4) and returned as a typed verdict, never an abort; adds the refusal_seq completeness oracle (reconciled by ./verify-chain), re-issues set_actor on session_user, and re-issues compute_row_hash to 58 columns under s42's own law -- NOT class-ratified fail-safe, ships under the same ratified spec; HISTORY: safe per its own header, and this scaffold's birth sequence below routes every birth act through the boundary functions and adds two s43 birth acts (the login-role standing declaration and the write-boundary principal registration)\n- s45 (standing lifecycle, ratified spec design/FABLE-STANDING-LIFECYCLE-SPEC.md, maintainer batch ratification ledger row 1481) licenses principal_binding_active on principal_standing_declared and principal_suspended (deliberately NOT principal_revoked -- that absence IS ratified terminal-by-type), re-issues kernel.principal_role with resurrection-proof governing-row semantics, re-issues the standing functions with the in-force filter a lift needs to be observable, and re-issues validate_supersession_target with a same-kind identity-continuous supersession discipline for the three lifecycle kinds -- NOT class-ratified fail-safe (four live re-issues), ships under its own ratification; HISTORY: safe per its own header, and this scaffold's standing declarations above now carry principal_binding_active true\n- s44 (model-identity attestation) adds the model_identity_attested kind, seven attest_* columns under two-way kind-shape CHECKs with closed grade/verdict vocabularies, a self-table FK making the attested target's existence structural, the model_attestations view, and re-issues compute_row_hash to 65 columns under s42's law -- additive kind + refusals, nothing relaxed, supersession deliberately allowed (contrast s43 R6); HISTORY: safe per its own header\n- s46 (credited views) adds the defeat-calculus display layer (model_defeated_rows + credited_current), additive derived views, nothing relaxed; HISTORY: safe per its own header (its defeat-input exclusion domain is re-issued by s50 below, ruling ledger row 1647)\n- s47 (claim-on-closed refusal, maintainer-prioritized 2026-07-18) prepends a third claim-time precondition -- a slug with an in-force work_closed row is not claimable -- class 2(a) fail-safe additive refusal; HISTORY: safe per its own header\n- s48 (review-witness row existence, spec design/FABLE-KERNEL-INTAKE-PAIR-SPEC.md delta 1, ledger row 1600) verifies at insert time that row:<id> tokens in the review-witness position of close-family kinds cite rows that exist -- class 2(a) fail-safe additive refusal, prose refs deliberately untouched; HISTORY: safe per its own header\n- s49 (journaler overflow guard, same spec delta 2, ledger row 1581, built under the maintainer's direct instruction) totalizes the attempted-identity resolution inside kernel.journal_write_refusal so an over-bigint actor string is journaled with attempted-id NULL instead of aborting the refusal recording -- strictly fail-safe effect, more refusals recorded, nothing newly permitted; HISTORY: safe per its own header\n- s50 (defeat-input raw domain, ratified spec design/FABLE-S46-DEFEAT-INPUT-DOMAIN-SPEC.md, maintainer-delegated ruling ledger row 1647) re-issues model_defeated_rows so its defeat-input exclusion quantifies over raw history, matching both engine producers -- protective-only, the defeated set can only shrink (witnessed WS46-c); HISTORY: safe per its own header. CHAIN ACT: s44 + s46-s50 entered by the maintainer's ratified act of 2026-07-18 (prepared by the orchestrator, ratified via the decision queue; the first --new-world run after this entry is the six deltas' first sequential witness as a chain)\n- s51 (artifact store, ratified spec design/FABLE-ARTIFACT-STORE-SPEC.md accepted as-is ledger row 1666, essential-records admission criterion row 1665) adds kernel.artifact -- content-addressed, append-only custody for bytes a ledger row's evidentiary force relies on -- and kernel.artifact_write, the fifth SECURITY DEFINER boundary function in s43's own verdict/journaling shape (refusals journaled digest-only, bytes never in the journal; artifact_too_large typed at 1 MiB; closed media vocabulary) -- NOT class-ratified fail-safe (new write path), ships under its accepted spec; HISTORY: safe per its own header\n- CHAIN ACT: s51 entered by the maintainer's ruling of 2026-07-18 (ledger row 1673 item 1)\n- s52 (artifact witness check, ratified spec design/FABLE-ARTIFACT-WITNESS-CHECK-SPEC.md, build ratified row 1673 item 2, merged row 1675) makes artifact:<hash> tokens in the review-witness position of the two close-family kinds insert-time existence-checked against kernel.artifact, malformed tokens refusing in the same shape -- class 2(a) fail-safe additive refusal, s48's sibling arms and prose refs untouched, judge --layer work AGREE both polarities; HISTORY: safe per its own header\n- CHAIN ACT: s52 entered by the maintainer's ruling of 2026-07-18 ('Well, we'll apply s52.')\n- s53 (belief substrate, ratified spec design/FABLE-BELIEF-SUBSTRATE-SPEC.md v2 Delta B1, ledger rows 1914/1919) adds the belief kind, nine belief_* columns under two-way (polarity/basis) and one-way (the other seven) kind-shape CHECKs plus five polarity/basis coupling CHECKs, two new refusal triggers (validate_belief_evidence, validate_belief_edges), one belief branch added to validate_supersession_target (a belief is revised only by its own holder; a cross-principal supersession attempt is refused, the correct act being a CONTEST), and re-issues compute_row_hash/ledger_current/countersigned_in_force to 74 columns under s42's law -- NOT class-ratified fail-safe (it mints vocabulary the whole project will reason in, per that spec's own §11), ships under its own ratification; HISTORY: safe per its own header\n- s54 (belief views, same spec v2 Delta B2) adds the typed-arm-only display layer (belief_current, contested_beliefs, credited_beliefs, corroboration, shared_premise), additive derived views, nothing relaxed, zero new columns/kinds; HISTORY: safe per its own header\n- s55 (dispatch-grain independence, same spec v2 Delta B3, Q6) widens review_detail_independence_check by one member (disclosed-isolated-dispatch), an honest disclosure treated exactly as self-review, zero function/trigger edits; HISTORY: safe per its own header. CHAIN ACT: s53/s54/s55 entered by this build's own commission (design/FABLE-BELIEF-SUBSTRATE-SPEC.md, ratified ledger rows 1914/1919), the s40-s44 same-commit-wiring precedent, chosen because this build's own task requires scratch witnessing via --new-world\n- s56 (reservation residue, Fable-authored spec design/FABLE-RESERVATION-RESIDUE-SPEC.md, maintainer-ratified 2026-07-22 against autoharn2 ledger rows 1093-1095) widens discharging_attest (s32's own single home) IN PLACE to also discharge attest_with_reservations verdicts, and adds two additive views (reservations_outstanding, review_verdicts) -- VIEW-ONLY, zero new ledger columns, zero new kinds, compute_row_hash untouched; HISTORY: safe per its own header\n- s57 (obligation revocation as a typed event, design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part A, maintainer-ratified in the same act as Parts B/C, ledger row 1150) adds the obligation_revoked kind (two mandatory columns, kind-shape CHECKs split from value CHECKs per the s40 house idiom) and kernel.obligation_revoke, the SIXTH SECURITY DEFINER write-boundary function (reuses s43's write_verdict type and journal_write_refusal unchanged) -- NOT class-ratified fail-safe (new write path + kind), ships under its own ratification; HISTORY: safe per its own header. CHAIN ACT: s56/s57 entered by this closing-batch build (ledger rows 1176/1178), following the s53-s55 same-commit-wiring precedent immediately above -- this --new-world run is the two deltas' first sequential witness as a chain, both detect queries (s56.detect.sql, s57.detect.sql) exercised against the newborn below.\n- s58 (missive substrate, design/FABLE-MISSIVES-KERNEL-SPEC.md, Fable-authored OUT OF FRAME, maintainer-ratified AS IT STANDS 2026-07-25 ledger row 1263, AMENDMENT 1 folded in) adds three new ledger kinds (missive_sent, missive_received, missive_disposed), ten missive_-prefixed kind-scoped columns carrying the wire envelope as typed columns (the envelope IS the row shape, ADR-0012 P7), the one-row kernel.world_identity table, the birth-registered courier principal's kind-allowlist trigger (validate_missive_courier_scope), and kernel.missive_dispose(jsonb), the fifth-family SECURITY DEFINER ceremony function -- NOT class-ratified fail-safe (new write paths + vocabulary), ships under its own ratification; HISTORY: safe per its own header. kernel.world_identity is written ONCE by a future world's birth sequence, not this one (s58's own header, ELEMENT 1) -- an s58 world with an empty world_identity refuses every missive write loudly, fail-safe and disclosed, never a silent gap; this scaffold run does not populate it, named here rather than silently assumed.\n- s59 (missive views, same spec §3, AMENDMENT 2 folded in) adds six new derived views (missive_outbound, missive_receipts, missive_undisposed, missive_stale, missive_delivery_audit, missive_open_threads), view-only, zero new ledger columns, zero new kinds, compute_row_hash untouched -- missive_outbound is the one declared raw-ledger-reading exception (transport is not truth, the s37/s56 precedent, restated one family over); HISTORY: safe per its own header. CHAIN ACT: s58/s59 entered by the maintainer's ratification of 2026-07-25 (ledger row 1263, \"FABLE-MISSIVES-KERNEL-SPEC ratified as it stands -- s58/s59 build unblocked, dispatching\"), wired into this chain by work item lineage-chain-lags-directory (ledger rows 1392/1393) after the s61 evidence round surfaced the gap -- every fixture before this build had masked the absence by applying lineage itself.\n- s60 (entitlement enforcement, design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §1, the ratified assembly basis -- rows 1379/1380 ratify design/CONSULT-WORK-GATING-SHAPE-2026-07-26.md §§B-C as the elaborated content the spec cites) adds one new kind (entitlement_class_configured), one new column (entitlement_act_class) plus a widened re-use of an existing column, one new BEFORE INSERT trigger member (validate_entitlement) coexisting with the existing chain members (validate_principal_binding/validate_supersession_target/validate_work_item), and read-only derived views/functions -- FAIL-SAFE-ADDITIVE (CLAUDE.md 2026-07-09 class rule): only adds refusals, nothing existing relaxed, no existing CHECK narrowed, no existing trigger body re-issued; HISTORY: safe per its own header. This scaffold's own s60 birth sequence (steps 5-6 below, appended after the existing s40/s43 acts, gated on the entitlement_act_class column) binds 'author' to role 'authority' and configures the default act-class role map -- see that code's own inline comment for why this ordering lets the binding act itself pass conjunct (a) vacuously. CHAIN ACT: s60 entered by the same ratified act as s58/s59's chain entry above (rows 1379/1380, maintainer-ratified 2026-07-26), this build (ledger rows 1392/1393) being the first --new-world run to wire the missives/entitlement family in as a single, sequential, witnessed chain; s61/s62 were authored on unmerged branches as of this build's own base and were deliberately NOT wired at that point (wiring an unmerged delta into a birth chain would violate the runs-are-linear discipline); both merged to main during this same session (s61 merge ledger row 1402, s62 merge row 1409) and their entries below were added at this branch's own merge, exactly the moment gates/lineage_chain_coverage.py (added by this build) demanded them -- the gate doing its job on its first live occasion.\n- s61 (signature symmetry and key binding, design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md section 2 v1.1, merged row 1402 after a fresh-context re-lap CLEARED all functional claims and a convergence check returned CONVERGED, rows 1395/1400) adds the commission/signature event kinds and their kind-scoped columns, SIGNED-supersession symmetry inside validate_supersession_target's single home, verify-against-the-s41-key-binding with the BINDING-VERIFIED vs DIRECTORY-VERIFIED grade split, proof-of-possession at bind time, revocation via the s41 retraction event, and the MULTIPLE-VALID-SIGNATURES typed refusal in both callers -- NOT class-ratified fail-safe (new kinds + live trigger re-issue), shipped under its own reviewed evidence rounds; HISTORY: safe per its own header, no birth act of its own (key bindings are operator acts, agent keys stay refused by ratified design)\n- s62 (delegation-lifecycle gating, spec section 1 AMENDMENT row 1385, three review rounds to CLEARS -- rows 1394/1398/1403/1407/1408 -- merged row 1409) closes the self-servable-chain hole the maintainer's own question found: acts-for assertion and supersession classify as act class delegation_lifecycle requiring the writer's chain-to-genesis, and the round-2 general rule makes severance an act against the TARGET's class (superseding any classified row requires that class's entitlement IN ADDITION to the candidate's own, entitlement_act_class_of_target + entitlement_enforce_class applied twice) -- FAIL-SAFE-ADDITIVE (only adds refusals) with the round-2 restructure shipped under three fresh-context review rounds; HISTORY: safe per its own header; no birth act of its own (genesis's own first edges pass chain-to-genesis trivially, witnessed by the setup-tui ceremony fixture's S62 world end-to-end). CHAIN ACT: s61/s62 wired at this branch's merge into a main that already carried both files, by the orchestrator under the same work item (rows 1392/1393) whose gate mandates exactly this wiring.\n- s63 (supersession-body restoration, design/FABLE-S63-SUPERSESSION-BODY-RESTORATION-SPEC.md, ledger rows 1429/1430) re-issues validate_supersession_target ONE more time with the UNION body -- s58 Element 5's four dropped branches (belief holder-only revision, missive_sent same-thread-successor-only, missive_received unconditionally unretractable, missive_disposed same-regards-only), each byte-diffed VERBATIM back in, plus s61 Element 7's symmetry block retained VERBATIM -- repairing s61's own stale-base defect (s61 cited s45, not the true immediately-prior s58, silently deleting all four branches; row 1430) -- FAIL-SAFE-ADDITIVE per CLAUDE.md's 2026-07-09 class rule (spec §5, resolved 2026-07-26: permits nothing new, returns the kernel to what s53/s58 already ratified, no per-delta maintainer question); ships with gates/lineage_reissue_lineage.py, a generic two-check DETECTOR for this exact false-stale-base class (citation + prior-body hash) for any multiply-defined lineage function; not yet wired into any enforcement path (not hooks/pre-commit, no other invocation site) -- wiring it is a separate maintainer session-gap hooks decision, tracked at ledger row 1438; HISTORY: safe per its own header, no birth act of its own.\n- s64 (principal-stamps delegation conditions, design/FABLE-PRINCIPAL-STAMPS-SPEC.md §3 item 1, maintainer-ratified 2026-07-26) adds five nullable delegation-edge condition columns on principal_relation_asserted (acts-for/dispatched-by, fresh assertions only -- redelegate depth, must-countersign, expiry, scope, and the independent-verification carve-out purpose), a new sibling chain-reach function honoring scope/expiry conjunction (deliberately NOT an overload of the existing 1-arg function, gates/kernel_function_census.py's own bare-name key discipline), a derived redelegation-budget function and a countersigner-collection function (both computed fresh, never served counters), and widens entitlement_act_class_of/_target/entitlement_enforce_class/validate_entitlement to close a hazard found in reach of this same surface (dispatched-by edges were previously ungated entirely) -- FAIL-SAFE-ADDITIVE per CLAUDE.md's 2026-07-09 class rule (only adds refusals, no existing CHECK narrowed, no existing trigger's pre-existing branch edited); HISTORY: safe per its own header, no birth act of its own (delegation_lifecycle/independent_verification_delegation stay out of the default conjunct-(a) role map, matching s62's own precedent)\n- s65 (refusal journal records the attempted kind, design/FABLE-S65-REFUSAL-ATTEMPTED-KIND-SPEC.md, maintainer-ratified 2026-07-27 ledger row 1487 -- \"Yes, let's have that column\") adds one nullable column (refusal_attempted_kind, one-way kind-shape CHECK licensed only on write_refused rows) and re-issues kernel.journal_write_refusal to extract the refused payload's own 'kind' key (TOTAL -- NULL when not extractable, never aborting the refusal recording) plus compute_row_hash to 98 columns under s42's law -- NOT class-ratified fail-safe (two live function re-issues), ships under the spec's own explicit maintainer ratification of this specific column and this specific privacy-relevant revelation; HISTORY: safe per its own header, no birth act of its own\n- s66 (forged-stamp journal totality, design/FABLE-S66-S67-JOURNAL-TOTALITY-SPEC.md §1, maintainer-ratified 2026-07-27 ledger row 1519 -- \"it's yes of course\") re-issues kernel.set_stamp with ONE new branch: a forged-complete-but-invalid vendor stamp on the boundary's own write_refused journal row now records stamp_verified=false instead of raising a second time and destroying the refusal it exists to journal (witnessed double-fire: the journaler's own INSERT re-fires set_stamp on the same forged session GUCs) -- every other kind's behavior, including the raise text, stays byte-identical; NOT class-ratified fail-safe (one live trigger re-issue altering one branch), ships under its own explicit ratification; HISTORY: safe per its own header, no birth act of its own\n- s67 (refusal-digest bound, same spec §2, maintainer-ratified ledger row 1514 item 1 -- \"all should go in\") re-issues kernel.journal_write_refusal so a refused payload's canonical text over 1,048,576 bytes (the s51 artifact_too_large precedent) journals with refusal_payload_digest NULL instead of digesting an unbounded direct-psql-bypass payload -- closes the ONE constraint that would have refused this widening (refusal_payload_digest_kind_shape re-issued mandatory-two-way -> one-way, the s43/s65 attempted-actor/attempted-kind idiom); the refusal itself (surface/sqlstate/message/attempted actor/role/kind) is unaffected and journals in full regardless of payload size -- NOT class-ratified fail-safe (a live function re-issue plus a CHECK loosened), ships under its own explicit ratification; HISTORY: safe per its own header, no birth act of its own. CHAIN ACT: s66/s67 entered by the same ratified act (ledger rows 1514/1519, maintainer-ratified 2026-07-27), this build being the pair's first sequential witness as a chain (seen-red/s66-s67-journal-totality/run_fixtures.py, both polarities, red first)\n- s68 (typed absence dispositions, design/FABLE-S68-TYPED-ABSENCE-DISPOSITIONS-SPEC.md, maintainer-ratified ledger rows 1541/1542 -- \"As for the NUL sentinel, that shoulde be fixed\") extends s67's own §2 AMENDMENT discipline (ADR-0012 P11 / ADR-0008's 2026-07-27 twin: NULL is not a vocabulary member) to the two remaining implicit-sentinel columns that amendment's own item 4 named as a visible gap -- refusal_attempted_kind (s65) and refusal_attempted_actor (s43/s49) -- adding two new kind-scoped disposition columns (refusal_attempted_kind_disposition, a four-member vocabulary; refusal_attempted_actor_disposition, a three-member vocabulary), two kind-guarded coupling CHECKs (the s44/s67 idiom, one of them the classifier-taught comparator=<> variant since three of the four kind-disposition members all mean NULL), and re-issues kernel.journal_write_refusal/compute_row_hash (101 columns) accordingly -- NOT class-ratified fail-safe (two live function re-issues), ships under its own explicit maintainer ratification; HISTORY: safe per its own header, no birth act of its own. CHAIN ACT: s68 entered by the same ratified act (ledger rows 1541/1542, maintainer-ratified 2026-07-27), this build being its first sequential witness as a chain (seen-red/s68-typed-absence-dispositions/run_fixtures.py, both polarities, red first, a NEW sibling fixture family per that file's own stated choice)\n- s69 (role-coherence refusals, design/FABLE-S69-ROLE-COHERENCE-REFUSALS-SPEC.md, maintainer-ratified autoharn3 ledger row 201) closes three enforcement gaps design/WORK-ROLE-PRACTICE-EVIDENCE-2026-07-28.md §4 found unmechanized: a work_closed row's actor must equal work_item_current.claimant for its slug, bound to the CURRENT/latest claimant only (row 201 §0 -- a claim stays defeatable-and-reclaimable, never frozen to a historical holder); a row:<id> witness citation on a close must be kind IN (review, finding) or an in-force child work_opened row (the planning-close carve-in); a kind=review row's regards target must carry no in-force superseder, the refusal naming the successor id -- plus the row-201-item-5 rider re-issuing validate_supersession_target with ONLY its printed CLI spelling corrected (./led -> ./autoharn led). FAIL-SAFE-ADDITIVE for the three refusals (only adds refusals, class-ratified AND individually maintainer-ratified); the rider is a teach-text-only re-issue, ratified on its own explicit item-5 basis. Zero new columns/kinds/views (spec §3); HISTORY: safe per its own header, no birth act of its own. CHAIN ACT: s69 entered by the same ratified act (row 201, maintainer-ratified 2026-07-28), this build being its first sequential witness as a chain (seen-red/s69-role-coherence-refusals/run_fixtures.py, both polarities, red first, a NEW sibling fixture family per the spec's own §4 instruction)\n- s70 (scope binding, design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md §1b/§1c, ratified basis ledger row 639 -- \"the s70 scope-binding kernel delta, authored and scratch-witnessed, entering NO chain until the next birth\") adds ONE new kind (principal_scope_bound, the entitlement machinery's NINTH authority-bearing token, scope_binding), three new nullable columns (scope_surfaces, scope_exclusions, scope_disclosure_mode) with a value-shape function (scope_exclusions_shape_ok) enforcing the closed four-member exclusion-family vocabulary, widens principal_subject_kind_shape/principal_binding_active_kind_shape (additive, every pre-existing kind's licensing unchanged) and entitlement_act_class_of/entitlement_act_class_of_target/entitlement_enforce_class (one new branch/token each, no existing branch edited), re-issues compute_row_hash/ledger_current/countersigned_in_force to 104 columns under s42's law, and adds one new derived view (principal_scopes, the s41 D-5 principal_role_bindings shape one kind over) whose fail-safe default is the OPEN scope for a principal with no bound row -- FAIL-SAFE-ADDITIVE per CLAUDE.md's 2026-07-09 class rule (only adds refusals/vocabulary/derived views, nothing existing relaxed), ships under its own ratified spec basis (row 639) since it also mints the ninth authority-bearing entitlement token, not the bare class rule alone; HISTORY: safe per its own header, no birth act of its own (scope_binding is deliberately left out of the default conjunct-(a) role map, the s62/s64 precedent). NOT YET ENFORCED at any boundary route -- the serving-layer filter (spec §2) and read-path identity/journaling (spec §1a) are named, flagged follow-ons this delta does not build; a world carrying this kernel delta alone is byte-identical in every served response to a world without it. Authored + scratch-witnessed (seen-red/s70-scope-binding/, ALL GREEN, banked red.txt -- ledger row 732); the commit-blocker this delta's own absence from THIS narrative caused was adjudicated DISSOLVED, not waived (ledger row 794: the gate was correctly demanding this exact entry, no gate exception, no forced commit). CHAIN ACT: s70 entered by this completion round under that adjudication (rows 639/732/794), this build being its first sequential witness as a chain (seen-red/s70-scope-binding/run_fixtures.py, both polarities, red first)."
    # --new-world ALSO auto-seeds the stamp secret (below) -- HOOKS.md must say so, not repeat the
    # generic "one manual step remains" text verbatim: an operator who trusted that stale claim and
    # re-ran the seeding block would TRUNCATE + re-INSERT an already-provisioned secret, ROTATING it
    # and invalidating every stamp already written under it (the exact hazard the block's own
    # comment warns against). Fixed here rather than left for the next reader to trip over.
    STAMP_SECRET_STATUS="**Already provisioned automatically by this --new-world scaffold run (see PROVENANCE above) — do NOT re-run the block below; re-seeding ROTATES the secret and invalidates every stamp already written under it. Shown for reference/recovery only.**"
    # s21 is now part of THIS world's birth lineage (line above) -- the template's own s21 status
    # bullet must say so, not the stale "NOT applied by any scaffold mode" claim (BACKLOG 2026-07-09,
    # "make the s21-and-future-delta apply step scriptable" mandate, piece 2).
    S21_STATUS="Applied automatically by this --new-world scaffold run (see the lineage chain above) -- this world's kernel already carries s21's (stamp_session, stamp_agent) pair-keyed distinctness and the s19 residue fix. No separate apply is needed."
    # REVIEWER_STATUS: mirrors the STAMP_SECRET_STATUS/S21_STATUS pattern above -- the honest,
    # mode-aware record of whether the `reviewer` principal this world's root CLAUDE.md.tmpl talks
    # about ("a reviewer principal exists") is actually true yet (BACKLOG "Maintainer ruling:
    # self-application", 2026-07-09 -- "starting a run becomes a verb": the operator no longer
    # hand-registers this principal for a --new-world scaffold).
    REVIEWER_STATUS="Registered automatically by this --new-world scaffold run through the s40 ceremony (principal 'reviewer', class subagent, purpose stated, a principal_registered event on the ledger; see the birth-sequence step in this same run, right after the stamp secret above) -- do NOT re-register; a repeat \`./autoharn led register-principal reviewer ...\` is REFUSED loudly with teach-text (s40 deleted the silent ON CONFLICT no-op), and the scaffold's own re-run existence check prints 'already registered' instead of attempting one."
    # COMMISSIONER_STATUS: mirrors REVIEWER_STATUS exactly -- the honest, mode-aware record of
    # whether the 'commissioner' principal (kernel/lineage/s25-commission-kind.sql's FULL signing
    # mode; BACKLOG "Five-item batch, maintainer-approved 2026-07-11 evening", item 2) exists yet.
    # Registering it here, alongside 'reviewer', means the maintainer's OWN signing act (see the
    # printed copy-paste line at the end of this script) never has to register its own principal
    # first -- the same "starting a run becomes a verb" closure REVIEWER_STATUS already documents.
    COMMISSIONER_STATUS="Registered automatically by this --new-world scaffold run through the s40 ceremony (principal 'commissioner', class human, purpose stated, a principal_registered event on the ledger; see the birth-sequence step in this same run, right after 'reviewer' above) -- do NOT re-register; a repeat is REFUSED loudly (s40 deleted the silent ON CONFLICT no-op), and the scaffold's own re-run existence check prints 'already registered' instead of attempting one. FULL-mode signing (the maintainer signs the ask himself): \`LED_ACTOR=commissioner ./autoharn led commission \"<the ask verbatim>\"\` -- typed by the maintainer in his OWN terminal, inside this world. LAZY-mode (the implementer vicariously transcribes the ask on receiving it, first ledger act, no commissioner guarantee): see this world's CLAUDE.md preamble."
else
    LINEAGE_CHAIN="NOT applied by this scaffold run -- apply a kernel lineage to $SCHEMA/$KERN/$ROLE manually (kernel/lineage/, see kernel/lineage/README.md) before first use"
    STAMP_SECRET_STATUS="**One manual step remains: provision the stamp secret. UNWITNESSED — the block below has not been run in this instance.**"
    S21_STATUS="NOT applied by this scaffold run (classic --schema/--kern/--role mode applies no kernel lineage at all -- see item 1 above). If this world's kernel predates s21, apply it as a separate, explicit operator act from autoharn's own checkout: \`bootstrap/apply-delta.sh <this-project's-directory> kernel/lineage/s21-session-aware-distinctness.sql\` (prints the resolved command, requires a typed schema confirmation, never applies bare) -- status/witness live in autoharn's BACKLOG.md (search \"s21\")."
    REVIEWER_STATUS="NOT registered by this scaffold run (classic --schema/--kern/--role mode applies no kernel lineage at all -- see item 1 above, so there is no \`principal\` table yet to register into). Once a kernel lineage is applied, register one explicitly: \`./autoharn led register-principal reviewer subagent\`."
    COMMISSIONER_STATUS="NOT registered by this scaffold run (classic --schema/--kern/--role mode applies no kernel lineage at all -- see item 1 above). Once a kernel lineage carrying kernel/lineage/s25-commission-kind.sql is applied, register one explicitly: \`./autoharn led register-principal commissioner human\`."
fi

AUTOHARN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# The single-home shim verb set (tracker item submodule-shim-set-drift, ledger row 1182) --
# THIS script's own scaffold loop below is the authority every other bootstrap script that
# writes or discovers these shims now sources instead of re-listing them by hand.
. "$AUTOHARN_ROOT/bootstrap/shim-verbs.sh"

# AUTOHARN_COMMIT -- the autoharn checkout's own commit hash at scaffold time, so a world's
# evidence can be tied to the INSTRUMENT VERSION that produced it (prior regulator-panel
# assessment's Tier-1 item 4: "no record ties a historical DENY to the hook bytes that produced
# it" -- vestigial_documentation/design/MAINT-RELITIGATION-SYNTHESIS.md, "No configuration index"). Read once, here,
# never re-derived: this same value is written into the PROVENANCE header below (ADR-0012 P1).
# Degrades honestly rather than silently blank -- a git failure or a dirty checkout are both
# real facts about the instrument that produced this world, not to be hidden behind an empty
# string (ADR-0002).
AUTOHARN_COMMIT_SHA="$(cd "$AUTOHARN_ROOT" && git rev-parse HEAD 2>/dev/null || true)"
AUTOHARN_COMMIT="$AUTOHARN_COMMIT_SHA"
AUTOHARN_DIRTY=0
if [ -n "$AUTOHARN_COMMIT" ]; then
    if ! (cd "$AUTOHARN_ROOT" && git diff --quiet && git diff --cached --quiet) 2>/dev/null; then
        AUTOHARN_DIRTY=1
        AUTOHARN_COMMIT="$AUTOHARN_COMMIT (DIRTY -- uncommitted changes were present in the autoharn checkout at scaffold time; this world's evidence cannot be reproduced from this commit hash alone)"
    fi
else
    AUTOHARN_COMMIT="UNAVAILABLE -- $AUTOHARN_ROOT is not a git checkout, or git is not on PATH (git rev-parse HEAD failed); this world's evidence cannot be tied to an instrument version by commit hash"
fi

# --pin submodule needs a REPRODUCIBLE commit to pin to -- a dirty or unavailable checkout would
# pin a deployment to bytes that cannot be reconstructed from the SHA alone, defeating the whole
# point (ADR-0002: refuse loudly rather than pin to a lie).
if [ "$PIN" = "submodule" ]; then
    if [ -z "$AUTOHARN_COMMIT_SHA" ]; then
        echo "new-project.sh: --pin submodule requires this autoharn checkout ($AUTOHARN_ROOT) to be" >&2
        echo "                a git repository with git on PATH -- git rev-parse HEAD failed." >&2
        exit 1
    fi
    if [ "$AUTOHARN_DIRTY" -eq 1 ]; then
        echo "new-project.sh: --pin submodule refuses to pin a deployment to a DIRTY autoharn" >&2
        echo "                checkout ($AUTOHARN_ROOT has uncommitted changes) -- the pinned SHA" >&2
        echo "                would not reproduce what actually gets copied into the submodule." >&2
        echo "                Commit or stash the changes in $AUTOHARN_ROOT, then re-run." >&2
        exit 1
    fi
fi

TEMPLATES="$AUTOHARN_ROOT/bootstrap/templates"
PY="$HOME/w/vdc/venvs/generic/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"

# PRE-WRITE VALIDATION (fix-round finding 1, autoharn3 row 101 re-review, 2026-07-28): the ONE
# place, on the --new-world/classic/--profile flow, where TEMPLATES first becomes resolvable --
# so this is the earliest point _scan_verb_templates()'s glob-plus-header check CAN run, and
# nothing this script writes (deployment.json, .autoharn-world.json, .gitignore, .claude/*,
# keys/, attestations/, roles/, the dispatcher itself, ...) has been written yet. Calling it here
# makes every one of this script's "Nothing was touched" refusal messages true on every path,
# including this one -- _write_world_dispatcher()'s own later call to the same function (near the
# END of the scaffold sequence, where the roster is actually consumed to write ./autoharn) is now
# a cheap, already-validated re-check, never the first place a header-less template is caught.
# Discards the DISPATCH_TABLE/VERB_ROSTER this validation-only call computes as a side effect --
# _write_world_dispatcher() recomputes them later itself (the templates directory cannot change
# mid-run) rather than threading state across the many intervening scaffold-writing sections.
_scan_verb_templates

# design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md §3: the FOREIGN-content refusal, BEFORE
# `mkdir -p` (this used to `mkdir -p` and merge into ANY occupied directory lacking
# deployment.json, silently -- the defect the spec's commission names). AUTOHARN_COMPLETE/
# AUTOHARN_PARTIAL are untouched here -- they keep the deployment.json-exists/--force gate below,
# unchanged. `classify_destination` is bootstrap/classify-destination.sh's own shell
# re-derivation of tools/setup_tui/destination.py's Python classifier (that module is the
# authority; see this sourced file's own header for why the two are kept in sync by a parity
# fixture, not codegen).
. "$AUTOHARN_ROOT/bootstrap/classify-destination.sh"
DEST_KIND="$(classify_destination "$DEST")"
if [ "$DEST_KIND" = "foreign" ] && [ "$ACCEPT_EXISTING_CONTENT" -ne 1 ]; then
    echo "new-project.sh: REFUSED -- '$DEST' is non-empty and carries no autoharn birth" >&2
    echo "                evidence (FOREIGN, design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md)." >&2
    echo "                Pass --accept-existing-content to scaffold into it anyway (the setup" >&2
    echo "                TUI passes this exactly when its fork-target screen recorded the" >&2
    echo "                operator's typed acknowledgment). Nothing touched." >&2
    exit 1
fi

# deploy-feature-manifest (ledger row 1274/1322): resolve the feature manifest BEFORE any
# filesystem/DB act (same "refuse before touching anything" posture every check above this line
# already follows). `_FEAT_PARSE.py` is a closed-schema JSON validator, never a bare tomllib/
# json.loads trusted further -- unknown keys, a bad TIER value, or a malformed principal_set row
# all REFUSE loudly here, nothing partially applied. Emits shell-assignable `KEY=value` lines
# (python's own `shlex.quote`, never hand-rolled escaping) for `eval`, plus a temp file of
# principal_set rows (name<TAB>agent_class<TAB>purpose per line) bash can loop over without
# re-parsing JSON itself.
F_PORTABLE_ADRS=""            # "" = not set by --features-file; 1/0 once resolved below
F_VENDORED_SKILLS=""
F_PANEL_EXTENSION=""
F_MAKESPAN_TIER=""
F_PRINCIPAL_SET_FILE=""
if [ -n "$FEATURES_FILE" ]; then
    [ -f "$FEATURES_FILE" ] || {
        echo "new-project.sh: --features-file '$FEATURES_FILE' does not exist. Nothing touched." >&2
        exit 1
    }
    _FEAT_ROWS_FILE="$(mktemp)"
    _FEAT_EVAL="$("$PY" - "$FEATURES_FILE" "$_FEAT_ROWS_FILE" <<'PYEOF'
import json, shlex, sys

path, rows_path = sys.argv[1], sys.argv[2]
CLOSED_KEYS = {"features_format", "portable_adrs", "vendored_skills", "panel_extension",
               "makespan_scheduler_tier", "principal_set"}
TIERS = {"off", "available", "blessed", "mandated", "forbidden"}
CLASSES = {"human", "model", "subagent", "tool"}
RESERVED = {"author", "reviewer", "commissioner", "write-boundary"}

def refuse(msg):
    print(f"new-project.sh: --features-file '{path}' REFUSED -- {msg}", file=sys.stderr)
    sys.exit(1)

try:
    with open(path, "r", encoding="utf-8") as f:
        doc = json.load(f)
except (OSError, json.JSONDecodeError) as exc:
    refuse(f"could not read/parse as JSON: {exc}")
if not isinstance(doc, dict):
    refuse("top level must be a JSON object")
unknown = sorted(set(doc) - CLOSED_KEYS)
if unknown:
    refuse(f"unknown key(s) (closed schema): {', '.join(unknown)}")

portable_adrs = doc.get("portable_adrs", True)
vendored_skills = doc.get("vendored_skills", True)
panel_extension = doc.get("panel_extension", False)
tier = doc.get("makespan_scheduler_tier", "off")
principal_set = doc.get("principal_set", [])

for name, val in (("portable_adrs", portable_adrs), ("vendored_skills", vendored_skills),
                  ("panel_extension", panel_extension)):
    if not isinstance(val, bool):
        refuse(f"'{name}' must be a JSON boolean, got {val!r}")
if tier not in TIERS:
    refuse(f"'makespan_scheduler_tier' must be one of {sorted(TIERS)}, got {tier!r}")
if not isinstance(principal_set, list):
    refuse("'principal_set' must be a JSON array")

seen = set()
rows = []
for i, row in enumerate(principal_set):
    if not isinstance(row, dict) or {"name", "agent_class", "purpose"} - set(row):
        refuse(f"'principal_set'[{i}] must be an object with name/agent_class/purpose")
    name, cls, purpose = row["name"], row["agent_class"], row["purpose"]
    if not isinstance(name, str) or not name.strip():
        refuse(f"'principal_set'[{i}].name must be a non-empty string")
    if name in RESERVED:
        refuse(f"'principal_set'[{i}].name '{name}' is reserved -- registered automatically by "
                f"every --new-world birth's own s40/s43 ceremony; do not re-declare it")
    if name in seen:
        refuse(f"'principal_set' declares '{name}' more than once")
    seen.add(name)
    if cls not in CLASSES:
        refuse(f"'principal_set'[{i}].agent_class must be one of {sorted(CLASSES)}, got {cls!r}")
    if not isinstance(purpose, str) or not purpose.strip():
        refuse(f"'principal_set'[{i}].purpose must be a non-empty string")
    rows.append((name, cls, purpose))

with open(rows_path, "w", encoding="utf-8") as f:
    for name, cls, purpose in rows:
        f.write(f"{name}\t{cls}\t{purpose}\n")

print(f"F_PORTABLE_ADRS={shlex.quote('1' if portable_adrs else '0')}")
print(f"F_VENDORED_SKILLS={shlex.quote('1' if vendored_skills else '0')}")
print(f"F_PANEL_EXTENSION={shlex.quote('1' if panel_extension else '0')}")
print(f"F_MAKESPAN_TIER={shlex.quote(tier)}")
PYEOF
    )" || exit 1
    eval "$_FEAT_EVAL"
    F_PRINCIPAL_SET_FILE="$_FEAT_ROWS_FILE"
fi
# Discrete-flag / --features-file overlap: refused, never silently resolved one way (ADR-0002).
if [ -n "$FEATURES_FILE" ] && [ "$_VENDOR_SKILLS_GIVEN" -eq 1 ]; then
    echo "new-project.sh: --no-vendored-skills AND --features-file both set vendored_skills --" >&2
    echo "                ambiguous. Pick one authority for this decision. Nothing touched." >&2
    exit 1
fi
if [ -n "$FEATURES_FILE" ] && [ "$_PANEL_EXTENSION_GIVEN" -eq 1 ]; then
    echo "new-project.sh: --panel-extension AND --features-file both set panel_extension --" >&2
    echo "                ambiguous. Pick one authority for this decision. Nothing touched." >&2
    exit 1
fi
if [ -n "$FEATURES_FILE" ] && [ "$_MAKESPAN_TIER_GIVEN" -eq 1 ]; then
    echo "new-project.sh: --makespan-tier AND --features-file both set makespan_scheduler_tier --" >&2
    echo "                ambiguous. Pick one authority for this decision. Nothing touched." >&2
    exit 1
fi
# Reconcile into the ONE set of vars the rest of this script reads from here on, regardless of
# whether the decision came from --features-file, a discrete flag, or (absent both) today's
# unchanged default.
if [ -n "$FEATURES_FILE" ]; then
    [ "$F_PORTABLE_ADRS" = "0" ] && LAW_SECTION=0
    [ "$F_VENDORED_SKILLS" = "0" ] && VENDOR_SKILLS=0
    [ "$F_PANEL_EXTENSION" = "1" ] && PANEL_EXTENSION=1
    MAKESPAN_TIER="$F_MAKESPAN_TIER"
fi
if [ "$MAKESPAN_TIER" != "off" ] && [ "$MAKESPAN_TIER" != "available" ] \
   && [ "$MAKESPAN_TIER" != "blessed" ] && [ "$MAKESPAN_TIER" != "mandated" ] \
   && [ "$MAKESPAN_TIER" != "forbidden" ]; then
    echo "new-project.sh: --makespan-tier '$MAKESPAN_TIER' is not recognized (must be one of" >&2
    echo "                off/available/blessed/mandated/forbidden). Nothing touched." >&2
    exit 1
fi
if [ -n "$F_PRINCIPAL_SET_FILE" ] && [ -s "$F_PRINCIPAL_SET_FILE" ] && [ "$FULL_LINEAGE" -ne 1 ]; then
    echo "new-project.sh: REFUSED -- --features-file declares a non-empty principal_set, but this" >&2
    echo "                run applies no kernel lineage at all (neither --new-world nor --profile" >&2
    echo "                tracker) -- there is no principal table yet to register into. Nothing" >&2
    echo "                touched." >&2
    exit 1
fi

mkdir -p "$DEST"
PROJECT_ROOT="$(cd "$DEST" && pwd)"
[ -n "$NAME" ] || NAME="$(basename "$PROJECT_ROOT")"

DEPLOYMENT="$PROJECT_ROOT/deployment.json"
if [ -f "$DEPLOYMENT" ] && [ "$FORCE" -ne 1 ]; then
    echo "new-project.sh: $DEPLOYMENT already exists -- refusing to overwrite (pass --force to replace it)." >&2
    exit 1
fi

echo "== stamping instance at $PROJECT_ROOT (name=$NAME) =="

# EXEC_ROOT -- the autoharn tree every operator verb + hook actually points at. Unpinned (the
# default, unchanged from before this flag existed): the live checkout, $AUTOHARN_ROOT, same as
# every world scaffolded before this build. --pin submodule: a FROZEN copy of THIS commit, living
# inside the deployment's own git tree at $PROJECT_ROOT/.autoharn -- design/ORCH-DEPLOYMENT-
# PINNING.md's whole point (a deployment stops executing another project's mutable working tree).
EXEC_ROOT="$AUTOHARN_ROOT"
if [ "$PIN" = "submodule" ]; then
    echo "-- --pin submodule: pinning autoharn@$AUTOHARN_COMMIT_SHA into $PROJECT_ROOT/.autoharn --"
    if [ -e "$PROJECT_ROOT/.autoharn" ] && [ "$FORCE" -ne 1 ]; then
        echo "new-project.sh: $PROJECT_ROOT/.autoharn already exists -- refusing to overwrite" >&2
        echo "                (pass --force to replace it, or this deployment is already pinned)." >&2
        exit 1
    fi
    if [ -e "$PROJECT_ROOT/.autoharn" ] && [ "$FORCE" -eq 1 ]; then
        echo "   --force: removing existing $PROJECT_ROOT/.autoharn before re-adding"
        (cd "$PROJECT_ROOT" && git submodule deinit -f .autoharn 2>/dev/null || true)
        rm -rf "$PROJECT_ROOT/.autoharn" "$PROJECT_ROOT/.git/modules/.autoharn"
    fi
    if (cd "$PROJECT_ROOT" && git rev-parse --is-inside-work-tree >/dev/null 2>&1); then
        echo "   $PROJECT_ROOT is already a git repository -- using it"
    else
        echo "   $PROJECT_ROOT is not yet a git repository -- running git init"
        (cd "$PROJECT_ROOT" && git init --quiet)
    fi
    # Default submodule URL: THIS checkout's own on-disk path -- a plain local-filesystem submodule
    # git supports natively, works with no network access, and is HONEST about its portability
    # limit (printed below). --pin-url overrides with a real remote for a submodule another
    # machine can also fetch.
    SUBMODULE_URL="${PIN_URL:-$AUTOHARN_ROOT}"
    # -c protocol.file.allow=always: ONLY set when SUBMODULE_URL is a local filesystem path (the
    # default absent --pin-url) -- git 2.38.1+ (CVE-2022-39253) refuses the "file" transport for a
    # submodule's internal clone unless explicitly allowed, even though `git submodule add` itself
    # was a direct, deliberate operator/scaffold action. A real remote URL (--pin-url) never needs
    # this override.
    _submodule_add_opts=""
    case "$SUBMODULE_URL" in
        *://*) ;;  # a real URL (https://, ssh://, git://, ...) -- no override needed
        *) _submodule_add_opts="-c protocol.file.allow=always" ;;
    esac
    (cd "$PROJECT_ROOT" && git $_submodule_add_opts submodule add --quiet "$SUBMODULE_URL" .autoharn)
    (cd "$PROJECT_ROOT/.autoharn" && git checkout --quiet "$AUTOHARN_COMMIT_SHA")
    (cd "$PROJECT_ROOT" && git add .gitmodules .autoharn)
    echo "   submodule added and pinned to $AUTOHARN_COMMIT_SHA (staged; this scaffold run commits"
    echo "   it, along with the operator verbs + hook wiring it points at, at the end of this run)"
    if [ -z "$PIN_URL" ]; then
        echo "   NOTE: submodule URL is a LOCAL PATH ($SUBMODULE_URL) -- this deployment's git clone"
        echo "   is portable on THIS machine only. For a submodule another machine can also fetch,"
        echo "   re-run with --pin-url <a real git remote for autoharn>."
    fi
    EXEC_ROOT="$PROJECT_ROOT/.autoharn"
fi

if [ "$FULL_LINEAGE" -eq 1 ]; then
    # --profile tracker's OWN idempotent-force contract, mirrored from the retired
    # bootstrap/track-work.sh (ledger row 1271, "mirror the semantics of track-work.sh"):
    # that script's own --force NEVER re-ran kernel DDL against a schema that already carried it
    # ("--force's job is 're-point/rewrite deployment.json and the verb shims', never 're-run
    # kernel DDL a second time'" -- its own header comment) -- it checked whether the kernel
    # schema already existed and, if so, SKIPPED the DDL apply entirely, continuing straight to
    # deployment.json/shims/principals. `--new-world` never had this idempotent-force shape (a
    # world is born once; the DB-SIDE PRE-FLIGHT GUARD below refuses unconditionally on ANY
    # existing relation, by design) -- sharing this file's FULL_LINEAGE code path between the two
    # modes would otherwise silently REGRESS track-work.sh's own documented --force contract for
    # tracker deployments (discovered live during this build: a `--profile tracker ... --force`
    # re-scaffold against an already-birthed deployment hit the SAME hard preflight refusal
    # `--new-world` uses, which never happened under the retired script). Fixed here, scoped
    # strictly to `--profile tracker`: skip the preflight-guard + DDL-apply block below entirely
    # when this profile's own kernel schema already exists, regardless of --force (mirroring
    # track-work.sh's own KERNEL_ALREADY_APPLIED check) -- the birth sequence further below still
    # runs its own idempotent existence checks (already provisioned / already registered), so
    # deployment.json, the verb shims, and the principals still re-derive correctly either way.
    SKIP_LINEAGE_APPLY=0
    # OWNER_ACCESS_SPLIT: whether THIS run performs (or, on a skipped re-run, previously
    # performed) the S2b three-identity split below -- becomes deployment.json's own
    # `owner_access_split` declaration. Defaults false; set true only inside the fresh-lineage-
    # apply branch further down. When lineage apply is SKIPPED (an already-migrated schema, the
    # `--profile tracker --force` re-derive case immediately below), this run makes no ownership
    # change at all -- so the flag must carry forward whatever this deployment's EXISTING
    # deployment.json already declared (a pre-S2b world re-run through --force must not start
    # falsely claiming the split; a post-S2b world re-run through --force must not lose the
    # declaration it already earned), never a blind reset to false.
    OWNER_ACCESS_SPLIT=false
    if [ "$PROFILE" = "tracker" ]; then
        _tracker_kernel_exists="$(printf '%s\n' "SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = :'kern');" \
            | psql -h "$HOST" -d "$DB" -v kern="$KERN" -tA)"
        if [ "$_tracker_kernel_exists" = "t" ]; then
            SKIP_LINEAGE_APPLY=1
            echo "-- $WORLD_LABEL: kernel schema '$KERN' already exists -- SKIPPING the DDL"
            echo "   re-apply (bootstrap/track-work.sh's own --force contract, mirrored: re-running"
            echo "   the full birth chain against an already-migrated schema is not safe -- CREATE"
            echo "   OR REPLACE VIEW cannot drop columns intermediate deltas already added). --force"
            echo "   here re-derives deployment.json + the verb shims + the boundary config + the"
            echo "   principals only; it does not touch existing kernel structure or ledger rows."
            if [ -f "$DEPLOYMENT" ]; then
                _prior_oas="$("$PY" -c "
import json
try:
    with open('$DEPLOYMENT', encoding='utf-8') as f:
        d = json.load(f)
    print('true' if d.get('owner_access_split') else 'false')
except Exception:
    print('false')
" 2>/dev/null)"
                [ "$_prior_oas" = "true" ] && OWNER_ACCESS_SPLIT=true
                echo "   owner_access_split carried forward from existing deployment.json: $OWNER_ACCESS_SPLIT"
                unset _prior_oas
            fi
        fi
        unset _tracker_kernel_exists
    fi
if [ "$SKIP_LINEAGE_APPLY" -ne 1 ]; then
    # DB-SIDE PRE-FLIGHT GUARD (ledger row 1148's ratified direction, reproduced mechanism):
    # `CREATE TABLE IF NOT EXISTS` silently SKIPS a wrong-shaped leftover relation from a prior,
    # partial birth, and s15-schema.sql's later `INSERT ... ON CONFLICT (db_role)` then dies
    # because the skipped table's own PK never got created -- the "s15 dead end" row 1148 closed:
    # re-birth over partial DB state, not a kernel defect. This mirrors the dest-DIRECTORY guard
    # above (classify_destination, ~line 336) but on the DATABASE side: query the catalog for
    # ANY existing relation under the target schema OR kernel-schema namespaces, BEFORE any DDL
    # below runs, and refuse loudly rather than walk in and die partway through. Queried live,
    # right here (never cached) -- a rehearsal that just tore its own scratch world down to zero
    # residue (teardown-world.sh's own verified-zero-residue step) sees an empty catalog and
    # passes; only genuine leftover state trips this.
    _preflight_psql_in() { printf '%s\n' "$1"; }
    PREFLIGHT_RELS=$(_preflight_psql_in \
        "SELECT n.nspname || '.' || c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname IN (:'schema', :'kern') AND c.relkind IN ('r','v','m','p','S') ORDER BY 1;" \
        | psql -h "$HOST" -d "$DB" -v schema="$SCHEMA" -v kern="$KERN" -tA)
    PREFLIGHT_COUNT=$(printf '%s\n' "$PREFLIGHT_RELS" | grep -c . || true)
    if [ "$PREFLIGHT_COUNT" -gt 0 ]; then
        PREFLIGHT_SAMPLE=$(printf '%s\n' "$PREFLIGHT_RELS" | head -5 | sed 's/^/     - /')
        # Same scratch-safe naming test teardown-world.sh itself applies to $NEW_WORLD -- so the
        # teardown command this refusal prints is the EXACT command that will succeed, including
        # the --force-non-scratch flag when (and only when) the world name needs it.
        PREFLIGHT_FORCE_FLAG=""
        case "$SCRATCH_NAME_CHECK" in
            run[0-9]*|s[0-9]*|faqwit*|svcfx*|probeworld*|*_scratch) ;;
            *) PREFLIGHT_FORCE_FLAG=" --force-non-scratch" ;;
        esac
        echo "new-project.sh: REFUSED -- schema '$SCHEMA' and/or kernel schema '$KERN' in $DB@$HOST" >&2
        echo "                already carry $PREFLIGHT_COUNT relation(s)/object(s) -- this is NOT" >&2
        echo "                an empty target for a fresh --new-world birth. Found (up to 5 shown):" >&2
        printf '%s\n' "$PREFLIGHT_SAMPLE" >&2
        echo "                Re-birthing a kernel lineage over partial DB state is the known s15" >&2
        echo "                dead end (ledger row 1148): CREATE TABLE IF NOT EXISTS silently skips" >&2
        echo "                a wrong-shaped leftover table, and s15's own ON CONFLICT (db_role)" >&2
        echo "                insert later dies because that skipped table's PK was never created." >&2
        echo "                Clear it first with the sanctioned teardown verb, then re-run:" >&2
        echo "                    bootstrap/teardown-world.sh $SCRATCH_NAME_CHECK --db $DB --host $HOST \\" >&2
        echo "                        --schema $SCHEMA --kern $KERN --role $ROLE$PREFLIGHT_FORCE_FLAG" >&2
        echo "                Nothing was touched -- no DDL below has run yet." >&2
        exit 1
    fi
    unset -f _preflight_psql_in

    # THE APPLY LIST IS GENERATED, not hand-typed (ledger rows 1392/1393/1399, fix round for
    # work item lineage-chain-lags-directory): a hand-typed `-f` block and the tracked
    # kernel/lineage/ directory have no structural link, so they drifted (s58-s60 landed in the
    # directory and stayed absent from this block for a day-plus). This loop derives the list
    # LIVE from the directory every run: every kernel/lineage/sNN-<slug>.sql file (a plain
    # top-level delta -- its own .detect.sql/.verify.sql/.accommodate*.sql companions are never
    # separately applied, see gates/lineage_chain_coverage.py's own NAMING SPACE writeup) with
    # N >= 20 is picked up, sorted NUMERICALLY by N (s9 vs s10 lexical-sort class bug avoided --
    # `sort -t: -k1,1n`, not a plain string sort). N < 20 (s10-s14, s17-s19) and non-sNN files
    # (high_watermark_1.sql, nla-schema.sql) are excluded exactly as the prior hand-typed block
    # excluded them -- see high_watermark_1.sql's own header: s15/s17/s19 arrive transitively via
    # its \ir chain, s18 is excluded there as Study-mode-only apparatus, s10-s14 are dead/
    # superseded pre-consolidation schema iterations, never separately applied by this scaffold.
    # gates/lineage_chain_coverage.py polices this loop's own threshold/exclusion contract
    # against the directory (does it exist, anchored; does its MIN_N/exclusion set match reality)
    # -- it does not, and structurally cannot, regex-scan a `-f` list that no longer exists here.
    _LINEAGE_APPLY_MIN_N=20
    _lineage_apply_entries=""
    for _lf in "$AUTOHARN_ROOT"/kernel/lineage/s[0-9]*-*.sql; do
        [ -e "$_lf" ] || continue
        _lbase=$(basename "$_lf")
        case "$_lbase" in
            *.detect.sql|*.verify.sql|*.accommodate.sql|*.accommodate.verify.sql) continue ;;
        esac
        _ln=${_lbase#s}
        _ln=${_ln%%-*}
        case "$_ln" in
            ''|*[!0-9]*) continue ;;
        esac
        [ "$_ln" -ge "$_LINEAGE_APPLY_MIN_N" ] || continue
        _lineage_apply_entries="$_lineage_apply_entries$_ln:$_lbase
"
    done
    _lineage_apply_sorted=$(printf '%s' "$_lineage_apply_entries" | sort -t: -k1,1n)
    unset _lineage_apply_entries _lf _lbase _ln

    _lineage_apply_desc=""
    for _entry in $_lineage_apply_sorted; do
        _lineage_apply_desc="$_lineage_apply_desc + s${_entry%%:*}"
    done
    _lineage_apply_desc=${_lineage_apply_desc# + }
    unset _entry
    echo "-- $WORLD_LABEL: applying high_watermark_1.sql + $_lineage_apply_desc to $DB (schema=$SCHEMA kern=$KERN role=$ROLE) --"

    _apply_lineage_deltas() {
        # A function's positional parameters are its OWN scope (POSIX: temporarily replaced on
        # call, restored on return) -- `set --` here builds a scratch `-f` argument list without
        # touching this script's own $1/$2/... (the dest-dir/--db/... CLI args parsed at the top
        # of this file). Mirrors this file's existing _preflight_psql_in/_psql_in house idiom
        # (defined, used, `unset -f`'d) rather than introducing a new pattern.
        set --
        for _entry in $_lineage_apply_sorted; do
            set -- "$@" -f "$AUTOHARN_ROOT/kernel/lineage/${_entry#*:}"
        done
        psql -h "$HOST" -d "$DB" -v ON_ERROR_STOP=1 \
            -v schema="$SCHEMA" -v kern="$KERN" -v role="$ROLE" \
            -f "$AUTOHARN_ROOT/kernel/lineage/high_watermark_1.sql" \
            "$@"
    }
    _apply_lineage_deltas
    unset -f _apply_lineage_deltas
    unset _lineage_apply_sorted _lineage_apply_desc _LINEAGE_APPLY_MIN_N _entry

    echo "   kernel applied (schema $SCHEMA + kernel schema $KERN + role $ROLE, s20 + s21 + s22 + s23 + s24 + s25 + s26 + s27 + s28 + s29 + s30 + s31 + s32 + s33 + s34 + s35 + s36 + s37 + s38 + s39 + s40 + s41 + s42 + s43 + s44 + s45 + s46 + s47 + s48 + s49 + s50 + s51 + s52 + s53 + s54 + s55 + s56 + s57 + s58 + s59 + s60 + s61 + s62 + s63 included -- s29's migration_epoch naturally seeds 0 on this empty ledger, see that file's own AMENDMENT header; s30 needs no epoch machinery of its own, HISTORY: safe; s40's own birth acts run below, after the seeds; s45 licenses principal_binding_active on the two standing-lifecycle kinds and is honored by the standing declarations below, which now carry the flag; s56/s57 are view-only/new-write-path respectively, neither needs a birth-sequence act of its own; s58's kernel.world_identity is left empty by this run (a future world's own birth act, s58's own header) -- missive writes refuse loudly, fail-safe, until an operator populates it; s59 is view-only; s60's own birth sequence (role bind + default act-class map) runs below, gated on the entitlement_act_class column this delta adds; s61 needs no birth act (key bindings are operator acts); s62 needs no birth act (genesis's first edges pass chain-to-genesis trivially); s63 needs no birth act of its own (a same-function re-issue, no new columns/kinds))"

    # S2b THREE-IDENTITY SPLIT (design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md §2;
    # ledger row 600, work item ac-scaffold-identity-split). Every relation/sequence/function the
    # lineage apply above just created is, at this point, owned by whichever identity ran THIS
    # script's own psql connection (the invoking superuser -- no -U was given anywhere above, so
    # it is the operator's own connecting identity, peer/trust-authenticated, per this cluster's
    # existing convention -- see kernel/lineage/s15-schema.sql's own header, "Run as the schema
    # owner (bork)"). Row 600's REJECTED shape is the granted access role ($ROLE) owning the
    # schema; that is NOT what happens today (the access role is merely GRANTed privileges by the
    # lineage files, never CREATE SCHEMA'd as), but neither is today's shape the RATIFIED one: the
    # owner today is the shared, LOGIN-capable superuser identity, not a role scoped to this world
    # and confined to birth-time use. This block closes that gap, WITHOUT editing any frozen
    # kernel/lineage/*.sql file (CLAUDE.md: nobody edits kernel/lineage without a Fable-authored,
    # maintainer-ratified spec -- this spec is that ratified basis, but the delta it authorizes is
    # scoped to THIS scaffold script, not the lineage files themselves): it REASSIGNS ownership of
    # every object the lineage apply just created, from the invoking superuser to a freshly
    # created, NON-LOGIN owner role ($OWNER) -- never granting that role membership to $ROLE, and
    # never granting $ROLE membership in it, so pg_has_role($ROLE, $OWNER, 'USAGE') stays false
    # (row 600's own correctness point: an owner-member connecting role could bypass its own
    # REVOKEs). ALTER ... OWNER TO does not touch existing GRANTs (an ACL entry is independent of
    # ownership), so every `GRANT ... TO :role` the lineage files already issued -- while the
    # objects were still owned by the invoker -- survives this reassignment unchanged; SECURITY
    # DEFINER functions (s17/s27/s40/s43/s44/s45/s51/s57/s58, ...) now execute as $OWNER instead of
    # as the invoker, which is the load-bearing change s43 Element 8's own session_user-keyed
    # set_actor() (re-issued at s43, unaffected by this reassignment) was already written to
    # tolerate: attribution keys on session_user (the real login identity), never on current_user
    # (which SECURITY DEFINER changes to the function's owner) -- so this split changes WHO OWNS,
    # never WHAT IS GRANTED or WHO IS ATTRIBUTED. Scoped to exactly the two namespaces this run
    # just created (never a blanket `REASSIGN OWNED BY`, which would also reassign every OTHER
    # world's objects this same invoking identity happens to own in a shared database -- this
    # project's own provisioning convention, bootstrap/provision-db.sh's header comment, is one
    # shared db / one schema pair per project, so a blanket reassign is a real collateral-damage
    # hazard, not a hypothetical one). Future births only (runs-are-linear): this whole block sits
    # inside the same `if [ "$SKIP_LINEAGE_APPLY" -ne 1 ]` guard as the lineage apply itself, so a
    # `--profile tracker --force` re-run against an ALREADY-migrated schema never re-enters here
    # (SKIP_LINEAGE_APPLY=1 short-circuits the entire enclosing block) -- no existing world's
    # ownership is ever touched by this script.
    echo "-- $WORLD_LABEL: S2b three-identity split -- creating non-login owner role '$OWNER' and reassigning schema/kern ownership to it (ledger row 600) --"
    psql -h "$HOST" -d "$DB" -q -v ON_ERROR_STOP=1 -v owner="$OWNER" <<'SQL'
SELECT NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'owner') AS need_owner \gset
\if :need_owner
CREATE ROLE :"owner" NOLOGIN;
\endif
SQL
    psql -h "$HOST" -d "$DB" -q -v ON_ERROR_STOP=1 -v schema="$SCHEMA" -v kern="$KERN" -v owner="$OWNER" <<'SQL'
SELECT set_config('birth.owner', :'owner', false),
       set_config('birth.schema', :'schema', false),
       set_config('birth.kern', :'kern', false);
DO $reassign$
DECLARE
    r         record;
    v_owner   text := current_setting('birth.owner');
    v_schema  text := current_setting('birth.schema');
    v_kern    text := current_setting('birth.kern');
    v_relkind text;
BEGIN
    EXECUTE format('ALTER SCHEMA %I OWNER TO %I', v_schema, v_owner);
    EXECUTE format('ALTER SCHEMA %I OWNER TO %I', v_kern, v_owner);
    -- Sequences LINKED to a serial/identity/GENERATED column (pg_depend deptype 'a'/'i') take
    -- their owner FROM that column's table automatically -- Postgres itself REFUSES an explicit
    -- `ALTER SEQUENCE ... OWNER TO` on one ("cannot change owner of sequence ...  linked to
    -- table ..."), witnessed live against this exact schema (every bigserial PK sequence here,
    -- e.g. kernel.principal_id_seq). Excluded from this loop for that reason -- their ownership
    -- already followed the table's ALTER above; only a genuinely STANDALONE sequence (e.g.
    -- kernel.refusal_seq, s43's own hand-created sequence, not a column's serial backing) needs
    -- its own explicit reassignment.
    -- Composite types (relkind 'c', e.g. s43's write_verdict) are objects in this namespace pair
    -- just like tables/views -- pre-fix this loop never reassigned them, leaving every composite
    -- type owned by the invoking superuser even after schema+kern+every table/view/function moved
    -- to the split owner (a hazard within reach of this exact block, fixed here rather than routed
    -- around). The auto-generated array type (e.g. `_write_verdict`) is NOT independently
    -- ALTERable -- Postgres refuses a direct `ALTER TYPE _foo OWNER TO ...` ("cannot alter array
    -- type") -- but its ownership is not left behind: Postgres propagates the base composite
    -- type's OWNER TO change to its array type internally, verified live (see the witness step
    -- for this fix).
    FOR r IN
        SELECT n.nspname, c.relname, c.relkind
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname IN (v_schema, v_kern) AND c.relkind IN ('r','v','m','p','c')
        UNION ALL
        SELECT n.nspname, c.relname, c.relkind
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname IN (v_schema, v_kern) AND c.relkind = 'S'
          AND NOT EXISTS (SELECT 1 FROM pg_depend d
                          WHERE d.objid = c.oid AND d.deptype IN ('a', 'i'))
    LOOP
        v_relkind := CASE r.relkind
            WHEN 'r' THEN 'TABLE' WHEN 'p' THEN 'TABLE' WHEN 'v' THEN 'VIEW'
            WHEN 'm' THEN 'MATERIALIZED VIEW' WHEN 'S' THEN 'SEQUENCE' WHEN 'c' THEN 'TYPE' END;
        EXECUTE format('ALTER %s %I.%I OWNER TO %I', v_relkind, r.nspname, r.relname, v_owner);
    END LOOP;
    FOR r IN
        SELECT p.oid::regprocedure::text AS sig
        FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname IN (v_schema, v_kern)
    LOOP
        EXECUTE format('ALTER FUNCTION %s OWNER TO %I', r.sig, v_owner);
    END LOOP;
END
$reassign$;
SQL
    echo "   owner role '$OWNER' now owns schema '$SCHEMA', kernel schema '$KERN', and every relation/sequence/function within them (SECURITY DEFINER functions now execute as this role); role '$ROLE' holds no membership in it and owns nothing"
    OWNER_ACCESS_SPLIT=true
fi

    # _psql_in: SQL text is always fed on stdin, never via -c -- psql's :'var'/:"var" bind-variable
    # interpolation (verified live against a real server, psql 18.3) is only performed for input it
    # parses as a script (stdin or -f), and is a silent no-op under -c (the literal colon reaches the
    # server and the statement errors out). Same fix shape/rationale as bootstrap/teardown-world.sh
    # commit 0ce5055 (ledger row 1637) and this file's own allowlist block above.
    _psql_in() { printf '%s\n' "$1"; }

    echo "-- $WORLD_LABEL: seeding the stamp secret (idempotent, mirrors drive/arm.sh ruling 43) --"
    mkdir -p "$PROJECT_ROOT/.claude/secrets"
    chmod 700 "$PROJECT_ROOT/.claude/secrets"
    SECRET_FILE="$PROJECT_ROOT/.claude/secrets/stamp_secret.hex"
    HAVE=$(_psql_in "SELECT count(*) FROM :\"kern\".stamp_secret;" | psql -h "$HOST" -d "$DB" -v kern="$KERN" -tA)
    if [ "$HAVE" = "1" ]; then
        echo "   a secret is already provisioned for ${KERN}.stamp_secret (1 row); not rotating"
    else
        ( umask 077; openssl rand -hex 32 > "$SECRET_FILE" )
        chmod 600 "$SECRET_FILE"
        HEX=$(cat "$SECRET_FILE")
        # KERN reaches DROP/TRUNCATE-adjacent DDL text as an identifier bind (:"kern"), HEX as a
        # literal bind (:'hex') -- both bound as psql -v variables via stdin, never spliced into the
        # SQL string (the allowlist above already restricts KERN to [A-Za-z0-9_]+; this is the
        # primary carrier per ADR-0012's 2026-07-18 amendment, not just defense-in-depth on KERN).
        _psql_in 'TRUNCATE :"kern".stamp_secret;' \
            | psql -h "$HOST" -d "$DB" -q -v ON_ERROR_STOP=1 -v kern="$KERN"
        _psql_in "INSERT INTO :\"kern\".stamp_secret (secret) VALUES (decode(:'hex','hex'));" \
            | psql -h "$HOST" -d "$DB" -q -v ON_ERROR_STOP=1 -v kern="$KERN" -v hex="$HEX"
        echo "   one fresh secret provisioned ($SECRET_FILE [chmod 600]; DB ${KERN}.stamp_secret)"
    fi

    # GENESIS SEED (design/MAINT-GPG-TRUST-LAYER.md Rung 3; kernel/lineage/s26-row-hash-chain.sql):
    # the row_hash chain's zz_set_row_hash trigger REFUSES the first ledger INSERT loudly if no
    # seed is provisioned (see that delta's own header) -- this MUST run before the first write,
    # same ordering constraint as the stamp secret above. Idempotent (INSERT ... ON CONFLICT DO
    # NOTHING via the only_one PK, mirroring stamp_secret's own one-row-table shape) -- but unlike
    # the stamp secret, this is NOT a secret (kernel/lineage/s26-row-hash-chain.sql's GENESIS SEED
    # section explains why: its only job is making two worlds' row-1 hashes differ, not
    # confidentiality), so it is generated and inserted directly, with no on-disk file mirroring
    # the stamp-secret pattern's chmod-600 ceremony -- there is nothing here that needs hiding.
    echo "-- $WORLD_LABEL: seeding the row_hash chain's genesis seed (idempotent) --"
    HAVE_GENESIS=$(_psql_in "SELECT count(*) FROM :\"kern\".chain_genesis;" \
        | psql -h "$HOST" -d "$DB" -v kern="$KERN" -tA 2>/dev/null || echo "0")
    if [ "$HAVE_GENESIS" = "1" ]; then
        echo "   a genesis seed is already provisioned for ${KERN}.chain_genesis (1 row); not rotating"
    elif [ "$HAVE_GENESIS" = "0" ]; then
        GENESIS_HEX=$(openssl rand -hex 32)
        _psql_in "INSERT INTO :\"kern\".chain_genesis (seed) VALUES (:'genesis_hex') ON CONFLICT (only_one) DO NOTHING;" \
            | psql -h "$HOST" -d "$DB" -q -v ON_ERROR_STOP=1 -v kern="$KERN" -v genesis_hex="$GENESIS_HEX"
        echo "   one fresh genesis seed provisioned (DB ${KERN}.chain_genesis)"
    else
        echo "   ${KERN}.chain_genesis does not exist -- this world's kernel predates s26-row-hash-chain.sql; skipping (not an error, an older lineage)"
    fi

    # WORLD IDENTITY SEED (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.1, kernel/lineage/
    # s58-missive-substrate.sql): kernel.world_identity is the one-row "which world am I"
    # setting every missive write checks (validate_missive_identity aborts loudly, teach-text, on
    # an empty table -- fail-safe, s43 Element 6's write-boundary-principal precedent). This row
    # was PREVIOUSLY left unpopulated by this scaffold on purpose (s58's own header: "a future
    # world's own birth act") -- that future has arrived; work item birth-standing-steps-scaffold
    # closes the gap the autoharn3 cutover had to populate by hand (design/
    # PHOENIX-SURVIVAL-UNIVERSE-2026-07-28.md §3/§7 ranks an undiscovered-until-loud-refusal gap
    # here below the courier/revocation gaps, but still nowhere scripted before this).
    #
    # Seeded the SAME WAY the genesis seed immediately above is: a plain, idempotent, un-SET-
    # ROLE'd owner INSERT, NOT through kernel.registration_write/ledger_write (the s40/s43
    # boundary-ceremony path the principal acts below use). This is not a shortcut around the
    # boundary -- the table's own grants (s58 §2.1) are `REVOKE ALL ... GRANT SELECT ... TO
    # :role`: the granted role holds no INSERT here at all, so there IS no boundary-function path
    # to route this through, and the spec's own witness plan (§11, "per world: ... INSERT
    # world_identity (worlda/worldb) as owner") seeds it exactly this way -- an owner-direct
    # INSERT is what "boundary ceremony" cashes out to for this one table, the same footing as
    # genesis.
    #
    # world_name is $SCRATCH_NAME_CHECK -- this run's own world name ($NEW_WORLD for --new-world,
    # $NAME for --profile tracker; the same variable the preflight teardown-command hint above
    # keys off of), already validated earlier in this script against the exact `[a-z0-9]{1,64}`
    # intersection this column's own CHECK (`world_name ~ '^[a-z0-9-]{1,64}$'`, s58 §2.1, byte-
    # identical to serving/boundary_multiplex_config.py's _DEPLOYMENT_NAME_RE) requires -- EXCEPT
    # when --profile tracker is invoked with both --boundary-url and --boundary-deployment given
    # explicitly (the one case that skips this script's own --name charclass check, ~line 635);
    # that pre-existing gap is unchanged by this addition and would surface here as a loud
    # CHECK-constraint abort (ON_ERROR_STOP=1), never a silent bad row.
    echo "-- $WORLD_LABEL: seeding kernel.world_identity (idempotent) --"
    HAVE_WORLD_IDENTITY=$(_psql_in "SELECT count(*) FROM :\"kern\".world_identity;" \
        | psql -h "$HOST" -d "$DB" -v kern="$KERN" -tA 2>/dev/null || echo "0")
    if [ "$HAVE_WORLD_IDENTITY" = "1" ]; then
        echo "   ${KERN}.world_identity already carries a row; not re-seeding"
    elif [ "$HAVE_WORLD_IDENTITY" = "0" ]; then
        _psql_in "INSERT INTO :\"kern\".world_identity (world_name) VALUES (:'world_name') ON CONFLICT (one_row) DO NOTHING;" \
            | psql -h "$HOST" -d "$DB" -q -v ON_ERROR_STOP=1 -v kern="$KERN" -v world_name="$SCRATCH_NAME_CHECK"
        echo "   world_identity seeded: world_name = '$SCRATCH_NAME_CHECK' (DB ${KERN}.world_identity)"
    else
        echo "   ${KERN}.world_identity does not exist -- this world's kernel predates s58-missive-substrate.sql; skipping (not an error, an older lineage)"
    fi

    # THE s40 BIRTH SEQUENCE (kernel/lineage/s40-principal-identity-events.sql §3.7; replaces
    # the pre-s40 ON CONFLICT DO NOTHING block that stood here -- the silent-no-op idiom s40
    # deleted from the verb is replaced at the scaffold by EXISTENCE CHECKS that print "already
    # registered": idempotent at the scaffold, never silent at the verb). Three explicit acts,
    # in this order, all as the granted role (SET ROLE, never a superuser bypass), all kept in
    # lockstep with bootstrap/templates/led.tmpl's own SQL by inspection:
    #   (1) `author`'s principal_registered EVENT -- the anchor row was seeded by s15 inside the
    #       chain apply (pre-s40 position, so the anchor-coupling trigger did not exist yet);
    #       the scaffold discharges its event explicitly. THE ONE GENESIS EXCEPTION: the event
    #       is SELF-ATTRIBUTED (actor = author) -- a first identity event cannot be attributed
    #       to any earlier-registered principal, mirroring the hash chain's genesis-seed
    #       precedent for a first link that cannot reference a predecessor; the self-attribution
    #       is named in the event's own statement text.
    #   (2) a principal_standing_declared event binding this world's role to `author` (actor =
    #       author, explicit) -- the DECLARED-not-silent default every strict-mode NULL-actor
    #       write resolves through: strict-on costs the solo operator nothing, the ratified
    #       reconciliation (basis row 1398).
    #   (3) `reviewer` (subagent) and `commissioner` (human) registered through the FULL
    #       ceremony (anchor + event atomically, actor = author, purposes stated) -- the same
    #       two standard principals every world was already born with, now with recorded
    #       registrations (BACKLOG "Maintainer ruling: self-application" 2026-07-09 closure,
    #       carried forward under s40's ceremony).
    # THE s40 BIRTH ACTS, ROUTED THROUGH THE s43 WRITE BOUNDARY (kernel/lineage/
    # s43-typed-verdict-write-boundary.sql: the granted role holds NO INSERT anywhere after
    # the chain above applied -- every birth act below is a boundary-function call, and a
    # 'refused' verdict is converted back into a LOUD scaffold failure by the DO-block
    # pattern each act uses: the birth of a world is exactly the place a refusal must stop
    # the line, not land as a quiet journal row). Two NEW s43 acts join the sequence: the
    # LOGIN-role standing declaration (step 2b -- s43 Element 8's dual declaration:
    # set_actor resolves on session_user now, so the login role the world's DSN
    # authenticates as needs its own declared standing, witnessed here at scaffold time as
    # session_user) and the write-boundary tool principal's registration (step 4 -- s43
    # Element 6: the identity that authors every write_refused row).
    echo "-- $WORLD_LABEL: s40/s43 birth sequence (author event, dual standing declarations, reviewer/commissioner/write-boundary ceremony) --"
    LOGIN_ROLE=$(psql -h "$HOST" -d "$DB" -tAc "SELECT session_user;")
    HAVE_AUTHOR_EVENT=$(_psql_in "SELECT count(*) FROM :\"schema\".ledger l JOIN :\"kern\".principal p ON p.id = l.principal_subject WHERE l.kind = 'principal_registered' AND p.name = 'author';" \
        | psql -h "$HOST" -d "$DB" -v schema="$SCHEMA" -v kern="$KERN" -tA)
    if [ "$HAVE_AUTHOR_EVENT" != "0" ]; then
        echo "   'author' already carries a registration event ($HAVE_AUTHOR_EVENT); not re-registering"
    else
        psql -h "$HOST" -d "$DB" -q -v ON_ERROR_STOP=1 -v role="$ROLE" -v schema="$SCHEMA" -v kern="$KERN" <<SQL
        SET ROLE :"role";
        SET search_path = :"schema", :"kern";
        -- KERN below (write_verdict's type qualifier) is inside a dollar-quoted DO body: psql's
        -- :"var" substitution does not reach dollar-quoted text (verified live), so this one
        -- reference is guarded by the allowlist check earlier in this script, not by a bind.
        DO \$bw\$
        DECLARE v ${KERN}.write_verdict;
        BEGIN
          SELECT * INTO v FROM ${KERN}.ledger_write(jsonb_build_object(
            'kind', 'principal_registered',
            'statement', 'principal ''author'' registered (class model) -- genesis exception: self-attributed (actor = author), the first identity event of this world; no earlier-registered principal exists to attribute it to (s40 birth sequence step 1)',
            'actor', (SELECT id FROM principal WHERE name = 'author'),
            'principal_subject', (SELECT id FROM principal WHERE name = 'author'),
            'principal_purpose', 'the scaffold connection principal: the identity this world''s granted role writes as by default'));
          IF v.disposition <> 'accepted' THEN
            RAISE EXCEPTION 'birth sequence step 1 refused (SQLSTATE %): %', v.sqlstate, v.message;
          END IF;
        END \$bw\$;
SQL
        echo "   (1) 'author' registration event recorded via the write boundary (genesis exception, self-attributed)"
    fi
    for _drole in "$ROLE" "$LOGIN_ROLE"; do
        HAVE_DECL=$(_psql_in "SELECT count(*) FROM :\"schema\".ledger_current lc WHERE lc.kind = 'principal_standing_declared' AND lc.principal_db_role = :'drole';" \
            | psql -h "$HOST" -d "$DB" -v schema="$SCHEMA" -v drole="$_drole" -tA)
        if [ "$HAVE_DECL" != "0" ]; then
            echo "   role '${_drole}' already carries a standing declaration; not re-declaring"
            continue
        fi
        psql -h "$HOST" -d "$DB" -q -v ON_ERROR_STOP=1 -v role="$ROLE" -v schema="$SCHEMA" -v kern="$KERN" -v drole="$_drole" <<SQL
        SET ROLE :"role";
        SET search_path = :"schema", :"kern";
        SELECT set_config('birth.drole', :'drole', false);
        -- KERN below (write_verdict's type qualifier) is inside a dollar-quoted DO body: guarded
        -- by the allowlist check earlier in this script, not by a bind (see the step-1 comment above).
        DO \$bw\$
        DECLARE v ${KERN}.write_verdict;
        BEGIN
          SELECT * INTO v FROM ${KERN}.ledger_write(jsonb_build_object(
            'kind', 'principal_standing_declared',
            'statement', format('database role ''%s'' speaks for principal ''author'' by default (standing declaration, s40 birth sequence step 2 / s43 Element 8''s dual declaration -- the declared-not-silent default)', current_setting('birth.drole')),
            'actor', (SELECT id FROM principal WHERE name = 'author'),
            'principal_subject', (SELECT id FROM principal WHERE name = 'author'),
            'principal_db_role', current_setting('birth.drole'),
            'principal_binding_active', true));
          IF v.disposition <> 'accepted' THEN
            RAISE EXCEPTION 'birth sequence step 2 refused (SQLSTATE %): %', v.sqlstate, v.message;
          END IF;
        END \$bw\$;
SQL
        echo "   (2) standing declaration recorded via the write boundary (role ${_drole} -> author)"
    done
    for _pname in reviewer commissioner write-boundary; do
        case "$_pname" in
            reviewer)       _pclass="subagent"; _ppurpose="the standard second principal a run needs: countersigns the author principal's rows (BACKLOG self-application ruling 2026-07-09)" ;;
            commissioner)   _pclass="human";    _ppurpose="the maintainer's own registered identity for FULL-mode commission signing (s25; five-item batch 2026-07-11 item 2)" ;;
            write-boundary) _pclass="tool";     _ppurpose="the kernel write boundary's own recording identity: every write_refused meta-event is authored by this principal; the attempted identity is carried in the event's refusal_attempted_* columns (s43)" ;;
        esac
        HAVE_P=$(_psql_in "SELECT count(*) FROM :\"kern\".principal WHERE name = :'pname';" \
            | psql -h "$HOST" -d "$DB" -v kern="$KERN" -v pname="$_pname" -tA)
        if [ "$HAVE_P" != "0" ]; then
            echo "   '${_pname}' already registered; skipping"
        else
            psql -h "$HOST" -d "$DB" -q -v ON_ERROR_STOP=1 -v role="$ROLE" -v schema="$SCHEMA" -v kern="$KERN" -v pname="$_pname" -v pclass="$_pclass" -v ppurpose="$_ppurpose" <<SQL
        SET ROLE :"role";
        SET search_path = :"schema", :"kern";
        SELECT set_config('birth.pname', :'pname', false),
               set_config('birth.pclass', :'pclass', false),
               set_config('birth.ppurpose', :'ppurpose', false);
        -- KERN below (write_verdict's type qualifier) is inside a dollar-quoted DO body: guarded
        -- by the allowlist check earlier in this script, not by a bind (see the step-1 comment above).
        DO \$bw\$
        DECLARE v ${KERN}.write_verdict;
        BEGIN
          SELECT * INTO v FROM ${KERN}.registration_write(jsonb_build_object(
            'name', current_setting('birth.pname'),
            'agent_class', current_setting('birth.pclass'),
            'purpose', current_setting('birth.ppurpose'),
            'statement', format('principal ''%s'' registered (class %s) -- s40 birth sequence step 3/4, registrar: author', current_setting('birth.pname'), current_setting('birth.pclass')),
            'actor', (SELECT id FROM principal WHERE name = 'author')));
          IF v.disposition <> 'accepted' THEN
            RAISE EXCEPTION 'birth sequence step 3/4 refused (SQLSTATE %): %', v.sqlstate, v.message;
          END IF;
        END \$bw\$;
SQL
            echo "   (3/4) '${_pname}' registered through the boundary ceremony (class ${_pclass}, registrar author)"
        fi
    done

    # THE s58 COURIER BIRTH ACT (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.6, kernel/lineage/
    # s58-missive-substrate.sql): the `courier` principal, birth-registered through the SAME
    # registration_write ceremony as reviewer/commissioner/write-boundary above -- witnessed
    # missing at the experience4 birth until the first courier pull refused (autoharn3 row 122 is
    # the by-hand fix this closes structurally); this scaffold now registers it every time, no
    # operator memory required. Purpose text is the spec's own §2.6 wording, verbatim (mirrors the
    # loop above's registrar/statement shape exactly, kept as its own block rather than folded
    # into that loop's `case` because this one act is gated on s58 being present in the applied
    # chain -- reviewer/commissioner/write-boundary need only s40/s43, always present here, so
    # their loop stays unconditional). Held to the SAME idempotent existence-check shape.
    HAVE_COURIER=$(_psql_in "SELECT count(*) FROM :\"kern\".principal WHERE name = 'courier';" \
        | psql -h "$HOST" -d "$DB" -v kern="$KERN" -tA)
    if [ "$HAVE_COURIER" != "0" ]; then
        echo "   'courier' already registered; skipping"
    else
        case "$HAVE_WORLD_IDENTITY" in
            0|1)
                psql -h "$HOST" -d "$DB" -q -v ON_ERROR_STOP=1 -v role="$ROLE" -v schema="$SCHEMA" -v kern="$KERN" <<SQL
        SET ROLE :"role";
        SET search_path = :"schema", :"kern";
        DO \$bw\$
        DECLARE v ${KERN}.write_verdict;
        BEGIN
          SELECT * INTO v FROM ${KERN}.registration_write(jsonb_build_object(
            'name', 'courier',
            'agent_class', 'tool',
            'purpose', 'Records cross-world missive arrivals pulled over the boundary service -- and can write nothing else (kernel-scoped: validate_missive_courier_scope, s58; consult §4.3, Q3 ratified row 1157). Never a deciding identity.',
            'statement', 'principal ''courier'' registered (class tool) -- s58 birth act, registrar: author',
            'actor', (SELECT id FROM principal WHERE name = 'author')));
          IF v.disposition <> 'accepted' THEN
            RAISE EXCEPTION 's58 courier birth act refused (SQLSTATE %): %', v.sqlstate, v.message;
          END IF;
        END \$bw\$;
SQL
                echo "   (courier) registered through the boundary ceremony (class tool, registrar author, s58)"
                ;;
            *)
                echo "   ${KERN}.world_identity does not exist -- this world's kernel predates s58-missive-substrate.sql; 'courier' has no scope trigger to bind to here, skipping (not an error, an older lineage)"
                ;;
        esac
    fi

    # THE s60 BIRTH SEQUENCE (kernel/lineage/s60-entitlement-enforcement.sql §1.3, spec §1 item
    # 3): "solo-world zero-friction by construction... the same birth run binds the roles the
    # default configuration names." TWO new acts, APPENDED after the existing s40/s43 sequence
    # above (nothing above moved or re-ordered -- a pure append, minimal and surgically scoped
    # per this delta's own commission, chosen so this edit collides with no other in-review
    # scaffold change touching this same file):
    #   (5) bind `author` to role 'authority' (principal_role_bound, actor=author) -- written
    #       BEFORE any entitlement_class_configured row exists, so conjunct (a) reads
    #       'principal_role_bound' as UNCONFIGURED at this exact moment (vacuous) -- the
    #       ordering that lets this very act pass with zero special-casing in the kernel
    #       trigger (s60's own header names this ordering explicitly). conjunct (b) passes
    #       trivially: author IS this world's genesis principal (step 1's own self-attribution).
    #   (6) configure the DEFAULT act-class role map -- five entitlement_class_configured rows,
    #       one per s60's default-mapped authority-bearing class, all naming role 'authority'
    #       (attention point 1, marked PROVISIONAL in s60's own header: one uniform role name is
    #       this delta's own policy choice, not kernel-hardcoded -- a deployment may reconfigure
    #       by writing fresh entitlement_class_configured rows later). Each of these acts is
    #       ITSELF authority-bearing (entitlement_class_configured is in the hardcoded conjunct-
    #       (b) set, unconditionally) -- author's chain trivially reaches genesis (self), so
    #       every one of these five acts passes on conjunct (b) alone; conjunct (a) does not
    #       apply to entitlement_class_configured writes in the default map (s60's own Element 8
    #       note: the configuration surface protects itself via conjunct (b) only, never a
    #       configuration-gated conjunct (a) on itself).
    # CAPABILITY-GATED (this same guard shape as every other optional-capability check in this
    # script): entitlement_act_class is s60's own marker column -- absent on any chain that does
    # not yet carry s60. s58/s59/s60 are now wired into the consolidated apply loop above (work
    # item lineage-chain-lags-directory, ledger rows 1392/1393 -- this comment previously said the
    # scaffold's LINEAGE_CHAIN ended at s57; that gap is what this same build closed), so a fresh
    # --new-world run always has the column and this guard's SKIP branch below is now dead in
    # practice for --new-world; it stays live for the classic --schema/--kern/--role scaffold
    # mode (which applies no kernel lineage at all, see the else-branch above) and for any future
    # chain that legitimately predates s60. Skipped with a named note, never a silent no-op, on
    # any chain that lacks the column.
    HAVE_S60=$(_psql_in "SELECT count(*) FROM information_schema.columns WHERE table_schema = :'schema' AND table_name = 'ledger' AND column_name = 'entitlement_act_class';" \
        | psql -h "$HOST" -d "$DB" -v schema="$SCHEMA" -tA)
    if [ "$HAVE_S60" = "0" ]; then
        echo "-- $WORLD_LABEL: s60 birth sequence SKIPPED -- this chain does not carry kernel/lineage/s60-entitlement-enforcement.sql (no entitlement_act_class column); role-gate/entitlement-config birth acts not applicable --"
    else
        echo "-- $WORLD_LABEL: s60 birth sequence (bind author to role 'authority', configure the default act-class map) --"
        HAVE_ROLE=$(_psql_in "SELECT count(*) FROM :\"schema\".principal_role_bindings prb JOIN :\"kern\".principal p ON p.id = prb.subject WHERE p.name = 'author' AND prb.role_name = 'authority';" \
            | psql -h "$HOST" -d "$DB" -v schema="$SCHEMA" -v kern="$KERN" -tA)
        if [ "$HAVE_ROLE" != "0" ]; then
            echo "   'author' already holds role 'authority'; not re-binding"
        else
            psql -h "$HOST" -d "$DB" -q -v ON_ERROR_STOP=1 -v role="$ROLE" -v schema="$SCHEMA" -v kern="$KERN" <<SQL
        SET ROLE :"role";
        SET search_path = :"schema", :"kern";
        DO \$bw\$
        DECLARE v ${KERN}.write_verdict;
        BEGIN
          SELECT * INTO v FROM ${KERN}.ledger_write(jsonb_build_object(
            'kind', 'principal_role_bound',
            'statement', 'author bound to role ''authority'' (s60 birth sequence step 5, the default conjunct-(a) role -- kernel/lineage/s60-entitlement-enforcement.sql)',
            'actor', (SELECT id FROM principal WHERE name = 'author'),
            'principal_subject', (SELECT id FROM principal WHERE name = 'author'),
            'principal_role_name', 'authority',
            'principal_binding_active', true));
          IF v.disposition <> 'accepted' THEN
            RAISE EXCEPTION 's60 birth sequence step 5 refused (SQLSTATE %): %', v.sqlstate, v.message;
          END IF;
        END \$bw\$;
SQL
            echo "   (5) 'author' bound to role 'authority' via the write boundary"
        fi
        for _actclass in principal_registered principal_role_bound standing_lifecycle milestone_closure gate_edge_supersession; do
            HAVE_CFG=$(_psql_in "SELECT count(*) FROM :\"schema\".entitlement_class_roles WHERE act_class = :'actclass';" \
                | psql -h "$HOST" -d "$DB" -v schema="$SCHEMA" -v actclass="$_actclass" -tA)
            if [ "$HAVE_CFG" != "0" ]; then
                echo "   act class '${_actclass}' already configured; not re-configuring"
            else
                psql -h "$HOST" -d "$DB" -q -v ON_ERROR_STOP=1 -v role="$ROLE" -v schema="$SCHEMA" -v kern="$KERN" -v actclass="$_actclass" <<SQL
        SET ROLE :"role";
        SET search_path = :"schema", :"kern";
        SELECT set_config('birth.actclass', :'actclass', false);
        DO \$bw\$
        DECLARE v ${KERN}.write_verdict;
        BEGIN
          SELECT * INTO v FROM ${KERN}.ledger_write(jsonb_build_object(
            'kind', 'entitlement_class_configured',
            'statement', format('act class ''%s'' requires role ''authority'' (s60 birth sequence step 6, the default act-class map -- ATTENTION POINT 1, provisional, kernel/lineage/s60-entitlement-enforcement.sql)', current_setting('birth.actclass')),
            'actor', (SELECT id FROM principal WHERE name = 'author'),
            'entitlement_act_class', current_setting('birth.actclass'),
            'principal_role_name', 'authority'));
          IF v.disposition <> 'accepted' THEN
            RAISE EXCEPTION 's60 birth sequence step 6 refused for act class % (SQLSTATE %): %', current_setting('birth.actclass'), v.sqlstate, v.message;
          END IF;
        END \$bw\$;
SQL
                echo "   (6) act class '${_actclass}' configured -> role 'authority' via the write boundary"
            fi
        done
    fi
fi

# --profile tracker: the boundary is served via ensure-running, not a standing daemon -- pick a
# free port, write boundary-multiplex.toml, and let BOUNDARY_URL/BOUNDARY_DEPLOYMENT (still empty
# unless the caller passed --boundary-url/--boundary-deployment explicitly -- explicit always
# wins) flow into the SAME deployment.json writer every mode already shares below. Nothing is
# started now: serving/ensure_running.py's `ensure_running_or_leave_unreachable` (already wired
# into every served shim template) spawns it as a detached child on this deployment's FIRST
# `./led`/`./pickup`/etc call -- this is the mechanism that dissolved track-work.sh's own
# "a standing tracker runs no boundary service by design" rationale (that script's `legacy/led`
# gap): the boundary is no longer a thing an operator stands up by hand, it is a thing that
# appears the moment it is needed.
if [ "$PROFILE" = "tracker" ] && [ -z "$BOUNDARY_URL" ] && [ -z "$BOUNDARY_DEPLOYMENT" ]; then
    echo "-- --profile tracker: boundary via ensure-running (no daemon started now) --"
    TRACKER_PORT="$("$PY" -c "import sys; sys.path.insert(0, '$AUTOHARN_ROOT'); from tools.setup_tui.probes import free_port; print(free_port())")"
    BOUNDARY_URL="http://127.0.0.1:$TRACKER_PORT"
    BOUNDARY_DEPLOYMENT="$NAME"
    TRACKER_TOML="$PROJECT_ROOT/boundary-multiplex.toml"
    if [ -f "$TRACKER_TOML" ] && [ "$FORCE" -ne 1 ]; then
        echo "   $TRACKER_TOML already exists -- left untouched (pass --force to replace it)"
    else
        cat > "$TRACKER_TOML" <<TRACKERTOML
[deployments.$NAME]
pghost = "$HOST"
pgdatabase = "$DB"
pguser = "$ROLE"
pgschema = "$SCHEMA"
pgkern = "$KERN"
TRACKERTOML
        echo "   wrote $TRACKER_TOML (port $TRACKER_PORT, section [deployments.$NAME])"
    fi
    echo "   deployment.json will carry boundary_url=$BOUNDARY_URL boundary_deployment=$NAME --"
    echo "   the first ./led/./pickup/./distance-to-clean/./asof-export call in this deployment"
    echo "   spawns the boundary automatically (ensure-running); no daemon is running yet."
fi

echo "-- deployment.json --"
"$PY" - "$DEPLOYMENT" "$DB" "$HOST" "$SCHEMA" "$KERN" "$ROLE" "$NAME" "$BOUNDARY_URL" "$BOUNDARY_DEPLOYMENT" "$OWNER_ACCESS_SPLIT" <<PYEOF
import sys
sys.path.insert(0, "$AUTOHARN_ROOT/filing")
from deployment_record import DeploymentRecord, write_deployment

path, db, host, schema, kern, role, name, boundary_url, boundary_deployment, owner_access_split = sys.argv[1:11]
write_deployment(path, DeploymentRecord(
    db=db, host=host, schema=schema, kern=kern, role=role, name=name or None,
    boundary_url=boundary_url or None, boundary_deployment=boundary_deployment or None,
    owner_access_split=(owner_access_split == "true") or None))
print(f"wrote {path}")
if not boundary_url or not boundary_deployment:
    print("   (boundary_url/boundary_deployment not supplied -- the rebased led/pickup/"
          "asof-export/distance-to-clean shims will refuse, teaching both names, until this "
          "deployment.json gains them by hand or a future --boundary-url/--boundary-deployment "
          "re-scaffold; ./legacy/ holds the direct-psql originals in the meantime)")
PYEOF

# .autoharn-world.json sentinel (design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md §2), written
# at the SAME point as deployment.json above -- the DECLARED birth marker; deployment.json +
# legacy/led remain the BEHAVIORAL evidence. `world` is written as the SAME value as
# deployment.json's own `name` field just written above (tools/setup_tui/destination.py's module
# docstring names this resolution explicitly: the two denote the same fact at birth time, and can
# only drift apart from a LATER hand-edit or a --force re-scaffold under a different --name --
# exactly the drift classify_destination's contradiction check exists to catch). `run` is
# `--new-world`'s own value, empty for a classic --schema/--kern/--role scaffold (no world/run
# concept at all). SENTINEL_SCHEMA is imported from destination.py, not re-typed (ADR-0012 P1).
echo "-- .autoharn-world.json sentinel --"
"$PY" - "$PROJECT_ROOT/.autoharn-world.json" "$NAME" "$NEW_WORLD" "$CREATED_AT" "$AUTOHARN_COMMIT_SHA" <<PYEOF
import json
import sys
sys.path.insert(0, "$AUTOHARN_ROOT")
from tools.setup_tui import destination

path, world, run, born, commit = sys.argv[1:6]
with open(path, "w", encoding="utf-8") as f:
    json.dump({
        "world": world, "run": run or None, "born": born,
        "autoharn_commit": commit or None, "schema": destination.SENTINEL_SCHEMA,
    }, f, indent=2)
    f.write("\n")
print(f"wrote {path}")
PYEOF

mkdir -p "$PROJECT_ROOT/.claude/logs" "$PROJECT_ROOT/.claude/secrets"
chmod 700 "$PROJECT_ROOT/.claude/secrets"

# .gitignore the scaffolding-owned churn paths INSIDE the subject repo this scaffold is stamping
# (tracker item `scaffold-log-churn-in-subject-repo`, ent-observatory cycle-001 NEW lesson 1: the
# invocation log landed git-tracked inside an audited subject repo -- picom/.claude/logs -- and
# churned on every session action; that cycle's audit agent handled it correctly by hand
# (excluding .claude from its diffs), but nothing stops the NEXT audit agent from missing that
# exclusion and treating the churn as a false-positive mutation signal. Fixed at birth here rather
# than left for every future audit to route around by hand.
#
# Append-if-missing (idempotent, mirrors the stamp-secret/genesis-seed never-rotate posture
# elsewhere in this script): a marker pair brackets the block so a re-scaffold (--force) or a
# second scaffold call against the same dest-dir never duplicates it.
#
# .claude/secrets/ (tracker item experience-secret-gitignore-hazard) belongs in this SAME block,
# alongside .claude/logs/: it holds THIS deployment's stamp secret
# (.claude/secrets/stamp_secret.hex, seeded above) -- a real credential, not mere churn, and
# tracking it git-side would let a future world's stamp secret leak into this repo's own
# history. Scaffold-owned, same as .claude/logs/, so it belongs in the SAME scaffold-written
# block rather than a second one grown here (ADR-0012 P1).
echo "-- .gitignore (scaffolding-owned churn + secret paths in the subject repo) --"
GITIGNORE="$PROJECT_ROOT/.gitignore"
GITIGNORE_MARK_BEGIN="# >>> autoharn scaffold-owned churn (bootstrap/new-project.sh) >>>"
GITIGNORE_MARK_END="# <<< autoharn scaffold-owned churn <<<"
# The scaffold-owned lines this block must carry INSIDE the markers. This list is checked
# content-aware, not just "does the marker exist" (tracker item experience-secret-gitignore-
# hazard follow-up): a deployment whose .gitignore carries the PRE-d211165 block (marker +
# .claude/logs/ but no .claude/secrets/, since .claude/secrets/ was added to this block by
# d211165, 2026-07-19, after some deployments already had the marker-only block) used to get
# "already carries the block -- left untouched" on --force re-scaffold, leaving the stamp secret
# un-ignored while the operator believed the fix applied. Fixed here: presence of the marker no
# longer short-circuits the check; each owned line is verified present INSIDE the block, and any
# missing one is appended inside it (before the end marker), loudly, append-only -- never a
# rewrite of anything else in the file, never a silent no-op, never a duplicate on re-run.
GITIGNORE_OWNED_LINES=".claude/logs/ .claude/secrets/"
if [ -f "$GITIGNORE" ] && grep -qF "$GITIGNORE_MARK_BEGIN" "$GITIGNORE" 2>/dev/null; then
    BLOCK_CONTENT="$(awk -v b="$GITIGNORE_MARK_BEGIN" -v e="$GITIGNORE_MARK_END" '
        $0==b {inblock=1; next}
        $0==e {inblock=0}
        inblock {print}
    ' "$GITIGNORE")"
    MISSING=""
    for _line in $GITIGNORE_OWNED_LINES; do
        # exact whole-line match ONLY -- a comment mentioning the path as prose text (e.g. "this
        # deployment's OWN stamp secret (.claude/secrets/stamp_secret.hex)") must never be
        # mistaken for the actual ignore pattern line.
        if ! printf '%s\n' "$BLOCK_CONTENT" | grep -qxF "$_line"; then
            MISSING="$MISSING $_line"
        fi
    done
    if [ -z "$MISSING" ]; then
        echo "   $GITIGNORE already carries the scaffold-owned churn block with every scaffold-owned path -- left untouched (idempotent)"
    else
        for _line in $MISSING; do
            "$PY" - "$GITIGNORE" "$GITIGNORE_MARK_END" "$_line" <<'PYEOF'
import sys
path, end_marker, line = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path) as f:
    lines = f.read().split("\n")
idx = lines.index(end_marker)
lines.insert(idx, line)
with open(path, "w") as f:
    f.write("\n".join(lines))
PYEOF
            echo "   NOTICE: $GITIGNORE's scaffold-owned churn block predates '$_line' -- appended it" >&2
            echo "   INSIDE the existing block (this .gitignore was scaffolded before that path was" >&2
            echo "   added to the scaffold-owned set; healed in place, nothing else in the file touched)." >&2
        done
    fi
else
    {
        echo ""
        echo "$GITIGNORE_MARK_BEGIN"
        echo "# Written by bootstrap/new-project.sh ($CREATED_AT), tracker item"
        echo "# scaffold-log-churn-in-subject-repo: these paths are scaffolding/hook RUNTIME OUTPUT"
        echo "# (invocation logs, change-gate state), not audited subject-repo content, and churn on"
        echo "# every session action -- tracking them git-side is a false-positive generator for any"
        echo "# diff/mutation-purity check run against this repo (ent-observatory cycle-001, NEW"
        echo "# lesson 1). Append-if-missing; safe to re-run."
        echo ".claude/logs/"
        echo "# .claude/secrets/ (tracker item experience-secret-gitignore-hazard): this"
        echo "# deployment's OWN stamp secret (.claude/secrets/stamp_secret.hex) -- a real"
        echo "# credential, never tracked git-side, so no future world's secret can leak into"
        echo "# this repo's own history."
        echo ".claude/secrets/"
        echo "$GITIGNORE_MARK_END"
    } >> "$GITIGNORE"
    echo "   appended scaffold-owned churn+secret block to $GITIGNORE (.claude/logs/, .claude/secrets/)"
fi
if (cd "$PROJECT_ROOT" && git rev-parse --is-inside-work-tree >/dev/null 2>&1); then
    :
else
    echo "   NOTE: $PROJECT_ROOT is not (yet) a git repo -- the .gitignore above was still written;"
    echo "   it is inert until this directory becomes one (e.g. \`git init\`), at which point it"
    echo "   takes effect immediately with no further action."
    echo "   Consequence while this window is open: \`led work close --review-bookkeeping"
    echo "   --witness commit:<sha>\` (the ceremony-free close for note-class work) needs a"
    echo "   commit to witness and is unusable without a repo here -- every close must go"
    echo "   --review-deferred instead, and each one accrues review-gap debt until this"
    echo "   directory is \`git init\`'d. Weigh initializing sooner against absorbing that debt."
fi

# sed substitution table, shared by every template below. `|` delimiter (paths contain `/`).
sedsubst() {
    sed \
        -e "s|__DB__|$DB|g" \
        -e "s|__HOST__|$HOST|g" \
        -e "s|__SCHEMA__|$SCHEMA|g" \
        -e "s|__KERN__|$KERN|g" \
        -e "s|__ROLE__|$ROLE|g" \
        -e "s|__PROJECT_ROOT__|$PROJECT_ROOT|g" \
        -e "s|__PROJECT_NAME__|$NAME|g" \
        -e "s|__AUTOHARN_ROOT__|$EXEC_ROOT|g" \
        -e "s|__CREATED_AT__|$CREATED_AT|g" \
        -e "s|__CREATE_CMD__|$CREATE_CMD|g" \
        -e "s|__AUTOHARN_COMMIT__|$AUTOHARN_COMMIT|g" \
        -e "s|__LINEAGE_CHAIN__|$LINEAGE_CHAIN|g" \
        -e "s|__STAMP_SECRET_STATUS__|$STAMP_SECRET_STATUS|g" \
        -e "s|__S21_STATUS__|$S21_STATUS|g" \
        -e "s|__REVIEWER_STATUS__|$REVIEWER_STATUS|g" \
        -e "s|__COMMISSIONER_STATUS__|$COMMISSIONER_STATUS|g"
}

# LAW section (tracker item portable-adr-delivery, maintainer instruction 2026-07-15): the
# portable ADR subset (design/MAINT-ADR-PORTABILITY-SPEC.md's own per-ADR treatment table --
# every ADR file under law/adr/ EXCEPT a Status:Retired-to-history tombstone already carries a
# generalize-in-place/examples-extract/already-portable/ui-scoped treatment, i.e. is written to
# be read and applied outside autoharn itself), each pointed at its file INSIDE THIS DEPLOYMENT'S
# OWN EXEC_ROOT -- REQUIRED SHAPE is no-copying: a pinned deployment (--pin submodule) already
# carries the full corpus at .autoharn/law/adr/ by construction (the submodule IS the copy), so
# this writes pointers, never a second copy of the ADR bytes. Derived from the filesystem, not a
# hand-maintained duplicate list (ADR-0012 P1: one source -- the corpus itself is the
# enumeration; a hardcoded second list would drift the moment an ADR's Status changes, exactly
# the "fossil array" ADR-0008 names). Two honest shapes, per EXEC_ROOT: PINNED (submodule, frozen
# to a commit -- pointers move only via bootstrap/upgrade-submodule.sh, deliberately) and
# UNPINNED live-exec (EXEC_ROOT is the shared checkout -- pointers move whenever that checkout
# changes, stated plainly rather than implying a frozen copy that does not exist; this is the
# deliberate shape for a deployment autoharn itself vendors, e.g. a panel project that cannot
# embed autoharn as a submodule without a cycle). Written into .claude/HOOKS.md always (the one
# doc guaranteed in every scaffold mode, pinned or not, new-world or classic) and into root
# CLAUDE.md too when --new-world writes one (auto-loaded at session start). --no-law suppresses
# this entirely -- an adopter who wants no ADR pointers says so explicitly, once.
#
# --profile tracker SKIPS THIS ENTIRE SECTION, through the CLAUDE.md-writing block further below
# (everything up to the `rm -f "$LAW_SECTION_FILE"` line) -- NO .claude/ hooks wiring, NO
# governance CLAUDE.md preamble, NO portable-ADR LAW section, in track-work.sh's own words,
# preserved verbatim: **"a standing project is not a governed world."**
if [ "$PROFILE" = "tracker" ]; then
    LAW_SECTION_FILE=""
    echo "-- .claude/ wiring / CLAUDE.md / LAW section: SKIPPED (--profile tracker) --"
    echo "   'a standing project is not a governed world' (bootstrap/track-work.sh's own words,"
    echo "   preserved) -- no change-gate, no stamp interception, no Stop-gate, no CLAUDE.md"
    echo "   governance preamble. Every row this deployment's ./led writes lands UNSTAMPED"
    echo "   (stamp_agent/stamp_session/stamp_hmac all NULL, stamp_verified=false), visible in"
    echo "   ./led --recent, not hidden -- the honest state of an unwired store. Hook wiring"
    echo "   remains a separate, deliberate act: copy new-project.sh's own .claude/ wiring stanzas"
    echo "   by hand (or re-scaffold this same directory with --new-world instead) if this"
    echo "   deployment should later become a governed world."
else
LAW_SECTION_FILE="$PROJECT_ROOT/.claude/.law-section.md.tmp"
if [ "$LAW_SECTION" -eq 1 ]; then
    echo "-- LAW section (portable ADR subset, design/MAINT-ADR-PORTABILITY-SPEC.md) --"
    if [ "$PIN" = "submodule" ]; then
        LAW_PIN_NOTE="This deployment is **PINNED** (git submodule at \`.autoharn\`, frozen to commit \`$AUTOHARN_COMMIT_SHA\`) -- the pointers below are frozen along with it. A newer autoharn's ADR corpus reaches this deployment only via a deliberate \`bootstrap/upgrade-submodule.sh\`, never silently on a \`git pull\` of autoharn itself."
    else
        LAW_PIN_NOTE="This deployment is **UNPINNED** (live-exec against the checkout at \`$EXEC_ROOT\`, no \`.autoharn\` submodule) -- the pointers below resolve into that checkout and MOVE whenever it changes; there is no frozen copy here. (Deliberate for a deployment that autoharn itself vendors -- e.g. a panel/demo project -- where pinning autoharn in as a submodule would create a submodule cycle.)"
    fi
    "$PY" - "$AUTOHARN_ROOT/law/adr" "$EXEC_ROOT" "$LAW_SECTION_FILE" "$LAW_PIN_NOTE" <<'PYEOF'
import pathlib
import sys

adr_dir, exec_root, out_path, pin_note = sys.argv[1:5]
adr_dir = pathlib.Path(adr_dir)
rows = []
for f in sorted(adr_dir.glob("[0-9][0-9][0-9][0-9]-*.md")):
    text = f.read_text(encoding="utf-8")
    lines = text.splitlines()
    # Find the first real H1 (`# ...`), not necessarily line 0 -- some ADRs open with an
    # HTML doc-attest-exempt comment block (e.g. 0012, 2026-07-15 table-sweep commission)
    # ahead of the heading; a fossil "read line 0 as the title" assumption would silently
    # mislabel every such ADR (exactly the fossil-array failure mode ADR-0008 names).
    title = f.name
    for ln in lines:
        s = ln.strip()
        if s.startswith("# "):
            title = s[2:].strip()
            break
    # Same reasoning for the Status line: search the whole file, not a fixed line-count
    # window, since a leading comment block can push it past any fixed cutoff.
    status_line = ""
    for ln in lines:
        if ln.strip().startswith("- **Status:**"):
            status_line = ln
            break
    if "Retired-to-history" in status_line:
        continue  # a tombstone carries no live rule content -- excluded from the served set
    rows.append((f.name, title))

with open(out_path, "w", encoding="utf-8") as out:
    out.write("## LAW (portable ADR subset, vendored via this scaffold)\n\n")
    out.write(
        "Written by `bootstrap/new-project.sh` (tracker item `portable-adr-delivery`, maintainer "
        "instruction 2026-07-15). The subset below is the CURRENTLY-SERVED, "
        "cross-project-portable slice of autoharn's ADR corpus -- "
        "`design/MAINT-ADR-PORTABILITY-SPEC.md`'s own per-ADR treatment table: every entry here "
        "already carries a `generalize-in-place`/`examples-extract`/`already-portable`/"
        "`ui-scoped-generalize-or-unserve` treatment, i.e. it is written to be read and applied "
        "outside autoharn itself (ADR-0001 is excluded -- its own Status retired it to a history "
        "tombstone; it carries no live rule content to extrapolate from). " + pin_note + "\n\n"
        "**Reading posture:** read each ADR IN FULL before any work requiring it -- diagnosing, "
        "designing, or touching code shaped by its rule -- and read it for its SPIRIT: these are "
        "principles to extrapolate from and interpret judiciously, not rules to satisfy by letter "
        "alone. Where letter and spirit appear to diverge, the spirit governs, and the divergence "
        "is surfaced, not silently resolved.\n\n"
    )
    for name, title in rows:
        out.write(f"- **{title}** -- `{exec_root}/law/adr/{name}`\n")
    out.write("\n")
PYEOF
    N=$(grep -c '^- \*\*' "$LAW_SECTION_FILE" 2>/dev/null || echo 0)
    echo "   generated LAW section ($N portable ADRs enumerated)"
else
    : > "$LAW_SECTION_FILE"
    echo "-- LAW section: --no-law given -- deployment scaffolded WITHOUT the portable-ADR LAW section --"
fi

echo "-- .claude/ wiring --"
sedsubst < "$TEMPLATES/settings.json.tmpl" > "$PROJECT_ROOT/.claude/settings.json"
# governed_files.json: --governed <comma-separated-patterns> lets THIS deployment declare its
# real work surface at birth (tracker item `scaffold-governed-set-language-default`, ent testbed
# finding 4, 2026-07-13) instead of inheriting the historical *.py-only default silently. Absent
# --governed, the old default template is copied unchanged (byte-identical scaffold behavior for
# every existing caller) -- but the gap it can leave is no longer silent: the loud notice below
# names the default and the exact one-line widening act, refusal-grade rather than a footnote.
if [ -n "$GOVERNED" ]; then
    "$PY" - "$PROJECT_ROOT/.claude/governed_files.json" "$GOVERNED" <<'PYEOF'
import json
import sys

path, patterns_csv = sys.argv[1:3]
patterns = [p.strip() for p in patterns_csv.split(",") if p.strip()]
with open(path, "w") as f:
    json.dump({"patterns": patterns}, f, indent=2)
    f.write("\n")
PYEOF
    echo "wrote .claude/governed_files.json (custom, --governed '$GOVERNED')"
else
    cp "$TEMPLATES/governed_files.json" "$PROJECT_ROOT/.claude/governed_files.json"
    echo "wrote .claude/governed_files.json (DEFAULT: *.py only)"
    echo ""
    echo "!! GOVERNED-SET DEFAULT NOTICE (no --governed given) !!"
    echo "This deployment's change gate governs *.py files ONLY -- the scaffold's historical"
    echo "default, not a judgment about what THIS project's real work surface is. If this"
    echo "deployment's work is not Python (SQL, shell, Terraform, config, docs, anything else),"
    echo "those files are UNGOVERNED right now: Claude Code can edit them with NO preceding ledger"
    echo "entry, and nothing will warn you again after this line."
    echo "Widen it with exactly one edit -- $PROJECT_ROOT/.claude/governed_files.json:"
    echo "  { \"patterns\": [\"*.py\", \"*.sql\", \"*.tf\"] }"
    echo "(fnmatch semantics, no restart needed: $PROJECT_ROOT/.claude/GOVERNED_FILES.md)"
    echo ""
fi
# COHERENCE PARTNER: .claude/GOVERNED_FILES.md and .claude/APPARATUS.md below are AUTOHARN's own
# prose, named in gates/doc_attestation_presence.py's DEPLOYMENT_SCAFFOLD_OWNED_MD (tracker item
# `abc-loop-offering`) so a scaffolded deployment's ./attest-doc/./distance-to-clean never asks
# an adopter to re-attest autoharn's own docs. Add any NEW scaffold-written .md file to BOTH
# sides -- an out-of-frame audit already caught one addition (attestations/README.md) missing
# from that set on day one; this comment exists so the next one is not missed the same way.
cp "$TEMPLATES/GOVERNED_FILES.md" "$PROJECT_ROOT/.claude/GOVERNED_FILES.md"
cp "$TEMPLATES/apparatus.json" "$PROJECT_ROOT/.claude/apparatus.json"
cp "$TEMPLATES/APPARATUS.md" "$PROJECT_ROOT/.claude/APPARATUS.md"
sedsubst < "$TEMPLATES/HOOKS.md.tmpl" > "$PROJECT_ROOT/.claude/HOOKS.md"
# LAW section insertion: the __LAW_SECTION__ placeholder line in HOOKS.md.tmpl is replaced with
# LAW_SECTION_FILE's content (`r` reads the file in raw, so its own __AUTOHARN_ROOT__-style
# tokens were already resolved when it was generated above -- no double-substitution needed) and
# the placeholder line itself is dropped. LAW_SECTION_FILE is empty (`--no-law`) or a real
# section (default) -- either way this is a no-op-safe insert (an empty `r` inserts nothing).
sed -i -e "/^__LAW_SECTION__\$/r $LAW_SECTION_FILE" -e "/^__LAW_SECTION__\$/d" "$PROJECT_ROOT/.claude/HOOKS.md"
echo "wrote .claude/settings.json, governed_files.json, GOVERNED_FILES.md, apparatus.json, APPARATUS.md, HOOKS.md"

# Vendored skills (tracker item skill-vendoring-hack-rationalization, maintainer commission
# 2026-07-15): install every skill under bootstrap/templates/claude-skills/ into this
# deployment's own .claude/skills/, verbatim -- a plain recursive copy, never a template
# substitution (the skill body is not autoharn's to rewrite; see each skill's own PROVENANCE.md
# for the precedence fact: Claude Code resolves same-named skills enterprise > personal >
# project, so a user's personal copy of the same name silently shadows this one -- duplication
# is idempotent by that platform rule, not a drift hazard needing a warning mechanism here).
# deploy-feature-manifest (ledger row 1274/1322): VENDOR_SKILLS opt-out (--no-vendored-skills /
# features.json's "vendored_skills": false) -- default stays ON (VENDOR_SKILLS=1), so an
# operator who never touches this decision gets today's exact unconditional-copy behavior.
if [ "$VENDOR_SKILLS" -eq 1 ] && [ -d "$TEMPLATES/claude-skills" ]; then
    mkdir -p "$PROJECT_ROOT/.claude/skills"
    for _skill_dir in "$TEMPLATES/claude-skills"/*/; do
        [ -d "$_skill_dir" ] || continue
        _skill_name="$(basename "$_skill_dir")"
        cp -r "$_skill_dir" "$PROJECT_ROOT/.claude/skills/$_skill_name"
        echo "wrote .claude/skills/$_skill_name (vendored skill, verbatim)"
    done
elif [ "$VENDOR_SKILLS" -eq 0 ]; then
    echo "-- vendored skills: DECLINED (--no-vendored-skills / features.json vendored_skills=false) -- .claude/skills/ NOT written --"
fi

# deploy-feature-manifest (ledger row 1274/1322): panel extension -- a LOCAL (never network)
# `git clone` of THIS checkout's own tools/autoharn-panel submodule into <dest>/panel. Nested at
# <dest>/panel specifically because tools/autoharn-panel/README.md's own config.py discovery
# order looks for `<repo_root>/../deployment.json` when nested under an autoharn-adjacent
# checkout -- <dest>/panel/../deployment.json is exactly <dest>/deployment.json, this world's own
# record, so the clone needs zero extra configuration to find its ledger. REFUSES loudly (never a
# silent skip) if the submodule is not populated in THIS autoharn checkout (`git submodule update
# --init --recursive` is the teaching text) -- an unpopulated source is a real blocker, not
# nothing to report.
if [ "$PANEL_EXTENSION" -eq 1 ]; then
    _PANEL_SRC="$AUTOHARN_ROOT/tools/autoharn-panel"
    if [ ! -f "$_PANEL_SRC/README.md" ]; then
        echo "new-project.sh: REFUSED -- --panel-extension asked to wire in tools/autoharn-panel," >&2
        echo "                but $_PANEL_SRC is not populated in this autoharn checkout (an" >&2
        echo "                uninitialized submodule). Run 'git submodule update --init" >&2
        echo "                --recursive' in $AUTOHARN_ROOT, then re-run this scaffold." >&2
        exit 1
    fi
    # --no-hardlinks: a plain `--local` clone tries to HARD-LINK object files by default, which
    # fails outright ("Invalid cross-device link") whenever <dest-dir> is on a different
    # filesystem/mount than this autoharn checkout (witnessed live: a /tmp scratch dest against a
    # checkout on a different mount) -- forcing a real copy instead is still zero-network (the
    # source is a local path, never a remote URL) and works across any filesystem boundary.
    if git clone --quiet --local --no-hardlinks -- "$_PANEL_SRC" "$PROJECT_ROOT/panel"; then
        echo "wrote panel/ (ledger-panel SPA, local clone of tools/autoharn-panel -- see panel/README.md; start with: cd panel && python3 -m pip install --user -r backend/requirements.txt, then backend/app.py finds this world's own deployment.json automatically)"
    else
        echo "new-project.sh: REFUSED -- 'git clone --local $_PANEL_SRC $PROJECT_ROOT/panel' failed." >&2
        exit 1
    fi
fi

# deploy-feature-manifest (ledger row 1274/1322): makespan-scheduler RESOURCES tier --
# DECLARATIVE-ONLY in this build (named blocker, not a silent stub): the carried-forward
# deployment-makespan-offering instance is a sibling checkout + editable venv install
# (design/workflows/panel-msched-resource-provisioning.toml's own witnessed specimen), but an
# operator-designated venv path is not knowable at scaffold time, and this scaffold makes no
# network/pip calls of its own -- so this writes a ready-to-paste `resource:` declaration
# template (design/ORCH-SPEC-RESOURCE-REGISTRY.md §2's six-field convention) plus the honest
# UNWITNESSED note, never a fabricated "installed" claim.
if [ "$MAKESPAN_TIER" != "off" ]; then
    mkdir -p "$PROJECT_ROOT/resources"
    cat > "$PROJECT_ROOT/resources/makespan-scheduler.resource-declaration.txt" <<MSCHED
# makespan-scheduler RESOURCES declaration -- prepared by new-project.sh (deploy-feature-manifest,
# ledger row 1274/1322), NOT yet applied. UNWITNESSED capability, named blocker: the sibling
# checkout + editable venv install this declaration presumes is NOT automated by this scaffold --
# the operator's own venv path is not known at scaffold time, and this scaffold makes no
# network/pip calls. To actually provision it (design/workflows/panel-msched-resource-provisioning.toml's
# own witnessed specimen):
#   1. sibling checkout: git clone <makespan-scheduler remote or local path> ../makespan-scheduler
#   2. editable install into your own operator-designated venv:
#        <your-venv>/bin/pip install -e ../makespan-scheduler
#   3. paste the line below (fill REACH with your venv's actual import path) as a ledger decision:
#        ./led decision "resource: NAME=makespan-scheduler; CLASS=solver; REACH=<your venv>/bin/python -c 'import makespan_scheduler'; WHAT-IT-PROVES=constraint-based precedence scheduling for multi-item commissions (s30 blocks-close edges as the precedence DAG); GUIDANCE=reach for this when a commission spans 3+ dependent/precedence-constrained/resource-conflicting work items; TIER=$MAKESPAN_TIER: <name the task shape here>"
MSCHED
    echo "wrote resources/makespan-scheduler.resource-declaration.txt (DECLARATIVE-ONLY -- tier=$MAKESPAN_TIER; sibling-checkout+install NOT automated, see file for the named blocker)"
fi

if [ -n "$NEW_WORLD" ]; then
    # CLAUDE.md's preamble states "a reviewer principal exists" as fact -- only true once the
    # reviewer-registration step above has actually run, so this file is written ONLY for
    # --new-world mode (classic mode has no principal table yet at all -- see REVIEWER_STATUS
    # above). This is the second half of the same BACKLOG ruling the reviewer registration
    # closes: "starting a run becomes a verb" names BOTH the hand-registered reviewer principal
    # AND the hand-pasted six-point governance prompt as the ceremony to fold into the scaffold.
    # Lands at the WORLD ROOT (not .claude/) and named exactly `CLAUDE.md` -- ratifier's
    # acceptance bar (2026-07-09): at most one scaffold command, one `cd`, one `claude`, and NO
    # paste step. A file named anything else, or living anywhere else, is not auto-loaded by
    # Claude Code at session start and would put the paste step right back.
    # COHERENCE PARTNER: this CLAUDE.md is in gates/doc_attestation_presence.py's
    # DEPLOYMENT_SCAFFOLD_OWNED_MD (see the .claude/ wiring block above's own coherence-partner
    # comment) -- it is autoharn's own prose, not an adopter's to re-attest.
    sedsubst < "$TEMPLATES/CLAUDE.md.tmpl" > "$PROJECT_ROOT/CLAUDE.md"
    sed -i -e "/^__LAW_SECTION__\$/r $LAW_SECTION_FILE" -e "/^__LAW_SECTION__\$/d" "$PROJECT_ROOT/CLAUDE.md"
    echo "wrote CLAUDE.md (governance preamble, auto-loaded at session start)"
fi
fi
rm -f "$LAW_SECTION_FILE" 2>/dev/null || true

# the ten verbs (led, judge, pickup, audit, distance-to-clean, verify-commission, verify-chain,
# asof-export, attest-doc, doctor): thin shims,
# not frozen sed-substituted copies (BACKLOG maintainer ruling 2026-07-11, "runs are strictly
# linear" disposition 6, "live verbs"; audit and distance-to-clean joined the same way later,
# each a new template file rather than an edit to an existing live one -- see their own
# commissions; verify-commission (design/MAINT-GPG-TRUST-LAYER.md Rung 2) and asof-export
# (ledger item asof-export-inspection-copy, vestigial_documentation/design/FABLE-21CFR11-STANDING-ASSESSMENT.md §11.10(b))
# each follow the SAME distance-to-clean precedent -- a brand-new template file carries none of
# led.tmpl's freeze risk, so it is safe to add regardless of any live wired session elsewhere.
# doctor (ledger rows 1147/1148, virgin-experience round) is the newest of these, same precedent.
# Baking was the asymmetry: hooks already execute live from this autoharn checkout per invocation
# (settings.json's __AUTOHARN_ROOT__ above), but led/judge/pickup were frozen copies -- a
# just-fixed led defect stayed live in every already-scaffolded world forever, reachable only by
# the NEXT scaffold. A shim closes that: it `exec`s bootstrap/templates/<verb>.tmpl straight out
# of THIS checkout, every invocation, so a template fix here reaches every existing world
# instantly. World-specific facts (db/host/schema/kern/role/name) are no longer sed-substituted
# either -- the .tmpl itself now resolves them LIVE from deployment.json, found next to the shim
# (the shim computes its own directory and passes it through via PICKUP_DEPLOYMENT -- the same
# env var `pickup`'s own live-resolution already used, extended to all three rather than growing
# three near-identical mechanisms, ADR-0012 P1). deployment.json itself stays scaffold-written
# per-world config (unchanged) -- only the VERBS stopped being copies.
# keys/ -- this deployment's OWN GPG keyring (SIGNED commissions, design/MAINT-GPG-TRUST-LAYER.md §3),
# deliberately separate from autoharn's law/keys/ (scoped exclusively to autoharn's own
# ratified/* tags). Mirrors bootstrap/track-work.sh's identical block; applied at the merge
# window per the key-residence refactor's documented frozen-remainder diff (BACKLOG 2026-07-12).
# COHERENCE PARTNER: keys/README.md and attestations/README.md below are BOTH in gates/
# doc_attestation_presence.py's DEPLOYMENT_SCAFFOLD_OWNED_MD (tracker item `abc-loop-offering`)
# -- they are autoharn's own templated prose, not an adopter's to re-attest. If a future template
# adds another scaffold-written .md file, add it to that set too (that module's own docstring
# names this exact scaffold as the coherence partner in the other direction).
echo "-- keys/ (this deployment's OWN GPG keyring; never autoharn's law/keys/) --"
mkdir -p "$PROJECT_ROOT/keys"
sedsubst < "$TEMPLATES/keys-README.md.tmpl" > "$PROJECT_ROOT/keys/README.md"
echo "wrote keys/README.md (AWAITING-KEY stub; commit THIS deployment's own signing key here)"

# attestations/ -- this deployment's OWN ADR-0017 A:B:C fresh-context attestation ledger
# (tracker item `abc-loop-offering`; design/ORCH-SPEC-ABC-OFFERING.md §3), deliberately separate
# from autoharn's own ledger of the same name, exactly the keys/ split above. The ledger FILE
# itself is created empty ONLY if it does not already exist -- the same idempotent,
# never-clobber-real-data posture this script's own header comment documents for the stamp
# secret ("skipped if a secret already exists, never silently rotated"): a --force re-scaffold
# must never truncate a ledger that already carries real attestation history.
echo "-- attestations/ (this deployment's OWN ADR-0017 A:B:C attestation ledger; never autoharn's) --"
mkdir -p "$PROJECT_ROOT/attestations"
sedsubst < "$TEMPLATES/attestations-README.md.tmpl" > "$PROJECT_ROOT/attestations/README.md"
if [ -f "$PROJECT_ROOT/attestations/doc-legibility-attestations.jsonl" ]; then
    echo "attestations/doc-legibility-attestations.jsonl already exists -- left untouched (never clobbered)"
else
    : > "$PROJECT_ROOT/attestations/doc-legibility-attestations.jsonl"
    echo "wrote attestations/doc-legibility-attestations.jsonl (empty; the honest starting state)"
fi
echo "wrote attestations/README.md"

# roles/ -- design/FABLE-ROLE-CHARTERS-AND-BRIEFS-SPEC.md deliverable 4 (commission ledger row
# 1663): an EMPTY scaffold + README stating the register-before-binding rule -- ADDITIVE ONLY,
# NO LINEAGE_CHAIN CONTACT (this block writes a directory and one templated README, nothing
# else; no kernel act, no ledger row -- a charter binds only when a LATER, explicit
# `tools/role_charter.py register` call writes the registration row, never at scaffold time).
# COHERENCE PARTNER: roles/README.md is in gates/doc_attestation_presence.py's
# DEPLOYMENT_SCAFFOLD_OWNED_MD (same set keys/README.md and attestations/README.md are already
# in, immediately above) -- it is autoharn's own templated prose, not an adopter's to re-attest.
echo "-- roles/ (this deployment's OWN role-charter directory; empty at birth, register-before-binding) --"
mkdir -p "$PROJECT_ROOT/roles"
sedsubst < "$TEMPLATES/roles-README.md.tmpl" > "$PROJECT_ROOT/roles/README.md"
echo "wrote roles/README.md"

# §6 AMENDMENT (2026-07-26, rows 1357/1365/1366/1367 -- design/FABLE-AUTOHARN-UMBRELLA-CLI-
# SPEC.md's scaffold clause executes) + CLASS FIX (2026-07-28, autoharn3 row 101, "the world-
# dispatcher generation ... derives its verb table from the bootstrap/templates/*.tmpl directory
# glob"): a world gets ONE dispatcher, `./autoharn`, routing `autoharn <verb> [args...]` to the
# matching `bootstrap/templates/<verb>.tmpl` + PICKUP_DEPLOYMENT env -- the roster is no longer a
# hand-maintained list (SHIM_VERBS_ALL/_verb_desc, both retired from this call site) but is
# derived, every run, from the templates directory itself by _write_world_dispatcher() (defined
# near this script's own top, alongside its full closure statement and the NON_VERB_TEMPLATES
# exclusion list) -- the SAME function --refresh-dispatcher calls below. Unknown verb: a teaching
# refusal listing the roster (never a bare shell "not found"). `--help`/no-args: the roster
# generated from the SAME table the dispatch/refusal paths read, never re-derived, writes
# nothing and touches no boundary. Existing pre-migration worlds keep their ten shim files
# untouched (runs-are-linear at birth; --refresh-dispatcher is the explicit, opt-in exception
# for a world's OWN wiring file, ledger row 101 item 4 -- never automatic, never silent).
echo "-- ./autoharn (this world's ONE dispatcher, no per-verb shims -- design/FABLE-AUTOHARN-UMBRELLA-CLI-SPEC.md §6 amendment, verb roster CLASS-FIXED autoharn3 row 101): routes to autoharn's live templates --"
_write_world_dispatcher

# deploy-feature-manifest (ledger row 1274/1322): principal_set, applied through the just-written
# `led` shim (--new-world mode only -- refused earlier, before any act, for classic mode). A
# `register-principal` write needs the boundary service REACHABLE (`led`'s served-shim rebase,
# design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md) -- for `--new-world`, unlike
# `--profile tracker`, this scaffold does NOT auto-configure ensure-running (that is the TUI's
# own separate "boundary" screen/step, run AFTER birth, or an explicit --boundary-url/
# --boundary-deployment pair on THIS invocation). So this writes a PREPARED script either way
# (mirrors steps_substrate.py's own pg_hba PREPARED-block precedent: an act this scaffold cannot
# safely perform blind is handed to the operator as an exact, ready-to-run command, never
# silently skipped) and, ONLY IF the boundary is ALREADY resolvable at this exact invocation
# (BOUNDARY_URL/BOUNDARY_DEPLOYMENT non-empty), ALSO runs it now, live, and reports the real
# witnessed result -- never a fabricated "registered" claim when the boundary was not up.
if [ -n "$F_PRINCIPAL_SET_FILE" ] && [ -s "$F_PRINCIPAL_SET_FILE" ]; then
    {
        echo "#!/bin/sh"
        echo "# principal_set, prepared by new-project.sh (deploy-feature-manifest, ledger row 1274/1322)."
        echo "# Run this once ./autoharn led is REACHABLE (boundary configured -- the TUI's own"
        echo "# 'Boundary' step, or ensure-running already spawned it on a prior ./autoharn led call)."
        echo 'HERE="$(cd "$(dirname "$0")" && pwd)"'
        while IFS="$(printf '\t')" read -r _pn _pc _pp; do
            [ -n "$_pn" ] || continue
            printf '"$HERE"/autoharn led register-principal %s %s --purpose %s\n' \
                "$(printf '%s' "$_pn" | sed "s/'/'\\\\''/g;s/^/'/;s/\$/'/")" \
                "$(printf '%s' "$_pc" | sed "s/'/'\\\\''/g;s/^/'/;s/\$/'/")" \
                "$(printf '%s' "$_pp" | sed "s/'/'\\\\''/g;s/^/'/;s/\$/'/")"
        done < "$F_PRINCIPAL_SET_FILE"
    } > "$PROJECT_ROOT/register-principal-set.sh"
    chmod +x "$PROJECT_ROOT/register-principal-set.sh"
    echo "wrote register-principal-set.sh (PREPARED -- one 'autoharn led register-principal' line per principal_set row)"
    if [ -n "$BOUNDARY_URL" ] && [ -n "$BOUNDARY_DEPLOYMENT" ]; then
        echo "-- boundary already resolvable this run (BOUNDARY_URL/BOUNDARY_DEPLOYMENT set) -- applying principal_set live --"
        if "$PROJECT_ROOT/register-principal-set.sh"; then
            echo "principal_set: WITNESSED (applied live -- see the led output above)"
        else
            echo "principal_set: REFUSED -- register-principal-set.sh exited nonzero; nothing further attempted. Re-run $PROJECT_ROOT/register-principal-set.sh by hand once the cause is fixed." >&2
            exit 1
        fi
    else
        echo "principal_set: PREPARED, NOT YET APPLIED -- boundary not resolvable at this invocation (typical for --new-world; the TUI's own Boundary step, or an explicit --boundary-url/--boundary-deployment pair, configures it). Run $PROJECT_ROOT/register-principal-set.sh once ./autoharn led is reachable."
    fi
fi

# ./legacy/ (design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md §5, ratified ledger row 1631):
# the direct-psql originals of the rebased verbs, whole and executable, demoted by placement
# never deleted -- "operator recovery when the boundary is down" (spec §5's own words). judge/
# audit/attest-doc/verify-commission/verify-chain do NOT rebase (spec §5's own closed
# enumeration: judge "drives clingo + differential against the world, not a ledger client in the
# boundary's sense"; audit is the SAME class -- engine/contemp_audit.py + engine/
# contemp_differential.py, clingo-driven -- so it stays in the single, unforked family above,
# never duplicated here) -- so this loop covers ONLY led/pickup/asof-export/distance-to-clean,
# each pointed at its OWN `legacy-<verb>.tmpl` sibling (bootstrap/templates/, the pre-rebase
# content, byte-identical save the one-line recovery header each carries at its own top).
#
# `led` IS THE ONE EXCEPTION (design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md's retirement act,
# ledger row 1149/1150): `legacy-led.tmpl` is DELETED from this repository outright -- the
# boundary is mandatory at every birth now (no decline path left that needs a working direct-
# psql `led`), and `led principal *` closed the one family that was ever missing from the served
# path. `legacy/led` still gets a FILE here (destination.py's own AUTOHARN_COMPLETE classifier
# guarantee depends on its existence), but it is a one-line teaching refusal, never a working
# CLI -- pickup/asof-export/distance-to-clean are UNCHANGED, real shims, same as always.
echo "-- ./legacy/ (pickup/asof-export/distance-to-clean's direct-psql originals; led is a teaching-refusal stub, retired) --"
mkdir -p "$PROJECT_ROOT/legacy"
cat > "$PROJECT_ROOT/legacy/led" <<'STUB'
#!/bin/sh
echo "legacy/led: RETIRED 2026-07 (design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md) -- every surface" >&2
echo "  serves through ./autoharn led now; the boundary is mandatory at every birth, and led" >&2
echo "  principal * (grant-competence/relate and their 11 siblings) closed the one family the" >&2
echo "  served path was ever missing. Use ./autoharn led instead." >&2
exit 1
STUB
chmod +x "$PROJECT_ROOT/legacy/led"
echo "wrote legacy/led (RETIRED teaching-refusal stub, design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md)"
for verb in pickup asof-export distance-to-clean; do
    cat > "$PROJECT_ROOT/legacy/$verb" <<SHIM
#!/bin/sh
HERE="\$(cd "\$(dirname "\$0")" && cd .. && pwd)"
exec env PICKUP_DEPLOYMENT="\$HERE/deployment.json" $EXEC_ROOT/bootstrap/templates/legacy-$verb.tmpl "\$@"
SHIM
    chmod +x "$PROJECT_ROOT/legacy/$verb"
    echo "wrote legacy/$verb (shim -> $EXEC_ROOT/bootstrap/templates/legacy-$verb.tmpl)"
done

# orchlog wrapper (deployment-orchlog-surfacing item, half (b) -- half (a), migrate printing the
# span, belongs to ./migrate and is untouched here). A DIFFERENT shape from the eight shims just
# above on purpose: orchlog is not a bootstrap/templates/*.tmpl instance-config resolver -- it is
# a repo-root verb (like led/judge/pickup themselves) that reads ITS OWN repo's git history
# (orchlog.d/*.md notes, keyed off each note's adding commit -- see orchlog's own module
# docstring), never this deployment's ledger, so it needs no PICKUP_DEPLOYMENT and no
# deployment.json at all. This wrapper only points it at the harness whose changelog a restarting
# deployment session wants to read: `exec harness orchlog --repo <harness-root>`, literally, with
# EXEC_ROOT (the live-exec harness tree every other verb/hook here already resolves against) as
# <harness-root> -- so a fresh session in THIS deployment can self-serve "what changed in autoharn
# since I was last here" without hand-relayed memo rows.
echo "-- orchlog wrapper (self-serve harness changelog, beside led/judge/pickup): exec's autoharn's own orchlog verb against $EXEC_ROOT, no deployment.json involved --"
cat > "$PROJECT_ROOT/orchlog" <<SHIM
#!/bin/sh
exec $EXEC_ROOT/orchlog --repo $EXEC_ROOT "\$@"
SHIM
chmod +x "$PROJECT_ROOT/orchlog"
echo "wrote orchlog (wrapper -> $EXEC_ROOT/orchlog --repo $EXEC_ROOT)"

if [ "$PIN" = "submodule" ]; then
    echo "-- --pin submodule: committing the pin + the verbs/hooks it points at --"
    (cd "$PROJECT_ROOT" && git add \
        autoharn orchlog \
        .claude/settings.json .gitignore 2>/dev/null || true)
    if (cd "$PROJECT_ROOT" && git diff --cached --quiet) 2>/dev/null; then
        echo "   nothing new to commit (already committed by an earlier --force re-run)"
    else
        (cd "$PROJECT_ROOT" && git commit --quiet -m "pin autoharn@$AUTOHARN_COMMIT_SHA via .autoharn submodule (bootstrap/new-project.sh --pin submodule)")
        echo "   committed: $(cd "$PROJECT_ROOT" && git log -1 --oneline)"
    fi
fi

# deploy-feature-manifest (ledger row 1274/1322): the canonical, hand-editable durable record --
# written EVERY run (regardless of whether --features-file/any discrete feature flag was given),
# reflecting the RESOLVED decisions this run actually applied. Absent every new flag, this is the
# ONE new file a scaffold now writes vs. before this build (RED-FIRST's own "manifest absent =
# today's scaffold byte-comparable, or differences enumerated" -- the enumerated difference is
# exactly this one additive file, its own values matching today's unchanged default behavior:
# portable ADRs on, skills vendored, no panel, no makespan declaration, no extra principals).
"$PY" - "$PROJECT_ROOT/features.json" "$LAW_SECTION" "$VENDOR_SKILLS" "$PANEL_EXTENSION" "$MAKESPAN_TIER" "${F_PRINCIPAL_SET_FILE:-}" <<'PYEOF'
import json, sys

out_path, law_section, vendor_skills, panel_extension, tier, rows_path = sys.argv[1:7]
principal_set = []
if rows_path:
    try:
        with open(rows_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line:
                    continue
                name, cls, purpose = line.split("\t", 2)
                principal_set.append({"name": name, "agent_class": cls, "purpose": purpose})
    except OSError:
        pass
manifest = {
    "features_format": 1,
    "portable_adrs": law_section == "1",
    "vendored_skills": vendor_skills == "1",
    "panel_extension": panel_extension == "1",
    "makespan_scheduler_tier": tier,
    "principal_set": principal_set,
}
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, sort_keys=True)
    f.write("\n")
PYEOF
echo "wrote features.json (the durable, hand-editable feature-manifest record of this run's resolved decisions)"
[ -n "$F_PRINCIPAL_SET_FILE" ] && rm -f "$F_PRINCIPAL_SET_FILE" 2>/dev/null || true

echo "== done =="
echo "Next steps:"
if [ -n "$NEW_WORLD" ]; then
    # Ratifier's acceptance bar (2026-07-09): starting a run is at most one scaffold command, one
    # `cd`, one `claude`, and NO paste step. This world already got there above (kernel + s20 +
    # s21 applied, stamp secret provisioned, 'reviewer' principal registered, CLAUDE.md written)
    # -- the footer below is the whole remaining ceremony, not an abbreviation of a longer one.
    echo "  $CREATE_CMD"
    echo "  cd $PROJECT_ROOT"
    echo "  claude   # then type your task as your first message -- CLAUDE.md auto-loads the"
    echo "           # governance preamble (author + reviewer + commissioner principals, all"
    echo "           # already registered above); nothing to paste."
    echo ""
    echo "(./autoharn led/judge/pickup/audit/distance-to-clean/verify-commission/verify-chain/"
    echo " attest-doc/asof-export/doctor, plus ./orchlog, are ready to use from inside that"
    echo " session -- run './autoharn --help' for the full generated roster; read"
    echo " $PROJECT_ROOT/.claude/HOOKS.md and replace its UNWITNESSED marks as you exercise each"
    echo " command. (./autoharn doctor answers \"is this world set up right?\" in one witnessed call --"
    echo " read it first if anything below looks off. ./orchlog lists the harness changelog --"
    echo " notes on things a restarting session would want to know about autoharn itself, e.g."
    echo " \`./orchlog\` or \`./orchlog since <sha>\`.)"
    echo ""
    echo "----- BEGIN MAINTAINER SIGNING BLOCK -----"
    echo "To SIGN this run's commission yourself (FULL mode -- kernel/lineage/s25-commission-"
    echo "kind.sql; the ask carries the commissioner's own guarantee, not a vicarious one), type"
    echo "this in YOUR OWN terminal, inside $PROJECT_ROOT (not inside the agent's session):"
    echo "  LED_ACTOR=commissioner ./autoharn led commission \"<the ask verbatim>\""
    echo "The record then shows a commissioner-actor row, and -- typed from a bare shell with no"
    echo "claude session running -- an unstamped-but-attributed row (\`led --recent\` shows"
    echo "stamp_agent as NULL, actor as 'commissioner'): stamp state + actor together are what"
    echo "make FULL mode mechanically distinguishable from LAZY mode (the implementer's own"
    echo "vicarious transcription, CLAUDE.md preamble point 10), never prose claims alone."
    echo ""
    echo "SIGNED mode (design/MAINT-GPG-TRUST-LAYER.md Rung 2 -- FULL, plus a detached GPG signature"
    echo "over the ask): do THIS INSTEAD of the plain FULL-mode line above, not after it --"
    echo "reading the ask from a file ONCE and reusing that same value for both the ledger write"
    echo "and the signature is what keeps the two byte-for-byte identical (typing the ask inline"
    echo "for FULL mode, then separately re-reading a file for the signature, is itself a"
    echo "byte-fidelity hazard -- see verify-commission.tmpl's own module docstring). With the ask"
    echo "in a file (say ~/aa), from YOUR OWN terminal, inside $PROJECT_ROOT:"
    echo "  STATEMENT=\"\$(cat ~/aa)\"                          # exactly what the ledger stores"
    echo "  LED_ACTOR=commissioner ./autoharn led commission \"\$STATEMENT\""
    echo "  printf '%s' \"\$STATEMENT\" | gpg --detach-sign --armor -o ~/aa.asc -"
    echo "  mkdir -p $PROJECT_ROOT/.claude"
    echo "  cp ~/aa.asc $PROJECT_ROOT/.claude/commission-<id>.asc   # <id> from the commission's own output"
    echo "  cd $PROJECT_ROOT && ./autoharn verify-commission --id <id>"
    echo "Signing 'printf %s \"\$STATEMENT\"' (never the raw file \"~/aa\") is deliberate: it signs"
    echo "byte-for-byte what \"\$(cat ~/aa)\" actually inserted into the ledger (command"
    echo "substitution strips trailing newlines; a raw-file signature would not, and would verify"
    echo "as FORGED-OR-CORRUPT despite being perfectly honest -- see verify-commission.tmpl's own"
    echo "module docstring for the full account of this hazard and its fix). Expect VERIFIED once"
    echo "a real key is committed at THIS deployment's keys/ directory (never autoharn's"
    echo "law/keys/ -- that one is scoped to autoharn's own law); until then every signature refuses"
    echo "as NO-COMMITTED-KEY, exit 3 (there is nothing to check it against yet -- distinct from"
    echo "FORGED-OR-CORRUPT, per user-guide/USER-GPG-TRUST-LAYER-FAQ.md) -- exercise the ceremony with a"
    echo "throwaway test key first if you want to see VERIFIED before the real key exists."
    echo ""
    echo "The SIGNED HEAD (design/MAINT-GPG-TRUST-LAYER.md Rung 3 -- the run-close ritual, one line):"
    echo "at the end of a session, from YOUR OWN terminal, inside $PROJECT_ROOT:"
    echo "  cd $PROJECT_ROOT"
    echo "  ./autoharn verify-chain --head > /tmp/head.json    # refuses (exit 1, empty stdout) if the"
    echo "                                             # chain is not INTACT -- verifies first"
    echo "  gpg --detach-sign --armor /tmp/head.json"
    echo "  mkdir -p $PROJECT_ROOT/.claude"
    echo "  cp /tmp/head.json /tmp/head.json.asc $PROJECT_ROOT/.claude/"
    echo "  git -C $PROJECT_ROOT add .claude/head.json .claude/head.json.asc"
    echo "Both files bank as committed evidence. From that moment, ANY retroactive alteration of"
    echo "this world's ledger -- including by the database superuser -- breaks the chain against a"
    echo "head your key vouches for: \"append-only by trigger\" becomes \"append-only or provably"
    echo "broken\" (design/MAINT-GPG-TRUST-LAYER.md §4). Full walkthrough, including WHY --head verifies"
    echo "before it will print anything: user-guide/USER-GPG-TRUST-LAYER-FAQ.md."
    echo "----- END MAINTAINER SIGNING BLOCK -----"
elif [ "$PROFILE" = "tracker" ]; then
    echo "This is a STANDING deployment (--profile tracker), not a run-scoped world: it has no run"
    echo "number, is never settled into dust, and has no defined end -- it persists for this"
    echo "project's lifetime, the same way an issue tracker does. NO hooks were wired (deliberate"
    echo "-- 'a standing project is not a governed world', track-work.sh's own words, preserved)."
    echo ""
    echo "  cd $PROJECT_ROOT"
    echo "  ./autoharn led work open first-item \"Describe the first thing to track\"   # boundary auto-spawns"
    echo "  ./autoharn pickup            # live resume brief, including every open work item in full"
    echo "  ./autoharn distance-to-clean # composed closure-debt read"
    echo "  ./autoharn led work claim <slug>  /  ./autoharn led work close <slug> shipped --witness \"<ref>\""
    echo "  ./autoharn led work violations    # cycles / dangling deps / duplicate opens"
    echo "  ./autoharn doctor                 # is this deployment set up right? (witnessed lines)"
    echo ""
    echo "(run './autoharn --help' for the full generated verb roster.) The FIRST call to any of"
    echo "the above spawns the boundary service automatically (a detached child; logs at"
    echo "$PROJECT_ROOT/service.log) -- nothing is running yet at this line."
    echo ""
    echo "Rows written here via ./autoharn led are UNSTAMPED (stamp_agent/stamp_session/stamp_hmac all"
    echo "NULL, stamp_verified=false) until a separate, deliberate act wires change_gate/"
    echo "stamp_intercept/clean_exit and provisions a stamp secret (copy new-project.sh's own"
    echo ".claude/ wiring stanzas by hand, or re-scaffold this directory with --new-world instead)."
    echo ""
    echo "keys/README.md (AWAITING-KEY) explains this deployment's OWN GPG keyring: commit a public"
    echo "key there (never to autoharn's law/keys/) to move SIGNED commissions from NO-COMMITTED-KEY"
    echo "to VERIFIED -- ./autoharn verify-commission --id <id>; see user-guide/USER-GPG-TRUST-LAYER-FAQ.md §3."
else
    echo "  1. Apply a kernel lineage to $DB/$SCHEMA/$KERN/$ROLE if not already applied (kernel/lineage/, autoharn)."
    echo "  2. Provision the stamp secret -- see $PROJECT_ROOT/.claude/HOOKS.md (marked UNWITNESSED until you run it)."
    echo "  3. cd $PROJECT_ROOT && ./autoharn led decision \"...\"  /  ./autoharn judge  /  ./autoharn pickup"
    echo "  4. Read $PROJECT_ROOT/.claude/HOOKS.md and replace its UNWITNESSED marks as you exercise each command."
    if [ "$PIN" = "submodule" ]; then
        echo ""
        echo "PINNED DEPLOYMENT: every verb above and every hook in .claude/settings.json now runs"
        echo "out of $PROJECT_ROOT/.autoharn (git submodule, pinned to $AUTOHARN_COMMIT_SHA) -- a"
        echo "merge to autoharn's own working branch will NEVER change this deployment's behavior"
        echo "again. To take a newer autoharn deliberately: bootstrap/upgrade-submodule.sh"
        echo "$PROJECT_ROOT <new-sha> (from the autoharn checkout, not from inside $PROJECT_ROOT)."
    fi
fi
