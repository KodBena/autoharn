#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T15:17:21Z
#   last-change: 2026-07-11T15:17:21Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""doc_critic_eval — regression harness for the zero-context-reader critic
(hooks/doc_legibility_critic.py; design/ADR-DRAFT-documentation-discipline.md instance
bindings). Mirrors instruments/demurral_eval.py: it runs the critic's OWN classifier (the
exact same `build_critic_prompt` / `critique_text` the deployed hook calls — no
separately-tuned proxy) over the eval corpus (instruments/doc_legibility_corpus.jsonl) and
reports precision/recall/F1 on the DEFECT class, plus a confusion matrix.

THE CORPUS IS REAL, BOTH-POLARITY, AND IN-REPO: every DEFECT row is a passage the discipline's
provenance names (the safety-critical-logging BRIEF's staccato, the three maintainer-hit
morning defects in their pre-fix `48dce0c^` state, the in-house fragments the doc_shapes
measurement pass found); every CLEAN row is a passage the maintainer reads clean (accepted
fixes from `48dce0c`, ADR prose, glossary entries) including deliberate HARD NEGATIVES (dense
but fully resolvable text — the failure mode to defend against is a critic that punishes
density instead of unresolvability). Small n (24) is a starter corpus, said plainly; it grows
from adjudicated live findings, and the number reported here travels with PROMPT_VERSION —
a stale number is treated as no number.

TWO READINGS, same rationale as the demurral harness:
  RAW       — accuracy over rows the classifier actually answered (the prompt's ceiling).
  EFFECTIVE — ERROR rows folded in as fail-open (the hook's production behavior: an ERROR
              on a gold-DEFECT row is a missed detection; on a gold-CLEAN row a silently
              correct pass). The honest "what does a live session get warned about" number.

Also reported, informationally (not scored): whether the predicted shape of a caught DEFECT
matches the gold shape — shape agreement is diagnostic, the verdict is what the hook acts on.

Usage:
    python3 instruments/doc_critic_eval.py [--concurrency N] [--timeout SECONDS]

Exit 0 always (a report, not a gate — any promotion of a threshold into CI is a maintainer
act). Lazy imports are banned (CLAUDE.md, 2026-07-02).
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import sys
from dataclasses import dataclass

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)  # instruments/ -> autoharn root
sys.path.insert(0, os.path.join(_REPO_ROOT, "hooks"))
import doc_legibility_critic as dc  # noqa: E402  (the ONE home for the critic machinery)

CORPUS_PATH = os.path.join(_REPO_ROOT, "instruments", "doc_legibility_corpus.jsonl")


@dataclass
class Row:
    rec: dict
    verdict: str          # DEFECT | CLEAN | ERROR
    shapes: list[str]     # predicted shapes (when DEFECT)
    error: str


def load_corpus(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def critique_all(rows: list[dict], concurrency: int, timeout: float) -> list[Row]:
    out: list[Row] = [None] * len(rows)  # type: ignore[list-item]

    def _one(i: int, rec: dict) -> tuple[int, Row]:
        r = dc.critique_text(rec["text"], timeout=timeout)
        return i, Row(rec, r.verdict, [f["shape"] for f in r.findings], r.error)

    with cf.ThreadPoolExecutor(max_workers=concurrency) as ex:
        futs = [ex.submit(_one, i, rec) for i, rec in enumerate(rows)]
        for fut in cf.as_completed(futs):
            i, row = fut.result()
            out[i] = row
    return out


def prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if (tp + fp) else float("nan")
    r = tp / (tp + fn) if (tp + fn) else float("nan")
    f1 = 2 * p * r / (p + r) if (p == p and r == r and (p + r) > 0) else float("nan")
    return p, r, f1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--timeout", type=float, default=60.0,
                    help="per-call allowance; the deployed hook's default is tighter, which "
                         "is exactly what EFFECTIVE vs RAW makes visible")
    args = ap.parse_args()

    corpus = load_corpus(CORPUS_PATH)
    results = critique_all(corpus, args.concurrency, args.timeout)

    n = len(results)
    errors = [r for r in results if r.verdict == "ERROR"]
    answered = [r for r in results if r.verdict != "ERROR"]

    # RAW: answered rows only.
    tp = sum(1 for r in answered if r.rec["label"] == "DEFECT" and r.verdict == "DEFECT")
    fn = sum(1 for r in answered if r.rec["label"] == "DEFECT" and r.verdict == "CLEAN")
    fp = sum(1 for r in answered if r.rec["label"] == "CLEAN" and r.verdict == "DEFECT")
    tn = sum(1 for r in answered if r.rec["label"] == "CLEAN" and r.verdict == "CLEAN")
    p, r_, f1 = prf(tp, fp, fn)

    # EFFECTIVE: ERROR folds in as fail-open (a CLEAN-equivalent verdict in production).
    etp, efp = tp, fp
    efn = fn + sum(1 for r in errors if r.rec["label"] == "DEFECT")
    etn = tn + sum(1 for r in errors if r.rec["label"] == "CLEAN")
    ep, er, ef1 = prf(etp, efp, efn)

    shape_match = sum(1 for r in answered
                      if r.rec["label"] == "DEFECT" and r.verdict == "DEFECT"
                      and r.rec.get("shape") in r.shapes)

    print(f"doc_critic_eval — corpus n={n}, prompt_version={dc.PROMPT_VERSION}, "
          f"model={dc.CLASSIFIER_MODEL}")
    print(f"  answered={len(answered)}  classifier errors/timeouts={len(errors)}")
    print()
    print("RAW (classifier-only, excludes ERROR rows):")
    print(f"  confusion: TP={tp} FN={fn} FP={fp} TN={tn}")
    print(f"  DEFECT class: precision={p:.3f} recall={r_:.3f} f1={f1:.3f}")
    print()
    print("EFFECTIVE (ERROR folded in as fail-open — the hook's real production behavior):")
    print(f"  confusion: TP={etp} FN={efn} FP={efp} TN={etn}")
    print(f"  DEFECT class: precision={ep:.3f} recall={er:.3f} f1={ef1:.3f}")
    print()
    print(f"Shape agreement on caught defects (informational): {shape_match}/{tp}")
    mis = [r for r in answered
           if (r.rec["label"] == "DEFECT") != (r.verdict == "DEFECT")]
    if mis or errors:
        print()
        print(f"Misclassified rows ({len(mis)}):")
        for r in mis:
            print(f"  gold={r.rec['label']} got={r.verdict} id={r.rec['id']} "
                  f"shapes={r.shapes}")
        if errors:
            print(f"ERROR rows ({len(errors)}): " + ", ".join(r.rec["id"] for r in errors))
    return 0


if __name__ == "__main__":
    sys.exit(main())
