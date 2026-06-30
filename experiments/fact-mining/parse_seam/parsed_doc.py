#!/usr/bin/env python
"""parse_seam.parsed_doc — the NEUTRAL parse type the fact extractor consumes.

This is the Port/ACL native representation (ADR-0012 P2): the one framework-neutral
type `doc_to_facts`/`extract_triples` read, decoded FROM a concrete parser (spaCy,
Stanza, …) by an adapter. The extractor never again names a spaCy attribute; it names
ONLY the fields below. "Add a parse backend" therefore means "write one adapter that
fills a `ParsedDoc`", with zero edits to the extractor (P2 check (a)).

It carries EXACTLY what the extractor + its resolver read, and nothing else (ADR-0012
P8: the type is the contract SSOT — no field the consumer does not use):

  * token: `text` / `pos` / `dep` / `lemma` / `head` (head-INDEX, not a live token
    handle — the dependency tree is a flat index array, framework-neutral) + `idx`
    (char offset, REQUIRED to map coref char-spans onto tokens — see `char_span`);
  * entity: `text` / `label` + char span (`start_char`/`end_char`) + token span
    (`start_token`/`end_token`, for the entity-membership test the resolver runs);
  * sentence: `index` + `text` + token span;
  * coref clusters: char-span clusters (the daemon's wire payload shape, decoded once).

FRAMEWORK-NEUTRAL: this module imports NO spaCy, NO torch, NO Stanza — it is plain
dataclasses + pure structural helpers (children/subtree/char_span derived from the
flat token+head-index arrays). That is what makes it the seam both sides meet at.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# A coref cluster is a list of mention spans, each a (start_char, end_char) pair; the
# clusters payload is a tuple of such clusters. This is the SAME shape the daemon wire
# carries (resolve.attach_coref_clusters decodes JSON arrays into this), kept neutral.
CharSpan = tuple[int, int]
CorefClusters = tuple[tuple[CharSpan, ...], ...]


@dataclass(frozen=True)
class ParsedToken:
    """One token, in flat-array form. `head` is the doc-local INDEX of this token's
    syntactic head (a token is its own head iff it is the dependency-tree root, exactly
    spaCy's `token.head is token` convention) — never a live object handle, so the tree
    is reconstructible by any backend that can emit (i, head-index) pairs."""

    i: int           # doc-local token index (position in ParsedDoc.tokens)
    text: str        # surface form
    pos: str         # coarse POS tag (spaCy `pos_`, Stanza `upos`)
    dep: str         # dependency relation to the head (spaCy `dep_`, Stanza `deprel`)
    lemma: str       # lemma (spaCy `lemma_`, Stanza `lemma`)
    head: int        # doc-local index of the head token (== i for the root)
    idx: int         # char offset of the token's first character in ParsedDoc.text

    @property
    def end_char(self) -> int:
        """Exclusive char offset just past the token (idx + len(text))."""
        return self.idx + len(self.text)


@dataclass(frozen=True)
class ParsedEnt:
    """A named entity: surface text + label + its char span AND token span. The token
    span (`start_token`..`end_token`, exclusive) is what the resolver's entity-membership
    test needs (`start_token <= tok.i < end_token`); the char span is the human/coref
    coordinate. spaCy `ent.start`/`ent.end` are token indices; `start_char`/`end_char`
    are char offsets — both are recorded so neither consumer has to recompute the other."""

    text: str
    label: str
    start_char: int
    end_char: int
    start_token: int
    end_token: int


@dataclass(frozen=True)
class ParsedSent:
    """A sentence: its doc-local index, its surface text (UNstripped — the extractor owns
    the `.strip()`, exactly as it did on `sent.text`), and its token span."""

    index: int
    text: str
    start_token: int
    end_token: int


@dataclass(frozen=True)
class ParsedDoc:
    """The neutral parse: the doc text plus flat token / entity / sentence arrays and the
    coref clusters. The structural helpers below (`children`/`subtree`/`char_span`/
    `ent_token_ids`) are PURE derivations of those arrays — the same graph spaCy exposes
    as `token.children`/`token.subtree`/`doc.char_span`, recomputed neutrally so the
    extractor needs none of spaCy's live objects."""

    text: str
    tokens: tuple[ParsedToken, ...]
    ents: tuple[ParsedEnt, ...]
    sents: tuple[ParsedSent, ...]
    coref_clusters: CorefClusters = field(default=())

    # ---- structural derivations (pure; the neutral form of spaCy's token graph) --------
    def children(self, i: int) -> list[ParsedToken]:
        """Tokens whose head is token `i`, in ascending index order (spaCy's
        `token.children` ordering). The root is excluded from its OWN children via the
        `t.i != i` guard (the root's head is itself)."""
        return [t for t in self.tokens if t.head == i and t.i != i]

    def subtree(self, i: int) -> list[ParsedToken]:
        """Token `i` plus all its descendants, ascending by index — the neutral
        `token.subtree`. Iterative DFS over `children`, so it is safe on any tree depth."""
        seen: list[ParsedToken] = []
        stack = [i]
        picked: set[int] = set()
        while stack:
            j = stack.pop()
            if j in picked:
                continue
            picked.add(j)
            seen.append(self.tokens[j])
            stack.extend(c.i for c in self.children(j))
        return sorted(seen, key=lambda t: t.i)

    def char_span(self, start: int, end: int) -> tuple[ParsedToken, ...] | None:
        """The tokens overlapping the char range [start, end) — the neutral equivalent of
        spaCy's `doc.char_span(start, end, alignment_mode="expand")`: every token that the
        range touches, expanded to whole-token boundaries. Returns None when the range is
        empty or no token overlaps (so a caller can try an inclusive-end fallback, exactly
        as resolve._char_span does with end+1)."""
        if end <= start:
            return None
        hit = tuple(t for t in self.tokens if t.idx < end and t.end_char > start)
        return hit or None

    def ent_token_ids(self) -> frozenset[int]:
        """The set of token indices that lie inside SOME entity — the neutral source for a
        token's `ent_type_` truthiness (a token "has an entity type" iff it is in an ent)."""
        ids: set[int] = set()
        for e in self.ents:
            ids.update(range(e.start_token, e.end_token))
        return frozenset(ids)
