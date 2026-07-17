# FABLE-RCA-CLASS-WIDTH-METACONSULT — polished living edition of the "is the RCA's class too narrow?" meta-consultation

**What this document is.** This is the polished living edition of a banked, verbatim
meta-consultation record:
[`design/ORCH-METACONSULT-RCA-CLASS-WIDTH-2026-07-18.md`](ORCH-METACONSULT-RCA-CLASS-WIDTH-2026-07-18.md)
(hereafter "the source"). The source is a frozen, point-in-time record — the complete,
unedited output of a second, out-of-frame, fresh-context Fable consultation, commissioned
by the maintainer on 2026-07-18. Its assignment was to take a rule this project's law
already states — [ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)'s
2026-07-02 amendment to Rule 2(a), which holds that **a newly named defect class should be
presumed too narrow until checked outward, because a class boundary that happens to
coincide with the edge of the fix already written is exactly the failure this rule exists
to catch** — and apply that rule *to a prior root-cause analysis itself*, as if the RCA
were the artifact under audit rather than a trusted input. The prior RCA under examination
is [`design/ORCH-RCA-ATTRIBUTION-CLASS-2026-07-18.md`](ORCH-RCA-ATTRIBUTION-CLASS-2026-07-18.md)
(hereafter "the RCA"), itself a banked, verbatim, out-of-frame Fable investigation into why
autoharn's ledger tool repeatedly misattributed writes to the wrong identity; a separate
polished edition of the RCA exists at
[`design/FABLE-ATTRIBUTION-CLASS-RCA.md`](FABLE-ATTRIBUTION-CLASS-RCA.md) and is assumed
readable background here, though this document restates enough to stand on its own. This
edition exists to make the meta-consultation's record readable by someone with none of the
authoring session's context, per
[ADR-0017 (the zero-context reader)](../law/adr/0017-the-zero-context-reader.md). **Where
this edition and the source ever appear to diverge, the source governs** — this document
adds no claim, opinion, or recommendation the source does not already make; it only unpacks
compressed language, glosses referents, and grounds structures. Substantive divergence from
the source is a defect in this edition, not a correction to it.

**Who this is for.** Anyone who needs to know whether the RCA's diagnosis of the
LED_ACTOR silent-misattribution defect class was named at the right scope, or too
narrowly — a future maintainer, a fresh AI collaborator continuing the remediation work, or
an outside auditor checking whether the project's own self-correction discipline was
actually applied to itself.

**What question it answers.** Did the RCA name its defect class too narrowly — the exact
failure mode ADR-0000's Rule 2(a) amendment warns against, and the same failure mode the
RCA itself found in an earlier, now-superseded fix attempt (commit `05bc000`)? **The answer
this consultation reaches is yes, on four of its seven examined axes**, with the remaining
three axes holding as the RCA stated them (one of those three with a partial exception, and
one with two minor nuances) — detailed below.

**Status.** This is analysis only; nothing in it has been built or ratified as a
consequence of this record existing. Per the maintainer's own commission (quoted in full in
§1 below), an outcome where the RCA's class was confirmed exactly as named ("idempotent")
was explicitly anticipated as a possible, valid result and was to be banked as evidence on
its own terms either way — the source's actual outcome, four widened axes, was **not** that
idempotent case. The remediation-direction changes this consultation recommends (§3 below)
await a maintainer ratification decision before any of them are built, on the same footing
as the RCA's own remediation direction. *Post-source development, an editorial note of
this edition and not a claim made by the source itself:* the brief prepared for this
edition states that the maintainer has, since the source was banked, ratified
"principal-surface-first ordering" and "strict-attribution-on-by-default" as governing
dispositions bearing on this material, and asked that this be recorded here as a dated
development citing the project's ledger. This edition's author checked the ledger (via the
`./led` command-line tool's `--recent` and `show` operations) up to its highest row
reachable at the time of this polish pass, row 1393 (dated 2026-07-18, the same day as the
source), and found no ledger row recording either ratification under those names or any
paraphrase of them. Rather than fabricate a citation or silently drop the claim, the author
recorded it as asserted-but-uncorroborated and flagged the divergence. **Resolution
(editorial note of this edition, dated the same day):** the author's refusal was correct
and caught a real recording failure — the ratification's original ledger insert had been
REFUSED (a `--grade` flag on a kernel predating the grade column) and the refusal had gone
unnoticed by the orchestrating session; the ruling was re-issued and now stands as ledger
row 1398 (with the incident itself filed as row 1399). The ratifications are therefore
real, dated 2026-07-18, and citable — and this edition's initial inability to find them
was the record-keeping working as intended, not an error in the search.

**Section numbering.** This edition keeps the source's own structure: §1 (the axes
examined), §2 (per-axis findings, split into 2.1–2.7 for the source's seven axes), §3 (what
the widened axes change about the remediation direction), §4 (what was deliberately not
examined), and a closing Confidence section — the same five-part shape the source uses,
renumbered only for markdown-heading nesting, never reordered or merged.

