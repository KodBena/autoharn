#!/bin/sh
# track-experiments.sh — give ANY project a STANDING, deployment-local recording surface for
# stores/001_research_ledger.sql (the PROJECT-AGNOSTIC measurement-provenance ledger: core.
# project/core.session + research.instrument/research.reading/research.finding + the derived
# research.finding_confirmed view). Mirrors bootstrap/track-work.sh's own offering shape
# exactly (this script's header comment is written the same way, on purpose, so a reader who
# already understands track-work.sh recognizes the pattern immediately) — see BACKLOG's
# "Chocofarm experiment-ledger disposition" entries (2026-07-11) and design/MAINTAINER-
# DECISION-BRIEF.md §4 for the full provenance of the store this script wires an adopter to.
#
# WHAT THIS IS, IN ONE SENTENCE: writes a small deployment-local record (research-ledger.json)
# plus ONE thin exec shim (record-reading) into <project-dir>, pointed at the STANDING
# `research` database's core/research schema pair — nothing else. It never applies the DDL
# itself (that is bootstrap/apply-research-ledger.sh's job, and stays exclusively the
# maintainer's own act — this script does not run it, does not offer to run it, and does not
# duplicate any of its logic) and it never wires a hook (no governance, no CLAUDE.md preamble,
# no runs-are-linear regime — the same "standing, not a governed world" posture track-work.sh
# already established for the work-item ledger, restated here for the research ledger).
#
# BOUNDED SCOPE, STATED PLAINLY (maintainer framing, 2026-07-12: "something our harness was
# supposed to service consumers of the harness... insofar as it's a kind of experiment ledger;
# though we've decided not to go all in on being a proper research ledger, that'd take us too
# far afield"): this script is the ONE adoption verb the offering gets. It does not add a
# second work-tracking layer, a second kernel, a second governance mode, or any new capability
# to stores/001_research_ledger.sql or filing/record_reading.py — both of those are used
# exactly as they already exist (a schema-vs-writer split this script respects, never blurs).
#
# Usage:
#   bootstrap/track-experiments.sh <project-dir> --name <name> --db <db> --host <host> \
#       [--core-schema <schema>] [--research-schema <schema>] [--force]
#
#   <project-dir>       where to write the deployment-local files (created if missing) — ANY
#                        directory; it need not be a git repo, need not be a Claude Code
#                        project, need not run any governed session (track-work.sh's own
#                        posture, restated).
#   --name               REQUIRED. This becomes the `project_id` every reading/finding this
#                        deployment records is attributed to in core.project (filing/
#                        record_reading.py's own ensure_project, called automatically on the
#                        FIRST record-reading invocation — nothing here writes to the database
#                        at adoption time; see "WHAT THIS DOES NOT DO" below). Pick something
#                        that will not collide with another project's own project_id on the
#                        SAME standing research db — project_id is this store's own namespacing
#                        axis (stores/001_research_ledger.sql's own header: "chocofarm's
#                        throughput_lab and omega's perf work are consumers that write here
#                        tagged project_id; this is not their schema").
#   --db                 the STANDING research database's name (matches filing/
#                        record_reading.py's own RL_DB / --db convention — NOT the same
#                        database as a project's own kernel-lineage ledger from track-work.sh
#                        or new-project.sh, which is a wholly separate store).
#   --host               the postgres host the standing research database lives on.
#   --core-schema         optional, default "core" (stores/001_research_ledger.sql's own fixed
#                        schema name — NOT parameterized like track-work.sh's --schema, because
#                        001's DDL is a single SHARED schema pair, not one-schema-per-project;
#                        override only to point this deployment at a scratch pair, e.g. for
#                        this offering's own seen-red fixture).
#   --research-schema     optional, default "research" (see --core-schema).
#   --force               overwrite an existing research-ledger.json at <project-dir> (default:
#                        refuse — mirrors track-work.sh's own re-run posture: a standing
#                        deployment is meant to persist indefinitely, so a bare re-run is
#                        presumptively a mistake, not a routine "refresh").
#
# WHAT THIS DOES NOT DO, on purpose:
#   - apply stores/001_research_ledger.sql, or ANY DDL, to any database. That ceremony (typed
#     confirmation, transaction-wrapped apply, preflight-for-already-applied) belongs solely to
#     bootstrap/apply-research-ledger.sh, run solely by the maintainer. This script's own
#     preflight (below) is READ-ONLY and purely informational — it never writes.
#   - wire any `.claude/` hook, apparatus, or governance preamble (track-work.sh's own "STANDING
#     vs WORLD" contrast applies here identically — see that script's header for the full
#     argument; not repeated here to avoid a second, driftable copy, ADR-0012 P1).
#   - touch git in any way (the caller commits research-ledger.json/record-reading if
#     <project-dir> is a git repo and wants them tracked — this script has no opinion on that).
#   - modify filing/record_reading.py or stores/001_research_ledger.sql in any way. The thin
#     recording surface this script writes is a CALLER of the former, never a second
#     implementation of either (ADR-0012 P1 again: one writer, one schema, this script only
#     wires an adopter to them).
set -eu

