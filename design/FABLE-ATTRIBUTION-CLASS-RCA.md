# FABLE-ATTRIBUTION-CLASS-RCA — polished living edition of the LED_ACTOR silent-misattribution RCA

**What this document is.** This is the polished living edition of a banked, verbatim
root-cause analysis (RCA): [`design/ORCH-RCA-ATTRIBUTION-CLASS-2026-07-18.md`](ORCH-RCA-ATTRIBUTION-CLASS-2026-07-18.md)
(hereafter "the source"). The source is a frozen, point-in-time record — a fresh-context
Fable investigation commissioned by the maintainer on 2026-07-17/18 under
[ADR-0018](../law/adr/0018-consults-are-not-front-loaded.md) discipline (the commission
received only the witnessed problem, its evidence, and the governing LAW — never the
orchestrating session's own candidate diagnoses). This edition exists to make that record
readable by someone with none of the authoring session's context, per
[ADR-0017 (the zero-context reader)](../law/adr/0017-the-zero-context-reader.md). **Where
this edition and the source ever appear to diverge, the source governs** — this document
adds no claim, opinion, or recommendation the source does not already make; it only
unpacks compressed language, glosses referents, and grounds structures. Substantive
divergence from the source is a defect in this edition, not a correction to it.

**Who this is for.** Anyone who needs to understand the LED_ACTOR silent-misattribution
defect class — what went wrong, why it kept going wrong, why nothing caught it sooner, and
what a fix would need to look like — without having sat in the session that investigated
it. That includes a future maintainer, a fresh AI collaborator picking up the work, or an
outside auditor.

**What question it answers.** Why did autoharn's ledger tool (`led`) repeatedly write
ledger rows attributed to the wrong principal (identity) — silently, with no error or
warning — even after the problem had apparently been fixed once already? And what would a
durable fix, and a durable guard against recurrence, need to contain?

**Status.** This is analysis and remediation *direction* only. Per the commission's own
terms, **nothing described in Part 2 below is implemented** by virtue of being banked here.
It awaits a maintainer ratification decision before any of it is built. Part 1 (the RCA
itself) describes defects and events that already happened and are already true of the
codebase; Part 2 (the remediation direction) describes what has *not yet* been built.

---

## Background you need before Part 1

A few pieces of standing vocabulary the source assumes. Skip ahead if you already have
them; each also gets a shorter inline gloss at first use below.

- **The ledger, `led`, and actors.** autoharn keeps an append-only Postgres record of
  decisions and work called "the ledger." Every row is written by an *actor* — a
  registered identity (`kernel.principal_role`) such as `author`, a named reviewer, or an
  automated process. The command-line tool that writes to it is `led` (source lives in
  [`bootstrap/templates/led.tmpl`](../bootstrap/templates/led.tmpl), which is expanded into
  each project's own `./led` executable). Correct attribution — knowing truthfully *who*
  wrote a row — is load-bearing: the kernel's whole design (signed "stamps," countersigns
  by a second reviewer, "review_gap" debt tracking) depends on rows carrying the right
  actor.
- **`LED_ACTOR`.** An environment variable an operator can set before running `led` to
  declare, explicitly, which registered principal a write should be attributed to (for
  example, when one human operates several named identities, or a dedicated reviewing
  principal opens work). It is meant to override the tool's default guess.
- **Kernel lineage and "s-numbers."** autoharn's Postgres schema is built as a sequence of
  additive migration steps called "lineage deltas," each named `sNN-description.sql` under
  `kernel/lineage/` (e.g. `s15-schema.sql`, `s29-obligation-item-key-and-typed-close.sql`).
  A delta is never edited in place once landed; a later fix is always a *new*, higher-
  numbered delta. "s15," "s29," etc. below are these files, referenced by number the way
  the source does.
- **The panel deployment.** A separate, downstream installation of this same harness, run
  as this project's own simulated downstream test-bed, at
  `~/w/vdc/1/experience/autoharn-panel`. It is cited
  here because it is the environment that first surfaced this defect class in live use (see
  §1.4 below) — it deliberately does *not* let its default "author" identity sign
  completions, which is exactly the condition needed to make a silent misattribution
  visible.
- **The kernel's law and its shorthand.** The source cites clauses from autoharn's
  Architecture Decision Records (ADRs, under `law/adr/`) by shorthand. Each is glossed at
  its first use below rather than up front; a full reading is at
  [law/adr/](../law/adr/) and [GLOSSARY.md](../GLOSSARY.md).

---

## 1. The root-cause analysis (source §1)

### 1.1 What the defect class is, mechanically (source §1.1)

At the database level, whenever a ledger row is inserted without an explicit actor, the
kernel fills one in automatically. The relevant trigger code, quoted verbatim from the
source (file `kernel/lineage/s15-schema.sql`, lines 136-145; the same pattern also exists
in an earlier delta, s13):

```sql
IF NEW.actor IS NULL THEN
  SELECT principal_id INTO NEW.actor FROM kernel.principal_role WHERE db_role = current_user;
END IF;
```

In plain words: if a row arrives with no actor set, the trigger looks up whichever
database role the current connection is using and silently substitutes that role's
registered principal as the actor. No error, no warning — the row is written as if that
had been the intended actor all along.

On the command-line side, an operator's intent to attribute a write to a *specific*
principal travels through the `LED_ACTOR` environment variable described above. But — and
this is the crux of the defect — **each individual write code path inside `led.tmpl` has
to separately opt in** to reading that variable: it must call a helper function
(`resolve_actor()`) and thread the result into its own INSERT statement via a
`NULLIF(:'actor_name','')` SQL bind. A write path that does nothing extra — one whose
INSERT statement simply omits the `actor` column — produces a NULL, and the kernel's
silent-fill trigger quoted above fires instead.

The source states the consequence plainly: **"the defect path is the zero-effort path" —
every newly written `led` write site starts out misattributing, and only extra work by
whoever writes that path makes it honest.**

Worse, a single database value — NULL — was made to mean at least four different things,
per the source:

1. The operator never set `LED_ACTOR` at all (intent never set).
2. The operator set `LED_ACTOR` to an empty string (intent set to empty).
3. The operator set `LED_ACTOR`, but the specific `led` write path they used never reads it
   (intent set, but dropped by the tool — an "unwired" path).
4. The operator set `LED_ACTOR` to a name that isn't registered as a principal — the
   lookup query matches no row and itself returns NULL. The source notes this is a second,
   latent version of the same defect, and quotes a fix commit (`05bc000`) that itself names
   the failure mode: such a write is "silently attributed to author, indistinguishable from
   unset."

The source calls this a **category collapse** — four genuinely different situations
folded into one indistinguishable signal (NULL) — and identifies it as "exactly ADR-0000
Specimen 2's kind" of error. *Gloss:* Specimen 2 is a named case study in
[ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md) (autoharn's
foundational type-driven-design tenet) about a bug where three genuinely distinct
quantities were compared as if they were one currency, producing a systematic
misclassification. The source is asserting the LED_ACTOR defect is the same shape of
error: incommensurable meanings merged into one representation. And because the meanings
were indistinguishable at the data level, **every instance of this defect was silent by
construction** — the kernel had no way to refuse a write it could not tell was wrong.

### 1.2 Why the defect class arose — a design/idiom problem, not a blame question (source §1.2)

The source is explicit that this section is diagnosing *how two individually reasonable
design decisions combined to create a hazard*, not assigning fault to a person.

**Decision 1 (kernel side): a default that looks fail-safe but is actually fail-*quiet*.**
Falling back to "whoever is connected" as the actor is genuinely the right behavior in a
"solo world" — a deployment with exactly one principal (`author`) who legitimately writes
everything. But the source notes that this default is licensed by
[ADR-0002](../law/adr/0002-fail-loudly.md) ("fail loudly" — autoharn's tenet that failures
should surface immediately and visibly rather than being silently absorbed, and its
graded "hierarchy of loudness" of exactly which behaviors are allowed to default quietly
and which must raise) — imported into the compositional-hygiene tenet
[ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md) as principle **P5**
("fail loud; remove the root cause") — and that hierarchy permits a silent default *only
when the default genuinely equals the intended value*. The trigger has no way to verify
that equivalence, because the channel carrying the operator's actual intent (`LED_ACTOR`)
terminates in the command-line tool and reaches the kernel only as a column value that may
or may not be present.

**Decision 2 (CLI side): intent is transported per call site, not per session.** The
`led.tmpl` source issues each ledger write as its own separate `psql` (Postgres
command-line client) invocation, each with its own hand-copied preamble setting up the
database role. The source counts **35 separate `SET ROLE` preambles** and, per a
independent enumeration in commit `9e33dc7`, **15 `INSERT INTO ledger` sites spread across
7 dispatch points** (7 distinct `led` subcommands/verbs, each with its own code path). Any
fact that should be scoped to the whole session — which role is connected, the SQL search
path, and (had it been designed this way) the operator's declared actor intent — instead
has 35 separate places where it gets set up. The source names this
**"ADR-0012 cancer B (SSOT dissolved; the same knowledge re-encoded in N places) at the
transport layer."** *Gloss:* ADR-0012 catalogs recurring defect shapes ("cancers") this
project has learned to recognize; "cancer B" is specifically the pattern where one fact
that should have a single source of truth (SSOT) is instead hand-copied into many places,
which lets copies drift apart. Here, the copying is what makes "a write path that ignores
operator intent" not just possible but the **default state of every newly written write
path** — there is no single place a new path could be plugged into that would make it
correct automatically.

**The tell that this is an idiom problem, not an accident.** The source points out that
the *same file* solved the analogous problem correctly for a different piece of intent:
the `--event-time` command-line flag. That flag is supported only by one generic write
path, and *every other* `led` verb **refuses it loudly** rather than silently ignoring it
— the file's own comment reads "never a silent drop; see the coverage guard" (around
`led.tmpl` line 60-64, with the actual guard code around lines 600-626). The source
diagnoses the structural difference: a command-line *flag* must pass through the dispatch
parser that routes each subcommand, so an unsupported flag forces that parser to make an
explicit decision about it (refuse, or don't). An *environment variable* like `LED_ACTOR`
requires no parsing at all — nothing forces any code path to look at it, so a path that
never reads it simply ignores it silently, by construction. The source's framing: LED_ACTOR
was "an intent channel with no forced read" — which it calls, at file scale, the same
"lying-signature disease" ADR-0012 catalogs as principle **P8** (typed signatures should be
the single source of truth of a contract, honored by the body — here, the tool's
documented behavior of "LED_ACTOR is honored" was a contract that no code mechanism
actually obliged any given write path to keep).

### 1.3 Why it recurred after being fixed once — the run-7/8 episode (source §1.3)

("Run-7/8" names two of this project's earlier numbered operational runs — under the
runs-are-linear doctrine, each run is a numbered world. Run-7's episode is recorded in
`bootstrap/templates/led.tmpl`'s own BACKLOG comments; run-8 appears in commit `05bc000`'s
own title.)

The source identifies an earlier fix attempt, commit `05bc000` (dated 2026-07-11), as a
**textbook specimen of a named, dated failure pattern**: naming a defect class narrowly
enough to match exactly the fix already built, rather than at its true general scope. This
pattern is documented as the **2026-07-02 amendment to ADR-0000 Rule 2(a)**
([ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)): Rule 2(a)
requires that, when a defect class is closed, the fix state a **closure statement** — an
explicit invariant, plus an explicitly *enumerated* "quantification universe" (every axis
and every sibling surface the defect could occur on) — precisely because, across a prior
study cited in that amendment, executors kept naming a class at exactly the scope of the
fix they had already written, leaving siblings open.

Commit `05bc000`'s own commit message claimed LED_ACTOR was now "honored on **every write
path** via ONE resolver" and that, per ADR-0000, the fix "**forecloses the class**." It
actually wired three write paths (`review`, `work claim`, and the `generic` path). But at
the moment that commit landed, the file *already contained* a fourth surface — `led work
open/depends/close` — added earlier in commit `a73638d`, which precedes `05bc000` in
history. The source's finding: **the "every" claim was never checked against an actual
enumerated list of write sites** — no per-INSERT census was taken, no closure statement was
written — so "every" was, in the source's words, "an umbrella claim with no witness,"
which it identifies as forbidden both by this project's standing rule that
**"claims carry witnesses"** (stated in [CLAUDE.md](../CLAUDE.md)) and by a 2026-07-02
amendment to [ADR-0013](../law/adr/0013-execution-integrity.md) requiring that a
completion claim have a specific evidentiary shape. The self-correcting presumption that
Rule 2(a)'s amendment establishes — *a newly named class should be presumed too narrow
until proven otherwise* — was not applied here.

Once that presumption failed to fire, the source describes what it calls "the recurrence
engine": new INSERT branches for ledger writes kept being added over time (an `s29`/`s38`
close constructor, `s30` "depends" branches, a "resolve-violation" path) with nothing
obliging any of them to bind an actor. This is, per the source, exactly the failure mode
named in **ADR-0011 Rule 4** ("enumeration fails open at the next instance") — and here it
is worse, because the enumeration required by Rule 4 was never even written down for
anyone to fail open against.

