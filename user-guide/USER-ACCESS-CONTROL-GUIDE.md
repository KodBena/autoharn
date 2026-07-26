# Access control in autoharn — delegation, taint, license boundaries, and reviewer read zoning

This page answers one commission (`./autoharn led show 1410` from the main checkout, and its
correction at row 1412): how does an operator (1) delegate authority, mechanically gated and
generally monotonic; (2) enforce taint semantics with a human acting as a signed filter, so no
information reaches the originating principal except through that approved human; (3) enforce a
license boundary preventing contamination across a licensing line; and (4) block read access to
a class of ledger rows for specific reviewers — the [ADR-0018](../law/adr/0018-consults-are-not-front-loaded.md)
case — without blocking it for reviewers generally. A closing section explains what about
autoharn's own construction lets these four gates be *structural* rather than merely documented.

**Audience and prerequisites.** You have a scaffolded world (`bootstrap/new-project.sh`) and are
comfortable with the vocabulary in [ORCH-OPERATING-CARD.md](ORCH-OPERATING-CARD.md) (principal,
role, standing, ledger, kernel) and the commission ladder in
[USER-GPG-TRUST-LAYER-FAQ.md](USER-GPG-TRUST-LAYER-FAQ.md) (LAZY/FULL/SIGNED). This page assumes
both rather than re-teaching them.

**Correction folded in (maintainer, row 1412, supersedes an earlier reading of row 1410):** the
maintainer's actual ask is narrower and more demanding than "ship four worked examples" — every
encoding below uses *only* generic, adopter-reachable harness primitives (typed ledger rows,
free-text role/act-class configuration — the [`s36`](../kernel/lineage/s36-decision-grade.sql)
graded-token idiom (a free-text, no-enum column where the kernel stores a word and deployment
policy decides which words matter), roles and
[`acts-for`](../kernel/lineage/s41-principal-bindings-and-relations.sql) chains (the transitive
delegation relation §1 explains),
the s61 signature verbs, and the ordinary Postgres GRANT/role/row-security substrate). Nothing
here is a taint-specific or license-specific feature this repository ships — every mechanism an
adopter could not write themselves, against their own world, from documentation alone, is instead
reported in §5 as a **harness expressiveness gap**, not quietly built around. That makes this
page double as a small expressiveness audit of the substrate it documents.

**Honest scoping, stated once up front (spec:
[`design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md`](../design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md)
§4).** Item 1 rests on kernel-live deltas:
[`kernel/lineage/s60-entitlement-enforcement.sql`](../kernel/lineage/s60-entitlement-enforcement.sql),
[`s61-signature-symmetry-and-key-binding.sql`](../kernel/lineage/s61-signature-symmetry-and-key-binding.sql),
[`s62-delegation-lifecycle-gating.sql`](../kernel/lineage/s62-delegation-lifecycle-gating.sql).
These three are now WIRED into `bootstrap/new-project.sh`'s `LINEAGE_CHAIN` (chain entries
2026-07-26, work item lineage-chain-lags-directory, ledger rows 1392/1393; s61/s62 wired at
their merges, rows 1402/1409) — a fresh `--new-world` scaffold today births through
[`s63-supersession-body-restoration.sql`](../kernel/lineage/s63-supersession-body-restoration.sql).
(Stale-claim correction 2026-07-26: this paragraph previously said the chain ends at s57;
that was true when written and false at head, caught when the panel surface survey
([`design/PANEL-GXP-SURFACE-KICKSTART-2026-07-26.md`](../design/PANEL-GXP-SURFACE-KICKSTART-2026-07-26.md))
cited it.) The
witness transcripts below predate the wiring: they were produced by hand-applying those
three files on top of a scaffolded world (`psql -f kernel/lineage/sNN-*.sql`, the same
pattern `seen-red/s60-entitlement-enforcement/`'s own fixture uses), never on a
live/production world. Items 2 and 3 are convention plus an
adopter-authored mechanical checker today, with their kernel conjuncts (taint, domain/zone) named
as reserved seats that would harden them later (§4 below). Item 4 rests on the existing s18/s20
grant substrate, generalized with a native Postgres feature (row-level security) that composes
with it.

---

## 1. Delegating authority, monotonically, with a mechanical gate that dies prospectively

### The general shape

Before `s60`, [`s41`](../kernel/lineage/s41-principal-bindings-and-relations.sql) could
*record* that a principal held a role or that one principal acted for
another, but nothing *checked* either fact at write time — any active principal could register a
new principal, bind a role, or supersede a milestone's closure. `s60` closes that with a
**factored acceptance predicate**, evaluated inside the same write boundary every kernel refusal
already goes through ([`s43`](../kernel/lineage/s43-typed-verdict-write-boundary.sql) — the
boundary functions `ledger_write`/`registration_write`/etc.),
never a second refusal surface:

- **Conjunct (a) — role binding.** For an act class this world's configuration names (a
  deployment-policy map, written as ordinary `entitlement_class_configured` rows — the same
  free-text, no-enum idiom [`s36`](../kernel/lineage/s36-decision-grade.sql)'s decision grade
  already established: the kernel stores a word,
  which words matter is deployment policy), the actor must hold an in-force `principal_role_bound`
  binding naming that role. An unconfigured act class is vacuously exempt from this conjunct.
- **Conjunct (b) — authority chain to genesis.** For the *authority-bearing* act set — registering
  a principal, binding a role, the standing lifecycle (declare/suspend/revoke), closing or
  superseding a milestone, superseding a gate edge, reconfiguring the entitlement map itself, and
  (as of `s62`, below) asserting or superseding an `acts-for` delegation edge — the actor's
  authority must trace, through zero or more `acts-for` relations, back to the world's genesis
  principal (the first principal ever registered, normally `author`).

**This is the monotone case.** Delegation here is *role-subset* delegation: a delegator writes an
`acts-for` edge naming a delegate, and the delegate's authority is now everything reachable
transitively back to genesis — there is no way, today, to hand a delegate a *narrower slice* of
the delegator's own authority (e.g. "you may bind roles but not register principals"); the chain
check is binary (reaches genesis, or does not), and any role bindings the delegate additionally
needs are separate, independently-checked `principal_role_bound` facts. So the honest reading is:
**role-subset expressiveness exists today at the role-binding layer** (bind the delegate only the
roles it needs; the chain conjunct is orthogonal and all-or-nothing), not as a single "delegate
exactly this much authority" primitive. A finer-grained, minted-not-carried sub-agent stamp — a
delegation that is itself scoped and cannot be silently widened downstream — is a **named future
spec** (ledger rows 1386/1387), not built. Say this plainly rather than imply more than exists.

