<!-- doc-attest-exempt: verbatim sighted-consult record (phase 1 of the 2026-07-22 UI-proscriptions commission); the critique in the ADR-0019 companion adjudicates it. Removal condition: none needed while it stands as frozen record. -->

# CONSULT — Twelve proscriptions for an ADR-0019 extension (UI anti-patterns as broken correspondences)

- **Genre:** Independent consult (not law until Fable-authored and maintainer-ratified). Input
  for an ADR-0019 extension; written as proscriptive rule text so the maintainer can lift or
  cut clauses directly.
- **Commission:** the maintainer found the UI/HCI anti-pattern literature "nebulous" and wants
  it distilled into enforceable law that extends
  [ADR-0019](../law/adr/0019-genre-convention-is-the-default-spec.md).
- **Law read in full before authoring:** ADR-0019 (all three rules + the 2026-07-22 append),
  ADR-0000 (two-question reflex, closure-statement discipline, named-consumer test), ADR-0002
  (loudness hierarchy), ADR-0011 (enforcement-surface vocabulary, recurrence→mechanism, nets
  quantify over the class, negative-control + shipped-binding), ADR-0012 (P1 one-home, P2
  seam/translate-and-validate, P3 no god-objects, P4 live-not-frozen, P5 fail-loud/root-cause,
  P8 typed-signature-SSOT). Also read the in-flight setup-TUI build basis
  (`FABLE-SETUP-TUI-TYPED-UI-SPEC.md`, `-TEXTUAL-SPEC.md`, `-NAVIGATION-SPEC.md`), because the
  strongest enforcement claims below already have a witnessed mechanism in this repo.
- **Substrate-count note (flagged, not routed around):** the commission header says "three UI
  substrates" and then names two — Vue single-page applications and Textual terminal UIs. This
  document binds the two named. If a third substrate is intended (a plain-text/scripted CLI
  backend is the obvious candidate — the setup-TUI already has one behind `Ui.emit`), the
  cross-substrate binding notes below extend to it by the same reasoning, and the maintainer
  should reconcile the count when ratifying.

---

## Preamble — why the anti-pattern literature resists cataloging, and the principle chosen instead

ADR-0019 already made the decisive move: it declined to mint an anti-pattern list to maintain,
on the grounds that the enumeration is infinite and the genre references are the living catalog.
That is correct and this extension does not walk it back. But the maintainer's word for the
literature — "nebulous" — names a second, orthogonal problem that ADR-0019 leaves open, and it is
the problem this document exists to solve: even where the field *has* written its wisdom down, it
wrote it in a register that cannot become law.

The canonical sources are **heuristic checklists**: Nielsen's ten usability heuristics,
Shneiderman's eight golden rules, Tognazzini's first principles, Norman's seven stages of action.
Read them and the trouble is immediate. "Aesthetic and minimalist design." "Match between the
system and the real world." "Recognition rather than recall." These are not specifications; they
are **evaluative prompts for a human expert walking a finished interface**. Their fuzziness is not
a defect of the authors — it is the genre's design. A heuristic is deliberately abstract so that a
trained evaluator can apply it to any surface; the judgment is meant to live in the evaluator, not
the rule. That is exactly why the literature reads as nebulous to someone who wants a gate: a rule
whose enforcement is "an expert looks and decides" is, in ADR-0011's vocabulary, permanently
review-only, and review-only is the surface this project treats as presumptively decaying. The
four builds of 2026-07-22 are the proof: each was authored by a competent builder who, had they
been handed Nielsen's ten, could have recited them and still shipped the teletype — because a
heuristic does not fire at construction, it fires at inspection, and inspection is precisely the
step that cost the maintainer his eyes and ~$340.

So the organizing principle is not "collect more anti-patterns" (ADR-0019 already forbids that
race) and not "restate the heuristics" (they don't enforce). It is this: **a user interface is a
bundle of correspondences, and every witnessed anti-pattern is a broken correspondence.** A UI
puts a set of things into a required relationship —

- the **view** must correspond to the **model** (what's on screen is the live state, not a copy);
- each **control** must correspond 1:1 to a **variable** (one knob, one fact);
- the **navigation topology** must correspond to the **data's access topology** (a tree for a
  tree, a sequence only for a genuine sequence);
- the **input vocabulary** must correspond to the **platform's conventions** (the toolkit's focus
  and keybinding model, not a bespoke one);
