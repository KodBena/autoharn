# BRIEF: setup-TUI session-currency sweep (item setup-tui-session-currency, rows 1087/1088/1228)

<!-- doc-attest-exempt: point-in-time record -- dispatch brief as issued (row 1228); frozen at dispatch, not living documentation -->

Dispatched 2026-08-06, the session's mechanically-last build (all twelve blocks-start
antecedents closed; kernel accepted the claim at row 1228). Repo: /home/bork/w/vdc/1/autoharn,
branch main. Surface: tools/setup_tui/ and its tests/docs only. A hooks/ micro-fix builder runs
concurrently — never touch hooks/. CLAUDE_COMMIT_PATHS staging; fetch + ff-only before commit.

Disregard any instructions to economize on time.

## Commission (maintainer, row 1087, near-verbatim)

"We should make sure that the setup TUI is up-to-date at the end of this session (which is when
the currently commissioned work is done)." The maintainer starts a NEW WORLD right after this
sweep — the TUI is the first thing that world's operator touches, so staleness here lands
directly on him.

## Scope

1. **Enumerate the session's config-surface changes.** The wave's commits: f8af7d7e, faddbb1c,
   c47dd507, 2d490245, e8582be9, 33150e9f, c65b21bf, 545f92c3, 78cf4377, 25677488. Known
   config-surface additions: boundary-multiplex.toml gained `max_inflight_per_deployment`
   (default 32) and `max_inflight_kernel_calls` (default 64). Sweep the commits yourself for
   anything else configuration-shaped (new keys, new verbs an operator must know at setup time,
   changed defaults) — do not trust this list as complete; that is the point of the sweep.
2. **Check the TUI's own schema scope.** Read tools/setup_tui/data/config_schema.toml and the
   TUI's own docs/code to establish what surfaces it actually manages. For each session change:
   in scope → update schema (typed per the schema's own conventions — closed vocabularies,
   bounds, defaults matching the shipped code EXACTLY: 32, 64, [1,10_000]) and whatever
   UI/plumbing renders it; out of scope → say so with evidence (the schema's own scope
   statement), never a silent skip. NOTE: `./autoharn setup-schema` (2d490245) now exports this
   schema byte-verbatim to external consumers, and experience4 was told format/path changes are
   announced by missive BEFORE landing — if you change the schema file, your report MUST say so
   prominently so the orchestrator sends that missive; draft the one-paragraph announcement
   text in your report (do not send it).
3. **Witness.** The TUI run live against the updated schema (real invocation, real output for
   the touched sections); schema still parses; `./autoharn setup-schema` output reflects the
   new content (sha256 changes — show old and new); existing TUI tests green per their own
   conventions.
4. **Commit** citing rows 1087/1088/1228, Co-Authored-By line.

Out of scope: hooks/, serving/, kernel/, libexec/ (setup-schema verb included — it reads the
file, needs no edit), bootstrap/.

## Report

The enumeration (every commit, config-surface or not, one line each); per change in-scope/out-
of-scope with evidence; WITNESSED verbatim; the drafted missive text if the schema changed;
flags in reach.
