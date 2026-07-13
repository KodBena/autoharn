# USER-DOC-AUDIT-LOOP — running the fresh-context documentation review in your own project

This page answers one question: **you just wrote or edited a markdown document in your own
project — what do you actually type to get it reviewed for legibility by a fresh, unbiased
reader, and how do you record that the review happened?** It is written for an **adopter** — an
operator or agent working inside a project that was scaffolded FROM autoharn (the framework whose
tooling this project's `led`/`pickup`/`attest-doc` verbs, and this page, all come from), using
either `bootstrap/new-project.sh` or `bootstrap/track-work.sh`. It is the step-by-step walkthrough
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

This loop has three roles, each with a different relationship to the document's context:

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

The six numbered steps below are the whole procedure, in order, from finishing an edit to
recording that it was reviewed:

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

("Waived" is a third, less common bucket: a document you've explicitly marked out of scope for
this loop — via the same inline `doc-attest-exempt: <reason>` marker ADR-0017's Exceptions
section names — distinct from the scaffold-owned exclusions above, which are autoharn's own docs
rather than anything you marked yourself.)

Edit that same file afterward and re-run `check`, and the same document reports `STALE` instead
— the review you have on file no longer matches what's on disk, which is the honest signal to
run the loop again, not evidence anything is broken.

## Briefing your reviewer: never fuse "verify these fixes" with "sweep for anything else"

This section exists because of a real, dated mistake, not a hypothetical one: on 2026-07-13, an
orchestrator running this loop in a live deployment (`ent`, one of the projects this framework
governs) briefed its round-2 reviewer with BOTH jobs in one message — "here are the 4 findings
from round 1, confirm they're fixed, and also do a general legibility pass." That single briefing
choice is the exact anchoring shape autoharn's own upstream recipe
(`design/ORCH-ABC-AUDIT-LOOP-RECIPE.md`, the "ROUND-2 DISCIPLINE" section this page's step 4
already points at) diagnosed and now guards against. It was produced in good faith — nothing about
it looks careless — which is exactly why it is worth a page of its own: the harm is
**distributional** (it shows up as a gap between how many defects two different briefing styles
find, averaged over many reviews), not **common-sense-visible** (no single review looks wrong on
its own; a reviewer that was told about 4 known findings and reports "those 4 are fixed" looks like
it did its job correctly).

### Two jobs, two reviewers — never one reviewer doing both

A "verify these known fixes" pass and a "sweep for anything else, fresh" pass are different jobs
with opposite correct briefings, and collapsing them into one reviewer invocation loses the value
of the sweep:

- **The targeted verifier.** Given the document AND the specific list of prior findings to check
  off (e.g. "confirm findings 1–4 from round 1 are actually fixed in the current text"). Here,
  front-loading the known findings is **correct** — it is the entire job. This reviewer is not
  pretending to be unbiased; it exists to close out a specific, named list.
- **The genuinely blind fresh sweeper** — this is **B**, the fresh-context reviewer this page's
  "The three roles" section already defines. B gets **the artifact and the commission only** — the
  document's current text and the zero-context-reader test (or, in the A:B:C loop's own terms,
  ADR-0017's Rule 1 and this recipe's briefing) — and nothing else: no prior findings, and no
  mention that a correction pass even happened. B does not know it is a "round 2"; it does not know
  a "round 1" exists. Telling B what round 1 found, or even that there was a round 1, hands it a
  frame to confirm instead of a document to judge fresh.

Fusing these two jobs into one briefing — "verify the known list, and also sweep" — silently
converts the sweep into a second verification pass: the reviewer's attention centers on the named
findings (they were the concrete, actionable part of the brief), and the "also sweep for anything
else" clause gets the same thin coverage a human's eye gives to "and anything else you notice" at
the end of a checklist. This is **anchoring**, the same faculty-that-corrupts problem
[ADR-0014 (request a second opinion when a problem resists resolution)](../law/adr/0014-executor-second-opinion.md)
already names for a different context: ADR-0014 Rule 3 requires that a second opinion never be
pre-led with "your diagnosis, your frame, or your list of suspected [problems]," because "a brief
that says 'find the [defect] I missed' reproduces your lock in the second agent and collapses an
independent perspective into *one × M* — your single frame, run twice." A fused verify+sweep
briefing is precisely that: the "known findings" list is the frame, and the fresh sweep — the one
part of the briefing supposed to be independent of it — gets run *inside* that frame instead of
outside it. If your deployment ever asks a reviewer to **co-sign** or countersign a document (the
same distinct-actor-review idea this framework's `countersign`/[`review_gap`](../GLOSSARY.md#review_gap)
machinery names for ledger rows generally), the identical rule applies: a co-signer told "these N
things were fixed, please also check for anything else" is not an independent second opinion — it
is your own frame, co-signed.

### The witnessed evidence (dated 2026-07-13, so the claim is not asserted from vibes)

