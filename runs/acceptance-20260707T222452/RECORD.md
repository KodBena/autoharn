# Acceptance run — CONSOLIDATION-MANDATE.md §6, executed (not asserted)

- **Run id:** acceptance-20260707T222452 — the first occupant of `runs/`.
- **Executor / served model (self-report):** the consolidation builder, **Opus 4.8 (1M)**
  (`claude-opus-4-8[1m]`) — the standing caveat applies: no introspective channel could detect
  a silent substitution. Design docs were authored by claude-fable-5 (their own self-report).
- **From a fresh clone:** `git clone` of autoharn into a scratch path; execution 1 at clone
  HEAD `d12c279`, the definitive execution 2 at clone HEAD `7032fa3`. Driver script + both
  full logs are in this directory — the record is whole, not cherry-picked.
- **DB substrate:** the harness host (`192.168.122.1`), throwaway schemas
  (`acc_demo`/`acc_demo_kernel`, dropped after). No evidence ledger touched.

## The §6 criteria, verbatim, with verdicts

> **the bootstrap runs green** — **GREEN** (execution-2 log §a: env, git-hook install, gate
> import-smoke, census gates, DB reachability all OK; exit 0).

> **a real mini-collaboration exercises the ledger and the refuse-and-teach gate** — **GREEN**
> (log §b): a scratch kernel stood up from the lineage (s15 + s17-stamp + s17-independence +
> s18 + s19); an actor-omitted ledger INSERT succeeded with the actor resolved from the
> connection (`actor=author`) **on a non-default-schema kernel — the s19 foreclosure live**;
> the change gate **refused** an unticketed edit (exit 2, deny JSON) and **taught** the honest
> path verbatim ("a change to a source file must be preceded by a ledger entry naming the
> file… Insert the entry, then re-issue"); the taught path was then complied with — entry
> filed, re-issued, **allowed** (`unlocked_by_entry=2`); the gate journal banks both outcomes
> (the witness). The kernel stamp path was exercised (forgery + staleness refused, unstamped
> recorded, proxy self-review caught).

> **a close runs against the new layout's instruments** — **RAN, verdict RED-honest**
> (log §c, both `--mode readiness` and `--mode close` via `instruments/close_manifest.py`
> from the clone): every mandatory line ran or declared itself; "(none)" is provably distinct
> from "did not run" throughout (F49) — `contemporaneity` rendered **N/A-declared** (exit-3
> convention, "NOT clean, NOT a crash"), consumers rendered **N/A by design** on a target with
> no acts stream, `close_sweep` **QUARANTINED loudly** (filed as finding 51: the SSOT's
> env-override actor-model hardcodes `kernel.principal` — the s19 class's instrument-layer
> sibling), and `findings_gate` went **RED on 6 OPEN findings** — which is the close machinery
> WORKING (an increment cannot report complete with undischarged findings; findings 33/34 are
> the maintainer's standing pair, 49–52 were filed by this build). A clean-green close on a
> scratch target with open findings would have been the dishonest outcome.

> **the gates (no_lazy_imports, staging guard, fixture census) run from the new repo's own
> pre-commit** — **GREEN, on a real commit from the clone** (log §d): the negative first — an
> UNDECLARED commit was **refused** by the clone's own pre-commit ("staging guard FAILED —
> commit refused, finding 33"); the declared commit then passed the full chain
> (staging_guard → no_lazy_imports → fixture_census → layout_census → doc-legibility
> report-only) and landed (`3c4ecb2`).

> **every migrated gate's seen-red still proves it can fail** — **GREEN** (log §e): fixture
> census green (22 gates, each with banked red evidence + a registered runnable fixture), and
> one **live red re-executed from the clone** per migrated gate class — kernel/s19 (the
> pre-fix `set_actor` refusal reproduced against a live throwaway), layout-census +
> fixture-census (registry-emptied specimens), no_lazy_imports (a planted function-body
> import, exit 1), staging guard (the refused commit above), destructive-DDL (specimen),
> append-only (specimen), findings gate (both polarities via its fixture, witness banked),
> doc-legibility (live red over the corpus, wired report-only pending the acronym sweep),
> the act_stream adapter + substrate-required + no-vacuous verifiers (mutation flips RED
> inside each), and core-a (`--negative-control` PASS = the broken fixture failed loudly).

## What the acceptance itself caught (execution 1 → fixed → execution 2)

Executing (not asserting) the acceptance surfaced two more instances of the old-layout path
class — `gates/findings_gate_fixture.py` (tools/ + db/harness/ paths) and
`seen-red/06-append-only-integrity/red-specimen.py` (parents[4]/tools) — fixed, recorded as
adaptations, re-proven, and two defects were **FILED** (findings 51, 52), not narrated. That
the acceptance run caught real defects is the §6 discipline doing its job.