usage() {
    echo "usage: $0 <project-dir> --name <name> --db <db> --host <host>" >&2
    echo "           [--core-schema <schema>] [--research-schema <schema>] [--force]" >&2
    echo "       (--name becomes this deployment's project_id in core.project — REQUIRED, this" >&2
    echo "        script's one namespacing input, mirroring track-work.sh's own required --name." >&2
    echo "        --core-schema/--research-schema default to 001_research_ledger.sql's own fixed" >&2
    echo "        names, core/research — override only to point at a scratch pair.)" >&2
    exit 2
}

# Captured BEFORE any argument parsing consumes "$@" (mirrors track-work.sh's own CREATE_CMD/
# CREATED_AT capture — the operator's ACTUAL invocation, printed at the end and written into
# research-ledger.json, so "how was this deployment adopted" never needs reconstruction).
CREATE_CMD="$0"
for _a in "$@"; do
    case "$_a" in
        *[\ \	]*) CREATE_CMD="$CREATE_CMD '$_a'" ;;
        *) CREATE_CMD="$CREATE_CMD $_a" ;;
    esac
done
CREATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

[ $# -ge 1 ] || usage
DEST="$1"; shift
NAME=""
FORCE=0
DB=""; HOST=""; CORE_SCHEMA="core"; RESEARCH_SCHEMA="research"
while [ $# -gt 0 ]; do
    case "$1" in
        --db) DB="$2"; shift 2 ;;
        --host) HOST="$2"; shift 2 ;;
        --core-schema) CORE_SCHEMA="$2"; shift 2 ;;
        --research-schema) RESEARCH_SCHEMA="$2"; shift 2 ;;
        --name) NAME="$2"; shift 2 ;;
        --force) FORCE=1; shift ;;
        *) echo "unrecognized argument: $1" >&2; usage ;;
    esac
done
[ -n "$NAME" ] || usage
[ -n "$DB" ] && [ -n "$HOST" ] || usage

# --- STRICT CHARACTER ALLOWLIST on every name that becomes SQL text ----------------------------
# ADR-0012's 2026-07-18 amendment ("The interpreter boundary -- a value never crosses as program
# text") + ADR-0000's same-day Rule 2(a) amendment (ledger row 1637, fixed first in
# bootstrap/teardown-world.sh commit 0ce5055, then in four sibling scripts by commit 1e18722,
# which flagged this script's own preflight query as the next sighting of the same pattern):
# CORE_SCHEMA/RESEARCH_SCHEMA reach the preflight SQL text below (bound as psql -v values) --
# checked before ANY SQL is built, covering both the defaults and a --core-schema/
# --research-schema override alike. NAME/DB/HOST never reach SQL text (NAME is JSON-escaped by
# json.dumps below; DB/HOST are psql's own -d/-h argv, never spliced into a query string) so
# they are outside this allowlist's scope, the same reasoning the sibling fixes applied.
for _name in "$CORE_SCHEMA" "$RESEARCH_SCHEMA"; do
    case "$_name" in
        ''|*[!A-Za-z0-9_]*)
            echo "track-experiments.sh: REFUSED -- '$_name' contains characters outside the" >&2
            echo "                      allowlist for a schema name (letters, digits, underscore" >&2
            echo "                      only). This applies to the --core-schema/--research-schema" >&2
            echo "                      overrides and their defaults alike. Nothing was touched." >&2
            exit 1
            ;;
    esac
