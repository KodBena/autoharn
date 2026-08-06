subject: f8af7d7e,c65b21bf
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

Two new OPTIONAL `boundary-multiplex.toml` top-level keys, same "sugar over the loader" idiom
`max_sse_clients` already established:

- `max_inflight_per_deployment` (int, default **32**) — replaces the old
  `max(4, 24 // len(deployments))` formula that produced an unprovenanced 6 on a busy hub. The
  `deployment_saturated` teach-text now names the configured value and where to change it.
- `max_inflight_kernel_calls` (int, default **64**, raised from the old hardcoded 24) — the
  global admission bound; resolved once at startup via `configure_max_inflight_kernel_calls()`.

**What a restarting orchestrator needs to know — the starvation-note polarity.** Because the new
per-deployment default (32) exceeds what the OLD global cap (24) would have allowed, the
per-deployment sub-bound could no longer bind before the global one did — flagged loudly by a
startup diagnostic, `inflight_per_deployment_starvation_note`, whenever the resolved
per-deployment value is not strictly less than the resolved global value. At the SHIPPED
defaults (32 < 64) the note is silent; set `max_inflight_kernel_calls` below 32 (or raise
`max_inflight_per_deployment` above it) and the note fires, naming the tradeoff and how to
restore sibling isolation.

**The structural threadpool derivation.** Raising the global default to 64 inverted a second,
previously-implicit invariant: the old 24 sat safely under anyio's own default ASGI threadpool
`CapacityLimiter` (40 tokens) by accident (two independent literals happening to land in the
right order, not a designed guarantee). Rather than re-tuning another magic number, the ASGI
threadpool's own `CapacityLimiter` is now sized STRUCTURALLY at ASGI startup (`_configure_
threadpool_capacity`, a `lifespan` handler — required because anyio's default limiter is bound
to the running event loop and cannot be configured from `main()`'s synchronous pre-loop setup)
from the RESOLVED `max_inflight_kernel_calls` plus a fixed, named `NON_KERNEL_THREADPOOL_
HEADROOM=16` (the exact margin the original 24-under-40 pairing carried). This is a derivation,
not a re-guess: the threadpool capacity always tracks whatever the kernel cap is actually
configured to, on any world, at any value.

Both new keys are wired into the setup TUI as of commit `4440fb34` (item
`setup-tui-session-currency`, same wave) — see `./autoharn setup-schema` for the current schema
shape.
