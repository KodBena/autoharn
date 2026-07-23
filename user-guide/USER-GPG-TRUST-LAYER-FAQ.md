# The GPG trust layer — operator FAQ

<!-- doc-attest-exempt: legacy-led-retirement inventory pass (2026-07-23, ledger row 1149/1150)
     — the only change at this content hash is one example command's own path,
     `<dest>/legacy/led commission ...` -> `<dest>/led commission ...`, mechanical fallout of
     `bootstrap/templates/legacy-led.tmpl`'s deletion (the served path already covered
     `commission`; the example just named the wrong, now-retired shim). No other prose touched. -->

This page is written for an adopter — this page's own prose calls that reader "an operator,"
the same role. It answers the question an operator actually has: **I've read
[design/MAINT-GPG-TRUST-LAYER.md](../design/MAINT-GPG-TRUST-LAYER.md) and I understand WHY this project signs things —
what do I actually type?** It is a companion to that spec, not a replacement for it: read
MAINT-GPG-TRUST-LAYER.md first for the reasoning (what a signature proves, what is deliberately left
unsigned, the three rungs); this page is the step-by-step "what you type, what you should see"
walkthrough for each ceremony, plus key management (generation, revocation, rotation) and the
GPG (GNU Privacy Guard, the standard OpenPGP signing tool) basics an operator who has never used
it needs.

Every command below was exercised, for real, against a THROWAWAY Ed25519 (a modern, fast,
small elliptic-curve signing algorithm — §1 below says more) test key generated specifically
for this witness pass — never a real maintainer key. Output quoted in this page is
real command output from that pass, not a hypothetical. Where a step needs a real key (which
does not exist yet in either trust domain this page covers — see
[law/keys/README.md](../law/keys/README.md) for autoharn's own, currently AWAITING-KEY, and §3
below for the other domain, a deployment's own `keys/README.md`, also AWAITING-KEY until you
commit one), that is stated explicitly rather than silently assumed. **Two different trust
domains appear throughout this page, and §3 is where they first diverge** — read that section's
opening even if you skip ahead, so "the public key" never reads as one undifferentiated step.

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
than a key that happens to sit on a disk (design/MAINT-GPG-TRUST-LAYER.md §1's whole argument). A
software key (the kind generated above, living in `~/.gnupg`) is the fallback, not the target
state.

Find your key's fingerprint (the 40-hex-character identifier every later step needs):

```sh
gpg --list-secret-keys --keyid-format=long
```

### 1a. Three different things, three different names

This confusion tripped up this FAQ's own live witness pass, so it earns its own paragraph
before you go further. Key generation produces (or points at) all three at once, and every
later step in this page names exactly one of them, never interchangeably:

- **The FINGERPRINT is** the 40-hex-character string `gpg --list-secret-keys` just printed. It
  *identifies* a key; it proves nothing by itself and is safe to paste anywhere (chat, a commit
  message, this FAQ). Every `<FINGERPRINT>` placeholder in this page means this string.
- **The PUBLIC key is** the output of `gpg --armor --export <FINGERPRINT>`, an ASCII-armored
  block starting `-----BEGIN PGP PUBLIC KEY BLOCK-----`. This is the one artifact in this whole
  layer that gets **committed** (§3 below) — it is what a verifier checks a signature against,
  and committing it is safe: it contains nothing that lets anyone sign as you.
- **The REVOCATION CERTIFICATE is** a separate file GPG writes automatically at key-creation
  time (§2, next), starting (once its safety colon is removed) `-----BEGIN PGP PUBLIC KEY
  BLOCK-----` too, which is exactly why it is easy to confuse with the public key above despite
  being a completely different artifact with an opposite handling rule: it is **never
  committed, ever, to either trust domain this page covers** — printed and stored offline
  instead (§2's own instructions). The reason for the opposite rule: importing a revocation
  certificate immediately and permanently revokes the key it names (§8's rotation ceremony
  demonstrates this live) — a public key committed to a repository lets people verify your
  signatures; a revocation certificate committed to a repository lets ANYONE invalidate your
  key at will. Same-looking armor block, opposite consequence.

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
up this very FAQ's own witness pass (§8 below, the rotation ceremony's own revocation step)
until noticed; if `gpg --batch --import
your.rev` reports `no valid OpenPGP data found`, this is why — `sed 's/^:-----BEGIN/-----BEGIN/'`
the file first (into a COPY, never edit the original in place).

## 3. Committing the public key — two different places, depending on what you're signing

**This is the step an earlier draft of this FAQ got wrong**, and a maintainer finding named it
plainly (2026-07-11): *"THIS repository should not have anything to do with end user's
keys... it seems like the entire usage is convoluted in a way that any end-user would find
counter-intuitive."* There are two trust domains below, and the public key from §1 is committed
to a DIFFERENT place for each. The same physical keypair may sign in both, but never commit its
public key to both places for the same reason a house key and a car key are not the same key
just because one person carries both.

**3a. Signing autoharn's OWN law** (Rung 1 — `ratified/*` tags on autoharn itself, §4 below).
Only someone maintaining THIS repository (autoharn) does this:

```sh
gpg --armor --export <FINGERPRINT> > law/keys/maintainer.asc
```

Commit `law/keys/maintainer.asc` to the autoharn repository, and record its fingerprint in
[`law/keys/README.md`](../law/keys/README.md) (replacing that file's "AWAITING-KEY" section
with the fingerprint and generation date) — so any later verification is self-contained: a
fresh clone never has to trust a fingerprint pasted into chat. `./attest-tags` is the only
verb that reads this directory, ever.

**3b. Signing a DEPLOYMENT's own commissions and chain heads** (Rung 2 and Rung 3 — SIGNED
commissions, §5 below, and the signed chain head, §6 below). Anyone who scaffolds a
deployment — a world (`bootstrap/new-project.sh --new-world`) or a standing project
(`bootstrap/track-work.sh`) — does this **in that deployment**, never in autoharn itself:

