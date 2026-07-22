#!/usr/bin/env python3
"""seen-red/setup-tui-signed-genesis-key-pinning/run_fixtures.py -- RED-then-GREEN witness for
AUTOHARN_BACKFLOW.md finding 1 (a real-world birth's own finding, verbatim in the commission that
drove this fix): `bootstrap/new-project.sh`'s signed-genesis stage generated a fresh keypair and
exported it to `keys/` as the one the deployment trusts, but the genesis commission ended up signed
with a DIFFERENT, pre-existing key already in the operator's keyring -- because
`tools/setup_tui/signed_genesis.py`'s `sign_statement_act` passed no `-u`/`--local-user` to gpg, so
with more than one secret key in the effective keyring, gpg's own AMBIENT DEFAULT key signed, not
necessarily the key `export_public_key_act` had just pinned into `keys/` via the fingerprint hole.
A second, related defect in the same finding: `discharge_write_act`'s `Hole` on
`FINGERPRINT_PRODUCES` received the PRODUCING act's raw real stdout -- the multi-key
`--list-secret-keys --with-colons` dump -- and spliced it, unparsed, into `keys/README.md`'s
committed section, instead of running it through the SAME `_parse_fpr_from_colons` extractor every
other consumer (`fingerprint_hole()`) uses.

Both fixes derive the signing key from the SAME single source (`fingerprint_hole()`, over
`FINGERPRINT_PRODUCES`'s real binding) `export_public_key_act` already used -- ADR-0012 P1, a fact
has one home -- rather than leaving the signing act to trust gpg's ambient state a second,
independently-resolved way.

THE SCENARIO THIS FIXTURE BUILDS, for real: a scratch GNUPGHOME containing TWO real secret keys --
key A ("the operator's pre-existing key", generated FIRST, so it is the one gpg treats as its own
ambient default absent an explicit -u) and key B (the ceremony's OWN freshly-generated key,
generated SECOND, the one `export_public_key_act` exports to `keys/`). It then builds the exact
plan act `sign_statement_act` returns -- once from `tools/setup_tui/signed_genesis.py` AS IT STOOD
at commit PRE_FIX_COMMIT below (pinned via `importlib`, the same technique
seen-red/setup-tui-pure-core-foundation/run_fixtures.py's `_load_pinned_commit_executor` uses to
load an exact prior commit's module without touching this world's own git state), and once from the
CURRENT, fixed module -- resolves each act's real argv against a bindings dict carrying the real
`--list-secret-keys --with-colons` dump (the same shape `FINGERPRINT_PRODUCES` really binds to in
a live ceremony), runs the REAL `gpg` command each act produces, and reads back WHICH key actually
signed via `gpg --list-packets`' own `issuer fpr v4 <FULL-FINGERPRINT>` line -- never a mocked
verdict. The same bindings dict drives `discharge_write_act`'s own real `.resolve()` for the second
half of the finding.

Needs a real `gpg` on PATH (required, not optional -- UNEXERCISED, exit 0, if absent). The
operator's real `~/.gnupg` is never touched -- every key lives in a scratch, throwaway GNUPGHOME
under a fixture-owned tempdir, removed in a `finally`. Lazy imports banned.

Usage: python3 seen-red/setup-tui-signed-genesis-key-pinning/run_fixtures.py
Exit 0 if every case matches (or infra is honestly UNEXERCISED); 1 otherwise."""
from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO))

from tools.setup_tui import signed_genesis as SG  # noqa: E402 -- the CURRENT, fixed module

FAILURES: list[str] = []


def check(label: str, cond: bool, detail: object = "") -> None:
    if cond:
        print(f"  OK   {label}")
    else:
        msg = f"FAIL {label}" + (f" -- {detail}" if detail != "" else "")
        print(f"  {msg}")
        FAILURES.append(msg)


PRE_FIX_COMMIT = "1de2553"  # tools/setup_tui/signed_genesis.py as it stood immediately before the
# AUTOHARN_BACKFLOW.md finding-1 fix (no -u/--local-user on the sign act; the raw colons dump
# spliced into discharge_write_act) -- pinned EXPLICITLY, never "HEAD", per
# seen-red/setup-tui-pure-core-foundation/run_fixtures.py's own PRE_FIX_COMMIT precedent (a moving
# target already caught a fixture stale once, seen-red/setup-tui-boundary-proc-cleanup's repair).


