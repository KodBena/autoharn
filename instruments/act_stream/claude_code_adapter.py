"""act_stream.claude_code_adapter — the CLAUDE-CODE-SPECIFIC act-stream adapter (consult 25 §2.1.2).

This adapter is vendor-specific BY CONSTRUCTION and says so: it knows Claude Code's completed
session-record format (the transcript JSONL, subagent JSONLs, assistant/user records with a
`message.content` list of thinking/text/tool_use/tool_result blocks). Every CC-ism lives HERE; the
contract (`contract.py`, `003_acts_stream.sql`) has none.

GUARANTEE LEVEL (manifest-declared): it parses COMPLETED session directories only — post-hoc
parsing is the declared guarantee; live hook capture is mechanism 2, DEFERRED. Attribution is from
RECORD STRUCTURE: the main transcript → actor 'main'; a subagent transcript file → 'sub:<label>'
with the label (the vendor's subagent_type) carried VERBATIM. It EXCLUDES model reasoning (the
`thinking` blocks — not an act) and token accounting (`message.usage`), declared EXCLUDED in the
manifest (F49: absent loudly, never silently empty).

Lazy imports banned: every import is top-of-file.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from contract import Act, FamilyStatus, KINDS, Manifest, Stream, persist

# Tool inputs whose value IS a classifiable target (a path / notebook / db object). A Bash `command` has
# no such key — but a Bash command that WRITES a file via a redirection (`> path`, `>> path`) or `tee`
# DOES name a target, and finding 18 requires we classify it (a subject may implement via Bash heredoc/
# printf rather than the Write tool; not classifying it made its ledger evidence-claims read as
# claimed_without_act). `_bash_write_target` extracts that target CONSERVATIVELY (a redirection/tee
# target only — never a read: cat/grep/sed-without-redirect set no target). One home for the rule (P1).
_PATH_KEYS = ("file_path", "path", "notebook_path")
# a redirection (`>`/`>>`, optional space) OR `tee [-a]` followed by a path token; the char class
# excludes shell metachars so `2>&1`/`>&1` (fd dups, not file writes) do not match.
_BASH_WRITE = re.compile(r"(?:>>?\s*|\btee\b(?:\s+-a)?\s+)([^\s|&;<>()]+)")


def _bash_write_target(command: str) -> str | None:
    """The FILE a Bash command writes via redirection/tee, or None (a read/no-write command, or a
    discard to a pseudo-device). The FIRST such target; a `/dev/*` target (`/dev/null`, `/dev/stderr`)
    is a discard, not a file write, so it is NOT a classifiable target — returning it would pollute the
    stream (and it is never a fenced implementation write). Downstream `_is_fenced` then filters real
    targets to the fenced dir."""
    m = _BASH_WRITE.search(command or "")
    if not m:
        return None
    tgt = m.group(1).strip().strip("\"'")
    # Reject non-file tokens the greedy `>` match can pick up in real commands: a `/dev/*` discard; a
    # bare number (an fd like `>&2`'s tail or an arithmetic `> 5`); an operator fragment (`>='R040']`
    # from a `[[ ]]`/awk comparison). A real file target — and every FENCED write, which is what f18
    # exists to catch — carries a path separator or a filename extension; require one.
    if not tgt or tgt.startswith("/dev/") or tgt.isdigit():
        return None
    if "/" not in tgt and "." not in tgt:
        return None
    return tgt


@dataclass(frozen=True)
class SubagentSource:
    """A completed subagent transcript file + its label (the vendor's subagent_type, verbatim). The
    label is the datum the spawning delegation recorded; the caller threads it (matching the Task
    input), so attribution stays 'from record structure' — main file vs sidechain file, label verbatim."""
    label: str
    path: Path


def _blocks(record: dict) -> list[dict]:
    """The content blocks of one CC record, or [] for a non-message record."""
    if record.get("type") not in ("assistant", "user"):
        return []
    msg = record.get("message")
    if not isinstance(msg, dict):
        return []
    content = msg.get("content")
    if isinstance(content, list):
        return [b for b in content if isinstance(b, dict)]
    if isinstance(content, str):  # a bare-string user/assistant message is one text block
        return [{"type": "text", "text": content}]
    return []


def _classify_target(tool_input: dict) -> str | None:
    for k in _PATH_KEYS:
        v = tool_input.get(k)
        if isinstance(v, str) and v:
            return v
    return None


def _todo_key(todo: dict) -> str:
    return str(todo.get("content", "")).strip()


def _todo_diff(prior: dict[str, str], todos: list[dict]) -> tuple[list[tuple[str, str]], dict[str, str]]:
    """Diff a TodoWrite against prior state → [(kind, content)] plan acts, plus the new state.
    created = a content not seen; closed = a content whose status became 'completed'; updated = any
    other status change; unchanged = no act. (The plan-of-record stream, native task events.)"""
    acts: list[tuple[str, str]] = []
    new: dict[str, str] = {}
    for t in todos:
        c, st = _todo_key(t), str(t.get("status", "")).strip()
        new[c] = st
        if c not in prior:
            acts.append(("plan_item_created", c))
        elif prior[c] != st:
            acts.append(("plan_item_closed" if st == "completed" else "plan_item_updated", c))
    return acts, new


def _acts_from_file(path: Path, actor: str, *, limit_blocks: int | None) -> list[Act]:
    """Parse ONE completed transcript file into acts, in file (ingestion) order, for one actor.
    Maintains its own tool_use_id→(name,target) pairing map and TodoWrite state (per file)."""
    out: list[Act] = []
    pending: dict[str, tuple[str, str | None]] = {}   # tool_use_id -> (tool name, target)
    todo_state: dict[str, str] = {}
    seen_blocks = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        rtype = rec.get("type")
        vseq = rec.get("uuid")
        vts = rec.get("timestamp")
        for b in _blocks(rec):
            bt = b.get("type")
            if bt == "thinking":
                continue  # EXCLUDED: model reasoning is not an act (manifest-declared)
            if limit_blocks is not None and seen_blocks >= limit_blocks:
                return out
            if bt in ("text", "tool_use", "tool_result"):
                seen_blocks += 1
            if bt == "text":
                kind = "message_out" if rtype == "assistant" else "message_in"
                sha, ex = Act.sha_excerpt(str(b.get("text", "")))
                out.append(Act(actor=actor, kind=kind, payload_sha256=sha, payload_excerpt=ex,
                               vendor_seq=vseq, vendor_ts=vts))
            elif bt == "tool_use":
                name = str(b.get("name", ""))
                inp = b.get("input") or {}
                sha, ex = Act.sha_excerpt(json.dumps(inp, sort_keys=True))
                if name in ("Task", "Agent", "Workflow"):
                    # The delegation tools. `Agent` is the CURRENT tool name; `Task` its legacy name
                    # (finding 23: the adapter recognized Task+Workflow but not Agent, so the e15 subject's
                    # real Agent spawns would have been parsed as generic non-relevant tool_calls). The
                    # Workflow tool is also a delegation (finding 17: its fan-out was invisible). Task/Agent
                    # carry the label in subagent_type; a Workflow's per-agent labels live in its journal
                    # (ingested via `workflow_dirs`), so its spawn act records the workflow itself.
                    if name in ("Task", "Agent"):
                        label = str(inp.get("subagent_type", "") or inp.get("description", ""))
                    else:
                        d = str(inp.get("description", "")).strip()
                        label = f"workflow:{d}" if d else "workflow"
                    out.append(Act(actor=actor, kind="delegation_spawn", name=f"sub:{label}",
                                   payload_sha256=sha, payload_excerpt=ex, vendor_seq=vseq, vendor_ts=vts))
                    pending[str(b.get("id", ""))] = (f"sub:{label}", None)
                elif name == "TodoWrite":
                    plan_acts, todo_state = _todo_diff(todo_state, inp.get("todos") or [])
                    for pkind, content in plan_acts:
                        psha, pex = Act.sha_excerpt(content)
                        out.append(Act(actor=actor, kind=pkind, name=content,
                                       payload_sha256=psha, payload_excerpt=pex,
                                       vendor_seq=vseq, vendor_ts=vts))
                else:
                    tgt = _classify_target(inp)
                    if tgt is None and name == "Bash":  # finding 18: a Bash-mediated file write names a target
                        tgt = _bash_write_target(str(inp.get("command", "")))
                    out.append(Act(actor=actor, kind="tool_call", name=name, target=tgt,
                                   payload_sha256=sha, payload_excerpt=ex, vendor_seq=vseq, vendor_ts=vts))
                    pending[str(b.get("id", ""))] = (name, tgt)
            elif bt == "tool_result":
                tuid = str(b.get("tool_use_id", ""))
                name, tgt = pending.get(tuid, (None, None))
                # a Task's return is a delegation_return; any other tool's result is a tool_result
                kind = "delegation_return" if (name or "").startswith("sub:") else "tool_result"
                sha, ex = Act.sha_excerpt(json.dumps(b.get("content", ""), sort_keys=True, default=str))
                out.append(Act(actor=actor, kind=kind, name=name, target=tgt,
                               payload_sha256=sha, payload_excerpt=ex, vendor_seq=vseq, vendor_ts=vts))
    return out


def _manifest(acts: list[Act]) -> Manifest:
    """Declare, per family, what this stream produced (F49). A CC-supported kind not emitted this run
    is CAPABLE (declared, not silent); model reasoning + token accounting are EXCLUDED; live hook
    capture is DEFERRED (mechanism 2 — this adapter parses COMPLETED records only)."""
    produced = {a.kind for a in acts}
    fams: dict[str, tuple[FamilyStatus, str]] = {}
    for k in sorted(KINDS):
        if k in produced:
            fams[k] = (FamilyStatus.PRODUCED, "emitted from completed records")
        else:
            fams[k] = (FamilyStatus.CAPABLE,
                       "Claude Code CAN produce this (native records/task events); not emitted this run")
    fams["model_reasoning"] = (FamilyStatus.EXCLUDED, "the `thinking` blocks are not acts")
    fams["token_accounting"] = (FamilyStatus.EXCLUDED, "`message.usage` is not an act")
    fams["live_hook_capture"] = (FamilyStatus.DEFERRED,
                                 "mechanism 2 — this adapter parses COMPLETED session dirs only")
    return Manifest(fams)


def agent_subs(subagents_dir: Path) -> list[SubagentSource]:
    """Enumerate the sidechain agents of a completed Agent-TOOL session (finding 23). The session's
    `subagents/` dir holds one `agent-<id>.jsonl` transcript per spawn + an `agent-<id>.meta.json`
    ({agentType, description, toolUseId, spawnDepth}). Attribution keys on the meta's `description` (the
    distinctive label the spawn recorded — `agentType` is often generic, e.g. 'general-purpose'), falling
    back to agentType then the agent id. Order is filename order (deterministic; id-is-order is THE key)."""
    subs: list[SubagentSource] = []
    for meta in sorted(subagents_dir.glob("agent-*.meta.json")):
        transcript = meta.parent / (meta.name[: -len(".meta.json")] + ".jsonl")
        if not transcript.exists():
            continue
        try:
            info = json.loads(meta.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            info = {}
        label = str(info.get("description") or info.get("agentType") or transcript.stem)
        subs.append(SubagentSource(label=label, path=transcript))
    return subs


def workflow_subs(workflow_dir: Path, labels: dict[str, str] | None = None) -> list[SubagentSource]:
    """Enumerate the fan-out agents of a completed Workflow-TOOL run (finding 17). The workflow dir holds
    `journal.jsonl` ({started|result, agentId, ...} per agent) + one `agent-<agentId>.jsonl` transcript
    per agent. Attribution keys on the vendor's stable `agentId` (the Workflow tool does NOT persist a
    per-agent semantic role label the way Task persists subagent_type — the honest residual of finding
    17); a caller that knows the role map may pass `labels` (agentId → role) for legibility. Order is
    the journal's first-seen order (ingestion order; id-is-order remains THE key)."""
    journal = workflow_dir / "journal.jsonl"
    labels = labels or {}
    seen: list[str] = []
    for line in journal.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            aid = json.loads(line).get("agentId")
        except json.JSONDecodeError:
            continue
        if aid and aid not in seen:
            seen.append(aid)
    subs: list[SubagentSource] = []
    for aid in seen:
        f = workflow_dir / f"agent-{aid}.jsonl"
        if f.exists():
            subs.append(SubagentSource(label=labels.get(aid, f"wf:{aid[:8]}"), path=f))
    return subs


