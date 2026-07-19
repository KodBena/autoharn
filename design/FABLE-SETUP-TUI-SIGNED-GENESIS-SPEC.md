# Setup TUI — the signed genesis: one ceremony, no further rigamarole

<!-- doc-attest-exempt: build-basis spec; attestation rides witnessed delivery -->

**Status: Fable-authored 2026-07-19, build basis. Commission: ledger row 1724
(maintainer, verbatim there) — which LIFTS, in this scoped form, the standing
crypto deferral by the maintainer's own raise. Extends
[FABLE-SETUP-TUI-SPEC.md](FABLE-SETUP-TUI-SPEC.md) (all three posture rules, the
out-of-sequence and `--dry-run` amendments bind) and builds ON the shipped GPG
trust layer (design/MAINT-GPG-TRUST-LAYER.md, `verify-commission`/`verify-chain`
templates, `filing/gpg_trust.py`, the deployment `keys/` residence with its
AWAITING-KEY stub) — it introduces NO second crypto stack, no new tooling
choice: the tooling decision is already made and ratified there.**

## The maintainer's frame, which is the design

The why-PGP-failed friction class is the target: nobody except wizards used it
right, because generation was a quiz, feedback was absent, and the ceremony was
performed once, blind. The counter-design, in his words: adopters see the
commands actually being run, in sequence, after selections are done — eased into
the workflow; an initially signed commission (if any), or bequeathal of
authority, requires **no further crypto rigamarole**; the TUI carries pointers
to the relevant documentation at the acts that need high assurance (assigning
roles and authority).

## 1. The ceremony (one new screen, between Birth and Boundary; skippable, skip recorded)

**Screen: "Signed genesis" — ON BY DEFAULT, optional by one recorded keypress.**
The maintainer's refinement (same-day, banked with the commission): optional,
and "if benign and 'no-op' for non-rigorous use, it should be turned on by
default." It qualifies: the ceremony is one-time, adds no ongoing burden (§1.5
forecloses the rigamarole class), and a skip costs one keypress recorded as
SKIPPED — so the flow PRESENTS the ceremony as the default path (confirm
default = yes), the same declared-not-silent posture the s40 family ratified
for attribution. Declining is legitimate and legible, never nagged afterward. Facts line first (feature_facts entry:
aspiration = the SIGNED commission mode, MAINT-GPG-TRUST-LAYER §3, NIST-lineage
authenticity aspiration as that spec names it; external = `gpg` binary, key
custody burden — stated plainly). Then, in order, every act shown as the exact
command before it runs (rule 1):

1. **Keygen, no quiz.** ONE fixed shape — the modern default the trust-layer
   spec's own rungs assume (ed25519, sign-only, no expiry quiz; the builder
   reads MAINT-GPG-TRUST-LAYER.md and mirrors ITS stated parameters — if it
   fixes none, ed25519/sign-only/no-expiry is this spec's fix). The passphrase
   prompt is gpg's own, interactive, never captured or scripted by the TUI.
   Under `--scripted` witnessing, a scratch GNUPGHOME with a fixture passphrase
   is used (gpg_trust.py's scratch-keyring mechanics); the OPERATOR path always
   uses the operator's choice of GNUPGHOME, default their own.
2. **Key lands where the record expects it.** Public key exported into THIS
   deployment's `keys/` (discharging the AWAITING-KEY stub with the real key
   and a one-line provenance note), shown as the exact export command. The
   private key is NEVER copied, moved, or read by the TUI — a facts line states
   where it lives (the GNUPGHOME) and that its custody is the operator's, with
   the docs pointer.
3. **Sign the genesis act.** The world's founding commission row — the
   bequeathal of authority, whichever row the operator designates as genesis
   (default: the birth's own founding commission if one was written; else the
   TUI offers to write one now, through `led`, in FULL mode first) — gets the
   SIGNED-mode detached signature at `.claude/commission-<id>.asc`, exactly the
   artifact `verify-commission` already checks. Exact gpg command shown.
