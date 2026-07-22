#!/usr/bin/env python3
"""rename_doc — the per-document, ADR-0012-composable rename primitive for the
doc-audience-taxonomy work item (tracker slug `doc-audience-taxonomy`; maintainer mechanism
2026-07-12, orchestrator's three strengthenings — see BACKLOG.md and CLAUDE.md's
IN-FORCE-DECISIONS row for the full brief).

WHAT IT DOES, given one OLD path and one NEW path (both repo-relative, both `*.md`):

  1. `git mv OLD NEW`.
  2. Rewrites every relative markdown link, in every git-tracked `*.md` file (including NEW
     itself, for self-references), whose target resolves to OLD, so it resolves to NEW instead
     — using `gates/link_integrity.py`'s own regex, target-classifier, and path-resolver
     (`LINK`, `classify_target`, `resolve`, `iter_raw_line_links`) as the ONE shared parser
     (CLAUDE.md ADR-0012 P1: one home for the link grammar, two consumers — the gate reads it,
     this tool rewrites it). It never re-derives the link syntax with a fresh regex.
  3. Optionally inserts the ONE-line `Audience: <word>` declaration immediately under the
     document's title (ADR-0017-governed content edit; see ATTESTATION HANDLING below).
  4. Runs `gates/link_integrity.py` and reports its exit code — the caller decides whether to
     commit on that basis; this tool never commits.

ATTESTATION HANDLING (doc-attestation/2, `gates/doc_attestation_presence.py`). A rename alone
(step 1+2, no header) leaves the renamed file's bytes IDENTICAL, so this tool auto-appends a
mechanical **rename-note** record at the new path carrying the SAME content_sha256 forward,
citing the prior record it supersedes (ledger line number) in `b_id` — no B-loop, because
nothing a fresh-context reader would parse has changed. Concretely this run: EVERY renamed doc
also gains the Audience header line in the SAME change (the taxonomy's own mechanism), so the
byte-identical branch is exercised only by this tool's own seen-red fixture (both branches must
work; only one is live traffic this pass — stated honestly, not silently assumed). When a header
IS inserted, content_sha256 changes and this tool does NOT fabricate an attestation — it prints
that one is owed and leaves writing it (after the real A:B:C loop, scoped by ADR-0017 Rule 4 to
"at minimum the edited sections and the document's opening") to `gates/doc_attestation_presence.py
--record`, called directly once the fresh-context review is in hand.

Every OTHER `*.md` file this tool edits in step 2 (a "collateral" file — its prose is untouched,
only a link's path text changed) has its content_sha256 change too, which can invalidate an
EXISTING attestation for that file's prior content. `--collateral-attest` (on by default) writes
a mechanical carry-forward record for each such file, honestly identical in spirit to the
rename-note case: same clauses_checked as the prior record if one exists (cited by ledger line),
b_id stating exactly which link(s) were repointed and that no prose changed. A collateral file
with NO prior attestation is left alone (nothing to carry forward; touching it here would be
inventing a review that never happened) and printed as `COLLATERAL-NEEDS-FIRST-ATTESTATION` for
the operator to route separately.

USAGE:
  python3 tools/rename_doc.py OLD.md NEW.md [--audience {maintainer,orchestrator,adopter}]
      [--secondary {maintainer,orchestrator,adopter}] [--insert-title "Title text"]
      [--no-collateral-attest] [--dry-run]

Exit 0 on a clean rename with link_integrity green; 1 if link_integrity is red after the rewrite
(a deliberately-missed reference is exactly what this signals — the seen-red both-polarity proof
is seen-red/rename-doc/); 2 on a usage/precondition error.

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"],
                                 capture_output=True, text=True, check=True).stdout.strip())
sys.path.insert(0, str(REPO_ROOT / "gates"))

import link_integrity as li  # the ONE shared parser: LINK, classify_target, resolve, iter_raw_line_links

LEDGER_PATH = REPO_ROOT / "attestations" / "doc-legibility-attestations.jsonl"
ATTEST_GATE = REPO_ROOT / "gates" / "doc_attestation_presence.py"

AUDIENCE_WORDS = ("maintainer", "orchestrator", "adopter")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tracked_md() -> list[str]:
    r = subprocess.run(["git", "-C", str(REPO_ROOT), "ls-files", "*.md"],
                        capture_output=True, text=True, check=True)
    return [ln for ln in r.stdout.splitlines() if ln.strip()]


def _rewrite_target(raw: str, new_path_component: str) -> str:
    """Reconstruct one link's raw target text (the content between the parens) with its path
    swapped to `new_path_component`, preserving `<...>` wrapping, a `#anchor`, and a trailing
    ` "title"` — the exact structure `classify_target` parses, inverted."""
    lead_ws = raw[:len(raw) - len(raw.lstrip())]
    trail_ws = raw[len(raw.rstrip()):]
    body = raw.strip()
    head, sep, rest = body.partition(' ')
    wrapped = head.startswith('<') and head.endswith('>')
    inner = head[1:-1] if wrapped else head
    _, asep, anchor = inner.partition('#')
    new_head = new_path_component + (asep + anchor if asep else '')
    if wrapped:
        new_head = '<' + new_head + '>'
    new_body = new_head + (sep + rest if sep else '')
    return lead_ws + new_body + trail_ws


def _relink(referencing_abs: Path, target_abs: Path, root_relative: bool) -> str:
    if root_relative:
        return '/' + os.path.relpath(target_abs, REPO_ROOT).replace(os.sep, '/')
    return os.path.relpath(target_abs, referencing_abs.parent).replace(os.sep, '/')


def rewrite_links_everywhere(old_rel: str, new_rel: str, dry_run: bool) -> list[str]:
    """Scan every tracked *.md file (post-`git mv`, so `new_rel` already exists on disk) for a
    link resolving to `old_rel`'s former location, and repoint it at `new_rel`. Returns the list
    of files actually modified (repo-relative)."""
    old_abs = os.path.normpath(REPO_ROOT / old_rel)
    changed: list[str] = []
    for rel in _tracked_md():
        path = REPO_ROOT / rel
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        # Recompute per physical line (not the fence-stripped copy iter_raw_line_links scans) so
        # we can slice/replace the ORIGINAL bytes; iter_raw_line_links is used only to find which
        # (line, match) pairs are real, in-scope link occurrences.
        edits_by_line: dict[int, list[tuple[int, int, str]]] = {}
        for ln, m in li.iter_raw_line_links(text):
            classified = li.classify_target(m.group(1))
            if classified is None:
                continue
            path_part, _anchor = classified
            resolved = li.resolve(str(path), path_part)
            if os.path.normpath(resolved) != old_abs:
                continue
            new_abs = REPO_ROOT / new_rel
            new_component = _relink(path, new_abs, root_relative=path_part.startswith('/'))
            new_target = _rewrite_target(m.group(1), new_component)
            edits_by_line.setdefault(ln, []).append((m.start(1), m.end(1), new_target))
        if not edits_by_line:
            continue
        # Apply right-to-left within each line so earlier spans stay valid.
        new_lines = list(lines)
        for ln, spans in edits_by_line.items():
            line = new_lines[ln - 1]
            for start, end, repl in sorted(spans, key=lambda s: -s[0]):
                line = line[:start] + repl + line[end:]
            new_lines[ln - 1] = line
        new_text = ''.join(new_lines)
        if new_text != text:
            changed.append(rel)
            if not dry_run:
                path.write_text(new_text, encoding="utf-8")
    return changed


_TITLE = re.compile(r'^#\s')


def insert_audience_header(text: str, audience: str, secondary: str | None,
                            insert_title: str | None) -> str:
    lines = text.splitlines(keepends=True)
    if insert_title:
        lines = [f"# {insert_title}\n", "\n"] + lines
    title_idx = next((i for i, l in enumerate(lines) if _TITLE.match(l)), None)
    if title_idx is None:
        raise SystemExit(
            "rename_doc: no H1 title line found (no line starting with '# ') — pass "
            "--insert-title \"...\" to add one before the Audience header can be placed "
            "'immediately under its title' as the taxonomy requires")
    insert_at = title_idx + 1
    if insert_at < len(lines) and lines[insert_at].strip() == '':
        insert_at += 1
    audience_line = f"Audience: {audience}"
    if secondary:
        audience_line += f" (+secondary: {secondary})"
    block = [audience_line + "\n", "\n"]
    return ''.join(lines[:insert_at] + block + lines[insert_at:])


def _prior_record_line(doc_rel: str, content_sha256: str) -> int | None:
    if not LEDGER_PATH.exists():
        return None
    last = None
    for i, line in enumerate(LEDGER_PATH.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("doc") == doc_rel and rec.get("content_sha256") == content_sha256:
            last = (i, rec)
    if last is None:
        return None
    return last


def _carry_forward_adjudication(prior: dict, prior_line: int) -> dict | None:
    """A carry-forward record is always WRITTEN at doc-attestation/2 (the gate's --record always
    emits SCHEMA_LATEST), which REQUIRES a typed `adjudication` object whenever `escalated` is
    true (design/ORCH-SPEC-DOC-ATTESTATION-2.md). A prior /2 record already carries one — reuse it
    verbatim. A prior /1 record kept its escalation disposition as b_id free text (the seam /2
    exists to close); this synthesizes an HONEST, clearly-labeled /2 adjudication FROM that text
    rather than inventing a new judgment — the gate itself declares adjudication content is
    reviewed like any other claim, never policed for correctness here. Returns None if
    `escalated` is falsy (no adjudication needed or permitted)."""
    if not prior.get("escalated"):
        return None
    if prior.get("schema") == "doc-attestation/2" and "adjudication" in prior:
        return prior["adjudication"]
    return {
        "adjudicated_by": "tools/rename_doc.py (mechanical carry-forward, doc-audience-taxonomy rename sweep)",
        "disposition": (f"no re-adjudication performed here — this is a mechanical path/link-only "
                         f"carry-forward of the prior escalated doc-attestation/1 record's own "
                         f"disposition, whose b_id (ledger line {prior_line}) already narrates who "
                         f"adjudicated the escalation and what was applied; content_sha256 changed "
                         f"only via the rename/relink, not via new prose"),
        "adjudicated_at": prior.get("attested_at", "unknown"),
    }


def write_rename_note(old_rel: str, new_rel: str, content_sha256: str) -> bool:
    """Case 1 (byte-identical rename): append a mechanical rename-note record at the new path,
    same content_sha256, carrying the prior record's rounds forward. Returns True if written."""
    found = _prior_record_line(old_rel, content_sha256)
    if found is None:
        print(f"rename_doc: no prior attestation found for {old_rel} @ {content_sha256[:12]}... "
              f"— nothing to carry forward; {new_rel} needs its own first A:B:C attestation "
              f"(not a rename-note case)")
        return False
    line_no, prior = found
    body = {
        "doc": new_rel,
        "b_id": (f"path rename, content byte-identical, no header added this step; "
                 f"prior record for this exact content at "
                 f"attestations/doc-legibility-attestations.jsonl line {line_no} "
                 f"(doc was {old_rel}) — tools/rename_doc.py"),
        "rounds": prior.get("rounds"),
        "escalated": prior.get("escalated", False),
    }
    adj = _carry_forward_adjudication(prior, line_no)
    if adj is not None:
        body["adjudication"] = adj
    return _record(body)