---

## Background you need before §1

A few pieces of standing vocabulary the source assumes, each also glossed inline at first
use below.

- **This document's own verdict vocabulary: WIDER and HOLDS.** These two words are how
  this consultation (and, following it, this edition) labels each axis's outcome under the
  ADR-0000 Rule 2(a) presumption. **WIDER** means the consultation found the RCA's class, as
  named, to be narrower than the evidence actually supports — a sibling instance, surface,
  or boundary exists that the RCA's stated class does not cover. **HOLDS** means the
  consultation checked the RCA's stated scope outward and found it actually correct as
  drawn — the presumption-of-narrowness was applied and did not overturn the RCA's claim on
  that axis. Per the commission's own instruction (quoted in §1), HOLDS findings are
  reported with the same evidentiary care as WIDER ones — a HOLDS is not a shortcut past
  verification, it is a checked and discharged presumption.
- **The ledger, `led`, LED_ACTOR, and actors.** As in the RCA: autoharn keeps an
  append-only Postgres record of decisions and work called "the ledger," every row written
  by a registered identity ("actor" / "principal"). The command-line tool `led`
  (source in [`bootstrap/templates/led.tmpl`](../bootstrap/templates/led.tmpl)) writes to
  it. `LED_ACTOR` is an environment variable an operator sets to declare which registered
  principal a write should be attributed to.
- **The dictum.** Shorthand this edition uses for the specific rule under test: the
  2026-07-02 amendment to [ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)
  Rule 2(a), which requires that a defect-class closure be stated as a **closure statement**
  with three named parts (an invariant, an explicitly enumerated quantification universe,
  and a denomination check in the resource that actually detonates) and inverts the default
  presumption: *"the class as first named is presumed too narrow"* until checked outward.
  This is the *2026-07-02* amendment specifically — a different, later provision of the same
  ADR, its **Revisit #4** of 2026-07-12, governs a separate concern (the standards registry
  a completeness audit must check against) and is not the rule this consultation applies.
- **Kernel lineage and "s-numbers."** autoharn's Postgres schema is built as a sequence of
  additive migration files named `sNN-description.sql` under `kernel/lineage/`
  (e.g. `s15-schema.sql`, `s19-trigger-search-path.sql`), each landed once and never edited
  in place; a later fix is always a new, higher-numbered file. "s14," "s15," "s19," etc.
  below are these files, referenced by number as the source does.
- **The panel deployment, its own "checkout," and the shim.** A separate, downstream
  installation of this same harness — an editorial note of this edition: per this project's
  own vocabulary, it is this project's own simulated downstream test-bed, run under a single
  git identity, not a document maintained by any outside team — living at
  `~/w/vdc/1/experience/autoharn-panel`. It runs its own copy of the `led` tool, but not by
  containing its own independent source: it uses a three-line **shim**, a tiny wrapper
  script at `experience/autoharn-panel/led` whose entire body execs the `led.tmpl` file
  found in a *separate, sibling git checkout* of this same autoharn repository, located at
  `~/w/vdc/1/experience/autoharn`. That sibling checkout is what this document calls the
  **serving checkout**, and the distinction it draws against a **repository file** (the
  source file as it exists, at whatever commit, inside *this* checkout, the one being edited
  right now) is the load-bearing finding of Axis 2 below: a fix landing as a commit in this
  repository does not, by itself, change what the panel's shim actually executes — that
  depends on the serving checkout separately being brought forward to (or past) that commit.
- **GUC.** Postgres terminology for a session-scoped configuration parameter ("Grand Unified
  Configuration" parameter) — a value set once with `SET` that persists for the lifetime of
  one database connection, as opposed to a value that must be re-supplied on every query.
  The RCA's proposed remediation (glossed further in the RCA's own polished edition) would
  use one to carry attribution intent for a whole `led` session rather than per write site.
