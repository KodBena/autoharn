# ORCH-SPEC-ABC-OFFERING — the fresh-context doc audit loop as a deployment offering

<!-- doc-attest-exempt: doc-tree relocation mechanical edit (work item doc-tree-reorg-user-guide, ledger row 1620, 2026-07-18) -- relative link path(s) repointed to a sibling file's new location after a git-mv relocation elsewhere in the tree; no prose rewrite, same disposition as the v1.1.2 release-cut's own markers (commit 543a389). Removal condition: strike this marker and run the real A:B:C loop next time this file is touched for content, not just link repair. -->


Audience: orchestrator (design spec; implementation stages are Sonnet-executable per §5).
Status: Fable-authored 2026-07-12, from the maintainer's same-morning question ("is there
a reason we can't use it for end users?" — on the record in this repository's tracker
ledger, work item `abc-loop-offering`; run `./led show <id>` or `./led --recent` at the
repository root to read it). The answer his question got: no architectural blocker —
the loop's fresh reviewer (role B) is an ordinary subagent invocation billed to the
session that chooses to run it, never a `claude -p` side-channel — only residence.
This spec decides the residence. The loop itself is defined by
[law/adr/0017](../law/adr/0017-the-zero-context-reader.md) and operationalized by
[ORCH-ABC-AUDIT-LOOP-RECIPE.md](../user-guide/ORCH-ABC-AUDIT-LOOP-RECIPE.md); nothing here changes
either — this document only says which pieces ship to an adopting deployment and which
stay upstream.

## 1. What an adopting deployment is missing today

The workflow steps of the recipe (author → fresh-context B → repair → re-review →
record) run identically inside any Claude Code session — the B-spawn prompt is
self-contained by design. What a scaffolded deployment (a world or standing project
created by `bootstrap/new-project.sh` or the track-work offering) cannot do today:

- **Record an attestation**: the recorder/validator
  ([gates/doc_attestation_presence.py](../gates/doc_attestation_presence.py)) and the
  attestation ledger (`attestations/doc-legibility-attestations.jsonl`) are autoharn's
  own; a deployment has neither the tool on its verb surface nor a ledger file of its
  own to append to.
- **Check presence**: autoharn checks at pre-commit — but a scaffolded world is not
  guaranteed a git repository (the scaffold, `bootstrap/new-project.sh`, creates none; a
  world's own agent may or may not initialize one, and run 12 demonstrated both states
  within one morning — its `./pickup` reported "no git repo found" at scaffold time,
  then its agent git-initialized mid-run to carry commit witnesses), so the commit-time
  enforcement point cannot be relied on there.

## 2. Residence — what ships, what stays

The same boundary rule as deployment-local signing keys
([MAINT-GPG-TRUST-LAYER.md](MAINT-GPG-TRUST-LAYER.md)) and per-deployment resource
declarations ([ORCH-SPEC-RESOURCE-REGISTRY.md](ORCH-SPEC-RESOURCE-REGISTRY.md) §2):
autoharn is used like a library; everything a deployment owns lands in the deployment:

