#!/usr/bin/env python3
"""coverage_audit — the governance-coverage join (FINDINGS F33, consult 13 §2.4/§5.3).

The F33 defect: the change-policy gate hardcoded a governed set (`substrate/`) derived from the
FIRST subject's emergent directory choice, and every acceptance probe drew its paths from that
same instance vocabulary — so verification measured the governed set against itself. The e10
subject named its engine `nlafs/`, and 15 of 20 of its `.py` files (21 of 32 mutation events)
were written with ZERO gate events, silently ungoverned under a green apparatus. Nobody caught it
for four links because nobody ran the orphan-side check.

This instrument is that check, made standing. It joins the subject's ACTUAL mutation record (the
guest audit log — ground truth, independent of the gate) against the gate journal, and reports
the DIVERGENCE (I5's gap-visible direction):

  * governed-zero-events : a `.py` file in the subject's committed manifest that was mutated but
                           produced NO gate event (allow or deny). These are the F33 holes.
  * ungated-mutation-events : any mutated `.py` path (committed or not) with zero gate events — a
                           superset of the above that also catches never-committed files.

At an e11-class run close (invariant `*.py` keying) BOTH must be zero: the gate saw everything
the subject coded. Run on the historical arms it reproduces the holes the series shipped blind
(s11 = 15 files / 21 events; s10 and s9 each = their ungoverned top-level driver).

Probe-vocabulary independence (F33's own lesson, applied to THIS instrument's acceptance): the
self-test fixtures use a vocabulary (`gizmo_core/`) that appears in no gate config and no prior
subject repo, so the detector is proven against paths it could not have been fitted to.

Read-only. Consumes: a subject repo's `git ls-files`, a gate journal, and the guest audit log.
Nothing is written.
"""
from __future__ import annotations

import collections
import json
import os
import subprocess
import sys
from dataclasses import dataclass

AUDIT_LOG = "/home/bork/w/vdc/1/epistemic-audit/logs/all.audit.jsonl"
DEPLOYED_JOURNAL = "/home/bork/w/vdc/1/epistemic-audit/logs/change_gate.journal.jsonl"

# Historical arms, for the retro-runs (the known holes the series shipped before F33 was seen).
# session prefix = the audit-log session_id prefix that uniquely identifies the subject run.
RETRO = {
    "s9":  ("/home/bork/w/vdc/1/epistemic-e8",
            "/home/bork/w/vdc/1/epistemic-operator/witness/e8-s9.change_gate.journal.recovered.jsonl",
            "1fee6cdb"),
    "s10": ("/home/bork/w/vdc/1/epistemic-e9",
            "/home/bork/w/vdc/1/epistemic-operator/witness/e9-s10.change_gate.journal.jsonl",
            "29d0ebb3"),
    "s11": ("/home/bork/w/vdc/1/epistemic-e10",
            "/home/bork/w/vdc/1/epistemic-operator/witness/e10-s11.change_gate.journal.jsonl",
            "51384fb5"),
}


@dataclass
class Coverage:
    manifest: list[str]                 # committed .py files (relpath)
    gate: collections.Counter           # relpath -> gate event count
    mut: collections.Counter            # relpath -> mutation event count (from the audit log)
    governed_zero_events: list[tuple[str, int]]   # manifest files mutated with zero gate events
    ungated_mutation_events: list[tuple[str, int]]  # any mutated .py with zero gate events (superset)

    # The ungated superset splits into two DISTINCT verdict classes (F38 / consult 15 §7-5a). The
    # relpaths are already repo-relative (keyed in `_gate_counts`/`_mut_counts` via os.path.relpath),
    # so an out-of-root path is exactly one whose relpath escapes the root ('..' prefix or absolute).
    @staticmethod
    def _out_of_root(rel: str) -> bool:
        return rel.startswith(os.pardir + os.sep) or rel == os.pardir or os.path.isabs(rel)

    @property
    def perimeter(self) -> list[tuple[str, int]]:
        """Out-of-root ungated mutations — a `.py` the subject wrote OUTSIDE the governed root
        (e.g. a session scratchpad). Ungoverned BY DESIGN (SUBJECT_ROOT anchoring), NOT a coverage
        hole: it is the governance-PERIMETER datum (F38). Reported on its own line, never as a hole."""
        return [(f, n) for f, n in self.ungated_mutation_events if self._out_of_root(f)]

    @property
    def in_root_ungated(self) -> list[tuple[str, int]]:
        """Ungated mutations UNDER the root — genuine governance escapes (the F33 class). Superset
        of `governed_zero_events`: it also catches an in-root `.py` the gate missed that was never
        committed (so it is not in the manifest). Any non-empty value here is a real COVERAGE HOLE."""
        return [(f, n) for f, n in self.ungated_mutation_events if not self._out_of_root(f)]

    @property
    def clean(self) -> bool:
        # CLEAN is a statement about the GOVERNED PERIMETER only: the gate saw every mutated `.py`
        # under the root. Out-of-root perimeter flags do NOT flip this (they were never in scope for
        # the gate) — that conflation is exactly the e11-close verdict bug this split fixes.
        return not self.in_root_ungated


