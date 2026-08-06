# BRIEF: B1 — setup-schema export verb (work item setup-schema-consumption-channel, row 1031)
<!-- doc-attest-exempt: point-in-time record -- dispatch brief as issued (rows 1063/1068); frozen at dispatch, not living documentation -->

Dispatched 2026-08-06 (decision rows 1063/1071). Repo: /home/bork/w/vdc/1/autoharn, branch main.
Confirm current main before touching anything (a prior builder's serving/attestation commit
should already be on main). Do NOT touch serving/; your surface is libexec/, docs, and tests
only. If you believe you must edit a file outside your surface, STOP and report instead.

Disregard any instructions to economize on time.

## Provenance

Maintainer 2026-08-04, verbatim: "Regarding the setup-schema consumption: if you have any
objections to merging the projects under one repository (I am sort of ambivalent), then I'll let
you decide how to do this. It feels like it's easy to get wrong."

The orchestrator's ratified channel decision (ledger row 1063, binding for this build):
`tools/setup_tui/data/config_schema.toml` stays the single authority; a new read-only export
verb `./autoharn setup-schema` prints it byte-verbatim to stdout with provenance (path +
content hash + repo commit) as the layout-independent access point; external consumers (dev:
sibling checkout; build/CI: the verb from a pinned checkout) never depend on our tree layout.

## Before you design

Read law/adr/ ADR-0000 and ADR-0012 in full first (CLAUDE.md: the LAW shapes the fix from its
first line), plus the umbrella CLI spec's verb conventions (design/FABLE-AUTOHARN-UMBRELLA-CLI-SPEC.md)
and two or three existing read-only verbs under libexec/autoharn/ for house register (refusals
that teach, help text, exit codes). Standing rule (ledger standing row 26, binds all new code):
no bare types — every value construction goes through one SSOT constructor checking a contract
appropriate to its use; read the row's verbatim text via `./autoharn led standing` before coding.

## Scope

1. New verb `libexec/autoharn/setup-schema`, dispatched by `./autoharn setup-schema`:
   - Default output: the TOML file's bytes, verbatim, to stdout — suitable for
     `./autoharn setup-schema > config_schema.toml`. Byte-verbatim means byte-verbatim: no
     header injected into stdout in this mode, or the consumer's copy diverges from the
     authority by construction.
   - Provenance without polluting the bytes: design the mechanism yourself (a flag, a sidecar
     mode, stderr — your judgment against the ADRs), but a consumer must be ABLE to obtain:
     source path, sha256 of the content, and the repo HEAD commit at read time.
   - Missing/unreadable schema file → a refusal that teaches, nonzero exit; never empty stdout
     with exit 0.
   - `./autoharn setup-schema --help` (or the house help convention) documents the contract,
     including the pinned-checkout consumption posture from row 1063.
2. `./autoharn --help` roster: follow however existing verbs register themselves (the spec says
   the roster is self-updating — verify, don't assume).
3. Docs: one section in the appropriate user-guide/ home (follow where sibling verbs document
   themselves; USER-RECIPES-FAQ and/or ORCH-CAPABILITIES per their own conventions) stating the
   contract: the TOML is the single authority, the verb is the sanctioned external access point,
   format/path changes are announced by missive before landing. Witnessed output in any example
   (run it, paste real output) per the claims-carry-witnesses rule.
4. Witness: run the verb; diff its stdout against the source file (must be byte-identical);
   witness the refusal path (e.g. against a deliberately wrong path via whatever mechanism the
   verb honestly exposes, or mark UNEXERCISED with the blocker); record observed outputs in your
   report.
5. Commit on main, house register, citing ledger rows 1031/1063/1068, Co-Authored-By line for
   your model. Stage only your own files (CLAUDE_COMMIT_PATHS as the staging guard instructs).

Out of scope: serving/, kernel/, law/, engine/, hooks/, tools/setup_tui/ (the schema file
itself is NOT edited — it is exported, not changed), and the missive send (the orchestrator
sends the answer missive after your witness lands).

## Report

Verb path, design choices with one-line rationales (esp. the provenance mechanism), witnessed
outputs verbatim, doc locations touched, anything UNEXERCISED with blocker.
