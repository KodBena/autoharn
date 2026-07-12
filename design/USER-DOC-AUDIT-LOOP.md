# USER-DOC-AUDIT-LOOP — running the fresh-context documentation review in your own project

Audience: adopter — an operator or agent working inside a project that was scaffolded FROM
autoharn (the framework whose tooling this project's `led`/`pickup`/`attest-doc` verbs, and this
page, all come from), using either `bootstrap/new-project.sh` or `bootstrap/track-work.sh`.

This page answers one question: **you just wrote or edited a markdown document in your own
project — what do you actually type to get it reviewed for legibility by a fresh, unbiased
reader, and how do you record that the review happened?** It is the step-by-step walkthrough
("what you type, what you should see") for the discipline autoharn calls the **A:B:C
fresh-context audit loop**. The loop itself, and why it exists, is defined in autoharn's own
`law/adr/0017-the-zero-context-reader.md` (the "zero-context reader" tenet) and operationalized
in `design/ORCH-ABC-AUDIT-LOOP-RECIPE.md` — both live in the autoharn checkout this project was
scaffolded from, not in your own project directory. This page does not repeat either in full;
it is the short path through them for your own project's documents.

## Why this exists, in one paragraph

A document you just wrote reads as complete to you because your own conversation silently
supplies every referent, every unstated assumption, every "obviously" — and that context
vanishes the moment the session ends. A reader who was not in that conversation — a teammate the
next morning, an agent picking the project back up cold — gets the skeleton, not the sentence.
The fix this project uses is not "try harder to write clearly"; it is to have a **genuinely
fresh reader** — a second AI agent invocation that has seen nothing but the document itself —
judge it before you call it done, because you (the author) are structurally the one reader who
cannot perform that judgment on your own text.

## The three roles

- **A** — you, or whoever wrote/edited the document. A has full context — the task that
  motivated the edit, the conversation that shaped the wording — and, for that reason, cannot
  self-certify the document's legibility (see the paragraph above).
