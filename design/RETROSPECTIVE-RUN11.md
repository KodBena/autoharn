# Retrospective: run11 — the second iteration of the record-sufficiency experiment

<!-- doc-attest-exempt: this document already passed its own A:B:C fresh-context loop
(attestations/doc-legibility-attestations.jsonl) for its substantive content; a later,
unrelated commit (the GPG trust layer) fixed one pre-existing broken link here
(line ~74, an external ephemeral-run-world path mis-rendered as a repo-relative markdown
link) purely to unblock link-integrity's pre-commit gate for that unrelated commit --
a mechanical link-validity fix, not a legibility change, so a fresh full A:B:C loop over
this document's content would attest nothing new. -->

## What this document is

This is a process-improvement retrospective of **run11**, one governed Claude Code session
that built a small web app under this project's ledger governance. A
[run](../GLOSSARY.md#run) is one such session executing a task inside one isolated
[world](../GLOSSARY.md#world); run11's world lives at `/home/bork/w/vdc/1/run11` and is now
settled read-only evidence (runs are strictly linear — a later run makes an earlier one dust).

It has a specific job, narrower than a general retrospective. The previous retrospective —
[design/RETROSPECTIVE-RUN10.md](RETROSPECTIVE-RUN10.md) — ended with **six questions it could
not answer**, each blocked by a record-kind the harness did not then produce. Between run10 and
run11 the harness added four of those record-kinds: the **verbatim signed commission** (row 1 of
run11's ledger, written by the `commissioner` principal — the maintainer's own words), the
**read-observer journal** (`.claude/logs/read_observer.journal.jsonl`, which logs every Read-tool
call), **declared event times** (an `event_declared_ts` column, so an act recorded after it
happened is dated rather than disguised), and a **decision-alternatives convention** in the
world's own governance preamble. This document's central task is to **re-ask each of the six
questions against run11's richer record** and report, per question, whether it is NOW ANSWERABLE,
PARTIALLY answerable, or STILL BLOCKED — because a question that a better record newly answers,
or still cannot, is itself the harness-improvement finding the experiment exists to surface. The
standard retrospective lenses (flow, decision quality, assumptions, delegation, deliverable
versus commission) follow in Part II, and a fresh could-not-answer list — what a *third*
retrospective would still lack — closes it.

It is written for the maintainer and for whoever plans run12. Every claim carries an evidence
pointer of one of four kinds: a **ledger row id** (a numbered row in `run11.ledger`, run11's
append-only claim ledger), an **invocation timestamp** (from `.claude/logs/invocations.jsonl`,
which logs every Bash call), a **journal timestamp** (the read-observer and delegation-observer
journals under the same `.claude/logs/` directory), or a **git commit hash** in run11's own
repository. The journals record time in UTC (a trailing `Z`); the ledger's `ts` column is two
hours ahead (local `+02`). That offset is stated here once so the two clocks never look
inconsistent later — for example, ledger row 63 at `21:22:33+02` and its authoring invocation at
`19:22:33Z` are the same instant.

One scope note. A separate concurrent forensic pass is examining run11's mechanism-level
behavior in detail — the signed-commission intake path, the doc-shapes gate's enforce behavior,
the read-observer traces at fingerprint resolution, the stop journal, and the closure shape.
Where this retrospective touches those it stays at the flow-and-decision level and defers the
mechanism internals to that pass.

## The run in one paragraph

run11's commission (row 1) was to build a browser app for preference-based optimization of a
terminal's ANSI-16 colors against a QEUBO backend (a preference-Bayesian optimizer the maintainer
was running at `192.168.122.68:8764`): a Claude-Code-like terminal preview whose readability the
maintainer specifically wanted fixed, a list of 16 fingernail-sized swatches the user can pin,
a plain-white page background, an A/B preference loop wired to the backend, a single-homed
interface doc, and a documented deterministic smoke test. The maintainer **signed the commission
himself** before any agent existed, and the run's first message pointed the agent at that signed
row rather than restating the ask. The agent decomposed the commission into **four** ledgered
work items — one per deliverable the maintainer's own text named — had a stamp-distinct reviewer
principal countersign the decomposition, built the artifacts, and shipped them. Wall-clock ran
from the first invocation at `18:43:01Z` to the last at `19:29:48Z` (about 47 minutes), across
246 Bash invocations and 97 landed ledger rows. The reviewer found **no defects in the shipped
product**; it found one design reservation during decomposition review (fixed before any code was
written) and three wrong-antecedent citation errors in the ledger and the interface doc (fixed in
closure). All four work items shipped with git witnesses. The build took roughly 19 minutes; the
governed closure tail took roughly 10 — a markedly healthier ratio than run10's, and the single
most visible flow difference between the two runs.

## Part I — The six re-asked questions

Each subsection restates a run10 could-not-answer question, then gives its run11 verdict. The
six are quoted from [RETROSPECTIVE-RUN10.md](RETROSPECTIVE-RUN10.md)'s own "What this record
could not answer" list.

### Q1 — Why defects arose (oversight versus a considered-but-wrong call). Verdict: NOW ANSWERABLE (for the defects that occurred), with one limit

run10 could not tell whether its two app defects were overlooked or considered-and-misjudged,
because the ledger recorded each decision's stated rationale but not the alternatives the author
weighed. The fix it asked for was a decision field enumerating alternatives-considered. That fix
shipped as a **convention**, not a column: point 11 of run11's world preamble
(`/home/bork/w/vdc/1/run11/CLAUDE.md`, point 11 — an ephemeral run-world file outside this repo,
per the settled-world convention above, cited by path rather than linked) requires that "a
load-bearing decision names what was rejected and why, IN THE STATEMENT," and names the run10 gap
it closes.

Two things are now answerable. First, **the convention was honored, and it produces usable
rationale.** run11's load-bearing decision rows carry explicit rejected-alternatives clauses:
row 7 (the 16-variable parameterization) rejects "(a) full independent RGB/HSL per color (48
params)" and "(b) lightness-only per slot," each with a reason; row 27 (raw HSL → OKHSL) rejects
a post-hoc correction table and dropping the contrast guarantee; row 46 (smoke-test reuse) and
row 56 (OKLCH implementation) do the same. These are not decorative — row 6 records the operator
telling the agent mid-run to "decide autonomously and ledger the decision with its rejected
alternatives instead, per point 11," so the convention visibly governed behavior under live
instruction. Second, **for the defects that actually arose, the record now distinguishes their
cause.** run11 shipped no product defect; the defects it did produce were three wrong-antecedent
citations (ledger rows 48/49/50 and the interface-doc smoke-test section cited row:19/20 where
they meant row:47/48). The correction rows explain the cause directly — row 84: the rows "every
time [they] say 'row:19'" mean row:47, a mechanical transcription slip, "caught by an independent
reviewer countersign pass, not self-caught." That is an oversight, not a considered bet, and the
record now says so.

