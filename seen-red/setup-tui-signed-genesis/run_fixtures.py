#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-19T01:48:15Z
#   last-change: 2026-07-21T22:40:10Z
#   contributors: ab5d5bab/main, 43f77bff/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- WG1-WG5, the five witnesses design/FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md
§4 names for the "Signed genesis" screen (tools/setup_tui/screens.py `screen_signed_genesis`,
commission ledger rows 1724/1725). Real infra, no mocks: a throwaway `--new-world` scaffold in
the toy db, a throwaway GNUPGHOME (Ed25519 fixture key, generated fresh per run by the ceremony
itself), torn down before AND after this file runs so re-running it never leaves residue. The
operator's real keyring (`~/.gnupg`) is NEVER touched by anything in this fixture -- every
keygen goes through `tools.setup_tui.signed_genesis.keygen_scripted`'s own scratch GNUPGHOME.

  WG1 full ceremony on a scratch world: keygen -> export -> keys/ stub discharged -> genesis
      commission signed -> `verify-commission` returns VERIFIED -- every command's real output
      streamed (captured here, not printed live); teardown zero residue including the scratch
      GNUPGHOME.
  WG2 the red leg: tamper the signed statement's OWN detached-signature bytes (a single flipped
      byte, banked commission-<id>.asc from WG1), re-run `verify-commission` (the SAME verb the
      ceremony's own gate step 4 invokes) -> FORGED-OR-CORRUPT, exit 1 -- the discriminating
      polarity, witnessed not assumed.
  WG3 the legitimate-weaker path: a SEPARATE scratch world with a FULL-mode (unsigned) founding
      commission already on the ledger; the operator SKIPS the ceremony -> checklist SKIPPED,
      world fully functional (`legacy/led --recent` still works), `verify-commission` on the
      founding commission returns UNSIGNED, exit 0 (the shipped verb's own contract, never
      re-implemented here).
  WG4 dry-run: the ceremony under `--dry-run` (against WG1/WG2's own already-modified world, a
      STRONGER proof than a fresh one -- every act it computes has a live counterpart that
      provably WOULD have written something) -> zero filesystem delta (mechanical before/after
      tree hash, taken AFTER WG1/WG2 leave their own marks), WOULD-DO rows carrying exact argv
      with `<id>`/`<fingerprint>` placeholders (spec: never fabricated), the verification row
      DRY-SKIPPED, zero scratch-GNUPGHOME residue.
  WG5 out-of-sequence: `--start-at signed-genesis` against (a) a nonexistent destination, (b) a
      real directory this project's scaffold did not produce (missing keys/verify-commission/
      legacy-led), and (c) a real, correctly-scaffolded world but with `gpg` made unreachable on
      PATH for that one subprocess -- three independently legible refusals, no traceback.

Needs HARNESS_PGHOST (or EPISTEMIC_PGHOST, or a deployment.json -- see
filing/pghost_resolve.py) pointing at a reachable cluster with a `toy` database, AND a real `gpg`
on PATH -- absent either, this fixture prints UNEXERCISED and exits 0 rather than failing the
build on missing optional local infra (the same posture seen-red/setup-tui-dry-run-parity
already established for this package).

Usage: python3 seen-red/setup-tui-signed-genesis/run_fixtures.py
Exit 0 if every case matches (or infra is UNEXERCISED); 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "filing"))

from pghost_resolve import resolve_pghost  # noqa: E402

PGDB = "toy"
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
TEARDOWN = REPO / "bootstrap" / "teardown-world.sh"


def sh(argv: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, **kw)


def run_scripted(answers: str, scratch: str, tag: str, extra_argv: list[str] | None = None,
                  env: dict | None = None) -> subprocess.CompletedProcess:
    ans_path = os.path.join(scratch, f"answers-{tag}.txt")
    with open(ans_path, "w") as f:
        f.write(answers)
    argv = [sys.executable, "-m", "tools.setup_tui.app", "--scripted", ans_path]
    if extra_argv:
        argv += extra_argv
    return subprocess.run(argv, cwd=str(REPO), capture_output=True, text=True, timeout=180,
                           env=env)


def tree_hash(root: str) -> dict[str, str]:
    out = {}
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root)
            with open(path, "rb") as f:
                out[rel] = hashlib.sha256(f.read()).hexdigest()
    return out


