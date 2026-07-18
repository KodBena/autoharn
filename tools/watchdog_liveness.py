#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-13T17:13:41Z
#   last-change: 2026-07-18T10:53:29Z
#   contributors: 3c50e030/main, ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""tools/watchdog_liveness.py -- the watchdog-liveness-harness slice (tracker item
`watchdog-liveness-harness`; design/ORCH-WATCHDOG-LIVENESS.md is the ONE design home this file's
every claim traces back to -- read that note first, this docstring restates only what a reader
needs to run the file, not why it is shaped this way).

WHAT THIS IS: a DIAGNOSTIC, not a gate. It reads a deployment's `.claude/logs/*.jsonl` journals
(the hook-observed action stream: `hooks/stamp_intercept.py` + `hooks/posttooluse_bash_completion.py`
for Bash dispatch/completion pairing; `hooks/pretooluse_delegation_observer.py` for subagent
dispatch/return pairing; every other `.claude/logs/*.journal.jsonl` for a generic recency pulse)
plus, best-effort, the deployment's own ledger (`estimate:` rows + `work_item_current` +
`work_claimed` timestamps) and reports, per surface, how long it has been since the last
observed event versus what was expected -- NEVER a death verdict. See design/
ORCH-WATCHDOG-LIVENESS.md Section 0: large-payload single-generation work between tool calls is
INVISIBLE to this checker's every signal, so a breach here is worded as a LIVENESS QUESTION
("no observable activity for Xm against an expected Ym -- look here"), never as "STALE", "HUNG",
or "DEAD". Nothing in this file kills, retries, or mutates anything -- it is read-only, end to
end, and its exit code (0 clean / 1 questions raised) is a diagnostic signal for an operator's
own polling loop, never a merge gate (hence `tools/`, not `gates/` -- see the design note's
"why tools/, not gates/").

