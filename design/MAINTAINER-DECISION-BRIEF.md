# Maintainer decision brief — six things only you can decide

This document lays out six decisions in the autoharn project that no one else is authorized to
make for you — each one is prepared as a short question with a plain recommendation, not a
design document you need to evaluate from first principles. It is written for you specifically:
someone running this project who does not write code and does not want to read source files or
database schemas in order to answer a question. If you work through all six in one sitting, the
honest total time cost is roughly 30 minutes for the first five (three quick answers, one script,
and one five-to-ten-minute file edit) plus 15 to 30 minutes for the sixth, which is a one-time
setup step that takes longer if you still need to obtain a hardware security key.

Each section below follows the same shape: what the question actually is, why it exists, what
saying yes or no gets you, a recommendation, and exactly what to type or say. Where a decision has
a genuinely fine "no" answer — several of them do — that is stated plainly; declining is not a
mistake.

---

## 1. Should the "needs a second pair of eyes" flag catch everything a person does, or just one task?

*This decision is tracked internally under the name `review-gap-scope-ruling`; the full
technical write-up is [REVIEW-GAP-SCOPE-SEMANTICS-RULING.md](REVIEW-GAP-SCOPE-SEMANTICS-RULING.md).*

**The question.** The project can mark someone as needing a second reviewer: from that point on,
every single thing that person does is flagged as unreviewed until someone else checks it — not
just the one task you had in mind when you flagged them. This has surprised two different sessions,
who assumed the flag applied narrowly. The question is whether to formally accept that the flag is
all-or-nothing, or to commission work that would make it apply to just the specific task.

**Why it exists.** Two real incidents cost extra work because the flag's broad reach wasn't
written down anywhere as intended behavior; a formal answer stops the same confusion from
recurring and tells future builders which behavior is deliberate.

- **If you say yes** (accept the current all-or-nothing behavior as intended): nothing in the
  software changes. The behavior is simply written down as correct, and the instructions already
  added to the flagging command explain it clearly so the confusion doesn't repeat.
- **If you say no**: the door stays open to a future project that narrows the flag to a single
  task — real engineering work with its own review — a perfectly reasonable choice if you want
  that extra precision down the line.

**Recommendation: yes.** Both incidents that caused confusion were actually caused by flagging
the wrong person (a reviewer instead of the worker), not by the flag being too broad, and a flag
that catches too much is safer than one that catches too little.

