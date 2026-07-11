#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T14:35:32Z
#   last-change: 2026-07-11T14:49:43Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""doc-legibility gate — the incident-born `*_violations` check for stranded acronyms.

Class, not instance (ADR-0011 Rule 4): instead of defining acronyms one at a time, this FAILS the
build if ANY acronym-like token in the scoped docs is neither (a) defined — bolded `**TOK**` in a
definition surface (the persistent gates/doc-legibility/terms.md, the survey KEY.md, or the root
GLOSSARY.md) — nor (b) explicitly allow-listed as common knowledge. The allowlist makes the
"this one is obvious" judgement itself reviewable.

The check keys on the *atomic* acronym, not the surface token: a compound like `LTL/CTL`,
`AGM-rational`, `non-LLM`, or `QUAL-4` is resolved part-by-part, and a plural like `LLMs`/`ABoxes`
falls back to its stem. So defining `LTL` once clears every `LTL/*` it ever appears in — the class
is discharged, not the instance. (A whole compound CAN still be defined as a unit — e.g. `DO-178C`,
`MC/DC` — and that takes precedence.) Ordinary Title-Case / lowercase words inside a compound
(`Safety-Invariant`, `AGM-rational`) carry no acronym and never trip the gate.

Empty violations ⇒ clean. Non-empty ⇒ exit 1. Run from repo root:  python3 gates/doc-legibility/check.py