- **The RCA's section numbers, `judge`, and `./audit`.** Where this document cites, e.g.,
  "the RCA's §1.4" or "§2(b)," it means the numbered sections of the RCA under examination
  (see [its polished edition](FABLE-ATTRIBUTION-CLASS-RCA.md) for the full unpacked text).
  `./judge` is this project's cross-check that derives the same verdict two independent
  ways (once in SQL, once in Answer Set Programming) and compares them; `./audit` is a
  separate operator verb (see [GLOSSARY.md](../GLOSSARY.md#audit)).
- **Panel rows.** Numbered rows in the panel deployment's own, separate ledger database —
  distinct row numbers from this project's own upstream ledger (the one `./led --recent`
  reads in this repository). A citation like "panel rows 1765 and 1768" below means rows in
  that downstream database, read live and read-only by the consultant during this session.

---

## 1. The axes on which the presumption was applied (source §1)

The source opens with a **method note**, quoted here in full because it states the
consultation's own evidentiary standard: *"every claim below marked WITNESSED was verified
this session against files, commits, or live read-only queries; nothing is repeated from
the RCA's prose on trust. Conjecture is marked as such. Per the commission, HOLDS findings
are stated with the same care as WIDER ones."*

The commission itself — the maintainer's instruction that produced this consultation — is
recorded verbatim in this project's ledger (row 1389, 2026-07-18) and is reproduced here in
full because it is the standard the whole document is judged against: *"One thing I would
like to do now, a bit as an experiment but mostly because I do not want to miss anything and
this is one of those things that, as said, is a never-again situation, and am personally not
competent to do this: Have* another *Fable consult apply the ADR-0000 dictum (And the
presumption is inverted: the class as first named is presumed too narrow) to the RCA
itself! Lets see if something of substance can come out of that. If it comes out idempotent
(possible), let that stand as evidence on its own, but* [do not] *front-load it."* The
consultation was run out-of-frame — a fresh Fable instance with no memory of the session
that produced the RCA — and briefed under
[ADR-0018](../law/adr/0018-consults-are-not-front-loaded.md) discipline: it received the
dictum itself, the RCA as the object under examination, the underlying evidence corpus, and
the governing law, but **no candidate list of wider classes was suggested to it** — finding
them, or finding none, was the consultation's own work.

The source lists seven axes it applied the dictum to, each corresponding to a distinct
component of the RCA's own diagnosis:

1. **The class name** — the RCA's own naming of the defect as "silent misattribution of
   ledger writes" / "a ledger-writing site that can ignore operator attribution intent."
2. **The quantification universe, write surfaces** — the RCA's enumerated list: "7 dispatch
   points / 15 INSERT sites in `bootstrap/templates/led.tmpl`; new-project.sh seeding; any
   hook or engine path."
3. **The quantification universe, kernel surfaces** — the RCA's citation of "the kernel
   `set_actor` default (`s15-schema.sql:136-145`, same idiom in s13)."
4. **The detection-surface list** — the RCA's §1.4 (why discovery was late) and the closure
   statement's part 2, "detection surfaces obliged" to catch a recurrence.
5. **The named exclusions** — things the RCA explicitly said its proposed remediation would
   *not* cover: direct-`psql` writer honesty; historical rows; the upstream ledger's own
   row 63.
6. **The §3 generalization** — the RCA's broader claim, in its §3, that "silent-wrong-by-
   default" is a recurring shape across the project, its cited instance list, and its
   proposed "default-adversarial witness rule."
7. **The closure-statement candidate itself** — whether the boundary of the RCA's own
   proposed invariant happens to coincide with the edge of the fix that already motivated
   it, which is the exact failure shape the dictum names.

---

## 2. Per-axis findings (source §2)

### 2.1 Axis 1 — the class name: **WIDER**, and the sibling is live today, not future

The RCA already generalizes, in its own §2(b), to an "operator-intent-channel manifest" and
names sibling intent channels (`--event-time`, `--refs`, and others) as candidates for that
manifest — so the RCA's own remediation-direction prose already gestures outward. But the
RCA presents those siblings as *future* manifest work, while its actual closure invariant
(closure-statement part 1) is scoped to attribution alone. This consultation found that the
sibling class the RCA gestures at is **already live in the current, fully-fixed tree**, not
a future risk:

**WITNESSED:** `led.tmpl:457-472` — a shared parsing loop at the top of the file parses
`-f -e --supersedes --amends --amends-scope --answers --refs --concern --evidence
--confidence --event-time` *before* the tool dispatches to any specific subcommand, for
every verb. Of that list, only `--event-time` carries a per-verb coverage guard (around
lines 615-626) — the loud-refusal idiom the RCA itself credits as the model to follow (its
§1.2). The `review` subcommand's INSERT statement (line 1258) binds only
`(kind, statement, regards, actor)` — no `--refs`, no `--supersedes`, no `--evidence`, no
`--confidence`; `led work claim`'s INSERT (line 1554) binds only
`(kind, work_slug, statement, actor)`; `led work close`'s INSERT (line 2043) binds none of
these shared-loop channels at all. The practical consequence: running, for example,
`./led --refs row:12 review 42 attest technical "basis"` successfully *parses* `--refs`,
writes the row, and silently drops the value with no error — a silent no-op of an explicit
operator instruction, mechanically the same shape as the LED_ACTOR class the RCA
investigated, just on a different channel. A separate guard, `refuse_flag_in_statement`
(lines 706-732), only catches flags placed *after* the statement text on the command line;
a flag placed *before* the verb on a subcommand that does not read it is swallowed by
construction, and this is a **distinct** defect from the already-tracked
`led-refs-flag-order-parser-bug` (a trailing-flag *parsing* bug, since escalated to its own
refusal — the RCA's §3 already cites it as a sibling instance elsewhere).

The general form of the class, per this consultation, is therefore: **a per-call-site-
transported operator-intent channel riding a silently-lossy substrate.** LED_ACTOR was one
instance of that general shape; roughly eight such channels, crossed with the roughly six
non-generic `led` verbs, are standing instances of the same shape *today* — not a future
manifest-building exercise but a present gap. The RCA's own §1.2 analysis ("a channel with
no forced read") already states this generality in the abstract; it is the RCA's class
*name* and closure *invariant* that then narrow back down to attribution specifically.

### 2.2 Axis 2 — the write-surface universe: one **WIDER** (load-bearing), the remainder **HOLDS**, partly re-verified

**HOLDS, and independently re-checked.** This consultation audited the surfaces the RCA had
left as "not audited — enters the universe by the gate's structural predicate, or is named
excluded" (the RCA's closure-statement part 2). By its own grep sweep: `hooks/` contains no
ledger `INSERT` statement anywhere (only teach-text mentions of the concept); `engine/`
writes only to scratch and derived-join schemas (files matching `*_scratch.py` and
`acts_join.py` — these are copies of ledger data for computation, not the ledger source of
truth); `bootstrap/new-project.sh` and `track-work.sh` insert only rows in `principal`,
`stamp_secret`, and `chain_genesis` — no ledger rows at all (the RCA's phrasing, "birth-chain
seeding writes," is thus slightly over-inclusive as a description, but harmlessly so — it
does not point at an actual gap); and the panel backend's sole write path shells out to the
world's own `./led` with `LED_ACTOR` already set
(`tools/autoharn-panel/backend/extensions/autoharn/cosign.py:1-52`), so it inherits whatever
`led.tmpl` itself does rather than writing independently. The RCA's own `led.tmpl` census
also checks out on re-count: exactly 15 `INSERT INTO ... ledger` sites and 35 `SET ROLE`
preambles (both independently re-counted this session), and all 15 currently bind an
`actor` value.

**WIDER — the serving-surface axis. This is the consultation's single load-bearing
finding.** The RCA's stated universe is denominated in "INSERT sites in
`bootstrap/templates/led.tmpl`" — that is, a *file identity* inside *this* repository. But
the defect actually detonates on *deployed executions* of that file, and — per the
Background section above — the deployment topology in question is not a scaffolded copy of
the file but a **shim** execing into a **serving checkout** that can independently lag
behind this repository. **WITNESSED, four legs:**

1. `/home/bork/w/vdc/1/experience/autoharn-panel/led` is confirmed to be exactly a
   three-line shim whose body execs
   `/home/bork/w/vdc/1/experience/autoharn/bootstrap/templates/led.tmpl` — a checkout at a
   separate filesystem path from the repository this fix landed in.
2. That serving checkout's own git state is pinned at commit `fe70575`. It contains commit
   `e506806` (the work-open attribution fix), but **does not contain** commits `9e33dc7` or
   `5ad05cf` — the depends/close/resolve-violation attribution fix that merged into *this*
   repository on 2026-07-17 — confirmed by running `git cat-file -t 9e33dc7` against the
   serving checkout's own object store, which fails (the commit object is simply absent
   there). Concretely, that serving checkout's own copy of `led.tmpl`'s `work_closed`
   INSERT statements (at its own lines 1882 and 2018) carry **no `actor` column at all**.
3. The panel's own live ledger (read read-only, using the DSN recorded in the panel
   deployment's own `deployment.json`) shows **panel rows 1765 and 1768**, both
   `work_closed` events, both attributed to `actor=1` (`author`), both dated 2026-07-17 —
   *new instances of the misattribution defect, beyond the set of rows the RCA itself
   cited (its rows 1502 through 1746), written* ***after*** *the upstream fix (`5ad05cf`)
   had already merged into this repository.* On the very same day, a different, correctly
   configured principal (id 21, `item-countersign`) correctly signed 71 rows through the
   properly wired `review` code path — so the serving checkout's staleness, not any
   remaining defect in the fixed code, is what produced rows 1765 and 1768.
4. No surface in the RCA's own detection universe — the proposed coverage gate, the
   proposed fixtures, `./audit` — runs against a *deployment's serving checkout* at all;
   nothing in the RCA's proposal obliges the shim's execution target to carry any minimum
   commit or lineage state.

The practical conclusion: the class the RCA's own §1.3/§2 language describes as "closed
across every ledger-writing path" (a characterization `led.tmpl`'s own current coverage
comment repeats) remains, in fact, **open and actively producing misattributed rows at the
one deployment whose ledger can actually be checked for it.** The RCA's closure statement
(its §4-equivalent "not covered" list) never names deployment or serving-checkout freshness
as either covered or excluded — the omission is inherited from thinking in terms of file
identities inside one repository, not an argued decision. This consultation characterizes
it as a superclass instance of the RCA's own cited "CB-33" lesson (green on the tree that
was actually exercised, unverified on the surface that actually serves the panel's live
completions) — recommitted one level up, at *checkout* granularity rather than *code-path*
granularity.

