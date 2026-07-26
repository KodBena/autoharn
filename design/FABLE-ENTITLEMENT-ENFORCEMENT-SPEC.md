# FABLE-ENTITLEMENT-ENFORCEMENT-SPEC — the ratified access-control frame, built

<!-- doc-attest-exempt: Fable-authored spec 2026-07-26, assembling the maintainer's
ratification of rows 1379/1380 (READ TOGETHER — the settlement is under protest at an
environmentally-imposed ceiling, not an endorsement; if the platform ceiling lifts, the
settlement reopens). Removal condition: superseded by the build's completion record. -->

- **Status:** RATIFIED basis (rows 1379/1380: "incorporate it with the WORK-GATING
  kaboodle. Let's implement this"); this spec is the assembly, not a new proposal. The
  §5 attention points are the only open choices, flagged for the maintainer's leisure,
  none blocking the v1 build.
- **The frame (ratified):** design/CONSULT-WORK-GATING-SHAPE-2026-07-26.md §§B–C in
  full — that document IS this spec's elaborated content; this file adds only the delta
  boundaries, the requirements fold-in, the witness plan, and the closure statement.
- **The instance annex:** design/FABLE-CONSULT-ACCESS-CONTROL-DEPTH-2026-07-22.md §§2–3
  (taint mark, zones, s51 airlock, DB-role zoning v2) — rejected-at-delivery as a
  generic design (row 1378), ratified as instance material under the frame.
- **First-class requirements folded in (row 1377):** (R1) trusted domains over
  principals; (R2) worlds incorporated into the domain concept; (R3) granular ledger
  read access by authorization level — ADR-0018's fresh-context integrity with the
  dishonest-or-curious reviewer as a NAMED adversary of the read path.

## 1. Delta v1 — s60-entitlement-enforcement (kernel/lineage, fail-safe additive)

Everything in this delta only ADDS refusals — nothing existing is relaxed — so it sits
inside the class-ratified fail-safe family (CLAUDE.md 2026-07-09 ruling): scratch-schema
witness on both polarities with the SQL/ASP differential in AGREE admits it to the birth
chain without a per-delta maintainer question.

1. **The factored acceptance predicate** (consult §B.3), inside the existing s43
   boundary functions, per act class, refusals journaled as `write_refused` with taught
   text. v1 conjuncts exactly two:
   (a) actor holds an in-force role binding the world's configuration names for the
   act class (configuration via the s36 graded-token idiom; role names stay free text
   per the ratified §9(c) ruling);
   (b) for authority-bearing acts — principal registration, role binding, standing
   lifecycle, allocation/milestone closure and supersession, gate-edge supersession —
   the actor's authority chain roots at genesis: transitive reachability over in-force
   `acts-for`/grant events, evaluated fresh at act time (the s40 computed-at-read law),
   chain links dying with supersession or standing loss (the ratified I5 asymmetry:
   past accepted acts stay credited unless positively defeated).
2. **The ASP twin ships in the same delta** — the chain closure in the
   `ledger_defeat.lp` stratification shape, beside `in_force/1`, never into it; `judge`
   holds AGREE from birth. Not filed as pairing debt.
3. **Solo-world zero-friction by construction** (consult §B.3.2): the birth sequence
   already registers maintainer/orchestrator and records `orchestrator acts-for
   maintainer`; the same sequence binds the roles the default configuration names. No
   dormant permissive branch.
4. **The WHO half of supersession** extends `validate_supersession_target`'s single
   home (s45's own precedent), never a parallel path.

### §1 AMENDMENT (2026-07-26, row 1385) — delegation acts join the authority-bearing set (s62)

§1.1b's enumeration omitted delegation acts, and s60 implemented the omission faithfully —
leaving `acts-for` assertion and supersession ungated and conjunct (b) SELF-SERVABLE (a
refused principal could mint their own chain edge and retry; the refusal text taught the
bypass). Found by the maintainer's own question; authoring defect owned on the row. s62
closes it, fail-safe additive: `principal_relation_asserted` with relation `acts-for`
(fresh and superseding) classifies as act class `delegation_lifecycle`, requiring the
WRITER's chain-to-genesis — the consult's own "each grant itself authorized" property;
genesis bootstraps the first edges at birth exactly as s60's configuration rows do. The
s60 refusal remedy text is corrected in the same delta: the edge is written by the
DELEGATOR, never self-asserted.

## 2. Delta v1.1 — signature symmetry and the key binding (serving/verbs, small)

From the consult's §B.2 table, the three rows not yet true:
1. **SIGNED supersession symmetry**: an act whose force rests on a verified signature
   is superseded only by a SIGNED act (one rule, generalizing the recovery-mode
   two-signature shape).
2. **verify against the s41 binding**: `verify-commission` (and the new act
   verification) checks the actor's in-force `principal_key_bound` fingerprint when one
   exists, not only the deployment `keys/` directory.
3. **Proof of possession at binding**: the key-binding act is itself signed by the key
   being bound; revocation by GPG revocation certificate + the s41 retraction event.
   All human-grade paths; agent keys stay refused by ratified design.

## 3. Work gating — documentation only (consult §B.4)

Zero new kernel surface: the milestone convention over s39 becomes a recipe in
user-guide/USER-RECIPES-FAQ.md (open the milestone, draw the `blocks-start` edge,
the flip is an authority-checked close — SIGNED at the maintainer's option). The
probes seam is stated verbatim: probes recommend the flip; the milestone act IS the
flip; the s39 edge enforces it. Prioritization never enters the kernel (§A1's cut).

## 4. The conjunct seats — reserved now, built by their own deltas

The acceptance predicate's later conjuncts, each entering as its own class-ratified
delta when its arc ratifies, with the DEPTH annex as the instance design where noted:
- **domain/zone** (R1+R2): label vocabulary on principals AND worlds; per-world genesis
  roots make every world a self-anchored domain; cross-domain authority only by
  explicit typed cross-root acts (missives' foreign-non-binding posture is the
  standing default). Instance design: DEPTH §3 (zones, s51 airlock; DB-role zoning).
- **taint**: origin labels + MANDATORY `derived_from` provenance edges on tainted
  flows (voluntary refs ground only advisory taint — the load-bearing caveat);
  propagation as the stratified closure in ASP's home ground; enforcement only as a
  boundary conjunct over in-force facts. Instance design: DEPTH §2 (session-granularity
  exposure mark over the basis DAG); the fixture-sandbox marker (rows 1315/1316) is
  the house's working one-bit precedent.
- **read access** (R3): DB-role-enforced read zoning over the s18/s20 grant substrate —
  connection-level confinement, never declared-zone theater (the nla BLOCKING-HAZARD
  lesson); a consult/review process connects as a role that CANNOT read beyond its
  briefed slice; the served GET surface gains per-zone scoping in the same arc (today
  it is unauthenticated — the spec that arms this conjunct must say how, not wave).

## 5. Attention points (the under-determined choices, maintainer's leisure)

1. Which act classes the DEFAULT world configuration role-gates in v1 (the consult
   names the authority-bearing set; the exact default map is policy).
2. Whether milestone-closure joins the authority-bearing set everywhere or only when
   the milestone carries inbound `blocks-start` edges (narrower; my inclination).
3. The role vocabulary the birth sequence binds by default (names are free text; the
   default set is scaffold policy).

## 6. Witness plan (scratch, both polarities, red first)

Per s-delta discipline: scratch world on the toy host; RED — an actor without the
named role binding refused per act class (journaled, taught); an authority-bearing act
by a principal with no chain to genesis refused; a chain severed mid-flight (suspend
the delegate) refuses the next act while past acts stay credited (I5 witnessed); GREEN
— the birth-bound solo world performs every ordinary act unchanged (zero-friction leg,
byte-compared against a pre-delta world's transcript); SQL/ASP differential AGREE on
all of it; the v1.1 signature legs red/green with a real detached signature and a
forged one. The gating recipe witnessed end-to-end as the consult's worked example.

## License

Public Domain (The Unlicense).
