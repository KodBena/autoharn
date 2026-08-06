# Boundary multiplexing and the CLI rebase onto it — build basis

<!-- doc-attest-exempt: draft spec awaiting maintainer ratification; A:B:C attestation
     rides the ratified revision, not the draft -->

**Status: DRAFT, Fable-authored 2026-07-18, NOT ratified. Build doubly gated: (1) the
maintainer's sign-off on this spec, (2) the boundary-service review loop reaching its
fixpoint (the loop reviews `serving/` at pinned commits; building this before the loop
closes would swap the review target mid-pass).** (Header corrected 2026-07-28, autoharn3
design-drift-triage sweep, ledger row 90: "NOT ratified" / "build doubly gated" stood
stale — both gates cleared and the build shipped and merged: `serving/boundary_service.py`
implements the full `/d/{deployment}` discriminator (route table grown to fourteen routes)
and `serving/boundary_multiplex_config.py` exists; the CLI rebase (§5) is live (`led`/
`pickup`/`asof-export`/`distance-to-clean` all run through the boundary); the §6 `./legacy/`
plan was itself further superseded by FABLE-LEGACY-LED-RETIREMENT-SPEC.md (`./legacy/led`
is now a one-line teaching-refusal stub, `legacy-led.tmpl` deleted outright). Historical
prose below kept verbatim.) Authored now rather than later for a
stated reason: the maintainer named the direction on 2026-07-18 ("we'll want to move the
CLI verbs to run on top of the FastAPI server (placing the old ones in ./legacy) and make
sure that the FastAPI server can service multiple deployments (essentially a JSON/TOML
config that configures for multiplexing) since I don't want to have to start one FastAPI
server for every deployment"), and serving/-semantics specs are Fable-authored under the
standing orchestration contract — so the spec exists before the authoring window closes,
and the build waits for its gates.

## 1. What this is

Two coupled changes, one spec because the second is only safe on top of the first:

- **Multiplexing:** one boundary-service process serves N deployments, selected by a
  closed path discriminator, configured by one operator-authored config file. No
  per-deployment server processes.
- **CLI rebase:** the scaffolded operator verbs (`led`, `judge`, `pickup`,
  `asof-export`, …) become thin clients of the boundary service instead of direct psql
  callers. The direct-psql originals move to `./legacy/` inside the deployment, intact
  and runnable, clearly marked.

Non-goals, named so they are not read as accidental omissions: no authentication layer
beyond today's trust model (localhost bind, OS-user trust — unchanged, and its absence
stays a named property, not an oversight); no change to kernel semantics or the s43
write boundary; no crypto/signing anywhere (standing ruling); no live-world migration
of existing deployments (§6).

## 2. Deployment discriminator (closed, config-enumerated)

Every route gains a leading `/d/{deployment}` segment: `/d/{deployment}/health`,
`/d/{deployment}/write/ledger`, etc. The `{deployment}` value is valid iff it is a key
of the loaded config — a closed enumeration fixed at startup. Anything else refuses
typed 404 `{"disposition": "unknown_deployment", "known": [<the config's keys>],
"message": <teach-text>}`. No unprefixed routes survive in a multiplex-scaffolded
world: the route table stays closed and single-shaped, not dual-dialect. (A config
with exactly one deployment is the degenerate case and is the expected common one;
the discriminator is still mandatory — one shape, not two.)

Deployment names: `[a-z0-9-]{1,64}`, refused at config load otherwise. The name is an
operator label, never interpolated into SQL — it selects a config entry, and the entry
carries the connection facts.

## 3. The config file

TOML (comments matter in an operator-authored file; JSON stays acceptable to the
maintainer per his words — the build implements TOML and the choice is his to override
at ratification). One file, passed explicitly (`--config <path>`); no search-path
magic, no defaults file. Shape:

