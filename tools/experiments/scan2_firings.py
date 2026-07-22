#!/usr/bin/env python3
"""scan2_firings — the append-only firing ledger for tools/experiments/compound_nominal_scan2.py
(ledger row 337, "detector-firing-telemetry"; unblocked by the maintainer's 2026-07-14 detector
adoption, ledger row 658).

WHY THIS EXISTS (verbatim in substance, the maintainer's own reason, ledger row 337): scan2 may
be non-general or biased — its specimen was known to its builder, so a rank-1 catch on that
specimen is IN-SAMPLE evidence, not proof of general validity. If the detector is
effective-but-biased, the accumulated firing data — INCLUDING its false positives — is the
dataset a later, more disciplined solution gets worked out from. This module is that dataset's
one writer (P1, ADR-0012): every fired finding from a real scan2 run over the live corpus lands
here, compressed, before a human ever triages it.

SHAPE. One append-only file, `tools/experiments/results/scan2-firings.jsonl`, two record kinds
sharing it (a `kind` discriminator field), never mutated in place — a later disposition is a
NEW appended record, not an edit of the firing line it disposes (the file's own append-only
posture is the audit property; rewriting a line to attach a verdict would destroy it):

  - `firing`  — one per fired finding per run: WHAT fired (finding_key, rule/angle, rank,
    score), WHERE (compressed site list), and WHEN/on WHAT corpus state (run_id, run_ts,
    git_hash, git_dirty). `disposition` is always null on this record kind — it is never
    known at record time.
  - `disposition` — a human verdict backfilled at triage, keyed by `finding_key` (and,
    optionally, the specific `run_id` it was read from). Applied by
    `python3 tools/experiments/scan2_firings.py triage <finding_key> <TP|FP|house-term> [--run
    <run_id>] [--note TEXT] [--by NAME]`. A finding_key is stable across runs (the same
    compound / same table header recurs run to run with the same key), so one triage call
    covers every future recurrence unless a specific `--run` narrows it.

WHAT IS RECORDED, WHAT IS NOT (stated, not silent — ADR-0000 Rule 2a closure-statement
discipline, itself externally reviewed, not self-certified — see next paragraph). Recorded:
`cmd_class1` and `cmd_tables` in compound_nominal_scan2.py — the two modes that scan the LIVE
tracked corpus and are the tool's actual detection runs; recording is unconditional in both (no
flag disables it), so a real fired candidate cannot happen unrecorded. EVERY fired candidate is
recorded, every run — the full ranked/findings list, not the printed top-K. NOT recorded at
all: `cmd_specimens` — it scans synthetic/historical specimen text spliced in from git history
for a self-test of recall, not a production run against the live corpus; folding its synthetic
"<SPECIMEN:...>" pseudo-paths into the triage dataset under a real git_hash would misrepresent
what was actually found in the tree at that commit. That is the one stated exclusion, not an
accidental gap.

WHY NOT BOUND TO THE PRINTED TOP-K (a corrected design decision, kept here as a record of the
correction rather than erased — ADR-0013 Rule 5, verify the artifact, not the claim). An
earlier revision of this module bounded CLASS 1 recording to `--top`/`--dump-all`, on the
theory that a candidate never shown to a reviewer was never a "finding" in the triage sense.
An out-of-frame hack-rationalization review (run before this module's first commit) caught the
real cost: bounding to the printed top-K survivorship-biases the accumulating dataset toward
whatever the CURRENT, unproven `10*A + 3*B + C` score formula already favors — precisely the
bias this telemetry exists to let a later, more disciplined pass diagnose and correct (the
maintainer's own stated reason for commissioning it, ledger row 337: "the accumulated firing
data INCLUDING false positives becomes the dataset"). Recording everything is the more literal,
more general reading and needs no maintainer decision; its cost — a five-figure line count per
bare invocation on this corpus, since angle C is a documented flood with no defect-detection
claim of its own — is disclosed here, not hidden, and is the dataset's signal, not noise to
pre-filter. If committed-file growth becomes an operational problem, retention/rotation policy
is a real follow-up question for the maintainer; it is not a reason to narrow what gets
recorded today.

COMPRESSED, PER THE COMMISSION. A firing record carries the artifact site(s) (capped at 3), the
rule/angle(s) that fired, rank, score, and a short human-readable detail string (capped at 300
chars) — never the full ranked-list internals (segment token lists, full label/form arrays for
a CLASS 2 table). Diagnostic-grade (this project's action-stream ruling): best-effort, not a
tamper-evident audit spine.

SCHEMA ENFORCEMENT. `validate_record` is the one place a record's shape is checked (P1); the
gate `gates/scan2_firing_schema.py` imports it rather than re-deriving the schema (P7's
cross-boundary no-second-writer rule applied within one language) and validates every banked
line, so a malformed record is a checkable, gated fact rather than an unenforced convention
(ADR-0012 cancer G).

Lazy imports banned (CLAUDE.md, 2026-07-02 edict).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FIRINGS_PATH = REPO / "tools" / "experiments" / "results" / "scan2-firings.jsonl"

SCHEMA_VERSION = 1
DETECTOR = "compound_nominal_scan2"
VALID_CLASSES = {"class1", "class2"}
VALID_DISPOSITIONS = {"TP", "FP", "house-term"}
MAX_SITES = 3
MAX_DETAIL = 300


class RecordError(ValueError):
    """A record failed construction-time validation — refused, not silently accepted
    (ADR-0012 P2: a boundary translates-and-validates; it does not coerce)."""


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_run_id() -> str:
    return uuid.uuid4().hex[:16]


def corpus_git_hash() -> tuple[str, bool]:
    """(HEAD commit hash, working-tree dirty?) for the corpus this run scanned. Never raises —
    an observer/recorder that breaks the tool call over a git hiccup is the wrong failure mode;
    a failure here yields ("unknown", True), loudly distinguishable from a real hash."""
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True,
                               text=True, timeout=10, check=True).stdout.strip()
        status = subprocess.run(["git", "status", "--porcelain"], cwd=REPO, capture_output=True,
                                 text=True, timeout=10, check=True).stdout
        return head, bool(status.strip())
    except Exception:  # noqa: BLE001 -- never break the scan over a git hiccup
        return "unknown", True


def _truncate(s: str, n: int) -> str:
    s = s or ""
    return s if len(s) <= n else s[: n - 1] + "…"


@dataclass(frozen=True)
class FiringRecord:
    """One fired finding, one run. `disposition` is always None here — see module docstring;
    the eventual human verdict is a separate, later-appended DispositionRecord, keyed by
    `finding_key`."""

    run_id: str
    run_ts: str
    git_hash: str
    git_dirty: bool
    defect_class: str
    mode: str
    finding_key: str
    rule: str
    rank: int
    score: float
    sites: list = field(default_factory=list)
    detail: str = ""
    kind: str = "firing"
    schema_version: int = SCHEMA_VERSION
    detector: str = DETECTOR
    disposition: str | None = None

    def __post_init__(self):
        if self.defect_class not in VALID_CLASSES:
            raise RecordError(f"defect_class {self.defect_class!r} not in {VALID_CLASSES}")
        if not self.finding_key:
            raise RecordError("finding_key is required")
        if not self.rule:
            raise RecordError("rule (the angle(s) that fired) is required")
        if self.rank < 1:
            raise RecordError(f"rank must be >= 1, got {self.rank}")
        object.__setattr__(self, "sites", list(self.sites)[:MAX_SITES])
        object.__setattr__(self, "detail", _truncate(self.detail, MAX_DETAIL))


@dataclass(frozen=True)
class DispositionRecord:
    """A human verdict backfilled at triage. `run_id=None` means "applies to every run's
    firing under this finding_key", the common case (the same compound recurs run to run)."""

    finding_key: str
    disposition: str
    ts: str = field(default_factory=_utcnow_iso)
    run_id: str | None = None
    note: str = ""
    by: str = ""
    kind: str = "disposition"
    schema_version: int = SCHEMA_VERSION
    detector: str = DETECTOR

    def __post_init__(self):
        if self.disposition not in VALID_DISPOSITIONS:
            raise RecordError(f"disposition {self.disposition!r} not in {VALID_DISPOSITIONS}")
        if not self.finding_key:
            raise RecordError("finding_key is required")
        object.__setattr__(self, "note", _truncate(self.note, MAX_DETAIL))