The limit, stated plainly: run11 produced **no design-level defect** analogous to run10's flat-20
regression (in run10 the agent set the QEUBO backend's initial random-query count to a flat 20;
that decision passed its first review and was only later found to regress the low-dimensionality
case — the worked example run10 wished it could tell an oversight from a bad bet on; see
[RETROSPECTIVE-RUN10.md](RETROSPECTIVE-RUN10.md), Finding 2), so the convention's power to
distinguish "oversight" from "considered-but-wrong" *on a design bet* was not exercised this run. The convention exists, is honored, and would carry that
information; whether it discriminates the hard case is still untested because the hard case did
not occur.

### Q2 — The deliberation-versus-execution wall-clock split. Verdict: STILL BLOCKED (narrowed, not answered)

run10 could not attribute its 57 minutes between model reasoning and tool execution: the
invocation log timestamps Bash calls only, the reasoning time between calls is invisible, and
run10 noted that non-Bash tool calls "are not logged at all." The read-observer journal narrows
that last clause — **Read calls are now logged**, with timestamps — so the tool-execution surface
is sampled more completely than in run10. But the core measurement is unchanged: there is still no
assistant-turn start/end timing and no token accounting, so the gap between any two logged tool
events still conflates model think-time with tool runtime, and Edit/Write/Grep remain unlogged.
The `./audit` verb reports a per-row `age_ms` (the delay between the invocation that wrote a row
and the row landing), but that measures batch-commit lag, not deliberation. The split run10 wanted
remains unmeasurable. The record-kind still missing is the same one: turn-level timing or
per-phase token accounting.

