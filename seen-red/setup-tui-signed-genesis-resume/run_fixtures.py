#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-19T03:54:23Z
#   last-change: 2026-07-19T04:19:45Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""seen-red/setup-tui-signed-genesis-resume/run_fixtures.py -- live, red-before-green proof of
tools/setup_tui/signed_genesis.py's resume-after-death fix (ledger row 1799 finding 7):
`screen_signed_genesis`'s OPERATOR branch must detect a partial ceremony (a key already exported
/ keys/README.md already discharged / a commission .asc present-but-unverified) and OFFER to
REUSE the existing key instead of unconditionally generating a second one into the operator's
real keyring.

SCOPE, NAMED HONESTLY (not silently narrowed): driving the REAL, interactive `gpg
--quick-generate-key` / interactive detached-sign prompts headlessly is not possible in this
sandbox -- verified directly (no `/dev/tty`, no working pinentry even with
`--pinentry-mode loopback` + a scripted answer-bot pinentry-program: `gpg: cannot open '/dev/tty'`
/ `gpg: Sorry, no terminal at all requested`). Those two gpg interactions are ORTHOGONAL to the
resume-detection logic this finding fixes (the hazard is "does the code check for resumable state
before keygen," not "does gpg's own pinentry protocol work headlessly," which is unrelated,
pre-existing, and out of this finding's scope). This fixture therefore monkeypatches exactly TWO
call sites, both here in the fixture only, never in product code:
  * `signed_genesis.keygen_operator` -> a REAL, LIVE, non-interactive keygen into the SAME
    `gnupghome` the real function would use (the same `--batch --generate-key` mechanism
    `keygen_scripted` already uses in product code, just applied under the operator contract:
    `scratch=False`, the gnupghome is never torn down). A genuine key is generated -- this is not
    a mock of "does a key get created," only of "how the passphrase is supplied."
  * `signed_genesis.sign_statement` -> the REAL function, called with `scripted=True` forced
    (the fixture-owned key's known FIXTURE_PASSPHRASE makes this a genuine, valid signature --
    only the interactive-vs-loopback passphrase delivery differs from what the operator UI path
    would otherwise select).
Everything else -- `detect_resumable`, `discharge_keys_readme`, `export_public_key`,
`run_verify_commission`, the REAL `screen_signed_genesis` function loaded from its own file (pre-
fix from `git show HEAD:tools/setup_tui/screens.py`, post-fix from the current file, the SAME
technique seen-red/setup-tui-boundary-proc-cleanup uses) -- runs for real, against a real scratch
world and a real, dedicated (never `~/.gnupg`) scratch GNUPGHOME.

The is_scripted branch selector (`isinstance(ui, ScriptedUi)`) is what routes
`screen_signed_genesis` into its OPERATOR sub-flow (where this finding's fix lives) rather than
the `--scripted`-witnessing sub-flow (which never persists a GNUPGHOME across runs, so "resume"
is not a concept there) -- so this fixture drives it with `_OperatorLikeUi`, a small Ui subclass
that answers deterministically from a list (same mechanism as `ScriptedUi`) but is deliberately
NOT an instance of `ScriptedUi`, so `screen_signed_genesis` takes the real operator branch.

  RED (pre-fix, `git show HEAD:tools/setup_tui/screens.py`): pre-seed a partial ceremony (keygen
      -> export -> `discharge_keys_readme` -- killed BEFORE verify, per the commission's own
      witness recipe), then run the pre-fix `screen_signed_genesis` again with the SAME
      name/email/gnupghome/commission. Pre-fix code has no resume check -- it calls
      `keygen_operator` UNCONDITIONALLY a second time. Observed: TWO secret keys now in the
      GNUPGHOME (the first stranded, unrecorded).
  GREEN (post-fix, current `tools/setup_tui/screens.py`): the SAME pre-seed recipe against a
      fresh world/GNUPGHOME, then the CURRENT `screen_signed_genesis` detects the partial state,
      offers resume, and (answered "yes") completes the ceremony WITHOUT a second keygen call.
      Observed: ONE secret key throughout, and `verify-commission` returns VERIFIED.

Needs HARNESS_PGHOST (or EPISTEMIC_PGHOST, or deployment.json) and a real `gpg` on PATH --
absent either, UNEXERCISED, exit 0. Zero residue: every scratch world torn down, every scratch
GNUPGHOME removed, in a `finally`. Lazy imports banned."""
from __future__ import annotations

import importlib.util
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
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "filing"))

from pghost_resolve import resolve_pghost  # noqa: E402

from tools.setup_tui import checklist as ck  # noqa: E402
from tools.setup_tui import signed_genesis  # noqa: E402
from tools.setup_tui.ui import Ui  # noqa: E402

PGDB = "toy"
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
TEARDOWN = REPO / "bootstrap" / "teardown-world.sh"


class _OperatorLikeUi(Ui):
    """Answers deterministically from a fixed list, same mechanism as `ScriptedUi`, but is
    deliberately NOT an instance of `ScriptedUi` -- `screen_signed_genesis`'s own `is_scripted =
    isinstance(ui, ScriptedUi)` selector takes the OPERATOR sub-branch (where this finding's fix
    lives) only when `ui` is not one. Every method still ECHOES prompt+answer to stdout, matching
    `ScriptedUi`'s own contract, so this fixture's transcript reads the same way."""

    def __init__(self, answers: list[str]) -> None:
        self._answers = list(answers)
        self._i = 0

    def _next(self, prompt: str) -> str:
        if self._i >= len(self._answers):
            raise RuntimeError(
                f"_OperatorLikeUi ran out of answers at prompt {prompt!r} (had "
                f"{len(self._answers)})"
            )
        val = self._answers[self._i]
        self._i += 1
        return val

    def ask_text(self, prompt: str, default: str | None = None) -> str:
        val = self._next(prompt)
        print(f"{prompt}: {val}   [fixture-operator]")
        return val

    def ask_choice(self, prompt: str, options: list[tuple[str, str]]) -> str:
        keys = [k for k, _ in options]
        val = self._next(prompt)
        if val not in keys:
            raise RuntimeError(f"answer {val!r} for {prompt!r} not in {keys}")
        print(f"choice: {val}   [fixture-operator]")
        return val

    def confirm(self, prompt: str, default: bool = False) -> bool:
        val = self._next(prompt).lower()
        result = val in ("y", "yes", "true", "1")
        print(f"{prompt}: {'yes' if result else 'no'}   [fixture-operator]")
        return result

    def pause(self, prompt: str = "Press enter when done: ") -> None:
        val = self._next(prompt)
        print(f"{prompt}{val}   [fixture-operator]")


def sh(argv: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, **kw)


def birth(host: str, world: str, dest: str) -> None:
    r = sh(["bash", str(NEW_PROJECT), dest, "--new-world", world, "--db", PGDB, "--host", host],
           timeout=180)
    assert r.returncode == 0, f"birth of {world} failed: {(r.stdout + r.stderr)[-2000:]}"
    for verb in ("led", "verify-commission"):
        os.chmod(os.path.join(dest, verb), 0o755)


def teardown(host: str, world: str, dest: str) -> None:
    sh([str(TEARDOWN), world, "--db", PGDB, "--host", host, "--dir", dest],
       input=f"{world}\n", timeout=60)


def write_founding_commission(dest: str, statement: str) -> int:
    r = sh([os.path.join(dest, "legacy", "led"), "commission", statement],
           env={**os.environ, "LED_ACTOR": "commissioner"})
    assert r.returncode == 0, f"commission write failed: {r.stdout}{r.stderr}"
    m = re.search(r"row (\d+) written\.", r.stdout)
    assert m, f"no row id in output: {r.stdout}"
    return int(m.group(1))


def load_screens_module(source_path: str, tag: str):
    """Loads `tools/setup_tui/screens.py`'s source from `source_path` as an independent module
    object -- used to load BOTH the pre-fix (`git show HEAD:...`, written to a scratch file) and
    the post-fix (current, on-disk) versions side by side in one process, exactly the technique
    seen-red/setup-tui-boundary-proc-cleanup already established for app.py."""
    spec = importlib.util.spec_from_file_location(f"setup_tui_screens_{tag}", source_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def real_headless_keygen_operator(name: str, email: str, gnupghome: str | None, *,
                                   dry_run: bool = False) -> signed_genesis.KeygenResult:
    """The fixture's stand-in for `signed_genesis.keygen_operator` (module docstring: SCOPE) --
    a REAL, LIVE key is generated (same `--batch --generate-key` + fixture passphrase mechanism
    `keygen_scripted` already uses in product code), into the GIVEN `gnupghome` (never a fresh
    tempdir of its own, unlike `keygen_scripted`), with `scratch=False` (the operator contract:
    this gnupghome is never torn down by `teardown_scratch`). Swaps ONLY how the passphrase is
    supplied; every other observable (a new secret key lands in `gnupghome`) is real."""
    os.makedirs(gnupghome, exist_ok=True)
    os.chmod(gnupghome, 0o700)
    batch_text = (
        "Key-Type: eddsa\nKey-Curve: ed25519\nKey-Usage: sign\n"
        f"Name-Real: {name}\nName-Email: {email}\nExpire-Date: 0\n"
        f"Passphrase: {signed_genesis.FIXTURE_PASSPHRASE}\n%commit\n"
    )
    batch_path = os.path.join(gnupghome, f"keygen-{int(time.time() * 1000)}.batch")
    with open(batch_path, "w", encoding="utf-8") as f:
        f.write(batch_text)
    argv = ["gpg", "--homedir", gnupghome, "--batch", "--generate-key", batch_path]
    r = sh(argv)
    assert r.returncode == 0, f"headless keygen failed: {r.stdout}{r.stderr}"
    fprs = signed_genesis._secret_key_fingerprints(gnupghome)
    assert fprs, f"headless keygen produced no secret key in {gnupghome}"
    return signed_genesis.KeygenResult(gnupghome=gnupghome, fingerprint=fprs[-1], argv=argv,
                                        scratch=False, returncode=r.returncode)


# Captured at import time, BEFORE `main()` ever patches `signed_genesis.sign_statement` -- the
# stub below calls THIS reference, never the (by-then-patched) module attribute, to avoid
# recursing into itself.
_ORIG_SIGN_STATEMENT = signed_genesis.sign_statement


def real_forced_scripted_sign(gnupghome, statement, asc_path, *, scripted, dry_run=False):
    """The fixture's stand-in for `signed_genesis.sign_statement` (module docstring: SCOPE) --
    calls the REAL function, `scripted` forced True regardless of what the caller passed, so
    signing goes through gpg's own `--pinentry-mode loopback --passphrase` leg (which the
    fixture's own fixture-passphrase keys, generated by `real_headless_keygen_operator` above,
    genuinely accept) instead of a real interactive pinentry prompt this sandbox cannot drive."""
    return _ORIG_SIGN_STATEMENT(gnupghome, statement, asc_path, scripted=True, dry_run=dry_run)


def secret_key_count(gnupghome: str) -> int:
    return len(signed_genesis._secret_key_fingerprints(gnupghome))


def seed_partial_ceremony(dest: str, name: str, email: str, gnupghome: str) -> str:
    """Pre-seeds EXACTLY the partial state the commission's witness recipe names: "kill after
    discharge_keys_readme pre-verify" -- keygen (real, headless) -> export -> discharge the
    keys/README.md AWAITING-KEY stub -- and deliberately stops there (no sign, no verify),
    simulating a process death between the README write and the verify step. Returns the
    generated fingerprint."""
    keygen = real_headless_keygen_operator(name, email, gnupghome)
    fpr = keygen.fingerprint
    assert fpr, "seed: headless keygen produced no fingerprint"
    _res, armored = signed_genesis.export_public_key(gnupghome, fpr)
    assert armored.strip(), "seed: export produced no armored key text"
    filename = signed_genesis.key_filename(name)
    keys_path = os.path.join(dest, "keys", filename)
    with open(keys_path, "w", encoding="utf-8") as f:
        f.write(armored)
    signed_genesis.discharge_keys_readme(dest, filename, fpr, name, email)
    return fpr


def main() -> int:
    try:
        pghost = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST")
    except SystemExit as exc:
        print(f"UNEXERCISED: {exc}\nThis fixture needs a live, reachable Postgres host -- set "
              f"HARNESS_PGHOST to run it for real.")
        return 0
    if not shutil.which("gpg"):
        print("UNEXERCISED: 'gpg' not found on PATH.")
        return 0

    base = int(time.time())
    scratch = tempfile.mkdtemp(prefix="setup-tui-signed-genesis-resume-")
    live_worlds: list[tuple[str, str]] = []
    name = "AUTOHARN OPERATOR FIXTURE KEY -- THROWAWAY"
    email = "operator-fixture@example.invalid"

    # Monkeypatch (module docstring: SCOPE) -- applied to the SHARED signed_genesis module
    # object, so both the pre-fix and post-fix screens.py module loads (which each do `from
    # tools.setup_tui import signed_genesis`, resolving to this same sys.modules entry) see it.
    orig_keygen_operator = signed_genesis.keygen_operator
    orig_sign_statement = signed_genesis.sign_statement
    signed_genesis.keygen_operator = real_headless_keygen_operator
    signed_genesis.sign_statement = real_forced_scripted_sign
    try:
        prefix_screens_path = os.path.join(scratch, "screens_prefix.py")
        r = sh(["git", "-C", str(REPO), "show", "HEAD:tools/setup_tui/screens.py"])
        assert r.returncode == 0 and r.stdout.strip(), (
            f"could not read HEAD:tools/setup_tui/screens.py -- {r.stderr}"
        )
        assert "detect_resumable" not in r.stdout, (
            "fixture assumption stale: HEAD:tools/setup_tui/screens.py ALREADY carries the "
            "resume fix -- this fixture's RED leg needs a genuinely pre-fix copy"
        )
        with open(prefix_screens_path, "w", encoding="utf-8") as f:
            f.write(r.stdout)
        screens_prefix = load_screens_module(prefix_screens_path, "prefix")

        current_screens_path = str(REPO / "tools" / "setup_tui" / "screens.py")
        current_text = Path(current_screens_path).read_text(encoding="utf-8")
        assert "detect_resumable" in current_text, (
            "fixture assumption stale: the current tools/setup_tui/screens.py no longer calls "
            "detect_resumable -- update this fixture"
        )
        screens_current = load_screens_module(current_screens_path, "current")

        # ================================ RED: pre-fix screens.py ============================
        world_red = f"probeworldsgr{base}1"
        dest_red = os.path.join(scratch, "dest_red")
        gnupghome_red = os.path.join(scratch, "gnupghome_red")
        birth(pghost, world_red, dest_red)
        live_worlds.append((world_red, dest_red))
        commission_id_red = write_founding_commission(
            dest_red, "RED leg founding commission -- resume-after-death fixture.")

        seed_fpr_red = seed_partial_ceremony(dest_red, name, email, gnupghome_red)
        assert secret_key_count(gnupghome_red) == 1, "RED seed: expected exactly one key"
        readme_red = Path(dest_red, "keys", "README.md").read_text(encoding="utf-8")
        assert "KEY COMMITTED" in readme_red and seed_fpr_red in readme_red, (
            "RED seed: keys/README.md was not discharged with the seeded fingerprint"
        )

        answers_red = [
            "y",                      # run the ceremony now
            "y",                      # use existing (founding) commission
            name,                     # Key Name-Real
            email,                    # Key Name-Email
            gnupghome_red,            # GNUPGHOME (SAME as the seed -- this IS the resume case)
        ]
        cl_red = ck.Checklist()
        state_red = {"dry_run": False, "dest": dest_red}
        screens_prefix.screen_signed_genesis(_OperatorLikeUi(answers_red), cl_red, state_red)

        red_key_count = secret_key_count(gnupghome_red)
        assert red_key_count == 2, (
            f"RED leg: expected the pre-fix code to have unconditionally generated a SECOND "
            f"key (no resume check) -- got {red_key_count} key(s) in {gnupghome_red}"
        )
        print(f"RED ok (pre-fix, HEAD:tools/setup_tui/screens.py, no resume check): a SECOND "
              f"key was silently generated into {gnupghome_red} on top of the seeded partial "
              f"ceremony -- {red_key_count} secret keys now present (the first stranded, "
              f"unrecorded)")

        teardown(pghost, world_red, dest_red)
        live_worlds.remove((world_red, dest_red))

        # =============================== GREEN: post-fix screens.py ==========================
        world_green = f"probeworldsgr{base}2"
        dest_green = os.path.join(scratch, "dest_green")
        gnupghome_green = os.path.join(scratch, "gnupghome_green")
        birth(pghost, world_green, dest_green)
        live_worlds.append((world_green, dest_green))
        commission_id_green = write_founding_commission(
            dest_green, "GREEN leg founding commission -- resume-after-death fixture.")

        seed_fpr_green = seed_partial_ceremony(dest_green, name, email, gnupghome_green)
        assert secret_key_count(gnupghome_green) == 1, "GREEN seed: expected exactly one key"

        answers_green = [
            "y",                      # run the ceremony now
            "y",                      # use existing (founding) commission
            name,                     # Key Name-Real
            email,                    # Key Name-Email
            gnupghome_green,          # GNUPGHOME (SAME as the seed)
            "y",                      # [NEW] reuse the existing key? -- offered only post-fix
        ]
        cl_green = ck.Checklist()
        state_green = {"dry_run": False, "dest": dest_green}
        screens_current.screen_signed_genesis(_OperatorLikeUi(answers_green), cl_green,
                                               state_green)

        green_key_count = secret_key_count(gnupghome_green)
        assert green_key_count == 1, (
            f"GREEN leg: expected the resumed ceremony to generate NO second key -- got "
            f"{green_key_count} key(s) in {gnupghome_green}"
        )
        fprs_after = signed_genesis._secret_key_fingerprints(gnupghome_green)
        assert fprs_after == [seed_fpr_green], (
            f"GREEN leg: the ONE key present must be the SAME reused fingerprint -- "
            f"seeded {seed_fpr_green}, found {fprs_after}"
        )
        vres, body = signed_genesis.run_verify_commission(dest_green, commission_id_green)
        assert body.get("verdict") == "VERIFIED", (
            f"GREEN leg: expected verify-commission VERIFIED after resume -- got {body}: "
            f"{vres.output[-1500:]}"
        )
        print(f"GREEN ok (post-fix, current tools/setup_tui/screens.py, resume offered and "
              f"accepted): ONE key throughout ({seed_fpr_green}), no second keygen call, "
              f"verify-commission VERIFIED")

        teardown(pghost, world_green, dest_green)
        live_worlds.remove((world_green, dest_green))

        print("ALL CASES OK -- signed_genesis.py resume-after-death, red before green, real "
              "gpg + real postgres, zero residue")
        return 0
    finally:
        signed_genesis.keygen_operator = orig_keygen_operator
        signed_genesis.sign_statement = orig_sign_statement
        for world, dest in live_worlds:
            teardown(pghost, world, dest)
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
