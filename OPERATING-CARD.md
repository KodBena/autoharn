# OPERATING CARD — read this first, operate from here

Written 2026-07-11 after an Opus-model fresh-context probe of this repo reported its
orientation gaps; this card is the fix. It condenses; it does not supersede. SSOTs:
CLAUDE.md (law + orchestration), CAPABILITIES.md (what is witnessed), BACKLOG.md dated
tail (live findings), HANDOFF.md (session entry point). When this card and an SSOT
disagree, the SSOT wins and the divergence is a defect to file.

## What this is, and where you stand

autoharn is a governance harness for AI-collaborator work: agents' decisions go through
an append-only Postgres ledger (the kernel) that refuses forgery, self-review, silent
mutation, and unwitnessed "done", enforced by Claude Code hooks that refuse-and-teach.
**The two-cwd model, stated flatly: you orchestrate from `/home/bork/w/vdc/1/autoharn`;
the operator verbs (`led`, `judge`, `pickup`) do NOT exist here — they are materialized
into each world directory at scaffold time.** Hooks, however, execute FROM this repo on
every invocation in every wired world: an edit to hooks/ goes live everywhere instantly,
which is why hooks/ is never edited while any wired session is live.

## Vocabulary (the words the docs assume)

- **world** — one isolated experiment habitat: a subject schema + kernel schema pair in
  Postgres, plus a project directory carrying the verbs, `deployment.json`,
  `.claude/apparatus.json`, and an auto-loaded CLAUDE.md governance preamble. One world
  per run; a run's subject never sees a sibling's ledger.
- **run** — one governed Claude Code session (or resumed chain of sessions) executing a
  task inside one world. Runs are strictly LINEAR: run M > N settles run N as dust —
  older worlds are read-only evidence, never patched or refreshed (maintainer ruling,
  2026-07-11).
- **birth chain** — the SQL applied at world creation: `high_watermark_1.sql` (bundling
  s15 → s17-stamp → s17-independence → s19) → s20 → s21 → s22. There is no s16; s18 is
  deliberately excluded (experiment apparatus, not kernel). See kernel/lineage/README.md.
- **delta** — one additive lineage step. It reaches reality by entering the birth chain;
  the next world's scaffold carries it. Never applied to an existing world (see the
  decision tree below).
- **scratch schema** — a throwaway schema pair in the toy db used to witness a delta or
  fixture, torn down to zero residue after.
- **stamp** — an HMAC binding a ledger row to the actual Claude session/agent that wrote
  it, injected into every Bash command by hook; unstamped rows are visible, not hidden.
- **principal** — a registered identity (`author`, `reviewer`) rows are attributed to;
  `LED_ACTOR=reviewer` selects one. **SoD** = separation of duties between them.
- **obligation** — a `countersign_obligation` row: the obliged principal's EVERY row
  (any kind) shows in `review_gap` until a distinct actor attests it. Scope is a label,
  not a filter. Oblige the WORKER, never the reviewer (see `led obligate` teach-text).
- **permit-to-work** — no writes to governed files unless an open+claimed s22 work item
  exists.
- **seen-red** — banked proof a gate has actually refused at least once; a gate never
  seen red is a claim.
- **ephemera** — local session transcripts/snapshots; never committed (privacy ruling).

## The four verbs (run inside a world directory)

- `./led <kind> "<statement>"` — write a ledger row (kinds incl. decision, assumption,
  finding, question, verification). `./led --refs row:<id> ...` cites an antecedent.
  `./led work open <slug> <title>` / `work claim <slug>` / `work close <slug> shipped
  --witness "<ref>"` — the work-item loop. `./led review-gap`, `question-status`,
  `work list`, `work violations` — the debt views. Witness: CAPABILITIES items 7–11.
- `./judge` — the ASP/SQL differential. Closed verdicts: `AGREE` (green) |
  `DIVERGE_BY_DESIGN` | `DIVERGE_DEFECT` | `QUARANTINED`; non-zero exit iff defect or
  quarantine — both are TYPED escalation events: stop and route upward, with the banked
  DerivationRecord pair under engine/docs/ledger-marriage/derivations/ as the artifact.
  Diagnosis walkthrough: engine/docs/JUDGE-READING.md. Witness: CAPABILITIES item 12.
- `./pickup` — live-derived resume brief (six sections incl. IN-FLIGHT work items),
  recomputed from the ledger every time, never stored. Witness: CAPABILITIES item 11.
- the scaffold — see next section. Witness: CAPABILITIES item 13.

## Start a run / resume a run

Fresh world (witnessed, runs 5–7):
```
cd /home/bork/w/vdc/1/autoharn
bootstrap/new-project.sh /home/bork/w/vdc/1/runN --new-world runN --db toy --host 192.168.122.1
cd /home/bork/w/vdc/1/runN && claude    # type the task as the first message; nothing is pasted
```

Resume (the run-8 subject; UNWITNESSED until run 8 banks it. Maintainer ruling
2026-07-11: governed resumption is a FRESH session hydrated from the ledger — never a
reloaded conversation):
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
   Worked examples: s21/s22 sail through as class 1; review_gap scope filtering (option
   B in design/REVIEW-GAP-SCOPE-SEMANTICS-RULING.md) routes as class 2 — it would make
   the view catch FEWER rows.

## Hooks × kernel map (mode read live from `<world>/.claude/apparatus.json`)

| mechanism (hooks/) | fires on | reads / does | default |
|---|---|---|---|
| change_gate + permit_to_work (pretooluse_change_gate.py) | PreToolUse Write/Edit | ledger declaration + `work_item_current` open+claimed | enforce |
| stamp_intercept.py | PreToolUse Bash | injects HMAC stamp as PGOPTIONS, unconditionally | enforce |
| clean_exit (stop_clean_exit.py) | Stop | review_gap / question_status / open work / violations; blocks dirty stop (3-strike breaker) | enforce |
| mutation_observer (posttooluse_mutation_observer.py) | Post Bash | find -newer sweep; warns on mutation with no work item | observe (enforce impossible) |
| delegation_observer (pretooluse_delegation_observer.py) | PreToolUse Task/Agent | journals every subagent dispatch; warns when no open+claimed work item | observe |
| demurral_detect.py | AskUserQuestion, Stop | out-of-frame Rule-3 classifier; warns only | **OFF (costs money)** |

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