```toml
# boundary-multiplex.toml
[deployments.autoharn1]
pghost = "192.168.122.1"
pgdatabase = "autoharn1"
pguser = "led_writer"        # the same role split the single-deployment service uses

[deployments.omega]
pghost = "192.168.122.1"
pgdatabase = "omega"
pguser = "led_writer"
```

Load semantics, per ADR-0000/ADR-0002: the WHOLE file validates before the socket
binds — unknown keys anywhere refuse startup by name; a missing required key refuses by
name; zero deployments refuses. A config error after startup is impossible by
construction (the file is read once; no reload endpoint — restart is the reload, and a
restart is cheap because the server is stateless between requests). Per-deployment
reachability is NOT probed at startup: an unreachable deployment's kernel is a
per-request typed 503 `infra_failure` on that deployment's routes, exactly as today —
startup validates the config's shape, not the world's health.

## 4. What multiplexing must preserve (the A1–A10 closure, per deployment)

Every axis the amendment history closed holds per deployment, and the witness suite
re-runs against the multiplexed shape before this ships:

- Route closure: the route table is the per-deployment table crossed with the config's
  key set; `/d/{unknown}/...` is the only new refusal shape.
- Size/time/parse/value/id-domain/exit-code axes: unchanged mechanisms, now keyed by
  the selected deployment's connection facts.
- Concurrency admission: `MAX_INFLIGHT_KERNEL_CALLS` stays the GLOBAL bound (it
  protects the shared threadpool, which is process-wide), and gains a per-deployment
  sub-bound `MAX_INFLIGHT_PER_DEPLOYMENT` (default: `max(4,
  MAX_INFLIGHT_KERNEL_CALLS // len(deployments))`, computed at startup, printed at
  startup) so one deployment's stalled kernel cannot occupy the whole global bound and
  starve its siblings. Both refusals are typed 503; the body names WHICH bound
  (`server_saturated` vs `deployment_saturated`) — one condition per label, per the
  A6/A8 label-honesty rulings.
- Audit: `audit_served.py` gains `--deployment <name>`; its per-deployment contract is
  otherwise unchanged.

## 5. The CLI rebase

The scaffolded verbs become clients of the boundary: same argv surface, same typed
verdicts, same exit codes — the transport under them changes from psql to HTTP against
the configured boundary URL + the deployment's own name. Facts the shim needs (base
URL, deployment name) live in the deployment's existing `deployment.json`, two new
keys, refused-if-absent by the new shims.

- **Read verbs** (`pickup`, `asof-export read`, `led` read subcommands, …): pure
  clients of the read routes, including their pagination discipline.