- **Stays upstream, single-homed**: the record schema and its validator (the existing
  gate module, refactored only as far as parameterizing the ledger path and document
  root, which today default to autoharn's own); the B-prompt template (already
  single-homed in `hooks/doc_legibility_critic.py`'s `CRITIC_PROMPT_TEMPLATE`, which
  deployments can reach because their hook surface is autoharn's hooks/); ADR-0017 and
  the recipe.
- **Ships per deployment**: a thin verb shim `./attest-doc` (the same three-line
  exec-the-template pattern as `led`/`pickup`), the deployment's own attestation ledger
  file (created empty by the scaffold, like `keys/README.md`'s AWAITING-KEY stub —
  an empty ledger is honest), and a USER- audience edition of the recipe ordered by
  [USER-GUIDE.md](../user-guide/USER-GUIDE.md)'s shelf.

## 3. The verb — `./attest-doc`

Two subcommands, mirroring the upstream tool's two duties:

- `./attest-doc record <json-file>` — validate and append a doc-attestation/2 record to
  the DEPLOYMENT's ledger, content hash computed from the deployment's own on-disk file,
  same refusals as upstream (a malformed record never enters the ledger).
- `./attest-doc check [paths...]` — report, per in-scope document, whether an attestation
  matches its current content: ATTESTED, NO-ATTESTATION, or STALE (a record exists for
  different bytes). Scope in version 1 is every `*.md` under the deployment directory,
  minus the exemption marker
  [gates/doc_attestation_presence.py](../gates/doc_attestation_presence.py) already
  defines (`doc-attest-exempt: <reason>`, following ADR-0017's `doc-shapes-allow:`
  precedent for the sibling gate)
  and minus scaffold-owned files (the deployment's own CLAUDE.md, APPARATUS.md and kin —
  those are autoharn's docs, attested upstream, not the adopter's to re-attest).

## 4. Enforcement grade — verb-first, opt-in, never a silent cost

Worlds have no pre-commit, so presence-checking joins the verb surface where "done"
already lives: `./distance-to-clean` gains a DOC-ATTESTATION section counting in-scope
documents with NO-ATTESTATION or STALE status as named debt. This is gated by one
apparatus switch (`doc_attestation` mode in the deployment's `.claude/apparatus.json`:
`off` | `observe`), default **off** — not because the check costs anything (it is pure
hashing, no LLM call; the maintainer's no-silent-billing mandate is about spend, and
running the LOOP is where the spend is), but because the loop is a workflow a deployment
adopts by choice, and debt-nagging for a discipline nobody adopted would be noise. The
flip is one line, documented in the USER recipe edition. No LLM verdict ever blocks
anything (the standing ratification: presence and structural validity are checkable;
B's content judgment is not a blocking input) — and per the maintainer's standing
proviso, the mode being `off` never licenses an agent to treat ADR-0017's discipline as
optional where it applies.

## 5. Implementation routing (all stages Sonnet-executable from this spec)

- **Stage A — parameterize the upstream tool**: ledger path + doc root as explicit
  parameters on `gates/doc_attestation_presence.py`'s entry points (autoharn's own
  invocations unchanged, its defaults preserved bit-for-bit; seen-red: upstream gate
  behavior identical before/after).
- **Stage B — the verb + scaffold**: `attest-doc` template under `bootstrap/templates/`,
  shim wired by `new-project.sh` and the track-work offering, empty ledger + stub README
  seeded; seen-red both polarities on a scratch deployment (record accepted and
  re-checked ATTESTED; malformed record refused; STALE witnessed after an edit).
- **Stage C — distance-to-clean section + apparatus switch**, default off; witnessed in
  both modes; APPARATUS.md row per its table's conventions.
- **Stage D — USER-DOC-AUDIT-LOOP.md**: the recipe's USER- edition (what you type, what
  you should see — the maintainer's standing walkthrough register), linked from
  USER-GUIDE.md's Operate section; it inherits this spec's §4 honesty about cost (the
  loop spends session tokens by choice, roughly two to three times per documentation
  change, per ADR-0017's own consequences section).

## Closure statement (in the spirit of [ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)'s closure discipline — the universe-and-deliberate-absences parts; its denomination-check field concerns defect-class foreclosures and does not apply to a design scope)

The universe is the maintainer's question (can end users have the loop?) plus the four
constraints captured in the tracker item: no-git worlds (§4 answers with the verb
surface), a USER- recipe edition (§5 stage D), deployment-local ledgers (§2, §3), and
freeze-gating of template changes (§5 stages B–C are bootstrap/templates work, subject
to the standing freeze rule whenever a wired session is live). Deliberately absent,
named where they fall: hook-grade write-time enforcement (§4 — presence is checked
where "done" is computed, not per keystroke); any blocking role for B's verdict (§4);
re-attestation of scaffold-owned docs by adopters (§3). No new obligations on autoharn's
own workflow are created — its pre-commit path stands unchanged.
