# autoharn

A **harness for working with AI collaborators** — a metaproject that formalizes a
maintainer's Claude Code workflow into *queryable* tools (SQL stores + logic
programs) so that what an AI engineer needs to "do the right thing" is something it
can **pull on demand**, not something the maintainer must re-explain every session.

It is deliberately general: its subject is *doing the right thing, and documenting how*,
for concrete projects — including ones not yet conceived. Two real projects (an
operations-research package and a Go-study web app) serve as the worked examples it is
derived from, not as its scope.

> **New to the vocabulary?** Coined terms — [Pillar](GLOSSARY.md#pillar),
> [intent SSOT](GLOSSARY.md#intent-ssot), [Mechanization Discipline](GLOSSARY.md#mechanization-discipline), … —
> are defined in **[GLOSSARY.md](GLOSSARY.md)** and linked on first use throughout the docs, so you
> never have to grep to learn what a term means.

## The thesis

Prose disciplines decay, because they are policed by one person's memory. The only
durable corrective is a **mechanism** — a queryable, mechanical net that quantifies over
the *class* of a defect, not the instance. autoharn is that net, generalized from a single
existing precedent (a Postgres "anti-corruption layer" that replaced a hand-edited JSON
file with a relational source-of-truth + invariant gate) into three pillars:

1. **[Capability registry](GLOSSARY.md#pillar-1) ([intent SSOT](GLOSSARY.md#intent-ssot)).** What tools, services, venvs, and *blessed*
   methods are available — including automated-reasoning / optimization tools (Z3,
   OR-Tools) that yield *provable* results rather than statistical hunches. The agent
   **queries** this at point-of-need (pull), instead of leaning on stale injected memory
   (push) exactly when context is thinnest.

2. **[Provenance / accountability ledger](GLOSSARY.md#pillar-2).** Attributable links between a git commit, a
   benchmark artifact, its environment, the hypothesis it tested, and the session that
   authored it — so a performance claim is a checkable fact, and a regression is traceable
   to the change that introduced it.

3. **[Logic safety net](GLOSSARY.md#pillar-3).** Per-store invariant gates backed by real engines: *classical*
   logic (SQL `WITH RECURSIVE`, Z3, OR-Tools CP-SAT) for provable invariants, and
   *non-classical* logic (defeasible / temporal / paraconsistent) for the things prose
   handles informally — superseded decisions, provisional records, conflicting advisories.

The unifying north star is a discipline the source projects already name **"Mechanization
Discipline"**: *convert every executive lapse into a mechanism, so the same error is never
seen twice.* autoharn is, in one line, the CI sweep that discipline openly admits it lacks.

## Status

Early. The first artifact is the **foundational map** — a high-fidelity survey of the
existing disciplines, the SQL/lint mechanisms already in use, the benchmark-attribution
gap, and the tool/intent surface — which grounds the design so the harness grows *out of*
existing conventions rather than imposing foreign ones.

- 📍 **[docs/research/2026-06-27-foundational-map/](docs/research/2026-06-27-foundational-map/)**
  — start with `00-synthesis.md`.

## A note on the name

`autoharn` is intentionally neutral. The harness is built with, and currently tuned for,
Anthropic's Claude Code, but its design (pull-not-push capability SSOT, attributable
provenance, logic-backed invariant gates) is not specific to any one assistant.
