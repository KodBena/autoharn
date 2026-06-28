#!/usr/bin/env python
"""First spaCy fact-mining pass over a Project Gutenberg plain-text book.

Goal of THIS script: prove the pipeline runs and show, concretely, what raw
material spaCy hands us to turn into *facts in different logics* (Pillar 3).

It is deliberately a sketch, not a product. It extracts three families of
candidate facts, each of which lands naturally in a different logic:

  1. SVO triples   (subject -> predicate -> object) via the dependency parse.
                   -> the atoms of a classical/relational fact base: pred(s, o).
  2. Named entities (PERSON, GPE, DATE, ORG, ...) via NER.
                   -> the constants/sorts those atoms range over.
  3. Temporal cues (DATE/TIME entities + the sentence they sit in).
                   -> the raw material for a temporal logic (valid-time facts).

Nothing here commits to a logic yet; it surfaces the candidates so we can see
the shape of the signal before designing the encoder.

Usage:
    python extract.py /home/bork/pg/pg78966.txt              # default sample
    python extract.py /home/bork/pg/pg78966.txt --max-sents 400
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass

import spacy

# --- model catalogue ----------------------------------------------------------
# Pipelines we know how to fetch. `trf` requires the `spacy-transformers` extra
# and torch (already present as a CPU build); the rest are CNN pipelines that
# run fast on CPU. Sizes are approximate download sizes.
MODELS = {
    "en_core_web_sm":  "~12 MB  CNN, no vectors. Fast. Noisy NER. (default)",
    "en_core_web_md":  "~40 MB  CNN + 20k word vectors. Same speed as sm.",
    "en_core_web_lg":  "~560 MB CNN + 514k word vectors. Still CPU-fast.",
    "en_core_web_trf": "~440 MB RoBERTa transformer. Best accuracy. CPU-OK but ~5-15x slower; needs spacy-transformers.",
}


def model_help() -> str:
    lines = ["available models (install with: python -m spacy download <name>):"]
    for name, desc in MODELS.items():
        lines.append(f"  {name:18} {desc}")
    return "\n".join(lines)


def load_model(name: str):
    try:
        return spacy.load(name)
    except OSError:
        hint = "python -m spacy download " + name
        if name == "en_core_web_trf":
            hint = "pip install spacy-transformers && " + hint
        print(f"model {name!r} is not installed. Install it with:\n    {hint}",
              file=sys.stderr)
        raise SystemExit(2)

# --- Gutenberg boilerplate stripping -----------------------------------------

START_RE = re.compile(r"\*\*\* ?START OF .*?\*\*\*", re.S)
END_RE = re.compile(r"\*\*\* ?END OF .*?\*\*\*", re.S)


def load_body(path: str, body_start_line: int | None) -> str:
    """Return the narrative body with PG header/footer removed.

    If body_start_line is given (1-based), prefer it: it lets us skip the long
    table-of-contents / list-of-figures front matter, which is not prose and
    only produces parser noise.
    """
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()

    text = "".join(lines)
    m = END_RE.search(text)
    if m:
        text = text[: m.start()]

    if body_start_line is not None:
        return "".join(lines[body_start_line - 1 :])

    m = START_RE.search(text)
    if m:
        text = text[m.end() :]
    return text


def normalise(text: str) -> str:
    """Light cleanup so paragraphs survive sentence segmentation.

    PG wraps prose at ~70 cols; we join intra-paragraph line breaks (single
    newline) but keep paragraph breaks (blank line). We also drop [Illustration]
    blocks and lines that are clearly front-matter table rows (dot leaders /
    trailing page numbers).
    """
    text = re.sub(r"\[Illustration:.*?\]", " ", text, flags=re.S)
    # drop table-of-contents / figure-list rows: text ... <pagenum>
    cleaned = []
    for ln in text.splitlines():
        if re.search(r"\s{2,}\d{1,4}\s*$", ln):  # trailing page number
            continue
        cleaned.append(ln)
    text = "\n".join(cleaned)
    # collapse single newlines inside paragraphs, keep blank-line breaks
    text = re.sub(r"\n{2,}", " ", text)  # paragraph sep placeholder
    text = re.sub(r"\s*\n\s*", " ", text)
    text = text.replace(" ", "\n\n")
    return text


# --- fact extraction ----------------------------------------------------------


@dataclass
class Triple:
    subj: str           # human-readable phrase (subtree)
    pred: str
    obj: str
    negated: bool
    sent: str
    subj_key: str = ""  # canonical constant the logics join on (coref/entity-resolved)
    obj_key: str = ""
    sent_i: int = 0     # sentence index within the doc (for provenance grouping)


def subtree_span(token):
    """Compact text for a token's subtree (the phrase it heads)."""
    words = sorted(token.subtree, key=lambda t: t.i)
    return " ".join(w.text for w in words)


def _default_key(token):
    return token.lemma_.lower()


