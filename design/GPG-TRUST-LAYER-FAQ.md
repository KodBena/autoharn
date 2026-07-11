# The GPG trust layer — operator FAQ

This page answers the question an operator actually has: **I've read
[design/GPG-TRUST-LAYER.md](GPG-TRUST-LAYER.md) and I understand WHY this project signs things —
what do I actually type?** It is a companion to that spec, not a replacement for it: read
GPG-TRUST-LAYER.md first for the reasoning (what a signature proves, what is deliberately left
unsigned, the three rungs); this page is the step-by-step "what you type, what you should see"
walkthrough for each ceremony, plus key management (generation, revocation, rotation) and the
GPG (GNU Privacy Guard, the standard OpenPGP signing tool) basics an operator who has never used
it needs.

Every command below was exercised, for real, against a THROWAWAY Ed25519 test key generated
specifically for this witness pass — never a real maintainer key. Output quoted in this page is
real command output from that pass, not a hypothetical. Where a step needs the maintainer's real
key (which does not exist yet — see [law/keys/README.md](../law/keys/README.md), currently
AWAITING-KEY), that is stated explicitly rather than silently assumed.

## 1. Key generation

This project generates one keypair, once, using **Ed25519** (a modern, fast, small
elliptic-curve algorithm — every throwaway test key used to witness this layer used it):

```sh
gpg --full-generate-key
```

Choose "(9) ECC (sign and encrypt)" or the Ed25519-specific option your `gpg` version offers, set
an expiration you're comfortable with (or none — "0" — matching the test keys used here), and
supply a real name and email when prompted. For a **non-interactive** generation (useful for
scripting, and exactly how every test key in this repository's seen-red fixtures is made — see
`seen-red/attest-tags/run_fixtures.py` for a live, runnable example), a batch file works:

```
%no-protection
Key-Type: eddsa
Key-Curve: ed25519
Key-Usage: sign
Name-Real: Your Name
Name-Email: you@example.com
Expire-Date: 0
%commit
```

```sh
gpg --batch --generate-key your-batch-file.txt
```