def _manifest(repo: str) -> list[str]:
    out = subprocess.run(["git", "-C", repo, "ls-files", "*.py"],
                         capture_output=True, text=True)
    return sorted(p for p in out.stdout.split() if p)


def _gate_counts(journal: str, repo: str) -> collections.Counter:
    """relpath -> gate event count. Both allow ('file') and deny ('target') events count: a
    governed path produces a journal event either way; a hole produces neither."""
    c: collections.Counter = collections.Counter()
    try:
        fh = open(journal, encoding="utf-8")
    except FileNotFoundError:
        return c
    for line in fh:
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        p = e.get("file") or e.get("target")
        if isinstance(p, str) and p:
            c[os.path.relpath(p, repo)] += 1
    fh.close()
    return c


def _mut_counts(audit_log: str, repo: str, session_prefix: str) -> collections.Counter:
    """relpath -> mutation event count, from the audit log (ground truth, gate-independent).
    Counts Write/Edit/NotebookEdit events on `.py` paths for the session."""
    c: collections.Counter = collections.Counter()
    for line in open(audit_log, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not str(e.get("session_id", "")).startswith(session_prefix):
            continue
        if e.get("tool") not in ("Write", "Edit", "NotebookEdit"):
            continue
        sal = e.get("salient", "")
        if isinstance(sal, str) and sal.endswith(".py"):
            c[os.path.relpath(sal, repo)] += 1
    return c


def audit_data(manifest: list[str], gate: collections.Counter,
               mut: collections.Counter) -> Coverage:
    """Pure join over already-loaded data (the acceptance-testable core)."""
    gov_zero = [(f, mut[f]) for f in sorted(manifest) if mut[f] and not gate[f]]
    ungated = [(f, n) for f, n in sorted(mut.items()) if n and not gate[f]]
    return Coverage(manifest, gate, mut, gov_zero, ungated)


def audit_session(repo: str, journal: str, audit_log: str,
                  session_prefix: str) -> Coverage:
    return audit_data(_manifest(repo),
                      _gate_counts(journal, repo),
                      _mut_counts(audit_log, repo, session_prefix))


def report(label: str, cov: Coverage) -> None:
    n_mut = sum(1 for f in cov.manifest if cov.mut[f])
    n_gate = sum(1 for f in cov.manifest if cov.gate[f])
    print(f"\n=== coverage_audit — {label} ===")
    print(f"  committed .py files: {len(cov.manifest)}  mutated: {n_mut}  with gate events: {n_gate}")
    gz_events = sum(n for _, n in cov.governed_zero_events)
    print(f"  GOVERNED-ZERO-EVENTS: {len(cov.governed_zero_events)} files, {gz_events} mutation events")
    for f, n in cov.governed_zero_events:
        print(f"     {f}: {n}")
    # in-root ungated that is NOT a committed-manifest orphan: an in-root .py the gate missed that
    # was never committed. Still a governance escape (F33 class), printed distinctly to avoid
    # double-listing the manifest orphans already shown above.
    orphan_set = {g for g, _ in cov.governed_zero_events}
    inroot_extra = [(f, n) for f, n in cov.in_root_ungated if f not in orphan_set]
    if inroot_extra:
        print(f"  IN-ROOT UNGATED (uncommitted, gate missed): {len(inroot_extra)} files")
        for f, n in inroot_extra:
            print(f"     {f}: {n}")
    # PERIMETER — its OWN verdict class (F38): out-of-root ungated mutations, ungoverned by design.
    # A distinct labeled line; it never reads as a coverage hole and never flips CLEAN.
    if cov.perimeter:
        pm_events = sum(n for _, n in cov.perimeter)
        print(f"  PERIMETER FLAG: {len(cov.perimeter)} out-of-root ungated .py, {pm_events} mutation events "
              f"(ungoverned by design — governance-perimeter datum, F38; NOT a coverage hole)")
        for f, n in cov.perimeter:
            print(f"     {f}: {n}")
    # Two independent verdict lines: the coverage verdict (governed perimeter) and the perimeter note.
    verdict = "CLEAN (gate saw every mutated .py under the governed root)" if cov.clean else \
        "COVERAGE HOLE — mutated .py under the root with zero gate events (governed orphan, F33)"
    print(f"  -> COVERAGE: {verdict}")
    if cov.perimeter:
        print(f"  -> PERIMETER: {len(cov.perimeter)} out-of-root ungated mutation(s) — advisory (F38), not a coverage verdict")


# --------------------------------------------------------------------------- acceptance case

def _acceptance() -> int:
    """coverage_audit's own acceptance case: synthetic fixtures in a NOVEL vocabulary the gate
    config and prior subjects never used (`gizmo_core/`), proving the detector fires on a hole,
    stays quiet on full coverage, and does not mistake a never-mutated governed file for a hole.
    Then the live retro-runs on s9/s10/s11 (the known historical holes)."""
    ok = True

    def _c(name: str, cond: bool, detail: str = "") -> None:
        nonlocal ok
        ok = ok and cond
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"   ({detail})" if detail else ""))

    print("== coverage_audit acceptance (synthetic; novel gizmo_core/ vocabulary) ==")
    # CA1 — a mutated file with zero gate events IS a hole.
    manifest = ["gizmo_core/widget.py", "gizmo_core/sprocket.py", "gizmo_main.py"]
    gate = collections.Counter({"gizmo_core/widget.py": 3})               # only widget governed
    mut = collections.Counter({"gizmo_core/widget.py": 3, "gizmo_core/sprocket.py": 2, "gizmo_main.py": 1})
    cov = audit_data(manifest, gate, mut)
    _c("CA1 mutated-but-ungated files are holes",
       {f for f, _ in cov.governed_zero_events} == {"gizmo_core/sprocket.py", "gizmo_main.py"}
       and sum(n for _, n in cov.governed_zero_events) == 3,
       f"holes={cov.governed_zero_events}")
    # CA2 — full coverage: every mutated file has a gate event -> zero holes, CLEAN.
    gate2 = collections.Counter({"gizmo_core/widget.py": 3, "gizmo_core/sprocket.py": 1, "gizmo_main.py": 1})
    cov2 = audit_data(manifest, gate2, mut)
    _c("CA2 full coverage -> zero holes, CLEAN", cov2.clean and not cov2.governed_zero_events,
       f"holes={cov2.governed_zero_events}")
    # CA3 — a governed file that was never mutated is NOT a hole (no false positive).
    mut3 = collections.Counter({"gizmo_core/widget.py": 2})               # sprocket/main untouched
    cov3 = audit_data(manifest, gate, mut3)
    _c("CA3 never-mutated governed file is not a hole", cov3.clean,
       f"holes={cov3.governed_zero_events}")
    # CA4 — a mutated .py NOT in the committed manifest is still caught (ungated superset).
    mut4 = collections.Counter({"gizmo_core/widget.py": 1, "gizmo_core/uncommitted.py": 1})
    cov4 = audit_data(manifest, gate, mut4)  # gate governs only widget
    _c("CA4 uncommitted mutated .py caught by ungated superset",
       not cov4.clean and any(f == "gizmo_core/uncommitted.py" for f, _ in cov4.ungated_mutation_events),
       f"ungated={cov4.ungated_mutation_events}")
    # CA5 — an OUT-OF-ROOT mutated .py (a session scratchpad, ../../.tmp/smoke.py) is a PERIMETER
    # flag, NOT a coverage hole: the split (F38 / consult 15 §7-5a). CLEAN holds; perimeter fires.
    mut5 = collections.Counter({"gizmo_core/widget.py": 3, "gizmo_core/sprocket.py": 2, "gizmo_main.py": 1,
                                "../../../tmp/scratch/smoke.py": 1})
    gate5 = collections.Counter({"gizmo_core/widget.py": 3, "gizmo_core/sprocket.py": 1, "gizmo_main.py": 1})
    cov5 = audit_data(manifest, gate5, mut5)  # every in-root .py governed; only the out-of-root one is ungated
    _c("CA5 out-of-root ungated .py is a PERIMETER flag, not a COVERAGE HOLE (verdict split)",
       cov5.clean and not cov5.governed_zero_events and not cov5.in_root_ungated
       and [f for f, _ in cov5.perimeter] == ["../../../tmp/scratch/smoke.py"],
       f"clean={cov5.clean} perimeter={cov5.perimeter} in_root_ungated={cov5.in_root_ungated}")

    print("\n== coverage_audit live retro-runs (the known F33 holes the series shipped) ==")
    retro_ok = True
    for label, (repo, journal, sess) in RETRO.items():
        cov = audit_session(repo, journal, AUDIT_LOG, sess)
        report(f"{label} ({os.path.basename(repo)})", cov)
    # assertions on the retro output (the design's expected reproductions; §2.4/§6.1)
    s11 = audit_session(*RETRO["s11"][:2], AUDIT_LOG, RETRO["s11"][2])
    _c("RETRO s11 = 15 files / 21 events (consult 13 §2.4)",
       len(s11.governed_zero_events) == 15 and sum(n for _, n in s11.governed_zero_events) == 21,
       f"{len(s11.governed_zero_events)} files / {sum(n for _,n in s11.governed_zero_events)} events")
    s10 = audit_session(*RETRO["s10"][:2], AUDIT_LOG, RETRO["s10"][2])
    _c("RETRO s10 hole = conformance.py (e9 driver, per §6.1)",
       {f for f, _ in s10.governed_zero_events} == {"conformance.py"},
       f"holes={[f for f,_ in s10.governed_zero_events]}")
    s9 = audit_session(*RETRO["s9"][:2], AUDIT_LOG, RETRO["s9"][2])
    # NB: §6.1 wrote "s9 ⊇ conformance.py", but e8's top-level driver is run_pilot.py — the design's
    # filename is imprecise; the CLASS (the ungoverned top-level driver) reproduces name-independently.
    _c("RETRO s9 hole = run_pilot.py (e8 driver; design said conformance.py — see consult §deviations)",
       {f for f, _ in s9.governed_zero_events} == {"run_pilot.py"},
       f"holes={[f for f,_ in s9.governed_zero_events]}")

    print(f"\n{'ALL PASS' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("--acceptance", "-a"):
        return _acceptance()
    # live close: coverage_audit.py <label> --repo=<> --journal=<> --session=<prefix>
    label = args[0]
    repo = journal = None
    session = None
    for a in args[1:]:
        if a.startswith("--repo="):
            repo = os.path.expanduser(a.split("=", 1)[1])
        elif a.startswith("--journal="):
            journal = os.path.expanduser(a.split("=", 1)[1])
        elif a.startswith("--session="):
            session = a.split("=", 1)[1]
    if label in RETRO and not (repo and journal and session):
        repo_d, journal_d, session_d = RETRO[label]
        repo = repo or repo_d; journal = journal or journal_d; session = session or session_d
    if not (repo and journal and session):
        print("usage: coverage_audit.py                       # acceptance (self-test + retro s9/s10/s11)\n"
              "       coverage_audit.py <label> --repo=<dir> --journal=<file> --session=<id-prefix>\n"
              "  (import audit_session / audit_data for the pure join)")
        return 2
    cov = audit_session(repo, journal, AUDIT_LOG, session)
    report(f"{label} ({os.path.basename(repo)})", cov)
    return 0 if cov.clean else 1


if __name__ == "__main__":
    sys.exit(main())