```sh
gpg --armor --export <FINGERPRINT> > <deployment-dir>/keys/maintainer.asc
```

Commit (or otherwise keep, if the deployment is not itself version-controlled)
`<deployment-dir>/keys/maintainer.asc` alongside that deployment's own `deployment.json` — the
scaffold already wrote `<deployment-dir>/keys/README.md` there (an AWAITING-KEY stub explaining
exactly this). `verify-commission` reads ONLY this directory for that deployment, never
autoharn's `law/keys/` — an end user standing up their own deployment commits their signing key
to their OWN project, not to this repository.

In both cases, the **private** key and the revocation certificate (§2) never appear in either
repository, ever.

Once committed, the relevant verb finds it automatically: `attest-tags` reads autoharn's own
`law/keys/*.asc`; `bootstrap/templates/verify-commission.tmpl` reads the deployment's own
`keys/*.asc` — two different directories, resolved by `filing/gpg_trust.py`'s one shared "build
a scratch keyring from a set of committed keys" mechanism (see that module's own docstring),
never the operator's ambient keyring in either case.
`bootstrap/templates/verify-chain.tmpl`'s signed-head ceremony (§6) is the one ceremony on this
page that does **not** read a committed-keys directory at all: it is a direct `gpg
--detach-sign` / `gpg --verify` pair run by you, against your own ambient `~/.gnupg` keyring —
the same key that made the signature verifies it back, with nothing to commit anywhere for
that step alone.

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
(the commissioner types the `led commission` line himself, from his own terminal — evidenced by
two signals together: the row's actor, and the ABSENCE of a "stamp," this project's term for the
HMAC (hash-based message authentication code — a cryptographic checksum keyed by a secret only
the host holds) a Claude Code session's tool interception injects into every ledger write it
makes; a row
typed from a bare shell with no live session carries no stamp at all, which is consistent with
a human having typed it directly rather than an agent transcribing it), SIGNED (FULL, plus the
detached GPG signature this section walks through).

