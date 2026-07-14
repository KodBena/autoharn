# Deployment pinning — decoupling a scaffolded deployment's operator verbs from autoharn's live working checkout

Audience: orchestrator and maintainer. This document answers one question: **how does a
scaffolded autoharn deployment (an "adopter" — a project that consumes autoharn's `led`,
`judge`, `pickup`, and the other operator verbs) stop having its behavior change the instant
someone merges a change into autoharn's own working branch?** It is a design note, not a
built change: nothing in `bootstrap/`, `hooks/`, or any scaffolded deployment is edited by
this document. It answers the tracker item `deployment-live-exec-coupling`
(work-item slug in this project's ledger, read via `./led`), approved for design work by the
maintainer on 2026-07-14 (ledger row 684, "go-ahead: ALL SIX Part-B items approved … deployment-live-exec-coupling
(build, composes with recovery-mode concern)"; the design-scoped ask is in the same day's row 686:
"schedule design note + migration path (submodule default, copy-at-scaffold fallback); build/merge
gated appropriately").

## The problem, stated plainly

When `bootstrap/new-project.sh` (this project calls it **the scaffold**) stands up a new
deployment, the operator verbs it writes into that deployment — `led`, `judge`, `pickup`, and
the rest — are **not** self-contained copies. They are thin shell shims that `exec` autoharn's
own template scripts (`bootstrap/templates/*.tmpl`) *live*, reading them out of whatever commit
autoharn's own working checkout happens to be on at the moment the shim runs. This is not an
oversight; it is a deliberate, dated ruling (`bootstrap/new-project.sh`'s own header comment,
"BACKLOG maintainer ruling 2026-07-11 'runs are strictly linear' disposition 6 'live verbs'"):
the verbs stopped being sed-substituted frozen copies specifically so that a template fix lands
in every already-scaffolded world instantly, matching how this project's own governance hooks
(the scripts that intercept a Claude Code tool call before it runs, e.g. the change gate and the
stamp injector — [`GLOSSARY.md#wired`](../GLOSSARY.md#wired)) already execute live out of the
`hooks/` directory per invocation, rather than a frozen per-world copy.

That ruling made sense for autoharn's own worlds (`run5`, `run7`, and the like) — throwaway
experiment habitats living inside the same checkout, expected to inherit fixes immediately, and
covered by the same session's own "runs are strictly linear" posture (a run's world is either
being actively worked in this checkout or is dust; there is no third state where staleness
matters). It does not hold for an **adopter**: a separate project, on a separate machine or a
separate clone, that scaffolded itself against autoharn once and has been running against it
ever since. For an adopter, "live" means: the moment anyone merges a change to autoharn's
working branch, every adopter's `led`/`judge`/`pickup` invocation changes behavior — mid-session,
whether or not that adopter is ready for it, whether or not anyone told its operator, and
whether or not the adopter's own deployment even still matches the schema/kernel/ledger shape
the new template assumes.

**~/ent is the motivating, witnessed case, not a hypothetical.** It is a real scaffolded
deployment consuming autoharn's live verbs exactly as described above, and it is the deployment
a recent merge to autoharn's `next` branch had to be held up and carefully staged around,
specifically because a live session was running there and an unstaged template change would
have reached it instantly. As of this note ~/ent is a broken installation, and — per the
maintainer's own 2026-07-14 framing (quoted in full in the companion note,
[`ORCH-RECOVERY-MODE-SIGNED.md`](ORCH-RECOVERY-MODE-SIGNED.md)) — it is *still* broken. This
design does not diagnose or fix ~/ent's brokenness (that is out of scope here, and ~/ent
carries a live session this project treats as strictly read-only); it takes ~/ent's situation
as the concrete evidence that the live-exec coupling is a real operational hazard for
deployments, not merely an abstract inelegance.

The maintainer's own framing of the fix (relayed verbatim in the source brief that opened this
tracker item, `design/MAINT-MAINTAINER-DECISION-BRIEF-2026-07-14.md` §B5): an adopter should
consume this project the way "responsible adults" do — at a pinned, deliberate version, the way
software libraries normally work. He named the standard mechanism himself: a **git submodule**,
a well-understood way for one project to depend on a specific, frozen snapshot of another,
upgraded only by an explicit, recorded act.

## Design: submodule-as-default

The default shape for a **new** adopter deployment: the deployment directory carries autoharn
as a **git submodule**, pinned at a specific commit SHA, rather than the scaffold writing shims
that `exec` a sibling checkout's live files by path. Concretely, relative to today's shape:

- **Today:** `led`/`judge`/`pickup`/etc. in a scaffolded world are shims that `exec` (or
  `source`) `bootstrap/templates/*.tmpl` resolved from wherever autoharn's own checkout lives on
  that machine (typically a path baked in at scaffold time, e.g. `~/w/vdc/1/autoharn`) — one
  shared, mutable tree, read fresh on every invocation.
