# Elucidation Consult — Ratification Edition (2026-07-22)

## What this document is

This document merges three separate pieces of work into one, and rewrites them in plain
language so that a reader with none of the background that produced them — no memory of
the original screens, the original conversations, or this project's internal shorthand —
can open any single section on its own and understand it.

The three pieces, in the order they happened:

1. **A "consult," phase 1.** In this project, a "consult" is a bounded, one-topic piece of
   analysis handed to a fresh instance of Fable (the name this project uses for its senior
   AI authoring collaborator), kept deliberately separate from the work being reviewed.
   (Editorial gloss, not a source quote: the maintainer's own stated reason for the
   separation, quoted in the RCA document itself, was "so as to separate concerns" — this
   file does not have a sourced basis for a stronger claim about sympathy or bias, so it is
   not asserted.) Phase 1 of this
   consult was shown two example screens from this project's setup wizard — a text-based
   interface a person runs when first configuring a brand-new installation of this
   software (the project calls the interface the "setup TUI" and the person running it a
   "founding operator") — and nothing else: no knowledge of how the screens were built. It
   found ten defects in how the screens present information to that operator. This is
   recorded in full and unedited at
   `design/CONSULT-FABLE-ELUCIDATION-RCA-2026-07-22.md` — called "the RCA document" for
   the rest of this file.
2. **The same consult, phase 2.** The consult was then given the implementation history
   behind those same two screens — the written instructions ("the brief") a human
   maintainer had given to an AI builder, and the report that builder produced — and asked
   to speculate on *why* those ten defects happened. Note the method: the maintainer
   deliberately did not ask the builder itself, on the standing view that a builder's own
   after-the-fact explanation of its own mistake is worth little; instead a separate,
   outside model was asked to reason about the cause from the evidence. This is the second
   half of the same RCA document.
3. **A follow-up consult, phase 3.** A further consult was asked to propose concrete fixes:
   six specific mechanisms meant to make each defect class either impossible to build or at
   least loudly visible when it recurs, rather than just written down as a lesson learned.
   This is recorded in full and unedited at
   `design/CONSULT-FABLE-ELUCIDATION-RCA-2026-07-22-PHASE3.md` — called "the phase-3
   document" below.

Both source documents are frozen, verbatim records of what the consulted model actually
wrote. This file does not edit them, and reading this file is not a substitute for reading
them where the original wording matters. What this file does is restate their content, one
self-contained piece at a time, in language that does not assume the reader already knows
this project's setup-wizard internals, its ledger, or its law documents (the "ADR"
numbered files under `law/adr/` that record the project's ratified engineering rules). No
claim is strengthened, weakened, or stripped of its stated qualifiers in the rewriting;
anywhere a passage could not be rendered plainly without changing what it asserts, the
original sentence is quoted directly and flagged as a quote rather than paraphrased.

Nothing in this document is itself a ratification decision. Part 3's mechanism sections
each end with a plain statement of what adopting that mechanism would commit the project
to — but whether to adopt any of them, in what form, and on what timeline, is the
maintainer's decision alone; this document deliberately does not include a checklist,
approval form, or recommendation of which to accept.

---

# Part 1 — The ten defects

Background common to all ten: the phase-1 consult was shown two example screens meant to
be shown to a founding operator during setup. The first ("specimen 1") lays out two ways
to get a database for the software to use — using a database that already exists and is
reachable, or having the installer stand up a brand-new, dedicated database — and states
what each path requires and does. The second ("specimen 2") is a "Principals & authority"
screen: it lists, per feature, four fields — `Aspiration` (what the feature is trying to
achieve), `Standards` (what named external standard, if any, the feature relates to),
`Mechanism` (what file or component implements it), and `External` (what happens outside
the software itself, such as a prerequisite or a manual step). Both screens are generated
from small structured data files this project calls `feature_facts` and its sibling files
`durable_decisions` and `principals_authority`. The screens were produced by an AI builder instance
following written instructions from a human-and-AI "orchestrator" pair, in the round of
work that followed a sixth attempt ("round 6") that had been retired for a different
reason: it had deleted real content in order to satisfy a formatting rule. (The originals
never number this later round explicitly; "the seventh round" would be an inference from
context, not a term either source document uses, so it is left unnumbered here.)

### D1 — A standard the project only aspires to got rendered as if it were already met

**Severity the consult gave it: CRITICAL — the worst of the ten.**

What happened: specimen 2's screen, in one entry, shows a bare line reading
`Standards: NIST SP 800-63`. NIST SP 800-63 is a named U.S. federal standard covering
digital identity. To anyone reading that screen, a name sitting in a field labeled
`Standards` reads as a claim that the feature meets, or is certified against, that
standard. But the actual underlying source material — the sentence this line was built
from — said something much weaker: the project *aspires to* that standard's way of
breaking identity down into parts (its "decomposition"), not that the project conforms to
it. The original wording was, in the consult's own phrasing, "aspiration:
NIST SP 800-63's identity/lifecycle/binding decomposition" — quoted here directly because
the difference between "aspires to X's shape" and "meets X" is exactly what changed, and a
paraphrase risks losing that difference again.

Why it matters: turning "we aspire to be shaped like this standard" into a bare standard
name in a field literally called `Standards` silently strengthened a weak, honest claim
into an unqualified one, on precisely the topic — certification against a federal identity
standard — where a founding operator is most likely to make a real trust decision based on
what they read. In a project whose whole audit culture is "claims carry witnesses" (every
claim about what has been done or verified should be backed by concrete, checkable
evidence, not asserted on faith), this is the single worst kind of defect: the rendered
screen now asserts something the source material never asserted.

A companion problem the consult calls out as the same root cause (labeled "D1a" in the
original): once the standard's name was pulled out into its own field, the sentence left
behind — "identity/lifecycle/binding decomposition" — no longer says whose decomposition
it is. The referent (the standard) was amputated into a different field, so the remaining
sentence doesn't fully make sense on its own either. The consult's own name for this half
of the defect: "referential binding broken by decomposition."

The consult's own name for this class of defect: "lossy decomposition of a compound claim
— fielding a sentence changed its truth value; an aspiration was laundered into a
standing." ("Standing" here means an established, accepted status — the claim went from
"we want to look like this" to "we already are this.")

### D2 — Internal project shorthand leaked onto the operator's screen

**Severity the consult gave it: HIGH.**

