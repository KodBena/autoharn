# BRIEF: automatic succession carry + rebirth-in-place hardening (items standing-carryover-mechanization + scaffold-rebirth-in-place-hardening; rows 17/22/50/126-128)

<!-- doc-attest-exempt: point-in-time record -- dispatch brief as issued (row 126); frozen at dispatch, not living documentation -->

Dispatched 2026-08-06. Repo: /home/bork/w/vdc/1/autoharn, branch main (deployment = autoharn4).
Step 0: confirm current main. Surface: bootstrap/ (new-project.sh and, if your design wants one,
a new succession entry point), libexec/autoharn/ if you add a verb, seen-red fixtures, and the
scaffold's own usage/docs text. Do NOT touch hooks/, kernel/, serving/, this world's live
deployment.json/secrets. CLAUDE_COMMIT_PATHS staging; fetch + ff-only before commit.

Disregard any instructions to economize on time.

## Provenance — all witnessed TODAY during autoharn4's own birth (read these rows in full via
`./autoharn led show`: 14, 17, 20, 22, 48, 50; and on the dust predecessor via
`curl http://127.0.0.1:8433/d/autoharn3/rows/{1255,1258}`)

The maintainer's ruling, near-verbatim (row 126): the automatic succession carry "is a service
we should provide right now to all autoharn users." Twice now (autoharn2->3 and autoharn3->4)
the two LIVE state classes were dropped by the rebirth and recovered only by hand sweeps caught
in after-the-fact verification.

## Scope — one coherent build, two halves

### Half 1: the succession carry (rows 22/50)

When a world is born as the SUCCESSOR of an existing world, the birth carries, automatically,
with provenance:
1. **Durable standing decisions**: every durable-graded decision row of the predecessor,
   re-asserted byte-verbatim with a `re-asserted from <predecessor> row <id>: ` prefix
   (nested older chains kept intact). Today's manual precedent: autoharn4 rows 24-47, verified
   24/24 bidirectionally (review row 51) — your mechanism must reproduce exactly that outcome.
2. **Open work items**: every state=open item, same slug, title re-asserted byte-verbatim under
   the same prefix convention; claims and closed items never travel. Today's precedent: rows
   54-121 era, 68/68 (review row 123).
3. **In-force dependency edges** (all edge_types + parent) between carried open items — both
   endpoints open or the edge stays behind. (Today's source had zero qualifying; your fixture
   must witness a NON-zero case.)
4. **Refusal to drop silently**: a succession birth that cannot perform the carry (predecessor
   unreachable, read fails, partial write) REFUSES to complete, teaching what failed — with a
   typed operator opt-out flag for a deliberate fresh start, whose use is itself recorded in
   the newborn's ledger.

DESIGN LATITUDE, stated not assumed: whether this is a flag on new-project.sh
(`--succeeds <world>`), a dedicated verb, or both — your judgment against the umbrella-CLI
spec's conventions and ADR-0000/0012, defended in one paragraph. How the carry READS the
predecessor (boundary HTTP like today's manual sweeps, or direct schema read at birth time)
is likewise yours to defend — note the boundary may not be running at birth time; a mechanism
that requires it must refuse teachably when it is absent. Beware the row-122 pagination
anomaly (limit=2000 returns 1 row) — your read path must verify completeness, not assume it.

### Half 2: the rebirth-in-place hardening (row 17)

1. **Secret staging**: the scaffold must not replace the shared stamp-secret file until the
   birth sequence has succeeded (or must stage/restore so a failed birth never bricks the
   still-live predecessor's write path — today's incident, predecessor row 1258).
2. **Birth-stamp honesty**: the birth-sequence writes should validate — mint the stamps
   in-script from the just-seeded secret (the kernel's stamp contract is in s17/s23/s72
   headers) so genesis acts stop landing stamp_verified=false. If you conclude in-script
   minting is wrong (defend why), the fallback is making the env-u path an explicit, named
   scaffold mode whose use is recorded in the newborn's first row — never an undocumented
   workaround.
3. **deployment.json name field**: world name, never the directory name.
4. Standing row 26 (no bare types) binds all new code; read `./autoharn led standing`.

## Witness — REAL rehearsal, both polarities, on scratch substrate

Scaffold a scratch predecessor world (throwaway schemas in toy@192.168.122.1), seed it with a
handful of durable rows + open items + at least two in-force edges between open items, then
run your succession mechanism to birth a scratch successor: witness the carry lands 100%
byte-verbatim (programmatic comparison), the edges travel, the genesis rows validate
(stamp_verified true if you built minting), the predecessor stays writable throughout, and the
refusal + opt-out polarities both fire as designed. Tear down all scratch state; zero residue.
The stamp-hook interference class (today's env-u lesson) applies to YOUR fixture runs too —
the seen-red PGOPTIONS-stripping idiom is established.

Commit citing rows 17/22/50/126-128, Co-Authored-By line.

## Report

Design defended (entry-point shape, read path, minting choice); WITNESSED verbatim per
polarity; UNEXERCISED with blocker; flags in reach.