**Absence of a stamp is a rebuttable presumption, not proof.** The stamp is a disclosed
tripwire, not a hidden one: an agent transcribing a commission through a live Claude Code
session gets caught because the interception stamps its row automatically. But the stamp's
absence only tells you the row did not pass through a live, stamped session — it cannot, by
itself, rule out every other way a stampless row could arrive. Read "FULL" as what the
negative evidence supports, not as a settled fact about who typed it. **The standing rule: a
CONTESTED commission — one whose FULL status, or whose actor's identity, is disputed by anyone
with standing to dispute it — must be SIGNED (the ceremony below) before it is relied upon.**
The dispute is not resolved by re-arguing the absence-of-stamp signal harder; it is resolved by
producing the cryptographic signature that actually settles the question a negative inference
cannot.

[`bootstrap/templates/CLAUDE.md.tmpl`](../bootstrap/templates/CLAUDE.md.tmpl)'s governance-preamble
point about commission verification (search that file for "LAZY" if the point is renumbered by a
later edit — a positional "point 10" would dangle, so it is named by content here, not position)
teaches LAZY/FULL to every agent at intake; SIGNED is the operator's own act, below.

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

The witness pass covered all outcomes (`seen-red/verify-commission/red.txt` banks the full
transcript, on a throwaway `--new-world` scaffold with a throwaway test key); the table below
records them:

| You did | Verdict | Exit |
|---|---|---|
| FULL-signed only, no `.asc` banked | `UNSIGNED` — "legitimate FULL-mode commission, not a defect" | 0 |
| Signed with `printf '%s'` per above, key committed | `VERIFIED` | 0 |
| The `.asc` covers a DIFFERENT statement (tampered), a committed key exists to check it against | `FORGED-OR-CORRUPT` — a real cryptographic mismatch | 1 |
| A signature is banked but the deployment's OWN `keys/` is empty (AWAITING-KEY, a fresh scaffold's honest starting state) | the DISTINCT typed refusal `NO-COMMITTED-KEY` — "nothing exists to check the claimed signature against," never confused with an actual forgery | 3 |
| `gpg` itself is not installed | the OTHER typed refusal, `GPG-UNAVAILABLE` (`"the 'gpg' binary is not on PATH"`), never folded into any of the three verdicts above | 2 |

