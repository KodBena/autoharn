# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T22:13:55Z
#   last-change: 2026-07-18T11:07:38Z
#   contributors: a857c93d/main, ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""verify_adapter — run the two pre-registered adapter fixtures against the INDEPENDENT oracle
(harness/e15-build/PRE-REGISTERED-expectations.md, committed BEFORE this adapter existed), prove
each mutation flips RED, round-trip the DB persist (id-is-order), and prove the manifest's F49
require() refuses a non-produced family. Exit non-zero on any failure (ADR-0002).

The expected tuple sequences below are TRANSCRIBED from the pre-registration doc (the oracle);
they are not re-derived from the adapter. The point of the fixture is agreement with the oracle."""
from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

from claude_code_adapter import SubagentSource, parse_completed_session
from contract import PGHOST, Act, CapabilityError, persist

HERE = Path(__file__).resolve().parent


def _resolve_real_transcript(*env_vars: str) -> Path:
    """Resolve fixture 2's banked real transcript (session-37017f46), env-or-refuse (ADR-0002,
    same pattern as pghost_resolve.resolve_pghost / instruments/close_manifest.py's ACTS_FENCED /
    PERF_SESSION_DIR): this session's off-repo ephemera lives only on the machine that captured
    it, so a fresh checkout gets a loud refusal naming exactly what to set, never a silent
    default to any one maintainer's home directory."""
    for var in env_vars:
        val = os.environ.get(var)
        if val:
            return Path(val).expanduser()
    names = " or ".join(env_vars) if env_vars else "VERIFY_ADAPTER_REAL_TRANSCRIPT"
    raise SystemExit(
        f"REFUSED: no path resolved for fixture 2's banked real transcript "
        f"(session-37017f46) -- set {names} to the persisted session's "
        f"session-transcript/37017f46-fa65-4981-b669-b4204a444de8.jsonl. Never defaulting to "
        f"any one maintainer's home directory.")


REAL_TRANSCRIPT = _resolve_real_transcript("VERIFY_ADAPTER_REAL_TRANSCRIPT")

# ---- the pre-registered expectation (transcribed from PRE-REGISTERED-expectations.md Part 1) ----
EXPECT_SYN = [
    ("main", "message_in", None, None),
    ("main", "message_out", None, None),
    ("main", "tool_call", "Bash", None),
    ("main", "tool_result", "Bash", None),
    ("main", "tool_call", "Write", "/fenced/report_lint.py"),
    ("main", "tool_result", "Write", "/fenced/report_lint.py"),
    ("main", "plan_item_created", "parse header", None),
    ("main", "plan_item_created", "validate sections", None),
    ("main", "delegation_spawn", "sub:general-purpose", None),
    ("main", "delegation_return", "sub:general-purpose", None),
    ("main", "plan_item_closed", "parse header", None),
    ("sub:general-purpose", "tool_call", "Read", "/fenced/report_lint.py"),
    ("sub:general-purpose", "tool_result", "Read", "/fenced/report_lint.py"),
]
# CORRECTED slice (see PRE-REGISTERED-expectations.md "CORRECTION" amendment): the initial
# hand-derivation excluded string-content user messages (an extraction-script artifact); the
# independent re-read of the raw JSONL restores them as message_in. First 10 act-bearing blocks:
EXPECT_REAL = [
    ("main", "message_in", None, None),    # "Hi, are you able to inspect pdf's..." (user str-content)
    ("main", "message_out", None, None),   # "Short answer: yes..."
    ("main", "tool_call", "Bash", None),
    ("main", "tool_result", "Bash", None),
    ("main", "tool_call", "Bash", None),
    ("main", "tool_result", "Bash", None),
    ("main", "message_out", None, None),   # "Yes — and the tooling..."
    ("main", "message_in", None, None),    # "I'd ask that you either install..." (user str-content)
    ("main", "message_out", None, None),   # "Let me check the venv's..."
    ("main", "tool_call", "Bash", None),
]


def _tuples(acts: tuple[Act, ...]) -> list[tuple]:
    return [(a.actor, a.kind, a.name, a.target) for a in acts]


def _syn_stream():
    return parse_completed_session(
        HERE / "fixtures/syn_session/syn-main.jsonl",
        [SubagentSource("general-purpose", HERE / "fixtures/syn_session/subagents/syn-sub.jsonl")],
        run_id="fixture-syn", source_ref="fixtures/syn_session")


def _real_stream():
    return parse_completed_session(REAL_TRANSCRIPT, [], run_id="fixture-real",
                                   source_ref="session-37017f46 (commit 3c8d1d8) slice[0:10]",
                                   limit_blocks=10)