def _load_pinned_signed_genesis(commit: str, scratch: str):
    r = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{commit}:tools/setup_tui/signed_genesis.py"],
        capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip(), (
        f"could not read {commit}:tools/setup_tui/signed_genesis.py -- {r.stderr}")
    assert '"-u", fingerprint_hole()' not in r.stdout, (
        f"fixture assumption stale: {commit}:tools/setup_tui/signed_genesis.py ALREADY carries "
        f"the -u fix -- PRE_FIX_COMMIT needs repinning to a genuinely earlier commit")
    path = os.path.join(scratch, "signed_genesis_prefix.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(r.stdout)
    spec = importlib.util.spec_from_file_location("signed_genesis_prefix", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["signed_genesis_prefix"] = mod  # (dataclass field-type resolution needs this)
    spec.loader.exec_module(mod)
    return mod


def _gpg(gnupghome: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["gpg", "--homedir", gnupghome, *args], capture_output=True, text=True)


def _generate_key(gnupghome: str, name: str, email: str) -> None:
    batch = (
        "Key-Type: eddsa\nKey-Curve: ed25519\nKey-Usage: sign\n"
        f"Name-Real: {name}\nName-Email: {email}\nExpire-Date: 0\n%no-protection\n%commit\n"
    )
    batch_path = os.path.join(gnupghome, f"batch-{email}.txt")
    with open(batch_path, "w", encoding="utf-8") as f:
        f.write(batch)
    r = _gpg(gnupghome, "--batch", "--generate-key", batch_path)
    assert r.returncode == 0, f"keygen for {email} failed: {r.stderr}"


def _fprs_from_colons(colons: str) -> list[str]:
    return [ln.split(":")[9] for ln in colons.splitlines() if ln.startswith("fpr")]


def _signing_fpr(asc_path: str) -> str:
    """The FULL fingerprint of the key that actually produced `asc_path`'s detached signature, per
    `gpg --list-packets`' own `issuer fpr v4 <fpr>` subpacket line -- a real, independent read, not
    a re-derivation from anything this fixture already computed."""
    r = subprocess.run(["gpg", "--list-packets", asc_path], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    m = re.search(r"issuer fpr v4 ([0-9A-Fa-f]+)", r.stdout)
    assert m, f"no 'issuer fpr v4' subpacket in --list-packets output:\n{r.stdout}"
    return m.group(1).upper()


def case_sign_with_wrong_vs_right_key() -> None:
    print("case: sign_statement_act -- ambient-default (RED) vs the key just generated (GREEN)")
    scratch = tempfile.mkdtemp(prefix="setup-tui-signed-genesis-key-pinning-")
    gnupghome = os.path.join(scratch, "gnupghome")
    os.makedirs(gnupghome, mode=0o700)
    try:
        # Key A -- "a different, pre-existing key already in the operator's keyring" (the backflow
        # finding's own words), generated FIRST so it is gpg's own ambient default absent -u.
        _generate_key(gnupghome, "Operator Pre-Existing Key", "operator-preexisting@example.invalid")
        # Key B -- the ceremony's OWN freshly-generated key, generated SECOND -- the one that gets
        # exported to keys/ and the one that OUGHT to sign.
        _generate_key(gnupghome, "Ceremony Generated Key", "ceremony-generated@example.invalid")

        r = _gpg(gnupghome, "--list-secret-keys", "--with-colons")
        assert r.returncode == 0, r.stderr
        colons = r.stdout
        fprs = _fprs_from_colons(colons)
        check("two real secret keys present in the scratch keyring", len(fprs) == 2, fprs)
        fpr_a, fpr_b = fprs[0], fprs[1]
        check("key B (just-generated) is the LAST fpr line -- the same convention "
              "_parse_fpr_from_colons relies on", fpr_b == fprs[-1], fprs)

        statement = "RED/GREEN fixture genesis commission statement -- never a real commission."
        # The bindings dict a real commit_executor would carry at this point in the ceremony:
        # FINGERPRINT_PRODUCES bound to list_secret_key_act's REAL raw stdout (the multi-key dump
        # -- exactly what a live ceremony sees when the operator's keyring already holds a key).
        bindings = {SG.FINGERPRINT_PRODUCES: colons}

        pre = _load_pinned_signed_genesis(PRE_FIX_COMMIT, scratch)

        # --- RED: pre-fix sign_statement_act carries no -u -> gpg's ambient default (key A, the
        # pre-existing key) signs, NOT the key export_public_key_act just exported to keys/. ------
        asc_red = os.path.join(scratch, "commission-red.asc")
        pre_act, _ = pre.sign_statement_act(gnupghome, statement, asc_red, scripted=False)
        argv_red, stdin_red = pre_act.resolve(bindings)
        check("pre-fix argv carries no -u/--local-user (the defect's own shape)",
              "-u" not in argv_red and "--local-user" not in argv_red, argv_red)
        r_red = subprocess.run(argv_red, input=stdin_red, capture_output=True, text=True)
        check("pre-fix sign command itself succeeded (exit 0)", r_red.returncode == 0, r_red.stderr)
        signer_red = _signing_fpr(asc_red)
        check("RED: pre-fix signed with the WRONG key (gpg's ambient default, the pre-existing "
              "key A) -- reproducing AUTOHARN_BACKFLOW.md finding 1 for real",
              signer_red == fpr_a, (signer_red, "fpr_a", fpr_a, "fpr_b", fpr_b))
        check("RED: pre-fix did NOT sign with the just-generated key B",
              signer_red != fpr_b, (signer_red, fpr_b))

        # --- GREEN: post-fix sign_statement_act threads -u <fingerprint_hole()> -- the SAME single
        # source export_public_key_act already reads its own --export <fpr> from. -----------------
        asc_green = os.path.join(scratch, "commission-green.asc")
        post_act, _ = SG.sign_statement_act(gnupghome, statement, asc_green, scripted=False)
        argv_green, stdin_green = post_act.resolve(bindings)
        check("post-fix argv carries -u <fingerprint>", "-u" in argv_green, argv_green)
        r_green = subprocess.run(argv_green, input=stdin_green, capture_output=True, text=True)
        check("post-fix sign command itself succeeded (exit 0)", r_green.returncode == 0,
              r_green.stderr)
        signer_green = _signing_fpr(asc_green)
        check("GREEN: post-fix signed with the JUST-GENERATED key B (matches the exported one)",
              signer_green == fpr_b, (signer_green, "fpr_a", fpr_a, "fpr_b", fpr_b))
        check("GREEN: post-fix did NOT sign with the ambient-default pre-existing key A",
              signer_green != fpr_a, (signer_green, fpr_a))

        # --- discharge_write_act's own half of the same finding: the raw multi-key colons dump vs
        # the parsed fingerprint spliced into keys/README.md's committed section. -----------------
        dest = os.path.join(scratch, "dest")
        os.makedirs(os.path.join(dest, "keys"))
        readme_path = os.path.join(dest, "keys", "README.md")
        awaiting_text = "# keys/\n\n" + SG.AWAITING_HEADER + "\n\n(no key committed yet)\n"

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(awaiting_text)
        pre_discharge = pre.discharge_write_act(dest, "ceremony-generated-key.asc",
                                                 "Ceremony Generated Key",
                                                 "ceremony-generated@example.invalid")
        _, red_content = pre_discharge.resolve(bindings)
        check("RED: pre-fix discharge spliced the RAW multi-key colons dump into README.md "
              "(gpg's own field-separator shape -- 'sec:'/'uid:' lines -- leaking key A's "
              "presence too, exactly the finding's own second half)",
              "sec:" in red_content and "uid:" in red_content, red_content[:400])
        check("RED: pre-fix discharge text does NOT carry a clean, standalone parsed fingerprint",
              f"fingerprint `{fpr_b}`" not in red_content, red_content[:400])

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(awaiting_text)
        post_discharge = SG.discharge_write_act(dest, "ceremony-generated-key.asc",
                                                  "Ceremony Generated Key",
                                                  "ceremony-generated@example.invalid")
        _, green_content = post_discharge.resolve(bindings)
        check("GREEN: post-fix discharge carries the PARSED fingerprint (the same extractor "
              "fingerprint_hole() uses), never the raw dump",
              f"fingerprint `{fpr_b}`" in green_content and "sec:" not in green_content
              and "uid:" not in green_content, green_content[:400])

        SG.teardown_scratch(gnupghome)
        check("scratch GNUPGHOME removed, zero residue", not os.path.isdir(gnupghome))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def main() -> int:
    if shutil.which("gpg") is None:
        print("UNEXERCISED: 'gpg' not found on PATH -- this fixture needs a real GnuPG binary "
              "(a scratch GNUPGHOME + two real fixture keys, never the operator's own keyring).")
        return 0
    case_sign_with_wrong_vs_right_key()
    if FAILURES:
        print(f"\n{len(FAILURES)} FAILURE(S):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("\nall cases GREEN (or honestly UNEXERCISED)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
