# USER GUIDE — from a project and a Postgres box to a working, audited record

This page is written for an adopter — someone with a project of their own and a Postgres
database they can reach, who wants to know how autoharn fits in. It is the front door: not for someone already
running it, and not for someone maintaining autoharn itself (see [§7](#7-where-everything-else-lives)
for where those readers go instead). autoharn's other user-facing pages each answer one
question well but assume you already know which one to read first; this page's only job is to
put them in the order a new reader actually needs: install, adopt, operate, audit. Read it once
top to bottom, then keep it as a map back to the page that answers whatever you hit next.

## 1. What autoharn gives your project

autoharn gives your project an append-only record of what was decided, who decided it, and
when — this guide calls it "the record," and the pages it links to call the same thing "the
ledger"; the two words name one artifact — plus a set of small tools that read and write that
record so nobody has to trust memory, a chat transcript, or a hand-edited file. Every entry is
attributed to whoever actually wrote it
(never a self-declared name), nothing already written can be silently edited or deleted, and a
handful of guardrails refuse an action that would break that guarantee — but refuse *with an
explanation*, not a bare error, so the refusal itself tells you what to do next (the
"refuse-and-teach" idea [§6](#6-when-something-refuses) covers in full). Day to day, you touch
this through a small number of commands — this guide calls them **verbs** because each one does
one clear thing, [§4](#4-operate-the-seven-verbs) names all seven.

## 2. Before you start

You need two things before any of the commands below will work: a Postgres database and a
database role that can connect to it, and a stable place for the autoharn checkout itself to
live.

**The Postgres side.** If you don't already have a database and role set up, read
[USER-CONFIGURATION.md's "FAQ: provisioning Postgres for
autoharn"](USER-CONFIGURATION.md#faq-provisioning-postgres-for-autoharn) — it is a copy-paste
walkthrough (create a role, create a database, grant it what the tooling needs, confirm you can
reach it) with what you should see at each step. If your Postgres cluster's superuser accepts
connections with no password at all, that same page's [pg_hba
FAQ](USER-CONFIGURATION.md#faq-the-pg_hba-network-rule-you-may-want-to-add) is worth a read
before you go further, though closing that hole is your own act on your own schedule, not
something any command below does for you.

**Where autoharn lives, and why that matters.** You do not copy autoharn's code into your
project. You clone or check out autoharn once, and every project you scaffold from it keeps
running that same checkout's files, live, forever — a fix in autoharn reaches every project
scaffolded from it on its very next command, with nothing to re-install. The cost of that design
is real and stated plainly in [USER-CONFIGURATION.md's install-path
contract](USER-CONFIGURATION.md#the-install-path-contract--read-this-before-you-move-anything):
if you move, rename, or delete the autoharn checkout after scaffolding a project from it, that
project's commands quietly stop resolving. **Pick a path for your autoharn checkout and keep
it** for as long as any project scaffolded from it is in use; that same page also explains the
one-command fix if you ever have no choice but to move it.

## 3. Adopt: three commands, three different commitments

autoharn does not have one "install" step — it has three separate scaffolds, because "track
what I'm working on," "run a fully governed session," and "record an experiment reading" are
different commitments with different weight. Pick the one that matches what you actually need
today; you can add the others later, and none of them requires the others first. Every command
below was run for real against a throwaway target and torn down with zero residue while this
page was written — confirmed live, not a transcript reused from elsewhere. Condensed output is
shown below; the full transcripts live in the pages each section links to.

### 3a. Just track your work: `bootstrap/track-work.sh`

The lightest of the three is a standing, Postgres-backed replacement for a hand-edited TODO file.
It needs no hooks and no session governance, and it works in any directory — it doesn't need to
be a git repository or a Claude Code project at all.

```sh
cd /path/to/your/autoharn-checkout
bootstrap/track-work.sh /path/to/your-project --name yourproject --db <db> --host <host>
```

**What you should see** (condensed from a real run against a throwaway schema): a block of
`CREATE SCHEMA`/`CREATE TABLE`/`GRANT` lines from the database apply, then

```
   'reviewer' + 'commissioner' principals registered ('author' was already seeded by s15-schema.sql)
-- deployment.json --
wrote /path/to/your-project/deployment.json
wrote led (shim -> .../bootstrap/templates/led.tmpl)
wrote judge (shim -> .../bootstrap/templates/judge.tmpl)
wrote pickup (shim -> .../bootstrap/templates/pickup.tmpl)
wrote audit (shim -> .../bootstrap/templates/audit.tmpl)
wrote distance-to-clean (shim -> .../bootstrap/templates/distance-to-clean.tmpl)
wrote verify-commission (shim -> .../bootstrap/templates/verify-commission.tmpl)
wrote verify-chain (shim -> .../bootstrap/templates/verify-chain.tmpl)
wrote attest-doc (shim -> .../bootstrap/templates/attest-doc.tmpl)
wrote asof-export (shim -> .../bootstrap/templates/asof-export.tmpl)
-- ./legacy/ (pickup/asof-export/distance-to-clean's direct-psql originals, demoted by
   placement, spec §5; THIS deployment has no boundary service of its own, so these three are
   the working verbs) --
wrote legacy/led (RETIRED teaching-refusal stub -- see FLAGGED GAP note below)
wrote legacy/pickup (shim -> .../bootstrap/templates/legacy-pickup.tmpl)
wrote legacy/asof-export (shim -> .../bootstrap/templates/legacy-asof-export.tmpl)
wrote legacy/distance-to-clean (shim -> .../bootstrap/templates/legacy-distance-to-clean.tmpl)
== done ==
```

**FLAGGED GAP (legacy-led-retirement, design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md, ledger row
1149/1150) — `led` specifically has no working path for a `track-work.sh` deployment right
now.** `bootstrap/templates/legacy-led.tmpl` is deleted outright as part of that retirement;
`./legacy/led` is now a one-line teaching refusal, never a working CLI, and `./led` (the served
shim) refuses too — this deployment shape deliberately writes no `boundary_url`/
`boundary_deployment` ("a standing work tracker runs no boundary service by design," this
script's own header). This is a genuine, unresolved gap the retirement found in reach and
named rather than silently shipped or unilaterally patched (giving `track-work.sh` its own
standing boundary service is a real architecture question outside that pass's own mandate).
`judge`/`pickup`/`audit`/`distance-to-clean`/the signing verbs are unaffected. Until a
maintainer decision resolves this, treat a `track-work.sh` deployment's own ledger as
read/write via `./pickup` and direct `psql`, not `./led`.

**What landed where:** `deployment.json` (which database/schema this project points at) and nine
small command files (`led`, `judge`, `pickup`, `audit`, `distance-to-clean`, `verify-commission`,
`verify-chain`, `attest-doc`, `asof-export`) in your project directory — nothing written back
into the autoharn checkout.

**UPDATED 2026-07-18 — `./led`/`./pickup`/`./asof-export`/`./distance-to-clean` now talk HTTP to
a boundary service by default** — a "boundary service" is `serving/boundary_service.py`, a
FastAPI server this repository ships that translates HTTP calls into the same reads and writes
against the Postgres database (this guide's "record"/"ledger," §1 above) these verbs always made,
so a project's ledger can be reached from more than one process without each one shelling out to
`psql` directly
([design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md](../design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md)
§5, ratified row 1631; the full recipe is in
[USER-RECIPES-FAQ.md's boundary-multiplex section](USER-RECIPES-FAQ.md#boundary-multiplex-cli-rebase-and-the-workflow-unit-compiler-2026-07-18),
linked again below). **This scaffold runs no boundary service of its own** — a standing work
tracker is a perpetual, hookless store for a project's whole lifetime, never a run-scoped,
hook-wired session (`bootstrap/track-work.sh`'s own header comment states this contrast under the
heading "STANDING vs WORLD" — see that file directly for the full text). WITNESSED live: those
four shims refuse with exit 4 out of the box
(`led: deployment record at .../deployment.json is missing required-for-the-served-shim
field(s): boundary_url, boundary_deployment ...`). The scaffold writes `./legacy/pickup`/
`./legacy/asof-export`/`./legacy/distance-to-clean` for exactly this reason — the direct-`psql`
originals, demoted by placement, not deleted — so "try it immediately" below uses those.
**`led` is the ONE exception, and a currently-open gap** (legacy-led-retirement,
design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md, ledger row 1149/1150): its own direct-psql
original, `legacy-led.tmpl`, is deleted outright, and `./legacy/led` is now a one-line teaching
refusal — a `track-work.sh` deployment has no working `led` verb at all right now (see §3a's own
FLAGGED GAP note above). Use `./pickup` to read, and a direct `psql` session against this
deployment's own schema (named in its `deployment.json`) to write, until a maintainer decision
resolves this:

```sh
cd /path/to/your-project
./pickup
```

`./pickup` prints your open work back to you — confirmed live during this page's own
verification pass, back when `./legacy/led work open` was still the working write path (now
retired; the read side, `./pickup`, is unaffected). (If you later stand up a boundary service for
this deployment and add its
`boundary_url`/`boundary_deployment` to `deployment.json` by hand, the un-prefixed `./led`/
`./pickup` start working too — see
[USER-RECIPES-FAQ.md's boundary-multiplex section](USER-RECIPES-FAQ.md#boundary-multiplex-cli-rebase-and-the-workflow-unit-compiler-2026-07-18)
for what those two keys are and the exit-code split the served shims use.) For the full detail —
the exact command shape, and how this option differs from §3b's below — read
[design/USER-WORK-STATUS-OFFERING.md](USER-WORK-STATUS-OFFERING.md)
and [USER-CONFIGURATION.md's own
section](USER-CONFIGURATION.md#bootstraptrack-worksh--a-standing-work-tracker-not-a-governed-world).

### 3b. Run a governed Claude Code session: `bootstrap/new-project.sh --new-world`

The full commitment is a habitat for one governed AI-collaborator session: every file edit is
checked against the ledger, and every write is attributed and tamper-evident. Use this when you want an AI
collaborator to do real work under the same discipline autoharn holds itself to.

```sh
cd /path/to/your/autoharn-checkout
bootstrap/new-project.sh /path/to/your-project --new-world yourworld --db <db> --host <host>
cd /path/to/your-project && claude
```

**What you should see** (condensed; confirmed live against a throwaway [world](../GLOSSARY.md#world) —
this guide's word for one scaffolded project instance): the same kind of
database-apply block as above, then a fresh secret provisioned for attributing writes ([§5
below](#5-audit-and-trust) explains what this "stamp" secret proves), the standard identities
registered, and

```
-- .claude/ wiring --
wrote .claude/settings.json, governed_files.json, GOVERNED_FILES.md, apparatus.json, APPARATUS.md, HOOKS.md
wrote CLAUDE.md (governance preamble, auto-loaded at session start)
-- the three verbs (led, judge, pickup) --
wrote led (executable)
wrote judge (executable)
wrote pickup (executable)
== done ==
```

Running `./judge` right after scaffolding printed `AGREE` in this page's own verification pass —
two independent ways the harness (autoharn's own tooling; this page uses the two names
interchangeably from here on) computes "what is currently true" (a rule engine and a plain SQL
query) agreeing on a brand-new, still-empty project. That is the expected result for a fresh
[world](../GLOSSARY.md#world); [§4](#4-operate-the-seven-verbs) explains what `./judge` checks and
what a disagreement would mean.

**What landed where:** everything §3a describes above, plus `.claude/settings.json` (wires the
hooks that check every edit), a stamp secret, and a `CLAUDE.md` at your project's root that
Claude Code loads automatically at session start — nothing to paste into your first message.
Unlike §3a, this scaffold accepts `--boundary-url`/`--boundary-deployment` flags to point the new
world at an already-running boundary service; omit them and `./led`/`./pickup` refuse with the
same exit-4 message §3a's own boundary-multiplex note shows. **Pass `--boundary-url`/
`--boundary-deployment` (or use the setup wizard, `python3 -m tools.setup_tui.app`, which stands
one up for you) rather than omitting them** (legacy-led-retirement, design/FABLE-LEGACY-LED-
RETIREMENT-SPEC.md, ledger row 1149/1150): the boundary is now MANDATORY for a governed world --
`./legacy/led` no longer exists as a working fallback (a one-line teaching-refusal stub, since
`legacy-led.tmpl` is deleted outright); `./legacy/pickup`/`./legacy/asof-export`/
`./legacy/distance-to-clean` remain real, working shims regardless. The full "what state lands
where" table, every file this writes and
whether you commit it, is [USER-CONFIGURATION.md's own reference
table](USER-CONFIGURATION.md#what-state-lands-where); a slower, narrated walkthrough of the same
scaffold (including how to tear a throwaway one down) is
[USER-WALKTHROUGH.md](USER-WALKTHROUGH.md).

### 3c. Record an experiment reading: `bootstrap/track-experiments.sh`

The narrowest of the three: wires your project to a shared measurement ledger — a separate,
cross-project store, not the per-project record/ledger §1 above defines — that keeps a raw
reading (a benchmark number, a timing) structurally separate from anyone's interpretation of it,
so "a reading of the data recorded as the data" cannot happen by accident.

```sh
cd /path/to/your/autoharn-checkout
bootstrap/track-experiments.sh /path/to/your-project --name yourproject --db <db> --host <host>
```

**What you should see** (confirmed live): `research-ledger.json` and one command file,
`record-reading`, written into your project directory, and — honestly, because this was the real
result on the box this guide was verified against — a note that the shared database tables this
points at have not been created yet on that particular host, so the first `record-reading` call
will fail loudly until the tables exist. That step (`bootstrap/apply-research-ledger.sh`) is
**exclusively a maintainer act, on the one shared database it targets** — this scaffold never
runs it and never offers to; your very first `record-reading` call is the honest way to find out
whether it has already been done for the database you're pointed at.

**What landed where:** two files in your project directory, no database schema changes.
`bootstrap/track-experiments.sh`'s own header comment carries the full usage contract and the
exact `record-reading` command shape. For the full scope — what is deliberately not included,
such as study-design tooling or an analysis layer — read
[design/USER-WORK-STATUS-OFFERING.md](USER-WORK-STATUS-OFFERING.md), which describes this
offering's sibling (the work tracker from §3a) for contrast.

## 4. Operate: the seven verbs

Once a project is scaffolded (either §3a or §3b), you interact with it through seven small
commands. Six of them (`led`, `judge`, `pickup`, `audit`, `distance-to-clean`, `attest-doc`) run
from inside your project directory, once it exists; the seventh — the scaffold itself — runs once,
before the project exists, from the autoharn checkout. This section is a paragraph-each index — the
authoritative detail, including exact output and what each verdict means, is
[ORCH-OPERATING-CARD.md](ORCH-OPERATING-CARD.md), written for whoever is actually running a
session; read it once you're past this page.

**`./led`** writes one entry to the record — a decision, a finding, an assumption, a piece of
work opened or claimed or closed — and reads entries back. Every entry is attributed to whoever
actually connected and wrote it, never to a name you type. `./led work open <slug> "<title>"`
opens a task; `./led --recent` shows the latest entries. This is the one verb you'll type by hand
most often.

**`./judge`** checks the record for internal consistency, two independent ways at once — a rule
engine and a plain SQL query both compute "what is currently true," and `./judge` reports whether
they agree. A clean project reports `AGREE`; anything else is a signal to stop and look, not
something to work around.

**`./pickup`** prints a live summary of where things stand — open work, unanswered questions,
outstanding reviews, recent changes — recomputed from the record every time it runs, never from a
stored file that could go stale. It is the right first command in any project you're returning to,
including one someone else worked on.

**`./audit`** checks *when* things happened against *when they were recorded* — did an entry get
written at the time of the event it describes, or added later. This is a read-only check; run it
any time, mid-project or after.

**`./distance-to-clean`** is one composed report of everything still outstanding — open
questions, pending reviews, unclaimed work — across the record, in one command instead of several.

**`./attest-doc`** is a separate, optional verb for a separate discipline: recording that a
markdown document in your project was reviewed by a fresh, unbiased AI reader before you called
it done (the "A:B:C fresh-context audit loop" this project runs on its own documentation).
`./attest-doc check` reports which of your documents are attested, stale, or never reviewed;
`./attest-doc record` files a new review. It costs nothing to run and nothing blocks on it —
[design/USER-DOC-AUDIT-LOOP.md](USER-DOC-AUDIT-LOOP.md) is the full "what you type, what
you should see" walkthrough, including how to fold its debt into `./distance-to-clean` once you
start using it.

**The scaffold** (`bootstrap/new-project.sh`, `bootstrap/track-work.sh`,
`bootstrap/track-experiments.sh` — §3 above) is the seventh verb: the one you run once per project,
from the autoharn checkout, to stand the other six up.

**Putting the task itself on the record.** If you want the very first thing your project's record
shows to be the task you gave it — rather than an AI collaborator's own paraphrase of your chat
message — [ORCH-OPERATING-CARD.md's "Start a run / resume a run"
section](ORCH-OPERATING-CARD.md#start-a-run--resume-a-run)
walks the **commission start**: you write the ask to a file and put it on the record yourself,
from your own terminal, before any session begins. Adding a cryptographic signature over that
same ask — turning it into what this project calls a **signed commission**, so the record can
later prove a human, not just a piece of software, actually made the request — is a further,
optional step; [design/USER-GPG-TRUST-LAYER-FAQ.md
§5](USER-GPG-TRUST-LAYER-FAQ.md#5-ceremony-2--signed-commissions) is the copy-paste
ceremony for it, and [§5 below](#5-audit-and-trust) says more about what signing buys you.

**Turning mechanisms on or off.** Everything a scaffolded project checks automatically — from
refusing an unattributed file edit to a costed check that reads your documentation for clarity —
is controlled by one file, `.claude/apparatus.json`, per project. It ships with the checks that
cost nothing turned on and the two checks that spend real money per use turned off:

<!-- doc-attest-exempt: 2026-07-19 typed-table-ssot-integration commission — the only change
     at this content hash is wrapping the pre-existing "kind of mechanism" table in typed-table:BEGIN/
     END anchors and regenerating it through tools/doc_table_generation.py, whose call site
     lives in tools/doc_table_registry.py. Every cell's text is unchanged; the only byte-level
     difference is the delimiter row reformatted from the old "|---|---|---|" to the canonical
     "| --- | --- | --- |" tools/markdown_tables.render_separator produces — content-preserving
     in exactly the sense gates/doc_tables.py's own separator-fix precedent already treats as
     such (a delimiter row carries no content), plus the two new anchor comments and one
     provenance comment, none of which is prose a reader parses for meaning. No prose changed,
     so ADR-0017's fresh-context legibility concern does not apply to this touch; no live A:B:C
     loop was run (this session cannot fork a genuinely fresh reviewer) and this marker does not
     claim one did. SCOPED, not a standing exemption on the whole file (narrower than
     ADR-0012.md's own precedent for this exact class of touch, which that file's own marker
     flagged as worth tightening) — mechanically this token exempts the whole file for as long
     as it stays present, same known gap ADR-0012.md's marker names; the next PROSE edit to this
     file should get a real attestation and this marker removed, not carried forward as cover. -->

<!-- typed-table:BEGIN id=user-guide-mechanism-kinds -->
| kind of mechanism | default | example |
| --- | --- | --- |
| free (no external call) | on | refusing an edit with no ledger entry behind it |
| costed (one billed call per use) | off, and says so next to the switch | reading a document for legibility with an LLM |
<!-- constructor-generated: tools/experiments/typed_table.py; declared type former = 'kind of mechanism'; 2 row(s) type-checked at construction (forced articulation + empty-header refusal + column-count coherence); see vestigial_documentation/design/ORCH-TYPED-TABLE-EXPERIMENT.md -->
<!-- typed-table:END id=user-guide-mechanism-kinds -->

The full reference — every mechanism this project ships, what it does, and exactly how to flip
it — is [USER-CONFIGURATION.md's apparatus.json
section](USER-CONFIGURATION.md#the-apparatusjson-mechanism-switchboard); read it before turning
anything on that isn't on by default.

## 5. Audit and trust

What can the record actually prove to someone who was not in the room? Four things, each with
its own mechanism:

- **Attribution** — every entry is tied to the actual database connection that wrote it, a
  cryptographic checksum keyed by a secret only the writer holds, which the harness calls a
  [stamp](../GLOSSARY.md#stamp), not a name the writer typed in. You can see
  this yourself: an entry written from a governed session carries a stamp; one written from a
  bare shell does not, and that absence is visible, never hidden.
- **Immutability** — nothing already written can be edited or deleted; a change of mind is
  recorded as a new entry that supersedes the old one, and the old one stays exactly as it was.
  [USER-WALKTHROUGH.md's "File a decision, read it back"](USER-WALKTHROUGH.md#2-file-a-decision-read-it-back)
  shows this live, including the refusal you get if you try to `UPDATE` or `DELETE` a row.
- **Contemporaneity** — the [`./audit`](#4-operate-the-seven-verbs) verb checks every entry for
  whether it was recorded at the time of the event it describes, or added after the fact, and
  reports the honest answer rather than assuming good faith.
- **The signing layer is** an optional further step where a real person, using a key outside the
  database entirely, vouches for a specific ask or a specific state of the record with a
  cryptographic signature. This proves something the database-level guarantees above cannot: not
  just "this entry wasn't altered," but "a human, not merely a piece of software with database
  access, stood behind this." [design/USER-GPG-TRUST-LAYER-FAQ.md](USER-GPG-TRUST-LAYER-FAQ.md)
  is the full step-by-step for generating a key, signing, and verifying — including what this
  layer does **not** protect against, stated plainly in its own closing section.

**Money and token figures are not one of the four things above, and never will be.** Draw the
line precisely: a raw, hook-witnessed **event count** (N subagent spawns really happened,
witnessed by the harness) is evidentiary. Anything **derived** from that count — a
subagent-spend estimate, or a dollar figure autoharn shows you anywhere — is a different kind
of figure and is **diagnostic-grade, not evidentiary**: useful for noticing a session that looks
obviously runaway, never sound enough to bill against, reconcile as an expense, or trust the way
you trust attribution, immutability, contemporaneity, or a signature above. This is a standing
maintainer ruling (2026-07-11), restated as a permanent design boundary in
[design/ORCH-SPEC-RESOURCE-ACCOUNTING.md
§6](../design/ORCH-SPEC-RESOURCE-ACCOUNTING.md#6-the-financial-audit-grade-boundary): turning a
witnessed count into a dollar figure is a pricing step outside the harness, and that step
inherits none of the harness's own guarantees. If you need a number you can bill against, price
the witnessed counts yourself, outside autoharn, against your own known rate — do not treat any
total the harness prints as an accounting artifact.

## 6. When something refuses

Most of what autoharn adds to a governed project is not a feature you invoke — it is a set of
checks that get in your way on purpose when something is about to happen without a record behind
it. The design principle is **refuse-and-teach**: a refusal is never a bare error. It names what
was missing and what to do about it, so the refusal message itself is the instruction, not a
puzzle to go read documentation for. Three refusals you are likely to meet early:

- **"No ledger entry for this edit."** A governed project (§3b) refuses to let you edit a file
  it's watching until there is a record explaining why — write the `./led decision` or
  `./led finding` entry first, then make the edit.
- **"No open, claimed work item."** Similarly, a governed project wants an open-and-claimed task
  behind any edit, not just a record of intent — `./led work open <slug> "<title>"` then
  `./led work claim <slug>` before touching files.
- **`NO-COMMITTED-KEY`** (only if you use the signing layer, [§5](#5-audit-and-trust)). This means
  exactly what it says — nothing has been committed yet to check a signature against — and is
  deliberately a different, calmer message than "forged": your project just hasn't had a real
  signing key committed to it yet. [design/USER-GPG-TRUST-LAYER-FAQ.md
  §3](USER-GPG-TRUST-LAYER-FAQ.md#3-committing-the-public-key--two-different-places-depending-on-what-youre-signing)
  covers committing one.

Every mechanism that can refuse something is listed, with what it checks and its default,
in [USER-CONFIGURATION.md's apparatus.json section](USER-CONFIGURATION.md#the-apparatusjson-mechanism-switchboard) —
worth a skim before your first session so a refusal is recognition, not surprise.

## 7. Where everything else lives

This repository's documents are prefixed by who they're for, so you can tell at a glance whether
a page is meant for you:

- **`USER-`** pages are for you: an adopter using autoharn in your own project. This guide is one.
- **`ORCH-`** pages are for whoever is actually running or orchestrating a session day to day
  (`ORCH-OPERATING-CARD.md`, [§4](#4-operate-the-seven-verbs) above, is the main one). They are
  useful once you're past adoption and into regular use.
- **`MAINT-`** pages are for autoharn's own maintainer: decisions about autoharn's law and
  infrastructure, not things an adopter's project needs to act on.
- **Unprefixed root files** (`CLAUDE.md`, `README.md`, `BACKLOG.md`, `FINDINGS.md`,
  `GLOSSARY.md`) stay unprefixed either because a tool looks for that exact name
  (`CLAUDE.md`, `README.md`), or because they are genuinely universal across every audience (the
  dated findings journal, the glossary this guide links into throughout).

The full taxonomy decision, including why each individual document landed where it did, is
[BACKLOG.md's dated taxonomy
entry](../BACKLOG.md#doc-audience-taxonomy--shipped-2026-07-12).

## Related

The pages this guide ordered into a journey, gathered here as one map:

- [design/USER-RECIPES-FAQ.md](USER-RECIPES-FAQ.md) — "can I do that?": an intent-keyed
  index of operator recipes, each pointing at the one page where the full truth lives; the
  quickest route from a use case in your head to the right document.
- [USER-CONFIGURATION.md](USER-CONFIGURATION.md) — every configurable surface, the install-path
  contract, and the Postgres FAQ [§2](#2-before-you-start) points at.
- [USER-WALKTHROUGH.md](USER-WALKTHROUGH.md) — a slower, narrated ten-minute walkthrough of
  standing up and tearing down a project, including a scaffold transcript confirmed live against
  a real, throwaway database.
- [design/USER-GPG-TRUST-LAYER-FAQ.md](USER-GPG-TRUST-LAYER-FAQ.md) — the signing layer's
  full ceremony, key generation through rotation.
- [design/USER-WORK-STATUS-OFFERING.md](USER-WORK-STATUS-OFFERING.md) — the work-tracking
  offering [§3a](#3a-just-track-your-work-bootstraptrack-worksh) uses, and why BACKLOG.md is a
  findings journal rather than a work tracker as of 2026-07-11.
- [ORCH-OPERATING-CARD.md](ORCH-OPERATING-CARD.md) — the operator-facing reference for the seven
  verbs, resuming a project, and how to decide whether a future fix to autoharn's own database
  schema is safe to fold into your next project automatically or needs the maintainer's
  sign-off first; read it once you're running sessions regularly.
- [GLOSSARY.md](../GLOSSARY.md) — every coined term this guide and its siblings use, defined once.