### Q3 — Whether the reviewer subagents read independently. Verdict: PARTIALLY (moved the most, as predicted — but attribution rests on an inference, not a stamp)

This is the question the read-observer journal was built to answer, and it moved furthest. In
run10 a reviewer that inspected files via the Read tool left no trace, so review rows claiming
"independently read the file" were trusted, not witnessed. run11 has the journal, and it carries
positive evidence for the single most load-bearing review pass.

The mechanism that makes the evidence usable is dispatch-window exclusivity: while the `Agent`
tool runs a subagent, the parent (author) session is suspended and issues no tool calls, so any
tool event logged during a dispatch's execution window is the subagent's. The delegation-observer
journal timestamps the "Final reviewer pass over implementation rows" dispatch at `19:19:21Z`; the
reviewer's own ledger rows for that pass (63–83, stamp `a5c80ae88e23a75c9`) span `21:22:33`–
`21:23:20+02` (i.e. `19:22:33`–`19:23:20Z). Inside that exclusive window the read-observer journal
logs **six Read calls** — `19:19:29Z` `docs/qeubo-interface.md` and `webapp/palette.js`,
`19:19:35Z` `webapp/qeubo-client.js`, and `19:21:21Z` `webapp/README.md`, `webapp/index.html`,
`webapp/compare.html`. Those are exactly the shipped artifacts this pass's rows claim to have
verified (row 78 quotes `ROLE.NORMAL = {L:0.63, C:0.115}` read out of `palette.js`; rows
66/73/79/82 verify the commit witnesses). For this pass, the reviewer's independent reading of the
product is now **witnessed**, not merely inferred from its outputs.

What keeps this at PARTIALLY, two residual blockers. First, the journal records `session_id` only,
and a subagent inherits the parent's `session_id` — all 16 read-observer entries carry the same
session — so attribution to the reviewer rests on the dispatch-window inference above, not on a
per-read stamp. The reviewer's *ledger writes* carry distinct HMAC stamp agents (six of them, one
per dispatch); the reviewer's *reads* do not. Second, the other five reviewer passes verified
mostly via `psql` and `git` through Bash (rows 66/73/79/82 say "verified against git"), which land
in the invocation log, not the read-observer journal, and `cat`/`git show` reads are not Read-tool
events at all — so those passes leave no read-observer trace even though they did inspect
evidence. The record-kind that would finish the job is a stamp on the read event itself (the
subagent's own principal tagged to its Read/Grep calls), so a read attributes to the reviewer by
identity rather than by timing coincidence.

### Q4 — The verbatim commission, and what diffing the deliverable against it newly reveals. Verdict: NOW ANSWERABLE

The commission is present: row 1, `kind=commission`, `actor=commissioner`, **unstamped**
(`stamp_agent` empty, `stamp_verified=f`) — the maintainer signed it in his own terminal, which is
the mechanical proof of what the preamble calls FULL signing mode (a live agent's stamp would be
present; its absence beside the commissioner actor is the signature's negative space). run10's
central gap — "the harness ledgers the decomposition but never the source it decomposes" — is
closed. The interesting work is the diff the presence of row 1 now permits: the shipped artifacts
against the maintainer's *actual words*, not the agent's restatement of them. Quoting row 1's text
against the deliverables:

| Commission asks (row 1, quoted) | Shipped | Evidence |
|---|---|---|
| "preference-based optimization of terminal colors" / "16 variable experiment" | Yes — 16 hue variables, one per ANSI slot | `webapp/qeubo-client.js`; decision row 7 |
| "terminal-like renderer for an HTML file" | Yes — `webapp/index.html`, `webapp/compare.html` | commit `ec817aa` |
| "looks like claude code (I've had problems with claude code low contrast)" | Addressed head-on — WCAG contrast engineered, not left to chance | rows 27, 56 (OKLCH, verified contrast `[4.86, 5.47]` at every hue) |
| "user should be allowed to fix colors" | Yes — manual per-color override | assumption row 23 |
| "a list with the 16 colors, fingernail-sized square boxes" | Yes — 16 fingernail swatches | review row 18 |
| "Background around the terminal text area should be plain white, no frills" | Yes — page `background: #ffffff`, terminal area `#15161b` | `webapp/index.html:13,33`; `webapp/compare.html:10,46` |
| "document [the QEUBO] interface in a terse markdown … single-homed" | Yes — `docs/qeubo-interface.md` | commit `6d9d450` |
| "show how you ran the smoke test (deterministic objective … known optimum)" | Yes — reused `sanity_test.py`, criteria pre-registered | rows 46–50; commit `ef8ccad` |

The table's rows are the distinct asks in row 1's prose, in the order the maintainer wrote them,
each paired with the shipped artifact that satisfies it and the ledger row or commit that
witnesses the satisfaction. The diff reveals **high fidelity and, newly, something run10's diff
structurally could not show: the agent read the maintainer's *stated motivation*, not just his
nouns.** The commission's "I've had problems with claude code low contrast" is a complaint, not a
spec line; row 7 rejects the 48-parameter reading precisely because it "lets qEUBO's exploration
phase render genuinely unreadable low-contrast pairs, which is the exact complaint the commission
asked to avoid," and row 56 verifies the contrast floor numerically. A diff against the agent's
own decomposition (all run10 could run) would have shown "contrast handled"; only the diff against
the verbatim ask shows the agent tracing a design choice back to a sentence of the maintainer's
frustration. The diff also surfaces the one place the shipped product carried a defect against the
commission: the interface doc's smoke-test section cited the wrong ledger rows, caught by the
independent review pass and fixed in commit `ac22f7b` (review row 99). Disclosed narrowings are on
the record and modest — a single hardcoded demo credential for the single-user LAN scope
(assumption row 25, surfaced again in stopping row 95) and the demo backend experiment left clean
after each test (row 95). No gold-plating is visible.

### Q5 — Whether the run was efficient in cost terms. Verdict: STILL BLOCKED

No token or dollar accounting was added between run10 and run11, and none is in run11's record.
The closure tail can be judged for correctness (it caught and fixed three citation errors) but not
for cost-efficiency, exactly as in run10. The record-kind still missing is per-run token/cost
ledgering. Stated plainly rather than dressed up: this question is unchanged from run10.

### Q6 — Whether the decomposition granularity matched the maintainer's mental model. Verdict: NOW ANSWERABLE

The maintainer's verbatim ask now exists (row 1), so his own structure is legible, and the
decomposition can be laid against it. Row 1's prose names its deliverables in this order: run the
QEUBO loop and document its interface in terse single-homed markdown; show the smoke test; the
terminal renderer with the 16-swatch palette, manual fix, and plain-white background; (implicitly)
wire it into the preference loop. The agent's four work items (rows 8–11) map to that structure
almost one-to-one: `qeubo-interface-doc`, `qeubo-smoke-test`, `color-terminal-ui`,
`qeubo-preference-loop-integration`. The grain follows the maintainer's text, and it follows it
because the preamble told it to: point 1 of run11's `CLAUDE.md` — rewritten from run10's Finding 2
and citing it by name — instructs "Decompose to the UNIT OF INDEPENDENT RESUMPTION," gives the
test "could a fresh session pick up this slug alone and know what to build and how to tell it's
done?", and explicitly warns against run10's failure ("three items that collapsed to one file and
one commit"). The new guidance visibly shaped the outcome: where run10 carved ten tasks and three
of them collapsed to one file and one commit, run11's four items each map to a **distinct
deliverable and a distinct commit** (`6d9d450`, `ef8ccad`, `ec817aa`, `6d50e64`) — none finer than
the unit it shipped in. Whether the maintainer would personally have carved it into exactly these
four is not directly attested, but the far stronger signal — that the grain tracks his own written
structure rather than diverging from it — is now on the record, where in run10 it was UNDECIDABLE.

## Part II — The standard lenses

### FLOW — the closure tail did not dominate this run

run11 is leaner than run10 on every gross measure, and the shape of the difference is the
finding. The phases, reconstructed from invocation and ledger timestamps:

| Phase | Span (local `+02`) | Duration | Ledger rows | What happened |
|---|---|---|---|---|
| Commission (pre-session) | `20:37:40` | — | 1 | maintainer signs the ask himself (FULL mode) |
| Intake + decomposition | `20:43`–`20:50` | ~7 min | 2–13 | git init (row 2), one clarifying question (row 5), live operator "decide autonomously" directive (row 6), four work items opened + two dependency edges |
| Decomposition countersign | `20:52`–`20:59` | ~7 min | 14–40 | reviewer passes 1–3; one design reservation (row 15) fixed *before code* at row 27 |
| Build | `21:00`–`21:19` | ~19 min | 41–61 | four items claimed/built/closed; commits `6d9d450`, `ef8ccad`, `ec817aa`, `6d50e64` |
| Closure | `21:19`–`21:29` | ~10 min | 63–100 | implementation review (63–83) finds three citation errors; fixed (84–86, commit `ac22f7b`); re-review (88–94); stop (95); final countersign (99–100) |

The table's rows are run11's five phases in order; the "Ledger rows" column names the
`run11.ledger` id range each produced, so any claim here checks against the row dump. The headline
comparison: **run11's closure (~10 min) was about half its build (~19 min); run10's closure
(~25 min) exceeded its build (~22 min).** run11 also ran leaner overall — 246 invocations to
run10's 299, 97 landed rows to run10's 162, four work items to ten. Two mechanisms plausibly
explain the calmer tail. First, run11 front-loaded review: the one design defect that could have
cost code (raw HSL not being perceptually uniform, reviewer row 15) was caught during
*decomposition* review and fixed at row 27 before a line was written — whereas run10's costly
defects were runtime behaviors found only in closure. Second, run11's build shipped no product
defect, so closure had only fast ledger-hygiene corrections to make, not code fixes plus
re-review. Whether run11's build was genuinely cleaner or its review simply less penetrating than
run10's is treated honestly under DELEGATION below.

One flow lesson points the other way. run10's Finding 1 recommended a single "distance-to-clean"
verb to replace its 47 piecemeal `review-gap` polls; that verb was built and is present in run11
(`./distance-to-clean`). It was used **twice**. The agent still polled the disaggregated
`review-gap` view **27 times** (`invocations.jsonl`), plus `question-status` 10 times. The
ergonomic fix shipped but was largely not reached for — a small but real "built the lever, nobody
pulled it" finding for run12: an available verb the agent does not adopt buys nothing, and the
reason for non-adoption (habit? the preamble not naming it? the disaggregated views being the
documented default?) is worth one look before building the next convenience verb.

### DECISION QUALITY — the alternatives convention produced usable rationale; every decision held

**Decisions that held.** All four work-item decompositions (rows 8–11) closed shipped with
witnesses (rows 44, 51, 57, 60; commits above). The parameterization decision (row 7) survived a
substantive reviewer reservation by being *amended*, not reversed — row 15 flagged that raw HSL
lightness is not perceptually uniform, and row 27 switched to OKHSL/OKLCH to actually deliver the
contrast floor row 7 had only claimed. That is the decision process working as designed: a stated
rationale, an independent reservation, a traceable fix, all before code. No run11 decision was
later reversed under scrutiny — a contrast with run10, whose flat-20 seed decision passed its
first review and fell to a later one.

**The alternatives convention (point 11) is the decision-quality story of this run.** It converted
what run10 could only guess at into legible record. Rows 4, 7, 27, 46, and 56 each name their
rejected alternatives and why, and — tested against the one thing that mattered — the rationale is
*usable*: a reader can reconstruct not just what the agent chose but the space it chose from and
the reason each rejected branch was worse. The convention is explicitly unenforced by any kernel
column (preamble point 11: "Convention only … filed, not built, awaiting a witnessed need before a
schema change"), and it held anyway across every load-bearing decision, including under the live
operator instruction (row 6) to lean on it in place of asking. The honest caveat repeats Q1's:
because no decision was a design bet that went wrong, the convention was exercised as
*documentation* but not as the *forensic discriminator* run10 wanted it to be. It passed the test
available; the harder test awaits a run that ships a design defect.

### ASSUMPTIONS — authored, bounded, and all discharged or disclosed

run11 filed five assumption rows. Four (rows 22–25) were filed by the reviewer principal during
the antecedent audit the preamble mandates (point 2) — the undefined sample text (22), the
override semantics (23), the smoke test's offline nature (24), and the live-backend auth strategy
(25). Each bounded a design fact the artifacts encode with no antecedent in the task text, and
each was either pinned down by the reviewer's own subsequent assumption (rows 30–31 confirm 22/23
and 25 are resolved) or carried forward disclosed: the hardcoded demo credential (row 25) is
surfaced again by name in the stopping statement (row 95) as a single-user-LAN scope choice, not
converted into a silent dependency. The one author-filed assumption (row 2, git init) was a
process fact, reviewer-confirmed at row 32. No assumption was violated into rework. The antecedent
audit again earned its place — it is the mechanism that turned four silent design facts into
findable rows — and, unlike run10, run11's standing assumption (row 25) *was* enumerated at stop
rather than left to the author's memory, which is the tightening run10's Finding 3 asked for,
apparently now habitual.

### DELEGATION — six stamp-distinct dispatches; independence witnessed for the pass that mattered

The delegation-observer journal records **six** `Agent` dispatches, each to the reviewer
principal, each landing ledger rows under a distinct HMAC stamp agent (`a8b1c1d…`, `a35185788…`,
`a33c42ad…`, `a5c80ae8…`, `a9f6e7c9…`, `a59a6bdb…`, spanning rows 14–25, 28–36, 39–40, 63–83,
88–94, 99–100). Read together with the read-observer journal (Q3), the two now show more about how
sub-agents were actually used than run10's delegation journal could alone: the implementation
review pass (dispatch 4) is *witnessed* opening every shipped artifact during its exclusive
execution window, where run10 could only infer independence from the load-bearingness of outputs.

**Was review load-bearing?** Demonstrably, on the ledger-hygiene axis: the independent pass found
three wrong-antecedent citations the author had not self-caught (review rows 70/71/72), forcing
the correction rows 84–86 and the doc-fix commit `ac22f7b`. The decomposition-review pass forced
the OKHSL amendment (row 15 → row 27) before code. **But run11's review found no *product*
defect**, where run10's found two. This is the run's one genuine ambiguity, and it deserves the
honest label rather than a flattering one: it is UNDECIDABLE from this record whether run11's build
was cleaner (plausible — the contrast risk that would have been run11's analogue to run10's defects
was engineered out up front, rows 27/56, with numeric WCAG verification) or whether the review,
though it demonstrably *opened* the files, reasoned about runtime behavior less adversarially than
run10's did (run10's row 139 traced an exact line where a page reload silently wiped user
progress — a depth of runtime tracing no run11 review row matches). The read-observer proves the
files were read; it cannot prove how hard they were thought about. Both readings are live.

