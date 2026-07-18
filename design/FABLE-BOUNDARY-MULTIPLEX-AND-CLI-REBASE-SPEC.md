# Boundary multiplexing and the CLI rebase onto it — build basis

<!-- doc-attest-exempt: draft spec awaiting maintainer ratification; A:B:C attestation
     rides the ratified revision, not the draft -->

**Status: DRAFT, Fable-authored 2026-07-18, NOT ratified. Build doubly gated: (1) the
maintainer's sign-off on this spec, (2) the boundary-service review loop reaching its
fixpoint (the loop reviews `serving/` at pinned commits; building this before the loop
closes would swap the review target mid-pass).** Authored now rather than later for a
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
