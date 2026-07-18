# Error-recurrence hook — the self-triggering half of the capture discipline

<!-- doc-attest-exempt: build-basis spec; attestation rides witnessed delivery -->

**Status: Fable-authored 2026-07-19, build basis. Maintainer-directed same date ("I
think we should do the automatic part that the ADR-0011 FAQ question refers to"),
which supersedes row 1696's build-on-recurrence hold — his instruction is the
ratification, read plainly. Constraints carried from row 1696 verbatim: the signal
originates from the hook/action-stream layer (the evidentiary basis); otelcol stays
the observability window; detective control ONLY — the hook surfaces priors, it
never blocks, never writes suspensions, never polices.**

## The one hard safety rule (why the build is shaped this way)

Hooks execute LIVE from this checkout, per invocation, in every session that runs
here (new-project.sh's own baking note) — and the standing contract forbids
modifying hooks/ while a live session runs there. Therefore this build is
**additive-and-inert**: ONE NEW file under hooks/, gated internally by a NEW
apparatus key that is absent-or-off everywhere until an operator flips it; ZERO
edits to any existing hooks/ file; the live wiring of THIS repo (its settings/
apparatus) is untouched — adoption here is the maintainer's own act at a session
boundary. New worlds receive the mechanism via the scaffold templates, in `observe`
mode by default.

## Mechanism

1. **`hooks/posttooluse_error_recurrence.py`** — fires on the post-tool-use signal
   (same transport as the existing posttooluse hooks; mirror their config/dispatch
   convention exactly — read how posttooluse_bash_completion.py is wired and copy
   the shape). Internally: if the apparatus key `error_recurrence` is absent or
   `off`, exit 0 immediately (inert). Otherwise, on a tool result that matches an
   ERROR SIGNATURE (non-zero exit of a governed verb, a kernel refusal SQLSTATE
   line, a gate failure line — a small, enumerated, documented signature list, not
   a general regex zoo), derive a compact class signature and run the CROSS-CHECK:
   a read-only query of the world's ledger for `defect:` rows (the FAQ's grammar,
   USER-RECIPES-FAQ "Capturing errors..." section) whose CLASS-SLUG or specimen
   text matches. Matching is deliberately dumb in v1: slug token overlap + trigram
   text similarity, thresholds documented in-file; ADR-0011 mints anything smarter
   on witnessed misses.
2. **Output = teaching, never enforcement.** On a hit: print (to the hook's
   surface-to-session channel, matching the house convention the other observe
   hooks use) the prior rows' ids, class slugs, and foreclosing-fix fields, plus
   one line: "this class has priors — ADR-0011 says a recurrence mints a mechanical
   check." On no hit: silence. On its OWN failure (ledger unreachable, malformed
   rows): fail OPEN with a single stderr line saying the cross-check did not run —
   a detective control that silently dies is worse than none, and one that blocks
   the session is worse than that.
3. **Read path**: the world's own read transport — `./legacy/led`-style direct read
   or the boundary `/views/` route if the world's deployment.json carries the
   boundary keys; the hook must not hang on a dead boundary (short timeout, then
   the legacy path, then fail-open).
4. **Apparatus + docs**: `bootstrap/templates/apparatus.json` gains
   `"error_recurrence": "observe"` (new worlds observe by default);
   `HOOKS.md.tmpl` documents the mechanism, its signature list, its fail-open
   posture, and the off switch. This repo's own live apparatus/settings: NOT
   touched by the build.

## Witnesses (scratch worlds only; the hook exercised by INVOKING IT DIRECTLY with
a synthesized post-tool-use payload — never by wiring it into this repo's live
session)

- **WE1** world with a banked `defect:` row; synthesized error payload matching
  the class → hook prints the prior (id, slug, foreclosing-fix) and the ADR-0011
  line. Both transports if cheap; else the exercised one named.
- **WE2** payload matching no prior → silence (exit 0, no output).
- **WE3** apparatus key off/absent → inert (exit 0 immediately, no ledger query —
  witnessed by timing or query-log absence, not assumed).
- **WE4** ledger unreachable (bad host) → fail-open stderr line, exit 0, no hang
  (timeout witnessed).
- **WE5** a non-error tool result (ordinary success payload) → no signature match,
  no query (the signature list's precision leg).
- **WE6** scaffold: a fresh scratch world's apparatus.json carries the key at
  observe and its HOOKS.md documents it (template leg witnessed via a real
  --new-world run, torn down zero-residue).

## Amendment — 2026-07-19: the "unreachable" exit-status leg is reachable via PostToolUseFailure

The build witnessed (3×, harness 2.1.214) that PostToolUse never fires on a
non-zero Bash exit and disclosed the governed-verb-nonzero signature leg as
unreachable live. That disclosure was honest but incomplete: the harness's
documented contract splits the cases — PostToolUse fires only on tool success,
and a sibling event, **PostToolUseFailure**, fires on tool failure with the same
matcher patterns (code.claude.com/docs hooks reference, verified 2026-07-19).
The leg is therefore reachable; the miss was ours (only one event probed), not a
harness restriction. Binding consequence: when the dispatch wiring is authored
(the named open seam — an operator/maintainer act), the hook registers under
BOTH events; the hook file itself already parses the payload and needs no
signature-list change. The hook's in-file docstring currently carries the
falsified "unreachable" claim — correcting it is queued for the next
session-boundary hooks/ act (live-hooks rule; the file is unwired and inert, so
the stale sentence misleads no live path meanwhile).

New files only under hooks/ + the two template edits; NO edits to existing hooks/
files, this repo's .claude/ or apparatus config, kernel, law, serving, or
new-project.sh beyond what template wiring genuinely requires (if new-project.sh
must copy/mention the new template content, that edit is additive and named —
LINEAGE_CHAIN untouched). Python, top-of-file imports; gates apply; per-claim
witnessing; zero residue.
