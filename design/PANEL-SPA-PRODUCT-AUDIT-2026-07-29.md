<!-- doc-attest-exempt: as-delivered Opus product audit, filed verbatim 2026-07-29 (maintainer
commission: "I need the SPA to look professional up to SAP/Oracle standards and be GxP in all
respects"; work item spa-gxp-product-audit row 528). First rendered-pixels pass over the panel --
51 Chromium screenshots + computed-style measurements, evidence under the session scratchpad's
shots/ directory (ephemeral; the prose carries file:line witnesses independently). ADR-0017 loop
pending. Removal condition: the loop's attestation record or the maintainer's disposition. -->

I have everything I need. Writing the report.

---

# GxP + enterprise-professionalism audit of the autoharn-panel SPA

**Subject:** `/home/bork/w/vdc/2/autoharn-panel/frontend` (Vue 3 + Vite), rendered live against the experience4 boundary at `127.0.0.1:8433`.
**Method:** scratch copy built and served on `:5200`; 51 Chromium screenshots across 26 tabs at 1920×1080, 375×812, and dark scheme, plus computed-style measurement of every rendered leaf element. All evidence under `…/scratchpad/shots/`. Read-only on both repos; no POST issued; no ledger touched.

**Standing on prior art:** the three PANEL-GXP surveys each disclose that *"the panel's rendered output was never seen. No dev server was started, no build run, no screenshot taken"* (`design/PANEL-GXP-SURFACE-FRESH-2026-07-28.md:471`). This is the first pass that looked. Where a finding is already filed I say so and do not claim it.

---

## §1 The verdict, honestly

The maintainer's read — *"very shoddy and unprofessional, not like SAP/Oracle enterprise"* — is correct, and it is mostly **one defect wearing many faces**, not twenty independent ones. That is the useful news.

### 1.1 The headline: declared column widths are silently discarded on every table under 200 rows

`DataTable.vue` accepts a per-column `width`. That value is consumed in exactly one place — `gridTemplate` (`core/components/DataTable.vue:151-153`) — which is bound **only** to the virtualized (≥200-row) path. The plain `<table>` path emits `<th>` with no width and no `<colgroup>` (`:192-206`), and `style.css:449-454` sets `table-layout: fixed`. Fixed layout with no declared widths divides the width **equally among all columns**.

Concretely, `StandingDecisionsTab.vue:26-30` declares:

```
{ key: 'id',        label: 'id',        width: '4.5rem' },
{ key: 'grade',     label: 'grade',     width: '7rem'   },
{ key: 'statement', label: 'statement', width: '3fr'    },
```

Intent: a narrow id, a narrow grade, statement takes the rest. **What renders** (57 rows, so the plain path): three equal thirds — a 3-digit id and the single repeated word `durable` each occupy ~290 px while the statement is squeezed into ~300 px and wraps to six lines, with ~700 px of empty page gutter beside it. WITNESSED: `crop-standing-top.png`, `desktop1920-standing-decisions.png`.

Same mechanism, same look, on `desktop1920-discharge-records.png` (TITLE crushed to ~120 px wrapping 15 lines beside three near-empty columns) and on the ledger, where it breaks identifiers and timestamps mid-token: `principal_registere / d`, `principal_role_bou / nd`, and `2026-07-28 00:21:45.502679+02` / `:00` — a timestamp split across lines inside its UTC offset (`crop-ledger-filters.png`). Every table in the app is under 200 rows in normal use, so this is the default rendering everywhere.

This single defect produces most of the "shoddy" impression. It is not in prior art. **GAP / WITNESSED.**

### 1.2 Typography has no scale, and four fifths of the app is small print

Measured across all 26 desktop tabs: **4,274 rendered text elements in 17 distinct font sizes; 3,395 of them (79.4%) below 12 px.** The single most common size is **9.76 px** (1,126 elements); 20 elements render at 9.52 px. Only 93 elements sit at the 14 px base and 26 at the 16.8 px `h1`.

`tokens/tokens.css` is colour-only — 15 colour tokens and two font stacks, and **no spacing, type-scale, radius or elevation tokens at all**. Consequently `style.css` carries ~40 hand-picked `rem` literals (`0.32`, `0.45`, `0.6`, `0.7`, `0.86`, `0.92`…) with no modular relationship. This is ADR-0019 **C22** ("a color, *spacing*, or interactive control … instantiated with raw/ad-hoc values") unmet at the token layer, plus **12 raw hex literals** outside the token file (`style.css:331,333,341,357,372`; `SetupConfigurationTab.vue:96`; `SetupExportSection.vue:105`; `ResourceFieldsCard.vue:78`; and four `var(--text-dim, #888)` fallbacks) — the literal case C22 names. Prior art records *no verdict on typography anywhere*, so this is new. **WITNESSED (`shots/measurements.json`) + DOC-SOURCED.**

### 1.3 No view tells you how old its data is

Grepping the whole of `src/` for `asOf|lastLoaded|fetchedAt|loadedAt` returns nothing that renders a data-freshness stamp. The only hits are the *As-of inspection* tab (a point-in-time **query** feature — a different thing) and a relative-minutes helper in `CitationLink.vue:87`. Every tab has a **Refresh** button and **not one** shows when the data on screen was loaded. WITNESSED across all 26 screenshots.

That is ADR-0019 **C7** — an aging operational datum with no viewer-legible as-of time and no distinct stale state, the rule the appendix itself calls *"the canonical control-room fatality"*. `PANEL-GXP-SURFACE-FRESH2-2026-07-29.md:315` already named C7 as unmet and acute; this run confirms it holds in the rendered product, on every surface.

### 1.4 The e-signature form fabricates the signature's meaning when left blank

`CosignPanel.vue:90`:

```js
basis: basis.value || '(no basis text entered)',
```

If the signer leaves the basis field empty, the panel **substitutes a synthetic string and submits it as the operator's basis**. The permanent kernel record then carries a reason-for-signature that no human typed, indistinguishable at the record level from one that was. For the ALCOA *Original*/*Accurate* legs, and for the thing a co-signature exists to assert, this is a record-integrity hazard rather than a cosmetic one — I flag it loudly per the standing engineering-responsibility bar. The honest alternatives are to require the field or to persist a typed "no basis given" absence, not a sentence in the operator's voice. **DOC-SOURCED** (`CosignPanel.vue:90`); UNVERIFIED at runtime by design — exercising it would require a POST, which the commission forbids.

### 1.5 The persistent chrome advertises a cosmetic gate and hides the real one

The header shows, always: `Ledger panel`, a **safe mode** badge, an **enable unsafe mode** button, and `experience4@experience4`. What it does **not** show:

- **Who is signed in.** No user, no principal, no role, anywhere in the app.
- **`identity_enforcement`.** The live boundary reports `"grace"` — the panel's own glossary defines that as *"an unauthenticated write is let through"* (`glossaryTerms.ts:112`). This fact is rendered on **one of 26 tabs** (`CapabilitiesTab.vue:139-140`), not in the chrome.

So the always-visible indicator is `safe mode` — a **client-side** toggle whose own tooltip concedes *"the boundary service … is the real enforcement point, unaffected by this toggle"* (`App.vue:159`) — while the server-side posture that decides whether records are attributable at all is buried. For ALCOA *Attributable* that is exactly inverted. The underlying unenforced-attribution fact is already filed (`…FRESH2:115-119`, H4); **that it is mis-ranked in the UI's own attention hierarchy is new.**

Related, and new: `experience4@experience4` is tautological. `health.ts:54-55` maps **both** `schema` and `kern_schema` from the same `bh.world`, and `App.vue:170` renders `{{ schema }}@{{ kern_schema }}` — so this strip can only ever print `X@X`. **WITNESSED + DOC-SOURCED.**

### 1.6 The product talks to its own developers

Product copy cites internal specs at the operator. On the default tab: *"the boundary's `rows/current` route carries no server-side filter grammar, **SPEC.md sec 2.1**"* — a document the prior survey established **does not exist**, while being cited 119 times. Standing decisions opens with *"…previously invisible in this SPA"*. The footer of every page reads *"Ledger panel — **Vue 3 port**. Extension boundary: core (rows/kinds/refs/supersession) vs `extensions/autoharn` … per SPEC.md sec 4."* Review gap tells the operator to consult `AUTOHARN_BACKFLOW.md`.

No SAP or Oracle console ships its own porting history and module boundaries in the page footer. The stale-citation *class* is filed (`…FRESH2:353-356`); the **register** problem — that this is developer-to-developer prose occupying the product's primary explanatory surface — is not. **WITNESSED** (all screenshots).

### 1.7 Ranked summary

| # | Gap | Class |
|---|---|---|
| 1 | Declared column widths discarded on the <200-row path (§1.1) | GAP, new |
| 2 | 79.4% of text under 12 px; 17 sizes; no spacing/type tokens (§1.2) | GAP, new |
| 3 | No as-of/freshness on any view (§1.3) | C7, filed as gap, now witnessed |
| 4 | E-signature basis fabricated when blank (§1.4) | GAP, new |
| 5 | No signed-in identity; `grace` posture buried (§1.5) | partly filed; mis-ranking new |
| 6 | Developer prose as product copy (§1.6) | register problem new |
| 7 | Write-arming control is 17 px tall (§3.4) | C21, new |
| 8 | No designed focus styles app-wide (§3.5) | C17, new |
| 9 | Expand affordance concatenated into record text (§2.2) | C13, new |
| 10 | Form/table borders at 1.43:1 (§3.6) | C19 non-text, new |

---

## §2 The GxP experience map — as it renders today

### 2.1 ALCOA+, leg by leg

| Leg | What the UI shows today | What an enterprise GxP user needs | Class |
|---|---|---|---|
| **Attributable** | `ACTOR` column renders a bare integer (`1`). No signed-in user anywhere. `identity_enforcement: grace` on tab 18 only. | Resolved principal *name* on every row; persistent "acting as" in chrome; enforcement posture in chrome. | Raw-id filed (`…FRESH2:407` C8); identity absence filed (H4); **WITNESSED** here |
| **Legible** | Identifiers and timestamps break mid-token (`principal_registere/d`, `+02`/`:00`); 79% of text <12 px; superseded rows dimmed to `opacity: .72` (`style.css:466`). | Record text never fractured by layout; superseded marked by label/position, not reduced legibility. | **GAP** — new |
| **Contemporaneous** | No as-of on any view; `ts` is INSERT time and nothing says so at render. | Every view stamped with load time + stale state past a threshold; event-vs-record time distinguished. | C7 filed; **WITNESSED** |
| **Original** | Verbatim kernel refusals rendered un-elided, un-summarized (`CosignPanel.vue:149-170`). Genuinely good. | — | **Met** |
| **Accurate** | Blank basis silently becomes `'(no basis text entered)'`. | Never synthesize a field the signer did not supply. | **GAP** — new, §1.4 |
| **Complete** | Statements truncate at 240 chars with in-place expand, now keyboard-reachable (`DataRow.vue:99-102,116-119`). But the expand hint is concatenated **into the record string** (§2.2). | Full text always retrievable; record text free of UI chrome. | Mixed |
| **Consistent** | Two adjacently-named, differently-keyed views (`Review gap` actor-keyed vs `Work review gap` item-keyed). Panel heading "Board" under a nav item labelled "Recent ledger". | One vocabulary, nav label = page title. | **GAP** |
| **Enduring / Available** | As-of inspection exists and works; no CSV/JSON export anywhere in 26 tabs. | Export of any audited view for retention/inspection. | Filed (`…FRESH2:341`); **WITNESSED absent** |

### 2.2 Record rendering is contaminated with UI chrome — new

`useTruncatedText.ts:66-68` builds the control affordance **into the data string**:

```js
return `${text.slice(0, truncateAt)}… [${expandHint} -- ${text.length} chars total]`
```

Rendered, an audit record reads *"…content unchanged] re-asserted from… **[click row to expand -- 1112 chars total]**"* (WITNESSED, `crop-standing-top.png`). An operator who selects and copies that statement — the ordinary way anyone extracts a record for a report — copies the UI's control text as part of the record. For human-readable record rendering this is a real defect, and it is ADR-0019 **C13** (operator-facing content as a raw string carrying its own presentation rather than a typed element). The fix shape is structural: emit the truncated text and the expand control as two elements, not one concatenated string.

### 2.3 Audit-trail review as a task

- **"What is outstanding against whom"** has no single surface; the answer is spread across `Review gap`, `Work review gap`, `Countersign obligations`, `Discharge records`, `Reservations outstanding`. Already filed (`…FRESH2:406`, C7-of-that-doc). WITNESSED: five separate nav entries, no assembled queue.
- **Supersession chain** is reachable only by opening an item view (`detail-item-1.png`, `detail-item-24.png`) — there is no listing surface for superseded rows. Filed as the #1 open item (`…FRESH:477`).
- **Discharge grade**, the kernel-computed non-forgeable independence fact, has a full badge vocabulary in `style.css:372-376` and renders in the `DISCHARGE GRADE` column — but on `desktop1920-discharge-records.png` most rows read `(no discharge record found)` or `deferred` in **plain text, not as badges**, so the strongest available integrity signal is visually indistinguishable from ordinary cell text.
- **Segregation of duties**: `PrincipalsTab`/`WorkRoleCensusTab` both render a select-then-inspect master-detail ("Select a principal above to see its full identity/SoD picture") — the right shape. But nothing pre-emptively tells a signer *"you authored this row, you cannot countersign it"*; the user discovers it by hitting the refusal. Filed (`KICKSTART:192`), still true.

### 2.4 E-signature manifestation

The co-sign form collects verdict, independence and basis. It displays **no signer identity and no timestamp** — the two other components a signature manifestation is normally expected to carry alongside meaning. It also has no action-scoped confirmation: the only guard is the global `safe mode` toggle, itself a single 17 px-tall click (§3.4). Once accepted, a co-signature on an append-only ledger cannot be withdrawn, which puts it squarely in **C10**'s class (irreversible action guarded by neither a confirm step nor an undo).

**Credit where due:** safe mode is implemented as a *separate template branch* (`CosignPanel.vue:124-127`), so the submit path is structurally unreachable rather than CSS-hidden — that is the correct construction and should not be churned.

---

## §3 Professionalism gap list, by user-visible impact

**3.1 — Equal-width columns on every table under 200 rows.** Genre: SAP Fiori's responsive table and Oracle's interactive report both size columns by declared importance and truncate/wrap the *narrow* fields, never the primary text field. Trips **C22** (the sanctioned component fails to carry the width contract on one of its two paths). *Shape hint:* have the plain path emit a `<colgroup>` from the same `Column.width` the grid path already consumes — one source, both paths.

**3.2 — No type scale; 17 sizes, 79% under 12 px.** Genre: both reference systems ship a fixed, small type ramp anchored at a 14 px body. Trips **C22**. *Shape hint:* add type/spacing tokens to `tokens.css` and let components choose a step, never a literal.

**3.3 — 1180 px content cap on a 1920 px viewport.** `style.css:24` caps `#app` at 1180 px; with the 240 px rail the data area is ~48% of the screen while columns starve (WITNESSED, every desktop shot). Genre: enterprise consoles use a fluid shell — a fixed rail with a content area that grows. Trips **ADR-0019 Rule 1** (the exemplars do not do this). *Shape hint:* fluid content column with a generous max, not a fixed 1180.

**3.4 — The write-arming control is 107×17 px.** `.mode-toggle-btn` (`style.css:345`) measures 17 px tall — the control that arms every write in the app. `.citation-link` renders at 35×14 / 41×11 px, 47 instances on one tab. Trips **C21** (24×24 baseline), in exactly the way C21 warns about: *"on a destructive control that is C10's hazard delivered by a mis-click."* *Shape hint:* min-height on interactive tokens; the mode toggle deserves to be the largest control in the header, not the smallest.

**3.5 — No designed focus indicator anywhere.** The only `:focus` rule in all of `src/` is `.skip-link:focus`. Tabbing to the active nav item yields the UA default `rgb(16,16,16) auto 1px` (WITNESSED, `detail-focus-ring.png`). Trips **C17**. *Shape hint:* one tokenised `:focus-visible` ring applied at the base layer.

**3.6 — Form-field and table borders at 1.43:1.** `--border #d9d8d2` on `--panel-bg #ffffff` = **1.43:1** (dark: 1.38:1) against the 3:1 non-text threshold; `--accent-dim` button borders = 3.73:1 against 4.5:1. This is why inputs read as barely-there in `crop-ledger-filters.png`. Trips **C19**. Separately, `button:disabled { opacity: .5 }` renders the co-sign button at ~2.32:1 — WCAG exempts disabled controls, but in this app disabled *is* the default state of every write control, so it is the state operators see permanently.

**3.7 — 26 undifferentiated peer nav items.** Already the maintainer's own `second_observations:3.1`; I confirm it renders as one flat 26-item rail with no grouping, counts or rationale, including three confusable neighbours (*Review gap*, *Work review gap*, *Review stamp distinctness*). Trips **ADR-0019 Rule 4**. Not novel — listed for completeness of the rendered picture.

**3.8 — Filter row breaks label from control.** At 1920 px the ledger filter wraps so `to:` sits at the end of line 1 while its date input is on line 2 (WITNESSED, `crop-ledger-filters.png`). Trips **C20**'s spirit (label association) even though `for=` is present. Also here: `limit: 0` uses 0 as a magic sentinel whose meaning lives in a **placeholder** (`LedgerTab.vue:209`, `placeholder="0 = all"`) that disappears the moment you type — the exact C20 failure mode.

**3.9 — Unassociated labels and a placeholder-only field on the write surfaces.** `CosignPanel.vue:131,135` use bare `<label>verdict:</label>` / `<label>independence:</label>` with no `for` and no wrapping; `:139` gives the **basis** input no label at all, only a placeholder. Same pattern at `MissiveUndisposedTab.vue:192,196`. Trips **C20**. Notably the app's *read* filters are correctly labelled throughout — the labelling discipline fails precisely on the two write forms. **DOC-SOURCED**, not witnessed: safe mode keeps these unrendered (my render-time scan found zero unlabelled inputs, which is why I mark it this way).

**3.10 — Nav label ≠ page title; two nav styles on one screen.** Nav says *Recent ledger*, the page says *Board*. On Setup, the section list uses a filled dark active state while the main rail uses a light bordered one (WITNESSED, `desktop1920-setup-configuration.png`). Trips **C22** (consistency). *Shape hint:* one active-state treatment; page title derives from the nav label.

**3.11 — Raw timestamps.** `2026-07-28 00:21:45.502679+02:00` rendered unformatted, microseconds and all, then fractured by 3.1. Genre: enterprise consoles render a locale-stable, fixed-width timestamp with precision on demand. *Shape hint:* one timestamp component; it is also the natural home for the C7 as-of stamp.

**3.12 — Layout discontinuity at the 200-row boundary.** Under 200 rows the page grows without bound (`credited-current` = 8,602 px for 100 rows); at 200 the same data becomes a 480 px scroll box (`DataTable.vue:228`). The long-page half is the maintainer's own accepted no-elision tradeoff and I am **not** filing it as a defect; the *discontinuity* — two unrelated shapes for the same view depending on row count — is the finding.

---

## §4 What is already genre-correct — do not churn

1. **The colour palette.** Every text token pair passes WCAG 4.5:1 in **both** light and dark (body 16.09:1; muted 6.83:1; every badge 5.70–7.14:1; dark equivalents 4.83–7.87:1). This is better than most enterprise consoles ship. Restyle spacing and type; leave the hues alone.
2. **No horizontal overflow at any width.** `scrollWidth == clientWidth` on all 26 tabs at 1920 and all 10 at 375. The round-2 responsive work holds.
3. **The narrow-width stacked-card degradation.** `stack-on-narrow` turns each row into a labelled card via `data-label` (WITNESSED, `narrow375-work-items.png`). Genuinely well done.
4. **Empty states that carry meaning.** *"No review gaps — every countersign obligation is currently discharged."* / *"No undisposed missives — inbox zero."* These distinguish "empty because nothing is wrong" from "no data", which is the hard part of **C6**. Eleven of them, all in this register.
5. **Verbatim refusal rendering, no paving-over** (`CosignPanel.vue:7-9,149`), and success driven only from the awaited response (**C5** met).
6. **Safe mode as a structural branch**, not a disabled attribute (§2.4).
7. **Accessible sortable headers** — `aria-sort` on the active and all other sortable columns, Enter/Space converging on the click path (`DataTable.vue:121-143`), plus the WAI-ARIA tablist with roving tabindex and arrow keys (`App.vue:108-138`), the skip link, and `role="alert"` on error banners.
8. **Keyboard row-expand is fixed** — `DataRow.vue:87,99-102,116-119` gates `tabindex`/`role=button`/`keydown` on `interactive`, closing the prior "permanently elided for keyboard users" finding.
9. **The Setup / configuration screen.** The best surface in the app: real label-left form layout, secondary section nav, derived fields visibly read-only and marked `(derived)` — **C2** honoured visibly. Use it as the in-house pattern the other 25 tabs converge on.
10. **Glossary tooltips on closed-vocabulary enums** (verdict, independence, disposition, discharge grade). The right instinct; only the delivery (`title`, hover-only) needs revisiting.

---

## §5 Closure

**Rendered and inspected — all 26 tabs at 1920×1080:** ledger, profiles, commissions, work-items, obligation-tree, discharge-records, review-gap, questions, work-violations, findings-snags, standing-decisions, countersign-obligation, review-stamp-distinctness, work-review-gap, model-attestations, model-defeated-rows, credited-current, capabilities, asof-inspection, artifacts, principals, work-role-census, mail, glossary, setup-configuration, reservations-outstanding.
**At 375×812:** the first 10. **Dark scheme:** the first 5. **Additional routes:** `/item/1`, `/item/24`, an unknown path (404 view), and a keyboard-focus probe. 51 PNGs + `measurements.json` in `…/scratchpad/shots/`.

**Could not exercise, with the concrete blocker:**
- **Every write flow** — co-sign submit, missive dispose, setup export-apply. The commission forbids POSTs to the live boundary, and safe mode additionally keeps the co-sign form structurally unrendered. §1.4, §2.4 and §3.9 are therefore **DOC-SOURCED at file:line**, not witnessed, and the fabricated-basis finding in particular deserves runtime confirmation before anyone acts on it.
- **The obligation-tree ECharts canvas** rendered but effectively empty at every width; the already-filed hover-overflow defect (row:792) needs pointer interaction I did not drive.
- **Data-dependent states**: 11 tabs were empty on this world, so their populated layouts are unjudged. The ≥200-row virtualized path never triggered — max observed was 100 rows — so §3.12's second half is inferred from source, not seen.
- **Stale/disconnected rendering** could not be provoked without interfering with the service.

**Honest limits of this judgment:**
- One engine (Chromium), one zoom level, no OS font scaling, no RTL, no print, no screen reader. Contrast figures are computed from tokens, not sampled from pixels — correct for flat backgrounds, which is what this app uses.
- I judged genre conformance against my own knowledge of SAP Fiori and Oracle Redwood/APEX conventions; **I did not fetch reference material**, so genre claims in §3 are named at the level of well-established convention (fluid shell with fixed rail, grouped launchpad navigation, column-priority tables, global header carrying user identity) and deliberately avoid specific spec citations I could not verify.
- One judgment I flagged and then withdrew: the very tall pages (up to 11,586 px) are the maintainer's own accepted no-elision tradeoff, recorded as *"the design's own stated tradeoff working as intended … not a bug."* I am not filing it. Reading the prior art before writing is what stopped that false finding, and it is the reason §1's ranking excludes several things that look wrong on a screenshot but are decided policy.
- Screenshots evidence the prose; they are not the argument. Every §1 and §3 claim carries either a filename or a `file:line`.

**Bottom line:** the panel's *foundations* are better than it looks — the palette, the responsive behaviour, the accessibility scaffolding, the refusal honesty and the empty-state writing are all at or near the bar. What is missing is the presentation layer that would let any of that read as enterprise software: a type and spacing scale, honest column widths, a freshness stamp, an identity strip, and product copy written for an operator rather than a maintainer. Fixing §1.1 and §1.2 alone would move the visual verdict more than the other twenty items combined.
