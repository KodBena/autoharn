"""userpromptsubmit_row_resolve — zero-LLM-cost `/row <id> [<id> ...]` ledger resolver
(maintainer commission 2026-07-26, verbatim constraint: fine only "if a '/row nnnn' doesn't
invoke the claude LLM backend"). A UserPromptSubmit hook that recognizes the exact shape
`/row 1325` (or `/row 1325 1326 ...`) typed as the whole prompt, resolves each id via the
LOCAL, READ-ONLY `./autoharn led show <id>` CLI, and BLOCKS the prompt with the row text —
no model turn, no tokens spent, for that shape only. Every other prompt passes through
completely untouched (module design constraint: a hook that slows or mangles an ordinary
prompt is worse than no hook at all).

VERIFIED CONTRACT (Claude Code hooks docs, `hooks.md`, UserPromptSubmit sections — fetched and
grep'd directly against the raw doc text for this build, not recalled from memory or a
first-pass agent summary that turned out to conflate two different events' text; see this
commit's own message for the two conflicting first-pass reads this build discarded):

  * stdin carries `{session_id, transcript_path, cwd, permission_mode,
    hook_event_name: "UserPromptSubmit", prompt}` — "UserPromptSubmit hooks receive the
    `prompt` field containing the text the user submitted" (hooks.md "UserPromptSubmit
    input"). `prompt` is the exact field name; there is no `user_prompt` alias.

  * THE BLOCKING PATH THIS HOOK USES IS EXIT 0 + A JSON `decision` FIELD, NOT EXIT 2.
    hooks.md "UserPromptSubmit decision control": `decision: "block"` "prevents the prompt
    from being processed and erases it from context. Omit to allow the prompt to proceed."
    `reason` is "Shown to the user when `decision` is `"block"`. Not added to context" —
    this is the load-bearing sentence for the zero-cost guarantee: the maintainer's own
    acceptance-bar sharpening (this build's own session) demanded proof that a blocked
    prompt's displayed text is NOT silently re-injected into a LATER turn's context, which
    would recreate the LLM cost one turn downstream instead of avoiding it. `reason` is
    documented as explicitly NOT added to context, at any turn — this is the field this hook
    uses to carry the resolved row text. (`additionalContext` is documented as adding text
    "alongside the submitted prompt" — the wrong field for a BLOCKED prompt, since there is
    no submitted prompt left once `decision: "block"` erases it; this hook never sets it.)
    hooks.md's per-event `ok: false` behavior table states plainly, for this exact event:
    "`PostToolBatch`, `UserPromptSubmit`, and `UserPromptExpansion`: the turn ends and the
    reason appears as a warning line" — a warning line in the transcript, never a model
    invocation.

  * Exit code 2 is a SEPARATE, real blocking path for this event too (hooks.md's "Exit code 2
    behavior per event" table: `UserPromptSubmit` / "Blocks prompt processing and erases the
    prompt") but its stderr-handling text is written GENERICALLY across all hook events
    ("stderr text is fed back to Claude as an error message") and is not spelled out
    UserPromptSubmit-specifically the way the exit-0 JSON path is. This hook deliberately
    uses the exit-0 `decision`/`reason` path instead, because that path's own doc text names
    the "not added to context" guarantee explicitly, in so many words, for the exact field
    this hook populates — the exit-2 path is not proof against re-injection with the same
    directness, so it is not the path relied on here for a machine-checked zero-cost claim.

  * A non-matching prompt: this hook prints nothing and exits 0. No JSON on stdout at exit 0
    means "omit `decision`... to allow the prompt to proceed" (same section) — ordinary,
    untouched pass-through, not a degraded or partial block.

WHY THIS HOOK NEVER USES `additionalContext` OR PLAIN-STDOUT CONTEXT INJECTION on the
matching path: those are the two exit-0 mechanisms hooks.md documents for ADDING context
ALONGSIDE a prompt that still proceeds to the model — the opposite of this hook's job, which
is to make sure the model is never invoked for a `/row` prompt at all.

RESOLUTION MECHANICS (design constraint 1, maintainer commission verbatim): shells out to the
LOCAL, READ-ONLY `./autoharn led show <id>` CLI ONLY — never the HTTP boundary service
directly, never any network beyond what that CLI itself does internally. The row text stays on
the terminal's trust boundary (the feasibility investigation's own flag, named in the
commission). `ROW_RESOLVE_AUTOHARN_BIN` overrides the executable path invoked in place of
`<repo-root>/autoharn` — a FIXTURE-ONLY knob (this build's own seen-red family points it at a
small mock CLI so the fixture proves the hook's own regex/budget/formatting logic without a
live deployment.json or a served boundary), never a runtime configuration surface a deployment
is expected to touch.

MATCHING — tight and anchored (design constraint 2, maintainer commission verbatim: "the
matcher is a tight anchored regex on the whole prompt... anything else exits pass-through
immediately"): `^/row\\s+\\d+(\\s+\\d+)*\\s*$` against the prompt text. Anything else — a
`/row` with no digits, a `/row` embedded mid-sentence, a completely unrelated prompt — is not
this hook's business, full stop, zero cost past one regex check.

LATENCY HAZARD, NAMED AND MITIGATED (not in the commission's own text, but a hazard this build
found in the doc text while reading it and is obligated to fix or flag loudly, CLAUDE.md's
engineering-responsibility standard): "A UserPromptSubmit command... hook that reaches its
timeout is canceled and its output... is discarded. The prompt still reaches Claude without
that context" (hooks.md "UserPromptSubmit" section). If this hook's own CLI calls ran long
enough to trip Claude Code's own 30s default UserPromptSubmit hook timeout, the OUTCOME WOULD BE
THE OPPOSITE OF THE COMMISSION: the block JSON is discarded, and the `/row` prompt — the exact
text this whole hook exists to intercept — reaches the model anyway, silently, defeating the
zero-cost guarantee on exactly the turn it matters. Mitigated by a wall-clock BUDGET
(`_HOOK_BUDGET_S`, comfortably under the 30s default, itself overridable via
`ROW_RESOLVE_BUDGET_S` for a deployment that has widened the hook's own `timeout` field in
settings.json) tracked across every `led show` call this invocation makes: each call's own
per-call timeout is clamped to whatever budget remains, and once the budget is exhausted this
hook stops resolving further ids and says so in the block text, rather than let the whole
invocation run past Claude Code's own hook timeout and leak the prompt through. A hard cap on
the NUMBER of ids in one prompt (`_MAX_IDS`) is the same hazard's belt-and-suspenders twin: a
pathological `/row 1 2 3 ... 500` is still syntactically a match for the anchored regex above.

FAILURE IS HONEST (design constraint 3, maintainer commission verbatim): an unknown row ->
`./autoharn led show <id>`'s own refusal text (stderr, exit 1: "led show: REFUSED -- no row
<id>.", `bootstrap/templates/led.tmpl`'s `cmd_show`) is shown verbatim in the block reason,
never swallowed or replaced. CLI unreachable (missing executable, launch failure, timeout) is
shown as this hook's own honest error text, STILL inside a `decision: "block"` — this hook
NEVER falls through to a silent pass-through on a `/row`-shaped prompt, because a silent
pass-through on exactly this shape is exactly "burning a model turn on a /row prompt", the one
outcome the commission forbids outright.

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below is imported at module load.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)  # hooks/ -> repo root

# The exact matcher (design constraint 2, verbatim): anchored on the WHOLE prompt, one or more
# whitespace-separated digit groups after "/row ". Nothing else is this hook's business.
# TRIGGER CHANGED 2026-07-26, witnessed live by the maintainer in a real session: a
# `/`-prefixed prompt NEVER REACHES UserPromptSubmit — Claude Code's own slash-command
# parser intercepts it client-side first ("Unknown command: /row"), so the original
# `/row ...` trigger was unreachable by construction. Every prior witness drove the hook
# with synthetic stdin JSON and so never caught it: an integration gap at the one boundary
# no fixture crossed (the real UI's input parsing). Bare `row <id> [...]`/`rows <id> [...]`
# is an ordinary prompt, which this hook demonstrably receives. The anchored whole-prompt
# match keeps ordinary prose safe: only a prompt that IS the command shape, alone on a
# single line, matches.
_ROW_PROMPT_RE = re.compile(r"^rows?\s+\d+(\s+\d+)*\s*$")

# Belt-and-suspenders cap on how many ids one prompt can request (LATENCY HAZARD note above) —
# a pathological `/row 1 2 ... 500` is still a syntactic match for the regex above.
_MAX_IDS = 25

# Per-call default timeout for one `led show <id>` invocation, and the overall wall-clock
# budget this hook holds itself to across ALL calls in one invocation (LATENCY HAZARD note
# above: comfortably under Claude Code's own 30s default UserPromptSubmit hook timeout, so a
# slow/unreachable CLI degrades this hook's OWN output rather than tripping Claude Code's outer
# timeout and leaking the `/row` prompt through to the model). Both overridable via env for the
# seen-red fixture (which wants to exercise the budget-exhaustion path deterministically, fast).
_PER_CALL_TIMEOUT_S = float(os.environ.get("ROW_RESOLVE_TIMEOUT_S", "8.0"))
_HOOK_BUDGET_S = float(os.environ.get("ROW_RESOLVE_BUDGET_S", "20.0"))

# FIXTURE-ONLY override (module docstring): the executable invoked in place of
# `<repo-root>/autoharn`. Never a runtime/deployment configuration surface.
_AUTOHARN_BIN = os.environ.get("ROW_RESOLVE_AUTOHARN_BIN") or os.path.join(_REPO_ROOT, "autoharn")


def _first(d, *keys, default=None):
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] is not None:
            return d[k]
    return default


def extract_row_ids(prompt: str) -> list[str] | None:
    """Returns the ordered list of id strings if `prompt` is EXACTLY the `/row <id> [...]`
    shape (anchored, module docstring MATCHING section), else None — the pass-through case.

    NEWLINE HAZARD, found and fixed 2026-07-26 (CLAUDE.md engineering-responsibility standard
    — a hazard met in passing while reviewing this hook, fixed rather than routed around):
    `\\s` inside `_ROW_PROMPT_RE` matches `\\n` as well as space/tab, and `re.match` with `$`
    (no `re.MULTILINE`) anchors `$` at end-of-string OR just before a trailing `\\n` — so an
    ordinary two-line prompt whose second line happens to be pure digits, e.g. literally
    "/row 5\\n6", was wrongly recognized as the `/row 5 6` shape and silently blocked/resolved,
    which is exactly the "hook that mangles an ordinary prompt" hazard design constraint 2
    exists to rule out (see this hook's own `g-mixed-request-not-matched` fixture for the
    single-line analogue of this same class of bug). Fixed here by rejecting any EMBEDDED
    newline before the anchored regex ever runs, so a `/row` command is strictly single-line —
    the regex itself is left as `\\s`-based (module docstring's MATCHING text quotes the
    pattern verbatim) rather than narrowed to `[ \\t]`, so the fix is visible at the guard, not
    hidden inside the pattern text the docstring already commits to.

    TRAILING-NEWLINE RULING (same finding, decided 2026-07-26): a prompt that is otherwise a
    pure `/row <id> [...]` command plus exactly ONE trailing newline and nothing after it
    (e.g. "/row 5\\n", the shape a terminal/editor's own auto-appended newline on submission
    would produce) carries no additional content past the command — there is no "second line"
    for the hook to have silently swallowed, unlike the embedded-newline case above. Judged
    still a match: exactly one trailing `\\n` is stripped before the newline-embedded check and
    the anchored match, so "/row 5\\n" resolves row 5 same as "/row 5", while "/row 5\\n6" and
    "/row 5\\n\\n" (a second, blank-but-real line) are both rejected as pass-through.
    """
    if not isinstance(prompt, str):
        return None
    body = prompt[:-1] if prompt.endswith("\n") else prompt
    if "\n" in body:
        return None
    if not _ROW_PROMPT_RE.match(body):
        return None
    return re.findall(r"\d+", body)


def _resolve_one(row_id: str, timeout: float) -> str:
    """Runs `<autoharn> led show <row_id>` (design constraint 1: local CLI only, read-only,
    never the HTTP service directly) and returns the text to show for this one row — the CLI's
    own stdout on success, its own refusal text on a known refusal (exit 1, stderr), or this
    hook's own honest error text if the CLI could not be run at all or timed out (design
    constraint 3: failure is honest, never a silent pass-through)."""
    try:
        cp = subprocess.run(
            [_AUTOHARN_BIN, "led", "show", row_id],
            cwd=_REPO_ROOT, capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return (f"row {row_id}: CLI TIMED OUT after {timeout:.1f}s calling "
                f"`{_AUTOHARN_BIN} led show {row_id}` -- still blocked, never falling through "
                f"to the model on a /row prompt.")
    except Exception as e:  # noqa: BLE001 -- CLI unreachable is an honest error, never a crash
        return (f"row {row_id}: CLI UNREACHABLE ({type(e).__name__}: {e}) calling "
                f"`{_AUTOHARN_BIN} led show {row_id}` -- still blocked, never falling through "
                f"to the model on a /row prompt.")
    combined = (cp.stdout or "").rstrip("\n")
    err = (cp.stderr or "").rstrip("\n")
    if cp.returncode == 0:
        return f"row {row_id}:\n{combined}" if combined else f"row {row_id}: (no fields returned)"
    # non-zero exit: the CLI's OWN refusal/error text (design constraint 3), shown verbatim,
    # never replaced or paraphrased by this hook.
    text = err or combined or f"(exit {cp.returncode}, no output)"
    return f"row {row_id}: {text}"


def build_reason(row_ids: list[str]) -> str:
    """Resolves every id in `row_ids` (up to `_MAX_IDS`, within `_HOOK_BUDGET_S` wall-clock
    total -- LATENCY HAZARD note above), and returns the combined block text for the
    `decision: "block"` `reason` field."""
    truncated = len(row_ids) > _MAX_IDS
    ids = row_ids[:_MAX_IDS]
    blocks: list[str] = []
    deadline = time.monotonic() + _HOOK_BUDGET_S
    budget_exhausted_at: int | None = None
    for i, row_id in enumerate(ids):
        remaining = deadline - time.monotonic()
        if remaining <= 0.5:
            budget_exhausted_at = i
            break
        per_call = min(_PER_CALL_TIMEOUT_S, remaining)
        blocks.append(_resolve_one(row_id, per_call))
    notes = []
    if budget_exhausted_at is not None:
        skipped = ids[budget_exhausted_at:]
        notes.append(f"(hook time budget exhausted -- {len(skipped)} row(s) not attempted: "
                     f"{', '.join(skipped)})")
    if truncated:
        notes.append(f"(only the first {_MAX_IDS} of {len(row_ids)} requested rows were "
                      f"resolved -- one /row prompt is capped at {_MAX_IDS})")
    header = f"row-prompt resolved locally via `{_AUTOHARN_BIN} led show <id>` -- no model turn spent."
    parts = [header, ""] + blocks
    if notes:
        parts += [""] + notes
    return "\n".join(parts)


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # unparseable stdin -- nothing this hook can act on, pass through
    if not isinstance(payload, dict):
        return 0

    prompt = _first(payload, "prompt", default="")
    row_ids = extract_row_ids(prompt)
    if row_ids is None:
        return 0  # not a /row prompt -- untouched pass-through, zero added cost

    reason = build_reason(row_ids)
    # Exit 0 + top-level `decision: "block"` (module docstring VERIFIED CONTRACT): the prompt is
    # erased from context, never reaches the model, and `reason` is documented as NOT added to
    # context at any later turn either -- no model call now, no re-created cost downstream.
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
