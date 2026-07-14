<!-- doc-attest-exempt: WP-C builder (commission-decomposition-manifest) has no agent-forking
tool available for the ADR-0017 A:B:C loop in this subagent invocation (same gap named at
ledger rows 699 and 714). Removal condition: strike this marker and run the real A:B:C loop
(or route through gates/doc_attestation_presence.py's normal path) the next time a session
with forking available touches this file, per ADR-0017 Rule 4 (migrates on touch). -->

# SCHEMA — the commission decomposition manifest shape

This document explains what a file under `panel/manifests/` is, for a reader who has never
seen the maintainer co-sign panel before. If you only want to know what a *specific* manifest
says, read that manifest's own `items` array directly — this file is about the *shape*, not
any one commission's content.

## What problem this solves

A ledger row of `kind='commission'` (see [GLOSSARY.md](../../GLOSSARY.md) for what the ledger
is) can be a single long, banked-verbatim block of text — a maintainer's executive response
covering dozens of separate asks in one sitting. The ledger itself has no notion of "item 3 of
this commission is done, item 7 is still open." A decomposition manifest is how the panel
supplies that missing structure without ever editing the commission row itself: it is a
**separate, hand-authored JSON file** that says, for one commission, "here is the list of
distinct items inside it, and here is which other ledger facts (if any) genuinely witness each
item's disposition."

The manifest is authored by a person or agent reading the commission closely — it is not
derived mechanically, because deciding "does ledger row 720 really discharge concern B1" is a
judgment call a machine cannot safely make. What the panel's backend computes mechanically,
every time the page loads, is each item's live **status** (OPEN / WITNESSED / PARTIAL /
COSIGNED) — see `panel/backend/disposition.py` — from the witnesses this manifest names, joined
against whatever the ledger currently says about those witnesses. The manifest names the
*evidence to look at*; the backend looks at it fresh, live, every time — a manifest is never
allowed to assert a status itself.

## File naming

One manifest file per commission, named `<manifest_id>.json` in this directory, where
`manifest_id` is a short slug the panel's URL and API use to address it (e.g.
`GET /api/commission/0714_exec_response`). `manifest_id` inside the file MUST match the
filename stem.

## Top-level shape

```json
{
  "manifest_id": "0714_exec_response",
  "commission_row": 680,
  "title": "MAINTAINER EXECUTIVE RESPONSE 2026-07-14",
  "items": [ /* Item objects, see below */ ]
}
```

- `manifest_id` (string) — matches the filename stem, and what the panel API's
  `{manifest_id}` path segment expects.
- `commission_row` (integer) — the ledger row `id` (in the deployment's `ledger` table,
  `kind='commission'`) this manifest decomposes. The panel reads that row live and shows it
  alongside the decomposition, so a reader can always check the manifest against the source.
- `title` (string) — a short human label for the commission, shown as the page heading.
  Not a verbatim slice; ordinary prose is fine here.
- `items` (array of Item objects) — the enumerated item universe. See "How to enumerate an
  item universe" below for what "complete" means here.

## Item object shape

```json
{
  "id": "A1",
  "parent": null,
  "label": "Part A1 / A1 — Stage 0, fact-family engine integration, ...",
  "text": "Yes obviously stage 0. Prioritize (b) integration for fact families ...",
  "witnesses": [
    {"ref_kind": "work", "ref": "kr-titration-design-exploration", "note": "..."},
    {"ref_kind": "row", "ref": 681, "note": "..."}
  ]
}
```

- `id` (string) — a stable, unique-within-this-manifest identifier. Prefer the commission's
  own labels where the commission has them (its own headings, letters, numbers) so a reader
  cross-checking the manifest against the source commission does not have to guess a mapping.
  Where the source commission's own labels collide across sections (this project's own
  commission 680 is the worked example: it has an "A2" nested under "Part A1" that is a
  *completely different item* from the standalone "Part A2" section — the maintainer named
  this exact confusion himself in the commission, see item `B2`), give each a distinct `id`
  and use `label` to carry the disambiguating context; never invent an `id` that would recreate
  the same collision one level down.
- `parent` (string id or `null`) — for a manifest whose commission has a real tree structure
  (sub-items under a numbered item), the parent's `id`. `null` for a top-level item. A flat
  commission (every item top-level) is valid — `parent` is always `null` in that case, not
  omitted (every Item object carries the key).