- **B** — a fresh reviewer: a brand-new `Agent` tool invocation given ONLY the document's text
  and the zero-context-reader test (four questions: does every sentence parse, does every
  reference resolve, is every table/list introduced by prose, does the opening say in plain
  words what the document is and who it's for). B has never seen your conversation.
- **C** — whoever repairs what B found. Usually you (A) again, since C is executing concrete
  fixes B already specified, not making a fresh judgment.

## Step by step

**1. Finish writing or editing your document.** Any `.md` file in your project you want reviewed
— a README, a design note, an operating card. (Skip this loop entirely for code comments, commit
messages, or other registers ADR-0017 explicitly does not cover — see that document's own
"Scope" section if you're unsure.)

**2. Ask your Claude Code session to spawn a fresh reviewer.** In the same session where you
wrote the document, say something like: *"Spawn a fresh subagent as B in the A:B:C loop for
`<path-to-your-doc>` — give it only law/adr/0017-the-zero-context-reader.md's Rule 1 test and the
document's own text, nothing else from this conversation, and have it report either a list of
findings (each with a file:line, a verbatim quote, and a suggested repair) or an explicit CLEAN
verdict naming all four clauses it checked."* `design/ORCH-ABC-AUDIT-LOOP-RECIPE.md` (autoharn
checkout) carries the exact prompt skeleton this instruction is shorthand for, if you want to
paste it verbatim instead of paraphrasing.

**3. Read what B reports.** Either a CLEAN verdict, or a list of concrete findings. A bare "looks
fine" with no per-finding detail is not a valid verdict — ask B to redo it with specifics.

**4. If B found anything, fix it, then send the repaired document back to B once more.** This is
round 2, and it is the last one: if B still finds defects after a second pass, stop — don't run a
third round. That is a **non-converging review**, and the honest move is to record the DEFECT
verdict as escalated (step 5 still applies; you are not blocked, you are just recording the
truth) and get a second opinion before touching the document again.

**5. Record the result with `./attest-doc record`.** This is the step this page exists to add —
the loop above works the same way inside any Claude Code session, but until now a scaffolded
project had nowhere of its own to write the result down. Build a small JSON file naming your
document, an id for B's invocation, and one object per round:

```sh
cat > /tmp/my-attestation.json <<'EOF'
{
  "doc": "README.md",
  "b_id": "fresh-agent-2026-07-12-1",
  "escalated": false,
  "rounds": [
    {"round": 1, "verdict": "CLEAN", "findings": [],
     "clauses_checked": ["1a", "1b", "1c", "1d"]}
  ]
}
EOF
./attest-doc record /tmp/my-attestation.json
```

You should see something like:

```
doc_attestation_presence --record: appended attestation for README.md (schema doc-attestation/2,
content_sha256 8f492043aa67..., 1 round(s), escalated=False)
```

If your JSON is malformed — say, a DEFECT round with an empty `findings` list, which is an
umbrella verdict and not a real one — `./attest-doc record` refuses loudly and appends nothing:

```
doc_attestation_presence --record: REFUSED — malformed record for README.md:
  rounds[0]: DEFECT verdict carries no findings — an umbrella verdict is no verdict (ADR-0017,
  'B's verdict has a required shape')
```

Nothing partial ever lands in your ledger; you fix the JSON and re-run the same command.

**6. Check where you stand with `./attest-doc check`.** With no arguments it reports every
in-scope markdown file in your project — every `*.md` except the handful your scaffold itself
wrote (your own `CLAUDE.md`, `.claude/APPARATUS.md`, `.claude/HOOKS.md`,
`.claude/GOVERNED_FILES.md`, `keys/README.md` — those are autoharn's own prose, already reviewed
upstream, not yours to re-review) — classified as `ATTESTED` (a review exists for the file's
exact current bytes), `STALE` (a review exists, but you've edited the file since), or
`NO-ATTESTATION` (never reviewed). A worked example, run against a small project with one
document reviewed and clean:

```
attest-doc check: 1 doc(s) in scope, 5 scaffold-owned excluded, 0 waived.
  scaffold-owned (autoharn's own docs, attested upstream -- not yours to re-attest):
    .claude/APPARATUS.md
    .claude/GOVERNED_FILES.md
    .claude/HOOKS.md
    CLAUDE.md
    keys/README.md
  ATTESTED        README.md
attest-doc check: 1 ATTESTED, 0 STALE, 0 NO-ATTESTATION  (0 debt = clean)
```

Edit that same file afterward and re-run `check`, and the same document reports `STALE` instead
— the review you have on file no longer matches what's on disk, which is the honest signal to
run the loop again, not evidence anything is broken.

## Seeing your debt alongside everything else: `./distance-to-clean`

`./distance-to-clean` already gives you one composed read of everything outstanding across your
project's ledger (open reviews, unanswered questions, unclaimed work). It can fold in this
loop's own debt too, in a DOC-ATTESTATION line, but it does **not** count that debt by default —
adding the loop's debt to your "distance to clean" is something you opt into, the same way
adopting the loop itself is optional. Flip it on in `.claude/apparatus.json`:

```json
"doc_attestation": {"mode": "observe"}
```

Once flipped, `./distance-to-clean` prints a line like:

```
doc-attestation   : 1 debt (0 NO-ATTESTATION, 1 STALE, 0 ATTESTED) -- ['README.md (STALE)']
```

and that count joins the overall `TOTAL debt` figure. Leave it at the shipped default (`"off"`)
if you have not started running the loop yet — a debt count for a discipline you haven't adopted
is noise, not assurance, and the switch is there so you turn it on when it becomes true of you,
not before. Flipping it costs nothing to check (it's a file hash comparison, no network, no
billed call) — the thing that costs money is step 2 above, spawning B, and that cost is the same
whether or not this switch is on.

## What this does not do

- It never makes any AI verdict block anything. `./attest-doc check` and `./distance-to-clean`'s
  DOC-ATTESTATION line report presence and shape only — whether a review happened and was
  recorded correctly — never whether B's CLEAN/DEFECT judgment was itself right. Nothing here
  refuses a commit or an edit.
- It is not wired to your version control automatically. Your project may not even be a git
  repository (a plain `bootstrap/new-project.sh` scaffold creates none — it only becomes one once
  you run the scaffold with its `--new-world` flag) — `./attest-doc` needs none. If your project
  IS a git repo and you want a commit blocked on a
  missing attestation, that is a further, separate step you would wire yourself; it does not ship
  by default.
- It costs real money each time you actually run it. Spawning a fresh B, and a possible second
  round, is a real, billed `Agent` invocation each time — roughly two to three times the tokens
  of writing the document in the first place. `./attest-doc check`/`record` themselves, and the
  `distance-to-clean` switch, cost nothing; the loop (step 2 above) is where the spend is, and
  it is spent only when you choose to run it.

## Related

- `law/adr/0017-the-zero-context-reader.md` (autoharn checkout) — the law this loop implements,
  in full, including exactly what counts as "maintainer-facing" and what is exempt.
- `design/ORCH-ABC-AUDIT-LOOP-RECIPE.md` (autoharn checkout) — the exact B-invocation prompt
  skeleton this page's step 2 paraphrases, plus the record's full JSON schema.
- `gates/doc_attestation_presence.py` (autoharn checkout) — the module `./attest-doc` is a thin
  shim over; its own module docstring is the authoritative record format reference.
- `design/ORCH-SPEC-ABC-OFFERING.md` (autoharn checkout) — the design that decided this loop
  ships to your project at all, and exactly what stays upstream versus what lands here.
- `USER-GUIDE.md`'s Operate section, in your own project's autoharn checkout — where `./attest-doc`
  sits alongside `led`/`judge`/`pickup`/`audit`/`distance-to-clean` in the fuller verb reference.