def parse_completed_session(main_transcript: Path, subagents: list[SubagentSource], *,
                            run_id: str, source_ref: str,
                            subagents_dirs: list[Path] | None = None,
                            workflow_dirs: list[Path] | None = None,
                            workflow_labels: dict[str, str] | None = None,
                            limit_blocks: int | None = None) -> Stream:
    """Parse a COMPLETED Claude-Code session into a vendor-neutral Stream. Ingestion order = main
    transcript (file order) THEN each explicit subagent file THEN each Agent-tool sidechain (from
    `subagents_dirs`, filename order) THEN each Workflow-tool fan-out agent (from `workflow_dirs`, journal
    order). `limit_blocks` bounds the MAIN transcript for a slice fixture (subagents parsed whole)."""
    acts = _acts_from_file(main_transcript, "main", limit_blocks=limit_blocks)
    subs = list(subagents)
    for sd in (subagents_dirs or []):
        subs += agent_subs(sd)
    for wd in (workflow_dirs or []):
        subs += workflow_subs(wd, workflow_labels)
    for sub in subs:
        acts += _acts_from_file(sub.path, f"sub:{sub.label}", limit_blocks=None)
    return Stream(run_id=run_id, adapter="claude_code", source_ref=source_ref,
                  manifest=_manifest(acts), acts=tuple(acts))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Parse a completed Claude Code session dir into an act stream.")
    ap.add_argument("main_transcript", type=Path)
    ap.add_argument("--sub", action="append", default=[], metavar="LABEL=PATH",
                    help="a subagent file as LABEL=PATH (label = the subagent_type, verbatim)")
    ap.add_argument("--subagents-dir", action="append", default=[], metavar="DIR",
                    help="an Agent-tool session's subagents/ dir (agent-*.jsonl + .meta.json) to ingest (finding 23)")
    ap.add_argument("--workflow-dir", action="append", default=[], metavar="DIR",
                    help="a Workflow-tool run dir (journal.jsonl + agent-*.jsonl) to ingest (finding 17)")
    ap.add_argument("--workflow-label", action="append", default=[], metavar="AGENTID=ROLE",
                    help="optional agentId->role label for a workflow agent (else keyed by agentId)")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--source-ref", required=True)
    ap.add_argument("--limit-blocks", type=int, default=None)
    ap.add_argument("--persist", action="store_true", help="write to the harness acts schema")
    ap.add_argument("--schema", default="acts")
    args = ap.parse_args(argv)
    subs = [SubagentSource(*s.split("=", 1)) for s in args.sub]
    subs = [SubagentSource(label=s.label, path=Path(s.path)) for s in subs]
    wf_labels = dict(s.split("=", 1) for s in args.workflow_label)
    stream = parse_completed_session(args.main_transcript, subs, run_id=args.run_id,
                                     source_ref=args.source_ref,
                                     subagents_dirs=[Path(d) for d in args.subagents_dir],
                                     workflow_dirs=[Path(d) for d in args.workflow_dir],
                                     workflow_labels=wf_labels, limit_blocks=args.limit_blocks)
    for i, a in enumerate(stream.acts, 1):
        print(f"{i:3} {a.actor:22} {a.kind:20} {a.name or '':24} {a.target or ''}")
    print(f"# {len(stream.acts)} acts; manifest produced={sorted(stream.manifest.produced())}")
    if args.persist:
        sid = persist(stream, schema=args.schema)
        print(f"# persisted stream id {sid} to {args.schema}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
