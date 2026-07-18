# Maintainer decision brief — five things only you can decide

Audience: maintainer

This is a wholesale rewrite of the decision brief, dated 2026-07-12. The prior edition (six
decisions, written earlier this same day) survives in git history — it is not deleted, just
superseded; this is the one live copy going forward, per this project's own "one live document,
never two" rule. Three of the prior six were answered by you or ratified since that edition was
written and now appear only as one-liners in "Settled since the last edition" below; one was
removed from your queue entirely by your own standing ruling; the remaining two, plus three new
ones, are the live questions below.

This document is written for you specifically: someone running this project who does not write
code and does not want to read source files or database schemas to answer a question. Each
section follows the same shape: what the question actually is, why it exists, what saying yes
or no gets you, one recommendation, and exactly what to type or say. Where a decision has a
genuinely fine "no" answer, that is stated plainly — declining is not a mistake.

**Honest total time cost, recomputed for this edition:** roughly 20–40 minutes for the three
quick items (one script, one optional model session, one scheduling nod), plus 15–30 minutes for
key generation if you haven't already got a hardware key on hand, plus 5–10 minutes for the
publish decision (item 5: one license choice and two terminal commands). The trust-domain
decision (item 3) carries no time budget at all — it is explicitly "answer whenever you get to
it," not part of today's arithmetic.

---

## 1. Generate your personal signing key — the one step only you can do, and it just got more load-bearing

*Tracked internally as `maintainer-key-generation`. Verified open on the tracker this session
(`./led work list`, still status `open`, no closing row). Walkthrough:
[GPG-TRUST-LAYER-FAQ.md](../../user-guide/USER-GPG-TRUST-LAYER-FAQ.md); current honest state (no key on file):
[law/keys/README.md](../../law/keys/README.md), which reads "AWAITING-KEY" as of this session's own
read.*

**The question.** Same as before: the project can cryptographically sign a ratification, a
task instruction, or a session's closing record, so anyone can verify it really came from you
without trusting the project's own infrastructure. The mechanism is built and tested against a
throwaway key; your real key is the only missing piece. What's changed since the last edition
is that three separate things now converge on this one gap, verified this session:

- **A new safety mechanism (kernel delta "s27") landed** that catches an administrator quietly
  deleting the *newest* rows off the end of the project's activity log — a gap the previous
  safety net (added earlier) didn't cover. Read its own fine print
  ([`kernel/lineage/s27-chain-high-water.sql`](../../kernel/lineage/s27-chain-high-water.sql), its
  "LIMITS" section) and the independently
  verified research behind it (this project keeps a running, append-only activity log of
  every decision and finding, called "the ledger"; entry 194 there records the check that
  matters here, checked this session against the published sources — this is evidence for an
  auditor, not something you need to go look up yourself): every construction in the published literature agrees that a log's own
  internal chain, however good, cannot defend against the log's own administrator from inside
  one system — the only real closing move is an **externally held, signed** anchor of "how far
  the log has reached." That anchor is exactly Ceremony 3 in your GPG walkthrough (§6 of
  [GPG-TRUST-LAYER-FAQ.md](../../user-guide/USER-GPG-TRUST-LAYER-FAQ.md)), and it needs your real key to mean
  anything.
- **A rule about disputed instructions is inert without a real key.** The project's rule (FAQ
  §5, verified this session at that exact section: "a CONTESTED commission... must be SIGNED...
  before it is relied upon") only has teeth once a real signature is possible.
- **The signing tool itself is already wired to expect your key.** `./verify-chain --head`
  (the command that produces the thing you'd sign) already refuses to run over a log the
  project's own tripwire has flagged as suspect (verified this session, in the tool's own header
  comment: it exits with an error rather than signing "a chain the witness itself flags").
  The machinery is waiting; only the key is missing.

**Why it exists.** A signature only means something if it comes from a key nobody else
controls — and the project is honest that no such key exists yet rather than faking one.