- **Write verbs** (`led` write subcommands): clients of the four write routes; the s43
  typed `write_verdict` passes through byte-faithfully. The boundary's own refusals
  (422/413/408/503 shapes) surface as the shim's stderr with their teach-text and a
  distinct nonzero exit code — a boundary refusal must never be dressed as a kernel
  refusal (exit-code fidelity, A4's ruling, now visible at the shim layer).
- **`./legacy/`**: the direct-psql originals move there whole, executable, with a
  one-line header naming why they exist (operator recovery when the boundary is down —
  the recovery-mode concern already on the ledger) and that the boundary path is the
  serviced one. Nothing silently loses the old capability; it is demoted by placement,
  not deleted. Whether `./legacy/` eventually retires is a later maintainer call.
- **What does NOT rebase:** `judge` (drives clingo + differential against the world,
  not a ledger client in the boundary's sense) and the bootstrap scaffolding itself
  keep their current transport; enumerated here so the rebase's scope is closed, not
  "all verbs, surely".

## 6. Migration posture (runs are linear — no exception here)

New worlds get the new shims + `./legacy/` via the scaffold, from the commit this
lands. Existing deployments are dust-and-settled per the standing ruling: they keep
their direct-psql verbs, unpatched; an operator who wants the new shape re-scaffolds.
No refresh verb, no in-place migration, no dual-mode shims.

## 7. Witnesses (sketch — the build's fixture pass binds these)

- **WM1** two-deployment config, a write to each: each lands in ITS OWN world's ledger
  and not the sibling's (the cross-contamination probe, both directions).
- **WM2** `/d/{unknown}/health` → typed 404 `unknown_deployment` naming the known set.
- **WM3** config with an unknown key / missing key / zero deployments → startup refusal
  naming the defect; socket never binds.
- **WM4** one deployment's kernel stalled: its routes exhaust ITS sub-bound → typed 503
  `deployment_saturated`; the sibling deployment's routes and `/health` stay prompt
  (measured, per the A9 method).
- **WM5** a rebased shim's kernel-refused write: stderr and exit code byte-faithful to
  the s43 verdict; a boundary-refused write distinguishably typed.
- **WM6** `./legacy/` verb runs green against its world after the rebase.

## 8. Open questions for ratification (answers change the build)

1. TOML confirmed, or JSON preferred?
2. Path discriminator `/d/{name}` confirmed, or a different closed selector?
3. Does the single mandatory discriminator (even for one deployment) get his sign-off?
   It is the closed-shape choice, but it breaks URL compatibility with the current
   single-deployment service (which nothing external depends on yet, which is why now
   is the cheap moment).
4. Is `./legacy/` retirement a decision he wants scheduled, or left open?

## Amendment — 2026-08-06: `MAX_INFLIGHT_PER_DEPLOYMENT` is deployment-configurable, default 32

*(Dated append per ADR-0005 Rule 8 / ADR-0020's posture — additive only, the ratified §4 body
above stands verbatim and is not rewritten. Provenance: missive row 1011 (experience4's
commissioner, also this project's maintainer) and decision row 1068 (schedule-execution
ruling, dispatching this item as "A1"); build in design/BRIEF-A1-INFLIGHT-CAP-AND-WOULD-PRODUCE-
2026-08-04.md.)*

§4's original text names the per-deployment sub-bound's default as `max(4,
MAX_INFLIGHT_KERNEL_CALLS // len(deployments))`. In real multi-deployment operation this
formula produced `MAX_INFLIGHT_PER_DEPLOYMENT=6` (four deployments, 24 // 4) — witnessed
(ledger row 1994) making one live operator session plus one parallel test/agent consumer
against a single deployment trip immediate 503 `deployment_saturated` refusals, which
cascaded into 77 wholesale e2e failures elsewhere. The commissioner's own words: "its
provenance is unclear to the commissioner ('I don't know how that got there')." Read
plainly: the formula is not undocumented, but the specific FLOOR/default it was left to
produce was never a deliberately-chosen concurrency target for real operation — it was a
mechanical division with no operational sizing behind it, and it bit exactly the "one
human plus one automated consumer" shape this project's own worlds actually see.

**The fix, as built.** `MAX_INFLIGHT_PER_DEPLOYMENT` is now an OPTIONAL top-level
`boundary-multiplex.toml` key, `max_inflight_per_deployment` — same whole-file
validation-before-bind discipline every other tunable in this file already has
(`serving/boundary_multiplex_config.py`'s `load_multiplex_config_with_inflight_limit`), a
positive integer bounded `[1, 10_000]` (a sanity ceiling against a typo, not operational
advice). Its default is **32** (row 1068's own choice, within the commissioner's stated
24-64 band), superseding the `len(deployments)`-derived formula above entirely — the
default no longer varies with deployment count. The per-deployment `deployment_saturated`
refusal's teach-text names the configured value and where to change it
(`serving/boundary_service.py`'s `DeploymentCallSaturated` message).

**A structural consequence, named honestly, not silently absorbed.** §4's own rationale for
this sub-bound is "so one deployment's stalled kernel cannot occupy the whole global bound
and starve its siblings" — that protection depends on the sub-bound being SMALLER than the
global `MAX_INFLIGHT_KERNEL_CALLS` (24, unchanged by this amendment). The new default, 32,
is LARGER than 24: at the shipped default, the per-deployment gate can never bind before
the global one does, so a single deployment's own burst CAN occupy the entire global
admission pool — the sibling-starvation protection this sub-bound existed for does not
hold at the default configuration. This is a deliberate tradeoff (headroom for the common
single-or-few-deployment case over sibling isolation under a stalled deployment), not an
oversight: `serving/boundary_service.py`'s `inflight_per_deployment_starvation_note` prints
a loud startup diagnostic whenever the resolved value is `>= MAX_INFLIGHT_KERNEL_CALLS`,
naming the consequence and that setting `max_inflight_per_deployment` below 24 restores
sibling isolation. Nothing is silently clamped: an operator's configured value (or the
shipped default) is honored at face value and the tradeoff is surfaced, not hidden
(ADR-0002 fail-loud over a silent behavior-altering override). Left for a later, separate
maintainer call: whether `MAX_INFLIGHT_KERNEL_CALLS` itself should also rise — out of this
item's scope (design/BRIEF-A1-INFLIGHT-CAP-AND-WOULD-PRODUCE-2026-08-04.md's own named
surface is the per-deployment cap only).

## Amendment — 2026-08-06: `MAX_INFLIGHT_KERNEL_CALLS` raised to 64, deployment-configurable

*(Dated append per ADR-0005 Rule 8 / ADR-0020's posture — additive only, the ratified §4 body
and the amendment immediately above stand verbatim and are not rewritten. Provenance: the A1
builder's own flagged finding (commit f8af7d7e, report banked) that the shipped
`MAX_INFLIGHT_PER_DEPLOYMENT` default (32) exceeds the then-global `MAX_INFLIGHT_KERNEL_CALLS`
(24), breaking the sibling-starvation sub-bound relation the amendment immediately above names
honestly; maintainer ruling 2026-08-06, ledger row 1113: "yes, the global rises." Build in
design/BRIEF-GLOBAL-INFLIGHT-CAP-2026-08-06.md, ledger rows 1113/1115.)*

**The fix, as built.** `MAX_INFLIGHT_KERNEL_CALLS` — until now a fixed module-level Python
constant, `24` — is now ALSO an OPTIONAL top-level `boundary-multiplex.toml` key,
`max_inflight_kernel_calls`, resolved through the SAME `serving/boundary_multiplex_config.py`
loader family the per-deployment key already uses
(`load_multiplex_config_with_inflight_limit`, extended rather than duplicated), same
whole-file validation-before-bind discipline, a positive integer bounded `[1, 10_000]` (a
sanity ceiling against a typo, matching every other tunable's own ceiling shape in this file
— not operational advice). Its default is **64** — the orchestrator's stated choice, 2x the
per-deployment default (32), restoring `MAX_INFLIGHT_PER_DEPLOYMENT < MAX_INFLIGHT_KERNEL_CALLS`
at shipped defaults (the relation the amendment above disclosed as broken) with headroom for
two busy deployments to each run near their own per-deployment ceiling concurrently without
touching the global one. `serving/boundary_service.py`'s module-level `MAX_INFLIGHT_KERNEL_CALLS`
and its `_KERNEL_CALL_SEMAPHORE` are now resolved and bound ONCE at process startup (via the new
`configure_max_inflight_kernel_calls`, the same construction-time-defense-in-depth pattern
`configure_sse_poll_interval`/`configure_max_sse_clients` already establish) rather than fixed
at import time — every call site downstream (`_psql`'s admission gate, `server_saturated`'s
typed body, the startup banner, the diagnostic-logging `STARTUP` event) reads the resolved
value, never a stale import-time literal. The `KernelCallSaturated` refusal's teach-text now
names the configured value and where to change it (`boundary-multiplex.toml`'s
`max_inflight_kernel_calls` key, default 64), mirroring `DeploymentCallSaturated`'s own
established wording.

**The starvation relation, re-checked, not re-derived.** `inflight_per_deployment_starvation_
note` (unchanged in shape) already compared `per_dep_limit` against `MAX_INFLIGHT_KERNEL_CALLS`
as a module-global read at call time, never a captured literal — so with BOTH keys now
independently configurable, the check is, by construction, always against the RESOLVED values
of both, not a hardcoded relation. Witnessed both polarities (`seen-red/boundary-multiplex/
run_fixtures.py`, WM-INFLIGHT-DEFAULT and WM-INFLIGHT-FIRES): at shipped defaults (32 < 64) the
note is correctly ABSENT — the sibling-starvation protection genuinely holds again, closing the
gap the amendment above disclosed; an explicit config with the per-deployment bound at or above
the global one (either axis moved) still correctly FIRES the note.

**A structural consequence, named honestly, then RETIRED not re-tuned (CLAUDE.md's
hazard-in-reach obligation; ledger row 1141, orchestrator ruling ledgered rows 1147/1148).**
`MAX_INFLIGHT_KERNEL_CALLS`'s original value, 24, was chosen deliberately UNDER the ASGI
threadpool's own default concurrency (anyio's `CapacityLimiter`, 40 tokens on the review host —
see this file's own §4 "Concurrency admission" and `serving/boundary_service.py`'s ADMISSION
AXIS docstring) precisely so kernel-call occupancy alone could never starve non-kernel work or
`/health`'s own thread dispatch. That relation was, on inspection, a MAGIC-NUMBER RACE — two
independently-literal constants (this service's own 24, anyio's own default-40 limiter) that
happened to satisfy the invariant only because neither had yet been raised past the other; the
new shipped default, 64, broke it numerically (64 > 40), reintroducing the unbounded-queueing
pathology A9's own iteration-7 measurements were built to close (this file's §4, "80 -> 5.3s,
200 -> 27.7s, 600 -> no answer in 180s") the moment sustained load approached the new default.

**The fix, as built (still this item, brought into scope by orchestrator ruling on the row-1141
flag).** The relation is now STRUCTURAL, not numeric: `serving/boundary_service.py`'s ASGI
threadpool — anyio's own default thread `CapacityLimiter` — is sized at ASGI startup from the
RESOLVED `MAX_INFLIGHT_KERNEL_CALLS` plus a fixed, named headroom,
`NON_KERNEL_THREADPOOL_HEADROOM = 16` (the orchestrator's stated judgment: the EXACT margin the
original 24-under-40 pairing already carried, preserved as a deliberate constant rather than an
emergent fact of two independent literals — sized for the same purpose the original margin
served, comfortably covering this service's own small, enumerable non-kernel-call surface:
`/health` and any future non-`_psql`-gated route). `resolve_threadpool_capacity(n) = n +
NON_KERNEL_THREADPOOL_HEADROOM` is the ONE derivation (ADR-0012 P1) both the synchronous startup
banner/diagnostic (`main()`, which runs before any ASGI event loop exists) and the actual
APPLICATION read — the latter via `create_app`'s own `lifespan` context manager
(`_configure_threadpool_capacity`), the one place FastAPI guarantees code runs INSIDE the
running event loop before the app ever accepts a request, which is required because
`anyio.to_thread.current_default_thread_limiter()` is bound to whichever loop is currently
running and cannot be configured from synchronous pre-loop setup. The relation now holds by
CONSTRUCTION for every value `MAX_INFLIGHT_KERNEL_CALLS` can ever resolve to — never again by
two constants staying coincidentally in the right order. Witnessed both polarities: the resolved
`threadpool_capacity` is named in both the stderr banner and the diagnostic `startup` event at
the shipped default (64 -> 80) and at an explicit override (16 -> 32); and, since the limiter has
no HTTP-visible surface, a direct in-process leg (`seen-red/boundary-multiplex/run_fixtures.py`,
WM-THREADPOOL-STRUCTURAL) drives `create_app`'s own `lifespan` context manager directly and
reads `anyio.to_thread.current_default_thread_limiter().total_tokens` back, confirming the value
is genuinely APPLIED (64 -> 80, 10 -> 26), not merely computed and printed.
