# Identity and authority — recipes

<!-- doc-attest-exempt: relocation-class mechanical move (work item faq-refactor-by-concern, ledger row 185 adjudication, 2026-07-28) -- the content below is byte-preserved prose moved verbatim out of user-guide/USER-RECIPES-FAQ.md (commit `178ec789439044bebb664e7374c2be757d064d11`; sections named in the provenance line above), plus mechanical `../` link-depth repairs and named cross-file link/anchor rewrites for content that relocated to a sibling factor file; no other prose was reworded (ADR-0020's clause 1: a residue disposition and a link gate are the mechanical floor, never a substitute for a cold meaning-preservation read -- that read DID run, by a fresh-context Agent invocation distinct from the session that performed the move; see this work item's execution report for the per-file outcome). The ADR-0017 A:B:C legibility loop is a SEPARATE read this session did not run: the coordinator schedules it after merge, per this work item's adjudication conditions (ledger row 185). Waived here only to unblock this commit. Removal condition: strike this marker and run the real ADR-0017 A:B:C loop next time this file is touched for content, not just link repair. -->

*Factored out of [`user-guide/USER-RECIPES-FAQ.md`](../USER-RECIPES-FAQ.md) at commit
`178ec789439044bebb664e7374c2be757d064d11`, sections "Granting and revoking a principal's authority (s40/s41)", "Entitlement
enforcement and work gating (s60)", "Suspending, reviving, and revoking a principal's standing
(s45)", "Work-unit role assignment", and "Role charters and briefs"; byte-preserving (mechanical
`../` depth repairs and named cross-file link rewrites only).*

**Charter:** who may act, on what basis, and what happens when that changes. Belongs:
principals, standing, roles, competences, relations, entitlement, and the work-lifecycle roles
that ride them. Does not belong: review obligations (see REVIEW-AND-GATING.md in this
directory), or the compartmentalization/read-zoning worked examples that
[USER-ACCESS-CONTROL-GUIDE.md](../USER-ACCESS-CONTROL-GUIDE.md) already owns — cross-reference,
never absorb.

---

<!-- doc-attest-exempt: file-scope relocation disclosure, added at the faq-refactor-by-concern split (ledger row 185, 2026-07-28) precisely so the marker further below (scoping only the "Work-unit role assignment" section) is not misread as this file's only exemption, or as not applying to the rest of this file. This file relocates FOUR sections from user-guide/USER-RECIPES-FAQ.md: "Granting and revoking a principal's authority (s40/s41)", "Entitlement enforcement and work gating (s60)", "Suspending, reviving, and revoking a principal's standing (s45)", and "Role charters and briefs" moved byte-preserving (mechanical link-depth/cross-file-link repair only, no prose rewrite) and carry no separate content-freshness marker of their own beyond this one. "Work-unit role assignment" is DIFFERENT -- it is new prose (Fable-authored 2026-07-28) that has never been through any A:B:C loop, and its own marker (immediately above that section's heading) says so. Because gates/doc_attestation_presence.py's `_has_waiver()` check is whole-FILE, not per-section, EITHER marker being present exempts this entire file from the gate; this marker exists so a reader does not mistake the other marker's narrow "this whole Work-unit role assignment section" scope claim for a claim about the other four sections named above, which THIS marker -- not that one -- is what actually covers. Removal condition: strike this marker (independently of the Work-unit-role marker) once a real A:B:C attestation covers the four relocated-verbatim sections named above. -->

## Granting and revoking a principal's authority (s40/s41)

These two entries deviate from this page's usual point-elsewhere convention (full command
sequences with quoted witnessed output, not a one-liner plus a pointer) because the surface is
new and unfamiliar: `principal` went from four flat columns with no history to an event-sourced
identity model (registration, standing, role/key bindings, competence, relationships) in kernel
deltas s40/s41. Delivery record: [orchlog.d/s40-s41-principal-identity.md](../../orchlog.d/s40-s41-principal-identity.md);
full spec: [design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md](../../design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md).