- **Proposed:** the scaffold adds autoharn as a submodule at `<deployment>/.autoharn/`, pinned
  to the commit the scaffold ran from. The operator verb shims `exec` templates out of
  `<deployment>/.autoharn/bootstrap/templates/` — a path inside the *deployment's own* git tree,
  whose content is frozen at whatever commit the submodule pointer names, not wherever
  autoharn's separate working checkout happens to be at invocation time.
- **Upgrading** an adopter to a newer autoharn becomes the explicit, recorded act the maintainer
  asked for: `cd <deployment>/.autoharn && git fetch && git checkout <new-sha>`, followed by
  `git add .autoharn && git commit` in the deployment's own tree to record the new pin, and a
  `./led decision "upgrade: autoharn .autoharn submodule <old-sha> -> <new-sha>"` row so the
  ledger carries the fact. A deployment's operator verbs never change behavior except at this
  moment, and never as a side effect of someone else's unrelated merge.

This is the *default* shape because it gives the adopter the sharpest guarantee (byte-identical
templates, verifiable by the submodule's own pinned SHA, with `git` doing the pinning-integrity
work autoharn does not have to reinvent) at the lowest new-mechanism cost — no autoharn code
change is needed beyond the scaffold script itself; `git submodule` is standard tooling this
project already depends on being present.

## Fallback: copy-at-scaffold

Not every adopter's environment supports (or wants) a submodule — a deployment directory that is
not itself a git repository, an environment where submodule tooling is unavailable or
undesirable, or an adopter who explicitly wants a smaller footprint than a nested `.autoharn/`
checkout. For that case: the scaffold **copies** the rendered `bootstrap/templates/*.tmpl`
files into the deployment directory as ordinary, non-`exec`-live files at scaffold time — the
historical shape this project used before the 2026-07-11 "live verbs" ruling, restored
specifically for adopters (autoharn's own `run*` worlds keep the live-exec shape; that ruling
was correctly scoped to them and this design does not revisit it).

A copy-at-scaffold deployment upgrades by re-running (a to-be-written) `bootstrap/upgrade-project.sh`
against the deployment directory: it re-renders the current `bootstrap/templates/*.tmpl` set and
overwrites the deployment's copies, the same way `new-project.sh` writes them the first time,
recording the act with the same `./led decision "upgrade: …"` convention named above. This
gives the adopter the same "upgrade is an explicit act" property as the submodule path, at the
cost of losing git's own pin-integrity verification (a copy's provenance is only as good as the
ledger row recording when and from what commit it was copied — worth naming honestly rather than
glossing over).

**Which one a given adopter gets is a scaffold-time flag** (e.g. `--pin submodule` default,
`--pin copy` fallback), not a maintainer judgment call made once for the whole project — different
adopters have different constraints, and the scaffold should not force a choice that does not
fit an adopter's environment.

## Migration path for EXISTING deployments — ~/ent is the motivating case

A deployment scaffolded before this design exists (~/ent, and any other adopter scaffolded under
the current live-exec shape) is not automatically pinned by shipping this design — pinning a
running deployment is itself an act, and this section is that act's shape, stated in advance so
it is not improvised under pressure the day it is finally run.

1. **Freeze the deployment at its currently-running commit.** Determine the autoharn commit the
   deployment's shims currently resolve against (today: whatever commit the shared checkout path
   is on; recorded going forward at scaffold time once this design lands, per the "Buildable now"
   section below). This is the commit the deployment has actually been running — not the tip of
   any branch, and not a commit chosen for being "current" or "clean."
2. **Stand up the pin at that frozen commit.** For the submodule path: `git submodule add` at that
   exact SHA inside the deployment's own tree (or, if the deployment directory is not a git repo,
   the copy-at-scaffold fallback: copy the rendered templates from that exact commit). Either way,
   the migration does **not** silently upgrade the deployment to autoharn's current tip — it pins
   it to what it was already running, so the migration itself is not conflated with an upgrade.
3. **Verify the shims resolve to the pin, not the shared checkout.** Confirm (by path, or by a
   deliberate smoke invocation) that `led`/`judge`/`pickup` now `exec` the pinned copy. This step
   is what actually retires the coupling for that deployment — steps 1–2 without this verification
   would leave the shim pointed at the old live path by accident.