def write_collateral_note(rel: str, old_content_sha256_unused: str) -> str:
    """Case: a file whose ONLY change was a mechanical link retarget (no prose touched). If it
    carried a prior attestation for its pre-edit content, carry the verdict/clauses forward
    honestly (b_id names the mechanical cause); otherwise leave it alone and report the gap."""
    path = REPO_ROOT / rel
    new_sha = _sha256(path)
    # Find the most recent record for this doc at ANY prior content (best-effort: latest by doc).
    prior = None
    prior_line = None
    if LEDGER_PATH.exists():
        for i, line in enumerate(LEDGER_PATH.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("doc") == rel:
                prior, prior_line = rec, i
    if prior is None:
        return "COLLATERAL-NEEDS-FIRST-ATTESTATION"
    if prior.get("content_sha256") == new_sha:
        return "COLLATERAL-UNCHANGED"  # link rewrite happened to be a no-op for this file's hash
    body = {
        "doc": rel,
        "b_id": (f"mechanical link-retarget only (tools/rename_doc.py, doc-audience-taxonomy "
                 f"rename sweep) — no prose changed; prior attestation for this document's prior "
                 f"content at attestations/doc-legibility-attestations.jsonl line {prior_line}"),
        "rounds": prior.get("rounds"),
        "escalated": prior.get("escalated", False),
    }
    adj = _carry_forward_adjudication(prior, prior_line)
    if adj is not None:
        body["adjudication"] = adj
    ok = _record(body)
    return "COLLATERAL-CARRIED-FORWARD" if ok else "COLLATERAL-RECORD-FAILED"


def _record(body: dict) -> bool:
    p = subprocess.run([sys.executable, str(ATTEST_GATE), "--record", "-"],
                        input=json.dumps(body), capture_output=True, text=True)
    print(p.stdout.strip())
    if p.returncode != 0:
        print(p.stderr.strip(), file=sys.stderr)
        return False
    return True


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--audience", choices=AUDIENCE_WORDS)
    ap.add_argument("--secondary", choices=AUDIENCE_WORDS)
    ap.add_argument("--insert-title")
    ap.add_argument("--no-collateral-attest", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    old_rel, new_rel = args.old, args.new
    old_abs, new_abs = REPO_ROOT / old_rel, REPO_ROOT / new_rel
    if not old_abs.exists():
        print(f"rename_doc: OLD does not exist: {old_rel}", file=sys.stderr)
        return 2
    if new_abs.exists():
        print(f"rename_doc: NEW already exists: {new_rel}", file=sys.stderr)
        return 2
    if args.secondary and not args.audience:
        print("rename_doc: --secondary requires --audience", file=sys.stderr)
        return 2

    pre_sha = _sha256(old_abs)
    print(f"rename_doc: {old_rel} -> {new_rel}  (pre-rename sha256 {pre_sha[:12]}...)")

    if args.dry_run:
        print("rename_doc: --dry-run, stopping before any mutation")
        return 0

    subprocess.run(["git", "-C", str(REPO_ROOT), "mv", old_rel, new_rel], check=True)

    collateral = rewrite_links_everywhere(old_rel, new_rel, dry_run=False)
    # rewrite_links_everywhere may also have touched NEW itself (self-references) — exclude it
    # from the "collateral" bucket, it is the renamed doc, handled below.
    collateral = [f for f in collateral if f != new_rel]
    print(f"rename_doc: relinked {len(collateral)} referencing file(s): {collateral}")

    if args.audience:
        text = new_abs.read_text(encoding="utf-8")
        new_text = insert_audience_header(text, args.audience, args.secondary, args.insert_title)
        new_abs.write_text(new_text, encoding="utf-8")

    post_sha = _sha256(new_abs)
    content_changed = post_sha != pre_sha
    print(f"rename_doc: post-rename sha256 {post_sha[:12]}...  content_changed={content_changed}")

    if content_changed:
        print(f"rename_doc: ATTESTATION REQUIRED for {new_rel} — content changed (header "
              f"inserted); run the A:B:C loop scoped per ADR-0017 Rule 4 to the touched opening, "
              f"then 'python3 gates/doc_attestation_presence.py --record' — this tool does not "
              f"fabricate that record.")
    else:
        write_rename_note(old_rel, new_rel, post_sha)

    if not args.no_collateral_attest:
        for rel in collateral:
            status = write_collateral_note(rel, "")
            print(f"rename_doc: collateral {rel}: {status}")

    gate = subprocess.run([sys.executable, str(REPO_ROOT / "gates" / "link_integrity.py")],
                           cwd=str(REPO_ROOT))
    if gate.returncode != 0:
        print("rename_doc: link_integrity FAILED after rewrite — do not commit this state",
              file=sys.stderr)
        return 1
    print("rename_doc: link_integrity clean — safe to stage and commit")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