Meanwhile, the situation was actively made to look *more* closed than it was: a code
comment describing LED_ACTOR coverage, after a later commit `8c4bb3b`, came to read that
the resolver covered "for **EVERY** ledger-writing verb — … alike (ONE resolution point …
shared by all **four**)." The source flags this as self-contradictory on its face — it
says "EVERY" and then enumerates exactly four, in a file that (per the `9e33dc7`
enumeration) has seven dispatch points — and notes this overclaiming comment stood
uncorrected until a later reviewer forced it to be made honest in commit `6561e8a`. The
source's diagnosis of why this matters beyond the specific miscount: **"A comment claiming
coverage it lacks is a describing record that actively launders the gap"** — every later
reader, and every later fix built on top of it, inherits the false belief that this problem
is already closed.

Finally, the source notes that a separate 2026-07-02 amendment to
[ADR-0011](../law/adr/0011-mechanization-discipline.md) — the rule that, at a
life-critical/standing-service bar, **"the mechanism ships WITH the first fix"** (i.e. a
fix is not complete until the automated check that would catch its own recurrence exists
alongside it) — was already standing law on 2026-07-11, and was not obeyed by `05bc000`.
That fix did ship with a witness (evidence that it worked, gathered on a throwaway "probe
world" from three different angles/polarities), **but no recurrence net** — nothing that
would have gone red automatically the moment an eighth INSERT site was written without
binding an actor. The source assigns this specific omission upward rather than to the
individual fix's author, citing **ADR-0000 Rule 2(b)**, which it reads as making a
recurrence guard that was never mechanized structurally "the executive's to own" — i.e. an
organizational/process gap, not an implementer's personal error.

### 1.4 Why discovery was late, piecemeal, and depended on someone happening to look (source §1.4)

The source describes this defect class as fitting a documented profile — **"invisible-at-
authoring, visible-only-in-aggregate,"** a pattern already named in ADR-0011's Context
section — plus one extra aggravating property specific to this case: **it is invisible
even in aggregate as long as the default and the true intent happen to agree.** In a
"solo world" where the single registered principal `author` legitimately writes
everything, a row misattributed to `author` looks identical to a row correctly attributed
to `author`. Detecting the defect at all requires an environment where the default answer
is *wrong* — and the source identifies the first such environment as **the panel
deployment** (glossed above), which deliberately stopped letting its `author` identity
sign completions.

The source states it verified this live, read-only, against the panel deployment's actual
database (connection details taken from `experience/autoharn-panel/deployment.json`):
ledger rows 1502, 1599, 1710, 1716, 1719, 1732, and 1746 were all `work_closed` events, all
attributed to actor `1` (`author`), while the principal who actually should have been
credited — `item-countersign` — is a different registered principal, `21`. The panel
team's own incident report (`AUTOHARN_BACKFLOW.md`, "Finding 1" plus an addendum) is quoted
describing this in their own words as "not caller error, a CLI gap … the one write every
item's completion requires."

The source then works through, one at a time and honestly, each of autoharn's existing
automated verification mechanisms, to explain **why none of them caught this class before
the panel deployment tripped over it live**:

- **The "seen-red" fixture suites** — 90-plus test corpora under `seen-red/` that bank
  known-bad ("red") examples to prove a guard correctly rejects them. The source's finding:
  these suites exist *for guards that already exist* — a check that was never built has no
  corresponding fixture. A separate mechanism, `gates/fixture_census.py`, verifies every
  *existing* guard has a fixture; it does not and cannot verify that every *promise*
  (documented behavior) has a guard at all. The defect here was an absence, and this
  discipline only audits presences. The source adds that even the specific witness taken
  for the `05bc000` fix — the "three-polarity" probe mentioned above — only exercised the
  write paths that fix itself touched, not the class as a whole; it calls this "the witness
  universe was scope-of-fix, not class," and identifies it as the same lesson from a named
  prior case, **"CB-33's shipped-binding lesson"** (from the 2026-07-02 ADR-0011 amendment
  quoted above): a check can be green on the surfaces it happened to exercise while the
  surface actually used in production (here, the panel's completions) was never touched.
- **Pre-commit gates** (automated checks that run before code is committed, under
  `gates/`) — the source finds every one of these is scoped to checking documentation
  shape, code structure, or the kernel schema's shape. None of them reads `led.tmpl`'s
  INSERT statements to check whether their column lists include `actor`. No gate's
  declared scope ("universe," in the source's terminology) ever included "does this write
  path honor the intent channel" — and a gate cannot catch something outside the universe
  it was told to check.
- **The kind/shape manifest gates** (`kind_shape_manifest_gate.py` and related allowlist
  checks, which verify that certain database columns only take values legal for their
  row's "kind") — the source finds these are, by their own documented scope, restricted to
  columns whose legal values vary by row kind. The `actor` column is what the project
  calls a "CORE" column — legal on every kind of row, and filled automatically by the
  trigger described in §1.1 — which places it definitionally outside what these gates are
  built to check. The source calls this "correct behavior of a correctly-scoped gate" —
  the miss is that no *separate*, purpose-built check for intent-channel coverage existed
  at all.
- **The SQL/ASP differential, `./judge`** (glossed: autoharn's cross-check that derives
  the same verdict two independent ways — once in SQL, once in Answer Set Programming, a
  logic-programming paradigm run via the `clingo` engine — and compares them, to catch
  cases where the two encodings of "what the rules say" disagree). The source's finding:
  `./judge` verifies that two independent encodings of the *rules* agree about the *rows*
  already in the ledger. A misattributed row is still a well-formed row; both encodings
  would agree on it exactly as they would on a correctly attributed one. Attribution
  correctness is a question upstream of anything `./judge` checks.
- **What actually caught instances 2 through 4, and why it worked.** The source
  identifies the one mechanism that did catch later instances of this class: a
  documentation review pass required under [ADR-0017](../law/adr/0017-the-zero-context-reader.md)
  (the same tenet governing this document — see its "B-pass," an independent, fresh-context
  reviewer role). That pass caught a misattributing `led work open` code path (commit
  `e506806`, whose message the source quotes: "Caught by a doc B-pass that traced the
  actual INSERT branches after a spy's no-gotcha verdict" — a "spy," in this project's
  vocabulary, is a read-only reconnaissance subagent dispatched to gather
  evidence) because a piece of
  documentation — `design/USER-RECIPES-FAQ.md`, around line 308 — made a specific,
  checkable promise ("set LED_ACTOR for a dedicated-principal opener") that the reviewer
  traced against the actual code and found false. A separate, unrelated code reviewer of
  that same fix then caught a third instance by refusing to accept the overclaiming "EVERY
  … four" comment described in §1.3 and insisting on an honest enumeration instead (commit
  `6561e8a`). And the panel deployment's own no-author policy caught a fourth instance
  simply by changing the *oracle* — making the previously-invisible default now visibly
  wrong. The source draws one pattern across all three successful catches: **"the only
  surfaces that caught the class were the ones that compared intent against mechanism."**
  Every purely code-facing check, by contrast, verified the mechanism against *itself*
  (fixtures against guards that were actually built; gates against their own declared
  scope; the differential against its own twin encoding) — which the source calls
  "self-referential verification," which a coherent absence passes forever. The
  source states this as a finding, not a coincidence to be praised: **"the system's
  intent-vs-mechanism comparison existed only in the documentation pipeline."**

### 1.5 The tooling's own mode of failure, treated as a subject in its own right (source §1.5)

The source records that the maintainer, on learning of this, called the way the defect
surfaced "tacky," and states the record supports a sharper description: **the tooling
asserted coverage it did not have, twice, in its own self-description** — the `05bc000`
commit message's "every write path" claim (which the source's count shows covered 3 of at
least 6 write paths) and the post-`8c4bb3b` code comment's "EVERY … all four" claim (which
covered 4 of 7). Because the tool's own documentation of itself was false, the only way
anyone actually found each instance was archaeological: a person or reviewer manually
reading prose claims against the actual source code.

The source contrasts this with what a well-built tool would have done: the `--event-time`
flag idiom already present in the same file (§1.2) *refuses loudly* on any path that
doesn't support it. Had LED_ACTOR been built the same way, the very first attempt to use
it on an unwired path would have surfaced the gap immediately, as a visible refusal with
explanatory text — "in seconds," per the source — instead of silently succeeding with
wrong data.

The source's closing characterization of severity: the defect being named a
"never-again" class is earned not merely by the misattribution itself, but specifically by
**"the silent no-op of an explicit operator instruction"** — the operator said, in effect,
"sign this as principal X," and the tool said nothing while doing something else. The
source situates this against the kernel's overall purpose: the entire design (signed
"stamps," countersigns by a second party, `review_gap` debt tracking, segregation of
duties between principals) exists specifically to make "who signed this" a fact the system
can be trusted on. An attribution channel that fails silently is, in the source's words, "a
hazard under [CLAUDE.md](../CLAUDE.md)'s plank-with-a-nail standard" — and it stood
unaddressed through at least two shipped fixes that passed directly by it without closing
it.

