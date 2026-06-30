#!/usr/bin/env python
"""End-to-end contradiction-detection runner — the REAL pipeline, reversibly.

    text
      -> extract.build_nlp / doc_to_facts        (REUSED extractor, no re-parse)
      -> contra_detect.claims_from_bundle        (pure function of the FactBundle)
      -> contra_detect.find_contradictions       (R-NEG / R-FUNC / R-NUM)
      -> ContraStore.insert_findings             (contra.finding, ON CONFLICT DO NOTHING)
      -> loaders.contra_finding_tasks            (rows -> BATCH Task)
      -> HeadlessFrontend(RulePolicy).adjudicate (REUSED decision seam, verbatim)
      -> ContraStore.persist                     (contra.adjudication)
      -> contra.review                           (read back, print)

Modes:
  --synthetic                 the committed planted fixture (proves detection FIRES)
  --rfc PATH                  a real ~/distill RFC (proves the pipeline RUNS on real text)
  --ephemeral-claude          OPTIONAL stretch: ~/.claude assistant turns, STDOUT-ONLY,
                              redacted, writes NOTHING to the DB / any file

Rewind the whole store:  DROP SCHEMA contra CASCADE;

This runner lives on the fact-mining side because it imports the heavy spaCy extractor
and the one-home DSN (spans.DEFAULT_DSN); it reaches the adjudicate package (the decision
seam + ContraStore) over sys.path. The cross-package coupling between detector and
adjudicator is the contra.finding ROWS, not a Python import."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

import contra_detect as cd
import extract
from spans import DEFAULT_DSN

# reach the adjudicate package (the REUSED decision surface + the new ContraStore)
_ADJ = str(Path(__file__).resolve().parent.parent / "adjudicate")
if _ADJ not in sys.path:
    sys.path.insert(0, _ADJ)

import instances as inst          # noqa: E402
from contra_store import ContraStore  # noqa: E402
from frontend_headless import HeadlessFrontend, RulePolicy  # noqa: E402
from loaders import contra_finding_tasks  # noqa: E402


# --------------------------------------------------------------- detection helpers
def _claims_from_paragraphs(nlp: object, paragraphs: list[str]) -> list[cd.Claim]:
    """Parse each paragraph (REUSED extractor) and merge its claims. Merging across
    paragraphs lets the rules see cross-paragraph clashes too; grounding stays per-claim
    (the source sentence is carried on the Claim)."""
    claims: list[cd.Claim] = []
    for doc in nlp.pipe(paragraphs):  # type: ignore[attr-defined]
        claims.extend(cd.claims_from_bundle(extract.doc_to_facts(doc)))
    return claims


def _print_findings(findings: list[cd.Finding]) -> None:
    if not findings:
        print("  (no findings)")
        return
    for f in findings:
        print(f"  [{f.rule}] subject={f.subj_key!r} predicate={f.pred!r}")
        print(f"      A: {f.claim_a}")
        print(f"      B: {f.claim_b}")
        print(f"      grounding: {f.grounding}")


def _adjudicate_and_persist(source_doc: str, findings: list[cd.Finding], dsn: str) -> None:
    """The persisted half: write findings, build tasks, drive the REUSED
    HeadlessFrontend(RulePolicy) over the contradiction schema, persist verdicts, and
    print the contra.review rows."""
    schema = inst.contradiction_schema()
    store = ContraStore(dsn=dsn, adjudicator="rule:auto")
    store.ensure_schema(schema)

    n_new = store.insert_findings(source_doc, [f.as_row() for f in findings])
    print(f"  contra.finding: {n_new} new row(s) inserted "
          f"(idempotent ON CONFLICT DO NOTHING; total for this doc: {len(store.findings(source_doc))})")

    tasks = contra_finding_tasks(schema, store, source_doc)
    frontend = HeadlessFrontend(RulePolicy(inst.CONTRA_SUGGESTED))
    adjudications = frontend.adjudicate(schema, tasks)

    by_task = {t.task_id: t for t in tasks}
    for adj in adjudications:
        store.persist(schema, by_task[adj.task_id], [adj])
    print(f"  contra.adjudication: {len(adjudications)} verdict(s) written "
          f"(adjudicator=rule:auto, via HeadlessFrontend(RulePolicy))")


def run_synthetic(dsn: str) -> None:
    fixture = Path(__file__).parent / "fixtures" / "contra_synthetic.txt"
    print(f"=== SYNTHETIC fixture: {fixture} ===")
    nlp = extract.load_model("en_core_web_sm")
    claims = _claims_from_paragraphs(nlp, [fixture.read_text(encoding="utf-8")])
    findings = cd.find_contradictions(claims)
    print(f"claims extracted: {len(claims)}; findings: {len(findings)}")
    _print_findings(findings)
    source_doc = "synthetic:contra_synthetic.txt"
    _adjudicate_and_persist(source_doc, findings, dsn)


def run_rfc(path: str, max_paras: int, dsn: str) -> None:
    print(f"=== REAL doc: {path} (max-paras={max_paras}) ===")
    body = extract.normalise(extract.load_body(path, None))
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()][:max_paras]
    nlp = extract.load_model("en_core_web_sm")
    claims = _claims_from_paragraphs(nlp, paragraphs)
    findings = cd.find_contradictions(claims)
    by_rule: dict[str, int] = {}
    for f in findings:
        by_rule[f.rule] = by_rule.get(f.rule, 0) + 1
    print(f"paragraphs parsed: {len(paragraphs)}; claims extracted: {len(claims)}; "
          f"findings: {len(findings)} by-rule={by_rule or '{}'}")
    _print_findings(findings)
    source_doc = f"rfc:{Path(path).name}"
    _adjudicate_and_persist(source_doc, findings, dsn)


# ---------------------------------------------- ephemeral .claude stretch (no DB) --
# secret/PII scrub applied BEFORE any display. Commits nothing, writes nothing.
_SCRUB = [
    (re.compile(r"host=\S+|dbname=\S+|postgres(?:ql)?://\S+"), "<DSN>"),
    (re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"), "<IP>"),
    (re.compile(r"sk-[A-Za-z0-9_\-]{8,}|gh[pousr]_[A-Za-z0-9]{8,}|xox[baprs]-[A-Za-z0-9-]+"), "<TOKEN>"),
    (re.compile(r"/(?:home|Users|root)/[^\s\"']+"), "<PATH>"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "<EMAIL>"),
]


def _scrub(text: str) -> str:
    for pat, repl in _SCRUB:
        text = pat.sub(repl, text)
    return text


def _assistant_texts(path: Path) -> Iterable[str]:
    """Yield assistant-turn text blocks from a .claude transcript jsonl (best-effort)."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            ev = json.loads(ln)
        except json.JSONDecodeError:
            continue
        if not isinstance(ev, dict) or ev.get("type") != "assistant":
            continue
        msg = ev.get("message")
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if isinstance(content, str):
            yield content
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    t = block.get("text")
                    if isinstance(t, str):
                        yield t


