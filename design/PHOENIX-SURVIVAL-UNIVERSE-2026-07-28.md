<!-- doc-attest-exempt: as-delivered enumeration record, filed verbatim 2026-07-28
(commission row 252: the maintainer's ADR-0000 direction on phoenix-survival --
"the class as first named is presumed too narrow"; read-only Sonnet enumerator,
classify-don't-fix mandate). This is the evidence base the phoenix runbook's
survival-audit closure statement cites. Removal condition: superseded by a later
enumeration. -->

**Provenance:** produced by the commissioned read-only enumerator (Sonnet, 2026-07-28)
from the system itself -- ledger kinds from the last kind-check re-issue, grammars from
led.tmpl's validators, carry behavior from extract_context.py read in full, config
surfaces from the tree, specimens verified against the autoharn2->autoharn3 cutover.
Filed verbatim by the coordinator.

---

## Deliverable: the phoenix-survival universe (commission row 252)

Read-only throughout. DB access: `env -u PGOPTIONS psql -h 192.168.122.1 -d toy`, schemas `autoharn2`/`autoharn2_kernel` (dust) and `autoharn3`/`autoharn3_kernel` (current). Ledger-kind vocabulary read from `kernel/lineage/s61-signature-symmetry-and-key-binding.sql:179-197` (last delta that re-issues `ledger_kind_check`; confirmed no s62-s68 file re-issues it). Statement grammars read from `bootstrap/templates/led.tmpl:1145-1471`. Extraction behavior read from `bootstrap/extract_context.py` in full (678 lines).

### 1. Ledger kinds (33, at s61)

| kind | temporal scope | reasoning |
|---|---|---|
| assumption | historical-record | a point-in-time working premise; superseded/retracted normally |
| decision | **both** | historical UNLESS `decision_grade IS NOT NULL` (s36) → then standing-force via `standing_decisions` view (`kernel/lineage/s36-decision-grade.sql:240-244`). The witnessed specimen: rows 209/241 were ungraded in autoharn2, near-lost, later re-asserted `--grade durable` |
| question | standing-force until answered | `question_status.answered=false` rows are live obligations |
| verification | historical-record | point-in-time check outcome |
| finding | historical-record | e.g. row 210 itself — but a finding can *cause* a durable decision; the finding text itself doesn't cross |
| snag | historical-record (never-class in extract) | `extract_context.py` NEVER_KINDS — count+id only, statement dropped by design |
| revision | historical-record | amends a prior row; dies with the world it amended in |
| note | historical-record | free-text annotation |
| review | historical-record (drop-with-reason) | `extract_context.py` DROP_KINDS 1.7 — "review discharges never cross, credit and debt alike" |
| work_opened | standing-force while open | crosses via `work_item_current WHERE state='open'` (1.4) |
| work_claimed | historical-record | claim binds a session that dies with the world — `extract_open_work`'s own comment: `dust_claimant_excluded` |
| work_depends_on | standing-force while parent open | dependency edge; not separately extracted (rides with 1.4 only as far as `work_item_current` reflects it) |
| work_closed | historical-record | closed work is done; debt on it is explicitly never-carried (`work_review_gap`/`work_item_violations` → drop-with-reason) |
| commission | historical-record (never-class) | extract 1.10 — count+id only |
| work_violation_disposition | historical-record (never-class) | extract 1.12 |
| principal_registered | standing-force | identity must exist for future writes to attribute; but only name+agent_class crosses (see §3) |
| principal_suspended / principal_revoked | standing-force | a live suspension/revocation is exactly the kind of MUST-NOT that should never silently lapse — **not extracted at all** |
| principal_standing_declared | standing-force | binds future entitlement; **not extracted** |
| principal_relation_asserted | standing-force | **not extracted** |
| principal_role_bound | standing-force | **not extracted** |
| principal_key_bound | standing-force | **not extracted** |
| principal_competence_granted | standing-force | **not extracted** |
| write_refused | historical-record (never-class) | extract 1.12 |
| model_identity_attested | historical-record | per-invocation attestation |
| belief | historical-record | belief substrate row, point-in-time |
| obligation_revoked | historical-record | revocation event, but if the underlying obligation was standing this changes future state — not separately carried |
| missive_sent/received/disposed | **standing-force until disposed** | cross-world state (item 6) — **not extracted**; see below |
| entitlement_class_configured | standing-force | governs future entitlement checks; **not extracted** |
| commission_signature_verified / principal_key_possession_verified | historical-record | one-time verification marker facts |

### 2. Statement grammars (8, not 7 — `led.tmpl:1462-1470`)

`resource:`, `estimate:`, `actual:`, `taxon:`, `interface:`, `outcome:`, `review:`, `review-done:`. No `task-policy:` grammar exists (brief's placeholder guess was wrong, as warned). All eight are written as bare `kind='decision'` rows through `cmd_generic` — **none has its own ledger kind**.

- **resource:** (`led.tmpl:1152-1182`) — six fields incl. TIER ∈ {available, blessed:, mandated:, forbidden:}. A `forbidden:` row is a standing MUST-NOT — standing-force. Verified empty in both autoharn2 and autoharn3 currently (`SELECT count(*) FROM ledger WHERE statement ILIKE 'resource:%'` → 0 both), so the deontic-tier hazard is presently latent, not manifest.
- **estimate:**/**actual:** — diagnostic-only by design, but temporally they're historical measurements; the *practice* of writing them is what's standing-force (row 241).
- **taxon:**/**interface:** — standing-force: they govern how future artifacts are classified.
- **outcome:** — diagnostic retrospective, historical-record.
- **review:**/**review-done:** — standing (open queue item) until disposed.

**Gap found, not previously named**: because all eight grammars live as `kind='decision'`, and `extract_context.py`'s `extract_standing_decisions()` (when `standing_decisions` exists, i.e. s36+) reads `WHERE kind='decision' AND decision_grade IS NOT NULL` only — **any `resource:`/`estimate:`/`actual:`/`taxon:`/`interface:`/`outcome:`/`review:` row that is not `--grade durable` does NOT cross the phoenix at all**, structurally, the same shape as the ungraded-decision near-loss generalized to every one of these eight grammars. Witnessed directly: rows 244-251 in autoharn3 (`actual:`/`estimate:` rows) all show `decision_grade` NULL (`psql` query run live). The tool's own `CLASSES_OUT_OF_SCOPE["1.8"]` comment (`extract_context.py:110-112`) states "estimates/actuals have no ledger `kind`" — true in the narrow sense (no dedicated CHECK-constraint member) but this masks that they DO live as `kind=decision` and so ARE nominally in scope of 1.2's query, just silently filtered out by the grade predicate. This is a documentation/reasoning gap in the extractor itself, not only a missing feature.

### 3. Kernel side-tables/registries

| table/registry | fresh birth re-creates? | does extract carry it? | else |
|---|---|---|---|
| `principal` (name, agent_class) | yes (DDL, s15) | **yes**, but ONLY name+agent_class (`extract_context.py:298-311`, `cmd_ingest` "1.1_principal_roster") | — |
| principal classes/standing declarations/relations/role bindings/key bindings/competences (`s40`/`s41`/`s45` kinds) | DDL yes, data no | **no** — not in `extract_all()` (`extract_context.py:434-441` lists only principals/standing_decisions/open_work/open_questions/drop_and_never) | operator-memory or NONE |
| entitlement_class_configured / entitlement config (`s60`) | DDL yes, data no | **no** | operator-memory or NONE |
| `world_identity` (`kernel/lineage/s58-missive-substrate.sql:247-262`) | DDL yes (table), **row: NO** — explicitly left empty by `bootstrap/new-project.sh:1228`'s own comment ("s58's kernel.world_identity is left empty by this run... a future world's own birth act") | n/a (not ledger-shaped) | **operator-step, undocumented in the scaffold itself** — spec (`design/FABLE-MISSIVES-KERNEL-SPEC.md:697` "INSERT `world_identity`... as boundary ceremonies") names the step but `new-project.sh` doesn't automate it. Verified populated in autoharn3 (`SELECT * FROM autoharn3_kernel.world_identity` → `autoharn3`) — someone did it by hand at this cutover |
| `artifact` store (`s51`) | DDL yes, data no | **no** | NONE — artifact content is presumably re-derivable from the git tree it hashes, but the store's own accumulated hash→path index does not cross |
| `review_detail` (`s15-schema.sql:270`) | DDL yes, data no | **no** (folded under 1.7 drop-with-reason, count+id only) | historical-record correctly, per design |
| `chain_high_water` | self-seeds at `max_id=0` (`s27-chain-high-water.sql:192-194`) | n/a | **correctly world-scoped** — not a gap; chains don't span worlds by design (runs-are-linear) |

### 4. The extract script itself (`bootstrap/extract_context.py`)

`extract_all()` (line 434) pulls exactly five classes: 1.1 principal roster (name/class only), 1.2 standing decisions (graded only, `decision_grade IS NOT NULL`), 1.4 open work (unclaimed only) + debt (dropped by name), 1.5 open questions, and count-only records for review/commission/violation/refusal/snag. Everything else — every principal side-table in §3, every missive kind, `belief`, `obligation_revoked`, `entitlement_class_configured`, `model_identity_attested`, resource/estimate/taxon/interface/review-queue rows that aren't graded durable — is **structurally ignored**, not merely deprioritized. `CLASSES_OUT_OF_SCOPE` (lines 108-112) documents five of the twelve consult classes as out of scope, but as shown in §2 that documentation is itself imprecise about why (1.8).

### 5. Config surfaces

| surface | tracked in git? | survival mechanism |
|---|---|---|
| `deployment.json` | no (`.gitignore:43`) | scaffold-regenerated at birth from CLI args — fine, no data to lose |
| `boundary-multiplex.toml` | no (`.gitignore:46`) | scaffold-regenerated — fine |
| `courier.toml` | **no, and not even in `.gitignore`** (checked: `grep -n courier .gitignore` → empty; `git status` shows it `??`) | **NONE for the counterpart-identity list.** Current content (`courier.toml`) names `experience4 = "http://127.0.0.1:8433"` — a world name that dies at that counterpart's own next phoenix. Nothing regenerates or updates this on either side; it's exactly the row-252 near-loss #4 (courier principal) generalized — here it's the counterpart-address book, not the principal |
| `.autoharn-world.json` | no, untracked | scaffold-written |
| `features.json` | untracked, no `.gitignore` entry found either | scaffold-written from CLI flags at THAT invocation only (`bootstrap/new-project.sh:2168-2196`, "durable, hand-editable feature-manifest record"); a phoenix does not read the OLD world's features.json — the operator must re-pass matching flags or accept defaults. Operator-memory |
| `.claude/apparatus.json`, `governed_files.json` | untracked (never tracked in repo history — `git log --all -- keys/ roles/` empty) | scaffold-regenerated from `--governed`/apparatus flags or DEFAULT (`*.py only`, `bootstrap/new-project.sh:1832-1833`) — a customized governed-file glob reverts to default unless the operator re-passes it. Operator-memory |
| `keys/`, `roles/` | never tracked | scaffold stub + operator-populated (GPG keyring material, role bindings) — NONE for actual key material across phoenix; each world's keyring is its own |
| `attestations/` (jsonl ledgers, e.g. `pre-review-log.jsonl`) | only `README.md` is present now (untracked) | the jsonl logs themselves are per-world evidence; no carry mechanism seen — historical-record, correctly NONE unless a study needs them |
| `orchlog.d/` | tracked in some cases (seen in git status: several files ARE tracked from a prior commit) | mixed — scaffold writes fresh entries; existing entries under version control are git-carried |

### 6. Cross-world state

- **Open missive threads**: `autoharn3.missive_undisposed` currently returns 0 rows (queried live) — no open threads at present, but the mechanism has **no extraction path at all**: `missive_sent`/`missive_received`/`missive_disposed` are not among `extract_context.py`'s five extracted classes. If a phoenix happened mid-thread, the thread state would be silently stranded in the dust world.
- **Counterpart couriers pointing at the dead world**: symmetric to the courier.toml gap above — the counterpart (`experience4`) has autoharn3's OLD name in its own courier.toml; nothing here updates it, and nothing here would update ours if we renamed.
- **In-flight work claimed by dead sessions**: `extract_open_work` (`extract_context.py:365-368`) explicitly excludes the claimant (`dust_claimant_excluded`) — correctly handled, not a gap; the item itself still crosses unclaimed if open.

### 7. Witnessed specimens reproduced + further members found

| specimen | channel | status |
|---|---|---|
| durable decisions (graded) | designed channel (`standing_decisions` view + extract 1.2) | WORKS |
| ungraded process rules (+A:B:C) | was NONE, now durable-graded (row 209) | patched per-specimen, not structurally — the *class* (ungraded decision rows in general) is still exposed |
| estimates practice | grammar survives in code; **practice/data itself was NONE** until row 241 re-adopted it as a durable decision (which only re-asserts the *practice*, not any individual estimate row — those still don't cross unless graded, see §2) | partially patched |
| courier principal registration | operator-remembered; row 122 shows it registered in autoharn3, but nothing in `bootstrap/new-project.sh` registers a `courier` principal at birth (grepped: zero hits for `'courier'` in that file outside the verb-dispatcher work) | **still NONE — unfixed** |
| **NEW: world_identity row** | operator-step, undocumented in scaffold (§3) | NONE in automation, populated by hand this cutover |
| **NEW: courier.toml counterpart list** | NONE — not even gitignored, no regeneration, no cross-world notification (§5) | unfixed |
| **NEW: the eight statement-grammar classes when ungraded** (resource:/estimate:/actual:/taxon:/interface:/outcome:/review:/review-done:) | NONE unless individually graded durable (§2) | structural, unfixed, currently latent (no `resource:` rows exist yet to lose) |
| **NEW: all principal side-tables** — suspensions, revocations, standing declarations, relations, role/key bindings, competences, entitlement config | NONE (§3) | unfixed — a `principal_suspended`/`principal_revoked` row is the single highest-consequence case: a REVOKED principal's revocation not crossing means the successor world could re-admit a revoked actor |
| **NEW: open missive threads / missive kind family** | NONE (§6) | unfixed, currently latent (0 open threads) |
| **NEW: features.json / governed_files.json customizations** | operator-memory (must re-pass flags) | unfixed but lower stakes — silent reversion to defaults, not a silent loosening of a security-relevant control (though `governed_files.json` narrowing IS relevant if a world had widened its governed-file glob and the phoenix quietly reverted to `*.py only`) |

### Ranking of every operator-memory/NONE row, by blast radius

1. **Principal suspensions/revocations not carried (NONE)** — highest: a revoked principal could be functionally re-admitted in the successor world with no structural block; this is a security-relevant MUST-NOT silently dropped, worse in kind than the three known specimens because it's a *revocation*, not a process convention.
2. **`resource:` `forbidden:`-tier rows, when ungraded (NONE via the grade-filter gap)** — a standing MUST-NOT on a tool/backend not carrying forward is exactly ADR-0000's "presumed too narrow" dictum in its sharpest form; currently latent only because no `resource:` rows exist yet in either world.
3. **Courier principal registration (operator-remembered, unfixed)** — already witnessed causing a real refusal at experience4 birth; confirmed still absent from `new-project.sh`.
4. **`world_identity` row (operator-step, undocumented in scaffold)** — a missing row causes every missive write to refuse loudly (fail-safe by design), so the failure mode is loud rather than silent, but the step itself is nowhere scripted.
5. **Courier.toml counterpart list (NONE, not even gitignored)** — stale counterpart addressing after either side's phoenix; degrades gracefully (missives to a dead world just don't arrive) but is unmonitored.
6. **Open missive threads / missive-kind family generally (NONE in extraction)** — currently latent (0 open threads witnessed), but structurally unrepresented.
7. **Other principal side-tables (standing declarations, relations, role/key bindings, competences, entitlement config) (NONE)** — lower urgency than #1/#2 since these tend to be additive/informational rather than prohibitive, but same structural absence.
8. **`estimate:`/`actual:`/other-grammar rows when ungraded (NONE)** — diagnostic-grade by design (maintainer's own bound: "100% diagnostic, never policy"), so the blast radius is process-improvement data loss, not a safety hazard — lowest of the structural gaps.
9. **`features.json`/`governed_files.json` operator-memory reversion to defaults** — lowest: annoyance/config-drift class, not a hazard class, though a widened `governed_files.json` reverting to the narrow default is worth a name in the closure statement since it's a silent *narrowing of what's governed*, arguably backwards from the usual fail-safe direction (it should be widened to stay safe, and silently narrows instead).

No recommendations beyond this ranking — the closure statement is the coordinator's to write.