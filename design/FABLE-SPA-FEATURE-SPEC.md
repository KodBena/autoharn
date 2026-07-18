<!-- doc-attest-exempt: pointer stub (same shape as BACKLOG.md's own pointer-stub exemption); the
     substantive content it points at moved to KodBena/autoharn-panel's own SPEC.md, which is a
     separate repository this document does not govern the legibility of -->

# Ledger-panel SPA — feature specification (POINTER)

This document's content moved to the SPA's own repository at its birth, per its own
opening line ("This document moves to the SPA's own repository at its birth and lives
there; autoharn's copy becomes a pointer"). The full text — Principles, the P0/P1/P2 tiers,
the obligation-graph view, the extension boundary, the no-elision rule — lives at:

- **`SPEC.md`** in [KodBena/autoharn-panel](https://github.com/KodBena/autoharn-panel), or,
  inside an autoharn checkout that has adopted the submodule, `tools/autoharn-panel/SPEC.md`.

The SPA itself ships into an adopting project as a git submodule (`tools/autoharn-panel`),
an enabled-by-default extension over the core generic ledger viewer — see
[USER-CONFIGURATION.md](../user-guide/USER-CONFIGURATION.md) ("The autoharn-panel extension") for the
submodule-add command and the environment variables that point a checkout at a deployment.

This pointer is not a summary and carries no independent design content — read the SPA
repo's `SPEC.md` for anything substantive; do not cite this file as a source for a claim
about the SPA's design.
