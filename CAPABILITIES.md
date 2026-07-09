# CAPABILITIES — what the harness can already do, in plain words

Each item: what you get, how it is enforced, and how we know it works — **witnessed** means it
has fired for real at least once (the evidence is banked); **built, unexercised** means the
mechanism exists but has never fired in anger. Nothing here is aspiration; the aspirational
layer lives in `law/briefs/`. Source of record: `law/briefs/BRIEF-CONFORMANCE-MAP.md`.

## Witnessed

**1. Decisions that cannot be quietly rewritten.**
Every decision/assumption/finding is an append-only row. UPDATE, DELETE, TRUNCATE are refused by
database trigger — not by convention. Changing your mind is a *new* row linked to the old one
(`supersedes` for replacement, `amends` for one clause), so the record shows what was believed and
when, forever. *Witnessed: e17 exercised both correction tracks organically; refused mutations are
banked in `seen-red/06`.*

**2. Authorship you didn't type, so it can't be faked by typing.**
Every row is attributed. The `actor` is resolved from the database connection; on top of that, rows
written through the intercepted path carry an HMAC **stamp** binding them to the actual Claude
session/agent that wrote them — injected by a hook, unforgeable without a secret the writer's role
cannot read. A forged or stale stamp is refused at write time; a bypass write is recorded as
unstamped, visibly. *Witnessed: e17 live; forgery/staleness refusal proven by
`kernel/fixtures/s17_stamp_fixture.py`.*

**3. A second pair of eyes that has to be real.**
A review claiming independence is refused unless it was written by a *provably different
invocation* (different stamp identity) than the work it reviews — one Claude context wearing two
hats is caught mechanically, not by trust. *Witnessed once (N=1, a proof of mechanism, not a
rate): at e17 an inflated independence claim was refused live, and the genuinely independent
reviewer then caught a real defect the author's own verification had passed.*

**4. Edits gated on declared intent (refuse-and-teach).**
With the change-gate hook wired, an edit to a governed source file is *refused* unless a current
ledger entry declares that file — and the refusal message teaches the exact honest path (file the
entry, re-issue). Comply and it unlocks; both the refusal and the unlock land in a journal.
*Witnessed: the §6 acceptance run drove refusal → teach → comply → allow from a fresh clone
(`runs/acceptance-20260707T222452/`).*

**5. "Done" that can't be claimed while checks are missing.**
A close (the end-of-increment verdict) runs a registry of mandatory checks. A check that did not
run is loudly QUARANTINED — provably distinct from "passed" and from "nothing to check" — and any
OPEN finding turns the close RED: an increment cannot report complete with undischarged defects.
*Witnessed: the acceptance close came out RED-honest on 6 open findings, which is the machinery
working, not failing.*

**6. Commits gated mechanically, and every gate proven able to fail.**
Pre-commit runs the refusal chain (staging scope, lazy imports, layout/fixture censuses). Every
gate has banked **seen-red** evidence — a recorded run where it actually refused — because a gate
never seen red is a claim, not a guarantee. *Witnessed: an undeclared commit was refused from a
fresh clone; each migrated gate re-proved red (`seen-red/`).*

## Built, unexercised (exists; has not yet fired in anger)

- **Assumption validity bounds** — an assumption can carry "valid until / valid within" and an
  expiry closure exists, but no real task has posed a bounded assumption yet.
- **Review fix-point** — a close line requiring review rounds to continue until a stamp-distinct
  review finds nothing undisposed (the "iterate until clean" loop). Built for e18; gates nothing
  yet.

## Honest limits (so the guarantees aren't oversold)

- **Machine-observable events only.** The gap-detection works where a trigger is mechanical (a
  write, a commit, a close line). *Noticing* a hazard, *recognizing* an assumption — judgment
  events — have no oracle; nothing can prove one silently didn't happen. Backstop: the independent
  review (item 3) and the engineering-responsibility clause in `CLAUDE.md`.
- **The stamp is a tripwire, not authentication.** Same OS user; the secret is huntable by a
  determined local attacker. It catches drift and self-review, not a malicious admin.
- **N=1 where it says N=1.** One witnessed firing proves the mechanism exists, not how often it
  catches things.
- **Tool provenance covers the apparatus's own solvers** (engine runs bank a pinned
  engine+version+hashes record), **not yet the subject's build tools.**
