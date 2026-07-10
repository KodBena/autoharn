# Reading a judge verdict

Operator/orchestrator doc for `./judge` (runs `bootstrap/templates/judge.tmpl` →
`engine/ledger_differential.py --retain` against the calling project's own
`deployment.json`). Detecting a red verdict is covered elsewhere (CAPABILITIES.md,
OPERATING-CARD.md); this is the missing next step — how to see *what* diverged,
without reading engine source. Commands below ran live against this repo's own
`toy`/`run3` targets on 2026-07-11; output is quoted verbatim and marked WITNESSED.
One case is marked UNWITNESSED.

## 1. What the two sides compute

Every target's ledger is judged by two *independent* producers over the same facts;
the differential (`engine/ledger_differential.py`) checks they agree bit-for-bit.
**The SQL floor** (`ledger_floor.py`), producer one: Postgres recursive CTEs
computing the monotone parts (supersession closure, in-force/head resolution)
directly off the *live* DB rows — "SQL's home turf." **The ASP/clingo derivation**
(`ledger_tnow.lp`), producer two: the same judgments plus the non-monotone parts
(defaults-and-exceptions closure over clause-defeaters), computed by
grounding-and-solving over a serialized text export of the same ledger (the EDB).
Different engines, different code paths, the same underlying facts by two routes —
agreement is evidence the encoding is trustworthy, not an assumption.

## 2. The four verdicts

**AGREE** — empty symmetric difference: `only_asp` and `only_sql` are both `[]`, both
DerivationRecords are present, neither producer quarantined. Not a TYPED escalation
event. Operator's next move: none required; `./judge` already banked the pair with
`--retain` if you want the artifact later.

**DIVERGE_BY_DESIGN** — divergence confined to a *declared* defeater-lens set (a
named, expected disagreement). **UNWITNESSED as a live outcome**: `verdict()`'s
current code (`ledger_differential.py:183-192`) has no branch returning it — its own
comment says why: *"no defeater-lens is declared this increment; any Δ is a
defect."* Any divergence today is `DIVERGE_DEFECT`, never this; if it ever appears,
an engine-layer spec declared a new lens and the code changed under this doc.

