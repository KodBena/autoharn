# FABLE-SETUP-TUI-CHECKLIST-SPLIT-SPEC — "told" is not "verified", and selected daemons become an artifact

autoharn's setup TUI (the terminal wizard under `tools/setup_tui/` that creates new
autoharn deployments) keeps a setup checklist: a per-item record of what each wizard
screen established, each row carrying a status word. This spec, for whoever
implements or reviews the wizard, fixes two related defects: one status word
(`PREPARED`) currently blurs "the operator was told what to run" with "the thing is
confirmed present," and the set of background daemons an operator selects is never
written down anywhere runnable — so a selected daemon can silently never start.

- **Status:** Proposed (Fable-authored; Track 2.4 of
  [FABLE-SETUP-TUI-FIELD-STRATEGY.md](FABLE-SETUP-TUI-FIELD-STRATEGY.md); build
  gated on maintainer reading).
- **Date:** 2026-07-21
- **Commissions (verbatim):** maintainer observation g: "had to manually start
  boundary-multiplex / 1. on that note: should create a daemon collection script
  depending on selected options that start all relevant daemons and stores into the
  project folder." — and `AUTOHARN_BACKFLOW.md` finding 3's close: "have the setup
  checklist's 'PREPARED' status distinguish 'instructions printed' from
  'prerequisite file confirmed present,' and/or have the checklist verify at the end
  whether an operator-selected feature ever actually came up."

## 1. The defect class (ADR-0000 Rule 2)

**(a) The type.** `checklist.py`'s status vocabulary — `WITNESSED` (observed
happening), `SKIPPED` (operator declined), `PREPARED` (the value under repair here),
`REFUSED` (a gate said no), `WOULD_DO` / `DRY_SKIPPED` (dry-run analogues of an
effect and a skip) — lets one value, PREPARED, mean both "the operator
was told what to run" and "the thing this line depends on exists / is running." The
witnessed consequence (backflow 3): an opted-in monitoring feature produced zero
coverage, silently, its PREPARED rows reading as assurance — while the printed start
line referenced a config file the scaffold never wrote. The substrate screen already
models the honest form (a PREPARED block *plus* a separate live-probe verification
row); the observability screen opted out. The foreclosing type splits the status by
what was actually established, and reifies "the daemons this run selected" as data
with one home, from which both the checklist rows and a runnable artifact derive —
the single-source-of-truth principle P1 of
[ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md).

**(b) The lapse.** PREPARED was minted for one screen and reused by intention-drift;
no review asked what claim each row's status actually warrants. The net: the split
vocabulary makes the weaker claim unrepresentable as the stronger one, and the
end-of-run verification pass makes "selected but never came up" a loud row instead
of silence.

## 2. Status vocabulary change

`PREPARED` splits into three closed members (names final unless the maintainer
objects at ratification of the strategy):

- `INSTRUCTED` — the operator was shown a command/unit text; nothing about the
  world's state is claimed. (The old PREPARED's honest reading.)
- `PREPARED` — narrowed: every prerequisite artifact the printed instruction
  references was confirmed present at print time (config file exists, referenced
  interpreter exists). A PREPARED row names its confirmed prerequisites in detail.
- `VERIFIED_UP` — a live probe confirmed the named service running/healthy (the
  substrate screen's existing pattern, promoted to vocabulary).

Rules: a screen may not emit `PREPARED` without listing what it checked;
`INSTRUCTED` is always legal and never lies. Existing checklist consumers
(`Checklist.render`, the committed DataTable view, fixtures asserting on statuses)
migrate mechanically; grep the fixture corpus for `PREPARED` assertions and update
each with its own stated reason in the docstring and commit message — the practice
commit b565db1 established when it repaired six fixtures deliberately rather than
in bulk. The status enum is a
closed vocabulary (ADR-0008): no screen invents ad hoc detail-string conventions to
carry what a status should.

## 3. Selected daemons become one fact with one home

The wizard's decision phase queues typed plan entries — "Acts" (`plan.py`'s
`WriteAct`, `CommandAct`, `BackgroundAct`, …) — that its commit phase later
executes. A new plan-level record joins them (in `plan.py`, alongside the existing
Act types):
`DaemonSelection(name, argv, cwd, env_notes, health_probe)` — appended by each
screen that selects a standing service (boundary service, otelcol, otel-watch;
anything future). From this single list derive, at commit time:

1. **`<dest>/start-daemons`** — a generated, executable script (via the existing
   `runner.write_file` choke point — the one function through which all of the
   wizard's file writes are routed, so effects stay auditable at a single site) that
   starts every selected daemon with correct
   stdio hygiene, refuses per-daemon when a prerequisite is missing (ADR-0002 rung
   3, naming the missing artifact), and is idempotent (a daemon already up is
   reported, not double-started). The maintainer's g.1, verbatim scope: "depending
   on selected options ... stores into the project folder."
2. **The checklist rows** for those daemons (INSTRUCTED/PREPARED per §2 at commit;
   the script itself is the durable instruction).
3. **The end-of-run verification pass**: after commit, one screen-agnostic sweep
   probes each `DaemonSelection` with its `health_probe` and writes a `VERIFIED_UP`
   or a loud not-up row per daemon. "Selected but never started" is thereby a
   visible red-adjacent row, never silence.

Prerequisite artifacts join the same record: selecting otel-sentry adds the
`otelcol-config.yaml` WriteAct to the plan (closing the printed-command-references-
missing-file defect at its root) — the config template's content belongs to the
feature's scaffold data, not to screens.py (compose with the proposed ADR-0012
"data is not code" amendment,
[FABLE-ADR-0012-DATA-IS-NOT-CODE-AMENDMENT.md](FABLE-ADR-0012-DATA-IS-NOT-CODE-AMENDMENT.md);
do not add new embedded prose blocks).

## 4. Purity and scope

All new effects (script write, config write, probes-after-commit) live in the commit
phase through the existing choke points; the decision phase gains only the pure
accumulation of `DaemonSelection` facts. The purity gate's exemption table is not
extended. The boundary-service interpreter fallback fix (Track 3, separate task)
composes: `start-daemons` uses the same resolved-interpreter fact, resolved once.
Out of scope: systemd unit installation, daemon supervision/restart policy, and any
change to what features exist.

## 5. Witness set

- Vocabulary: fixtures asserting each of the three statuses is emitted only under
  its warrant; red leg — the observability screen on a world where the config
  WriteAct is suppressed must yield a loud not-up row, never PREPARED silence
  (red against pinned pre-fix module: the old code emits PREPARED with no config).
- `start-daemons`: scripted-mode birth in a scratch world; run the generated script;
  witness boundary `/health` green through it; re-run witnesses idempotence; a
  deliberately-broken prerequisite witnesses the per-daemon loud refusal. Teardown,
  zero residue.
- Regression: the scripted-smoke suite
  (`seen-red/setup-tui-scripted-smoke/`, currently 13 scripted end-to-end cases —
  the count is that fixture's own, and grows with it) plus the dry-run-parity
  fixture (dry-run must
  show the script/config as WOULD_DO rows and write nothing — parity table updated
  with rationale).