4. **Record the migration** with a `./led decision` row in **this** project's own ledger (the
   ledger a migration act should be visible in, per this project's standing self-application rule
   — CLAUDE.md, "Self-application"): `./led decision "migrate: <deployment-name> pinned to
   autoharn@<sha> (deployment-live-exec-coupling migration)"`. If the deployment carries its own
   ledger (every scaffolded deployment does, per its own `deployment.json` and Postgres schema —
   see the [`world` glossary entry](../GLOSSARY.md#world)), the migration is also worth a row
   there, in the deployment's own voice, so an operator reading *that* deployment's history sees
   the pin without cross-referencing autoharn's ledger.
5. **Any future upgrade for that deployment is now the explicit act** described in "submodule-as-
   default" or "copy-at-scaffold" above — never a side effect of an autoharn merge again.

This migration is deliberately **not** run against ~/ent by this document. ~/ent carries a live
session; this project's standing rule is strictly read-only there for exactly that reason (the
same "never modify hooks/ or a user project while a live session runs there" rule CLAUDE.md
states under ORCHESTRATION, restated for this task's dispatch by the maintainer's own 2026-07-14
commission), and migrating a deployment mid-session is itself an act that needs to not race a
live operator. The migration
path above is written so that whoever runs it — a future Sonnet builder, once ~/ent's live
session has ended and the maintainer clears the work — has the concrete steps rather than having
to reconstruct them under time pressure.

## What retires the ent merge gate

Today, a merge to autoharn's working branch that touches `hooks/` or `bootstrap/templates/` must
be held (built in a worktree, merge deferred) whenever a live session might be running against a
deployment that consumes those files live — an operating consequence of the never-modify-during-
a-live-session rule quoted above, applied specifically to these two directories because they are
what a deployment's shims execute live. Once a
deployment is pinned (submodule or copy-at-scaffold, per this
design), an autoharn merge no longer reaches that deployment at all until its operator runs the
explicit upgrade act — so the specific hazard the gate exists to prevent (an unrelated merge
silently changing a live deployment's behavior mid-session) is structurally gone for that
deployment, and the merge gate can be dropped **for deployments that have completed the
migration above**.

This retirement is scoped honestly, not oversold:

- It retires the gate **per pinned deployment**, not globally on day one — every adopter still
  running unmigrated (live-exec) continues to need the gate until it migrates. The gate itself
  should stay in force as a default until every known adopter is confirmed pinned; dropping it
  prematurely would reintroduce exactly the hazard this design closes.
- It retires the **execution-code coupling** hazard specifically. It does not retire whatever
  independent reasons might exist to be careful around a live session for other causes (e.g. data
  write coordination inside a deployment's own ledger, which is a concern about concurrent writes
  to a database, not about which version of `led`'s code is running) — those are separate hazards
  this design does not claim to address, named here so the retirement is not read more broadly
  than it is.
- It does not touch `kernel/lineage` semantics or `law/` in any way — pinning is entirely a
  scaffold/bootstrap mechanism (which files a deployment's shims execute), and this design
  introduces no kernel delta, no new ledger kind, and no change to the
  [birth chain](../GLOSSARY.md#birth-chain) (the ordered kernel SQL a new world receives at
  scaffold time). It is
  Sonnet-buildable on that basis alone (see the next section).

## Buildable now vs. constitutional

Everything this design proposes — the scaffold's `--pin` flag, the submodule wiring, the
copy-at-scaffold fallback script, the migration steps, the `./led decision` recording convention
— is ordinary `bootstrap/`-surface engineering: no `kernel/lineage`, `law/`, or `engine/lp/`
semantics are touched, so none of it needs a Fable-authored, maintainer-ratified spec under this
project's standing constitutional-route rule (CLAUDE.md, "ORCHESTRATION"). It is Sonnet-
executable once the maintainer green-lights the build (already given in principle at ledger row
684/686; the build itself is separate work from this design note and, per the same
never-modify-hooks/-or-a-user-project-during-a-live-session rule cited above, belongs in a
worktree with its merge gated on the existing ent-session merge gate until built and until
~/ent's live session clears).

## Related

- [`design/ORCH-RECOVERY-MODE-SIGNED.md`](ORCH-RECOVERY-MODE-SIGNED.md) — the companion design
  note this item composes with (ledger row 687 names the composition explicitly): recovery mode
  operates against a specific deployment's state, and a pinned deployment (this document) is what
  makes "which version of autoharn's own logic performed a recovery" an answerable, recorded
  question rather than "whatever the shared checkout happened to be running that day."
- [`design/MAINT-MAINTAINER-DECISION-BRIEF-2026-07-14.md`](MAINT-MAINTAINER-DECISION-BRIEF-2026-07-14.md),
  §B5 — the source framing this design executes, including the maintainer's own "responsible
  adults" / submodule language quoted above.
- [`GLOSSARY.md#the-scaffold`](../GLOSSARY.md#the-scaffold) and
  [`GLOSSARY.md#led-and-pickup`](../GLOSSARY.md#led-and-pickup) — the current live-exec shape this
  design changes for adopters, defined precisely.
- [`bootstrap/new-project.sh`](../bootstrap/new-project.sh)'s own header comment — the dated
  2026-07-11 "live verbs" ruling this design narrows in scope (from "every scaffolded world" to
  "autoharn's own `run*` worlds only"; adopters get the pinned shape instead).
- [CLAUDE.md](../CLAUDE.md), "Runs are strictly linear" — the ruling this design does not touch: it governs
  whether an *existing world's data* may be patched (no), which is a different question from
  whether a deployment's *operator-verb code* stays live-coupled to a shared checkout (this
  document's subject). The two are easy to conflate because both cite "runs are linear" as their
  motivating precedent; they are not the same axis.
