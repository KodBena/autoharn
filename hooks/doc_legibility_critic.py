"""doc_legibility_critic — the zero-context-reader editorial critic
(design/ADR-DRAFT-documentation-discipline.md, Rule 1's out-of-frame instrument; BACKLOG
"Documentation legibility indictment (maintainer, 2026-07-11 morning)").

WHAT THIS CATCHES: a maintainer-facing markdown document, at the moment it is written or
edited, that fails the zero-context reader test — text complete for its author (whose live
context silently supplies every missing subject, referent, and connective) and skeletal for
every later reader. The classifier is briefed on the TEST, never on a shape list: the named
shapes (fragmentation, slash-soup, contextual starvation, unresolved referents, positional
references, jargon-first openings) ride in the prompt as worked specimens only, because
enumeration fails open at the next instance (ADR-0011 Rule 4) and the failure is a paraphrase
engine. Findings are STRUCTURED — shape, verbatim quote, suggested repair — so a human or
agent can act on each one; an umbrella verdict is treated as no verdict (the ADR-0013
2026-07-02 amendment's claim-shape rule, applied to critique).

WHY THE AUTHOR CANNOT SELF-CERTIFY (the design's load-bearing fact): the test asks what the
text does WITHOUT the author's context, and the author is the one reader who cannot unknow
that context. So the honest checker is out-of-frame by construction. This module is one
transport for that check (a headless small-model call, briefed cold). The other transport is
the maintainer-proposed A:B:C fresh-context audit workflow (2026-07-11; see the ADR draft's
enforcement section): a separate reviewer agent B that sees ONLY the document plus the
discipline — never the author's conversation. Both transports want the same briefing, so
CRITIC_PROMPT_TEMPLATE below is the ONE home of it (ADR-0012 P1): the A:B:C reviewer's
commission embeds this same prompt, and the eval harness measures this same prompt — one
judgment, measured once, used everywhere.

OBSERVER MODE ONLY (house rule, 2026-07-09 mandate) — THIS HOOK NEVER BLOCKS, NEVER DENIES,
NEVER ASKS. On a DEFECT verdict it (a) injects the findings into the agent's own context via
`hookSpecificOutput.additionalContext`, and (b) appends a record to
`.claude/logs/doc_legibility_critic.journal.jsonl` under the session's cwd. Whether any LLM
judgment in this discipline may EVER block is an explicit question in the ADR draft's
ratification packet — never a default this file adopts.

APPARATUS.JSON SWITCHBOARD — DEFAULT OFF BECAUSE COSTED (maintainer mandate 2026-07-10: "no
world may silently bill its operator"): `mechanisms.doc_legibility_critic.mode` at
`<root>/.claude/apparatus.json` (root = GATE_SUBJECT_ROOT env var, else the session's cwd).
Missing file/key resolves to "off" — exit before any subprocess. "observe" is the only real
on-state; "enforce" is not implemented (warned, degraded to "observe"). Per-mechanism
settings mirror hooks/demurral_detect.py exactly: `classifier_command` (argv list override),
`timeout_s`, `cost_note`.

ATTACHMENT POINT: PostToolUse on Write|Edit whose file_path ends in `.md`. Delivered here
UNWIRED (this pass touches no existing hooks/ wiring nor bootstrap/templates/ — house rule);
the settings.json block for a maintainer/orchestrator pass to drop in:

    {"hooks": {"PostToolUse": [
        {"matcher": "Write|Edit",
         "hooks": [{"type": "command",
                    "command": "python3 __AUTOHARN_ROOT__/hooks/doc_legibility_critic.py",
                    "timeout": 15}]}]}}

FAIL-OPEN ON TIMEOUT/ERROR, same named choice as the demurral detector, same stated reason:
this is an OBSERVER, and a classifier hiccup must never cost the session anything. MEASURED
HONESTY inherited from that precedent: observed `claude -p` latency for prompts of this size
is ~7–20s, so at a 10s default a substantial fraction of live calls time out and fail open;
the eval harness's numbers (instruments/doc_critic_eval.py over
instruments/doc_legibility_corpus.jsonl) report both the RAW ceiling and the EFFECTIVE
fail-open-folded number, and those numbers are this hook's honest strength claim.

GOODHARTING: a fixed critic prompt is a target the illegibility register can drift past.
PROMPT_VERSION is bumped on every prompt edit; the corpus is re-grown and the eval re-run
against each new version — a stale number is worse than none.

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

# One model name, one home (shared by hook and eval harness — ADR-0012 P1).
CLASSIFIER_MODEL = "claude-haiku-4-5-20251001"

# Per-call hard timeout; DOC_CRITIC_TIMEOUT_S overrides (the eval harness and the seen-red
# fixture pass a longer allowance for a real verdict — see the demurral precedent's note).
CLASSIFIER_TIMEOUT_S = float(os.environ.get("DOC_CRITIC_TIMEOUT_S", "10.0"))

# Bump on every CRITIC_PROMPT_TEMPLATE edit; recorded in every journal entry and eval report.
PROMPT_VERSION = "v2"

# Content longer than this is truncated before classification (a headless small model, not a
# book reviewer); the truncation is marked in the text so the critic knows the tail is absent.
MAX_TEXT_CHARS = 6000

# Content shorter than this is skipped: too little text to judge grounding on.
MIN_TEXT_CHARS = 40

CRITIC_PROMPT_TEMPLATE = """You are a documentation legibility critic for an engineering project whose documentation is written mostly by LLM agents. You receive ONE markdown passage, EXCERPTED from a longer document you cannot see. You have deliberately been given no other context — no conversation, no repository, no author's intent. You are the ZERO-CONTEXT READER: judge whether the passage's own text gives a cold reader what they need — and never penalize the passage for being an excerpt.

