# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T19:56:25Z
#   last-change: 2026-07-11T19:56:25Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""gpg_trust -- the ONE home for "build a throwaway GNUPGHOME from this repo's committed
public keys" (design/GPG-TRUST-LAYER.md; ADR-0012 P1). Three callers need exactly this
operation and none else: `attest-tags` (Rung 1, verifies `ratified/*` git tags),
`bootstrap/templates/verify-commission.tmpl` (Rung 2, verifies a signed commission's detached
signature), and `bootstrap/templates/verify-chain.tmpl` (Rung 3, verifies a signed chain-head).
Before this module each would have re-authored "import law/keys/*.asc into a scratch keyring,
never the operator's ambient one" independently -- a second/third hand-copy of the same fact
(ADR-0012 P1's B cancer: SSOT dissolved). This module is the one definition; every caller reads
it, none re-derives it.

WHY A SCRATCH KEYRING, ALWAYS (design/GPG-TRUST-LAYER.md §7): "the PUBLIC key is committed ...
so verification is self-contained for any repo clone." Verifying against the operator's default
`~/.gnupg` keyring would make a verdict depend on whatever keys happen to be imported on THIS
machine -- not reproducible from a fresh clone, and silently permissive if the operator's own
keyring happens to contain the forger's key too (imported for some unrelated reason). A scratch
GNUPGHOME containing exactly the committed `law/keys/*.asc` files closes that: the verdict
depends only on what this repository itself vouches for.

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


class GpgUnavailable(Exception):
    """Raised when the `gpg` binary itself is not on PATH -- a distinct, typed refusal from any
    verdict about a signature (design/GPG-TRUST-LAYER.md's "handle absent-gpg-binary honestly"
    instruction): a caller catches this separately and reports the missing CAPABILITY, never
    folding it into UNSIGNED/UNVERIFIABLE/FORGED-OR-CORRUPT, which are all judgments the tool
    can only make once gpg itself is present to make them with."""


def gpg_available() -> bool:
    return shutil.which("gpg") is not None


def committed_keys(keys_dir: Path) -> list[Path]:
    """Every *.asc file under keys_dir -- the committed public keys this run trusts. A README
    stub (law/keys/README.md, the AWAITING-KEY state) is never picked up by the *.asc glob."""
    if not keys_dir.is_dir():
        return []
    return sorted(keys_dir.glob("*.asc"))


def build_scratch_keyring(keys: list[Path]) -> Path:
    """A throwaway GNUPGHOME, scoped to one invocation, containing exactly `keys` -- never the
    operator's ambient default keyring. Caller tears it down (shutil.rmtree); raises
    GpgUnavailable up front if gpg is not on PATH, before creating anything on disk."""
    if not gpg_available():
        raise GpgUnavailable("the 'gpg' binary is not on PATH -- GPG trust layer verbs need "
                              "GnuPG installed (see design/GPG-TRUST-LAYER-FAQ.md)")
    home = Path(tempfile.mkdtemp(prefix="gpg-trust-scratch-"))
    home.chmod(0o700)
    for key in keys:
        r = subprocess.run(["gpg", "--homedir", str(home), "--batch", "--import", str(key)],
                            capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"failed to import committed key {key}: {r.stderr.strip()}")
    return home


def teardown_scratch_keyring(gnupghome: Path | None) -> None:
    if gnupghome is not None:
        shutil.rmtree(gnupghome, ignore_errors=True)