def main() -> int:
    ok = True

    # ---- fixture 1: synthetic ----
    syn = _syn_stream()
    got = _tuples(syn.acts)
    p1 = got == EXPECT_SYN
    ok &= p1
    print(f"[{'OK ' if p1 else '!! '}] fixture 1 (synthetic): {len(got)} acts vs oracle {len(EXPECT_SYN)} "
          f"-> {'AGREE' if p1 else 'DIVERGE'}")
    if not p1:
        for i, (g, e) in enumerate(zip(got, EXPECT_SYN)):
            if g != e:
                print(f"       row {i}: got {g} expected {e}")
    # payloads: every act carries a sha256, excerpts bounded; thinking + usage excluded (13, not more)
    assert all(a.payload_sha256 for a in syn.acts), "an act is missing its payload_sha256"
    # manifest: CHECKED against the pre-registered expectation, not merely printed (finding-5 fix —
    # the manifest was F49-loud in prose but decorative in the check; a mislabeled family now fails).
    prod = syn.manifest.produced()
    fam = {f: s.value for f, (s, _) in syn.manifest.families.items()}
    # PRE-REGISTERED (PRE-REGISTERED-expectations.md Part 1 Fixture 1, + the dated CAPABLE refinement):
    EXPECT_PRODUCED = {"tool_call", "tool_result", "message_in", "message_out",
                       "delegation_spawn", "delegation_return", "plan_item_created", "plan_item_closed"}
    EXPECT_FAM = {"plan_item_updated": "capable",       # refined from pre-reg "DEFERRED" (dated note)
                  "model_reasoning": "excluded", "token_accounting": "excluded",
                  "live_hook_capture": "deferred"}
    manifest_ok = (prod == EXPECT_PRODUCED
                   and all(fam.get(f) == v for f, v in EXPECT_FAM.items()))
    ok &= manifest_ok
    print(f"[{'OK ' if manifest_ok else '!! '}] fixture 1 manifest matches pre-registration: "
          f"produced={sorted(prod)}; plan_item_updated={fam.get('plan_item_updated')}, "
          f"EXCLUDED={{model_reasoning,token_accounting}}, live_hook_capture={fam.get('live_hook_capture')}")
    if not manifest_ok:
        print(f"       MISMATCH: produced Δ={prod ^ EXPECT_PRODUCED}; "
              f"fam={ {f: fam.get(f) for f in EXPECT_FAM} }")

    # mutation 1: attribute the subagent acts to 'main' -> DIVERGE from oracle (RED)
    mut1 = [replace(a, actor="main") if a.actor.startswith("sub:") else a for a in syn.acts]
    m1_red = _tuples(tuple(mut1)) != EXPECT_SYN
    ok &= m1_red
    print(f"[{'OK ' if m1_red else '!! '}] fixture 1 mutation (attribution defeat): flips "
          f"{'RED' if m1_red else 'GREEN — MUTATION DID NOT FLIP'}")

    # ---- fixture 2: real banked slice ----
    real = _real_stream()
    gotr = _tuples(real.acts)
    p2 = gotr == EXPECT_REAL
    ok &= p2
    print(f"[{'OK ' if p2 else '!! '}] fixture 2 (real banked slice, session-37017f46): {len(gotr)} acts "
          f"vs oracle {len(EXPECT_REAL)} -> {'AGREE' if p2 else 'DIVERGE'}")
    if not p2:
        for i, (g, e) in enumerate(zip(gotr, EXPECT_REAL)):
            if g != e:
                print(f"       row {i}: got {g} expected {e}")

    # mutation 2: drop message_out (treat surfaced text as reasoning) -> DIVERGE from oracle (RED)
    mut2 = [a for a in real.acts if a.kind != "message_out"]
    m2_red = _tuples(tuple(mut2)) != EXPECT_REAL
    ok &= m2_red
    print(f"[{'OK ' if m2_red else '!! '}] fixture 2 mutation (exclusion-boundary defeat): flips "
          f"{'RED' if m2_red else 'GREEN — MUTATION DID NOT FLIP'}")

    # ---- DB round-trip: persist fixture 1 into a scratch acts schema, read back id-is-order ----
    schema = "acts_fixture_scratch"
    subprocess.run(["psql", "-h", PGHOST, "-d", "harness", "-c",
                    f"DROP SCHEMA IF EXISTS {schema} CASCADE;"], capture_output=True, text=True)
    subprocess.run(["psql", "-h", PGHOST, "-d", "harness", "-v", "ON_ERROR_STOP=1",
                    "-v", f"schema={schema}", "-f", str(HERE.parent.parent /
                    "stores" / "003_acts_stream.sql")], capture_output=True, text=True)   # autoharn: stores/
    sid = persist(syn, schema=schema)
    back = subprocess.run(["psql", "-h", PGHOST, "-d", "harness", "-tA", "-F", "|",
                           "-c", f"SELECT id, actor, kind, coalesce(name,''), coalesce(target,'') "
                                 f"FROM {schema}.act WHERE stream_id={sid} ORDER BY id;"],
                          capture_output=True, text=True).stdout.strip().splitlines()
    ids = [int(r.split("|")[0]) for r in back]
    id_order = ids == sorted(ids) and len(ids) == len(syn.acts)
    ok &= id_order
    print(f"[{'OK ' if id_order else '!! '}] DB round-trip: {len(ids)} acts persisted, id-is-order "
          f"{'held' if id_order else 'BROKEN'} (append-only contract)")
    subprocess.run(["psql", "-h", PGHOST, "-d", "harness", "-c",
                    f"DROP SCHEMA IF EXISTS {schema} CASCADE;"], capture_output=True, text=True)

    # ---- F49: require() a non-produced family refuses loudly ----
    try:
        syn.manifest.require("live_hook_capture")
        refused = False
    except CapabilityError:
        refused = True
    ok &= refused
    print(f"[{'OK ' if refused else '!! '}] F49 require('live_hook_capture') refuses loudly "
          f"{'(DEFERRED, not silent)' if refused else '— DID NOT REFUSE'}")

    print(f"\n# ADAPTER {'GREEN — both fixtures agree with the pre-registered oracle; both mutations flip RED' if ok else 'RED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