def append_records(records: list) -> int:
    """Append one JSON line per record, in order. Never called with zero records by the
    detector's own run path (nothing to write when nothing fired) but tolerates it here."""
    if not records:
        return 0
    FIRINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FIRINGS_PATH, "a", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")
    return len(records)


def record_class1_run(ranked: list, mode: str) -> int:
    """Build + append one FiringRecord per CLASS-1 fired candidate -- the caller passes the
    FULL ranked list, every candidate any angle fired on, not a top-K/--dump-all-scoped slice
    (see this module's docstring, "WHY NOT BOUND TO THE PRINTED TOP-K"). `rank` is the 1-based
    position within `ranked` (the score-sorted order), which may run into five figures on a
    bare invocation. Unconditional: called once per cmd_class1 invocation, no flag to skip."""
    run_id, run_ts = new_run_id(), _utcnow_iso()
    git_hash, dirty = corpus_git_hash()
    records = []
    for i, r in enumerate(ranked, 1):
        angles = ",".join(sorted(r["angles"].keys()))
        detail = (f"{r['pair']!r} x{r['count']} in {r['docs']} doc(s); "
                  + ",".join(f"{k}={v}" for k, v in sorted(r["angles"].items())))
        records.append(FiringRecord(
            run_id=run_id, run_ts=run_ts, git_hash=git_hash, git_dirty=dirty,
            defect_class="class1", mode=mode, finding_key=f"class1:{r['pair']}",
            rule=angles, rank=i, score=r["score"], sites=r.get("sites", []), detail=detail,
        ))
    return append_records(records)


