subject: abba0dd
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

Three small `led` items landed together at `abba0dd` (build `a2c2a5f`, fixup `cf51542` — three
independent fresh-context Sonnet reviews came back FIT-WITH-FINDINGS, the fixer closed all
three findings in one commit). All three live in `bootstrap/templates/led.tmpl` only — no kernel
delta, no birth-chain gate, available in any world scaffolded from this commit forward,
including worlds that predate s42/s43. Delivery record: ledger row 1562; closes: rows 1563
(`led-work-list-state-filter`), 1565 (`led-help-token-closure`), 1567 (`led-json-payload-mode`).

**`led-help-token-closure`.** `'help'`/`'-h'`/`'--help'` as the FIRST word of a statement now
prints usage and writes zero rows on every writing subcommand — including `led decision --help`,
which the fixup closed: it used to fall into the generic unrecognized-flag refusal instead of the
same usage-and-exit-0 teach every other subcommand's `--help` gets. **Not yet complete for
`review`, though:** a bare `led review --help`/`-h`/`help` hits `review`'s pre-existing `$# -lt 4`
arg-count guard (`bootstrap/templates/led.tmpl` ~line 2501) before `check_help_or_dash_first_word`
(line 2506) is reached — 1 positional short of the 4 the guard wants — so it's zero-write but
exits **1**, not 0. The exit-0 path only fires once the three required positionals precede the
token (`led review <id> <verdict> <indep> --help`). Witnessed live against `autoharn1`, row count
unchanged either way. Genuine gap in `led.tmpl`, not closed by this fixup. Any
OTHER dash-leading first word (not a recognized help token) now REFUSES with usage rather than
silently committing the dash-word as statement prose — the gap `refuse_flag_in_statement`
already closed for KNOWN `led` flags anywhere in a statement, now closed for an UNKNOWN
dash-leading FIRST word too. If you see a garbage row whose whole statement is a bare `--help`
in an OLD ledger, that predates this fix; nothing retroactive.

**`led-json-payload-mode`.** `led --json <ledger|review|registration|obligation> <file|->` is a
new, additional write path — a JSON object routed VERBATIM to the matching s43 write-boundary
function (`ledger_write`/`review_write`/`registration_write`/`obligation_write`), the exact
payload shape `serving/`'s HTTP boundary service already accepts. Validation here is
well-formedness-and-shape only (parses as JSON, top-level object); everything else — including
the refusal or acceptance itself — is the kernel's own typed verdict, passed through verbatim,
never re-worded. Size-bounded at `MAX_WRITE_BODY_BYTES` = 1048576 bytes (1 MiB, matching the
HTTP boundary service's own bound), checked twice: raw bytes before parsing, re-serialized bytes
before the `psql` call. **s43-only, deliberately no pre-s43 fallback** — a world whose birth
chain predates `1fc4e8c`/`84729de` refuses `--json` outright (`capability_absent`), before the
size bound or the kernel ever see the payload; mirrors the HTTP boundary service's own pre-s43
refusal. `autoharn1` itself is pre-s43 (checked live: `has_s43_boundary` reads false against
this world), so if you are working in this checkout's own world, `--json`'s live surface here is
exactly two refusal shapes — bad `<surface>` word, or `capability_absent` — regardless of what
the file contains; do not expect to see the size-bound or kernel-refusal-passthrough behavior
until dispatched against a genuinely s43-carrying world. Fuller live cases (accepted write
echoing a row id, kernel-level unknown-key refusal) are in
`seen-red/led-json-payload-mode/run_fixtures.py`'s banked evidence, not reproducible here.
**Builder-flagged open choice, disclosed not smuggled in:** `--json` does NOT read `LED_ACTOR`
and inject it — the payload is taken verbatim; a caller wanting a specific actor passes the
already-resolved principal id directly as the payload's own `actor` key.

**`led-work-list-state-filter`.** `led work list` now defaults to `state <> 'closed'` (open or
claimed only) instead of the full historical dump — maintainer directive 2026-07-13, the
unfiltered view had grown to ~60 lifetime items (closed included) and had already overflowed an
orchestrator context read once. `--all` restores the previous full-history view unchanged. This
is a READ-VERB DEFAULT ONLY — nothing is deleted or hidden from the ledger itself; `led work
asof <timestamp>` and the raw ledger rows remain the complete, unfiltered record either way. If
a script or habit of yours assumed `led work list` shows closed items, it needs `--all` now; the
usage text (`led work list [--all]`) and this note are the only places that say so.

Migration: none needed for any of the three — no kernel delta, no lineage entry, nothing for
`./migrate` to plan. A checkout on `abba0dd` or later already has all three in `led.tmpl`; an
older checkout picks them up on its next `git pull` of the harness itself (not a per-world
migration).