Two measurements from the same incident family, both on `design/ORCH-KR-TITRATION-EXPLORATION.md`
(a document inside the autoharn checkout itself — the framework dogfoods this loop on its own
documentation). The dated account lives in `design/ORCH-ABC-AUDIT-LOOP-RECIPE.md`'s "ROUND-2
DISCIPLINE" section (autoharn checkout) and, at the finer grain of a single dated entry, on
autoharn's own internal decision tracker as row 293 — an internal record your own project's
checkout has no access to and does not need to chase; it is cited here only as the dated
provenance for the numbers below, not as a link you can follow:

- **Confirmation-mode rounds found 0.** The document was attested CLEAN across **two** ordinary
  round-2-after-repairs passes — reviews that (like the fused briefing above) center their
  attention on "were the specific repairs made," not "sweep this document fresh." Both rounds
  reported CLEAN. Both times, the maintainer — reading cold, with no briefing at all — caught a
  real legibility defect the two confirmation-mode rounds had missed (a table-label type mismatch
  the first time, a sixth distinct defect the second time).
- **Adversarial fresh sweeps found 4, then 7.** When a reviewer was instead given *only* the
  document and the general legibility test — no list of what a prior round already found, no
  framing that repairs had just happened — it surfaced **4 more defects** the confirmation-mode
  rounds had never named. Later, after those 4 were repaired, a second such adversarial fresh
  sweep over the same document found **7 more findings** the confirmation-mode rounds (the same
  category named just above, not a different one) still never surfaced.

Same reviewer type (an ordinary fresh subagent), same document, same law being applied — the only
variable across these numbers is whether the reviewer walked in blind or was pointed at a known
list. Zero versus four and seven is the size of the harm a fused or list-anchored briefing hides.

A second, related defect from the same incident family: **a resumed reviewer re-asserted a stale
verdict against contradicting bytes.** A round-2 review that was a `SendMessage`-resumed
continuation of round 1's own agent (rather than a brand-new invocation) repeated its round-1
verdict **verbatim** against on-disk text that, by then, directly contradicted it — the resumed
agent's prior turn had already committed to a verdict in its own context and did not genuinely
re-read the repaired file. This is why the rule below is **fresh-fork-never-resume**, not merely
"brief the sweeper blind": even a reviewer given no findings list can still anchor on its own prior
verdict if it is the same live agent, resumed, rather than a fresh one.

### The four rules this section asks you to follow

Everything above compresses to four concrete rules:

1. **The two-agent split.** Never ask one reviewer invocation to both verify a named list of prior
   findings and perform a fresh sweep. If you need both, that is two separate `Agent` dispatches —
   a targeted verifier (front-loaded, correctly) and a genuinely blind B (artifact + commission
   only).
2. **Round-2-after-repairs is the WEAKER verdict.** Per this page's step 4 and the upstream
   recipe's "ROUND-2 DISCIPLINE" section: your round-2 B must repeat the FULL fresh sweep over the
   entire document as it now stands — never only "check that the named findings were fixed." A
   round 2 that only re-checks the round-1 finding list is not a valid round 2; it is a rubber
   stamp wearing round 2's clothes, and the 0-versus-4-and-7 numbers above are the measured cost of
   running it that way.
3. **Fresh-fork-never-resume.** Every round of B, at every step, is a brand-new `Agent`
   invocation — never a `SendMessage`-resumed continuation of a prior round's agent. A resumed
   agent already committed to a verdict in its own context and cannot genuinely re-read the
   document the way a fresh fork can.
4. **Verdict-as-final-message.** Whoever spawns B reads B's own final output as the verdict, full
   stop. B should never be asked to route its own report anywhere via `SendMessage` — to an agent
   type, a session it guesses is listening, or anywhere else. This is stated as its own rule in
   `design/ORCH-ABC-AUDIT-LOOP-RECIPE.md` ("B VERDICT ROUTING") because a verdict routed by
   `SendMessage` has been witnessed failing to deliver, repeatedly, across independent loop runs —
   printing the verdict as the final message is what makes it recoverable regardless of who
   dispatched the review.

None of this changes what you type in step 2 above — it changes what you put in B's briefing (give
it the document and the test, never a prior finding list or the fact that a correction pass
happened) and what you do with round 2 (a full fresh sweep, a new fork, a verdict you read from B's
own final message).

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

Where the fuller account of each cited rule, tool, or design decision lives:

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
- `law/adr/0014-executor-second-opinion.md` (autoharn checkout) — Rule 3's independence-brief
  discipline ("do not pre-lead") this page's "Briefing your reviewer" section applies to the
  verify/sweep split and to co-signer briefings generally.
- `design/USER-RECIPES-FAQ.md`'s "Documentation quality" section (autoharn checkout) — the short
  pointer entry that sends a reader here for the verify/sweep briefing discipline.