def record_class2_run(findings: list) -> int:
    """Build + append one FiringRecord per CLASS-2 flagged table (every entry in `findings`
    carries at least one hit -- scan_class2 only appends when `rec["hits"]` is non-empty).
    Unconditional: called once per cmd_tables invocation, no flag to skip."""
    run_id, run_ts = new_run_id(), _utcnow_iso()
    git_hash, dirty = corpus_git_hash()
    records = []
    for r in findings:
        angles = ",".join(sorted({a for a, _msg, _s in r["hits"]}))
        detail = "; ".join(f"[{a}] {msg}" for a, msg, _s in r["hits"][:2])
        records.append(FiringRecord(
            run_id=run_id, run_ts=run_ts, git_hash=git_hash, git_dirty=dirty,
            defect_class="class2", mode="tables", finding_key=f"class2:{r['doc']}:{r['header']}",
            rule=angles, rank=len(records) + 1, score=r["score"],
            sites=[f"{r['doc']}:{r['line']}"], detail=detail,
        ))
    return append_records(records)


def validate_record(rec: dict) -> list:
    """Schema check over one already-parsed jsonl line. Returns a list of violation strings
    (empty == valid). The one home of the schema (P1) -- gates/scan2_firing_schema.py imports
    this rather than re-deriving it."""
    errs = []
    kind = rec.get("kind")
    if kind not in ("firing", "disposition"):
        errs.append(f"kind {kind!r} not in ('firing', 'disposition')")
        return errs  # nothing else is checkable without a known kind
    if rec.get("schema_version") != SCHEMA_VERSION:
        errs.append(f"schema_version {rec.get('schema_version')!r} != {SCHEMA_VERSION}")
    if not rec.get("detector"):
        errs.append("detector is required")
    if kind == "firing":
        if rec.get("defect_class") not in VALID_CLASSES:
            errs.append(f"defect_class {rec.get('defect_class')!r} not in {VALID_CLASSES}")
        for field_name in ("run_id", "run_ts", "git_hash", "finding_key", "rule"):
            if not rec.get(field_name):
                errs.append(f"{field_name} is required on a firing record")
        if not isinstance(rec.get("git_dirty"), bool):
            errs.append(f"git_dirty must be a bool, got {rec.get('git_dirty')!r}")
        rank = rec.get("rank")
        if not isinstance(rank, int) or rank < 1:
            errs.append(f"rank must be an int >= 1, got {rank!r}")
        score = rec.get("score")
        if not isinstance(score, (int, float)):
            errs.append(f"score must be numeric, got {score!r}")
        sites = rec.get("sites")
        if not isinstance(sites, list) or len(sites) > MAX_SITES:
            errs.append(f"sites must be a list of at most {MAX_SITES}, got {sites!r}")
        disp = rec.get("disposition")
        if disp is not None:
            errs.append(f"a firing record must carry disposition=null, got {disp!r} "
                        "(disposition is a separate, later-appended record)")
    else:  # disposition
        if not rec.get("finding_key"):
            errs.append("finding_key is required on a disposition record")
        if rec.get("disposition") not in VALID_DISPOSITIONS:
            errs.append(f"disposition {rec.get('disposition')!r} not in {VALID_DISPOSITIONS}")
    return errs


def cmd_triage(args: argparse.Namespace) -> int:
    try:
        rec = DispositionRecord(finding_key=args.finding_key, disposition=args.disposition,
                                run_id=args.run, note=args.note or "", by=args.by or "")
    except RecordError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 1
    append_records([rec])
    scope = f"run {args.run}" if args.run else "every run"
    print(f"triaged {args.finding_key!r} -> {args.disposition} ({scope})")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    tri = sub.add_parser("triage", help="backfill a human disposition for a finding_key")
    tri.add_argument("finding_key")
    tri.add_argument("disposition", choices=sorted(VALID_DISPOSITIONS))
    tri.add_argument("--run", help="scope the verdict to one run_id (default: every run)")
    tri.add_argument("--note", help="free-text triage note (capped at %d chars)" % MAX_DETAIL)
    tri.add_argument("--by", help="who triaged it")
    args = ap.parse_args(argv)
    if args.cmd == "triage":
        return cmd_triage(args)
    return 1  # argparse's `required=True` makes this unreachable; kept as an honest default


if __name__ == "__main__":
    sys.exit(main())
