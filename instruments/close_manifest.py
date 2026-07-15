#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T22:13:36Z
#   last-change: 2026-07-14T22:13:43Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""close_manifest — the loud, complete run-close verification runner.

ADR-0015 Rule 3/4 + ADR-0016, made concrete. Before this manifest the close-sweep was a bare
sequence of instrument calls: when `close_sweep.py` crashed on `nla` (kernel.principal absent) the
mandatory R3b/condition-1/condition-3 lines produced NOTHING and the silence read as a clean close
(link 21 F49). A non-run is not a pass; it is NO RESULT, and must be quarantined LOUDLY.

The class this forecloses (ADR-0000 Rule 2a): "a mandatory close line silently did not run, or ran
against the wrong / commingled substrate, and its absence read as clean." The type that closes it is
a MANIFEST that (1) enumerates every mandatory close line, (2) runs each and records
{OK | QUARANTINED(reason)} — an exception or non-zero exit is QUARANTINED, never dropped, (3)
DECLARES the substrate each line read (the database, and the gate journal's window + repo span, so a
commingled journal is a printed warning, not a silent corruption — ADR-0015 Rule 4), and (4) EXITS
NON-ZERO if any mandatory line is quarantined, so a broken close cannot be mistaken for a clean one.

Closure statement:
  - invariant: every mandatory close line reports a status; a non-run is QUARANTINED and turns the
    whole close red; the substrate (db + journal window + repo span) is declared, never assumed.
  - quantification universe: the mandatory close set {soundness, observed_currency, contemporaneity,
    close_sweep, stale_enactment_debt}; axes {ran/crashed, substrate-declared, journal-commingled}.
  - denomination: "clean close" is denominated in "every mandatory line ran on the declared,
    single-run substrate", never in "the sweep printed something".

