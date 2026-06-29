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
from typing import TypedDict

import resolve

# NOTE (the lard, foreclosed): spaCy is NOT imported at module scope. `import spacy`
# transitively pulls thinc -> torch (~1.06s) + transformers, and a client that only
# needs the pure-text helpers (load_body/normalise) or the JSON facts wire must not
# pay it. spaCy is lazy-imported strictly inside load_model() — the one place that
# actually loads a local pipeline. So `import extract` stays import-light, and the
# remote (--remote) path of load_facts never drags the ML stack (proven by the gate
# test_lean_remote_client.py). doc_to_facts below operates on an ALREADY-parsed Doc,
# so it needs no spaCy import of its own.

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
    import spacy  # lazy: the ONLY module-local spaCy import (keeps `import extract` light)
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


# --- the facts wire schema, as ONE typed authority (ADR-0012 P7/P8) ----------
# The daemon->client wire and the load_facts consumer share these record shapes.
# Previously the only authority was the doc_to_facts docstring (prose the code could
# not check, restated at each of three sites); the TypedDicts make the wire shape a
# single checkable home. `sent`/`index` are the DOC-LOCAL sentence index; every value
# is a str/int/bool, so JSON is bit-exact for them (ADR-0009 discrete-invariant).
class SentRecord(TypedDict):
    index: int
    text: str


class EntityRecord(TypedDict):
    sent: int
    text: str
    canonical: str
    label: str


class TemporalRecord(TypedDict):
    sent: int
    text: str
    label: str


class TripleRecord(TypedDict):
    sent: int
    subj: str
    pred: str
    obj: str
    subj_key: str
    obj_key: str
    negated: bool


class FactBundle(TypedDict):
    sents: list[SentRecord]
    entities: list[EntityRecord]
    temporal: list[TemporalRecord]
    triples: list[TripleRecord]