A hardware-backed token (a YubiKey-class device) is **strongly preferred** over the software key
generated above: the private key physically cannot leave the token, and every signature requires
a physical touch — which is what makes a signature evidence of a *deliberate human act* rather
than a key that happens to sit on a disk (design/GPG-TRUST-LAYER.md §1's whole argument). A
software key (the kind generated above, living in `~/.gnupg`) is the fallback, not the target
state.

Find your key's fingerprint (the 40-hex-character identifier every later step needs):

```sh
gpg --list-secret-keys --keyid-format=long
```

## 2. The revocation certificate — print it and store it offline, NOW

`gpg --full-generate-key` (and the batch form above) **automatically writes a revocation
certificate** to `~/.gnupg/openpgp-revocs.d/<FINGERPRINT>.rev` the moment the key is created. **Do
this before anything else, while the key is fresh:**

1. Copy that file to durable, OFFLINE storage — a USB drive in a drawer, printed on paper, not a
   second copy in the same `~/.gnupg` the key itself lives in. If the signing key is ever lost or
   compromised, this certificate is the ONLY way to tell the world "that key is no longer good" —
   losing it means a compromised key can never be cleanly disavowed.
2. Never commit it to this repository. A committed revocation certificate would let ANYONE revoke
   the maintainer's key — the opposite of what it protects.

**A revocation certificate has a colon before its `-----BEGIN` line**, deliberately — GPG prints a
warning in the file itself: *"To avoid an accidental use of this file, a colon has been inserted
before the 5 dashes below. Remove this colon with a text editor before importing."* This tripped
up this very FAQ's own witness pass (§5 below) until noticed; if `gpg --batch --import
your.rev` reports `no valid OpenPGP data found`, this is why — `sed 's/^:-----BEGIN/-----BEGIN/'`
the file first (into a COPY, never edit the original in place).

## 3. Committing the public key (only step that touches this repository)

```sh
gpg --armor --export <FINGERPRINT> > law/keys/maintainer.asc
```

Commit `law/keys/maintainer.asc`, and record its fingerprint in `law/keys/README.md` (replacing
that file's "AWAITING-KEY" section with the fingerprint and generation date) — so any later
verification is self-contained: a fresh clone never has to trust a fingerprint pasted into chat.
The **private** key and the revocation certificate never appear in this repository, ever.

Once committed, every verb below finds it automatically — `attest-tags`,
`bootstrap/templates/verify-commission.tmpl`, and `bootstrap/templates/verify-chain.tmpl` all
read `law/keys/*.asc` at the moment they run (`filing/gpg_trust.py`, their one shared home for
"build a scratch keyring from the committed keys" — see that module's own docstring for why a
scratch keyring, never the operator's ambient one).

## 4. Ceremony 1 — signing a ratification tag

At the moment the maintainer ratifies something (an ADR, a delta, a design), sign a git tag
naming it:

```sh
git tag -s ratified/adr-0017 -m "ratified with Rule 4 proviso" <commit-sha>
git push origin ratified/adr-0017    # once this repo has a remote push policy
```

Verify (anyone, anywhere, with only a clone and the committed public key):

```sh
./attest-tags
```

**Witnessed** (throwaway test key, scratch repo — `seen-red/attest-tags/red.txt` banks the full
transcript): a tag signed with a committed key reports
`[OK] ratified/adr-test -> <sha>: GOOD`, exit 0. An **unsigned** (lightweight) tag reports
`[!!] ... BAD`, with git's own `cannot verify a non-tag object` detail, exit 1. A tag signed by a
key that was never committed to `law/keys/` — the **forged** case — reports `[!!] ... BAD`, exit
1, identically loud. A commit whose message contains the word "RATIFIED" with no covering tag is
listed by id and subject as an uncovered claim. `./attest-tags` also runs cleanly against THIS
repository today: zero `ratified/*` tags exist yet, so it reports every RATIFIED-marked commit in
this repo's own history as uncovered — an honest, expected finding given no key has been
committed yet, not a bug in the tool.

## 5. Ceremony 2 — SIGNED commissions

A **commission** is the ledger row recording the operator's ask — the task a session was given,
written to the append-only ledger via `./led commission "<the ask>"` (`./led` is this project's
ledger-writing verb; `LED_ACTOR=<name>` selects which registered principal the row is attributed
to) so the ask itself is part of the governed record, not just chat. The commission ladder is
LAZY < FULL < SIGNED — three increasing strengths of guarantee about who actually made the ask:
LAZY (an implementing agent transcribes the ask it was given, no commissioner guarantee), FULL
(the commissioner types the `led commission` line himself, from his own terminal — proven by two
signals together: the row's actor, and the ABSENCE of a "stamp," this project's term for the
HMAC a Claude Code session's tool interception injects into every ledger write it makes; a row
typed from a bare shell with no live session carries no stamp at all, which is exactly what
proves a human typed it directly rather than an agent transcribing it), SIGNED (FULL, plus the
detached GPG signature this section walks through).
`bootstrap/templates/CLAUDE.md.tmpl` point 10 teaches LAZY/FULL to every agent at intake; SIGNED
is the operator's own act, below.

**Step 1 — put the ask in a file and FULL-sign it**, from your own terminal, inside the scaffolded
world. Read it into `$STATEMENT` FIRST, and use that SAME variable for the `led commission` call —
never retype or re-quote the ask a second time, which is exactly how a byte-fidelity gap could
sneak back in between two supposedly-identical copies of "the same" text:

```sh
STATEMENT="$(cat ~/aa)"
LED_ACTOR=commissioner ./led commission "$STATEMENT"
```

Note the row's `id` from the output (`./led --recent` also shows it) — the first commission of a
fresh world is `id=1`.

**Step 2 — add the detached signature** (a signature kept in its own separate file, as opposed
to a clearsigned or embedded signature bundled with the data it covers — the shape every
ceremony on this page uses), signing the SAME `$STATEMENT` from Step 1:

```sh
printf '%s' "$STATEMENT" | gpg --detach-sign --armor -o ~/aa.asc -
mkdir -p <world>/.claude
cp ~/aa.asc <world>/.claude/commission-<id>.asc
```

**Why `printf '%s' "$STATEMENT"` and not `gpg --detach-sign --armor ~/aa`** (the shape you might
reach for first): `$(cat ~/aa)` — what `led commission` actually inserts into the ledger — strips
every trailing newline. If you instead sign the raw file `~/aa` directly, and that file ends in a
newline (nearly every editor-saved file does), you are signing bytes that differ from what the
ledger stores by exactly that trailing newline — and a completely honest, unaltered commission
verifies as `FORGED-OR-CORRUPT`. This is a real defect class this project's implementation found
and closed (see `bootstrap/templates/verify-commission.tmpl`'s own module docstring for the full
account); `printf '%s'` with no trailing newline is the fix, and it is what the scaffold itself
prints at the end of every `--new-world` run — copy that block, don't retype it from memory. This
is also why Step 1 reads `$STATEMENT` from the file rather than typing the ask inline a second
time: two independently-typed copies of "the same" text are themselves a byte-fidelity hazard,
just relocated one step earlier — one file, one variable, read once, used twice.

**Step 3 — verify:**

```sh
./verify-commission --id <id>
```

**Witnessed, all outcomes** (`seen-red/verify-commission/red.txt` banks the full transcript, on a
throwaway `--new-world` scaffold with a throwaway test key):

| You did | Verdict | Exit |
|---|---|---|
| FULL-signed only, no `.asc` banked | `UNSIGNED` — "legitimate FULL-mode commission, not a defect" | 0 |
| Signed with `printf '%s'` per above, key committed | `VERIFIED` | 0 |
| The `.asc` covers a DIFFERENT statement (tampered), a committed key exists to check it against | `FORGED-OR-CORRUPT` — a real cryptographic mismatch | 1 |
| A signature is banked but `law/keys/` is empty (AWAITING-KEY, today's real state) | the DISTINCT typed refusal `NO-COMMITTED-KEY` — "nothing exists to check the claimed signature against," never confused with an actual forgery | 3 |
| `gpg` itself is not installed | the OTHER typed refusal, `GPG-UNAVAILABLE` (`"the 'gpg' binary is not on PATH"`), never folded into any of the three verdicts above | 2 |

The `NO-COMMITTED-KEY` and `GPG-UNAVAILABLE` refusals are deliberately NOT `FORGED-OR-CORRUPT`,
even though both are loud: `FORGED-OR-CORRUPT` means "a committed key exists and the signature
does not match against it" — real, checkable evidence of tampering — while a refusal means
"nothing here is decidable at all," a different fact an operator or an automated gate should
never confuse with an actual forged commission. (An earlier pass folded the no-committed-key case
into `FORGED-OR-CORRUPT`; an out-of-frame review caught it before this shipped, because doing so
would make every commission in a fresh, keyless repository — this repository's own real state
today — indistinguishable from an actual forgery by verdict string alone. See
`verify-commission.tmpl`'s own module docstring for the full account.)

Real quoted output from the witness pass (the VERIFIED case, test key committed at a scratch
`law/keys/`):

```
verify-commission: row 1 (actor=commissioner, signing_mode=FULL)
  statement: 'Build the GPG trust layer per design/GPG-TRUST-LAYER.md, all three rungs.'
  [OK] VERIFIED
        statement sha256=0584c054c8844320c9ea64e37378b7a92168cf61b2f24c87b2bec39d7eed1cbe. gpg: Signature made ...
gpg: Good signature from "AUTOHARN TEST KEY -- THROWAWAY -- NEVER A REAL MAINTAINER KEY <test-throwaway@example.invalid>" [unknown]
```

**Until a real key is committed at `law/keys/maintainer.asc`, every genuinely SIGNED commission in
this repository will refuse as `NO-COMMITTED-KEY` (exit 3)** — this is correct, honest behavior
(there is nothing to check the signature against, which is not the same fact as a forged one), not
a defect to route around. Exercise the ceremony with a throwaway test key first (§7 below) if you
want to see `VERIFIED` before the real key exists.

## 6. Ceremony 3 — the signed chain head (the run-close ritual)

At the end of a session (or whenever you want to anchor the ledger's current state against your
own key), from your own terminal, inside the world:

```sh
./verify-chain --head > /tmp/head.json
gpg --detach-sign --armor /tmp/head.json
mkdir -p <world>/.claude
cp /tmp/head.json /tmp/head.json.asc <world>/.claude/
git -C <world> add .claude/head.json .claude/head.json.asc
```

`--head` prints **exactly** `{world, max_id, head_hash, utc}` as JSON on stdout and nothing
else — deliberately, so a naive `verify-chain --head | gpg --detach-sign` never accidentally signs
a banner line along with the JSON. It **verifies the whole chain first**: if the chain is not
`INTACT`, `--head` refuses (exit 1, empty stdout, a diagnostic on stderr) rather than signing a
head over a chain it has not confirmed — signing a broken chain would manufacture false assurance,
worse than refusing.

**Witnessed, both polarities** (`seen-red/s26-row-hash-chain/red.txt`; also exercised live on a
real `--new-world` scaffold with the throwaway test key, real quoted output):

```
$ ./verify-chain --head
{"world": "s26probe1", "max_id": 2, "head_hash": "50c017270073913fe2a8052b41f40a43dcba58f035450e42844430448b2ca63a", "utc": "2026-07-11T20:14:47Z"}
$ gpg --detach-sign --armor /tmp/head.json
$ gpg --verify .claude/head.json.asc .claude/head.json
gpg: Good signature from "AUTOHARN TEST KEY -- THROWAWAY -- NEVER A REAL MAINTAINER KEY <test-throwaway@example.invalid>" [ultimate]
```

And, on a chain a historical row was surgically altered on (a scratch schema, real tamper, real
detection):

```
$ ./verify-chain
verify-chain: BROKEN -- first break at row id 1:
    stored:   c266b9dacbf6dee0277a9b6d3d015579cb4a1204e43fad21684a195526eb87d7
    expected: 7053046a90b56a06fad7fbba4593be7a3d2267b3102b457d920eafec6fcaa052
$ ./verify-chain --head
verify-chain --head: REFUSED -- chain is not INTACT (status=BROKEN, ...); signing a head over a
non-verified chain is refused, not attempted.
```

From the moment a head is signed, **any** retroactive alteration of that world's ledger —
including by the database superuser, who can bypass every trigger — breaks the chain against a
head your key vouches for. "Append-only by trigger" becomes "append-only or provably broken."

## 7. Exercising a ceremony before the real key exists

Every ceremony above works identically with a throwaway test key — that is how this whole layer
was witnessed, end to end, before any real maintainer key existed. To try one yourself:

```sh
mkdir -p /tmp/gpg-throwaway-home && chmod 700 /tmp/gpg-throwaway-home
export GNUPGHOME=/tmp/gpg-throwaway-home    # tells gpg to use THIS keyring directory instead of
                                             # your real ~/.gnupg, so the throwaway key never
                                             # mixes with (or masquerades as) your real one
gpg --batch --generate-key <(cat <<'EOF'
%no-protection
Key-Type: eddsa
Key-Curve: ed25519
Key-Usage: sign
Name-Real: My Throwaway Test Key
Name-Email: throwaway@example.invalid
Expire-Date: 0
%commit
EOF
)
```

Export the public half to wherever a verb's `--keys-dir` / `AUTOHARN` override points (never to
the real `law/keys/` in this repository — a throwaway key committed there, even briefly, is
exactly the kind of accidental-trust hazard this whole layer exists to prevent). `attest-tags
--keys-dir <path>` and `AUTOHARN=<a scratch tree with its own law/keys/> ./verify-commission` both
accept overrides for exactly this purpose — see their own `--help`-equivalent module docstrings.

## 8. Rotation — witnessed, not aspirational

Rotation is: **revoke the old key, generate a new one, commit the new public key, re-sign the
current chain heads.** This procedure was exercised, for real, on the throwaway test key used
throughout this FAQ — every command below is what was actually run, and the output is real.

**Step 1 — revoke.** Apply the revocation certificate generated at key creation (§2):

```sh
sed 's/^:-----BEGIN/-----BEGIN/' ~/.gnupg/openpgp-revocs.d/<OLD-FINGERPRINT>.rev > /tmp/revoke-clean.asc
gpg --batch --import /tmp/revoke-clean.asc
```

Witnessed output:
```
gpg: key 24E80FB7B970C89B: "AUTOHARN TEST KEY -- THROWAWAY -- NEVER A REAL MAINTAINER KEY <...>" revocation certificate imported
gpg: Total number processed: 1
gpg:    new key revocations: 1
```

**A revoked key immediately becomes unusable for NEW signing** — this is stronger than "flagged
but still works," and it was a genuine finding of this witness pass, not assumed in advance:

```sh
$ printf 'test statement' | gpg -u <OLD-FINGERPRINT> --detach-sign --armor -o /tmp/sig.asc -
gpg: skipped "<OLD-FINGERPRINT>": Unusable secret key
gpg: signing failed: Unusable secret key
```

(Signatures made **before** revocation remain cryptographically valid when checked against a
keyring that has not yet imported the revocation — revocation stops FUTURE use, it does not erase
the past. Distributing the revocation, per step 3 below, is what makes the world at large stop
trusting the old key going forward.)

**Step 2 — generate the replacement**, exactly as in §1:

```sh
gpg --full-generate-key    # or the batch form
```

**Step 3 — commit the new public key**, exactly as in §3 — `law/keys/maintainer.asc` is
overwritten with the new key's export, and `law/keys/README.md`'s recorded fingerprint updates to
match. (For a real rotation, also distribute the revocation certificate itself somewhere reachable
— a keyserver, or simply noting in the commit message that the prior fingerprint is revoked — so
verifiers who cached the old key learn not to trust it either.)

**Step 4 — re-sign the current chain heads.** For every world whose head was signed under the old
key, run Ceremony 3 (§6) again with the new key:

```sh
./verify-chain --head > /tmp/head.json
gpg --detach-sign --armor /tmp/head.json    # now signs with the NEW default key
```

Witnessed with the rotated test key (a fresh chain-head-shaped document, signed and verified):

```
$ gpg --verify head-for-resign.json.asc head-for-resign.json
gpg: Signature made Sat 11 Jul 2026 10:19:59 PM CEST
gpg:                using EDDSA key BC9E286393F4091FB19DF7CC6A4B9704D73F4360
gpg: Good signature from "AUTOHARN TEST KEY ROTATED -- THROWAWAY -- SEEN-RED <test-throwaway-rotated@example.invalid>" [ultimate]
```

That is the whole procedure: four steps, each already exercised above, none of it aspirational.

## 9. What this layer does NOT protect against (read this before trusting it)

- A superuser with schema-owner privilege on the Postgres database can still disable a trigger,
  alter a row, and re-enable the trigger — `kernel/lineage/s26-row-hash-chain.sql`'s own header
  says this plainly. What the row-hash chain adds is DETECTABILITY: the alteration becomes visible
  the moment anyone re-walks the chain, and a SIGNED head (§6) makes that detection independent of
  trusting the database at all — the signature lives outside it entirely.
- Every verb in this layer trusts only `law/keys/*.asc` — never the operator's ambient `~/.gnupg`
  keyring. If you `gpg --import` a stray key into your own keyring for an unrelated reason, it has
  no effect on what `attest-tags`, `verify-commission`, or `verify-chain` accept.
- None of this replaces the existing HMAC stamp (`kernel/lineage/s17-stamp-mechanism.sql`) — the
  stamp still proves which live invocation wrote a row; the signature layer proves a HUMAN, outside
  the host entirely, vouched for something at a point in time. They answer different questions.

## Related

- [design/GPG-TRUST-LAYER.md](GPG-TRUST-LAYER.md) — the spec this FAQ operationalizes; read it
  first for the reasoning.
- [law/keys/README.md](../law/keys/README.md) — what belongs in the committed-keys directory, and
  today's honest AWAITING-KEY state.
- [`attest-tags`](../attest-tags), [`bootstrap/templates/verify-commission.tmpl`](../bootstrap/templates/verify-commission.tmpl),
  [`bootstrap/templates/verify-chain.tmpl`](../bootstrap/templates/verify-chain.tmpl),
  [`filing/gpg_trust.py`](../filing/gpg_trust.py) — the implementation each ceremony above drives.
- [`bootstrap/templates/led.tmpl`](../bootstrap/templates/led.tmpl) — the ledger-writing verb
  (`./led` in a scaffolded world) that §5's `led commission` call and every other ledger act in
  this project go through; not part of the GPG trust layer itself, but the tool §5 assumes.
- `seen-red/attest-tags/`, `seen-red/verify-commission/`, `seen-red/s26-row-hash-chain/` — the
  banked both-polarity witness transcripts this FAQ quotes from.
