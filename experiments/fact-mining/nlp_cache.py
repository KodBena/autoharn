#!/usr/bin/env python
"""Redis-backed DocBin cache for spaCy parses.

Parsing is the expensive step (a GPU round-trip for the transformer model). The
result for a given (model, pipeline-config, text) is deterministic, so we cache
it: key by a content hash, store the DocBin bytes, and skip the parse on a hit.

Placement: the cache lives on the GUEST, next to the consumer, in front of the
remote daemon — a hit avoids the wire call entirely.

Which redis: use the VOLATILE instance (127.0.0.1:6380, allkeys-lru, no
persistence). Parses are regenerable, so an evictable cache is the correct home.
Do NOT use 6379 (noeviction, disk-persisted) — that is a durable system of
record; filling it with regenerable blobs could make it refuse writes.

Key namespacing: shared redis is used by multiple projects (see the foundational
map's cross-project-collision warning), so every key is prefixed `autoharn:`.

Wire/format safety: values are spaCy DocBin (msgpack) bytes, OR — for the lean
remote facts wire — JSON fact records (FactCache). Both are data, not code.

IMPORT DISCIPLINE: spaCy is lazy-imported (inside DocCache) so `import nlp_cache`
stays import-light. The remote facts path uses FactCache (json+redis only), so
--remote --cache never drags the ML stack — the same leanness the wire cut earns.
"""

from __future__ import annotations

import hashlib
import json

import redis

DEFAULT_URL = "redis://127.0.0.1:6380/0"  # the volatile-lru instance
PREFIX = "autoharn:spacy:doc"
PREFIX_FACTS = "autoharn:spacy:facts"  # the facts wire is a DISTINCT cache namespace


def _cache_key(prefix: str, model_label: str, text: str, disable: tuple[str, ...]) -> str:
    """ONE home (ADR-0012 P1) for the content-hash cache key both caches use; only the
    namespace prefix differs (a DocBin parse vs the JSON facts derived from it)."""
    h = hashlib.sha256()
    h.update(model_label.encode())
    h.update(b"\0")
    h.update(",".join(sorted(disable)).encode())
    h.update(b"\0")
    h.update(text.encode("utf-8"))
    return f"{prefix}:{h.hexdigest()}"


def _pipe_cached(texts, disable, cache_get, fetch_misses, cache_put):
    """ONE home (ADR-0012 P1/P3) for cache-miss batching, shared by CachingNLP (DocBin)
    and CachingFacts (JSON facts): forward only cache-missing texts to the inner
    pipeline in one batch, store each result, and preserve input order on return."""
    texts = list(texts)
    disable = tuple(disable)
    out = [None] * len(texts)
    miss_idx, miss_txt = [], []
    for i, t in enumerate(texts):
        v = cache_get(t, disable)
        if v is None:
            miss_idx.append(i)
            miss_txt.append(t)
        else:
            out[i] = v
    if miss_txt:
        got = list(fetch_misses(miss_txt, disable))
        for j, v in enumerate(got):
            out[miss_idx[j]] = v
            cache_put(miss_txt[j], v, disable)
    return out


class DocCache:
    def __init__(self, model_label: str, url: str = DEFAULT_URL,
                 ttl_seconds: int | None = None, vocab=None):
        import spacy  # lazy: only the DocBin cache needs spaCy (keeps `import nlp_cache` light)
        from spacy.tokens import DocBin  # noqa: F401  (used in get/put)
        self.r = redis.Redis.from_url(url)
        self.model_label = model_label
        self.ttl = ttl_seconds
        # a blank vocab suffices to rehydrate a DocBin (strings travel in it)
        self.vocab = vocab or spacy.blank("en").vocab
        self.hits = 0
        self.misses = 0

    def key(self, text: str, disable: tuple[str, ...]) -> str:
        return _cache_key(PREFIX, self.model_label, text, disable)

    def get(self, text: str, disable: tuple[str, ...] = ()):
        from spacy.tokens import DocBin
        raw = self.r.get(self.key(text, disable))
        if raw is None:
            self.misses += 1
            return None
        self.hits += 1
        docs = list(DocBin().from_bytes(raw).get_docs(self.vocab))
        return docs[0] if docs else None

    def put(self, text: str, doc, disable: tuple[str, ...] = ()):
        from spacy.tokens import DocBin
        db = DocBin(store_user_data=True)
        db.add(doc)
        self.r.set(self.key(text, disable), db.to_bytes(), ex=self.ttl)

    def stats(self) -> dict:
        total = self.hits + self.misses
        return {"hits": self.hits, "misses": self.misses,
                "hit_rate": round(self.hits / total, 3) if total else None}


class FactCache:
    """The LEAN counterpart of DocCache for the remote facts wire: caches the JSON
    fact records (extract.doc_to_facts output) per text. json+redis only — NO spaCy —
    so --remote --cache stays import-light. A distinct key namespace (PREFIX_FACTS)
    keeps it from colliding with DocBin entries for the same (model, text)."""

    def __init__(self, model_label: str, url: str = DEFAULT_URL,
                 ttl_seconds: int | None = None):
        self.r = redis.Redis.from_url(url)
        self.model_label = model_label
        self.ttl = ttl_seconds
        self.hits = 0
        self.misses = 0

    def key(self, text: str, disable: tuple[str, ...]) -> str:
        return _cache_key(PREFIX_FACTS, self.model_label, text, disable)

    def get(self, text: str, disable: tuple[str, ...] = ()):
        raw = self.r.get(self.key(text, disable))
        if raw is None:
            self.misses += 1
            return None
        self.hits += 1
        return json.loads(raw)

    def put(self, text: str, facts: dict, disable: tuple[str, ...] = ()):
        self.r.set(self.key(text, disable), json.dumps(facts).encode("utf-8"), ex=self.ttl)

    def stats(self) -> dict:
        total = self.hits + self.misses
        return {"hits": self.hits, "misses": self.misses,
                "hit_rate": round(self.hits / total, 3) if total else None}


class CachingNLP:
    """Wrap any nlp-like (local Language or RemoteNLP) with a DocCache.

    Only cache-missing texts are forwarded to the inner pipeline, in one batch,
    preserving input order on return.
    """

    def __init__(self, inner, cache: DocCache):
        self.inner = inner
        self.cache = cache

    def pipe(self, texts, disable=()):
        return _pipe_cached(
            texts, disable, self.cache.get,
            lambda t, d: self.inner.pipe(t, disable=d), self.cache.put)

    def __call__(self, text, **kw):
        return self.pipe([text], **kw)[0]

    # passthroughs so it stays a drop-in
    def info(self):
        return getattr(self.inner, "info", lambda: {"local": True})()


class CachingFacts:
    """Wrap a RemoteNLP with a FactCache on the LEAN facts wire. Mirrors CachingNLP but
    over `.pipe_facts` (JSON facts) instead of `.pipe` (DocBin) — a cache hit avoids
    the wire call entirely, exactly as the DocBin cache does, and shares the one
    miss-batching home (_pipe_cached). spaCy-free: the whole point of the facts cut."""

    def __init__(self, inner, cache: FactCache):
        self.inner = inner
        self.cache = cache

    def pipe_facts(self, texts, disable=()):
        out = _pipe_cached(
            texts, disable, self.cache.get,
            lambda t, d: self.inner.pipe_facts(t, disable=d), self.cache.put)
        # surface the inner's verify result (None on the non-coref cache path)
        self.last_coref_verify = getattr(self.inner, "last_coref_verify", None)
        return out

    def info(self):
        return getattr(self.inner, "info", lambda: {"local": True})()
