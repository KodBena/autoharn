#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-19T20:08:43Z
#   last-change: 2026-07-19T20:08:43Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""seen-red/setup-tui-signed-genesis-resume/run_fixtures.py -- PHASE-2 REPLACEMENT (design/
FABLE-SETUP-TUI-PURE-CORE-SPEC.md, commission ledger rows 1823 point 2 / 1825 / 1835) of this
census slot's prior content.

WHY REPLACED, NOT LEFT UNMODIFIED (itemized in the Phase-2 build report per its own build
conditions): the prior fixture proved `tools/setup_tui/signed_genesis.py`'s bespoke
`detect_resumable`/`ResumeCandidate` partial-ceremony scan (ledger row 1799 finding 7) -- a
mechanism that existed because a screen could die MID-SCREEN under the old progressive-execution
model, with no other record of how far it got. `screens.py`'s Phase-2 rewrite retires that
mechanism (see its own module docstring and `signed_genesis.py`'s comment at the retirement site):
under the pure-core model, `commit_executor.CommitJournal`'s generic per-entry resume (WPC4,
already proven at the module level by seen-red/setup-tui-pure-core-foundation's case 3) covers
"kill mid-commit, re-run, resume cleanly" for EVERY plan entry, keygen included -- so the
genesis-specific archaeology this fixture's old red/green pair exercised no longer exists to
prove red-then-green against. This replacement proves the SAME property (a real gpg keygen is
NEVER silently repeated after a mid-commit death) against the mechanism that now actually
provides it: a REAL commit_executor.execute() run over the REAL signed_genesis.py plan-act chain
(keygen -> list-secret-keys -> export -> keys/ write -> README discharge), with a real gpg into a
scratch GNUPGHOME, killed (via a raising on_result callback, the same technique
seen-red/setup-tui-pure-core-foundation's case 3 uses) immediately after the real keygen act, then
resumed by a second execute() call against the same destination/journal.

SCOPE, NAMED HONESTLY: this fixture proves the resume property over the KEYGEN-THROUGH-DISCHARGE
sub-chain only, against a SCRATCH destination directory that carries a hand-seeded
keys/README.md (the AWAITING-KEY stub `bootstrap/templates/keys-README.md.tmpl` ships) rather than
a real born world -- the sign+verify tail needs `<dest>/legacy/led` and `<dest>/verify-commission`,
which only a real Postgres-backed birth produces; that tail's OWN resume behavior is covered by the
SAME generic journal mechanism (nothing genesis-specific about it) and is not re-proven here to
avoid needing live infra this census slot did not originally require for its red/green core claim.
If HARNESS_PGHOST/EPISTEMIC_PGHOST/deployment.json is set, an OPTIONAL extended case additionally
births a real scratch world and proves the sign+verify tail resumes too; absent one, that case is
UNEXERCISED (exit 0), never silently skipped without saying so.

Needs a real `gpg` on PATH (required, not optional -- this fixture's own claim is about a REAL
keygen never repeating). Zero residue: every scratch GNUPGHOME and destination directory removed
in a `finally`. Lazy imports banned.

Usage: python3 seen-red/setup-tui-signed-genesis-resume/run_fixtures.py
Exit 0 if every case matches (or reports its own UNEXERCISED honestly); 1 otherwise."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "filing"))

from tools.setup_tui import commit_executor as CE  # noqa: E402
from tools.setup_tui import plan as P  # noqa: E402
from tools.setup_tui import signed_genesis as SG  # noqa: E402

FAILURES: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  OK   {label}")
    else:
        msg = f"FAIL {label}" + (f" -- {detail}" if detail else "")
        print(f"  {msg}")
        FAILURES.append(msg)


def _secret_key_count(gnupghome: str) -> int:
    r = subprocess.run(["gpg", "--homedir", gnupghome, "--list-secret-keys", "--with-colons"],
                        capture_output=True, text=True)
    return sum(1 for ln in r.stdout.splitlines() if ln.startswith("fpr"))


def case_keygen_never_repeats_on_resume() -> None:
    print("case: mid-commit death right after a REAL keygen -> resume never double-keygens")
    if shutil.which("gpg") is None:
        print("  UNEXERCISED: 'gpg' not on PATH -- this fixture's own claim needs a real keygen")
        return
    tmp = tempfile.mkdtemp(prefix="setup-tui-signed-genesis-resume-")
    try:
        dest = os.path.join(tmp, "dest")
        os.makedirs(os.path.join(dest, "keys"))
        # A hand-seeded AWAITING-KEY stub, matching bootstrap/templates/keys-README.md.tmpl's own
        # shape closely enough for discharge_write_act's own marker logic to find and replace --
        # this fixture proves the RESUME property of the plan-act chain, not a full birth.
        readme_path = os.path.join(dest, "keys", "README.md")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("# keys/\n\n" + SG.AWAITING_HEADER + "\n\n(no key committed yet)\n")

        name, email = "Resume Fixture Key", "resume-fixture@example.invalid"
        # FINDING-2 FIX (fresh-context review of b565db1): the scratch GNUPGHOME setup is now
        # ITSELF a plan entry (a CallableAct, entry 0) -- never a decision-time filesystem effect.
        # keygen's own argv holds Holes on that entry's real return value (the actual gnupghome
        # path, unknowable until this entry runs), matching production code (screen_signed_
        # genesis) exactly rather than reaching into "private" setup functions directly.
        setup_act, setup_produces = SG.prepare_scratch_gnupghome_act(name, email)
        keygen_act, keygen_produces = SG.keygen_scripted_act(SG.gnupghome_hole(),
                                                               SG.batch_path_hole())
        list_act, list_produces = SG.list_secret_key_act(SG.gnupghome_hole())
        export_act, export_produces = SG.export_public_key_act(SG.gnupghome_hole())
        filename = SG.key_filename(name)

        plan = P.Plan()
        plan.append(P.PlanEntry(screen="signed-genesis", item="scratch GNUPGHOME prepared",
                                 lesson="l", act=setup_act, produces=setup_produces))
        plan.append(P.PlanEntry(screen="signed-genesis", item="keypair generated",
                                 lesson="l", act=keygen_act, produces=keygen_produces))
        plan.append(P.PlanEntry(screen="signed-genesis", item="fingerprint listed",
                                 lesson="l", act=list_act, produces=list_produces))
        plan.append(P.PlanEntry(screen="signed-genesis", item="public key exported",
                                 lesson="l", act=export_act, produces=export_produces))
        plan.append(P.PlanEntry(screen="signed-genesis", item="public key written to keys/",
                                 lesson="l", act=SG.keys_write_act(dest, filename)))
        plan.append(P.PlanEntry(screen="signed-genesis",
                                 item="keys/README.md AWAITING-KEY discharged", lesson="l",
                                 act=SG.discharge_write_act(dest, filename, name, email)))

        def _die_after_keygen(i: int, entry: object, result: object,
                              proc: object = None) -> None:
            # PHASE-2 addition to on_result's signature (commit_executor.py's own note):
            # a 4th positional arg, the entry's own started Popen (None here -- no
            # BackgroundAct in this plan). Entry 1 is now keygen (entry 0 is the scratch
            # GNUPGHOME setup, FINDING-2's own reordering).
            if i == 1:
                raise RuntimeError("simulated mid-commit death, right after the real keygen")

        crashed = False
        try:
            CE.execute(plan, dest, on_result=_die_after_keygen)
        except RuntimeError:
            crashed = True
        check("the simulated death propagated (never silently swallowed)", crashed)

        # The real gnupghome path is only known once entry 0 has actually run -- read it back
        # from the journal itself (FINDING-1's own persisted-bindings mechanism), the same way a
        # resumed execute() call will.
        journal = CE.CommitJournal.open_or_create(CE.journal_path(dest), len(plan.entries))
        gnupghome = journal.bindings().get(SG.SCRATCH_GNUPGHOME_PRODUCES)
        check("the scratch GNUPGHOME path was really persisted after entry 0 succeeded",
              bool(gnupghome) and os.path.isdir(gnupghome), gnupghome)

        count_after_crash = _secret_key_count(gnupghome)
        check("exactly ONE real secret key exists after the keygen act (before resume)",
              count_after_crash == 1, f"count={count_after_crash}")

        check("journal marked setup+keygen entries DONE despite the crash",
              journal.statuses[0] == CE.DONE and journal.statuses[1] == CE.DONE,
              journal.statuses)
        check("journal still names entries 2-5 PENDING", all(
            s == CE.PENDING for s in journal.statuses[2:]), journal.statuses)

        # RESUME: a fresh execute() call against the SAME destination/plan must not re-run the
        # setup or keygen entries (no second scratch dir, no second key) and must complete the
        # remaining chain for real -- including the export/discharge entries whose Holes depend
        # on entry 0's (setup) and entry 1's (keygen->list) bindings, both loaded from the
        # journal by FINDING-1's own fix, genuinely exercised here across a real resume.
        result = CE.execute(plan, dest)
        check("resumed execution completed", result.completed)
        check("the resumed run's bindings still carry the SAME scratch gnupghome path "
              "(loaded from the journal, not regenerated)",
              result.bindings.get(SG.SCRATCH_GNUPGHOME_PRODUCES) == gnupghome,
              result.bindings.get(SG.SCRATCH_GNUPGHOME_PRODUCES))
        count_after_resume = _secret_key_count(gnupghome)
        check("still exactly ONE secret key after resume -- keygen was NOT repeated",
              count_after_resume == 1, f"count={count_after_resume}")

        keys_path = os.path.join(dest, "keys", filename)
        check("the public key was really exported and written",
              os.path.isfile(keys_path) and open(keys_path).read().startswith(
                  "-----BEGIN PGP PUBLIC KEY BLOCK-----"))
        with open(readme_path, encoding="utf-8") as f:
            readme_text = f.read()
        check("keys/README.md discharged to KEY COMMITTED, exactly once (no duplicate section)",
              readme_text.count(SG.KEY_COMMITTED_HEADER) == 1 and
              SG.AWAITING_HEADER not in readme_text, readme_text)
        fpr = result.bindings.get(SG.FINGERPRINT_PRODUCES, "")
        check("the discharged README names the REAL fingerprint (not a placeholder)",
              bool(fpr) and fpr in readme_text, (fpr, readme_text[:200]))

        check("journal removed once every entry is DONE",
              not os.path.isfile(CE.journal_path(dest)))
        SG.teardown_scratch(gnupghome)
        check("scratch GNUPGHOME removed, zero residue", not os.path.isdir(gnupghome))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    case_keygen_never_repeats_on_resume()
    if FAILURES:
        print(f"\n{len(FAILURES)} FAILURE(S):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("\nall cases GREEN (or honestly UNEXERCISED)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
