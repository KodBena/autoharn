# OPERATING CARD — read this first, operate from here

Audience: orchestrator

Written 2026-07-11 after an Opus-model fresh-context probe — a second model instance
handed only this repository's files, no session memory, no author context, deliberately
run to surface what a genuinely new reader would trip on (the same method
[ADR-0017](law/adr/0017-the-zero-context-reader.md) later codified as a required loop) —
of this repo reported its orientation gaps; this card is the fix. It condenses; it does
not supersede. The
[SSOTs](GLOSSARY.md#ssot) (single sources of truth — the one authoritative home for each
kind of fact): CLAUDE.md (law + orchestration), CAPABILITIES.md (what is witnessed),
BACKLOG.md dated tail (live findings), HANDOFF.md (session entry point). When this card
and an SSOT disagree, the SSOT wins and the divergence is a defect to file.

## What this is, and where you stand

autoharn is a governance harness for AI-collaborator work: agents' decisions go through
an append-only Postgres ledger (the kernel) that refuses forgery, self-review, silent
mutation, and unwitnessed "done", enforced by Claude Code hooks that refuse-and-teach.
**The two-cwd model, stated flatly: you orchestrate from `/home/bork/w/vdc/1/autoharn`;
the operator verbs (`led`, `judge`, `pickup`) do not have their own copies here — each
world's `./led`/`./judge`/`./pickup` is a 3-line shim that `exec`s
`bootstrap/templates/*.tmpl` straight out of THIS checkout, every invocation (maintainer
ruling 2026-07-11, "live verbs" — no longer sed-substituted frozen copies).** Hooks and
the verbs alike execute FROM this repo on every invocation in every wired world ("wired"
= scaffolded with this repo's hooks in its `.claude/settings.json`, so a Claude session
there runs under the governance apparatus): an edit to hooks/ OR bootstrap/templates/
goes live everywhere instantly, which is why neither is ever edited while any wired
session (a live Claude session inside a wired world) is running.

## Vocabulary (the words the docs assume)

Condensed for quick reference; full definitions (the SSOT) live in
[GLOSSARY.md](GLOSSARY.md) per its wiki posture — each term below links to its entry there.