THE TEST (judge only this): does the passage's own text let a competent cold reader
  1. parse every sentence (subjects and verbs present — a noun phrase is not a paragraph, and separators like "/", "—", "→", "·" may join items within a stated frame but may not replace the sentence that states the frame);
  2. find a ROAD to every referent — where a road is any of: a markdown link, an explicit file path, a stable named identifier of a findable artifact (an ADR/standard number like "ADR-0013" or "ISO 15489", a section anchor like "§2" or a quoted section name, a named log/audit/commit), or a definition in the passage itself. A referent FAILS only when the reader is given NO road at all: a bare internal coinage or alias used as if already known ("the pilot", "the WHY-ledger / R-WHY / R-QTY work", "the increment") with no link, no path, no definition, and nowhere named to look;
  3. know what every structure is (a table, list, or code block must be introduced by prose saying what it is and why it is here);
  4. and, if the passage is clearly a document's opening, learn from it in plain words what the document is, for whom, and what question it answers — before any apparatus jargon?

CALIBRATION (load-bearing): most professional documentation is CLEAN. Dense, heavily cross-referential, compressed prose is the HOUSE STYLE of a well-run repository, not a defect. Flag only text that would actually defeat a cold reader; when in doubt, answer CLEAN.

WORKED SPECIMENS of failure (examples of what failing the test looks like, NOT an exhaustive list — a passage can fail in a shape not named here; flag that under shape=OTHER):
  - FRAGMENT: "The core deliverable." standing as a paragraph. (Headings are not paragraphs and are never fragments; nor is a compact opener completed by its own colon, like "Ten minutes: stand up a ledger, file a decision, tear it down.")
  - SLASH-SOUP: "B-method / Event-B (Abrial) with Atelier B / Rodin — RATP Line 14 — abstract machine → refinement → implementation" — names chained by punctuation doing the work sentences owed the reader, with no sentence stating what the chain IS.
  - STARVATION: a table or section dropped on the reader with no grounding sentence.
  - UNRESOLVED-REFERENT: "per the harness DB claim-ledger and the WHY-ledger / R-WHY / R-QTY work" — internal aliases, no road (no link, no path, no definition, nowhere named to look).
  - POSITIONAL-REF: "see HANDOFF open-work item 2" — a pointer by bare position into a document that gets rewritten wholesale. (A quoted named anchor plus a position, like HANDOFF "Open work" item 1, carries a road and is fine.)
  - JARGON-OPENING: a document plainly addressed to a non-expert decision-maker that opens with quoted SQL and undefined internal terms instead of a plain-words statement.

DO NOT FLAG (hard negatives — density is not the defect; roadlessness is):
  (a) telegraphic registers that carry their frame: table cells, glossary entries under their own heading, commit trailers, code blocks, checklists whose surrounding prose states the frame;
  (b) dense prose whose referents all carry roads (linked, path-named, identifier-named, or defined inline) — a long sentence with many clauses is fine if it parses;
  (c) a passage that QUOTES defective text in order to diagnose, label, or fix it;
  (d) domain terms a competent engineer knows from plain English or general practice (you are zero-CONTEXT, not zero-knowledge);
  (e) cross-references by stable identifier — file paths, ADR/standard numbers, § anchors, quoted section names, dated entries — even though you cannot follow them from this excerpt: the road exists, and that is what the test asks.

Respond with EXACTLY this format, nothing else:

VERDICT: DEFECT
FINDING: shape=<FRAGMENT|SLASH-SOUP|STARVATION|UNRESOLVED-REFERENT|POSITIONAL-REF|JARGON-OPENING|OTHER> | quote=<short verbatim excerpt from the passage> | repair=<one sentence: the concrete fix>
(one FINDING line per distinct defect, each with a verbatim quote — never an umbrella claim about the passage as a whole)

or

VERDICT: CLEAN

