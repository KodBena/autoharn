# law/keys/ — committed GPG public keys for AUTOHARN'S OWN LAW, and nothing else

This directory holds the GPG (GNU Privacy Guard, the OpenPGP signing standard) **public**
keys that verify ONE thing: signatures over THIS repository's own `ratified/*` git tags —
the maintainer's act of ratifying an ADR, a delta, or a design in autoharn's own law. It is
written for the maintainer generating or rotating this repository's own ratification key, and
for anyone reading `./attest-tags`'s output and wanting to know what it checked against. The
[GPG trust layer spec](../../design/GPG-TRUST-LAYER.md) names three signing mechanisms in
build order, calling each a "Rung" (a tier of what gets signed and how strongly, Rung 1
being the lightest): this directory serves Rung 1 only, its §2 — signed `ratified/*` tags —
and `./attest-tags` is the only verb that reads this directory. Every file here is a
**public** key (`.asc`, ASCII-armored, safe to commit) — never a private key, never a
passphrase, never a revocation certificate (that last one is printed and stored offline per
the spec's §7, deliberately **not** committed, so its existence is never leaked alongside the
key it revokes).

## This directory is scoped to autoharn's own law-signing — nothing downstream

**This directory has no bearing on any deployment's own signing.** A scaffolded deployment —
a world (`bootstrap/new-project.sh --new-world`) or a standing project
(`bootstrap/track-work.sh`) — carries its OWN `keys/` directory next to its own
`deployment.json`, used for SIGNED **commissions** — a commission is the ledger row recording
an operator's ask (see [the operator FAQ](../../design/GPG-TRUST-LAYER-FAQ.md) §5 for the full
definition and the LAZY/FULL/SIGNED ladder) — the spec's §3, Rung 2, verified by
`./verify-commission`, and any future signed chain-head verification (the spec's §4, Rung 3).
An end user standing up a deployment commits their own signing key to **their own project's
`keys/`**, never here — see that deployment's own `keys/README.md` (a stub the scaffold
writes) and [the operator FAQ](../../design/GPG-TRUST-LAYER-FAQ.md) §3 for the full
two-domain split, with the ceremony commands for each.

This boundary is deliberate and corrective: an earlier draft of the FAQ pointed every end
user's signing key at this directory, conflating autoharn's own law-signing with every
downstream deployment's commission-signing — a maintainer finding, 2026-07-11, stated
plainly: *"THIS repository should not have anything to do with end user's keys... it seems
like the entire usage is convoluted in a way that any end-user would find
counter-intuitive."* The fix is this file's boundary, stated once, here, rather than left
for a reader to infer from usage.

## Current state: AWAITING-KEY

**`law/keys/maintainer.asc` does not exist yet.** No real maintainer keypair has been
generated as of this writing. This file is a placeholder explaining what belongs here once
one is, not a fabricated key — inventing a key here would be worse than the gap it fills:
`./attest-tags` treats "no key" as LOUD, never a silent pass — it reports every `ratified/*`
tag as `UNVERIFIABLE` when this directory carries no key, and says so in its own output. A
repo with no key here is honest about having no verifiable ratifications yet; a repo with a
fake key would be dishonest about having any.

## What lands here once a key exists

- **`maintainer.asc`** — the maintainer's public key, ASCII-armored (`gpg --armor --export
  <fingerprint> > law/keys/maintainer.asc`). Its **fingerprint** is then stated in the law
  (this file, replacing this section) so verification is self-contained for any clone: a
  reader never has to trust a fingerprint pasted into chat or a commit message, only the
  40-hex-character string recorded here next to the file it names.
- One `.asc` file **per additional human principal**, if and when a second human joins this
  project's own ratification act (the spec's §5, a filed, not-yet-built multi-principal
  extension) — each named for the principal it belongs to, each with its fingerprint recorded
  the same way.

## Generation guidance (FAQ-sized here; the full procedure lives in the operator FAQ)

- Generate with `gpg --full-generate-key`, choosing Ed25519 — the same algorithm used for the
  disposable, clearly-marked-test-only keys this project generates to prove each verb works
  before a real key exists, banked as evidence under `seen-red/` (this repository's directory
  of both-polarity witness transcripts, one subdirectory per gate or verb): see
  `seen-red/attest-tags/`, `seen-red/verify-commission/`, `seen-red/s26-row-hash-chain/`.
- **Strongly preferred: a hardware-backed token** (a YubiKey-class device) — the private key
  physically cannot leave the token, and every signature requires a physical touch, which is
  what makes a signature evidence of a *deliberate human act* rather than a key sitting on a
  disk (the spec's §1, its whole point).
- **Print the revocation certificate and store it offline**, away from this repository and
  away from the signing key itself. It is the only way to invalidate a compromised or
  retired key; losing it means a compromised key can never be cleanly disavowed. The FAQ's §1a
  distinguishes this from the fingerprint and the public key, a distinction worth reading
  before generating anything.
- The full generation → commit → rotation walkthrough, with exact commands and the exercised
  rotation ceremony, lives in
  [`design/GPG-TRUST-LAYER-FAQ.md`](../../design/GPG-TRUST-LAYER-FAQ.md) — this stub only
  states what belongs in this directory and why nothing does yet.

## What `./attest-tags` does when this directory is empty (today's state)

`./attest-tags` reads `law/keys/*.asc` at the moment it runs and degrades **honestly**,
never silently: every `ratified/*` tag is reported `UNVERIFIABLE` (not a pass) when no key
is committed here, printed in the tool's own output, never fabricated trust. This file is
the honest record of that absence, kept where the next reader — human or agent — will look
first.

## Related

- [`design/GPG-TRUST-LAYER.md`](../../design/GPG-TRUST-LAYER.md) — the spec, §2 for Rung 1
  (what this directory serves) and §7's key-residence split (why this directory and a
  deployment's own `keys/` are deliberately different places).
- [`design/GPG-TRUST-LAYER-FAQ.md`](../../design/GPG-TRUST-LAYER-FAQ.md) — the operator
  walkthrough, §3 for the two-domain commit ceremony side by side.
- [`attest-tags`](../../attest-tags), [`filing/gpg_trust.py`](../../filing/gpg_trust.py) —
  the verb that reads this directory, and the shared scratch-keyring mechanics it uses.