CONFIG: a deployment's own `.claude/apparatus.json`, `mechanisms.watchdog` block (design note
Section 4). Missing file/key/mechanism degrades to the byte-held defaults below -- this checker
never refuses to run for want of config, matching every other apparatus-reading file in this
project's own convention (`filing/apparatus_registry.py`'s known-mechanisms scan already treats
this file's `MECHANISM_KEY` as a legitimate non-hook reader). This file never WRITES
apparatus.json and never touches `bootstrap/templates/apparatus.json` (a concurrent merge-gated
pass owns that file per this commission's own "do not touch" list) -- only a deployment's own
already-scaffolded copy, if one exists under `--root`.

MODE FIELD IS PRESENTLY INERT (tracker item `watchdog-mode-field-inert`; design note Section 4,
"The `mode` field is presently INERT"): `load_watchdog_config()` below deliberately does not read
a `mode` key from the `watchdog` block. This build implements the observe rung only -- there is
no `warn` or `enforce` rung yet for `mode` to select between, so a config's `"mode"` value
(whatever it is set to, including absent) has no effect on this checker's behavior. Named here so
the doc and the code cannot silently drift apart on this point (ADR-0002 Rule 4: a config field
the receiver cannot honor must not be silently accepted as if it were) -- when a `warn` rung is
built, this paragraph and its design-note counterpart are the two places to update together.

Stdlib-only, top-of-file imports (the lazy-import gate, gates/no_lazy_imports.py, applies).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

MECHANISM_KEY = "watchdog"  # apparatus_registry.py's pattern-1 extraction shape (module docstring).

_DEFAULT_SLACK_RATIO = 10.0
_DEFAULT_SLACK_ABSOLUTE_S = 1.0
_DEFAULT_IDLE_WARN_S = 300.0
_DEFAULT_CLASSES = {
    "bash": {"expected_s": 0.1, "slack_ratio": 10.0, "slack_absolute_s": 1.0},
    "subagent": {"expected_s": 60.0, "slack_ratio": 3.0, "slack_absolute_s": 30.0},
}


# ---------------------------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class ClassThreshold:
    expected_s: float
    slack_ratio: float
    slack_absolute_s: float

    def threshold_s(self) -> float:
        return self.expected_s * self.slack_ratio + self.slack_absolute_s

    def fmt_basis(self) -> str:
        return f"{self.expected_s}s x{self.slack_ratio} +{self.slack_absolute_s}s"


@dataclass(frozen=True)
class WatchdogConfig:
    idle_warn_s: float
    classes: dict[str, ClassThreshold]

    def for_class(self, name: str) -> ClassThreshold:
        return self.classes.get(name, self.classes["bash"])


def load_watchdog_config(root: Path | None) -> WatchdogConfig:
    """Reads `<root>/.claude/apparatus.json`'s `mechanisms.watchdog` block, best-effort (module
    docstring). Never raises; a missing file/key/mechanism, or a malformed value at any depth,
    silently falls back to the byte-held defaults above -- the same "never widen, never crash"
    posture every hook's own `_load_apparatus_quiet` keeps. Deliberately does NOT read a `mode`
    key -- see module docstring "MODE FIELD IS PRESENTLY INERT": this build has only one rung
    (observe), so there is nothing for `mode` to select yet."""
    idle_warn_s = _DEFAULT_IDLE_WARN_S

    cfg: dict = {}
    if root is not None:
        path = root / ".claude" / "apparatus.json"
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            mechs = raw.get("mechanisms") if isinstance(raw, dict) else None
            entry = mechs.get(MECHANISM_KEY) if isinstance(mechs, dict) else None
            if isinstance(entry, dict):
                cfg = entry
        except Exception:  # noqa: BLE001 -- best-effort, never crash on a missing/malformed file
            cfg = {}

    idle_warn_s = float(cfg.get("idle_warn_s", idle_warn_s))
    # `default_slack_ratio`/`default_slack_absolute_s` are an EXPLICIT operator override, applied
    # only when actually present in config -- NOT collapsed with "absent" (a prior build of this
    # function did exactly that, which silently made each built-in class's own distinct byte-held
    # slack defaults -- bash 10.0x/+1.0s, subagent 3.0x/+30.0s, per the module-level
    # `_DEFAULT_CLASSES` table -- dead code: with no apparatus.json at all, `subagent` would
    # threshold against the generic 10.0x/+1.0s figure instead of its own documented 3.0x/+30.0s,
    # a hazard found and fixed while building this same file's fixture coverage). `None` here
    # means "operator did not set this" and each built-in class falls through to its OWN default.
    default_ratio_override = cfg.get("default_slack_ratio")
    default_abs_override = cfg.get("default_slack_absolute_s")

    raw_classes = cfg.get("classes") if isinstance(cfg.get("classes"), dict) else {}
    merged: dict[str, ClassThreshold] = {}
    for name, defaults in _DEFAULT_CLASSES.items():
        override = raw_classes.get(name) if isinstance(raw_classes.get(name), dict) else {}
        class_ratio_default = (default_ratio_override if default_ratio_override is not None
                                else defaults["slack_ratio"])
        class_abs_default = (default_abs_override if default_abs_override is not None
                              else defaults["slack_absolute_s"])
        merged[name] = ClassThreshold(
            expected_s=float(override.get("expected_s", defaults["expected_s"])),
            slack_ratio=float(override.get("slack_ratio", class_ratio_default)),
            slack_absolute_s=float(override.get("slack_absolute_s", class_abs_default)),
        )
    # any class named only in config (not one of the two built-in defaults) is honored too --
    # a genuinely new custom class has no baked-in default of its own, so it falls through to the
    # explicit operator override if given, else this module's generic byte-held constants.
    for name, override in raw_classes.items():
        if name in merged or not isinstance(override, dict):
            continue
        merged[name] = ClassThreshold(
            expected_s=float(override.get("expected_s", 1.0)),
            slack_ratio=float(override.get(
                "slack_ratio",
                default_ratio_override if default_ratio_override is not None else _DEFAULT_SLACK_RATIO)),
            slack_absolute_s=float(override.get(
                "slack_absolute_s",
                default_abs_override if default_abs_override is not None else _DEFAULT_SLACK_ABSOLUTE_S)),
        )
    return WatchdogConfig(idle_warn_s=idle_warn_s, classes=merged)


# ---------------------------------------------------------------------------------------------
# Journal I/O
# ---------------------------------------------------------------------------------------------

def _read_jsonl(path: Path) -> list[dict]:
    """Every well-formed JSON object line, in file order. Malformed lines are skipped, never
    raised -- mirrors every hook journal reader in this project (e.g.
    `hooks/pretooluse_delegation_observer.py`'s own `_read_journal_lines`)."""
    if not path.is_file():
        return []
    out: list[dict] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(rec, dict):
                out.append(rec)
    except OSError:
        pass
    return out


def _parse_ts(s: str) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------------------------
# Class 1 -- Bash dispatch/completion pairing (mirrors
# hooks/posttooluse_bash_completion.py's own FIFO-by-command_sha256 pairing, READ-ONLY here --
# this file never writes invocations.jsonl/bash_completions.jsonl, only reads what those two
# hooks already wrote).
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class DispatchFinding:
    surface: str
    key: str
    elapsed_s: float
    threshold: ClassThreshold
    is_question: bool

    def line(self) -> str:
        basis = self.threshold.fmt_basis()
        if self.is_question:
            return (f"LIVENESS QUESTION: {self.surface} dispatch {self.key} has shown no "
                     f"observable activity for {self.elapsed_s:.1f}s against an expected "
                     f"{basis} -- look here.")
        return (f"  - {self.key}: elapsed {self.elapsed_s:.1f}s vs expected {basis} -- "
                f"within slack, quiet")


def bash_dispatch_status(logs_dir: Path, now: datetime, cfg: WatchdogConfig) -> list[DispatchFinding]:
    """Every Bash dispatch in `invocations.jsonl` with no paired completion in
    `bash_completions.jsonl` (paired by `command_sha256`, FIFO -- same correlation
    `hooks/posttooluse_bash_completion.py` itself performs at write time), reported against the
    `bash` class threshold. Returns one finding per still-open dispatch; an empty list means
    every dispatch has a matching completion (nothing open) OR no invocations were journaled at
    all (an unwired/quiet deployment) -- both print as "quiet" by the caller, not distinguished
    here (neither is a liveness question)."""
    dispatches = _read_jsonl(logs_dir / "invocations.jsonl")
    completions = _read_jsonl(logs_dir / "bash_completions.jsonl")
    paired_tokens = {c.get("token") for c in completions if c.get("pairing") == "token" and c.get("token")}
    threshold = cfg.for_class("bash")
    findings: list[DispatchFinding] = []
    for d in dispatches:
        token = d.get("token")
        if not token or token in paired_tokens:
            continue
        ts = _parse_ts(d.get("wall_clock") or d.get("ts") or "")
        if ts is None:
            continue
        elapsed = (now - ts).total_seconds()
        is_q = elapsed > threshold.threshold_s()
        findings.append(DispatchFinding("bash", str(token)[:8], elapsed, threshold, is_q))
    return findings


# ---------------------------------------------------------------------------------------------
# Class 3 -- subagent dispatch/return pairing (mirrors
# hooks/pretooluse_delegation_observer.py's own current correlation field, `tool_use_id` -- NOT
# `dispatch_ts`/`prompt_sha256` FIFO pairing, which is what an earlier build of this checker
# assumed; that hook's own module docstring states the change plainly ("prompt_sha256/
# prompt_excerpt remain, as event facts for a human/consumer to recognize the dispatch by, no
# longer as a correlation key" -- "tool_use_id... the identity the return leg now keys on"). A
# checker still pairing on the old field would silently never find a match and misreport every
# completed subagent call as perpetually open -- a hazard fixed here rather than shipped (CLAUDE.md
# engineering-responsibility clause), found while building this same file's slice.
# ---------------------------------------------------------------------------------------------

def subagent_dispatch_status(logs_dir: Path, now: datetime, cfg: WatchdogConfig) -> list[DispatchFinding]:
    """Every subagent dispatch line (no `kind` field) in `delegation_observer.journal.jsonl`
    whose `tool_use_id` never appears as some later `kind: "return"` line's own `tool_use_id` --
    an open, unreturned delegation. Honest limits: (1) no task-slug is carried by this journal,
    so only the class-default `subagent` threshold applies, never a per-task `estimate:`-sourced
    one (design note Section 1, class 3); (2) `tool_use_id` is written defensively by the hook
    (`if tool_use_id: rec["tool_use_id"] = ...`) and can be absent on either leg -- a dispatch or
    return record with no `tool_use_id` at all cannot be paired either way, and is skipped from
    this detector rather than guessed at (reporting it "open" would be a fabricated finding;
    reporting it "quiet" would hide a genuine stall -- neither is honest)."""
    lines = _read_jsonl(logs_dir / "delegation_observer.journal.jsonl")
    claimed_tool_use_ids = {r.get("tool_use_id") for r in lines
                             if r.get("kind") == "return" and r.get("tool_use_id")}
    threshold = cfg.for_class("subagent")
    findings: list[DispatchFinding] = []
    for d in lines:
        if d.get("kind") == "return":
            continue
        tool_use_id = d.get("tool_use_id")
        if not tool_use_id or tool_use_id in claimed_tool_use_ids:
            continue
        ts = _parse_ts(d.get("ts") or "")
        if ts is None:
            continue
        elapsed = (now - ts).total_seconds()
        is_q = elapsed > threshold.threshold_s()
        key = str(d.get("session_id", ""))[:8] or str(tool_use_id)[:8]
        findings.append(DispatchFinding("subagent", key, elapsed, threshold, is_q))
    return findings


# ---------------------------------------------------------------------------------------------
# Class 4/2/5 -- generic surface recency: the most recent timestamp across EVERY journal this
# deployment's hooks write, indistinguishably (design note Section 1, classes 2/4/5 are not
# separable from journal recency alone -- see Section 0).
# ---------------------------------------------------------------------------------------------

_KNOWN_JOURNAL_NAMES = (
    "invocations.jsonl",
    "bash_completions.jsonl",
    "delegation_observer.journal.jsonl",
    "mutation_observer.journal.jsonl",
    "read_observer.journal.jsonl",
    "doc_shapes_gate.journal.jsonl",
    "apparatus_flip.journal.jsonl",
    "change_gate.journal.jsonl",
    "stop_clean_exit.journal.jsonl",
)

_TS_FIELDS = ("ts", "wall_clock")


def _latest_ts_in(path: Path) -> datetime | None:
    latest: datetime | None = None
    for rec in _read_jsonl(path):
        for field in _TS_FIELDS:
            ts = _parse_ts(rec.get(field, ""))
            if ts is not None and (latest is None or ts > latest):
                latest = ts
    return latest


def surface_recency(logs_dir: Path, now: datetime, cfg: WatchdogConfig) -> tuple[float | None, bool]:
    """(seconds_since_latest_event, is_question). `seconds_since_latest_event` is None when no
    journal under `logs_dir` carries any parseable timestamp at all (an unwired/never-run
    deployment -- reported as SKIPPED by the caller, not as quiet or a question, since "no
    activity ever observed" and "no activity observed for this session" are honestly different
    conditions this function does not conflate)."""
    latest: datetime | None = None
    names = set(_KNOWN_JOURNAL_NAMES)
    if logs_dir.is_dir():
        names |= {p.name for p in logs_dir.glob("*.jsonl")}
    for name in names:
        ts = _latest_ts_in(logs_dir / name)
        if ts is not None and (latest is None or ts > latest):
            latest = ts
    if latest is None:
        return None, False
    elapsed = (now - latest).total_seconds()
    return elapsed, elapsed > cfg.idle_warn_s


# ---------------------------------------------------------------------------------------------
# Whole-item watchdog -- the first in-flight consumer of estimate:/work_item_current (design
# note Section 4 item 4). Best-effort: requires a resolvable deployment + a reachable DB;
# degrades to SKIPPED otherwise, never pretended clean.
# ---------------------------------------------------------------------------------------------

def _find_deployment(root: Path) -> dict | None:
    path = root / "deployment.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:  # noqa: BLE001
        return None


def _psql_tuples(dep: dict, sql: str) -> subprocess.CompletedProcess:
    host = dep.get("host", "")
    db = dep.get("db", "")
    return subprocess.run(
        ["psql", "-h", host, "-d", db, "-tA", "-F", "\x1f", "-R", "\x1e", "-c", sql],
        capture_output=True, text=True, timeout=8,
    )


def work_item_watchdog(root: Path, now: datetime, cfg: WatchdogConfig) -> tuple[list[str], str | None]:
    """(finding_lines, skip_reason). `skip_reason` is None iff the check actually ran (even if
    it found nothing); otherwise it names why (no deployment.json, DB unreachable, no
    work-item-layer kernel) -- never silently treated as clean."""
    dep = _find_deployment(root)
    if dep is None:
        return [], "no deployment.json under --root; ledger check not run"
    schema = dep.get("schema", "public")
    threshold = cfg.for_class("bash")  # whole-item check reuses the same slack knobs, generically
    try:
        r = _psql_tuples(dep,
            f"SELECT w.slug, l.ts, e.statement "
            f"FROM {schema}.work_item_current w "
            f"JOIN {schema}.ledger l ON l.kind = 'work_claimed' AND l.work_slug = w.slug "
            f"JOIN {schema}.ledger e ON e.kind = 'decision' AND e.statement ~ ('^estimate: ' || w.slug || ' \\|') "
            f"WHERE w.state = 'open' AND w.claimant IS NOT NULL "
            f"ORDER BY w.slug, l.id DESC, e.id DESC;"
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        return [], f"ledger unreachable: {type(e).__name__}: {e}"
    if r.returncode != 0:
        return [], f"ledger query failed: {r.stderr.strip()}"
    lines: list[str] = []
    seen_slugs: set[str] = set()
    for rec in r.stdout.split("\x1e"):
        if not rec.strip():
            continue
        parts = [p.strip() for p in rec.split("\x1f")]
        if len(parts) != 3:
            continue
        slug, claimed_ts_raw, statement = parts
        if slug in seen_slugs:
            continue  # ORDER BY ... DESC already put the latest claim/estimate first per slug
        seen_slugs.add(slug)
        claimed_ts = _parse_ts(claimed_ts_raw.replace(" ", "T", 1))
        if claimed_ts is None:
            continue
        elapsed = (now - claimed_ts).total_seconds()
        if elapsed > threshold.threshold_s() * 60:  # WALL-CLOCK fields are minutes-scale, not seconds
            lines.append(
                f"LIVENESS QUESTION: work item '{slug}' has been claimed for "
                f"{elapsed / 60:.1f}m with no closure -- estimate on record ({statement}) -- "
                f"look here.")
    return lines, None


# ---------------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------------

def _fmt_elapsed(seconds: float) -> str:
    return f"{seconds:.1f}s"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", required=True, help="deployment root (holds .claude/logs/, "
                                                    "optionally deployment.json)")
    ap.add_argument("--now", default=None, help="ISO-8601 UTC timestamp to treat as 'now' "
                                                 "(testing/fixture use; defaults to real now)")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    logs_dir = root / ".claude" / "logs"
    now = _parse_ts(args.now) if args.now else datetime.now(timezone.utc)
    if now is None:
        print(f"ERROR: --now value {args.now!r} is not a parseable ISO-8601 timestamp", file=sys.stderr)
        return 2

    cfg = load_watchdog_config(root)
    questions = 0

    print("=== BASH DISPATCHES ===")
    bash_findings = bash_dispatch_status(logs_dir, now, cfg)
    bash_questions = [f for f in bash_findings if f.is_question]
    if not bash_findings:
        print("quiet: 0 open dispatch(es)")
    else:
        print(f"{'LIVENESS QUESTIONS RAISED' if bash_questions else 'quiet'}: "
              f"{len(bash_findings)} open dispatch(es), {len(bash_questions)} liveness question(s)")
        for f in bash_findings:
            print(f.line())
    questions += len(bash_questions)

    print("=== SUBAGENT DISPATCHES ===")
    sub_findings = subagent_dispatch_status(logs_dir, now, cfg)
    sub_questions = [f for f in sub_findings if f.is_question]
    if not sub_findings:
        print("quiet: 0 open dispatch(es)")
    else:
        print(f"{'LIVENESS QUESTIONS RAISED' if sub_questions else 'quiet'}: "
              f"{len(sub_findings)} open dispatch(es), {len(sub_questions)} liveness question(s)")
        for f in sub_findings:
            print(f.line())
    questions += len(sub_questions)

    print("=== SURFACE RECENCY (all journals) ===")
    elapsed, is_q = surface_recency(logs_dir, now, cfg)
    if elapsed is None:
        print("SKIPPED (no journal with a parseable timestamp under this root)")
    elif is_q:
        print(f"LIVENESS QUESTION: no journal in this deployment has recorded an event for "
              f"{_fmt_elapsed(elapsed)} (warn at {cfg.idle_warn_s:.0f}s) -- look here.")
        questions += 1
    else:
        print(f"quiet: most recent event {_fmt_elapsed(elapsed)} ago (warn at {cfg.idle_warn_s:.0f}s)")

    print("=== WORK ITEMS (ledger, best-effort) ===")
    item_lines, skip_reason = work_item_watchdog(root, now, cfg)
    if skip_reason is not None:
        print(f"SKIPPED ({skip_reason})")
    elif not item_lines:
        print("quiet: no open+claimed work item exceeds its estimate x slack")
    else:
        for line in item_lines:
            print(line)
        questions += len(item_lines)

    print(f"--- verdict: {questions} liveness question(s) raised ---")
    return 1 if questions else 0


if __name__ == "__main__":
    sys.exit(main())
