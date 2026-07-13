# autoharn

Autoharn is the continuation home of the AI-collaborator harness project: clone this repo for
any important work. From a fresh clone you can do **both** things this project is for —

- **collaborate** under the harness — through the working standard, the append-only decision
  ledger, [stamps](GLOSSARY.md#stamp) (the HMAC binding each ledger row to the session that
  wrote it), and hooks that **[refuse-and-teach](GLOSSARY.md#refuse-and-teach)** — refuse an
  action that would break a guarantee, but explain what to do instead rather than failing
  silently — plus, when something resists resolution, "fire up an auditor"
  ([bootstrap/AUDITOR.md](bootstrap/AUDITOR.md)'s independent second opinion); and
- **build** the project — run closes (the run-completion step recorded under `runs/`; see
  the tree below), file findings/foreclosures, run the fixture and layout census scripts
  against the capability registry ([Pillar 1](GLOSSARY.md#pillar-1)), and build engine
  increments.

Autoharn is the corrected consolidation of two older repos (`claude_harness`,
`epistemic-operator`) into one human-navigable home. Those repos become read-only evidence
archives after the recorded **[HOME-FLIP](GLOSSARY.md#home-flip)** — the maintainer-performed
cutover after which this repo, not the two source repos, is authoritative (recorded in
[`provenance/HOME-FLIP.md`](provenance/HOME-FLIP.md)); the complete working surface lives
here, organized so every directory level is `ls`-legible.

> New here? Start with **[`USER-GUIDE.md`](USER-GUIDE.md)** — the front door: it gates you on
> the two prerequisites (a Postgres database you can reach and a Claude Code install) BEFORE
> any command asks for them, then walks you through scaffolding your own governed project.
> Read **[`CLAUDE.md`](CLAUDE.md)** next (the working standard every session runs under),
> then **[`bootstrap/QUICKSTART.md`](bootstrap/QUICKSTART.md)** — a walkthrough from cloning
> the repo to collaborating in it, executed rather than merely proofread; note its `psql`
> examples name the maintainer's own LAN database host, so substitute yours per
> **[`USER-CONFIGURATION.md`](USER-CONFIGURATION.md)**. What *binds* is in **[`law/`](law/)**;
> the vocabulary is in **[`GLOSSARY.md`](GLOSSARY.md)**.

## The tree (what each directory IS — one currency each)

Each line also carries a bracketed tag folded in from `ORCH-DIRCLASS.md` (moved to
[`vestigial_documentation/ORCH-DIRCLASS.md`](vestigial_documentation/ORCH-DIRCLASS.md) in the
2026-07-12 vestigial sweep — see [`VESTIGIAL-INDEX.md`](VESTIGIAL-INDEX.md)): **[CORE]** —
needed for a functioning autoharn; **[DOC]** —
documentation, excludable; **[RESEARCH]** — research corpora / experiments-on-the-harness,
excludable; **[OTHER]** — anything else. A directory that straddles two classes says so on its
own line rather than being forced into one
([ADR-0008](law/adr/0008-classification-discipline.md)).

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
hooks/        what INTERCEPTS at run time: git pre-commit, stamp, change gate (below)  [CORE]
drive/        run machinery for a collaboration: launch, arm template, delivery drill  [RESEARCH — apparatus, not corpus; a couple of probes double as Use-mode demo helpers]
seen-red/     both-polarity gate evidence (a gate never seen red is a claim)  [RESEARCH]
design/       pattern & design documents (not law, not run evidence)  [DOC]
research/     sourced research corpora  [RESEARCH]
runs/         NEW run/close records accrue here  [OTHER]
ephemera/     local-only session snapshots — gitignored, NEVER committed (privacy ruling 2026-07-09; the audit trail is the ledger + committed artifacts)  [OTHER]
provenance/   the transition record: migration manifest, path-translation, HOME-FLIP  [OTHER]
```

A few terms in that tree are house shorthand for specific files and scripts rather than
free-standing project vocabulary, so they are resolved here instead of in `GLOSSARY.md`:
**odd-link judgment** is design/analysis-track work, as opposed to even-numbered build-track
work — the numbering convention from
[`vestigial_documentation/judgment/POST-FABLE-OPERATING-BRIEF.md`](vestigial_documentation/judgment/POST-FABLE-OPERATING-BRIEF.md),
which also names **[POST-FABLE law](GLOSSARY.md#post-fable-law)**: judgment banked to disk
after the maintainer's primary authoring model withdrew, applied but never re-derived or
weakened by a later session. A **consult** is one numbered entry in that same series;
"consults 27/31/35/39" names four specific ones, filed under `judgment/e-series/`.
**acts-EDB** is the acts *extensional database* — `instruments/act_stream/` builds it from
session transcripts for the ASP (Answer Set Programming) engine to reason over — and the
parenthetical **(the Port/ACL)** names that adapter as this project's [anti-corruption
layer](GLOSSARY.md#anti-corruption-layer) for transcript ingestion: the one validated
boundary, never a hand-parsed shortcut. **[Both-polarity](GLOSSARY.md#both-polarity)**
fixtures (also the `seen-red/` line above) prove a property on both a passing and a failing
case, not only the happy path. **Arm template** and **delivery drill** are two of `drive/`'s
demo helpers ([`drive/arm.sh`](drive/arm.sh), [`drive/delivery_drill.py`](drive/delivery_drill.py)):
arming a template run and rehearsing a delivery end-to-end. **Census gates** are
[`gates/fixture_census.py`](gates/fixture_census.py) and
[`gates/layout_census.py`](gates/layout_census.py), which check that fixtures and
directories are registered rather than silently orphaned. **The change gate**
([`hooks/pretooluse_change_gate.py`](hooks/pretooluse_change_gate.py)) is the hook that
refuses an edit to a file no open work-item ticket has declared, so a change always traces
back to the ticket that authorized it.

## Two entry points

- **"How do I collaborate here?"** Go to [`bootstrap/`](bootstrap/) for setup and the
  walkthrough; the working standard is [`CLAUDE.md`](CLAUDE.md); what binds is [`law/`](law/).
- **"How do I build here?"** Work through [`engine/`](engine/), [`kernel/`](kernel/),
  [`stores/`](stores/), and [`instruments/`](instruments/); [`judgment/`](judgment/) holds
  the banked design basis those directories build against.

## Status

This is a fresh home, migrated 2026-07-07 from the two source repos (per
[`provenance/`](provenance/)). The migration provenance
([`provenance/MIGRATION.tsv`](provenance/MIGRATION.tsv)) records every file's source repo,
commit, and sha256. The epistemic-pilot series — the maintainer's ongoing line of
AI-collaborator governance pilots that autoharn continues (see [`provenance/`](provenance/)
for the repos it consolidates) — is not winding down; the standing bar is the maintainer's, referring to the US Nuclear
Regulatory Commission (NRC) as this project's stand-in for the highest external-assurance bar
it imagines being audited against: *until we can hand this harness to the NRC and walk away
in good conscience, we are not done.*

### Trust domain

Every role in this project's evidence chain — operator, verifier, database administrator,
and host owner — is one person in one trust domain. All tamper-evidence guarantees are
bounded accordingly; no claim of externally-verifiable assurance is made. This bound is
accepted and named rather than mitigated (maintainer ruling 2026-07-13). A second
key-holder or external state anchoring remain documented upgrades should the bound ever
be revisited — neither is in progress or planned.
