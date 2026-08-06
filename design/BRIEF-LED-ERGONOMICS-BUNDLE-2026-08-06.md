# BRIEF: led ergonomics bundle — four maintainer-prioritized items (rows 1087/1102 family)

<!-- doc-attest-exempt: point-in-time record -- dispatch brief as issued (row 1087 priority set); frozen at dispatch, not living documentation -->

Dispatched 2026-08-06, after the B1 builder's libexec/docs commit lands (confirm it is on main
at step 0 — the setup-schema verb commit). Repo: /home/bork/w/vdc/1/autoharn, branch main. Your
surface: libexec/autoharn/led, its seen-red fixtures, and the user-guide docs sections the four
items themselves need. STOP and report rather than edit outside it. Commit discipline: stage
only your files (CLAUDE_COMMIT_PATHS); fetch + ff-only merge before committing; never touch
other builders' dirty files.

Disregard any instructions to economize on time.

## Before you design

Read law/adr/ ADR-0000, ADR-0008, ADR-0012 in full; `./autoharn led standing` (row 26 no-bare-types
binds); libexec/autoharn/led end to end (house register: refusals that teach, exit codes, --json
discipline). The four items below are maintainer-prioritized 2026-08-06 in this order.

## Scope — four items, one commit

1. **led-read-projection-flags.** Two orchestrators keep piping led output through ad-hoc
   `python3 -c` filters (25 in one session). Add projection/filter flags to the read verbs
   (--recent/current/show/work list at minimum — enumerate what you cover and why): the shapes
   the witnessed filters actually needed (field projection, kind/slug/state filtering — design
   against the real uses, state your choices). Typed refusals for unknown fields/kinds, never
   silent empties.
2. **led-review-gap-false-clean.** Bare `led review-gap` silently returns empty while
   `led work review-gap` holds rows — a false-clean read, hazard-class. Make the bare verb
   truthful: either include work-item gap debt in its output (labeled), or refuse-and-teach
   pointing at the sub-verb — pick whichever the verb's existing contract honestly supports and
   defend in one line. Silent empty-while-debt-exists must be gone. Both polarities witnessed.
3. **refuse-verdict-legibility.** Orchestrator decision (this brief): gap surfaces SHOULD
   distinguish "reviewed-and-refused" from "never reviewed" — a refusal is information, absence
   is not, and conflating them is exactly ADR-0008 fuzzy-matching. Implement at the CLI
   presentation layer ONLY, from data the existing views already serve; if the distinction is
   not derivable without a kernel or serving change, STOP that sub-item and report the concrete
   gap (it then routes to spec) — do not fake it client-side.
4. **json-write-surface-parity.** `led --json` reaches ledger/review/registration/obligation
   but not obligation_revoke or missive_dispose though both exist as verbs. Close the parity
   gap following the existing --json contract exactly; refusals that teach for malformed input;
   both polarities witnessed.

Witness discipline throughout: real invocations against this world's live ledger for reads
(read-only) and a scratch/throwaway substrate for writes — never a fabricated transcript;
seen-red fixtures per the suite's own conventions. Commit citing the four item slugs + rows
1087/1102, Co-Authored-By line.

Out of scope: kernel/, serving/, hooks/, bootstrap/, the setup-schema verb, boundary routes.

## Report

Per item: what changed, design choices with one-line rationales, WITNESSED verbatim both
polarities / UNEXERCISED with blocker, flags in reach.
