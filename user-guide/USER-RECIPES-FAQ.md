# Can I do that? — recipes FAQ for operators

This page is written for an operator of a scaffolded project who wants to know whether the
harness supports a thing they have in mind, and what to actually type if it does. Every
entry below began life as a real operator question ("can we use X for end users?", "can I
track Y?") asked of this project's orchestrator during 2026-07; the answers were built,
witnessed, and then condensed here. This page deliberately restates NO grammar and NO
ceremony in full — each recipe names the intent, the one-line shape, the honest limit, and
the ONE page where the full truth lives (this project's single-source-of-truth discipline:
a grammar documented twice drifts). The dense per-mechanism inventory this page complements
is [ORCH-CAPABILITIES.md](../ORCH-CAPABILITIES.md); the front door for first-time setup is
[USER-GUIDE.md](USER-GUIDE.md). Delegating authority, taint (license/provenance contamination) compartmentalization, and
reviewer read zoning ([ADR-0018](../law/adr/0018-consults-are-not-front-loaded.md)) get their own worked-example page:
[USER-ACCESS-CONTROL-GUIDE.md](USER-ACCESS-CONTROL-GUIDE.md).

A note on two terms used unglossed across the suite: the **kernel** is this
project's enforced Postgres layer (schema, functions, constraints -- the thing that
accepts or refuses every write); a **world** is one scaffolded, database-backed
deployment of it (the one defining home is [GLOSSARY.md#world](../GLOSSARY.md#world), used everywhere).

## Contents

The sections below, in the order the original single page listed them — each link
now opens the recipe file that section moved to at the split.

- [Planning and retrospectives](recipes/DECLARING-AND-QUEUES.md#planning-and-retrospectives)
- [Workflow patterns](recipes/METHODS.md#workflow-patterns)
- [Getting started: the guided setup TUI (`python3 -m tools.setup_tui`)](recipes/SETUP-AND-SCAFFOLD.md#getting-started-the-guided-setup-tui-python3--m-toolssetup_tui)
- [Declaring things on the ledger](recipes/DECLARING-AND-QUEUES.md#declaring-things-on-the-ledger)
- [Granting and revoking a principal's authority (s40/s41)](recipes/IDENTITY-AND-AUTHORITY.md#granting-and-revoking-a-principals-authority-s40s41)
- [Entitlement enforcement and work gating (s60): who may act, and when a claim may start](recipes/IDENTITY-AND-AUTHORITY.md#entitlement-enforcement-and-work-gating-s60-who-may-act-and-when-a-claim-may-start)
- [Recording verdicts and refusals as typed, queryable ledger entries (s42/s43)](recipes/EVIDENCE-AND-TRUST.md#recording-verdicts-and-refusals-as-typed-queryable-ledger-entries-s42s43)
- [Suspending, reviving, and revoking a principal's standing (s45)](recipes/IDENTITY-AND-AUTHORITY.md#suspending-reviving-and-revoking-a-principals-standing-s45)
- [Model identity: watchdog, attestation, defeat](recipes/EVIDENCE-AND-TRUST.md#model-identity-watchdog-attestation-defeat)
- [Trust ceremonies](recipes/EVIDENCE-AND-TRUST.md#trust-ceremonies)
- [Review discipline](recipes/REVIEW-AND-GATING.md#review-discipline)
- [Work-unit role assignment: who opens, claims, closes, and reviews](recipes/IDENTITY-AND-AUTHORITY.md#work-unit-role-assignment-who-opens-claims-closes-and-reviews)
- [Classifying audit/diagnostic findings](recipes/REVIEW-AND-GATING.md#classifying-auditdiagnostic-findings)
- [The findings-ledger / mined-checklist / +A:B:C pattern](recipes/REVIEW-AND-GATING.md#the-findings-ledger--mined-checklist--abc-pattern)
- [Capturing errors so they cannot quietly recur (ADR-0000 / ADR-0011)](recipes/METHODS.md#capturing-errors-so-they-cannot-quietly-recur-adr-0000--adr-0011)
- [Drift backstops (one generic method for anything that goes quietly stale)](recipes/METHODS.md#drift-backstops-one-generic-method-for-anything-that-goes-quietly-stale)
- [Documentation quality](recipes/REVIEW-AND-GATING.md#documentation-quality)
- [Operating rhythm](recipes/METHODS.md#operating-rhythm)
- [Your review queue](recipes/DECLARING-AND-QUEUES.md#your-review-queue)
- [Correcting the record — supersession, and what to do about its fallout](recipes/THE-RECORD.md#correcting-the-record--supersession-and-what-to-do-about-its-fallout)
- [The ledger boundary service (`serving/`)](recipes/CLI-AND-BOUNDARY.md#the-ledger-boundary-service-serving)
- [Reaching the ledger through a shared boundary service, and compiling workflow units (2026-07-18)](recipes/CLI-AND-BOUNDARY.md#reaching-the-ledger-through-a-shared-boundary-service-and-compiling-workflow-units-2026-07-18)
- [Role charters and briefs (`tools/role_charter.py`, `tools/role_brief.py`)](recipes/IDENTITY-AND-AUTHORITY.md#role-charters-and-briefs-toolsrole_charterpy-toolsrole_briefpy)
- [CLI quality-of-life: row-id echo and `judge` auto-layer detection](recipes/CLI-AND-BOUNDARY.md#cli-quality-of-life-row-id-echo-and-judge-auto-layer-detection)
- [`led` help tokens, `--json` payload mode, and `work list`'s default filter (led.tmpl trio)](recipes/CLI-AND-BOUNDARY.md#led-help-tokens---json-payload-mode-and-work-lists-default-filter-ledtmpl-trio)
- [Ledger-wide as-of read and inspection-copy export (`asof-export`)](recipes/THE-RECORD.md#ledger-wide-as-of-read-and-inspection-copy-export-asof-export)
- [Exporting the setup TUI's config schema for external consumers (`./autoharn setup-schema`)](recipes/SETUP-AND-SCAFFOLD.md#exporting-the-setup-tuis-config-schema-for-external-consumers-autoharn-setup-schema)
- [Deployments can self-serve the harness changelog (`orchlog` wrapper at scaffold)](recipes/SETUP-AND-SCAFFOLD.md#deployments-can-self-serve-the-harness-changelog-orchlog-wrapper-at-scaffold)
- [Verifying tags, signed commissions, and documentation debt (`attest-tags`, `verify-commission`, `attest-doc`, `distance-to-clean`)](recipes/EVIDENCE-AND-TRUST.md#verifying-tags-signed-commissions-and-documentation-debt-attest-tags-verify-commission-attest-doc-distance-to-clean)
- [Recusal and independent RCA (a conflict-of-interest method harvested downstream)](recipes/METHODS.md#recusal-and-independent-rca-a-conflict-of-interest-method-harvested-downstream)
- [What this page is not](#what-this-page-is-not)


## Planning and retrospectives

Estimate-vs-actual retrospective rows; nothing gates on accuracy. Full recipe: [recipes/DECLARING-AND-QUEUES.md](recipes/DECLARING-AND-QUEUES.md#planning-and-retrospectives).

## Workflow patterns

The A:B:C fix-point loop, workflow-script gotchas, makespan scheduling, ordering proofs, bookkeeping-close pairing. Full recipe: [recipes/METHODS.md](recipes/METHODS.md#workflow-patterns).

## Getting started: the guided setup TUI (`python3 -m tools.setup_tui`)

The guided, driver-only TUI from nothing to a running world. Full recipe: [recipes/SETUP-AND-SCAFFOLD.md](recipes/SETUP-AND-SCAFFOLD.md#getting-started-the-guided-setup-tui-python3--m-toolssetup_tui).

## Declaring things on the ledger

`resource:`/`taxon:`/`interface:`/`task-policy:` rows and their honest enforcement tiers. Full recipe: [recipes/DECLARING-AND-QUEUES.md](recipes/DECLARING-AND-QUEUES.md#declaring-things-on-the-ledger).

## Granting and revoking a principal's authority (s40/s41)

Registering principals, standing, roles, competence, relations. Full recipe: [recipes/IDENTITY-AND-AUTHORITY.md](recipes/IDENTITY-AND-AUTHORITY.md#granting-and-revoking-a-principals-authority-s40s41).

## Entitlement enforcement and work gating (s60): who may act, and when a claim may start

Who may act, and when a claim may start. Full recipe: [recipes/IDENTITY-AND-AUTHORITY.md](recipes/IDENTITY-AND-AUTHORITY.md#entitlement-enforcement-and-work-gating-s60-who-may-act-and-when-a-claim-may-start).

**"Can I also restrict WHAT a principal may read, not just what it may do?"** — yes, added
2026-07-29: scope binding, the boundary's own scope filter, and `judge`'s entitlement-layer
differential. Full recipe:
[USER-ACCESS-CONTROL-GUIDE.md §7](USER-ACCESS-CONTROL-GUIDE.md#7-the-general-medium-scope-binding-scope-filtering-and-the-entitlement-floor)
— note its own currency caveat: the kernel side (s70/s71) rides the next scaffolded world's
birth chain, not autoharn3 today; the served-boundary filter and CLI minting are live now.

## Recording verdicts and refusals as typed, queryable ledger entries (s42/s43)

Refused writes as committed, attributed, hash-covered ledger rows. Full recipe: [recipes/EVIDENCE-AND-TRUST.md](recipes/EVIDENCE-AND-TRUST.md#recording-verdicts-and-refusals-as-typed-queryable-ledger-entries-s42s43).

## Suspending, reviving, and revoking a principal's standing (s45)

Standing lifecycle and its honest one-way limits. Full recipe: [recipes/IDENTITY-AND-AUTHORITY.md](recipes/IDENTITY-AND-AUTHORITY.md#suspending-reviving-and-revoking-a-principals-standing-s45).

## Model identity: watchdog, attestation, defeat

OTel provenance watchdog, attestation, and model-defeat derivation. Full recipe: [recipes/EVIDENCE-AND-TRUST.md](recipes/EVIDENCE-AND-TRUST.md#model-identity-watchdog-attestation-defeat).

## Trust ceremonies

The GPG web-of-trust layer's ceremonies. Full recipe: [recipes/EVIDENCE-AND-TRUST.md](recipes/EVIDENCE-AND-TRUST.md#trust-ceremonies).

## Review discipline

Countersign obligations, `decomposition_review`, content-free-review detection, the changeset-vs-commit and precondition-gating recipes. Full recipe: [recipes/REVIEW-AND-GATING.md](recipes/REVIEW-AND-GATING.md#review-discipline).

## Work-unit role assignment: who opens, claims, closes, and reviews

Who opens, claims, closes, and reviews a work item. Full recipe: [recipes/IDENTITY-AND-AUTHORITY.md](recipes/IDENTITY-AND-AUTHORITY.md#work-unit-role-assignment-who-opens-claims-closes-and-reviews).

## Classifying audit/diagnostic findings

The finding-severity taxonomy. Full recipe: [recipes/REVIEW-AND-GATING.md](recipes/REVIEW-AND-GATING.md#classifying-auditdiagnostic-findings).

## The findings-ledger / mined-checklist / +A:B:C pattern

Mining recurring findings into a checklist, and the +A:B:C loop. Full recipe: [recipes/REVIEW-AND-GATING.md](recipes/REVIEW-AND-GATING.md#the-findings-ledger--mined-checklist--abc-pattern).

## Capturing errors so they cannot quietly recur (ADR-0000 / ADR-0011)

Turning a caught error into a durable, non-recurring check. Full recipe: [recipes/METHODS.md](recipes/METHODS.md#capturing-errors-so-they-cannot-quietly-recur-adr-0000--adr-0011).

## Drift backstops (one generic method for anything that goes quietly stale)

The generic method for anything that goes quietly stale. Full recipe: [recipes/METHODS.md](recipes/METHODS.md#drift-backstops-one-generic-method-for-anything-that-goes-quietly-stale).

## Documentation quality

The fresh-context documentation review loop, and briefing your reviewer. Full recipe: [recipes/REVIEW-AND-GATING.md](recipes/REVIEW-AND-GATING.md#documentation-quality).

## Operating rhythm

Picking up work, safety-mechanism modes, and the linear-runs ruling. Full recipe: [recipes/METHODS.md](recipes/METHODS.md#operating-rhythm).

## Your review queue

The one grammar whose single documented home is this suite. Full recipe: [recipes/DECLARING-AND-QUEUES.md](recipes/DECLARING-AND-QUEUES.md#your-review-queue).

## Correcting the record — supersession, and what to do about its fallout

Supersession, cascade, and orphan disposition. Full recipe: [recipes/THE-RECORD.md](recipes/THE-RECORD.md#correcting-the-record--supersession-and-what-to-do-about-its-fallout).

## The ledger boundary service (`serving/`)

The HTTP boundary service over the ledger. Full recipe: [recipes/CLI-AND-BOUNDARY.md](recipes/CLI-AND-BOUNDARY.md#the-ledger-boundary-service-serving).

## Reaching the ledger through a shared boundary service, and compiling workflow units (2026-07-18)

Multiplexing several deployments behind one boundary-service process; the workflow-unit compiler. Full recipe: [recipes/CLI-AND-BOUNDARY.md](recipes/CLI-AND-BOUNDARY.md#reaching-the-ledger-through-a-shared-boundary-service-and-compiling-workflow-units-2026-07-18).

## Role charters and briefs (`tools/role_charter.py`, `tools/role_brief.py`)

Written statements of what a role is for and what it may do. Full recipe: [recipes/IDENTITY-AND-AUTHORITY.md](recipes/IDENTITY-AND-AUTHORITY.md#role-charters-and-briefs-toolsrole_charterpy-toolsrole_briefpy).

## CLI quality-of-life: row-id echo and `judge` auto-layer detection

`led`'s row-id echo; `judge`'s auto-layer detection. Full recipe: [recipes/CLI-AND-BOUNDARY.md](recipes/CLI-AND-BOUNDARY.md#cli-quality-of-life-row-id-echo-and-judge-auto-layer-detection).

## `led` help tokens, `--json` payload mode, and `work list`'s default filter (led.tmpl trio)

Three small `led` usability changes, all in `led.tmpl`. Full recipe: [recipes/CLI-AND-BOUNDARY.md](recipes/CLI-AND-BOUNDARY.md#led-help-tokens---json-payload-mode-and-work-lists-default-filter-ledtmpl-trio).

## Ledger-wide as-of read and inspection-copy export (`asof-export`)

Reconstructing the whole ledger's in-force state as of a past moment. Full recipe: [recipes/THE-RECORD.md](recipes/THE-RECORD.md#ledger-wide-as-of-read-and-inspection-copy-export-asof-export).

<!-- doc-attest-exempt: this index line is new prose, Sonnet-authored 2026-08-06 alongside the
full recipe section it points to (work item setup-schema-consumption-channel, ledger rows
1031/1063/1068); no live A:B:C loop has run on it yet and this marker does not claim one did.
Removal condition: strike this marker and run the real A:B:C loop next time this line is
touched for its own prose content. -->

## Exporting the setup TUI's config schema for external consumers (`./autoharn setup-schema`)

Byte-verbatim export of `tools/setup_tui/data/config_schema.toml`, with provenance. Full recipe: [recipes/SETUP-AND-SCAFFOLD.md](recipes/SETUP-AND-SCAFFOLD.md#exporting-the-setup-tuis-config-schema-for-external-consumers-autoharn-setup-schema).

## Deployments can self-serve the harness changelog (`orchlog` wrapper at scaffold)

The `orchlog` shim the scaffold writes at birth. Full recipe: [recipes/SETUP-AND-SCAFFOLD.md](recipes/SETUP-AND-SCAFFOLD.md#deployments-can-self-serve-the-harness-changelog-orchlog-wrapper-at-scaffold).

## Verifying tags, signed commissions, and documentation debt (`attest-tags`, `verify-commission`, `attest-doc`, `distance-to-clean`)

Is this claim on the record actually checkable, or only asserted? Full recipe: [recipes/EVIDENCE-AND-TRUST.md](recipes/EVIDENCE-AND-TRUST.md#verifying-tags-signed-commissions-and-documentation-debt-attest-tags-verify-commission-attest-doc-distance-to-clean).

## Recusal and independent RCA (a conflict-of-interest method harvested downstream)

A conflict-of-interest method harvested downstream, review-only. Full recipe: [recipes/METHODS.md](recipes/METHODS.md#recusal-and-independent-rca-a-conflict-of-interest-method-harvested-downstream).

## What this page is not

This page is not an inventory (that is [ORCH-CAPABILITIES.md](../ORCH-CAPABILITIES.md), where every
mechanism carries witnessed output or an honest UNWITNESSED mark), it is not a setup guide
([USER-GUIDE.md](USER-GUIDE.md)), and it is not a promise that a recipe listed here is
enforced — where an entry says "declaration only," the enforcement genuinely does not
exist yet, and the cited spec names the stage that would build it.

