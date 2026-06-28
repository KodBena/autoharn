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

Wire/format safety: values are spaCy DocBin (msgpack) bytes — data, not code.
"""

from __future__ import annotations

import hashlib

import redis
import spacy
from spacy.tokens import DocBin

DEFAULT_URL = "redis://127.0.0.1:6380/0"  # the volatile-lru instance
PREFIX = "autoharn:spacy:doc"


class DocCache:
    def __init__(self, model_label: str, url: str = DEFAULT_URL,
                 ttl_seconds: int | None = None, vocab=None):
        self.r = redis.Redis.from_url(url)
        self.model_label = model_label
        self.ttl = ttl_seconds
        # a blank vocab suffices to rehydrate a DocBin (strings travel in it)
        self.vocab = vocab or spacy.blank("en").vocab
        self.hits = 0
        self.misses = 0

    def key(self, text: str, disable: tuple[str, ...]) -> str:
        h = hashlib.sha256()
        h.update(self.model_label.encode())
        h.update(b"\0")
        h.update(",".join(sorted(disable)).encode())
        h.update(b"\0")
        h.update(text.encode("utf-8"))
        return f"{PREFIX}:{h.hexdigest()}"

    def get(self, text: str, disable: tuple[str, ...] = ()):
        raw = self.r.get(self.key(text, disable))
        if raw is None:
            self.misses += 1
            return None
        self.hits += 1
        docs = list(DocBin().from_bytes(raw).get_docs(self.vocab))
        return docs[0] if docs else None

    def put(self, text: str, doc, disable: tuple[str, ...] = ()):
        db = DocBin(store_user_data=True)
        db.add(doc)
        self.r.set(self.key(text, disable), db.to_bytes(), ex=self.ttl)

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
        texts = list(texts)
        disable = tuple(disable)
        out = [None] * len(texts)
        miss_idx, miss_txt = [], []
        for i, t in enumerate(texts):
            d = self.cache.get(t, disable)
            if d is None:
                miss_idx.append(i)
                miss_txt.append(t)
            else:
                out[i] = d
        if miss_txt:
            parsed = list(self.inner.pipe(miss_txt, disable=disable))
            for j, d in enumerate(parsed):
                out[miss_idx[j]] = d
                self.cache.put(miss_txt[j], d, disable)
        return out

    def __call__(self, text, **kw):
        return self.pipe([text], **kw)[0]

    # passthroughs so it stays a drop-in
    def info(self):
        return getattr(self.inner, "info", lambda: {"local": True})()
