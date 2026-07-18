<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

**AUDIENCE: this note is addressed to the autoharn-panel deployment's own orchestrator** — the
session (or its successor) that plans and builds the panel SPA/service, not to autoharn's own
maintainer-facing docs readers. It exists so that panel's next session PLANS against this
ratified direction instead of discovering it mid-build. It records a decision already made
upstream in autoharn's own ledger (rows 1471 and 1481), not a new proposal for panel to weigh.

**The one-sentence direction:** FastAPI becomes the SOLE declared boundary Port into the ledger
for UI-class consumers; the Vue app collapses to a pure consumer with zero database coupling.
This is ratified maintainer direction (ledger row 1471, endorsed by the orchestrator as the
concrete instantiation of the defeasibility envelope's serving-surface recommendation,
[design/FABLE-DEFEASIBILITY-ENVELOPE-2026-07-18.md](../design/FABLE-DEFEASIBILITY-ENVELOPE-2026-07-18.md)
§9), batch-ratified with seven other items at row 1481. Read row 1471 in full
(`./led show 1471` from an autoharn checkout) before building against this note — this is a
compressed pointer, not a restatement of its full text.

**Why now, not later:** two structural facts landed in autoharn's own kernel this same day that
make this the *right* moment for panel to plan against, rather than an aspiration to defer.

1. **Raw SQL is now structurally closed, not merely discouraged.** Kernel deltas s42/s43
   (commits `1fc4e8c`/`84729de`, spec:
   [FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md](../design/FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md);
   operator-facing delivery: [orchlog.d/s42-s43-typed-verdicts.md](s42-s43-typed-verdicts.md))
   revoke `INSERT` on every kernel-governed table from the granted role. A future panel-hosting
   world born on these commits has no raw-INSERT path left for ANY client to reach for, panel
   included — the four SECURITY DEFINER boundary functions
   (`kernel.ledger_write`/`review_write`/`registration_write`/`obligation_write`) are the only
   write path that exists. If panel's own architecture doc still describes writing SQL directly
   against the ledger (the maintainer's own characterization of panel's current access path,
   quoted in the envelope note §9: *"autoharn-panel writes SQL directly which is just bad"*),
   that description is now stale for any world born post-s43, not merely disapproved of.
2. **Refusals are now typed, UI-renderable verdicts, not stack traces.** Every boundary function
   returns `kernel.write_verdict` (`disposition`, `row_id`, `refusal_id`, `sqlstate`, `message`)
   — a refusal is a value, never a thrown exception the service has to catch and translate. This
   is a genuine synergy worth designing for from day one: FastAPI, calling the boundary functions
   instead of raw SQL, gets the refusal's own kernel-authored teach-text (`message`) for free and
   can surface it directly in the UI as first-class explanatory text — "why was this refused" —
   instead of manufacturing its own error copy or leaking a database error to the browser.

**The architecture, stated in the layering row 1471 itself insists on (so nobody conflates the
two boundaries):**

- **The kernel's own inner boundary** — s43's write functions plus the derived views
  (`ledger_current`, `principal_standing_current` and siblings — plus `credited_current`, once built; no credited view exists yet —
  etc.) — remains the authority. It is where truth is decided.
- **FastAPI is the OUTER declared boundary** (this project's [ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md) P2 sense of "Port"): it
  must add no truth of its own. Translate-and-validate, refuse what it cannot honor, never
  coerce — P2's own words, verbatim, cited because they are the exact discipline this
  consolidation asks FastAPI to hold. It reads the kernel's own views; it does not maintain a
  second, parallel notion of what is true.
- **Vue is a pure consumer.** No direct database coupling of any kind — every read and write the
  SPA performs goes through FastAPI's declared surface.

**The credited-view / SPA display contract** (envelope note §9.4, binding, not a
recommendation to weigh): **credited-only is the correct DEFAULT** — the SPA should not display
overruled ledger rows, pointwise-superseded or computed-defeated alike, by default. But the
standing ruling this project holds everywhere else — *ergonomics only with auditability held
constant* — makes the second half binding too: defeated and overruled rows, of BOTH kinds, must
remain reachable through an explicit history mode, shown as defeated-WITH-CAUSE (which
attestation, which grant, what grade defeated it — not merely "hidden"). A display layer that
made defeated history unreachable would be the dishonest version of the maintainer's own wish —
a censored record wearing a clean one — and no serving architecture the envelope note considers
is licensed to build that. This is the wall panel's read surface is designed against, not a
detail to relitigate.

On WHICH read architecture serves that contract: the envelope note (§9.3–§9.5) enumerates three —
(a) a standing read daemon, (b) engine-materialized defeat facts cached and joined by SQL, (c) an
ordinary SQL view (`credited`-style, read the way `ledger_current` is read today) — and its own
recommendation is **(c) now**, escalating to (b) or (a) only when a measured need for them
actually appears, because every defeat judgment in the envelope is stratified and therefore
plain-SQL-expressible; minting a standing high-authority serving daemon ahead of a judgment that
needs one would be ceremony ahead of substance. This is the note's inclination with its honest
alternative stated, not yet a maintainer ratification of the read side specifically — read §9.5's
"Reserved for the maintainer" sentence directly before committing panel's own build to one of the
three.

**What is NOT yet built, so panel does not plan around imagined machinery:** the `credited`-style
view itself does not exist yet in autoharn's kernel as of this note — row 1471 names it as
"already specified in the pinned envelope note," meaning designed, not shipped. Panel's own
build is `SONNET work, post-freeze, unblocked whenever the maintainer resumes the panel`
(row 1471's own execution-routing line) — it is authorized to proceed, but should confirm via a
fresh `./migrate --dry-run` (or reading autoharn's own current `kernel/lineage/` directory)
whether the credited view has landed on the commit panel is building against, rather than assume
it from this note.

**Authority note, carried forward from row 1471 verbatim in substance:** as the single surface
deciding what every operator sees, the FastAPI service inherits the same treatment autoharn's own
sentry-class services get — a registered principal for any writes it performs, and (per the
envelope note's day-4 discussion of a standing daemon) auditability of what it served against what
the kernel views actually hold, should panel ever move past option (c) to (a) or (b).

**Citations, for a panel session picking this note up cold:** ledger rows 1471 (the ratified
serving-boundary consolidation) and 1481 (batch ratification including the envelope's cascade
policy, which panel's future defeat-aware reads will need); the envelope note's §9 in full for
the read-architecture trade analysis this note compresses.
