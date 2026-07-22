"""gpg_trust -- the ONE home for "build a throwaway GNUPGHOME from a set of committed public
keys" (design/MAINT-GPG-TRUST-LAYER.md; ADR-0012 P1). Two callers need exactly this operation and
none else: `attest-tags` (Rung 1, verifies THIS repository's own `ratified/*` git tags, against
`law/keys/*.asc`) and `bootstrap/templates/verify-commission.tmpl` (Rung 2, verifies a signed
commission's detached signature, against a DEPLOYMENT's own `keys/*.asc` -- a sibling of that
deployment's `deployment.json`, never `law/keys/`). Before this module each would have
re-authored "import a set of committed keys into a scratch keyring, never the operator's ambient
one" independently -- a second hand-copy of the same fact (ADR-0012 P1's B cancer: SSOT
dissolved). This module is the one definition; every caller reads it, none re-derives it --
callers differ in WHICH directory they pass to `committed_keys()`/`build_scratch_keyring()`,
never in HOW a scratch keyring gets built from whatever directory that is (design/
MAINT-GPG-TRUST-LAYER.md §7's key-residence split: two trust domains, one shared mechanism).

`bootstrap/templates/verify-chain.tmpl` (Rung 3) is NOT a caller of this module today, despite
earlier drafts of this docstring and user-guide/USER-GPG-TRUST-LAYER-FAQ.md claiming otherwise -- its
signed-head ceremony is an ad hoc `gpg --detach-sign` / `gpg --verify` pair run by the operator
directly against their own ambient keyring (user-guide/USER-GPG-TRUST-LAYER-FAQ.md §6), not a
committed-key lookup through this module. Corrected here rather than left to perpetuate the
same conflation a maintainer finding already caught once in the FAQ (2026-07-11, "key-residence
refactor").

WHY A SCRATCH KEYRING, ALWAYS (design/MAINT-GPG-TRUST-LAYER.md §7): "the PUBLIC key is committed ...
so verification is self-contained for any repo clone." Verifying against the operator's default
`~/.gnupg` keyring would make a verdict depend on whatever keys happen to be imported on THIS
machine -- not reproducible from a fresh clone, and silently permissive if the operator's own
keyring happens to contain the forger's key too (imported for some unrelated reason). A scratch
GNUPGHOME containing exactly the committed keys closes that: the verdict depends only on what
the relevant trust domain (autoharn's own law, or one specific deployment) itself vouches for.

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


class GpgUnavailable(Exception):
    """Raised when the `gpg` binary itself is not on PATH -- a distinct, typed refusal from any
    verdict about a signature (design/MAINT-GPG-TRUST-LAYER.md's "handle absent-gpg-binary honestly"
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
                              "GnuPG installed (see user-guide/USER-GPG-TRUST-LAYER-FAQ.md)")
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
