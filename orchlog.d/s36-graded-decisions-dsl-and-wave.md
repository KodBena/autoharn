subject: d5d52d4
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

One development wave landed 2026-07-16, most of it sourced from THIS deployment's own
findings (the compaction incident, AUTOHARN_BACKFLOW.md, and the maintainer's decision
queue). What you get, and what each piece needs:

**Free after the maintainer pulls the autoharn checkout** (live verbs execute in place;
no action in this repo):
- `./distance-to-clean` now checks the SAME five debt categories as the stop-gate
  (claimed-open work items and `work_review_gap` included) — its "TOTAL debt: 0" no
  longer under-counts what the Stop hook will block on. Where it cannot see session
  identity it says so in a printed caveat instead of hiding the gap.
- `led work open` now really parses `--refs` (every `--refs` you ever passed there was
  silently swallowed into the title — that is why the commission-decomposition view
  showed `items: []`; re-open or re-edge anything that mattered). All `work`
  subcommands now REFUSE unknown/typo'd `--flags` with a teach-text instead of
  silently dropping them.
- The delegation observer's warning is now honest: EITHER a session decision row OR an
  open+claimed work item silences it, and the text says exactly what is checked. Its
  advice now also prompts for a durable landing path for any dispatch deliverable that
  must outlive the session (your lost cycle-2 audit is the motivating specimen), and
  for worktree isolation when parallel dispatches mutate files.
- `attest-doc check` / `distance-to-clean`'s doc-attestation section no longer sweep
  gitignored vendor trees (your 155-item flood): raw-disk discovery stays (untracked
  real docs remain in scope) but `git check-ignore` now filters.
- `tools/workflow_check.py` + `design/workflows/*.toml`: a v0 pipeline DSL (phases /
  roles / convergence / landing_zones, nothing more) with four transcribed specimens —
  two of them are YOUR pipelines (ledger rows 42, 57) and your hand-built
  `scripts/cycle-workflow-template.mjs`. Validate a declaration with
  `python3 <autoharn>/tools/workflow_check.py <file.toml>`. Its README's "known
  misfits" section records what v0 deliberately cannot express yet.
- `tools/export_precedence.py`: emits this world's in-force `blocks-close` edges in
  makespan-scheduler's new native `depends_on` format (the scheduler's
  add-precedence-constraints branch is merged upstream) — the manual
  precedence-correction step you kept doing is retired.

**Requires `./migrate` (kernel delta s36, HISTORY: safe — one nullable column + one
view; the maintainer runs this, not you):**
- `led decision --grade durable "<statement>"` — a durability grade on decision rows.
- `./led standing` and a new no-recency-limit STANDING-DECISIONS section at the top of
  `./pickup`: ALL in-force graded decisions, regardless of age. This exists because a
  standing decision of yours (rows 193/200) could never have surfaced in pickup's
  LIMIT-10 recency window. Until s36 is applied, these refuse politely with a
  teach-text — that refusal is expected, not breakage.
- GRADE WHAT MUST SURVIVE: after migration, re-issue your durable standing decisions
  (filing homes, standing policies) with `--grade durable`. Superseding/retracting a
  graded decision removes it from the standing view automatically — grade freely.

**Requires one settings edit in THIS repo (maintainer's call, .claude/settings.json is
theirs):** the post-compaction re-injection hook — after a compaction or resume, all
in-force `durable` decisions are printed back into your fresh context automatically,
byte-capped, loudly truncated, failing open. The block to add alongside the existing
"Stop" entry, in this repo's own absolute-path idiom:

```json
"SessionStart": [
  {
    "matcher": "compact|resume",
    "hooks": [
      {
        "type": "command",
        "command": "env LEDGER_DEPLOYMENT=/home/bork/w/vdc/1/experience/autoharn-panel/deployment.json python3 /home/bork/w/vdc/1/experience/autoharn/hooks/sessionstart_durable_decisions.py",
        "timeout": 15
      }
    ]
  }
]
```

**Optional (defaults apply when absent):** `.claude/apparatus.json` →
`mechanisms.standing_decisions` `{"grades": ["durable"], "byte_cap": 4000}` — which
grade words the hook/pickup surface, and the injection byte budget. Pure policy data,
no mode switch.