def doc_to_facts(doc, coref_clusters=None) -> FactBundle:
    """THE SSOT per-document fact extractor (ADR-0012 P1: one home, two callers).

    Given a parsed spaCy `Doc` (and, optionally, the daemon's coref clusters to
    attach first), return a JSON-serializable dict of the discrete fact records the
    `mining` schema stores — the SAME records load_facts.py used to extract inline.
    There is exactly ONE home for this logic now; both callers use it:

      * the GPU daemon (nlp_server.handle, format="facts") runs it host-side so the
        --remote client receives finished JSON facts and never imports spaCy;
      * load_facts.py runs it locally (non-remote path) on each Doc it parses.

    The records are all strings + int offsets, so JSON is EXACT for them (no float
    coercion possible) — the discrete-invariant bit-exact bar of ADR-0009 applies:
    a round-tripped fact must be identical, never reordered-into-loss or coerced.

    Shape (the wire's one authority, ADR-0012 P7):
      {
        "sents":    [{"index": int, "text": str}, ...],          # doc-local order
        "entities": [{"sent": int, "text": str, "canonical": str, "label": str}, ...],
        "temporal": [{"sent": int, "text": str, "label": str}, ...],
        "triples":  [{"sent": int, "subj": str, "pred": str, "obj": str,
                      "subj_key": str, "obj_key": str, "negated": bool}, ...],
      }
    `index`/`sent` are the DOC-LOCAL sentence index (enumerate(doc.sents)); the
    caller maps that to its running sentence budget + DB sent_id. doc_to_facts owns
    *what a fact is*; the caller owns *which facts survive the budget* and *their DB
    identity* (the functional-core / imperative-shell split, ADR-0012 P9).
    """
    if coref_clusters is not None:
        # daemon path: attach the host-computed clusters so resolve.resolver_for sees
        # them. Exactly what the OLD remote client did before walking the Doc — the
        # resolution is therefore identical, only its HOME moved host-side. The wire
        # payload is decoded by the ONE decoder (resolve.attach_coref_clusters), shared
        # with nlp_client.pipe, so the two paths cannot drift on the cluster encoding.
        resolve.attach_coref_clusters(doc, coref_clusters)

    key_fn = resolve.resolver_for(doc)  # coref- + entity-resolved canonical constants
    sents: list[SentRecord] = []
    entities: list[EntityRecord] = []
    temporal: list[TemporalRecord] = []
    for si, sent in enumerate(doc.sents):
        sents.append({"index": si, "text": sent.text.strip()})
        for e in sent.ents:
            entities.append({
                "sent": si, "text": e.text,
                "canonical": resolve.canonical_key(e.text), "label": e.label_,
            })
            if e.label_ in ("DATE", "TIME"):
                temporal.append({"sent": si, "text": e.text, "label": e.label_})

    triples: list[TripleRecord] = []
    for t in extract_triples(doc, key_fn):
        triples.append({
            "sent": t.sent_i, "subj": t.subj, "pred": t.pred, "obj": t.obj,
            "subj_key": t.subj_key, "obj_key": t.obj_key, "negated": t.negated,
        })

    return {"sents": sents, "entities": entities,
            "temporal": temporal, "triples": triples}


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
        info = nlp.await_ready()  # patient: wait through the daemon's warmup, don't 5s-crash
        model_label = m or info.get("default", "remote")
        if verbose:
            print(f"=== remote daemon: {remote} | info: {info} ===")
    else:
        nlp = load_model(model)
        model_label = model
        if verbose:
            print(f"=== model: {nlp.meta['lang']}_{nlp.meta['name']} {nlp.meta['version']} "
                  f"| pipes: {nlp.pipe_names} ===")

    cache = None
    if cache_url:
        # The cache caches WHAT TRAVELS THE WIRE (ADR-0012 P7: derive from the wire's
        # one authority). On the remote path the wire is now JSON facts, so the cache
        # is the LEAN FactCache (json+redis, no spaCy) wrapping RemoteNLP.pipe_facts —
        # keeping --remote --cache import-light. Locally the wire is still a DocBin, so
        # it stays the DocCache. nlp_cache is lazy-imported here only, so a no-cache run
        # never touches it.
        if remote:
            from nlp_cache import CachingFacts, FactCache
            cache = FactCache(model_label, url=cache_url)
            nlp = CachingFacts(nlp, cache)
        else:
            from nlp_cache import CachingNLP, DocCache
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

    # collect sentences across paragraphs up to the sample budget. This consumes the
    # SSOT extractor (doc_to_facts) rather than re-walking doc.sents / re-deriving the
    # ("DATE","TIME") temporal classification inline — so "what an entity/temporal/SVO
    # fact is" has exactly ONE home (ADR-0012 P1), shared with load_facts.
    triples, ents, dates = [], [], []
    n_sents = 0
    for doc in docs:
        facts = doc_to_facts(doc)
        sent_text = {s["index"]: s["text"] for s in facts["sents"]}
        budget = set()  # doc-local sentence indices that survive the sample budget
        for s in facts["sents"]:
            if n_sents >= args.max_sents:
                break
            budget.add(s["index"])
            n_sents += 1
        triples.extend(t for t in facts["triples"] if t["sent"] in budget)
        ents.extend((e["text"], e["label"]) for e in facts["entities"] if e["sent"] in budget)
        dates.extend((tm["text"], sent_text[tm["sent"]])
                     for tm in facts["temporal"] if tm["sent"] in budget)
        if n_sents >= args.max_sents:
            break

    print(f"=== sample: {n_sents} sentences from {len(paragraphs)} paragraphs ===")
    if cache:
        print(f"=== cache stats: {cache.stats()} ===")
    print()

    print(f"--- SVO candidate triples ({len(triples)}) -> classical fact base ---")
    for t in triples[:25]:
        neg = "NOT " if t["negated"] else ""
        print(f"  ({t['subj']!r}, {neg}{t['pred']!r}, {t['obj']!r})")
    if len(triples) > 25:
        print(f"  ... +{len(triples) - 25} more")

    print(f"\n--- named entities ({len(ents)}) -> constants / sorts ---")
    from collections import Counter
    by_label = Counter(lbl for _, lbl in ents)
    for lbl, n in by_label.most_common():
        examples = sorted({txt for txt, l in ents if l == lbl})[:6]
        print(f"  {lbl:8} x{n:<3} e.g. {examples}")

    print(f"\n--- temporal cues ({len(dates)}) -> temporal logic (valid-time) ---")
    for txt, sent in dates[:15]:
        print(f"  [{txt!r}] in: {sent[:90]}...")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
