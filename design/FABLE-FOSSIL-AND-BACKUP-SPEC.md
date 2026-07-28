# FABLE-FOSSIL-AND-BACKUP-SPEC — referrals outlive worlds; backups are witnessed or they are hopes

<!-- doc-attest-exempt: Fable-authored spec 2026-07-29, authored under the maintainer's
ratified world-agnostic-referral reading (autoharn3 durable row 355, his words verbatim
there) and the design he confirmed at rows 354/355; NOT yet ratified as a buildable
spec -- his disposition of THIS text gates any build. The A:B:C loop runs on the build.
Removal condition: superseded by the ratification row or the build's merge record. -->
<!-- design-currency: status=proposed depends-on=FABLE-MISSIVES-KERNEL-SPEC.md -->

The governing principle, the maintainer's own (row 355, verbatim): *"a referral to a
previous world is just a referral with the same guarantees as those to any world
(modulo ownership/gpg signage, so to speak, which would work the the present world
attests to some artifact of any other world, regardless of whether it's an ancestor
or just any world at all)."* Everything below is two world-agnostic layers, never
three mechanisms:

- **Layer R (resolution + integrity):** an `xrow:<world>:<id>:<hash>` referral means
  one thing regardless of which world: locate the row through ANY available backend
  and verify it against the citation's own content hash. Backends, in preference
  order: live schema → counterpart's served boundary → **fossil**. No
  ancestor-special semantics anywhere; the missive substrate already lives this
  contract between peers, and the fossil backend extends it to the dead.
- **Layer A (attestation):** the present world attests to an artifact of some other
  world — a fossil row IS that shape ("this world witnessed that world's chain head H
  and manifest hash M at time T"). Signing such rows, when the signing program wakes
  (the standing crypto deferral is untouched by this spec; the slot is named, not
  built), binds OUR attestation and never borrows the dead world's authority.

## 1. The fossilization ceremony (replaces the ad-hoc dust-disposal plan)

A world is disposed of ONLY through this ceremony, scripted as one verb
(`autoharn fossilize <deployment-record>` in this repo's own libexec; runs-are-linear
governs the kernel, not operator wiring):

1. **Verify first, loudly:** `verify-chain` against the dust world must report INTACT
   with tail-coverage and refusal-oracle confirmed; any other verdict refuses the
   whole ceremony (a fossil of an unverified chain would launder doubt into
   permanence).
2. **Export completely:** every table of `<world>` and `<world>_kernel`, data +
   schema, in the `asof-export` artifact discipline (deterministic text + JSON +
   per-file sha256 manifest), into `fossils/<world>/<iso-ts>/` — a LOCAL directory,
   never committed to the public repo (size + the standing privacy rulings); the
   MANIFEST alone (small, hashes only) is committed.
3. **The fossil row:** one ledger row in the PRESENT world (`kind=decision`, graded
   durable, statement grammar `fossil: <world> | <chain-head-id> | <chain-head-hash>
   | <manifest-sha256> | <fossil-path> | <basis>` — validated at write time like its
   sibling grammars) recording what was witnessed. This row is the Layer-A
   attestation and the resolver's index.
4. **Only then drop** the schemas, remove the deployment from the hub's multiplex
   config, and `service restart` (the drained verb) — each step printed, the whole
   transcript per the self-application rule.
5. **Counterpart courtesy:** if the world had courier counterparts, a missive to each
   announcing the fossilization (thread `<present>/fossil-notices`) — they hold
   xrows into the dust world and deserve to know resolution just moved backends.
   (The full succession protocol stays work item courier-counterpart-handover, row
   271 — this is one message, not the protocol.)

## 2. The fossil resolver (Layer R's third backend)

`led show <id>` and every xrow-resolving path gain one fallback: when the named
world's schema is absent, look up the world in the present ledger's `fossil:` rows,
read the row from the fossil export, and — non-negotiable — **verify the row's
content hash against the citation's hash** before presenting it, labeling the output
`FOSSIL-RESOLVED (verified)` or refusing with `FOSSIL-HASH-MISMATCH` (a mismatch is a
first-class alarm, never a warning). A fossil lookup with no fossil row refuses
naming what fossilization would have produced. Consequence stated plainly: provenance
sidecars and carried citations need to survive only until their world fossilizes —
the one-generation-sidecar finding (extract review round 2, pending zero-trust
confirmation) is thereby closed by DISCLOSURE plus this resolver, not by grade-spam.

## 3. Backup and the restore drill (the live world's Enduring/Available)

1. **`autoharn backup`:** dumps the live database (pg_dump custom format per
   schema-pair) to `backups/<iso-ts>/` on a SECOND medium (config names the target;
   refuses if the target is the same filesystem as the database — the refusal
   teaches why), writes a manifest, and records one `backup:` grammar row
   (`backup: <target> | <manifest-sha256> | <bytes-oom> | <basis>`), diagnostic-grade
   per the standing accounting rule.
2. **The restore drill, without which nothing above is real:** `autoharn backup
   --drill` restores the latest backup into a scratch schema, runs `verify-chain`
   against the restored copy, witnesses INTACT, tears down, and records a
   `drill:` row. A backup regimen with dumps and no drills is a hope with a cron
   job.
3. **Doctor checks, both:** `last backup age` and `last restore-drill age`, each
   PASS/FAIL with configured maxima (defaults: backup 7d, drill 30d) and teach-texts
   naming the exact commands. Staleness is loud, never a dashboard-green lie.
4. Scheduling stays the operator's (cron or hand); the verbs are the unit — no
   daemon, no new service surface.

## 4. What this spec does NOT do

No kernel change (the fossil/backup/drill rows are statement-grammar decisions, the
pre-existing extensible shape); no signing (slot named, deferral honored); no
public-repo fossil/dump content (manifests only); no automatic disposal (the ceremony
is operator-invoked, maintainer-decided per world); no change to extract/phoenix
semantics (fossils COMPLEMENT the extract — the extract carries the living forward,
the fossil preserves the dead verbatim).

## 5. Witness plan (scratch, both polarities, red first)

A scratch world born, written to, fossilized: verify-chain-refusal polarity (corrupt
one row hash in a copy, ceremony refuses); happy path produces export + manifest +
fossil row; schema dropped; `led show` of a pre-recorded xrow into it resolves
FOSSIL-RESOLVED (verified); a deliberately tampered fossil file yields
FOSSIL-HASH-MISMATCH refusing loudly; missing-fossil lookup refuses teaching.
Backup: dump + manifest + row witnessed; same-filesystem target refused; drill
restores, verify-chain INTACT on the copy, drill row written; doctor both checks both
polarities (fresh = PASS; aged config-minima on scratch = FAIL with working
teach-text commands, EXECUTED per the birth-steps precedent). Gates clean; grammar
validators for `fossil:`/`backup:`/`drill:` refuse malformed rows.

## 6. Closure statement (ADR-0000 Rule 2(a))

Quantification universe: the ways a record can fail Enduring/Available — the dead
world's rows unreachable (resolver backend), unverifiable (citation-hash check),
disposed-without-witness (ceremony's verify-first), the live world's media loss
(backup), backup unrestorable (drill), staleness invisible (doctor), and provenance
dying between generations (the sidecar limit, closed by resolver + disclosure). Not
covered, stated honestly: signing (deferred by standing ruling, slot named);
off-site/geographic redundancy (the second-medium bound is local — an operator
choice this spec does not make); the counterpart succession protocol (row 271, its
own design); fossil-format migration across far-future schema epochs (the manifest
records the exporting lineage head; reading old fossils stays a documented manual
path until a need is witnessed).

## License

Public Domain (The Unlicense).
