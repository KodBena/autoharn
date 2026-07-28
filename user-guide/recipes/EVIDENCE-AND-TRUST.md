<!-- doc-attest-exempt: the +A:B:C loop RAN and closed on this suite 2026-07-28 (A-side
pre-review + three blind suite-wide rounds, DEFECT trend 11-6-2, every DEFECT repaired,
coordinator adjudication on the record at ledger row 313; per-file doc-attestation/2
records with the full round history are appended to the attestations jsonl the same
day). This waiver marker persists ONLY because the record schema's own two-round cap
(gates/doc_attestation_presence.py refuses rounds>2 and umbrella verdicts) cannot yet
represent a three-round adjudicated loop -- filed as work item
attestation-schema-multiround; strike this marker when the schema can carry the loop
that actually ran. -->

# Evidence and trust — recipes

*Factored out of [`user-guide/USER-RECIPES-FAQ.md`](../USER-RECIPES-FAQ.md) at commit
`178ec789439044bebb664e7374c2be757d064d11`, sections "Recording verdicts and refusals as typed, queryable ledger entries
(s42/s43)", "Model identity: watchdog, attestation, defeat", "Trust ceremonies", and "Verifying
tags, signed commissions, and documentation debt"; byte-preserving (mechanical `../` depth
repairs and named cross-file link rewrites only).*

**Charter:** can I believe what the record says, and how would I prove it. Belongs: hash
coverage, refusal journaling, signatures, tag/commission verification, model-identity
attestation and defeat, documentation-debt verification. Does not belong: the documentation
review loop itself (see REVIEW-AND-GATING.md in this directory).

---

## Recording verdicts and refusals as typed, queryable ledger entries (s42/s43)

