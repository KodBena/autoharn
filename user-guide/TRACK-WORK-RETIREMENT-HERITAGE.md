# TRACK-WORK-RETIREMENT-HERITAGE — what `bootstrap/track-work.sh` was, why it retired, and its modern equivalent

<!-- doc-attest-exempt: brand-new document, this build (2026-07-25, ledger row 1271, bootstrap/
track-work.sh retirement arc). No genuine fresh-context second reviewer was available inside this
single-agent build session to run ADR-0017's real A:B:C loop (B requires a separate invocation
with no access to this session's own context -- not available to a lone builder). Flagged
honestly rather than silently bypassed or falsely marked mechanical -- this arc is bootstrap-tier
with strengthened review following. Removal condition: strike this marker and run the real A:B:C
loop during that follow-on review, or the next time this file is touched for content. -->

Audience: orchestrator (+secondary: maintainer) — this document records what
`bootstrap/track-work.sh` was, why its serviceless shape retired, and the exact modern
invocation for whoever next configures a standing work tracker, or wonders why a script BACKLOG/
design docs once pointed at now exits 1.

## What `bootstrap/track-work.sh` was

Born 2026-07-11 under the maintainer's own commission (his framing, near-verbatim, quoted in
[`user-guide/USER-WORK-STATUS-OFFERING.md`](USER-WORK-STATUS-OFFERING.md), the closure record for
what that document calls "the omega work-status litigation" — a question this project had
re-opened and re-closed at least three times without shipping an answer). Its founding act is
commit `4316a87` (`bootstrap/track-work.sh` + its own closure doc — `git show 4316a87` from this
checkout). The
offering it shipped: **any directory**, not just an autoharn-governed world, gets a standing,
indefinite-lifetime, Postgres-backed work tracker in one command — applying this repo's kernel
lineage (capped, at the time, at `s25-commission-kind.sql` — the newest delta that existed the
day the script was written, not a deliberate ceiling), writing `deployment.json` + that
deployment's own `keys/`, registering the three standard principals, and wiring the seven
operator verbs as live shims — deliberately **without** any hooks, governance preamble, or stamp
secret. Its own header comment named the distinction it existed to keep honest, verbatim:

> A STANDING deployment ... is explicitly OUTSIDE that regime: it has NO run number, NO "settles
> into dust" event, and NO defined end ... WHY NO HOOKS ARE WIRED (deliberate, not an oversight —
> say this loudly, in the output too): a standing project is not a governed world.

This is the phrase this retirement preserves verbatim (see "What survives, unchanged" below) —
it was never about the boundary or the shim mechanism; it was about hooks and governance.

track-work.sh's own known, self-disclosed gap (flagged loudly in its own header comment, never
silently routed around) was `legacy/led`: a standing tracker runs no boundary service "by
design," so when `legacy-led.tmpl` (the direct-psql original) was deleted outright by
[`design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md`](../vestigial_documentation/design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md)'s
retirement act, a track-work.sh-scaffolded deployment was left with **no working `led` verb at
all** — `./led` refused by the script's own no-boundary design, and `./legacy/led` execed a file
that no longer existed. The script's own comment named this a flagged, unresolved gap requiring a
maintainer decision — "does 'standing, not world' preclude a boundary, or was that distinction
always about hooks/run-linearity/stamp-secrets, never about the HTTP layer?" — outside the scope
of whichever pass wrote that comment.

## Why its serviceless shape retired

The maintainer's ruling closing that exact question (ledger row 1271, 2026-07-25, quoted here
verbatim because the reasoning matters more than a paraphrase):

> Of course ./autoharn is the one and only interface to autoharn ... I'm not in the game for
> serving stone-aged relics ... [after the need-vs-surface distinction was untangled: the work
> ledger itself is fully served through the boundary; only track-work.sh's no-service-by-design
> scaffolder is the relic, its founding assumption dissolved by ensure-running] ... We should
> then include a deployment template for such minimalistic deployments that they can hydrate,
> which would mirror the semantics of track-work.sh, if only to document what was once there and
> what it would look like in the modern world.