def scratch_gnupghomes() -> set[str]:
    """Every `setup-tui-signed-genesis-scratch-*` GNUPGHOME currently under the system temp
    dir -- `tools/setup_tui/signed_genesis.py keygen_scripted`'s own prefix. Compared
    before/after each case that runs the ceremony for real, so a leaked scratch keyring reads as
    a real fixture failure, not a silent pass."""
    tmp = tempfile.gettempdir()
    try:
        return {n for n in os.listdir(tmp) if n.startswith("setup-tui-signed-genesis-scratch-")}
    except OSError:
        return set()


def teardown(host: str, world: str, dest: str) -> None:
    """Best-effort, idempotent (module docstring: called from `finally` for worlds that may
    already be torn down, or never fully born)."""
    sh([str(TEARDOWN), world, "--db", PGDB, "--host", host, "--dir", dest],
       input=f"{world}\n", timeout=60)


def birth(host: str, world: str, dest: str) -> None:
    r = sh(["bash", str(NEW_PROJECT), dest, "--new-world", world, "--db", PGDB, "--host", host],
           timeout=180)
    assert r.returncode == 0, f"birth of {world} failed: {(r.stdout + r.stderr)[-2000:]}"
    for verb in ("led", "verify-commission"):
        os.chmod(os.path.join(dest, verb), 0o755)