**The act.** Say to whoever is running the session: "yes to the review-gap ruling" (or simply
"ratified" — the project's word for "approved by you"). Nothing to type into a terminal —
whoever is running the session records your answer and updates the ruling document to show it
is settled, dated, and attributed to you.

---

## 2. Two already-built, already-tested features are waiting for your sign-off

*This decision is tracked internally under the name `adr-amendment-texts`. The two paragraphs
below were drafted on 2026-07-10 and are quoted here word-for-word from the project's internal
planning notes at that date (git revision `9ecc23a` of HANDOFF.md, a snapshot you never need to
look up yourself — it is recorded here only so the exact original wording can be verified later
if anyone needs to).*

**The question.** This project keeps its foundational rules in a set of numbered documents
("ADRs" — think of them as the project's bylaws). Two of those documents describe features that
have since been fully built and tested, but the bylaws themselves haven't been updated to say so
yet, because updating them requires your explicit go-ahead. Below are the two paragraphs, exactly
as drafted, ready to append the moment you approve.

**Why it exists.** By standing project practice, the bylaws only change with your explicit
approval ("ratification") — an agent can draft the wording, but it can never file it as official.
These two paragraphs have been sitting, fully written, since 2026-07-10.

Amendment to the rule on avoiding overconfident excuse-making (a paragraph to append to
"Revisit #3" of ADR-0000):

> The out-of-frame rationalization-detector named here was minted as a mechanism:
> hooks/demurral_detect.py (observer; PreToolUse on AskUserQuestion + Stop), regression-tested
> against the adversarial corpus instruments/demurral_corpus.jsonl (n=121; precision 0.981,
> recall 0.929 raw / 0.852 at shipped timeout; witness banked in seen-red/demurral-detector/).
> Its costed classifier defaults off per world. Promotion to enforcing remains a maintainer act.

Amendment to the rule on doing work thoroughly rather than declaring it done early (a paragraph
to append to "Revisit #2" of ADR-0013):

> Rule 3's enforcement surface tightened from review-only toward the gate: the
> justification-as-suspect check now runs mechanically at the two canonical sites (the pre-loaded
> question; the completion claim). It warns; it does not refuse. The Rule's admission stands — the
> faculty it guards is still the faculty that acts — but the demurral now leaves a trace the
> executor did not choose to leave.

You do not need to parse every technical term in these two paragraphs. What matters: both describe
software that was actually built, tested against a measured accuracy number, and left switched off
by default — the paragraphs are catching the written rules up to what is already true, not asking
you to turn anything on.

- **If you say yes**: both paragraphs are appended verbatim to their respective rule documents,
  dated and attributed to you, and the written rules match reality.
- **If you say no**: the rule documents stay exactly as they are today. This does not switch
  anything off — the software described keeps running exactly as it does now either way; this
  decision only controls whether the bylaws mention it.

**Recommendation: yes, on both.** The underlying software is already built, tested, and off by
default under standing project policy — approving only brings the written record into line with
what is already true; it changes no running behavior.

**The act.** Say "ratified" to whoever is running the session. Both paragraphs are appended
verbatim, dated, and attributed to you, in [law/adr/0000-the-alpha-and-the-omega-type-driven-design.md](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)
and [law/adr/0013-execution-stamina-and-structural-completeness.md](../law/adr/0013-execution-stamina-and-structural-completeness.md).

---

## 3. A rule document about performance claims still describes a different, earlier project

*This decision is tracked internally under the name `adr0009-reinstance`; the document in
question is [law/adr/0009-performance-investigation-discipline.md](../law/adr/0009-performance-investigation-discipline.md).*

**The question.** One of the project's bylaws (ADR-0009) sets a rule for how anyone claims "this
change made things faster" — a reasonable rule in the abstract. But it was copied word-for-word
from an earlier, unrelated project and still names that other project's own file names and tools
throughout. The question is whether someone should rewrite it to describe this project's own
performance-testing setup, or leave it as an inactive historical document.

**Why it exists.** A rule that points to files and tools that don't exist in this project can't
actually be followed here as written; it either needs adapting to autoharn's own tools, or it
should stay formally understood as not-yet-applicable, so nobody wastes time chasing a reference
to code from a different codebase.

- **If you say yes**: someone rewrites the document's examples and tool references to point at
  autoharn's own experiment and measurement setup, and the rule becomes something people working
  on this project can actually use.
- **If you say no**: the document remains an inactive copy from the earlier project, out of scope
  for autoharn's own work — a reasonable state to stay in, especially if this project doesn't yet
  make the kind of "this got faster" claims the rule is meant to discipline.

**Recommendation: a mild yes, at your convenience, no urgency.** Adapting it removes a standing
inconsistency — a bylaw that names a different project's files — at the cost of one editing pass;
nothing in the project currently depends on this document being current, so there is no deadline
attached to this one.

**The act.** Say "yes to ADR-0009" or "no to ADR-0009" to whoever is running the session. On yes,
the document's scope and tool references are rewritten for autoharn and the change is recorded as
your decision, dated.

---

## 4. Turn experiment notes into a searchable record, with one script

*This decision is tracked internally under the name `research-ledger-apply`; the script it runs
is [bootstrap/apply-research-ledger.sh](../bootstrap/apply-research-ledger.sh).*

**The question.** Right now, when someone runs an experiment or measures something (for example,
"is the new version of X faster than the old one"), the result gets written up as a paragraph of
prose in a document. There is a ready-to-run script that instead creates a small, permanent set of
database tables for recording exactly that kind of result as structured, searchable data. The
script is fully prepared and waiting only for you to run it.

**Why it exists.** A number written into a paragraph can't be searched, compared, or aggregated
later without a person re-reading every document; a small database built for exactly this purpose
gives every future experiment result a permanent, queryable home instead.

- **If you say yes and run it**: the small database structure is created, and from then on any
  experiment's numbers can be recorded there and queried later, instead of relying on someone
  re-reading old write-ups.
- **If you say no (don't run it)**: nothing is created; experiment results continue to be written
  up as prose, exactly as today — a workable way to keep going if you'd rather not add another
  piece of database infrastructure right now.

**Recommendation: yes.** The script is self-protecting — it refuses to run twice, requires you to
type the database name back before touching anything, and rolls back cleanly if anything goes
wrong partway through — so the downside risk is low, and it directly enables the kind of
searchable evidence the project's evaluation work already wants.

**The act.** Open a terminal (the command-line window on your computer, where you type text
commands instead of clicking) in this project's folder on disk, and run:

```
bootstrap/apply-research-ledger.sh
```

It prints which database it's about to change, then asks: `Type the database name (research) to
confirm, or anything else to abort:`. Type `research` and press enter. You should see it print
`-- apply succeeded --`. Nothing is touched unless you type that exact word back.

---

## 5. Close a network security hole on the database machine

*This decision is tracked internally under the name `pg-hba-hardening`; the full technical
write-up is [PG-HBA-HARDENING.md](PG-HBA-HARDENING.md).*

**The question.** One database account has full administrator power over every database the
project uses — and today, that account can be reached from anywhere on the local network with no
password at all. It is the equivalent of a master key left in an unlocked front door because the
street is assumed to be private. The prepared fix requires a password for that one account, even
from trusted network addresses, while leaving every ordinary, limited-power account's access
completely unchanged.

**Why it exists.** This exact gap — the administrator account reachable, password-free, from the
network — is how a past incident was able to delete project governance data. It is still open
today; the fix has been investigated and written up, but never applied, because applying it to a
live database is your call to make, not an agent's.

- **If you say yes and apply it**: the administrator account requires a password from the network
  going forward, on every database on the machine at once, while every ordinary script or
  automated process the project runs keeps working exactly as before.
- **If you say no**: the administrator account stays reachable without a password from the local
  network, exactly as today — a real, named risk rather than a hidden one; if you're confident the
  network in question is genuinely private and trusted, leaving it as-is is a known trade-off, not
  an oversight.

**Recommendation: yes.** The document behind this was written specifically so your part takes
minutes rather than an investigation, and the underlying weakness already caused one real incident
in this project's history.

**The act.** This is a short sequence of steps, not a single line — each one is spelled out in
[PG-HBA-HARDENING.md](PG-HBA-HARDENING.md) section 3, with exactly what you should see at each
step. Budget about five to ten minutes, including two checks at the end that confirm it worked.
Start by opening a terminal (the command-line window on your computer) and running this first
command — it opens `psql`, the database's own command-line tool — and leave that session open
until the very last step (it is your safety net if anything goes wrong):

```
psql -h 192.168.122.1 -U bork -d toy
```

You should land at a `toy=#` prompt with no password requested — that is today's open state,
confirming you're connected before anything changes. From there, follow the document's section 3
step by step; it tells you, at each step, exactly what success looks like and what to do if
something looks wrong.

---

## 6. Generate your personal signing key — the one step only you can do

*This decision is tracked internally under the name `his-key-generation`; the step-by-step
walkthrough is [GPG-TRUST-LAYER-FAQ.md](GPG-TRUST-LAYER-FAQ.md), and the project's current,
honest state (no key on file yet) is recorded in [law/keys/README.md](../law/keys/README.md).*

**The question.** The project can cryptographically sign key actions — a formal approval you've
given, the exact instruction you gave a session, or the final state of a session's work log — so
that anyone, at any point in the future, can verify a specific action really came from you,
without having to trust the project's own infrastructure. This whole mechanism is already built
and tested, using a throwaway test key that stands in for a real one. Before it can verify anything
real, you need to generate one personal signing key (a small piece of cryptographic identity,
ideally stored on a physical hardware device) — this is the one step in the entire mechanism that
only you, personally, can perform.

**Why it exists.** A signature is only meaningful if it comes from a key nobody else controls.
The project is deliberately honest about having no such key on file today: every tool that checks
for one reports a loud, distinct "no key exists yet" rather than pretending to verify something it
can't.

- **If you generate a key**: real approvals, real task instructions, and real end-of-session
  records can be signed and independently verified by anyone, forever — not just trusted because
  the project says so.
- **If you don't (yet)**: the project keeps working exactly as it does today. Approvals are still
  recorded under your name in the project's activity log, just without a cryptographic guarantee
  attached — a perfectly fine state to remain in if you don't need that extra assurance right now.

**Recommendation: worth doing when convenient, ideally with a hardware security key (a small USB
device) rather than a key stored only as a file on your computer.** The verification mechanism is
already built and tested end to end on a test key; your key is the only missing piece standing
between "tested" and "actually protecting your real approvals."

**The act, in order:**

1. Generate the key:
   ```
   gpg --full-generate-key
   ```
   When prompted, choose the "(9) ECC (sign and encrypt)" option (or your `gpg` version's
   Ed25519-specific option), set an expiration you're comfortable with, and enter your name and
   email.

2. **Immediately after — before doing anything else with the new key** — GPG will have
   automatically written a "revocation certificate," a file that is the *only* way to ever cancel
   this key if it's ever lost or stolen. To find it, first find your key's "fingerprint" — a long
   unique ID string GPG assigns to your key, the way a serial number identifies a specific physical
   object:
   ```
   gpg --list-secret-keys --keyid-format=long
   ```
   The output includes a line that looks like this (a real example, from a test key made only to
   check this walkthrough — yours will show your own name and a different string):
   ```
   pub   ed25519/24E80FB7B970C89B 2026-07-11 [SC]
         BC9E286393F4091FB19DF7CC6A4B9704D73F4360
   uid           [ultimate] AUTOHARN TEST KEY <test-throwaway@example.invalid>
   ```
   The 40-character line under `pub` (here, `BC9E286393F4091FB19DF7CC6A4B9704D73F4360`) is the
   fingerprint. Using yours, copy the file at
   `~/.gnupg/openpgp-revocs.d/<your fingerprint>.rev` to a USB drive or print it, and store it
   somewhere away from this computer entirely. Never commit this file to the project, ever —
   anyone holding it could cancel your key.

3. Tell whoever is running the session that your key exists. Exporting the public half of the key
   and committing it to the project (as `law/keys/maintainer.asc`) is a step that can be done on
   your behalf from there — only the private key and the revocation certificate must stay under
   your own control; the public half is meant to be shared.

**What each signing act then buys you, once your key is committed, in one sentence each:**

- **Signing a ratification tag** — anyone, from any copy of the project, can verify you personally
  approved a specific rule or decision, without trusting the project's own claims about it.
- **Signing a commission** (a recorded task instruction) — the strongest of three levels of proof
  that a specific instruction to a session genuinely came from you, checkable independently of
  whoever carried the instruction out.
- **Signing a session's closing record** — a tamper-evident anchor: any later alteration of that
  session's activity log — even by someone with full database administrator power — becomes
  provably detectable, because the alteration would no longer match your signature.

---

## Related

The documents below are the full technical sources behind each decision above, for anyone who
wants more detail than this brief carries; you do not need to read any of them to answer the six
questions.

- [ABC-AUDIT-LOOP-RECIPE.md](ABC-AUDIT-LOOP-RECIPE.md) and
  [law/adr/0017-the-zero-context-reader.md](../law/adr/0017-the-zero-context-reader.md) — the
  legibility discipline this document was written and independently checked against.
- [REVIEW-GAP-SCOPE-SEMANTICS-RULING.md](REVIEW-GAP-SCOPE-SEMANTICS-RULING.md),
  [PG-HBA-HARDENING.md](PG-HBA-HARDENING.md), [GPG-TRUST-LAYER-FAQ.md](GPG-TRUST-LAYER-FAQ.md) —
  the full technical source documents behind decisions 1, 5, and 6, for anyone who wants more
  detail than this brief carries.
- [law/adr/0009-performance-investigation-discipline.md](../law/adr/0009-performance-investigation-discipline.md),
  [law/adr/0000-the-alpha-and-the-omega-type-driven-design.md](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md),
  [law/adr/0013-execution-stamina-and-structural-completeness.md](../law/adr/0013-execution-stamina-and-structural-completeness.md) —
  the bylaws named in decisions 2 and 3.
- [bootstrap/apply-research-ledger.sh](../bootstrap/apply-research-ledger.sh),
  [law/keys/README.md](../law/keys/README.md) — the script and the current honest state named in
  decisions 4 and 6.