**Both conjuncts are evaluated fresh, every time — nothing is cached.** A delegate's past accepted
acts are never retroactively touched by a later change to the delegator's own standing; only the
*next* act is affected. This is the **I5 asymmetry**
([`kernel/lineage/s45-standing-lifecycle.sql`](../kernel/lineage/s45-standing-lifecycle.sql)):
lifecycle standing never conditions defeat force — suspending a principal gates its future writes,
it supersedes nothing and withdraws nothing.

### The self-service bypass s62 closed, and why it matters to this doc

`s60`'s own remedy text for a chain-refusal originally read (paraphrased): "write yourself an
`acts-for` edge to a chained principal." That is a live self-service bypass — `s60` classified
*registering a principal* as authority-bearing but never classified *asserting the delegation edge
itself*, so a refused principal could simply grant themselves the very fact the refusal demanded.
The maintainer found this by asking the question directly (row 1385); `s62` closes it: a
`principal_relation_asserted` row naming relation `acts-for` (fresh assertion **or** supersession)
is now itself act class `delegation_lifecycle`, requiring the *writer* — the delegator granting
downstream authority, never the delegate about themselves — to already chain-reach genesis. `s62`
also generalizes severance: `validate_entitlement` now checks **both** the candidate write's own
class **and**, when the write supersedes another row, the *target* row's class — "severance is an
act against the target's class," so sabotaging someone else's delegation edge via a differently-
typed candidate row (a `work_depends_on` row superseding a live `acts-for` edge — a second,
independent attack shape this delta's own fixture drills alongside the self-service bypass above)
is caught too. This is a small, concrete instance of
[CLAUDE.md](../CLAUDE.md)'s hazard-in-reach corollary (an in-reach defect gets fixed or flagged
loudly, not routed around because it wasn't the assigned task) happening inside this project's own
kernel: the fix rewrote not just the
logic but the refusal's own *teach-text*, because the old text taught the exploit.

### Worked example — witnessed live, this session, on a throwaway scratch world

Scratch world `probeworldacg` (schema/kernel/role `probeworldacg`/`probeworldacg_kernel`/
`probeworldacg_rw`), scaffolded via `bootstrap/new-project.sh --new-world probeworldacg --db toy
--host 192.168.122.1`, then hand-extended with the five deltas after `s57` in lineage order —
[`s58`](../kernel/lineage/s58-missive-substrate.sql) and
[`s59`](../kernel/lineage/s59-missive-views.sql) (an unrelated messaging substrate that s60
happens to be layered on top of in this kernel's lineage order, applied only because s60
requires them as a prerequisite) and then s60/s61/s62 themselves (all five applied cleanly, no
errors). Torn down afterward with `bootstrap/teardown-world.sh`, zero residue verified. Three
principals: `author` (genesis, bound to role `authority`), `attacker` (registered, later bound to
role `authority` too, but with **no** `acts-for` chain), connected via a second Postgres login role
(`attacker_role`) declared to speak for `attacker` — mirroring the real multi-role-per-world
pattern, not a single shared connection.

**Refused — role held, no chain (conjunct b), live SQLSTATE quoted verbatim:**
```
$ psql -U attacker_role -d toy -c "select probeworldacg_kernel.registration_write(
    '{\"name\":\"nobody2\",\"agent_class\":\"human\",\"purpose\":\"...\"}'::jsonb);"

registration_write | (refused,,26,P0001,"Ledger policy: entitlement refused (s60/s62/round-2 row
1403, factored acceptance predicate conjunct b, this row's own act class) — act class
'principal_registered' is authority-bearing ...; actor 6's authority chain (transitive
reachability over in-force acts-for relations, kernel/lineage/s41-principal-bindings-and-
relations.sql) does not reach this world's genesis principal. Remedy: this is NOT a write you can
perform on yourself — have your DELEGATOR run, on your behalf: ./autoharn led principal relate
<delegator-principal-name> acts-for <a-principal-already-chain-connected-to-genesis>, covering
you ... — or have a severed link repaired ...")
```

**The delegator writes the edge on the delegate's behalf — accepted:**
```
$ psql -U bork -d toy -c "select probeworldacg_kernel.ledger_write(
    '{\"kind\":\"principal_relation_asserted\",\"statement\":\"attacker acts-for author\",
      \"principal_subject\":6,\"principal_object\":1,\"principal_relation\":\"acts-for\",
      \"principal_binding_active\":true}'::jsonb);"

ledger_write | (accepted,27,,,)
```

**The delegate's act now succeeds, through the legitimately-written chain:**
```
$ psql -U attacker_role -d toy -c "select probeworldacg_kernel.registration_write(
    '{\"name\":\"delegated-hire\",\"agent_class\":\"human\",\"purpose\":\"...\"}'::jsonb);"

registration_write | (accepted,28,,,)
```

**Revoke by supersession — the delegator retracts the same edge:**
```
$ psql -U bork -d toy -c "select probeworldacg_kernel.ledger_write(
    '{\"kind\":\"principal_relation_asserted\",\"statement\":\"revoke: attacker acts-for author,
      retracted\",\"principal_subject\":6,\"principal_object\":1,\"principal_relation\":\"acts-for\",
      \"principal_binding_active\":false,\"supersedes\":27}'::jsonb);"

ledger_write | (accepted,29,,,)
```

**The chain died prospectively — the delegate's next act refuses, same refusal shape as before:**
```
$ psql -U attacker_role -d toy -c "select probeworldacg_kernel.registration_write(
    '{\"name\":\"nobody3\",\"agent_class\":\"human\",\"purpose\":\"...\"}'::jsonb);"

registration_write | (refused,,31,P0001,"Ledger policy: entitlement refused ... actor 6's
authority chain ... does not reach this world's genesis principal. ...")
```

**But the delegate's earlier accepted act (row 28) stays credited — the I5 asymmetry, not merely
asserted:**
```
$ psql -U bork -d toy -c "select id,kind,statement from probeworldacg.ledger_current where id=28;"
28|principal_registered|principal 'delegated-hire' registered (class human)
   -- still present in ledger_current after the chain severed
```

This is the maintainer's own toy example: finite, short, monotonic while the chain lives,
revocable by ordinary supersession, and the revocation's effect is prospective-only by
construction — nothing about *how* `ledger_current` computes "in force" needed to change for
revocation to work; it fell out of the same current-truth projection every other kind already
uses. The full adversarial version of this same scenario (sabotage via a wrong-relation candidate,
a cross-kind `work_depends_on` vessel, a chainless-and-roleless saboteur) is banked verbatim at
[`seen-red/s62-delegation-lifecycle-gating/red.txt`](../seen-red/s62-delegation-lifecycle-gating/red.txt)
— every verdict quoted above matches that
banked transcript's own refusal text byte-for-byte, because it is the same mechanism.

---

## 2. Taint semantics with a human-signed filter — read-side first

### The shape that does NOT hold up, and the one that does

The naive design lets information flow freely and adds a mechanical gate that *audits* recorded
flows afterward for bypasses of the human filter. That is backwards for this requirement: an
after-the-fact audit can only ever catch a bypass that already happened, and "no information must
reach the originating principal other than via the approved human principal" is a claim about a
channel, not about a log. The shape that actually delivers the guarantee is the one item 4 below
already needs: **the originating principal's own database connection role simply cannot `SELECT`
the compartmented material.** The one path by which compartmented content crosses into that
principal's readable zone is a write authored by the approved human filter, and that authorship is
checked mechanically — not by a claimed name, but against the live `s61` signature machinery (a
verified signature against a bound key, the same verb `verify-commission --attest` uses). The
adopter-side mechanical checker becomes a **secondary tripwire** — worth having, but not the
primary enforcement; the DB connection is.

### Built from generic primitives, no autoharn-specific feature

Everything below is standard Postgres plus the s61 signature kind already shipped:

1. **Row-level security (RLS)**, a native Postgres feature, on the ledger table. A `USING`
   predicate per connecting role decides which *rows* that role's `SELECT` can see, at the
   database layer — the same layer [`s18`](../kernel/lineage/s18-criterion-principals.sql)'s reviewer roles
   (dedicated Postgres LOGIN roles, the house idiom §4 details) already use for column-level carving
   (this is the row-level generalization of that idiom, not a different mechanism).
2. A **free-text labeling convention** on `statement` (`COMPARTMENT: ...`) — no schema change.
   **This label must be correct on the row's first write.** RLS narrows on raw `statement` text,
   with no regard for supersession — a mislabeled compartment row is a permanent leak, not a
   correctable mistake; §4 below states this once, in full, as the authoritative rule for every
   label-based gate on this page (this one included), with a live-witnessed negative example.
3. The **`s61` `commission_signature_verified` kind and `signed_commissions` view**, already
   shipped, unmodified.

The policy, in full (an adopter would write exactly this against their own world):

```sql
CREATE POLICY subject_compartment_filter ON <schema>.ledger
  FOR SELECT TO subject_role
  USING (
    statement IS NULL
    OR statement NOT LIKE 'COMPARTMENT:%'
    OR (kind = 'commission' AND <schema>.commission_is_signed(ledger.id))
  );
```

**A real pitfall, worth naming so the next author does not lose an hour to it:** the first, more
obvious version of this policy called the `signed_commissions` view directly inside the `USING`
clause. That view reads `ledger_current`, which is a `security_invoker` view over the *same*
RLS-enabled `ledger` table — so evaluating the policy re-triggers RLS on `ledger` from inside its
own policy, and Postgres refuses with `infinite recursion detected in policy for relation
"ledger"`. The fix is a small `SECURITY DEFINER` helper function (`commission_is_signed`, owned by
the table owner, who — as owner — bypasses RLS by construction) that reads the raw table directly
and returns a boolean; the policy calls the function instead of the view chain. This is an
ordinary SQL authoring technique, not autoharn machinery, and any Postgres-literate adopter can
write it themselves — named here as a documented gotcha, not an expressiveness gap.

**A second, more dangerous pitfall, because it fails silently rather than refusing loudly:** any
adopter-authored view over `ledger` — not just `signed_commissions`, *any* `CREATE VIEW ... AS
SELECT ... FROM ledger` an operator writes later, for a purpose that has nothing to do with taint
— runs with its owner's privileges by default and bypasses every RLS policy above entirely unless
that view sets `security_invoker = true`. §4 below states this as a mandate, with a live-witnessed
bypass and fix, once for the whole page; it applies here identically — this compartment filter is
exactly as bypassable through an innocent later view as §4's embargo filter is.

### Worked example — witnessed live

Same scratch world as §1, extended. A raw, untrusted exposure is written as an ordinary row:

```
$ psql -U bork -d toy -c "select probeworldacg_kernel.ledger_write(
    '{\"kind\":\"decision\",\"statement\":\"COMPARTMENT: raw web-fetched content ingested by the
      research agent -- untrusted, unfiltered, must never reach the originating/subject principal
      directly\",\"confidence\":\"low\"}'::jsonb);"
ledger_write | (accepted,34,,,)
```

**Refused, structurally — not a permission-denied error, zero rows, on the base table directly:**
```
$ psql -U subject_role -d toy -c "select id, statement from probeworldacg.ledger where id=34;"
 id | statement
----+-----------
(0 rows)
```

Zero rows rather than an error is the honest, stronger form: `subject_role` was granted ordinary
`SELECT` on the table (RLS narrows what that grant can see), so there is no permission boundary to
probe for information ("does this id even exist?") — the row is invisible the same way a row that
was never written would be.

**The human filter reviews the compartmented material and writes a real, GPG-signed clearance**
(throwaway scratch key, `GNUPGHOME` isolated from any real keyring):
```
$ psql -U bork -d toy -c "select probeworldacg_kernel.ledger_write(
    '{\"kind\":\"commission\",\"statement\":\"CLEARED FOR SUBJECT: reviewed the raw web-fetched
      exposure (ledger row 34); nothing actionable crosses except this cleared summary -- the
      source stays compartmented\",\"actor\":3}'::jsonb);"
ledger_write | (accepted,35,,,)

$ printf '%s' "$STATEMENT" | gpg --detach-sign --armor -o commission-35.asc -
$ gpg --verify commission-35.asc commission-35.txt
gpg: Signature made ...
gpg: Good signature from "AUTOHARN ACCESS-CONTROL-GUIDE THROWAWAY KEY -- NEVER A REAL MAINTAINER
KEY <acg-throwaway@example.invalid>" [ultimate]

$ psql -U bork -d toy -c "select probeworldacg_kernel.ledger_write(
    '{\"kind\":\"commission_signature_verified\",\"statement\":\"verify-commission --attest: row
      35 VERIFIED ...\",\"signature_attests_row\":35,\"signature_grade\":\"directory-verified\",
      \"principal_key_fingerprint\":\"85ED1AEAF35003E97500371F1D84A23C8A1E6357\"}'::jsonb);"
ledger_write | (accepted,36,,,)
```

**Now visible to `subject_role` — the crossing — while the raw material stays invisible:**
```
$ psql -U subject_role -d toy -c "select id, statement from probeworldacg.ledger where id in
  (34,35,36);"
 id |                               statement
----+------------------------------------------------------------------------
 35 | CLEARED FOR SUBJECT: reviewed the raw web-fetched exposure (ledger row...
 36 | verify-commission --attest: row 35 VERIFIED against a directory-commit...
(2 rows)
```
Row 34 — the raw exposure — never appears. `subject_role` never had the privilege to see it,
verified-signature or not; only the human filter's *own new row* crosses.

**Honesty about how the write was attributed in this scratch run:** the `commission` row above was
written with an explicit `"actor":3` override from the `bork` connection, which — being the schema
owner — can bypass the ordinary strict-declared-default attribution
[`s40`](../kernel/lineage/s40-principal-identity-events.sql) otherwise enforces (the
same disclosed superuser/owner bound named throughout this kernel: `s43`'s own recipe entry names
it plainly). In a real deployment the commissioner's own DB role would carry its own
`principal_standing_declared` row (the same pattern `bork`/`probeworldacg_rw` carry for `author`
at birth), and the write would need no override. This scratch shortcut was taken for time, named
here rather than silently smoothed over.

### Composition and honest limits

**What this does NOT cover: out-of-band channels.** DB grants confine only *ledger-mediated* flows.
Nothing here stops the originating principal's own process from reading a shared filesystem, an
environment variable, or a terminal the human filter also has open — those channels are outside any
grant's reach entirely and need hooks-layer/workspace isolation (worktree isolation, the
per-agent-tool-restriction pattern the
[`design/FABLE-CONSULT-ACCESS-CONTROL-DEPTH-2026-07-22.md`](../design/FABLE-CONSULT-ACCESS-CONTROL-DEPTH-2026-07-22.md)
consult names for web-touching vs. kernel-writing vs. review agents) to close. Naming this boundary
plainly, not papering over it, is the point.

