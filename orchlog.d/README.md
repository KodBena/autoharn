# orchlog.d/ — the changelog for a restarting orchestrator

This directory is a policy document plus a set of short notes. It exists so that an
orchestrator session that is starting fresh — after a restart, a handoff, or a long gap —
can learn, in a few seconds, what changed in this repository's operator surface since it was
last paying attention: a refusal that used to be spurious and now is not, a verb whose flag
order changed, a semantics change that would otherwise surprise a returning session. It is
read with the `./orchlog` verb at the repository root (`./orchlog` to list every note,
`./orchlog since <commit-ish>` to list only what landed after a given commit). This page is
the POLICY for who writes a note and when; the notes themselves are the other files in this
directory.

## Why the directory is named `orchlog.d/`, not `orchlog/`

The commissioning brief for this feature named the notes directory `orchlog/` and the verb
`orchlog`. A plain filesystem cannot hold both a file and a directory of the same name in the
same parent directory — it is not a style question, it is an impossibility (verified directly:
writing to a path that is already a directory fails with "is a directory"). Something had to
give, and the choice made here keeps the verb's name exactly as specified (`./orchlog`,
matching the one-word naming of every sibling operator verb — `pickup`, `judge`, `led`,
`audit`) and renames only the directory, to `orchlog.d/` — the standard Unix convention for
"the directory that backs a same-named thing" (`cron.d/`, `logrotate.d/`, `sudoers.d/`), which
reads, to anyone who has used a Unix system, as exactly what this directory is. This note
records the deviation and its reason in place, per this project's own rule that a design
deviation is stated, not silently taken (see the `orchlog` verb's own docstring for the same
note from the executable's side).

## The policy: land the note with the change, or with a named follow-up

When a commit changes something a restarting orchestrator would want to know about — a
refusal it may have hit and that is now fixed, a new operator verb, a changed semantics for
an existing one — **the same commit adds a note here**, or, if the note is written after the
fact, a follow-up commit adds one that names the original commit via the note's `subject:`
field (format below). Not every commit needs a note: this directory is deliberately
**nullable by construction** — most commits carry no note, and a commit that changes nothing
an orchestrator would need to relearn should add nothing here. The judgment of "would a
restarting orchestrator want to know this" is not mechanically checked (no gate enforces that
a note gets added); it is the same review-only judgment call this project already makes for
every discipline whose trigger is "is this a hazard/gap worth naming" rather than a
checkable shape (ADR-0011 Rule 1's honest declaration that some obligations are review-only).

## Note file format

Every file in this directory except this `README.md` is a note. A note is a plain markdown
file whose **optional** first line is exactly:

```
subject: <commit-ish>
```

naming the commit the note is *about* — used when a note is written some time after the
commit it describes, so a reader can jump straight to the change. Everything from the next
non-blank line onward is the note's **body**, written directly to the restarting
orchestrator: what changed, what symptom it resolves, and what to do differently now. Keep
it brief — a note is a changelog entry, not an essay; a paragraph or two is normal.

A note **never contains its own hash**. The commit that actually *added* the note file is
derived by `./orchlog` itself, straight from git's own record
(`git log --diff-filter=A -- orchlog.d/<file>`) — this is deliberate: a note authored in the
same commit that lands the change it describes cannot know its own future commit hash ahead
of time, so asking an author to write it would be asking for a guess or a two-step commit
dance. Deriving the adding commit from git dissolves that egg-vs-hen problem entirely: **git
is the correlation**, not the note's own text. This is also why `./orchlog`'s ordering and its
`since <commit-ish>` filtering both key on the *adding* commit, never on the optional
`subject:` field — `subject:` is displayed for context only.

## Doc-gate posture: this README is fully governed; individual notes are exempt

This `README.md` is a maintainer-facing policy document under ADR-0017 (The Zero-Context
Reader) and carries a full fresh-context (A:B:C) attestation like any other governed doc in
this repository — it is not itself an exception.

The **individual notes**, however, are a different kind of artifact: short, structured,
point-in-time changelog entries, closer in kind to a dated `BACKLOG.md` entry than to prose
documentation — ADR-0017's own Exceptions already name "point-in-time records" as outside the
zero-context-reader mandate's full weight, because forcing a two-round fresh-context review
loop onto every three-sentence entry in a directory whose whole design intent is "cheap to
add, most commits add none" would make the discipline itself the friction that discourages
landing notes at all — the opposite of what this directory is for. Each note therefore may
carry the inline waiver comment (shown here with the comment delimiters spelled out as HTML
entities, `&lt;!--` / `--&gt;`, so this README's own example text is not itself mistaken for
a real waiver by the gate that checks for one):

```
&lt;!-- doc-attest-exempt: point-in-time orchestrator changelog entry --&gt;
```

which, written for real (not spelled out) as `<!--` then `doc-attest-exempt: <reason>` then
`-->`, uses this repository's existing exemption mechanism
(`gates/doc_attestation_presence.py`'s waiver-token convention). A note is still reviewed
like any other change when it lands — the waiver exempts it from the *mechanized* A:B:C
gate, not from ordinary review — and a note that later needs a genuine documentation-quality
pass (it grew long, or its claims turned out to matter beyond a changelog line) can simply
drop the waiver comment and pick up full A:B:C coverage like any other document.

## Related

- The `./orchlog` verb (repository root) is this directory's one reader; its own docstring
  restates the note-file format and the `orchlog.d/` naming note above, so either document
  stands alone.
- [law/adr/0017-the-zero-context-reader.md](../law/adr/0017-the-zero-context-reader.md) is the
  documentation-legibility law this README complies with in full, and whose Exceptions this
  policy cites for the individual notes' lighter treatment.
- [gates/doc_attestation_presence.py](../gates/doc_attestation_presence.py) is the mechanized
  gate this README's own attestation satisfies, and whose waiver-token convention the notes
  above use.
