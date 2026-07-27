# FABLE-SERVICE-DRAIN-RESTART-SPEC — `autoharn service restart`: a drained, witnessed hub handover

<!-- doc-attest-exempt: Fable-authored spec 2026-07-27, maintainer-ratified the same day
(work item boundary-hub-restart-robustness, row 1553 option A; ratification row 1557 item 2,
"as you suggest on all outstanding decisions"). The A:B:C loop runs on the build, not the
proposal text. Removal condition: superseded by the build's merge record. -->
<!-- design-currency: status=ratified depends-on=FABLE-AUTOHARN-UMBRELLA-CLI-SPEC.md -->

One new subcommand on the existing control plane (`libexec/autoharn-service`, shared logic
in `serving/ensure_running.py` — ADR-0012 P1, extend the one home, never a second copy):
`autoharn service restart`. Motivation, witnessed at the autoharn2 rebirth planning: the
hub reads `boundary-multiplex.toml` ONCE at startup (a deliberately closed enumeration —
that posture is NOT changed by this spec; hot-reload was considered and REJECTED at
ratification, row 1553's option C), so adding/retiring a world's deployment today means a
hand-timed stop/start that blips every served world for an unwitnessed interval. `restart`
makes that interval bounded, drained, and witnessed.

## 1. Semantics, in order, each leg loud

1. **Own-process check (the `stop` discipline, verbatim posture):** refuse — teaching
   text, nothing signaled — when there is no pidfile, or the pidfile's pid is not a
   `serving.boundary_service` process per `/proc/<pid>/cmdline` (PID reuse). An adopted
   or hand-started hub is not ours to restart; the refusal names the alternative (stop
   it where it was started, or start fresh here).
2. **Config pre-validation, BEFORE any signal:** load the current
   `boundary-multiplex.toml` through `serving/boundary_multiplex_config.py`'s own
   `load_multiplex_config` (the one shape authority). An invalid config refuses HERE —
   the old process keeps serving; a restart must never trade a working hub for a
   config-parse crash loop. Print the deployment roster the new process WILL serve.
3. **Drain:** SIGTERM the old process (uvicorn's own graceful path: listen socket
   closes, in-flight requests complete). Wait bounded (default 30s, `--drain-timeout`
   overridable); on timeout REFUSE loudly with the pid still running — never escalate
   to SIGKILL unasked (`--force-kill` is the operator's explicit escalation, printed
   as such).
4. **Spawn:** the existing start path verbatim (bind-as-lock, child writes the
   pidfile after its own synchronous bind — no new race logic; reuse
   `ensure_running`'s structural resolution).
5. **Handover deviation from `start`'s adopt-is-success (stated, deliberate):** if the
   bind race is lost to a FOREIGN process in the gap, `restart` REFUSES loudly naming
   the squatter instead of adopting — the operator's intent was "my new config is now
   serving," and an adopted stranger structurally defeats that intent even when it
   answers /health. (row 1165's adopt ruling governs `start`; `restart`'s contract is
   stricter by its own purpose — this paragraph is the disclosed divergence.)
6. **Witness before reporting:** probe `/d/{name}/health` for EVERY deployment in the
   newly loaded config, version-compatibly (the existing probe helper — never bare
   200-counting, the SEVERE-4 lesson). Report per deployment: `SERVING <name>` or the
   probe's own failure; exit nonzero if any deployment fails, with the hub left
   running (a partially-healthy hub is reported, not rolled back — rollback is the
   operator re-editing the config and running `restart` again; say so in the output).
7. One-line summary with the measured gap: `restart: drained <pid> in X.Xs, new pid
   <pid>, unserved window ~Y.Ys, N/N deployments healthy`.

## 2. What this spec does NOT do

No hot-reload, no SIGHUP handler, no admin/mutation endpoint on the service itself, no
change to `serving/boundary_service.py`'s startup-fixed deployment enumeration or
per-deployment bound computation. The service process stays ignorant of `restart`'s
existence; everything lives in the control plane. `status`/`start`/`stop` behavior is
byte-identical.

## 3. Witness plan (scratch, both polarities, red first — new seen-red family, registered)

All on a scratch hub: throwaway world(s) on 192.168.122.1, dynamically-chosen loopback
port, its own scratch toml/pidfile under a temp dir — NEVER port 8433/8422, never this
repo's own boundary-multiplex.toml or pidfile. RED first: restart with no pidfile
refuses, nothing signaled (witness the old process undisturbed); restart with a
pidfile naming a reused/wrong pid refuses; restart with an INVALID toml refuses at
leg 2 with the old process still serving (probe it after); bind-race-lost-to-foreign
leg: a squatter bound during the gap → refusal naming it (constructible: stop, bind a
dummy socket, run restart). GREEN: edit the scratch toml to ADD a second deployment,
`restart`, witness both `/d/{name}/health` probes pass and the summary line's
measured gap; a request issued to the old process just before restart completes
successfully (drain witnessed) — if a genuinely in-flight-across-SIGTERM request
proves impractical to construct against the real service, witness the graceful-
shutdown log line + clean exit instead and mark the stronger leg UNEXERCISED with
that stated blocker, never a silent pass. `--drain-timeout` exercised with a tiny
value against a healthy hub (completes under it). Roster/usage text updated
(`autoharn --help`, `service --help`, the umbrella parity fixture). Full gates clean.

## 4. Closure statement (ADR-0000 Rule 2(a))

Quantification universe: the ways the operator's "my edited config is now serving"
intent can silently fail across a hub handover — old process not ours (leg 1), new
config invalid (leg 2), old process never drains (leg 3), race lost to a stranger
(leg 5), new process up but a deployment unhealthy (leg 6) — each mapped to a loud,
typed leg above. Not covered, stated honestly: zero-downtime overlap (SO_REUSEPORT,
row 1553's option B) is deliberately not built until the measured gap from leg 7
shows it matters; a hub started by hand outside this control plane stays outside it.

## License

Public Domain (The Unlicense).