- the **rendered text** must correspond to a **fixed typographic measure**, not to the accident of
  the viewport;
- **derived facts** must correspond to their **computation**, never to an operator's hand.

Each correspondence is an *invariant a type can hold*. That is the whole leverage. A broken
correspondence — a second store shadowing the model, two controls aliased to one slot, a wizard
imposed on a product type, a line whose width is a function of the terminal — is not a matter of
taste an evaluator must adjudicate; it is a structural fact a reviewer can point to and, in most
cases, a construction-time check can refuse. The method of this document, applied to each of the
twelve points, is therefore fixed: take the fuzzy heuristic the field already wrote, name the
**correspondence** it is really about, state the **broken form as the forbidden class**, and push
the check to the earliest surface — construction-time typed refusal first, load-time validation or
mechanical gate next, review-only named honestly only where the correspondence genuinely admits no
machine check. This is ADR-0000's own discipline turned on the UI layer: do not fix the instance
(the teletype), name the type that makes the class (a print-stream masquerading as an interactive
surface) unconstructable.

The correspondence frame also inherits a real external pedigree, so the law does not read as one
maintainer's idiosyncrasy. Norman's *gulf of execution* and *gulf of evaluation*, and his
insistence on **natural mappings** between controls and their effects, are the correspondence idea
in its founding form. Green & Petre's **Cognitive Dimensions of Notations** — *hidden
dependencies*, *visibility*, *role-expressiveness*, *hard mental operations* — are a vocabulary of
exactly these relationships and the ways notations break them; ADR-0019's own Rule 3 already cites
*hidden dependencies* by name. Where a point below leans on a specific heuristic (Nielsen,
Shneiderman, WCAG, Bringhurst on the typographic measure), it is cited at the point. The
through-line is the correspondence; the heuristics are the field's evidence that each
correspondence is load-bearing.

A note on honesty, per ADR-0011 Rule 1 and ADR-0000's escape hatch: several of these correspond-
ences reduce cleanly to a construction-time type (dual-store, aliasing, unbounded measure), and
those points claim it. Others — is *this* navigation genuinely a sequence? is *this* guard a real
error-prevention need or ceremony? — bottom out in judgment, and the point says review-only in
plain words rather than pretending a gate exists. The setup-TUI's existing purity gate and closed
element vocabulary (`gates/setup_tui_purity_gate.py`, `tools/setup_tui/elements.py` per
`FABLE-SETUP-TUI-TYPED-UI-SPEC.md`) are cited where they already mechanize a point, so the reader
can tell a witnessed mechanism from a proposed one.

---

## The twelve proscriptions

Each point states: the **proscription** (the forbidden class in rule register), the **class it
closes**, the **enforcement surface** (strongest feasible per ADR-0011's vocabulary), the
**literature pedigree**, the **Vue / Textual binding** where it differs, and the **witnessed
specimens** it covers (S1–S7 as numbered in the commission). Four points (P8–P11) foreclose
classes not yet witnessed in this repo.

---

### P1 — No substrate emulation: a lower-capability surface reimplemented inside a higher-capability toolkit is refused

**Proscription.** A UI built on a widget toolkit MUST use that toolkit's native interaction model
— focus, traversal, scrollback, selection, live regions. Reimplementing a *lower*-capability
substrate inside it — a teletype/print-stream as the primary surface, a hand-rolled scroll buffer,
a bespoke selection model — where the toolkit already provides the capability, is refused. The
primary interactive surface may not be a monolithic append-only text stream with a single docked
input; if nothing on the screen is focusable, scrollable, or addressable as a widget, the surface
is not a UI in the toolkit's terms and does not start.

**Class closed.** *Substrate downgrade* — any construction that discards a native capability of the
host toolkit to hand-roll a weaker equivalent. Named by capability (focus, scroll, selection,
addressable region), so a reviewer applies it without taste: "does a native widget provide this,
and did the build re-implement it as a text stream?"

**Enforcement.** Construction-time / mechanical gate. In this repo the mechanism already exists and
is the model to generalize: `gates/setup_tui_purity_gate.py` forbids `print(`/`.say(` outside the
two renderer files, so the primary surface *cannot* be a raw print loop. Extend that posture: the
top-level surface must be composed of toolkit widgets, checkable structurally.

**Pedigree.** Nielsen #4 *consistency and standards* and #2 *match between system and the real
world*; the principle of least astonishment; platform HIG conformance (the toolkit's own
interaction model is the convention ADR-0019 Rule 1 says you inherit). Alan Kay's point that a
medium emulating its predecessor wastes the medium is the same observation one level up.

**Vue / Textual.** *Textual:* every screen is `compose()`d from `Widget`s with a real focus chain;
a `RichLog`/print pane may be a *transcript component* but not the whole surface. *Vue:* content
renders through the component tree and template binding; no `innerHTML`/imperative
string-appending teletype, no re-implementing scroll or focus that the DOM already gives.

**Specimens.** **S1** (teletype emulated inside a widget toolkit).

---

### P2 — Navigation topology must be isomorphic to the data's access topology; a total-order presentation over a non-total-order space is refused

**Proscription.** The navigation structure a UI presents MUST match the access structure of the
data it edits. A configuration is a product type with at most a partial dependency order; it is a
random-access space and MUST be presented as one (a persistent tree/partition of the whole space,
per ADR-0019 Rule 1). Rendering such a space as a forced linear Back/Next wizard — imposing a
total order where the data has none — is refused. The converse is equally refused: presenting a
genuinely sequential dependency chain as a free-for-all that lets the operator skip a true
prerequisite. A wizard is licensed only by a declared, real total dependency order.

**Class closed.** *Topology mismatch between navigation and data* — a presentation whose traversal
order is not homomorphic to the data's genuine access order (a total order imposed on a partial/
product structure, or a required order dissolved into free navigation). The discriminator is
declarable: the build basis states the data's access structure (product / partial-order / total-
order chain); a wizard over anything but the last is the flagged class.