- **If you generate a key:** real approvals, real task instructions, and real session-closing
  records can be signed and independently verified by anyone, forever, including against a
  hypothetical future administrator (which could be a compromised copy of this project, not
  necessarily you) trying to quietly rewrite history.
- **If you don't (yet):** everything keeps working exactly as today. Approvals are still
  recorded under your name in the project's own activity log, just without the cryptographic
  guarantee — a fine state to stay in if you don't need that extra assurance right now.

**Recommendation: worth doing when convenient, with a hardware key (a small USB device) if you
can get one, rather than a software-only key.** Three separate pieces of the project now point
at this one missing step; none of them can be relaxed instead, because the whole point is a key
nobody else — including this project's own software — controls.

**The act, in order (unchanged from the last edition — this part was already good; commands
re-verified this session against [GPG-TRUST-LAYER-FAQ.md](../../user-guide/USER-GPG-TRUST-LAYER-FAQ.md) §1–§2):**

1. Generate the key:
   ```
   gpg --full-generate-key
   ```
   Choose the "(9) ECC (sign and encrypt)" option (or your `gpg` version's Ed25519-specific
   option), set an expiration you're comfortable with, and enter your name and email.

2. **Immediately after — before doing anything else with the new key** — find your key's
   fingerprint (a 40-character ID string, like a serial number):
   ```
   gpg --list-secret-keys --keyid-format=long
   ```
   GPG automatically wrote a "revocation certificate" — the only way to ever cancel this key if
   it's lost or stolen — to `~/.gnupg/openpgp-revocs.d/<your fingerprint>.rev`. Copy that file to
   a USB drive or print it, and store it away from this computer entirely. Never commit it to
   the project — anyone holding it could cancel your key.

3. Tell whoever is running the session that your key exists. Exporting the public half and
   committing it to the project (as `law/keys/maintainer.asc`) can be done on your behalf from
   there — only the private key and the revocation certificate must stay under your own control.

---

## 2. Turn experiment notes into a searchable record, with one script

*Tracked internally as `research-ledger-apply`. Verified open on the tracker this session, and
the script it runs still exists and is unmodified:
[bootstrap/apply-research-ledger.sh](../../bootstrap/apply-research-ledger.sh) (confirmed present,
executable, this session). Content unchanged from the last edition.*