The dissolving fact: `serving/ensure_running.py`'s `ensure_running_or_leave_unreachable` — wired
into every served shim template (`led.tmpl`, `pickup.tmpl`, `distance-to-clean.tmpl`,
`asof-export.tmpl`) since the umbrella-CLI build — spawns the boundary as a detached child on a
deployment's **first** call, automatically, if `deployment.json` carries `boundary_url` +
`boundary_deployment` and a `boundary-multiplex.toml` sits beside it. This is what dissolved
track-work.sh's own "a standing tracker runs no boundary service by design" rationale: that
rationale was sound in 2026-07-11's world, where standing up a boundary meant a hand-launched,
manually-managed daemon a lightweight work tracker had no business requiring — but ensure-running
means the boundary is no longer a thing an operator stands up by hand at all; it is a thing that
appears the moment it is needed and needs no standing daemon. The service-vs-no-service tension
track-work.sh's own header comment agonized over was never really about whether a standing
tracker *should* have a boundary — it was about whether standing one up was worth the ceremony.
Ensure-running removed the ceremony, so the tension dissolved rather than resolved.

## The modern equivalent

```sh
bootstrap/new-project.sh <project-dir> --profile tracker --name <name> --db <db> --host <host> \
    [--schema <schema>] [--kern <kern>] [--role <role>] [--force]
cd <project-dir>
./autoharn led work open first-item "Describe the first thing to track"   # boundary auto-spawns
./autoharn pickup
```

Point for point, what changed and what survived:

| track-work.sh (2026-07-11) | `--profile tracker` (2026-07-25) |
|---|---|
| Kernel lineage capped at `s25-commission-kind.sql` (the era's own head, not a deliberate ceiling) | **Full current kernel lineage** (whatever `s${LINEAGE_HEAD}` is as of the run — the SAME apply chain `--new-world` uses, ADR-0012 P1: one birth sequence, not two) |
| Seven hand-listed operator verbs | `SHIM_VERBS_ALL` from `bootstrap/shim-verbs.sh` — never a second hand list |
| No boundary at all (the flagged gap); `legacy/led` a dead-end teaching-refusal stub with no working recovery | Boundary configured (a free port, `boundary-multiplex.toml`) but **not started** at scaffold time — `ensure_running_or_leave_unreachable` spawns it as a detached child on the first `./led`/`./pickup`/etc call |
| No stamp secret provisioned (deliberate: nothing would read it) | A stamp secret **is** provisioned (the same shared birth-sequence code path `--new-world` uses applies it too) — inert, not harmful, exactly the kernel's own "apply the full chain, dormant subsystems included" rationale, generalized here to the stamp secret specifically. Rows remain UNSTAMPED regardless (nothing reads the secret absent hooks) |
| `keys/`, `attestations/`, the three standard principals | Unchanged |
| **NO hooks, NO governance preamble** — "a standing project is not a governed world" | **Unchanged, verbatim** — this is the one distinction that survives untouched. `--profile tracker` writes no `.claude/settings.json`, no `governed_files.json`, no `apparatus.json`, no `HOOKS.md`, no root `CLAUDE.md`, no portable-ADR LAW section |

The one phrase this retirement was built to keep honest — **"a standing project is not a governed
world"** — is track-work.sh's own words, and it survives in `--profile tracker`'s own scaffold
output unchanged. What retired was the serviceless boundary shape that phrase never actually
required.

## Related

- [`bootstrap/new-project.sh`](../bootstrap/new-project.sh) — the `--profile tracker` mode itself;
  its own header comment carries the full usage contract.
- [`bootstrap/track-work.sh`](../bootstrap/track-work.sh) — now a one-line teaching-refusal stub
  (this retirement's act); `git log -p --follow` on this path recovers the original in full.
- [`user-guide/USER-WORK-STATUS-OFFERING.md`](USER-WORK-STATUS-OFFERING.md) — the founding closure
  record this heritage doc supersedes as the *current* operator-facing pointer (carries a dated
  closure note forwarding here, added by this same retirement).
- `serving/ensure_running.py` — the mechanism that dissolved track-work.sh's own no-boundary
  rationale.
- ledger row 1271 — the maintainer ruling this retirement discharges, quoted above in full.