4. **The gate verifies, not the keypress.** The screen runs THIS world's
   `./verify-commission <id>` and requires the verdict **VERIFIED** before
   recording the ceremony WITNESSED in the checklist. Any other outcome renders
   the verb's own teaching and records REFUSED/PREPARED honestly. This is the
   demystification lever: the operator SEES verification succeed against their
   own key, once, for real.
5. **And then it stops.** Nothing else in the flow — and nothing in the
   world's ongoing operation — demands another signature. The checklist's
   ceremony entry states this in one line: subsequent acts ride the ledger's
   own append-only record; SIGNED remains available for later commissions as a
   deliberate act (docs pointer), never a nag. No signing hooks, no signature
   gates on ordinary verbs, no expiry treadmill: v1 forecloses the rigamarole
   class by simply not building it.

## 2. Pointers at the high-assurance acts

The role-charter registration and any authority-carrying hydration act (the
catalog's authority-shaped entries, fork-provenance) get one added facts line:
"high-assurance act — see <doc>" pointing at the world's own copies of the
GPG-trust FAQ / charter docs (the world-relative paths the scaffold ships, so
the pointer is valid inside the born world, not only in autoharn's repo).
Pointers are one line each, at the point of decision, never a wall of text —
the ease-in is the sequence of real commands, not documentation homework.

## 3. Dry-run and out-of-sequence, explicitly

Under `--dry-run` the ceremony performs NO act (no keygen, no export, no
signature, no led row): every step lands in the WOULD-DO table with its exact
argv, and the verification step records DRY-SKIPPED (it cannot verify a
signature that was never made — a dry run that fakes VERIFIED would be the
exact lie the gate exists to prevent). Entered via `--start-at`, the screen
independently validates: destination exists, world has `keys/` and
`verify-commission`, `gpg` present — refusing legibly on each (the
out-of-sequence rule's standing obligation).

## 4. Witnesses (scratch worlds + scratch GNUPGHOME only; the operator's real keyring is never touched by any witness)

- **WG1** full ceremony on a scratch world: keygen → export → keys/ stub
  discharged → genesis commission signed → `verify-commission` returns
  VERIFIED — every command's real output streamed and banked; teardown zero
  residue including the scratch GNUPGHOME.
- **WG2** the red leg: tamper with the signed statement bytes (or the .asc),
  re-run `verify-commission` → FORGED-OR-CORRUPT, the gate REFUSES to record
  WITNESSED. The discriminating polarity, witnessed not assumed.
- **WG3** the legitimate-weaker path: operator skips the ceremony → checklist
  SKIPPED, world fully functional, `verify-commission` on the founding
  commission returns UNSIGNED with exit 0 (the shipped verb's own contract).
- **WG4** dry-run: ceremony under `--dry-run` → zero filesystem/keyring delta
  (mechanical before/after), WOULD-DO rows carry the exact argv, verification
  row DRY-SKIPPED.
- **WG5** out-of-sequence: `--start-at` the ceremony screen against a world
  missing `gpg` or `keys/` → legible refusal per precondition, no traceback.

## 5. Build conditions

Changes under `tools/setup_tui/` + seen-red/ (census-registered fixtures;
smoke fixture extended) + the feature_facts/durable-decisions registries as §1
requires. NO changes to `verify-commission`/`verify-chain`/`gpg_trust.py`
semantics (they are the authority this ceremony drives — TUI stays a driver of
existing verbs, rule 1); no kernel, law, serving, hooks, bootstrap-script
edits. If the shipped verbs are found unable to serve a step, STOP and report
(the Block D escalation shape) rather than working around. Python, top-of-file
imports; all gates incl. interpreter-boundary lint; per-claim witnessing; zero
residue. Doc seam per row 1699: the GPG-trust FAQ gains the ceremony's
operator walkthrough (what you type, what you should see) or the deferral is
named. SEQUENCING: builds only after the `--dry-run` build (row 1719) merges —
same package surface, and §3 depends on its choke point.