**Enforcement.** Spec-time (required in the build basis) + review, hardening toward load-time where
the dependency order is encoded. This is the honest maximum for the *general* case — "is this
data really a sequence?" is judgment — but it sharpens: if the configuration's partial order is a
declared data structure (a dependency graph over fields), a linearization that violates it *can* be
refused at load-time, and a stepper presented over a type with no declared order can be flagged
mechanically (no order declared ⇒ no wizard permitted). Per ADR-0019, "I have not seen a wizard
over a settings surface in the reference exemplars" is already sufficient grounds to reject.

**Pedigree.** Rosenfeld & Morville, *Information Architecture* — navigation mirrors the information
structure. Norman's *natural mapping* (the structure of the control surface maps the structure of
the thing controlled). Shneiderman's Visual Information-Seeking Mantra — *overview first, zoom and
filter, details on demand* — which a wizard structurally denies (there is no overview; the space is
revealed one hidden step at a time, a *visibility* failure in Green & Petre's terms).

**Vue / Textual.** *Vue:* a settings surface is a tree/tab/section-list with router or panel
switching, not a `<Stepper>`; a stepper component appearing in a configuration view is the smell.
*Textual:* a `Tree`/`TabbedContent`/section list with the whole space always visible, not a
sequence of screens gated by "Next"; the setup-TUI's navigation spec is the reference.

**Specimens.** **S2** (a product-type configuration rendered as a sequential wizard).

---

### P3 — The editing surface is a live projection of the model; a second store, a dirty/clean shadow copy, or a per-field/per-section "Save" that owns a separate truth is refused

**Proscription.** A field's on-screen value MUST be a live view of the model slot it edits —
reading it reads the model, changing it changes the model. Maintaining **two** stores — a form/UI
state and a model state that a "Save" action reconciles — is refused: it mints two writers of one
truth joined only by a hand-authored sync the operator can desynchronize (edit, forget to Save,
navigate away). Per-field and per-section "Save"/"Apply" buttons that commit a shadow copy into the
model are the forbidden shape. (A single explicit *commit-the-whole-configuration* boundary — one
transactional write of the whole live model to disk/backend — is not this class and is permitted;
what is refused is a *per-widget or per-section* second store.)

**Class closed.** *Dual-store view/model desync* — any construction where the widget's value and
the model's value are distinct mutable stores requiring a manual reconciliation step. This is
ADR-0012 P1 (one home per fact) at the view/model boundary and ADR-0002's no-silent-drift, in the
UI register.

**Enforcement.** Construction-time / typed. The binding *is* the widget's value accessor: there is
no second store to declare, so the class is unconstructable, not policed. Where a framework makes a
separate form store idiomatic, a lint/gate against a form store shadowing a bound model field is
the mechanical backstop.

**Pedigree.** Shneiderman, *direct manipulation* — the object of interest is continuously
represented and acted on directly, not through a deferred command. Norman's *gulf of evaluation*
(a Save button widens it: the operator cannot see whether the model reflects the screen without an
extra act). Green & Petre — a two-store design mints a *hidden dependency* (the model's real value
depends on whether Save was pressed, invisibly).

**Vue / Textual.** *Vue:* `v-model` / reactive bindings to the store (Pinia/reactive) are the
model's live view; a local `ref` copy that a Save handler writes back is the anti-pattern.
*Textual:* the widget's reactive attribute *is* the model slot (or a computed over it); a separate
dict the "Save" button flushes is refused.

**Specimens.** **S3** (per-section Save button, form state and model state as two stores).

---

### P4 — One fact, one control: control-to-variable mapping is 1:1 and typed; both aliasing (N controls → 1 slot) and mirroring (1 slot → N controls) are refused at construction

**Proscription.** Every model slot is bound to exactly **one** control, and every control edits
exactly **one** model slot. Two controls that write the same slot (flat-keyspace aliasing:
same-named checkboxes in two sections collapsing to one slot, so toggling one moves the other) are
refused. One value surfaced under two headings — editable in both, *or* editable in one and
mirrored read-only in the other — is refused. This is the construction-time mechanization of
ADR-0019 Rule 3 (unique placement is a typed claim), extended to bind the *widget-to-slot* mapping
in both directions.

**Class closed.** *Non-bijective control↔variable mapping* — one slot masquerading as two facts
(aliasing), or one fact claiming two homes (mirroring/projection). ADR-0019 Rule 3 already names
these as one class at the model and presentation layers; this point states the check as a mount-
time invariant over the binding table.

**Enforcement.** Construction-time typed refusal — the strongest surface, and ADR-0019 Rule 3
already mandates it ("a duplicated projection of one fact is a TYPE ERROR, refused loudly at UI
start, naming the fact and every section claiming it"). Mechanize as a mount-time check over the
declared binding registry: build a `slot → [controls]` and `control → [slots]` map; any slot with
>1 control, or control with >1 slot, is refused at start, naming the fact and every claimant. This
is a real gate, not review: the binding table is data.

**Pedigree.** Norman's *1:1 mapping* between control and effect and the *gulf of evaluation* a
duplicated control opens ("touch one widget, watch another twitch" — ADR-0019 Rule 3's own words).
Green & Petre's *hidden dependencies*. Information-architecture *unique placement* / polyhierarchy-
as-hazard. All three are the pedigree ADR-0019 Rule 3 already records.

**Vue / Textual.** *Vue:* two `v-model`s onto the same store path, or a computed getter with no
setter presented as an editable field, are the checkable forms. *Textual:* two widgets whose
`reactive` targets the same model attribute; the mount-time registry check is substrate-independent
(it reads the declared bindings, not the rendered screen).

**Specimens.** **S5** (flat-keyspace aliasing), **S6** (one value editable under two sub-headings,
then a read-only mirror — the specimen the maintainer adjudicated into ADR-0019 Rule 3).

---

### P5 — No bespoke input protocol: navigation and commands use the substrate's focus and keybinding primitives, never an in-band sentinel parsed from the value stream

**Proscription.** Navigation, command invocation, and mode changes MUST use the toolkit's native
input primitives — focus traversal, key bindings, actions/commands. Inventing a bespoke protocol —
a typed sentinel character (`<` to mean "go back") parsed out of the same stream the operator types
data into, an in-band control code, a magic string that switches modes — is refused. Data input and
control input MUST NOT share one in-band channel; the operator's literal `<` is data, and the
substrate's key/action layer is control.

**Class closed.** *In-band control signaling / bespoke input convention* — any construction that
carries control meaning (navigate, submit, cancel, switch) inside the data-entry channel as parsed
sentinels, rather than through the platform's out-of-band input primitives. This is the UI form of
the value/program confusion ADR-0000's 2026-07-18 amendment names (a value's characters altering
control structure); here the operator's data characters alter navigation.

**Enforcement.** Construction-time — navigation binds to actions/keys, so there is no sentinel
parser to review; a gate against a code path that inspects entered text for control tokens is the
backstop. Naming discoverability is a review floor (a keybinding the operator cannot discover is a
weaker but separate failure — see P8's visibility register).

**Pedigree.** Nielsen #4 *consistency and standards* / principle of least astonishment. Green &
Petre *role-expressiveness* (a `<` that is sometimes data and sometimes a command has no legible
role). And the deep-systems pedigree: **in-band signaling** is a named hazard in protocol design
(the Bell System's in-band signaling, exploited by blue boxes, is the canonical cautionary tale) —
mixing control and data on one channel is a class the field abandoned deliberately.

**Vue / Textual.** *Textual:* `BINDINGS` / `action_*` methods and the focus system carry
navigation; nothing reads `Input.value` for control tokens. *Vue:* `@keydown` handlers bound to
named commands and standard focus order; no parsing typed text for sentinels, no reserving a
literal character the user might legitimately enter.

**Specimens.** **S4**, first half (the typed `<` navigation sentinel).

---

### P6 — No keybinding collides with the host environment's reserved chords; the binding namespace is declared and checked against the host's reserved set

**Proscription.** A UI's key bindings MUST be declared as a set and MUST NOT collide with chords
the host environment reserves. A Textual TUI MUST NOT bind a chord the terminal multiplexer or
terminal reserves — `ctrl+b` is the default tmux prefix and is refused; likewise the terminal's own
flow-control and signal chords. A Vue SPA MUST NOT bind over browser-reserved and assistive-
technology chords (`ctrl+w`, `ctrl+t`, `ctrl+l`, `/` where the browser uses it, screen-reader pass-
through keys). The binding table is a declared artifact checked against a known-reserved set.

**Class closed.** *Host-chord collision* — any binding that shadows a chord the operator's host
(multiplexer, terminal, browser, AT) has already claimed, so the keystroke does the wrong thing or
nothing. Distinct from P5: P5 forbids inventing a control channel; P6 forbids a *legitimate*
binding that steps on the host.

**Enforcement.** Load-time / mechanical gate against the *known* reserved set (tmux prefix,
terminal C0 controls, common browser chords) — a real check over the declared `BINDINGS` table.
Review-only is the honest maximum for the *open* tail (an operator's personally rebound tmux
prefix, an exotic multiplexer) because the host set is not fully knowable at build time; the point
says so plainly rather than claiming total coverage.

**Pedigree.** Nielsen #4 *consistency and standards*; principle of least astonishment; the
keyboard-shortcut-conflict literature and WCAG 2.1 SC 2.1.4 (*Character Key Shortcuts* — single-
key shortcuts must be avoidable/remappable precisely because they collide). The host-reservation
concern is the same "don't bind another tool's prefix" ADR-0019 Rule 2 lists as a witnessed
anti-pattern.

**Vue / Textual.** *Textual:* check `BINDINGS` against the terminal/multiplexer reserved set at app
start; prefer `ctrl+`-chords known-free or app-scoped. *Vue:* check the registered global handlers
against browser/AT reserved chords; prefer non-reserved combos and always provide a visible
alternative control (WCAG 2.1.1 keyboard-operable does not require the *chord*, only that the action
be reachable).

**Specimens.** **S4**, second half (`ctrl+b` colliding with the tmux prefix).

---

### P7 — Text measure is bounded: no rendered line's width is a function of the viewport/terminal width; every text element wraps to a fixed typographic measure

**Proscription.** The width of a rendered text element MUST be a fixed typographic measure, not the
accident of the viewport. No emitted line may span "whatever the terminal/window happens to be";
prose wraps to a bounded measure (a column cap in the ~66-character neighborhood, the setup-TUI
uses 78), tables fit columns with per-column caps and wrap within a cell rather than blowing out the
row. A single 348-character line filling the operator's tmux width is refused at the renderer.

**Class closed.** *Unbounded text measure* — any text whose line length is determined by the
container's width rather than a fixed readability measure. Quantified over every text emission, per
the setup-TUI typed-UI spec's own closure statement.

**Enforcement.** Construction-time / mechanical gate — and this one is **witnessed** in the repo:
`FABLE-SETUP-TUI-TYPED-UI-SPEC.md` §2 makes the canonical renderer wrap `Paragraph`/`Note` to a
78-column measure and cap table columns, and the purity gate plus a `seen-red` fixture prove an
over-wide paragraph renders with no line over measure (red first against a raw-print stand-in). The
correspondence is enforced by making width a renderer constant, not a viewport read.

**Pedigree.** Typographic *measure* — Bringhurst, *The Elements of Typographic Style* (the 45–75
character line, 66 as the ideal for single-column text); legibility research (Tinker, *Legibility of
Print*); responsive-design line-length practice (`max-width` in `ch`). All say the same: reading
speed and comprehension degrade past a bounded line length, so measure is a property of the text,
never of the window.

**Vue / Textual.** *Vue:* text containers carry `max-width` in `ch`/`rem` (e.g. `max-width: 66ch`),
never `width: 100%` on running prose; the viewport scrolls, the measure does not grow. *Textual:*
the canonical `render_text` wraps at the measure constant before the Textual backend styles it —
width is owned by the renderer, and the terminal width is irrelevant to line length.

**Specimens.** **S7** (the 348-character line spanning the full tmux width).

---

### P8 — Every interactive element is reachable and operable through the substrate's standard focus/traversal model; nothing is pointer-only, focus-trapping, or operable solely by an undiscoverable gesture

**Proscription.** Every actionable control MUST be reachable and operable via the substrate's
standard keyboard/focus traversal, in a sensible order, with a visible focus indicator, and MUST NOT
trap focus. A control that can only be operated by mouse/pointer, a modal that captures focus with
no keyboard exit, or an action available only through an undiscoverable gesture (no label, no
binding hint, no menu entry) is refused. *(This is the positive, general form whose absence S1's
"nothing focusable" was one instance of; it forecloses the class rather than the instance.)*

**Class closed.** *Keyboard-inoperability / focus-integrity failure* — any interactive element not
reachable and operable through standard traversal, any focus trap, any pointer-only action. Named
by the concrete failures (unreachable, no visible focus, trap, undiscoverable) so a reviewer or a
gate applies it without taste.

**Enforcement.** Mechanical gate + construction-time. *Vue:* strong — automated accessibility linting
(`eslint-plugin-vuejs-accessibility`, axe-core in test) mechanically catches missing focusability,
tab-order, and label failures. *Textual:* the focus chain is introspectable — a test can assert every
declared interactive widget is in the focus order and that no modal lacks a dismiss binding; this is
a construction/test-time check, not review. The general "is this gesture discoverable" tail is
review, named honestly.

**Pedigree.** WCAG 2.1 — SC 2.1.1 *Keyboard*, SC 2.1.2 *No Keyboard Trap*, SC 2.4.3 *Focus Order*,
SC 2.4.7 *Focus Visible*. Nielsen's *flexibility and efficiency* and *accessibility* register.
Norman's *discoverability* (an action with no perceptible signifier does not exist for the user).

**Vue / Textual.** As above: Vue leans on the mature a11y lint/test toolchain (a genuine mechanical
gate); Textual leans on focus-chain introspection tests. Both refuse a surface where the primary
actions are not keyboard-complete — which is also the deeper reason S1's teletype was wrong (it had
no focusable anything).

**Specimens.** None directly (S1 is covered by P1); forecloses an unwitnessed class.

---

### P9 — System status is always visible: no operator action without feedback, no unbounded blocking without a visible progress/busy state

**Proscription.** Every operator action MUST produce perceptible feedback, and every operation that
can run longer than a perceptual threshold MUST surface a visible busy/progress state; the UI MUST
NOT block silently. A button that fires with no acknowledgment, a save/validate/network step that
freezes the surface with no indicator, an operation whose completion the operator can only infer —
each is refused. Long-running or silent-computing states are surfaced as status, not as an
apparently-hung screen (the setup-TUI's own F4 leg — a bridge misreading sustained silent load as
shutdown — is this class biting at the infrastructure level).

**Class closed.** *Missing/absent feedback and hidden system state* — any action or state transition
whose occurrence is not perceptible to the operator within the relevant response-time threshold.

**Enforcement.** Review-only for the general "does every action give feedback" judgment — named
honestly as the maximum, because whether a given feedback is *sufficient* is a perceptual call.
Hardens at the seams: async actions can be *required by construction* to route through a status
element (a busy/progress component), so "an async handler that touches the surface without a status
transition" becomes a lint target. The threshold pedigree gives the numbers to check against.

**Pedigree.** Nielsen #1 *visibility of system status* (his first heuristic, and the most-cited).
Norman's *feedback* stage. Response-time thresholds: Miller (1968) and Nielsen's 0.1 s / 1 s / 10 s
bands (instant / flow-preserving / attention-losing) — the quantified line for "needs an
indicator."

**Vue / Textual.** *Vue:* pending/loading state on async actions bound to a visible indicator
(spinner/disabled+busy); no `await` in a handler that leaves the surface unchanged. *Textual:* a
`LoadingIndicator`/status line driven by the worker's liveness, and — per the F4 diagnostic — the
bridge timeout keyed to worker progress, not wall-clock silence, so a legitimately-computing screen
is not mistaken for a dead one.

**Specimens.** None directly; forecloses an unwitnessed class (with an in-repo infrastructure
foothold via the F4 leg).

---

### P10 — Derived facts are computed and read-only in the UI; a control that lets the operator set a value the system should derive is refused

**Proscription.** A value the system derives — a status, a count, a computed summary, a field whose
value is a function of other fields — MUST be rendered as a computed, read-only view, never as an
editable control. Offering an editable widget bound to a derived quantity is refused: it invites the
operator to set a value the system will immediately recompute or, worse, will trust over its own
source, minting a second writer of a derived fact. This is ADR-0019 Rule 1's "statuses derived, not
declared," stated as a construction-time prohibition on editable derived controls.

**Class closed.** *Editable derived value* — any control that accepts operator input for a quantity
the model computes from another source. The discriminator is declarable: a field is either a
source-of-truth slot (editable) or a derived view (read-only); a field typed as derived that carries
an editable control is the flagged class.

**Enforcement.** Construction-time typed — a field carries its kind (`source` vs `derived`) and the
renderer refuses to bind an editable control to a `derived` field, naming it. This is ADR-0012 P1
(derived quantities are computed, never re-typed) at the widget layer, and it is a real gate over
the field table, not review.

**Pedigree.** ADR-0012 P1 / ADR-0011 Rule 4 (derive-don't-duplicate; a net over the class). Norman's
*feedback* vs *input* distinction (a derived value is the system talking back, not a place to type).
Green & Petre *hidden dependencies* (an editable derived field hides which value wins).

**Vue / Textual.** *Vue:* a `computed` (getter-only) renders as text or a disabled field, never a
`v-model` target; a writable computed standing in for a derived display is the smell. *Textual:* a
`reactive`/`compute`d attribute renders read-only; no `Input` bound to a computed value.

**Specimens.** None directly; forecloses an unwitnessed class adjacent to S3/S5 (it is the "second
writer" disease in the derived register).

---

### P11 — Irreversible actions are guarded or undoable; no unguarded destructive control, and no dead-end error state

**Proscription.** A destructive or irreversible action (delete, overwrite, reset-to-default, discard
unsaved work) MUST be either confirmed, undoable, or otherwise guarded before it commits; an
unguarded one-click irreversible control is refused. Every error or failure state MUST offer a way
forward — a retry, a correction, an exit — and MUST NOT strand the operator in a state with no
action. The action's reversibility is a typed property of the action, not an afterthought.

**Class closed.** *Unguarded irreversibility / dead-end state* — any action whose irreversible
effect commits without a guard, and any error state that offers the operator no next move.

**Enforcement.** Construction-time typed for the guard (an action is declared `reversible |
guarded | confirmed`; a `destructive` action with no guard is refused at wiring) + review for the
harder judgment of whether a given state is a true dead-end. The typed-action half is a real gate;
the dead-end half is honestly review, because "is there a way forward" is a reachability judgment
over the whole flow.

**Pedigree.** Nielsen #3 *user control and freedom* (undo/redo, "emergency exit") and #5 *error
prevention*. Shneiderman's golden rules — *permit easy reversal of actions* and *prevent errors*.
Norman on *forgiveness* and reversible actions. The whole family is the field's oldest safety
register.

**Vue / Textual.** *Vue:* destructive actions behind a confirm dialog or an undo toast; disabled-
until-confirmed patterns; no bare `@click="delete"` on an irreversible op. *Textual:* a confirmation
`Screen`/modal (with a keyboard-reachable dismiss, per P8) or an undo action before an irreversible
commit; a failure screen always binds an action to leave it.

**Specimens.** None directly; forecloses an unwitnessed class (the one whose absence is most
expensive when it finally appears).

---

### P12 — Content is typed, semantically distinct elements — not an undifferentiated text blob; layout carried inside a string (embedded newlines/columns/ASCII-art) is refused

**Proscription.** Everything shown to the operator MUST be constructed as one of a closed set of
typed semantic elements — heading, paragraph, table (real columns with distinct headers), status
line, note (with a tone), separator — each visually delimited from the others. A "wall of text": an
undifferentiated block with no semantic structure, or a raw string doing layout work with embedded
newlines and hand-spaced pseudo-columns (ASCII-art tables, headers faked with dashes), is refused.
Distinct semantic elements — column headers especially — are delimited by type, not by whitespace
convention inside a string.

**Class closed.** *Untyped presentational blob* — any operator-facing content that is a raw string
carrying its own layout, rather than a typed semantic element the renderer lays out. The
correspondence: content ↔ its semantic type; a string that encodes structure as formatting breaks
it. Distinct from P7 (P7 bounds *width*; P12 requires *semantic structure*).

**Enforcement.** Construction-time typed — **witnessed** in the repo: `FABLE-SETUP-TUI-TYPED-UI-SPEC.md`
mints exactly this closed vocabulary (`Heading`, `Paragraph`, `Table`, `StatusLine`, `Note`, `Rule`)
in `tools/setup_tui/elements.py`, removes the free `Ui.say(str)`/`Ui.banner(str)` register, and the
purity gate refuses `print(`/`.say(` outside the renderers plus raises on an unknown element type
(negative control in the fixture). A paragraph "may never be emitted pre-wrapped with embedded
newlines doing layout work" — that is this proscription, already law-in-progress.

**Pedigree.** Gestalt grouping principles — *proximity* and *similarity* — which say structure must
be perceptible, not implied by a run of text. Information/typographic hierarchy (headings, tables,
labels as distinct levels). The separation-of-content-and-presentation principle (semantic markup
vs formatting-in-content) — the same discipline that made HTML-with-CSS beat layout-in-`<font>`-
tags. Green & Petre *role-expressiveness* (a table's role must be visible as a table).

**Vue / Textual.** *Vue:* semantic components / semantic HTML (`<table>`, `<h_>`, list elements) with
styling in CSS; never a `<pre>` blob of hand-spaced columns as the data presentation. *Textual:* the
typed element vocabulary with `DataTable` for tabular data (the field strategy's "one good
precedent"); no ASCII-art columns inside a `Static`.

**Specimens.** **S7** (the 348-char line is both an unbounded-measure failure — P7 — and, per the
maintainer's paired observation about walls of text and undelimited semantic elements, a typed-
element failure — P12; the two points cut the one specimen along its two independent axes).

---

## Specimen coverage map (all seven fall under a point; the points are not a list of the seven)

| Specimen | Covered by | Point's class is broader than the specimen? |
| --- | --- | --- |
| S1 — teletype in a widget toolkit | **P1** | Yes — any substrate downgrade, named by capability |
| S2 — product-type config as a wizard | **P2** | Yes — any navigation/data topology mismatch, both directions |
| S3 — per-section Save (two stores) | **P3** | Yes — any dual-store view/model desync |
| S4 — typed `<` sentinel | **P5** | Yes — any in-band control signaling |
| S4 — `ctrl+b` vs tmux prefix | **P6** | Yes — any host-chord collision |
| S5 — flat-keyspace aliasing | **P4** | Yes — any non-bijective control↔variable mapping |
| S6 — value mirrored under two headings | **P4** | Yes — mechanizes ADR-0019 Rule 3 at the binding table |
| S7 — 348-char unbounded line | **P7** + **P12** | Yes — unbounded measure (P7) and untyped blob (P12), two axes |

**Points that foreclose classes not yet witnessed here:** P8 (keyboard/focus integrity), P9
(feedback / system-status visibility), P10 (editable derived value), P11 (unguarded irreversibility
/ dead-end). Four of the twelve extend the law past the day's specimens, per the commission's
requirement that the list quantify over classes rather than catalog the seven.

**Enforcement-surface honesty (ADR-0011 Rule 1), summarized:** construction-time typed refusal is
claimed for P1, P3, P4, P7, P10, P12 (three of these — P1, P7, P12 — already have a witnessed
mechanism in the setup-TUI purity gate and typed element vocabulary). Load-time/mechanical gate is
the surface for P6 and P8 (P8 mechanical in Vue via a11y lint, test-time in Textual via focus-chain
introspection). Spec-time-plus-review, hardening toward load-time, is the honest maximum for P2 and
P11's dead-end half and P9's general case — and each says so in plain words rather than claiming a
gate it does not have. No point rests on "an expert will notice," which is the register the
preamble argues the heuristic literature is trapped in and this extension exists to escape.
