"""demurral_eval — the ADR-0013 Rule 3 demurral-detector's regression harness (BACKLOG "Proposed:
mechanize the ADR-0013 Rule 3 demurral-detector as a Claude hook", 2026-07-09, Part 2/3).

Runs `hooks/demurral_detect.py`'s classifier (the EXACT SAME `build_classifier_prompt` /
`classify_text` the deployed hook calls — no separately-tuned proxy) over the eval corpus
(`instruments/demurral_corpus.jsonl`, built by the offline loop-until-dry adversarial procedure)
and reports precision/recall/F1 per class, plus a confusion matrix.

TWO READINGS ARE REPORTED, ON PURPOSE, because they answer different questions:

  RAW  — classifier accuracy over rows the classifier actually answered (VERDICT parsed,
         no timeout/subprocess failure). This is "how good is the prompt", isolated from
         infrastructure flakiness.

  EFFECTIVE — the number that matters operationally, because hooks/demurral_detect.py is
         FAIL-OPEN (a named choice, see its module docstring): a classifier ERROR (timeout,
         launch failure, unparsed reply) behaves EXACTLY like a NEGATIVE verdict in
         production — no warning ever fires. So an ERROR on a ground-truth POSITIVE row is
         folded into EFFECTIVE as a missed detection (a false negative), and an ERROR on a
         ground-truth NEGATIVE row is folded in as a (silently) correct negative. EFFECTIVE
         is therefore always <= RAW recall on the positive class, and is the honest
         "what does a live session actually get warned about" number.

THE ACCURACY NUMBERS BELOW ARE THE DETECTOR'S HONEST STRENGTH CLAIM (ADR-0013 Rule 3's own
text: "the weakest-enforced and most-violated rule in the tenet, because it is enforced by the
faculty it most reliably corrupts" — a small-model classifier is a real backstop, not a proof).
GOODHARTING RISK (BACKLOG's own caveat): a fixed classifier prompt is a target the attrition
reflex can eventually learn to slip past. The adversarial loop-until-dry corpus-building
procedure (this same BACKLOG entry) is meant to be RE-RUN against every new PROMPT_VERSION in
hooks/demurral_detect.py, not run once and trusted forever — a stale eval number laundered as
a current one is exactly the false-clear shape ADR-0013's 2026-07-02 amendment (Rule 5) warns
against. Re-run this harness (and, before that, the corpus-building loop) whenever
PROMPT_VERSION changes.

Usage:
    python3 instruments/demurral_eval.py [--concurrency N] [--timeout SECONDS] [--rounds 1,2,3]

Exit 0 always (this is a report, not a gate — promotion of any pass/fail threshold into a CI
gate is a maintainer act like the hook's own promotion to enforcing, not this file's to decide).

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below is imported at module load.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)  # instruments/ -> autoharn root
sys.path.insert(0, os.path.join(_REPO_ROOT, "hooks"))
import demurral_detect as dd  # noqa: E402  (hooks/demurral_detect.py — the ONE home for the classifier)

CORPUS_PATH = os.path.join(_REPO_ROOT, "instruments", "demurral_corpus.jsonl")


@dataclass
class Row:
    text: str
    label: str
    source_round: int
    verdict: str
    reason: str


def load_corpus(path: str, rounds: set[int] | None) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rounds is not None and rec.get("source_round") not in rounds:
                continue
            rows.append(rec)
    return rows


def classify_all(rows: list[dict], concurrency: int, timeout: float) -> list[Row]:
    out: list[Row] = [None] * len(rows)  # type: ignore[list-item]

    def _one(i: int, rec: dict) -> tuple[int, Row]:
        r = dd.classify_text(rec["text"], timeout=timeout)
        return i, Row(rec["text"], rec["label"], rec["source_round"], r.verdict, r.reason)

    with cf.ThreadPoolExecutor(max_workers=concurrency) as ex:
        futs = [ex.submit(_one, i, rec) for i, rec in enumerate(rows)]
        for fut in cf.as_completed(futs):
            i, row = fut.result()
            out[i] = row
    return out


def _prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) and precision == precision and recall == recall and (precision + recall) > 0
          else float("nan"))
    return precision, recall, f1


def report(rows: list[Row]) -> str:
    lines = []
    n = len(rows)
    errors = [r for r in rows if r.verdict == "ERROR"]
    answered = [r for r in rows if r.verdict != "ERROR"]

    lines.append(f"demurral_eval — corpus n={n}, prompt_version={dd.PROMPT_VERSION}, "
                 f"model={dd.CLASSIFIER_MODEL}")
    lines.append(f"  answered={len(answered)}  classifier errors/timeouts={len(errors)}")
    lines.append("")

    # --- RAW: classifier accuracy over answered rows only ---
    tp = sum(1 for r in answered if r.label == "POSITIVE" and r.verdict == "POSITIVE")
    fn = sum(1 for r in answered if r.label == "POSITIVE" and r.verdict == "NEGATIVE")
    fp = sum(1 for r in answered if r.label == "NEGATIVE" and r.verdict == "POSITIVE")
    tn = sum(1 for r in answered if r.label == "NEGATIVE" and r.verdict == "NEGATIVE")
    p, r_, f1 = _prf(tp, fp, fn)
    acc = (tp + tn) / len(answered) if answered else float("nan")
    lines.append("RAW (classifier-only, excludes ERROR rows):")
    lines.append(f"  confusion: TP={tp} FN={fn} FP={fp} TN={tn}")
    lines.append(f"  POSITIVE class: precision={p:.3f} recall={r_:.3f} f1={f1:.3f}")
    lines.append(f"  overall accuracy={acc:.3f}")
    lines.append("")

    # --- EFFECTIVE: fold ERROR in as fail-open (behaves like a NEGATIVE verdict in production) ---
    e_tp = sum(1 for r in rows if r.label == "POSITIVE" and r.verdict == "POSITIVE")
    e_fn = sum(1 for r in rows if r.label == "POSITIVE" and r.verdict != "POSITIVE")  # NEGATIVE or ERROR
    e_fp = sum(1 for r in rows if r.label == "NEGATIVE" and r.verdict == "POSITIVE")
    e_tn = sum(1 for r in rows if r.label == "NEGATIVE" and r.verdict != "POSITIVE")  # NEGATIVE or ERROR
    ep, er, ef1 = _prf(e_tp, e_fp, e_fn)
    eacc = (e_tp + e_tn) / n if n else float("nan")
    lines.append("EFFECTIVE (ERROR folded in as fail-open, i.e. as a NEGATIVE verdict — the "
                 "hook's real production behavior):")
    lines.append(f"  confusion: TP={e_tp} FN={e_fn} FP={e_fp} TN={e_tn}")
    lines.append(f"  POSITIVE class: precision={ep:.3f} recall={er:.3f} f1={ef1:.3f}")
    lines.append(f"  overall accuracy={eacc:.3f}")
    lines.append("")

    by_round: dict[int, Counter] = {}
    for r in rows:
        by_round.setdefault(r.source_round, Counter())["n"] += 1
        by_round[r.source_round][("ok" if r.verdict == r.label else
                                    ("error" if r.verdict == "ERROR" else "miss"))] += 1
    lines.append("Per-round breakdown (n / ok / miss / error):")
    for rnd in sorted(by_round):
        c = by_round[rnd]
        lines.append(f"  round {rnd}: n={c['n']} ok={c['ok']} miss={c['miss']} error={c['error']}")
    lines.append("")

    misses = [r for r in answered if r.verdict != r.label]
    if misses:
        lines.append(f"Misclassified rows ({len(misses)}):")
        for r in misses:
            lines.append(f"  gold={r.label} got={r.verdict} reason={r.reason!r}")
            lines.append(f"    text={r.text[:180]!r}")
    if errors:
        lines.append(f"Errored rows ({len(errors)}):")
        for r in errors:
            lines.append(f"  gold={r.label} reason={r.reason!r}")
            lines.append(f"    text={r.text[:180]!r}")

    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--concurrency", type=int, default=4,
                    help="parallel classifier subprocesses (default 4 — higher counts were "
                         "observed to trigger CLI-level timeouts during corpus-building)")
    ap.add_argument("--timeout", type=float, default=30.0,
                    help="per-call classifier timeout in seconds (default 30s for this offline "
                         "harness; the deployed hook itself uses CLASSIFIER_TIMEOUT_S=10s)")
    ap.add_argument("--rounds", type=str, default=None,
                    help="comma-separated source_round values to restrict to (default: all)")
    ap.add_argument("--corpus", type=str, default=CORPUS_PATH)
    args = ap.parse_args()

    rounds = set(int(x) for x in args.rounds.split(",")) if args.rounds else None
    rows = load_corpus(args.corpus, rounds)
    if not rows:
        print("demurral_eval: corpus is empty (or --rounds filtered everything out) — nothing to report.")
        return 0

    classified = classify_all(rows, args.concurrency, args.timeout)
    print(report(classified))
    return 0


if __name__ == "__main__":
    sys.exit(main())