**The question.** When someone runs an experiment or measures something (for example, "is the
new version of X faster than the old one"), the result is currently written up as a paragraph of
prose. A ready-to-run script instead creates a small, permanent database structure for recording
that kind of result as structured, searchable data. It is fully prepared and waiting only for
you to run it.

**Why it exists.** A number written into a paragraph can't be searched or compared later
without a person re-reading every document; a small database built for exactly this purpose
gives every future experiment result a permanent, queryable home instead.

- **If you say yes and run it:** the database structure is created; from then on, experiment
  numbers can be recorded there and queried later.
- **If you say no:** nothing is created; experiment results keep being written up as prose,
  exactly as today.

**Recommendation: yes.** The script refuses to run twice, requires you to type the database name
back before touching anything, and rolls back cleanly if anything goes wrong partway — the
downside risk is low, and it directly enables the searchable evidence the project's evaluation
work already wants.

**The act.** Open a terminal in this project's folder and run:

```
bootstrap/apply-research-ledger.sh
```

It prints which database it's about to change, then asks: `Type the database name (research) to
confirm, or anything else to abort:`. Type `research` and press enter. You should see it print
`-- apply succeeded --`. Nothing is touched unless you type that exact word back.

---

## 3. The trust-domain decision — the one standing wall behind all of this project's guarantees

*This item is new to this edition. Sources, both read in full this session: the five-lens independent review you
commissioned ([MAINT-RELITIGATION-SYNTHESIS.md](MAINT-RELITIGATION-SYNTHESIS.md)) and the separately
verified research literature (the ledger's entry 194). Tracked as the standing Tier-3 item
(this project's lowest-urgency priority bucket — no deadline, revisit when convenient) both
sources name; no separate tracker slug. It carries over from an earlier, separate document
([REGULATOR-ADOPTION-ASSESSMENT.md](MAINT-REGULATOR-ADOPTION-ASSESSMENT.md), a prior review
panel's assessment), which first raised this same single-trust-domain question — the five-lens
review above is a second, independent look at the same question, and both now agree.*

**The question.** Every part of this project's evidence trail — the person who runs the work,
the account that could verify it, the database administrator, and the company hosting the
database — is, today, the same one entity: you, on your own machine, under one hosting vendor.
Five independent review panels (asked to judge the project's design as if it had years of clean
adoption behind it) converged on the same single finding: this is **the** wall between "good
internal bookkeeping" and "assurance an outside skeptic would accept," and it is not something
more code can fix. Separately, a literature check (verified this session against the published
sources) confirms the same thing from research on tamper-evident logs generally: no surveyed
construction defends a log against its own administrator from inside one trust domain — every
real remedy either brings in a second key-holder, anchors the log's state somewhere external, or
relies on independently administered hardware.

**Why it exists.** This is not a defect anyone can code away; it is a structural property of
"one person runs everything," and the five-panel review plus the literature check both landed on
it independently, which is why it is presented to you now as a real decision rather than a
lingering TODO.

Your three real options, as the panel and the literature frame them:

- **(a) Accept the single-trust-domain limit in writing, as a known and understood bound.** The
  cheapest option, and an honest one — you are not hiding the limitation, you are naming it.
  Costs nothing to build; costs one sentence to state formally.
- **(b) A second key-holder.** A real second person with independent signing authority over the
  project's key decisions — genuinely raises the bar, but requires recruiting and trusting an
  actual second human, which is not always available or wanted.
- **(c) External anchoring of the project's chain state.** Periodically publish a fingerprint of
  the project's current state to something outside your own control — free, low-effort options
  exist (OpenTimestamps is the literature's standard low-cost example: a free service that
  timestamps a fingerprint against the Bitcoin blockchain, giving you independent proof a
  given state existed at a given time, without needing a second person at all).

**Recommendation: (a) now, (c) later if you want stronger assurance without recruiting anyone.**
Writing down the limit costs you nothing and is honest regardless of which other option you
eventually take; external anchoring (option c) is the next cheapest real upgrade and doesn't
require finding a second trusted person, which makes it the natural next step if you ever want
more than the written acknowledgment. Option (b) is worth keeping in mind but only if a genuine
second collaborator with signing authority becomes available — recruiting one just to satisfy
this item would be backwards.

**The act.** This has no deadline — it is explicitly a Tier-3, at-leisure decision; the panel's
own wording is "nothing urgently." When you're ready, tell whoever is running the session which
option (or combination) you want recorded, and it gets written into the project's law as your
ruling, dated and attributed to you.

---

## 4. Two small follow-ups from the Opus-readiness check you ran

*This item is new to this edition. Source, read in full this session: ledger rows 181 (the graded results) and
173 (the instrument's own stated limits).*

**Background, briefly.** You had a candidate model (Opus) graded against a set of real
questions this project has actually needed answered. Verified this session: the graded result
was 13 correct-and-cited-properly, 5 correct refusals of trap questions, and 1 wrong-but-fixable
answer (already fixed and merged) — no fabricated citations, no unsafe compliance with a trap.
That result only covers *knowledge and guidance* questions, though — the instrument itself says
plainly (row 173) that it does not cover *live judgment calls*, which is the other half of what
"ready" would mean.

**4a. Run the same questionnaire against a cheaper model (Sonnet), as an optional control.**

- **What it buys:** proof that the project's own documentation — not the model's raw
  capability — is what's carrying the result. If a cheaper model scores similarly, that's
  strong evidence the answers are genuinely there in the docs for anyone to find, not something
  only a stronger model can piece together.
- **Cost:** one model session, and a few minutes of your time to paste the same question sheet
  in again.
- **If you skip it:** the existing result stands on its own; you just don't get the extra
  confirmation of *why* it worked.

**Recommendation: worth doing, low cost, no urgency.** It's a cheap, already-designed
experiment (the instrument names it as optional, ready to run) that either strengthens
confidence in the documentation or flags a real gap — either outcome is useful.

**4b. Schedule the supervised live drill — the part the questionnaire admits it doesn't test.**

- **What it buys:** the other half of "ready" — whether a model makes good judgment calls in a
  live, running session (when to hand something back to you, when to escalate), not just
  whether it can answer questions correctly when asked directly.
- **Cost:** a real supervised session where you watch the model actually operate, rather than
  grade written answers — meaningfully more of your time than either of the other items here,
  and no fixed length since it depends on what comes up.
- **If you skip it:** the readiness picture stays half-verified — good on knowledge, unproven on
  live judgment.

**Recommendation: schedule it when you have a session to spend watching rather than doing.**
This is the one item here that can't be shortened; it is real supervision time, not a
five-minute act, so it's reasonable to wait for a convenient window rather than treat it as
urgent.

**The act.** For 4a, say "run the Sonnet control" to whoever is running the session — a fresh
Sonnet session gets the same question sheet, graded the same way. For 4b, pick a time and say
so; there's no prep needed beyond having a live session ready to be watched.

---

## 5. Publish the current work — which history goes public, and under what license

*This item is new to this edition. Source: your own ruling earlier today (publish before the
current model is phased out, as continuity insurance), plus a read-only publication-readiness
audit run this session — its full findings are on the project's activity log (the ledger), and
the load-bearing facts are restated here so you don't need to look anything up.*

**The question.** The repository is **already public**: an earlier version was pushed to
`github.com/KodBena/autoharn` on 2026-07-07, and anyone can see it today. What is NOT public is
everything since — roughly 260 commits of work and counting (all the machinery, documentation,
and safety mechanisms built since then; 262 when the audit measured it on 2026-07-12, and the
count grows as work continues — whoever runs the publish will state the exact live number at
push time) exist only on your machine, on a branch named `next`. Your stated intent is
that if the successor model can't maintain the project for you, a stranger who finds the
repository should be able to finish the work as they see fit. That needs two decisions from
you: which history to publish, and under what license.

**Why it exists.** Publishing is your act alone (standing rule), and the audit that clears the
way was completed this session: the full history — every commit on every branch — was swept for
secrets, private keys, credentials, and session transcripts, and came back clean; no personal
identifiers beyond your accepted placeholder identity; the two navigation gaps a stranger would
hit (the README not pointing at the front-door guide; setup commands naming your own LAN
database host with no explanation) were fixed and independently reviewed this session. One
caution stands: publish by pushing the one named branch, never with a "push everything" command
(`--all`/`--mirror`), because local scratch branches from this session's builder agents would
ride along.

**On the license (decided together with the push, because it determines what a stranger may
legally do):** today the repository has no license file at all, which legally means "all rights
reserved" — a stranger who finds it may read it but may NOT legally continue the work, which
would defeat your stated purpose in publishing. Adding one small standard license file fixes
that.

- **If you publish (and license it):** the complete current state becomes public, and a stranger
  finding it has both the material and the legal right to continue the work — your stated
  insurance goal, achieved.
- **If you don't (yet):** the stale 2026-07-07 snapshot stays public as-is; the real work
  remains only on your machine, and the insurance doesn't exist until you do publish.

**Recommendation: publish by fast-forwarding the public default branch to the current work, and
add the MIT license.** The two histories don't conflict (the current work is a clean,
straight-line continuation of what's already public — verified this session), so this is the
simplest honest story: one public branch carrying the complete history. MIT because it is the
shortest, most universally understood "do what you want, credit me, no warranty" license, which
matches "finish the work as they see fit" exactly; if you'd rather have an explicit patent
grant, Apache-2.0 is the standard alternative — either serves the purpose, and this choice is
yours, not something to delegate.

**The act, in order:**

1. Tell whoever is running the session which license you choose ("MIT" or "Apache-2.0" is
   enough) — the license file gets added and committed for you, under your name as copyright
   holder.
2. Then, in a terminal in this project's folder, publish:
   ```
   git checkout master && git merge --ff-only next && git push origin master
   ```
   You should see the merge print `Fast-forward` (never a conflict — if it says anything about
   conflicts, stop and say so instead of proceeding), and the push end with lines naming
   `master -> master`. Then switch back to the working branch: `git checkout next`.
3. Optional, afterward: also `git push origin next` so the working branch itself is public and
   the two stay in step from here on.

---

## Removed from your queue

- **The database network-access hardening item** (previously item 5, "close a network security
  hole on the database machine") is removed from this brief per your own 2026-07-12 ruling that
  host-perimeter questions are not re-raised to you. No action is being solicited on it here.

---

## Settled since the last edition

- **The two ADR amendment texts** (previously item 2) were ratified and appended — verified
  this session in [law/adr/0000-the-alpha-and-the-omega-type-driven-design.md](../../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)
  and [law/adr/0013-execution-integrity.md](../../law/adr/0013-execution-integrity.md),
  both carrying the exact quoted paragraphs; tracker item `adr-amendment-texts` is closed
  (`shipped`, law commit `1012e21`).
- **ADR-0009's re-instancing** (previously item 3) is done — verified this session in
  [law/adr/0009-performance-investigation-discipline.md](../../law/adr/0009-performance-investigation-discipline.md),
  whose Scope and Provenance sections now carry a dated, bracketed rewrite pointing at autoharn's
  own tools (the append-only ledger, `./judge`, `./audit`); tracker item `adr0009-reinstance` is
  closed (`shipped`, commit `47b6693`).
- **The "does the review flag apply to one task or everything" question** (previously item 1)
  did not get ratified as originally posed. Verified this session: you rejected the yes/no
  framing itself as too narrow ("there's a deontic smell to the entire question") and asked for
  general vocabulary instead; that broader design work now lives in a different document
  ([ORCH-SPEC-RESOURCE-REGISTRY.md](../../design/ORCH-SPEC-RESOURCE-REGISTRY.md) §4). The original tracker
  item is closed as `superseded`; the underlying software behavior (a flag catches everything a
  flagged person does) is unchanged and the plain-language explanation already added to the
  flagging command stands.

---

## Related

The documents below are the full technical sources behind each decision above, for anyone who
wants more detail than this brief carries; you do not need to read any of them to answer the
five questions.

- [ORCH-ABC-AUDIT-LOOP-RECIPE.md](../../user-guide/ORCH-ABC-AUDIT-LOOP-RECIPE.md) and
  [law/adr/0017-the-zero-context-reader.md](../../law/adr/0017-the-zero-context-reader.md) — the
  legibility discipline this document was written and independently checked against.
- [GPG-TRUST-LAYER-FAQ.md](../../user-guide/USER-GPG-TRUST-LAYER-FAQ.md),
  [law/keys/README.md](../../law/keys/README.md) — the full walkthrough and current state behind
  item 1.
- [bootstrap/apply-research-ledger.sh](../../bootstrap/apply-research-ledger.sh) — the script
  behind item 2.
- [MAINT-RELITIGATION-SYNTHESIS.md](MAINT-RELITIGATION-SYNTHESIS.md) — the five-lens review
  behind item 3, and [MAINT-REGULATOR-ADOPTION-ASSESSMENT.md](MAINT-REGULATOR-ADOPTION-ASSESSMENT.md) —
  the earlier, separate assessment that first raised the same question.
- [MAINT-REVIEW-GAP-SCOPE-SEMANTICS-RULING.md](../../design/MAINT-REVIEW-GAP-SCOPE-SEMANTICS-RULING.md) — the
  full record of the settled review-flag question, including your own transcribed answer.
- [law/adr/0009-performance-investigation-discipline.md](../../law/adr/0009-performance-investigation-discipline.md),
  [law/adr/0000-the-alpha-and-the-omega-type-driven-design.md](../../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md),
  [law/adr/0013-execution-integrity.md](../../law/adr/0013-execution-integrity.md) —
  the bylaws named in the settled items above.