def run_ephemeral_claude(max_files: int, max_examples: int) -> None:
    """EPHEMERAL: detect self-contradictions across an AI collaborator's own assistant
    turns. STDOUT ONLY — never writes contra.finding / the DB / any file. Aggregate
    counts + a few REDACTED examples; commits nothing private."""
    root = Path.home() / ".claude" / "projects"
    print(f"=== EPHEMERAL .claude stretch (stdout-only, redacted): {root} ===")
    if not root.exists():
        print("  (no ~/.claude/projects directory — skipped)")
        return
    nlp = extract.load_model("en_core_web_sm")
    files = sorted(root.rglob("*.jsonl"))[:max_files]
    n_files = n_turns = n_claims = n_find = 0
    by_rule: dict[str, int] = {}
    examples: list[cd.Finding] = []
    for fp in files:
        texts = [t for t in _assistant_texts(fp) if t.strip()]
        if not texts:
            continue
        n_files += 1
        n_turns += len(texts)
        # parse each assistant turn as its own doc; merge claims per session (one file)
        claims: list[cd.Claim] = []
        for doc in nlp.pipe(texts):  # type: ignore[attr-defined]
            claims.extend(cd.claims_from_bundle(extract.doc_to_facts(doc)))
        n_claims += len(claims)
        findings = cd.find_contradictions(claims)
        n_find += len(findings)
        for f in findings:
            by_rule[f.rule] = by_rule.get(f.rule, 0) + 1
            if len(examples) < max_examples:
                examples.append(f)
    print(f"  files scanned: {n_files}; assistant turns: {n_turns}; "
          f"claims extracted: {n_claims}; candidate findings: {n_find} by-rule={by_rule or '{}'}")
    print(f"  up to {max_examples} REDACTED candidate self-contradiction(s):")
    if not examples:
        print("    (none)")
    for f in examples[:max_examples]:
        print(f"    [{f.rule}] subject={_scrub(f.subj_key)!r} predicate={f.pred!r}")
        print(f"        A: {_scrub(f.claim_a)}")
        print(f"        B: {_scrub(f.claim_b)}")
        print(f"        grounding: {_scrub(f.grounding)}")
    print("  (ephemeral: nothing written to contra.* / the DB / any file)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--synthetic", action="store_true", help="run the planted fixture")
    ap.add_argument("--rfc", metavar="PATH", default=None, help="run a real RFC doc")
    ap.add_argument("--max-paras", type=int, default=200, help="paragraph cap for --rfc")
    ap.add_argument("--ephemeral-claude", action="store_true",
                    help="OPTIONAL stretch: ~/.claude assistant turns, stdout-only")
    ap.add_argument("--max-files", type=int, default=40, help="file cap for --ephemeral-claude")
    ap.add_argument("--max-examples", type=int, default=3, help="redacted examples to print")
    ap.add_argument("--dsn", default=DEFAULT_DSN, help="harness DSN (default: spans.DEFAULT_DSN)")
    args = ap.parse_args()

    ran = False
    if args.synthetic:
        run_synthetic(args.dsn)
        ran = True
    if args.rfc:
        run_rfc(args.rfc, args.max_paras, args.dsn)
        ran = True
    if args.ephemeral_claude:
        run_ephemeral_claude(args.max_files, args.max_examples)
        ran = True
    if not ran:
        run_synthetic(args.dsn)  # default mode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