PASSAGE TO CRITIQUE:
\"\"\"
{text}
\"\"\"
"""


def build_critic_prompt(text: str) -> str:
    if len(text) > MAX_TEXT_CHARS:
        text = text[:MAX_TEXT_CHARS] + "\n[... truncated for classification ...]"
    return CRITIC_PROMPT_TEMPLATE.format(text=text)


_VERDICT_RE = re.compile(r"VERDICT:\s*(DEFECT|CLEAN)", re.IGNORECASE)
_FINDING_RE = re.compile(
    r"FINDING:\s*shape=(?P<shape>[A-Z-]+)\s*\|\s*quote=(?P<quote>.*?)\s*\|\s*repair=(?P<repair>.*)",
    re.IGNORECASE,
)


@dataclass
class CritiqueResult:
    verdict: str  # "DEFECT" | "CLEAN" | "ERROR"
    findings: list[dict] = field(default_factory=list)  # {shape, quote, repair}
    raw: str = ""
    elapsed_s: float = 0.0
    error: str = ""


def critique_text(text: str, *, timeout: float = CLASSIFIER_TIMEOUT_S,
                  model: str = CLASSIFIER_MODEL,
                  command: list[str] | None = None) -> CritiqueResult:
    """Invoke the critic headlessly (`claude -p --model <model>` by default, or `command` —
    the apparatus.json `classifier_command` override). Never raises: any subprocess failure,
    timeout, or unparsed reply returns verdict=ERROR — fail-open for the hook (behaves like
    CLEAN: no warning), but counted distinctly by the eval harness (an ERROR is detector
    unavailability, not a judgment)."""
    prompt = build_critic_prompt(text)
    argv = command if command else ["claude", "-p", "--model", model]
    t0 = time.monotonic()
    try:
        cp = subprocess.run(argv, input=prompt, capture_output=True, text=True,
                            timeout=timeout)
    except subprocess.TimeoutExpired:
        return CritiqueResult("ERROR", error=f"critic timed out after {timeout}s",
                              elapsed_s=time.monotonic() - t0)
    except Exception as e:  # noqa: BLE001 — any launch failure is fail-open, not a crash
        return CritiqueResult("ERROR", error=f"critic launch failed: {type(e).__name__}: {e}",
                              elapsed_s=time.monotonic() - t0)
    elapsed = time.monotonic() - t0
    raw = (cp.stdout or "") + (("\n" + cp.stderr) if cp.returncode != 0 and cp.stderr else "")
    vm = _VERDICT_RE.search(raw)
    if not vm:
        return CritiqueResult("ERROR", error="critic reply carried no parseable VERDICT line",
                              raw=raw, elapsed_s=elapsed)
    verdict = vm.group(1).upper()
    findings = [{"shape": m.group("shape").upper(),
                 "quote": m.group("quote").strip(),
                 "repair": m.group("repair").strip()}
                for m in _FINDING_RE.finditer(raw)]
    if verdict == "DEFECT" and not findings:
        # A defect verdict with no per-finding specimen is an umbrella claim — no verdict.
        return CritiqueResult("ERROR", error="DEFECT verdict carried no parseable FINDING line "
                              "(umbrella verdicts are not verdicts)", raw=raw, elapsed_s=elapsed)
    return CritiqueResult(verdict, findings=findings, raw=raw, elapsed_s=elapsed)


# ---------------------------------------------------------------------------------------
# Hook I/O — PostToolUse on Write|Edit of markdown. Field-aliasing helper matches the
# convention hooks/demurral_detect.py / hooks/pretooluse_change_gate.py already use.
# ---------------------------------------------------------------------------------------

def _first(d: Any, *keys: str, default: Any = None) -> Any:
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] is not None:
            return d[k]
    return default


def _extract_markdown_payload(payload: dict) -> tuple[str, str]:
    """Return (file_path, written_text) for a Write/Edit of a .md file, else ("", "")."""
    tool = _first(payload, "tool_name", "toolName", "name", default="")
    if tool not in ("Write", "Edit"):
        return "", ""
    tool_input = _first(payload, "tool_input", "toolInput", "input", default={})
    if not isinstance(tool_input, dict):
        return "", ""
    file_path = _first(tool_input, "file_path", "filePath", default="")
    if not isinstance(file_path, str) or not file_path.endswith(".md"):
        return "", ""
    text = _first(tool_input, "content", "new_string", "newString", default="")
    return file_path, text if isinstance(text, str) else ""


def _journal_path(payload: dict) -> Optional[Path]:
    cwd = _first(payload, "cwd", default="")
    if not cwd or not isinstance(cwd, str):
        return None
    return Path(cwd) / ".claude" / "logs" / "doc_legibility_critic.journal.jsonl"


def _journal(payload: dict, record: dict) -> None:
    path = _journal_path(payload)
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 — fail-open applies to the logging path too
        pass


# ---------------------------------------------------------------------------------------
# apparatus.json switchboard — self-contained, same posture as every sibling hook.
# ---------------------------------------------------------------------------------------
_VALID_MODES = ("off", "observe", "enforce")
MECHANISM_KEY = "doc_legibility_critic"


def _apparatus_root(payload: dict) -> Optional[str]:
    env_root = os.environ.get("GATE_SUBJECT_ROOT")
    if env_root:
        return env_root
    cwd = _first(payload, "cwd", default="")
    return cwd if cwd and isinstance(cwd, str) else None


def _load_apparatus_quiet(root: Optional[str]) -> dict:
    if not root:
        return {}
    path = os.path.join(root, ".claude", "apparatus.json")
    try:
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg if isinstance(cfg, dict) else {}
    except Exception:
        return {}


def _mechanism_entry(apparatus: dict) -> dict:
    mechs = apparatus.get("mechanisms")
    entry = mechs.get(MECHANISM_KEY) if isinstance(mechs, dict) else None
    return entry if isinstance(entry, dict) else {}


def _resolve_mode(entry: dict, root: Optional[str]) -> str:
    """Default "off" — this mechanism spends a real `claude -p` call per invocation, and no
    world may silently bill its operator (maintainer mandate 2026-07-10). "enforce" is not
    implemented (observer-only by design; promotion is a ratification-packet question)."""
    default = "off"
    raw = entry.get("mode")
    if raw is None:
        return default
    if raw == "enforce":
        print(f"[apparatus] WARNING: mechanisms.{MECHANISM_KEY}.mode='enforce' is not "
              "implemented (observer-only by design — see hooks/doc_legibility_critic.py "
              "module docstring); behaving as 'observe'.", file=sys.stderr)
        return "observe"
    if raw in _VALID_MODES:
        return raw
    print(f"[apparatus] WARNING: mechanisms.{MECHANISM_KEY}.mode={raw!r} in "
          f"{root}/.claude/apparatus.json is unrecognized (must be one of {_VALID_MODES}) — "
          f"never widening permissions (this mechanism spends money per invocation when "
          f"enabled); falling back to {default!r}.", file=sys.stderr)
    return default


DISCIPLINE_REMINDER = (
    "Zero-context-reader discipline (design/ADR-DRAFT-documentation-discipline.md, Rule 1): "
    "a document is finished only when a reader with none of this session's context can parse "
    "every sentence, resolve every referent, and know what every section is about from the "
    "text and its links alone. This is an OBSERVER-MODE finding; it does not block. Repair "
    "or consciously disregard each finding — an unread finding is the malady's next instance."
)


def _emit_findings(payload: dict, file_path: str, result: CritiqueResult) -> None:
    lines = [f"[doc-legibility-critic] {len(result.findings)} finding(s) in {file_path} "
             f"(observer-mode, non-blocking):"]
    for f in result.findings:
        lines.append(f"  - shape={f['shape']} | quote={f['quote']!r} | repair: {f['repair']}")
    lines.append(DISCIPLINE_REMINDER)
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "\n".join(lines),
    }}))
    _journal(payload, {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z",
        "event": "PostToolUse",
        "file": file_path,
        "verdict": result.verdict,
        "findings": result.findings,
        "prompt_version": PROMPT_VERSION,
        "elapsed_s": round(result.elapsed_s, 3),
    })


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # unparseable stdin -> unwired/unknown caller, pass through untouched
    if not isinstance(payload, dict):
        return 0

    # Switchboard first: "off" (the default) exits before anything costs work.
    root = _apparatus_root(payload)
    entry = _mechanism_entry(_load_apparatus_quiet(root))
    mode = _resolve_mode(entry, root)
    if mode == "off":
        return 0

    event = _first(payload, "hook_event_name", "hookEventName", default="")
    if event != "PostToolUse":
        return 0
    file_path, text = _extract_markdown_payload(payload)
    if not file_path or len(text.strip()) < MIN_TEXT_CHARS:
        return 0

    timeout_raw = entry.get("timeout_s")
    try:
        timeout_s = float(timeout_raw) if timeout_raw is not None else CLASSIFIER_TIMEOUT_S
    except (TypeError, ValueError):
        timeout_s = CLASSIFIER_TIMEOUT_S
    cmd_raw = entry.get("classifier_command")
    command = (cmd_raw if isinstance(cmd_raw, list) and cmd_raw
               and all(isinstance(c, str) for c in cmd_raw) else None)

    try:
        result = critique_text(text, timeout=timeout_s, command=command)
    except Exception:  # noqa: BLE001 — belt-and-suspenders; critique_text already fail-opens
        return 0

    if result.verdict != "DEFECT":
        return 0  # CLEAN, or ERROR (fail-open) -> silent

    _emit_findings(payload, file_path, result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