- `label` (string) — a short, human-authored heading for the item. Ordinary prose, not a
  verbatim slice; this is where you disambiguate a collision (see `id` above) or otherwise
  orient a reader before they reach `text`.
- `text` (string) — a **verbatim slice** of the commission's own words for this item. This is
  data, not authored prose, and is therefore exempt from this project's documentation-legibility
  rules (paraphrase-freedom is deliberate: [ADR-0005](../../law/adr/0005-documentation-discipline.md)'s
  verbatim-commission convention, reaffirmed after a 2026-07-13 censure for paraphrasing a brief
  and narrowing its scope in the retelling — see this project's ledger for the dated record).
  Where the commission itself does not give a named item individual text (this project's own
  commission 680 says "B1 through B6 all yes" without spelling out B3, B4, or B5 word for word —
  their content lives in a *different* document the commission's own B1/B2/B6 sentences point
  at), `text` carries the shortest verbatim fragment that is genuinely there, and the item's
  `witnesses[].note` fields say plainly where the fuller content actually comes from. Never
  paraphrase to fill the gap.
- `witnesses` (array of Witness objects, possibly empty) — see below. **An item with no
  genuine witness gets `"witnesses": []`, full stop.** This is not a defect in the manifest; it
  is the honest statement that nothing in the ledger yet discharges this item, and the panel
  will render it OPEN/UNWITNESSED accordingly. Inventing or stretching a witness to avoid an
  empty array is the exact hack-rationalization tell this project's tooling is built to catch —
  see [law/adr/0000](../../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)'s
  closure-statement discipline and this project's `hack-rationalization-detector` review pass.

## Witness object shape

```json
{"ref_kind": "work", "ref": "pgaudit-exploration", "note": "why this genuinely pertains"}
```

or

```json
{"ref_kind": "row", "ref": 716, "note": "why this genuinely pertains"}
```

- `ref_kind` — exactly `"work"` or `"row"`.
  - `"work"` means `ref` is a **work-item slug** (a string) as it appears in this deployment's
    `work_item_current` table (the ledger's own tracking of a piece of work from
    `work_opened` through `work_claimed` to `work_closed`). The panel resolves this live: it
    reads the work item's current state (open/claimed/closed), resolution, and witness text
    fresh from the ledger every time the page loads — this manifest never records that state
    itself, because it would go stale the moment the work item's state changes.
  - `"row"` means `ref` is a **ledger row id** (an integer) — a specific decision, finding, or
    other ledger entry that itself is the disposition (not routed through the work-item
    lifecycle). The panel resolves this live too: it reads that row's kind, statement, actor,
    and timestamp fresh every time.
- `ref` — the slug (string) or row id (integer) per `ref_kind` above. It MUST resolve to a
  real row in the live ledger. A `ref` that does not resolve is a manifest defect, not a
  legitimate "maybe" — if you are not sure a witness is real, leave it out of the array
  entirely (see the empty-array rule above), never guess at an id.
- `note` — a short, human-authored explanation of *why this witness genuinely pertains to this
  item* — the authored judgment call this manifest exists to record. Quote the ledger text that
  justifies the claim where practical; a bare "see row 683" with no explanation is not enough
  for a reader to trust the link.

## How to enumerate an item universe (ADR-0000 closure-statement discipline)

A decomposition manifest is itself a closure statement in the sense
[ADR-0000's Rule 2(a) 2026-07-02 amendment](../../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md#amendments)
describes: it claims to cover the commission's item *universe*, and that claim is falsifiable —
a reader can open the source commission row and check nothing was silently dropped. Read the
commission row in full (`./led show <row-id>`, see the repo root `led` verb) before authoring
the item list; do not enumerate from a summary or a memory of what the commission said. Every
distinct ask, posture, or concern the commission's own text separates out (by heading, numbered
list, or explicit enumeration) gets its own `id`. Do not merge two of the commission's own
distinct items into one manifest item to save authoring time, and do not split one of the
commission's items into several unless the commission's own text already does so.

## How status is computed (not this file's job)

This file never contains a `status` field. Status is derived live, at read time, by
`panel/backend/disposition.py`, from the witnesses this manifest names and their current
ledger state — see that module's own documentation for the exact rule (OPEN / WITNESSED /
PARTIAL / COSIGNED). The reason status is never stored here or anywhere else is the same
lesson this project's stamp/hash pairing defect taught at the ledger's own dispatch/completion
layer: a derived fact written to storage can go stale and silently lie; a derived fact computed
at read time cannot.