**Prominent caveat, read before typing anything below:** these `led principal ...` verbs exist
only in a world whose [birth chain](../../GLOSSARY.md#birth-chain) carries commit `87f00b4` (s41)
and, for the identity-events half alone, `39480ec` (s40) — runs are strictly linear, so an
already-scaffolded world gains none of this. If you want to try these commands today without
waiting for your next real world, scaffold a disposable one first —
[USER-GUIDE.md](../USER-GUIDE.md) §3b has the `bootstrap/new-project.sh --new-world`
walkthrough — and play there; tear it down when done.

**Does MY world actually have s40/s41?** Run `./autoharn migrate <deployment-dir> --dry-run` from your
autoharn checkout (`<deployment-dir>` is the path to your scaffolded world). Per its own
documented behavior ([README.md §4](../../README.md#4-bring-a-deployments-database-up-to-date-with-a-newer-kernel)):
it prints the resolved db/host/schema, then reports which deltas — by name — your world's
database is missing, by running each birth-chain entry's own `.detect.sql` check against your
live schema and stopping at the first one that reads false; nothing is applied under
`--dry-run`. Read straight from the verb's own source
(`bootstrap/migrate_core.py`): the two shapes you will actually see are `migrate: current
lineage head = <name>` followed by `migrate: '<deployment-name>' is already at the lineage
head. Nothing to migrate.` if s41 (or later) is already applied, or `migrate: missing (<n>):
s40-principal-identity-events, s41-principal-bindings-and-relations[, ...]` naming exactly
what your world lacks. There is no lighter-weight check than this — `distance-to-clean` does
not report lineage position — so this is the one command to run.

**How do I set up the principals in a new world?**
You mostly don't have to — a world born on this commit or later starts with a WORKING set of
principals, not an empty registry. Here is exactly what the scaffold already did for you, and
what to type for anything beyond that.

*What birth already gave you.* The scaffold's birth sequence, run once at `--new-world` time,
is three explicit, attributed acts, in order: (1) the connection principal `author` is
registered through the full s40 ceremony (self-attributed — the one genesis exception, since
nothing else exists yet to attribute it to) and its `principal_registered` event lands; (2) a
`principal_standing_declared` event binds the world's database role to `author` — this is the
"declared, not silent" default: it is why your very first `./led` write, with no
[`LED_ACTOR`](../../GLOSSARY.md#principal) (the environment variable that names which registered
principal a `led` write is attributed to) set, just works; (3) `reviewer` and `commissioner`
are registered the same way, each with a stated purpose. Witnessed on a real `--new-world` scaffold run
(`seen-red/s40-principal-identity-events/red.txt`, case `new-world-birth-sequence`): *"scaffold
exit=0; registration events=3 (author, reviewer, commissioner), standing declarations=1; first
no-LED_ACTOR write exit=0, attributed 'author|declared-default'"*. If all you need is the
baseline three principals a solo operator's world already assumes, you are done — no further
setup required.

*Registering an additional principal.* `--purpose` is mandatory on an s40+ kernel; omit it and
you are refused, not silently ignored. The refusal below cites "AC-2," NIST 800-53's
Account Management control (the standard the registration ceremony's mandatory-purpose
requirement is grounded in — quoted verbatim below, not paraphrased). Witnessed
(`seen-red/s40-principal-identity-events/red.txt`, case `purpose-mandatory`, and the exact
refusal text from `bootstrap/templates/led.tmpl`'s own source):

```sh
$ ./autoharn led register-principal nopurpose model
```
```
led register-principal: REFUSED -- --purpose is mandatory on an s40 kernel: a
  registration is a recorded, attributed event with a stated purpose (AC-2's
  'account with a stated purpose'; kernel/lineage/s40-principal-identity-events.sql).
usage: led register-principal <name> <human|model|subagent|tool> --purpose "<why this identity exists>"
```
(exit 1). Supply `--purpose` and it constructs:
```sh
$ ./autoharn led register-principal reviewer2 model --purpose "second-tier model reviewer"
```
Re-registering the same name is never a silent no-op — both class polarities refuse loudly
(`seen-red/s40-principal-identity-events/red.txt`, cases `register-duplicate-same-class` and
`register-duplicate-class-mismatch`). Same class, same name again:
```
led register-principal: REFUSED -- principal 'reviewer2' is already registered
  (id <id>, class model, purpose: <purpose>). Re-registration is never a silent no-op
  (s40 §3.7 -- the panel's silent ON CONFLICT DO NOTHING class, closed): if you meant
  this existing principal, just use it (LED_ACTOR=reviewer2); if you meant a NEW
  identity, pick a new name.
```
A different class under the same name refuses too, naming the mismatch and pointing at
`./led principal relate <new> succeeds <old>` (once s41 has landed) as the way to record a
genuine identity succession rather than a rename — names are immutable by rule, and a class
change is a new identity, never an edit to the old one.

*Declaring standing.* This binds a database role's default attribution to a registered
principal — the same declared-not-silent act the scaffold performed for `author`. `--db-role` is optional
and defaults to your own world's connection role (read directly from `bootstrap/templates/led.tmpl`'s
source: `db_role="$ROLE"` unless overridden) — the same `role` value your deployment's own
`deployment.json` already carries (README.md's configuration table names this field; run `cat
<world-dir>/deployment.json` and look at `"role"` if you've forgotten it). For the common case
— rotating which principal your world's OWN connection role speaks for — you never need to
pass `--db-role` at all:
```sh
$ ./autoharn led principal declare-standing reviewer2
```
Only pass `--db-role <name>` explicitly when declaring standing for a DIFFERENT Postgres role
than the one your `deployment.json` already names — e.g. a second writer role your world's
kernel DDL granted separately (`\du` in `psql` lists every role that exists on the database if
you need to find one by hand). Re-declaring for the same role auto-supersedes the prior
declaration (this is how you rotate which principal a role speaks for).

*Binding a role.* Role text is free, non-empty, organizational text, not a closed vocabulary
(ratified §9(c) — role naming is organizational configuration, not the harness's to impose):
```sh
$ ./autoharn led principal bind-role reviewer2 --role "sql-review"
```

*Granting competence* — the [safety-critical-logging BRIEF](../../law/briefs/safety-critical-logging/BRIEF.md)'s
**G13 record** (that document's required-work-product entry for "who is believed competent for
what safety activity, at what band, on what basis" — a competence assignment or its change),
recordable but NOT gating (nothing in v1 refuses an act for lack of a matching grant):
```sh
$ ./autoharn led principal grant-competence reviewer2 --activity "sql-review" --band "B" --basis "track record on s37-s39"
```
Witnessed lifecycle (`seen-red/s41-principal-bindings-and-relations/red.txt`, case
`competence-lifecycle`): *"grant OK (view: 'sql-review|B'); duplicate refused; empty band
refused (1); re-band via --supersedes replaced (band now 'A'); stray --band on withdrawal
refused; STALE supersession target refused; withdrawal OK (view 0 rows, raw 3 rows -- grant+
re-band+terminal withdrawal); raw inactive-from-birth refused by the kernel CHECK"*. The band
and basis fields are free text — the spec's own ratification (§9(g)) calls this a **placeholder
architecture only, not a considered final design**; do not read the free-text shape as a
settled judgment that a closed band vocabulary (ASIL/SIL/DAL-style) is never coming.

*Relating two principals* — the closed vocabulary is `acts-for`, `dispatched-by`,
`same-natural-person`, `succeeds`:
```sh
$ ./autoharn led principal relate reviewer2 acts-for reviewer3
```
Self-edges refuse at the kernel, both via the CLI and via a raw direct write
(`seen-red/s41-principal-bindings-and-relations/red.txt`, case `self-edges-refused`: *"all
four CLI self-edges refused=True; raw kernel-trigger self-edge exit=3 with the taught
text"*). `same-natural-person` is symmetric and canonicalized (stored lower-`id`-first
regardless of the order you type it), witnessed both orderings in case `snp-canonicalization`.

*Looking at what exists.* No dedicated `led principal list`/`show` verb ships in v1 — this is a
genuine gap, not a hidden feature (UNEXERCISED beyond the derived views themselves). The
sanctioned way to look today is the same "query the view directly" pattern the CLI already uses
internally for its own convenience reads (e.g. `led standing`'s own implementation is a plain
`SELECT * FROM standing_decisions`, per `bootstrap/templates/led.tmpl`): the human-readable
surface is the `principal_standing_current` view (name, class, standing, registered_at,
registrar, purpose — one row per principal); the binding surfaces are `principal_relations`,
`principal_role_bindings` (deliberately not `principal_roles` — that name is reserved for the
unrelated db-role↔principal binding view, `principal_role`), `principal_keys`, and
`principal_competences`. All four binding views show only currently-active, unsuperseded rows;
every retraction stays visible in the raw ledger history regardless.

*Suspending or revoking a principal, and the honest limit on getting back.*
```sh
$ ./autoharn led principal suspend reviewer2 "on leave"
$ ./autoharn led principal revoke reviewer2 "compromised"
```
Writes under a suspended-or-revoked principal then refuse at the kernel (witnessed,
`seen-red/s40-principal-identity-events/red.txt`, case `revoke-refuses-writes /
successor-passes`: revoked write exit=3, successor registration exit=0, successor write
exit=0). **No v1 verb lifts a suspension or a revocation, for either kind, and if both are
ever written for the same principal, `revoked` always wins the reported standing regardless of
which order they landed in** (case `precedence-both-orders`: *"suspend-then-revoke reads
'revoked', revoke-then-suspend reads 'revoked'"*). The only way back to an active identity is
registering a fresh successor principal and recording the succession:
```sh
$ ./autoharn led register-principal reviewer2-successor model --purpose "reviewer2's replacement identity"
$ ./autoharn led principal relate reviewer2-successor succeeds reviewer2
```
This is a new identity, not a reinstated old one — a real, if heavier, escape hatch, disclosed
as a deliberate v1 limit rather than an oversight.

**Can I use GPG to sign roles / authenticate myself as a principal?**
Answering exactly what was asked, in three honest parts — this is not a recommendation to go
generate a key; the standing deferral on key generation ("key generation/signing deferred until
all else banked; never re-raise as recommendation") is the maintainer's own ruling to lift, not
this page's to nudge him toward.

*(1) What exists now.* `led principal bind-key <name> --fingerprint "<fp>"` records an OpenPGP
v4 fingerprint against a HUMAN principal — a typed, dated, countersignable ledger row (a
`principal_key_bound` event), refused outright on any non-human subject
(`seen-red/s41-principal-bindings-and-relations/red.txt`, case `key-binding-polarity`: *"model
bind exit=3 (taught); human bind exit=0, view rows=1; malformed fingerprint exit=3 (kernel shape
CHECK named)"*). That is the whole of what's built: an empty-until-ceremony slot. **Nothing
anywhere verifies a signature against it.** "Signing a role," as a cryptographically verified
act, does not exist in v1 — a role binding (`led principal bind-role`) is an attributed,
countersignable ledger row, exactly like every other kind this project records; it is never a
signed object, and `bind-key` does not change that for any other kind.

*(2) What actually exercising this for real would require.* No maintainer keypair exists
anywhere in this project today —
[law/keys/README.md](../../law/keys/README.md) states its directory's state plainly:
`AWAITING-KEY`, "no real maintainer keypair has been generated as of this writing." Rung 1 (the
signed-tag mechanism this directory backs) is built; it has never been armed. Exercising
`bind-key` for real, rather than against a throwaway test key, needs the one-time key generation
the maintainer's own standing ruling has deferred. If he chooses to lift that deferral, the
recipe is [design/MAINT-GPG-TRUST-LAYER.md](../../design/MAINT-GPG-TRUST-LAYER.md) §7 (`gpg
--full-generate-key`, hardware-backed preferred so each signature costs a physical touch), then
`led principal bind-key <name> --fingerprint "<the generated fingerprint>"`. The ceremony shape
that DOES already exist today, on top of that binding, is an ordinary countersign — a review row
regarding the binding event, using the same verb every other ledger row is countersigned with:
```sh
$ ./autoharn led review <bind-key-row-id> attest technical "fingerprint verified against a witnessed key-signing party"
```
(`led review`'s independence argument requires a stamp-distinct invocation — one whose HMAC
stamp (the session-identifying tripwire described just below) differs from the row being
reviewed's own — for anything above `self-review`; see the verb's own usage text in
`bootstrap/templates/led.tmpl`.) A key-binding
proposal followed by a countersign on that same binding row therefore needs zero new review
machinery to close the loop — the binding event is just another countersignable ledger row, like
any other.

*(3) The honest limit.* Binding a fingerprint records custody of a key against an identity — it
does not authenticate sessions, and it does not make `bind-key` a login mechanism. The HMAC
stamp (`kernel/lineage/s17-stamp-mechanism.sql`) remains the tripwire that answers "which live
invocation wrote this row"; the key slot answers a different, narrower question ("who does this
fingerprint belong to"), and answers it only once someone actually signs something and a
verifier checks that signature — which nothing in this project does yet for a role or a
principal binding. Signature-*verified* acts are a future rung, not this one.

## Entitlement enforcement and work gating (s60): who may act, and when a claim may start

**Prominent caveat, matching the s40/s41 entry above:** these mechanisms exist only in a world
whose birth chain carries `kernel/lineage/s60-entitlement-enforcement.sql` (and, for work gating
proper, `s39-blocks-start.sql`, already carried by every current birth chain). At the time this
recipe was written `s60` is authored and scratch-witnessed
(`seen-red/s60-entitlement-enforcement/red.txt`) but not yet wired into
`bootstrap/new-project.sh`'s `LINEAGE_CHAIN` — check with `./autoharn migrate <deployment-dir>
--dry-run` (see the s40/s41 entry above for exactly how to read its output) before assuming a
given world has it.

### What entitlement enforcement adds

Before s60, s41 could *record* that a principal held a role, or that one principal acted for
another — but nothing *checked* either fact at write time. Any active principal could register a
new principal, bind a role, suspend/revoke someone, or supersede a milestone's closure or a
gate edge. s60 closes exactly that gap with a **factored acceptance predicate**, evaluated inside
the same write boundary every other kernel refusal already goes through (s43) — no second
refusal surface, no new CLI ceremony beyond the existing `led principal` verbs:

- **Conjunct (a) — role binding.** For an act class this world's configuration names (a small,
  deployment-policy map — see below), the actor must hold an in-force `principal_role_bound`
  binding naming the configured role. An act class nobody has configured is not gated by this
  conjunct at all (vacuously satisfied).
- **Conjunct (b) — authority chain to genesis.** For the *authority-bearing* act set —
  registering a principal, binding a role, the standing lifecycle (declare/suspend/revoke),
  closing or superseding a **milestone's** closure (a work item something else's claim
  `blocks-start`-depends on), and superseding a `blocks-start` gate edge — the actor's authority
  must trace, through zero or more `acts-for` relations, back to the world's genesis principal
  (the very first principal ever registered — normally `author`). This conjunct applies whether
  or not conjunct (a) is even configured for that class; it is what actually forecloses "any
  active principal may register a new principal."

Both conjuncts are evaluated **fresh, every time** — nothing is cached, and nothing about a
principal's *past* accepted acts changes when their standing later changes. If a delegate in the
middle of a chain is suspended, every chain that ran *through* them stops working for *future*
acts; nothing they already wrote is retroactively touched (the same "chain death is prospective,
credited acts stay credited" asymmetry `s45`'s standing lifecycle already establishes one layer
down).

**The birth-sequence default.** A newly-scaffolded solo world discharges this for you: `author`
(this world's genesis principal) is bound to role `authority`, and the five default act classes
above are each configured to require that same role — so a solo operator's *own* acts are
unaffected (author already holds the role, and trivially reaches genesis by being genesis).
Nothing changes for an ordinary `./led decision "..."` or `./led work open ...` — entitlement
gates only the six act classes named above, never anything else.

### Worked example: a delegate with no chain gets refused, a suspended link severs it prospectively

Witnessed live against a real scratch database (`seen-red/s60-entitlement-enforcement/red.txt`,
full transcript; every verdict below is quoted verbatim from that run, not paraphrased). Three
principals: `author` (genesis, role `authority`), `D1` (`acts-for author`, role `authority`),
`D2` (`acts-for D1`, role `authority`) — so D2's authority derives transitively through D1.

D2 performs an authority-bearing act (registering a fourth principal) while the chain is intact —
**accepted**:
```
verdict={'row_id': 24, 'message': None, 'sqlstate': None, 'refusal_id': None,
         'disposition': 'accepted'}
```
`author` then suspends D1 (an authority-bearing act itself, which `author` may do trivially —
being genesis). D2's chain to genesis now runs through a suspended principal. D2 attempts a
*second* registration — **refused**, conjunct (b), even though D2's own standing was never
touched:
```
Ledger policy: entitlement refused (s60, factored acceptance predicate conjunct b) — act
class 'principal_registered' is authority-bearing ...; actor 8's authority chain
(transitive reachability over in-force acts-for relations, kernel/lineage/
s41-principal-bindings-and-relations.sql) does not reach this world's genesis principal.
Remedy: an in-force acts-for relation ... or have a severed link repaired (suspension/
revocation severs a chain PROSPECTIVELY only; past accepted acts through that link stay
credited, kernel/lineage/s45-standing-lifecycle.sql's I5 asymmetry).
```
D2's *first* act (row 24) is unaffected — still present in `ledger_current` after the chain
severed (the credited-views witness of the I5 asymmetry, not merely asserted):
```
=== RED-3-I5-past-act-credited ===
  [ok] D2's FIRST act (row 24), written before D1's suspension, is still present in
       ledger_current after the chain severed -- count=1
```
The remedy in every refusal's own text: `./led principal relate <name> acts-for <delegator>` to
extend or repair a chain, `./led principal bind-role <name> "<role>"` to satisfy conjunct (a).

### Work gating: milestone dependencies as an authority-checked switch (s39, over s60)

Zero new kernel surface here — the mechanism is `s39`'s `blocks-start` edge type, already built;
what s60 adds is that **flipping the switch is now an authority-checked act** (closing or
re-editing the gated milestone), closing the loophole where anyone could quietly unbolt a gate.
The construction, worked end to end (verbs and refusal text from `s39-blocks-start.sql` and
`led.tmpl`'s own source — read-from-DDL where not independently re-witnessed in this pass):

```sh
./autoharn led work open v2-release   --title "v2.0.0 ships"        # the milestone
./autoharn led work open spa-polish   --title "SPA polish pass"
./autoharn led work depends spa-polish v2-release --type blocks-start   # judgment, spent once

./autoharn led work claim spa-polish
  → REFUSED (write_refused row journaled, s43):
    "Ledger policy: claim of work item 'spa-polish' refused — its blocks-start
     antecedent(s) are not yet resolved: v2-release (item is not yet closed).
     Claim and finish each named antecedent first (./led work claim <antecedent>,
     then ./led work close <antecedent> <resolution> ...), or -- if the dependency
     itself is wrong -- correct the record (see the 'Correcting the record'
     recipe, THE-RECORD.md in this recipe suite) ..."

# ... months later, v2 ships. The flip, at whichever grade the act warrants:
./autoharn led work claim v2-release
./autoharn led work close v2-release shipped --witness "tag v2.0.0"
#   under s60: v2-release carries an INBOUND blocks-start edge (spa-polish depends on
#   it), so its close is entitlement-gated -- accepted only from an actor whose
#   in-force role binding covers milestone closure (conjunct a) and whose authority
#   chain reaches genesis (conjunct b); optionally commissioned SIGNED for
#   non-repudiation (a future rung, not yet built -- see the note below).

./autoharn led work startable         # spa-polish now listed (work_startable, s39 Element 5)
./autoharn led work claim spa-polish  # accepted; work proceeds
```

**What counts as a "milestone" for entitlement purposes.** Only a work item that itself carries
at least one in-force *inbound* `blocks-start` edge (something else depends on its closure) is
entitlement-gated on close — an ordinary work item's close is never gated (a deliberate, narrower
reading, marked provisional in `s60`'s own header: attention point 2). Wrong-gate repair stays
first-class: superseding the mistaken `work_depends_on` row (and re-issuing a corrected one) is
itself entitlement-gated as "gate-edge supersession" — the same authority check that protects the
milestone's own close also protects the edge that makes it a milestone at all.

**Composition with discharge probes (postponed, named for completeness).** A probe (registry
code, read-only, best-effort) may *recommend* the flip; the milestone act *is* the flip; the s39
edge *enforces* it. Probes never gate directly — a gate that probed would hang a fail-safe
refusal on a best-effort observation, and a probe that gated would violate its own best-effort
posture. This composition is unchanged by s60; only who may perform the flip is new.

**What this recipe does not cover.** Reconfiguring the default act-class map (which role each of
the five classes requires), and the human-grade SIGNED-commission symmetry for supersession of a
signed act, are both named follow-ons (`design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md` §2, a
*separate* delta from `s60` — not built by this pass). Reconfiguration today is a direct
`entitlement_class_configured` write through the boundary (`kernel/lineage/
s60-entitlement-enforcement.sql` Element 1/4) — no dedicated `led` verb exists for it yet.

## Suspending, reviving, and revoking a principal's standing (s45)

Like the two sections above, this one deviates from the page's usual point-elsewhere
convention because the surface is new: kernel delta s45 gives two governance states — a
db_role's standing declaration, and a principal's suspension — a sanctioned way OUT, where
before s40/s41 there was only a way in. Delivery record:
[orchlog.d/s45-standing-lifecycle.md](../../orchlog.d/s45-standing-lifecycle.md); full spec:
[design/FABLE-STANDING-LIFECYCLE-SPEC.md](../../design/FABLE-STANDING-LIFECYCLE-SPEC.md).

**Prominent caveat, read before typing anything below:** none of this exists in a world whose
[birth chain](../../GLOSSARY.md#birth-chain) predates commit `94f5b7a` — runs are strictly linear,
so an already-scaffolded world gains nothing here. Run `./autoharn migrate <deployment-dir> --dry-run`
to see whether your world has s45; if it names it as missing, the two verbs below are
unavailable until your next real world is born on a checkout that carries this commit.

**What does "unbind" mean, and what do I type?** A db_role's standing declaration (the
"anonymous writes on this connection count as principal X" default that
`./led principal declare-standing` sets) can be repointed to a different principal any number
of times, but before s45 it could never be turned OFF — the only escapes were suspending the
bound principal (which blocks that identity on every channel, not just this role) or pointing
the role at a fabricated tombstone principal (a real misattribution risk). s45 adds a
sanctioned third way:

```sh
$ ./autoharn led principal undeclare-standing
```

(`--db-role <role>` is only needed if you are unbinding a role other than your own
deployment's connection role — the common case needs no flag.) After this, an anonymous write
on that role (no `LED_ACTOR` set) refuses again, exactly as it would on a role that was never
declared for — a fresh `./led principal declare-standing <name>` re-binds it. **This is
forward-only**: rows already written under the old declaration keep their old attribution
forever. If the reason for unbinding is that past rows were misattributed, that is a job for
the defeat pipeline below (a mismatch attestation, not a retroactive rewrite) — nothing in
s45 touches history.

**What does "suspension is liftable" mean, and what do I type?** Before s45, `./led principal
suspend` had no reverse — suspension degenerated into a soft, permanent revocation in
practice, even though the vocabulary implied it was temporary. s45 makes it genuinely
reversible:

```sh
$ ./autoharn led principal suspend reviewer2 "on leave"
$ ./autoharn led principal lift-suspension reviewer2
```

Once lifted, `reviewer2`'s writes are accepted again. **Revocation stays terminal by type —
this is the other half of the same delta: it was always a disclosed design limit, and it is
now enforced by the kernel itself, not merely unbuilt.** There is no verb, in this or any prior version, that reverses a
revocation: a lift-shaped revocation row is structurally unrepresentable (the same
`principal_binding_active` flag that suspension uses is refused outright on the revoked kind),
and a kernel-level supersession rule refuses any attempt to hide a revocation behind an
unrelated superseding row. `lift-suspension` on a principal that is both suspended and revoked
still writes the lift (and warns that standing stays `revoked`, because revocation dominates
suspension in the reported standing) — it changes nothing about the revocation. The only way
back from a revocation remains what s40/s41 already gave you: register a fresh successor
principal and record `./led principal relate <new> succeeds <old>`.

**Does lifting a suspension restore credit for what the principal wrote while suspended?**
No, and this is worth internalizing before it looks like a bug: standing (suspended, revoked,
active) never conditions defeat. Suspending or revoking a principal gates its *future* writes
only; it never withdraws or discounts anything that principal already wrote, and lifting a
suspension changes nothing about which of its past rows are credited. The only sanctioned
lever over whether a specific row is credited is a mismatch attestation under the defeat
pipeline, covered in the next section. This was a maintainer ruling (ledger row 1481,
2026-07-18), named here because a future reader who notices a suspended principal's old work
still counting is looking at the design, not a defect.

**EXISTING WORLDS GAIN NOTHING HERE, restated because it matters most.** Both mechanisms above
are authored, scratch-witnessed, and wired into the scaffold's lineage chain only — they reach
reality solely at a *future* world's birth. If your world predates `94f5b7a`, `undeclare-standing`
and `lift-suspension` are not verbs your `led` script has; `./autoharn migrate --dry-run` will name
`s45-standing-lifecycle` among the missing deltas.

**Honest limits.** A schema owner/superuser can bypass every trigger this delta adds, the
standing disclosed bound every kernel delta carries. The duplicate-active suspension guard is
CLI-side, so a direct (non-CLI) writer can still stack multiple suspensions on one principal,
each then needing its own lift. And in a solo world whose only active principal is suspended,
lifting that suspension needs a *second* active principal to write it — s45 narrows this
dead-end from "impossible" to "needs one more registered principal," but does not close it; a
truly solo, fully-suspended world still needs a schema-owner act to recover.

<!-- doc-attest-exempt: this whole "Work-unit role assignment" section is new prose,
Fable-authored 2026-07-28 under work item work-role-doctrine-faq (autoharn3 row 170,
maintainer-commissioned row 168c: current practice "hap-hazard", taxonomy possibly too
coarse, careful treatment wanted). Every empirical claim cites the filed census
design/WORK-ROLE-PRACTICE-EVIDENCE-2026-07-28.md rather than recall. A second-Fable
ADR-0018 consult reviewed this section same-day with web prior art
(design/CONSULT-WORK-ROLE-DOCTRINE-2026-07-28.md, incl. its disclosed deviation) and
its corrections are applied below; that is a consult, not an A:B:C legibility loop,
and this marker claims only what ran. RATIFIED 2026-07-28 (autoharn3 row 201, the
maintainer's disposition verbatim there): the SHOULD-clauses below now bind as
convention, and the three candidate deltas are ratified as s69
(design/FABLE-S69-ROLE-COHERENCE-REFUSALS-SPEC.md, build in flight) — with his
imperfect-agents proviso woven into the section text where it bears. Removal
condition: strike when a real A:B:C attestation covers this section. -->

## Work-unit role assignment: who opens, claims, closes, and reviews

What this section rests on: a read-only census of every work-item lifecycle act across
three real worlds ([design/WORK-ROLE-PRACTICE-EVIDENCE-2026-07-28.md](../../design/WORK-ROLE-PRACTICE-EVIDENCE-2026-07-28.md)
— read it before disputing a number here). Its headline: in all three worlds, 100% of
opens, claims, and closes were performed by one principal (`author`) in one session
(`main`), with zero exceptions; every separation-of-roles fact in the record lives on
the *review* surface, not the work lifecycle. So the questions below are not answered
from what we do — what we do is uniform to the point of vacuity — but from what the
mechanism enforces, what real organizations converge on, and where those two disagree.
The organizational frame used throughout (initiator / owner / performer / verifier /
approver, the change-control and CAPA roles of regulated-industry practice) is a
reference frame in this page's usual sense, never an adopted requirement.

**Who opens a work item — and does opening obligate the opener to anything?**
Anyone who *sees* the need opens; opening is the initiator's act and carries no
ownership. This mirrors the convergent real-organization rule — anyone may raise a
change request or file a CAPA; triage, not the filer, decides who owns it — and it is
also what the kernel enforces, which is nothing: no trigger ties any later lifecycle
act to the opener's identity (evidence §4). An orchestrator opening items on sighting
is therefore correct practice, not sloppiness — the census's 41-of-102 opened-never-
claimed items in autoharn2 are a visible backlog, not a defect, *provided* each open
item carries its visible current rationale (the standing rule from the 2026-07-23
directive: executable-now, blocked-on-named-thing, awaiting-maintainer, or closed with
reason — an item sitting open with no stated why is itself a defect). The opener's one
gated obligation is that rationale, written into the opening statement. A second
obligation is convention, not gate (added on the 2026-07-28 consult's finding): an
item intended to be claimed carries a definition-of-done a zero-context closer could
adjudicate against (ADR-0017 applied to item text), and its dependencies as typed
edges (`blocks-start`/`blocks-close`) rather than prose — the close-attestation and
regards-the-successor rules below have nothing to bite on without it. Change-control
practice puts acceptance criteria in the change request, not in the closer's head.

**Must the principal that opened the item also close it?** No — and forcing that would
invert the real accountability. Closure is the *owner's* attestation that the work is
done as the resolution says; the initiator is often the least-placed identity to make
that claim (the reporter of a defect is rarely its fixer). Accountability rides the
CLAIM, not the open: the claimant is the owner of record, and the closer should be the
claimant of record at close time. Note the tense of "should": today that is convention,
not mechanism — the CLI enforces claim-before-close (led-side only; the kernel checks
merely that the item was *opened*), and nothing anywhere checks that the closer IS the
claimant (evidence §4, from the live trigger bodies). A close by a different principal
than the claimant is representable and silent. Until that changes, treat closer ≠
claimant as a handoff that must be made visible: the incoming owner claims first
(multiple claims are legal by design; `work_item_current` resolves last-claim-wins),
then closes as themselves. That claim-over-a-live-claim by a distinct actor IS the
handoff's entire record — no new ledger kind is needed (the 2026-07-28 consult
demoted its own instinct for one on the named-consumer test), but the same shape is
also what a claim-steal would look like, so the role-census view below is what makes
the two distinguishable by inspection. A silent cross-identity close is exactly the
"haphazard" shape this section exists to retire.

**Who claims — the orchestrator, or the agent actually doing the work?** The identity
that will *perform* claims. Here is where the census says our practice, not our
schema, is too coarse: the principal registry already carries the finer identities
(`author`, `reviewer`, subagent-class delegates, and the repo's own `autoharn
dispatch` verb — [design/FABLE-DISPATCH-MECHANICS-SPEC.md](../../design/FABLE-DISPATCH-MECHANICS-SPEC.md); s64 supplies the kernel
side, the delegation-condition columns and the scoped chain walk, while the mint verb
itself is repo-local and not yet scaffolded into fresh worlds), yet every claim ever
recorded was `author`'s. When a commissioned builder executes, the honest record is a
claim by the minted delegate (or at minimum an opening/claiming statement naming the
dispatch), so that "who actually did this" is a query, not an archaeology exercise
over commission briefs. The orchestrator claims in its own name only work it performs
itself. This costs one `dispatch mint` per commission and buys the attribution the
whole principal layer was built to record.

**Under a review/fix gate: who reviews, who fixes, who re-closes, who re-reviews?**
Four rules, each with its specimen or refusal already in the record:

1. **The performer never verifies their own work under an independence claim above
   `self-review`.** This one IS mechanism, not convention: claiming `technical` or
   above from the same (stamp_session, stamp_agent) that wrote the reviewed row is
   refused by the kernel with a teaching text (evidence §2's row-339 specimen; s21/
   s41). `self-review` itself is legal and honest — the record's 31-of-31 self-review
   rate is a disclosed single-operator reality, not a scandal — but it is *graded*:
   `discharge_grade` is kernel-computed from stamp identity and cannot be asserted
   upward. Render unto the vocabulary what the vocabulary can prove.
2. **A `refuse` verdict reopens the substance, and the fix lands as a superseding
   close by the owner** — not an edit of the refused close, not a quiet re-review of
   the old row. The panel-board-view thread (evidence §2: refused close 413 → fix →
   superseding close 427) is the worked positive specimen.
3. **The re-review regards the SUCCESSOR close row, never the superseded one.** The
   same thread's mis-citation (review 431 citing dead row 413, self-caught and
   re-filed as 435) is the worked negative specimen — and note it was caught by the
   author's own stop-gate discipline, not by any mechanism; the s48 witness-existence
   trigger checks that a cited row exists, not that it is the right row or even
   review-shaped (evidence §3 specimen 1 is a witness-ref pointing at a
   `work_claimed` row, accepted silently). This rule is the third candidate delta,
   not merely convention (the 2026-07-28 consult's finding — the section's own worked
   negative specimen was the one failure it declined to mechanize): refuse a `review`
   whose `regards` row has an unsuperseded successor, teaching "cite the successor."
4. **The refusing reviewer is the preferred re-reviewer.** The verifier who rejected
   is the one who knows what the rejection meant — the same reason regulated practice
   routes a CAPA's verification back to the QA identity that raised the
   nonconformance. Where that identity is genuinely unavailable, a fresh reviewer
   reads the refusal first; what is not acceptable is the fix's own author attesting
   the fix under a claimed independence (rule 1 already refuses the mechanized part
   of that; the rest is this convention).

**So is the taxonomy too coarse, or the practice?** The evidence says: the practice.
The five organizational roles map onto existing vocabulary with nothing missing —
initiator = opener; owner = claimant of record; performer = claimant or its minted
delegate; verifier = reviewer with kernel-graded independence; approver = the strict
close / s60 entitlement conjunct, where armed. What the census actually exposed is
three narrower gaps, two mechanical and one habitual: (a) closer-is-claimant is
enforced nowhere; (b) the s48 witness-ref check verifies existence but not shape, so
a claim row can silently stand as a "review witness"; (c) `review_detail` — the only
place independence and grade are recorded — has zero adoption outside experience4.
(a) and (b) are fail-safe kernel deltas, joined by (d) review-regards-in-force
(fix-gate rule 3's mechanization, added on the 2026-07-28 consult's finding) — all
three only ADD refusals, and all three were RATIFIED 2026-07-28 as one delta, s69
(maintainer disposition, autoharn3 row 201;
[design/FABLE-S69-ROLE-COHERENCE-REFUSALS-SPEC.md](../../design/FABLE-S69-ROLE-COHERENCE-REFUSALS-SPEC.md) is the governing spec). His
ratification carried a proviso that binds the shape and this doctrine alike, his
words: a higher authority "can be capable of judging another actor inept … so a
claim must be able to be defeated and reclaimed" — autoharn must handle imperfect
agents. Consequence, stated here as doctrine: NOTHING in this section freezes a role
assignment — a claim is defeated by a later claim (the reclaim path), an open item
is superseded or overturned through ordinary append-only supersession, and s69's
closer refusal binds to the LATEST in-force claimant precisely so the reclaim path
composes with it. Delta (b) ships ONLY in the per-close-shape enumeration the planning
subsection below states; its flat "review/finding only" form would refuse honest
planning closes and must not ship. (c) is not a delta at all: it is this section,
applied — and the role-census view that serves it has its consumers named:
`./pickup`-time hydration ("who owns what right now") and post-hoc RCA ("who was
accountable when this shipped"); a view "for visibility" alone would fail the
named-consumer test this project applies to its own proposals first.

**Planning, restructuring, and decomposition — the doctrine one level up** (added
2026-07-28, consult-reviewed). A decomposition is itself authored content: the child
items, edges, and acceptance criteria a planner writes can be wrong the way code can,
so every rule above recurses onto it. The planner never countersigns their own
decomposition above `self-review` (the stamp-distinctness refusal already covers the
mechanized part); the reviewer who countersigned the original plan is the preferred
reviewer of its restructuring; and plan-before-build is already mechanizable today as
the two-gate composition documented under "Review discipline" (`blocks-start` edges
plus `decomposition_review`). Three specifics:

1. **Composite parents: the shape-owner claims at decomposition time.** A composite
   parent is often never *performed*, only structured — so "accountability rides the
   claim" reads as: the decomposer claims the parent when decomposing, and the claim
   records "I own this tree's shape," not "I will perform it." Its eventual close is
   then ordinary under the closer-is-claimant rule — no trigger carve-out needed,
   and deliberately none proposed: a bookkeeping exemption in the refusal itself
   would reopen the hole the delta closes.
2. **Self-re-scoping is self-review in disguise.** The live hazard of restructuring
   is the performer narrowing an item's scope at close time until "done" becomes
   reachable — the closure-statement failure ADR-0000's 2026-07-02 amendment names
   ("the class gets named at exactly the scope of the fix already built"), operating
   at work-item grain. Doctrine: a superseding open or cascade that moves a claimed
   item's finish line gets the same verification posture as a close, and never
   solely by the identity whose finish line it moves. Convention-plus-visibility
   today, stated honestly per ADR-0011 Rule 1: a refusal would need a decidable
   discriminator between self-serving narrowing and legitimate coordinator
   restructuring, and none exists yet.
3. **A planning item's witness is its decomposition — stated decidably.** For `row:`
   witness citations, the legal shapes are `review`/`finding` rows generally, PLUS
   `work_opened` rows of children where the closing slug has in-force parent edges
   to them; `bookkeeping` closes cite `commit:<sha>`, which the s48 `row:` check
   never touches, so they are unaffected by construction. (The earlier "per
   resolution kind" phrasing was not decidable — `work_resolution` has no "planning"
   member — and was corrected by the consult before anyone built it.)

## Role charters and briefs (`tools/role_charter.py`, `tools/role_brief.py`)

**What are a "charter" and a "brief," and when do I use them?** They are the assembly wiring
for durable roles — the CLI-side half of the s40/s41 identity model above, commissioned to
close the gap between "a principal is registered" and "an instance dispatched under that
role actually knows what it is and what it faces." Full spec:
[FABLE-ROLE-CHARTERS-AND-BRIEFS-SPEC.md](../../design/FABLE-ROLE-CHARTERS-AND-BRIEFS-SPEC.md)
(commission ledger row 1663; built commit `822c2cc`). Two halves, named once:
- **Charter** — the static half: what a role IS. A per-role markdown file (typically
  `roles/<role>/CHARTER.md` in a scaffolded world — `bootstrap/new-project.sh` ships an
  empty `roles/` plus a README stating the register-before-binding rule). It binds only
  when REGISTERED: a `decision` ledger row naming the role's principal, the file's
  repo-relative path, and its sha256 (computed from the on-disk bytes by the tool itself,
  never caller-supplied — ADR-0002's class of bug foreclosed by construction). A drifting
  loose file with no registration row is UNREGISTERED, and the tooling says so rather than
  guessing.
- **Brief** — the derived half: what a role FACES right now. Never authored, always
  computed at instantiation time, scoped to the role's principal: its in-force decisions,
  its obligation debt (`review_gap`/`work_review_gap`), open questions in its concerns, its
  claimable work, and its standing (an s45 suspension is surfaced LOUDLY at the top — an
  instance must learn it is suspended from its own brief, not from its first refusal).

**When would I actually reach for these, as opposed to just talking to an agent?** When you
want a role's context to be a derived, auditable fact rather than whatever prose happened to
be pasted into a prompt — most concretely, the workflow-unit compiler's dispatch step
(["Reaching the ledger through a shared boundary service ..."](CLI-AND-BOUNDARY.md#reaching-the-ledger-through-a-shared-boundary-service-and-compiling-workflow-units-2026-07-18))
hands a driven phase's agent `charter + brief` for its role via `--role-map <toml-role>=<
principal>`, refusing (with teaching) a mapping to an uncharted principal unless
`--allow-uncharted` is passed explicitly (a loud escape hatch, not a silent default). Outside
the compiler, register a charter for any durable role the moment its responsibilities stop
fitting in a sentence you're willing to retype every session.

**Commands, no raw SQL anywhere — `led` is the only write surface.** WITNESSED this session
(`--help`, byte-for-byte):
```
$ python3 tools/role_charter.py
usage: python3 tools/role_charter.py register <role> <path> [--led PATH] [--scan-limit N]
       python3 tools/role_charter.py show <role>           [--led PATH] [--scan-limit N]
       python3 tools/role_charter.py amend <role> <path>   [--led PATH] [--scan-limit N]
$ python3 tools/role_brief.py
usage: python3 tools/role_brief.py brief <role> [--led PATH] [--scan-limit N]
```
`register` writes the fixed-shape row (`role-charter registered: role=<role>
path=<repo-relative-path> sha256=<64-hex-digest>`) via `led decision`; `show` reports the
in-force registration and whether the file's current bytes still match the registered
hash — a mismatch is a loud `DRIFT` warning, not a silent pass-through; `amend` writes a new
row with `--supersedes <old-row-id>` (the ledger's own s31 uniform-retraction mechanism —
the old registration drops out of `ledger_current` exactly like any other superseded row).
`role_brief.py brief <role>` prints one clearly-headed section per source, each section
naming its own provenance (which view, which filter); work-family sections go via `--led`
exactly as the compiler does, so the served-boundary gap on those views (named elsewhere on
this page) stays visible rather than papered over.

**Honest limits, and what an operator will actually see with no charter registered yet.**
WITNESSED this session, against a real scaffolded world with no registered charter for
`author`:
```
$ python3 tools/role_charter.py show author
role_charter: REFUSED -- role 'author' has no registered charter (scanned the last 100000
  ledger_current rows; see this tool's own JC1 note if the real registration is older than
  that). Register one:
  python3 tools/role_charter.py register author <path>
```
and `role_brief.py brief <role>` needs the work-family views' `work_startable` (kernel s39)
present in the target world's schema; a pre-s39 world refuses legibly rather than printing a
partial or wrong brief — WITNESSED against a world one delta short:
```
$ python3 tools/role_brief.py brief author --led ./led
role_brief: REFUSED -- './led work startable' failed:
led work startable: REFUSED -- requires kernel/lineage/s39-blocks-start.sql applied
  to this project's schema (work_startable view not found ...)
```
A charter registration row is a convention over ordinary `decision` rows, not a minted
kernel kind (the spec's own "Honest limits" section, by design — the ADR-0011 conversion to
a typed kind is deferred until the convention is witnessed recurring); a malformed
hand-written registration is caught by `show`'s hash check, not refused at write time. Role
proliferation stays the operator's own judgment — the tool grants nothing; authority remains
entirely the kernel's standing/binding facts. Full witness record (WB1–WB6, both polarities,
scratch world, zero residue) is in the build commit (`822c2cc`)'s own message, covering
register/show/DRIFT/amend, empty-vs-populated brief sections against their direct view
queries, an obligation appearing then discharging in the next brief, percolation across two
roles, compiler wiring with the uncharted-refusal and `--allow-uncharted` legs, and an s45
suspension surfaced then lifted.