### 2.3 Axis 3 — kernel surfaces: **WIDER** on the enumeration (minor), one sibling checked and **discharged**

**WIDER (minor).** The RCA cites the silent-default trigger idiom as living at
`s15-schema.sql:136-145`, "same idiom in s13." This consultation confirms the idiom
**also lives** in `s14-schema.sql:188`, and that `set_actor` — the trigger function
itself — is **re-declared** (its body re-defined, not merely referenced) by
`s19-trigger-search-path.sql:64`, which is the live version of that function's body in
every world built at s19 or later, with additional trigger-ordering dependencies noted in
files `s17`, `s21`, and `s26`. The RCA's own "not covered" list names "s13-vs-s15
differences" explicitly, but does not name s14 or the s19 re-declaration. This matters
mechanically for remediation, not just as a count correction: any future delta that "splits
the NULL" (distinguishes intent-absent from intent-dropped, per the RCA's §2(a) proposal)
must land against whichever schema delta is the *current lineage head's* actual declaration
of `set_actor` — and the same lesson the RCA's own §2(b) applies to its proposed coverage
gate (detect a sibling by fingerprinting its behavior against the schema, never by a pinned
file name — citing this project's own 2026-07-16 "s29/s30 detect siblings" ruling) applies
equally to locating `set_actor` itself.

**HOLDS — an argued exclusion, checked and discharged.**
`kernel/lineage/nla-schema.sql:72` carries the same silent-default shape, but in a
different SQL form: a column-level `DEFAULT` clause
(`actor text NOT NULL DEFAULT current_user`) rather than a trigger body. That file's own
preamble comment argues the exclusion explicitly: it states that single-writer isolation in
that schema's use case makes connection-identity attribution correct by construction (the
default genuinely equals the intended value, because there is structurally only one
principal who can write there). This consultation checked that argument outward and
**discharged** it — it is a real instance of the solo-world case that
[ADR-0002](../law/adr/0002-fail-loudly.md) (this project's "fail loudly" tenet) genuinely
licenses a silent default for, not a silently-missed sibling of the defect class.

### 2.4 Axis 4 — the detection-surface list: **HOLDS**, with two nuances

**WITNESSED:** the `gates/` directory (this project's pre-commit automated checks) contains
no check for intent-channel coverage or INSERT-column completeness —
`column_complete_gate.py`, despite its name, checks a *different* shape entirely (view
columns versus table columns matching, not which flags an INSERT statement binds), and
`ledger_reader_allowlist` is a read-side check, not a write-side one. The RCA's own
surface-by-surface walk of *why* each existing verification surface could not have seen this
absence survives this consultation's independent re-walk unchanged. Two nuances are added,
neither of which overturns the RCA's finding:

- The kernel already has one pre-existing surface where a silent default *was* made
  adversarial for exactly one write path: the "same-actor-review refusal" — a misattributed
  review of one's own row is refused loudly, and `led.tmpl`'s own comment near line 1245
  states that the tool relies on this behavior. The RCA's §1.4 does not list this surface
  among the ones it evaluated (it only guards *reviews*, not the broader class, so its
  omission does not change the RCA's finding), but it is worth naming here as the one
  in-kernel example that already embodies the discipline the RCA's §3 later proposes
  standing up more generally (a default-adversarial test condition).
- The documentation "B-pass" — the ADR-0017 fresh-context review instrument the RCA's §1.4
  crowns as the one mechanism that actually caught later instances of this class — itself
  rides an attribution trust boundary of its own: `gates/doc_attestation_presence.py:62-64`
  states plainly that whether the B reviewer is actually a *different* identity from the A
  author is not machine-policed. This consultation characterizes this as an **argued
  exclusion**, not a silent gap — it follows the same identity-enumeration-fails-open
  reasoning [ADR-0017](../law/adr/0017-the-zero-context-reader.md) itself states for why it
  does not attempt to police A/B identity at the write hook — but notes that the RCA's own
  finding ("only intent-vs-mechanism comparison surfaces fired") should carry the caveat
  that even that one surface's own who-did-this check is, itself, an honor-system trust
  boundary.

### 2.5 Axis 5 — the named exclusions: **HOLDS**, one **partially discharged**

**Direct-`psql` writer honesty: HOLDS.** The same trust boundary the kernel already states
for a related column, `event_declared_ts` (an operator-declared event time the system
trusts rather than machine-verifies) — no mechanism can close this without adopting a
fundamentally different threat model, and the RCA was correct to name it as out of scope
rather than address it.

**Historical rows: HOLDS.** This project's "runs are linear" governing rule (a run's world,
once superseded, is read-only settled evidence, never patched) applies here as everywhere
else; the panel deployment corrects a misattributed row, if it chooses to, by writing a new
*superseding* row in its own ledger, never by rewriting the old one.

**Upstream row 63: partially discharged this session.** This consultation independently,
live-read the upstream project's own ledger (not the panel's) and confirms: `autoharn1`
ledger row 63 is a `work_claimed` event, attributed to `actor=1` (`author`), dated
2026-07-12 — consistent with the RCA's commit-message-based forensic reconstruction of what
that row should be. What this consultation states it **cannot** independently distinguish
is whether this is the *exact* row the earlier "run-7" investigation notes referred to, or a
same-shaped row from a since-superseded run-world now "dust" under the runs-are-linear
rule; either way, the shape the RCA describes does genuinely exist upstream.

### 2.6 Axis 6 — the §3 generalization: **HOLDS** on its cited instances; one sibling dropped without argument (**modest WIDER**)

The specific instances the RCA's §3 cites as evidence for "silent-wrong-by-default" being a
recurring pattern all check out wherever this consultation independently probed them. But
this consultation found that the RCA, in harvesting examples from the panel deployment's own
incident findings, took the panel's "Finding 1" asks #1 (a proposed `principal.revoked` flag)
and #3 (a uniform `resolve_actor()` call pattern) into its remediation direction, while
**silently dropping ask #2** without discussion: the panel's finding that
`register-principal`'s own INSERT clause,
`ON CONFLICT (name) DO NOTHING` — **WITNESSED live at `led.tmpl:880`, present in the current
tree** — is itself a silent no-op of an explicit registration attempt whenever the given
name is already taken. This consultation characterizes this as the *same shape* the RCA's
own §1.5 uses to justify the "never-again" severity designation for the LED_ACTOR class
(an explicit operator instruction, silently no-opped) — occurring inside the very same
attribution subsystem, inside the RCA's own cited evidence source (the panel's Finding 1),
and arguably **worse than benign**: re-registering an existing principal name with a
*different* `agent_class` value silently leaves the *old* class standing unchanged on the
existing row — a divergence between what the operator declared and what the system actually
recorded, with no signal raised anywhere. Neither the RCA's §2 (remediation direction) nor
its §3 (generalization) names this sibling, either as covered or as an explicitly reasoned
exclusion. This consultation grades the finding a **modest WIDER**.