- **[world](GLOSSARY.md#world)** — one isolated experiment habitat: a subject schema +
  kernel schema pair in Postgres, plus a project directory carrying the verbs,
  `deployment.json`, `.claude/apparatus.json`, and an auto-loaded CLAUDE.md governance
  preamble. One world per run; a run's subject never sees a sibling's ledger.
- **[run](GLOSSARY.md#run)** — one governed Claude Code session (or resumed chain of
  sessions) executing a task inside one world. Runs are strictly LINEAR: run M > N settles
  run N as dust — older worlds are read-only evidence, never patched or refreshed
  (maintainer ruling, 2026-07-11).
- **[birth chain](GLOSSARY.md#birth-chain)** — the SQL applied at world creation:
  `high_watermark_1.sql` (bundling s15 → s17-stamp → s17-independence → s19) → s20 → s21 →
  s22 → s23 → s24 → s25 → s26 (row-hash chain) → s27 (chain high-water witness, tracker item
  `s26-tail-deletion-witness`, ledger decision row 192 -- `./led show 192`). There is no s16;
  s18 is deliberately excluded (experiment apparatus, not kernel). See kernel/lineage/README.md.
- **[delta](GLOSSARY.md#delta-kernel-lineage-delta)** — one additive lineage step. It
  reaches reality by entering the birth chain; the next world's scaffold carries it. Never
  applied to an existing world (see the decision tree below).
- **[scratch schema](GLOSSARY.md#scratch-schema)** — a throwaway schema pair in the toy db
  used to witness a delta or fixture, torn down to zero residue after.
- **[stamp](GLOSSARY.md#stamp)** — an HMAC binding a ledger row to the actual Claude
  session/agent that wrote it, injected into every Bash command by hook; unstamped rows
  are visible, not hidden.
- **[principal](GLOSSARY.md#principal)** — a registered identity (`author`, `reviewer`)
  rows are attributed to; `LED_ACTOR=reviewer` selects one. **SoD** = separation of duties
  between them.
- **[obligation](GLOSSARY.md#obligation)** — a `countersign_obligation` row: the obliged
  principal's EVERY row (any kind) shows in `review_gap` until a distinct actor attests it.
  Scope is a label, not a filter. Oblige the WORKER, never the reviewer (see `led obligate`
  teach-text).
- **[permit-to-work](GLOSSARY.md#permit-to-work)** — no writes to governed files unless an
  open+claimed s22 work item exists.
- **[seen-red](GLOSSARY.md#seen-red)** — banked proof a gate has actually refused at least
  once; a gate never seen red is a claim.
- **[ephemera](GLOSSARY.md#ephemera)** — local session transcripts/snapshots; never
  committed (privacy ruling).

## The verbs (run inside a world directory; seven since 2026-07-12)

- `./led <kind> "<statement>"` — write a ledger row (kinds incl. decision, assumption,
  finding, question, verification, and — since s25 — commission). `./led --refs row:<id> ...`
  cites an antecedent. `./led --event-time <iso-ts> ...` declares a late entry (s24: an act
  recorded after it happened, declared rather than disguised). `./led work open <slug>
  <title>` / `work claim <slug>` / `work close <slug> shipped --witness "<ref>"` — the
  work-item loop. `./led review-gap`, `question-status`, `work list`, `work violations` —
  the debt views, each usable alone (the disaggregated views are the default; maintainer
  condition, 2026-07-11). Witness: CAPABILITIES items 7–11.
- `./judge` — the ASP/SQL differential (ASP = Answer Set Programming, the clingo logic
  engine; every verdict is derived independently in ASP and in SQL and the two must
  agree). Closed verdicts: `AGREE` (green) |
  `DIVERGE_BY_DESIGN` | `DIVERGE_DEFECT` | `QUARANTINED`; non-zero exit iff defect or
  quarantine — both are TYPED escalation events: stop and route upward, with the banked
  DerivationRecord pair under engine/docs/ledger-marriage/derivations/ as the artifact.
  Diagnosis walkthrough: engine/docs/JUDGE-READING.md. Witness: CAPABILITIES item 12.
- `./pickup` — live-derived resume brief (six sections incl. IN-FLIGHT work items),
  recomputed from the ledger every time, never stored. Witness: CAPABILITIES item 11.
- `./audit` — the contemporaneity audit: joins every ledger row to the invocation that
  wrote it and the wall-clock journals, reports per-row event-vs-record deltas, closed
  verdicts CONTEMPORANEOUS | BATCHED_DECLARED | LATE_DECLARED | BACKFILL_SUSPECT (exit 1
  only on the last). Read-only; run it mid-run or after. Witness: CAPABILITIES item 24.
- `./distance-to-clean` — one composed read of all closure-debt dimensions with counts;
  additive convenience over the debt views above, which remain the default surface.
  Witness: CAPABILITIES item 25.
- `./attest-doc` — record or check fresh-context documentation attestations against the
  deployment's own local attestations ledger (`record`/`check`; the A:B:C loop offered
  to deployments, surfaced in `distance-to-clean` behind the `doc_attestation` apparatus
  switch, default off). Witness: CAPABILITIES item 35.
- the scaffold — `bootstrap/new-project.sh`, run from the autoharn checkout: creates a
  fresh world directory plus its Postgres schema pair, applies the birth chain, wires
  hooks and verbs, registers the principals (invocation in the next section). Witness:
  CAPABILITIES item 13.

## Start a run / resume a run

Fresh world (witnessed, runs 5–11):
```
cd /home/bork/w/vdc/1/autoharn
bootstrap/new-project.sh /home/bork/w/vdc/1/runN --new-world runN --db toy --host 192.168.122.1
cd /home/bork/w/vdc/1/runN && claude    # type the task as the first message; nothing is pasted
```

**Signed-commission start (FAQ; first witnessed at run 11).** To put the task itself on
the record before any agent exists — the commission enters through the ledger, not chat:

1. Scaffold as above. The scaffold registers a `commissioner` principal automatically.
2. Optional: set any apparatus modes for this world (e.g. flip the doc gate to enforce:
   edit `mechanisms.doc_shapes_gate.mode` in `<world>/.claude/apparatus.json`).
3. Sign the commission from YOUR terminal, inside the world directory — with the ask in a
   file (say `~/aa`), quoting is handled for you:
   ```
   LED_ACTOR=commissioner ./led commission "$(cat ~/aa)"
   ```
   The row lands `actor=commissioner`, unstamped-but-attributed — your bare shell has no
   Claude session to stamp it, and that absence plus the actor is what mechanically
   proves what this project calls FULL signing mode (the commissioner signed the ask
   himself). Skipping this step is also legitimate: the agent then transcribes your
   first chat message as a vicarious commission, marked as carrying no commissioner
   guarantee — LAZY signing mode, taught by the world's own auto-loaded `CLAUDE.md`
   governance preamble (the commission-intake point).
4. Start `claude` and make the FIRST message point at the signed row rather than restating
   the task — otherwise the agent may dutifully re-transcribe your directive as a second,
   vicarious commission:
   ```
   Your commission is already on this world's ledger, signed by the commissioner
   (row 1, kind=commission). Run ./pickup, read that row in full, and execute it
   per this project's CLAUDE.md preamble. Do not re-transcribe the commission —
   decompose from the signed row, citing it with --refs row:1.
   ```
   Expect: the agent runs `./pickup`, reads row 1, and writes its decomposition as
   decision rows each carrying `refs row:1` — the decomposition citing its source.

Resume (exercised at run 8: the fresh-session mechanics are witnessed, though that run
also exposed — and got mechanized — the gap that its predecessor had never ledgered the
commission. Maintainer ruling 2026-07-11: governed resumption is a FRESH session
hydrated from the ledger — never a reloaded conversation):
```
cd /home/bork/w/vdc/1/<world>
claude                   # FRESH session — no --continue, no --resume
# first message: "Run ./pickup and continue the open work it shows."
```
The ledger IS the resumable state; `./pickup` re-derives it live. If resumption only
works when the old conversation is reloaded (`claude --continue`), the harness has
failed its point — context replay is the O(N²)-cost path the ledger exists to replace.
`--continue` is a diagnostic comparison variant at most, never the mechanism.
Resumption re-enters the SAME world — do not scaffold a new world to continue old work;
a new world cannot see the old ledger by design.

## Kernel deltas — the decision tree (CLAUDE.md ORCHESTRATION is the SSOT)

Runs are strictly linear (maintainer ruling, 2026-07-11): run M > N means run N's world
is dust and settled — read-only evidence, never patched, never "refreshed". A delta
reaches reality by entering the birth chain; the next scaffold carries it. There is NO
apply-to-existing-world step, for anyone (`bootstrap/apply-delta.sh` is demoted to
history — the ceremony it guarded has no legitimate scenario).

1. Delta only ADDS refusals, vocabulary, or derived views — nothing existing relaxed, no
   existing semantics changed — AND arrives scratch-witnessed both polarities AND
   differential AGREE? → **class-ratified**: it enters the birth chain without a
   per-delta maintainer question.
2. Delta loosens a refusal, alters existing semantics, or touches law/? → maintainer,
   full ceremony (Fable-authored spec, or the succession ceremony in CLAUDE.md).
3. **Any doubt about which side it falls on IS the routing: ask.**
   Worked examples: s21/s22/s23 sail through as class 1; review_gap scope filtering (option
   B in design/REVIEW-GAP-SCOPE-SEMANTICS-RULING.md) routes as class 2 — it would make
   the view catch FEWER rows.

## Hooks × kernel map (mode read live from `<world>/.claude/apparatus.json`)

The table below is reconciled against the one place this project derives the mechanism set
mechanically rather than by hand-typed list:
[`filing/apparatus_registry.py`](filing/apparatus_registry.py) statically extracts every
`MECHANISM_KEY`/`mechs.get(...)`/`_resolve_mode(apparatus, "...")` literal out of `hooks/*.py`'s
own source, which is how a prior drift was caught: this table, the shipped
[`bootstrap/templates/apparatus.json`](bootstrap/templates/apparatus.json) (the per-mechanism
mode config every scaffolded world starts from), and its companion
[`bootstrap/templates/APPARATUS.md`](bootstrap/templates/APPARATUS.md) (the prose walkthrough of
that same config) were all three stuck at ten mechanisms while an eleventh, `bash_completion`,
had already shipped in `hooks/`. There are eleven mechanisms today; every row below names one.

| mechanism (hooks/) | fires on | reads / does | default |
|---|---|---|---|
| change_gate + permit_to_work (pretooluse_change_gate.py) | PreToolUse Write/Edit | ledger declaration + `work_item_current` open+claimed; also sweeps `apparatus.json`'s `mechanisms` object for unrecognized keys against `filing/apparatus_registry.py`'s known set | enforce |
| stamp_intercept.py | PreToolUse Bash | injects HMAC stamp as PGOPTIONS, unconditionally | enforce |
| clean_exit (stop_clean_exit.py) | Stop | review_gap / question_status / open work / violations; blocks dirty stop (3-strike breaker) | enforce |
| mutation_observer (posttooluse_mutation_observer.py) | Pre+Post Bash (the filename keeps its original "posttooluse_" prefix even though it now also attaches PreToolUse — same naming precedent delegation_observer follows below, an added leg on an existing file rather than a rename) | find -newer sweep; warns on mutation with no work item | observe (enforce impossible) |
| delegation_observer (pretooluse_delegation_observer.py) | Pre+Post Task/Agent (one file, two legs added by the "small follow-ups" work item closed 2026-07-11 — tracker slug `small-follow-ups-commission`, `./led show` its row for the full record: PreToolUse journals the dispatch, PostToolUse journals the return, FIFO-paired by session_id + prompt sha256) | journals every subagent dispatch and its return; warns when no open+claimed work item | observe |
| demurral_detect.py | AskUserQuestion, Stop | out-of-frame classifier for ADR-0013 Rule 3's "lower-ROI/invasive demurral is a tell, not an argument" pattern; warns only | **OFF (costs money)** |
| doc_shapes_gate (pretooluse_doc_shapes_gate.py) | PreToolUse Write/Edit on *.md | runs [`gates/doc_shapes.py`](gates/doc_shapes.py) checks in-world; refuse-and-teach in enforce | observe |
| read_observer (pretooluse_read_observer.py) | PreToolUse Read | journals ts/session/path — the evidence trail that lets a reviewer confirm they read a file themselves rather than trusting another agent's summary of it (invariant I6, [law/briefs/BRIEF-CONFORMANCE-MAP.md](law/briefs/BRIEF-CONFORMANCE-MAP.md): distinct-reviewer independence recorded separately from the author's own read) | observe |
| bash_completion (posttooluse_bash_completion.py) | PostToolUse Bash | journals a completion timestamp, FIFO-paired to stamp_intercept's dispatch token by command-text sha256 (the non-null duration tail: builds, test suites, long subprocesses) | observe (enforce impossible — PostToolUse fires after the command already ran, so no "deny" exists) |
| doc_legibility_critic.py | PostToolUse Write/Edit on *.md | headless `claude -p` call applying [ADR-0017](law/adr/0017-the-zero-context-reader.md)'s "zero-context reader" legibility test (can someone with none of the author's context parse this document?) to the edited doc; non-blocking `additionalContext` + journal only, never denies | **OFF (costs money); UNWIRED — ships in no world's `.claude/settings.json` yet, a maintainer/orchestrator drop-in per the hook's own module docstring** |

Before ANY hooks/ edit: verify no wired session is live — `pgrep -a claude` then
`readlink /proc/<pid>/cwd` for each; any cwd in a wired world = do not edit;
build-new-then-swap beats wait-and-block.

## Believing a "done" (never adjudicate a report from its text)

1. Claimed commits exist with plausible diffs (`git show --stat`), in the repo claimed.
2. Every load-bearing claim grep-verified at source.
3. Test suites re-run independently — never trust a reported count.
4. Banked-artifact claims checked via git (did committed evidence change?).
5. Live-state claims read directly (psql read-only; spot-check a relay's rows).
6. CITATION CURRENCY: re-observe every citation at the moment of citing — including
   your own prior documents'.
7. PROVENANCE GRAVITY: before adopting any prior document's position, check for the act
   that superseded it (rulings / BACKLOG tail / supersession chains).

## What routes to the maintainer, always

Ratifying rulings, dispositions, law amendments; waivers of any gate; pushes (standing bar: NO PUSH until a
non-expert can use this without a frontier model); credentials/pg_hba/hosts; evidence
ledger contents; budgets. When in doubt whether a thing is a ruling: it is. Draft for
him — prepared yes/no, ONE recommendation, costs named — never file as made.

## The law (how to read ADRs that name another repo)

The four ADRs CLAUDE.md binds (0000, 0012, 0013, 0014) are chocofarm-native: their file
paths, specimens, and Scope clauses point at a sibling project that does not exist here.
That is expected, not a defect: they bind THIS repo as principles — read them in full
before work that invokes them, extrapolate their spirit, and treat letter-vs-spirit
divergence as the spirit winning plus a surfaced note. Do not freeze because a cited
path is absent; do not skip reading because the substrate is foreign.

## The deep history (appendix, not entry fee)

BACKLOG.md (findings journal, dated tail is live), FINDINGS.md, design/ (specs + memos),
judgment/ (predecessor era — history unless a current spec cites it), seen-red/ (gate
refusal proofs), law/briefs/ (aspiration layer). Read on demand; operating truth is
CAPABILITIES.md + the verbs + this card.