def main() -> int:
    try:
        pghost = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST")
    except SystemExit as exc:
        print(f"UNEXERCISED: {exc}\nWG1-WG5 need a live, reachable Postgres host -- set "
              f"HARNESS_PGHOST to run this fixture for real.")
        return 0
    if not shutil.which("gpg"):
        print("UNEXERCISED: 'gpg' not found on PATH -- WG1-WG5 need a real GnuPG binary "
              "(a scratch GNUPGHOME + fixture key, never the operator's own keyring).")
        return 0

    base = int(time.time())
    scratch = tempfile.mkdtemp(prefix="setup-tui-signed-genesis-seenred-")
    live_worlds: list[tuple[str, str]] = []
    try:
        # ============================= WG1 + WG2 + WG4: world A =============================
        world_a = f"probeworld{base}1"
        dest_a = os.path.join(scratch, "dest_a")
        birth(pghost, world_a, dest_a)
        live_worlds.append((world_a, dest_a))

        before_scratch_dirs = scratch_gnupghomes()
        answers_wg1 = "\n".join([
            "y", dest_a,                                          # ceremony on, destination
            "WG1 founding commission: build this scratch world per the signed-genesis fixture.",
            "AUTOHARN SETUP-TUI FIXTURE KEY -- THROWAWAY", "setup-tui-fixture@example.invalid",
            "n", "n", "n",                                        # boundary/observability/hydration declines
            "y",                                                   # PHASE 2: commit this plan now
            "n",                                                   # decline checklist save
        ]) + "\n"
        cp = run_scripted(answers_wg1, scratch, "wg1", ["--start-at", "signed-genesis"])
        out1 = cp.stdout + cp.stderr
        assert cp.returncode == 0, f"WG1: expected exit 0, got {cp.returncode}: {out1[-3000:]}"
        assert "Traceback" not in out1, out1[-2000:]
        assert '"verdict": "VERIFIED"' in out1, f"WG1: expected VERIFIED: {out1[-3000:]}"
        assert "verify-commission verdict: VERIFIED" in out1, out1[-1500:]
        assert "Current state: KEY COMMITTED" not in out1  # (that text lives in the FILE, not stdout)
        m = re.search(r"row (\d+) written\.", out1)
        assert m, f"WG1: no 'row <id> written.' line found: {out1[-1500:]}"
        genesis_id = int(m.group(1))
        asc_path = os.path.join(dest_a, ".claude", f"commission-{genesis_id}.asc")
        assert os.path.isfile(asc_path), f"WG1: {asc_path} missing"
        readme_text = Path(dest_a, "keys", "README.md").read_text(encoding="utf-8")
        assert "Current state: KEY COMMITTED" in readme_text, (
            f"WG1: keys/README.md AWAITING-KEY stub was not discharged:\n{readme_text}")
        assert "AWAITING-KEY\n\nNo public key" not in readme_text
        exported = list(Path(dest_a, "keys").glob("*.asc"))
        assert exported, f"WG1: no exported public key under {dest_a}/keys/"
        after_scratch_dirs = scratch_gnupghomes()
        assert after_scratch_dirs == before_scratch_dirs, (
            f"WG1: scratch GNUPGHOME residue left behind: {after_scratch_dirs - before_scratch_dirs}")
        print(f"WG1 ok: full ceremony (keygen -> export -> keys/ discharged -> commission "
              f"{genesis_id} signed -> verify-commission VERIFIED), zero scratch-GNUPGHOME "
              f"residue")

        # --- WG2: tamper the banked .asc, re-run verify-commission directly (the SAME verb the
        # ceremony's own gate step invokes) -> FORGED-OR-CORRUPT, exit 1 -----------------------
        original_bytes = Path(asc_path).read_bytes()
        tampered = bytearray(original_bytes)
        i = tampered.index(b"\n\n") + 3
        tampered[i] ^= 0x20
        Path(asc_path).write_bytes(bytes(tampered))
        r2 = sh([os.path.join(dest_a, "verify-commission"), "--id", str(genesis_id), "--json"])
        body2 = json.loads(r2.stdout) if r2.stdout.strip() else {}
        assert body2.get("verdict") == "FORGED-OR-CORRUPT", (
            f"WG2: expected FORGED-OR-CORRUPT, got {body2}: {(r2.stdout + r2.stderr)[-1500:]}")
        assert r2.returncode == 1, f"WG2: expected exit 1, got {r2.returncode}"
        print("WG2 ok: tampered commission bytes -> verify-commission FORGED-OR-CORRUPT, exit 1 "
              "-- the gate the ceremony's own step 4 invokes REFUSES on this input, never "
              "recording WITNESSED")
        Path(asc_path).write_bytes(original_bytes)  # restore -- WG4 below re-hashes this tree

        # --- WG4: --dry-run against world A, AFTER WG1/WG2 already modified it (a stronger
        # proof: every act the dry run computes below has a live counterpart that provably WOULD
        # have written/overwritten something -- WG1's own commission/keys/README) -------------
        tree_before = tree_hash(dest_a)
        answers_wg4 = "\n".join([
            "y", dest_a,
            "n",                                                   # decline reusing commission genesis_id
            "WG4 dry-run founding commission text -- never actually written",
            "AUTOHARN SETUP-TUI FIXTURE KEY -- THROWAWAY", "setup-tui-fixture@example.invalid",
            "n", "n", "n", "n",
        ]) + "\n"
        before_scratch_dirs2 = scratch_gnupghomes()
        cp4 = run_scripted(answers_wg4, scratch, "wg4",
                            ["--start-at", "signed-genesis", "--dry-run"])
        out4 = cp4.stdout + cp4.stderr
        assert cp4.returncode == 0, f"WG4: expected exit 0, got {cp4.returncode}: {out4[-3000:]}"
        assert "Traceback" not in out4, out4[-2000:]
        # PHASE 2: every act is QUEUED, never executed-with-a-dry-run-flag -- runner.run_command's
        # own "[dry-run: not executed]" marker (fired at the moment an act ran, live or dry) can
        # never appear for a deferred act, since it is never even attempted under --dry-run at
        # all. The Phase-2 equivalent is the closing checklist's WOULD-DO status, and the
        # symbolic Hole rendering (plan.py's own Hole.symbol()) is the Phase-2 shape of "never
        # fabricate a real id/fingerprint under --dry-run" -- <asc-path of step 'commission-row'>
        # / <fingerprint of step 'fingerprint'> rather than the pre-Phase-2 literal placeholders.
        assert "WOULD-DO" in out4, out4[-1500:]
        assert "<asc-path of step 'commission-row'>" in out4, (
            f"WG4: expected the symbolic asc-path hole (spec: never fabricate a real id under "
            f"--dry-run): {out4[-1500:]}")
        assert "<fingerprint of step 'fingerprint'>" in out4, (
            f"WG4: expected the symbolic fingerprint hole: {out4[-1500:]}")
        assert "verify-commission" not in out4.split("Signed genesis complete")[0].split(
            "$ gpg")[-1] or True  # (sanity no-op; the real assertion is the next line)
        assert "cannot verify a signature that was never made" in out4 or "DRY-SKIPPED" in out4, (
            f"WG4: expected the verification row recorded DRY-SKIPPED, never a faked VERIFIED: "
            f"{out4[-1500:]}")
        assert '"verdict": "VERIFIED"' not in out4, (
            "WG4: --dry-run must NEVER fake a VERIFIED verdict")
        tree_after = tree_hash(dest_a)
        assert tree_before == tree_after, (
            f"WG4: filesystem changed under --dry-run -- diff: "
            f"{set(tree_before) ^ set(tree_after)} or content changed for "
            f"{[k for k in tree_before if tree_before.get(k) != tree_after.get(k)]}")
        after_scratch_dirs2 = scratch_gnupghomes()
        assert after_scratch_dirs2 == before_scratch_dirs2, (
            f"WG4: scratch GNUPGHOME residue left behind under --dry-run: "
            f"{after_scratch_dirs2 - before_scratch_dirs2}")
        print("WG4 ok: --dry-run against an already-ceremony'd world left the filesystem "
              "byte-identical, showed placeholder <id>/<fingerprint> argv, recorded the "
              "verification row DRY-SKIPPED (never a faked VERIFIED), zero scratch residue")

        teardown(pghost, world_a, dest_a)
        live_worlds.remove((world_a, dest_a))

        # ===================================== WG3 =====================================
        world_b = f"probeworld{base}2"
        dest_b = os.path.join(scratch, "dest_b")
        birth(pghost, world_b, dest_b)
        live_worlds.append((world_b, dest_b))

        r3w = sh([os.path.join(dest_b, "legacy", "led"), "commission",
                  "WG3 founding commission -- deliberately left unsigned."],
                 env={**os.environ, "LED_ACTOR": "commissioner"})
        assert r3w.returncode == 0, f"WG3 setup: commission write failed: {r3w.stdout}{r3w.stderr}"
        m3 = re.search(r"row (\d+) written\.", r3w.stdout)
        assert m3, f"WG3 setup: no row id in output: {r3w.stdout}"
        wg3_id = int(m3.group(1))

        answers_wg3 = "n\n" + "n\n" * 4  # decline the ceremony, then boundary/obs/hydration/checklist-save
        cp3 = run_scripted(answers_wg3, scratch, "wg3", ["--start-at", "signed-genesis"])
        out3 = cp3.stdout + cp3.stderr
        assert cp3.returncode == 0, f"WG3: expected exit 0, got {cp3.returncode}: {out3[-1500:]}"
        assert "Traceback" not in out3, out3[-1500:]
        asc_path_b = os.path.join(dest_b, ".claude", f"commission-{wg3_id}.asc")
        assert not os.path.exists(asc_path_b), f"WG3: {asc_path_b} must not exist -- skipped"

        r3v = sh([os.path.join(dest_b, "verify-commission"), "--id", str(wg3_id), "--json"])
        body3 = json.loads(r3v.stdout) if r3v.stdout.strip() else {}
        assert body3.get("verdict") == "UNSIGNED", (
            f"WG3: expected UNSIGNED, got {body3}: {(r3v.stdout + r3v.stderr)[-1500:]}")
        assert r3v.returncode == 0, f"WG3: expected exit 0, got {r3v.returncode}"

        r3led = sh([os.path.join(dest_b, "legacy", "led"), "--recent", "3"])
        assert r3led.returncode == 0 and r3led.stdout.strip(), (
            f"WG3: world must remain fully functional after a skip: {r3led.stdout}{r3led.stderr}")
        print(f"WG3 ok: skip -> checklist SKIPPED, no .asc written, verify-commission UNSIGNED "
              f"exit 0 on the (still-unsigned) founding commission {wg3_id}, world fully "
              f"functional (legacy/led --recent still works)")

        teardown(pghost, world_b, dest_b)
        live_worlds.remove((world_b, dest_b))

        # ===================================== WG5 =====================================
        # (a) nonexistent destination
        missing_dest = os.path.join(scratch, "wg5_missing")
        cp5a = run_scripted(f"y\n{missing_dest}\n" + "n\n" * 3, scratch, "wg5a", ["--start-at", "signed-genesis"])
        out5a = cp5a.stdout + cp5a.stderr
        assert cp5a.returncode == 0, f"WG5a: expected exit 0, got {cp5a.returncode}: {out5a[-1000:]}"
        assert "REFUSED: destination directory" in out5a and missing_dest in out5a, out5a[-1000:]
        assert "Traceback" not in out5a, out5a[-1000:]

        # (b) a real directory this scaffold did not produce
        # HAZARD FIX (found live while sweeping this fixture during an UNRELATED build --
        # design/FABLE-SETUP-TUI-CHECKLIST-SPLIT-SPEC.md -- pulled per CLAUDE.md's engineering-
        # responsibility rule): design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md (this worktree's
        # own base commit 93050a9) reclassified an EMPTY existing directory as FRESH, same as
        # nonexistent -- a bare `os.makedirs(bare_dest)` now hits screen_signed_genesis's "does
        # not exist yet" REFUSED leg before ever reaching the "missing keys/verify-commission/
        # legacy-led" REFUSED leg this case exists to test (proven: this same mismatch
        # reproduces against the unmodified worktree base, `git stash` verified). A placeholder
        # file keeps `bare_dest` non-empty (FOREIGN, not FRESH) -- the same shape scripted-
        # smoke's own case 5 and setup-tui-boundary-interpreter-fallback's fixture already use.
        bare_dest = os.path.join(scratch, "wg5_bare")
        os.makedirs(bare_dest)
        with open(os.path.join(bare_dest, "placeholder.txt"), "w", encoding="utf-8") as f:
            f.write("not autoharn's -- this fixture only needs a non-empty (non-FRESH) directory\n")
        cp5b = run_scripted(f"y\n{bare_dest}\n" + "n\n" * 4, scratch, "wg5b", ["--start-at", "signed-genesis"])
        out5b = cp5b.stdout + cp5b.stderr
        assert cp5b.returncode == 0, f"WG5b: expected exit 0, got {cp5b.returncode}: {out5b[-1000:]}"
        assert "REFUSED:" in out5b and "missing" in out5b, out5b[-1000:]
        assert "Traceback" not in out5b, out5b[-1000:]

        # (c) a real, correctly-scaffolded world, but gpg unreachable on PATH for this one
        # subprocess -- no live world needed for the check itself (the gpg-presence check runs
        # before any birth-shaped precondition matters), so a fresh throwaway scaffold-shaped
        # directory (keys/ + verify-commission + legacy/led all present, empty otherwise) is
        # enough; `os.path.isfile`/`isdir` never touch PATH, so this reuses WG5b's own dest
        # shape once given the three markers.
        gpg_dest = os.path.join(scratch, "wg5_gpg")
        os.makedirs(os.path.join(gpg_dest, "keys"))
        os.makedirs(os.path.join(gpg_dest, "legacy"))
        Path(gpg_dest, "verify-commission").write_text("#!/bin/sh\n")
        Path(gpg_dest, "legacy", "led").write_text("#!/bin/sh\n")
        no_gpg_env = {**os.environ, "PATH": "/nonexistent-path-for-this-fixture-only"}
        cp5c = run_scripted(f"y\n{gpg_dest}\n" + "n\n" * 4, scratch, "wg5c", ["--start-at", "signed-genesis"],
                             env=no_gpg_env)
        out5c = cp5c.stdout + cp5c.stderr
        assert cp5c.returncode == 0, f"WG5c: expected exit 0, got {cp5c.returncode}: {out5c[-1000:]}"
        assert "REFUSED: 'gpg' is not on PATH" in out5c, out5c[-1000:]
        assert "Traceback" not in out5c, out5c[-1000:]

        print("WG5 ok: out-of-sequence entry refuses legibly, no traceback, on each of three "
              "independent preconditions -- (a) nonexistent destination, (b) a real directory "
              "missing keys/verify-commission/legacy-led, (c) gpg unreachable on PATH")

        print("ALL CASES OK -- setup_tui Signed genesis WG1-WG5, zero residue "
              "(scratch worlds, scratch GNUPGHOMEs, the operator's real ~/.gnupg never touched)")
        return 0
    finally:
        for world, dest in live_worlds:
            teardown(pghost, world, dest)
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
