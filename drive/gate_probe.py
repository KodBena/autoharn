#!/usr/bin/env python3
"""e14 gate probe — the event-61 repair, proven on a SCRATCH subject root, a COPY journal, and
`probe.ledger` fixture rows in the isolated `nla` database. NEVER touches the durable subject ledger
(public.ledger — append-only, untruncatable), the deployed journal, or any exhibit dir; probes live
on the scratch mirror.

It drives harness/e14-build/pretooluse_change_policy.py exactly as Claude Code would (a PreToolUse
hook fed the tool-call JSON on stdin), with E13_GATE_STATE / E13_GATE_JOURNAL / E13_SUBJECT_ROOT
env-overridden to throwaway paths plus E13_GATE_DB=nla + E13_GATE_LEDGER=probe.ledger (the disclosed
probe-only override; deployment leaves both unset -> the durable nla ledger), and asserts the gate's
decision. The probe seeds probe.ledger (owner-run) with the fixture and resets the MIRROR only.

Cases:
  A. BASE gate intact: an edit with no naming ledger entry is DENIED (needs_entry).
  B. DECLARED-file-list unlock: a ticket whose `files:` list names the file ALLOWS the edit.
  C. EVENT-61 reproduction: a stale verification row whose evidence COMMAND-QUOTES the file
     (`pytest tests/<f>`), with NO ticket declaring the file, is DENIED — the coincidental
     command-quote no longer authorizes a change (the e11/e12 gate ALLOWED exactly this).
  D. PROSE naming still works: a ticket naming the file in plain prose (not a command) ALLOWS.
  E. WINDOW reuse: a second edit inside the window reuses the ticket (ALLOW, reused).
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.join(os.path.dirname(HERE), "hooks", "pretooluse_change_gate.py")  # autoharn: hooks/ (renamed [C13])
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "filing"))
import pghost_resolve  # noqa: E402 (filing/pghost_resolve.py -- never a literal host default)
# The subject ledger lives in the isolated `nla` database; the gate + this probe target it. Fixtures
# run on the `probe` scratch mirror in `nla` (append-only stripped), never the durable ledger.
PGHOST, PGDB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "nla"


def psql(sql: str) -> str:
    return subprocess.run(["psql", "-h", PGHOST, "-d", PGDB, "-tA", "-v", "ON_ERROR_STOP=1", "-c", sql],
                          capture_output=True, text=True, check=True).stdout


def seed(kind: str, statement: str, *, rationale="", evidence="", concern=None, actor="author") -> int:
    # actor is a text column in nla (stamped from the connection identity by default); the gate keys
    # on kind/enacts/naming, never on actor, so a neutral literal suffices for the fixture.
    cols = ["kind", "statement", "rationale", "evidence", "actor"]
    vals = [_q(kind), _q(statement), _q(rationale), _q(evidence), _q(actor)]
    if concern:
        cols.append("concern"); vals.append(_q(concern))
    sql = f"INSERT INTO probe.ledger({','.join(cols)}) VALUES({','.join(vals)}) RETURNING id;"
    return int(psql(sql).splitlines()[0].strip())  # first line is the RETURNING id (then the tag)


def _q(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def run_gate(path: str, env: dict, tool="Edit") -> tuple[int, str]:
    payload = json.dumps({"tool_name": tool, "tool_input": {"file_path": path}})
    p = subprocess.run([sys.executable, GATE], input=payload, capture_output=True, text=True,
                       env={**os.environ, **env})
    return p.returncode, (p.stdout + p.stderr)


def expect(label: str, got_deny: bool, want_deny: bool, extra="") -> bool:
    ok = got_deny == want_deny
    verb = "DENY" if got_deny else "ALLOW"
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {verb} (wanted {'DENY' if want_deny else 'ALLOW'}) {extra}")
    return ok


def journal_tail(journal: str) -> dict:
    with open(journal) as f:
        lines = [l for l in f if l.strip()]
    return json.loads(lines[-1]) if lines else {}


def main() -> int:
    psql("TRUNCATE probe.ledger RESTART IDENTITY CASCADE;")
    tmp = tempfile.mkdtemp(prefix="e14-gate-probe-")
    subj_root = os.path.join(tmp, "subject")
    os.makedirs(os.path.join(subj_root, "tests"))
    target = os.path.join(subj_root, "tests", "test_milestone_b.py")
    open(target, "w").write("# probe target\n")
    state = os.path.join(tmp, "state.json")
    journal = os.path.join(tmp, "journal.jsonl")
    env = {"E13_GATE_STATE": state, "E13_GATE_JOURNAL": journal, "E13_SUBJECT_ROOT": subj_root,
           "E13_GATE_LEDGER": "probe.ledger", "E13_GATE_DB": "nla"}
    passes, total = 0, 0

    def check(label, want_deny, tool="Edit", inspect=None):
        nonlocal passes, total
        rc, out = run_gate(target, env, tool)
        got_deny = rc == 2
        total += 1
        extra = ""
        if inspect and not got_deny:
            extra = f"flags={journal_tail(journal).get('ticket_flags')}"
        if expect(label, got_deny, want_deny, extra):
            passes += 1

    print(f"# e14 gate probe (F45 event-61 repair) — subject_root={subj_root}\n")

    print("A. base gate intact — no naming entry -> DENY:")
    check("A no-entry edit", want_deny=True)

    print("\nC. EVENT-61 reproduction — a stale verification row COMMAND-QUOTES the file, no ticket "
          "declares it -> DENY (the e11/e12 gate ALLOWED this):")
    # the row-24 shape: evidence quotes `pytest tests/test_milestone_b.py`, names nothing else
    seed("verification", "Milestone B passes: execute performs the planned transfers.",
         rationale="SPEC 9 met.", evidence="pytest tests/test_milestone_b.py -q => passed")
    # the row-31 shape: an honest ruling ticket that OMITS test_milestone_b.py from its files: list
    seed("note", "Revise per operator ruling to per-edge transfers.",
         rationale="Carries the ruling into files.",
         evidence="files: substrate/planner.py substrate/plan.py substrate/execute.py",
         concern="enactment")
    check("C command-quote does not unlock", want_deny=True)

    print("\nB. DECLARED-file-list unlock — a ticket whose files: list names the file -> ALLOW:")
    seed("note", "Update the B1 test key for per-edge transfers.",
         rationale="Ruling consequence.",
         evidence="files: substrate/planner.py tests/test_milestone_b.py", concern="enactment")
    check("B declared-file unlock", want_deny=False, inspect=True)

    print("\nE. WINDOW reuse — a second edit inside the window reuses the ticket -> ALLOW (reused):")
    check("E window reuse", want_deny=False, inspect=True)
    reused = journal_tail(journal).get("reused_ticket")
    total += 1
    if expect("E reused_ticket flag", got_deny=False, want_deny=False, extra=f"reused={reused}") and reused:
        passes += 1

    print("\nD. PROSE naming (not a command) still unlocks -> ALLOW:")
    # fresh file + a prose-naming ticket
    target2 = os.path.join(subj_root, "planner2.py")
    open(target2, "w").write("# p\n")
    seed("decision", "Rework planner2.py to emit one Transfer per surviving edge.", concern="design")
    rc, out = run_gate(target2, env)
    total += 1
    if expect("D prose naming unlock", got_deny=(rc == 2), want_deny=False):
        passes += 1

    print(f"\n# RESULT: {passes}/{total} gate cases pass")
    psql("TRUNCATE probe.ledger RESTART IDENTITY CASCADE;")  # leave the mirror clean
    return 0 if passes == total else 1


if __name__ == "__main__":
    sys.exit(main())