A reserved kernel seat covers what is not yet built here.
[`design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md`](../design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md)
§4 names a **taint
conjunct** as a later, its-own-ratified addition to the same factored acceptance predicate `s60`
already established — origin labels plus *mandatory* `derived_from`-style provenance edges on
tainted flows, propagation as a stratified ASP closure, enforcement as a boundary conjunct over
in-force facts (never gate today; a documented v1-flags-not-gates posture). What is built today —
the RLS confinement plus the s61-verified crossing — is a **convention-plus-Postgres-substrate**
answer that delivers the actual invariant now; the reserved conjunct would eventually let the
*write itself* refuse rather than relying on read confinement plus a labeling convention.

---

## 3. A mechanical license gate — and the coupling decision

**Coupling decision, stated and explained (the maintainer explicitly left this open — "maybe
couple this with taint mechanics if it makes sense"):** the taint gate (§2) and the license gate
below reuse the **same underlying shape** — a free-text label convention on `statement`, plus the
`refs` column as a derivation/citation edge, walked as a small graph by an adopter-authored script
— but they are **not merged into one gate or one invariant**. The reason: taint's rule is a
*channel* rule (who may connect and read what) enforced at the DB-connection layer; license's rule
is a *compatibility* rule (does this derivation cross an incompatible boundary) that has nothing to
do with who is reading — a fully-trusted, fully-authorized engineer can still commit a
license-incompatible derivation. Coupling them into one mechanism would either weaken the taint
guarantee (making it content-checkable rather than structurally unreadable) or force every license
check through a reviewer-role framing it does not need. What *is* shared, deliberately: the same
`refs`-as-derivation-edge convention, so an adopter who has already learned one gate's shape reads
the other with no new vocabulary.

### Built from generic primitives

`refs` is a plain `text` column every kind may carry
([`kernel/lineage/s15-schema.sql`](../kernel/lineage/s15-schema.sql)'s own
comment: *"a bare reference uses refs"*) — no schema change, no autoharn feature. The convention:
a `decision` row's `statement` may begin `LICENSE:<spdx-id>: ...`; its `refs` column may contain
`row:<id>` tokens naming the rows it derives from. An adopter-side script (**not** part of
autoharn's own `gates/` — this lives in the adopter's own repo/CI, reading their own world's
ledger over an ordinary `psql` `SELECT`) builds the derivation graph and checks a small
compatibility matrix:

```python
def compatible(descendant: str, ancestor: str) -> bool:
    if ancestor == "GPL-3.0":
        return descendant in ("GPL-3.0",)   # GPL-3.0 is viral in this policy
    return True                              # permissive ancestors impose nothing
```

(Full script: `license_gate.py`, ~80 lines, reproduced in full below — it is short enough to
carry inline, per this page's own worked-example convention.)

```python
#!/usr/bin/env python3
"""license_gate.py -- adopter-side example gate. Reads via plain psql; no autoharn internals."""
import re, subprocess, sys

def compatible(descendant: str, ancestor: str) -> bool:
    if ancestor == "GPL-3.0":
        return descendant in ("GPL-3.0",)
    return True

LABEL_RE = re.compile(r"^LICENSE:([A-Za-z0-9.\-]+):")
REF_RE = re.compile(r"row:(\d+)")

def fetch_rows(pghost, pgdatabase, schema):
    q = f"SELECT id, statement, refs FROM {schema}.ledger_current WHERE kind = 'decision' ORDER BY id;"
    out = subprocess.run(["psql", "-h", pghost, "-d", pgdatabase, "-tA", "-F", "\x1f", "-c", q],
                          check=True, capture_output=True, text=True).stdout
    rows = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\x1f")
        rid, statement = int(parts[0]), parts[1]
        refs = parts[2] if len(parts) > 2 and parts[2] else None
        rows.append((rid, statement, refs))
    return rows

def main():
    pghost, pgdatabase, schema = sys.argv[1], sys.argv[2], sys.argv[3]
    license_of, parents_of = {}, {}
    for rid, statement, refs in fetch_rows(pghost, pgdatabase, schema):
        m = LABEL_RE.match(statement)
        if not m:
            continue
        license_of[rid] = m.group(1)
        parents_of[rid] = [int(p) for p in REF_RE.findall(refs or "")]
    violations = []
    for rid, lic in license_of.items():
        for parent in parents_of.get(rid, []):
            parent_lic = license_of.get(parent)
            if parent_lic and not compatible(lic, parent_lic):
                violations.append(f"row {rid} (LICENSE:{lic}) derives from row {parent} "
                                   f"(LICENSE:{parent_lic}) -- incompatible")
    if violations:
        print("license_gate: REFUSED --"); [print(f"  - {v}") for v in violations]
        return 1
    print(f"license_gate: clean -- {len(license_of)} labeled row(s) checked, 0 violations.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

### Trip, then pass — witnessed live, on the same scratch world

Three `decision` rows: a vendored `LICENSE:GPL-3.0` library (row 37), an internal wrapper built
directly on it (`LICENSE:GPL-3.0`, `refs: row:37`, row 38), and — the violation — a
`LICENSE:proprietary` customer build citing the wrapper (`refs: row:38`, row 39):

```
$ python3 license_gate.py 192.168.122.1 toy probeworldacg
license_gate: REFUSED -- license-incompatible derivation(s) found:
  - row 39 (LICENSE:proprietary) derives from row 38 (LICENSE:GPL-3.0) -- incompatible: a
    GPL-3.0 ancestor cannot be crossed by a proprietary descendant.
```

Corrected by ordinary supersession — the customer build ships GPL-3.0 with a source offer, not
proprietary — the same house idiom every other correction in this kernel uses (write a fresh row,
`supersedes` the wrong one, nothing is edited in place):

```
$ psql -U bork -d toy -c "select probeworldacg_kernel.ledger_write(
    '{\"kind\":\"decision\",\"statement\":\"LICENSE:GPL-3.0: correction -- the customer build
      ships GPL-3.0 too (source offer included), not proprietary\",\"refs\":\"row:38\",
      \"supersedes\":39,\"confidence\":\"medium\"}'::jsonb);"
ledger_write | (accepted,42,,,)

$ python3 license_gate.py 192.168.122.1 toy probeworldacg
license_gate: clean -- 5 labeled row(s) checked, 0 violations.
```

### Honest limits

**This subsection explains why supersession is the right fix here, and why that does not
generalize.** The correction above
rewrites a *compatibility judgment* — GPL-3.0-or-proprietary is checkable and re-checkable from the
label alone, and nothing about who may read the row is at stake, so a fresh row that supersedes the
wrong one is a complete, honest fix: the gate re-reads `ledger_current`, sees the correction, and
the old verdict is retired the same way every other correction in this kernel retires. **This
pattern does NOT carry over to a label that controls read confinement** (§2's compartment prefix,
§4's `CONSULT-EMBARGO:` prefix) — there, supersession fixes which row is authoritative but never
un-shows a row a confined role already had standing access to see, because the RLS policy narrows
on raw `statement` text with no regard for supersession. §4 states this distinction once, in full,
with a live-witnessed negative example; a license mislabel and a confidentiality mislabel look like
the same kind of typo but have opposite consequences, and this page is careful not to let the one
worked example here be read as license for the other.

The label is a **text convention**, not a structural type — nothing stops a writer with ordinary
INSERT access from mislabeling a derivation, and the gate can only see what the convention was
applied to. This is the same residual §5 names as an expressiveness gap: there is no first-class,
kernel-typed classification column an RLS policy or a gate script can key on instead of parsing
`statement` text. The reserved kernel seat for this class (`design/FABLE-ENTITLEMENT-ENFORCEMENT-
SPEC.md` §4's **domain/zone** conjunct — label vocabulary on principals and worlds, cross-domain
authority only by explicit typed acts) would eventually give both this gate and §2's taint gate a
real column to key on instead of a prefix convention.

---

## 4. Read access blocked for a class of rows, for specific reviewers (ADR-0018)

[ADR-0018](../law/adr/0018-consults-are-not-front-loaded.md) states the discipline this recipe
serves: a consult "receives exactly: the witnessed problem, its evidence, and the governing LAW ...
never ... the commissioner's candidate answers, enumerated options, suspect lists, reading lists,
priors, or leanings." That is a **read-access** requirement — a fresh-context consult-class
reviewer must not be able to see rows carrying the commissioner's own candidate answers or suspect
ordering, while a general-class reviewer (reviewing the ordinary way, with full context) has no
such restriction. This is the read-side mechanism §2 above borrows.

### The substrate: connection-level confinement, never declared-zone theater

[`kernel/lineage/s18-criterion-principals.sql`](../kernel/lineage/s18-criterion-principals.sql)
already establishes the house idiom: dedicated
Postgres LOGIN roles (`rev1`/`rev2` there), narrow `GRANT`s carved by column, a negative-control
assertion block baked into the delta that RAISEs if broader access ever leaks.
[`s20`](../kernel/lineage/s20-obligation-grants-and-view-refresh.sql) fixed the
general class this rests on — a view built with `SELECT l.*` freezes its column list at `CREATE
VIEW` time, so a later `ALTER TABLE ADD COLUMN` silently never reaches it; every kernel view since
re-issues with an explicit column list for exactly this reason.

**The standing lesson this all traces to, named honestly rather than glossed over:**
[`kernel/lineage/nla-schema.sql`](../kernel/lineage/nla-schema.sql)'s own `BLOCKING HAZARD`
comment (lines 232–241): a separate,
catalog-isolated database was built specifically so a subject role could not read the operator
catalog — and isolation still failed *live*, because PostgreSQL grants `CONNECT` to `PUBLIC` by
default and the local `pg_hba.conf` admitted every role to every database. **A declared zone with
shared credentials is documentation, not confinement.** Row-level security composes with this
lesson rather than contradicting it: the policy below is enforced by Postgres itself at the row
level, for the exact connecting role, with no reliance on the querying code behaving.

### Worked example — witnessed live, same scratch world

A general decision and an embargoed one:
```
$ psql -U bork -d toy -c "select probeworldacg_kernel.ledger_write(
    '{\"kind\":\"decision\",\"statement\":\"CONSULT-EMBARGO: candidate fix list and suspect
      ordering for the s60 audit, drafted by the orchestrator ahead of the fresh-context consult
      -- ADR-0018 forbids handing a consult the commissioner's own candidate answers, so this row
      must never reach a consult-class reviewer\",\"confidence\":\"medium\"}'::jsonb);"
ledger_write | (accepted,32,,,)
```

Two reviewer roles, `consult_reviewer_role` and `general_reviewer_role`, both granted ordinary
`SELECT` on the ledger table and `ledger_current`, narrowed by row-level security policies:

```sql
ALTER TABLE probeworldacg.ledger ENABLE ROW LEVEL SECURITY;

CREATE POLICY consult_reviewer_row_filter ON probeworldacg.ledger
  FOR SELECT TO consult_reviewer_role
  USING (statement IS NULL OR statement NOT LIKE 'CONSULT-EMBARGO:%');

CREATE POLICY general_reviewer_full_read ON probeworldacg.ledger
  FOR SELECT TO general_reviewer_role
  USING (true);
```

**The consult-class reviewer's read is silently narrowed, not merely denied a table** — the
embargoed row does not exist for this connection, on the base table directly:
```
$ psql -U consult_reviewer_role -d toy -c "select id, statement from probeworldacg.ledger where
  id=32;"
 id | statement
----+-----------
(0 rows)
```
Twenty-six rows out of the world's twenty-seven visible to this role at that point — exactly the
one embargoed row missing (verified by count against the unrestricted `bork` connection: 27
total). No permission-denied error at any layer — the row is invisible the same way a
never-written row would be, which is what makes this **structural** rather than a client-side
filter a careless reader could route around.

**The general-class reviewer sees it, unrestricted:**
```
$ psql -U general_reviewer_role -d toy -c "select id, statement from probeworldacg.ledger_current
  where id=32;"
 id |                        statement
----+-----------------------------------------------------------
 32 | CONSULT-EMBARGO: candidate fix list and suspect orderin...
(1 row)
```

Both roles read through the *exact same view* (`ledger_current`) — the difference is entirely at
the row-security layer beneath it, per-role, enforced by Postgres on every access path (the base
table too, as shown above), never by which view happened to be queried.

### Embargo-first: the label must be right on the first write (the authoritative statement)

**Supersession corrects FORCE, never VISIBILITY.** Every RLS policy in this page (§2's and this
section's alike) is a `USING` predicate over the *raw* `statement` text of *every row the table
holds* — it has no idea, and does not ask, whether a row is currently in force or has been
superseded ten times over. `ledger_current`/`ledger` quantify over history, not over "what's true
now"; superseding a mislabeled row changes which row a *reader who resolves supersession* treats
as authoritative, but the mislabeled row itself never stops existing, never stops being a row the
confined role's grant can see, and never becomes retroactively embargoed. **A label mistake made
on the first write is therefore not a bug to fix later — it is a permanent leak**, because this
kernel has no `UPDATE` path for a governed table at all (line-item in §6 below) and no "please
also embargo my past self" operation. The maintainer's own framing for this (row 1418, on the
motivating case): building an isolated worktree to hide comments from a reviewer "wouldn't do if
we'd written the commission with a typo in the first, then superseded the typo'd entry — the
reviewer could then work out where the comment-ful source is."

**Witnessed live, same scratch mechanics as every other example on this page, a fresh scratch
world (`fixacgw0060`, torn down after, zero residue verified — the original `probeworldacg` world
this page's other examples were run against no longer exists; runs are linear, this is a fresh
witness of the same mechanism, not a continuation).** An orchestrator writes the exact ADR-0018
embargo content from this page's own §4 example — but forgets the `CONSULT-EMBARGO:` prefix, an
ordinary labeling typo:
```
$ psql -d toy -c "select fixacgw0060_kernel.ledger_write(
    '{\"kind\":\"decision\",\"statement\":\"candidate fix list and suspect ordering for the s60
      audit -- ADR-0018 forbids handing a consult reviewer this content\",
      \"confidence\":\"medium\"}'::jsonb);"
ledger_write | (accepted,7,,,)
```

The same RLS policy this section teaches (`... USING (statement NOT LIKE 'CONSULT-EMBARGO:%' ...
)`) is already in force. Because row 7 carries no `CONSULT-EMBARGO:` prefix, it is not narrowed —
**the confined reviewer reads it in full, first try, no bypass needed:**
```
$ psql -U consult_reviewer_role_fixacgw0060 -d toy -c "select id, statement from fixacgw0060.ledger
  where id=7;"
 id |                                                       statement
----+-----------------------------------------------------------------------------------------------------------------------
  7 | candidate fix list and suspect ordering for the s60 audit -- ADR-0018 forbids handing a consult reviewer this content
(1 row)
```

The mistake is caught and corrected the idiomatic way — a fresh, correctly-labeled row superseding
the bad one, exactly the pattern §3's license correction uses:
```
$ psql -d toy -c "select fixacgw0060_kernel.ledger_write(
    '{\"kind\":\"decision\",\"statement\":\"CONSULT-EMBARGO: candidate fix list and suspect
      ordering for the s60 audit -- ADR-0018 forbids handing a consult reviewer this
      content\",\"confidence\":\"medium\",\"supersedes\":7}'::jsonb);"
ledger_write | (accepted,8,,,)
```

**The new row is correctly embargoed — the policy narrows it exactly as designed:**
```
$ psql -U consult_reviewer_role_fixacgw0060 -d toy -c "select id, statement from fixacgw0060.ledger
  where id=8;"
 id | statement
----+-----------
(0 rows)
```

**But row 7 — the mislabeled corpse, now superseded — is still fully readable to the confined
role, on the raw table and through `ledger_current` alike, forever:**
```
$ psql -U consult_reviewer_role_fixacgw0060 -d toy -c "select id, statement from fixacgw0060.ledger
  where id=7;"
 id |                                                       statement
----+-----------------------------------------------------------------------------------------------------------------------
  7 | candidate fix list and suspect ordering for the s60 audit -- ADR-0018 forbids handing a consult reviewer this content
(1 row)

$ psql -U consult_reviewer_role_fixacgw0060 -d toy -c "select id, statement from
  fixacgw0060.ledger_current where id in (7,8);"
 id |                                                       statement
----+-----------------------------------------------------------------------------------------------------------------------
  7 | candidate fix list and suspect ordering for the s60 audit -- ADR-0018 forbids handing a consult reviewer this content
(1 row)
```

**The moral, stated plainly rather than left to be inferred:** supersession is the correct fix for
*being wrong* (§3's license case — a compatibility judgment, checkable and re-checkable, no read
boundary at stake). It is never the fix for *mislabeling a zoning/embargo boundary* — that mistake
is realized the instant the write commits, and the only remedies are a carve (an exceptional,
superuser-level operation on the row outside every ordinary kernel write path — and one that
breaks the tamper-evident hash-chain invariant this kernel otherwise holds, so it is a last resort
named here rather than a workflow step) or never-write (get the label right on the first write,
which is the only remedy that costs nothing and the only one this page recommends). Treat every
zoning label the way `s43`'s write boundary treats every act: checked before the write commits,
never patched after.

### The view-authorship trap — an adopter view over `ledger` bypasses RLS by default, witnessed

RLS above governs the *table*. Postgres views do not inherit that confinement automatically: a
view's `SELECT` runs with the *view owner's* privileges unless the view opts out
(`security_invoker`, default `false`) — so a completely innocent-looking view, written by an
exempt owner with no compartment/embargo awareness at all, silently reopens every boundary above.

**The schema owner (`bork` in this scratch world, the same disclosed exempt bound named throughout
this page — §2's actor override, §6's tradeoffs paragraph) writes an ordinary summary view, no
special privilege requested, granted to the confined role:**
```
$ psql -d toy -c "create view fixacgw0060.decisions_summary as select id, kind, statement from
  fixacgw0060.ledger where kind = 'decision'; grant select on fixacgw0060.decisions_summary to
  consult_reviewer_role_fixacgw0060;"
CREATE VIEW
GRANT
```

**The confined reviewer reads the embargoed row straight through it — full bypass, the RLS policy
never fires, because the view runs as its owner, not as the querying role:**
```
$ psql -U consult_reviewer_role_fixacgw0060 -d toy -c "select id, statement from
  fixacgw0060.decisions_summary where id=8;"
 id |                                                               statement
----+----------------------------------------------------------------------------------------------------------------------------------------
  8 | CONSULT-EMBARGO: candidate fix list and suspect ordering for the s60 audit -- ADR-0018 forbids handing a consult reviewer this content
(1 row)
```

**`security_invoker = true` on the same view, same GRANT, nothing else changed, closes it — the
confined role's read through the view now narrows exactly like the base table:**
```
$ psql -d toy -c "alter view fixacgw0060.decisions_summary set (security_invoker = true);"
ALTER VIEW

$ psql -U consult_reviewer_role_fixacgw0060 -d toy -c "select id, statement from
  fixacgw0060.decisions_summary where id=8;"
 id | statement
----+-----------
(0 rows)
```

(The unlabeled corpse, row 7, still leaks through this now-fixed view too — consistent with the
embargo-first finding above: `security_invoker` makes the view respect the table's RLS policy, it
does not retroactively fix a mislabeled row the policy itself never narrowed.)

**Mandate, stated plainly, not left for an adopter to discover the hard way:** every
adopter-authored view over a governed, RLS-carrying table (`ledger`, `ledger_current`, or any view
built on either) in this recipe family MUST be created — or altered — with `security_invoker =
true` (Postgres 15+; every worked example on this page ran on Postgres 18). Where the deployment
target predates Postgres 15, or `security_invoker` is unavailable for some other reason, the
zoning predicate itself must be repeated inside the view's own `WHERE` clause — a second place to
keep in sync with the table policy, strictly worse than the one-line flag, but the only remaining
structural option. A view that does neither is not a weaker version of this recipe; it is a
silent, total bypass of it, indistinguishable at read time from a correctly-narrowed one until
someone thinks to check `pg_views.security_invoker`.

### Honest limits (named, not glossed over)

**The served GET surface is unauthenticated today.**
[`design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md`](../design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md)
§4's own words: "the served GET surface gains per-zone scoping in the same arc [as the domain/zone
conjunct]; today it is unauthenticated." This recipe secures a direct Postgres connection with a
named, distinct login role — it says nothing about a boundary service serving the same content over
HTTP to an unauthenticated caller. Do not read this recipe as covering that surface.

**Row-class classification is, again, a text convention** (`CONSULT-EMBARGO:` prefix) rather than a
structural, kernel-typed column — the same residual §3 names. An RLS policy can match on any SQL
expression, so a real deployment is not stuck with prefix-matching (a dedicated marker table joined
by row id, populated at write time, would be sturdier and is well within reach of ordinary SQL —
still a generic technique, not an autoharn feature), but nothing in the shipped kernel today hands
an adopter a structural label to key on instead.

---

## 5. Expressiveness gaps found while building this page (input to the v2 enforcement round)

"v2" here is the maintainer's second-round enforcement ruling (ledger rows 1411/1412):
MECHANICAL enforcement gates built from GENERIC primitives an end user can wield, never
pattern-specific features. Per the maintainer's correction (row 1412): every point below is a generic-substrate gap, stated
generically, never as "add a taint/license feature." Each was hit while trying to encode the four
recipes above from primitives a zero-context adopter already has.

1. **The kernel has no structural, kernel-typed classification/label column on `ledger` rows.** Both the taint
   compartment convention (§2) and the license label convention (§3), and the ADR-0018 embargo
   convention (§4), had to be encoded as a `statement`-text prefix matched by `LIKE`, because no
   generic, free-text (s36-idiom) column exists for "what class of thing is this row" the way
   `entitlement_act_class` exists for act classification. RLS policies, license gates, and
   compartment gates all had to parse prose instead of matching a column. The `domain/zone` and
   taint conjuncts named in
   [`design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md`](../design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md)
   §4 would close this if
   built as a *generic* labeled column (graded-token idiom, no enum) rather than a
   taint-or-license-specific field — a single generic label surface would serve all three recipes
   above identically. **The consequence, stated rather than left implicit:** because the
   convention is text parsed by `LIKE`/regex rather than a type the write boundary itself could
   validate, a labeling mistake at write time is invisible until someone reads the row through the
   wrong role's connection — and for the confidentiality-carrying labels (§2, §4) that mistake is
   permanent the instant it commits, per §4's embargo-first discipline and its live-witnessed
   negative example. A structural column would not just be tidier; it would let the write boundary
   itself refuse a malformed or missing zone label before the row exists at all, closing the exact
   window this fragility leaves open today.
2. **`refs` is unstructured text, parsed by regex here.** It works (§3), but every adopter who
   wants a derivation graph re-implements the same `row:<id>` token convention and the same
   fragile regex. A generic, structured multi-value reference column (or a documented, canonical
   token grammar for `refs` itself) would remove one hand-rolled parser per adopter rather than
   leaving citation-edge parsing as private knowledge each gate reinvents.
3. **RLS self-reference recursion is a real authoring trap with no generic guidance.** Composing
   an RLS policy with the s61 signature views (both resting on the same RLS-enabled table) hits
   `infinite recursion detected in policy` unless the author already knows the `SECURITY DEFINER`
   escape-hatch pattern. This is a documentation gap more than a substrate gap — noted here because
   it is exactly the kind of "private knowledge a zero-context adopter would not have" the
   correction asks to surface — but it did not block the encoding (§2 above carries the fix), so it
   is not filed as a blocking gap, only flagged.
4. **There is no served-boundary equivalent of RLS.** §4's honest-limits paragraph names this: the DB-level
   confinement in this page has no counterpart on the served GET surface, which authenticates no
   caller at all today. Building the domain/zone conjunct without also arming the served surface
   would leave exactly the gap [`s51`](../kernel/lineage/s51-artifact-store.sql)'s airlock
   pattern already warns about (a compliant path that
   is cheaper than the leaky one, not a leaky path closed outright).

None of the four recipes above needed a workaround that *silently* stood in for a missing
primitive — where a generic technique existed (RLS + a `SECURITY DEFINER` helper, `refs` regex
parsing, a `statement` prefix), it was used and named as exactly that: a technique built from
existing generic vocabulary, not a hidden autoharn-specific shim.

---

## 6. What makes these gates structural rather than merely documented

The four recipes above lean on the same handful of mechanisms, repeatedly, on purpose — this is
the harness's actual claim to usefulness: a **generic** substrate carries all four patterns without
needing a feature per pattern, which is the point the maintainer's correction was making. Stated
plainly, with the tradeoffs that go with each:

- **Nothing is edited in place — every row is append-only, corrected only by supersession — and
  this is an integrity virtue AND a confidentiality hazard, both true at once, stated plainly
  rather than only the flattering half.** Every
  correction above (the revoked delegation, the corrected license row) is a fresh row naming what
  it supersedes — there is no `UPDATE` path for a governed table at all. For integrity this is
  unambiguously good: a mistaken write cannot be quietly fixed in place, only outlived by a row
  that says so, which is also the audit trail nothing can retroactively edit out from under a
  reader. **The same property cuts the other way for confidentiality**: a row that should never
  have been readable by some role also cannot be quietly fixed in place — supersession changes
  which row is authoritative, never which rows a standing grant can already see (§4's embargo-first
  discipline, with a live-witnessed negative example: a mislabeled row, once superseded by a
  correctly-labeled one, still leaks the original to a confined reviewer forever). The discipline
  this buys — an unforgeable history — is the same discipline that makes a labeling mistake
  permanent. Both halves are the point; naming only the first would be a marketing claim, not an
  honest one.
- **Every write funnels through one typed boundary.** `s43`'s five `SECURITY DEFINER` functions are the *only* way a
  granted role's writes reach a governed table — the granted role holds no direct `INSERT`
  privilege at all. Every refusal in this page came from inside that one boundary, in the same
  shape (`disposition`, `message`, `sqlstate`, `refusal_id`), which is why a new conjunct (§1's
  chain check, §2's signature symmetry) is a few lines inside an existing trigger chain rather than
  a new enforcement surface to keep in sync with the old one.
- **In-force truth is computed at read, from one projection.** `ledger_current` is the *only* place
  "what is true right now" is computed, everywhere in this kernel — there is no cached
  "current role" table, no materialized "who is entitled" snapshot to go stale. The chain-to-genesis
  check in §1, the RLS policies in §2 and §4, and the license graph in §3 all read live off the same
  append-only history, which is why revocation in §1 took effect on the *very next* read with no
  separate invalidation step.
- **Entitlement is evaluated fresh, at act time, from the same rows the write itself is about to
  join.** Nothing about who may act is decided ahead of time and cached — `principal_authority_chain_
  reaches_genesis` is a `STABLE` function re-walked on every call, which is exactly why suspending a
  delegate changed the *next* act's outcome without anyone touching the delegate's past rows.
- **Connection identity attributes every row — never a name typed into a payload.** `s40`'s
  strict-declared-default attribution means a write's `actor` comes from *which database role
  actually connected*, resolved server-side against `principal_standing_declared` rows, not from a
  client-supplied field (the one exception exercised in this page — an explicit `actor` override —
  worked only because the connecting role was the schema owner, a disclosed bound named at the
  point it was used in §2, not a general escape hatch).
- **Every kernel delta this page relies on ships its refusal logic as an SQL/ASP twin, proven
  against a red-first banked fixture before its green is credited.** Every such delta ships
  its refusal logic in both SQL (what actually runs) and a parallel ASP encoding, differential-
  tested to agreement (`judge`), and every fixture is required to have been *seen red* — demonstrated
  failing on the exact defect shape it guards — before its green is credited. This is why the
  refusal text quoted in §1 and reproduced from
  [`seen-red/s62-delegation-lifecycle-gating/red.txt`](../seen-red/s62-delegation-lifecycle-gating/red.txt)
  matches this session's own fresh run byte-for-byte: it is the same mechanism, not a coincidentally
  similar one.
- **Gates stop a defect from recurring mechanically, rather than relying on a prose reminder.**
  [`gates/staging_guard.py`](../gates/staging_guard.py)'s
  `CLAUDE_COMMIT_PATHS` discipline (used to commit this very page, below) is the house pattern the
  license and taint gates in §2/§3 imitate: a small, readable, adopter-owned script that trips
  loudly on a real violation and passes cleanly on a real fix, checked in CI rather than remembered.

**Naming this section's own title honestly: "structural" has a boundary, and it runs through view
authorship.** RLS is structural for *direct* table access — no client-side filter to route around,
enforced by Postgres itself on every connection, exactly as claimed above. It is NOT structural
against a later `CREATE VIEW`: an adopter-authored view over a governed table runs with its
*owner's* privileges by default and silently bypasses every policy this page teaches unless that
view sets `security_invoker = true` (§2's and §4's mandate, with a live-witnessed bypass-then-fix
in §4). Once RLS is in play, **view authorship joins the trusted computing base** the same way the
schema-owner/superuser bound already does below — a single ordinary-looking `CREATE VIEW`, written
by someone with no idea a compartment or embargo policy exists, undoes the whole recipe. This page
does not get to claim "structural, full stop" without naming that one mandatory rule the claim now
depends on.

**The tradeoffs, stated rather than left implicit.** A database superuser or schema owner bypasses
every trigger, every RLS policy, and every grant here — that bound is unchanged by anything in this
page and is named at every point it was actually exercised (§2's actor override). The signature
machinery in §1/§2 buys **falsifiability**, not cryptographic impossibility, against a
directly-privileged writer who skips `gpg` entirely and forges a `commission_signature_verified`
row by hand — the same disclosed grade as the [session HMAC
stamp](../kernel/lineage/s17-stamp-mechanism.sql) (a per-session tamper-evidence tag distinct from
a writer's own claim of who they are) and the hash chain elsewhere in this kernel. And every label-based convention in §2–§4 is exactly as strong as the discipline applying
it consistently — §5's gaps are the honest list of where a structural column would replace that
discipline with a type, and are not yet built.