SCOPE (maintainer ruling 2026-07-07, finding 48 [C15]): ALL tracked human-readable `*.md`
— "the gate ought to apply to any documentation a human might read", not just the survey +
architecture through-line it was born on. The definition surfaces (GLOSSARY.md / terms.md /
the survey KEY.md) stay global and are excluded from scope (they DEFINE, they are not gated).
"""
import re, sys, os, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SURVEY = os.path.join(ROOT, "research/obligations-formalisms-survey")
# Definition surfaces (a token defined here counts as defined everywhere in scope). terms.md is the
# persistent, hand-authored glossary; KEY.md is the survey's generated legend; GLOSSARY.md the root SSOT.
DEF_FILES = [os.path.join(ROOT, "gates/doc-legibility/terms.md"),
             os.path.join(SURVEY, "KEY.md"), os.path.join(ROOT, "GLOSSARY.md")]
_DEF_BASENAMES = {"terms.md", "KEY.md", "GLOSSARY.md"}


def _tracked_md():
    """Every git-tracked *.md under the repo — the widened scope (finding 48)."""
    r = subprocess.run(["git", "-C", ROOT, "ls-files", "*.md"],
                       capture_output=True, text=True, check=True)
    return [os.path.join(ROOT, ln) for ln in r.stdout.splitlines() if ln.strip()]


# Scope: every tracked *.md whose acronyms must all be defined, minus the definition surfaces,
# minus judgment/** — declared HISTORY (OPERATING-CARD.md: "predecessor era — history unless a
# current spec cites it"), the same principled exclusion gates/link_integrity.py uses, applied
# here consistently (2026-07-11 doc-legibility-indictment assessment, BACKLOG disposition).
_EXCLUDE_DIR_PREFIXES = ("judgment/",)
SCOPE = [f for f in _tracked_md()
         if os.path.basename(f) not in _DEF_BASENAMES
         and not any(os.path.relpath(f, ROOT).startswith(p) for p in _EXCLUDE_DIR_PREFIXES)]
ALLOW = os.path.join(ROOT, "gates/doc-legibility/allowlist.txt")

TOKEN = re.compile(r'[A-Za-z0-9]+(?:[-/][A-Za-z0-9]+)*\+?')

def atomic_parts(tok):
    """Split a surface token into atomic sub-tokens on '-' and '/' (drop a trailing '+')."""
    return [p for p in re.split(r'[-/]', tok.rstrip('+')) if p]

def is_acronymish(part):
    """An atomic part that looks like an acronym / jargon-code: ≥2 uppercase letters.
    This deliberately excludes ordinary lowercase or Title-Case words (`rational`, `Invariant`),
    which carry at most one uppercase and so are never flagged."""
    if len(part) < 2 or len(part) > 16 or part.isdigit():
        return False
    return sum(1 for c in part if c.isupper()) >= 2

def part_defined(part, defined):
    """A part is defined if it (or its singular stem, dropping a trailing lowercase 's'/'es') is."""
    if part in defined:
        return True
    if part.endswith('es') and part[:-2] in defined:
        return True
    # Acronym plural: a trailing lowercase 's' on an all-caps stem (LLMs→LLM, APIs→API, AFs→AF).
    # The char before the 's' must be uppercase — i.e. the body of an acronym — so we never strip
    # the 's' off an ordinary lowercased word.
    if part.endswith('s') and part[-2].isupper() and part[:-1] in defined:
        return True
    return False

def unresolved_parts(tok, defined):
    """Return the acronym-ish atomic parts of `tok` that are neither defined nor allowlisted.
    A whole-token match (e.g. an allowlisted compound or a unit-defined standard like `DO-178C`)
    short-circuits to resolved."""
    t = tok.rstrip('+')
    if tok in defined or t in defined:
        return []
    return [p for p in atomic_parts(t) if is_acronymish(p) and not part_defined(p, defined)]

def strip_for_prose(line):
    """Drop markdown link/image TARGETS and inline-code spans; keep link TEXT and prose."""
    line = re.sub(r'\]\([^)]*\)', ']', line)      # ](url-or-anchor) -> ]
    line = re.sub(r'<a id="[^"]*">.*?</a>', '', line)
    parts = line.split('`')
    return ' '.join(parts[i] for i in range(0, len(parts), 2))   # even = outside inline code

def tokens_of(path, prose_only=True):
    out = []
    fence = False
    for ln, line in enumerate(open(path, encoding='utf-8'), 1):
        if line.lstrip().startswith('```'):
            fence = not fence; continue
        if fence:
            continue
        text = strip_for_prose(line) if prose_only else line
        for m in TOKEN.finditer(text):
            out.append((m.group(0), ln))
    return out

def defined_set():
    d = set()
    for f in DEF_FILES:
        if not os.path.exists(f):
            continue
        txt = open(f, encoding='utf-8').read()
        for bold in re.findall(r'\*\*([^*]+)\*\*', txt):          # every bolded definition lead
            for m in TOKEN.finditer(bold):
                d.add(m.group(0))
        for aid in re.findall(r'<a id="([^"]+)"></a>', txt):      # anchors (obligation codes etc.)
            d.add(aid.upper()); d.add(aid)
    if os.path.exists(ALLOW):
        for line in open(ALLOW, encoding='utf-8'):
            line = line.split('#', 1)[0].strip()
            if line:
                d.add(line)
    return d

def main():
    defined = defined_set()
    violations = {}   # atomic token -> list of (file, line)
    for f in SCOPE:
        rel = os.path.relpath(f, ROOT)
        for tok, ln in tokens_of(f):
            for part in unresolved_parts(tok, defined):   # report the atomic acronym, not the compound
                violations.setdefault(part, []).append((rel, ln))
    if not violations:
        print(f"doc-legibility: clean ✓  ({len(SCOPE)} docs, {len(defined)} defined/allowlisted tokens)")
        print(f"  excluded: judgment/** — declared history (OPERATING-CARD.md)")
        return 0
    print(f"doc-legibility: {len(violations)} undefined acronym(s) across {len(SCOPE)} docs — define in "
          f"gates/doc-legibility/terms.md or add to gates/doc-legibility/allowlist.txt")
    print(f"  excluded: judgment/** — declared history (OPERATING-CARD.md)\n")
    for tok in sorted(violations, key=lambda t: (-len(violations[t]), t)):
        locs = violations[tok]
        where = ", ".join(f"{r}:{l}" for r, l in locs[:3]) + (" …" if len(locs) > 3 else "")
        print(f"  {tok:16s} ×{len(locs):<3d} {where}")
    return 1

if __name__ == "__main__":
    sys.exit(main())
