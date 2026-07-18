subject: 455d97c,76543a7,5a5acef,e22a65a,1eacf76
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

Five deliveries landed close together in the 2026-07-18 overnight batch (decision rows
1580/1585, tracker parent `post-freeze-documentation-debt`), none of which had a changelog
note until now: a protective watchdog-liveness harness, a fix for maintainer-home-directory
path literals in three instruments, three pre-existing layout-census registration gaps closed
at a merge seam, a fixture-census tightening from present-on-disk to git-tracked, and a
DB-free unit test pinning the acts-manifest SSOT invariant. **None is a kernel/lineage delta**
— every item below is code, tests, or gate logic on the harness side; nothing here needs
`./migrate` and no world's scaffold changes because of this note.

**Watchdog-liveness harness (builder `4d679e0`, fixer `a14e78a`, merge `455d97c`; ledger
decision row 1595; work items `watchdog-liveness-harness`/`watchdog-mode-field-inert`, closed
rows 1596/1598 and 1597/1599).** `tools/watchdog_liveness.py` is a new, read-only diagnostic
that answers one question — has a dispatched Bash command, subagent, or the deployment's
own journal set gone quiet longer than its expected-duration-times-slack — for the observe
rung only (`mode` is presently INERT; `warn`/`enforce` are unbuilt). Full design, taxonomy,
and reach limits: [design/ORCH-WATCHDOG-LIVENESS.md](../design/ORCH-WATCHDOG-LIVENESS.md). The
build shipped in two acts: `4d679e0` implemented the checker and its fixtures, but a fresh
independent review caught the Class-1 Bash-dispatch pairing joining on a field the completion
journal never writes — every completed dispatch reported open forever, masked because both
fixture polarities' completion journals were empty (the same regression class
[design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md](../design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md)
documents); `a14e78a` fixed the join to key on `tool_use_id`, added the M2
mechanism-dead tripwire (one typed finding when ≥20 eligible dispatches have zero paired
completions, instead of flooding per-dispatch questions), and a second fresh review returned
CLEAN. WITNESSED (re-run live for this note, unchanged since the fixed transcript in the
design doc's own §4):

```
$ python3 tools/watchdog_liveness.py --root seen-red/watchdog-liveness/fixtures/stale --now 2026-07-13T12:10:00Z
=== BASH DISPATCHES ===
LIVENESS QUESTIONS RAISED: 1 open dispatch(es), 1 liveness question(s)
LIVENESS QUESTION: bash dispatch b2c3d4e5 has shown no observable activity for 596.0s against an expected 0.1s x10.0 +1.0s -- look here.
=== SUBAGENT DISPATCHES ===
LIVENESS QUESTIONS RAISED: 1 open dispatch(es), 1 liveness question(s)
LIVENESS QUESTION: subagent dispatch sess-sta has shown no observable activity for 600.0s against an expected 60.0s x3.0 +30.0s -- look here.
=== SURFACE RECENCY (all journals) ===
LIVENESS QUESTION: no journal in this deployment has recorded an event for 570.0s (warn at 300s) -- look here.
=== WORK ITEMS (ledger, best-effort) ===
SKIPPED (no deployment.json under --root; ledger check not run)
--- verdict: 3 liveness question(s) raised ---
$ echo $?
1
```

Every finding is phrased as a "LIVENESS QUESTION," never `STALE`/`HUNG`/`DEAD` as a bare
verdict — a stall this checker sees is a look-here, categorically not an estimate/cost
violation (the never-cost-policing invariant, `design/USER-RETROSPECTIVE-RECIPE.md` §6, stands
untouched). `tools/`, not `gates/`: this checker never blocks a commit; it is a diagnostic an
operator or a future `distance-to-clean` section reads.

**Maintainer-home path literals removed from three instruments (merge `76543a7`; ledger
decision row 1585; work item `instrument-home-path-literals`, opened row 1578, closed row
1592).** `instruments/cite_check.py`'s `LOG_DIR` default and
`instruments/act_stream/verify_adapter.py`'s `REAL_TRANSCRIPT` fixture path used to be silent
literal paths under one maintainer's home directory; both now resolve env-or-refuse
(`EPISTEMIC_LOG_DIR`, `VERIFY_ADAPTER_REAL_TRANSCRIPT` respectively), mirroring
`pghost_resolve.resolve_pghost`'s existing pattern (ADR-0002, fail loud rather than default
silently to one machine's layout). `instruments/ledger_target.py`'s `e16`/`e17`/`e18` registry
literals switch from an absolute `/home/...` path to `~/...`, matching that same registry's
own `e15` entry. WITNESSED — running the adapter fixture on this checkout, which has neither
env var set, now refuses loudly instead of defaulting:

```
$ python3 instruments/act_stream/verify_adapter.py
REFUSED: no path resolved for fixture 2's banked real transcript (session-37017f46) -- set VERIFY_ADAPTER_REAL_TRANSCRIPT to the persisted session's session-transcript/37017f46-fa65-4981-b669-b4204a444de8.jsonl. Never defaulting to any one maintainer's home directory.
```

If you were relying on the old silent default (unlikely — it only ever resolved on the one
machine that captured that transcript), set the named env var; there is no other behavior
change.

**Three pre-existing layout-census breaches registered (`5a5acef`; ledger decision row 1585,
"three pre-existing layout-census breaches registered", fixed at the same merge seam as the
`asof-export` item rather than left for the next run — flagged by that item's own builder).**
`gates/layout_census.py` gained three entries it should already have carried:
`otel-attest` (the OTel model-attestation verb) and
`ANTHROPIC-FEEDBACK-2026-07-17-security-recommendation-incident.md` (a root standing document,
commit `2f19f88`) as `ROOT_FILES`, and `serving/` (the FastAPI ledger boundary service, first
landed at merge `9942950`) as a `ROOT_DIRS` entry. If your world's `layout_census` gate
already flagged one of these three as unregistered, that breach is now closed — no other
behavior change. WITNESSED (re-run live for this note):

```
$ python3 gates/layout_census.py
layout-census: clean ✓  (26 registered dirs, 31 root docs; per-directory currency patterns hold). Single-currency judgment for new files is review-only.
$ echo $?
0
```

**Fixture-census tightened from present-on-disk to git-tracked (merge `e22a65a`; ledger
decision row 1585; work item `fixture-census-tracked-targets`, opened row 1503, closed row
1589).** Class net from an s45 adversarial review's blocking finding (ledger row 1502):
commit `94f5b7a` had bundled a `fixture_census` registry row for `defeat-pipeline` before those
files were committed, and a concurrent sibling builder's *uncommitted* hunk in the same shared
working tree made the fixture read present-on-disk — so the pre-fix census (presence-only)
read GREEN on a commit that, on a clean checkout, was actually RED. `gates/fixture_census.py`
now additionally verifies every registry target (the `seen-red/<dir>`, its red-evidence file,
and its registered fixture) is `git ls-files`-tracked, not merely present on disk; a negative
control in `seen-red/fixture-census/red-specimen.py` creates a real, deliberately-never-added
probe directory and confirms the gate reports the specific UNTRACKED breach, cleaning up after
itself. `seen-red/s45-standing-lifecycle/run_fixtures.py` also gained the fixture-census leg
its own spec had listed but the harness never invoked — the mechanical root cause the s45
review adjudicated. If your world's `fixture_census` gate previously read GREEN on an
uncommitted registry target in a shared worktree, it now reads RED for exactly that case;
every git-tracked registration is unaffected. WITNESSED (re-run live for this note):

```
$ python3 gates/fixture_census.py
fixture-census: clean ✓  (115 seen-red gates, each with banked red evidence and a registered runnable fixture). Live red-re-execution is the acceptance gate (§6).
$ echo $?
0
```

**Acts-manifest F50 SSOT pinned by a DB-free unit test (merge `1eacf76`; ledger decision row
1585; work item `acts-manifest-ssot-import-time`, opened row 1576, closed row 1590).** Closes
the deferred half of an earlier out-of-frame review (`engine-tests-ledger-acts-drift`,
2026-07-14): `acts_edb.acts_manifest()`'s `set(m) == set(ACTS_PREDS)` invariant was only ever
checked call-time, inside a live-fixture-backed test that asserts a superset — if a future
consumer path stops calling `acts_manifest()` every run, drift detection goes silent again.
`engine/tests/test_ledger_acts.py` gains
`test_manifest_key_set_exactly_matches_acts_preds_db_free`, which monkeypatches
`Target.has_relation`/`has_col` to force every family onto the DEFERRED branch (no `psql` call,
no scratch-fixture build via `las.setup()`) and asserts literal set equality against
`ACTS_PREDS` — the standalone, always-run pin the original ledger item asked for. WITNESSED
(re-run live for this note):

```
$ python3 -m pytest engine/tests/test_ledger_acts.py -k "manifest_key_set_exactly" -v
engine/tests/test_ledger_acts.py::test_manifest_key_set_exactly_matches_acts_preds_db_free PASSED [100%]
======================= 1 passed, 6 deselected in 0.06s ========================
```

Migration: none for any of the five — no kernel delta, nothing for `./migrate` to plan. The
five commits chain in this order on `main`: `e22a65a` → `1eacf76` → `76543a7` → `5a5acef` →
`455d97c` (each an ancestor of the next, confirmed via `git merge-base --is-ancestor`), so a
checkout on `455d97c` or later already has all five.
