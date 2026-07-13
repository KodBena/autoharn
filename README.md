# autoharn

The continuation home of the AI-collaborator harness project: the repo you clone for
any important work. From a fresh clone you can do **both** things this project is for —

- **collaborate** under the harness (the working standard, the decision ledger, stamps,
  refuse-and-teach, "fire up an auditor" on a snag); and
- **build** the project (run closes, file findings/foreclosures, run the census/registry,
  build engine increments).

It is the corrected consolidation of two older repos (`claude_harness`, `epistemic-operator`)
into one human-navigable home. Those repos become read-only evidence archives after the
recorded HOME-FLIP; the complete working surface lives here, organized so every directory
level is `ls`-legible.

> New here? Start with **`USER-GUIDE.md`** — the front door: it gates you on the two
> prerequisites (a Postgres database you can reach and a Claude Code install) BEFORE any
> command asks for them, then walks you through scaffolding your own governed project.
> Then **`CLAUDE.md`** (the working standard every session runs under) and
> **`bootstrap/QUICKSTART.md`** (clone → collaborating, executed not proofread — note its
> `psql` examples name the maintainer's own LAN database host; substitute yours per
> `USER-CONFIGURATION.md`). What *binds* is in **`law/`**; the vocabulary is in
> **`GLOSSARY.md`**.

## The tree (what each directory IS — one currency each)

Each line also carries a bracketed tag folded in from `ORCH-DIRCLASS.md` (moved to
`vestigial_documentation/ORCH-DIRCLASS.md` in the 2026-07-12 vestigial sweep — see
`VESTIGIAL-INDEX.md`): **[CORE]** — needed for a functioning autoharn; **[DOC]** —
documentation, excludable; **[RESEARCH]** — research corpora / experiments-on-the-harness,
excludable; **[OTHER]** — anything else. A directory that straddles two classes says so on its
own line rather than being forced into one (ADR-0008).

```
bootstrap/    clone → collaborating: bootstrap.sh, QUICKSTART.md, AUDITOR.md  [CORE]
law/          what BINDS — read in full before work that invokes it  [DOC — but binding-in-spirit, not merely descriptive]
  adr/          the ADR corpus 0000–0017, verbatim
  briefs/       authoritative external-standards briefs + conformance map
judgment/     pre-banked odd-link judgment: apply, never weaken (POST-FABLE law)  [DOC — but normative-in-spirit like law/]
  engine/       engine seeds + panel + increment-0 (the live design basis)
  e-series/     governing analyses (consults 27/31/35/39) + pending ratification packages
  rulings/      ratified deliberation records
kernel/       the subject decision-ledger kernel  [CORE]
  lineage/      s10 … s28 DDL in order; new increments append
  fixtures/     both-polarity kernel fixtures
stores/       harness-db operational-store DDL (findings/foreclosures/rulings/acts/…) + fixtures  [CORE]
instruments/  close-time instruments: manifest, consumers, derivers, verifiers  [CORE]
  act_stream/   the session-transcript → acts-EDB adapter (the Port/ACL)
engine/       the deductive engine (ledger⇄logic marriage) — the project's build front  [CORE]
  lp/           the ASP programs
  tests/        engine tests (pure-logic + parity)
gates/        what REFUSES at commit: staging guard, lazy-import, census gates, doc-legibility  [CORE]
filing/       what WRITES records: file_finding / file_foreclosure / … / persist_ephemera  [CORE]
hooks/        what INTERCEPTS at run time: git pre-commit, stamp, change gate  [CORE]
drive/        run machinery for a collaboration: launch, arm template, delivery drill  [RESEARCH — apparatus, not corpus; a couple of probes double as Use-mode demo helpers]
seen-red/     both-polarity gate evidence (a gate never seen red is a claim)  [RESEARCH]
design/       pattern & design documents (not law, not run evidence)  [DOC]
research/     sourced research corpora  [RESEARCH]
runs/         NEW run/close records accrue here  [OTHER]
ephemera/     local-only session snapshots — gitignored, NEVER committed (privacy ruling 2026-07-09; the audit trail is the ledger + committed artifacts)  [OTHER]
provenance/   the transition record: migration manifest, path-translation, HOME-FLIP  [OTHER]
```

## Two entry points

- **"How do I collaborate here?"** → `bootstrap/` (setup + walkthrough), standard in
  `CLAUDE.md`, what binds in `law/`.
- **"How do I build here?"** → `engine/`, `kernel/`, `stores/`, `instruments/`, with
  `judgment/` holding the banked design basis.

## Status

Fresh home, migrated 2026-07-07 from the two source repos (per `provenance/`). The
migration provenance (`provenance/MIGRATION.tsv`) records every file's source repo,
commit, and sha256. The epistemic-pilot series is not winding down; the standing bar is
the maintainer's: *until we can hand this harness to the NRC and walk away in good
conscience, we are not done.*

### Trust domain

Every role in this project's evidence chain — operator, verifier, database administrator,
and host owner — is one person in one trust domain. All tamper-evidence guarantees are
bounded accordingly; no claim of externally-verifiable assurance is made. This bound is
accepted and named rather than mitigated (maintainer ruling 2026-07-13). A second
key-holder or external state anchoring remain documented upgrades should the bound ever
be revisited — neither is in progress or planned.