Like the [principal-identity entries](IDENTITY-AND-AUTHORITY.md#granting-and-revoking-a-principals-authority-s40s41) (covered in the identity-and-authority recipes, not this file), these three entries deviate from this page's usual
point-elsewhere convention (full witnessed output, not a one-liner plus a pointer) because the
surface is new: kernel deltas s42/s43 turn a refused write from a transaction that leaves no
trace into a committed, attributed ledger row, and widen the tamper-evidence hash chain to cover
every column instead of thirty. Delivery record:
[orchlog.d/s42-s43-typed-verdicts.md](../../orchlog.d/s42-s43-typed-verdicts.md); full spec:
[FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md](../../design/FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md).

**Prominent caveat, read before typing anything below:** none of this exists in a world whose
[birth chain](../../GLOSSARY.md#birth-chain) predates commits `1fc4e8c` (s42) and `84729de` (s43) —
runs are strictly linear, so an already-scaffolded world gains nothing here. Run `./autoharn migrate
<deployment-dir> --dry-run` to see whether your world has s42/s43; if it names them as missing,
everything below is unavailable until your next real world is born on a checkout that carries
these commits.

**What happens now when a write is refused?**
Before s42/s43, a refused write was a `RAISE EXCEPTION` that aborted the transaction — the
attempt itself left no trace anywhere but a server log. After s43, the granted database role
holds NO `INSERT` privilege on any kernel-governed table at all; every write goes through one of
four functions (`kernel.ledger_write`, `review_write`, `registration_write`,
`obligation_write`), and a refusal caught inside one of them is committed as an ordinary
`write_refused` ledger row and handed back to the caller as a typed verdict — never a silent
abort. Witnessed (`seen-red/s43-typed-verdict-write-boundary/red.txt`, case 1): a write attempted
under a revoked principal returns

```
disposition=refused, sqlstate=P0001, refusal_id=<row id>
message: "Ledger policy: strict attribution (s40) — actor principal N is revoked ..."
```

and the ledger holds a COMMITTED `write_refused` row you can look at like any other row —
`refusal_sqlstate=P0001`, `refusal_surface='ledger'`, `refusal_attempted_actor=<the revoked
principal's id>`, `refusal_attempted_role='bork'` (the server-witnessed `session_user`, never
something the client asserted), `actor=<the write-boundary tool principal>` (never the attempted
actor itself — a refused principal cannot honestly author the record of its own refusal), and a
64-hex `refusal_payload_digest` (a SHA-256 of the attempted payload — the payload's actual
content is never stored, digest only —
[FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md](../../design/FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md)'s
own rule R4, ratified for poison/privacy reasons: committing a refused payload verbatim would
hand an adversary a permanent, hash-chained storage channel). The row that was
attempted never lands; only the record that it was attempted, and refused, does.

**To look at `write_refused` rows directly:** they are ordinary ledger rows like any other, so
the same `psql`/`led show`/`./led` reading tools that work on any other row work here —
`kind = 'write_refused'` is the row to filter on, and the six `refusal_*` columns above are
where the detail lives. There is no dedicated `led` verb for this in v1 (a genuine gap, not a
hidden feature), so reading them today means a direct query or `./led show <row-id>` once you
have an id — e.g. from `./verify-chain`'s own reconciliation output (next entry) or from
scanning recent rows.

**The plain point worth internalizing: probing attempts leave traces now.** An agent (or a
person) trying a write it is not permitted to make — writing under a revoked identity, attempting
a malformed payload, retrying a refused registration — used to vanish into a rolled-back
transaction with nothing durable behind it but a server log line. After s42/s43 it does not
vanish: it becomes a permanent, attributed, hash-chained, countersignable row, exactly as durable
as a row that succeeded. This is true of ceremony refusals too, not just plain ledger writes —
review-ceremony refusals, registration-ceremony refusals (a duplicate name, a missing
`--purpose`), and malformed-payload refusals (an unknown key, a server-owned key, a bad value
cast) all journal the same way, as one `write_refused` row per refused attempt
(`seen-red/s43-typed-verdict-write-boundary/red.txt`, case 1).

**Two things this does NOT do, stated so the guarantee is not over-read.** A raw `INSERT`
attempted directly against `ledger` by the granted role never reaches the boundary at all — it
fails at the database privilege layer first (`permission denied for table ledger`, SQLSTATE
42501, witnessed case 2) and is NOT journaled as a `write_refused` row; its only residual trace
is the Postgres server log, which rotates. And a database superuser or schema owner can always
bypass every trigger and privilege check here — that bound is unchanged by this delta, and the
closing move against it remains a GPG-signed chain head (`verify-chain --head`), covered in
"Trust ceremonies" below.

**What does `verify-chain` check now?**
Two things changed, and a third check is new.

*Full coverage.* The one function the whole tamper-evidence chain rests on,
`compute_row_hash`, used to serialize only thirty of the ledger's columns (the set as of
2026-early kernel deltas) — every column added since then, twenty-two of them including all
twelve principal-identity columns, sat OUTSIDE the hash chain: a schema-owner tamper of, say,
which principal a revocation regards changed no hash, and `./verify-chain` reported the chain
`INTACT` right over the rewrite. Witnessed live, this exact scenario
(`seen-red/s42-row-hash-full-coverage/red.txt`, case 1):

```
verify-chain: INTACT -- 4 row(s) walked, head id=4 hash=<64-hex>
(exit 0)
```

— reported clean, immediately after an owner tampered `work_parent` on a committed row with
triggers disabled. After s42, `compute_row_hash` covers every ledger column except `row_hash`
itself (52 at the s42 head, 58 once s43's own six new columns are included), and the same class
of tamper is now caught (case 2, witnessed on all 52 columns individually, not sampled):

```
verify-chain: BROKEN -- first break at row id 19:
    stored:   <64-hex, the pre-tamper hash>
    expected: <64-hex, recomputed over the tampered content>
  (1 of 20 row(s) mismatch total. ...)
(exit 1)
```

*The completeness oracle — the `refusal_seq` reconciliation.* A non-transactional sequence
(`kernel.refusal_seq`) is bumped immediately before every `write_refused` row is journaled;
because a Postgres sequence's `nextval` is never rolled back, it counts every refusal attempt
that reached the boundary regardless of what happened to the surrounding transaction.
`./verify-chain` now compares the count of committed `write_refused` rows against this sequence.

*What `BROKEN` vs `FORGERY-SUSPECT` mean, and what to do on each* — drawn from the delta's own
guidance, stated plainly where the header gives no further operator action:

- **`BROKEN`** (a row's stored hash disagrees with a fresh recomputation over its own content,
  the ordinary chain-tamper report shown above): a row's content was altered after the fact.
  The delta's own header gives no remediation beyond the standing chain-integrity posture — this
  is a serious finding. **The disposition is: stop and consult, not improvise.** Do not attempt
  to "fix" a broken chain by editing rows or regenerating hashes yourself; treat it as evidence
  and escalate to whoever owns the world's integrity posture.
- **`FORGERY-SUSPECT`** (`REFUSAL-ORACLE-FORGERY-SUSPECT`, when the count of `write_refused`
  rows EXCEEDS what the sequence counted): only the boundary functions can mint a
  `write_refused` row through the sanctioned path — a payload that tries to claim
  `kind = 'write_refused'` directly is refused with a forgery-channel teach-text. This verdict
  means a `write_refused` row exists that the counting mechanism never saw mint — i.e. it was
  forged outside the sanctioned path (an owner-side direct INSERT bypassing the boundary
  entirely). Witnessed (`seen-red/s43-typed-verdict-write-boundary/red.txt`, case 3):
  ```
  verify-chain: REFUSAL-ORACLE-FORGERY-SUSPECT -- N journaled write_refused row(s) but
  the sequence only counted N-1 ... (exit 6; --head REFUSES)
  ```
  Same disposition as `BROKEN`: **stop and consult** — this is not a state to self-remediate,
  and `--head` itself refuses to sign over it. The opposite inequality (sequence count HIGHER
  than the row count) is NOT this failure — it is EXPLAIN-grade, with legitimate named causes
  (a client-side transaction that wrapped the boundary call and rolled it back; a journal-insert
  double failure) and does not, by itself, indicate tampering.
- `write_refused` rows are also unretractable by rule: nothing may supersede one
  ([FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md](../../design/FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md)'s
  own rule R6, ratified).
  If you see a row attempting to supersede a `write_refused` row, that attempt is itself refused
  and journaled — it is not a state `verify-chain` needs a separate disposition for, because it
  cannot succeed in the first place.

## Model identity: watchdog, attestation, defeat

Three pieces landed together as one arc, answering "if a session's serving model gets silently
substituted, how would I know, and what happens to what it already wrote?" Delivery record:
[orchlog.d/defeat-pipeline-and-otel-identity.md](../../orchlog.d/defeat-pipeline-and-otel-identity.md);
full specs:
[design/FABLE-OTEL-SENTRY-SPEC.md](../../design/FABLE-OTEL-SENTRY-SPEC.md) (including its dated A1/A2
amendments) and
[design/FABLE-DEFEAT-PIPELINE-SPEC.md](../../design/FABLE-DEFEAT-PIPELINE-SPEC.md) (including its dated A1
amendment).

**Read this once, before anything else on this topic: none of it is a guarantee.** Every layer
below — the watchdog, the attestations, the defeat derivation — authenticates a *pipe* (a
process, a channel, a database write path); nothing anywhere authenticates the emitter's
honesty, because the model-identity string originates inside the unauthenticated CLI process
itself. This is stated plainly in the sentry spec's own §7 standing rebuttals and carried
forward here rather than oversold: everything on this page is audit-supporting
evidence, never authentication (in NIST 800-53 terms, for readers who want the mapping: the
AU control family (Audit and Accountability), never IA-2 (Identification and Authentication -- user identity proofing)). A dishonest or silent session is observed as nothing and
defeats nothing — absence of telemetry proves nothing, permanently, in either direction.

**How would I actually notice a model substitution as it happens?** The watchdog
(`otel-watch`) is a small always-on process that tails the local OTel (OpenTelemetry) collector's export and
compares each request's observed model against the session's declared expected model; on a
mismatch it calls a mail-notification script (on this host, the maintainer's own
`notify.py`, the one that already makes his phone beep on turn completion — if you are not
him, wire your own notifier there; the watchdog just executes the configured script), so a
substitution surfaces within seconds rather than at the next audit. It writes nothing to the ledger — it is notification, not evidence. A session with no
declared expectation is reported as *unwatched*, loudly, so you can never mistake silence for
"watched and clean." **UNWITNESSED for this page:** the watchdog's own witness legs were not
re-run to produce this entry; treat its behavior as spec'd, not freshly observed here.

**How do I get a post-hoc, ledger-recorded answer for rows already written?** `./otel-attest`
is a batch verb (not a daemon) that correlates ledger rows against the collector's export and
writes one defeasible attestation row per attributable row, at one of four closed confidence
grades naming the strength of the join that earned it:

- `exact-command` — the row's own command is tied to one specific, bracketing request.
- `turn-bracketed` — command detail unavailable, but every request in the row's turn window
  agrees on one model.
- `session-scoped` — bracketing is ambiguous, but every request in the session's covering
  window still names one model.
- `ambiguous` — the window shows more than one model, or a load-bearing join failed. **As of a
  2026-07-18 spec amendment, an ambiguous attestation always writes `model=unresolved`** — never
  a fabricated single model, never an invented multi-model packing. The conflicting models are
  named in the row's `basis=` field instead. If every candidate in the window contradicts the
  declared expectation, the verdict is still `MISMATCH` (which model is unclear, but the
  substitution is not); if at least one candidate matches, the verdict is `unevaluated`; an
  ambiguous row is never written `match`. Two edge cases (the spec's A1 addendum): an
  *empty* candidate window — ambiguity via join failure, nothing in evidence at all — is
  `unevaluated`, never MISMATCH (zero evidence proves nothing); and a session with no
  declared expected model is also `unevaluated` — there is nothing to contradict.

No row is written at all when no correlated telemetry exists — absence of events is never
treated as evidence.

**A MISMATCH or ambiguous attestation is easy to miss if you only look at attestation rows —
does it surface anywhere else?** Yes: any attestation whose verdict is `MISMATCH` (including an
`ambiguous` row whose verdict resolves to `MISMATCH` per the rule above) additionally writes a
companion `finding` ledger row, so it lands in ordinary review flow instead of sitting quietly
in attestation bulk.

**What happened to `./otel-attest`'s first build, and is it safe to use now?** It was
adversarially reviewed (ledger row 1505) and found to silently fold every `ambiguous` case into
the write-nothing path — the opposite of the spec's own rule. The verb was held out of service
until the fix landed (commit `c3301e5`) and is back in service now, with the `model=unresolved`
behavior above, plus a write-time refusal on any field value containing a `|` or newline (an
unauthenticated model string could otherwise corrupt the row's later parse).

**How do I see what a MISMATCH actually does to derived standing?** `./judge --layer defeat`
derives it: a ledger row backed by an unsuperseded mismatch attestation, written by a principal
holding an unsuperseded, active competence grant for `model-identity-attestation`, is excluded
from the `credited` reading, computed fresh by two independent producers (a SQL twin and an ASP
program) required to agree bit-for-bit. Nothing is edited or deleted — a defeated row stays
fully visible in raw history, always shown together with its cause. **WITNESSED**, run
read-only against this repository's own live world (2026-07-18):

```sh
$ ./judge --layer defeat
```
(2026-07-27 correction, root-shim-pruning residue sweep, ledger row 1357: dated 2026-07-18,
eight days before the umbrella-CLI scaffold migration, rows 1365/1366/1367, 2026-07-26,
retired the bare `./judge` shim this transcript typed — left as the dated record it is; the
current equivalent invocation is `./autoharn judge --layer defeat`.)
```
# marriage differential -- layer='defeat'
#   closed verdict vocabulary: ['AGREE', 'DIVERGE_BY_DESIGN', 'DIVERGE_DEFECT', 'QUARANTINED']; RED = ['DIVERGE_DEFECT', 'QUARANTINED']

  [!! ] autoharn1 QUARANTINED        asp=0 sql=0 atoms; Δasp=[] Δsql=[]
          asp QUARANTINED: EDB export failed: CapabilityError: target 'autoharn1' did not emit trust_grant/n (capability absent): no principal_binding_active/principal_competence_activity columns on this schema (pre-s41 lineage) -- capability absent, not record-empty. A silent empty here would be the F49 vacuous-pass; refusing loudly.
          sql QUARANTINED: EDB export failed: CapabilityError: target 'autoharn1' did not emit trust_grant/n (capability absent): no principal_binding_active/principal_competence_activity columns on this schema (pre-s41 lineage) -- capability absent, not record-empty. A silent empty here would be the F49 vacuous-pass; refusing loudly.

# DIFFERENTIAL RED -- a target diverged/quarantined (NO RESULT)
```

This is a QUARANTINE, not a bug: the defeat pipeline needs typed competence grants (s41) to
derive anything, and this repository's own live world predates s41, so both producers refuse
loudly with the same named reason rather than silently reading an empty derivation as "nothing
is defeated" — the exact vacuous-pass mistake this design forecloses on purpose. A world whose
birth chain carries s41 or later will derive real `credited`/`model_defeated` results here
instead of this refusal.

**Does suspending or revoking the attesting principal change what it already defeated?** No —
see ["Suspending, reviving, and revoking a principal's standing (s45)"](IDENTITY-AND-AUTHORITY.md#suspending-reviving-and-revoking-a-principals-standing-s45) (in the identity-and-authority recipes): standing never conditions defeat, by ratified rule. A
suspended or revoked principal's past mismatch attestations, under a still-in-force competence
grant, keep defeating exactly as before; only superseding the grant or the attestation itself
changes what is credited.

**Honest limits, carried forward rather than oversold:**

- The ceiling is permanent, not a v1 gap: nothing here can ever prove which model served a
  request, only observe and record what the emitting process claimed. The sentry spec names the
  one thing that would close this — provider-side response signing — and it does not exist.
- The watchdog fails silent on its own death or a mail failure; a `--heartbeat` option is an
  opt-in mitigation, not a default.
- The typed kernel form of an attestation (kernel delta `s44`) and its dedicated credited-read
  views are authored in the specs above but not yet in any birth chain; until an s44+ world
  exists, `./otel-attest`'s rows are ordinary `verification` rows, and the engine-side
  computation shown above is the only way to see `credited`/`model_defeated` at all.
- A malformed attestation row halts derivation for its whole target until it is superseded —
  deliberate (fail loud beats skip silent), but a real operational cost if it happens.

## Trust ceremonies

**Can I prove a commission really came from me?** (a "commission" here is a ledgered
instruction attributed to a principal — the maintainer or an agent acting for them — and the
question is how strongly that attribution can be trusted). Full grammar and worked walkthrough:
[USER-GPG-TRUST-LAYER-FAQ.md](../USER-GPG-TRUST-LAYER-FAQ.md) §5–§7.
Yes, and it comes in three increasing strengths: **LAZY** (the row's stated actor is taken on
its word, no cryptographic or structural check), **FULL** (the right actor recorded on the row,
plus the absence of the interception stamp a hook adds only when an agent — not the maintainer
directly — wrote the row: a rebuttable presumption, not proof), and **SIGNED** (a detached GPG
signature over the row, checked against a known key — the only strength that survives a
dispute). The standing rule is that a **CONTESTED** commission (one whose attributed actor is
disputed after the fact) must be SIGNED to stand. You can rehearse every ceremony with a
throwaway key before any real key exists.

**Can I anchor the ledger so later tampering is provable?**
Yes — sign the chain head at run close (`verify-chain --head`, then a detached signature).
Any retroactive row alteration then breaks provably against a head your key vouches for;
the head also carries the apparatus-config hash, so a mechanism flipped off between two
signed heads is provable by comparing them. Known honest limits: the chain-hash mechanism proves
tampering with rows *between* two signed heads, but a deleted row at the very tail of the chain
(the newest end, appended after the last signature) is invisible to the chain alone — nothing
has signed over it yet (tracker item `s26-tail-deletion-witness` holds the designed fix — a
ledger row, not a committed page: `./autoharn led show s26-tail-deletion-witness` at the repository root
reads it), and the
apparatus comparison is manual, not auto-flagged.
Walkthrough: [USER-GPG-TRUST-LAYER-FAQ.md](../USER-GPG-TRUST-LAYER-FAQ.md) §6.

## Verifying tags, signed commissions, and documentation debt (`attest-tags`, `verify-commission`, `attest-doc`, `distance-to-clean`)

This section covers four related, but separately-invoked, operator verbs that all answer some
version of "is this claim on the record actually checkable, or only asserted?": `attest-tags`
(are the commit tags claiming ratification really signed by a committed key?),
`verify-commission` (does a signed commission's banked signature actually match the ledger
row's current bytes?), `attest-doc` (has a document been through a fresh-context read at its
CURRENT bytes, per [ADR-0017](../../law/adr/0017-the-zero-context-reader.md)'s zero-context-reader
test?), and `distance-to-clean`'s composed DOC-ATTESTATION section (which reads the identical
classification `attest-doc check` reads, folded into one debt total alongside review-gap,
question-status, and work-item debt). This work traces to the maintainer's 2026-07-18 overnight
batch, item 11 ("attest-tags (zero mentions) ... A:B:C with live transcripts"), tracked as
ledger item `overnight-batch-doc-backfill` (claimed row 1606, parent
`post-freeze-documentation-debt` — a ledger row, not a committed page: `./autoharn led show 1606` at the
repository root reads it in full).

**Can I check whether this repository's own `ratified/*` git tags are honestly signed?**
Yes — `attest-tags` is a repo-root operator verb ([MAINT-GPG-TRUST-LAYER.md](../../design/MAINT-GPG-TRUST-LAYER.md)
§2's "Rung 1"; it verifies THIS repo's own tags, so unlike `led`/`judge`/`pickup` it is never scaffolded into a
deployment) that enumerates every `ratified/*` tag, verifies each one with `git verify-tag`
against ONLY the committed public key(s) in `--keys-dir` (default `law/keys/*.asc`) — built as a
throwaway `GNUPGHOME` per invocation, never the operator's ambient keyring — and separately
flags any commit whose message contains a standalone "RATIFIED" marker but is not the exact
target of a tag that verified GOOD. It reports three per-tag verdicts, all printed, none silent:
`GOOD` (verified against a committed key), `BAD` (a real cryptographic mismatch — tampered,
unsigned, or signed by an uncommitted key), and `UNVERIFIABLE` (no public key is committed at
all — this repository's own honest state today under the standing crypto-generation deferral,
named so it is never mistaken for a pass). Exit 0 only if every enumerated tag verified GOOD and
every RATIFIED-marked commit is covered by one.

Run bare against this checkout (`./autoharn attest-tags`, no flags), the tool reports its own honest
starting state — every tag UNVERIFIABLE because `law/keys/` carries no committed key yet, plus a
list of RATIFIED-marked commits with no covering tag (this checkout's own commit history is long
and largely off-topic for this FAQ entry, so only the header is quoted here; the finding-by-
finding detail below exercises every verdict shape instead). This WITNESSED run's header lines
show `./autoharn attest-tags` against this checkout:
```sh
$ ./autoharn attest-tags
```
```
attest-tags: /home/bork/w/vdc/1/autoharn
  keys committed in /home/bork/w/vdc/1/autoharn/law/keys: 0  (AWAITING-KEY — see law/keys/README.md; every tag below is UNVERIFIABLE until a key lands)
  ratified/* tags: 0

  29 commit(s) claim ratification with no verifying ratified/* tag:
  ...
```
(exit 1). To see every verdict shape (`GOOD`, `BAD`, and the exit-0 all-covered case, not only
`UNVERIFIABLE`), the verb's own `--repo`/`--keys-dir` overrides — documented in its own usage
text as "the witness harness's own use: a scratch repo + a scratch keys dir carrying a THROWAWAY
test key" — point it at a small scratch git repository built for exactly this purpose, with a
throwaway GPG key generated under a scratch `GNUPGHOME` (never the operator's own keyring), one
commit claiming ratification with no tag at all, one whose tag is genuinely signed and covers it,
and one whose tag was tampered after signing. That scratch repo, with the throwaway key
committed, WITNESSED all three non-clean verdicts in one run:
```sh
$ ./autoharn attest-tags --repo /tmp/.../repo --keys-dir /tmp/.../keys-real
```
```
attest-tags: /tmp/.../repo
  keys committed in /tmp/.../keys-real: 1
  ratified/* tags: 2
  [!!] ratified/bad-case -> 4dbfc127374d65f9343195a172d1a9ac77bd483c: BAD
        error: ratified/bad-case: cannot verify a non-tag object of type commit.
  [OK] ratified/good-case -> a050bf2d4c6465a3d07c1f16e88750c3c8d6cf26: GOOD

  2 commit(s) claim ratification with no verifying ratified/* tag:
    !! 9ee65db42b4a RATIFIED: a claim whose tag will be tampered/BAD
    !! 16fec35929eb RATIFIED: a claim with no tag at all (uncovered case)

attest-tags: FINDINGS ABOVE — see marks (exit 1)
```
A second scratch repo, with a single RATIFIED-marked commit whose tag is real and covering,
WITNESSED the clean, exit-0 case:
```sh
$ ./autoharn attest-tags --repo /tmp/.../repo-clean --keys-dir /tmp/.../keys-real
```
```
attest-tags: /tmp/.../repo-clean
  keys committed in /tmp/.../keys-real: 1
  ratified/* tags: 1
  [OK] ratified/only-case -> d20638cf8a5f9dd6c8fabc7fa0efeb0f973ee4a0: GOOD

  every RATIFIED-marked commit is covered by a GOOD tag (or none exist to claim).

attest-tags: clean (exit 0)
```
`--json` prints the same three verdicts machine-readably (`tags`, `uncovered_ratification_claims`,
`ok`); run WITNESSED against the same key-and-tag scratch repo above, it printed `"ok": false`
with the `BAD` tag's detail and both uncovered SHAs enumerated by field (exit 1).

**Can I check that a specific ledger commission row's banked GPG signature is actually genuine
and current?** Yes — `verify-commission` ([MAINT-GPG-TRUST-LAYER.md](../../design/MAINT-GPG-TRUST-LAYER.md) §3's "Rung 2") reads
one `commission`-kind ledger row (most recent by default, or `--id N`), recomputes the
statement's SHA-256 digest from the row's OWN current bytes (never a caller-supplied digest),
and — if a `.claude/commission-<id>.asc` is banked — checks it against ONLY this deployment's own
`keys/*.asc` (a sibling of its `deployment.json`; never autoharn's `law/keys/`, a deliberate
split named in its own module docstring's "KEY-RESIDENCE REVISION" note). It reaches one of five
closed determinations, journaled to `.claude/logs/verify_commission.jsonl` on every run
regardless of which one fires: three verdicts — `VERIFIED` (0, a signed statement whose current
bytes match a
checkable signature), `UNSIGNED` (0, a legitimate weaker claim — LAZY or FULL mode, no `.asc`
banked at all, never a defect), `FORGED-OR-CORRUPT` (1, a real cryptographic mismatch) — plus two
typed refusals distinct from all three, because neither leaves any verdict decidable:
`GPG-UNAVAILABLE` (2, `gpg` itself missing) and `NO-COMMITTED-KEY` (3, a signature is banked but
this deployment's own `keys/` is empty — distinct from `FORGED-OR-CORRUPT`, mirroring
`attest-tags`'s own `UNVERIFIABLE`, per the module docstring's dated REVISION NOTE explaining why
an earlier version wrongly folded the two together).

All five were WITNESSED on a scratch deployment (`bootstrap/new-project.sh --new-world`, torn
down after). The first case shows what happens with no commission row at all:
```sh
$ ./verify-commission
```
```
verify-commission: no commission row found (any commission row) in faq11probe.ledger
```
(exit 2). Writing a LAZY-mode commission (`./led commission "..."`, no `.asc` banked) and
checking it produces:
```
verify-commission: row 7 (actor=author, signing_mode=LAZY)
  statement: 'probe commission, LAZY mode (vicarious transcription), for FAQ item 11 witnessing'
  [..] UNSIGNED
        no .claude/commission-7.asc found — legitimate LAZY-mode commission, not a defect (spec §3: UNSIGNED is a weaker claim, never a failure)
```
(exit 0). Writing a FULL-mode commission (`LED_ACTOR=commissioner ./led commission "..."`) and
banking a real signature over it, while this deployment's own `keys/` is still empty, produces:
```
verify-commission: row 8 (actor=commissioner, signing_mode=FULL)
  statement: 'probe commission, FULL mode, for FAQ item 11 witnessing'
  [!!] NO-COMMITTED-KEY -- a signature is banked (commission-8.asc) but /tmp/faq11-scratch/keys carries NO committed public key (AWAITING-KEY) — nothing exists to check the claimed signature against
```
(exit 3). Committing a throwaway key to this deployment's own `keys/` and re-checking the same
row produces:
```
verify-commission: row 8 (actor=commissioner, signing_mode=FULL)
  statement: 'probe commission, FULL mode, for FAQ item 11 witnessing'
  [OK] VERIFIED
        statement sha256=95582fe15d486f11a596427016b65225496cb199dda6542203a103507ba17f83. gpg: Signature made Sat Jul 18 16:20:12 2026 CEST
gpg:                using EDDSA key 10BC2094D89C920FDE920382B0FCF425E8145063
gpg: Good signature from "attest-tags-probe <probe@example.invalid>" [unknown]
gpg: WARNING: This key is not certified with a trusted signature!
gpg:          There is no indication that the signature belongs to the owner.
      10BC2094D89C920FDE920382B0FCF425E8145063
```
(exit 0). Corrupting one byte of the banked `.asc` after signing, then re-checking the same row,
produces:
```
verify-commission: row 8 (actor=commissioner, signing_mode=FULL)
  statement: 'probe commission, FULL mode, for FAQ item 11 witnessing'
  [!!] FORGED-OR-CORRUPT
        statement sha256=95582fe15d486f11a596427016b65225496cb199dda6542203a103507ba17f83. gpg: CRC error; 753034 - 555B53
gpg: no signature found
gpg: the signature could not be verified.
```
(exit 1). The run's own event journal confirms all six determinations across this session
landed (`GPG-UNAVAILABLE` never fired — `gpg` was present throughout):
```
{"ts": "2026-07-18T14:19:56.247Z", "verdict": "UNSIGNED"}
{"ts": "2026-07-18T14:20:04.173Z", "verdict": "UNSIGNED"}
{"ts": "2026-07-18T14:20:12.346Z", "verdict": "NO-COMMITTED-KEY"}
{"ts": "2026-07-18T14:20:17.509Z", "verdict": "VERIFIED"}
{"ts": "2026-07-18T14:20:31.064Z", "verdict": "FORGED-OR-CORRUPT"}
{"ts": "2026-07-18T14:20:36.196Z", "verdict": "VERIFIED"}
```

**Can I record and check whether a document has actually been through the ADR-0017 fresh-context
loop, at its CURRENT bytes, from inside a scaffolded deployment?** Yes — `attest-doc` is the
per-deployment verb answering the maintainer's own question, "is there a reason we can't [use the
fresh-context audit loop] for end users?" (already answered "no" for `USER-DOC-AUDIT-LOOP.md`
in the [Documentation quality](REVIEW-AND-GATING.md#documentation-quality) recipe; this is the verb that question built). `./attest-doc check [PATH...]` classifies every
in-scope `*.md` (default: every one under this deployment, minus scaffold-owned docs — attested
upstream in autoharn itself, not this deployment's to re-attest — and inline-waived ones) as
`ATTESTED` (a fresh-context record exists for this file's EXACT current bytes), `STALE` (a record
exists for this path, but at different bytes — the loop ran once, the file changed since), or
`NO-ATTESTATION` (no record at all); exit 0 iff every in-scope doc is ATTESTED. `./attest-doc
record <json-file>` validates and appends one attestation record — the same schema, same
refusals, as the upstream gate's own `--record` — to THIS deployment's own
`attestations/doc-legibility-attestations.jsonl` (seeded empty at scaffold time), never
autoharn's own ledger of that name.

All three classification states were WITNESSED on a scratch deployment (torn down after).
Checking a freshly scaffolded world's own docs, before any attestation exists, produces:
```sh
$ ./attest-doc check
```
```
attest-doc check: 4 doc(s) in scope, 6 scaffold-owned excluded, 0 waived.
  scaffold-owned (autoharn's own docs, attested upstream -- not yours to re-attest):
    .claude/APPARATUS.md
    .claude/GOVERNED_FILES.md
    .claude/HOOKS.md
    CLAUDE.md
    attestations/README.md
    keys/README.md
  NO-ATTESTATION  .claude/skills/hack-rationalization-detector/PROVENANCE.md
  NO-ATTESTATION  .claude/skills/hack-rationalization-detector/SKILL.md
  NO-ATTESTATION  .claude/skills/hack-rationalization-detector/olds.md
  NO-ATTESTATION  .claude/skills/hack-rationalization-detector/references/known-cases.md
attest-doc check: 0 ATTESTED, 0 STALE, 4 NO-ATTESTATION
```
(exit 1). Recording a throwaway probe document with a well-shaped `doc-attestation/1` JSON body
(`schema`, `doc`, `content_sha256` matching the file's exact bytes, `b_id` — free text naming
which B-round wrote the record — one CLEAN round
enumerating all four Rule-1 clauses, `escalated: false`) produces:
```sh
$ ./attest-doc record /tmp/probe-attestation.json
```
```
doc_attestation_presence --record: appended attestation for probe-doc.md (schema doc-attestation/2, content_sha256 0c5669e635c1..., 1 round(s), escalated=False)
```
(exit 0; the printed schema reads `/2` — the record was accepted and upgraded on write, the
gate's own `doc-attestation/1`-and-`/2` dual-acceptance noted in its module docstring). Checking
that same file again immediately afterward produces:
```
attest-doc check: 1 doc(s) in scope, 0 scaffold-owned excluded, 0 waived.
  ATTESTED        probe-doc.md
attest-doc check: 1 ATTESTED, 0 STALE, 0 NO-ATTESTATION  (0 debt = clean)
```
(exit 0). Appending one more sentence to the same file, so its bytes diverge from what was
attested, then produces:
```
attest-doc check: 1 doc(s) in scope, 0 scaffold-owned excluded, 0 waived.
  STALE           probe-doc.md
attest-doc check: 0 ATTESTED, 1 STALE, 0 NO-ATTESTATION
```
(exit 1) — the classification is purely content-hash-keyed, never path-keyed: the SAME path,
edited, reads STALE, not ATTESTED-for-the-old-content.

**Does this join `distance-to-clean`'s composed debt total?** Yes, opt-in only — the
DOC-ATTESTATION section reads the identical `classify()`/`discover_md()` `attest-doc check`
reads (ADR-0012 P1: one classifier, two callers), but only counts toward TOTAL debt once
`mechanisms.doc_attestation.mode` is `"observe"` in this deployment's `.claude/apparatus.json`
(default `"off"` — a deployment that never adopted the A:B:C loop should see no debt for a
discipline it never opted into; a bad mode value never widens, same convention every mechanism
in this project's apparatus switchboard already follows). Both polarities were WITNESSED on the
same scratch deployment. With the default `"off"`, `distance-to-clean` prints:
```
doc-attestation   : off (opt-in -- set mechanisms.doc_attestation.mode to 'observe' in .claude/apparatus.json once you're running the ADR-0017 A:B:C loop, so debt here reflects a discipline you actually adopted)

TOTAL debt: 0  (0 = clean)
```
Flipping the mode to `observe` (with the STALE probe-doc.md and four scaffold-skill
NO-ATTESTATION docs from above still in place, plus one open+claimed work item added to also
exercise the WORK-ITEMS line in the same pass) then produces:
```sh
$ ./distance-to-clean
```
```
### SECTION: DISTANCE-TO-CLEAN

(reads the SAME views `led review-gap` / `led question-status` / `led work violations` already expose, PLUS the two categories the stop-gate hook (hooks/stop_clean_exit.py) also checks that those three commands don't -- computes nothing new; those three commands remain the disaggregated default, unchanged by this verb)

review-gap        : 0 row(s)
question-status   : 0 open of 0 total
work-violations   : 0 violation(s)
work-items        : 1 open+claimed item(s) [CAVEAT: this tool has no session identity, unlike the stop-gate hook -- it cannot narrow to only THIS session's claims, so it counts every claimed-open item, matching the hook's own DEGRADE fallback for when session ownership can't be proven] -- slugs: ['probe-work']
work-review-gap   : 0 deferred-review item(s)
doc-attestation   : 5 debt (4 NO-ATTESTATION, 1 STALE, 0 ATTESTED) -- ['.claude/skills/hack-rationalization-detector/PROVENANCE.md (NO-ATTESTATION)', '.claude/skills/hack-rationalization-detector/SKILL.md (NO-ATTESTATION)', '.claude/skills/hack-rationalization-detector/olds.md (NO-ATTESTATION)', '.claude/skills/hack-rationalization-detector/references/known-cases.md (NO-ATTESTATION)', 'probe-doc.md (STALE)']

TOTAL debt: 6
```
(exit 1). This is the same composed verb the ["Documentation quality"](REVIEW-AND-GATING.md#documentation-quality) section already
introduces via `USER-DOC-AUDIT-LOOP.md`; this entry is the witnessed transcript that section
points at rather than restates.

**A note on `settings.json.tmpl`.** This is not a verb — it is the hook-wiring template
`bootstrap/new-project.sh` fills in (`__PROJECT_ROOT__`, `__AUTOHARN_ROOT__`, `__DB__`, `__HOST__`,
`__SCHEMA__`) and writes to every scaffolded deployment's own `.claude/settings.json`, the file
Claude Code itself reads at session start to learn which hooks fire on which tool events. Reading
its own source (`bootstrap/templates/settings.json.tmpl`) rather than a description of it: it
wires nine hook attachments across five lifecycle points *[editorial correction, verified against `bootstrap/templates/settings.json.tmpl` at the suite's legibility loop: the template wires FOUR lifecycle points — PreToolUse, PostToolUse, Stop, SessionStart — through ten matcher blocks; "five" as preserved overcounts]* — `PreToolUse` (the change gate, stamp
interception, the SQL-write block, and the doc-shapes gate, matched to `Write`/`Edit`/`Bash`/
`AskUserQuestion`/`Read`/`Task|Agent|Workflow` respectively -- *[editorial, verified against the template at the suite's legibility loop: "respectively" cannot carry the real mapping -- the change gate, stamp interception, and SQL block ride the `*` matcher; the demurral detector `AskUserQuestion`; the mutation observer `Bash`; the delegation observer `Task|Agent|Workflow`; the doc-shapes gate `Write|Edit`; the read observer `Read`]* -- widened from `Task|Agent` by the
Workflow-tool-coverage work item, ledger row 1355; this sentence's own matcher text was stale,
corrected 2026-07-26 doc sweep), `PostToolUse` (the mutation observer twice,
bash completion, the apparatus-flip journal, the delegation observer), a single `Stop` entry
(the stop-gate plus demurral detection), and a `SessionStart` entry scoped to `compact|resume`
(durable-decision replay). Every hook is invoked as `env <VARS> python3
__AUTOHARN_ROOT__/hooks/<script>.py`, so each one reads its own connection/path parameters from
its own named environment variables rather than a shared config object — the same "no shared
mutable config" posture the rest of this project's verb surface follows. This file is the ONE
home of that wiring (ADR-0012 P1): a scaffolded deployment's `.claude/HOOKS.md` documents what
each hook does in prose, but the template above is what actually arms them, and the two are kept
in sync by the scaffold writing both from the same run. UNWITNESSED beyond what a scaffold run
already demonstrates elsewhere in this recipe suite (the `--new-world` scaffold transcript under
["Deployments can self-serve the harness changelog"](SETUP-AND-SCAFFOLD.md#deployments-can-self-serve-the-harness-changelog-orchlog-wrapper-at-scaffold) (in the setup-and-scaffold recipes) shows the scaffold writing this file's
filled-in sibling among its output, but a session-start hook-firing trace was not separately
re-captured for this entry) — the concrete blocker is that observing every one of the nine
attachments actually fire would need a live Claude Code session inside a scaffolded deployment
exercising every matched tool type in turn, which this documentation pass did not run.

(2026-07-27 correction, root-shim-pruning residue sweep, ledger row 1357: the "Verifying tags,
signed commissions, and documentation debt" section above traces to the maintainer's 2026-07-18
overnight batch, and its `verify-commission`/`distance-to-clean` WITNESSED transcripts (scratch
deployment `faq11probe`, real row ids) predate the umbrella-CLI scaffold migration, rows
1365/1366/1367, 2026-07-26, which retired the bare shims those transcripts typed — left as the
dated record they are; the current equivalent invocations are `./autoharn verify-commission` /
`./autoharn distance-to-clean`.)