### 2.7 Axis 7 — the closure-statement candidate itself: **WIDER**, and it is the dictum's own tell

The RCA's own proposed closure statement (its §2(b), part 1) states its invariant over
"operator-declared **attribution** intent" specifically; part 2's coverage-gate proposal
asserts that each INSERT statement should "ride the session-intent preamble (or bind
actor)." Under that exact closure statement as written, the live `--refs`-on-`review`
silent drop this consultation found under Axis 1 (§2.1 above) would **pass green** — the
invariant's own boundary coincides exactly with the edge of the fix already built (commit
`5ad05cf`), which is, verbatim, the failure shape the ADR-0000 dictum being applied in this
whole consultation exists to name. This consultation notes, in fairness to the RCA, that its
own manifest proposal in §2(b) *does* separately state the genuinely wider invariant
("every dispatch path either honors or loudly refuses each channel") — so the RCA in one
sense **already contains its own correction** — but that wider invariant appears there only
as a piece of proposed remediation *hardware* (the manifest mechanism), not as the actual
**closure statement** the defect class would be certified closed against. A closure
statement narrower than the very remediation it is bundled alongside is, in this
consultation's own words, "the overclaim mechanism of `05bc000` in a politer form" — a
direct callback to the earlier, already-diagnosed overclaiming fix commit the RCA's own §1.3
examines.

