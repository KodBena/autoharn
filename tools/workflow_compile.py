#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T19:48:12Z
#   last-change: 2026-07-18T19:51:41Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""workflow_compile — the fixed-shape-TOML-to-kernel-coupled-units compiler
(design/FABLE-WORKFLOW-UNIT-COMPILER-SPEC.md, commission ledger row 1658, compile target
ratified row 1659: KERNEL-COUPLED UNITS -- the kernel is the truth, the workflow obeys it).

WHAT THIS DOES. Reads one `design/workflows/*.toml` (the pipeline-dsl-v0 grammar; see
design/workflows/README.md and tools/workflow_check.py, which this tool shells out to as its
OWN pre-compile validation gate -- a TOML that workflow_check.py refuses is refused here too,
verbatim, before any output is written) and emits exactly two artifacts per the governing
spec's "Outputs" section:

  1. a HYDRATION SCRIPT (<out-dir>/<stem>/hydrate.sh) -- a deterministic sequence of `led`
     invocations: one `led work open` per phase, one `led work depends ... blocks-start` per
     depends_on edge, and (when a phase's `reviews` clause signals an independent countersign)
     an obligation act, gated by the row-1640 debt-surface confirmation.
  2. a DRIVER SCRIPT (<out-dir>/<stem>/drive.py) -- executes the wave by kernel conversation:
     claim, dispatch (prints the phase's prose brief), close, obeying whatever the kernel says.

THE ONE DESIGN COMMITMENT THIS TOOL HONORS: it adds NO enforcement machinery of its own. Every
blocking mechanism named in the commission (dependency blocker, completion blocker, obligation
blocker, role constraint) is a kernel fact the DRIVER discovers by attempting the act and
reading the kernel's own refusal -- never precomputed here. This compiler's own job stops at
emitting the deterministic, mechanical sequence of invocations; it evaluates no "is this
blocked" question of its own.

JUDGMENT CALLS THIS TOOL MAKES WHERE THE SPEC IS SILENT ON MECHANICS (documented here per
CLAUDE.md's "no hazard routed around silently" standard -- none of these touch kernel/law, all
are overridable at hydrate/drive time, none of them constitute a refusal the kernel didn't
already make):

  J1. PRINCIPAL IDENTITY. `[roles.<phase>]`'s authors/implements/reviews fields are PROSE
      (the specimens carry values like "sonnet-independent-subagent", "orchestrator") -- not
      registered ledger principal names, and the spec's Outputs section describes the driver
      claiming "as the implementing principal" without naming a mapping mechanism. This tool
      does not invent one from the prose. Both generated artifacts default every phase's
      implementing/claiming principal to 'author' (the one principal every --new-world scaffold
      registers as the connection's own default-speaking identity, s40 birth sequence) and
      accept a `--actor <phase>=<principal>` override (repeatable) at RUN time, never compile
      time -- the same posture `LED_ACTOR` already gives every other `led` verb.
  J2. OBLIGATION-NEED DETECTION. A phase is judged to want an independent-countersign
      obligation act iff `[roles.<phase>].reviews` is present, non-empty, textually DISTINCT
      (case/whitespace-folded) from that phase's own authors/implements text (same-actor
      self-review is not "independent"), and does not contain any of the case-insensitive
      substrings {"bookkeeping", "deferred explicitly", "explicitly none", "no independent"}
      (each names, in the specimens actually on file, a phase whose reviews clause explicitly
      is NOT a standing independent-countersign request -- a deferred item-keyed review, a
      judgment-free bookkeeping close, or an explicit absence). This is a heuristic over the
      four specimens on file, not a formal grammar the exploration spec defines; a future
      specimen this heuristic misjudges is a real gap to bring back to the exploration spec,
      not silently patched here.
  J3. ONE OBLIGATION ACT PER TOML, NOT PER PHASE. `led obligate` is ACTOR-keyed, not
      scope-keyed (the row-1640 teaching: a second obligate on an already-obliged actor is
      REFUSED as redundant governance, not layered). So when J2 fires for one or more phases
      naming the SAME default obliged-actor ('author'), the hydration script emits exactly ONE
      `led obligate` act for that actor, not one per triggering phase.
  J4. CLOSE DISPOSITION. The driver defaults every phase's close to `--review-deferred` (the
      honest default absent an actual witnessed review artifact this mechanical driver could
      cite) UNLESS the phase's `reviews` text contains "bookkeeping" (case-insensitive), in
      which case it uses `--review-bookkeeping --witness commit:<sha>`, with <sha> supplied by
      a required `--commit-witness <phase>=<sha>` driver argument (refused locally, driver-side,
      with a plain usage message -- NOT a kernel refusal -- if omitted for a bookkeeping phase).

Usage:
    python3 tools/workflow_compile.py <path-to.toml> [--out-dir DIR]

Exit 0 having written both artifacts (executable, chmod 0755) on success. Exit 1 if
workflow_check.py refuses the input (its refusal text is relayed verbatim) or the TOML cannot
otherwise be compiled. Lazy imports banned; stdlib only.
"""
from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_CHECK = REPO_ROOT / "tools" / "workflow_check.py"

# J2's non-independent signal substrings (case-insensitive containment test). Each is drawn
# from a phrase actually present in one of the four on-file specimens' reviews clauses, naming
# a phase whose review is explicitly NOT a standing independent-countersign request: a
# self-review/self-witness (same actor reviewing itself, even when the prose differs from the
# implements text -- e.g. "self-witnessed both polarities"), a deferred item-keyed review, a
# judgment-free bookkeeping close, or a discharge of an ALREADY-deferred item-keyed review
# (orchestrator-merge's own text: "discharging the review deferred at close-deferred") rather
# than a fresh standing obligation.
_NON_INDEPENDENT_SIGNALS = ("bookkeeping", "deferred explicitly", "explicitly none",
                            "no independent", "self-witness", "self-review", "discharging")


class CompileError(Exception):
    """Raised with a message explaining exactly why compilation was refused."""


def _fold(text: str) -> str:
    return " ".join(text.split()).casefold()


def validate_with_workflow_check(toml_path: Path) -> None:
    """Shell out to tools/workflow_check.py -- the ONE structural-validity check for this
    grammar (design/workflows/README.md, "The validator") -- rather than re-implementing its
    four refusal classes here. A TOML workflow_check refuses is refused here, verbatim."""
    proc = subprocess.run(
        [sys.executable, str(WORKFLOW_CHECK), str(toml_path)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise CompileError(
            f"workflow_check.py refused {toml_path} -- compilation stops here, before any "
            f"output is written:\n{proc.stderr.strip()}"
        )


def load_toml(toml_path: Path) -> dict:
    return tomllib.loads(toml_path.read_bytes().decode("utf-8"))


def phase_order(doc: dict) -> list[str]:
    """Declared order from [[phases]] -- open acts do not need topological order (work open
    carries no dependency precondition; only work depends/claim do), so declaration order is
    used as-is, matching the TOML's own reading order."""
    return [p["name"] for p in doc["phases"]]


def depends_edges(doc: dict) -> list[tuple[str, str]]:
    """(phase, antecedent) pairs, one per depends_on entry, in phase-declaration order then
    depends_on array order -- deterministic, matching the spec's 'deterministic sequence'
    requirement for the hydration script."""
    edges: list[tuple[str, str]] = []
    for p in doc["phases"]:
        for dep in p.get("depends_on", []):
            edges.append((p["name"], dep))
    return edges


def needs_obligation(doc: dict, phase: str) -> bool:
    """J2: does this phase's reviews clause name an independent countersign?"""
    roles = doc.get("roles", {}).get(phase, {})
    reviews = roles.get("reviews")
    if not reviews:
        return False
    reviews_folded = _fold(reviews)
    if any(sig in reviews_folded for sig in _NON_INDEPENDENT_SIGNALS):
        return False
    other = roles.get("implements") or roles.get("authors") or ""
    if other and _fold(other) == reviews_folded:
        return False
    return True


def is_bookkeeping_phase(doc: dict, phase: str) -> bool:
    roles = doc.get("roles", {}).get(phase, {})
    reviews = roles.get("reviews") or ""
    return "bookkeeping" in _fold(reviews)


def _bash_ident(phase: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in phase).upper()


HYDRATE_TEMPLATE = '''#!/usr/bin/env bash
# GENERATED by tools/workflow_compile.py from {toml_rel} -- do not hand-edit; recompile instead.
# design/FABLE-WORKFLOW-UNIT-COMPILER-SPEC.md's hydration-script artifact for workflow '{stem}'.
#
# Idempotent-by-refusal (per the governing spec): re-running this script is safe. Per PHASE, if
# `led work open` refuses (duplicate-open, s22/s31 semantics), this script treats that phase as
# ALREADY HYDRATED -- its depends_on edges and obligation act (already issued the first time,
# by construction: they are only ever issued in the same run as a phase's own successful open)
# are skipped too, never re-issued. This is a per-phase idempotency granularity, not a
# per-statement one: `led work depends` itself has no duplicate-edge refusal in this kernel (it
# silently appends another advisory row), so this script's own skip-on-duplicate-open logic is
# what keeps a second full run from adding rows -- not a kernel property.
set -uo pipefail

LED="./legacy/led"
OBLIGATE_ASSIGNED_BY="reviewer"
OBLIGATE_OBLIGED_ACTOR="author"
NO_OBLIGATE=0
ASSUME_YES=0

usage() {{
  echo "usage: $0 [--led <path>] [--obligate-assigned-by <principal>] [--obligate-obliged-actor <principal>] [--no-obligate] [--yes]" >&2
  exit 2
}}

while [ $# -gt 0 ]; do
  case "$1" in
    --led) LED="$2"; shift 2 ;;
    --obligate-assigned-by) OBLIGATE_ASSIGNED_BY="$2"; shift 2 ;;
    --obligate-obliged-actor) OBLIGATE_OBLIGED_ACTOR="$2"; shift 2 ;;
    --no-obligate) NO_OBLIGATE=1; shift ;;
    --yes) ASSUME_YES=1; shift ;;
    *) echo "$0: unrecognized argument '$1'" >&2; usage ;;
  esac
done

# deployment.json lives at the SCAFFOLD ROOT, read relative to the CURRENT WORKING DIRECTORY --
# not derived from --led's own path (both ./led and ./legacy/led resolve deployment.json this
# same way internally, from different directory depths, so deriving it from --led's dirname is
# fragile; this script is meant to be run from the scaffold root, exactly like `led` itself).
DEPLOYMENT="./deployment.json"

echo "-- workflow-unit hydration: {stem} (source {toml_rel}) --"
echo "-- led: $LED --"

# Returns 0 (already hydrated -- caller must skip this phase's edges/obligation) or 1 (freshly
# opened -- caller proceeds). Sets $OPEN_RC as the raw led exit code for callers that care.
open_phase() {{
  local slug="$1" title="$2"
  out=$("$LED" work open "$slug" "$title" 2>&1)
  OPEN_RC=$?
  if [ "$OPEN_RC" -eq 0 ]; then
    echo "$out"
    return 1
  fi
  if printf '%s' "$out" | grep -qi "already has an opening act"; then
    echo "$slug: already hydrated (duplicate-open refusal, treated as done) -- skipping its depends_on edges and obligation act."
    return 0
  fi
  echo "$out" >&2
  echo "$0: REFUSED for an UNEXPECTED reason (not duplicate-open) -- stopping rather than guessing." >&2
  exit 1
}}

{open_calls}

{depends_calls}

if [ "$NO_OBLIGATE" -eq 1 ]; then
  echo "-- --no-obligate given: skipping the obligation act ({obligation_phase_list}) --"
elif [ "{needs_any_obligation}" = "1" ]; then
  echo "-- obligation act needed (row-1640 debt-surface guard): phase(s) {obligation_phase_list} name an independent countersign --"
  echo "-- checking existing rows already written by '$OBLIGATE_OBLIGED_ACTOR' (these become retroactive debt-surface once obliged, per row-1640) --"
  HOST=$(python3 -c "import json; print(json.load(open('$DEPLOYMENT'))['host'])" 2>/dev/null)
  DB=$(python3 -c "import json; print(json.load(open('$DEPLOYMENT'))['db'])" 2>/dev/null)
  SCHEMA=$(python3 -c "import json; print(json.load(open('$DEPLOYMENT'))['schema'])" 2>/dev/null)
  if [ -n "$HOST" ] && [ -n "$DB" ] && [ -n "$SCHEMA" ]; then
    EXISTING_ROWS=$(psql -h "$HOST" -d "$DB" -tA -c \\
      "SELECT count(*) FROM ${{SCHEMA}}.ledger WHERE actor = (SELECT id FROM ${{SCHEMA}}_kernel.principal WHERE name = '$OBLIGATE_OBLIGED_ACTOR');" 2>/dev/null || echo "?")
  else
    EXISTING_ROWS="?"
  fi
  echo "-- PROJECTED DEBT-SURFACE DELTA: obliging '$OBLIGATE_OBLIGED_ACTOR' will retroactively flag its $EXISTING_ROWS existing ledger row(s) as review debt (led work review-gap / led review-gap), per the row-1640 obligate-footgun teaching (retroactive, no temporal bound, self-amplifying). --"
  if [ "$ASSUME_YES" -eq 1 ]; then
    echo "-- --yes given: proceeding without interactive confirmation --"
    CONFIRMED=1
  else
    printf "Type OBLIGATE to confirm writing this obligation row, anything else to skip: "
    read -r REPLY
    if [ "$REPLY" = "OBLIGATE" ]; then CONFIRMED=1; else CONFIRMED=0; fi
  fi
  if [ "$CONFIRMED" -eq 1 ]; then
    out=$("$LED" obligate "{stem}-review" "$OBLIGATE_ASSIGNED_BY" "$OBLIGATE_OBLIGED_ACTOR" 2>&1)
    rc=$?
    if [ $rc -eq 0 ]; then
      echo "$out"
    elif printf '%s' "$out" | grep -qi "already carries an"; then
      echo "$OBLIGATE_OBLIGED_ACTOR: already obliged (treated as already hydrated) --"
      echo "$out"
    else
      echo "$out" >&2
      exit 1
    fi
  else
    echo "-- obligation act SKIPPED (not confirmed) -- re-run with --yes or type OBLIGATE to write it. --"
  fi
else
  echo "-- no phase in this workflow names an independent countersign (J2) -- no obligation act to hydrate. --"
fi

echo "-- hydration complete for {stem} --"
'''

DRIVE_TEMPLATE = '''#!/usr/bin/env python3
"""GENERATED by tools/workflow_compile.py from {toml_rel} -- do not hand-edit; recompile instead.
design/FABLE-WORKFLOW-UNIT-COMPILER-SPEC.md's driver artifact for workflow '{stem}'.

Executes the wave by kernel conversation: for each phase, in an order re-derived by re-polling
`led work claim` every round (never precomputed here -- the claim's own verdict is the gate,
per the governing spec's one design commitment), CLAIM (as --actor, default 'author'; a
refusal is a BLOCKED unit, reported and moved past, never overridden), DISPATCH (prints the
phase's prose brief -- authors/implements/reviews text from the source TOML -- for the caller's
own agent dispatch; this driver does not itself invoke an agent), CLOSE (--review-deferred by
default, or --review-bookkeeping --witness commit:<sha> when the phase's reviews clause names a
bookkeeping close -- see J4 in tools/workflow_compile.py's own docstring).

Usage:
    python3 {stem}/drive.py [--led <path>] [--actor <phase>=<principal> ...]
                              [--commit-witness <phase>=<sha> ...] [--dry-run] [--rounds N]

Exit 0 when the round budget completes (whether or not every phase closed -- BLOCKED units are
an ordinary, reportable outcome, not a driver failure); exit 1 on an unexpected kernel refusal
at CLOSE time (a close, unlike a claim, should not refuse once claimed, so that IS treated as
unexpected here) or a local usage error (exit 2).
"""
from __future__ import annotations

import os
import subprocess
import sys

STEM = "{stem}"
TOML_REL = "{toml_rel}"

PHASES = {phases_repr}
BRIEFS = {briefs_repr}
BOOKKEEPING_PHASES = {bookkeeping_repr}
DEFAULT_ACTOR = "author"


def run_led(led: str, args: list[str], actor: str) -> tuple[int, str]:
    proc = subprocess.run([led] + args, capture_output=True, text=True,
                           env={{**os.environ, "LED_ACTOR": actor}})
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def parse_kv(pairs: list[str]) -> dict[str, str]:
    out: dict[str, str] = {{}}
    for pair in pairs:
        if "=" not in pair:
            print(f"drive.py: '{{pair}}' is not <key>=<value>", file=sys.stderr)
            sys.exit(2)
        k, v = pair.split("=", 1)
        out[k] = v
    return out


def main(argv: list[str]) -> int:
    led = "./legacy/led"
    actor_overrides: dict[str, str] = {{}}
    commit_witness: dict[str, str] = {{}}
    dry_run = False
    rounds = len(PHASES) + 1

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--led":
            led = argv[i + 1]; i += 2
        elif a == "--actor":
            actor_overrides.update(parse_kv([argv[i + 1]])); i += 2
        elif a == "--commit-witness":
            commit_witness.update(parse_kv([argv[i + 1]])); i += 2
        elif a == "--dry-run":
            dry_run = True; i += 1
        elif a == "--rounds":
            rounds = int(argv[i + 1]); i += 2
        else:
            print(f"drive.py: unrecognized argument '{{a}}'", file=sys.stderr)
            return 2

    for phase in BOOKKEEPING_PHASES:
        if phase not in commit_witness:
            print(f"drive.py: REFUSED locally (not a kernel refusal) -- phase '{{phase}}' "
                  f"closes --review-bookkeeping and needs --commit-witness {{phase}}=<sha>, "
                  f"none given.", file=sys.stderr)
            return 2

    print(f"-- driving workflow '{{STEM}}' (source {{TOML_REL}}) via {{led}} --")

    closed: set[str] = set()
    for round_no in range(1, rounds + 1):
        made_progress = False
        for phase in PHASES:
            slug = f"{{STEM}}-{{phase}}"
            if slug in closed:
                continue
            actor = actor_overrides.get(phase, DEFAULT_ACTOR)
            print(f"round {{round_no}}: attempting claim of '{{slug}}' as '{{actor}}' ...")
            if dry_run:
                print(f"  (dry-run) would run: LED_ACTOR={{actor}} {{led}} work claim {{slug}}")
                continue
            claim_rc, claim_out = run_led(led, ["work", "claim", slug], actor)
            if claim_rc != 0:
                print(f"  BLOCKED -- kernel refusal (verbatim):\\n{{claim_out}}")
                continue
            print(f"  claimed: {{claim_out}}")
            brief = BRIEFS.get(phase, "")
            print(f"  DISPATCH -- brief for '{{phase}}':\\n{{brief}}")
            if phase in BOOKKEEPING_PHASES:
                close_args = ["work", "close", slug, "shipped", "--review-bookkeeping",
                              "--witness", f"commit:{{commit_witness[phase]}}"]
            else:
                close_args = ["work", "close", slug, "shipped", "--review-deferred",
                              "--witness", f"unit:{{slug}}"]
            close_rc, close_out = run_led(led, close_args, actor)
            if close_rc != 0:
                print(f"  CLOSE REFUSED -- kernel refusal (verbatim):\\n{{close_out}}",
                      file=sys.stderr)
                return 1
            print(f"  closed: {{close_out}}")
            closed.add(slug)
            made_progress = True
        if len(closed) == len(PHASES) or (not made_progress and not dry_run):
            break

    print(f"-- drive complete: {{len(closed)}}/{{len(PHASES)}} phase(s) closed --")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
'''


def render_hydrate(stem: str, toml_rel: str, doc: dict) -> str:
    phases = phase_order(doc)

    open_calls_lines = []
    for phase in phases:
        slug = f"{stem}-{phase}"
        title = f"{phase} phase of {stem} (from {toml_rel})"
        ident = _bash_ident(phase)
        open_calls_lines.append(
            f'open_phase "{slug}" "{title}"\n'
            f'PHASE_{ident}_FRESH=$?\n'
        )
    open_calls = "\n".join(open_calls_lines)

    depends_lines = []
    for phase, dep in depends_edges(doc):
        slug = f"{stem}-{phase}"
        dep_slug = f"{stem}-{dep}"
        ident = _bash_ident(phase)
        depends_lines.append(
            f'if [ "$PHASE_{ident}_FRESH" -eq 1 ]; then\n'
            f'  out=$("$LED" work depends "{slug}" "{dep_slug}" --type blocks-start 2>&1); rc=$?\n'
            f'  echo "$out"\n'
            f'  [ $rc -eq 0 ] || {{ echo "$0: REFUSED writing depends edge {slug} -> {dep_slug}" >&2; exit 1; }}\n'
            f'else\n'
            f'  echo "{slug}: skipping depends_on edge to {dep_slug} (phase already hydrated)"\n'
            f'fi'
        )
    depends_calls = "\n".join(depends_lines) if depends_lines else \
        "echo '-- no depends_on edges declared --'"

    obligation_phases = [p for p in phases if needs_obligation(doc, p)]
    needs_any = "1" if obligation_phases else "0"
    obligation_phase_list = ", ".join(obligation_phases) if obligation_phases else "(none)"

    return HYDRATE_TEMPLATE.format(
        toml_rel=toml_rel, stem=stem,
        open_calls=open_calls, depends_calls=depends_calls,
        needs_any_obligation=needs_any, obligation_phase_list=obligation_phase_list,
    )


def render_drive(stem: str, toml_rel: str, doc: dict) -> str:
    phases = phase_order(doc)
    briefs = {}
    for phase in phases:
        roles = doc.get("roles", {}).get(phase, {})
        parts = []
        for key in ("authors", "implements", "reviews"):
            if roles.get(key):
                parts.append(f"{key}: {roles[key]}")
        conv = doc.get("convergence", {}).get(phase, {})
        if conv.get("done"):
            parts.append(f"done: {conv['done']}")
        landing = doc.get("landing_zones", {}).get(phase, {})
        zone = landing.get("zone") if isinstance(landing, dict) else landing
        if zone:
            parts.append(f"landing_zone: {zone}")
        briefs[phase] = "\n".join(parts)
    bookkeeping = [p for p in phases if is_bookkeeping_phase(doc, p)]

    return DRIVE_TEMPLATE.format(
        stem=stem, toml_rel=toml_rel,
        phases_repr=repr(phases),
        briefs_repr=repr(briefs), bookkeeping_repr=repr(bookkeeping),
    )


def compile_toml(toml_path: Path, out_dir: Path) -> tuple[Path, Path]:
    validate_with_workflow_check(toml_path)
    doc = load_toml(toml_path)
    stem = toml_path.stem
    try:
        toml_rel = str(toml_path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        toml_rel = str(toml_path)

    unit_dir = out_dir / stem
    unit_dir.mkdir(parents=True, exist_ok=True)

    hydrate_path = unit_dir / "hydrate.sh"
    hydrate_path.write_text(render_hydrate(stem, toml_rel, doc))
    hydrate_path.chmod(0o755)

    drive_path = unit_dir / "drive.py"
    drive_path.write_text(render_drive(stem, toml_rel, doc))
    drive_path.chmod(0o755)

    return hydrate_path, drive_path


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: python3 tools/workflow_compile.py <path-to.toml> [--out-dir DIR]",
              file=sys.stderr)
        return 2
    toml_arg = argv[0]
    out_dir = REPO_ROOT / "tools" / "workflow_units"
    i = 1
    while i < len(argv):
        if argv[i] == "--out-dir":
            out_dir = Path(argv[i + 1])
            i += 2
        else:
            print(f"unrecognized argument: {argv[i]}", file=sys.stderr)
            return 2

    toml_path = Path(toml_arg)
    try:
        hydrate_path, drive_path = compile_toml(toml_path, out_dir)
    except CompileError as exc:
        print(f"workflow_compile: REFUSED -- {exc}", file=sys.stderr)
        return 1

    print(f"workflow_compile: OK -- wrote {hydrate_path} and {drive_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