Usage: close_manifest.py <target> [--log=PATH ...] [--journal=PATH]
"""
from __future__ import annotations

import contextlib
import glob
import hashlib
import io
import json
import os
import re
import subprocess
import sys
from collections import Counter
from typing import NamedTuple

import review_queue as _review_queue
import soundness as _soundness
import stale_enactment_debt as _sed
from ledger_target import resolve
from pghost_resolve import resolve_pghost
from review_without_detail import atoms_for as _review_without_detail_atoms

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)   # autoharn: consumers are now repo-local (engine/, gates/), not cross-repo
DEFAULT_LOG_GLOB = "/home/bork/pg_log/tee.log"
DEFAULT_JOURNAL = os.path.expanduser("~/w/vdc/1/epistemic-audit/logs/change_gate.journal.jsonl")


def _instrument_argv(module: str, target: str, logs: list[str], journal: str) -> list[str]:
    """The argv for one close line. Each instrument takes the target name; the log/journal consumers
    take theirs. One home for how each mandatory line is invoked (no scattered call sites)."""
    base = [sys.executable, os.path.join(HERE, f"{module}.py")]
    if module in ("observed_currency", "close_sweep"):
        return base + [f"--log={p}" for p in logs] + [target]
    if module == "stale_enactment_debt":
        return base + [f"--journal={journal}", target]
    return base + [target]  # soundness, contemporaneity


# The MANDATORY close set — every line here must run clean or the close is red. (review_queue and
# derive_trail are diagnostic, not part of the pass/fail close; add here only what gates the close.)
MANDATORY = ["soundness", "observed_currency", "contemporaneity", "close_sweep", "stale_enactment_debt"]

# DECLARED OBSERVER lines (AC7, link-24 marriage increment 1) — in the accounting so a non-run is
# VISIBLE, but NOT (yet) gating the close red. Per link-23 M-2 the marriage differential earns
# mandatory status only after it has observed one e15 close (observer-first, ADR-0011: a net earns
# its gate by being seen working). Its status is reported here every close so a silent non-run is
# impossible (ADR-0015 Rule 3/4); it just does not turn the close red until promoted. The runner
# lives cross-repo (fact-mining side, read-only); it is NEVER hand-synced — a kernel/operator change
# lands as a red parity test there (design §10).
MARRIAGE_DIFFERENTIAL = os.path.join(REPO_ROOT, "engine", "ledger_differential.py")  # autoharn: repo-local engine/
# soundness_twin is the OPERATOR-side immune-system differential (soundness.lp ASP vs soundness.py
# live-psql core) — the analog of the marriage differential for the operator twins. It exists so a
# keying divergence between the two soundness encodings (the F-D hazard, 2026-07-06) can never again
# pass silently. Reported every close (never skippable, ADR-0015 Rule 3/4); observer-first (M-2), it
# does not gate this close red until promoted.
SOUNDNESS_TWIN = os.path.join(HERE, "soundness_twin.py")
DECLARED_OBSERVERS = ["marriage_differential", "soundness_twin"]

# The three e15 audit consumers (consult 25 §2.3), REGISTERED as MANDATORY close lines (A.7 / F49):
# a crashed or skipped consumer is loud, never silent (the e14 close's silent non-run is the specimen).
# They gate consumer-bearing targets (an acts stream, which e15 carries; a rehearsal mock declares its
# target via env). Until an acts stream is parsed for the run they report DEFERRED LOUDLY (never a
# silent empty) — the correct PRE-RUN state (Phase-0 readiness on the empty substrate stays green).
#
# LIVE MANDATORY (Increment 5): when a stream IS present the consumers RUN the REAL acts.act<->s15
# matching differential (the deriver acts_join.py). This REPLACES Increment-4's NOT-WIRED placeholder
# (which gated red as a deliberate "wire me" flag). A present-but-unrun consumer is impossible now: it
# RUNS, and a crash or an ASP<->SQL divergence QUARANTINES (gates red, F49/ADR-0013 R5); a DESCRIPTIVE
# finding atom is data (non-foreclosure §1.3) and does NOT gate. No silent-vacuous-pass reintroduced.
ACTS_CONSUMERS = ["stale_attestation", "claimed_without_act", "unledgered_span"]
ACTS_STREAM_DB = os.environ.get("HARNESS_DB", "harness")
ACTS_STREAM_SCHEMA = os.environ.get("ACTS_STREAM_SCHEMA", "acts")
# e15 is the standing consumer-bearing target; a rehearsal mock adds its own target via env (so no mock
# name is ever hardcoded into the instrument). One home for the acts.act<->s15 deriver (cross-repo, the
# marriage-differential idiom): a kernel/operator change lands as a red run there, never a hand-sync.
ACTS_CONSUMER_TARGETS = {"e15", "e16", "e17", "e18"} | {t for t in os.environ.get("ACTS_CONSUMER_EXTRA", "").split(",") if t}
ACTS_JOIN = os.path.join(REPO_ROOT, "engine", "acts_join.py")  # autoharn: repo-local engine/
# The row_performed_by consumer (finding 28, Increment 7): claimed-vs-performed over the subject session's
# ledger-INSERT acts. A registered close line on a consumer-bearing target; needs the SESSION DIR (the
# INSERT acts' full commands live in the transcript, not the truncated acts contract). DESCRIPTIVE atoms
# do NOT gate; a Python<->SQL DIVERGE or a crash QUARANTINES (F49).
ROW_PERFORMED = os.path.join(HERE, "row_performed_by.py")  # autoharn: repo-local instruments/


# ---- CONSUMER SUBSTRATE resolution (finding 36) -----------------------------------------------------
# The two consumer substrate pointers — the acts `--fenced` work-dir and the row_performed_by
# `--session-dir` — are TARGET-RESOLVED from the ledger_target SSOT, never a close_manifest module-global
# default. Before this, ACTS_FENCED defaulted to `~/nk4-build` (e15) and PERF_SESSION_DIR to the e15
# subject dir, so a bare `close_manifest.py e16 --mode close` measured e15's fence + e15's transcript
# against e16's ledger and every acts/perf consumer returned a VACUOUS 0/all-unbound — a silent
# wrong-substrate pass (finding 36 / F49; run B = close-e16-post-disposition.txt is the banked specimen;
# RCA close-substrate-rca-2026-07-07.md proves it line-by-line). The db/schema/actor substrate was ALWAYS
# target-resolved via ledger_target; these two pointers were the one gap. Precedence: an explicit env var
# is a LOUD override (declared in the header); else the registry; else UNREGISTERED (→ REQUIRED-ABSENT at
# close, never a silent empty).
def _resolve_fenced(target: str) -> tuple[str | None, str]:
    """Resolve the acts consumers' fenced-dir substrate for `target`. Returns (dir_or_None, source):
    ENV-OVERRIDE (ACTS_FENCED set, loud) > registry (ledger_target.fenced_dir) > UNREGISTERED (None)."""
    env = os.environ.get("ACTS_FENCED")
    if env:
        return os.path.expanduser(env), "ENV-OVERRIDE"
    fd = resolve(target).fenced_dir
    return (os.path.expanduser(fd), "registry") if fd else (None, "UNREGISTERED")


def _resolve_session_dir(target: str) -> tuple[str | None, str]:
    """Resolve the row_performed_by consumer's session-dir substrate for `target`. Returns
    (dir_or_None, source): ENV-OVERRIDE (PERF_SESSION_DIR set, loud) > registry
    (ledger_target.subject_session_dir) > UNREGISTERED (None). Same finding-36 discipline as fenced."""
    env = os.environ.get("PERF_SESSION_DIR")
    if env:
        return os.path.expanduser(env), "ENV-OVERRIDE"
    sd = resolve(target).subject_session_dir
    return (os.path.expanduser(sd), "registry") if sd else (None, "UNREGISTERED")

# The FOURTH consumer (WORK-UNIT-findings-disposition): the general findings-ledger close-gate. It goes
# RED if ANY finding is OPEN (no disposition act — F28: prose never closes a finding). An increment
# cannot report complete with undischarged findings; a real hazard debt (the TRUNCATE-CASCADE hole,
# finding 6a) is SEEN RED before anything disposes it. GLOBAL by default; FINDINGS_INCREMENT scopes it.
FINDINGS_GATE = os.path.join(REPO_ROOT, "gates", "findings_gate.py")  # autoharn: repo-local gates/


def _journal_substrate(journal: str) -> tuple[str, list[str], tuple[str, str] | None]:
    """Declare the gate journal's substrate: the repos it references and its entry_ts window. A
    journal spanning >1 subject repo is COMMINGLED (not reset between runs) — a loud warning, because
    an instrument joining it against one run's ledger silently mixes runs (the e14 finding)."""
    repos: set[str] = set()
    times: list[str] = []
    try:
        for line in open(journal, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            f = r.get("file") or ""
            for part in f.split(os.sep):
                if part.startswith("epistemic-"):
                    repos.add(part)
                    break
            if r.get("entry_ts"):
                times.append(r["entry_ts"])
    except FileNotFoundError:
        return ("MISSING", [], None)
    window = (min(times), max(times)) if times else None
    return ("OK", sorted(repos), window)


def run_line(module: str, argv: list[str]) -> tuple[str, str]:
    """Run one close line. Returns (status, detail). A crash / non-zero exit is QUARANTINED — the
    silent-non-run class this manifest exists to make loud (ADR-0015 Rule 3)."""
    try:
        cp = subprocess.run(argv, capture_output=True, text=True, timeout=180)
    except Exception as e:  # noqa: BLE001 — a runner that cannot even launch the line quarantines it
        return ("QUARANTINED", f"could not launch: {type(e).__name__}: {e}")
    # A DECLARED N/A (exit 3, the closed exit vocabulary) is a line that legitimately could not analyze
    # this target — rendered N/A (loud, VISIBLE in the verdict), NEVER OK. Collapsing "could not run"
    # into OK on a mandatory gate is the ADR-0015 R4 / F49 violation the out-of-frame audit caught.
    if cp.returncode == 3:
        tail = next((ln for ln in reversed(cp.stdout.splitlines()) if ln.strip()), "declared N/A")
        return ("N/A", tail.strip().lstrip("= ").rstrip("= "))
    if cp.returncode != 0:
        tail = (cp.stderr.strip().splitlines() or ["(no stderr)"])[-1]
        return ("QUARANTINED", f"exit {cp.returncode}: {tail}")
    if not cp.stdout.strip():
        return ("QUARANTINED", "ran but produced NO output (a silent line is not a clean line)")
    return ("OK", f"{len(cp.stdout.splitlines())} lines")


def run_marriage_differential(target: str) -> tuple[str, str]:
    """Run the cross-repo marriage differential (ledger_tnow.lp vs the SQL floor) on the close
    target as a DECLARED OBSERVER — read-only, NON-gating. Returns (status, detail). A missing
    runner or a non-zero exit is reported (QUARANTINED/AGREE-RED), never silently dropped, but it
    does not turn THIS close red (M-2 observer-first)."""
    if not os.path.exists(MARRIAGE_DIFFERENTIAL):
        return ("QUARANTINED", "runner not found (fact-mining repo absent from this checkout)")
    try:
        cp = subprocess.run([sys.executable, MARRIAGE_DIFFERENTIAL, target],
                            cwd=os.path.dirname(MARRIAGE_DIFFERENTIAL),
                            capture_output=True, text=True, timeout=120)
    except Exception as e:  # noqa: BLE001
        return ("QUARANTINED", f"could not launch: {type(e).__name__}: {e}")
    tail = (cp.stdout.strip().splitlines() or ["(no output)"])[-1]
    return ("AGREE" if cp.returncode == 0 else "RED", tail)


def run_soundness_twin() -> tuple[str, str]:
    """Run the operator-twin differential (soundness.lp vs soundness.py) as a DECLARED OBSERVER —
    read-only, target-independent (it checks the banked s10 record + the self-superseding-citation
    boundary). A divergence/quarantine is reported, never silently dropped, but it does not turn THIS
    close red until promoted (observer-first, M-2). Exit-code vocabulary from soundness_twin.py:
    0 AGREE, 1 DIVERGE (defect), 2 QUARANTINED (substrate), 3 BROKEN (negative control failed)."""
    if not os.path.exists(SOUNDNESS_TWIN):
        return ("QUARANTINED", "soundness_twin.py not found")
    try:
        cp = subprocess.run([sys.executable, SOUNDNESS_TWIN], capture_output=True, text=True, timeout=120)
    except Exception as e:  # noqa: BLE001
        return ("QUARANTINED", f"could not launch: {type(e).__name__}: {e}")
    tail = (cp.stdout.strip().splitlines() or ["(no output)"])[-1]
    status = {0: "AGREE", 1: "DIVERGE", 2: "QUARANTINED", 3: "BROKEN"}.get(cp.returncode, "RED")
    return (status, tail)


def _acts_run_id(target: str) -> str:
    return os.environ.get("ACTS_RUN_ID", target)


def _acts_stream_present(run_id: str) -> bool:
    """True iff an acts stream for this run has been parsed into the harness acts schema. A DEFERRED
    (no-stream) report pre-run is correct and green; at the real close the stream exists and the
    consumers RUN (a missing stream at close would then be a loud DEFERRED, never a silent skip)."""
    try:
        cp = subprocess.run(["psql", "-h", resolve_pghost("EPISTEMIC_PGHOST"),
                             "-d", ACTS_STREAM_DB, "-tAc",
                             f'SELECT count(*) FROM "{ACTS_STREAM_SCHEMA}".stream '
                             f"WHERE run_id = '{run_id}';"],
                            capture_output=True, text=True, timeout=30)
        return cp.returncode == 0 and cp.stdout.strip().isdigit() and int(cp.stdout.strip()) > 0
    except Exception:  # noqa: BLE001 — a probe that cannot even run reports no-stream, handled as DEFERRED loudly
        return False


def run_acts_consumers(target: str, mode: str) -> list[tuple[str, str, str]]:
    """Run (or loudly defer/refuse) the three registered audit consumers. Returns [(name, status,
    detail)]. Status vocabulary: OK (RAN — atoms are descriptive data, non-gating) | DEFERRED (no acts
    stream parsed yet, READINESS-mode — loud, not silent, green pre-run) | REQUIRED-ABSENT (no acts
    stream, CLOSE-mode — RED, gating) | N/A (target carries no acts stream by design) | QUARANTINED
    (crashed / ASP<->SQL diverged — gates red). LIVE MANDATORY (Increment 5): a present stream RUNS the
    real deriver; no NOT-WIRED silent-vacuous-pass.

    The oracle §9 readiness-vs-close split (maintainer, 2026-07-07; finding 11): on an EMPTY acts stream,
    `mode='readiness'` DEFERS (green — no run has occurred, the empty substrate is expected pre-run)
    while `mode='close'` goes REQUIRED-ABSENT (RED — a real close with no parsed acts stream is a red
    close, never a silent/deferred pass). The substrate is byte-identical in both modes (an empty
    stream); the mode is the CALLER's declared claim about whether a run has happened, and it CANNOT be
    inferred from the substrate — that is the entire point of the ruling. Default is close (fail-safe:
    the strict, loud direction) so a DEFER is an opt-in, DECLARED choice (arm_e15.sh --verify passes
    --mode readiness), never a silent default that could re-launder the F49 vacuous pass at a real
    close."""
    if target not in ACTS_CONSUMER_TARGETS:
        return [(c, "N/A", "target carries no acts stream by design (e15 / a declared rehearsal target)")
                for c in ACTS_CONSUMERS]
    # SUBSTRATE gate (finding 36): the fenced work-dir is target-resolved. A consumer-bearing target with
    # NO registered fenced substrate (and no ACTS_FENCED override) CANNOT be measured — at CLOSE that is
    # REQUIRED-ABSENT (RED), never a silent vacuous pass reading some other run's fence; at readiness it
    # DEFERS loudly. This mirrors the empty-stream oracle §9 split, on the substrate-pointer axis.
    fenced, fsrc = _resolve_fenced(target)
    if fenced is None:
        if mode == "close":
            return [(c, "REQUIRED-ABSENT", f"no fenced substrate registered for target '{target}' "
                     "(ledger_target.fenced_dir is None and ACTS_FENCED unset) — RED at CLOSE. A close "
                     "with no fenced substrate cannot measure claims/spans; it must not silently read "
                     "another run's fence (finding 36).") for c in ACTS_CONSUMERS]
        return [(c, "DEFERRED", f"no fenced substrate registered for target '{target}' yet (readiness; "
                 "loud, not silent — register ledger_target.fenced_dir or set ACTS_FENCED).")
                for c in ACTS_CONSUMERS]
    run_id = _acts_run_id(target)
    if not _acts_stream_present(run_id):
        if mode == "close":
            return [(c, "REQUIRED-ABSENT", f"acts stream REQUIRED at CLOSE (oracle §9) but NONE parsed "
                     f"for run '{run_id}' — RED. A real close with no acts stream is a red close, never "
                     "a deferred/silent pass (finding 11 disposition).")
                    for c in ACTS_CONSUMERS]
        return [(c, "DEFERRED", f"no acts stream parsed for run '{run_id}' yet (correct pre-run "
                 "READINESS; loud, not silent — F49). Runs at Phase-4/close over the parsed "
                 "acts.act<->s15 join.")
                for c in ACTS_CONSUMERS]
    # LIVE: run the REAL acts.act<->s15 matching differential (acts_join.py, cross-repo — the
    # marriage-differential idiom). A crash / ASP<->SQL divergence QUARANTINES (gates red); a finding
    # atom is descriptive (non-foreclosure §1.3) and does NOT gate.
    join_schema = os.environ.get("ACTS_JOIN_SCHEMA", f"{target}_acts_join")
    source = os.environ.get("ACTS_LEDGER_SOURCE", target)
    if not os.path.exists(ACTS_JOIN):
        return [(c, "QUARANTINED", "acts_join.py deriver not found (fact-mining repo absent from checkout)")
                for c in ACTS_CONSUMERS]
    try:
        cp = subprocess.run(
            [sys.executable, ACTS_JOIN, "--close", "--acts-schema", ACTS_STREAM_SCHEMA,
             "--run-id", run_id, "--source", source, "--join-schema", join_schema, "--fenced", fenced],
            cwd=os.path.dirname(ACTS_JOIN), capture_output=True, text=True, timeout=180)
    except Exception as e:  # noqa: BLE001
        return [(c, "QUARANTINED", f"deriver could not launch: {type(e).__name__}: {e}")
                for c in ACTS_CONSUMERS]
    parsed: dict[str, tuple[str, str]] = {}
    for line in cp.stdout.splitlines():
        if line.startswith("acts:"):
            body = line[len("acts:"):]
            name = body.split()[0]
            rest = body[len(name):].strip()
            status = rest.split()[0] if rest else "QUARANTINED"
            parsed[name] = (status, rest[len(status):].strip())
    out: list[tuple[str, str, str]] = []
    for c in ACTS_CONSUMERS:
        if c in parsed:
            st, det = parsed[c]
            # Cross-check the EXIT CODE against the parsed stdout (ADR-0013 R5): a deriver that printed
            # OK lines but exited non-zero is a LYING readout — trust neither over the other; a
            # non-zero exit with an OK line QUARANTINES (the audit's latent-softness note).
            if cp.returncode != 0 and st == "OK":
                st, det = "QUARANTINED", f"deriver exited {cp.returncode} despite an OK line (exit-code/stdout disagree): {det}"
            out.append((c, st, det))
        else:  # the deriver ran but did not report this consumer — a non-run is QUARANTINED, never dropped
            tail = (cp.stderr.strip().splitlines() or ["(no stderr)"])[-1]
            out.append((c, "QUARANTINED", f"deriver did not report this consumer (exit {cp.returncode}): {tail}"))
    return out


PERF_CONSUMERS = ["proxy_written", "self_performed", "unbound_row"]


def run_perf_consumers(target: str, mode: str) -> list[tuple[str, str, str]]:
    """Run the row_performed_by consumer (finding 28) on a consumer-bearing target: the claimed-vs-
    performed differential over the subject session's ledger-INSERT acts. N/A on non-consumer targets;
    DEFERRED pre-run (no acts stream — readiness) / REQUIRED-ABSENT (close, gates) per the oracle §9
    split, exactly like the acts consumers; QUARANTINED if the session dir is absent or the Python<->SQL
    differential diverges/crashes; atoms are DESCRIPTIVE, non-gating."""
    if target not in ACTS_CONSUMER_TARGETS:
        return [(c, "N/A", "target carries no subject session by design") for c in PERF_CONSUMERS]
    # SUBSTRATE gate (finding 36): the subject session dir is target-resolved. A consumer-bearing target
    # with NO registered session substrate (and no PERF_SESSION_DIR override) CANNOT be measured — at
    # CLOSE that is REQUIRED-ABSENT (RED); at readiness it DEFERS loudly. Reading another run's transcript
    # against this run's rows leaves every row unbound (run B's unbound_row(1..7) specimen).
    session_dir, ssrc = _resolve_session_dir(target)
    if session_dir is None:
        if mode == "close":
            return [(c, "REQUIRED-ABSENT", f"no session substrate registered for target '{target}' "
                     "(ledger_target.subject_session_dir is None and PERF_SESSION_DIR unset) — RED at "
                     "CLOSE. A close with no session transcript cannot bind rows to their INSERT acts; it "
                     "must not silently read another run's transcript (finding 36).") for c in PERF_CONSUMERS]
        return [(c, "DEFERRED", f"no session substrate registered for target '{target}' yet (readiness; "
                 "loud — register ledger_target.subject_session_dir or set PERF_SESSION_DIR).")
                for c in PERF_CONSUMERS]
    # Same readiness/close split as the acts consumers: this deriver needs the PARSED acts stream (its
    # INSERT acts) — absent pre-run. DEFER on an empty stream in readiness; REQUIRED-ABSENT (red) at close.
    run_id = _acts_run_id(target)
    if not _acts_stream_present(run_id):
        if mode == "close":
            return [(c, "REQUIRED-ABSENT", f"acts stream REQUIRED at CLOSE (oracle §9) but NONE parsed "
                     f"for run '{run_id}' — RED.") for c in PERF_CONSUMERS]
        return [(c, "DEFERRED", f"no acts stream parsed for run '{run_id}' yet (correct pre-run READINESS; "
                 "loud, not silent). Runs at close over the parsed session's ledger-INSERT acts.")
                for c in PERF_CONSUMERS]
    if not os.path.exists(ROW_PERFORMED):
        return [(c, "QUARANTINED", "row_performed_by.py not found (fact-mining repo absent)") for c in PERF_CONSUMERS]
    if not os.path.isdir(session_dir):
        return [(c, "QUARANTINED", f"registered session dir absent on disk: {session_dir}") for c in PERF_CONSUMERS]
    source = os.environ.get("ACTS_LEDGER_SOURCE", target)
    join_schema = os.environ.get("PERF_JOIN_SCHEMA", f"{target}_perf_join")
    try:
        cp = subprocess.run([sys.executable, ROW_PERFORMED, "--close", "--session-dir", session_dir,
                             "--source", source, "--join-schema", join_schema],
                            cwd=os.path.dirname(ROW_PERFORMED), capture_output=True, text=True, timeout=180)
    except Exception as e:  # noqa: BLE001
        return [(c, "QUARANTINED", f"deriver could not launch: {type(e).__name__}: {e}") for c in PERF_CONSUMERS]
    parsed: dict[str, tuple[str, str]] = {}
    for line in cp.stdout.splitlines():
        if line.startswith("perf:"):
            body = line[len("perf:"):]
            name = body.split()[0]
            rest = body[len(name):].strip()
            status = rest.split()[0] if rest else "QUARANTINED"
            parsed[name] = (status, rest[len(status):].strip())
    out: list[tuple[str, str, str]] = []
    for c in PERF_CONSUMERS:
        if c in parsed:
            st, det = parsed[c]
            if cp.returncode != 0 and st == "OK":  # exit-code/stdout disagreement QUARANTINES (ADR-0013 R5)
                st, det = "QUARANTINED", f"deriver exited {cp.returncode} despite an OK line: {det}"
            out.append((c, st, det))
        else:
            tail = (cp.stderr.strip().splitlines() or ["(no stderr)"])[-1]
            out.append((c, "QUARANTINED", f"deriver did not report this consumer (exit {cp.returncode}): {tail}"))
    return out


def run_findings_gate() -> tuple[str, str]:
    """The fourth consumer: the findings-ledger close-gate. RED if any finding is OPEN (gates the close
    red); GREEN if none; QUARANTINED if it cannot query (a gate that cannot run is NO RESULT, never a
    silent green — ADR-0015 R3). Exit vocabulary from findings_gate.py: 0 green, 1 red, 2 quarantine."""
    if not os.path.exists(FINDINGS_GATE):
        return ("QUARANTINED", "findings_gate.py not found (claude_harness absent from this checkout)")
    try:
        cp = subprocess.run([sys.executable, FINDINGS_GATE], capture_output=True, text=True, timeout=60)
    except Exception as e:  # noqa: BLE001
        return ("QUARANTINED", f"could not launch: {type(e).__name__}: {e}")
    tail = (cp.stdout.strip().splitlines() or ["(no output)"])
    detail = tail[0] + (f" (+{len(tail) - 1} open)" if len(tail) > 1 else "")
    return ({0: "GREEN", 1: "RED", 2: "QUARANTINED"}.get(cp.returncode, "QUARANTINED"), detail)


# The FORECLOSURE-DEBT mechanism (db/harness/006; WORK-UNIT-foreclosure-debt). Two permanent lines.
# The check-line REGISTRY: a foreclosure's check_line_id must resolve to a line that actually exists
# (the manifest's MANDATORY set OR a registered gate/lint id below). A foreclosure naming a deleted line
# reverts to RED (rot), never a silent checkbox. Gates append their line id here as they are built.
HARNESS_PGHOST_FC = resolve_pghost("EPISTEMIC_PGHOST")
FORECLOSURE_LINE_REGISTRY = set(MANDATORY) | {
    "destructive-ddl-guard",   # tools/no_destructive_ddl.py (specimen 5; forecloses acts-schema-reset)
    "append-only-integrity",   # tools/append_only_integrity.py (forecloses findings 6+15; append-only guard)
    "verify-adapter",          # tools/act_stream/verify_adapter.py (forecloses 5+17+23; adapter<->oracle agreement)
    "bash-write-classification",  # tools/act_stream/verify_bash_write.py (forecloses 18; Bash-redirection write acct)
    "relevant-act-classification",  # experiments/fact-mining/verify_relevant_act.py (forecloses 9; oracle §4)
    "operator-turn-extraction",   # experiments/fact-mining/verify_operator_turns.py (forecloses 25; task-notif skip)
    "contemporaneity-degrade",    # instruments/verify_contemporaneity_degrade.py (forecloses 12; N/A exit-3 contract)
    "consumer-no-vacuous-pass",   # instruments/verify_consumer_no_vacuous.py (forecloses 4; empty-close REQUIRED-ABSENT)
    "consumer-substrate-required",  # instruments/verify_substrate_required.py (forecloses 36; unregistered substrate -> REQUIRED-ABSENT at close)
    "delivery-freight-integrity",   # instruments/close_manifest.py delivery_freight_integrity line (forecloses 35 stage 1; byte-mismatched delivery -> RED)
    "staging-guard",              # tools/staging_guard.py (forecloses 33; explicit-paths commit, no index sweep)
    "binder-bind-many",           # experiments/fact-mining/verify_binder.py (forecloses 39; one-act-may-bind-many)
    "gate-journal-registered",    # instruments/verify_gate_journal_registered.py (forecloses 42; arm-time contemporaneity registration)
    "review-without-detail",      # instruments/review_without_detail.py (forecloses 38; descriptive detail-less-review line, Addendum A)
    "arming-delivery-set",        # harness/e18-build/arm_e18.sh --delivery-set (forecloses 43; the arming automation EMITS the byte-frozen paste set, refuses a packet missing a frozen delivery item)
    "criterion-reviewer-grants",  # harness/e18-build/s18-criterion-principals.sql extended negative control (forecloses 45; asserts BOTH polarities at apply: content columns/review_detail DENIED + every enumerated trigger-chain read/call PRESENT — a mis-granted reviewer role cannot arm silently)
}
_HARNESS_ROOT = os.path.expanduser("~/w/vdc/1/claude_harness")


def _fc_psql(sql: str) -> tuple[bool, str]:
    try:
        cp = subprocess.run(["psql", "-h", HARNESS_PGHOST_FC, "-d", "harness", "-tA", "-F", "\x1f", "-c", sql],
                            capture_output=True, text=True, timeout=30)
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"
    return cp.returncode == 0, (cp.stdout if cp.returncode == 0 else cp.stderr).strip()


def run_foreclosure_debt() -> tuple[str, str]:
    """RED iff harness.foreclosure_debt is nonempty — the experiment cannot close with an unanswered
    ADR-0000 never-again question (a fixed finding with no class_foreclosure row). GREEN when none."""
    if not os.path.isdir(_HARNESS_ROOT):
        return ("QUARANTINED", "claude_harness absent from this checkout")
    ok, out = _fc_psql("SELECT finding_id FROM harness.foreclosure_debt ORDER BY finding_id;")
    if not ok:
        return ("QUARANTINED", f"cannot query foreclosure_debt: {out[-120:]}")
    ids = [x for x in out.splitlines() if x.strip()]
    if not ids:
        return ("GREEN", "every fixed finding carries a class_foreclosure row (ADR-0000 answered)")
    return ("RED", f"{len(ids)} fixed finding(s) owe a foreclosure (unanswered never-again): {ids}")


def run_foreclosure_integrity() -> tuple[str, str]:
    """For every NON-WAIVED foreclosure row: (a) its check_line_id resolves in the registry, and (b) the
    seen-red artifact exists and its sha256 matches — else RED (rot: a deleted gate, a drifted artifact),
    never a silent decay into a checkbox."""
    if not os.path.isdir(_HARNESS_ROOT):
        return ("QUARANTINED", "claude_harness absent")
    ok, out = _fc_psql("SELECT foreclosure_id, finding_id, check_line_id, red_artifact, red_sha256 "
                       "FROM harness.class_foreclosure WHERE kind <> 'waived' ORDER BY foreclosure_id;")
    if not ok:
        return ("QUARANTINED", f"cannot query class_foreclosure: {out[-120:]}")
    rows = [r.split("\x1f") for r in out.splitlines() if r.strip()]
    if not rows:
        return ("GREEN", "no non-waived foreclosures to integrity-check yet")
    rot: list[str] = []
    for fcid, fid, line, artifact, sha in rows:
        if line not in FORECLOSURE_LINE_REGISTRY:
            rot.append(f"fc{fcid}(finding {fid}): check-line '{line}' not in registry (gate deleted?)")
            continue
        path = os.path.join(_HARNESS_ROOT, artifact) if not os.path.isabs(artifact) else artifact
        if not os.path.exists(path):
            rot.append(f"fc{fcid}(finding {fid}): seen-red artifact missing ({artifact})")
            continue
        live = hashlib.sha256(open(path, "rb").read()).hexdigest()
        if live != sha:
            rot.append(f"fc{fcid}(finding {fid}): seen-red sha DRIFTED ({artifact})")
    if rot:
        return ("RED", f"{len(rot)} foreclosure(s) rotted: {rot}")
    return ("GREEN", f"all {len(rows)} non-waived foreclosures intact (line registered + seen-red matches)")


def run_append_only_integrity() -> tuple[str, str]:
    """RED iff any audit-spine table (harness.finding/finding_disposition/class_foreclosure/
    rationalization_* and present acts.*) has lost its append-only UPDATE+DELETE guard — the
    finding-6/15 class, mechanized. Runs the registered `append-only-integrity` gate."""
    if not os.path.isdir(_HARNESS_ROOT):
        return ("QUARANTINED", "claude_harness absent")
    gate = os.path.join(_HARNESS_ROOT, "tools", "append_only_integrity.py")
    try:
        cp = subprocess.run([sys.executable, gate, "--host", HARNESS_PGHOST_FC],
                            capture_output=True, text=True, timeout=60)
    except Exception as e:  # noqa: BLE001
        return ("QUARANTINED", f"{type(e).__name__}: {e}")
    last = (cp.stdout.strip().splitlines() or ["(no output)"])[-1]
    if cp.returncode == 0:
        return ("GREEN", last.lstrip("# "))
    return ("RED", last.lstrip("# "))


# The DELIVERY-FREIGHT-INTEGRITY line (finding 35 stage 1). A delivery filing in acts.ruling is a binding
# ruling recording that freight was DELIVERED to the subject; the row it delivers is its "freight". Before
# this line, the delivered-text == ratified-freight edge was held only by byte-equality + prose regards
# (id 26 -> id 25), with NO trigger or close line refusing a freight-less delivery or a
# delivery-whose-verbatim-DIFFERS-from-its-freight (the forged-ruling / stale-authority class on the
# rulings spine itself). Stage 2 (the e17-era `delivers` FK + a byte-identity trigger) rides e17; this
# stage-1 close line is the immediate mechanization. The pure verdict is a functional core (ADR-0000 /
# ADR-0012 P9) so the seen-red fixture exercises it on hand-built rows without touching append-only
# acts.ruling.
class RulingRow(NamedTuple):
    """One acts.ruling row, enough to decide delivery-freight integrity. Bytes-faithful: verbatim is
    pulled hex-encoded so no psql field/record/newline munging can perturb the byte-equality check."""
    id: int
    binding_grade: str
    regards: str
    verbatim: str
    verbatim_sha256: str
    delivers: int | None = None   # finding 35 stage 2: the FORMAL freight key (None => convention fallback)


def _is_delivery(regards: str) -> bool:
    """Delivery-detection CONVENTION (finding 35 stage 1; convention-based, PENDING the e17 delivers-FK
    that will make this a formal column). A delivery filing is a binding ruling whose `regards` records
    the ACT of delivering freight to the subject — detected conservatively by the token 'delivered'
    (past-tense delivery act). This deliberately EXCLUDES the freight's own self-label 'delivery freight'
    (the frozen ratified row, which says 'delivery freight', not 'delivered'), so the freight is not
    mistaken for its own delivery. Conservative by design: a false negative (a real delivery this misses)
    leaves that row unchecked but never fabricates a RED; the e17 FK closes the residual.

    A row that IS freight is NEVER a delivery OF freight — regardless of how its own regards happens to
    describe when it will be delivered. The original exclusion keyed only on the exact phrase 'delivery
    freight'; e17's freight (ruling 32) self-describes as 'question-freight … delivered only after a
    question row', whose 'delivered' token was mis-read as a delivery act (a false RED, 2026-07-07). The
    robust discriminator: any regards naming the row as freight (`freight` present) is the freight, not a
    delivery — a genuine delivery row records the ACT ('delivered …') and does not call itself freight
    (e16's real delivery, ruling 26, says 'delivered §Operations', no 'freight')."""
    r = (regards or "").lower()
    if "freight" in r:
        return False
    return "delivered" in r


def _delivery_freight_verdict(rows: list[RulingRow]) -> tuple[str, str]:
    """PURE core: given ALL acts.ruling rows, verify every DELIVERY filing byte-matches an EARLIER
    (lower-id) binding freight row — verbatim_sha256 equality AND verbatim equality. GREEN with the count
    checked (0-in-scope reported honestly, never a faked pass); RED naming the offending ruling ids on a
    delivery that matches nothing (freight-less) or whose verbatim DIFFERS from an earlier same-sha
    binding row (byte-mismatch — the forged-freight case). 'Binding or ratified standing' = binding_grade
    'binding' (the only ratified grade; informational drafts like id 24 are NOT freight standing)."""
    by_id = {r.id: r for r in rows}
    # finding 35 stage 2: a row with a FORMAL `delivers` FK is a delivery regardless of prose; a binding
    # row whose regards records a 'delivered' act is the CONVENTION fallback where no FK is set yet.
    deliveries = [r for r in rows if r.delivers is not None
                  or (r.binding_grade == "binding" and _is_delivery(r.regards))]
    if not deliveries:
        return ("GREEN", "0 delivery rows in scope (no delivers-FK and no binding ruling's regards records "
                "a delivery act)")
    bad: list[str] = []
    checked: list[str] = []
    for d in deliveries:
        if d.delivers is not None:
            # FORMAL FK: verify against exactly the declared freight (the DB trigger also enforces this).
            f = by_id.get(d.delivers)
            if f is None:
                bad.append(f"ruling {d.id}: delivers-FK -> {d.delivers} which is not present")
            elif f.id >= d.id:
                bad.append(f"ruling {d.id}: delivers-FK -> {d.delivers} is not an earlier freight")
            elif f.verbatim_sha256 == d.verbatim_sha256 and f.verbatim == d.verbatim:
                checked.append(f"ruling {d.id}=FK=>freight {f.id}")
            else:
                bad.append(f"ruling {d.id}: delivers-FK freight {f.id} verbatim DIFFERS (byte-mismatch)")
            continue
        earlier_binding = [r for r in rows if r.id < d.id and r.binding_grade == "binding"]
        exact = [r for r in earlier_binding
                 if r.verbatim_sha256 == d.verbatim_sha256 and r.verbatim == d.verbatim]
        if exact:
            checked.append(f"ruling {d.id}->freight {exact[0].id} (convention)")
            continue
        sha_only = [r for r in earlier_binding if r.verbatim_sha256 == d.verbatim_sha256]
        if sha_only:
            bad.append(f"ruling {d.id}: earlier binding freight {sha_only[0].id} sha-matches but verbatim "
                       "DIFFERS (byte-mismatch — delivered text is not the frozen freight)")
        else:
            bad.append(f"ruling {d.id}: NO earlier binding freight row byte-matches it "
                       "(freight-less delivery filing)")
    if bad:
        return ("RED", f"{len(bad)} of {len(deliveries)} delivery row(s) FAIL freight-integrity: {bad}")
    return ("GREEN", f"{len(checked)} delivery row(s) checked, each byte-matches an earlier binding "
            f"freight (sha256 + verbatim): {checked}")


def run_delivery_freight_integrity() -> tuple[str, str]:
    """Query acts.ruling (verbatim hex-encoded, byte-faithful) and run the pure freight-integrity verdict
    (finding 35 stage 1). QUARANTINED if acts.ruling cannot be read — a gate that cannot run is NO RESULT,
    never a silent green (ADR-0015 R3)."""
    ok, out = _fc_psql(
        "SELECT id || '|' || binding_grade || '|' || "
        "encode(convert_to(coalesce(regards,''),'UTF8'),'hex') || '|' || "
        "encode(convert_to(verbatim,'UTF8'),'hex') || '|' || verbatim_sha256 || '|' || "
        "coalesce(delivers::text,'') "
        "FROM acts.ruling ORDER BY id;")
    if not ok:
        return ("QUARANTINED", f"cannot read acts.ruling: {out[-120:]}")
    rows: list[RulingRow] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) != 6:
            return ("QUARANTINED", f"unexpected acts.ruling row shape ({len(parts)} fields): {parts[:2]}")
        rid, grade, regards_hex, verbatim_hex, sha, delivers_s = parts
        try:
            regards = bytes.fromhex(regards_hex).decode("utf-8")
            verbatim = bytes.fromhex(verbatim_hex).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as e:
            return ("QUARANTINED", f"could not decode ruling {rid} hex payload: {type(e).__name__}: {e}")
        rows.append(RulingRow(int(rid), grade, regards, verbatim, sha,
                              int(delivers_s) if delivers_s.strip() else None))
    return _delivery_freight_verdict(rows)