done
unset _name

AUTOHARN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

mkdir -p "$DEST"
PROJECT_ROOT="$(cd "$DEST" && pwd)"

CONFIG="$PROJECT_ROOT/research-ledger.json"
if [ -f "$CONFIG" ] && [ "$FORCE" -ne 1 ]; then
    echo "track-experiments.sh: $CONFIG already exists -- refusing to overwrite (pass --force to replace it)." >&2
    echo "  (a standing deployment is meant to persist indefinitely; re-running this script against" >&2
    echo "  an existing one is presumptively a mistake, not a routine 'refresh' -- there is no such" >&2
    echo "  concept here, mirroring track-work.sh's identical posture on its own deployment.json.)" >&2
    exit 1
fi

echo "== standing research-ledger recording surface at $PROJECT_ROOT (project_id=$NAME) =="
echo "   This is a STANDING, deployment-local adoption, not a governed world: no hooks, no run"
echo "   number, no defined end. It wires this project to the ALREADY-EXISTING (or not yet"
echo "   applied -- see the preflight below) shared research ledger at $HOST/$DB, schema pair"
echo "   $CORE_SCHEMA/$RESEARCH_SCHEMA -- it does not create, own, or modify that schema."
echo ""

# READ-ONLY, INFORMATIONAL ONLY (never writes; see "WHAT THIS DOES NOT DO" above). Mirrors
# bootstrap/apply-research-ledger.sh's own preflight query exactly (same SELECT, same two
# tables checked) so this script's "is it applied?" answer can never drift from that script's
# own understanding of what "applied" means (ADR-0012 P1 -- one definition, not a second one
# re-derived here). A failed connection is reported honestly and does not abort adoption --
# the deployment-local files below are useful on their own regardless of DB reachability right
# now (the same posture record_reading.py itself takes: it never pre-checks reachability
# either, letting the first real write attempt be the honest signal).
set +e
# SQL text fed on stdin, never via -c (psql's :'var'/:"var" substitution is a silent no-op under
# -c, verified live -- same fix shape as bootstrap/teardown-world.sh commit 0ce5055 and the four
# sibling scripts fixed by commit 1e18722). CORE_SCHEMA/RESEARCH_SCHEMA are bound as psql -v
# string-literal values (:'core_schema'/:'research_schema'), concatenated with a literal
# '.project'/'.reading' suffix inside SQL, then handed to to_regclass exactly as the original
# raw-interpolated string was -- the value crosses the interpreter boundary as DATA, never as
# spliced program text, so a crafted name can no longer alter the query's structure (the
# allowlist above additionally refuses anything outside [A-Za-z0-9_]+ before this SQL is built).
APPLIED="$(printf '%s\n' \
    "SELECT to_regclass(:'core_schema' || '.project') IS NOT NULL OR to_regclass(:'research_schema' || '.reading') IS NOT NULL;" \
    | psql -h "$HOST" -d "$DB" -v core_schema="$CORE_SCHEMA" -v research_schema="$RESEARCH_SCHEMA" -tA 2>&1)"
PREFLIGHT_STATUS=$?
set -e
if [ "$PREFLIGHT_STATUS" -ne 0 ]; then
    echo "-- preflight: could not reach $HOST/$DB to check whether the research ledger schema is"
    echo "   applied yet ($APPLIED). Proceeding anyway -- writing the deployment-local files below"
    echo "   does not require the database to be reachable right now; the first real 'record-reading'"
    echo "   call is the honest signal if the target turns out to be unreachable or unapplied."
