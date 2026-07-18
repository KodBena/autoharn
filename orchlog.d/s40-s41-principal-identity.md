subject: 39480ec
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

s40 (`39480ec`) and s41 (`87f00b4`) landed: the kernel's `principal` table — the record of
*who* every ledger row is attributed to — is no longer four flat columns with no history.
Everything that can happen to an identity (registration, standing, role/key bindings,
competence, relationships to other principals) is now an append-only, attributed ledger
event, the same "event now, derived view for current truth" idiom s29/s30/s31 already use
elsewhere in the kernel. Full spec:
[design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md](../design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md)
(the frozen build basis, corrections C1–C13 governing); orchestrator-verified delivery record:
ledger row 1448.

**Read this before assuming your world has any of it: EXISTING worlds gain NOTHING here.**
Runs are strictly linear — these two deltas apply only at a *future* world's birth. A world
scaffolded before these commits stays on its old silent-column `principal` table forever;
nothing here is retrofitted onto it.

**The registration ceremony changed shape.** `register-principal`'s old
`ON CONFLICT (name) DO NOTHING` — a silent no-op on any re-registration by the same name,
the panel deployment's own Finding 1 ask #2 — is deleted. A duplicate name now REFUSES
loudly before the INSERT, in both polarities: registering the same name again with the SAME
class refuses (the identity already exists, use it); registering the same name with a
DIFFERENT class also refuses, with text naming the mismatch (classes are immutable — a
class change is a new principal plus a `succeeds` relation, not a rename). `--purpose` is
now mandatory on an s40+ kernel; the kernel itself won't let a bare anchor row commit
without a same-transaction `principal_registered` event, so even a hand-driven `psql`
registration can't skip the event half.

**Attribution is strict, always, with no toggle** — every write must resolve to a
registered principal that is neither suspended nor revoked, full stop. This sounds like
new friction; in practice it is zero for a solo world, because of the **declared-not-silent
default**: the scaffold now registers `author`/`reviewer`/`commissioner` through the full
ceremony at birth and explicitly declares `author` as the world's standing principal — so
an ordinary `./led` write with no `LED_ACTOR` set just works, resolved against that
declaration, exactly as before. What's foreclosed is only the *undeclared* fallback — a
write with no declaration and no explicit actor now gets a taught refusal pointing at
`./led principal declare-standing` instead of a bare NOT NULL error.

**Eleven new `led principal <verb>` subcommands**, grouped by family (`register-principal`
itself stays a top-level verb, rebuilt per the ceremony above, not counted in the eleven):

- *Lifecycle:* `declare-standing`, `suspend`, `revoke`.
- *Relationships:* `relate <subj> <rel> <obj>` / `unrelate ... --supersedes <id>`
  (`acts-for`, `dispatched-by`, `same-natural-person`, `succeeds` — closed vocabulary,
  self-edges refused; `same-natural-person` is canonicalized lower-id-first at write time,
  both kernel- and CLI-enforced, so it can't be recorded twice under swapped operand order).
- *Role bindings:* `bind-role <name> --role "<r>"` / `release-role ... --supersedes <id>`
  (role names are FREE non-empty text in v1, ratified — NOT a closed vocabulary; role
  naming is organizational configuration, not the harness's to impose).
- *Key bindings:* `bind-key <name> --fingerprint "<fp>"` / `revoke-key ... --supersedes <id>`
  (OpenPGP v4 fingerprint shape only; refused on any non-human principal — agent keys stay
  refused).
- *Competence:* `grant-competence <name> --activity "<a>" --band "<b>" --basis "<c>"` /
  `withdraw-competence ... --activity "<a>" --supersedes <id>`.

**Suspension and revocation: `revoked` always dominates `suspended`, and NEITHER lifts in
v1.** If a principal ends up both suspended and revoked (either write order), its standing
reads `revoked` — a strict severity ordering, not a recency one. There is no verb, in this
version, that reinstates a suspended or revoked principal. The only escape is registering a
FRESH successor principal and recording `./led principal relate <new> succeeds <old>` — a
real identity change, not a status flip. This is a deliberate, disclosed limit (spec §3.4/§8),
not an oversight.

**Competence records are recordable, NOT gating — and the band/activity vocabulary is a
loud, disclosed placeholder.** `grant-competence`/`withdraw-competence` let you record who is
believed competent for what, at what claimed band, on what basis — the safety-critical-logging
BRIEF's G13 record, finally with a typed home. Nothing in v1 checks a competence grant before
accepting any act; enforcement is a named future amendment, not built here. The band and
activity fields are free text, non-empty, and the spec's own ratification (§9(g), ledger row
1426) says explicitly: **this is a placeholder architecture only, not a considered final
design** — whether it closes to something like ASIL/SIL/DAL bands is deferred until real
deployment data exists to ground a choice.

**Derived views worth looking at directly:** `principal_standing_current` (name, class,
standing, registered_at, registrar, purpose — the one-row-per-principal human-readable
surface), `principal_relations`, `principal_role_bindings` (deliberately not
`principal_roles` — that name is reserved for the unrelated db-role↔principal binding view,
`principal_role`), `principal_keys`, `principal_competences`. All four binding views filter to
currently-active, unsuperseded rows; the raw ledger always keeps the full history including
every retraction.

**Honest limits worth carrying forward, not just reading once:**

- A database superuser/schema-owner can always bypass every trigger here, same disclosed
  bound as every prior kernel delta.
- Standing is checked strictly **at write time** — a later suspension or revocation does not
  retroactively cast doubt on writes made while a principal was still active. That's correct
  for a record, not a bug.
- **Row-hash chain coverage gap, filed as its own standing hazard:** `compute_row_hash` (s26)
  serializes only the s24-era column set. Every column added since s28 — including all
  twelve new s40/s41 principal columns — sits OUTSIDE the tamper-evidence hash chain today.
  The builder flagged this themselves (an ADR-0013 renegotiation, not a silent gap) rather
  than quietly widening the hash's own semantics on this delta's license — that's a separate,
  Fable-authored, maintainer-ratified delta family of its own. Filed as ledger work item
  `row-hash-chain-column-coverage`, row 1449, MAINTAINER-BANDWIDTH-GATED, queued not
  dispatched.
- **Total-revocation dead-end:** if every registered principal in a world ends up suspended
  or revoked, there is no sanctioned way to register a successor — `register-principal`'s own
  event requires an active actor. Recovery below one active principal is a schema-owner act
  only (spec §8, correction C7). A CLI refusal specifically naming this case (e.g. refusing
  to revoke the LAST active principal) was considered and deliberately not built in v1.
- A declared standing default authenticates nothing — it says who the connection speaks for,
  not who is at the keyboard. The key-binding slot (`bind-key`) records custody of a
  fingerprint; nothing anywhere verifies a signature against it yet (see the FAQ entry below
  for the honest GPG answer in full).