---

## 3. What the WIDER findings change about the remediation direction — direction only (source §3)

The source is explicit that this section states *direction*, not a built or ratified
change; nothing here is implemented by virtue of this document existing.

1. **The universe must be denominated in serving executions, not file identities.** Ahead
   of any of the RCA's own §2 machinery, the consultation states the cheapest *actually
   real* remediation is operational, not architectural: the serving checkout at
   `/home/bork/w/vdc/1/experience/autoharn` must be brought forward to carry commits
   `9e33dc7` and `5ad05cf`, or the panel deployment keeps producing misattributed closes
   daily — panel rows 1765 and 1768 (§2.2 above) are direct proof this is presently
   happening, not a hypothetical risk. Direction proposed: the closure universe gains a
   third column beyond "write surfaces" and "kernel surfaces" — **deployments, and the
   checkouts their shims exec** — and the project's recurrence-detection net gains a
   deployment-freshness surface: a deployment's own verbs asserting a minimum lineage or
   commit state of the tree they execute, in the same spirit as this project's existing
   verify-chain posture. The consultation notes this is the same lesson already ratified
   elsewhere in this project under the name "worktree bases are stale" (a standing rule that
   a builder's isolated working copy can silently lag the branch it thinks it is building
   against).
2. **The proposed gate should key on the channel *set*, not the actor channel alone.** The
   shared parsing loop (`led.tmpl:457-472`) and its flag vocabulary
   (`LED_FLAG_VOCAB`, around line 706) are already the one-list single source of truth of
   every intent channel that exists; the consultation's proposed gate predicate is "every
   channel the shared loop parses is, per dispatch path, either honored or loudly refused" —
   generalizing the existing `--event-time` coverage guard to the whole channel set — rather
   than a gate scoped to the actor channel specifically. Without this widening, a gate built
   exactly as the RCA describes would certify closure over a class that, per Axis 1
   (§2.1 above), still has eight live siblings standing.
