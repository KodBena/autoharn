# FABLE-BOUNDARY-SSE-EVENTS-SPEC — a push signal for the boundary, strictly additive

<!-- doc-attest-exempt: Fable-authored spec 2026-07-28, maintainer-ratified in advance
(work item boundary-sse-events, autoharn3 row 169; his words: implement if it cannot
affect the CLI tools -- "we should absolutely implement it"; his punch-list item 7:
timer-based refresh annoying, "may need backend extension to allow SSE"). The A:B:C
loop runs on the build, not the proposal text. Removal condition: superseded by the
build's merge record. -->
<!-- design-currency: status=ratified depends-on=FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md -->

One new route on `serving/boundary_service.py`: `GET /d/{deployment}/events`,
`text/event-stream`. Everything else is untouched — no existing route changes shape,
no CLI client calls it, a client that never subscribes never notices (the ratifying
condition). The closed-enumeration posture is kept: this is one more member of the
typed universe, documented here, not an open surface.

## 1. Semantics — a SIGNAL, not a data channel

The stream carries **head advancement only**: when a deployment's ledger head (max
row id) grows, subscribers receive one event `event: head` with data
`{"head_id": <n>}`. No row content ever crosses the stream — a client that learns the
head moved fetches rows through the existing read routes, with all their bounds,
pagination discipline, and refusal taxonomy intact. This keeps the stream (a) trivially
cheap, (b) free of any second pagination/serialization contract, (c) honest about what
SSE here is: the server polls Postgres once so N clients don't, plus latency.

Mechanics, each deliberate:

1. **One shared watcher per deployment**, started lazily on first subscriber, stopped
   when the last unsubscribes: polls `max(id)` at `SSE_POLL_INTERVAL_SECS` (default 2,
   config-overridable in boundary-multiplex.toml). No kernel change, no
   LISTEN/NOTIFY trigger (that is a lineage delta for a future birth; slot named,
   deliberately not built — same posture as row 169's sketch).
2. **Resume**: the client may send `Last-Event-ID: <n>` (or `?after_head=<n>`); on
   connect the server immediately emits the current head if it exceeds that value, so
   a reconnecting client misses nothing and never needs event replay (heads are
   monotone; the latest one subsumes all prior).
3. **Keepalive**: a comment line (`: keepalive`) every 15s so intermediaries do not
   reap idle connections.
4. **Connection bound, its own, never the request gate's**: SSE connections are
   long-lived and must NOT occupy the 24-slot inflight admission gate (16 panels
   would starve the API). A separate `MAX_SSE_CLIENTS` (default 16, per hub) with a
   typed refusal beyond it: HTTP 503, `{"disposition": "sse_saturated",
   "max_clients": <n>, "message": <teach-text naming reconnect-with-backoff>}`.
   `/meta` advertises `max_sse_clients` and `sse_poll_interval_secs` (ADR-0016:
   advertised limits are contract).
5. **Restart interplay, stated honestly**: `autoharn service restart` SIGTERMs the
   hub; SSE connections die with it. That is correct behavior — the client's resume
   contract (item 2) makes reconnection lossless. The spec adds NOTHING to the
   restart path; say so in the route's own docstring so nobody "improves" it into a
   drain exception.
6. **Per-deployment isolation**: a subscriber to `/d/A/events` learns nothing about
   deployment B — the watcher and head are per-deployment, same as every other route
   under the multiplex.

## 2. What this spec does NOT do

No row payloads, no filtered subscriptions, no event kinds beyond `head`, no CORS
change (the panel's dev proxy already handles origin; production story unchanged and
unowned here), no kernel trigger, no change to `service restart`, no client-side
consumption built (the panel is the consumer; our CLI tools never call this).

## 3. Witness plan (scratch hub, both polarities, red first — new seen-red family, registered)

Scratch hub on a loopback port (NEVER 8433/8422), throwaway world. RED: /events on an
unknown deployment 404s with the standard teach-text; subscriber count at
MAX_SSE_CLIENTS+1 refused with `sse_saturated` (lower the cap via config in scratch to
witness cheaply); the stream emits NOTHING on a quiet ledger except keepalives
(witness ≥30s of silence). GREEN: subscribe with curl -N, write one ledger row through
the boundary, witness `event: head` within 2×poll interval carrying the new head;
reconnect with Last-Event-ID below head, witness the immediate catch-up event;
reconnect with Last-Event-ID == head, witness silence-plus-keepalives; two concurrent
subscribers both receive the same head event; a subscriber on deployment A receives
nothing when only B advances; kill the hub mid-stream (scratch), witness the client
sees clean EOF. Existing routes byte-identical (spot-diff /health, /meta minus the two
new advertised fields, one view read pre/post). Inflight gate untouched: saturate SSE
to its cap and witness an ordinary GET still admitted. Full gates clean.

## 4. Closure statement (ADR-0000 Rule 2(a))

Quantification universe: the ways a push signal could disturb the existing contract —
an existing route changing shape (none touched; witnessed byte-identical), the
admission gate starved by long-lived connections (separate bound, witnessed
independent), an unbounded new surface (cap + advertised in /meta), a second data
contract (structurally excluded: head ids only), restart semantics (unchanged, resume
makes it lossless), cross-deployment leakage (per-deployment watchers). Not covered,
stated honestly: LISTEN/NOTIFY push (future delta, named slot); production CORS (not
this spec's problem, restated as unowned); the panel's client-side consumption
(theirs).

## License

Public Domain (The Unlicense).
