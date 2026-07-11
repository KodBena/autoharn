# The GPG trust layer — signed ratifications, signed commissions, anchored ledgers

This document specifies how GPG (GNU Privacy Guard, the standard OpenPGP signing tool)
is applied to this project: what gets signed, by whom, what each signature proves, and
what is deliberately left unsigned. It is written for the maintainer who will hold the
key and for the executor who builds from it.

STATUS: this spec was authored by Fable (this project's name for its senior, Opus-class
authoring model, distinct from the Sonnet-class model that executes most day-to-day work —
see [CLAUDE.md's ORCHESTRATION section](../CLAUDE.md#orchestration--the-standing-delegation-contract-2026-07-09))
on 2026-07-11. The direction is maintainer-ratified
same day ("let's do it, all of it, not just the easy part"); the session sign-off concept in
§5 is the maintainer's own contribution, recorded near-verbatim. Implementation is
commissioned from this document per the delegation contract ([CLAUDE.md's ORCHESTRATION
section](../CLAUDE.md#orchestration--the-standing-delegation-contract-2026-07-09): a Sonnet-class executor builds, this document is its spec). The s26 kernel
delta below is class-ratified in shape — the pre-ratified class of strictly additive
kernel changes, defined in the same ORCHESTRATION section — and is proven before
landing on a throwaway [scratch schema](../GLOSSARY.md#scratch-schema), both polarities.

## 1. The problem, and what a signature adds

Everything the harness proves today, it proves inside one trust domain: the host and
the Postgres server. The [HMAC stamp](../GLOSSARY.md#stamp) binds a ledger row (one
record in the append-only decision log each world keeps in Postgres) to a Claude
session, but the stamp's secret lives on the host; append-only is enforced by database
triggers a superuser could drop. A GPG signature is different in kind, not degree: the private key lives
outside that domain (with the human, ideally in a hardware token), so a valid signature
is evidence that survives even a compromised host — and anyone holding the public key
can verify it while trusting none of our infrastructure. Three properties, none
otherwise available: non-repudiation, forgery resistance against the apparatus itself,
and outside-verifiability.

The corollary that shapes everything below: a signature is valuable exactly because a
HUMAN performed a deliberate act. Anything signed automatically, by a key stored on the
host, is a glorified HMAC wearing a stronger uniform — see §6.

## 2. Rung 1 — signed ratification tags (git-native, no new code)

Ratifications are currently chat utterances transcribed into commits. The upgrade: at
each ratification act, the maintainer signs a git tag naming it:

```
git tag -s ratified/adr-0017 -m "ratified with Rule 4 proviso" <commit>
git push origin ratified/adr-0017        # when the repo has a remote push policy
```

Verification (anyone, anywhere): `git verify-tag ratified/adr-0017`.

Because git history is a hash tree, one signed tag pins the ENTIRE repository state at
that commit — the law text, the attestation ledger, the banked
[seen-red](../GLOSSARY.md#seen-red) gate-refusal evidence, the solver-run provenance
records under engine/docs/ — making everything beneath it retroactively tamper-evident. The implementation ships a
verb (working name `./attest-tags`, autoharn-side) that enumerates `ratified/*` tags,
verifies each signature against the committed public key, and reports any commit
claiming ratification without a verifying tag. Refusals are loud; an unverifiable
signature is reported as a defect, never skipped.

## 3. Rung 2 — SIGNED commissions (the third signing mode)

The commission ladder becomes LAZY < FULL < SIGNED:

- LAZY — the implementing agent transcribes the ask (the maintainer's task statement,
  verbatim); marked "no commissioner guarantee".
- FULL — the commissioner types the `led commission` line from his own terminal;
  proven by actor + absent stamp.
- SIGNED — FULL, plus the file holding the ask (`~/aa` in the example below) carries a
  detached signature:

```
gpg --detach-sign --armor ~/aa            # produces ~/aa.asc, one extra line of ceremony
LED_ACTOR=commissioner ./led commission "$(cat ~/aa)"
cp ~/aa.asc <world>/.claude/commission-1.asc   # the scaffold prints these lines
```

The implementation extends the commission flow so the row's statement hash and the
banked `.asc` are verifiable together: a verification verb (working name
`./verify-commission`) recomputes the statement's digest, checks the detached signature
against the committed public key, and reports VERIFIED | UNSIGNED (a FULL/LAZY
commission — legitimate, just a weaker claim) | FORGED-OR-CORRUPT (loud, non-zero
exit). The [world](../GLOSSARY.md#world)'s auto-loaded CLAUDE.md governance preamble
teaches agents to run it at intake and to record the verdict in the first ledger row of
their task breakdown.

What SIGNED closes: "the maintainer asked for X" can no longer be manufactured by any
agent, orchestrator, or host compromise. This is the electronic-signature shape
regulators mean (unique to the signer, verifiable, bound to the record such that
alteration is detectable).

## 4. Rung 3 — the anchored ledger (kernel delta s26 + the signed head)

The deep gap, named by this project's own logic-coverage survey: tamper-evident
happens-before is owned by no logic family — it is cryptography's job.

**s26 (kernel delta, strictly additive):** every ledger row gains `row_hash` — the
SHA-256 of a canonical serialization of the row's own content concatenated with the
PREDECESSOR row's `row_hash` (the genesis row hashes a world-birth seed recorded at
scaffold). Computed by trigger at insert; NULL nowhere; existing semantics untouched.
A verification verb (working name `./verify-chain`) walks the chain and reports the
first break, if any. Scratch-witnessed both polarities (an intact chain verifies; a
surgically altered historical row breaks it AT THE ALTERED ROW) with the SQL/ASP
differential in AGREE, then enters the birth chain for the next world.

**The signed head (the human act):** at run close, the maintainer signs the chain head:

```
./verify-chain --head > /tmp/head.json     # {world, max_id, head_hash, utc}
gpg --detach-sign --armor /tmp/head.json
```

both files bank as committed evidence. From that moment, ANY retroactive alteration of
that world's ledger — including by the database superuser — breaks the chain against a
head the maintainer's key vouches for. "Append-only by trigger" becomes "append-only
or provably broken."

## 5. The session sign-off (maintainer's concept, the multi-human extension)

The maintainer, at ratification, near-verbatim: for a multi-human team "we might want
to 'sign off' on a session's total work before closing it, manually, so that's the
trust/audit link in the human world — as humans we have responsibilities that need to
be tracked as well."

For a single maintainer, §4's signed head IS this act: signing the chain head at close
says "I vouch for this session's total recorded work," and the record shows a human
took responsibility at a point in time. For a multi-human team the same mechanics
generalize without new cryptography: each human principal holds a key (fingerprints
committed per principal), signs the chain head of the sessions they supervised, and the kernel (the governance
schema every world carries) already models who OWES an attestation: a standing
[obligation](../GLOSSARY.md#obligation) on the human [principal](../GLOSSARY.md#principal),
whose unmet instances the `review_gap` debt view surfaces — so an unsigned-off session
shows as standing debt. FILED as the designed extension, not built:
autoharn has one human today, and multi-principal key ceremony (distribution,
revocation, quorum questions) deserves its own ratification when a second human exists.

## 6. What is deliberately NOT signed, and why

- **Agent-written rows.** An agent's key necessarily lives on the host the agent runs
  on — the same trust domain as everything it would attest. It proves nothing the HMAC
  stamp does not, while pretending to prove what the human key does. Refused.
- **Every commit.** Signature fatigue converts a deliberate act into a reflex; the
  value concentrates at the moments that carry authority (ratifications, commissions,
  heads). Routine commits stay under the existing gate chain.
- **Anything automated.** A cron-signed digest is a signature without a signing act.
  If a signature did not cost a human a deliberate moment, it carries no human meaning.

## 7. Key management (the real cost, kept FAQ-sized)

The maintainer generates one keypair, once (`gpg --full-generate-key`, Ed25519 type). A
hardware-backed keypair (a YubiKey-class token) is strongly preferred: the private key
physically cannot leave the token and each signature requires a touch, which makes every
signature evidence of a deliberate human act. Print the revocation certificate and store it
offline.

#### Key residence — two trust domains, kept apart

(Refined 2026-07-11, after a maintainer finding that this section's original wording
conflated them — "THIS repository should not have anything to do with end user's keys.")
The same physical keypair may sign in both domains, but the PUBLIC key is committed to a
DIFFERENT place depending on what it is signing, and a verifying verb reads only its own
domain's directory, never the other's: **autoharn's own law** — Rung 1's signed
`ratified/*` tags on THIS repository — is verified by `./attest-tags` against
`law/keys/*.asc`, fingerprint stated in `law/keys/README.md`; that directory is scoped
exclusively to autoharn's own law-signing and knows nothing of any downstream deployment.
**Every scaffolded deployment** — a world (`new-project.sh --new-world`) or a standing
project (`track-work.sh`) — carries its OWN `keys/` directory next to its own
`deployment.json`, and `verify-commission` (Rung 2) and any future signed-head verification
path (Rung 3) resolve only THAT deployment's `keys/`, never autoharn's `law/keys/` — an end
user standing up a deployment commits their signing key to their own project, never to this
repository. Rotation, in either domain, follows the same four steps: revoke the old key,
generate a new one, commit the new public key at that domain's own path, and re-sign the
current chain heads — a documented one-page procedure, exercised once on a script-generated
THROWAWAY test key (defined in the next paragraph) so it is witnessed, not aspirational.

Every verification step above ships as a scripted verb (self-application ruling: no
prose-plus-hand-gpg procedures). Witness strategy: fixtures use a script-generated (this
project's word for its own tooling is "apparatus" — CAPABILITIES.md's own opening line calls
it "autoharn's governance apparatus"; a script-generated key is one the fixture harness itself
creates via a batch `gpg --generate-key`, no human involved) THROWAWAY key, clearly marked
test-only, so both polarities are witnessed end-to-end without waiting on the maintainer's
real key; the real key slots in purely via each domain's own keys directory and
configuration.

## 8. Adoption order and status

1. Rung 1 (signed tags): available the moment the maintainer has a key — the verb and
   FAQ ship first.
2. Rung 2 (SIGNED commissions): verb + gate + preamble teaching; usable at the
   commission of run 12 (the next scaffolded [run](../GLOSSARY.md#run) after this spec).
3. Rung 3 (s26 + signed head): kernel delta with the standard ceremony; enters the
   birth chain for the next scaffolded world; the signed-head act becomes part of the
   run-close ritual — one line, FAQ'd.

Status lines below this point are maintained by the implementing commission, dated,
per ADR-0005 Rule 8.
