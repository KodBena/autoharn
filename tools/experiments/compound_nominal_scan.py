#!/usr/bin/env python3
"""compound_nominal_scan — EXPERIMENT, NOT A WIRED GATE (vestigial_documentation/design/ORCH-COMPOUND-NOMINAL-DETECTION.md).

Crudest-honest feasibility probe for detecting the "trust story" defect class: a novel,
lowercased noun-noun (or noun-noun-noun) compound whose inter-noun semantic relation is
unrecoverable to a zero-context reader, and which resolves to no definition surface
(GLOSSARY.md, gates/doc-legibility/terms.md, or an inline gloss in the same document).

This is the same architecture as the existing undefined-acronym scan (gates/doc-legibility/
check.py), one abstraction up: flag a token pattern, subtract everything that resolves to a
known definition surface, report what's left with a measured false-positive load.

HARD LIMITATION, stated up front (ADR-0011 Rule 1 honesty). This has NO part-of-speech
tagger. Separating a genuine N+N compound ("trust story") from adjective+noun ("live session",
"fresh context") or verb+noun ("trust boundaries") is exactly what a POS tagger does and this
script cannot. It approximates a noun lexicon from the corpus itself (words seen in a
determiner/preposition slot) plus adjective/participle suffix filters. The precision this buys
is MEASURED in the companion results file, not asserted. Stdlib only, deliberately: the
no-lazy-imports law (CLAUDE.md 2026-07-02) plus the dependency posture of gates/ (every gate is
stdlib-only) means adding a real tagger (spaCy/NLTK) is a maintainer decision, not this probe's
to make.

Run:  python3 tools/experiments/compound_nominal_scan.py            # summary + full hit list
      python3 tools/experiments/compound_nominal_scan.py --sample 40  # first N hits, for hand-classification
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GLOSSARY = REPO_ROOT / "GLOSSARY.md"
TERMS = REPO_ROOT / "gates" / "doc-legibility" / "terms.md"

# Same corpus exclusions the shipped gates use, plus research/ (see note).
EXCLUDE_DIR_PREFIXES = ("judgment/", "vestigial_documentation/", "research/")
# research/ is the frozen obligations-formalisms survey — dense domain jargon with its own
# KEY.md legend; it is not maintainer-facing prose in the ADR-0017 sense and would dominate a
# noun-compound scan with legitimate multi-word technical terms. Excluded here and the
# exclusion is named, not silent (mirrors the shipped gates' printed-exclusion convention).

DETERMINERS = {
    "the", "a", "an", "this", "that", "these", "those", "each", "every", "no", "any",
    "some", "all", "both", "either", "neither", "one", "its", "their", "our", "your",
    "his", "her", "my", "whose", "which", "what", "another", "such", "same", "other",
}
PREPOSITIONS = {
    "of", "in", "on", "for", "to", "by", "with", "from", "at", "as", "into", "onto",
    "over", "under", "per", "via", "about", "against", "between", "across", "through",
    "within", "without", "upon", "toward", "towards", "before", "after", "during",
}
# A bigram with either slot in this closed-class set is never N+N.
STOP = DETERMINERS | PREPOSITIONS | {
    "and", "or", "but", "nor", "so", "yet", "if", "then", "else", "when", "while",
    "is", "are", "was", "were", "be", "been", "being", "am", "do", "does", "did",
    "has", "have", "had", "having", "will", "would", "shall", "should", "can", "could",
    "may", "might", "must", "not", "yes", "it", "they", "them", "we", "us",
    "you", "he", "she", "him", "i", "me", "who", "whom", "how", "why", "where",
    "here", "there", "now", "than", "too", "very", "just", "only", "also", "still",
    "more", "most", "less", "least", "much", "many", "few", "up", "out", "off",
    "down", "again", "once", "ever", "never", "always", "often", "well", "even",
    "like", "unlike", "because", "since", "until", "unless", "though", "although",
    "however", "therefore", "thus", "hence", "instead", "rather", "etc",
    "vs", "let", "get", "got", "see",
}
# Adjective/participle suffixes (crude morphology): a word ending in one is treated as a
# modifier, not a noun head, dropping "live session", "deductive maintenance", "typed grammars".
ADJ_SUFFIXES = (
    "al", "ive", "ous", "ic", "ical", "ful", "less", "ary", "ent", "ant", "able",
    "ible", "ly", "ing", "ed", "ish", "ory",
)
# Lexicalized compounds the maintainer named benign ("olive oil" class) + house time-compounds.
LEXICALIZED_OK = {
    ("olive", "oil"), ("common", "sense"), ("side", "effect"), ("real", "time"),
    ("run", "time"), ("build", "time"), ("write", "time"), ("commit", "time"),
    ("top", "level"), ("open", "source"), ("plain", "english"), ("plain", "words"),
    ("plain", "language"), ("data", "model"), ("edge", "case"), ("corner", "case"),
    ("test", "bed"), ("code", "block"), ("source", "code"), ("test", "case"),
}
COMMON_ADJ = {
    "live", "fresh", "new", "old", "full", "whole", "half", "empty", "clean", "dirty",
    "hard", "soft", "high", "low", "long", "short", "large", "small", "big", "little",
    "good", "bad", "best", "worst", "right", "wrong", "true", "false", "real", "fake",
    "open", "closed", "free", "busy", "safe", "next", "last", "first", "final", "main",
    "core", "raw", "plain", "flat", "deep", "wide", "narrow", "broad", "left",
    "top", "bottom", "front", "back", "inner", "outer", "local", "remote", "single",
    "double", "triple", "partial", "total", "prior", "current",
    "actual", "given", "known", "silent", "loud", "cheap", "dead", "alive",
    "own", "sole", "mere", "bare", "sound", "honest", "lazy", "eager", "stale",
    "red", "green", "blue", "black", "white", "grey", "gray", "warm", "cold", "cool",
}


def tracked_md() -> list[Path]:
    r = subprocess.run(["git", "-C", str(REPO_ROOT), "ls-files", "*.md"],
                       capture_output=True, text=True, check=True)
    out = []
    for ln in r.stdout.splitlines():
        if not ln.strip():
            continue
        if any(ln.startswith(p) for p in EXCLUDE_DIR_PREFIXES):
            continue
        if os.path.basename(ln) in {"GLOSSARY.md", "terms.md", "KEY.md"}:
            continue  # definition surfaces
        out.append(REPO_ROOT / ln)
    return out


WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")


def strip_prose(line: str) -> str:
    """Drop markdown link TARGETS and inline-code spans; keep link text, prose, table cells."""
    line = re.sub(r"\]\([^)]*\)", "]", line)            # ](url) -> ]
    line = re.sub(r"<[^>]+>", " ", line)                # html tags
    parts = line.split("`")
    return " ".join(parts[i] for i in range(0, len(parts), 2))  # even = outside inline code


def multiword_defs() -> set[tuple[str, ...]]:
    """Multi-word coined terms from the definition surfaces — the whitelist SSOT.
    GLOSSARY.md `##`/`###` headings and terms.md `**bold**` leads, lowercased, tupled to 2/3."""
    defs: set[tuple[str, ...]] = set()
    for f, patt in ((GLOSSARY, re.compile(r"^#{2,3}\s+(.*)$", re.M)),
                    (TERMS, re.compile(r"\*\*([^*]+)\*\*"))):
        if not f.exists():
            continue
        txt = f.read_text(encoding="utf-8")
        for m in patt.finditer(txt):
            words = [w.lower() for w in WORD.findall(m.group(1))]
            for n in (2, 3):
                for i in range(len(words) - n + 1):
                    defs.add(tuple(words[i:i + n]))
    return defs


def is_noun_head(w: str) -> bool:
    """Poor-man's POS: could `w` be a noun? Reject function words, common adjectives, and
    adjective/participle-suffixed words. Everything surviving is TREATED AS noun-capable — the
    crude core, and the source of most false positives (measured, not hidden)."""
    if w in STOP or w in COMMON_ADJ:
        return False
    if len(w) < 3:
        return False
    for suf in ADJ_SUFFIXES:
        if w.endswith(suf) and len(w) > len(suf) + 2:
            return False
    return True


def build_noun_lexicon(files: list[Path]) -> set[str]:
    """Words seen immediately after a determiner or preposition anywhere in the corpus — a
    slot that strongly selects nouns. Gates the modifier slot: 'trust' qualifies because
    'the trust ...' / 'of trust' occur. Crude, corpus-derived, no external lexicon."""
    lex: set[str] = set()
    selector = DETERMINERS | PREPOSITIONS
    for f in files:
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        in_code = False
        for line in lines:
            s = line.strip()
            if s.startswith("```") or s.startswith("~~~"):
                in_code = not in_code
                continue
            if in_code:
                continue
            toks = [w.lower() for w in WORD.findall(strip_prose(line))]
            for a, b in zip(toks, toks[1:]):
                if a in selector and b not in STOP:
                    lex.add(b)
    return lex


def scan(files, noun_lex, whitelist):
    """Yield (path, lineno, ngram, text) for each candidate novel N+N / N+N+N compound."""
    hits = []
    for f in files:
        rel = os.path.relpath(f, REPO_ROOT)
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        in_code = False
        for ln, line in enumerate(lines, 1):
            s = line.strip()
            if s.startswith("```") or s.startswith("~~~"):
                in_code = not in_code
                continue
            if in_code or s.startswith("#") or s.startswith("<!--"):
                continue
            text = strip_prose(line)
            words = WORD.findall(text)
            low = [w.lower() for w in words]
            i = 0
            while i < len(words) - 1:
                matched = False
                for n in (3, 2):          # prefer the longer match
                    if i + n > len(words):
                        continue
                    span = words[i:i + n]
                    lspan = tuple(low[i:i + n])
                    if any(w[0].isupper() for w in span):
                        break             # lowercase-only defect profile
                    if not all(is_noun_head(w) for w in lspan):
                        continue
                    if not all(w in noun_lex for w in lspan):
                        continue
                    if lspan in whitelist:
                        continue
                    hits.append((rel, ln, " ".join(lspan), s))
                    i += n
                    matched = True
                    break
                if not matched:
                    i += 1
    return hits


# ---------------------------------------------------------------------------------------
# Second defect class: TABLE LABEL-COLUMN TYPE INCOHERENCE (cross-division / fundamentum
# divisionis violation). The MECHANICAL part — parse tables, extract the label column's header
# and each row label, and emit the maintainer's "broadcast" concatenation (header + ": " +
# label) for review — is done here. The TYPE-COHERENCE judgment (does each concatenation read
# as a well-formed phrase of the declared type?) is SEMANTIC and stays with a human/LLM reader;
# this pass only enumerates the surface a reviewer must check and counts it.
# ---------------------------------------------------------------------------------------

def find_tables(files):
    """Yield (rel, header_line_no, header_cells, [(row_line_no, first_cell)...]) for every
    GitHub-flavored markdown table: a header row of `| a | b |`, a `| --- | --- |` delimiter,
    then body rows. Only well-formed pipe tables are recognized (the corpus's tables all are)."""
    tables = []
    for f in files:
        rel = os.path.relpath(f, REPO_ROOT)
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        in_code = False
        i = 0
        while i < len(lines):
            s = lines[i].strip()
            if s.startswith("```") or s.startswith("~~~"):
                in_code = not in_code
                i += 1
                continue
            if in_code:
                i += 1
                continue
            # A header row followed by a delimiter row of only |, -, :, spaces.
            if (s.startswith("|") and i + 1 < len(lines)
                    and re.fullmatch(r"\|[\s:|-]+\|?", lines[i + 1].strip())
                    and "-" in lines[i + 1]):
                header = [c.strip() for c in s.strip("|").split("|")]
                rows = []
                j = i + 2
                while j < len(lines) and lines[j].strip().startswith("|"):
                    cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                    rows.append((j + 1, cells[0] if cells else ""))
                    j += 1
                if rows:
                    tables.append((rel, i + 1, header, rows))
                i = j
                continue
            i += 1
    return tables


def cmd_tables(files):
    tables = find_tables(files)
    # A "label column" is worth the broadcast test when its header is a noun phrase declaring a
    # type/genus and it has >=3 rows (a real enumeration). We cannot judge that mechanically, so
    # we emit ALL tables' label columns and let the reader apply the test to a sample.
    print(f"table_broadcast (EXPERIMENT): {len(tables)} markdown tables across {len(files)} docs")
    multi = [t for t in tables if len(t[3]) >= 3]
    print(f"  tables with >=3 body rows (enumeration-shaped, broadcast-testable): {len(multi)}\n")
    for rel, hln, header, rows in multi:
        genus = header[0] if header else ""
        print(f"  {rel}:{hln}  label-column header = {genus!r}")
        for rln, label in rows:
            print(f"      broadcast: {genus} : {label}")
        print()
    return 0


def main(argv):
    if argv and argv[0] == "--tables":
        return cmd_tables(tracked_md())
    sample = None
    if argv and argv[0] == "--sample":
        sample = int(argv[1]) if len(argv) > 1 else 40
    files = tracked_md()
    whitelist = multiword_defs() | LEXICALIZED_OK
    noun_lex = build_noun_lexicon(files)
    hits = scan(files, noun_lex, whitelist)
    freq = Counter(h[2] for h in hits)

    print(f"compound_nominal_scan (EXPERIMENT): {len(files)} docs scanned "
          f"(excluded: {', '.join(EXCLUDE_DIR_PREFIXES)} + definition surfaces)")
    print(f"  noun-lexicon size (corpus-derived): {len(noun_lex)}")
    print(f"  whitelist (GLOSSARY/terms multiword + lexicalized): {len(whitelist)}")
    print(f"  TOTAL candidate hits: {len(hits)}  ({len(freq)} distinct compounds)\n")
    print("  distinct compounds by frequency (top 70):")
    for comp, c in freq.most_common(70):
        print(f"    {c:4d}  {comp}")

    if sample is not None:
        print(f"\n  --- first {sample} hits in corpus order (for hand-classification) ---")
        for rel, ln, comp, text in hits[:sample]:
            print(f"    {rel}:{ln}  [{comp}]")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
