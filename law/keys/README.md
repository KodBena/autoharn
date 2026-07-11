# law/keys/ — committed GPG public keys

This directory holds the GPG (GNU Privacy Guard, the OpenPGP signing standard) **public**
keys this repository trusts for the [GPG trust layer](../../design/GPG-TRUST-LAYER.md) — the
mechanism that lets a maintainer's git tag, a ledger **commission** (the ledger row recording
an operator's ask — see [the operator FAQ](../../design/GPG-TRUST-LAYER-FAQ.md) §5), or a ledger
chain-head signature be verified by anyone, from any fresh clone, without trusting this
project's own infrastructure (`design/GPG-TRUST-LAYER.md` §1). Every file here is a **public**
key (`.asc`, ASCII-armored, safe to commit) — never a private key, never a passphrase, never a
revocation certificate (that last one is printed and stored offline per
`design/GPG-TRUST-LAYER.md` §7, deliberately **not** committed, so its existence is never leaked
alongside the key it revokes).

## Current state: AWAITING-KEY

**`law/keys/maintainer.asc` does not exist yet.** No real maintainer keypair has been
generated as of this writing. This file is a placeholder explaining what belongs here once
one is, not a fabricated key — inventing a key here would be worse than the gap it fills, since
every tool that reads this directory treats "no key" as LOUD, never a silent pass, each in its
own precise vocabulary rather than one shared word: `./attest-tags` reports `UNVERIFIABLE`,
`./verify-commission` reports the distinct refusal `NO-COMMITTED-KEY` (see "What tools do"
below for why the two are named differently, deliberately), and `./verify-chain`'s own
chain-integrity check needs no key at all — only its optional signed-head ceremony does, a
separate, human-driven act outside this tool's verdict vocabulary. A repo with no key in this
directory is honest about having no verifiable ratifications yet; a repo with a fake key would
be dishonest about having any.

## What lands here once a key exists

- **`maintainer.asc`** — the maintainer's public key, ASCII-armored (`gpg --armor --export
  <fingerprint> > law/keys/maintainer.asc`). Its **fingerprint** is then stated in the law
  (this file, replacing this section) so verification is self-contained for any clone: a
  reader never has to trust a fingerprint pasted into chat or a commit message, only the
  40-hex-character string recorded here next to the file it names.
- One `.asc` file **per additional human principal**, if and when a second human joins this
  project (design/GPG-TRUST-LAYER.md §5's filed, not-yet-built multi-principal extension) —
  each named for the principal it belongs to, each with its fingerprint recorded the same way.

## Generation guidance (FAQ-sized here; the full procedure lives in the operator FAQ)

- `gpg --full-generate-key`, Ed25519 (matches the throwaway test key's algorithm used to
  witness every verb in this layer — see `seen-red/attest-tags/`,
  `seen-red/verify-commission/`, `seen-red/s26-row-hash/`).
- **Strongly preferred: a hardware-backed token** (a YubiKey-class device) — the private key
  physically cannot leave the token, and every signature requires a physical touch, which is
  what makes a signature evidence of a *deliberate human act* rather than a key sitting on a
  disk (`design/GPG-TRUST-LAYER.md` §1's whole point).
- **Print the revocation certificate and store it offline**, away from this repository and
  away from the signing key itself. It is the only way to invalidate a compromised or
  retired key; losing it means a compromised key can never be cleanly disavowed.
- The full generation → commit → rotation walkthrough, with exact commands and the exercised
  rotation ceremony, lives in
  [`design/GPG-TRUST-LAYER-FAQ.md`](../../design/GPG-TRUST-LAYER-FAQ.md) — this stub only
  states what belongs in this directory and why nothing does yet.

## What tools do when this directory is empty (today's state)

Every verb in the GPG trust layer reads `law/keys/*.asc` at the moment it runs and degrades
**honestly**, never silently:

- `./attest-tags` reports every `ratified/*` tag as `UNVERIFIABLE` (not a pass) when no key
  is committed, and says so in its own output.
- `./verify-commission` reports `UNSIGNED` for any commission carrying no `.asc`. A FULL or
  LAZY commission (the two lighter rungs below SIGNED on this project's commission-signing
  ladder; see `design/GPG-TRUST-LAYER-FAQ.md` §5 for the full LAZY/FULL/SIGNED walkthrough) is
  still a legitimate, weaker claim. A commission that *does* carry a signature but has no key
  to check it against is never treated as passing by omission: it is refused loudly, distinctly
  from a genuinely forged signature (see `verify-commission.tmpl`'s own module docstring for the
  exact refusal shape).
- `./verify-chain --head`'s printed signing ceremony is unusable until a key exists; the
  chain-integrity check itself (`./verify-chain`, no `--head`) needs no key at all — it is a
  hash-chain walk, orthogonal to signing.

None of these tools fabricate trust in the absence of a key. This file is the honest record
of that absence, kept where the next reader — human or agent — will look first.