**DIVERGE_DEFECT** — an undeclared divergence: `only_asp` and/or `only_sql` is
non-empty. TYPED escalation event (CLAUDE.md ORCHESTRATION: "Escalate on TYPED
events (gate-refusal streaks, DIVERGE_DEFECT/QUARANTINED, …), never on
self-assessment"). Operator's next move: do not hand-patch `ledger_tnow.lp` or
`ledger_floor.py` — both sit inside the engine/lp boundary CLAUDE.md reserves for a
Fable-authored, maintainer-ratified spec. Diagnose per §3, write up, route it.

**QUARANTINED** — NO RESULT: a producer crashed, produced zero atoms over a
non-empty EDB (the F49 silent-non-run guard), or either DerivationRecord is missing.
Never read as a pass. TYPED escalation event (same CLAUDE.md line as above).
Operator's next move: read the printed `asp QUARANTINED: …` / `sql QUARANTINED: …`
line (§4) — it names the concrete reason — before touching anything.

## 3. Diagnosing DIVERGE_DEFECT

**Where the banked pair lives.** Every `--retain` run banks a run-unique directory
`engine/docs/ledger-marriage/derivations/<target>/<UTC-ts>_<input-hash[:12]>/`
(never a single mutable slot — a later run cannot clobber an earlier one). A real
one on disk, `.../toy/20260709T112043Z_f6816fb75951/`, holds `edb.lp` (the EDB
text), `asp_atoms.txt` / `sql_atoms.txt` (each producer's sorted atom set), and
`derivation.json` (the two `DerivationRecord`s plus `only_asp`/`only_sql`). That
record's verdict is `AGREE` — every banked record in this repo today is AGREE, so a
genuine DIVERGE_DEFECT is not on disk to quote. To ground the diagnosis anyway, this
doc reproduced one live (WITNESSED this session; no files retained or committed):

```
$ python3 -c "
import ledger_differential as D
edb = D.export('toy').edb_text()
mutated = '\n'.join(l for l in edb.splitlines() if l.strip() != 'amends(17,1).')
override = D.run_asp('toy', mutated).atoms
res = D.run_differential('toy', edb_text=None, asp_atoms_override=override)
print('verdict:', res.verdict())
print('only_asp:', sorted(res.only_asp))
print('only_sql:', sorted(res.only_sql))
"
verdict: DIVERGE_DEFECT
only_asp: []
only_sql: ['clause_defeat(17,1)']
```

This drops the real edge `amends(17,1).` (present in the banked `toy` EDB, entry 17
clause-defeating entry 1) from *only* the ASP side's input text, leaving the SQL
floor reading the unmutated live DB — the same technique as
`test_ledger_marriage.py::test_single_producer_mutation_is_diverge_defect`'s own
negative control. It is a manufactured single-producer mutation, not an actual
defect present in the repo today.

**Reading Δasp/Δsql.** `only_asp` = atoms the ASP side produced that SQL did not
(ASP over-derived). `only_sql` = atoms SQL produced that ASP did not (ASP
under-derived, or ASP is missing input SQL still has). The example above is the
second shape: `only_sql=['clause_defeat(17,1)']`, `only_asp=[]`.

**Telling the three causes apart**, given that shape (adapt symmetrically for the
`only_asp`-non-empty shape):

- **ASP-encoding bug** — the rule for the diverging predicate in `ledger_tnow.lp` is
  wrong (a missing body literal, a `not` in the wrong place). Check: does
  `ledger_tnow.lp`'s rule for that predicate (e.g. `clause_defeat`) match the
  corresponding CTE in `ledger_floor.py` line for line, given the *unmutated* EDB
  both sides should have received?
- **Stale-view / export artifact** — `ledger_edb.py`'s `export().edb_text()` is out
  of sync with the live DB (a fact family the schema now carries but the export
  doesn't emit, or an export taken at a different moment than the SQL query ran).
  Exactly the shape manufactured above: the ASP side's *input text* was missing a
  fact the live DB still has, so SQL (`input_basis: "live-db rows read directly"`)
  still saw it and ASP (`input_basis: "edb-text (ledger_edb export, serialized)"`)
  did not. Check: does the current `edb.lp` carry every fact family the live DB has?
- **Kernel bug** — a genuine defect in the underlying ledger data/lineage itself.
  The differential is structurally blind to this: both producers read from the same
  true source (directly or via export), so a kernel-level defect both honestly
  reflect shows as AGREE-on-a-wrong-answer, not a divergence. A DIVERGE_DEFECT thus
  rules kernel-data corruption *out* as the cause of the specific Δ atoms shown —
  a shared-input defect cannot make the two producers compute different things.

## 4. QUARANTINED in detail

Three distinct code paths all bank the one `QUARANTINED` verdict (`verdict()`,
`ledger_differential.py:183-189`): either producer's `.quarantine` field is set
(crash, missing program file, or the F49 zero-atoms-over-nonempty-EDB guard), or
either producer's `.record` is `None` (a lost DerivationRecord). Live witnessed
example (this session), the documented `--drop-record` negative control from
`judge.tmpl`'s own usage comment:

```
$ python3 ledger_differential.py --drop-record toy
  [!! ] toy    QUARANTINED        asp=124 sql=124 atoms; Δasp=[] Δsql=[]

# DIFFERENTIAL RED -- a target diverged/quarantined (NO RESULT)
```

Atom counts are non-zero and equal (124/124 — the two sides genuinely agreed):
QUARANTINED here is purely "the witness is missing," not "the answer was wrong."
**Provably distinct from "passed":** `verdict()` checks quarantine/missing-record
*before* it checks the atom sets, so `AGREE` is reachable only past that gate — a
run cannot land on AGREE by omission. **To see which** producer quarantined and why,
read the `asp/sql QUARANTINED: …` line `print_result` emits under the verdict line
(reason string, e.g. `"clingo failed: …"`, `"…ZERO atoms over a non-empty EDB…"`,
`"SQL floor failed: …"`), or `derivation.json`'s `asp_quarantine`/`sql_quarantine`.

## 5. Five minutes, judge is red

1. Read the printed line: `[!! ] <target> <VERDICT> asp=N sql=M atoms; Δasp=[...] Δsql=[...]`.
2. QUARANTINED → read the `asp/sql QUARANTINED: <reason>` line right under it. Stop
   there; there is no atom diff to chase, only a missing witness or a crash.
3. DIVERGE_DEFECT → open the newest
   `engine/docs/ledger-marriage/derivations/<target>/<ts>_<hash>/derivation.json`
   for the two DerivationRecords' `input_hash`/`program_hash`/`ts`.
4. `only_sql` non-empty, `only_asp` empty → suspect a stale ASP export or an
   under-firing `.lp` rule (§3). Reverse for `only_asp` non-empty.
5. This is a TYPED escalation event either way (CLAUDE.md ORCHESTRATION) — do not
   hand-edit `ledger_tnow.lp`/`ledger_floor.py`; route the finding to a
   Fable-authored, maintainer-ratified spec.
