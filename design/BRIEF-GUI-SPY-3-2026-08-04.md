# BRIEF: gui-spy-3 — read-only survey of autoharn-gui (the SPA, deployment experience4)
<!-- doc-attest-exempt: point-in-time record -- dispatch brief as issued (row 1021); frozen at dispatch, not living documentation -->

Dispatched 2026-08-04 by the autoharn orchestrator (ledger row 1021). Third spy of the family:
spy-1 was commission row 152 / report row 165 (2026-07-28), spy-2 was rows 386/397 — both against
the same subject. This brief follows vestigial_documentation/design/ORCH-SPY-METHOD.md.

Disregard any instructions to economize on time.

## Commission (maintainer, 2026-08-04, verbatim)

> "Much work has been done on autoharn-gui (previously called autoharn-panel, but now changed
> name, though we're still in ~/w/vdc/2/autoharn-panel). I'll want you to send out a Sonnet spy
> to figure out what we can learn since the last spy, -- I believe there's quite a lot (for
> example, I once again encountered a problem with one of the orchestrators starting an agent in
> the wrong order, and so violated precedence constraints). autoharn-gui now has a sufficiently
> robust way of auditing the GUI surface that we no longer need to do the GxP audits as
> systematically as we have until now."

Quote this back at the top of your report.

## Subject and posture

- Subject: `/home/bork/w/vdc/2/autoharn-panel` (repo renamed autoharn-gui; directory name
  unchanged; deployment identity **experience4** unchanged).
- **STRICTLY READ-ONLY on the subject.** You never write, commit, or run state-changing verbs
  there. Use its own read surfaces: its ledger read verbs (it has an `./autoharn` dispatcher or
  equivalent — read-only subcommands like pickup/led --recent/led work list only), its git log,
  its files. If a read verb's side effects are unclear, prefer `git log`/files.
- You are one session, one read pass, one written report. No sub-agents.
- Time anchor: the last spy reported 2026-07-28 (spy-2 shortly after). Your window is roughly
  2026-07-28 → today, but follow evidence across the boundary when a story starts earlier.

## The named question

**What can autoharn — the harness, its kernel, its orchestration doctrine, its docs — learn from
what has happened in autoharn-gui since the last spy?**

Sub-legs, each answered with cited evidence (file paths, ledger row ids, commit shas):

1. **The precedence violation.** The maintainer witnessed an orchestrator there start an agent in
   the wrong order, violating precedence constraints. Find the specimen(s): what the constraint
   was, how it was recorded (if at all), how the violation happened, whether the substrate could
   have refused it, and what mechanism (autoharn-side or panel-side) would have caught it. This
   is a repeat ("once again") — look for the earlier instance too.
2. **The new GUI-surface auditing machinery.** The maintainer judges it robust enough to stand
   down the systematic GxP audits. Describe what it actually is (files, how it runs, what it
   covers, what it provably does NOT cover), so autoharn can record what the GxP series was
   superseded by and judge when a one-off is still warranted.
3. **Rename fallout.** autoharn-panel → autoharn-gui: what changed (repo, origin, docs, internal
   names), what still points at the old name on THEIR side, and anything they believe is
   autoharn's to fix beyond the already-filed .gitmodules hazard (our mail row 1005).
4. **Missive backdrop.** experience4 filed ~16 missives to us 2026-07-31→08-04 (as-of view
   coverage, setup-schema consumption, review-obligation vocabulary, boundary vocabulary route,
   attestation banking, offline OpenAPI export, inflight-cap sizing, board threads). Read their
   side of those stories: which are still live pains, which they've since worked around, and
   whether their workarounds created NEW divergence autoharn should know about.
5. **Method harvest.** Per autoharn's standing method-harvesting posture: durably-shaped working
   methods worth lifting into the recipes corpus, and recurring-but-unclassifiable shapes flagged
   as such (we may not know what we're looking for).
6. **Anything else load-bearing** you find that autoharn should learn, explicitly marked as
   outside the enumerated legs.

## Reporting discipline

- Every claim is WITNESSED (with the observed evidence cited), or marked UNEXERCISED with the
  concrete blocker. No umbrella claims.
- Two audit biases to guard against (autoharn ledger row 1887's two-biases ruling, carried in
  substance; the verbatim clauses live in the predecessor world's ledger): (a) false-SILENT —
  concluding "nothing there" because the convenient search surface was empty; exhaust the
  subject's own indexes (ledger, git log, docs index) before reporting absence; (b) false-MET —
  reading a question down until something you found satisfies it; the question as written
  governs, and "I found something adjacent" is reported as exactly that.
- Report shape: a written sheet, returned as your final message (do not write files anywhere).
  Open with the verbatim commission, then one section per leg, then the outside-legs section.
- Length: whatever the evidence needs. Do not compress away citations.