# The review-queue-debt close line (engine INC 1; ruling 110 §5 INC 1 + refute-adversarial flaw 9):
# open + aging unadjudicated FLAGS counted PER FAMILY, on the face of every close — a green close
# over unread flags is the dressed-up-QED at system level. VISIBILITY is mandatory now; the RED
# threshold is a later maintainer ruling, so the line's color is OK-with-counts (QUARANTINED only
# when it cannot derive). Flag AGE is NOT-AVAILABLE until an adjudication store lands (OQ9) —
# declared on the line, never silently omitted. The flag->family map comes from the ONE authority
# (judgment_registry.py, fact-mining side) via subprocess — the marriage-differential idiom, never
# a hand-synced copy.
JUDGMENT_REGISTRY = os.path.join(REPO_ROOT, "engine", "judgment_registry.py")  # autoharn: repo-local engine/


def run_review_queue_debt(target: str, journal: str,
                          consumer_details: list[tuple[str, str]],
                          extra_counts: dict[str, int] | None = None) -> tuple[str, str]:
    """Count open flags per family for `target`. `consumer_details` = (flag_name, detail_text) pairs
    from the acts/perf/review_without_detail lines THIS close already ran (their atoms are counted
    from the detail text — the line consumes the close's own derivations, it does not re-run them).
    Ledger-side flags are derived here via the producers' own pure cores (soundness.load+derive,
    sed.report captured) — one home each, no re-encoding."""
    if not os.path.exists(JUDGMENT_REGISTRY):
        return ("QUARANTINED", "judgment_registry.py not found (fact-mining repo absent) — the "
                               "flag->family authority is unreachable")
    try:
        cp = subprocess.run([sys.executable, JUDGMENT_REGISTRY, "--family-map"],
                            capture_output=True, text=True, timeout=60)
        if cp.returncode != 0:
            return ("QUARANTINED", f"family-map authority exited {cp.returncode}: "
                                   f"{(cp.stderr.splitlines() or ['?'])[-1]}")
        fam_of: dict[str, str] = json.loads(cp.stdout)
    except Exception as e:  # noqa: BLE001 — a debt line that cannot ground its vocabulary is NO RESULT
        return ("QUARANTINED", f"family-map load failed: {type(e).__name__}: {e}")
    counts: Counter = Counter()
    try:
        rows, edges, sup = _soundness.load(target)
        alias, unsound, launder = _soundness.derive(rows, edges, sup)
        counts["alias_surface"] += len(alias)
        counts["unsound_derivation"] += len(unsound)
        # launder is the negative-control PROOF, not an open flag; deliberately uncounted.
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            _sed.report(target, journal)
        counts["stale_enactment_row"] += sum(
            1 for ln in buf.getvalue().splitlines()
            if ln.lstrip().startswith(("DEBT ", "CLAUSE-STALE ")))
        for rec in _review_queue._flag_records(journal):
            counts["ticket_flags"] += len(rec.get("ticket_flags") or [])
    except Exception as e:  # noqa: BLE001
        return ("QUARANTINED", f"ledger-side flag derivation failed: {type(e).__name__}: {e}")
    for flag_name, detail in consumer_details:
        counts[flag_name] += len(re.findall(rf"\b{re.escape(flag_name)}\(", detail))
    for flag_name, n in (extra_counts or {}).items():
        counts[flag_name] += n
    per_family: Counter = Counter()
    unmapped: list[str] = []
    for flag_name, n in counts.items():
        f = fam_of.get(flag_name)
        if f is None:
            unmapped.append(flag_name)  # loud: an unregistered flag name is a parity defect
        elif n:
            per_family[f] += n
    named = " ".join(f"{k}={v}" for k, v in sorted(counts.items()) if v) or "(none)"
    fam_txt = " ".join(f"{f}:{per_family[f]}" for f in sorted(per_family)) or "(all zero)"
    detail = (f"open flags by family: {fam_txt}; named: {named}; age=NOT-AVAILABLE (OQ9); "
              f"RED threshold: unruled (visibility line)")
    if unmapped:
        return ("QUARANTINED", f"flag name(s) {unmapped} not in the registry family map — "
                               f"register or exclude them (parity); counts so far: {detail}")
    return ("OK", detail)