The `NO-COMMITTED-KEY` and `GPG-UNAVAILABLE` refusals are deliberately NOT `FORGED-OR-CORRUPT`,
even though both are loud: `FORGED-OR-CORRUPT` means "a committed key exists and the signature
does not match against it" — real, checkable evidence of tampering — while a refusal means
"nothing here is decidable at all," a different fact an operator or an automated gate should
never confuse with an actual forged commission. (An earlier pass folded the no-committed-key case
into `FORGED-OR-CORRUPT`; a fresh, independent reviewer — deliberately without the implementer's
own reasoning in view, this project's standing practice for catching self-rationalized shortcuts
before they ship ([CLAUDE.md's engineering-responsibility
corollary](../CLAUDE.md#engineering-responsibility-corollary-of-the-standard-above)) — caught it
before this shipped, because doing so
would make every commission in a fresh, keyless repository — this repository's own real state
today — indistinguishable from an actual forgery by verdict string alone. See
`verify-commission.tmpl`'s own module docstring for the full account.)

The witness pass produced this real quoted output (the VERIFIED case, test key committed at the
scaffolded world's own scratch `keys/` — never autoharn's `law/keys/`, per §3b above):

```
verify-commission: row 1 (actor=commissioner, signing_mode=FULL)
  statement: 'Build the GPG trust layer per design/GPG-TRUST-LAYER.md, all three rungs.'
  [OK] VERIFIED
        statement sha256=0584c054c8844320c9ea64e37378b7a92168cf61b2f24c87b2bec39d7eed1cbe. gpg: Signature made ...
gpg: Good signature from "AUTOHARN TEST KEY -- THROWAWAY -- NEVER A REAL MAINTAINER KEY <test-throwaway@example.invalid>" [unknown]
```

(The quoted statement text above says `design/GPG-TRUST-LAYER.md`, not
`design/MAINT-GPG-TRUST-LAYER.md` — this is the real, byte-exact commission text from before this
spec's rename to its current `MAINT-` prefixed name, quoted verbatim rather than edited to match,
per this project's own byte-fidelity discipline. Same file, old name.)

**Until a real key is committed at that deployment's own `keys/<name>.asc` (never autoharn's
`law/keys/maintainer.asc` — §3b above), every genuinely SIGNED commission in that deployment
will refuse as `NO-COMMITTED-KEY` (exit 3)** — this is correct, honest behavior (there is
nothing to check the signature against, which is not the same fact as a forged one), not a
defect to route around. Exercise the ceremony with a throwaway test key first (§7 below) if you
want to see `VERIFIED` before a real key exists.

### 5a. The setup TUI's own "Signed genesis" screen — the same ceremony, automated

If you scaffolded with `python3 -m tools.setup_tui.app` (the guided wizard —
[USER-RECIPES-FAQ.md](USER-RECIPES-FAQ.md#getting-started-the-guided-setup-tui-python3--m-toolssetup_tui)),
the "Signed genesis" screen drives exactly the Step 1–3 ceremony above for you, in order, showing
every command before it runs (`design/FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md`;
`tools/setup_tui/signed_genesis.py`) — it is a driver of the same `led`/`gpg`/`verify-commission`
verbs this FAQ already covers, not a second implementation. It sits between "Principals &
authority" and "Boundary" in the eleven-screen flow (the full ordered list, with what each
screen does, is
[USER-RECIPES-FAQ.md](USER-RECIPES-FAQ.md#getting-started-the-guided-setup-tui-python3--m-toolssetup_tui)'s
own — not repeated here), on by default (declining is one recorded keypress, never nagged
again). Everything below was exercised for real, this witness pass, against a scratch world (a
disposable `--new-world` scaffold on a scratch Postgres cluster) and a scratch `GNUPGHOME` (a
throwaway keyring in `/tmp`, torn down after) — never against the operator's real keyring,
never against a real deployment. ("This witness pass" is this page's own established term —
see the intro above, which names the throwaway Ed25519 test key every quoted command on this
page was run against.)

**The four visible commands, in order** (the same shapes as §5's Steps 1–3, just run for you):

```sh
$ <dest>/led commission '<your founding-commission statement>'
led: row 7 written.

$ gpg --homedir <scratch-or-your-GNUPGHOME> --batch --generate-key <keygen-batch-file>
gpg: revocation certificate stored as '<GNUPGHOME>/openpgp-revocs.d/<FINGERPRINT>.rev'

$ gpg --homedir <GNUPGHOME> --armor --export <FINGERPRINT>
-----BEGIN PGP PUBLIC KEY BLOCK-----
...
-----END PGP PUBLIC KEY BLOCK-----
  wrote <dest>/keys/<slug>.asc

$ gpg --homedir <GNUPGHOME> --detach-sign --armor -o <dest>/.claude/commission-<id>.asc -
$ <dest>/verify-commission --id <id> --json
```

(The operator path skips `--batch`/`--pinentry-mode loopback` — those two `gpg` flags appear
only when the TUI itself is run under ITS OWN `--scripted` flag (`python3 -m
tools.setup_tui.app --scripted <answers-file>`, the non-interactive witnessing mode this whole
page's examples were exercised under), so a fixture passphrase can drive `gpg` non-interactively
without a human at the keyboard; run the TUI interactively instead, and `gpg` prompts YOU for a
passphrase through its own pinentry, never captured or scripted by this tool.)

**The VERIFIED gate.** Step 4 is the screen's own gate, not the keypress that triggered it: it
runs `<dest>/verify-commission --id <id> --json` and only records the ceremony WITNESSED in the
closing checklist if the verdict is exactly `VERIFIED` — any other outcome (the §5 table's other
four rows) renders the verb's own teaching and records REFUSED/PREPARED honestly instead. Real,
witnessed output from this witness pass (a throwaway fixture key, ed25519, generated fresh for
this run):

```json
{
  "id": 7,
  "actor": "commissioner",
  "signing_mode": "FULL",
  "verdict": "VERIFIED",
  "detail": "statement sha256=c39c2def88fd48704800e85acf23cb92d90a37aee46e5a24af7462d64362f69f. gpg: Signature made Sun Jul 19 05:28:03 2026 CEST\ngpg:                using EDDSA key 77D9ECBB58A5B051FBB7324087647A03F4E42A66\ngpg: Good signature from \"AUTOHARN SETUP-TUI FIXTURE KEY -- THROWAWAY <setup-tui-fixture@example.invalid>\" [unknown]\ngpg: WARNING: This key is not certified with a trusted signature!\ngpg:          There is no indication that the signature belongs to the owner.\n      77D9ECBB58A5B051FBB7324087647A03F4E42A66"
}
```

Once VERIFIED lands, the screen also rewrites `<dest>/keys/README.md`'s `AWAITING-KEY` stub
into a `KEY COMMITTED` section (name, fingerprint, timestamp, a one-line pointer to this FAQ's §2
on the private key's custody) — never touching the rest of the templated file outside that one
section.

**The skip path — declining is legitimate, not a lesser world.** Answering no to "Run the Signed
genesis ceremony now?" records `SKIPPED` in the checklist and leaves the world fully functional:
`verify-commission` on that world's founding commission reads `UNSIGNED`, exit 0 — the same
honest, non-defect verdict §5's table already names, never a failure. Witnessed this witness
pass by writing a second commission with no `.asc` at all and asking the gate directly:

```json
{
  "id": 8,
  "actor": "commissioner",
  "signing_mode": "FULL",
  "verdict": "UNSIGNED",
  "detail": "no .claude/commission-8.asc found — legitimate FULL-mode commission, not a defect (spec §3: UNSIGNED is a weaker claim, never a failure)"
}
```

**Key rotation via re-run — now marker-idempotent.** Running the screen again against the same
world (`--start-at signed-genesis`, or walking the whole flow again on a later scaffold) generates
a FRESH key, re-exports it to the SAME `keys/<slug>.asc` path, re-signs the SAME designated
commission, and re-verifies — the screen offers to reuse an already-designated commission as the
genesis row rather than writing a new one every time. `keys/README.md`'s `KEY COMMITTED` section
is wrapped in explicit `BEGIN`/`END` markers and a re-run replaces only the marked middle, never
appending a second stale section — witnessed this witness pass: after a second, independent run
against the same scratch world with a brand-new fixture key, the README still carries exactly
one `KEY COMMITTED` section, now naming the new fingerprint:

```
$ grep -c "Current state: KEY COMMITTED" keys/README.md
1
- ... fingerprint `B7F87D7F0C8E895A0AED80874635E5C8221E946F`, committed 2026-07-19T03:28:22Z ...
```

(the first run's fingerprint, `77D9ECBB58A5B051FBB7324087647A03F4E42A66`, is gone — overwritten,
not appended alongside — and `verify-commission` against the same commission id re-verified
`VERIFIED` under the new key, same shape as the JSON block above.) This closes the exact hazard a
naive re-run would otherwise create: a stale first section claiming a fingerprint that is no
longer the one actually committed.

**Custody, stated plainly.** The TUI never reads, copies, or moves the private key at any point —
every act above touches only the PUBLIC half (`--armor --export`) or invokes `gpg` as a
subprocess that reads the private key from its own `GNUPGHOME` directly. Where that key lives:
your own `GNUPGHOME` (your ambient `~/.gnupg` by default, or wherever you told the ceremony's
keygen prompt to use it) if you ran the ceremony interactively; a throwaway, torn-down-after
scratch directory if you ran it under `--scripted` witnessing (never your own keyring — spec §1
item 1). What its loss means: the same as losing any signing key covered by §2 above — without
the private key OR its printed-and-stored-offline revocation certificate, you can neither sign a
future commission with this identity nor revoke it; the already-committed public key and the
signatures it already produced remain verifiable, but no NEW signature can ever again come from
that identity. Print the revocation certificate now (§2), before you need it — the ceremony does
not do this for you, by design (a one-time keygen with no further crypto rigamarole, per
`design/FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md`'s own frame).

## 6. Ceremony 3 — the signed chain head (the run-close ritual)

At the end of a session (or whenever you want to anchor the ledger's current state against your
own key), from your own terminal, inside the world, run:

```sh
./verify-chain --head > /tmp/head.json
gpg --detach-sign --armor /tmp/head.json
mkdir -p <world>/.claude
cp /tmp/head.json /tmp/head.json.asc <world>/.claude/
git -C <world> add .claude/head.json .claude/head.json.asc
```

`--head` prints **exactly** `{world, max_id, head_hash, utc, apparatus_hash}` as JSON on stdout and
nothing else — deliberately, so a naive `verify-chain --head | gpg --detach-sign` never accidentally
signs a banner line along with the JSON. It **verifies the whole chain first**: if the chain is not
`INTACT`, `--head` refuses (exit 1, empty stdout, a diagnostic on stderr) rather than signing a
head over a chain it has not confirmed — signing a broken chain would manufacture false assurance,
worse than refusing.

*(Dated append, 2026-07-12, tracker item `apparatus-flip-witnessing` — per ADR-0005 Rule 8, the worked
example just below is a point-in-time record and is not retro-edited; it predates this field.)*
`apparatus_hash` is the SHA-256 of this world's `.claude/apparatus.json` at the moment of signing
(or the literal string `"absent"` if that file does not exist) — additive to the original four-key
shape, not a redefinition of it. It rides inside the same signed head, so two signed heads whose
`apparatus_hash` differ PROVE apparatus.json changed somewhere between them — a flip of a
mechanism's mode (e.g. turning a safety hook `"off"`) between two signed heads is now provable at
zero new infrastructure: no kernel/lineage change, just one more field in the JSON object this
ceremony already signs. Stated precisely: this is weaker than the row_hash chain's own guarantee.
`./verify-chain` self-verifies the whole ledger chain in one command with no prior artifact needed;
`apparatus_hash` has no such continuous chain of custody, so proving a flip occurred means fetching
two separately-signed `head.json` files and comparing their `apparatus_hash` fields by hand (no
automated two-head-diff tool exists yet) — "provable once you compare," not "auto-flagged the way
a tampered row is." See `seen-red/s26-row-hash-chain/run_fixtures.py` case
`i-apparatus-hash-detects-flip` for a live, witnessed run: editing `.claude/apparatus.json` with
zero ledger activity produces a second head whose `apparatus_hash` differs while
`head_hash`/`max_id` stay byte-identical.

Unlike §5's `verify-commission`, this ceremony reads no committed-keys directory at all — the
`gpg --verify` step below checks the signature against YOUR OWN ambient `~/.gnupg` keyring,
the same key you just signed with. There is nothing to commit to either `law/keys/` or a
deployment's `keys/` for this specific step; §3b's deployment `keys/` directory exists for
`verify-commission`, not this ceremony.

This was witnessed on both polarities (`seen-red/s26-row-hash-chain/red.txt`; also exercised
live on a real `--new-world` scaffold with the throwaway test key, real quoted output):

```
$ ./verify-chain --head
{"world": "s26probe1", "max_id": 2, "head_hash": "50c017270073913fe2a8052b41f40a43dcba58f035450e42844430448b2ca63a", "utc": "2026-07-11T20:14:47Z"}
$ gpg --detach-sign --armor /tmp/head.json
$ gpg --verify .claude/head.json.asc .claude/head.json
gpg: Good signature from "AUTOHARN TEST KEY -- THROWAWAY -- NEVER A REAL MAINTAINER KEY <test-throwaway@example.invalid>" [ultimate]
```

And, on a chain where a historical row was surgically altered (a scratch schema, real tamper,
real detection):

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
was witnessed, end to end, before any real maintainer key existed. To try one yourself, run:

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

Export the public half to wherever the relevant verb resolves keys from for the domain you're
testing (§3 above names both): `attest-tags --keys-dir <path>` accepts an override for
autoharn's own domain — never point it at the real `law/keys/` in this repository, a throwaway
key committed there, even briefly, is exactly the kind of accidental-trust hazard this whole
layer exists to prevent. For `verify-commission`, export to a THROWAWAY deployment's own
`<deployment-dir>/keys/` (a scratch `--new-world` scaffold, torn down after — never a real
deployment's `keys/`, for the identical reason).

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

**Step 3 — commit the new public key**, exactly as in §3, at whichever domain's path the OLD key
lived at (§3a's `law/keys/maintainer.asc` for autoharn's own law, or §3b's
`<deployment-dir>/keys/<name>.asc` for a deployment) — the file there is overwritten with the
new key's export, and that domain's own `README.md`-recorded fingerprint updates to match. (For
a real rotation, also distribute the revocation certificate itself somewhere reachable — a
keyserver, or simply noting in the commit message that the prior fingerprint is revoked — so
verifiers who cached the old key learn not to trust it either.)

**Step 4 — re-sign the current chain heads.** For every world whose head was signed under the old
key, run Ceremony 3 (§6) again with the new key:

```sh
./verify-chain --head > /tmp/head.json
gpg --detach-sign --armor /tmp/head.json    # now signs with the NEW default key
```

This was witnessed with the rotated test key (a fresh chain-head-shaped document, signed and
verified):

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
- Every verb in this layer trusts only its own domain's committed-keys directory — `attest-tags`
  reads autoharn's own `law/keys/*.asc`; `verify-commission` reads a deployment's own
  `keys/*.asc` — never the operator's ambient `~/.gnupg` keyring, and never each other's
  directory (§3 above). If you `gpg --import` a stray key into your own keyring for an unrelated
  reason, it has no effect on what either verb accepts. `verify-chain`'s signed-head ceremony
  (§6) is the one exception, by design: it uses the ambient keyring directly.
- None of this replaces the existing HMAC stamp (`kernel/lineage/s17-stamp-mechanism.sql`) — the
  stamp still proves which live invocation wrote a row; the signature layer proves a HUMAN, outside
  the host entirely, vouched for something at a point in time. They answer different questions.

## Related

- [design/MAINT-GPG-TRUST-LAYER.md](../design/MAINT-GPG-TRUST-LAYER.md) — the spec this FAQ operationalizes; read it
  first for the reasoning, especially §7's key-residence split (the same two domains §3 above
  walks as a ceremony).
- [law/keys/README.md](../law/keys/README.md) — autoharn's OWN committed-keys directory (§3a),
  scoped exclusively to autoharn's own law-signing, and today's honest AWAITING-KEY state.
- A deployment's own `keys/README.md` (§3b) — written by the scaffold at
  `bootstrap/templates/keys-README.md.tmpl`; not a repo-relative link here because it lives
  inside each scaffolded deployment, not in this repository.
- [`attest-tags`](../attest-tags), [`bootstrap/templates/verify-commission.tmpl`](../bootstrap/templates/verify-commission.tmpl),
  [`bootstrap/templates/verify-chain.tmpl`](../bootstrap/templates/verify-chain.tmpl),
  [`filing/gpg_trust.py`](../filing/gpg_trust.py) — the implementation each ceremony above drives.
- [`design/FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md`](../design/FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md),
  [`tools/setup_tui/signed_genesis.py`](../tools/setup_tui/signed_genesis.py) — §5a's automated
  "Signed genesis" screen; a driver of §5's own ceremony, no second implementation.
- [`bootstrap/templates/led.tmpl`](../bootstrap/templates/led.tmpl) — the ledger-writing verb
  (`./led` in a scaffolded world) that §5's `led commission` call and every other ledger act in
  this project go through; not part of the GPG trust layer itself, but the tool §5 assumes.
- `seen-red/attest-tags/`, `seen-red/verify-commission/`, `seen-red/s26-row-hash-chain/` — the
  banked both-polarity witness transcripts this FAQ quotes from.
