#!/usr/bin/env python
"""parse_seam.resolve_parsed — the resolver, ported to the neutral ParsedDoc.

`resolve.resolver_for(doc)` reads spaCy attributes (`doc._.coref_clusters`,
`doc.char_span`, `doc.ents`, `tok.pos_`/`ent_type_`/`dep_`/`lemma_`/`i`). This module is
its BEHAVIOR-IDENTICAL twin over `ParsedDoc` — mention-by-mention the same scoring and the
same fallbacks — so the neutral fact path resolves the same canonical constants the spaCy
path always did. The pure string canonicalizer (`resolve.canonical_key`) is REUSED, not
re-authored (ADR-0012 P1: one home for that fact); only the doc-walking parts are
re-expressed against the neutral fields.

It is FRAMEWORK-NEUTRAL (imports only `resolve.canonical_key`, itself import-light).
"""

from __future__ import annotations

from collections.abc import Callable

from resolve import canonical_key

from parse_seam.parsed_doc import ParsedDoc, ParsedToken


def _char_span(pdoc: ParsedDoc, s: int, e: int) -> tuple[ParsedToken, ...] | None:
    """Tolerant char->tokens (exclusive vs inclusive end), mirroring resolve._char_span:
    try [s, e), then [s, e+1)."""
    return pdoc.char_span(s, e) or pdoc.char_span(s, e + 1)


def _span_text(pdoc: ParsedDoc, span: tuple[ParsedToken, ...]) -> str:
    """The surface substring a token span covers — the neutral `Span.text`
    (doc.text[first.idx : last.end_char], whitespace between tokens included)."""
    return pdoc.text[span[0].idx:span[-1].end_char]


def _pick_representative(
    pdoc: ParsedDoc, spans: list[tuple[ParsedToken, ...]], ent_ids: frozenset[int]
) -> tuple[ParsedToken, ...]:
    """Best mention to stand for a cluster — the most constant-like one, scored EXACTLY as
    resolve._pick_representative: prefer not-a-pronoun, then carries-an-entity, then
    not-a-relative-clause, then the SHORTEST (a clean constant beats a long NP)."""

    def score(sp: tuple[ParsedToken, ...]) -> tuple[int, int, int, int]:
        not_pron = 0 if all(t.pos in ("PRON", "DET") for t in sp) else 1
        has_ent = 1 if any(t.i in ent_ids for t in sp) else 0
        no_relcl = 0 if any(t.dep == "relcl" for t in sp) else 1
        return (not_pron, has_ent, no_relcl, -len(_span_text(pdoc, sp)))

    return max(spans, key=score)


def build_resolution_map(pdoc: ParsedDoc) -> dict[int, str]:
    """token index -> canonical key, for tokens inside a non-representative coref mention.
    Line-for-line the neutral form of resolve.build_resolution_map."""
    ent_ids = pdoc.ent_token_ids()
    resmap: dict[int, str] = {}
    for cluster in pdoc.coref_clusters:
        spans = [_char_span(pdoc, s, e) for s, e in cluster]
        kept = [sp for sp in spans if sp is not None]
        if len(kept) < 2:
            continue
        rep = _pick_representative(pdoc, kept, ent_ids)
        rep_key = canonical_key(_span_text(pdoc, rep))
        if not rep_key:
            continue
        for sp in kept:
            if sp is rep:
                continue
            for tok in sp:
                resmap[tok.i] = rep_key
    return resmap


def _entity_key(pdoc: ParsedDoc, token: ParsedToken) -> str | None:
    """Canonical key of the named entity the token belongs to, else None (neutral form of
    resolve._entity_key: scan ents for the one whose token span contains `token.i`)."""
    for e in pdoc.ents:
        if e.start_token <= token.i < e.end_token:
            return canonical_key(e.text)
    return None


def resolver_for(pdoc: ParsedDoc) -> Callable[[ParsedToken], str]:
    """key(token) -> canonical constant, using coref (if present) + entity norm. The four
    fallbacks are resolve.resolver_for's, unchanged: (1) coref referent, (2) entity
    normalization, (3) an UNRESOLVED pronoun is not a constant (""), (4) lemma fallback."""
    resmap = build_resolution_map(pdoc)

    def key(token: ParsedToken) -> str:
        if token.i in resmap:
            return resmap[token.i]
        ek = _entity_key(pdoc, token)
        if ek:
            return ek
        if token.pos == "PRON":
            return ""
        return canonical_key(token.lemma)

    return key