---

## 2. The class-remediation direction (source §2)

The source frames this section as "ADR-0000-grade" — i.e. following the two-question
discipline [ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)
prescribes for closing a defect class: first, what *type* (data shape / structural rule)
would make the whole class impossible to represent, not merely detected after the fact;
second, what *mechanism* would loudly catch any future recurrence. As stated in the Status
section above, **none of what follows is built** — it is proposed direction only, pending
the maintainer's ratification.

### 2.(a) What shape would make the class unrepresentable?

The source names the class abstractly as **"a ledger-writing site that can ignore
operator attribution intent"** — which exists, per Part 1, because intent is carried
per-call-site over a substrate (the NULL-triggered default) that silently fills gaps. The
proposed foreclosing shape moves the intent-carrying responsibility **out of individual
call sites entirely**, at two layers:

- **CLI layer — one single owner of the session boundary.** *Gloss:* this invokes
  ADR-0012 principles **P1** (single source of truth — every fact has exactly one
  authoritative home) and **P2** (a boundary between two concerns is an explicit port
  with its dependency injected; a port translates-and-validates — it decodes the foreign
  representation into the native one and rejects what it cannot honor). The proposal:
  attribution intent should become a fact of the *database session* as a whole, not a fact
  re-supplied at each individual INSERT's column list. Concretely, the 35 hand-copied `SET
  ROLE` preambles (§1.2) should collapse into one shared preamble — their single rightful
  home — which, after `resolve_actor()` confirms the declared actor actually exists, issues
  one `SET app.led_actor = ...` statement: a Postgres session variable ("GUC," Grand
  Unified Configuration parameter, in Postgres terminology) that persists for the whole
  database connection rather than needing to be threaded through each query. Under this
  design, a write path could no longer ignore LED_ACTOR by doing nothing — honoring it
  would require *no* per-site code at all, because the session already carries it. The
  source states this explicitly inverts today's defect polarity: currently correctness is
  opt-in per write site; under a session-scoped transport, only a *deliberate* piece of
  code could still misattribute. The source also notes the 35-preamble duplication is
  itself the enabling P1 violation (§1.2) and should be collapsed to one owner in the same
  change, describing this collapse as "new structure" under a 2026-07-02 amendment to
  ADR-0012 (a rule that a large corrective diff earns its own careful review as new
  structure, not as a small patch).
- **Kernel layer — distinguish what NULL currently collapses, and offer an optional strict
  mode.** The proposal: the trigger function (`set_actor`) should be extended to check the
  session-level intent variable *first* (meaning intent was explicitly declared), and only
  fall back to the connection-role default when no intent was declared at all — recovering
  the distinction between "intent set" and "intent absent" that §1.1 describes as
  collapsed. On top of that, the source proposes an **opt-in "strict" mode**, settable per
  deployment (either a flag in a kernel table, or via a related mechanism the panel
  deployment has itself separately proposed, called `principal.revoked`, described in the
  panel's own "Finding 1, ask #1"), that would turn "this principal is no longer authorized
  to sign" from an unenforced policy statement into an actual database-level refusal
  (a BEFORE-INSERT trigger check). Under this proposed mode, in the panel's actual
  scenario, the *first* misattributed close would have produced a loud refusal instead of
  the five silent wrong rows in evidence. Strict mode would remain *off* by default in a
  solo-world deployment, where the connection-role default genuinely is correct and where
  ADR-0002 (§1.2) licenses exactly that default. The source characterizes both of these
  kernel-layer changes as **additive refusals or new vocabulary only** — nothing existing
  is loosened — which places them, if witnessed on a scratch/throwaway schema in both
  "should pass"/"should refuse" directions with `./judge` agreeing, inside the
  **class-ratified fail-safe tier** this project's [CLAUDE.md](../CLAUDE.md) describes
  (changes of this shape don't need a per-change maintainer question) — though the source
  notes the maintainer still routes any doubt to himself, as always.

### 2.(b) What mechanism would catch recurrence loudly?

*Gloss: this answers the second of ADR-0000's two questions, and follows ADR-0011 Rules 2
and 4 (recurrence converts to a mechanized check) and the "mechanism ships with the fix"
amendment quoted in §1.3.*

- **A gate/CI-layer check: an intent-channel coverage gate.** The proposal is to
  mechanize the same enumeration commit `9e33dc7` already did by hand (the 15-site,
  7-dispatch-point census cited throughout Part 1): an automated check that walks every
  `INSERT INTO <ledger>` statement in `led.tmpl` and confirms each one either rides the
  proposed session-intent preamble (or otherwise explicitly binds an actor) or appears on a
  *named, reasoned* allowlist of exceptions. The source specifies this must be a
  **structural predicate** — it must recognize the *shape* of an unwired INSERT, not a
  hand-maintained list of known site names — citing as precedent a 2026-07-16 ruling
  (visible in this repository's git log as the commit "s29/s30 detect siblings") that a
  detection mechanism must fingerprint behavior over the schema, never pin a specific name,
  because a later refactor can silently move the thing being detected without changing its
  behavior. Per the 2026-07-02 ADR-0011 amendment on negative controls (§1.3), the gate
  must also ship with a demonstrated **red case** — proof it actually fails on the
  pre-`5ad05cf` tree shape (the tree as it stood before the merge commit `5ad05cf`, which
  wired the last three write paths) or on a synthetic unwired INSERT — and be registered
  with the fixture-census discipline described in §1.4.
- **Generalize to a channel registry, not just this one instance.** The source proposes an
  **operator-intent-channel manifest**: an explicit, closed enumeration of every channel by
  which an operator's intent is meant to reach a `led` write — `LED_ACTOR`, `--event-time`,
  `--refs`, `--grade`, `--supersedes`, `--witness`, and any future addition such as a
  hypothetical `LED_SERIES` — each with its own declared coverage set, checked by the same
  gate to confirm every dispatch path either **honors or loudly refuses** each one. This
  promotes the `--event-time` idiom (§1.2) from one flag's individually hand-built guard
  into a general net covering the whole class of intent channels. The source ties this to
  a separate standing rule, "ADR-0000 Revisit #4 Clause 2," which requires that any such
  registry be a first-class, discoverable artifact rather than something only reconstructible
  by reading the corpus — because, as the source puts it, "the unregistered channel is
  exactly the one every audit misses."
- **Standing both-polarity fixtures.** A permanent (not one-off) "seen-red" style test
  suite that exercises every `led` write verb under three conditions: (i) LED_ACTOR unset,
  (ii) LED_ACTOR set to a registered, non-default principal, and (iii) LED_ACTOR set to an
  unregistered name. This makes the panel deployment's accidental "default is wrong"
  oracle (§1.4) a *deliberate, permanent* part of this project's own test suite, rather
  than something that only became visible by chance in a downstream deployment. The source
  notes commit `9e33dc7` already demonstrated this once, by hand, on throwaway probe
  worlds — but without a standing, permanently-run suite, that demonstration is exactly
  the kind of "describing record" ADR-0011 warns decays over time (§1.3).

### The closure statement (per ADR-0000 Rule 2(a), three required parts — see the sharpened rule quoted in §1.3)

The source proposes the following as a **candidate** closure statement (i.e. offered for
ratification, not yet adopted):

1. **The invariant:** an operator-declared attribution intent accompanying a ledger write
   either takes effect on that write, or the write is refused with explanatory
   ("teach-text") output. A silent no-op of a declared intent should be structurally
   impossible at the CLI transport layer, and refusable at the kernel boundary.
2. **The quantification universe, explicitly enumerated** (per the requirement in §1.3
   that this list actually be written down, not implied):
   - *Write surfaces covered:* the 7 dispatch points / 15 INSERT sites in `led.tmpl` (and,
     structurally, any *future* `INSERT INTO ledger` site there, since the gate is meant to
     key on the shape of the problem, not a fixed count); the ledger-seeding writes in
     `bootstrap/new-project.sh` (the script that sets up a new project's initial "birth
     chain" of ledger rows); and any hook or engine code path that writes ledger rows. The
     source explicitly flags that it **did not itself audit** this last category — these
     enter the universe either by matching the gate's structural predicate automatically,
     or by being explicitly named as excluded; they are not silently left out of scope.
   - *Layers that can silently default, all named:* CLI-side environment-variable
     resolution (the three unset/empty/unregistered variants from §1.1); CLI-side flag
     parsing (the source notes a related, sibling defect class already tracked elsewhere,
     named `led-refs-flag-order-parser-bug`, where flags get silently swallowed into
     statement text); SQL-level NULL fall-through (the `NULLIF` bind and the no-match
     subquery lookup, both from §1.1); the kernel's `set_actor` trigger default itself; and
     the read layer — views that display a misattributed row exactly as if it were
     correctly attributed.
   - *Detection surfaces that would be obliged to catch a recurrence:* the proposed
     coverage gate, the proposed both-polarity fixture suite, the ADR-0017 documentation
     B-pass (since, per §1.4, a documented promise is itself a falsifiable, checkable
     claim), and `./audit` (a separate operator verb; see [GLOSSARY.md](../GLOSSARY.md#audit)).
   - *Explicitly named as NOT covered by this proposal:* a person writing directly to the
     database with `psql` and supplying a deliberately wrong actor value (this is an
     accepted "writer-honesty" trust boundary, the same kind of bound already accepted
     elsewhere for a related field called `event_declared_ts` — the ledger column carrying
     an operator-declared event time via the `--event-time` flag, whose truthfulness is
     likewise trusted to the writer rather than machine-verified); and historical rows already
     written under the old, defective behavior (see the next bullet).
3. **The denomination check** (the requirement that a fix's evidence be measured in the
   actual unit that matters, not a proxy for it): the proposal states the bound must be
   measured in **attribution rows themselves** — checked per INSERT site and per intent
   channel — and explicitly never in a proxy measure such as "the resolver function
   exists" or "a comment says every path is covered." The source points out these are
   exactly the two proxy currencies the overclaiming commit message and comment from §1.3
   were paid in.

### What the source explicitly proposes NOT building

- **Strict mode as the default**, rather than opt-in. The source states this would break
  the legitimate solo-world case (§1.2/2.(a)) and would itself be an instance of a
  separately-named failure mode, "the over-typing weaponization ADR-0000 Revisit #2 warns
  of" (making a rule stricter than the cases it must cover actually require). Strict mode
  should be opt-in per deployment only.
- **Backfilling or correcting historical rows.** Per this project's standing "runs are
  linear" rule (rows already written are settled evidence, never edited after the fact),
  the panel deployment's already-misattributed rows stay as-is; any correction would take
  the form of new, superseding rows in their own ledger, never a rewrite. The source notes
  this matches how the `05bc000` fix already handled the same question — frozen worlds'
  copies of `led` are never retroactively touched.
- **A second, separate attribution channel** (for example, a new `--actor` command-line
  flag alongside `LED_ACTOR`). The source states two channels for one fact would itself be
  a fresh instance of "cancer B" (§1.2) at the interface layer.
- **Any LLM-judged detection** for this specific class — the source states every check
  this class needs can be fully deterministic (rule-based, not model-judgment-based).
- **Any certification-bureaucracy apparatus.** The source explicitly invokes a
  previously-rejected design (referred to as "the condemned-refgraph lesson," a prior
  instance of over-built process this project has already decided against) as the pattern
  to avoid, and states the goal is "one gate, one fixture suite, one manifest —
  mechanisms, not paperwork."

---

## 3. Generalization: is this a recurring shape elsewhere? (source §3)

The source asks, and answers with cited evidence, whether "silent-wrong-by-default" is a
pattern that recurs beyond this one specific defect class elsewhere in the project. It
answers **yes**, and lists specific, already-found instances:

- `seen-red/pickup-connection-failure-silent-empty/` — a test fixture (its own directory
  name states the finding) documenting that the project's `pickup` verb (the ledger
  "hydration"/read verb) returns silently empty on a connection failure, rather than
  raising a visible error.
- A note recorded during a documented run ("run-11") that an un-dispatched `led show`
  invocation was silently accepted as if it were a valid `kind="show"` row — consuming a
  sequence ID it shouldn't have.
- A separately-tracked defect, `led-refs-flag-order-parser-bug`, where command-line flags
  get silently absorbed into surrounding statement text rather than being parsed; its own
  escalation notes record that a warning-only (non-blocking) tripwire for this "re-bit
  twice in one day" before it was finally converted into an actual refusal — which the
  source calls "the same lesson (quiet signal ≠ net) one notch up" from the LED_ACTOR case.
- The project's own file-provenance stamping tool (the mechanism that records which
  session/run produced a file) itself **corrupted files and mis-attributed runs**, and had
  to be fixed three separate times (commits `e787ccb`, `9902c18`, `5d2ef21`) — cited as an
  instance of the project's own enforcement machinery failing silently, referenced in the
  same 2026-07-02 ADR-0011 amendment already discussed in §1.3.
- **"CB-33"** (glossed in §1.4 above): a case, from the same amendment, of load-bearing
  automated checks reporting green while actually measuring a code path that was never
  shipped to production.
- A separate, earlier root-cause analysis (referred to as "the what-did-we-miss RCA,"
  filed as "ADR-0000 Revisit #4") that found five independent layers of the system all
  silently inheriting the same omission, with zero warning flags raised anywhere.
- The "acronym gate" discussed in [ADR-0017](../law/adr/0017-the-zero-context-reader.md)'s
  own Context section — a documentation-legibility check that the source cites as itself an
  example of "a detection surface wired into nothing — silently not enforcing."

The source's generalized statement of the pattern: **"a default or fallback whose
correctness is conditional, running on surfaces where nobody has manufactured the
condition's failure."** Its proposed single discipline most likely to catch the *next*
unnamed instance of this shape: a **"default-adversarial witness rule,"** proposed as a
dated addition to ADR-0011 Rule 3's existing "probe-verify" requirement — stated as: *any
behavior that has a fallback or default must include, in the set of conditions it is tested
against, at least one where that default is the wrong answer.* This generalizes the panel
deployment's "no-author" policy (which accidentally created exactly this condition, per
§1.4) into a deliberate, standing testing discipline. The source's own framing of why this
matters: silent-wrong-by-default is precisely the kind of defect that passes every test
whose environment happens to agree with the default value; the discipline's purpose is to
keep at least one test environment that deliberately never agrees with it.

The source explicitly **flags as speculation** (its own term) whether either this rule, or
the intent-channel registry from §2.(b), would actually catch a channel that *nobody ever
registers in the first place* — noting plainly that a registry cannot, by definition,
catch what was never entered into it. For that residual, unnamed-channel case, the source
identifies the one mechanism that already worked once by coincidence rather than by design:
the ADR-0017 documentation review pass (§1.4), which treats every documentation promise as
a checkable, falsifiable claim to be traced back to its actual mechanism. The source
characterizes this as "judgment-transported detection" — a human/reviewer-judgment-based
safety net rather than a mechanized one — and states, citing "the ADR-0011 Rule 1
obligation" (the requirement to state a mechanism's limits honestly rather than implying
false completeness), that this is an honestly acknowledged review-grade backstop, not a
guaranteed catch.

---

## 4. What this RCA deliberately does not cover, and its confidence levels (source §4)

**Deliberately out of scope**, stated explicitly by the source:

- Implementation of anything described in Part 2 — the commission's mandate was analysis
  and direction only.
- A full audit of ledger-writing code paths *outside* `led.tmpl` — specifically, hooks,
  the engine code, and `new-project.sh`'s seeding writes. The "7 dispatch points / 15
  INSERT sites" figure used throughout rests on the independently-reviewed enumeration
  from commit `9e33dc7`, not on the source's own re-count.
- The upstream autoharn project's own ledger row 63 — the source verified the panel
  deployment's database live, but did not verify the upstream (this project's own) ledger
  in the same way.
- A full reading of [ADR-0002](../law/adr/0002-fail-loudly.md) (the "fail loudly" tenet).
  The source states its knowledge of ADR-0002's rules reached it only through verbatim
  quotations already embedded in ADR-0011, ADR-0012, and ADR-0013 (ADR-0002 was not on the
  commission's required-reading list), so any use the source makes of ADR-0002 leans only
  on those already-quoted rules, not an independent reading.
- The precise differences in how the `set_actor` trigger idiom evolved between kernel
  lineage deltas `s13` and `s15` — the source confirmed only that the *idiom itself* (the
  IF NEW.actor IS NULL pattern quoted in §1.1) is identical between them, not every detail
  of their history.
- A separate, parallel "principal design consult" the commission mentions is running
  alongside this RCA, commissioned by the maintainer — the source states explicitly it has
  not seen this consult's contents, deliberately, per the ADR-0018 front-loading
  discipline described in this document's opening (a consult must not be shown another
  consult's conclusions before forming its own).

**Confidence levels, stated by section, verbatim in substance:**

- **Part 1 (the RCA itself): high.** Every load-bearing claim is anchored to a specific
  commit, file and line, or a live database row the source read itself during the
  investigation session.
- **Part 2 (the remediation direction): high** on the mapping from diagnosis to proposed
  shape, and on the gate design; **medium** specifically on whether the proposed
  session-level GUC (Postgres session variable) transport mechanism is mechanically
  workable as described — the source states this was verified as *feasible* (the
  multi-invocation `psql` structure used today supports it, since the actor-resolving step
  and the actual write already run as separate sessions, so the proposed `SET` statement
  would need to live in the write's own preamble) but was **not prototyped or built**.
- **Part 3 (the generalization): high** on the specific cited instances; the proposed
  single unifying discipline (the "default-adversarial witness rule") is characterized as
  a design judgment call, with its stated limitation (does not catch an unregistered
  channel) treated as genuinely real, not a formality.
- **Part 4 (this section): complete**, to the extent of the source's own knowledge at the
  time of writing.