def main() -> int:
    args = sys.argv[1:]
    logs: list[str] = []
    journal = DEFAULT_JOURNAL
    mode = "close"  # fail-safe default: strict. readiness is the opt-in, DECLARED choice (oracle §9).
    targets: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--log="):
            logs.append(os.path.expanduser(a.split("=", 1)[1]))
        elif a.startswith("--journal="):
            journal = os.path.expanduser(a.split("=", 1)[1])
        elif a.startswith("--mode="):
            mode = a.split("=", 1)[1]
        elif a == "--mode":
            i += 1
            if i >= len(args):
                print("--mode requires an argument (readiness|close)", file=sys.stderr)
                return 2
            mode = args[i]
        else:
            targets.append(a)
        i += 1
    if mode not in ("readiness", "close"):
        print(f"unknown --mode '{mode}' (expected readiness|close)", file=sys.stderr)
        return 2
    if not logs:
        logs = sorted(glob.glob(DEFAULT_LOG_GLOB)) or [DEFAULT_LOG_GLOB]
    if not targets:
        print("usage: close_manifest.py <target> [--mode readiness|close] [--log=PATH ...] "
              "[--journal=PATH]", file=sys.stderr)
        return 2

    overall_red = 0
    for target in targets:
        tgt = resolve(target)
        jstatus, repos, window = _journal_substrate(journal)
        print(f"# close-manifest — target '{target}' -> {tgt.db}.{tgt.rel()}")
        print(f"#   substrate (ADR-0015 Rule 4): db={tgt.db} schema={tgt.schema} "
              f"actor-model={tgt.subject_actor_sql} login-role={tgt.login_role}")
        # Declare the CONSUMER substrate too (finding 36): the fenced work-dir and subject session dir the
        # acts/perf consumers read are per-target facts, not module-global defaults. Declaring them here is
        # exactly ADR-0015 Rule 4 — the RCA's root cause was that these two pointers were the ONE part of
        # the substrate the manifest did NOT declare, so an e15-default misread never surfaced.
        af, afsrc = _resolve_fenced(target)
        sd, sdsrc = _resolve_session_dir(target)
        print(f"#   consumer substrate (finding 36): acts-fenced={af or '(none registered)'} [{afsrc}]  "
              f"perf-session-dir={sd or '(none registered)'} [{sdsrc}]")
        if "ENV-OVERRIDE" in (afsrc, sdsrc):
            print("#   consumer-substrate WARNING: an ENV OVERRIDE is active (ACTS_FENCED / "
                  "PERF_SESSION_DIR) — the ledger_target registry is being overridden for this run.")
        print(f"#   MODE: {mode}  (oracle §9 — readiness DEFERS on an empty acts stream; close REQUIRES "
              f"it: absence at close is RED. Default close; --mode readiness is the declared pre-run opt-in.)")
        print(f"#   gate journal: {journal}")
        if jstatus == "MISSING":
            print("#   journal WARNING: file missing — journal-consuming lines will read nothing")
        else:
            wtxt = f"{window[0]} .. {window[1]}" if window else "(no timestamps)"
            print(f"#   journal window: {wtxt}")
            if len(repos) > 1:
                print(f"#   journal WARNING: COMMINGLED across {len(repos)} runs {repos} — not reset "
                      f"between runs; journal-joined lines (stale_enactment_debt, contemporaneity gate "
                      f"summary) mix runs. Scope with --since or reset the journal at run start.")
            elif repos:
                print(f"#   journal repos: {repos} (single run)")
        print(f"#   tee.log(s): {logs}\n")

        results = [(m, *run_line(m, _instrument_argv(m, target, logs, journal))) for m in MANDATORY]
        # A DECLARED N/A (exit 3) is loud + VISIBLE but does NOT gate red — it is neither "ran clean"
        # nor "crashed", it is "this line legitimately could not analyze this target". Only a
        # QUARANTINED (crash / silent line) gates red (F49). N/A is rendered distinctly, never as OK.
        red = [m for m, st, _ in results if st not in ("OK", "N/A")]
        na = [m for m, st, _ in results if st == "N/A"]
        for m, st, detail in results:
            mark = {"OK": "OK ", "N/A": "N/A"}.get(st, "!! ")
            print(f"  [{mark}] {m:24} {st:12} {detail}")

        # DECLARED OBSERVER lines — reported, NOT gating (AC7 / link-23 M-2 observer-first).
        for name, (st, detail) in [("marriage_differential", run_marriage_differential(target)),
                                   ("soundness_twin", run_soundness_twin())]:
            print(f"  [obs] {name:24} {st:12} {detail} (declared observer — "
                  f"not gating this close; promotes to mandatory after one e15 close, M-2)")

        # The three e15 audit consumers — REGISTERED mandatory close lines (A.7 / F49). A QUARANTINED
        # (crashed) consumer turns the close red; DEFERRED (no acts stream yet) is loud but green
        # pre-run; N/A on non-e15 targets. A skipped consumer is impossible — each reports a status.
        # OK/DEFERRED/N/A do not gate; QUARANTINED (crashed) and NOT-WIRED (present-but-unrun) DO gate
        # red — a mandatory consumer never green-passes without having RUN (finding-3 fix; F49/ADR-0013 R5).
        debt_details: list[tuple[str, str]] = []  # (flag, detail) fed to the review-queue-debt line
        for name, st, detail in run_acts_consumers(target, mode):
            # QUARANTINED (crash / ASP<->SQL diverge) gates; REQUIRED-ABSENT (close-mode, no acts stream)
            # gates per oracle §9; a descriptive finding atom (OK) and a readiness DEFERRED do not.
            gating_red = st in ("QUARANTINED", "REQUIRED-ABSENT")
            mark = "!! " if gating_red else "con"
            print(f"  [{mark}] acts:{name:19} {st:12} {detail}")
            if st == "OK":
                debt_details.append((name, detail))
            if gating_red:
                red.append(f"acts:{name}")

        # The row_performed_by consumer (finding 28) — claimed-vs-performed. Atoms DESCRIPTIVE (non-gating);
        # a Python<->SQL DIVERGE / crash / non-run QUARANTINES (gates red, F49). N/A on non-consumer targets.
        for name, st, detail in run_perf_consumers(target, mode):
            gating_red = st in ("QUARANTINED", "REQUIRED-ABSENT")
            print(f"  [{'!! ' if gating_red else 'con'}] perf:{name:19} {st:12} {detail}")
            if st == "OK":
                debt_details.append((name, detail))
            if gating_red:
                red.append(f"perf:{name}")

        # review_without_detail (finding 38, consult 37 Addendum A) — DESCRIPTIVE: names detail-less review
        # rows at close (adjudication disposes; does not gate). QUARANTINED (cannot read) gates red.
        rwd_st, rwd_detail = _review_without_detail_atoms(target)
        rwd_red = rwd_st == "QUARANTINED"
        print(f"  [{'!! ' if rwd_red else 'con'}] review_without_detail    {rwd_st:12} {rwd_detail}")
        if not rwd_red:
            debt_details.append(("review_without_detail", rwd_detail))
        if rwd_red:
            red.append(f"review_without_detail:{rwd_st}")

        # The FOURTH consumer — the findings-ledger close-gate (WORK-UNIT-findings-disposition). RED on
        # any OPEN finding (undischarged debt); QUARANTINED if it cannot query. Both gate the close red.
        fg_st, fg_detail = run_findings_gate()
        fg_red = fg_st in ("RED", "QUARANTINED")
        print(f"  [{'!! ' if fg_red else 'OK '}] findings_gate            {fg_st:12} {fg_detail}")
        if fg_red:
            red.append(f"findings_gate:{fg_st}")

        # The review-queue-debt line (engine INC 1): per-family open-flag counts on the face of
        # every close. QUARANTINED gates red; OK-with-counts never does (threshold unruled).
        m_open = re.search(r"(\d+) OPEN finding", fg_detail or "")
        rqd_st, rqd_detail = run_review_queue_debt(
            target, journal, debt_details,
            extra_counts={"open_finding": int(m_open.group(1))} if m_open else None)
        rqd_red = rqd_st == "QUARANTINED"
        print(f"  [{'!! ' if rqd_red else 'OK '}] review_queue_debt        {rqd_st:12} {rqd_detail}")
        if rqd_red:
            red.append(f"review_queue_debt:{rqd_st}")

        # The two permanent FORECLOSURE-DEBT lines (db/harness/006; ADR-0000 never-again mechanized). Both
        # gate the close red: debt = a fixed finding with no answered foreclosure; integrity = a foreclosure
        # whose gate was deleted or whose seen-red drifted (rot). Registered once, run every close forever.
        for name, (st, detail) in [("foreclosure_debt", run_foreclosure_debt()),
                                   ("foreclosure_integrity", run_foreclosure_integrity()),
                                   ("append_only_integrity", run_append_only_integrity()),
                                   ("delivery_freight_integrity", run_delivery_freight_integrity())]:
            fc_red = st in ("RED", "QUARANTINED")
            print(f"  [{'!! ' if fc_red else 'OK '}] {name:24} {st:12} {detail}")
            if fc_red:
                red.append(f"{name}:{st}")

        if red:
            overall_red = 1
            print(f"\n# CLOSE RED — {len(red)} mandatory line(s) not OK (quarantined / required-absent / "
                  f"open-findings): {red}. A red line is NO RESULT or an undischarged requirement "
                  f"(ADR-0015 Rule 3; oracle §9), never a clean close.")
        else:
            na_note = (f" ({len(na)} DECLARED N/A, VISIBLE not silent: {na} — a line that could not "
                       f"analyze this target, rendered N/A never OK)" if na else "")
            print(f"\n# CLOSE GREEN — {len(MANDATORY) - len(na)} of {len(MANDATORY)} mandatory lines "
                  f"ran on the declared substrate{na_note}. (A green close is not a clean readout: the "
                  f"LINES' own review-queue findings still stand for the odd link; this manifest gates "
                  f"only that they RAN or declared N/A.)")
    return overall_red


if __name__ == "__main__":
    sys.exit(main())