What happened: several items on the two example screens address the wrong reader. Some
specific instances the consult found: a note reading "(memory: config-fragments-need-the-
real-file -- pg_hba lines are never authored without reading the live target file first)"
— this is an AI collaborator's own internal note-to-self about how *it* should behave when
writing configuration files; a founding operator reading the setup wizard cannot act on
it, cannot verify it, and should never see the assistant's private working notes at all. A
phrase like "(the omega-lab shape)" refers to some earlier internal deployment the
founding operator, who is setting up a brand-new installation, has no way to know about.
"the s40/s41 family" is this project's internal numbering for a specific batch of changes
("delta" is this project's word for a discrete change) — meaningless outside the project.
And both screens display internal specification-document filenames (such as
`FABLE-SETUP-TUI-SPEC.md`) as though they were meaningful to the person using the wizard,
when they are really the project's own internal planning-document names.

Why it matters: this content was correct and useful *in its original home* — as an
internal audit trail meant for the project's own future maintainers or AI collaborators —
but it was copied verbatim onto a screen meant for someone with none of that background.
The consult's name for this: "audience-boundary violation — internal provenance and
workshop vocabulary rendered verbatim into operator-facing surface; the text elucidates
the builders' history, not the operator's choice."

### D3 — A raw, unfilled-in placeholder appeared on the actual screen

**Severity the consult gave it: HIGH.**

What happened: specimen 2 displays the literal text `<dest>/legacy/led`. `<dest>` is a
template placeholder meant to be automatically replaced with a real path when the screen
is generated — here that substitution never happened, and the raw placeholder syntax
reached the screen a real operator sees. Compounding the confusion: the path also contains
the word `legacy`, an unexplained label shown to someone setting up a brand-new
installation, who has no "legacy" anything yet.

Why it matters: beyond the immediate confusion of an unreadable line, this is what the
consult calls "a trust-destroying defect in a high-assurance product" — if the tool that
renders these screens is shown to leave unexpanded placeholders on-screen, an operator now
has reason to doubt every other line on the page, because they can no longer tell which
lines were correctly generated and which were not. The consult's class name: "template-
expansion failure / broken rendering pipeline visible in product."

### D4 — Design documents got filed as "mechanisms," and slots hold the wrong kind of thing

**Severity the consult gave it: HIGH.**

What happened, in three related instances: (1) both example screens list plain design
documents (planning write-ups, such as `design/FABLE-SETUP-TUI-SPEC.md`) under the
`Mechanism` field — but a design document is not a mechanism (an implementing component);
it is background reading or rationale, a different kind of thing than the field's name
promises. (2) In specimen 2, the `Aspiration` field for one entry contains mechanism-style
content ("via the s40/s41 family" — that internal change-numbering again) which then
*also* reappears, redundantly, in the `Mechanism` lines directly below it. (3) In
specimen 1, one entry's `Aspiration` field says "none named" and then, in the very next
breath, names something anyway ("house config-fragment discipline only") — so the field
simultaneously claims to be empty and holds content.

Why it matters: this project markets itself on having typed, structured data instead of
loose free-text notes — a schema (a fixed set of named fields, each meant to hold one kind
of thing) is only useful if each field actually holds the kind of thing its name promises.
Here the fields are populated by whatever happened to be nearby in the source text, not by
what kind of thing they actually are. The consult's class name: "slot-type violation /
cross-contamination — the schema exists but its fields are populated by proximity, not by
kind; a typed façade over untyped filing." The consult adds that for a project that
specifically sells itself on typed structure, this is a credibility problem: the artifact's
own internal structure fails the very standard the project preaches to others.

### D5 — The same field label means three different things in different places

**Severity the consult gave it: MEDIUM-HIGH.**

What happened: the field labeled `External` carries three unrelated meanings across the
two screens. In specimen 1's "existing database" entry, it means "no manual steps
required." In specimen 1's "dedicated database" entry, it means "manual actions a human
must go and perform on a separate machine." In specimen 2, it means something like "no new
software packages need installing, and, by the way, here is what this feature does
internally" — a positive description smuggled inside what reads like a negation ("no
new... but here's what it does").

Why it matters: a founding operator cannot learn what a field means by reading one section
and then trust that meaning in the next section — the same label silently changes its
contract depending on where you are on the page. The consult's class name: "inconsistent
field semantics — same label, shifting contract; the reader must re-derive the schema per
section."

### D6 — Empty fields get rendered as if they were content

**Severity the consult gave it: MEDIUM.**

What happened: the line `Aspiration: none named.` appears twice, once per screen, as an
ordinary content line — the field has nothing to say, but the screen still makes the
operator read and parse a sentence that amounts to "there is nothing here."

Why it matters: in a screen meant to help someone make a decision, every line the reader
has to read should earn its place. "None named" is what the consult calls "template
residue" — leftover machinery from how the data is stored, not information a reader needs.
Either the empty field should be left off the screen entirely, or something actually useful
should be said in its place. The consult's class name: "schema leakage — the storage shape
rendered as the presentation shape; nulls printed as prose." ("Null," a term borrowed from
databases, means an empty or absent value.)

### D7 — The screen answers the wrong question for the reader it claims to serve

**Severity the consult gave it: MEDIUM.**

What happened: the stated purpose of these screens is to help a founding operator decide
what to enable while setting up a new installation. Neither example screen actually
supports that decision. A line such as `Mechanism: tools/setup_tui/pghba.py` (a file path
inside the project's source code) is meaningful to a project maintainer with the code open
on their own machine, not to an operator sitting at a setup wizard with no code in front of
them. Meanwhile, the information that would actually help someone decide — what happens if
you pick this path, can you change your mind later, what do you need to already have in
place — is either missing or buried. The single most decision-relevant fact on either
screen — that the "dedicated database" path "requires a live, network-reachable Postgres
cluster the operator administers" (a fully working, separately-managed database server the
operator must already have running and be responsible for) — arrives last, tucked inside
the `External` field, rather than stated up front.

Why it matters: the consult's class name says it directly: "altitude mismatch —
implementation inventory presented where decision guidance was owed; the content answers
'what files exist' when the reader asked 'what should I choose and what will it cost me'."
("Altitude" here is used the way it's often used in writing advice — the level of
abstraction or distance from ground-level detail; the screen is pitched at the wrong
altitude for its declared reader.)

### D8 — The writing style is an internal audit log's style, not an explanation

**Severity the consult gave it: MEDIUM.**

What happened: the text throughout both screens is telegraphic — `label: value`, `label:
value`, one after another — with no connecting sentences explaining what any of it means
or why it matters. It reads like an audit record or an inventory list, i.e., writing suited
to this project's own internal evidence-keeping culture, but it is shown under a heading
that calls it an "elucidation" (an explanation meant to make something clear to a reader).

Why it matters: the register (tone and style) is honest — nothing in it is false on its
own terms — but it does not communicate to the reader it is supposedly written for. The
consult's class name: "register transplant — internal evidentiary register shipped as
user-facing explanatory prose."

### D9 — The two screens don't even look consistent with each other

**Severity the consult gave it: LOW-MEDIUM.**

What happened: specimen 1 has no section heading at all — instead, every line repeats a
prefix like "Existing-db path --" or "Dedicated-db path --" to fake the grouping a proper
heading would provide, forcing the reader to compare prefixes line-by-line to figure out
the structure. Specimen 2, by contrast, *does* get a heading ("Principals & authority")
with plain unprefixed fields below it — so the same underlying kind of record is displayed
two different ways within the same wizard. On top of that, specimen 2 repeats the
`Mechanism:` label three separate times for three separate mechanisms, instead of using one
labeled list.

