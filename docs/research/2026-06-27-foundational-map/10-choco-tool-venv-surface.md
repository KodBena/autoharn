# Report 10 — choco/tool-venv-surface — chocofarm's tool / venv / capability surface (Pillar 1; authored directly after the structured-output reader hit its retry cap twice)

## Summary

chocofarm has NO dependency manifest — pyproject.toml is [tool.mypy] config only and the package is explicitly 'unpackaged' — so the shared venv /home/bork/w/vdc/venvs/generic (Python 3.13.13) is the de-facto AND only capability SSOT, recorded in exactly one CLAUDE.md line that names the interpreter but not the stack inside it. That venv already carries a rich automated-reasoning / optimization stack: z3 4.16.0 (SMT), ortools 9.15.6755 (CP-SAT), cvxpy 1.9.1 (convex), sympy 1.14.0 (CAS), scipy 1.17.1, networkx 3.6.1 — plus the numerics jax 0.10.1, numba 0.65.1, optax 0.2.8. The maintainer's 'reach for the provable tool' intent IS realized, but only in silos a cold agent cannot discover: Z3 in 26 formal-model scripts under docs/design/stall-investigation/ (concurrency admissibility / FIFO / starvation / drain proofs); CP-SAT in exactly one site (throughput-lab/hp/backends/cpsat.py, the enumerate-all-solutions hp config-space driver with symmetry-orbit canonicalization — the 'declarative hyperparameter sweep'); cvxpy in exactly one site (the leaf-eval convex allocation driver). sympy, scipy.optimize and networkx are installed but used NOWHERE — the venv as 'a projection of intent' the brief names. Nothing enumerates any of this, and nothing records what each tool PROVES, so an agent must be told rather than asking.

## Key facts

- No dependency manifest: pyproject.toml is [tool.mypy] only; chocofarm is 'unpackaged'. The venv /home/bork/w/vdc/venvs/generic (Python 3.13.13) is the de-facto capability SSOT, named in one CLAUDE.md line (159-161).
- Capability row — z3 | solver/SMT | venv generic, 4.16.0 | invoke `from z3 import Solver` | PROVES: feasibility / UNSAT, admissibility, safety & starvation / FIFO invariants — exact, not sampled.
- Capability row — ortools CP-SAT | solver/CP-IP | venv generic, 9.15.6755 | invoke `from ortools.sat.python import cp_model` | PROVES: finite-domain feasibility + EXHAUSTIVE enumeration with symmetry dedup.
- Capability row — cvxpy | solver/convex | venv generic, 1.9.1 | invoke `import cvxpy` | PROVES: globally-optimal convex allocation (the leaf-eval throughput bound).
- Capability row — sympy 1.14.0 / scipy.optimize (scipy 1.17.1) / networkx 3.6.1 | CAS / numeric optimization / graph algorithms | venv generic | INSTALLED, USED NOWHERE — 'projection of intent': blessed by presence, neglected in practice.
- Capability row — numerics jax 0.10.1, numba 0.65.1, optax 0.2.8 | lib | venv generic | the AZ forward + njit hot-path + optimizer stack.
- Z3 is USED but SILOED: 26 files (2 `import z3` + 24 `from z3`) under docs/design/stall-investigation/{formal,blind-model,blind-model-v2}/ — formal SMT models of the throughput stall (convoy{,2,3,4}, model{,2,3}, fairqueue-starvation-N, inflight<=1, producer-FIFO, server-drain admissibility). A blessed PRACTICE invisible to a cold agent.
- CP-SAT is USED in exactly ONE file: throughput-lab/hp/backends/cpsat.py — to_cpsat(ConfigSpace) builds a CpModel mirroring an IR, enumerate(enumerate_all_solutions=True) projects each solution and collapses the joint symmetry orbit to a lex-min canonical key; CP-SAT is 'the primary enumerator', the grid backend (Oracle B) cross-checks. This IS the declarative hyperparameter sweep.
- cvxpy is USED in exactly ONE file: tools/analysis/leaf_eval_bound/alloc/driver.py (the leaf-eval allocation / throughput lower-bound convex program).
- Test entry point: `PYTHONPATH=. /home/bork/w/vdc/venvs/generic/bin/python -m pytest tests/ -q` (CLAUDE.md:160-161). leaf_eval_bound ships its own runners (throughput_bound.py, transport_sweep.py, untrusted_drive.py) + a self-contained MANUAL.md/GLOSSARY.md pair that defers numeric values to grounding.py (their SSOT).
- Redis roles (chocofarm): 6380 volatile-lru = worker transport (az/parallel.py); 6379 noeviction disk-persisted = hp registry (hp/registry.py); facts in chocofarm/config.py (CLAUDE.md:162-167). These ROLES differ from omega's same ports — a cross-project registry MUST namespace by project.
- Experiment/TB roots differ from omega: chocofarm uses ~/w/vdc/chocobo/runs/ + ~/w/vdc/chocobo/tb/az/ (port 6006), gitignored; omega uses /home/bork/w/vdc/tensorboard/. 'Never discard experiment output — preserve under ~/w/vdc, not /tmp' (CLAUDE.md:168-172).
- Host: 4-vCPU libvirt VM; pin `--cores 0,1,2,3` (~1.9x ceiling); ptrace_scope=1 means py-spy cannot attach — use PYTHONFAULTHANDLER=1 + kill -ABRT for thread tracebacks (CLAUDE.md:173-176).
- chocofarm git rule DIVERGES from autoharn/omega: 'stage by explicit path, NEVER git add -A'; commits end Co-Authored-By: Claude Opus 4.8; pushing session-born branches needs the maintainer's explicit consent (an automated guardrail refuses otherwise) (CLAUDE.md:179-182).