elif [ "$APPLIED" = "t" ]; then
    echo "-- preflight: the research ledger schema ($CORE_SCHEMA/$RESEARCH_SCHEMA) IS applied on"
    echo "   $HOST/$DB -- this deployment is ready to record readings immediately."
else
    echo "-- preflight: the research ledger schema ($CORE_SCHEMA/$RESEARCH_SCHEMA) is NOT yet applied"
    echo "   on $HOST/$DB. This deployment is still written below (it is useful the moment"
    echo "   the schema lands), but the first 'record-reading' call will fail loudly (psql's own"
    echo "   'relation does not exist') until the maintainer runs bootstrap/apply-research-ledger.sh"
    echo "   -- this script does not run it and does not offer to; that stays the maintainer's act."
fi
echo ""

echo "-- research-ledger.json --"
# Inline, not a shared module (mirrors track-work.sh's own choice to inline the sedsubst
# convention for its per-verb shims): this JSON shape has exactly one writer, this script, and
# no other consumer parses it programmatically today (the record-reading shim below bakes its
# own values directly rather than reading this file back) -- ADR-0012 P1 does not ask for a
# module with a single call site. json.dumps is used only to escape CREATE_CMD/paths safely,
# never to invent structure beyond this flat object.
PY="$HOME/w/vdc/venvs/generic/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"
"$PY" - "$CONFIG" "$NAME" "$HOST" "$DB" "$CORE_SCHEMA" "$RESEARCH_SCHEMA" "$CREATED_AT" "$CREATE_CMD" <<'PYEOF'
import json
import sys

path, project_id, host, db, core_schema, research_schema, created_at, create_cmd = sys.argv[1:9]
record = {
    "project_id": project_id,
    "host": host,
    "db": db,
    "core_schema": core_schema,
    "research_schema": research_schema,
    "created_at": created_at,
    "create_cmd": create_cmd,
}
with open(path, "w", encoding="utf-8") as f:
    json.dump(record, f, indent=2)
    f.write("\n")
PYEOF
echo "wrote $CONFIG"

echo "-- record-reading (thin exec shim -- bakes connection params, execs filing/record_reading.py"
echo "   LIVE out of this checkout, same 'a fix reaches every deployment instantly' mechanism"
echo "   track-work.sh's own verb shims use) --"
cat > "$PROJECT_ROOT/record-reading" <<SHIM
#!/bin/sh
exec env RL_PGHOST="$HOST" RL_DB="$DB" RL_CORE_SCHEMA="$CORE_SCHEMA" RL_RESEARCH_SCHEMA="$RESEARCH_SCHEMA" \\
    python3 "$AUTOHARN_ROOT/filing/record_reading.py" "\$@"
SHIM
chmod +x "$PROJECT_ROOT/record-reading"
echo "wrote record-reading (shim -> $AUTOHARN_ROOT/filing/record_reading.py, connection params baked)"

echo ""
echo "== done =="
echo "   $CREATE_CMD"
echo ""
echo "NO hooks were wired, NO database DDL was applied (deliberate -- see this script's own header"
echo "comment). Use the shim exactly as filing/record_reading.py's own CLI documents, connection"
echo "flags already filled in:"
echo "  cd $PROJECT_ROOT"
echo "  ./record-reading record-reading --project $NAME --metric <name> --value <v> \\"
echo "      --git-commit <sha> --git-tree clean --instrument-name <n> --instrument-kind script \\"
echo "      --source-hash <sha256> --instrument-git-commit <sha> --instrument-git-tree clean"
echo "  ./record-reading record-finding --project $NAME --reading <id> --interpretation \"<text>\""
echo ""
echo "research-ledger.json records what this deployment points at, for a human or a later"
echo "re-adoption to read; the shim's own baked env vars are the live source record-reading"
echo "actually runs against (generated together, from the same values, at the same time -- they"
echo "cannot independently drift from what research-ledger.json also reports)."