Why it matters: a reader moving between screens in the same wizard has to re-learn the
visual layout each time, because there is no single, consistent way this project renders
"a labeled record with several fields." The consult's class name: "serialization
masquerading as layout, applied inconsistently — the renderer has no stable presentation
grammar for its own record type."

### D10 — Punctuation is doing several jobs at once and hard line-wraps confuse the reader

**Severity the consult gave it: LOW — the mildest of the ten.**

What happened: a plain double-hyphen (`--`) is used to mean an em dash (a punctuation mark
used for a pause or aside) in some places and a list-item marker in others — and on
specimen 1 it also visually collides with the line's own prefix separator, so the same two
characters are simultaneously a field separator and a parenthetical dash on the same
screen. Separately, long lines get cut mid-phrase with no visual difference between a
wrapped continuation and a genuinely new item (examples the consult quotes: "an /
already-reachable", "pg_hba install + / reload + createdb").

Why it matters: this is the least severe defect — a matter of visual hygiene rather than
meaning — but it still makes the screen harder to parse correctly. The consult's class
name: "untyped punctuation — one glyph carrying multiple structural roles; wrap policy
ignorant of the line-oriented format it wraps."

### How the consult ranked these ten against each other

In the consult's own words, given here as a direct quote because it is a judgment call
best left in its original form rather than re-summarized: "D1 is the only defect that makes
the artifact *assert a falsehood-shaped claim* (everything else makes it confusing, leaky,
or ugly); D2/D3 damage operator trust in the whole surface; D4–D6 corrupt the schema the
reader is being taught; D7–D8 make the content miss its purpose; D9–D10 are presentation."

---

# Part 2 — The causal findings (why this happened)

Background: after the ten defects above were diagnosed by a model that saw only the
finished screens, a second phase of the same consult was given the actual history behind
them — the written brief a human-and-AI "orchestrator" gave to an AI "builder" (called "the
implementer" below), and the report the implementer produced — and asked to speculate
about *why* the defects happened. The consult is explicit throughout that this is
speculation about mechanism, offered in place of asking the implementer to explain its own
mistake after the fact, which the maintainer considers worthless testimony (a person or
model explaining, after being caught, why they did something is rarely a reliable account
of what actually drove the decision at the time).

### Finding 1 — How the worst defect (D1) came to feel like the right, careful thing to do

The consult walks through four steps by which the standard-name defect (D1 above: an
aspiration to a standard got rendered as if the standard were already met) could have
arisen, noting that at every step the implementer was plausibly doing something locally
sensible.

**Step 1: the brief itself had already answered the question, by example.** The written
brief given to the implementer included, as a worked example of the target format, the
literal line `standards = ["NIST SP 800-63 ..."]` — using the real data, not a made-up
placeholder. When a brief shows the exact target data already sorted into a field, an
instruction elsewhere in the same brief to "choose the honest shape per file after reading
the actual content" is, in practice, already settled for that one piece of data — the
judgment call was made by whoever wrote the example, and the implementer would have had to
actively second-guess the person who commissioned the work to undo it. The consult's
guess: the implementer likely read the "choose the honest shape" instruction as applying
only to the other data points the brief hadn't already pre-sorted.

**Step 2: the original wording's grammar made the mistake easy.** The source sentence read
"aspiration: NIST SP 800-63's identity/lifecycle/binding decomposition" — note the
possessive `'s`. A possessive is a weak, easy-to-miss way of carrying meaning. Sorting text
into typed fields is essentially a search-and-extract operation: scan the sentence, find
the piece of text that matches a field's expected shape, and lift it out. "NIST SP 800-63"
is a perfect match for a field called `standards`; the possessive `'s` — which carries the
entire difference between "aspires to be shaped like X" and "conforms to X" — has nowhere
to go, because nothing in the schema (the fixed set of fields) is built to capture
grammar, only content.

**Step 3: the implementer's own report shows the loss was principled, not careless.** The
implementer's own summary of its work stated that its "aspiration" sentences were now "one
short citation-free sentence each" — meaning the implementer was following a self-imposed
rule that aspiration text should have all citations and references stripped out and moved
to their own dedicated fields. Under that rule, removing "NIST SP 800-63's" from the
aspiration sentence wasn't a mistake to the implementer — it was correctly filing a
citation into its proper home. This is the consult's central point: the defect is "what
conscientiousness looks like when the conservation law being enforced is 'no token lost'
rather than 'no claim strengthened.'" Every word survived somewhere on the screen — nothing
was deleted — but the *connection* between the standard's name and the qualifier that made
it an aspiration rather than a fact was lost, and a process built to check "did anything go
missing" has no way to notice a lost connection between two things that are both still
present.

**Step 4: the previous attempt's failure trained the wrong alarm.** The prior round
("round 6") had been retired specifically because it deleted real content to satisfy a
formatting rule. The consult's speculation: that history likely installed exactly one
alarm in the implementer's process — watch out for deleting things — and this defect
passes that particular check cleanly, because nothing was deleted; something was instead
promoted to a stronger claim than the source supported. The failure mode the implementer
had been sensitized against (destroying content) is close to the opposite of the failure
mode it actually committed (inflating a claim by rearranging content). Five rounds of
solid prior work would only deepen this: an implementer that has learned "I catch things, I
disclose gaps" has calibrated itself against defects that look like loss or bugs, and this
defect looks like neither — it is only visible if you re-read the finished screen fresh, as
if for the first time, and ask "what does this now claim?" — a step nothing in the process
prompted anyone to take (this is Finding 2, below).

A companion note: once the standard's name is extracted out of the possessive phrase, the
words left behind ("identity/lifecycle/binding decomposition") have no subject anymore —
nothing in the process re-checks the leftover text to see if it still reads as a complete,
sensible claim; it only checks that the leftover text is still well-formed as a string.

### Finding 2 — Why the project's own automated checks did not catch any of this

The project already had automated checks ("fixtures," meaning small tests that confirm a
piece of work meets certain mechanical rules) in place for this round of work. The consult
found that none of them could have caught defects D1 through D8 above, for a structural
reason, not bad luck. Three examples, quoted because the precision matters:

- One check confirmed "no rendered line contains a bare pipe [the `|` character]" — this
  only checks that the *old*, previous rendering format was removed. It has no way to look
  at whether the *new* content is accurate, because it was never designed to look at
  content at all.
- Another check confirmed "components render as separate labeled elements" — meaning: if N
  pieces of data went in, N separate labeled fields came out. This confirms the schema
  (the typed field structure) was applied, but cannot ask whether applying it preserved
  the original meaning. The consult notes this check would, if anything, count D6 (empty
  fields rendered as content lines) as *correct*, since an empty field rendering as a
  labeled line is exactly the shape this check rewards.
- A third check confirmed that a data-loading step correctly refuses malformed input
  ("red-first" in this project's vocabulary, meaning the check is proven to correctly fail
  before it is trusted to correctly pass). This check is sound and did its job — and is
  irrelevant to every one of the ten defects.

The consult's general diagnosis: every one of these checks tests a "mechanical invariant"
— some fixed, checkable property of the change itself (does it avoid a banned character,
does it produce the right number of fields, does a refusal fire correctly) — because
mechanical invariants are the only thing a cheap automated check can test. Whether the
finished screen actually gives a founding operator a true, useful picture is a property of
how a human reader experiences the output, and nothing in the original brief asked anyone
to check *that*. So the checks were real, and they passed honestly — they were just
witnesses to the wrong question. The consult ties this to a pattern this project has
separately named on the *auditor's* side of similar work (a documented tendency, referred
to in this project's decision ledger — the project's append-only log of maintainer
rulings and findings, read via a tool called `./led` — as ledger row 1887's gloss: "false-MET —
requirements read down to fit found mechanisms"): here
the same pattern shows up on the *builder's* side — "elucidation is honest and useful" got
silently redefined, in practice, as "passes the three things we know how to test," and
passing those three things felt, sincerely, like having achieved the goal.

One further point: to catch this kind of defect automatically, someone would first have
needed to write down, in advance, what the *original* text actually claimed ("the source
asserts aspiration-to, not conformance-with") so a check could compare the before and
after. Nobody did that — the one person who understood the original claim's real strength
(whoever first wrote the underlying checklist line) was not part of this round of work at
all, and the brief's own worked example asserted the opposite of what would have been the
correct comparison point.

### Finding 3 — Who caused which defect: brief, prior data, or this round's builder

The consult splits responsibility for the ten defects into three sources.

**Caused mainly by the written brief the orchestrator gave the implementer:**
- D1/D1a (the standard-name inflation) — the brief's worked example was the direct cause,
  as Finding 1 above describes; the implementer's citation-stripping rule contributed, but
  was executing the brief's own example faithfully.
- D6 (empty fields rendered as content) — the brief's instruction to render "each
  component as its own labeled element," combined with a fixed four-field vocabulary
  (Aspiration/Standards/Mechanism/External), reads naturally as "always render all four
  fields." Nothing in the brief said to hide an empty field, and — per Finding 1's Step
  4 — an implementer carrying a recent memory of being penalized for *deleting* content
  would not invent the idea of suppressing an empty field on its own initiative. From the
  implementer's point of view, writing "Aspiration: none named" is honest disclosure, not
  noise — exactly the behavior this project's "no umbrella claims, no unstated gaps" norm
  rewards.
- Part of D9 (the inconsistent screen layouts) — the brief specified how to render one
  data element but, in the excerpt available, gave no rule for how to group or head a
  screen covering multiple options; specimen 1's prefix-repetition trick was one
  reasonable way to fill that genuine gap in the instructions.

**Caused mainly by where the underlying data came from (checklist log lines repurposed as
screen content):** the source data behind these screens originated as short, one-line
entries in an internal audit log — text meant for the project's own future auditors, where
internal references are the entire point.
- D2 (internal shorthand leaking through) — every one of the internal-sounding phrases
  (the internal deployment reference, the memory note, the internal change numbering, the
  internal spec filenames) was *correct, appropriate content for its original genre*: an
  internal audit-log line. Moving that content onto an operator-facing screen crossed an
  audience boundary without anyone translating it for the new audience; the brief's
  instruction was to reshuffle this content between fields, and nothing in that
  instruction could ever remove or rewrite it — doing so would have risked tripping the
  same content-deletion alarm from Finding 1's Step 4.
- D3 (the raw placeholder) — almost certainly literal text already present in the source
  log line, where it was harmless (a log entry describing a path pattern in the abstract).
  A field-by-field reshuffling of existing text preserves it faithfully; only someone
  reading the finished screen fresh, as an actual reader, would notice it doesn't belong
  there.
- D5 (the `External` field meaning three different things) — this inconsistency predates
  the current round of work: whoever originally wrote these log lines used the word
  "external" loosely, meaning something a little different each time. Turning loose,
  informal log text into a rigid, typed field *froze* that pre-existing looseness into
  what now looks like a broken, inconsistent contract. The implementer's instruction to
  "choose the honest shape per file" was given per individual file, with nothing asking
  for consistency of meaning *across* files.
- D7/D8 (wrong altitude, wrong register) — the checklist-log style simply *is* an
  inventory-of-mechanisms style; whoever first decided, in an earlier round, to reuse
  these log lines as operator-facing explanation is the original source of this problem —
  this round inherited content whose genre was already wrong, and was instructed to
  restructure it, not to rewrite its voice from scratch.

**Caused mainly by the implementer's own choices, this round:**
- D4 (design documents filed as mechanisms) — the brief's own worked example for the
  `Mechanism` field only showed database-schema files as examples; the implementer's
  decision to also file a design-document citation as a third "mechanism" entry was its
  own classification choice. The implementer's own report reveals it actually understood
  the type mismatch — describing its own rule as "one file-path/ledger-row citation per
  entry" — meaning it was privately treating the field as "any citation to a file," not as
  "mechanism," and did not notice the tension between that private definition and the
  field's stated name. The consult calls this the clearest example of a defect the
  implementer owns outright.
- The related D4 instance where mechanism-sounding content was left inside an aspiration
  sentence after its citations were stripped out — an artifact of treating "make this
  sentence citation-free" as a simple find-and-remove-parentheses operation rather than a
  genuinely meaning-based edit.
- The absence of any recorded misgiving — across five solid prior rounds, this implementer
  had built a habit of honestly flagging gaps and uncertainties in its own work; the fact
  that nothing in its process generated even a candidate doubt about this defect is itself
  informative, and is the same fixture-blindness described in Finding 2, experienced from
  inside the implementer's own process rather than from outside.

**Shared and low-interest:** D10 (the punctuation and line-wrap issues) traces to this
project's general house habit of using plain ASCII punctuation, combined with the brief
never stating a line-wrap policy — the consult calls this the "lowest interest" item on the
list.

### Finding 4 — The orchestrator's own share of the blame, stated plainly

The consult is explicit that the party who wrote the brief and directed this round of work
(referred to throughout as "the orchestrator" — the human-and-AI pairing that commissions
and directs a round of building work) bears a substantial share of the responsibility, and
on the single worst defect (D1), the largest share. Three specific points, each restated
here in full because each is a distinct claim:

1. **The brief's worked example was itself a classification decision made without reading
   the source carefully — and it carried the authority of a specification.** Putting the
   real data `standards = ["NIST SP 800-63 ..."]` into the brief as an example made the
   brief the *first* place this mistake was made; the implementer only reproduced it. An
   instruction elsewhere in the same brief to "choose the honest shape after reading the
   actual content" does not cancel out a worked example that already shows one specific
   answer — a worked example built from real data functions as a reading already
   performed, by the person who commissioned the work, and that reading outranks a general
   instruction sitting next to it. Had whoever wrote the brief read the original source
   sentence carefully before choosing that example, the possessive ("NIST SP 800-63's...")
   was there to notice.
2. **The brief asked for, and tested for, mechanical structure — and asked for nothing
   about meaning.** Every deliverable named in the brief was mechanical: the schema, a
   refusal-on-bad-input check, correct element rendering, a size measurement. The actual
   purpose of the screens — helping an operator understand something true — was never
   written into the brief as something that would be tested at all. A brief that says
   "render this as typed fields" and never says "the finished screen, read cold by someone
   with no background, must claim no more than the source claimed, and must actually help
   the stated reader decide something" has, in effect, defined "done" in a way that
   D1 through D8 all satisfy. The implementer built exactly what was asked for, and its
   checks confirmed exactly what was askable.
3. **The brief introduced a dedicated `Standards` field into a body of data that, as far as
   the consult could tell, contained only one standard-shaped entry among roughly 29 total
   entries.** Creating a dedicated field for something creates pressure to fill it, and
   whatever ends up in that field automatically reads as more authoritative than the same
   words would have read inline in a sentence — a bare standard's name sitting alone in a
   field literally called `Standards` carries a claim of conformance that the same name,
   embedded in a sentence, never had. The very existence of that field is part of how D1
   happened, and creating that field was the orchestrator's design choice, not the
   implementer's.

The consult is equally explicit about what the orchestrator is *not* responsible for: the
earlier decision (in a prior round) to reuse internal audit-log lines as operator-facing
explanation in the first place — though the consult hedges this one: that earlier decision
lies outside the evidence this consult was given, and it, too, might turn out to have been
orchestrator-directed — and D4's design-document-filed-as-mechanism problem, which actually
went against what the brief's own example showed.

### Finding 5 — Named patterns in how an AI builder's judgment can go wrong

The consult names several recurring patterns of reasoning it believes are visible in this
episode, useful because they may recur in future rounds of work even on unrelated tasks:

- **Rules standing in for goals.** The formatting rules given to the implementer (no
  pipe characters, a fixed field structure, a refusal check) were meant to serve an
  unstated underlying goal ("the operator reads something true and useful"). Because the
  rules were checkable and the goal was never written down as something to check, the
  rules quietly became the entire target — and the automated checks then confirmed that
  the rules were followed, which felt like confirming the goal was met.
- **Instructions read more narrowly than intended.** "Choose the honest shape per file"
  ended up read as "for the files the brief hadn't already pre-sorted"; "elucidation"
  ended up read as "however the existing data renders once schema-fied"; a general
  expectation of consistency ended up read as "internally consistent within one section,"
  which is how D5 (the drifting meaning of `External`) survived unnoticed.
- **The "conservation proxy" — a newly named pattern.** The consult names this pattern
  because it believes the project's existing vocabulary doesn't already cover it: after
  the prior round was penalized for *deleting* content, the implementer's sense of
  integrity became calibrated almost entirely around "did I lose anything" — and inflating
  a claim by rearranging still-present content walked straight through that check
  unguarded, because nothing was lost. In the consult's own words: "no content lost"
  standing in for "no meaning changed." D1 is described as this pattern's textbook
  example: every word survived somewhere on the screen, and the claim got stronger anyway.
  The consult links this to the same pattern this project has already named on the audit
  side — ledger row 1887's gloss: "false-MET — requirements read down to fit found
  mechanisms" — here it appears minted fresh on the building side, and the consult adds a
  caution: any future brief that reminds a
  builder about a past deletion mistake, without also naming this inflation-by-rearranging
  risk, is liable to reproduce the same blind spot.
- **"Worked-example supremacy" — a second newly named pattern.** A worked example inside a
  brief, if it uses real data from the actual task rather than made-up sample data,
  functions as a pre-graded answer for that specific piece of data, not as a mere
  illustration of the general shape wanted — and any nearby instruction giving the builder
  room for its own judgment does not, in practice, reopen a question the example already
  answered. The consult's practical conclusion: if a project wants a builder to genuinely
  exercise per-item judgment, its briefs must show the *shape* of what's wanted using
  made-up, synthetic content — never real data from the corpus being worked on.

The consult's one-line overall summary, quoted directly because it draws all the strands
together: "D1 was committed first by the brief (seeded example), executed faithfully by a
builder whose integrity-detector had been tuned by history to fire on deletion and
therefore read claim-inflation as tidiness; the fixtures could not see any of D1–D8 because
every witness attested a mechanical invariant of the delta while the defects live in what
the artifact asserts to its reader — a proposition no one commissioned a witness for. Brief:
D1, D6, part of D9. Provenance: D2, D3, D5, D7, D8. Implementer: D4 and the missing
misgiving. The orchestrator's share is real and largest exactly where the defect is worst."

---

# Part 3 — Six proposed mechanisms

Background: a further, separate consult ("phase 3") was then asked to propose concrete
fixes for the defect classes above — not general advice, but specific mechanisms with a
stated scope, a stated enforcement point, a stated cost, and a named person or role who
benefits from each one ("named consumer" — this project's standing rule that any proposed
mechanism must name a specific person or role who would actually use it, or it gets
dropped as ceremony rather than adopted). The consult says it was commissioned by the
maintainer "in the spirit of ADR-0000 and ADR-0011," and it is explicit that this
phase-3 document itself was not committed by the consult — the orchestrator installs it.
The consult was also explicit, up front, about
things it deliberately did *not* propose, and it kept its reasons in three distinct
categories rather than one blanket exclusion:

- **Already adopted elsewhere:** (1) the rule that briefs must use made-up example data
  rather than real data (Finding 5's "worked-example supremacy" fix, already adopted), and
  (2) the requirement that operator-facing work be checked by someone reading it cold, as a
  fresh reader (also already adopted — this is called the "cold-reading witness" below —
  and recorded at ledger rows 1120–1121). Mechanisms M3 and M4 below build a mechanical
  floor *under* these two adoptions; they do not restate them, they backstop them.
- **Already legislated, but not enforced:** the visual/layout defects D9 and D10 above, and
  half of D6, which the consult says are already covered by an existing project rule about
  user-interface construction (referred to as "ADR-0019," specifically its Rule 1, plus a
  pair of companion rules this project calls "C12" and "C13" — all part of this project's
  numbered rule document about interface-building). If these recur, the consult treats the
  recurrence as a finding that the existing rule is not being enforced strongly enough — an
  enforcement-gap finding grounded specifically against what C12 and C13 already declare as
  their covered surfaces — not as a gap calling for a brand-new rule.
- **Out of reach, and said so as such:** none of the six mechanisms below reads meaning.
  Wherever the actual question is one of semantics — what a sentence means, not what shape
  it has — the honest ceiling is human review, and each place that ceiling applies is named
  explicitly where it comes up, rather than left as a silent gap.

The distinction between the three categories matters: the first needs no further action at
all, the second is a live defect against a rule that already exists on the books, and the
third is a limit the consult is naming on purpose rather than a gap it failed to notice.

Each mechanism below is written to stand alone. Where a mechanism references this
project's law documents (its "ADR"s — numbered Architecture Decision Records that record
ratified engineering rules) or its decision ledger (the append-only log of maintainer
rulings, read with a command-line tool called `./led`), a short plain-language gloss is
given in place, rather than assuming the reader already knows them.

### M1 — Require every reference to an outside standard to state its relationship, not just its name

**What it forecloses:** D1/D1a above — the defect where an aspiration to a standard's
shape was rendered as though the standard were already met.

**What is proposed:** the underlying problem, stated generally, is that a claim whose
truth depends on the *relationship* between two things (here: the project and the
standard) was being stored in a data structure that only captures the two things
themselves, and discards the relationship connecting them — the possessive "NIST SP
800-63's" carried the entire claim, and a simple field-extraction operation has no way to
notice grammar like a possessive. The fix: a reference to an external standard, framework,
or certification is never stored as a bare name. It is stored as a small structured record
naming (a) which standard, and (b) what the actual relationship is, chosen from a fixed,
closed list of options: "aspires to" (we want to be shaped like this), "informed by" (this
influenced our thinking), "named only" (mentioned for context, no claim), or "conforms to"
(we actually meet this) — and "conforms to" specifically cannot be recorded at all unless
it is accompanied by a pointer to actual evidence proving it. Under this rule, a bare
standard name sitting alone in a field is not a possible thing to store — the software
itself refuses to accept it. A second, independent invariant sits on the renderer's side of
the same fix, not just the loader's: the screen itself always displays the relationship
word alongside the standard's name, never the name alone — so even along some path that
manages to bypass the loader's own refusal, a relation-less standard name still cannot
reach the founding operator's screen, because the renderer has nothing to show unless a
relationship word is present to show alongside it.

This would be checked automatically in two places: when the underlying data is first
written or loaded (the software refuses malformed data before it is ever stored), and
again when the screen is actually generated for display. It also proposes scanning any
free-text field for the standard's own name and refusing if it appears there without the
structured relationship record — so a standard's name can't sneak back in through prose
instead of the proper field. The set of standard identifiers this check recognizes is not
hand-maintained inside the check itself; it is derived from the project's own
`law/STANDARDS-REGISTRY.md` file, so adding a new standard to that one registry
automatically extends what the check looks for, with no second place to remember to update.

Restated in plain terms, the check keys on the *shape of the value* being stored, not on
the name of the field holding it — so a bare standard name is caught wherever it turns up,
not just in the one field this incident happened to involve. In scope, alongside
`feature_facts` (where the D1 defect actually shipped), are its sibling data-split files
`durable_decisions` and `principals_authority`, plus any future corpus that the same family
of data loaders reads — the check is written against what a value looks like, so it
automatically extends to new files without needing to be told about them by name.

One more thing this mechanism does, stated as a single clause: it takes ADR-0000 Revisit
#4 Clause 2's existing proviso that a standard may be "named, not conformed" — previously a
sentence of prose someone had to remember and apply by hand — and turns that same proviso
into a type the software enforces, so it is no longer something a reader has to recall, it
is something the data structure itself cannot violate.

The consult is explicit about what this mechanism does *not* catch, and names two distinct
gaps rather than one: (i) any free-form writing under this project's `design/` and `docs/`
folders is out of scope for this check entirely, regardless of whether it happens to name a
standard — that territory is governed by an existing project rule about disclaiming
standards-scope in such writing, plus ordinary review; and (ii) separately, and not limited
to those two folders, conformance-flavored prose that never names a specific registry
entry by its recognized identifier (for instance, a sentence saying "complies with best
practice" without naming a specific standard) has no identifier for the check to hook onto,
anywhere in the project — for that, the mechanism states plainly that the honest limit is
human review, backstopped by the already-adopted cold-reading witness requirement, not a
machine check.

One more thing worth stating plainly: no numeric threshold exists anywhere in this
mechanism — there is no count, percentage, or size limit being checked. That absence is
deliberate and declared, not an oversight; the check is a vacuous one (it either finds a
bare standard name and refuses, or it doesn't), and the consult names it as such rather
than dressing it up with an invented number.

**Adopting this means:** every time any part of the project's data records a relationship
to a named external standard, whoever enters that data must explicitly choose one of the
four relationship words above — the software will refuse to accept a bare standard name
with no stated relationship, and will refuse a "conforms to" claim with no evidence
attached. This adds a small amount of friction to entering this specific kind of data (the
consult frames the friction itself as the point — being forced to choose is being forced to
be honest), and it requires building the actual refusal check described, including a
negative control run under this project's rule for exactly this kind of check (the
2026-07-02 amendment to ADR-0011): the check is fed the real defect that was actually
shipped (the literal `standards = ["NIST SP 800-63"]` line), and it earns no credit for
passing anything until it is first shown correctly rejecting that exact case. A registry identifier turning up in ordinary prose
*about* the standard, rather than actually claiming a relationship to it, is a possible
false positive here — but the consult expects that to be rare in fact corpora of this
project's kind, and where it does happen, the refusal itself teaches the fix (move the
mention into the typed escape). The named consumers of this mechanism are: the founding
operator reading the screen, who is protected from a conformance claim the project cannot
back up, and the fact author at the point of entering the data, who is taught the honest
distinction by the refusal itself.

### M2 — Require every content-restructuring change to account for every piece of moved text, not just check nothing vanished

**What it forecloses:** the "conservation proxy" pattern from Finding 5 above — the
general pattern behind D1, where a change that reorganizes existing prose into structured
fields severs a meaningful connection between two pieces of text while every individual
word survives somewhere, and the only self-check performed was "did anything disappear,"
which this kind of change passes automatically because nothing needs to disappear for the
underlying claim to still be inflated. This mechanism also, as a side effect, would have
caught the duplication half of D4 — "via the s40/s41 family" surviving both in the
Aspiration field and, redundantly, as Mechanism entries.

**What is proposed:** because Finding 1 showed the actual damage can live in something as
small as two characters of grammar (the possessive `'s`), this mechanism proposes tracking
individual runs of characters, not whole words or sentences. Any project work that
restructures existing written material into structured fields must produce, alongside the
change itself, a "meaning ledger" — a record that accounts for every stretch of the
original text that either moved to a different field, was dropped entirely, or was copied
into more than one field. Each such stretch must be given exactly one of four labels:
"moved without change in meaning," "moved but its connecting relationship was cut and
retyped" (this is the label that exists specifically to force someone to notice and answer
the exact question nobody asked in the actual incident), "dropped, with a stated reason,"
or "duplicated, with a stated reason." A change with any unaccounted-for stretch of moved,
dropped, or duplicated text does not get merged into the project.

The consult is explicit about what this doesn't cover: text that is entirely paraphrased
rather than moved (where there's no clean "before" chunk to track, so the check degrades to
a general written justification, reviewed by a person) and any content that is written
fresh in the same piece of work (there is no "before" version to compare against at all).
Both of those cases fall back to ordinary human review, stated plainly as the honest limit.
The measurement unit is the actual characters of the real source text being changed —
deliberately not a rough percentage or a sample, because a sampling-based check is exactly
the kind of shortcut this mechanism exists to prevent. Stated as an explicit figure rather
than left implicit: the requirement is that 100% of the character residue gets a
disposition, with no piece of it exempted — a percentage-based threshold below that would
itself be the same read-down this mechanism exists to catch.

**Adopting this means:** any future project work that reorganizes existing prose into
structured data fields must produce this accounting as part of the change, and the change
is blocked from merging until every moved, dropped, or duplicated stretch of text has a
stated reason. This is real, meaningful extra effort, roughly proportional to how much a
given change actually rearranges text — which the consult argues is also roughly
proportional to how risky that change is, so the added effort lands where the risk is
highest. Because this kind of large content-restructuring change is rare, the standing,
day-to-day cost to the project is expected to be near zero. Its negative control is to run
the gate on the actual s40/s41 elucidation migration — the named artifact this defect
actually shipped in — confirming it correctly flags both the moved
"NIST SP 800-63" text and the dropped possessive `'s` before being trusted anywhere else.
The declared false-positive surface is whitespace/punctuation normalization noise — the
residue matcher normalizes whitespace only, nothing else, and that choice is stated plainly
in the gate.
The named
consumers of this mechanism are: the reviewer of the migration, who today has no artifact
to check meaning-preservation against and so cannot actually check it; and, secondarily,
whoever investigates a future incident like this one, who gets a record of dispositions to
read instead of having to reconstruct what happened from scratch.

### M3 — Separate what's said to insiders from what's shown to a founding operator, and refuse unfilled placeholders on sight

**What it forecloses:** D2 (internal project shorthand leaking onto the operator's screen)
and D3 (the raw, unfilled-in placeholder appearing on the actual screen). This is described
as a mechanical safety net underneath the already-adopted requirement that operator-facing
work get a cold read by an outside reader — not a replacement for that requirement.

**What is proposed:** the project currently has no way to mark "this piece of data is
meant for insiders" versus "this piece of data is meant for a founding operator" — audience
is treated as understood rather than as something the software can check. The fix: any
piece of data destined for an operator-facing screen may only reference paths belonging to
a stated, approved list of operator-visible things (the project's user-facing commands and
documentation) — anything else is refused unless it's explicitly marked as "deliberately
exposed to the operator, with a one-line reason," which itself becomes something a human
reviewer can check. Separately, any text destined for an operator screen is scanned for the
literal pattern of an unfilled placeholder (something like `<word>`) and refused if found —
this specifically targets the actual site where the D3 defect appeared, since a
placeholder failing to get filled in is a substitution problem that happens after data is
first loaded, at the point the screen is actually built.

The consult is explicit that this mechanism only catches things with a recognizable pattern
(a path-shaped reference, a placeholder-shaped pattern) — an insider term or internal
shorthand with no distinctive telltale shape (like referring to something only insiders
would recognize by an ordinary-sounding name) would pass straight through this check
undetected. That remaining gap is explicitly left to the already-adopted requirement that a
human read the finished operator-facing screen cold, before it ships.

In scope, as with M1, are `feature_facts` and its sibling data-split files
`durable_decisions` and `principals_authority`, plus any future corpus that the same family
of data loaders reads.

As with the other mechanisms here, no numeric threshold exists anywhere in this one either —
that absence is deliberate and declared, not an oversight; the check is a vacuous one, named
as such rather than dressed up with an invented bound.

**Adopting this means:** two separate checks, running at two separate times. The path-
reference check runs at write/load time, against stored corpora — any operator-facing path
reference outside an approved list is refused when the data is first entered or loaded,
unless explicitly and visibly marked as an intentional exception. The placeholder check
runs separately, later, at the point a screen is actually rendered or constructed — this is
deliberate, because an unfilled placeholder is a substitution failure that can arise after
the data has already loaded cleanly, which is the actual site where the D3 defect appeared;
checking only at load time would have missed it. The main ongoing cost is that legitimate
content which does need to reference something internal must be explicitly marked with a
one-line justification each time — a small, repeatable cost, not a large one. It would need
to be tested against the actual shipped defects (the literal `<dest>/legacy/led` line and
the literal `design/FABLE-SETUP-TUI-SPEC.md` reference) to confirm it correctly flags both
before being trusted elsewhere. Ordinary prose that merely happens to resemble a path is a
possible false positive on the path-shaped check, but the consult expects that to be low in
a corpus of this project's kind, and each one is a one-marker fix; the placeholder check is
expected to have near-zero false positives, since an angle-bracket literal reaching
operator-facing text is essentially always the defect it is looking for. The named
consumers of this mechanism are: the founding operator, who is spared the workshop's
interior vocabulary; the fact author, who is taught by the refusal; and the executor of the
cold-reading witness requirement, whose scarce attention is reserved for the tail that only
a human reader can catch.

### M4 — Every claim that something was "verified" must state what, specifically, it verified

**What it makes visible:** the pattern in Finding 2 — a set of automated checks that each
attest some mechanical property of a change (no banned character, correct field count, a
refusal firing correctly) but collectively never attest anything about whether the finished
product actually serves its reader, while being experienced, sincerely, as having verified
the whole thing.

**What is proposed:** every time a piece of project work reports that something was
"WITNESSED" (this project's term for a claim backed by concrete, checkable evidence, as
opposed to an unsupported assertion), and every individual automated check in a test suite,
must be labeled with which of two kinds of thing it actually confirmed: a "delta-contract"
claim (a mechanical property of the change itself — a format rule, a count, a refusal
firing) or an "artifact-purpose" claim (something stated in terms a real reader or user of
the finished thing would recognize — what a cold reader of the output would actually take
it to mean, or be able to do with it). Any piece of work whose end product is meant to be
read or used by a person must include at least one "artifact-purpose"-labeled check or
claim, or must explicitly say "this was not exercised, and here is the concrete reason why"
— the same three-way honesty standard (witnessed / refused-as-expected / unexercised-with-
a-reason) this project already applies elsewhere, gaining one more dimension to sort
claims by.

The consult is explicit about the limit here: nothing can mechanically judge whether a
label is *true* (a mechanical check mislabeled as "artifact-purpose" would still pass this
count) or whether a purpose-check is actually *adequate*. Those remain matters for a human
reviewer. What this mechanism changes is that the absence of any purpose-focused check
becomes visible and loud — a reviewer no longer has to reconstruct, from nothing, that no
one ever checked whether the thing actually worked for its reader; they just see an empty
column where that check should be.

**Adopting this means:** every report of completed work and every automated test must be
tagged with which of the two claim types it actually makes, and any work whose output is
meant for a human reader must show at least one "artifact-purpose" claim or an honest
"not exercised, here's why." This is mechanically enforced only in one specific place: where
the project's conformance instrument (the tool that checks a piece of work against its
commissioned claims) is the one carrying the report, the instrument itself requires the
`attests:` field to be filled in, and can fail a reader-facing piece of work outright if it
carries zero "artifact-purpose" entries. Everywhere else — reports that don't go through
that instrument, and whether any given tag is actually true rather than just present — stays
review-only; nothing mechanical can check truthfulness of a tag, only its presence. The cost
is small to record (one tag per claim) but the practical effect is that some pieces of work
will start honestly reporting "this was not checked against its actual purpose, and here is
the blocker" — which is a form of friction that is itself useful information, not overhead
to be minimized away. The named consumer of this mechanism is the orchestrator reading the
report to decide whether to accept the work — today that reader cannot tell "the
deliverable was witnessed" apart from "the change to the deliverable was witnessed," and
this whole episode showed that the difference between those two was the entire event.

### M5 — License an AI builder to stop and ask, whenever a brief's instructions and a brief's examples disagree

**What it forecloses:** the residual risk behind "worked-example supremacy" (Finding 5) —
even after the rule that briefs must use made-up example data is adopted, a brief could
still pre-resolve a judgment call it claims to be delegating to the builder through some
other channel: a list of items, an aside in the prose, an attached document from an earlier
round of work, or — the consult specifically flags this as the strongest version of the
problem and one nobody had previously named — a test/fixture shipped with the brief that
already assumes a particular answer.

**What is proposed:** any brief that hands a judgment call to the builder must include a
clearly labeled list of exactly which judgment calls the builder is being trusted to make.
Standing rule: if the builder, anywhere in the brief or anything attached to it, finds an
instance where that judgment call already appears resolved one way or another, it must
treat this as a licensed, expected event — stop, flag the conflict, and ask — rather than
silently going along with either the delegation or the pre-resolved answer. Making the stop
free and expected is the point: an implementer should never have to guess whether raising
this counts as insubordination.

The consult is explicit that actually detecting when some part of a brief secretly
resolves a listed judgment call is a matter of meaning, not something a mechanical check
can catch — no automated tool can read "this clause resolves that judgment." The one
mechanical assist is that the labeled list of delegated judgment calls now exists at all,
giving a human reviewer something concrete to check the rest of the brief against.

Here too, no numeric threshold exists anywhere in this mechanism; that absence is
deliberate and declared, not an oversight — the check is vacuous, named as such.

**Adopting this means:** every brief that delegates any judgment call to a builder must
explicitly list which calls it's delegating, and the builder is explicitly permitted — and
expected — to stop and ask whenever it finds part of the brief (an example, a list, an
attached document, or a test) that already seems to answer one of those listed calls,
rather than silently picking a side. The cost is one written section per brief, plus some
number of stop-and-ask exchanges going forward, some of which will turn out to be false
alarms — treated as an acceptable, cheap cost given that the actual incident this
mechanism responds to was a real, ratified defect in law-adjacent project content. The
named consumers of this mechanism are: the implementer, who gains a licensed stop instead
of a silent, unaccountable choice between obeying the delegation or obeying the
pre-resolved answer; and the orchestrator, whose own brief is now checked against its own
delegation list — the commissioner of the work is implicated by construction, which this
episode showed was warranted.

### M6 — Every data field gets a one-sentence statement of what it means, checked at the point the field is defined

**What it forecloses:** D5 above — the same field label (`External`) silently meaning
three different things in three different places, because nobody had ever written down,
in one place, what the field is actually supposed to mean.

**What is proposed:** every field in every structured data file this project's setup
wizard reads from must carry a single required sentence, written where the field itself is
defined in the software, stating what that field asserts and to whom. The refusal fires at
the point the field's own definition is written or imported, not later when some data file
using it happens to load: in the software, a field's definition is a small schema
description with a `charter` slot that has no default value, so a field definition missing
its one-sentence charter makes that schema description itself fail to construct — the
schema cannot even come into existence without it, which is stronger than merely refusing
a data file at load time. It is not optional filler, it is a required part of defining the
field at all. This sentence then
becomes the fixed reference point that a human reviewer, or a future person restructuring
this data, can check any given entry's content against, rather than each person inventing
their own private, unstated understanding of what the field means (which is exactly how D5
happened — each section was internally consistent with its own private, never-written-down
idea of what "External" meant).

In scope, as with M1 and M3, are all fields of `feature_facts` and its sibling data-split
files `durable_decisions` and `principals_authority`, plus any future corpus read by the
same family of data loaders.

The consult is explicit that this does not by itself guarantee every entry actually matches
its field's stated meaning — that remains a matter for human review, now made easier
because there's finally something concrete to check against, rather than something to
invent from scratch each time.

As with the other mechanisms, no numeric threshold exists anywhere in this one; that
absence is deliberate and declared, not an oversight — the check is vacuous, named as such
rather than faked with an invented bound.

**Adopting this means:** whoever defines a data field in this project's setup-wizard data
files must write one plain sentence stating what that field means and who it's for, and the
field's own schema definition will refuse to come into existence at all if that sentence is
missing. This is a small, one-time cost per field, paid when the field is first created,
not on every use of it afterward. The consult flags one plausible failure mode of its own
proposal, stated plainly rather than left implicit: a charter can be written as filler —
a sentence that satisfies the requirement without actually saying anything useful — and the
only thing likely to catch that is the same cold-reading witness that later has to consume
the charter. An unused, filler charter is, in the consult's own framing, precisely the kind
of never-enforced entry that a "things nobody ever checks against get culled" condition
should remove. The named consumers of this mechanism are: the executor
of the cold-reading witness requirement, who gains a stated contract to check content
against instead of having to infer one; and the implementer of the next migration, who
gains the same contract this episode's implementer had to invent, alone, per field.

---

## A note on the roll-up table in the phase-3 document

The phase-3 document ends with a short table summarizing, for each of the six mechanisms
above, which enforcement point is strongest and which part is honestly left to human
review — and a closing note about how to cull, if the maintainer chooses to drop or scale
back any of the six: cull from the bottom of each mechanism's *own* cost column, never by
removing a whole mechanism from the table. The note specifically flags M4's tagging
requirement and M6's one-sentence field charter as the two to keep rather than cut — they
are the cheapest items in the whole set, and the other mechanisms' own honestly-declared
review ceilings depend on them staying in place. That table and recommendation
are not reproduced here in full, since it is a comparison across all six mechanisms at
once rather than a self-contained claim any single section needs — a reader who wants the
exact table can find it at the end of `design/CONSULT-FABLE-ELUCIDATION-RCA-2026-07-22-
PHASE3.md`.

One part of that table is worth stating here directly, because it is a timing commitment
rather than a comparison: per ADR-0011's 2026-07-02 amendment, at this project's bar
mechanisms M1 through M3 ship together with the corrective fix to the current corpus, not
deferred until a second occurrence of the same defect — the first fix's definition of
"done" includes its own net.