def extract_triples(doc, key_fn=None):
    """Very simple SVO extraction off the dependency parse.

    For each verb, pair its nominal subject(s) with its direct object / attribute
    / prepositional complement. This is intentionally shallow — it misses a lot —
    but it shows the relational atoms spaCy makes available.

    `key_fn(token) -> str` maps a subject/object head token to its canonical
    constant (coref- and entity-resolved); defaults to the head lemma. Pass the
    resolver from resolve.py to get joinable constants.
    """
    key_fn = key_fn or _default_key
    triples = []
    for si, sent in enumerate(doc.sents):
        for tok in sent:
            if tok.pos_ not in ("VERB", "AUX"):
                continue
            subjs = [c for c in tok.children if c.dep_ in ("nsubj", "nsubjpass")]
            objs = [c for c in tok.children if c.dep_ in ("dobj", "attr", "oprd", "dative")]
            # prepositional objects: verb -> prep -> pobj
            for prep in (c for c in tok.children if c.dep_ == "prep"):
                for pobj in (g for g in prep.children if g.dep_ == "pobj"):
                    objs.append(pobj)
            if not subjs or not objs:
                continue
            negated = any(c.dep_ == "neg" for c in tok.children)
            pred = tok.lemma_
            for s in subjs:
                for o in objs:
                    triples.append(
                        Triple(
                            subj=subtree_span(s),
                            pred=pred,
                            obj=subtree_span(o),
                            negated=negated,
                            sent=sent.text.strip(),
                            subj_key=key_fn(s),
                            obj_key=key_fn(o),
                            sent_i=si,
                        )
                    )
    return triples


def build_nlp(model: str, remote: str | None, cache_url: str | None, verbose: bool = False):
    """Construct the parsing interface shared by extract.py and load_facts.py.

    Returns (nlp, model_label, cache). `nlp` exposes .pipe()/__call__ whether it
    is a local Language, a RemoteNLP daemon client, or either wrapped in a cache.
    `model_label` is the effective pipeline name (used for cache keys / provenance).
    """
    if remote:
        from nlp_client import RemoteNLP
        # pass model only if the user overrode the default, else let the daemon decide
        m = None if model == "en_core_web_sm" else model
        nlp = RemoteNLP(remote, model=m)
        model_label = m or nlp.info().get("default", "remote")
        if verbose:
            print(f"=== remote daemon: {remote} | info: {nlp.info()} ===")
    else:
        nlp = load_model(model)
        model_label = model
        if verbose:
            print(f"=== model: {nlp.meta['lang']}_{nlp.meta['name']} {nlp.meta['version']} "
                  f"| pipes: {nlp.pipe_names} ===")

    cache = None
    if cache_url:
        from nlp_cache import DocCache, CachingNLP
        cache = DocCache(model_label, url=cache_url)
        nlp = CachingNLP(nlp, cache)
        if verbose:
            print(f"=== cache: {cache_url} (model_label={model_label!r}) ===")
    return nlp, model_label, cache


def main() -> int:
    ap = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=model_help(),
    )
    ap.add_argument("path")
    ap.add_argument("--model", default="en_core_web_sm", metavar="NAME",
                    help="spaCy pipeline to load (see list below); default %(default)s")
    ap.add_argument("--remote", metavar="ADDR", default=None,
                    help="use the GPU daemon at ADDR (e.g. tcp://192.168.122.1:5599) "
                         "instead of loading a local model")
    ap.add_argument("--body-start-line", type=int, default=834,
                    help="1-based line where narrative prose begins (skips front matter)")
    ap.add_argument("--max-sents", type=int, default=120,
                    help="cap sentences processed, for a fast first look")
    ap.add_argument("--max-paras", type=int, default=40,
                    help="cap paragraphs fed to the parser (bounds work for a sample)")
    ap.add_argument("--cache", metavar="URL", nargs="?", const="redis://127.0.0.1:6380/0",
                    default=None,
                    help="cache parses in redis (default URL: the volatile 6380 instance). "
                         "On a hit, no parse/wire call is made.")
    args = ap.parse_args()

    body = normalise(load_body(args.path, args.body_start_line))

    nlp, model_label, cache = build_nlp(args.model, args.remote, args.cache, verbose=True)

    # parse per-paragraph: bounds work for a sample and gives the cache a
    # reusable granularity (one key per paragraph, not one per whole book).
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()][: args.max_paras]
    docs = nlp.pipe(paragraphs)

    # collect sentences across paragraphs up to the sample budget
    triples, ents, dates = [], [], []
    n_sents = 0
    for doc in docs:
        for sent in doc.sents:
            if n_sents >= args.max_sents:
                break
            span = sent.as_doc()
            triples.extend(extract_triples(span))
            ents.extend((e.text, e.label_) for e in span.ents)
            dates.extend(e for e in span.ents if e.label_ in ("DATE", "TIME"))
            n_sents += 1
        if n_sents >= args.max_sents:
            break

    print(f"=== sample: {n_sents} sentences from {len(paragraphs)} paragraphs ===")
    if cache:
        print(f"=== cache stats: {cache.stats()} ===")
    print()

    print(f"--- SVO candidate triples ({len(triples)}) -> classical fact base ---")
    for t in triples[:25]:
        neg = "NOT " if t.negated else ""
        print(f"  ({t.subj!r}, {neg}{t.pred!r}, {t.obj!r})")
    if len(triples) > 25:
        print(f"  ... +{len(triples) - 25} more")

    print(f"\n--- named entities ({len(ents)}) -> constants / sorts ---")
    from collections import Counter
    by_label = Counter(lbl for _, lbl in ents)
    for lbl, n in by_label.most_common():
        examples = sorted({txt for txt, l in ents if l == lbl})[:6]
        print(f"  {lbl:8} x{n:<3} e.g. {examples}")

    print(f"\n--- temporal cues ({len(dates)}) -> temporal logic (valid-time) ---")
    for e in dates[:15]:
        print(f"  [{e.text!r}] in: {e.sent.text.strip()[:90]}...")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