3. **Any kernel delta should target the lineage head's `set_actor` declaration**, meaning
   the s19 re-declaration and its later trigger-ordering constraints (§2.3 above), not the
   s15 file's original, now-frozen text — fingerprinted per the same detect-drift lesson the
   RCA already cites for its own proposed gate.
4. **The remediation should carry the panel's dropped ask #2** (§2.6 above) — a refusal on
   duplicate `register-principal` attempts, or at minimum a refusal specifically on a
   conflicting `agent_class` value — into the same family of additive-refusal deltas the
   RCA's §2(a) already proposes, or it should be named as an excluded sibling with a stated
   reason, rather than left unaddressed by omission.

---

## 4. What this consultation deliberately did not examine (source §4)

Stated explicitly by the source as out of scope for this pass:

- Implementation of anything described in §2 or §3 above — no code, kernel delta, or gate
  was written; all database access performed during this consultation was read-only
  (`SELECT`), run under the deployments' own existing database roles.
- **Executing** the live `--refs`-on-`review` silent-drop witness described under Axis 1
  (§2.1) — actually running that command would itself write a misattributed row to a real
  ledger. The finding rests instead on reading the shared parsing loop's code and the
  affected INSERT statements' column lists, and is marked as resting on that reading rather
  than on an executed reproduction.
