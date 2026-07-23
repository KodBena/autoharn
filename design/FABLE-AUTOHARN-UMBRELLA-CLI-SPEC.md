# FABLE-AUTOHARN-UMBRELLA-CLI-SPEC — one program, git semantics, self-ensuring service

<!-- doc-attest-exempt: commissioned build basis, frozen 2026-07-23 pending ratification;
assembles the already-ledgered bindings of rows 1151-1154, 1159, 1162, 1165. Removal
condition: superseded by a polished live edition or the build's completion record. -->

- **Status:** Fable-authored 2026-07-23; awaits maintainer ratification. Pre-tag per the
  maintainer's ruling ("It would be silly to tag v2 with obsolete residue").
- **Commissions assembled (all verbatim in their rows):** row 1151 (git-type semantics;
  "the program is just a client to the FastAPI"), 1152 (root carries exactly ONE
  executable; implementations to a libexec-style directory), 1153 (idempotent,
  transparent service: human-started, LLM-started, or already-running all equivalent),
  1154 (no systemd/D-Bus/init dependence anywhere), 1159 (exploration must be free —
  help never writes, dry-run exists), 1162 (single-trust-domain v1; forward
  compatibility as named empty slots, never designs), 1165 (many concurrent sessions
  as the norm; spawn race resolved by bind-as-lock; version handshake with teaching
  refusal on skew).

## 1. The program

`./autoharn` at the repo/world root — the ONLY executable there. Dispatch is git's own
architecture: `autoharn <verb> [args...]` executes `libexec/autoharn/<verb>` (the
current ten verb implementations relocated, not rewritten — their semantics, refusal
texts, and exit codes carry over unchanged; this build is a re-plumbing, not a rewrite,
and every existing seen-red fixture must pass with only its invocation spelling
updated). Nested subcommands compose as today (`autoharn led work open ...`).
`autoharn --help` is GENERATED from the dispatch table — one line per verb with its
one-sentence description — making the help output the authoritative, drift-proof verb
roster (the count-drift class the doorway round just paid for dies at the root: docs
cite "run `autoharn --help`" rather than asserting numbers).

## 2. Ensure-running (the transparent service)

Every invocation that needs the boundary resolves it: reachable → use it, regardless
of who started it. Unreachable → consult the world's own deployment record and
descriptor, SPAWN the service as an ordinary child process (plain subprocess, detached,
its own logs under the world's directory; no init system, no D-Bus — row 1154), print
ONE line saying so (transparent is never silent — ADR-0002), then proceed. The spawn
race under concurrent sessions: the port bind IS the lock; a loser detects the lost
bind, re-probes, and ADOPTS the winner — someone-else-started-it is a success case
(row 1165). A service that cannot start (port genuinely held by a non-autoharn
process, config invalid) refuses loudly with the diagnosis; ./doctor's boundary line
is the standing check. `autoharn service status|start|stop` exist as explicit verbs
for operators who want manual control; ensure-running never fights an explicit stop
within the same invocation's scope.

## 3. Version handshake

The health/meta surface carries an explicit wire-protocol version alongside the
existing capability flags. Every client checks compatibility on first contact per
session (cached thereafter); a mismatch refuses with teaching naming BOTH versions and
the remedy (upgrade path or the matching checkout), never a silent misparse. The
protocol is versioned from v1 with an `authn_mode` field whose v1 value is
`single-operator` — the row-1162 named-empty-slot discipline: the descriptor schema
carries world identity including the s41 key-binding slot; nothing designs the trust
tier, nothing forecloses it.

## 4. Registration (the descriptor)

Birth writes a descriptor file (world name, host, boundary URL, epoch, capabilities,
protocol version, the named-empty identity slots) into the multiplexer's registry
directory; the multiplexer picks up new worlds without hand-edited config. Hub
consolidation: this build merges this host's two standing services into ONE hub as
the registry's first act (the maintainer has declared the old 8422 service
inconsequential; the consolidation is now free). The opt-in advertise/discover tier
(pure-Python mDNS, default refuse) is a named FOLLOW-ON, not this build — its slot in
the descriptor exists, its implementation waits for the multi-host arc.

## 5. Exploration safety (row 1159)

`--help` at every depth never writes and never requires a reachable boundary. Write
verbs gain `--dry-run`: print the exact payload and target surface, write nothing,
exit 0. The garbage-statement guard carries over unchanged.

## 6. Transition

The ten root executables become one-line alias shims (`exec ./autoharn <verb> "$@"`
with a single deprecation line to stderr) for ONE window — removed at the first
post-2.0.0 minor. The scaffold ships `autoharn` + `libexec/` + the alias shims;
./doctor learns the new resolution. CLAUDE.md's operator-surface sentence is
superseded at ratification ("the operator surface is `./autoharn` and its
subcommands; `autoharn --help` is the authoritative self-updating list"). The
doorway docs transform in the same build (the card's forward note discharges;
QUICKSTART/USER-GUIDE/README spellings update; the roster becomes "see
`autoharn --help`").

## 7. Witness plan

Both polarities throughout: dispatch parity (every verb's existing fixture green under
the new spelling via the aliases AND the umbrella form); generated help matches the
dispatch table mechanically (a fixture greps both); ensure-running — cold start spawns
with the one-line notice, warm start adopts silently-except-reads, the race witnessed
with two concurrent invocations against a down service (one spawns, one adopts, one
service survives); explicit-stop respected; version handshake red-first against a
skewed version constant; descriptor written at a scratch birth and picked up by the
hub without config edits; hub consolidation witnessed (both worlds served by one
service, old service retired); --dry-run prints-without-writing red/green; help-never-
writes swept at every depth. ./doctor all-PASS on a newborn under the new surface.