## Existing mechanisms (reuse, don't reinvent)

| Mechanism | What it does | Location |
|---|---|---|
| **hp/backends/cpsat.py — CP-SAT enumerate-all + orbit canonicalizer** | Lowers a ConfigSpace IR to an ortools CpModel, enumerates ALL solutions, collapses symmetry orbits to a lex-min canonical key; CP-SAT is the primary enumerator with a grid oracle (Oracle B) cross-check. The working proof that OR-Tools is a blessed, in-use provable tool — a flagship registry row AND a Pillar-3 gate candidate (the 'same config' orbit invariant is decidable). | `/home/bork/w/vdc/1/chocofarm/throughput-lab/hp/backends/cpsat.py` |
| **docs/design/stall-investigation/* — the Z3 formal-model corpus** | 26 Z3/SMT scripts proving concurrency properties (admissibility, FIFO, starvation, inflight<=1, drain) of the throughput stall — the 'provable beats statistical hunch' practice, already realized. Should be registered as a blessed METHOD (formal modeling) with these as exemplars. | `/home/bork/w/vdc/1/chocofarm/docs/design/stall-investigation/{formal,blind-model,blind-model-v2}/` |
| **tools/analysis/leaf_eval_bound — self-documenting OR tool (cvxpy)** | A throughput lower-bound tool (convex allocation via cvxpy) with a Stand-Alone-Principle MANUAL.md + GLOSSARY.md that carry every contract and defer numeric values to grounding.py (the value SSOT). The template for how a registry entry should carry its own how-to-invoke + what-it-proves. | `/home/bork/w/vdc/1/chocofarm/tools/analysis/leaf_eval_bound/{MANUAL.md,GLOSSARY.md,alloc/driver.py,runners/}` |
| **CLAUDE.md 'Operational facts' block** | The closest thing to a capability SSOT today: interpreter path, redis roles, experiment roots, host/pinning, git rule — but as PROSE, unqueryable, and partial (it names the interpreter, not the z3/ortools/cvxpy stack inside it). | `/home/bork/w/vdc/1/chocofarm/CLAUDE.md:153-182` |

## Gaps (where the haphazardness lives)

- No dependency manifest exists (pyproject is mypy-only); the ONLY record that z3/ortools/cvxpy/sympy/scipy/networkx exist is the venv's installed set — discoverable only by running `pip list`, which no agent does unprompted.
- The blessed PRACTICES are siloed: Z3-for-formal-concurrency-modeling lives in a docs/design investigation dir; CP-SAT-for-config-enumeration in one hp backend; cvxpy in one alloc driver. A cold agent sees none and defaults to the statistical / StackExchange path.
- Installed-but-unused tools (sympy, scipy.optimize, networkx) are pure latent intent — blessed by presence, reachable by no signal. The maintainer's 'projection of intent' complaint, made concrete.
- No what-it-PROVES metadata anywhere: even where a tool is used, nothing states 'reach for Z3 for an admissibility/feasibility proof' vs 'CP-SAT for finite-domain enumeration' vs 'cvxpy for a convex allocation'. The agent must already know the task-shape -> tool mapping.
- Cross-project COLLISION risk: chocofarm and omega reuse the same redis ports for DIFFERENT roles and use different TB/experiment roots and different git rules — a single registry will mis-answer unless it namespaces by project.

## Harness hooks (where a registry / ledger / logic-gate plugs in)

- Seed Pillar-1 rows from `pip list` of each venv (generic, kataproxy) plus a per-solver probe: row(z3, solver/SMT, generic, invoke=`from z3 import Solver`, probe=`.../python -c 'import z3'`, proves='feasibility/UNSAT, admissibility, safety/starvation invariants — exact'); same for ortools and cvxpy; and an EXPLICIT row for installed-but-unused sympy/scipy.optimize/networkx so 'blessed & available' is a queryable fact, not latent.
- Register blessed METHODS, not just libs: a 'formal-modeling (Z3)' capability whose exemplars point at docs/design/stall-investigation/*; a 'declarative config sweep (CP-SAT)' capability pointing at hp/backends/cpsat.py; a 'convex throughput bound (cvxpy)' capability pointing at the leaf-eval alloc driver. The what-it-proves column IS the eliciting mechanism the maintainer wants ('ask, don't wait to be told').
- Make the registry the answer to 'is there a blessed/provable tool for THIS task?' — keyed by task-shape (feasibility -> z3; finite enumeration -> cp_model; convex alloc -> cvxpy; symbolic -> sympy; graph -> networkx) so an independent engineer reaches for it as a reflex instead of being instructed.
- Lift the CP-SAT / leaf-eval obligations into Pillar-3 gates: cpsat.py's orbit-canonical 'same config' invariant and the Criterion partition are decidable — register them as obligations a solver discharges, writing a provable pass/fail back to the ledger.
- Namespace the registry by project (chocofarm vs omega) so the colliding redis-port ROLES, the divergent TB/experiment roots, and the divergent git rules (chocofarm 'never git add -A' vs autoharn) are each answered correctly per-project.

## Anchors (attribution)

| Claim | Where |
|---|---|
| z3 4.16.0, ortools 9.15.6755 (cp_model OK), cvxpy 1.9.1, sympy 1.14.0, scipy 1.17.1, networkx 3.6.1, jax 0.10.1, numba 0.65.1, optax 0.2.8 all import in the generic venv (Python 3.13.13) | `/home/bork/w/vdc/venvs/generic/bin/python — imports verified 2026-06-27` |
| pyproject.toml is [tool.mypy] config only; chocofarm is 'unpackaged'; the venv is the de-facto SSOT named in one CLAUDE.md line | `/home/bork/w/vdc/1/chocofarm/pyproject.toml:1; CLAUDE.md:159-161` |
| Z3 used in 26 formal-model scripts (2 `import z3` + 24 `from z3`) under the stall investigation | `/home/bork/w/vdc/1/chocofarm/docs/design/stall-investigation/{formal,blind-model,blind-model-v2}/*.py` |
| CP-SAT is the primary enumerator: to_cpsat(ConfigSpace) + enumerate_all_solutions + lex-min orbit canonicalization; grid backend cross-checks | `/home/bork/w/vdc/1/chocofarm/throughput-lab/hp/backends/cpsat.py:1-30` |
| cvxpy used in exactly one file — the leaf-eval allocation driver | `/home/bork/w/vdc/1/chocofarm/tools/analysis/leaf_eval_bound/alloc/driver.py` |
| sympy / scipy.optimize / networkx installed but used in ZERO chocofarm source files | `grep census over chocofarm/**/*.py (excl. venvs, __pycache__), 2026-06-27` |
| chocofarm git rule diverges: stage by explicit path, NEVER `git add -A`; pushing session branches needs explicit consent | `/home/bork/w/vdc/1/chocofarm/CLAUDE.md:179-182` |


---
*This report was **hand-authored** by the assistant (claude-opus-4-8[1m]), 2026-06-27 — NOT produced by the reader workflow. The `choco/tool-venv-surface` structured-output reader exceeded its retry cap (5 failed calls) on BOTH the original run and a dedicated backfill run (`wf_ead2d79d-647`), so the inventory was gathered directly (verified venv imports + a grep use-site census) and written in the same schema as reports 01–09. Anchors cite `file:line/section` in the source projects.*
