#!/usr/bin/env python3
"""compound_nominal_scan2 — EXPERIMENT, NOT A WIRED GATE (second attempt; supersedes-or-
confirms vestigial_documentation/design/ORCH-COMPOUND-NOMINAL-DETECTION.md — the companion design note is
vestigial_documentation/design/ORCH-COMPOUND-NOMINAL-DETECTION-2.md).

Ranked, report-only static detectors for two defect classes in LLM-authored prose:

  CLASS 1 — coined noun-noun compounds whose inter-noun relation is unrecoverable to a
            zero-context reader (specimen: "trust story").
  CLASS 2 — table label-column type incoherence: an ill-typed element in a structured
            product (specimen: the original KR section-5 table, header "capability for a
            Haiku-tier consumer" over rows two of which are not capabilities).

DESIGN POSTURE (differences from the first attempt, tools/experiments/compound_nominal_scan.py):

  * RANKED top-K output with a stated scoring function, never a binary red/green verdict —
    the house's cry-wolf history (gates/doc-legibility/README.md) rules out un-measured
    binary gating, and the maintainer's commission explicitly asks for measured-precision
    ranking instead.
  * The first attempt derived its noun lexicon FROM the corpus (a word is a noun if seen in
    a determiner slot), which made it structurally blind to exactly the rare heads that mark
    the defect ("story" never determinered => "trust story" never emitted). This tool
    INVERTS that signal (angle B: a head that lives only inside compounds is suspicious) and
    additionally EMBEDS its lexicons as in-file data (angles A, C) so rarity in the corpus
    cannot blind them.
  * Multiple independent angles, each with its own soundness story, compared side by side.

THE ANGLES AND THEIR SOUNDNESS STORIES (what each rule CAN and CANNOT conclude):

  A  metaphor-head x definition-surface (CLASS 1).
     CAN conclude: "this bigram's head noun is in a curated lexicon of Claude-idiom
     metaphor heads (story/posture/journey/...), and the bigram resolves to no definition
     surface (GLOSSARY.md headings, terms.md bold leads, inline gloss in the same doc) and
     is not a lexicalized English compound."  CANNOT conclude: that the relation is
     unrecoverable in general — a metaphor-headed compound can still be legible in context.
     The lexicon is finite and curated; compounds with heads outside it are invisible to
     this angle BY CONSTRUCTION (stated incompleteness). Precision is measured, not claimed.

  B  borrowed-head statistic (CLASS 1).
     CAN conclude: "this head noun's corpus life is (almost) exclusively as the head of
     compounds — it (nearly) never appears as a determinered standalone noun — which is the
     statistical signature of a word imported for a borrowed/figurative sense."  CANNOT
     conclude: defectiveness; a legitimate technical head can share the signature. Pure
     corpus statistics, no semantics, no curated list. This is the first attempt's blindness
     turned into its detector.

  C  embedded-POS-lite N+N novelty ranking (CLASS 1; the control angle).
     CAN conclude: "this bigram is N+N-shaped under an embedded closed-class filter and is
     rare in the corpus."  CANNOT conclude: anything about relation recoverability — Downing
     (1977): the relation set of novel compounds is not finitely enumerable, so N+N shape
     detection is NOT defect detection. Included as the honest re-run of the first
     attempt's architecture with embedded (not corpus-derived) lexicons, to measure whether
     the first verdict was an artifact of the corpus-derived lexicon or of the approach.

  D  form-parallelism on table label columns (CLASS 2).
     CAN conclude: "this label column mixes surface grammatical forms (verb-initial
     imperative vs nominal vs question vs gerund) at a stated majority/minority split."
     CANNOT conclude: type incoherence. Form-parallelism is a one-sided proxy for
     type-parallelism: mixed forms => suspicion worth a human read; uniform forms => NOTHING
     (five nominals can still mix capabilities with costs). The classifier itself is a
     heuristic over embedded verb/determiner lists and is measured, not assumed.

  E  header-anchored form typing (CLASS 2).
     CAN conclude: "the label column's header head-noun is in a small declared type lexicon
     (capability/operation/step/... expect action-form labels; directory/file/term/...
     expect nominal labels; question expects question-form), and row R's surface form does
     not match the header's declared kind."  CANNOT conclude: semantic inhabitation — it
     type-checks FORM against the header, not meaning. Fires only on lexicon hits (stated
     incompleteness); silent on headers outside the lexicon.

  F  empty-label-column-header lint (CLASS 2, carried over from attempt 1).
     Sound structural fact: a label column with no header declares no type to check against.
     Zero judgment involved.

REPORT-ONLY BY DESIGN. Nothing here exits non-zero on findings; the output is a ranked list
for a human (or an LLM reviewer) to judge. Stdlib only (the no-lazy-imports law and the
gates/ dependency posture; a real POS tagger is a maintainer dependency decision, argued in
the design note, not taken here).

FIRING TELEMETRY (ledger row 337, maintainer directive, unblocked 2026-07-14). Adoption of
this detector is conditional on tracking EVERY fired candidate, every run -- the maintainer's
own words: "the accumulated firing data INCLUDING false positives becomes the dataset [for] a
more general, disciplined solution" (the method may be biased; the specimen that proved it was
known to its builder). `--tables` and the default CLASS-1 scan each append one compressed
record per fired candidate to tools/experiments/results/scan2-firings.jsonl via
scan2_firings.py, unconditionally -- recording is not a flag, so a real firing cannot happen
unrecorded, and it is NOT bounded to --top/--dump-all: an earlier revision of this code bounded
recording to the printed top-K on the theory that a candidate no reviewer saw was never a
"finding"; an out-of-frame hack-rationalization review caught that this survivorship-biases the
dataset toward whatever the CURRENT, unproven scoring function already favors -- exactly what
the telemetry exists to let a later pass correct -- so the bound was removed. The disclosed
cost: on this corpus the internal candidate pool commonly runs into five figures per invocation
(angle C is a documented flood, "the measured-flood control angle", no defect-detection claim
of its own -- see angle C's soundness story above); that volume is the dataset's signal, not
noise, and if it becomes an operational (repo-size) problem, retention/rotation is a real
follow-up question for the maintainer, not a reason to pre-filter today. See scan2_firings.py's
own docstring for the schema, the disposition-backfill workflow, and the one stated mode
exclusion (--specimens, a recall self-test over synthetic/historical text, is not recorded at
all -- unrelated to the surfaced/full question, since specimen text is not the live corpus).

Run (from the repo root):
  python3 tools/experiments/compound_nominal_scan2.py                 # CLASS 1 ranked scan
  python3 tools/experiments/compound_nominal_scan2.py --tables        # CLASS 2 table scan
  python3 tools/experiments/compound_nominal_scan2.py --specimens     # recall on the
        pre-registered specimen set (reads the pre-repair KR doc out of git history)
  python3 tools/experiments/compound_nominal_scan2.py --top 50        # widen the ranked list
  python3 tools/experiments/compound_nominal_scan2.py --angle C       # one angle in isolation
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

# firing telemetry (ledger row 337, unblocked by the 2026-07-14 detector-adoption decision,
# ledger row 658) -- imported, not reimplemented (ADR-0012 P1): this module's own cmd_class1/
# cmd_tables call it unconditionally so a real firing cannot happen unrecorded. See
# scan2_firings.py's own docstring for the schema and what is/isn't recorded.
from scan2_firings import record_class1_run, record_class2_run

REPO = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Corpus definition (printed, never silent)
# ---------------------------------------------------------------------------
EXCLUDE_PREFIXES = (
    "vestigial_documentation/",  # declared vestigial
    "judgment/",                 # frozen point-in-time transcripts (history, not live prose)
)
DEF_SURFACES = (
    "GLOSSARY.md",
    "gates/doc-legibility/terms.md",
    "vestigial_documentation/research/obligations-formalisms-survey/KEY.md",
)
# Files carrying the in-repo evidence-record marker are banked quoted-specimen collections
# (ADR-0017 Exceptions: quoted defects / point-in-time records), excluded and printed.
EXEMPT_MARKER = "doc-attest-exempt"

# The pre-repair KR document (specimen source), by blob: parent of the repair commit a4ef32d.
SPECIMEN_COMMIT = "b96a8c8"
SPECIMEN_PATH = "vestigial_documentation/design/ORCH-KR-TITRATION-EXPLORATION.md"

# ---------------------------------------------------------------------------
# Embedded lexicons — in-file data, deliberately NOT corpus-derived (see docstring).
# ---------------------------------------------------------------------------
DETERMINERS = {
    "the", "a", "an", "this", "that", "these", "those", "each", "every", "no", "any",
    "some", "all", "both", "either", "neither", "its", "their", "our", "your", "his",
    "her", "my", "whose", "another", "such", "one", "two", "three", "four", "five",
    "several", "many", "few", "most", "more", "less",
}
PREPOSITIONS = {
    "of", "in", "on", "for", "to", "by", "with", "from", "at", "as", "into", "onto",
    "over", "under", "per", "via", "about", "against", "between", "across", "through",
    "within", "without", "upon", "toward", "towards", "before", "after", "during",
    "beside", "behind", "above", "below", "near", "off", "out", "up", "down", "around",
}
FUNCTION_WORDS = DETERMINERS | PREPOSITIONS | {
    "and", "or", "but", "nor", "so", "yet", "if", "then", "else", "than", "because",
    "while", "when", "where", "how", "why", "who", "whom", "which", "what", "it", "they",
    "we", "you", "i", "he", "she", "them", "us", "him", "me", "is", "are", "was", "were",
    "be", "been", "being", "am", "do", "does", "did", "done", "have", "has", "had",
    "having", "will", "would", "shall", "should", "can", "could", "may", "might", "must",
    "not", "never", "always", "only", "also", "too", "very", "just", "still", "already",
    "here", "there", "now", "once", "twice", "again", "ever", "even", "thus", "hence",
    "therefore", "however", "moreover", "instead", "rather", "quite", "almost", "nearly",
    "itself", "themselves", "yourself", "himself", "herself", "myself", "ourselves",
    "something", "anything", "nothing", "everything", "someone", "anyone", "everyone",
    "none", "e.g", "i.e", "etc", "vs", "et", "al",
}
# Verbs that are (in this register) essentially never nouns.
VERBS_UNAMBIG = {
    "enumerate", "detect", "invoke", "verify", "describe", "define", "ensure", "confirm",
    "emit", "refuse", "resolve", "derive", "execute", "delete", "remove", "apply", "adopt",
    "examine", "evaluate", "generate", "provide", "produce", "receive", "require",
    "declare", "decide", "deliver", "explain", "extract", "identify", "ignore", "include",
    "exclude", "prevent", "propose", "publish", "quantify", "recognize", "reconcile",
    "reject", "restate", "restore", "retrieve", "satisfy", "select", "specify",
    "submit", "summarize", "suppress", "survive", "translate", "validate",
    "assert", "assume", "attach", "avoid", "become", "believe",
    "carry", "catch", "choose", "cite", "collect", "compare", "compute", "consider",
    "contain", "convert", "create", "depend", "expect", "fetch", "follow", "happen",
    "implement", "inherit", "inspect", "install", "introduce", "learn", "maintain",
    "mention", "obtain", "occur", "perform", "permit", "precede", "prefer", "prepare",
    "presume", "print", "push", "reach", "recover", "reduce",
    "refactor", "regenerate", "render", "repair", "replace", "represent", "reproduce",
    "rerun", "retire", "reuse", "rewrite", "route", "send", "ship",
    "solve", "spawn", "steer", "strip", "teach", "tell", "throw", "touch",
    "treat", "understand", "unpack", "untangle", "violate", "write",
    "accept", "add", "allow", "ask", "attest",
    "build", "bring", "clarify", "communicate", "conclude", "connect", "constrain",
    "construct", "consume", "continue", "debug", "demonstrate", "deny", "deprecate",
    "destroy", "die", "differ", "disambiguate", "discover", "dispose", "distribute",
    "divide", "earn", "eat", "elevate", "eliminate", "employ",
    "enable", "encode", "enforce", "enter", "establish", "exceed", "exist", "expand",
    "expire", "explore", "expose", "extend", "fall", "feed", "fill",
    "find", "finish", "forbid", "forget",
    "freeze", "gather", "give", "go", "grow", "guarantee",
    "hunt", "improve", "infer", "inform", "inject",
    "insert", "intend", "intercept", "interpret", "isolate", "keep",
    "know", "launch", "leave", "let", "lift",
    "lose", "make", "manage", "mean", "meet", "migrate", "modify",
    "narrow", "obey", "observe", "operate", "orient",
    "overwrite", "pay", "persist", "pick", "populate",
    "predict", "preserve", "presuppose", "pretend",
    "promote", "prove", "pull", "put", "govern",
}

# Noun-or-verb words: common in both roles; a bigram starting with one of these is only a
# verb phrase if the following context says so (see classify_label / class-1 filters).
VERBS_AMBIG = {
    "look", "run", "check", "trust", "cost", "work", "read", "write", "flag", "use",
    "state", "record", "report", "review", "audit", "test", "claim", "mark", "name",
    "note", "change", "call", "commit", "gate", "hook", "stamp", "witness", "judge",
    "answer", "question", "measure", "scan", "probe", "merge", "fork", "mint", "file",
    "ship", "land", "queue", "trigger", "sweep", "block", "guard", "release", "attempt",
    "count", "cut", "drop", "edit", "fix", "force", "handle", "hold", "hunt", "join",
    "keep", "kill", "launch", "lead", "list", "load", "match", "miss", "mix", "move",
    "need", "open", "order", "own", "parse", "pass", "pin", "place", "point", "pose",
    "post", "process", "demand", "discharge", "cover", "cross", "close", "commission",
    "complete", "correct", "fire", "gain", "fail", "author", "build", "catch", "clean",
    "help", "walk", "talk", "start", "stop", "end", "set", "get", "take", "turn", "show",
    "stand", "step", "act", "aim", "bank", "base", "seed",
}
# Common adjectives the suffix rules miss (zero-derived / irregular).
ADJECTIVES = {
    "live", "fresh", "same", "own", "full", "new", "real", "raw", "dead", "clean",
    "dirty", "high", "low", "big", "small", "large", "long", "short", "open", "closed",
    "false", "true", "wrong", "right", "hard", "soft", "safe", "unsafe", "whole",
    "single", "double", "current", "prior", "next", "last", "first", "second", "third",
    "other", "main", "top", "bottom", "inner", "outer", "deep", "shallow", "broad",
    "narrow", "cheap", "quick", "slow", "early", "late", "strong", "weak", "good", "bad",
    "best", "worst", "better", "worse", "old", "young", "free", "busy", "ready", "clear",
    "plain", "bare", "blind", "cold", "hot", "warm", "dark", "light", "loud", "quiet",
    "honest", "exact", "precise", "subtle", "overall", "foreign", "common", "rare",
    "frequent", "separate", "distinct", "explicit", "implicit", "concrete", "robust",
    "silent", "stale", "flat", "rich", "thin", "thick", "wide", "tight", "loose", "sound",
    "whole", "empty", "blank", "senior", "junior", "human", "mere", "sole", "dual",
    "extra", "meta", "sub", "non", "pre", "post", "anti", "self", "half", "future",
    "present", "past", "downstream", "upstream", "standalone", "standing", "wholesale",
}
ADJ_SUFFIXES = ("al", "ive", "ous", "ic", "ful", "less", "able", "ible", "ary", "ory", "est",
                "ent", "ant", "ish", "like", "ed", "ing", "ly", "most", "wise")

# Abstract-relation modifiers that boost angle A (the "trust" in "trust story"):
# abstract nouns naming attitudes/valuations whose jamming against a metaphor head is the
# canonical Claude-idiom shape.
ABSTRACT_MODIFIERS = {
    "trust", "safety", "risk", "truth", "blame", "consent", "confidence", "assurance",
    "belief", "doubt", "hope", "fear", "intent", "care", "faith", "honesty", "quality",
    "health", "maturity", "courage", "comfort", "pain", "shame", "guilt", "pride",
    "luck", "success", "failure", "victory", "defeat", "value", "worth", "merit",
    "privacy", "security", "liability", "legitimacy", "credibility", "authority",
}

# Angle A: curated Claude-idiom metaphor heads, weighted. Enumerated from (i) the
# commission's seed list, (ii) a corpus sweep for figurative heads, (iii) the authoring
# model's own knowledge of its idiom. Finite and stated: heads outside this list are
# invisible to angle A.
METAPHOR_HEADS = {
    # weight 3 — narrative/somatic/artistic heads, near-always figurative in tech prose
    "story": 3, "journey": 3, "dance": 3, "choreography": 3, "muscle": 3, "texture": 3,
    "tapestry": 3, "symphony": 3, "orchestra": 3, "melody": 3, "song": 3, "poem": 3,
    "poetry": 3, "dna": 3, "heartbeat": 3, "soul": 3, "spirit": 3, "mood": 3,
    "flavor": 3, "flavour": 3, "aroma": 3, "taste": 3, "cathedral": 3, "garden": 3,
    "zoo": 3, "constellation": 3, "galaxy": 3, "theater": 3, "theatre": 3, "ballet": 3,
    "narrative": 3, "saga": 3, "chapter": 2, "personality": 3, "psyche": 3,
    # weight 2 — physical/spatial heads, frequently figurative, sometimes house-legit
    "posture": 2, "landscape": 2, "terrain": 2, "fabric": 2, "gravity": 2,
    "geometry": 2, "altitude": 2, "spine": 2, "skeleton": 2, "anatomy": 2,
    "currency": 2, "hygiene": 2, "pulse": 2, "rhythm": 2, "appetite": 2, "diet": 2,
    "metabolism": 2, "ecosystem": 2, "weather": 2, "climate": 2, "temperature": 2,
    "friction": 2, "horizon": 2, "compass": 2, "footprint": 2, "fingerprint": 2,
    "silhouette": 2, "shadow": 2, "mirror": 2, "lens": 2, "prism": 2, "gesture": 2,
    "reflex": 2, "instinct": 2, "appetite": 2, "hunger": 2, "thirst": 2, "wound": 2,
    "scar": 2, "disease": 2, "malady": 2, "medicine": 2, "cure": 2, "therapy": 2,
    "surgery": 2, "autopsy": 2, "archaeology": 2, "excavation": 2, "gardening": 2,
    # weight 1 — heads with heavy legitimate house use; flagged faintly, whitelist-rescued
    "surface": 1, "register": 1, "key": 1, "frame": 1, "shape": 1, "budget": 1,
    "debt": 1, "tax": 1, "price": 1, "cost": 1, "bar": 1, "ceiling": 1, "floor": 1,
}

# Lexicalized English compounds (relation frozen by convention; never defects).
LEXICALIZED = {
    "success story", "user story", "cover story", "short story", "end user", "use case",
    "edge case", "corner case", "olive oil", "state machine", "machine learning",
    "unit test", "test suite", "source code", "code review", "root cause", "world war",
    "north star", "rule of thumb", "user interface", "command line", "type checker",
    "model checker", "sanity check", "smoke test", "shell script", "git blame",
}

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")
# Segment breakers: any punctuation that carries relation information a bigram must not
# cross (the first attempt's "artifacts (spec + proof)" -> "artifacts spec proof" artifact).
SEGMENT_SPLIT_RE = re.compile(r"[.,;:()\[\]{}<>\"“”‘’|/\\!?=+*&%$#@~^]|—|–|->|=>|`|'s\b|\.\.\.")


def is_adjective(w: str) -> bool:
    lw = w.lower()
    if lw in ADJECTIVES:
        return True
    if "-" in lw:  # hyphenated modifiers ("Haiku-tier", "zero-context") act adjectivally
        return True
    return lw.endswith(ADJ_SUFFIXES) and len(lw) > 4


def git_lines(*args: str) -> list[str]:
    out = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, check=True)
    return out.stdout.splitlines()


def corpus_paths() -> tuple[list[Path], list[str]]:
    """Tracked *.md minus exclusions. Returns (paths, printed_exclusion_notes)."""
    notes = []
    files = [f for f in git_lines("ls-files", "*.md")]
    keep: list[Path] = []
    for f in files:
        if f.startswith(EXCLUDE_PREFIXES):
            continue
        if f in DEF_SURFACES:
            continue
        p = REPO / f
        try:
            head = p.read_text(encoding="utf-8", errors="replace")[:600]
        except OSError:
            continue
        if EXEMPT_MARKER in head:
            notes.append(f"excluded (evidence-record marker '{EXEMPT_MARKER}'): {f}")
            continue
        keep.append(p)
    notes.insert(0, f"excluded prefixes: {', '.join(EXCLUDE_PREFIXES)}; "
                    f"definition surfaces: {', '.join(DEF_SURFACES)}")
    return keep, notes


# The stamp-block regex is assembled from parts so this file never contains the literal
# marker text: the provenance stamper is known to corrupt files carrying its own marker
# (ADR-0011, 2026-07-02 amendment — witnessed again while authoring this file).
_MARK = "PROVENANCE-STAMP"
STAMP_RE = re.compile(r">>> " + _MARK + r" >>>.*?<<< " + _MARK + r" <<<", re.S)
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
FENCE_RE = re.compile(r"^(```|~~~)")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
URL_RE = re.compile(r"https?://\S+")
LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def strip_markdown(text: str) -> list[str]:
    """Markdown -> prose lines (same line numbering as the source; code lines blanked)."""
    text = STAMP_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    text = COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    lines, out, in_fence = text.splitlines(), [], False
    for ln in lines:
        if FENCE_RE.match(ln.strip()):
            in_fence = not in_fence
            out.append("")
            continue
        if in_fence:
            out.append("")
            continue
        ln = INLINE_CODE_RE.sub(" , ", ln)   # code spans are segment breaks, not words
        ln = URL_RE.sub(" ", ln)
        ln = LINK_RE.sub(r"\1", ln)
        ln = ln.replace("**", " ").replace("*", " ").replace("__", " ")
        out.append(ln)
    return out


def segments(line: str):
    for seg in SEGMENT_SPLIT_RE.split(line):
        toks = TOKEN_RE.findall(seg)
        if toks:
            yield toks


# ---------------------------------------------------------------------------
# Definition surfaces (whitelist SSOT) + inline-gloss detection
# ---------------------------------------------------------------------------
def load_defined_terms() -> set[str]:
    terms: set[str] = set()
    heading_re = re.compile(r"^#{2,4}\s+(.*)$")
    bold_re = re.compile(r"\*\*([^*]+)\*\*")
    for rel in DEF_SURFACES:
        p = REPO / rel
        if not p.exists():
            continue
        for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
            m = heading_re.match(ln)
            if m and rel.endswith("GLOSSARY.md"):
                terms.add(re.sub(r"[`*]", "", m.group(1)).strip().lower())
            for b in bold_re.findall(ln):
                terms.add(re.sub(r"[`*]", "", b).strip().lower())
    return {t for t in terms if t}


def singular(s: str) -> str:
    return s[:-1] if s.endswith("s") and not s.endswith("ss") else s


def is_defined(compound: str, defined: set[str]) -> bool:
    c = compound.lower()
    return c in defined or singular(c) in defined or c in LEXICALIZED


GLOSS_NEAR_RE_TMPL = r"\b%s\b\s*(\(|—|–|:\s|\bmeans\b|\bi\.e\.)"


def inline_glossed(compound: str, doc_text: str) -> bool:
    pat = GLOSS_NEAR_RE_TMPL % re.escape(compound)
    return re.search(pat, doc_text, re.I) is not None


# ---------------------------------------------------------------------------
# CLASS 1 — corpus statistics + the three angles
# ---------------------------------------------------------------------------
class CorpusStats:
    def __init__(self):
        self.det_slot = Counter()       # token seen right after a determiner/possessive
        self.head_uses = Counter()      # token seen as 2nd element of an N+N-ish pair
        self.pair_count = Counter()     # (w, h) occurrence count
        self.pair_docs = defaultdict(set)

    def feed(self, doc_id: str, toks: list[str]):
        low = [t.lower() for t in toks]
        for i, t in enumerate(low):
            if i > 0 and low[i - 1] in DETERMINERS:
                self.det_slot[t] += 1
        for i in range(len(low) - 1):
            w, h = low[i], low[i + 1]
            if w in FUNCTION_WORDS or h in FUNCTION_WORDS:
                continue
            if len(w) < 3 or len(h) < 3:
                continue
            if is_adjective(w) or w in VERBS_UNAMBIG or h in VERBS_UNAMBIG:
                continue
            if w.endswith("s") and (w[:-1] in VERBS_UNAMBIG or w[:-2] in VERBS_UNAMBIG):
                continue  # 3rd-person verb form as "modifier" ("produces theater")
            if toks[i][0].isupper() or toks[i + 1][0].isupper():
                continue  # proper nouns / Title-Case house names are out of the defect profile
            self.head_uses[h] += 1
            self.pair_count[(w, h)] += 1
            self.pair_docs[(w, h)].add(doc_id)

    def borrowed_ratio(self, h: str) -> float:
        return self.head_uses[h] / (self.det_slot[h] + 1)


def scan_class1(docs: dict[str, str], defined: set[str], angles: str = "ABC"):
    """Returns (stats, findings) where findings is a list of dicts, one per distinct pair."""
    stats = CorpusStats()
    doc_lines: dict[str, list[str]] = {}
    for doc_id, text in docs.items():
        lines = strip_markdown(text)
        doc_lines[doc_id] = lines
        for ln in lines:
            for toks in segments(ln):
                stats.feed(doc_id, toks)

    findings: dict[tuple[str, str], dict] = {}

    def occurrence_sites(pair):
        sites = []
        w, h = pair
        pat = re.compile(r"\b%s\s+%s\b" % (re.escape(w), re.escape(h)), re.I)
        for doc_id in stats.pair_docs[pair]:
            for n, ln in enumerate(doc_lines[doc_id], 1):
                if pat.search(ln):
                    sites.append(f"{doc_id}:{n}")
        return sites

    for (w, h), cnt in stats.pair_count.items():
        compound = f"{w} {h}"
        if is_defined(compound, defined):
            continue
        glossed = any(inline_glossed(compound, docs[d]) for d in stats.pair_docs[(w, h)])
        if glossed:
            continue
        rec = {"pair": compound, "count": cnt, "docs": len(stats.pair_docs[(w, h)]),
               "angles": {}, "score": 0.0}

        # --- angle A: metaphor head ---
        if "A" in angles and h in METAPHOR_HEADS:
            wgt = METAPHOR_HEADS[h]
            a = 2.0 * wgt
            if w in ABSTRACT_MODIFIERS:
                a += 2.0
            if stats.borrowed_ratio(h) >= 2.0:
                a += 1.0
            if len(stats.pair_docs[(w, h)]) <= 2:
                a += 1.0
            rec["angles"]["A"] = round(a, 2)

        # --- angle B: borrowed-head statistic ---
        if "B" in angles:
            br = stats.borrowed_ratio(h)
            if br >= 2.0 and stats.det_slot[h] <= 4 and stats.head_uses[h] >= 2 \
                    and not is_adjective(h) and cnt <= 6:
                rec["angles"]["B"] = round(min(br, 12.0), 2)

        # --- angle C: embedded-POS-lite N+N novelty (control) ---
        if "C" in angles:
            vp_shape = (w in VERBS_AMBIG and (h.endswith("s") or h in DETERMINERS))
            if not vp_shape and w not in VERBS_AMBIG or (w in VERBS_AMBIG and h in METAPHOR_HEADS):
                # novelty score: rare pairs rank high; flood expected and measured
                rec["angles"]["C"] = round(3.0 / cnt, 2)

        if rec["angles"]:
            # master score: A dominates (curated precision angle), B next, C tail
            rec["score"] = (rec["angles"].get("A", 0.0) * 10
                            + rec["angles"].get("B", 0.0) * 3
                            + rec["angles"].get("C", 0.0))
            rec["sites"] = occurrence_sites((w, h))[:6]
            findings[(w, h)] = rec

    ranked = sorted(findings.values(), key=lambda r: (-r["score"], r["pair"]))
    return stats, ranked


# ---------------------------------------------------------------------------
# CLASS 2 — table parsing, form classifier, angles D/E/F
# ---------------------------------------------------------------------------
TABLE_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
ALIGN_RE = re.compile(r"^\s*\|?\s*:?-{3,}.*$")

DET_QUANT = DETERMINERS | {"what", "which"}
PARTICLES = {"up", "out", "off", "down", "over", "in", "on", "away", "back", "through"}
WH_STARTS = {"what", "which", "who", "whom", "whose", "how", "why", "when", "where",
             "does", "do", "is", "are", "can", "should", "will", "would", "may"}
GERUND_NOT = {"thing", "string", "king", "ring", "nothing", "something", "anything",
              "everything", "spring", "wing", "sibling", "warning", "evening", "morning"}

ACTION_HEADS = {"capability", "capabilities", "operation", "operations", "action",
                "actions", "step", "steps", "task", "tasks", "command", "commands",
                "procedure", "procedures", "verb", "verbs", "move", "moves",
                "activity", "activities", "recipe", "recipes"}
NOMINAL_HEADS = {"directory", "directories", "file", "files", "mechanism", "mechanisms",
                 "artifact", "artifacts", "term", "terms", "name", "names", "field",
                 "fields", "kind", "kinds", "lens", "lenses", "milestone", "milestones",
                 "phase", "phases", "criterion", "criteria", "tier", "tiers", "item",
                 "items", "member", "members", "column", "columns", "table", "tables",
                 "document", "documents", "doc", "docs", "path", "paths", "tool",
                 "tools", "gate", "gates", "hook", "hooks", "surface", "surfaces",
                 "layer", "layers", "component", "components", "property", "properties",
                 "resource", "resources", "concept", "concepts", "quantity", "quantities"}
QUESTION_HEADS = {"question", "questions"}


def classify_label(label: str) -> str:
    """Surface-form classifier: VP | NOM | QUESTION | GERUND | CODE | EMPTY.
    Heuristic over embedded lists; its errors are part of the measured precision."""
    raw = label.strip()
    if not raw:
        return "EMPTY"
    if re.fullmatch(r"`[^`]*`.*", raw) or raw.startswith("`"):
        return "CODE"
    # strip emphasis markers ONLY (* and backtick). '_' stays: deleting it glues code
    # identifiers ("tlab_finding" -> "tlabfinding", a fake gerund — a measured bug).
    stripped = re.sub(r"[*`]", "", raw).strip()
    stripped = re.sub(r"^\([^)]*\)\s*", "", stripped)  # leading "(reuse) x" annotation
    toks = [t.lower() for t in TOKEN_RE.findall(stripped)]
    if not toks:
        return "CODE"
    if stripped.endswith("?") or toks[0] in WH_STARTS:
        return "QUESTION"
    t0 = toks[0]
    if len(toks) == 1:
        return "NOM"  # a single word's form is underdetermined ("Build", "MIGRATE")
    if "-" in t0 or "_" in stripped.split()[0]:
        return "NOM"  # hyphenated/underscored first tokens are modifiers/identifiers
    if t0.endswith("ing") and t0 not in GERUND_NOT and len(t0) > 5:
        # gerund HEAD only when followed by det/prep ("running the sweep");
        # otherwise a gerund MODIFIER ("tooling discipline") — nominal.
        if toks[1] in DET_QUANT or toks[1] in PREPOSITIONS:
            return "GERUND"
        return "NOM"
    if t0 in VERBS_UNAMBIG:
        return "VP"
    if t0 in VERBS_AMBIG:
        t1 = toks[1]
        if t1 in DET_QUANT:
            return "VP"
        if t1 in PARTICLES and (len(toks) == 2 or toks[2] in DET_QUANT or len(toks) > 2):
            return "VP"
        if is_adjective(t1) and len(toks) > 2:
            return "VP"          # "run full sweep"
        if t1 == "to":
            return "NOM"         # "cost to stand up" — noun + infinitive complement
        return "NOM"
    return "NOM"


def header_expectation(header: str):
    """The header's TYPE-DECLARING word is the head of its first noun phrase — the last
    content word before the first preposition ('capability for a Haiku-tier consumer' ->
    'capability'; 'Omega capability' -> 'capability'), not the first content word."""
    toks = [t.lower() for t in TOKEN_RE.findall(re.sub(r"[*`]", "", header))]
    phrase = []
    for t in toks:
        if t in PREPOSITIONS or t in {"per", "answered"}:
            break
        phrase.append(t)
    head = None
    for t in reversed(phrase):
        if t in FUNCTION_WORDS or is_adjective(t):
            continue
        head = t
        break
    if head in ACTION_HEADS:
        return head, {"VP", "GERUND"}
    if head in QUESTION_HEADS:
        return head, {"QUESTION"}
    if head in NOMINAL_HEADS:
        return head, {"NOM", "CODE"}
    return None, None


def parse_tables(lines: list[str]):
    """Yield (start_line_no, header_cells, body_rows[list[list[str]]])."""
    i, n = 0, len(lines)
    while i < n - 1:
        m = TABLE_ROW_RE.match(lines[i])
        if m and ALIGN_RE.match(lines[i + 1] or ""):
            header = [c.strip() for c in m.group(1).split("|")]
            body, j = [], i + 2
            while j < n:
                mb = TABLE_ROW_RE.match(lines[j])
                if not mb:
                    break
                body.append([c.strip() for c in mb.group(1).split("|")])
                j += 1
            yield i + 1, header, body
            i = j
        else:
            i += 1


def scan_class2(docs: dict[str, str], min_rows: int = 3):
    findings = []
    for doc_id, text in docs.items():
        # tables live in raw text (code fences can contain pipe art; strip fences only)
        lines, in_fence, keep = text.splitlines(), False, []
        for ln in lines:
            if FENCE_RE.match(ln.strip()):
                in_fence = not in_fence
                keep.append("")
                continue
            keep.append("" if in_fence else ln)
        for lineno, header, body in parse_tables(keep):
            if len(body) < min_rows:
                continue
            h0 = header[0] if header else ""
            labels = [row[0] if row else "" for row in body]
            forms = [classify_label(lb) for lb in labels]
            rec = {"doc": doc_id, "line": lineno, "header": h0, "labels": labels,
                   "forms": forms, "hits": []}

            # F — empty header lint (sound structural fact)
            if not re.sub(r"[*_`\s]", "", h0):
                rec["hits"].append(("F", "label column has an EMPTY header — no type "
                                         "declared to check labels against", 1.0))

            judged = [f for f in forms if f not in ("EMPTY", "CODE")]
            # E — header-anchored form typing
            head_word, expected = header_expectation(h0)
            if expected:
                bad = [(lb, f) for lb, f in zip(labels, forms)
                       if f not in expected and f not in ("EMPTY", "CODE")]
                # An ill-typed ELEMENT lives in a mostly-coherent column. If (nearly)
                # every row "mismatches", the type lexicon is wrong about this table's
                # convention, not the table about its type — stay silent (measured:
                # capability-columns legitimately written as noun phrases exist).
                if bad and judged and len(bad) / len(judged) <= 0.5:
                    rec["hits"].append((
                        "E",
                        f"header head '{head_word}' expects {sorted(expected)} labels; "
                        f"mismatching rows: " + "; ".join(f"'{lb}' [{f}]" for lb, f in bad),
                        2.0 + len(bad)))

            # D — unanchored form parallelism
            if len(judged) >= 4:
                c = Counter(judged)
                if len(c) >= 2:
                    (maj, majn), = [c.most_common(1)[0]]
                    minn = len(judged) - majn
                    if 1 <= minn and minn / len(judged) <= 0.45:
                        minority = [(lb, f) for lb, f in zip(labels, forms)
                                    if f != maj and f not in ("EMPTY", "CODE")]
                        rec["hits"].append((
                            "D",
                            f"form mix: majority {maj} x{majn}, minority " +
                            "; ".join(f"'{lb}' [{f}]" for lb, f in minority),
                            1.0 + majn / len(judged)))
            if rec["hits"]:
                rec["score"] = sum(s for _, _, s in rec["hits"])
                findings.append(rec)
    findings.sort(key=lambda r: -r["score"])
    return findings


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------
def load_docs() -> tuple[dict[str, str], list[str]]:
    paths, notes = corpus_paths()
    docs = {str(p.relative_to(REPO)): p.read_text(encoding="utf-8", errors="replace")
            for p in paths}
    return docs, notes


def cmd_class1(args):
    docs, notes = load_docs()
    defined = load_defined_terms()
    stats, ranked = scan_class1(docs, defined, angles=args.angle or "ABC")
    # Telemetry scope: EVERY fired candidate, every run -- the full `ranked` list, not the
    # printed top-K (ledger row 337, maintainer's own words: "the accumulated firing data
    # INCLUDING false positives becomes the dataset [for] a more general, disciplined
    # solution"). An earlier revision of this code bounded recording to --top/--dump-all on
    # the theory that a candidate never shown to a reviewer was never a "finding"; an
    # out-of-frame hack-rationalization review caught the real cost of that: bounding to the
    # printed top-K survivorship-biases the dataset toward whatever the CURRENT (unproven,
    # that's the whole reason telemetry exists) score formula already favors, structurally
    # excluding exactly the low-ranked real defects and false positives the maintainer said he
    # wants preserved. Recording everything is the more literal, more general reading of the
    # commission and needs no maintainer decision -- only accepting its disclosed cost: on
    # this corpus the internal pool commonly runs into five figures (angle C is a documented
    # flood -- "measured-flood control angle", no defect-detection claim of its own -- see its
    # soundness story above), so a bare invocation appends a five-figure line count. That
    # volume IS the signal this dataset is for, not noise to pre-filter; if it becomes an
    # operational problem (repo size), retention/rotation is a real follow-up question for the
    # maintainer, not a reason to silently narrow what gets recorded today.
    # unconditional -- no flag skips this; a real fired finding cannot happen unrecorded
    # (ledger row 337). record_class1_run is a no-op write (0 lines) when ranked is empty.
    n_recorded = record_class1_run(ranked, args.angle or "ABC")
    print(f"compound_nominal_scan2 (EXPERIMENT, report-only): CLASS 1 ranked scan")
    for n in notes:
        print(f"  {n}")
    print(f"  corpus: {len(docs)} docs; defined terms (GLOSSARY/terms/KEY + lexicalized): "
          f"{len(defined)}+{len(LEXICALIZED)}")
    print(f"  distinct candidate pairs (any angle fired): {len(ranked)}")
    print(f"  firing telemetry: {n_recorded} record(s) appended to "
          f"tools/experiments/results/scan2-firings.jsonl (every fired candidate this run -- "
          f"see this module's docstring, 'FIRING TELEMETRY')")
    per_angle = Counter(a for r in ranked for a in r["angles"])
    print(f"  per-angle candidate counts: {dict(per_angle)}")
    print(f"\n  ranking function: score = 10*A + 3*B + C, where")
    print(f"    A = 2*head_weight + 2*[abstract modifier] + [borrowed head] + [<=2 docs]")
    print(f"    B = min(head_uses/(determinered_uses+1), 12) when ratio>=2, det<=4, pair<=6")
    print(f"    C = 3/pair_count (novelty tail — the measured-flood control angle)")
    top = args.top or 25
    print(f"\n  top {top}:")
    for i, r in enumerate(ranked[:top], 1):
        ang = ", ".join(f"{k}={v}" for k, v in sorted(r["angles"].items()))
        print(f"  {i:3}. [{r['score']:7.2f}] {r['pair']!r}  x{r['count']} in {r['docs']} doc(s)  ({ang})")
        for s in r["sites"][:3]:
            print(f"        {s}")
    if args.dump_all:
        print(f"\n  full ranked list ({len(ranked)}):")
        for i, r in enumerate(ranked, 1):
            print(f"  {i:5}. [{r['score']:7.2f}] {r['pair']!r} x{r['count']} "
                  f"({','.join(sorted(r['angles']))})")


def cmd_tables(args):
    docs, notes = load_docs()
    findings = scan_class2(docs)
    # unconditional -- no flag skips this; a real firing cannot happen unrecorded (ledger row
    # 337). record_class2_run is a no-op write (0 lines) when findings is empty.
    n_recorded = record_class2_run(findings)
    n_tables = 0
    for _doc, text in docs.items():
        n_tables += len(list(parse_tables(text.splitlines())))
    print("compound_nominal_scan2 (EXPERIMENT, report-only): CLASS 2 table scan")
    for n in notes:
        print(f"  {n}")
    print(f"  corpus: {len(docs)} docs, {n_tables} markdown tables")
    print(f"  flagged label columns: {len(findings)} (ranked; angle E > D > F by score)")
    print(f"  firing telemetry: {n_recorded} record(s) appended to "
          f"tools/experiments/results/scan2-firings.jsonl")
    for i, r in enumerate(findings, 1):
        print(f"\n  {i:3}. [{r['score']:.2f}] {r['doc']}:{r['line']}  header={r['header']!r}")
        print(f"       forms: {list(zip(r['labels'], r['forms']))}")
        for angle, msg, s in r["hits"]:
            print(f"       [{angle} +{s:.2f}] {msg}")


def cmd_specimens(args):
    print("compound_nominal_scan2 — recall on the PRE-REGISTERED specimen set")
    print(f"  specimen source: git {SPECIMEN_COMMIT}:{SPECIMEN_PATH} (pre-repair blob;")
    print(f"  the repair commit a4ef32d fixed both specimens, so the live corpus no longer")
    print(f"  carries them except as quoted evidence)")
    out = subprocess.run(["git", "show", f"{SPECIMEN_COMMIT}:{SPECIMEN_PATH}"],
                         cwd=REPO, capture_output=True, text=True, check=True)
    spec_text = out.stdout
    docs, _ = load_docs()
    defined = load_defined_terms()

    # S1 — CLASS 1: "trust story" must be emitted from the pre-repair doc.
    docs_plus = dict(docs)
    docs_plus["<SPECIMEN:pre-repair-KR>"] = spec_text
    _stats, ranked = scan_class1(docs_plus, defined)
    hit = next((i, r) for i, r in enumerate(ranked, 1) if r["pair"] == "trust story") \
        if any(r["pair"] == "trust story" for r in ranked) else None
    if hit:
        i, r = hit
        print(f"\n  S1 'trust story' (CLASS 1): CAUGHT — global rank {i} of {len(ranked)}, "
              f"score {r['score']:.2f}, angles {r['angles']}")
    else:
        print("\n  S1 'trust story' (CLASS 1): MISSED")

    # S2 — CLASS 2: the section-5 table must be flagged.
    findings = scan_class2({"<SPECIMEN:pre-repair-KR>": spec_text})
    s2 = [f for f in findings if "capability" in f["header"].lower()]
    if s2:
        f = s2[0]
        print(f"\n  S2 original KR sec-5 table (CLASS 2): CAUGHT — {f['doc']}:{f['line']}")
        print(f"     header={f['header']!r}")
        print(f"     forms: {list(zip(f['labels'], f['forms']))}")
        for angle, msg, s in f["hits"]:
            print(f"     [{angle} +{s:.2f}] {msg}")
    else:
        print("\n  S2 original KR sec-5 table (CLASS 2): MISSED")
        for f in findings:
            print(f"     (flagged instead: {f['header']!r} at {f['doc']}:{f['line']})")

    # Negative control: the REPAIRED table (live corpus) must NOT be flagged by E/D.
    live = scan_class2({k: v for k, v in docs.items() if k == SPECIMEN_PATH})
    flagged_repaired = [f for f in live if "question" in f["header"].lower()
                        or "capability" in f["header"].lower()]
    print(f"\n  negative control — repaired KR table in live corpus flagged: "
          f"{'YES (see below)' if flagged_repaired else 'NO (as it should be)'}")
    for f in flagged_repaired:
        for angle, msg, s in f["hits"]:
            print(f"     [{angle}] {msg}")

    # S3 — the prior attempt's one hand-classified 'weak DEFECT' dissolves on inspection.
    print("\n  S3 'artifacts spec proof' (prior classification #25): VOID — the source text is")
    print("     'the formal artifacts (spec + proof)' (law/briefs/.../sweep-assurance-cases-gsn.md);")
    print("     the prior scanner tokenized across parentheses. Not a compound; a tokenization")
    print("     artifact. This scanner segments at punctuation, so the shape cannot recur.")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tables", action="store_true", help="CLASS 2 table scan")
    ap.add_argument("--specimens", action="store_true", help="recall on pre-registered specimens")
    ap.add_argument("--top", type=int, default=25, help="ranked list size (CLASS 1)")
    ap.add_argument("--angle", help="restrict CLASS 1 to a subset of angles, e.g. 'A' or 'BC'")
    ap.add_argument("--dump-all", action="store_true", help="print the full ranked list")
    args = ap.parse_args(argv)
    if args.specimens:
        cmd_specimens(args)
    elif args.tables:
        cmd_tables(args)
    else:
        cmd_class1(args)
    return 0  # report-only by design: findings never fail the run


if __name__ == "__main__":
    sys.exit(main())
