#!/usr/bin/env python3
"""
grep_tells.py — surface the laundering signature in a change's justification.

A "tell" is a minimality-word (the vocabulary used to argue a fix down) that
appears near a named alternative fix (evidence a better fix was in hand). The
documented failures both contain this: "scope creep" one sentence from
"producer/owner"; "brittle in principle ... acceptable" at a reparse site.

This is a HEURISTIC FLAG, not proof. A hit marks the sentence to read — the
place where a more-correct fix may have been named and then discarded on a
discipline-word instead of a concrete cost. Zero hits is not absolution; a
clean implementer simply stopped narrating the downgrade.

Usage:
    python grep_tells.py path/to/justification.txt
    python grep_tells.py path/to/file.diff
    git show <sha> | python grep_tells.py -
    git log -1 --format=%B | python grep_tells.py -

Exit code is 0 always (this is an advisory scanner, not a CI gate by itself);
it prints a structured report and a final tally. Wrap it in your own gate if
you want non-zero on hits.
"""

import re
import sys

# Words used to argue a fix DOWN. Lowercased, matched as whole-ish phrases.
MINIMALITY_TERMS = [
    "scope creep", "out of scope", "over-engineer", "overengineer",
    "over-build", "overbuild", "gold-plat", "proportionate", "minimal",
    "minimality", "minimal-touch", "for now", "good enough", "acceptable",
    "pragmatic", "don't need", "do not need", "no need to", "not worth",
    "premature", "later", "follow-up", "followup", "defer", "punt",
    "band-aid", "bandaid", "quick fix", "quick win", "one notch deeper",
    "optional", "nice to have", "nice-to-have", "ship it", "kiss",
]

# Cues that a BETTER / MORE-GENERAL fix (or a hazard) was NAMED. Their presence
# near a minimality term is the signature.
NAMED_FIX_CUES = [
    "the right fix", "correct fix", "deeper fix", "deeper-but-right",
    "proper fix", "real fix", "better fix", "ideal", "ought to",
    "we could instead", "could instead", "the general case", "general fix",
    "ownership", "owner", "producer", "invariant", "the root cause",
    "root cause", "really should", "should really", "the honest",
    "brittle", "fragile", "hack", "workaround", "shortcut", "smell",
    "technically wrong", "not the root", "treats the symptom", "symptom",
    "in principle",
]

# How close (in characters) a minimality term and a named-fix cue must be to
# count as a co-occurrence. ~1-2 sentences.
WINDOW = 220


def find_terms(text_lc, terms):
    hits = []
    for t in terms:
        start = 0
        while True:
            i = text_lc.find(t, start)
            if i == -1:
                break
            hits.append((i, i + len(t), t))
            start = i + 1
    return hits


def line_of(text, idx):
    return text.count("\n", 0, idx) + 1


def snippet(text, lo, hi, pad=90):
    s = max(0, lo - pad)
    e = min(len(text), hi + pad)
    frag = text[s:e].replace("\n", " ")
    frag = re.sub(r"\s+", " ", frag).strip()
    return ("…" if s > 0 else "") + frag + ("…" if e < len(text) else "")


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    src = sys.argv[1]
    text = sys.stdin.read() if src == "-" else open(src, encoding="utf-8", errors="replace").read()

    lc = text.lower()
    min_hits = find_terms(lc, MINIMALITY_TERMS)
    cue_hits = find_terms(lc, NAMED_FIX_CUES)

    # A tell = a minimality term with a named-fix cue within WINDOW chars.
    tells = []
    for (mlo, mhi, mterm) in min_hits:
        near = [c for c in cue_hits if abs(c[0] - mlo) <= WINDOW]
        if near:
            # nearest cue
            c = min(near, key=lambda c: abs(c[0] - mlo))
            span_lo = min(mlo, c[0])
            span_hi = max(mhi, c[1])
            tells.append({
                "line": line_of(text, mlo),
                "minimality": mterm,
                "named_fix": c[2],
                "snippet": snippet(text, span_lo, span_hi),
            })

    # de-dup overlapping tells by (line, minimality, named_fix)
    seen = set()
    uniq = []
    for t in tells:
        k = (t["line"], t["minimality"], t["named_fix"])
        if k not in seen:
            seen.add(k)
            uniq.append(t)

    print("=" * 72)
    print(f"grep_tells: {src}")
    print("=" * 72)
    if not uniq:
        print("No tells. A minimality-word adjacent to a named-better-fix was not")
        print("found. NOTE: this is not absolution — a downgrade made silently")
        print("(without narrating the better fix) leaves no tell here. Proceed to")
        print("Step 2 (enumerate writers) regardless.")
    else:
        print(f"{len(uniq)} tell(s) — each is a place a better fix may have been")
        print("named and then argued down. For each, demand the DOWNGRADE line:")
        print("what CONCRETE COST justified the narrower fix? A discipline-word is")
        print("not a cost.\n")
        for i, t in enumerate(uniq, 1):
            print(f"[{i}] line {t['line']}: "
                  f"'{t['minimality']}'  ~near~  '{t['named_fix']}'")
            print(f"    … {t['snippet']}")
            print()

    print("-" * 72)
    print(f"minimality-terms seen: {len(min_hits)} | "
          f"named-fix cues seen: {len(cue_hits)} | "
          f"co-occurrence tells: {len(uniq)}")
    print("Advisory only. Read the snippets; the scanner cannot tell a justified")
    print("narrowing from a hack — only YOU comparing cost-vs-mood can.")


if __name__ == "__main__":
    main()