- The original run-7/run-8 world schemas — under this project's runs-are-linear rule, those
  worlds are settled, read-only "dust," not live evidence to re-derive from.
- Non-ledger journals written by `hooks/`.
- The panel deployment's frontend code.
- `tools/makespan-scheduler`.
- [ADR-0002](../law/adr/0002-fail-loudly.md), [ADR-0005](../law/adr/0005-documentation-discipline.md),
  and [ADR-0008](../law/adr/0008-classification-discipline.md) in full — used, as the RCA
  itself used them, only via their verbatim quotations already embedded in
  [ADR-0011](../law/adr/0011-mechanization-discipline.md) and
  [ADR-0013](../law/adr/0013-execution-integrity.md), the same bound the RCA itself
  declared for the same documents.
- The maintainer's separate, parallel, out-of-frame "principal design consult" — deliberately
  unseen by this consultation, exactly as the RCA itself deliberately did not see it, per the
  [ADR-0018](../law/adr/0018-consults-are-not-front-loaded.md) front-loading discipline.
- The stamp/session attribution machinery (kernel deltas `s17`/`s21`) beyond the
  trigger-ordering references already cited under Axis 3 (§2.3 above). The source flags,
  explicitly marked as its own conjecture and not investigated, a possible sibling class it
  did not probe: **"session identity silently defaulted"** — i.e., whether a comparable
  silent-default hazard exists in how a database *session's* identity (as opposed to a
  ledger row's declared actor) gets assigned.

---

## Confidence (source's closing Confidence section)

Per-axis confidence levels, stated by the source:

- **Axis 1 (§2.1): high** — code-witnessed (the shared parsing loop and each INSERT's
  column list were read directly), not executed.
- **Axis 2 (§2.2): high** — the serving-surface finding rests on four independent
  witnesses, including live database rows read this session.
- **Axis 3 (§2.3): high** on the underlying grep facts (the s14/s19 locations); the
  remediation implication drawn from them is a judgment call, not a fact claim.
- **Axis 4 (§2.4): high** on the gate census (which gates exist and what they check); the
  two added nuances are offered as observations, not as defects found.
- **Axis 5 (§2.5): high.**
- **Axis 6 (§2.6): high** on the witness itself (`led.tmpl:880` and the `ON CONFLICT`
  clause); modest specifically in how much weight the finding carries.
- **Axis 7 (§2.7): high** that the RCA's closure text is scoped to the actor channel as
  written; **medium-high** specifically on the interpretive claim that this constitutes the
  ADR-0000 dictum's own "tell" — held at medium-high rather than high because the RCA's own
  manifest bullet shows its author *did* see the wider invariant, which cuts against reading
  the narrower closure statement as a fully blind miss.

**The bottom line, in the dictum's own terms**, quoted from the source: *"the RCA is a
strong document whose analysis already reaches the general class; its naming — the closure
invariant and the universe's denomination — contracts back to the attribution instance and
to one file in one checkout."* The ADR-0000 Rule 2(a) presumption of too-narrow is **not
discharged**: two siblings are live and witnessed (the non-actor channel drops in the
already-fixed tree, per Axis 1; the panel deployment's still-misattributing closes running
through a stale serving checkout, per Axis 2); one sibling was harvested from the RCA's own
evidence source and then dropped without argument (`register-principal`'s silent no-op, per
Axis 6); and the single widest finding overall is that **the defect class detonates per
serving execution, while every net the RCA proposes quantifies per repository file.**
