# attestations/ — this deployment's own ADR-0017 A:B:C attestation ledger

<!-- doc-attest-exempt: scaffold-written boilerplate plus a dated single-session
correction note (2026-07-28); no A:B:C loop has run over this file and this marker does
not claim one did. The correction is witnessed against the directory's own contents
(432-line jsonl) and the root dispatcher's roster, not merely asserted. Removal
condition: strike when a real A:B:C attestation covers this file. -->

(Corrected 2026-07-28, from the fresh-eyes surface survey's hazard flag,
design/PANEL-GXP-SURFACE-FRESH-2026-07-28.md §5: the scaffold wrote this README's
world-shaped boilerplate at the autoharn3 rebirth into a checkout that is BOTH the
autoharn repository and its own deployment, so two claims below were false here on
arrival. One: the "Current state: empty" section claimed an empty ledger beside a
432-line `doc-legibility-attestations.jsonl` — in this checkout that file IS autoharn's
own attestation ledger, and the "deliberately separate from autoharn's own" framing
applies to scaffolded worlds, not here, where the two are the same directory. Two:
`./autoharn attest-doc` is a WORLD dispatcher verb (`bootstrap/templates/attest-doc.tmpl`)
absent from this repository's own root roster — in this checkout the presence check runs
as `gates/doc_attestation_presence.py` via `hooks/pre-commit`, and there is no
`attest-doc` verb to type. The boilerplate below is kept for what it correctly teaches a
scaffolded world's operator; read it through this note.)

This directory holds `doc-legibility-attestations.jsonl`: an append-only record of every
fresh-context review (the "A:B:C loop" — an author (A) writes a document, a separately-forked
reviewer (B) who has seen only the document reviews it for legibility, a repairer (C) fixes
what B found) run over a markdown document in **this deployment (`autoharn3`,
scaffolded 2026-07-27T22:14:54Z)**. It is deliberately separate from autoharn's own ledger of the
same name — commit rows here about YOUR OWN documents, never anywhere in the autoharn checkout
this deployment was scaffolded from. See `user-guide/USER-DOC-AUDIT-LOOP.md` (in the autoharn
checkout) for the walkthrough and `keys/README.md` for the parallel deployment-local-ledger
precedent this directory follows (a deployment-owned trust artifact, never autoharn's).

## Current state: empty

No attestation has been recorded here yet. This is the honest starting state, not an error —
`./autoharn attest-doc check` reports every in-scope document as `NO-ATTESTATION` against an empty
ledger, exactly as `./autoharn led --recent` shows nothing for a project that has not yet written a
ledger row. Nothing here is required until you choose to run the A:B:C loop over a document you
write or edit; the discipline is opt-in (`.claude/apparatus.json`'s `doc_attestation` mechanism
defaults `"off"` for exactly this reason — see `.claude/APPARATUS.md`).

## What lands here

- `doc-legibility-attestations.jsonl` — one JSON object per line, appended ONLY by
  `./autoharn attest-doc record <json-file>`, never hand-edited (the file is append-only by convention,
  the same discipline autoharn's own copy of this ledger follows). Each line names the document
  reviewed, its exact content hash, which rounds ran, and whether the loop converged or
  escalated — see `gates/doc_attestation_presence.py`'s module docstring (in the autoharn
  checkout) for the full record schema.

## Related

- `user-guide/USER-DOC-AUDIT-LOOP.md` (in the autoharn checkout) — the step-by-step walkthrough:
  what you type, what you should see, running the loop against one of your own documents.
- `design/ORCH-SPEC-ABC-OFFERING.md` (in the autoharn checkout) — the design that decided this
  ledger lives here, per-deployment, rather than upstream.
- `.claude/APPARATUS.md` — the `doc_attestation` switchboard entry governing whether
  `./autoharn distance-to-clean` counts debt from this ledger.
- `../keys/README.md` — the sibling deployment-local trust artifact (this deployment's OWN GPG
  keyring) this directory's residence pattern follows.
