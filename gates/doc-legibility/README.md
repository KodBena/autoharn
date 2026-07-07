# doc-legibility gate

A mechanical gate that **fails the build if any acronym-like token in the scoped docs is neither
defined nor explicitly allow-listed.** It exists because the maintainer twice hit an undefined
acronym in the docs (first `SBC`, then `MC/DC`) and called the documentation opaque. Per
[ADR-0011 Rule 4](../../GLOSSARY.md#mechanization-discipline) the fix is the **class, not the
instance**: not a hand-list of the two acronyms that bit us, but a check that catches *every*
stranded acronym, including ones not yet written.

## What it enforces

For every doc in scope, every token with **≥2 uppercase letters** (an acronym / jargon-code) must be
either:

1. **defined** — bolded `**TOKEN**` on a *definition surface*, or
2. **allow-listed** — listed in [`allowlist.txt`](allowlist.txt) as common knowledge or a proper noun.

Anything else is a violation; the gate prints a grouped, counted list and exits non-zero. Empty
violations ⇒ `clean ✓`.

The check keys on the **atomic** acronym, not the surface token: a compound like `LTL/CTL`,
`non-LLM`, or `HP AC2/AC3` is resolved part-by-part, and a plural (`LLMs`, `ABoxes`) falls back to
its stem — so defining `LTL` once discharges every `LTL/*`, and defining `LLM` clears `LLMs`. A whole
compound can still be defined as a unit when that is the real term (`MC-DC`, `HL-MRF`, `SMT-LIB`),
and that takes precedence. Ordinary lowercase/Title-Case words never trip the gate.

### Scope

- `docs/ARCHITECTURE.md`
- the obligations×formalisms survey (`docs/research/2026-06-27-obligations-formalisms-survey/**.md`),
  minus its own definition surfaces (`KEY.md`, `GLOSSARY.md`).

Adjust `SCOPE` in [`check.py`](check.py) to widen coverage.

## Where definitions live

Three definition surfaces, all read by the gate (`DEF_FILES` in `check.py`):

| surface | role |
|---|---|
| [`terms.md`](terms.md) | the persistent, hand-authored acronym glossary (this directory) — the home for stray jargon |
| survey [`KEY.md`](../../docs/research/2026-06-27-obligations-formalisms-survey/KEY.md) | the survey's own legend (obligation codes, tiers, tool index) |
| root [`GLOSSARY.md`](../../GLOSSARY.md) | autoharn's coined vocabulary |

A token is "defined" if it is bolded `**TOKEN**` on any of these. (`GLOSSARY.md` headings use `###`,
not bold, so terms only reachable there — e.g. `SSOT` — are mirrored into `terms.md`.)

## How to run

```sh
python3 tools/doc-legibility/check.py     # from the repo root; exit 0 = clean, 1 = violations
```

No dependencies (Python 3 stdlib only).

## How to extend (define vs allow-list)

When the gate flags a new token, make exactly one honest choice:

- **It is real jargon** (a logic, an algorithm, a standard, a domain term) → **define it** in
  [`terms.md`](terms.md), one line, `**TOKEN** — one-line definition.`, in the right group. Get the
  expansion *right* (web-search to confirm: `MC-DC` = Modified Condition/Decision Coverage,
  `WCET` = Worst-Case Execution Time, `DvP` = Delivery-versus-Payment). Defining the singular stem
  also clears its plural.
- **It is genuinely common knowledge or a proper noun** (`SQL`, `API`, `OS`, `JSON`; `NASA`, `NYSE`,
  `ICU`; a tool/conference/journal/license name) → add it to [`allowlist.txt`](allowlist.txt).

> **Honesty (load-bearing).** An allow-list entry is a *claim* that the token needs no project
> definition. Do **not** allow-list genuine jargon to make the gate pass — that manufactures exactly
> the false authority this project exists to kill. Define real jargon; allow-list only the truly
> common and proper nouns.

## Wire it into CI / pre-commit (recommended)

The gate is only a *class*-fix if it cannot silently regress. Run it on every change:

- **pre-commit hook** — `.git/hooks/pre-commit` (or a `pre-commit` framework hook) that runs
  `python3 tools/doc-legibility/check.py` and blocks the commit on non-zero exit.
- **CI** — a job step `python3 tools/doc-legibility/check.py`; a failed step fails the build, with
  the grouped violation list in the log telling the author exactly what to define or allow-list.

Either way the contract is the same: a new undefined acronym cannot land in the scoped docs.