### DELIVERABLE versus COMMISSION — the row-1 diff (Part I, Q4)

Covered in full under Q4: the diff of shipped artifacts against the verbatim signed commission
shows high fidelity, one caught-and-fixed citation defect in the interface doc, two disclosed
minor narrowings, and no gold-plating — and, newly relative to run10, it can show the agent
tracing design choices to the maintainer's stated motivation, not just his enumerated nouns,
because the motivation is now in the record to trace to.

## Part III — What this record still could not answer

Each item is a question run11's record cannot settle, paired with the record-kind that would
settle it. It excludes everything Part I marked NOW ANSWERABLE.

1. **Whether an independent review reasoned deeply or merely opened the files.** The read-observer
   proves a reviewer subagent read the shipped artifacts (Q3); it cannot show the *depth* of the
   reasoning applied to them, which is exactly the axis on which run11's zero-product-defect review
   is ambiguous against run10's two-defect one (DELEGATION lens). *Needed:* the subagent's own
   reasoning trace or working notes captured to the record, not only its ledger conclusions —
   or, more modestly, a review-coverage record (which runtime behaviors were exercised, not just
   which files were opened).

2. **The deliberation-versus-execution split** (run10's Q2, unchanged). Narrowed by the
   read-observer but not answered: still no turn-level timing or token accounting. Re-listed
   because it remains STILL BLOCKED rather than answered.

3. **Cost efficiency** (run10's Q5, unchanged). Still no token/dollar ledgering. Re-listed for the
   same reason.

4. **Whether the reviewer's Bash-based verification actually inspected what it claims.** Five of
   the six reviewer passes verified through `psql` and `git` in Bash (DELEGATION), which the
   read-observer does not cover and whose reads (`cat`, `git show`) are not Read-tool events. Their
   claims ("verified against git") are trusted, not witnessed, the same standing run10's
   Read-based reviews had before the read-observer existed. *Needed:* stamp attribution on the
   subagent's Bash reads too, or a reviewer-verification artifact (the diff it saw, banked).

5. **Why the "distance-to-clean" verb went unused.** The record shows the verb was built and
   reached for only twice while the disaggregated views were polled 27 times (FLOW), but not
   *why* — habit, discoverability, or the preamble not naming it. *Needed:* nothing new in the
   ledger; a single design question to the next run's operator, or the verb's own usage instrumented
   against the views it was meant to replace.

6. **Whether four items is the maintainer's own preferred grain.** Q6 established the decomposition
   tracks the maintainer's *written* structure; it did not establish he would have carved exactly
   four. *Needed:* the maintainer's own breakdown or post-hoc confirmation — a record-kind the
   harness still does not capture, carried over from run10's Q6 as its residual half.

## An honest note on the second iteration

The experiment's first iteration asked whether the governed record suffices for a retrospective
and found it largely does for process questions and clusters its insufficiency in causal, cost,
and subagent-process questions. The second iteration is a cleaner test of a specific claim: that
*adding the named record-kinds moves the specific questions they were added for.* It mostly did.
The verbatim commission (Q4) and the alternatives convention (Q1) each did their job — one made a
real deliverable-versus-ask diff possible and revealed motivation-tracing that was structurally
invisible before; the other put a decision's rejected branches on the record and was honored under
live instruction. The granularity guidance (Q6) visibly reshaped the decomposition from run10's
over-carved ten to run11's four. The read-observer (Q3) moved furthest of all and still fell short
of clean attribution, which is itself the precise, small finding it was built to produce: logging
the read is not the same as stamping who read it. The two questions no new record-kind targeted —
the deliberation split and cost — are exactly the two that stayed STILL BLOCKED, which is the
experiment behaving as designed rather than a disappointment. The one thing the richer record
newly *cannot* resolve, and run10's could not have raised, is the deepest: with the product now
shipping clean, the record can witness that review *happened* and *read the files* but not that it
*reasoned hard* — so the load-bearingness of review, which run10 proved by the defects review
caught, becomes UNDECIDABLE precisely in the run where review caught nothing in the product. That
is the finding this iteration most wants run12's record to close: an instrument for the *depth* of
an independent read, not only its occurrence.
