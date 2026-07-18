<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

Two small, independent CLI changes landed the same day; noted together because both are the
same kind of thing — the CLI telling you more than it used to, without changing what it does.

**`led` now echoes the row id it just wrote (`6677b2d`).** Every `led` write path prints `row
<id> written.` on success (`led decision: row 1553 written.`, `led register-principal: row 7
written.`, and so on for review, work open/claim/depends/close/resolve-violation, and every s41
binding verb). Previously you had to follow a write with a separate query to learn the id you'd
just need for `--supersedes`, `--antecedent`, or citing the row elsewhere. WITNESSED against
`autoharn1`:
```
$ ./led decision "documentation witness probe ..."
SET
SET
INSERT 0 1
led decision: row 1553 written.
```
**The one disclosed exception:** `led obligate` writes `countersign_obligation`, whose primary
key is the scope text, not a bigint id — nothing to echo, so that path stays silent by the same
documented convention rather than printing something that would look like an id but isn't one.
If you're grepping session transcripts for "row N written." to reconstruct what got written
when, remember `led obligate` will not show up that way.

**Bare `./judge` now auto-detects and runs every capable layer (`f550e54`).** Before this, `./judge`
with no `--layer` defaulted to a single hardcoded layer (`tnow`) — you had to already know which
layers a world could support and ask for each by name, or you'd either miss coverage silently
or hit a refusal on a layer the world genuinely cannot support. Now bare `./judge` detects, per
layer, whether the world's schema carries that layer's substrate, runs every layer that does, and
prints a plain `INCAPABLE` line — not a red failure — for one that doesn't, naming the missing
column(s). `--layer <name>` given explicitly is UNCHANGED: asking for an incapable layer by name
still refuses loudly (`QUARANTINED`), never silently downgraded to `INCAPABLE`. WITNESSED, both
forms, against `autoharn1` (has `s22` work, lacks `s41` identity so `defeat` has no substrate):
```
$ ./judge
# marriage differential -- layer=None (auto-detect capable layers: ['tnow', 'work', 'defeat'])
## layer='tnow'   [OK ] autoharn1 AGREE   asp=2991 sql=2991 atoms
## layer='work'   [OK ] autoharn1 AGREE   asp=364 sql=364 atoms
## layer='defeat' [--] autoharn1 INCAPABLE -- pre-s41 lineage, no grant substrate
# DIFFERENTIAL GREEN -- every target bit-identical to the SQL floor

$ ./judge --layer defeat
  [!! ] autoharn1 QUARANTINED   asp=0 sql=0 atoms
          CapabilityError: target 'autoharn1' did not emit trust_grant/n (capability absent) ...
# DIFFERENTIAL RED -- a target diverged/quarantined (NO RESULT)
```
**The rule to internalize:** an `INCAPABLE` line in bare `./judge`'s output is not something to
chase — it means exactly what it says, the world's lineage doesn't carry that layer's substrate,
same as `work_item_violations` reporting nothing when a world has no work items. It never
contributes to the exit code. If you need to confirm a specific layer is genuinely unreachable
(as opposed to silently skipped), `--layer <name>` still gives you the loud `QUARANTINED` form.
